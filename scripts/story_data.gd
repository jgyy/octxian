extends RefCounted

const GROUPS := ["chapters", "characters", "nodes"]

# Return an error without a partial campaign; callers decide how to report it.
static func load_campaign(path: String = "res://data/story.json") -> Dictionary:
	var root := _read(path)
	if not root.error.is_empty():
		return root
	var raw: Dictionary = root.story
	var failure := _validate_groups(raw, path)
	if not failure.is_empty():
		return _failure(failure)
	var books = raw.get("books", [])
	if not books is Array:
		return _failure("Story books must be an array of repository paths.")
	var merged: Dictionary = raw.duplicate()
	for group in GROUPS:
		merged[group] = raw[group].duplicate()
	var seen := {}
	for name in books:
		if not name is String or not _valid_book_path(name):
			return _failure("Book paths must stay under data/books: %s" % str(name))
		if seen.has(name):
			return _failure("Repeated story book: %s" % name)
		seen[name] = true
		var part_result := _read("res://" + name)
		if not part_result.error.is_empty():
			return part_result
		var part: Dictionary = part_result.story
		if part.size() != GROUPS.size():
			return _failure("%s: books contain only chapters, characters and nodes." % name)
		failure = _validate_groups(part, name)
		if not failure.is_empty():
			return _failure(failure)
		for group in GROUPS:
			for key in part[group]:
				if merged[group].has(key):
					return _failure("%s: duplicate %s ID: %s" % [name, group, str(key)])
				merged[group][key] = part[group][key]
	if not merged.get("start") is String or not merged.nodes.has(merged.start):
		return _failure("The campaign start must name a loaded scene.")
	return {"story": merged, "error": ""}

static func _valid_book_path(name: String) -> bool:
	if not name.begins_with("data/books/") or not name.ends_with(".json") or name.contains("\\") or name.contains(":"):
		return false
	for part in name.split("/", true):
		if part.is_empty() or part == "." or part == "..":
			return false
	return true

static func _read(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return _failure("Missing story book: %s" % path)
	var parser := JSON.new()
	var source := FileAccess.get_file_as_string(path)
	var status := parser.parse(source)
	if status != OK:
		return _failure("%s: malformed JSON at line %d: %s" % [path, parser.get_error_line(), parser.get_error_message()])
	if not parser.data is Dictionary:
		return _failure("%s: story files must contain an object." % path)
	var duplicate := _validate_unique_keys(source, path)
	if not duplicate.is_empty():
		return _failure(duplicate)
	return {"story": parser.data, "error": ""}

# JSON.parse silently keeps the last duplicate key. Inspect valid JSON tokens
# before returning it, including escaped spellings of the same object key.
static func _validate_unique_keys(source: String, path: String) -> String:
	var containers: Array[Dictionary] = []
	var index := 0
	while index < source.length():
		var token := source[index]
		if token == "\"":
			var start := index
			index = source.find("\"", index + 1)
			while index >= 0:
				var escapes := 0
				var preceding := index - 1
				while preceding > start and source[preceding] == "\\":
					escapes += 1
					preceding -= 1
				if escapes % 2 == 0:
					break
				index = source.find("\"", index + 1)
			if not containers.is_empty():
				var context: Dictionary = containers.back()
				if context.object and context.key:
					var key: String = JSON.parse_string(source.substr(start, index - start + 1))
					if context.names.has(key):
						return "%s: duplicate JSON key: %s" % [path, key]
					context.names[key] = true
					context.key = false
		elif token == "{":
			containers.append({"object": true, "key": true, "names": {}})
		elif token == "[":
			containers.append({"object": false})
		elif token == "}" or token == "]":
			containers.pop_back()
		elif token == "," and not containers.is_empty():
			var context: Dictionary = containers.back()
			if context.object:
				context.key = true
		index += 1
	return ""

static func _validate_groups(raw: Dictionary, path: String) -> String:
	for group in GROUPS:
		if not raw.get(group) is Dictionary:
			return "%s: %s must be an object." % [path, group]
		for key in raw[group]:
			if not key is String or key.is_empty() or not raw[group][key] is Dictionary:
				return "%s: invalid %s entry." % [path, group]
	return ""

static func _failure(message: String) -> Dictionary:
	return {"story": {}, "error": message}
