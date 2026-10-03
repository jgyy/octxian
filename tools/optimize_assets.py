"""Compact bundled media, preserving artwork pixels and narration provenance."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import pathlib
import subprocess
import tempfile

from PIL import Image

if __package__:
    from .voice_assets import audio_metadata, clip_entry
else:
    from voice_assets import audio_metadata, clip_entry


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                     suffix=".tmp", delete=False) as temporary:
        json.dump(value, temporary, indent=2)
        temporary.write("\n")
        name = pathlib.Path(temporary.name)
    name.replace(path)


def compact_art(root, workers):
    folder = root / "assets/art"
    manifest_path = folder / "compression.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {
        "encoding": "lossless WebP; exact RGBA pixels, alpha and dimensions retained",
        "images": {},
    }

    def convert(path):
        output = path.with_suffix(".webp")
        with Image.open(path) as source:
            pixels = source.convert("RGBA").tobytes()
            source.save(output, format="WEBP", lossless=True, quality=100,
                        method=6, exact=True)
            size = list(source.size)
        with Image.open(output) as delivered:
            if delivered.size != tuple(size) or delivered.convert("RGBA").tobytes() != pixels:
                raise ValueError(f"Artwork pixels changed: {path}")
        return path, output, {
            "source": path.relative_to(root).as_posix(),
            "source_sha256": digest(path), "source_bytes": path.stat().st_size,
            "sha256": digest(output), "bytes": output.stat().st_size,
            "native_size": size, "rgba_sha256": hashlib.sha256(pixels).hexdigest(),
        }

    with ThreadPoolExecutor(max_workers=workers) as pool:
        converted = list(pool.map(convert, sorted(folder.rglob("*.png"))))
    replacements = {old.relative_to(root).as_posix(): new.relative_to(root).as_posix()
                    for old, new, _ in converted}
    text_files = [root / "README.md"]
    for name, pattern in (("data", "*.json"), ("scripts", "*.gd"),
                          ("docs", "*.md"), ("assets/art", "*.md")):
        text_files.extend((root / name).rglob(pattern))
    for path in text_files:
        if not path.exists():
            continue
        original = path.read_text(encoding="utf-8")
        text = original
        for old, new in replacements.items():
            text = text.replace(old, new)
        if path in (folder / "PROVENANCE.md", root / "docs/INTERIORS.md"):
            for old, new, _ in converted:
                text = text.replace(old.name, new.name)
        if text != original:
            path.write_text(text, encoding="utf-8")
    catalog_path = root / "data/world_assets.json"
    if catalog_path.exists():
        catalog = json.loads(catalog_path.read_text())
        for group in ("npcs", "monsters"):
            for entry in catalog.get(group, []):
                provenance = entry.get("provenance", {})
                if "source_sha256" in provenance:
                    provenance["source_sha256"] = digest(root / provenance["source_path"])
        write_json(catalog_path, catalog)
    for old, new, record in converted:
        manifest["images"][new.relative_to(root).as_posix()] = record
    write_json(manifest_path, manifest)
    for old, new, _ in converted:
        importer = pathlib.Path(str(old) + ".import")
        if importer.exists():
            # Retain the resource UID; Godot rebuilds the destination on import.
            updated = importer.read_text().replace(old.relative_to(root).as_posix(),
                                                    new.relative_to(root).as_posix())
            pathlib.Path(str(new) + ".import").write_text(updated)
            importer.unlink()
        old.unlink()
    print(f"Verified lossless pixels for {len(converted)} paintings.", flush=True)


def compact_voices(root, workers):
    folder = root / "assets/generated/voices"
    manifest_path = folder / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    encoding = "ffmpeg libvorbis, mono, 16000 Hz, quality 0"

    def convert(item):
        node_id, info = item
        source = root / info["file"]
        source_metadata = audio_metadata(source)
        if digest(source) != info["sha256"]:
            raise ValueError(f"Narration bytes changed before compression: {node_id}")
        if source.suffix == ".ogg" and info.get("encoding") == encoding:
            return node_id, info, source, source
        output = folder / (node_id + ".ogg")
        with tempfile.TemporaryDirectory(prefix=".compress-", dir=folder) as temporary:
            compressed = pathlib.Path(temporary) / "voice.ogg"
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
                            "-y", "-threads", "1", "-i", str(source), "-map_metadata", "-1",
                            "-ac", "1", "-ar", "16000", "-c:a", "libvorbis", "-q:a", "0", "-threads", "1",
                            str(compressed)], check=True)
            metadata = audio_metadata(compressed)
            if abs(metadata["seconds"] - source_metadata["seconds"]) > .011:
                raise ValueError(f"Narration timing changed: {node_id}")
            record = {**clip_entry(root, compressed, info["text_sha256"], metadata),
                      "file": output.relative_to(root).as_posix(), "encoding": encoding,
                      "compression_source": {"sha256": info["sha256"],
                                             "format": source_metadata["format"],
                                             "encoding": info.get("encoding", "unrecorded")}}
            # The coordinator replaces files and checkpoints their new records together.
            pending = folder / (node_id + ".ogg.tmp")
            compressed.replace(pending)
        return node_id, record, source, pending

    items = list(manifest["lines"].items())
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for count, (node_id, record, source, pending) in enumerate(pool.map(convert, items), 1):
            output = folder / (node_id + ".ogg")
            if pending != output:
                pending.replace(output)
            manifest["lines"][node_id] = record
            write_json(manifest_path, manifest)
            if source != output:
                source.unlink()
                pathlib.Path(str(source) + ".import").unlink(missing_ok=True)
            if count % 100 == 0 or count == len(items):
                print(f"Verified narration {count}/{len(items)}.", flush=True)
    manifest["encoding"] = "All clips: 16000 Hz mono Vorbis quality 0; source encoding recorded per clip"
    write_json(manifest_path, manifest)


def compact_screenshots(root):
    replacements = {}
    for path in (root / "docs/screenshots").glob("*.png"):
        jpeg = path.with_suffix(".jpg")
        if not jpeg.exists():
            raise ValueError(f"Missing review JPEG: {jpeg}")
        with Image.open(path) as original, Image.open(jpeg) as preview:
            if original.size != preview.size:
                raise ValueError(f"Review dimensions changed: {jpeg}")
            preview.verify()
        replacements[path.relative_to(root).as_posix()] = jpeg.relative_to(root).as_posix()
    for path in [root / "README.md", *(root / "docs").rglob("*.md")]:
        if path.exists():
            text = path.read_text(encoding="utf-8")
            for old, new in replacements.items():
                text = text.replace(old, new)
            path.write_text(text, encoding="utf-8")
    for name in replacements:
        path = root / name
        path.unlink()
        pathlib.Path(str(path) + ".import").unlink(missing_ok=True)
    print(f"Retained {len(replacements)} full-size JPEG review captures.", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=pathlib.Path,
                        default=pathlib.Path(__file__).resolve().parents[1])
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()
    root = args.root.resolve()
    compact_art(root, args.workers)
    compact_voices(root, args.workers)
    compact_screenshots(root)


if __name__ == "__main__":
    main()
