"""Check continuation repair audits against the current local campaign.

Canonical schema:
    {"source_base": "<40-character commit SHA>", "repairs": [
        {"id": "unique-root-defect", "path": "data/books/book.json",
         "node_id": "existing_scene", "before": "Original complete prose.",
         "after": "Current complete prose.", "reason": "Evidenced defect.",
         "category": "continuity",
         "affected_passages": [
             {"path": "data/story.json", "node_id": "another_scene",
              "before": "Original prose.", "after": "Current prose."}
         ]}
    ]}

Legacy aliases review_base/source_commit and related_changes are normalized.
There is one count per root repair, regardless of its affected passages. A node
may appear only once across the entire audit suite. Optional source_node_paths
maps original node IDs to their original file paths and excludes newly added or
moved nodes. All checks are offline. Without a source index, current anchors
cannot establish historical membership. A nonempty before is not proof of its
authenticity; compare it with the fixed source revision during source review.
These checks do not replace editorial judgment.
"""
import argparse
import json
import pathlib
import re

if __package__:
    from .story_data import load_story
else:
    from story_data import load_story

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_AUDITS = tuple(
    "docs/CONTINUITY_REPAIRS_20261003_" + name + ".json"
    for name in ("OPENING", "COURT", "RING", "CULTIVATION")
)
SOURCE_ALIASES = ("source_base", "review_base", "source_commit")
PASSAGE_ALIASES = ("affected_passages", "related_changes")


def _read_json(path):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f"Duplicate JSON key: {key}")
            value[key] = item
        return value

    try:
        return json.loads(path.read_text(encoding="utf-8"),
                          object_pairs_hook=unique)
    except (OSError, UnicodeError, ValueError) as error:
        raise ValueError(f"Cannot read audit input {path}: {error}") from error


def _text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be nonempty text")
    return value


def _alias(value, keys, label, default=None):
    present = [value[key] for key in keys if key in value]
    if not present:
        return default
    if any(item != present[0] for item in present[1:]):
        raise ValueError(f"{label}: conflicting aliases {', '.join(keys)}")
    return present[0]


def _story_path(value):
    value = _text(value, "passage path")
    path = pathlib.PurePosixPath(value)
    if (path.is_absolute() or value != path.as_posix()
            or any(part in ("", ".", "..") for part in value.split("/"))
            or "\\" in value or ":" in value):
        raise ValueError(f"Invalid story path: {value!r}")
    if value != "data/story.json" and not (
            value.startswith("data/books/") and path.suffix == ".json"):
        raise ValueError(f"Unknown story path: {value!r}")
    return value


def _passage(raw, label):
    if not isinstance(raw, dict):
        raise ValueError(f"{label}: passage must be an object")
    result = {
        "path": _story_path(raw.get("path")),
        "node_id": _text(raw.get("node_id"), label + " node_id"),
        "before": _text(raw.get("before"), label + " before"),
        "after": _text(raw.get("after"), label + " after"),
    }
    if " ".join(result["before"].split()) == " ".join(result["after"].split()):
        raise ValueError(f"{label}: no-op repair")
    return result


def normalize_audit(raw, label="audit"):
    """Return one normalized record per claimed root defect."""
    if not isinstance(raw, dict):
        raise ValueError(f"{label}: audit must be an object")
    source = _alias(raw, SOURCE_ALIASES, label)
    if not isinstance(source, str) or re.fullmatch(r"[0-9a-fA-F]{40}", source) is None:
        raise ValueError(f"{label}: source_base must be a full commit SHA")
    rows = raw.get("repairs")
    if not isinstance(rows, list):
        raise ValueError(f"{label}: repairs must be an array")
    normalized = []
    for number, row in enumerate(rows, 1):
        where = f"{label} repair {number}"
        if not isinstance(row, dict):
            raise ValueError(f"{where}: repair must be an object")
        root_id = _text(row.get("id"), where + " id")
        _text(row.get("reason"), where + " reason")
        _text(row.get("category"), where + " category")
        passages = [_passage(row, where)]
        related = _alias(row, PASSAGE_ALIASES, where, [])
        if not isinstance(related, list):
            raise ValueError(f"{where}: affected_passages must be an array")
        passages.extend(_passage(item, f"{where} affected passage {index}")
                        for index, item in enumerate(related, 1))
        normalized.append({"id": root_id, "passages": passages})
    passage_count = sum(len(row["passages"]) for row in normalized)
    for key in ("total_repairs", "defect_count"):
        if key in raw and (type(raw[key]) is not int or raw[key] != len(normalized)):
            raise ValueError(f"{label}: {key} does not match distinct root records")
    for key in ("changed_passages", "changed_scene_count", "total_edited_nodes",
                "changed_scene_paragraphs"):
        if key in raw and (type(raw[key]) is not int or raw[key] != passage_count):
            raise ValueError(f"{label}: {key} does not match affected passages")
    return {"source_base": source.lower(), "repairs": normalized}


def story_node_index(root=ROOT):
    """Use only loaded campaign files and retain each node's actual origin."""
    root = pathlib.Path(root)
    load_story(root)  # Reject duplicate IDs/keys and unsafe or missing book paths.
    base = _read_json(root / "data/story.json")
    paths = ["data/story.json", *base.get("books", [])]
    index = {}
    for path in paths:
        data = base if path == "data/story.json" else _read_json(root / path)
        for node_id, node in data["nodes"].items():
            index[node_id] = {"path": path, "text": node.get("text")}
    return index


def validate_documents(documents, node_index, source_node_paths=None,
                       expected_source_base=None):
    """Validate current anchors; optionally constrain original membership."""
    if source_node_paths is not None:
        if not isinstance(source_node_paths, dict):
            raise ValueError("source_node_paths must map node IDs to story paths")
        for node_id, path in source_node_paths.items():
            _text(node_id, "source node ID")
            _story_path(path)
    if expected_source_base is not None:
        if not isinstance(expected_source_base, str) or re.fullmatch(
                r"[0-9a-fA-F]{40}", expected_source_base) is None:
            raise ValueError("expected_source_base must be a full commit SHA")
        expected_source_base = expected_source_base.lower()
    audits = [normalize_audit(document, f"audit {index}")
              for index, document in enumerate(documents, 1)]
    roots, nodes, bases = set(), set(), set()
    for audit in audits:
        bases.add(audit["source_base"])
        if expected_source_base is not None and audit["source_base"] != expected_source_base:
            raise ValueError("Audit source_base differs from the required source revision")
        for repair in audit["repairs"]:
            if repair["id"] in roots:
                raise ValueError(f"Duplicate root repair ID: {repair['id']}")
            roots.add(repair["id"])
            for passage in repair["passages"]:
                node_id, path = passage["node_id"], passage["path"]
                if node_id in nodes:
                    raise ValueError(f"Duplicate affected node: {node_id}")
                nodes.add(node_id)
                current = node_index.get(node_id)
                if current is None:
                    raise ValueError(f"Unknown story node: {node_id}")
                if current["path"] != path:
                    raise ValueError(f"Story path mismatch for {node_id}: {path}")
                if source_node_paths is not None:
                    if node_id not in source_node_paths:
                        raise ValueError(f"New node excluded from repairs: {node_id}")
                    if source_node_paths[node_id] != path:
                        raise ValueError(f"Source path mismatch for {node_id}: {path}")
                if passage["after"] != current["text"]:
                    raise ValueError(f"Stale after anchor for {node_id}")
    if len(bases) > 1:
        raise ValueError("Audit suite must use one fixed source_base")
    return {
        "source_base": next(iter(bases), None),
        "audit_count": len(audits),
        "repair_count": len(roots),
        "affected_node_count": len(nodes),
        "source_membership_checked": source_node_paths is not None,
    }


def validate_audits(root=ROOT, audit_paths=DEFAULT_AUDITS,
                    source_node_paths=None, expected_source_base=None):
    root = pathlib.Path(root)
    documents = [_read_json(root / path) for path in audit_paths]
    return validate_documents(documents, story_node_index(root),
                              source_node_paths, expected_source_base)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audits", nargs="*", help="Audit JSON paths, relative to root")
    parser.add_argument("--root", type=pathlib.Path, default=ROOT)
    parser.add_argument("--source-base", help="Require this fixed source commit SHA")
    parser.add_argument("--source-node-index",
                        help="JSON mapping original node IDs to source file paths")
    args = parser.parse_args(argv)
    try:
        source = (_read_json(args.root / args.source_node_index)
                  if args.source_node_index else None)
        report = validate_audits(args.root, args.audits or DEFAULT_AUDITS,
                                 source, args.source_base)
    except ValueError as error:
        parser.exit(1, f"Continuation audit validation failed: {error}\n")
    print(f"Validated {report['audit_count']} audits: "
          f"{report['repair_count']} distinct repairs; "
          f"{report['affected_node_count']} affected current story nodes.")
    if not report["source_membership_checked"]:
        print("Historical node membership was not checked; source review is required.")
    print("Current anchors and audit structure do not replace editorial judgment.")
    return report


if __name__ == "__main__":
    main()
