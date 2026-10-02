"""Regression examples: reject the previous weak motion and false positives."""
import pathlib
import sys
import unittest

import cv2
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
from animation_motion import motion_metrics, require_visible_motion


def figure(raised=False):
    image = Image.new("RGBA", (384, 512))
    draw = ImageDraw.Draw(image)
    draw.ellipse((164, 40, 216, 96), fill=(226, 186, 146, 255))
    draw.rectangle((158, 95, 222, 280), fill=(70, 150, 135, 255))
    draw.polygon([(158, 230), (222, 230), (256, 470), (126, 470)], fill=(100, 180, 165, 255))
    if raised:
        draw.line([(220, 120), (282, 172), (318, 66)], fill=(226, 186, 146, 255), width=24)
    else:
        draw.line([(220, 120), (235, 190), (240, 250)], fill=(226, 186, 146, 255), width=24)
    draw.line([(160, 120), (137, 185), (146, 245)], fill=(226, 186, 146, 255), width=24)
    return image


class VisibleMotionTests(unittest.TestCase):
    def rejected(self, a, b):
        with self.assertRaises(AssertionError):
            require_visible_motion(motion_metrics(a, b), "regression fixture")

    def test_identical_portrait(self):
        self.rejected(figure(), figure())

    def test_previous_two_pixel_sway(self):
        source = figure()
        shifted = Image.new("RGBA", source.size)
        shifted.alpha_composite(source, (2, 2))
        self.rejected(source, shifted)

    def test_previous_breathing_and_wind_mesh(self):
        source = figure()
        yy, xx = np.mgrid[:source.height, :source.width].astype(np.float32)
        sample_x = (xx - source.width / 2) / 1.008 + source.width / 2
        sample_x -= 5.0 * (0.1 + yy / source.height) ** 2
        shifted = cv2.remap(np.asarray(source), sample_x, yy - 2.2, cv2.INTER_LINEAR)
        self.rejected(source, Image.fromarray(shifted))

    def test_whole_portrait_panning(self):
        source = figure()
        shifted = Image.new("RGBA", source.size)
        shifted.alpha_composite(source, (20, 0))
        self.rejected(source, shifted)

    def test_particles_without_body_movement(self):
        source = figure()
        other = source.copy()
        draw = ImageDraw.Draw(other)
        for x in range(30, 360, 40):
            draw.ellipse((x, 15, x + 12, 27), fill=(150, 225, 210, 65))
        self.rejected(source, other)

    def test_tint_without_articulation(self):
        source = figure()
        pixels = np.asarray(source).copy()
        pixels[:, :, :3] = 240 - pixels[:, :, :3] // 2
        self.rejected(source, Image.fromarray(pixels))

    def test_visible_hand_and_forearm_gesture(self):
        require_visible_motion(motion_metrics(figure(), figure(True)), "raised hand")


if __name__ == "__main__":
    unittest.main()
