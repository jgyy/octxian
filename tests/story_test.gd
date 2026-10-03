extends SceneTree

const State = preload("res://scripts/story_state.gd")
const Attributes = preload("res://scripts/attributes.gd")
var failures: Array[String] = []

func check(condition: bool, message: String) -> void:
	if not condition:
		failures.append(message)
		push_error(message)

func _initialize() -> void:
	_test_attributes()
	_test_city_continuations()
	_test_city_settlements()
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

	var orchard_openings := {
		"ending_river_return": "orchard_from_return",
		"ending_river_stair": "orchard_from_stair",
		"ending_river_harbor": "orchard_from_harbor"
	}
	for ending in orchard_openings:
		var orchard = State.new()
		orchard.current = ending
		orchard.stats.trust = 101
		check(orchard.advance() and orchard.current == orchard_openings[ending], "Every river outcome must retain its distinct orchard opening")
		check(orchard.stats.trust == 101 and orchard.history.back().text == orchard.story.nodes[ending].text, "Book IV must preserve long-campaign attributes and prior ending prose")
		check(orchard.advance() and orchard.current == "orchard_arrival", "Every orchard opening must reach the healing hall")

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

func _test_attributes() -> void:
	var samples := [
		[0, 0, 3, 3, 0.0], [2, 0, 3, 1, 2.0 / 3.0],
		[3, 3, 6, 3, 0.0], [5, 3, 6, 1, 2.0 / 3.0],
		[6, 6, 10, 4, 0.0], [9, 6, 10, 1, 0.75],
		[10, 10, -1, 0, 1.0], [State.MAX_STAT, 10, -1, 0, 1.0]
	]
	for key in Attributes.KEYS:
		for sample in samples:
			var profile: Dictionary = Attributes.profile(key, sample[0])
			check(profile.value == sample[0], "Profiles must retain the full attribute value")
			check(profile.rank_minimum == sample[1] and profile.next_minimum == sample[2], "Attribute rank boundaries must match their thresholds")
			check(profile.remaining == sample[3] and is_equal_approx(profile.progress, sample[4]), "Rank progress and remaining points must agree")
			check(profile.rank == Attributes.profile(key, sample[1]).rank, "Values within a rank must retain the same rank")
			check(not str(profile.description).is_empty() and not str(profile.growth).is_empty(), "Every attribute must explain its meaning and growth")
		check(Attributes.profile(key, 2).rank != Attributes.profile(key, 3).rank, "Three points must advance the first rank")
		check(Attributes.profile(key, 5).rank != Attributes.profile(key, 6).rank, "Six points must advance the second rank")
		check(Attributes.profile(key, 9).rank != Attributes.profile(key, 10).rank, "Ten points must advance the final rank")

	var gated = State.new()
	gated.current = "first_choice"
	gated.stats = {"qi": 3, "trust": 0, "insight": 7, "resolve": 2}
	var choice := {
		"next": "trust",
		"effects": {"resolve": 1, "trust": 2, "qi": 1},
		"requires": {"resolve": 2, "trust": 1, "qi": 3}
	}
	gated.story.nodes.first_choice.choices[0] = choice
	var before_stats: Dictionary = gated.stats.duplicate()
	var before_history: Array = gated.history.duplicate(true)
	var details: Dictionary = gated.choice_details(choice)
	check(details.effects == PackedStringArray(["Qi +1", "Trust +2", "Resolve +1"]), "Effect previews must follow the canonical attribute order")
	check(details.requirements == PackedStringArray(["Qi 3/3", "Trust 0/1", "Resolve 2/2"]), "Requirements must display both satisfied and unmet thresholds")
	check(details.missing == PackedStringArray(["Trust 0/1"]), "Missing requirements must contain only unmet thresholds")
	check(not details.available and not gated.can_choose(choice) and not gated.choose(0), "Preview and application must agree on locked choices")
	check(gated.stats == before_stats and gated.history == before_history and gated.current == "first_choice", "Locked choices must preserve the journey")
	gated.stats.trust = 1
	before_stats = gated.stats.duplicate()
	details = gated.choice_details(choice)
	check(details.available and gated.can_choose(choice), "Meeting every requirement must enable the choice")
	check(gated.stats == before_stats, "Available previews must not apply their effects")
	check(gated.choose(0) and gated.current == "trust", "An available preview must permit the same transition")
	check(gated.stats == {"qi": 4, "trust": 3, "insight": 7, "resolve": 3} and gated.history.size() == 1, "Applied effects must match the preview and record one transition")

	for requirement in [[], "qi", {"unknown": 0}, {"qi": true}, {"qi": "1"}, {"qi": 1.5}, {"qi": INF}, {"qi": NAN}, {"qi": -1}, {"qi": State.MAX_STAT + 1}]:
		_check_attribute_choice_rejected({"next": "trust", "requires": requirement, "effects": {"trust": 1}}, "Malformed requirements must be rejected")
	for effect in [[], "qi", {"unknown": 1}, {"qi": true}, {"qi": "1"}, {"qi": 1.5}, {"qi": INF}, {"qi": NAN}, {"qi": 1, "trust": -1}]:
		_check_attribute_choice_rejected({"next": "trust", "effects": effect}, "Malformed or underflowing effects must be rejected")
	_check_attribute_choice_rejected({"next": "missing", "effects": {"qi": 1}}, "Missing destinations must disable the preview")
	_check_attribute_choice_rejected({"next": "trust", "effects": {"qi": 1}}, "Overflow must disable the preview", {"qi": State.MAX_STAT})

	var spending = State.new()
	spending.current = "first_choice"
	spending.stats.qi = 1
	spending.story.nodes.first_choice.choices[0] = {"next": "trust", "effects": {"trust": 2, "qi": -1}}
	check(spending.choice_details(spending.node().choices[0]).effects == PackedStringArray(["Qi -1", "Trust +2"]), "Valid decreases must have an accurate signed preview")
	check(spending.choose(0) and spending.stats.qi == 0 and spending.stats.trust == 2, "Valid decreases must remain playable")

	var legacy_path := "user://attribute_legacy_test.json"
	var legacy_stats := {"qi": State.MAX_STAT, "trust": 101, "insight": 6, "resolve": 10}
	var legacy_file := FileAccess.open(legacy_path, FileAccess.WRITE)
	legacy_file.store_string(JSON.stringify({"version": 1, "current": "first_choice", "stats": legacy_stats, "history": []}))
	legacy_file.close()
	var legacy = State.new()
	check(legacy.load_game(legacy_path) and legacy.stats == legacy_stats, "Version-1 saves must preserve long campaign values exactly")
	check(legacy.save_game(legacy_path), "Loaded attribute values must remain saveable")
	var round_trip = State.new()
	check(round_trip.load_game(legacy_path) and round_trip.stats == legacy_stats, "Ranks must not clamp persisted values")
	DirAccess.remove_absolute(legacy_path)

func _check_attribute_choice_rejected(choice: Dictionary, message: String, starting_stats: Dictionary = {}) -> void:
	var state = State.new()
	state.current = "first_choice"
	state.stats.merge(starting_stats, true)
	state.story.nodes.first_choice.choices[0] = choice
	var before_stats: Dictionary = state.stats.duplicate()
	var before_history: Array = state.history.duplicate(true)
	var details: Dictionary = state.choice_details(choice)
	check(not details.available and not str(details.reason).is_empty(), message + ": explain why")
	check(not state.can_choose(choice), message + ": disable selection")
	check(not state.choose(0), message + ": refuse application")
	check(state.current == "first_choice" and state.stats == before_stats and state.history == before_history, message + ": preserve scene, stats and journal")

func _test_city_continuations() -> void:
	var openings := {
		"ending_orchard_breath": "city_from_breath",
		"ending_orchard_care": "city_from_care",
		"ending_orchard_funds": "city_from_funds",
		"ending_orchard_pause": "city_from_pause"
	}
	var expected_stats := {"qi": 101, "trust": 202, "insight": 303, "resolve": 404}
	for ending in openings:
		var traveler = State.new()
		traveler.current = ending
		traveler.stats = expected_stats.duplicate()
		check(traveler.advance() and traveler.current == openings[ending], "Every orchard settlement must retain its own city opening")
		check(traveler.stats == expected_stats, "Continuing into Book V must preserve every long-campaign attribute")
		check(not traveler.history.is_empty() and traveler.history.back().text == traveler.story.nodes[ending].text, "The previous settlement prose must remain in the city journal")
		var expected_history: Array = traveler.history.duplicate(true)
		check(traveler.save_game("user://city_checkpoint.json"), "A city continuation checkpoint must save")
		var restored = State.new()
		check(restored.load_game("user://city_checkpoint.json"), "A city continuation checkpoint must load")
		check(restored.current == openings[ending] and restored.stats == expected_stats and restored.history == expected_history, "Book V saves must preserve the selected opening, attributes and prior outcome")
		check(restored.advance() and restored.current == "city_arrival", "Every city opening must reach the same market without repeating an orchard settlement")
	DirAccess.remove_absolute("user://city_checkpoint.json")

func _test_city_settlements() -> void:
	var gates := ["qi", "insight", "trust"]
	var destinations := ["city_credit_bridge", "city_separate_ledgers", "city_license_pool", "city_batch_audit"]
	var ending_nodes := ["ending_city_credit", "ending_city_ledgers", "ending_city_pool", "ending_city_audit"]
	for index in range(4):
		var traveler = State.new()
		traveler.current = "city_final_choice"
		if index < gates.size():
			traveler.stats[gates[index]] = 2
			var before_stats: Dictionary = traveler.stats.duplicate()
			var before_history: Array = traveler.history.duplicate(true)
			check(not traveler.can_choose(traveler.node().choices[index]) and not traveler.choose(index), "The city settlement gate must reject a value below its threshold")
			check(traveler.current == "city_final_choice" and traveler.stats == before_stats and traveler.history == before_history, "A blocked city settlement must preserve stats, prose and location")
			traveler.stats[gates[index]] = 3
		else:
			for locked in range(3):
				check(not traveler.can_choose(traveler.node().choices[locked]), "Specialized city settlements must be locked at zero attributes")
		check(traveler.choose(index) and traveler.current == destinations[index], "Every city settlement must be playable at its own threshold, including the untrained audit")
		var steps := 0
		while not traveler.node().has("ending") and steps < 12:
			if not traveler.advance():
				break
			steps += 1
		check(traveler.current == ending_nodes[index] and traveler.node().has("ending"), "Each city settlement must reach its distinct ending without another gated decision")

	var investigation = State.new()
	investigation.current = "city_investigation_choice"
	var expected_entries := ["city_mask_entry", "city_registry_entry", "city_perfumer_entry"]
	for index in range(expected_entries.size()):
		check(investigation.can_choose(investigation.node().choices[index]), "Every city investigation must remain available at zero attributes")
		var branch = State.new()
		branch.current = investigation.current
		check(branch.choose(index) and branch.current == expected_entries[index], "The city hub must open the selected investigation")
