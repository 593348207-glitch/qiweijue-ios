from __future__ import annotations

import argparse
import hashlib
import io
import json
import tarfile
from pathlib import Path

EXPECTED_CONTROL = "Package: com.codev.hercomeback.ui-sdk"
EXPECTED_PREFIX = "var/jb/Library/Developer/Frameworks/HCSafeOverlay.xcframework/"
FORBIDDEN = ["MobileSubstrate", "DynamicLibraries", "HerComebackTools.plist", "TweakEntry", "MSHookFunction", "UnityFramework"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("deb", type=Path)
    ap.add_argument("--manifest", type=Path, required=True)
    args = ap.parse_args()
    blob = args.deb.read_bytes()
    if not blob.startswith(b"!<arch>\n"):
        raise SystemExit("not an ar/deb archive")
    members = {}
    offset = 8
    while offset + 60 <= len(blob):
        header = blob[offset:offset + 60]
        if header[58:60] != b"`\n":
            raise SystemExit(f"invalid ar header at {offset}")
        name = header[:16].decode("ascii", "replace").strip().rstrip("/")
        size = int(header[48:58].decode("ascii").strip())
        start = offset + 60
        members[name] = blob[start:start + size]
        offset = start + size + (size & 1)
    if members.get("debian-binary", b"").strip() != b"2.0":
        raise SystemExit("bad debian-binary marker")
    control_member = next((name for name in members if name.startswith("control.tar")), None)
    data_member = next((name for name in members if name.startswith("data.tar")), None)
    if not control_member or not data_member:
        raise SystemExit("missing control/data archive")
    with tarfile.open(fileobj=io.BytesIO(members[control_member]), mode="r:*") as tf:
        control_file = next((m for m in tf.getmembers() if m.isfile() and m.name.lstrip("./") == "control"), None)
        if not control_file:
            raise SystemExit("control file is missing from control archive")
        control = tf.extractfile(control_file).read().decode("utf-8", "replace")
    with tarfile.open(fileobj=io.BytesIO(members[data_member]), mode="r:*") as tf:
        files = [m.name.lstrip("./") for m in tf.getmembers() if m.isfile()]
        framework = next((m for m in tf.getmembers() if m.name.endswith("/Info.plist") and m.isfile()), None)
    if EXPECTED_CONTROL not in control:
        raise SystemExit("package identity mismatch")
    if not any(path.startswith(EXPECTED_PREFIX) for path in files):
        raise SystemExit("XCFramework missing from developer framework path")
    hits = [marker for marker in FORBIDDEN if any(marker in path for path in files)]
    if hits:
        raise SystemExit(f"forbidden injection/game payload paths: {hits}")
    manifest = {"deb": str(args.deb), "size": len(blob), "sha256": hashlib.sha256(blob).hexdigest().upper(), "package": "com.codev.hercomeback.ui-sdk", "payload_paths": sorted(files), "forbidden_path_hits": hits, "passed": True}
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"passed": True, "package": manifest["package"], "payload_files": len(files), "forbidden_path_hits": hits}, ensure_ascii=False))


if __name__ == "__main__":
    main()
