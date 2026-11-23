#!/bin/sh
# Isolated draft smoke. Two Godot processes, one fresh profile. Not the player profile.
set -e
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
GODOT="${GODOT:-/tmp/godot-bin/Godot_v4.7.2-stable_linux.x86_64}"
OUT="${VC27_DRAFT_OUT:-/tmp/vc27_draft_loop_out}"
USER_NAME="vc27_draft_loop"
USER_DIR="$HOME/.local/share/$USER_NAME"
rm -rf "$OUT" "$USER_DIR"
mkdir -p "$OUT"
if [ -e "$ROOT/override.cfg" ]; then
	echo "override.cfg already present, stop"
	exit 2
fi
cat > "$ROOT/override.cfg" <<EOF
[application]
config/use_custom_user_dir=true
config/custom_user_dir_name="$USER_NAME"
EOF
cleanup() {
	rm -f "$ROOT/override.cfg"
	rm -rf "$USER_DIR"
}
trap cleanup EXIT
set +e
"$GODOT" --headless --path "$ROOT" --script res://tests/hd2d_draft_loop.gd > "$OUT/phase1.txt" 2> "$OUT/phase1.err"
echo $? > "$OUT/phase1.exit"
set -e
if [ "$(cat "$OUT/phase1.exit")" != "0" ]; then
	echo "phase1=$(cat "$OUT/phase1.exit") phase2=skipped"
	exit 1
fi
set +e
VC27_DRAFT_PHASE=2 "$GODOT" --headless --path "$ROOT" --script res://tests/hd2d_draft_loop.gd > "$OUT/phase2.txt" 2> "$OUT/phase2.err"
echo $? > "$OUT/phase2.exit"
set -e
if [ -f "$USER_DIR/save_v1.json" ]; then
	cp "$USER_DIR/save_v1.json" "$OUT/save_v1.json"
fi
echo "phase1=$(cat "$OUT/phase1.exit") phase2=$(cat "$OUT/phase2.exit")"
test "$(cat "$OUT/phase1.exit")" = "0"
test "$(cat "$OUT/phase2.exit")" = "0"
