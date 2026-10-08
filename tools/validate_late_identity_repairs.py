"""Authenticate one Tuo Yin identity defect across two closing passages."""
import argparse
import json
import pathlib
import subprocess

from tools.story_data import load_story

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = "0fe9938bf765611b3fe9d31c747fec6067346620"
BOOK = "data/books/book_xvi_desert_24.json"
AUDIT = "docs/LATE_IDENTITY_REPAIRS_20261008.json"
REPLACEMENTS = {
    "desert_p24_002": ("receipt himself.", "receipt herself."),
    "desert_p24_rejoin": ("returned to his own household", "returned to her own household"),
}


def validate(root=ROOT, verify_source=False):
    root = pathlib.Path(root)
    audit = json.loads((root / AUDIT).read_text(encoding="utf-8"))
    book = json.loads((root / BOOK).read_text(encoding="utf-8"))
    assert audit["source_commit"] == SOURCE and audit["source_path"] == BOOK
    assert audit["requested_plot_holes"] == 1000
    assert audit["confirmed_underlying_defects"] == len(audit["defects"]) == 1
    assert audit["affected_source_passages"] == len(audit["repairs"]) == 2
    assert audit["target_met"] is False and audit["displayed_word_delta"] == 0
    assert {repair["node_id"] for repair in audit["repairs"]} == set(REPLACEMENTS)
    defect = audit["defects"][0]
    assert defect["classification"] == "character_identity_contradiction"
    assert set(defect["affected_node_ids"]) == set(REPLACEMENTS)
    assert len(defect["evidence"]) == 3
    assert "Her scarf" in defect["evidence"][0]["node"]["text"]
    assert "her clinician's review" in defect["evidence"][1]["node"]["text"]
    assert "Tuo said she had spent years" in defect["evidence"][2]["node"]["text"]
    for repair in audit["repairs"]:
        node_id = repair["node_id"]
        assert repair["source_path"] == BOOK
        before, after = repair["before"], repair["after"]
        old, new = REPLACEMENTS[node_id]
        assert before["text"].count(old) == 1
        assert after["text"] == before["text"].replace(old, new)
        assert book["nodes"][node_id] == after
        assert {k: v for k, v in before.items() if k != "text"} == {
            k: v for k, v in after.items() if k != "text"}, "Pronoun repair changed mechanics"
        assert len(after["text"].split()) - len(before["text"].split()) == repair["displayed_word_delta"] == 0
    prior = audit["historical_overlap"]
    assert len(prior) == len({entry["path"] for entry in prior}) == 25
    assert all(entry["matching_target_ids"] == [] for entry in prior)
    campaign = load_story(root)
    assert all(campaign["nodes"][repair["node_id"]] == repair["after"]
               for repair in audit["repairs"])

    if verify_source:
        cache = {}

        def source_raw(path):
            if path not in cache:
                cache[path] = subprocess.run(
                    ["git", "show", SOURCE + ":" + path], cwd=root,
                    check=True, capture_output=True, text=True).stdout
            return cache[path]

        def source_sha(path):
            return subprocess.run(
                ["git", "rev-parse", SOURCE + ":" + path], cwd=root,
                check=True, capture_output=True, text=True).stdout.strip()

        original = json.loads(source_raw(BOOK))
        assert source_sha(BOOK) == audit["source_file_sha"]
        for repair in audit["repairs"]:
            assert original["nodes"][repair["node_id"]] == repair["before"], "Incorrect source anchor"
        for evidence in defect["evidence"]:
            original_evidence = json.loads(source_raw(evidence["source_path"]))
            assert original_evidence["nodes"][evidence["node_id"]] == evidence["node"], "Incorrect corroborating source"
        for entry in prior:
            assert source_sha(entry["path"]) == entry["sha"]
            assert not any(node_id in source_raw(entry["path"])
                           for node_id in REPLACEMENTS), "Previously audited target"

    return {"confirmed_new_underlying_defects": 1, "affected_source_passages": 2,
            "displayed_word_delta": 0, "previous_audits_checked": 25,
            "requested_repairs": 1000, "target_met": False,
            "source_verified": verify_source}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-source", action="store_true")
    args = parser.parse_args()
    print(json.dumps(validate(verify_source=args.verify_source), indent=2))
