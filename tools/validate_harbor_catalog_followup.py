"""Authenticate the harbor gallery's alignment with established story roles."""
import argparse
import json
import pathlib
import subprocess

from tools.story_data import load_story

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = "f50979b6bb8e3bbed6eec7b866c92377509a964b"
SOURCE_BLOB = "2bf8f3a0afc3e0ecf647f5135976bf6e73e21d78"
AUDIT = "docs/HARBOR_CATALOG_FOLLOWUP_20261008.json"
BEFORE = "An experienced harbor rigger whose work coat and hands carry the wear of rope and weather."
AFTER = "He Ming is a female salt packer and migrant household delegate. Her weathered work coat and saffron scarf belong to the established harbor wage and family-search story; professional rigging and rescue remain Yan Su's work."


def validate(root=ROOT, verify_source=False):
    root = pathlib.Path(root)
    audit = json.loads((root / AUDIT).read_text())
    assert audit["source_commit"] == SOURCE
    assert audit["source_file_sha"] == SOURCE_BLOB
    assert audit["credited_literary_defects"] == 0
    assert audit["before_description"] == BEFORE
    assert audit["after_description"] == AFTER
    world = json.loads((root / "data/world_assets.json").read_text())
    people = {entry["id"]: entry for entry in world["npcs"]}
    assert people["harbor_he_ming"]["description"] == AFTER
    story = load_story(root)
    assert story["characters"]["harbor_he_ming"]["title"] == "Salt packer and migrant household delegate"
    assert "a packer awaiting wages" in story["nodes"]["harbor_p01_006"]["text"]
    assert "Harbor rigger and ordinary rescue foreman" == people["harbor_yan_su"]["description"]
    if verify_source:
        actual = subprocess.check_output(
            ["git", "rev-parse", SOURCE + ":data/world_assets.json"], cwd=root, text=True).strip()
        assert actual == SOURCE_BLOB
        raw = subprocess.check_output(
            ["git", "show", SOURCE + ":data/world_assets.json"], cwd=root, text=True)
        prior = json.loads(raw)
        old = next(entry for entry in prior["npcs"] if entry["id"] == "harbor_he_ming")
        assert old["description"] == BEFORE
    print("HARBOR_CATALOG_FOLLOWUP_OK: existing role aligned; zero new literary credit")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-source", action="store_true")
    validate(verify_source=parser.parse_args().verify_source)
