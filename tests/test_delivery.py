"""Production quotas are independent; passing draft validation is not completion."""
import contextlib
import hashlib
import io
import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
from PIL.PngImagePlugin import PngInfo

from tools import validate_world


def catalog(original=100, interiors=100, npcs=500, monsters=501):
    return {
        "backgrounds": ([{} for _ in range(original)] +
                        [{"collection": "building_interiors"} for _ in range(interiors)]),
        "npcs": [{} for _ in range(npcs)],
        "monsters": [{} for _ in range(monsters)],
        "items": [],
    }


class DeliveryTests(unittest.TestCase):
    def test_every_quota_is_required(self):
        self.assertTrue(validate_world.delivery_report(catalog(), 2000000, 10001)["complete"])
        for group, count in (("original", 99), ("interiors", 99), ("npcs", 499), ("monsters", 500)):
            with self.subTest(group=group):
                report = validate_world.delivery_report(catalog(**{group: count}), 2000000, 10001)
                self.assertFalse(report["complete"])
        self.assertFalse(validate_world.delivery_report(catalog(), 1999999, 10001)["complete"])

    def test_former_million_word_target_no_longer_finishes_delivery(self):
        report = validate_world.delivery_report(catalog(), 1000001, 10001)
        self.assertFalse(report["word_target_met"])
        self.assertEqual(report["remaining"]["authored_words"], 999999)
        self.assertFalse(report["complete"])

    def test_exactly_one_thousand_sprites_is_insufficient(self):
        report = validate_world.delivery_report(catalog(monsters=500), 2000000, 10001)
        self.assertEqual(report["delivered_unique_sprites"], 1000)
        self.assertEqual(report["remaining"]["unique_sprites"], 1)
        self.assertFalse(report["sprite_target_met"])
        self.assertFalse(report["complete"])

    def test_surplus_humans_cannot_replace_spirit_beasts(self):
        report = validate_world.delivery_report(catalog(npcs=1001, monsters=0), 2000000, 10001)
        self.assertTrue(report["sprite_target_met"])
        self.assertFalse(report["complete"])
        self.assertEqual(report["remaining"]["monsters"], 501)

    def test_current_original_sprites_retain_credit(self):
        report = validate_world.delivery_report(catalog(original=5, interiors=30, npcs=4, monsters=2), 10274, 196)
        self.assertEqual(report["delivered_unique_sprites"], 6)
        self.assertEqual(report["remaining"]["npcs"], 496)
        self.assertEqual(report["remaining"]["monsters"], 499)
        self.assertEqual(report["remaining"]["unique_sprites"], 995)

    def test_extra_interiors_cannot_replace_original_backgrounds(self):
        report = validate_world.delivery_report(catalog(original=5, interiors=195), 2000000, 10001)
        self.assertEqual(report["delivered_art"]["backgrounds"], 200)
        self.assertFalse(report["art_targets_met"])
        self.assertEqual(report["remaining"]["backgrounds"], 95)
        self.assertEqual(report["remaining"]["building_interiors"], 0)

    def test_original_interiors_do_not_count_as_extra(self):
        world = catalog(interiors=0)
        world["backgrounds"] = [{"environment": "interior"} for _ in range(200)]
        report = validate_world.delivery_report(world, 2000000, 10001)
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
                self.assertEqual(saved["remaining"]["authored_words"], 1989726)
                self.assertEqual(saved["remaining"]["unique_sprites"], 995)

    def test_strict_command_passes_only_when_complete(self):
        report = validate_world.delivery_report(catalog(), 2000000, 10001)
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(validate_world, "ROOT", pathlib.Path(temporary)), patch.object(validate_world, "inspect", return_value=report):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(validate_world.main(["--require-complete"]), 0)


class OriginalArtworkTests(unittest.TestCase):
    def test_native_resolution_floor(self):
        for size in ((1024, 1536), (1536, 1024), (2048, 3072)):
            self.assertTrue(validate_world.native_sprite_size(size))
        for size in ((512, 768), (1024, 1024), (1000, 1536)):
            self.assertFalse(validate_world.native_sprite_size(size))

    def test_png_metadata_cannot_create_a_unique_painting(self):
        painting = Image.new("RGBA", (4, 4), (180, 30, 20, 255))
        first, second = io.BytesIO(), io.BytesIO()
        painting.save(first, format="PNG")
        metadata = PngInfo()
        metadata.add_text("description", "Different packaging")
        painting.save(second, format="PNG", pnginfo=metadata)
        self.assertNotEqual(hashlib.sha256(first.getvalue()).digest(),
                            hashlib.sha256(second.getvalue()).digest())
        with Image.open(io.BytesIO(first.getvalue())) as left:
            with Image.open(io.BytesIO(second.getvalue())) as right:
                self.assertEqual(validate_world.painting_fingerprint(left),
                                 validate_world.painting_fingerprint(right))

    def test_hidden_rgb_and_transparent_padding_do_not_create_unique_art(self):
        first = Image.new("RGBA", (4, 4), (255, 0, 0, 0))
        second = Image.new("RGBA", (4, 4), (0, 255, 0, 0))
        first.putpixel((1, 1), (50, 100, 150, 255))
        second.putpixel((1, 1), (50, 100, 150, 255))
        padded = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
        padded.paste(first, (2, 2))
        expected = validate_world.painting_fingerprint(first)
        self.assertEqual(expected, validate_world.painting_fingerprint(second))
        self.assertEqual(expected, validate_world.painting_fingerprint(padded))

    def test_visible_changes_remain_distinct(self):
        first = Image.new("RGBA", (4, 4), (180, 30, 20, 255))
        second = first.copy()
        second.putpixel((2, 2), (20, 30, 180, 255))
        self.assertNotEqual(validate_world.painting_fingerprint(first),
                            validate_world.painting_fingerprint(second))

    def test_fully_transparent_images_are_rejected(self):
        with self.assertRaisesRegex(AssertionError, "visible pixels"):
            validate_world.painting_fingerprint(Image.new("RGBA", (4, 4), (0, 0, 0, 0)))

    def test_historical_record_and_retained_native_original_are_accepted(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            source = root / "assets/art/world/su_lan.png"
            source.parent.mkdir(parents=True)
            image = Image.new("RGBA", (1024, 1536), (0, 0, 0, 0))
            image.paste((120, 50, 20, 255), (256, 32, 768, 1504))
            image.save(source)
            record = root / "assets/art/PROVENANCE.md"
            record.write_text("Historical original GPT paintings, retained at native size.")
            entry = {
                "id": "su_lan", "path": "assets/art/world/su_lan.png",
                "native_size": [1024, 1536],
                "provenance": {
                    "kind": "original_painting", "derivation": "none",
                    "source_path": "assets/art/world/su_lan.png",
                    "native_size": [1024, 1536], "record": "assets/art/PROVENANCE.md",
                },
            }
            self.assertEqual(validate_world.validate_sprite_provenance(root, entry),
                             hashlib.sha256(source.read_bytes()).hexdigest())
            entry["provenance"]["native_size"] = [2048, 3072]
            with self.assertRaisesRegex(AssertionError, "source native dimensions"):
                validate_world.validate_sprite_provenance(root, entry)

    def test_declared_derivatives_cannot_count_as_originals(self):
        entry = {"id": "recolored_sprite",
                 "provenance": {"kind": "original_painting", "derivation": "recolor"}}
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(AssertionError, "Variants"):
                validate_world.validate_sprite_provenance(pathlib.Path(temporary), entry)


if __name__ == "__main__":
    unittest.main()
