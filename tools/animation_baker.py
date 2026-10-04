"""Retain independent native portraits byte for byte; Godot supplies body bob."""
import hashlib
import json
import pathlib
import shutil

from PIL import Image

CELL = (1024, 1536)
GENERATOR = "native-portrait-bob-v2"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_native_portrait(path):
    """Reject a low-resolution, flattened or empty source before delivery."""
    with Image.open(path) as image:
        image.load()
        if image.size != CELL or image.mode != "RGBA":
            raise ValueError(f"Expected native {CELL} RGBA portrait: {path}")
        low, high = image.getchannel("A").getextrema()
        if low != 0 or high < 160:
            raise ValueError(f"Expected transparent margins and visible artwork: {path}")


def bake_sprites(root, out, force=False):
    raw_catalog = (root / "data/wardrobe.json").read_bytes()
    catalog = json.loads(raw_catalog)
    destination = out / "sprites"
    destination.mkdir(parents=True, exist_ok=True)
    manifest = {
        "version": 5, "generator": GENERATOR, "baker_sha256": digest(pathlib.Path(__file__)),
        "source": "GPT Images",
        "derivation": "Native original bytes retained; whole-body bobbing in Godot",
        "portrait_count": len(catalog["characters"]) * len(catalog["outfits"]),
        "cell": list(CELL), "catalog_sha256": hashlib.sha256(raw_catalog).hexdigest(),
        "outfits": {}
    }
    expected = set()
    for outfit in catalog["outfits"]:
        info = {"characters": {}}
        manifest["outfits"][outfit["id"]] = info
        suffix = "" if outfit["id"] == "sect" else "_" + outfit["id"]
        for character in catalog["characters"]:
            source = root / outfit["portraits"][character]
            validate_native_portrait(source)
            path = destination / f"{character}{suffix}.png"
            expected.add(path)
            source_hash = digest(source)
            if force or not path.exists() or digest(path) != source_hash:
                shutil.copyfile(source, path)
            info["characters"][character] = {
                "path": str(path.relative_to(root)), "sha256": source_hash,
                "source": str(source.relative_to(root)), "source_sha256": source_hash,
                "native_size": list(CELL)
            }
    for obsolete in destination.glob("*.png"):
        if obsolete not in expected:
            obsolete.unlink()
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Wardrobe: {manifest['portrait_count']} independent native portraits; no resampling.")
