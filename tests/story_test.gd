extends SceneTree

const State = preload("res://scripts/story_state.gd")
var failures: Array[String] = []

func check(condition: bool, message: String) -> void:
	if not condition:
		failures.append(message)
		push_error(message)

func _initialize() -> void:
	var state = State.new()
	check(state.current == "arrival", "Story should start at arrival")
	check(state.story.get("chapters", {}).has("book_ii"), "Campaign chapters should load")
	for key in state.story.nodes:
		var node: Dictionary = state.story.nodes[key]
		check(state.story.characters.has(node.speaker), "Unknown speaker: " + key)
		if node.has("next"):
			check(state.story.nodes.has(node.next), "Broken next link: " + key)
		for choice in node.get("choices", []):
			check(state.story.nodes.has(choice.next), "Broken choice link: " + key)
		check(not str(node.text).is_empty(), "Empty text: " + key)
	state.current = "first_choice"
	check(not state.choose(-1) and not state.choose(9), "Out-of-range choices should fail")
	check(state.choose(0), "Valid choice should succeed")
	check(state.stats.trust == 2 and state.stats.qi == 1, "Choice effects should apply")
	check(state.current == "trust", "Choice should follow its link")
	state.current = "final_choice"
	check(not state.choose(0), "Qi-gated choice should be disabled")
	check(state.current == "final_choice", "Blocked choices must not advance")
	state.stats.qi = 4
	check(state.choose(0) and state.current == "shared", "Qualified choice should advance")
	check(state.save_game("user://test_save.json"), "Save should write")
	var restored = State.new()
	check(restored.load_game("user://test_save.json"), "Save should round trip")
	check(restored.current == state.current and restored.stats == state.stats, "Save should restore state")
	var bad := FileAccess.open("user://bad_save.json", FileAccess.WRITE)
	bad.store_string('{"version":1,"current":"arrival","stats":{"qi":"oops"},"history":[]}')
	bad.close()
	check(not restored.load_game("user://bad_save.json"), "Corrupt stat values should be rejected")
	check(restored.current == "shared", "Failed load must preserve current state")

	check(not restored.go("missing"), "Unknown destinations must be rejected")
	state.current = "first_choice"
	var snapshot_stats: Dictionary = state.stats.duplicate()
	var snapshot_history: Array = state.history.duplicate(true)
	var broken: Dictionary = state.story.nodes.first_choice.choices[0].duplicate(true)
	broken.next = "missing"
	state.story.nodes.first_choice.choices[0] = broken
	check(not state.choose(0), "Choice with a broken destination must fail")
	check(state.stats == snapshot_stats and state.history == snapshot_history and state.current == "first_choice", "Failed choices must leave stats, journal and scene untouched")
	state = State.new()
	state.current = "first_choice"
	state.story.nodes.first_choice.choices[0].effects["unknown"] = 1
	check(not state.choose(0) and state.stats.trust == 0, "Unknown effect stats must be rejected atomically")
	state = State.new()
	state.current = "first_choice"
	state.story.nodes.first_choice.choices[0].effects.trust = 1.5
	check(not state.choose(0) and state.stats.trust == 0, "Fractional effects must not mutate stats")
	state = State.new()
	state.stats.qi = 101
	check(state.save_game("user://test_save.json"), "Long campaign stats should save")
	check(restored.load_game("user://test_save.json") and restored.stats.qi == 101, "Stats over 100 should round trip")
	state.current = "first_choice"
	state.stats.trust = state.MAX_STAT
	snapshot_stats = state.stats.duplicate()
	check(not state.choose(0) and state.stats == snapshot_stats, "Overflowing effects must fail atomically")
	state = State.new()
	state.current = "ending_shared"
	check(state.advance() and state.current == "lantern_shared", "Book I ending should retain its continuation into Book II")

	var continuations := {
		"ending_crossing": "river_from_crossing",
		"ending_bell": "river_from_bell",
		"ending_seed": "river_from_seed",
		"ending_ledger": "river_from_ledger"
	}
	for ending in continuations:
		var continuation_state = State.new()
		continuation_state.current = ending
		continuation_state.stats.trust = 7
		check(continuation_state.advance(), "Every valley settlement should continue")
		check(continuation_state.current == continuations[ending], "Settlement must keep its own spring opening")
		check(continuation_state.stats.trust == 7 and continuation_state.history.back().text == continuation_state.story.nodes[ending].text, "Continuations must preserve stats and prior ending prose")
		check(continuation_state.save_game("user://test_save.json"), "Third-book checkpoint should save")
		var continuation_restore = State.new()
		check(continuation_restore.load_game("user://test_save.json") and continuation_restore.current == continuations[ending], "Third-book checkpoint should round trip")
		check(continuation_restore.advance() and continuation_restore.current == "river_arrival", "Every opening must reach the same spring landing")

	# Stats are monotone. Values above the greatest gate are equivalent for
	# reachability; arithmetic overflow is checked separately above.
	var campaign: Dictionary = State.new().story
	var caps := {"qi": 0, "trust": 0, "insight": 0, "resolve": 0}
	var expected_endings := {}
	for scene_node in campaign.nodes.values():
		if scene_node.has("ending"):
			expected_endings[scene_node.ending] = true
		for choice in scene_node.get("choices", []):
			for key in choice.get("requires", {}):
				caps[key] = maxi(caps[key], int(choice.requires[key]))
			for effect in choice.get("effects", {}).values():
				check(effect >= 0, "Capped traversal requires monotone stat effects")
	var reached := {}
	var endings := {}
	var visited := {}
	var queue: Array = [{"current": campaign.start, "stats": {"qi": 0, "trust": 0, "insight": 0, "resolve": 0}}]
	var cursor := 0
	while cursor < queue.size():
		var entry: Dictionary = queue[cursor]
		cursor += 1
		var visit_key := str(entry.current)
		for key in State.STAT_KEYS:
			entry.stats[key] = mini(int(entry.stats[key]), int(caps[key]))
			visit_key += ":" + str(entry.stats[key])
		if visited.has(visit_key):
			continue
		visited[visit_key] = true
		var traveler = State.new(campaign)
		traveler.current = entry.current
		traveler.stats = entry.stats.duplicate()
		reached[traveler.current] = true
		var node: Dictionary = traveler.node()
		if node.has("ending"):
			endings[node.ending] = true
		if node.has("next") or node.has("continuation"):
			if traveler.advance():
				queue.append({"current": traveler.current, "stats": traveler.stats.duplicate()})
		else:
			for index in range(node.get("choices", []).size()):
				var branch = State.new(campaign)
				branch.current = entry.current
				branch.stats = entry.stats.duplicate()
				if branch.choose(index):
					queue.append({"current": branch.current, "stats": branch.stats.duplicate()})
	check(reached.size() == campaign.nodes.size(), "Every scene should be reachable under its gates")
	check(endings == expected_endings, "Every authored ending should be reachable")
	print("Reachable scenes: %d; distinct capped states: %d" % [reached.size(), visited.size()])
	DirAccess.remove_absolute("user://test_save.json")
	DirAccess.remove_absolute("user://bad_save.json")
	if failures.is_empty():
		print("JADE_VOW_STORY_TESTS_OK: all routes, gates and save validation")
	quit(0 if failures.is_empty() else 1)
