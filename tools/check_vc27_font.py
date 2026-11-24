#!/usr/bin/env python3
"""Every non-ASCII character in data, scripts, and scenes must be in both UI fonts."""
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
FONT_R = ROOT / "art/fonts/GenWanMin2TC-R.subset.otf"
FONT_SB = ROOT / "art/fonts/GenWanMin2TC-SB.subset.otf"
FONT_FB = ROOT / "art/fonts/vc27_label_fallback.otf"
DROID = Path("/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf")


def files() -> list[Path]:
    found: list[Path] = []
    data = ROOT / "data"
    if data.is_dir():
        found.extend(sorted(data.glob("*.json")))
    found.extend(sorted((ROOT / "scripts").rglob("*.gd")))
    found.extend(sorted((ROOT / "scenes").rglob("*.tscn")))
    return found


def wanted() -> set[str]:
    chars: set[str] = set()
    for path in files():
        text = path.read_text(encoding="utf-8", errors="replace")
        for ch in text:
            if ord(ch) > 127 and not ch.isspace():
                chars.add(ch)
    return chars


def cmap_of(path: Path) -> set[int]:
    font = TTFont(str(path))
    return set(font.getBestCmap() or {})


def report() -> int:
    need = wanted()
    have_r = cmap_of(FONT_R)
    have_sb = cmap_of(FONT_SB)
    have_fb = cmap_of(FONT_FB)
    miss_r = sorted(ch for ch in need if ord(ch) not in have_r and ord(ch) not in have_fb)
    miss_sb = sorted(ch for ch in need if ord(ch) not in have_sb and ord(ch) not in have_fb)
    missing = sorted(set(miss_r) | set(miss_sb))
    print("ALL_DATA_CMAP_CHECKED=%d" % len(need))
    print("ALL_DATA_CMAP_MISSING=%d" % len(missing))
    print("FONT_CMAP_CHECKED=%d" % len(need))
    print("FONT_CMAP_MISSING=%d" % len(missing))
    if missing:
        print("FONT_CMAP_MISSING_CHARS=%s" % "".join(missing))
        return 1
    return 0


def rebuild() -> int:
    need = wanted()
    have_r = cmap_of(FONT_R)
    have_sb = cmap_of(FONT_SB)
    # Keep every project character in the fallback itself. Godot walks that
    # chain from Font.has_char, and the subset fonts do not cover the new copy.
    extra = sorted(need)
    text = "".join(extra)
    out = ROOT / "tools" / "_vc27_fallback_chars.txt"
    out.write_text(text, encoding="utf-8")
    print("FALLBACK_CHARS=%d" % len(extra))
    if not extra:
        return 0
    from fontTools.subset import Subsetter, Options
    font = TTFont(str(DROID))
    opt = Options()
    opt.layout_features = ["*"]
    opt.glyph_names = True
    opt.symbol_cmap = True
    opt.legacy_cmap = True
    opt.notdef_glyph = True
    opt.notdef_outline = True
    opt.recommended_glyphs = True
    opt.name_IDs = ["*"]
    opt.name_legacy = True
    opt.name_languages = ["*"]
    subsetter = Subsetter(options=opt)
    subsetter.populate(text=text)
    subsetter.subset(font)
    font.save(str(FONT_FB))
    print("WROTE", FONT_FB)
    return report()


def main() -> int:
    if "--rebuild" in sys.argv:
        return rebuild()
    return report()


if __name__ == "__main__":
    sys.exit(main())
