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
import re
import shutil
import stat
import struct
import subprocess
import sys
import zipfile
import zlib
from pathlib import Path

SKIP_DIRS = {".godot", ".gradle", "android", "build", "__pycache__", ".git", "userdata", "user_data"}
SKIP_FILES = {"export_presets.cfg", "export_credentials.cfg", "override.cfg"}
SKIP_SUFFIXES = {".keystore", ".jks", ".apk", ".aab"}
PNG_SIG = b"\x89PNG\r\n\x1a\n"
MEMBER_NAME = "MEMBER_SHA256"
CLOSURE_NAME = "hd2d_root_closure.sha256"
RES_TOKEN = re.compile(r"res://([A-Za-z0-9_./%+\-@]+)")
BINARY_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".webp", ".glb", ".ogg", ".wav", ".mp3",
    ".otf", ".ttf", ".aac",
}
MATERIAL_NULL_FUNCS = (
    "material_casts_shadows",
    "material_is_animated",
    "material_get_instance_shader_parameters",
    "material_update_dependency",
)


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


def reject_rel(rel: str) -> None:
    text = rel.replace("\\", "/")
    if not text or "\x00" in text or text.startswith("/") or text.startswith("//"):
        raise SystemExit(f"refusing delta path {rel}")
    head = text.split("/", 1)[0]
    if ":" in head:
        raise SystemExit(f"refusing delta path {rel}")
    parts = [part for part in text.split("/") if part not in ("", ".")]
    if not parts or any(part == ".." for part in parts):
        raise SystemExit(f"refusing delta path {rel}")


def safe_join(root: Path, rel: str) -> Path:
    rel = rel.replace("\\", "/")
    reject_rel(rel)
    dest = (root / rel).resolve()
    if root.resolve() not in dest.parents and dest != root.resolve():
        raise SystemExit(f"refusing delta path {rel}")
    return dest


def require_fresh_output(path: Path) -> None:
    """Accept a missing path or an empty directory. Do not create or delete anything."""
    if not path.exists() and not path.is_symlink():
        return
    if path.is_symlink() or not path.is_dir():
        raise SystemExit(f"output is not an empty directory: {path}")
    if any(path.iterdir()):
        raise SystemExit(f"output is not empty: {path}")


def load_identity() -> dict[str, str]:
    ident = Path(__file__).with_name("hd2d_baseline_67519344.sha256")
    return {rel: digest for digest, rel in read_manifest(ident)}


def closure_path() -> Path:
    return Path(__file__).with_name(CLOSURE_NAME)


def read_closure(path: Path | None = None) -> tuple[dict[str, str], list[str]]:
    required: dict[str, str] = {}
    absent: list[str] = []
    for raw in (path or closure_path()).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        kind, rest = line.split(None, 1)
        if kind == "required":
            digest, rel = rest.split(None, 1)
            required[rel.replace("\\", "/")] = digest.lower()
        elif kind == "source_absent":
            absent.append(rest.replace("\\", "/"))
        else:
            raise SystemExit(f"bad closure line: {line}")
    if "scenes/Main.tscn" not in required:
        raise SystemExit("root closure is missing scenes/Main.tscn")
    return required, absent


def source_names(path: Path) -> set[str]:
    """File names only. Secret names are skipped and their bytes are not read."""
    names: set[str] = set()
    if path.is_dir():
        for src in path.rglob("*"):
            if src.is_symlink() or not src.is_file() or skipped(src):
                continue
            names.add(src.relative_to(path).as_posix())
        return names
    if path.is_file() and path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as zf:
            return set(_zip_file_names(zf)) - {MEMBER_NAME}
    raise SystemExit(f"not a directory or zip: {path}")


def assert_root_available(available: set[str], required: dict[str, str]) -> None:
    missing = sorted(rel for rel in required if rel not in available)
    if not missing:
        return
    first = [rel for rel in ("scenes/Main.tscn", "project.godot", "icon.png", "scripts/autoload/GameData.gd") if rel in missing]
    preview = ", ".join(first + [rel for rel in missing if rel not in first][:8])
    raise SystemExit(
        "art-only baseline is missing the root game files required by project.godot "
        f"({len(missing)}): {preview}"
    )


def _consider_file(repo: Path, rel: str, required: dict[str, str], queue: list[str]) -> None:
    if rel in required or skipped(Path(rel)) or rel.startswith(("godot_hd2d_v6/", "hd2d_stage/", ".godot/")):
        return
    path = repo / rel
    if path.is_symlink() or not path.is_file():
        return
    required[rel] = sha256(path)
    queue.append(rel)
    for suffix in (".import", ".uid"):
        extra = rel + suffix
        extra_path = repo / extra
        if extra not in required and extra_path.is_file() and not extra_path.is_symlink() and not skipped(extra_path):
            required[extra] = sha256(extra_path)


def _consider_tree(repo: Path, prefix: str, required: dict[str, str], queue: list[str], seen_dirs: set[str]) -> None:
    prefix = prefix.strip("/") + "/"
    if prefix in seen_dirs or prefix.startswith(("godot_hd2d_v6/", "hd2d_stage/", ".godot/")):
        return
    seen_dirs.add(prefix)
    base = repo / prefix
    if not base.is_dir() or base.is_symlink():
        return
    for child in base.rglob("*"):
        if not child.is_file() or child.is_symlink() or skipped(child):
            continue
        rel = child.relative_to(repo).as_posix()
        _consider_file(repo, rel, required, queue)


def collect_root_closure(repo: Path) -> tuple[dict[str, str], list[str]]:
    """Real files reachable from the root project. Does not invent missing art."""
    required: dict[str, str] = {}
    absent: list[str] = []
    queue: list[str] = []
    seen_dirs: set[str] = set()

    def consider(token: str) -> None:
        rel = token.replace("\\", "/").split("::", 1)[0].strip()
        if not rel or rel.startswith(("godot_hd2d_v6/", "hd2d_stage/", ".godot/", "uid:")):
            return
        if skipped(Path(rel)):
            return
        if "%" in rel or "*" in rel or rel.endswith("/"):
            prefix = rel.split("%", 1)[0].split("*", 1)[0]
            if not prefix.endswith("/"):
                prefix = prefix.rsplit("/", 1)[0] + "/" if "/" in prefix else prefix
            base = repo / prefix
            if not base.exists():
                absent.append(prefix)
            else:
                _consider_tree(repo, prefix, required, queue, seen_dirs)
            return
        path = repo / rel
        if path.is_dir() and not path.is_symlink():
            _consider_tree(repo, rel, required, queue, seen_dirs)
            return
        if path.is_file() and not path.is_symlink():
            before = len(required)
            _consider_file(repo, rel, required, queue)
            if rel.startswith("addons/") and "/" in rel:
                _consider_tree(repo, "/".join(rel.split("/")[:2]), required, queue, seen_dirs)
            if len(required) != before or rel in required:
                return
        absent.append(rel)

    seeds = [
        "project.godot",
        "icon.png",
        "scenes/Main.tscn",
        "tests/hd2d_same_view.gd",
        "tools/stage_hd2d_assets.py",
        "tools/hd2d_stage_prerequisites.sha256",
        "tools/hd2d_pilot_compare_host.gd.txt",
        "tools/hd2d_pilot_compare_main.gd.txt",
        "scripts/hd2d_exterior_host.gd",
        "scripts/hd2d_presentation.gd",
        "scripts/hd2d_assets.gd",
        "scripts/hd2d_door.gd",
    ]
    for rel in seeds:
        consider(rel)
    class_name = re.compile(r"(?m)^class_name\s+[A-Za-z_][A-Za-z0-9_]*")
    for path in repo.rglob("*.gd"):
        if not path.is_file() or path.is_symlink() or skipped(path):
            continue
        rel = path.relative_to(repo).as_posix()
        if rel.startswith(("godot_hd2d_v6/", "hd2d_stage/", ".godot/")):
            continue
        try:
            head = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if class_name.search(head):
            consider(rel)
    while queue:
        rel = queue.pop()
        path = repo / rel
        if path.suffix.lower() in BINARY_SUFFIXES or skipped(path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for match in RES_TOKEN.finditer(text):
            consider(match.group(1))
    return required, sorted(set(absent))


def write_closure(repo: Path, dest: Path) -> None:
    required, absent = collect_root_closure(repo)
    lines = [
        "# Root files the compare loads. Hashes are of the named source tree.",
        "# required <sha256> <path>",
        "# source_absent <path> is referenced and was not in that tree. No stub is added.",
    ]
    for rel in sorted(required):
        lines.append(f"required {required[rel]} {rel}")
    for rel in absent:
        lines.append(f"source_absent {rel}")
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")


def split_closure(required: dict[str, str]) -> tuple[dict[str, str], dict[str, str]]:
    support: dict[str, str] = {}
    assets: dict[str, str] = {}
    for rel, digest in required.items():
        if rel.startswith(("art/", "art-pet/", "audio/")):
            assets[rel] = digest
        else:
            support[rel] = digest
    return support, assets


def build_support_zip(repo: Path, dest: Path, required: dict[str, str] | None = None) -> dict[str, bytes]:
    if required is None:
        required, _absent = read_closure()
    members: dict[str, bytes] = {}
    for rel, digest in sorted(required.items()):
        path = repo / rel
        if path.is_symlink() or not path.is_file() or skipped(path):
            raise SystemExit(f"root support file is not a regular file: {rel}")
        data = path.read_bytes()
        got = hashlib.sha256(data).hexdigest()
        if got != digest:
            raise SystemExit(f"root support hash mismatch {rel}")
        members[rel] = data
    listed = [f"{hashlib.sha256(members[name]).hexdigest()}  {name}" for name in sorted(members)]
    packed = dict(members)
    packed[MEMBER_NAME] = ("\n".join(listed) + "\n").encode("utf-8")
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as handle:
        for name in sorted(packed):
            handle.writestr(name, packed[name])
    return packed


def classify_godot_log(text: str, required: set[str] | None = None) -> dict:
    """Separate import/parse failures from the known null-material teardown lines."""
    required = required or set()
    fatal: list[str] = []
    material: list[str] = []
    rows = [raw.strip() for raw in text.splitlines() if raw.strip()]
    index = 0
    while index < len(rows):
        line = rows[index]
        nxt = rows[index + 1] if index + 1 < len(rows) and rows[index + 1].startswith("at:") else ""
        if nxt:
            index += 1
        blob = f"{line} {nxt}".strip()
        index += 1
        if "Parameter \"material\" is null" in blob and any(name in blob for name in MATERIAL_NULL_FUNCS):
            material.append(blob)
            continue
        line = blob
        path_match = RES_TOKEN.search(line)
        rel = path_match.group(1) if path_match else ""
        structural = any(token in line for token in (
            "Failed to create an autoload",
            "Parse Error",
            "SCRIPT ERROR",
            "Failed to load script",
            "Cannot open file",
        ))
        resource = "Failed loading resource" in line or "Attempt to open script" in line or "Resource file not found" in line
        if structural or (resource and (not rel or rel in required)):
            fatal.append(line)
    material_class = "none"
    if material and not fatal:
        material_class = "lifetime_cleanup"
    elif material:
        material_class = "alongside_fatal"
    return {
        "fatal": fatal,
        "material_null": material,
        "material_null_class": material_class,
        "material_null_note": (
            "Four RendererRD material RID lookups returned null once each. "
            "The same calls appear at process teardown after a drawn frame. "
            "They are not a Failed-loading-resource for a frozen texture, and they are not removed from the log."
            if material_class == "lifetime_cleanup" else ""
        ),
    }


def parse_manifest_text(text: str) -> list[tuple[str, str]]:
    rows = []
    seen = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        digest, rel = line.split(None, 1)
        digest = digest.lower()
        rel = rel.replace("\\", "/")
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise SystemExit(f"bad member digest for {rel}")
        reject_rel(rel)
        if rel == MEMBER_NAME:
            raise SystemExit("MEMBER_SHA256 must not list itself")
        if rel in seen:
            raise SystemExit(f"duplicate manifest entry {rel}")
        if skipped(Path(rel)):
            raise SystemExit(f"manifest lists a skipped entry {rel}")
        seen.add(rel)
        rows.append((digest, rel))
    if not rows:
        raise SystemExit("MEMBER_SHA256 lists no files")
    return rows


def _zip_file_names(zf: zipfile.ZipFile) -> list[str]:
    names = []
    for info in zf.infolist():
        name = info.filename.replace("\\", "/")
        is_dir = name.endswith("/")
        rel = name[:-1] if is_dir else name
        reject_rel(rel)
        mode = (info.external_attr >> 16) & 0xFFFF
        if mode and stat.S_ISLNK(mode):
            raise SystemExit(f"refusing symlink entry {name}")
        if skipped(Path(rel)):
            raise SystemExit(f"refusing secret entry {name}")
        if is_dir:
            continue
        names.append(name)
    if len(names) != len(set(names)):
        raise SystemExit("duplicate zip entry")
    return names


def verify_delta_members(delta: Path, expected_sha: str | None = None, identity: dict[str, str] | None = None) -> list[str]:
    """Check the member list before any extract. MEMBER_SHA256 is not a listed file."""
    if identity is None:
        identity = load_identity()
    if delta.is_file() and delta.suffix.lower() == ".zip":
        with zipfile.ZipFile(delta) as zf:
            names = _zip_file_names(zf)
            if MEMBER_NAME not in names:
                raise SystemExit("delta is missing MEMBER_SHA256")
            rows = parse_manifest_text(zf.read(MEMBER_NAME).decode("utf-8"))
            listed = {rel: digest for digest, rel in rows}
            members = set(names) - {MEMBER_NAME}
            missing = sorted(set(listed) - members)
            unlisted = sorted(members - set(listed))
            if missing:
                raise SystemExit(f"manifest lists files that are not in the zip: {missing}")
            if unlisted:
                raise SystemExit(f"zip members are not listed in MEMBER_SHA256: {unlisted}")
            for rel, digest in listed.items():
                if rel in identity and identity[rel] != digest:
                    raise SystemExit(f"delta changes frozen file {rel}")
            for rel, digest in listed.items():
                got = hashlib.sha256(zf.read(rel)).hexdigest()
                if got != digest:
                    raise SystemExit(f"member hash mismatch {rel}")
        if expected_sha and sha256(delta).lower() != expected_sha.lower():
            raise SystemExit("delta sha mismatch")
        return [rel for _digest, rel in rows]
    if not delta.is_dir():
        raise SystemExit(f"delta is not a directory or zip: {delta}")
    found = []
    for src in sorted(delta.rglob("*")):
        rel = src.relative_to(delta).as_posix()
        reject_rel(rel)
        if src.is_symlink():
            raise SystemExit(f"refusing symlink entry {rel}")
        if src.is_dir():
            if skipped(src):
                raise SystemExit(f"refusing secret entry {rel}")
            continue
        if skipped(src):
            raise SystemExit(f"refusing secret entry {rel}")
        found.append(rel)
    if len(found) != len(set(found)):
        raise SystemExit("duplicate delta entry")
    if MEMBER_NAME not in found:
        raise SystemExit("delta is missing MEMBER_SHA256")
    rows = parse_manifest_text((delta / MEMBER_NAME).read_text(encoding="utf-8"))
    listed = {rel: digest for digest, rel in rows}
    members = set(found) - {MEMBER_NAME}
    missing = sorted(set(listed) - members)
    unlisted = sorted(members - set(listed))
    if missing:
        raise SystemExit(f"manifest lists files that are not in the delta: {missing}")
    if unlisted:
        raise SystemExit(f"delta files are not listed in MEMBER_SHA256: {unlisted}")
    for rel, digest in listed.items():
        if rel in identity and identity[rel] != digest:
            raise SystemExit(f"delta changes frozen file {rel}")
        src = delta / rel
        if src.is_symlink() or skipped(src):
            raise SystemExit(f"refusing secret entry {rel}")
        if sha256(src) != digest:
            raise SystemExit(f"member hash mismatch {rel}")
    if expected_sha:
        raise SystemExit("delta sha applies to a zip, not a directory")
    return [rel for _digest, rel in rows]


def apply_delta(delta: Path, work: Path, names: list[str] | None = None, expected_sha: str | None = None, identity: dict[str, str] | None = None) -> None:
    if names is None:
        names = verify_delta_members(delta, expected_sha, identity)
    if delta.is_file() and delta.suffix.lower() == ".zip":
        with zipfile.ZipFile(delta) as zf:
            for name in names:
                if name == MEMBER_NAME or skipped(Path(name)):
                    raise SystemExit(f"refusing to extract {name}")
                dest = safe_join(work, name)
                dest.parent.mkdir(parents=True, exist_ok=True)
                if dest.is_symlink():
                    raise SystemExit(f"refusing to replace symlink {name}")
                with zf.open(name) as src, dest.open("wb") as out:
                    shutil.copyfileobj(src, out)
        return
    for name in names:
        if name == MEMBER_NAME or skipped(Path(name)):
            raise SystemExit(f"refusing to extract {name}")
        src = delta / name
        if src.is_symlink() or not src.is_file():
            raise SystemExit(f"refusing delta path {name}")
        dest = safe_join(work, name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)


def prepare(
    baseline: Path,
    delta: Path,
    work: Path,
    expected_sha: str | None = None,
    root_packs: list[Path] | None = None,
    root_shas: list[str] | None = None,
    closure: Path | None = None,
) -> None:
    require_fresh_output(work)
    packs = list(root_packs or [])
    shas = list(root_shas or [])
    names_by_pack = []
    for index, pack in enumerate(packs):
        sha = shas[index] if index < len(shas) and shas[index] else None
        names_by_pack.append(verify_delta_members(pack, sha))
    delta_names = verify_delta_members(delta, expected_sha)
    ident = Path(__file__).with_name("hd2d_baseline_67519344.sha256")
    check_hashes(baseline, ident, "baseline")
    prereq = Path(__file__).with_name("hd2d_stage_prerequisites.sha256")
    check_hashes(baseline, prereq, "stage prerequisites")
    required, _absent = read_closure(closure)
    available = source_names(baseline)
    for pack in packs:
        available.update(source_names(pack))
    available.update(delta_names)
    assert_root_available(available, required)
    work.mkdir(parents=True, exist_ok=True)
    copy_tree(baseline, work)
    for pack, names in zip(packs, names_by_pack):
        apply_delta(pack, work, names)
    apply_delta(delta, work, delta_names)
    check_hashes(work, ident, "work after delta")
    for rel, digest in required.items():
        src = work / rel
        if src.is_symlink() or not src.is_file():
            raise SystemExit(f"root closure missing after prepare: {rel}")
        got = sha256(src)
        if got != digest:
            raise SystemExit(f"root closure hash mismatch {rel}\n  expected {digest}\n  actual   {got}")
    check_hashes(work, prereq, "stage prerequisites")
    stage = work / "tools" / "stage_hd2d_assets.py"
    subprocess.run([sys.executable, str(stage)], cwd=work, check=True)
    staged = work / "hd2d_stage" / "textures" / "tiles" / "cloud_shadow.png"
    if staged.is_symlink() or not staged.is_file():
        raise SystemExit("stage did not produce hd2d_stage/textures/tiles/cloud_shadow.png")


def make_pilot(work: Path, pilot: Path) -> None:
    require_fresh_output(pilot)
    pilot.mkdir(parents=True, exist_ok=True)
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
    material_class = "none"
    material_count = 0
    material_note = ""
    if closure_path().is_file():
        required_paths, _absent_paths = read_closure()
        combined = []
        for name in ("pilot.err.log", "root.err.log", "pilot.import.err.log", "root.import.err.log"):
            log_path = out / name
            if log_path.is_file():
                combined.append(log_path.read_text(encoding="utf-8", errors="replace"))
        if combined:
            report = classify_godot_log("\n".join(combined), set(required_paths))
            material_class = report["material_null_class"]
            material_count = len(report["material_null"])
            material_note = report["material_null_note"]
            for line in report["fatal"][:8]:
                reasons.append(line)
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
        "material_null_class": material_class,
        "material_null_count": material_count,
        "material_null_note": material_note,
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
    if "[Parameter(Mandatory = $true)][string[]]$RootPack" not in script or "Expand-PackArgument" not in script:
        raise SystemExit("selftest: powershell entry does not require the root packs")
    import_block = script.split("function Import-Project", 1)[1].split("function Start-Godot", 1)[0]
    if "Save-GodotStreams" not in import_block or import_block.find("Save-GodotStreams") > import_block.find('throw "Godot import timed out'):
        raise SystemExit("selftest: timeout does not flush Godot logs first")
    fresh = script.find("Assert-FreshOutput $OutputDir")
    created = script.find("New-Item -ItemType Directory")
    prepare_at = script.find("'prepare'")
    if fresh < 0 or created < 0 or prepare_at < 0 or fresh > created or fresh > prepare_at:
        raise SystemExit("selftest: OutputDir is not checked before a write")
    if "OutputDir is not empty" not in script or "$outputAccepted" not in script:
        raise SystemExit("selftest: nonempty OutputDir cleanup is not refused")
    shutil.rmtree(root, ignore_errors=True)
    import unittest
    suite = unittest.defaultTestLoader.loadTestsFromName("test_hd2d_evidence")
    outcome = unittest.TextTestRunner(verbosity=1).run(suite)
    if not outcome.wasSuccessful():
        raise SystemExit("selftest: unit tests failed")
    print("selftest ok windows_gpu_proof=false")
    print("checker fixture can record windows_gpu_proof; this process did not launch Windows")


def _paired_args(argv: list[str]) -> tuple[dict[str, str], list[str], list[str]]:
    args: dict[str, str] = {}
    roots: list[str] = []
    root_shas: list[str] = []
    pairs = list(zip(argv[::2], argv[1::2]))
    if len(argv) % 2:
        raise SystemExit("arguments must be --flag value pairs")
    for key, value in pairs:
        if key == "--root":
            roots.append(value)
        elif key == "--root-sha":
            root_shas.append(value)
        else:
            args[key] = value
    return args, roots, root_shas


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "prepare":
        args, roots, root_shas = _paired_args(sys.argv[2:])
        work = Path(args["--work"])
        prepare(
            Path(args["--baseline"]),
            Path(args["--delta"]),
            work,
            args.get("--delta-sha") or None,
            [Path(item) for item in roots],
            root_shas,
        )
        make_pilot(work, Path(args["--pilot"]))
        print("prepare ok")
        return
    if cmd == "import-log":
        args, _roots, _shas = _paired_args(sys.argv[2:])
        text = Path(args["--err"]).read_text(encoding="utf-8", errors="replace")
        required, _absent = read_closure()
        report = classify_godot_log(text, set(required))
        out = Path(args["--out"]) if "--out" in args else None
        payload = {
            "ok": not report["fatal"],
            "windows_gpu_proof": False,
            "reasons": report["fatal"][:20],
            "material_null_class": report["material_null_class"],
            "material_null_count": len(report["material_null"]),
            "material_null_note": report["material_null_note"],
        }
        if out:
            out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"ok": payload["ok"], "material_null_class": payload["material_null_class"], "fatal": len(report["fatal"])}))
        if report["fatal"]:
            raise SystemExit(1)
        return
    if cmd == "fresh-output":
        args = dict(zip(sys.argv[2::2], sys.argv[3::2]))
        require_fresh_output(Path(args["--out"]))
        print("fresh-output ok")
        return
    if cmd == "check":
        args = dict(zip(sys.argv[2::2], sys.argv[3::2]))
        launch = Path(args["--launch"]) if "--launch" in args else None
        check(Path(args["--out"]), launch)
        return
    if cmd == "selftest":
        selftest()
        return
    raise SystemExit("usage: hd2d_evidence.py prepare|check|fresh-output|selftest")


if __name__ == "__main__":
    main()
