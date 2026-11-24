#!/usr/bin/env bash
# Engineering root record only. Not the matched Mobile pair.
# The pair is tools/run_hd2d_mobile_compare.sh and it is not pixel acceptance.
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
export HD2D_COMPARE_FULL="${HD2D_COMPARE_FULL:-0}"
export HD2D_COMPARE_STEPS="${HD2D_COMPARE_STEPS:-1}"
export HD2D_MODE=low
export HD2D_VP=1080x2280
if [[ -z "${HD2D_COMPARE_OUT:-}" ]]; then
  export HD2D_COMPARE_OUT="/tmp/hd2d_compare_engineering"
fi
mkdir -p "$HD2D_COMPARE_OUT"
python3 "$ROOT/tools/stage_hd2d_assets.py"
"$GODOT" --headless --path "$ROOT" --rendering-method gl_compatibility --script res://tests/hd2d_same_view.gd
echo "Engineering GL only. Matched Mobile pair: tools/run_hd2d_mobile_compare.sh"
