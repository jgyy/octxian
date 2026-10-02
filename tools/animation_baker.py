"""Bake distinct GPT gesture poses into smooth, looping RGBA sprite sheets."""
import hashlib
import json
import math
import pathlib

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from animation_motion import motion_metrics, require_visible_motion

CELL = (384, 512)
FRAMES = 64
GENERATOR = "keyposes-flow-v1"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pose_pair(sheet, index, columns):
    """Separate the two poses at the transparent seam; align their foot baseline."""
    width, height = sheet.size
    column = sheet.crop((index * width // columns, 0, (index + 1) * width // columns, height))
    alpha = np.asarray(column)[:, :, 3]
    mass = np.count_nonzero(alpha >= 32, axis=1)
    candidates = np.arange(int(height * 0.46), int(height * 0.57))
    quiet = candidates[mass[candidates] == mass[candidates].min()]
    seam = int(quiet[np.argmin(np.abs(quiet - height / 2))])
    crops = [column.crop((0, 0, column.width, seam)),
             column.crop((0, seam, column.width, height))]
    boxes = [crop.getchannel("A").point(lambda value: 255 if value >= 32 else 0).getbbox()
             for crop in crops]
    if any(box is None for box in boxes):
        raise ValueError(f"Missing pose in column {index}")
    left = max(0, min(box[0] for box in boxes) - 4)
    right = min(column.width, max(box[2] for box in boxes) + 4)
    heights = [box[3] - box[1] + 8 for box in boxes]
    scale = min((CELL[0] - 40) / (right - left), (CELL[1] - 40) / max(heights))
    result = []
    for crop, box in zip(crops, boxes):
        top, bottom = max(0, box[1] - 4), min(crop.height, box[3] + 4)
        cut = crop.crop((left, top, right, bottom))
        cut = cut.resize((max(1, round(cut.width * scale)), max(1, round(cut.height * scale))),
                         Image.Resampling.LANCZOS)
        image = Image.new("RGBA", CELL)
        image.alpha_composite(cut, ((CELL[0] - cut.width) // 2, CELL[1] - 20 - cut.height))
        result.append(image)
    require_visible_motion(motion_metrics(*result), f"GPT pose column {index}")
    return result


def premultiply(image):
    pixels = np.asarray(image, dtype=np.float32) / 255
    pixels[:, :, :3] *= pixels[:, :, 3:4]
    return pixels


def optical_flow(a, b):
    gray_a = cv2.cvtColor(np.uint8(np.clip(a[:, :, :3] * 255, 0, 255)), cv2.COLOR_RGB2GRAY)
    gray_b = cv2.cvtColor(np.uint8(np.clip(b[:, :, :3] * 255, 0, 255)), cv2.COLOR_RGB2GRAY)
    forward = cv2.calcOpticalFlowFarneback(gray_a, gray_b, None, 0.5, 5, 41, 7, 7, 1.5, 0)
    backward = cv2.calcOpticalFlowFarneback(gray_b, gray_a, None, 0.5, 5, 41, 7, 7, 1.5, 0)
    return cv2.GaussianBlur(forward, (5, 5), 0.8), cv2.GaussianBlur(backward, (5, 5), 0.8)


def render_frame(a, b, flows, frame, motion, grid):
    phase = 2 * math.pi * frame / FRAMES
    amount = 0.5 - 0.5 * math.cos(phase)
    if motion == "channeling":
        amount = amount ** 0.8
    elif motion == "resolve":
        amount = amount * amount * (3 - 2 * amount)
    elif motion == "wind":
        amount = 0.5 - 0.5 * math.cos(phase + 0.45)
    xx, yy = grid
    forward, backward = flows
    # Blend motion-compensated, premultiplied samples: transparent edges stay clean.
    pose_a = cv2.remap(a, xx - forward[:, :, 0] * amount,
                     yy - forward[:, :, 1] * amount, cv2.INTER_LINEAR)
    pose_b = cv2.remap(b, xx - backward[:, :, 0] * (1 - amount),
                     yy - backward[:, :, 1] * (1 - amount), cv2.INTER_LINEAR)
    pixels = pose_a * (1 - amount) + pose_b * amount
    # Independently move loose silk and hair, leaving the feet anchored.
    strength = {"idle": 3.5, "channeling": 6.0, "wind": 13.0, "resolve": 5.0}[motion]
    lateral = 1 - np.exp(-((xx - CELL[0] / 2) / 75) ** 2)
    cloth = np.clip((yy - 200) / 240, 0, 1) * lateral
    hair = np.exp(-((yy - 145) / 85) ** 2) * lateral
    anchored = np.clip((CELL[1] - 20 - yy) / 220, 0, 1)
    sway = strength * (cloth * math.sin(phase + 0.6) + hair * math.sin(phase + 1.0))
    sway += 2.2 * math.sin(phase) * anchored
    lift = 1.6 * math.sin(phase + 0.4) * anchored
    pixels = cv2.remap(pixels, np.float32(xx - sway), np.float32(yy - lift), cv2.INTER_LINEAR)
    alpha = pixels[:, :, 3:4]
    pixels[:, :, :3] = np.divide(pixels[:, :, :3], alpha,
                                  out=np.zeros_like(pixels[:, :, :3]), where=alpha > 0.001)
    image = Image.fromarray(np.uint8(np.clip(pixels * 255, 0, 255)))
    if motion in ("channeling", "resolve"):
        aura = Image.new("RGBA", CELL)
        draw = ImageDraw.Draw(aura)
        color = (149, 229, 213, 65) if motion == "channeling" else (231, 198, 126, 55)
        for particle in range(8):
            theta = phase + particle * math.pi / 4
            x = CELL[0] / 2 + math.cos(theta) * 166
            y = 265 + math.sin(theta) * 150
            draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill=color)
        image = Image.alpha_composite(image, aura.filter(ImageFilter.GaussianBlur(1.2)))
    return image


def bake_sprites(root, out, force=False):
    catalog_bytes = (root / "data/wardrobe.json").read_bytes()
    catalog = json.loads(catalog_bytes)
    destination = out / "sprites"
    destination.mkdir(parents=True, exist_ok=True)
    manifest_path = destination / "manifest.json"
    previous = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    baker_hash = digest(pathlib.Path(__file__))
    expected = len(catalog["characters"]) * len(catalog["outfits"]) * len(catalog["motions"]) * FRAMES
    manifest = {"version": 3, "generator": GENERATOR, "baker_sha256": baker_hash,
                "source": "GPT Images", "derivation": "distinct gesture key poses, bidirectional optical-flow tweening, cloth and hair motion",
                "frame_count": expected, "fps": catalog["fps"], "cell": list(CELL),
                "key_poses_per_appearance": 2,
                "catalog_sha256": hashlib.sha256(catalog_bytes).hexdigest(), "outfits": {}}
    yy, xx = np.mgrid[:CELL[1], :CELL[0]].astype(np.float32)
    generated = 0
    for outfit in catalog["outfits"]:
        outfit_id = outfit["id"]
        source_hash = digest(root / outfit["source"])
        pose_hash = digest(root / outfit["poses"])
        sheet = Image.open(root / outfit["poses"]).convert("RGBA")
        if sheet.getchannel("A").getextrema()[0] == 255:
            raise ValueError(f"{outfit_id}: GPT pose sheet needs transparency")
        info = {"source": outfit["source"], "source_sha256": source_hash,
                "pose_source": outfit["poses"], "pose_source_sha256": pose_hash, "characters": {}}
        manifest["outfits"][outfit_id] = info
        cached = previous.get("outfits", {}).get(outfit_id, {})
        reusable = (previous.get("generator") == GENERATOR and previous.get("baker_sha256") == baker_hash
                    and previous.get("cell") == list(CELL) and cached.get("pose_source_sha256") == pose_hash
                    and cached.get("source_sha256") == source_hash)
        suffix = "" if outfit_id == "sect" else "_" + outfit_id
        for index, character in enumerate(catalog["characters"]):
            info["characters"][character] = {}
            pair = None
            for motion in catalog["motions"]:
                path = destination / f"{character}{suffix}_{motion}.png"
                old = cached.get("characters", {}).get(character, {}).get(motion, {})
                if not force and reusable and path.exists() and old.get("frames") == FRAMES and digest(path) == old.get("sha256"):
                    info["characters"][character][motion] = old
                    continue
                if pair is None:
                    print(f"Preparing distinct poses: {character}/{outfit_id}", flush=True)
                    pair = pose_pair(sheet, index, len(catalog["characters"]))
                    arrays = [premultiply(image) for image in pair]
                    flows = optical_flow(*arrays)
                frames = [render_frame(*arrays, flows, index, motion, (xx, yy)) for index in range(FRAMES)]
                metrics = motion_metrics(frames[0], frames[FRAMES // 2])
                require_visible_motion(metrics, f"{character}/{outfit_id}/{motion}")
                atlas = Image.new("RGBA", (CELL[0] * 8, CELL[1] * 8))
                for index, image in enumerate(frames):
                    atlas.alpha_composite(image, ((index % 8) * CELL[0], (index // 8) * CELL[1]))
                atlas.save(path, compress_level=6)
                info["characters"][character][motion] = {
                    "path": str(path.relative_to(root)), "frames": FRAMES,
                    "sha256": digest(path), "visible_motion": metrics}
                generated += FRAMES
                print(f"Baked {character}/{outfit_id}/{motion}: {FRAMES} frames, body change {metrics['changed_fraction']:.1%}", flush=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Wardrobe: {expected:,} visibly animated frames; {generated:,} newly baked.", flush=True)
