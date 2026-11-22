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
    print(f"stage_hd2d_assets: copied {copied} regular files, no symlinks")


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(1)
