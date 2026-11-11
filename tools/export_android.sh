#!/usr/bin/env bash
# M1b：gradle 出包，注入 PetOverlayService，簽同一把 G0 debug keystore（唔入 git），v2+v3。
set -euo pipefail
GODOT="${GODOT:-/home/box/tools/godot/godot}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export JAVA_HOME="${JAVA_HOME:-/home/box/tools/jdk-17.0.21+9}"
export ANDROID_HOME="${ANDROID_HOME:-/home/box/Android/Sdk}"
export PATH="$JAVA_HOME/bin:$ANDROID_HOME/platform-tools:$PATH"
OUT="${OUT:-/workspace/apk/微光小圃-godot-m1d.apk}"
mkdir -p "$(dirname "$OUT")"

CFG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/godot"
mkdir -p "$CFG_DIR"
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

KS="${G0_DEBUG_KEYSTORE:-/home/box/keep/godot/keys/g0-debug.keystore}"
if [[ ! -f "$KS" ]]; then
  KS="/home/box/keep/godot/g0-debug.keystore"
fi
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
if git -C "$ROOT" check-ignore -q export_credentials.cfg; then
  echo "credentials gitignored ok"
else
  echo "WARNING: export_credentials.cfg not ignored" >&2
fi

# 安裝／補齊 android/build 模板（直接 unzip 官方 template；godot --install-android-build-template 無頭會卡住）
TEMPLATE_ZIP="${GODOT_ANDROID_SOURCE:-$HOME/.local/share/godot/export_templates/4.7.2.stable/android_source.zip}"
if [[ ! -f "$ROOT/android/build/build.gradle" ]]; then
  echo "== unzip android build template =="
  mkdir -p "$ROOT/android/build"
  unzip -qo "$TEMPLATE_ZIP" -d "$ROOT/android/build"
fi
if [[ ! -f "$ROOT/android/build/build.gradle" ]]; then
  echo "missing android template $TEMPLATE_ZIP" >&2
  exit 2
fi
# Godot 4.7 gradle export 讀 android/.build_version（build 目錄嘅上一層）
VER_FILE="$ROOT/android/.build_version"
if [[ ! -f "$VER_FILE" ]]; then
  echo -e "4.7.2.stable\ned1daf0bf001b61586d9930840f2f1394092c079" > "$VER_FILE"
  echo "wrote $VER_FILE"
fi
cp -f "$VER_FILE" "$ROOT/android/build/.build_version" || true

python3 "$ROOT/tools/inject_android_overlay.py" "$ROOT" "$ROOT/android/build"

"$GODOT" --headless --path "$ROOT" --import --quit || true
mkdir -p /workspace/apk
# 出包前再注入一次，避免 export 重寫模板之後冇 service
# Godot export 可能喺開始時覆寫 android/build；先 export 失敗就再注入＋gradle。
set +e
"$GODOT" --headless --path "$ROOT" --export-debug "Android" "$OUT" >/tmp/godot-m1b-export.log 2>&1
EX=$?
set -e
# 若 manifest 被覆寫，再注入並用 gradle 組 APK
python3 "$ROOT/tools/inject_android_overlay.py" "$ROOT" "$ROOT/android/build"
if ! rg -q "PetOverlayService" "$ROOT/android/build/src/main/AndroidManifest.xml"; then
  echo "inject failed to keep PetOverlayService" >&2
  exit 2
fi
if [[ ! -f "$OUT" || "$EX" -ne 0 ]]; then
  echo "godot export exit=$EX, try gradle assemble"
  tail -40 /tmp/godot-m1b-export.log
  # 再跑一次 export（manifest 已注入）
  set +e
  "$GODOT" --headless --path "$ROOT" --export-debug "Android" "$OUT" >>/tmp/godot-m1b-export.log 2>&1
  EX=$?
  set -e
fi
# 最後一次注入之後一定要再 gradle，先至會將 GLES required=false / overlay 打入最終 APK。
# Godot --export-debug 會寫 src/debug manifest（glEs required=true）再組包；只靠 export 出品會漏 P1-4。
KS="${DEBUG_KEYSTORE:-${G0_DEBUG_KEYSTORE:-/home/box/keep/godot/keys/g0-debug.keystore}}"
if [[ ! -f "$KS" ]]; then
  KS="/home/box/keep/godot/g0-debug.keystore"
fi
GRADLEW="$ROOT/android/build/gradlew"
if [[ -x "$GRADLEW" ]]; then
  echo "gradle assemble after final inject (package/version/abi + GLES patch)"
  (cd "$ROOT/android/build" && ./gradlew assembleStandardDebug --stacktrace \
    -Pexport_package_name=hk.vizard.glimmer.fpet.godot \
    -Pexport_version_code=${EXPORT_VERSION_CODE:-9} \
    -Pexport_version_name=${EXPORT_VERSION_NAME:-2.0.0-m1d} \
    -Pexport_enabled_abis=arm64-v8a \
    -Pexport_path=/workspace/apk \
    -Pexport_filename=${EXPORT_FILENAME:-微光小圃-godot-m1d.apk} \
    -Pperform_zipalign=true \
    -Pperform_signing=true \
    -Pdebug_keystore_file="$KS" \
    -Pdebug_keystore_password=android \
    -Pdebug_keystore_alias=androiddebugkey
  ) | tee /tmp/godot-m1a-gradle.log
  APK=$(find "$ROOT/android/build/build/outputs/apk" -name '*.apk' | head -1)
  if [[ -n "$APK" ]]; then
    cp -f "$APK" "$OUT"
  fi
fi
if [[ ! -f "$OUT" ]]; then
  echo "APK missing $OUT" >&2
  tail -50 /tmp/godot-m1b-export.log
  exit 3
fi
ls -la "$OUT"
# 用同一把 G0 debug key 重簽 v2+v3（等 Kurt 可以覆蓋安裝 M1a）
APKS="${ANDROID_HOME}/build-tools/36.1.0/apksigner"
if [[ ! -x "$APKS" ]]; then
  APKS="${ANDROID_HOME}/build-tools/34.0.0/apksigner"
fi
if [[ -x "$APKS" && -f "$KS" ]]; then
  TMPAPK="${OUT}.signed.apk"
  "$APKS" sign --ks "$KS" --ks-pass pass:android --ks-key-alias androiddebugkey --key-pass pass:android     --v1-signing-enabled true --v2-signing-enabled true --v3-signing-enabled true     --out "$TMPAPK" "$OUT"
  mv -f "$TMPAPK" "$OUT"
  "$APKS" verify --print-certs "$OUT" | tee /tmp/godot-m1b-apksigner.log
fi
# 保險：若 APK 冇 service，唔過
AAPT="${ANDROID_HOME}/build-tools/34.0.0/aapt2"
if [[ -x "$AAPT" ]]; then
  "$AAPT" dump xmltree --file AndroidManifest.xml "$OUT" | rg -n "PetOverlayService|androidx-startup|SYSTEM_ALERT_WINDOW|glEsVersion|CAMERA" || true
fi
