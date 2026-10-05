"""Authenticate deferred growth and harder desert branches against their source."""
import argparse
import json
import pathlib
import subprocess
from tools.story_data import load_story, authored_word_count

ROOT = pathlib.Path(__file__).resolve().parents[1]
AUDIT = "docs/NARRATIVE_REPAIRS_20261005.json"


def validate(root=ROOT, verify_source=False):
    root = pathlib.Path(root)
    audit = json.loads((root / AUDIT).read_text(encoding="utf-8"))
    story = load_story(root)
    files, source_files = {}, {}
    def current(path):
        if path not in files:
            files[path] = json.loads((root / path).read_text(encoding="utf-8"))
        return files[path]
    def source(path):
        if path not in source_files:
            result = subprocess.run(
                ["git", "show", audit["source_base"] + ":" + path], cwd=root,
                check=True, capture_output=True, text=True)
            source_files[path] = json.loads(result.stdout)
        return source_files[path]
    repairs = audit["repairs"]
    assert len(repairs) == audit["repair_sites"] == 101
    assert len({r["id"] for r in repairs}) == 101
    assert len({(r["node_id"], r["choice_index"]) for r in repairs}) == 101
    assert len({r["completion_node"] for r in repairs}) == 101
    for repair in repairs:
        choice = current(repair["path"])["nodes"][repair["node_id"]]["choices"][repair["choice_index"]]
        assert choice == repair["after"] and "effects" not in choice
        assert repair["before"]["effects"] == repair["earned"]
        assert {k: v for k, v in repair["before"].items() if k != "effects"} == choice
        end = current(repair["completion_path"])["nodes"][repair["completion_node"]]
        assert end["text"] == repair["completion_text"]
        assert end["earned"] == repair["earned"]
        assert end["legacy_credit"] == {
            "choice_node": repair["node_id"], "branch_nodes": repair["branch"]}
        assert repair["branch"][0] == choice["next"]
        assert repair["branch"][-1] == repair["completion_node"]
        for first, second in zip(repair["branch"], repair["branch"][1:]):
            node = story["nodes"][first]
            assert node.get("next", node.get("continuation")) == second
            assert "earned" not in node
        assert "choices" not in end and "next" in end
        if verify_source:
            assert source(repair["path"])["nodes"][repair["node_id"]]["choices"][repair["choice_index"]] == repair["before"]
            old_end = source(repair["completion_path"])["nodes"][repair["completion_node"]]
            assert old_end["text"] == end["text"] and "earned" not in old_end
    locations = audit["locations"]
    assert len(locations) == 70
    assert len({r["node_id"] for r in locations}) == len(locations)
    for repair in locations:
        node = current(repair["path"])["nodes"][repair["node_id"]]
        assert node["background"] == repair["after"]
        if verify_source:
            assert source(repair["path"])["nodes"][repair["node_id"]]["background"] == repair["before"]
    assert len(audit["decisions"]) == 6
    for decision in audit["decisions"]:
        nodes = current(decision["path"])["nodes"]
        assert nodes[decision["anchor"]]["next"] == decision["decision_id"]
        point = nodes[decision["decision_id"]]
        assert [c["next"] for c in point["choices"]] == decision["branches"]
        assert len(point["choices"]) == 3
        assert sum(not c.get("requires") for c in point["choices"]) >= 2
        assert all(not c.get("effects") for c in point["choices"])
        assert len({nodes[k]["text"] for k in decision["branches"]}) == 3
        for branch in decision["branches"]:
            assert nodes[branch]["next"] == decision["rejoin"]
            assert "earned" not in nodes[branch]
        if verify_source:
            old = source(decision["path"])["nodes"]
            assert old[decision["anchor"]]["next"] == decision["before_next"]
            assert decision["decision_id"] not in old
    assert authored_word_count(story) > 1_000_000
    return {"causality_sites": len(repairs), "location_sites": len(locations),
            "new_decisions": 6, "new_consequences": 18,
            "words": authored_word_count(story), "scenes": len(story["nodes"]),
            "source_verified": verify_source}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-source", action="store_true")
    args = parser.parse_args()
    print(json.dumps(validate(verify_source=args.verify_source), indent=2))
