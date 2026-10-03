"""Protect retained native sources from resizing, flattening and source substitution."""
import json
import pathlib
import tempfile
import unittest
from PIL import Image, ImageDraw
from tools.animation_baker import CELL, bake_sprites, digest, validate_native_portrait


class PortraitTests(unittest.TestCase):
    def test_native_bytes_survive_generation_and_cache_reuse(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            (root / "data").mkdir()
            source = root / "portrait.png"
            image = Image.new("RGBA", CELL)
            ImageDraw.Draw(image).rectangle((200, 100, 800, 1400), fill=(40, 120, 80, 255))
            image.save(source)
            catalog = {"characters": ["lin_yue"], "outfits": [
                {"id": "sect", "portraits": {"lin_yue": "portrait.png"}}]}
            (root / "data/wardrobe.json").write_text(json.dumps(catalog))
            output = root / "assets/generated"
            bake_sprites(root, output)
            runtime = output / "sprites/lin_yue.png"
            self.assertEqual(runtime.read_bytes(), source.read_bytes())
            original_hash = digest(runtime)
            bake_sprites(root, output)
            self.assertEqual(digest(runtime), original_hash)
            manifest = json.loads((output / "sprites/manifest.json").read_text())
            self.assertEqual(manifest["outfits"]["sect"]["characters"]["lin_yue"]["native_size"], list(CELL))

    def test_low_resolution_flattened_and_empty_sources_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = pathlib.Path(temporary) / "invalid.png"
            for mode, size, color in [("RGBA", (384, 512), (1, 2, 3, 255)),
                                      ("RGB", CELL, (1, 2, 3)),
                                      ("RGBA", CELL, (0, 0, 0, 0)),
                                      ("RGBA", CELL, (1, 2, 3, 255))]:
                with self.subTest(mode=mode, size=size, color=color):
                    Image.new(mode, size, color).save(path)
                    with self.assertRaises(ValueError):
                        validate_native_portrait(path)


if __name__ == "__main__":
    unittest.main()
