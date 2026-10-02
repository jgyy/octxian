"""Publish GIFs and contact sheets decoded from the actual game sprite atlases."""
import json
import pathlib

from PIL import Image, ImageDraw
from animation_baker import pose_pair

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "build/animations"
OUT.mkdir(parents=True, exist_ok=True)
catalog = json.loads((ROOT / "data/wardrobe.json").read_text())
manifest = json.loads((ROOT / "assets/generated/sprites/manifest.json").read_text())
width, height = manifest["cell"]
TILE = (192, 256)


def read_frames(character, outfit, motion):
    info = manifest["outfits"][outfit]["characters"][character][motion]
    sheet = Image.open(ROOT / info["path"]).convert("RGBA")
    return [sheet.crop(((i % 8) * width, (i // 8) * height,
                       (i % 8 + 1) * width, (i // 8 + 1) * height))
            .resize(TILE, Image.Resampling.LANCZOS) for i in range(64)]


for outfit in catalog["outfits"]:
    cast = [read_frames(character, outfit["id"], "idle") for character in catalog["characters"]]
    panels = []
    for index in range(64):
        panel = Image.new("RGB", (TILE[0] * 4, TILE[1] + 42), (13, 29, 32))
        draw = ImageDraw.Draw(panel)
        draw.text((12, 8), f"{outfit['name']} - frame {index:02d}/63", fill=(235, 218, 170))
        for column, frames in enumerate(cast):
            panel.paste(frames[index], (column * TILE[0], 34), frames[index])
        panels.append(panel)
    # GIF durations are in 10ms units: alternating 60/70/60/60 = 16 fps.
    panels[0].save(OUT / f"{outfit['id']}.gif", save_all=True, append_images=panels[1:],
                   duration=[60, 70, 60, 60] * 16, loop=0, disposal=2, optimize=False)
    contact = Image.new("RGB", (TILE[0] * 8, (TILE[1] + 28) * 4), (13, 29, 32))
    draw = ImageDraw.Draw(contact)
    for row, frames in enumerate(cast):
        for column, index in enumerate(range(0, 64, 8)):
            x, y = column * TILE[0], row * (TILE[1] + 28)
            draw.text((x + 4, y + 4), f"{catalog['characters'][row]} f{index:02d}", fill=(235, 218, 170))
            contact.paste(frames[index], (x, y + 24), frames[index])
    contact.save(OUT / f"{outfit['id']}_frames.jpg", quality=78, optimize=True)
    print(f"Previewed actual {outfit['id']} atlas frames as GIF and eight-pose contact sheet.", flush=True)

motions = [read_frames("lin_yue", "sect", motion) for motion in catalog["motions"]]
panels = []
for index in range(64):
    panel = Image.new("RGB", (TILE[0] * 4, TILE[1] + 42), (13, 29, 32))
    draw = ImageDraw.Draw(panel)
    for column, frames in enumerate(motions):
        draw.text((column * TILE[0] + 6, 8), catalog["motions"][column], fill=(235, 218, 170))
        panel.paste(frames[index], (column * TILE[0], 34), frames[index])
    panels.append(panel)
panels[0].save(OUT / "motions.gif", save_all=True, append_images=panels[1:],
               duration=[60, 70, 60, 60] * 16, loop=0, disposal=2, optimize=False)

rigs = json.loads((ROOT / "data/animation_rigs.json").read_text())["outfits"]
for outfit in catalog["outfits"]:
    source = Image.open(ROOT / outfit["poses"]).convert("RGBA")
    guide = Image.new("RGB", (width * 4, height * 2), (13, 29, 32))
    draw = ImageDraw.Draw(guide)
    for column, character in enumerate(catalog["characters"]):
        pair, points = pose_pair(source, column, 4, rigs[outfit["id"]][character])
        for row, (pose, joints) in enumerate(zip(pair, points)):
            x, y = column * width, row * height
            guide.paste(pose, (x, y), pose)
            for first, second in [(0, 5), (5, 10)]:
                draw.line((x + joints[first, 0], y + joints[first, 1],
                           x + joints[second, 0], y + joints[second, 1]), fill=(255, 200, 50), width=2)
            for index in (0, 5, 10, 15, 20):
                px, py = joints[index] + [x, y]
                draw.ellipse((px - 3, py - 3, px + 3, py + 3), fill=(255, 80, 80))
    guide.save(OUT / f"{outfit['id']}_rig.jpg", quality=82, optimize=True)
