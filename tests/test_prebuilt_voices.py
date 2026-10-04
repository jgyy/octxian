"""Draft narration must never replace a scene with stale or unverified speech."""
import hashlib
import json
import pathlib
import tempfile
import unittest

import numpy as np
import soundfile as sf

from tools.prebuilt_voices import load_prebuilt, adopt_prebuilt, PREBUILD_FOLDER
from tools.voice_assets import VOICE_FOLDER, clip_entry, validate_clip
from tools.prebuild_voices import draft_nodes


class PrebuiltNarrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = pathlib.Path(self.temporary.name)
        self.cache = self.root / PREBUILD_FOLDER
        self.folder = self.cache / VOICE_FOLDER
        self.folder.mkdir(parents=True)
        self.text = "A saved, actually authored draft scene."
        self.source = self.folder / "draft.ogg"
        samples = (np.sin(np.arange(2205) * .1) * .25).astype("float32")
        sf.write(self.source, samples, 22050, subtype="VORBIS")
        digest = hashlib.sha256(self.text.encode()).hexdigest()
        self.record = clip_entry(self.cache, self.source, digest)
        self.manifest = {"model_sha256": "model-one", "lines": {"draft": self.record}}
        (self.folder / "manifest.json").write_text(json.dumps(self.manifest))

    def test_valid_cached_speech_retains_bytes_and_decodes_in_live_location(self):
        cache, lines = load_prebuilt(self.root, "model-one")
        original = self.source.read_bytes()
        adopted = adopt_prebuilt(self.root, cache, "draft", self.text, lines["draft"])
        self.assertIsNotNone(adopted)
        self.assertEqual(adopted[0].read_bytes(), original)
        loaded, metadata = validate_clip(self.root, "draft", self.text, self.record)
        self.assertEqual(loaded, adopted[0])
        self.assertEqual(metadata["codec"], "vorbis")

    def test_changed_model_cannot_supply_live_narration(self):
        _, lines = load_prebuilt(self.root, "model-two")
        self.assertEqual(lines, {})
        self.assertFalse((self.root / VOICE_FOLDER / "draft.ogg").exists())

    def test_changed_text_does_not_overwrite_an_existing_clip(self):
        destination = self.root / VOICE_FOLDER / "draft.ogg"
        destination.parent.mkdir(parents=True)
        destination.write_bytes(b"existing clip remains untouched")
        self.assertIsNone(adopt_prebuilt(self.root, self.cache, "draft",
                                        "A different later scene.", self.record))
        self.assertEqual(destination.read_bytes(), b"existing clip remains untouched")

    def test_corrupt_cached_audio_is_rejected(self):
        self.source.write_bytes(b"not an Ogg")
        self.assertIsNone(adopt_prebuilt(self.root, self.cache, "draft",
                                        self.text, self.record))
        self.assertFalse((self.root / VOICE_FOLDER / "draft.ogg").exists())

    def test_hash_correct_silent_audio_still_cannot_be_adopted(self):
        sf.write(self.source, np.zeros(2205, dtype="float32"), 22050, subtype="VORBIS")
        record = dict(self.record, sha256=hashlib.sha256(self.source.read_bytes()).hexdigest())
        self.assertIsNone(adopt_prebuilt(self.root, self.cache, "draft", self.text, record))

    def test_bad_checkpoint_falls_back_to_fresh_generation(self):
        (self.folder / "manifest.json").write_text("{interrupted")
        self.assertEqual(load_prebuilt(self.root, "model-one")[1], {})


class DraftIndexTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = pathlib.Path(self.temporary.name)
        (self.root / "data/books").mkdir(parents=True)
        (self.root / "docs").mkdir()
        self.active = {"speaker": "narrator", "actor": "lin_yue",
                       "text": "The already integrated scene.", "ending": "End"}
        story = {"version": 1, "title": "Fixture", "start": "active",
                 "characters": {}, "chapters": {}, "nodes": {"active": self.active}, "books": []}
        (self.root / "data/story.json").write_text(json.dumps(story))
        self.name = "data/books/book_xii_canal_01.json"
        (self.root / "docs/DRAFT_BOOKS_20261003.json").write_text(json.dumps({"parts": [self.name]}))
        self.book = {"chapters": {}, "characters": {}, "nodes": {
            "draft": {"speaker": "narrator", "text": "A distinct saved draft.",
                      "next": "not_yet_authored"}}}
        self.write_book()

    def write_book(self):
        (self.root / self.name).write_text(json.dumps(self.book))

    def test_pending_links_do_not_add_draft_nodes_to_the_live_story(self):
        self.assertEqual(set(draft_nodes(self.root)), {"draft"})
        live = json.loads((self.root / "data/story.json").read_text())
        self.assertEqual(set(live["nodes"]), {"active"})

    def test_live_text_cannot_be_shadowed_by_a_draft(self):
        self.book["nodes"]["active"] = dict(self.active, text="A silently replaced active scene.")
        self.write_book()
        with self.assertRaises(ValueError):
            draft_nodes(self.root)

    def test_readability_limit_applies_to_saved_draft_speech(self):
        self.book["nodes"]["draft"]["text"] = "word " * 101
        self.write_book()
        with self.assertRaises(ValueError):
            draft_nodes(self.root)

    def test_duplicate_draft_scene_ids_are_rejected(self):
        other = "data/books/book_xiii_forest_01.json"
        (self.root / other).write_text(json.dumps(self.book))
        (self.root / "docs/DRAFT_BOOKS_20261003.json").write_text(
            json.dumps({"parts": [self.name, other]}))
        with self.assertRaises(ValueError):
            draft_nodes(self.root)


if __name__ == "__main__":
    unittest.main()
