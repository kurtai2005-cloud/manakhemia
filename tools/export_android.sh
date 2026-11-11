#!/usr/bin/env bash
set -euo pipefail
GODOT="${GODOT:-/home/box/tools/godot/godot}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export JAVA_HOME="${JAVA_HOME:-/home/box/tools/jdk-17.0.21+9}"
export ANDROID_HOME="${ANDROID_HOME:-/home/box/Android/Sdk}"
export PATH="$JAVA_HOME/bin:$ANDROID_HOME/platform-tools:$PATH"
OUT="${OUT:-/workspace/apk/微光小圃-godot-g0.apk}"
mkdir -p "$(dirname "$OUT")"

# editor settings（SDK／JDK 路徑）
CFG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/godot"
mkdir -p "$CFG_DIR"
# 第一次開 editor 產生 settings，再補路徑
"$GODOT" --headless --path "$ROOT" --quit-after 1 >/tmp/godot-settings-boot.log 2>&1 || true
SETTINGS=$(ls -1 "$CFG_DIR"/editor_settings-*.tres 2>/dev/null | tail -1 || true)
echo "editor settings: ${SETTINGS:-none}"
if [[ -n "${SETTINGS}" ]]; then
  python3 - << PY
from pathlib import Path
p = Path("$SETTINGS")
t = p.read_text(encoding="utf-8", errors="replace")
def upsert(text, key, val):
    line = f'{key} = "{val}"'
    import re
    if key in text:
        return re.sub(rf'^{re.escape(key)}\s*=.*$', line, text, flags=re.M)
    # insert near end before last empty
    if "export/android/" in text or True:
        if not text.endswith("\n"):
            text += "\n"
        text += line + "\n"
    return text
t2 = upsert(t, "export/android/java_sdk_path", "$JAVA_HOME")
t2 = upsert(t2, "export/android/android_sdk_path", "$ANDROID_HOME")
if t2 != t:
    p.write_text(t2, encoding="utf-8")
    print("patched", p)
else:
    print("settings unchanged")
PY
fi

# credentials 喺 repo 外：project 目錄嘅 export_credentials.cfg（gitignore）
KS="${G0_DEBUG_KEYSTORE:-/home/box/keep/godot/g0-debug.keystore}"
if [[ ! -f "$KS" ]]; then
  echo "missing keystore $KS" >&2
  exit 1
fi
CREDS="$ROOT/export_credentials.cfg"
cat > "$CREDS" << EOF
[preset.0]

script_encryption_key=""

[preset.0.options]

keystore/debug="$KS"
keystore/debug_user="androiddebugkey"
keystore/debug_password="android"
keystore/release=""
keystore/release_user=""
keystore/release_password=""
EOF
# 保證唔入 git
if git -C "$ROOT" check-ignore -q export_credentials.cfg; then
  echo "credentials gitignored ok"
else
  echo "WARNING: export_credentials.cfg not ignored" >&2
fi

"$GODOT" --headless --path "$ROOT" --import --quit || true
mkdir -p /workspace/apk
# 相對 export_presets 嘅 export_path 係 ../../apk/... 由 project 計
"$GODOT" --headless --path "$ROOT" --export-debug "Android" "$OUT"
ls -la "$OUT"
