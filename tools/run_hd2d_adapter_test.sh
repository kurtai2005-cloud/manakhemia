#!/usr/bin/env bash
# Isolated user dir. Does not export an APK and does not use the default save.
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
  echo "run_hd2d_adapter_test: python3 is required to copy the 675 stage" >&2
  exit 1
fi
STAGE_TEX="$ROOT/hd2d_stage/pet/r4/pet_tuanrong_radiant_side_idle_01.png.import"
STAGE_CTEX=""
if [[ -f "$STAGE_TEX" ]]; then
  STAGE_CTEX="$(awk -F'"' '/^path=/{print $2; exit}' "$STAGE_TEX")"
  STAGE_CTEX="${STAGE_CTEX#res://}"
fi
if [[ ! -f "$ROOT/.godot/global_script_class_cache.cfg" || ! -f "$STAGE_TEX" || -z "$STAGE_CTEX" || ! -f "$ROOT/$STAGE_CTEX" ]]; then
  "$GODOT" --headless --path "$ROOT" --import --quit
fi
"$GODOT" --headless --path "$ROOT" --script res://tests/hd2d_adapter_test.gd
