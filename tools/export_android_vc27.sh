#!/usr/bin/env bash
# Internal VC27 test APK. Separate package id and a newly generated debug key.
# Does not read the G0 keystore and does not replace hk.vizard.glimmer.fpet.godot.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GODOT="${GODOT:-/tmp/godot-bin/Godot_v4.7.2-stable_linux.x86_64}"
export JAVA_HOME="${JAVA_HOME:-$(dirname "$(dirname "$(readlink -f "$(command -v java)")")")}"
export ANDROID_HOME="${ANDROID_HOME:-/tmp/android-sdk}"
export PATH="$JAVA_HOME/bin:$ANDROID_HOME/platform-tools:$PATH"
FINAL="${FINAL:-/opt/cursor/artifacts/vc27-draft-11fb9c14-r11.apk}"
OUT="${OUT:-/tmp/vc27-apk/vc27-draft-11fb9c14-r11.apk}"
PKG="hk.vizard.glimmer.fpet.vc27draft"
VER_CODE=21
VER_NAME="vc27-11fb9c14-r11"
KS="${VC27_DEBUG_KEYSTORE:-/tmp/vc27-apk/vc27-debug.keystore}"
mkdir -p "$(dirname "$OUT")" "$(dirname "$KS")" /tmp/vc27-apk

if [[ -e "$ROOT/override.cfg" ]]; then
  echo "override.cfg exists, stop" >&2
  exit 2
fi
if [[ ! -x "$GODOT" ]]; then
  echo "missing godot $GODOT" >&2
  exit 2
fi

if [[ ! -f "$KS" ]]; then
  keytool -genkeypair -v \
    -keystore "$KS" \
    -storepass android \
    -keypass android \
    -alias androiddebugkey \
    -keyalg RSA -keysize 2048 -validity 10000 \
    -dname "CN=VC27 Debug, OU=VC27, O=VC27, L=HK, ST=HK, C=HK"
fi

CFG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/godot"
mkdir -p "$CFG_DIR"
"$GODOT" --headless --path "$ROOT" --quit-after 1 >/tmp/vc27-godot-boot.log 2>&1 || true
SETTINGS=$(ls -1 "$CFG_DIR"/editor_settings-*.tres 2>/dev/null | tail -1 || true)
if [[ -n "${SETTINGS}" ]]; then
  python3 - "$SETTINGS" "$JAVA_HOME" "$ANDROID_HOME" << 'PY'
import re, sys
from pathlib import Path
p, java_home, sdk = sys.argv[1:]
text = Path(p).read_text(encoding="utf-8", errors="replace")
def upsert(src, key, val):
    line = f'{key} = "{val}"'
    if key in src:
        return re.sub(rf'^{re.escape(key)}\s*=.*$', line, src, flags=re.M)
    if not src.endswith("\n"):
        src += "\n"
    return src + line + "\n"
text = upsert(text, "export/android/java_sdk_path", java_home)
text = upsert(text, "export/android/android_sdk_path", sdk)
Path(p).write_text(text, encoding="utf-8")
print("settings", p)
PY
fi

CREDS="$ROOT/export_credentials.cfg"
cleanup() {
  rm -f "$CREDS"
}
trap cleanup EXIT
cat > "$CREDS" << EOF
[preset.1]

script_encryption_key=""

[preset.1.options]

keystore/debug="$KS"
keystore/debug_user="androiddebugkey"
keystore/debug_password="android"
keystore/release=""
keystore/release_user=""
keystore/release_password=""
EOF

TEMPLATE_ZIP="$HOME/.local/share/godot/export_templates/4.7.2.stable/android_source.zip"
if [[ ! -f "$ROOT/android/build/build.gradle" ]]; then
  mkdir -p "$ROOT/android/build"
  unzip -qo "$TEMPLATE_ZIP" -d "$ROOT/android/build"
fi
printf '4.7.2.stable\ned1daf0bf001b61586d9930840f2f1394092c079\n' > "$ROOT/android/.build_version"
cp -f "$ROOT/android/.build_version" "$ROOT/android/build/.build_version"
printf 'sdk.dir=%s\n' "$ANDROID_HOME" > "$ROOT/android/build/local.properties"

echo "== godot export-debug Android VC27 =="
set +e
"$GODOT" --headless --path "$ROOT" --export-debug "Android VC27" "$OUT" >/tmp/vc27-godot-export.log 2>&1
EX=$?
set -e
echo "godot export exit=$EX"
tail -30 /tmp/vc27-godot-export.log || true

# Godot omits rendering_method.mobile when it equals the engine default.
# The phone build still has to carry the explicit mobile value.
python3 - "$ROOT/android/build" << 'PY'
import struct, sys
from pathlib import Path
root = Path(sys.argv[1])
files = list(root.rglob("project.binary"))
if not files:
    raise SystemExit("project.binary missing")
key = b"rendering/renderer/rendering_method.mobile"
for path in files:
    data = bytearray(path.read_bytes())
    if key in data:
        print("renderer key already in", path)
        continue
    count = struct.unpack_from("<I", data, 4)[0]
    struct.pack_into("<I", data, 4, count + 1)
    text = b"mobile"
    variant = struct.pack("<II", 4, len(text)) + text + b"\x00\x00"
    data += struct.pack("<I", len(key)) + key + struct.pack("<I", len(variant)) + variant
    path.write_bytes(data)
    print("patched", path, "count", count + 1)
PY
# The index is written before this patch. Refresh every recorded size and md5
# from the asset files Gradle will pack, before zipalign and signing.
python3 "$ROOT/tools/check_vc27_sparsepck.py" sync "$ROOT/android/build/src/main/assets"

cp -f "$ROOT/tools/android_vc27/Vc27PreviewApp.java" "$ROOT/android/build/src/main/java/com/godot/game/Vc27PreviewApp.java"
cp -f "$ROOT/tools/android_vc27/Vc27PreviewLaunch.java" "$ROOT/android/build/src/main/java/com/godot/game/Vc27PreviewLaunch.java"
python3 "$ROOT/tools/android_vc27/patch_manifest.py" "$ROOT/android/build"
python3 - "$ROOT/android/build/res" << 'PY'
import sys
from pathlib import Path
root = Path(sys.argv[1])
for path in root.rglob("godot_project_name_string.xml"):
    text = path.read_text(encoding="utf-8")
    if "微光小圃" in text:
        path.write_text(text.replace("微光小圃", "微光試稿"), encoding="utf-8")
        print("renamed", path)
PY

echo "== gradle assembleStandardDebug =="
(cd "$ROOT/android/build" && ./gradlew assembleStandardDebug --stacktrace --max-workers 2 \
  -Pexport_package_name="$PKG" \
  -Pexport_version_code="$VER_CODE" \
  -Pexport_version_name="$VER_NAME" \
  -Pexport_enabled_abis=arm64-v8a \
  -Pexport_path="$(dirname "$OUT")" \
  -Pexport_filename="$(basename "$OUT")" \
  -Pexport_build_type=debug \
  -Pexport_edition=standard \
  -Pexport_format=apk \
  -Pperform_zipalign=true \
  -Pperform_signing=true \
  -Pdebug_keystore_file="$KS" \
  -Pdebug_keystore_password=android \
  -Pdebug_keystore_alias=androiddebugkey
) | tee /tmp/vc27-gradle.log

APK=$(find "$ROOT/android/build/build/outputs/apk" -name '*.apk' | head -1)
if [[ -z "$APK" ]]; then
  echo "gradle apk missing" >&2
  exit 3
fi
cp -f "$APK" "$OUT"
mkdir -p "$(dirname "$FINAL")"
cp -f "$OUT" "$FINAL"
python3 "$ROOT/tools/check_vc27_sparsepck.py" verify "$FINAL"
ls -lh "$OUT" "$FINAL"
echo "VC27_EXPORT_OK exit=$EX apk=$FINAL"
