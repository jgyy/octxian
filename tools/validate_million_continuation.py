"""Verify the 101 source-anchored causal/transition repair sites and integration."""
import argparse
import json
import pathlib
import subprocess
from collections import deque

from tools.story_data import load_story, authored_word_count

ROOT = pathlib.Path(__file__).resolve().parents[1]


def validate(root=ROOT, verify_source=False):
    root = pathlib.Path(root)
    story = load_story(root)
    audit = json.loads((root / "docs/CONTINUITY_REPAIRS_20261004.json").read_text())
    assert len(audit["repairs"]) == 101
    assert len({r["id"] for r in audit["repairs"]}) == 101
    source_cache = {}
    def source(path):
        if path not in source_cache:
            result = subprocess.run(["git", "show", audit["source_base"] + ":" + path],
                                    cwd=root, check=True, capture_output=True, text=True)
            source_cache[path] = json.loads(result.stdout)
        return source_cache[path]
    completions = set()
    for repair in audit["repairs"]:
        node = story["nodes"][repair["node_id"]]
        if repair["category"] == "choice_causality":
            choice = node["choices"][repair["choice_index"]]
            assert choice == repair["after"], repair["id"] + ": stale choice anchor"
            assert "effects" not in choice, repair["id"] + ": premature reward"
            if verify_source:
                original = source(repair["path"])["nodes"][repair["node_id"]]
                assert original["choices"][repair["choice_index"]] == repair["before"]
            completion = repair["completion_node"]
            if completion is not None:
                assert completion not in completions, "Each completed task is credited once"
                completions.add(completion)
                end = story["nodes"][completion]
                assert end["text"] == repair["completion_text"]
                assert end["earned"] == repair["earned"]
                cursor, visited = choice["next"], set()
                while cursor != completion:
                    assert cursor not in visited, "Reward branch must reach actual completion"
                    visited.add(cursor)
                    assert "earned" not in story["nodes"][cursor]
                    cursor = story["nodes"][cursor]["next"]
        elif repair["category"] == "unfinished_closure":
            assert node["next"] == repair["after_next"]
            assert node["next"] in story["nodes"]
            if verify_source:
                assert source(repair["path"])["nodes"][repair["node_id"]]["next"] == repair["before_next"]
                missing = subprocess.run(["git", "cat-file", "-e",
                    audit["source_base"] + ":" + repair["added_path"]],
                    cwd=root, capture_output=True)
                assert missing.returncode != 0, "Closing sequence was missing at source"
        else:
            assert repair["category"] == "absent_continuation"
            assert node["continuation"] == repair["after_continuation"]
            if verify_source:
                assert "continuation" not in source(repair["path"])["nodes"][repair["node_id"]]
    assert len(completions) == 92
    seen, queue = set(), deque([story["start"]])
    while queue:
        key = queue.popleft()
        if key in seen:
            continue
        seen.add(key)
        node = story["nodes"][key]
        queue.extend(node[field] for field in ("next", "continuation") if field in node)
        queue.extend(c["next"] for c in node.get("choices", []))
    assert seen == set(story["nodes"]), "All integrated scenes must be reachable"
    assert authored_word_count(story) >= 1000001
    assert len(story["chapters"]) == 17
    for key in ("forest_24_005", "desert_p24_005", "archive_25_006"):
        choices = story["nodes"][key]["choices"]
        assert {k for c in choices for k in c.get("requires", {})} == {"qi", "trust", "insight", "resolve"}
        assert any(not c.get("requires") for c in choices), "Keep qualified support available"
        assert len({story["nodes"][c["next"]]["text"] for c in choices}) == len(choices)
    return {"repair_sites": 101, "completed_tasks": 92,
            "words": authored_word_count(story), "scenes": len(seen)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-source", action="store_true")
    args = parser.parse_args()
    print(json.dumps(validate(verify_source=args.verify_source), indent=2))
