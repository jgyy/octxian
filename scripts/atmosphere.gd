extends Control

const EFFECTS := ["lanterns", "rain", "reed_light", "bell", "qi", "first_trace", "paired_trace", "second_pair_trace", "storm_discharge", "snow", "mist", "dust", "heat_haze", "embers", "petals", "sea_spray", "none"]
const FIRST_TRACE = preload("res://assets/art/effects/first_qi_trace.png")
const PAIRED_TRACE = preload("res://assets/art/effects/paired_channel_trace.png")
const SECOND_PAIR_TRACE = preload("res://assets/art/effects/second_pair_trace.png")
const STORM_DISCHARGE = preload("res://assets/art/effects/storm_discharge.png")
var clock := 0.0
var effect := "lanterns"
var layers: Array[String] = ["lanterns"]
var paused := false
var enabled := true:
	set(value):
		enabled = value
		queue_redraw()

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE

func set_effects(values: Array) -> void:
	var selected: Array[String] = []
	for value in values:
		if EFFECTS.has(str(value)) and not selected.has(str(value)) and selected.size() < 3:
			selected.append(str(value))
	if selected.is_empty():
		selected.append("none")
	if selected != layers:
		layers = selected
		effect = layers[0]
		clock = 0.0
	queue_redraw()

func set_effect(value: String) -> void:
	set_effects([value])

func _process(delta: float) -> void:
	if enabled and not paused and layers != ["none"]:
		clock += delta
		queue_redraw()

func _draw() -> void:
	if not enabled:
		return
	for layer in layers:
		_draw_layer(layer)

func _draw_layer(selected: String) -> void:
	if selected == "none":
		return
	var stage := Vector2(maxf(size.x, 1.0), maxf(size.y, 1.0))
	if selected == "storm_discharge":
		var extent := Vector2(540.0, 360.0) * (stage.x / 1600.0)
		var center := stage * Vector2(0.41, 0.45)
		var opacity := 0.56 + sin(clock * 0.8) * 0.08
		draw_texture_rect(STORM_DISCHARGE, Rect2(center - extent / 2.0, extent), false, Color(1.0, 1.0, 1.0, opacity))
	elif selected == "first_trace" or selected == "paired_trace" or selected == "second_pair_trace":
		var extent := Vector2(360.0, 240.0) * (stage.x / 1600.0)
		var center := stage * Vector2(0.76, 0.48)
		var opacity := 0.24 + (sin(clock * 0.8) + 1.0) * 0.07
		var trace: Texture2D = SECOND_PAIR_TRACE if selected == "second_pair_trace" else (PAIRED_TRACE if selected == "paired_trace" else FIRST_TRACE)
		draw_texture_rect(trace, Rect2(center - extent / 2.0, extent), false, Color(1.0, 1.0, 1.0, opacity))
	elif selected == "rain":
		for i in range(95):
			var x := fposmod(i * 173.3 - clock * 37.0, stage.x)
			var y := fposmod(i * 89.7 + clock * (280.0 + i % 7 * 12.0), stage.y)
			draw_line(Vector2(x, y), Vector2(x - 4.0, y + 17.0), Color(0.73, 0.86, 0.91, 0.17), 1.0)
	elif selected == "bell":
		var phase := fposmod(clock, 5.0) / 5.0
		var center := stage * Vector2(0.69, 0.39)
		for ring in range(3):
			draw_arc(center, 26.0 + phase * 220.0 + ring * 27.0, 0.0, TAU, 80, Color(0.88, 0.76, 0.46, (1.0 - phase) * 0.13), 1.8, true)
	elif selected == "mist" or selected == "heat_haze":
		for band in range(5):
			var y := stage.y * (0.28 + band * 0.105) + sin(clock * 0.22 + band) * 9.0
			var tint := Color(0.74, 0.84, 0.85, 0.035) if selected == "mist" else Color(0.94, 0.78, 0.53, 0.025)
			draw_style_box(_haze_style(tint), Rect2(-60, y, stage.x + 120, 42))
	elif selected in ["snow", "dust", "embers", "petals", "sea_spray"]:
		for i in range(44):
			var falling := selected == "snow" or selected == "petals" or selected == "sea_spray"
			var x := fposmod(i * 173.3 + clock * (9.0 + i % 5) + sin(clock * 0.4 + i) * 18.0, stage.x)
			var y := fposmod(i * 89.7 + clock * (22.0 if falling else -12.0) + stage.y, stage.y)
			var tint := Color(0.9, 0.94, 1.0, 0.25)
			if selected == "dust":
				tint = Color(0.84, 0.7, 0.49, 0.13)
			elif selected == "embers":
				tint = Color(1.0, 0.57, 0.23, 0.24)
			elif selected == "petals":
				tint = Color(0.94, 0.72, 0.77, 0.28)
			if selected == "petals":
				draw_line(Vector2(x, y), Vector2(x + 3.0, y + 1.0), tint, 2.0, true)
			else:
				draw_circle(Vector2(x, y), 1.0 + i % 3, tint)
	else:
		var reed := selected == "reed_light"
		var qi := selected == "qi"
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

func _haze_style(tint: Color) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = tint
	style.set_corner_radius_all(20)
	return style
