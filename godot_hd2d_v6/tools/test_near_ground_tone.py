#!/usr/bin/env python3
"""Asset-informed static checks for v0.6.18-pilot vc24 near-ground tone.

Run from the pilot root (textures optional via HD2D_MACRO_FIXTURE):
    python3 tools/test_near_ground_tone.py

Optional Godot 4.7 parse load (set GODOT_BIN or put godot4 on PATH):
    GODOT_BIN=godot4 python3 tools/test_near_ground_tone.py
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FG_WARM_D = (90.0, 210.0)
FG_WARM_LIT = 0.58
FGD_NEAR = 45.0


def read(rel: str) -> str:
    p = ROOT / rel
    if not p.is_file():
        raise SystemExit(f"missing {p}")
    return p.read_text(encoding="utf-8")


def must(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"FAIL {msg}")
    print(f"ok  {msg}")


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    if edge1 <= edge0:
        return 1.0 if x >= edge1 else 0.0
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def warm_k_shader(vr: float, r: float, g: float, b: float, fgd: float = FGD_NEAR) -> float:
    """Mirror near_lawn.gdshader v0.6.18 warm_k (fg_warm multiply weight)."""
    yel = max(g - r * 0.88, 0.0)
    dist = 1.0 - smoothstep(FG_WARM_D[0], FG_WARM_D[1], fgd)
    lit = smoothstep(FG_WARM_LIT, 0.84, vr)
    chroma = 1.0 - smoothstep(0.038, 0.11, yel)
    blue = smoothstep(0.085, 0.165, b)
    return dist * lit * chroma * blue


def macro_vr(r: int, g: int, b: int) -> float:
    macro_ref = (0.235, 0.29, 0.115)
    lw = (0.30, 0.59, 0.11)
    m = (r / 255.0, g / 255.0, b / 255.0)
    return sum(a * x for a, x in zip(m, lw)) / sum(a * x for a, x in zip(macro_ref, lw))


def load_macro_samples() -> list[tuple[float, float, float, float]]:
    macro_path = Path(
        os.environ.get(
            "HD2D_MACRO_FIXTURE",
            "/tmp/v618-assets/godot_hd2d_v6/textures/near_macro.png",
        )
    )
    if not macro_path.is_file():
        return []
    from PIL import Image  # type: ignore

    img = Image.open(macro_path).convert("RGBA")
    w, h = img.size
    region = (-340.0, -120.0, 340.0, 330.0)
    out: list[tuple[float, float, float, float]] = []
    for iz in range(0, h, 4):
        for ix in range(0, w, 4):
            wx = region[0] + (ix + 0.5) / w * (region[2] - region[0])
            wz = region[1] + (iz + 0.5) / h * (region[3] - region[1])
            if not (-100 <= wx <= 100 and -20 <= wz <= 130):
                continue
            r, g, b, _ = img.getpixel((ix, iz))
            rf, gf, bf = r / 255.0, g / 255.0, b / 255.0
            vr = macro_vr(r, g, b)
            out.append((vr, rf, gf, bf))
    return out


def line_has_invalid_c_comment(line: str) -> bool:
    """GDScript uses #; stray // (not res:// or ://) causes parse errors."""
    stripped = line.split("#", 1)[0]
    s = stripped.replace("res://", "\0").replace("://", "\0")
    return "//" in s


def audit_gdscript_comments() -> None:
    for rel in ("scenes/art_depth.gd", "scenes/capture.gd"):
        path = ROOT / rel
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line_has_invalid_c_comment(line):
                raise SystemExit(f"FAIL {rel}:{i} invalid GDScript // comment: {line.strip()!r}")


def try_godot_script_load() -> None:
    godot = os.environ.get("GODOT_BIN") or shutil.which("godot4") or shutil.which("godot")
    if not godot:
        print("    (skip godot parse — GODOT_BIN / godot4 not available)")
        return
    smoke = ROOT / "tools/gdscript_parse_smoke.gd"
    if not smoke.is_file():
        raise SystemExit("missing tools/gdscript_parse_smoke.gd")
    proc = subprocess.run(
        [godot, "--headless", "--path", str(ROOT), "--script", str(smoke)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    combined = (proc.stdout or "") + (proc.stderr or "")
    if re.search(r"Parse Error|Failed to load script", combined, re.I):
        raise SystemExit(f"FAIL godot reported script parse/load error:\n{combined[-4000:]}")
    if proc.returncode != 0:
        raise SystemExit(f"FAIL godot exit {proc.returncode}:\n{combined[-4000:]}")
    print("ok  godot headless loads art_depth.gd + capture.gd")


def main() -> None:
    t0 = time.perf_counter()
    sh = read("shaders/near_lawn.gdshader")
    art = read("scenes/art_depth.gd")
    proj = read("project.godot")
    cap = read("scenes/capture.gd")

    must('config/version="0.6.18-pilot"' in proj, "project version 0.6.18-pilot")
    must("0.6.18-pilot vc27" in cap, "capture labels vc27")
    must("hd2d v6.18-pilot vc27 start" in cap, "capture start marker vc27")
    must("art depth v6.18-pilot vc27 ready" in art, "art_depth boot string")
    must("perf v6.18-pilot vc27" in art, "art_depth perf marker vc27")
    must("emission*albedo" in art and "night_sky_rgb" in art, "vc27 sky×albedo wiring")
    must('\tif ev == "":\n\t\treturn 0.3\n' in art, "unset HD2D_NIGHT_TOE defaults to 0.3")
    must('if ev == "0":\n\t\treturn 0.0' in art, "HD2D_NIGHT_TOE=0 stays off")
    tex = read("shaders/texel_lit.gdshader")
    tuft = read("shaders/tuft.gdshader")
    must("night_alb * night_sky_rgb" in tex and "night_macro_on" in tex, "ground emission is albedo-modulated")
    must("night_own_grass" in tex and "night_outer_on" in tex and "vec3(0.0)" not in tex.split("if (night_toe_gain")[1].split("EMISSION = em")[0], "back ground keeps the outer grass, not a black fill")
    must("night_own_grass" in art and "GroundOuter" in art, "outer grass bound for the far ground")
    must("night_bounce_rgb" not in tex and "smoothstep(night_toe" not in tex, "no constant bounce or camera band on ground")
    must("_bind_night_ground" in art and "near_macro.png" in art.split("_apply_night_surface_toe")[1], "inner and outer share the macro handoff")
    must("ALBEDO * night_sky_rgb" in tuft and "smoothstep(0.45" not in tuft, "tuft sky×albedo, no root glow")
    must("ground_tex" in sh and "bl / max(blade_mean" in sh, "near night matches GroundInner bake")
    night = sh.split("if (fg_night_toe > 0.0 && night_toe_gain > 0.0)")[1].split("ALBEDO = alb;")[0]
    must("m.rgb" in night and "bake_w" in night and "discard" not in night, "foreground keeps macro past the bake")
    sim = subprocess.run([sys.executable, "tools/night_sky_albedo_sim.py"], capture_output=True, text=True, cwd=ROOT)
    must(sim.returncode == 0, "texture sim: " + (sim.stdout or sim.stderr))
    print((sim.stdout or "").strip())
    dap = read("shaders/ground_dapple.gdshader")
    must("uniform float speed = 1.15" in dap, "dapple drift slowed")
    must("0.65 * wind" in dap and "- drift * 0.25" in dap, "dapple layers stay coherent")
    must("static_amt" in dap and "cloud_at" in dap, "static tree shade and cloud modulation kept")
    must("diag_shader_time" not in dap, "production dapple has no diag uniform")
    audit_gdscript_comments()
    print("ok  no invalid // in patched GDScript")
    try_godot_script_load()
    must("uniform float fg_night_toe" in sh, "shader fg_night_toe uniform")
    must("uniform float fg_warm_lit" in sh, "shader fg_warm_lit gate")
    must("max(m.g - m.r * 0.88" in sh, "fg_warm chroma gate in shader")
    must("mix(vec3(1.0), fg_warm, warm_k)" in sh, "fg_warm gated by warm_k")
    must("0.0020, 0.0036, 0.0068" in sh, "conservative cool shade toe")
    must("fg_night_toe" in art and "fg_dim" in art, "art_depth drives night toe + fg_dim")
    must("HD2D_POOL_GAIN" not in sh and "HD2D_POOL_GAIN" in art, "pool gain stays art-side")
    must("smoothstep(0.038, 0.11, yel)" in sh, "yellow-green macro suppresses fg_warm")

    # Synthetic corners (not tautological with file reads)
    must(warm_k_shader(0.95, 50 / 255, 76 / 255, 29 / 255) < 0.05, "hero macro (lush yellow-green) blocks fg_warm")
    must(warm_k_shader(0.72, 40 / 255, 30 / 255, 45 / 255) > 0.35, "low-yel high-B macro may take fg_warm")
    must(warm_k_shader(0.90, 40 / 255, 30 / 255, 12 / 255) < 0.08, "olive-low-B pocket blocks fg_warm")
    must(warm_k_shader(0.85, 0.5, 0.5, 0.5, fgd=240.0) < 0.02, "far camera: no fg_warm")

    samples = load_macro_samples()
    if samples:
        wks = [warm_k_shader(vr, r, g, b) for vr, r, g, b in samples]
        wks.sort()
        med = wks[len(wks) // 2]
        p90 = wks[int(len(wks) * 0.9)]
        high_yel = [
            warm_k_shader(vr, r, g, b)
            for vr, r, g, b in samples
            if (g - r * 0.88) > 0.10
        ]
        must(len(high_yel) > 50, "macro fixture yields high-yel hero band samples")
        must(sum(1 for w in high_yel if w < 0.06) / len(high_yel) > 0.85, "≥85% high-yel macro pixels skip fg_warm")
        must(med < 0.12, f"macro walk band median warm_k={med:.3f} (was ~1.0 ungated v6.16)")
        must(p90 < 0.35, f"macro walk band p90 warm_k={p90:.3f}")
        print(f"    macro samples={len(samples)} med_wk={med:.3f} p90={p90:.3f}")
    else:
        print("    (skip macro fixture — set HD2D_MACRO_FIXTURE or unpack v618 textures)")

    print(f"passed in {time.perf_counter() - t0:.3f}s")


if __name__ == "__main__":
    main()