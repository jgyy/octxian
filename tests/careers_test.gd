extends SceneTree

const State = preload("res://scripts/story_state.gd")
const SAVE_PATH := "user://careers_test.json"
const CAREERS := ["kiln", "archive", "survey", "independent"]
const ENTRIES := ["career_kiln_entry", "career_archive_entry", "career_survey_entry", "career_independent_entry"]
var failures: Array[String] = []
var covered: Dictionary = {}
var checked_rewards: Dictionary = {}
var tested_paths := 0

func check(condition: bool, message: String) -> void:
	if not condition:
		failures.append(message)
		push_error(message)

func clear_save() -> void:
	for suffix in ["", ".bak", ".tmp"]:
		if FileAccess.file_exists(SAVE_PATH + suffix):
			DirAccess.remove_absolute(SAVE_PATH + suffix)

func copy_state(original):
	var copied = State.new(original.story)
	copied.current = original.current
	copied.stats = original.stats.duplicate()
	copied.history = original.history.duplicate(true)
	copied.journey_seed = original.journey_seed
	copied.encounters = original.encounters.duplicate(true)
	copied.decisions = original.decisions.duplicate(true)
	copied.completed_practice = original.completed_practice.duplicate(true)
	return copied

func round_trip(original):
	check(original.save_game(SAVE_PATH), "Career checkpoint must save: " + original.current)
	var restored = State.new(original.story)
	check(restored.load_game(SAVE_PATH), "Career checkpoint must load: " + original.current)
	check(restored.current == original.current and restored.stats == original.stats, "Career checkpoints must retain the scene and attributes")
	check(restored.decisions == original.decisions and restored.completed_practice == original.completed_practice, "Career checkpoints must retain enrollment and completed work")
	check(restored.history == original.history, "Career checkpoints must retain the actual work journal")
	return restored

func walk_to(traveler, target: String, limit: int = 1000) -> bool:
	var steps := 0
	while traveler.current != target and steps < limit:
		var moved := false
		if traveler.node().has("choices") and not traveler.node().get("random_event", false):
			for index in range(traveler.node().choices.size()):
				if traveler.can_choose(traveler.node().choices[index]):
					moved = traveler.choose(index)
					break
		else:
			moved = traveler.advance()
		if not moved:
			return false
		steps += 1
	return traveler.current == target

func test_portfolio(completed, career: String) -> void:
	var traveler = round_trip(completed)
	var expected_entry := "career_%s_entry" % career
	var portfolio := "career_portfolio_%s_01" % career
	check(walk_to(traveler, portfolio), "Saved enrollment must select its authored portfolio: " + career)
	check(traveler.decisions.get("career_enrol_choice", "") == expected_entry, "The portfolio must retain its original enrolled profession")
	var reviewed_stats: Dictionary = traveler.stats.duplicate()
	traveler = round_trip(traveler)
	check(walk_to(traveler, "career_next_choice"), "Every portfolio must offer the next career decision")
	check(traveler.stats == reviewed_stats, "A portfolio description cannot award unperformed work")
	var renewal := -1
	for index in range(traveler.node().get("choices", []).size()):
		if traveler.node().choices[index].get("next", "") == "career_renew_dispatch":
			renewal = index
	check(renewal >= 0, "The next decision must offer an actual renewal request")
	if renewal < 0:
		return
	check(traveler.choose(renewal), "Every profession must be able to request its bounded renewal")
	traveler = round_trip(traveler)
	check(walk_to(traveler, "career_renew_%s_01" % career), "Saved enrollment must select its own renewal terms: " + career)
	check(traveler.stats == reviewed_stats, "Requesting renewal cannot award a completed shift")
	check(traveler.decisions.get("career_enrol_choice", "") == expected_entry, "Renewal must preserve the selected profession")
	tested_paths += 1

func test_reward(traveler, scene_id: String, earned: Dictionary, previous_stats: Dictionary, previously_completed: bool) -> void:
	var expected := previous_stats.duplicate()
	if not previously_completed:
		for key in earned:
			expected[key] = int(expected[key]) + int(earned[key])
	check(traveler.stats == expected, "Only leaving actual completed work may grant its authored credit: " + scene_id)
	check(traveler.completed_practice.has(scene_id), "Actual completed career work must be recorded: " + scene_id)
	if checked_rewards.has(scene_id):
		return
	checked_rewards[scene_id] = true
	var repeated = round_trip(traveler)
	repeated.current = scene_id
	var before_repeat: Dictionary = repeated.stats.duplicate()
	check(repeated.advance() and repeated.stats == before_repeat, "Saved completed work cannot pay twice on revisit: " + scene_id)

func test_profession(campaign: Dictionary, selection: int) -> void:
	var enrolled = State.new(campaign)
	enrolled.current = "career_enrol_choice"
	enrolled.stats = {"qi": 10, "trust": 10, "insight": 10, "resolve": 10}
	var initial_stats: Dictionary = enrolled.stats.duplicate()
	check(enrolled.choose(selection) and enrolled.current == ENTRIES[selection], "Enrollment must select the actual requested career")
	check(enrolled.stats == initial_stats and enrolled.completed_practice.is_empty(), "Enrollment cannot award unperformed training")
	enrolled = round_trip(enrolled)
	var committed = copy_state(enrolled)
	committed.current = "career_enrol_choice"
	var prior_decisions: Dictionary = committed.decisions.duplicate()
	check(not committed.choose((selection + 1) % ENTRIES.size()), "An existing career commitment cannot silently switch professions")
	check(committed.current == "career_enrol_choice" and committed.stats == initial_stats and committed.decisions == prior_decisions, "Rejected enrollment switches must be atomic")
	var queue: Array = [enrolled]
	var seen: Dictionary = {}
	var cursor := 0
	var completed_paths := 0
	while cursor < queue.size() and cursor < 20000:
		var traveler = queue[cursor]
		cursor += 1
		if traveler.current == "career_reunion_01":
			test_portfolio(traveler, CAREERS[selection])
			completed_paths += 1
			continue
		var visit := JSON.stringify([traveler.current, traveler.stats, traveler.decisions, traveler.completed_practice])
		if seen.has(visit):
			continue
		seen[visit] = true
		var scene_id: String = traveler.current
		covered[scene_id] = true
		var scene: Dictionary = traveler.node()
		check(scene.get("cultivation", {}) == {"realm": "qi_gathering", "stage": "5: Four pairs"}, "Career qualifications cannot manufacture a cultivation breakthrough: " + scene_id)
		if scene.has("choices") and not scene.get("random_event", false):
			var available := 0
			for index in range(scene.choices.size()):
				if not traveler.can_choose(scene.choices[index]):
					continue
				var branch = copy_state(traveler)
				var before: Dictionary = branch.stats.duplicate()
				check(branch.choose(index), "An available career training choice must progress: " + scene_id)
				check(branch.stats == before, "Selecting a lesson or specialty cannot award its uncompleted practice: " + scene_id)
				queue.append(branch)
				available += 1
			check(available > 0, "Every career decision must retain an available method: " + scene_id)
		else:
			var before: Dictionary = traveler.stats.duplicate()
			var previously_completed: bool = traveler.completed_practice.has(scene_id)
			var earned: Dictionary = scene.get("earned", {})
			var moved: bool = traveler.advance()
			check(moved, "Every career shift must reach its next authored scene: " + scene_id)
			if not moved:
				continue
			if earned.is_empty():
				check(traveler.stats == before, "Uncredited career scenes cannot award practice: " + scene_id)
			else:
				test_reward(traveler, scene_id, earned, before, previously_completed)
			queue.append(traveler)
	check(cursor < 20000, "Career training coverage must remain finite")
	check(completed_paths > 0, "Every enrolled profession must complete at least one actual training path")
	var untrained = State.new(campaign)
	untrained.current = "career_enrol_choice"
	check(untrained.can_choose(untrained.node().choices[selection]), "Zero attribute scores must still allow enrollment in every career")
	check(untrained.choose(selection), "Untrained aspirants must be able to enter supervised work")
	check(walk_to(untrained, "career_reunion_01"), "Every career must retain a complete supervised route for an untrained aspirant")
	test_portfolio(untrained, CAREERS[selection])

func _initialize() -> void:
	clear_save()
	var campaign: Dictionary = State.new().story
	check(campaign.chapters.has("book_xx_careers"), "The delivered campaign must load the career chapter")
	var continuation = State.new(campaign)
	continuation.current = "crossing_final_common"
	check(continuation.advance() and continuation.current == "career_entry", "Reed Crossing must continue into the actual career chapter")
	check(walk_to(continuation, "career_enrol_choice"), "The career opening must reach enrollment")
	check(continuation.node().get("choices", []).size() == 4, "Enrollment must offer three professions and independent work")
	for selection in range(CAREERS.size()):
		test_profession(campaign, selection)
	for scene_id in campaign.nodes:
		for career in CAREERS:
			if scene_id.begins_with("career_%s_" % career):
				check(covered.has(scene_id), "Every authored career training scene must be reachable: " + scene_id)
		if scene_id.begins_with("career_") and campaign.nodes[scene_id].has("earned"):
			check(checked_rewards.has(scene_id), "Every authored career practice credit must be exercised: " + scene_id)
	var legacy = State.new(campaign)
	legacy.current = "career_reunion_01"
	check(walk_to(legacy, "career_portfolio_independent_01"), "A checkpoint without enrollment cannot claim a guild qualification")
	check(legacy.decisions.is_empty() and legacy.completed_practice.is_empty() and legacy.stats == {"qi": 0, "trust": 0, "insight": 0, "resolve": 0}, "Legacy fallback cannot invent enrollment or completed work")
	legacy.current = "career_renew_dispatch"
	check(legacy.advance() and legacy.current == "career_renew_independent_01", "Renewal without a recorded enrollment must retain the independent fallback")
	clear_save()
	if failures.is_empty():
		print("JADE_VOW_CAREERS_TESTS_OK: %d training paths; %d completion rewards; saved portfolios and bounded renewals" % [tested_paths, checked_rewards.size()])
	quit(0 if failures.is_empty() else 1)
