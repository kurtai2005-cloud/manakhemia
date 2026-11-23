#!/usr/bin/env python3
"""Every UI and ecosystem-json character must exist in the packaged UI fonts."""
import re
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
FONTS = [
    ROOT / "art/fonts/GenWanMin2TC-R.subset.otf",
    ROOT / "art/fonts/GenWanMin2TC-SB.subset.otf",
    ROOT / "art/fonts/vc27_label_fallback.otf",
]
SOURCES = [ROOT / "scripts", ROOT / "data/ecosystem_v1.json"]


def wanted() -> set[str]:
    chars: set[str] = set()
    files = []
    for src in SOURCES:
        if src.is_dir():
            files.extend(src.rglob("*.gd"))
        elif src.is_file():
            files.append(src)
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        for ch in text:
            o = ord(ch)
            if o < 128 and ch not in "·（）：，。、「」！？":
                continue
            if ch.isspace():
                continue
            # CJK, fullwidth, and the punctuation that rides with Chinese labels.
            if o >= 0x2E80 or ch in "·（）：，。、「」！？":
                chars.add(ch)
    return chars


def cmap_of(path: Path) -> set[int]:
    font = TTFont(str(path))
    cmap = font.getBestCmap() or {}
    return set(cmap)


def main() -> int:
    need = wanted()
    have: set[int] = set()
    for path in FONTS:
        have |= cmap_of(path)
    missing = sorted(ch for ch in need if ord(ch) not in have)
    print("FONT_CMAP_CHECKED=%d" % len(need))
    print("FONT_CMAP_MISSING=%d" % len(missing))
    if missing:
        print("FONT_CMAP_MISSING_CHARS=%s" % "".join(missing))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
