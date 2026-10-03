"""The pinned installer must reuse verified caches and reject modified archives."""
import hashlib
import pathlib
import tempfile
import unittest
from unittest import mock
import zipfile

from tools import bootstrap_godot


class GodotBootstrapTests(unittest.TestCase):
    def test_verified_cache_needs_no_network(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            archive = root / bootstrap_godot.ARCHIVE_NAME
            payload = b"fixture executable"
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr(bootstrap_godot.BINARY_NAME, payload)
            checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
            no_network = mock.Mock(side_effect=AssertionError("Cache reuse must be offline"))
            with mock.patch.object(bootstrap_godot, "EXPECTED_SHA256", checksum):
                binary = bootstrap_godot.install(root, no_network)
            no_network.assert_not_called()
            self.assertEqual(binary.read_bytes(), payload)
            self.assertTrue(binary.stat().st_mode & 0o111)

    def test_modified_cache_is_deleted_without_extraction(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            archive = root / bootstrap_godot.ARCHIVE_NAME
            archive.write_bytes(b"untrusted cached bytes")
            no_network = mock.Mock(side_effect=AssertionError("Existing cache should be verified first"))
            with self.assertRaisesRegex(SystemExit, "checksum mismatch"):
                bootstrap_godot.install(root, no_network)
            no_network.assert_not_called()
            self.assertFalse(archive.exists())
            self.assertFalse((root / bootstrap_godot.BINARY_NAME).exists())


if __name__ == "__main__":
    unittest.main()
