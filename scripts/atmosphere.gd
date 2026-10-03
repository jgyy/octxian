extends Control

const EFFECTS := ["lanterns", "rain", "reed_light", "bell", "qi", "first_trace", "none"]
const FIRST_TRACE = preload("res://assets/art/effects/first_qi_trace.png")
var clock := 0.0
var effect := "lanterns"
var paused := false
var enabled := true:
	set(value):
		enabled = value
		queue_redraw()

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE

func set_effect(value: String) -> void:
	var selected := value if EFFECTS.has(value) else "lanterns"
	if selected != effect:
		effect = selected
		clock = 0.0
	queue_redraw()

func _process(delta: float) -> void:
	if enabled and not paused and effect != "none":
		clock += delta
		queue_redraw()

func _draw() -> void:
	if not enabled or effect == "none":
		return
	var stage := Vector2(maxf(size.x, 1.0), maxf(size.y, 1.0))
	if effect == "first_trace":
		var extent := Vector2(360.0, 240.0) * (stage.x / 1600.0)
		var center := stage * Vector2(0.76, 0.48)
		var opacity := 0.24 + (sin(clock * 0.8) + 1.0) * 0.07
		draw_texture_rect(FIRST_TRACE, Rect2(center - extent / 2.0, extent), false, Color(1.0, 1.0, 1.0, opacity))
	elif effect == "rain":
		for i in range(95):
			var x := fposmod(i * 173.3 - clock * 37.0, stage.x)
			var y := fposmod(i * 89.7 + clock * (280.0 + i % 7 * 12.0), stage.y)
			draw_line(Vector2(x, y), Vector2(x - 4.0, y + 17.0), Color(0.73, 0.86, 0.91, 0.17), 1.0)
	elif effect == "bell":
		var phase := fposmod(clock, 5.0) / 5.0
		var center := stage * Vector2(0.69, 0.39)
		for ring in range(3):
			draw_arc(center, 26.0 + phase * 220.0 + ring * 27.0, 0.0, TAU, 80, Color(0.88, 0.76, 0.46, (1.0 - phase) * 0.13), 1.8, true)
	else:
		var reed := effect == "reed_light"
		var qi := effect == "qi"
		var tint := Color(0.49, 0.89, 0.83) if reed or qi else Color(0.82, 0.88, 0.73)
		for i in range(42 if not qi else 64):
			var x := fposmod(i * 173.3 + clock * (8.0 + i % 5), stage.x)
			var y := fposmod(i * 89.7 - clock * (16.0 if reed or qi else 9.0) + stage.y, stage.y)
			var glow := (sin(clock * 0.6 + i) + 1.0) * 0.09 + 0.06
			tint.a = glow
			if reed:
				draw_line(Vector2(x, y), Vector2(x + 2.0, y - 13.0), tint, 1.5)
			else:
				draw_circle(Vector2(x, y), 1.2 + i % 3, tint)
