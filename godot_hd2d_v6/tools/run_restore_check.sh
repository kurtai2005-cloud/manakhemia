#!/bin/sh
# Isolated seed then a new verify process. Does not keep a caller's override.cfg.
# Usage: ./tools/run_restore_check.sh /path/to/Godot [rendering-method]
# GPU reviewer: pass mobile. This VM uses gl_compatibility.
set -eu
GODOT=${1:-godot}
METHOD=${2:-mobile}
ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PROFILE=vc27_care_restore_$$
FAKE_NOW=1710000000000
EXPECT="$ROOT/user_restore_expect.json"
LOGDIR=${HD2D_LOG_DIR:-/tmp/vc27_restore_$$}
BACKUP=$(mktemp)
HAD_OVERRIDE=0
mkdir -p "$LOGDIR"
cd "$ROOT"
if [ -f "$ROOT/override.cfg" ]; then
	cp "$ROOT/override.cfg" "$BACKUP"
	HAD_OVERRIDE=1
fi
cleanup() {
	if [ "$HAD_OVERRIDE" -eq 1 ]; then
		cp "$BACKUP" "$ROOT/override.cfg"
	else
		rm -f "$ROOT/override.cfg"
	fi
	rm -f "$BACKUP" "$EXPECT"
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
"$GODOT" --headless --import --path "$ROOT" > "$LOGDIR/import.log" 2>&1
IMPORT=$?
set -e
echo "import_exit=$IMPORT"
if [ "$IMPORT" -ne 0 ]; then
	cat "$LOGDIR/import.log"
	exit "$IMPORT"
fi
DRIVER=${HD2D_DISPLAY_DRIVER:-x11}
run_phase() {
	PHASE=$1
	LOG=$2
	set +e
	HD2D_PROFILE_PHASE=$PHASE \
	HD2D_PROFILE_NAME="$PROFILE" \
	HD2D_FAKE_NOW_MS=$FAKE_NOW \
	HD2D_EXPECT_FILE="$EXPECT" \
	HD2D_MODE=low \
	"$GODOT" --rendering-method "$METHOD" --display-driver "$DRIVER" --path "$ROOT" \
		> "$LOG" 2>&1
	CODE=$?
	set -e
	if [ "$CODE" -eq 0 ] && grep -q '^FAIL ' "$LOG"; then
		echo "FAIL log contains FAIL while exit was 0"
		CODE=1
	fi
	echo "${PHASE}_exit=$CODE"
	return "$CODE"
}
set +e
run_phase seed "$LOGDIR/seed.log"
SEED=$?
set -e
if [ "$SEED" -ne 0 ]; then
	cat "$LOGDIR/seed.log"
	exit "$SEED"
fi
set +e
run_phase verify "$LOGDIR/verify.log"
VERIFY=$?
set -e
echo "logs=$LOGDIR"
cat "$LOGDIR/seed.log"
echo "-----"
cat "$LOGDIR/verify.log"
exit "$VERIFY"
