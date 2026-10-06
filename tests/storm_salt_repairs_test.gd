extends SceneTree

const State = preload("res://scripts/story_state.gd")
var failures: Array[String] = []

func check(value: bool, message: String) -> void:
    if not value:
        failures.append(message)
        push_error(message)

func write_legacy(campaign: Dictionary, repair: Dictionary, scores: Dictionary, rules: int, current: String, completed: bool = false) -> void:
    var entries: Array = [{"speaker": campaign.nodes[repair.node_id].speaker,
        "text": campaign.nodes[repair.node_id].text}]
    if completed:
        entries.append({"speaker": campaign.nodes[repair.completion_node].speaker,
            "text": campaign.nodes[repair.completion_node].text})
    var saved := {"version": 1, "current": current, "stats": scores,
        "history": entries, "completed_practice": {}}
    if rules > 0:
        saved["practice_rules"] = rules
    var file := FileAccess.open("user://storm_salt_legacy.json", FileAccess.WRITE)
    file.store_string(JSON.stringify(saved))
    file.close()

func _initialize() -> void:
    call_deferred("_run")

func _run() -> void:
    var campaign: Dictionary = State.new().story
    var audit: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://docs/STORM_SALT_REPAIRS_20261006.json"))
    var initial := {"qi": 100, "trust": 100, "insight": 100, "resolve": 100}
    check(State.CURRENT_PRACTICE_RULES == 3, "This batch introduces practice rules 3")
    for repair in audit.repairs:
        var expected: Dictionary = initial.duplicate()
        for stat in repair.earned:
            expected[stat] += int(repair.earned[stat])
        var traveler = State.new(campaign)
        traveler.current = repair.node_id
        traveler.stats = initial.duplicate()
        check(traveler.choose(int(repair.choice_index)) and traveler.stats == initial,
            repair.id + ": selecting future work gives no growth")
        check(traveler.save_game("user://storm_salt_current.json"), "Save new pending work")
        var saved: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("user://storm_salt_current.json"))
        check(saved.practice_rules == 3 and saved.version == 1, "Identify new rules without changing save version")
        var resumed = State.new(campaign)
        check(resumed.load_game("user://storm_salt_current.json"), "Restore pending work")
        for scene in repair.branch:
            check(resumed.current == scene and resumed.stats == initial, repair.id + ": work remains pending")
            check(resumed.advance(), repair.id + ": complete authored passage")
        check(resumed.stats == expected and resumed.completed_practice.has(repair.completion_node),
            repair.id + ": completion grants exactly the original credit")
        check(resumed.save_game("user://storm_salt_current.json"), "Save completed work")
        var restored = State.new(campaign)
        check(restored.load_game("user://storm_salt_current.json"), "Restore completed work")
        restored.current = repair.completion_node
        check(restored.advance() and restored.stats == expected, "Revisit cannot pay twice")
        for rules in [0, 1, 2]:
            write_legacy(campaign, repair, expected, rules, repair.branch[0])
            var legacy = State.new(campaign)
            check(legacy.load_game("user://storm_salt_legacy.json"), "Load older paid selection")
            check(legacy.completed_practice.has(repair.completion_node) and legacy.stats == expected,
                repair.id + ": preserve previously paid selection credit")
            legacy.current = repair.completion_node
            check(legacy.advance() and legacy.stats == expected, "Older branch cannot double-pay")
            write_legacy(campaign, repair, expected, rules, resumed.current, true)
            var past = State.new(campaign)
            check(past.load_game("user://storm_salt_legacy.json") and past.completed_practice.has(repair.completion_node),
                "Previously completed work retains its recognition")
            write_legacy(campaign, repair, initial, rules, repair.node_id)
            var unselected = State.new(campaign)
            check(unselected.load_game("user://storm_salt_legacy.json"), "Load before an old choice")
            check(not unselected.completed_practice.has(repair.completion_node), "Unselected work is unpaid")
            check(unselected.choose(int(repair.choice_index)), "Choose after migration")
            for scene in repair.branch:
                check(unselected.current == scene and unselected.advance(), "Perform migrated pending task")
            check(unselected.stats == expected, "Unselected older task receives completed credit")
        var overflow = State.new(campaign)
        overflow.current = repair.completion_node
        overflow.stats = initial.duplicate()
        for stat in repair.earned:
            overflow.stats[stat] = State.MAX_STAT
        var old_scores: Dictionary = overflow.stats.duplicate()
        check(not overflow.advance() and overflow.current == repair.completion_node
            and overflow.stats == old_scores and overflow.history.is_empty()
            and overflow.completed_practice.is_empty(), "Overflow fails atomically before recording completion")

    # New migration must preserve rewards deferred by both earlier revisions.
    for entry in [{"file": "docs/NARRATIVE_REPAIRS_20261005.json", "rules": 1},
        {"file": "docs/ADDITIONAL_REPAIRS_20261005.json", "rules": 2}]:
        var previous: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://" + entry.file))
        for repair in previous.repairs:
            write_legacy(campaign, repair, initial, int(entry.rules), repair.branch[0])
            var pending = State.new(campaign)
            check(pending.load_game("user://storm_salt_legacy.json"), "Load earlier pending practice")
            check(not pending.completed_practice.has(repair.completion_node), "Earlier deferred work stays pending")
            var expected: Dictionary = initial.duplicate()
            for stat in repair.earned:
                expected[stat] += int(repair.earned[stat])
            pending.current = repair.completion_node
            check(pending.advance() and pending.stats == expected, "Earlier pending reward still pays on completion")

    var retained = State.new(campaign)
    retained.current = "pendant"
    retained.stats = initial.duplicate()
    for rules in [-1, 4, 2.5, "3"]:
        var file := FileAccess.open("user://storm_salt_bad.json", FileAccess.WRITE)
        file.store_string(JSON.stringify({"version": 1, "current": "arrival",
            "stats": initial, "history": [], "practice_rules": rules}))
        file.close()
        check(not retained.load_game("user://storm_salt_bad.json") and retained.current == "pendant"
            and retained.stats == initial and retained.history.is_empty()
            and retained.completed_practice.is_empty(), "Invalid revision fails atomically")
    for path in ["user://storm_salt_current.json", "user://storm_salt_legacy.json", "user://storm_salt_bad.json"]:
        for candidate in [path, path + ".bak"]:
            if FileAccess.file_exists(candidate):
                DirAccess.remove_absolute(candidate)
    if failures.is_empty():
        print("JADE_VOW_STORM_SALT_REPAIRS_TESTS_OK")
    quit(0 if failures.is_empty() else 1)
