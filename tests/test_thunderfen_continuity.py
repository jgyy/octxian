"""Chance changes conditions, never earned capability or unoffered access."""
import json
import pathlib
import unittest
from tools.story_data import load_story


class ThunderfenContinuityTests(unittest.TestCase):
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

    def test_all_foundry_outcomes_continue_without_an_offscreen_promotion(self):
        expected = {"foundry_end_bench": "ridge_from_bench",
                    "foundry_end_survey": "ridge_from_survey",
                    "foundry_end_home": "ridge_from_home"}
        for ending, opening in expected.items():
            self.assertEqual(self.nodes[ending]["continuation"], opening)
            self.assertEqual(self.nodes[opening]["next"], "ridge_departure_001")
        for identifier, node in self.nodes.items():
            if node.get("chapter") == "book_ix":
                with self.subTest(scene=identifier):
                    self.assertEqual(node["cultivation"],
                                     {"realm": "qi_gathering", "stage": "4: Second pair"})
        self.assertNotIn("ridge_final_choice",
                         self.reachable_without("foundry_assessment_018"))

    def test_chance_cannot_grant_attributes_or_buy_permissions(self):
        events = [(identifier, node) for identifier, node in self.nodes.items()
                  if node.get("random_event")]
        self.assertEqual({identifier for identifier, _ in events},
                         {"ridge_weather_event", "ridge_incident_event"})
        for identifier, node in events:
            self.assertEqual(len(node["choices"]), 3)
            for choice in node["choices"]:
                self.assertFalse(choice.get("effects"))
                self.assertFalse(choice.get("requires"))

    def test_independent_findings_and_recovered_checks_cannot_be_bypassed(self):
        for checkpoint in ("ridge_findings_001", "ridge_findings_002",
                           "ridge_findings_004", "ridge_findings_005",
                           "ridge_return_002", "ridge_return_004",
                           "ridge_return_006", "ridge_return_007"):
            with self.subTest(checkpoint=checkpoint):
                self.assertNotIn("ridge_final_choice", self.reachable_without(checkpoint))

    def test_offered_cooperation_is_available_without_a_player_score(self):
        for identifier, index in (("city_registry_choice", 1),
                                  ("city_perfumer_choice", 1),
                                  ("court_final_choice", 1),
                                  ("court_docket_first_choice", 1),
                                  ("court_rain_calibration_choice", 1)):
            with self.subTest(scene=identifier):
                self.assertFalse(self.nodes[identifier]["choices"][index].get("requires"))

    def test_paperwork_and_funding_cannot_condition_tissue_or_supply_qi(self):
        cases = (("court_investigation_choice", 1, None),
                 ("court_investigation_choice", 2, None),
                 ("court_cost_time_choice", 2, "court_cost_time_interruption"),
                 ("court_docket_source_choice", 2, "court_docket_index_path"),
                 ("city_final_choice", 0, None))
        for identifier, index, completion in cases:
            choice = self.nodes[identifier]["choices"][index]
            with self.subTest(scene=identifier):
                if completion is None:
                    effects = choice["effects"]
                else:
                    self.assertNotIn("effects", choice)
                    self.assertEqual(choice["next"], completion)
                    effects = self.nodes[completion]["earned"]
                self.assertEqual(effects.get("qi", 0), 0)
                self.assertEqual(effects.get("resolve", 0), 0)
        self.assertIn("pole moved the reeds", self.nodes["ring_marsh_ache"]["text"])
        self.assertNotIn("pulse moved reeds", self.nodes["ring_marsh_ache"]["text"])

    def test_audit_has_real_unique_changed_anchors_and_matches_delivered_text(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        audit = json.loads((root / "docs/CONTINUITY_REPAIRS_20261003.json").read_text())
        anchors = set()
        for repair in audit["repairs"]:
            key = (repair["scene"], repair.get("choice_index"))
            self.assertNotIn(key, anchors)
            anchors.add(key)
            self.assertNotEqual(repair["before"], repair["after"])
            node = self.nodes[repair["scene"]]
            current = (node["choices"][repair["choice_index"]]
                       if "choice_index" in repair else node["text"])
            self.assertEqual(current, repair["after"])
        self.assertGreaterEqual(len(anchors), 101)


if __name__ == "__main__":
    unittest.main()
