extends SceneTree

const State = preload("res://scripts/story_state.gd")
const SAVE_PATH := "user://consequences_test_save.json"
const BAD_PATH := "user://consequences_test_bad.json"
var failures: Array[String] = []

func check(condition: bool, message: String) -> void:
	if not condition:
		failures.append(message)
		push_error(message)

func _campaign() -> Dictionary:
	return {
		"start": "fork", "characters": {"narrator": {"name": "Narrator"}},
		"nodes": {
			"fork": {"speaker": "narrator", "text": "One boat, two urgent tasks.", "choices": [
				{"text": "Shelter the witness.", "next": "shelter"},
				{"text": "Secure the original evidence.", "next": "evidence"}
			]},
			"shelter": {"speaker": "narrator", "text": "You move the witness before the flood.", "next": "regroup"},
			"evidence": {"speaker": "narrator", "text": "You move the records before the flood.", "next": "regroup"},
			"regroup": {"speaker": "narrator", "text": "Both routes meet at the courthouse.", "next": "reckoning"},
			"reckoning": {"speaker": "narrator", "text": "The hearing opens days later.", "next": "unknown", "routes": [
				{"decision": "fork", "selected": "shelter", "next": "witness"},
				{"decision": "fork", "selected": "evidence", "next": "records"}
			]},
			"witness": {"speaker": "narrator", "text": "The witness lives; the original records were lost.", "next": "ending"},
			"records": {"speaker": "narrator", "text": "The records survived; no witness can testify.", "next": "ending"},
			"unknown": {"speaker": "narrator", "text": "The older checkpoint does not establish either result.", "next": "ending"},
			"ending": {"speaker": "narrator", "text": "The hearing closes.", "ending": true},
			"ordinary": {"speaker": "narrator", "text": "An ordinary attribute-gated choice.", "choices": [
				{"text": "Study the ward.", "next": "regroup", "requires": {"qi": 5}, "effects": {"insight": 1}}
			]},
			"practice": {"speaker": "narrator", "text": "A completed practice scene.", "earned": {"qi": 1}, "next": "regroup"},
			"chance": {"speaker": "narrator", "text": "Weather changes without a player decision.", "random_event": true, "choices": [
				{"text": "Clear weather.", "next": "shelter"}, {"text": "Rain.", "next": "evidence"}
			]}
		}
	}

func _snapshot(state) -> Dictionary:
	return {
		"current": state.current, "stats": state.stats.duplicate(true),
		"history": state.history.duplicate(true), "decisions": state.decisions.duplicate(true),
		"journey_seed": state.journey_seed, "encounters": state.encounters.duplicate(true),
		"completed_practice": state.completed_practice.duplicate(true),
		"recovered_checkpoint": state.recovered_checkpoint
	}

func _payload(state) -> Dictionary:
	return {
		"version": 1, "current": state.current, "stats": state.stats.duplicate(true),
		"history": state.history.duplicate(true), "decisions": state.decisions.duplicate(true),
		"journey_seed": state.journey_seed, "encounters": state.encounters.duplicate(true),
		"completed_practice": state.completed_practice.duplicate(true), "practice_rules": 3
	}

func _write_checkpoint(path: String, payload: Dictionary) -> bool:
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		return false
	file.store_string(JSON.stringify(payload))
	var result := file.get_error()
	file.close()
	return result == OK

func _clear_checkpoint(path: String) -> void:
	for suffix in ["", ".bak", ".tmp"]:
		if FileAccess.file_exists(path + suffix):
			DirAccess.remove_absolute(path + suffix)

func _walk_to_hearing(state, index: int) -> bool:
	return state.choose(index) and state.advance() and state.advance() and state.current == "reckoning"

func _test_delayed_consequences() -> void:
	var shelter = State.new(_campaign())
	var evidence = State.new(_campaign())
	check(_walk_to_hearing(shelter, 0) and _walk_to_hearing(evidence, 1), "Both commitments must reach the same later hearing")
	check(shelter.stats == evidence.stats, "Delayed consequences must distinguish journeys with identical attributes")
	check(shelter.decisions == {"fork": "shelter"} and evidence.decisions == {"fork": "evidence"}, "Decisions must record source scene and destination rather than an option index")
	check(shelter.advance() and evidence.advance(), "Both delayed consequences must be playable")
	check(shelter.current == "witness" and evidence.current == "records", "Earlier commitments must change the later people and evidence available")
	check(shelter.stats == evidence.stats and shelter.node().text != evidence.node().text, "Consequences must change story facts without requiring a stat difference")
	var precedence = State.new(_campaign())
	precedence.current = "reckoning"
	precedence.decisions = {"fork": "shelter", "ordinary": "regroup"}
	precedence.story.nodes.reckoning.routes = [
		{"decision": "ordinary", "selected": "regroup", "next": "records"},
		{"decision": "fork", "selected": "shelter", "next": "witness"}
	]
	check(precedence.advance() and precedence.current == "records", "When several valid records match, authored route order must select the first match")

func _test_saves_and_revisits() -> void:
	var state = State.new(_campaign())
	check(_walk_to_hearing(state, 0), "Consequence checkpoint setup must succeed")
	check(state.save_game(SAVE_PATH), "A decision-bearing checkpoint must save")
	var restored = State.new(_campaign())
	check(restored.load_game(SAVE_PATH) and restored.decisions == state.decisions, "Decision records must survive a version-one checkpoint round trip")
	check(restored.advance() and restored.current == "witness", "A restored decision must select the same delayed consequence")
	restored.current = "fork"
	var before := _snapshot(restored)
	check(not restored.can_choose(restored.node().choices[1]) and not restored.choose(1), "Revisiting a choice must not switch an established commitment")
	check(_snapshot(restored) == before, "A blocked commitment change must preserve every journey field")
	check(restored.can_choose(restored.node().choices[0]) and restored.choose(0), "Revisiting the same recorded destination must remain playable")
	check(restored.decisions == {"fork": "shelter"}, "Repeating a commitment must retain its original record")
	var reordered = State.new(_campaign())
	reordered.story.nodes.fork.choices.reverse()
	check(reordered.load_game(SAVE_PATH), "Choice order changes must not invalidate a destination-based checkpoint")
	reordered.current = "fork"
	check(not reordered.choose(0) and reordered.choose(1) and reordered.current == "shelter", "A reordered menu must keep the saved destination instead of the old option number")

	var other = State.new(_campaign())
	check(_walk_to_hearing(other, 1) and other.save_game(SAVE_PATH), "The next checkpoint must preserve the prior decision in its backup")
	DirAccess.remove_absolute(SAVE_PATH)
	var recovered = State.new(_campaign())
	check(recovered.load_game(SAVE_PATH) and recovered.recovered_checkpoint and recovered.decisions == {"fork": "shelter"}, "Backup recovery must retain the backed-up commitment")
	check(recovered.advance() and recovered.current == "witness", "Recovered checkpoints must preserve delayed consequences")

func _test_legacy_fallback() -> void:
	var state = State.new(_campaign())
	state.current = "reckoning"
	var old := _payload(state)
	old.erase("decisions")
	check(_write_checkpoint(BAD_PATH, old), "Legacy checkpoint setup must write")
	state.decisions = {"fork": "evidence"}
	check(state.load_game(BAD_PATH) and state.decisions.is_empty(), "A legacy checkpoint must clear prior in-memory decisions")
	check(state.advance() and state.current == "unknown", "A missing old commitment must follow the authored fallback without inventing a result")
	old.erase("journey_seed")
	old.erase("encounters")
	old.erase("completed_practice")
	old.erase("practice_rules")
	check(_write_checkpoint(BAD_PATH, old) and state.load_game(BAD_PATH), "Original version-one checkpoints must remain readable")
	check(state.advance() and state.current == "unknown", "Original checkpoints must retain the same consequence fallback")

func _test_invalid_saves_are_atomic() -> void:
	var state = State.new(_campaign())
	check(_walk_to_hearing(state, 0), "Invalid-save setup must establish a real commitment")
	state.stats.insight = 9
	state.encounters = {"chance": "shelter"}
	state.completed_practice = {"practice": true}
	state.recovered_checkpoint = true
	var before := _snapshot(state)
	var valid := _payload(state)
	var invalid_records: Array = [
		[], {"missing": "shelter"}, {"fork": "missing"}, {"fork": "records"},
		{"regroup": "reckoning"}, {"chance": "shelter"}, {"practice": "regroup"},
		{"fork": 0}, {"fork": true}, {"fork": null}
	]
	for invalid in invalid_records:
		var bad: Dictionary = valid.duplicate(true)
		bad.current = "evidence"
		bad.stats.insight = 0
		bad.journey_seed = 123
		bad.encounters = {}
		bad.completed_practice = {}
		bad.decisions = invalid
		check(_write_checkpoint(BAD_PATH, bad), "Malformed decision checkpoint must write")
		check(not state.load_game(BAD_PATH), "Invalid decision records must be rejected: " + JSON.stringify(invalid))
		check(_snapshot(state) == before, "A rejected decision checkpoint must preserve every journey field")
	var late_failure: Dictionary = valid.duplicate(true)
	late_failure.decisions = {"fork": "evidence"}
	late_failure.practice_rules = 999
	check(_write_checkpoint(BAD_PATH, late_failure) and not state.load_game(BAD_PATH), "A later validation failure must reject otherwise valid decisions")
	check(_snapshot(state) == before, "Decisions must not apply before the rest of checkpoint validation finishes")

func _test_invalid_routes_are_atomic() -> void:
	var valid_route := {"decision": "fork", "selected": "shelter", "next": "witness"}
	var invalid_routes: Array = [
		{}, [], [null], [{"decision": "fork", "selected": "shelter"}],
		[{"decision": "fork", "selected": "shelter", "next": 1}],
		[{"decision": "missing", "selected": "shelter", "next": "witness"}],
		[{"decision": "fork", "selected": "records", "next": "witness"}],
		[{"decision": "chance", "selected": "shelter", "next": "witness"}],
		[{"decision": "fork", "selected": "shelter", "next": "missing"}],
		[valid_route, valid_route],
		[valid_route, {"decision": "fork", "selected": "evidence", "next": "missing"}],
		[{"decision": "fork", "selected": "shelter", "next": "witness", "unexpected": true}]
	]
	for routes in invalid_routes:
		var state = State.new(_campaign())
		check(_walk_to_hearing(state, 0), "Malformed-route setup must establish a commitment")
		state.story.nodes.reckoning.routes = routes
		state.story.nodes.reckoning.earned = {"qi": 1}
		var before := _snapshot(state)
		check(not state.advance(), "Malformed routes must reject advance: " + JSON.stringify(routes))
		check(_snapshot(state) == before, "Invalid routes must preserve scene, attributes, journal, records and unearned practice")
	for invalid in ["records", "missing", 0, true]:
		var state = State.new(_campaign())
		state.current = "reckoning"
		state.decisions = {"fork": invalid}
		var before := _snapshot(state)
		check(not state.advance() and _snapshot(state) == before, "Invalid in-memory decisions must never activate a route or mutate the journey")
	var fallback = State.new(_campaign())
	fallback.current = "reckoning"
	fallback.decisions = {"fork": "shelter"}
	fallback.story.nodes.reckoning.next = "missing"
	var before := _snapshot(fallback)
	check(not fallback.advance() and _snapshot(fallback) == before, "An invalid fallback must reject even when a matching route exists")
	var malformed_options: Array = [
		{}, [], [null], [{"next": 1}], [{"next": "missing"}],
		[{"next": "shelter"}, {"next": "shelter"}]
	]
	for options in malformed_options:
		var source = State.new(_campaign())
		source.current = "reckoning"
		source.decisions = {"fork": "shelter"}
		source.story.nodes.fork.choices = options
		var snapshot := _snapshot(source)
		check(not source.advance() and _snapshot(source) == snapshot, "Malformed or ambiguous source choices must not activate a consequence")
	var overflow = State.new(_campaign())
	check(_walk_to_hearing(overflow, 0), "Earned consequence setup must establish a commitment")
	overflow.story.nodes.reckoning.earned = {"qi": 1}
	overflow.stats.qi = overflow.MAX_STAT
	before = _snapshot(overflow)
	check(not overflow.advance() and _snapshot(overflow) == before, "A valid route with overflowing earned credit must reject without applying any part of the transition")

func _test_existing_choice_behavior() -> void:
	var malformed = State.new(_campaign())
	malformed.story.nodes.fork.choices.append({"text": "Broken alternative.", "next": "missing"})
	var initial := _snapshot(malformed)
	check(not malformed.can_choose(malformed.node().choices[0]) and not malformed.choose(0) and _snapshot(malformed) == initial, "A malformed source must not create decision records that its own save reader rejects")
	var numeric = State.new(_campaign())
	numeric.story.nodes["123"] = {"speaker": "narrator", "text": "A numeric-looking ID."}
	numeric.story.nodes.fork.choices[0].next = 123
	initial = _snapshot(numeric)
	check(not numeric.choose(0) and _snapshot(numeric) == initial, "A numeric destination must not create a non-string decision record")
	var state = State.new(_campaign())
	state.current = "ordinary"
	var before := _snapshot(state)
	check(not state.choose(0) and _snapshot(state) == before, "An ordinary blocked choice must not create a decision record")
	state.stats.qi = 5
	check(state.choose(0) and state.current == "regroup" and state.stats.qi == 5 and state.stats.insight == 1, "Ordinary choices must retain existing attribute gates and effects")
	check(state.decisions == {"ordinary": "regroup"}, "Successful ordinary choices must record only their own source")
	state.current = "practice"
	check(state.advance() and state.stats.qi == 6 and state.completed_practice == {"practice": true}, "Practice must still award credit only after completing its scene")
	check(state.decisions == {"ordinary": "regroup"}, "Narrative transitions and practice must not create player decisions")
	state.current = "chance"
	check(not state.choose(0) and state.advance() and state.encounters.has("chance"), "Random encounters must retain their separate recorded-outcome behavior")
	check(state.decisions == {"ordinary": "regroup"}, "Random encounters must not masquerade as player commitments")

func _initialize() -> void:
	_clear_checkpoint(SAVE_PATH)
	_clear_checkpoint(BAD_PATH)
	_test_delayed_consequences()
	_test_saves_and_revisits()
	_test_legacy_fallback()
	_test_invalid_saves_are_atomic()
	_test_invalid_routes_are_atomic()
	_test_existing_choice_behavior()
	_clear_checkpoint(SAVE_PATH)
	_clear_checkpoint(BAD_PATH)
	if failures.is_empty():
		print("JADE_VOW_CONSEQUENCES_TESTS_OK")
		quit(0)
	else:
		print("%d consequence tests failed" % failures.size())
		quit(1)
