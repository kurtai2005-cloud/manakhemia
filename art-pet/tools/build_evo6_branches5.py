#!/usr/bin/env python3
"""build_evo6_branches5.py — 團絨 evo6 新增 5 條支線 概念稿（stage 5 守夜者 44／stage 6 靜光 48，idle 1 幀，唔係動畫）。
v3 lumi feel：直接 import build_evo6_concept 嘅 lf_* 管線（身形、絨邊、4 級陰影、4×5 豆眼、口、腮紅、描邊），只加分支特徵＋分支色盤。
Pillow + numpy 逐像素程式繪製，無 AI。alpha 0/255、無 AA、面向右；pivot＝(w/2, h-3)。
Output -> ../sprites/tuanrong/evo6_concept/branches5/
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_evo6_concept as EC
bt = EC.bt; IDX = EC.IDX; RAMP = EC.RAMP
OUT = os.path.join(EC.OUT, "branches5"); ROOT = EC.ROOT

# ---------------------------------------------------------------- 分支色盤（同 palette_lumi 做法：共用 31 槽，只換分支唔用嘅槽）
# 換：peach0-2＋egg_dark（身 ramp 4 級）、egg_shade（分支主特徵色）、cyan（點綴／小光點）、glow／glow_mid／glow_core（分支燈色）
SW5 = {
 "tide":    {"egg_dark": ("tide0", "#3F8FA6"), "peach0": ("tide1", "#5FB0C2"), "peach1": ("tide2", "#8ED2D8"), "peach2": ("tide3", "#C6EEEA"),
             "egg_shade": ("fin", "#4C78C6"), "cyan": ("foam", "#F2FFFC"),
             "glow": ("drop_g", "#62CFEF"), "glow_mid": ("drop_gm", "#A6EEFA"), "glow_core": ("drop_gc", "#EAFFFF")},
 "shroom":  {"egg_dark": ("cocoa0", "#8A6450"), "peach0": ("cocoa1", "#A87E62"), "peach1": ("cocoa2", "#C89E7E"), "peach2": ("cocoa3", "#E6C6A4"),
             "egg_shade": ("gill", "#F4DCC4"), "cyan": ("spore", "#DDFFB4"),
             "glow": ("myco_g", "#8ED87A"), "glow_mid": ("myco_gm", "#C4F2A2"), "glow_core": ("myco_gc", "#F2FFDA")},
 "crystal": {"egg_dark": ("quartz0", "#B07A9C"), "peach0": ("quartz1", "#CF9BB8"), "peach1": ("quartz2", "#EABFD2"), "peach2": ("quartz3", "#FAE2EC"),
             "egg_shade": ("shard", "#9688DE"), "cyan": ("prism", "#C6F2FF"),
             "glow": ("prism_g", "#D8A8FF"), "glow_mid": ("prism_gm", "#F0D4FF"), "glow_core": ("prism_gc", "#FFF6FF")},
 "moon":    {"egg_dark": ("night0", "#3A4776"), "peach0": ("night1", "#50639A"), "peach1": ("night2", "#6C84BA"), "peach2": ("night3", "#97ADD8"),
             "egg_shade": ("cap_d", "#5A4E9C"), "cyan": ("star", "#FFF4A8"),
             "glow": ("moon_g", "#EFE09A"), "glow_mid": ("moon_gm", "#FFF2C4"), "glow_core": ("moon_gc", "#FFFFF0")},
 "ember":   {"egg_dark": ("brick0", "#963E37"), "peach0": ("brick1", "#BE5844"), "peach1": ("brick2", "#DA7A56"), "peach2": ("brick3", "#F0A87C"),
             "egg_shade": ("ash", "#5C3C40"), "cyan": ("hot", "#FFE070"),
             "glow": ("flame_g", "#FF6E36"), "glow_mid": ("flame_gm", "#FFB04A"), "glow_core": ("flame_gc", "#FFF0A0")},
}
EC.SWAPS.update(SW5)
for k in SW5: RAMP[k] = ["egg_dark", "peach0", "peach1", "peach2"]
EMIS5 = {"tide": {"glow_core", "glow_mid"}, "shroom": {"glow_core", "glow_mid", "cyan"}, "crystal": {"glow_core", "glow_mid", "cyan"},
         "moon": {"glow_core", "glow_mid", "cyan"}, "ember": {"glow_core", "glow_mid", "cyan"}}
EC.EMIS.update(EMIS5)

lf_canvas, lf_body, lf_hi, lf_feet, lf_arms, lf_face, lf_stem, lf_clean = EC.lf_canvas, EC.lf_body, EC.lf_hi, EC.lf_feet, EC.lf_arms, EC.lf_face, EC.lf_stem, EC.lf_clean
outl, rot_ell, ear, tail_puff, sparkle, aura, spots, ring, shade = EC.outl, EC.rot_ell, EC.ear, EC.tail_puff, EC.sparkle, EC.aura, EC.spots, EC.ring, EC.shade

def geo(elder):
    S = 48 if elder else 44; rx, ry = (13.8, 11.6) if elder else (12.9, 10.9); k = rx / 19
    cv, cx, cy, bottom = lf_canvas(S, rx, ry); return S, rx, ry, k, cv, cx, cy, bottom
def body(cv, cx, cy, bottom, rx, ry, k, key, N=15, rb=3.3):
    lf_feet(cv, cx, bottom, rx, 2.4, 1.9)
    lf_arms(cv, cx, cy, rx, ry, 2.3 * k ** .5, RAMP[key][2])
    bm, kk = lf_body(cv, cx, cy, rx, ry, key, N, rb * k, skip_top=True)
    lf_hi(cv, cx, cy, rx, ry, col="cream4"); return bm
def blob(cv, pts, r):
    m = np.zeros_like(cv.solid)
    for (x, y) in pts: m |= cv.ell(x, y, r, r)
    return m
def finish_aura(cv, c1, c2, extra=()):
    aura(cv, c1, c2); lf_clean(cv, (c1, c2) + tuple(extra))

# ---------------------------------------------------------------- 1 水珠（tide）
def drop_bulb(cv, x, by, r):
    """水珠燈：圓底＋向上尖頂（光滑），左上高光"""
    m = cv.ell(x, by, r + 0.8, r + 0.8)
    for j in range(int(r * 2.2) + 1):
        t = j / (r * 2.2); half = (r + 0.8) * (1 - t) ** 1.3
        m |= (np.abs(cv.xx + .5 - x) <= half) & (cv.yy == int(round(by - j)))
    cv.paint(m, "glow"); inner = m & ~ring(m) & ~ring(m & ~ring(m)) | (cv.ell(x, by, r - 0.3, r - 0.3)); cv.paint(inner & m, "glow_mid")
    cv.put(x - 1, by - 1, "glow_core"); cv.put(x - 1, by - 2, "glow_core"); cv.put(x, by - 1, "glow_core")
    outl(cv, m); return m
def bubble(cv, x, y, r):
    m = cv.ell(x, y, r, r); rg = ring(m) & (cv.a == 0); cv.a[rg] = IDX["fin" if False else "egg_shade"]; cv.put(x - r * 0.4, y - r * 0.4, "cyan")
def r_tide(elder=False):
    S, rx, ry, k, cv, cx, cy, bottom = geo(elder); key = "tide"
    if elder:   # 背鰭翼（兩塊大鰭，深藍＋泡沫邊）
        for j, (a, b, ang) in enumerate(((8.2, 3.0, 150), (6.8, 2.5, 176))):
            d = (math.cos(math.radians(ang)), -math.sin(math.radians(ang))); bx0, by0 = cx - rx * 0.6, cy - ry * 0.2 + j * 2.2
            w = rot_ell(cv, bx0 + d[0] * a * 0.7, by0 + d[1] * a * 0.7, a, b, ang); cv.paint(w, "egg_shade")
            cv.paint(w & ~rot_ell(cv, bx0 + d[0] * a * 0.7 + .6, by0 + d[1] * a * 0.7 + .8, a - 1.2, b - 1.0, ang), "peach2"); cv.solid |= w
    # 魚尾鰭（分叉）
    tx, ty = cx - rx - 0.6, cy + ry * 0.35
    for ang in (148, 212):
        m = rot_ell(cv, tx - 2.4, ty + (-1.6 if ang < 180 else 1.2), 4.2 if elder else 3.6, 1.7, ang); cv.paint(m, "egg_shade"); cv.solid |= m
        cv.paint(m & rot_ell(cv, tx - 2.0, ty + (-1.4 if ang < 180 else 1.0), 2.4, 0.9, ang), "peach1")
    # 鰭耳（向後撥）
    for s in (-1, 1):
        ex, ey_ = cx + s * rx * 0.6, cy - ry * 0.74
        m = rot_ell(cv, ex - 1.0, ey_ - 1.6, 4.4 if elder else 3.9, 1.9, 125 if s < 0 else 100); cv.paint(m, "egg_shade"); cv.solid |= m
        cv.paint(m & rot_ell(cv, ex - 0.6, ey_ - 1.0, 2.6, 0.9, 125 if s < 0 else 100), "peach2")
    bm = body(cv, cx, cy, bottom, rx, ry, k, key, 15, 3.2)
    tip = lf_stem(cv, cx, cy - ry, int(round(5 * k)), 2, ("egg_shade", "egg_dark"), lean=0.8)
    cv.outline()
    # 肚波紋（泡沫色 wave）
    for x in range(int(cx - rx * 0.42), int(cx + rx * 0.5)):
        y = cy + ry * 0.80 + (1 if (x // 2) % 2 else 0)
        if bm[int(y), x] and cv.a[int(y), x] != IDX["outline"]: cv.a[int(y), x] = IDX["cyan"]
    spots(cv, bm, [(-0.6, 0.1), (-0.78, 0.38), (0.66, 0.2)], "egg_dark", cx, cy, rx, ry)
    drop_bulb(cv, tip[0] + 0.5, tip[1] - 2.2, 2.4 if elder else 2.0)
    lf_face(cv, cx, cy, rx, ry, bm, "L", dx=1, br=(2.2, 1.3))
    if elder:   # 三粒小水珠繞燈＋泡泡 aura
        for (dx, dy) in ((-7, 1), (7, -1), (0, -7)):
            x, y = tip[0] + dx, tip[1] - 2.2 + dy; cv.put(x, y, "glow_mid"); cv.put(x, y - 1, "glow_core")
        finish_aura(cv, "glow", "cyan")
        for (x, y, r) in ((5, 12, 1.6), (S - 6, 18, 1.3), (6, 26, 1.0)): bubble(cv, x, y, r)
        lf_clean(cv, ("egg_shade", "cyan"))
    else:
        bubble(cv, cx + rx + 3.5, cy - ry * 0.5, 1.4); bubble(cv, cx + rx + 5.5, cy - ry * 0.95, 1.0)
    return cv.a, key

# ---------------------------------------------------------------- 2 菇傘（shroom）
def r_shroom(elder=False):
    S, rx, ry, k, cv, cx, cy, bottom = geo(elder); key = "shroom"
    tail_puff(cv, cx - rx - 0.8, cy + 2.0, 2.8, key)
    if elder:   # 腳邊兩粒發光細菇
        for (x, s) in ((cx - rx - 3.5, 1.0), (cx + rx + 3.2, 0.85)):
            st = cv.ell(x, bottom - 1.2, 0.9, 1.6); cv.paint(st, "egg_shade"); cv.solid |= st
            cp = cv.ell(x, bottom - 3.0, 2.4 * s, 1.6 * s) & (cv.yy <= bottom - 2.6); cv.paint(cp, "glow"); cv.paint(cp & (cv.yy <= bottom - 3.6), "glow_mid"); cv.solid |= cp
    bm = body(cv, cx, cy, bottom, rx, ry, k, key, 14, 3.4)
    # 背苔（左上一撮綠）
    for (dx, dy, r) in ((-0.62, -0.38, 1.9), (-0.42, -0.62, 1.6), (-0.8, -0.05, 1.5)):
        m = cv.ell(cx + dx * rx, cy + dy * ry, r, r) & bm; cv.paint(m, "leaf"); cv.put(cx + dx * rx + 0.5, cy + dy * ry + 0.5, "leaf_d")
    # 菇帽（頂住頭、闊過頭少少，紅帽白點、底一行菇褶）
    cw, ch = rx * (1.0 if elder else 0.86), (6.4 if elder else 5.4)
    capy = cy - ry * 0.52
    cap = cv.ell(cx + 0.8, capy, cw, ch) & (cv.yy <= capy + 0.6)
    if elder:  # 帽邊微微垂落
        cap |= cv.ell(cx + 0.8 - cw + 1.6, capy + 0.8, 1.8, 1.6) | cv.ell(cx + 0.8 + cw - 1.6, capy + 0.8, 1.8, 1.6)
    cv.paint(cap, "berry"); cv.paint(cap & (cv.yy >= capy - 0.6), "berry_d"); cv.solid |= cap
    gill = (cv.yy == int(capy + 1)) & (np.abs(cv.xx + .5 - cx - 0.8) <= cw - 1.6) & ~cap
    cv.a[gill] = IDX["egg_shade"]; cv.solid |= gill
    if elder:   # 發光菇褶點
        for x in range(int(cx - cw + 3), int(cx + cw - 1), 3): cv.put(x, capy + 1, "glow_mid")
    for (dx, dy, r) in ((-0.5, -0.45, 1.3), (0.15, -0.72, 1.2), (0.55, -0.3, 1.0), (-0.12, -0.15, 0.8)):
        cv.a[cv.ell(cx + 0.8 + dx * cw, capy + dy * ch, r, r) & cap & (cv.yy < capy - 0.6)] = IDX["cream4"]
    # 頂上發光細菇燈（短柄）
    top = capy - ch + 0.6
    tip = lf_stem(cv, cx + 1.6, top, 2, 1, ("egg_shade", "egg_shade"), 0.4)
    cv.outline()
    bx_, by_ = tip[0], tip[1] - 1.4; r = 2.6 if elder else 2.2
    mc = cv.ell(bx_, by_, r + 0.7, r * 0.8 + 0.4) & (cv.yy <= by_ + 0.6); cv.paint(mc, "glow"); cv.paint(mc & cv.ell(bx_ - .4, by_ - .4, r - 0.2, r * 0.6), "glow_mid")
    cv.put(bx_ - 1, by_ - 1, "glow_core"); cv.put(bx_ + 1, by_ - 0.5, "cyan"); outl(cv, mc)
    lf_face(cv, cx, cy + 0.6, rx, ry, bm, "L", dx=1, br=(2.2, 1.3))
    if elder:
        finish_aura(cv, "cyan", "glow_mid")
        for (x, y) in ((4, 14), (S - 5, 9), (S - 7, 24)): cv.put(x, y, "cyan"); cv.put(x + 1, y - 1, "glow_mid")
        lf_clean(cv, ("cyan", "glow_mid"))
    else:
        for (x, y) in ((cx + rx + 3, cy - ry * 0.9), (cx + rx + 5, cy - ry * 0.4)): cv.put(x, y, "cyan")
    return cv.a, key

# ---------------------------------------------------------------- 3 晶角（crystal）
def diamond(cv, x, y, a, b):
    m = (np.abs(cv.xx + .5 - x) / a + np.abs(cv.yy + .5 - y) / b) <= 1.0
    cv.paint(m, "glow"); cv.paint(m & (cv.yy + .5 < y) & (cv.xx + .5 < x + 0.6), "glow_mid")
    cv.paint(m & (np.abs(cv.xx + .5 - x) < 0.6), "glow_core"); outl(cv, m); return m
def shard(cv, bx, by, h, w, lean, light="cyan"):
    m = ear(cv, bx, by, h, w, lean, ("egg_shade", "egg_shade"))
    half = m & (cv.xx + .5 < bx + lean * (by - cv.yy - .5) / max(h, 1))
    cv.paint(half, light); return m
def r_crystal(elder=False):
    S, rx, ry, k, cv, cx, cy, bottom = geo(elder); key = "crystal"
    if elder:   # 背後晶冠（5 支晶柱放射）
        hx_, hy_ = cx, cy - ry * 0.25
        for ang in (155, 128, 102, 76, 50):
            ar = math.radians(ang); L = 17.5 if ang in (102,) else 15.5
            bx, by = hx_ + math.cos(ar) * (L - 5.0), hy_ - math.sin(ar) * (L - 5.0)
            m = rot_ell(cv, bx, by, 5.0, 2.1, ang); cv.paint(m, "egg_shade"); cv.paint(m & rot_ell(cv, bx - .6, by - .6, 3.4, 1.0, ang), "glow_mid"); cv.solid |= m
    tail_puff(cv, cx - rx - 1.0, cy + 1.5, 3.0, key, tip="egg_shade")
    for s in (-1, 1): shard(cv, cx + s * rx * 0.56, cy - ry * 0.62, 8.6 if elder else 7.8, 6.0, s * 1.6)
    bm = body(cv, cx, cy, bottom, rx, ry, k, key, 16, 3.2)
    # 背脊細晶（左上 3 粒）
    for (dx, dy, h) in ((-0.86, -0.12, 4.6), (-0.7, -0.5, 5.2)):
        shard(cv, cx + dx * rx, cy + dy * ry + 1.0, h, 3.8, -2.4, "glow_mid")
    tip = lf_stem(cv, cx, cy - ry, int(round(4 * k)), 1, ("egg_shade", "egg_shade"))
    cv.outline()
    # 晶粉閃點（面頰／身）
    for (a, b, c) in ((-0.55, 0.05, "cyan"), (0.7, 0.42, "glow_core"), (-0.25, 0.6, "cyan"), (0.4, -0.55, "glow_core")):
        x, y = int(round(cx + a * rx)), int(round(cy + b * ry))
        if bm[y, x] and cv.a[y, x] != IDX["outline"]: cv.a[y, x] = IDX[c]
    diamond(cv, tip[0] + 0.5, tip[1] - 3.2, 2.7 if elder else 2.3, 3.8 if elder else 3.3)
    lf_face(cv, cx, cy, rx, ry, bm, "L", dx=1, br=(2.2, 1.3))
    if elder:
        for (x, y) in ((4, 20), (S - 5, 26)):
            for (dx, dy, c) in ((0, 0, "glow_core"), (0, -1, "glow_mid"), (0, 1, "glow_mid"), (-1, 0, "glow"), (1, 0, "glow"), (0, -2, "cyan")): cv.put(x + dx, y + dy, c)
        finish_aura(cv, "glow", "cyan")
        sparkle(cv, S - 7, 6, "glow_core", "cyan")
    else:
        sparkle(cv, int(cx + rx + 4), int(cy - ry * 0.7), "glow_core", "cyan")
    return cv.a, key

# ---------------------------------------------------------------- 4 月眠（moon）
def crescent(cv, x, y, r, off=(1.3, -0.6)):
    m = cv.ell(x, y, r, r) & ~cv.ell(x + off[0] * r / 2.2, y + off[1] * r / 2.2, r * 0.82, r * 0.82)
    cv.paint(m, "glow"); cv.paint(m & cv.ell(x - 0.5, y - 0.3, r - 0.9, r - 0.9), "glow_mid"); cv.put(x - r * 0.55, y, "glow_core")
    outl(cv, m); return m
def r_moon(elder=False):
    S, rx, ry, k, cv, cx, cy, bottom = geo(elder); key = "moon"
    if elder:   # 背後大月牙＋左下雲枕
        mx, my, R = cx - 2, cy - ry * 0.55, 15.8
        mm = cv.ell(mx, my, R, R) & ~cv.ell(mx + 4.2, my - 3.0, R * 0.9, R * 0.9) & (cv.yy < cy + 2)
        cv.paint(mm, "glow"); cv.paint(mm & cv.ell(mx - 1, my, R - 1.6, R - 1.6), "glow_mid"); cv.solid |= mm
        cl = blob(cv, [(cx - rx - 2.5, bottom - 2.4), (cx - rx + 0.5, bottom - 3.6), (cx - rx - 5.2, bottom - 1.8)], 2.4) & (cv.yy <= bottom)
        cv.paint(cl, "white"); cv.paint(cl & (cv.yy >= bottom - 1.6), "peach2"); cv.solid |= cl
    tail_puff(cv, cx - rx - 1.0, cy + 1.8, 3.0, key, tip="cyan")
    bm = body(cv, cx, cy, bottom, rx, ry, k, key, 15, 3.3)
    # 睡帽：由頭頂向後斜企、帽尖微垂，間條；帽尖吊住月牙燈
    P = []; n = 22; L = 1.0 if not elder else 1.12
    for i in range(n + 1):
        t = i / n
        x = cx + 2.5 - (11.5 * L) * t ** 1.3; y = cy - ry + 1.2 - (12.0 * L) * math.sin(t * 2.1)
        r = 5.6 * (1 - t) ** 1.2 + 0.8; P.append((x, y, r))
    cap = np.zeros_like(cv.solid)
    for (x, y, r) in P: cap |= cv.ell(x, y, r, r)
    cap &= ~(bm & (cv.yy > cy - ry + 2.2))
    cv.paint(cap, "zzz")
    for i, (x, y, r) in enumerate(P):
        if i % 6 == 3: cv.a[cap & cv.ell(x, y, r + 0.3, r + 0.3) & ~cv.ell(P[i - 1][0], P[i - 1][1], P[i - 1][2] + 0.2, P[i - 1][2] + 0.2)] = IDX["egg_shade"]
    brim = cap & (cv.yy >= int(cy - ry + 0.8)) & (cv.yy <= int(cy - ry + 2.2))
    cv.paint(brim, "cream4"); cv.solid |= cap
    cv.outline()
    spots(cv, bm, [(-0.6, 0.18), (0.62, 0.45), (-0.3, 0.6)], "cyan", cx, cy, rx, ry)   # 星點雀斑
    ex, ey_, _ = P[-1]
    for j in range(2): cv.put(ex - 1 - j, ey_ + 1.5 + j, "outline")
    crescent(cv, ex - 3.4, ey_ + 5.0, 2.8 if elder else 2.5, off=(-1.3, -0.6))
    fcx, ey = lf_face(cv, cx, cy, rx, ry, bm, "L", dx=1, br=(2.2, 1.3))
    # 半瞇眼：眼頂兩行蓋返身色＋一條眼皮線（企住都瞓著）
    eoff = rx * 0.40
    for s in (-1, 1):
        x0 = int(round(fcx + s * eoff - 2)); y0 = int(round(ey - 2.5))
        for xx in range(x0, x0 + 4):
            for yy in (y0, y0 + 1):
                if cv.a[yy, xx] in (IDX["outline"], IDX["cream4"], IDX["cyan"]): cv.a[yy, xx] = IDX["peach1"]
            cv.a[y0 + 2, xx] = IDX["outline"]
    if elder:
        finish_aura(cv, "cyan", "glow_mid")
        for (x, y) in ((S - 6, 30), (4, 8)): sparkle(cv, x, y, "cyan", "glow_mid")
        lf_clean(cv, ("cyan", "glow_mid"))
    else:
        for (x, y) in ((cx + rx + 4, cy - 1), (cx - rx - 3, cy - ry - 1)): sparkle(cv, int(x), int(y), "cyan", "glow_mid")
    return cv.a, key

# ---------------------------------------------------------------- 5 火苗（ember）
def flame(cv, x, by, r, h, lean=1.2):
    """火苗：圓底＋向上收窄、尖端向後勾（lean）；外 glow、中 glow_mid、底 core"""
    m = cv.ell(x, by, r + 0.6, r + 0.6)
    for j in range(int(h) + 1):
        t = j / h; half = (r + 0.6) * (1 - t) ** 0.9; ox = lean * t * t + 0.6 * math.sin(t * 5)
        m |= (np.abs(cv.xx + .5 - (x + ox)) <= half) & (cv.yy == int(round(by - j)))
    cv.paint(m, "glow")
    mid = m & ~EC.dil(ring(m))
    cv.paint(mid, "glow_mid"); cv.paint(mid & cv.ell(x, by, r * 0.6, r * 0.6), "glow_core"); outl(cv, m); return m
def r_ember(elder=False):
    S, rx, ry, k, cv, cx, cy, bottom = geo(elder); key = "ember"
    if elder:   # 背後火翼（兩撮向後飄嘅火）
        for j, (a, b, ang) in enumerate(((7.8, 2.6, 156), (6.2, 2.2, 132))):
            d = (math.cos(math.radians(ang)), -math.sin(math.radians(ang))); bx0, by0 = cx - rx * 0.62, cy - ry * 0.2 - j * 1.5
            w = rot_ell(cv, bx0 + d[0] * a * 0.7, by0 + d[1] * a * 0.7, a, b, ang); cv.paint(w, "glow")
            cv.paint(w & rot_ell(cv, bx0 + d[0] * a * 0.6, by0 + d[1] * a * 0.6, a - 2.0, b - 1.1, ang), "glow_mid"); cv.solid |= w
    # 火尾：尾毛球＋尾尖火
    tm = tail_puff(cv, cx - rx - 1.0, cy + 1.6, 3.0, key)
    for s in (-1, 1): ear(cv, cx + s * rx * 0.58, cy - ry * 0.68, 7.2 if elder else 6.6, 5.0, s * 1.6, ("peach0", "glow"))
    bm = body(cv, cx, cy, bottom, rx, ry, k, key, 16, 3.3)
    tip = lf_stem(cv, cx, cy - ry, int(round(4 * k)), 2, ("egg_shade", "egg_shade"))
    cv.outline()
    flame(cv, cx - rx - 2.6, cy - 1.6, 1.6, 4.5, lean=-1.6)   # 尾尖火（向後）
    # 煤灰點＋熱火星雀斑
    spots(cv, bm, [(-0.62, 0.15), (0.66, 0.4), (-0.3, 0.62)], "egg_shade", cx, cy, rx, ry)
    spots(cv, bm, [(-0.75, 0.38), (0.78, 0.08)], "cyan", cx, cy, rx, ry)
    flame(cv, tip[0] + 0.5, tip[1] - 2.0, 2.3 if elder else 2.0, 6.5 if elder else 5.5)
    lf_face(cv, cx, cy, rx, ry, bm, "L", dx=1, br=(2.2, 1.3))
    if elder:   # 火冠（頭頂兩旁細火）＋火星 aura
        for dx in (-5.5, 5.5): flame(cv, cx + dx + 0.5, cy - ry + 1.0, 1.1, 3.2, lean=0.6 * np.sign(dx))
        finish_aura(cv, "cyan", "glow_mid")
        for (x, y) in ((S - 6, 10), (5, 20)): cv.put(x, y, "cyan"); cv.put(x, y - 1, "glow_mid")
        lf_clean(cv, ("cyan", "glow_mid"))
    else:
        for (x, y) in ((cx + rx + 3, cy - ry * 0.95), (cx + rx + 5, cy - ry * 0.55)): cv.put(x, y, "cyan")
    return cv.a, key

BR5 = [  # (id, 名, 特質一句, 特徵, renderer)
 ("tide", "水珠", "自稱游水冠軍，其實靠頭頂水珠燈浮住", "水珠燈・鰭耳・分叉魚尾・肚波紋・泡泡", r_tide),
 ("shroom", "菇傘", "戴住菇帽自稱森林博士，見菇就話食得", "紅白菇帽・發光細菇燈・背苔・孢子", r_shroom),
 ("crystal", "晶角", "覺得自己閃到冇朋友，成日照鏡（其實係晶粉）", "晶角耳・菱形晶燈・背脊細晶・晶粉閃點", r_crystal),
 ("moon", "月眠", "話自己係夜貓守夜專家，企住都瞓著", "尖睡帽吊月牙燈・半瞇眼・星點雀斑", r_moon),
 ("ember", "火苗", "以為自己好熱血好勁，一熱就喊熱", "火苗燈・火尖耳・尾尖火・火星雀斑", r_ember),
]
OLD4 = [("lumi", "螢絨", "螢火翼・雙觸角燈・分節尾燈"), ("radiant", "燦光", "太陽放射燈・金尖耳・光尾"), ("soft", "柔光", "垂葉耳・奶油圓斑・葉尾"), ("dust", "微塵", "推高眼鏡・手揸小燈・塵雲尾")]

# ---------------------------------------------------------------- outputs
def wrap(t, n):
    return [t[i:i + n] for i in range(0, len(t), n)]
def scene_multi(v, its, xs):
    D = os.path.join(ROOT, "scenes", "hd2d", v); g = json.load(open(os.path.join(D, "grade.json")))
    MX, MY = 14, 12; box = (MX, MY, MX + 195, MY + 422); f01, hx = EC.f01, EC.hx
    Lf = lambda n: f01(Image.open(os.path.join(D, n)).crop(box))
    def over(C, l): al = l[..., 3:]; return C * (1 - al) + l[..., :3] * al
    C = Lf("sky.png")[..., :3]
    for n in ("far.png", "mid.png"): C = over(C, Lf(n))
    yy, xx = np.mgrid[0:422, 0:195]; emf = np.zeros((422, 195)); glc = np.zeros((422, 195, 3)); fy = 292
    for (sid, nm, S, im, pk, a), fx in zip(its, xs):
        s_ = f01(im); ps = s_.copy(); ps[..., :3] = s_[..., :3] * hx(g["petTint"]) * hx(g["ambientTint"])
        em = np.asarray(EC.emissive(a, pk), float)[..., 3] / 255
        ps[..., :3] = ps[..., :3] * (1 - em[..., None]) + s_[..., :3] * em[..., None]
        x0, y0 = fx - S // 2, fy - (S - 3)
        C = C * (1 - (np.exp(-(((xx - fx) / (S * 0.28)) ** 2 + ((yy - fy) / 2.0) ** 2)) * 0.4)[..., None])
        full = np.zeros((422, 195, 4)); full[y0:y0 + S, x0:x0 + S] = ps; C = over(C, full)
        e1 = np.zeros((422, 195)); e1[y0:y0 + S, x0:x0 + S] = em; emf += e1
        gcol = np.array(EC.pal_rgb(pk)[IDX["glow_mid"]], float) / 255
        glc += e1[..., None] * gcol
    C = over(C, Lf("fore.png"))
    C = C * Lf("lightmap.png")[..., :3] + Lf("light_add.png")[..., :3]
    C = C + Lf("emissive_blur.png")[..., :3] * g["bloom"]["intensity"]
    bl = np.stack([np.asarray(Image.fromarray((np.clip(glc[..., i], 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.5)), float) / 255 for i in range(3)], -1)
    C = C + bl * 0.5
    fog = hx(g["fog"]["color"]); d = g["fog"]["density"]; C = C * (1 - d) + fog * d
    return Image.fromarray((np.clip(C, 0, 1) * 255 + .5).astype(np.uint8), "RGB")

def main():
    os.makedirs(OUT, exist_ok=True)
    items = {}; stats = {}
    for bid, nm, trait, feat, fn in BR5:
        for st, S, el in (("5", 44, False), ("6", 48, True)):
            a, pk = fn(el); assert a.shape == (S, S)
            sid = f"evo6_{st}_{'guard' if not el else 'still'}_{bid}_{S}"
            im = EC.to_img(a, pk); im.save(os.path.join(OUT, sid + ".png")); EC.emissive(a, pk).save(os.path.join(OUT, sid + "_emissive.png"))
            arr = np.asarray(im); assert set(np.unique(arr[..., 3])) <= {0, 255}
            assert {tuple(c) for c in arr[arr[..., 3] > 0][:, :3]} <= set(EC.pal_rgb(pk)[1:]), sid
            ys, xs = np.nonzero(arr[..., 3])
            touch = bool(xs.min() == 0 or ys.min() == 0 or xs.max() == S - 1 or ys.max() == S - 1)
            stats[sid] = dict(branch=bid, name=("靜光・" if el else "守夜者・") + nm, canvas=S, pivot=[S // 2, S - 3], bbox=[int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
                              colours=int(len(np.unique(a)) - 1), palette=f"palette_evo6_{pk}.json", emissivePx=int((np.asarray(EC.emissive(a, pk))[..., 3] > 0).sum()), touches_edge=touch,
                              below_ground=int((arr[S - 2:, :, 3] > 0).sum()))
            items[(bid, el)] = (sid, nm, S, im, pk, a)
    for k in SW5:
        json.dump({"palette": k, "count": 31, "swapped": {a: b[0] for a, b in SW5[k].items()}, "emissive": sorted(EMIS5[k]), "colors": EC.pal_json(k)},
                  open(os.path.join(OUT, f"palette_evo6_{k}.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(stats, open(os.path.join(OUT, "_stats.json"), "w"), ensure_ascii=False, indent=1)

    # ---- lineup 6x：舊 4 ＋ 新 5，上行守夜者 44、下行靜光 48；共用地線
    Z = 6; CELL = 64; pad = 8; lab = 92; BG = (58, 56, 78, 255); NEW_BG = (70, 66, 100, 255)
    cols = 9; W = cols * (CELL * Z + pad) + pad; H = 64 + 2 * (CELL * Z + lab + pad) + pad
    sheet = Image.new("RGBA", (W, H), (24, 22, 34, 255)); dr = ImageDraw.Draw(sheet); f = EC.font(22); fs = EC.font(19); fb = EC.font(28)
    dr.text((pad, 10), "團絨 evo6 支線 lineup（6x，每格 64 框、腳底共用地線）：左 4＝現有分支，右 5＝新支線（v3 lumi feel）。上行＝守夜者 44px，下行＝靜光 48px", fill=(240, 236, 250), font=fb)
    def cell(col, row, im, S, title, sub, new):
        x0 = pad + col * (CELL * Z + pad); y0 = 64 + row * (CELL * Z + lab + pad)
        c = Image.new("RGBA", (CELL, CELL), NEW_BG if new else BG); c.alpha_composite(im, (CELL // 2 - S // 2, 61 - (S - 3)))
        sheet.paste(c.resize((CELL * Z, CELL * Z), Image.NEAREST), (x0, y0))
        dr.line([x0, y0 + 62 * Z, x0 + CELL * Z, y0 + 62 * Z], fill=(120, 116, 150), width=1)
        dr.text((x0 + 4, y0 + CELL * Z + 4), title, fill=(255, 226, 140) if new else (240, 236, 250), font=f)
        for i, ln in enumerate(wrap(sub, 19)[:3]): dr.text((x0 + 4, y0 + CELL * Z + 32 + i * 21), ln, fill=(205, 200, 222), font=fs)
    for i, (bid, nm, feat) in enumerate(OLD4):
        for row, (st, S, pre) in enumerate((("5_adult", 44, "守夜者・"), ("6_elder", 48, "靜光・"))):
            im = Image.open(os.path.join(EC.OUT, f"evo6_{st}_{bid}_{S}.png")).convert("RGBA")
            cell(i, row, im, S, f"{pre}{nm} {S}px", feat if row == 0 else "（現有分支）", False)
    for j, (bid, nm, trait, feat, fn) in enumerate(BR5):
        for row, el in enumerate((False, True)):
            sid, _, S, im, pk, a = items[(bid, el)]
            cell(4 + j, row, im, S, f"新 {'靜光' if el else '守夜者'}・{nm} {S}px", trait if row == 0 else feat, True)
    sheet.convert("RGB").save(os.path.join(OUT, "evo6_branches5_lineup_6x.png"))

    # ---- H1 scene mockup：3 隻同場（守夜者・水珠、靜光・月眠、守夜者・火苗）＋單隻 2 張
    trio = [items[("tide", False)], items[("moon", True)], items[("ember", False)]]
    p = scene_multi("H1", trio, [44, 98, 152])
    p.save(os.path.join(OUT, "evo6_branches5_scene_H1.png"))
    Z2 = 3; big = p.resize((195 * Z2, 422 * Z2), Image.NEAREST)
    duo = [scene_multi("H1", [items[("shroom", True)]], [97]), scene_multi("H1", [items[("crystal", True)]], [97])]
    ms = Image.new("RGB", (195 * Z2 + 2 * (195 * 2) + 40, 422 * Z2 + 60), (24, 22, 34)); d3 = ImageDraw.Draw(ms)
    ms.paste(big, (10, 10)); d3.text((14, 422 * Z2 + 18), "H1 晨光：守夜者・水珠｜靜光・月眠｜守夜者・火苗（3x）", fill=(240, 236, 250), font=f)
    for i, q in enumerate(duo):
        x0 = 195 * Z2 + 20 + i * (195 * 2 + 10); ms.paste(q.resize((195 * 2, 422 * 2), Image.NEAREST), (x0, 10))
        d3.text((x0 + 4, 422 * 2 + 18), ["靜光・菇傘（2x）", "靜光・晶角（2x）"][i], fill=(240, 236, 250), font=f)
    ms.save(os.path.join(OUT, "evo6_branches5_scene_mockup.png"))
    print(json.dumps({k: (v["bbox"], v["touches_edge"], v["below_ground"], v["emissivePx"]) for k, v in stats.items()}, ensure_ascii=False))

if __name__ == "__main__":
    main()
