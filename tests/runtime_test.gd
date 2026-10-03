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
	await _test_narration_formats(game)
	check(not game.is_reading, "Game should open on title")
	await _test_attribute_ui(game)
	_test_cultivation_ui(game)
	_test_foundry_ui(game)
	_test_modal_rebuilds(game)
	game._begin()
	check(game.is_reading and game.dialogue != null, "Begin should display dialogue")
	game._advance()
	check(game.dialogue.visible_characters == -1, "Advance should complete typewriter first")
	game._advance()
	check(game.state.current == "mortal_001", "Next advance should enter mortal recruitment before the upper gate")
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

	game._interiors()
	var interiors: Array = game._interior_entries()
	check(not interiors.is_empty(), "Interior gallery must contain delivered building paintings")
	for index in range(interiors.size()):
		game._interior_selected(index)
		var native: Array = interiors[index].native_size
		check(game.interior_image.texture != null and game.interior_image.texture.get_size() == Vector2(native[0], native[1]), "Every interior must load at its recorded native size")
	var interior_selector: OptionButton = game.popup.find_child("InteriorSelector", true, false)
	check(interior_selector.selected == interiors.size() - 1, "Programmatic interior selection must update the caption")
	var interior_texture: Texture2D = game.interior_image.texture
	game._interior_selected(-1)
	game._interior_selected(interiors.size())
	check(game.interior_image.texture == interior_texture, "Invalid interior selections must preserve the current painting")
	game._close_popup()
	game._interior_selected(0)
	check(game.popup == null, "Selection after closing the interior gallery must be harmless")

	game._items()
	check(game.item_image.texture.get_size() == Vector2(1024, 1536), "Object inspection must retain native artwork")
	check(game.item_description.text.contains("custody"), "Inspection must explain the object's keeper")
	game._item_selected(1)
	check(game.item_image.texture.get_size() == Vector2(1536, 1024), "Landscape object art must retain its native aspect")
	var object_selector: OptionButton = game.popup.find_child("ObjectSelector", true, false)
	check(object_selector.selected == 1 and object_selector.get_item_text(1) == "A Sealed Echo Case", "Programmatic object selection must update its caption")
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
	game.state.current = "orchard_arrival"
	game._scene()
	check(game.actor.character == "ren_qiao" and game.actor.sprite.texture.get_size() == Vector2(1024, 1536), "Orchard healer must load his retained native original")
	game.state.current = "orchard_hart_answer"
	game._scene()
	check(game.actor.character == "frostroot_hart" and game.actor.sprite.texture.get_size() == Vector2(1024, 1536), "Frostroot Hart must load its own native original")
	await _test_city_ui(game)
	await _test_court_ui(game)
	game.state.current = "orchard_resolution_choice"
	game._scene()
	game.dialogue.visible_characters = -1
	var heart_before: int = game.state.stats.trust
	game._choose(3)
	check(game.state.current == "orchard_pause" and game.state.stats.trust == heart_before + 2, "Book IV must retain an available settlement and apply its attribute effects")
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
	DirAccess.remove_absolute("user://settings.cfg")
	# Use the production exit path: free the players before its audio-drain timer
	# ends, rather than waiting while they are alive and quitting just after free.
	game.set_process(false)
	game._quit_game(0 if failures.is_empty() else 1)
	check(not game.audio.music.finished.is_connected(game.audio.music.play), "Shutdown must disconnect the repeating score")
	for player in [game.audio.music, game.audio.effects, game.audio.voice]:
		check(not player.playing and player.stream == null, "Shutdown must stop and release every audio stream")
	game = null
	scene = null
	if failures.is_empty():
		print("JADE_VOW_RUNTIME_TESTS_OK: UI, saved wardrobes, accessibility, voices and 48 whole-body bob combinations")

func _test_attribute_ui(game) -> void:
	var shortcut := InputEventKey.new()
	shortcut.keycode = KEY_C
	shortcut.pressed = true
	check(game.ui.find_child("AttributesButton", true, false) != null, "Title must offer the attributes panel")
	game._unhandled_key_input(shortcut)
	_check_attribute_panel(game)
	await process_frame
	check(game.popup.get_global_rect().end.y <= 900.0, "Attribute cards must fit inside the viewport")
	check(not game.is_reading and game.state.current == "arrival", "Opening attributes from the title must preserve the journey")
	game._close_popup()
	check(not game.atmosphere.paused, "Closing attributes must resume scene effects")

	game._begin()
	game.state.current = "first_choice"
	game._scene()
	game._advance()
	var choice_button: Button = game.choice_box.find_child("Choice_0", true, false)
	var choice_details: Label = game.choice_box.find_child("ChoiceDetails_0", true, false)
	check(game.choice_box.get_child_count() == 3 and game.choice_box.get_child(0) is VBoxContainer, "Each choice must have its own card")
	check(choice_button != null and not choice_button.disabled, "Playable choices must remain enabled")
	check(choice_details != null and choice_details.is_visible_in_tree() and choice_details.text.contains("Qi Control +1") and choice_details.text.contains("Dao Heart +2"), "Choice gains must be visible before selection")

	game.dialogue.visible_characters = 1
	game.text_clock = 1.0
	game.auto_clock = 1.25
	game.auto_read = true
	game.fast_read = true
	var before_stats: Dictionary = game.state.stats.duplicate()
	var before_history: Array = game.state.history.duplicate(true)
	var attributes_button: Button = game.ui.find_child("AttributesButton", true, false)
	check(attributes_button != null, "Reading must offer the attributes panel")
	if attributes_button != null:
		attributes_button.emit_signal("pressed")
	_check_attribute_panel(game)
	var effect_clock: float = game.atmosphere.clock
	game._process(3.0)
	game.atmosphere._process(3.0)
	game._advance()
	game._choose(0)
	check(game.state.current == "first_choice" and game.state.stats == before_stats and game.state.history == before_history, "The attributes modal must block story choices and advancement")
	check(game.dialogue.visible_characters == 1 and game.text_clock == 1.0 and game.auto_clock == 1.25, "The attributes modal must pause typewriter, fast and automatic reading")
	check(game.atmosphere.clock == effect_clock, "The attributes modal must freeze scene effects")
	game._close_popup()
	game.auto_read = false
	game.fast_read = false
	game._advance()
	game._choose(0)
	check(game.state.current == "trust" and game.state.stats.qi == 1 and game.state.stats.trust == 2, "Closing attributes must restore choice interaction")
	check(game.status_label.text.contains("Qi Control +1") and game.status_label.text.contains("Dao Heart +2"), "Choice gains must appear on the resulting scene")
	var totals: Label = game.ui.find_child("AttributeTotals", true, false)
	check(totals != null and totals.text.contains("CONTROL 01") and totals.text.contains("DAO HEART 02"), "Scene totals must refresh after gaining attributes")
	game._unhandled_key_input(shortcut)
	_check_attribute_panel(game)
	game._close_popup()

	game.state.current = "final_choice"
	game._scene()
	game._advance()
	choice_button = game.choice_box.find_child("Choice_0", true, false)
	choice_details = game.choice_box.find_child("ChoiceDetails_0", true, false)
	check(choice_button != null and choice_button.disabled and choice_button.tooltip_text.contains("Qi Control 1/3"), "Locked choices must be disabled and explain their gate")
	check(choice_details != null and choice_details.is_visible_in_tree() and choice_details.text.contains("Locked") and choice_details.text.contains("Qi Control 1/3") and choice_details.text.contains("Dao Heart +1"), "Locked requirements and possible gains must remain visible")
	game.state.stats.qi = 3
	game._scene()
	game._advance()
	choice_button = game.choice_box.find_child("Choice_0", true, false)
	choice_details = game.choice_box.find_child("ChoiceDetails_0", true, false)
	check(choice_button != null and not choice_button.disabled, "Reaching the threshold must unlock the rebuilt choice")
	check(choice_details != null and choice_details.text.contains("Requires") and choice_details.text.contains("Qi Control 3/3"), "Satisfied requirements must refresh with current values")
	game._attributes()
	_check_attribute_panel(game)
	game._close_popup()

	# Check the actual containers after Godot has laid out every authored choice.
	for id in game.state.story.nodes:
		if not game.state.story.nodes[id].has("choices"):
			continue
		game.state.current = id
		game._scene()
		game._advance()
		await process_frame
		for card in game.choice_box.get_children():
			check(card.get_global_rect().end.y <= 568.0, "Choice cards and attribute summaries must clear the dialogue: " + id)
	game._begin()
	check(game.state.history.is_empty() and game.state.stats == {"qi": 0, "trust": 0, "insight": 0, "resolve": 0}, "A new journey must reset attribute gains and history")
	game._attributes()
	_check_attribute_panel(game)
	game._close_popup()
	game._title()

func _check_attribute_panel(game) -> void:
	check(game.popup != null and game.popup.name == "AttributePanel", "Attributes must open the named modal")
	if game.popup == null:
		return
	check(game.atmosphere.paused, "Attributes must pause scene effects")
	for key in game.StoryState.Attributes.KEYS:
		var profile: Dictionary = game.StoryState.Attributes.profile(key, game.state.stats[key])
		var value_label: Label = game.popup.find_child("AttributeValue_" + key, true, false)
		var rank_label: Label = game.popup.find_child("AttributeRank_" + key, true, false)
		var progress: ProgressBar = game.popup.find_child("AttributeProgress_" + key, true, false)
		check(value_label != null and value_label.text == "%s · %d" % [profile.name, profile.value], "Every attribute card must show its current name and value")
		check(rank_label != null and rank_label.text.contains(str(profile.rank)), "Every attribute card must show its current rank")
		check(progress != null and progress.max_value > 0.0 and is_equal_approx(progress.value / progress.max_value, profile.progress), "Attribute progress bars must match the current rank")

func _test_city_ui(game) -> void:
	game.state.current = "city_arrival"
	game._scene()
	check(game.background.texture != null and game.background.texture.get_size() == Vector2(1536, 1024), "The city market must load its retained native painting")
	var encounters := {
		"city_mask_studio": "qiao_sen",
		"city_registry_mei": "mei_dulan",
		"city_registry_tao": "tao_wen",
		"city_perfumer_workroom": "fei_nuo",
		"city_courser_terms": "porcelain_courser",
		"city_perfumer_moth_terms": "glasswing_moth"
	}
	for scene_id in encounters:
		game.state.current = scene_id
		game._scene()
		var portrait: Texture2D = game.actor.sprite.texture
		check(game.actor.character == encounters[scene_id] and portrait != null, "City encounters must load their own registered original: " + scene_id)
		if portrait == null:
			continue
		check(portrait.get_size() == Vector2(1024, 1536), "City portraits must retain native resolution: " + scene_id)
		check(is_equal_approx(game.actor.sprite.scale.x, game.actor.sprite.scale.y), "City portraits must fit without stretching: " + scene_id)
		check(is_equal_approx(portrait.get_height() * game.actor.sprite.scale.y, 680.0), "City portraits must use the dialogue stage height: " + scene_id)
		game.actor.display_height = 350.0
		game.actor.show_character(str(encounters[scene_id]))
		game._scene()
		check(is_equal_approx(portrait.get_height() * game.actor.sprite.scale.y, 680.0), "Cached city portraits must resize when returning from previews: " + scene_id)

	game.state.current = "city_final_choice"
	game.state.stats = {"qi": 0, "trust": 0, "insight": 0, "resolve": 0}
	game._scene()
	game._advance()
	await process_frame
	for index in range(2):
		var blocked: Button = game.choice_box.find_child("Choice_" + str(index), true, false)
		var summary: Label = game.choice_box.find_child("ChoiceDetails_" + str(index), true, false)
		check(blocked != null and blocked.disabled, "Untrained city settlement choices must remain locked")
		check(summary != null and summary.text.contains("Locked"), "City settlement gates must be visible before choosing")
	var fallback: Button = game.choice_box.find_child("Choice_3", true, false)
	check(fallback != null and not fallback.disabled, "The city audit must remain available without attribute training")
	var before_stats: Dictionary = game.state.stats.duplicate()
	var before_history: Array = game.state.history.duplicate(true)
	game._choose(0)
	check(game.state.current == "city_final_choice" and game.state.stats == before_stats and game.state.history == before_history, "A locked city UI choice must preserve the journey")
	game._choose(3)
	check(game.state.current == "city_batch_audit", "The unrestricted city settlement must remain playable through the UI")


func _test_narration_formats(game) -> void:
	var manifest = JSON.parse_string(FileAccess.get_file_as_string("res://assets/generated/voices/manifest.json"))
	check(manifest is Dictionary and manifest.get("lines") is Dictionary, "Narration records must be available at runtime")
	if not manifest is Dictionary or not manifest.get("lines") is Dictionary:
		return
	var enabled_before: bool = game.audio.enabled
	game.audio.enabled = true
	for extension in ["wav", "ogg"]:
		for id in manifest.lines:
			if not str(manifest.lines[id].get("file", "")).ends_with("." + extension):
				continue
			game.audio.speak(id)
			await process_frame
			var stream = game.audio.voice.stream
			check(stream != null, "The audio director must load authored %s narration" % extension)
			if stream != null:
				check(stream.get_length() > 0.0, "Narration playback must have a real duration")
				if extension == "ogg":
					check(stream is AudioStreamOggVorbis, "New narration must load as native Vorbis audio")
				else:
					check(stream is AudioStreamWAV, "Legacy narration must retain WAV playback")
			game.audio.voice.stop()
			game.audio.voice.stream = null
			break
	game.audio.enabled = enabled_before


func _test_court_ui(game) -> void:
	check(game.state.story.chapters.has("book_vi"), "The runtime must load the modular court chapter")
	var encounters := {
		"court_upper_bench": "he_lian",
		"court_luo_shan": "luo_shan",
		"court_bai_qun": "bai_qun",
		"court_du_heng": "du_heng",
		"court_rain_heron": "rain_heron"
	}
	for scene_id in encounters:
		game.state.current = scene_id
		game._scene()
		var portrait: Texture2D = game.actor.sprite.texture
		var expected_size := _court_world_size(game, str(encounters[scene_id]))
		check(game.actor.character == encounters[scene_id] and portrait != null, "Every court participant must load its own registered original: " + scene_id)
		check(expected_size != Vector2.ZERO, "Court participants must retain their native catalog record: " + scene_id)
		if portrait != null:
			check(portrait.get_size() == expected_size, "Court portraits must retain their actual native pixels: " + scene_id)
			check(is_equal_approx(game.actor.sprite.scale.x, game.actor.sprite.scale.y), "Court portraits must fit without stretching: " + scene_id)
			check(is_equal_approx(portrait.get_height() * game.actor.sprite.scale.y, 680.0), "Court portraits must use the dialogue stage height: " + scene_id)
		var background_id := str(game.state.node().background)
		check(game.background.texture != null and game.background.texture.get_size() == _court_world_size(game, background_id), "Court scenes must load their registered native environment: " + scene_id)

	game.state.current = "court_weather_setup"
	game._scene()
	check(game.actor.character == "lin_yue", "The weather setup must stage Lin Yue's demonstration")
	check(game.background.texture != null and game.background.texture.get_size() == _court_world_size(game, "rain_court_terrace"), "The ordinary signal demonstration must use the sheltered terrace painting")

	game.state.current = "court_investigation_choice"
	game.state.stats = {"qi": 0, "trust": 0, "insight": 0, "resolve": 0}
	game._scene()
	game._advance()
	await process_frame
	check(game.choice_box.get_child_count() == 4, "The court inquiry hub must display four independent teams")
	for index in range(4):
		var available: Button = game.choice_box.find_child("Choice_" + str(index), true, false)
		check(available != null and not available.disabled, "Every court investigation must remain available in the untrained UI")
	for card in game.choice_box.get_children():
		check(card.get_global_rect().end.y <= 568.0, "All four court routes must clear the dialogue")

	game.state.current = "court_final_choice"
	game._scene()
	game._advance()
	await process_frame
	for index in range(3):
		var blocked: Button = game.choice_box.find_child("Choice_" + str(index), true, false)
		var summary: Label = game.choice_box.find_child("ChoiceDetails_" + str(index), true, false)
		check(blocked != null and blocked.disabled, "Untrained specialized court remedies must be locked in the UI")
		check(summary != null and summary.text.contains("Locked") and summary.text.contains("0/4"), "Court remedy thresholds and gains must be visible")
	var fallback: Button = game.choice_box.find_child("Choice_3", true, false)
	check(fallback != null and not fallback.disabled, "The dated court remand must remain available without training")
	var before_stats: Dictionary = game.state.stats.duplicate()
	var before_history: Array = game.state.history.duplicate(true)
	game._choose(0)
	check(game.state.current == "court_final_choice" and game.state.stats == before_stats and game.state.history == before_history, "A locked court UI remedy must preserve the journey")
	game._choose(3)
	check(game.state.current == "court_remand_proposal" and game.state.stats.trust == 2, "The ungated court remedy must advance through the UI and apply Dao Heart")

func _court_world_size(game, id: String) -> Vector2:
	for group in ["backgrounds", "npcs", "monsters"]:
		for entry in game.world.get(group, []):
			if entry.id == id:
				return Vector2(entry.native_size[0], entry.native_size[1])
	return Vector2.ZERO

func _test_modal_rebuilds(game) -> void:
	game._begin()
	game._settings()
	check(game.atmosphere.paused, "Opening a modal must pause the scene")
	# The footer remains reachable while the modal is open.
	var menu: Button
	for child in game.ui.get_children():
		if child is Button and child.text == "Menu":
			menu = child
	check(menu != null, "Reading must offer the Menu button")
	if menu != null:
		menu.emit_signal("pressed")
	check(game.popup == null and not game.is_reading and not game.atmosphere.paused, "Returning to the title from a modal must resume its effects")
	var clock: float = game.atmosphere.clock
	game.atmosphere._process(0.5)
	check(game.atmosphere.clock > clock, "Title effects must actually progress after dismissing a modal through Menu")

	game._attributes()
	game._begin()
	check(game.popup == null and game.is_reading and not game.atmosphere.paused, "Beginning a journey from a modal must resume scene effects")
	game._journal()
	game.state.current = "pendant"
	game._scene()
	check(game.popup == null and not game.atmosphere.paused, "Rebuilding dialogue must clear the modal pause")
	game._title()

func _test_cultivation_ui(game) -> void:
	game._begin()
	game._attributes()
	var button: Button = game.popup.find_child("CultivationButton", true, false)
	check(button != null, "Attributes must link to the cultivation codex")
	if button != null:
		button.emit_signal("pressed")
	check(game.popup != null and game.popup.name == "CultivationPanel", "Cultivation must open its named panel")
	check(game.atmosphere.paused, "Cultivation codex must pause scene effects")
	var before_stats: Dictionary = game.state.stats.duplicate()
	var before_history: Array = game.state.history.duplicate(true)
	var selector: OptionButton = game.popup.find_child("CultivationSelector", true, false)
	var detail: RichTextLabel = game.popup.find_child("CultivationDetail", true, false)
	check(selector != null and selector.item_count == 16, "Codex must expose twelve realms and four practice references")
	if selector != null and detail != null:
		for index in range(selector.item_count):
			game._cultivation_selected(index)
			check(selector.selected == index and not detail.text.is_empty(), "Every codex selection must show its own reference")
		var retained_text: String = detail.text
		game._cultivation_selected(-1)
		game._cultivation_selected(selector.item_count)
		check(detail.text == retained_text, "Invalid codex selections must preserve the reference")
	game._advance()
	game._choose(0)
	check(game.state.current == "arrival" and game.state.stats == before_stats and game.state.history == before_history, "Codex browsing must preserve the journey")
	var mortal_label: String = game._cultivation_label(game.state.node())
	game.state.stats.qi = game.StoryState.MAX_STAT
	check(game._cultivation_label(game.state.node()) == mortal_label and mortal_label.begins_with("Mortal"), "Attribute points must never promote an authored mortal realm")
	game.state.stats = before_stats
	game._close_popup()
	check(not game.atmosphere.paused, "Closing the codex must resume scene effects")
	for sample in [{"node": "han_mei_shift", "actor": "han_mei"}, {"node": "mortal_mite_choice", "actor": "furnace_mite"}]:
		game.state.current = sample.node
		game._scene()
		check(game.actor.character == sample.actor and game.actor.sprite.texture != null, "New cultivation portraits must render")
		if game.actor.sprite.texture != null:
			check(game.actor.sprite.texture.get_size() == Vector2(1024, 1536), "Cultivation sprites must retain native dimensions")
		check(game.background.texture != null and game.background.texture.get_size() == Vector2(1672, 941), "Mortal training must use the native terrace environment")
	game._items()
	game._item_selected(2)
	check(game.item_image.texture != null and game.item_image.texture.get_size() == Vector2(1024, 1536), "Practice wick must be inspectable at native size")
	game._close_popup()
	for sample in [{"node": "sluice_005", "actor": "duan_zhi"}, {"node": "reed_step_011", "actor": "brine_mantis"}]:
		game.state.current = sample.node
		game._scene()
		check(game.actor.character == sample.actor and game.actor.sprite.texture != null, "Sluice characters must render native portraits")
		if game.actor.sprite.texture != null:
			check(game.actor.sprite.texture.get_size() == Vector2(1024, 1536), "Sluice sprites must retain full native detail")
		check(game.background.texture != null and game.background.texture.get_size() == Vector2(1536, 1024), "Sluice scenes must use their own environment")
	game.state.current = "channels_044"
	game._scene()
	var first_pair: String = game._cultivation_label(game.state.node())
	check(first_pair.contains("3: First pair") and game.atmosphere.effect == "paired_trace", "The earned pair must select its authored realm and native effect")
	game.state.stats.qi = game.StoryState.MAX_STAT
	check(game._cultivation_label(game.state.node()) == first_pair, "A high attribute score cannot skip the first-pair stage")
	game.state.stats = before_stats
	game._items()
	game._item_selected(3)
	check(game.item_image.texture != null and game.item_image.texture.get_size() == Vector2(1024, 1536), "Meridian caliper must be inspectable at native size")
	check(game.atmosphere.paused, "Inspection must pause the paired-channel effect")
	game._close_popup()
	check(not game.atmosphere.paused, "Closing inspection must resume the paired-channel scene")
	game.state.current = "arrival"
	game._title()

func _test_foundry_ui(game) -> void:
	game._begin()
	var before_stats: Dictionary = game.state.stats.duplicate()
	for sample in [
		{"node": "foundry_arrival_003", "actor": "su_yan"},
		{"node": "foundry_arrival_014", "actor": "zhen"},
		{"node": "foundry_creature_002", "actor": "voidglass_centipede"},
		{"node": "foundry_home_004", "actor": "yue_mother"}
	]:
		game.state.current = sample.node
		game._scene()
		check(game.actor.character == sample.actor and game.actor.sprite.texture != null, "Foundry participants must render their independent portraits")
		if game.actor.sprite.texture != null:
			check(game.actor.sprite.texture.get_size() == Vector2(1024, 1536), "Foundry portraits must retain native detail")
		check(game.background.texture != null and game.background.texture.get_size() == Vector2(1536, 1024), "Foundry and home scenes must use their native environments")
	game.state.current = "foundry_earned_002"
	game._scene()
	var earned: String = game._cultivation_label(game.state.node())
	check(earned.contains("4: Second pair") and game.atmosphere.effect == "second_pair_trace", "The earned second pair must select its authored stage and native effect")
	game.state.stats.qi = game.StoryState.MAX_STAT
	check(game._cultivation_label(game.state.node()) == earned, "Choice attributes must not change the fourth-stage certificate")
	game.state.stats = before_stats
	var effect_clock: float = game.atmosphere.clock
	game._items()
	var found_comb := false
	for index in range(game.world.get("items", []).size()):
		if game.world.items[index].id == "phase_comb":
			found_comb = true
			game._item_selected(index)
			check(game.item_image.texture != null and game.item_image.texture.get_size() == Vector2(1024, 1536), "The phase comb must be inspectable at native size")
	check(found_comb, "The phase comb must appear in the item gallery")
	game.atmosphere._process(0.5)
	check(game.atmosphere.clock == effect_clock, "Object inspection must freeze the second-pair effect")
	game._close_popup()
	game._motion_changed(true)
	game.atmosphere._process(0.5)
	check(game.atmosphere.clock == effect_clock and not game.atmosphere.enabled, "Reduced motion must suppress the second-pair effect")
	game._motion_changed(false)
	game.atmosphere._process(0.5)
	check(game.atmosphere.clock > effect_clock, "The second-pair effect must resume when motion is enabled")
	game.state.current = "arrival"
	game._title()
