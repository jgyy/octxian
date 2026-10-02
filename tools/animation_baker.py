"""Extract intact character portraits; Godot supplies the whole-body bob."""
import hashlib
import json
import pathlib

import numpy as np
from PIL import Image

CELL = (384, 512)
GENERATOR = "portrait-bob-v1"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_portrait(sheet, index, columns):
    """Use the complete resting pose in the top row, preserving its proportions."""
    width, height = sheet.size
    column = sheet.crop((index * width // columns, 0, (index + 1) * width // columns, height))
    alpha = np.asarray(column.getchannel("A"))
    mass = np.count_nonzero(alpha >= 32, axis=1)
    candidates = np.arange(int(height * 0.46), int(height * 0.57))
    quiet = candidates[mass[candidates] == mass[candidates].min()]
    seam = int(quiet[np.argmin(np.abs(quiet - height / 2))])
    portrait = column.crop((0, 0, column.width, seam))
    box = portrait.getchannel("A").point(lambda value: 255 if value >= 32 else 0).getbbox()
    if box is None:
        raise ValueError(f"Missing resting portrait in column {index}")
    portrait = portrait.crop((max(0, box[0] - 4), max(0, box[1] - 4),
                              min(portrait.width, box[2] + 4), min(portrait.height, box[3] + 4)))
    portrait.thumbnail((CELL[0] - 40, CELL[1] - 40), Image.Resampling.LANCZOS)
    result = Image.new("RGBA", CELL)
    result.alpha_composite(portrait, ((CELL[0] - portrait.width) // 2, CELL[1] - 20 - portrait.height))
    return result


def bake_sprites(root, out, force=False):
    catalog_bytes = (root / "data/wardrobe.json").read_bytes()
    catalog = json.loads(catalog_bytes)
    destination = out / "sprites"
    destination.mkdir(parents=True, exist_ok=True)
    manifest_path = destination / "manifest.json"
    previous = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    baker_hash = digest(pathlib.Path(__file__))
    manifest = {"version": 4, "generator": GENERATOR, "baker_sha256": baker_hash,
                "source": "GPT Images", "derivation": "intact resting portraits with whole-body bobbing in Godot",
                "portrait_count": len(catalog["characters"]) * len(catalog["outfits"]), "cell": list(CELL),
                "catalog_sha256": hashlib.sha256(catalog_bytes).hexdigest(), "outfits": {}}
    for outfit in catalog["outfits"]:
        outfit_id = outfit["id"]
        source_hash = digest(root / outfit["poses"])
        info = {"source": outfit["poses"], "source_sha256": source_hash, "characters": {}}
        manifest["outfits"][outfit_id] = info
        cached = previous.get("outfits", {}).get(outfit_id, {})
        reusable = (previous.get("generator") == GENERATOR and previous.get("baker_sha256") == baker_hash
                    and previous.get("catalog_sha256") == manifest["catalog_sha256"]
                    and previous.get("cell") == list(CELL) and cached.get("source_sha256") == source_hash)
        suffix = "" if outfit_id == "sect" else "_" + outfit_id
        with Image.open(root / outfit["poses"]) as source:
            sheet = source.convert("RGBA")
        for index, character in enumerate(catalog["characters"]):
            path = destination / f"{character}{suffix}.png"
            old = cached.get("characters", {}).get(character, {})
            if not force and reusable and path.exists() and digest(path) == old.get("sha256"):
                info["characters"][character] = old
                continue
            extract_portrait(sheet, index, len(catalog["characters"])).save(path, compress_level=9)
            info["characters"][character] = {"path": str(path.relative_to(root)), "sha256": digest(path)}
            print(f"Prepared intact portrait: {character}/{outfit_id}", flush=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Wardrobe: {manifest['portrait_count']} portraits with runtime body bobbing.", flush=True)
