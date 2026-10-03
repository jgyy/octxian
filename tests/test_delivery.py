"""Production quotas are independent; passing draft validation is not completion."""
import contextlib
import io
import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch

from tools import validate_world


def catalog(original=100, interiors=100, npcs=100, monsters=100):
    return {
        "backgrounds": ([{} for _ in range(original)] +
                        [{"collection": "building_interiors"} for _ in range(interiors)]),
        "npcs": [{} for _ in range(npcs)],
        "monsters": [{} for _ in range(monsters)],
        "items": [],
    }


class DeliveryTests(unittest.TestCase):
    def test_every_quota_is_required(self):
        self.assertTrue(validate_world.delivery_report(catalog(), 1000001, 10001)["complete"])
        for group in ("original", "interiors", "npcs", "monsters"):
            with self.subTest(group=group):
                report = validate_world.delivery_report(catalog(**{group: 99}), 1000001, 10001)
                self.assertFalse(report["complete"])
        self.assertFalse(validate_world.delivery_report(catalog(), 1000000, 10001)["complete"])

    def test_extra_interiors_cannot_replace_original_backgrounds(self):
        report = validate_world.delivery_report(catalog(original=5, interiors=195), 1000001, 10001)
        self.assertEqual(report["delivered_art"]["backgrounds"], 200)
        self.assertFalse(report["art_targets_met"])
        self.assertEqual(report["remaining"]["backgrounds"], 95)
        self.assertEqual(report["remaining"]["building_interiors"], 0)

    def test_original_interiors_do_not_count_as_extra(self):
        world = catalog(interiors=0)
        world["backgrounds"] = [{"environment": "interior"} for _ in range(200)]
        report = validate_world.delivery_report(world, 1000001, 10001)
        self.assertFalse(report["complete"])
        self.assertEqual(report["remaining"]["building_interiors"], 100)

    def test_strict_command_fails_but_writes_reviewable_report(self):
        report = validate_world.delivery_report(catalog(original=5, interiors=10, npcs=4, monsters=2), 10274, 196)
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            with patch.object(validate_world, "ROOT", root), patch.object(validate_world, "inspect", return_value=report):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(validate_world.main([]), 0)
                    self.assertEqual(validate_world.main(["--require-complete"]), 1)
                saved = json.loads((root / "build/content_report.json").read_text())
                self.assertFalse(saved["complete"])
                self.assertEqual(saved["remaining"]["authored_words"], 989727)

    def test_strict_command_passes_only_when_complete(self):
        report = validate_world.delivery_report(catalog(), 1000001, 10001)
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(validate_world, "ROOT", pathlib.Path(temporary)), patch.object(validate_world, "inspect", return_value=report):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(validate_world.main(["--require-complete"]), 0)


if __name__ == "__main__":
    unittest.main()
