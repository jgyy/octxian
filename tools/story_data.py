"""Load the campaign and its independently authored book files atomically."""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
GROUPS = ("chapters", "characters", "nodes")


def _unique_object(pairs):
    value = {}
    for key, entry in pairs:
        if key in value:
            raise ValueError(f"Duplicate JSON key: {key}")
        value[key] = entry
    return value


def _read(path):
    try:
        raw = json.loads(path.read_text(encoding="utf-8"),
                         object_pairs_hook=_unique_object)
    except (OSError, UnicodeError, ValueError) as error:
        raise ValueError(f"Cannot load story file {path}: {error}") from error
    if not isinstance(raw, dict):
        raise ValueError(f"Story file must be an object: {path}")
    return raw


def _groups(raw, path):
    for group in GROUPS:
        entries = raw.get(group)
        if not isinstance(entries, dict):
            raise ValueError(f"{path}: {group} must be an object")
        for key, entry in entries.items():
            if not key or not isinstance(entry, dict):
                raise ValueError(f"{path}: invalid {group} entry {key!r}")


def book_path(root, name):
    """Books are manifest entries under data/books, never external paths."""
    if not isinstance(name, str) or not name or "\\" in name or ":" in name:
        raise ValueError(f"Invalid book path: {name!r}")
    relative = pathlib.PurePosixPath(name)
    if (relative.is_absolute() or name != relative.as_posix()
            or any(part in ("", ".", "..") for part in name.split("/"))
            or not name.startswith("data/books/")
            or relative.suffix != ".json"):
        raise ValueError(f"Book path must stay under data/books: {name!r}")
    root = pathlib.Path(root).resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root / "data/books"):
        raise ValueError(f"Book path escapes data/books: {name!r}")
    if not path.is_file():
        raise ValueError(f"Missing story book: {name}")
    return path


def load_story(root=ROOT):
    """Merge once; reject missing files and conflicting IDs instead of overwriting."""
    root = pathlib.Path(root).resolve()
    source = root / "data/story.json"
    raw = _read(source)
    raw.setdefault("chapters", {})
    _groups(raw, source)
    books = raw.get("books", [])
    if not isinstance(books, list):
        raise ValueError("Story books must be an array of repository paths")
    merged = dict(raw)
    for group in GROUPS:
        merged[group] = dict(raw[group])
    seen = set()
    for name in books:
        path = book_path(root, name)
        if path in seen:
            raise ValueError(f"Repeated story book: {name}")
        seen.add(path)
        part = _read(path)
        if set(part) != set(GROUPS):
            raise ValueError(f"{name}: book files contain only chapters, characters and nodes")
        _groups(part, name)
        for group in GROUPS:
            overlap = merged[group].keys() & part[group].keys()
            if overlap:
                raise ValueError(f"{name}: duplicate {group} IDs: {', '.join(sorted(overlap))}")
            merged[group].update(part[group])
    if not isinstance(merged.get("start"), str) or merged["start"] not in merged["nodes"]:
        raise ValueError("The campaign start must name a loaded scene")
    return merged


def authored_word_count(story):
    """Count only the prose displayed by playable nodes, excluding labels and notes."""
    return sum(len(node["text"].split()) for node in story["nodes"].values())
