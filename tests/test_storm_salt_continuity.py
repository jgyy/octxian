"""Protect new-arc evidence, safe completion and actual artwork integration."""
import json
import pathlib
import unittest
from collections import deque

from tools.story_data import load_story


ROOT = pathlib.Path(__file__).resolve().parents[1]
IX_TO_X = {
    "ridge_model_003": "storm_from_model",
    "ridge_route_003": "storm_from_route",
    "ridge_home_003": "storm_from_home"
}
X_TO_XI = {
    "storm_end_public": "salt_from_public",
    "storm_end_workshop": "salt_from_workshop",
    "storm_end_home": "salt_from_home"
}
FINAL_CHOICES = {
    "book_x_storm_ledger": "storm_final_choice",
    "book_xi_salt_road": "salt_final_choice"
}
REQUIRED_BEFORE_FINAL = {
    "book_x_storm_ledger": [
        "storm_arrival_005",
        "storm_compare_002",
        "storm_compare_008",
        "storm_warning_007",
        "storm_after_001",
        "storm_settle_004",
        "storm_settle_008"
    ],
    "book_xi_salt_road": [
        "salt_arrival_012",
        "salt_arrival_016",
        "salt_findings_001",
        "salt_findings_002",
        "salt_water_clearance",
        "salt_findings_003",
        "salt_findings_004",
        "salt_findings_005",
        "salt_findings_006",
        "salt_grain_invoice",
        "salt_findings_010",
        "salt_findings_011",
        "salt_findings_012",
        "salt_findings_013",
        "salt_findings_016",
        "salt_recovery_009",
        "salt_recovery_010",
        "salt_recovery_011",
        "salt_recovery_012",
        "salt_recovery_014"
    ]
}
NEW_ART = {
    "backgrounds": {
        "thunderfen_warning_observatory": {
            "size": [
                1774,
                887
            ],
            "field": "background"
        },
        "salt_lantern_watermill": {
            "size": [
                1672,
                941
            ],
            "field": "background"
        }
    },
    "npcs": {
        "yuan_lian": {
            "size": [
                1024,
                1536
            ],
            "field": "actor"
        }
    },
    "monsters": {
        "reedglass_salamander": {
            "size": [
                1024,
                1536
            ],
            "field": "actor"
        }
    }
}


class StormSaltContinuityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.story = load_story()
        cls.nodes = cls.story["nodes"]
        cls.world = json.loads((ROOT / "data/world_assets.json").read_text(encoding="utf-8"))

    def reachable(self, start, omitted=None, ungated_only=False):
        """Traverse from a particular entrance, including continuing endings."""
        reached, queue = set(), deque([start])
        while queue:
            identifier = queue.popleft()
            if identifier == omitted or identifier in reached:
                continue
            reached.add(identifier)
            node = self.nodes[identifier]
            queue.extend(node[field] for field in ("next", "continuation") if field in node)
            queue.extend(choice["next"] for choice in node.get("choices", [])
                         if not ungated_only or not choice.get("requires"))
        return reached

    def test_all_prior_outcomes_have_distinct_valid_continuations(self):
        for mapping, chapter in ((IX_TO_X, "book_x_storm_ledger"),
                                 (X_TO_XI, "book_xi_salt_road")):
            self.assertEqual(len(set(mapping.values())), 3)
            for ending, entrance in mapping.items():
                with self.subTest(ending=ending):
                    self.assertIn("ending", self.nodes[ending])
                    self.assertEqual(self.nodes[ending]["continuation"], entrance)
                    self.assertEqual(self.nodes[entrance]["chapter"], chapter)
                    self.assertIn(FINAL_CHOICES[chapter], self.reachable(entrance))

    def test_every_new_scene_preserves_the_earned_second_pair(self):
        for chapter in FINAL_CHOICES:
            self.assertIn(chapter, self.story["chapters"])
            scenes = {identifier: node for identifier, node in self.nodes.items()
                      if node.get("chapter") == chapter}
            self.assertTrue(scenes, f"{chapter} must contain playable scenes")
            for identifier, node in scenes.items():
                with self.subTest(scene=identifier):
                    self.assertEqual(node["cultivation"],
                                     {"realm": "qi_gathering", "stage": "4: Second pair"})

    def test_independent_reports_safety_and_funding_dominate_final_decisions(self):
        # These are authored policy anchors, independent of the continuity ledger.
        # First establish reachability so a broken entrance cannot pass vacuously.
        for chapter, entrances in (("book_x_storm_ledger", IX_TO_X.values()),
                                   ("book_xi_salt_road", X_TO_XI.values())):
            final = FINAL_CHOICES[chapter]
            for entrance in entrances:
                self.assertIn(final, self.reachable(entrance))
                for checkpoint in REQUIRED_BEFORE_FINAL[chapter]:
                    with self.subTest(entrance=entrance, checkpoint=checkpoint):
                        self.assertEqual(self.nodes[checkpoint]["chapter"], chapter)
                        self.assertNotIn(final, self.reachable(entrance, omitted=checkpoint),
                                         f"{entrance} can skip {checkpoint}")

    def test_each_final_decision_has_an_ungated_route_to_its_own_ending(self):
        for chapter, final in FINAL_CHOICES.items():
            choices = self.nodes[final]["choices"]
            available = [choice for choice in choices if not choice.get("requires")]
            with self.subTest(final=final):
                self.assertTrue(available, "A player score must not force another field task")
                endings = {identifier for identifier, node in self.nodes.items()
                           if node.get("chapter") == chapter and "ending" in node}
                self.assertTrue(endings)
                for choice in available:
                    self.assertTrue(endings & self.reachable(choice["next"], ungated_only=True),
                                    "The available offer must be completable without a score gate")

    def test_all_four_new_originals_are_used_in_reachable_new_scenes(self):
        reached = self.reachable(self.story["start"])
        new_scenes = {identifier: self.nodes[identifier] for identifier in reached
                      if self.nodes[identifier].get("chapter") in FINAL_CHOICES}
        for category, originals in NEW_ART.items():
            for identifier, policy in originals.items():
                with self.subTest(asset=identifier):
                    entries = [entry for entry in self.world[category]
                               if entry["id"] == identifier]
                    self.assertEqual(len(entries), 1)
                    self.assertEqual(entries[0]["native_size"], policy["size"])
                    uses = [node for node in new_scenes.values()
                            if node.get(policy["field"]) == identifier]
                    self.assertTrue(uses, "A gallery entry must also participate in the new story")
                    if category == "npcs":
                        self.assertIn(identifier, self.story["characters"])
                        self.assertTrue(any(node.get("speaker") == identifier for node in uses),
                                        "The new portrait must render with its registered speaker")
        self.assertEqual(self.nodes["salt_findings_003"]["speaker"], "yuan_lian")
        self.assertEqual(self.nodes["salt_findings_003"]["actor"], "yuan_lian")
        self.assertEqual(self.nodes["salt_recovery_005"]["actor"], "reedglass_salamander")


if __name__ == "__main__":
    unittest.main()
