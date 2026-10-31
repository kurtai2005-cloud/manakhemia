#!/usr/bin/env python3
"""build_evo6_animBC.py — 團絨 evo6 batch B（守夜者 44 ×4 分支）＋ batch C（靜光 48 ×4 MVP）動畫。
外觀＝evo6_concept v3「lumi feel」lf5_* 畫法（build_evo6_concept.py），逐幀按 pose 參數重畫（pose-aware）；
姿勢＝現有同名 clip（motion std23 ＋ liveliness s1/s2；守夜者・微塵另加 s3 nuzzle_purr／reunion_happy）——只換外觀層。
引擎／錨點／kit／atlas／預覽＝build_evo6_anim.py（batch A）同一套（import 做 module，唔跑佢 main）。
分支色盤：螢絨＝palette_lumi（lumi_fur／fly 槽，emissive＝fly/fly_core）、微塵＝palette_dust（dust 灰米／lens）、燦光・柔光＝基本 31 色（emissive＝glow_core/glow_mid）。
Pillow＋numpy 程式逐像素繪製，原創，無 AI。alpha 0/255、無 AA、向右。
用法：python3 build_evo6_animBC.py [B|C|BC]（預設 BC）
"""
import json, math, os, shutil, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_evo6_anim as A
import build_tuanrong as bt
import build_tuanrong_motion as M
import build_tuanrong_liveliness as L
import build_evo6_concept as EC
import build_tuanrong_live_s3 as S3
from build_tuanrong import FORMS, IDX

ROOT, TR, OUT, PRV, MOT = A.ROOT, A.TR, A.OUT, A.PRV, A.MOT
BACK = os.path.join(ROOT, "_backups", "pre_evo6_animBC_20261031")
BG = A.BG
BRANCH_NAME = {"lumi": "螢絨", "radiant": "燦光", "soft": "柔光", "dust": "微塵"}
BRANCHES = ["lumi", "radiant", "soft", "dust"]
PALKEY = {"lumi": "lumi", "radiant": "base", "soft": "base", "dust": "dust"}
PALFILE = {"lumi": "palette_lumi.json", "base": "palette_base.json", "dust": "palette_dust.json"}
EMIS_NAMES = {"lumi": ("egg_shade", "cyan"), "base": ("glow_core", "glow_mid"), "dust": ("glow_core", "glow_mid")}
EMIS_PALNAMES = {"lumi": ("fly", "fly_core"), "base": ("glow_core", "glow_mid"), "dust": ("glow_core", "glow_mid")}   # 同一色喺各自 palette 檔嘅名
STILL_ORDER = ["idle", "blink", "emo_happy", "fall_asleep", "sleep_loop", "wake", "picked_up"]
S3_DUST = list(S3.S3_ORDER)

# ---- ramps (registered in both bt.RAMPS (arms/extras) and EC.RAMP (shade))
RAMPS = {"g_radiant": ["cream1", "cream2", "cream3", "cream4"], "g_soft": ["peach0", "peach1", "peach2", "cream3"],
         "g_lumi": ["zzz", "peach0", "peach1", "peach2"], "g_dust": ["peach0", "peach1", "peach2", "white"]}
SUN = {"radiant": ["cream2", "cream3", "cream4", "glow_core"], "soft": ["peach1", "peach2", "cream3", "cream4"],
       "lumi": ["peach0", "peach1", "peach2", "cream4"], "dust": ["peach1", "peach2", "white", "cream4"]}

# ---- forms
def _form(br, elder):
    S = 48 if elder else 44
    g = {"radiant": ((13.8, 11.6) if elder else (12.9, 10.9), 19, 16, 3.4, True, (0.0, 0.32, 0.55, 0.50), 6),
         "soft":    ((14.4, 12.2) if elder else (13.6, 11.6), 21, 12, 3.6, False, (0.0, 0.32, 0.55, 0.50), 6),
         "lumi":    ((13.6, 11.5) if elder else (12.9, 10.9), 19, 14, 3.0, False, (1.0, 0.34, 0.50, 0.45), 5),
         "dust":    ((13.8, 11.6) if elder else (13.0, 11.0), 19, 16, 3.2, False, (0.0, 0.32, 0.55, 0.50), 6)}[br]
    (rx, ry), kd, N, rbk, skip, belly, nt = g; k = rx / kd
    return dict(S=S, rx=rx, ry=ry, G=S - 3, ramp="g_" + br, N=N, rb=rbk * k, big=True, stem=0, k=k, skip_top=skip, belly=belly, nt=nt,
                name=("靜光・" if elder else "守夜者・") + BRANCH_NAME[br], stage=6 if elder else 5, tier="L", fdx0=1, fdy0=0.0, eo=0.40,
                br=(2.2, 1.3), arm=2.3 * k ** .5, feet=(2.4, 1.9), headk=(1.0, 0.85), pot=29 if elder else 27,
                branch=br, elder=elder, pal=PALKEY[br])
GUARD = {f"evo_guard_{b}": _form(b, False) for b in BRANCHES}
STILL = {f"evo_still_{b}": _form(b, True) for b in BRANCHES}
NEW = {**GUARD, **STILL}
A.EVO.update(NEW); FORMS.update(NEW)
for b in BRANCHES:
    bt.RAMPS["g_" + b] = RAMPS["g_" + b]; EC.RAMP["g_" + b] = RAMPS["g_" + b]
for fid, f in NEW.items():
    bt.RAMPS["sun_" + fid] = SUN[f["branch"]]; EC.RAMP["sun_" + fid] = SUN[f["branch"]]
    _, S, _, rx, ry, cx, cy = L._geo(fid, {})
    L.HEAD_K[fid] = f["headk"]
    hx, hy = int(round(cx + f["headk"][0] * rx)), int(round(cy - f["headk"][1] * ry))
    M.ANCH[fid] = dict(head_r=(hx - S // 2, hy - (S - 3)), pot=(f["pot"], 0), sun=(0, 0))
A.PT_KEYS = ("eyeL", "eyeR", "mouth", "head_r", "bulb", "bulb2", "tail")

def pal_rgb(form): return EC.pal_rgb(FORMS[form]["pal"]) if form in NEW else EC.pal_rgb("base")
def emis_ids(form): return sorted(IDX[n] for n in EMIS_NAMES[FORMS[form]["pal"] if form in NEW else "base"])
def to_img(a, form):
    rgb = pal_rgb(form); o = np.zeros(a.shape + (4,), np.uint8)
    for i, c in enumerate(rgb):
        if i: o[a == i, :3] = c; o[a == i, 3] = 255
    return Image.fromarray(o, "RGBA")
def emis_img(a, form):
    o = np.zeros(a.shape + (4,), np.uint8); o[np.isin(a, emis_ids(form))] = (255, 255, 255, 255)
    return Image.fromarray(o, "RGBA")

# ============================================================ lamp / feature geometry (shared by renderer and anchors)
def geo(form, p):
    f = FORMS[form]; _, S, _, rx, ry, cx, cy = L._geo(form, p); k = f["k"]; el = f["elder"]; br = f["branch"]
    sway = p.get("sway", 0) * 0.5; droop = p.get("droop", 0); tw = p.get("twinkle", 0)
    g = {}
    if br == "radiant":
        ln = int(round(7 * k)); pts = A.stem_pts(cx, cy - ry, ln, 0.0, sway, droop * 0.8)
        tx, ty = pts[-1]; kk = k * (1.05 if el else 1.0)
        g.update(stem=pts, bulb=(tx + 0.5, ty - 2 * kk), kk=kk)
    elif br == "soft":
        ln = int(round(5 * k)); pts = A.stem_pts(cx, cy - ry, ln, 0.0, sway, droop * 0.8)
        tx, ty = pts[-1]; g.update(stem=pts, bulb=(tx + 0.5, ty - 2.6), br_=2.6 * k ** .5)
    elif br == "lumi":
        ANTS = [(1, 0.55, 10), (6, 0.85, 9)] + ([(-3, -0.35, 8)] if el else [])
        ants = []
        for (bo, lean, ln) in ANTS:
            ln = int(round(ln * k * (1.15 if el else 1.0))); bxa = cx + bo * k; y0 = cy - ry + 1.5; pts = []
            for j in range(ln + 1):
                t = j / ln
                pts.append((bxa + lean * j * 0.9 + 2.2 * k * t * t * np.sign(lean) + sway * t + droop * t * t * 2.2 * np.sign(lean),
                            y0 - j + 1.8 * k * t * t + droop * t * t * 2.5))
            ants.append(pts)
        g["ants"] = ants
        g["bulbs"] = [(pts[-1][0] + .4, pts[-1][1] - .6) for pts in ants]
        g["bulb"], g["bulb2"] = g["bulbs"][0], g["bulbs"][1]
        tx, ty = cx - rx - 1.0 * k, cy + ry * 0.42 + 0.4 * math.sin(p.get("fluff", 0.0) * 2.0)
        g["tailc"] = (tx, ty); g["tail"] = (tx - 1.6 * k, ty + 0.4 * k)
    elif br == "dust":
        sw = (0, 1, 0, -1)[tw % 4] * 0.5
        g["bulb"] = (cx + rx * 0.88 + 1 + sw * 0.6, cy + ry * 0.55 + abs(sw))
        if el: g["bulb2"] = (cx + 1, cy - ry - 4.5 + (0.5 if tw % 4 in (1, 2) else 0.0))
    return g

# ============================================================ renderer
def _col(sick, c, alt="sick1"): return alt if sick else c

def render_adult(form, p):
    f = FORMS[form]; S = f["S"]; cv = bt.Cv(S); br = f["branch"]; el = f["elder"]; k = f["k"]
    sick = p.get("sick", False); ramp = "sick" if sick else f["ramp"]; R = bt.RAMPS[ramp]
    _, _, _, rx, ry, cx, cy = L._geo(form, p)
    lift = p.get("lift", 0.0); ground = f["G"] - 1.0 - lift
    sway = p.get("sway", 0); droop = p.get("droop", 0); bud = p.get("bud", 1.0); ph = p.get("fluff", 0.0); tw = p.get("twinkle", 0)
    G = geo(form, p); flap = math.sin(ph * 2.0 + tw * 1.3)
    gl = lambda c: ("sick1" if sick else c)
    # ---------------- behind: elder halo / wings, tails, ears
    if el and br == "radiant":
        hx_, hy_ = cx, cy - ry * 0.35
        hm = cv.ell(hx_, hy_, 17.5, 15.5) & ~cv.ell(hx_, hy_, 15.8, 13.9) & (cv.yy < hy_ + 2)
        cv.paint(hm, gl("glow")); cv.paint(hm & (((cv.xx + cv.yy + tw) % 4) == 0), gl("glow_core")); cv.solid |= hm
        for j, (a, b, ang) in enumerate(((8.0, 2.8, 150), (6.6, 2.3, 172))):
            ang = ang + 6 * flap * (1 if j == 0 else 0.6) - 10 * min(1.0, droop)
            d = (math.cos(math.radians(ang)), -math.sin(math.radians(ang)))
            bx0, by0 = cx - rx * 0.62, cy - ry * 0.15 + j * 2
            w = EC.rot_ell(cv, bx0 + d[0] * a * 0.7, by0 + d[1] * a * 0.7, a, b, ang)
            cv.paint(w, gl("glow")); cv.paint(w & EC.rot_ell(cv, bx0 + d[0] * a * 0.7 - .6, by0 + d[1] * a * 0.7 - .8, a - 1.5, b - 1.2, ang), gl("glow_mid")); cv.solid |= w
    if el and br == "soft":
        for j, (a, b, ang) in enumerate(((7.4, 2.7, 150), (6.0, 2.2, 122))):
            EC.leaf(cv, cx - rx * 0.62 - 3, cy - ry * 0.25 - j * 3, a, b, ang + 6 * flap - 12 * min(1.0, droop), gl("leaf"), _col(sick, "leaf_d", "sick0"))
    if el and br == "dust":
        for j, ang in enumerate((150, 125)):
            ang = ang + 5 * flap - 10 * min(1.0, droop); yy0 = cy - ry * 0.3 - j * 2.5
            m = EC.rot_ell(cv, cx - rx * 0.6 - 3, yy0, 6.6 - j, 2.6, ang)
            cv.paint(m, gl("cream4")); cv.paint(m & (cv.yy > yy0), _col(sick, "cream2", "sick0")); cv.solid |= m
    tail = None
    if br == "lumi":
        wings = [(-0.78, -0.10, 7.8, 3.3, 166), (-0.66, -0.36, 7.0, 2.9, 142)]
        if el: wings = [(-0.70, -0.34, 8.6, 3.4, 124)] + wings
        for wi, (bxo, byo, a, b, ang) in enumerate(wings):
            ang = ang + 7 * flap * (1 if wi % 2 == 0 else -0.7) - 14 * min(1.0, droop)
            a, b = a * k * (1.05 if el else 1.0), max(2.0, b * k * (1.1 if el else 1.0))
            bx0, by0 = cx + bxo * rx, cy + byo * ry
            d = (math.cos(math.radians(ang)), -math.sin(math.radians(ang)))
            wc = (bx0 + d[0] * a * 0.62, by0 + d[1] * a * 0.62)
            m = EC.rot_ell(cv, wc[0], wc[1], a, b, ang); cv.paint(m, "drop"); cv.solid |= m
            cv.paint(m & EC.rot_ell(cv, wc[0] + d[0] - 0.6, wc[1] + d[1] - 0.6, a - 2.2 * k, b - 1.6 * k, ang), "white")
            cv.put(wc[0] + d[0] * a * 0.8, wc[1] + d[1] * a * 0.8, "drop_d")
        tx, ty = G["tailc"]
        trx, trY = 7.4 * k * (1.15 if el else 1.0), 6.6 * k * (1.15 if el else 1.0)
        tail = cv.ell(tx, ty, trx, trY); cv.paint(tail, gl("egg_dark")); cv.solid |= tail
    if br == "radiant":
        wag = 0.6 * math.sin(ph * 2.0); r = 3.6 if el else 3.2; tx, ty = cx - rx - 1.0, cy + 1.5 - wag
        m = cv.ell(tx, ty, r, r * 0.9) | cv.ell(tx - r * 0.6, ty - r * 0.8, r * 0.7, r * 0.7)
        A.shade(cv, m, tx, ty, r, r, ramp); cv.solid |= m
        cv.paint(cv.ell(tx - r * 0.75, ty - r * 1.05, r * 0.5, r * 0.5) & m, gl("glow"))
        perk = 0.6 if bud > 1.1 else 0.0
        for s in (-1, 1):
            EC.ear(cv, cx + s * rx * 0.58, cy - ry * 0.70 + droop * 0.8, (7.5 if el else 6.8) - droop * 1.8 + perk, 5.4, s * (2.0 + droop * 1.6), (R[1] if sick else "cream2", gl("glow")))
    if br == "soft":
        EC.leaf(cv, cx - rx - 1.6, cy + ry * 0.35 - 0.5 * math.sin(ph * 2), 3.8 if el else 3.4, 1.8, 200 + 8 * math.sin(ph * 2), gl("leaf"), _col(sick, "leaf_d", "sick0"))
    if br == "dust":
        wag = 0.5 * math.sin(ph * 2.0)
        for (dx, dy, r) in ((-rx - 0.6, ry * 0.45, 2.6), (-rx - 2.8 - wag, ry * 0.15, 2.0), (-rx - 1.2, ry * -0.1 - wag, 1.6)):
            m = cv.ell(cx + dx, cy + dy, r, r); A.shade(cv, m, cx + dx, cy + dy, r, r, ramp); cv.solid |= m
    # ---------------- feet / arms
    frx, fry = f["feet"]; fi = p.get("feet_in", 0.0); fl = p.get("flift", (0, 0))
    for i, s in enumerate((-1, 1)):
        m = cv.ell(cx + s * rx * 0.45 * (1 - fi), ground + 0.35 - fl[i], frx, fry); cv.paint(m, "orange"); cv.solid |= m
        cv.paint(m & (cv.yy >= int(ground + 0.6 - fl[i])), "orange_d")
    arms = p.get("arms", "down"); armc = "peach0" if (br == "lumi" and not sick) else R[2]
    if arms != "none":
        ar = f["arm"]
        for s in (-1, 1):
            if arms == "down": ax, ay = cx + s * (rx - 0.2), cy + ry * 0.2
            elif arms == "up": ax, ay = cx + s * (rx - 0.4), cy - ry * 0.35 - 1
            else: ax, ay = cx + s * (rx - 0.6), cy + ry * (0.1 if s < 0 else 0.0)
            m = cv.ell(ax, ay, ar, ar); cv.paint(m, armc); cv.solid |= m
    # ---------------- body
    bm = cv.ell(cx, cy, rx, ry); N, rb = f["N"], f["rb"]
    for i in range(N):
        th = 2 * math.pi * (i + 0.5) / N; sn = math.sin(th)
        if sn > 0.78: continue
        if f["skip_top"] and sn < -0.8 and abs(math.cos(th)) < 0.35: continue
        wob = 0.3 * math.sin(ph * 2 + min(i, N - 1 - i) * 1.3)
        r_b = rb * (1 + 0.08 * math.cos(2 * th))
        bm |= cv.ell(cx + (rx - r_b * 0.45 + wob) * math.cos(th), cy + (ry - r_b * 0.45 + wob) * sn, r_b, r_b)
    kk = A.shade(cv, bm, cx, cy, rx, ry, ramp, 0.15)
    bdx, byk, brx, bry = f["belly"]
    cv.a[cv.ell(cx + bdx, cy + ry * byk, rx * brx, ry * bry) & bm & (kk <= 1)] = IDX[R[2]]
    for (tx_, ty_) in EC.LF_TICKS[:f["nt"]]:
        px, py = cx + tx_ * rx * 0.95, cy + ty_ * ry * 0.95
        cv.put(px, py, R[0]); cv.put(px + 1, py + 1, R[0]); cv.put(px - 1, py - 1, R[0])
    cv.solid |= bm
    if not sick:
        if br == "lumi":
            hx, hy = cx - rx * 0.30, cy - ry * 0.58
            for dx, dy in ((0, 0), (1, 0), (2, 0), (-1, 1), (0, -1)): cv.put(hx + dx, hy + dy, "white")
        else: EC.lf_hi(cv, cx, cy, rx, ry, col="white" if br == "dust" else "cream4")
    # ---------------- head features (solid, outlined together)
    if br == "radiant":
        for (px_, py_) in G["stem"]:
            for q in range(2):
                x = int(round(px_ - 0.5 + q)); y = int(round(py_))
                if 0 <= x < S and 0 <= y < S: cv.a[y, x] = IDX[("sick0" if sick else ("orange", "orange_d")[q])]; cv.solid[y, x] = True
    if br == "soft":
        for (px_, py_) in G["stem"]:
            for q in range(2):
                x = int(round(px_ - 0.5 + q)); y = int(round(py_))
                if 0 <= x < S and 0 <= y < S: cv.a[y, x] = IDX[("sick0" if sick else ("orange", "orange_d")[q])]; cv.solid[y, x] = True
        tx, ty = G["stem"][-1]; dr = min(1.0, droop)
        for s in (-1, 1):
            m = cv.ell(tx + s * 2.6, ty - 1.2 + dr * 1.2, 1.9, 1.5); cv.paint(m, "sick1" if sick else "orange"); cv.solid |= m
            cv.put(tx + s * 1.6, ty - 1.2 + dr * 1.2, "sick0" if sick else "orange_d")
        for s in (-1, 1):   # 垂葉耳（身前）
            ang = (-60 if s > 0 else 240) + (s * -25 * dr) + (s * 10 if bud > 1.1 else 0)
            EC.leaf(cv, cx + s * rx * 0.86, cy - ry * 0.22 + dr, 4.0 if el else 3.6, 1.9, ang, gl("leaf"), _col(sick, "leaf_d", "sick0"))
    if br == "lumi":
        for pts in G["ants"]:
            for (x, y) in pts:
                xi, yi = int(round(x)), int(round(y))
                if 0 <= xi < S and 0 <= yi < S: cv.a[yi, xi] = IDX["outline"]; cv.solid[yi, xi] = True
    if br == "dust":
        for (bx, pts) in ((0, ((0, 0), (0, -1), (1, -2), (2, -3), (2, -4), (1, -5))), (-4, ((0, 0), (-1, -1), (-2, -2), (-2, -3))), (4, ((0, 0), (1, -1), (1, -2)))):
            for (dx, dy) in pts:
                off = int(round(sway * (-dy) / 5)) if dy <= -2 else 0
                if droop > 0.5 and dy <= -2: off += int(round(min(droop, 1.5) * (-dy) / 2)); dy = max(dy, -3)
                x, y = int(cx + 1 + bx + dx + off), int(cy - ry + 1 + dy)
                if 0 <= x < S and 0 <= y < S: cv.a[y, x] = IDX["sick1" if sick else "peach1"]; cv.solid[y, x] = True
    cv.outline()
    # ---------------- post-outline details
    if br == "radiant":
        for (dx, dy) in ((0, 3), (-1, 4), (1, 4)): cv.put(cx + dx, cy - ry + dy, "sick0" if sick else "orange")   # 額日紋
    if br == "lumi":
        tx, ty = G["tailc"]; seg = tail & ~bm
        for ox in (-0.5 * k, 2.8 * k):
            cv.a[seg & (np.abs(cv.xx + .5 - (tx + ox) - (cv.yy + .5 - ty) * 0.35) < 0.6)] = IDX["outline"]
        free = seg & (cv.a != IDX["outline"])
        if not sick:
            pulse = 1.0 + 0.08 * ((tw % 3) - 1) + 0.1 * (bud - 1.0)
            cv.a[cv.ell(tx - 1.6 * k, ty + 0.4 * k, 4.8 * k * (1.15 if el else 1) * pulse, 4.4 * k * (1.15 if el else 1) * pulse) & free] = IDX["egg_shade"]
            if droop < 0.8: cv.a[cv.ell(tx - 2.6 * k, ty, 2.4 * k * pulse, 2.4 * k * pulse) & free] = IDX["cyan"]
        for bi, (x, y) in enumerate(G["bulbs"]):
            r = 2.2 * k ** .5 * (1.1 if el else 1.0)
            m = cv.ell(x, y, r, r); cv.paint(m, "sick1" if sick else "egg_shade")
            if not sick and (droop < 0.8 or bi == 0) and (tw + bi) % 4 != 3:
                cv.put(x - .4, y - .4, "cyan"); cv.put(x + .6, y - .4, "cyan")
            cv.a[EC.ring(m) & (cv.a == 0)] = IDX["outline"]
        DOTS = [(-13, -3, 1), (-7, -10, 1), (-15, 4, 0), (-9, 3, 0), (-2, -12, 0), (5, -11, 1), (-12, 9, 0), (12, -6, 0)]
        dpos = []
        for i, (dx, dy, big) in enumerate(DOTS):
            x, y = cx + dx * rx / 19.0, cy + dy * ry / 16.0; xi, yi = int(round(x)), int(round(y))
            if not (0 <= xi < S and 0 <= yi < S) or not bm[yi, xi] or cv.a[yi, xi] == IDX["outline"]: continue
            on = (i + tw) % 3 != 0 and not sick
            cv.put(x, y, "cyan" if on else ("sick0" if sick else "peach2")); dpos.append((xi, yi))
            if big and i % 2 == 0 and on:
                for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if bm[yi + oy, xi + ox] and cv.a[yi + oy, xi + ox] != IDX["outline"]: cv.a[yi + oy, xi + ox] = IDX["egg_shade"]
        if el and len(dpos) >= 4 and not sick:
            for (pp, q) in ((0, 1), (1, 3)):
                (x1, y1), (x2, y2) = dpos[pp], dpos[q]
                for t in np.linspace(0.3, 0.7, 3):
                    xi, yi = int(round(x1 + (x2 - x1) * t)), int(round(y1 + (y2 - y1) * t))
                    if bm[yi, xi] and cv.a[yi, xi] not in (IDX["outline"], IDX["cyan"], IDX["egg_shade"]): cv.a[yi, xi] = IDX["egg_dark"]
    if br == "soft":
        EC.spots(cv, bm, [(-0.62, -0.25), (-0.3, -0.6), (0.62, -0.42), (-0.78, 0.25), (0.1, -0.7)], "sick0" if sick else "cream3", cx, cy, rx, ry, big=True)
        bx_, by_ = G["bulb"]; r = G["br_"] * (0.92 + 0.08 * min(bud, 1.4))
        if sick:
            m = cv.ell(bx_, by_, r, r); cv.paint(m, "sick1"); EC.outl(cv, m)
        else:
            m = cv.ell(bx_, by_, r + 0.9, r + 0.9); cv.paint(m, "glow"); cv.paint(cv.ell(bx_, by_, r, r), "glow" if bud < 0.8 else "glow_mid")
            if bud >= 0.8:
                for (ox, oy) in ((-0.5, -0.5), (0.5, -0.5), (-0.5, 0.5)): cv.put(bx_ + ox, by_ + oy, "glow_core")
            else: cv.put(bx_ - 0.5, by_ - 0.5, "glow_mid")
            EC.outl(cv, m)
        if el:   # 花冠
            for i, a in enumerate(range(-165, 0, 33)):
                ar = math.radians(a); px, py = cx + math.cos(ar) * rx * 0.62, cy - ry * 0.78 + math.sin(ar) * 2.6
                if abs(px - bx_) < 2.5: continue
                pm = cv.ell(px, py, 2.2, 2.2); cv.paint(pm, "sick1" if sick else ("blush" if i % 2 else "cream4")); cv.put(px, py, "sick0" if sick else "glow"); EC.outl(cv, pm)
    if br == "radiant":
        bx_, by_ = G["bulb"]
        if sick:
            m = cv.ell(bx_, by_, 3.0 * G["kk"] + 1, 3.0 * G["kk"] + 1); cv.paint(m, "sick1"); cv.put(bx_ - 0.5, by_ - 0.5, "cream2"); EC.outl(cv, m)
        else: draw_sun(cv, bx_, by_, G["kk"], bud, el, tw, droop, p.get("sunk", 1.0))
        if el:
            ux, uy = cx + 1, cy + ry * 0.62
            for (dx, dy, c) in ((0, 0, "glow_core"), (1, 0, "glow"), (-1, 0, "glow"), (0, 1, "glow"), (0, -1, "glow"), (2, 0, "orange"), (-2, 0, "orange")):
                xi, yi = int(ux + dx), int(uy + dy)
                if 0 <= xi < S and 0 <= yi < S and bm[yi, xi] and cv.a[yi, xi] not in (IDX["outline"], IDX["blush"]): cv.a[yi, xi] = IDX["sick1" if sick else c]
    if br == "dust":
        EC.spots(cv, bm, [(-0.62, 0.15), (-0.3, 0.62), (0.62, 0.5), (-0.75, 0.42), (0.8, 0.05)], "sick0" if sick else "peach0", cx, cy, rx, ry)
    # ---------------- face (old-clip templates)
    fcx, ey, eoff, my, bx, by, ho = A.face_geo(form, cx, cy, rx, ry)
    if br == "dust":   # 眼鏡推咗上額頭（body 層，唔遮眼）
        gr = 2.6 if el else 2.3; gy = cy - ry * 0.52 + (0.6 if droop > 0.8 else 0)
        for s in (-1, 1):
            ex, gyy = cx + 1 + s * rx * 0.36, gy + (0 if s > 0 else 0.6)
            lm = cv.ell(ex, gyy, gr, gr * 0.85); rg = lm & ~cv.ell(ex, gyy, gr - 1.0, gr * 0.85 - 1.0)
            cv.a[lm & ~rg] = IDX["sick1" if sick else "cyan"]; cv.a[rg] = IDX["outline"]; cv.put(ex - 0.6, gyy - 0.6, "white")
        for x in range(int(round(cx + 1 - rx * 0.36 + gr - 0.5)), int(round(cx + 1 + rx * 0.36 - gr + 1))): cv.put(x, gy, "outline")
    cm = dict(A.CMX)
    if br == "lumi": cm["w"] = "cyan"
    ET, MT = A.EYE_TPL["L"], A.MOUTH_TPL["L"]
    eyes = p.get("eyes", "open"); mouth = p.get("mouth", "smile")
    if eyes == "sick":
        bt.draw_tmpl_c(cv, fcx - eoff, ey, ET["sickL"], cm); bt.draw_tmpl_c(cv, fcx + eoff, ey, ET["sickR"], cm)
    elif eyes != "none":
        for s in (-1, 1): bt.draw_tmpl_c(cv, fcx + s * eoff, ey, ET[eyes], cm)
    if mouth != "none": bt.draw_tmpl_c(cv, fcx, my, MT[mouth], cm)
    if p.get("blush", True):
        brx, bry = f["br"]
        for s in (-1, 1):
            m = cv.ell(fcx + s * bx + M.FACE[0], by + M.FACE[1], brx, bry)
            cv.a[m & bm & (cv.a != IDX["outline"])] = IDX["sick0" if sick else "blush"]
    # ---------------- lamps in front (dust hand lamp + elder orbit)
    if br == "dust":
        lx, ly = G["bulb"]
        if sick: m = cv.ell(lx, ly, 1.8, 1.8); cv.paint(m, "sick1"); EC.outl(cv, m)
        else:
            r = (1.9 if el else 1.6) * (0.9 + 0.1 * min(bud, 1.3))
            EC.glow_bulb(cv, lx, ly, r, core=bud >= 0.8)
        if el:
            hx_, hy_ = G["bulb2"]; hy0 = cy - ry - 3.5
            for i, t in enumerate(np.linspace(0, 2 * math.pi, 22, endpoint=False)):
                x, y = cx + 1 + math.cos(t + tw * 0.29) * 9, hy0 + math.sin(t + tw * 0.29) * 2.6
                xi, yi = int(round(x)), int(round(y))
                if 0 <= xi < S and 0 <= yi < S and cv.a[yi, xi] == 0: cv.put(x, y, "peach1" if i % 3 else ("sick1" if sick else "glow_mid"))
            if sick: m = cv.ell(hx_, hy_, 2.0, 2.0); cv.paint(m, "sick1"); EC.outl(cv, m)
            else: EC.glow_bulb(cv, hx_, hy_, 2.2 * (0.9 + 0.1 * min(bud, 1.3)))
        elif not sick:   # 守夜者微塵：身邊兩粒飄塵（逐幀上下飄）
            cv.put(cx - rx - 5, cy - ry * 0.6 + (tw % 2), "peach1"); cv.put(cx - rx - 4, cy - ry * 0.8 - (tw % 2), "peach2")
    # ---------------- elder aura (animated dotted)
    if el and not sick:
        col, col2 = {"radiant": ("glow", "glow_core"), "soft": ("blush", "cream4"), "lumi": ("egg_shade", "cyan"), "dust": ("peach2", "glow_mid")}[br]
        aura(cv, col, col2, tw)
        if br == "lumi" and droop < 0.8:
            for (x, y) in ((S - 5, 6), (S - 4, 26)):
                if (tw % 2 == 0 and y == 6) or (tw % 2 == 1 and y == 26): EC.sparkle(cv, x, y, "cyan", "egg_shade")
                else: cv.put(x, y, "egg_shade")
        if br == "soft":
            for i, (x, y) in enumerate(((4, 10), (S - 5, 15), (S - 7, 4))):
                yy = y + (tw + i) % 3
                cv.put(x, yy, "blush"); cv.put(x + 1, yy, "blush"); cv.put(x, yy + 1, "blush_d")
        clean_edge(cv)
    a0 = cv.a.copy()
    for fx_ in p.get("extras", []): fx_(cv, cx, cy, rx, ry)
    return A.keep_fx_inside(a0, cv.a)

def draw_sun(cv, tx, by, kk, bud, el, tw, droop, sunk=1.0):
    """= lf_sun（燦光放射燈）pose-aware：bud 縮放、twinkle 交替長短輻條、droop 收細"""
    rr = 4.4 * kk * (1.15 if el else 1.0) * (0.9 + 0.1 * min(bud, 1.4)) * (0.85 if droop > 0.8 else 1.0)
    angs = [-170, -150, -130, -110, -90, -70, -50, -30, -10]
    if droop < 0.8:
        for i, a in enumerate(angs):
            lng = (10.5 if (i + tw) % 2 == 1 else 12.5) * kk * (1.12 if el else 1.0) * (0.8 + 0.2 * min(bud, 1.3))
            if i in (0, 8): lng *= 0.75
            lng *= sunk
            ar = math.radians(a); steps = int(lng)
            for s_ in range(int(rr), steps + 1):
                cv.put(tx + math.cos(ar) * s_, by + math.sin(ar) * s_, "glow_mid" if s_ < steps else "glow_core")
            cv.put(tx + math.cos(ar) * (steps + 1), by + math.sin(ar) * (steps + 1), "glow_warm")
    cv.paint(cv.ell(tx, by, rr + 1.4 * kk, rr + 1.4 * kk), "glow"); cv.paint(cv.ell(tx, by, rr, rr), "glow_mid")
    cv.paint(cv.ell(tx - .4, by - .4, max(1.0, rr - 1.4 * kk), max(1.0, rr - 1.4 * kk)), "glow_core")
    if droop < 0.8:
        for j, (dx, dy) in enumerate(((-16, -4), (15, -6))):
            x, y = tx + dx * kk, by + dy * kk; cv.put(x, y, "glow_core")
            if (tw + j) % 2 == 0:
                for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)): cv.put(x + ox, y + oy, "glow_mid")

def aura(cv, col, col2, tw):
    s = cv.a > 0; d1 = EC.dil(s); r = EC.dil(d1) & ~d1
    pat = ((cv.xx * 2 + cv.yy + tw) % 5 == 0) & (cv.yy < cv.n - 9)
    cv.a[r & pat & (cv.a == 0)] = IDX[col]
    r2 = EC.dil(EC.dil(d1)) & ~EC.dil(d1); cv.a[r2 & ((cv.xx * 3 + cv.yy + 2 * tw) % 7 == 0) & (cv.yy < cv.n - 9) & (cv.a == 0)] = IDX[col2]

def clean_edge(cv, m=2):
    """aura／星點唔准近邊 m px（之後仲有 shear／pend）"""
    S = cv.n; e = np.zeros((S, S), bool); e[:m] = e[-m:] = True; e[:, :m] = e[:, -m:] = True
    lab = cv.a.copy(); iso = (cv.a > 0) & ~EC.dil(cv.solid)
    cv.a[e & iso] = 0

_prev_render = A.render_evo
def render_evo2(form, p):
    return render_adult(form, p) if form in NEW else _prev_render(form, p)
A.render_evo = render_evo2

# ============================================================ anchors / kit / build
_prev_anchors = A.evo_anchors
def anchors(form, p, vis=True):
    out = _prev_anchors(form, p, vis)
    if form in NEW:
        G = geo(form, p); sx = lambda y: L._shear_x(form, p, y)
        for key in ("bulb", "bulb2", "tail"):
            if key in G:
                x, y = int(math.floor(G[key][0])), int(math.floor(G[key][1])); out[key] = [x + sx(y), y]
        fv = out.pop("faceVisible"); out["faceVisible"] = fv
    return out

def build_kit(form):
    kit = A.build_kit(form)
    if form in NEW and FORMS[form]["branch"] == "lumi":   # 螢絨眼高光＝fly_core（同 lumi 64 kit）
        for n, (a, pv) in list(kit.items()):
            if n.startswith("eyes_"): b = a.copy(); b[a == IDX["cream4"]] = IDX["cyan"]; kit[n] = (b, pv)
    return kit

def form_order(form):
    if form in STILL: return list(STILL_ORDER)
    o = A.ORDER_STD + A.ORDER_NEW
    if FORMS[form]["branch"] == "dust": o += S3_DUST
    return o

def meta(form, clip):
    if clip in S3.S3_META: m = S3.S3_META[clip]; return (m[0], m[1], m[2], m[3], m[4])
    return A.meta(clip)

def build_form(form):
    A.CUR[0] = form
    C = M.clips(form); NC, NFACE, NVIS = L.new_clips(form)
    if FORMS[form]["branch"] == "dust" and form in GUARD:
        C3, F3 = S3.s3_clips(form); NC = dict(NC); NFACE = dict(NFACE); NC.update(C3); NFACE.update(F3)
    kit = build_kit(form); order = form_order(form); clips = {}
    for clip in order:
        new = clip in NC; src = NC[clip] if new else C[clip]
        c = dict(noface=[], full=[], overlay=[], anchors=[], new=new)
        for kf, p in enumerate(src):
            p = dict(p); p["_k"] = kf
            if clip != "idle": p = M.render_fit(form, p, f"{clip}_{kf + 1:02d}")
            if new:
                body = L.body_render(form, p)
                while p.get("rot") and A.touches(body):
                    p["rot"] = p["rot"] - 1; M.FIT_LOG.append((form, f"{clip}_{kf + 1:02d}", ["rot-1"])); body = L.body_render(form, p)
                for _ in range(3):   # pend 吊擺掂邊 → 收細擺幅
                    if not (p.get("pend") and A.touches(body)): break
                    p["pend"] = p["pend"] - (1 if p["pend"] > 0 else -1); M.FIT_LOG.append((form, f"{clip}_{kf + 1:02d}", ["pend"])); body = L.body_render(form, p)
                for _ in range(8):   # 仲掂邊：掂底 → lift+1；掂頂 → 燦光縮太陽輻條 sunk／否則 lift-1
                    if not A.touches(body): break
                    ys = np.nonzero(body.any(1))[0]; S_ = body.shape[0]
                    if ys.max() >= S_ - 1 and ys.min() >= 2: p["lift"] = p.get("lift", 0) + 1; tagf = "lift+1"
                    elif ys.min() <= 0 and FORMS[form]["branch"] == "radiant" and p.get("sunk", 1.0) > 0.6: p["sunk"] = p.get("sunk", 1.0) - 0.1; tagf = "sunk"
                    elif ys.max() >= S_ - 1 and FORMS[form]["branch"] == "radiant" and p.get("sunk", 1.0) > 0.6: p["sunk"] = p.get("sunk", 1.0) - 0.1; p["lift"] = p.get("lift", 0) + 1; tagf = "sunk+lift"
                    elif ys.min() <= 0: p["lift"] = p.get("lift", 0) - 1; tagf = "lift-1"
                    else: break
                    M.FIT_LOG.append((form, f"{clip}_{kf + 1:02d}", [tagf])); body = L.body_render(form, p)
                an = A.pend_rot(form, p, anchors(form, p, NVIS.get(clip, [True] * 99)[kf]), clip in L.PIVOT_OVERRIDE)
                face = NFACE[clip][kf]; an["face"] = dict(face) if face else None
                full = L.compose_face(body, an, face, kit)
            else:
                full = M.render(form, p); body = M.render(form, L.noface_params(p))
                an = anchors(form, p, True)
                eo = p.get("eyes", "open"); mo = p.get("mouth", "smile")
                an["face"] = dict(eyes=L.OLD_EYE.get(eo, eo), gaze="C", mouth=L.OLD_MOUTH.get(mo, mo), src=f"{eo}/{mo}")
            ov = np.where(full != body, full, 0).astype(np.uint8)
            c["noface"].append(body); c["full"].append(full); c["overlay"].append(ov); c["anchors"].append(an)
        clips[clip] = c
    A.CUR[0] = None
    return order, clips, kit

# ============================================================ io
def fsize(form): return FORMS[form]["S"]
def fpiv(form): S = fsize(form); return (S // 2, S - 3)

def write_files(form, order, clips, kit):
    d = os.path.join(OUT, form)
    if os.path.isdir(d): shutil.rmtree(d)
    for s in ("frames", "layers", "emissive", "kit"): os.makedirs(os.path.join(d, s), exist_ok=True)
    for clip in order:
        c = clips[clip]
        for kf in range(len(c["full"])):
            n = f"{clip}_{kf + 1:02d}"
            to_img(c["full"][kf], form).save(os.path.join(d, "frames", n + ".png"))
            to_img(c["noface"][kf], form).save(os.path.join(d, "layers", n + "_noface.png"))
            to_img(c["overlay"][kf], form).save(os.path.join(d, "layers", n + "_faceov.png"))
            emis_img(c["full"][kf], form).save(os.path.join(d, "emissive", n + "_emissive.png"))
            emis_img(c["noface"][kf], form).save(os.path.join(d, "emissive", n + "_noface_emissive.png"))
    for name, (a, pv) in kit.items(): to_img(a, form).save(os.path.join(d, "kit", name + ".png"))
    f = FORMS[form]; br = f["branch"]
    bk = {"lumi": "bulb = 前觸角燈頭、bulb2 = 後觸角燈頭" + ("（靜光第三支觸角唔另出錨點）" if f["elder"] else "") + "、tail = 尾燈中心",
          "radiant": "bulb = 頭頂太陽燈中心", "soft": "bulb = 頭頂柔光燈芽中心",
          "dust": "bulb = 手揸小燈中心" + ("、bulb2 = 頭頂軌道吊燈中心" if f["elder"] else "")}[br]
    fa = {"version": 1, "form": form, "frameSize": f["S"], "coords": "frame-local px, origin = frame top-left, y down",
          "pivotPx": list(fpiv(form)), "pivotOverride": {"picked_up": "grab"}, "palette": f"../{PALFILE[f['pal']]}",
          "keys": "eyeL/eyeR/mouth = 五官錨點（kit piece pivot；已含面右移 1px）; head_r = 頭右上圖示; " + bk + "; faceVisible; face = 預設表情; grab = 頭頂拎點（picked_up，亦係 pivot）",
          "anchors": {clip: clips[clip]["anchors"] for clip in order}}
    p = os.path.join(d, f"face_anchors_{form}.json")
    with open(p, "w") as fh:
        head = {k_: v for k_, v in fa.items() if k_ != "anchors"}
        fh.write(json.dumps(head, ensure_ascii=False)[:-1] + ',\n "anchors":{\n')
        fh.write(',\n'.join('  ' + json.dumps(cl) + ':[\n' + ',\n'.join('   ' + json.dumps(a, ensure_ascii=False, separators=(",", ":")) for a in lst) + ']'
                            for cl, lst in fa["anchors"].items()) + '}}\n')
    json.load(open(p))

def write_atlas(form, order, clips, kit):
    piv = fpiv(form); items = []; anims = {}; f = FORMS[form]
    for clip in order:
        c = clips[clip]; fps, loop, lf, pr, intr = meta(form, clip)
        pov = "grab" if clip == "picked_up" else None
        pv = (lambda kf, c=c: tuple(c["anchors"][kf]["grab"])) if pov else (lambda kf: piv)
        extra = {"pivot": pov} if pov else {}
        if loop and lf: extra["loopFrom"] = lf
        if clip in L.HOLD_LAST_S: extra["holdLast_s"] = L.HOLD_LAST_S[clip]
        ff = [f"{clip}_{kf + 1:02d}" for kf in range(len(c["full"]))]
        nf = [f"{clip}_noface_{kf + 1:02d}" for kf in range(len(c["full"]))]
        for kf in range(len(ff)):
            items.append((ff[kf], c["full"][kf], pv(kf))); items.append((nf[kf], c["noface"][kf], pv(kf)))
        anims[clip] = {"frames": ff, "fps": fps, "loop": loop, **extra}
        anims[clip + "_noface"] = {"frames": nf, "fps": fps, "loop": loop, **extra}
    for name, (a, pv) in kit.items(): items.append((name, a, pv))
    pages = L.pack_pages(items)
    assert len(pages) == 1, f"atlas {form} must fit one 1024-wide page"
    W, H, pos = pages[0]; lut = {n: (a, pv) for n, a, pv in items}
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); emi = Image.new("RGBA", (W, H), (0, 0, 0, 0)); jf = {}
    for name, (x, y, w, h) in pos.items():
        a, pv = lut[name]
        A.paste_ex(img, to_img(a, form), x, y, w, h); A.paste_ex(emi, emis_img(a, form), x, y, w, h)
        jf[name] = {"frame": {"x": x, "y": y, "w": w, "h": h}, "rotated": False, "trimmed": False,
                    "spriteSourceSize": {"x": 0, "y": 0, "w": w, "h": h}, "sourceSize": {"w": w, "h": h},
                    "pivot": {"x": round(pv[0] / w, 4), "y": round(pv[1] / h, 4)}, "pivotPx": {"x": int(pv[0]), "y": int(pv[1])}}
    base = f"atlas_{form}"
    img.save(os.path.join(OUT, base + ".png")); emi.save(os.path.join(OUT, base + "_emissive.png"))
    en = EMIS_PALNAMES[f["pal"]]
    m = {"image": base + ".png", "emissive": base + "_emissive.png", "size": {"w": W, "h": H}, "scale": 1, "format": "RGBA8888",
         "padding": 2, "extrude": 1, "form": form, "name": f["name"], "stage": f["stage"], "branch": f["branch"], "frameSize": f["S"], "pivotPx": list(piv),
         "palette": PALFILE[f["pal"]], "emissiveColors": list(en),
         "pivotRule": f"body frames bottom-center {tuple(piv)}；picked_up* pivotPx = anchors.grab（頭頂拎點）；kit pieces pivotPx = anchor point",
         "note": f"{f['name']}：<clip>_NN 完整幀、<clip>_noface_NN 無臉身體、五官 eyes_*/mouth_*（4×5 L 級 kit" + ("，眼高光＝fly_core" if f["branch"] == "lumi" else "") +
                 f"）。{base}_emissive.png 同 layout，白＝發光（{'/'.join(en)}）。"}
    json.dump({"frames": jf, "animations": anims, "meta": m}, open(os.path.join(OUT, base + ".json"), "w"), indent=1, ensure_ascii=False)
    return W, H, len(items)

def contact(form, order, clips, kit, Z=4):
    S = fsize(form); cell = S * Z + 6; cols = max(max(len(clips[c]["full"]) for c in order), 9)
    LW = 150; rows = list(order) + ["face presets"]
    cs = Image.new("RGBA", (LW + cols * cell + 6, 30 + len(rows) * (cell + 4) + 6), BG); dr = ImageDraw.Draw(cs); fn = A.font(14)
    dr.text((8, 6), f"{form} {FORMS[form]['name']} {S}px  pivot {fpiv(form)}  {Z}x", fill=(255, 248, 224, 255), font=fn)
    for r, clip in enumerate(order):
        y = 30 + r * (cell + 4); fps = meta(form, clip)[0]
        dr.text((8, y + 8), clip, fill=(255, 248, 224, 255), font=fn)
        dr.text((8, y + 26), f"{len(clips[clip]['full'])}f {fps}fps", fill=(200, 196, 230, 255), font=A.font(11))
        for kf, a in enumerate(clips[clip]["full"]):
            cs.alpha_composite(to_img(a, form).resize((S * Z, S * Z), Image.NEAREST), (LW + kf * cell, y))
    y = 30 + len(order) * (cell + 4); dr.text((8, y + 8), "face presets", fill=(255, 248, 224, 255), font=fn)
    c = clips["idle"]
    for kf, nm2 in enumerate(["neutral", "happy", "sleepy", "surprised", "hungry", "cuddly", "grumpy", "curious", "wink"]):
        a = L.compose_face(c["noface"][0], c["anchors"][0], L.PRESETS[nm2], kit)
        cs.alpha_composite(to_img(a, form).resize((S * Z, S * Z), Image.NEAREST), (LW + kf * cell, y))
    os.makedirs(PRV, exist_ok=True); cs.save(os.path.join(PRV, f"{form}_contact_4x.png"))

def gifs(form, order, clips):
    d = os.path.join(PRV, "gif"); os.makedirs(d, exist_ok=True); S = fsize(form); Z = 6
    pick = [c for c in ["idle", "walk", "emo_happy", "sleep_loop", "wake", "picked_up", "smug_pose", "act_cool", "lookup_tip", "cheer_jump", "nuzzle_purr", "reunion_happy"] if c in order]
    for clip in pick:
        fr = []
        for a in clips[clip]["full"]:
            m = Image.new("RGBA", (S + 4, S + 4), BG); m.alpha_composite(to_img(a, form), (2, 2)); fr.append(m.resize(((S + 4) * Z, (S + 4) * Z), Image.NEAREST))
        L.save_gif(os.path.join(d, f"{form}_{clip}_6x.gif"), fr, meta(form, clip)[0], loops=2, hold_last_ms=300)

def batch_contact(res, forms, tag, title, Z=4):
    picks = ([("idle", 0), ("idle", 2), ("blink", 2), ("walk", 2), ("emo_happy", 1), ("sleep_loop", 0), ("eat", 2), ("droop", 3), ("sick", 0),
              ("picked_up", 1), ("smug_pose", 3), ("act_cool", 2), ("lookup_tip", 2), ("cheer_jump", 2), ("celebrate", 2)] if tag == "B" else
             [("idle", 0), ("idle", 1), ("idle", 2), ("idle", 3), ("blink", 2), ("emo_happy", 0), ("emo_happy", 1), ("fall_asleep", 2), ("sleep_loop", 0),
              ("sleep_loop", 2), ("wake", 1), ("wake", 3), ("picked_up", 1), ("picked_up", 4)])
    CELL = 52; LW = 150; W = LW + len(picks) * (CELL * Z + 4) + 8; H = 34 + len(forms) * (CELL * Z + 24) + 8
    cs = Image.new("RGBA", (W, H), BG); dr = ImageDraw.Draw(cs)
    dr.text((8, 8), title, fill=(255, 248, 224, 255), font=A.font(15))
    for r, form in enumerate(forms):
        order, clips, kit = res[form]; piv = fpiv(form); y0 = 34 + r * (CELL * Z + 24)
        dr.text((8, y0 + 40), FORMS[form]["name"], fill=(255, 248, 224, 255), font=A.font(18))
        dr.text((8, y0 + 66), f"{fsize(form)}px", fill=(200, 196, 230, 255), font=A.font(14))
        for kf, (clip, i) in enumerate(picks):
            i = min(i, len(clips[clip]["full"]) - 1); a = clips[clip]["full"][i]; x0 = LW + kf * (CELL * Z + 4)
            ox, oy = CELL // 2 - piv[0], CELL - 4 - piv[1]
            m = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0)); m.alpha_composite(to_img(a, form), (ox, oy))
            cs.alpha_composite(m.resize((CELL * Z, CELL * Z), Image.NEAREST), (x0, y0))
            dr.text((x0 + 4, y0 + CELL * Z + 2), f"{clip}_{i + 1:02d}", fill=(200, 196, 230, 255), font=A.font(11))
    cs.save(os.path.join(PRV, f"evo6_batch{tag}_contact_4x.png"))

# ============================================================ docs (re-read right before write; merge, additions only; atomic)
def atomic_write(path, text):
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".tmp_evo6bc_")
    with os.fdopen(fd, "w", encoding="utf-8") as fh: fh.write(text)
    os.chmod(tmp, 0o644); os.replace(tmp, path)

def backup(path):
    os.makedirs(BACK, exist_ok=True)
    dst = os.path.join(BACK, os.path.relpath(path, ROOT).replace("/", "__"))
    if not os.path.exists(dst): shutil.copy2(path, dst)

def update_docs(res, ainfo, forms, tag):
    p = os.path.join(MOT, "CLIPS.json"); backup(p)
    D = json.load(open(p, encoding="utf-8"))        # re-read immediately before write
    for form in forms:
        order, clips, kit = res[form]; f = FORMS[form]; W, H, n = ainfo[form]
        D["forms"][form] = {"name": f["name"], "stage": f["stage"], "branch": f["branch"], "evo6": True, "batch": tag, "frameSize": f["S"], "pivotPx": list(fpiv(form)),
            "atlas": f"../evo6/atlas_{form}.png", "json": f"../evo6/atlas_{form}.json", "emissive": f"../evo6/atlas_{form}_emissive.png",
            "atlasSize": [W, H], "atlasPieces": n, "frames": sum(len(clips[c]["full"]) for c in order),
            "palette": f"../evo6/{PALFILE[f['pal']]}", "emissiveColors": list(EMIS_PALNAMES[f["pal"]]),
            "faceAnchors": f"../evo6/{form}/face_anchors_{form}.json", "clips": order, "concept": "../evo6_concept/（v3 lumi feel）",
            "faceRig": True, "faceTier": "L 4×5", "hasBulb": True, "headRightAnchor": list(M.ANCH[form]["head_r"]), "potAnchor": list(M.ANCH[form]["pot"]),
            "sunAnchor": [0, 0], "kitPieces": sorted(kit),
            **({"std23": A.ORDER_STD, "liveliness": A.ORDER_NEW} if form in GUARD else {"mvp": STILL_ORDER, "std": [c for c in STILL_ORDER if c != "picked_up"], "liveliness": ["picked_up"]}),
            **({"s3": S3_DUST} if form in GUARD and f["branch"] == "dust" else {}),
            "note": BR_NOTE[(f["branch"], f["elder"])]}
    for c in D["clips"]:
        nme = c["name"]
        for form in forms:
            order, clips, kit = res[form]
            if nme in clips:
                c.setdefault("anchors", {})[form] = clips[nme]["anchors"]
                c[form] = {"frames": len(clips[nme]["full"]), "full": f"../evo6/{form}/frames/{nme}_NN.png", "noface": f"../evo6/{form}/layers/{nme}_NN_noface.png",
                           "faceov": f"../evo6/{form}/layers/{nme}_NN_faceov.png", "emissive": f"../evo6/{form}/emissive/{nme}_NN_emissive.png",
                           "atlasClip": nme, "nofaceClip": f"{nme}_noface", "atlas": f"../evo6/atlas_{form}.json"}
    key = "evo6B" if tag == "B" else "evo6C"
    D[key] = {"batch": tag, "forms": forms, "tool": "tools/build_evo6_animBC.py", "validator": "tools/validate_evo6_anim.py",
              "note": ("守夜者 44 ×4 分支（螢絨／燦光／柔光／微塵）：std23 ＋ 生命感 s1/s2（含 picked_up）；微塵另加 s3 nuzzle_purr／reunion_happy。" if tag == "B" else
                       "靜光 48 ×4 分支 MVP：idle、blink、emo_happy、fall_asleep／sleep_loop／wake、picked_up。"),
              "palettes": {"lumi": "../evo6/palette_lumi.json（emissive fly/fly_core）", "dust": "../evo6/palette_dust.json（lens＝鏡片，唔發光）", "radiant/soft": "../evo6/palette_base.json"},
              "rebuildNote": "build_tuanrong_liveliness_docs.py 重砌 CLIPS.json → 之後要再跑 build_lumi.py、build_tuanrong_live_s3.py、build_evo6_anim.py、build_evo6_animBC.py。"}
    atomic_write(p, json.dumps(D, indent=1, ensure_ascii=False))
    mp = os.path.join(MOT, "CLIPS.md"); backup(mp); md = open(mp, encoding="utf-8").read()
    a_, b_ = f"<!-- EVO6{tag}-START -->", f"<!-- EVO6{tag}-END -->"
    if a_ in md: md = md[:md.index(a_)].rstrip() + "\n\n" + md[md.index(b_) + len(b_):].lstrip()
    rows = []
    for form in forms:
        order, clips, kit = res[form]; W, H, n = ainfo[form]; tot = sum(len(clips[c]["full"]) for c in order)
        rows.append(f"| {FORMS[form]['name']} `{form}` | {fsize(form)} | {fpiv(form)} | {len(order)} | {tot} | `../evo6/atlas_{form}.png`（{W}×{H}，{n} 塊）＋ `_emissive` | {PALFILE[FORMS[form]['pal']]} |")
    title = "守夜者 44 ×4（batch B）" if tag == "B" else "靜光 48 ×4 MVP（batch C）"
    sec = (f"{a_}\n## 進化 6 階 {title}\n"
           "- 外觀＝`../evo6_concept/`（v3 lumi feel，lf5_* 畫法逐幀 pose-aware 重畫）；姿勢＝現有同名 clip，只換外觀層；4×5 L 級 kit；picked_up pivot＝grab。\n"
           "- 每幀 frames／layers（_noface／_faceov）／emissive；錨點 `../evo6/<form>/face_anchors_<form>.json`（bulb＝主燈；螢絨另有 bulb2／tail；靜光微塵 bulb2＝軌道吊燈）。\n"
           + ("- 微塵另加 s3：nuzzle_purr 4、reunion_happy 5。\n" if tag == "B" else "- MVP clip：" + "、".join(STILL_ORDER) + "。\n")
           + "\n| 形態 | px | pivot | clip | 幀 | atlas | 色盤 |\n|---|---|---|---|---|---|---|\n" + "\n".join(rows) + f"\n{b_}\n")
    if tag == "C" and "<!-- EVO6B-END -->" in md:
        i = md.index("<!-- EVO6B-END -->") + len("<!-- EVO6B-END -->"); md = md[:i] + "\n\n" + sec + md[i:]
    elif "<!-- EVO6A-END -->" in md:
        i = md.index("<!-- EVO6A-END -->") + len("<!-- EVO6A-END -->"); md = md[:i] + "\n\n" + sec + md[i:]
    else: md = md.rstrip() + "\n\n" + sec
    atomic_write(mp, md)

BR_NOTE = {
 ("lumi", False): "守夜者・螢絨：背後雙翼（拍翼跟 fluff／twinkle 相位）、分節尾燈（脈衝）、雙觸角燈頭、身上光點逐幀閃、面右移、眼高光 fly_core；emissive＝fly/fly_core。",
 ("radiant", False): "守夜者・燦光：額日紋、金尖耳（droop 垂／bud 企）、光尾（擺）、頭頂太陽放射燈（輻條長短交替閃）；emissive＝glow_core/glow_mid。",
 ("soft", False): "守夜者・柔光：垂葉耳（身前，droop 垂低）、奶油圓斑、葉尾（擺）、頭頂柔光燈芽＋橙葉。",
 ("dust", False): "守夜者・微塵：灰米 dust 色盤、亂翹呆毛、圓眼鏡推咗上額頭（自以為好醒）、手揸小燈（輕擺）、塵雲尾；鏡片 lens 唔發光；另加 s3 nuzzle_purr／reunion_happy。",
 ("lumi", True): "靜光・螢絨：第三對翼、第三支觸角、星座連線、大尾燈、螢光 aura（逐幀流動）。",
 ("radiant", True): "靜光・燦光：背後日輪光拱（光點流動）、雙金翼（拍）、胸前日徽、金光 aura。",
 ("soft", True): "靜光・柔光：背後葉翼（拍）、花冠、飄花瓣 aura（逐幀落）。",
 ("dust", True): "靜光・微塵（塵賢者）：紙頁翼（拍）、塵粒軌道環（轉）＋頭頂吊燈、aura。",
}

# ============================================================ main
def run(tag):
    forms = list(GUARD) if tag == "B" else list(STILL)
    res = {}; ainfo = {}; stats = {}
    for form in forms:
        res[form] = build_form(form); order, clips, kit = res[form]
        write_files(form, order, clips, kit); ainfo[form] = write_atlas(form, order, clips, kit)
        contact(form, order, clips, kit); gifs(form, order, clips)
        edge = [f"{c}_{kf + 1:02d}" for c in order for kf, a in enumerate(clips[c]["full"]) if A.touches(a)]
        stats[form] = {"clips": {c: len(clips[c]["full"]) for c in order}, "nClips": len(order), "frames": sum(len(clips[c]["full"]) for c in order),
                       "atlas": ainfo[form][:2], "pieces": ainfo[form][2], "edgeTouch": edge,
                       "fit_adjustments": [f"{b}:{'/'.join(c)}" for a, b, c in M.FIT_LOG if a == form]}
        print(form, "clips", len(order), "frames", stats[form]["frames"], "atlas", ainfo[form], "edge", edge, flush=True)
    title = ("團絨 evo6 batch B — 守夜者 44 ×4（螢絨／燦光／柔光／微塵，4x，同一地線）" if tag == "B" else "團絨 evo6 batch C — 靜光 48 ×4 MVP（4x，同一地線）")
    batch_contact(res, forms, tag, title)
    for key in ("lumi", "dust"):
        src = os.path.join(TR, "evo6_concept", f"palette_evo6_{key}.json"); shutil.copy(src, os.path.join(OUT, PALFILE[key]))
    pb = next(p for p in (os.path.join(MOT, "palette.json"), os.path.join(TR, "palette.json")) if os.path.exists(p))
    if not os.path.exists(os.path.join(OUT, "palette_base.json")): shutil.copy(pb, os.path.join(OUT, "palette_base.json"))
    if "--no-docs" not in sys.argv: update_docs(res, ainfo, forms, tag)
    json.dump(stats, open(os.path.join(OUT, f"_stats_batch{tag}.json"), "w"), indent=1, ensure_ascii=False)
    return res

if __name__ == "__main__":
    which = next((a for a in sys.argv[1:] if not a.startswith("--")), "BC")
    for t in which: run(t)
