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
	check(not game.atmosphere.enabled and game.actor.reduced_motion and game.actor.sprite.position.is_zero_approx(), "Reduced motion should stop animation")
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
	check(not game.wardrobe_previews["shen_qing"].reduced_motion, "Clothing previews must animate")
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
	check(game.wardrobe_previews["lin_yue"].reduced_motion, "Reduced motion should stop wardrobe previews")
	game._close_popup()
	game._motion_changed(false)
	game._title()
	check(game.actor.outfit == "festival", "Title should use the selected Lin Yue clothing")
	check(not game.is_reading, "Menu should return to title")
	game.actor.display_height = 640.0
	var cached_portrait: Texture2D = game.actor.sprite.texture
	game._title()
	check(game.actor.sprite.texture == cached_portrait and is_equal_approx(game.actor.sprite.texture.get_height() * game.actor.sprite.scale.y, 730.0), "Cached title portraits must resize when the stage changes")
	for id in game.Wardrobe.CHARACTERS:
		for clothing in game.wardrobe.options():
			for motion in game.actor.LOOPS:
				game.actor.show_character(id, motion, str(clothing["id"]))
				check(game.actor.outfit == clothing["id"], "Every character outfit should load")
				var portrait: Texture2D = game.actor.sprite.texture
				check(portrait != null and portrait.get_size() == Vector2(384, 512), "Every outfit must load one intact portrait")
				game.actor.set_process(false)
				game.actor.reset_motion()
				game.actor._process(1.0)
				var high: float = game.actor.sprite.position.y
				game.actor._process(2.0)
				var low: float = game.actor.sprite.position.y
				check(high > 0.0 and low < 0.0 and absf(high) <= 12.0, "%s/%s/%s must gently bob the whole body" % [id, clothing["id"], motion])
				check(game.actor.sprite.texture == portrait and game.actor.sprite.rotation == 0.0, "Bobbing must preserve the complete portrait")
				game.actor._process(1.0)
				check(game.actor.sprite.position.is_zero_approx(), "The body bob must loop smoothly")
				game.actor.set_reduced_motion(true)
				game.actor._process(1.0)
				check(game.actor.sprite.position.is_zero_approx(), "Reduced motion must leave the body at rest")
				game.actor.set_reduced_motion(false)
				game.actor.set_process(true)
				await process_frame
	game.actor.reset_motion()
	await create_timer(0.2).timeout
	check(absf(game.actor.sprite.position.y) > 0.1, "Actual playback should move the complete portrait")

	game.state.current = "ending_shared"
	game._scene()
	game.dialogue.visible_characters = -1
	game._advance()
	check(game.state.current == "lantern_shared", "UI should continue from Book I into Book II")
	game.state.current = "lantern_hub"
	game._scene()
	game.dialogue.visible_characters = -1
	check(game.actor.character == "su_lan" and game.actor.sprite.texture.get_size() == Vector2(1024, 1536), "Quest keeper should use her native portrait")
	check(game.background.texture.get_size() == Vector2(1672, 941), "Book II should load its new background")
	game._choose(1)
	check(game.state.current == "reed_approach", "Quest hub should branch into the spirit route")
	game.state.current = "reed_voice"
	game._scene()
	check(game.actor.character == "reed_listener", "Spirit should use its own sprite")
	check(game.atmosphere.effect == "reed_light", "Marsh scenes should select reed-light effects")
	game.atmosphere.set_process(false)
	var effect_clock: float = game.atmosphere.clock
	game.atmosphere.paused = true
	game.atmosphere._process(0.5)
	check(game.atmosphere.clock == effect_clock, "Modal pause should freeze scene effects")
	game.atmosphere.paused = false
	game._motion_changed(true)
	game.atmosphere._process(0.5)
	check(game.atmosphere.clock == effect_clock, "Reduced motion should stop effects")
	game._motion_changed(false)
	game.atmosphere._process(0.5)
	check(game.atmosphere.clock > effect_clock, "Enabled effects should resume")
	game.atmosphere.set_process(true)
	var portrait_height: float = game.actor.sprite.texture.get_height() * game.actor.sprite.scale.y
	check(game.actor.position.y - portrait_height / 2.0 - 12.0 > 112.0, "Scene portraits must clear the header throughout their bob")
	check(game.actor.position.y + portrait_height / 2.0 + 12.0 < 830.0, "Scene portraits must remain behind the dialogue panel and clear the footer")
	var speaker_label: Label = game.ui.get_node("SpeakerName")
	var speaker_title: Label = game.ui.get_node("SpeakerTitle")
	check(speaker_title.position.x > speaker_label.position.x + speaker_label.get_minimum_size().x, "Long speaker names and role labels must not overlap")
	game._world()
	check(game.world_previews.size() == 3, "World gallery should show all three asset categories")
	for preview in game.world_previews.values():
		check(preview.image.texture != null, "World gallery should load actual artwork")
	game._close_popup()

	game._items()
	check(game.item_image.texture.get_size() == Vector2(1024, 1536), "Object inspection must retain native artwork")
	check(game.item_description.text.contains("custody"), "Inspection must explain the object's keeper")
	game._item_selected(1)
	check(game.item_image.texture.get_size() == Vector2(1536, 1024), "Landscape object art must retain its native aspect")
	game._item_selected(-1)
	check(game.item_image.texture != null, "Invalid object indices must preserve the preview")
	game._close_popup()

	game.state.current = "river_xiu"
	game._scene()
	check(game.actor.character == "wei_xiu" and game.atmosphere.effect == "rain", "Spring landing must load the new pilot and rain")
	game.state.current = "harbor_answer"
	game._scene()
	check(game.actor.character == "mooring_eel" and game.atmosphere.effect == "none", "Sheltered spirit scene should use its portrait and calm effect")
	check(game.background.texture.get_size() == Vector2(1672, 941), "Harbor must retain the native environment")
	game.state.history.append({"speaker": "narrator", "text": "[b]literal[/b]"})
	game._journal()
	var logs: Array[Node] = game.popup.find_children("*", "RichTextLabel", true, false)
	check(logs.size() == 1 and logs[0].get_parsed_text().contains("[b]literal[/b]"), "Journal must preserve prose rather than interpret markup")
	game._close_popup()
	game.state.history.pop_back()
	check(game.dialogue.scroll_active, "Longer dialogue should remain accessible through scrolling")
	var corrupt := ConfigFile.new()
	corrupt.set_value("reading", "speed", [1, 2])
	corrupt.set_value("reading", "motion", "false")
	corrupt.set_value("reading", "voice", "false")
	corrupt.set_value("audio", "Music", {"broken": true})
	corrupt.save("user://settings.cfg")
	game._load_settings()
	check(game.text_speed == 38.0 and not game.reduced_motion and game.audio.enabled, "Malformed settings should use typed defaults")
	check(AudioServer.get_bus_volume_db(AudioServer.get_bus_index("Music")) == -8.0, "Malformed volume should recover")
	check(game._setting_number(corrupt, "missing", "missing", 38.0, 12.0, 100.0) == 38.0, "Missing numeric settings should use defaults")
	game.audio.shutdown()
	await create_timer(0.25).timeout
	DirAccess.remove_absolute("user://settings.cfg")
	game.queue_free()
	await process_frame
	game = null
	scene = null
	await process_frame
	if failures.is_empty():
		print("JADE_VOW_RUNTIME_TESTS_OK: UI, saved wardrobes, accessibility, voices and 48 whole-body bob combinations")
	call_deferred("quit", 0 if failures.is_empty() else 1)
