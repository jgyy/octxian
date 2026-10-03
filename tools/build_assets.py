"""Prepare three wardrobes for four GPT-art characters and synthesize audio.

Whole-body bobbing runs in Godot. Unchanged portraits are reused;
--force regenerates every outfit portrait.
"""
import argparse
import pathlib
import subprocess
import tempfile
import wave

import numpy as np
from animation_baker import bake_sprites

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/generated"
RATE = 22050


def write_wav(path, samples, rate=RATE):
    path.parent.mkdir(parents=True, exist_ok=True)
    samples = np.clip(samples, -0.95, 0.95)
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(rate)
        audio.writeframes((samples * 32767).astype("<i2").tobytes())


def write_score(path, samples):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".score-", dir=path.parent) as folder:
        source = pathlib.Path(folder) / "score.wav"
        output = pathlib.Path(folder) / "score.ogg"
        write_wav(source, samples)
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
                        "-y", "-i", str(source), "-map_metadata", "-1",
                        "-c:a", "libvorbis", "-q:a", "3", str(output)], check=True)
        output.replace(path)
    legacy = path.with_suffix(".wav")
    legacy.unlink(missing_ok=True)
    pathlib.Path(str(legacy) + ".import").unlink(missing_ok=True)


def sprites(force=False):
    bake_sprites(ROOT, OUT, force=force)


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
    write_score(OUT / "audio/cloud_sea.ogg", result)


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
