#!/usr/bin/env python3
"""build_evo6_concept.py — 團絨 6 階段進化「尺寸／外形」概念草圖（只係 idle 1 幀，唔係動畫）。
Pillow + numpy 逐像素程式繪製，無 AI。每階段用自己畫布尺寸，pivot=(w/2, h-3)。
GDD lock（遊策）：光卵24 / 絨點28 / 絨芽32 / 絨跳38 / 守夜者44（螢絨・燦光・柔光・微塵）/ 靜光48（4 分支）
Output -> ../sprites/tuanrong/evo6_concept/
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_tuanrong as bt
ROOT = os.path.normpath(os.path.join(HERE, ".."))
SPR = os.path.join(ROOT, "sprites", "tuanrong")
OUT = os.path.join(SPR, "evo6_concept")
IDX = dict(bt.IDX); NAMES = list(bt.PAL.keys())

# ---- 分支調色盤：共用 31 槽，只換「佢用唔著」嘅槽（同 palette_lumi 做法一樣）
SWAPS = {
 "base": {},
 "lumi": {"peach0": ("lumi_fur0", "#A99FD8"), "peach1": ("lumi_fur1", "#C6BDEA"), "peach2": ("lumi_fur2", "#E2DCF6"),
          "egg_dark": ("fly_d", "#8FCB4E"), "egg_shade": ("fly", "#CFF26A"), "cyan": ("fly_core", "#F2FFB8")},
 # 微塵：灰米絨（塵兔）＋ 眼鏡反光；換 peach×3（柔光專用）、cyan（未用）
 "dust": {"peach0": ("dust0", "#8C8296"), "peach1": ("dust1", "#B1A8B5"), "peach2": ("dust2", "#D5CDD3"),
          "cyan": ("lens", "#CFEAF2")},
}
def pal_rgb(key):
    out = [(0, 0, 0)]
    for n in NAMES:
        h = SWAPS[key][n][1] if n in SWAPS[key] else bt.PAL[n]
        out.append(tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)))
    return out
def pal_json(key):
    return [{"index": IDX[n], "name": SWAPS[key][n][0] if n in SWAPS[key] else n,
             "hex": SWAPS[key][n][1] if n in SWAPS[key] else bt.PAL[n]} for n in NAMES]

TH = bt.TH
RAMP = {
 "baby":   ["cream1", "cream2", "cream3", "cream4"],
 "cream":  ["cream0", "cream1", "cream2", "cream3"],
 "radiant": ["cream1", "cream2", "cream3", "cream4"],
 "soft":   ["peach0", "peach1", "peach2", "cream3"],
 "lumi":   ["zzz", "peach0", "peach1", "peach2"],          # = lumi_fur 槽
 "dust":   ["peach0", "peach1", "peach2", "white"],        # = dust 槽（灰米）
 "egg":    ["egg_dark", "egg_shade", "glow", "glow_mid"],
 "shell":  ["egg_dark", "egg_shade", "glow", "glow_mid"],
}

# ---------------------------------------------------------------- helpers
def dil(m):
    d = m.copy(); d[1:] |= m[:-1]; d[:-1] |= m[1:]; d[:, 1:] |= m[:, :-1]; d[:, :-1] |= m[:, 1:]; return d
def ring(m): return dil(m) & ~m
def outl(cv, m):  # 獨立部件描邊（只落喺透明位）
    cv.a[ring(m) & (cv.a == 0)] = IDX["outline"]
def shade(cv, m, cx, cy, rx, ry, ramp, bias=0.15):
    nx = (cv.xx + .5 - cx) / rx; ny = (cv.yy + .5 - cy) / ry
    r2 = np.clip(nx * nx + ny * ny, 0, 1.4)
    sv = -(0.55 * nx + 0.8 * ny) - 0.38 * r2 + bias
    kk = np.clip(sum((sv > t).astype(int) for t in TH), 0, 3)
    rc = np.array([IDX[c] for c in RAMP[ramp]], np.uint8)
    cv.a[m] = rc[kk][m]; return kk
def fluff(cv, cx, cy, rx, ry, N, rb, skip_top=False):
    m = cv.ell(cx, cy, rx, ry)
    for i in range(N):
        th = 2 * math.pi * (i + 0.5) / N; sn = math.sin(th)
        if sn > 0.78: continue
        if skip_top and sn < -0.85: continue
        m |= cv.ell(cx + (rx - rb * .45) * math.cos(th), cy + (ry - rb * .45) * sn, rb, rb)
    return m
def rot_ell(cv, cx, cy, a, b, ang):
    d = (math.cos(math.radians(ang)), -math.sin(math.radians(ang)))
    X = cv.xx + .5 - cx; Y = cv.yy + .5 - cy
    u = X * d[0] + Y * d[1]; v = -X * d[1] + Y * d[0]
    return (u / a) ** 2 + (v / b) ** 2 <= 1.0
def feet(cv, cx, bottom, fx, frx, fry, col="orange", cold="orange_d"):
    for s in (-1, 1):
        m = cv.ell(cx + s * fx, bottom + 0.3, frx, fry); cv.paint(m, col); cv.solid |= m
        cv.paint(m & (cv.yy >= int(bottom + 0.6)), cold)
def arms(cv, cx, cy, rx, ry, r, col):
    for s in (-1, 1):
        m = cv.ell(cx + s * (rx - 0.2), cy + ry * 0.22, r, r); cv.paint(m, col); cv.solid |= m
EYE_M = {"open": [".##.", "#w##", "####", ".##."]}
FACE_MODE = "dopey"          # "orig" = 第一版（對比圖用）；"dopey" = Kurt 2026-10-31「好似螢絨咁呆啲」
# ---- 呆萌面（蠢蠢地但覺得自己好醒）：
#   眼：平頂「半瞇」＝上面一行係深一級毛色眼皮（l），細粒、分得好開、擺得低（大額頭）、高光喺下面（望上望空、有啲放空）
#   口：細細個 ω 貓口（好似暗爽／自以為醒），擺得貼近眼
#   面整體右移（向右睇），同螢絨一樣
DOPE_EYE = {
 "big":   ["###", "w##", "###"],                  # 44/48：3×3 細豆眼（舊版 4×5 大眼 → 細粒＝呆）
 "mid":   ["###", "w##", "###"],                  # 38：3×3 豆眼（高光左上）
 "baby":  [".##.", "#w##", "####", ".##."],      # 28 絨點：BB 大豆眼（同 big 一樣 4×4，但分得更開）
 "small": ["##", "w#"],                            # 32：2×2 豆眼
}
# 歪嘴笑：向右（面向）嗰邊口角翹高 → 「哼，我好醒」
DOPE_MOUTH = {"big": ["...#", "#.#.", ".#.."], "mid": ["..#", "##."], "small": ["..#", "##."]}
def face(cv, cx, cy, rx, ry, size, bm, dx=1, eye="open", mouth="smile", eoff=0.40, ey_k=0.08, blush=True, wcol="cream4", lid=None, k=None, sepk=None, eyet=None):
    if FACE_MODE == "orig":
        fcx = cx + dx; ey = cy + ry * ey_k
        cm = {"#": "outline", "w": wcol, "r": "blush_d"}
        t = EYE_M[eye] if size == "mid" else bt.EYE[size == "big"][eye]
        bt.draw_tmpl_c(cv, fcx - rx * eoff, ey, t, cm); bt.draw_tmpl_c(cv, fcx + rx * eoff, ey, t, cm)
        mt = bt.MOUTH[size == "big"][mouth]
        bt.draw_tmpl_c(cv, fcx, ey + max(3, ry * 0.36), mt, cm)
        if blush:
            br = (2.2, 1.3) if size == "big" else (1.6, 0.9)
            for s in (-1, 1):
                m = cv.ell(fcx + s * rx * 0.64, ey + ry * 0.26, *br); cv.a[m & bm & (cv.a != IDX["outline"])] = IDX["blush"]
        return fcx, ey
    # ---- dopey
    fcx = cx + dx + 1; ey = cy + ry * (DOPE_K[size] if k is None else k)
    sep = rx * (DOPE_SEP[size] if sepk is None else sepk)
    cm = {"#": "outline", "w": wcol, "l": lid or "outline"}
    t = DOPE_EYE[eyet or size]; h = len(t)
    for s in (-1, 1):
        bt.draw_tmpl_c(cv, fcx + s * sep, ey, t, cm)
    mt = DOPE_MOUTH[size]
    my = ey + h / 2 + len(mt) / 2 + (0.5 if size == "big" else 0.0) + (1.0 if eyet == "baby" else 0.0)
    bt.draw_tmpl_c(cv, fcx + 0.5, my, mt, cm)
    if blush:
        br = (2.0, 1.1) if size == "big" else (1.4, 0.8)
        for s in (-1, 1):
            m = cv.ell(fcx + s * (sep + (2.2 if size == "big" else 1.4)), ey + h / 2 + 1.4, *br); cv.a[m & bm & (cv.a != IDX["outline"])] = IDX["blush"]
    return fcx, ey
DOPE_K = {"big": 0.26, "mid": 0.22, "small": 0.22}      # 眼擺低啲（大額頭）
DOPE_SEP = {"big": 0.46, "mid": 0.45, "small": 0.42}    # 兩眼分開啲
def glow_bulb(cv, x, y, r, core=True, cols=("glow", "glow_mid", "glow_core")):
    m = cv.ell(x, y, r + 0.8, r + 0.8); cv.paint(m, cols[0]); cv.paint(cv.ell(x, y, r, r), cols[1])
    if core: cv.put(x - .5, y - .5, cols[2]); cv.put(x + .5, y - .5, cols[2]); cv.put(x - .5, y + .5, cols[2])
    outl(cv, m); return m
def stem(cv, x, y0, ln, w=1, lean=0.0, cols=("orange", "orange_d")):
    pts = []
    for j in range(ln + 1):
        t = j / max(1, ln); px = x + lean * t * t; py = y0 - j
        for k in range(w):
            cv.put(px + k, py, cols[min(k, 1)]); cv.solid[int(np.clip(round(py), 0, cv.n - 1)), int(np.clip(round(px + k), 0, cv.n - 1))] = True
        pts.append((px, py))
    return pts[-1]
def leaf(cv, x, y, a, b, ang, col="leaf", cold="leaf_d"):
    m = rot_ell(cv, x, y, a, b, ang); cv.paint(m, col); cv.solid |= m
    d = (math.cos(math.radians(ang)), -math.sin(math.radians(ang)))
    for s in np.linspace(-a * 0.5, a * 0.4, max(2, int(a))):
        cv.put(x + d[0] * s, y + d[1] * s, cold)
    return m
def ear(cv, bx, by, h, w, lean, cols):
    """尖耳：三角絨（底闊 w，高 h，傾 lean）"""
    m = np.zeros_like(cv.solid)
    for j in range(int(h) + 1):
        t = j / h; half = w * (1 - t) * 0.5 + 0.35
        x = bx + lean * t; y = by - j
        m |= (np.abs(cv.xx + .5 - x) <= half) & (cv.yy == int(round(y)))
    cv.paint(m, cols[0]); cv.solid |= m
    tip = m & (cv.yy <= by - h * 0.55); cv.paint(tip, cols[1])
    return m
def tail_puff(cv, x, y, r, ramp, tip=None, cx=None, cy=None):
    m = cv.ell(x, y, r, r * 0.9) | cv.ell(x - r * 0.6, y - r * 0.8, r * 0.7, r * 0.7)
    shade(cv, m, x, y, r, r, ramp); cv.solid |= m
    if tip: cv.paint(cv.ell(x - r * 0.75, y - r * 1.05, r * 0.5, r * 0.5) & m, tip)
    return m
def sparkle(cv, x, y, c0="glow_core", c1="glow_mid"):
    cv.put(x, y, c0)
    for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        if cv.a[int(np.clip(y + oy, 0, cv.n - 1)), int(np.clip(x + ox, 0, cv.n - 1))] == 0: cv.put(x + ox, y + oy, c1)
def aura(cv, col, col2=None, dist=2):
    """全體光環：外輪廓再出 dist px 嘅點狀光（alpha 255，無 AA）"""
    s = cv.a > 0; d1 = s
    for _ in range(dist - 1): d1 = dil(d1)
    r = dil(d1) & ~d1
    pat = ((cv.xx * 2 + cv.yy) % 5 == 0) & (cv.yy < cv.n - 9)
    cv.a[r & pat & (cv.a == 0)] = IDX[col]
    if col2:
        r2 = dil(dil(d1)) & ~dil(d1); cv.a[r2 & ((cv.xx * 3 + cv.yy) % 7 == 0) & (cv.a == 0)] = IDX[col2]
def spots(cv, bm, pts, col, cx, cy, rx, ry, big=False):
    for (a, b) in pts:
        x, y = int(round(cx + a * rx)), int(round(cy + b * ry))
        for ox, oy in ([(0, 0)] + ([(1, 0), (0, 1), (1, 1)] if big else [])):
            xx, yy = x + ox, y + oy
            if 0 <= xx < cv.n and 0 <= yy < cv.n and bm[yy, xx] and cv.a[yy, xx] != IDX["outline"]: cv.a[yy, xx] = IDX[col]

# ---------------------------------------------------------------- stage renderers (each returns (a, palette_key))
def s1_egg():
    """光卵 24：重畫細蛋＋星塵＋頂部一條微裂（快孵）"""
    S = 24; cv = bt.Cv(S); cx = 12.0; rx, ry = 6.9, 8.6; bottom = 21.0; cy = bottom - ry
    m = bt.egg_mask(cv, cx, cy, rx, ry); shade(cv, m, cx, cy, rx, ry, "egg", 0.2); cv.solid |= m
    for (a, b, c) in ((-0.35, -0.3, "cream4"), (0.4, 0.2, "cream3"), (-0.2, 0.55, "cream4"), (0.1, 0.05, "glow_warm"), (-0.55, 0.2, "glow_warm")):
        cv.put(cx + a * rx, cy + b * ry, c)
    cv.put(cx + 0.4 * rx + 1, cy + 0.2 * ry, "cream3")
    cv.outline()
    for (x, y) in ((cx + 1, cy - ry + 2), (cx + 2, cy - ry + 3), (cx + 1, cy - ry + 4)): cv.put(x, y, "egg_dark")  # 微裂
    cv.put(cx - rx * .5, cy - ry * .55, "cream4"); cv.put(cx - rx * .5 + 1, cy - ry * .55, "cream4")
    sparkle(cv, 3, 6); sparkle(cv, 21, 9); cv.put(20, 18, "glow")
    return cv.a, "base"

def s2_dot():
    """絨點 28（初生）：新 → 眼開（大 BB 眼）、頭頂第一撮捲毛、坐喺半個蛋殼入面（無腳）"""
    S = 28; cv = bt.Cv(S); cx = 14.0; G = 25
    rx, ry = 8.4, 7.6; cy = G - 1 - ry - 2.5
    bm = fluff(cv, cx, cy, rx, ry, 8, 1.6, skip_top=True); kk = shade(cv, bm, cx, cy, rx, ry, "baby"); cv.solid |= bm
    # 捲毛 tuft（新特徵，2px 粗捲）
    tx, ty = cx + 0.5, cy - ry + 0.5
    for (dx, dy) in ((0, 0), (1, 0), (0, -1), (1, -1), (1, -2), (2, -2), (2, -3), (1, -4), (0, -4), (-1, -4), (-1, -3), (0, -3)):
        x, y = int(tx + dx), int(ty + dy); cv.a[y, x] = IDX["cream3"]; cv.solid[y, x] = True
    cv.outline()
    # 蛋殼杯（三角鋸齒頂）
    top = G - 6 + np.abs((cv.xx % 6) - 3)
    sh = bt.egg_mask(cv, cx, G - 5.0, rx + 1.4, 5.6) & (cv.yy >= top) & (cv.yy <= G)
    shade(cv, sh, cx, G - 4, rx + 1, 5, "shell", 0.25)
    rg = ring(sh) & (cv.yy <= G + 1); cv.a[rg] = IDX["outline"]
    for x in (cx - 4, cx + 4): cv.put(x, G - 3, "cream4")
    cv.put(cx - 5, G - 2, "glow_warm")
    face(cv, cx, cy - 1.5, rx, ry, "mid", bm, eoff=0.40, ey_k=0.0, mouth="smile", lid="cream1", k=0.0, eyet="baby", sepk=0.42, dx=0)
    sparkle(cv, 3, 7); cv.put(24, 5, "glow_mid")
    return cv.a, "base"

def s3_sprout():
    """絨芽 32：新 → 長出腳仔同手、頭頂雙葉芽（綠，未發光）、絨毛輪廓"""
    S = 32; cv = bt.Cv(S); cx = 16.0; G = 29; bottom = G - 1
    rx, ry = 10.2, 8.8; cy = bottom - ry
    feet(cv, cx, bottom, rx * 0.45, 2.0, 1.4)
    arms(cv, cx, cy, rx, ry, 1.6, "cream1")
    bm = fluff(cv, cx, cy, rx, ry, 10, 1.7); kk = shade(cv, bm, cx, cy, rx, ry, "cream"); cv.solid |= bm
    cv.a[cv.ell(cx, cy + ry * 0.35, rx * 0.5, ry * 0.45) & bm & (kk <= 1)] = IDX["cream2"]
    tip = stem(cv, cx, int(cy - ry) + 1, 3, 1, 0.5, ("leaf_d", "leaf_d"))
    leaf(cv, tip[0] - 2.4, tip[1] - 0.8, 2.8, 1.5, 155); leaf(cv, tip[0] + 2.6, tip[1] - 1.4, 3.0, 1.6, 30)
    cv.outline()
    cv.put(tip[0], tip[1] - 1, "leaf"); outl(cv, cv.a == IDX["leaf"])
    face(cv, cx, cy, rx, ry, "small", bm, dx=1, eoff=0.42, lid="cream0")
    cv.put(cx - rx * .45, cy - ry * .5, "cream4"); cv.put(cx - rx * .45 + 1, cy - ry * .5, "cream4")
    return cv.a, "base"

def s4_hop():
    """絨跳 38（少年）：新 → 第一次「著燈」（芽變燈泡）、尖耳、捲尾、肚白、身形直身少少"""
    S = 38; cv = bt.Cv(S); cx = 19.0; G = 35; bottom = G - 1
    rx, ry = 10.8, 10.2; cy = bottom - ry
    tail_puff(cv, cx - rx - 1.5, cy + 1.5, 3.4, "cream", tip="orange")
    feet(cv, cx, bottom, rx * 0.45, 2.2, 1.6)
    arms(cv, cx, cy, rx, ry, 1.9, "cream1")
    for s in (-1, 1): ear(cv, cx + s * rx * 0.55 + 1, cy - ry * 0.62, 6, 5.5, s * 1.6, ("cream1", "orange"))
    bm = fluff(cv, cx, cy, rx, ry, 12, 2.0); kk = shade(cv, bm, cx, cy, rx, ry, "cream"); cv.solid |= bm
    cv.a[cv.ell(cx + 1, cy + ry * 0.36, rx * 0.5, ry * 0.46) & bm] = IDX["cream3"]
    tip = stem(cv, cx + 1, int(cy - ry) + 1, 4, 1, 0.6)
    leaf(cv, tip[0] - 2.2, tip[1] + 1.2, 2.2, 1.1, 160)
    cv.outline()
    glow_bulb(cv, tip[0] + 0.5, tip[1] - 2.2, 2.2)
    face(cv, cx, cy, rx, ry, "mid", bm, dx=1, eoff=0.40, lid="cream0")
    cv.put(cx - rx * .45, cy - ry * .5, "cream4"); cv.put(cx - rx * .45 + 1, cy - ry * .5, "cream4")
    sparkle(cv, tip[0] + 6, tip[1] - 4)
    return cv.a, "base"

# --- 守夜者 / 靜光 共用骨架
def adult_base(S, rx, ry, ramp, N, rb, ear_h, ear_cols, eye="big"):
    cv = bt.Cv(S); cx = S / 2; G = S - 3; bottom = G - 1; cy = bottom - ry
    return cv, cx, cy, bottom

def s5_radiant(elder=False):
    """燦光：新 → 奶白金新配色、橙色「日紋」條紋、太陽放射燈泡、金尖耳、光尾
       靜光：＋背後日輪光環（halo）、頸鬃、雙金翼、點狀光環 aura"""
    S = 48 if elder else 44; cv = bt.Cv(S); cx = S / 2; G = S - 3; bottom = G - 1
    rx, ry = (13.6, 11.6) if elder else (12.6, 10.8); cy = bottom - ry
    if elder:  # 日輪 halo：身後一個大光拱（頭頂上方半圓）
        hx_, hy_ = cx + 1, cy - ry * 0.35
        hm = cv.ell(hx_, hy_, 17.5, 15.5) & ~cv.ell(hx_, hy_, 15.8, 13.9) & (cv.yy < hy_ + 2)
        cv.paint(hm, "glow"); cv.paint(hm & (((cv.xx + cv.yy) % 4) == 0), "glow_core"); cv.solid |= hm
        for k, (a, b, ang) in enumerate(((8.4, 2.9, 140), (6.8, 2.4, 165))):   # 金翼（背後左上）
            d = (math.cos(math.radians(ang)), -math.sin(math.radians(ang)))
            bx0, by0 = cx - rx * 0.6, cy - ry * 0.2 + k * 2
            w = rot_ell(cv, bx0 + d[0] * a * 0.7, by0 + d[1] * a * 0.7, a, b, ang)
            cv.paint(w, "glow"); cv.paint(w & rot_ell(cv, bx0 + d[0] * a * 0.7 - .6, by0 + d[1] * a * 0.7 - .8, a - 1.5, b - 1.2, ang), "glow_mid"); cv.solid |= w
    tail_puff(cv, cx - rx - 1.2, cy + 1, 4.0 if elder else 3.6, "radiant", tip="glow")
    feet(cv, cx, bottom, rx * 0.45, 2.5, 1.8)
    arms(cv, cx, cy, rx, ry, 2.2, "cream2")
    for s in (-1, 1): ear(cv, cx + s * rx * 0.55 + 1, cy - ry * 0.6, 7.5 if elder else 6.5, 6.0, s * 2.0, ("cream2", "glow"))
    bm = fluff(cv, cx, cy, rx, ry, 14, 2.6); kk = shade(cv, bm, cx, cy, rx, ry, "radiant"); cv.solid |= bm
    cv.a[cv.ell(cx + 1, cy + ry * 0.36, rx * 0.5, ry * 0.46) & bm] = IDX["cream4"]
    tip = stem(cv, cx + 1, int(cy - ry) + 1, 3, 2)
    cv.outline()
    # 日紋（新 pattern）：身側橙 chevron
    for s in (-1, 1):
        for j in range(2):
            x0 = cx + s * rx * (0.82 - 0.16 * j); y0 = cy - ry * 0.1 + j * 3
            for t in range(3):
                xx = x0 - s * t; yy = y0 + (t if t < 2 else 0) - 1
                xi, yi = int(round(xx)), int(round(yy))
                if bm[yi, xi] and cv.a[yi, xi] != IDX["outline"]: cv.a[yi, xi] = IDX["orange"]
    cv.put(cx + 1, cy - ry + 3, "orange"); cv.put(cx, cy - ry + 4, "orange"); cv.put(cx + 2, cy - ry + 4, "orange")  # 額日紋
    # 太陽燈泡
    bx, by = tip[0] + 0.5, tip[1] - 3.0
    rr = 3.2 if elder else 2.6; ln = (8.5, 7.0) if elder else (6.5, 5.2)
    for i, a in enumerate(range(-170, 11, 20 if elder else 30)):
        L = ln[i % 2]; ar = math.radians(a)
        for s_ in range(int(rr) + 1, int(L) + 1):
            x, y = bx + math.cos(ar) * s_, by + math.sin(ar) * s_
            if 0 <= y < S and cv.a[int(round(y)), int(round(np.clip(x, 0, S - 1)))] in (0,): cv.put(x, y, "glow_mid" if s_ < L else "glow_warm")
    glow_bulb(cv, bx, by, rr)
    face(cv, cx, cy, rx, ry, "big", bm, dx=1, lid="cream1")
    cv.put(cx - rx * .45, cy - ry * .52, "cream4"); cv.put(cx - rx * .45 + 1, cy - ry * .52, "cream4")
    if elder:  # 胸前日徽（新 pattern）
        ux, uy = cx + 1, cy - ry * 0.55
        for (dx, dy, c) in ((0, 0, "glow_core"), (1, 0, "glow"), (-1, 0, "glow"), (0, 1, "glow"), (0, -1, "glow"),
                            (2, 0, "orange"), (-2, 0, "orange"), (1, 1, "orange"), (-1, 1, "orange"), (1, -1, "orange"), (-1, -1, "orange")):
            xi, yi = int(ux + dx), int(uy + dy)
            if bm[yi, xi] and cv.a[yi, xi] != IDX["outline"]: cv.a[yi, xi] = IDX[c]
    if elder:
        aura(cv, "glow", "glow_core"); sparkle(cv, S - 4, 8); sparkle(cv, 3, 14)
    return cv.a, "base"

def s5_soft(elder=False):
    """柔光：新 → 蜜桃新配色、垂耳葉（長葉耳）、奶油圓斑、葉尾、葉苞燈
       靜光：＋花冠（5 瓣）、背後葉翼、飄花瓣 aura"""
    S = 48 if elder else 44; cv = bt.Cv(S); cx = S / 2; G = S - 3; bottom = G - 1
    rx, ry = (14.4, 12.0) if elder else (13.4, 11.2); cy = bottom - ry
    if elder:
        for k, (a, b, ang) in enumerate(((7.8, 2.8, 150), (6.2, 2.3, 120))):
            w = leaf(cv, cx - rx * 0.62 - 3, cy - ry * 0.25 - k * 3, a, b, ang)
    # 葉尾
    leaf(cv, cx - rx - 2.0, cy + ry * 0.35, 4.2 if elder else 3.6, 1.9, 200)
    feet(cv, cx, bottom, rx * 0.45, 2.6, 1.8)
    arms(cv, cx, cy, rx, ry, 2.3, "peach1")
    bm = fluff(cv, cx, cy, rx, ry, 12, 3.0); kk = shade(cv, bm, cx, cy, rx, ry, "soft"); cv.solid |= bm
    cv.a[cv.ell(cx + 1, cy + ry * 0.36, rx * 0.5, ry * 0.45) & bm & (kk <= 1)] = IDX["peach2"]
    # 垂耳葉（兩邊向下垂）
    for s in (-1, 1):
        leaf(cv, cx + s * (rx * 0.78), cy - ry * 0.35, 4.6 if elder else 4.0, 2.0, 90 + s * -70 + (180 if s < 0 else 0) - 180 * (s < 0) + (0 if s > 0 else 0) if False else (-55 if s > 0 else 235))
    tip = stem(cv, cx + 1, int(cy - ry) + 1, 3, 1)
    for s in (-1, 1): leaf(cv, tip[0] + s * 2.6, tip[1] - 0.6, 2.6, 1.3, 25 if s > 0 else 155)
    cv.outline()
    spots(cv, bm, [(-0.55, -0.25), (-0.3, 0.55), (0.6, 0.55), (0.65, -0.35), (-0.75, 0.25), (0.05, -0.55)], "cream3", cx, cy, rx, ry, big=True)
    glow_bulb(cv, tip[0] + 0.5, tip[1] - 3.0, 2.6 if elder else 2.2)
    if elder:  # 花冠
        for i, a in enumerate(range(-160, 0, 32)):
            ar = math.radians(a); px, py = cx + 1 + math.cos(ar) * rx * 0.55, cy - ry * 0.82 + math.sin(ar) * 3.0
            pm = cv.ell(px, py, 2.4, 2.4); cv.paint(pm, "blush" if i % 2 else "cream4"); cv.put(px, py, "glow"); outl(cv, pm)
    face(cv, cx, cy + 0.5, rx, ry, "big", bm, dx=1, mouth="smile", lid="peach0")
    if elder:
        aura(cv, "blush", "cream4")
        for (x, y) in ((4, 10), (S - 5, 15), (S - 7, 4)):
            cv.put(x, y, "blush"); cv.put(x + 1, y, "blush"); cv.put(x, y + 1, "blush_d")
    return cv.a, "base"

def s5_lumi(elder=False):
    """螢絨：新 → 夜紫新配色、觸角燈、尾燈、背翼、身上光點
       靜光：＋雙對大翼、長觸角大燈＋第三支冠燈、星座光點連線、大尾燈、螢光 aura"""
    S = 48 if elder else 44; cv = bt.Cv(S); cx = S / 2; G = S - 3; bottom = G - 1
    rx, ry = (13.4, 11.4) if elder else (12.6, 10.8); cy = bottom - ry
    wings = ((8.6, 3.2, 150), (7.6, 2.8, 118), (6.0, 2.4, 172)) if elder else ((6.4, 2.6, 150), (5.6, 2.3, 125))
    for (a, b, ang) in wings:
        d = (math.cos(math.radians(ang)), -math.sin(math.radians(ang)))
        bx0, by0 = cx - rx * 0.62, cy - ry * 0.25
        wc = (bx0 + d[0] * a * 0.62, by0 + d[1] * a * 0.62)
        m = rot_ell(cv, wc[0], wc[1], a, b, ang); cv.paint(m, "drop"); cv.solid |= m
        hi = rot_ell(cv, wc[0] + d[0] - .6, wc[1] + d[1] - .6, a - 2, b - 1.4, ang); cv.paint(m & hi, "white")
    tx, ty = cx - rx * 0.92, cy + ry * 0.42
    tr = 5.0 if elder else 4.2
    tail = cv.ell(tx, ty, tr, tr * 0.9); cv.paint(tail, "egg_dark"); cv.solid |= tail
    feet(cv, cx, bottom, rx * 0.45, 2.4, 1.7)
    arms(cv, cx, cy, rx, ry, 2.1, "peach0")
    bm = fluff(cv, cx, cy, rx, ry, 14, 2.4); kk = shade(cv, bm, cx, cy, rx, ry, "lumi"); cv.solid |= bm
    cv.a[cv.ell(cx + 2, cy + ry * 0.34, rx * 0.5, ry * 0.45) & bm & (kk <= 1)] = IDX["peach1"]
    ants = []
    specs = ((0, 0.45, 12), (6, 0.9, 11), (-4, -0.5, 9)) if elder else ((1, 0.45, 9), (6, 0.85, 8))
    for (bo, lean, ln) in specs:
        pts = []
        for j in range(ln + 1):
            t = j / ln; pts.append((cx + bo + lean * j * 0.8 + 1.6 * t * t * np.sign(lean), cy - ry + 1.5 - j + 1.4 * t * t))
        ants.append(pts)
    cv.outline()
    for pts in ants:
        for (x, y) in pts:
            if cv.a[int(round(y)), int(round(x))] == 0 or y < cy - ry: cv.put(x, y, "outline")
    ants = [p[-1] for p in ants]
    seg = tail & ~bm
    cv.a[cv.ell(tx - 1.2, ty + 0.3, tr * 0.7, tr * 0.6) & seg & (cv.a != IDX["outline"])] = IDX["egg_shade"]
    cv.a[cv.ell(tx - 2.0, ty, tr * 0.35, tr * 0.35) & seg & (cv.a != IDX["outline"])] = IDX["cyan"]
    for (x, y) in ants:
        glow_bulb(cv, x + .4, y - .6, 2.0 if elder else 1.6, cols=("egg_shade", "egg_shade", "cyan"))
    dots = [(-0.6, -0.2), (-0.35, -0.6), (0.3, -0.65), (-0.75, 0.3), (-0.4, 0.15), (0.72, -0.3)]
    if elder: dots += [(-0.15, -0.35), (0.55, 0.65), (-0.6, 0.65), (0.1, -0.8)]
    spots(cv, bm, dots, "cyan", cx, cy, rx, ry)
    if elder:  # 星座連線（fly_d 細線）
        for (p, q) in ((0, 1), (1, 6), (6, 2)):
            (a1, b1), (a2, b2) = dots[p], dots[q]
            for t in np.linspace(0.25, 0.75, 4):
                x = cx + (a1 + (a2 - a1) * t) * rx; y = cy + (b1 + (b2 - b1) * t) * ry
                xi, yi = int(round(x)), int(round(y))
                if bm[yi, xi] and cv.a[yi, xi] not in (IDX["outline"], IDX["cyan"]): cv.a[yi, xi] = IDX["egg_dark"]
    face(cv, cx, cy, rx, ry, "big", bm, dx=2, wcol="cyan", lid="zzz")
    if elder:
        aura(cv, "egg_shade", "cyan"); sparkle(cv, S - 5, 6, "cyan", "egg_shade"); sparkle(cv, S - 3, 26, "cyan", "egg_shade")
    return cv.a, "lumi"

def s5_dust(elder=False):
    """微塵（新設計，傻得意＋小聰明）：新 → 灰米塵兔配色、亂翹呆毛、圓眼鏡、肚前一粒小燈泡（似揸住盞燈）、身上塵點、一舊塵雲跟住
       靜光（塵賢者）：＋大眼鏡＋白長眉鬚、塵粒軌道環（halo）、頭頂一盞吊燈、書頁翼（一對紙翼）"""
    S = 48 if elder else 44; cv = bt.Cv(S); cx = S / 2; G = S - 3; bottom = G - 1
    rx, ry = (13.8, 11.6) if elder else (13.0, 11.0); cy = bottom - ry
    if elder:  # 紙頁翼
        for k, ang in enumerate((150, 125)):
            m = rot_ell(cv, cx - rx * 0.6 - 3, cy - ry * 0.3 - k * 2.5, 6.6 - k, 2.6, ang)
            cv.paint(m, "cream4"); cv.paint(m & (cv.yy > cy - ry * 0.3 - k * 2.5), "cream2"); cv.solid |= m
    # 塵雲尾（雲狀三粒）
    for (dx, dy, r) in ((-rx - 1.0, ry * 0.45, 2.6), (-rx - 3.2, ry * 0.15, 2.0), (-rx - 1.6, ry * -0.1, 1.6)):
        m = cv.ell(cx + dx, cy + dy, r, r); shade(cv, m, cx + dx, cy + dy, r, r, "dust"); cv.solid |= m
    feet(cv, cx, bottom, rx * 0.45, 2.4, 1.7, "cream0", "orange_dd")
    arms(cv, cx, cy, rx, ry, 2.1, "peach0")
    bm = fluff(cv, cx, cy, rx, ry, 18, 2.2); kk = shade(cv, bm, cx, cy, rx, ry, "dust"); cv.solid |= bm
    # 呆毛（亂翹）
    for (bx, pts) in ((0, ((0, 0), (0, -1), (1, -2), (2, -3), (2, -4), (1, -5))), (-4, ((0, 0), (-1, -1), (-2, -2), (-2, -3))), (4, ((0, 0), (1, -1), (1, -2)))):
        for (dx, dy) in pts:
            x, y = cx + 1 + bx + dx, cy - ry + 1 + dy; cv.put(x, y, "peach1"); cv.solid[int(y), int(x)] = True
    cv.outline()
    spots(cv, bm, [(-0.6, -0.1), (-0.3, 0.6), (0.62, 0.5), (0.5, -0.55), (-0.75, 0.4), (-0.2, -0.65), (0.8, 0.0)], "cream0", cx, cy, rx, ry)
    fcx, ey = face(cv, cx, cy, rx, ry, "big", bm, dx=2, blush=True, lid="peach0")
    # 圓眼鏡（outline 圈＋lens 反光）
    gr = 3.6 if elder else 3.1
    gk = DOPE_SEP["big"] if FACE_MODE == "dopey" else 0.40
    for s in (-1, 1):
        ex = fcx + s * rx * gk
        lm = cv.ell(ex, ey, gr, gr); rg = lm & ~cv.ell(ex, ey, gr - 1.0, gr - 1.0)
        cv.a[lm & ~rg] = IDX["cyan"]; cv.a[rg] = IDX["outline"]
        if True:   # 鏡片後面：細豆眼（2×2）
            for ox, oy in ((0, 0), (1, 0), (0, 1), (1, 1)): cv.put(ex + ox - .5, ey + oy - .5, "outline")
            cv.put(ex - gr + 1.6, ey - gr + 1.6, "white")
    for x in range(int(round(fcx - rx * gk + gr)), int(round(fcx + rx * gk - gr)) + 1): cv.put(x, ey - 1, "outline")
    if elder:  # 白長眉＋鬚
        for s in (-1, 1):
            for t in range(5): cv.put(fcx + s * (rx * gk + t - 2), ey - gr - 1 + (t > 2) * (t - 2) * 0.6 * 1, "white")
        bd = cv.ell(fcx, ey + ry * 0.5, rx * 0.36, ry * 0.30) & bm; cv.a[bd] = IDX["white"]; cv.a[ring(bd) & bm & (cv.yy > ey + 2)] = IDX["peach2"]
        if FACE_MODE == "dopey": bt.draw_tmpl_c(cv, fcx + 0.5, ey + ry * 0.36, ["..#", "##."], {"#": "outline"})   # 鬚入面都係歪嘴笑
        else: cv.put(fcx, ey + ry * 0.35, "outline"); cv.put(fcx - 1, ey + ry * 0.35, "outline")
    # 揸住嘅小燈（肚前右手）
    lx, ly = cx + rx * (0.86 if FACE_MODE == "dopey" else 0.72), cy + ry * (0.62 if FACE_MODE == "dopey" else 0.45)
    glow_bulb(cv, lx + 1, ly, 1.6 if not elder else 1.9)
    if elder:  # 塵粒軌道環 halo + 吊燈
        hx_, hy_ = cx + 1, cy - ry - 3.5
        for t in np.linspace(0, 2 * math.pi, 22, endpoint=False):
            x, y = hx_ + math.cos(t) * 9, hy_ + math.sin(t) * 2.6
            if cv.a[int(round(y)), int(round(x))] == 0: cv.put(x, y, "peach1" if int(t * 3) % 2 else "glow_mid")
        glow_bulb(cv, hx_, hy_ - 1, 2.2)
        aura(cv, "peach2", "glow_mid")
    else:
        cv.put(cx - rx - 5, cy - ry * 0.6, "peach1"); cv.put(cx - rx - 4, cy - ry * 0.8, "peach2")
    return cv.a, "dust"

STAGES = [  # (id, name, size, renderer)
 ("1_egg", "光卵", 24, s1_egg), ("2_dot", "絨點", 28, s2_dot), ("3_sprout", "絨芽", 32, s3_sprout), ("4_hop", "絨跳", 38, s4_hop)]
BR = [("lumi", "螢絨", s5_lumi), ("radiant", "燦光", s5_radiant), ("soft", "柔光", s5_soft), ("dust", "微塵", s5_dust)]

def to_img(a, key):
    rgb = pal_rgb(key); o = np.zeros(a.shape + (4,), np.uint8)
    for i, c in enumerate(rgb):
        if i: o[a == i, :3] = c; o[a == i, 3] = 255
    return Image.fromarray(o, "RGBA")
EMIS = {"lumi": {"egg_shade", "cyan"}, "base": {"glow_core", "glow_mid"}, "dust": {"glow_core", "glow_mid"}}
def emissive(a, key):
    m = np.isin(a, [IDX[n] for n in EMIS[key]]); o = np.zeros(a.shape + (4,), np.uint8); o[m] = 255
    return Image.fromarray(o, "RGBA")

# ---------------------------------------------------------------- sheets
FONT = None
def font(sz):
    for p in ("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
              "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf"):
        if os.path.exists(p): return ImageFont.truetype(p, sz)
    return ImageFont.load_default()

def main():
    os.makedirs(OUT, exist_ok=True)
    items = []  # (key, label, size, img, palkey, a)
    for sid, nm, S, fn in STAGES:
        a, pk = fn(); assert a.shape == (S, S); items.append((sid, nm, S, to_img(a, pk), pk, a))
    for st, S, el in (("5", 44, False), ("6", 48, True)):
        for bid, bnm, fn in BR:
            a, pk = fn(el); assert a.shape == (S, S)
            items.append((f"{st}_{'adult' if not el else 'elder'}_{bid}", ("靜光・" if el else "守夜者・") + bnm, S, to_img(a, pk), pk, a))
    stats = {}
    for sid, nm, S, im, pk, a in items:
        im.save(os.path.join(OUT, f"evo6_{sid}_{S}.png"))
        if pk == "lumi" or sid.startswith("6"): emissive(a, pk).save(os.path.join(OUT, f"evo6_{sid}_{S}_emissive.png"))
        arr = np.asarray(im); assert set(np.unique(arr[..., 3])) <= {0, 255}
        assert {tuple(c) for c in arr[arr[..., 3] > 0][:, :3]} <= set(pal_rgb(pk)[1:]), sid
        ys, xs = np.nonzero(arr[..., 3])
        stats[sid] = dict(name=nm, canvas=S, pivot=[S // 2, S - 3], bbox_w=int(xs.max() - xs.min() + 1), bbox_h=int(ys.max() - ys.min() + 1),
                          colours=int(len(np.unique(a)) - 1), palette=pk, touches_edge=bool(xs.min() == 0 or ys.min() == 0 or xs.max() == S - 1))
    for k in ("base", "lumi", "dust"):
        json.dump({"palette": k, "count": 31, "swapped": {a: b[0] for a, b in SWAPS[k].items()}, "colors": pal_json(k)},
                  open(os.path.join(OUT, f"palette_evo6_{k}.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(stats, open(os.path.join(OUT, "_stats.json"), "w"), ensure_ascii=False, indent=1)

    # ---- lineup 6x：共用地線，每格 64 框，stage 5–6 四分支疊行
    Z = 6; CELL = 64; pad = 6; lab = 30; BG = (58, 56, 78, 255)
    cols = 6; rows = 4
    W = cols * (CELL * Z + pad) + pad; H = rows * (CELL * Z + lab + pad) + pad + 40
    sheet = Image.new("RGBA", (W, H), (24, 22, 34, 255)); dr = ImageDraw.Draw(sheet); f = font(22); fb = font(26)
    dr.text((pad, 6), "團絨 6 階段進化概念（尺寸跟 GDD lock；每格 64×64 比較框、腳底共用地線 y=61、1px=6x）", fill=(240, 236, 250), font=fb)
    def cell(col, row, im, S, text):
        x0 = pad + col * (CELL * Z + pad); y0 = 40 + pad + row * (CELL * Z + lab + pad)
        c = Image.new("RGBA", (CELL, CELL), BG); c.alpha_composite(im, (CELL // 2 - S // 2, 61 - (S - 3)))
        sheet.paste(c.resize((CELL * Z, CELL * Z), Image.NEAREST), (x0, y0))
        dr.line([x0, y0 + 62 * Z, x0 + CELL * Z, y0 + 62 * Z], fill=(120, 116, 150), width=1)
        dr.text((x0 + 4, y0 + CELL * Z + 2), text, fill=(240, 236, 250), font=f)
    for i, (sid, nm, S, im, pk, a) in enumerate(items[:4]): cell(i, 0, im, S, f"{i + 1} {nm} {S}px")
    for j in range(4):
        for k, st in enumerate((4, 8)):
            sid, nm, S, im, pk, a = items[st + j]; cell(4 + k, j, im, S, f"{5 + k} {nm} {S}px")
    sheet.save(os.path.join(OUT, "evo6_lineup_6x.png"))

    # ---- vs current（64 燦光 現行 vs 新 44 / 48）
    cur = Image.open(os.path.join(SPR, "frames", "pet_tuanrong_radiant_idle_01.png")).convert("RGBA")
    pan = [(cur, 64, "現行 燦光 64px"), (items[5][3], 44, "新 守夜者・燦光 44px"), (items[9][3], 48, "新 靜光・燦光 48px"),
           (items[2][3], 32, "絨芽 32px（參考）")]
    W2 = 4 * (CELL * Z + pad) + pad; vs = Image.new("RGBA", (W2, CELL * Z + lab + 50), (24, 22, 34, 255)); d2 = ImageDraw.Draw(vs)
    d2.text((pad, 6), "大小對比：同一地線、同一倍率（6x）", fill=(240, 236, 250), font=fb)
    for i, (im, S, t) in enumerate(pan):
        x0 = pad + i * (CELL * Z + pad); y0 = 44
        c = Image.new("RGBA", (CELL, CELL), BG); c.alpha_composite(im, (CELL // 2 - S // 2, 61 - (S - 3)))
        vs.paste(c.resize((CELL * Z, CELL * Z), Image.NEAREST), (x0, y0)); d2.text((x0 + 4, y0 + CELL * Z + 2), t, fill=(240, 236, 250), font=f)
    vs.save(os.path.join(OUT, "evo6_vs_current_6x.png"))

    # ---- scene mockup（H3 晝；附 H4 夜睇螢絨發光）
    mock = [("H3", items[2]), ("H3", items[5]), ("H3", items[8]), ("H4", items[8])]
    panels = [scene_panel(v, it) for v, it in mock]
    Z2 = 2; pw, ph = 195 * Z2, 422 * Z2
    ms = Image.new("RGB", (4 * (pw + 8) + 8, ph + 70), (24, 22, 34)); d3 = ImageDraw.Draw(ms)
    for i, ((v, it), p) in enumerate(zip(mock, panels)):
        ms.paste(p.resize((pw, ph), Image.NEAREST), (8 + i * (pw + 8), 8))
        d3.text((12 + i * (pw + 8), ph + 16), f"{v}  {it[1]} {it[2]}px", fill=(240, 236, 250), font=f)
    ms.save(os.path.join(OUT, "evo6_scene_mockup_2x.png"))
    for (v, it), p in zip(mock, panels): p.save(os.path.join(OUT, f"evo6_scene_{v}_{it[0]}.png"))
    eyes_compare(items)
    print(json.dumps(stats, ensure_ascii=False))

def eyes_compare(items):
    """舊面（第一版）vs 新呆萌面，右邊附螢絨 idle 做參考；同一地線、6x"""
    global FACE_MODE
    FACE_MODE = "orig"
    old = [fn()[0] for _, _, _, fn in STAGES[1:]] + [fn(el)[0] for el in (False, True) for _, _, fn in BR]
    FACE_MODE = "dopey"
    new = [it for it in items[1:]]
    Z = 6; CELL = 64; pad = 6; lab = 30; BG = (58, 56, 78, 255)
    n = len(new); cols = 6
    W = cols * (CELL * Z + pad) + pad; H = 4 * (CELL * Z + lab + pad) + pad + 44 + 16
    sh = Image.new("RGBA", (W, H), (24, 22, 34, 255)); dr = ImageDraw.Draw(sh); f = font(22); fb = font(24)
    dr.text((pad, 8), "面部對比（6x）：每組上＝舊版第一稿／下＝新「呆萌」版（螢絨款豆眼：細、分得開、擺低＋歪嘴笑）；右下＝螢絨 idle 參考", fill=(240, 236, 250), font=fb)
    def put(col, row, im, S, text, hl=False):
        x0 = pad + col * (CELL * Z + pad); y0 = 44 + pad + row * (CELL * Z + lab + pad) + (16 if row >= 2 else 0)
        c = Image.new("RGBA", (CELL, CELL), (66, 62, 96, 255) if hl else BG); c.alpha_composite(im, (CELL // 2 - S // 2, 61 - (S - 3)))
        sh.paste(c.resize((CELL * Z, CELL * Z), Image.NEAREST), (x0, y0))
        dr.text((x0 + 4, y0 + CELL * Z + 2), text, fill=(255, 226, 140) if hl else (200, 196, 214), font=f)
    for i, (it, oa) in enumerate(zip(new, old)):
        sid, nm, S, im, pk, a = it
        blk = i // 6; col = i % 6
        put(col, blk * 2, to_img(oa, pk), S, f"舊 {nm} {S}px")
        put(col, blk * 2 + 1, im, S, f"新 {nm} {S}px", hl=True)
    lumi = Image.open(os.path.join(SPR, "lumi", "frames", "idle_01.png")).convert("RGBA")
    put(5, 3, lumi, 64, "參考：螢絨 idle 64px（現行動畫）")
    sh.save(os.path.join(OUT, "evo6_eyes_compare_6x.png"))

def f01(im): return np.asarray(im.convert("RGBA"), float) / 255
def hx(h): return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float) / 255
def scene_panel(v, it):
    sid, nm, S, im, pk, a = it
    D = os.path.join(ROOT, "scenes", "hd2d", v); g = json.load(open(os.path.join(D, "grade.json")))
    MX, MY = 14, 12; box = (MX, MY, MX + 195, MY + 422)
    L = lambda n: f01(Image.open(os.path.join(D, n)).crop(box))
    def over(C, l): al = l[..., 3:]; return C * (1 - al) + l[..., :3] * al
    C = L("sky.png")[..., :3]
    for n in ("far.png", "mid.png"): C = over(C, L(n))
    s = f01(im); ps = s.copy(); ps[..., :3] = s[..., :3] * hx(g["petTint"]) * hx(g["ambientTint"])
    em = np.asarray(emissive(a, pk), float)[..., 3] / 255
    ps[..., :3] = ps[..., :3] * (1 - em[..., None]) + s[..., :3] * em[..., None]
    fx, fy = 97, 292; x0, y0 = fx - S // 2, fy - (S - 3)
    yy, xx = np.mgrid[0:422, 0:195]
    C = C * (1 - (np.exp(-(((xx - fx) / (S * 0.28)) ** 2 + ((yy - fy) / 2.0) ** 2)) * 0.4)[..., None])
    full = np.zeros((422, 195, 4)); full[y0:y0 + S, x0:x0 + S] = ps; C = over(C, full)
    C = over(C, L("fore.png"))
    C = C * L("lightmap.png")[..., :3] + L("light_add.png")[..., :3]
    C = C + L("emissive_blur.png")[..., :3] * g["bloom"]["intensity"]
    emf = np.zeros((422, 195)); emf[y0:y0 + S, x0:x0 + S] = em
    gl = np.asarray(Image.fromarray((emf * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.5)), float) / 255
    C = C + gl[..., None] * (hx("#cff26a") if pk == "lumi" else hx("#ffe98a")) * (1.3 if v == "H4" else 0.5)
    fog = hx(g["fog"]["color"]); d = g["fog"]["density"]; C = C * (1 - d) + fog * d
    return Image.fromarray((np.clip(C, 0, 1) * 255 + .5).astype(np.uint8), "RGB")

if __name__ == "__main__":
    main()
