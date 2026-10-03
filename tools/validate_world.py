"""Validate delivered world art and story; report production targets honestly."""
import argparse
import hashlib
import json
import pathlib
from collections import deque

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
STAT_KEYS = {"qi", "trust", "insight", "resolve"}
BASE_ACTORS = {"lin_yue", "shen_qing", "elder_yun", "mo_ran"}
WORD_TARGET = 1000001
ORIGINAL_ART_TARGETS = {"backgrounds": 100, "npcs": 100, "monsters": 100}
ADDITIONAL_ART_TARGETS = {"building_interiors": 100}


def delivery_report(world, words, scenes):
    """Keep the 100 extra interiors separate from the original 100 backgrounds."""
    delivered = {group: len(world[group]) for group in ORIGINAL_ART_TARGETS}
    interiors = sum(entry.get("collection") == "building_interiors"
                    for entry in world["backgrounds"])
    original = dict(delivered)
    original["backgrounds"] -= interiors
    deficits = {"authored_words": max(0, WORD_TARGET - words)}
    deficits.update({group: max(0, target - original[group])
                     for group, target in ORIGINAL_ART_TARGETS.items()})
    deficits["building_interiors"] = max(0, ADDITIONAL_ART_TARGETS["building_interiors"] - interiors)
    art_met = all(original[group] >= target
                  for group, target in ORIGINAL_ART_TARGETS.items())
    art_met = art_met and interiors >= ADDITIONAL_ART_TARGETS["building_interiors"]
    return {
        "scenes": scenes,
        "authored_words": words,
        "word_target": WORD_TARGET,
        "word_target_met": words >= WORD_TARGET,
        "delivered_art": delivered,
        "delivered_original_art": original,
        "delivered_additional_art": {"building_interiors": interiors},
        "delivered_items": len(world.get("items", [])),
        "art_targets": {"backgrounds": 200, "npcs": 100, "monsters": 100},
        "original_art_targets": dict(ORIGINAL_ART_TARGETS),
        "additional_art_targets": dict(ADDITIONAL_ART_TARGETS),
        "art_targets_met": art_met,
        "remaining": deficits,
        "complete": words >= WORD_TARGET and art_met,
    }


def reachable_without(story, omitted):
    reached, queue = set(), deque([story["start"]])
    while queue:
        key = queue.popleft()
        if key == omitted or key in reached:
            continue
        reached.add(key)
        node = story["nodes"][key]
        queue.extend(node[field] for field in ("next", "continuation") if field in node)
        queue.extend(choice["next"] for choice in node.get("choices", []))
    return reached


def inspect(root):
    world = json.loads((root / "data/world_assets.json").read_text())
    story = json.loads((root / "data/story.json").read_text())
    assert world["requested"] == {"backgrounds": 200, "npcs": 100, "monsters": 100}, "Preserve all original and extra art quotas"
    assert world["requested_additional"] == ADDITIONAL_ART_TARGETS, "Preserve the 100 extra interiors"
    ids, paths, hashes = set(), set(), set()
    for group in ("backgrounds", "npcs", "monsters", "items"):
        for entry in world.get(group, []):
            assert entry["id"] not in ids, "Duplicate world ID"
            assert entry["path"] not in paths, "Duplicate artwork path"
            if "collection" in entry:
                assert group == "backgrounds" and entry["collection"] == "building_interiors", "Unknown art collection"
                assert entry.get("environment") == "interior", "Extra backgrounds must be building interiors"
            ids.add(entry["id"])
            paths.add(entry["path"])
            path = root / entry["path"]
            assert path.is_file(), f"Missing artwork: {path}"
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            assert digest not in hashes, "Duplicated artwork must not inflate counts"
            hashes.add(digest)
            with Image.open(path) as image:
                assert list(image.size) == entry["native_size"], "Keep native resolution"
                image.verify()
            if group != "backgrounds":
                with Image.open(path) as image:
                    assert image.mode == "RGBA", "Sprites require native alpha"
                    assert image.getchannel("A").getextrema()[0] < 255, "Sprite background must contain transparency"
    backgrounds = {entry["id"] for entry in world["backgrounds"]}
    actors = BASE_ACTORS | {entry["id"] for group in ("npcs", "monsters") for entry in world[group]}
    texts = set()
    for key, node in story["nodes"].items():
        assert node["speaker"] in story["characters"], f"Unknown speaker in {key}"
        assert node["actor"] in actors, f"Unknown actor in {key}"
        assert node["text"].strip(), f"Empty scene {key}"
        normalized = " ".join(node["text"].split())
        assert normalized not in texts, f"Repeated scene prose must not inflate the manuscript: {key}"
        texts.add(normalized)
        assert len(node["text"].split()) <= 100, f"Keep dialogue readable in {key}"
        assert sum(field in node for field in ("next", "choices", "ending")) == 1, f"Ambiguous navigation: {key}"
        if "effect" in node:
            assert node["effect"] in {"lanterns", "rain", "reed_light", "bell", "qi", "none"}
        if "background" in node:
            assert node["background"] in backgrounds
        if "chapter" in node:
            assert node["chapter"] in story["chapters"]
        if "continuation" in node:
            assert "ending" in node and node["continuation"] in story["nodes"]
        if "next" in node:
            assert node["next"] in story["nodes"]
        for choice in node.get("choices", []):
            assert choice["next"] in story["nodes"]
            for field in ("effects", "requires"):
                for stat, value in choice.get(field, {}).items():
                    assert stat in STAT_KEYS and isinstance(value, int)
                    if field == "requires":
                        assert value >= 0
    continuity = json.loads((root / "data/continuity.json").read_text())
    assert set(continuity["reviewed_chapters"]) == set(story["chapters"]), "Review every delivered chapter"
    for fact in continuity["facts"]:
        assert fact["statement"].strip() and fact["anchors"]
        assert set(fact["anchors"]) <= set(story["nodes"]), f"Missing continuity anchor: {fact['id']}"
    reached, queue = set(), deque([story["start"]])
    while queue:
        key = queue.popleft()
        if key in reached:
            continue
        reached.add(key)
        node = story["nodes"][key]
        queue.extend(node[field] for field in ("next", "continuation") if field in node)
        queue.extend(choice["next"] for choice in node.get("choices", []))
    assert reached == set(story["nodes"]), "Every scene must be reachable"
    for checkpoint in continuity.get("checkpoints", []):
        target = checkpoint["before"]
        assert target in story["nodes"]
        for required in checkpoint["required"]:
            assert required in story["nodes"]
            assert target not in reachable_without(story, required), (
                f"Continuity checkpoint {checkpoint['id']} bypasses {required}"
            )
    words = sum(len(node["text"].split()) for node in story["nodes"].values())
    return delivery_report(world, words, len(story["nodes"]))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-complete", action="store_true",
                        help="Fail unless the manuscript, original art, and 100 extra interiors are delivered")
    args = parser.parse_args(argv)
    report = inspect(ROOT)
    output = ROOT / "build/content_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if args.require_complete and not report["complete"]:
        print("Production deliverables remain unfinished; see the remaining counts above.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
