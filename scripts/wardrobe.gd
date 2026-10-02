extends RefCounted

const CHARACTERS := ["lin_yue", "shen_qing", "elder_yun", "mo_ran"]
const DEFAULT_OUTFIT := "sect"
var catalog: Dictionary = {}
var selections := {}

func _init() -> void:
	var raw = JSON.parse_string(FileAccess.get_file_as_string("res://data/wardrobe.json"))
	if raw is Dictionary:
		catalog = raw
	restore({})

func options() -> Array:
	return catalog.get("outfits", [])

func is_valid(character: String, outfit: String) -> bool:
	if not CHARACTERS.has(character):
		return false
	for option in options():
		if option["id"] == outfit:
			return true
	return false

func select(character: String, outfit: String) -> bool:
	if not is_valid(character, outfit):
		return false
	selections[character] = outfit
	return true

func selected(character: String) -> String:
	return str(selections.get(character, DEFAULT_OUTFIT))

func restore(saved: Variant) -> void:
	for character in CHARACTERS:
		selections[character] = DEFAULT_OUTFIT
	if saved is Dictionary:
		for character in CHARACTERS:
			select(character, str(saved.get(character, DEFAULT_OUTFIT)))

func source_path(outfit: String) -> String:
	for option in options():
		if option["id"] == outfit:
			return "res://" + str(option["source"])
	return "res://assets/art/cast.png"

func animation_path(character: String, animation: String, outfit: String) -> String:
	if not is_valid(character, outfit):
		outfit = DEFAULT_OUTFIT
	var suffix := "" if outfit == DEFAULT_OUTFIT else "_" + outfit
	return "res://assets/generated/sprites/%s%s_%s.png" % [character, suffix, animation]
