"""Books must merge without silent omissions, conflicting IDs, or inflated prose."""
import json
import pathlib
import tempfile
import unittest

from tools.story_data import authored_word_count, load_story


def base_story():
    return {
        "version": 1, "title": "Fixture", "start": "arrival",
        "chapters": {"book_i": {"title": "Opening"}},
        "characters": {"narrator": {"name": "Narrator"}},
        "nodes": {"arrival": {"speaker": "narrator", "text": "Three honest words.",
                              "next": "arrival"}},
    }


def next_book():
    return {
        "chapters": {"book_ii": {"title": "A label should never count"}},
        "characters": {"visitor": {"name": "Many more uncounted labels"}},
        "nodes": {"second": {"speaker": "visitor", "text": "Five freshly authored scene words.",
                             "ending": "A label is excluded"}},
    }


class StoryDataTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = pathlib.Path(self.temporary.name)
        (self.root / "data/books").mkdir(parents=True)
        self.base = base_story()

    def write(self, path, value):
        (self.root / path).write_text(json.dumps(value), encoding="utf-8")

    def load(self):
        self.write("data/story.json", self.base)
        return load_story(self.root)

    def test_legacy_campaign_has_identical_ids_and_save_version(self):
        story = self.load()
        self.assertEqual(story, self.base)
        self.assertEqual(story["version"], 1)

    def test_merge_counts_only_scene_prose_and_preserves_cross_book_links(self):
        self.base["books"] = ["data/books/book_ii.json"]
        self.base["nodes"]["arrival"]["next"] = "second"
        self.write("data/books/book_ii.json", next_book())
        story = self.load()
        self.assertEqual(set(story["nodes"]), {"arrival", "second"})
        self.assertEqual(story["nodes"]["arrival"]["next"], "second")
        self.assertEqual(authored_word_count(story), 8)
        self.assertEqual(len(story["chapters"]), 2)
        self.assertNotIn("visitor", self.base["characters"])

    def test_duplicate_ids_in_every_group_are_rejected(self):
        self.base["books"] = ["data/books/book_ii.json"]
        for group in ("chapters", "characters", "nodes"):
            with self.subTest(group=group):
                book = next_book()
                key = next(iter(self.base[group]))
                book[group][key] = self.base[group][key]
                self.write("data/books/book_ii.json", book)
                with self.assertRaisesRegex(ValueError, "duplicate " + group):
                    self.load()

    def test_conflicts_between_two_parts_are_rejected(self):
        self.base["books"] = ["data/books/a.json", "data/books/b.json"]
        self.write("data/books/a.json", next_book())
        self.write("data/books/b.json", next_book())
        with self.assertRaisesRegex(ValueError, "duplicate chapters"):
            self.load()

    def test_repeated_book_entries_are_rejected(self):
        self.base["books"] = ["data/books/book_ii.json"] * 2
        self.write("data/books/book_ii.json", next_book())
        with self.assertRaisesRegex(ValueError, "Repeated story book"):
            self.load()

    def test_missing_and_malformed_files_are_explicit_failures(self):
        self.base["books"] = ["data/books/book_ii.json"]
        with self.assertRaisesRegex(ValueError, "Missing story book"):
            self.load()
        (self.root / "data/books/book_ii.json").write_text("{not json")
        with self.assertRaisesRegex(ValueError, "Cannot load story file"):
            self.load()

    def test_path_escape_and_external_urls_are_rejected(self):
        for name in ("../outside.json", "/tmp/outside.json", "data/books/../../outside.json",
                     "data/books/../book.json", "data/books/./book.json",
                     "data/books//book.json", "data\\books\\book.json",
                     "https://example.com/book.json", "data/story.json",
                     "data/books/book.txt", 3):
            with self.subTest(name=name):
                self.base["books"] = [name]
                with self.assertRaises(ValueError):
                    self.load()

    def test_symlink_cannot_escape_the_books_directory(self):
        external = self.root / "outside.json"
        external.write_text(json.dumps(next_book()))
        (self.root / "data/books/link.json").symlink_to(external)
        self.base["books"] = ["data/books/link.json"]
        with self.assertRaisesRegex(ValueError, "escapes data/books"):
            self.load()

    def test_schema_and_recursive_manifests_are_rejected(self):
        self.base["books"] = ["data/books/book_ii.json"]
        for value in ([], {"chapters": {}, "characters": {}, "nodes": []},
                      dict(next_book(), books=[]), {"chapters": {}, "nodes": {}}):
            with self.subTest(value=value):
                self.write("data/books/book_ii.json", value)
                with self.assertRaises(ValueError):
                    self.load()
        self.base["books"] = "data/books/book_ii.json"
        with self.assertRaisesRegex(ValueError, "array"):
            self.load()

    def test_duplicate_keys_inside_json_do_not_silently_overwrite_prose(self):
        self.base["books"] = ["data/books/book_ii.json"]
        (self.root / "data/books/book_ii.json").write_text(
            '{"chapters": {}, "characters": {}, "nodes": {"same": {}, "same": {}}}')
        with self.assertRaisesRegex(ValueError, "Duplicate JSON key"):
            self.load()

    def test_invalid_start_fails_after_the_atomic_merge(self):
        self.base["start"] = "missing"
        with self.assertRaisesRegex(ValueError, "start"):
            self.load()


if __name__ == "__main__":
    unittest.main()
