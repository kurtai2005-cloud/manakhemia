#!/bin/sh
# Two Godot processes, isolated user dir, 540x1140 override.
# Usage: ./tools/run_restore_check.sh /path/to/Godot [rendering-method]
# Reviewer GPU: pass "mobile". This VM's software GL run uses gl_compatibility.
set -eu
GODOT=${1:-godot}
METHOD=${2:-mobile}
ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PROFILE=vc27_care_restore_$$
FAKE_NOW=1710000000000
EXPECT="$ROOT/user_restore_expect.json"
LOGDIR=${HD2D_LOG_DIR:-/tmp/vc27_restore_$$}
mkdir -p "$LOGDIR"
cd "$ROOT"
cleanup() {
	rm -f "$ROOT/override.cfg" "$EXPECT"
}
trap cleanup EXIT
cat > "$ROOT/override.cfg" << EOF
[display]
window/size/viewport_width=540
window/size/viewport_height=1140

[application]
config/use_custom_user_dir=true
config/custom_user_dir_name="$PROFILE"
EOF
echo "profile=$PROFILE"
echo "project=$ROOT"
echo "method=$METHOD"
set +e
HD2D_PROFILE_PHASE=seed \
HD2D_PROFILE_NAME="$PROFILE" \
HD2D_FAKE_NOW_MS=$FAKE_NOW \
HD2D_EXPECT_FILE="$EXPECT" \
HD2D_MODE=low \
"$GODOT" --rendering-method "$METHOD" --display-driver x11 --path "$ROOT" \
	> "$LOGDIR/seed.log" 2>&1
SEED=$?
set -e
echo "seed_exit=$SEED"
if [ "$SEED" -ne 0 ]; then
	cat "$LOGDIR/seed.log"
	exit "$SEED"
fi
set +e
HD2D_PROFILE_PHASE=verify \
HD2D_PROFILE_NAME="$PROFILE" \
HD2D_FAKE_NOW_MS=$FAKE_NOW \
HD2D_EXPECT_FILE="$EXPECT" \
HD2D_MODE=low \
"$GODOT" --rendering-method "$METHOD" --display-driver x11 --path "$ROOT" \
	> "$LOGDIR/verify.log" 2>&1
VERIFY=$?
set -e
echo "verify_exit=$VERIFY"
echo "logs=$LOGDIR"
cat "$LOGDIR/seed.log"
echo "-----"
cat "$LOGDIR/verify.log"
exit "$VERIFY"
