extends Node2D

const Wardrobe = preload("res://scripts/wardrobe.gd")
const LOOPS := ["idle", "channeling", "wind", "resolve"]
var wardrobe = Wardrobe.new()
var sprite := AnimatedSprite2D.new()
var character := ""
var motion := "idle"
var outfit := "sect"
var display_height := 730.0
var fade_in := true

func _ready() -> void:
	add_child(sprite)

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
	var path: String = wardrobe.animation_path(id, animation, clothing)
	if ResourceLoader.exists(path):
		var atlas: Texture2D = load(path)
		var frames := SpriteFrames.new()
		frames.remove_animation("default")
		frames.add_animation("cycle")
		frames.set_animation_speed("cycle", 16.0)
		frames.set_animation_loop("cycle", true)
		var cell := Vector2(atlas.get_width() / 8.0, atlas.get_height() / 8.0)
		for i in range(64):
			var frame := AtlasTexture.new()
			frame.atlas = atlas
			frame.region = Rect2(Vector2(i % 8, floori(i / 8.0)) * cell, cell)
			frames.add_frame("cycle", frame)
		sprite.sprite_frames = frames
		sprite.scale = Vector2.ONE * (display_height / cell.y)
		sprite.play("cycle")
	else:
		var atlas: Texture2D = load(wardrobe.source_path(clothing))
		var frame := AtlasTexture.new()
		frame.atlas = atlas
		var index: int = Wardrobe.CHARACTERS.find(id)
		frame.region = Rect2(index * atlas.get_width() / 4.0, 0, atlas.get_width() / 4.0, atlas.get_height())
		var frames := SpriteFrames.new()
		frames.add_frame("default", frame)
		sprite.sprite_frames = frames
		sprite.scale = Vector2.ONE * (display_height / atlas.get_height())
	if fade_in:
		modulate.a = 0.0
		create_tween().tween_property(self, "modulate:a", 1.0, 0.35)
	else:
		modulate.a = 1.0
