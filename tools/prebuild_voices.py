"""Narrate saved draft parts without adding them to the playable manuscript."""
import hashlib
import json
import pathlib
from piper import PiperVoice

if __package__:
    from .generate_voices import ROOT, CACHE, MODEL, BASE, download, render_clip, _write_manifest
    from .story_data import load_story
    from .voice_assets import VOICE_FOLDER, VOICE_ENCODING, NODE_ID, clip_entry, reusable_clip
    from .prebuilt_voices import PREBUILD_FOLDER
else:
    from generate_voices import ROOT, CACHE, MODEL, BASE, download, render_clip, _write_manifest
    from story_data import load_story
    from voice_assets import VOICE_FOLDER, VOICE_ENCODING, NODE_ID, clip_entry, reusable_clip
    from prebuilt_voices import PREBUILD_FOLDER

DRAFT_INDEX = ROOT / "docs/DRAFT_BOOKS_20261003.json"
TIMING = {"narrator": 1.04, "lin_yue": .96, "shen_qing": 1.00,
          "elder_yun": 1.12, "mo_ran": 1.08}


def draft_nodes(root=ROOT):
    root = pathlib.Path(root).resolve()
    index = json.loads((root / "docs/DRAFT_BOOKS_20261003.json").read_text())
    active = load_story(root)["nodes"]
    nodes = {}
    for name in index["parts"]:
        path = (root / name).resolve()
        if not path.is_relative_to(root / "data/books") or path.suffix != ".json":
            raise ValueError(f"Unexpected draft book: {name}")
        book = json.loads(path.read_text(encoding="utf-8"))
        for node_id, node in book["nodes"].items():
            if node_id in active:
                if active[node_id]["text"] != node["text"]:
                    raise ValueError(f"Draft differs from active scene: {node_id}")
                continue
            if node_id in nodes or not NODE_ID.fullmatch(node_id):
                raise ValueError(f"Duplicate or unsafe draft scene: {node_id}")
            if not isinstance(node.get("text"), str) or not 0 < len(node["text"].split()) <= 100:
                raise ValueError(f"Invalid draft scene prose: {node_id}")
            nodes[node_id] = node
    return nodes


def main():
    nodes = draft_nodes()
    cache_root = ROOT / PREBUILD_FOLDER
    out = cache_root / VOICE_FOLDER
    out.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    model = download(MODEL)
    download(MODEL + ".json")
    card = download("MODEL_CARD")
    model_digest = hashlib.sha256(model.read_bytes()).hexdigest()
    voice = PiperVoice.load(str(model))
    manifest_path = out / "manifest.json"
    try:
        old = json.loads(manifest_path.read_text())
    except (OSError, ValueError):
        old = {}
    old_lines = old.get("lines", {}) if old.get("model_sha256") == model_digest else {}
    manifest = {"engine": "Piper 1.3.0 (neural ONNX)", "voice": "en_US-lessac-medium",
                "model_url": f"{BASE}/{MODEL}", "model_sha256": model_digest,
                "model_card": card.read_text(), "purpose": "Unintegrated authored draft cache",
                "lines": dict(old_lines)}
    for node_id, node in nodes.items():
        text = node["text"]
        digest = hashlib.sha256(text.encode()).hexdigest()
        previous = old_lines.get(node_id, {})
        reused = reusable_clip(cache_root, node_id, text, previous)
        if reused is not None:
            output, metadata = reused
            status = "Reused"
        else:
            output = out / f"{node_id}.ogg"
            metadata = render_clip(voice, text, output, TIMING.get(node["speaker"], 1.04))
            status = "Generated"
        manifest["lines"][node_id] = {**clip_entry(cache_root, output, digest, metadata),
                                      "encoding": VOICE_ENCODING}
        if status == "Generated":
            _write_manifest(manifest_path, manifest)
        print(f"{status} draft narration: {node_id} ({metadata['seconds']:.1f}s)", flush=True)
    _write_manifest(manifest_path, manifest)
    (out / "MODEL_CARD").write_text(card.read_text())
    print(f"Verified {len(nodes)} draft clips; no playable manuscript credit was changed.", flush=True)


if __name__ == "__main__":
    main()
