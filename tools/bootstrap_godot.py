"""Install the pinned official Godot archive, verifying its published SHA-256."""
import hashlib
import pathlib
import urllib.request
import zipfile

VERSION = "4.7.2-stable"
# Official release asset digest, verified 2026-10-02:
# https://github.com/godotengine/godot/releases/tag/4.7.2-stable
EXPECTED_SHA256 = "cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4"
ARCHIVE_NAME = f"Godot_v{VERSION}_linux.x86_64.zip"
BINARY_NAME = f"Godot_v{VERSION}_linux.x86_64"
DOWNLOAD_URL = f"https://github.com/godotengine/godot/releases/download/{VERSION}/{ARCHIVE_NAME}"


def install(dest=pathlib.Path(".cache/godot"), downloader=None):
    dest = pathlib.Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    archive = dest / ARCHIVE_NAME
    if not archive.exists():
        partial = dest / (ARCHIVE_NAME + ".part")
        try:
            (downloader or urllib.request.urlretrieve)(DOWNLOAD_URL, partial)
            partial.replace(archive)
        finally:
            partial.unlink(missing_ok=True)
    with archive.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    if digest != EXPECTED_SHA256:
        archive.unlink()
        raise SystemExit("Godot archive checksum mismatch")
    with zipfile.ZipFile(archive) as bundle:
        # Extract only the expected executable from the verified release.
        bundle.extract(BINARY_NAME, dest)
    binary = dest / BINARY_NAME
    binary.chmod(0o755)
    return binary


if __name__ == "__main__":
    print(install())
