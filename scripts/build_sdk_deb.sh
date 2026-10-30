#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_DIR="${BUILD_DIR:-$ROOT/build}"
XCFRAMEWORK="$BUILD_DIR/HCSafeOverlay.xcframework"
PKG_ROOT="$BUILD_DIR/sdk-deb-root"
CONTROL_DIR="$PKG_ROOT/DEBIAN"
FRAMEWORKS_DIR="$PKG_ROOT/var/jb/Library/Developer/Frameworks"
DEB="$BUILD_DIR/HCSafeOverlay-UI-SDK_1.0.0_iphoneos-arm64.deb"

if [[ ! -d "$XCFRAMEWORK" ]]; then
  echo "Missing XCFramework: $XCFRAMEWORK" >&2
  exit 2
fi
if ! command -v dpkg-deb >/dev/null 2>&1; then
  echo "dpkg-deb is required" >&2
  exit 2
fi

rm -rf "$PKG_ROOT"
mkdir -p "$CONTROL_DIR" "$FRAMEWORKS_DIR"
cp "$ROOT/packaging/sdk-control" "$CONTROL_DIR/control"
cp -R "$XCFRAMEWORK" "$FRAMEWORKS_DIR/HCSafeOverlay.xcframework"
chmod -R a+rX "$PKG_ROOT"
mkdir -p "$BUILD_DIR"
rm -f "$DEB"
dpkg-deb --root-owner-group --build "$PKG_ROOT" "$DEB"
echo "Built $DEB"
