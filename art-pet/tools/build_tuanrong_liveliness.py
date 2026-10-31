#!/usr/bin/env python3
"""build_tuanrong_liveliness.py — 團絨「生命感」精簡級（face rig + 新 clip）。
Pillow + numpy 程式逐像素繪製，原創，無 AI。只用 31 色盤、alpha 0/255、無抗鋸齒。
重用 build_tuanrong_motion.py renderer（唔改佢、唔覆蓋 motion/ 現有檔）。
輸出 -> ../sprites/tuanrong/motion/liveliness/
用法: python3 build_tuanrong_liveliness.py [--stage1]
"""
import json, math, os, shutil, sys, copy
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_tuanrong_motion as M
import build_tuanrong as bt
from build_tuanrong import IDX, FORMS, to_img

MOT = M.OUT
OUT = os.path.join(MOT, "liveliness")
BG = (92, 88, 128, 255)
FORM_LIST = ("sprout", "radiant", "soft")

# ============================================================ face kit (eyes / mouth / bulb)
GAZE = {"L": (-2, 0), "CL": (-1, 0), "C": (0, 0), "CR": (1, 0), "R": (2, 0), "U": (0, -1), "D": (0, 1)}
MOVING = ["neutral", "surprised", "squint", "angry", "sad"]
CLOSED = ["happy", "sleepy", "wink"]
EYE_STYLES = ["neutral", "happy", "surprised", "sleepy", "squint", "wink", "angry", "sad"]
MOUTH_STYLES = EYE_STYLES

# left-eye templates: (tl relative to eye anchor, rows, brow pixels)  '#' outline, 'w' cream4 highlight
EYE_T = {
 True: {
  "neutral":   ((-2, -2), [".##.", "#w##", "####", "####", ".##."], []),
  "surprised": ((-2, -3), [".###.", "#ww##", "#w###", "#####", "#####", ".###."], []),
  "squint":    ((-2, -1), ["####", "#w##", ".##."], []),
  "angry":     ((-2, -2), ["#...", "###.", "#w##", "####", ".##."], [(-3, -4), (-2, -4), (-1, -3), (0, -3), (1, -2)]),
  "sad":       ((-2, -2), ["...#", ".###", "#ww#", "####", ".##."], [(-3, -2), (-2, -3), (-1, -3), (0, -4), (1, -4)]),
  "happy":     ((-2, -1), ["..#..", ".#.#.", "#...#"], []),
  "sleepy":    ((-2, 0), ["#...#", ".###."], []),
  "wink":      ((-2, -2), ["#...", ".#..", "..##", ".#..", "#..."], []),
 },
 False: {
  "neutral":   ((-1, -1), ["##", "w#", "##"], []),
  "surprised": ((-1, -1), ["###", "w##", "###"], []),
  "squint":    ((-1, 0), ["##", "w#"], []),
  "angry":     ((-1, -1), ["#.", "w#", "##"], [(-2, -3), (-1, -3), (0, -2)]),
  "sad":       ((-1, -1), [".#", "w#", "##"], [(-2, -2), (-1, -3), (0, -3)]),
  "happy":     ((-1, -1), [".#.", "#.#"], []),
  "sleepy":    ((-1, 0), ["#.#", ".#."], []),
  "wink":      ((-1, -1), ["#.", ".#", "#."], []),
 }}
# mouth: (tl relative to mouth anchor, rows)  '#' outline 'r' blush_d 'p' blush
MOUTH_T = {
 True: {
  "neutral":   ((-2, 0), ["#...#", ".###."]),
  "happy":     ((-3, 0), ["#######", "#rrrrr#", ".#rrr#.", "..###.."]),
  "surprised": ((-2, 0), [".###.", "#rrr#", "#rrr#", ".###."]),
  "sleepy":    ((-1, 0), [".#.", "#r#", ".#."]),
  "squint":    ((-3, 0), ["#..#..#", ".##.##."]),
  "wink":      ((-2, 0), ["#...#", ".###.", ".#p#.", "..#.."]),
  "angry":     ((-3, 0), [".#.#.#.", "#.#.#.#"]),
  "sad":       ((-2, 0), [".###.", "#...#"]),
 },
 False: {
  "neutral":   ((-1, 0), ["#.#", ".#."]),
  "happy":     ((-1, 0), ["###", "#r#", ".#."]),
  "surprised": ((-1, 0), [".#.", "#r#", ".#."]),
  "sleepy":    ((0, 0), ["##"]),
  "squint":    ((-2, 0), ["#.#.#", ".#.#."]),
  "wink":      ((-1, 0), ["#.#", ".#.", ".p."]),
  "angry":     ((-2, 0), [".#.#.", "#.#.#"]),
  "sad":       ((-1, 0), [".#.", "#.#"]),
 }}
CMAP = {"#": "outline", "w": "cream4", "r": "blush_d", "p": "blush"}

def eye_pixels(big, style, side, gaze):
    (tx, ty), rows, brow = EYE_T[big][style]
    w = len(rows[0]); h = len(rows)
    gx, gy = GAZE[gaze]
    px = {}
    hl = [(i, j) for j, r in enumerate(rows) for i, ch in enumerate(r) if ch == "w"]
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch == ".": continue
            ii = i if side == "l" else (w - 1 - i)
            px[(tx + ii + gx, ty + j + gy)] = "outline"
    # highlight keeps light-from-upper-left on both eyes
    for (i, j) in hl:
        k = (tx + i + gx, ty + j + gy)
        if k in px: px[k] = "cream4"
    for (bx, by) in brow:
        bxx = bx if side == "l" else (2 * tx + w - 1 - bx)
        px[(bxx, by)] = "outline"
    return px

def mouth_pixels(big, style):
    (tx, ty), rows = MOUTH_T[big][style]
    return {(tx + i, ty + j): CMAP[ch] for j, r in enumerate(rows) for i, ch in enumerate(r) if ch != "."}

def bulb_pixels(form):
    """(base, glow) dict offsets relative to bulb anchor. base = fixed palette; glow = light layer for engine tint"""
    base, glow = {}, {}
    if form == "sprout":
        rows = [".ggg.", "gmmmg", "gmcmg", "gmmmg", ".ggg."]
        for j, r in enumerate(rows):
            for i, ch in enumerate(r):
                if ch == "g": base[(i - 2, j - 2)] = "glow"
                elif ch == "m": glow[(i - 2, j - 2)] = "cream4"
                elif ch == "c": glow[(i - 2, j - 2)] = "white"
    else:
        rr = 4.4 if form == "radiant" else 2.6
        ro = rr + (1.4 if form == "radiant" else 0.9)
        rc = rr - 1.4 if form == "radiant" else 1.3
        R = int(math.ceil(ro)) + 1
        for y in range(-R, R + 1):
            for x in range(-R, R + 1):
                d = math.hypot(x, y)
                if d <= rc: glow[(x, y)] = "white"
                elif d <= rr: glow[(x, y)] = "cream4"
                elif d <= ro: base[(x, y)] = "glow"
    return base, glow

def piece_arr(pxmap, bbox):
    x0, y0, x1, y1 = bbox
    a = np.zeros((y1 - y0 + 1, x1 - x0 + 1), np.uint8)
    for (x, y), c in pxmap.items(): a[y - y0, x - x0] = IDX[c]
    return a, (-x0, -y0)

def bbox_of(maps):
    xs = [x for m in maps for (x, y) in m]; ys = [y for m in maps for (x, y) in m]
    return min(xs), min(ys), max(xs), max(ys)

def build_kit(form):
    """returns dict name -> (arr, pivotPx(x,y)); uniform canvas per kind"""
    big = FORMS[form]["big"]
    eyes = {}
    for st in EYE_STYLES:
        for g in (GAZE if st in MOVING else ["C"]):
            for side in ("l", "r"):
                eyes[f"eyes_{st}_{g}_{side}"] = eye_pixels(big, st, side, g)
    bb = bbox_of(eyes.values())
    kit = {k: piece_arr(v, bb) for k, v in eyes.items()}
    mouths = {f"mouth_{st}": mouth_pixels(big, st) for st in MOUTH_STYLES}
    bb = bbox_of(mouths.values())
    kit.update({k: piece_arr(v, bb) for k, v in mouths.items()})
    b, g = bulb_pixels(form)
    bb = bbox_of([b, g])
    kit["bulb_base"] = piece_arr(b, bb); kit["bulb_glow"] = piece_arr(g, bb)
    return kit

# expression presets (brief's 8 + kit names)
PRESETS = {
 "neutral":   dict(eyes="neutral", gaze="C", mouth="neutral"),
 "happy":     dict(eyes="happy", gaze="C", mouth="happy"),
 "sleepy":    dict(eyes="sleepy", gaze="C", mouth="sleepy"),
 "surprised": dict(eyes="surprised", gaze="C", mouth="surprised"),
 "hungry":    dict(eyes="sad", gaze="D", mouth="wink", prop="sweat"),
 "cuddly":    dict(eyes="squint", gaze="C", mouth="squint", prop="heart"),
 "grumpy":    dict(eyes="angry", gaze="C", mouth="angry"),
 "curious":   dict(eyes="neutral", gaze="U", mouth="sleepy", prop="question"),
 "wink":      dict(eyes="neutral", gaze="C", eyesR="wink", mouth="wink"),
}
BULB_TINT = {  # engine multiply tint for bulb_glow layer (white->tint), intensity = brightness / alpha of glow
 "happy":   dict(tint="#FFD45E", intensity=1.0, pulse="1.2s 呼吸 0.85–1.0", palettePreview=["glow_core", "glow_warm"]),
 "neutral": dict(tint="#FFEFC4", intensity=0.8, pulse="無", palettePreview=["cream3", "cream2"]),
 "sleepy":  dict(tint="#8F85C2", intensity=0.55, pulse="3s 慢呼吸 0.4–0.6", palettePreview=["zzz", "zzz"]),
 "hungry":  dict(tint="#F2A65A", intensity=0.75, pulse="閃爍 0.8s（0.6–0.8）", palettePreview=["glow", "orange"]),
 "grumpy":  dict(tint="#E5584D", intensity=0.85, pulse="0.4s 跳兩下", palettePreview=["blush", "berry"]),
}
OLD_EYE = {"open": "neutral", "happy": "happy", "sleep": "sleepy", "blink": "sleepy", "half": "squint", "wide": "surprised",
           "shine": "surprised", "sick": "sick(保留原幀)", "none": "none"}
OLD_MOUTH = {"smile": "neutral", "open": "happy", "o": "surprised", "flat": "sleepy", "frown": "sad", "yawn": "surprised",
             "cat": "squint", "none": "none"}

# ============================================================ anchors (frame-local px, top-left origin)
HEAD_K = {}
def _geo(form, p):
    f = FORMS[form]; S = f["S"]; big = f["big"]
    sx, sy = p.get("sx", 1.0), p.get("sy", 1.0)
    rx, ry = f["rx"] * sx, f["ry"] * sy
    lift = p.get("lift", 0.0)
    cx = S / 2 + p.get("dx", 0.0)
    bottom = f["G"] - 1.0 - lift
    cy = bottom - ry
    return f, S, big, rx, ry, cx, cy

def _shear_x(form, p, y):
    sh = p.get("shear", 0)
    if not sh: return 0
    S = FORMS[form]["S"]; y0 = S - 3; ref = FORMS[form]["ry"] * 2.0
    return 0 if y >= y0 else int(round(sh * (y0 - y) / ref))

def anchors(form, p, face_visible=True):
    f, S, big, rx, ry, cx, cy = _geo(form, p)
    fdx, fdy = p.get("fdx", 0), p.get("fdy", 0)
    turn = p.get("ft", 0.0) * rx
    ey = cy + ry * 0.08
    eoff = rx * (0.40 if big else 0.42) * p.get("feoff", 1.0)
    out = {}
    for nm, sg in (("eyeL", -1), ("eyeR", 1)):
        ecx = cx + sg * eoff + fdx + turn; eyy = ey + fdy
        if big: ax, ay = int(round(ecx - 2)) + 2, int(round(eyy - 2.5)) + 2
        else:   ax, ay = int(round(ecx - 1)) + 1, int(round(eyy - 1.5)) + 1
        out[nm] = [ax + _shear_x(form, p, ay), ay]
    my = ey + ry * 0.38 + fdy; mcx = cx + fdx + turn
    if big: ax, ay = int(round(mcx - 2.5)) + 2, int(round(my - 1))
    else:   ax, ay = int(round(mcx - 1.5)) + 1, int(round(my - 1))
    out["mouth"] = [ax + _shear_x(form, p, ay), ay]
    kx, ky = HEAD_K[form]
    hx, hy = int(round(cx + kx * rx)), int(round(cy - ky * ry))
    out["head_r"] = [hx + _shear_x(form, p, hy), hy]
    # bulb (bud centre) — mirrors bt.render_pet stem math
    top = cy - ry; sy0 = int(round(top)) + 1
    stem_h = max(2, f["stem"] + p.get("stem_d", 0))
    droop = p.get("droop", 0); sway = p.get("sway", 0)
    tx = cx + sway + droop * 2; ty = sy0 - stem_h + droop * 1.5
    if form == "sprout": bx, by = int(round(tx)), int(round(ty - 2.5))
    elif form == "radiant": bx, by = int(round(tx)), int(round(ty - 2))
    else: bx, by = int(round(tx)), int(round(ty - 2.6))
    out["bulb"] = [bx + _shear_x(form, p, by), by]
    out["faceVisible"] = bool(face_visible)
    return out

def init_head_k():
    for form in FORM_LIST:
        f = FORMS[form]; hx, hy = M.ANCH[form]["head_r"]
        _, S, big, rx, ry, cx, cy = _geo(form, {})
        pivx, pivy = S // 2, S - 3
        HEAD_K[form] = ((pivx + hx - cx) / rx, (cy - (pivy + hy)) / ry)

# ============================================================ hanging (picked_up) helpers
def grab_point(form, p):
    """head-top pickup point (frame px): body-ellipse top centre, just at the sprout stem base"""
    f, S, big, rx, ry, cx, cy = _geo(form, p)
    return [int(math.floor(cx)), int(round(cy - ry))]

def _pend_dx(y, gy, ref, amt):
    return 0 if (not amt or y <= gy) else int(round(amt * (y - gy) / ref))

def pend_shear(a, form, p):
    """pendulum sway about the grab point: rows below grab shift by amt*(y-gy)/ref (feet move amt px)"""
    amt = p.get("pend", 0)
    if not amt: return a
    S = a.shape[0]; gy = grab_point(form, p)[1]; ref = (S - 3) - gy
    out = np.zeros_like(a)
    for y in range(S):
        sh = _pend_dx(y, gy, ref, amt)
        if sh == 0: out[y] = a[y]
        elif sh > 0: out[y, sh:] = a[y, :-sh]
        else: out[y, :sh] = a[y, -sh:]
    return out

def pend_anchors(form, p, an):
    gx, gy = grab_point(form, p); amt = p.get("pend", 0); S = FORMS[form]["S"]; ref = (S - 3) - gy
    for key in ("eyeL", "eyeR", "mouth", "head_r", "bulb"):
        x, y = an[key]; an[key] = [x + _pend_dx(y, gy, ref, amt), y]
    an["grab"] = [gx, gy]
    return an

def body_render(form, p):
    q = dict(p); q.pop("pend", None)
    return pend_shear(M.render(form, noface_params(q)), form, p)

# ============================================================ extra body drawing for new clips
def _ring(m):
    d = np.zeros_like(m); d[1:, :] |= m[:-1, :]; d[:-1, :] |= m[1:, :]; d[:, 1:] |= m[:, :-1]; d[:, :-1] |= m[:, 1:]
    return d & ~m

def ex_arm(form, side, ang, behind=False, reach=1.0):
    big = FORMS[form]["big"]
    def f(cv, cx, cy, rx, ry):
        ramp = bt.RAMPS[FORMS[form]["ramp"]]; col, hi = ramp[2], ramp[3]
        a = math.radians(ang)
        sx0, sy0 = cx + side * rx * 0.80, cy - ry * 0.02
        L = (5.0 if big else 2.8) * reach
        ar, pr = (2.5, 2.3) if big else (1.6, 1.5)
        px, py = sx0 + side * math.cos(a) * L, sy0 + math.sin(a) * L
        m = cv.ell(sx0, sy0, ar, ar) | cv.ell((sx0 + px) / 2, (sy0 + py) / 2, (ar + pr) / 2, (ar + pr) / 2) | cv.ell(px, py, pr, pr)
        rg = _ring(m)
        if behind:
            empty = cv.a == 0
            cv.a[m & empty] = IDX[col]; cv.a[rg & empty] = IDX["outline"]
        else:
            cv.a[rg] = IDX["outline"]; cv.a[m] = IDX[col]
            cv.put(px - side * 0.6, py - pr * 0.4, hi)
    return f

def ex_down_arm_behind(form, side):
    big = FORMS[form]["big"]
    def f(cv, cx, cy, rx, ry):
        ramp = bt.RAMPS[FORMS[form]["ramp"]]
        ar = 2.3 if big else 1.6
        m = cv.ell(cx + side * (rx - 0.2), cy + ry * 0.2, ar, ar)
        empty = cv.a == 0
        cv.a[m & empty] = IDX[bt.ramp_color(FORMS[form]["ramp"], 0.2, bt.TH)]
        cv.a[_ring(m) & empty] = IDX["outline"]
    return f

def ex_speed(form, n):
    big = FORMS[form]["big"]
    def f(cv, cx, cy, rx, ry):
        rows = [(-0.45, 6), (0.05, 9), (0.5, 5)] if big else [(-0.3, 3), (0.3, 2)]
        for k, (fy, ln) in enumerate(rows):
            ln = max(1, ln - ((n + k) % 3))
            y = int(round(cy + fy * ry)); xe = int(round(cx - rx - 2))
            for x in range(max(1, xe - ln), xe):
                if 0 <= y < cv.n and cv.a[y, x] == 0: cv.a[y, x] = IDX["white"]
    return f

def ex_spray(form, k):
    big = FORMS[form]["big"]
    def f(cv, cx, cy, rx, ry):
        my = cy + ry * 0.40
        if big: pts = [(0, -2, "drop"), (2, 0, "white"), (3, -3, "white"), (2, 2, "drop"), (5, -1, "drop")] if k == 0 else [(4, -3, "white"), (6, 1, "drop"), (7, -1, "white")]
        else: pts = [(1, -1, "drop"), (2, 1, "white")] if k == 0 else [(3, 0, "white")]
        for dx, dy, c in pts:
            x, y = int(round(cx + rx + 1 + dx)), int(round(my + dy))
            if 1 <= x < cv.n - 1 and 1 <= y < cv.n and cv.a[y, x] == 0: cv.put(x, y, c)
    return f

def ex_swirl(form):
    big = FORMS[form]["big"]
    def f(cv, cx, cy, rx, ry):
        ramp = bt.RAMPS[FORMS[form]["ramp"]]
        rows = [".##.", "#..#", "..#.", ".#.."] if big else [".#.", "#.#", "..#"]
        dark = "peach0" if form == "soft" else "cream0"
        x0, y0 = int(round(cx - len(rows[0]) / 2)), int(round(cy - ry * 0.25))
        for j, r in enumerate(rows):
            for i, ch in enumerate(r):
                if ch == "#" and cv.a[y0 + j, x0 + i] not in (0, IDX["outline"]): cv.a[y0 + j, x0 + i] = IDX[dark]
        # back of feet tuft / little tail
        tx, ty = int(round(cx)), int(round(cy + ry * 0.62))
        for (ox, oy) in (((0, 0), (1, 0), (-1, 0), (0, 1)) if big else ((0, 0),)):
            if cv.a[ty + oy, tx + ox] not in (0, IDX["outline"]): cv.put(tx + ox, ty + oy, ramp[3])
    return f

def ex_dust(form, k):
    big = FORMS[form]["big"]
    def f(cv, cx, cy, rx, ry):
        G = FORMS[form]["G"] - 1
        pts = ([(-rx - 2, -1), (-rx - 4, -3), (-rx - 1, -4)] if k == 0 else [(-rx - 5, -2), (-rx - 3, -5)]) if big else ([(-rx - 1, -1)] if k == 0 else [(-rx - 2, -2)])
        for dx, dy in pts:
            x, y = int(round(cx + dx)), int(round(G + dy))
            if 1 <= x < cv.n - 1 and 0 <= y < cv.n and cv.a[y, x] == 0: cv.put(x, y, "cream3")
    return f

def ex_legs(form, flift, feet_in):
    """little dangling leg stubs joining body bottom to the hanging feet (picked_up)"""
    big = FORMS[form]["big"]
    def f(cv, cx, cy, rx, ry):
        bottom = cy + ry; fx = rx * 0.45; foot_ry = 1.5 if big else 1.0
        lw = 2 if big else 1
        leg = np.zeros_like(cv.a, bool)
        for sgn, fl in ((-1, flift[0]), (1, flift[1])):
            fcx = cx + sgn * fx * (1 - feet_in); fcy = bottom + foot_ry * 0.1 + 0.2 - fl
            x0 = int(math.floor(fcx - lw / 2 + 0.5))
            for y in range(int(round(bottom - 2)), int(round(fcy))):
                for x in range(x0, x0 + lw):
                    if 0 <= y < cv.n and 0 <= x < cv.n and cv.a[y, x] in (0, IDX["outline"]): leg[y, x] = True
        cv.a[leg] = IDX["orange_d"]
        rg = _ring(leg) & (cv.a == 0)
        cv.a[rg] = IDX["outline"]
    return f

# ============================================================ new clips
F = lambda e, g="C", m="neutral", eR=None: dict(eyes=e, gaze=g, mouth=m, **({"eyesR": eR} if eR else {}))

def new_clips(form):
    big = FORMS[form]["big"]; u = 2 if big else 1; j = 4 if big else 2
    C = {}; FACE = {}; VIS = {}
    # A3 walk_happy: two hops per cycle (contact squash -> rise -> peak) x2, net dx 0
    WH = []; fc = []
    DXW = [-1, 0, 1, 1, 0, -1]
    for k in range(6):
        i = k % 3; right = k >= 3
        sy = [.88, 1.08, 1.03][i]; sx = [1.10, .94, .97][i]; lift = [0, max(1, j // 2), j][i]
        fl = [(0, 0), (u, u), (u, u)][i]
        WH.append(dict(sx=sx, sy=sy, lift=lift, flift=fl, feet_in=[0, .2, .3][i], shear=u, dx=DXW[k], fdx=u,
                       sway=(-u if i == 1 else (u if i == 2 else 0)), bud=[1.0, 1.15, 1.25][i], arms=("upx" if i == 2 else "down"),
                       fluff=k * .5, twinkle=k))
        fc.append(F("happy", "C", "happy") if i != 0 else F("happy", "C", "neutral"))
    C["walk_happy"] = WH; FACE["walk_happy"] = fc
    # A3 walk_drag: low, slow, droopy bud, feet scuffing
    WD = []; fc = []
    for k in range(6):
        i = k % 3; right = k >= 3
        fl = [(0, 0), (1, 0), (0, 0)][i]
        if right: fl = (fl[1], fl[0])
        WD.append(dict(sx=[1.08, 1.06, 1.07][i], sy=[.88, .91, .90][i], lift=0, flift=fl, feet_in=[.0, .1, .2][i],
                       shear=[0, u // 2, 0][i], dx=[0, 0, 1, 1, 0, 0][k] if big else 0, droop=1, bud=[.7, .65, .7][i],
                       fdy=1, fdx=u // 2, sway=[0, -u // 2, 0][i], fluff=k * .3,
                       extras=[ex_dust(form, 0)] if i == 1 else []))
        fc.append(F("sad", "D", "sleepy") if k not in (2, 5) else F("squint", "D", "sleepy"))
    C["walk_drag"] = WD; FACE["walk_drag"] = fc
    # A2 sniff: lean down to ground, two sniffs, back up happy
    C["sniff"] = [dict(sy=.93, sx=1.05, shear=u, fdx=u, fdy=1, bud=.9, sway=u),
                  dict(sy=.86, sx=1.10, shear=2 * u, fdx=u, fdy=2 if big else 1, bud=.85, sway=u, droop=1),
                  dict(sy=.88, sx=1.08, shear=2 * u, dx=1, fdx=u, fdy=1, bud=.9, sway=2 * u, droop=1, fluff=.8),
                  dict(sy=1.04, sx=.97, shear=0, bud=1.15, fluff=1.2)]
    FACE["sniff"] = [F("squint", "D", "neutral"), F("squint", "D", "sleepy"), F("happy", "C", "sleepy"), F("neutral", "CR", "neutral")]
    # A2 lookup: stretch up, gaze up, wonder
    C["lookup"] = [dict(sy=1.03, sx=.98, shear=-u, fdy=-1, sway=-u, bud=1.05),
                   dict(sy=1.08, sx=.95, shear=-u, fdy=-1, sway=-u, bud=1.2, twinkle=1, arms="upx"),
                   dict(sy=1.07, sx=.96, shear=-u, fdy=-1, sway=-2 * u if big else -u, bud=1.25, twinkle=2, fluff=.6, arms="upx"),
                   dict(sy=1.0, sx=1.0, bud=1.05, twinkle=3)]
    FACE["lookup"] = [F("neutral", "U", "neutral"), F("surprised", "U", "surprised"), F("surprised", "U", "sleepy"), F("happy", "C", "neutral")]
    # A2 swat: spot bug -> wind up paw -> swipe -> proud
    LB = ex_down_arm_behind(form, -1)
    C["swat"] = [dict(sy=.95, sx=1.04, shear=-u, arms="none", extras=[LB, ex_arm(form, 1, -40, behind=True)], bud=1.0),
                 dict(sy=1.04, sx=.97, shear=-u, lift=1, arms="none", extras=[LB, ex_arm(form, 1, -95, reach=1.15)], bud=1.15),
                 dict(sy=.90, sx=1.08, shear=2 * u, dx=u, arms="none", extras=[LB, ex_arm(form, 1, 25, reach=1.25)], bud=1.1, sway=2 * u),
                 dict(sy=1.02, sx=.99, shear=u, arms="down", bud=1.05, sway=u)]
    FACE["swat"] = [F("surprised", "U", "neutral"), F("angry", "CR", "angry"), F("squint", "R", "angry"), F("happy", "C", "happy")]
    # B1 scratch: paw up behind head, quick scritches, relieved
    C["scratch"] = [dict(sy=.98, shear=-u, arms="none", extras=[LB, ex_arm(form, 1, -60)], bud=1.0, fdx=-1),
                    dict(sy=.97, shear=-u, sway=u, arms="none", extras=[LB, ex_arm(form, 1, -80, reach=1.1)], bud=1.05, fluff=.5, fdx=-1),
                    dict(sy=.97, shear=-2 * u if big else -u, sway=-u, arms="none", extras=[LB, ex_arm(form, 1, -58, reach=1.05)], bud=1.0, fluff=1.0, fdx=-1),
                    dict(sy=.97, shear=-u, sway=u, arms="none", extras=[LB, ex_arm(form, 1, -82, reach=1.1)], bud=1.05, fluff=1.5, fdx=-1),
                    dict(sy=.97, shear=-2 * u if big else -u, sway=-u, arms="none", extras=[LB, ex_arm(form, 1, -58, reach=1.05)], bud=1.0, fluff=2.0, fdx=-1),
                    dict(sy=.95, sx=1.04, bud=1.1, fluff=2.5)]
    FACE["scratch"] = [F("squint", "CL", "neutral"), F("squint", "CL", "squint"), F("happy", "C", "squint"), F("squint", "CL", "squint"), F("happy", "C", "squint"), F("happy", "C", "neutral")]
    # B2 sneeze: ah -> ahh -> CHOO -> rebound -> sniffle
    C["sneeze"] = [dict(sy=1.05, sx=.97, shear=-u, fdy=-1, bud=1.05, sway=-u),
                   dict(sy=1.10, sx=.94, shear=-2 * u if big else -u, fdy=-1, bud=1.15, sway=-u, lift=0),
                   dict(sy=.84, sx=1.12, shear=2 * u, dx=u, fdy=1, bud=1.3, sway=2 * u, extras=[ex_spray(form, 0)]),
                   dict(sy=1.02, sx=.99, shear=u, bud=1.1, sway=u, extras=[ex_spray(form, 1)]),
                   dict(sy=.98, sx=1.02, bud=1.0)]
    FACE["sneeze"] = [F("squint", "U", "surprised"), F("squint", "U", "surprised"), F("happy", "C", "happy"), F("squint", "C", "neutral"), F("neutral", "CL", "wink")]
    # D3 nuzzle: lean into finger on the right, rub up/down
    NZ = [(u, 0, .98, 0), (2 * u, -1, 1.02, u), (2 * u, 0, .96, u), (u, 1 if big else 0, .97, 0), (2 * u, -1, 1.02, u), (2 * u, 0, .95, 2 * u)]
    C["nuzzle"] = [dict(shear=sh, dx=u // 2 if big else 0, fdx=u, fdy=fy, sy=sy_, sx=2 - sy_, sway=sw, bud=1.1, fluff=k * .6, twinkle=k)
                   for k, (sh, fy, sy_, sw) in enumerate(NZ)]
    FACE["nuzzle"] = [F("squint", "CR", "squint"), F("happy", "C", "squint"), F("happy", "C", "squint"), F("squint", "CR", "squint"), F("happy", "C", "squint"), F("happy", "C", "happy")]
    # D5 rush: anticipate -> run (2..5 loopable) -> brake  -> cheer_jump
    C["rush"] = [dict(sy=.86, sx=1.10, shear=-u, bud=.95, sway=u),
                 dict(sy=1.04, sx=.95, shear=3 * u if big else 2, lift=u, flift=(u, 0), fdx=u, sway=-2 * u if big else -u, bud=1.15, extras=[ex_speed(form, 0)]),
                 dict(sy=.94, sx=1.04, shear=3 * u if big else 2, lift=0, flift=(0, u), fdx=u, sway=-2 * u if big else -u, bud=1.1, extras=[ex_speed(form, 1), ex_dust(form, 0)]),
                 dict(sy=1.04, sx=.95, shear=3 * u if big else 2, lift=u, flift=(0, u), fdx=u, sway=-2 * u if big else -u, bud=1.15, extras=[ex_speed(form, 2)]),
                 dict(sy=.94, sx=1.04, shear=3 * u if big else 2, lift=0, flift=(u, 0), fdx=u, sway=-2 * u if big else -u, bud=1.1, extras=[ex_speed(form, 3), ex_dust(form, 1)]),
                 dict(sy=.90, sx=1.08, shear=-u, dx=u, sway=2 * u, bud=1.2, extras=[ex_dust(form, 0)])]
    FACE["rush"] = [F("surprised", "R", "surprised"), F("happy", "C", "happy"), F("neutral", "R", "happy"), F("happy", "C", "happy"), F("neutral", "R", "happy"), F("surprised", "CR", "happy")]
    # D2 turn_back: back view -> 3/4 -> pop front -> settle
    C["turn_back"] = [dict(blush=False, sway=-u, bud=1.0, extras=[ex_swirl(form)]),
                      dict(blush=False, sx=.97, shear=u, ft=.33, feoff=.62, sway=-u, bud=1.05),
                      dict(sy=1.06, sx=.96, lift=u, bud=1.2, sway=u, arms="upx"),
                      dict(sy=.97, sx=1.03, bud=1.05)]
    FACE["turn_back"] = [None, F("neutral", "R", "neutral"), F("surprised", "C", "surprised"), F("happy", "C", "happy")]
    VIS["turn_back"] = [False, True, True, True]
    # D6 picked_up: pinched/held at head-top (grab anchor), body hangs & stretches a little,
    # feet dangle and kick alternately, whole body sways like a pendulum about the grab point.
    PU = []; fc = []
    A = 3 if big else 2                       # pendulum shift at feet (px)
    K = 2 if big else 1                       # foot kick height (px)
    LIFT = 3 if big else 1                    # body raised so dangling feet have room
    for k in range(6):
        ph = 2 * math.pi * k / 6
        pend = ([1, 3, 1, -1, -3, -1] if big else [1, 2, 1, -1, -2, -1])[k]   # triangle swing, even steps
        kl = ([2, 2, 1, 0, 0, 1] if big else [1, 1, 0, 0, 0, 0])[k]   # left foot kick (px up)
        kr = ([0, 0, 1, 2, 2, 1] if big else [0, 0, 0, 1, 1, 0])[k]   # right foot kick, alternating
        bob = [0, 1, 0, 0, 1, 0][k]           # tiny stretch bounce (hanging "boing")
        fl = (kl - LIFT, kr - LIFT)
        PU.append(dict(sy=1.06 + 0.02 * bob, sx=0.95 - 0.02 * bob, lift=LIFT, flift=fl, feet_in=0.18,
                       arms="down", bud=1.0, sway=(-1 if pend > 1 else (1 if pend < -1 else 0)), fluff=k * .4, twinkle=k, pend=pend,
                       extras=[ex_legs(form, fl, 0.18)]))
        fc.append(F("happy", "C", "happy"))
    C["picked_up"] = PU; FACE["picked_up"] = fc
    if not big:
        for cn in C:
            for p_ in C[cn]:
                if p_.get("lift", 0) > 0: p_["bud"] = min(p_.get("bud", 1.0), 1.0)
    return C, FACE, VIS

NEW_ORDER = ["walk_happy", "walk_drag", "sniff", "lookup", "swat", "scratch", "sneeze", "nuzzle", "rush", "turn_back", "picked_up"]
PIVOT_OVERRIDE = {"picked_up": "grab"}      # clip pivot = anchors[k].grab instead of foot pivot (w/2, h-3)
FACE_ON_ENTER = {"picked_up": dict(eyes="surprised", gaze="D", mouth="surprised", loops=1,
                                   note="第一個循環（≈0.75s）用 surprised（gaze D 望地下），之後轉 happy（預設幀表情）；放低前可換 neutral/sad 自由")}
# fps, loop, loopFrom, priority, interruptible, cooldown, next, category, item, trigger, notes
NEW_META = {
 "walk_happy": (10, True, 0, 2, True, 0, "idle", "A3 心情步姿", "walk 嘅替身：心情 ≥ 70（或 emo_happy 後 10 秒內）時 walk 改播 walk_happy",
                "蹦跳步，每循環 2 跳；原地播，引擎移 x（建議每循環 ≈14px／64px、7px／32px，比 walk 快 15%）。可配腳步塵 G3。"),
 "walk_drag": (6, True, 0, 2, True, 0, "idle", "A3 心情步姿", "walk 嘅替身：精力 < 40 或飽腹 < 40 時 walk 改播 walk_drag",
               "拖步：矮身、光芽垂低、第 2／5 幀腳邊起塵。引擎位移 ≈ walk 嘅 60%。"),
 "sniff": (6, False, 0, 2, True, 25, "idle", "A2 中途停低", "walk 途中每段 15% 機率停低（3 款 A2 平均抽）；或行經花盆／食物",
           "低頭嗅地兩下再抬頭；第 2–3 幀可配 0.3s 嗅嗅音效。"),
 "lookup": (5, False, 0, 2, True, 25, "idle", "A2 中途停低", "同上；夜晚／有螢火／流星事件時權重 ×3",
            "抬頭望天；第 2–3 幀可 hold 0.8s（引擎延長）；配 gaze U。"),
 "swat": (8, False, 0, 2, False, 40, "idle", "A2 中途停低", "同上；或場景有蟲仔／螢火 fx 飛近 head_r 範圍",
          "撥走蟲仔：第 3 幀（索引 2）出手判定；蟲仔 fx 由引擎（可用螢火 icon）。"),
 "scratch": (8, False, 0, 1, True, 600, "idle", "B1 抓癢", "idle 變化抽籤（權重 12）；同一小動作 ≥10 分鐘唔重複",
             "後爪去頭頂抓 2 下；第 2–5 幀可重播 1 次；表情舒服瞇眼。"),
 "sneeze": (8, False, 0, 1, False, 600, "idle", "B2 打噴嚏", "idle 變化抽籤（權重 8）；靠近花盆／曬太陽後機率 ×2；冷天 ×1.5",
            "第 3 幀（索引 2）乞嗤（噴霧點烙入幀）；可配音效；之後 30% 接 emo_surprised。"),
 "nuzzle": (6, True, 0, 4, True, 0, "idle", "D3 長按蹭手", "長按寵物 ≥0.4s 持續；手指喺寵物右邊（左邊用 scaleX −1）",
            "向右挨埋手指上下磨蹭；鬆手後播完當前幀回 idle；掛 heart（head_r）；取代 emo_cuddly 作長按版。"),
 "rush": (12, False, 0, 6, False, 0, "cheer_jump", "D5 久未見衝埋嚟", "開 app 時離線 ≥6h（每日最多 1 次）",
          "第 1 幀起步；第 2–5 幀（loopRange [1,4]）跑步循環直至到達玩家前位置；第 6 幀煞停 → 接 cheer_jump。速度線同塵烙入幀。"),
 "picked_up": (8, True, 0, 7, False, 0, "idle", "D6 被拎起（浮動團絨）", "Android 浮動寵物：手指按住寵物頭頂拖動／長按拎起（拖曳開始）時播；直至放手",
               "pivot＝anchors.grab（頭頂拎點），唔係腳底 pivot：引擎將 grab 對準手指位置。身體吊住微拉長、成個以 grab 為軸左右擺（鐘擺 shear）、兩隻腳交替輕踢。第一個循環建議 surprised（faceOnEnter），之後 happy。放手 → 引擎跌落／彈返地面再接 idle（或 emo_surprised）。可按拖動速度改 fps 6–12。"),
 "turn_back": (8, False, 0, 4, False, 0, "emo_happy", "D2 點一下回頭", "寵物背向／行緊路時被點一下；或 walk 中被點",
               "第 1 幀背面（faceVisible=false，唔好疊五官）、第 2 幀 3/4 側（眼距收窄）、第 3 幀轉正彈起、第 4 幀定。之後按心情接 emo_happy（心情≥50）或 emo_surprised。"),
}

# ============================================================ helpers
def frame_list(form):
    """yield (clip, k, p_final, face_default, visible, is_new) for every clip/frame"""
    C = M.clips(form)
    for clip in M.ORDER:
        for k, p in enumerate(C[clip], 1):
            if clip not in ("idle", "eat", "celebrate", "sick"): p = M.render_fit(form, p, f"{clip}_{k:02d}")
            eo = p.get("eyes", "open"); mo = p.get("mouth", "smile")
            yield clip, k, p, dict(eyes=OLD_EYE.get(eo, eo), gaze="C", mouth=OLD_MOUTH.get(mo, mo), src=f"{eo}/{mo}"), True, False

def noface_params(p):
    q = dict(p); q["eyes"] = "none"; q["mouth"] = "none"
    q["extras"] = [e for e in p.get("extras", []) if not getattr(e, "face", False)]
    return q

def place(canvas, arr, ax, ay, piv):
    """paste palette-index piece into canvas at anchor (in-place); clips at border"""
    h, w = arr.shape; x0, y0 = ax - piv[0], ay - piv[1]
    for yy in range(h):
        for xx in range(w):
            c = arr[yy, xx]
            if c and 0 <= y0 + yy < canvas.shape[0] and 0 <= x0 + xx < canvas.shape[1]:
                canvas[y0 + yy, x0 + xx] = c

def compose_face(body, anc, face, kit, bulb_mood=None):
    a = body.copy()
    if face is None or not anc["faceVisible"]:
        pass
    else:
        g = face.get("gaze", "C"); eL = face["eyes"]; eR = face.get("eyesR", eL)
        def ename(st, side):
            gg = g if st in MOVING else "C"
            return f"eyes_{st}_{gg}_{side}"
        for nm, st, side in (("eyeL", eL, "l"), ("eyeR", eR, "r")):
            arr, piv = kit[ename(st, side)]; place(a, arr, anc[nm][0], anc[nm][1], piv)
        arr, piv = kit["mouth_" + face["mouth"]]; place(a, arr, anc["mouth"][0], anc["mouth"][1], piv)
    if bulb_mood:
        arr, piv = kit["bulb_base"]; place(a, arr, anc["bulb"][0], anc["bulb"][1], piv)
        arr, piv = kit["bulb_glow"]; core, mid = BULB_TINT[bulb_mood]["palettePreview"]
        t = arr.copy(); t[arr == IDX["white"]] = IDX[core]; t[arr == IDX["cream4"]] = IDX[mid]
        place(a, t, anc["bulb"][0], anc["bulb"][1], piv)
    return a

def next_pow2(n):
    p = 1
    while p < n: p *= 2
    return p

def pack_pages(items, maxw=1024, maxh=1024, pad=2):
    """shelf pack into >=1 pages. items [(name, arr, pivot)] -> list of pages [(W,H,{name:(x,y,w,h)})]"""
    order = sorted(items, key=lambda t: (-t[1].shape[0], t[0]))
    pages = []; cur = {}; x = y = pad; rowh = 0
    for name, a, _ in order:
        h, w = a.shape
        if x + w + pad > maxw: x = pad; y += rowh + pad; rowh = 0
        if y + h + pad > maxh:
            pages.append(cur); cur = {}; x = y = pad; rowh = 0
        cur[name] = (x, y, w, h); x += w + pad; rowh = max(rowh, h)
    pages.append(cur)
    out = []
    for pg in pages:
        H = next_pow2(max(y + h for (x, y, w, h) in pg.values()) + pad)
        out.append((maxw, H, pg))
    return out

def write_atlas(form, items, anims, tag_meta):
    pages = pack_pages(items)
    lut = {n: (a, piv) for n, a, piv in items}
    files = []
    for pi, (W, H, pos) in enumerate(pages):
        suf = "" if len(pages) == 1 else "_" + "abcdefgh"[pi]
        png = os.path.join(OUT, f"atlas_{form}_live{suf}.png")
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); jf = {}
        for name, (x, y, w, h) in pos.items():
            a, piv = lut[name]; im = to_img(a); e = np.array(im)
            img.paste(im, (x, y))
            img.paste(Image.fromarray(e[:1], "RGBA"), (x, y - 1)); img.paste(Image.fromarray(e[-1:], "RGBA"), (x, y + h))
            img.paste(Image.fromarray(e[:, :1], "RGBA"), (x - 1, y)); img.paste(Image.fromarray(e[:, -1:], "RGBA"), (x + w, y))
            jf[name] = {"frame": {"x": x, "y": y, "w": w, "h": h}, "rotated": False, "trimmed": False,
                        "spriteSourceSize": {"x": 0, "y": 0, "w": w, "h": h}, "sourceSize": {"w": w, "h": h},
                        "pivot": {"x": round(piv[0] / w, 4), "y": round(piv[1] / h, 4)}, "pivotPx": {"x": piv[0], "y": piv[1]}}
        img.save(png)
        meta = {"image": os.path.basename(png), "size": {"w": W, "h": H}, "scale": 1, "format": "RGBA8888", "padding": 2, "extrude": 1}
        meta.update(tag_meta)
        my_anims = {k: v for k, v in anims.items() if all(f in pos for f in v["frames"])}
        json.dump({"frames": jf, "animations": my_anims, "meta": meta}, open(png.replace(".png", ".json"), "w"), indent=1, ensure_ascii=False)
        files.append(os.path.basename(png))
    return files

def save_gif(path, frames, fps, loops=2, hold_last_ms=0, durs=None):
    seq = frames * loops
    pil = [f.convert("RGB").quantize(colors=64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for f in seq]
    dur = (durs * loops) if durs else [int(1000 / fps)] * len(pil); dur[-1] += hold_last_ms
    pil[0].save(path, save_all=True, append_images=pil[1:], duration=dur, loop=0, disposal=1)

def big_img(a, Z, bg=BG, pad=0):
    S = a.shape[0]
    m = Image.new("RGBA", (a.shape[1] + 2 * pad, S + 2 * pad), bg); m.alpha_composite(to_img(a), (pad, pad))
    return m.resize((m.width * Z, m.height * Z), Image.NEAREST)

# ============================================================ main build
def build(stage1=False):
    init_head_k()
    os.makedirs(OUT, exist_ok=True)
    result = {"forms": {}}
    anchors_all = {}
    for form in FORM_LIST:
        S = FORMS[form]["S"]; piv = (S // 2, S - 3)
        for d in ("layers", "frames", "preview"):
            os.makedirs(os.path.join(OUT, d, form), exist_ok=True)
        kit = build_kit(form)
        clips = {}   # clip -> dict(noface=[], full=[], overlay=[], anchors=[], new=bool)
        # existing clips
        for clip, k, p, face, vis, _ in frame_list(form):
            if stage1 and clip not in ("idle", "walk"): continue
            full = M.render(form, p); body = M.render(form, noface_params(p))
            ov = np.where(full != body, full, 0).astype(np.uint8)
            an = anchors(form, p, vis); an["face"] = face
            c = clips.setdefault(clip, dict(noface=[], full=[], overlay=[], anchors=[], new=False))
            c["noface"].append(body); c["full"].append(full); c["overlay"].append(ov); c["anchors"].append(an)
        if not stage1:
            C, FACE, VIS = new_clips(form)
            for clip in NEW_ORDER:
                c = clips.setdefault(clip, dict(noface=[], full=[], overlay=[], anchors=[], new=True))
                for k, p in enumerate(C[clip]):
                    p = M.render_fit(form, p, f"{clip}_{k + 1:02d}")
                    body = body_render(form, p)
                    vis = VIS.get(clip, [True] * 99)[k]
                    an = anchors(form, p, vis)
                    if clip in PIVOT_OVERRIDE: an = pend_anchors(form, p, an)
                    face = FACE[clip][k]
                    an["face"] = dict(face) if face else None
                    full = compose_face(body, an, face, kit)
                    ov = np.where(full != body, full, 0).astype(np.uint8)
                    c["noface"].append(body); c["full"].append(full); c["overlay"].append(ov); c["anchors"].append(an)
        # write pngs
        for clip, c in clips.items():
            for k in range(len(c["noface"])):
                to_img(c["noface"][k]).save(os.path.join(OUT, "layers", form, f"{clip}_{k + 1:02d}_noface.png"))
                to_img(c["overlay"][k]).save(os.path.join(OUT, "layers", form, f"{clip}_{k + 1:02d}_faceov.png"))
                if c["new"]:
                    to_img(c["full"][k]).save(os.path.join(OUT, "frames", form, f"{clip}_{k + 1:02d}.png"))
        os.makedirs(os.path.join(OUT, "kit", form), exist_ok=True)
        for name, (a, pv) in kit.items():
            to_img(a).save(os.path.join(OUT, "kit", form, name + ".png"))
        # atlas
        items = []; anims = {}
        for clip, c in clips.items():
            fps = (NEW_META[clip][0] if c["new"] else M.META[clip][0]); loop = (NEW_META[clip][1] if c["new"] else M.META[clip][1])
            pv = (lambda k: tuple(c["anchors"][k][PIVOT_OVERRIDE[clip]])) if clip in PIVOT_OVERRIDE else (lambda k: piv)
            extra = {"pivot": PIVOT_OVERRIDE[clip]} if clip in PIVOT_OVERRIDE else {}
            nf = [f"{clip}_noface_{k + 1:02d}" for k in range(len(c["noface"]))]
            for k, (n, a) in enumerate(zip(nf, c["noface"])): items.append((n, a, pv(k)))
            anims[f"{clip}_noface"] = {"frames": nf, "fps": fps, "loop": loop, **extra}
            if c["new"]:
                ff = [f"{clip}_{k + 1:02d}" for k in range(len(c["full"]))]
                for k, (n, a) in enumerate(zip(ff, c["full"])): items.append((n, a, pv(k)))
                anims[clip] = {"frames": ff, "fps": fps, "loop": loop, **extra}
        for name, (a, pv) in kit.items(): items.append((name, a, pv))
        files = write_atlas(form, items, anims, {"form": form, "frameSize": S, "pivotRule": "body frames bottom-center (w/2, h-3); kit pieces pivotPx = anchor point; picked_up* frames pivotPx = anchors.grab (頭頂拎點，animation pivot=grab)",
                                                    "note": "團絨生命感：<clip>_noface 無臉身體、新 clip 完整幀、五官套 eyes_*/mouth_*、燈泡 bulb_base/bulb_glow"})
        anchors_all[form] = {clip: c["anchors"] for clip, c in clips.items()}
        result["forms"][form] = dict(clips=clips, kit=kit, atlas=files)
    # face_anchors.json (mirror of CLIPS.json anchors)
    fa = {"version": 1, "coords": "frame-local px, origin = frame top-left, y down (同 CLIPS.json anchors)",
          "pivotPx": {f: [FORMS[f]["S"] // 2, FORMS[f]["S"] - 3] for f in FORM_LIST},
          "keys": "eyeL/eyeR/mouth = 五官錨點（kit piece pivotPx 對準）; head_r = 頭頂右上圖示; bulb = 光芽燈泡中心; faceVisible=false 唔好疊五官; face = 呢幀預設表情（kit 名）; grab = 頭頂拎點（只 picked_up 有，亦係該 clip 嘅 pivot）",
          "pivotOverride": PIVOT_OVERRIDE,
          "anchors": anchors_all}
    json.dump(fa, open(os.path.join(OUT, "face_anchors.json"), "w"), ensure_ascii=False, indent=None, separators=(",", ":"))
    # pretty-ish: one frame per line
    txt = json.dumps(fa, ensure_ascii=False)
    with open(os.path.join(OUT, "face_anchors.json"), "w") as fh:
        fh.write('{"version":1,\n "coords":' + json.dumps(fa["coords"], ensure_ascii=False) + ',\n "pivotPx":' + json.dumps(fa["pivotPx"]) +
                 ',\n "keys":' + json.dumps(fa["keys"], ensure_ascii=False) + ',\n "pivotOverride":' + json.dumps(fa["pivotOverride"]) + ',\n "anchors":{\n')
        fl = []
        for form in FORM_LIST:
            cl = []
            for clip, lst in anchors_all[form].items():
                cl.append('   ' + json.dumps(clip) + ':[\n' + ',\n'.join('    ' + json.dumps(a, ensure_ascii=False, separators=(",", ":")) for a in lst) + ']')
            fl.append('  ' + json.dumps(form) + ':{\n' + ',\n'.join(cl) + '}')
        fh.write(',\n'.join(fl) + '}}\n')
    json.loads(open(os.path.join(OUT, "face_anchors.json")).read())
    return result

# ============================================================ previews
def previews(res, stage1=False):
    for form, R in res["forms"].items():
        S = FORMS[form]["S"]; kit = R["kit"]; clips = R["clips"]
        Z = 8
        pdir = os.path.join(OUT, "preview", form)
        # A1 walk gaze demo (walk noface + neutral eyes, gaze sweeps)
        seq = ["C", "CR", "R", "R", "CR", "C", "CL", "L", "L", "CL", "C", "U", "U", "C", "D", "C", "C", "C"]
        w = clips["walk"]; fr = []
        for i, g in enumerate(seq):
            k = i % 6
            fr.append(big_img(compose_face(w["noface"][k], w["anchors"][k], dict(eyes="neutral", gaze=g, mouth="neutral"), kit), Z, pad=2))
        save_gif(os.path.join(pdir, "A1_walk_gaze_8x.gif"), fr, 10, loops=2)
        if stage1:
            continue
        # every new clip with default face, + bulb mood
        for clip in NEW_ORDER:
            c = clips[clip]; fps = NEW_META[clip][0]
            fr = [big_img(c["full"][k], Z, pad=2) for k in range(len(c["full"]))]
            save_gif(os.path.join(pdir, f"{clip}_8x.gif"), fr, fps, loops=(3 if len(fr) <= 5 else 2), hold_last_ms=250)
        # picked_up: grab-aligned preview (pivot = grab fixed on screen), entry surprised loop -> happy loops; + strip
        pickup_preview(form, clips["picked_up"], kit, pdir)
        # G1 bulb moods on idle
        fr = []; durs = []
        for mood in BULB_TINT:
            face = {"happy": PRESETS["happy"], "neutral": PRESETS["neutral"], "sleepy": PRESETS["sleepy"], "hungry": PRESETS["hungry"], "grumpy": PRESETS["grumpy"]}[mood]
            for k in range(4):
                c = clips["idle"]
                fr.append(big_img(compose_face(c["noface"][k], c["anchors"][k], face, kit, bulb_mood=mood), Z, pad=2)); durs.append(170)
        save_gif(os.path.join(pdir, "G1_bulb_moods_8x.gif"), fr, 6, loops=1, durs=durs)
        # expression presets cycling on idle (8 expressions)
        fr = []; durs = []
        for nm in ["neutral", "happy", "sleepy", "surprised", "hungry", "cuddly", "grumpy", "curious", "wink"]:
            for k in range(4):
                c = clips["idle"]
                fr.append(big_img(compose_face(c["noface"][k], c["anchors"][k], PRESETS[nm], kit), Z, pad=2)); durs.append(160)
        save_gif(os.path.join(pdir, "face_presets_on_idle_8x.gif"), fr, 6, loops=1, durs=durs)
    if not stage1:
        contact_sheets(res)

def pickup_preview(form, c, kit, pdir, Z=8):
    S = FORMS[form]["S"]; n = len(c["noface"])
    gys = [c["anchors"][k]["grab"][1] for k in range(n)]
    W = S + 8
    gx0, gy0 = W // 2, 3 + max(gys)            # screen point the grab pivot is pinned to (whole sprite visible)
    H = gy0 + (S - min(gys)) + 3
    def frame(k, face, mark=True):
        a = compose_face(c["noface"][k], c["anchors"][k], face, kit)
        g = c["anchors"][k]["grab"]
        m = Image.new("RGBA", (W, H), BG); m.alpha_composite(to_img(a), (gx0 - g[0], gy0 - g[1]))
        if mark:   # preview-only marker (not an asset): red px = grab pivot pinned to the finger point
            m.putpixel((gx0, gy0), (255, 70, 70, 255))
        return m.resize((W * Z, H * Z), Image.NEAREST)
    sur = dict(FACE_ON_ENTER["picked_up"]); sur.pop("loops"); sur.pop("note")
    seq = [frame(k, sur) for k in range(n)] + [frame(k, c["anchors"][k]["face"]) for k in range(n)] * 2
    save_gif(os.path.join(pdir, "picked_up_grab_8x.gif"), seq, NEW_META["picked_up"][0], loops=2)
    row1 = [frame(k, c["anchors"][k]["face"]) for k in range(n)]; row2 = [frame(k, sur) for k in range(n)]
    row3 = [frame(k, None, mark=False) for k in range(n)]
    strip = Image.new("RGBA", (W * Z * n, H * Z * 3), BG)
    for r, row in enumerate((row1, row2, row3)):
        for k, im in enumerate(row): strip.paste(im, (k * W * Z, r * H * Z))
    strip.save(os.path.join(pdir, "picked_up_strip_8x.png"))

def contact_sheets(res):
    for form, R in res["forms"].items():
        S = FORMS[form]["S"]; kit = R["kit"]; clips = R["clips"]
        Z = 6 if S == 32 else 3; cell = S * Z + 8
        rows = []
        for clip in NEW_ORDER: rows.append([clips[clip]["full"][k] for k in range(len(clips[clip]["full"]))])
        idle = clips["idle"]
        rows.append([compose_face(idle["noface"][0], idle["anchors"][0], PRESETS[n], kit) for n in ["neutral", "happy", "sleepy", "surprised", "hungry", "cuddly", "grumpy", "curious"]])
        rows.append([compose_face(idle["noface"][0], idle["anchors"][0], dict(eyes="neutral", gaze=g, mouth="neutral"), kit) for g in ["L", "CL", "C", "CR", "R", "U", "D"]] +
                    [compose_face(idle["noface"][0], idle["anchors"][0], PRESETS["wink"], kit)])
        rows.append([compose_face(idle["noface"][0], idle["anchors"][0], PRESETS["neutral"], kit, bulb_mood=m) for m in BULB_TINT] +
                    [clips[c]["noface"][0] for c in ("idle", "walk", "sunbathe")])
        rows.append([clips[c]["noface"][len(clips[c]["noface"]) // 2] for c in ("emo_happy", "play", "sleep_loop", "pot_bump", "catch_reach", "droop", "eat", "sick")])
        cols = 8
        W = cols * cell + 8; H = len(rows) * cell + 8
        img = Image.new("RGBA", (W, H), BG)
        for r, row in enumerate(rows):
            for c, a in enumerate(row):
                img.alpha_composite(to_img(a).resize((S * Z, S * Z), Image.NEAREST), (8 + c * cell, 8 + r * cell))
        img.save(os.path.join(OUT, f"contact_{form}_liveliness.png"))
        # kit sheet (8x)
        names = list(kit.keys()); Zk = 8
        mw = max(a.shape[1] for a, _ in kit.values()); mh = max(a.shape[0] for a, _ in kit.values())
        cw, ch = mw * Zk + 8, mh * Zk + 8; cols = 14
        img = Image.new("RGBA", (cols * cw + 8, math.ceil(len(names) / cols) * ch + 8), (200, 190, 170, 255))
        for i, n in enumerate(names):
            a, pv = kit[n]
            img.alpha_composite(to_img(a).resize((a.shape[1] * Zk, a.shape[0] * Zk), Image.NEAREST), (8 + (i % cols) * cw, 8 + (i // cols) * ch))
        img.save(os.path.join(OUT, f"kit_{form}_8x.png"))

if __name__ == "__main__":
    st1 = "--stage1" in sys.argv
    res = build(stage1=st1)
    previews(res, stage1=st1)
    print("ok", {f: {c: len(v["noface"]) for c, v in R["clips"].items()} for f, R in res["forms"].items()})
    print("fit", M.FIT_LOG[-20:])
