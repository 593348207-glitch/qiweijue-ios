# Qiweijue iOS UI-only overlay prototype

This repository builds a small UIKit static library for a floating button and a diagnostic panel. Its click path performs a bundle/version/mapping gate before showing UI and contains no Unity/game-data bridge.

## Build

On macOS with Xcode command-line tools installed:

```sh
SDK=iphoneos ARCHS=arm64 scripts/build_framework.sh
SDK=iphonesimulator ARCHS=arm64 scripts/build_framework.sh
```

Outputs are written to `build/<sdk>/libHCSafeOverlay.a`. After both slices are built, package and verify them with:

```sh
bash scripts/package_xcframework.sh
```

This creates `build/HCSafeOverlay.xcframework` and `build/HCSafeOverlay.xcframework.manifest.json`. The verifier checks device and simulator platform declarations, arm64 architecture, public header, and per-slice SHA-256 values. The source has a minimum iOS deployment target of 15.0.

## Tests

```sh
python3 tests/ui_only_harness.py --out build/ui_only_harness.json
```

GitHub Actions runs the state-machine tests, builds device/simulator arm64 static libraries, packages and verifies the XCFramework, then builds and verifies a rootless developer SDK DEB.

The rootless developer SDK DEB installs only `HCSafeOverlay.xcframework` under `/var/jb/Library/Developer/Frameworks/`; it contains no MobileSubstrate filter, game launch hook, or process-injection entry point. This package is a build dependency for a host application and does not add an overlay to the game by itself. Artifact validation checks the Debian control identity and rejects injection/game payload paths.

## Integration contract

The host app supplies its own `UIWindow` and constructs `HCSafeOverlay` with the expected bundle identifier, short version, and a mapping-verification boolean. Keep that boolean false until a separate version check has succeeded. The current prototype only displays and dismisses UI. Do not connect a game/native bridge to this diagnostic build.
