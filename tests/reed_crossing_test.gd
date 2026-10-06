extends SceneTree

const State = preload("res://scripts/story_state.gd")
const SAVE_PATH := "user://reed_crossing_test.json"
var failures: Array[String] = []

func check(condition: bool, message: String) -> void:
	if not condition:
		failures.append(message)
		push_error(message)

func clear_save() -> void:
	for suffix in ["", ".bak", ".tmp"]:
		if FileAccess.file_exists(SAVE_PATH + suffix):
			DirAccess.remove_absolute(SAVE_PATH + suffix)

func _initialize() -> void:
	clear_save()
	var campaign: Dictionary = State.new().story
	var paths := 0
	var outcomes: Dictionary = {}
	for diagnostic in range(4):
		for cargo in range(3):
			for notice in range(3):
				for funding in range(3):
					var state = State.new(campaign)
					state.current = "crossing_entry"
					state.stats = {"qi": 10, "trust": 10, "insight": 10, "resolve": 10}
					var visited: Dictionary = {}
					var steps := 0
					while state.current != "crossing_final_common" and steps < 180:
						visited[state.current] = true
						var moved := false
						match state.current:
							"crossing_diagnostic_choice":
								var before: Dictionary = state.stats.duplicate()
								moved = state.choose(diagnostic)
								check(state.stats == before, "Selecting a method must not award practice")
							"crossing_load_choice":
								check(state.save_game(SAVE_PATH), "Cargo-boundary checkpoint must save")
								var restored = State.new(campaign)
								check(restored.load_game(SAVE_PATH), "Cargo-boundary checkpoint must load")
								check(restored.decisions == state.decisions and restored.stats == state.stats, "Method and actual completed practice must survive loading")
								state = restored
								moved = state.choose(cargo)
							"crossing_notice_choice":
								moved = state.choose(notice)
							"crossing_fund_choice":
								moved = state.choose(funding)
							_:
								moved = state.advance()
						check(moved, "Every offered path must progress: " + state.current)
						if not moved:
							break
						steps += 1
					check(state.current == "crossing_final_common", "Each full method/cargo/notice/policy combination must finish")
					var cargo_result: String = ["crossing_grain_result_01", "crossing_linen_result_01", "crossing_wages_result_01"][cargo]
					var policy_result: String = ["crossing_end_grain", "crossing_end_linen", "crossing_end_wages"][funding]
					check(visited.has(cargo_result) and visited.has(policy_result), "Final account must preserve both actual selections")
					if funding == 0:
						var quantity: String = ["crossing_order_six_01", "crossing_order_twelve_gap_01", "crossing_order_twelve_01"][cargo]
						check(visited.has(quantity), "Grain order must use its actual prior cargo quantity")
					check(state.stats.qi == 10 + (1 if diagnostic == 0 else 0), "Only completed qi work earns qi")
					check(state.stats.insight == 10 + (1 if diagnostic == 1 else 0), "Only completed source study earns comprehension")
					check(state.stats.resolve == 10 + (1 if diagnostic == 2 else 0), "Only completed rod work earns physique")
					check(state.stats.trust == 10 + (1 if notice == 0 else 0), "Only completed open responsibility earns Dao Heart")
					outcomes[str(cargo) + ":" + str(funding)] = true
					paths += 1
	check(paths == 108 and outcomes.size() == 9, "All 108 combinations must retain nine cargo-policy accounts")
	var low = State.new(campaign)
	low.current = "crossing_diagnostic_choice"
	check(not low.can_choose(low.node().choices[0]) and not low.can_choose(low.node().choices[1]), "Untrained players cannot lead trained diagnoses")
	check(low.can_choose(low.node().choices[2]) and low.can_choose(low.node().choices[3]), "Two ordinary diagnostic approaches remain available")
	low.current = "crossing_notice_choice"
	check(not low.can_choose(low.node().choices[0]) and low.can_choose(low.node().choices[1]) and low.can_choose(low.node().choices[2]), "Ordinary explanation methods remain available")
	var practice = State.new(campaign)
	practice.current = "crossing_rod_03"
	check(practice.advance() and practice.stats.resolve == 1, "Physical credit follows actual completed rod work")
	practice.current = "crossing_rod_03"
	check(practice.advance() and practice.stats.resolve == 1, "Revisiting completed rod work cannot repay practice")
	clear_save()
	if failures.is_empty():
		print("JADE_VOW_REED_CROSSING_TESTS_OK: 108 paths; 9 retained cargo-policy accounts")
	quit(0 if failures.is_empty() else 1)
