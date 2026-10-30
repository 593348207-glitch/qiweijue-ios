from __future__ import annotations

import argparse
import hashlib
import json
import plistlib
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def verify(root: Path) -> dict:
    info_path = root / "Info.plist"
    if not info_path.is_file():
        raise ValueError("XCFramework Info.plist is missing")
    info = plistlib.loads(info_path.read_bytes())
    libraries = info.get("AvailableLibraries", [])
    slices = []
    for entry in libraries:
        identifier = entry["LibraryIdentifier"]
        library_path = root / identifier / entry["LibraryPath"]
        headers_path = root / identifier / entry.get("HeadersPath", "Headers")
        headers = headers_path / "HCSafeOverlay.h"
        if not library_path.is_file():
            raise ValueError(f"Library slice is missing: {library_path}")
        if not headers.is_file():
            raise ValueError(f"Public header is missing: {headers}")
        slices.append({
            "identifier": identifier,
            "platform": entry.get("SupportedPlatform"),
            "variant": entry.get("SupportedPlatformVariant"),
            "architectures": entry.get("SupportedArchitectures", []),
            "library": str(library_path.relative_to(root)),
            "library_sha256": sha256(library_path),
            "header": str(headers.relative_to(root)),
            "header_sha256": sha256(headers),
        })
    platforms = {(item["platform"], item["variant"]) for item in slices}
    if ("ios", None) not in platforms or ("ios", "simulator") not in platforms:
        raise ValueError(f"Expected iOS device and simulator slices, got {platforms}")
    if any("arm64" not in item["architectures"] for item in slices):
        raise ValueError("Every XCFramework slice must include arm64")
    return {"xcframework": root.name, "format_version": info.get("XCFrameworkFormatVersion"), "slices": slices}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("xcframework", type=Path)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.xcframework)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"passed": True, "slices": len(result["slices"]), "manifest": str(args.manifest)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
