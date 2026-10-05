extends SceneTree

const State = preload("res://scripts/story_state.gd")
var failures: Array[String] = []

func check(value: bool, message: String) -> void:
    if not value:
        failures.append(message)
        push_error(message)

func _initialize() -> void:
    call_deferred("_run")

func _run() -> void:
    var campaign: Dictionary = State.new().story
    var audit: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://docs/NARRATIVE_REPAIRS_20261005.json"))
    for repair in audit.repairs:
        var traveler = State.new(campaign)
        traveler.current = repair.node_id
        traveler.stats = {"qi": 10, "trust": 10, "insight": 10, "resolve": 10}
        var original: Dictionary = traveler.stats.duplicate()
        check(traveler.choose(int(repair.choice_index)), repair.id + ": choose")
        check(traveler.stats == original, repair.id + ": preference grants no growth")
        check(traveler.save_game("user://narrative_new.json"), "Save before completion")
        var resumed = State.new(campaign)
        check(resumed.load_game("user://narrative_new.json"), "Restore pending branch")
        for scene_id in repair.branch:
            check(resumed.current == scene_id, repair.id + ": exclusive path")
            check(resumed.stats == original, repair.id + ": no premature credit")
            check(resumed.advance(), repair.id + ": advance actual work")
        var expected: Dictionary = original.duplicate()
        for stat in repair.earned:
            expected[stat] += int(repair.earned[stat])
        check(resumed.stats == expected, repair.id + ": completed growth")
        check(resumed.save_game("user://narrative_new.json"), "Save completed growth")
        var restored = State.new(campaign)
        check(restored.load_game("user://narrative_new.json"), "Restore completed growth")
        restored.current = repair.completion_node
        check(restored.advance() and restored.stats == expected, repair.id + ": no replay credit")

        # An old checkpoint already paid on selection. Migration keeps its scores.
        var legacy = FileAccess.open("user://narrative_legacy.json", FileAccess.WRITE)
        legacy.store_string(JSON.stringify({"version": 1, "current": repair.branch[0],
            "stats": expected, "history": [{"speaker": campaign.nodes[repair.node_id].speaker,
            "text": campaign.nodes[repair.node_id].text}], "completed_practice": {}}))
        legacy.close()
        var prior = State.new(campaign)
        check(prior.load_game("user://narrative_legacy.json"), "Load old branch checkpoint")
        check(prior.stats == expected and prior.completed_practice.has(repair.completion_node),
            repair.id + ": old credit recognised without changing scores")
        prior.current = repair.completion_node
        check(prior.advance() and prior.stats == expected, repair.id + ": no migration duplicate")
        check(prior.save_game("user://narrative_new.json"), "Persist migrated checkpoint")
        check(restored.load_game("user://narrative_new.json") and restored.stats == expected,
            "Migrated checkpoint stays stable after another load")

    for decision in audit.decisions:
        for index in range(3):
            var ordinary = State.new(campaign)
            ordinary.current = decision.decision_id
            var option: Dictionary = ordinary.node().choices[index]
            check(ordinary.can_choose(option) == (not option.has("requires")), "Ordinary approach availability")
            ordinary.stats = {"qi": 10, "trust": 10, "insight": 10, "resolve": 10}
            check(ordinary.choose(index), "Every trained desert approach must be available")
            check(ordinary.advance() and ordinary.current == decision.rejoin,
                "Consequences rejoin before the original observation")
            check(ordinary.stats == {"qi": 10, "trust": 10, "insight": 10, "resolve": 10},
                "Dilemma preferences must not manufacture training")

    var bad = FileAccess.open("user://narrative_bad.json", FileAccess.WRITE)
    bad.store_string(JSON.stringify({"version": 1, "current": "arrival",
        "stats": {"qi": 0, "trust": 0, "insight": 0, "resolve": 0},
        "history": [], "practice_rules": 3}))
    bad.close()
    var retained = State.new(campaign)
    retained.current = "pendant"
    check(not retained.load_game("user://narrative_bad.json") and retained.current == "pendant",
        "Unknown practice-rule revisions reject atomically")
    for path in ["user://narrative_new.json", "user://narrative_legacy.json", "user://narrative_bad.json"]:
        for candidate in [path, path + ".bak"]:
            if FileAccess.file_exists(candidate):
                DirAccess.remove_absolute(candidate)
    if failures.is_empty():
        print("JADE_VOW_NARRATIVE_REVISION_TESTS_OK")
    quit(0 if failures.is_empty() else 1)
