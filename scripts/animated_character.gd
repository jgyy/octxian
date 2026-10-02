extends Node2D

const LOOPS := ["idle", "channeling", "wind", "resolve"]
var sprite := AnimatedSprite2D.new()
var character := ""
var motion := "idle"

func _ready() -> void:
	add_child(sprite)

func show_character(id: String, animation: String = "idle") -> void:
	if not LOOPS.has(animation):
		animation = "idle"
	if character == id and motion == animation:
		return
	character = id
	motion = animation
	var path := "res://assets/generated/sprites/%s_%s.png" % [id, animation]
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
			frame.region = Rect2(Vector2(i % 8, i / 8) * cell, cell)
			frames.add_frame("cycle", frame)
		sprite.sprite_frames = frames
		sprite.scale = Vector2.ONE * (730.0 / cell.y)
		sprite.play("cycle")
	else:
		var atlas: Texture2D = load("res://assets/art/cast.png")
		var frame := AtlasTexture.new()
		frame.atlas = atlas
		var index := ["lin_yue", "shen_qing", "elder_yun", "mo_ran"].find(id)
		frame.region = Rect2(maxi(index, 0) * atlas.get_width() / 4.0, 0, atlas.get_width() / 4.0, atlas.get_height())
		var frames := SpriteFrames.new()
		frames.add_frame("default", frame)
		sprite.sprite_frames = frames
		sprite.scale = Vector2.ONE * (730.0 / atlas.get_height())
	modulate.a = 0.0
	create_tween().tween_property(self, "modulate:a", 1.0, 0.35)
