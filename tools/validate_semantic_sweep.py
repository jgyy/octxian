"""Authenticate the six distinct current-source continuity repairs without inflating counts."""
import argparse
import json
import pathlib
import subprocess
from tools.story_data import load_story

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = "1bb309ba5cc8621673a041e80b91cf38414af8cb"

def validate(root=ROOT, verify_source=False):
    root = pathlib.Path(root)
    late = json.loads((root / "docs/LATE_CONTINUITY_AUDIT_20261006.json").read_text())
    salt = json.loads((root / "docs/audits/vii_xii_salt_purchase_volume_20261006.json").read_text())
    coverage = json.loads((root / "docs/SEMANTIC_CONTINUITY_REVIEW_20261006.json").read_text())
    assert late["source_commit"] == salt["audited_head"] == SOURCE
    cases = late["confirmed_defects"]
    ids = [case["id"] for case in cases] + [case["id"] for case in salt["defects"]]
    assert len(ids) == len(set(ids)) == 6, "Count the shared salt discovery once"
    assert late["scope"]["confirmed_underlying_defects"] == 5
    assert salt["defect_count"] == 1
    assert late["scope"]["requested_plot_hole_target"] == 1000
    assert late["scope"]["target_verified"] is False
    records = [repair for case in cases for repair in case["repairs"]]
    for case in cases:
        assert case["affected_source_sites"] == len(case["repairs"])
    for case in salt["defects"]:
        records.append({"path": case["source_path"], "node_id": case["node"],
                        "before": case["before_text"], "after": case["after_text"]})
    assert len(records) == len({(r["path"], r["node_id"]) for r in records}) == 27
    story = load_story(root)
    source_cache = {}
    current_cache = {}
    def before_book(path):
        if path not in source_cache:
            raw = subprocess.run(["git", "show", SOURCE + ":" + path], cwd=root,
                                 check=True, capture_output=True, text=True).stdout
            source_cache[path] = json.loads(raw)
        return source_cache[path]
    def current_book(path):
        if path not in current_cache:
            current_cache[path] = json.loads((root / path).read_text())
        return current_cache[path]
    delta = 0
    for record in records:
        path, node_id = record["path"], record["node_id"]
        current = current_book(path)["nodes"][node_id]
        assert current["text"] == record["after"], "Stale current repair: " + node_id
        assert len(current["text"].split()) <= 100
        assert record["before"] != record["after"]
        assert story["nodes"][node_id] == current
        delta += len(record["after"].split()) - len(record["before"].split())
        if verify_source:
            original = before_book(path)["nodes"][node_id]
            assert original["text"] == record["before"], "Incorrect source anchor: " + node_id
            assert {k:v for k,v in original.items() if k != "text"} == {
                k:v for k,v in current.items() if k != "text"}, "Prose repair changed mechanics"
    if verify_source:
        for case in cases:
            for evidence in case["evidence"]:
                assert before_book(evidence["path"])["nodes"][evidence["node_id"]]["text"] == evidence["text"]
        for case in salt["defects"]:
            for evidence in case["evidence"]:
                assert before_book(case["source_path"])["nodes"][evidence["node"]]["text"] == evidence["text"]
    assert delta == 2
    assert "thirty-nine accepted jars" in story["nodes"]["salt_purchase_003"]["text"]
    assert 40 - 1 == 39 and 39 + 40 + 40 + 1 == 120
    assert 1185 + 120 == 1305 and 1305 - 5 == 1300
    assert "One loose cover" in story["nodes"]["salt_purchase_002"]["text"]
    assert "those ten litres" in story["nodes"]["salt_purchase_002"]["text"]
    assert story["nodes"]["desert_p24_role_resolve"]["earned"] == {"resolve": 2}
    report = {"confirmed_new_underlying_defects": 6, "affected_source_passages": 27,
              "displayed_word_delta": delta, "requested_repairs": 1000, "target_met": False,
              "source_verified": verify_source}
    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-source", action="store_true")
    args = parser.parse_args()
    print(json.dumps(validate(verify_source=args.verify_source), indent=2))
