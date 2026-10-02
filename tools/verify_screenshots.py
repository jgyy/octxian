"""Verify actual game captures and create compact JPEG copies for review."""
import pathlib

import numpy as np
from PIL import Image

root = pathlib.Path(__file__).resolve().parents[1]
folder = root / "build/screenshots"
images = []
for name in ("title", "dialogue", "cast"):
    source = Image.open(folder / f"{name}.png").convert("RGB")
    assert source.width >= 1280 and source.height >= 720, "Capture must use the real game viewport"
    pixels = np.asarray(source)
    assert pixels.std() > 15, "Screenshot must contain a rendered scene"
    source.save(folder / f"{name}.jpg", quality=82, optimize=True)
    images.append(pixels)
assert not np.array_equal(images[0], images[1]), "Title and dialogue must be different views"
assert not np.array_equal(images[1], images[2]), "Cast modal must render on top of dialogue"
print("Verified three distinct rendered game captures.")
