"""Verify every wardrobe, unique transparent frames, music and neural narration."""
import hashlib
import json
import pathlib
import wave

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/generated"


def main():
    raw_catalog = (ROOT / "data/wardrobe.json").read_bytes()
    catalog = json.loads(raw_catalog)
    manifest = json.loads((OUT / "sprites/manifest.json").read_text())
    assert manifest["catalog_sha256"] == hashlib.sha256(raw_catalog).hexdigest()
    assert set(manifest["outfits"]) == {item["id"] for item in catalog["outfits"]}
    count = 0
    hashes = set()
    w, h = manifest["cell"]
    for outfit in catalog["outfits"]:
        outfit_id = outfit["id"]
        entry = manifest["outfits"][outfit_id]
        assert entry["source_sha256"] == hashlib.sha256((ROOT / outfit["source"]).read_bytes()).hexdigest()
        assert set(entry["characters"]) == set(catalog["characters"])
        for character, motions in entry["characters"].items():
            assert set(motions) == set(catalog["motions"]), character
            for motion, info in motions.items():
                suffix = "" if outfit_id == "sect" else f"_{outfit_id}"
                assert info["path"] == f"assets/generated/sprites/{character}{suffix}_{motion}.png"
                assert info["frames"] == catalog["frames_per_cycle"] == 64
                path = ROOT / info["path"]
                assert hashlib.sha256(path.read_bytes()).hexdigest() == info["sha256"]
                image = Image.open(path).convert("RGBA")
                assert image.size == (w * 8, h * 8)
                for index in range(info["frames"]):
                    frame = image.crop(((index % 8) * w, (index // 8) * h, (index % 8 + 1) * w, (index // 8 + 1) * h))
                    minimum, maximum = frame.getchannel("A").getextrema()
                    assert minimum == 0 and maximum > 0, "Each frame must be transparent and contain artwork"
                    digest = hashlib.sha256(frame.tobytes()).hexdigest()
                    assert digest not in hashes, "Animation frames must be unique"
                    hashes.add(digest)
                    count += 1
    expected = len(catalog["characters"]) * len(catalog["outfits"]) * len(catalog["motions"]) * catalog["frames_per_cycle"]
    assert count == manifest["frame_count"] == expected == 3072
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
    print(f"Verified {count} unique GPT-art frames across 12 outfits, 5 music/effects files, {len(voices['lines'])} neural voice clips.")


if __name__ == "__main__":
    main()
