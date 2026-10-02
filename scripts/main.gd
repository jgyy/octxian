extends Control

const StoryState = preload("res://scripts/story_state.gd")
const Character = preload("res://scripts/animated_character.gd")
const AudioDirector = preload("res://scripts/audio_director.gd")
const Atmosphere = preload("res://scripts/atmosphere.gd")
const GOLD := Color("#ccb887")
const JADE := Color("#a9ccbd")
const INK := Color("#10252a")
const PALE := Color("#e5e7da")

var state = StoryState.new()
var ui := Control.new()
var actor = Character.new()
var audio = AudioDirector.new()
var atmosphere = Atmosphere.new()
var dialogue: RichTextLabel
var choice_box: VBoxContainer
var continue_button: Button
var popup: PanelContainer
var is_reading := false
var auto_read := false
var fast_read := false
var reduced_motion := false
var text_speed := 38.0
var text_clock := 0.0
var auto_clock := 0.0
var status_label: Label

func _ready() -> void:
	_build_theme()
	var background := TextureRect.new()
	background.texture = load("res://assets/art/azure_cloud.png")
	background.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	background.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	background.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(background)
	var gradient := Gradient.new()
	gradient.set_color(0, Color(0.015, 0.06, 0.07, 0.88))
	gradient.set_color(1, Color(0.015, 0.06, 0.07, 0.12))
	var gradient_texture := GradientTexture2D.new()
	gradient_texture.gradient = gradient
	gradient_texture.width = 1600
	gradient_texture.height = 900
	var shade := TextureRect.new()
	shade.texture = gradient_texture
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(shade)
	add_child(actor)
	actor.position = Vector2(1175, 485)
	actor.show_character("lin_yue")
	atmosphere.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(atmosphere)
	add_child(audio)
	ui.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(ui)
	_load_settings()
	_title()
	if OS.get_cmdline_user_args().has("--capture"):
		call_deferred("_capture")

func _build_theme() -> void:
	var font := SystemFont.new()
	font.font_names = PackedStringArray(["DejaVu Sans", "Noto Sans", "Arial"])
	var game_theme := Theme.new()
	game_theme.default_font = font
	game_theme.default_font_size = 21
	game_theme.set_color("font_color", "Label", PALE)
	game_theme.set_color("default_color", "RichTextLabel", PALE)
	for kind in ["normal", "hover", "pressed", "focus", "disabled"]:
		var style := StyleBoxFlat.new()
		style.bg_color = Color(0.07, 0.17, 0.18, 0.85)
		style.border_color = GOLD if kind in ["hover", "focus"] else Color(0.66, 0.77, 0.69, 0.25)
		style.set_border_width_all(1)
		style.set_corner_radius_all(4)
		style.content_margin_left = 20
		style.content_margin_right = 20
		style.content_margin_top = 12
		style.content_margin_bottom = 12
		game_theme.set_stylebox(kind, "Button", style)
	game_theme.set_color("font_color", "Button", PALE)
	game_theme.set_color("font_hover_color", "Button", GOLD)
	game_theme.set_color("font_disabled_color", "Button", Color("#7d8b88"))
	theme = game_theme

func _clear() -> void:
	for child in ui.get_children():
		ui.remove_child(child)
		child.queue_free()
	popup = null
	dialogue = null
	choice_box = null
	continue_button = null
	status_label = null

func _label(text: String, point: Vector2, font_size: int = 22, color: Color = PALE, parent: Node = null) -> Label:
	if parent == null:
		parent = ui
	var label := Label.new()
	label.text = text
	label.position = point
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", color)
	parent.add_child(label)
	return label

func _serif(label: Label) -> void:
	var font := SystemFont.new()
	font.font_names = PackedStringArray(["DejaVu Serif", "Noto Serif", "Georgia"])
	label.add_theme_font_override("font", font)

func _button(text: String, point: Vector2, width: float, action: Callable, parent: Node = null) -> Button:
	if parent == null:
		parent = ui
	var button := Button.new()
	button.text = text
	button.position = point
	button.custom_minimum_size = Vector2(width, 48)
	button.size = Vector2(width, 48)
	button.pressed.connect(action)
	parent.add_child(button)
	return button

func _line(point: Vector2, width: float, color: Color = GOLD, parent: Node = null) -> void:
	if parent == null:
		parent = ui
	var line := ColorRect.new()
	line.color = color
	line.position = point
	line.size = Vector2(width, 1)
	line.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(line)

func _header() -> void:
	_label("◈  JADE VOW", Vector2(72, 35), 22, GOLD)
	_label("AN ORIGINAL XIANXIA TALE", Vector2(75, 70), 10, JADE)
	_button("The cast", Vector2(1050, 36), 135, _cast)
	_button("Journal", Vector2(1200, 36), 130, _journal)
	_button("Settings", Vector2(1345, 36), 150, _settings)
	_line(Vector2(72, 112), 1424, Color(0.8, 0.75, 0.6, 0.25))

func _title() -> void:
	is_reading = false
	audio.voice.stop()
	_clear()
	_header()
	actor.position = Vector2(1190, 518)
	actor.show_character("lin_yue", "idle")
	_label("BOOK I   /   THE STAR BENEATH THE MOUNTAIN", Vector2(95, 222), 14, GOLD)
	_line(Vector2(95, 267), 86)
	var title := _label("Jade Vow", Vector2(89, 290), 112)
	_serif(title)
	_label("A thousand paths.\nOne promise.", Vector2(97, 448), 36, JADE)
	_label("Ascend the mist. Uncover a forgotten covenant.\nChoose what you will carry into the heavens.", Vector2(99, 563), 22)
	_button("Begin your journey   →", Vector2(98, 661), 327, _begin)
	var resume := _button("Continue", Vector2(441, 661), 166, _resume)
	resume.disabled = not FileAccess.file_exists("user://jade_vow_save.json")
	_label("36 story scenes  ·  3 endings  ·  A living, animated cast", Vector2(100, 738), 15, JADE)
	_line(Vector2(72, 822), 1424, Color(0.8, 0.75, 0.6, 0.25))
	_label("AZURE CLOUD SECT", Vector2(74, 842), 12, GOLD)
	_label("Chapter one • The arrival", Vector2(660, 842), 12, JADE)
	_label("Press Enter to begin", Vector2(1300, 842), 12, JADE)

func _begin() -> void:
	state = StoryState.new()
	auto_read = false
	fast_read = false
	is_reading = true
	_scene()

func _resume() -> void:
	if state.load_game():
		is_reading = true
		_scene()
	else:
		_toast("The save could not be loaded. Your current journey is safe.")

func _scene() -> void:
	_clear()
	_header()
	actor.position = Vector2(1205, 419)
	var node: Dictionary = state.node()
	actor.show_character(str(node.get("actor", "lin_yue")), str(node.get("animation", "idle")))
	actor.sprite.speed_scale = 0.0 if reduced_motion else 1.0
	_label("CHAPTER ONE", Vector2(77, 146), 13, GOLD)
	_label("The star beneath the mountain", Vector2(77, 174), 27, PALE)
	_label("QI %02d    TRUST %02d    INSIGHT %02d    RESOLVE %02d" % [state.stats.qi, state.stats.trust, state.stats.insight, state.stats.resolve], Vector2(78, 222), 14, JADE)
	if node.has("ending"):
		_label("ENDING DISCOVERED", Vector2(80, 315), 13, GOLD)
		var ending_label := _label(str(node.ending), Vector2(78, 343), 36)
		_serif(ending_label)
	var panel := Panel.new()
	panel.position = Vector2(65, 580)
	panel.size = Vector2(1470, 250)
	var panel_style := StyleBoxFlat.new()
	panel_style.bg_color = Color(0.022, 0.065, 0.073, 0.95)
	panel_style.border_color = Color(0.65, 0.72, 0.62, 0.6)
	panel_style.set_border_width_all(1)
	panel_style.set_corner_radius_all(5)
	panel.add_theme_stylebox_override("panel", panel_style)
	ui.add_child(panel)
	var speaker_id := str(node.get("speaker", "narrator"))
	var character: Dictionary = state.story.characters[speaker_id]
	_label(str(character.name), Vector2(104, 599), 24, Color(character.color))
	_label(str(character.title), Vector2(280, 607), 13, JADE)
	_line(Vector2(104, 638), 1388, Color(0.65, 0.72, 0.62, 0.2))
	dialogue = RichTextLabel.new()
	dialogue.position = Vector2(104, 657)
	dialogue.size = Vector2(1260, 128)
	dialogue.add_theme_font_size_override("normal_font_size", 25)
	dialogue.text = str(node.get("text", ""))
	dialogue.visible_characters = 0
	dialogue.scroll_active = false
	ui.add_child(dialogue)
	text_clock = 0.0
	auto_clock = 0.0
	choice_box = VBoxContainer.new()
	choice_box.position = Vector2(78, 290)
	choice_box.size = Vector2(850, 265)
	choice_box.add_theme_constant_override("separation", 9)
	ui.add_child(choice_box)
	choice_box.visible = false
	var choices: Array = node.get("choices", [])
	for i in range(choices.size()):
		var choice: Dictionary = choices[i]
		var button := Button.new()
		button.text = "%d  %s" % [i + 1, choice.text]
		button.alignment = HORIZONTAL_ALIGNMENT_LEFT
		button.custom_minimum_size = Vector2(850, 52)
		button.disabled = not state.can_choose(choice)
		if choice.has("requires"):
			var parts: PackedStringArray = []
			for key in choice.requires:
				parts.append("%s %d" % [str(key).to_upper(), choice.requires[key]])
			button.tooltip_text = "Requires " + ", ".join(parts)
		button.pressed.connect(_choose.bind(i))
		choice_box.add_child(button)
	continue_button = _button("→", Vector2(1397, 719), 78, _advance)
	continue_button.visible = choices.is_empty()
	_button("Save", Vector2(74, 844), 95, _save)
	_button("Load", Vector2(181, 844), 95, _resume)
	_button("Log", Vector2(288, 844), 95, _journal)
	_button("Auto: " + ("on" if auto_read else "off"), Vector2(933, 844), 132, _toggle_auto)
	_button("Fast: " + ("on" if fast_read else "off"), Vector2(1080, 844), 132, _toggle_fast)
	_button("Menu", Vector2(1227, 844), 110, _title)
	_button("Voice: " + ("on" if audio.enabled else "off"), Vector2(1352, 844), 170, _toggle_voice)
	status_label = _label("", Vector2(406, 857), 13, GOLD)
	audio.speak(state.current)
	if node.has("sfx"):
		audio.effect(str(node.sfx))

func _choose(index: int) -> void:
	if popup != null:
		return
	if dialogue != null and dialogue.visible_characters >= 0 and dialogue.visible_characters < dialogue.get_total_character_count():
		return
	if state.choose(index):
		audio.effect()
		_scene()

func _advance() -> void:
	if popup != null:
		return
	if dialogue != null and dialogue.visible_characters >= 0 and dialogue.visible_characters < dialogue.get_total_character_count():
		dialogue.visible_characters = -1
		text_clock = dialogue.get_total_character_count()
		choice_box.visible = true
		return
	if state.node().has("ending"):
		_title()
	elif state.advance():
		audio.effect()
		_scene()

func _save() -> void:
	_toast("Journey saved." if state.save_game() else "Could not write the save file.")

func _toast(message: String) -> void:
	if status_label != null:
		status_label.text = message

func _toggle_auto() -> void:
	auto_read = not auto_read
	_refresh_controls()

func _toggle_fast() -> void:
	fast_read = not fast_read
	_refresh_controls()

func _toggle_voice() -> void:
	audio.enabled = not audio.enabled
	if not audio.enabled:
		audio.voice.stop()
	_save_settings()
	_refresh_controls()

func _refresh_controls() -> void:
	for child in ui.get_children():
		if child is Button:
			if child.text.begins_with("Auto:"):
				child.text = "Auto: " + ("on" if auto_read else "off")
			elif child.text.begins_with("Fast:"):
				child.text = "Fast: " + ("on" if fast_read else "off")
			elif child.text.begins_with("Voice:"):
				child.text = "Voice: " + ("on" if audio.enabled else "off")

func _process(delta: float) -> void:
	if not is_reading or dialogue == null or popup != null:
		return
	var total := dialogue.get_total_character_count()
	if dialogue.visible_characters >= 0 and dialogue.visible_characters < total:
		text_clock += delta * text_speed * (8.0 if fast_read else 1.0)
		dialogue.visible_characters = mini(int(text_clock), total)
	else:
		choice_box.visible = true
		auto_clock += delta
		if auto_read and auto_clock > 2.0 and not audio.voice.playing and state.node().has("next"):
			_advance()

func _unhandled_key_input(event: InputEvent) -> void:
	if not event is InputEventKey or not event.pressed or event.echo:
		return
	if event.keycode == KEY_ESCAPE:
		if popup != null:
			_close_popup()
		elif is_reading:
			_settings()
		return
	if popup != null:
		return
	if event.keycode in [KEY_ENTER, KEY_SPACE]:
		if is_reading:
			_advance()
		else:
			_begin()
	if is_reading:
		if event.keycode == KEY_S:
			_save()
		elif event.keycode == KEY_L:
			_journal()
		elif event.keycode >= KEY_1 and event.keycode <= KEY_4:
			_choose(event.keycode - KEY_1)

func _make_popup(title: String) -> VBoxContainer:
	_close_popup()
	popup = PanelContainer.new()
	popup.position = Vector2(270, 150)
	popup.size = Vector2(1060, 640)
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.035, 0.09, 0.10, 0.99)
	style.border_color = GOLD
	style.set_border_width_all(1)
	style.set_content_margin_all(28)
	popup.add_theme_stylebox_override("panel", style)
	ui.add_child(popup)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 20)
	popup.add_child(column)
	var row := HBoxContainer.new()
	column.add_child(row)
	var label := Label.new()
	label.text = title
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	label.add_theme_font_size_override("font_size", 31)
	_serif(label)
	row.add_child(label)
	var close := Button.new()
	close.text = "Close  ×"
	close.pressed.connect(_close_popup)
	row.add_child(close)
	return column

func _close_popup() -> void:
	if popup != null:
		ui.remove_child(popup)
		popup.queue_free()
		popup = null

func _journal() -> void:
	var column := _make_popup("The traveler's journal")
	var log := RichTextLabel.new()
	log.bbcode_enabled = true
	log.custom_minimum_size = Vector2(960, 490)
	log.size_flags_vertical = Control.SIZE_EXPAND_FILL
	log.add_theme_font_size_override("normal_font_size", 20)
	if state.history.is_empty():
		log.text = "Your journey begins at Azure Cloud.\n\nDialogue and discoveries will be recorded here."
	else:
		for entry in state.history:
			var name_text: String = state.story.characters[entry.speaker].name
			log.append_text("[color=#ccb887]%s[/color]\n%s\n\n" % [name_text, entry.text])
	column.add_child(log)

func _cast() -> void:
	var column := _make_popup("Those who share your path")
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 28)
	column.add_child(row)
	for id in ["lin_yue", "shen_qing", "elder_yun", "mo_ran"]:
		var card := VBoxContainer.new()
		card.custom_minimum_size = Vector2(226, 475)
		row.add_child(card)
		var portrait := TextureRect.new()
		var atlas: Texture2D = load("res://assets/art/cast.png")
		var cropped := AtlasTexture.new()
		var index := ["lin_yue", "shen_qing", "elder_yun", "mo_ran"].find(id)
		cropped.atlas = atlas
		cropped.region = Rect2(index * atlas.get_width() / 4.0, 0, atlas.get_width() / 4.0, atlas.get_height())
		portrait.texture = cropped
		portrait.custom_minimum_size = Vector2(210, 360)
		portrait.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		portrait.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		card.add_child(portrait)
		var name_label := Label.new()
		name_label.text = str(state.story.characters[id].name)
		name_label.add_theme_color_override("font_color", GOLD)
		card.add_child(name_label)
		var detail := Label.new()
		detail.text = str(state.story.characters[id].title)
		detail.add_theme_font_size_override("font_size", 14)
		card.add_child(detail)

func _settings() -> void:
	var column := _make_popup("A quieter journey")
	for bus in ["Music", "SFX", "Voice"]:
		var row := HBoxContainer.new()
		column.add_child(row)
		var label := Label.new()
		label.text = bus + " volume"
		label.custom_minimum_size.x = 235
		row.add_child(label)
		var slider := HSlider.new()
		slider.min_value = -40
		slider.max_value = 0
		slider.step = 1
		slider.value = AudioServer.get_bus_volume_db(AudioServer.get_bus_index(bus))
		slider.custom_minimum_size = Vector2(650, 45)
		slider.value_changed.connect(_volume_changed.bind(bus))
		row.add_child(slider)
	var speed := HSlider.new()
	speed.min_value = 12
	speed.max_value = 100
	speed.value = text_speed
	speed.custom_minimum_size.y = 40
	speed.value_changed.connect(_speed_changed)
	var caption := Label.new()
	caption.text = "Reading speed"
	column.add_child(caption)
	column.add_child(speed)
	var motion := CheckButton.new()
	motion.text = "Reduce motion"
	motion.button_pressed = reduced_motion
	motion.toggled.connect(_motion_changed)
	column.add_child(motion)
	var voice_toggle := CheckButton.new()
	voice_toggle.text = "Neural voice narration"
	voice_toggle.button_pressed = audio.enabled
	voice_toggle.toggled.connect(_voice_changed)
	column.add_child(voice_toggle)
	var help := Label.new()
	help.text = "Enter / Space: advance    1–4: choose    S: save    L: journal    Esc: close\nNarration uses the open Piper Lessac neural voice."
	help.add_theme_font_size_override("font_size", 17)
	column.add_child(help)

func _volume_changed(value: float, bus: String) -> void:
	AudioServer.set_bus_volume_db(AudioServer.get_bus_index(bus), value)
	_save_settings()

func _speed_changed(value: float) -> void:
	text_speed = value
	_save_settings()

func _motion_changed(value: bool) -> void:
	reduced_motion = value
	atmosphere.enabled = not value
	actor.sprite.speed_scale = 0.0 if value else 1.0
	_save_settings()

func _voice_changed(value: bool) -> void:
	audio.enabled = value
	if not value:
		audio.voice.stop()
	_save_settings()
	_refresh_controls()

func _save_settings() -> void:
	var config := ConfigFile.new()
	config.set_value("reading", "speed", text_speed)
	config.set_value("reading", "motion", reduced_motion)
	config.set_value("reading", "voice", audio.enabled)
	for bus in ["Music", "SFX", "Voice"]:
		config.set_value("audio", bus, AudioServer.get_bus_volume_db(AudioServer.get_bus_index(bus)))
	config.save("user://settings.cfg")

func _load_settings() -> void:
	var config := ConfigFile.new()
	if config.load("user://settings.cfg") != OK:
		return
	text_speed = clampf(float(config.get_value("reading", "speed", 38.0)), 12.0, 100.0)
	reduced_motion = bool(config.get_value("reading", "motion", false))
	atmosphere.enabled = not reduced_motion
	actor.sprite.speed_scale = 0.0 if reduced_motion else 1.0
	audio.enabled = bool(config.get_value("reading", "voice", true))
	for bus in ["Music", "SFX", "Voice"]:
		AudioServer.set_bus_volume_db(AudioServer.get_bus_index(bus), clampf(float(config.get_value("audio", bus, -8.0)), -40.0, 0.0))

func _capture() -> void:
	DirAccess.make_dir_recursive_absolute("res://build/screenshots")
	await get_tree().create_timer(1.2).timeout
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("res://build/screenshots/title.png")
	_begin()
	state.current = "first_choice"
	_scene()
	dialogue.visible_characters = -1
	await get_tree().create_timer(1.2).timeout
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("res://build/screenshots/dialogue.png")
	_cast()
	await get_tree().create_timer(0.4).timeout
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("res://build/screenshots/cast.png")
	print("JADE_VOW_CAPTURE_OK")
	get_tree().quit()
