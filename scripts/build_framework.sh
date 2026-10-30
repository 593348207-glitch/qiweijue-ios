#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="${OUT_DIR:-$ROOT/build}"
SDK="${SDK:-iphoneos}"
ARCHS="${ARCHS:-arm64}"
MIN_IOS="${MIN_IOS:-15.0}"
CLANG="$(xcrun --sdk "$SDK" --find clang++)"
SDKROOT="$(xcrun --sdk "$SDK" --show-sdk-path)"
if [[ "$SDK" == "iphonesimulator" ]]; then
  TARGET="arm64-apple-ios${MIN_IOS}-simulator"
else
  TARGET="arm64-apple-ios${MIN_IOS}"
fi
mkdir -p "$OUT_DIR/$SDK"

"$CLANG" \
  -target "$TARGET" \
  -isysroot "$SDKROOT" \
  -arch "$ARCHS" \
  -std=c++17 \
  -fobjc-arc \
  -fvisibility=hidden \
  -Wall -Wextra -Werror \
  -I "$ROOT/Sources/HCSafeOverlay/include" \
  -c "$ROOT/Sources/HCSafeOverlay/HCSafeOverlay.mm" \
  -o "$OUT_DIR/$SDK/HCSafeOverlay.o"

"$(xcrun --sdk "$SDK" --find libtool)" \
  -static -o "$OUT_DIR/$SDK/libHCSafeOverlay.a" \
  "$OUT_DIR/$SDK/HCSafeOverlay.o"

echo "Built $OUT_DIR/$SDK/libHCSafeOverlay.a"
