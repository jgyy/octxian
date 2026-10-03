extends RefCounted

const Attributes = preload("res://scripts/attributes.gd")
const SAVE_VERSION := 1
# Long campaigns may exceed 100; enforce the same limit on play and load.
const MAX_STAT := 2147483647
const STAT_KEYS = Attributes.KEYS
var story: Dictionary = {}
var current := "arrival"
var stats := {"qi": 0, "trust": 0, "insight": 0, "resolve": 0}
var history: Array = []

func _init(source: Dictionary = {}) -> void:
	# Traversal tools may reuse one immutable campaign instead of reparsing it per branch.
	var raw = source if not source.is_empty() else JSON.parse_string(FileAccess.get_file_as_string("res://data/story.json"))
	if raw is Dictionary:
		story = raw
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
	var choices: Array = node().get("choices", [])
	if index < 0 or index >= choices.size():
		return false
	var choice: Dictionary = choices[index]
	var details := choice_details(choice)
	if not details.available or not go(str(choice.get("next", ""))):
		return false
	stats = details.updated_stats
	return true

func advance() -> bool:
	return go(str(node().get("next", node().get("continuation", ""))))

func go(target: String) -> bool:
	if not story.get("nodes", {}).has(target):
		return false
	history.append({"speaker": node().get("speaker", "narrator"), "text": node().get("text", "")})
	current = target
	return true

func save_game(path: String = "user://jade_vow_save.json") -> bool:
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		return false
	file.store_string(JSON.stringify({"version": SAVE_VERSION, "current": current, "stats": stats, "history": history}))
	return true

func load_game(path: String = "user://jade_vow_save.json") -> bool:
	if not FileAccess.file_exists(path):
		return false
	var data = JSON.parse_string(FileAccess.get_file_as_string(path))
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
	current = data["current"]
	stats = validated_stats
	history = data["history"].duplicate(true)
	return true
