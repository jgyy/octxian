"""Download the pinned official Godot release and verify its published SHA-256."""
import hashlib
import json
import pathlib
import urllib.request
import zipfile

VERSION = "4.7.2-stable"
DEST = pathlib.Path(".cache/godot")
DEST.mkdir(parents=True, exist_ok=True)
request = urllib.request.Request(
    f"https://api.github.com/repos/godotengine/godot/releases/tags/{VERSION}",
    headers={"User-Agent": "jade-vow-ci"},
)
with urllib.request.urlopen(request, timeout=90) as response:
    release = json.load(response)
name = f"Godot_v{VERSION}_linux.x86_64.zip"
asset = next(a for a in release["assets"] if a["name"] == name)
archive = DEST / name
if not archive.exists():
    urllib.request.urlretrieve(asset["browser_download_url"], archive)
digest = asset.get("digest", "")
if not digest.startswith("sha256:"):
    raise SystemExit("Official release has no SHA-256; refusing unverified binary")
if hashlib.sha256(archive.read_bytes()).hexdigest() != digest.split(":", 1)[1]:
    archive.unlink()
    raise SystemExit("Godot archive checksum mismatch")
with zipfile.ZipFile(archive) as bundle:
    bundle.extractall(DEST)
binary = DEST / f"Godot_v{VERSION}_linux.x86_64"
binary.chmod(0o755)
print(binary)
