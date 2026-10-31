#!/usr/bin/env python3
"""build_tuanrong.py — 團絨 (Tuanrong) procedural pixel sprite builder.
Pillow + numpy only. No AI art. Re-runnable:  python3 build_tuanrong.py
Output -> ../sprites/tuanrong/
"""
import json, math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "sprites", "tuanrong"))
FR = os.path.join(OUT, "frames")

# ---------------------------------------------------------------- palette
PAL = {  # name: hex   (index 0 = transparent)
 "outline":"#3B2A3E",
 "cream0":"#D69A66","cream1":"#E9BE84","cream2":"#F6DDB0","cream3":"#FFEFC4","cream4":"#FFF8E0",
 "peach0":"#E8A074","peach1":"#F5BF93","peach2":"#FBD8B4",
 "orange":"#F2A65A","orange_d":"#E07F45","orange_dd":"#B8643F",
 "glow_core":"#FFFBD0","glow_mid":"#FFE98A","glow":"#FFD45E","glow_warm":"#FF8A3D",
 "egg_shade":"#F2B93C","egg_dark":"#D98F2E",
 "blush":"#F28B9B","blush_d":"#D9667A",
 "berry":"#E5584D","berry_d":"#A33F4A","leaf":"#6BBF6A","leaf_d":"#3A7D4E",
 "zzz":"#8F85C2","white":"#F3EEFA","cyan":"#7FF0E0","drop":"#7FC4E8","drop_d":"#4FA3D9",
 "sick0":"#A3B08C","sick1":"#C9D6B0",
}
NAMES = list(PAL.keys())
IDX = {n: i + 1 for i, n in enumerate(NAMES)}
RGB = [(0, 0, 0)] + [tuple(int(PAL[n][i:i + 2], 16) for i in (1, 3, 5)) for n in NAMES]
assert len(NAMES) <= 32

# ramps dark -> light
RAMPS = {
 "cream_hi": ["cream1", "cream2", "cream3", "cream4"],       # radiant (brighter)
 "cream":    ["cream0", "cream1", "cream2", "cream3"],       # sprout
 "peach":    ["peach0", "peach1", "peach2", "cream3"],       # soft
 "sick":     ["sick0", "sick1", "cream2", "cream2"],
 "egg":      ["egg_dark", "egg_shade", "glow", "glow_mid"],
 "egg_glow": ["egg_shade", "glow", "glow_mid", "glow_core"],
}

# ---------------------------------------------------------------- helpers
class Cv:
    def __init__(s, n):
        s.n = n
        s.a = np.zeros((n, n), np.uint8)
        s.yy, s.xx = np.mgrid[0:n, 0:n]
        s.solid = np.zeros((n, n), bool)
    def ell(s, cx, cy, rx, ry):
        return (((s.xx + .5 - cx) / rx) ** 2 + ((s.yy + .5 - cy) / ry) ** 2) <= 1.0
    def put(s, x, y, c):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < s.n and 0 <= y < s.n:
            s.a[y, x] = IDX[c] if isinstance(c, str) else c
    def paint(s, mask, c):
        s.a[mask] = IDX[c]
    def tmpl(s, x, y, rows, cmap):
        for j, r in enumerate(rows):
            for i, ch in enumerate(r):
                if ch in cmap:
                    s.put(x + i, y + j, cmap[ch])
    def outline(s, color="outline"):
        m = s.solid
        d = np.zeros_like(m)
        d[1:, :] |= m[:-1, :]; d[:-1, :] |= m[1:, :]
        d[:, 1:] |= m[:, :-1]; d[:, :-1] |= m[:, 1:]
        ring = d & ~m
        s.a[ring] = IDX[color]

def ramp_color(ramp, s, th):
    k = 0
    for t in th:
        if s > t: k += 1
    return RAMPS[ramp][min(k, len(RAMPS[ramp]) - 1)]

# eye / mouth templates  ('#' dark, 'w' highlight, 'r' mouth inside, 'b' blush)
EYE = {
 False: {  # small (32px)
  "open": ["##", "w#", "##"], "blink": ["##"], "happy": [".#.", "#.#"], "sleep": ["#.#", ".#."],
  "sickL": ["#.", ".#", "#."], "sickR": [".#", "#.", ".#"],
 },
 True: {   # big (64px)
  "open": [".##.", "#w##", "####", "####", ".##."], "blink": ["####"], "happy": ["..#..", ".#.#.", "#...#"],
  "sleep": ["#...#", ".###."],
  "sickL": ["#..", ".#.", "..#", ".#.", "#.."], "sickR": ["..#", ".#.", "#..", ".#.", "..#"],
 },
}
MOUTH = {
 False: {"smile": ["#.#", ".#."], "open": ["###", "#r#", ".#."], "flat": ["###"], "frown": [".#.", "#.#"], "o": ["##", "##"], "none": []},
 True:  {"smile": ["#...#", ".###."], "open": [".###.", "#rrr#", "#rrr#", ".###."], "flat": ["#####"],
         "frown": [".###.", "#...#"], "o": [".##.", "#rr#", ".##."], "none": []},
}
CM = {"#": "outline", "w": "cream4", "r": "blush_d"}

def draw_tmpl_c(cv, cx, cy, rows, cm=CM):
    if not rows: return
    h = len(rows); w = len(rows[0])
    cv.tmpl(int(round(cx - w / 2)), int(round(cy - h / 2)), rows, cm)

HEART_S = ["#.#", "###", ".#."]
HEART_B = [".#.#.", "#####", ".###.", "..#.."]
STAR_S = [".#.", "###", ".#."]
STAR_B = ["..#..", "..#..", "#####", "..#..", "..#.."]
Z_S = ["###", ".#.", "###"]
Z_B = ["#####", "...#.", "..#..", ".#...", "#####"]
DROP_S = [".#.", "###", "###", ".#."]
DROP_B = ["..#..", ".###.", "#####", "#####", ".###."]

# ---------------------------------------------------------------- pet renderer
FORMS = {
 # S, rx, ry, G(ground), ramp, bumps N, rb, big
 "sprout":  dict(S=32, rx=10.6, ry=9.2, G=30, ramp="cream", N=10, rb=1.7, big=False, stem=3),
 "radiant": dict(S=64, rx=19.0, ry=16.0, G=61, ramp="cream_hi", N=16, rb=3.4, big=True, stem=7),
 "soft":    dict(S=64, rx=21.0, ry=18.0, G=61, ramp="peach", N=12, rb=3.6, big=True, stem=5),
}
TH = [-0.28, 0.12, 0.45]

def render_pet(form, p):
    f = FORMS[form]; S = f["S"]; big = f["big"]
    cv = Cv(S)
    sick = p.get("sick", False)
    ramp = "sick" if sick else f["ramp"]
    sx, sy = p.get("sx", 1.0), p.get("sy", 1.0)
    rx, ry = f["rx"] * sx, f["ry"] * sy
    lift = p.get("lift", 0.0)
    cx = S / 2 + p.get("dx", 0.0)
    bottom = f["G"] - 1.0 - lift
    cy = bottom - ry
    k = 2 if big else 1  # scale unit

    # --- behind: glow around bud handled later. feet
    fx = rx * 0.45
    foot_ry = 1.0 * (1.5 if big else 1)
    foot_rx = 2.6 if big else 2.0
    foot_squash = p.get("feet_in", 0.0)
    flift = p.get("flift", (0, 0))   # optional per-foot lift (px): (left, right); default 0 = unchanged output
    for sgn in (-1, 1):
        m = cv.ell(cx + sgn * fx * (1 - foot_squash), bottom + foot_ry * 0.1 + 0.2 - flift[0 if sgn < 0 else 1], foot_rx, foot_ry + 0.5)
        cv.paint(m, "orange"); cv.solid |= m
        low = m & (cv.yy >= int(bottom + foot_ry * 0.4))
        cv.paint(low, "orange_d")
    # --- arms
    arms = p.get("arms", "down")
    ar = 2.3 if big else 1.6
    if arms != "none":
        for sgn in (-1, 1):
            if arms == "down":
                ax, ay = cx + sgn * (rx - 0.2), cy + ry * 0.2
            elif arms == "up":
                ax, ay = cx + sgn * (rx - 0.4), cy - ry * 0.35 - 1
            else:  # eat: right arm forward-in
                ax, ay = (cx + sgn * (rx - 0.6), cy + ry * (0.1 if sgn < 0 else 0.0))
            m = cv.ell(ax, ay, ar, ar)
            cv.paint(m, ramp_color(ramp, 0.2, TH)); cv.solid |= m
    # --- stem + sprout solid parts
    sway = p.get("sway", 0)
    top = cy - ry
    stem_len = f["stem"] + p.get("stem_d", 0)
    droop = p.get("droop", 0)
    bud_x = cx + sway
    stem_h = max(2, stem_len)
    # --- body with fluff bumps
    bm = cv.ell(cx, cy, rx, ry)
    N, rb = f["N"], f["rb"]
    ph = p.get("fluff", 0.0)
    for i in range(N):
        th = 2 * math.pi * (i + 0.5) / N
        sn = math.sin(th)
        if sn > 0.78: continue
        if form == "radiant" and sn < -0.8 and abs(math.cos(th)) < 0.35: continue
        wob = 0.3 * math.sin(ph * 2 + (min(i, N - 1 - i)) * 1.3)
        r_b = rb * (1 + 0.08 * math.cos(2 * th))
        bm |= cv.ell(cx + (rx - r_b * 0.45 + wob) * math.cos(th), cy + (ry - r_b * 0.45 + wob) * sn, r_b, r_b)
    # shade
    nx = (cv.xx + .5 - cx) / rx; ny = (cv.yy + .5 - cy) / ry
    r2 = np.clip(nx * nx + ny * ny, 0, 1.4)
    sv = -(0.55 * nx + 0.8 * ny) - 0.38 * r2 + 0.15
    levels = len(RAMPS[ramp])
    col = np.zeros((S, S), np.uint8)
    for lv in range(levels):
        pass
    kk = np.zeros((S, S), int)
    for t in TH: kk += (sv > t)
    kk = np.clip(kk, 0, levels - 1)
    rcols = np.array([IDX[c] for c in RAMPS[ramp]], np.uint8)
    cv.a[bm] = rcols[kk][bm]
    cv.solid |= bm
    bodymask = bm
    # belly patch
    bl = cv.ell(cx, cy + ry * 0.32, rx * 0.55, ry * 0.5) & bm
    cv.a[bl & (kk <= levels - 3)] = rcols[min(levels - 2, 2)] if not sick else rcols[2]
    # fur ticks (dark strokes)
    ticks = [(-0.62, 0.15), (-0.35, 0.62), (0.52, 0.45), (0.68, -0.05), (0.15, 0.78), (-0.72, 0.5)]
    for (tx, ty) in ticks[: (6 if big else 3)]:
        px, py = cx + tx * rx * 0.95, cy + ty * ry * 0.95
        c0 = RAMPS[ramp][0 if not big or ramp != "cream_hi" else 0]
        cv.put(px, py, c0); cv.put(px + 1, py + 1, c0)
        if big: cv.put(px - 1, py - 1, c0)
    # highlight
    hx, hy = cx - rx * 0.45, cy - ry * 0.52
    if not sick:
        cv.put(hx, hy, "cream4"); cv.put(hx + 1, hy, "cream4"); cv.put(hx - 1, hy + 1, "cream4")
        if big: cv.put(hx + 2, hy, "cream4"); cv.put(hx - 2, hy + 2, "cream4"); cv.put(hx, hy - 1, "cream4"); cv.put(hx + 1, hy - 1, "cream4")
    # --- stem (solid, outlined)
    sx0 = int(round(bud_x))
    stem_cols = ["orange", "orange_d"]
    stem_w = 2 if big else 1
    pts = []
    sy0 = int(round(top)) + 1
    for j in range(stem_h + 1):
        t = j / max(1, stem_h)
        xo = sway * t * (1.0) + droop * (t ** 2) * 2
        yo = sy0 - j + (droop * (t ** 2) * 1.5)
        pts.append((cx + xo, yo))
    for (px, py) in pts:
        for w in range(stem_w):
            x = int(round(px - (stem_w - 1) / 2 + w)); y = int(round(py))
            cv.put(x, y, "orange" if w == 0 else "orange_d"); cv.solid[min(max(y, 0), S - 1), min(max(x, 0), S - 1)] = True
    tipx, tipy = pts[-1]
    # leaves (solid)
    leaves = p.get("leaves", form == "soft")
    if leaves:
        for sgn in (-1, 1):
            lx = tipx + sgn * (3.2 if big else 2.5); ly = tipy - 1.5 + (p.get("droop", 0) * 3.5)
            m = cv.ell(lx, ly, 2.4 if big else 1.8, 2.2 if big else 1.2)
            cv.paint(m, "orange" if not sick else "sick1"); cv.solid |= m
            cv.put(lx - sgn * 1, ly, "orange_d" if not sick else "sick0"); cv.put(lx - sgn * 2, ly, "orange_d" if not sick else "sick0")
    # sprout cluster for radiant: small side shoots
    # --- outline
    cv.outline()
    # --- face
    ey = cy + ry * 0.08
    eoff = rx * (0.40 if big else 0.42)
    face = p.get("eyes", "open")
    if face in ("sick",):
        draw_tmpl_c(cv, cx - eoff, ey, EYE[big]["sickL"]); draw_tmpl_c(cv, cx + eoff, ey, EYE[big]["sickR"])
    else:
        t = EYE[big][face]
        draw_tmpl_c(cv, cx - eoff, ey, t); draw_tmpl_c(cv, cx + eoff, ey, t)
    my = ey + (ry * 0.38 if big else ry * 0.38)
    mth = p.get("mouth", "smile")
    draw_tmpl_c(cv, cx, my + (0 if big else 0), MOUTH[big][mth])
    if p.get("blush", True):
        bx = rx * (0.62 if big else 0.64); by = ey + ry * 0.26
        for sgn in (-1, 1):
            mb = cv.ell(cx + sgn * bx, by, 2.4 if big else 1.5, 1.4 if big else 0.8)
            c = "blush" if not sick else "sick0"
            cv.a[mb & bodymask] = IDX[c]
    # --- glowing bud (on top of outline)
    bud = p.get("bud", 1.0)
    draw_bud(cv, form, tipx, tipy, bud, sick, p)
    for fx_ in p.get("extras", []):
        fx_(cv, cx, cy, rx, ry)
    return cv.a

def draw_bud(cv, form, tx, ty, bud, sick, p):
    big = FORMS[form]["big"]
    if sick:
        cs = ["cream2", "sick1", "sick0"]
        r = 1.5 if not big else 2.4
        m = cv.ell(tx, ty - r * 0.5, r, r)
        cv.paint(m, "sick1"); cv.put(tx, ty - r * .5, "cream2")
        # outline for visibility
        mm = m
        d = np.zeros_like(mm); d[1:, :] |= mm[:-1, :]; d[:-1, :] |= mm[1:, :]; d[:, 1:] |= mm[:, :-1]; d[:, :-1] |= mm[:, 1:]
        cv.a[d & ~mm & (cv.a == 0)] = IDX["outline"]
        return
    if form == "sprout":
        by = ty - 2.5
        x0, y0 = int(round(tx)) - 2, int(round(by)) - 2
        rows = [".ggg.", "gmmmg", "gmcmg", "gmmmg", ".ggg."] if bud >= 1.0 else [".ggg.", "gmmmg", "gmmmg", "gmmmg", ".ggg."]
        cv.tmpl(x0, y0, rows, {"g": "glow", "m": "glow_mid", "c": "glow_core"})
        if bud > 1.05:
            for dx, dy in ((-4, -2), (4, -1), (0, -4)):
                cv.put(tx + dx, by + dy, "glow_mid")
    elif form == "radiant":
        by = ty - 2
        rr = 4.4 * (0.9 + 0.1 * bud)
        # spokes: dandelion fan
        angs = [-170, -150, -130, -110, -90, -70, -50, -30, -10]
        for i, a in enumerate(angs):
            ln = 10.5 if (i % 2 == 1) else 12.5
            ln *= (0.9 + 0.1 * bud)
            if i in (0, 8): ln *= 0.75
            ar = math.radians(a)
            steps = int(ln)
            for s_ in range(int(rr), steps + 1):
                px = tx + math.cos(ar) * s_; py = by + math.sin(ar) * s_
                cv.put(px, py, "glow_mid" if s_ < steps else "glow_core")
            ex = tx + math.cos(ar) * (steps + 1); ey_ = by + math.sin(ar) * (steps + 1)
            cv.put(ex, ey_, "glow_warm"); cv.put(ex + math.cos(ar), ey_ + math.sin(ar), "glow_warm") if False else None
        halo = cv.ell(tx, by, rr + 1.4, rr + 1.4); cv.paint(halo, "glow")
        cv.paint(cv.ell(tx, by, rr, rr), "glow_mid")
        cv.paint(cv.ell(tx - .4, by - .4, rr - 1.4, rr - 1.4), "glow_core")
        # sparkles
        for (dx, dy, ph) in ((-16, -4, 0), (15, -6, 1), (-10, -11, 2), (11, -12, 3)):
            if bud >= 0.8 and (p.get("twinkle", 0) + ph) % 4 < 2:
                cv.put(tx + dx, by + dy, "glow_core")
                for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    cv.put(tx + dx + ox, by + dy + oy, "glow_mid")
    else:  # soft
        by = ty - 2.6
        r = 2.6 * (0.9 + 0.1 * bud)
        cv.paint(cv.ell(tx, by, r + 0.9, r + 0.9), "glow_mid" if False else "glow")
        cv.paint(cv.ell(tx, by, r, r), "glow_mid")
        cv.put(tx - 0.5, by - 0.5, "glow_core"); cv.put(tx + 0.5, by - 0.5, "glow_core"); cv.put(tx - 0.5, by + 0.5, "glow_core")

# ---------------------------------------------------------------- extras
def ex_berry(size, off, bite=0):
    def f(cv, cx, cy, rx, ry):
        bx = cx + rx * 0.9 + off[0]; by = cy + ry * 0.45 + off[1]
        r = size
        m = cv.ell(bx, by, r, r)
        if bite:
            m &= ~cv.ell(bx - r * 0.9, by - r * 0.3, r * (0.55 if bite == 1 else 0.85), r * (0.55 if bite == 1 else 0.85))
        d = np.zeros_like(m); d[1:, :] |= m[:-1, :]; d[:-1, :] |= m[1:, :]; d[:, 1:] |= m[:, :-1]; d[:, :-1] |= m[:, 1:]
        cv.a[d & ~m] = IDX["outline"]
        cv.paint(m, "berry")
        cv.paint(m & (cv.xx + cv.yy > bx + by + r * 0.4), "berry_d")
        cv.put(bx - r * 0.4, by - r * 0.4, "cream4")
        if bite < 2:
            cv.put(bx, by - r - 0.6, "leaf_d"); cv.put(bx + 1, by - r - 1.6, "leaf"); cv.put(bx + 2, by - r - 1.6, "leaf")
    return f

def ex_crumbs(pts):
    def f(cv, cx, cy, rx, ry):
        for (dx, dy) in pts: cv.put(cx + dx, cy + dy, "berry")
    return f

def ex_z(big, n):
    def f(cv, cx, cy, rx, ry):
        if big:
            cv.tmpl(int(cx + rx * 0.7), int(cy - ry * 1.15), Z_B, {"#": "zzz"})
            if n >= 2: cv.tmpl(int(cx + rx * 0.95) + 3, int(cy - ry * 1.15) - 8, Z_S, {"#": "zzz"})
        else:
            cv.tmpl(int(cx + rx * 0.8), int(cy - ry * 1.0), Z_S, {"#": "zzz"})
            if n >= 2: cv.tmpl(int(cx + rx * 0.8) + 2, int(cy - ry * 1.0) - 4, [".#", "##"][:0] or ["##", ".#"] if False else Z_S, {"#": "zzz"})
    return f

def ex_hearts(big, which):
    def f(cv, cx, cy, rx, ry):
        T = HEART_B if big else HEART_S
        pos = {0: (-rx * 0.95 - 6, -ry * 0.9), 1: (rx * 0.75, -ry * 1.05)}
        x, y = pos[which]
        cv.tmpl(int(cx + x), int(cy + y), T, {"#": "blush"})
    return f

def ex_star(big, dx, dy, c="glow"):
    def f(cv, cx, cy, rx, ry):
        T = STAR_B if big else STAR_S
        cv.tmpl(int(cx + dx * rx), int(cy + dy * ry), T, {"#": c})
    return f

def ex_drop(big, dx, dy):
    def f(cv, cx, cy, rx, ry):
        T = DROP_B if big else DROP_S
        x, y = int(cx + dx * rx), int(cy + dy * ry)
        for j, r in enumerate(T):
            for i, ch in enumerate(r):
                if ch == "#": cv.put(x + i, y + j, "drop")
        cv.put(x + 1, y + 1, "white")
    return f

# ---------------------------------------------------------------- animations (pet forms)
def anim(form):
    big = FORMS[form]["big"]
    sw = 1 if not big else 2
    A = {}
    # idle: breathe + sprout sway + blink
    A["idle"] = [
        dict(sx=1.0, sy=1.0, sway=0, eyes="open", fluff=0.0, twinkle=0, bud=1.0),
        dict(sx=0.98, sy=1.05, sway=sw, eyes="open", fluff=0.5, twinkle=1, bud=1.1),
        dict(sx=1.0, sy=1.0, sway=0, eyes="blink", fluff=1.0, twinkle=2, bud=1.0),
        dict(sx=1.03, sy=0.96, sway=-sw, eyes="open", fluff=1.5, twinkle=3, bud=0.9),
    ]
    bs = 4.2 if big else 2.4
    A["eat"] = [
        dict(eyes="open", mouth="smile", arms="eat", sway=0, extras=[ex_berry(bs, (3 if big else 2, -2 if big else -1))]),
        dict(eyes="open", mouth="open", arms="eat", sx=1.0, sy=1.03, sway=sw, extras=[ex_berry(bs, (-1 if big else 0, 0))]),
        dict(eyes="happy", mouth="flat", arms="eat", sx=1.05, sy=0.97, sway=0, extras=[ex_berry(bs * .8, (-3 if big else -1, 1), 1)]),
        dict(eyes="happy", mouth="smile", arms="eat", sx=1.0, sy=1.0, sway=-sw, extras=[ex_berry(bs * .6, (-4 if big else -2, 2), 2),
                                       ex_crumbs([(-rx_, 8) for rx_ in ([10, 14] if big else [4])] if False else [])]),
    ]
    A["sleep"] = [
        dict(sx=1.06, sy=0.88, eyes="sleep", mouth="none", blush=True, arms="down", sway=0, droop=1, bud=0.7, extras=[ex_z(big, 1)]),
        dict(sx=1.04, sy=0.92, eyes="sleep", mouth="none", blush=True, arms="down", sway=0, droop=1, bud=0.6, extras=[ex_z(big, 2)]),
    ]
    j = 4 if big else 2
    A["happy"] = [
        dict(sx=1.08, sy=0.88, eyes="happy", mouth="smile", arms="down", lift=0, extras=[]),
        dict(sx=0.95, sy=1.08, eyes="happy", mouth="open", arms="up", lift=j, sway=sw, bud=1.2, extras=[ex_star(big, -0.95, -0.7), ex_hearts(big, 1)]),
        dict(sx=0.96, sy=1.06, eyes="happy", mouth="open", arms="up", lift=j * 0.7, sway=-sw, bud=1.2, extras=[ex_hearts(big, 0), ex_star(big, 0.9, -0.5, "glow_core")]),
        dict(sx=1.08, sy=0.9, eyes="happy", mouth="smile", arms="down", lift=0, bud=1.0, extras=[ex_star(big, 0.85, -0.2)]),
    ]
    A["sick"] = [
        dict(sick=True, sx=1.03, sy=0.94, eyes="sick", mouth="frown", blush=True, arms="down", sway=0, droop=1, dx=-0.0, feet_in=0.1, extras=[ex_drop(big, 0.75, -0.75)]),
        dict(sick=True, sx=1.02, sy=0.95, eyes="sick", mouth="frown", blush=True, arms="down", sway=0, droop=1, dx=1.0 if big else 1.0, feet_in=0.1, extras=[ex_drop(big, 0.75, -0.55)]),
    ]
    return A

# ---------------------------------------------------------------- egg
def egg_mask(cv, cx, cy, rx, ry, tilt=0.0, grow=0.0):
    nx = (cv.xx + .5 - cx) / (rx * (1 + 0.16 * ((cv.yy + .5 - cy) / ry)) + grow)
    ny = (cv.yy + .5 - cy) / (ry + grow)
    return nx * nx + ny * ny <= 1.0

def render_egg(p):
    S = 32; cv = Cv(S)
    glow = p.get("glow", 0)
    cx = 16.0; rx = 8.6 * p.get("sx", 1); ry = 10.4 * p.get("sy", 1)
    bottom = 29.0 - p.get("lift", 0)
    cy = bottom - ry
    tilt = p.get("tilt", 0)  # px shift at top
    ramp = "egg_glow" if glow else "egg"
    m = egg_mask(cv, cx, cy, rx, ry)
    # shear
    if tilt:
        sh = np.zeros_like(m)
        for y in range(S):
            off = int(round(tilt * (bottom - y) / (2 * ry)))
            sh[y] = np.roll(m[y], off)
        m = sh; cx += tilt * 0.0
    nx = (cv.xx + .5 - cx) / rx; ny = (cv.yy + .5 - cy) / ry
    r2 = np.clip(nx * nx + ny * ny, 0, 1.4)
    sv = -(0.55 * nx + 0.8 * ny) - 0.38 * r2 + 0.2
    kk = np.zeros((S, S), int)
    for t in TH: kk += (sv > t)
    kk = np.clip(kk, 0, 3)
    rc = np.array([IDX[c] for c in RAMPS[ramp]], np.uint8)
    if glow:  # halo behind
        g = glow
        h1 = egg_mask(cv, cx, cy, rx, ry, grow=1.2 + g) & ~m
        h2 = egg_mask(cv, cx, cy, rx, ry, grow=2.6 + g * 1.6) & ~m & ~h1
        cv.paint(h1, "glow_mid")
        cv.paint(h2 & (((cv.xx + cv.yy) % 2) == 0), "glow_core" if g > 1 else "glow_mid")
    cv.a[m] = rc[kk][m]
    cv.solid |= m
    # star-dust spots (cream) + orange dots, relative to egg
    def spot(fx, fy, c, big=False):
        x = cx + fx * rx; y = cy + fy * ry
        cv.put(x, y, c)
        if big:
            for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)): cv.put(x + ox, y + oy, c)
    spots = [(-0.35, -0.3, "cream4", True), (0.4, 0.15, "cream3", True), (-0.2, 0.5, "cream4", False), (0.5, -0.45, "cream4", False),
             (0.05, 0.1, "glow_warm", False), (-0.55, 0.15, "glow_warm", False), (0.15, 0.7, "glow_warm", False)]
    for (a, b, c, bg) in spots:
        x = int(round(cx + a * rx)); y = int(round(cy + b * ry))
        if m[min(max(y, 0), S - 1), min(max(x, 0), S - 1)]:
            spot(a, b, c, bg and (m[y, x] and m[y + 1, x] and m[y - 1, x] and m[y, x + 1] and m[y, x - 1]))
    cv.outline()
    # shine
    cv.put(cx - rx * 0.5, cy - ry * 0.55, "cream4"); cv.put(cx - rx * 0.5 + 1, cy - ry * 0.55, "cream4"); cv.put(cx - rx * 0.5 - 1, cy - ry * 0.55 + 1, "cream4")
    # sparkles (twinkle)
    tw = p.get("twinkle", None)
    if tw is not None:
        pos = [(5, 6), (26, 9), (27, 21), (4, 19)]
        for i, (x, y) in enumerate(pos):
            ph = (tw + i) % 4
            if ph == 0:
                cv.put(x, y, "glow_core")
                for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)): cv.put(x + ox, y + oy, "glow_mid")
            elif ph == 1:
                cv.put(x, y, "glow")
    if glow:
        # rays
        L = 3 + glow * 2
        for (dxs, dys) in ((0, -1), (1, -1), (-1, -1), (1, 0), (-1, 0)):
            sx0 = cx + dxs * (rx + 3.5 + glow); sy0 = cy + dys * (ry * (0.9) + 3.5 + glow)
            for s_ in range(int(L)):
                cv.put(sx0 + dxs * s_ * 0.7 , sy0 + dys * s_ * 0.7, "glow_core" if s_ == 0 else "glow_mid")
        for (x, y) in ((5, 7), (26, 8), (27, 22), (4, 21)):
            if glow > 1:
                cv.put(x, y, "glow_core")
                for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)): cv.put(x + ox, y + oy, "glow_mid")
    return cv.a

def egg_anim():
    return {
     "idle": [dict(tilt=0, sx=1, sy=1, twinkle=0), dict(tilt=1, sx=0.99, sy=1.02, twinkle=1, lift=0),
              dict(tilt=0, sx=1.0, sy=1.0, twinkle=2), dict(tilt=-1, sx=0.99, sy=1.02, twinkle=3)],
     "glow": [dict(glow=1, sx=1.0, sy=1.0, twinkle=0), dict(glow=2, sx=1.04, sy=1.04, lift=0.5, twinkle=1)],
    }

README = """# 團絨 Tuanrong 像素 sprite（MVP，原創）
程式化繪製（Pillow／numpy），全部 RGBA PNG、透明底、無抗鋸齒、只用 palette.json 色。重跑：`python3 ../../tools/build_tuanrong.py`

## 形態／尺寸
| form | 階段 | 尺寸 | state（幀數） |
|---|---|---|---|
| egg | 光卵 | 32x32 | idle 4、glow 2 |
| sprout | 芽崽「絨芽」 | 32x32 | idle 4、eat 4、sleep 2、happy 4、sick 2 |
| radiant | 成年「燦光」 | 64x64 | 同上 |
| soft | 成年「柔光」 | 64x64 | 同上 |
共 54 幀。腳底統一貼底（sprite 底邊約 y=G）；唔畫投影，由引擎做 blob shadow。

## 檔案
- `frames/pet_tuanrong_<form>_<state>_<01..>.png` 單幀
- `pet_tuanrong_<form>_sheet.png` 橫排（順序 idle、eat、sleep、happy、sick／glow）
- `pet_tuanrong_<form>_preview_8x.png／.gif` 8x 最近鄰預覽（深色底）
- `pet_tuanrong_atlas.png／.json` 圖集（2048 寬、padding 2px、extrude 1px、免 trim；含 `animations`＋fps）
- `palette.png／palette.json`（31 色＋透明）、`tuanrong_contact_sheet.png`（四形態 idle_01，8x，相似度檢查用）

## fps 建議（loop）
idle 6、eat 8、sleep 2、happy 8、sick 3、glow 4。引擎：Nearest、關 mipmap、整數倍縮放。

## 色盤
31 色（暖米黃／淺橘為主，另有光色、腮紅、食物、zzz、病態灰綠、水滴）；詳見 palette.json。
"""

# ---------------------------------------------------------------- IO
def to_img(a):
    rgba = np.zeros(a.shape + (4,), np.uint8)
    for i, c in enumerate(RGB):
        if i == 0: continue
        rgba[a == i, :3] = c; rgba[a == i, 3] = 255
    return Image.fromarray(rgba, "RGBA")

STATE_ORDER = ["idle", "eat", "sleep", "happy", "sick", "glow"]
FPS = {"idle": 6, "eat": 8, "sleep": 2, "happy": 8, "sick": 3, "glow": 4}
SIZES = {"egg": 32, "sprout": 32, "radiant": 64, "soft": 64}
FORM_ORDER = ["egg", "sprout", "radiant", "soft"]

def build_all():
    frames = {}  # form -> state -> [np arrays]
    frames["egg"] = {st: [render_egg(p) for p in ps] for st, ps in egg_anim().items()}
    for form in ("sprout", "radiant", "soft"):
        A = anim(form)
        frames[form] = {st: [render_pet(form, p) for p in ps] for st, ps in A.items()}
    return frames

def pack(items, maxw=2048, pad=2):
    # shelf packer, tallest-first
    items = sorted(items, key=lambda t: (-t[2].shape[0], t[0]))
    x = y = pad; rowh = 0; pos = {}
    for name, _, a in items:
        h, w = a.shape[:2]
        if x + w + pad > maxw:
            x = pad; y += rowh + pad; rowh = 0
        pos[name] = (x, y, w, h)
        x += w + pad; rowh = max(rowh, h)
    H = y + rowh + pad
    return pos, H

def main():
    import shutil
    if os.path.isdir(OUT):  # keep motion/ (built by build_tuanrong_motion.py)
        for _n in os.listdir(OUT):
            if _n == 'motion': continue
            _p = os.path.join(OUT, _n)
            shutil.rmtree(_p) if os.path.isdir(_p) else os.remove(_p)
    os.makedirs(FR, exist_ok=True)
    frames = build_all()
    # per-frame files
    items = []; anim_meta = {}
    for form in FORM_ORDER:
        n = SIZES[form]
        sheet_imgs = []
        for st in STATE_ORDER:
            if st not in frames[form]: continue
            names = []
            for i, a in enumerate(frames[form][st], 1):
                name = f"pet_tuanrong_{form}_{st}_{i:02d}"
                to_img(a).save(os.path.join(FR, name + ".png"))
                items.append((name, form, a)); names.append(name); sheet_imgs.append(a)
            anim_meta[f"{form}_{st}"] = dict(frames=names, fps=FPS[st], loop=True)
        # sheet (single row)
        sh = np.concatenate(sheet_imgs, axis=1)
        to_img(sh).save(os.path.join(OUT, f"pet_tuanrong_{form}_sheet.png"))
        # preview: rows per state, 8x, dark bg
        Z = 8; gap = 12; bg = (92, 88, 128, 255)
        rows = [st for st in STATE_ORDER if st in frames[form]]
        maxc = max(len(frames[form][st]) for st in rows)
        W = maxc * n * Z + (maxc + 1) * gap; H = len(rows) * n * Z + (len(rows) + 1) * gap
        pv = Image.new("RGBA", (W, H), bg)
        for r, st in enumerate(rows):
            for c, a in enumerate(frames[form][st]):
                im = to_img(a).resize((n * Z, n * Z), Image.NEAREST)
                pv.alpha_composite(im, (gap + c * (n * Z + gap), gap + r * (n * Z + gap)))
        pv.save(os.path.join(OUT, f"pet_tuanrong_{form}_preview_8x.png"))
        # gif (8x, all states in sequence)
        gf, dur = [], []
        for st in rows:
            for a in frames[form][st]:
                base = Image.new("RGBA", (n * Z, n * Z), bg)
                base.alpha_composite(to_img(a).resize((n * Z, n * Z), Image.NEAREST))
                gf.append(base.convert("RGB").quantize(colors=64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
                dur.append(int(1000 / FPS[st]))
            # repeat idle-like short states so they read
            reps = {"sleep": 2, "sick": 3, "glow": 3}.get(st, 1)
            for _ in range(reps - 1):
                for a in frames[form][st]:
                    base = Image.new("RGBA", (n * Z, n * Z), bg)
                    base.alpha_composite(to_img(a).resize((n * Z, n * Z), Image.NEAREST))
                    gf.append(base.convert("RGB").quantize(colors=64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
                    dur.append(int(1000 / FPS[st]))
        gf[0].save(os.path.join(OUT, f"pet_tuanrong_{form}_preview_8x.gif"), save_all=True, append_images=gf[1:], duration=dur, loop=0, disposal=1)
    open(os.path.join(OUT, 'README.md'), 'w', encoding='utf-8').write(README)
    # atlas
    pos, H = pack(items)
    atl = np.zeros((H, 2048), np.uint8)
    atlas_img = Image.new("RGBA", (2048, H), (0, 0, 0, 0))
    jf = {}
    for name, form, a in items:
        x, y, w, h = pos[name]
        im = to_img(a)
        atlas_img.paste(im, (x, y))
        # extrude 1px
        e = np.array(im)
        atlas_img.paste(Image.fromarray(e[:1], "RGBA"), (x, y - 1)); atlas_img.paste(Image.fromarray(e[-1:], "RGBA"), (x, y + h))
        atlas_img.paste(Image.fromarray(e[:, :1], "RGBA"), (x - 1, y)); atlas_img.paste(Image.fromarray(e[:, -1:], "RGBA"), (x + w, y))
        jf[name] = {"frame": {"x": x, "y": y, "w": w, "h": h}, "rotated": False, "trimmed": False,
                    "spriteSourceSize": {"x": 0, "y": 0, "w": w, "h": h}, "sourceSize": {"w": w, "h": h}}
    atlas_img.save(os.path.join(OUT, "pet_tuanrong_atlas.png"))
    json.dump({"frames": jf, "animations": anim_meta,
               "meta": {"image": "pet_tuanrong_atlas.png", "size": {"w": 2048, "h": H}, "scale": 1, "format": "RGBA8888", "padding": 2, "extrude": 1}},
              open(os.path.join(OUT, "pet_tuanrong_atlas.json"), "w"), indent=1)
    # palette
    used = set()
    for form in frames.values():
        for st in form.values():
            for a in st: used |= set(np.unique(a).tolist())
    used.discard(0)
    pj = [{"index": i, "name": n, "hex": PAL[n]} for n, i in IDX.items()]
    json.dump({"transparent": True, "count": len(NAMES), "used_count": len(used), "colors": pj}, open(os.path.join(OUT, "palette.json"), "w"), indent=1, ensure_ascii=False)
    cols = 8; sw = 48
    rowsn = math.ceil(len(NAMES) / cols)
    pi = Image.new("RGBA", (cols * sw, rowsn * sw), (0, 0, 0, 0))
    for n, i in IDX.items():
        k = i - 1; x, y = (k % cols) * sw, (k // cols) * sw
        pi.paste(Image.new("RGBA", (sw, sw), RGB[i] + (255,)), (x, y))
    pi.save(os.path.join(OUT, "palette.png"))
    # contact sheet: idle_01 of 4 forms, 8x, no text
    Z = 8; m = 32; ims = []
    for form in FORM_ORDER:
        n = SIZES[form]; ims.append(to_img(frames[form]["idle"][0]).resize((n * Z, n * Z), Image.NEAREST))
    W = sum(i.width for i in ims) + m * (len(ims) + 1); Hh = max(i.height for i in ims) + 2 * m
    cs = Image.new("RGBA", (W, Hh), (92, 88, 128, 255)); x = m
    for im in ims:
        cs.alpha_composite(im, (x, Hh - m - im.height)); x += im.width + m
    cs.save(os.path.join(OUT, "tuanrong_contact_sheet.png"))
    print("frames:", {f: {s: len(v) for s, v in d.items()} for f, d in frames.items()})
    print("palette:", len(NAMES), "defined,", len(used), "used; atlas H", H)

if __name__ == "__main__":
    main()
