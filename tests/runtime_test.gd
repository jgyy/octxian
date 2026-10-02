extends SceneTree

var failures: Array[String] = []

func check(condition: bool, message: String) -> void:
	if not condition:
		failures.append(message)
		push_error(message)

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var scene: PackedScene = load("res://scenes/main.tscn")
	var game = scene.instantiate()
	root.add_child(game)
	await process_frame
	check(not game.is_reading, "Game should open on title")
	game._begin()
	check(game.is_reading and game.dialogue != null, "Begin should display dialogue")
	game._advance()
	check(game.dialogue.visible_characters == -1, "Advance should complete typewriter first")
	game._advance()
	check(game.state.current == "pendant", "Next advance should move to next scene")
	game.state.current = "first_choice"
	game._scene()
	game.dialogue.visible_characters = -1
	game._choose(0)
	check(game.state.current == "trust", "UI choice should change story")
	game._settings()
	check(game.popup != null, "Settings should open")
	var current: String = game.state.current
	game._advance()
	check(game.state.current == current, "Modal should pause advance")
	game._close_popup()
	game._journal()
	check(game.popup != null, "Journal should open")
	game._close_popup()
	game._motion_changed(true)
	check(not game.atmosphere.enabled and game.actor.sprite.speed_scale == 0.0, "Reduced motion should stop animation")
	game._motion_changed(false)
	game._toggle_voice()
	check(not game.audio.enabled, "Voice toggle should disable narration")
	game._title()
	check(not game.is_reading, "Menu should return to title")
	for id in ["lin_yue", "shen_qing", "elder_yun", "mo_ran"]:
		for motion in game.actor.LOOPS:
			game.actor.show_character(id, motion)
			check(game.actor.sprite.sprite_frames.get_frame_count("cycle") == 64, "Every character/motion must have 64 real frames")
			check(game.actor.sprite.is_playing(), "Every sprite should animate")
			await process_frame
	DirAccess.remove_absolute("user://settings.cfg")
	game.queue_free()
	await process_frame
	game = null
	scene = null
	await process_frame
	if failures.is_empty():
		print("JADE_VOW_RUNTIME_TESTS_OK: UI, modals, accessibility, voices and 16 animated cycles")
	call_deferred("quit", 0 if failures.is_empty() else 1)
