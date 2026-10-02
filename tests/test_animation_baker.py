"""Protect intact portraits from stretching and split-body regressions."""
import pathlib
import sys
import unittest

from PIL import Image, ImageDraw

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
from animation_baker import CELL, extract_portrait


class PortraitTests(unittest.TestCase):
    def test_selects_the_resting_pose_without_mixing_in_the_second_pose(self):
        sheet = Image.new("RGBA", (200, 600))
        draw = ImageDraw.Draw(sheet)
        draw.rectangle((20, 20, 180, 270), fill=(20, 100, 200, 255))
        draw.rectangle((20, 330, 180, 580), fill=(240, 40, 20, 255))
        portrait = extract_portrait(sheet, 0, 1)
        self.assertEqual(portrait.size, CELL)
        self.assertEqual(portrait.getpixel((192, 300)), (20, 100, 200, 255))
        self.assertEqual(portrait.getpixel((0, 0))[3], 0)

    def test_preserves_the_proportions_of_a_wide_portrait(self):
        sheet = Image.new("RGBA", (600, 600))
        ImageDraw.Draw(sheet).rectangle((20, 40, 580, 240), fill=(40, 120, 80, 255))
        box = extract_portrait(sheet, 0, 1).getchannel("A").point(lambda value: 255 if value >= 160 else 0).getbbox()
        self.assertAlmostEqual((box[2] - box[0]) / (box[3] - box[1]), 561 / 201, delta=0.08)

    def test_missing_portrait_fails_instead_of_publishing_an_empty_character(self):
        with self.assertRaises(ValueError):
            extract_portrait(Image.new("RGBA", (200, 600)), 0, 1)


if __name__ == "__main__":
    unittest.main()
