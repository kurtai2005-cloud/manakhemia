#!/usr/bin/env bash
# Capture v2 shots via Xvfb + llvmpipe. Do NOT use --headless for screenshots.
set -euo pipefail
ROOT="/workspace/game-design/detail_pilot/godot_hd2d_v6"
GODOT="${GODOT:-/home/box/tools/godot/godot}"
export LIBGL_ALWAYS_SOFTWARE=1
export GALLIUM_DRIVER=llvmpipe
export MESA_GL_VERSION_OVERRIDE=3.3
export MESA_GLSL_VERSION_OVERRIDE=330
export HD2D_CAPTURE=1

XVFB=(xvfb-run -a -s "-screen 0 1080x1920x24")
COMMON=("$GODOT" --display-driver x11 --rendering-driver opengl3
        --rendering-method gl_compatibility --audio-driver Dummy --path "$ROOT")

echo "=== import ==="
"$GODOT" --headless --import --path "$ROOT" --audio-driver Dummy --quit || true

for mode in high low night; do
  echo "=== capture $mode ==="
  HD2D_CAPTURE=1 HD2D_MODE="$mode" "${XVFB[@]}" "${COMMON[@]}" --resolution 1080x1920 --quit-after 400
  ls -la "$ROOT/GODOT_${mode^^}.png" || echo "MISSING $mode"
done
ls -la "$ROOT/GODOT_COTTAGE_CROP.png" || true
