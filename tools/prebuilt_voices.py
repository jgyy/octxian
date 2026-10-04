"""Reuse separately cached draft narration only after text, model and audio checks."""
import hashlib
import json
import pathlib
import shutil
import tempfile

if __package__:
    from .voice_assets import VOICE_FOLDER, reusable_clip
else:
    from voice_assets import VOICE_FOLDER, reusable_clip

PREBUILD_FOLDER = pathlib.Path(".cache/voice-prebuild")


def load_prebuilt(root, model_digest):
    cache_root = pathlib.Path(root) / PREBUILD_FOLDER
    manifest_path = cache_root / VOICE_FOLDER / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return cache_root, {}
    if not isinstance(manifest, dict) or manifest.get("model_sha256") != model_digest:
        return cache_root, {}
    lines = manifest.get("lines")
    return cache_root, lines if isinstance(lines, dict) else {}


def adopt_prebuilt(root, cache_root, node_id, text, record):
    reused = reusable_clip(cache_root, node_id, text, record)
    if reused is None:
        return None
    source, metadata = reused
    destination = pathlib.Path(root) / record["file"]
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".adopt-", dir=destination.parent) as folder:
        temporary = pathlib.Path(folder) / source.name
        shutil.copyfile(source, temporary)
        if hashlib.sha256(temporary.read_bytes()).hexdigest() != record["sha256"]:
            return None
        temporary.replace(destination)
    return destination, metadata
