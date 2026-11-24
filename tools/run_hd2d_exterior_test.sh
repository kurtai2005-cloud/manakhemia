#!/usr/bin/env bash
# Isolated user dir. Stages copies, then checks the exterior host.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GODOT="${GODOT:-/tmp/godot-bin/Godot_v4.7.2-stable_linux.x86_64}"
PROFILE="${HD2D_PROFILE_NAME:-vc27_root_adapter_$$}"
CFG="$ROOT/override.cfg"
cleanup() { rm -f "$CFG"; }
trap cleanup EXIT
cat > "$CFG" << EOF
[application]
config/use_custom_user_dir=true
config/custom_user_dir_name="$PROFILE"
EOF
if command -v python3 >/dev/null 2>&1; then
  python3 "$ROOT/tools/stage_hd2d_assets.py"
elif command -v py >/dev/null 2>&1; then
  py -3 "$ROOT/tools/stage_hd2d_assets.py"
else
  echo "run_hd2d_exterior_test: python3 is required" >&2
  exit 1
fi
CLOUD="$ROOT/hd2d_stage/textures/tiles/cloud_shadow.png.import"
NEED_IMPORT=0
if [[ ! -f "$ROOT/.godot/global_script_class_cache.cfg" || ! -f "$CLOUD" ]]; then
  NEED_IMPORT=1
fi
if [[ "$NEED_IMPORT" == "0" ]]; then
  CTEX="$(awk -F'"' '/^path=/{print $2; exit}' "$CLOUD")"
  CTEX="${CTEX#res://}"
  if [[ ! -f "$ROOT/$CTEX" ]]; then
    NEED_IMPORT=1
  fi
fi
if [[ "$NEED_IMPORT" == "1" ]]; then
  "$GODOT" --headless --path "$ROOT" --import --quit
fi
"$GODOT" --headless --path "$ROOT" --script res://tests/hd2d_exterior_test.gd
