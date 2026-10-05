"""Regression checks for integrated manuscript and authenticated repair anchors."""
import unittest
from tools.validate_million_continuation import validate


class MillionContinuationTests(unittest.TestCase):
    def test_playable_manifest_rewards_and_all_finale_roles(self):
        report = validate()
        self.assertEqual(report["repair_sites"], 101)
        self.assertEqual(report["completed_tasks"], 92)
        self.assertGreater(report["words"], 1000000)


if __name__ == "__main__":
    unittest.main()
