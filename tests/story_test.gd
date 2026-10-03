extends SceneTree

const State = preload("res://scripts/story_state.gd")
const Attributes = preload("res://scripts/attributes.gd")
const StoryData = preload("res://scripts/story_data.gd")
var failures: Array[String] = []

# Exercise backend failures without requiring a full disk or a Windows runner.
class IncompleteCheckpointState:
	extends "res://scripts/story_state.gd"

	func _read_checkpoint_file(path: String) -> Dictionary:
		var result: Dictionary = super._read_checkpoint_file(path)
		if path.ends_with(".tmp") and result.ok and not result.bytes.is_empty():
			var truncated: PackedByteArray = result.bytes
			truncated.resize(truncated.size() - 1)
			result.bytes = truncated
		return result

class RenameFailureState:
	extends "res://scripts/story_state.gd"

	var fail_restore := false
	var commit_attempts := 0

	func _commit_checkpoint(temporary_path: String, path: String) -> int:
		commit_attempts += 1
		if commit_attempts == 1 or fail_restore:
			# Match the Windows edge: the destination is removed before move fails.
			if FileAccess.file_exists(path):
				DirAccess.remove_absolute(path)
			return FAILED
		return super._commit_checkpoint(temporary_path, path)

func check(condition: bool, message: String) -> void:
	if not condition:
		failures.append(message)
		push_error(message)

func _initialize() -> void:
	_test_story_loading()
	_test_attributes()
	_test_atomic_saves()
	_test_duplicate_json_keys()
	_test_ring_campaign()
	_test_city_continuations()
	_test_city_settlements()
	_test_court_continuations()
	_test_court_routes_and_remedies()
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
	_remove_checkpoint("user://test_save.json")
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
	_remove_checkpoint(legacy_path)

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
	_remove_checkpoint("user://city_checkpoint.json")

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


func _test_story_loading() -> void:
	var loaded := StoryData.load_campaign()
	check(loaded.error.is_empty() and loaded.story.nodes.has("arrival"), "The complete book manifest must load atomically")
	var injected := {
		"start": "fixture", "characters": {"narrator": {"name": "Narrator"}},
		"chapters": {}, "nodes": {"fixture": {"speaker": "narrator", "text": "Injected traversal prose.", "ending": "fixture"}},
		"books": ["data/books/intentionally_missing.json"]
	}
	var traveler = State.new(injected)
	check(traveler.current == "fixture" and traveler.story.nodes.size() == 1, "Injected merged campaigns must bypass disk loading")
	var missing := StoryData.load_campaign("user://missing_story_fixture.json")
	check(not missing.error.is_empty() and missing.story.is_empty(), "Missing campaigns must not produce partial stories")
	var fixture_path := "user://invalid_story_fixture.json"
	var file := FileAccess.open(fixture_path, FileAccess.WRITE)
	file.store_string(JSON.stringify({"start": "fixture", "characters": {}, "chapters": {}, "nodes": {"fixture": {}}, "books": ["data/books/../escape.json"]}))
	file.close()
	var unsafe := StoryData.load_campaign(fixture_path)
	check(not unsafe.error.is_empty() and unsafe.story.is_empty(), "Book manifests must reject path escapes before reading")
	file = FileAccess.open(fixture_path, FileAccess.WRITE)
	file.store_string("{malformed")
	file.close()
	var malformed := StoryData.load_campaign(fixture_path)
	check(not malformed.error.is_empty() and malformed.story.is_empty(), "Malformed campaign JSON must fail explicitly")
	DirAccess.remove_absolute(fixture_path)


func _test_court_continuations() -> void:
	var campaign: Dictionary = State.new().story
	check(campaign.chapters.has("book_vi"), "The delivered modular campaign must contain Book VI")
	check(campaign.get("books", []).has("data/books/book_vi.json"), "Book VI must be loaded through the explicit book manifest")
	var openings := {
		"ending_city_credit": "court_from_credit",
		"ending_city_ledgers": "court_from_ledgers",
		"ending_city_pool": "court_from_pool",
		"ending_city_audit": "court_from_audit"
	}
	var expected_stats := {"qi": 101, "trust": 202, "insight": 303, "resolve": 404}
	for ending in openings:
		var traveler = State.new(campaign)
		traveler.current = ending
		traveler.stats = expected_stats.duplicate()
		check(traveler.advance() and traveler.current == openings[ending], "Every city remedy must retain its own court opening")
		check(traveler.stats == expected_stats, "Book VI continuations must preserve every long-campaign attribute")
		check(traveler.history.size() == 1 and traveler.history.back().text == campaign.nodes[ending].text, "The selected city outcome must remain in the court journal")
		var expected_history: Array = traveler.history.duplicate(true)
		check(traveler.save_game("user://court_checkpoint.json"), "Modular court checkpoints must remain version-1 saves")
		var restored = State.new(campaign)
		check(restored.load_game("user://court_checkpoint.json"), "Modular court checkpoints must round trip")
		check(restored.current == openings[ending] and restored.stats == expected_stats and restored.history == expected_history, "Court saves must retain source-independent IDs, attributes and prior prose")
		check(restored.advance() and restored.current == "court_arrival", "Each route-specific court opening must reach the same cliff without repeating a city settlement")
	_remove_checkpoint("user://court_checkpoint.json")

func _test_court_routes_and_remedies() -> void:
	var campaign: Dictionary = State.new().story
	var entries := ["court_witness_entry", "court_rain_entry", "court_cost_entry", "court_docket_entry"]
	var gains := ["trust", "qi", "resolve", "insight"]
	for index in range(entries.size()):
		var traveler = State.new(campaign)
		traveler.current = "court_investigation_choice"
		check(traveler.node().choices.size() == 4, "Book VI must offer its four independent investigation teams")
		check(traveler.can_choose(traveler.node().choices[index]), "Every court investigation must be available without prior training")
		check(traveler.choose(index) and traveler.current == entries[index], "The court hub must open the selected investigation only")
		check(traveler.stats[gains[index]] == 1, "Joining a court inquiry must apply its declared attribute gain")
		var visited := {}
		var steps := 0
		while traveler.current != "court_findings" and steps < 500:
			visited[traveler.current] = true
			check(traveler.node().get("chapter") == "book_vi", "Court inquiries must remain in their authored chapter")
			if traveler.node().has("choices"):
				var chosen := false
				for option in range(traveler.node().choices.size()):
					if traveler.can_choose(traveler.node().choices[option]):
						chosen = traveler.choose(option)
						break
				check(chosen, "Every reached court inquiry decision must have an available route")
				if not chosen:
					break
			elif not traveler.advance():
				break
			steps += 1
		check(traveler.current == "court_findings", "Every finite court investigation must return to the common findings")
		for other in entries:
			if other != entries[index]:
				check(not visited.has(other), "Lin Yue must follow one court investigation rather than all four at once")
		steps = 0
		while traveler.current != "court_final_choice" and steps < 80:
			visited[traveler.current] = true
			if not traveler.advance():
				break
			steps += 1
		check(traveler.current == "court_final_choice", "Common reports and protections must precede every court remedy")
		for required in ["court_witness_report", "court_rain_report", "court_cost_report", "court_docket_report", "court_scope_test", "court_no_cause_verdict", "court_public_rights", "court_remaining_fund", "court_permission_review", "court_failure_clause"]:
			check(visited.has(required), "Selected inquiries must still receive all bounded findings and unconditional protections: " + required)
		check(traveler.can_choose(traveler.node().choices[3]), "The dated remand must remain available after every investigation")

	var gates := ["qi", "trust", "insight"]
	var destinations := ["court_weather_proposal", "court_local_proposal", "court_staged_proposal", "court_remand_proposal"]
	var endings := ["ending_court_weather", "ending_court_local", "ending_court_staged", "ending_court_remand"]
	var expected_after := [
		{"qi": 5, "trust": 0, "insight": 1, "resolve": 0},
		{"qi": 0, "trust": 5, "insight": 0, "resolve": 1},
		{"qi": 0, "trust": 1, "insight": 5, "resolve": 0},
		{"qi": 0, "trust": 0, "insight": 0, "resolve": 2}
	]
	for index in range(destinations.size()):
		var traveler = State.new(campaign)
		traveler.current = "court_final_choice"
		check(traveler.node().choices.size() == 4, "The finite court fund must offer four bounded remedy plans")
		if index < gates.size():
			traveler.stats[gates[index]] = 3
			var before_stats: Dictionary = traveler.stats.duplicate()
			var before_history: Array = traveler.history.duplicate(true)
			check(not traveler.can_choose(traveler.node().choices[index]) and not traveler.choose(index), "A court remedy must reject attributes below its four-point threshold")
			check(traveler.current == "court_final_choice" and traveler.stats == before_stats and traveler.history == before_history, "A rejected court remedy must preserve the journey atomically")
			traveler.stats[gates[index]] = 4
		else:
			for locked in range(gates.size()):
				check(not traveler.can_choose(traveler.node().choices[locked]), "Specialized court remedies must stay locked at zero attributes")
		check(traveler.choose(index) and traveler.current == destinations[index], "Each court remedy must open at its stated threshold, including the ungated remand")
		check(traveler.stats == expected_after[index], "Court remedy gains must match their explicit playable design")
		var steps := 0
		while not traveler.node().has("ending") and steps < 12:
			if not traveler.advance():
				break
			steps += 1
		check(traveler.current == endings[index] and traveler.node().has("ending"), "Every bounded court remedy must reach its distinct authored outcome")

func _test_atomic_saves() -> void:
	var path := "user://atomic_save_test.json"
	var temporary_path := path + ".tmp"
	var backup_path := path + ".bak"
	_remove_checkpoint(path)
	var state = State.new()
	check(state.save_game(path), "The initial checkpoint must save")
	var original := FileAccess.get_file_as_string(path)
	check(not FileAccess.file_exists(temporary_path), "A completed save must leave no temporary file")
	state.current = "pendant"
	state.stats.trust = 7
	check(DirAccess.make_dir_absolute(temporary_path) == OK, "The write-failure fixture must block the temporary path")
	check(not state.save_game(path), "A blocked temporary write must report failure")
	check(DirAccess.dir_exists_absolute(temporary_path), "A blocked save must preserve the preexisting temporary-path directory")
	check(FileAccess.get_file_as_string(path) == original, "A failed replacement must preserve the previous checkpoint byte for byte")
	var restored = State.new()
	check(restored.load_game(path) and restored.current == "arrival" and restored.stats.trust == 0, "The preserved checkpoint must remain loadable")
	DirAccess.remove_absolute(temporary_path)

	var incomplete = IncompleteCheckpointState.new()
	incomplete.current = "pendant"
	check(not incomplete.save_game(path), "A truncated readback must reject a write even when flush reports success")
	check(FileAccess.get_file_as_string(path) == original and not FileAccess.file_exists(temporary_path), "Incomplete staged writes must preserve the checkpoint and remove the temporary file")

	check(DirAccess.make_dir_absolute(backup_path) == OK, "The backup-failure fixture must block the backup path")
	check(not state.save_game(path), "An unverified backup must prevent replacement of the primary checkpoint")
	check(FileAccess.get_file_as_string(path) == original, "A failed backup must preserve the existing primary checkpoint")
	DirAccess.remove_absolute(backup_path)
	check(state.save_game(path), "An existing checkpoint must be replaceable after a failed write")
	check(restored.load_game(path) and restored.current == "pendant" and restored.stats.trust == 7 and not restored.recovered_checkpoint, "A successful replacement must restore the new primary checkpoint")
	check(FileAccess.get_file_as_string(backup_path) == original, "Replacement must retain the complete previous checkpoint as a backup")
	check(not FileAccess.file_exists(temporary_path), "Replacing a checkpoint must consume its temporary file")

	var replacement := FileAccess.get_file_as_string(path)
	var rename_failure = RenameFailureState.new()
	rename_failure.current = "first_choice"
	check(not rename_failure.save_game(path), "A failed commit that removes the destination must report failure")
	check(rename_failure.commit_attempts == 2 and FileAccess.get_file_as_string(path) == replacement, "A failed commit must restore the previous primary from verified bytes")
	check(restored.load_game(path) and restored.current == "pendant" and not restored.recovered_checkpoint, "Restored primary checkpoints must remain loadable")

	var recovery_failure = RenameFailureState.new()
	recovery_failure.fail_restore = true
	recovery_failure.current = "first_choice"
	check(not recovery_failure.save_game(path), "Failed commit and recovery moves must report failure")
	check(not FileAccess.file_exists(path) and FileAccess.get_file_as_string(backup_path) == replacement, "Failed recovery must leave the verified backup intact")
	check(State.has_save(path), "The Continue control must recognize a recoverable backup")
	check(restored.load_game(path) and restored.current == "pendant" and restored.stats.trust == 7 and restored.recovered_checkpoint, "A missing primary must recover the previous checkpoint from its backup")
	check(not FileAccess.file_exists(temporary_path), "Failed recovery must clean up its staged file")

	var corrupt := FileAccess.open(path, FileAccess.WRITE)
	corrupt.store_string("{broken")
	corrupt.close()
	check(not restored.load_game(path) and restored.current == "pendant", "An existing corrupt primary must still fail without silently loading an older backup")
	_remove_checkpoint(path)

	var directory_path := "user://atomic_save_destination_test"
	check(DirAccess.make_dir_absolute(directory_path) == OK, "The rename-failure fixture must create a directory")
	check(not state.save_game(directory_path), "Replacing a directory must report a failed commit")
	check(DirAccess.dir_exists_absolute(directory_path), "A failed commit must preserve the destination directory")
	check(not FileAccess.file_exists(directory_path + ".tmp"), "A failed commit must clean up its temporary file")
	DirAccess.remove_absolute(directory_path)

func _remove_checkpoint(path: String) -> void:
	for suffix in ["", ".tmp", ".bak"]:
		DirAccess.remove_absolute(path + suffix)

func _test_duplicate_json_keys() -> void:
	var fixture_path := "user://duplicate_story_fixture.json"
	var malformed := [
		'{"chapters":{},"chapters":{}}',
		'{"nodes":{"scene":{"text":"first"},"scene":{"text":"second"}}}',
		'{"same":1,"\\u0073ame":2}',
		'{"records":[{"same":1,"same":2}]}'
	]
	for contents in malformed:
		var file := FileAccess.open(fixture_path, FileAccess.WRITE)
		file.store_string(contents)
		file.close()
		var result := StoryData._read(fixture_path)
		check(result.error.contains("duplicate JSON key") and result.story.is_empty(), "Duplicate JSON keys must fail before any story can be returned: " + contents)

	var valid := {
		"records": [{"same": 1}, {"same": 2}],
		"first": {"same": 3}, "second": {"same": 4},
		"text": 'Braces { } and commas, "quoted words" and \\paths remain prose.'
	}
	var serialized := JSON.stringify(valid)
	var file := FileAccess.open(fixture_path, FileAccess.WRITE)
	file.store_string(serialized)
	file.close()
	var loaded := StoryData._read(fixture_path)
	# JSON numbers decode as floats; compare against the same decoded types.
	var expected = JSON.parse_string(serialized)
	check(loaded.error.is_empty() and loaded.story == expected, "Distinct object scopes and quoted punctuation must remain valid JSON")
	DirAccess.remove_absolute(fixture_path)

func _test_ring_campaign() -> void:
	var campaign: Dictionary = State.new().story
	check(campaign.chapters.has("book_vii"), "The campaign must contain Book VII")
	check(campaign.get("books", []).has("data/books/book_vii.json"), "Book VII must load from the explicit manifest")
	var openings := {
		"ending_court_weather": "ring_from_weather",
		"ending_court_local": "ring_from_local",
		"ending_court_staged": "ring_from_staged",
		"ending_court_remand": "ring_from_remand"
	}
	var expected_stats := {"qi": 101, "trust": 202, "insight": 303, "resolve": 404}
	var checkpoint := "user://ring_checkpoint_test.json"
	for ending in openings:
		var traveler = State.new(campaign)
		traveler.current = ending
		traveler.stats = expected_stats.duplicate()
		check(traveler.advance() and traveler.current == openings[ending], "Every court outcome must retain its own ring opening")
		check(traveler.stats == expected_stats and traveler.history.size() == 1 and traveler.history.back().text == campaign.nodes[ending].text, "Ring continuations must preserve long-campaign attributes and the chosen court outcome")
		check(traveler.save_game(checkpoint), "A ring opening checkpoint must save")
		var restored = State.new(campaign)
		check(restored.load_game(checkpoint), "A ring opening checkpoint must load")
		check(restored.current == openings[ending] and restored.stats == expected_stats and restored.history == traveler.history, "Ring checkpoints must round trip the scene, attributes and journal")
		check(restored.advance() and restored.current == "ring_arrival", "Every ring opening must reach the shared arrival")
	_remove_checkpoint(checkpoint)

	var entries := ["ring_marsh_entry", "ring_archive_entry", "ring_road_entry"]
	var gains := ["qi", "insight", "trust"]
	for index in range(entries.size()):
		var traveler = State.new(campaign)
		traveler.current = "ring_investigation_choice"
		check(traveler.node().get("choices", []).size() == 3, "The ring investigation must offer three independent routes")
		check(traveler.can_choose(traveler.node().choices[index]), "Every ring investigation must be playable with zero attributes")
		check(traveler.choose(index) and traveler.current == entries[index] and traveler.stats[gains[index]] == 1, "The selected ring investigation must apply its stated gain and open its own route")
		var visited := {}
		var steps := 0
		while traveler.current != "ring_findings" and steps < campaign.nodes.size():
			check(not visited.has(traveler.current), "Ring investigations must not cycle: " + traveler.current)
			if visited.has(traveler.current):
				break
			visited[traveler.current] = true
			check(traveler.node().get("chapter") == "book_vii", "Ring investigations must stay in Book VII")
			if traveler.node().has("choices"):
				var chosen := false
				for option in range(traveler.node().choices.size()):
					if traveler.can_choose(traveler.node().choices[option]):
						chosen = traveler.choose(option)
						break
				check(chosen, "Every reached ring inquiry decision must have an available route: " + traveler.current)
				if not chosen:
					break
			elif not traveler.advance():
				break
			steps += 1
		check(traveler.current == "ring_findings", "Every ring investigation must return to the common findings")
		for other in entries:
			if other != entries[index]:
				check(not visited.has(other), "An investigation must follow only its selected route")

	var destinations := ["ring_return_proposal", "ring_custody_proposal", "ring_refusal_proposal"]
	var endings := ["ending_ring_return", "ending_ring_custody", "ending_ring_refusal"]
	for index in range(destinations.size()):
		var traveler = State.new(campaign)
		traveler.current = "ring_final_choice"
		var original_stats: Dictionary = traveler.stats.duplicate()
		check(traveler.node().get("choices", []).size() == 3, "Book VII must offer three resolutions")
		check(traveler.can_choose(traveler.node().choices[index]), "Every ring resolution must remain available at zero attributes")
		check(traveler.choose(index) and traveler.current == destinations[index] and traveler.stats == original_stats, "Ring resolutions must follow the selected proposal without hidden attribute changes")
		var steps := 0
		while not traveler.node().has("ending") and steps < campaign.nodes.size():
			if not traveler.advance():
				break
			steps += 1
		check(traveler.current == endings[index] and traveler.node().has("ending"), "Each ring resolution must reach its own authored outcome")
