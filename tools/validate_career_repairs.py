"""Authenticate two source contradictions and keep a circuit clarification out of defect counts."""
import argparse
import json
import pathlib
import subprocess

from tools.story_data import load_story

ROOT = pathlib.Path(__file__).resolve().parents[1]
AUDIT = "docs/CAREER_CONTINUITY_REPAIRS_20261007.json"
BOOK = "data/books/book_xix_reed_crossing.json"
SOURCE = "659f6c413867a3c7d5857e4b89c4f3aae1f39ae8"
DEFECT_IDS = {"crossing_linen_04", "crossing_evidence_rod_01"}
CLARIFIED_IDS = {"crossing_qi_03", "crossing_rise_03"}


def records(audit):
    return audit["repairs"] + [
        repair for case in audit["clarifications"] for repair in case["repairs"]]


def validate_records(book, audit, canon, source_book=None, source_canon=None):
    assert audit["source_commit"] == SOURCE
    assert audit["source_book_path"] == BOOK
    assert audit["requested_plot_holes"] == 1000
    assert audit["confirmed_underlying_defects"] == len(audit["repairs"]) == 2
    assert audit["affected_source_passages"] == 2
    assert audit["clarification_cases"] == len(audit["clarifications"]) == 1
    assert audit["clarified_source_passages"] == 2
    assert audit["total_changed_source_passages"] == 4
    assert audit["target_met"] is False
    assert {r["node_id"] for r in audit["repairs"]} == DEFECT_IDS
    assert len({r["root_cause"] for r in audit["repairs"]}) == 2
    assert all(r["classification"] == "confirmed_continuity_defect"
               for r in audit["repairs"])
    case = audit["clarifications"][0]
    assert case["classification"] == "terminology_clarification"
    assert case["confirmed_defect_credit"] == 0
    assert {r["node_id"] for r in case["repairs"]} == CLARIFIED_IDS
    all_records = records(audit)
    assert len(all_records) == len({r["node_id"] for r in all_records}) == 4
    assert set(book) == {"chapters", "characters", "nodes"}
    assert len(book["nodes"]) == 125
    delta = 0
    for repair in all_records:
        node_id = repair["node_id"]
        assert repair["source_path"] == BOOK
        before, after = repair["before"], repair["after"]
        assert book["nodes"][node_id] == after, "Stale current repair: " + node_id
        assert before["text"] != after["text"]
        assert {k: v for k, v in before.items() if k != "text"} == {
            k: v for k, v in after.items() if k != "text"}, "Prose repair changed mechanics"
        assert len(after["text"].split()) <= 100
        change = len(after["text"].split()) - len(before["text"].split())
        assert change == repair["displayed_word_delta"]
        delta += change
        if source_book is not None:
            assert source_book["nodes"][node_id] == before, "Incorrect source anchor: " + node_id
        assert repair["evidence"]
        for evidence in repair["evidence"]:
            assert evidence["source_path"] == BOOK
            if source_book is not None:
                assert source_book["nodes"][evidence["node_id"]] == evidence["node"], (
                    "Incorrect corroborating evidence: " + evidence["node_id"])
    assert delta == audit["displayed_word_delta"] == 9
    words = sum(len(n["text"].split()) for n in book["nodes"].values())
    assert audit["book_words_before"] == 9109
    assert words == audit["book_words_after"] == 9118
    assert words - delta == audit["book_words_before"]
    assert "From the upper-path waiting room," in book["nodes"]["crossing_linen_04"]["text"]
    assert "after the second observation" in book["nodes"]["crossing_evidence_rod_01"]["text"]
    assert "separate from the two ranges" in book["nodes"]["crossing_evidence_rod_01"]["text"]
    assert "external reference-frame circuit" in book["nodes"]["crossing_qi_03"]["text"]
    assert "bounded reference trace" in book["nodes"]["crossing_rise_03"]["text"]
    assert all(book["nodes"][node_id]["cultivation"] == {
        "realm": "qi_gathering", "stage": "5: Four pairs"} for node_id in DEFECT_IDS | CLARIFIED_IDS)
    evidence = case["canon_evidence"]
    assert evidence["source_path"] == "data/cultivation.json"
    realm = next(r for r in canon["realms"] if r["id"] == "qi_gathering")
    assert realm == evidence["realm"]
    assert realm["stages"][4] == "5: Four pairs"
    assert realm["stages"][6] == "7: Small circuit"
    if source_canon is not None:
        assert next(r for r in source_canon["realms"] if r["id"] == "qi_gathering") == realm
    historical = audit["historical_assertion_check"]
    assert len(historical) == len({r["path"] for r in historical}) == 23
    assert all(r["matching_targets"] == [] for r in historical)
    return {"confirmed_new_underlying_defects": 2, "affected_source_passages": 2,
            "clarification_cases": 1, "clarified_source_passages": 2,
            "displayed_word_delta": delta, "current_book_words": words,
            "requested_repairs": 1000, "target_met": False}


def validate(root=ROOT, verify_source=False):
    root = pathlib.Path(root)
    audit = json.loads((root / AUDIT).read_text(encoding="utf-8"))
    book = json.loads((root / BOOK).read_text(encoding="utf-8"))
    canon = json.loads((root / "data/cultivation.json").read_text(encoding="utf-8"))
    source_cache = {}

    def source(path):
        if path not in source_cache:
            raw = subprocess.run(["git", "show", SOURCE + ":" + path], cwd=root,
                                 check=True, capture_output=True, text=True).stdout
            source_cache[path] = raw
        return source_cache[path]

    before_book = json.loads(source(BOOK)) if verify_source else None
    before_canon = json.loads(source("data/cultivation.json")) if verify_source else None
    report = validate_records(book, audit, canon, before_book, before_canon)
    story = load_story(root)
    assert all(story["nodes"][r["node_id"]] == book["nodes"][r["node_id"]]
               for r in records(audit))
    if verify_source:
        actual_sha = subprocess.run(["git", "rev-parse", SOURCE + ":" + BOOK], cwd=root,
                                    check=True, capture_output=True, text=True).stdout.strip()
        assert actual_sha == audit["source_book_blob_sha"]
        for historical in audit["historical_assertion_check"]:
            assert not any(node_id in source(historical["path"])
                           for node_id in DEFECT_IDS | CLARIFIED_IDS)
            actual_sha = subprocess.run(
                ["git", "rev-parse", SOURCE + ":" + historical["path"]], cwd=root,
                check=True, capture_output=True, text=True).stdout.strip()
            assert actual_sha == historical["sha"]
    report["source_verified"] = verify_source
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-source", action="store_true")
    args = parser.parse_args()
    print(json.dumps(validate(verify_source=args.verify_source), indent=2))
