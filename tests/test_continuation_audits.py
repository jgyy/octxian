"""Audit counts must represent distinct source defects and exact current prose."""
import contextlib
import io
import json
import pathlib
import tempfile
import unittest

from tools.validate_continuation_audits import (
    main, normalize_audit, validate_audits, validate_documents,
)

SOURCE = "d2ce2851c8e47842104607ec5999ffba6fdabe1c"


def passage(node_id="arrival", path="data/story.json"):
    return {
        "path": path, "node_id": node_id,
        "before": "Original source paragraph.",
        "after": "Repaired arrival paragraph." if node_id == "arrival"
                 else "Repaired book paragraph.",
    }


def audit():
    return {
        "source_base": SOURCE, "total_repairs": 1,
        "repairs": [{
            "id": "FIX-001", **passage(),
            "reason": "An offered private record was read at a public table.",
            "category": "privacy",
        }],
    }


class ContinuationAuditTests(unittest.TestCase):
    def setUp(self):
        self.index = {
            "arrival": {"path": "data/story.json",
                        "text": "Repaired arrival paragraph."},
            "second": {"path": "data/books/book_ii.json",
                       "text": "Repaired book paragraph."},
        }

    def test_multipassage_root_counts_once_and_checks_both_origins(self):
        value = audit()
        value["repairs"][0]["affected_passages"] = [
            passage("second", "data/books/book_ii.json")]
        value["changed_passages"] = 2
        report = validate_documents(
            [value], self.index,
            source_node_paths={key: row["path"] for key, row in self.index.items()},
            expected_source_base=SOURCE)
        self.assertEqual(report["repair_count"], 1)
        self.assertEqual(report["affected_node_count"], 2)
        self.assertTrue(report["source_membership_checked"])

    def test_existing_source_and_passage_aliases_normalize(self):
        value = audit()
        value["source_commit"] = value.pop("source_base")
        value["defect_count"] = value.pop("total_repairs")
        value["repairs"][0]["related_changes"] = [
            passage("second", "data/books/book_ii.json")]
        value["changed_scene_count"] = 2
        report = validate_documents([value], self.index)
        self.assertEqual((report["repair_count"], report["affected_node_count"]), (1, 2))
        ring_style = audit()
        ring_style["review_base"] = ring_style.pop("source_base")
        self.assertEqual(normalize_audit(ring_style)["source_base"], SOURCE)

    def test_no_op_and_whitespace_only_edits_cannot_count(self):
        for before in ("Repaired arrival paragraph.", "  Repaired  arrival paragraph.\n"):
            with self.subTest(before=before):
                value = audit()
                value["repairs"][0]["before"] = before
                with self.assertRaisesRegex(ValueError, "no-op"):
                    validate_documents([value], self.index)

    def test_nonempty_source_and_current_text_are_required(self):
        for field, text in (("before", ""), ("before", " \n "), ("before", None),
                            ("after", ""), ("after", 7)):
            with self.subTest(field=field, text=text):
                value = audit()
                value["repairs"][0][field] = text
                with self.assertRaisesRegex(ValueError, "nonempty text"):
                    validate_documents([value], self.index)

    def test_duplicate_root_ids_across_audits_are_rejected(self):
        other = audit()
        other["repairs"][0].update(passage("second", "data/books/book_ii.json"))
        with self.assertRaisesRegex(ValueError, "Duplicate root repair ID"):
            validate_documents([audit(), other], self.index)

    def test_same_node_cannot_inflate_separate_root_counts(self):
        other = audit()
        other["repairs"][0]["id"] = "FIX-002"
        with self.assertRaisesRegex(ValueError, "Duplicate affected node"):
            validate_documents([audit(), other], self.index)

    def test_same_node_cannot_repeat_within_one_root(self):
        value = audit()
        value["repairs"][0]["affected_passages"] = [passage()]
        with self.assertRaisesRegex(ValueError, "Duplicate affected node"):
            validate_documents([value], self.index)

    def test_non_story_and_unsafe_paths_are_rejected(self):
        for path in ("data/characters.json", "../data/story.json",
                     "data/books/../story.json", "data/books//book_ii.json",
                     "/data/story.json", "https://example.com/book.json"):
            with self.subTest(path=path):
                value = audit()
                value["repairs"][0]["path"] = path
                with self.assertRaises(ValueError):
                    validate_documents([value], self.index)

    def test_existing_node_cannot_claim_another_known_story_file(self):
        value = audit()
        value["repairs"][0]["path"] = "data/books/book_ii.json"
        with self.assertRaisesRegex(ValueError, "Story path mismatch"):
            validate_documents([value], self.index)

    def test_unknown_node_is_not_a_source_repair(self):
        value = audit()
        value["repairs"][0]["node_id"] = "invented"
        with self.assertRaisesRegex(ValueError, "Unknown story node"):
            validate_documents([value], self.index)

    def test_stale_after_anchor_fails_even_when_node_exists(self):
        value = audit()
        value["repairs"][0]["after"] = "An earlier proposed revision."
        with self.assertRaisesRegex(ValueError, "Stale after anchor"):
            validate_documents([value], self.index)

    def test_source_index_excludes_new_current_nodes(self):
        value = audit()
        value["repairs"][0].update(passage("second", "data/books/book_ii.json"))
        with self.assertRaisesRegex(ValueError, "New node excluded"):
            validate_documents([value], self.index,
                               source_node_paths={"arrival": "data/story.json"})

    def test_source_node_cannot_claim_a_new_file_location(self):
        with self.assertRaisesRegex(ValueError, "Source path mismatch"):
            validate_documents([audit()], self.index,
                               source_node_paths={"arrival": "data/books/old.json"})

    def test_declared_counts_cannot_inflate_computed_report(self):
        for field in ("total_repairs", "defect_count", "changed_passages",
                      "changed_scene_count", "total_edited_nodes", "changed_scene_paragraphs"):
            with self.subTest(field=field):
                value = audit()
                value[field] = 100
                with self.assertRaisesRegex(ValueError, "does not match"):
                    validate_documents([value], self.index)

    def test_source_alias_conflict_and_mixed_revisions_fail(self):
        value = audit()
        value["review_base"] = "a" * 40
        with self.assertRaisesRegex(ValueError, "conflicting aliases"):
            validate_documents([value], self.index)
        other = audit()
        other["source_base"] = "a" * 40
        other["repairs"][0]["id"] = "FIX-002"
        other["repairs"][0].update(passage("second", "data/books/book_ii.json"))
        with self.assertRaisesRegex(ValueError, "one fixed source_base"):
            validate_documents([audit(), other], self.index)
        with self.assertRaisesRegex(ValueError, "required source revision"):
            validate_documents([other], self.index, expected_source_base=SOURCE)

    def test_conflicting_related_passage_aliases_fail(self):
        value = audit()
        value["repairs"][0]["related_changes"] = []
        value["repairs"][0]["affected_passages"] = [
            passage("second", "data/books/book_ii.json")]
        with self.assertRaisesRegex(ValueError, "conflicting aliases"):
            validate_documents([value], self.index)


class LocalCampaignAuditTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = pathlib.Path(temporary.name)
        (self.root / "data/books").mkdir(parents=True)
        (self.root / "docs").mkdir()
        base = {
            "start": "arrival", "chapters": {}, "characters": {},
            "nodes": {"arrival": {"text": "Repaired arrival paragraph.",
                                  "next": "second"}},
            "books": ["data/books/book_ii.json"],
        }
        book = {
            "chapters": {}, "characters": {},
            "nodes": {"second": {"text": "Repaired book paragraph.",
                                 "ending": "Done"}},
        }
        self.write("data/story.json", base)
        self.write("data/books/book_ii.json", book)
        value = audit()
        value["repairs"][0]["affected_passages"] = [
            passage("second", "data/books/book_ii.json")]
        self.write("docs/audit.json", value)

    def write(self, path, value):
        (self.root / path).write_text(json.dumps(value), encoding="utf-8")

    def test_reads_the_local_manifest_and_prints_exact_counts(self):
        report = validate_audits(self.root, ["docs/audit.json"])
        self.assertEqual(report["repair_count"], 1)
        self.assertEqual(report["affected_node_count"], 2)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            main(["--root", str(self.root), "docs/audit.json",
                  "--source-base", SOURCE])
        self.assertIn("1 distinct repairs; 2 affected current story nodes", output.getvalue())
        self.assertIn("Historical node membership was not checked", output.getvalue())
        self.assertIn("do not replace editorial judgment", output.getvalue())

    def test_cli_original_index_excludes_an_added_scene_offline(self):
        self.write("docs/source_nodes.json", {"arrival": "data/story.json"})
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as failure:
                main(["--root", str(self.root), "docs/audit.json",
                      "--source-node-index", "docs/source_nodes.json"])
        self.assertEqual(failure.exception.code, 1)

    def test_present_but_unlisted_book_is_not_a_known_source_path(self):
        self.write("data/books/unlisted.json", {
            "chapters": {}, "characters": {},
            "nodes": {"extra": {"text": "Repaired book paragraph."}},
        })
        value = audit()
        value["repairs"][0].update(passage("extra", "data/books/unlisted.json"))
        self.write("docs/audit.json", value)
        with self.assertRaisesRegex(ValueError, "Unknown story node"):
            validate_audits(self.root, ["docs/audit.json"])


if __name__ == "__main__":
    unittest.main()
