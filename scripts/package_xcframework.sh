#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_DIR="${BUILD_DIR:-$ROOT/build}"
DEVICE_LIB="$BUILD_DIR/iphoneos/libHCSafeOverlay.a"
SIMULATOR_LIB="$BUILD_DIR/iphonesimulator/libHCSafeOverlay.a"
HEADERS="$ROOT/Sources/HCSafeOverlay/include"
OUT="$BUILD_DIR/HCSafeOverlay.xcframework"

for path in "$DEVICE_LIB" "$SIMULATOR_LIB" "$HEADERS/HCSafeOverlay.h"; do
  if [[ ! -f "$path" ]]; then
    echo "Missing required input: $path" >&2
    exit 2
  fi
done

rm -rf "$OUT"
xcodebuild -create-xcframework \
  -library "$DEVICE_LIB" -headers "$HEADERS" \
  -library "$SIMULATOR_LIB" -headers "$HEADERS" \
  -output "$OUT"

python3 "$ROOT/scripts/verify_xcframework.py" "$OUT" \
  --manifest "$BUILD_DIR/HCSafeOverlay.xcframework.manifest.json"

echo "Built $OUT"
