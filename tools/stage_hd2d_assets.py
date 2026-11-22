#!/usr/bin/env python3
"""Copy frozen 675 bytes into hd2d_stage as regular files.

Does not create symlinks, junctions, or hard links. Does not modify
godot_hd2d_v6. A source whose SHA-256 differs from
tools/hd2d_stage_prerequisites.sha256 is refused.
"""
from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tools" / "hd2d_stage_prerequisites.sha256"
SOURCE_PREFIX = "godot_hd2d_v6/art/"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def prerequisites() -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for raw in MANIFEST.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        digest, rel = line.split(None, 1)
        rows.append((digest, rel.replace("\\", "/")))
    if not rows:
        raise SystemExit("stage_hd2d_assets: prerequisite manifest is empty")
    return rows


def destination(src_rel: str) -> Path:
    if not src_rel.startswith(SOURCE_PREFIX):
        raise SystemExit(f"stage_hd2d_assets: unexpected source {src_rel}")
    return ROOT / "hd2d_stage" / src_rel[len(SOURCE_PREFIX):]


PILOT = ROOT / "godot_hd2d_v6"
STAGE = ROOT / "hd2d_stage"
ASSET_TREES = ("textures", "shaders", "art")
REMAP_SCRIPTS = (
    "scenes/capture.gd",
    "scenes/art_depth.gd",
    "scenes/prop_bump.gd",
    "gameplay/m1_walk_clip.gd",
    "gameplay/m1_camera_policy.gd",
    "gameplay/m1_ui_layout.gd",
)
DATA_FILES = ("data/prop_bump.json",)
PROVENANCE = ROOT / "tools" / "hd2d_generated_provenance.txt"
SKIP_NAMES = {".import", ".uid"}


def write_regular(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_symlink() or dest.exists():
        dest.unlink()
    shutil.copyfile(src, dest)
    if dest.is_symlink() or not dest.is_file():
        raise SystemExit(f"stage_hd2d_assets: copy did not leave a regular file at {dest}")
    if sha256(dest) != sha256(src):
        raise SystemExit(f"stage_hd2d_assets: copied bytes differ at {dest}")


def copy_assets() -> int:
    copied = 0
    for folder in ASSET_TREES:
        src_root = PILOT / folder
        if not src_root.is_dir():
            raise SystemExit(f"stage_hd2d_assets: missing {src_root}")
        for src in src_root.rglob("*"):
            if not src.is_file() or src.is_symlink():
                if src.is_symlink():
                    raise SystemExit(f"stage_hd2d_assets: refusing symlink source {src}")
                continue
            if src.suffix in SKIP_NAMES or src.name.endswith(".import"):
                continue
            dest = STAGE / folder / src.relative_to(src_root)
            write_regular(src, dest)
            copied += 1
    for rel in DATA_FILES:
        src = PILOT / rel
        if src.is_symlink() or not src.is_file():
            raise SystemExit(f"stage_hd2d_assets: need a regular file at {rel}")
        write_regular(src, STAGE / rel)
        copied += 1
    return copied


def remap_scripts() -> None:
    # Path-only copies. Lifecycle binding lives in scripts/hd2d_exterior_host.gd.
    lines = [
        "# Path-only generated copies. Not the lifecycle host.",
        "# kind frozen_sha256 generated_sha256 frozen_path generated_path",
    ]
    for rel in REMAP_SCRIPTS:
        src = PILOT / rel
        if src.is_symlink() or not src.is_file():
            raise SystemExit(f"stage_hd2d_assets: need a regular script at {rel}")
        frozen = src.read_text(encoding="utf-8")
        generated = frozen.replace("res://", "res://hd2d_stage/")
        if generated.replace("res://hd2d_stage/", "res://") != frozen:
            raise SystemExit(f"stage_hd2d_assets: remap is not a res:// prefix for {rel}")
        dest = STAGE / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.is_symlink() or dest.exists():
            dest.unlink()
        dest.write_text(generated, encoding="utf-8")
        kind = "prefix" if generated != frozen else "identical"
        lines.append(
            f"{kind} {sha256(src)} {sha256(dest)} godot_hd2d_v6/{rel} hd2d_stage/{rel}"
        )
    PROVENANCE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    copied = 0
    for digest, rel in prerequisites():
        src = ROOT / rel
        if src.is_symlink() or not src.is_file():
            raise SystemExit(f"stage_hd2d_assets: need a regular file at {rel}")
        got = sha256(src)
        if got != digest:
            raise SystemExit(
                f"stage_hd2d_assets: hash mismatch for {rel}\n"
                f"  expected {digest}\n  actual   {got}"
            )
        dest = destination(rel)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.is_symlink() or dest.exists():
            dest.unlink()
        shutil.copyfile(src, dest)
        if dest.is_symlink() or not dest.is_file():
            raise SystemExit(f"stage_hd2d_assets: copy did not leave a regular file at {dest}")
        if sha256(dest) != digest:
            raise SystemExit(f"stage_hd2d_assets: copied bytes differ at {dest}")
        copied += 1
    assets = copy_assets()
    remap_scripts()
    print(
        f"stage_hd2d_assets: copied {copied} listed files, "
        f"{assets} exterior assets, {len(REMAP_SCRIPTS)} scripts, no symlinks"
    )


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(1)
