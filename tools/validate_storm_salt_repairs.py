"""Authenticate thirteen newly deferred storm/salt rewards against fixed source."""
import argparse
import json
import pathlib
import subprocess
from collections import Counter
from tools.story_data import load_story, authored_word_count

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE_BASE = "c90102c720c0fd97fe31559851c57ee38e976d55"
AUDIT = "docs/STORM_SALT_REPAIRS_20261006.json"


def destinations(node):
    return ([node[field] for field in ("next", "continuation") if field in node]
            + [choice["next"] for choice in node.get("choices", [])])


def validate_campaign(audit, story):
    repairs = audit["repairs"]
    assert audit["source_base"] == SOURCE_BASE, "Use the independently fixed source"
    assert audit["repair_sites"] == len(repairs) == 13
    assert audit["root_causes"] == 1 and audit["save_rule_revision"] == 3
    assert audit["requested_repair_sites"] == 100
    assert audit["unfulfilled_requested_repair_sites"] == 87
    assert len({r["id"] for r in repairs}) == 13
    assert len({(r["node_id"], r["choice_index"]) for r in repairs}) == 13
    assert len({r["completion_node"] for r in repairs}) == 13
    nodes = story["nodes"]
    incoming = Counter(target for node in nodes.values() for target in destinations(node))
    for repair in repairs:
        choice = nodes[repair["node_id"]]["choices"][repair["choice_index"]]
        assert choice == repair["after"] and "effects" not in choice, "No selection reward"
        assert {k: v for k, v in repair["before"].items() if k != "effects"} == choice
        assert repair["before"]["effects"] == repair["earned"]
        branch = repair["branch"]
        assert branch and len(set(branch)) == len(branch)
        assert branch[0] == choice["next"] and branch[-1] == repair["completion_node"]
        completion = nodes[branch[-1]]
        assert completion["text"] == repair["completion_text"]
        assert completion["earned"] == repair["earned"]
        assert completion["legacy_credit"] == {
            "choice_node": repair["node_id"], "branch_nodes": branch, "rules_before": 3}
        assert repair["legacy_rules_before"] == 3
        assert "choices" not in completion and len(destinations(completion)) == 1
        for first, second in zip(branch, branch[1:]):
            assert destinations(nodes[first]) == [second]
            assert "earned" not in nodes[first], "Credit must await the final passage"
        assert all(incoming[key] == 1 for key in branch), "Reward work must stay exclusive"
        for other in nodes[repair["node_id"]]["choices"]:
            if other != choice:
                assert other["next"] not in branch
    return {"new_repair_sites": 13, "root_causes": 1, "save_rule_revision": 3,
            "requested_repair_sites": 100, "unfulfilled_requested_repair_sites": 87,
            "words": authored_word_count(story), "word_target": 2000000,
            "remaining_words": max(0, 2000000 - authored_word_count(story))}


def validate(root=ROOT, verify_source=False):
    root = pathlib.Path(root)
    audit = json.loads((root / AUDIT).read_text(encoding="utf-8"))
    story = load_story(root)
    report = validate_campaign(audit, story)
    earlier_sites = set()
    earlier_completions = set()
    for path in ("docs/CONTINUITY_REPAIRS_20261004.json",
                 "docs/NARRATIVE_REPAIRS_20261005.json",
                 "docs/ADDITIONAL_REPAIRS_20261005.json"):
        previous = json.loads((root / path).read_text(encoding="utf-8"))
        for repair in previous["repairs"]:
            if "choice_index" in repair:
                earlier_sites.add((repair["node_id"], repair["choice_index"]))
            if repair.get("completion_node"):
                earlier_completions.add(repair["completion_node"])
    assert not ({(r["node_id"], r["choice_index"]) for r in audit["repairs"]} & earlier_sites)
    assert not ({r["completion_node"] for r in audit["repairs"]} & earlier_completions)
    if verify_source:
        sources = {}
        for repair in audit["repairs"]:
            for path in (repair["path"], repair["completion_path"]):
                if path not in sources:
                    result = subprocess.run(
                        ["git", "show", SOURCE_BASE + ":" + path], cwd=root,
                        capture_output=True, text=True, check=True)
                    sources[path] = json.loads(result.stdout)
            original = sources[repair["path"]]["nodes"]
            assert original[repair["node_id"]]["choices"][repair["choice_index"]] == repair["before"]
            old_completion = sources[repair["completion_path"]]["nodes"][repair["completion_node"]]
            assert old_completion["text"] == repair["completion_text"]
            assert "earned" not in old_completion and "legacy_credit" not in old_completion
            for first, second in zip(repair["branch"], repair["branch"][1:]):
                assert destinations(original[first]) == [second]
    report["source_verified"] = verify_source
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-source", action="store_true")
    args = parser.parse_args()
    print(json.dumps(validate(verify_source=args.verify_source), indent=2))
