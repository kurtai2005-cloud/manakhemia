#!/usr/bin/env python3
"""build_tuanrong_motion.py — 團絨 pet-motion clips (sprout/radiant/soft) + shared props.
Pillow + numpy only, procedural, original. Re-runnable: python3 build_tuanrong_motion.py
Reuses build_tuanrong.py renderer + palette (31 colours).  Output -> ../sprites/tuanrong/motion/
"""
import json, math, os, shutil, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_tuanrong as bt
from build_tuanrong import IDX, RGB, PAL, NAMES, FORMS, to_img

OUT = os.path.join(bt.OUT, "motion")
BG = (92, 88, 128, 255)

# ------------------------------------------------------------ extra face templates (palette colours only)
bt.EYE[False].update({"none": [], "half": ["##", "w#"], "wide": ["###", "w##", "###"], "shine": ["###", "ww#", "###"]})
bt.EYE[True].update({"none": [], "half": ["####", "#w##", ".##."],
                     "wide": [".###.", "#w###", "#####", "#####", "#####", ".###."],
                     "shine": [".###.", "#ww##", "#####", "#####", ".###."]})
bt.MOUTH[False].update({"yawn": [".#####.", "#rrrrr#", "#rrrrr#", "#rrtrr#", ".#####."], "cat": ["#.#", ".#."]})
bt.MOUTH[True].update({"yawn": ["..#####..", ".#rrrrr#.", "#rrrrrrr#", "#rrrtrrr#", ".#rrrrr#.", "..#####.."], "cat": ["#.#.#", ".#.#."]})
bt.CM["t"] = "blush"

FACE = [0, 0]
_orig_dt = bt.draw_tmpl_c
def _dt(cv, cx, cy, rows, cm=bt.CM):
    _orig_dt(cv, cx + FACE[0], cy + FACE[1], rows, cm)
bt.draw_tmpl_c = _dt

bt.RAMPS["sun_sprout"] = ["cream1", "cream2", "cream3", "cream4"]
bt.RAMPS["sun_radiant"] = ["cream2", "cream3", "cream4", "glow_core"]
bt.RAMPS["sun_soft"] = ["peach1", "peach2", "cream3", "cream4"]

# ------------------------------------------------------------ face extras (marked .face so overlay can split them)
def ex_brow(big, kind="worry"):
    pts = [(-2, 0), (-1, 0), (0, -1), (1, -1)] if big else [(-1, 0), (0, -1)]
    def f(cv, cx, cy, rx, ry):
        ey = cy + ry * 0.08 + FACE[1]; eoff = rx * (0.40 if big else 0.42)
        by = ey - (4.5 if big else 3.0)
        for sgn in (-1, 1):
            ex = cx + sgn * eoff + FACE[0]
            for u, dy in pts:
                cv.put(ex - sgn * u, by + dy, "outline")
    f.face = True
    return f

def ex_cheeks(big):
    def f(cv, cx, cy, rx, ry):
        ey = cy + ry * 0.08
        for sgn in (-1, 1):
            m = cv.ell(cx + sgn * rx * 0.62, ey + ry * 0.26, 3.6 if big else 2.2, 2.2 if big else 1.3)
            cv.a[m & cv.solid & (cv.a != IDX["outline"])] = IDX["blush"]
            cv.put(cx + sgn * rx * 0.62, ey + ry * 0.26, "blush_d")
    f.face = True
    return f

def ex_arms_up(form):
    big = FORMS[form]["big"]
    def f(cv, cx, cy, rx, ry):
        ramp = bt.RAMPS[FORMS[form]["ramp"]]
        col = ramp[2]; hi = ramp[3]
        for sgn in (-1, 1):
            if big: parts = [(cx + sgn * (rx + .6), cy - ry * .25, 2.6, 3.2), (cx + sgn * (rx + 1.8), cy - ry * .25 - 4.2, 2.3, 2.6)]
            else:   parts = [(cx + sgn * (rx + .3), cy - ry * .2, 1.7, 2.1), (cx + sgn * (rx + 1.1), cy - ry * .2 - 2.6, 1.5, 1.6)]
            m = np.zeros_like(cv.solid)
            for (x, y, a, b) in parts: m |= cv.ell(x, y, a, b)
            d = np.zeros_like(m); d[1:, :] |= m[:-1, :]; d[:-1, :] |= m[1:, :]; d[:, 1:] |= m[:, :-1]; d[:, :-1] |= m[:, 1:]
            cv.a[d & ~m] = IDX["outline"]
            cv.a[m] = IDX[col]
            x, y, a, b = parts[1]
            cv.put(x - sgn * .5, y - b * .3, hi)
    return f

def ex_warm(big, t):
    cand = [(-0.55, -0.5), (-0.2, -0.78), (0.15, -0.62), (-0.72, -0.1), (0.4, -0.45), (-0.4, 0.1)]
    def f(cv, cx, cy, rx, ry):
        for k in (t % 6, (t + 3) % 6):
            tx, ty = cand[k]
            x, y = int(round(cx + tx * rx)), int(round(cy + ty * ry))
            for (ox, oy, c) in ((0, 0, "glow_core"), (1, 0, "glow_mid"), (-1, 0, "glow_mid"), (0, 1, "glow_mid"), (0, -1, "glow_mid")) if big else ((0, 0, "glow_core"),):
                xx, yy = x + ox, y + oy
                if 0 <= xx < cv.n and 0 <= yy < cv.n and cv.a[yy, xx] not in (0, IDX["outline"]):
                    cv.a[yy, xx] = IDX[c]
    return f

# ------------------------------------------------------------ renderer wrapper
def shear_arr(a, form, amount):
    S = a.shape[0]; f = FORMS[form]
    y0 = S - 3; ref = f["ry"] * 2.0
    out = np.zeros_like(a)
    for y in range(S):
        sh = 0 if y >= y0 else int(round(amount * (y0 - y) / ref))
        if sh == 0: out[y] = a[y]
        elif sh > 0: out[y, sh:] = a[y, :-sh]
        else: out[y, :sh] = a[y, -sh:]
    return out

def render(form, p):
    p = dict(p)
    FACE[0], FACE[1] = p.pop("fdx", 0), p.pop("fdy", 0)
    sh = p.pop("shear", 0)
    ramp = p.pop("ramp", None)
    if p.get("arms") == "upx":
        p["arms"] = "none"; p["extras"] = list(p.get("extras", [])) + [ex_arms_up(form)]
    old = FORMS[form]["ramp"]
    if ramp: FORMS[form]["ramp"] = ramp
    try:
        a = bt.render_pet(form, p)
    finally:
        FORMS[form]["ramp"] = old
    if sh: a = shear_arr(a, form, sh)
    return a

FIT_LOG = []
def render_fit(form, p, tag=""):
    """render; if sprite touches top/left/right border, ease lift/sy/dx/shear until it fits"""
    p = dict(p); log = []
    for _ in range(12):
        a = render(form, p)
        if a[0].any():
            if p.get("lift", 0) > 0: p["lift"] = p["lift"] - 1; log.append("lift-1")
            else: p["sy"] = round(p.get("sy", 1.0) - .02, 3); log.append("sy-.02")
            if p.get("bud", 1.0) > 1.0: p["bud"] = 1.0
        elif a[:, 0].any() or a[:, -1].any():
            side = 1 if a[:, -1].any() else -1
            dxs, shs = p.get("dx", 0) * side, p.get("shear", 0) * side
            if shs > 0 and shs >= dxs: p["shear"] = p["shear"] - side; log.append("shear")
            elif dxs > 0: p["dx"] = p["dx"] - side; log.append("dx")
            elif p.get("sway", 0) * side > 0: p["sway"] = p["sway"] - side; log.append("sway")
            elif p.get("sx", 1.0) > 1.0: p["sx"] = round(p["sx"] - .02, 3); log.append("sx-.02")
            else: break
        else: break
    if log: FIT_LOG.append((form, tag, log))
    return p

def render_split(form, p):
    """full frame, face-less body frame, face overlay (face pixels only)"""
    full = render(form, p)
    q = dict(p); q["eyes"] = "none"; q["mouth"] = "none"; q["blush"] = False
    q["extras"] = [e for e in p.get("extras", []) if not getattr(e, "face", False)]
    body = render(form, q)
    ov = np.where(full != body, full, 0).astype(np.uint8)
    return full, body, ov

# ------------------------------------------------------------ clip definitions
def clips(form):
    f = FORMS[form]; big = f["big"]; u = 2 if big else 1; j = 4 if big else 2
    br = lambda: ex_brow(big); ch = lambda: ex_cheeks(big)
    base = bt.anim(form)
    sunr = "sun_" + form
    C = {}
    C["idle"] = base["idle"]
    C["blink"] = [dict(eyes="open"), dict(eyes="half", sy=.99), dict(eyes="blink", sy=.98), dict(eyes="half")]
    C["sway"] = [dict(bud=1.05), dict(sway=2 * u, shear=1, bud=1.1, fluff=.5),
                 dict(sy=1.02, bud=1.0, fluff=1.0), dict(sway=-2 * u, shear=-1, bud=1.1, fluff=1.5)]
    C["yawn"] = [dict(eyes="half", mouth="o", sy=1.04, sx=.98),
                 dict(eyes="sleep", mouth="yawn", sy=1.08, sx=.96, arms="upx", bud=1.2),
                 dict(eyes="sleep", mouth="yawn", sy=1.10, sx=.95, arms="upx", bud=1.25, sway=u),
                 dict(eyes="half", mouth="o", sy=.97, sx=1.03)]
    C["emo_happy"] = [dict(eyes="happy", mouth="open", sx=1.05, sy=.95),
                      dict(eyes="happy", mouth="open", sx=.97, sy=1.05, lift=u, arms="upx", bud=1.15, sway=u)]
    C["emo_hungry"] = [dict(eyes="open", mouth="frown", sx=1.04, sy=.94, bud=.75, droop=1, extras=[br()]),
                       dict(eyes="open", mouth="o", sx=1.06, sy=.90, bud=.65, droop=1, dx=1, extras=[br()])]
    C["emo_wantplay"] = [dict(eyes="shine", mouth="open", arms="upx", sx=1.04, sy=.94),
                         dict(eyes="shine", mouth="open", arms="upx", lift=u, sx=.97, sy=1.05, sway=u, bud=1.15)]
    C["emo_sleepy"] = [dict(eyes="half", mouth="flat", sx=1.04, sy=.94, droop=1, bud=.8),
                       dict(eyes="sleep", mouth="flat", sx=1.07, sy=.90, droop=1, bud=.65, fdy=1)]
    C["emo_cuddly"] = [dict(eyes="happy", mouth="cat", sx=1.04, sy=.96, dx=-u, shear=-u, fdx=-1, extras=[ch()]),
                       dict(eyes="happy", mouth="cat", sx=1.04, sy=.96, dx=u, shear=u, fdx=1, extras=[ch()])]
    C["emo_surprised"] = [dict(eyes="wide", mouth="o", arms="upx", lift=u, sx=.94, sy=1.08, bud=1.25),
                          dict(eyes="wide", mouth="o", arms="upx", lift=1, sx=.98, sy=1.04, bud=1.15)]
    # ---- walk v2: one full gait (left step, right step), periodic: frame 6 flows into frame 1, net dx = 0
    # per step (3 frames): contact-squash -> push-off/rise (swing foot lifts) -> reach (body highest) ; waddle via dx + lean
    L = [0, 1, 1] if not big else [0, 1, 2]
    SY = [.94, 1.02, 1.04]; SX = [1.06, .98, .97]; FI = [0, .15, .35]
    FL = [(0, 0), (0, u), (0, 0)]               # swing-foot lift: stepping foot leaves the ground mid-step
    DXW = [-1, 0, 1, 1, 0, -1]
    C["walk"] = []
    for k in range(6):
        i = k % 3; right = k >= 3
        fl = (FL[i][1], FL[i][0]) if right else FL[i]
        C["walk"].append(dict(eyes="open", mouth="smile", sx=SX[i], sy=SY[i], lift=L[i], feet_in=FI[i], flift=fl,
                              shear=u + (1 if i == 1 else 0), dx=DXW[k], fdx=u, sway=u if i == 2 else 0,
                              bud=(1.1 if i == 2 else 1.0)))
    # ---- play v2: crouch -> wind-up twist -> spring -> pounce (peak) -> land squash -> settle.  baked dx nets to 0
    pdx = [-u, -u, 0, 2 * u, u, 0]
    C["play"] = [dict(eyes="shine", mouth="open", arms="upx", sx=1.14, sy=.82, shear=-u, dx=pdx[0], bud=.9),
                 dict(eyes="shine", mouth="open", arms="upx", sx=1.16, sy=.80, shear=-u, dx=pdx[1], bud=.9, fdx=-u // 2),
                 dict(eyes="wide", mouth="open", arms="upx", sx=.92, sy=1.10, lift=max(1, j // 2), shear=2 * u, dx=pdx[2], bud=1.0 if not big else 1.15, fdx=u),
                 dict(eyes="shine", mouth="open", arms="upx", sx=.98, sy=1.03, lift=j, shear=2 * u, dx=pdx[3], bud=1.0 if not big else 1.2, fdx=u),
                 dict(eyes="happy", mouth="open", arms="down", sx=1.18, sy=.80, shear=u, dx=pdx[4], bud=1.0),
                 dict(eyes="happy", mouth="smile", sx=1.02, sy=1.03, bud=1.05, dx=pdx[5])]
    C["fall_asleep"] = [dict(eyes="half", mouth="flat", sy=.97, bud=.95),
                        dict(eyes="blink", mouth="o", sx=1.03, sy=.93, droop=1, bud=.85, fdy=1),
                        dict(eyes="half", mouth="flat", sy=.97, bud=.9, droop=1),
                        dict(eyes="sleep", mouth="none", sx=1.06, sy=.88, droop=1, bud=.7)]
    SL = [.86, .90, .94, .90]
    C["sleep_loop"] = [dict(eyes="sleep", mouth="none", sx=1.0 + (1.0 - s) * .5, sy=s, droop=1, bud=b, fluff=k * .5)
                       for k, (s, b) in enumerate(zip(SL, [.7, .65, .6, .65]))]
    C["wake"] = [dict(eyes="half", mouth="o", sx=1.03, sy=.93, droop=1, bud=.8),
                 dict(eyes="blink", mouth="yawn", arms="upx", sx=.95, sy=1.08, bud=1.2),
                 dict(eyes="half", mouth="o", sx=1.0, sy=1.0, sway=u, bud=1.05),
                 dict(eyes="open", mouth="smile", bud=1.0)]
    SB_SY = [.90, .92, .94, .96, .94, .92, .90, .90]
    C["sunbathe"] = []
    for k in range(8):
        C["sunbathe"].append(dict(ramp=sunr, eyes="sleep" if k in (3, 4) else "happy", mouth="smile",
                                  sx=1.0 + (1.0 - SB_SY[k]) * .6, sy=SB_SY[k], arms="upx" if k in (2, 3, 4) else "down",
                                  bud=1.2, sway=(k % 4 in (1,)) * u - (k % 4 == 3) * u, twinkle=k, fluff=k * .4,
                                  extras=[ex_warm(big, k)]))
    C["pot_bump"] = [dict(eyes="open", mouth="smile", sy=.97, shear=u, fdx=u),
                     dict(eyes="open", mouth="smile", sx=1.1, sy=.86, shear=-u, dx=-u, fdx=u),
                     dict(eyes="wide", mouth="open", sx=.94, sy=1.06, lift=1, shear=2 * u, dx=u, fdx=u),
                     dict(eyes="sick", mouth="o", sx=.84, sy=1.04, shear=2 * u, dx=2 * u, bud=1.3, fdx=u),
                     dict(eyes="sick", mouth="o", sx=1.02, sy=.90, shear=-u, dx=u, bud=1.1),
                     dict(eyes="wide", mouth="o", sy=1.04, sway=-u, dx=0, fdx=-1),
                     dict(eyes="half", mouth="o", sy=.98, shear=u, sway=u, fdx=-u),
                     dict(eyes="open", mouth="smile")]
    C["catch_reach"] = [dict(eyes="shine", mouth="open", fdy=-1),
                        dict(eyes="shine", mouth="open", arms="upx", sx=.96, sy=1.06, shear=u, bud=1.1, fdy=-1),
                        dict(eyes="shine", mouth="open", arms="upx", lift=u, sx=.94, sy=1.10 if not big else 1.07, shear=u, bud=1.15, fdy=-1),
                        dict(eyes="wide", mouth="open", arms="upx", lift=j, sx=.96, sy=1.04, shear=u, bud=1.2, fdy=-1),
                        dict(eyes="happy", mouth="open", arms="eat", sx=1.10, sy=.86),
                        dict(eyes="happy", mouth="smile", arms="upx", lift=u, sx=.97, sy=1.04, bud=1.2, sway=u)]
    C["cheer_jump"] = [dict(eyes="happy", mouth="smile", sx=1.15, sy=.80),
                       dict(eyes="happy", mouth="open", arms="upx", lift=max(1, j // 2), sx=.92, sy=1.08, bud=1.2),
                       dict(eyes="happy", mouth="open", arms="upx", lift=j, sx=.98, sy=1.02, bud=1.25, sway=u),
                       dict(eyes="happy", mouth="open", arms="upx", lift=max(1, int(j * .6)), sx=.96, sy=1.04, bud=1.2, sway=-u),
                       dict(eyes="happy", mouth="smile", sx=1.15, sy=.80),
                       dict(eyes="happy", mouth="open", arms="upx", sx=1.0, sy=1.03, bud=1.15)]
    C["droop"] = [dict(eyes="open", mouth="frown", sy=.96, droop=1, bud=.8, extras=[br()]),
                  dict(eyes="half", mouth="frown", sx=1.05, sy=.90, droop=1, bud=.6, extras=[br()]),
                  dict(eyes="blink", mouth="flat", sx=1.10, sy=.84, droop=1, bud=.5, fdy=1, extras=[br()]),
                  dict(eyes="half", mouth="frown", sx=1.09, sy=.85, droop=1, bud=.5, dx=-1, fdy=1, extras=[br()]),
                  dict(eyes="half", mouth="frown", sx=1.09, sy=.85, droop=1, bud=.45, dx=1, fdy=1, extras=[br()]),
                  dict(eyes="half", mouth="frown", sx=1.10, sy=.84, droop=1, bud=.5, fdy=1, extras=[br()])]
    if not big:   # 32px: only 4px headroom -> bud stays ~1.0 on lifted frames so the 2px jump survives
        for cn in ("catch_reach", "cheer_jump", "play", "walk"):
            for p_ in C[cn]:
                if p_.get("lift", 0) > 0: p_["bud"] = min(p_.get("bud", 1.0), 1.0)
    C["eat"] = base["eat"]; C["celebrate"] = base["happy"]; C["sick"] = base["sick"]
    return C

ORDER = ["idle", "blink", "sway", "yawn", "emo_happy", "emo_hungry", "emo_wantplay", "emo_sleepy", "emo_cuddly",
         "emo_surprised", "walk", "play", "fall_asleep", "sleep_loop", "wake", "sunbathe", "pot_bump",
         "catch_reach", "cheer_jump", "droop", "eat", "celebrate", "sick"]
# clip meta: fps, loop, loopFrom, priority, interruptible
META = {
 "idle": (6, True, 0, 0, True), "blink": (10, False, 0, 1, True), "sway": (5, False, 0, 1, True), "yawn": (4, False, 0, 1, True),
 "emo_happy": (4, False, 0, 4, True), "emo_hungry": (3, True, 0, 3, True), "emo_wantplay": (4, True, 0, 3, True),
 "emo_sleepy": (2, True, 0, 3, True), "emo_cuddly": (3, True, 0, 4, True), "emo_surprised": (6, False, 0, 4, False),
 "walk": (10, True, 0, 2, True), "play": (8, False, 0, 3, False),
 "fall_asleep": (3, False, 0, 5, False), "sleep_loop": (2, True, 0, 5, True), "wake": (5, False, 0, 5, False),
 "sunbathe": (4, True, 0, 2, True), "pot_bump": (8, False, 0, 2, False),
 "catch_reach": (8, False, 0, 6, False), "cheer_jump": (10, False, 0, 6, False), "droop": (4, True, 3, 6, True),
 "eat": (8, False, 0, 5, False), "celebrate": (8, False, 0, 5, False), "sick": (3, True, 0, 5, True),
}
EMO = [c for c in ORDER if c.startswith("emo_")]

# ------------------------------------------------------------ generic raster helpers (rect canvas)
class Pv(bt.Cv):
    def __init__(s, w, h):
        s.w, s.h, s.n = w, h, max(w, h)
        s.a = np.zeros((h, w), np.uint8)
        s.yy, s.xx = np.mgrid[0:h, 0:w]
        s.solid = np.zeros((h, w), bool)
    def put(s, x, y, c):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < s.w and 0 <= y < s.h:
            s.a[y, x] = IDX[c] if isinstance(c, str) else c
    def auto_outline(s, color="outline"):
        s.solid = s.a != 0
        s.outline(color)

def tmpl_arr(pv, x, y, rows, cmap):
    pv.tmpl(x, y, rows, cmap)

def shift_arr(a, dx, dy=0):
    out = np.zeros_like(a)
    h, w = a.shape
    xs0, xs1 = max(0, -dx), min(w, w - dx); ys0, ys1 = max(0, -dy), min(h, h - dy)
    if xs1 > xs0 and ys1 > ys0:
        out[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx] = a[ys0:ys1, xs0:xs1]
    return out

def shear_rows(a, y0, ref, amount):
    out = np.zeros_like(a)
    for y in range(a.shape[0]):
        sh = 0 if y >= y0 else int(round(amount * (y0 - y) / ref))
        if sh == 0: out[y] = a[y]
        elif sh > 0: out[y, sh:] = a[y, :-sh]
        else: out[y, :sh] = a[y, -sh:]
    return out

def heart_mask(pv, cx, cy, s):
    X = (pv.xx + .5 - cx) / s; Y = -(pv.yy + .5 - cy) / s
    return ((X * X + Y * Y - 1) ** 3 - X * X * Y ** 3) <= 0

# ------------------------------------------------------------ props
def p_flowerpot(bump=0, plant_shear=0, pot_dx=0):
    pv = Pv(32, 32)
    pot = Pv(32, 32); plant = Pv(32, 32)
    # pot
    for y in range(17, 29):
        if y <= 19: x0, x1 = 8, 23
        else:
            k = y - 20; x0, x1 = 9 + int(k * .25), 22 - int(k * .25)
        for x in range(x0, x1 + 1):
            c = "orange"
            if y <= 19:
                c = "peach1" if y == 17 else ("orange" if x < x1 - 3 else "orange_d")
                if y == 19: c = "orange_d" if x >= x0 + 2 else "orange_dd"
            else:
                c = "orange" if x < x1 - 4 else "orange_d"
                if y >= 27: c = "orange_d" if x < x1 - 2 else "orange_dd"
                if x == x0 + 1 and y in (21, 22): c = "peach1"
            pot.a[y, x] = IDX[c]
    for x in range(10, 22): pot.a[17, x] = IDX["orange_dd"]            # soil
    for x in range(11, 21): pot.a[17, x] = IDX["orange_dd"] if x % 3 else IDX["outline"]
    # plant
    for y in range(8, 17):
        plant.a[y, 16] = IDX["leaf_d"]; plant.a[y, 15] = IDX["leaf"]
    for (cx, cy, rx, ry, sg) in ((11.5, 13.5, 3.2, 1.7, -1), (20.5, 11.5, 3.2, 1.7, 1)):
        m = plant.ell(cx, cy, rx, ry)
        plant.a[m] = IDX["leaf"]
        plant.a[m & (plant.xx * sg > cx * sg)] = IDX["leaf_d"]
        plant.a[int(cy), int(cx)] = IDX["leaf_d"]
    # flower
    fx, fy = 15.5, 6.0
    for (ox, oy) in ((0, -3), (3, -1), (2, 2), (-2, 2), (-3, -1)):
        m = plant.ell(fx + ox, fy + oy, 2.0, 2.0); plant.a[m] = IDX["blush"]
    plant.a[plant.ell(fx, fy, 2.0, 2.0)] = IDX["glow_mid"]
    plant.a[int(fy), int(fx)] = IDX["glow_core"]
    plant.a[int(fy) - 3, int(fx) - 1] = IDX["white"]
    if plant_shear: plant.a = shear_rows(plant.a, 17, 14, plant_shear)
    a = plant.a.copy(); a[pot.a != 0] = pot.a[pot.a != 0]
    # pot (dx) after plant to keep plant rooted: shift pot rows only
    if pot_dx:
        pa = shift_arr(pot.a, pot_dx)
        a = plant.a.copy(); a[pa != 0] = pa[pa != 0]
    pv.a = a
    pv.auto_outline()
    return pv.a

def p_sun_patch(phase):
    pv = Pv(48, 16)
    cx, cy = 24, 8
    X = (pv.xx + .5 - cx) / 22.0; Y = (pv.yy + .5 - cy) / 7.0
    r = X * X + Y * Y
    chk = ((pv.xx + pv.yy + phase) % 2 == 0)
    chk2 = ((pv.xx // 2 + pv.yy // 2 + phase) % 2 == 0)
    pv.a[r <= 1.0] = IDX["glow_mid"]
    pv.a[(r > .72) & (r <= 1.0) & ~chk] = 0                       # soft rim (dither)
    pv.a[(r > .86) & (r <= 1.0) & chk2] = 0
    pv.a[(r <= .5) & chk] = IDX["glow_core"]
    pv.a[(r <= .22)] = IDX["glow_core"]
    # drifting dust motes
    for (x, y) in ((14, 5), (33, 10), (26, 3)):
        pv.put(x + phase, y, "white")
    return pv.a

def p_zzz(f):
    pv = Pv(24, 24)
    Z7 = ["#######", ".....##", "....##.", "...##..", "..##...", ".##....", "#######"]
    parts = [(bt.Z_S, 2, 18 - f), (bt.Z_B, 6, 10 - f)]
    if f >= 1: parts.append((Z7, 14, 1 + (0 if f == 1 else 1)))
    if f == 2: parts[0] = (bt.Z_S, 3, 15)
    big = pv
    for rows, x, y in parts:
        t = Pv(24, 24); t.tmpl(x, y, rows, {"#": "zzz"})
        big.a[t.a != 0] = t.a[t.a != 0]
    pv.auto_outline()
    return pv.a

def p_heart(f):
    pv = Pv(16, 16)
    T = [[".XX.XX.", "XXXXXXX", "XXXXXXX", ".XXXXX.", "..XXX..", "...X..."],
         [".XXX.XXX.", "XXXXXXXXX", "XXXXXXXXX", "XXXXXXXXX", ".XXXXXXX.", "..XXXXX..", "...XXX...", "....X...."]][f]
    h, w = len(T), len(T[0]); x0 = (16 - w) // 2; y0 = 14 - h
    pv.tmpl(x0, y0, T, {"X": "blush"})
    for j in range(h):
        for i in range(w):
            if T[j][i] == "X" and (i - w / 2) + (j - h / 2) * 0.8 > w * .22: pv.a[y0 + j, x0 + i] = IDX["blush_d"]
    pv.put(x0 + 1, y0 + 1, "white")
    if f: pv.put(x0 + 2, y0 + 1, "white")
    pv.auto_outline()
    return pv.a

def p_sweat(f):
    pv = Pv(16, 16)
    y = 3 + f * 1
    cx, cy, r = 8, y + 7.0, 3.3
    m = pv.ell(cx, cy, r, r) | ((pv.yy >= y) & (pv.yy < cy) & (np.abs(pv.xx + .5 - cx) <= (pv.yy - y + .5) * r / (cy - y)))
    pv.a[m] = IDX["drop"]
    pv.a[m & (pv.xx + .5 - cx > 1.0) & (pv.yy > cy - 3)] = IDX["drop_d"]
    pv.put(cx - 1.5, cy - 1, "white"); pv.put(cx - 1.5, cy, "white")
    pv.auto_outline()
    return pv.a

def p_exclaim(f):
    pv = Pv(16, 16)
    y = 2 + (0 if f == 0 else 1)
    rows = ["####", "####", "####", "####", ".##.", ".##.", "....", ".##.", ".##."]
    pv.tmpl(6, y, rows, {"#": "berry"})
    for yy in range(y, y + 9):
        for xx in (8, 9):
            if pv.a[yy, xx]: pv.a[yy, xx] = IDX["berry_d"]
    pv.put(6, y, "white"); pv.put(6, y + 1, "white")
    pv.auto_outline()
    return pv.a

def p_question(f):
    pv = Pv(16, 16)
    y = 3 + (0 if f == 0 else 1)
    rows = [".####.", "##..##", "....##", "...##.", "..##..", "..##..", "......", "..##..", "..##.."]
    pv.tmpl(5, y, rows, {"#": "drop"})
    for yy in range(y, y + 9):
        for xx in range(5, 11):
            if pv.a[yy, xx] and xx >= 8 and yy > y + 1: pv.a[yy, xx] = IDX["drop_d"]
    pv.put(6, y, "white"); pv.put(5, y + 1, "white")
    pv.auto_outline()
    return pv.a

# props: name -> (list of arrays, pivot(x,y), fps, loop, note)
def build_props():
    P = {}
    P["flowerpot_idle"] = ([p_flowerpot()], (16, 29), 1, True)
    sh = [3, -3, 2, -1]; pdx = [1, 0, 0, 0]
    P["flowerpot_bump"] = ([p_flowerpot(plant_shear=s, pot_dx=d) for s, d in zip(sh, pdx)], (16, 29), 8, False)
    P["sun_patch"] = ([p_sun_patch(0), p_sun_patch(1)], (24, 8), 2, True)
    P["zzz"] = ([p_zzz(i) for i in range(3)], (2, 22), 2, True)
    P["heart"] = ([p_heart(0), p_heart(1)], (8, 14), 3, True)
    P["sweat"] = ([p_sweat(0), p_sweat(1)], (8, 14), 3, True)
    P["exclaim"] = ([p_exclaim(0), p_exclaim(1)], (8, 14), 4, True)
    P["question"] = ([p_question(0), p_question(1)], (8, 14), 3, True)
    return P

# anchors: pet pivot -> where the (head-right) icon pivot goes, per form;  ground ones: pot_dx
ANCH = {"sprout": dict(head_r=(9, -14), pot=(22, 0), sun=(0, 0)),
        "radiant": dict(head_r=(16, -28), pot=(31, 0), sun=(0, 0)),
        "soft": dict(head_r=(18, -30), pot=(34, 0), sun=(0, 0))}

# attachments per clip: (prop, anchor, start_frame, behind)
ATT = {
 "emo_hungry": [("sweat", "head_r", 0, False)], "emo_wantplay": [("question", "head_r", 0, False)],
 "emo_sleepy": [("zzz", "head_r", 0, False)], "emo_cuddly": [("heart", "head_r", 0, False)],
 "emo_surprised": [("exclaim", "head_r", 0, False)],
 "fall_asleep": [("zzz", "head_r", 1, False)], "sleep_loop": [("zzz", "head_r", 0, False)],
 "sunbathe": [("sun_patch", "sun", 0, True)],
 "pot_bump": [("flowerpot_idle", "pot", 0, False), ("flowerpot_bump", "pot", 3, False)],
 "droop": [("sweat", "head_r", 3, False)],
}

# ------------------------------------------------------------ atlas
def next_pow2(n):
    p = 1
    while p < n: p *= 2
    return p

def make_atlas(items, out_png, out_json, anims, meta_extra, maxw=1024, pad=2, pivots=None):
    """items: [(name, uint8 array)]; shelf-pack; pad 2, extrude 1. Returns (W,H,pos)"""
    order = sorted(items, key=lambda t: (-t[1].shape[0], t[0]))
    x = y = pad; rowh = 0; pos = {}
    for name, a in order:
        h, w = a.shape
        if x + w + pad > maxw: x = pad; y += rowh + pad; rowh = 0
        pos[name] = (x, y, w, h); x += w + pad; rowh = max(rowh, h)
    H = next_pow2(y + rowh + pad)
    W = maxw if True else maxw
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    jf = {}
    for name, a in items:
        x, y, w, h = pos[name]; im = to_img(a); e = np.array(im)
        img.paste(im, (x, y))
        img.paste(Image.fromarray(e[:1], "RGBA"), (x, y - 1)); img.paste(Image.fromarray(e[-1:], "RGBA"), (x, y + h))
        img.paste(Image.fromarray(e[:, :1], "RGBA"), (x - 1, y)); img.paste(Image.fromarray(e[:, -1:], "RGBA"), (x + w, y))
        piv = (pivots or {}).get(name, (w / 2, h - 3))
        jf[name] = {"frame": {"x": x, "y": y, "w": w, "h": h}, "rotated": False, "trimmed": False,
                    "spriteSourceSize": {"x": 0, "y": 0, "w": w, "h": h}, "sourceSize": {"w": w, "h": h},
                    "pivot": {"x": round(piv[0] / w, 4), "y": round(piv[1] / h, 4)}, "pivotPx": {"x": piv[0], "y": piv[1]}}
    img.save(out_png)
    meta = {"image": os.path.basename(out_png), "size": {"w": W, "h": H}, "scale": 1, "format": "RGBA8888", "padding": pad, "extrude": 1}
    meta.update(meta_extra)
    json.dump({"frames": jf, "animations": anims, "meta": meta}, open(out_json, "w"), indent=1, ensure_ascii=False)
    return W, H, pos

# ------------------------------------------------------------ previews
def compose(form, clip, i, A, P, scale=8, canvas_w=None):
    S = FORMS[form]["S"]
    CW = canvas_w or S
    TOP = 14
    m = Image.new("RGBA", (CW, S + 8 + TOP), BG)
    px = (CW - S) // 2 if canvas_w is None else (S // 2)  # pet left-ish if wide
    pet = A[clip][i]
    pivx, pivy = S // 2, S - 3
    atts = ATT.get(clip, [])
    def paste_prop(att):
        name, anc, st, behind = att
        arrs, piv, fps, loop = A["_props"][name]
        n = len(arrs)
        if i < st: return
        k = (i - st) % n if loop else min(i - st, n - 1)
        ox, oy = ANCH[form][anc]
        x = px + pivx + ox - piv[0]; y = TOP + pivy + oy - piv[1]
        m.alpha_composite(to_img(arrs[k]), (int(x), int(y)))
    for att in atts:
        if att[3]: paste_prop(att)
    m.alpha_composite(to_img(pet), (px, TOP))
    for att in atts:
        if not att[3]: paste_prop(att)
    return m.resize((CW * scale, (S + 8 + TOP) * scale), Image.NEAREST)

def save_gif(path, frames, fps, loops=1, hold_last_ms=0):
    seq = frames * loops
    pil = [f.convert("RGB").quantize(colors=64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for f in seq]
    dur = [int(1000 / fps)] * len(pil); dur[-1] += hold_last_ms
    pil[0].save(path, save_all=True, append_images=pil[1:], duration=dur, loop=0, disposal=1)

# ------------------------------------------------------------ main
def main():
    if os.path.isdir(OUT): shutil.rmtree(OUT)
    for d in ("frames", "layers", "props", "preview"):
        os.makedirs(os.path.join(OUT, d), exist_ok=True)
    shutil.copy(os.path.join(bt.OUT, "palette.json"), os.path.join(OUT, "palette.json"))
    props = build_props()
    stats = {}
    wide_clips = {"pot_bump"}
    allA = {}
    for form in ("sprout", "radiant", "soft"):
        S = FORMS[form]["S"]
        os.makedirs(os.path.join(OUT, "frames", form), exist_ok=True)
        os.makedirs(os.path.join(OUT, "layers", form), exist_ok=True)
        os.makedirs(os.path.join(OUT, "preview", form), exist_ok=True)
        C = clips(form)
        A = {"_props": props}
        for clip in ORDER:
            arrs = []
            for k, p in enumerate(C[clip], 1):
                if clip not in ("idle", "eat", "celebrate", "sick"):
                    p = render_fit(form, p, f"{clip}_{k:02d}")
                if clip in EMO:
                    full, body, ov = render_split(form, p)
                    to_img(body).save(os.path.join(OUT, "layers", form, f"{clip}_{k:02d}_noface.png"))
                    to_img(ov).save(os.path.join(OUT, "layers", form, f"{clip}_{k:02d}_overlay.png"))
                else:
                    full = render(form, p)
                arrs.append(full)
                to_img(full).save(os.path.join(OUT, "frames", form, f"{clip}_{k:02d}.png"))
            A[clip] = arrs
        allA[form] = A
        # atlas
        items = []; anims = {}
        for clip in ORDER:
            names = [f"{clip}_{k:02d}" for k in range(1, len(A[clip]) + 1)]
            for n, a in zip(names, A[clip]): items.append((n, a))
            fps, loop, lf, pr, intr = META[clip]
            d = {"frames": names, "fps": fps, "loop": loop}
            if loop and lf: d["loopFrom"] = lf
            if not loop and clip == "droop": pass
            anims[clip] = d
        W, H, pos = make_atlas(items, os.path.join(OUT, f"atlas_{form}.png"), os.path.join(OUT, f"atlas_{form}.json"), anims,
                               {"form": form, "frameSize": S, "pivotRule": "bottom-center (w/2, h-3)"})
        stats[form] = dict(frames=len(items), atlas=(W, H), clips={c: len(A[c]) for c in ORDER})
        # gifs
        for clip in ORDER:
            fps, loop, lf, pr, intr = META[clip]
            cw = int(S * 1.75) if clip in wide_clips else None
            fr = [compose(form, clip, i, A, props, 8, cw) for i in range(len(A[clip]))]
            save_gif(os.path.join(OUT, "preview", form, f"{clip}_8x.gif"), fr, fps, loops=(3 if len(fr) <= 4 else 2), hold_last_ms=300)
        # contact sheet (first + middle frame per clip), no text
        Z = 8 if S == 32 else 4
        cols = 8; cell = S * Z + 12
        sel = []
        for clip in ORDER:
            n = len(A[clip]); sel += [A[clip][0], A[clip][n // 2]]
        rows = math.ceil(len(sel) / cols)
        cs = Image.new("RGBA", (cols * cell + 12, rows * cell + 12), BG)
        for k, a in enumerate(sel):
            im = to_img(a).resize((S * Z, S * Z), Image.NEAREST)
            cs.alpha_composite(im, (12 + (k % cols) * cell, 12 + (k // cols) * cell))
        cs.save(os.path.join(OUT, f"contact_{form}.png"))
    # props atlas
    items = []; anims = {}; pivs = {}
    for name, (arrs, piv, fps, loop) in props.items():
        names = []
        for k, a in enumerate(arrs, 1):
            n = f"{name}_{k:02d}"; names.append(n); items.append((n, a)); pivs[n] = piv
            to_img(a).save(os.path.join(OUT, "props", n + ".png"))
        anims[name] = {"frames": names, "fps": fps, "loop": loop}
    make_atlas(items, os.path.join(OUT, "atlas_props.png"), os.path.join(OUT, "atlas_props.json"), anims,
               {"note": "per-frame pivot = pivotPx (prop pivot aligns to CLIPS anchor)"}, pivots=pivs)
    # prop gifs
    for name, (arrs, piv, fps, loop) in props.items():
        w = arrs[0].shape[1]; h = arrs[0].shape[0]
        fr = []
        for a in arrs:
            m = Image.new("RGBA", (w, h), BG); m.alpha_composite(to_img(a)); fr.append(m.resize((w * 8, h * 8), Image.NEAREST))
        save_gif(os.path.join(OUT, "props", f"{name}_8x.gif"), fr, fps, loops=4)
    stats["fit_adjustments"] = [f"{a}:{b}:{'/'.join(c)}" for a, b, c in FIT_LOG]
    json.dump({"stats": stats}, open(os.path.join(OUT, "_stats.json"), "w"), indent=1)
    write_clips_docs()
    print(json.dumps(stats, ensure_ascii=False)[:1500])

# ------------------------------------------------------------ docs: CLIPS.md / CLIPS.json (filled in docs module)
def write_clips_docs():
    try:
        import build_tuanrong_docs as D
        D.write(OUT, ORDER, META, ATT, ANCH, props_info={k: (len(v[0]), v[1], v[2], v[3], v[0][0].shape[1], v[0][0].shape[0]) for k, v in build_props().items()})
    except ImportError:
        print("docs module missing")

if __name__ == "__main__":
    main()
