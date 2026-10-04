extends RefCounted

# Ranks describe growth; story gates continue to use exact point totals.
const KEYS := ["qi", "trust", "insight", "resolve"]
const RANK_THRESHOLDS := [0, 3, 6, 10]
const DEFINITIONS := {
	"qi": {
		"name": "Qi Control",
		"description": "Precision of admission, circulation and clean discharge on already earned routes. Points never supply fuel or award a realm.",
		"growth": "Grow through calibrated practice. Realm advancement needs its own tests and recovery.",
		"ranks": ["Unpracticed", "Measured", "Controlled", "Precise"]
	},
	"trust": {
		"name": "Dao Heart",
		"description": "Steadiness against fear, greed and heart demons; expressed by honest limits and freely kept commitments.",
		"growth": "Grow by resisting shortcuts, admitting mistakes and honoring another person\'s refusal. No rank buys consent.",
		"ranks": ["Unexamined", "Grounded", "Steady", "Clear"]
	},
	"insight": {
		"name": "Comprehension",
		"description": "Ability to study techniques, formations and evidence, and distinguish a tested mechanism from an attractive guess.",
		"growth": "Grow by asking questions, studying inscriptions, and comparing records.",
		"ranks": ["Searching", "Observant", "Discerning", "Lucid"]
	},
	"resolve": {
		"name": "Physique",
		"description": "Ordinary conditioning, balance and recovery under safe loads. Strength does not open an unearned meridian.",
		"growth": "Grow through recovered conditioning, safe carrying and ordinary footwork. Paperwork and determination do not train tissue.",
		"ranks": ["Untried", "Rooted", "Tempered", "Unshaken"]
	}
}

static func attribute_name(key: String) -> String:
	return str(DEFINITIONS.get(key, {}).get("name", key.capitalize()))

static func profile(key: String, value: int) -> Dictionary:
	if not DEFINITIONS.has(key):
		return {}
	var definition: Dictionary = DEFINITIONS[key]
	var rank_index := 0
	for index in range(RANK_THRESHOLDS.size()):
		if value >= RANK_THRESHOLDS[index]:
			rank_index = index
	var minimum: int = RANK_THRESHOLDS[rank_index]
	var next_minimum: int = RANK_THRESHOLDS[rank_index + 1] if rank_index + 1 < RANK_THRESHOLDS.size() else -1
	var progress := 1.0
	if next_minimum >= 0:
		progress = clampf(float(value - minimum) / float(next_minimum - minimum), 0.0, 1.0)
	return {
		"name": definition.name,
		"description": definition.description,
		"growth": definition.growth,
		"value": value,
		"rank": definition.ranks[rank_index],
		"rank_minimum": minimum,
		"next_minimum": next_minimum,
		"remaining": maxi(0, next_minimum - value),
		"progress": progress
	}
