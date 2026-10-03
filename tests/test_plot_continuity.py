"""Protect facts which every affected branch must establish before relying on them."""
import unittest
from tools.story_data import load_story


class PlotContinuityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.story = load_story()

    def reachable_without(self, blocked):
        reached, queue = set(), [self.story["start"]]
        for identifier in queue:
            if identifier == blocked or identifier in reached:
                continue
            reached.add(identifier)
            node = self.story["nodes"][identifier]
            queue.extend(node[field] for field in ("next", "continuation") if field in node)
            queue.extend(choice["next"] for choice in node.get("choices", []))
        return reached

    def assert_required(self, required, targets):
        for prerequisite in required:
            reached = self.reachable_without(prerequisite)
            for target in targets:
                with self.subTest(prerequisite=prerequisite, target=target):
                    self.assertNotIn(target, reached)

    def test_all_mountain_outcomes_require_discovery_isolation_and_star_terms(self):
        self.assert_required(
            ("exile", "fracture", "star_terms"),
            ("ending_shared", "ending_covenant", "ending_release"))

    def test_every_river_outcome_passes_the_common_sheltered_stop(self):
        self.assert_required(
            ("river_interim",),
            ("ending_river_return", "ending_river_stair", "ending_river_harbor"))

    def test_harbor_departure_requires_funded_review_and_accepted_scope(self):
        self.assert_required(
            ("harbor_first_reply", "harbor_review", "harbor_review_terms"),
            ("harbor_departure", "ending_river_harbor"))

    def test_owner_outcomes_require_context_and_separate_receipt_comparison(self):
        self.assert_required(
            ("ring_jin_context", "ring_shared_marsh_report",
             "ring_shared_archive_report", "ring_shared_road_report",
             "ring_private_request", "ring_eel_comparison_terms", "ring_eel_recognition"),
            ("ending_ring_return", "ending_ring_custody", "ending_ring_refusal"))

    def test_later_books_keep_the_last_earned_protagonist_stage(self):
        later = {"book_iii", "book_iv", "book_v", "book_vi", "book_vii"}
        expected = {"realm": "qi_gathering", "stage": "3: First pair"}
        for identifier, node in self.story["nodes"].items():
            if node.get("chapter") in later:
                with self.subTest(scene=identifier):
                    self.assertEqual(node.get("cultivation"), expected)


if __name__ == "__main__":
    unittest.main()
