"""Verify real sprite frames, animation uniqueness, audio, and every spoken line."""
import hashlib
import json
import pathlib
import wave

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/generated"


def main():
    manifest = json.loads((OUT / "sprites/manifest.json").read_text())
    count = 0
    hashes = set()
    w, h = manifest["cell"]
    for character, motions in manifest["characters"].items():
        assert set(motions) == {"idle", "channeling", "wind", "resolve"}, character
        for info in motions.values():
            path = ROOT / info["path"]
            assert hashlib.sha256(path.read_bytes()).hexdigest() == info["sha256"]
            image = Image.open(path).convert("RGBA")
            assert image.size == (w * 8, h * 8)
            for index in range(info["frames"]):
                frame = image.crop(((index % 8) * w, (index // 8) * h, (index % 8 + 1) * w, (index // 8 + 1) * h))
                assert frame.getchannel("A").getextrema()[0] == 0, "Frame must be transparent"
                digest = hashlib.sha256(frame.tobytes()).hexdigest()
                assert digest not in hashes, "Animation frames must be unique"
                hashes.add(digest)
                count += 1
    assert count == manifest["frame_count"] == 1024
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
    print(f"Verified {count} unique GPT-art-derived animation frames, 5 music/effects files, {len(voices['lines'])} neural voice clips.")


if __name__ == "__main__":
    main()
