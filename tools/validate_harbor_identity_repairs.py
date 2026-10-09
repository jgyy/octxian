"""Authenticate two harbor character-identity defects without counting the shared passage twice."""
import argparse
import json
import pathlib
import subprocess

from tools.story_data import load_story

ROOT = pathlib.Path(__file__).resolve().parents[1]
AUDIT = "docs/HARBOR_IDENTITY_REPAIRS_20261007.json"
SOURCE = "659f6c413867a3c7d5857e4b89c4f3aae1f39ae8"
BOOK = "data/books/book_xiv_harbor_27.json"
SOURCE_BLOB = "fc627e416290f921bdbe1b31a78eb89f3ede3d0e"
LUO = "HARBOR-LUO-IDENTITY-20261007"
KE = "HARBOR-KE-IDENTITY-20261007"
EXPECTED_NODES = {"harbor_road_012", "harbor_road_017"}
EXPECTED_AFFECTED = {
    LUO: {"harbor_road_012", "harbor_road_017"},
    KE: {"harbor_road_012"},
}
EXPECTED_TEXT_EDITS = {
    "harbor_road_012": [
        ("The others let her say both things.", "The others let him say both things."),
        ("after checking his own paid shift.", "after checking her own paid shift."),
    ],
    "harbor_road_017": [
        ("Luo her accepted hours", "Luo his accepted hours"),
    ],
}
HISTORICAL_PATHS = {
    "docs/ADDITIONAL_REPAIRS_20261005.json",
    "docs/CHOICE_CONSEQUENCE_AUDIT_20261006.json",
    "docs/CONTINUATION_SECOND_SOURCE_INDEX_20261003.json",
    "docs/CONTINUATION_SOURCE_INDEX_20261003.json",
    "docs/CONTINUITY_REPAIRS_20261003.json",
    "docs/CONTINUITY_REPAIRS_20261003_COURT.json",
    "docs/CONTINUITY_REPAIRS_20261003_CULTIVATION.json",
    "docs/CONTINUITY_REPAIRS_20261003_OPENING.json",
    "docs/CONTINUITY_REPAIRS_20261003_RING.json",
    "docs/CONTINUITY_REPAIRS_20261003_SECOND_CITY.json",
    "docs/CONTINUITY_REPAIRS_20261003_SECOND_CULTIVATION.json",
    "docs/CONTINUITY_REPAIRS_20261003_SECOND_FERRY.json",
    "docs/CONTINUITY_REPAIRS_20261003_SECOND_ORCHARD.json",
    "docs/CONTINUITY_REPAIRS_20261003_SECOND_RING.json",
    "docs/CONTINUITY_REPAIRS_20261003_SECOND_RIVER.json",
    "docs/CONTINUITY_REPAIRS_20261004.json",
    "docs/LATE_CONTINUITY_AUDIT_20261006.json",
    "docs/NARRATIVE_REPAIRS_20261005.json",
    "docs/REED_CROSSING_REPAIRS_20261006.json",
    "docs/SEMANTIC_CONTINUITY_REVIEW_20261006.json",
    "docs/STORM_SALT_REPAIRS_20261006.json",
    "docs/audits/vii_xii_causal_review_20261006.json",
    "docs/audits/vii_xii_salt_purchase_volume_20261006.json"
}


def validate(root=ROOT, verify_source=False):
    root = pathlib.Path(root)
    audit = json.loads((root / AUDIT).read_text(encoding="utf-8"))
    assert audit["schema_version"] == 1
    assert audit["source_commit"] == SOURCE
    assert audit["source_path"] == BOOK
    assert audit["source_file_sha"] == SOURCE_BLOB
    assert audit["requested_plot_holes"] == 1000
    assert audit["confirmed_underlying_defects"] == len(audit["defects"]) == 2
    assert audit["affected_source_passages"] == len(audit["repairs"]) == 2
    assert audit["corrected_pronoun_sites"] == 3
    assert audit["displayed_word_delta"] == 0
    assert audit["target_met"] is False
    assert {r["node_id"] for r in audit["repairs"]} == EXPECTED_NODES
    defects = {d["id"]: d for d in audit["defects"]}
    assert set(defects) == {LUO, KE}
    for defect_id, defect in defects.items():
        assert defect["classification"] == "confirmed_character_identity_defect"
        assert set(defect["affected_nodes"]) == EXPECTED_AFFECTED[defect_id]
        assert len(defect["affected_nodes"]) == len(EXPECTED_AFFECTED[defect_id])
        assert defect["evidence"]
    book = json.loads((root / BOOK).read_text(encoding="utf-8"))
    story = load_story(root)
    sources = {}
    source_shas = {}

    def source(path):
        if path not in sources:
            raw = subprocess.run(["git", "show", SOURCE + ":" + path], cwd=root,
                                 check=True, capture_output=True, text=True).stdout
            sources[path] = raw
        return sources[path]

    def source_sha(path):
        if path not in source_shas:
            source_shas[path] = subprocess.run(
                ["git", "rev-parse", SOURCE + ":" + path], cwd=root,
                check=True, capture_output=True, text=True).stdout.strip()
        return source_shas[path]

    changed_sites = 0
    delta = 0
    for repair in audit["repairs"]:
        node_id = repair["node_id"]
        before, after = repair["before_node"], repair["after_node"]
        assert book["nodes"][node_id] == story["nodes"][node_id] == after, (
            "Stale current identity repair: " + node_id)
        assert before["text"] != after["text"]
        assert {k: v for k, v in before.items() if k != "text"} == {
            k: v for k, v in after.items() if k != "text"}, "Identity correction changed mechanics"
        expected_text = before["text"]
        for old, new in EXPECTED_TEXT_EDITS[node_id]:
            assert expected_text.count(old) == 1
            expected_text = expected_text.replace(old, new, 1)
        assert expected_text == after["text"], "Correction exceeds the authenticated pronoun sites"
        declared_text = before["text"]
        assert repair["changes"]
        expected_defects = {LUO, KE} if node_id == "harbor_road_012" else {LUO}
        assert {c["defect_id"] for c in repair["changes"]} == expected_defects
        assert len(repair["changes"]) == len(EXPECTED_TEXT_EDITS[node_id])
        for change in repair["changes"]:
            assert node_id in EXPECTED_AFFECTED[change["defect_id"]]
            assert change["old"] != change["new"] and change["old"]
            assert declared_text.count(change["old"]) == 1
            declared_text = declared_text.replace(change["old"], change["new"], 1)
            changed_sites += 1
        assert declared_text == after["text"]
        actual_delta = len(after["text"].split()) - len(before["text"].split())
        assert actual_delta == repair["word_delta"] == 0
        assert len(after["text"].split()) <= 100
        delta += actual_delta
        if verify_source:
            assert source_sha(BOOK) == SOURCE_BLOB
            assert json.loads(source(BOOK))["nodes"][node_id] == before
    assert changed_sites == 3 and delta == 0
    for defect in defects.values():
        for evidence in defect["evidence"]:
            assert evidence["quote"] and evidence["quote"] in evidence["node"]["text"]
            assert len(evidence["source_file_sha"]) == 40
            if verify_source:
                assert source_sha(evidence["path"]) == evidence["source_file_sha"]
                assert json.loads(source(evidence["path"]))["nodes"][evidence["node_id"]] == evidence["node"]
    historical = audit["historic_audits"]
    assert len(historical) == len({r["path"] for r in historical}) == 23
    assert {r["path"] for r in historical} == HISTORICAL_PATHS
    assert all(r["matching_targets"] == [] and r["credited_overlap"] is False for r in historical)
    if verify_source:
        for prior in historical:
            assert source_sha(prior["path"]) == prior["source_file_sha"]
            assert not any(node_id in source(prior["path"]) for node_id in EXPECTED_NODES), (
                "Historical source mentions a newly credited target: " + prior["path"])
    current_review = root / "docs/CAREER_CONTINUITY_REPAIRS_20261007.json"
    if current_review.exists():
        assert not any(node_id in current_review.read_text(encoding="utf-8")
                       for node_id in EXPECTED_NODES), "Overlap with this PR's earlier repair audit"
    return {"confirmed_new_underlying_defects": 2, "affected_source_passages": 2,
            "corrected_pronoun_sites": changed_sites, "displayed_word_delta": delta,
            "requested_repairs": 1000, "target_met": False, "source_verified": verify_source}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-source", action="store_true")
    args = parser.parse_args()
    print(json.dumps(validate(verify_source=args.verify_source), indent=2))
