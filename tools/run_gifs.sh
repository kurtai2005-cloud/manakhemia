#!/usr/bin/env bash
# M1c.1 玩法預覽 GIF（預設只出 hunt enter+BGM）；GODOT_GIF_FEATS 可覆寫
set -euo pipefail
GODOT="${GODOT:-/home/box/tools/godot/godot}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${GODOT_GIF_DIR:-/home/box/keep/godot/M1c1}"
export DISPLAY="${DISPLAY:-:24}"
export GODOT_M1A_DEMO=1
export GODOT_M1B_DEMO=1
export GODOT_M1C_DEMO=1
export GODOT_M1C1_DEMO=1
mkdir -p "$OUT"
feats=(${GODOT_GIF_FEATS:-hunt})
for feat in "${feats[@]}"; do
  FRAMES="/tmp/m1c1-gif-${feat}"
  mkdir -p "$FRAMES"
  rm -f "$FRAMES"/*.png
  echo "== gif $feat =="
  GODOT_M1C1_GIF="$feat" GODOT_M1C1_FRAME_DIR="$FRAMES" GODOT_M1C_GIF="$feat" GODOT_M1C_FRAME_DIR="$FRAMES" GODOT_M1A_GIF="$feat" GODOT_M1A_FRAME_DIR="$FRAMES" \
    "$GODOT" --path "$ROOT" --rendering-driver opengl3 --fixed-fps 15 \
    res://tests/GifMain.tscn
  n=$(ls -1 "$FRAMES"/*.png 2>/dev/null | wc -l)
  echo "  frames=$n"
  if [[ "$n" -lt 8 ]]; then
    echo "  FAIL too few frames for $feat" >&2
    exit 1
  fi
  pal="/tmp/m1c1-pal-${feat}.png"
  dest="$OUT/m1c1-${feat}.gif"
  ffmpeg -y -hide_banner -loglevel error -framerate 15 -pattern_type glob -i "$FRAMES/${feat}_*.png" \
    -vf "scale=360:-1:flags=neighbor,palettegen=max_colors=64:stats_mode=diff" "$pal"
  ffmpeg -y -hide_banner -loglevel error -framerate 15 -pattern_type glob -i "$FRAMES/${feat}_*.png" -i "$pal" \
    -lavfi "scale=360:-1:flags=neighbor[x];[x][1:v]paletteuse=dither=none" -loop 0 "$dest"
  python3 - "$dest" << 'PY'
import sys
from pathlib import Path
p=Path(sys.argv[1])
kb=p.stat().st_size/1024
print(f"  {p} {kb:.1f} KB")
if p.stat().st_size>5*1024*1024:
    print("  FAIL gif >5MB", file=sys.stderr)
    sys.exit(1)
PY
done
echo "== gifs in $OUT =="
ls -la "$OUT"
