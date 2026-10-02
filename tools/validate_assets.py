"""Verify every wardrobe, unique transparent frames, music and neural narration."""
import hashlib
import json
import pathlib
import wave

from PIL import Image

from animation_baker import CELL, GENERATOR, digest
from animation_motion import motion_metrics, require_visible_motion

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/generated"


def main():
    raw_catalog = (ROOT / "data/wardrobe.json").read_bytes()
    catalog = json.loads(raw_catalog)
    manifest = json.loads((OUT / "sprites/manifest.json").read_text())
    assert manifest["catalog_sha256"] == hashlib.sha256(raw_catalog).hexdigest()
    assert set(manifest["outfits"]) == {item["id"] for item in catalog["outfits"]}
    assert manifest["version"] == 3 and manifest["generator"] == GENERATOR
    assert manifest["cell"] == list(CELL) and manifest["key_poses_per_appearance"] == 2
    assert manifest["baker_sha256"] == digest(ROOT / "tools/animation_baker.py")
    assert manifest["rig_sha256"] == digest(ROOT / "data/animation_rigs.json")
    assert manifest["rig_code_sha256"] == digest(ROOT / "tools/pose_rig.py")
    motion_report = {}
    count = 0
    hashes = set()
    w, h = manifest["cell"]
    for outfit in catalog["outfits"]:
        outfit_id = outfit["id"]
        entry = manifest["outfits"][outfit_id]
        assert entry["source_sha256"] == hashlib.sha256((ROOT / outfit["source"]).read_bytes()).hexdigest()
        assert entry["pose_source"] == outfit["poses"]
        assert entry["pose_source_sha256"] == digest(ROOT / outfit["poses"])
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
                decoded_frames = []
                for index in range(info["frames"]):
                    frame = image.crop(((index % 8) * w, (index // 8) * h, (index % 8 + 1) * w, (index // 8 + 1) * h))
                    decoded_frames.append(frame)
                    minimum, maximum = frame.getchannel("A").getextrema()
                    assert minimum == 0 and maximum > 0, "Each frame must be transparent and contain artwork"
                    frame_hash = hashlib.sha256(frame.tobytes()).hexdigest()
                    assert frame_hash not in hashes, "Animation frames must be unique"
                    hashes.add(frame_hash)
                    count += 1
                label = f"{character}/{outfit_id}/{motion}"
                metrics = motion_metrics(decoded_frames[0], decoded_frames[32])
                require_visible_motion(metrics, label)
                motion_report[label] = metrics
    report_path = ROOT / "build/animations/motion_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(motion_report, indent=2) + "\n")
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
    print(f"Verified {count} visibly moving unique GPT-art frames across 12 outfits, 5 music/effects files, {len(voices['lines'])} neural voice clips.")


if __name__ == "__main__":
    main()
