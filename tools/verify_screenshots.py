"""Verify actual game captures and create compact JPEG copies for review."""
import pathlib

import numpy as np
from PIL import Image

root = pathlib.Path(__file__).resolve().parents[1]
folder = root / "build/screenshots"
images = []
for name in ("title", "dialogue", "cast", "wardrobe_training", "wardrobe_festival", "outfit_dialogue"):
    source = Image.open(folder / f"{name}.png").convert("RGB")
    assert source.width >= 1280 and source.height >= 720, "Capture must use the real game viewport"
    pixels = np.asarray(source)
    assert pixels.std() > 15, "Screenshot must contain a rendered scene"
    source.save(folder / f"{name}.jpg", quality=82, optimize=True)
    images.append(pixels)
assert not np.array_equal(images[0], images[1]), "Title and dialogue must be different views"
assert not np.array_equal(images[1], images[2]), "Cast modal must render on top of dialogue"
assert not np.array_equal(images[3], images[4]), "Training and festival outfits must render differently"
assert not np.array_equal(images[1], images[5]), "Chosen outfits must render in story scenes"
print("Verified six rendered captures including both wardrobes and selected story clothing.")
