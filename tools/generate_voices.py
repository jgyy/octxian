"""Render the entire opening with Piper's open neural Lessac voice; resumable."""
import hashlib
import json
import pathlib
import urllib.request
import wave

from piper import PiperVoice, SynthesisConfig

ROOT = pathlib.Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache/voice"
OUT = ROOT / "assets/generated/voices"
BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium"
MODEL = "en_US-lessac-medium.onnx"
CACHE.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)


def download(name):
    path = CACHE / name
    if not path.exists():
        temporary = path.with_suffix(path.suffix + ".part")
        urllib.request.urlretrieve(f"{BASE}/{name}", temporary)
        temporary.replace(path)
    return path


def main():
    model = download(MODEL)
    download(MODEL + ".json")
    card = download("MODEL_CARD")
    voice = PiperVoice.load(str(model))
    story = json.loads((ROOT / "data/story.json").read_text())
    old_path = OUT / "manifest.json"
    old = json.loads(old_path.read_text()) if old_path.exists() else {"lines": {}}
    manifest = {"engine": "Piper 1.3.0 (neural ONNX)", "voice": "en_US-lessac-medium",
                "model_url": f"{BASE}/{MODEL}",
                "model_sha256": hashlib.sha256(model.read_bytes()).hexdigest(),
                "model_card": card.read_text(), "lines": {}}
    timing = {"narrator": 1.04, "lin_yue": .96, "shen_qing": 1.00, "elder_yun": 1.12, "mo_ran": 1.08}
    for node_id, node in story["nodes"].items():
        text = node["text"]
        digest = hashlib.sha256(text.encode()).hexdigest()
        output = OUT / f"{node_id}.wav"
        if not output.exists() or old["lines"].get(node_id, {}).get("text_sha256") != digest:
            with wave.open(str(output), "wb") as wav_file:
                voice.synthesize_wav(text, wav_file, syn_config=SynthesisConfig(length_scale=timing[node["speaker"]]))
        with wave.open(str(output)) as wav_file:
            seconds = wav_file.getnframes() / wav_file.getframerate()
            if seconds <= 0:
                raise ValueError(f"Empty narration for {node_id}")
        manifest["lines"][node_id] = {"file": str(output.relative_to(ROOT)), "seconds": round(seconds, 2),
                                      "text_sha256": digest, "sha256": hashlib.sha256(output.read_bytes()).hexdigest()}
        print(f"Neural voice: {node_id} ({seconds:.1f}s)")
    old_path.write_text(json.dumps(manifest, indent=2) + "\n")
    (OUT / "MODEL_CARD").write_text(card.read_text())
    print(f"Generated {len(manifest['lines'])} neural narration clips.")


if __name__ == "__main__":
    main()
