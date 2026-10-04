extends SceneTree

const State = preload("res://scripts/story_state.gd")
var failures: Array[String] = []

func check(value: bool, message: String) -> void:
	if not value:
		failures.append(message)
		push_error(message)

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var campaign: Dictionary = State.new().story
	var traveler = State.new(campaign)
	traveler.current = "canal_p01_021"
	var before: Dictionary = traveler.stats.duplicate()
	check(traveler.choose(2) and traveler.stats == before, "Listening preference must not condition tissue or award practice")
	traveler.current = "canal_p01_045"
	check(traveler.advance() and traveler.stats.insight == 1 and traveler.stats.resolve == 0, "Completed source comparison earns comprehension")
	traveler.current = "canal_p01_045"
	check(traveler.advance() and traveler.stats.insight == 1, "Revisiting completed practice must not farm points")
	check(traveler.save_game("user://continuation_test.json"), "Completed practice checkpoint must save")
	var restored = State.new(campaign)
	check(restored.load_game("user://continuation_test.json") and restored.completed_practice == traveler.completed_practice, "Completed reward records must survive save/load")
	restored.current = "canal_p01_045"
	check(restored.advance() and restored.stats.insight == 1, "Loaded practice must remain single-use")
	var invalid = FileAccess.open("user://continuation_bad.json", FileAccess.WRITE)
	invalid.store_string(JSON.stringify({"version": 1, "current": "arrival", "stats": restored.stats, "history": [], "completed_practice": {"arrival": true}}))
	invalid.close()
	var current: String = restored.current
	var retained: Dictionary = restored.stats.duplicate()
	check(not restored.load_game("user://continuation_bad.json") and restored.current == current and restored.stats == retained, "Invalid reward records reject saves atomically")
	for choice_id in ["forest_24_005", "desert_p24_005", "archive_25_006"]:
		for index in range(5):
			var role = State.new(campaign)
			role.current = choice_id
			role.stats = {"qi": 0, "trust": 0, "insight": 0, "resolve": 0}
			check(role.can_choose(role.node().choices[index]) == (index == 4), "Untrained travelers retain only qualified support at " + choice_id)
			role.stats = {"qi": 10, "trust": 10, "insight": 10, "resolve": 10}
			check(role.choose(index), "Training must unlock each distinct role")
			check(role.advance(), "Every performed role rejoins its closing sequence")
	var scene: PackedScene = load("res://scenes/main.tscn")
	var game = scene.instantiate()
	root.add_child(game)
	await process_frame
	game.is_reading = true
	game.state.current = "archive_25_006"
	game._scene()
	check(game.stage_companions[0].visible and game.stage_companions[1].visible, "Three native sprites must appear together")
	for portrait in [game.actor, game.stage_companions[0], game.stage_companions[1]]:
		check(portrait.sprite.texture != null, "Every ensemble member must load native artwork")
		check(portrait.position.y - portrait.display_height / 2.0 - 12.0 > 112.0, "Ensemble portraits must clear navigation")
		check(portrait.position.y + portrait.display_height / 2.0 + 12.0 < 580.0, "Ensemble portraits must clear dialogue")
	game.state.current = "archive_25_rejoin"
	game._scene()
	check(game.atmosphere.layers == ["petals", "mist"], "Authored atmosphere layers must render together")
	game._attributes()
	var clock: float = game.atmosphere.clock
	game.atmosphere._process(1.0)
	check(game.atmosphere.clock == clock, "Panels must pause every atmosphere layer")
	game._close_popup()
	game._motion_changed(true)
	for portrait in game.stage_companions:
		check(portrait.reduced_motion and portrait.sprite.position.is_zero_approx(), "Reduced motion must stop all companions")
	check(not game.atmosphere.enabled, "Reduced motion must suppress every background layer")
	game.state.current = "forest_24_005"
	game.state.stats = {"qi": 0, "trust": 0, "insight": 0, "resolve": 0}
	game._scene()
	game.dialogue.visible_characters = -1
	var key_event := InputEventKey.new()
	key_event.keycode = KEY_5
	key_event.pressed = true
	game._unhandled_key_input(key_event)
	check(game.state.current == "forest_24_role_help", "The ungated fifth role must be keyboard-accessible")
	game.state.current = "first_choice"
	game._scene()
	var selected_scene: String = game.state.current
	var selected_stats: Dictionary = game.state.stats.duplicate()
	check(game._set_outfit("shen_qing", "festival"), "Companion outfits must be selectable")
	var companion_updated := false
	for portrait in [game.actor, game.stage_companions[0], game.stage_companions[1]]:
		if portrait.visible and portrait.character == "shen_qing":
			companion_updated = portrait.outfit == "festival"
	check(companion_updated and game.state.current == selected_scene and game.state.stats == selected_stats, "Companion clothing must update immediately without changing the journey")
	game._set_outfit("shen_qing", "sect")
	game._title()
	check(not game.stage_companions[0].visible and not game.stage_companions[1].visible, "Title must clear prior scene companions")
	game.audio.music.stop()
	game.audio.voice.stop()
	game.audio.effects.stop()
	root.remove_child(game)
	game.free()
	for path in ["user://continuation_test.json", "user://continuation_test.json.bak", "user://continuation_bad.json"]:
		if FileAccess.file_exists(path):
			DirAccess.remove_absolute(path)
	if failures.is_empty():
		print("JADE_VOW_CONTINUATION_TESTS_OK")
	quit(0 if failures.is_empty() else 1)
