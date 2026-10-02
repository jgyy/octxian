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
	check(state.story.nodes.size() == 102, "Opening and Book II scenes should load")
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

	var reached := {}
	var endings := {}
	var visited := {}
	var queue: Array = [{"current": "arrival", "stats": {"qi": 0, "trust": 0, "insight": 0, "resolve": 0}}]
	while not queue.is_empty():
		var entry: Dictionary = queue.pop_front()
		var visit_key := str(entry.current) + JSON.stringify(entry.stats)
		if visited.has(visit_key):
			continue
		visited[visit_key] = true
		var traveler = State.new()
		traveler.current = entry.current
		traveler.stats = entry.stats.duplicate()
		reached[traveler.current] = true
		var node: Dictionary = traveler.node()
		if node.has("ending"):
			endings[node.ending] = true
			if node.has("continuation") and traveler.advance():
				queue.append({"current": traveler.current, "stats": traveler.stats.duplicate()})
		elif node.has("next"):
			if traveler.advance():
				queue.append({"current": traveler.current, "stats": traveler.stats.duplicate()})
		else:
			for index in range(node.get("choices", []).size()):
				var branch = State.new()
				branch.current = entry.current
				branch.stats = entry.stats.duplicate()
				if branch.choose(index):
					queue.append({"current": branch.current, "stats": branch.stats.duplicate()})
	check(reached.size() == state.story.nodes.size(), "Every scene should be reachable")
	check(endings.size() == 7, "All three opening and four Book II endings should be reachable")
	DirAccess.remove_absolute("user://test_save.json")
	DirAccess.remove_absolute("user://bad_save.json")
	if failures.is_empty():
		print("JADE_VOW_STORY_TESTS_OK: all routes, gates and save validation")
	quit(0 if failures.is_empty() else 1)
