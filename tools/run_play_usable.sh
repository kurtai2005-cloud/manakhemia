#!/bin/sh
# Isolated player-input proof. Refuses the player profile and an existing override.cfg.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
GODOT="${GODOT:-/tmp/godot-bin/Godot_v4.7.2-stable_linux.x86_64}"
OUT="${1:-/tmp/vc27_play_usable_out}"
LOG="$OUT/logs"
PROFILE="vc27_play_usable"
case "$OUT" in
*vc27_play_36bfd*) echo "refusing player profile path" >&2; exit 2 ;;
esac
if [ -z "${DISPLAY:-}" ]; then
  echo "no DISPLAY; this proof needs a window" >&2
  exit 2
fi
if [ -e "$ROOT/override.cfg" ]; then
  echo "override.cfg already exists; leaving it untouched" >&2
  exit 2
fi
rm -rf "$OUT"
mkdir -p "$LOG"
cat > "$ROOT/override.cfg" <<EOF
[application]
config/use_custom_user_dir=true
config/custom_user_dir_name="$PROFILE"
EOF
cleanup() {
  rm -f "$ROOT/override.cfg"
  rm -rf "$HOME/.local/share/godot/app_userdata/$PROFILE" "$HOME/.local/share/$PROFILE"
}
trap cleanup EXIT
cd "$ROOT"
set +e
VC27_USABLE_OUT="$OUT" "$GODOT" --path "$ROOT" --rendering-method mobile \
  --script res://tests/hd2d_play_usable.gd \
  > "$LOG/stdout.txt" 2> "$LOG/stderr.txt"
ec=$?
set -e
printf '%s\n' "$ec" > "$LOG/exit_code.txt"
echo "exit=$ec"
exit "$ec"
