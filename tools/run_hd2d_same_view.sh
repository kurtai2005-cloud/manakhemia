#!/usr/bin/env bash
# Root side of the same-view pair. Does not write the default save.
# Set HD2D_COMPARE_OUT to an empty directory. Software GL is not acceptance.
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
export HD2D_COMPARE_FIXED=1
export HD2D_MODE="${HD2D_MODE:-low}"
export HD2D_VP="${HD2D_VP:-1080x1920}"
if [[ -z "${HD2D_COMPARE_OUT:-}" ]]; then
  export HD2D_COMPARE_OUT="$ROOT/../hd2d_compare_out"
fi
python3 "$ROOT/tools/stage_hd2d_assets.py"
"$GODOT" --headless --path "$ROOT" --rendering-method gl_compatibility --script res://tests/hd2d_same_view.gd
echo "Pilot reference, separate process, do not use the default HD2D_OUT path:"
echo "HD2D_MODE=low HD2D_VP=1080x1920 HD2D_OUT=<empty-dir> $GODOT --headless --path \"$ROOT/godot_hd2d_v6\" --rendering-method gl_compatibility"
