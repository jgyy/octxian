"""Bake distinct GPT gesture poses into smooth, looping RGBA sprite sheets."""
import hashlib
import json
import math
import pathlib

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from animation_motion import motion_metrics, require_visible_motion
from pose_rig import build_points, intermediate_points, pose_amount, require_solid_hands, arm_layers, move_segment, composite_over, align_body_donor, move_palm

CELL = (384, 512)
FRAMES = 64
GENERATOR = "cutout-gesture-v3"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pose_pair(sheet, index, columns, rig):
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
    for row, crop in enumerate(crops):
        pixels = np.asarray(crop).copy()
        mask = np.uint8(pixels[:, :, 3] >= 16)
        linked = cv2.dilate(mask, np.ones((3, 3), np.uint8))
        count, labels, stats, _ = cv2.connectedComponentsWithStats(linked, 8)
        if count > 1:
            primary = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
            keep = np.uint8(labels == primary) * 255
            keep = np.asarray(Image.fromarray(keep).filter(ImageFilter.GaussianBlur(0.6)), dtype=np.float32) / 255
            pixels[:, :, 3] = np.uint8(pixels[:, :, 3] * keep)
            crops[row] = Image.fromarray(pixels)
    boxes = [crop.getchannel("A").point(lambda value: 255 if value >= 32 else 0).getbbox()
             for crop in crops]
    if any(box is None for box in boxes):
        raise ValueError(f"Missing pose in column {index}")
    left = max(0, min(box[0] for box in boxes) - 4)
    right = min(column.width, max(box[2] for box in boxes) + 4)
    heights = [box[3] - box[1] + 8 for box in boxes]
    scale = min((CELL[0] - 40) / (right - left), (CELL[1] - 40) / max(heights))
    target_width = max(1, round((right - left) * scale))
    result, points = [], []
    for row, (crop, box) in enumerate(zip(crops, boxes)):
        top, bottom = max(0, box[1] - 4), min(crop.height, box[3] + 4)
        cut = crop.crop((left, top, right, bottom))
        cut = cut.resize((target_width, CELL[1] - 40),
                         Image.Resampling.LANCZOS)
        image = Image.new("RGBA", CELL)
        image.alpha_composite(cut, ((CELL[0] - cut.width) // 2, CELL[1] - 20 - cut.height))
        result.append(image)
        row_offset = 0 if row == 0 else seam
        origin_x = index * width // columns
        def transform(point):
            return np.float32([
                (CELL[0] - cut.width) // 2 + (point[0] - origin_x - left) * cut.width / (right - left),
                20 + (point[1] - row_offset - top) * cut.height / (bottom - top)])
        points.append(build_points(sheet, rig[row], transform, CELL))
    require_visible_motion(motion_metrics(*result), f"GPT pose column {index}")
    return result, points


def premultiply(image):
    pixels = np.asarray(image, dtype=np.float32) / 255
    pixels[:, :, :3] *= pixels[:, :, 3:4]
    return pixels


def render_frame(a, b, layers, rig, frame, motion, grid):
    phase = 2 * math.pi * frame / FRAMES
    amount = pose_amount(phase, motion)
    xx, yy = grid
    intermediate = intermediate_points(rig, amount)
    pixels = layers[0][0].copy()
    # Independently move loose silk and hair, leaving the feet anchored.
    strength = {"idle": 3.5, "channeling": 6.0, "wind": 13.0, "resolve": 5.0}[motion]
    lateral = 1 - np.exp(-((xx - CELL[0] / 2) / 75) ** 2)
    cloth = np.clip((yy - 200) / 240, 0, 1) * lateral
    hair = np.exp(-((yy - 145) / 85) ** 2) * lateral
    anchored = np.clip((CELL[1] - 20 - yy) / 220, 0, 1)
    sway = strength * (cloth * math.sin(phase + 0.6) + hair * math.sin(phase + 1.0))
    sway += 2.2 * math.sin(phase) * anchored
    lift = 1.6 * math.sin(phase + 0.4) * anchored
    # Neck-anchored head tilt keeps a single, sharp face.
    neck = rig[0][15] + np.float32([0, 48])
    angle = math.radians(2.8) * math.sin(phase + 0.2)
    head_weight = np.clip((neck[1] + 8 - yy) / 65, 0, 1)
    rotated_x = (xx - neck[0]) * math.cos(angle) + (yy - neck[1]) * math.sin(angle) + neck[0]
    rotated_y = -(xx - neck[0]) * math.sin(angle) + (yy - neck[1]) * math.cos(angle) + neck[1]
    map_x = xx - sway + (rotated_x - xx) * head_weight
    map_y = yy - lift + (rotated_y - yy) * head_weight
    pixels = cv2.remap(pixels, np.float32(map_x), np.float32(map_y), cv2.INTER_LINEAR)
    # A single texture set keeps the moving arm and palm sharp and opaque.
    for layer_index, start_index, end_index in [(1, 10, 5), (2, 5, 0)]:
        segment = move_segment(layers[1][layer_index], rig[1][start_index], rig[1][end_index],
                               intermediate[start_index], intermediate[end_index])
        pixels = composite_over(pixels, segment)
    pixels = composite_over(pixels, move_palm(layers[1][3], rig[1], intermediate))
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
    rig_path = root / "data/animation_rigs.json"
    rigs = json.loads(rig_path.read_text())["outfits"]
    rig_hash = digest(rig_path)
    rig_code_hash = digest(root / "tools/pose_rig.py")
    expected = len(catalog["characters"]) * len(catalog["outfits"]) * len(catalog["motions"]) * FRAMES
    manifest = {"version": 3, "generator": GENERATOR, "baker_sha256": baker_hash, "rig_sha256": rig_hash, "rig_code_sha256": rig_code_hash,
                "source": "GPT Images", "derivation": "distinct gesture key poses, two-bone cutout arm rig, single sharp body, cloth and hair motion",
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
                    and previous.get("rig_sha256") == rig_hash and previous.get("rig_code_sha256") == rig_code_hash
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
                    pair, rig_points = pose_pair(sheet, index, len(catalog["characters"]), rigs[outfit_id][character])
                    arrays = [premultiply(image) for image in pair]
                    radius = {"sect": 26, "training": 14, "festival": 17}[outfit_id]
                    donor = align_body_donor(arrays[1], rig_points[1], rig_points[0])
                    layers = [arm_layers(arrays[0], rig_points[0], radius, donor),
                              arm_layers(arrays[1], rig_points[1], radius)]
                frames = [render_frame(*arrays, layers, rig_points, index, motion, (xx, yy)) for index in range(FRAMES)]
                hand_coverage = require_solid_hands(frames, rig_points, motion)
                metrics = motion_metrics(frames[0], frames[FRAMES // 2])
                require_visible_motion(metrics, f"{character}/{outfit_id}/{motion}")
                atlas = Image.new("RGBA", (CELL[0] * 8, CELL[1] * 8))
                for index, image in enumerate(frames):
                    atlas.alpha_composite(image, ((index % 8) * CELL[0], (index // 8) * CELL[1]))
                atlas = atlas.quantize(colors=256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
                atlas.save(path, compress_level=9)
                info["characters"][character][motion] = {
                    "path": str(path.relative_to(root)), "frames": FRAMES,
                    "sha256": digest(path), "visible_motion": metrics, "moving_hand_opaque_coverage": hand_coverage}
                generated += FRAMES
                print(f"Baked {character}/{outfit_id}/{motion}: {FRAMES} frames, body change {metrics['changed_fraction']:.1%}", flush=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Wardrobe: {expected:,} visibly animated frames; {generated:,} newly baked.", flush=True)
