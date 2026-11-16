#!/usr/bin/env python3
"""Compare vc26 r2 constant emission vs vc27 sky×albedo on the real ground bake.

Reads ground_composed_low.png (sRGB). Reconstructs the night EMISSION term only
(Lambert is ~0 on the crushed bottom). Prints B/G and spatial luma stdev.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = [
    ROOT / "textures" / "ground_composed_low.png",
    Path("/tmp/v618-assets/godot_hd2d_v6/textures/ground_composed_low.png"),
]
SKY = np.array([0.70, 0.92, 1.00], dtype=np.float64)
R2 = np.array([0.018, 0.022, 0.038], dtype=np.float64)


def srgb_to_linear(u8: np.ndarray) -> np.ndarray:
    c = u8.astype(np.float64) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def filmic_8(lin: np.ndarray) -> np.ndarray:
    x = np.clip(lin * 1.35, 0.0, None)
    y = x / (1.0 + x)
    return np.clip(np.round(y * 255.0), 0, 255)


def main() -> int:
    path = next((p for p in CANDIDATES if p.exists()), None)
    if path is None:
        print("missing ground_composed_low.png")
        return 1
    im = np.asarray(Image.open(path).convert("RGB"))
    lin = srgb_to_linear(im)
    # subsample
    lin = lin[::8, ::8]
    r2 = np.broadcast_to(R2, lin.shape)
    v27 = lin * SKY
    a = filmic_8(r2)
    b = filmic_8(v27)

    def stats(tag: str, img: np.ndarray, src: np.ndarray) -> tuple[float, float, float]:
        r, g, bl = img[..., 0], img[..., 1], img[..., 2]
        lum = 0.30 * r + 0.59 * g + 0.11 * bl
        bg = float(np.median(bl) / max(float(np.median(g)), 1.0))
        std = float(lum.std())
        # correlation of output G with source linear G (texture kept)
        corr = float(np.corrcoef(img[..., 1].ravel(), src[..., 1].ravel())[0, 1])
        print(f"{tag:18} med=({np.median(r):.0f},{np.median(g):.0f},{np.median(bl):.0f}) B/G={bg:.2f} lum_std={std:.1f} corrG={corr:.3f}")
        return bg, std, corr

    print("texture", path, "sample", lin.shape)
    bg_r, std_r, c_r = stats("vc26_r2_constant", a, lin)
    bg_v, std_v, c_v = stats("vc27_sky_x_albedo", b, lin)
    # black texel must stay dark: zero albedo → zero emission
    zero = filmic_8(np.zeros(3) * SKY)
    print("zero_albedo_8bit", zero.tolist())
    ok = bg_v < 1.0 and c_v > 0.95 and std_v > std_r * 1.5 and float(zero.max()) < 2.0 and bg_r > 1.2
    print("sim_pass", ok)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())