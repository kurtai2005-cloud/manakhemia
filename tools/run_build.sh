#!/usr/bin/env bash
# 每次出包／提交前：headless 單元測試 + 低／中畫質截圖。
# 本地唔需要跑 GUT（遊測會喺公開 repo 用 GitHub Actions 跑 GUT）。
set -euo pipefail
GODOT="${GODOT:-/home/box/tools/godot/godot}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VER="${GODOT_SHOT_VER:-G0.1}"
SHOT="${GODOT_SHOT_DIR:-/home/box/keep/godot/${VER}}"
export DISPLAY="${DISPLAY:-:24}"
export GODOT_SHOT_DIR="$SHOT"
mkdir -p "$SHOT"

echo "== unit tests =="
"$GODOT" --headless --path "$ROOT" res://tests/TestMain.tscn

echo "== smoke (low + mid screenshots → $SHOT) =="
"$GODOT" --path "$ROOT" --rendering-driver opengl3 res://tests/SmokeMain.tscn

python3 - "$SHOT" << 'PY'
import sys
from pathlib import Path
from PIL import Image
d = Path(sys.argv[1])
needed = ["g01-day.png", "g01-night.png", "g01-mid-day.png", "g01-mid-night.png",
          "g01-day-front-tree.png", "g01-day-behind-tree.png",
          "g01-day-front-cottage.png", "g01-day-behind-cottage.png",
          "g01-w412-day.png", "g01-w412-night.png", "g01-w412-mid-day.png",
          "g01-w768-day.png", "g01-w768-night.png", "g01-w768-mid-day.png"]
fail = 0
BEIGE = (0xFF, 0xE8, 0xC8)
for name in needed:
    p = d / name
    if not p.exists():
        print(f"MISSING {p}")
        fail += 1
        continue
    im = Image.open(p)
    w, h = im.size
    print(f"OK file {name} {w}x{h} {p.stat().st_size} bytes")
    # 地面：畫面下 1/4 中間應該係綠草，唔可以成幅 #ffe8c8
    mid_bot = im.getpixel((w//2, int(h*0.88)))[:3]
    top = im.getpixel((w//2, 12))[:3]
    def near(a,b,tol=8):
        return all(abs(a[i]-b[i])<=tol for i in range(3))
    greenish = mid_bot[1] > mid_bot[0] + 5 and mid_bot[1] > 60
    if not greenish:
        print(f"  FAIL {name}: bottom mid {mid_bot} is not grass green")
        fail += 1
    else:
        print(f"  grass mid-bottom {mid_bot}")
    if near(top, BEIGE) and "night" not in name:
        print(f"  WARN {name}: top is fog beige {top} (sky card may not be drawing)")
    else:
        print(f"  sky/top {top}")
    # 低／中都要係完整 3D（唔可以空洞或純色）
    if p.stat().st_size < 20000:
        print(f"  FAIL {name}: file too small, likely empty clear-color")
        fail += 1
sys.exit(fail)
PY

echo "== run_build OK  shots in $SHOT =="
