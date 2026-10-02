extends RefCounted

const SAVE_VERSION := 1
# Long campaigns may exceed 100; enforce the same limit on play and load.
const MAX_STAT := 2147483647
const STAT_KEYS := ["qi", "trust", "insight", "resolve"]
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

func can_choose(choice: Dictionary) -> bool:
	for key in choice.get("requires", {}):
		if int(stats.get(key, 0)) < int(choice["requires"][key]):
			return false
	return true

func choose(index: int) -> bool:
	var choices: Array = node().get("choices", [])
	if index < 0 or index >= choices.size() or not can_choose(choices[index]):
		return false
	var choice: Dictionary = choices[index]
	var target := str(choice.get("next", ""))
	if not story.get("nodes", {}).has(target):
		return false
	var updated := stats.duplicate()
	for key in choice.get("effects", {}):
		var effect = choice["effects"][key]
		if not STAT_KEYS.has(key) or not (effect is int or effect is float):
			return false
		if not is_finite(float(effect)) or effect != int(effect):
			return false
		var value := int(updated.get(key, 0)) + int(effect)
		if value < 0 or value > MAX_STAT:
			return false
		updated[key] = value
	if not go(target):
		return false
	stats = updated
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
