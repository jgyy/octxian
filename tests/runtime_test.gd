extends SceneTree

var failures: Array[String] = []

func check(condition: bool, message: String) -> void:
	if not condition:
		failures.append(message)
		push_error(message)


func _pose_difference(frames: SpriteFrames) -> float:
	var first := frames.get_frame_texture("cycle", 0).get_image()
	var opposite := frames.get_frame_texture("cycle", 32).get_image()
	if first == null or opposite == null:
		return 0.0
	var body := 0
	var changed := 0
	for y in range(0, floori(first.get_height() * 0.60), 4):
		for x in range(0, first.get_width(), 4):
			var a := first.get_pixel(x, y)
			var b := opposite.get_pixel(x, y)
			if maxf(a.a, b.a) < 0.63:
				continue
			body += 1
			var delta := Vector3(a.r * a.a - b.r * b.a, a.g * a.a - b.g * b.a, a.b * a.a - b.b * b.a)
			if delta.length_squared() > 3.0 * pow(24.0 / 255.0, 2):
				changed += 1
	return float(changed) / maxf(body, 1)

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
	game._cast()
	check(game.wardrobe_previews.size() == 4, "Wardrobe should have an animated preview for every character")
	var selector: OptionButton = game.popup.find_child("Outfit_shen_qing", true, false)
	check(selector != null and selector.item_count == 3, "Each character should have three clothing options")
	var before_node: String = game.state.current
	var before_stats: Dictionary = game.state.stats.duplicate()
	selector.select(1)
	selector.emit_signal("item_selected", 1)
	check(game.wardrobe.selected("shen_qing") == "training", "Dropdown should choose the training outfit")
	check(game.actor.outfit == "training", "Current scene should use the chosen outfit immediately")
	check(game.wardrobe_previews["shen_qing"].outfit == "training", "Preview should use the chosen outfit")
	check(game.state.current == before_node and game.state.stats == before_stats, "Clothing changes must preserve the story")
	check(game.wardrobe_previews["shen_qing"].sprite.is_playing(), "Clothing previews must animate")
	game._set_outfit("lin_yue", "festival")
	var settings := ConfigFile.new()
	check(settings.load("user://settings.cfg") == OK, "Wardrobe preferences should be saved")
	check(settings.get_value("wardrobe", "choices", {})["lin_yue"] == "festival", "Each character's preference should persist")
	game.wardrobe.restore({})
	game._load_settings()
	check(game.wardrobe.selected("lin_yue") == "festival" and game.wardrobe.selected("shen_qing") == "training", "Reload should restore independent clothing choices")
	check(not game._set_outfit("lin_yue", "unknown"), "Unknown clothing choices should be rejected")
	var restored = game.Wardrobe.new()
	restored.restore({"lin_yue": "unknown", "shen_qing": "festival", "missing_character": "training"})
	check(restored.selected("lin_yue") == "sect" and restored.selected("shen_qing") == "festival", "Damaged wardrobe settings should fall back to robes")
	check(restored.selections.size() == 4, "Settings must not introduce unknown characters")
	game._close_popup()
	game._scene()
	check(game.actor.outfit == "training", "Selected clothing should survive scene rebuilds")
	game._motion_changed(true)
	game._cast()
	check(game.wardrobe_previews["lin_yue"].sprite.speed_scale == 0.0, "Reduced motion should stop wardrobe previews")
	game._close_popup()
	game._motion_changed(false)
	game._title()
	check(game.actor.outfit == "festival", "Title should use the selected Lin Yue clothing")
	check(not game.is_reading, "Menu should return to title")
	for id in game.Wardrobe.CHARACTERS:
		for clothing in game.wardrobe.options():
			for motion in game.actor.LOOPS:
				game.actor.show_character(id, motion, str(clothing["id"]))
				check(game.actor.outfit == clothing["id"], "Every character outfit should load")
				check(game.actor.sprite.sprite_frames.get_frame_count("cycle") == 64, "Every outfit/motion must have 64 real frames")
				check(game.actor.sprite.is_playing(), "Every outfit must animate")
				check(_pose_difference(game.actor.sprite.sprite_frames) >= 0.20, "%s/%s/%s must visibly change its upper-body pose" % [id, clothing["id"], motion])
				await process_frame
	await create_timer(0.2).timeout
	check(game.actor.sprite.frame > 0, "Actual sprite playback should advance animation frames")
	game.audio.shutdown()
	await create_timer(0.25).timeout
	DirAccess.remove_absolute("user://settings.cfg")
	game.queue_free()
	await process_frame
	game = null
	scene = null
	await process_frame
	if failures.is_empty():
		print("JADE_VOW_RUNTIME_TESTS_OK: UI, saved wardrobes, accessibility, voices and 48 animated outfit cycles")
	call_deferred("quit", 0 if failures.is_empty() else 1)
