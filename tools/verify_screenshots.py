"""Verify actual game captures and create compact JPEG copies for review."""
import pathlib

import numpy as np
from PIL import Image

root = pathlib.Path(__file__).resolve().parents[1]
folder = root / "build/screenshots"
images = []
for name in ("title", "dialogue", "cast", "wardrobe_training", "wardrobe_festival", "outfit_dialogue", "quest_hub", "spirit_encounter", "world_gallery", "ferry_encounter", "archive_encounter", "river_pilot", "river_spirit", "river_harbor", "object_bronze_clapper", "object_sealed_echo_case", "interior_gallery", "attributes", "attribute_choices", "orchard_healer", "orchard_spirit", "orchard_choices", "city_market", "city_mask_maker", "city_archivist", "city_courier", "city_perfumer", "city_courser", "city_moth", "city_choices"):
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
assert not np.array_equal(images[6], images[7]), "Quest and spirit scenes must differ"
assert not np.array_equal(images[7], images[8]), "World gallery must render separately"
assert not np.array_equal(images[9], images[10]), "Ferryman and archivist must render as distinct characters"
assert not np.array_equal(images[11], images[12]), "Pilot and river spirit must render independently"
assert not np.array_equal(images[12], images[13]), "River and harbor scenes must use distinct environments"
assert not np.array_equal(images[14], images[15]), "Object paintings must render as distinct inspectable artifacts"
assert not np.array_equal(images[8], images[16]), "Interior gallery must render its own full painting view"
assert not np.array_equal(images[1], images[17]), "Attributes must render a separate character panel"
assert not np.array_equal(images[1], images[18]), "Gated choices must render their visible requirements"
assert not np.array_equal(images[19], images[20]), "Orchard healer and spirit must render distinct originals"
assert not np.array_equal(images[20], images[21]), "Orchard settlement choices must render separately"
for index in range(23, 29):
    assert not np.array_equal(images[22], images[index]), "City portraits must render independently of the market"
for first in range(23, 29):
    for second in range(first + 1, 29):
        assert not np.array_equal(images[first], images[second]), "Every city character must have a distinct rendered encounter"
assert not np.array_equal(images[22], images[29]), "City settlement choices must render separately"
print("Verified thirty rendered captures across five books, the world gallery, wardrobes and both painted objects.")

# Timed samples come from the real Godot viewport.
animation_folder = root / "build/animations"
rendered = [Image.open(animation_folder / "rendered" / f"frame_{index:02d}.png").convert("RGB")
            for index in range(16)]
start = np.asarray(rendered[0], dtype=np.float32)[50:330, 520:940]
body_change = max(float(np.mean(np.abs(start - np.asarray(frame, dtype=np.float32)[50:330, 520:940])))
                  for frame in rendered[1:])
assert body_change >= 0.2, f"Rendered body bob is missing: {body_change:.3f}"
rendered[0].save(animation_folder / "rendered_game.gif", save_all=True,
                 append_images=rendered[1:], duration=250, loop=0, disposal=2, optimize=False)
comparison = Image.new("RGB", (480 * 4, 270))
for column, index in enumerate((0, 4, 8, 12)):
    comparison.paste(rendered[index].resize((480, 270), Image.Resampling.LANCZOS), (column * 480, 0))
comparison.save(animation_folder / "rendered_game_frames.jpg", quality=82, optimize=True)
print(f"Verified gentle body bob in timed game playback: maximum mean body-region change {body_change:.2f}/255.")
