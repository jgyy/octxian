"""Validate decoded narration while retaining its text and byte provenance."""
import hashlib
import math
import pathlib
import re

import numpy as np
import soundfile as sf

VOICE_FOLDER = pathlib.PurePosixPath("assets/generated/voices")
NODE_ID = re.compile(r"[A-Za-z0-9_]+\Z")
VOICE_ENCODING = "ffmpeg libvorbis, mono, 8000 Hz, constrained 10000 bit/s"
VOICE_FFMPEG_ARGS = ("-ac", "1", "-ar", "8000", "-c:a", "libvorbis",
                     "-b:a", "10k", "-minrate", "10k", "-maxrate", "10k")


def voice_output_args(source):
    """Keep the decoded source length when resampling Vorbis encoder padding."""
    with sf.SoundFile(source) as audio:
        duration = audio.frames / audio.samplerate
    return (*VOICE_FFMPEG_ARGS, "-t", str(duration))


def audio_metadata(path):
    """Inspect and decode the real clip, rejecting empty, corrupt or silent audio."""
    path = pathlib.Path(path)
    expected = {".wav": ("WAV", "PCM_16", "pcm_s16le"),
                ".ogg": ("OGG", "VORBIS", "vorbis")}
    if path.suffix not in expected:
        raise ValueError(f"Unsupported narration format: {path}")
    container, subtype, codec = expected[path.suffix]
    try:
        with sf.SoundFile(path) as audio:
            if audio.format != container or audio.subtype != subtype:
                raise ValueError(f"Unexpected narration codec: {path}")
            if audio.channels != 1 or audio.frames <= 0 or audio.samplerate <= 0:
                raise ValueError(f"Narration must contain mono samples: {path}")
            frames, audible = 0, False
            for block in audio.blocks(blocksize=65536, dtype="float32"):
                if not np.isfinite(block).all():
                    raise ValueError(f"Invalid narration samples: {path}")
                frames += len(block)
                audible = audible or bool(np.any(np.abs(block) > 0.000001))
            if frames != audio.frames or not audible:
                raise ValueError(f"Empty, silent or incomplete narration: {path}")
            return {"format": path.suffix[1:], "codec": codec, "channels": 1,
                    "sample_rate": audio.samplerate,
                    "seconds": round(frames / audio.samplerate, 2)}
    except (OSError, RuntimeError) as error:
        raise ValueError(f"Cannot decode narration {path}: {error}") from error


def clip_path(root, node_id, name):
    if not isinstance(node_id, str) or not NODE_ID.fullmatch(node_id):
        raise ValueError(f"Unsafe narration scene ID: {node_id!r}")
    allowed = {str(VOICE_FOLDER / f"{node_id}.wav"),
               str(VOICE_FOLDER / f"{node_id}.ogg")}
    if name not in allowed:
        raise ValueError(f"Unexpected narration path for {node_id}: {name!r}")
    root = pathlib.Path(root).resolve()
    path = (root / name).resolve()
    if not path.is_relative_to(root / VOICE_FOLDER):
        raise ValueError(f"Narration path escapes its folder: {name!r}")
    if not path.is_file():
        raise ValueError(f"Missing narration: {name}")
    return path


def clip_entry(root, path, text_sha256, metadata=None):
    path = pathlib.Path(path)
    metadata = audio_metadata(path) if metadata is None else metadata
    return {"file": str(path.relative_to(root)), **metadata,
            "text_sha256": text_sha256,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def validate_clip(root, node_id, text, info):
    if not isinstance(info, dict):
        raise ValueError(f"Missing narration record for {node_id}")
    digest = hashlib.sha256(text.encode()).hexdigest()
    if info.get("text_sha256") != digest:
        raise ValueError(f"Narration text changed: {node_id}")
    path = clip_path(root, node_id, info.get("file"))
    if info.get("sha256") != hashlib.sha256(path.read_bytes()).hexdigest():
        raise ValueError(f"Narration bytes changed: {node_id}")
    metadata = audio_metadata(path)
    seconds = info.get("seconds")
    if (isinstance(seconds, bool) or not isinstance(seconds, (int, float))
            or not math.isfinite(seconds) or abs(seconds - metadata["seconds"]) > 0.011):
        raise ValueError(f"Narration duration changed: {node_id}")
    # Original manifests predate codec fields; retain their validated PCM clips.
    for field in ("format", "codec", "channels", "sample_rate"):
        if field in info and info[field] != metadata[field]:
            raise ValueError(f"Narration {field} changed: {node_id}")
    return path, metadata


def reusable_clip(root, node_id, text, info):
    try:
        return validate_clip(root, node_id, text, info)
    except (ValueError, TypeError):
        return None
