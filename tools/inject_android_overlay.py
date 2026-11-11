#!/usr/bin/env python3
"""將 native/android 浮動團絨來源注入 Godot gradle 工程（android/build）。"""
from __future__ import annotations

import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

AND = "{http://schemas.android.com/apk/res/android}"
TOOLS = "{http://schemas.android.com/tools}"
ET.register_namespace("android", "http://schemas.android.com/apk/res/android")
ET.register_namespace("tools", "http://schemas.android.com/tools")

PERMS = [
    "android.permission.INTERNET",
    "android.permission.SYSTEM_ALERT_WINDOW",
    "android.permission.FOREGROUND_SERVICE",
    "android.permission.FOREGROUND_SERVICE_SPECIAL_USE",
    "android.permission.POST_NOTIFICATIONS",
    "android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS",
    "android.permission.ACTIVITY_RECOGNITION",
    "android.permission.ACCESS_COARSE_LOCATION",
]
FEATURES = [
    ("android.hardware.sensor.stepcounter", False),
    ("android.hardware.location", False),
    ("android.hardware.location.network", False),
]


def copy_tree(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, dest, dirs_exist_ok=True)
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)


def ensure_perm(root: ET.Element, name: str) -> None:
    for el in root.findall("uses-permission"):
        if el.get(f"{AND}name") == name:
            return
    el = ET.Element("uses-permission")
    el.set(f"{AND}name", name)
    # insert before application
    app = root.find("application")
    if app is not None:
        idx = list(root).index(app)
        root.insert(idx, el)
    else:
        root.append(el)


def ensure_feature(root: ET.Element, name: str | None, gl: str | None, required: bool) -> None:
    for el in root.findall("uses-feature"):
        if name and el.get(f"{AND}name") == name:
            el.set(f"{AND}required", "true" if required else "false")
            return
        if gl and el.get(f"{AND}glEsVersion") == gl:
            el.set(f"{AND}required", "true" if required else "false")
            el.set(f"{TOOLS}replace", "android:required")
            return
    el = ET.Element("uses-feature")
    if name:
        el.set(f"{AND}name", name)
    if gl:
        el.set(f"{AND}glEsVersion", gl)
        el.set(f"{TOOLS}replace", "android:required")
    el.set(f"{AND}required", "true" if required else "false")
    app = root.find("application")
    if app is not None:
        root.insert(list(root).index(app), el)
    else:
        root.append(el)


def find_child(app: ET.Element, tag: str, name: str) -> ET.Element | None:
    for el in app.findall(tag):
        if el.get(f"{AND}name") == name:
            return el
    return None


def patch_manifest(path: Path) -> None:
    tree = ET.parse(path)
    root = tree.getroot()
    for p in PERMS:
        ensure_perm(root, p)
    ensure_feature(root, None, "0x00030000", False)
    for name, req in FEATURES:
        ensure_feature(root, name, None, req)

    app = root.find("application")
    if app is None:
        raise SystemExit("no <application> in " + str(path))

    # Godot activity portrait
    act = find_child(app, "activity", ".GodotApp")
    if act is None:
        act = find_child(app, "activity", "com.godot.game.GodotApp")
    if act is not None:
        act.set(f"{AND}screenOrientation", "portrait")
        prev = act.get(f"{TOOLS}replace", "")
        bits = [b for b in prev.split(",") if b]
        if "android:screenOrientation" not in bits:
            bits.append("android:screenOrientation")
        act.set(f"{TOOLS}replace", ",".join(bits))

    def ensure_activity(name: str, label: str, exported: str) -> None:
        el = find_child(app, "activity", name)
        if el is None:
            el = ET.SubElement(app, "activity")
            el.set(f"{AND}name", name)
        el.set(f"{AND}screenOrientation", "portrait")
        el.set(f"{AND}label", label)
        el.set(f"{AND}exported", exported)
        el.set(f"{AND}theme", "@android:style/Theme.Material.Light.DarkActionBar")

    ensure_activity("hk.vizard.glimmer.fpet.SettingsActivity", "浮動團絨", "true")
    ensure_activity("hk.vizard.glimmer.fpet.PowerGuideActivity", "自啟動／省電白名單", "false")

    svc = find_child(app, "service", "hk.vizard.glimmer.fpet.PetOverlayService")
    if svc is None:
        svc = ET.SubElement(app, "service")
        svc.set(f"{AND}name", "hk.vizard.glimmer.fpet.PetOverlayService")
    svc.set(f"{AND}exported", "false")
    svc.set(f"{AND}foregroundServiceType", "specialUse")
    prop = None
    for ch in svc:
        if ch.tag == "property" and ch.get(f"{AND}name") == "android.app.PROPERTY_SPECIAL_USE_FGS_SUBTYPE":
            prop = ch
            break
    if prop is None:
        prop = ET.SubElement(svc, "property")
        prop.set(f"{AND}name", "android.app.PROPERTY_SPECIAL_USE_FGS_SUBTYPE")
    prop.set(
        f"{AND}value",
        "Floating virtual pet overlay drawn above other apps while the user has it switched on (desktop companion).",
    )

    # plugin meta-data
    found = False
    for el in app.findall("meta-data"):
        if el.get(f"{AND}name") == "org.godotengine.plugin.v2.GlimmerOverlay":
            el.set(f"{AND}value", "hk.vizard.glimmer.fpet.GlimmerOverlayPlugin")
            found = True
    if not found:
        md = ET.SubElement(app, "meta-data")
        md.set(f"{AND}name", "org.godotengine.plugin.v2.GlimmerOverlay")
        md.set(f"{AND}value", "hk.vizard.glimmer.fpet.GlimmerOverlayPlugin")

    def ensure_plugin(meta_name: str, cls: str) -> None:
        hit = False
        for el in app.findall("meta-data"):
            if el.get(f"{AND}name") == meta_name:
                el.set(f"{AND}value", cls)
                hit = True
        if not hit:
            md = ET.SubElement(app, "meta-data")
            md.set(f"{AND}name", meta_name)
            md.set(f"{AND}value", cls)

    ensure_plugin("org.godotengine.plugin.v2.RealWorld", "hk.vizard.glimmer.fpet.RealWorldPlugin")
    ensure_plugin("org.godotengine.plugin.v2.Share6d", "hk.vizard.glimmer.fpet.Share6dPlugin")

    # InitializationProvider authority
    prov = find_child(app, "provider", "androidx.startup.InitializationProvider")
    if prov is None:
        prov = ET.SubElement(app, "provider")
        prov.set(f"{AND}name", "androidx.startup.InitializationProvider")
    prov.set(f"{AND}authorities", "${applicationId}.androidx-startup")
    prov.set(f"{AND}exported", "false")
    prev = prov.get(f"{TOOLS}replace", "")
    bits = [b for b in prev.split(",") if b]
    if "android:authorities" not in bits:
        bits.append("android:authorities")
    prov.set(f"{TOOLS}replace", ",".join(bits))

    tree.write(path, encoding="utf-8", xml_declaration=True)
    print("patched manifest", path)


def main() -> int:
    repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/workspace/glimmer-godot")
    build = Path(sys.argv[2] if len(sys.argv) > 2 else repo / "android/build")
    src = repo / "native/android/src/main"
    if not (build / "build.gradle").exists() and not (build / "src/main/AndroidManifest.xml").exists():
        print("android/build not ready:", build, file=sys.stderr)
        return 2
    copy_tree(src / "java", build / "src/main/java")
    copy_tree(src / "res", build / "src/main/res")
    copy_tree(src / "assets", build / "src/main/assets")
    mf = build / "src/main/AndroidManifest.xml"
    if not mf.exists():
        print("missing", mf, file=sys.stderr)
        return 3
    patch_manifest(mf)
    for flavor in ("debug", "release", "instrumented"):
        fm = build / "src" / flavor / "AndroidManifest.xml"
        if fm.exists():
            patch_manifest(fm)
    print("injected overlay into", build)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
