"""Check real return paths, source evidence and preserved earlier endings."""
import json
import pathlib
import unittest
from collections import deque

from tools.story_data import load_story
from tools.validate_return_repairs import validate
from tools.validate_world import validate_routes

ROOT = pathlib.Path(__file__).resolve().parents[1]
CHAPTER = "book_xxiv_return"
ENDINGS = {"return_public_close", "return_source_close", "return_listener_close"}


class ReturnTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.story = load_story(ROOT)
        cls.nodes = {key: node for key, node in cls.story["nodes"].items()
                     if node.get("chapter") == CHAPTER}

    def test_each_season_ending_retains_its_identity_and_continues(self):
        for path in ("water", "archive", "road", "kiln", "garden", "harbor"):
            ending = self.story["nodes"]["season_end_" + path]
            self.assertTrue(ending["ending"])
            self.assertEqual(ending["continuation"], "return_001")

    def test_actual_choices_reach_all_distinct_outcomes_without_awarding_growth(self):
        validate_routes(self.story)
        reached, endings = set(), set()
        queue = deque(["return_001"])
        while queue:
            key = queue.popleft()
            if key in reached:
                continue
            reached.add(key)
            node = self.nodes[key]
            self.assertEqual(node["cultivation"],
                             {"realm": "qi_gathering", "stage": "5: Four pairs"})
            self.assertNotIn("earned", node)
            self.assertLessEqual(len(node["text"].split()), 100)
            if "ending" in node:
                endings.add(key)
            elif "choices" in node:
                self.assertEqual(key, "return_choice")
                for choice in node["choices"]:
                    self.assertFalse(choice.get("requires"))
                    self.assertFalse(choice.get("effects"))
                    queue.append(choice["next"])
            else:
                queue.append(node["next"])
        self.assertEqual(reached, set(self.nodes))
        self.assertEqual(endings, ENDINGS)

    def test_each_option_keeps_its_own_complete_consequence(self):
        options = self.nodes["return_choice"]["choices"]
        for option, ending in zip(options, (
                "return_public_close", "return_source_close", "return_listener_close")):
            current, seen = option["next"], set()
            while current != ending:
                self.assertNotIn(current, seen)
                seen.add(current)
                self.assertNotIn("choices", self.nodes[current])
                current = self.nodes[current]["next"]
            self.assertEqual(len(seen), 6)
            self.assertTrue(self.nodes[ending]["ending"])
        self.assertIn("no established answer", self.nodes["return_public_006"]["text"])
        self.assertIn("not establish how", self.nodes["return_source_004"]["text"])
        self.assertIn("not recovered the missing leaf", self.nodes["return_listener_006"]["text"])

    def test_one_source_defect_has_two_published_passages(self):
        report = validate(ROOT)
        self.assertEqual(report["repair_count"], 1)
        self.assertEqual(report["affected_node_count"], 2)
        self.assertFalse(report["source_prose_checked"])



if __name__ == "__main__":
    unittest.main()
