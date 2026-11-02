# -*- coding: utf-8 -*-
"""第 8 批 工作場景 V3-A：像素繪圖工具＋5 張場景 1x 層（procedural，Pillow/numpy，唔用 AI 圖）。
座標一律用 art 座標（195×422）；層 223×446＝art＋邊距 MX14／MY12。sprite 層 alpha 只得 0／255。"""
import math, colorsys
import numpy as np
from PIL import Image, ImageDraw
AW, AH, MX, MY = 195, 422, 14, 12
LW, LH = AW + 2 * MX, AH + 2 * MY

def hx(h):
    h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def sh(c, k, hue=0.0, sat=1.0):
    """HD-2D 式明暗：暗位偏藍紫、亮位偏暖。k<1 暗，k>1 光。"""
    c = hx(c) if isinstance(c, str) else c
    h, l, s = colorsys.rgb_to_hls(*[v / 255 for v in c[:3]])
    if k < 1: h = (h + (0.66 - h) * (1 - k) * 0.18 + hue) % 1
    else: h = (h + (0.11 - h) * (k - 1) * 0.25 + hue) % 1
    l = min(1, max(0, l * k)); s = min(1, s * sat)
    r, g, b = colorsys.hls_to_rgb(h, l, s); return (int(r * 255 + .5), int(g * 255 + .5), int(b * 255 + .5))
def mixc(a, b, t):
    a = hx(a) if isinstance(a, str) else a; b = hx(b) if isinstance(b, str) else b
    return tuple(int(a[i] * (1 - t) + b[i] * t + .5) for i in range(3))

class Lyr:
    """一張 1x 層；所有方法收 art 座標。"""
    def __init__(s, w=LW, h=LH, ox=MX, oy=MY):
        s.im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); s.d = ImageDraw.Draw(s.im); s.ox, s.oy = ox, oy
    def c(s, col): col = hx(col) if isinstance(col, str) else col; return tuple(col[:3]) + (255,)
    def px(s, x, y, col): s.d.point((int(x) + s.ox, int(y) + s.oy), s.c(col))
    def rect(s, x0, y0, x1, y1, col): s.d.rectangle([x0 + s.ox, y0 + s.oy, x1 + s.ox, y1 + s.oy], s.c(col))
    def line(s, pts, col, w=1): s.d.line([(x + s.ox, y + s.oy) for x, y in pts], s.c(col), w)
    def poly(s, pts, col): s.d.polygon([(x + s.ox, y + s.oy) for x, y in pts], s.c(col))
    def ell(s, x0, y0, x1, y1, col): s.d.ellipse([x0 + s.ox, y0 + s.oy, x1 + s.ox, y1 + s.oy], s.c(col))
    def clear(s, x0, y0, x1, y1): s.d.rectangle([x0 + s.ox, y0 + s.oy, x1 + s.ox, y1 + s.oy], (0, 0, 0, 0))
    def clear_ell(s, x0, y0, x1, y1): s.d.ellipse([x0 + s.ox, y0 + s.oy, x1 + s.ox, y1 + s.oy], (0, 0, 0, 0))
    def box(s, x0, y0, x1, y1, col, ol=True, hi=1.18, lo=.72):
        """立體方塊：面＋頂／左高光＋底／右暗邊＋深色描邊。"""
        s.rect(x0, y0, x1, y1, col)
        s.rect(x0, y0, x1, y0, sh(col, hi)); s.rect(x0, y0, x0, y1, sh(col, (hi + 1) / 2))
        s.rect(x0, y1, x1, y1, sh(col, lo)); s.rect(x1, y0, x1, y1, sh(col, (lo + 1) / 2))
        if ol: s.d.rectangle([x0 - 1 + s.ox, y0 - 1 + s.oy, x1 + 1 + s.ox, y1 + 1 + s.oy], outline=s.c(sh(col, .42)))
    def vgrad(s, x0, y0, x1, y1, stops, dither=True):
        """直向漸變（4×4 Bayer 抖色，像素感）。stops=[(t,col)…]"""
        B = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.
        cols = [(t, np.array(hx(c) if isinstance(c, str) else c, float)) for t, c in stops]
        for y in range(y0, y1 + 1):
            t = (y - y0) / max(1, y1 - y0)
            for i in range(len(cols) - 1):
                if cols[i][0] <= t <= cols[i + 1][0]: a, b = cols[i], cols[i + 1]; u = (t - a[0]) / max(1e-6, b[0] - a[0]); break
            c = a[1] * (1 - u) + b[1] * u
            for x in range(x0, x1 + 1):
                q = c + ((B[y % 4, x % 4] - .5) * 6 if dither else 0)
                s.px(x, y, tuple(int(v) for v in np.clip(q, 0, 255)))
    def paste(s, other, dx=0, dy=0):
        s.im.alpha_composite(other.im if isinstance(other, Lyr) else other, (dx, dy))
    def np(s): return np.asarray(s.im).astype(float) / 255

def texturize(im, amp=7, seed=1, mask=None):
    """不透明位加 3 級 hash 噪點（保持 0/255 alpha）。"""
    a = np.asarray(im).astype(np.int16).copy(); rnd = np.random.RandomState(seed)
    n = rnd.randint(-1, 2, a.shape[:2]) * amp; op = a[..., 3] > 0
    if mask is not None: op &= mask
    for i in range(3): a[..., i] = np.where(op, np.clip(a[..., i] + n, 0, 255), a[..., i])
    return Image.fromarray(a.astype(np.uint8), 'RGBA')
def binarize(im):
    a = np.asarray(im).copy(); a[..., 3] = np.where(a[..., 3] >= 128, 255, 0); a[a[..., 3] == 0] = 0; return Image.fromarray(a, 'RGBA')
def outline(im, col, inner=False):
    """sprite 外描邊 1px（0/255）。"""
    a = np.asarray(im).copy(); m = a[..., 3] > 0; p = np.pad(m, 1)
    ring = (p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]) & ~m
    c = hx(col) if isinstance(col, str) else col; a[ring] = tuple(c[:3]) + (255,); return Image.fromarray(a, 'RGBA')

# ---------------------------------------------------------------- 共用小物件
def plant(L, x, y, s=1.0, leaf='#4f8a3a', pot='#b5653a', flower=None, seed=0):
    rnd = np.random.RandomState(seed); pw = int(9 * s)
    for i in range(int(14 * s)):
        a = rnd.uniform(-2.6, -.5); r = rnd.uniform(6, 15) * s; lx, ly = x + math.cos(a) * r, y - 2 + math.sin(a) * r
        L.line([(x, y - 2), (lx, ly)], sh(leaf, .7)); L.ell(lx - 2, ly - 1, lx + 2, ly + 1, sh(leaf, rnd.uniform(.85, 1.25)))
        if flower and i % 3 == 0: L.rect(lx - 1, ly - 1, lx, ly, flower); L.px(lx, ly - 1, sh(flower, 1.3))
    L.box(x - pw // 2, y - 1, x + pw // 2, y + int(8 * s), pot); L.rect(x - pw // 2 - 1, y - 1, x + pw // 2 + 1, y, sh(pot, 1.15))
def letter(L, x, y, col='#f4ead2', seal=None, w=6, h=4):
    L.rect(x, y, x + w, y + h, col); L.line([(x, y), (x + w // 2, y + h // 2), (x + w, y)], sh(col, .75))
    L.rect(x, y + h, x + w, y + h, sh(col, .7))
    if seal: L.rect(x + w // 2 - 1, y + h // 2, x + w // 2, y + h // 2 + 1, seal)
def lantern_hang(L, x, y0, y1, col='#c99a3c'):
    for yy in range(y0, y1, 2): L.px(x, yy, sh(col, .6))
    L.poly([(x - 6, y1 + 6), (x, y1), (x + 6, y1 + 6)], sh(col, .9)); L.rect(x - 6, y1 + 6, x + 6, y1 + 7, sh(col, .7))
    L.rect(x - 3, y1 + 8, x + 3, y1 + 11, '#fff2c0'); L.rect(x - 4, y1 + 12, x + 4, y1 + 12, sh(col, .6))
def bunting(L, x0, x1, y, cols, sag=6):
    n = (x1 - x0) // 9; pts = []
    for i in range(n + 1):
        t = i / n; pts.append((x0 + (x1 - x0) * t, y + sag * 4 * t * (1 - t)))
    L.line(pts, '#5a4430')
    for i in range(n):
        (ax, ay), (bx, by) = pts[i], pts[i + 1]; c = cols[i % len(cols)]
        L.poly([(ax + 1, ay + 1), (bx - 1, by + 1), ((ax + bx) / 2, (ay + by) / 2 + 7)], c)
        L.line([(ax + 1, ay + 1), (bx - 1, by + 1)], sh(c, 1.25))
def planks_floor(L, y0, y1, base, seed=3, vanish=(97, 120)):
    """透視木地板：橫縫隨深度變闊＋放射直縫。"""
    rnd = np.random.RandomState(seed); L.rect(-MX, y0, AW - 1 + MX, y1, base)
    y = y0; k = 0
    while y < y1:
        gap = 4 + (y - y0) * .09; ny = int(y + gap)
        L.rect(-MX, ny, AW + MX - 1, ny, sh(base, .62)); L.rect(-MX, y + 1, AW + MX - 1, y + 1, sh(base, 1.12)); k += 1
        y = ny + 1
    for i in range(-14, 15):
        x0 = vanish[0] + i * 7; x1 = vanish[0] + i * 7 * (1 + (y1 - y0) / 60)
        L.line([(x0, y0), (x1, y1)], sh(base, .78))
    for i in range(220):
        x = rnd.randint(-MX, AW + MX); yy = rnd.randint(y0, y1); L.px(x, yy, sh(base, rnd.choice([.85, 1.1, .92])))
def stars_px(L, rect, n, seed, cols=('#ffffff', '#fff2c8', '#cfe0ff')):
    rnd = np.random.RandomState(seed)
    for i in range(n):
        x, y = rnd.randint(rect[0], rect[2]), rnd.randint(rect[1], rect[3]); c = cols[rnd.randint(len(cols))]
        L.px(x, y, c)
        if rnd.rand() < .12: L.px(x - 1, y, sh(c, .6)); L.px(x + 1, y, sh(c, .6)); L.px(x, y - 1, sh(c, .6)); L.px(x, y + 1, sh(c, .6))
def cloud(L, x, y, w, col, seed=0):
    rnd = np.random.RandomState(seed)
    for i in range(6):
        cx = x + rnd.uniform(0, w); r = rnd.uniform(w * .12, w * .22)
        L.ell(cx - r, y - r * .8, cx + r, y + r * .6, col)
    L.rect(x, y, x + w, y + 3, col)
    for i in range(6):
        cx = x + rnd.uniform(0, w); r = rnd.uniform(w * .1, w * .18); L.ell(cx - r, y - r * .9, cx + r * .6, y - r * .3, sh(col, 1.08))
    L.rect(x + 2, y + 3, x + w - 2, y + 3, sh(col, .86))
