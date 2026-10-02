extends Node2D

const Wardrobe = preload("res://scripts/wardrobe.gd")
const LOOPS := ["idle", "channeling", "wind", "resolve"]
var wardrobe = Wardrobe.new()
var sprite := Sprite2D.new()
var character := ""
var motion := "idle"
var outfit := "sect"
var display_height := 730.0
var fade_in := true
var reduced_motion := false
var motion_time := 0.0
var fade_tween: Tween

func _ready() -> void:
	add_child(sprite)

func _process(delta: float) -> void:
	if reduced_motion or character.is_empty():
		return
	var duration := float(wardrobe.catalog.get("seconds_per_cycle", 4.0))
	motion_time = fmod(motion_time + delta, duration)
	var phase := TAU * motion_time / duration
	var amplitude := float(wardrobe.catalog.get("bob_pixels", {}).get(motion, 6.0))
	sprite.position.y = sin(phase) * amplitude * display_height / 730.0

func reset_motion() -> void:
	motion_time = 0.0
	sprite.position = Vector2.ZERO

func set_reduced_motion(value: bool) -> void:
	reduced_motion = value
	if value:
		reset_motion()

func show_character(id: String, animation: String = "idle", clothing: String = "sect") -> void:
	if not Wardrobe.CHARACTERS.has(id):
		id = "lin_yue"
	if not wardrobe.is_valid(id, clothing):
		clothing = Wardrobe.DEFAULT_OUTFIT
	if not LOOPS.has(animation):
		animation = "idle"
	if character == id and motion == animation and outfit == clothing:
		return
	character = id
	motion = animation
	outfit = clothing
	reset_motion()
	var path: String = wardrobe.portrait_path(id, clothing)
	if ResourceLoader.exists(path):
		sprite.texture = load(path)
	else:
		var source: Texture2D = load(wardrobe.source_path(clothing))
		var portrait := AtlasTexture.new()
		portrait.atlas = source
		var index: int = Wardrobe.CHARACTERS.find(id)
		portrait.region = Rect2(index * source.get_width() / 4.0, 0, source.get_width() / 4.0, source.get_height())
		sprite.texture = portrait
	sprite.scale = Vector2.ONE * (display_height / sprite.texture.get_height())
	if fade_tween and fade_tween.is_valid():
		fade_tween.kill()
	if fade_in and not reduced_motion:
		modulate.a = 0.0
		fade_tween = create_tween()
		fade_tween.tween_property(self, "modulate:a", 1.0, 0.35)
	else:
		modulate.a = 1.0
