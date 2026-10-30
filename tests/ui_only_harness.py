from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class VersionGate:
    bundle_id: str
    short_version: str
    metadata_version: int
    mapping_passed: bool

    def check(self, expected_bundle: str, expected_version: str, expected_metadata: int):
        if self.bundle_id != expected_bundle:
            return False, "bundle_id_mismatch"
        if self.short_version != expected_version:
            return False, "game_version_mismatch"
        if self.metadata_version != expected_metadata:
            return False, "metadata_version_mismatch"
        if not self.mapping_passed:
            return False, "native_mapping_not_verified"
        return True, "ok"


@dataclass
class MockBridge:
    calls: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Rect:
    x: float
    y: float
    width: float
    height: float

    def contains(self, point: tuple[float, float]) -> bool:
        px, py = point
        return self.x <= px < self.x + self.width and self.y <= py < self.y + self.height


def passthrough_hit(point: tuple[float, float], button: Rect, panel: Rect | None) -> str:
    if button.contains(point):
        return "floating_button"
    if panel and panel.contains(point):
        return "panel"
    return "underlying_game"


@dataclass
class PanelController:
    gate: VersionGate
    bridge: MockBridge
    expected_bundle: str
    expected_version: str
    expected_metadata: int
    visible: bool = False
    status: str = "closed"
    error: str | None = None

    def on_float_button_click(self):
        ok, reason = self.gate.check(self.expected_bundle, self.expected_version, self.expected_metadata)
        if not ok:
            self.visible = False
            self.status = "blocked"
            self.error = reason
            return self.state()
        if self.visible:
            self.visible = False
            self.status = "closed"
            self.error = None
            return self.state()
        self.visible = True
        self.status = "ui_only"
        self.error = None
        return self.state()

    def state(self):
        return {"visible": self.visible, "status": self.status, "error": self.error, "bridge_calls": list(self.bridge.calls)}


def run_cases():
    cases = []
    bridge = MockBridge()
    panel = PanelController(VersionGate("com.judian.hercomeback.ios", "1.1.110101749", 31, True), bridge, "com.judian.hercomeback.ios", "1.1.110101749", 31)
    state = panel.on_float_button_click()
    cases.append({"name": "verified_version_opens_ui_only", "state": state, "passed": state["status"] == "ui_only" and state["bridge_calls"] == []})
    bridge = MockBridge()
    panel = PanelController(VersionGate("com.judian.hercomeback.ios", "1.1.108131227", 31, True), bridge, "com.judian.hercomeback.ios", "1.1.110101749", 31)
    state = panel.on_float_button_click()
    cases.append({"name": "old_version_returns_without_native_call", "state": state, "passed": state["status"] == "blocked" and state["error"] == "game_version_mismatch" and state["bridge_calls"] == []})
    bridge = MockBridge()
    panel = PanelController(VersionGate("com.judian.hercomeback.ios", "1.1.110101749", 31, False), bridge, "com.judian.hercomeback.ios", "1.1.110101749", 31)
    state = panel.on_float_button_click()
    cases.append({"name": "unverified_mapping_returns_without_native_call", "state": state, "passed": state["status"] == "blocked" and state["error"] == "native_mapping_not_verified" and state["bridge_calls"] == []})

    for name, gate, expected_error in [
        ("bundle_id_mismatch_returns", VersionGate("wrong.bundle", "1.1.110101749", 31, True), "bundle_id_mismatch"),
        ("metadata_mismatch_returns", VersionGate("com.judian.hercomeback.ios", "1.1.110101749", 30, True), "metadata_version_mismatch"),
    ]:
        bridge = MockBridge()
        panel = PanelController(gate, bridge, "com.judian.hercomeback.ios", "1.1.110101749", 31)
        state = panel.on_float_button_click()
        cases.append({"name": name, "state": state, "passed": state["status"] == "blocked" and state["error"] == expected_error and state["bridge_calls"] == []})

    bridge = MockBridge()
    panel = PanelController(VersionGate("com.judian.hercomeback.ios", "1.1.110101749", 31, True), bridge, "com.judian.hercomeback.ios", "1.1.110101749", 31)
    opened = panel.on_float_button_click()
    closed = panel.on_float_button_click()
    cases.append({"name": "verified_click_toggles_open_close", "state": {"opened": opened, "closed": closed}, "passed": opened["visible"] and closed["status"] == "closed" and closed["bridge_calls"] == []})

    button = Rect(18, 120, 64, 64)
    panel_rect = Rect(96, 112, 260, 180)
    hit_button = passthrough_hit((40, 140), button, panel_rect)
    hit_panel = passthrough_hit((120, 140), button, panel_rect)
    hit_game = passthrough_hit((380, 800), button, panel_rect)
    cases.append({"name": "passthrough_hit_regions", "state": {"button": hit_button, "panel": hit_panel, "outside": hit_game}, "passed": hit_button == "floating_button" and hit_panel == "panel" and hit_game == "underlying_game"})
    return {"passed": all(case["passed"] for case in cases), "cases": cases}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    result = run_cases()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"passed": result["passed"], "cases": len(result["cases"])}, ensure_ascii=False))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
