#!/usr/bin/env python3
"""vc26 r2: prove ALBEDO toe vs EMISSION bounce at night Mobile lighting (no GPU claim)."""
from __future__ import annotations

import math
import sys

# capture.gd night branch defaults (lights.json fallback)
SUN_E = 0.12
SUN_RGB = (0.55, 0.62, 0.85)
AMB_E = 0.35
AMB_RGB = (0.29, 0.35, 0.56)  # #4a5a90
NDOT_L = 0.72  # up-facing ground / tuft card normal
ALBEDO_DARK = 0.055  # typical crushed bake texel linear estimate

OLD_TOE_ALBEDO = 0.005
NEW_BOUNCE_EM = 0.018
DARK_GATE = 1.0
NIGHT_TOE_GAIN = 1.0
EXP = 1.35  # filmic tonemap exposure (capture _setup_environment night)


def lambert_rgb(albedo: float) -> tuple[float, float, float]:
    sun = tuple(SUN_E * NDOT_L * c * albedo for c in SUN_RGB)
    amb = tuple(AMB_E * c * albedo for c in AMB_RGB)
    return tuple(s + a for s, a in zip(sun, amb))


def luma(rgb: tuple[float, float, float]) -> float:
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def filmic_simple(linear: float) -> float:
    # crude Filmic + exposure proxy (not engine-identical; shows order of magnitude)
    x = max(0.0, linear * EXP)
    return x / (1.0 + x)


def main() -> int:
    base = lambert_rgb(ALBEDO_DARK)
    base_l = luma(base)
    bump_albedo = lambert_rgb(ALBEDO_DARK + OLD_TOE_ALBEDO * DARK_GATE * NIGHT_TOE_GAIN)
    bump_l = luma(bump_albedo)
    em = tuple(b + NEW_BOUNCE_EM * DARK_GATE * NIGHT_TOE_GAIN for b in base)
    em_l = luma(em)
    fb = filmic_simple(base_l)
    fb_b = filmic_simple(bump_l)
    fb_e = filmic_simple(em_l)
    ratio_bump = (bump_l - base_l) / max(base_l, 1e-6)
    ratio_em = (em_l - base_l) / max(base_l, 1e-6)
    print("night_lambert base_luma=", round(base_l, 5), "8bit≈", int(round(filmic_simple(base_l) * 255)))
    print(
        "albedo_toe delta_luma=", round(bump_l - base_l, 6),
        "relative=", round(ratio_bump * 100, 2), "%",
        "8bit_delta≈", int(round((fb_b - fb) * 255)),
    )
    print(
        "emission_bounce delta_luma=", round(em_l - base_l, 5),
        "relative=", round(ratio_em * 100, 1), "%",
        "8bit_delta≈", int(round((fb_e - fb) * 255)),
    )
    print("emission_vs_albedo_toe linear_gain=", round((em_l - base_l) / max(bump_l - base_l, 1e-9), 1), "x")
    ok = (em_l - base_l) > 10.0 * (bump_l - base_l) and (fb_e - fb) > 0.015
    print("algebra_pass=", ok, "(emission must dominate albedo-toe under night Lambert)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())