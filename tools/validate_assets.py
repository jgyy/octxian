"""Verify intact wardrobe portraits, original music and neural narration."""
import hashlib
import json
import pathlib
import wave

from PIL import Image
from animation_baker import CELL, GENERATOR, digest

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/generated"


def main():
    raw_catalog = (ROOT / "data/wardrobe.json").read_bytes()
    catalog = json.loads(raw_catalog)
    manifest = json.loads((OUT / "sprites/manifest.json").read_text())
    assert manifest["catalog_sha256"] == hashlib.sha256(raw_catalog).hexdigest()
    assert manifest["version"] == 4 and manifest["generator"] == GENERATOR
    assert manifest["cell"] == list(CELL)
    assert manifest["baker_sha256"] == digest(ROOT / "tools/animation_baker.py")
    assert set(manifest["outfits"]) == {item["id"] for item in catalog["outfits"]}
    assert set(catalog["bob_pixels"]) == set(catalog["motions"])
    assert catalog["seconds_per_cycle"] > 0
    assert all(0 < value <= 12 for value in catalog["bob_pixels"].values())
    paths = set()
    for outfit in catalog["outfits"]:
        entry = manifest["outfits"][outfit["id"]]
        assert entry["source"] == outfit["poses"]
        assert entry["source_sha256"] == digest(ROOT / outfit["poses"])
        assert set(entry["characters"]) == set(catalog["characters"])
        for character, info in entry["characters"].items():
            suffix = "" if outfit["id"] == "sect" else "_" + outfit["id"]
            assert info["path"] == f"assets/generated/sprites/{character}{suffix}.png"
            path = ROOT / info["path"]
            assert digest(path) == info["sha256"]
            with Image.open(path) as source:
                image = source.convert("RGBA")
            assert image.size == CELL
            minimum, maximum = image.getchannel("A").getextrema()
            assert minimum == 0 and maximum >= 160, "Portraits need transparency and solid artwork"
            paths.add(path)
    assert paths == set((OUT / "sprites").glob("*.png")), "Remove obsolete animation atlases"
    assert len(paths) == manifest["portrait_count"] == 12
    story = json.loads((ROOT / "data/story.json").read_text())
    voices = json.loads((OUT / "voices/manifest.json").read_text())
    assert set(voices["lines"]) == set(story["nodes"]), "Every scene must have neural voice audio"
    for key, node in story["nodes"].items():
        info = voices["lines"][key]
        assert info["text_sha256"] == hashlib.sha256(node["text"].encode()).hexdigest()
        path = ROOT / info["file"]
        assert info["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    for path in list((OUT / "audio").glob("*.wav")) + list((OUT / "voices").glob("*.wav")):
        with wave.open(str(path)) as audio:
            assert audio.getnframes() > 0 and audio.getsampwidth() == 2, path
    assert len(list((OUT / "audio").glob("*.wav"))) == 5
    print(f"Verified {len(paths)} intact portraits, 5 music/effects files, {len(voices['lines'])} neural voice clips.")


if __name__ == "__main__":
    main()
