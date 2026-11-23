#!/usr/bin/env python3
"""Add the preview launcher to a Godot Android manifest. Does not change the normal activity."""
import sys
from pathlib import Path

LAUNCH = """
        <activity
            android:name=".Vc27PreviewApp"
            android:process=":vc27preview"
            android:exported="false"
            android:theme="@style/GodotAppSplashTheme"
            android:launchMode="singleInstancePerTask"
            android:excludeFromRecents="false"
            android:screenOrientation="portrait"
            android:windowSoftInputMode="adjustResize"
            android:configChanges="layoutDirection|locale|orientation|keyboardHidden|screenSize|smallestScreenSize|density|keyboard|navigation|screenLayout|uiMode"
            android:resizeableActivity="false" />
        <activity
            android:name=".Vc27PreviewLaunch"
            android:exported="true"
            android:label="微光試稿·試玩"
            android:excludeFromRecents="true"
            android:theme="@android:style/Theme.NoDisplay">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
"""

def _label_launcher(text: str) -> str:
    if 'android:name=".GodotAppLauncher"' not in text:
        return text
    if 'GodotAppLauncher"' in text and 'android:label="微光試稿"' in text:
        return text
    return text.replace(
        'android:name=".GodotAppLauncher"',
        'android:name=".GodotAppLauncher"\n            android:label="微光試稿"',
        1,
    )


def main() -> None:
    root = Path(sys.argv[1])
    changed = 0
    for path in root.rglob("AndroidManifest.xml"):
        if "build/intermediates" in str(path):
            continue
        text = path.read_text(encoding="utf-8")
        original = text
        text = text.replace('android:screenOrientation="landscape"', 'android:screenOrientation="portrait"')
        text = _label_launcher(text)
        if "Vc27PreviewLaunch" not in text and "</application>" in text and ".GodotApp" in text:
            text = text.replace("</application>", LAUNCH + "    </application>", 1)
        if text != original:
            path.write_text(text, encoding="utf-8")
            changed += 1
            print("patched", path)
    if changed == 0:
        raise SystemExit("no AndroidManifest.xml patched")

if __name__ == "__main__":
    main()
