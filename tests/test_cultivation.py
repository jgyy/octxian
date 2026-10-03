"""Cultivation is earned through mandatory practice, not choice-point thresholds."""
import copy
import unittest

from tools.cultivation import load_canon, validate_progress
from tools.story_data import load_story


class CultivationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.story = load_story()
        cls.canon = load_canon()

    def reachable_without(self, blocked):
        reached = set()
        queue = [self.story["start"]]
        for identifier in queue:
            if identifier == blocked or identifier in reached:
                continue
            reached.add(identifier)
            node = self.story["nodes"][identifier]
            queue.extend(node[field] for field in ("next", "continuation") if field in node)
            queue.extend(choice["next"] for choice in node.get("choices", []))
        return reached

    def test_canon_matches_every_authored_realm_label(self):
        realms = validate_progress(self.canon, self.story)
        self.assertEqual(len(realms), 12)
        self.assertEqual(self.canon["protagonist"]["starting_qi"], 0)
        self.assertEqual(self.story["nodes"][self.story["start"]]["cultivation"],
                         {"realm": "mortal", "stage": "Unsensed"})

    def test_unknown_realms_and_wrong_stage_are_rejected(self):
        for progress in ({"realm": "instant_immortal", "stage": "1"},
                         {"realm": "mortal", "stage": "Sealed core"},
                         ["mortal"]):
            with self.subTest(progress=progress):
                story = {"nodes": {"fixture": {"cultivation": progress}}}
                with self.assertRaisesRegex(ValueError, "cultivation"):
                    validate_progress(self.canon, story)

    def test_duplicate_or_incomplete_canon_is_rejected(self):
        canon = copy.deepcopy(self.canon)
        canon["realms"].append(copy.deepcopy(canon["realms"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            validate_progress(canon, self.story)
        canon = copy.deepcopy(self.canon)
        canon["realms"][2]["recovery"] = ""
        with self.assertRaisesRegex(ValueError, "Incomplete"):
            validate_progress(canon, self.story)

    def test_no_path_skips_training_and_three_recovered_trace_tests(self):
        required = ("mortal_rejoin_002", "tempering_006", "tempering_013",
                    "tempering_after_004", "tempering_after_005",
                    "tempering_after_011", "tempering_after_012")
        for identifier in required:
            with self.subTest(checkpoint=identifier):
                self.assertNotIn("tempering_after_013", self.reachable_without(identifier))
                self.assertNotIn("pendant", self.reachable_without(identifier))

    def test_mortal_choices_grant_no_qi_and_never_promote_a_realm(self):
        for identifier in ("mortal_first_choice", "mortal_mite_choice"):
            node = self.story["nodes"][identifier]
            for choice in node["choices"]:
                self.assertEqual(choice.get("effects", {}).get("qi", 0), 0)
                target = self.story["nodes"][choice["next"]]
                self.assertEqual(target["cultivation"], node["cultivation"])
        for identifier in ("breath", "inscription", "sword", "ending_shared",
                           "ending_covenant", "ending_release"):
            self.assertEqual(self.story["nodes"][identifier]["cultivation"],
                             {"realm": "qi_gathering", "stage": "1: Trace"})

    def test_training_branch_outcomes_rejoin_the_earned_path(self):
        for identifier in ("mortal_work_001", "mortal_study_001", "mortal_recover_001",
                           "mite_cloth_001", "mite_scoop_001", "mite_warning_001"):
            seen = set()
            current = identifier
            rejoin = ("mortal_rejoin_001" if identifier.startswith("mortal_")
                      else "tempering_after_001")
            while current != rejoin:
                self.assertNotIn(current, seen)
                seen.add(current)
                current = self.story["nodes"][current]["next"]
            self.assertIn(rejoin, self.reachable_without(""))

    def test_no_valley_path_skips_retention_and_first_pair_assessments(self):
        required = ("sluice_020", "sluice_021", "sluice_037", "sluice_038",
                    "sluice_039", "sluice_040", "channels_028", "channels_031",
                    "channels_041", "channels_042", "channels_043", "channels_044")
        for identifier in required:
            with self.subTest(checkpoint=identifier):
                self.assertNotIn("lantern_arrival", self.reachable_without(identifier))

    def test_stage_changes_occur_after_recovered_tests(self):
        for identifier in ("sluice_037", "sluice_038", "sluice_039"):
            self.assertEqual(self.story["nodes"][identifier]["cultivation"]["stage"],
                             "1: Trace")
        self.assertEqual(self.story["nodes"]["sluice_040"]["cultivation"]["stage"],
                         "2: Retention")
        for identifier in ("channels_041", "channels_042", "channels_043"):
            self.assertEqual(self.story["nodes"][identifier]["cultivation"]["stage"],
                             "2: Retention")
        self.assertEqual(self.story["nodes"]["channels_044"]["cultivation"]["stage"],
                         "3: First pair")

    def test_mantis_choices_keep_the_same_stage_and_rejoin(self):
        node = self.story["nodes"]["reed_step_011"]
        for choice in node["choices"]:
            with self.subTest(route=choice["next"]):
                current, seen = choice["next"], set()
                while current != "reed_step_012":
                    self.assertNotIn(current, seen)
                    seen.add(current)
                    target = self.story["nodes"][current]
                    self.assertEqual(target["cultivation"], node["cultivation"])
                    current = target["next"]
                self.assertEqual(len(seen), 2)


if __name__ == "__main__":
    unittest.main()
