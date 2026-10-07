"""Regression checks for source authenticity and honest continuity-repair counts."""
import copy
import json
import pathlib
import unittest

from tools.validate_career_repairs import AUDIT, BOOK, records, validate_records

ROOT = pathlib.Path(__file__).resolve().parents[1]


class CareerRepairAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = json.loads((ROOT / AUDIT).read_text(encoding="utf-8"))
        cls.book = json.loads((ROOT / BOOK).read_text(encoding="utf-8"))
        cls.canon = json.loads((ROOT / "data/cultivation.json").read_text(encoding="utf-8"))
        cls.source_book = copy.deepcopy(cls.book)
        for repair in records(cls.audit):
            cls.source_book["nodes"][repair["node_id"]] = copy.deepcopy(repair["before"])

    def validate(self, book=None, audit=None, source_book=None):
        return validate_records(
            self.book if book is None else book,
            self.audit if audit is None else audit,
            self.canon,
            self.source_book if source_book is None else source_book,
            self.canon)

    def test_authored_source_evidence_and_current_repairs_agree(self):
        report = self.validate()
        self.assertEqual(report["confirmed_new_underlying_defects"], 2)
        self.assertEqual(report["clarification_cases"], 1)
        self.assertFalse(report["target_met"])

    def test_fabricated_source_anchor_is_rejected(self):
        source_book = copy.deepcopy(self.source_book)
        source_book["nodes"]["crossing_linen_04"]["text"] += " Invented testimony."
        with self.assertRaises(AssertionError):
            self.validate(source_book=source_book)

    def test_report_cannot_reverse_performed_relief_chronology(self):
        source_book = copy.deepcopy(self.source_book)
        node = source_book["nodes"]["crossing_rod_03"]
        node["text"] = node["text"].replace(
            "after the timed interval", "before the second observation")
        with self.assertRaises(AssertionError):
            self.validate(source_book=source_book)

    def test_editorial_repair_cannot_change_a_story_transition(self):
        audit = copy.deepcopy(self.audit)
        book = copy.deepcopy(self.book)
        audit["repairs"][0]["after"]["next"] = "crossing_final_common"
        book["nodes"]["crossing_linen_04"]["next"] = "crossing_final_common"
        with self.assertRaises(AssertionError):
            self.validate(book=book, audit=audit)

    def test_ambiguous_circuit_language_cannot_add_defect_credit(self):
        audit = copy.deepcopy(self.audit)
        audit["confirmed_underlying_defects"] = 3
        audit["clarifications"][0]["confirmed_defect_credit"] = 1
        with self.assertRaises(AssertionError):
            self.validate(audit=audit)

    def test_second_clarification_passage_cannot_be_omitted(self):
        audit = copy.deepcopy(self.audit)
        audit["clarifications"][0]["repairs"].pop()
        with self.assertRaises(AssertionError):
            self.validate(audit=audit)


if __name__ == "__main__":
    unittest.main()
