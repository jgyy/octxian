"""Reject crossfades and ensure crisp bodies with solid articulated hands."""
import pathlib
import sys
import unittest

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
from animation_baker import premultiply, render_frame
from pose_rig import build_points, intermediate_points, arm_layers, move_segment, place_hand, require_solid_hands
from test_animation_motion import figure


class HandPathTests(unittest.TestCase):
    def setUp(self):
        self.images = [figure(), figure(True)]
        specs = [
            {"hand": [240, 250], "elbow": [235, 190], "shoulder": [220, 120],
             "face": [190, 68], "hip": [190, 240]},
            {"hand": [318, 66], "elbow": [282, 172], "shoulder": [220, 120],
             "face": [190, 68], "hip": [190, 240]},
        ]
        self.points = [build_points(image, spec, lambda point: point, image.size)
                       for image, spec in zip(self.images, specs)]
        yy, xx = np.mgrid[:512, :384].astype(np.float32)
        self.grid = xx, yy

    def palm_alpha(self, image, point):
        x, y = np.rint(point).astype(int)
        return float(np.mean(np.asarray(image)[y - 2:y + 3, x - 2:x + 3, 3]))

    def render(self, images=None, frame=16):
        arrays = [premultiply(image) for image in (images or self.images)]
        layers = [arm_layers(array, points, 14) for array, points in zip(arrays, self.points)]
        return render_frame(*arrays, layers, self.points, frame, "idle", self.grid)

    def test_crossfade_leaves_the_intermediate_hand_missing(self):
        halfway = intermediate_points(self.points, 0.5)
        self.assertLess(self.palm_alpha(Image.blend(*self.images, 0.5), halfway[0]), 160)

    def test_rig_keeps_the_moving_palm_solid(self):
        halfway = intermediate_points(self.points, 0.5)
        self.assertGreaterEqual(self.palm_alpha(self.render(), halfway[0]), 200)

    def test_source_body_stays_sharp_without_pose_crossfading(self):
        changed = self.images[1].copy()
        draw = ImageDraw.Draw(changed)
        draw.rectangle((165, 240, 205, 330), fill=(240, 40, 30, 255))
        normal = np.asarray(self.render())
        with_different_body = np.asarray(self.render([self.images[0], changed]))
        np.testing.assert_array_equal(normal[290:310, 175:195], with_different_body[290:310, 175:195])

    def test_identity_arm_transform_keeps_pixels(self):
        layer = premultiply(self.images[0])
        start, end = self.points[0][5], self.points[0][0]
        result = move_segment(layer, start, end, start, end)
        self.assertLess(float(np.mean(np.abs(result - layer))), 0.001)

    def test_hand_follows_an_outward_arc(self):
        halfway = intermediate_points(self.points, 0.5)
        straight = (self.points[0][0] + self.points[1][0]) / 2
        self.assertGreater(float(halfway[0, 0] - straight[0]), 20)

    def test_cutout_hand_stays_opaque_along_the_path(self):
        for frame in (8, 16, 24, 40, 48, 56):
            amount = 0.5 - 0.5 * np.cos(2 * np.pi * frame / 64)
            point = intermediate_points(self.points, amount)[0]
            self.assertGreaterEqual(self.palm_alpha(self.render(frame=frame), point), 200)

    def test_static_hands_cannot_pass_gesture_validation(self):
        with self.assertRaises(AssertionError):
            require_solid_hands([self.images[0]] * 64, [self.points[0], self.points[0]], "idle")


if __name__ == "__main__":
    unittest.main()
