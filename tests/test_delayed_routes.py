"""Delayed consequences must follow real choices without retaining every old branch."""
import unittest

from tools.validate_world import future_decisions, reachable_without, validate_routes


def campaign():
    return {
        "start": "choice",
        "nodes": {
            "choice": {"choices": [{"next": "left"}, {"next": "right"}]},
            "left": {"next": "dispatch"},
            "right": {"next": "dispatch"},
            "dispatch": {
                "next": "legacy",
                "routes": [
                    {"decision": "choice", "selected": "left", "next": "left_result"},
                    {"decision": "choice", "selected": "right", "next": "right_result"},
                ],
            },
            "left_result": {"next": "finish"},
            "right_result": {"next": "finish"},
            "legacy": {"next": "finish"},
            "finish": {"ending": "Done"},
        },
    }


class DelayedRouteTests(unittest.TestCase):
    def test_only_actual_choice_outcomes_are_reachable(self):
        story = campaign()
        validate_routes(story)
        reached = reachable_without(story)
        self.assertEqual(reached, set(story["nodes"]) - {"legacy"})
        # Merely drawing a fallback edge must not count it as delivered prose.
        story["start"] = "dispatch"
        self.assertEqual(reachable_without(story), {"dispatch", "legacy", "finish"})

    def test_a_route_cannot_borrow_an_unvisited_branch_decision(self):
        story = campaign()
        story["nodes"]["left"] = {"ending": "Left departs"}
        self.assertNotIn("left_result", reachable_without(story))
        self.assertIn("right_result", reachable_without(story))

    def test_route_aware_checkpoint_cannot_be_bypassed(self):
        story = campaign()
        self.assertNotIn("left_result", reachable_without(story, "left"))
        self.assertIn("right_result", reachable_without(story, "left"))
        self.assertNotIn("finish", reachable_without(story, "choice"))

    def test_first_matching_route_defines_reachability(self):
        story = campaign()
        story["nodes"]["left"]["next"] = "later_choice"
        story["nodes"]["right"]["next"] = "later_choice"
        story["nodes"]["later_choice"] = {"choices": [{"next": "later_yes"}]}
        story["nodes"]["later_yes"] = {"next": "dispatch"}
        story["nodes"]["dispatch"]["routes"].append({
            "decision": "later_choice", "selected": "later_yes", "next": "shadowed",
        })
        story["nodes"]["shadowed"] = {"ending": "Never selected"}
        validate_routes(story)
        self.assertNotIn("shadowed", reachable_without(story))

    def test_only_future_route_keys_are_retained(self):
        story = campaign()
        relevant = future_decisions(story)
        self.assertEqual(relevant["choice"], set())
        self.assertEqual(relevant["left"], {"choice"})
        self.assertEqual(relevant["dispatch"], {"choice"})
        self.assertEqual(relevant["left_result"], set())
        self.assertEqual(relevant["finish"], set())

    def test_many_old_choices_do_not_multiply_traversal_states(self):
        nodes = {"finish": {"ending": "Done"}}
        for index in range(60):
            target = f"choice_{index + 1}" if index < 59 else "finish"
            nodes[f"choice_{index}"] = {"choices": [
                {"next": f"left_{index}"}, {"next": f"right_{index}"},
            ]}
            nodes[f"left_{index}"] = {"next": target}
            nodes[f"right_{index}"] = {"next": target}
        story = {"start": "choice_0", "nodes": nodes}
        self.assertTrue(all(not keys for keys in future_decisions(story).values()))
        self.assertEqual(reachable_without(story), set(nodes))

    def test_malformed_or_ambiguous_conditions_are_rejected(self):
        invalid = [
            None, {}, "route", [],
            [{"decision": "choice", "selected": "left"}],
            [{"decision": "choice", "selected": "left", "next": "left_result", "extra": True}],
            [{"decision": "missing", "selected": "left", "next": "left_result"}],
            [{"decision": "left", "selected": "dispatch", "next": "left_result"}],
            [{"decision": "choice", "selected": "finish", "next": "left_result"}],
            [{"decision": "choice", "selected": "left", "next": "missing"}],
            [{"decision": "choice", "selected": "left", "next": 1}],
            [
                {"decision": "choice", "selected": "left", "next": "left_result"},
                {"decision": "choice", "selected": "left", "next": "right_result"},
            ],
        ]
        for routes in invalid:
            with self.subTest(routes=routes):
                story = campaign()
                story["nodes"]["dispatch"]["routes"] = routes
                with self.assertRaises(AssertionError):
                    validate_routes(story)

    def test_routes_require_an_ordinary_narrative_fallback(self):
        for field, value in (
                ("choices", [{"next": "finish"}]), ("ending", "Done"),
                ("continuation", "finish"), ("random_event", True)):
            with self.subTest(field=field):
                story = campaign()
                story["nodes"]["dispatch"][field] = value
                with self.assertRaises(AssertionError):
                    validate_routes(story)
        story = campaign()
        del story["nodes"]["dispatch"]["next"]
        with self.assertRaises(AssertionError):
            validate_routes(story)

    def test_distinct_choice_labels_need_distinct_saved_identities(self):
        story = campaign()
        story["nodes"]["choice"]["choices"].append({"text": "Another label", "next": "left"})
        with self.assertRaisesRegex(AssertionError, "distinct destination identities"):
            validate_routes(story)

    def test_random_encounters_cannot_be_player_decisions(self):
        story = campaign()
        story["nodes"]["choice"]["random_event"] = True
        with self.assertRaises(AssertionError):
            validate_routes(story)


if __name__ == "__main__":
    unittest.main()
