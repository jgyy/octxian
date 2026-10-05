"""Authenticate the second 100-site causality revision and its save threshold."""
import argparse
import json
import pathlib
import subprocess
from tools.story_data import load_story, authored_word_count

ROOT = pathlib.Path(__file__).resolve().parents[1]
AUDIT = "docs/ADDITIONAL_REPAIRS_20261005.json"


def validate(root=ROOT, verify_source=False):
    root = pathlib.Path(root)
    audit = json.loads((root / AUDIT).read_text(encoding="utf-8"))
    story = load_story(root)
    old_audit = json.loads((root / "docs/NARRATIVE_REPAIRS_20261005.json").read_text())
    repairs = audit["repairs"]
    assert audit["repair_sites"] == len(repairs) == 100
    assert audit["save_rule_revision"] == 2
    assert len({r["id"] for r in repairs}) == 100
    assert len({(r["node_id"], r["choice_index"]) for r in repairs}) == 100
    assert len({r["completion_node"] for r in repairs}) == 100
    assert not ({(r["node_id"], r["choice_index"]) for r in repairs}
                & {(r["node_id"], r["choice_index"]) for r in old_audit["repairs"]})
    assert not ({r["completion_node"] for r in repairs}
                & {r["completion_node"] for r in old_audit["repairs"]})
    source_files = {}

    def source(path):
        if path not in source_files:
            result = subprocess.run(
                ["git", "show", audit["source_base"] + ":" + path], cwd=root,
                capture_output=True, text=True, check=True)
            source_files[path] = json.loads(result.stdout)
        return source_files[path]

    for repair in repairs:
        node = story["nodes"][repair["node_id"]]
        option = node["choices"][repair["choice_index"]]
        assert option == repair["after"] and "effects" not in option
        assert {k: v for k, v in repair["before"].items() if k != "effects"} == option
        assert repair["before"]["effects"] == repair["earned"]
        completion = story["nodes"][repair["completion_node"]]
        assert completion["text"] == repair["completion_text"]
        assert completion["earned"] == repair["earned"]
        assert completion["legacy_credit"] == {
            "choice_node": repair["node_id"], "branch_nodes": repair["branch"],
            "rules_before": 2}
        assert repair["legacy_rules_before"] == 2
        assert repair["branch"][0] == option["next"]
        assert repair["branch"][-1] == repair["completion_node"]
        assert "next" in completion and "choices" not in completion
        for first, second in zip(repair["branch"], repair["branch"][1:]):
            passage = story["nodes"][first]
            assert passage["next"] == second and "earned" not in passage
        if verify_source:
            old = source(repair["path"])["nodes"][repair["node_id"]]
            assert old["choices"][repair["choice_index"]] == repair["before"]
            old_completion = source(repair["completion_path"])["nodes"][repair["completion_node"]]
            assert old_completion["text"] == repair["completion_text"]
            assert "earned" not in old_completion
    for repair in old_audit["repairs"]:
        completion = story["nodes"][repair["completion_node"]]
        assert completion["legacy_credit"].get("rules_before", 1) == 1
    return {"additional_causality_sites": len(repairs),
            "combined_causality_sites": len(repairs) + len(old_audit["repairs"]),
            "save_rule_revision": 2, "words": authored_word_count(story),
            "scenes": len(story["nodes"]), "source_verified": verify_source}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-source", action="store_true")
    args = parser.parse_args()
    print(json.dumps(validate(verify_source=args.verify_source), indent=2))
