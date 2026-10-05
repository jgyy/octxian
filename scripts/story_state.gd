extends RefCounted

const Attributes = preload("res://scripts/attributes.gd")
const StoryData = preload("res://scripts/story_data.gd")
const SAVE_VERSION := 1
# Long campaigns may exceed 100; enforce the same limit on play and load.
const MAX_STAT := 2147483647
const STAT_KEYS = Attributes.KEYS
var story: Dictionary = {}
var current := "arrival"
var stats := {"qi": 0, "trust": 0, "insight": 0, "resolve": 0}
var history: Array = []
var recovered_checkpoint := false
var journey_seed: int = randi_range(1, 2147483646)
var encounters: Dictionary = {}
# Practice credit follows completed scenes and is awarded once per journey.
var completed_practice: Dictionary = {}

func _init(source: Dictionary = {}) -> void:
	# Injected traversal campaigns are already merged; never reload their book files.
	if not source.is_empty():
		story = source
	else:
		var loaded := StoryData.load_campaign()
		if not loaded.error.is_empty():
			push_error(loaded.error)
			return
		story = loaded.story
	current = str(story.get("start", "arrival"))

func node() -> Dictionary:
	return story.get("nodes", {}).get(current, {})

# Preview and application share validation, including malformed requirements and overflow.
func choice_details(choice: Dictionary) -> Dictionary:
	var details := {
		"available": false, "reason": "",
		"effects": PackedStringArray(), "requirements": PackedStringArray(),
		"missing": PackedStringArray(), "updated_stats": stats.duplicate()
	}
	if not story.get("nodes", {}).has(str(choice.get("next", ""))):
		details.reason = "This choice has no valid destination."
		return details
	var requirements = choice.get("requires", {})
	var effects = choice.get("effects", {})
	if not requirements is Dictionary or not effects is Dictionary:
		details.reason = "This choice has invalid attribute data."
		return details
	for key in requirements:
		var value = requirements[key]
		if not STAT_KEYS.has(key) or not (value is int or value is float):
			details.reason = "This choice has an invalid attribute requirement."
			return details
		if not is_finite(float(value)) or value < 0 or value > MAX_STAT or value != int(value):
			details.reason = "This choice has an invalid attribute requirement."
			return details
	for key in effects:
		var effect = effects[key]
		if not STAT_KEYS.has(key) or not (effect is int or effect is float):
			details.reason = "This choice has an invalid attribute change."
			return details
		if not is_finite(float(effect)) or effect < -MAX_STAT or effect > MAX_STAT or effect != int(effect):
			details.reason = "This choice has an invalid attribute change."
			return details
		var updated: int = int(stats.get(key, 0)) + int(effect)
		if updated < 0 or updated > MAX_STAT:
			details.reason = "This choice would exceed the attribute limits."
			return details
		details.updated_stats[key] = updated
	for key in STAT_KEYS:
		var title := Attributes.attribute_name(key)
		if requirements.has(key):
			var requirement := "%s %d/%d" % [title, int(stats.get(key, 0)), int(requirements[key])]
			details.requirements.append(requirement)
			if int(stats.get(key, 0)) < int(requirements[key]):
				details.missing.append(requirement)
		if effects.has(key) and int(effects[key]) != 0:
			var effect: int = int(effects[key])
			details.effects.append("%s %s%d" % [title, "+" if effect > 0 else "", effect])
	details.available = details.missing.is_empty()
	if not details.available:
		details.reason = "Requires " + ", ".join(details.missing)
	return details

func can_choose(choice: Dictionary) -> bool:
	return bool(choice_details(choice).available)

func choose(index: int) -> bool:
	if node().get("random_event", false):
		return false
	var choices: Array = node().get("choices", [])
	if index < 0 or index >= choices.size():
		return false
	var choice: Dictionary = choices[index]
	var details := choice_details(choice)
	if not details.available or not go(str(choice.get("next", ""))):
		return false
	stats = details.updated_stats
	return true

func encounter_target() -> String:
	if not node().get("random_event", false):
		return ""
	var options: Array = node().get("choices", [])
	if options.size() < 2:
		return ""
	var targets: Array[String] = []
	for option in options:
		if not option is Dictionary or option.has("effects") or option.has("requires"):
			return ""
		var target := str(option.get("next", ""))
		if not story.get("nodes", {}).has(target) or targets.has(target):
			return ""
		targets.append(target)
	if encounters.has(current):
		return str(encounters[current]) if targets.has(str(encounters[current])) else ""
	var generator := RandomNumberGenerator.new()
	generator.seed = journey_seed ^ current.hash()
	return targets[generator.randi_range(0, targets.size() - 1)]

func advance() -> bool:
	if node().get("random_event", false):
		var event_id := current
		var target := encounter_target()
		if target.is_empty() or not go(target):
			return false
		encounters[event_id] = target
		return true
	return go(str(node().get("next", node().get("continuation", ""))))

func go(target: String) -> bool:
	if not story.get("nodes", {}).has(target):
		return false
	if node().has("earned") and not completed_practice.has(current):
		var reward := choice_details({"next": target, "effects": node().earned})
		if not reward.available:
			return false
		stats = reward.updated_stats
		completed_practice[current] = true
	history.append({"speaker": node().get("speaker", "narrator"), "text": node().get("text", "")})
	current = target
	return true

static func has_save(path: String = "user://jade_vow_save.json") -> bool:
	return FileAccess.file_exists(path) or FileAccess.file_exists(path + ".bak")

func _read_checkpoint_file(path: String) -> Dictionary:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return {"ok": false, "bytes": PackedByteArray()}
	var length := file.get_length()
	var bytes := file.get_buffer(length)
	var read_error := file.get_error()
	file.close()
	return {"ok": read_error == OK and bytes.size() == length, "bytes": bytes}

func _write_verified_checkpoint(path: String, bytes: PackedByteArray) -> bool:
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		return false
	file.store_buffer(bytes)
	file.flush()
	var write_error := file.get_error()
	file.close()
	if write_error != OK:
		return false
	# Some backends do not expose late flush errors through get_error().
	var written := _read_checkpoint_file(path)
	return written.ok and written.bytes == bytes

func _commit_checkpoint(temporary_path: String, path: String) -> int:
	return DirAccess.rename_absolute(temporary_path, path)

func save_game(path: String = "user://jade_vow_save.json") -> bool:
	var temporary_path := path + ".tmp"
	var backup_path := path + ".bak"
	var bytes := JSON.stringify({"version": SAVE_VERSION, "current": current, "stats": stats, "history": history, "journey_seed": journey_seed, "encounters": encounters, "completed_practice": completed_practice, "practice_rules": 1}).to_utf8_buffer()
	if not _write_verified_checkpoint(temporary_path, bytes):
		if FileAccess.file_exists(temporary_path):
			DirAccess.remove_absolute(temporary_path)
		return false
	var previous := _read_checkpoint_file(path)
	if FileAccess.file_exists(path):
		if not previous.ok or not _write_verified_checkpoint(backup_path, previous.bytes):
			DirAccess.remove_absolute(temporary_path)
			return false
	# Keep a verified prior checkpoint: Windows removes an existing destination
	# before attempting the move, so a failed rename can leave the primary absent.
	if _commit_checkpoint(temporary_path, path) != OK:
		if previous.ok and _write_verified_checkpoint(temporary_path, previous.bytes):
			_commit_checkpoint(temporary_path, path)
		DirAccess.remove_absolute(temporary_path)
		return false
	return true

func load_game(path: String = "user://jade_vow_save.json") -> bool:
	# Recover the prior checkpoint only when a replacement left no primary file.
	var checkpoint_path := path if FileAccess.file_exists(path) else path + ".bak"
	var checkpoint := _read_checkpoint_file(checkpoint_path)
	if not checkpoint.ok:
		return false
	var parser := JSON.new()
	if parser.parse(checkpoint.bytes.get_string_from_utf8()) != OK:
		return false
	var data = parser.data
	if not data is Dictionary or data.get("version", -1) != SAVE_VERSION:
		return false
	if not story["nodes"].has(data.get("current", "")):
		return false
	if not data.get("stats") is Dictionary or not data.get("history") is Array:
		return false
	var validated_stats := {}
	for key in STAT_KEYS:
		var value = data["stats"].get(key)
		if not (value is float or value is int) or value < 0 or value > MAX_STAT or not is_finite(float(value)) or value != int(value):
			return false
		validated_stats[key] = int(value)
	for entry in data["history"]:
		if not entry is Dictionary or not entry.get("text") is String or not entry.get("speaker") is String:
			return false
		if not story["characters"].has(entry["speaker"]):
			return false
	var validated_seed: int = journey_seed
	var validated_encounters: Dictionary = {}
	if data.has("journey_seed") != data.has("encounters"):
		return false
	if data.has("journey_seed"):
		var seed_value = data.journey_seed
		if not (seed_value is int or seed_value is float) or not is_finite(float(seed_value)) or seed_value != int(seed_value) or seed_value < 1 or seed_value > 2147483646:
			return false
		if not data.encounters is Dictionary:
			return false
		validated_seed = int(seed_value)
		for event_id in data.encounters:
			if not story.nodes.has(event_id) or not story.nodes[event_id].get("random_event", false):
				return false
			var options: Array = story.nodes[event_id].get("choices", [])
			var valid_target := false
			for option in options:
				if option.get("next", "") == data.encounters[event_id]:
					valid_target = true
			if not valid_target or not data.encounters[event_id] is String:
				return false
		validated_encounters = data.encounters.duplicate(true)
	var validated_practice: Dictionary = {}
	if data.has("completed_practice"):
		if not data.completed_practice is Dictionary:
			return false
		for practice_id in data.completed_practice:
			if not story.nodes.has(practice_id) or not story.nodes[practice_id].has("earned") or not data.completed_practice[practice_id] is bool or data.completed_practice[practice_id] != true:
				return false
		validated_practice = data.completed_practice.duplicate(true)
	# Version-1 checkpoints predating deferred credit already received these
	# gains when selecting the branch. Preserve those scores without paying twice.
	var rules = data.get("practice_rules", 0)
	if not (rules is int or rules is float) or (rules != 0 and rules != 1):
		return false
	if rules == 0:
		var prior_texts := {}
		for entry in data["history"]:
			prior_texts[entry.text] = true
		for practice_id in story.nodes:
			var practice: Dictionary = story.nodes[practice_id]
			if not practice.has("legacy_credit"):
				continue
			var origin: String = practice.legacy_credit.choice_node
			var branch: Array = practice.legacy_credit.branch_nodes
			if prior_texts.has(practice.text) or (branch.has(data.current) and prior_texts.has(story.nodes[origin].text)):
				validated_practice[practice_id] = true
	completed_practice = validated_practice
	journey_seed = validated_seed
	encounters = validated_encounters
	current = data["current"]
	stats = validated_stats
	history = data["history"].duplicate(true)
	recovered_checkpoint = checkpoint_path != path
	return true
