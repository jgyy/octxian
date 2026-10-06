"""Authenticate the evidenced branch repair and inspect authored consequence delivery."""
import argparse
import json
import pathlib
import subprocess

from tools.story_data import authored_word_count, load_story

ROOT = pathlib.Path(__file__).resolve().parents[1]
AUDIT_PATH = "docs/CHOICE_CONSEQUENCE_AUDIT_20261006.json"


def validate(root=ROOT, verify_source=False):
    root = pathlib.Path(root)
    story = load_story(root)
    audit = json.loads((root / AUDIT_PATH).read_text())
    source_cache = {}

    def source(path):
        if path not in source_cache:
            result = subprocess.run(
                ["git", "show", audit["source_commit"] + ":" + path],
                cwd=root, check=True, capture_output=True, text=True)
            source_cache[path] = json.loads(result.stdout)
        return source_cache[path]

    assert audit["scope"]["requested_plot_hole_target"] == 1000
    assert audit["scope"]["confirmed_plot_holes"] == len(audit["confirmed_repairs"])
    assert not audit["scope"]["target_verified"], "Do not turn reviewed sites into invented defects"
    for repair in audit["confirmed_repairs"]:
        assert repair["classification"] == "confirmed_inconsistent_branch_fact"
        assert story["nodes"][repair["scene_id"]] == repair["after"]
        assert repair["before"]["text"] != repair["after"]["text"]
        if verify_source:
            original = source(repair["source_path"])["nodes"]
            assert original[repair["scene_id"]] == repair["before"], "Repair source is stale"
            evidence = repair["evidence"]
            assert original[evidence["seed_only_result_scene"]]["text"] == evidence["seed_only_result"]
            assert original[evidence["shared_exclusion_scene"]]["text"] == evidence["shared_exclusion"]

    callbacks = json.loads((root / audit["new_book_path"]).read_text())["nodes"]
    visited, routed = set(), 0
    for item in audit["consequence_improvements"]:
        assert item["classification"] == "missing_downstream_consequence"
        assert story["nodes"][item["decision"]] == item["decision_before"]
        assert story["nodes"][item["gate"]] == item["gate_after"]
        assert item["gate_after"]["next"] == item["gate_before"]["next"] == item["fallback"]
        assert item["gate_after"]["text"] == item["gate_before"]["text"]
        if verify_source:
            assert source(item["source_path"])["nodes"][item["gate"]] == item["gate_before"]
            assert source(item["decision_source_path"])["nodes"][item["decision"]] == item["decision_before"]
        selections = {choice["next"] for choice in item["decision_before"]["choices"]}
        assert {route["selected"] for route in item["gate_after"]["routes"]} == selections
        site_scenes = set()
        for route in item["gate_after"]["routes"]:
            assert route["decision"] == item["decision"]
            cursor, branch = route["next"], set()
            while cursor != item["fallback"]:
                assert cursor in callbacks and cursor not in branch
                branch.add(cursor)
                scene = callbacks[cursor]
                assert not set(scene) & {"earned", "choices", "routes", "ending"}
                assert scene["cultivation"] == item["gate_before"]["cultivation"]
                cursor = scene["next"]
            assert len(branch) == 3, "Each actual consequence must have its complete three-passage followthrough"
            assert not site_scenes & branch, "Selected callbacks must stay exclusive"
            site_scenes.update(branch)
            routed += 1
        assert site_scenes == set(item["callback_scene_ids"])
        visited.update(site_scenes)
    assert visited == set(callbacks)
    assert routed == audit["scope"]["selected_callback_routes"]
    assert len(callbacks) == audit["scope"]["new_callback_scenes"]
    assert len(audit["consequence_improvements"]) == audit["scope"]["gameplay_consequence_improvements"]

    if verify_source:
        root_source = source("data/story.json")
        originals = dict(root_source["nodes"])
        for path in root_source["books"]:
            originals.update(source(path)["nodes"])
        assert len(originals) == audit["scope"]["authored_scene_nodes_scanned"]
        assert sum("choices" in node and not node.get("random_event", False)
                   for node in originals.values()) == audit["scope"]["authored_decision_nodes_scanned"]

    words = authored_word_count(story)
    return {
        "source_commit": audit["source_commit"],
        "verified_new_plot_repairs": len(audit["confirmed_repairs"]),
        "requested_plot_repairs": 1000,
        "plot_repair_target_met": len(audit["confirmed_repairs"]) >= 1000,
        "consequence_improvements": len(audit["consequence_improvements"]),
        "selected_callback_routes": routed,
        "callback_words": sum(len(scene["text"].split()) for scene in callbacks.values()),
        "displayed_words": words,
        "word_target": 2000000,
        "remaining_words": max(0, 2000000 - words),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-source", action="store_true")
    args = parser.parse_args()
    print(json.dumps(validate(verify_source=args.verify_source), indent=2))
