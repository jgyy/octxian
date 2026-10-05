extends SceneTree

const State = preload("res://scripts/story_state.gd")
var failures: Array[String] = []

func check(value: bool, message: String) -> void:
    if not value:
        failures.append(message)
        push_error(message)

func write_checkpoint(campaign: Dictionary, repair: Dictionary, scores: Dictionary, rules: int, at_choice: bool = false) -> void:
    var checkpoint := FileAccess.open("user://additional_legacy.json", FileAccess.WRITE)
    var saved := {"version": 1, "current": repair.node_id if at_choice else repair.branch[0],
        "stats": scores, "history": [{"speaker": campaign.nodes[repair.node_id].speaker,
        "text": campaign.nodes[repair.node_id].text}], "completed_practice": {}}
    if rules > 0:
        saved["practice_rules"] = rules
    checkpoint.store_string(JSON.stringify(saved))
    checkpoint.close()

func _initialize() -> void:
    call_deferred("_run")

func _run() -> void:
    var campaign: Dictionary = State.new().story
    var audit: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://docs/ADDITIONAL_REPAIRS_20261005.json"))
    var original := {"qi": 100, "trust": 100, "insight": 100, "resolve": 100}
    for repair in audit.repairs:
        var traveler = State.new(campaign)
        traveler.current = repair.node_id
        traveler.stats = original.duplicate()
        check(traveler.choose(int(repair.choice_index)), repair.id + ": choose")
        check(traveler.stats == original, repair.id + ": no preference growth")
        check(traveler.save_game("user://additional_current.json"), "Save pending revision-2 work")
        var saved: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("user://additional_current.json"))
        check(saved.practice_rules == 2, "New checkpoints identify the second rules")
        var resumed = State.new(campaign)
        check(resumed.load_game("user://additional_current.json"), "Resume pending work")
        var expected: Dictionary = original.duplicate()
        for stat in repair.earned:
            expected[stat] += int(repair.earned[stat])
        for scene in repair.branch:
            check(resumed.current == scene and resumed.stats == original, repair.id + ": branch credit is pending")
            check(resumed.advance(), repair.id + ": perform consequence")
        check(resumed.stats == expected, repair.id + ": completed credit")
        check(resumed.save_game("user://additional_current.json"), "Save completed work")
        var restored = State.new(campaign)
        check(restored.load_game("user://additional_current.json"), "Restore completed work")
        restored.current = repair.completion_node
        check(restored.advance() and restored.stats == expected, repair.id + ": replay cannot pay twice")
        for rules in [0, 1]:
            write_checkpoint(campaign, repair, expected, rules)
            var legacy = State.new(campaign)
            check(legacy.load_game("user://additional_legacy.json"), "Load earlier rule checkpoint")
            check(legacy.completed_practice.has(repair.completion_node) and legacy.stats == expected,
                repair.id + ": recognise previous selection credit")
            legacy.current = repair.completion_node
            check(legacy.advance() and legacy.stats == expected, repair.id + ": old credit stays single")
            check(legacy.save_game("user://additional_current.json"), "Persist rule migration")
            check(restored.load_game("user://additional_current.json") and restored.stats == expected,
                "Repeated migration loads preserve scores")
            write_checkpoint(campaign, repair, original, rules, true)
            var waiting = State.new(campaign)
            check(waiting.load_game("user://additional_legacy.json"), "Load before selecting a task")
            check(not waiting.completed_practice.has(repair.completion_node), "Viewing a choice is not paid work")
            check(waiting.choose(int(repair.choice_index)), "Choose after migration")
            for scene in repair.branch:
                check(waiting.current == scene and waiting.advance(), "Complete new pending task")
            check(waiting.stats == expected, "Unselected legacy task earns its own completed growth")

    # Revision-1 saves had already deferred the original 101 branches.
    # They must not be marked paid just because the next revision was loaded.
    var first: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://docs/NARRATIVE_REPAIRS_20261005.json"))
    for repair in first.repairs:
        write_checkpoint(campaign, repair, original, 1)
        var pending = State.new(campaign)
        check(pending.load_game("user://additional_legacy.json"), "Load revision-1 original pending work")
        check(not pending.completed_practice.has(repair.completion_node),
            "The second migration must preserve first-revision pending credit")
        var expected: Dictionary = original.duplicate()
        for stat in repair.earned:
            expected[stat] += int(repair.earned[stat])
        pending.current = repair.completion_node
        check(pending.advance() and pending.stats == expected, "Original pending work still receives its reward")

    var invalid := FileAccess.open("user://additional_bad.json", FileAccess.WRITE)
    invalid.store_string(JSON.stringify({"version": 1, "current": "arrival",
        "stats": original, "history": [], "practice_rules": 3}))
    invalid.close()
    var retained = State.new(campaign)
    retained.current = "pendant"
    retained.stats = original.duplicate()
    check(not retained.load_game("user://additional_bad.json") and retained.current == "pendant" and retained.stats == original,
        "Unknown rules reject without changing the live checkpoint")
    for path in ["user://additional_current.json", "user://additional_legacy.json", "user://additional_bad.json"]:
        for candidate in [path, path + ".bak"]:
            if FileAccess.file_exists(candidate):
                DirAccess.remove_absolute(candidate)
    if failures.is_empty():
        print("JADE_VOW_ADDITIONAL_REPAIRS_TESTS_OK")
    quit(0 if failures.is_empty() else 1)
