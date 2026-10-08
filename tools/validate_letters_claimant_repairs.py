"""Authenticate one published claimant-attribution defect at two Book XVIII passages."""
import argparse
import copy
import json
import pathlib
import subprocess

from tools.story_data import load_story

ROOT = pathlib.Path(__file__).resolve().parents[1]
AUDIT = "docs/LETTERS_CLAIMANT_REPAIRS_20261008.json"
SOURCE = "8e419bbb154fa2911d0f5b73a7bfee493c9f2507"
BOOK = "data/books/book_xviii_consequences.json"
SOURCE_BLOB = "2ddf24ae1e45fcffa8ebd28467165c953e95c31b"
DEFECT = "published-xviii-compensation-holder"
EXPECTED_EDITS = {
    "letters_prepare_003": (
        "Her existing house right and paid compensation were already settled.",
        "The earlier inquiry's house right and paid compensation belonged to He Xi's mother.",
        3,
    ),
    "letters_sun_result_002": (
        "Her ownership, settled compensation and private notebook stayed beyond this new task.",
        "Her ownership and private notebook stayed beyond this new task.",
        -2,
    ),
}
CANONICAL_ANCHORS = {
    ("data/books/book_xvii_archive_04.json", "archive_04_witness_016"):
        "1a9692abd8725a07490884764fb2daecdb5999c0",
    ("data/books/book_xvii_archive_21.json", "archive_21_004"):
        "88883ec8834a80d5e587b9e92780d111d635da9c",
    ("data/books/book_xvii_archive_22.json", "archive_22_036"):
        "64c4bf770516eeefd377af63b311ddbc40c0efeb",
    ("data/books/book_xvii_archive_22.json", "archive_22_037"):
        "64c4bf770516eeefd377af63b311ddbc40c0efeb",
    ("data/books/book_xvii_archive_23.json", "archive_23_011"):
        "a8855584e8b3e226273f1002a031fa73baf414ca",
    ("data/books/book_xvii_archive_24.json", "archive_24_042"):
        "93936aa9d5d5672bd23d71689993728eedf09532",
}
HISTORICAL_BLOBS = {
    "docs/CHOICE_CONSEQUENCE_AUDIT_20261006.json": "7d82fca79007d6d71217581a4b9832f275808e59",
    "docs/REED_CROSSING_REPAIRS_20261006.json": "e81008b6557f5ff8e6257d6f304a4ef0015d3e8d",
    "docs/CAREER_CONTINUITY_REPAIRS_20261007.json": "2e306efd77c1c9a006395d66d07f3c508f85cdcc",
    "docs/HARBOR_IDENTITY_REPAIRS_20261007.json": "232f8218b5cc2b5fa33c2afb4774e41261b4eed6",
    "docs/COMMISSION_CONTINUITY_REPAIRS_20261008.json": "91acc3dc5e3b8c02415ffcbb1767b7d2c2be738a",
    "docs/LATE_IDENTITY_REPAIRS_20261008.json": "00179389fd86a36829a1538c8d249eacdc154915",
    "docs/LATE_CONTINUITY_AUDIT_20261006.json": "2d927df69bb47be9257ca354095207428c733616",
    "docs/SEMANTIC_CONTINUITY_REVIEW_20261006.json": "f87976fc2884c250d96800e9c2defdf8e42d3e26",
    "docs/CONTINUITY_REPAIRS_20261004.json": "c4fb5d5d9d0024778d3cf6e234b727f87d1e4d57",
}


def validate(root=ROOT, verify_source=False):
    root = pathlib.Path(root)
    audit = json.loads((root / AUDIT).read_text(encoding="utf-8"))
    assert audit["schema_version"] == 1
    assert audit["source_commit"] == SOURCE
    assert audit["source_path"] == BOOK
    assert audit["source_file_sha"] == SOURCE_BLOB
    assert audit["requested_plot_holes"] == 1000
    assert audit["confirmed_underlying_defects"] == len(audit["defects"]) == 1
    assert audit["affected_source_passages"] == len(audit["repairs"]) == 2
    assert audit["target_met"] is False
    assert audit["displayed_word_delta"] == 1
    assert audit["book_words_before"] == 7218
    assert audit["book_words_after"] == 7219
    assert audit["book_scenes"] == 92
    defect = audit["defects"][0]
    assert defect["id"] == DEFECT
    assert defect["classification"] == "confirmed_claimant_attribution_defect"
    assert set(defect["affected_nodes"]) == set(EXPECTED_EDITS)
    assert len(defect["affected_nodes"]) == 2
    assert {r["node_id"] for r in audit["repairs"]} == set(EXPECTED_EDITS)
    book = json.loads((root / BOOK).read_text(encoding="utf-8"))
    story = load_story(root)
    assert set(book) == {"chapters", "characters", "nodes"}
    assert len(book["nodes"]) == 92
    assert sum(len(n["text"].split()) for n in book["nodes"].values()) == 7219
    assert all(len(n["text"].split()) <= 100 for n in book["nodes"].values())
    sources = {}
    source_shas = {}

    def source(path):
        if path not in sources:
            sources[path] = subprocess.run(
                ["git", "show", SOURCE + ":" + path], cwd=root, check=True,
                capture_output=True, text=True, encoding="utf-8").stdout
        return sources[path]

    def source_sha(path):
        if path not in source_shas:
            source_shas[path] = subprocess.run(
                ["git", "rev-parse", SOURCE + ":" + path], cwd=root, check=True,
                capture_output=True, text=True, encoding="utf-8").stdout.strip()
        return source_shas[path]

    delta = 0
    for repair in audit["repairs"]:
        node_id = repair["node_id"]
        before, after = repair["before_node"], repair["after_node"]
        assert repair["root_cause"] == DEFECT
        assert repair["classification"] == "confirmed_claimant_attribution_defect"
        assert repair["source_path"] == BOOK
        assert repair["source_file_sha"] == SOURCE_BLOB
        assert book["nodes"][node_id] == story["nodes"][node_id] == after, (
            "Stale current claimant repair: " + node_id)
        assert {k: v for k, v in before.items() if k != "text"} == {
            k: v for k, v in after.items() if k != "text"}, "Correction changed mechanics"
        old, new, expected_delta = EXPECTED_EDITS[node_id]
        assert before["text"].count(old) == 1
        assert before["text"].replace(old, new, 1) == after["text"], (
            "Correction exceeds the authenticated claimant wording")
        actual_delta = len(after["text"].split()) - len(before["text"].split())
        assert repair["word_delta"] == actual_delta == expected_delta
        delta += actual_delta
        if verify_source:
            assert source_sha(BOOK) == SOURCE_BLOB
            assert json.loads(source(BOOK))["nodes"][node_id] == before
    assert delta == 1
    evidence = defect["evidence"]
    assert len(evidence) == len(CANONICAL_ANCHORS) == 6
    assert {(e["path"], e["node_id"]) for e in evidence} == set(CANONICAL_ANCHORS)
    for anchor in evidence:
        path, node_id = anchor["path"], anchor["node_id"]
        assert anchor["source_file_sha"] == CANONICAL_ANCHORS[(path, node_id)]
        assert anchor["quote"] and anchor["quote"] in anchor["node"]["text"]
        if verify_source:
            assert source_sha(path) == anchor["source_file_sha"]
            assert json.loads(source(path))["nodes"][node_id] == anchor["node"]
    historical = audit["historic_audits"]
    assert len(historical) == len(HISTORICAL_BLOBS) == 9
    assert {r["path"] for r in historical} == set(HISTORICAL_BLOBS)
    for prior in historical:
        assert prior["source_file_sha"] == HISTORICAL_BLOBS[prior["path"]]
        assert prior["matching_targets"] == [] and prior["credited_overlap"] is False
        if verify_source:
            assert source_sha(prior["path"]) == prior["source_file_sha"]
            assert not any(node_id in source(prior["path"]) for node_id in EXPECTED_EDITS), (
                "Previously audited repair target: " + prior["path"])
    if verify_source:
        expected_book = copy.deepcopy(json.loads(source(BOOK)))
        for repair in audit["repairs"]:
            expected_book["nodes"][repair["node_id"]] = repair["after_node"]
        assert expected_book == book, "Unlisted change to the authenticated Book XVIII fragment"
    return {
        "confirmed_new_underlying_defects": 1,
        "affected_source_passages": 2,
        "displayed_word_delta": delta,
        "book_words": 7219,
        "book_scenes": 92,
        "requested_repairs": 1000,
        "target_met": False,
        "source_verified": verify_source,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-source", action="store_true")
    args = parser.parse_args()
    print(json.dumps(validate(verify_source=args.verify_source), indent=2))
