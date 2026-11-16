#!/bin/sh
# r4 evidence fixture. Isolated profile. Does not touch the normal save.
# Without a movie path this is the windowed run. A clamped window stays distinct
# and must not be reported as the 1080x2280 movie close.
# With a movie png path, the temporary override also sets stretch mode viewport
# so the movie texture is the 1080x2280 viewport, not a bilinear resize of the
# window. That override is removed when this script exits. project.godot is not changed.
# Software GL on this VM is an engineer check only. It is not Mobile and not a smoothness claim.
# The GPU reviewer omits HD2D_DISPLAY_DRIVER and passes mobile.
# Usage:
#   ./tools/run_walk_clip_trace.sh /path/to/Godot mobile
#   ./tools/run_walk_clip_trace.sh /path/to/Godot mobile /tmp/vc27_walkclip.png
set -eu
GODOT=${1:-godot}
METHOD=${2:-mobile}
MOVIE=${3:-}
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
STRETCH=""
if [ -n "$MOVIE" ]; then
	STRETCH='window/stretch/mode="viewport"'
fi
cat > "$ROOT/override.cfg" << EOF
[display]
window/size/viewport_width=1080
window/size/viewport_height=2280
$STRETCH

[application]
config/use_custom_user_dir=true
config/custom_user_dir_name="$PROFILE"
EOF
echo "profile=$PROFILE"
echo "method=$METHOD"
echo "viewport=1080x2280"
echo "movie=${MOVIE:-none}"
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
MOVIE_ARGS=""
if [ -n "$MOVIE" ]; then
	MOVIE_ARGS="--write-movie $MOVIE"
fi
set +e
# shellcheck disable=SC2086
HD2D_PROFILE_PHASE=walkclip \
HD2D_PROFILE_NAME="$PROFILE" \
HD2D_MODE=low \
"$GODOT" --rendering-method "$METHOD" --display-driver "$DRIVER" $MOVIE_ARGS --path "$ROOT" \
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
