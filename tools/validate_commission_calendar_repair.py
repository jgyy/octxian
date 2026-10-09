"""Authenticate one existing commission-calendar contradiction; exclude mechanics from literary credit."""
import argparse
import json
import pathlib
import subprocess

from tools.story_data import load_story

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = "0fe9938bf765611b3fe9d31c747fec6067346620"
BOOK = "data/books/book_xxi_commissions.json"
AUDIT = "docs/COMMISSION_CONTINUITY_REPAIRS_20261008.json"
NODE = "commission_calendar_02"


def validate(root=ROOT, verify_source=False):
    root = pathlib.Path(root)
    audit = json.loads((root / AUDIT).read_text(encoding="utf-8"))
    book = json.loads((root / BOOK).read_text(encoding="utf-8"))
    assert audit["source_commit"] == SOURCE
    assert audit["source_book_path"] == BOOK
    assert audit["requested_plot_holes"] == 1000
    assert audit["confirmed_underlying_defects"] == len(audit["repairs"]) == 1
    assert audit["affected_source_passages"] == 1
    assert audit["target_met"] is False
    repair = audit["repairs"][0]
    assert repair["classification"] == "confirmed_continuity_defect"
    assert repair["source_path"] == BOOK and repair["node_id"] == NODE
    before, after = repair["before"], repair["after"]
    assert before["text"] != after["text"]
    assert book["nodes"][NODE] == after
    assert {k: v for k, v in before.items() if k != "text"} == {
        k: v for k, v in after.items() if k != "text"}, "Editorial repair changed mechanics"
    assert "She had accepted the appointment but had not attended it." in before["text"]
    assert "Where neither was documented, both headings stayed empty." in after["text"]
    delta = len(after["text"].split()) - len(before["text"].split())
    assert delta == repair["displayed_word_delta"] == audit["displayed_word_delta"] == 11
    words = sum(len(node["text"].split()) for node in book["nodes"].values())
    assert audit["book_words_before"] == 6931
    assert words == audit["book_words_after"] == 6942
    assert words - delta == audit["book_words_before"]
    assert repair["evidence"]
    mechanics = audit["mechanics"]
    assert len(mechanics) == 1 and mechanics[0]["classification"] == "engine_replay_defect"
    assert mechanics[0]["confirmed_literary_defect_credit"] == 0

    campaign = load_story(root)
    assert campaign["nodes"][NODE] == after
    current = "career_enrol_choice"
    decisions = {}
    selected = repair["actual_route_witness"]["selected_choices"]
    assert selected == {"career_enrol_choice": "career_independent_entry",
                        "career_next_choice": "career_home_01"}
    for _ in range(500):
        if current == NODE:
            break
        node = campaign["nodes"][current]
        if "choices" in node:
            target = selected[current]
            assert any(choice["next"] == target for choice in node["choices"])
            decisions[current] = target
        else:
            matches = [route["next"] for route in node.get("routes", [])
                       if decisions.get(route["decision"]) == route["selected"]]
            target = matches[0] if matches else node.get("next", node.get("continuation"))
        assert target in campaign["nodes"]
        current = target
    assert current == NODE and decisions == selected, "The actual independent/home witness must reach the shared calendar"

    if verify_source:
        cache = {}

        def source(path):
            if path not in cache:
                raw = subprocess.run(["git", "show", SOURCE + ":" + path], cwd=root,
                                     check=True, capture_output=True, text=True).stdout
                cache[path] = json.loads(raw)
            return cache[path]

        original = source(BOOK)
        assert original["nodes"][NODE] == before, "Incorrect exact source anchor"
        original_sha = subprocess.run(["git", "rev-parse", SOURCE + ":" + BOOK], cwd=root,
                                      check=True, capture_output=True, text=True).stdout.strip()
        assert original_sha == audit["source_book_blob_sha"]
        for evidence in repair["evidence"]:
            assert source(evidence["source_path"])["nodes"][evidence["node_id"]] == evidence["node"], "Incorrect corroborating source"
        engine_sha = subprocess.run(
            ["git", "rev-parse", SOURCE + ":" + mechanics[0]["source_path"]], cwd=root,
            check=True, capture_output=True, text=True).stdout.strip()
        assert engine_sha == mechanics[0]["source_blob_sha"]

    return {"confirmed_new_underlying_defects": 1, "separate_mechanics_repairs": 1,
            "mechanics_literary_credit": 0, "displayed_word_delta": delta,
            "current_book_words": words, "requested_repairs": 1000,
            "target_met": False, "source_verified": verify_source}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-source", action="store_true")
    args = parser.parse_args()
    print(json.dumps(validate(verify_source=args.verify_source), indent=2))
