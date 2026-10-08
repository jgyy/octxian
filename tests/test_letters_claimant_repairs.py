"""Check the actual claimant repair and authenticate its published Git source."""
import copy
import json
import pathlib
import tempfile
import unittest
from unittest import mock

from tools.validate_letters_claimant_repairs import AUDIT, BOOK, ROOT, validate


class LettersClaimantRepairTests(unittest.TestCase):
    def read_current(self):
        audit = json.loads((ROOT / AUDIT).read_text(encoding="utf-8"))
        book = json.loads((ROOT / BOOK).read_text(encoding="utf-8"))
        return audit, book

    def fixture(self, root, audit, book):
        for path, model in ((AUDIT, audit), (BOOK, book)):
            target = pathlib.Path(root) / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(model, ensure_ascii=False), encoding="utf-8")

    def test_actual_current_fragment_and_campaign(self):
        result = validate()
        self.assertEqual(result["confirmed_new_underlying_defects"], 1)
        self.assertEqual(result["affected_source_passages"], 2)
        self.assertEqual(result["displayed_word_delta"], 1)
        self.assertEqual(result["book_words"], 7219)
        self.assertFalse(result["target_met"])

    def test_actual_git_show_source_and_canonical_anchors(self):
        # CI must fetch the pinned source commit before this test.
        # This invokes real git show/rev-parse for the original fragment,
        # all six canonical scene anchors and all nine overlap documents.
        result = validate(verify_source=True)
        self.assertTrue(result["source_verified"])

    def test_stale_fragment_is_rejected(self):
        audit, book = self.read_current()
        repair = audit["repairs"][0]
        book["nodes"][repair["node_id"]] = copy.deepcopy(repair["before_node"])
        with tempfile.TemporaryDirectory() as tmp:
            self.fixture(tmp, audit, book)
            with mock.patch("tools.validate_letters_claimant_repairs.load_story",
                            return_value={"nodes": book["nodes"]}):
                with self.assertRaises(AssertionError):
                    validate(tmp)

    def test_campaign_cannot_ignore_corrected_fragment(self):
        audit, book = self.read_current()
        stale_story = copy.deepcopy(book)
        repair = audit["repairs"][0]
        stale_story["nodes"][repair["node_id"]] = copy.deepcopy(repair["before_node"])
        with mock.patch("tools.validate_letters_claimant_repairs.load_story",
                        return_value=stale_story):
            with self.assertRaises(AssertionError):
                validate()

    def test_scene_manifestations_do_not_count_as_two_roots(self):
        audit, book = self.read_current()
        audit["confirmed_underlying_defects"] = 2
        with tempfile.TemporaryDirectory() as tmp:
            self.fixture(tmp, audit, book)
            with mock.patch("tools.validate_letters_claimant_repairs.load_story",
                            return_value={"nodes": book["nodes"]}):
                with self.assertRaises(AssertionError):
                    validate(tmp)

    def test_claimant_fix_cannot_change_navigation(self):
        audit, book = self.read_current()
        repair = audit["repairs"][0]
        repair["after_node"]["next"] = "letters_review_end"
        book["nodes"][repair["node_id"]] = copy.deepcopy(repair["after_node"])
        with tempfile.TemporaryDirectory() as tmp:
            self.fixture(tmp, audit, book)
            with mock.patch("tools.validate_letters_claimant_repairs.load_story",
                            return_value={"nodes": book["nodes"]}):
                with self.assertRaises(AssertionError):
                    validate(tmp)


if __name__ == "__main__":
    unittest.main()
