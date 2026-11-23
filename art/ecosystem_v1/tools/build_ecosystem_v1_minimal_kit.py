#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the 微光小圃 ecosystem v1 minimal-readable art kit (offline Pillow only)."""
from __future__ import annotations

import hashlib
import json
import math
import os
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont
from PIL.PngImagePlugin import PngInfo

ROOT = Path("/home/box/keep/godot/hd2d-pilot-v6/ecosystem_v1_minimal_kit")
SERIES2 = Path("/workspace/s2art/art-pet/sprites/series2")
SS = 4  # supersample
CATEGORY = "minimal_readable_draft"
COMMENT = "minimal_readable_draft | 微光小圃 活生態圈 v1 | not final 675 polish"

# --- palette (warm, aligned with 675 tuanrong creams / ink) ---
INK = (59, 42, 62, 255)
INK_SOFT = (59, 42, 62, 180)
CREAM = (255, 248, 224, 255)
CREAM2 = (255, 239, 196, 255)
PAPER = (247, 236, 210, 255)
GOLD = (255, 212, 94, 255)
GOLD_D = (232, 168, 58, 255)
SAND = (233, 190, 132, 255)
PEACH = (242, 166, 90, 255)
CORAL = (224, 127, 69, 255)
ORANGE = (255, 138, 61, 255)
PINK = (242, 139, 155, 255)
ROSE = (196, 86, 110, 255)
WOOD = (155, 102, 55, 255)
WOOD_M = (124, 78, 40, 255)
WOOD_D = (92, 58, 30, 255)
WOOD_L = (196, 148, 92, 255)
LEAF_L = (154, 204, 118, 255)
LEAF = (92, 160, 86, 255)
LEAF_D = (47, 106, 58, 255)
MOSS = (62, 92, 54, 255)
SOIL = (132, 86, 52, 255)
SOIL_D = (96, 62, 38, 255)
SOIL_L = (168, 118, 72, 255)
TEAL_L = (143, 203, 196, 255)
TEAL = (74, 158, 158, 255)
TEAL_D = (40, 100, 110, 255)
SKY = (143, 203, 217, 255)
BLUE = (74, 130, 186, 255)
NAVY = (46, 78, 122, 255)
PURPLE = (132, 110, 186, 255)
LAV = (186, 168, 216, 255)
WHITE = (255, 255, 255, 255)
SHADOW = (40, 28, 22, 70)

FONT_REG = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_IDX = 4  # Noto Sans CJK HK


def font(size, bold=False):
    path = FONT_BOLD if bold else FONT_REG
    return ImageFont.truetype(path, size, index=FONT_IDX)


def rgba(c, a=None):
    if a is None:
        return tuple(c) if len(c) == 4 else (*c[:3], 255)
    return (*c[:3], int(a))


def lerp_c(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3)) + (int(a[3] + (b[3] - a[3]) * t) if len(a) > 3 else 255,)


def resize_premul(im: Image.Image, size) -> Image.Image:
    src = im.convert("RGBA")
    arr = np.array(src).astype(np.float32)
    a = arr[..., 3:4] / 255.0
    arr[..., :3] *= a
    premul = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
    out = premul.resize(size, Image.Resampling.LANCZOS)
    arr = np.array(out).astype(np.float32)
    a = arr[..., 3:4]
    arr[..., :3] = np.divide(arr[..., :3], a / 255.0, out=np.zeros_like(arr[..., :3]), where=a > 0.5)
    arr[..., 3] = np.clip(a[..., 0], 0, 255)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")


def canvas(w, h):
    return Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))


def down(im, w, h):
    return resize_premul(im, (w, h))


def paste(dst, src, xy=(0, 0)):
    if src.mode != "RGBA":
        src = src.convert("RGBA")
    dst.alpha_composite(src, dest=xy)


def layer(size):
    return Image.new("RGBA", size, (0, 0, 0, 0))


def draw_of(im):
    return ImageDraw.Draw(im, "RGBA")


def ellipse(draw, cx, cy, rx, ry, fill=None, outline=None, width=0):
    box = [cx - rx, cy - ry, cx + rx, cy + ry]
    if fill is not None:
        draw.ellipse(box, fill=fill)
    if outline is not None and width > 0:
        draw.ellipse(box, outline=outline, width=width)


def rrect(draw, box, rad, fill=None, outline=None, width=0):
    draw.rounded_rectangle(box, radius=rad, fill=fill, outline=outline, width=width)


def line(draw, pts, fill, width, joint="curve"):
    draw.line(pts, fill=fill, width=width, joint=joint)


def poly(draw, pts, fill=None, outline=None):
    draw.polygon(pts, fill=fill, outline=outline)


def soft_shadow(size, box, rad, color=SHADOW, blur=6):
    im = layer(size)
    d = draw_of(im)
    rrect(d, box, rad, fill=color)
    return im.filter(ImageFilter.GaussianBlur(blur * SS / 4))


def soft_ellipse_shadow(size, cx, cy, rx, ry, color=SHADOW, blur=8):
    im = layer(size)
    d = draw_of(im)
    ellipse(d, cx, cy, rx, ry, fill=color)
    return im.filter(ImageFilter.GaussianBlur(blur * SS / 4))


def stroke_ellipse(dst, cx, cy, rx, ry, fill, outline, width):
    d = draw_of(dst)
    ellipse(d, cx, cy, rx, ry, fill=fill, outline=outline, width=width)


def stroke_alpha(src, color=INK, radius=None):
    """Clean outline by dilating alpha (avoids PIL thick-line sawtooth on diagonals)."""
    if radius is None:
        radius = int(1.7 * SS)
    k = radius * 2 + 1
    if k % 2 == 0:
        k += 1
    a = src.split()[3]
    dilated = a.filter(ImageFilter.MaxFilter(k))
    # slight blur for AA of the ring
    ring = ImageChops.subtract(dilated, a)
    ring = ring.filter(ImageFilter.GaussianBlur(SS * 0.35))
    stroke = Image.new("RGBA", src.size, color)
    stroke.putalpha(ring)
    out = Image.new("RGBA", src.size, (0, 0, 0, 0))
    paste(out, stroke)
    paste(out, src)
    return out


def disk_plate(im, cx, cy, r, fill=CREAM, rim=WOOD_M, rim_w=None, shadow=True):
    """Soft circular / rounded-square badge used by 64px icons."""
    W, H = im.size
    if shadow:
        paste(im, soft_ellipse_shadow((W, H), cx, cy + int(2.5 * SS), r * 1.02, r * 0.38, (40, 28, 22, 80), 5))
    d = draw_of(im)
    rw = rim_w if rim_w is not None else max(2 * SS, int(r * 0.08))
    # slightly rounded square plate (reads better at 20px than a thin ring)
    box = [cx - r, cy - r, cx + r, cy + r]
    rrect(d, box, int(r * 0.32), fill=fill, outline=rim, width=rw)
    # inner highlight
    rrect(d, [cx - r + rw, cy - r + rw, cx + r - rw, cy - r + r * 0.45], int(r * 0.22), fill=rgba(WHITE, 55))


def teardrop_pts(cx, cy, rx, ry, tip_down=True):
    pts = []
    for i in range(24):
        t = i / 23
        ang = math.pi * (0.15 + 0.70 * t)  # upper bulb
        if not tip_down:
            ang = -ang
        pts.append((cx + rx * math.cos(ang), cy - ry * 0.25 + ry * 0.75 * math.sin(ang)))
    # tip
    if tip_down:
        pts.append((cx, cy + ry))
    else:
        pts.append((cx, cy - ry))
    return pts


def star_pts(cx, cy, r_out, r_in, n=5, rot=-math.pi / 2):
    pts = []
    for i in range(n * 2):
        r = r_out if i % 2 == 0 else r_in
        a = rot + i * math.pi / n
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def heart_pts(cx, cy, w, h):
    pts = []
    for i in range(40):
        t = math.pi * 2 * i / 40
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((cx + x / 16.0 * (w / 2), cy - y / 17.0 * (h / 2)))
    return pts


def crescent_mask(size, cx, cy, r, cut_cx, cut_cy, cut_r):
    m = Image.new("L", size, 0)
    d = ImageDraw.Draw(m)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    d.ellipse([cut_cx - cut_r, cut_cy - cut_r, cut_cx + cut_r, cut_cy + cut_r], fill=0)
    return m


def fill_mask(size, mask, color):
    im = layer(size)
    im.paste(color, mask=mask)
    return im


def measure_opaque(im: Image.Image):
    a = np.array(im.convert("RGBA"))[..., 3]
    ys, xs = np.where(a > 0)
    if len(xs) == 0:
        return {"empty": True}
    solid = np.where(a >= 128)
    last_y = int(ys.max())
    last_solid = int(solid[0].max()) if solid[0].size else last_y
    first_y = int(ys.min())
    first_x, last_x = int(xs.min()), int(xs.max())
    return {
        "empty": False,
        "bbox": [first_x, first_y, last_x, last_y],
        "last_opaque_row": last_y,
        "last_solid_row": last_solid,
        "sole_edge": last_y + 1,
        "first_opaque_row": first_y,
        "center_x": (first_x + last_x) / 2.0,
        "anchor_px": [round((first_x + last_x) / 2.0, 2), last_y],
    }


def save_png(im, path: Path, meta_title: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    info = PngInfo()
    info.add_text("Title", meta_title)
    info.add_text("Comment", COMMENT)
    info.add_text("Software", "ecosystem_v1_minimal_kit / Pillow")
    info.add_text("Category", CATEGORY)
    im.convert("RGBA").save(path, "PNG", pnginfo=info)
    return path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()

# ---------------------------------------------------------------------------
# 64x64 icons
# ---------------------------------------------------------------------------

def icon_base(hue_fill=CREAM, rim=WOOD_M):
    im = canvas(64, 64)
    cx = cy = 32 * SS
    disk_plate(im, cx, cy, 26 * SS, fill=hue_fill, rim=rim, rim_w=2 * SS)
    return im


def draw_icon_stat_power():
    # Warm stone / clenched paw — strength. Cream plate, terracotta paw, gold spark.
    im = icon_base((255, 244, 220, 255), (140, 78, 42, 255))
    d = draw_of(im)
    cx, cy = 32 * SS, 34 * SS
    # paw body
    ellipse(d, cx, cy + 1 * SS, 11.5 * SS, 9.5 * SS, fill=CORAL, outline=INK, width=2 * SS)
    # toes
    for dx, dy, r in [(-9, -7, 3.4), (-3.2, -10, 3.6), (3.2, -10, 3.6), (9, -7, 3.4)]:
        ellipse(d, cx + dx * SS, cy + dy * SS, r * SS, r * SS, fill=PEACH, outline=INK, width=int(1.6 * SS))
    # pad highlight
    ellipse(d, cx - 2 * SS, cy + 1 * SS, 5 * SS, 3.6 * SS, fill=rgba(WHITE, 80))
    # gold spark top-right (readable chevron burst)
    sx, sy = 46 * SS, 18 * SS
    poly(d, star_pts(sx, sy, 5.2 * SS, 2.2 * SS, 4, -math.pi / 4), fill=GOLD, outline=INK, )
    # reinforce star outline
    d.polygon(star_pts(sx, sy, 5.2 * SS, 2.2 * SS, 4, -math.pi / 4), outline=INK)
    d.line(star_pts(sx, sy, 5.2 * SS, 2.2 * SS, 4, -math.pi / 4) + [star_pts(sx, sy, 5.2 * SS, 2.2 * SS, 4, -math.pi / 4)[0]], fill=INK, width=max(SS, 3))
    return down(im, 64, 64)


def draw_icon_stat_agility():
    # Two motion crescents + dart tip.
    im = icon_base((232, 246, 236, 255), (40, 110, 100, 255))
    d = draw_of(im)
    # back swoosh
    d.arc([12 * SS, 18 * SS, 44 * SS, 50 * SS], start=200, end=40, fill=TEAL_D, width=int(4.2 * SS))
    d.arc([14 * SS, 20 * SS, 42 * SS, 48 * SS], start=200, end=40, fill=TEAL, width=int(3.2 * SS))
    # front swoosh
    d.arc([18 * SS, 14 * SS, 52 * SS, 46 * SS], start=200, end=30, fill=INK, width=int(4.4 * SS))
    d.arc([20 * SS, 16 * SS, 50 * SS, 44 * SS], start=200, end=30, fill=GOLD_D, width=int(3.2 * SS))
    d.arc([21 * SS, 17 * SS, 49 * SS, 43 * SS], start=210, end=20, fill=GOLD, width=int(1.8 * SS))
    # dart head at tip
    tip_x, tip_y = 48.5 * SS, 20 * SS
    poly(d, [(tip_x + 6 * SS, tip_y - 4 * SS), (tip_x + 1 * SS, tip_y + 6 * SS), (tip_x - 7 * SS, tip_y + 1 * SS)], fill=GOLD, outline=INK)
    d.polygon([(tip_x + 6 * SS, tip_y - 4 * SS), (tip_x + 1 * SS, tip_y + 6 * SS), (tip_x - 7 * SS, tip_y + 1 * SS)], outline=INK)
    d.line([(tip_x + 6 * SS, tip_y - 4 * SS), (tip_x + 1 * SS, tip_y + 6 * SS), (tip_x - 7 * SS, tip_y + 1 * SS), (tip_x + 6 * SS, tip_y - 4 * SS)], fill=INK, width=max(2, int(1.5 * SS)))
    return down(im, 64, 64)


def draw_icon_stat_stamina():
    # Sturdy heart + leaf vein.
    im = icon_base((255, 242, 228, 255), (140, 70, 55, 255))
    d = draw_of(im)
    pts = heart_pts(32 * SS, 33 * SS, 28 * SS, 24 * SS)
    poly(d, pts, fill=CORAL)
    d.line(pts + [pts[0]], fill=INK, width=int(2.1 * SS), joint="curve")
    # inner highlight heart
    pts2 = heart_pts(32 * SS, 32.2 * SS, 16 * SS, 13.5 * SS)
    poly(d, pts2, fill=rgba(GOLD, 200))
    # leaf vein
    d.line([(32 * SS, 24 * SS), (32 * SS, 42 * SS)], fill=INK, width=int(1.6 * SS))
    d.line([(32 * SS, 30 * SS), (26 * SS, 35 * SS)], fill=INK, width=SS)
    d.line([(32 * SS, 30 * SS), (38 * SS, 35 * SS)], fill=INK, width=SS)
    return down(im, 64, 64)


def _zone_icon(plate, rim, painter):
    im = icon_base(plate, rim)
    painter(im, draw_of(im))
    return down(im, 64, 64)


def draw_icon_zone_garden():
    def p(im, d):
        # grass clumps + flower
        for dx, w in [(-10, 7), (0, 8), (10, 7)]:
            ellipse(d, (32 + dx) * SS, 42 * SS, w * SS, 4.2 * SS, fill=LEAF_D)
        # blades
        for x, h in [(22, 8), (26, 12), (30, 9), (34, 13), (38, 8), (42, 11)]:
            d.line([(x * SS, 42 * SS), (x * SS, (42 - h) * SS)], fill=LEAF, width=int(1.8 * SS))
        # flower
        cx, cy = 32 * SS, 24 * SS
        for i in range(5):
            a = -math.pi / 2 + i * 2 * math.pi / 5
            ellipse(d, cx + 6.2 * SS * math.cos(a), cy + 5.6 * SS * math.sin(a), 4.2 * SS, 4.2 * SS, fill=PINK, outline=INK, width=SS)
        ellipse(d, cx, cy, 3.4 * SS, 3.4 * SS, fill=GOLD, outline=INK, width=SS)
    return _zone_icon((236, 250, 230, 255), LEAF_D, p)


def draw_icon_zone_cottage_yard_work():
    def p(im, d):
        # little house
        body = [18 * SS, 30 * SS, 46 * SS, 48 * SS]
        rrect(d, body, 2 * SS, fill=SAND, outline=INK, width=int(1.8 * SS))
        roof = [(16 * SS, 31 * SS), (32 * SS, 16 * SS), (48 * SS, 31 * SS)]
        poly(d, roof, fill=CORAL)
        d.line(roof + [roof[0]], fill=INK, width=int(1.8 * SS), joint="curve")
        # door
        rrect(d, [29 * SS, 36 * SS, 35 * SS, 48 * SS], 1 * SS, fill=WOOD_D, outline=INK, width=SS)
        # window
        rrect(d, [20 * SS, 35 * SS, 26 * SS, 41 * SS], 1 * SS, fill=SKY, outline=INK, width=SS)
        # small work table to the right-front
        rrect(d, [40 * SS, 42 * SS, 52 * SS, 48 * SS], 1 * SS, fill=WOOD, outline=INK, width=SS)
        # pot on table
        ellipse(d, 46 * SS, 40 * SS, 3.2 * SS, 2.4 * SS, fill=TEAL_D, outline=INK, width=SS)
    return _zone_icon((255, 242, 224, 255), WOOD_D, p)


def draw_icon_zone_prairie_edge():
    def p(im, d):
        # horizon hill
        d.pieslice([8 * SS, 26 * SS, 56 * SS, 54 * SS], start=200, end=340, fill=LEAF, outline=INK, width=int(1.6 * SS))
        d.pieslice([20 * SS, 30 * SS, 62 * SS, 56 * SS], start=200, end=340, fill=LEAF_L, outline=INK, width=int(1.4 * SS))
        # grass tufts at edge
        for x in (16, 22, 28, 34, 40, 46):
            d.line([(x * SS, 44 * SS), ((x - 1.5) * SS, 34 * SS)], fill=LEAF_D, width=int(1.6 * SS))
            d.line([(x * SS, 44 * SS), ((x + 1.8) * SS, 33 * SS)], fill=LEAF, width=int(1.6 * SS))
        # small sun
        ellipse(d, 46 * SS, 20 * SS, 5 * SS, 5 * SS, fill=GOLD, outline=INK, width=SS)
    return _zone_icon((255, 248, 220, 255), (110, 130, 50, 255), p)


def draw_icon_zone_farm():
    def p(im, d):
        # isometric plot
        cx, cy = 32 * SS, 38 * SS
        rw, rd = 18 * SS, 9 * SS
        top = [(cx, cy - rd), (cx + rw, cy), (cx, cy + rd), (cx - rw, cy)]
        poly(d, top, fill=SOIL)
        d.line(top + [top[0]], fill=INK, width=int(1.8 * SS), joint="curve")
        # furrows
        d.line([(cx - 8 * SS, cy - 2 * SS), (cx + 8 * SS, cy + 6 * SS)], fill=SOIL_D, width=SS)
        d.line([(cx - 4 * SS, cy - 5 * SS), (cx + 10 * SS, cy + 2 * SS)], fill=SOIL_D, width=SS)
        # sprout
        d.line([(cx, cy - 2 * SS), (cx, cy - 16 * SS)], fill=LEAF_D, width=int(2 * SS))
        ellipse(d, cx - 5 * SS, cy - 16 * SS, 5 * SS, 3.2 * SS, fill=LEAF, outline=INK, width=SS)
        ellipse(d, cx + 5.5 * SS, cy - 14 * SS, 5 * SS, 3.2 * SS, fill=LEAF_L, outline=INK, width=SS)
    return _zone_icon((255, 240, 220, 255), SOIL_D, p)


def draw_icon_zone_workshop():
    def p(im, d):
        # workbench
        rrect(d, [14 * SS, 36 * SS, 50 * SS, 48 * SS], 2 * SS, fill=WOOD, outline=INK, width=int(1.8 * SS))
        # legs
        d.rectangle([17 * SS, 48 * SS, 21 * SS, 52 * SS], fill=WOOD_D, outline=INK, width=SS)
        d.rectangle([43 * SS, 48 * SS, 47 * SS, 52 * SS], fill=WOOD_D, outline=INK, width=SS)
        # stove / pot
        rrect(d, [20 * SS, 24 * SS, 34 * SS, 37 * SS], 2 * SS, fill=(110, 96, 92, 255), outline=INK, width=int(1.6 * SS))
        ellipse(d, 27 * SS, 24 * SS, 7 * SS, 3 * SS, fill=(80, 70, 68, 255), outline=INK, width=SS)
        # hammer
        d.line([(38 * SS, 34 * SS), (48 * SS, 18 * SS)], fill=WOOD_D, width=int(2.2 * SS))
        rrect(d, [44 * SS, 14 * SS, 54 * SS, 22 * SS], 1 * SS, fill=(150, 150, 158, 255), outline=INK, width=SS)
        # small spark
        ellipse(d, 24 * SS, 20 * SS, 2 * SS, 2 * SS, fill=GOLD)
    return _zone_icon((255, 236, 214, 255), WOOD_D, p)


def draw_icon_zone_prairie_deep():
    def p(im, d):
        # deeper darker hills
        d.pieslice([6 * SS, 22 * SS, 50 * SS, 58 * SS], start=200, end=340, fill=MOSS, outline=INK, width=int(1.6 * SS))
        d.pieslice([18 * SS, 28 * SS, 62 * SS, 60 * SS], start=200, end=340, fill=LEAF_D, outline=INK, width=int(1.4 * SS))
        # tall grass
        for x, h, col in [(16, 18, LEAF), (21, 22, LEAF_L), (26, 16, LEAF), (32, 24, LEAF_L), (38, 18, LEAF), (44, 21, LEAF_D), (49, 15, LEAF)]:
            d.line([(x * SS, 46 * SS), ((x - 2) * SS, (46 - h) * SS)], fill=col, width=int(1.8 * SS))
        # two small fireflies (not a sun)
        for fx, fy in ((42 * SS, 20 * SS), (50 * SS, 28 * SS)):
            ellipse(d, fx, fy, 5.5 * SS, 5.5 * SS, fill=rgba(GOLD, 55))
            ellipse(d, fx, fy, 2.0 * SS, 2.0 * SS, fill=GOLD, outline=INK, width=max(2, SS))
    return _zone_icon((214, 232, 220, 255), (30, 70, 60, 255), p)


def draw_icon_zone_family_wall():
    def p(im, d):
        # wall board
        rrect(d, [14 * SS, 18 * SS, 50 * SS, 48 * SS], 3 * SS, fill=WOOD_L, outline=INK, width=int(1.8 * SS))
        # two frames
        rrect(d, [18 * SS, 22 * SS, 30 * SS, 36 * SS], 1 * SS, fill=CREAM, outline=INK, width=int(1.6 * SS))
        rrect(d, [33 * SS, 22 * SS, 45 * SS, 36 * SS], 1 * SS, fill=CREAM, outline=INK, width=int(1.6 * SS))
        # tiny hearts
        poly(d, heart_pts(24 * SS, 29 * SS, 7 * SS, 6 * SS), fill=PINK)
        poly(d, heart_pts(39 * SS, 29 * SS, 7 * SS, 6 * SS), fill=GOLD)
        # lower rail
        d.rectangle([16 * SS, 40 * SS, 48 * SS, 44 * SS], fill=WOOD, outline=INK, width=SS)
    return _zone_icon((255, 240, 228, 255), ROSE, p)


# ---------------------------------------------------------------------------
# UI chrome
# ---------------------------------------------------------------------------

PILL_SLICE = {"left": 28, "top": 12, "right": 28, "bottom": 12, "keep_height_px": 56}


def _draw_pill(fill, rim, rim_w=3, inner_glow=None, highlight=True):
    w, h = 160, 56
    im = canvas(w, h)
    d = draw_of(im)
    rad = (h // 2) * SS
    box = [2 * SS, 2 * SS, (w - 2) * SS, (h - 2) * SS]
    # drop shadow
    paste(im, soft_shadow(im.size, [3 * SS, 5 * SS, (w - 1) * SS, (h - 1) * SS], rad, (40, 28, 22, 70), 4))
    rrect(d, box, rad, fill=fill, outline=rim, width=rim_w * SS)
    if highlight:
        rrect(d, [6 * SS, 4 * SS, (w - 6) * SS, 20 * SS], (10 * SS), fill=rgba(WHITE, 70))
    if inner_glow:
        glow = layer(im.size)
        gd = draw_of(glow)
        rrect(gd, [4 * SS, 4 * SS, (w - 4) * SS, (h - 4) * SS], rad - 2 * SS, outline=inner_glow, width=2 * SS)
        paste(im, glow.filter(ImageFilter.GaussianBlur(2 * SS)))
        # crisp inner rim
        rrect(d, [5 * SS, 5 * SS, (w - 5) * SS, (h - 5) * SS], rad - 3 * SS, outline=inner_glow, width=SS)
    return down(im, w, h)


def draw_ui_zone_pill_bg():
    return _draw_pill(PAPER, WOOD_M, rim_w=3, highlight=True)


def draw_ui_zone_pill_active():
    return _draw_pill((255, 246, 214, 255), GOLD_D, rim_w=4, inner_glow=GOLD, highlight=True)


def _portrait_frame(active=False):
    im = canvas(64, 64)
    d = draw_of(im)
    # outer
    fill = GOLD if active else WOOD
    rim = GOLD_D if active else WOOD_D
    paste(im, soft_shadow(im.size, [4 * SS, 6 * SS, 60 * SS, 62 * SS], 10 * SS, (40, 28, 22, 80), 4))
    rrect(d, [3 * SS, 3 * SS, 61 * SS, 61 * SS], 10 * SS, fill=fill, outline=INK, width=int(1.8 * SS))
    # inner wood lip
    inner_fill = CREAM2 if not active else (255, 250, 220, 255)
    rrect(d, [10 * SS, 10 * SS, 54 * SS, 54 * SS], 6 * SS, fill=inner_fill, outline=INK, width=int(1.5 * SS))
    # punch a transparent viewing hole
    hole = Image.new("L", im.size, 0)
    hd = ImageDraw.Draw(hole)
    hd.rounded_rectangle([14 * SS, 14 * SS, 50 * SS, 50 * SS], radius=5 * SS, fill=255)
    # apply hole: set alpha to 0 inside
    arr = np.array(im)
    m = np.array(hole)
    arr[m == 255, 3] = 0
    im = Image.fromarray(arr, "RGBA")
    if active:
        # soft gold halo around frame (outside the hole)
        glow = layer((64 * SS, 64 * SS))
        gd = draw_of(glow)
        rrect(gd, [1 * SS, 1 * SS, 63 * SS, 63 * SS], 12 * SS, outline=rgba(GOLD, 160), width=3 * SS)
        glow = glow.filter(ImageFilter.GaussianBlur(2 * SS))
        # don't fill the hole with glow
        garr = np.array(glow)
        garr[m == 255, 3] = 0
        glow = Image.fromarray(garr, "RGBA")
        base = Image.new("RGBA", im.size, (0, 0, 0, 0))
        paste(base, glow)
        paste(base, im)
        im = base
    return down(im, 64, 64)


def draw_ui_pet_portrait_frame():
    return _portrait_frame(False)


def draw_ui_pet_portrait_frame_active():
    return _portrait_frame(True)

# ---------------------------------------------------------------------------
# Props (128 / 192 / 48) — 3/4 view, ground-centered
# ---------------------------------------------------------------------------

def iso_pts(cx, cy, rw, rd):
    return [(cx, cy - rd), (cx + rw, cy), (cx, cy + rd), (cx - rw, cy)]


def iso_box(d, cx, cy, rw, rd, thick, top, side_l, side_r, outline=INK, ow=None, dest_im=None):
    """Draw a simple isometric slab. cy is the top-face center.
    If dest_im is given, faces are composed with a clean morphological outline."""
    ow = ow if ow is not None else int(1.6 * SS)
    top_pts = iso_pts(cx, cy, rw, rd)
    left = [top_pts[3], top_pts[2], (top_pts[2][0], top_pts[2][1] + thick), (top_pts[3][0], top_pts[3][1] + thick)]
    right = [top_pts[1], top_pts[2], (top_pts[2][0], top_pts[2][1] + thick), (top_pts[1][0], top_pts[1][1] + thick)]
    if dest_im is not None:
        tmp = layer(dest_im.size)
        td = draw_of(tmp)
        poly(td, left, fill=side_l)
        poly(td, right, fill=side_r)
        poly(td, top_pts, fill=top)
        tmp = stroke_alpha(tmp, outline, max(int(ow), int(1.5 * SS)))
        paste(dest_im, tmp)
    else:
        poly(d, left, fill=side_l)
        poly(d, right, fill=side_r)
        poly(d, top_pts, fill=top)
        d.line(top_pts + [top_pts[0]], fill=outline, width=ow, joint="curve")
        d.line(left, fill=outline, width=ow, joint="curve")
        d.line(right, fill=outline, width=ow, joint="curve")
    return top_pts


def ground_shadow(im, cx, cy, rx, ry, alpha=80):
    paste(im, soft_ellipse_shadow(im.size, cx, cy, rx, ry, (40, 28, 22, alpha), 6))


def draw_farm_plot(stage=0):
    """stage 0 empty, 1 sprout, 2 growing, 3 ripe. Complete drop-in prop including plot."""
    im = canvas(128, 128)
    d = draw_of(im)
    cx, cy = 64 * SS, 78 * SS
    rw, rd, thick = 44 * SS, 22 * SS, 10 * SS
    ground_shadow(im, cx, cy + thick + 4 * SS, 42 * SS, 14 * SS, 90)
    # wooden border slab slightly larger
    iso_box(d, cx, cy + 1 * SS, rw + 6 * SS, rd + 3 * SS, thick + 2 * SS,
            top=WOOD, side_l=WOOD_D, side_r=WOOD_M, ow=int(1.8 * SS), dest_im=im)
    # soil top
    iso_box(d, cx, cy - 2 * SS, rw - 4 * SS, rd - 2 * SS, 6 * SS,
            top=SOIL, side_l=SOIL_D, side_r=(110, 72, 44, 255), ow=int(1.5 * SS), dest_im=im)
    # furrows
    for i, t in enumerate((0.25, 0.5, 0.75)):
        x0 = cx + (-rw + 10 * SS) * (1 - t) + (0) * t
        # diagonal furrow along depth
        p1 = (cx - (rw - 10 * SS) + i * 12 * SS, cy - 2 * SS)
        p2 = (cx - 8 * SS + i * 12 * SS, cy + rd - 8 * SS)
        if i < 3:
            d.line([ (cx - 22 * SS + i * 14 * SS, cy - 6 * SS),
                     (cx + 8 * SS + i * 10 * SS, cy + 10 * SS) ], fill=SOIL_D, width=int(1.4 * SS))
    if stage == 0:
        # empty — slightly darker seed holes
        for dx, dy in [(-12, -2), (4, 4), (16, -4)]:
            ellipse(d, cx + dx * SS, cy + dy * SS, 3 * SS, 1.6 * SS, fill=SOIL_D)
        return down(im, 128, 128)

    def leaf(x, y, rx, ry, ang_deg, col=LEAF):
        # simple leaf ellipse rotated via a small temp layer
        lw, lh = int(rx * 2 + 8 * SS), int(ry * 2 + 8 * SS)
        tmp = layer((lw, lh))
        td = draw_of(tmp)
        ellipse(td, lw / 2, lh / 2, rx, ry, fill=col, outline=INK, width=max(SS, int(1.2 * SS)))
        tmp = tmp.rotate(-ang_deg, resample=Image.Resampling.BICUBIC, expand=True)
        paste(im, tmp, (int(x - tmp.size[0] / 2), int(y - tmp.size[1] / 2)))

    def stem(x1, y1, x2, y2, w=2.2):
        d.line([(x1, y1), (x2, y2)], fill=LEAF_D, width=int(w * SS))

    if stage == 1:
        # tiny sprout
        bx, by = cx + 2 * SS, cy - 4 * SS
        stem(bx, by, bx, by - 16 * SS, 2.0)
        leaf(bx - 7 * SS, by - 16 * SS, 8 * SS, 4.5 * SS, 35, LEAF)
        leaf(bx + 8 * SS, by - 14 * SS, 7.5 * SS, 4.2 * SS, -30, LEAF_L)
    elif stage == 2:
        bx, by = cx + 2 * SS, cy - 4 * SS
        stem(bx, by, bx, by - 34 * SS, 2.6)
        # side stems
        stem(bx, by - 16 * SS, bx - 14 * SS, by - 28 * SS, 1.8)
        stem(bx, by - 18 * SS, bx + 16 * SS, by - 30 * SS, 1.8)
        leaf(bx - 16 * SS, by - 30 * SS, 11 * SS, 6 * SS, 40, LEAF)
        leaf(bx + 18 * SS, by - 32 * SS, 12 * SS, 6.2 * SS, -38, LEAF_L)
        leaf(bx - 6 * SS, by - 40 * SS, 10 * SS, 5.5 * SS, 20, LEAF)
        leaf(bx + 8 * SS, by - 42 * SS, 10 * SS, 5.5 * SS, -18, LEAF_L)
        leaf(bx + 2 * SS, by - 28 * SS, 8 * SS, 4.5 * SS, 8, LEAF)
    else:
        # ripe bush with warm fruits
        bx, by = cx + 2 * SS, cy - 4 * SS
        stem(bx, by, bx, by - 36 * SS, 3.0)
        stem(bx, by - 14 * SS, bx - 18 * SS, by - 30 * SS, 2.0)
        stem(bx, by - 16 * SS, bx + 20 * SS, by - 32 * SS, 2.0)
        leaf(bx - 20 * SS, by - 32 * SS, 13 * SS, 7 * SS, 42, LEAF)
        leaf(bx + 22 * SS, by - 34 * SS, 13 * SS, 7 * SS, -40, LEAF_L)
        leaf(bx - 8 * SS, by - 46 * SS, 12 * SS, 6.5 * SS, 16, LEAF)
        leaf(bx + 10 * SS, by - 48 * SS, 12 * SS, 6.5 * SS, -14, LEAF_L)
        leaf(bx - 2 * SS, by - 30 * SS, 11 * SS, 6 * SS, 6, LEAF)
        leaf(bx + 14 * SS, by - 22 * SS, 9 * SS, 5 * SS, -50, LEAF)
        # fruits
        fruits = [
            (bx - 10 * SS, by - 28 * SS, CORAL),
            (bx + 8 * SS, by - 36 * SS, ORANGE),
            (bx + 16 * SS, by - 24 * SS, ROSE),
            (bx - 2 * SS, by - 42 * SS, GOLD_D),
            (bx + 4 * SS, by - 22 * SS, PINK),
        ]
        for fx, fy, col in fruits:
            ellipse(d, fx, fy, 5.2 * SS, 5.2 * SS, fill=col, outline=INK, width=int(1.4 * SS))
            ellipse(d, fx - 1.5 * SS, fy - 1.6 * SS, 1.6 * SS, 1.4 * SS, fill=rgba(WHITE, 140))
    return down(im, 128, 128)


def draw_farm_plot_empty():
    return draw_farm_plot(0)


def draw_farm_crop_stage1_sprout():
    return draw_farm_plot(1)


def draw_farm_crop_stage2_growing():
    return draw_farm_plot(2)


def draw_farm_crop_stage3_ripe():
    return draw_farm_plot(3)


def draw_work_outdoor_stove_table():
    im = canvas(128, 128)
    d = draw_of(im)
    cx, cy = 64 * SS, 82 * SS
    ground_shadow(im, cx, cy + 8 * SS, 46 * SS, 14 * SS, 90)
    # table slab
    iso_box(d, cx, cy - 18 * SS, 46 * SS, 20 * SS, 8 * SS,
            top=WOOD_L, side_l=WOOD_D, side_r=WOOD, ow=int(1.8 * SS), dest_im=im)
    # four legs (front two visible, back suggested)
    def leg(x, y, h=22):
        d.rectangle([x - 2.4 * SS, y, x + 2.4 * SS, y + h * SS], fill=WOOD_D, outline=INK, width=SS)
    # approximate leg positions at table corners
    leg(cx - 30 * SS, cy - 8 * SS, 22)
    leg(cx + 30 * SS, cy - 8 * SS, 22)
    leg(cx - 14 * SS, cy + 6 * SS, 16)
    leg(cx + 14 * SS, cy + 6 * SS, 16)
    # clay stove on the table (slightly left)
    sx, sy = cx - 10 * SS, cy - 30 * SS
    # body
    rrect(d, [sx - 16 * SS, sy - 4 * SS, sx + 16 * SS, sy + 16 * SS], 3 * SS,
          fill=(132, 92, 74, 255), outline=INK, width=int(1.6 * SS))
    # fire mouth
    ellipse(d, sx, sy + 8 * SS, 7 * SS, 5 * SS, fill=(40, 24, 20, 255), outline=INK, width=SS)
    ellipse(d, sx, sy + 8 * SS, 4.5 * SS, 3.2 * SS, fill=ORANGE)
    ellipse(d, sx, sy + 8 * SS, 2.2 * SS, 1.6 * SS, fill=GOLD)
    # pot
    ellipse(d, sx, sy - 8 * SS, 12 * SS, 6 * SS, fill=TEAL_D, outline=INK, width=int(1.6 * SS))
    rrect(d, [sx - 10 * SS, sy - 14 * SS, sx + 10 * SS, sy - 4 * SS], 2 * SS, fill=TEAL, outline=INK, width=int(1.5 * SS))
    ellipse(d, sx, sy - 14 * SS, 10 * SS, 4 * SS, fill=TEAL_D, outline=INK, width=int(1.4 * SS))
    # handle
    d.arc([sx + 8 * SS, sy - 16 * SS, sx + 20 * SS, sy - 4 * SS], start=270, end=90, fill=INK, width=int(1.8 * SS))
    # subtle steam (not flashy)
    for i, (dx, dy) in enumerate([(-3, -24), (2, -28), (6, -22)]):
        ellipse(d, sx + dx * SS, sy + dy * SS, 2.4 * SS, 3.2 * SS, fill=rgba(WHITE, 90))
    # small board / bowl on the right of the table
    iso_box(d, cx + 22 * SS, cy - 24 * SS, 12 * SS, 6 * SS, 3 * SS,
            top=CREAM2, side_l=SAND, side_r=WOOD, ow=SS, dest_im=im)
    ellipse(d, cx + 22 * SS, cy - 26 * SS, 4 * SS, 3 * SS, fill=PINK, outline=INK, width=SS)
    return down(im, 128, 128)


def draw_work_outdoor_post_rack():
    im = canvas(128, 128)
    d = draw_of(im)
    cx, cy = 64 * SS, 86 * SS
    ground_shadow(im, cx, cy + 4 * SS, 40 * SS, 12 * SS, 90)
    # base plinth
    iso_box(d, cx, cy, 36 * SS, 14 * SS, 6 * SS, top=WOOD, side_l=WOOD_D, side_r=WOOD_M, ow=int(1.6 * SS), dest_im=im)
    # two posts
    def post(x):
        d.rectangle([x - 3 * SS, cy - 70 * SS, x + 3 * SS, cy - 2 * SS], fill=WOOD_L, outline=INK, width=int(1.4 * SS))
    post(cx - 22 * SS)
    post(cx + 22 * SS)
    # top bar
    d.rectangle([cx - 26 * SS, cy - 72 * SS, cx + 26 * SS, cy - 66 * SS], fill=WOOD, outline=INK, width=int(1.4 * SS))
    # three shelves (front face + thin top)
    shelves = [cy - 54 * SS, cy - 36 * SS, cy - 18 * SS]
    mail_cols = [
        [PAPER, CREAM2, SAND],
        [CREAM, (230, 200, 160, 255), PINK],
        [SAND, PAPER, GOLD],
    ]
    for si, sy in enumerate(shelves):
        # shelf board iso-ish
        iso_box(d, cx, sy, 28 * SS, 8 * SS, 4 * SS, top=WOOD_L, side_l=WOOD_D, side_r=WOOD, ow=int(1.4 * SS), dest_im=im)
        # envelopes standing on shelf
        for j, col in enumerate(mail_cols[si]):
            ex = cx - 16 * SS + j * 16 * SS
            ey = sy - 2 * SS
            rrect(d, [ex - 6 * SS, ey - 16 * SS, ex + 6 * SS, ey], 1 * SS, fill=col, outline=INK, width=SS)
            # flap
            poly(d, [(ex - 6 * SS, ey - 10 * SS), (ex, ey - 3 * SS), (ex + 6 * SS, ey - 10 * SS)], fill=rgba(WOOD, 80))
            d.line([(ex - 6 * SS, ey - 10 * SS), (ex, ey - 3 * SS), (ex + 6 * SS, ey - 10 * SS)], fill=INK, width=SS)
    # small hanging tag
    d.polygon([(cx + 22 * SS, cy - 70 * SS), (cx + 30 * SS, cy - 66 * SS), (cx + 30 * SS, cy - 56 * SS),
               (cx + 22 * SS, cy - 58 * SS)], fill=GOLD, outline=INK)
    d.line([(cx + 22 * SS, cy - 70 * SS), (cx + 30 * SS, cy - 66 * SS), (cx + 30 * SS, cy - 56 * SS),
            (cx + 22 * SS, cy - 58 * SS), (cx + 22 * SS, cy - 70 * SS)], fill=INK, width=SS)
    return down(im, 128, 128)


def _fruit(d, x, y, r, col, squash=1.0):
    ellipse(d, x, y, r, r * squash, fill=col, outline=INK, width=int(1.4 * SS))
    ellipse(d, x - r * 0.3, y - r * 0.35, r * 0.28, r * 0.22, fill=rgba(WHITE, 130))
    # tiny stem
    d.line([(x, y - r * squash), (x + r * 0.15, y - r * squash - 3 * SS)], fill=LEAF_D, width=max(SS, 3))


def draw_storage_fruit_pile(full=False):
    im = canvas(128, 128)
    d = draw_of(im)
    cx, cy = 64 * SS, 92 * SS
    ground_shadow(im, cx, cy, 40 * SS if full else 28 * SS, 12 * SS if full else 9 * SS, 90)
    # shallow wooden tray
    rw = 40 * SS if full else 30 * SS
    iso_box(d, cx, cy - 6 * SS, rw, 16 * SS if full else 12 * SS, 5 * SS,
            top=WOOD_L, side_l=WOOD_D, side_r=WOOD, ow=int(1.5 * SS), dest_im=im)
    fruits_low = [
        (cx - 10 * SS, cy - 14 * SS, 10 * SS, CORAL, 0.9),
        (cx + 8 * SS, cy - 12 * SS, 9 * SS, ORANGE, 0.92),
        (cx + 2 * SS, cy - 22 * SS, 8 * SS, GOLD_D, 0.95),
        (cx - 4 * SS, cy - 8 * SS, 6.5 * SS, PINK, 0.9),
    ]
    fruits_full = fruits_low + [
        (cx - 18 * SS, cy - 10 * SS, 8 * SS, ROSE, 0.9),
        (cx + 18 * SS, cy - 14 * SS, 8.5 * SS, PEACH, 0.92),
        (cx - 8 * SS, cy - 28 * SS, 8 * SS, ORANGE, 0.9),
        (cx + 10 * SS, cy - 28 * SS, 7.5 * SS, CORAL, 0.92),
        (cx + 1 * SS, cy - 36 * SS, 7 * SS, PINK, 0.95),
        (cx - 16 * SS, cy - 22 * SS, 7 * SS, GOLD, 0.9),
        (cx + 16 * SS, cy - 22 * SS, 6.5 * SS, ROSE, 0.9),
        (cx + 4 * SS, cy - 16 * SS, 6 * SS, (210, 70, 80, 255), 0.9),
    ]
    for x, y, r, col, sq in (fruits_full if full else fruits_low):
        _fruit(d, x, y, r, col, sq)
    return down(im, 128, 128)


def draw_storage_fruit_pile_low():
    return draw_storage_fruit_pile(False)


def draw_storage_fruit_pile_full():
    return draw_storage_fruit_pile(True)


def draw_family_wall_board():
    im = canvas(192, 128)
    d = draw_of(im)
    # hanging board, contact at bottom edge of board (wall-mounted, still give a soft contact shadow)
    ground_shadow(im, 96 * SS, 112 * SS, 80 * SS, 10 * SS, 60)
    # main plank
    rrect(d, [10 * SS, 18 * SS, 182 * SS, 110 * SS], 8 * SS, fill=WOOD_L, outline=INK, width=int(2 * SS))
    # wood grain
    for y, a in [(36, 50), (58, 40), (82, 45), (98, 35)]:
        d.line([(18 * SS, y * SS), (174 * SS, (y + 2) * SS)], fill=rgba(WOOD, a), width=SS)
    # top rail
    rrect(d, [10 * SS, 18 * SS, 182 * SS, 32 * SS], 8 * SS, fill=WOOD, outline=INK, width=int(1.8 * SS))
    # hanging rings
    for x in (36, 156):
        ellipse(d, x * SS, 16 * SS, 5 * SS, 5 * SS, fill=None, outline=INK, width=int(2 * SS))
        ellipse(d, x * SS, 16 * SS, 3 * SS, 3 * SS, fill=None, outline=SAND, width=SS)
    # four empty frame slots
    slots = [(28, 44, 60, 92), (70, 44, 102, 92), (112, 44, 144, 92), (154, 44, 176, 92)]
    # last one slightly narrower
    slots = [
        (22, 42, 62, 98),
        (68, 42, 108, 98),
        (114, 42, 154, 98),
        (160, 48, 178, 92),  # small slot
    ]
    inners = [CREAM, (255, 248, 230, 255), CREAM2, PAPER]
    for (x0, y0, x1, y1), inn in zip(slots, inners):
        rrect(d, [x0 * SS, y0 * SS, x1 * SS, y1 * SS], 3 * SS, fill=WOOD_D, outline=INK, width=int(1.6 * SS))
        rrect(d, [(x0 + 4) * SS, (y0 + 4) * SS, (x1 - 4) * SS, (y1 - 4) * SS], 2 * SS, fill=inn, outline=INK, width=SS)
    # tiny heart glyph on the rail (family)
    poly(d, heart_pts(96 * SS, 25 * SS, 10 * SS, 8 * SS), fill=PINK)
    d.line(heart_pts(96 * SS, 25 * SS, 10 * SS, 8 * SS) + [heart_pts(96 * SS, 25 * SS, 10 * SS, 8 * SS)[0]], fill=INK, width=SS, joint="curve")
    return down(im, 192, 128)


def draw_family_wall_frame_slot():
    im = canvas(48, 48)
    d = draw_of(im)
    paste(im, soft_shadow(im.size, [4 * SS, 6 * SS, 44 * SS, 46 * SS], 4 * SS, (40, 28, 22, 70), 3))
    rrect(d, [3 * SS, 3 * SS, 45 * SS, 45 * SS], 5 * SS, fill=WOOD, outline=INK, width=int(1.6 * SS))
    rrect(d, [8 * SS, 8 * SS, 40 * SS, 40 * SS], 3 * SS, fill=WOOD_L, outline=INK, width=SS)
    # transparent hole
    hole = Image.new("L", im.size, 0)
    hd = ImageDraw.Draw(hole)
    hd.rounded_rectangle([11 * SS, 11 * SS, 37 * SS, 37 * SS], radius=2 * SS, fill=255)
    arr = np.array(im)
    m = np.array(hole)
    arr[m == 255, 3] = 0
    im = Image.fromarray(arr, "RGBA")
    return down(im, 48, 48)


# ---------------------------------------------------------------------------
# Kid markers A–H (48x48), distinct color + shape
# ---------------------------------------------------------------------------

def _marker_shadow(im):
    paste(im, soft_ellipse_shadow(im.size, 24 * SS, 40 * SS, 14 * SS, 5 * SS, (40, 28, 22, 80), 4))


def draw_kid_marker_A():
    # Teal water drop / tail-fin (A 滴滴 / 水)
    im = canvas(48, 48)
    _marker_shadow(im)
    tmp = layer(im.size)
    d = draw_of(tmp)
    cx, cy = 24 * SS, 28 * SS
    # rounded drop body
    ellipse(d, cx, cy, 11 * SS, 11.5 * SS, fill=TEAL)
    # sharp tip up, overlapping the body
    poly(d, [
        (cx, 7 * SS),
        (cx - 10.5 * SS, 22 * SS),
        (cx + 10.5 * SS, 22 * SS),
    ], fill=TEAL)
    tmp = stroke_alpha(tmp, INK, int(1.7 * SS))
    paste(im, tmp)
    d = draw_of(im)
    # highlight
    ellipse(d, 20 * SS, 26 * SS, 3.2 * SS, 4.2 * SS, fill=rgba(WHITE, 160))
    # small fin
    fin = layer(im.size)
    fd = draw_of(fin)
    poly(fd, [(30 * SS, 30 * SS), (39 * SS, 25 * SS), (32 * SS, 36 * SS)], fill=TEAL_L)
    fin = stroke_alpha(fin, INK, SS)
    paste(im, fin)
    return down(im, 48, 48)


def draw_kid_marker_B():
    # Sky-blue bubble
    im = canvas(48, 48)
    _marker_shadow(im)
    d = draw_of(im)
    ellipse(d, 24 * SS, 24 * SS, 14 * SS, 14 * SS, fill=rgba(SKY, 220), outline=INK, width=int(1.8 * SS))
    ellipse(d, 24 * SS, 24 * SS, 11 * SS, 11 * SS, fill=rgba(WHITE, 50), outline=TEAL, width=SS)
    ellipse(d, 19 * SS, 19 * SS, 4 * SS, 5 * SS, fill=rgba(WHITE, 180))
    ellipse(d, 28 * SS, 16 * SS, 2 * SS, 2.4 * SS, fill=rgba(WHITE, 160))
    return down(im, 48, 48)


def draw_kid_marker_C():
    # Orange flame (C 火角)
    im = canvas(48, 48)
    _marker_shadow(im)
    d = draw_of(im)
    flame = [(24 * SS, 8 * SS), (34 * SS, 20 * SS), (32 * SS, 36 * SS), (24 * SS, 40 * SS),
             (16 * SS, 36 * SS), (14 * SS, 20 * SS)]
    # smoother flame via two ellipses + tip
    ellipse(d, 24 * SS, 28 * SS, 11 * SS, 13 * SS, fill=ORANGE, outline=INK, width=int(1.7 * SS))
    poly(d, [(24 * SS, 6 * SS), (33 * SS, 22 * SS), (15 * SS, 22 * SS)], fill=ORANGE)
    d.line([(15 * SS, 22 * SS), (24 * SS, 6 * SS), (33 * SS, 22 * SS)], fill=INK, width=int(1.7 * SS), joint="curve")
    ellipse(d, 24 * SS, 30 * SS, 6.5 * SS, 8 * SS, fill=GOLD, outline=INK, width=SS)
    ellipse(d, 24 * SS, 32 * SS, 3 * SS, 4 * SS, fill=CREAM)
    return down(im, 48, 48)


def draw_kid_marker_D():
    # Gold crystal spike (D 金刺 / 石)
    im = canvas(48, 48)
    _marker_shadow(im)
    d = draw_of(im)
    crystal = [(24 * SS, 7 * SS), (36 * SS, 22 * SS), (30 * SS, 40 * SS), (18 * SS, 40 * SS), (12 * SS, 22 * SS)]
    poly(d, crystal, fill=GOLD)
    d.line(crystal + [crystal[0]], fill=INK, width=int(1.8 * SS), joint="curve")
    poly(d, [(24 * SS, 7 * SS), (30 * SS, 22 * SS), (24 * SS, 40 * SS), (20 * SS, 22 * SS)], fill=GOLD_D)
    d.line([(24 * SS, 7 * SS), (24 * SS, 40 * SS)], fill=INK, width=SS)
    ellipse(d, 20 * SS, 20 * SS, 2 * SS, 3 * SS, fill=rgba(WHITE, 150))
    return down(im, 48, 48)


def draw_kid_marker_E():
    # Red chili / ember tail (E 辣椒)
    im = canvas(48, 48)
    _marker_shadow(im)
    d = draw_of(im)
    # chili body curved
    ellipse(d, 22 * SS, 26 * SS, 11 * SS, 14 * SS, fill=ROSE, outline=INK, width=int(1.7 * SS))
    # tip curve
    poly(d, [(30 * SS, 18 * SS), (40 * SS, 12 * SS), (36 * SS, 24 * SS)], fill=ROSE)
    d.line([(30 * SS, 18 * SS), (40 * SS, 12 * SS), (36 * SS, 24 * SS)], fill=INK, width=int(1.5 * SS), joint="curve")
    # calyx
    for ang in (-50, 0, 50):
        a = math.radians(ang - 90)
        lx, ly = 18 * SS + 8 * SS * math.cos(a), 14 * SS + 7 * SS * math.sin(a)
        ellipse(d, lx, ly, 3.2 * SS, 2.2 * SS, fill=LEAF_D, outline=INK, width=SS)
    ellipse(d, 18 * SS, 14 * SS, 3.5 * SS, 2.5 * SS, fill=LEAF, outline=INK, width=SS)
    ellipse(d, 18 * SS, 24 * SS, 3 * SS, 4 * SS, fill=rgba(WHITE, 110))
    return down(im, 48, 48)


def draw_kid_marker_F():
    # Yellow star (F 星彈)
    im = canvas(48, 48)
    _marker_shadow(im)
    d = draw_of(im)
    pts = star_pts(24 * SS, 24 * SS, 16 * SS, 6.8 * SS, 5, -math.pi / 2)
    poly(d, pts, fill=GOLD)
    d.line(pts + [pts[0]], fill=INK, width=int(1.8 * SS), joint="curve")
    pts2 = star_pts(24 * SS, 24 * SS, 8 * SS, 3.4 * SS, 5, -math.pi / 2)
    poly(d, pts2, fill=CREAM)
    return down(im, 48, 48)


def draw_kid_marker_G():
    # Night book (G 書 / 夜糰)
    im = canvas(48, 48)
    _marker_shadow(im)
    d = draw_of(im)
    # book
    rrect(d, [10 * SS, 12 * SS, 38 * SS, 40 * SS], 3 * SS, fill=PURPLE, outline=INK, width=int(1.8 * SS))
    # spine
    d.rectangle([22 * SS, 12 * SS, 26 * SS, 40 * SS], fill=(80, 64, 130, 255), outline=INK, width=SS)
    # pages
    rrect(d, [13 * SS, 16 * SS, 21 * SS, 36 * SS], 1 * SS, fill=PAPER, outline=INK, width=SS)
    rrect(d, [27 * SS, 16 * SS, 35 * SS, 36 * SS], 1 * SS, fill=PAPER, outline=INK, width=SS)
    # tiny moon on cover corner
    ellipse(d, 32 * SS, 20 * SS, 3.2 * SS, 3.2 * SS, fill=GOLD, outline=INK, width=SS)
    return down(im, 48, 48)


def draw_kid_marker_H():
    # Lavender crescent moon (H 月角)
    im = canvas(48, 48)
    _marker_shadow(im)
    # crescent via mask
    size = im.size
    m = crescent_mask(size, 26 * SS, 24 * SS, 15 * SS, 33 * SS, 20 * SS, 11 * SS)
    moon = fill_mask(size, m, LAV)
    paste(im, moon)
    d = draw_of(im)
    # outline of crescent: draw outer and inner circles stroke only where mask edge is — approximate with arc
    d.arc([11 * SS, 9 * SS, 41 * SS, 39 * SS], start=50, end=300, fill=INK, width=int(1.8 * SS))
    d.arc([22 * SS, 9 * SS, 44 * SS, 31 * SS], start=80, end=270, fill=INK, width=int(1.6 * SS))
    ellipse(d, 18 * SS, 18 * SS, 2 * SS, 2.4 * SS, fill=rgba(WHITE, 160))
    return down(im, 48, 48)

# ---------------------------------------------------------------------------
# Asset registry
# ---------------------------------------------------------------------------

# (relpath, kind, w, h, json_keys, zh, use, fn)
ASSETS = [
    ("ui/icon_stat_power.png", "ui_icon", 64, 64, ["combat_stats.ids.力量"], "力量", "輕戰鬥數值圖示：力量", draw_icon_stat_power),
    ("ui/icon_stat_agility.png", "ui_icon", 64, 64, ["combat_stats.ids.身手"], "身手", "輕戰鬥數值圖示：身手", draw_icon_stat_agility),
    ("ui/icon_stat_stamina.png", "ui_icon", 64, 64, ["combat_stats.ids.耐力"], "耐力", "輕戰鬥數值圖示：耐力", draw_icon_stat_stamina),
    ("ui/icon_zone_garden.png", "ui_icon", 64, 64, ["zones.starting_always_on.garden", "save_migration.defaults_if_missing.zones_unlocked.garden"], "花園", "區域小標：花園", draw_icon_zone_garden),
    ("ui/icon_zone_cottage_yard_work.png", "ui_icon", 64, 64, ["zones.starting_always_on.cottage_yard_work"], "屋旁基礎工位", "區域小標：屋旁基礎工位", draw_icon_zone_cottage_yard_work),
    ("ui/icon_zone_prairie_edge.png", "ui_icon", 64, 64, ["zones.starting_always_on.prairie_edge"], "草原邊", "區域小標：草原邊", draw_icon_zone_prairie_edge),
    ("ui/icon_zone_zone_farm.png", "ui_icon", 64, 64, ["zones.unlockable.zone_farm"], "農圃", "區域小標：農圃（檔名雙 zone_ 對應穩定 id zone_farm）", draw_icon_zone_farm),
    ("ui/icon_zone_zone_workshop.png", "ui_icon", 64, 64, ["zones.unlockable.zone_workshop"], "開放工作角", "區域小標：開放工作角", draw_icon_zone_workshop),
    ("ui/icon_zone_zone_prairie_deep.png", "ui_icon", 64, 64, ["zones.unlockable.zone_prairie_deep"], "草原深處", "區域小標：草原深處", draw_icon_zone_prairie_deep),
    ("ui/icon_zone_zone_family_wall.png", "ui_icon", 64, 64, ["zones.unlockable.zone_family_wall"], "家族牆空間", "區域小標：家族牆空間", draw_icon_zone_family_wall),
    ("ui/ui_zone_pill_bg.png", "ui_chrome", 160, 56, ["zones"], "切區膠囊（平時）", "切區膠囊按鈕底圖（平時）", draw_ui_zone_pill_bg),
    ("ui/ui_zone_pill_active.png", "ui_chrome", 160, 56, ["zones"], "切區膠囊（選中）", "切區膠囊按鈕底圖（選中）", draw_ui_zone_pill_active),
    ("ui/ui_pet_portrait_frame.png", "ui_chrome", 64, 64, [], "寵物頭像框（平時）", "寵物頭像切鏡框（平時，中空透明）", draw_ui_pet_portrait_frame),
    ("ui/ui_pet_portrait_frame_active.png", "ui_chrome", 64, 64, [], "寵物頭像框（選中）", "寵物頭像切鏡框（選中，中空透明）", draw_ui_pet_portrait_frame_active),
    ("props/farm_plot_empty.png", "prop", 128, 128, ["zones.unlockable.zone_farm"], "空地塊", "農圃空地塊（含木框土壤，3/4 視角）", draw_farm_plot_empty),
    ("props/farm_crop_stage1_sprout.png", "prop", 128, 128, ["zones.unlockable.zone_farm"], "作物階段 1 萌芽", "農圃作物階段 1：萌芽（含地上地塊，可整件替換）", draw_farm_crop_stage1_sprout),
    ("props/farm_crop_stage2_growing.png", "prop", 128, 128, ["zones.unlockable.zone_farm"], "作物階段 2 生長", "農圃作物階段 2：生長（含地上地塊，可整件替換）", draw_farm_crop_stage2_growing),
    ("props/farm_crop_stage3_ripe.png", "prop", 128, 128, ["zones.unlockable.zone_farm"], "作物階段 3 成熟", "農圃作物階段 3：成熟結果（含地上地塊，可整件替換）", draw_farm_crop_stage3_ripe),
    ("props/work_outdoor_stove_table.png", "prop", 128, 128, ["zones.starting_always_on.cottage_yard_work", "zones.unlockable.zone_workshop"], "露天檯灶", "露天簡易檯灶（屋旁工位／開放工作角）", draw_work_outdoor_stove_table),
    ("props/work_outdoor_post_rack.png", "prop", 128, 128, ["zones.starting_always_on.cottage_yard_work", "zones.unlockable.zone_workshop"], "露天郵架", "露天郵架／分揀架", draw_work_outdoor_post_rack),
    ("props/storage_fruit_pile_low.png", "prop", 128, 128, ["save_migration.keep_fields.fruits"], "果堆（少）", "倉位可見果堆（少量）", draw_storage_fruit_pile_low),
    ("props/storage_fruit_pile_full.png", "prop", 128, 128, ["save_migration.keep_fields.fruits"], "果堆（滿）", "倉位可見果堆（滿堆）；§6.1 正式倉堆留最後精修", draw_storage_fruit_pile_full),
    ("props/family_wall_board.png", "prop", 192, 128, ["zones.unlockable.zone_family_wall"], "家族牆木板", "家族牆木板佔位（含相框槽）", draw_family_wall_board),
    ("props/family_wall_frame_slot.png", "prop", 48, 48, ["zones.unlockable.zone_family_wall"], "家族牆相框槽", "家族牆單個相框槽（中空透明）", draw_family_wall_frame_slot),
    ("kids_markers/kid_marker_A.png", "kid_marker", 48, 48, [], "細佬標記 A 滴滴／水", "細佬 A 頭飾／色帶小標（水滴＋尾鰭）", draw_kid_marker_A),
    ("kids_markers/kid_marker_B.png", "kid_marker", 48, 48, [], "細佬標記 B 燈燈／泡泡", "細佬 B 頭飾／色帶小標（泡泡）", draw_kid_marker_B),
    ("kids_markers/kid_marker_C.png", "kid_marker", 48, 48, [], "細佬標記 C 火仔／火", "細佬 C 頭飾／色帶小標（火焰）", draw_kid_marker_C),
    ("kids_markers/kid_marker_D.png", "kid_marker", 48, 48, [], "細佬標記 D 熔石／金刺", "細佬 D 頭飾／色帶小標（金晶）", draw_kid_marker_D),
    ("kids_markers/kid_marker_E.png", "kid_marker", 48, 48, [], "細佬標記 E 火糰／辣椒", "細佬 E 頭飾／色帶小標（辣椒）", draw_kid_marker_E),
    ("kids_markers/kid_marker_F.png", "kid_marker", 48, 48, [], "細佬標記 F 星彈／星", "細佬 F 頭飾／色帶小標（星）", draw_kid_marker_F),
    ("kids_markers/kid_marker_G.png", "kid_marker", 48, 48, [], "細佬標記 G 夜糰／書", "細佬 G 頭飾／色帶小標（夜書）", draw_kid_marker_G),
    ("kids_markers/kid_marker_H.png", "kid_marker", 48, 48, [], "細佬標記 H 月角／月", "細佬 H 頭飾／色帶小標（新月）", draw_kid_marker_H),
]

ZONE_TABLE = [
    ("garden", "花園", "starting", "icon_zone_garden.png"),
    ("cottage_yard_work", "屋旁基礎工位", "starting", "icon_zone_cottage_yard_work.png"),
    ("prairie_edge", "草原邊", "starting", "icon_zone_prairie_edge.png"),
    ("zone_farm", "農圃", "unlockable", "icon_zone_zone_farm.png"),
    ("zone_workshop", "開放工作角", "unlockable", "icon_zone_zone_workshop.png"),
    ("zone_prairie_deep", "草原深處", "unlockable", "icon_zone_zone_prairie_deep.png"),
    ("zone_family_wall", "家族牆空間", "unlockable", "icon_zone_zone_family_wall.png"),
]


def offset_y_centered(sole_edge, height, node_y, pixel_size=1.0):
    """Sprite3D centered=true: sole_world = node_y + offset_y*ps + (H/2 - sole_edge)*ps.
    Want sole_world = 0 → offset_y = (sole_edge - H/2) - node_y/ps."""
    return (sole_edge - height / 2.0) - (node_y / pixel_size)


# ---------------------------------------------------------------------------
# series2 measurements
# ---------------------------------------------------------------------------

def _strip_frames(path: Path):
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    if w % h == 0:
        fw, fh, n = h, h, w // h
        boxes = [(i * fw, 0, (i + 1) * fw, fh) for i in range(n)]
    elif h % w == 0:
        fw, fh, n = w, w, h // w
        boxes = [(0, i * fh, fw, (i + 1) * fh) for i in range(n)]
    else:
        fw, fh, n = w, h, 1
        boxes = [(0, 0, w, h)]
    frames = []
    arr = np.array(im)
    for i, (x0, y0, x1, y1) in enumerate(boxes):
        a = arr[y0:y1, x0:x1, 3]
        ys, xs = np.where(a > 0)
        solid = np.where(a >= 128)
        if ys.size == 0:
            frames.append({"i": i, "empty": True})
            continue
        last = int(ys.max())
        first = int(ys.min())
        last_s = int(solid[0].max()) if solid[0].size else last
        frames.append({
            "i": i,
            "empty": False,
            "last_opaque_row": last,
            "last_solid_row": last_s,
            "first_opaque_row": first,
            "sole_edge": last + 1,
            "bbox": [int(xs.min()), first, int(xs.max()), last],
        })
    return {"file": str(path), "strip_size": [w, h], "frame_size": [fw, fh], "frame_count": n, "frames": frames}


def measure_series2():
    forms = [f"{L}{s}" for L in "ABCDEFGH" for s in "123"]
    forms += ["S1", "S2"] + [f"S4{L}" for L in "ABCDEFGH"]
    acts = ["idle", "walk", "cry", "eat", "sleep"]
    actions = SERIES2 / "actions"
    out = {
        "source": str(SERIES2),
        "docs": {
            "SERIES2_4A.md": "48×48, pivot (24,45), groundRow 46; B 系跟 B1 腳 y=45",
            "forms/tuned.json": {"size": [48, 48], "pivot": [24, 45], "groundRow": 46},
            "actions/actions.json": {"frameSize": 48, "pivot": [24, 45]},
        },
        "675_reference": {
            "canvas": [64, 64],
            "sole_row": 62,
            "sole_edge": 63,
            "layout_anchor_not_sole": [32, 61],
            "centered": True,
            "pixel_size": 1,
            "node_y_convention": 29,
            "offset_y_after_overlay": 2,
            "note": "r4 SPEC 原 new_offset=null；後來工程 overlay 用 offset.y=+2，令足底邊落到世界 Y=0。本契約跟 overlay 慣例。",
        },
        "complete": True,
        "forms": {},
    }
    missing = []
    top_clip = []
    for form in forms:
        rec = {"form": form, "actions": {}, "group": None}
        for act in acts:
            p = actions / f"{form}_{act}.png"
            if not p.exists():
                missing.append(p.name)
                rec["actions"][act] = {"missing": True}
                continue
            rec["actions"][act] = _strip_frames(p)
        idle = rec["actions"].get("idle", {})
        walk = rec["actions"].get("walk", {})
        idle_frames = idle.get("frames") or []
        walk_frames = walk.get("frames") or []
        idle_sole = max((f["last_opaque_row"] for f in idle_frames if not f.get("empty")), default=None)
        walk_soles = [f["last_opaque_row"] for f in walk_frames if not f.get("empty")]
        walk_first = [f["first_opaque_row"] for f in walk_frames if not f.get("empty")]
        rec["idle_last_opaque_row"] = idle_sole
        rec["walk_last_opaque_row_min"] = min(walk_soles) if walk_soles else None
        rec["walk_last_opaque_row_max"] = max(walk_soles) if walk_soles else None
        rec["walk_first_opaque_row_min"] = min(walk_first) if walk_first else None
        rec["eat_last_opaque_row_max"] = max((f["last_opaque_row"] for f in rec["actions"].get("eat", {}).get("frames", []) if not f.get("empty")), default=None)
        # recommended Sprite3D to plant idle/contact sole at world Y=0, same node as 675
        if idle_sole is not None:
            rec["recommended"] = {
                "reuse_path_pattern": f"actions/{form}_{{idle,walk,cry,eat,sleep}}.png",
                "frame_size": [48, 48],
                "centered": True,
                "pixel_size": 1,
                "do_not_upscale_to_64": True,
                "scale_vs_675": 48 / 64,
                "node_y": 29,
                "offset_y": idle_sole - 52,  # last_opaque - 52 derived: o = lastY - 52 for H=48, node=29, ps=1
                "offset_y_formula": "idle_last_opaque_row - 52   # == offset_y_centered(sole_edge=idle+1, H=48, node_y=29, ps=1)",
                "official_pivot_px": [24, 45],
                "official_groundRow": 46,
                "bind_offset_to": "idle/contact sole (not eat squash, not walk airborne frames)",
            }
            rec["group"] = f"idle_sole_{idle_sole}_offset_y_{idle_sole - 52}"
        if rec["walk_first_opaque_row_min"] == 0:
            rec["top_clip_risk"] = True
            top_clip.append(form)
        out["forms"][form] = rec
    out["missing_files"] = missing
    out["complete"] = len(missing) == 0
    out["top_clip_walk_forms"] = top_clip
    out["offset_groups"] = {
        "offset_y_-6__idle_sole_46": [f for f, r in out["forms"].items() if r.get("idle_last_opaque_row") == 46],
        "offset_y_-7__idle_sole_45": [f for f, r in out["forms"].items() if r.get("idle_last_opaque_row") == 45],
    }
    out["fallback"] = {
        "when": "錨點／片幅同 675 唔合，或認唔出細佬",
        "do": "保持 pixel_size=1（細佬約為團絨 75% 高），按 form 用 recommended.offset_y；再疊 kids_markers/kid_marker_{A–H}.png 喺頭頂（billboard，約 headTop + 2px）。唔好把 48 拉到 64。675 正式行走套留最後精修。",
        "marker_size": [48, 48],
        "marker_files": [f"kids_markers/kid_marker_{L}.png" for L in "ABCDEFGH"],
    }
    return out


# ---------------------------------------------------------------------------
# Contact sheet
# ---------------------------------------------------------------------------

def _bg_grass(w, h):
    im = Image.new("RGBA", (w, h), (32, 48, 34, 255))
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(20261124)
    for _ in range(int(w * h / 40)):
        x = int(rng.integers(0, w))
        y = int(rng.integers(0, h))
        col = (int(28 + rng.integers(0, 24)), int(50 + rng.integers(0, 30)), int(30 + rng.integers(0, 20)), 255)
        d.line([(x, y), (x + int(rng.integers(-4, 5)), y - int(rng.integers(3, 10)))], fill=col, width=1)
    # vignette-ish darker bottom
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rectangle([0, int(h * 0.75), w, h], fill=(20, 28, 18, 40))
    im.alpha_composite(overlay)
    return im


def _bg_wood(w, h):
    im = Image.new("RGBA", (w, h), (232, 210, 170, 255))
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(20261124)
    for y in range(0, h, 5):
        col = (int(210 + rng.integers(0, 30)), int(180 + rng.integers(0, 25)), int(140 + rng.integers(0, 20)), 255)
        d.line([(0, y + int(rng.integers(0, 2))), (w, y + int(rng.integers(0, 3)))], fill=col, width=1)
    for _ in range(18):
        x = int(rng.integers(10, max(11, w - 10)))
        y = int(rng.integers(10, max(11, h - 10)))
        d.ellipse([x, y, x + 8, y + 4], outline=(180, 140, 90, 80), width=1)
    return im


def _checker_label(text, size=18, bold=False, fill=(40, 28, 24, 255)):
    f = font(size, bold=bold)
    # measure
    tmp = Image.new("L", (4, 4), 0)
    d = ImageDraw.Draw(tmp)
    bbox = d.textbbox((0, 0), text, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    im = Image.new("RGBA", (tw + 8, th + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # halo
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1)]:
        d.text((4 + dx, 2 + dy), text, font=f, fill=(255, 248, 230, 220))
    d.text((4, 2), text, font=f, fill=fill)
    return im


def make_contact_sheet(built):
    """built: list of dicts with rel, im, w, h, zh, kind."""
    W = 2560
    margin = 36
    # group
    groups = [
        ("1. 輕戰鬥數值圖示（64×64，另附 24px／20px 縮圖驗可讀性）", "ui_icon_stat"),
        ("2. 區域小標（64×64，檔名對穩定 zone id）", "ui_icon_zone"),
        ("3. 切區膠囊同頭像框（觸控高度 ≥48px）", "ui_chrome"),
        ("4. 農圃地塊同作物三階段（128×128，3/4 視角）", "farm"),
        ("5. 工位、郵架同倉位果堆（128×128）", "work"),
        ("6. 家族牆佔位（192×128 木板、48×48 相框槽）", "family"),
        ("7. 細佬 A–H 頭飾／色帶小標（48×48）", "kid_marker"),
    ]

    def group_of(rec):
        rel = rec["rel"]
        if rel.startswith("ui/icon_stat_"):
            return "ui_icon_stat"
        if rel.startswith("ui/icon_zone_"):
            return "ui_icon_zone"
        if rel.startswith("ui/ui_"):
            return "ui_chrome"
        if "farm_" in rel:
            return "farm"
        if rel.startswith("props/work_") or "fruit_pile" in rel:
            return "work"
        if "family_wall" in rel:
            return "family"
        if rel.startswith("kids_markers/"):
            return "kid_marker"
        return "other"

    # card layout
    # each card: two previews + caption
    def card_size(rec):
        w, h = rec["w"], rec["h"]
        # preview box
        pv = 160 if max(w, h) <= 64 else (200 if max(w, h) <= 128 else 240)
        # two previews side by side + pad
        cw = pv * 2 + 28
        ch = pv + 78
        if rec["rel"].startswith("ui/icon_"):
            ch += 44  # 24/20 proof row
        return cw, ch, pv

    # measure rows
    header_h = 210
    footer_h = 260
    rows_meta = []
    y = header_h
    for title, gid in groups:
        items = [r for r in built if group_of(r) == gid]
        if not items:
            continue
        y += 54
        x = margin
        row_h = 0
        row = []
        for rec in items:
            cw, ch, pv = card_size(rec)
            if x + cw > W - margin and row:
                rows_meta.append((title if not row else None, row, row_h))
                # only first row of group gets title — simplify: title once then flow
                y += row_h + 16
                x = margin
                row, row_h = [], 0
                title = None
            row.append((rec, cw, ch, pv))
            row_h = max(row_h, ch)
            x += cw + 16
        if row:
            rows_meta.append((title, row, row_h))
            y += row_h + 24
    total_h = y + footer_h

    sheet = Image.new("RGBA", (W, total_h), (248, 242, 228, 255))
    d = ImageDraw.Draw(sheet)
    # header band
    d.rectangle([0, 0, W, header_h], fill=(58, 40, 36, 255))
    d.rectangle([0, header_h - 8, W, header_h], fill=GOLD)
    title_f = font(42, bold=True)
    sub_f = font(20, bold=False)
    small_f = font(16, bold=False)
    d.text((margin, 28), "微光小圃 · 活生態圈 v1 最少可讀美術包", font=title_f, fill=CREAM)
    d.text((margin, 86), "minimal_readable_draft  ·  非最終 675 精修  ·  2026-11-24  Asia/Hong_Kong UTC+8", font=sub_f, fill=GOLD)
    d.text((margin, 124), "左格：暗色草地底　　右格：淺色木底　　全部新產出透明 PNG 均未烘焙浮水印（標記寫喺 PNG tEXt／MANIFEST／本表）", font=small_f, fill=PAPER)
    d.text((margin, 154), str(ROOT) + "    共 %d 張新 PNG（另加本聯絡表）" % len(built), font=small_f, fill=SAND)

    y = header_h + 16
    pending_title = None
    for title, row, row_h in rows_meta:
        if title:
            d.text((margin, y), title, font=font(22, bold=True), fill=INK)
            y += 40
        x = margin
        for rec, cw, ch, pv in row:
            # card background
            d.rounded_rectangle([x, y, x + cw, y + ch], radius=10, fill=(255, 250, 240, 255), outline=(160, 120, 80, 255), width=2)
            # two preview boxes
            gw = pv
            gh = pv
            # grass
            gbox = (x + 10, y + 10, x + 10 + gw, y + 10 + gh)
            wbox = (x + 14 + gw, y + 10, x + 14 + 2 * gw, y + 10 + gh)
            grass = _bg_grass(gw, gh)
            wood = _bg_wood(gw, gh)
            sheet.paste(grass, (gbox[0], gbox[1]))
            sheet.paste(wood, (wbox[0], wbox[1]))
            # scale asset to fit with padding
            src = rec["im"]
            pad = 10
            avail = pv - pad * 2
            scale = min(avail / src.size[0], avail / src.size[1], 2.0 if max(src.size) <= 64 else 1.5)
            nw, nh = max(1, int(src.size[0] * scale)), max(1, int(src.size[1] * scale))
            shown = resize_premul(src, (nw, nh))
            for box in (gbox, wbox):
                px = box[0] + (pv - nw) // 2
                py = box[1] + (pv - nh) // 2
                sheet.alpha_composite(shown, (px, py))
            # labels under
            caption = f"{Path(rec['rel']).name}   {rec['w']}×{rec['h']}"
            d.text((x + 10, y + 14 + pv), caption, font=font(14, bold=True), fill=INK)
            d.text((x + 10, y + 14 + pv + 20), rec["zh"], font=font(13), fill=(90, 60, 40, 255))
            # 20/24 proofs for icons
            if rec["rel"].startswith("ui/icon_"):
                proof_y = y + 14 + pv + 40
                d.text((x + 10, proof_y), "24px", font=font(12), fill=WOOD_D)
                d.text((x + 80, proof_y), "20px", font=font(12), fill=WOOD_D)
                s24 = resize_premul(src, (24, 24))
                s20 = resize_premul(src, (20, 20))
                # place on mini grass / wood chips
                for sx0, sim, sz in ((40, s24, 24), (110, s20, 20)):
                    bg = _bg_grass(sz + 8, sz + 8)
                    sheet.paste(bg, (x + sx0, proof_y + 16))
                    sheet.alpha_composite(sim, (x + sx0 + 4, proof_y + 20))
                    bg2 = _bg_wood(sz + 8, sz + 8)
                    sheet.paste(bg2, (x + sx0 + 50, proof_y + 16))
                    sheet.alpha_composite(sim, (x + sx0 + 54, proof_y + 20))
            x += cw + 16
        y += row_h + 20

    # footer
    fy = total_h - footer_h + 16
    d.rectangle([0, fy - 16, W, total_h], fill=(58, 40, 36, 255))
    notes = [
        "本包性質：最少可讀佔位（minimal_readable_draft），唔係 675 精修、唔係 Kurt 畫面驗收、未接入引擎。",
        "既有 HUD 習慣：照顧圖示源像素 32×32、Nearest 整數倍；本包新圖示為 64×64 抗鋸齒。同欄混用時請用線性縮放或單獨層，唔好對本包套 Nearest。",
        "切區膠囊 160×56（高 ≥48）；9-slice 邊距 left/right=28、top/bottom=12；控制項高度請保持 56，只橫向拉伸。頭像框 64×64，中空透明。",
        "675 團絨行路：64×64、末不透明行 62、足底邊 63、centered、pixel_size=1、node y=29、overlay offset.y=+2。細佬 series2 保持 48×48、pixel_size=1，多數 form offset.y=−6，B1／H3／S4B 用 −7。",
        "暫時合體：唔新造完整形態。雙影偏移 + 暖金青漸層 tint + 光圈呼吸，參數見 ART_CONTRACT.md。正式合體形態留最後精修。",
        "作物階段檔名 stage1_sprout / stage2_growing / stage3_ripe 係美術佔位鍵；遊策 JSON 尚未列出 crop_stages，接入前建議補 key。",
    ]
    for i, line in enumerate(notes):
        d.text((margin, fy + 8 + i * 32), line, font=font(15), fill=PAPER)
    return sheet

# ---------------------------------------------------------------------------
# ART_CONTRACT + MANIFEST + main
# ---------------------------------------------------------------------------

def write_art_contract(s2, manifest_n):
    p = ROOT / "ART_CONTRACT.md"
    # offset groups
    g46 = ", ".join(s2["offset_groups"]["offset_y_-6__idle_sole_46"])
    g45 = ", ".join(s2["offset_groups"]["offset_y_-7__idle_sole_45"])
    clips = ", ".join(s2["top_clip_walk_forms"]) or "（無）"
    missing = ", ".join(s2["missing_files"]) or "無（A–H 各 1–3 階＋S1／S2／S4A–H，每階 idle／walk／cry／eat／sleep 齊）"

    text = f"""# 活生態圈 v1 · 最少可讀美術接入契約（給遊程）

寫於 2026-11-24 Asia/Hong_Kong UTC+8。  
包路徑：`{ROOT}`  
性質：**最少可讀佔位（`minimal_readable_draft`）**，唔係最終 675 精修，唔係 Kurt 畫面驗收，未接入引擎。  
對齊：`/home/box/keep/遊策/ecosystem-v1-data-draft.json`、`master-gameplay-roadmap-2026-11-24-support.md`。  
675 基準：`/home/box/keep/godot/hd2d-pilot-v6/pet_walk_art_r4/`（64×64，sole 行 62，邊 63）。  
既有 HUD：`/home/box/keep/godot/hd2d-pilot-v6/gameplay_art_r1/SPEC.md`。

---

## ① 七區命名同穩定 id

| 穩定 id（JSON 100%） | 中文 | 類型 | 本包圖示檔名 |
|---|---|---|---|
| `garden` | 花園 | 起始 | `ui/icon_zone_garden.png` |
| `cottage_yard_work` | 屋旁基礎工位 | 起始 | `ui/icon_zone_cottage_yard_work.png` |
| `prairie_edge` | 草原邊 | 起始 | `ui/icon_zone_prairie_edge.png` |
| `zone_farm` | 農圃 | 解鎖 | `ui/icon_zone_zone_farm.png` |
| `zone_workshop` | 開放工作角 | 解鎖 | `ui/icon_zone_zone_workshop.png` |
| `zone_prairie_deep` | 草原深處 | 解鎖 | `ui/icon_zone_zone_prairie_deep.png` |
| `zone_family_wall` | 家族牆空間 | 解鎖 | `ui/icon_zone_zone_family_wall.png` |

解鎖四區嘅穩定 id **本身已帶** `zone_` 前綴；圖示檔名再加一層 `icon_zone_`，所以會出現 `icon_zone_zone_farm.png` 這種雙 `zone_`。請用表對，唔好自行改名。

切區膠囊：`ui/ui_zone_pill_bg.png`／`ui/ui_zone_pill_active.png`（160×56）。  
9-slice 邊距：`left=28, right=28, top=12, bottom=12`。控制項高度**保持 56**，只准橫向拉伸（全高膠囊，垂直拉伸會變形）。  
寵物頭像切鏡框：`ui/ui_pet_portrait_frame.png`／`ui_pet_portrait_frame_active.png`（64×64，中空透明，至少 48px 觸控）。

輕戰鬥數值（JSON `combat_stats.ids` 用中文）：

| JSON id | 檔名 |
|---|---|
| 力量 | `ui/icon_stat_power.png` |
| 身手 | `ui/icon_stat_agility.png` |
| 耐力 | `ui/icon_stat_stamina.png` |

---

## ② 細佬 A–H：series2 實測、腳底錨點、縮放同 fallback

來源（本機舊套，齊檔）：`{SERIES2}`  
規格文件：`SERIES2_4A.md`、`forms/tuned.json`、`actions/actions.json`。  
官方標稱：畫布 **48×48**，`pivot (24, 45)`，`groundRow 46`（B 系跟 B1，腳 y=45）。alpha 0/255，Nearest 像素風。

實測（全部 34 個階段 × 5 動作 strip **齊檔**，缺檔：{missing}）：

- idle／cry／sleep：多數 form 末不透明行 **46**；**B1、H3、S4B** 為 **45**（同官方 B1 例外；注意 B2／B3 已係 46，唔好成「B 系」一刀切）。
- walk：接觸／抬腳在 `idle_sole` 同 `idle_sole-2` 之間來回（例如 44–46 或 43–45），屬步態，唔係錨點漂移。
- eat：多數會瞬間落到 `idle_sole+1`（47 或 46）——食嘢下壓，**唔好**用 eat 嘅最大 Y 去算 offset，否則 idle 會浮 1px。
- 頂裁切風險（walk 有幀 `first_opaque_row == 0`）：**{clips}**。48 畫布裝唔下部分 3 階／S4 頭頂，屬舊素材邊界；認唔出就靠頭飾標記。

### 同 675 團絨對齊（跟現行 overlay 慣例，唔跟 r4 SPEC 的 `new_offset=null`）

675 行路圖：獨立幀 **64×64**，末不透明行 **62**，足底邊 **63**，`centered=true`，`pixel_size=1`，node y **29**，工程 overlay **`offset.y = +2`**，令足底邊落到世界 Y=0。

細佬建議（同一套 Sprite3D 慣例，**唔好把 48 拉到 64**）：

| 項 | 值 |
|---|---|
| 畫布／幀 | 48×48 strip（walk／cry／eat 6 幀，idle／sleep 4 幀） |
| `centered` | `true` |
| `pixel_size` | `1`（細佬約為團絨高度 48/64 = **0.75**） |
| node y | `29`（同 675） |
| `offset.y` 多數 form | **−6**（idle 足底行 46） |
| `offset.y` 例外 | **−7**：{g45} |
| 公式 | `offset.y = idle_last_opaque_row - 52`  （等效：`sole_edge - 24 - 29`） |

**offset.y = −6 嘅 form：** {g46}

機讀詳表：`series2_measurements.json`。

### Fallback 規則

1. 優先重用本機 series2 嘅 `actions/<FORM>_{{idle,walk,cry,eat,sleep}}.png` 跑通。
2. 若認唔出系別，或頂裁切令人困惑：喺頭頂 billboard 疊 `kids_markers/kid_marker_{{A–H}}.png`（48×48，透明底；建議錨在標記底邊，放喺頭頂再上約 2px）。A 水滴、B 泡泡、C 火、D 金晶、E 辣椒、F 星、G 夜書、H 新月，色同形狀互異。
3. 再唔得先用現有小號 clip，仍然加標記。
4. 675 化正式行走套、統一片幅同精修錨點：**留最後統一精修**，今次唔做。

---

## ③ 暫時合體視覺（唔新造完整形態）

對齊 JSON `fusion.type = temporary`，完咗分開、保留原兩隻同族譜。

建議（全部用現有兩隻 sprite，唔出新身體）：

| 參數 | 建議值 |
|---|---|
| 雙影偏移 | 副影相對主影 `+6 px` X（64 空間；約 `0.09 ×` 主體寬）。主影 alpha 1.0，副影 alpha **0.45** |
| 主／副深度 | 副影畫在主影後；兩隻原始寵物邏輯上仍在場，只係合體期間改用雙影呈現 |
| tint 漸層 | 暖金 `#F2D98A` → 青 `#7EC8C3`（可用 `#E8B84A`／`#4A9E9A` 做深色）。`modulate` 按正弦在兩色之間來回 |
| tint 週期 | **1.6 s**（`t = 0.5 + 0.5 * sin(2π * time / 1.6)`） |
| tint 強度 | 乘在原色上約 **0.28–0.40**（唔要整隻變成純金／純青） |
| 光圈 | 柔和橢圓環，半徑約 **0.70 ×** 身體寬；顏色跟同一金青漸層 |
| 光圈呼吸 | alpha **0.22–0.48**，週期同樣 **1.6 s**，可同相或相位差 π |
| 開始／分開 | 淡入 0.35 s；結束淡出光圈同副影 0.40 s，然後恢復兩隻獨立本體 |
| 不做 | 新合體形態、分合骨骼動畫、永久合併刪隻 |

---

## ④ 48px 觸控同 19:9 Note10+ 安全區

| 項目 | 值 |
|---|---|
| 已認可 Low 視口 | **540×1140**（19:9） |
| Note10+ 邏輯 2× | **1080×2280**（19:9；本包 UI 按呢個比例預留） |
| 官方 `project.godot` | 仍為 **1080×1920**（唔係 19:9）。真機 Note10+ 以 19:9 安全區為準，唔好只按 1080×1920 擺底欄 |
| 安全區（540 座標） | 左右 inset **24**，上下 inset **28**（見 gameplay_art_r1 SPEC） |
| 安全區（1080×2280） | 左右 **48**，上下 **56** |
| 本包觸控 | 膠囊高 **56**（≥48）；頭像框 **64**（≥48）；圖示本身 64，若做可點圖示請向外墊到至少 48，**唔好放大貼圖** |

既有照顧 HUD 圖示源像素係 **32×32、Nearest、整數倍**。本包新圖示／道具係 **抗鋸齒暖手繪**，64／128 源。同欄混用時：本包用線性過濾或獨立 Canvas 層，**唔好對本包套 `TEXTURE_FILTER_NEAREST`**，否則邊緣會花。

---

## ⑤ 本包係最少可讀佔位，最後統一 675 精修

今次只交 support 清單裏「試稿最少可讀」嗰欄：區域標、三項戰鬥小標、切鏡掣、農圃地塊＋三階段作物、露天檯灶／郵架、可見果堆、家族牆木板／相框、細佬可認標記。

**明確留最後統一精修（本包不做）：**

- 細佬 675 化正式行走套
- 廚房煮／郵局打包專用動作
- 擴建室內同正式家具位
- §6.1 包裹、正式倉堆、合力抬、坐上大件、揮手召集
- 合體正式形態同分合動畫
- 家族牆關係線同成就框
- 新獵區（林邊、溪邊、花海、山丘）同銀金證

作物檔名 `farm_crop_stage1_sprout`／`stage2_growing`／`stage3_ripe` 係完整可替換道具（每張已含地面地塊，唔好再同 `farm_plot_empty` 疊一次）。JSON 尚未列出 `crop_stages` key，建議遊策補上後再把檔名寫進數值檔。

道具錨點：`MANIFEST.json` 每件有實測 `anchor_px`、`last_opaque_row`、`sole_edge`。建議 Sprite3D `centered=true`、`pixel_size=1`、node 放在地面 Y=0 時：

`offset.y = sole_edge - H/2`

（同 675 公式，只係 node_y=0 而唔係 29。）牆類（`family_wall_board`）可改掛喺牆局部座標，唔強制貼地。

所有新 PNG 帶 tEXt：`Category=minimal_readable_draft`。聯絡表：`contact_sheet.png`。機讀清單：`MANIFEST.json`（{manifest_n} 件新圖）。
"""
    p.write_text(text, encoding="utf-8")
    return p


def build_manifest(entries):
    doc = {
        "_title": "微光小圃 活生態圈 v1 最少可讀美術包 MANIFEST",
        "_updated": "2026-11-24 Asia/Hong_Kong UTC+8",
        "_root": str(ROOT),
        "_category_default": CATEGORY,
        "_note": "本包全部新圖均為 minimal_readable_draft，最後統一 675 精修。series2 原檔屬 reuse，不複製入本包。",
        "nine_slice": {
            "ui/ui_zone_pill_bg.png": PILL_SLICE,
            "ui/ui_zone_pill_active.png": PILL_SLICE,
        },
        "assets": entries,
        "deferred_final_polish": [
            "細佬 675 化正式行走套",
            "廚房煮／郵局打包專用動作",
            "擴建室內同正式家具位",
            "§6.1 包裹、正式倉堆、合力抬、坐上大件、揮手召集",
            "合體正式形態同分合動畫",
            "家族牆關係線同成就框",
            "新獵區（林邊、溪邊、花海、山丘）同銀金證",
        ],
        "reuse_not_in_this_kit": {
            "series2": str(SERIES2),
            "tuanrong_675_walk": "/home/box/keep/godot/hd2d-pilot-v6/pet_walk_art_r4/frames/r4/",
            "care_ui_32": "/workspace/gameplay_art_r1/assets/icons/",
        },
    }
    path = ROOT / "MANIFEST.json"
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "ui").mkdir(exist_ok=True)
    (ROOT / "props").mkdir(exist_ok=True)
    (ROOT / "kids_markers").mkdir(exist_ok=True)

    print("Measuring series2…")
    s2 = measure_series2()
    s2_path = ROOT / "series2_measurements.json"
    s2_path.write_text(json.dumps(s2, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("  complete", s2["complete"], "missing", s2["missing_files"], "top_clip", s2["top_clip_walk_forms"])
    print("  groups", {k: v for k, v in s2["offset_groups"].items()})

    built = []
    manifest_entries = []
    for rel, kind, w, h, keys, zh, use, fn in ASSETS:
        print("Drawing", rel, "…")
        im = fn()
        assert im.size == (w, h), f"{rel} got {im.size} expected {(w, h)}"
        path = ROOT / rel
        save_png(im, path, zh)
        meas = measure_opaque(im)
        digest = sha256(path)
        rec = {
            "rel": rel,
            "im": im,
            "w": w,
            "h": h,
            "zh": zh,
            "kind": kind,
        }
        built.append(rec)
        # offset for props at node y=0, centered, ps=1
        sole = meas.get("sole_edge")
        off0 = (sole - h / 2.0) if sole is not None else None
        manifest_entries.append({
            "path": rel,
            "absolute": str(path),
            "use": use,
            "zh": zh,
            "kind": kind,
            "category": CATEGORY,
            "width": w,
            "height": h,
            "sha256": digest,
            "json_keys": keys,
            "anchor_px": meas.get("anchor_px"),
            "last_opaque_row": meas.get("last_opaque_row"),
            "sole_edge": sole,
            "bbox": meas.get("bbox"),
            "suggested_sprite3d": {
                "centered": True,
                "pixel_size": 1,
                "node_y_if_grounded": 0,
                "offset_y_if_grounded": off0,
                "offset_formula": "sole_edge - H/2  (centered, ps=1, node_y=0)",
            } if kind in ("prop",) else (
                {"touch_min_px": 48, "nine_slice": PILL_SLICE} if "pill" in rel else
                {"touch_min_px": 48, "inner_hole_transparent": True} if "portrait" in rel or "frame_slot" in rel else
                {"readable_at_px": [24, 20]} if kind == "ui_icon" else
                {"overlay_on": "kid headTop + 2px"} if kind == "kid_marker" else {}
            ),
        })

    print("Writing contact sheet…")
    sheet = make_contact_sheet(built)
    sheet_path = ROOT / "contact_sheet.png"
    save_png(sheet, sheet_path, "活生態圈 v1 最少可讀聯絡表")
    print("  contact sheet", sheet.size)

    print("Writing ART_CONTRACT + MANIFEST…")
    contract = write_art_contract(s2, len(manifest_entries))
    man = build_manifest(manifest_entries)

    # also record contact sheet in a sidecar note? not required as an asset of the game.
    print("DONE")
    print("ROOT", ROOT)
    print("PNG assets", len(manifest_entries))
    print("contract", contract)
    print("manifest", man)
    print("sheet", sheet_path, "sha", sha256(sheet_path))
    print("series2", s2_path)


if __name__ == "__main__":
    main()
