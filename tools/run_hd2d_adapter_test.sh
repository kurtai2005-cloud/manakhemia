#!/usr/bin/env bash
# Isolated user dir. Does not export an APK and does not use the default save.
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
if [[ ! -f "$ROOT/.godot/global_script_class_cache.cfg" ]]; then
  "$GODOT" --headless --path "$ROOT" --import --quit
fi
"$GODOT" --headless --path "$ROOT" --script res://tests/hd2d_adapter_test.gd
