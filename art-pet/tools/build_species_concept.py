#!/usr/bin/env python3
"""build_species_concept — 團絨「每條路線變種族」概念（遊美，2026-11-01）。只係概念，唔係正式動畫。
全部用 Python Pillow／numpy 逐像素程式繪製（冇用 AI 出圖），原創生物（唔係現實動物）。
sprite：v3 色盤（motion/palette.json 31 色）、alpha 0/255、無抗鋸齒。風格方向板（style_directions/）係探索用，有自己色盤＋烘焙光影。
用法：python3 build_species_concept.py [all|sprites|sheets|styles|check]"""
import json, os, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.normpath(os.path.join(HERE, ".."))
TR = os.path.join(ROOT, "sprites", "tuanrong"); MOT = os.path.join(TR, "motion")
OUT = os.path.join(TR, "species_concept"); SPR = os.path.join(OUT, "sprites"); PRV = os.path.join(OUT, "preview"); STY = os.path.join(OUT, "style_directions")
PAL = {c["name"]: c["hex"] for c in json.load(open(os.path.join(MOT, "palette.json")))["colors"]}
def rgb(n): h = PAL[n]; return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
V3 = {rgb(n) for n in PAL}
OL = "outline"

# ======================================================================= 遮罩工具（像素中心取樣，冇抗鋸齒）
class Cv:
    def __init__(s, S, k=1.0, ox=0.0, oy=0.0): s.S = S; s.k = k; s.ox = ox; s.oy = oy; s.yy, s.xx = np.mgrid[0:S, 0:S] + 0.5
    def p(s, x, y): return x * s.k + s.ox, y * s.k + s.oy
    def ell(s, cx, cy, rx, ry, rot=0):
        cx, cy = s.p(cx, cy); rx *= s.k; ry *= s.k; c, si = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        u = (s.xx - cx) * c + (s.yy - cy) * si; v = -(s.xx - cx) * si + (s.yy - cy) * c
        return (u / rx) ** 2 + (v / ry) ** 2 <= 1
    def circ(s, cx, cy, r): return s.ell(cx, cy, r, r)
    def poly(s, pts):
        im = Image.new("L", (s.S, s.S)); ImageDraw.Draw(im).polygon([s.p(x, y) for x, y in pts], fill=255); return np.array(im) > 0
    def caps(s, pts, r0, r1=None):
        """粗線（沿點列撒圓），半徑 r0→r1 漸變"""
        r1 = r0 if r1 is None else r1; m = np.zeros((s.S, s.S), bool); n = len(pts) - 1
        for i in range(n):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]; L = max(1, int(math.hypot(x1 - x0, y1 - y0) * 3))
            for t in np.linspace(0, 1, L + 1):
                tt = (i + t) / n; m |= s.circ(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, r0 + (r1 - r0) * tt)
        return m
    def bez(s, p0, p1, p2, n=24): return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0], (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in np.linspace(0, 1, n)]
    def rect(s, x0, y0, x1, y1): return s.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    def star(s, cx, cy, R, r, n=5, rot=-90):
        pts = []
        for i in range(2 * n):
            a = math.radians(rot + i * 180 / n); rr = R if i % 2 == 0 else r; pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        return s.poly(pts)

# ======================================================================= 分件渲染
class Sprite:
    def __init__(s, cv): s.cv = cv; s.parts = []; s.anc = {}; s.decals = []
    def add(s, mask, ramp, z=0, shade="ball", inner=True, name=""):
        s.parts.append(dict(m=mask, ramp=ramp, z=z, shade=shade, inner=inner, name=name)); return mask
    def dec(s, x, y, col):   # 單點 decal（畫喺最後，outline 之前）
        s.decals.append((x, y, col))
    def render(s, outline=True):
        S = s.cv.S; lab = -np.ones((S, S), int); zb = np.full((S, S), -1e9)
        for i, p in enumerate(s.parts):
            w = p["m"] & (p["z"] >= zb); lab[w] = i; zb[w] = p["z"]
        out = np.zeros((S, S, 4), np.uint8); a = lab >= 0
        for i, p in enumerate(s.parts):
            m = lab == i
            if not m.any(): continue
            ys, xs = np.nonzero(p["m"]); cx, cy = (xs.min() + xs.max() + 1) / 2, (ys.min() + ys.max() + 1) / 2
            rx, ry = max(1, (xs.max() - xs.min() + 1) / 2), max(1, (ys.max() - ys.min() + 1) / 2)
            u = (s.cv.xx - cx) / rx; v = (s.cv.yy - cy) / ry; R = p["ramp"]; n = len(R)
            if p["shade"] == "flat": idx = np.full((S, S), n - 2 if n > 1 else 0)
            elif p["shade"] == "stripe": idx = ((np.floor((s.cv.yy - cy) / 2.0 + (s.cv.xx - cx) / 3.0)).astype(int) % 2) * (n - 1)
            else:
                L = -(0.55 * u + 0.8 * v)
                idx = np.where(L < -0.38, 0, np.where(L < 0.3, 1, np.where(L < 0.78, 2, 3)))
                idx = np.minimum(idx, n - 1)
                if n >= 4:  # 高光點：左上細圈先用最亮
                    hi = ((u + 0.42) ** 2 + (v + 0.5) ** 2) < 0.05
                    idx = np.where(hi, n - 1, np.minimum(idx, n - 2))
                # 下緣 1px 陰影
                below = np.zeros_like(m); below[:-1] = ~m[1:]; idx = np.where(below & (idx > 0), 0, idx)
            for j, cn in enumerate(R):
                w = m & (idx == j); out[w, :3] = rgb(cn)
            if p["inner"]:   # 同較低 z 件嘅交界：用自己最深色描
                nb = np.zeros_like(m)
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    sh = np.roll(lab, (dy, dx), (0, 1)); oth = (sh >= 0) & (sh != i)
                    zs = np.array([s.parts[q]["z"] for q in range(len(s.parts))] + [0])[sh]
                    nb |= m & oth & (zs < p["z"])
                out[nb, :3] = rgb(R[0])
        out[a, 3] = 255
        for x, y, col in s.decals:
            xi, yi = int(x), int(y)
            if 0 <= xi < S and 0 <= yi < S and a[yi, xi]: out[yi, xi, :3] = rgb(col)
        if outline:
            ed = np.zeros((S, S), bool)
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                sh = np.roll(a, (dy, dx), (0, 1))
                if dy == 1: sh[0] = False
                if dy == -1: sh[-1] = False
                if dx == 1: sh[:, 0] = False
                if dx == -1: sh[:, -1] = False
                ed |= a & ~sh
            out[ed, :3] = rgb(OL)
        return out

def px(img, x, y, col):
    x, y = int(round(x)), int(round(y))
    if 0 <= y < img.shape[0] and 0 <= x < img.shape[1]: img[y, x, :3] = rgb(col); img[y, x, 3] = 255
def stamp(img, x, y, rows, cmap):
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch in cmap: px(img, x + i, y + j, cmap[ch])

# ======================================================================= 臉（扮醒呆表情）
EXPR = {"neutral": ("open", "smile", None), "smug": ("half", "smirk", "brow1"), "proud_wrong": ("happy", "grin", "brows"),
        "confused_conf": ("uneven", "smile", "brow1"), "think_asleep": ("line", "o", None), "caught": ("wide", "wavy", None),
        "lecture": ("up", "o", "brows")}
def face(img, an, expr="neutral", big=False):
    et, mt, br = EXPR[expr]; (lx, ly), (rx, ry) = an["eyeL"], an["eyeR"]; mx, my = an["mouth"]
    for k, (x, y) in enumerate(((lx, ly), (rx, ry))):
        x, y = int(round(x)), int(round(y)); t = et
        if et == "uneven": t = "open" if k == 1 else "half"
        if t in ("open", "up", "wide"):
            h = 3 if big else 2; dy = -1 if t == "up" else 0
            for j in range(h):
                for i in range(2): px(img, x - 1 + i, y - 1 + j + dy, OL)
            if t == "wide": px(img, x - 1, y - 2, OL); px(img, x, y - 2, OL); px(img, x - 1, y - 1, "white")
            else: px(img, x - 1, y - 1 + dy, "white")
        elif t == "half":
            for i in range(3): px(img, x - 2 + i, y - 1, OL)
            px(img, x - 1, y, OL); px(img, x, y, OL)
        elif t == "happy": px(img, x - 2, y, OL); px(img, x - 1, y - 1, OL); px(img, x, y - 1, OL); px(img, x + 1, y, OL)
        elif t == "line":
            for i in range(3): px(img, x - 2 + i, y, OL)
    if br == "brow1": px(img, rx - 2, ry - 3, OL); px(img, rx - 1, ry - 4, OL); px(img, rx, ry - 4, OL)
    if br == "brows":
        px(img, lx - 2, ly - 4, OL); px(img, lx - 1, ly - 3, OL); px(img, rx - 1, ry - 3, OL); px(img, rx, ry - 4, OL)
    mx, my = int(round(mx)), int(round(my))
    if mt == "smile": px(img, mx - 1, my, OL); px(img, mx, my + 1, OL); px(img, mx + 1, my, OL)
    elif mt == "grin": [px(img, mx - 1 + i, my, OL) for i in range(3)]; px(img, mx - 2, my - 1, OL); px(img, mx + 2, my - 1, OL); px(img, mx, my + 1, "berry_d")
    elif mt == "smirk": px(img, mx - 1, my, OL); px(img, mx, my, OL); px(img, mx + 1, my - 1, OL)
    elif mt == "o": px(img, mx, my, "berry_d"); px(img, mx + 1, my, "berry_d"); px(img, mx, my + 1, OL); px(img, mx + 1, my + 1, OL)
    elif mt == "wavy": px(img, mx - 2, my + 1, OL); px(img, mx - 1, my, OL); px(img, mx, my + 1, OL); px(img, mx + 1, my, OL); px(img, mx + 2, my + 1, OL)
    if an.get("blush", True):
        for x, y, d in ((lx - 3, ly + 2, 1), (rx + 2, ry + 2, -1)):
            px(img, x, y, "blush"); px(img, x + d, y, "blush")

GLYPH = {"?": ["oo.", "..o", ".o.", "...", ".o."], "!": ["o", "o", "o", ".", "o"], "z": ["ooo", "..o", ".o.", "o..", "ooo"],
         "sweat": [".w.", "wdw", "ddd", ".d."], "spark": [".y.", "yWy", ".y."], "1": [".o", "oo", ".o", ".o", ".o"], "+": ["...", ".o.", "ooo", ".o.", "..."],
         "=": ["...", "ooo", "...", "ooo", "..."], "3": ["oo.", "..o", ".o.", "..o", "oo."], "smoke": [".s.", "sws", ".s."]}
def glyph(img, x, y, g, col=OL):
    stamp(img, x, y, GLYPH[g], {"o": col, "w": "white", "d": "drop", "y": "glow", "W": "glow_core", "s": "zzz"})

# ======================================================================= 共同記號：頭頂燈泡＋絨毛
BULB = {"tide": "drop", "shroom": "blush", "crystal": "cyan", "moon": "glow_mid", "ember": "glow_warm", "radiant": "glow",
        "soft": "peach1", "dust": "sick1", "lumi": "leaf", "base": "glow"}
def bulb(sp, x, y, route, r=2.2, stem=2, z=50):
    cv = sp.cv
    if stem: sp.add(cv.caps([(x, y + r), (x, y + r + stem)], 0.6), ["leaf_d", "leaf"], z=z - 1, shade="flat", inner=False)
    sp.add(cv.circ(x, y, r + 0.9), [BULB[route], BULB[route]], z=z, shade="flat")
    sp.add(cv.circ(x - 0.3, y - 0.3, r * 0.55 + 0.3), ["glow_core"], z=z + 1, shade="flat", inner=False)
    sp.anc["bulb"] = cv.p(x, y)
def fluff(sp, x, y, z=40):   # 團絨絨毛：細三撮（family trait）
    cv = sp.cv; sp.add(cv.caps([(x - 1.6, y + 1), (x - 0.8, y - 1)], 0.7) | cv.caps([(x, y + 1), (x + 0.4, y - 1.6)], 0.7) | cv.caps([(x + 1.6, y + 1), (x + 1.4, y - 0.6)], 0.7),
                       ["cream1", "cream3", "cream4"], z=z, shade="flat", inner=False)

# ======================================================================= 9 種原創生物
# 每個 fn(still) → Sprite；guard 44px（k=1）、still 48px（k=1.08，地線對齊）。座標用 44 基準。
def mk(still, S=None):
    if still: S = S or 48; k = 1.08; return Cv(S, k, (S - 44 * k) / 2, S - 44 * k)
    return Cv(S or 44)
GROUND = 42
def sp_tide(still, expr="neutral"):
    cv = mk(still); sp = Sprite(cv); r = 11.5 if not still else 12
    body = cv.circ(22, 30, r) | cv.poly([(22 - r * 0.72, 30 - r * 0.7), (22, 13.5), (22 + r * 0.72, 30 - r * 0.7)])
    sp.add(body, ["drop_d", "drop", "cyan", "white"], z=10)
    sp.add(cv.ell(17, 30, 2.2, 6.5, -8) & body, ["cyan", "white"], z=12, shade="flat", inner=False)           # 透明身反光
    for (x, y, rr) in ((26.5, 36, 1.6), (15.5, 37, 1.1), (27, 24, 1.0)):
        sp.add(cv.circ(x, y, rr) & ~cv.circ(x, y, rr - 0.9), ["white"], z=13, shade="flat", inner=False)        # 身入面細泡
    jets = [((22, 14), (13, 7), (9, 13)), ((22, 14), (31, 7), (35, 13))] + ([((22, 14), (22, 2), (22, 4))] if still else [])
    for p0, p1, p2 in jets[:2]:
        sp.add(cv.caps(cv.bez(p0, p1, p2), 1.3, 0.8), ["drop", "cyan"], z=20, shade="flat")
        sp.add(cv.circ(p2[0], p2[1] + 1.5, 1.4), ["drop", "cyan", "white"], z=21)
    sp.add(cv.ell(16, 41.5, 3, 1.6) | cv.ell(28, 41.5, 3, 1.6), ["drop_d", "drop"], z=9)
    if still:   # 第二形態：泳圈（驚深水）＋三粒水珠頂冠
        ring = cv.ell(22, 35, 16, 4.6) & ~cv.ell(22, 34.4, 12.5, 2.6)
        front = ring & (cv.yy > 34.4 * cv.k + cv.oy)
        sp.add(front, ["berry_d", "white"], z=30, shade="stripe"); sp.add(ring & ~front, ["berry_d", "berry"], z=5, shade="flat")
        for x in (14, 30): sp.add(cv.circ(x, 6, 1.5), ["drop", "cyan", "white"], z=22)
    bulb(sp, 22, 11, "tide", stem=1); fluff(sp, 22, 15.2, z=19)
    sp.anc.update(eyeL=cv.p(18.3, 29), eyeR=cv.p(26.3, 29), mouth=cv.p(22, 32.5), hand=cv.p(33, 32), headR=cv.p(30, 20), top=cv.p(22, 13), ground=cv.p(22, GROUND)[1])
    return sp
def sp_shroom(still, expr="neutral"):
    cv = mk(still); sp = Sprite(cv); rx = 19 if not still else 21
    cap = cv.ell(22, 21, rx, 14) & (cv.yy < cv.p(0, 22.5)[1])
    if still:   # 波浪帽邊
        for i in range(7): cap |= cv.circ(22 - rx + 3 + i * (2 * rx - 6) / 6, 22.5, 2.4)
    sp.add(cap, ["berry_d", "berry", "blush", "white"], z=20)
    for (x, y, r) in ((15, 13, 2.6), (25, 9.5, 2.0), (31, 16, 2.4), (9, 19, 1.5), (21, 17, 1.4)):
        sp.add(cv.circ(x, y, r) & cap, ["cream3", "white"], z=21, shade="flat", inner=False)
    stalk = cv.ell(22, 30, 8.5, 9) & (cv.yy > cv.p(0, 21)[1])
    sp.add(stalk, ["cream0", "cream1", "cream2", "cream4"], z=10)
    if still: sp.add(cv.rect(22 - rx + 3, 22, 22 + rx - 3, 23.6) & ~stalk, ["cream0", "cream1"], z=19, shade="flat")   # 菇褶
    sp.add(cv.ell(17.5, 39.5, 3.2, 2.8) | cv.ell(26.5, 39.5, 3.2, 2.8), ["cream0", "cream1", "cream2"], z=9)
    if still: sp.add(cv.ell(39.5, 27.5, 1.2, 2.0) | cv.circ(39.5, 26, 1.0), ["drop_d", "drop", "white"], z=22)        # 帽邊滴水（自己濕晒）
    bulb(sp, 22, 4.6, "shroom", stem=1.4, z=50); fluff(sp, 22, 8.4, z=24)
    sp.anc.update(eyeL=cv.p(18.5, 28.5), eyeR=cv.p(26, 28.5), mouth=cv.p(22.3, 32), hand=cv.p(31, 33), headR=cv.p(34, 18), top=cv.p(22, 7), ground=cv.p(22, GROUND)[1])
    return sp
def sp_crystal(still, expr="neutral"):
    cv = mk(still); sp = Sprite(cv)
    body = cv.ell(22, 30, 13.5, 12); sp.add(body, ["zzz", "white", "white", "cream4"], z=10)
    sp.add(cv.ell(22, 33.5, 7.5, 6) & body, ["cream3", "cream4"], z=11, shade="flat", inner=False)                     # 肚
    h = 17 if not still else 21
    horn = cv.poly([(19, 19.5), (23.5, 19), (25.5 + h * 0.16, 19 - h), (21, 19 - h * 0.45)])
    sp.add(horn, ["drop_d", "drop", "cyan", "white"], z=20)
    sp.add(cv.poly([(22, 19), (23.2, 19), (25.4 + h * 0.16, 19.6 - h), (24.2 + h * 0.1, 19 - h * 0.55)]) & horn, ["cyan", "white"], z=21, shade="flat", inner=False)
    for (x, y, s_) in ((10, 22, 3.2), (8, 28, 2.6)) + (((35, 21, 2.8),) if still else ()):
        sp.add(cv.poly([(x - s_ * 0.6, y + s_ * 0.6), (x, y - s_), (x + s_ * 0.6, y + s_ * 0.6)]), ["drop_d", "drop", "cyan"], z=8)
    sp.add(cv.ell(16, 41, 3.5, 2.2) | cv.ell(28, 41, 3.5, 2.2), ["zzz", "white"], z=9)
    if still:   # 浮晶片×2
        for (x, y) in ((6, 12), (38, 10)): sp.add(cv.poly([(x, y - 2.6), (x + 1.8, y), (x, y + 2.6), (x - 1.8, y)]), ["drop", "cyan", "white"], z=30)
    bulb(sp, 25.5 + h * 0.16, 17.5 - h, "crystal", r=2.0, stem=0, z=50); fluff(sp, 16, 19.5, z=22)
    sp.anc.update(eyeL=cv.p(17.5, 28), eyeR=cv.p(26.5, 28), mouth=cv.p(22, 31.5), hand=cv.p(34, 32), headR=cv.p(32, 20), top=cv.p(22, 18), ground=cv.p(22, GROUND)[1])
    sp.anc["monocle"] = sp.anc["eyeR"]
    return sp
def sp_moon(still, expr="neutral"):
    cv = mk(still); sp = Sprite(cv); oy = -3 if still else 0
    body = (cv.ell(22, 29 + oy, 16, 11.5) & ~cv.ell(22, 19.5 + oy, 15, 6.5)) | cv.circ(7.6, 25.6 + oy, 2.2) | cv.circ(36.4, 25.6 + oy, 2.2)
    sp.add(body, ["egg_dark", "egg_shade", "glow_mid", "glow_core"], z=10)
    tail = cv.bez((36, 25 + oy), (44, 6 + oy), (27, 9 + oy), 30) if not still else cv.bez((36, 25 + oy), (47, 4 + oy), (26, 6.5 + oy), 30)
    sp.add(cv.caps(tail, 2.6, 1.2), ["zzz", "white"], z=12, shade="stripe")
    pe = tail[-1]
    if still:
        cloud = cv.circ(12, 41, 4.5) | cv.circ(21, 42, 5.5) | cv.circ(31, 41, 4.8) | cv.circ(37, 42, 3.4)
        sp.add(cloud, ["zzz", "white", "white", "cream4"], z=5)
        sp.add(cv.star(pe[0] - 1, pe[1] + 1, 3.4, 1.5), ["egg_shade", "glow", "glow_core"], z=14)
    else:
        sp.add(cv.circ(pe[0] - 1, pe[1] + 1, 2.5), ["cream3", "white"], z=13)
        sp.add(cv.ell(16, 41, 2.6, 1.6) | cv.ell(28, 41, 2.6, 1.6), ["egg_dark", "egg_shade"], z=9)
    bulb(sp, 7.6, 18.5 + oy, "moon", r=2.0, stem=1.6, z=50); fluff(sp, 7.6, 22.6 + oy, z=15)
    sp.anc.update(eyeL=cv.p(17, 30 + oy), eyeR=cv.p(27, 30 + oy), mouth=cv.p(22, 33.5 + oy), hand=cv.p(34, 32 + oy), headR=cv.p(33, 22 + oy), top=cv.p(22, 24 + oy), ground=cv.p(22, GROUND)[1], blush=True)
    return sp
def sp_ember(still, expr="neutral"):
    cv = mk(still); sp = Sprite(cv)
    body = cv.ell(22, 32, 11, 9.5); sp.add(body, ["orange_dd", "orange_d", "orange", "glow_mid"], z=10)
    sp.add(cv.ell(22, 35.5, 6, 4.5) & body, ["peach1", "peach2"], z=11, shade="flat", inner=False)
    big = 1.0 if not still else 1.3
    def flame(cx, base, h, w):
        return cv.poly([(cx - w, base), (cx - w * 1.05, base - h * 0.45), (cx - w * 0.45, base - h * 0.7), (cx - w * 0.2, base - h * 0.55), (cx, base - h),
                        (cx + w * 0.35, base - h * 0.62), (cx + w * 0.8, base - h * 0.78), (cx + w * 1.05, base - h * 0.4), (cx + w, base)]) | cv.ell(cx, base - 1, w, 3)
    fo = flame(22, 25, 19 * big, 8.5 * big)
    if still: fo |= flame(12, 27, 9, 3.5) | flame(32.5, 27, 9, 3.5)
    sp.add(fo, ["berry", "glow_warm", "glow_warm", "glow"], z=8)
    sp.add(flame(22, 24, 13 * big, 5.5 * big), ["glow_warm", "glow", "glow_mid"], z=9, inner=False)
    sp.add(cv.ell(28.5, 30, 2.2, 1.4), ["orange_dd"], z=12, shade="flat", inner=False)                                    # 燒焦印
    sp.add(cv.ell(15, 40.5, 3, 2) | cv.ell(29, 40.5, 3, 2), ["orange_dd", "orange_d"], z=9)
    wand = cv.caps([(33, 36), (39, 27)], 0.7); sp.add(wand, ["outline", "outline"], z=30, shade="flat", inner=False)
    sp.add(cv.circ(39.4, 26.4, 1.2), ["white"], z=31, shade="flat", inner=False)
    if still: sp.add(cv.poly([(18.5, 36.5), (22, 38), (25.5, 36.5), (25.5, 39.8), (22, 38.4), (18.5, 39.8)]), ["berry_d", "berry"], z=13)  # 魔術師煲呔
    bulb(sp, 22, 15 - (3 if still else 0), "ember", r=2.3, stem=0, z=50)
    fluff(sp, 22, 22.6, z=11)
    sp.anc.update(eyeL=cv.p(18, 31), eyeR=cv.p(26, 31), mouth=cv.p(22, 34.5), hand=cv.p(33, 35), headR=cv.p(31, 26), top=cv.p(22, 23), ground=cv.p(22, GROUND)[1])
    return sp
def sp_radiant(still, expr="neutral"):
    cv = mk(still); sp = Sprite(cv)
    tr = 43.5 if not still else 44.5
    cape = cv.poly([(11, 24), (29, 24), (34, 34), (43, tr - 2), (43.5, tr), (20, tr), (7, tr - 1), (9, 32)])
    sp.add(cape, ["berry_d", "berry", "berry", "blush"], z=5)
    if still: sp.add(cv.caps([(7.5, tr - 1.5), (20, tr - 0.7), (43, tr - 1)], 1.4), ["cream3", "white"], z=6, shade="flat")   # 白毛邊
    body = cv.ell(20, 31, 11.5, 10.5); sp.add(body, ["cream0", "cream1", "cream2", "cream4"], z=10)
    sp.add(cv.ell(20, 22.5, 8, 2.4), ["cream3", "white"], z=11, shade="flat")                                              # 披風領
    R = 8.5 if not still else 10
    sp.add(cv.star(20, 13.5 - (1 if still else 0), R, R * 0.45), ["egg_dark", "egg_shade", "glow", "glow_mid"], z=20)
    if still:
        for (x, y, c) in ((16.5, 14, "berry"), (23.5, 14, "cyan")): sp.add(cv.circ(x, y, 1.0), [c], z=21, shade="flat", inner=False)
    sp.add(cv.ell(15.5, 40.5, 3, 2) | cv.ell(25, 40.5, 3, 2), ["cream0", "cream1"], z=9)
    bulb(sp, 20, 13.5 - (1 if still else 0), "radiant", r=1.6, stem=0, z=50)
    sp.anc.update(eyeL=cv.p(16, 30), eyeR=cv.p(24, 30), mouth=cv.p(20, 33.5), hand=cv.p(31, 32), headR=cv.p(29, 22), top=cv.p(20, 21), ground=cv.p(22, GROUND)[1])
    return sp
def sp_soft(still, expr="neutral"):
    cv = mk(still); sp = Sprite(cv); f = -3   # 浮起
    cl = [(13, 28, 7.5), (22, 23.5, 10), (31, 28, 7.5), (22, 31, 8.5)] + ([(7, 33, 4.5), (37, 33, 4.5), (31, 19, 5)] if still else [])
    m = np.zeros((cv.S, cv.S), bool)
    for x, y, r in cl: m |= cv.circ(x, y + f, r)
    # 「以為自己隱咗身」：下緣 2 行棋盤透明；每團雲獨立打光（鼓鼓哋）
    ys = np.nonzero(m.any(1))[0]; yb = ys.max(); chk = ((cv.xx.astype(int) + cv.yy.astype(int)) % 2 == 0) & (cv.yy.astype(int) >= yb - 1)
    for i, (x, y, r) in enumerate(sorted(cl, key=lambda c: c[1])):
        sp.add(cv.circ(x, y + f, r) & ~chk, ["cream2", "cream4", "white", "white"], z=10 + i * 0.1, inner=False)
    if still: sp.add(cv.caps(cv.bez((38, 30 + f), (46, 26 + f), (42, 20 + f)), 1.3, 0.6), ["cream2", "white"], z=9, shade="flat")
    sp.add(cv.ell(22, 42.5, 8, 1.2), ["cream1", "cream1"], z=1, shade="flat", inner=False)                                    # 影（浮住）
    bulb(sp, 22, 9.5 + f, "soft", r=2.0, stem=1.6, z=50); fluff(sp, 22, 13.2 + f, z=15)
    sp.anc.update(eyeL=cv.p(18, 27 + f), eyeR=cv.p(26, 27 + f), mouth=cv.p(22, 30.5 + f), hand=cv.p(33, 29 + f), headR=cv.p(30, 18 + f), top=cv.p(22, 14 + f), ground=cv.p(22, GROUND)[1])
    return sp
def sp_dust(still, expr="neutral"):
    cv = mk(still); sp = Sprite(cv); r = 7.5 if not still else 9.5; cy = GROUND - r - 2
    th = np.arctan2(cv.yy - cv.p(22, cy)[1], cv.xx - cv.p(22, cy)[0]); d = np.hypot(cv.xx - cv.p(22, cy)[0], cv.yy - cv.p(22, cy)[1]) / cv.k
    rr = r + 1.4 * (np.abs(np.sin(th * 7)) ** 3)                                                                          # 亂毛波
    sp.add(d <= rr, ["sick0", "sick1", "white", "white"], z=10)
    sp.add(cv.ell(18.5, GROUND - 0.8, 1.6, 1.2) | cv.ell(25.5, GROUND - 0.8, 1.6, 1.2), ["sick0", "sick1"], z=9)
    # 獨立：細孭包（棍＋包袱）
    sp.add(cv.caps([(27, cy + 3), (35, cy - 9)], 0.6), ["orange_dd", "orange_d"], z=30, shade="flat", inner=False)
    sp.add(cv.circ(35.5, cy - 9.5, 3.2 if not still else 3.8), ["berry_d", "berry", "blush"], z=31)
    sp.dec(*cv.p(35, cy - 10), "white"); sp.dec(*cv.p(36.5, cy - 8.5), "white")
    if still:
        sp.add(cv.caps([(14, cy + 2.5), (22, cy + 4), (30, cy + 2.5)], 1.2), ["leaf_d", "leaf"], z=20, shade="flat")      # 頸巾（扮流浪）
        for (x, y) in ((8, GROUND - 2), (11, GROUND - 6), (6, GROUND - 8)): sp.add(cv.circ(x, y, 1.0), ["sick1"], z=2, shade="flat")
    bulb(sp, 22, cy - r - 7.5, "dust", r=1.8, stem=4, z=50); fluff(sp, 22, cy - r - 1.5, z=15)
    sp.anc.update(eyeL=cv.p(19, cy - 0.5), eyeR=cv.p(25.5, cy - 0.5), mouth=cv.p(22.3, cy + 2.5), hand=cv.p(28, cy + 2), headR=cv.p(28, cy - r), top=cv.p(22, cy - r), ground=cv.p(22, GROUND)[1])
    return sp
SPECIES = {   # route → (名, 種族, fn, 剪影一句, 扮醒 gag)
    "tide": ("水珠", "滴滴波", sp_tide, "倒轉水滴＋頭頂兩條噴泉鬚，透明身", "自封海洋之王，第二形態要戴泳圈（驚深水）"),
    "shroom": ("菇傘", "傘咕", sp_shroom, "超闊紅白點菇帽＋細莖身＋兩粒短莖腳", "落雨擘大個傘扮保護你，帽邊滴水自己濕晒"),
    "crystal": ("晶角", "碎碎角", sp_crystal, "圓糰身＋一支斜斜大水晶角＋背後細晶片", "戴晶片當單片眼鏡扮學者"),
    "moon": ("月眠", "眠眠嚧", sp_moon, "仰面半月碗身＋條間條睡帽尾（尾尖波波）", "瞇眼話「我喺度思考」，其實瞓緊"),
    "ember": ("火苗", "燒燒噚", sp_ember, "細豆身頂住一團比身高嘅火（興奮就大）", "扮魔術師，魔術棒揮兩下就燒到自己"),
    "radiant": ("燦光", "閃閃冠", sp_radiant, "五角星冠＋拖地過長披風（剪影向右拖長）", "自稱王者，成日踩到自己披風"),
    "soft": ("柔光", "棉棉霧", sp_soft, "雲團身浮離地面，下緣漸散（冇腳）", "以為自己隱咗身（其實好明顯）"),
    "dust": ("微塵", "灰灰粒", sp_dust, "極細亂毛球＋長天線燈泡＋孭包袱", "要人照顧但自信話「我好獨立」"),
    "lumi": ("螢絨", "螢螢翼", None, "沿用已批螢絨：背後翼＋觸角燈＋尾燈（隱藏）", "以為自己識飛，拍翼拍到攰都係離地 1px"),
}
ROUTES = ["tide", "shroom", "crystal", "moon", "ember", "radiant", "soft", "dust", "lumi"]

def lumi_frame(still):
    """螢螢翼＝沿用已批 evo_guard_lumi／evo_still_lumi idle_01；概念圖用最近 v3 色顯示（原 atlas 唔改）"""
    f = "evo_still_lumi" if still else "evo_guard_lumi"; a = np.array(Image.open(os.path.join(TR, "evo6", f, "frames", "idle_01.png")).convert("RGBA"))
    pal = np.array(sorted(V3)); op = a[..., 3] > 0; c = a[op][:, :3].astype(int)
    d = ((c[:, None, :] - pal[None]) ** 2).sum(-1); a[op, :3] = pal[d.argmin(1)]; a[..., 3] = np.where(op, 255, 0); return a
def species_img(route, still, expr="neutral"):
    if route == "lumi":
        a = lumi_frame(still); S = a.shape[0]
        an = json.load(open(os.path.join(TR, "evo6", "evo_still_lumi" if still else "evo_guard_lumi", f"face_anchors_{'evo_still_lumi' if still else 'evo_guard_lumi'}.json")))
        return a, {"lumi": True, "S": S, "raw": an}
    sp = SPECIES[route][2](still); img = sp.render(); an = dict(sp.anc); an["S"] = sp.cv.S
    face(img, an, expr, big=True); return img, an

# ======================================================================= 共用幼年（光卵→絨點→絨芽→絨跳＋一個種族小特徵）
def base_body(cv, sp, cx, cy, rx, ry, z=10):
    sp.add(cv.ell(cx, cy, rx, ry), ["cream0", "cream1", "cream2", "cream4"], z=z)
    sp.add(cv.ell(cx, cy + ry * 0.4, rx * 0.55, ry * 0.42), ["cream3", "cream4"], z=z + 1, shade="flat", inner=False)
def stage_img(stage, route="base"):
    if stage == 1:
        cv = Cv(24); sp = Sprite(cv); sp.add(cv.ell(12, 13, 8.5, 10), ["egg_dark", "egg_shade", "glow", "glow_mid"], z=10)
        sp.add(cv.caps([(6, 11), (9, 13), (12, 10), (15, 13), (18, 11)], 0.5), ["egg_dark"], z=11, shade="flat", inner=False)
        sp.add(cv.circ(12, 17, 2), ["glow_mid", "glow_core"], z=12, shade="flat", inner=False); img = sp.render(); return img
    if stage == 2:
        cv = Cv(28); sp = Sprite(cv); base_body(cv, sp, 14, 16, 8.5, 7.5)
        sp.add(cv.ell(14, 22, 10, 5.5) & (cv.yy > 19), ["egg_dark", "egg_shade", "glow"], z=20)
        sp.add(cv.poly([(4, 19.5), (7, 17), (9, 19.5), (12, 17), (15, 19.5), (18, 17), (21, 19.5), (24, 17), (24.5, 20), (4, 20)]), ["egg_dark", "egg_shade", "glow"], z=20)
        img = sp.render(); face(img, {"eyeL": (11, 14), "eyeR": (17, 14), "mouth": (14, 16.5)}); return img
    if stage == 3:
        cv = Cv(32); sp = Sprite(cv); base_body(cv, sp, 16, 21, 9.5, 8.5)
        sp.add(cv.ell(12.5, 9, 3.8, 2.0, -30) | cv.ell(19.5, 9, 3.8, 2.0, 30), ["leaf_d", "leaf"], z=12)
        sp.add(cv.caps([(16, 13), (16, 11)], 0.6), ["leaf_d"], z=11, shade="flat")
        sp.add(cv.ell(11.5, 30, 2.6, 1.6) | cv.ell(20.5, 30, 2.6, 1.6), ["cream0", "cream1"], z=9)
        img = sp.render(); face(img, {"eyeL": (13, 20), "eyeR": (19.5, 20), "mouth": (16.3, 23)}); return img
    # stage 4 絨跳 38px：尖耳＋捲尾＋燈泡（路線色）＋一個小特徵
    cv = Cv(38); sp = Sprite(cv); base_body(cv, sp, 19, 25, 11, 10)
    if route != "shroom":
        sp.add(cv.poly([(10, 19), (11, 9.5), (15.5, 16)]) | cv.poly([(28, 19), (27, 9.5), (22.5, 16)]), ["cream0", "cream1", "cream2"], z=9)
    sp.add(cv.caps(cv.bez((29, 30), (36, 28), (33, 22)), 1.4, 1.0), ["cream0", "cream1", "cream2"], z=8)
    sp.add(cv.circ(33, 21.5, 1.6), ["orange_d", "orange"], z=8)
    sp.add(cv.ell(14, 35.5, 2.8, 1.7) | cv.ell(24, 35.5, 2.8, 1.7), ["cream0", "cream1"], z=9)
    by = 8.5
    if route == "tide":
        sp.add(cv.caps(cv.bez((19, 14), (14, 9), (12, 13)), 0.8, 0.5), ["drop", "cyan"], z=12, shade="flat"); sp.add(cv.circ(12, 14, 1.0), ["drop", "cyan"], z=12)
    elif route == "shroom":
        sp.add(cv.ell(19, 15.5, 9, 5) & (cv.yy < 16.5), ["berry_d", "berry", "blush"], z=12); sp.add(cv.circ(15.5, 13.5, 1.2) | cv.circ(22.5, 12.8, 1.0), ["white"], z=13, shade="flat", inner=False); by = 7.5
    elif route == "crystal":
        sp.add(cv.poly([(23, 16.5), (25, 16.2), (27.5, 9.5)]), ["drop_d", "drop", "cyan"], z=12)
    elif route == "moon":
        sp.add(cv.caps(cv.bez((29, 30), (36, 28), (33, 22)), 1.5, 1.0), ["zzz", "white"], z=8.5, shade="stripe"); sp.add(cv.circ(33, 21, 1.8), ["cream3", "white"], z=9)
    elif route == "ember":
        sp.add(cv.poly([(31, 23), (32, 17), (33.5, 20.5), (35, 16.5), (35.5, 23)]) | cv.circ(33.3, 22, 2), ["glow_warm", "glow", "glow_mid"], z=9)
    elif route == "radiant":
        sp.add(cv.star(19, by, 4.6, 2.0), ["egg_dark", "egg_shade", "glow"], z=12)
    elif route == "soft":
        sp.add(cv.circ(33, 25, 2.6) | cv.circ(35.5, 22.5, 2.2) | cv.circ(31, 22, 2.0), ["cream2", "white", "white"], z=9)
    elif route == "dust":
        sp.add(cv.caps([(14, 16), (13, 12)], 0.8) | cv.caps([(17, 15), (17.5, 10.5)], 0.8) | cv.caps([(23, 15.5), (25, 12)], 0.8), ["sick0", "sick1"], z=12, shade="flat")
    elif route == "lumi":
        sp.add(cv.ell(8.5, 22, 3.6, 2.2, -35) | cv.ell(29.5, 21, 3.6, 2.2, 35), ["zzz", "white", "cyan"], z=7)
    bulb(sp, 19, by, route if route != "base" else "base", r=2.0, stem=2.4, z=50)
    img = sp.render(); face(img, {"eyeL": (15.5, 24), "eyeR": (23, 24), "mouth": (19.3, 27.5)}, big=True); return img

# ======================================================================= 道具（扮醒 kit）
def prop(img, an, kind):
    S = img.shape[0]; cv = Cv(S); sp = Sprite(cv)
    (lx, ly), (rx, ry) = an["eyeL"], an["eyeR"]; tx, ty = an["top"]; hx, hy = an["hand"]; ex, ey = an["headR"]
    if kind == "glasses":   # 歪咗嘅眼鏡（一邊高一邊低）
        r = 2.6; m = (cv.circ(lx, ly - 0.5, r + 0.8) & ~cv.circ(lx, ly - 0.5, r - 0.2)) | (cv.circ(rx, ry + 1.2, r + 0.8) & ~cv.circ(rx, ry + 1.2, r - 0.2))
        m |= cv.caps([(lx + r, ly - 0.5), (rx - r, ry + 1.2)], 0.4); sp.add(m, ["orange_dd"], z=1, shade="flat", inner=False)
    elif kind == "book":    # 倒轉書：封面向觀眾，書名「∀」同書名線都倒轉
        bx, by_ = hx - 3, hy - 6; sp.add(cv.rect(bx - 5, by_ - 4, bx + 5, by_ + 5), ["leaf_d", "leaf"], z=1, shade="flat")
        sp.add(cv.rect(bx + 4, by_ - 3, bx + 5.5, by_ + 4), ["cream3", "white"], z=2, shade="flat", inner=False)
    elif kind == "gradcap": # 過大學士帽
        w = 10; sp.add(cv.poly([(tx - w, ty - 5), (tx, ty - 9), (tx + w, ty - 5), (tx, ty - 1.5)]), ["outline", "zzz"], z=2, shade="flat")
        sp.add(cv.rect(tx - 5, ty - 4, tx + 5, ty + 0.5), ["outline", "outline"], z=1, shade="flat", inner=False)
        sp.add(cv.caps([(tx + 1, ty - 5.5), (tx + w + 1, ty - 3), (tx + w + 1.5, ty + 3)], 0.5), ["glow", "glow"], z=3, shade="flat", inner=False)
        sp.add(cv.circ(tx + w + 1.5, ty + 3.8, 1.2), ["egg_shade", "glow"], z=3, shade="flat", inner=False)
    elif kind == "pencil":  # 耳後鉛筆
        sp.add(cv.caps([(ex - 4, ey + 3), (ex + 5, ey - 4)], 0.9), ["egg_shade", "glow"], z=1, shade="flat")
        sp.add(cv.circ(ex - 4.2, ey + 3.2, 1.0), ["berry"], z=2, shade="flat", inner=False); sp.add(cv.circ(ex + 5.4, ey - 4.3, 0.8), ["peach1"], z=2, shade="flat", inner=False)
    elif kind == "magnifier":  # 揸錯邊嘅放大鏡（揸住鏡、把手向外）
        sp.add(cv.circ(hx, hy, 3.0) & ~cv.circ(hx, hy, 1.8), ["orange_dd"], z=1, shade="flat", inner=False)
        sp.add(cv.circ(hx, hy, 1.8), ["drop", "cyan"], z=1, shade="flat", inner=False)
        sp.add(cv.caps([(hx + 2.5, hy - 2.5), (hx + 7, hy - 7)], 0.8), ["orange_dd", "orange_d"], z=1, shade="flat", inner=False)
    elif kind == "chalk":   # 細黑板 1+1=3
        bx, by_ = hx - 2, hy - 13; sp.add(cv.rect(bx - 1, by_ - 1, bx + 21, by_ + 8), ["orange_dd", "orange_dd"], z=1, shade="flat")
        sp.add(cv.rect(bx, by_, bx + 20, by_ + 7), ["leaf_d", "leaf_d"], z=2, shade="flat", inner=False)
    elif kind == "monocle":
        sp.add(cv.circ(rx, ry, 3.4) & ~cv.circ(rx, ry, 2.3), ["drop", "cyan"], z=1, shade="flat", inner=False)
        sp.add(cv.caps([(rx + 2.5, ry + 2), (rx + 3.5, ry + 7)], 0.4), ["glow"], z=1, shade="flat", inner=False)
    elif kind == "umbrella":  # 傘咕：撐起菇帽扮保護你，自己濕晒（雨點）
        pass
    pm = sp.render(outline=kind not in ("glasses", "monocle", "magnifier"))
    out = img.copy(); m = pm[..., 3] > 0; out[m] = pm[m]
    if kind == "chalk":
        x0, y0 = int(round(hx - 1)), int(round(hy - 12))
        for i, g in enumerate("1+1=3"): glyph(out, x0 + i * 4, y0, g, "white")
    if kind == "book":
        bx, by_ = int(hx - 3), int(hy - 6)
        stamp(out, bx - 3, by_ - 2, ["o...o", "o...o", "ooooo", ".o.o.", "..o.."], {"o": "white"})   # 倒轉「A」
        for i in range(5): px(out, bx - 3 + i, by_ + 4, "glow")                                          # 書名線喺底（倒轉）
    return out
def gpos(img):
    """表情符號位：sprite 外框右上（避開身上配件）"""
    ys, xs = np.nonzero(img[..., 3]); W = img.shape[1]; return min(int(xs.max()) + 2, W - 4), max(int(ys.min()) + 2, 2)
def pad(img, P):
    S = img.shape[0]; o = np.zeros((S + 2 * P, S + 2 * P, 4), np.uint8); o[P:P + S, P:P + S] = img; return o
GAG = {"tide": ("caught", ["sweat"]), "shroom": ("proud_wrong", ["rain"]), "crystal": ("smug", ["monocle"]), "moon": ("think_asleep", ["z"]),
       "ember": ("caught", ["smoke"]), "radiant": ("proud_wrong", ["trip"]), "soft": ("smug", ["hide"]), "dust": ("proud_wrong", ["!"]), "lumi": ("lecture", [])}
def gag_img(route):
    expr, fx = GAG[route]
    if route == "lumi": img, an = species_img("lumi", True)
    else:
        img, an = species_img(route, True, expr)
    img = pad(img, 8); S = img.shape[0]; o = 8
    if route == "crystal": img = pad(prop(img[8:-8, 8:-8], an, "monocle"), 8)
    gx, gy = gpos(img)
    if "sweat" in fx: glyph(img, gx, gy + 8, "sweat")
    if "z" in fx: glyph(img, an["top"][0] + o + 8, an["top"][1] + o - 14, "z", "zzz"); glyph(img, an["top"][0] + o + 13, an["top"][1] + o - 19, "z", "zzz")
    if "smoke" in fx: glyph(img, an["hand"][0] + o + 5, an["hand"][1] + o - 14, "smoke"); glyph(img, an["hand"][0] + o + 2, an["hand"][1] + o - 18, "smoke")
    if "!" in fx: glyph(img, gx, gy, "!")
    if "rain" in fx:
        for (x, y) in ((6, 4), (14, 1), (40, 3), (50, 7), (3, 14), (55, 16), (46, 20)): stamp(img, x, y, ["d", "d", "."], {"d": "drop"})
        glyph(img, 30, 2, "spark")
    if "trip" in fx:   # 踩到披風：成隻向前傾
        im = Image.fromarray(img).rotate(-14, resample=Image.NEAREST, center=(S / 2, S - 8)); img = np.array(im); glyph(img, 8, 10, "sweat")
    if "hide" in fx:   # 以為隱身：成隻棋盤隱一半（alpha 0/255）
        yy, xx = np.mgrid[0:S, 0:S]; img[((xx + yy) % 2 == 0) & (yy > S * 0.55), 3] = 0
    if route == "lumi": glyph(img, 6, 6, "!")
    return img

# ======================================================================= 表單工具
def font(sz):
    for p in ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc", "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc"):
        if os.path.exists(p): return ImageFont.truetype(p, sz)
    return ImageFont.load_default()
BG = rgb("cream3"); BG2 = rgb("cream2")
def text(d, xy, s, sz=13, col=OL, anchor="la"):
    d.fontmode = "1"; d.text(xy, s, font=font(sz), fill=rgb(col), anchor=anchor)
def grid(rows, cell, scale, rowlab=None, collab=None, title=None, lw=110, ground=None):
    """rows: list of list of RGBA（每格置中、貼底）；全部 v3（底色 cream3／cream2 交替），alpha 255"""
    th = 30 if title else 0; ch = 22 if collab else 0; nr = len(rows); nc = max(len(r) for r in rows); C = cell * scale
    W = (lw if rowlab else 0) + nc * C; H = th + ch + nr * C
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    if title: text(d, (8, 6), title, 15)
    if collab:
        for j, s in enumerate(collab): text(d, ((lw if rowlab else 0) + j * C + C // 2, th + 3), s, 12, anchor="ma")
    for i, r in enumerate(rows):
        y0 = th + ch + i * C
        if rowlab: text(d, (6, y0 + C // 2 - 16), rowlab[i][0], 14); text(d, (6, y0 + C // 2 + 2), rowlab[i][1], 12, "orange_dd") if len(rowlab[i]) > 1 else None
        for j, c in enumerate(r):
            x0 = (lw if rowlab else 0) + j * C
            if (i + j) % 2: d.rectangle([x0, y0, x0 + C - 1, y0 + C - 1], fill=BG2)
            if c is None: continue
            h, w = c.shape[:2]; big = Image.fromarray(c).resize((w * scale, h * scale), Image.NEAREST)
            px_ = x0 + (C - w * scale) // 2; py_ = y0 + C - h * scale - (ground if ground is not None else (C - h * scale) // 2)
            im.paste(big, (px_, py_), big)
    return im

# ======================================================================= 輸出
def build_sprites():
    os.makedirs(SPR, exist_ok=True); meta = {}
    for r in ROUTES:
        for still in (False, True):
            img, an = species_img(r, still); nm = f"sp_{r}_{'still_48' if still else 'guard_44'}.png"
            Image.fromarray(img).save(os.path.join(SPR, nm)); meta.setdefault(r, {})["still" if still else "guard"] = {"file": f"sprites/{nm}", "anchors": {k: (list(v) if isinstance(v, tuple) else v) for k, v in an.items() if k != "raw"}}
        h = stage_img(4, r); Image.fromarray(h).save(os.path.join(SPR, f"hop_{r}_38.png")); meta[r]["hop"] = {"file": f"sprites/hop_{r}_38.png"}
    for st, S in ((1, 24), (2, 28), (3, 32)): Image.fromarray(stage_img(st)).save(os.path.join(SPR, f"stage{st}_shared_{S}.png"))
    json.dump({"note": "概念 sprite（idle 單幀）。lumi 為已批設計（顯示用最近 v3 色），其餘原創。anchors 係 sprite 座標（px）。",
               "routes": {r: dict(meta[r], name=SPECIES[r][0], species=SPECIES[r][1], silhouette=SPECIES[r][3], gag=SPECIES[r][4]) for r in ROUTES}},
              open(os.path.join(OUT, "species.json"), "w"), ensure_ascii=False, indent=1, default=lambda o: float(o))
def build_sheets():
    os.makedirs(PRV, exist_ok=True); P = []
    sh = [stage_img(1), stage_img(2), stage_img(3)]
    rows = [[sh[0], sh[1], sh[2], stage_img(4, r), species_img(r, False)[0], species_img(r, True)[0]] for r in ROUTES]
    im = grid(rows, 52, 3, [(SPECIES[r][0], SPECIES[r][1]) for r in ROUTES], ["1 光卵", "2 絨點", "3 絨芽", "4 絨跳＋小特徵", "5 守夜者＝變種族", "6 靜光＝第二形態"],
              "團絨變種族：進化鏈（1–3 共用；4 只長一個小特徵；5 起剪影完全唔同）", lw=120, ground=6)
    p = os.path.join(PRV, "species_transform_sheet_3x.png"); im.save(p); P.append(p)
    # lineup：靜光一排、守夜者一排
    im = grid([[species_img(r, True)[0] for r in ROUTES], [species_img(r, False)[0] for r in ROUTES]], 54, 3, [("靜光", "第二形態"), ("守夜者", "變種族")],
              [f"{SPECIES[r][1]}（{SPECIES[r][0]}）" for r in ROUTES], "9 種原創團絨種族 lineup（3x）", lw=96, ground=6)
    p = os.path.join(PRV, "species_lineup_3x.png"); im.save(p); P.append(p)
    # 剪影比較
    def sil(a): o = a.copy(); o[o[..., 3] > 0, :3] = rgb(OL); return o
    im = grid([[sil(species_img(r, False)[0]) for r in ROUTES]], 54, 3, None, [SPECIES[r][1] for r in ROUTES], "剪影一眼分（守夜者 44px，實心 outline 色）", ground=6)
    p = os.path.join(PRV, "species_silhouettes_3x.png"); im.save(p); P.append(p)
    # 表情 kit：3 種 × 6 表情
    ex = ["smug", "proud_wrong", "confused_conf", "think_asleep", "caught", "lecture"]
    exl = ["得意半瞇", "自信答錯", "唔明扮明", "諗緊（瞓著）", "被拆穿", "講大道理"]
    def exfx(r, e):
        img, an = species_img(r, False, e); img = pad(img, 10); gx, gy = gpos(img)
        g = {"confused_conf": ("?", OL), "think_asleep": ("z", "zzz"), "caught": ("sweat", OL), "proud_wrong": ("spark", OL), "lecture": ("!", OL), "smug": ("spark", OL)}[e]
        glyph(img, gx, gy, *g); return img
    kr = ["tide", "moon", "radiant"]
    im = grid([[exfx(r, e) for e in ex] for r in kr], 64, 3, [(SPECIES[r][1], SPECIES[r][0]) for r in kr], exl, "「扮好聰明但其實呆呆地」表情 kit（6 款，眼／眉／口 rig 共用）", lw=96, ground=4)
    p = os.path.join(PRV, "kit_expressions_3x.png"); im.save(p); P.append(p)
    pr = ["glasses", "book", "gradcap", "pencil", "magnifier", "chalk"]; prl = ["歪眼鏡", "倒轉書", "過大學士帽", "耳後鉛筆", "揸錯放大鏡", "黑板 1+1=3"]
    pexp = {"glasses": "smug", "book": "lecture", "gradcap": "proud_wrong", "pencil": "confused_conf", "magnifier": "lecture", "chalk": "proud_wrong"}
    def pimg(r, k):
        img, an = species_img(r, False, pexp[k]); img = pad(img, 10)
        an2 = {kk: ((v[0] + 10, v[1] + 10) if isinstance(v, tuple) else v) for kk, v in an.items()}; return prop(img, an2, k)
    pr_r = ["crystal", "shroom", "dust"]
    im = grid([[pimg(r, k) for k in pr] for r in pr_r], 64, 3, [(SPECIES[r][1], SPECIES[r][0]) for r in pr_r], prl, "扮醒道具 kit（6 件，用 eye／top／hand／headR 錨點）", lw=96, ground=4)
    p = os.path.join(PRV, "kit_props_3x.png"); im.save(p); P.append(p)
    im = grid([[gag_img(r) for r in ROUTES]], 70, 3, None, [f"{SPECIES[r][1]}" for r in ROUTES], "每種族專屬「扮醒」gag（靜光形態）", ground=4)
    p = os.path.join(PRV, "kit_species_gags_3x.png"); im.save(p); P.append(p)
    return P

# ======================================================================= HD-2D 場景（分層＋景深＋光，全部烘入圖層）
def blur(a, r): return np.array(Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))).astype(float) / 255 if r else a
def over(dst, rgbA):   # rgbA float HxWx4
    a = rgbA[..., 3:4]; return dst * (1 - a) + rgbA[..., :3] * a
def noise(H, W, sc, seed):
    rs = np.random.RandomState(seed); g = rs.rand(H // sc + 3, W // sc + 3)
    return np.array(Image.fromarray((g * 255).astype(np.uint8)).resize((W + 3 * sc, H + 3 * sc), Image.BICUBIC)).astype(float)[:H, :W] / 255
STYLE = {
    "base": dict(sky=("#9CD3F5", "#FDF3D8"), far="#B9D8C6", hill=("#8FC79A", "#6BAE7E"), ground=("#A8D48E", "#7DB86E"), path="#F3E3BC", tree=("#5E9E6A", "#7DBB7A"),
                 trunk="#8A5A44", house=("#F6DDB0", "#E5584D"), water=("#7FC4E8", "#4FA3D9"), fg="#3F7A50", flower=("#FFFFFF", "#FFD45E", "#F28B9B"), light="#FFF1CC", lamp="#FFD45E", bloom=0.35, shadow="#3B2A3E"),
    "dreamy": dict(sky=("#BBA9EE", "#FFE1EE"), far="#D8CBF4", hill=("#C3CCF4", "#A9B4EA"), ground=("#F6DCEC", "#E6C3E2"), path="#FFF4FA", tree=("#A496E0", "#C9B8F4"),
                   trunk="#9C7FB8", house=("#FFF1F7", "#F2A0C4"), water=("#C9E6FF", "#A4C8F4"), fg="#8F82D2", flower=("#FFFFFF", "#FFE6A8", "#FFB8D8"), light="#FFF4FA", lamp="#FFE9B0", bloom=0.8, shadow="#7A5FA8"),
    "water": dict(sky=("#9FCBE6", "#FBF0DA"), far="#C9D6C2", hill=("#A9C6A8", "#93B596"), ground=("#D6DDB0", "#C2CD99"), path="#F1E6CC", tree=("#88AE8C", "#A5C49F"),
                  trunk="#9A7458", house=("#F2E2C4", "#D98471"), water=("#A9CFE0", "#86B5CF"), fg="#7E9F7E", flower=("#FFFDF5", "#F3CF7A", "#E9A3A3"), light="#FFF3DC", lamp="#F7D58A", bloom=0.18, shadow="#7A5A4A"),
    "candy": dict(sky=("#4B3FA8", "#FF9FC8"), far="#8C7CF0", hill=("#3FD0C6", "#1F9C9C"), ground=("#FFB3D6", "#F27EB6"), path="#FFE6F3", tree=("#6C5CE0", "#9C8CFF"),
                  trunk="#B0507E", house=("#FFF0FA", "#FF4F7B"), water=("#7FF0FF", "#2FB8E8"), fg="#3A2CB0", flower=("#FFFFFF", "#FFE45E", "#FF6FA8"), light="#FFFFFF", lamp="#FFF27A", bloom=0.6, shadow="#3A1E6E"),
}
STYLE.update({
    "paper": dict(sky=("#F6D3AE", "#FAEBD2"), far="#E9B48C", hill=("#DB8E68", "#C97656"), ground=("#A3C48A", "#8DB177"), path="#F7E8C8", tree=("#3F8466", "#62A57A"),
                  trunk="#6E4434", house=("#FFF3DE", "#E0503F"), water=("#79C0D6", "#55A4C0"), fg="#2C6450", flower=("#FFFFFF", "#FFD45E", "#F28B9B"), light="#FFF6E2", lamp="#FFD45E", bloom=0.15, shadow="#5A3626"),
    "felt": dict(sky=("#B9D6E8", "#F2E4D2"), far="#B3C7AC", hill=("#8FB67A", "#7AA267"), ground=("#A7C877", "#90B563"), path="#E8D1A8", tree=("#5A9152", "#79AB66"),
                 trunk="#87593F", house=("#F5E4C8", "#D6504C"), water=("#88C2DF", "#66A6CB"), fg="#4A7A43", flower=("#FFFFFF", "#FFD873", "#F59AA8"), light="#FFF3DA", lamp="#FFD873", bloom=0.25, shadow="#4A3838"),
    "neon": dict(sky=("#0B0926", "#2E1950"), far="#1E1850", hill=("#17174A", "#100D33"), ground=("#0F2A3C", "#0B1C2C"), path="#2A2266", tree=("#3A1E6E", "#2C1858"),
                 trunk="#24183E", house=("#22204A", "#5A1E4A"), water=("#123E7A", "#0C2A5A"), fg="#07061A", flower=("#7FF0E0", "#FF7AD9", "#FFE45E"), light="#9FB8FF", lamp="#FFD45E", bloom=1.1, shadow="#000010"),
    "enamel": dict(sky=("#6FAEDC", "#D2E8F2"), far="#C3CFE6", hill=("#5BA897", "#469282"), ground=("#8ACB8D", "#73B579"), path="#F6E1BE", tree=("#2C7A68", "#3C9880"),
                   trunk="#874A37", house=("#FFF5E4", "#D63F4C"), water=("#4FA3D9", "#2C7DBE"), fg="#1D5A4F", flower=("#FFFFFF", "#FFD45E", "#F28B9B"), light="#FFF8E8", lamp="#FFD45E", bloom=0.2, shadow="#3B2A3E"),
})
GOLD, GOLD_HI, GOLD_D = "#E2B04A", "#FFE6A3", "#9C6B1E"
PADSTY = {"paper": 2, "enamel": 1, "felt": 0, "neon": 0}
def erode(m, k=1):
    for _ in range(k): m = m & shift(m, 1) & shift(m, -1) & shift(m, 0, 1) & shift(m, 0, -1)
    return m
def dilate(m, k=1):
    for _ in range(k): m = m | shift(m, 1) | shift(m, -1) | shift(m, 0, 1) | shift(m, 0, -1)
    return m
LAST_BOX = []
def hx(h): return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float) / 255
def shift(m, dy, dx=0):
    o = np.zeros_like(m)
    H, W = m.shape; ys = slice(max(0, dy), H + min(0, dy)); yd = slice(max(0, -dy), H + min(0, -dy)); xs = slice(max(0, dx), W + min(0, dx)); xd = slice(max(0, -dx), W + min(0, -dx))
    o[ys, xs] = m[yd, xd]; return o
def scene(style, W, H, sprites, seed=3, gy=None, lampx=0.86):
    """HD-2D 分層：遠景（強 DoF）→中景→焦點地面＋角色（清晰）→前景（最強 DoF）；光束／燈暈／bloom 全部烘入圖層（canvas2D 冇 shader）。
    sprites: list of (img RGBA uint8, x_center, y_ground, depth 0..1)。回傳 uint8 RGB。"""
    st = STYLE[style]; yy, xx = np.mgrid[0:H, 0:W].astype(float); t = yy / H; rs = np.random.RandomState(seed)
    paper = 0.955 + 0.045 * noise(H, W, 2, 21) + 0.02 * noise(H, W, 1, 22) if style == "water" else None
    gy = H * 0.66 if gy is None else gy
    def grad(c0, c1, m=None):
        if m is not None and m.any():
            ys = np.nonzero(m.any(1))[0]; tt = np.clip((yy - ys.min()) / max(1, ys.max() - ys.min()), 0, 1)
        else: tt = t
        return hx(c0) * (1 - tt[..., None]) + hx(c1) * tt[..., None]
    C = grad(*st["sky"])
    if style == "water": C = C * 0.85 + hx("#FBF6EA") * 0.15
    NE = np.zeros((H, W, 3)); HALO = np.zeros((H, W, 3)); SPM = np.zeros((H, W)); LAST_BOX.clear()
    fib = (0.97 + 0.03 * noise(H, W, 1, 41)) if style == "paper" else None
    if style == "paper": C = C * fib[..., None]
    if style == "felt": C = C * (0.93 + 0.08 * noise(H, W, 1, 43))[..., None]
    if style == "neon":   # 月亮＋星
        moon_ = ((xx - W * 0.74) ** 2 + (yy - H * 0.14) ** 2 < 13 ** 2) & ~((xx - W * 0.74 - 6) ** 2 + (yy - H * 0.14 + 3) ** 2 < 12 ** 2)
        C[moon_] = hx("#FFF2B8"); NE += moon_[..., None] * hx("#FFE9A0") * 0.8
        for _ in range(60):
            x, y = rs.randint(0, W), rs.randint(0, int(H * 0.55)); C[y, x] = hx(["#FFFFFF", "#9FB8FF", "#FF9FE0"][rs.randint(3)])
    def paint(C, m, col, r=0.0, alpha=1.0):
        """按風格畫一層：col 可以係 HxWx3 或 hex"""
        c = hx(col) * np.ones((H, W, 3)) if isinstance(col, str) else col.copy(); a = m.astype(float)
        if style == "paper" and m.any():   # 剪紙：平塗 2 階＋左上切口白邊＋落影（烘入下一層）
            mc = c[m].mean(0); c[:] = mc; c[m & (yy > (np.nonzero(m.any(1))[0].mean() + 6))] = mc * 0.92
            cut = m & ~shift(m, 1, 1); c[cut] = c[cut] * 0.55 + 0.45
            S_ = blur(shift(m, 3, 2).astype(float)[..., None].repeat(3, -1), 2.2)[..., 0] * (1 - a) * 0.38
            C = C * (1 - S_[..., None]) + hx(st["shadow"]) * S_[..., None]; c = c * fib[..., None]
        if style == "felt" and m.any():    # 毛氈：毛邊（noise 吃邊）＋絨紋＋虛線車縫
            a = ((blur(a, 1.0) + (noise(H, W, 1, rs.randint(99)) - 0.5) * 0.55) > 0.5).astype(float); mm = a > 0
            c = c * (0.9 + 0.12 * noise(H, W, 1, rs.randint(99)))[..., None]
            puff = blur(mm.astype(float)[..., None].repeat(3, -1), 4)[..., 0]; c = c * (0.8 + 0.28 * puff)[..., None]   # 塞棉鼓起
            ring = erode(mm, 3) & ~erode(mm, 4) & ((((xx + yy) // 3) % 2) == 0)
            c[ring] = c[ring] * 0.45 + hx("#FFF4DE") * 0.55
            S_ = blur(shift(mm, 2, 1).astype(float)[..., None].repeat(3, -1), 1.6)[..., 0] * (1 - a) * 0.25
            C = C * (1 - S_[..., None]) + hx(st["shadow"]) * S_[..., None]
        if style == "neon" and m.any():    # 霓虹：暗身＋頂邊霓虹管（同色發光入 NE）
            mc = c[m].mean(0); rc = np.clip(mc / max(mc.max(), 1e-3), 0, 1) * 0.85 + 0.15
            rim = m & ~shift(m, 2); c[rim] = rc; NE[rim] += rc * (0.55 if r < 2 else 0.25)
        if style == "enamel" and m.any():  # 琺瑯：金線圍邊（上亮下深）＋平塗＋一點白反光
            mc = c[m].mean(0); c[:] = mc
            bd = m & ~erode(m, 2 if r < 2 else 3); top = bd & ~shift(m, 2); c[bd] = hx(GOLD); c[top] = hx(GOLD_HI); c[bd & ~shift(m, -2)] = hx(GOLD_D)
            ys_, xs_ = np.nonzero(erode(m, 4))
            if len(ys_) > 40:
                sx, sy = xs_.min() + (xs_.max() - xs_.min()) * 0.25, ys_.min() + 2
                c[((xx - sx) / 3) ** 2 + ((yy - sy) / 1.2) ** 2 < 1] = 1.0
        if style == "dreamy":   # 頂邊柔光 rim
            rim = m & ~shift(m, 2); c[rim] = c[rim] * 0.5 + 0.5
        if style == "water":    # 水彩：邊界抖動＋褪色見紙＋色池（邊深）＋顆粒
            wob = blur(a, 1.2) + (noise(H, W, 4, rs.randint(99)) - 0.5) * 0.5; a = (wob > 0.5).astype(float)
            c = c * 0.9 + hx("#FBF6EA") * 0.1; edge = np.clip(a - blur(a, 1.6), 0, 1)
            c = c * (1 - 0.32 * edge[..., None]) * (0.9 + 0.14 * noise(H, W, 6, rs.randint(99)))[..., None]; a = blur(a, 0.5)
        if style == "candy":    # 玻璃糖：頂邊高光線＋內部漸深＋半透
            top = m & ~shift(m, 1); hl = m & shift(m, 1) & ~shift(m, 3); c[top] = c[top] * 0.4 + 0.6; c[hl] = c[hl] * 0.75 + 0.25
            dist = blur(m.astype(float), 3); c = c * (0.78 + 0.22 * (1 - dist))[..., None] + 0.0; a = a * alpha
        L = np.concatenate([c, a[..., None]], -1)
        if r: L = blur(L, r)
        return over(C, L)
    # --- 天空雲（DoF 2px）
    cl = np.zeros((H, W), bool)
    for (cx_, cy_, sc_) in ((W * 0.25, H * 0.2, 1.0), (W * 0.7, H * 0.12, 0.8), (W * 0.55, H * 0.32, 0.6)):
        for dx_, dy_, r_ in ((-10, 2, 8), (0, -3, 11), (11, 1, 8), (20, 4, 5), (-18, 5, 5)):
            cl |= (((xx - cx_ - dx_ * sc_) / 1.5) ** 2 + (yy - cy_ - dy_ * sc_) ** 2 < (r_ * sc_) ** 2) & (yy < cy_ + 5 * sc_)
    C = paint(C, cl, {"candy": "#FFD6F0", "neon": "#2A2468", "paper": "#FFF6E6"}.get(style, "#FFFFFF"), r=1.6, alpha=0.85)
    # --- 遠景：浮空小島＋遠塔（DoF 3px）
    far = yy > gy - 74 + 16 * np.sin(xx / W * 5 + seed) + 8 * np.sin(xx / W * 13)
    isl = ((xx - W * 0.78) / 26) ** 2 + ((yy - gy + 150) / 7) ** 2 < 1; isl |= (((xx - W * 0.78) / 18) ** 2 + ((yy - gy + 143) / 12) ** 2 < 1) & (yy > gy - 150)
    tower = (np.abs(xx - W * 0.2) < 6) & (yy > gy - 128) | ((((xx - W * 0.2) / 9) ** 2 + ((yy - gy + 128) / 10) ** 2) < 1) & (yy < gy - 126)
    C = paint(C, isl | tower, st["far"], r=2.4); C = paint(C, far, st["far"], r=3)
    # --- 中景：圓樹＋菇屋（窗燈）（DoF 1.2px）
    mid = yy > gy - 40 + 10 * np.sin(xx / W * 7 + 1.3) + 5 * np.sin(xx / W * 19)
    C = paint(C, mid, grad(*st["hill"], mid), r=1.6)
    tm = np.zeros((H, W), bool); tk = np.zeros((H, W), bool)
    for i, x in enumerate((-6, 30, 150, 186, 210)):
        x = x * W / 195; r = 15 + 5 * (i % 2); cy = gy - 36 - (i % 2) * 7
        tm |= ((xx - x) ** 2 + (yy - cy) ** 2 < r * r) | ((xx - x - r * 0.6) ** 2 + (yy - cy - 4) ** 2 < (r * 0.7) ** 2); tk |= (np.abs(xx - x) < 2.5) & (yy > cy) & (yy < gy - 8)
    C = paint(C, tk, st["trunk"], r=1.0); C = paint(C, tm, grad(*st["tree"][::-1], tm), r=1.0)
    hx0 = W * 0.62; hb = gy - 12
    house = ((xx - hx0) / 12) ** 2 + ((yy - hb + 8) / 11) ** 2 < 1; house &= yy < hb
    cap = (((xx - hx0) / 22) ** 2 + ((yy - hb + 20) / 15) ** 2 < 1) & (yy < hb - 16)
    win = ((xx - hx0 + 4) / 2.5) ** 2 + ((yy - hb + 9) / 3) ** 2 < 1; door = (np.abs(xx - hx0 - 4) < 3) & (yy > hb - 8) & (yy < hb)
    C = paint(C, house, st["house"][0], r=0.9); C = paint(C, cap, st["house"][1], r=0.9)
    dots = cap & ((((xx - hx0 + 9) ** 2 + (yy - hb + 26) ** 2) < 9) | (((xx - hx0 + 4) ** 2 + (yy - hb + 32) ** 2) < 6) | (((xx - hx0 + 11) ** 2 + (yy - hb + 22) ** 2) < 5))
    C = paint(C, dots, "#FFFFFF", r=0.9); C = paint(C, win, st["lamp"], r=0.6); C = paint(C, door, st["trunk"], r=0.9)
    glow = np.exp(-(((xx - hx0 + 4) ** 2 + (yy - hb + 9) ** 2) / (2 * 6.0 ** 2))) * 0.8
    # --- 焦點層：地面＋小路＋水池（清晰）
    gm = yy > gy - 4 + 2 * np.sin(xx / 9)
    C = paint(C, gm, grad(*st["ground"], gm))
    path = (np.abs(xx - (W * 0.5 + 26 * np.sin((yy - gy) / 38))) < 6 + (yy - gy) * 0.22) & gm
    C = paint(C, path, st["path"])
    pond = ((xx - W * 0.2) / 30) ** 2 + ((yy - gy - 68) / 9) ** 2 < 1
    C = paint(C, pond, grad(*st["water"], pond))
    ref = pond & (np.abs(np.sin(yy * 1.6 + xx * 0.1)) > 0.93); C = paint(C, ref, "#FFFFFF", alpha=0.7)
    for _ in range(46):   # 草點／花
        x, y = rs.randint(0, W), rs.randint(int(gy + 2), H - 40); c = st["flower"][rs.randint(3)]
        if not pond[y, x] and not path[y, x]: C[y, x] = hx(c); C[y - 1, x] = C[y - 1, x] * 0.5 + hx(c) * 0.5
    # 路燈（右）
    lx, ly = W * lampx, gy + 22
    post = (np.abs(xx - lx) < 1.1) & (yy > ly - 34) & (yy < ly); lampm = ((xx - lx) / 3.5) ** 2 + ((yy - ly + 37) / 4.5) ** 2 < 1
    C = paint(C, post, st["trunk"]); C = paint(C, lampm, st["lamp"])
    glow += np.exp(-(((xx - lx) ** 2 + (yy - ly + 37) ** 2) / (2 * 9.0 ** 2))) * 1.0
    # --- 角色（影＋sprite；sprite 保持像素清晰）
    for img, cx, gyy, dep in sorted(sprites, key=lambda s: s[2]):
        sty_img = style_sprite(img, style); h, w = sty_img.shape[:2]; P_ = PADSTY.get(style, 0); x0 = int(round(cx - w / 2)); y0 = int(round(gyy - h + P_))
        sh = ((xx - cx) / (w * 0.34)) ** 2 + ((yy - gyy + 1.5) / 2.4) ** 2 < 1
        C = C * (1 - 0.25 * sh[..., None]) + hx(st["shadow"]) * 0.25 * sh[..., None]
        L = np.zeros((H, W, 4)); ys, xs = slice(max(0, y0), min(H, y0 + h)), slice(max(0, x0), min(W, x0 + w))
        L[ys, xs] = sty_img[ys.start - y0:ys.stop - y0, xs.start - x0:xs.stop - x0].astype(float) / 255
        if style in ("paper", "felt", "enamel"):   # 實體公仔／紙／徽章：落影
            S_ = blur(shift(L[..., 3] > 0, 3 if style == "paper" else 2, 2).astype(float)[..., None].repeat(3, -1), 1.8)[..., 0] * (1 - L[..., 3]) * 0.35
            C = C * (1 - S_[..., None]) + hx(st["shadow"]) * S_[..., None]
        C = over(C, L)
        if style == "neon":   # 寵物＝夜燈：成隻剪影外發光（顏色＝燈泡路線色）＋亮位 bloom
            gm_ = L[..., 3]; bc = np.array(SPRITE_GLOW.get(id(img), {}).get("col", (255, 220, 120))) / 255
            HALO += gm_[..., None] * bc; SPM = np.maximum(SPM, gm_); lum = L[..., :3].mean(-1); NE += (L[..., :3] * ((lum > 0.7) * gm_)[..., None]) * 0.22
        LAST_BOX.append((x0, y0, w, h))
        g = SPRITE_GLOW.get(id(img), {}).get("bulb")
        if g is not None: glow += np.exp(-(((xx - x0 - P_ - g[0]) ** 2 + (yy - y0 - P_ - g[1]) ** 2) / (2 * 4.5 ** 2))) * 0.9
    # --- 前景：草葉＋上角樹葉（DoF 最強）
    fg = np.zeros((H, W), bool)
    for i in range(14):
        bx = rs.randint(-10, W + 10); hgt = rs.randint(18, 40); fg |= (np.abs(xx - bx - (H - yy) * 0.25 * ((i % 2) * 2 - 1)) < 3.2 * np.clip((yy - (H - hgt)) / hgt, 0, 1) + 0.0) & (yy > H - hgt)
    fg |= ((xx + 10) ** 2 / 1100 + (yy - H + 6) ** 2 / 1600 < 1)
    leaf = ((xx - W + 6) ** 2 / 900 + (yy + 4) ** 2 / 500 < 1) | ((xx + 4) ** 2 / 500 + (yy - 20) ** 2 / 300 < 1)
    C = paint(C, fg, st["fg"], r=4.0); C = paint(C, leaf, st["fg"], r=6.0)
    # --- 光：左上光束＋燈暈 bloom＋vignette（＋風格專屬）
    beam = np.clip(1 - np.abs((xx - yy * 0.5) - W * 0.22) / 24, 0, 1) * np.clip(1 - yy / (H * 0.85), 0, 1)
    beam2 = np.clip(1 - np.abs((xx - yy * 0.5) - W * 0.52) / 12, 0, 1) * np.clip(1 - yy / (H * 0.7), 0, 1)
    k = {"base": 0.2, "dreamy": 0.3, "water": 0.14, "candy": 0.1, "paper": 0.16, "felt": 0.16, "neon": 0.05, "enamel": 0.1}[style]
    C = C + hx(st["light"]) * ((beam + beam2 * 0.6) * k)[..., None]
    C = C + hx(st["lamp"]) * (blur(np.clip(glow, 0, 1)[..., None].repeat(3, -1), 1)[..., :1] * st["bloom"] * 0.7)
    if style == "dreamy":   # 粉彩 bokeh＋全畫面 bloom＋光塵
        for _ in range(22):
            x, y, r = rs.randint(0, W), rs.randint(0, int(H * 0.75)), rs.randint(3, 10); m = (xx - x) ** 2 + (yy - y) ** 2 < r * r
            C = C * (1 - 0.16 * m[..., None]) + hx(["#FFFFFF", "#FFE3F5", "#E3F0FF"][rs.randint(3)]) * 0.16 * m[..., None]
        B = blur(np.clip(C, 0, 1), 7); C = 1 - (1 - C) * (1 - B * 0.2)
        for _ in range(30):
            x, y = rs.randint(1, W - 1), rs.randint(1, int(H * 0.8)); C[y, x] = C[y, x] * 0.3 + 0.7
    if style == "water":    # 紙紋乘落全畫面（包括 sprite），再加少少紙纖維
        C = C * paper[..., None]; fib = (noise(H, W, 1, 31) > 0.985); C[fib] = C[fib] * 0.92
    if style == "candy":    # 一條大光澤斜帶＋閃星
        band = np.clip(1 - np.abs((xx + yy * 0.6) - W * 0.9) / 18, 0, 1) * np.clip(1 - yy / (H * 0.6), 0, 1); C = C + 0.12 * band[..., None]
        for _ in range(24):
            x, y = rs.randint(2, W - 2), rs.randint(2, int(H * 0.55)); C[y, x] = 1
            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)): C[y + dy, x + dx] = np.minimum(1, C[y + dy, x + dx] + 0.35)
    if style == "neon":   # 霓虹 bloom：兩層高斯（窄＋闊）
        NE = NE + glow[..., None] * hx(st["lamp"]) * 0.5
        C = C + blur(np.clip(NE, 0, 1), 1.5) * 0.6 + blur(np.clip(NE, 0, 1), 6) * 0.6
        hb_ = blur(np.clip(HALO, 0, 1), 3) * 0.8 + blur(np.clip(HALO, 0, 1), 8) * 0.5; C = C + hb_ * (1 - SPM)[..., None] + hb_ * SPM[..., None] * 0.12
        rs2 = np.random.RandomState(8)
        for _ in range(26):   # 螢光粒
            x, y = rs2.randint(1, W - 1), rs2.randint(int(H * 0.4), H - 50); C[y, x] = C[y, x] * 0.2 + hx(["#7FF0E0", "#FFE45E", "#FF7AD9"][rs2.randint(3)]) * 0.8
    if style == "paper":  # 剪紙舞台：上下紙邊框（層次感）
        ed = (yy < 4 + 2 * np.sin(xx / 7)) | (yy > H - 5 + 2 * np.sin(xx / 6 + 1))
        C[ed] = hx("#FFF8EC") * fib[ed][..., None]
    if style == "enamel": # 徽章外框：金邊圓角框
        d_ = np.minimum.reduce([xx, yy, W - 1 - xx, H - 1 - yy]); C[d_ < 3] = hx(GOLD); C[d_ < 1] = hx(GOLD_D); C[(d_ >= 1) & (d_ < 1.9)] = hx(GOLD_HI)
    vig = 1 - 0.2 * (((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2) * 2.2
    if style == "neon": vig = 1 - 0.45 * (((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2) * 2.2
    C = C * vig[..., None]
    return (np.clip(C, 0, 1) * 255).astype(np.uint8)
SPRITE_GLOW = {}
def style_sprite(img, style):
    """風格方向：sprite 本身點變（概念示範）"""
    if style == "base": return img
    a = img.copy(); op = a[..., 3] > 0; c = a[..., :3].astype(float)
    isol = op & (np.abs(c - np.array(rgb(OL))).sum(-1) < 3)
    if style == "dreamy":   # 彩色外框（selout：用鄰近色變深偏紫）＋粉彩化
        c = c * 0.82 + np.array([255, 236, 250]) * 0.18
        k = np.ones((3, 3)); ins = op & ~isol; nb = np.zeros_like(c); cnt = np.zeros(op.shape)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                sh = np.roll(np.roll(c * ins[..., None], dy, 0), dx, 1); nb += sh; cnt += np.roll(np.roll(ins, dy, 0), dx, 1)
        sel = nb / np.maximum(cnt, 1)[..., None] * 0.55 + np.array([110, 80, 150]) * 0.45
        c[isol] = sel[isol]
    if style == "water":    # 啡色細外框＋褪色＋水彩斑
        c = c * 0.78 + np.array([245, 236, 220]) * 0.22; c[isol] = [122, 92, 74]
        n = noise(a.shape[0], a.shape[1], 3, 7); c = c * (0.94 + 0.1 * n)[..., None]
    if style == "candy":    # 飽和＋玻璃高光（左上弧白＋底部反光）
        g = c.mean(-1, keepdims=True); c = np.clip(g + (c - g) * 1.35, 0, 255)
        ys, xs = np.nonzero(op & ~isol)
        if len(ys):
            cy, cx = ys.mean(), xs.mean(); ry, rx = (ys.max() - ys.min()) / 2, (xs.max() - xs.min()) / 2
            yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]; u = (xx - cx) / max(rx, 1); v = (yy - cy) / max(ry, 1)
            arc = (np.abs(np.hypot(u + 0.1, v + 0.1) - 0.6) < 0.13) & (u < -0.05) & (v < -0.05) & op & ~isol
            c[arc] = [255, 255, 255]
            bot = (np.abs(np.hypot(u, v) - 0.7) < 0.08) & (v > 0.35) & op & ~isol; c[bot] = c[bot] * 0.5 + 255 * 0.5
        c[isol] = [58, 30, 110]
    if style in ("paper", "felt", "enamel", "neon"):
        ins = op & ~isol
        def nbmean(cc, mask):
            nb = np.zeros_like(cc); cnt = np.zeros(mask.shape)
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1): nb += np.roll(np.roll(cc * mask[..., None], dy, 0), dx, 1); cnt += np.roll(np.roll(mask, dy, 0), dx, 1)
            return nb / np.maximum(cnt, 1)[..., None]
    if style == "paper":    # 剪紙：2 階平塗（每色貼近最近亮／暗）＋外框變深色紙＋外圈 2px 白紙邊
        lum = c.mean(-1, keepdims=True); base = nbmean(c, ins)
        c = np.where(lum > 175, c * 0.85 + 255 * 0.15, c * 0.9); c[isol] = base[isol] * 0.6
        P = 2; o = np.zeros((a.shape[0] + 2 * P, a.shape[1] + 2 * P, 4), np.uint8); cc = np.zeros(o.shape[:2] + (3,)); m0 = np.zeros(o.shape[:2], bool)
        cc[P:-P, P:-P] = c; m0[P:-P, P:-P] = op; rim = dilate(m0, 2) & ~m0
        cc[rim] = [255, 250, 238]; o[..., :3] = np.clip(cc, 0, 255).astype(np.uint8); o[..., 3] = np.where(m0 | rim, 255, 0); return o
    if style == "felt":     # 毛氈：外框＝鄰色變深（無黑線）＋絨紋＋內圈虛線車縫＋燈泡變鈕
        base = nbmean(c, ins); c[isol] = base[isol] * 0.62
        n = noise(a.shape[0], a.shape[1], 1, 17); c = c * (0.92 + 0.12 * n)[..., None]
        puff = blur(op.astype(float)[..., None].repeat(3, -1), 3)[..., 0]; c = c * (0.82 + 0.26 * puff)[..., None]
        ring = erode(op, 2) & ~erode(op, 3) & (((np.indices(op.shape).sum(0)) // 2) % 2 == 0); c[ring] = c[ring] * 0.2 + np.array([255, 248, 232]) * 0.8
    if style == "neon":     # 夜燈：身暗＋外框霓虹（路線色）＋燈泡／發光色保持亮
        lum = c.mean(-1); bright = op & (lum > 170) & (c[..., 2] < 200) & (c[..., 0] > 200)
        keep = c.copy(); c = c * 0.5 + np.array([30, 20, 70]) * 0.5; c[bright] = keep[bright]
        nc = np.array(NEON_COL.get(id(img), (127, 240, 224)), float); c[isol] = nc
    if style == "enamel":   # 琺瑯：外框金（左上亮金）＋平塗（ramp 收做 2 階）＋外圈 1px 金邊＋白反光
        lum = c.mean(-1, keepdims=True); base = nbmean(c, ins); c = np.where(lum > 190, base * 0.5 + c * 0.5 + 18, base * 0.5 + c * 0.5)
        gm = isol; tl = gm & ~np.roll(op, 1, 0) | gm & ~np.roll(op, 1, 1)
        c[gm] = hx(GOLD_D) * 255; c[tl] = hx(GOLD) * 255
        ys, xs = np.nonzero(ins)
        if len(ys):
            cy, cx = ys.mean(), xs.mean(); yy_, xx_ = np.indices(op.shape); sh = ins & (((xx_ - cx + (xs.max() - xs.min()) * 0.22) / 2.2) ** 2 + ((yy_ - cy + (ys.max() - ys.min()) * 0.2) / 1.0) ** 2 < 1)
            c[sh] = 255
        P = 1; o = np.zeros((a.shape[0] + 2 * P, a.shape[1] + 2 * P, 4), np.uint8); cc = np.zeros(o.shape[:2] + (3,)); m0 = np.zeros(o.shape[:2], bool)
        cc[P:-P, P:-P] = c; m0[P:-P, P:-P] = op; rim = dilate(m0, 1) & ~m0; cc[rim] = hx(GOLD_HI) * 255
        o[..., :3] = np.clip(cc, 0, 255).astype(np.uint8); o[..., 3] = np.where(m0 | rim, 255, 0); return o
    a[..., :3] = np.clip(c, 0, 255).astype(np.uint8); return a
NEON_COL = {}
STYLE_INFO = {
    "dreamy": ("1 夢幻柔光", "粉彩 bloom、彩色外框、bokeh"),
    "water": ("2 繪本水彩", "紙紋＋水彩斑、啡色細線、低 bloom"),
    "candy": ("3 玻璃糖果", "飽和寶石色、玻璃高光、深紫外框"),
}
UICOL = {"dreamy": ((255, 245, 252), (150, 120, 190)), "water": ((246, 238, 222), (122, 92, 74)), "candy": ((255, 255, 255), (78, 40, 150)), "base": ((255, 248, 224), (59, 42, 62)),
         "paper": ((255, 248, 234), (110, 68, 52)), "felt": ((245, 232, 206), (110, 74, 56)), "neon": ((24, 18, 60), (127, 240, 224)), "enamel": ((255, 246, 228), (156, 107, 30))}
def ui_overlay(img, style):
    im = Image.fromarray(img); d = ImageDraw.Draw(im); W, H = im.size
    col = UICOL[style]
    d.rounded_rectangle([8, 8, W - 9, 26], 8, fill=col[0], outline=col[1]); d.fontmode = "1"; d.text((16, 10), "團絨　心情 82　Lv.5", font=font(11), fill=col[1])
    for i, s in enumerate(("餵", "洗", "玩", "瞓")):
        x = 14 + i * 45; d.rounded_rectangle([x, H - 34, x + 34, H - 12], 9, fill=col[0], outline=col[1]); d.text((x + 11, H - 31), s, font=font(12), fill=col[1])
    return np.array(im)
def bubble(img, x, y, s, style):
    im = Image.fromarray(img); d = ImageDraw.Draw(im); f = font(10); w = int(d.textlength(s, font=f)) + 10
    col = UICOL[style]
    d.rounded_rectangle([x, y, x + w, y + 16], 6, fill=col[0], outline=col[1]); d.polygon([(x + 10, y + 16), (x + 16, y + 16), (x + 9, y + 22)], fill=col[0], outline=col[1])
    d.fontmode = "1"; d.text((x + 5, y + 2), s, font=f, fill=col[1]); return np.array(im)
def build_styles():
    os.makedirs(STY, exist_ok=True); P = []; boards = []
    picks = [("shroom", False, "proud_wrong"), ("crystal", True, "smug"), ("moon", False, "think_asleep")]
    for style in ("dreamy", "water", "candy"):
        spr = []
        for (r, still, e), (cx, gy, dep) in zip(picks, ((50, 300, 0.2), (106, 322, 0.0), (158, 296, 0.6))):
            img, an = species_img(r, still, e)
            if r == "crystal": img = prop(img, an, "monocle")
            SPRITE_GLOW[id(img)] = {"bulb": an.get("bulb", (img.shape[1] / 2, 4))}; spr.append((img, cx, gy, dep))
        sc = scene(style, 195, 422, spr)
        sc = bubble(sc, 74, 228, "我計過：雲係我吹㗎", style); sc = ui_overlay(sc, style)
        big = Image.fromarray(sc).resize((195 * 2, 422 * 2), Image.NEAREST)
        cap = Image.new("RGB", (390, 44), BG); d = ImageDraw.Draw(cap); text(d, (8, 4), STYLE_INFO[style][0], 16); text(d, (8, 24), STYLE_INFO[style][1], 12, "orange_dd")
        b = Image.new("RGB", (390, 844 + 44), BG); b.paste(cap, (0, 0)); b.paste(big, (0, 44)); p = os.path.join(STY, f"style_{style}_board_2x.png"); b.save(p); P.append(p); boards.append(b)
    cmp_ = Image.new("RGB", (390 * 3 + 40, 888 + 30), BG); d = ImageDraw.Draw(cmp_); text(d, (10, 6), "HD-2D 風格方向比較（同一場景、同 3 隻：傘咕／碎碎角（靜光＋單片晶）／眠眠嚧；195×422 ×2）", 14)
    for i, b in enumerate(boards): cmp_.paste(b, (10 + i * 400, 30))
    p = os.path.join(STY, "style_compare.png"); cmp_.save(p); P.append(p)
    # 場景 mockup（現行方向 base，9 隻同場）
    spr = []
    pos = [(34, 140, .5), (92, 138, .5), (150, 140, .5), (208, 138, .5), (266, 136, .5), (62, 184, 0), (130, 186, 0), (196, 184, 0), (254, 186, 0)]
    order = ["moon", "crystal", "lumi", "tide", "soft", "shroom", "radiant", "ember", "dust"]
    for r, (cx, gy, dep) in zip(order, pos):
        img, an = species_img(r, r in ("radiant", "shroom"))
        if r == "lumi": an = {"bulb": (img.shape[1] / 2, 8)}
        SPRITE_GLOW[id(img)] = {"bulb": an.get("bulb")}; spr.append((img, cx, gy, dep))
    sc = scene("base", 300, 210, spr, seed=5, gy=118, lampx=0.985); sc = bubble(sc, 226, 136, "我好獨立㗎", "base"); sc = bubble(sc, 4, 76, "我喺度思考…", "base")
    sc = bubble(sc, 176, 74, "我係海洋之王", "base")
    p = os.path.join(PRV, "species_mockup_scene_3x.png"); Image.fromarray(sc).resize((900, 630), Image.NEAREST).save(p); P.append(p)
    return P

STY7 = [(1, "dreamy", "夢幻柔光", "粉彩 bloom、彩色外框、bokeh"), (2, "water", "繪本水彩", "紙紋＋水彩斑、啡色細線"), (3, "candy", "玻璃糖果", "飽和寶石色、玻璃高光"),
        (4, "paper", "剪紙立體", "一層層剪紙＋烘焙落影、白紙切邊、紙纖維"), (5, "felt", "毛絨布偶", "毛氈絨紋、毛邊、虛線車縫、公仔落影"),
        (6, "neon", "黃昏霓虹夢", "深靛夜世界、霓虹邊管、寵物＝夜燈"), (7, "enamel", "寶石琺瑯", "金線掐絲、平塗琺瑯、白反光點、徽章框")]
def board7(n, style, title, sub):
    """手機板（195×422 ×2）＋右邊 2x 放大 inset（直接裁同一場景，連光影；即遊戲內 4x）"""
    picks = [("shroom", False, "proud_wrong"), ("crystal", True, "smug"), ("moon", False, "think_asleep")]; spr = []
    for (r, still, e), (cx, gy, dep) in zip(picks, ((50, 300, 0.2), (106, 322, 0.0), (158, 296, 0.6))):
        img, an = species_img(r, still, e)
        if r == "crystal": img = prop(img, an, "monocle")
        SPRITE_GLOW[id(img)] = {"bulb": an.get("bulb", (img.shape[1] / 2, 4)), "col": rgb(BULB[r])}; NEON_COL[id(img)] = rgb(BULB[r]); spr.append((img, cx, gy, dep))
    sc = scene(style, 195, 422, spr); boxes = list(LAST_BOX)
    # LAST_BOX 依 y_ground 排序（同 sprites 排序一致）→ 按 x 重排做 inset
    crops = []
    for (x0, y0, w, h) in sorted(boxes):
        m = 5; xa, ya, xb, yb = max(0, x0 - m), max(0, y0 - m), min(195, x0 + w + m), min(422, y0 + h + 4)
        crops.append(Image.fromarray(sc[ya:yb, xa:xb]))
    sc = bubble(sc, 74, 228, "我計過：雲係我吹㗎", style if style in UICOL else "base"); sc = ui_overlay(sc, style)
    big = Image.fromarray(sc).resize((390, 844), Image.NEAREST); SW = 232
    b = Image.new("RGB", (390 + SW, 844 + 48), BG); d = ImageDraw.Draw(b)
    text(d, (8, 4), f"{n} {title}", 17); text(d, (8, 27), sub, 12, "orange_dd"); b.paste(big, (0, 48))
    text(d, (398, 52), "2x inset（遊戲內 4x）", 12); y = 74
    for c, nm in zip(crops, ("傘咕", "碎碎角（靜光）", "眠眠嚧")):
        k = min(4, (SW - 16) // c.width, 250 // c.height); cz = c.resize((c.width * k, c.height * k), Image.NEAREST)
        b.paste(cz, (390 + (SW - cz.width) // 2, y)); text(d, (398, y + cz.height + 2), nm, 11); y += cz.height + 22
    p = os.path.join(STY, f"style_{n}_board_2x.png"); b.save(p); return p, b
def build_styles7():
    os.makedirs(STY, exist_ok=True); P = []; B = []
    for n, st, t_, s_ in STY7: p, b = board7(n, st, t_, s_); P.append(p); B.append(b)
    w, h = B[0].size; cols = 4; im = Image.new("RGB", (cols * (w + 12) + 12, 2 * (h + 12) + 40), BG); d = ImageDraw.Draw(im)
    text(d, (12, 8), "HD-2D 風格方向 1–7 比較（同一場景、同 3 隻：傘咕／碎碎角（靜光＋單片晶）／眠眠嚧；195×422 ×2＋右邊 2x inset）", 18)
    for i, b in enumerate(B): im.paste(b, (12 + (i % cols) * (w + 12), 40 + (i // cols) * (h + 12)))
    p = os.path.join(STY, "style_compare_all.png"); im.save(p); P.append(p)
    im.resize((im.width // 2, im.height // 2), Image.LANCZOS).save(os.path.join(STY, "style_compare_all_half.png")); P.append(os.path.join(STY, "style_compare_all_half.png"))
    return P

# ======================================================================= 檢查
def check():
    E = []
    for f in sorted(os.listdir(SPR)):
        a = np.array(Image.open(os.path.join(SPR, f)).convert("RGBA"))
        if not np.isin(a[..., 3], (0, 255)).all(): E.append(f"{f}: alpha 唔係 0/255")
        cols = {tuple(int(v) for v in c) for c in np.unique(a[a[..., 3] == 255][:, :3], axis=0)}
        if cols - V3: E.append(f"{f}: 非 v3 色 {sorted(cols - V3)[:3]}")
    for f in ("species_transform_sheet_3x.png", "species_lineup_3x.png", "species_silhouettes_3x.png", "kit_expressions_3x.png", "kit_props_3x.png", "kit_species_gags_3x.png"):
        a = np.array(Image.open(os.path.join(PRV, f)).convert("RGB")); cols = {tuple(int(v) for v in c) for c in np.unique(a.reshape(-1, 3), axis=0)}
        if cols - V3: E.append(f"{f}: 非 v3 色 {len(cols - V3)}")
    # 剪影差異：守夜者兩兩 IoU（貼底置中）
    def sil(r):
        a = species_img(r, False)[0][..., 3] > 0; o = np.zeros((60, 60), bool); ys, xs = np.nonzero(a)
        a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]; h, w = a.shape; o[60 - h:, (60 - w) // 2:(60 - w) // 2 + w] = a; return o
    S_ = {r: sil(r) for r in ROUTES}; worst = (0, None)
    for i, a in enumerate(ROUTES):
        for b in ROUTES[i + 1:]:
            iou = (S_[a] & S_[b]).sum() / (S_[a] | S_[b]).sum(); worst = max(worst, (round(float(iou), 3), f"{a}/{b}"))
    if worst[0] > 0.72: E.append(f"剪影太似：{worst}")
    for e in E: print("ERR", e)
    print(f"species_concept check: {len(E)} errors；剪影最高 IoU {worst}")
    return worst, E
if __name__ == "__main__":
    w = sys.argv[1] if len(sys.argv) > 1 else "all"
    if w in ("all", "sprites"): build_sprites()
    if w in ("all", "sheets"): print("\n".join(build_sheets()))
    if w in ("all", "styles"): print("\n".join(build_styles()))
    if w in ("all", "styles7"): print("\n".join(build_styles7()))
    if w in ("all", "check"): sys.exit(1 if check()[1] else 0)
