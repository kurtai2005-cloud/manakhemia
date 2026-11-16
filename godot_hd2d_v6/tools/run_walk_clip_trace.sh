#!/bin/sh
# r4 walk candidate, Low 19:9. Isolated profile. Does not touch the normal save.
# Software GL on this VM is an engineer check only. It is not Mobile and not a smoothness claim.
# The GPU reviewer omits HD2D_DISPLAY_DRIVER and passes mobile.
# Usage: ./tools/run_walk_clip_trace.sh /path/to/Godot [rendering-method]
set -eu
GODOT=${1:-godot}
METHOD=${2:-mobile}
ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PROFILE=vc27_walkclip_$$
LOGDIR=${HD2D_LOG_DIR:-/tmp/vc27_walkclip_$$}
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
window/size/viewport_width=1080
window/size/viewport_height=2280

[application]
config/use_custom_user_dir=true
config/custom_user_dir_name="$PROFILE"
EOF
echo "profile=$PROFILE"
echo "method=$METHOD"
echo "viewport=1080x2280"
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
HD2D_PROFILE_PHASE=walkclip \
HD2D_PROFILE_NAME="$PROFILE" \
HD2D_MODE=low \
"$GODOT" --rendering-method "$METHOD" --display-driver "$DRIVER" --path "$ROOT" \
	> "$LOGDIR/walkclip.log" 2>&1
CODE=$?
set -e
if [ "$CODE" -eq 0 ] && grep -q '^FAIL ' "$LOGDIR/walkclip.log"; then
	CODE=1
fi
echo "walkclip_exit=$CODE"
echo "logs=$LOGDIR"
cat "$LOGDIR/walkclip.log"
exit "$CODE"
