#!/usr/bin/env python3
"""Prepare a clean 675+delta tree and judge comparison evidence.

State JSON is not enough. A result is ok only when both PNGs exist, decode,
and are 1080x2280, and the state records match. windows_gpu_proof is true
only when the Windows launcher wrote a displayed-launch manifest.
This file does not claim that proof by itself.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import struct
import subprocess
import sys
import zlib
from pathlib import Path

SKIP_DIRS = {".godot", ".gradle", "android", "build", "__pycache__", ".git", "userdata", "user_data"}
SKIP_FILES = {"export_presets.cfg", "export_credentials.cfg", "override.cfg"}
SKIP_SUFFIXES = {".keystore", ".jks", ".apk", ".aab"}
PNG_SIG = b"\x89PNG\r\n\x1a\n"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def skipped(path: Path) -> bool:
    if any(part in SKIP_DIRS for part in path.parts):
        return True
    if path.name in SKIP_FILES or path.suffix.lower() in SKIP_SUFFIXES:
        return True
    return False


def read_manifest(path: Path) -> list[tuple[str, str]]:
    rows = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        digest, rel = line.split(None, 1)
        rows.append((digest, rel.replace("\\", "/")))
    return rows


def check_hashes(root: Path, manifest: Path, label: str) -> None:
    for digest, rel in read_manifest(manifest):
        src = root / rel
        if src.is_symlink() or not src.is_file():
            raise SystemExit(f"{label}: missing regular file {rel}")
        got = sha256(src)
        if got != digest:
            raise SystemExit(f"{label}: hash mismatch {rel}\n  expected {digest}\n  actual   {got}")


def copy_tree(src: Path, dest: Path) -> None:
    if src.is_symlink():
        raise SystemExit(f"refusing symlink source {src}")
    if src.is_dir():
        if src.name in SKIP_DIRS:
            return
        dest.mkdir(parents=True, exist_ok=True)
        for child in src.iterdir():
            copy_tree(child, dest / child.name)
        return
    if skipped(src):
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() or dest.is_symlink():
        dest.unlink()
    shutil.copyfile(src, dest)


def safe_join(root: Path, rel: str) -> Path:
    rel = rel.replace("\\", "/").lstrip("/")
    if rel.startswith("../") or "/../" in f"/{rel}/" or rel == "..":
        raise SystemExit(f"refusing delta path {rel}")
    dest = (root / rel).resolve()
    if root.resolve() not in dest.parents and dest != root.resolve():
        raise SystemExit(f"refusing delta path {rel}")
    return dest


def apply_delta(delta: Path, work: Path) -> None:
    if delta.is_file() and delta.suffix.lower() == ".zip":
        import zipfile
        with zipfile.ZipFile(delta) as zf:
            for info in zf.infolist():
                name = info.filename.replace("\\", "/")
                if name.endswith("/") or skipped(Path(name)):
                    continue
                dest = safe_join(work, name)
                dest.parent.mkdir(parents=True, exist_ok=True)
                if dest.exists() or dest.is_symlink():
                    dest.unlink()
                with zf.open(info) as src, dest.open("wb") as out:
                    shutil.copyfileobj(src, out)
        return
    if not delta.is_dir():
        raise SystemExit(f"delta is not a directory or zip: {delta}")
    for src in delta.rglob("*"):
        if not src.is_file() or src.is_symlink() or skipped(src):
            continue
        rel = src.relative_to(delta).as_posix()
        dest = safe_join(work, rel)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists() or dest.is_symlink():
            dest.unlink()
        shutil.copyfile(src, dest)


def prepare(baseline: Path, delta: Path, work: Path) -> None:
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    ident = Path(__file__).with_name("hd2d_baseline_67519344.sha256")
    check_hashes(baseline, ident, "baseline")
    copy_tree(baseline, work)
    apply_delta(delta, work)
    check_hashes(work, ident, "work after delta")
    prereq = work / "tools" / "hd2d_stage_prerequisites.sha256"
    check_hashes(work, prereq, "stage prerequisites")
    stage = work / "tools" / "stage_hd2d_assets.py"
    subprocess.run([sys.executable, str(stage)], cwd=work, check=True)


def make_pilot(work: Path, pilot: Path) -> None:
    if pilot.exists():
        shutil.rmtree(pilot)
    pilot.mkdir(parents=True)
    src_godot = work / "godot_hd2d_v6"
    text = (src_godot / "project.godot").read_text(encoding="utf-8")
    text = text.replace("viewport_height=1920", "viewport_height=2280", 1)
    (pilot / "project.godot").write_text(text, encoding="utf-8")
    for folder in ("art", "data", "gameplay", "scenes", "shaders", "textures"):
        copy_tree(src_godot / folder, pilot / folder)
    tools = work / "tools"
    shutil.copyfile(tools / "hd2d_pilot_compare_host.gd.txt", pilot / "hd2d_pilot_compare_host.gd")
    shutil.copyfile(tools / "hd2d_pilot_compare_main.gd.txt", pilot / "hd2d_pilot_compare_main.gd")


def png_size(data: bytes) -> tuple[int, int]:
    if len(data) < 33 or not data.startswith(PNG_SIG) or data[12:16] != b"IHDR":
        raise ValueError("invalid png")
    width, height = struct.unpack(">II", data[16:24])
    if width <= 0 or height <= 0:
        raise ValueError("invalid png")
    # Confirm the IDAT stream is zlib data, not a truncated header.
    zlib.decompress(_idat(data))
    return width, height


def _idat(data: bytes) -> bytes:
    pos = 8
    blob = b""
    while pos + 8 <= len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        tag = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + length]
        if len(chunk) != length:
            raise ValueError("invalid png")
        if tag == b"IDAT":
            blob += chunk
        if tag == b"IEND":
            break
        pos += 12 + length
    if not blob:
        raise ValueError("invalid png")
    return blob


def inspect_png(path: Path) -> tuple[int, int]:
    if not path.is_file() or path.is_symlink():
        raise ValueError("missing")
    data = path.read_bytes()
    if len(data) == 0:
        raise ValueError("empty")
    if not data.startswith(PNG_SIG):
        raise ValueError("invalid")
    width, height = png_size(data)
    if (width, height) != (1080, 2280):
        raise ValueError(f"wrong size {width}x{height}")
    return width, height


def near(a, b, tol: float = 0.02) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) <= tol
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return all(near(x, y, tol) for x, y in zip(a, b))
    return a == b


def check(out: Path, launch: Path | None) -> dict:
    reasons = []
    pilot_png = out / "pilot_standalone.png"
    root_png = out / "root_presentation.png"
    pilot_json = out / "pilot_standalone.json"
    root_json = out / "root_presentation.json"
    for path in (pilot_png, root_png):
        try:
            inspect_png(path)
        except ValueError as exc:
            reasons.append(f"{path.name}: {exc}")
    states = []
    for path in (pilot_json, root_json):
        if not path.is_file():
            reasons.append(f"{path.name}: missing")
            states.append({})
            continue
        states.append(json.loads(path.read_text(encoding="utf-8-sig")))
    pilot, root = states
    keys = (
        "viewport_actual", "mode", "steps", "fixed_dt", "follow_camera_steps",
        "tick_camera_called", "tick_play_called", "care_present",
        "camera_overwritten_each_step", "camera_origin", "camera_fov",
        "visual_global", "visual_offset_y", "visual_pixel_size", "cloud_t", "pet_lag",
    )
    for key in keys:
        if not near(pilot.get(key), root.get(key)):
            reasons.append(f"state {key}")
    if pilot.get("viewport_actual") != [1080, 2280] or root.get("viewport_actual") != [1080, 2280]:
        reasons.append("viewport")
    if pilot.get("follow_camera_steps") != 20 or root.get("follow_camera_steps") != 20:
        reasons.append("follow steps")
    if pilot.get("renderer_actual") != "mobile" or root.get("renderer_actual") != "mobile":
        reasons.append("renderer")
    if not pilot.get("png_written") or not root.get("png_written"):
        reasons.append("png_written is false")
    if pilot.get("care_present") or root.get("care_present"):
        reasons.append("care")
    windows = False
    if launch and launch.is_file():
        meta = json.loads(launch.read_text(encoding="utf-8-sig"))
        windows = bool(meta.get("displayed")) and str(meta.get("os", "")).lower().startswith("windows") and not meta.get("headless")
    result = {
        "ok": not reasons,
        "reasons": reasons,
        "windows_gpu_proof": False,
        "pixel_match_claimed": False,
        "pilot_png": str(pilot_png),
        "root_png": str(root_png),
        "pilot_json": str(pilot_json),
        "root_json": str(root_json),
        "render_target_note": "root SubViewport 1080x2280 versus pilot window 1080x2280; images are evidence, not declared identical",
    }
    if result["ok"] and windows:
        result["windows_gpu_proof"] = True
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["ok"], "windows_gpu_proof": result["windows_gpu_proof"], "reasons": reasons}))
    if reasons:
        raise SystemExit(1)
    return result


def write_png(path: Path, width: int, height: int) -> None:
    raw = b"".join(b"\x00" + (b"\x20\x80\x40" * width) for _ in range(height))
    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    path.write_bytes(PNG_SIG + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def matched_state(side: str) -> dict:
    return {
        "viewport_actual": [1080, 2280],
        "mode": "low",
        "steps": 20,
        "fixed_dt": 1.0 / 60.0,
        "follow_camera_steps": 20,
        "tick_camera_called": False,
        "tick_play_called": False,
        "care_present": False,
        "camera_overwritten_each_step": False,
        "camera_origin": [12.0, 193.0, 207.826858520508],
        "camera_fov": 50.0,
        "visual_global": [0.0, 29.0, 0.0],
        "visual_offset_y": 2.0,
        "visual_pixel_size": 1.0,
        "cloud_t": 0.333333333333333,
        "pet_lag": [0.0, 29.0, 0.0],
        "renderer_actual": "mobile",
        "png_written": True,
        "side": side,
    }


def selftest() -> None:
    import tempfile
    root = Path(tempfile.mkdtemp(prefix="hd2d_evidence_"))
    cases = []
    def run(name: str, build) -> None:
        case = root / name
        case.mkdir()
        build(case)
        try:
            check(case, None)
            cases.append((name, "unexpected ok"))
        except SystemExit as exc:
            cases.append((name, 0 if exc.code in (1, None) else exc.code))
    def missing(case: Path) -> None:
        (case / "pilot_standalone.json").write_text("{}", encoding="utf-8")
        (case / "root_presentation.json").write_text("{}", encoding="utf-8")
    def empty(case: Path) -> None:
        missing(case)
        (case / "pilot_standalone.png").write_bytes(b"")
        (case / "root_presentation.png").write_bytes(b"")
    def bad(case: Path) -> None:
        missing(case)
        (case / "pilot_standalone.png").write_bytes(b"not a png, really")
        (case / "root_presentation.png").write_bytes(b"not a png, really")
    def wrong(case: Path) -> None:
        missing(case)
        write_png(case / "pilot_standalone.png", 2, 2)
        write_png(case / "root_presentation.png", 2, 2)
    run("missing", missing)
    run("empty", empty)
    run("invalid", bad)
    run("wrongsize", wrong)
    good = root / "good"
    good.mkdir()
    write_png(good / "pilot_standalone.png", 1080, 2280)
    write_png(good / "root_presentation.png", 1080, 2280)
    (good / "pilot_standalone.json").write_text(json.dumps(matched_state("pilot_standalone")), encoding="utf-8")
    (good / "root_presentation.json").write_text(json.dumps(matched_state("root_presentation")), encoding="utf-8")
    result = check(good, None)
    if not result["ok"] or result["windows_gpu_proof"]:
        raise SystemExit("selftest: synthetic images must pass the file check without Windows GPU proof")
    failed = [name for name, code in cases if code != 0]
    if failed:
        raise SystemExit(f"selftest fail-closed cases did not fail: {cases}")
    claimed = root / "claimed"
    claimed.mkdir()
    write_png(claimed / "pilot_standalone.png", 1080, 2280)
    write_png(claimed / "root_presentation.png", 1080, 2280)
    (claimed / "pilot_standalone.json").write_text(json.dumps(matched_state("pilot_standalone")), encoding="utf-8")
    (claimed / "root_presentation.json").write_text(json.dumps(matched_state("root_presentation")), encoding="utf-8")
    (claimed / "launch.json").write_text(json.dumps({"displayed": True, "headless": False, "os": "windows"}), encoding="utf-8")
    claimed_result = check(claimed, claimed / "launch.json")
    if not claimed_result["windows_gpu_proof"]:
        raise SystemExit("selftest: checker did not accept a windows launch fixture")
    blocked = root / "blocked"
    blocked.mkdir()
    (blocked / "launch.json").write_text(json.dumps({"displayed": True, "headless": False, "os": "windows"}), encoding="utf-8")
    try:
        check(blocked, blocked / "launch.json")
        raise SystemExit("selftest: windows manifest without PNGs was accepted")
    except SystemExit as exc:
        if exc.code not in (1, None):
            raise
    secret_src = root / "secret_src"
    secret_dst = root / "secret_dst"
    secret_src.mkdir()
    preset = secret_src / "export_presets.cfg"
    keystore = secret_src / "release.keystore"
    preset.write_text("SECRET", encoding="utf-8")
    keystore.write_bytes(b"SECRET")
    (secret_src / "keep.txt").write_text("ordinary", encoding="utf-8")
    preset.chmod(0)
    keystore.chmod(0)
    try:
        copy_tree(secret_src, secret_dst)
    finally:
        preset.chmod(0o644)
        keystore.chmod(0o644)
    if (secret_dst / "export_presets.cfg").exists() or (secret_dst / "release.keystore").exists():
        raise SystemExit("selftest: sensitive files were copied")
    if (secret_dst / "keep.txt").read_text(encoding="utf-8") != "ordinary":
        raise SystemExit("selftest: ordinary file was not copied")
    try:
        safe_join(secret_dst, "../export_presets.cfg")
        raise SystemExit("selftest: path escape was accepted")
    except SystemExit as exc:
        if "refusing" not in str(exc):
            raise
    ident = Path(__file__).with_name("hd2d_baseline_67519344.sha256")
    ident_root = root / "ident"
    repo = Path(__file__).resolve().parents[1]
    for _digest, rel in read_manifest(ident):
        src = repo / rel
        dest = ident_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
    check_hashes(ident_root, ident, "identity fixture")
    script = Path(__file__).with_name("run_hd2d_mobile_compare.ps1").read_text(encoding="utf-8")
    for required in (
        "[Parameter(Mandatory = $true)][string]$GodotExe",
        "[Parameter(Mandatory = $true)][string]$Python",
        "[Parameter(Mandatory = $true)][string]$Baseline675",
        "[Parameter(Mandatory = $true)][string]$DeltaPath",
        "[Parameter(Mandatory = $true)][string]$OutputDir",
        "$env:HD2D_COMPARE_GRAB = '1'",
        "$env:HD2D_COMPARE_DISPLAY = '1'",
        "--rendering-method",
        "hd2d_evidence.py",
    ):
        if required not in script:
            raise SystemExit(f"selftest: powershell entry missing {required}")
    displayed = script.split("function Start-Godot", 1)[1].split("\nfunction ", 1)[0]
    if "--headless" in displayed or "\nbash " in script or script.startswith("bash"):
        raise SystemExit("selftest: powershell entry requests headless or bash")
    if "function Import-Project" not in script or "--import" not in script:
        raise SystemExit("selftest: asset import pass is missing")
    shutil.rmtree(root, ignore_errors=True)
    print("selftest ok windows_gpu_proof=false")
    print("checker fixture can record windows_gpu_proof; this process did not launch Windows")


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "prepare":
        args = dict(zip(sys.argv[2::2], sys.argv[3::2]))
        work = Path(args["--work"])
        prepare(Path(args["--baseline"]), Path(args["--delta"]), work)
        make_pilot(work, Path(args["--pilot"]))
        print("prepare ok")
        return
    if cmd == "check":
        args = dict(zip(sys.argv[2::2], sys.argv[3::2]))
        launch = Path(args["--launch"]) if "--launch" in args else None
        check(Path(args["--out"]), launch)
        return
    if cmd == "selftest":
        selftest()
        return
    raise SystemExit("usage: hd2d_evidence.py prepare|check|selftest")


if __name__ == "__main__":
    main()
