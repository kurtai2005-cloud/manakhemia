#!/usr/bin/env bash
# Engineering copy of the comparison. The Windows evidence entry is
# tools/run_hd2d_mobile_compare.ps1. This file is not that proof.
# Both processes request a real PNG. A missing image fails.
# Does not edit godot_hd2d_v6.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GODOT="${GODOT:-godot}"
OUT="${HD2D_COMPARE_OUT:-$ROOT/../hd2d_mobile_compare}"
STEPS="${HD2D_COMPARE_STEPS:-20}"
HEADLESS=()
if [[ "${HD2D_COMPARE_HEADLESS:-}" == "1" ]]; then
  HEADLESS=(--headless)
fi
python3 "$ROOT/tools/hd2d_evidence.py" fresh-output --out "$OUT"
mkdir -p "$OUT"
PILOT="$OUT/pilot_project"
mkdir -p "$PILOT"
python3 - "$ROOT/godot_hd2d_v6/project.godot" "$PILOT/project.godot" << 'PY'
import sys
from pathlib import Path
text = Path(sys.argv[1]).read_text(encoding="utf-8")
text = text.replace("viewport_width=1080", "viewport_width=1080", 1)
text = text.replace("viewport_height=1920", "viewport_height=2280", 1)
Path(sys.argv[2]).write_text(text, encoding="utf-8")
PY
for dir in art data gameplay scenes shaders textures; do
  cp -a "$ROOT/godot_hd2d_v6/$dir" "$PILOT/$dir"
done
cp "$ROOT/tools/hd2d_pilot_compare_host.gd.txt" "$PILOT/hd2d_pilot_compare_host.gd"
cp "$ROOT/tools/hd2d_pilot_compare_main.gd.txt" "$PILOT/hd2d_pilot_compare_main.gd"
PROFILE="vc27_root_adapter_pilot_$$"
cat > "$PILOT/override.cfg" << EOF
[application]
config/use_custom_user_dir=true
config/custom_user_dir_name="$PROFILE"
EOF
export HD2D_COMPARE_OUT="$OUT"
export HD2D_COMPARE_FIXED=1
export HD2D_COMPARE_FULL=1
export HD2D_COMPARE_STEPS="$STEPS"
export HD2D_COMPARE_GRAB=1
export HD2D_COMPARE_DISPLAY=1
export HD2D_MODE=low
export HD2D_VP=1080x2280
"$GODOT" --headless --path "$PILOT" --import --quit
set +e
"$GODOT" "${HEADLESS[@]}" --path "$PILOT" --rendering-method mobile --script res://hd2d_pilot_compare_main.gd
pilot_rc=$?
ROOT_PROFILE="vc27_root_adapter_root_$$"
ROOT_CFG="$ROOT/override.cfg"
cat > "$ROOT_CFG" << EOF
[application]
config/use_custom_user_dir=true
config/custom_user_dir_name="$ROOT_PROFILE"
EOF
python3 "$ROOT/tools/stage_hd2d_assets.py"
"$GODOT" "${HEADLESS[@]}" --path "$ROOT" --rendering-method mobile --script res://tests/hd2d_same_view.gd
root_rc=$?
rm -f "$ROOT_CFG" "$PILOT/override.cfg"
set -e
echo "pilot_exit=$pilot_rc root_exit=$root_rc"
python3 "$ROOT/tools/hd2d_evidence.py" check --out "$OUT"
status=$?
echo "evidence_exit=$status"
echo "Windows displayed entry is tools/run_hd2d_mobile_compare.ps1. This shell is not that proof."
if [[ "$status" -eq 0 ]]; then
  exit 2
fi
exit "$status"
