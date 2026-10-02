"""Check that hands travel through solid intermediate positions."""
import pathlib
import sys
import unittest

import numpy as np
from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
from pose_rig import build_points, intermediate_points, triangulate, warp_pose
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
        self.triangles = triangulate(self.points, self.images[0].size)
        yy, xx = np.mgrid[:512, :384].astype(np.float32)
        self.grid = xx, yy

    def palm_alpha(self, image, point):
        x, y = np.rint(point).astype(int)
        return float(np.mean(np.asarray(image)[y - 2:y + 3, x - 2:x + 3, 3]))

    def test_crossfade_leaves_the_intermediate_hand_missing(self):
        halfway = intermediate_points(self.points, 0.5)
        crossfade = Image.blend(*self.images, 0.5)
        self.assertLess(self.palm_alpha(crossfade, halfway[0]), 160)

    def test_rig_keeps_the_moving_palm_solid(self):
        halfway = intermediate_points(self.points, 0.5)
        warped = [warp_pose(np.asarray(image, dtype=np.float32), points, halfway,
                            self.triangles, self.grid)
                  for image, points in zip(self.images, self.points)]
        result = Image.fromarray(np.uint8((warped[0] + warped[1]) / 2))
        self.assertGreaterEqual(self.palm_alpha(result, halfway[0]), 200)

    def test_pose_endpoints_keep_their_original_pixels(self):
        for image, points in zip(self.images, self.points):
            source = np.asarray(image, dtype=np.float32)
            result = warp_pose(source, points, points, self.triangles, self.grid)
            self.assertLess(float(np.mean(np.abs(result - source))), 0.1)

    def test_hand_follows_an_outward_arc(self):
        halfway = intermediate_points(self.points, 0.5)
        straight = (self.points[0][0] + self.points[1][0]) / 2
        self.assertGreater(float(halfway[0, 0] - straight[0]), 20)
        self.assertLess(float(halfway[0, 1]), float(straight[1]))


if __name__ == "__main__":
    unittest.main()
