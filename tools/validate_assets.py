"""Verify intact wardrobe portraits, original music and neural narration."""
import hashlib
import json
import pathlib
import wave

from PIL import Image
if __package__:
    from .animation_baker import CELL, GENERATOR, digest
    from .story_data import load_story
    from .voice_assets import audio_metadata, validate_clip
else:
    from animation_baker import CELL, GENERATOR, digest
    from story_data import load_story
    from voice_assets import audio_metadata, validate_clip

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/generated"


def main():
    compression = json.loads((ROOT / "assets/art/compression.json").read_text())
    paintings = set()
    for name, info in compression["images"].items():
        path = ROOT / name
        assert digest(path) == info["sha256"], "Compressed artwork bytes changed"
        with Image.open(path) as image:
            assert list(image.size) == info["native_size"], "Keep native artwork dimensions"
            assert hashlib.sha256(image.convert("RGBA").tobytes()).hexdigest() == info["rgba_sha256"], "Compressed artwork pixels changed"
        paintings.add(path)
    assert paintings == set((ROOT / "assets/art").rglob("*.webp")), "Record every compressed painting"
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
    story = load_story(ROOT)
    voices = json.loads((OUT / "voices/manifest.json").read_text())
    assert set(voices["lines"]) == set(story["nodes"]), "Every scene must have neural voice audio"
    voice_paths = set()
    for key, node in story["nodes"].items():
        path, _ = validate_clip(ROOT, key, node["text"], voices["lines"][key])
        voice_paths.add(path)
    delivered = set((OUT / "voices").glob("*.wav")) | set((OUT / "voices").glob("*.ogg"))
    assert voice_paths == delivered, "Remove stale or untracked narration clips"
    for path in (OUT / "audio").glob("*.wav"):
        with wave.open(str(path)) as audio:
            assert audio.getnframes() > 0 and audio.getsampwidth() == 2, path
    assert len(list((OUT / "audio").glob("*.wav"))) == 4
    score = audio_metadata(OUT / "audio/cloud_sea.ogg")
    assert score["seconds"] == 48.0, "Keep the complete background composition"
    print(f"Verified {len(paths)} intact portraits, 5 music/effects files, {len(voices['lines'])} neural voice clips.")


if __name__ == "__main__":
    main()
