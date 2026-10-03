extends RefCounted

# Ranks describe growth; story gates continue to use exact point totals.
const KEYS := ["qi", "trust", "insight", "resolve"]
const RANK_THRESHOLDS := [0, 3, 6, 10]
const DEFINITIONS := {
	"qi": {
		"name": "Qi",
		"description": "Spiritual energy used to channel wards and share their burden.",
		"growth": "Grow through breathing practice and working with protective wards.",
		"ranks": ["Dormant", "Kindled", "Flowing", "Resonant"]
	},
	"trust": {
		"name": "Trust",
		"description": "The bonds that help people act together by choice.",
		"growth": "Grow by listening, sharing responsibility, and honoring permission.",
		"ranks": ["Unproven", "Open", "Reliable", "Steadfast"]
	},
	"insight": {
		"name": "Insight",
		"description": "Understanding of old vows, hidden evidence, and possible solutions.",
		"growth": "Grow by asking questions, studying inscriptions, and comparing records.",
		"ranks": ["Searching", "Observant", "Discerning", "Lucid"]
	},
	"resolve": {
		"name": "Resolve",
		"description": "The will to carry a promise through difficult decisions.",
		"growth": "Grow through sword practice, protecting others, and keeping commitments.",
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
