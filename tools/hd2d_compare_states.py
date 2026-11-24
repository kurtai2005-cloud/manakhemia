#!/usr/bin/env python3
"""Diff two same-view state records. Does not treat missing pixels as a match."""
from __future__ import annotations

import json
import sys
from pathlib import Path

KEYS = (
    "viewport_actual",
    "aspect",
    "mode",
    "steps",
    "fixed_dt",
    "follow_camera_steps",
    "tick_camera_called",
    "tick_play_called",
    "care_present",
    "camera_overwritten_each_step",
    "camera_origin",
    "camera_basis",
    "camera_fov",
    "camera_keep_aspect",
    "visual_global",
    "visual_offset_y",
    "visual_pixel_size",
    "cloud_t",
    "pet_lag",
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def near(a, b, tol: float = 0.02) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) <= tol
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return all(near(x, y, tol) for x, y in zip(a, b))
    return a == b


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: hd2d_compare_states.py pilot.json root.json")
    pilot = load(Path(sys.argv[1]))
    root = load(Path(sys.argv[2]))
    failed = False
    for key in KEYS:
        if not near(pilot.get(key), root.get(key)):
            failed = True
            print(f"DELTA {key}\n  pilot={pilot.get(key)}\n  root={root.get(key)}")
    if pilot.get("viewport_actual") != [1080, 2280] or root.get("viewport_actual") != [1080, 2280]:
        failed = True
        print("DELTA viewport is not 1080x2280")
    if not pilot.get("follow_camera_steps") or not root.get("follow_camera_steps"):
        failed = True
        print("DELTA follow_camera did not run on both sides")
    if pilot.get("care_present") or root.get("care_present"):
        failed = True
        print("DELTA pilot care node is present")
    pixel = "not compared"
    if pilot.get("renderer_actual") != "mobile" or root.get("renderer_actual") != "mobile":
        pixel = "not mobile, no pixel claim"
        failed = True
        print("DELTA renderer_actual is not mobile on both sides")
    print("pixel:", pixel)
    if failed:
        print("same_view: NOT matched")
        raise SystemExit(1)
    print("same_view: state matched, pixels not claimed")


if __name__ == "__main__":
    main()
