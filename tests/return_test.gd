extends SceneTree

const StoryState = preload("res://scripts/story_state.gd")
var failures := 0

func check(ok: bool, message: String) -> void:
	if not ok:
		push_error(message)
		failures += 1

func walk(traveler, target: String) -> bool:
	var steps := 0
	while traveler.current != target and steps < 100:
		if traveler.node().has("ending") or traveler.node().has("choices") or not traveler.advance():
			return false
		steps += 1
	return traveler.current == target

func _initialize() -> void:
	var traveler = StoryState.new()
	var endings := ["return_public_close", "return_source_close", "return_listener_close"]
	for path in ["water", "archive", "road", "kiln", "garden", "harbor"]:
		var original = StoryState.new(traveler.story)
		original.current = "season_end_" + path
		var title: String = original.node().ending
		check(original.advance() and original.current == "return_001", "Every real season ending must continue")
		check(original.history.back().text == traveler.story.nodes["season_end_" + path].text, "The prior ending must remain in the journal")
		check(not title.is_empty(), "Retain the prior ending's identity")
	traveler.current = "return_001"
	check(walk(traveler, "return_choice"), "Read the complete finding before choosing an approach")
	var save_path := "user://return_test_choice.json"
	check(traveler.save_game(save_path), "Save before the first return decision")
	for selection in range(endings.size()):
		var restored = StoryState.new(traveler.story)
		check(restored.load_game(save_path), "Restore the actual choice checkpoint")
		check(restored.choose(selection), "Every return approach must be available at zero scores")
		var destination: String = restored.story.nodes.return_choice.choices[selection].next
		check(restored.decisions.get("return_choice", "") == destination, "Save the actual selected destination")
		check(walk(restored, endings[selection]), "Keep each chosen consequence and its own ending")
		check(restored.stats == {"qi": 0, "trust": 0, "insight": 0, "resolve": 0}, "Returning awards no unperformed growth")
		var finish_path := "user://return_test_finish.json"
		check(restored.save_game(finish_path), "Save the actual ending")
		var loaded = StoryState.new(traveler.story)
		check(loaded.load_game(finish_path) and loaded.current == endings[selection], "Restore the distinct ending")
		check(loaded.decisions == restored.decisions and loaded.history == restored.history, "Retain the real choice and journal")
		for suffix in ["", ".bak", ".tmp"]:
			if FileAccess.file_exists(finish_path + suffix):
				DirAccess.remove_absolute(finish_path + suffix)
	for suffix in ["", ".bak", ".tmp"]:
		if FileAccess.file_exists(save_path + suffix):
			DirAccess.remove_absolute(save_path + suffix)
	if failures == 0:
		print("JADE_VOW_RETURN_TESTS_OK")
	quit(0 if failures == 0 else 1)
