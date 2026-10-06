extends SceneTree

const State = preload("res://scripts/story_state.gd")
const SAVE_PATH := "user://authored_consequences_test.json"
var failures: Array[String] = []

func check(condition: bool, message: String) -> void:
	if not condition:
		failures.append(message)
		push_error(message)

func _clear_checkpoint() -> void:
	for suffix in ["", ".bak", ".tmp"]:
		if FileAccess.file_exists(SAVE_PATH + suffix):
			DirAccess.remove_absolute(SAVE_PATH + suffix)

func _initialize() -> void:
	_clear_checkpoint()
	var campaign: Dictionary = State.new().story
	var checked := 0
	for router_id in campaign.nodes:
		var router: Dictionary = campaign.nodes[router_id]
		if not router.has("routes"):
			continue
		var legacy = State.new(campaign)
		legacy.current = router_id
		check(legacy.advance() and legacy.current == router.next, "An actual campaign router must preserve its unspecified legacy fallback: " + router_id)
		for route in router.routes:
			var source: Dictionary = campaign.nodes[route.decision]
			var option := -1
			for index in range(source.choices.size()):
				if source.choices[index].next == route.selected:
					option = index
			var chosen = State.new(campaign)
			chosen.current = route.decision
			# This contract checks identity and delayed routing; complete route
			# traversal separately checks which attribute gates can be earned.
			chosen.stats = {"qi": 100, "trust": 100, "insight": 100, "resolve": 100}
			check(option >= 0 and chosen.choose(option), "Every authored delayed condition must originate in a playable real menu option: " + router_id)
			var expected_decision := {}
			expected_decision[route.decision] = route.selected
			check(chosen.decisions == expected_decision, "An authored option must record the stable destination named by its later route: " + router_id)
			# Equalize scores to prove that this later destination uses the
			# recorded commitment rather than a numerical attribute difference.
			chosen.stats = {"qi": 50, "trust": 50, "insight": 50, "resolve": 50}
			chosen.current = router_id
			check(chosen.save_game(SAVE_PATH), "An authored delayed commitment must save before its consequence: " + router_id)
			var restored = State.new(campaign)
			check(restored.load_game(SAVE_PATH) and restored.decisions == chosen.decisions, "An authored delayed commitment must survive checkpoint loading: " + router_id)
			check(restored.stats == chosen.stats and restored.advance() and restored.current == route.next, "Equal-score journeys must still follow their authored saved consequence: " + router_id)
			checked += 1
	check(checked > 0, "The delivered campaign must contain actual delayed narrative consequences")
	_clear_checkpoint()
	if failures.is_empty():
		print("JADE_VOW_AUTHORED_CONSEQUENCES_TESTS_OK: %d authored conditions" % checked)
	quit(0 if failures.is_empty() else 1)
