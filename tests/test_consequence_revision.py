"""Keep the published branch evidence and measured delivery tied to playable data."""
import unittest
from tools.validate_consequence_revision import validate


class ConsequenceRevisionTests(unittest.TestCase):
    def test_exact_editorial_evidence_and_exclusive_followthrough(self):
        report = validate()
        self.assertEqual(report["verified_new_plot_repairs"], 1)
        self.assertEqual(report["consequence_improvements"], 6)
        self.assertEqual(report["selected_callback_routes"], 19)
        self.assertFalse(report["plot_repair_target_met"])
        self.assertEqual(report["remaining_words"], max(0, 2000000 - report["displayed_words"]))


if __name__ == "__main__":
    unittest.main()
