"""Authenticate two current-source repairs and report the new continuation honestly."""
import argparse
import json
import pathlib
import subprocess

from tools.story_data import authored_word_count, load_story

ROOT = pathlib.Path(__file__).resolve().parents[1]
AUDIT = "docs/REED_CROSSING_REPAIRS_20261006.json"
SOURCE = "a8d6ddf1d7c73c77fc8c66be6932fab403269bfc"


def validate(root=ROOT, verify_source=False):
    root = pathlib.Path(root)
    audit = json.loads((root / AUDIT).read_text())
    assert audit["source_commit"] == SOURCE
    assert audit["requested_plot_holes"] == 1000
    assert audit["confirmed_underlying_defects"] == len(audit["repairs"]) == 2
    assert audit["affected_source_passages"] == 2 and audit["target_met"] is False
    assert len({r["root_cause"] for r in audit["repairs"]}) == 2
    story = load_story(root)
    sources = {}

    def source(path):
        if path not in sources:
            result = subprocess.run(
                ["git", "show", SOURCE + ":" + path], cwd=root,
                check=True, capture_output=True, text=True)
            sources[path] = json.loads(result.stdout)
        return sources[path]

    for repair in audit["repairs"]:
        assert repair["classification"] == "confirmed_continuity_defect"
        assert story["nodes"][repair["node_id"]] == repair["after"]
        assert repair["before"]["text"] != repair["after"]["text"]
        assert {k: v for k, v in repair["before"].items() if k != "text"} == {
            k: v for k, v in repair["after"].items() if k != "text"}
        if verify_source:
            assert source(repair["source_path"])["nodes"][repair["node_id"]] == repair["before"]
            for evidence in repair["evidence"]:
                assert source(evidence["source_path"])["nodes"][evidence["node_id"]] == evidence["node"]
    continuation = audit["continuation"]
    assert story["nodes"][continuation["node_id"]] == continuation["after"]
    assert continuation["after"] == {**continuation["before"], "continuation": "crossing_entry"}
    if verify_source:
        assert source(continuation["source_path"])["nodes"][continuation["node_id"]] == continuation["before"]
    book = json.loads((root / audit["new_book_path"]).read_text())
    assert set(book) == {"chapters", "characters", "nodes"}
    assert len(book["nodes"]) == 125
    assert all(node["cultivation"] == {"realm": "qi_gathering", "stage": "5: Four pairs"}
               for node in book["nodes"].values())
    assert all(len(node["text"].split()) <= 100 for node in book["nodes"].values())
    words = sum(len(node["text"].split()) for node in book["nodes"].values())
    assert words == 9109
    total = authored_word_count(story)
    return {"new_scenes": len(book["nodes"]), "new_displayed_words": words,
            "confirmed_plot_holes": 2, "requested_plot_holes": 1000,
            "plot_hole_target_met": False, "displayed_words": total,
            "remaining_words": max(0, 2000000 - total), "source_verified": verify_source}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-source", action="store_true")
    args = parser.parse_args()
    print(json.dumps(validate(verify_source=args.verify_source), indent=2))
