"""Validate reference cultivation canon and authored realm metadata."""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
REALM_FIELDS = ("mechanism", "admission", "practice", "breakthrough", "capabilities",
                "limits", "failure", "recovery", "span")


def validate_progress(canon, story):
    realms = {}
    for realm in canon["realms"]:
        identifier = realm["id"]
        if identifier in realms:
            raise ValueError(f"Duplicate cultivation realm: {identifier}")
        stages = realm["stages"]
        if not stages or len(stages) != len(set(stages)):
            raise ValueError(f"Empty or duplicate stages: {identifier}")
        if any(not isinstance(stage, str) or not stage.strip() for stage in stages):
            raise ValueError(f"Invalid stage: {identifier}")
        if any(not isinstance(realm.get(field), str) or not realm[field].strip()
               for field in REALM_FIELDS):
            raise ValueError(f"Incomplete cultivation realm: {identifier}")
        realms[identifier] = set(stages)
    if canon["protagonist"]["starting_realm"] not in realms:
        raise ValueError("Unknown protagonist starting realm")
    for identifier, node in story["nodes"].items():
        if "cultivation" not in node:
            continue
        progress = node["cultivation"]
        if not isinstance(progress, dict):
            raise ValueError(f"Invalid cultivation progress: {identifier}")
        realm = progress.get("realm")
        if realm not in realms or progress.get("stage") not in realms[realm]:
            raise ValueError(f"Unknown cultivation realm or stage: {identifier}")
    return realms


def load_canon(root=ROOT):
    return json.loads((pathlib.Path(root) / "data/cultivation.json").read_text(encoding="utf-8"))

def validate_delivery(progress, story):
    """Recompute manuscript credit from uniquely identified playable prose."""
    identifiers = progress["rewrite_scene_ids"]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("Duplicate rewrite scene credit")
    if not set(identifiers) <= set(story["nodes"]):
        raise ValueError("Unknown rewrite scene credit")
    words = lambda node: len(node["text"].split())
    total = sum(words(node) for node in story["nodes"].values())
    rewritten = sum(words(story["nodes"][identifier]) for identifier in identifiers)
    expected = {
        "displayed_scenes": len(story["nodes"]),
        "displayed_words": total,
        "rewrite_scenes": len(identifiers),
        "rewrite_words": rewritten,
        "inherited_words": total - rewritten,
        "remaining_displayed_words": max(0, progress["strict_word_target"] - total),
        "remaining_rewrite_words": max(0, progress["strict_word_target"] - rewritten),
    }
    for field, actual in expected.items():
        if progress.get(field) != actual:
            raise ValueError(f"Stale manuscript accounting: {field}")
    if progress["strict_word_target"] != 1000001:
        raise ValueError("Preserve the strict million-plus manuscript target")
    return expected
