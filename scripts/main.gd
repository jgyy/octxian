extends Control

func _ready() -> void:
	var title := Label.new()
	title.text = "JADE VOW\nA thousand paths. One promise."
	title.position = Vector2(100, 180)
	title.add_theme_font_size_override("font_size", 72)
	add_child(title)
