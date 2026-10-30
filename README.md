# Qiweijue iOS UI-only overlay prototype

This repository builds a small UIKit static library for a floating button and a diagnostic panel. Its click path performs a bundle/version/mapping gate before showing UI and contains no Unity/game-data bridge.

## Build

On macOS with Xcode command-line tools installed:

```sh
SDK=iphoneos ARCHS=arm64 scripts/build_framework.sh
SDK=iphonesimulator ARCHS=arm64 scripts/build_framework.sh
```

Outputs are written to `build/<sdk>/libHCSafeOverlay.a`. The source has a minimum iOS deployment target of 15.0.

## Tests

```sh
python3 tests/ui_only_harness.py --out build/ui_only_harness.json
```

GitHub Actions runs the state-machine tests and builds device/simulator arm64 static libraries on a macOS runner. The workflow uploads build artifacts; it does not sign or package a game tweak.

## Integration contract

The host app supplies its own `UIWindow` and constructs `HCSafeOverlay` with the expected bundle identifier, short version, and a mapping-verification boolean. Keep that boolean false until a separate version check has succeeded. The current prototype only displays and dismisses UI. Do not connect a game/native bridge to this diagnostic build.
