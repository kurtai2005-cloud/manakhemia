#!/usr/bin/env bash
set -euo pipefail
GODOT="${GODOT:-/home/box/tools/godot/godot}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export DISPLAY="${DISPLAY:-:24}"
echo "== unit tests =="
"$GODOT" --headless --path "$ROOT" res://tests/TestMain.tscn
echo "== smoke =="
"$GODOT" --path "$ROOT" --rendering-driver opengl3 res://tests/SmokeMain.tscn
