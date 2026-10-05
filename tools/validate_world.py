"""Validate delivered world art and story; report production targets honestly."""
import argparse
import hashlib
import json
import pathlib
from collections import deque

from PIL import Image

if __package__:
    from .story_data import authored_word_count, load_story
    from .cultivation import load_canon, validate_progress, validate_delivery
else:
    from story_data import authored_word_count, load_story
    from cultivation import load_canon, validate_progress, validate_delivery

ROOT = pathlib.Path(__file__).resolve().parents[1]
STAT_KEYS = {"qi", "trust", "insight", "resolve"}
BASE_ACTORS = {"lin_yue", "shen_qing", "elder_yun", "mo_ran"}
WORD_TARGET = 1000001
SPRITE_TARGET = 1001
MIN_SPRITE_NATIVE_SIZE = (1024, 1536)
ORIGINAL_ART_TARGETS = {"backgrounds": 100, "npcs": 500, "monsters": 501}
ADDITIONAL_ART_TARGETS = {"building_interiors": 100}
HISTORICAL_SPRITES = {
    "su_lan", "wei_jin", "an_ru", "wei_xiu", "reed_listener", "mooring_eel",
}


def native_sprite_size(size):
    """Require genuine native detail, accepting either canvas orientation."""
    return (min(size) >= MIN_SPRITE_NATIVE_SIZE[0]
            and max(size) >= MIN_SPRITE_NATIVE_SIZE[1])


def painting_fingerprint(image):
    """Ignore PNG metadata, hidden RGB, and transparent canvas padding."""
    rgba = image.convert("RGBA")
    bounds = rgba.getchannel("A").getbbox()
    assert bounds is not None, "Artwork must contain visible pixels"
    rgba = rgba.crop(bounds)
    rendered = Image.new("RGBA", rgba.size, (0, 0, 0, 255))
    rendered.alpha_composite(rgba)
    digest = hashlib.sha256()
    digest.update(f"{rgba.width}x{rgba.height}:".encode())
    digest.update(rendered.convert("RGB").tobytes())
    digest.update(rgba.getchannel("A").tobytes())
    return digest.hexdigest()


def local_asset_path(root, name):
    assert isinstance(name, str) and name, "Asset references must be paths"
    path = (root / name).resolve()
    assert path.is_relative_to(root.resolve()), "Asset references must stay in the repository"
    assert path.is_file(), f"Missing asset reference: {name}"
    return path


def validate_sprite_provenance(root, entry):
    """Verify retained native sources; design originality also needs review."""
    provenance = entry.get("provenance")
    assert isinstance(provenance, dict), f"Record original provenance for {entry['id']}"
    assert provenance.get("kind") == "original_painting", "Count original paintings only"
    assert provenance.get("derivation") == "none", "Variants do not count as new originals"
    assert not provenance.get("derived_from"), "Derived sprites do not count as new originals"
    source = local_asset_path(root, provenance.get("source_path"))
    record_name = provenance.get("record")
    record = local_asset_path(root, record_name)
    record_text = record.read_text(encoding="utf-8").strip()
    assert record_text, "Original creation records must contain evidence"
    historical = (entry["id"] in HISTORICAL_SPRITES
                  and record_name == "assets/art/PROVENANCE.md")
    assert (historical or entry["id"] in record_text or entry["path"] in record_text), (
        "Creation record must identify the original"
    )
    source_digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if "source_sha256" in provenance:
        assert provenance["source_sha256"] == source_digest, "Original source checksum changed"
    with Image.open(source) as original:
        original.load()
        assert list(original.size) == provenance.get("native_size"), "Record source native dimensions"
        assert list(original.size) == entry["native_size"], "Do not enlarge or crop the retained original"
        assert native_sprite_size(original.size), "Original portraits require native 1024×1536 or higher"
        with Image.open(root / entry["path"]) as delivered:
            delivered.load()
            assert painting_fingerprint(original) == painting_fingerprint(delivered), (
                "The delivered sprite must retain the original painting"
            )
    return source_digest


def delivery_report(world, words, scenes):
    """Keep extra interiors separate and count each original sprite once."""
    delivered = {group: len(world[group]) for group in ORIGINAL_ART_TARGETS}
    interiors = sum(entry.get("collection") == "building_interiors"
                    for entry in world["backgrounds"])
    original = dict(delivered)
    original["backgrounds"] -= interiors
    sprites = original["npcs"] + original["monsters"]
    deficits = {"authored_words": max(0, WORD_TARGET - words)}
    deficits.update({group: max(0, target - original[group])
                     for group, target in ORIGINAL_ART_TARGETS.items()})
    deficits["building_interiors"] = max(0, ADDITIONAL_ART_TARGETS["building_interiors"] - interiors)
    deficits["unique_sprites"] = max(0, SPRITE_TARGET - sprites)
    art_met = all(original[group] >= target
                  for group, target in ORIGINAL_ART_TARGETS.items())
    art_met = (art_met
               and interiors >= ADDITIONAL_ART_TARGETS["building_interiors"]
               and sprites >= SPRITE_TARGET)
    return {
        "scenes": scenes,
        "authored_words": words,
        "word_target": WORD_TARGET,
        "word_target_met": words >= WORD_TARGET,
        "delivered_art": delivered,
        "delivered_original_art": original,
        "delivered_additional_art": {"building_interiors": interiors},
        "delivered_items": len(world.get("items", [])),
        "delivered_unique_sprites": sprites,
        "sprite_target": SPRITE_TARGET,
        "sprite_target_met": sprites >= SPRITE_TARGET,
        "minimum_sprite_native_size": list(MIN_SPRITE_NATIVE_SIZE),
        "art_targets": {"backgrounds": 200, "npcs": 500, "monsters": 501},
        "original_art_targets": dict(ORIGINAL_ART_TARGETS),
        "additional_art_targets": dict(ADDITIONAL_ART_TARGETS),
        "art_targets_met": art_met,
        "remaining": deficits,
        "complete": words >= WORD_TARGET and art_met,
        "originality_validation": (
            "Retained original sources, native dimensions, file hashes, and "
            "decoded pixels are checked. Distinct designs require editorial "
            "review; poses, recolors, mirrors, and other derivatives do not "
            "qualify as independent originals."
        ),
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
    story = load_story(root)
    validate_progress(load_canon(root), story)
    assert world["requested"] == {"backgrounds": 200, "npcs": 500, "monsters": 501}, "Preserve background quotas and 1001 original sprites"
    assert world["requested_additional"] == ADDITIONAL_ART_TARGETS, "Preserve the 100 extra interiors"
    ids, paths, hashes, pixel_hashes, sprite_sources = set(), set(), set(), set(), set()
    for group in ("backgrounds", "npcs", "monsters", "items", "effects"):
        for entry in world.get(group, []):
            assert entry["id"] not in ids, "Duplicate world ID"
            assert entry["path"] not in paths, "Duplicate artwork path"
            if "collection" in entry:
                assert group == "backgrounds" and entry["collection"] == "building_interiors", "Unknown art collection"
                assert entry.get("environment") == "interior", "Extra backgrounds must be building interiors"
            ids.add(entry["id"])
            paths.add(entry["path"])
            path = local_asset_path(root, entry["path"])
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            assert digest not in hashes, "Duplicated artwork must not inflate counts"
            hashes.add(digest)
            with Image.open(path) as image:
                assert list(image.size) == entry["native_size"], "Keep native resolution"
                image.verify()
            with Image.open(path) as image:
                image.load()
                pixels = painting_fingerprint(image)
                assert pixels not in pixel_hashes, "Reencoding or transparent padding must not inflate counts"
                pixel_hashes.add(pixels)
                if group != "backgrounds":
                    assert image.mode == "RGBA", "Sprites require native alpha"
                    minimum, maximum = image.getchannel("A").getextrema()
                    assert minimum == 0 and maximum > 0, f"Sprites require visible content and a transparent background: {entry['id']}"
                if group in ("npcs", "monsters"):
                    assert native_sprite_size(image.size), "Portraits require native 1024×1536 or higher"
                    histogram = image.getchannel("A").histogram()
                    assert sum(histogram[32:]) * 100 >= image.width * image.height, "Portraits require substantial visible artwork"
            if group in ("npcs", "monsters"):
                source_digest = validate_sprite_provenance(root, entry)
                assert source_digest not in sprite_sources, "One source must not count as several originals"
                sprite_sources.add(source_digest)
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
        if "random_event" in node:
            assert node["random_event"] is True and "choices" in node, "Chance events need alternatives"
            alternatives = node["choices"]
            assert len(alternatives) >= 2 and len({c["next"] for c in alternatives}) == len(alternatives)
            assert all(not set(c) & {"effects", "requires"} for c in alternatives), "Chance does not award skills or gate rights"
        if "effect" in node:
            assert node["effect"] in {"lanterns", "rain", "reed_light", "bell", "qi", "first_trace", "paired_trace", "second_pair_trace", "storm_discharge", "snow", "mist", "dust", "heat_haze", "embers", "petals", "sea_spray", "none"}
        if "effects" in node:
            assert isinstance(node["effects"], list) and 1 <= len(node["effects"]) <= 3
            assert len(set(node["effects"])) == len(node["effects"])
            assert set(node["effects"]) <= {"lanterns", "rain", "reed_light", "bell", "qi", "first_trace", "paired_trace", "second_pair_trace", "storm_discharge", "snow", "mist", "dust", "heat_haze", "embers", "petals", "sea_spray", "none"}
        if "cast" in node:
            assert isinstance(node["cast"], list) and 1 <= len(node["cast"]) <= 3
            assert len(set(node["cast"])) == len(node["cast"])
            assert node["actor"] in node["cast"] and set(node["cast"]) <= actors
        if "earned" in node:
            assert "choices" not in node, "Completed practice belongs after decisions"
            assert isinstance(node["earned"], dict) and node["earned"]
            assert all(stat in STAT_KEYS and type(value) is int and 0 < value <= 10
                       for stat, value in node["earned"].items())
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
    words = authored_word_count(story)
    report = delivery_report(world, words, len(story["nodes"]))
    progress = json.loads((root / "docs/CULTIVATION_PROGRESS.json").read_text())
    report["cultivation_rewrite"] = validate_delivery(progress, story)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-complete", action="store_true",
                        help="Require >1 million words, 500 human sprites, 501 beasts, and all background quotas")
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
