"""Preview the intact portraits with the same whole-body bob used by Godot."""
import json
import math
import pathlib

from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "build/animations"
OUT.mkdir(parents=True, exist_ok=True)
catalog = json.loads((ROOT / "data/wardrobe.json").read_text())
manifest = json.loads((ROOT / "assets/generated/sprites/manifest.json").read_text())
TILE = (192, 256)
SAMPLES = 64


def read_frames(character, outfit, motion):
    info = manifest["outfits"][outfit]["characters"][character]
    with Image.open(ROOT / info["path"]) as source:
        portrait = source.convert("RGBA").resize(TILE, Image.Resampling.LANCZOS)
    amplitude = catalog["bob_pixels"][motion] * TILE[1] / 730
    frames = []
    for index in range(SAMPLES):
        frame = Image.new("RGBA", TILE)
        offset = round(math.sin(math.tau * index / SAMPLES) * amplitude)
        frame.alpha_composite(portrait, (0, offset))
        frames.append(frame)
    return frames


def save_loop(path, panels):
    panels[0].save(path, save_all=True, append_images=panels[1:],
                   duration=[60, 70, 60, 60] * 16, loop=0, disposal=2, optimize=True)


for outfit in catalog["outfits"]:
    cast = [read_frames(character, outfit["id"], "idle") for character in catalog["characters"]]
    panels = []
    for index in range(SAMPLES):
        panel = Image.new("RGB", (TILE[0] * 4, TILE[1] + 42), (13, 29, 32))
        draw = ImageDraw.Draw(panel)
        draw.text((12, 8), f"{outfit['name']} - whole-body bob", fill=(235, 218, 170))
        for column, frames in enumerate(cast):
            panel.paste(frames[index], (column * TILE[0], 34), frames[index])
        panels.append(panel)
    save_loop(OUT / f"{outfit['id']}.gif", panels)
    contact = Image.new("RGB", (TILE[0] * 8, (TILE[1] + 28) * 4), (13, 29, 32))
    draw = ImageDraw.Draw(contact)
    for row, frames in enumerate(cast):
        for column, index in enumerate(range(0, SAMPLES, 8)):
            x, y = column * TILE[0], row * (TILE[1] + 28)
            draw.text((x + 4, y + 4), f"{catalog['characters'][row]} t{index:02d}", fill=(235, 218, 170))
            contact.paste(frames[index], (x, y + 24), frames[index])
    contact.save(OUT / f"{outfit['id']}_frames.jpg", quality=78, optimize=True)
    print(f"Previewed intact {outfit['id']} portraits with a gentle body bob.", flush=True)

motions = [read_frames("lin_yue", "sect", motion) for motion in catalog["motions"]]
panels = []
for index in range(SAMPLES):
    panel = Image.new("RGB", (TILE[0] * 4, TILE[1] + 42), (13, 29, 32))
    draw = ImageDraw.Draw(panel)
    for column, frames in enumerate(motions):
        draw.text((column * TILE[0] + 6, 8), catalog["motions"][column], fill=(235, 218, 170))
        panel.paste(frames[index], (column * TILE[0], 34), frames[index])
    panels.append(panel)
save_loop(OUT / "motions.gif", panels)
