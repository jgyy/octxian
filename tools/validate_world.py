"""Validate delivered world art and story; report production targets honestly."""
import json
import pathlib
from collections import deque

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
STAT_KEYS = {"qi", "trust", "insight", "resolve"}
BASE_ACTORS = {"lin_yue", "shen_qing", "elder_yun", "mo_ran"}


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
    ids, paths, hashes = set(), set(), set()
    import hashlib
    for group in ("backgrounds", "npcs", "monsters", "items"):
        for entry in world.get(group, []):
            assert entry["id"] not in ids, "Duplicate world ID"
            assert entry["path"] not in paths, "Duplicate artwork path"
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
    for key, node in story["nodes"].items():
        assert node["speaker"] in story["characters"], f"Unknown speaker in {key}"
        assert node["actor"] in actors, f"Unknown actor in {key}"
        assert node["text"].strip(), f"Empty scene {key}"
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
    # Structural reachability is independent of the gated state traversal in Godot.
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
    # Required knowledge/safety scenes must dominate their decision in every
    # structural path, so a future shortcut cannot silently skip the evidence.
    for checkpoint in continuity.get("checkpoints", []):
        target = checkpoint["before"]
        assert target in story["nodes"]
        for required in checkpoint["required"]:
            assert required in story["nodes"]
            assert target not in reachable_without(story, required), (
                f"Continuity checkpoint {checkpoint['id']} bypasses {required}"
            )
    # Count displayed prose once. Catalog descriptions, choice labels, design
    # documents and the number of possible traversals are not manuscript words.
    words = sum(len(node["text"].split()) for node in story["nodes"].values())
    report = {
        "scenes": len(story["nodes"]),
        "authored_words": words,
        "word_target": 1000001,
        "word_target_met": words >= 1000001,
        "delivered_art": {group: len(world[group]) for group in ("backgrounds", "npcs", "monsters")},
        "delivered_items": len(world.get("items", [])),
        "art_targets": world["requested"],
    }
    report["art_targets_met"] = all(report["delivered_art"][group] >= target for group, target in world["requested"].items())
    return report


def main():
    report = inspect(ROOT)
    output = ROOT / "build/content_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
