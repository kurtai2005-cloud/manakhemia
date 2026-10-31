#!/usr/bin/env python3
"""團絨 飾品（完整版）＋收藏品 — 遊美。Pillow/numpy 程式像素繪製，無 AI；v3 色盤；alpha 0/255。
ACC1：框架（ACCESSORIES.json、slot、per-clip 可見度、fit）、收藏品 12 件（16/32）、飾品 草帽／蝴蝶結／頸巾 × 25 形態 × 全部 clip。

做法（逐形態逐幀貼身＋跟變形）：
- 每幀由現有 face anchors（eyeL/eyeR/mouth/head_r/bulb/faceVisible）＋身體剪影推導 fit：
  axis（眼中點→燈泡；冇燈泡就垂直眼線）、top（沿 axis 向上，頭頂最後一行 ±r 全實）、hw（頭頂下 2px 頭闊）、
  ang（axis 相對 idle_01 嘅傾斜，<6° 當 0）、hs（頭高／idle 頭高 → 壓扁／拉長）。
- 飾品每幀用 fit 參數重新 raster（唔係縮放舊圖）：帽闊跟 hw、高跟 hs、轉角跟 ang（label map 轉，再描邊上光）→ 乾淨像素。
- 帽：燈泡／莖（頭頂以上、axis ±0.45hw 嘅身體像素）喺飾品層挖空 → 莖穿過帽、燈永遠喺面。
- 頸巾：順住頸線（mouth 下）剪影畫，跟 ang 斜；尾巴有慣性（跟身體中心前一幀位移反向擺）。
- 逐形態手調：FIT 表（dx/dy/scale/variant）；月眠／菇傘本身有帽 → 草帽用「帽針」細版掛喺帽側。
- 可見度：一個 clip 任何一幀 fit 唔成立（搵唔到頭頂、會遮五官／燈）→ 成個 clip 收起（唔會一閃一閃），原因寫入 ACCESSORIES.json。
輸出：sprites/tuanrong/accessories/（ACCESSORIES.json、items/<item>/atlas_<item>_<form>.png/json、fit_<item>.json、ref/）、ui/collectibles/。
用法：python3 build_accessories.py [all|collectibles|items [item…]|preview]"""
import json, os, sys, math, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.normpath(os.path.join(HERE, ".."))
TR = os.path.join(ROOT, "sprites", "tuanrong"); MOT = os.path.join(TR, "motion"); LV = os.path.join(MOT, "liveliness"); LU = os.path.join(TR, "lumi"); EV = os.path.join(TR, "evo6")
ACCD = os.path.join(TR, "accessories"); COLD = os.path.join(ROOT, "ui", "collectibles"); PREV = os.path.join(TR, "preview", "accessories")
PAL = {c["name"]: c["hex"] for c in json.load(open(os.path.join(MOT, "palette.json")))["colors"]}
def rgb(n): h = PAL[n]; return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
V3 = {rgb(n) for n in PAL}
PAD = 8   # 飾品層 = 身體幀四邊各加 PAD（尾巴／帽可以出 frame 邊）

# ================================================================ 形態／幀
CL = json.load(open(os.path.join(MOT, "CLIPS.json")))
EVO = [f for f, fe in CL["forms"].items() if fe.get("evo6") and f != "evo_egg" and "clipDefs" not in fe]
FORMS = ["sprout", "radiant", "soft", "lumi"] + EVO
HATFORMS = {"evo_guard_moon", "evo_still_moon", "evo_guard_shroom", "evo_still_shroom"}
def anchors(form):
    if form in ("sprout", "radiant", "soft"): return json.load(open(os.path.join(LV, "face_anchors.json")))["anchors"][form]
    if form == "lumi": return json.load(open(os.path.join(LU, "face_anchors_lumi.json")))["anchors"]
    return json.load(open(os.path.join(EV, form, f"face_anchors_{form}.json")))["anchors"]
def frame_path(form, clip, k):
    n = f"{clip}_{k:02d}.png"
    if form in ("sprout", "radiant", "soft"):
        p = os.path.join(LV, "frames", form, n)
        return p if os.path.exists(p) else os.path.join(MOT, "frames", form, n)
    if form == "lumi": return os.path.join(LU, "frames", n)
    return os.path.join(EV, form, "frames", n)
def load(p): return np.array(Image.open(p).convert("RGBA"))

# ================================================================ fit（每幀）
def _run(a, p, d, r):
    """p 點沿 d（單位向量）方向 ±r 係咪全實"""
    H, W = a.shape
    for t in range(-r, r + 1):
        if abs(t) <= 1: continue
        x, y = int(round(p[0] + d[0] * t)), int(round(p[1] + d[1] * t))
        if not (0 <= x < W and 0 <= y < H) or not a[y, x]: return False
    return True
def _width(a, p, d):
    H, W = a.shape; n = 0
    for sgn in (1, -1):
        t = 0 if sgn == 1 else 1
        while True:
            x, y = int(round(p[0] + d[0] * t * sgn)), int(round(p[1] + d[1] * t * sgn))
            if not (0 <= x < W and 0 <= y < H) or not a[y, x]: break
            n += 1; t += 1
    return n
AXIS = {"lumi": "eyes", "evo_guard_lumi": "eyes", "evo_still_lumi": "eyes"}   # 呢啲形態個 bulb 錨點係頭頂芽／尾燈，唔做 axis
def fit(img, an, ref=None, form=None):
    """回傳 dict：ok, axis(ux,uy 向上), perp, top(x,y), hw, ang(度，相對 ref), hs, eyemid"""
    a = img[..., 3] > 0; H, W = a.shape; S = W
    if "eyeL" in an and "eyeR" in an:
        em = ((an["eyeL"][0] + an["eyeR"][0]) / 2, (an["eyeL"][1] + an["eyeR"][1]) / 2)
    elif "grab" in an: em = (an["grab"][0], an["grab"][1] + S * 0.3)
    else: return {"ok": False, "why": "冇眼錨點"}
    if "eyeL" in an: ex, ey = an["eyeR"][0] - an["eyeL"][0], an["eyeR"][1] - an["eyeL"][1]; v = (ey, -ex)
    else: v = (0, -1)
    if "bulb" in an and AXIS.get(form) != "eyes":
        vb = (an["bulb"][0] - em[0], an["bulb"][1] - em[1])
        d = math.degrees(math.atan2(vb[0], -vb[1]) - math.atan2(v[0], -v[1]))
        d = (d + 180) % 360 - 180
        if abs(d) <= 40: v = vb          # 燈泡喺頭頂先用佢定 axis（lumi 尾燈、dust、moon 唔係）
    L = math.hypot(*v) or 1; u = (v[0] / L, v[1] / L); pp = (-u[1], u[0])
    r = max(2, int(round(S * 0.11)))
    # 由眼中點沿 axis 向上，搵最後一個 ±r 全實嘅點
    top = None; t = 0
    while t < S:
        p = (em[0] + u[0] * t, em[1] + u[1] * t)
        if _run(a, p, pp, r): top = p
        elif top is not None: break
        t += 0.5
    if top is None: return {"ok": False, "why": "搵唔到頭頂"}
    top = (int(round(top[0])), int(round(top[1])))
    hw = _width(a, (top[0] - u[0] * 2, top[1] - u[1] * 2), pp)
    hh = math.hypot(top[0] - em[0], top[1] - em[1])
    ang = math.degrees(math.atan2(u[0], -u[1]))
    f = {"ok": True, "u": u, "pp": pp, "top": top, "hw": hw, "hh": hh, "ang_abs": ang, "em": em}
    if ref:
        da = ang - ref["ang_abs"]; f["ang"] = 0.0 if abs(da) < 6 else da
        f["ws"] = hw / ref["hw"]; f["hs"] = hh / max(ref["hh"], 1)
    else: f["ang"] = 0.0; f["ws"] = 1.0; f["hs"] = 1.0
    return f

# ================================================================ label map → 轉角 → 描邊上光
def _L(c): return (LAB[c] if c else 0) if isinstance(c, str) else c
class Spr:
    def __init__(s, w, h): s.w, s.h = w, h; s.m = np.zeros((h, w), np.int16)
    def px(s, x, y, c):
        c = _L(c)
        x, y = int(round(x)), int(round(y))
        if 0 <= x < s.w and 0 <= y < s.h: s.m[y, x] = c
    def ell(s, cx, cy, rx, ry, c, half=None):
        c = _L(c)
        yy, xx = np.mgrid[0:s.h, 0:s.w]; m = ((xx - cx) / max(rx, .01)) ** 2 + ((yy - cy) / max(ry, .01)) ** 2 <= 1.0
        if half == "top": m &= yy <= cy
        if half == "bot": m &= yy >= cy
        s.m[m] = c
    def rect(s, x0, y0, x1, y1, c):
        c = _L(c)
        s.m[max(0, int(y0)):max(0, int(y1) + 1), max(0, int(x0)):max(0, int(x1) + 1)] = c
    def poly(s, pts, c):
        c = _L(c)
        mk = Image.new("L", (s.w * 4, s.h * 4), 0); ImageDraw.Draw(mk).polygon([(x * 4, y * 4) for x, y in pts], fill=255)
        s.m[np.asarray(mk.resize((s.w, s.h), Image.BOX)) >= 128] = c
    def line(s, x0, y0, x1, y1, c):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1): t = i / max(n, 1); s.px(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, c)
LAB = {}; RAMP = {}
def mat(name, shade, base, hi):
    if name not in LAB: LAB[name] = len(LAB) + 1
    RAMP[LAB[name]] = (shade, base, hi); return LAB[name]
GOLD = mat("gold", "egg_dark", "glow", "glow_core"); STRAW = mat("straw", "egg_dark", "egg_shade", "glow_mid"); STRAWD = mat("strawd", "egg_dark", "egg_dark", "egg_shade")
RED = mat("red", "berry_d", "berry", "blush"); REDF = mat("redf", "berry", "berry", "berry"); PINK = mat("pink", "blush_d", "blush", "white"); PINKD = mat("pinkd", "blush_d", "blush_d", "blush_d")
WHITE = mat("white", "cream3", "white", "white"); BLUE = mat("blue", "drop_d", "drop", "white"); LEAF = mat("leaf", "leaf_d", "leaf", "leaf"); LEAFD = mat("leafd", "leaf_d", "leaf_d", "leaf_d")
BROWN = mat("brown", "orange_dd", "orange_d", "orange"); BROWND = mat("brownd", "orange_dd", "orange_dd", "orange_d"); ORANGE = mat("orange", "orange_d", "orange", "glow_mid")
PURPLE = mat("purple", "zzz", "zzz", "white"); GLASS = mat("glass", "drop_d", "drop", "white"); CYAN = mat("cyan", "drop", "cyan", "white"); INK = mat("ink", "outline", "outline", "outline")
SNOW = mat("snow", "drop", "white", "white"); SNOWC = mat("snowc", "white", "white", "white"); SHELL = mat("shell", "cream0", "cream2", "cream4"); REDD = mat("redd", "berry_d", "berry_d", "berry_d")
GLOWT = mat("glowt", "glow_mid", "glow_mid", "glow_mid"); GLOWT2 = mat("glowt2", "glow_warm", "glow_warm", "glow_warm"); CREAM = mat("cream", "cream1", "cream3", "cream4")

def rotate_labels(m, piv, ang):
    """nearest 轉 label map（以 piv 為軸，ang 度，正＝順時針）；回傳新 map＋新 piv"""
    if abs(ang) < 1e-6: return m, piv
    h, w = m.shape; R = int(math.ceil(math.hypot(w, h))) + 2
    out = np.zeros((2 * R + 1, 2 * R + 1), m.dtype); a = math.radians(ang); ca, sa = math.cos(a), math.sin(a)
    yy, xx = np.mgrid[0:2 * R + 1, 0:2 * R + 1]; dx, dy = xx - R, yy - R
    sx = ca * dx + sa * dy + piv[0]; sy = -sa * dx + ca * dy + piv[1]
    xi, yi = np.round(sx).astype(int), np.round(sy).astype(int); ok = (xi >= 0) & (xi < w) & (yi >= 0) & (yi < h)
    out[ok] = m[yi[ok], xi[ok]]
    ys, xs = np.nonzero(out)
    if not len(xs): return m, piv
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    return out[y0:y1 + 1, x0:x1 + 1], (R - x0, R - y0)
def render(m, outline=True, shade=True):
    """m: label map（0＝空）→ RGBA，四邊加 1px 描邊位。hi＝上／左邊緣，shade＝下／右邊緣"""
    h, w = m.shape; M = np.zeros((h + 2, w + 2), m.dtype); M[1:-1, 1:-1] = m
    img = np.zeros((h + 2, w + 2, 4), np.uint8)
    up = np.roll(M, 1, 0); lf = np.roll(M, 1, 1); dn = np.roll(M, -1, 0); rt = np.roll(M, -1, 1)
    for lab, (sh, base, hi) in RAMP.items():
        sel = M == lab
        if not sel.any(): continue
        img[sel, :3] = rgb(base)
        if shade:
            e_hi = sel & ((up != lab) | (lf != lab)); img[e_hi, :3] = rgb(hi)
            e_sh = sel & ((dn != lab) | (rt != lab)); img[e_sh, :3] = rgb(sh)
        img[sel, 3] = 255
    if outline:
        a = img[..., 3] > 0; e = np.zeros_like(a)
        e[1:] |= a[:-1]; e[:-1] |= a[1:]; e[:, 1:] |= a[:, :-1]; e[:, :-1] |= a[:, 1:]
        e &= ~a; img[e, :3] = rgb("outline"); img[e, 3] = 255
    return img

# ================================================================ 飾品 generator（參數化：每幀按 fit 重畫）
def odd(x, lo=3): x = max(lo, int(round(x))); return x | 1
def gen_straw(W, H):
    s = Spr(W, H); c = (W - 1) / 2; cw = W * 0.29
    s.ell(c, H - 1.6, W / 2 - .2, max(1.25, H * 0.2), STRAW)
    s.ell(c, H - 2.2, cw, H - 2.2, STRAW, "top")
    yb = H - 3; s.rect(int(round(c - cw)) + 1, yb, int(round(c + cw)) - 1, yb, RED)
    if H >= 9: s.rect(int(round(c - cw)) + 1, yb - 1, int(round(c + cw)) - 1, yb - 1, RED)
    for x in range(1, W - 1, 3):
        if s.m[H - 1, x]: s.m[H - 1, x] = STRAWD
    if W >= 21:   # 編織紋：錯開短點（唔好斜紋）
        for y in range(2, yb - 1, 2):
            for x in range(W):
                if s.m[y, x] == STRAW and (x + (y // 2) * 2) % 4 == 0: s.m[y, x] = STRAWD
    return s.m, ((W - 1) / 2, H - 1)        # piv＝帽底中心
def gen_bow(W, H):
    s = Spr(W, H); c = (W - 1) / 2; m = (H - 1) / 2
    s.poly([(0, 0), (c + .5, m - .3), (c + .5, m + 1.3), (0, H)], PINK); s.poly([(W, 0), (c + .5, m - .3), (c + .5, m + 1.3), (W, H)], PINK)
    if W >= 11:   # 大啲嘅蝴蝶結加摺線
        s.line(1, 1, c - 1, m, PINKD); s.line(W - 2, 1, c + 1, m, PINKD)
    s.ell(c, m, max(.8, W * .09), max(.8, W * .09), PINKD)
    if W >= 13:   # 帶尾
        s2 = Spr(W, H + 3); s2.m[:H] = s.m; s2.poly([(c - 1, m + 1), (c + .5, m + 1), (c - 2.5, H + 2.6), (c - 4, H + 1.8)], PINK); s2.poly([(c + .5, m + 1), (c + 2, m + 1), (c + 5, H + 1.8), (c + 3.5, H + 2.6)], PINK)
        return s2.m, (c, m)
    return s.m, (c, m)

# ================================================================ 逐形態手調表（睇完 preview 先定）
# dx/dy：帽／結位置微調（相對 fit，idle 座標）；sc：尺寸倍率；variant：hatpin（本身有帽嘅形態）
FIT = {
    "straw": {f: {"dx": 0, "dy": 0, "sc": 1.0} for f in FORMS},
    "bow": {f: {"dx": 0, "dy": 0, "sc": 1.0} for f in FORMS},
    "scarf": {f: {"dy": 0, "th": 0} for f in FORMS},
}
for f in HATFORMS: FIT["straw"][f] = {"dx": 0, "dy": 0, "sc": 1.0, "variant": "hatpin"}
for f in ("evo_guard_moon", "evo_still_moon"): FIT["straw"][f]["pin"] = "r"
FIT["straw"]["evo_guard_moon"]["sc"] = 1.45; FIT["straw"]["evo_still_moon"]["sc"] = 0.75
# hw 俾頂帽／耳／葉拉闊或者收窄嘅形態 → 蝴蝶結尺寸手調
for f_, k_ in {"evo_still_moon": 0.62, "evo_guard_moon": 1.4, "evo_still_radiant": 0.8, "evo_still_ember": 0.85, "evo_still_soft": 0.9}.items(): FIT["bow"][f_]["sc"] = k_
FIT["straw"]["evo_still_radiant"]["sc"] = 0.8; FIT["straw"]["evo_still_soft"]["sc"] = 0.9; FIT["straw"]["evo_still_ember"]["sc"] = 0.85
FIT["bow"]["evo_guard_lumi"].update(dy=2, sc=0.85); FIT["bow"]["evo_still_lumi"].update(dy=1, sc=0.9)

def place(canvas, spr, x, y):
    """spr（RGBA）左上角放喺 canvas (x,y)（canvas 座標，已含 PAD）"""
    h, w = spr.shape[:2]; H, W = canvas.shape[:2]
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0: return
    sub = spr[y0 - y:y1 - y, x0 - x:x1 - x]; m = sub[..., 3] > 0; canvas[y0:y1, x0:x1][m] = sub[m]

def head_cut(body, f):
    """身體幀入面「頭頂以上、axis 附近」嘅像素（燈泡／莖／光芒）→ 帽要挖空"""
    a = body[..., 3] > 0; H, W = a.shape; yy, xx = np.mgrid[0:H, 0:W]
    dx, dy = xx - f["top"][0], yy - f["top"][1]
    along = dx * f["u"][0] + dy * f["u"][1]; perp = np.abs(dx * f["pp"][0] + dy * f["pp"][1])
    lum = body[..., :3].astype(int).sum(-1)          # 深色描邊／莖唔挖（俾帽蓋住，洞口先乾淨）
    return a & (along > 0.5) & (perp <= max(2.5, 0.45 * f["hw"])) & (lum > 3 * 90)

def face_px(an, S):
    """五官保護區：eyeL/eyeR ±1、mouth ±1（faceVisible 先計）"""
    pts = []
    if an.get("faceVisible", True):
        for k in ("eyeL", "eyeR", "mouth"):
            if k in an:
                x, y = an[k]; pts += [(x + i, y + j) for i in (-1, 0, 1) for j in (-1, 0, 1)]
    return pts

def draw_straw(body, an, f, ref, form, prev=None):
    S = body.shape[0]; cfg = FIT["straw"][form]; can = np.zeros((S + 2 * PAD, S + 2 * PAD, 4), np.uint8)
    if cfg.get("variant") == "hatpin":
        # 帽針：細草帽掛喺本身頂帽側面（head_l 上面）
        if cfg.get("pin") == "r": cx = an["head_r"][0] - 3; cy = an["head_r"][1] - 5
        else: cx = 2 * f["em"][0] - an["head_r"][0]; cy = an["head_r"][1] - 1
        W = odd(ref["hw"] * 0.62 * cfg["sc"] * min(max(f["ws"], .85), 1.15), 7); H = max(3, int(round(W * 0.42)))
        m, piv = gen_straw(W, H); m, piv = rotate_labels(m, piv, -14 + f["ang"])
        spr = render(m); px_, py_ = piv[0] + 1, piv[1] + 1
        place(can, spr, int(round(cx + cfg["dx"] - px_)) + PAD, int(round(cy + cfg["dy"] - py_)) + PAD)
        return can, {"variant": "hatpin", "pos": [round(cx, 1), cy], "W": W, "H": H}
    ws = min(max(f["ws"], 0.8), 1.3); hs = min(max(f["hs"], 0.8), 1.25)
    W = odd(ref["hw"] * 1.2 * cfg["sc"] * ws, 9); H = max(4, int(round(ref["hw"] * 1.2 * cfg["sc"] * 0.42 * (0.5 + 0.5 * hs))))
    m, piv = gen_straw(W, H); m, piv = rotate_labels(m, piv, f["ang"])
    spr = render(m); px_, py_ = piv[0] + 1, piv[1] + 1
    sink = max(1, int(round(ref["hw"] * 0.13)))       # 帽沉落頭頂幾多 px
    bx = f["top"][0] - f["u"][0] * sink + cfg["dx"]; by = f["top"][1] - f["u"][1] * sink + cfg["dy"]
    x, y = int(round(bx - px_)), int(round(by - py_))
    # 唔可以遮眼：帽底要喺眼上面 ≥2px
    fp = face_px(an, S)
    for _ in range(6):
        tmp = np.zeros_like(can); place(tmp, spr, x + PAD, y + PAD)
        if not any(tmp[py + PAD, px + PAD, 3] for px, py in fp if 0 <= px + PAD < tmp.shape[1] and 0 <= py + PAD < tmp.shape[0]): break
        y -= 1
    place(can, spr, x + PAD, y + PAD)
    cut = head_cut(body, f); sub = can[PAD:PAD + S, PAD:PAD + S]
    hole = cut & (sub[..., 3] > 0); sub[hole] = 0
    # 莖／燈穿過帽：洞口一圈補描邊（帽像素貼住洞 → outline 色）
    if hole.any():
        e = np.zeros_like(hole); e[1:] |= hole[:-1]; e[:-1] |= hole[1:]; e[:, 1:] |= hole[:, :-1]; e[:, :-1] |= hole[:, 1:]
        e &= (sub[..., 3] > 0); sub[e, :3] = rgb("outline")
    return can, {"variant": "hat", "piv": [round(bx, 1), round(by, 1)], "W": W, "H": H, "ang": round(f["ang"], 1)}

def draw_bow(body, an, f, ref, form, prev=None):
    S = body.shape[0]; cfg = FIT["bow"][form]; can = np.zeros((S + 2 * PAD, S + 2 * PAD, 4), np.uint8)
    ws = min(max(f["ws"], 0.8), 1.25)
    W = odd(ref["hw"] * 0.6 * cfg["sc"] * ws, 7); H = odd(W * 0.56, 5)
    m, piv = gen_bow(W, H); m, piv = rotate_labels(m, piv, f["ang"] + 12)
    spr = render(m); px_, py_ = piv[0] + 1, piv[1] + 1
    cx, cy = an["head_r"][0] + cfg["dx"], an["head_r"][1] + 1 + cfg["dy"]
    x, y = int(round(cx - px_)), int(round(cy - py_))
    fp = face_px(an, S)
    for _ in range(6):
        tmp = np.zeros_like(can); place(tmp, spr, x + PAD, y + PAD)
        if not any(tmp[py + PAD, px + PAD, 3] for px, py in fp if 0 <= px + PAD < tmp.shape[1] and 0 <= py + PAD < tmp.shape[0]): break
        x += 1; y -= 1
    place(can, spr, x + PAD, y + PAD)
    return can, {"pos": [cx, cy], "W": W, "H": H, "ang": round(f["ang"] + 12, 1)}

def neck_gap(ref): return max(2, min(3, int(round(ref["hw"] * 0.14))))
def draw_scarf(body, an, f, ref, form, prev=None):
    S = body.shape[0]; cfg = FIT["scarf"][form]; can = np.zeros((S + 2 * PAD, S + 2 * PAD, 4), np.uint8)
    a = body[..., 3] > 0
    th = max(2, int(round(ref["hw"] / 7))) + cfg["th"]
    if "mouth" in an and an.get("faceVisible", True): ny = an["mouth"][1] + neck_gap(ref)
    else: ny = int(round(f["em"][1] + ref["neck_off"] * f["hs"]))
    ny += cfg["dy"]
    cx = f["em"][0]; t = math.tan(math.radians(f["ang"])) if f["ang"] else 0.0
    # 中心行身體 run（只計連住中心嗰段，唔包片葉／道具）
    def run_at(y):
        if not (0 <= y < S): return None
        xc = int(round(cx))
        if not a[y, xc]: return None
        xl = xc
        while xl - 1 >= 0 and a[y, xl - 1]: xl -= 1
        xr = xc
        while xr + 1 < S and a[y, xr + 1]: xr += 1
        return xl, xr
    rr = run_at(ny)
    if rr is None: return None, {"why": "頸位冇身體"}
    if "neck_half" in ref:     # 唔包道具（例：月眠靜光個月牙）：run 夾喺 idle 頸闊 × ws ＋2
        lim = ref["neck_half"] * min(max(f["ws"], .8), 1.3) + 2
        rr = (max(rr[0], int(math.floor(cx - lim))), min(rr[1], int(math.ceil(cx + lim))))
    xl, xr = rr; lab = np.zeros((S + 2 * PAD, S + 2 * PAD), np.int16)
    for x in range(xl - 1, xr + 2):
        dyx = int(round(-t * (x - cx)))
        for r in range(th):
            y = ny + dyx + r
            # 每行再用剪影收邊（身體闊度會變）
            rr2 = run_at(y) if 0 <= y < S else None
            if rr2 is None or not (max(rr2[0], xl) - 1 <= x <= min(rr2[1], xr) + 1): continue
            lab[y + PAD, x + PAD] = WHITE if ((x - xl) // 2) % 3 == 0 else RED
    # 尾巴（右邊，慣性：身體中心向右郁 → 尾向左擺）
    lag = 0
    if prev is not None: lag = int(max(-2, min(2, -(f["em"][0] - prev["em"][0]))))
    tl = th * 2 + 1; tw = max(2, th)
    x0 = xr - th - tw // 2 + 1
    for j in range(tl):
        sw = int(round(lag * j / max(tl - 1, 1)))
        for i in range(tw):
            x = x0 + i + sw; y = ny + int(round(-t * (x0 - cx))) + th + j
            if 0 <= y + PAD < lab.shape[0] and 0 <= x + PAD < lab.shape[1]:
                lab[y + PAD, x + PAD] = WHITE if j >= tl - 2 else RED
    img = render(lab)[1:-1, 1:-1]
    # 唔遮五官
    for px, py in face_px(an, S): img[py + PAD, px + PAD] = 0
    return img, {"ny": ny, "th": th, "run": [xl, xr], "lag": lag, "ang": round(f["ang"], 1)}

ITEMS = {
    "straw": {"name": "草帽", "slot": "head", "anchor": "top", "draw": draw_straw, "batch": "ACC1"},
    "bow": {"name": "蝴蝶結", "slot": "side_r", "anchor": "head_r", "draw": draw_bow, "batch": "ACC1"},
    "scarf": {"name": "頸巾", "slot": "neck", "anchor": "neck", "draw": draw_scarf, "batch": "ACC1"},
}

# ================================================================ 收藏品 12 件（16／32 各自 raster）
def col_draw(key, n):
    s = Spr(n - 2, n - 2); m = n - 2; c = (m - 1) / 2; u = m / 14
    if key == "petal":
        s.poly([(c, 1 * u), (c + 4.5 * u, 5 * u), (c + 3.5 * u, 11 * u), (c + .5, 12.5 * u), (c - 3 * u, 11 * u), (c - 4.5 * u, 5 * u)], "pink")
        s.poly([(c - .5, 0), (c + 1.5, 0), (c + .5, 2.2 * u)], "") ; s.line(c + .3, 3 * u, c + .3, 9 * u, "pinkd")
    elif key == "snail":
        s.ell(c, c, 6 * u, 6 * u, "shell")
        for t in np.linspace(0, 4.2 * math.pi, 220):
            r = 5.4 * u * (1 - t / (4.6 * math.pi)); s.px(c + math.cos(t) * r, c + math.sin(t) * r, "brown")
    elif key == "cicada":
        s.ell(c, 4 * u, 3 * u, 2.5 * u, "shell"); s.poly([(c - 3.5 * u, 5 * u), (c + 3.5 * u, 5 * u), (c + 2 * u, 13 * u), (c - 2 * u, 13 * u)], "shell")
        for y in np.arange(7 * u, 13 * u, 2 * u): s.line(c - 2.5 * u, y, c + 2.5 * u, y, "brown")
        s.px(c - 1.6 * u, 3.5 * u, "brownd"); s.px(c + 1.6 * u, 3.5 * u, "brownd")
        for sgn in (-1, 1): s.line(c + sgn * 3 * u, 7 * u, c + sgn * 5.5 * u, 9 * u, "brown")
    elif key == "sunflower":
        for i in range(10): a = i * math.pi / 5; s.ell(c + math.cos(a) * 4.9 * u, c + math.sin(a) * 4.9 * u, 1.7 * u, 1.7 * u, "gold" if i % 2 else "straw")
        s.ell(c, c, 3.4 * u, 3.4 * u, "brownd")
        for i in range(0, 20, 3): s.px(c + math.cos(i) * 1.8 * u, c + math.sin(i) * 1.8 * u, "brown")
    elif key == "maple":
        pts = []
        for i in range(10):
            a = -math.pi / 2 + i * 2 * math.pi / 10; r = (6.3 if i % 2 == 0 else 3.2) * u
            if i == 5: r = 1.2 * u
            pts.append((c + .5 + math.cos(a) * r, c + .5 + math.sin(a) * r))
        s.poly(pts, "red"); s.line(c + .3, c + 1, c + .3, 13.5 * u, "brownd")
        for i in (1, 3, 7, 9): a = -math.pi / 2 + i * 2 * math.pi / 10; s.line(c + .3, c + .3, c + .3 + math.cos(a) * 3.8 * u, c + .3 + math.sin(a) * 3.8 * u, "redd")
    elif key == "acorn":
        s.ell(c, 8 * u, 4.4 * u, 5 * u, "orange"); s.ell(c, 5.2 * u, 5 * u, 2.6 * u, "brown", "top"); s.rect(int(c - 5 * u), int(5.2 * u), int(c + 5 * u), int(6.2 * u), "brownd"); s.line(c + .3, 0, c + 1, 2.6 * u, "brownd")
    elif key == "snowflake":
        for i in range(6):
            a = i * math.pi / 3; ex, ey = c + .4 + math.cos(a) * 6.3 * u, c + .4 + math.sin(a) * 6.3 * u; s.line(c + .4, c + .4, ex, ey, "snowc")
            mx, my = c + .4 + math.cos(a) * 3.8 * u, c + .4 + math.sin(a) * 3.8 * u
            if n >= 24:
                for d in (-1, 1): s.line(mx, my, mx + math.cos(a + d * .9) * 2 * u, my + math.sin(a + d * .9) * 2 * u, "snowc")
        s.px(c + .4, c + .4, "white")
    elif key == "snowman":
        s.ell(c, 9.5 * u, 4.3 * u, 4 * u, "snow"); s.ell(c, 4.2 * u, 3 * u, 2.9 * u, "snow")
        s.px(c - 1 * u, 3.8 * u, "ink"); s.px(c + 1 * u, 3.8 * u, "ink"); s.px(c + .4, 5 * u, "orange")
        s.rect(int(c - 3 * u), int(6.6 * u), int(c + 3 * u), int(7.2 * u), "red")
    elif key == "meteor":
        s.line(2 * u, 12 * u, 8 * u, 6 * u, "glowt"); s.line(1 * u, 10 * u, 6 * u, 5 * u, "glowt2")
        pts = [(9.5 * u + (4.2 * u if i % 2 == 0 else 1.9 * u) * math.sin(i * math.pi / 5), 4.5 * u - (4.2 * u if i % 2 == 0 else 1.9 * u) * math.cos(i * math.pi / 5)) for i in range(10)]
        s.poly(pts, "gold")
    elif key == "marble":
        s.ell(c, c, 6 * u, 6 * u, "glass")
        for i, col in enumerate(("red", "gold", "leaf", "purple")):
            for t in np.linspace(-.6, .6, 30): s.px(c + math.cos(t + i * 1.2) * (2 + i * .9) * u, c + math.sin(t + i * 1.2) * (2 + i * .9) * u, col)
    elif key == "clover":
        for a in (0, math.pi / 2, math.pi, 3 * math.pi / 2):
            px_, py_ = c + .5 + math.cos(a + math.pi / 4) * 3.3 * u, c - 1 * u + math.sin(a + math.pi / 4) * 3.3 * u; s.ell(px_, py_, 2.8 * u, 2.8 * u, "leaf")
        s.line(c + .5, c + 1 * u, c + 3 * u, 13 * u, "leafd"); s.px(c + .5, c - 1 * u, "gold")
    elif key == "goldbulb":
        s.ell(c, 5.5 * u, 4.6 * u, 4.8 * u, "gold"); s.rect(int(c - 2 * u), int(9.5 * u), int(c + 2 * u), int(12 * u), "brownd")
        for y in np.arange(10 * u, 12 * u, 1.2 * u): s.line(c - 2 * u, y, c + 2 * u, y, "brown")
        s.px(c - 1.6 * u, 3.5 * u, "white")
    return render(s.m, shade=n >= 24)
COL = [("petal", "櫻花瓣", "春"), ("snail", "蝸牛殼", "雨"), ("cicada", "蟬殼", "夏"), ("sunflower", "迷你向日葵", "夏"), ("maple", "紅楓葉", "秋"), ("acorn", "橡果", "秋"),
       ("snowflake", "雪花結晶", "冬"), ("snowman", "迷你雪人", "冬"), ("meteor", "流星碎", "稀有"), ("marble", "彩虹玻璃珠", "稀有"), ("clover", "四葉草", "稀有"), ("goldbulb", "金燈泡", "極稀有")]
COL_OBTAIN = {"petal": "3–5 月晴天 H1／H3（湊 5 片 → 櫻花髮飾）", "snail": "落雨或雨停後 2h", "cicada": "6–8 月 H1–H3", "sunflower": "6–8 月晴天",
    "maple": "9–11 月", "acorn": "9–11 月（湊 5 粒 → 橡果帽）", "snowflake": "12–2 月陰／霧", "snowman": "12–2 月連續 3 日有上線",
    "meteor": "H4 夜晚 1%（月眠領先 ×2）", "marble": "雨停後第 1 個鐘 2%", "clover": "任何晴天 1%", "goldbulb": "0.2%；保底：累計執 50 件必出（唔係抽卡，冇得買）"}
COL_RARITY = {"春": "common", "雨": "common", "夏": "common", "秋": "common", "冬": "common", "稀有": "rare", "極稀有": "legendary"}
def silhouette(img):
    o = np.zeros_like(img); m = img[..., 3] > 0; o[m, :3] = rgb("cream1"); o[m, 3] = 255
    a = m; e = np.zeros_like(a); e[1:] |= a[:-1]; e[:-1] |= a[1:]; e[:, 1:] |= a[:, :-1]; e[:, :-1] |= a[:, 1:]
    inner = m & ~(np.roll(a, 1, 0) & np.roll(a, -1, 0) & np.roll(a, 1, 1) & np.roll(a, -1, 1)); o[inner, :3] = rgb("cream0"); return o
def build_collectibles():
    os.makedirs(COLD, exist_ok=True); frames = {}; meta = []
    for key, name, cat in COL:
        for n in (16, 32):
            im = col_draw(key, n); assert im.shape[:2] == (n, n), (key, n, im.shape)
            Image.fromarray(im, "RGBA").save(os.path.join(COLD, f"col_{key}_{n}.png"), optimize=True)
            sil = silhouette(im); Image.fromarray(sil, "RGBA").save(os.path.join(COLD, f"col_{key}_{n}_sil.png"), optimize=True)
            frames[f"col_{key}_{n}"] = im; frames[f"col_{key}_{n}_sil"] = sil
        meta.append({"key": key, "name": name, "category": cat, "rarity": COL_RARITY[cat], "obtain": COL_OBTAIN[key],
                     "icon16": f"col_{key}_16.png", "icon32": f"col_{key}_32.png", "silhouette16": f"col_{key}_16_sil.png", "silhouette32": f"col_{key}_32_sil.png",
                     "unlocks": {"petal": "sakura", "acorn": "acorn"}.get(key)})
    # atlas：固定格（32 一行 12 格 ×2（彩／剪影），16 一行）— 唔 trim，方便 UI
    W = 12 * 36; atl = np.zeros((2 * 36 + 2 * 20, W, 4), np.uint8); fj = {}
    for i, (key, _, _) in enumerate(COL):
        for j, (suf, n, y) in enumerate([("", 32, 2), ("_sil", 32, 38), ("", 16, 74), ("_sil", 16, 94)]):
            nm = f"col_{key}_{n}{suf}"; x = i * 36 + 2; atl[y:y + n, x:x + n] = frames[nm]
            fj[nm] = {"frame": {"x": x, "y": y, "w": n, "h": n}, "rotated": False, "trimmed": False, "spriteSourceSize": {"x": 0, "y": 0, "w": n, "h": n}, "sourceSize": {"w": n, "h": n}}
    Image.fromarray(atl, "RGBA").save(os.path.join(COLD, "atlas_collectibles.png"), optimize=True)
    json.dump({"frames": fj, "meta": {"image": "atlas_collectibles.png", "size": {"w": W, "h": atl.shape[0]}, "padding": 2, "extrude": 0, "palette": "v3 (motion/palette.json)",
               "note": "收藏櫃第 2 頁「季節／稀有」12 格。_sil＝未收集剪影（icon alpha 自動出）。16px 唔上光（太細），32px 有上光。"}},
              open(os.path.join(COLD, "atlas_collectibles.json"), "w"), ensure_ascii=False, indent=1)
    json.dump({"version": 1, "batch": "ACC1", "page": "收藏櫃第 2 頁（季節／稀有）", "items": meta,
               "note": "攞法係建議值，等遊策落 config；全部唔使真錢、冇 gacha。"}, open(os.path.join(COLD, "collectibles.json"), "w"), ensure_ascii=False, indent=1)
    return meta

# ================================================================ 預覽
def comp(body, ov):
    S = body.shape[0]; c = np.zeros_like(ov); c[PAD:PAD + S, PAD:PAD + S] = body
    m = ov[..., 3] > 0; c[m] = ov[m]; return c
def font(sz):
    for p in ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc", "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc"):
        if os.path.exists(p): return ImageFont.truetype(p, sz)
    return ImageFont.load_default()
def sheet(cells, cols, cell, scale, labels=None, title=None, bg=(246, 240, 230)):
    """cells: list of RGBA np arrays（任何尺寸，置中放喺 cell×cell）"""
    rows = (len(cells) + cols - 1) // cols; th = 22 if title else 0; lh = 14 if labels else 0
    W = cols * cell * scale; H = th + rows * (cell * scale + lh)
    im = Image.new("RGB", (W, H), bg); d = ImageDraw.Draw(im); f = font(11)
    if title: d.text((6, 3), title, fill=(59, 42, 62), font=font(13))
    for i, c in enumerate(cells):
        r, k = divmod(i, cols); x0 = k * cell * scale; y0 = th + r * (cell * scale + lh)
        if (r + k) % 2: d.rectangle([x0, y0, x0 + cell * scale - 1, y0 + cell * scale - 1], fill=(236, 228, 216))
        if c is not None:
            t = Image.fromarray(c); t = t.resize((t.width * scale, t.height * scale), Image.NEAREST)
            im.paste(t, (x0 + (cell * scale - t.width) // 2, y0 + (cell * scale - t.height) // 2), t)
        if labels: d.text((x0 + 2, y0 + cell * scale), labels[i][:22], fill=(59, 42, 62), font=f)
    return im

# ================================================================ 逐幀生成 → 可見度 → atlas
def clips_of(form):
    an = anchors(form); return [(c, an[c]) for c in an]
NECK_LIM = {"evo_still_moon": 0.5}   # 月牙連住身體：頸巾只包身
def ref_fit(form):
    an = anchors(form); b = load(frame_path(form, "idle", 1)); r = fit(b, an["idle"][0], form=form)
    a0 = an["idle"][0]
    r["neck_off"] = (a0["mouth"][1] + neck_gap(r) - r["em"][1]) if "mouth" in a0 else r["hh"] * 0.8
    ny = int(round(r["em"][1] + r["neck_off"])); row = b[ny, :, 3] > 0; xc = int(round(r["em"][0])); xl = xr = xc
    while xl - 1 >= 0 and row[xl - 1]: xl -= 1
    while xr + 1 < len(row) and row[xr + 1]: xr += 1
    r["neck_half"] = max(xc - xl, xr - xc) * NECK_LIM.get(form, 1.0)
    return r
def overlaps_face(ov, an, S):
    for x, y in face_px(an, S):
        if ov[y + PAD, x + PAD, 3]: return True
    return False
GLOW_KEYS = ("bulb", "bulb2")
def cut_glow(ov, an):
    """燈泡／發光點 ±1 一律喺飾品層挖空 → 燈永遠喺面"""
    for k in GLOW_KEYS:
        if k in an:
            x, y = an[k]; ov[max(0, y - 1 + PAD):y + 2 + PAD, max(0, x - 1 + PAD):x + 2 + PAD] = 0
def overlaps_bulb(ov, body, an):
    """燈泡錨點本身（±1）唔可以俾飾品遮"""
    if "bulb" not in an: return False
    x, y = an["bulb"]
    if not body[y, x, 3]: return False
    return any(ov[y + j + PAD, x + i + PAD, 3] and body[y + j, x + i, 3] for i in (-1, 0, 1) for j in (-1, 0, 1)
               if 0 <= y + j < body.shape[0] and 0 <= x + i < body.shape[1])

def gen_item_form(item, form):
    """回傳 frames{name: ovRGBA}, fits{clip:[...]}, hidden{clip: why}"""
    ref = ref_fit(form); S = load(frame_path(form, "idle", 1)).shape[0]
    draw = ITEMS[item]["draw"]; frames = {}; fits = {}; hidden = {}
    manual = dict(HIDE.get(item, {}).get(form, {})); manual.update(HIDE.get(item, {}).get("*", {}))
    for clip, alist in clips_of(form):
        if clip in manual: hidden[clip] = manual[clip]; continue
        out = []; why = None; prev = None
        bodies = [load(frame_path(form, clip, k)) for k in range(1, len(alist) + 1)]
        fs = [fit(b, a, ref, form=form) for b, a in zip(bodies, alist)]
        bad = [k for k, f in enumerate(fs, 1) if not f["ok"]]
        if bad: hidden[clip] = f"{clip}_{bad[0]:02d}: {fs[bad[0] - 1]['why']}"; continue
        # 傾角：3-tap 平滑＋夾 ±28°（過渡幀唔會一下打側）
        raw = [f["ang"] for f in fs]
        for i, f in enumerate(fs):
            w = raw[max(0, i - 1):i + 2]; f["ang"] = max(-28.0, min(28.0, (sum(w) + raw[i]) / (len(w) + 1)))
            if abs(f["ang"]) < 4: f["ang"] = 0.0
        for k, an in enumerate(alist, 1):
            body = bodies[k - 1]; f = fs[k - 1]
            ov, info = draw(body, an, f, ref, form, prev)
            if ov is None: why = f"{clip}_{k:02d}: {info['why']}"; break
            if not ov[..., 3].any(): why = f"{clip}_{k:02d}: 飾品完全被遮"; break
            n0 = int((ov[..., 3] > 0).sum()); cut_glow(ov, an)
            if (ov[..., 3] > 0).sum() < 0.65 * n0: why = f"{clip}_{k:02d}: 燈泡位置喺飾品正中（挖空後剩唔夠 65%）"; break
            if overlaps_face(ov, an, S): why = f"{clip}_{k:02d}: 會遮五官"; break
            if overlaps_bulb(ov, body, an): why = f"{clip}_{k:02d}: 會遮燈泡"; break
            info.update({"top": list(f["top"]), "hw": f["hw"], "ws": round(f["ws"], 3), "hs": round(f["hs"], 3)})
            out.append((f"{clip}_{k:02d}", ov, info)); prev = f
        if why: hidden[clip] = why; continue
        for n, ov, info in out: frames[n] = ov
        fits[clip] = [i for _, _, i in out]
    return frames, fits, hidden, S

# 手動收起（睇完動作 preview 決定；原因會寫入 ACCESSORIES.json）
HIDE = {"straw": {"*": {"leaf_umbrella": "撐葉傘：葉蓋住頭頂，頭飾收起（避免帽畫喺葉上面）"}}}

def pack_atlas(frames, S, pad=2, extrude=1, maxw=1024):
    """trim → shelf pack；回傳 PIL image + frames json（TexturePacker 風格，同 evo6 atlas 一致）"""
    ents = []
    for n, ov in frames.items():
        ys, xs = np.nonzero(ov[..., 3]); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        ents.append((n, ov[y0:y1, x0:x1], x0, y0))
    order = sorted(ents, key=lambda e: (-e[1].shape[0], e[0]))
    x = y = 0; rowh = 0; pos = {}; g = pad + extrude
    for n, t, _, _ in order:
        h, w = t.shape[:2]
        if x + w + 2 * g > maxw: x = 0; y += rowh; rowh = 0
        pos[n] = (x + g, y + g); x += w + 2 * g; rowh = max(rowh, h + 2 * g)
    H = y + rowh; Wd = maxw if y else max(x, 1)
    def p2(v): n = 1
    atl = np.zeros((max(H, 1), Wd, 4), np.uint8); fj = {}
    for n, t, ox, oy in ents:
        px, py = pos[n]; h, w = t.shape[:2]; atl[py:py + h, px:px + w] = t
        # extrude 1px：複製邊緣（alpha 照樣 0/255）
        atl[py - 1, px:px + w] = t[0]; atl[py + h, px:px + w] = t[-1]; atl[py:py + h, px - 1] = t[:, 0]; atl[py:py + h, px + w] = t[:, -1]
        atl[py - 1, px - 1] = t[0, 0]; atl[py - 1, px + w] = t[0, -1]; atl[py + h, px - 1] = t[-1, 0]; atl[py + h, px + w] = t[-1, -1]
        fj[n] = {"frame": {"x": int(px), "y": int(py), "w": int(w), "h": int(h)}, "rotated": False, "trimmed": True,
                 "spriteSourceSize": {"x": int(ox) - PAD, "y": int(oy) - PAD, "w": int(w), "h": int(h)},
                 "sourceSize": {"w": S, "h": S}}
    return Image.fromarray(atl, "RGBA"), dict(sorted(fj.items()))

def form_anims(form):
    """抄返身體 atlas 嘅 fps/loop，令飾品 clip 同身體同步"""
    if form in ("sprout", "radiant", "soft"):
        cand = [os.path.join(LV, f"atlas_live_{form}.json"), os.path.join(MOT, f"atlas_{form}.json")]
    elif form == "lumi": cand = [os.path.join(LU, "atlas_lumi.json")]
    else: cand = [os.path.join(EV, f"atlas_{form}.json")]
    anim = {}
    for p in cand:
        if os.path.exists(p):
            for k, v in json.load(open(p)).get("animations", {}).items(): anim.setdefault(k, {"fps": v.get("fps"), "loop": v.get("loop")})
    return anim

def build_items(items):
    os.makedirs(ACCD, exist_ok=True); summary = {}
    for item in items:
        od = os.path.join(ACCD, "items", item); os.makedirs(od, exist_ok=True)
        fitall = {}; summary[item] = {}
        for form in FORMS:
            frames, fits, hidden, S = gen_item_form(item, form)
            img, fj = pack_atlas(frames, S)
            base = f"atlas_{item}_{form}"; img.save(os.path.join(od, base + ".png"), optimize=True)
            fa = form_anims(form); anims = {}
            for clip in fits:
                fr = [f"{clip}_{k:02d}" for k in range(1, len(fits[clip]) + 1)]
                anims[clip] = {"frames": fr, "fps": fa.get(clip, {}).get("fps"), "loop": fa.get(clip, {}).get("loop")}
            meta = {"image": base + ".png", "size": {"w": img.width, "h": img.height}, "padding": 2, "extrude": 1,
                    "item": item, "slot": ITEMS[item]["slot"], "form": form, "frameSize": S, "overlayPad": PAD,
                    "note": "飾品 overlay：spriteSourceSize 係相對身體幀左上（可以負數＝出 frame 邊）。畫喺 face 之上、emissive 之下；scaleX 鏡像同身體一齊。"}
            json.dump({"frames": fj, "animations": anims, "hiddenClips": hidden, "meta": meta},
                      open(os.path.join(od, base + ".json"), "w"), ensure_ascii=False, indent=1)
            fitall[form] = {"ref": {"top": list(ref_fit(form)["top"]), "hw": ref_fit(form)["hw"]}, "clips": fits}
            nclip = len(clips_of(form)); summary[item][form] = {"atlas": f"items/{item}/{base}.json", "clips": nclip,
                    "visibleClips": len(fits), "frames": len(frames), "hidden": hidden, "variant": FIT[item][form].get("variant", "default")}
            print(item, form, f"{len(fits)}/{nclip} clips", len(frames), "frames", "hidden:", list(hidden)[:6])
        json.dump(fitall, open(os.path.join(od, f"fit_{item}.json"), "w"), ensure_ascii=False, separators=(",", ":"))
    return summary

HIMOTION = ["cheer_jump", "lookup_tip", "getup", "rush", "picked_up", "turn_back", "sleep_loop", "leaf_umbrella", "shiver", "sneeze"]
def preview_motion(item, forms, clips, path, scale=3, maxf=8):
    cells = []; labs = []; cell = max(load(frame_path(f, "idle", 1)).shape[0] for f in forms) + 2 * PAD
    for form in forms:
        frames, fits, hidden, S = gen_item_form(item, form); an = anchors(form)
        for clip in clips:
            if clip not in an: continue
            for k in range(1, maxf + 1):
                if k > len(an[clip]): cells.append(None); labs.append(""); continue
                b = load(frame_path(form, clip, k)); n = f"{clip}_{k:02d}"
                ov = frames.get(n, np.zeros((S + 2 * PAD, S + 2 * PAD, 4), np.uint8))
                cells.append(comp(b, ov)); labs.append((form.replace("evo_", "") + " " if k == 1 else "") + (n if n in frames else n + " 隱"))
    im = sheet(cells, maxf, cell, scale, labs, f"{ITEMS[item]['name']} {item} — 動作跟隨"); im.save(path); return path
def preview_idle(items, path, forms=None, clip="idle", k=1, scale=3):
    forms = forms or FORMS; cells = []; labs = []
    for form in forms:
        b = load(frame_path(form, clip, k)); S = b.shape[0]; bb = np.zeros((S + 2 * PAD, S + 2 * PAD, 4), np.uint8); bb[PAD:PAD + S, PAD:PAD + S] = b
        cells.append(bb); labs.append(form.replace("evo_", ""))
        for it in items:
            frames, fits, hidden, _ = CACHE.get((it, form)) or CACHE.setdefault((it, form), gen_item_form(it, form))
            n = f"{clip}_{k:02d}"; cells.append(comp(b, frames[n]) if n in frames else bb); labs.append(ITEMS[it]["name"] + ("" if n in frames else " 隱"))
    im = sheet(cells, (len(items) + 1) * 2, 64 + 2 * PAD, scale, labs, f"飾品 × 25 形態 — {clip}_{k:02d}"); im.save(path); return path
CACHE = {}

# ================================================================ ACCESSORIES.json（merge-safe：保留其他批嘅 items／forms）
ALL_ITEMS = [  # 13 件總表（batch 未到嘅 status＝planned）
    ("straw", "草帽", "head", "top", "夏（6–8 月）收藏櫃集齊夏季小物 3 件（蟬殼／迷你向日葵＋1）", "ACC1"),
    ("beanie", "毛冷帽", "head", "top", "冬（12–2 月）第一次觸發 shiver 嗰日送（「凍親呀？」）", "ACC2"),
    ("nightcap", "睡帽", "head", "top", "日記連續寫滿 7 日；月眠路線領先時機會加倍", "ACC4"),
    ("crown", "小皇冠", "head", "top", "成就徽章 20 個（終局獎勵之一）", "ACC2"),
    ("acorn", "橡果帽", "head", "top", "秋（9–11 月）散步執夠橡果 ×5 自動合成", "ACC2"),
    ("bow", "蝴蝶結", "side_r", "head_r", "親密度到 40", "ACC1"),
    ("starclip", "星星髮夾", "side_l", "head_l", "星星碎商店 60", "ACC3"),
    ("sakura", "櫻花髮飾", "side_l", "head_l", "春（3–5 月）執夠櫻花瓣 ×5", "ACC3"),
    ("glasses", "圓框眼鏡", "face", "eyeL/eyeR", "日記翻舊頁 30 日／捉迷藏累計 10 局", "ACC3"),
    ("scarf", "頸巾", "neck", "neck", "霧天／冬陪佢玩 3 次", "ACC1"),
    ("leafcollar", "葉仔領", "neck", "neck", "小圃 6 種花各開過一次", "ACC4"),
    ("bell", "燈泡小鈴", "bulb", "bulb", "每日委託連續 14 日", "ACC4"),
    ("halo", "燈泡光環", "bulb", "bulb", "第一次進化成守護型／化光紀念", "ACC4"),
]
def size_class(S): return "S" if S <= 32 else ("M" if S <= 48 else "L")
def write_accessories_json(summary):
    p = os.path.join(ACCD, "ACCESSORIES.json")
    old = json.load(open(p)) if os.path.exists(p) else {}
    d = dict(old)
    d["version"] = max(1, old.get("version", 1))
    d["note"] = ("團絨飾品 overlay（完整版）。每個 item × form 一個 atlas；幀名同身體幀一樣（<clip>_NN）。"
                 "引擎：身體 → 臉 → 飾品（按 drawOrder）→ emissive；scaleX 鏡像同身體一齊。hiddenClips 入面嘅 clip 成段唔畫（唔會逐幀閃）。")
    d["slots"] = {"head": {"max": 1, "anchor": "top"}, "side_r": {"max": 1, "anchor": "head_r"}, "side_l": {"max": 1, "anchor": "head_l"},
                  "face": {"max": 1, "anchor": "eyeL/eyeR", "rule": "faceVisible=false 收起"}, "neck": {"max": 1, "anchor": "neck"},
                  "bulb": {"max": 1, "anchor": "bulb"}}
    d["drawOrder"] = ["body", "face", "neck", "head", "side_r", "side_l", "face_acc", "bulb", "emissive"]
    d["sizeClasses"] = {"S": {"maxFrame": 32, "forms": [f for f in FORMS if load(frame_path(f, "idle", 1)).shape[0] <= 32]},
                        "M": {"maxFrame": 48, "forms": [f for f in FORMS if 32 < load(frame_path(f, "idle", 1)).shape[0] <= 48]},
                        "L": {"maxFrame": 64, "forms": [f for f in FORMS if load(frame_path(f, "idle", 1)).shape[0] > 48]}}
    d["forms"] = FORMS; d["overlayPad"] = PAD
    d["fitRules"] = {"axis": "眼中點→燈泡（燈泡同眼線垂直方向差 ≤40° 先用；lumi 系用眼線）", "top": "沿 axis 向上，最後一個 ±0.11S 全實嘅點",
                     "hw": "頭頂下 2px 頭闊", "ang": "axis 相對 idle_01，3-tap 平滑，夾 ±28°，<4° 當 0", "hs": "頭高／idle 頭高",
                     "glowCut": "bulb／bulb2 ±1 飾品層一律挖空", "headCut": "head slot：頭頂以上、axis ±0.45hw 嘅身體像素（莖／燈／光芒）挖空",
                     "visibility": "一個 clip 任何一幀 fit 唔成立／遮五官／挖空後剩 <65% → 成段收起"}
    items = {it["key"]: it for it in old.get("items", [])} if isinstance(old.get("items"), list) else dict(old.get("items", {}))
    for key, name, slot, anc, obtain, batch in ALL_ITEMS:
        e = dict(items.get(key, {})); e.update({"key": key, "name": name, "slot": slot, "anchor": anc, "obtain": obtain, "batch": batch})
        if key in summary:
            e["status"] = "done"; e["fit"] = f"items/{key}/fit_{key}.json"; e["forms"] = summary[key]
            e["ref"] = {sc: f"ref/acc_{key}_{sc}.png" for sc in ("S", "M", "L")}
            e["counts"] = {"forms": len(summary[key]), "visibleClips": sum(v["visibleClips"] for v in summary[key].values()),
                           "clips": sum(v["clips"] for v in summary[key].values()), "frames": sum(v["frames"] for v in summary[key].values())}
        else: e.setdefault("status", "planned")
        items[key] = e
    d["items"] = items
    json.dump(d, open(p, "w"), ensure_ascii=False, indent=1)
    return d

def build_refs(items):
    """S／M／L 參考圖（idle_01 fit 出嚟嘅單件 sprite，俾 UI 衣櫃 icon／設計對照）"""
    rd = os.path.join(ACCD, "ref"); os.makedirs(rd, exist_ok=True)
    rep = {"S": "sprout", "M": "evo_guard_radiant", "L": "radiant"}
    for it in items:
        for sc, form in rep.items():
            frames, _, _, S = CACHE.get((it, form)) or CACHE.setdefault((it, form), gen_item_form(it, form))
            ov = frames["idle_01"]; ys, xs = np.nonzero(ov[..., 3])
            Image.fromarray(ov[ys.min():ys.max() + 1, xs.min():xs.max() + 1], "RGBA").save(os.path.join(rd, f"acc_{it}_{sc}.png"), optimize=True)

def build_previews(items):
    os.makedirs(PREV, exist_ok=True); out = []
    half = (len(FORMS) + 1) // 2
    out.append(preview_idle(items, os.path.join(PREV, "acc1_forms_idle_a_3x.png"), FORMS[:half]))
    out.append(preview_idle(items, os.path.join(PREV, "acc1_forms_idle_b_3x.png"), FORMS[half:]))
    out.append(preview_idle(items, os.path.join(PREV, "acc1_forms_walk03_a_3x.png"), FORMS[:half], clip="walk", k=3))
    out.append(preview_idle(items, os.path.join(PREV, "acc1_forms_walk03_b_3x.png"), FORMS[half:], clip="walk", k=3))
    sets = {"straw": (["sprout", "evo_guard_radiant", "radiant"], ["cheer_jump", "lookup_tip", "getup", "rush", "turn_back"]),
            "straw_b": (["lumi", "evo_still_moon", "evo_guard_shroom"], ["cheer_jump", "lookup_tip", "getup", "picked_up", "sleep_loop"]),
            "bow": (["evo_dot", "evo_guard_lumi", "soft"], ["cheer_jump", "lookup_tip", "getup", "rush", "turn_back"]),
            "scarf": (["evo_hop", "radiant", "evo_guard_dust"], ["cheer_jump", "lookup_tip", "rush", "picked_up", "leaf_umbrella"])}
    for k, (forms, clips) in sets.items():
        it = k.split("_")[0]
        if it in items: out.append(preview_motion(it, forms, clips, os.path.join(PREV, f"acc1_motion_{k}_3x.png"), scale=3, maxf=6))
    # 收藏品
    cells = []; labs = []
    for key, name, cat in COL:
        for suf in ("32", "32_sil", "16", "16_sil"):
            cells.append(np.array(Image.open(os.path.join(COLD, f"col_{key}_{suf}.png")).convert("RGBA"))); labs.append(f"{name} {suf}" if suf == "32" else suf)
    im = sheet(cells, 8, 36, 4, labs, "收藏品 12 件 — 32／剪影／16／剪影（4x）"); p = os.path.join(PREV, "acc1_collectibles_4x.png"); im.save(p); out.append(p)
    return out

def main(argv):
    what = argv[1] if len(argv) > 1 else "all"; items = [a for a in argv[2:]] or [k for k in ITEMS]
    if what in ("all", "collectibles"): build_collectibles()
    if what in ("all", "items"):
        summ = build_items(items); write_accessories_json(summ); build_refs(items)
    if what in ("all", "preview"): print("\n".join(build_previews(items)))
if __name__ == "__main__": main(sys.argv)
