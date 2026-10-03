"""Mixed PCM/Vorbis narration must decode and remain tied to its authored text."""
import contextlib
import hashlib
import io
import json
import pathlib
import shutil
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import soundfile as sf

from tools.voice_assets import audio_metadata, clip_entry, reusable_clip, validate_clip


class VoiceAssetTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = pathlib.Path(self.temporary.name)
        self.folder = self.root / "assets/generated/voices"
        self.folder.mkdir(parents=True)
        self.text = "An actual spoken scene."
        self.digest = hashlib.sha256(self.text.encode()).hexdigest()
        # Audible signal for decoder tests, not counted as production narration.
        self.samples = (np.sin(np.arange(2205) * .1) * .25).astype("float32")

    def write(self, extension="wav", samples=None, subtype=None):
        path = self.folder / ("scene." + extension)
        subtype = subtype or ("PCM_16" if extension == "wav" else "VORBIS")
        sf.write(path, self.samples if samples is None else samples,
                 22050, subtype=subtype)
        return path

    def test_legacy_pcm_is_reused_without_changing_its_bytes(self):
        path = self.write()
        original = path.read_bytes()
        record = clip_entry(self.root, path, self.digest)
        for field in ("format", "codec", "channels", "sample_rate"):
            record.pop(field)
        reused = reusable_clip(self.root, "scene", self.text, record)
        self.assertEqual(reused[0], path)
        self.assertEqual(reused[1]["codec"], "pcm_s16le")
        self.assertEqual(path.read_bytes(), original)

    def test_vorbis_decodes_and_records_its_real_format(self):
        path = self.write("ogg")
        record = clip_entry(self.root, path, self.digest)
        loaded, metadata = validate_clip(self.root, "scene", self.text, record)
        self.assertEqual(loaded, path)
        self.assertEqual(metadata, {"format": "ogg", "codec": "vorbis", "channels": 1,
                                    "sample_rate": 22050, "seconds": .1})

    def test_text_and_file_hashes_both_control_resumption(self):
        path = self.write()
        record = clip_entry(self.root, path, self.digest)
        self.assertIsNone(reusable_clip(self.root, "scene", "Edited scene.", record))
        record["sha256"] = "wrong"
        self.assertIsNone(reusable_clip(self.root, "scene", self.text, record))
        with self.assertRaisesRegex(ValueError, "bytes changed"):
            validate_clip(self.root, "scene", self.text, record)

    def test_actual_codec_channels_and_duration_are_validated(self):
        path = self.write("ogg")
        record = clip_entry(self.root, path, self.digest)
        for field, value in (("codec", "pcm_s16le"), ("channels", 2),
                             ("sample_rate", 48000), ("seconds", .9),
                             ("seconds", float("nan"))):
            with self.subTest(field=field, value=value):
                corrupted = dict(record, **{field: value})
                self.assertIsNone(reusable_clip(self.root, "scene", self.text, corrupted))
        disguised = self.folder / "disguised.wav"
        shutil.copyfile(path, disguised)
        with self.assertRaisesRegex(ValueError, "codec"):
            audio_metadata(disguised)

    def test_silent_stereo_and_non_pcm16_wavs_are_rejected(self):
        for samples, subtype in ((np.zeros(2205), "PCM_16"),
                                 (np.column_stack((self.samples, self.samples)), "PCM_16"),
                                 (self.samples, "PCM_24")):
            with self.subTest(subtype=subtype, dimensions=samples.ndim):
                with self.assertRaises(ValueError):
                    audio_metadata(self.write(samples=samples, subtype=subtype))

    def test_missing_or_invalid_audio_is_never_reused(self):
        record = {"file": "assets/generated/voices/scene.ogg",
                  "text_sha256": self.digest, "sha256": "missing", "seconds": .1}
        self.assertIsNone(reusable_clip(self.root, "scene", self.text, record))
        path = self.folder / "scene.ogg"
        path.write_bytes(b"not an Ogg bitstream")
        record["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertIsNone(reusable_clip(self.root, "scene", self.text, record))

    def test_unexpected_paths_and_unsafe_scene_ids_are_rejected(self):
        path = self.write()
        record = clip_entry(self.root, path, self.digest)
        record["file"] = "assets/generated/voices/../../outside.wav"
        self.assertIsNone(reusable_clip(self.root, "scene", self.text, record))
        record["file"] = "assets/generated/voices/scene.wav"
        self.assertIsNone(reusable_clip(self.root, "../scene", self.text, record))

    def test_reused_vorbis_without_encoder_record_keeps_truthful_provenance(self):
        from tools import generate_voices

        path = self.write("ogg")
        original = path.read_bytes()
        record = clip_entry(self.root, path, self.digest)
        model = self.root / "fixture_model.onnx"
        model.write_bytes(b"fixture model, never used for synthesis")
        card = self.root / "MODEL_CARD"
        card.write_text("Test-only model provenance.")
        (self.root / "data").mkdir()
        story = {"version": 1, "start": "scene", "chapters": {},
                 "characters": {"narrator": {"name": "Narrator"}},
                 "nodes": {"scene": {"speaker": "narrator", "text": self.text,
                                     "ending": "Fixture"}}}
        (self.root / "data/story.json").write_text(json.dumps(story))
        manifest_path = self.folder / "manifest.json"
        manifest_path.write_text(json.dumps({
            "model_sha256": hashlib.sha256(model.read_bytes()).hexdigest(),
            "lines": {"scene": record}}))

        def download(name):
            return card if name == "MODEL_CARD" else model

        with patch.object(generate_voices, "ROOT", self.root), \
                patch.object(generate_voices, "OUT", self.folder), \
                patch.object(generate_voices, "CACHE", self.root / "cache"), \
                patch.object(generate_voices, "download", side_effect=download), \
                patch.object(generate_voices.PiperVoice, "load", return_value=object()), \
                contextlib.redirect_stdout(io.StringIO()):
            generate_voices.main()
        restored = json.loads(manifest_path.read_text())["lines"]["scene"]
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(restored["codec"], "vorbis")
        self.assertEqual(restored["encoding"],
                         "Retained Vorbis; original encoder settings unrecorded")
        self.assertNotIn("quality 3", restored["encoding"])

    def test_failed_batch_resumes_completed_clips_and_retains_future_legacy_records(self):
        from tools import generate_voices

        texts = {"first": "A revised opening.", "second": "A revised middle.",
                 "third": "An unchanged ending."}
        records = {}
        originals = {}
        for node_id, text in texts.items():
            path = self.folder / (node_id + ".wav")
            sf.write(path, self.samples, 22050, subtype="PCM_16")
            previous_text = text if node_id == "third" else "An older draft."
            digest = hashlib.sha256(previous_text.encode()).hexdigest()
            records[node_id] = clip_entry(self.root, path, digest)
            originals[node_id] = path.read_bytes()
        model = self.root / "fixture_model.onnx"
        model.write_bytes(b"fixture model, never used for synthesis")
        card = self.root / "MODEL_CARD"
        card.write_text("Test-only model provenance.")
        (self.root / "data").mkdir()
        story = {"version": 1, "start": "first", "chapters": {},
                 "characters": {"narrator": {"name": "Narrator"}},
                 "nodes": {node_id: {"speaker": "narrator", "text": text,
                                    "ending": "Fixture"}
                           for node_id, text in texts.items()}}
        (self.root / "data/story.json").write_text(json.dumps(story))
        manifest_path = self.folder / "manifest.json"
        manifest_path.write_text(json.dumps({
            "model_sha256": hashlib.sha256(model.read_bytes()).hexdigest(),
            "lines": records}))

        rendered = []

        def render(voice, text, output, length_scale):
            rendered.append(output.stem)
            if output.stem == "second" and rendered == ["first", "second"]:
                raise RuntimeError("fixture interruption")
            sf.write(output, self.samples, 22050, subtype="VORBIS")
            return audio_metadata(output)

        def download(name):
            return card if name == "MODEL_CARD" else model

        with patch.object(generate_voices, "ROOT", self.root), \
                patch.object(generate_voices, "OUT", self.folder), \
                patch.object(generate_voices, "CACHE", self.root / "cache"), \
                patch.object(generate_voices, "download", side_effect=download), \
                patch.object(generate_voices.PiperVoice, "load", return_value=object()), \
                patch.object(generate_voices, "render_clip", side_effect=render), \
                contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(RuntimeError, "fixture interruption"):
                generate_voices.main()
            checkpoint = json.loads(manifest_path.read_text())["lines"]
            completed = self.folder / "first.ogg"
            completed_bytes = completed.read_bytes()
            self.assertIsNotNone(reusable_clip(
                self.root, "first", texts["first"], checkpoint["first"]))
            self.assertEqual(checkpoint["third"], records["third"])
            self.assertEqual((self.folder / "third.wav").read_bytes(), originals["third"])
            self.assertFalse((self.folder / "first.wav").exists())

            rendered.clear()
            generate_voices.main()

        self.assertEqual(rendered, ["second"])
        self.assertEqual(completed.read_bytes(), completed_bytes)
        self.assertEqual((self.folder / "third.wav").read_bytes(), originals["third"])
        self.assertFalse((self.folder / "second.wav").exists())
        final = json.loads(manifest_path.read_text())["lines"]
        self.assertEqual(set(final), set(texts))
        for node_id, text in texts.items():
            self.assertIsNotNone(reusable_clip(self.root, node_id, text, final[node_id]))

    def test_removed_clips_survive_if_the_final_checkpoint_cannot_be_committed(self):
        from tools import generate_voices

        kept = self.write()
        removed = self.folder / "removed.wav"
        removed.write_bytes(kept.read_bytes())
        model = self.root / "fixture_model.onnx"
        model.write_bytes(b"fixture model, never used for synthesis")
        card = self.root / "MODEL_CARD"
        card.write_text("Test-only model provenance.")
        (self.root / "data").mkdir()
        story = {"version": 1, "start": "scene", "chapters": {},
                 "characters": {"narrator": {"name": "Narrator"}},
                 "nodes": {"scene": {"speaker": "narrator", "text": self.text,
                                     "ending": "Fixture"}}}
        (self.root / "data/story.json").write_text(json.dumps(story))
        manifest_path = self.folder / "manifest.json"
        manifest_path.write_text(json.dumps({
            "model_sha256": hashlib.sha256(model.read_bytes()).hexdigest(),
            "lines": {"scene": clip_entry(self.root, kept, self.digest),
                      "removed": clip_entry(self.root, removed, self.digest)}}))
        previous = manifest_path.read_bytes()
        removed_bytes = removed.read_bytes()

        def download(name):
            return card if name == "MODEL_CARD" else model

        with patch.object(generate_voices, "ROOT", self.root), \
                patch.object(generate_voices, "OUT", self.folder), \
                patch.object(generate_voices, "CACHE", self.root / "cache"), \
                patch.object(generate_voices, "download", side_effect=download), \
                patch.object(generate_voices.PiperVoice, "load", return_value=object()), \
                patch.object(generate_voices, "render_clip") as render, \
                patch.object(pathlib.Path, "replace", side_effect=OSError("fixture disk error")), \
                contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(OSError, "fixture disk error"):
                generate_voices.main()
        render.assert_not_called()
        self.assertEqual(manifest_path.read_bytes(), previous)
        self.assertEqual(removed.read_bytes(), removed_bytes)

    def test_failed_manifest_replace_preserves_the_previous_checkpoint(self):
        from tools.generate_voices import _write_manifest

        path = self.folder / "manifest.json"
        previous = b'{"lines": {"previous": {}}}\n'
        path.write_bytes(previous)
        with patch.object(pathlib.Path, "replace", side_effect=OSError("fixture disk error")):
            with self.assertRaisesRegex(OSError, "fixture disk error"):
                _write_manifest(path, {"lines": {"new": {}}})
        self.assertEqual(path.read_bytes(), previous)
        self.assertEqual(list(self.folder.iterdir()), [path])

    @unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg is installed in game CI")
    def test_new_synthesis_keeps_only_a_real_vorbis_clip(self):
        from tools.generate_voices import render_clip

        samples = (self.samples * 32767).astype("<i2")

        class FixtureVoice:
            def synthesize_wav(self, text, output, syn_config):
                output.setnchannels(1)
                output.setsampwidth(2)
                output.setframerate(22050)
                output.writeframes(samples.tobytes())

        output = self.folder / "scene.ogg"
        metadata = render_clip(FixtureVoice(), self.text, output, 1.04)
        self.assertEqual(metadata["codec"], "vorbis")
        self.assertEqual(metadata["channels"], 1)
        self.assertEqual(list(self.folder.iterdir()), [output])
        self.assertIsNotNone(reusable_clip(
            self.root, "scene", self.text, clip_entry(self.root, output, self.digest)))


if __name__ == "__main__":
    unittest.main()
