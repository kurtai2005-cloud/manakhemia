#!/usr/bin/env python3
"""build_seasons_v2.py — systems12 四季 v2：唔只 LUT，每季有自己嘅場景內容（H1–H4 全部）。
Pillow + numpy 程式逐像素繪製，原創，無 AI。輸出格式同 v1 一樣（seasons/<s>/<H#>/{sky,far,mid,fore,lightmap,lut}.png＋grade.json；seasons.json），
另加：seasons/<s>/<H#>/raw/*.png（季節版未烘 raw，驗證用）、palette.json，同 seasons/<s>/particles/（粒子 sprite 幀＋emitter）。
做法：
1. 每個 variant 嘅 raw 層按 material（index/*.png＋H#/palette.json 精確對色）分區。
2. 季節換色喺「H1 日光空間」定義；其他時段用 T_H（由 H1→H# 色盤 least-squares 擬合嘅 3×4 仿射）＋該 material 嘅殘差帶過去，所以黃昏／夜晚會自動跟光。
3. 季節內容（櫻花／向日葵／紅葉／雪頂…）用固定 seed 畫，四個時段位置一樣。
4. 之後同 v1 一樣：lut = season_fn(make_lut(variant grade))，bake → sky/far/mid/fore。
"""
import json, os, sys, math
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_hd2d_scenes as B
SCN = B.OUT; SEA = os.path.join(SCN, "seasons"); LW, LH = B.LW, B.LH
MOTPAL = json.load(open(os.path.join(HERE, "..", "sprites", "tuanrong", "motion", "palette.json")))
V3 = {c["name"]: c["hex"] for c in MOTPAL["colors"]}
MATS = json.load(open(os.path.join(SCN, "index", "materials.json")))["materials"]
MI = {m["name"]: m["index"] for m in MATS}; NM = {i: m["name"] for m in MATS for i in m["index"]}
EXFIT = {"SKY", "SUN", "MOON", "STAR", "LAMP", "LANTERN", "WIN", "FAR_WIN", "CLOUD"}
HS = ("H1", "H2", "H3", "H4")

def hx(h): return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float) / 255
def pal(H): return {c["index"]: hx(c["hex"]) for c in json.load(open(os.path.join(SCN, H, "palette.json")))["colors"]}
P1 = pal("H1")
def fit(H):
    P = pal(H); ks = [k for k in P1 if k in P and NM[k] not in EXFIT]
    X = np.array([np.r_[P1[k], 1] for k in ks]); Y = np.array([P[k] for k in ks])
    return np.linalg.lstsq(X, Y, rcond=None)[0], P

_H1OK = {}
def H1OK():
    if not _H1OK:
        P = P1; ref = np.zeros((256, 3)); [ref.__setitem__(i, c) for i, c in P.items()]
        for nm in ("sky", "far", "mid", "fore"):
            raw = np.asarray(Image.open(os.path.join(SCN, "H1", "raw", f"{nm}.png")).convert("RGBA")).astype(float) / 255
            m = np.asarray(Image.open(os.path.join(SCN, "index", "sky_index_H1.png" if nm == "sky" else f"{nm}_index.png"))).astype(int)
            _H1OK[nm] = (np.abs(raw[..., :3] - ref[m]).max(-1) < 0.6 / 255) & (raw[..., 3] > 0.5) & (m > 0)
        _H1OK["sky"][:] = False   # sky index 每款唔同
    return _H1OK

NIGHTMIX = {"H4": 0.45}
LW3 = np.array([0.2126, 0.7152, 0.0722])
def _lumr(H):
    P = pal(H); ks = [k for k in P1 if k in P and NM[k] not in EXFIT]
    return float(np.median([(P[k] @ LW3) / max(P1[k] @ LW3, 1e-3) for k in ks]))
LUMR = {H: _lumr(H) for H in ("H1", "H2", "H3", "H4")}

def q8(c): return np.round(np.clip(c, 0, 1) * 255) / 255

class Ctx:
    """一個 variant 嘅繪製環境：T（H1→H 色）、material 圖、raw 層"""
    def __init__(s, H):
        s.H = H; s.M, s.P = fit(H)
        s.L = {}; s.mat = {}; s.off = {}
        for nm in ("sky", "far", "mid", "fore"):
            raw = np.asarray(Image.open(os.path.join(SCN, H, "raw", f"{nm}.png")).convert("RGBA")).astype(float) / 255
            ip = os.path.join(SCN, "index", f"sky_index_{H}.png" if nm == "sky" else f"{nm}_index.png")
            m = np.asarray(Image.open(ip)).astype(int)
            ref = np.zeros((256, 3)); [ref.__setitem__(i, c) for i, c in s.P.items()]
            ok = (np.abs(raw[..., :3] - ref[m]).max(-1) < 0.6 / 255) & (raw[..., 3] > 0.5) & (m > 0)
            s.off[nm] = np.zeros((LH, LW, 3))
            if H != "H1":
                # 呢個時段獨有嘅紋理色（H1 同一格係精確 material）→ 當同 material，保留同色盤色嘅差（offset）
                xo = ~ok & (raw[..., 3] > 0.5) & (m > 0) & H1OK()[nm]
                s.off[nm][xo] = raw[xo, :3] - ref[m][xo]; ok |= xo
            s.mat[nm] = np.where(ok, m, 0); s.L[nm] = raw.copy()
    def Tf(s, c):
        """H1 色 → 呢個時段（未量化）。夜晚（H4）純仿射會令淺色變好飽和嘅藍 → 同「保色相、按亮度比縮暗」各半"""
        o = np.r_[c, 1] @ s.M
        k = NIGHTMIX.get(s.H, 0)
        if k: o = o * (1 - k) + c * LUMR[s.H] * k
        return o
    def T(s, h):
        c = hx(h) if isinstance(h, str) else np.asarray(h, float)
        return q8(s.Tf(c))
    def recol(s, nm, ix, h, where=None):
        """material level ix → 季節色 h（H1 空間），帶殘差"""
        if ix not in s.P: return
        c = hx(h); res = s.P[ix] - s.Tf(P1[ix]) if ix in P1 else 0
        col = q8(s.Tf(c) + res) if s.H != "H1" else q8(c)
        msk = s.mat[nm] == ix
        if where is not None: msk &= where
        s.L[nm][msk, :3] = np.clip(col + s.off[nm][msk], 0, 1)
    def mask(s, nm, *names):
        out = np.zeros((LH, LW), bool)
        for n in names: out |= np.isin(s.mat[nm], MI[n])
        return out
    def put(s, nm, msk, h):
        s.L[nm][msk, :3] = s.T(h); s.L[nm][msk, 3] = 1
    def clear(s, nm, msk): s.L[nm][msk] = 0
    def alpha(s, nm): return s.L[nm][..., 3] > 0.5

def sh(m, dy=0, dx=0):
    o = np.zeros_like(m)
    ys = slice(max(dy, 0), LH + min(dy, 0)); yd = slice(max(-dy, 0), LH + min(-dy, 0))
    xs = slice(max(dx, 0), LW + min(dx, 0)); xd = slice(max(-dx, 0), LW + min(-dx, 0))
    o[ys, xs] = m[yd, xd]; return o
def top_edge(m, free): return m & sh(free, 1)          # 上面一格係 free
def cap(m, free, d):
    t = top_edge(m, free); out = t.copy()
    for k in range(1, d): out |= sh(t, k) & m
    return out
def rng(seed): return np.random.default_rng(seed)
def N(cell, seed, **k): return B.vnoise(cell, seed, **k)
YY, XX = np.mgrid[0:LH, 0:LW]

def levels(c, nm, mat, cols, where=None):
    for ix, h in zip(MI[mat], cols): c.recol(nm, ix, h, where)

def disc(cx, cy, r): return (XX - cx) ** 2 + (YY - cy) ** 2 <= r * r + r * 0.6

def canopy_box(c):
    lf = c.mask("mid", "LEAF"); lf &= (YY < 215) & (XX < 120); return lf

# ------------------------------------------------------------------ 春
def spring(c):
    levels(c, "mid", "LEAF", ["#3f6b33", "#6da24a", "#a2d26c"])
    levels(c, "far", "TREE_FAR", ["#86a066", "#bccf8c"]); levels(c, "mid", "TREE_FAR", ["#86a066", "#bccf8c"])
    for nm in ("far", "mid"):
        levels(c, nm, "HILL_NEAR", ["#728458", "#b4c880"]); levels(c, nm, "HILL_FAR", ["#a8a888", "#ccd2a0"])
    levels(c, "mid", "GRASS", ["#4b6c36", "#7ca853", "#aad56c"]); levels(c, "mid", "MOSS", ["#55663a", "#b6d272"])
    levels(c, "mid", "SPROUT", ["#45622f", "#9ed062"])
    levels(c, "fore", "FLEAF", ["#2d4c2a", "#72aa58"]); levels(c, "fore", "FGRASS", ["#37522c", "#82b65a"])
    levels(c, "fore", "FFLOWER", ["#f08cb0"]); levels(c, "mid", "FLOWER_P", ["#f08cb0"])
    # 櫻花：樹冠上一團團粉紅
    lf = canopy_box(c); n1 = N(5.5, 101); n2 = N(2.2, 102)
    bl = lf & (n1 > 0.42)
    lv = c.mat["mid"]
    for ix, h in zip(MI["LEAF"], ["#d987a6", "#f2b0c6", "#fdd6e2"]): c.put("mid", bl & (lv == ix), h)
    c.put("mid", bl & top_edge(lf, ~lf) , "#fff0f5"); c.put("mid", bl & (n2 > 0.78), "#fff0f5")
    # 樹冠邊溢出花瓣團
    free = ~c.alpha("mid"); r = rng(7)
    edge = sh(lf, 1) | sh(lf, -1) | sh(lf, 0, 1) | sh(lf, 0, -1)
    spill = edge & free & (n1 > 0.5) & (r.random((LH, LW)) < 0.55); c.put("mid", spill, "#f2b0c6")
    # 遠樹粉紅
    for nm in ("far", "mid"):
        tf = c.mask(nm, "TREE_FAR"); nn = N(4, 103) > 0.55
        c.put(nm, tf & nn & (c.mat[nm] == MI["TREE_FAR"][0]), "#c88aa0"); c.put(nm, tf & nn & (c.mat[nm] == MI["TREE_FAR"][1]), "#ecbccb")
    # 地上小花＋落花瓣
    gr = c.mask("mid", "GRASS"); r = rng(11)
    pts = np.argwhere(gr & (r.random((LH, LW)) < 1 / 70) & (YY > 270))
    cols = ["#f4a6c0", "#fff6f0", "#f8e070", "#f4a6c0"]
    for k, (y, x) in enumerate(pts):
        h = cols[k % 4]
        if k % 3 == 0:
            for dy, dx in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
                if 0 <= y + dy < LH and 0 <= x + dx < LW and gr[y + dy, x + dx]: c.put("mid", (YY == y + dy) & (XX == x + dx), h)
            c.put("mid", (YY == y) & (XX == x), "#f8e070" if h != "#f8e070" else "#e07f45")
        else: c.put("mid", (YY == y) & (XX == x), h)
    under = gr & (XX < 110) & (YY > 268) & (YY < 330) & (r.random((LH, LW)) < 1 / 45); c.put("mid", under, "#fdd6e2")
    # 吊藤開花
    fl = c.mask("fore", "FLEAF"); vine = fl & (YY < 70) & (rng(12).random((LH, LW)) < 0.16); c.put("fore", vine, "#f6b6cb")
    c.put("fore", vine & sh(vine, 0, 1), "#fff0f5")

# ------------------------------------------------------------------ 夏
def sunflower(c, nm, x, ytop, ybot, r, free_only=True, block=None):
    can = ~c.alpha(nm) if free_only else np.ones((LH, LW), bool)
    if block is not None: can &= ~block
    stem = (np.abs(XX - x) <= 0) & (YY >= ytop + r) & (YY <= ybot)
    c.put(nm, stem & can, "#3a7d4e")
    for k, yy in enumerate(range(ytop + r + 5, ybot - 2, 7)):
        sgn = 1 if k % 2 else -1
        lfm = ((XX - (x + sgn * 3)) ** 2 / 9 + (YY - yy) ** 2 / 2.2 <= 1) & can
        c.put(nm, lfm, "#4fa046"); c.put(nm, lfm & (YY > yy), "#3a7d4e")
    pet = disc(x, ytop, r) & can; c.put(nm, pet, "#f2b42e")
    ang = np.arctan2(YY - ytop, XX - x); tips = pet & ((np.cos(ang * 10) > 0.3) | (np.hypot(XX - x, YY - ytop) < r - 1))
    c.put(nm, pet & ~tips, "#e0902e"); c.put(nm, tips & (YY < ytop), "#ffd45e")
    ctr = disc(x, ytop, max(1, r * 0.45)) & can; c.put(nm, ctr, "#6b3d22"); c.put(nm, ctr & ((XX + YY) % 2 == 0), "#8a5228")
    c.put(nm, ctr & (YY == ytop - int(r * 0.45)) , "#a86a34")

def cloud_puffs(c, nm, puffs, cols):
    m = np.zeros((LH, LW), bool)
    for (x, y, r) in puffs: m |= disc(x, y, r)
    base = m & (YY > max(y for _, y, _ in puffs) - 2)
    shade = m & ~sh(m, 2, 1)   # 右下邊
    c.put(nm, m, cols[0]); c.put(nm, m & (YY > np.array([p[1] for p in puffs]).mean() + 2), cols[1]); c.put(nm, shade | base, cols[2])
    c.put(nm, m & ~sh(m, -1, -1) & ~shade, "#ffffff")

def summer(c):
    levels(c, "mid", "LEAF", ["#1f4824", "#2f7a35", "#52ae48"])
    for nm in ("far", "mid"):
        levels(c, nm, "TREE_FAR", ["#3f6a3b", "#62a04e"]); levels(c, nm, "HILL_NEAR", ["#3b6234", "#71a24a"]); levels(c, nm, "HILL_FAR", ["#7c9c80", "#9ebe82"])
    levels(c, "mid", "GRASS", ["#244a22", "#3d7c31", "#62ac42"]); levels(c, "mid", "MOSS", ["#2e5228", "#6eaa44"]); levels(c, "mid", "SPROUT", ["#2a5226", "#5cac42"])
    levels(c, "fore", "FLEAF", ["#163a1c", "#3c8c3c"]); levels(c, "fore", "FGRASS", ["#1c4220", "#4a9a3e"])
    if c.H in ("H1", "H3"):
        levels(c, "sky", "SKY", ["#4f9eee", "#70b4f2", "#94c8f4", "#b8daf2", "#d4e8f0", "#e4eef0", "#eef2ee"])
        cloud_puffs(c, "sky", [(170, 92, 14), (186, 84, 12), (156, 100, 10), (198, 98, 11), (176, 72, 11), (188, 64, 8), (142, 106, 7), (208, 106, 7)],
                    ["#fbfaf4", "#e6eaf2", "#c8d2e2"])
    # 向日葵（籬笆後面，貼小屋）
    wood = c.mask("mid", "WOOD")
    for (x, yt, r) in ((118, 222, 4), (131, 214, 5), (145, 220, 5), (156, 228, 4), (64, 232, 3)):
        sunflower(c, "mid", x, yt, 266, r, block=wood)
    # 前景右下大向日葵
    sunflower(c, "fore", 200, 384, 446, 8, free_only=True)
    # 蟬（樹幹）
    tr = c.mask("mid", "TRUNK"); ys, xs = np.nonzero(tr & (YY > 205) & (YY < 225))
    if len(xs):
        x0 = int(np.median(xs)) + 1; y0 = 214
        body = ((XX >= x0) & (XX <= x0 + 1) & (YY >= y0) & (YY <= y0 + 4)); c.put("mid", body, "#3b2a3e")
        c.put("mid", (XX == x0 + 2) & (YY >= y0 + 1) & (YY <= y0 + 5), "#a3b08c"); c.put("mid", (XX == x0 - 1) & (YY >= y0 + 1) & (YY <= y0 + 5), "#c9d6b0")
        c.put("mid", (XX == x0) & (YY == y0), "#7fc4e8")

# ------------------------------------------------------------------ 秋
AUT = [["#7c2a20", "#bc462c", "#e46c3c"], ["#8a3e1c", "#d2722c", "#f2a444"], ["#8a6a22", "#d2a232", "#f4d25a"]]
def leaf_px(c, nm, x, y, h, h2, allow):
    for dy, dx in ((0, 0), (0, 1), (1, 0), (-1, 0), (0, -1)):
        yy, xx = y + dy, x + dx
        if 0 <= yy < LH and 0 <= xx < LW and allow[yy, xx]: c.put(nm, (YY == yy) & (XX == xx), h if (dy, dx) != (0, 1) else h2)

def autumn(c):
    lv = c.mat["mid"]; lf = c.mask("mid", "LEAF"); n = N(9, 201); n2 = N(4, 202)
    sel = np.where(n + 0.25 * n2 < 0.62, 0, np.where(n + 0.25 * n2 < 0.82, 1, 2))
    for s in range(3):
        for ix, h in zip(MI["LEAF"], AUT[s]): c.recol("mid", ix, h, where=(sel == s))
    for nm in ("far", "mid"):
        tf = c.mask(nm, "TREE_FAR"); nn = N(5, 203)
        levels(c, nm, "TREE_FAR", ["#8a4a28", "#cc843c"]); c.put(nm, tf & (nn > 0.6) & (c.mat[nm] == MI["TREE_FAR"][1]), "#c8502e")
        c.put(nm, tf & (nn < 0.3) & (c.mat[nm] == MI["TREE_FAR"][1]), "#e0b048")
        levels(c, nm, "HILL_NEAR", ["#6e5a36", "#b89a56"]); levels(c, nm, "HILL_FAR", ["#a88a6a", "#d2b27a"])
    levels(c, "mid", "GRASS", ["#5a5428", "#8c803a", "#bcaa52"]); levels(c, "mid", "MOSS", ["#5e5430", "#bca452"]); levels(c, "mid", "SPROUT", ["#6a5426", "#c49440"])
    levels(c, "fore", "FLEAF", ["#5c2a1a", "#c4602c"]); levels(c, "fore", "FGRASS", ["#4c4224", "#a28c40"])
    levels(c, "fore", "FFLOWER", ["#e07f45"])
    fl = c.mask("fore", "FLEAF"); c.put("fore", fl & (N(3, 204) > 0.65) & (c.mat["fore"] == MI["FLEAF"][1]), "#e2a03e")
    # 落葉：地面（樹下密啲）＋樹頭一堆
    gr = c.mask("mid", "GRASS") | c.mask("mid", "MOSS"); r = rng(21)
    dens = np.where(XX < 100, 1 / 28, 1 / 70)
    pts = np.argwhere(gr & (r.random((LH, LW)) < dens) & (YY > 268))
    for k, (y, x) in enumerate(pts):
        s = AUT[k % 3]; leaf_px(c, "mid", x, y, s[1], s[2], gr)
    tr = c.mask("mid", "TRUNK"); ys, xs = np.nonzero(tr)
    if len(xs):
        bx = int(np.median(xs[ys > ys.max() - 4])); by = int(ys.max()) + 1
        pile = ((XX - bx) ** 2 / 240 + (YY - by) ** 2 / 10 <= 1) & (YY <= by + 2)
        pn = N(1.6, 205)
        for s in range(3): c.put("mid", pile & ~tr & (pn >= s / 3) & (pn < (s + 1) / 3), AUT[s][(s + 1) % 3])
        c.put("mid", pile & ~tr & top_edge(pile, ~pile), "#f4d25a")
    # 南瓜 ×2
    for (x, y, rx, ry) in ((172, 333, 6, 4), (184, 346, 4, 3)):
        pm = ((XX - x) ** 2 / (rx * rx) + (YY - y) ** 2 / (ry * ry) <= 1)
        c.put("mid", pm, "#e07f45"); c.put("mid", pm & (np.abs(XX - x) % 3 == 0), "#b8643f")
        c.put("mid", pm & ~sh(pm, -1, 0) , "#b8643f"); c.put("mid", pm & (YY < y - ry + 2) & (np.abs(XX - x) < rx - 1) & ~(np.abs(XX - x) % 3 == 0), "#f2a65a")
        c.put("mid", (XX == x) & (YY >= y - ry - 2) & (YY < y - ry + 1), "#3a7d4e"); c.put("mid", (XX == x + 1) & (YY == y - ry - 2), "#6bbf6a")
        out = (sh(pm, 1) | sh(pm, -1) | sh(pm, 0, 1) | sh(pm, 0, -1)) & ~pm; c.put("mid", out & (YY >= y), "#3b2a3e")

# ------------------------------------------------------------------ 冬
SNOW = ["#b6c4dc", "#d8e2f0", "#f4f8ff"]
def branches(c, nm, x0, y0, ang, ln, w, depth, r, out):
    x1 = x0 + math.cos(ang) * ln; y1 = y0 - math.sin(ang) * ln
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for t in np.linspace(0, 1, n + 1):
        x = x0 + (x1 - x0) * t; y = y0 + (y1 - y0) * t
        for dx in range(w):
            xi, yi = int(round(x)) + dx, int(round(y))
            if 0 <= xi < LW and 0 <= yi < LH: out[yi, xi] = max(out[yi, xi], 2 if w > 1 else 1)
    if depth == 0 or ln < 4: return
    for da in (r.uniform(0.35, 0.7), -r.uniform(0.35, 0.7)) + ((r.uniform(-0.2, 0.2),) if depth > 2 else ()):
        branches(c, nm, x1, y1, ang + da, ln * r.uniform(0.62, 0.78), max(1, w - 1), depth - 1, r, out)

def winter(c):
    # 樹冠落晒葉 → 光禿樹枝＋枝頂積雪
    lf = canopy_box(c); c.clear("mid", lf)
    tr = c.mask("mid", "TRUNK"); ys, xs = np.nonzero(tr & (YY < 230))
    br = np.zeros((LH, LW), int)
    if len(xs):
        ytop = int(ys.min()); xc = float(np.median(xs[ys < ytop + 6]))
        r = rng(31)
        # 主幹延伸＋分枝
        branches(c, "mid", xc, ytop + 2, math.pi / 2, 30, 4, 0, r, br)
        for a, l, w in ((1.95, 34, 3), (1.25, 36, 3), (2.45, 26, 3), (0.75, 30, 3), (1.6, 28, 3)):
            branches(c, "mid", xc + r.uniform(-1, 1), ytop + r.uniform(0, 18), a, l, w, 4, r, br)
    brm = (br > 0) & ~tr
    c.put("mid", brm, "#5a3e30"); c.put("mid", (br == 2) & ~tr & ~sh(br == 2, 0, -1), "#432c23")
    free = ~c.alpha("mid")
    c.put("mid", top_edge(brm, free) & (YY < 236) & (rng(32).random((LH, LW)) < 0.8), SNOW[2])
    # 遠樹：結霜，頂有雪
    for nm in ("far", "mid"):
        tf = c.mask(nm, "TREE_FAR"); levels(c, nm, "TREE_FAR", ["#56686e", "#8aa0a8"])
        c.put(nm, cap(tf, ~tf, 2), SNOW[2])
        for mat, cols in (("HILL_NEAR", ["#9aaac2", "#e2eaf6"]), ("HILL_FAR", ["#b8c4d8", "#eef2fa"])): levels(c, nm, mat, cols)
        fh = c.mask(nm, "FAR_HOUSE"); c.put(nm, cap(fh, ~fh, 1), SNOW[2])
    # 地面：雪＋少少草尖
    gr = c.mask("mid", "GRASS") | c.mask("mid", "MOSS"); n = N(6, 301); r = rng(33)
    levels(c, "mid", "GRASS", SNOW); levels(c, "mid", "MOSS", [SNOW[1], SNOW[2]])
    poke = gr & (n > 0.78) & (r.random((LH, LW)) < 0.22); c.put("mid", poke, "#6a7658"); c.put("mid", poke & (r.random((LH, LW)) < 0.4), "#8a9670")
    tracks = gr & (np.abs(YY - (300 + 0.18 * (XX - 60))) < 1) & ((XX // 4) % 3 == 0) & (XX > 40) & (XX < 170); c.put("mid", tracks, SNOW[0])
    levels(c, "mid", "SPROUT", ["#56604a", "#8a9670"])
    pot = c.mask("mid", "POT"); nearpot = np.zeros_like(pot)
    for k in range(0, 10): nearpot |= sh(pot, -k) | sh(pot, -k, 2) | sh(pot, -k, -2)
    fw = c.mask("mid", "FLOWER_P", "FLOWER_Y")
    c.put("mid", fw & ~nearpot, SNOW[2]); c.put("mid", fw & nearpot, "#e5584d")  # 盆入面變聖誕紅，草地嘅小花蓋雪
    # 積雪：屋頂、籬笆、盆、石、燈柱、罐、菇
    am = c.alpha("mid")
    for mats, d in ((("ROOF",), 3), (("WOOD",), 2), (("POT", "SOIL"), 2), (("STONE",), 2), (("METAL", "LAMP"), 1), (("CAN",), 1), (("MUSH",), 2), (("LANTERN",), 1)):
        m = c.mask("mid", *mats); cp = cap(m, ~m & ~c.mask("mid", "ROOF", "WALL") if mats != ("ROOF",) else ~m, d)
        c.put("mid", cp, SNOW[2]); c.put("mid", cp & ~sh(cp, -1) & sh(m, -1) & ~sh(cp, 1) , SNOW[1])
        up = top_edge(m, ~am) & (mats[0] in ("ROOF", "WOOD", "POT"))
        c.put("mid", sh(up, -1) & ~am, SNOW[2])
    # 冰柱：屋簷底
    rf = c.mask("mid", "ROOF"); bot = rf & ~sh(rf, -1); ys, xs = np.nonzero(bot); r = rng(34)
    for y, x in zip(ys, xs):
        if x % 4 == (y % 2) and r.random() < 0.7:
            L = int(r.integers(2, 5))
            for k in range(1, L + 1):
                if y + k < LH: c.put("mid", (YY == y + k) & (XX == x), "#d8ecf8" if k < L else "#ffffff")
    # 前景：葉結霜、草變雪堆
    fl = c.mask("fore", "FLEAF"); levels(c, "fore", "FLEAF", ["#2a3c3e", "#6e8c8c"])
    c.put("fore", cap(fl, ~c.alpha("fore"), 1), SNOW[2])
    levels(c, "fore", "FGRASS", [SNOW[1], SNOW[2]]); levels(c, "fore", "FFLOWER", ["#e5584d"])
    drift = (YY > 438 - 4 * np.sin(XX / 13.0) - 2 * np.sin(XX / 5.0 + 1)) ; c.put("fore", drift, SNOW[2]); c.put("fore", drift & ~sh(drift, 1) , "#ffffff")
    c.put("fore", drift & (YY > 443), SNOW[1])
    if c.H in ("H1", "H3"):
        levels(c, "sky", "SKY", ["#a6bcd8", "#b8cade", "#c8d6e4", "#d6e0e8", "#e0e6ea", "#e6eaec", "#eceeee"])
        levels(c, "sky", "CLOUD", ["#d8dee8", "#f2f4f8"])

SEASON_FN = {"spring": spring, "summer": summer, "autumn": autumn, "winter": winter}

# ================================================================== 輸出：季節 raw
def season_raw(sk, H, od):
    """畫好季節版 raw 層 → 存 od/raw/*.png＋od/palette.json；回傳 {layer: float RGBA}"""
    c = Ctx(H); SEASON_FN[sk](c); rd = os.path.join(od, "raw"); os.makedirs(rd, exist_ok=True); cols = {}
    for nm in ("sky", "far", "mid", "fore"):
        L = c.L[nm]; a = L[..., 3] > 0.5; L[..., 3] = a.astype(float); L[~a, :3] = 0
        L[..., :3] = q8(L[..., :3]); B.save_rgba(L, os.path.join(rd, f"{nm}.png"))
        for v in np.unique(B.to8(L[a][:, :3]), axis=0): cols[tuple(int(x) for x in v)] = cols.get(tuple(int(x) for x in v), 0) + 1
    json.dump({"season": sk, "variant": H, "usedColors": len(cols), "note": "季節版 raw（未烘）用色；v1 variant 色盤＋季節內容色（經 T_H 帶入時段光）",
               "colors": ["#%02x%02x%02x" % k for k in sorted(cols)]}, open(os.path.join(od, "palette.json"), "w"), indent=0)
    return {nm: c.L[nm] for nm in c.L}

# ================================================================== 粒子 sprite（v3 色盤，alpha 0/255）
CELL = 8
def _rot_ellipse(rx, ry, ang, cx=3.5, cy=3.5):
    y, x = np.mgrid[0:CELL, 0:CELL].astype(float); x -= cx; y -= cy
    ca, sa = math.cos(ang), math.sin(ang); u = x * ca + y * sa; v = -x * sa + y * ca
    return (u / max(rx, .3)) ** 2 + (v / max(ry, .3)) ** 2 <= 1.0, u, v
def spr_petal(f, cols):
    th = f / 6 * math.pi * 2; m, u, v = _rot_ellipse(2.4, 0.5 + 1.2 * abs(math.cos(th)), f * math.pi / 6)
    if m.sum() < 2: m[3, 3] = m[3, 4] = True
    o = np.full((CELL, CELL), None, object); o[m] = cols[0]; o[m & (v < -0.3)] = cols[1]; o[m & (u > 1.4)] = cols[2]; return o
def spr_leaf(f, cols):
    th = f / 6 * math.pi * 2; m, u, v = _rot_ellipse(2.8, 0.6 + 1.4 * abs(math.cos(th)), f * math.pi / 3)
    o = np.full((CELL, CELL), None, object); o[m] = cols[0]; o[m & (v < -0.4)] = cols[1]; o[m & (np.abs(v) < 0.5) & (abs(math.cos(th)) > 0.4)] = cols[2]
    a = f * math.pi / 3; sx, sy = int(round(3.5 - 3.4 * math.cos(a))), int(round(3.5 - 3.4 * math.sin(a)))
    if 0 <= sx < CELL and 0 <= sy < CELL: o[sy, sx] = cols[2]
    return o
def spr_firefly(f):
    o = np.full((CELL, CELL), None, object); k = [0, 1, 2, 3, 2, 1][f]
    if k >= 2:
        for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)): o[3 + dy, 3 + dx] = "glow_mid" if k == 3 else "glow"
    if k == 3:
        for dy, dx in ((0, 2), (2, 0), (0, -2), (-2, 0)): o[3 + dy, 3 + dx] = "glow"
    o[3, 3] = ["glow_warm", "glow", "glow_core", "glow_core"][k]; return o
def spr_mote(f):
    o = np.full((CELL, CELL), None, object); k = [0, 1, 2, 1][f]; o[3, 3] = "glow_core"
    for r_ in range(1, k + 1):
        for dy, dx in ((0, r_), (r_, 0), (0, -r_), (-r_, 0)): o[3 + dy, 3 + dx] = "cream4" if r_ == k else "glow_core"
    return o
def spr_snow(v, f):
    o = np.full((CELL, CELL), None, object); tw = "white" if f % 2 == 0 else "cream4"
    if v == 0: o[3, 3] = tw
    elif v == 1: o[3:5, 3:5] = "white"; o[4, 4] = "drop" if f % 2 else "white"
    elif v == 2:
        for dy, dx in ((0, 0), (0, 1), (1, 0), (0, -1), (-1, 0)): o[3 + dy, 3 + dx] = "white"
        if f % 2: o[3, 3] = "drop"
    else:
        arms = ((0, 1), (1, 0), (0, -1), (-1, 0)) if f in (0, 2) else ((1, 1), (1, -1), (-1, 1), (-1, -1))
        o[3, 3] = "white"
        for dy, dx in arms:
            o[3 + dy, 3 + dx] = "white"; o[3 + 2 * dy, 3 + 2 * dx] = "drop" if f in (0, 2) else "white"
    return o

PARTICLES = {
 "spring": [dict(name="petal", frames=6, fps=8, variants=[("blush", "white", "blush_d"), ("peach2", "white", "blush"), ("white", "cream4", "blush")],
                 emitter=dict(spawn="top+right", ratePerSec=2.2, max=14, vx=[-14, -5], vy=[10, 20], sway=dict(amp=6, periodSec=2.4), lifeSec=14,
                              perVariant={"H1": 1.0, "H2": 0.8, "H3": 1.0, "H4": 0.4}))],
 "summer": [dict(name="firefly", frames=6, fps=6, variants=[("a",)], emitter=dict(spawn="area:ground", ratePerSec=0.8, max=8, vx=[-4, 4], vy=[-3, 2], sway=dict(amp=5, periodSec=3.0), lifeSec=6,
                 perVariant={"H1": 0.0, "H2": 0.6, "H3": 0.0, "H4": 1.0})),
            dict(name="sunmote", frames=4, fps=6, variants=[("a",)], emitter=dict(spawn="area:sky+light", ratePerSec=1.2, max=8, vx=[-2, 2], vy=[-3, -1], sway=dict(amp=2, periodSec=4.0), lifeSec=4,
                 note="熱浪光點（日光下閃）", perVariant={"H1": 1.0, "H2": 0.4, "H3": 1.0, "H4": 0.0}))],
 "autumn": [dict(name="leaf", frames=6, fps=8, variants=[("orange", "orange_d", "orange_dd"), ("berry", "berry_d", "orange_dd"), ("egg_shade", "egg_dark", "orange_dd")],
                 emitter=dict(spawn="top:tree", ratePerSec=1.6, max=12, vx=[-6, 10], vy=[14, 24], sway=dict(amp=9, periodSec=2.0), lifeSec=14,
                              perVariant={"H1": 1.0, "H2": 1.0, "H3": 1.0, "H4": 0.5}))],
 "winter": [dict(name="snow", frames=4, fps=4, variants=[("dot",), ("2px",), ("plus",), ("flake",)],
                 emitter=dict(spawn="top", ratePerSec=6.0, max=40, vx=[-4, 2], vy=[12, 26], sway=dict(amp=3, periodSec=3.2), lifeSec=20, weights=[0.45, 0.3, 0.17, 0.08],
                              perVariant={"H1": 1.0, "H2": 1.0, "H3": 1.0, "H4": 1.0}))],
}
def particle_sprite(sk, t, vi, f):
    v = t["variants"][vi]
    if t["name"] == "petal": return spr_petal(f, v)
    if t["name"] == "leaf": return spr_leaf(f, v)
    if t["name"] == "firefly": return spr_firefly(f)
    if t["name"] == "sunmote": return spr_mote(f)
    return spr_snow(vi, f)
def build_particles():
    out = {}
    for sk, types in PARTICLES.items():
        d = os.path.join(SEA, sk, "particles"); os.makedirs(d, exist_ok=True)
        rows = [(ti, vi) for ti, t in enumerate(types) for vi in range(len(t["variants"]))]
        W = max(t["frames"] for t in types) * CELL; Hh = len(rows) * CELL
        sheet = np.zeros((Hh, W, 4), np.uint8); frames = {}; anims = {}
        for r_, (ti, vi) in enumerate(rows):
            t = types[ti]; key = f"{t['name']}_{vi}"; anims[key] = []
            for f in range(t["frames"]):
                o = particle_sprite(sk, t, vi, f)
                for (y, x), cn in np.ndenumerate(o):
                    if cn is not None: sheet[r_ * CELL + y, f * CELL + x] = list(hx(V3[cn]) * 255 + 0.5) + [255]
                fn = f"{key}_{f:02d}"; frames[fn] = dict(x=f * CELL, y=r_ * CELL, w=CELL, h=CELL); anims[key].append(fn)
        Image.fromarray(sheet, "RGBA").save(os.path.join(d, "sheet.png"))
        meta = {"season": sk, "image": "sheet.png", "cell": CELL, "pivot": [3.5, 3.5], "palette": "v3（motion/palette.json），alpha 0/255",
                "frames": frames, "anims": anims,
                "types": [dict(name=t["name"], fps=t["fps"], frames=t["frames"], variants=[f"{t['name']}_{vi}" for vi in range(len(t["variants"]))], emitter=t["emitter"]) for t in types],
                "layer": "畫喺 fore 之上、UI 之下；唔受 lightmap（H4 夜晚引擎乘 0.75 亮度）；位置用整數像素",
                "note": "emitter 數值係建議（px/s，畫面座標 195×422）；perVariant ＝ 該時段 rate 倍數（0＝唔出）"}
        json.dump(meta, open(os.path.join(d, "particles.json"), "w"), ensure_ascii=False, indent=1)
        out[sk] = (sheet, meta)
    return out

def scatter_particles(img, sk, H, seed=5, scale=1):
    """預覽用：照 emitter 密度喺畫面撒一 frame 粒子（靜態 snapshot）"""
    sheet, meta = PCACHE[sk]; r = rng(seed + hash(sk) % 97); out = img.copy()
    for t in meta["types"]:
        mult = t["emitter"]["perVariant"][H]
        n = int(t["emitter"]["max"] * mult)
        for k in range(n):
            vi = int(r.integers(0, len(t["variants"]))) if "weights" not in t["emitter"] else int(r.choice(len(t["variants"]), p=t["emitter"]["weights"]))
            fn = meta["anims"][t["variants"][vi]][int(r.integers(0, t["frames"]))]; fr = meta["frames"][fn]
            sp = Image.fromarray(sheet[fr["y"]:fr["y"] + CELL, fr["x"]:fr["x"] + CELL])
            if t["name"] == "firefly": x, y = int(r.integers(10, LW - 10)), int(r.integers(230, 400))
            elif t["name"] == "sunmote": x, y = int(r.integers(10, LW - 10)), int(r.integers(60, 300))
            elif t["name"] == "leaf": x, y = int(r.integers(0, 160)), int(r.integers(60, 420))
            else: x, y = int(r.integers(0, LW - 8)), int(r.integers(0, LH - 8))
            out.alpha_composite(sp, (x, y))
    return out
PCACHE = {}
