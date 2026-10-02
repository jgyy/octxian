extends Control

var clock := 0.0
var enabled := true

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE

func _process(delta: float) -> void:
	if enabled:
		clock += delta
		queue_redraw()

func _draw() -> void:
	for i in range(42):
		var x := fmod(i * 173.3 + clock * (8.0 + i % 5), 1600.0)
		var y := fmod(i * 89.7 - clock * (9.0 + i % 3) + 1800.0, 900.0)
		var glow := (sin(clock * 0.6 + i) + 1.0) * 0.12 + 0.08
		draw_circle(Vector2(x, y), 1.2 + i % 3, Color(0.82, 0.88, 0.73, glow))
