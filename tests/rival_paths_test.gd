extends SceneTree

const State = preload("res://scripts/story_state.gd")
const SAVE_PATH := "user://rival_paths_test.json"
const CHAPTER := "book_xxii_rival"
const ENTRY := "rival_entry"
const BRANCHES := ["rival_compete_entry", "rival_cooperate_entry", "rival_independent_entry"]
const PRIOR_ENDINGS := ["commission_new_request_06", "commission_home_06", "commission_daywork_06"]
const CULTIVATION := {"realm": "qi_gathering", "stage": "5: Four pairs"}
var failures: Array[String] = []
var covered: Dictionary = {}
var tested_choices: Dictionary = {}
var tested_routes: Dictionary = {}
var ended_branches: Dictionary = {}
var ending_count := 0

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
	check(original.save_game(SAVE_PATH), "Rival choices and prose must save: " + original.current)
	var restored = State.new(original.story)
	check(restored.load_game(SAVE_PATH), "Rival choices and prose must load: " + original.current)
	check(restored.current == original.current and restored.stats == original.stats, "Rival checkpoints retain scene and attributes")
	check(restored.decisions == original.decisions and restored.completed_practice == original.completed_practice, "Rival checkpoints retain actual choices and completed work")
	check(restored.history == original.history and restored.journey_seed == original.journey_seed and restored.encounters == original.encounters, "Rival checkpoints retain the journal and encounter context")
	return restored

func saved_choice_contract(source, selected, decision_id: String, index: int) -> void:
	var signature := "%s:%d" % [decision_id, index]
	if tested_choices.has(signature):
		return
	tested_choices[signature] = true
	var restored = round_trip(selected)
	var destination: String = selected.decisions[decision_id]
	restored.current = decision_id
	var before_stats: Dictionary = restored.stats.duplicate()
	var before_decisions: Dictionary = restored.decisions.duplicate(true)
	var before_practice: Dictionary = restored.completed_practice.duplicate(true)
	var before_history: Array = restored.history.duplicate(true)
	for alternative in range(source.node().choices.size()):
		if source.node().choices[alternative].next == destination:
			continue
		check(not restored.choose(alternative), "A saved rival commitment cannot silently switch: " + decision_id)
		check(restored.current == decision_id and restored.stats == before_stats and restored.decisions == before_decisions and restored.completed_practice == before_practice and restored.history == before_history, "Rejected rival commitments remain atomic: " + decision_id)
	check(restored.choose(index) and restored.current == destination, "The saved selected rival option remains available on a revisit: " + decision_id)
	check(restored.stats == before_stats and restored.completed_practice == before_practice, "Repeating a cold trial decision cannot farm cultivation credit")

func routing_contract(traveler) -> void:
	var scene: Dictionary = traveler.node()
	var values: Array = []
	for route in scene.routes:
		values.append([route.decision, traveler.decisions.get(route.decision, "")])
	var signature := JSON.stringify([traveler.current, values])
	if tested_routes.has(signature):
		return
	tested_routes[signature] = true
	var expected: String = scene.next
	for route in scene.routes:
		if traveler.decisions.get(route.decision, "") == route.selected:
			expected = route.next
			break
	var restored = round_trip(traveler)
	var before_stats: Dictionary = restored.stats.duplicate()
	var before_practice: Dictionary = restored.completed_practice.duplicate(true)
	check(restored.advance() and restored.current == expected, "Saved rival relationships must select the first actual recorded consequence: " + traveler.current)
	check(restored.stats == before_stats and restored.completed_practice == before_practice, "A rival callback cannot create unperformed growth")
	var legacy = State.new(traveler.story)
	legacy.current = traveler.current
	check(legacy.advance() and legacy.current == scene.next, "Missing old decisions retain the unclaimed shared fallback: " + traveler.current)

# Keep only choices read later in signatures, while preserving full records in saves.
func future_decisions(campaign: Dictionary) -> Dictionary:
	var parents: Dictionary = {}
	var relevant: Dictionary = {}
	for scene_id in campaign.nodes:
		if campaign.nodes[scene_id].get("chapter", "") == CHAPTER:
			parents[scene_id] = {}
			relevant[scene_id] = {}
	for scene_id in parents:
		var scene: Dictionary = campaign.nodes[scene_id]
		var targets: Array = []
		if not scene.has("ending"):
			for field in ["next", "continuation"]:
				if scene.has(field):
					targets.append(scene[field])
		for option in scene.get("choices", []):
			targets.append(option.next)
		for route in scene.get("routes", []):
			targets.append(route.next)
			relevant[scene_id][route.decision] = true
		for target in targets:
			check(parents.has(target), "Rival graph edges must remain within the chapter")
			if parents.has(target):
				parents[target][scene_id] = true
	var queue: Array = []
	for scene_id in relevant:
		if not relevant[scene_id].is_empty():
			queue.append(scene_id)
	var cursor := 0
	while cursor < queue.size():
		var target: String = queue[cursor]
		cursor += 1
		for parent in parents[target]:
			var changed := false
			for decision in relevant[target]:
				if decision == parent and campaign.nodes[parent].has("choices") and not campaign.nodes[parent].get("random_event", false):
					continue
				if not relevant[parent].has(decision):
					relevant[parent][decision] = true
					changed = true
			if changed:
				queue.append(parent)
	return relevant

func signature(traveler, relevant: Dictionary) -> String:
	var ids: Array = relevant[traveler.current].keys()
	ids.sort()
	var selected: Array = []
	for decision in ids:
		if traveler.decisions.has(decision):
			selected.append([decision, traveler.decisions[decision]])
	return JSON.stringify([traveler.current, selected])

func prior_contexts(campaign: Dictionary) -> Array:
	var blank = State.new(campaign)
	blank.current = ENTRY
	var contexts: Array = [round_trip(blank)]
	var dependencies: Dictionary = {}
	for scene in campaign.nodes.values():
		if scene.get("chapter", "") != CHAPTER:
			continue
		for route in scene.get("routes", []):
			if campaign.nodes[route.decision].get("chapter", "") != CHAPTER:
				dependencies[route.decision] = true
	for decision in dependencies:
		var source: Dictionary = campaign.nodes[decision]
		for index in range(source.choices.size()):
			var traveler = State.new(campaign)
			traveler.current = decision
			check(traveler.can_choose(source.choices[index]) and traveler.choose(index), "Prior context must come from an actual ordinary selection: " + str(decision))
			var steps := 0
			while traveler.current != ENTRY and steps < 3000:
				var moved := false
				if traveler.node().has("choices"):
					for option in range(traveler.node().choices.size()):
						if traveler.can_choose(traveler.node().choices[option]):
							moved = traveler.choose(option)
							break
				else:
					moved = traveler.advance()
				if not moved:
					break
				steps += 1
			check(traveler.current == ENTRY, "The selected prior settlement must actually reach rival entry")
			if traveler.current == ENTRY:
				contexts.append(round_trip(traveler))
	return contexts

func traverse_zero_score(campaign: Dictionary) -> void:
	var relevant := future_decisions(campaign)
	var queue: Array = prior_contexts(campaign)
	var seen: Dictionary = {}
	var cursor := 0
	while cursor < queue.size() and cursor < 100000:
		var traveler = queue[cursor]
		cursor += 1
		var visit := signature(traveler, relevant)
		if seen.has(visit):
			continue
		seen[visit] = true
		var scene_id: String = traveler.current
		var scene: Dictionary = traveler.node()
		check(scene.get("chapter", "") == CHAPTER, "Rival trials must retain their chapter: " + scene_id)
		if scene.get("chapter", "") != CHAPTER:
			continue
		covered[scene_id] = true
		check(scene.get("cultivation", {}) == CULTIVATION, "Competition and recognition cannot manufacture a new realm: " + scene_id)
		check(not scene.has("earned") and traveler.completed_practice.is_empty(), "An elective low-load trial cannot claim completed cultivation practice: " + scene_id)
		check(traveler.stats == {"qi": 0, "trust": 0, "insight": 0, "resolve": 0}, "A zero-score rival journey must remain available without fabricated credit: " + scene_id)
		if scene.has("ending"):
			ending_count += 1
			ended_branches[traveler.decisions.get("rival_path_choice", "")] = true
			continue
		if scene.has("choices"):
			check(not scene.get("random_event", false), "Rival relationship decisions must belong to the player")
			var available := 0
			for index in range(scene.choices.size()):
				var option: Dictionary = scene.choices[index]
				check(traveler.can_choose(option), "Every elective rival method needs a zero-score path: " + scene_id)
				if not traveler.can_choose(option):
					continue
				var branch = copy_state(traveler)
				var before_stats: Dictionary = branch.stats.duplicate()
				var before_practice: Dictionary = branch.completed_practice.duplicate(true)
				check(branch.choose(index), "An available rival decision must progress: " + scene_id)
				check(branch.decisions.get(scene_id, "") == option.next, "Rival saves must record the actual selected destination: " + scene_id)
				check(branch.stats == before_stats and branch.completed_practice == before_practice, "Selecting a rival method must not award unperformed work: " + scene_id)
				saved_choice_contract(traveler, branch, scene_id, index)
				queue.append(branch)
				available += 1
			check(available > 0, "Every rival decision must retain an available path")
		else:
			if scene.has("routes"):
				routing_contract(traveler)
			var before_stats: Dictionary = traveler.stats.duplicate()
			var before_practice: Dictionary = traveler.completed_practice.duplicate(true)
			var moved: bool = traveler.advance()
			check(moved, "Every rival passage must reach its next authored scene: " + scene_id)
			check(traveler.stats == before_stats and traveler.completed_practice == before_practice, "Rival prose and callbacks must preserve existing cultivation credit: " + scene_id)
			if moved:
				queue.append(traveler)
	check(cursor < 100000, "Rival path enumeration must remain finite")
	check(ending_count >= 3, "The rival chapter must retain distinct completed outcomes")
	for branch in BRANCHES:
		check(ended_branches.has(branch), "Every elective rival path must reach a completed outcome: " + branch)
	for scene_id in campaign.nodes:
		if campaign.nodes[scene_id].get("chapter", "") == CHAPTER:
			check(covered.has(scene_id), "Every rival scene needs an actual playable choice history: " + scene_id)

func _initialize() -> void:
	clear_save()
	var campaign: Dictionary = State.new().story
	check(campaign.get("chapters", {}).has(CHAPTER) and campaign.get("nodes", {}).has(ENTRY), "The packaged campaign data must load the rival chapter")
	if not campaign.get("nodes", {}).has(ENTRY):
		quit(1)
		return
	for ending in PRIOR_ENDINGS:
		check(campaign.nodes.has(ending), "Every previous commission settlement must remain available")
		if not campaign.nodes.has(ending):
			continue
		var traveler = State.new(campaign)
		traveler.current = ending
		traveler.stats = {"qi": 7, "trust": 8, "insight": 9, "resolve": 10}
		var before_stats: Dictionary = traveler.stats.duplicate()
		check(traveler.node().has("ending") and traveler.advance() and traveler.current == ENTRY, "A completed commission keeps its ending and continues into elective trials: " + ending)
		check(traveler.stats == before_stats and traveler.history.back().text == campaign.nodes[ending].text, "Rival entry preserves the actual prior settlement and earned scores")
		round_trip(traveler)
	traverse_zero_score(campaign)
	clear_save()
	if failures.is_empty():
		print("JADE_VOW_RIVAL_PATHS_TESTS_OK: %d scenes; %d saved choices; %d saved route contexts; %d endings" % [covered.size(), tested_choices.size(), tested_routes.size(), ending_count])
	quit(0 if failures.is_empty() else 1)
