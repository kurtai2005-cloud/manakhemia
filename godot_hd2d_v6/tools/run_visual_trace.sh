#!/bin/sh
# Formal visual trace in its own isolated profile. Does not run verify and does not reset a save.
# Game time is about 17s. One process, phase=visual. Software GL here passes gl_compatibility;
# a GPU reviewer passes mobile and does not set HD2D_DISPLAY_DRIVER.
# Wake semantics are not changed: a pointer restores a faded panel; KEY_N only toggles night
# and does not clear appreciate. Night is the last input, after a >=2s appreciate hold with no input.
# Usage: ./tools/run_visual_trace.sh /path/to/Godot [rendering-method]
set -eu
GODOT=${1:-godot}
METHOD=${2:-mobile}
ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PROFILE=vc27_care_visual_$$
LOGDIR=${HD2D_LOG_DIR:-/tmp/vc27_visual_$$}
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
	rm -f "$BACKUP"
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
set +e
HD2D_PROFILE_PHASE=visual \
HD2D_PROFILE_NAME="$PROFILE" \
HD2D_MODE=low \
"$GODOT" --rendering-method "$METHOD" --display-driver "$DRIVER" --path "$ROOT" \
	> "$LOGDIR/visual.log" 2>&1
CODE=$?
set -e
if [ "$CODE" -eq 0 ] && grep -q '^FAIL ' "$LOGDIR/visual.log"; then
	CODE=1
fi
echo "visual_exit=$CODE"
echo "logs=$LOGDIR"
cat "$LOGDIR/visual.log"
exit "$CODE"
