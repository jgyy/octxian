extends SceneTree

const State = preload("res://scripts/story_state.gd")
const SAVE_PATH := "user://commissions_test.json"
const CHAPTER := "book_xxi_commissions"
const CAREERS := ["kiln", "archive", "survey", "independent"]
const TRAINING_ENTRIES := ["career_kiln_entry", "career_archive_entry", "career_survey_entry", "career_independent_entry"]
const ENTRIES := ["commission_kiln_entry", "commission_archive_entry", "commission_survey_entry", "commission_independent_entry"]
const PREVIOUS_ENDINGS := ["career_renew_kiln_02", "career_renew_archive_02", "career_renew_survey_02", "career_renew_independent_02", "career_home_02", "career_daywork_02"]
var failures: Array[String] = []
var covered: Dictionary = {}
var checked_rewards: Dictionary = {}
var checked_choices: Dictionary = {}
var checked_routes: Dictionary = {}
var tested_paths := 0
var tested_seeds := 0

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
	check(original.save_game(SAVE_PATH), "Commission checkpoint must save: " + original.current)
	var restored = State.new(original.story)
	check(restored.load_game(SAVE_PATH), "Commission checkpoint must load: " + original.current)
	check(restored.current == original.current and restored.stats == original.stats, "Commission checkpoints must retain the scene and earned attributes")
	check(restored.decisions == original.decisions and restored.completed_practice == original.completed_practice, "Commission checkpoints must retain actual choices and completed work")
	check(restored.history == original.history and restored.journey_seed == original.journey_seed and restored.encounters == original.encounters, "Commission checkpoints must retain the journal and journey")
	return restored

func projection(traveler, decision_ids: Array) -> Dictionary:
	var selected: Dictionary = {}
	for decision_id in decision_ids:
		selected[decision_id] = traveler.decisions.get(decision_id, "")
	return selected

func previous_decisions(campaign: Dictionary) -> Array:
	var dependencies: Dictionary = {}
	for scene_id in campaign.nodes:
		var scene: Dictionary = campaign.nodes[scene_id]
		if scene.get("chapter", "") != CHAPTER:
			continue
		for route in scene.get("routes", []):
			if not str(route.decision).begins_with("commission_"):
				dependencies[str(route.decision)] = true
	var result: Array = dependencies.keys()
	result.sort()
	return result

func walk_to(traveler, target: String, limit: int = 3000) -> bool:
	var steps := 0
	while traveler.current != target and steps < limit:
		if traveler.node().get("chapter", "") == CHAPTER:
			covered[traveler.current] = true
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

func training_seeds(campaign: Dictionary, selection: int, dependencies: Array) -> Array:
	var enrolled = State.new(campaign)
	enrolled.current = "career_enrol_choice"
	enrolled.stats = {"qi": 10, "trust": 10, "insight": 10, "resolve": 10}
	check(enrolled.choose(selection), "Actual training must enroll the requested profession")
	var seeds: Array = []
	var signatures: Dictionary = {}
	var queue: Array = [enrolled]
	var seen: Dictionary = {}
	var cursor := 0
	while cursor < queue.size() and cursor < 40000:
		var traveler = queue[cursor]
		cursor += 1
		if traveler.current == "commission_entry":
			var signature := JSON.stringify(projection(traveler, dependencies))
			if not signatures.has(signature):
				signatures[signature] = true
				seeds.append(round_trip(traveler))
			continue
		var visit := JSON.stringify([traveler.current, traveler.stats, traveler.decisions, traveler.completed_practice])
		if seen.has(visit):
			continue
		seen[visit] = true
		var scene: Dictionary = traveler.node()
		if scene.has("choices") and not scene.get("random_event", false):
			var available := 0
			for index in range(scene.choices.size()):
				if traveler.can_choose(scene.choices[index]):
					var branch = copy_state(traveler)
					check(branch.choose(index), "A real prior career decision must progress")
					queue.append(branch)
					available += 1
			check(available > 0, "Prior career training must retain an available route")
		else:
			var moved: bool = traveler.advance()
			check(moved, "Every completed prior career term must reach Book XXI: " + traveler.current)
			if moved:
				queue.append(traveler)
	check(cursor < 40000, "Prior training context enumeration must remain finite")
	check(not seeds.is_empty(), "Performed training must provide a commission checkpoint")
	return seeds

func expected_career(traveler) -> int:
	var recorded: String = traveler.decisions.get("career_enrol_choice", "")
	var index := TRAINING_ENTRIES.find(recorded)
	return index if index >= 0 else 3

func has_commission_work(traveler) -> bool:
	for scene_id in traveler.completed_practice:
		if str(scene_id).begins_with("commission_"):
			return true
	return false

func test_saved_choice(before, selected, decision_id: String, selection: int) -> void:
	var choice_key := "%s:%d" % [decision_id, selection]
	if checked_choices.has(choice_key):
		return
	checked_choices[choice_key] = true
	var restored = round_trip(selected)
	restored.current = decision_id
	var selected_target: String = selected.decisions[decision_id]
	var before_stats: Dictionary = restored.stats.duplicate()
	var before_practice: Dictionary = restored.completed_practice.duplicate(true)
	var before_decisions: Dictionary = restored.decisions.duplicate(true)
	var before_history: Array = restored.history.duplicate(true)
	for index in range(before.node().choices.size()):
		if before.node().choices[index].get("next", "") == selected_target:
			continue
		check(not restored.choose(index), "A saved commission decision cannot silently switch its committed method: " + decision_id)
		check(restored.current == decision_id and restored.stats == before_stats and restored.completed_practice == before_practice and restored.decisions == before_decisions and restored.history == before_history, "Rejected saved commission changes must be atomic")

func test_reward(traveler, scene_id: String, earned: Dictionary, before: Dictionary, was_completed: bool) -> void:
	var expected := before.duplicate()
	if not was_completed:
		for key in earned:
			expected[key] = int(expected[key]) + int(earned[key])
	check(traveler.stats == expected, "Only leaving performed commission work may grant its authored credit: " + scene_id)
	check(traveler.completed_practice.has(scene_id), "Performed commissioned work must be recorded: " + scene_id)
	if checked_rewards.has(scene_id):
		return
	checked_rewards[scene_id] = true
	var repeated = round_trip(traveler)
	repeated.current = scene_id
	var before_repeat: Dictionary = repeated.stats.duplicate()
	check(repeated.advance() and repeated.stats == before_repeat, "Saved completed commissioned work cannot award twice on revisit: " + scene_id)

func test_commissions(seed) -> void:
	tested_seeds += 1
	var original_enrollment: String = seed.decisions.get("career_enrol_choice", "")
	var queue: Array = [round_trip(seed)]
	var seen: Dictionary = {}
	var cursor := 0
	var completed_paths := 0
	while cursor < queue.size() and cursor < 250000:
		var traveler = queue[cursor]
		cursor += 1
		var visit := JSON.stringify([traveler.current, traveler.stats, traveler.decisions, traveler.completed_practice])
		if seen.has(visit):
			continue
		seen[visit] = true
		var scene_id: String = traveler.current
		var scene: Dictionary = traveler.node()
		check(scene.get("chapter", "") == CHAPTER, "Commission routes must stay in their authored chapter: " + scene_id)
		covered[scene_id] = true
		check(scene.get("cultivation", {}) == {"realm": "qi_gathering", "stage": "5: Four pairs"}, "Commission appointments cannot manufacture a cultivation breakthrough: " + scene_id)
		check(traveler.decisions.get("career_enrol_choice", "") == original_enrollment, "A commission must preserve the actual prior enrollment")
		if ENTRIES.has(scene_id):
			check(scene_id == ENTRIES[expected_career(traveler)], "Saved enrollment must select its own new commission entry")
		for career in CAREERS:
			if scene_id == "commission_portfolio_%s_01" % career:
				check(career == CAREERS[expected_career(traveler)] and has_commission_work(traveler), "A saved portfolio must name its actual profession and performed commission work")
		if scene.has("ending") and not scene.has("next") and not scene.has("continuation"):
			completed_paths += 1
			var accepted: bool = traveler.decisions.get("commission_offer_choice", "") == "commission_dispatch"
			if accepted:
				check(has_commission_work(traveler), "An accepted completed commission must contain performed work")
			else:
				check(not has_commission_work(traveler) and traveler.stats == seed.stats, "Deferring or declining a new term cannot invent completed commission work")
			continue
		if scene.has("choices") and not scene.get("random_event", false):
			check(not scene.has("earned"), "Selecting commission work cannot also claim its completion")
			var available := 0
			for index in range(scene.choices.size()):
				if not traveler.can_choose(scene.choices[index]):
					continue
				var branch = copy_state(traveler)
				var before: Dictionary = branch.stats.duplicate()
				var before_practice: Dictionary = branch.completed_practice.duplicate(true)
				check(branch.choose(index), "An available commission decision must progress: " + scene_id)
				check(branch.stats == before and branch.completed_practice == before_practice, "An intention or selected commission method cannot award unperformed work: " + scene_id)
				test_saved_choice(traveler, branch, scene_id, index)
				queue.append(branch)
				available += 1
			check(available > 0, "Every commission decision must retain an available route: " + scene_id)
		else:
			if scene.has("routes") or scene_id == "commission_receiving_01":
				var dependencies: Array = []
				for route in scene.get("routes", []):
					if not dependencies.has(route.decision):
						dependencies.append(route.decision)
				dependencies.sort()
				var saved_key := JSON.stringify([scene_id, projection(traveler, dependencies)])
				if not checked_routes.has(saved_key):
					checked_routes[saved_key] = true
					traveler = round_trip(traveler)
			var before: Dictionary = traveler.stats.duplicate()
			var was_completed: bool = traveler.completed_practice.has(scene_id)
			var earned: Dictionary = scene.get("earned", {})
			var moved: bool = traveler.advance()
			check(moved, "Performed commissions must reach the next authored scene: " + scene_id)
			if not moved:
				continue
			if earned.is_empty():
				check(traveler.stats == before, "Uncredited commission narration cannot award growth: " + scene_id)
			else:
				test_reward(traveler, scene_id, earned, before, was_completed)
			queue.append(traveler)
	check(cursor < 250000, "Commission branch traversal must remain finite")
	check(completed_paths > 0, "Every saved commission context must retain a complete playable route")
	tested_paths += completed_paths

func _initialize() -> void:
	clear_save()
	var campaign: Dictionary = State.new().story
	check(campaign.chapters.has(CHAPTER), "The delivered campaign must load the commissioned-work chapter")
	for ending in PREVIOUS_ENDINGS:
		var continuation = State.new(campaign)
		continuation.current = ending
		check(continuation.advance() and continuation.current == "commission_entry", "Each Book XX term must continue into the new offer: " + ending)
	var dependencies: Array = previous_decisions(campaign)
	for selection in range(CAREERS.size()):
		for seed in training_seeds(campaign, selection, dependencies):
			test_commissions(seed)
		var untrained = State.new(campaign)
		untrained.current = "career_enrol_choice"
		check(untrained.choose(selection), "Zero-score aspirants must still enter supervised career training")
		check(walk_to(untrained, "commission_entry"), "A zero-score journey must reach a genuine subsequent offer")
		test_commissions(untrained)
		var legacy_enrollment = State.new(campaign)
		legacy_enrollment.current = "career_enrol_choice"
		check(legacy_enrollment.choose(selection), "A legacy enrollment must be an actual choice")
		legacy_enrollment.current = "commission_entry"
		check(legacy_enrollment.completed_practice.is_empty(), "Legacy context cannot invent a prior qualification")
		test_commissions(legacy_enrollment)
	var legacy = State.new(campaign)
	legacy.current = "commission_entry"
	test_commissions(legacy)
	for scene_id in campaign.nodes:
		var scene: Dictionary = campaign.nodes[scene_id]
		if scene.get("chapter", "") == CHAPTER:
			check(covered.has(scene_id), "Every authored commission scene must be reachable through actual or legacy choices: " + scene_id)
			if scene.has("earned"):
				check(checked_rewards.has(scene_id), "Every commissioned completion credit must be exercised: " + scene_id)
	clear_save()
	if failures.is_empty():
		print("JADE_VOW_COMMISSIONS_TESTS_OK: %d retained contexts; %d commission paths; %d completion rewards; saved methods and native chapter continuity" % [tested_seeds, tested_paths, checked_rewards.size()])
	quit(0 if failures.is_empty() else 1)
