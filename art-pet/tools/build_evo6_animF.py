#!/usr/bin/env python3
"""build_evo6_animF.py — 團絨 evo6 新支線 ×5 動畫（batch F1 水珠／F2 菇傘／F3 晶角／F4 月眠／F5 火苗）。
每條支線：守夜者 44（stage 5，pivot (22,41)）＋靜光 48（stage 6，pivot (24,45)），全套 41 clip／180 幀
（std23 ＋ 生命感 s1/s2（含 picked_up）＋ s3 nuzzle_purr／reunion_happy），同 batch B/C/D 標準：
frames／layers（_noface／_faceov）／emissive／kit／face_anchors（bulb＝燈中心）／atlas＋emissive atlas。
外觀＝evo6_concept/branches5（build_evo6_branches5.py，v3 lumi feel）逐幀按 pose 參數重畫（pose-aware）；
引擎／錨點／kit／atlas＝build_evo6_animBC.py（import 做 module，唔跑佢 main，冇改佢）。
分支動態：水珠 浮浮下（idle 身浮＋燈／泡泡上下）、菇傘 菇帽搖、晶角 晶光閃（逐幀換閃點）、月眠 渴瞓（半瞇眼／點頭、瞓覺燈漸暗）、火苗 火苗閃（逐幀高低搖）。
靜光 aura（＋大件發光飾物）瞓覺漸暗同靜光一樣：fall_asleep 0.8→0.2、sleep_loop 0.2。
Pillow＋numpy 程式逐像素繪製，原創，無 AI。alpha 0/255、無 AA、向右。
用法：python3 build_evo6_animF.py F1 [F2 ...] [--no-docs]
"""
import json, math, os, shutil, sys, datetime
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_evo6_animBC as BC
import build_evo6_branches5 as B5          # 分支色盤（EC.SWAPS 只喺 runtime 加，唔改檔）
A, L, M, EC, bt, S3 = BC.A, BC.L, BC.M, BC.EC, BC.bt, BC.S3
FORMS, IDX = BC.FORMS, BC.IDX
ROOT, TR, OUT, PRV, MOT = BC.ROOT, BC.TR, BC.OUT, BC.PRV, BC.MOT
BACK = os.path.join(ROOT, "_backups", "pre_evo6_branches5_anim_20261031"); BC.BACK = BACK

NB = ["tide", "shroom", "crystal", "moon", "ember"]
BATCH = {"F1": "tide", "F2": "shroom", "F3": "crystal", "F4": "moon", "F5": "ember"}
BNAME = {b: nm for (b, nm, *_r) in B5.BR5}
TRAIT = {b: t for (b, _n, t, *_r) in B5.BR5}
BODY = {"tide": (15, 3.2), "shroom": (14, 3.4), "crystal": (16, 3.2), "moon": (15, 3.3), "ember": (16, 3.3)}
MOTION = {"tide": "浮浮下：idle 身浮 1px、水珠燈逐幀上下、泡泡上升、肚波紋流、鰭耳／魚尾擺",
          "shroom": "菇帽搖：菇帽逐幀左右擺＋斜（帽邊一高一低）、細菇燈跟住晃、孢子飄",
          "crystal": "晶光閃：晶耳／晶燈／身上晶粉閃點逐幀輪住閃（glint）",
          "moon": "渴瞓：idle／生命感 clip 間中半瞇眼、睡帽尖跟住點頭；fall_asleep 月牙燈漸暗、sleep_loop 暗、wake 返光",
          "ember": "火苗閃：頭頂火苗燈／尾尖火／耳尖逐幀高低擺、火星點閃"}

# ============================================================ forms / palettes / ramps
def _formF(br, el):
    S = 48 if el else 44; rx, ry = (13.8, 11.6) if el else (12.9, 10.9); k = rx / 19; N, rbk = BODY[br]
    return dict(S=S, rx=rx, ry=ry, G=S - 3, ramp="g_" + br, N=N, rb=rbk * k, big=True, stem=0, k=k, skip_top=True,
                belly=(0.0, 0.32, 0.55, 0.50), nt=6, name=("靜光・" if el else "守夜者・") + BNAME[br], stage=6 if el else 5, tier="L",
                fdx0=1, fdy0=0.0, eo=0.40, br=(2.2, 1.3), arm=2.3 * k ** .5, feet=(2.4, 1.9), headk=(1.0, 0.85), pot=29 if el else 27,
                branch=br, elder=el, pal=br)
GUARD5 = {f"evo_guard_{b}": _formF(b, False) for b in NB}
STILL5 = {f"evo_still_{b}": _formF(b, True) for b in NB}
NEW5 = {**GUARD5, **STILL5}
A.EVO.update(NEW5); FORMS.update(NEW5)
BC.GUARD.update(GUARD5); BC.STILL.update(STILL5); BC.NEW.update(NEW5)
for b in NB:
    BC.PALFILE[b] = f"palette_{b}.json"
    sw = B5.SW5[b]
    BC.EMIS_NAMES[b] = ("glow_core", "glow_mid") + (() if b == "tide" else ("cyan",))
    BC.EMIS_PALNAMES[b] = tuple(sw[n][0] for n in BC.EMIS_NAMES[b])
    bt.RAMPS["g_" + b] = EC.RAMP["g_" + b] = ["egg_dark", "peach0", "peach1", "peach2"]
LAMP_NAMES = ("glow", "glow_mid", "glow_core")
for fid, f in NEW5.items():
    bt.RAMPS["sun_" + fid] = EC.RAMP["sun_" + fid] = ["peach0", "peach1", "peach2", "cream4"]
    _, S, _, rx, ry, cx, cy = L._geo(fid, {})
    L.HEAD_K[fid] = f["headk"]
    hx, hy = int(round(cx + f["headk"][0] * rx)), int(round(cy - f["headk"][1] * ry))
    M.ANCH[fid] = dict(head_r=(hx - S // 2, hy - (S - 3)), pot=(f["pot"], 0), sun=(0, 0))
_has_s3_prev = BC.has_s3
BC.has_s3 = lambda form: form in NEW5 or _has_s3_prev(form)      # 新支線守夜者都有 s3（全套 41 clip）

def q_of(p): return int(p.get("twinkle", 0)) + int(p.get("_k", 0))   # 逐幀相位（每個 clip 都會郁）
def _col(sick, c, alt="sick0"): return alt if sick else c

# ============================================================ clip tweaks（姿勢唔變，只加分支動態）
LAMP_SLEEP = {"fall_asleep": lambda k, n: round(1.0 - 0.75 * k / max(1, n - 1), 2), "sleep_loop": lambda k, n: 0.25,
              "wake": lambda k, n: round(0.25 + 0.75 * k / max(1, n - 1), 2)}
DROWSY_LIVE = ("sniff", "lookup", "turn_back", "smug_pose", "act_cool", "lookup_tip", "getup", "walk_drag", "sniff_itch")
_clips0, _new0 = M.clips, L.new_clips
def clips_F(form):
    C = _clips0(form)
    if form not in NEW5: return C
    br = FORMS[form]["branch"]; C = {c: [dict(p) for p in v] for c, v in C.items()}
    if br == "tide":    # 浮浮下：idle 身浮 0→1→1→0
        for i, p in enumerate(C["idle"]): p["lift"] = p.get("lift", 0) + (0, 1, 1, 0)[i % 4]
    if br == "moon":    # 渴瞓：idle_02 半瞇、walk 單數幀半瞇；燈瞓覺漸暗
        C["idle"][1]["eyes"] = "half"
        for i, p in enumerate(C["walk"]):
            if i % 2 == 1 and p.get("eyes", "open") == "open": p["eyes"] = "half"
        for c, fn in LAMP_SLEEP.items():
            for i, p in enumerate(C[c]): p["_lamp"] = fn(i, len(C[c]))
    return C
def new_F(form):
    NC, NF, NV = _new0(form)
    if form in NEW5 and FORMS[form]["branch"] == "moon":
        NF = {c: [dict(x) if x else x for x in v] for c, v in NF.items()}
        for c in DROWSY_LIVE:
            for i, fc in enumerate(NF.get(c, [])):
                if fc and i % 2 == 1 and fc.get("eyes") == "neutral" and not fc.get("eyesR"): fc["eyes"] = "sleepy"
    return NC, NF, NV
M.clips, L.new_clips = clips_F, new_F

# ============================================================ geometry（renderer 同錨點共用）
def moon_hat(cx, cy, rx, ry, el, sway, droop, ph, q):
    P = []; Lh = 1.12 if el else 1.0; nod = 0.7 * math.sin(ph * 2.0 + q * 0.9)
    for i in range(23):
        t = i / 22
        x = cx + 2.5 - (11.5 * Lh) * t ** 1.3 + (sway * 0.8 + nod) * t * t
        y = cy - ry + 1.2 - (12.0 * Lh) * math.sin(t * 2.1) + min(droop, 1.5) * t * t * 3.0 + max(0.0, nod) * t * t
        P.append((x, y, 5.6 * (1 - t) ** 1.2 + 0.8))
    return P
def geo_F(form, p):
    f = FORMS[form]; _, S, _, rx, ry, cx, cy = L._geo(form, p); k = f["k"]; el = f["elder"]; br = f["branch"]
    sway = p.get("sway", 0) * 0.5; droop = p.get("droop", 0); ph = p.get("fluff", 0.0); q = q_of(p); g = {}
    if br == "tide":
        pts = A.stem_pts(cx, cy - ry, int(round(5 * k)), 0.8, sway, droop * 0.8); tx, ty = pts[-1]
        bob = (0, -0.5, -1.0, -0.5)[q % 4] if droop < 0.8 else 0.4
        g.update(stem=pts, bulb=(tx + 0.5, ty - 2.2 + bob))
    elif br == "shroom":
        wob = 0.8 * math.sin(ph * 2.0 + q * 1.3) + sway * 0.6
        cw, ch = rx * (1.0 if el else 0.86), (6.4 if el else 5.4)
        capx, capy = cx + 0.8 + wob, cy - ry * 0.52 + min(1.0, droop) * 0.8
        pts = A.stem_pts(capx + 0.8, capy - ch + 0.6, 2, 0.4, sway * 0.6 + wob * 0.4, droop * 0.6); tx, ty = pts[-1]
        g.update(wob=wob, cw=cw, ch=ch, capx=capx, capy=capy, stem=pts, bulb=(tx, ty - 1.4))
    elif br == "crystal":
        pts = A.stem_pts(cx, cy - ry, int(round(4 * k)), 0.0, sway, droop * 0.8); tx, ty = pts[-1]
        g.update(stem=pts, bulb=(tx + 0.5, ty - 3.2))
    elif br == "moon":
        P = moon_hat(cx, cy, rx, ry, el, sway, droop, ph, q); ex, ey = P[-1]
        g.update(hat=P, bulb=(ex - 3.4, ey + 5.0))
    elif br == "ember":
        pts = A.stem_pts(cx, cy - ry, int(round(4 * k)), 0.0, sway, droop * 0.8); tx, ty = pts[-1]
        g.update(stem=pts, fb=(tx + 0.5, ty - 2.0), bulb=(tx + 0.5, ty - 3.0))
    return g
_geo_prev = BC.geo
BC.geo = lambda form, p: geo_F(form, p) if form in NEW5 else _geo_prev(form, p)

# ============================================================ drawing helpers
def put_stem(cv, pts, cols, w=2):
    S = cv.n
    for (px_, py_) in pts:
        for qq in range(w):
            x = int(round(px_ - (w - 1) / 2 + qq)); y = int(round(py_))
            if 0 <= x < S and 0 <= y < S: cv.a[y, x] = IDX[cols[min(qq, len(cols) - 1)]]; cv.solid[y, x] = True
def tpuff(cv, x, y, r, ramp, tip=None):
    m = cv.ell(x, y, r, r * 0.9) | cv.ell(x - r * 0.6, y - r * 0.8, r * 0.7, r * 0.7); A.shade(cv, m, x, y, r, r, ramp); cv.solid |= m
    if tip: cv.paint(cv.ell(x - r * 0.75, y - r * 1.05, r * 0.5, r * 0.5) & m, tip)
    return m
def lamp_cols(lvl):
    """燈色（瞓覺漸暗）：1＝glow/glow_mid/glow_core；0.5–0.99 冇 core；<0.5 只 glow（唔發光）"""
    if lvl >= 0.99: return ("glow", "glow_mid", "glow_core")
    if lvl >= 0.5: return ("glow", "glow_mid", "glow_mid")
    return ("glow", "glow", "glow")
AURA5 = {"tide": ("glow", "cyan", "egg_shade"), "shroom": ("cyan", "glow_mid", "peach0"), "crystal": ("glow", "cyan", "egg_shade"),
         "moon": ("cyan", "glow_mid", "egg_shade"), "ember": ("cyan", "glow_mid", "egg_shade")}
def aura5(cv, br, tw, lvl):
    col, col2, dim = AURA5[br]; s = cv.a > 0; d1 = EC.dil(s); r = EC.dil(d1) & ~d1
    if lvl >= 0.99:
        cv.a[r & ((cv.xx * 2 + cv.yy + tw) % 5 == 0) & (cv.yy < cv.n - 9) & (cv.a == 0)] = IDX[col]
        r2 = EC.dil(EC.dil(d1)) & ~EC.dil(d1); cv.a[r2 & ((cv.xx * 3 + cv.yy + 2 * tw) % 7 == 0) & (cv.yy < cv.n - 9) & (cv.a == 0)] = IDX[col2]
    else:
        per = 8 if lvl >= 0.4 else 13; c = col if lvl >= 0.4 else dim
        cv.a[r & ((cv.xx * 2 + cv.yy + tw) % per == 0) & (cv.yy < cv.n - 9) & (cv.a == 0)] = IDX[c]
def free_put(cv, x, y, c):
    xi, yi = int(round(x)), int(round(y))
    if 2 <= xi < cv.n - 2 and 2 <= yi < cv.n - 3 and cv.a[yi, xi] == 0: cv.a[yi, xi] = IDX[c]
def fsparkle(cv, x, y, c0, c1):
    free_put(cv, x, y, c0)
    for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)): free_put(cv, x + ox, y + oy, c1)
def drop_bulb(cv, x, by, r, cols):
    m = cv.ell(x, by, r + 0.8, r + 0.8)
    for j in range(int(r * 2.2) + 1):
        t = j / (r * 2.2); half = (r + 0.8) * (1 - t) ** 1.3
        m |= (np.abs(cv.xx + .5 - x) <= half) & (cv.yy == int(round(by - j)))
    cv.paint(m, cols[0]); cv.paint(m & cv.ell(x, by, r - 0.3, r - 0.3), cols[1])
    for (ox, oy) in ((-1, -1), (-1, -2), (0, -1)): cv.put(x + ox, by + oy, cols[2])
    EC.outl(cv, m); return m
def diamond(cv, x, y, a, b, cols, glint):
    m = (np.abs(cv.xx + .5 - x) / a + np.abs(cv.yy + .5 - y) / b) <= 1.0
    cv.paint(m, cols[0]); cv.paint(m & (cv.yy + .5 < y) & (cv.xx + .5 < x + 0.6), cols[1])
    cv.paint(m & (np.abs(cv.xx + .5 - x) < 0.6), cols[2]); EC.outl(cv, m)
    if glint is not None:   # 閃：燈尖旁邊一粒十字星，逐幀換邊
        gx, gy = [(x + a + 1.5, y - b + 0.5), (x - a - 1.2, y - 0.5), (x + a + 0.8, y + b - 1.0)][glint % 3]
        fsparkle(cv, gx, gy, "glow_core", "cyan")
    return m
def crescent(cv, x, y, r, cols, off=(-1.3, -0.6)):
    m = cv.ell(x, y, r, r) & ~cv.ell(x + off[0] * r / 2.2, y + off[1] * r / 2.2, r * 0.82, r * 0.82)
    cv.paint(m, cols[0]); cv.paint(m & cv.ell(x - 0.5, y - 0.3, r - 0.9, r - 0.9), cols[1]); cv.put(x - r * 0.55, y, cols[2])
    EC.outl(cv, m); return m
def flame(cv, x, by, r, h, lean, cols):
    m = cv.ell(x, by, r + 0.6, r + 0.6)
    for j in range(int(h) + 1):
        t = j / h; half = (r + 0.6) * (1 - t) ** 0.9; ox = lean * t * t + 0.6 * math.sin(t * 5)
        m |= (np.abs(cv.xx + .5 - (x + ox)) <= half) & (cv.yy == int(round(by - j)))
    cv.paint(m, cols[0]); mid = m & ~EC.dil(EC.ring(m))
    cv.paint(mid, cols[1]); cv.paint(mid & cv.ell(x, by, r * 0.6, r * 0.6), cols[2]); EC.outl(cv, m); return m

# ============================================================ renderer
def render_F(form, p):
    f = FORMS[form]; S = f["S"]; cv = bt.Cv(S); br = f["branch"]; el = f["elder"]; k = f["k"]
    sick = p.get("sick", False); ramp = "sick" if sick else f["ramp"]; R = bt.RAMPS[ramp]
    _, _, _, rx, ry, cx, cy = L._geo(form, p)
    lift = p.get("lift", 0.0); ground = f["G"] - 1.0 - lift
    sway = p.get("sway", 0); droop = p.get("droop", 0); bud = p.get("bud", 1.0); ph = p.get("fluff", 0.0); tw = p.get("twinkle", 0)
    q = q_of(p); G = geo_F(form, p); flap = math.sin(ph * 2.0 + q * 1.3); dr = min(1.0, droop)
    lvl = p.get("_aura", 1.0); lamp = 0.0 if sick else p.get("_lamp", 1.0)
    big_lvl = min(lvl, p.get("_lamp", 1.0))        # 靜光大件發光飾物：跟 aura（月眠再跟燈）
    LC = lamp_cols(lamp)
    # ---------------- behind
    if el and br == "tide":     # 背鰭翼（拍）
        for j, (a, b, ang) in enumerate(((8.2, 3.0, 150), (6.8, 2.5, 176))):
            ang = ang + 6 * flap * (1 if j == 0 else -0.6) - 12 * dr
            d = (math.cos(math.radians(ang)), -math.sin(math.radians(ang))); bx0, by0 = cx - rx * 0.6, cy - ry * 0.2 + j * 2.2
            w = EC.rot_ell(cv, bx0 + d[0] * a * 0.7, by0 + d[1] * a * 0.7, a, b, ang); cv.paint(w, _col(sick, "egg_shade"))
            cv.paint(w & ~EC.rot_ell(cv, bx0 + d[0] * a * 0.7 + .6, by0 + d[1] * a * 0.7 + .8, a - 1.2, b - 1.0, ang), _col(sick, "peach2", "sick1")); cv.solid |= w
    if el and br == "crystal":  # 背後晶冠（5 支），逐幀一支閃
        hx_, hy_ = cx, cy - ry * 0.25
        for i, ang in enumerate((158, 128, 52, 22)):   # 中間留空俾菱形晶燈
            Lc = (16.0 if ang in (128, 52) else 14.0) - dr * 1.5; ar = math.radians(ang)
            bx, by = hx_ + math.cos(ar) * (Lc - 5.0), hy_ - math.sin(ar) * (Lc - 5.0)
            m = EC.rot_ell(cv, bx, by, 5.0, 2.1, ang); cv.paint(m, _col(sick, "egg_shade"))
            inner = m & EC.rot_ell(cv, bx - .6, by - .6, 3.4, 1.0, ang)
            if not sick: cv.paint(inner, "glow_mid" if big_lvl >= 0.45 else "peach2")
            if not sick and big_lvl >= 0.99 and i == q % 4: cv.put(bx + math.cos(ar) * 3.0, by - math.sin(ar) * 3.0, "glow_core")
            cv.solid |= m
    if el and br == "moon":     # 背後大月牙＋雲枕
        mx, my, Rm = cx - 2, cy - ry * 0.55, 15.8
        mm = cv.ell(mx, my, Rm, Rm) & ~cv.ell(mx + 4.2, my - 3.0, Rm * 0.9, Rm * 0.9) & (cv.yy < cy + 2)
        if sick: cv.paint(mm, "sick1")
        else:
            cv.paint(mm, "glow" if big_lvl >= 0.3 else "peach2")
            inner = mm & cv.ell(mx - 1, my, Rm - 1.6, Rm - 1.6)
            if big_lvl >= 0.99: cv.paint(inner, "glow_mid")
            elif big_lvl >= 0.45: cv.paint(inner & ((cv.xx + cv.yy) % 3 == 0), "glow_mid")
        cv.solid |= mm
        bottom = ground
        cl = cv.ell(cx - rx - 2.5, bottom - 2.4, 2.4, 2.4) | cv.ell(cx - rx + 0.5, bottom - 3.6, 2.4, 2.4) | cv.ell(cx - rx - 5.2, bottom - 1.8, 2.4, 2.4)
        cl &= (cv.yy <= bottom)
        cv.paint(cl, "white"); cv.paint(cl & (cv.yy >= bottom - 1.6), "peach2"); cv.solid |= cl
    if el and br == "ember":    # 背後火翼（閃）
        fl = 1.0 + 0.1 * ((q % 3) - 1)
        for j, (a, b, ang) in enumerate(((7.8, 2.6, 156), (6.2, 2.2, 132))):
            a = a * fl; ang = ang + 6 * flap * (1 if j == 0 else -0.7) - 12 * dr
            d = (math.cos(math.radians(ang)), -math.sin(math.radians(ang))); bx0, by0 = cx - rx * 0.62, cy - ry * 0.2 - j * 1.5
            w = EC.rot_ell(cv, bx0 + d[0] * a * 0.7, by0 + d[1] * a * 0.7, a, b, ang); cv.paint(w, "sick1" if sick else "glow")
            if not sick and big_lvl >= 0.45: cv.paint(w & EC.rot_ell(cv, bx0 + d[0] * a * 0.6, by0 + d[1] * a * 0.6, a - 2.0, b - 1.1, ang), "glow_mid")
            cv.solid |= w
    if el and br == "shroom":   # 腳邊兩粒發光細菇（輕搖）
        for i, (x, s) in enumerate(((cx - rx - 3.5, 1.0), (cx + rx + 3.2, 0.85))):
            x = x + (0.5 if (q + i) % 2 else 0.0)
            st = cv.ell(x, ground - 1.2, 0.9, 1.6); cv.paint(st, "egg_shade"); cv.solid |= st
            cp = cv.ell(x, ground - 3.0, 2.4 * s, 1.6 * s) & (cv.yy <= ground - 2.6)
            cv.paint(cp, "sick1" if sick else "glow")
            if not sick and big_lvl >= 0.45: cv.paint(cp & (cv.yy <= ground - 3.6), "glow_mid")
            cv.solid |= cp
    # tails / ears（身後）
    wag = 0.6 * math.sin(ph * 2.0 + q * 0.8)
    if br == "tide":
        tx, ty = cx - rx - 0.6, cy + ry * 0.35 - wag * 0.5
        for ang in (148, 212):
            a2 = ang + (8 * wag if ang < 180 else -8 * wag)
            m = EC.rot_ell(cv, tx - 2.4, ty + (-1.6 if ang < 180 else 1.2), 4.2 if el else 3.6, 1.7, a2); cv.paint(m, _col(sick, "egg_shade")); cv.solid |= m
            cv.paint(m & EC.rot_ell(cv, tx - 2.0, ty + (-1.4 if ang < 180 else 1.0), 2.4, 0.9, a2), R[2])
        for s in (-1, 1):
            ex, ey_ = cx + s * rx * 0.6, cy - ry * 0.74 + dr * 0.8
            ang = (125 if s < 0 else 100) + 5 * flap + 30 * dr * (1 if s < 0 else 1.6)
            m = EC.rot_ell(cv, ex - 1.0, ey_ - 1.6, 4.4 if el else 3.9, 1.9, ang); cv.paint(m, _col(sick, "egg_shade")); cv.solid |= m
            cv.paint(m & EC.rot_ell(cv, ex - 0.6, ey_ - 1.0, 2.6, 0.9, ang), _col(sick, "peach2", "sick1"))
    if br == "shroom": tpuff(cv, cx - rx - 0.8, cy + 2.0 - wag, 2.8, ramp)
    if br == "crystal":
        tpuff(cv, cx - rx - 1.0, cy + 1.5 - wag, 3.0, ramp, tip=_col(sick, "egg_shade"))
        for s in (-1, 1):
            m = EC.ear(cv, cx + s * rx * 0.56, cy - ry * 0.62 + dr * 0.8, (8.6 if el else 7.8) - dr * 2.0 + (0.6 if bud > 1.1 else 0), 6.0, s * (1.6 + dr * 1.6) + sway * 0.25, (_col(sick, "egg_shade"),) * 2)
            bx_ = cx + s * rx * 0.56; by_ = cy - ry * 0.62 + dr * 0.8; hh = (8.6 if el else 7.8)
            half = m & (cv.xx + .5 < bx_ + s * 1.6 * (by_ - cv.yy - .5) / hh)
            if not sick: cv.paint(half, "cyan" if lvl >= 0.45 else "peach2")   # 靜光瞓覺晶耳光跟 aura 暗
    if br == "moon": tpuff(cv, cx - rx - 1.0, cy + 1.8 - wag, 3.0, ramp, tip=None if sick else "cyan")
    if br == "ember":
        tpuff(cv, cx - rx - 1.0, cy + 1.6 - wag, 3.0, ramp)
        ft = (0.0, 0.8, 0.3, 1.1)[q % 4]
        for s in (-1, 1): EC.ear(cv, cx + s * rx * 0.58, cy - ry * 0.68 + dr * 0.8, (7.2 if el else 6.6) - dr * 1.8 + ft * (1 if s > 0 else 0.6), 5.0, s * (1.6 + dr * 1.4), (R[1], "sick1" if sick else "glow"))
    # ---------------- feet / arms（= BC）
    frx, fry = f["feet"]; fi = p.get("feet_in", 0.0); flf = p.get("flift", (0, 0))
    for i, s in enumerate((-1, 1)):
        m = cv.ell(cx + s * rx * 0.45 * (1 - fi), ground + 0.35 - flf[i], frx, fry); cv.paint(m, "orange"); cv.solid |= m
        cv.paint(m & (cv.yy >= int(ground + 0.6 - flf[i])), "orange_d")
    arms = p.get("arms", "down")
    if arms != "none":
        ar = f["arm"]
        for s in (-1, 1):
            if arms == "down": ax, ay = cx + s * (rx - 0.2), cy + ry * 0.2
            elif arms == "up": ax, ay = cx + s * (rx - 0.4), cy - ry * 0.35 - 1
            else: ax, ay = cx + s * (rx - 0.6), cy + ry * (0.1 if s < 0 else 0.0)
            m = cv.ell(ax, ay, ar, ar); cv.paint(m, R[2]); cv.solid |= m
    # ---------------- body（= BC）
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
    if not sick: EC.lf_hi(cv, cx, cy, rx, ry, col="cream4")
    # ---------------- head features（solid，一齊描邊）
    if br == "tide": put_stem(cv, G["stem"], (_col(sick, "egg_shade"), _col(sick, "egg_dark", "sick1")))
    if br == "crystal":
        for (dx, dy, h) in ((-0.86, -0.12, 4.6), (-0.7, -0.5, 5.2)):   # 背脊細晶
            m = EC.ear(cv, cx + dx * rx, cy + dy * ry + 1.0, h - dr, 3.8, -2.4 - dr, (_col(sick, "egg_shade"),) * 2)
            if not sick: cv.paint(m & (cv.xx + .5 < cx + dx * rx - 2.4 * (cy + dy * ry + 1.0 - cv.yy - .5) / h), "glow_mid" if lvl >= 0.45 else "peach2")
        put_stem(cv, G["stem"], (_col(sick, "egg_shade"),), w=1)
    if br == "ember": put_stem(cv, G["stem"], (_col(sick, "egg_shade"),))
    if br == "shroom":
        for (dx, dy, r) in ((-0.62, -0.38, 1.9), (-0.42, -0.62, 1.6), (-0.8, -0.05, 1.5)):   # 背苔
            m = cv.ell(cx + dx * rx, cy + dy * ry, r, r) & bm; cv.paint(m, _col(sick, "leaf")); cv.put(cx + dx * rx + 0.5, cy + dy * ry + 0.5, _col(sick, "leaf_d", "sick1"))
        capx, capy, cw, ch, wob = G["capx"], G["capy"], G["cw"], G["ch"], G["wob"]; tilt = 0.45 * wob
        cut = (cv.yy + .5) <= capy + 0.6 + tilt * (cv.xx + .5 - capx) / cw
        cap = cv.ell(capx, capy, cw, ch) & cut
        if el: cap |= (cv.ell(capx - cw + 1.6, capy + 0.8 - tilt, 1.8, 1.6) | cv.ell(capx + cw - 1.6, capy + 0.8 + tilt, 1.8, 1.6))
        cv.paint(cap, _col(sick, "berry", "sick1")); cv.paint(cap & ((cv.yy + .5) >= capy - 0.6 + tilt * (cv.xx + .5 - capx) / cw), _col(sick, "berry_d"))
        cv.solid |= cap
        gy = np.round(capy + 1 + tilt * (cv.xx + .5 - capx) / cw - 0.5).astype(int)
        gill = (cv.yy == gy) & (np.abs(cv.xx + .5 - capx) <= cw - 1.6) & ~cap
        cv.a[gill] = IDX[_col(sick, "egg_shade", "sick1")]; cv.solid |= gill
        if el and not sick and lvl >= 0.45:
            for x in range(int(capx - cw + 3), int(capx + cw - 1), 3): cv.put(x, capy + 1 + tilt * (x + .5 - capx) / cw, "glow_mid")
        for (dx, dy, r) in ((-0.5, -0.45, 1.3), (0.15, -0.72, 1.2), (0.55, -0.3, 1.0), (-0.12, -0.15, 0.8)):
            cv.a[cv.ell(capx + dx * cw, capy + dy * ch, r, r) & cap & ((cv.yy + .5) < capy - 0.6 + tilt * (cv.xx + .5 - capx) / cw)] = IDX["cream4" if not sick else "sick0"]
        put_stem(cv, G["stem"], ("egg_shade" if not sick else "sick1",), w=1)
    if br == "moon":
        P = G["hat"]; cap = np.zeros_like(cv.solid)
        for (x, y, r) in P: cap |= cv.ell(x, y, r, r)
        cap &= ~(bm & (cv.yy > cy - ry + 2.2))
        cv.paint(cap, _col(sick, "zzz", "sick1"))
        for i, (x, y, r) in enumerate(P):
            if i % 6 == 3: cv.a[cap & cv.ell(x, y, r + 0.3, r + 0.3) & ~cv.ell(P[i - 1][0], P[i - 1][1], P[i - 1][2] + 0.2, P[i - 1][2] + 0.2)] = IDX[_col(sick, "egg_shade")]
        brim = cap & (cv.yy >= int(cy - ry + 0.8)) & (cv.yy <= int(cy - ry + 2.2))
        cv.paint(brim, "cream4" if not sick else "sick0"); cv.solid |= cap
    cv.outline()
    # ---------------- post-outline details + lamps
    if br == "tide":
        for x in range(int(cx - rx * 0.42), int(cx + rx * 0.5)):     # 肚波紋（逐幀流）
            y = int(cy + ry * 0.70 + (1 if ((x // 2) + q) % 2 else 0))
            if 0 <= y < S and bm[y, x] and cv.a[y, x] != IDX["outline"]: cv.a[y, x] = IDX["sick0" if sick else "cyan"]
        EC.spots(cv, bm, [(-0.6, 0.1), (-0.78, 0.38), (0.66, 0.2)], R[0], cx, cy, rx, ry)
        bx_, by_ = G["bulb"]; r = (2.4 if el else 2.0) * (0.92 + 0.08 * min(bud, 1.4))
        if sick: m = cv.ell(bx_, by_, r, r); cv.paint(m, "sick1"); EC.outl(cv, m)
        else: drop_bulb(cv, bx_, by_, r, LC)
    if br == "shroom":
        bx_, by_ = G["bulb"]; r = (2.6 if el else 2.2) * (0.92 + 0.08 * min(bud, 1.4))
        mc = cv.ell(bx_, by_, r + 0.7, r * 0.8 + 0.4) & (cv.yy <= by_ + 0.6)
        if sick: cv.paint(mc, "sick1")
        else:
            cv.paint(mc, LC[0]); cv.paint(mc & cv.ell(bx_ - .4, by_ - .4, r - 0.2, r * 0.6), LC[1])
            cv.put(bx_ - 1, by_ - 1, LC[2]); cv.put(bx_ + 1, by_ - 0.5, "cyan" if lamp >= 0.99 else LC[1])
        EC.outl(cv, mc)
    if br == "crystal":
        for i, (a, b, c) in enumerate(((-0.55, 0.05, "cyan"), (0.7, 0.42, "glow_core"), (-0.25, 0.6, "cyan"), (0.4, -0.55, "glow_core"), (-0.7, 0.35, "cyan"), (0.15, 0.7, "glow_core"))):
            x, y = int(round(cx + a * rx)), int(round(cy + b * ry))   # 晶粉閃點：逐幀輪住
            if 0 <= y < S and bm[y, x] and cv.a[y, x] != IDX["outline"]:
                cv.a[y, x] = IDX["sick0" if sick else (c if (i + q) % 3 != 0 else "peach2")]
        bx_, by_ = G["bulb"]; a_, b_ = (2.7, 3.8) if el else (2.3, 3.3); sc = 0.92 + 0.08 * min(bud, 1.4)
        if sick:
            m = (np.abs(cv.xx + .5 - bx_) / a_ + np.abs(cv.yy + .5 - by_) / b_) <= 1.0; cv.paint(m, "sick1"); EC.outl(cv, m)
        else: diamond(cv, bx_, by_, a_ * sc, b_ * sc, LC, q if (lamp >= 0.99 and droop < 0.8) else None)
    if br == "moon":
        EC.spots(cv, bm, [(-0.6, 0.18), (0.62, 0.45), (-0.3, 0.6)], "sick0" if sick else "cyan", cx, cy, rx, ry)
        if not sick:   # 星點雀斑閃
            x, y = int(round(cx + [-0.6, 0.62, -0.3][q % 3] * rx)), int(round(cy + [0.18, 0.45, 0.6][q % 3] * ry))
            if bm[y, x] and cv.a[y, x] == IDX["cyan"]: cv.a[y, x] = IDX["peach2"]
        ex, ey_, _ = G["hat"][-1]
        for j in range(2): cv.put(ex - 1 - j, ey_ + 1.5 + j, "outline")
        bx_, by_ = G["bulb"]; r = 2.8 if el else 2.5
        if sick: m = cv.ell(bx_, by_, r, r) & ~cv.ell(bx_ - 1.3 * r / 2.2, by_ - 0.6 * r / 2.2, r * 0.82, r * 0.82); cv.paint(m, "sick1"); EC.outl(cv, m)
        else: crescent(cv, bx_, by_, r, LC)
    if br == "ember":
        fl = (0.0, 1.0, -0.5, 0.6)[q % 4]; lean = 1.2 + 0.8 * math.sin(q * 1.7) + sway * 0.3
        tfx, tfy = cx - rx - 2.6, cy - 1.6 - wag
        if sick: m = cv.ell(tfx, tfy, 1.4, 1.4); cv.paint(m, "sick1"); EC.outl(cv, m)
        else: flame(cv, tfx, tfy, 1.6, 4.5 + 0.8 * ((q + 1) % 3 - 1), -1.6 + 0.5 * math.sin(q * 2.1), LC)
        EC.spots(cv, bm, [(-0.62, 0.15), (0.66, 0.4), (-0.3, 0.62)], "sick0" if sick else "egg_shade", cx, cy, rx, ry)
        hot = [(-0.75, 0.38), (0.78, 0.08)]
        EC.spots(cv, bm, [hot[i] for i in range(2) if (i + q) % 3 != 0], "sick0" if sick else "cyan", cx, cy, rx, ry)
        bx_, fby = G["fb"]; r = (2.3 if el else 2.0) * (0.92 + 0.08 * min(bud, 1.4))
        if sick: m = cv.ell(bx_, fby, 1.8, 1.8); cv.paint(m, "sick1"); cv.put(bx_, fby - 2, "sick0"); EC.outl(cv, m)
        else:
            h = ((6.5 if el else 5.5) + fl) * (0.7 if droop > 0.8 else 1.0)
            flame(cv, bx_, fby, r, h, lean, LC)
    # ---------------- face（= BC：舊 clip 模板）
    fcx, ey, eoff, my, bx, by, ho = A.face_geo(form, cx, cy, rx, ry)
    cm = dict(A.CMX); ET, MT = A.EYE_TPL["L"], A.MOUTH_TPL["L"]
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
    # ---------------- front fx（guard 細飾／elder 飾物＋aura）
    if br == "tide" and not sick:
        bx_, by_ = G["bulb"]
        if el:
            for i in range(3):   # 三粒細水珠繞燈轉
                t = i * 2.094 + q * 0.5; x, y = bx_ + math.cos(t) * 7.0, by_ + 1.0 + math.sin(t) * 3.0
                free_put(cv, x, y, "glow_mid" if lamp >= 0.5 else "glow"); free_put(cv, x, y - 1, "glow_core" if lamp >= 0.99 else "glow")
    if br == "ember" and el and not sick:
        for dx in (-5.5, 5.5):
            flame(cv, cx + dx + 0.5, cy - ry + 1.0 + dr, 1.1, (3.2 + 0.7 * ((q + (dx > 0)) % 2)) * (0.6 if droop > 0.8 else 1.0), 0.6 * np.sign(dx), LC if big_lvl >= 0.45 else lamp_cols(0.3))
    if el and not sick and lvl > 0:
        aura5(cv, br, q, lvl)
        if lvl >= 0.99:
            if br == "tide":
                for i, (x, y, r) in enumerate(((5, 12, 1.6), (S - 6, 18, 1.3), (6, 26, 1.0))):
                    yy = y - (q + i) % 3; m = cv.ell(x, yy, r, r); rg = EC.ring(m) & (cv.a == 0); rg[:2] = rg[-3:] = False; cv.a[rg] = IDX["egg_shade"]; free_put(cv, x - r * 0.4, yy - r * 0.4, "cyan")
            if br == "shroom":
                for i, (x, y) in enumerate(((4, 14), (S - 5, 9), (S - 7, 24))):
                    yy = y - (q + i) % 3; free_put(cv, x, yy, "cyan"); free_put(cv, x + 1, yy - 1, "glow_mid")
            if br == "crystal":
                for i, (x, y) in enumerate(((4, 20), (S - 5, 26))):
                    yy = y + (0 if (q + i) % 2 else -1)
                    for (dx, dy, c) in ((0, 0, "glow_core"), (0, -1, "glow_mid"), (0, 1, "glow_mid"), (-1, 0, "glow"), (1, 0, "glow"), (0, -2, "cyan")): free_put(cv, x + dx, yy + dy, c)
                gx, gy = [(S - 7, 6), (S - 9, 11), (8, 5)][q % 3]; fsparkle(cv, gx, gy, "glow_core", "cyan")
            if br == "moon":
                for i, (x, y) in enumerate(((S - 6, 30), (4, 8))):
                    if (q + i) % 2 == 0: fsparkle(cv, x, y, "cyan", "glow_mid")
                    else: free_put(cv, x, y, "cyan")
            if br == "ember":
                for i, (x, y) in enumerate(((S - 6, 10), (5, 20), (S - 9, 4))):
                    yy = y - (q + i) % 3; free_put(cv, x, yy, "cyan"); free_put(cv, x, yy - 1, "glow_mid")
        BC.clean_edge(cv)
    elif not sick:
        if br == "tide":    # 泡泡上升
            for i, (x, y, r) in enumerate(((cx + rx + 3.5, cy - ry * 0.5, 1.4), (cx + rx + 5.5, cy - ry * 0.95, 1.0))):
                yy = y - ((q + i) % 3) * 0.8; m = cv.ell(x, yy, r, r); rg = EC.ring(m) & (cv.a == 0); rg[:2] = False; rg[:, -2:] = False
                cv.a[rg] = IDX["egg_shade"]; free_put(cv, x - r * 0.4, yy - r * 0.4, "cyan")
        if br == "shroom":
            for i, (x, y) in enumerate(((cx + rx + 3, cy - ry * 0.9), (cx + rx + 5, cy - ry * 0.4))): free_put(cv, x, y - (q + i) % 2, "cyan")
        if br == "crystal" and droop < 0.8:
            gx, gy = [(cx + rx + 4, cy - ry * 0.7), (cx + rx + 2, cy - ry * 1.15), (cx - rx - 3, cy - ry * 0.9)][q % 3]; fsparkle(cv, int(gx), int(gy), "glow_core", "cyan")
        if br == "moon" and lamp >= 0.99:
            for i, (x, y) in enumerate(((cx + rx + 4, cy - 1), (cx - rx - 3, cy - ry - 1))):
                if (q + i) % 2 == 0: fsparkle(cv, int(x), int(y), "cyan", "glow_mid")
                else: free_put(cv, int(x), int(y), "cyan")
        if br == "ember":
            for i, (x, y) in enumerate(((cx + rx + 3, cy - ry * 0.95), (cx + rx + 5, cy - ry * 0.55))): free_put(cv, x, y - (q + i) % 3, "cyan")
        BC.clean_edge(cv)
    a0 = cv.a.copy()
    for fx_ in p.get("extras", []): fx_(cv, cx, cy, rx, ry)
    return A.keep_fx_inside(a0, cv.a)

_render_prev = A.render_evo
A.render_evo = lambda form, p: render_F(form, p) if form in NEW5 else _render_prev(form, p)

BC.BR_NOTE.update({
 ("tide", False): "守夜者・水珠：鰭耳（擺）、分叉魚尾（擺）、頭頂水珠燈（逐幀浮上浮落）、肚皮泡沫波紋（流）、身邊泡泡上升；idle 身浮 1px；emissive＝drop_gc/drop_gm。",
 ("tide", True): "靜光・水珠：背鰭翼（拍）、三粒細水珠繞燈轉、泡泡 aura；瞓覺 aura 漸暗。",
 ("shroom", False): "守夜者・菇傘：紅白點菇帽（逐幀搖＋斜）、帽頂發光細菇燈（跟住晃）、背苔、孢子飄；emissive＝myco_gc/myco_gm/spore。",
 ("shroom", True): "靜光・菇傘：大垂邊菇帽、菇褶發光點、腳邊兩粒發光細菇（輕搖）、孢子 aura；瞓覺 aura＋菇光漸暗。",
 ("crystal", False): "守夜者・晶角：晶角耳（半邊晶光）、背脊細晶、菱形晶燈（旁邊十字閃逐幀換位）、身上晶粉閃點輪住閃；emissive＝prism_gc/prism_gm/prism。",
 ("crystal", True): "靜光・晶角：後腦 4 尖晶冠（中間留空俾晶燈；逐幀一支閃）、兩粒浮晶（上下）、晶光 aura；瞓覺 aura＋晶冠光漸暗。",
 ("moon", False): "守夜者・月眠：尖睡帽（帽尖跟住點頭）吊住月牙燈、星點雀斑（閃）、渴瞓半瞇眼（idle_02／walk／生命感間中）；fall_asleep 月牙燈漸暗、sleep_loop 暗、wake 返光；emissive＝moon_gc/moon_gm/star。",
 ("moon", True): "靜光・月眠：背後大月牙＋雲枕、星 aura；瞓覺 aura＋大月牙＋燈一齊漸暗、wake 返光。",
 ("ember", False): "守夜者・火苗：頭頂火苗燈（逐幀高低／左右搖）、火尖耳（閃）、尾尖火（閃）、煤灰＋火星雀斑（閃）；emissive＝flame_gc/flame_gm/hot。",
 ("ember", True): "靜光・火苗：背後火翼（閃）、頭頂兩旁火冠、火星 aura；瞓覺 aura＋火翼漸暗。",
})

# ============================================================ previews
PICKS = [("idle", 0), ("idle", 1), ("idle", 2), ("idle", 3), ("walk", 2), ("emo_happy", 1), ("eat", 2), ("sick", 0), ("fall_asleep", 0), ("fall_asleep", 3),
         ("sleep_loop", 0), ("wake", 2), ("picked_up", 1), ("smug_pose", 3), ("cheer_jump", 2), ("nuzzle_purr", 2), ("reunion_happy", 3)]
def batch_contact_F(res, forms, tag, Z=4):
    br = FORMS[forms[0]]["branch"]
    CELL = 52; LW = 170; W = LW + len(PICKS) * (CELL * Z + 4) + 8; H = 58 + 2 * len(forms) * (CELL * Z + 24) + 8
    cs = Image.new("RGBA", (W, H), BC.BG); dr = ImageDraw.Draw(cs)
    dr.text((8, 8), f"團絨 evo6 batch {tag} — {BNAME[br]}（{br}）守夜者 44／靜光 48 全套 41 clip（4x，同一地線；下排＝emissive）", fill=(255, 248, 224, 255), font=A.font(15))
    dr.text((8, 30), "分支動態：" + MOTION[br], fill=(200, 196, 230, 255), font=A.font(13))
    r = 0
    for form in forms:
        order, clips, kit = res[form]; piv = BC.fpiv(form)
        for em in (False, True):
            y0 = 58 + r * (CELL * Z + 24)
            dr.text((8, y0 + 40), FORMS[form]["name"], fill=(255, 248, 224, 255), font=A.font(17))
            dr.text((8, y0 + 66), f"{BC.fsize(form)}px " + ("emissive" if em else "frame"), fill=(200, 196, 230, 255), font=A.font(13))
            for kf, (clip, i) in enumerate(PICKS):
                c = clips[clip]; i = min(i, len(c["full"]) - 1); a = c["full"][i]; x0 = LW + kf * (CELL * Z + 4)
                ox, oy = CELL // 2 - piv[0], CELL - 4 - piv[1]; img = BC.to_img(a, form)
                if em: arr = np.array(img); arr[~np.isin(a, BC.emis_ids(form))] = 0; img = Image.fromarray(arr)
                m = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0)); m.alpha_composite(img, (ox, oy))
                cs.alpha_composite(m.resize((CELL * Z, CELL * Z), Image.NEAREST), (x0, y0))
                if not em:
                    bx, by = c["anchors"][i]["bulb"]; X, Y = x0 + (bx + ox) * Z + Z // 2, y0 + (by + oy) * Z + Z // 2
                    dr.line((X - 4, Y, X + 4, Y), fill=(255, 230, 0, 255)); dr.line((X, Y - 4, X, Y + 4), fill=(255, 230, 0, 255))
                dr.text((x0 + 4, y0 + CELL * Z + 2), f"{clip}_{i + 1:02d}", fill=(200, 196, 230, 255), font=A.font(11))
            r += 1
    p = os.path.join(PRV, f"evo6_batch{tag}_contact_4x.png"); cs.save(p); return p

# ============================================================ docs（寫之前即刻重讀；只加／更新自己 key；atomic）
def update_docs_F(res, ainfo, forms, tag):
    br = FORMS[forms[0]]["branch"]
    p = os.path.join(MOT, "CLIPS.json"); D = json.load(open(p, encoding="utf-8"))
    for form in forms:
        order, clips, kit = res[form]; f = FORMS[form]; W, H, n = ainfo[form]
        D["forms"][form] = {"name": f["name"], "stage": f["stage"], "branch": f["branch"], "evo6": True, "batch": tag, "frameSize": f["S"], "pivotPx": list(BC.fpiv(form)),
            "atlas": f"../evo6/atlas_{form}.png", "json": f"../evo6/atlas_{form}.json", "emissive": f"../evo6/atlas_{form}_emissive.png",
            "atlasSize": [W, H], "atlasPieces": n, "frames": sum(len(clips[c]["full"]) for c in order),
            "palette": f"../evo6/{BC.PALFILE[f['pal']]}", "emissiveColors": list(BC.EMIS_PALNAMES[f["pal"]]),
            "lampColors": [B5.SW5[br][nm][0] for nm in LAMP_NAMES],
            "faceAnchors": f"../evo6/{form}/face_anchors_{form}.json", "clips": order, "concept": "../evo6_concept/branches5/（v3 lumi feel 新支線）",
            "faceRig": True, "faceTier": "L 4×5", "hasBulb": True, "headRightAnchor": list(M.ANCH[form]["head_r"]), "potAnchor": list(M.ANCH[form]["pot"]),
            "sunAnchor": [0, 0], "kitPieces": sorted(kit), "std23": A.ORDER_STD, "liveliness": A.ORDER_NEW, "s3": BC.S3_DUST,
            "trait": TRAIT[br], "branchMotion": MOTION[br],
            **({"auraSleep": "fall_asleep 0.8→0.2 漸暗、sleep_loop 0.2（只內圈疏點、暗色）；大件發光飾物跟 aura 一齊暗"} if f["elder"] else {}),
            **({"lampSleep": "月牙燈：fall_asleep 1→0.25 漸暗（core→mid→淨 glow，唔發光）、sleep_loop 0.25、wake 0.25→1 返光"} if br == "moon" else {}),
            "lampRule": "bulb 錨點＝燈中心（" + {"tide": "頭頂水珠燈", "shroom": "菇帽頂細菇燈", "crystal": "頭頂菱形晶燈", "moon": "睡帽尖吊住嘅月牙燈", "ember": "頭頂火苗燈"}[br] + "）",
            "note": BC.BR_NOTE[(f["branch"], f["elder"])]}
    for c in D["clips"]:
        nme = c["name"]
        for form in forms:
            order, clips, kit = res[form]
            if nme in clips:
                c.setdefault("anchors", {})[form] = clips[nme]["anchors"]
                c[form] = {"frames": len(clips[nme]["full"]), "full": f"../evo6/{form}/frames/{nme}_NN.png", "noface": f"../evo6/{form}/layers/{nme}_NN_noface.png",
                           "faceov": f"../evo6/{form}/layers/{nme}_NN_faceov.png", "emissive": f"../evo6/{form}/emissive/{nme}_NN_emissive.png",
                           "atlasClip": nme, "nofaceClip": f"{nme}_noface", "atlas": f"../evo6/atlas_{form}.json"}
    E = D.setdefault("evo6F", {"tool": "tools/build_evo6_animF.py", "validator": "tools/validate_evo6_anim.py", "concept": "../evo6_concept/branches5/",
                               "note": "新支線 ×5（水珠／菇傘／晶角／月眠／火苗）：守夜者 44＋靜光 48，全套 41 clip／180 幀（std23＋生命感 s1/s2＋s3），每批一條支線。",
                               "batches": {}})
    E.setdefault("batches", {})[tag] = {"branch": br, "name": BNAME[br], "forms": forms, "trait": TRAIT[br], "motion": MOTION[br], "palette": f"../evo6/palette_{br}.json",
                                        "preview": [f"../preview/evo6/evo6_batch{tag}_contact_4x.png"] + [f"../preview/evo6/{fm}_contact_4x.png" for fm in forms]}
    E["forms"] = sorted({fm for b in E["batches"].values() for fm in b["forms"]})
    BC.atomic_write(p, json.dumps(D, indent=1, ensure_ascii=False))
    # CLIPS.md：EVO6F 段（由 CLIPS.json evo6F 重砌，只動自己段）
    mp = os.path.join(MOT, "CLIPS.md"); md = open(mp, encoding="utf-8").read()
    a_, b_ = "<!-- EVO6F-START -->", "<!-- EVO6F-END -->"
    if a_ in md: md = md[:md.index(a_)].rstrip() + "\n\n" + md[md.index(b_) + len(b_):].lstrip()
    rows = []
    for t in sorted(E["batches"]):
        for fm in E["batches"][t]["forms"]:
            fe = D["forms"][fm]
            rows.append(f"| {t} | {fe['name']} `{fm}` | {fe['frameSize']} | {tuple(fe['pivotPx'])} | {len(fe['clips'])} | {fe['frames']} | `../evo6/atlas_{fm}.png`（{fe['atlasSize'][0]}×{fe['atlasSize'][1]}，{fe['atlasPieces']} 塊）＋ `_emissive` | {os.path.basename(fe['palette'])} |")
    mot = "\n".join(f"- {t} {E['batches'][t]['name']}：{E['batches'][t]['motion']}" for t in sorted(E["batches"]))
    sec = (f"{a_}\n## 進化 6 階 batch F — 新支線 ×5（水珠／菇傘／晶角／月眠／火苗）\n"
           "- 外觀＝`../evo6_concept/branches5/`（v3 lumi feel，逐幀 pose-aware 重畫）；姿勢＝現有同名 clip；4×5 L 級 kit；picked_up pivot＝grab；bulb＝燈中心。\n"
           "- 每形態全套 41 clip／180 幀：std23＋生命感 s1/s2（含 picked_up）＋s3 nuzzle_purr／reunion_happy；frames／layers（_noface／_faceov）／emissive／atlas。\n"
           "- 靜光 fall_asleep aura 0.8→0.2、sleep_loop 0.2（同靜光 ×4）；大件發光飾物跟住暗。\n" + mot +
           "\n\n| batch | 形態 | px | pivot | clip | 幀 | atlas | 色盤 |\n|---|---|---|---|---|---|---|---|\n" + "\n".join(rows) + f"\n{b_}\n")
    anchor = next((m for m in ("<!-- EVO6E-END -->", "<!-- EVO6D-END -->", "<!-- EVO6C-END -->") if m in md), None)
    if anchor: i = md.index(anchor) + len(anchor); md = md[:i] + "\n\n" + sec + md[i:]
    else: md = md.rstrip() + "\n\n" + sec
    BC.atomic_write(mp, md)
    # ASSET_LOG.md：每批一段
    lp = os.path.join(ROOT, "ASSET_LOG.md"); lg = open(lp, encoding="utf-8").read()
    a_, b_ = f"<!-- EVO6{tag}-LOG-START -->", f"<!-- EVO6{tag}-LOG-END -->"
    if a_ in lg: lg = lg[:lg.index(a_)].rstrip() + "\n\n" + lg[lg.index(b_) + len(b_):].lstrip()
    fr = "、".join(f"`{fm}` {D['forms'][fm]['frames']} 幀" for fm in forms)
    ent = (f"{a_}\n## 2026-10-31 — 團絨 evo6 動畫 batch {tag}（新支線・{BNAME[br]} {br}）\n"
           f"- 守夜者 44＋靜光 48 全套 41 clip：{fr}；frames／layers／emissive／kit／face_anchors（bulb＝燈中心）／atlas＋emissive。色盤 `sprites/tuanrong/evo6/palette_{br}.json`。\n"
           f"- 分支動態：{MOTION[br]}。靜光瞓覺 aura 漸暗同靜光 ×4。\n"
           f"- 預覽 `sprites/tuanrong/preview/evo6/evo6_batch{tag}_contact_4x.png`；工具 `tools/build_evo6_animF.py {tag}`（Pillow/numpy 程式繪製，無 AI）；CLIPS.json 只新增自己 key（forms.<form>、clips[].<form>、anchors.<form>、evo6F.batches.{tag}）；CLIPS.md EVO6F 段；備份 `_backups/pre_evo6_branches5_anim_20261031/`。\n{b_}\n")
    lg = lg.rstrip() + "\n\n" + ent
    BC.atomic_write(lp, lg)

# ============================================================ io（= BC.write_files，bulb 說明換新支線）
LAMP_TXT = {"tide": "bulb = 頭頂水珠燈中心", "shroom": "bulb = 菇帽頂細菇燈中心", "crystal": "bulb = 頭頂菱形晶燈中心",
            "moon": "bulb = 睡帽尖吊住嘅月牙燈中心", "ember": "bulb = 頭頂火苗燈中心"}
def write_files_F(form, order, clips, kit):
    d = os.path.join(OUT, form)
    if os.path.isdir(d): shutil.rmtree(d)
    for s_ in ("frames", "layers", "emissive", "kit"): os.makedirs(os.path.join(d, s_), exist_ok=True)
    for clip in order:
        c = clips[clip]
        for kf in range(len(c["full"])):
            n = f"{clip}_{kf + 1:02d}"
            BC.to_img(c["full"][kf], form).save(os.path.join(d, "frames", n + ".png"))
            BC.to_img(c["noface"][kf], form).save(os.path.join(d, "layers", n + "_noface.png"))
            BC.to_img(c["overlay"][kf], form).save(os.path.join(d, "layers", n + "_faceov.png"))
            BC.emis_img(c["full"][kf], form).save(os.path.join(d, "emissive", n + "_emissive.png"))
            BC.emis_img(c["noface"][kf], form).save(os.path.join(d, "emissive", n + "_noface_emissive.png"))
    for name, (a, pv) in kit.items(): BC.to_img(a, form).save(os.path.join(d, "kit", name + ".png"))
    f = FORMS[form]
    fa = {"version": 1, "form": form, "frameSize": f["S"], "coords": "frame-local px, origin = frame top-left, y down",
          "pivotPx": list(BC.fpiv(form)), "pivotOverride": {"picked_up": "grab"}, "palette": f"../{BC.PALFILE[f['pal']]}",
          "keys": "eyeL/eyeR/mouth = 五官錨點（kit piece pivot；已含面右移 1px）; head_r = 頭右上圖示; " + LAMP_TXT[f["branch"]] + "; faceVisible; face = 預設表情; grab = 頭頂拎點（picked_up，亦係 pivot）",
          "anchors": {clip: clips[clip]["anchors"] for clip in order}}
    p = os.path.join(d, f"face_anchors_{form}.json")
    with open(p, "w") as fh:
        head = {k_: v for k_, v in fa.items() if k_ != "anchors"}
        fh.write(json.dumps(head, ensure_ascii=False)[:-1] + ',\n "anchors":{\n')
        fh.write(',\n'.join('  ' + json.dumps(cl) + ':[\n' + ',\n'.join('   ' + json.dumps(a, ensure_ascii=False, separators=(",", ":")) for a in lst) + ']'
                            for cl, lst in fa["anchors"].items()) + '}}\n')
    json.load(open(p))

# ============================================================ main
def run(tag):
    br = BATCH[tag]; forms = [f"evo_guard_{br}", f"evo_still_{br}"]
    res = {}; ainfo = {}; stats = {}
    for form in forms:
        res[form] = BC.build_form(form); order, clips, kit = res[form]
        write_files_F(form, order, clips, kit); ainfo[form] = BC.write_atlas(form, order, clips, kit)
        BC.contact(form, order, clips, kit); BC.gifs(form, order, clips)
        edge = [f"{c}_{kf + 1:02d}" for c in order for kf, a in enumerate(clips[c]["full"]) if A.touches(a)]
        stats[form] = {"clips": {c: len(clips[c]["full"]) for c in order}, "nClips": len(order), "frames": sum(len(clips[c]["full"]) for c in order),
                       "atlas": ainfo[form][:2], "pieces": ainfo[form][2], "edgeTouch": edge,
                       "fit_adjustments": [f"{b}:{'/'.join(c)}" for a, b, c in M.FIT_LOG if a == form]}
        print(form, "clips", len(order), "frames", stats[form]["frames"], "atlas", ainfo[form], "edge", edge, flush=True)
    src = os.path.join(TR, "evo6_concept", "branches5", f"palette_evo6_{br}.json"); shutil.copy(src, os.path.join(OUT, BC.PALFILE[br]))
    pv = batch_contact_F(res, forms, tag)
    if "--no-docs" not in sys.argv: update_docs_F(res, ainfo, forms, tag)
    json.dump(stats, open(os.path.join(OUT, f"_stats_batch{tag}.json"), "w"), indent=1, ensure_ascii=False)
    print("preview", pv)
    return res

if __name__ == "__main__":
    for t in [a for a in sys.argv[1:] if not a.startswith("--")]: run(t)
