"""Regression: selection, shortcuts and shared work cannot earn branch credit."""
import copy
import json
import pathlib
import unittest
from tools.story_data import load_story
from tools.validate_storm_salt_repairs import validate, validate_campaign

ROOT = pathlib.Path(__file__).resolve().parents[1]


class StormSaltRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.story = load_story()
        cls.audit = json.loads((ROOT / "docs/STORM_SALT_REPAIRS_20261006.json").read_text())

    def changed(self):
        story = dict(self.story)
        story["nodes"] = dict(self.story["nodes"])
        repair = self.audit["repairs"][0]
        for key in (repair["node_id"], *repair["branch"]):
            story["nodes"][key] = copy.deepcopy(story["nodes"][key])
        return story, repair

    def test_delivered_source_sites_do_not_recount_previous_repairs(self):
        report = validate()
        self.assertEqual(report["new_repair_sites"], 13)
        self.assertEqual(report["unfulfilled_requested_repair_sites"], 87)
        self.assertEqual(report["remaining_words"], max(0, 2000000 - report["words"]))

    def test_selection_cannot_reintroduce_the_reward(self):
        story, repair = self.changed()
        story["nodes"][repair["node_id"]]["choices"][repair["choice_index"]]["effects"] = repair["earned"]
        with self.assertRaises(AssertionError):
            validate_campaign(self.audit, story)

    def test_work_cannot_be_bypassed(self):
        story, repair = self.changed()
        story["nodes"][repair["branch"][0]]["next"] = repair["completion_node"]
        with self.assertRaises(AssertionError):
            validate_campaign(self.audit, story)

    def test_another_route_cannot_claim_the_exclusive_completion(self):
        story, repair = self.changed()
        story["nodes"]["unrelated_shortcut"] = {"text": "Unrelated route.", "next": repair["completion_node"]}
        with self.assertRaisesRegex(AssertionError, "exclusive"):
            validate_campaign(self.audit, story)

    def test_pending_reward_cannot_appear_before_completion(self):
        story, repair = self.changed()
        story["nodes"][repair["branch"][0]]["earned"] = repair["earned"]
        with self.assertRaisesRegex(AssertionError, "final passage"):
            validate_campaign(self.audit, story)

    def test_repointing_the_audit_cannot_redefine_original_source(self):
        audit = copy.deepcopy(self.audit)
        audit["source_base"] = "0" * 40
        with self.assertRaisesRegex(AssertionError, "fixed source"):
            validate_campaign(audit, self.story)


if __name__ == "__main__":
    unittest.main()
