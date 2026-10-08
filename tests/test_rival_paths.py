"""Exercise the rival chapter using actual local decisions and retained native art."""
from collections import deque
import json
import pathlib
import re
import unittest

from PIL import Image

from tools.story_data import load_story
from tools.validate_world import future_decisions, native_sprite_size, navigation_targets, validate_routes

ROOT = pathlib.Path(__file__).resolve().parents[1]
CHAPTER = "book_xxii_rival"
ENTRY = "rival_entry"
BRANCHES = ("rival_compete_entry", "rival_cooperate_entry", "rival_independent_entry")
PRIOR_ENDINGS = ("commission_new_request_06", "commission_home_06", "commission_daywork_06")
CULTIVATION = {"realm": "qi_gathering", "stage": "5: Four pairs"}


class RivalChapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.story = load_story(ROOT)
        cls.nodes = {key: node for key, node in cls.story["nodes"].items()
                     if node.get("chapter") == CHAPTER}
        cls.live_decisions = future_decisions(cls.story)

    def test_prior_settlements_continue_without_losing_their_endings(self):
        self.assertIn(CHAPTER, self.story["chapters"])
        self.assertIn(ENTRY, self.nodes)
        for key in PRIOR_ENDINGS:
            with self.subTest(ending=key):
                ending = self.story["nodes"][key]
                self.assertTrue(ending["ending"])
                self.assertEqual(ending["continuation"], ENTRY)

    def test_three_available_paths_have_distinct_scene_identity(self):
        options = self.nodes["rival_path_choice"]["choices"]
        self.assertEqual([choice["next"] for choice in options], list(BRANCHES))
        for choice in options:
            self.assertFalse(choice.get("requires"))
            self.assertFalse(choice.get("effects"))
        for prefix in ("rival_compete_", "rival_cooperate_", "rival_independent_"):
            self.assertTrue(any(key.startswith(prefix) for key in self.nodes), prefix)

    def test_an_elective_trial_cannot_award_growth_or_change_realm(self):
        for key, node in self.nodes.items():
            with self.subTest(scene=key):
                self.assertEqual(node["cultivation"], CULTIVATION)
                self.assertNotIn("earned", node)
                self.assertNotIn("random_event", node)
                self.assertTrue(node["text"].strip())
                self.assertLessEqual(len(node["text"].split()), 100)
                for choice in node.get("choices", []):
                    self.assertFalse(choice.get("effects"))
                    self.assertFalse(choice.get("requires"))

    def test_every_scene_is_reachable_on_an_actual_local_choice_history(self):
        validate_routes(self.story)
        prior_sources = {route["decision"] for node in self.nodes.values()
                         for route in node.get("routes", [])
                         if route["decision"] not in self.nodes}
        contexts = [{}]
        for source_id in sorted(prior_sources):
            source = self.story["nodes"][source_id]
            self.assertTrue(source.get("choices"))
            self.assertFalse(source.get("random_event", False))
            contexts.extend({source_id: choice["next"]} for choice in source["choices"])
        queue = deque((ENTRY, tuple(sorted(context.items()))) for context in contexts)
        visited, reached, endings, completed_branches = set(), set(), set(), set()
        while queue:
            key, stored = queue.popleft()
            signature = (key, tuple((decision, selected) for decision, selected in stored
                                    if decision in self.live_decisions[key]))
            if signature in visited:
                continue
            visited.add(signature)
            self.assertIn(key, self.nodes, "Rival journeys must stay within their chapter")
            reached.add(key)
            node = self.nodes[key]
            decisions = dict(stored)
            if "ending" in node:
                endings.add(key)
                completed_branches.add(decisions.get("rival_path_choice"))
                continue
            if "choices" in node:
                for choice in node["choices"]:
                    selected = dict(decisions)
                    selected[key] = choice["next"]
                    queue.append((choice["next"], tuple(sorted(selected.items()))))
                continue
            target = node["next"]
            for route in node.get("routes", []):
                if decisions.get(route["decision"]) == route["selected"]:
                    target = route["next"]
                    break
            queue.append((target, tuple(sorted(decisions.items()))))
        self.assertEqual(reached, set(self.nodes), "A union of impossible callbacks is insufficient")
        self.assertGreaterEqual(len(endings), 3)
        self.assertEqual(completed_branches, set(BRANCHES))

    def test_all_possible_edges_remain_acyclic(self):
        indegrees = {key: 0 for key in self.nodes}
        edges = {}
        for key, node in self.nodes.items():
            targets = set(navigation_targets(node))
            self.assertLessEqual(targets, self.nodes.keys())
            edges[key] = targets
            for target in targets:
                indegrees[target] += 1
        queue = deque(key for key, value in indegrees.items() if value == 0)
        visited = 0
        while queue:
            key = queue.popleft()
            visited += 1
            for target in edges[key]:
                indegrees[target] -= 1
                if indegrees[target] == 0:
                    queue.append(target)
        self.assertEqual(visited, len(self.nodes), "Rival routes must not create a practice loop")

    def test_new_full_names_do_not_shadow_named_prior_people(self):
        inherited = "\n".join(node["text"] for node in self.story["nodes"].values()
                              if node.get("chapter") != CHAPTER)
        for actor in ("rival_qiu_zhen", "rival_su_yao"):
            name = self.story["characters"][actor]["name"]
            with self.subTest(actor=actor, name=name):
                self.assertNotRegex(inherited, re.compile(r"\b" + re.escape(name) + r"\b",
                                                        re.IGNORECASE))

    def test_new_people_have_retained_native_transparent_originals(self):
        world = json.loads((ROOT / "data/world_assets.json").read_text())
        people = {entry["id"]: entry for entry in world["npcs"]}
        for actor in ("rival_qiu_zhen", "rival_su_yao"):
            with self.subTest(actor=actor):
                self.assertIn(actor, self.story["characters"])
                self.assertIn(actor, people)
                entry = people[actor]
                with Image.open(ROOT / entry["path"]) as image:
                    image.load()
                    self.assertEqual(image.mode, "RGBA")
                    self.assertEqual(list(image.size), entry["native_size"])
                    self.assertTrue(native_sprite_size(image.size))
                    minimum, maximum = image.getchannel("A").getextrema()
                    self.assertEqual(minimum, 0)
                    self.assertGreater(maximum, 0)
                provenance = entry["provenance"]
                self.assertEqual(provenance["kind"], "original_painting")
                self.assertEqual(provenance["derivation"], "none")
                self.assertFalse(provenance.get("derived_from"))
                self.assertEqual(provenance["native_size"], entry["native_size"])
                record = (ROOT / provenance["record"]).read_text()
                self.assertTrue(actor in record or entry["path"] in record)


if __name__ == "__main__":
    unittest.main()
