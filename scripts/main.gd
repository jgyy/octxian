extends Control

const StoryState = preload("res://scripts/story_state.gd")
const Attributes = preload("res://scripts/attributes.gd")
const Character = preload("res://scripts/animated_character.gd")
const Wardrobe = preload("res://scripts/wardrobe.gd")
const AudioDirector = preload("res://scripts/audio_director.gd")
const Atmosphere = preload("res://scripts/atmosphere.gd")
const GOLD := Color("#ccb887")
const JADE := Color("#a9ccbd")
const INK := Color("#10252a")
const PALE := Color("#e5e7da")

var state = StoryState.new()
var ui := Control.new()
var actor = Character.new()
var stage_companions: Array = []
var wardrobe = Wardrobe.new()
var wardrobe_previews := {}
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
var background := TextureRect.new()
var world: Dictionary = {}
var background_paths: Dictionary = {}
var cultivation_catalog: Dictionary = {}
var cultivation_entries: Array[Dictionary] = []
var world_previews: Dictionary = {}
var item_image: TextureRect
var item_description: RichTextLabel
var interior_image: TextureRect
var interior_description: RichTextLabel

func _ready() -> void:
	get_tree().auto_accept_quit = false
	_build_theme()
	var catalog = JSON.parse_string(FileAccess.get_file_as_string("res://data/world_assets.json"))
	if catalog is Dictionary:
		world = catalog
		for entry in world.get("backgrounds", []):
			background_paths[str(entry.id)] = "res://" + str(entry.path)
	var realm_data = JSON.parse_string(FileAccess.get_file_as_string("res://data/cultivation.json"))
	if realm_data is Dictionary:
		cultivation_catalog = realm_data
	background.texture = load("res://assets/art/azure_cloud.webp")
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
	for slot in range(2):
		var companion = Character.new()
		companion.visible = false
		add_child(companion)
		stage_companions.append(companion)
	atmosphere.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(atmosphere)
	add_child(audio)
	ui.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(ui)
	_load_settings()
	_title()
	if OS.get_cmdline_user_args().has("--capture"):
		call_deferred("_capture")
	elif OS.get_cmdline_user_args().has("--smoke-build"):
		call_deferred("_smoke_build")

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
	# Menu, Load and scene rebuilds can replace a modal without its Close button.
	atmosphere.paused = false
	for companion in stage_companions:
		companion.visible = false
	wardrobe_previews.clear()
	world_previews.clear()
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
	var attributes_button := _button("Attributes", Vector2(685, 36), 165, _attributes)
	attributes_button.name = "AttributesButton"
	attributes_button.tooltip_text = "Lin Yue's attributes · C"
	_button("World", Vector2(870, 36), 160, _world)
	_button("Wardrobe", Vector2(1050, 36), 135, _cast)
	_button("Journal", Vector2(1200, 36), 130, _journal)
	_button("Settings", Vector2(1345, 36), 150, _settings)
	_line(Vector2(72, 112), 1424, Color(0.8, 0.75, 0.6, 0.25))

func _title() -> void:
	is_reading = false
	atmosphere.set_effect("lanterns")
	background.texture = load("res://assets/art/world/lower_training_terrace.png")
	audio.voice.stop()
	_clear()
	_header()
	actor.display_height = 730.0
	actor.position = Vector2(1190, 518)
	actor.show_character("lin_yue", "idle", wardrobe.selected("lin_yue"))
	_label("BOOK I   /   THE FIRST RETAINED BREATH", Vector2(95, 222), 14, GOLD)
	_line(Vector2(95, 267), 86)
	var title := _label("Jade Vow", Vector2(89, 290), 112)
	_serif(title)
	_label("A mortal beginning.\nAn earned ascent.", Vector2(97, 448), 36, JADE)
	_label("Work. Fail. Recover. Learn to retain your first breath of qi.\nBuild the foundation of a path into the heavens.", Vector2(99, 563), 22)
	_button("Begin your journey   →", Vector2(98, 661), 327, _begin)
	var resume := _button("Continue", Vector2(441, 661), 166, _resume)
	resume.disabled = not StoryState.has_save()
	_label("%d story scenes  ·  %d books  ·  A living, animated cast" % [state.story.nodes.size(), state.story.get("chapters", {}).size()], Vector2(100, 738), 15, JADE)
	_line(Vector2(72, 822), 1424, Color(0.8, 0.75, 0.6, 0.25))
	_label("AZURE CLOUD SECT", Vector2(74, 842), 12, GOLD)
	_label("Chapter one • The mortal terrace", Vector2(660, 842), 12, JADE)
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
		if state.recovered_checkpoint:
			_toast("Recovered your previous checkpoint.")
	else:
		_toast("The save could not be loaded. Your current journey is safe.")

func _scene() -> void:
	_clear()
	_header()
	var node: Dictionary = state.node()
	atmosphere.set_effects(node.get("effects", [str(node.get("effect", "lanterns"))]))
	_stage_cast(node)
	var chapter: Dictionary = state.story.get("chapters", {}).get(node.get("chapter", "book_i"), {})
	_label(str(chapter.get("label", "BOOK I")), Vector2(77, 146), 13, GOLD)
	_label(str(chapter.get("title", "The star beneath the mountain")), Vector2(77, 174), 27, PALE)
	var background_path := str(background_paths.get(node.get("background", ""), "res://assets/art/azure_cloud.webp"))
	background.texture = load(background_path)
	var totals := _label("CONTROL %02d    DAO HEART %02d    COMPREHENSION %02d    PHYSIQUE %02d" % [state.stats.qi, state.stats.trust, state.stats.insight, state.stats.resolve], Vector2(78, 222), 14, JADE)
	totals.name = "AttributeTotals"
	var realm_label := _label(_cultivation_label(node), Vector2(78, 246), 13, GOLD)
	realm_label.name = "CultivationRealm"
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
	var speaker_label := _label(str(character.name), Vector2(104, 599), 24, Color(character.color))
	speaker_label.name = "SpeakerName"
	var title_x := maxf(280.0, speaker_label.position.x + speaker_label.get_minimum_size().x + 24.0)
	var character_title: String = str(character.title)
	if speaker_id == "lin_yue" and node.has("cultivation"):
		character_title = _cultivation_label(node)
	var speaker_title := _label(character_title, Vector2(title_x, 607), 13, JADE)
	speaker_title.name = "SpeakerTitle"
	_line(Vector2(104, 638), 1388, Color(0.65, 0.72, 0.62, 0.2))
	dialogue = RichTextLabel.new()
	dialogue.position = Vector2(104, 657)
	dialogue.size = Vector2(1260, 128)
	dialogue.add_theme_font_size_override("normal_font_size", 25)
	dialogue.text = str(node.get("text", ""))
	dialogue.visible_characters = 0
	dialogue.scroll_active = true
	ui.add_child(dialogue)
	text_clock = 0.0
	auto_clock = 0.0
	var choice_scroll := ScrollContainer.new()
	choice_scroll.name = "ChoiceScroll"
	choice_scroll.clip_contents = true
	choice_scroll.follow_focus = true
	choice_scroll.position = Vector2(78, 268)
	choice_scroll.size = Vector2(850, 288)
	choice_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	ui.add_child(choice_scroll)
	choice_box = VBoxContainer.new()
	choice_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	choice_box.custom_minimum_size = Vector2(826, 0)
	choice_box.add_theme_constant_override("separation", 6)
	choice_scroll.add_child(choice_box)
	choice_box.visible = false
	var choices: Array = [] if node.get("random_event", false) else node.get("choices", [])
	for i in range(choices.size()):
		var choice: Dictionary = choices[i]
		var details: Dictionary = state.choice_details(choice)
		var card := VBoxContainer.new()
		card.add_theme_constant_override("separation", 3)
		choice_box.add_child(card)
		var button := Button.new()
		button.name = "Choice_" + str(i)
		button.text = "%d  %s" % [i + 1, choice.text]
		button.alignment = HORIZONTAL_ALIGNMENT_LEFT
		button.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		button.add_theme_font_size_override("font_size", 18)
		button.custom_minimum_size = Vector2(826, 44)
		for kind in ["normal", "hover", "pressed", "focus", "disabled"]:
			var style: StyleBoxFlat = get_theme_stylebox(kind, "Button").duplicate()
			style.content_margin_top = 6
			style.content_margin_bottom = 6
			button.add_theme_stylebox_override(kind, style)
		button.disabled = not details.available
		var parts: PackedStringArray = []
		if not details.effects.is_empty():
			parts.append("Gains: " + ", ".join(details.effects))
		if not details.requirements.is_empty():
			parts.append(("Requires: " if details.available else "Locked: ") + ", ".join(details.requirements))
		if not details.available and details.missing.is_empty():
			parts.append(details.reason)
		button.tooltip_text = " · ".join(parts)
		button.pressed.connect(_choose.bind(i))
		card.add_child(button)
		if not parts.is_empty():
			var summary := Label.new()
			summary.name = "ChoiceDetails_" + str(i)
			summary.text = " · ".join(parts)
			summary.add_theme_font_size_override("font_size", 14)
			summary.add_theme_color_override("font_color", JADE if details.available else GOLD)
			card.add_child(summary)
	if choices.size() > 4:
		var scroll_hint := _label("Scroll for all %d choices · keys 1–%d select" % [choices.size(), mini(choices.size(), 9)], Vector2(78, 557), 13, GOLD)
		scroll_hint.name = "ChoiceScrollHint"
	continue_button = _button("→", Vector2(1397, 719), 78, _advance)
	continue_button.visible = choices.is_empty()
	if node.has("continuation"):
		continue_button.text = "→"
		continue_button.tooltip_text = "Continue to the next book"
	_button("Save", Vector2(74, 844), 95, _save)
	_button("Load", Vector2(181, 844), 95, _resume)
	_button("Log", Vector2(288, 844), 95, _journal)
	_button("Auto: " + ("on" if auto_read else "off"), Vector2(933, 844), 132, _toggle_auto)
	_button("Fast: " + ("on" if fast_read else "off"), Vector2(1080, 844), 132, _toggle_fast)
	_button("Menu", Vector2(1227, 844), 110, _title)
	_button("Voice: " + ("on" if audio.enabled else "off"), Vector2(1352, 844), 170, _toggle_voice)
	status_label = _label("", Vector2(406, 857), 13, GOLD)
	if node.has("earned") and not state.completed_practice.has(state.current):
		var credit: Dictionary = state.choice_details({"next": str(node.get("next", node.get("continuation", state.current))), "effects": node.earned})
		_label("Completed practice · " + ", ".join(credit.effects) + " on Continue", Vector2(78, 540), 14, JADE)
	audio.speak(state.current)
	if node.has("sfx"):
		audio.effect(str(node.sfx))

# Up to three intact native portraits fit to the right of the choice cards.
func _stage_cast(node: Dictionary) -> void:
	var ids: Array[String] = [str(node.get("actor", "lin_yue"))]
	for id in node.get("cast", []):
		if not ids.has(str(id)) and ids.size() < 3:
			ids.append(str(id))
	var portraits: Array = [actor]
	portraits.append_array(stage_companions)
	var positions: Array = [Vector2(1205, 474)] if ids.size() == 1 else ([Vector2(1110, 356), Vector2(1390, 366)] if ids.size() == 2 else [Vector2(1060, 354), Vector2(1250, 356), Vector2(1440, 367)])
	for slot in range(portraits.size()):
		var portrait = portraits[slot]
		portrait.visible = slot < ids.size()
		if not portrait.visible:
			continue
		portrait.display_height = 680.0 if ids.size() == 1 else (420.0 if slot == 0 else 390.0)
		portrait.position = positions[slot]
		portrait.show_character(ids[slot], str(node.get("animation", "idle")), wardrobe.selected(ids[slot]))
		portrait.set_reduced_motion(reduced_motion)
		var speaking := ids[slot] == str(node.get("speaker", "narrator"))
		var brightness := 1.0 if speaking or slot == 0 else 0.78
		portrait.modulate = Color(brightness, brightness, brightness, portrait.modulate.a)

func _choose(index: int) -> void:
	if popup != null:
		return
	if dialogue != null and dialogue.visible_characters >= 0 and dialogue.visible_characters < dialogue.get_total_character_count():
		return
	var choices: Array = state.node().get("choices", [])
	var gains: PackedStringArray = []
	if state.node().get("random_event", false):
		return
	if index >= 0 and index < choices.size():
		gains = state.choice_details(choices[index]).effects
	if state.choose(index):
		audio.effect()
		_scene()
		if not gains.is_empty():
			_toast(" · ".join(gains))

func _advance() -> void:
	if popup != null:
		return
	if dialogue != null and dialogue.visible_characters >= 0 and dialogue.visible_characters < dialogue.get_total_character_count():
		dialogue.visible_characters = -1
		text_clock = dialogue.get_total_character_count()
		choice_box.visible = choice_box.get_child_count() > 0
		return
	var credit_scene: String = state.current
	var pending_credit: bool = state.node().has("earned") and not state.completed_practice.has(credit_scene)
	var gains: PackedStringArray = []
	if pending_credit:
		var target: String = str(state.node().get("next", state.node().get("continuation", "")))
		gains = state.choice_details({"next": target, "effects": state.node().earned}).effects
	if state.node().has("ending"):
		if state.node().has("continuation") and state.advance():
			_scene()
		else:
			_title()
	elif state.advance():
		audio.effect()
		_scene()
	if pending_credit and state.current != credit_scene and state.completed_practice.has(credit_scene) and not gains.is_empty():
		_toast("Completed practice · " + " · ".join(gains))

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
		choice_box.visible = choice_box.get_child_count() > 0
		auto_clock += delta
		if auto_read and auto_clock > 2.0 and not audio.voice.playing and (state.node().has("next") or state.node().get("random_event", false)):
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
	if event.keycode == KEY_C:
		_attributes()
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
		elif event.keycode >= KEY_1 and event.keycode <= KEY_9:
			_choose(event.keycode - KEY_1)

func _make_popup(title: String) -> VBoxContainer:
	_close_popup()
	atmosphere.paused = true
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
	atmosphere.paused = false
	world_previews.clear()
	wardrobe_previews.clear()
	if popup != null:
		ui.remove_child(popup)
		popup.queue_free()
		popup = null


func _cultivation_label(node: Dictionary) -> String:
	var progress: Dictionary = node.get("cultivation", {})
	if progress.is_empty():
		return ""
	for entry in cultivation_catalog.get("realms", []):
		if str(entry.id) == str(progress.get("realm", "")):
			return "%s · %s" % [entry.name, progress.get("stage", "")]
	return ""

func _cultivation() -> void:
	var column := _make_popup("The gates of cultivation")
	popup.name = "CultivationPanel"
	popup.position = Vector2(210, 95)
	popup.size = Vector2(1180, 700)
	column.add_theme_constant_override("separation", 12)
	var hint := Label.new()
	hint.text = "Realms require practice, demonstrated control and recovery. Attribute points do not grant a realm."
	hint.add_theme_font_size_override("font_size", 16)
	column.add_child(hint)
	cultivation_entries.clear()
	var fundamentals: String = "RESERVE, CONTROL AND RECOVERY\n\n"
	for key in cultivation_catalog.get("measures", {}):
		fundamentals += "%s\n%s\n\n" % [str(key).capitalize(), cultivation_catalog.measures[key]]
	fundamentals += "THE PRACTICE CYCLE\n\n"
	for step in cultivation_catalog.get("cycle", []):
		fundamentals += "%d. %s\n%s\n\n" % [step.step, step.name, step.rule]
	cultivation_entries.append({"name": "Practice and measurement", "text": fundamentals})
	for entry in cultivation_catalog.get("realms", []):
		var content: String = "%s\n\nSTAGES\n%s\n\n" % [entry.name, " → ".join(PackedStringArray(entry.stages))]
		for field in ["mechanism", "admission", "practice", "breakthrough", "capabilities", "limits", "failure", "recovery", "span"]:
			content += "%s\n%s\n\n" % [str(field).capitalize(), entry.get(field, "")]
		cultivation_entries.append({"name": entry.name, "text": content})
	var anatomy: String = "CHANNELS AND RESERVOIRS\n\n"
	for entry in cultivation_catalog.get("anatomy", []):
		anatomy += "%s\n%s\nFailure: %s\n\n" % [entry.name, entry.function, entry.failure]
	cultivation_entries.append({"name": "Meridians and dantian", "text": anatomy})
	var techniques: String = "TECHNIQUES\n\n"
	for entry in cultivation_catalog.get("techniques", []):
		techniques += "%s · %s\n%s\nCost: %s\nFailure: %s\nGrowth: %s\n\n" % [entry.name, entry.minimum, entry.steps, entry.cost, entry.failure, entry.growth]
	cultivation_entries.append({"name": "Techniques", "text": techniques})
	var crafts: String = "CRAFTS AND RESOURCES\n\n"
	for entry in cultivation_catalog.get("crafts", []):
		crafts += "%s\n%s\nStarting work: %s\n\n" % [entry.name, entry.rule, entry.opening_use]
	for entry in cultivation_catalog.get("resources", []):
		crafts += "%s\n%s\nLimit: %s\n\n" % [entry.name, entry.use, entry.limit]
	cultivation_entries.append({"name": "Crafts and resources", "text": crafts})
	var selector := OptionButton.new()
	selector.name = "CultivationSelector"
	selector.custom_minimum_size.y = 44
	for entry in cultivation_entries:
		selector.add_item(str(entry.name))
	column.add_child(selector)
	var detail := RichTextLabel.new()
	detail.name = "CultivationDetail"
	detail.custom_minimum_size = Vector2(1100, 480)
	detail.size_flags_vertical = Control.SIZE_EXPAND_FILL
	detail.scroll_active = true
	detail.add_theme_font_size_override("normal_font_size", 20)
	column.add_child(detail)
	selector.item_selected.connect(_cultivation_selected)
	_cultivation_selected(0)

func _cultivation_selected(index: int) -> void:
	if index < 0 or index >= cultivation_entries.size() or popup == null:
		return
	var selector: OptionButton = popup.find_child("CultivationSelector", true, false)
	var detail: RichTextLabel = popup.find_child("CultivationDetail", true, false)
	if selector == null or detail == null:
		return
	selector.select(index)
	detail.text = str(cultivation_entries[index].text)
	detail.scroll_to_line(0)

func _attributes() -> void:
	var column := _make_popup("Lin Yue · Attributes")
	popup.name = "AttributePanel"
	var codex_button := Button.new()
	codex_button.name = "CultivationButton"
	codex_button.text = "Cultivation realms →"
	codex_button.pressed.connect(_cultivation)
	column.get_child(0).add_child(codex_button)
	column.add_theme_constant_override("separation", 12)
	var hint := Label.new()
	hint.text = "Practice earns attributes after completion. Your training changes which roles you can lead."
	hint.add_theme_font_size_override("font_size", 16)
	hint.add_theme_color_override("font_color", JADE)
	column.add_child(hint)
	var grid := GridContainer.new()
	grid.columns = 2
	grid.size_flags_vertical = Control.SIZE_EXPAND_FILL
	grid.add_theme_constant_override("h_separation", 16)
	grid.add_theme_constant_override("v_separation", 16)
	column.add_child(grid)
	for key in Attributes.KEYS:
		var profile: Dictionary = Attributes.profile(key, int(state.stats[key]))
		var card := PanelContainer.new()
		card.custom_minimum_size = Vector2(490, 210)
		card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var style := StyleBoxFlat.new()
		style.bg_color = Color(0.07, 0.17, 0.18, 0.85)
		style.border_color = Color(0.66, 0.77, 0.69, 0.25)
		style.set_border_width_all(1)
		style.set_content_margin_all(16)
		card.add_theme_stylebox_override("panel", style)
		grid.add_child(card)
		var content := VBoxContainer.new()
		content.add_theme_constant_override("separation", 8)
		card.add_child(content)
		var value_label := Label.new()
		value_label.name = "AttributeValue_" + key
		value_label.text = "%s · %d" % [profile.name, profile.value]
		value_label.add_theme_font_size_override("font_size", 25)
		value_label.add_theme_color_override("font_color", GOLD)
		content.add_child(value_label)
		var rank := Label.new()
		rank.name = "AttributeRank_" + key
		rank.text = "%s · %d %s to next rank" % [profile.rank, profile.remaining, "point" if profile.remaining == 1 else "points"] if profile.next_minimum >= 0 else "%s · Highest rank; points keep growing" % profile.rank
		rank.add_theme_font_size_override("font_size", 15)
		rank.add_theme_color_override("font_color", JADE)
		content.add_child(rank)
		var progress := ProgressBar.new()
		progress.name = "AttributeProgress_" + key
		progress.custom_minimum_size.y = 8
		progress.max_value = 1.0
		progress.step = 0.0
		progress.value = profile.progress
		progress.show_percentage = false
		content.add_child(progress)
		for text in [profile.description, profile.growth]:
			var description := Label.new()
			description.text = str(text)
			description.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			description.custom_minimum_size.x = 458
			description.add_theme_font_size_override("font_size", 16)
			content.add_child(description)
	var footer := Label.new()
	footer.text = "Attributes travel with you across books and are saved with your journey.   C: open · Esc: close"
	footer.add_theme_font_size_override("font_size", 16)
	column.add_child(footer)

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
			log.push_color(GOLD)
			log.add_text(name_text + "\n")
			log.pop()
			log.add_text(str(entry.text) + "\n\n")
	column.add_child(log)

func _cast() -> void:
	var column := _make_popup("Cast & wardrobe")
	popup.position = Vector2(210, 135)
	popup.size = Vector2(1180, 665)
	var hint := Label.new()
	hint.text = "Choose an outfit for each companion. Your choices follow you into the story."
	hint.add_theme_font_size_override("font_size", 16)
	hint.add_theme_color_override("font_color", JADE)
	column.add_child(hint)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 24)
	column.add_child(row)
	for id in Wardrobe.CHARACTERS:
		var card := VBoxContainer.new()
		card.custom_minimum_size = Vector2(256, 455)
		row.add_child(card)
		var portrait_space := Control.new()
		portrait_space.custom_minimum_size = Vector2(256, 350)
		card.add_child(portrait_space)
		var preview = Character.new()
		preview.display_height = 350.0
		preview.fade_in = false
		preview.position = Vector2(128, 175)
		portrait_space.add_child(preview)
		preview.show_character(id, "idle", wardrobe.selected(id))
		preview.set_reduced_motion(reduced_motion)
		wardrobe_previews[id] = preview
		var name_label := Label.new()
		name_label.text = str(state.story.characters[id].name)
		name_label.add_theme_color_override("font_color", GOLD)
		card.add_child(name_label)
		var detail := Label.new()
		detail.text = str(state.story.characters[id].title)
		detail.add_theme_font_size_override("font_size", 14)
		card.add_child(detail)
		var selector := OptionButton.new()
		selector.name = "Outfit_" + id
		selector.custom_minimum_size = Vector2(256, 48)
		selector.add_theme_font_size_override("font_size", 18)
		var options: Array = wardrobe.options()
		for index in range(options.size()):
			selector.add_item(str(options[index]["name"]))
			selector.set_item_metadata(index, str(options[index]["id"]))
			selector.get_popup().set_item_tooltip(index, str(options[index]["description"]))
			if options[index]["id"] == wardrobe.selected(id):
				selector.select(index)
		selector.item_selected.connect(_outfit_selected.bind(id))
		card.add_child(selector)

func _outfit_selected(index: int, character: String) -> void:
	var options: Array = wardrobe.options()
	if index < 0 or index >= options.size():
		return
	_set_outfit(character, str(options[index]["id"]))

func _set_outfit(character: String, outfit: String) -> bool:
	if not wardrobe.select(character, outfit):
		return false
	if wardrobe_previews.has(character):
		var preview = wardrobe_previews[character]
		preview.show_character(character, "idle", outfit)
		preview.set_reduced_motion(reduced_motion)
	if actor.character == character:
		actor.show_character(character, actor.motion, outfit)
		actor.set_reduced_motion(reduced_motion)
	for companion in stage_companions:
		if companion.visible and companion.character == character:
			companion.show_character(character, companion.motion, outfit)
			companion.set_reduced_motion(reduced_motion)
	_save_settings()
	return true

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
	help.text = "Enter / Space: advance    1–9: choose    S: save    L: journal    C: attributes    Esc: close\nNarration uses the open Piper Lessac neural voice."
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
	actor.set_reduced_motion(value)
	for companion in stage_companions:
		companion.set_reduced_motion(value)
	for preview in wardrobe_previews.values():
		preview.set_reduced_motion(value)
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
	config.set_value("wardrobe", "choices", wardrobe.selections)
	for bus in ["Music", "SFX", "Voice"]:
		config.set_value("audio", bus, AudioServer.get_bus_volume_db(AudioServer.get_bus_index(bus)))
	config.save("user://settings.cfg")

func _load_settings() -> void:
	var config := ConfigFile.new()
	if config.load("user://settings.cfg") != OK:
		return
	text_speed = _setting_number(config, "reading", "speed", 38.0, 12.0, 100.0)
	reduced_motion = _setting_bool(config, "reading", "motion", false)
	atmosphere.enabled = not reduced_motion
	actor.set_reduced_motion(reduced_motion)
	audio.enabled = _setting_bool(config, "reading", "voice", true)
	wardrobe.restore(config.get_value("wardrobe", "choices", {}))
	for bus in ["Music", "SFX", "Voice"]:
		AudioServer.set_bus_volume_db(AudioServer.get_bus_index(bus), _setting_number(config, "audio", bus, -8.0, -40.0, 0.0))

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
	_attributes()
	await get_tree().create_timer(0.4).timeout
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("res://build/screenshots/attributes.png")
	_close_popup()
	state.current = "final_choice"
	_scene()
	dialogue.visible_characters = -1
	await get_tree().create_timer(0.4).timeout
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("res://build/screenshots/attribute_choices.png")
	state.current = "first_choice"
	_scene()
	dialogue.visible_characters = -1
	_cast()
	await get_tree().create_timer(0.4).timeout
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("res://build/screenshots/cast.png")
	for outfit in ["training", "festival"]:
		for character in Wardrobe.CHARACTERS:
			_set_outfit(character, outfit)
		_cast()
		await get_tree().create_timer(0.8).timeout
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png("res://build/screenshots/wardrobe_%s.png" % outfit)
	_close_popup()
	state.current = "pendant"
	_scene()
	dialogue.visible_characters = -1
	await get_tree().create_timer(0.8).timeout
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("res://build/screenshots/outfit_dialogue.png")

	# Record real timed playback, with a quiet background so the actor's motion is clear.
	_set_outfit("lin_yue", Wardrobe.DEFAULT_OUTFIT)
	atmosphere.enabled = false
	actor.set_reduced_motion(false)
	await get_tree().create_timer(0.4).timeout
	actor.reset_motion()
	DirAccess.make_dir_recursive_absolute("res://build/animations/rendered")
	for index in range(16):
		await RenderingServer.frame_post_draw
		var snapshot := get_viewport().get_texture().get_image()
		snapshot.resize(960, 540, Image.INTERPOLATE_LANCZOS)
		snapshot.save_png("res://build/animations/rendered/frame_%02d.png" % index)
		await get_tree().create_timer(0.25).timeout

	for character in Wardrobe.CHARACTERS:
		_set_outfit(character, Wardrobe.DEFAULT_OUTFIT)

	atmosphere.enabled = not reduced_motion
	for sample in [{"id":"expansion_xu_lin_common_001","file":"xu_lin"}, {"id":"expansion_tidemirror_otter_common_001","file":"tidemirror_otter"}, {"id":"expansion_cinderback_pangolin_common_001","file":"cinderback_pangolin"}, {"id":"expansion_chen_rui_common_001","file":"chen_rui"}, {"id":"expansion_wu_zheng_common_001","file":"wu_zheng"}, {"id":"expansion_song_mei_common_001","file":"song_mei"}, {"id":"expansion_xu_lin_choice","file":"expanded_canal_choice"}, {"id":"forest_24_005","file":"forest_ensemble"}, {"id":"forest_24_close_1","file":"lanternwing_crane"}, {"id":"desert_p24_005","file":"desert_attributes"}, {"id":"archive_25_006","file":"archive_ensemble"}, {"id":"archive_25_rejoin","file":"archive_courtyard"}, {"id":"archive_25_lantern_keeper","file":"archive_lantern_keeper"}, {"id": "arrival", "file": "mortal_arrival"}, {"id": "han_mei_shift", "file": "mortal_han_mei"}, {"id": "mortal_mite_choice", "file": "mortal_mite"}, {"id": "tempering_after_013", "file": "first_trace"}, {"id": "sluice_005", "file": "sluice_examiner"}, {"id": "sluice_040", "file": "sluice_retention"}, {"id": "channels_044", "file": "paired_channel"}, {"id": "reed_step_011", "file": "brine_mantis"}, {"id": "lantern_hub", "file": "quest_hub"}, {"id": "reed_voice", "file": "spirit_encounter"}, {"id": "ferry_price", "file": "ferry_encounter"}, {"id": "archive_copies", "file": "archive_encounter"}, {"id": "river_xiu", "file": "river_pilot"}, {"id": "river_spirit", "file": "river_spirit"}, {"id": "harbor_answer", "file": "river_harbor"}, {"id": "orchard_arrival", "file": "orchard_healer"}, {"id": "orchard_hart_answer", "file": "orchard_spirit"}, {"id": "orchard_resolution_choice", "file": "orchard_choices"}, {"id": "city_arrival", "file": "city_market"}, {"id": "city_mask_studio", "file": "city_mask_maker"}, {"id": "city_registry_mei", "file": "city_archivist"}, {"id": "city_registry_tao", "file": "city_courier"}, {"id": "city_perfumer_workroom", "file": "city_perfumer"}, {"id": "city_courser_terms", "file": "city_courser"}, {"id": "city_perfumer_moth_terms", "file": "city_moth"}, {"id": "city_final_choice", "file": "city_choices"}, {"id": "court_upper_bench", "file": "court_upper_bench"}, {"id": "court_luo_shan", "file": "court_luo_shan"}, {"id": "court_bai_qun", "file": "court_bai_qun"}, {"id": "court_du_heng", "file": "court_du_heng"}, {"id": "court_rain_heron", "file": "court_rain_heron"}, {"id": "court_investigation_choice", "file": "court_investigation_choice"}, {"id": "court_final_choice", "file": "court_final_choice"}, {"id": "court_weather_setup", "file": "court_weather_setup"}, {"id":"foundry_arrival_003","file":"foundry_examiner"}, {"id":"foundry_arrival_014","file":"foundry_friend"}, {"id":"foundry_phase_001","file":"foundry_phase_room"}, {"id":"foundry_route_010","file":"foundry_material_fault"}, {"id":"foundry_creature_002","file":"foundry_creature"}, {"id":"foundry_earned_002","file":"second_pair"}, {"id":"foundry_final_choice","file":"foundry_choices"}, {"id":"foundry_home_004","file":"foundry_home"}, {"id":"foundry_assessment_018","file":"foundry_certificate"}, {"id":"ridge_departure_002","file":"ridge_surveyor"}, {"id":"ridge_pool_001","file":"ridge_tortoise"}, {"id":"ridge_weather_event","file":"ridge_weather"}, {"id":"ridge_incident_cloudhound_001","file":"ridge_cloudhound"}, {"id":"ridge_incident_surge_001","file":"ridge_discharge"}, {"id":"ridge_final_choice","file":"ridge_choices"}, {"id":"storm_warning_001","file":"storm_observatory"}, {"id":"storm_final_choice","file":"storm_choices"}, {"id":"salt_channels_001","file":"salt_watermill"}, {"id":"salt_findings_003","file":"salt_forewoman"}, {"id":"salt_recovery_005","file":"salt_salamander"}, {"id":"salt_final_choice","file":"salt_choices"}]:
		state.current = sample.id
		_scene()
		dialogue.visible_characters = -1
		await get_tree().create_timer(0.8).timeout
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png("res://build/screenshots/%s.png" % sample.file)
	_cultivation()
	_cultivation_selected(3)
	await get_tree().create_timer(0.4).timeout
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("res://build/screenshots/cultivation_codex.png")
	_close_popup()
	_world()
	await get_tree().create_timer(0.8).timeout
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("res://build/screenshots/world_gallery.png")
	_interiors()
	await get_tree().create_timer(0.4).timeout
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("res://build/screenshots/interior_gallery.png")
	_items()
	for index in range(world.get("items", []).size()):
		_item_selected(index)
		await get_tree().create_timer(0.4).timeout
		await RenderingServer.frame_post_draw
		var object_id := str(world.items[index].id)
		get_viewport().get_texture().get_image().save_png("res://build/screenshots/object_%s.png" % object_id)
	_close_popup()
	state.stats = {"qi": 0, "trust": 0, "insight": 0, "resolve": 0}
	for sample in [{"id":"desert_p01_008","file":"bitter_wells_yard"}, {"id":"desert_p01_034","file":"bitter_wells_workroom"}, {"id":"desert_p01_058","file":"bitter_wells_lodging"}, {"id":"desert_dilemma_origin","file":"desert_dilemma"}, {"id":"court_rain_trace_reader","file":"completed_comparison"}, {"id":"storm_claims_005","file":"storm_completed_practice"}, {"id":"salt_seed_trial_010","file":"salt_completed_practice"}]:
		state.current = sample.id
		_scene()
		dialogue.visible_characters = -1
		if state.node().has("choices"):
			_advance()
		await get_tree().create_timer(0.8).timeout
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png("res://build/screenshots/%s.png" % sample.file)

	# Capture real selected paths at identical attributes, including delayed results.
	state = StoryState.new(state.story)
	state.current = "letters_copy_choice"
	state.stats = {"qi": 10, "trust": 10, "insight": 10, "resolve": 10}
	_scene()
	dialogue.visible_characters = -1
	await get_tree().create_timer(0.8).timeout
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("res://build/screenshots/consequence_choices.png")
	var copy_results := ["letters_house_result_001", "letters_school_result_001", "letters_lamp_result_001"]
	for selection in range(copy_results.size()):
		state = StoryState.new(state.story)
		state.current = "letters_copy_choice"
		state.stats = {"qi": 10, "trust": 10, "insight": 10, "resolve": 10}
		if not state.choose(selection):
			push_error("The consequence capture could not select its actual branch.")
			_quit_game(1)
			return
		var steps := 0
		while state.current != copy_results[selection] and steps < state.story.nodes.size():
			var moved: bool
			if state.node().has("choices") and not state.node().get("random_event", false):
				moved = state.choose(0)
			else:
				moved = state.advance()
			if not moved:
				push_error("The consequence capture could not reach its delayed result.")
				_quit_game(1)
				return
			steps += 1
		if state.current != copy_results[selection] or state.stats != {"qi": 10, "trust": 10, "insight": 10, "resolve": 10}:
			push_error("The delayed consequence must differ while attributes stay identical.")
			_quit_game(1)
			return
		_scene()
		dialogue.visible_characters = -1
		await get_tree().create_timer(0.8).timeout
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png("res://build/screenshots/consequence_%s.png" % ["house", "school", "lamp"][selection])
	print("JADE_VOW_CAPTURE_OK")
	_quit_game()

func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST:
		_quit_game()

func _quit_game(exit_code: int = 0) -> void:
	var tree := get_tree()
	audio.shutdown()
	var timer := tree.create_timer(0.25)
	timer.timeout.connect(tree.quit.bind(exit_code))
	queue_free()

func _smoke_build() -> void:
	await get_tree().create_timer(1.0).timeout
	_begin()
	await get_tree().create_timer(0.5).timeout
	state.current = "first_choice"
	_scene()
	await get_tree().create_timer(0.5).timeout
	dialogue.visible_characters = -1
	_choose(0)
	await get_tree().create_timer(0.5).timeout
	var valid: bool = state.current == "trust" and audio.voice.stream != null
	valid = valid and actor.sprite.texture != null
	valid = valid and _set_outfit("shen_qing", "festival")
	valid = valid and actor.outfit == "festival" and actor.sprite.texture != null
	_set_outfit("shen_qing", Wardrobe.DEFAULT_OUTFIT)
	valid = valid and state.stats.trust == 0 and state.stats.qi == 0
	dialogue.visible_characters = -1
	_advance()
	valid = valid and state.stats.trust == 2 and state.stats.qi == 1 and state.completed_practice.has("trust")
	state.current = "river_xiu"
	_scene()
	await get_tree().create_timer(0.2).timeout
	valid = valid and actor.character == "wei_xiu" and actor.sprite.texture != null
	valid = valid and background.texture != null and audio.voice.stream != null
	state.current = "river_spirit"
	_scene()
	await get_tree().create_timer(0.2).timeout
	valid = valid and actor.character == "mooring_eel" and actor.sprite.texture != null
	state.current = "orchard_arrival"
	_scene()
	await get_tree().create_timer(0.2).timeout
	valid = valid and actor.character == "ren_qiao" and actor.sprite.texture != null and audio.voice.stream != null
	state.current = "orchard_hart_answer"
	_scene()
	await get_tree().create_timer(0.2).timeout
	valid = valid and actor.character == "frostroot_hart" and actor.sprite.texture != null and background.texture != null
	state.current = "city_arrival"
	_scene()
	await get_tree().create_timer(0.2).timeout
	valid = valid and background.texture != null and background.texture.get_size() == Vector2(1536, 1024)
	for encounter in [
		{"node": "city_mask_studio", "actor": "qiao_sen"},
		{"node": "city_registry_mei", "actor": "mei_dulan"},
		{"node": "city_registry_tao", "actor": "tao_wen"},
		{"node": "city_perfumer_workroom", "actor": "fei_nuo"},
		{"node": "city_courser_terms", "actor": "porcelain_courser"},
		{"node": "city_perfumer_moth_terms", "actor": "glasswing_moth"}
	]:
		state.current = str(encounter.node)
		_scene()
		await get_tree().create_timer(0.2).timeout
		valid = valid and actor.character == encounter.actor and actor.sprite.texture != null and audio.voice.stream != null
		if actor.sprite.texture != null:
			valid = valid and actor.sprite.texture.get_size() == Vector2(1024, 1536)
	# New encounters must be present in the source-free package.
	valid = valid and state.story.chapters.has("book_ix")
	for encounter in [{"node": "ridge_departure_002", "actor": "jiang_tao"}, {"node": "ridge_pool_001", "actor": "copperback_tortoise"}, {"node": "ridge_incident_cloudhound_001", "actor": "cloudhound"}]:
		state.current = str(encounter.node)
		_scene()
		valid = valid and actor.character == encounter.actor and actor.sprite.texture != null
		valid = valid and background.texture != null and audio.voice.stream is AudioStreamOggVorbis
	# Later books and their native originals must load in the source-free package.
	valid = valid and state.story.chapters.has("book_x_storm_ledger")
	valid = valid and state.story.chapters.has("book_xi_salt_road")
	for encounter in [{"node": "salt_findings_003", "actor": "yuan_lian"}, {"node": "salt_recovery_005", "actor": "reedglass_salamander"}]:
		state.current = str(encounter.node)
		_scene()
		valid = valid and actor.character == encounter.actor and actor.sprite.texture != null
		valid = valid and background.texture != null and audio.voice.stream is AudioStreamOggVorbis
		if actor.sprite.texture != null:
			valid = valid and actor.sprite.texture.get_size() == Vector2(1024, 1536)
	for location in [{"node": "storm_warning_001", "size": Vector2(1774, 887)}, {"node": "salt_channels_001", "size": Vector2(1672, 941)}]:
		state.current = str(location.node)
		_scene()
		valid = valid and background.texture != null and background.texture.get_size() == location.size
		valid = valid and audio.voice.stream is AudioStreamOggVorbis
	state.current = "ridge_weather_event"
	_scene()
	valid = valid and continue_button.visible and choice_box.get_child_count() == 0
	valid = valid and state.advance() and state.current.begins_with("ridge_weather_")
	# The standalone package must include modular book data, new art and Vorbis.
	valid = valid and state.story.chapters.has("book_vi")
	for encounter in [
		{"node": "court_upper_bench", "actor": "he_lian"},
		{"node": "court_luo_shan", "actor": "luo_shan"},
		{"node": "court_bai_qun", "actor": "bai_qun"},
		{"node": "court_du_heng", "actor": "du_heng"},
		{"node": "court_rain_heron", "actor": "rain_heron"},
		{"node": "court_weather_setup", "actor": "lin_yue"}
	]:
		state.current = str(encounter.node)
		_scene()
		await get_tree().create_timer(0.2).timeout
		valid = valid and actor.character == encounter.actor and actor.sprite.texture != null
		valid = valid and background.texture != null and audio.voice.stream is AudioStreamOggVorbis
	# The integrated final books, new originals and ensemble narration must survive export.
	for chapter in ["book_i", "book_ii", "book_iii", "book_iv", "book_v", "book_vi", "book_vii", "book_viii", "book_ix", "book_x_storm_ledger", "book_xi_salt_road", "book_xii_canal", "book_xiii_forest", "book_xiv_harbor", "book_xv_kiln", "book_xvi_desert", "book_xvii_archive", "book_xviii_letters"]:
		valid = state.story.chapters.has(chapter) and valid
	for encounter in [{"node": "forest_24_close_1", "actor": "lanternwing_crane"}, {"node": "archive_25_rejoin", "actor": "sun_nian"}, {"node": "archive_25_lantern_keeper", "actor": "lan_fen"}]:
		state.current = str(encounter.node)
		_scene()
		valid = valid and actor.character == encounter.actor and actor.sprite.texture != null
		valid = valid and background.texture != null and audio.voice.stream is AudioStreamOggVorbis
		if actor.sprite.texture != null:
			valid = valid and actor.sprite.texture.get_size() == Vector2(1024, 1536)
	valid = valid and background.texture != null and background.texture.get_size() == Vector2(1536, 1024)
	# Every new original and its authored encounter must survive standalone export.
	for encounter in [{"node":"expansion_xu_lin_common_001","actor":"xu_lin"},{"node":"expansion_tidemirror_otter_common_001","actor":"tidemirror_otter"},{"node":"expansion_cinderback_pangolin_common_001","actor":"cinderback_pangolin"},{"node":"expansion_chen_rui_common_001","actor":"chen_rui"},{"node":"expansion_wu_zheng_common_001","actor":"wu_zheng"},{"node":"expansion_song_mei_common_001","actor":"song_mei"}]:
		state.current = str(encounter.node)
		_scene()
		valid = valid and actor.character == encounter.actor and actor.sprite.texture != null
		valid = valid and actor.sprite.texture.get_size() == Vector2(1024, 1536)
		valid = valid and audio.voice.stream is AudioStreamOggVorbis
		valid = valid and background.texture != null
	state.current = "archive_25_006"
	_scene()
	valid = valid and stage_companions[0].visible and stage_companions[1].visible
	for companion in stage_companions:
		valid = valid and companion.sprite.texture != null
	valid = valid and background.texture != null and audio.voice.stream is AudioStreamOggVorbis
	valid = valid and atmosphere.layers == ["lanterns"]
	_cultivation()
	_cultivation_selected(12)
	var realm_selector: OptionButton = popup.find_child("CultivationSelector", true, false)
	valid = valid and cultivation_catalog.get("realms", []).size() == 12
	valid = valid and realm_selector != null and realm_selector.selected == 12
	_close_popup()
	state.current = "han_mei_shift"
	_scene()
	valid = valid and actor.character == "han_mei" and actor.sprite.texture != null
	state.current = "mortal_mite_choice"
	_scene()
	valid = valid and actor.character == "furnace_mite" and actor.sprite.texture != null
	# The packaged sluice arc must retain native art and authored advancement.
	for encounter in [{"node": "sluice_005", "actor": "duan_zhi"}, {"node": "reed_step_011", "actor": "brine_mantis"}]:
		state.current = str(encounter.node)
		_scene()
		valid = valid and actor.character == encounter.actor and actor.sprite.texture != null
		valid = valid and background.texture != null and background.texture.get_size() == Vector2(1536, 1024)
		valid = valid and audio.voice.stream is AudioStreamOggVorbis
	state.current = "channels_044"
	_scene()
	valid = valid and _cultivation_label(state.node()).contains("3: First pair")
	valid = valid and atmosphere.effect == "paired_trace"
	_items()
	_item_selected(3)
	valid = valid and item_image.texture != null and item_image.texture.get_size() == Vector2(1024, 1536)
	_close_popup()
	var retained_stats: Dictionary = state.stats.duplicate()
	state.stats = {"qi": 0, "trust": 0, "insight": 0, "resolve": 0}
	state.current = "court_final_choice"
	_scene()
	dialogue.visible_characters = -1
	_choose(3)
	valid = valid and state.current == "court_remand_proposal" and state.stats.trust == 0
	var remand_steps := 0
	while state.current != "court_remand_review" and remand_steps < 12:
		dialogue.visible_characters = -1
		_advance()
		remand_steps += 1
	valid = valid and state.current == "court_remand_review" and state.stats.trust == 0
	dialogue.visible_characters = -1
	_advance()
	valid = valid and state.stats.trust == 2 and state.completed_practice.has("court_remand_review")
	state.stats = retained_stats
	_interiors()
	_interior_selected(_interior_entries().size() - 1)
	valid = valid and interior_image.texture != null
	_items()
	_item_selected(1)
	valid = valid and item_image.texture != null
	if item_image.texture != null:
		valid = valid and item_image.texture.get_size() == Vector2(1536, 1024)
	_close_popup()
	_attributes()
	var attribute_value: Label = popup.find_child("AttributeValue_trust", true, false)
	valid = valid and attribute_value != null and attribute_value.text == "Dao Heart · 2"
	_close_popup()
	# Walk the new authored choice to its delayed result inside the exported pack.
	state = StoryState.new(state.story)
	state.current = "letters_copy_choice"
	state.stats = {"qi": 10, "trust": 10, "insight": 10, "resolve": 10}
	var copy_selected: bool = state.choose(0)
	valid = copy_selected and valid
	var consequence_steps := 0
	while state.current != "letters_house_result_001" and consequence_steps < 100:
		var moved: bool
		if state.node().has("choices") and not state.node().get("random_event", false):
			moved = state.choose(0)
		else:
			moved = state.advance()
		if not moved:
			valid = false
			break
		consequence_steps += 1
	valid = state.current == "letters_house_result_001" and valid
	valid = state.decisions.get("letters_copy_choice", "") == "letters_copy_house" and valid
	valid = state.stats == {"qi": 10, "trust": 10, "insight": 10, "resolve": 10} and valid
	_scene()
	valid = audio.voice.stream is AudioStreamOggVorbis and valid
	valid = actor.sprite.texture != null and background.texture != null and valid
	state.current = "letters_watch_end"
	_scene()
	valid = state.node().get("ending", "") == "The Covers and the Receiving Date" and valid
	valid = audio.voice.stream is AudioStreamOggVorbis and valid
	valid = actor.sprite.texture != null and background.texture != null and valid
	if valid:
		print("JADE_VOW_PACKAGE_OK: standalone story, world art, object inspection and narration")
	else:
		push_error("Packaged assets or story failed to load")
	_quit_game(0 if valid else 1)

func _world() -> void:
	var column := _make_popup("Places, people & spirit beasts")
	var interiors := Button.new()
	interiors.text = "Interiors →"
	interiors.pressed.connect(_interiors)
	column.get_child(0).add_child(interiors)
	var objects := Button.new()
	objects.text = "Inspect objects →"
	objects.pressed.connect(_items)
	column.get_child(0).add_child(objects)
	popup.position = Vector2(210, 130)
	popup.size = Vector2(1180, 680)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 24)
	column.add_child(row)
	for group in ["backgrounds", "npcs", "monsters"]:
		var card := VBoxContainer.new()
		card.custom_minimum_size = Vector2(350, 540)
		row.add_child(card)
		var label := Label.new()
		label.text = {"backgrounds": "Places", "npcs": "People", "monsters": "Spirit beasts"}[group]
		label.add_theme_color_override("font_color", GOLD)
		card.add_child(label)
		var selector := OptionButton.new()
		selector.name = "World_" + group
		selector.custom_minimum_size = Vector2(350, 45)
		selector.clip_text = true
		for entry in world.get(group, []):
			selector.add_item(str(entry.name))
		card.add_child(selector)
		var image := TextureRect.new()
		image.custom_minimum_size = Vector2(350, 345)
		image.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		image.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		card.add_child(image)
		var description := RichTextLabel.new()
		description.custom_minimum_size = Vector2(350, 120)
		description.add_theme_font_size_override("normal_font_size", 16)
		card.add_child(description)
		world_previews[group] = {"image": image, "description": description}
		selector.item_selected.connect(_world_selected.bind(group))
		_world_selected(0, group)

func _world_selected(index: int, group: String) -> void:
	var entries: Array = world.get(group, [])
	if index < 0 or index >= entries.size() or not world_previews.has(group):
		return
	var selector: OptionButton = popup.find_child("World_" + group, true, false)
	if selector != null:
		selector.select(index)
	var entry: Dictionary = entries[index]
	world_previews[group].image.texture = load("res://" + str(entry.path))
	world_previews[group].description.text = str(entry.description)


func _interior_entries() -> Array:
	var entries: Array = []
	for entry in world.get("backgrounds", []):
		if entry.get("collection", "") == "building_interiors":
			entries.append(entry)
	return entries

func _interiors() -> void:
	var column := _make_popup("Inside the world")
	popup.position = Vector2(210, 95)
	popup.size = Vector2(1180, 700)
	column.add_theme_constant_override("separation", 12)
	var selector := OptionButton.new()
	selector.name = "InteriorSelector"
	selector.custom_minimum_size.y = 44
	selector.clip_text = true
	for entry in _interior_entries():
		selector.add_item(str(entry.name))
	column.add_child(selector)
	interior_image = TextureRect.new()
	interior_image.custom_minimum_size = Vector2(1100, 440)
	interior_image.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	interior_image.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	column.add_child(interior_image)
	interior_description = RichTextLabel.new()
	interior_description.custom_minimum_size = Vector2(1100, 60)
	interior_description.add_theme_font_size_override("normal_font_size", 18)
	column.add_child(interior_description)
	selector.item_selected.connect(_interior_selected)
	_interior_selected(0)

func _interior_selected(index: int) -> void:
	var entries: Array = _interior_entries()
	if index < 0 or index >= entries.size() or popup == null:
		return
	var selector: OptionButton = popup.find_child("InteriorSelector", true, false)
	if selector == null or not is_instance_valid(interior_image):
		return
	selector.select(index)
	var entry: Dictionary = entries[index]
	interior_image.texture = load("res://" + str(entry.path))
	interior_description.text = str(entry.description)

func _items() -> void:
	var column := _make_popup("Objects & their keepers")
	var selector := OptionButton.new()
	selector.name = "ObjectSelector"
	for entry in world.get("items", []):
		selector.add_item(str(entry.name))
	column.add_child(selector)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 32)
	column.add_child(row)
	item_image = TextureRect.new()
	item_image.custom_minimum_size = Vector2(470, 430)
	item_image.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	item_image.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	row.add_child(item_image)
	item_description = RichTextLabel.new()
	item_description.custom_minimum_size = Vector2(440, 430)
	item_description.add_theme_font_size_override("normal_font_size", 23)
	row.add_child(item_description)
	selector.item_selected.connect(_item_selected)
	_item_selected(0)

func _item_selected(index: int) -> void:
	var entries: Array = world.get("items", [])
	if index < 0 or index >= entries.size():
		return
	# Keep programmatic selection (including captures) consistent with the control.
	if popup == null or not is_instance_valid(item_image):
		return
	var selector: OptionButton = popup.find_child("ObjectSelector", true, false)
	if selector != null:
		selector.select(index)
	var entry: Dictionary = entries[index]
	item_image.texture = load("res://" + str(entry.path))
	item_description.text = str(entry.description)

# ConfigFile permits arbitrary Variant values. Reject damaged numeric/bool fields
# before converting them, and require finite numbers for sliders.
func _setting_number(config: ConfigFile, section: String, key: String, fallback: float, minimum: float, maximum: float) -> float:
	var value = config.get_value(section, key, fallback)
	if not (value is int or value is float) or not is_finite(float(value)):
		return fallback
	return clampf(float(value), minimum, maximum)

func _setting_bool(config: ConfigFile, section: String, key: String, fallback: bool) -> bool:
	var value = config.get_value(section, key, fallback)
	return value if value is bool else fallback
