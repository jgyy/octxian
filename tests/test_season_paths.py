"""Exercise the season chapter using actual local decisions and retained native art."""
from collections import deque
import hashlib
import json
import pathlib
import unittest


from tools.story_data import load_story
from tools.validate_world import future_decisions, navigation_targets, validate_routes

ROOT = pathlib.Path(__file__).resolve().parents[1]
CHAPTER = "book_xxiii_season"
ENTRY = "season_entry"
BRANCHES = ("season_water_entry", "season_archive_entry", "season_road_entry",
            "season_kiln_entry", "season_garden_entry", "season_harbor_entry")
PRIOR_ENDINGS = ("rival_end_compete", "rival_end_cooperate", "rival_end_independent")
CULTIVATION = {"realm": "qi_gathering", "stage": "5: Four pairs"}


class SeasonChapterTests(unittest.TestCase):
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

    def test_six_available_paths_have_distinct_scene_identity(self):
        options = self.nodes["season_path_choice"]["choices"]
        self.assertEqual([choice["next"] for choice in options], list(BRANCHES))
        for choice in options:
            self.assertFalse(choice.get("requires"))
            self.assertFalse(choice.get("effects"))
        for prefix in ("season_water_", "season_archive_", "season_road_",
                       "season_kiln_", "season_garden_", "season_harbor_"):
            self.assertTrue(any(key.startswith(prefix) for key in self.nodes), prefix)

    def test_ordinary_seasonal_inquiry_cannot_award_unperformed_growth(self):
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
            self.assertIn(key, self.nodes, "Season journeys must stay within their chapter")
            reached.add(key)
            node = self.nodes[key]
            decisions = dict(stored)
            if "ending" in node:
                endings.add(key)
                completed_branches.add(decisions.get("season_path_choice"))
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
        self.assertEqual(len(endings), 6)
        self.assertEqual(completed_branches, set(BRANCHES))

    def test_missing_archive_history_leaves_specific_prior_actions_unclaimed(self):
        for number in range(2, 16):
            with self.subTest(arc=number):
                gate = self.nodes[f"season_archive_m{number:02d}_entry"]
                common = f"season_archive_m{number:02d}_common_001"
                self.assertEqual(gate["next"], common)
                self.assertIn(common, self.nodes)
                self.assertNotIn(common, {route["next"] for route in gate["routes"]})
                for route in gate["routes"]:
                    source = self.story["nodes"][route["decision"]]
                    self.assertIn(route["selected"], {choice["next"] for choice in source["choices"]})

    def test_all_possible_edges_remain_acyclic(self):
        indegrees = {key: 0 for key in self.nodes}
        edges = {}
        for key, node in self.nodes.items():
            targets = set() if "ending" in node else set(navigation_targets(node))
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
        self.assertEqual(visited, len(self.nodes), "Season routes must not create a practice loop")

    def test_requested_word_target_is_actual_displayed_prose(self):
        words = sum(len(node["text"].split()) for node in self.story["nodes"].values())
        self.assertGreaterEqual(words, 2_000_000)

    def test_delayed_history_is_bounded_for_exhaustive_path_coverage(self):
        self.assertLessEqual(max(len(self.live_decisions[key]) for key in self.nodes), 4)


    def test_original_season_paintings_retain_generator_bytes_and_playable_placements(self):
        proof = json.loads((ROOT / "assets/art/SEASON_20261008_PROMPTS.json").read_text())
        world = json.loads((ROOT / "data/world_assets.json").read_text())
        backgrounds = {entry["id"]: entry for entry in world["backgrounds"]}
        expected = {"season_orchard_gate", "season_archive_annex", "season_harbor_approach",
                    "season_canal_footpath", "season_kiln_courtyard", "season_letter_counter",
                    "season_kiln_public_room"}
        self.assertEqual({entry["id"] for entry in proof["entries"]}, expected)
        for entry in proof["entries"]:
            with self.subTest(painting=entry["id"]):
                data = (ROOT / entry["path"]).read_bytes()
                self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
                size = [int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")]
                self.assertEqual(size, entry["native_size"])
                self.assertEqual(size, backgrounds[entry["id"]]["native_size"])
                digest = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
                self.assertEqual(digest, entry["git_blob"], "Retain the original PNG, without resizing")
                self.assertEqual(len(data), entry["bytes"])
                self.assertFalse(entry["upsampled"])
                self.assertTrue(any(node["background"] == entry["id"] for node in self.nodes.values()))
        self.assertEqual(self.nodes["season_road_f01_008"]["background"], "season_letter_counter")
        self.assertEqual(self.nodes["season_kiln_01_008"]["background"], "season_kiln_public_room")


if __name__ == "__main__":
    unittest.main()
