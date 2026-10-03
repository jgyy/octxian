"""Protect independent recovered advancement and common branch knowledge."""
import unittest
from tools.story_data import load_story


class FoundryProgressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.story = load_story()
        cls.nodes = cls.story["nodes"]

    def reachable_without(self, blocked):
        reached, queue = set(), [self.story["start"]]
        for identifier in queue:
            if identifier == blocked or identifier in reached:
                continue
            reached.add(identifier)
            node = self.nodes[identifier]
            queue.extend(node[field] for field in ("next", "continuation") if field in node)
            queue.extend(choice["next"] for choice in node.get("choices", []))
        return reached

    def assert_required(self, prerequisites, target):
        for prerequisite in prerequisites:
            with self.subTest(prerequisite=prerequisite, target=target):
                self.assertNotIn(target, self.reachable_without(prerequisite))

    def test_every_ring_outcome_continues_into_the_same_existing_stage(self):
        for identifier in ("ending_ring_return", "ending_ring_custody", "ending_ring_refusal"):
            with self.subTest(outcome=identifier):
                self.assertEqual(self.nodes[identifier]["continuation"], "foundry_arrival_001")
        self.assertEqual(self.nodes["foundry_arrival_001"]["cultivation"],
                         {"realm": "qi_gathering", "stage": "3: First pair"})

    def test_no_fourth_stage_scene_bypasses_independent_certification(self):
        before = self.reachable_without("foundry_assessment_018")
        promoted = {identifier for identifier, node in self.nodes.items()
                    if node.get("chapter") == "book_viii"
                    and node.get("cultivation", {}).get("stage") == "4: Second pair"}
        self.assertTrue(promoted)
        self.assertFalse(promoted & before)
        self.assertEqual(self.nodes["foundry_assessment_018"]["cultivation"]["stage"],
                         "4: Second pair")

    def test_work_branches_receive_common_findings_before_route_practice(self):
        self.assert_required(("foundry_work_rejoin_001", "foundry_work_rejoin_004"),
                             "foundry_route_001")

    def test_resumption_requires_recovery_and_shared_defense_reports(self):
        self.assert_required(("foundry_recovery_015", "foundry_recovery_016",
                              "foundry_recovery_017", "foundry_recovery_018",
                              "foundry_creature_rejoin_003", "foundry_creature_rejoin_007"),
                             "foundry_resume_002")

    def test_all_three_trials_and_next_day_checks_precede_certification(self):
        self.assert_required(("foundry_assessment_001", "foundry_assessment_004",
                              "foundry_assessment_006", "foundry_assessment_008",
                              "foundry_assessment_011", "foundry_assessment_014",
                              "foundry_assessment_016", "foundry_assessment_017"),
                             "foundry_assessment_018")

    def test_final_work_choices_are_available_without_attribute_grinding(self):
        choices = self.nodes["foundry_final_choice"]["choices"]
        self.assertEqual(len(choices), 3)
        for choice in choices:
            with self.subTest(choice=choice["next"]):
                self.assertFalse(choice.get("requires"))
        for target in ("foundry_end_bench", "foundry_end_survey", "foundry_end_home"):
            self.assert_required(("foundry_assessment_018", "foundry_aftermath_008"), target)


if __name__ == "__main__":
    unittest.main()
