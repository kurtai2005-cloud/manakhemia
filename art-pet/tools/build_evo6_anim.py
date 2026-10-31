#!/usr/bin/env python3
"""build_evo6_anim.py — 團絨 6 階段進化 batch A 動畫：1 光卵 evo_egg 24、2 絨點 evo_dot 28、3 絨芽 evo_sprout 32、4 絨跳 evo_hop 38。
外觀＝evo6_concept v3「lumi feel」（build_evo6_concept.py 嘅 lf* 畫法：bump 毛球＋4 級 ramp＋肚＋tick＋高光＋1px 描邊＋4×5/4×4 豆眼）。
姿勢＝現有形態同名 clip（build_tuanrong_motion.clips std23 ＋ build_tuanrong_liveliness.new_clips s1/s2）——只換外觀層，
所以 timing／fps／priority 同 sprout/radiant/soft 一樣。光卵冇 face rig（同舊蛋）：idle 4、glow 2、tap 4、hatch 6、picked_up 4。
Pillow＋numpy 程式逐像素繪製，原創，無 AI。基本 31 色色盤（sprites/tuanrong/palette.json）、alpha 0/255、無 AA、向右。
每幀：完整幀、_noface、_faceov、emissive（白＝glow_core/glow_mid）、錨點 {eyeL,eyeR,mouth,head_r,bulb*,faceVisible,face,grab*}
（*bulb 只限絨跳＝第一粒著燈；grab 只限 picked_up）。face kit 按新尺寸重出（絨點/絨芽 4×4 豆眼 S 級、絨跳 4×5 L 級）。
atlas：每形態一張 1024 闊、padding 2、extrude 1、每幀 pivotPx；emissive atlas 同 layout。
CLIPS.json／CLIPS.md 只「加」evo_* 段（冪等），唔郁現有形態。
輸出：sprites/tuanrong/evo6/…、sprites/tuanrong/preview/evo6/…
用法：python3 build_evo6_anim.py
"""
import json, math, os, shutil, sys
import numpy as np
import scipy.ndimage as ndi
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_tuanrong as bt
import build_tuanrong_motion as M
import build_tuanrong_liveliness as L
import build_evo6_concept as EC
from build_tuanrong import FORMS, IDX

ROOT = os.path.normpath(os.path.join(HERE, ".."))                       # art-pet/
TR = bt.OUT                                                             # sprites/tuanrong
OUT = os.path.join(TR, "evo6")
PRV = os.path.join(TR, "preview", "evo6")
MOT = M.OUT
BACK = os.path.join(ROOT, "_backups", "pre_evo6_animA_20261031")
BG = (92, 88, 128, 255)
RGB = EC.pal_rgb("base")
EMIS = sorted(IDX[n] for n in ("glow_core", "glow_mid"))
CMX = {"#": "outline", "w": "cream4", "r": "blush_d", "t": "blush", "p": "blush"}

# ============================================================ forms (FORMS entries drive all shared pose / anchor helpers)
EVO = {
 "evo_dot":    dict(S=28, rx=8.6, ry=7.4, G=26, ramp="cream_hi", N=10, rb=1.7, big=False, stem=0,
                    name="絨點", stage=2, tier="S", fdx0=1, fdy0=-1.2, eo=0.46, br=(1.5, 0.9), nt=3, body_up=2.6,
                    arm=1.3, feet=None, headk=(0.92, 0.95), pot=20, my_off=-1.0),
 "evo_sprout": dict(S=32, rx=10.4, ry=8.8, G=29, ramp="cream", N=12, rb=max(1.8, 3.4 * 10.4 / 19), big=False, stem=3,
                    name="絨芽", stage=3, tier="S", fdx0=1, fdy0=0.0, eo=0.40, br=(1.6, 0.9), nt=4, body_up=0.0,
                    arm=1.7, feet=(2.0, 1.6), headk=(0.88, 0.62), pot=21),
 "evo_hop":    dict(S=38, rx=11.6, ry=9.8, G=35, ramp="cream", N=13, rb=3.4 * 11.6 / 19, big=False, stem=4,
                    name="絨跳", stage=4, tier="L", fdx0=1, fdy0=0.0, eo=0.40, br=(2.0, 1.1), nt=5, body_up=0.0,
                    arm=1.9, feet=(2.2, 1.8), headk=(1.02, 0.80), pot=23),
}
FORMS.update(EVO)
FORM_IDS = ["evo_egg", "evo_dot", "evo_sprout", "evo_hop"]
BODY_FORMS = ["evo_dot", "evo_sprout", "evo_hop"]
for fid in BODY_FORMS:
    bt.RAMPS["sun_" + fid] = list(bt.RAMPS["sun_radiant" if fid == "evo_dot" else "sun_sprout"])
for k, v in bt.RAMPS.items(): EC.RAMP.setdefault(k, v)

# ---- L._geo: 絨點個身坐高 body_up（坐喺半個蛋殼入面；ground/pivot 仍係殼底）
_orig_geo = L._geo
def _geo(form, p):
    f, S, big, rx, ry, cx, cy = _orig_geo(form, p)
    return f, S, big, rx, ry, cx, cy - f.get("body_up", 0.0)
L._geo = _geo

# ============================================================ face templates (old-clip renderer set + kit set)
EYE_TPL = {
 "S": {"open": [".##.", "#w##", "####", ".##."], "blink": ["####"], "happy": [".##.", "#..#"], "sleep": ["#..#", ".##."],
       "sickL": ["#..", ".##", "#.."], "sickR": ["..#", "##.", "..#"], "none": [], "half": ["####", "#w##", ".##."],
       "wide": [".##.", "#w##", "####", "####", ".##."], "shine": [".##.", "#ww#", "####", ".##."]},
 "L": bt.EYE[True],
}
MOUTH_TPL = {
 "S": {"smile": ["#..#", ".##."], "open": ["####", "#rr#", ".##."], "flat": [".##."], "frown": [".##.", "#..#"],
       "o": [".##.", "#rr#", ".##."], "none": [], "yawn": [".###.", "#rrr#", "#rtr#", ".###."], "cat": ["#.##.#", ".#..#."]},
 "L": bt.MOUTH[True],
}
L.EYE_T["S"] = {
 "neutral": ((-2, -2), [".##.", "#w##", "####", ".##."], []),
 "surprised": ((-2, -3), [".##.", "#ww#", "#w##", "####", ".##."], []),
 "squint": ((-2, -1), ["####", "#w##", ".##."], []),
 "angry": ((-2, -2), ["#...", "###.", "#w##", ".##."], [(-3, -4), (-2, -4), (-1, -3), (0, -3)]),
 "sad": ((-2, -2), ["...#", ".###", "#ww#", ".##."], [(-3, -3), (-2, -3), (-1, -4), (0, -4)]),
 "happy": ((-2, -1), [".##.", "#..#"], []),
 "sleepy": ((-2, 0), ["#..#", ".##."], []),
 "wink": ((-2, -1), ["##..", "..##", "##.."], []),
}
L.MOUTH_T["S"] = {
 "neutral": ((-2, 0), ["#..#", ".##."]),
 "happy": ((-2, 0), ["####", "#rr#", ".##."]),
 "surprised": ((-2, 0), [".##.", "#rr#", ".##."]),
 "sleepy": ((-1, 0), ["##", "##"]),
 "squint": ((-3, 0), ["#.##.#", ".#..#."]),
 "wink": ((-2, 0), ["#..#", ".##.", ".pp."]),
 "angry": ((-3, 0), [".#..#.", "#.##.#"]),
 "sad": ((-2, 0), [".##.", "#..#"]),
}
L.EYE_T["L"] = L.EYE_T[True]; L.MOUTH_T["L"] = L.MOUTH_T[True]

def face_geo(form, cx, cy, rx, ry):
    """shared by renderer, anchors, brow/cheek extras: face centre x, eye y, eye offset, mouth y, blush xy"""
    f = FORMS[form]; ho = len(EYE_TPL[f["tier"]]["open"])
    fcx = cx + f["fdx0"]; ey = cy + ry * 0.08 + f["fdy0"]; eoff = rx * f["eo"]
    my = max(ey + ry * 0.38, ey + ho / 2 + 1.5) + f.get("my_off", 0.0)   # 絨點：嘴上移 1px，唔黐殼邊
    bx = max(rx * 0.62, eoff + 2.6); by = max(ey + ry * 0.26, ey + ho / 2 + 0.6)
    return fcx, ey, eoff, my, bx, by, ho

# ---- face extras used by M.clips (brow / cheeks) → follow the lf face geometry
CUR = [None]
_orig_brow, _orig_cheeks = M.ex_brow, M.ex_cheeks
def ex_brow_evo(big, kind="worry"):
    form = CUR[0]
    if form not in EVO: return _orig_brow(big, kind)
    L_ = FORMS[form]["tier"] == "L"
    pts = [(-2, 0), (-1, 0), (0, -1), (1, -1)] if L_ else [(-1, 0), (0, 0), (1, -1)]
    def fn(cv, cx, cy, rx, ry):
        fcx, ey, eoff, my, bx, by, ho = face_geo(form, cx, cy, rx, ry)
        top = int(round(ey + M.FACE[1] - ho / 2))
        byy = top - (2 if L_ else 1)
        for sgn in (-1, 1):
            ex = fcx + sgn * eoff + M.FACE[0] + 0.5 * (1 if L_ else 0)
            for u, dy in pts:
                cv.put(ex - sgn * u, byy + dy, "outline")
    fn.face = True
    return fn
def ex_cheeks_evo(big):
    form = CUR[0]
    if form not in EVO: return _orig_cheeks(big)
    def fn(cv, cx, cy, rx, ry):
        fcx, ey, eoff, my, bx, by, ho = face_geo(form, cx, cy, rx, ry); brx, bry = FORMS[form]["br"]
        for sgn in (-1, 1):
            m = cv.ell(fcx + sgn * bx + M.FACE[0], by + M.FACE[1], brx + 0.8, bry + 0.5)
            cv.a[m & cv.solid & (cv.a != IDX["outline"])] = IDX["blush"]
            cv.put(fcx + sgn * bx + M.FACE[0], by + M.FACE[1], "blush_d")
    fn.face = True
    return fn
M.ex_brow, M.ex_cheeks = ex_brow_evo, ex_cheeks_evo

# ---- 絨點仲未有腳：picked_up 嘅吊腳仔 → 唔畫（殼黐住個尾跟住吊）
_orig_legs = L.ex_legs
def ex_legs_evo(form, flift, feet_in):
    if form == "evo_dot":
        def nop(cv, cx, cy, rx, ry): pass
        return nop
    return _orig_legs(form, flift, feet_in)
L.ex_legs = ex_legs_evo

# ============================================================ body renderer (pose-aware lf*)
def shade(cv, m, cx, cy, rx, ry, ramp, bias=0.15):
    return EC.shade(cv, m, cx, cy, rx, ry, ramp, bias)

def stem_pts(cx, top, ln, lean, sway, droop):
    pts = []; sy0 = int(round(top)) + 1
    for j in range(ln + 1):
        t = j / max(1, ln)
        pts.append((cx + lean * t * t + sway * t + droop * t * t * 2, sy0 - j + droop * t * t * 1.5))
    return pts

def put_stem(cv, pts, cols):
    for (px, py) in pts:
        x, y = int(round(px)), int(round(py))
        cv.put(x, y, cols[0]); cv.solid[min(max(y, 0), cv.n - 1), min(max(x, 0), cv.n - 1)] = True

TUFT = ((0, 0), (1, 0), (0, -1), (1, -1), (1, -2), (2, -2), (2, -3), (1, -4), (0, -4), (-1, -4), (-1, -3), (0, -3))
TUFT_FLOP = ((0, 0), (1, 0), (0, -1), (1, -1), (2, -1), (3, -1), (3, 0), (4, 0), (4, 1))

def hop_bud_geo(form, p, cx, cy, rx, ry):
    f = FORMS[form]; ln = max(2, f["stem"] + p.get("stem_d", 0))
    pts = stem_pts(cx, cy - ry, ln, 0.6, p.get("sway", 0), p.get("droop", 0))
    tx, ty = pts[-1]
    return pts, (tx + 0.5, ty - 2.2)

def render_evo(form, p):
    f = FORMS[form]; S = f["S"]; cv = bt.Cv(S)
    sick = p.get("sick", False); ramp = "sick" if sick else f["ramp"]; R = bt.RAMPS[ramp]
    _, _, _, rx, ry, cx, cy = L._geo(form, p)
    lift = p.get("lift", 0.0); ground = f["G"] - 1.0 - lift; bottom = cy + ry
    sway = p.get("sway", 0); droop = p.get("droop", 0); bud = p.get("bud", 1.0); ph = p.get("fluff", 0.0); tw = p.get("twinkle", 0)
    dot, spr, hop = form == "evo_dot", form == "evo_sprout", form == "evo_hop"
    tipc = "sick0" if sick else "orange"
    # ---- behind: tail + ears (絨跳)
    if hop:
        r = 3.2; wag = 0.6 * math.sin(ph * 2.0)
        tx, ty = cx - rx - 0.4, cy + 1.5 - wag
        m = cv.ell(tx, ty, r, r * 0.9) | cv.ell(tx - r * 0.6, ty - r * 0.8, r * 0.7, r * 0.7)
        shade(cv, m, tx, ty, r, r, ramp); cv.solid |= m
        cv.paint(cv.ell(tx - r * 0.75, ty - r * 1.05, r * 0.5, r * 0.5) & m, tipc)
        perk = 0.6 if bud > 1.1 else 0.0
        for s in (-1, 1):
            EC.ear(cv, cx + s * rx * 0.56, cy - ry * 0.70 + droop * 0.8, 6.5 - droop * 1.6 + perk, 5.0, s * (1.8 + droop * 1.6), (R[1], tipc))
    # ---- feet
    if f["feet"]:
        frx, fry = f["feet"]; fi = p.get("feet_in", 0.0); fl = p.get("flift", (0, 0))
        for i, s in enumerate((-1, 1)):
            m = cv.ell(cx + s * rx * 0.45 * (1 - fi), ground + 0.35 - fl[i], frx, fry); cv.paint(m, "orange"); cv.solid |= m
            cv.paint(m & (cv.yy >= int(ground + 0.6 - fl[i])), "orange_d")
    # ---- arms
    arms = p.get("arms", "down")
    if arms != "none" and not (dot and arms == "down"):
        ar = f["arm"]
        for s in (-1, 1):
            if arms == "down": ax, ay = cx + s * (rx - 0.2), cy + ry * 0.2
            elif arms == "up": ax, ay = cx + s * (rx - 0.4), cy - ry * 0.35 - 1
            else: ax, ay = cx + s * (rx - 0.6), cy + ry * (0.1 if s < 0 else 0.0)
            m = cv.ell(ax, ay, ar, ar); cv.paint(m, R[2]); cv.solid |= m
    # ---- body (lf_body + fluff wobble)
    bm = cv.ell(cx, cy, rx, ry); N, rb = f["N"], f["rb"]
    for i in range(N):
        th = 2 * math.pi * (i + 0.5) / N; sn = math.sin(th)
        if sn > 0.78: continue
        if sn < -0.8 and abs(math.cos(th)) < 0.35: continue
        wob = 0.3 * math.sin(ph * 2 + min(i, N - 1 - i) * 1.3)
        r_b = rb * (1 + 0.08 * math.cos(2 * th))
        bm |= cv.ell(cx + (rx - r_b * 0.45 + wob) * math.cos(th), cy + (ry - r_b * 0.45 + wob) * sn, r_b, r_b)
    kk = shade(cv, bm, cx, cy, rx, ry, ramp, 0.15)
    cv.a[cv.ell(cx, cy + ry * 0.32, rx * 0.55, ry * 0.5) & bm & (kk <= 1)] = IDX[R[2]]
    for (tx_, ty_) in EC.LF_TICKS[:f["nt"]]:
        px, py = cx + tx_ * rx * 0.95, cy + ty_ * ry * 0.95
        cv.put(px, py, R[0]); cv.put(px + 1, py + 1, R[0])
    cv.solid |= bm
    if not sick: EC.lf_hi(cv, cx, cy, rx, ry, big=False)
    # ---- head features (solid, outlined together)
    bud_c = None
    if dot:
        tx, ty = cx + 0.5, cy - ry + 0.5
        pat = TUFT_FLOP if droop > 0.5 else TUFT
        if droop > 0.5: ty += 1
        for (dx, dy) in pat:
            off = int(round(sway * (-dy) / 4 * 0.7)) if dy <= -2 else 0
            x, y = int(tx + dx + off), int(ty + dy)
            if 0 <= x < S and 0 <= y < S: cv.a[y, x] = IDX["sick1" if sick else "cream3"]; cv.solid[y, x] = True
    if spr:
        ln = max(2, f["stem"] + p.get("stem_d", 0))
        pts = stem_pts(cx, cy - ry, ln, 0.5, sway, droop); put_stem(cv, pts, ("sick0" if sick else "leaf_d",))
        tx, ty = pts[-1]; lc, ld = ("sick1", "sick0") if sick else ("leaf", "leaf_d")
        perk = 1.0 if bud > 1.05 else 0.0; dr = min(1.0, droop)
        EC.leaf(cv, tx - 2.4 + dr * 0.4, ty - 0.8 + dr * 1.4 - perk * 0.4, 2.8, 1.5, 155 + 40 * dr - 12 * perk, lc, ld)
        EC.leaf(cv, tx + 2.6 - dr * 0.4, ty - 1.4 + dr * 1.8 - perk * 0.4, 3.0, 1.6, 30 - 45 * dr + 12 * perk, lc, ld)
    if hop:
        pts, bud_c = hop_bud_geo(form, p, cx, cy, rx, ry)
        put_stem(cv, pts, ("sick0" if sick else "orange",))
        tx, ty = pts[-1]; lc, ld = ("sick1", "sick0") if sick else ("leaf", "leaf_d")
        EC.leaf(cv, tx - 2.2, ty + 1.4 + droop * 0.6, 2.2, 1.1, 160 + 30 * min(1.0, droop), lc, ld)
    cv.outline()
    # ---- 絨點 half egg shell (on top of body bottom)
    if dot:
        G = ground; xo = int(round(p.get("dx", 0.0)))
        top = G - 5 + np.minimum(np.abs(((cv.xx - xo) % 6) - 3), 2)
        srx = f["rx"] * (0.55 + 0.45 * p.get("sx", 1.0)) + 1.4
        sh = bt.egg_mask(cv, cx, G - 4.4, srx, 5.2) & (cv.yy >= top) & (cv.yy <= G)
        shade(cv, sh, cx, G - 4, srx - 0.4, 5, "shell", 0.25)
        cv.a[EC.ring(sh) & (cv.yy <= G + 1)] = IDX["outline"]
        cv.solid |= sh | (EC.ring(sh) & (cv.yy <= G + 1))
        for x in (cx - 4, cx + 4): cv.put(x, G - 3, "cream4")
        cv.put(cx - 5, G - 2, "glow_warm")
    # ---- face (old-clip templates; FACE offset via patched bt.draw_tmpl_c)
    fcx, ey, eoff, my, bx, by, ho = face_geo(form, cx, cy, rx, ry)
    ET, MT = EYE_TPL[f["tier"]], MOUTH_TPL[f["tier"]]
    eyes = p.get("eyes", "open"); mouth = p.get("mouth", "smile")
    if eyes == "sick":
        bt.draw_tmpl_c(cv, fcx - eoff, ey, ET["sickL"], CMX); bt.draw_tmpl_c(cv, fcx + eoff, ey, ET["sickR"], CMX)
    elif eyes != "none":
        for s in (-1, 1): bt.draw_tmpl_c(cv, fcx + s * eoff, ey, ET[eyes], CMX)
    if mouth != "none": bt.draw_tmpl_c(cv, fcx, my, MT[mouth], CMX)
    if p.get("blush", True):
        brx, bry = f["br"]
        for s in (-1, 1):
            m = cv.ell(fcx + s * bx + M.FACE[0], by + M.FACE[1], brx, bry)
            cv.a[m & bm & (cv.a != IDX["outline"])] = IDX["sick0" if sick else "blush"]
    # ---- 絨跳 glow bud (first lit bulb) + twinkle
    if hop:
        bx_, by_ = bud_c
        if sick:
            m = cv.ell(bx_, by_, 1.7, 1.7); cv.paint(m, "sick1"); cv.put(bx_ - 0.5, by_ - 0.5, "cream2"); EC.outl(cv, cv.ell(bx_, by_, 1.7, 1.7))
        else:
            r = 2.0 * (0.92 + 0.08 * min(bud, 1.4))
            m = cv.ell(bx_, by_, r + 0.9, r + 0.9); cv.paint(m, "glow")
            inner = cv.ell(bx_, by_, r, r)
            if bud < 0.8:
                cv.paint(inner, "glow"); cv.put(bx_ - 0.5, by_ - 0.5, "glow_mid")
            else:
                cv.paint(inner, "glow_mid")
                for (ox, oy) in ((-0.5, -0.5), (0.5, -0.5), (-0.5, 0.5)): cv.put(bx_ + ox, by_ + oy, "glow_core")
            cv.solid |= m
            EC.outl(cv, cv.ell(bx_, by_, r + 0.9, r + 0.9))
            if bud >= 1.0 and tw % 4 in (0, 1):
                sx_, sy_ = int(bx_ + 5), int(by_ - 2 - (tw % 2))
                if 2 <= sx_ <= S - 3 and 2 <= sy_ <= S - 3 and cv.a[sy_ - 1:sy_ + 2, sx_ - 1:sx_ + 2].max() == 0:
                    EC.sparkle(cv, sx_, sy_)
    a0 = cv.a.copy()
    for fx_ in p.get("extras", []): fx_(cv, cx, cy, rx, ry)
    return keep_fx_inside(a0, cv.a)

def keep_fx_inside(a0, a1):
    """extras（心心／星／汗…）出界 → 嗰一舊（8 連通）成舊向內推，唔掂 1px 邊；身體同其他 extras 唔郁"""
    d = (a1 != a0)
    if not d.any(): return a1
    S = a1.shape[0]; lab, n = ndi.label(d, structure=np.ones((3, 3), int)); out = a1.copy()
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        ox = (1 - xs.min() if xs.min() < 1 else 0) - (xs.max() - (S - 2) if xs.max() > S - 2 else 0)
        oy = (1 - ys.min() if ys.min() < 1 else 0) - (ys.max() - (S - 2) if ys.max() > S - 2 else 0)
        if not ox and not oy: continue
        out[ys, xs] = a0[ys, xs]
        out[ys + oy, xs + ox] = a1[ys, xs]
    return out

_orig_render_pet = bt.render_pet
def _render_pet(form, p):
    return render_evo(form, p) if form in EVO else _orig_render_pet(form, p)
bt.render_pet = _render_pet

for fid in BODY_FORMS:
    f = FORMS[fid]; _, S, _, rx, ry, cx, cy = L._geo(fid, {})
    L.HEAD_K[fid] = f["headk"]
    hx, hy = int(round(cx + f["headk"][0] * rx)), int(round(cy - f["headk"][1] * ry))
    M.ANCH[fid] = dict(head_r=(hx - S // 2, hy - (S - 3)), pot=(f["pot"], 0), sun=(0, 0))

# ---- lookup_tip / getup 後仰：RotSprite 式旋轉（Scale2x ×3 → 最近鄰旋轉 → 取格心），細 sprite 描邊唔會爛
def scale2x(a):
    p = np.pad(a, 1, mode="edge"); B, D, F, H = p[:-2, 1:-1], p[1:-1, :-2], p[1:-1, 2:], p[2:, 1:-1]; E = a
    o = np.zeros((a.shape[0] * 2, a.shape[1] * 2), a.dtype)
    o[0::2, 0::2] = np.where((D == B) & (B != F) & (D != H), D, E)
    o[0::2, 1::2] = np.where((B == F) & (B != D) & (F != H), F, E)
    o[1::2, 0::2] = np.where((D == H) & (D != B) & (H != F), D, E)
    o[1::2, 1::2] = np.where((H == F) & (D != H) & (B != F), F, E)
    return o
_orig_rot_arr = L.rot_arr
def rot_arr_evo(a, form, p):
    if form not in EVO: return _orig_rot_arr(a, form, p)
    deg = p.get("rot", 0)
    if not deg: return a
    big = scale2x(scale2x(scale2x(a))); K = 8
    th = math.radians(deg); px, py = L.rot_pivot(form, p); H, W = a.shape
    ys, xs = np.mgrid[0:H, 0:W].astype(float)
    dx, dy = xs + 0.5 - px, ys + 0.5 - py
    sx = px + dx * math.cos(th) - dy * math.sin(th); sy = py + dx * math.sin(th) + dy * math.cos(th)
    ix, iy = np.floor(sx * K).astype(int), np.floor(sy * K).astype(int)
    ok = (ix >= 0) & (ix < W * K) & (iy >= 0) & (iy < H * K)
    out = np.zeros_like(a); out[ok] = big[iy[ok], ix[ok]]
    return out
L.rot_arr = rot_arr_evo

def touches(a): return bool(a[0].any() or a[-1].any() or a[:, 0].any() or a[:, -1].any())

# ============================================================ anchors
def evo_anchors(form, p, vis=True):
    f, S, big, rx, ry, cx, cy = L._geo(form, p)
    fdx, fdy = p.get("fdx", 0), p.get("fdy", 0); turn = p.get("ft", 0.0) * rx
    fcx, ey, eoff, my, bx, by, ho = face_geo(form, cx, cy, rx, ry)
    eoff *= p.get("feoff", 1.0)
    op = EYE_TPL[f["tier"]]["open"]; wo = len(op[0])
    sm = MOUTH_TPL[f["tier"]]["smile"]; mw, mh = len(sm[0]), len(sm)
    out = {}
    for nm, sg in (("eyeL", -1), ("eyeR", 1)):
        ecx = (fcx + sg * eoff) + fdx + turn; eyy = ey + fdy
        ax, ay = int(round(ecx - wo / 2)) + 2, int(round(eyy - ho / 2)) + 2
        out[nm] = [ax + L._shear_x(form, p, ay), ay]
    mcx = fcx + fdx + turn; myy = my + fdy
    ax, ay = int(round(mcx - mw / 2)) + 2, int(round(myy - mh / 2))
    out["mouth"] = [ax + L._shear_x(form, p, ay), ay]
    kx, ky = L.HEAD_K[form]
    hx, hy = int(round(cx + kx * rx)), int(round(cy - ky * ry))
    out["head_r"] = [hx + L._shear_x(form, p, hy), hy]
    if form == "evo_hop":
        _, (bx_, by_) = hop_bud_geo(form, p, cx, cy, rx, ry)
        bx_, by_ = int(math.floor(bx_)), int(math.floor(by_))
        out["bulb"] = [bx_ + L._shear_x(form, p, by_), by_]
    out["faceVisible"] = bool(vis)
    return out

PT_KEYS = ("eyeL", "eyeR", "mouth", "head_r", "bulb")
def pend_rot(form, p, an, pick):
    if pick:
        gx, gy = L.grab_point(form, p); amt = p.get("pend", 0); S = FORMS[form]["S"]; ref = (S - 3) - gy
        for k in PT_KEYS:
            if k in an: x, y = an[k]; an[k] = [x + L._pend_dx(y, gy, ref, amt), y]
        an["grab"] = [gx, gy]
    if p.get("rot"):
        for k in PT_KEYS:
            if k in an: an[k] = list(L.rot_pt(form, p, *an[k]))
    return an

# ============================================================ face kit (re-exported at new sizes)
def build_kit(form):
    tier = FORMS[form]["tier"]; kit = {}
    eyes = {}
    for st in L.EYE_STYLES:
        for g in (L.GAZE if st in L.MOVING else ["C"]):
            for side in ("l", "r"): eyes[f"eyes_{st}_{g}_{side}"] = L.eye_pixels(tier, st, side, g)
    bb = L.bbox_of(eyes.values()); kit.update({k: L.piece_arr(v, bb) for k, v in eyes.items()})
    mouths = {f"mouth_{st}": L.mouth_pixels(tier, st) for st in L.MOUTH_STYLES}
    bb = L.bbox_of(mouths.values()); kit.update({k: L.piece_arr(v, bb) for k, v in mouths.items()})
    if form == "evo_hop":   # = soft-style glow bud at 2.0 radius (body render bulb r 2.0 + glow ring 0.9)
        base, glow = {}, {}
        for y in range(-4, 5):
            for x in range(-4, 5):
                d = math.hypot(x + 0.5, y + 0.5)          # anchor = floor(bud centre) → centre at +0.5
                if d <= 1.0: glow[(x, y)] = "white"
                elif d <= 2.0: glow[(x, y)] = "cream4"
                elif d <= 2.9: base[(x, y)] = "glow"
        bb = L.bbox_of([base, glow]); kit["bulb_base"] = L.piece_arr(base, bb); kit["bulb_glow"] = L.piece_arr(glow, bb)
    return kit

# ============================================================ build body forms
ORDER_STD = list(M.ORDER)
ORDER_NEW = list(L.NEW_ORDER)
def meta(clip):
    if clip in L.NEW_META: return tuple(L.NEW_META[clip][:5])
    return tuple(M.META[clip])

def build_form(form):
    CUR[0] = form
    C = M.clips(form)
    NC, NFACE, NVIS = L.new_clips(form)
    kit = build_kit(form)
    order = ORDER_STD + ORDER_NEW
    clips = {}
    for clip in order:
        new = clip in NC; src = NC[clip] if new else C[clip]
        c = dict(noface=[], full=[], overlay=[], anchors=[], new=new)
        for k, p in enumerate(src):
            p = dict(p); p["_k"] = k
            if clip != "idle": p = M.render_fit(form, p, f"{clip}_{k + 1:02d}")
            if new:
                body = L.body_render(form, p)
                while p.get("rot") and touches(body):          # 後仰掂邊 → 收細角度（記錄）
                    p["rot"] = p["rot"] - 1; M.FIT_LOG.append((form, f"{clip}_{k + 1:02d}", ["rot-1"])); body = L.body_render(form, p)
                an = pend_rot(form, p, evo_anchors(form, p, NVIS.get(clip, [True] * 99)[k]), clip in L.PIVOT_OVERRIDE)
                face = NFACE[clip][k]; an["face"] = dict(face) if face else None
                full = L.compose_face(body, an, face, kit)
            else:
                full = M.render(form, p); body = M.render(form, L.noface_params(p))
                an = evo_anchors(form, p, True)
                eo = p.get("eyes", "open"); mo = p.get("mouth", "smile")
                an["face"] = dict(eyes=L.OLD_EYE.get(eo, eo), gaze="C", mouth=L.OLD_MOUTH.get(mo, mo), src=f"{eo}/{mo}")
            ov = np.where(full != body, full, 0).astype(np.uint8)
            c["noface"].append(body); c["full"].append(full); c["overlay"].append(ov); c["anchors"].append(an)
        clips[clip] = c
    CUR[0] = None
    return order, clips, kit

# ============================================================ 光卵 evo_egg (24, no face rig)
EGG_S = 24; EGG_PIV = (12, 21)
def egg_geo(p):
    sx, sy = p.get("sx", 1.0), p.get("sy", 1.0); rx, ry = 6.9 * sx, 8.6 * sy
    cx = 12.0 + p.get("dx", 0.0); bottom = 21.0 - p.get("lift", 0.0); cy = bottom - ry
    return cx, cy, rx, ry

def _shear_rows(a, amt, y0, ref, up=True):
    if not amt: return a
    out = np.zeros_like(a); S = a.shape[0]
    for y in range(S):
        d = (y0 - y) if up else (y - y0)
        sh = 0 if d <= 0 else int(round(amt * d / ref))
        if sh == 0: out[y] = a[y]
        elif sh > 0: out[y, sh:] = a[y, :-sh]
        else: out[y, :sh] = a[y, -sh:]
    return out

CRACK = [(1, 2), (2, 3), (1, 4), (2, 5), (1, 6), (0, 7), (1, 8)]
CRACK4 = [(1, 2), (1, 3), (2, 3), (2, 4), (1, 4), (1, 5), (0, 5), (0, 6)]   # 孵化用：4 連通，深色裂紋讀得清
def reoutline(a):
    """斜切（tilt）後重新描邊：拆走外框，按新外形再描（裂紋等內部深色保留）"""
    ol = IDX["outline"]; nz = a > 0
    p = np.pad(nz, 1); inner4 = p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]
    core = nz & ((a != ol) | inner4)
    lab, n = ndi.label(core, structure=np.ones((3, 3), int))
    if n == 0: return a
    big = np.argmax(np.bincount(lab.ravel())[1:]) + 1; body = lab == big
    keep = nz & ~ndi.binary_dilation(body, structure=np.ones((3, 3), bool))   # 光點／星：照留，唔描邊
    out = np.where(body | keep, a, 0).astype(a.dtype); out[EC.ring(body) & ~body] = ol
    return out
def split_y(cx, cy, ry, x):
    return int(round(cy - 0.12 * ry)) + (0, -1, 0, 1)[int(math.floor(x - cx + 40)) % 4]

def render_egg(p):
    S = EGG_S; cv = bt.Cv(S); cx, cy, rx, ry = egg_geo(p)
    g = p.get("glow", 0); crack = p.get("crack", 0); tw = p.get("twinkle", 0); stage = p.get("hatch", 0)
    m = bt.egg_mask(cv, cx, cy, rx, ry)
    shade(cv, m, cx, cy, rx, ry, "egg", 0.2 + 0.1 * g); cv.solid |= m
    for (a, b, c) in ((-0.35, -0.3, "cream4"), (0.4, 0.2, "cream3"), (-0.2, 0.55, "cream4"), (0.1, 0.05, "glow_warm"), (-0.55, 0.2, "glow_warm")):
        cv.put(cx + a * rx, cy + b * ry, c)
    cv.put(cx + 0.4 * rx + 1, cy + 0.2 * ry, "cream3")
    cv.outline()
    # glow aura (outside outline, dotted, emissive)
    # crack：idle＝egg_dark 微裂（concept）；孵化＝outline 深色裂紋＋漏光
    cc = "egg_dark" if crack == 0 else "outline"
    if crack == 0:
        for (ox, oy) in CRACK[:3]: cv.put(cx + ox, cy - ry + oy, cc)
    elif stage < 3:
        for (ox, oy) in CRACK4[:(5, 8, 8)[min(crack, 3) - 1]]: cv.put(cx + ox, cy - ry + oy, cc)
        if crack >= 2:
            for (ox, oy) in ((-1, 6), (-2, 6), (3, 4), (3, 5)): cv.put(cx + ox, cy - ry + oy, "outline")
            for (ox, oy) in ((2, 2), (1, 6)): cv.put(cx + ox, cy - ry + oy, "glow_core")
    if crack >= 3:   # 圍一圈 zigzag 裂（之後開蓋），裂縫間漏光
        for x in range(int(cx - rx) + 1, int(cx + rx) + 1):
            y = split_y(cx, cy, ry, x)
            if 0 <= y < S and m[y, x]: cv.a[y, x] = IDX["outline"] if (x % 3) else IDX["glow_core"]
    cv.put(cx - rx * .5, cy - ry * .55, "cream4"); cv.put(cx - rx * .5 + 1, cy - ry * .55, "cream4")
    a = cv.a
    if p.get("tilt"): a = reoutline(_shear_rows(a, p["tilt"], int(round(cy + ry)), ry * 2))
    if g and stage < 4:   # glow aura：外框外一圈虛點（emissive）；glow≥2 推出 2px
        nz = a > 0; d1 = ndi.binary_dilation(nz)
        h1 = (ndi.binary_dilation(d1) & ~d1) if g > 1 else (d1 & ~nz)
        h1[[0, -1], :] = False; h1[:, [0, -1]] = False
        a = a.copy(); a[h1 & (((cv.xx + cv.yy + g) % 3) == 0)] = IDX["glow_mid"]
    # 3 = 蓋起 2px＋光縫；4 = 蓋彈去右上＋光柱；5 = 半殼＋光球（→ 絨點）
    if stage >= 3:
        top = np.zeros(a.shape, bool)
        for x in range(S): top[:split_y(cx, cy, ry, x) + 1, x] = True
        lidp = np.where(top, a, 0); base = np.where(top, 0, a)
        bm = base > 0; base[(EC.ring(bm) & top) & (np.roll(bm, -1, 0))] = IDX["outline"]
        out = np.zeros_like(a); oc = bt.Cv(S); oc.a = out
        yb = int(round(cy - 0.12 * ry))
        if stage == 3:
            for x in range(S):
                if bm[:, x].any():
                    ys0 = split_y(cx, cy, ry, x)
                    for y in range(ys0 - 1, ys0 + 1): out[y, x] = IDX["glow_core" if abs(x + 0.5 - cx) < 3 else "glow_mid"]
            for (x, y) in ((cx - rx - 1, yb - 1), (cx + rx + 1, yb - 1), (cx - rx - 2, yb - 2), (cx + rx + 2, yb - 2)): oc.put(x, y, "glow_mid")
        else:
            oy = yb - (3 if stage == 4 else 4); orr = 3.4 if stage == 4 else 3.2
            om = oc.ell(cx, oy, orr, orr); out[om] = IDX["glow_mid"]; out[oc.ell(cx, oy, orr - 1.4, orr - 1.4)] = IDX["glow_core"]
            out[EC.ring(om) & (out == 0)] = IDX["glow"]
            rays = ((-1, -1), (1, -1), (-1, 0.35), (1, 0.35)) if stage == 4 else ((-1, -1), (1, -1))
            ln = 3 if stage == 4 else 2
            for (dx, dy) in rays:
                for t in range(ln):
                    x, y = int(round(cx + dx * (orr + 2 + t))), int(round(oy + dy * (orr + 1 + t)))
                    if 1 <= x < S - 1 and 1 <= y < S - 1 and out[y, x] == 0: out[y, x] = IDX["glow_core" if t == 0 else "glow_mid"]
        out[bm] = base[bm]
        if stage == 3:
            ys, xs = np.nonzero(lidp)
            for y, x in zip(ys, xs):
                yy, xx = y - 2, x + 1
                if 1 <= yy < S - 1 and 1 <= xx < S - 1: out[yy, xx] = lidp[y, x]
        elif stage == 4:   # 蓋爆開 → 兩塊碎殼左右飛
            for (fx0, fy0, fl) in ((cx - 8.5, 3, -1), (cx + 6.5, 2, 1)):
                fx0 = int(round(fx0))
                for (ox, oy, c) in ((1, 0, "outline"), (2, 0, "outline"), (0, 1, "outline"), (1, 1, "cream4"), (2, 1, "cream2"), (3, 1, "outline"), (1, 2, "outline"), (2, 2, "outline")):
                    xx = fx0 + (ox if fl > 0 else 3 - ox); yy = fy0 + oy
                    if 1 <= xx < S - 1 and 1 <= yy < S - 1: out[yy, xx] = IDX[c]
        a = out
    lc = bt.Cv(S); lc.a = a
    # sparkles / stardust (twinkle phase)
    SP = [((3, 6), 0), ((21, 9), 1), ((19, 18), 2), ((4, 16), 3)]
    for (x, y), ph in SP:
        on = (tw + ph) % 4
        if a[y - 1:y + 2, x - 1:x + 2].any(): continue
        if on == 0: EC.sparkle(lc, x, y)
        elif on == 1: lc.put(x, y, "glow")
        elif on == 2 and g: lc.put(x, y, "glow_mid")
    for fx_ in p.get("extras", []): fx_(lc, cx, cy, rx, ry)
    return lc.a

def egg_pop(k):
    """tap: 小星仔彈出（右上）"""
    def fn(cv, cx, cy, rx, ry):
        x, y = int(cx + rx + 1), int(cy - ry + 3 - k)
        if 1 <= x < cv.n - 1 and 1 <= y < cv.n - 1: EC.sparkle(cv, x, y)
    return fn

EGG_CLIPS = {
 "idle":   [dict(tilt=0, twinkle=0), dict(tilt=1, sx=0.99, sy=1.01, twinkle=1), dict(tilt=0, twinkle=2), dict(tilt=-1, sx=0.99, sy=1.01, twinkle=3)],
 "glow":   [dict(glow=1, twinkle=0), dict(glow=2, sx=1.03, sy=1.03, twinkle=2)],
 "tap":    [dict(sx=1.08, sy=0.9, twinkle=0), dict(lift=1, sx=0.95, sy=1.05, tilt=1, twinkle=1, extras=[egg_pop(0)]),
            dict(lift=0, sx=1.04, sy=0.95, tilt=-1, twinkle=2, extras=[egg_pop(2)]), dict(tilt=0, twinkle=3)],
 "hatch":  [dict(crack=1, tilt=-1, dx=-0.5), dict(crack=2, tilt=1, dx=0.5, glow=1), dict(crack=3, sx=1.05, sy=0.94, glow=2),
            dict(crack=3, hatch=3, glow=1), dict(crack=3, hatch=4, glow=2), dict(crack=3, hatch=5, glow=1, twinkle=1)],
 "picked_up": [dict(tilt=0, twinkle=0, pend=0), dict(pend=1, twinkle=1), dict(pend=0, twinkle=2), dict(pend=-1, twinkle=3)],
}
EGG_ORDER = ["idle", "glow", "tap", "hatch", "picked_up"]
EGG_META = {"idle": (6, True, 0, 0, True), "glow": (4, True, 0, 2, True), "tap": (10, False, 0, 4, False),
            "hatch": (6, False, 0, 9, False), "picked_up": (6, True, 0, 7, False)}
EGG_NOTE = {"idle": "沿用舊蛋 idle（左右擺 0/+1/0/−1＋星塵閃）", "glow": "沿用舊蛋 glow（發光呼吸 2 幀）",
            "tap": "新：被點 → 壓扁、彈起、落地晃一晃、右上彈粒星（→ idle）",
            "hatch": "新：裂紋變長 → 漏光 → 開蓋 → 閃光 → 剩半個殼＋光球（最後一幀 hold；引擎 crossfade 去 evo_dot idle，絨點坐喺同款半殼）",
            "picked_up": "新（浮動寵物拖曳）：頂部拎起左右擺，pivot＝grab"}

def egg_grab(p):
    cx, cy, rx, ry = egg_geo(p); return [int(math.floor(cx)), int(round(cy - ry))]

def build_egg():
    clips = {}
    for clip in EGG_ORDER:
        c = dict(noface=[], full=[], overlay=[], anchors=[], new=True)
        for k, p in enumerate(EGG_CLIPS[clip]):
            p = dict(p); a = render_egg(p)
            if clip == "picked_up" and p.get("pend"):
                gx, gy = egg_grab(p); a = _shear_rows(a, p["pend"], gy, (EGG_S - 3) - gy, up=False)
            cx, cy, rx, ry = egg_geo(p)
            hx, hy = int(round(cx + 0.95 * rx)), int(round(cy - 0.75 * ry))
            an = {"head_r": [hx, hy], "faceVisible": False, "face": None,
                  "crack": [int(round(cx + 1)), int(round(cy - ry + 2))]}
            if clip == "picked_up": an["grab"] = egg_grab(p)
            c["full"].append(a); c["noface"].append(a.copy()); c["overlay"].append(np.zeros_like(a)); c["anchors"].append(an)
        clips[clip] = c
    return EGG_ORDER, clips, {}

# ============================================================ io helpers
def to_img(a):
    o = np.zeros(a.shape + (4,), np.uint8)
    for i, c in enumerate(RGB):
        if i: o[a == i, :3] = c; o[a == i, 3] = 255
    return Image.fromarray(o, "RGBA")
def emis_img(a):
    o = np.zeros(a.shape + (4,), np.uint8); o[np.isin(a, EMIS)] = (255, 255, 255, 255)
    return Image.fromarray(o, "RGBA")

def fsize(form): return EGG_S if form == "evo_egg" else FORMS[form]["S"]
def fpiv(form): S = fsize(form); return (S // 2, S - 3)
def form_meta(form, clip): return EGG_META[clip] if form == "evo_egg" else meta(clip)

def write_files(form, order, clips, kit):
    d = os.path.join(OUT, form)
    if os.path.isdir(d): shutil.rmtree(d)
    for s in ("frames", "layers", "emissive", "kit"): os.makedirs(os.path.join(d, s), exist_ok=True)
    for clip in order:
        c = clips[clip]
        for k in range(len(c["full"])):
            n = f"{clip}_{k + 1:02d}"
            to_img(c["full"][k]).save(os.path.join(d, "frames", n + ".png"))
            to_img(c["noface"][k]).save(os.path.join(d, "layers", n + "_noface.png"))
            to_img(c["overlay"][k]).save(os.path.join(d, "layers", n + "_faceov.png"))
            emis_img(c["full"][k]).save(os.path.join(d, "emissive", n + "_emissive.png"))
            emis_img(c["noface"][k]).save(os.path.join(d, "emissive", n + "_noface_emissive.png"))
    if not kit: os.rmdir(os.path.join(d, "kit"))
    for name, (a, pv) in kit.items(): to_img(a).save(os.path.join(d, "kit", name + ".png"))
    S = fsize(form)
    fa = {"version": 1, "form": form, "frameSize": S, "coords": "frame-local px, origin = frame top-left, y down",
          "pivotPx": list(fpiv(form)), "pivotOverride": {"picked_up": "grab"},
          "keys": ("eyeL/eyeR/mouth = 五官錨點（kit piece pivot；已含面右移 1px）; head_r = 頭右上圖示; "
                   + ("bulb = 第一粒燈芽中心（bulb_base/bulb_glow pivot）; " if form == "evo_hop" else "（冇 bulb：未著燈）; ")
                   + "faceVisible; face = 預設表情; grab = 頭頂拎點（picked_up，亦係 pivot）")
          if form != "evo_egg" else "head_r = 右上圖示; crack = 裂紋頂點; faceVisible=false（光卵冇 face rig）; grab = 拎點（picked_up pivot）",
          "anchors": {clip: clips[clip]["anchors"] for clip in order}}
    p = os.path.join(d, f"face_anchors_{form}.json")
    with open(p, "w") as fh:
        head = {k: v for k, v in fa.items() if k != "anchors"}
        fh.write(json.dumps(head, ensure_ascii=False)[:-1] + ',\n "anchors":{\n')
        fh.write(',\n'.join('  ' + json.dumps(cl) + ':[\n' + ',\n'.join('   ' + json.dumps(a, ensure_ascii=False, separators=(",", ":")) for a in lst) + ']'
                            for cl, lst in fa["anchors"].items()) + '}}\n')
    json.load(open(p))

def paste_ex(dst, im, x, y, w, h):
    e = np.array(im); dst.paste(im, (x, y))
    dst.paste(Image.fromarray(e[:1], "RGBA"), (x, y - 1)); dst.paste(Image.fromarray(e[-1:], "RGBA"), (x, y + h))
    dst.paste(Image.fromarray(e[:, :1], "RGBA"), (x - 1, y)); dst.paste(Image.fromarray(e[:, -1:], "RGBA"), (x + w, y))

def write_atlas(form, order, clips, kit):
    piv = fpiv(form); items = []; anims = {}
    for clip in order:
        c = clips[clip]; fps, loop, lf, pr, intr = form_meta(form, clip)
        pov = "grab" if clip == "picked_up" else None
        pv = (lambda k, c=c: tuple(c["anchors"][k]["grab"])) if pov else (lambda k: piv)
        extra = {"pivot": pov} if pov else {}
        if loop and lf: extra["loopFrom"] = lf
        if form != "evo_egg" and clip in L.HOLD_LAST_S: extra["holdLast_s"] = L.HOLD_LAST_S[clip]
        if form == "evo_egg" and clip == "hatch": extra["holdLast"] = True
        ff = [f"{clip}_{k + 1:02d}" for k in range(len(c["full"]))]
        nf = [f"{clip}_noface_{k + 1:02d}" for k in range(len(c["full"]))]
        for k in range(len(ff)):
            items.append((ff[k], c["full"][k], pv(k)))
            if form != "evo_egg": items.append((nf[k], c["noface"][k], pv(k)))
        anims[clip] = {"frames": ff, "fps": fps, "loop": loop, **extra}
        if form != "evo_egg": anims[clip + "_noface"] = {"frames": nf, "fps": fps, "loop": loop, **extra}
    for name, (a, pv) in kit.items(): items.append((name, a, pv))
    pages = L.pack_pages(items)
    assert len(pages) == 1, f"atlas {form} must fit one 1024-wide page"
    W, H, pos = pages[0]
    lut = {n: (a, pv) for n, a, pv in items}
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); emi = Image.new("RGBA", (W, H), (0, 0, 0, 0)); jf = {}
    for name, (x, y, w, h) in pos.items():
        a, pv = lut[name]
        paste_ex(img, to_img(a), x, y, w, h); paste_ex(emi, emis_img(a), x, y, w, h)
        jf[name] = {"frame": {"x": x, "y": y, "w": w, "h": h}, "rotated": False, "trimmed": False,
                    "spriteSourceSize": {"x": 0, "y": 0, "w": w, "h": h}, "sourceSize": {"w": w, "h": h},
                    "pivot": {"x": round(pv[0] / w, 4), "y": round(pv[1] / h, 4)}, "pivotPx": {"x": int(pv[0]), "y": int(pv[1])}}
    base = f"atlas_{form}"
    img.save(os.path.join(OUT, base + ".png")); emi.save(os.path.join(OUT, base + "_emissive.png"))
    S = fsize(form); nm = "光卵" if form == "evo_egg" else FORMS[form]["name"]
    m = {"image": base + ".png", "emissive": base + "_emissive.png", "size": {"w": W, "h": H}, "scale": 1, "format": "RGBA8888",
         "padding": 2, "extrude": 1, "form": form, "name": nm, "stage": FORM_IDS.index(form) + 1, "frameSize": S, "pivotPx": list(piv),
         "palette": "palette_base.json",
         "pivotRule": f"body frames bottom-center {tuple(piv)}；picked_up* pivotPx = anchors.grab（頭頂拎點）；kit pieces pivotPx = anchor point",
         "note": (f"{nm}：<clip>_NN 完整幀" + ("" if form == "evo_egg" else "、<clip>_noface_NN 無臉身體、五官 eyes_*/mouth_*（" + ("4×5 L" if FORMS[form]["tier"] == "L" else "4×4 S") + " 級 kit）")
                  + ("、bulb_base/bulb_glow（第一粒燈芽）" if form == "evo_hop" else "") + f"。{base}_emissive.png 同 layout，白＝發光（glow_core/glow_mid）。")}
    json.dump({"frames": jf, "animations": anims, "meta": m}, open(os.path.join(OUT, base + ".json"), "w"), indent=1, ensure_ascii=False)
    return W, H, len(items)

# ============================================================ previews
FONT = None
def font(sz=12):
    try: return EC.font(sz)
    except Exception: return None

def contact(form, order, clips, kit, Z=4):
    S = fsize(form); cell = S * Z + 6; cols = max(len(clips[c]["full"]) for c in order)
    LW = 150; rows = list(order) + (["face kit"] if kit else [])
    cs = Image.new("RGBA", (LW + cols * cell + 6, 30 + len(rows) * (cell + 4) + 6), BG); dr = ImageDraw.Draw(cs); fn = font(14)
    nm = "光卵" if form == "evo_egg" else FORMS[form]["name"]
    dr.text((8, 6), f"{form} {nm} {S}px  pivot {fpiv(form)}  {Z}x", fill=(255, 248, 224, 255), font=fn)
    for r, clip in enumerate(order):
        y = 30 + r * (cell + 4); fps = form_meta(form, clip)[0]
        dr.text((8, y + 8), clip, fill=(255, 248, 224, 255), font=fn)
        dr.text((8, y + 26), f"{len(clips[clip]['full'])}f {fps}fps", fill=(200, 196, 230, 255), font=font(11))
        for k, a in enumerate(clips[clip]["full"]):
            cs.alpha_composite(to_img(a).resize((S * Z, S * Z), Image.NEAREST), (LW + k * cell, y))
    if kit:   # face presets on idle_01 noface
        y = 30 + len(order) * (cell + 4)
        dr.text((8, y + 8), "face presets", fill=(255, 248, 224, 255), font=fn)
        c = clips["idle"]
        for k, nm2 in enumerate(["neutral", "happy", "sleepy", "surprised", "hungry", "cuddly", "grumpy", "curious", "wink"][:cols]):
            a = L.compose_face(c["noface"][0], c["anchors"][0], L.PRESETS[nm2], kit)
            cs.alpha_composite(to_img(a).resize((S * Z, S * Z), Image.NEAREST), (LW + k * cell, y))
    os.makedirs(PRV, exist_ok=True)
    cs.save(os.path.join(PRV, f"{form}_contact_4x.png"))

def gifs(form, order, clips):
    d = os.path.join(PRV, "gif"); os.makedirs(d, exist_ok=True); S = fsize(form); Z = 8
    pick = order if form == "evo_egg" else ["idle", "walk", "emo_happy", "sleep_loop", "picked_up", "smug_pose", "act_cool", "lookup_tip", "rush", "cheer_jump"]
    for clip in pick:
        fr = []
        for a in clips[clip]["full"]:
            m = Image.new("RGBA", (S + 4, S + 4), BG); m.alpha_composite(to_img(a), (2, 2)); fr.append(m.resize(((S + 4) * Z, (S + 4) * Z), Image.NEAREST))
        L.save_gif(os.path.join(d, f"{form}_{clip}_8x.gif"), fr, form_meta(form, clip)[0], loops=2, hold_last_ms=300)

def batch_contact(res, Z=4):
    """overall: rows = 4 stages (ground-aligned at 40px cells), representative frames"""
    picks = {"evo_egg": [("idle", 0), ("idle", 1), ("glow", 1), ("tap", 1), ("tap", 2), ("hatch", 0), ("hatch", 2), ("hatch", 3), ("hatch", 4), ("hatch", 5), ("picked_up", 1), ("picked_up", 3)],
             "_": [("idle", 0), ("blink", 1), ("walk", 2), ("emo_happy", 1), ("sleep_loop", 0), ("eat", 2), ("sick", 0), ("picked_up", 1),
                   ("smug_pose", 3), ("act_cool", 2), ("lookup_tip", 2), ("sniff_itch", 2), ("turn_back", 1), ("cheer_jump", 2)]}
    CELL = 42; ncol = max(len(v) for v in picks.values()); LW = 130
    W = LW + ncol * (CELL * Z + 4) + 8; H = 34 + len(FORM_IDS) * (CELL * Z + 24) + 8
    cs = Image.new("RGBA", (W, H), BG); dr = ImageDraw.Draw(cs); fn = font(15)
    dr.text((8, 8), "團絨 evo6 batch A — 光卵 24 / 絨點 28 / 絨芽 32 / 絨跳 38（4x，同一地線）", fill=(255, 248, 224, 255), font=fn)
    for r, form in enumerate(FORM_IDS):
        order, clips, kit = res[form]; S = fsize(form); piv = fpiv(form)
        y0 = 34 + r * (CELL * Z + 24)
        nm = "光卵" if form == "evo_egg" else FORMS[form]["name"]
        dr.text((8, y0 + 40), f"{FORM_IDS.index(form) + 1} {nm}", fill=(255, 248, 224, 255), font=font(18))
        dr.text((8, y0 + 66), f"{S}px", fill=(200, 196, 230, 255), font=fn)
        for k, (clip, i) in enumerate(picks.get(form, picks["_"])):
            i = min(i, len(clips[clip]["full"]) - 1); a = clips[clip]["full"][i]; x0 = LW + k * (CELL * Z + 4)
            # align pivot to cell (CELL/2, CELL-4)
            ox, oy = CELL // 2 - piv[0], CELL - 4 - piv[1]
            m = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0)); m.alpha_composite(to_img(a), (ox, oy))
            cs.alpha_composite(m.resize((CELL * Z, CELL * Z), Image.NEAREST), (x0, y0))
            dr.text((x0 + 4, y0 + CELL * Z + 2), f"{clip}_{i + 1:02d}", fill=(200, 196, 230, 255), font=font(11))
    cs.save(os.path.join(PRV, "evo6_batchA_contact_4x.png"))

# ============================================================ docs (CLIPS.json / CLIPS.md, idempotent, additions only)
MD_A = "<!-- EVO6A-START -->"; MD_B = "<!-- EVO6A-END -->"; LUMI_MARK = "<!-- LUMI-START -->"
def backup(path):
    os.makedirs(BACK, exist_ok=True)
    dst = os.path.join(BACK, os.path.relpath(path, ROOT).replace("/", "__"))
    if not os.path.exists(dst): shutil.copy2(path, dst)

def update_docs(res, ainfo):
    p = os.path.join(MOT, "CLIPS.json"); backup(p); D = json.load(open(p))
    for form in FORM_IDS:
        order, clips, kit = res[form]; S = fsize(form); W, H, n = ainfo[form]
        nm = "光卵" if form == "evo_egg" else FORMS[form]["name"]
        ent = {"name": nm, "stage": FORM_IDS.index(form) + 1, "evo6": True, "batch": "A", "frameSize": S, "pivotPx": list(fpiv(form)),
               "atlas": f"../evo6/atlas_{form}.png", "json": f"../evo6/atlas_{form}.json", "emissive": f"../evo6/atlas_{form}_emissive.png",
               "atlasSize": [W, H], "atlasPieces": n, "frames": sum(len(clips[c]["full"]) for c in order),
               "palette": "../evo6/palette_base.json", "faceAnchors": f"../evo6/{form}/face_anchors_{form}.json", "clips": order,
               "concept": "../evo6_concept/（v3 lumi feel）"}
        if form == "evo_egg":
            ent.update({"faceRig": False, "hasBulb": False, "clipDefs": {c: {"frames": len(clips[c]["full"]), "fps": EGG_META[c][0], "loop": EGG_META[c][1],
                        "priority": EGG_META[c][3], "interruptible": EGG_META[c][4], "notes": EGG_NOTE[c], **({"pivot": "grab"} if c == "picked_up" else {}),
                        **({"holdLast": True, "next": "evo_dot.idle（進化）"} if c == "hatch" else {}), "anchors": clips[c]["anchors"],
                        "full": f"../evo6/evo_egg/frames/{c}_NN.png", "emissive": f"../evo6/evo_egg/emissive/{c}_NN_emissive.png"} for c in order},
                        "note": "光卵：冇 face rig（同舊蛋）；_noface＝完整幀、_faceov 全透明（為咗同其他形態檔案結構一致）。"})
        else:
            f = FORMS[form]
            ent.update({"faceRig": True, "faceTier": "L 4×5" if f["tier"] == "L" else "S 4×4", "hasBulb": form == "evo_hop",
                        "headRightAnchor": list(M.ANCH[form]["head_r"]), "potAnchor": list(M.ANCH[form]["pot"]), "sunAnchor": [0, 0],
                        "kitPieces": sorted(kit), "std23": ORDER_STD, "liveliness": ORDER_NEW,
                        "note": {"evo_dot": "絨點：未有腳，坐喺半個蛋殼（殼＝光卵同款 egg ramp）；walk/rush 等係成個殼一齊彈；picked_up 冇吊腳（殼跟住）；arms 只喺 up/eat/upx 時出細肉手；冇 bulb。",
                                 "evo_sprout": "絨芽：有腳有手、頭頂未著燈雙葉芽（leaf/leaf_d，droop 時垂低、bud>1 時企起）；冇 bulb 錨點、冇身體 emissive。",
                                 "evo_hop": "絨跳：第一粒著燈（柔光款 bud r2.0，bulb 錨點＝燈芽中心）、尖耳（droop 時垂）、捲尾橙尖（fluff 相位擺）、白肚。"}[form]})
        D["forms"][form] = ent
    for c in D["clips"]:
        n = c["name"]
        for form in BODY_FORMS:
            order, clips, kit = res[form]
            if n in clips:
                c.setdefault("anchors", {})[form] = clips[n]["anchors"]
                c[form] = {"frames": len(clips[n]["full"]), "full": f"../evo6/{form}/frames/{n}_NN.png", "noface": f"../evo6/{form}/layers/{n}_NN_noface.png",
                           "faceov": f"../evo6/{form}/layers/{n}_NN_faceov.png", "emissive": f"../evo6/{form}/emissive/{n}_NN_emissive.png",
                           "atlasClip": n, "nofaceClip": f"{n}_noface", "atlas": f"../evo6/atlas_{form}.json"}
            else:
                c.get("anchors", {}).pop(form, None); c.pop(form, None)
    D["evo6"] = {"batch": "A", "forms": FORM_IDS, "tool": "tools/build_evo6_anim.py", "validator": "tools/validate_evo6_anim.py",
                 "note": "團絨 6 階段進化（光卵→絨點→絨芽→絨跳→守夜者→靜光）。batch A＝1–4 階；5 守夜者 44、6 靜光 48 未出。姿勢＝現有同名 clip，只換外觀層。",
                 "rebuildNote": "build_tuanrong_liveliness_docs.py 由 _backup_v1 重砌 CLIPS.json → 之後要再跑 build_lumi.py 同 build_evo6_anim.py。"}
    json.dump(D, open(p, "w"), indent=1, ensure_ascii=False)
    mp = os.path.join(MOT, "CLIPS.md"); backup(mp); md = open(mp, encoding="utf-8").read()
    if MD_A in md: md = md[:md.index(MD_A)].rstrip() + "\n\n" + md[md.index(MD_B) + len(MD_B):].lstrip()
    rows = []
    for form in FORM_IDS:
        order, clips, kit = res[form]; W, H, n = ainfo[form]
        nm = "光卵" if form == "evo_egg" else FORMS[form]["name"]
        tot = sum(len(clips[c]["full"]) for c in order)
        rows.append(f"| {FORM_IDS.index(form) + 1} | {nm} `{form}` | {fsize(form)} | {fpiv(form)} | {len(order)} | {tot} | `../evo6/atlas_{form}.png`（{W}×{H}，{n} 塊）＋ `_emissive` |")
    egg = res["evo_egg"]
    sec = f"""{MD_A}
## 進化 6 階 batch A（光卵／絨點／絨芽／絨跳，evo6 v3 lumi feel）
- 外觀＝`../evo6_concept/`（v3 lumi feel）；姿勢＝現有同名 clip（std23 ＋ 生命感 s1/s2，同 sprout/radiant/soft 一樣 fps／priority／anchors 結構），只換外觀層。
- 基本 31 色（`../palette.json`）、alpha 0/255、無 AA、向右；每形態一張 atlas（1024 闊、padding 2、extrude 1、每幀 pivotPx）＋ 同 layout emissive（白＝glow_core/glow_mid）。
- 每幀：`frames/<clip>_NN.png`、`layers/<clip>_NN_noface.png`／`_faceov.png`、`emissive/…`；錨點 `../evo6/<form>/face_anchors_<form>.json`（＝本檔 clips[].anchors.<form>）。
- face kit 按新尺寸重出：絨點／絨芽 4×4 豆眼（S 級）、絨跳 4×5（L 級＝燦光原裝）；bulb 只限絨跳（第一粒著燈）；picked_up pivot＝grab。
- 光卵冇 face rig（同舊蛋）：{"、".join(f"{c} {len(egg[1][c]['full'])}" for c in egg[0])}（定義喺 `forms.evo_egg.clipDefs`）。

| 階 | 形態 | px | pivot | clip | 幀 | atlas |
|---|---|---|---|---|---|---|
""" + "\n".join(rows) + f"""

5 守夜者 44、6 靜光 48 ＝ batch B／C（未出）。
{MD_B}
"""
    if LUMI_MARK in md:
        i = md.index(LUMI_MARK); md = md[:i].rstrip() + "\n\n" + sec + "\n" + md[i:]
    else:
        md = md.rstrip() + "\n\n" + sec
    open(mp, "w", encoding="utf-8").write(md)

# ============================================================ main
def main():
    os.makedirs(OUT, exist_ok=True); os.makedirs(PRV, exist_ok=True)
    res = {"evo_egg": build_egg()}
    for form in BODY_FORMS: res[form] = build_form(form)
    ainfo = {}; stats = {}
    for form in FORM_IDS:
        order, clips, kit = res[form]
        write_files(form, order, clips, kit)
        ainfo[form] = write_atlas(form, order, clips, kit)
        contact(form, order, clips, kit); gifs(form, order, clips)
        edge = [f"{c}_{k + 1:02d}" for c in order for k, a in enumerate(clips[c]["full"]) if a[0].any() or a[-1].any() or a[:, 0].any() or a[:, -1].any()]
        stats[form] = {"clips": {c: len(clips[c]["full"]) for c in order}, "nClips": len(order), "frames": sum(len(clips[c]["full"]) for c in order),
                       "atlas": ainfo[form][:2], "pieces": ainfo[form][2], "edgeTouch": edge,
                       "fit_adjustments": [f"{b}:{'/'.join(c)}" for a, b, c in M.FIT_LOG if a == form]}
        print(form, "clips", len(order), "frames", stats[form]["frames"], "atlas", ainfo[form], "edge", edge)
    batch_contact(res)
    shutil.copy(next(p for p in (os.path.join(MOT, "palette.json"), os.path.join(TR, "palette.json")) if os.path.exists(p)), os.path.join(OUT, "palette_base.json"))
    update_docs(res, ainfo)
    json.dump(stats, open(os.path.join(OUT, "_stats.json"), "w"), indent=1, ensure_ascii=False)
    return res

if __name__ == "__main__":
    main()
