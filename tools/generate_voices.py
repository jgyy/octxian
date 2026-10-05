"""Render the campaign with Piper; preserve valid clips and compress new narration."""
import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import pathlib
import subprocess
import tempfile
import urllib.request
import wave

import onnxruntime
from piper import PiperVoice, SynthesisConfig
from piper.config import PiperConfig

if __package__:
    from .story_data import load_story
    from .voice_assets import NODE_ID, audio_metadata, clip_entry, reusable_clip
    from .prebuilt_voices import load_prebuilt, adopt_prebuilt
else:
    from story_data import load_story
    from voice_assets import NODE_ID, audio_metadata, clip_entry, reusable_clip
    from prebuilt_voices import load_prebuilt, adopt_prebuilt

ROOT = pathlib.Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache/voice"
OUT = ROOT / "assets/generated/voices"
BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium"
MODEL = "en_US-lessac-medium.onnx"


def download(name):
    path = CACHE / name
    if not path.exists():
        temporary = path.with_suffix(path.suffix + ".part")
        urllib.request.urlretrieve(f"{BASE}/{name}", temporary)
        temporary.replace(path)
    return path


def render_clip(voice, text, output, length_scale):
    """Only the validated Vorbis clip survives; the intermediate PCM is temporary."""
    output = pathlib.Path(output)
    with tempfile.TemporaryDirectory(prefix=".narration-", dir=output.parent) as folder:
        temporary = pathlib.Path(folder)
        source, compressed = temporary / "source.wav", temporary / "voice.ogg"
        with wave.open(str(source), "wb") as wav_file:
            voice.synthesize_wav(text, wav_file,
                                 syn_config=SynthesisConfig(length_scale=length_scale))
        audio_metadata(source)
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
                        "-y", "-i", str(source), "-map_metadata", "-1", "-ac", "1", "-ar", "16000",
                        "-c:a", "libvorbis", "-q:a", "0", str(compressed)],
                       check=True)
        metadata = audio_metadata(compressed)
        compressed.replace(output)
    return metadata


def _write_manifest(path, manifest):
    """Commit completed clips without exposing a partially written checkpoint."""
    path = pathlib.Path(path)
    with tempfile.TemporaryDirectory(prefix=".manifest-", dir=path.parent) as folder:
        temporary = pathlib.Path(folder) / "manifest.json"
        temporary.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)


def load_renderer(model, workers):
    """Use one CPU thread per concurrent inference; Piper serializes phonemization."""
    if workers == 1:
        return PiperVoice.load(str(model))
    options = onnxruntime.SessionOptions()
    options.intra_op_num_threads = 1
    options.inter_op_num_threads = 1
    return PiperVoice(
        config=PiperConfig.from_dict(json.loads(pathlib.Path(str(model) + ".json").read_text())),
        session=onnxruntime.InferenceSession(str(model), sess_options=options,
                                             providers=["CPUExecutionProvider"]),
    )


def finish_pending(pending):
    """Return validated worker results to the sole manifest writer."""
    done, _ = wait(pending, return_when=FIRST_COMPLETED)
    # Dictionary order makes simultaneous completions deterministic for review.
    for future in list(pending):
        if future not in done:
            continue
        node_id, digest, output = pending.pop(future)
        yield node_id, digest, output, future.result()


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    story = load_story(ROOT)
    model = download(MODEL)
    download(MODEL + ".json")
    card = download("MODEL_CARD")
    workers = int(os.environ.get("JADE_VOW_VOICE_WORKERS", "1"))
    if not 1 <= workers <= 4:
        raise ValueError("JADE_VOW_VOICE_WORKERS must be between 1 and 4")
    voice = load_renderer(model, workers)
    model_digest = hashlib.sha256(model.read_bytes()).hexdigest()
    prebuilt_root, prebuilt_lines = load_prebuilt(ROOT, model_digest)
    old_path = OUT / "manifest.json"
    old = json.loads(old_path.read_text()) if old_path.exists() else {"lines": {}}
    old_lines = old.get("lines", {}) if old.get("model_sha256") == model_digest else {}
    manifest = {"engine": "Piper 1.3.0 (neural ONNX)", "voice": "en_US-lessac-medium",
                "model_url": f"{BASE}/{MODEL}", "model_sha256": model_digest,
                "model_card": card.read_text(),
                "encoding": "New clips: 16000 Hz mono Vorbis quality 0; validated existing clips retained",
                # Retain unprocessed records until their scenes are checked.
                "lines": {node_id: info for node_id, info in old_lines.items()
                          if node_id in story["nodes"]}}
    timing = {"narrator": 1.04, "lin_yue": .96, "shen_qing": 1.00,
              "elder_yun": 1.12, "mo_ran": 1.08}
    generated_encoding = "ffmpeg libvorbis, mono, 16000 Hz, quality 0"

    def record(node_id, digest, output, metadata, encoding, status):
        manifest["lines"][node_id] = {**clip_entry(ROOT, output, digest, metadata),
                                      "encoding": encoding}
        if status != "Reused":
            # Only this coordinator writes the atomic, resumable manifest.
            _write_manifest(old_path, manifest)
        for extension in (".wav", ".ogg"):
            obsolete = OUT / (node_id + extension)
            if obsolete != output and obsolete.exists():
                obsolete.unlink()
        print(f"{status} neural voice: {node_id} ({metadata['seconds']:.1f}s, {metadata['format']})",
              flush=True)

    pending = {}
    print(f"Narration renderer: {workers} concurrent worker(s)", flush=True)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for node_id, node in story["nodes"].items():
            if not NODE_ID.fullmatch(node_id):
                raise ValueError(f"Unsafe narration scene ID: {node_id}")
            text = node["text"]
            digest = hashlib.sha256(text.encode()).hexdigest()
            previous = old_lines.get(node_id, {})
            reused = reusable_clip(ROOT, node_id, text, previous)
            if reused is not None:
                output, metadata = reused
                encoding = previous.get("encoding")
                if not isinstance(encoding, str) or not encoding.strip():
                    encoding = ("Retained Vorbis; original encoder settings unrecorded"
                                if metadata["format"] == "ogg" else "Retained legacy PCM16")
                record(node_id, digest, output, metadata, encoding, "Reused")
                continue
            cached = adopt_prebuilt(ROOT, prebuilt_root, node_id, text,
                                   prebuilt_lines.get(node_id, {}))
            if cached is not None:
                output, metadata = cached
                record(node_id, digest, output, metadata, generated_encoding, "Adopted")
                continue
            output = OUT / f"{node_id}.ogg"
            length_scale = timing.get(node["speaker"], 1.04)
            if workers == 1:
                metadata = render_clip(voice, text, output, length_scale)
                record(node_id, digest, output, metadata, generated_encoding, "Generated")
                continue
            pending[pool.submit(render_clip, voice, text, output, length_scale)] = (
                node_id, digest, output)
            # Bound queued work and preserve completed clips during a long run.
            if len(pending) >= workers * 2:
                for result_id, result_digest, result_output, metadata in finish_pending(pending):
                    record(result_id, result_digest, result_output, metadata,
                           generated_encoding, "Generated")
        while pending:
            for result_id, result_digest, result_output, metadata in finish_pending(pending):
                record(result_id, result_digest, result_output, metadata,
                       generated_encoding, "Generated")
    _write_manifest(old_path, manifest)
    expected = {ROOT / info["file"] for info in manifest["lines"].values()}
    for path in list(OUT.glob("*.wav")) + list(OUT.glob("*.ogg")):
        if path not in expected:
            path.unlink()
    (OUT / "MODEL_CARD").write_text(card.read_text())
    print(f"Verified {len(manifest['lines'])} neural narration clips.")


if __name__ == "__main__":
    main()
