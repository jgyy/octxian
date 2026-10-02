"""Bake three wardrobes for four GPT-art characters: 3,072 animation frames.

Frames are derived from GPT portraits through four 64-frame motion cycles.
Validated unchanged atlases are reused, and --force rebakes every outfit.
"""
import argparse
import hashlib
import json
import math
import pathlib
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/generated"
CAST = ("lin_yue", "shen_qing", "elder_yun", "mo_ran")
MOTIONS = ("idle", "channeling", "wind", "resolve")
CELL = (192, 512)
FRAMES = 64
RATE = 22050


def write_wav(path, samples, rate=RATE):
    path.parent.mkdir(parents=True, exist_ok=True)
    samples = np.clip(samples, -0.95, 0.95)
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(rate)
        audio.writeframes((samples * 32767).astype("<i2").tobytes())


def sprites(force=False):
    catalog_bytes = (ROOT / "data/wardrobe.json").read_bytes()
    catalog = json.loads(catalog_bytes)
    destination = OUT / "sprites"
    destination.mkdir(parents=True, exist_ok=True)
    manifest_path = destination / "manifest.json"
    previous = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    expected = len(catalog["characters"]) * len(catalog["outfits"]) * len(MOTIONS) * FRAMES
    manifest = {"version": 2, "generator": "wardrobe-v1", "source": "GPT Images",
                "derivation": "mesh sway, breathing, qi aura", "frame_count": expected,
                "fps": catalog["fps"], "cell": list(CELL),
                "catalog_sha256": hashlib.sha256(catalog_bytes).hexdigest(), "outfits": {}}
    yy, xx = np.mgrid[:CELL[1], :CELL[0]]
    generated = 0
    for outfit in catalog["outfits"]:
        outfit_id = outfit["id"]
        source_path = ROOT / outfit["source"]
        source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
        source = Image.open(source_path).convert("RGBA")
        width, height = source.size
        alpha = np.asarray(source)[:, :, 3]
        print(f"GPT {outfit_id}: {source.size}, alpha {int(alpha.min())}..{int(alpha.max())}", flush=True)
        if alpha.min() == 255:
            raise ValueError(f"{outfit_id} source must have a transparent background")
        info = {"source": outfit["source"], "source_sha256": source_hash, "characters": {}}
        manifest["outfits"][outfit_id] = info
        cached = previous.get("outfits", {}).get(outfit_id, {})
        # Migrate the already verified original robe atlases without rebaking them.
        migrating = outfit_id == "sect" and previous.get("frame_count") == 1024 and "characters" in previous
        old_characters = previous["characters"] if migrating else cached.get("characters", {})
        reusable = migrating or (cached.get("source_sha256") == source_hash
                                and previous.get("generator") == "wardrobe-v1"
                                and previous.get("cell") == list(CELL))
        suffix = "" if outfit_id == "sect" else f"_{outfit_id}"
        for index, character in enumerate(catalog["characters"]):
            crop = source.crop((index * width // 4, 0, (index + 1) * width // 4, height))
            crop.thumbnail((166, 480), Image.Resampling.LANCZOS)
            base = Image.new("RGBA", CELL)
            base.alpha_composite(crop, ((CELL[0] - crop.width) // 2, (CELL[1] - crop.height) // 2))
            original = np.asarray(base)
            info["characters"][character] = {}
            for motion in MOTIONS:
                path = destination / f"{character}{suffix}_{motion}.png"
                old_info = old_characters.get(character, {}).get(motion, {})
                if (not force and reusable and path.exists() and old_info.get("frames") == FRAMES
                        and hashlib.sha256(path.read_bytes()).hexdigest() == old_info.get("sha256")):
                    info["characters"][character][motion] = old_info
                    continue
                atlas = Image.new("RGBA", (CELL[0] * 8, CELL[1] * 8))
                for frame in range(FRAMES):
                    phase = 2 * math.pi * frame / FRAMES + MOTIONS.index(motion) * 0.29
                    amplitude = {"idle": 1.8, "channeling": 2.4, "wind": 5.0, "resolve": 3.2}[motion]
                    sway = amplitude * math.sin(phase) * (0.1 + yy / CELL[1]) ** 2
                    breathe = 1.0 + 0.008 * math.sin(phase + 0.6)
                    sample_x = (xx - CELL[0] / 2) / breathe + CELL[0] / 2 - sway
                    sample_y = yy - 2.2 * math.sin(phase + 0.3)
                    x0 = np.floor(sample_x).astype(int)
                    y0 = np.floor(sample_y).astype(int)
                    wx = (sample_x - x0)[..., None]
                    wy = (sample_y - y0)[..., None]
                    x0 = np.clip(x0, 0, CELL[0] - 1)
                    y0 = np.clip(y0, 0, CELL[1] - 1)
                    x1 = np.clip(x0 + 1, 0, CELL[0] - 1)
                    y1 = np.clip(y0 + 1, 0, CELL[1] - 1)
                    pixels = ((original[y0, x0] * (1 - wx) + original[y0, x1] * wx) * (1 - wy)
                              + (original[y1, x0] * (1 - wx) + original[y1, x1] * wx) * wy)
                    image = Image.fromarray(np.uint8(pixels))
                    if motion in ("channeling", "resolve"):
                        aura = Image.new("RGBA", CELL)
                        draw = ImageDraw.Draw(aura)
                        color = (149, 229, 213, 65) if motion == "channeling" else (231, 198, 126, 55)
                        for particle in range(8):
                            theta = phase + particle * math.pi / 4
                            x = 96 + math.cos(theta) * 73
                            y = 268 + math.sin(theta) * 145
                            draw.ellipse((x - 2, y - 2, x + 2, y + 2), fill=color)
                        image = Image.alpha_composite(image, aura.filter(ImageFilter.GaussianBlur(1.2)))
                    atlas.alpha_composite(image, ((frame % 8) * CELL[0], (frame // 8) * CELL[1]))
                atlas.save(path, optimize=True)
                info["characters"][character][motion] = {
                    "path": str(path.relative_to(ROOT)), "frames": FRAMES,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
                generated += FRAMES
                print(f"Baked {character}/{outfit_id}/{motion}: {FRAMES} frames", flush=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Wardrobe: {expected:,} frames in {len(catalog['outfits'])} outfit sets; {generated:,} newly baked.")


def music():
    # Original pentatonic composition. Plucked string partials suggest a guzheng,
    # while a quiet drone and filtered noise leave room for narration.
    duration = 48
    time = np.arange(RATE * duration) / RATE
    result = 0.018 * np.sin(2 * np.pi * 130.81 * time)
    result += 0.010 * np.sin(2 * np.pi * 196.00 * time)
    notes = [60, 64, 67, 69, 67, 64, 62, 60, 67, 72, 74, 72, 69, 67, 64, 62]
    for index in range(32):
        midi = notes[index % len(notes)]
        frequency = 440 * 2 ** ((midi - 69) / 12)
        start = int(index * 1.5 * RATE)
        t = np.arange(min(RATE * 5, len(result) - start)) / RATE
        note = np.zeros(len(t))
        for partial in range(1, 7):
            note += np.sin(2 * np.pi * frequency * partial * t + partial * 0.1) * np.exp(-t * (1.5 + partial * 0.32)) / partial
        note *= 0.14 * np.minimum(t * 150, 1)
        result[start:start + len(note)] += note
        # A small echo returns the mountain's spacious acoustic.
        delayed = start + int(0.28 * RATE)
        length = min(len(note), len(result) - delayed)
        result[delayed:delayed + length] += note[:length] * 0.22
    fade = RATE * 2
    result[:fade] *= np.linspace(0, 1, fade)
    result[-fade:] *= np.linspace(1, 0, fade)
    write_wav(OUT / "audio/cloud_sea.wav", result)


def effects():
    rng = np.random.default_rng(1847)
    for name, duration in [("page", 0.16), ("bell", 2.8), ("qi", 1.4), ("sword", 0.65)]:
        t = np.arange(int(RATE * duration)) / RATE
        if name == "bell":
            samples = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * decay) * amp
                          for f, decay, amp in [(523.25, 1.5, .22), (1046.5, 2.5, .1), (1569.75, 3.0, .05)])
        elif name == "qi":
            samples = .16 * np.sin(2 * np.pi * (190 * t + 150 * t ** 2)) * np.sin(np.pi * t / duration) ** 2
        elif name == "sword":
            samples = rng.normal(0, .13, len(t)) * np.sin(np.pi * t / duration) ** 3
            samples += .08 * np.sin(2 * np.pi * (1500 * t - 900 * t ** 2)) * np.exp(-t * 8)
        else:
            samples = rng.normal(0, .04, len(t)) * np.sin(np.pi * t / duration) ** 2
        write_wav(OUT / f"audio/{name}.wav", samples)
    print("Original 48-second score and four sound effects generated.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio-only", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if not args.audio_only:
        sprites(force=args.force)
    music()
    effects()


if __name__ == "__main__":
    main()
