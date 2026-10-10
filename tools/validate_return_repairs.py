"""Validate the timetable repair against its published source and current prose."""
import argparse
import json
import pathlib
import subprocess

from .story_data import load_story
from .validate_continuation_audits import (
    normalize_audit, story_node_index, validate_documents,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
AUDIT = "docs/RETURN_REPAIRS_20261009.json"
SOURCE = "9461af86a503a358f356c628e30c3a721471f920"


def validate(root=ROOT, verify_source=False):
    root = pathlib.Path(root)
    document = json.loads((root / AUDIT).read_text(encoding="utf-8"))
    normalized = normalize_audit(document)
    if normalized["source_base"] != SOURCE:
        raise ValueError("Repair source must remain the published campaign")
    if len(normalized["repairs"]) != 1:
        raise ValueError("Count one timetable contradiction, not two passages")
    current = story_node_index(root)
    report = validate_documents([document], current, expected_source_base=SOURCE)
    expected = {"mortal_005", "mortal_018"}
    passages = normalized["repairs"][0]["passages"]
    if {item["node_id"] for item in passages} != expected:
        raise ValueError("Preserve both advertised timetable corrections")
    story = load_story(root)
    proof = document["repairs"][0]["evidence"]
    if {item["node_id"] for item in proof} != {
        "mortal_019", "mortal_rejoin_005", "mortal_rejoin_006",
        "mortal_rejoin_007", "mortal_rejoin_008",
    }:
        raise ValueError("Preserve the actual elapsed-time and recovered-award evidence")
    for item in proof:
        if current.get(item["node_id"]) != {"path": item["path"], "text": item["text"]}:
            raise ValueError("Stale timetable evidence")
    if "in eight weeks" not in passages[0]["before"]:
        raise ValueError("Record the contradicted announced wait")
    if "eight weeks away" not in passages[1]["before"]:
        raise ValueError("Record the second announced wait")
    if any("in eight weeks" in item["after"] or "eight weeks away" in item["after"]
           for item in passages):
        raise ValueError("The old fixed examination delay must be corrected")
    if "fifth week" not in story["nodes"]["mortal_018"]["text"]:
        raise ValueError("Keep the readiness-dependent first-check timetable visible")
    report["source_prose_checked"] = False
    if verify_source:
        cache = {}
        for item in [*passages, *proof]:
            path = item["path"]
            if path not in cache:
                try:
                    data = subprocess.run(
                        ["git", "show", f"{SOURCE}:{path}"], cwd=root,
                        check=True, capture_output=True, text=True,
                    ).stdout
                except subprocess.CalledProcessError as error:
                    raise ValueError(f"Fetch source {SOURCE} before source review") from error
                cache[path] = json.loads(data)["nodes"]
            node = cache[path].get(item["node_id"])
            expected_text = item.get("before", item.get("text"))
            if node is None or node.get("text") != expected_text:
                raise ValueError(f"Unauthenticated source passage: {item['node_id']}")
        report["source_prose_checked"] = True
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-source", action="store_true")
    args = parser.parse_args(argv)
    report = validate(verify_source=args.verify_source)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
