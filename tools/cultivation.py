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
