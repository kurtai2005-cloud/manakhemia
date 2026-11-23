#!/usr/bin/env bash
# Linux selftest on the current DISPLAY. Not a GPU or phone pass.
# --headless has no viewport image, so this script does not pass --headless.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GODOT="${GODOT:-/tmp/godot-bin/Godot_v4.7.2-stable_linux.x86_64}"
OUT="${CAPTURE_SELFTEST_OUT:-/tmp/vc27_capture_selftest_$$}"
CFG="$ROOT/override.cfg"
if [[ -e "$CFG" ]]; then
  echo "FAIL override.cfg already exists" >&2
  exit 2
fi
rm -rf "$HOME/.local/share/vc27_errand_capture" "$HOME/.local/share/vc27_progress_capture"
mkdir -p "$OUT/errand" "$OUT/progress" "$OUT/logs"
cleanup() { rm -f "$CFG"; }
trap cleanup EXIT
run_stage() {
  local name="$1" profile="$2" stage="$3" dest="$4"
  cat > "$CFG" << EOF
[application]
config/use_custom_user_dir=true
config/custom_user_dir_name="$profile"
EOF
  set +e
  CAPTURE_STAGE="$stage" CAPTURE_OUT="$dest" CAPTURE_PROJECT="$ROOT" CAPTURE_MAX_MS=220000 \
    "$GODOT" --rendering-method mobile --path "$ROOT" \
    --script res://tests/hd2d_capture_harness.gd \
    > "$OUT/logs/${stage}_stdout.txt" 2> "$OUT/logs/${stage}_stderr.txt"
  local ec=$?
  echo "$ec" > "$OUT/logs/${stage}.exit"
  echo "$stage EXIT:$ec"
  return "$ec"
}
if [[ -z "${DISPLAY:-}" ]]; then
  echo "FAIL no DISPLAY. Headless mode saved no viewport image." >&2
  exit 2
fi
echo "selftest out=$OUT"
echo "DISPLAY=$DISPLAY. Not an RTX or phone pass."
run_stage errand vc27_errand_capture errand_out "$OUT/errand"
run_stage errand vc27_errand_capture errand_resume "$OUT/errand"
run_stage progress vc27_progress_capture progress "$OUT/progress"
echo "SELFTEST_DONE $OUT"
