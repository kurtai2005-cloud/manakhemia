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
KNIT = mat("knit", "drop", "drop", "cyan"); KNITD = mat("knitd", "drop_d", "drop_d", "drop_d"); CREAMD = mat("creamd", "cream3", "cream3", "cream3"); GOLDD = mat("goldd", "egg_dark", "egg_dark", "glow")
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
def gen_straw(W, H, weave=True):
    s = Spr(W, H); c = (W - 1) / 2; cw = W * 0.29
    s.ell(c, H - 1.6, W / 2 - .2, max(1.25, H * 0.2), STRAW)
    s.ell(c, H - 2.2, cw, H - 2.2, STRAW, "top")
    yb = H - 3; s.rect(int(round(c - cw)) + 1, yb, int(round(c + cw)) - 1, yb, RED)
    if H >= 9: s.rect(int(round(c - cw)) + 1, yb - 1, int(round(c + cw)) - 1, yb - 1, RED)
    for x in range(1, W - 1, 3):
        if s.m[H - 1, x]: s.m[H - 1, x] = STRAWD
    if W >= 21 and weave:   # 編織紋：錯開短點（唔好斜紋）
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
    "beanie": {f: {"dx": 0, "dy": 0, "sc": 1.0} for f in FORMS},
    "acorn": {f: {"dx": 0, "dy": 0, "sc": 1.0} for f in FORMS},
    "crown": {f: {"dx": 0, "dy": 0, "sc": 1.0} for f in FORMS},
}
FIT["starclip"] = {f: {"dx": 0, "dy": 0, "sc": 1.0} for f in FORMS}
FIT["sakura"] = {f: {"dx": 0, "dy": 0, "sc": 1.0} for f in FORMS}
FIT["glasses"] = {f: {"r": 0.0} for f in FORMS}
FIT["leafcollar"] = {f: {"dy": 0} for f in FORMS}
FIT["bell"] = {f: {"dx": 0, "dy": 0} for f in FORMS}
FIT["halo"] = {f: {"dx": 0, "dy": 0, "sc": 1.0} for f in FORMS}
FIT["nightcap"] = {f: {"dx": 0, "dy": 0, "sc": 1.0} for f in FORMS}
for f in HATFORMS: FIT["nightcap"][f] = {"dx": 0, "dy": 0, "sc": 1.0, "variant": "hatpin"}
for f in ("evo_guard_moon", "evo_still_moon"): FIT["nightcap"][f]["pin"] = "r"
FIT["nightcap"]["evo_guard_moon"]["sc"] = 1.8; FIT["nightcap"]["evo_still_moon"]["sc"] = 0.8
for f_, k_ in {"evo_still_radiant": 0.8, "evo_still_soft": 0.9, "evo_still_ember": 0.85}.items(): FIT["nightcap"][f_]["sc"] = k_
FIT["glasses"]["evo_dot"]["forehead"] = True   # ACC5：dot 口喺兩眼之間只低 2px，全框／¾ 框都撞，ACC3 半框睇落似眉毛 → 改做「眼鏡推上額頭」（全圓框，戴喺眼上面）；其餘形態一律 ¾ 圓框
for it_ in ("starclip", "sakura"):
    for f_, k_ in {"evo_still_moon": 0.62, "evo_guard_moon": 1.4, "evo_still_radiant": 0.8, "evo_still_ember": 0.85, "evo_still_soft": 0.9}.items(): FIT[it_][f_]["sc"] = k_
for it_ in ("beanie", "acorn", "crown"):
    for f in HATFORMS: FIT[it_][f] = {"dx": 0, "dy": 0, "sc": 1.0, "variant": "hatpin"}
    for f in ("evo_guard_moon", "evo_still_moon"): FIT[it_][f]["pin"] = "r"
    FIT[it_]["evo_guard_moon"]["sc"] = 1.8; FIT[it_]["evo_still_moon"]["sc"] = 0.8
    for f_, k_ in {"evo_still_radiant": 0.8, "evo_still_soft": 0.9, "evo_still_ember": 0.85}.items(): FIT[it_][f_]["sc"] = k_
for f in HATFORMS: FIT["straw"][f] = {"dx": 0, "dy": 0, "sc": 1.0, "variant": "hatpin"}
for f in ("evo_guard_moon", "evo_still_moon"): FIT["straw"][f]["pin"] = "r"
FIT["straw"]["evo_guard_moon"]["sc"] = 1.8; FIT["straw"]["evo_still_moon"]["sc"] = 0.75
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

def head_cut(body, f, full=False):
    """身體幀入面「頭頂以上、axis 附近」嘅像素（燈泡／莖／光芒）→ 帽要挖空"""
    a = body[..., 3] > 0; H, W = a.shape; yy, xx = np.mgrid[0:H, 0:W]
    dx, dy = xx - f["top"][0], yy - f["top"][1]
    along = dx * f["u"][0] + dy * f["u"][1]; perp = np.abs(dx * f["pp"][0] + dy * f["pp"][1])
    lum = body[..., :3].astype(int).sum(-1)          # 深色描邊／莖唔挖（俾帽蓋住，洞口先乾淨）
    m = a & (along > 0.5) & (perp <= max(2.5, 0.45 * f["hw"]))
    if not full: return m & (lum > 3 * 90)
    # lumi 系（ACC2 polish）：淨係挖葉（綠）＋葉嘅描邊；莖同淺紫毛唔挖 → 帽身乾淨，唔再有一條條碎洞
    c = body[..., :3].astype(int); g = a & (c[..., 1] > c[..., 0] + 25) & (c[..., 1] > c[..., 2] + 10)
    gd = g.copy(); gd[1:] |= g[:-1]; gd[:-1] |= g[1:]; gd[:, 1:] |= g[:, :-1]; gd[:, :-1] |= g[:, 1:]
    return m & (g | (gd & (lum < 3 * 90)))

def face_px(an, S):
    """五官保護區：eyeL/eyeR ±1、mouth ±1（faceVisible 先計）"""
    pts = []
    if an.get("faceVisible", True):
        for k in ("eyeL", "eyeR", "mouth"):
            if k in an:
                x, y = an[k]; pts += [(x + i, y + j) for i in (-1, 0, 1) for j in (-1, 0, 1)]
    return pts

# ---- head slot 通用（ACC2 起：草帽／毛冷帽／橡果帽／小皇冠共用；每件嘅形狀參數喺 HEAD）
def gen_beanie(W, H, L=False):
    s = Spr(W, H); c = (W - 1) / 2; cuff = 3 if W >= 25 else 2; pr = max(1.6, W * 0.12)
    top0 = pr * 1.2                                   # 冚帽頂留位畀 pompom
    s.ell(c, H - cuff, W / 2 - .3, H - cuff - top0 + .5, KNIT, "top")
    for x in range(W):                                # 直坑紋（knit）：深坑＋左邊亮邊
        if x % 3 == 1:
            col = s.m[:H - cuff, x]; col[col == KNIT] = KNITD
    s.rect(0, H - cuff, W - 1, H - 1, WHITE)
    for x in range(1, W - 1, 2): s.m[H - 1, x] = CREAMD if s.m[H - 1, x] == WHITE else s.m[H - 1, x]
    s.ell(c - W * 0.24, pr, pr + .2, pr + .2, WHITE)   # pompom 偏左（燈泡位喺正中）
    return s.m, ((W - 1) / 2, H - 1)
def gen_acorn(W, H, L=False):
    s = Spr(W, H); c = (W - 1) / 2; rim = 2 if W < 25 else 3
    s.ell(c, H - rim, W / 2 - .2, H - rim - 1.2, BROWN, "top")
    s.rect(0, H - rim, W - 1, H - 1, BROWND)
    step = 3 if W < 25 else 2                         # 鱗片紋：L 密啲
    for y in range(H - rim):
        for x in range(W):
            if s.m[y, x] == BROWN and ((x + y) % (step + 1) == 0 or (x - y) % (step + 1) == 0): s.m[y, x] = BROWND
    for x in range(1, W - 1, 3): s.m[H - 1, x] = ORANGE
    s.line(c + 1, 0, c + 1, 1.5, BROWND)               # 帽蒂（有燈泡嘅形態會俾燈挖走）
    return s.m, ((W - 1) / 2, H - 1)
def gen_crown(W, H, L=False):
    s = Spr(W, H); c = (W - 1) / 2; band = 2 if W < 13 else 3
    s.rect(0, H - band, W - 1, H - 1, GOLD)
    n = 3 if W < 23 else 5; pw = W / n                # 尖：細皇冠 3 支（闊啲先唔會變鋸齒）
    for i in range(n):
        x0 = i * pw; hgt = 0 if i == n // 2 else (H * 0.3 if abs(i - n // 2) == 1 else H * 0.45)
        s.poly([(x0 - .3, H - band + .5), (x0 + pw + .3, H - band + .5), (x0 + pw / 2, hgt)], GOLD)
        if L or W >= 15: s.px(x0 + pw / 2, hgt + .4, WHITE)   # 尖頂小珠（M／L）
    s.px(c, H - band + band // 2, RED)
    for d in (-1, 1): s.px(c + d * W * 0.3, H - band + band // 2, CYAN)
    if L or W >= 19:                                   # L（64px 形態）：中間紅寶石 3px＋帶底刻紋
        s.rect(int(c) - 1, H - band + 1, int(c) + 1, H - 2, RED); s.px(c, H - band, RED)
        for x in range(0, W, 2):
            if s.m[H - 1, x] == GOLD: s.m[H - 1, x] = GOLDD
    return s.m, ((W - 1) / 2, H - 1)
HEAD = {   # k：闊＝k×hw；hr：高／闊；sink：沉落頭頂（×hw）；pin：帽針版闊（×hw）；pin_ang：帽針斜角
    "straw": {"gen": lambda W, H, L=False: gen_straw(W, H), "k": 1.2, "hr": 0.42, "sink": 0.13, "minW": 9, "pin": 0.62, "pin_ang": -14},
    "beanie": {"gen": gen_beanie, "k": 1.04, "hr": 0.62, "sink": 0.22, "minW": 9, "pin": 0.55, "pin_ang": -18},
    "acorn": {"gen": gen_acorn, "k": 0.98, "hr": 0.5, "sink": 0.16, "minW": 9, "pin": 0.55, "pin_ang": -16},
    "crown": {"gen": gen_crown, "k": 0.68, "hr": 0.52, "sink": 0.04, "minW": 7, "pin": 0.5, "pin_ang": -12},
}
CUT_FULL = {"lumi", "evo_guard_lumi", "evo_still_lumi"}   # lumi 系：成棵芽（連莖）畫喺帽前面，唔留碎洞
def cut_hole(sub, cut):
    hole = cut & (sub[..., 3] > 0); sub[hole] = 0
    if not hole.any(): return
    # 執走洞邊嘅碎帽仔（4 鄰 ≥3 係空）→ 再補描邊
    for _ in range(2):
        a = sub[..., 3] > 0; nb = np.zeros(a.shape, int)
        for sh, ax in ((1, 0), (-1, 0), (1, 1), (-1, 1)): nb += ~np.roll(a, sh, ax)
        near = np.zeros_like(hole); near[1:] |= hole[:-1]; near[:-1] |= hole[1:]; near[:, 1:] |= hole[:, :-1]; near[:, :-1] |= hole[:, 1:]
        spur = a & (nb >= 3) & near; sub[spur] = 0; hole |= spur
    e = np.zeros_like(hole); e[1:] |= hole[:-1]; e[:-1] |= hole[1:]; e[:, 1:] |= hole[:, :-1]; e[:, :-1] |= hole[:, 1:]
    e &= (sub[..., 3] > 0); sub[e, :3] = rgb("outline")
def make_head_draw(item):
    P = HEAD[item]
    def draw(body, an, f, ref, form, prev=None):
        S = body.shape[0]; cfg = FIT[item][form]; can = np.zeros((S + 2 * PAD, S + 2 * PAD, 4), np.uint8)
        if cfg.get("variant") == "hatpin":
            # 帽針：細版掛喺本身頂帽側面
            if cfg.get("pin") == "r": cx = an["head_r"][0] - 3; cy = an["head_r"][1] - 5
            else: cx = 2 * f["em"][0] - an["head_r"][0]; cy = an["head_r"][1] - 1
            W = odd(ref["hw"] * P["pin"] * cfg["sc"] * min(max(f["ws"], .85), 1.15), 7); H = max(3, int(round(W * P["hr"])))
            m, piv = P["gen"](W, H); m, piv = rotate_labels(m, piv, P["pin_ang"] + f["ang"])
            spr = render(m); px_, py_ = piv[0] + 1, piv[1] + 1
            place(can, spr, int(round(cx + cfg["dx"] - px_)) + PAD, int(round(cy + cfg["dy"] - py_)) + PAD)
            return can, {"variant": "hatpin", "pos": [round(cx, 1), cy], "W": W, "H": H}
        ws = min(max(f["ws"], 0.8), 1.3); hs = min(max(f["hs"], 0.8), 1.25)
        W = odd(ref["hw"] * P["k"] * cfg["sc"] * ws, P["minW"]); H = max(4, int(round(ref["hw"] * P["k"] * cfg["sc"] * P["hr"] * (0.5 + 0.5 * hs))))
        if item == "straw" and form in ("evo_guard_lumi", "evo_still_lumi"): m, piv = gen_straw(W, H, weave=False)   # M 號 lumi：葉多，帽身唔加織紋
        else: m, piv = P["gen"](W, H, L=S >= 64)
        m, piv = rotate_labels(m, piv, f["ang"])
        spr = render(m); px_, py_ = piv[0] + 1, piv[1] + 1
        sink = max(1, int(round(ref["hw"] * P["sink"])))       # 沉落頭頂幾多 px
        bx = f["top"][0] - f["u"][0] * sink + cfg["dx"]; by = f["top"][1] - f["u"][1] * sink + cfg["dy"]
        x, y = int(round(bx - px_)), int(round(by - py_))
        fp = face_px(an, S)        # 唔可以遮五官：撞到就逐 px 升
        for _ in range(8):
            tmp = np.zeros_like(can); place(tmp, spr, x + PAD, y + PAD)
            if not any(tmp[py + PAD, px + PAD, 3] for px, py in fp if 0 <= px + PAD < tmp.shape[1] and 0 <= py + PAD < tmp.shape[0]): break
            y -= 1
        place(can, spr, x + PAD, y + PAD)
        cut_hole(can[PAD:PAD + S, PAD:PAD + S], head_cut(body, f, full=form in CUT_FULL))
        return can, {"variant": "hat", "piv": [round(bx, 1), round(by, 1)], "W": W, "H": H, "ang": round(f["ang"], 1)}
    return draw
draw_straw = make_head_draw("straw")

def is_back(an): return not an.get("faceVisible", True)
def flip_lab(m, piv):
    """ACC5 背面：模板左右反轉（pivot 跟住反）"""
    return m[:, ::-1].copy(), (m.shape[1] - 1 - piv[0], piv[1])
def draw_bow(body, an, f, ref, form, prev=None):
    S = body.shape[0]; cfg = FIT["bow"][form]; can = np.zeros((S + 2 * PAD, S + 2 * PAD, 4), np.uint8)
    ws = min(max(f["ws"], 0.8), 1.25)
    W = odd(ref["hw"] * 0.6 * cfg["sc"] * ws, 7); H = odd(W * 0.56, 5)
    bk = is_back(an); sg = -1 if bk else 1              # ACC5：背面（faceVisible=false）＝左右鏡像，結去返畫面左邊
    m, piv = gen_bow(W, H)
    if bk: m, piv = flip_lab(m, piv)
    m, piv = rotate_labels(m, piv, f["ang"] + 12 * sg)
    spr = render(m); px_, py_ = piv[0] + 1, piv[1] + 1
    if bk:
        a0 = anchors(form)["idle"][0]; ed0 = abs(a0["eyeR"][0] - a0["eyeL"][0]) if "eyeL" in a0 else None
        hx, hy = head_l(an, f, ed0); cx, cy = hx - cfg["dx"], hy + 1 + cfg["dy"]
    else: cx, cy = an["head_r"][0] + cfg["dx"], an["head_r"][1] + 1 + cfg["dy"]
    x, y = int(round(cx - px_)), int(round(cy - py_))
    fp = face_px(an, S)
    for _ in range(6):
        tmp = np.zeros_like(can); place(tmp, spr, x + PAD, y + PAD)
        if not any(tmp[py + PAD, px + PAD, 3] for px, py in fp if 0 <= px + PAD < tmp.shape[1] and 0 <= py + PAD < tmp.shape[0]): break
        x += sg; y -= 1
    place(can, spr, x + PAD, y + PAD)
    info = {"pos": [cx, cy], "W": W, "H": H, "ang": round(f["ang"] + 12 * sg, 1)}
    if bk: info["mirrored"] = True; info["pos"] = [round(float(cx), 1), round(float(cy), 1)]
    return can, info

# ---- side_l（ACC3）：head_l＝head_r 以 axis 為鏡反射（跟傾角）
def head_l(an, f, ed0=None):
    """head_r 嘅鏡像：有兩隻眼就以兩眼中垂線做鏡（月眠呢類闊剪影都準）；冇眼先用 fit 中軸"""
    hr = np.array(an["head_r"], float)
    if "eyeL" in an and "eyeR" in an:
        a, b = np.array(an["eyeL"], float), np.array(an["eyeR"], float); m = (a + b) / 2; e = b - a
        if np.hypot(*e) >= max(4, 0.75 * (ed0 or 0)):      # 側面（眼距縮）就用返 fit 中軸
            e = e / np.hypot(*e); return tuple(hr - 2 * ((hr - m) @ e) * e)
    em = np.array(f["em"], float); u = np.array(f["u"], float); v = hr - em
    par = (v @ u) * u; return tuple(em + par - (v - par))
# 細尺寸手點模板（7／9px 用 polygon 會糊成一團）：G 金、W 白、B 藍、P 粉、D 深粉
TPL_LAB = {"G": GOLD, "W": WHITE, "B": BLUE, "P": PINK, "D": PINKD, ".": 0}
TPL = {
    ("star", 7): ["...G...", "..GGG..", "GGGGGGG", ".GGGGG.", ".GG.GG.", ".G...G.", "..BBB..", "..BBB.."],
    ("star", 9): ["....G....", "...GGG...", "...GGG...", "GGGGGGGGG", ".GGGWGGG.", "..GGGGG..", "..GG.GG..", ".GG...GG.", "...BBB...", "...BBB..."],
    ("sakura", 7): [".......", ".PP.PP.", "PPPDPPP", ".PDGDP.", "PPPDPPP", ".PP.PP.", "......."],
    ("sakura", 9): ["...PDP...", "..PPPPP..", "PP.PPP.PP", "DPPPGPPPD", "PPPGGGPPP", ".PPPGPPP.", "..PP.PP..", ".PPP.PPP.", ".DP...PD."],
}
def tpl(key, W, H):
    rows = TPL[key]; s = Spr(W, H); y0 = (H - len(rows)) // 2 if key[0] == "sakura" else H - len(rows)
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if TPL_LAB[ch]: s.m[y0 + j, i] = TPL_LAB[ch]
    return s
def gen_star(W, H, L=False):
    if ("star", W) in TPL and H == W + 1: return tpl(("star", W), W, H).m, ((W - 1) / 2, H - 1.5)
    s = Spr(W, H); c = (W - 1) / 2; cy = (H - 2) / 2; R = W / 2 - .2; r = R * 0.45
    pts = [(c + (R if i % 2 == 0 else r) * math.sin(math.radians(36 * i)), cy + .3 - (R if i % 2 == 0 else r) * math.cos(math.radians(36 * i))) for i in range(10)]
    s.poly(pts, GOLD)
    if W >= 11: s.px(c, cy, WHITE)                      # 星心反光
    s.rect(int(c) - max(1, W // 5), H - 2, int(c) + max(1, W // 5), H - 1, BLUE)   # 髮夾金屬片
    return s.m, (c, H - 1.5)
def gen_sakura(W, H, L=False):
    if ("sakura", W) in TPL and H == W: return tpl(("sakura", W), W, H).m, ((W - 1) / 2, (H - 1) / 2)
    s = Spr(W, H); c = (W - 1) / 2; cy = (H - 1) / 2; R = W / 2 - .3; pr = R * 0.46
    for i in range(5):                                  # 5 塊花瓣
        a = math.radians(72 * i - 90 + 18); s.ell(c + math.cos(a) * R * 0.52, cy + math.sin(a) * R * 0.52, pr, pr, PINK)
    s.ell(c, cy, max(.7, R * 0.22), max(.7, R * 0.22), GOLD)
    if W >= 11:                                         # 花瓣尖小缺口（櫻花）＋花蕊
        for i in range(5):
            a = math.radians(72 * i - 90 + 18); s.px(c + math.cos(a) * (R - .3), cy + math.sin(a) * (R - .3), PINKD)
    return s.m, (c, cy)
SIDE = {   # k：闊＝k×頭闊；rot：額外斜角；gen
    "starclip": {"gen": gen_star, "k": 0.42, "hr": 1.0, "rot": -14, "minW": 7},
    "sakura": {"gen": gen_sakura, "k": 0.46, "hr": 1.0, "rot": -10, "minW": 7},
}
def make_side_draw(item):
    P = SIDE[item]
    def draw(body, an, f, ref, form, prev=None):
        S = body.shape[0]; cfg = FIT[item][form]; can = np.zeros((S + 2 * PAD, S + 2 * PAD, 4), np.uint8)
        ws = min(max(f["ws"], 0.85), 1.15)
        W = odd(ref["hw"] * P["k"] * cfg["sc"] * ws, P["minW"]); H = W if item == "sakura" else W + 1
        m, piv = P["gen"](W, H, L=S >= 64)
        if item == "sakura" and W >= 11:               # M／L：加片葉；L：再加個花蕾
            m2 = np.zeros((H + 3, W + 4), m.dtype); m2[:H, 3:3 + W] = m
            sp = Spr(W + 4, H + 3); sp.m = m2
            sp.ell(1.6, H - 0.2, 1.6, 1.0, LEAF)
            if S >= 64: sp.ell(W + 2.2, H + 0.8, 1.3, 1.3, PINK)
            m, piv = sp.m, (piv[0] + 3, piv[1])
        bk = is_back(an); sg = -1 if bk else 1          # ACC5：背面＝左右鏡像，夾去返畫面右邊（head_r 側）
        if bk: m, piv = flip_lab(m, piv)
        m, piv = rotate_labels(m, piv, f["ang"] + P["rot"] * sg)
        spr = render(m); px_, py_ = piv[0] + 1, piv[1] + 1
        if bk: hx, hy = an["head_r"]; cx, cy = hx - cfg["dx"], hy + 1 + cfg["dy"]
        else:
            a0 = anchors(form)["idle"][0]; ed0 = abs(a0["eyeR"][0] - a0["eyeL"][0]) if "eyeL" in a0 else None
            hx, hy = head_l(an, f, ed0); cx, cy = hx + cfg["dx"], hy + 1 + cfg["dy"]
        x, y = int(round(cx - px_)), int(round(cy - py_))
        fp = face_px(an, S)
        for _ in range(6):     # 撞五官 → 向左上移（背面向右上）
            tmp = np.zeros_like(can); place(tmp, spr, x + PAD, y + PAD)
            if not any(tmp[py + PAD, px + PAD, 3] for px, py in fp if 0 <= px + PAD < tmp.shape[1] and 0 <= py + PAD < tmp.shape[0]): break
            x -= sg; y -= 1
        place(can, spr, x + PAD, y + PAD)
        info = {"pos": [round(cx, 1), round(cy, 1)], "W": W, "H": H, "ang": round(f["ang"] + P["rot"] * sg, 1)}
        if bk: info["mirrored"] = True
        return can, info
    return draw

# ---- face（ACC3）：圓框眼鏡，圈住 eyeL／eyeR，跟眼距同傾角；鏡片透明
EYE_REF = {}
def eye_blob(body, an, k):
    """eyeL／eyeR：由 anchor 附近深色像素做 8-連通 flood（±3 框內）→ 眼 blob 像素"""
    d = (body[..., 3] > 0) & (body[..., :3].astype(int).sum(-1) < 200); H, W = d.shape; x0, y0 = an[k]
    seeds = [(x0 + i, y0 + j) for r in range(0, 3) for i in range(-r, r + 1) for j in range(-r, r + 1) if 0 <= x0 + i < W and 0 <= y0 + j < H and d[y0 + j, x0 + i]]
    if not seeds: return []
    mx, my = an.get("mouth", (-99, -99))
    def near_m(x, y): return max(abs(x - mx), abs(y - my)) <= 2 and max(abs(x - x0), abs(y - y0)) > 1   # 唔好連埋個口
    st = [seeds[0]]; seen = {seeds[0]}
    while st:
        x, y = st.pop()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1), (x + 1, y + 1), (x - 1, y - 1), (x + 1, y - 1), (x - 1, y + 1)):
            if (nx, ny) not in seen and 0 <= nx < W and 0 <= ny < H and d[ny, nx] and abs(nx - x0) <= 3 and abs(ny - y0) <= 3 and not near_m(nx, ny):
                seen.add((nx, ny)); st.append((nx, ny))
    return list(seen)
def _eye_stats(bodies, alist, base_off=None):
    """每隻眼：clip 內眼 blob 中心相對 anchor 嘅平均偏移（取 0.5px）＋以呢個中心計嘅最大半寬 bx／半高 by"""
    offs = {"eyeL": [], "eyeR": []}; blobs = []
    for b, an in zip(bodies, alist):
        if not an.get("faceVisible", True) or "eyeL" not in an or "eyeR" not in an: continue
        for k in offs:
            px = eye_blob(b, an, k)
            if px:
                px = np.array(px, float); c = (px.min(0) + px.max(0)) / 2
                offs[k].append(c - np.array(an[k], float)); blobs.append((k, an[k], px))
    off = []
    for k in ("eyeL", "eyeR"):
        o = np.mean(offs[k], 0) if offs[k] else np.zeros(2)
        off.append(tuple(float(np.round(v * 2) / 2) for v in o)) if base_off is None else off.append(base_off[len(off)])
    bx = by = 0.0
    for k, a_, px in blobs:
        c = np.array(a_, float) + np.array(off[0 if k == "eyeL" else 1])
        bx = max(bx, float(np.abs(px[:, 0] - c[0]).max())); by = max(by, float(np.abs(px[:, 1] - c[1]).max()))
    return off, bx, by
def eye_ref(form):
    """idle 嘅眼 blob（每形態最細鏡片尺寸，全部 clip 唔會細過佢）"""
    if form in EYE_REF: return EYE_REF[form]
    A = anchors(form)["idle"]; B_ = [load(frame_path(form, "idle", k)) for k in range(1, len(A) + 1)]
    off, bx, by = _eye_stats(B_[:1], A[:1]); EYE_REF[form] = {"off": off, "bx": bx, "by": by}; return EYE_REF[form]
# 眼鏡逐 clip 試：(收窄, 壓扁, 上移, 向外, 逐幀跟眼)。先試標準大小，唔得先慢慢收；S 級細臉可以貼眼框
GL_RETRY = tuple((a, b, c, d, pf) for pf in (0, 1) for a, b, c, d in (
    (0, 0, 0, 0), (0, 0, .5, .3), (-.5, -.5, .5, .3), (0, -1, .5, .3), (-.5, -1, .5, .5), (-.5, -1.5, 1, .5), (-1, -1, .5, .3),
    (-1, -1, 0, 0), (-1, -1, .5, 0)))
def glasses_pre(fs, bodies, alist, form, clip=None):
    """成個 clip 用同一副眼鏡：中心＝anchor＋clip 平均偏移；鏡片半軸 ≥ idle"""
    er = eye_ref(form); off, bx, by = _eye_stats(bodies, alist)
    g = {"off": off, "bx": max(bx, er["bx"]), "by": max(by, er["by"])}
    # 逐幀跟眼模式用：以每幀自己中心計嘅最大半寬／半高
    pbx = pby = 0.0
    for b, an in zip(bodies, alist):
        if not an.get("faceVisible", True) or "eyeL" not in an or "eyeR" not in an: continue
        for k in ("eyeL", "eyeR"):
            px = eye_blob(b, an, k)
            if px: px = np.array(px, float); h = (px.max(0) - px.min(0)) / 2; pbx = max(pbx, float(h[0])); pby = max(pby, float(h[1]))
    g["pbx"] = max(pbx, er["bx"]); g["pby"] = max(pby, er["by"])
    for f in fs: f["gl"] = g
FH_MIN = 0.50
def draw_glasses(body, an, f, ref, form, prev=None):
    S = body.shape[0]; cfg = FIT["glasses"][form]; can = np.zeros((S + 2 * PAD, S + 2 * PAD, 4), np.uint8)
    if not an.get("faceVisible", True): return None, {"why": "faceVisible=false（背面／遮面）"}
    if "eyeL" not in an or "eyeR" not in an: return None, {"why": "冇眼錨點"}
    th = 2 if S >= 64 else 1; g = f.get("gl") or dict(eye_ref(form))
    drx, dry, lift, out, pf = (tuple(f.get("adj", ())) + (0, 0, 0, 0, 0))[:5]   # retry：收窄／壓扁／上移／向外／逐幀跟眼（成個 clip 一齊）
    offs = g["off"]
    if pf:                                                  # 動作 clip：每幀跟返眼 blob 中心（取 0.5px），鏡片尺寸不變
        offs = []
        for k, o in zip(("eyeL", "eyeR"), g["off"]):
            px = eye_blob(body, an, k)
            if px: px = np.array(px, float); c = (px.min(0) + px.max(0)) / 2; offs.append(tuple(c - np.array(an[k], float)))
            else: offs.append(o)
    cs = [np.array(an[k], float) + np.array(o) for k, o in zip(("eyeL", "eyeR"), offs)]
    dvec = cs[1] - cs[0]; dist = float(np.hypot(*dvec))
    e = dvec / max(dist, 1e-6); nrm = np.array([e[1], -e[0]])   # nrm 向上
    cs = [cs[0] + nrm * lift - e * out, cs[1] + nrm * lift + e * out]
    gbx, gby = (g["pbx"], g["pby"]) if pf else (g["bx"], g["by"])
    ax = gbx + 1.5 + cfg["r"] + drx; ay = gby + 1.5 + cfg["r"] + dry   # 圓角鏡片：眼外留約 1px
    if cfg.get("forehead"):                                 # 推上額頭：鏡片細圈，成副升到眼 blob 上面（框底離眼頂 ≥1px）
        # 細圈（ay 1.5）擱喺頭頂：框底離眼 blob 頂 1px，框頂可以略出頭頂剪影（似推上頭嘅眼鏡），但大部分要貼住頭
        ey_ = [min(p_[1] for p_ in eye_blob(body, an, k)) if eye_blob(body, an, k) else an[k][1] - 1 for k in ("eyeL", "eyeR")]
        ay = 1.5 + dry; ax = min(2.5 + drx, (dist + 2 * out) / 2 - th * 0.5)
        if ay < 0.9: return None, {"why": "額頭位唔夠（眼鏡會浮出個頭）"}
        # 兩片一齊沿 nrm 升（保持同眼線平行），升到兩隻眼都過：鏡心 y ≤ 眼頂 − 2.5 − ay
        L_ = max((c[1] - (ey - 2.5 - ay)) / max(1e-6, -nrm[1]) for c, ey in zip(cs, ey_))
        ncs = [c + nrm * L_ for c in cs]
        cs = ncs; gbx = gby = -9                             # 下面「眼太窄」檢查唔適用
    lim = (dist + 2 * out) / 2 - th * 0.5                 # 兩片外框最多共用 1px（窄臉＝連框）
    if ax > lim: ax = lim
    if ax < gbx + 0.45 + out or ay < gby + 0.45 + lift: return None, {"why": f"眼距 {dist:.1f}px 太窄（側面），戴唔落"}
    r = (ax + ay) / 2
    H, W = S + 2 * PAD, S + 2 * PAD; yy, xx = np.mgrid[0:H, 0:W]; xx = xx - PAD; yy = yy - PAD
    ring = np.zeros((H, W), bool); inner = np.zeros((H, W), bool)
    for c in cs:
        uu = (xx - c[0]) * e[0] + (yy - c[1]) * e[1]; vv = (xx - c[0]) * nrm[0] + (yy - c[1]) * nrm[1]
        n0 = (uu / ax) ** 2 + (vv / ay) ** 2; n1 = (uu / (ax + th)) ** 2 + (vv / (ay + th)) ** 2
        rr = (n0 >= 1) & (n1 < 1)
        inw = uu * (1 if c is cs[0] else -1)                # >0＝向鼻樑嗰邊
        if cfg.get("forehead"): pass                         # 額頭版：全圓框（離晒五官）
        elif cfg.get("half"): rr &= vv >= -0.25 * ay        # 細臉：半框（只畫上半圈）（ACC5 起冇形態用）
        elif cfg.get("notch", True): rr &= ~((vv < -0.25 * ay) & (inw > 0.2 * ax))   # 近口嗰角開口（¾ 圓框，全部形態一致）
        ring |= rr
        if th == 2: inner |= (n0 >= 1) & ((uu / (ax + 1)) ** 2 + (vv / (ay + 1)) ** 2 < 1)
    ex_ = ax
    # 鼻橋：兩圈內側、略高過眼中線
    a0 = cs[0] + e * (ex_ + th * .5) + nrm * ay * 0.35; a1 = cs[1] - e * (ex_ + th * .5) + nrm * ay * 0.35
    n_ = int(max(2, np.hypot(*(a1 - a0)) * 2)) + 1
    for t in np.linspace(0, 1, n_):
        q = a0 + (a1 - a0) * t; ring[int(round(q[1])) + PAD, int(round(q[0])) + PAD] = True
    # 鏡腳：外側向耳仔方向 2–3px，只畫喺身體上面
    arm = 3 if S >= 64 else 2; a = body[..., 3] > 0
    for c, sg in ((cs[0], -1), (cs[1], 1)):
        st = c + e * sg * (ex_ + th - .5) + nrm * ay * 0.35
        for t in range(1, arm + 1):
            q = st + e * sg * t + nrm * t * 0.3; qx, qy = int(round(q[0])), int(round(q[1]))
            if 0 <= qx < S and 0 <= qy < S and a[qy, qx]: ring[qy + PAD, qx + PAD] = True
    if cfg.get("forehead"):                                 # 額頭版：框要大部分貼喺頭上（唔好浮出剪影）
        bb = np.zeros((H, W), bool); bb[PAD:PAD + S, PAD:PAD + S] = a
        fh = float((ring & bb).sum() / max(1, ring.sum()))
        if fh < FH_MIN: return None, {"why": "額頭位唔夠（眼鏡會浮出個頭）"}
    can[ring, :3] = rgb("orange_dd"); can[ring, 3] = 255
    if th == 2: can[inner & ring, :3] = rgb("orange_d")     # L：鏡框加粗，內圈淺一級
    if r >= 3.5:                                             # 鏡片反光一點（唔掂眼）
        for c in cs:
            q_ = c + (-0.62 * (ax - 1), -0.62 * (ay - 1)); gx, gy = int(round(q_[0])), int(round(q_[1]))
            if 0 <= gx < S and 0 <= gy < S and a[gy, gx] and not can[gy + PAD, gx + PAD, 3]:
                can[gy + PAD, gx + PAD, :3] = rgb("white"); can[gy + PAD, gx + PAD, 3] = 255
    # 唔可以遮眼本身（深色 blob）同五官保護區
    d = a & (body[..., :3].astype(int).sum(-1) < 200)
    for k in ("eyeL", "eyeR"):
        if any(can[y + PAD, x + PAD, 3] for x, y in eye_blob(body, an, k)): return None, {"why": "鏡框會壓到眼"}
    info = {"c": [[round(float(c[0]), 2), round(float(c[1]), 2)] for c in cs], "r": round(float(r), 2), "ax": round(float(ax), 2), "ay": round(float(ay), 2), "th": th}
    if cfg.get("forehead"): info["forehead"] = True; info["onHead"] = round(fh, 2)
    return can, info

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

# ================================================================ ACC4：葉仔領（neck）／燈泡小鈴・燈泡光環（bulb）／睡帽（head，長尾）
# 燈泡玻璃半徑（idle 目測，逐形態手調）；dot／evo_sprout 冇燈泡 → fallback 用頭頂
BR = {"sprout": 2, "radiant": 4.5, "soft": 2.5, "lumi": 2, "evo_hop": 2.5, "evo_guard_lumi": 1.5, "evo_guard_radiant": 4,
      "evo_guard_soft": 2.5, "evo_guard_dust": 2.5, "evo_still_lumi": 1.5, "evo_still_radiant": 4.5, "evo_still_soft": 3,
      "evo_still_dust": 2.5, "evo_guard_tide": 2.5, "evo_still_tide": 3, "evo_guard_shroom": 2, "evo_still_shroom": 2.5,
      "evo_guard_crystal": 2, "evo_still_crystal": 2.5, "evo_guard_moon": 2, "evo_still_moon": 2.5, "evo_guard_ember": 2, "evo_still_ember": 2.5}
TOPBULB = {}
def top_bulb(form):
    """燈泡係咪喺頭頂（同 fit 一樣：眼中點→燈泡同眼線垂直方向差 ≤40°）；lumi 系（觸角）／dust（尾燈）／moon（帽尖月）唔係"""
    if form not in TOPBULB:
        a = anchors(form)["idle"][0]; ok = "bulb" in a and AXIS.get(form) != "eyes"
        if ok:
            em = ((a["eyeL"][0] + a["eyeR"][0]) / 2, (a["eyeL"][1] + a["eyeR"][1]) / 2); ex, ey = a["eyeR"][0] - a["eyeL"][0], a["eyeR"][1] - a["eyeL"][1]
            vb = (a["bulb"][0] - em[0], a["bulb"][1] - em[1]); d = math.degrees(math.atan2(vb[0], -vb[1]) - math.atan2(ey, ex))
            ok = abs((d + 180) % 360 - 180) <= 40
        TOPBULB[form] = ok and form not in ("evo_still_moon", "evo_guard_moon")   # 月眠：燈＝帽尖新月，唔當頭頂燈泡
    return TOPBULB[form]
def _loop(form, clip):
    return bool(form_anims(form).get(clip, {}).get("loop", False)) if clip else False
def _swing(pts, loop, k_x, k_y, decay, lim, maxd=14.0):
    """擺動（慣性）：身體點向右郁 → 掛件向左拖（＋＝順時針）；loop clip 行兩轉，攞第二轉（頭尾接得順）；每幀變化夾 ±maxd°"""
    n = len(pts); s = 0.0; out = [0.0] * n
    for p_ in range(2 if loop and n > 1 else 1):
        for k in range(n):
            if k: vx, vy = pts[k][0] - pts[k - 1][0], pts[k][1] - pts[k - 1][1]
            elif loop and n > 1: vx, vy = pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1]
            else: vx = vy = 0.0
            t_ = max(-lim, min(lim, decay * s + k_x * vx + k_y * vy)); s = s + max(-maxd, min(maxd, t_ - s)); out[k] = round(s, 2)   # 每幀最多轉 maxd°（唔會一格飛
    return out

# ---- 葉仔領（neck）：同頸巾一樣搵頸位（mouth＋gap／idle 頸距），跟剪影收邊；一圈葉仔向下垂＋前面一朵細花
def _neck_geom(body, an, f, ref, cfg):
    S = body.shape[0]; a = body[..., 3] > 0
    if "mouth" in an and an.get("faceVisible", True): ny = an["mouth"][1] + neck_gap(ref)
    else: ny = int(round(f["em"][1] + ref["neck_off"] * f["hs"]))
    ny += cfg["dy"]; cx = f["em"][0]; t = math.tan(math.radians(f["ang"])) if f["ang"] else 0.0
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
    if rr is None: return None
    if "neck_half" in ref:
        lim = ref["neck_half"] * min(max(f["ws"], .8), 1.3) + 2
        rr = (max(rr[0], int(math.floor(cx - lim))), min(rr[1], int(math.ceil(cx + lim))))
    return ny, cx, t, rr, run_at
LEAFA = mat("leafa", "leaf_d", "leaf", "sick1"); LEAFB = mat("leafb", "leaf_d", "leaf", "leaf")
def draw_leafcollar(body, an, f, ref, form, prev=None):
    S = body.shape[0]; cfg = FIT["leafcollar"][form]
    g = _neck_geom(body, an, f, ref, cfg)
    if g is None: return None, {"why": "頸位冇身體"}
    ny, cx, t, (xl, xr), run_at = g
    lw = 3 if S <= 32 else (4 if S <= 48 else 5); lh = 3 if S <= 32 else (4 if S <= 48 else 5)
    lab = np.zeros((S + 2 * PAD, S + 2 * PAD), np.int16)
    def put(x, y, c, clip=True):
        if clip:
            rr2 = run_at(y) if 0 <= y < S else None
            if rr2 is None or not (max(rr2[0], xl) - 1 <= x <= min(rr2[1], xr) + 1): return
        lab[y + PAD, x + PAD] = c
    # 葉仔：一片片尖頭向下、左右交替兩隻綠（相鄰有分界），頂行貼住頸位；兩邊最尾一片向外斜
    n = max(3, int(round((xr - xl + 3) / lw))); x0 = (xl + xr + 1) / 2 - n * lw / 2
    shape = {3: ["xxx", "xxx", ".x."], 4: ["xxxx", "xxxx", ".xx.", ".x.."], 5: ["xxxxx", "xxxxx", ".xxxx", "..xx.", "..x.."]}[lw]
    for i in range(n):
        lx = int(round(x0 + i * lw)); yb = ny + int(round(-t * (lx + lw / 2 - cx))); c = LEAFA if i % 2 else LEAFB
        sh = shape if i % 2 == 0 else [r[::-1] for r in shape]
        for yy, row in enumerate(sh[:lh]):
            for xx, ch in enumerate(row):
                if ch == "x": put(lx + xx, yb + yy, c, clip=yy == 0)
    fx = int(round(cx + (xr - xl) * 0.26)); fy = ny + int(round(-t * (fx - cx))) + (1 if S <= 32 else 2)   # 細花（前右）
    pet = [(-1, 0), (1, 0), (0, -1), (0, 1)] + ([(-1, -1), (1, -1), (-1, 1), (1, 1)] if S > 32 else [])
    for dx, dy in pet: put(fx + dx, fy + dy, PINK, clip=False)
    if S >= 64:
        for dx, dy in ((0, -2), (-2, 0), (2, 0), (0, 2)): put(fx + dx, fy + dy, PINK, clip=False)
    put(fx, fy, GOLD, clip=False)
    img = render(lab)[1:-1, 1:-1]
    for px, py in face_px(an, S): img[py + PAD, px + PAD] = 0
    return img, {"ny": ny, "run": [xl, xr], "lw": lw, "flower": [fx, fy], "ang": round(f["ang"], 1)}

# ---- 燈泡小鈴（bulb）：紅繩綁喺燈泡玻璃下面（右下），金鈴向下垂，跟身體郁有慣性擺
BELL_TPL = {   # 鈴（suzu）：圓身＋中間一條坑＋下面開口；頂一粒紅繩結
    5: ["..R..", ".GGG.", "GWGGG", "DDDDD", "GGKGG", ".GKG."],
    7: ["..R.R..", "...R...", "..GGG..", ".GWGGG.", "GWGGGGG", "DDDDDDD", "GGGKGGG", ".GGKGG.", "..GGG.."],
    9: ["..RR.RR..", "...RRR...", "...GGG...", ".GGWGGGG.", ".GWGGGGG.", "GWGGGGGGG", "DDDDDDDDD", "GGGGKGGGG", ".GGGKGGG.", "..GKKKG..", "...GGG..."],
}
BELL_LAB = {"G": GOLD, "W": WHITE, "R": RED, "K": INK, "D": GOLDD, ".": 0}
def bell_pre(fs, bodies, alist, form, clip=None):
    pts = [tuple(a["bulb"]) if "bulb" in a else f["top"] for a, f in zip(alist, fs)]
    for f, s in zip(fs, _swing(pts, _loop(form, clip), 7.0, 0.0, 0.5, 25.0)): f["swing"] = s
BELL_LOW = {}
def bell_low(form):
    """ACC5：燈泡錨點太低（鈴底離地 < max(6, 25%S)，例：guard_dust／still_dust 側邊低位燈）→ 成個形態改用頭頂 fallback（用 idle_01 判斷，全 clip 一致）"""
    if form in BELL_LOW: return BELL_LOW[form]
    an = anchors(form)["idle"][0]; low = False
    if "bulb" in an:
        b = load(frame_path(form, "idle", 1)); S = b.shape[0]; n = 5 if S <= 32 else (7 if S <= 48 else 9)
        g = int(np.nonzero(b[..., 3].any(1))[0].max()); hy = an["bulb"][1] + int(math.ceil(BR[form])) + 1 + FIT["bell"][form]["dy"]
        low = (g - (hy + n + 1)) < max(6, S * 0.25)
    BELL_LOW[form] = low; return low
def draw_bell(body, an, f, ref, form, prev=None):
    S = body.shape[0]; cfg = FIT["bell"][form]; can = np.zeros((S + 2 * PAD, S + 2 * PAD, 4), np.uint8)
    n = 5 if S <= 32 else (7 if S <= 48 else 9); rows = BELL_TPL[n]
    m = np.array([[BELL_LAB[c] for c in r] for r in rows], np.int16); piv = ((n - 1) / 2, 0)
    sw = f.get("swing", 0.0); m, piv = rotate_labels(m, piv, sw)
    spr = render(m); px_, py_ = piv[0] + 1, piv[1] + 1
    if "bulb" in an and not bell_low(form):
        bx, by = an["bulb"]; br = BR[form]; base = "bulb"
        hx = bx + int(round(br * 0.6)) + cfg["dx"]; hy = by + int(math.ceil(br)) + 1 + cfg["dy"]
    else:   # fallback：冇燈泡（dot／evo_sprout）或者燈泡太低（dust）→ 綁喺頭頂芽／毛嘅右邊
        base = "top" if "bulb" not in an else "top_low"; hx = f["top"][0] + f["pp"][0] * ref["hw"] * 0.22 + cfg["dx"]; hy = f["top"][1] + f["pp"][1] * ref["hw"] * 0.22 + cfg["dy"]
    x, y = int(round(hx - px_)), int(round(hy - py_)); fp = face_px(an, S)
    for _ in range(6):
        tmp = np.zeros_like(can); place(tmp, spr, x + PAD, y + PAD)
        if not any(tmp[py + PAD, px + PAD, 3] for px, py in fp if 0 <= px + PAD < tmp.shape[1] and 0 <= py + PAD < tmp.shape[0]): break
        x += 1; y -= 1
    place(can, spr, x + PAD, y + PAD)
    return can, {"pos": [round(float(hx), 1), round(float(hy), 1)], "W": n, "swing": sw, "base": base}

# ---- 燈泡光環（bulb）：金色扁圓環浮喺燈泡上面（頭頂燈泡形態）／頭頂上面（其餘），跟頭傾角
HALOH = mat("haloh", "glow", "glow", "glow")   # 暫用 label：環中間嘅洞（render 後清走）
def gen_halo(rx, ry, L=False):
    W = int(math.ceil(rx)) * 2 + 1; H = int(math.ceil(ry)) * 2 + 1; cx, cy = (W - 1) / 2, (H - 1) / 2
    yy, xx = np.mgrid[0:H, 0:W]; n0 = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2
    n1 = ((xx - cx) / max(rx - 1.0, .5)) ** 2 + ((yy - cy) / max(ry - 1.0, .35)) ** 2
    ring = (n0 <= 1.0) & (n1 > 1.0); m = np.zeros((H, W), np.int16); m[(n1 <= 1.0)] = HALOH
    m[ring & (yy < cy)] = GOLDD; m[ring & (yy >= cy)] = GOLD     # 後半圈暗啲，前半圈亮
    if L:
        ys, xs = np.nonzero(ring & (yy > cy)); i = int(np.argmin(np.abs(xs - (cx - rx * 0.45)) + np.abs(ys - (H - 1))))
        m[ys[i], xs[i]] = WHITE
    return m, (cx, cy)
def draw_halo(body, an, f, ref, form, prev=None):
    S = body.shape[0]; cfg = FIT["halo"][form]; can = np.zeros((S + 2 * PAD, S + 2 * PAD, 4), np.uint8)
    a = body[..., 3] > 0
    if top_bulb(form) and "bulb" in an:
        br = BR[form]; rx = (br + 2.0) * cfg["sc"]; ry = max(1.6, rx * 0.4); base = "bulb"
        bx, by = an["bulb"]; gap = br + 1.5 + ry + cfg["dy"]
        cx, cy = bx + f["u"][0] * gap, by + f["u"][1] * gap
    else:
        rx = max(3.5, min(ref["hw"] * 0.3, S * 0.13)) * cfg["sc"]; ry = max(1.6, rx * 0.4); base = "top"
        if "eyeL" in an: ex, ey = an["eyeR"][0] - an["eyeL"][0], an["eyeR"][1] - an["eyeL"][1]; L_ = math.hypot(ex, ey) or 1; ue = (ey / L_, -ex / L_)
        else: ue = (0.0, -1.0)
        cx = f["em"][0] + ue[0] * ref["hh"] + cfg.get("dx", 0)          # 眼中點沿眼線垂直方向上去（moon 唔會跌落月牙）
        cols = a[:, max(0, int(cx - rx - 1)):min(S, int(cx + rx + 2))]
        rows_ = np.nonzero(cols.any(1))[0]
        yt = rows_.min() if len(rows_) else f["top"][1]
        cy = yt - 2 - ry + cfg["dy"]
    ha = max(-12.0, min(12.0, f["ang"])) if base == "bulb" else 0.0      # 光環：跟燈泡傾少少（夾 ±12°）；頭頂版保持水平（細環一轉就似塊葉）
    m, piv = gen_halo(rx, ry, L=S >= 64); m, piv = rotate_labels(m, piv, ha)
    spr = render(m); spr[np.pad(m, 1) == HALOH] = 0       # 環中間嘅洞：唔描邊，透明
    px_, py_ = piv[0] + 1, piv[1] + 1
    x, y = int(round(cx - px_)), int(round(cy - py_))
    if y + PAD < 0: cy += -PAD - y; y = -PAD          # 跳得高嘅幀：光環貼住 padding 頂（落低少少，唔會俾切）
    if x + PAD < 0 or x + PAD + spr.shape[1] > can.shape[1]: return None, {"why": "光環出咗 padding"}
    place(can, spr, x + PAD, y + PAD)
    return can, {"c": [round(float(cx), 1), round(float(cy), 1)], "rx": round(float(rx), 2), "ry": round(float(ry), 2), "base": base, "ang": round(ha, 1)}

# ---- 睡帽（head）：紫白間條軟帽，帽尖向左瞓，長尾垂落左邊＋白色 pompom；尾有慣性擺動（loop clip 頭尾接順）
NIGHT = mat("night", "zzz", "zzz", "zzz")
def gen_nightcap(W, H, L=False):
    """帽身（唔連尾）：底闊 W、高 H；回傳 label map、piv（帽底中心）、tip（帽尖，local 座標）"""
    s = Spr(W, H); c = (W - 1) / 2; cuff = 3 if W >= 25 else 2
    tipx = c - W * 0.34; tipy = 0.4
    s.poly([(-.2, H - cuff + .6), (W + .2, H - cuff + .6), (W * 0.86, H * 0.42), (c + W * 0.06, H * 0.12), (tipx, tipy), (tipx - .8, tipy + 1.6), (W * 0.12, H * 0.45)], NIGHT)
    sw = 2 if W < 25 else 3                                             # 斜間條（白）
    for y in range(H - cuff):
        for x in range(W):
            if s.m[y, x] == NIGHT and ((x + y * 0.7) // sw) % 2 == 0 and y > 0: s.m[y, x] = WHITE
    s.rect(0, H - cuff, W - 1, H - 1, WHITE)
    for x in range(1, W - 1, 2): s.m[H - 1, x] = CREAMD
    if L or W >= 17:                                                    # 細星（金）
        sx, sy = int(round(c + W * 0.22)), int(round(H * 0.55))
        if 0 <= sy < H - cuff: s.px(sx, sy, GOLD); s.px(sx - 1, sy, GOLD); s.px(sx + 1, sy, GOLD); s.px(sx, sy - 1, GOLD); s.px(sx, sy + 1, GOLD)
    return s.m, ((W - 1) / 2, H - 1), (tipx, tipy + .6)
def gen_pincap(W, H, L=False):
    """ACC5 月眠別針版迷你睡帽：窄底高錐、帽尖向右彎；橫間（唔用斜間，細尺寸斜間似羽毛）；回傳同 gen_nightcap"""
    s = Spr(W, H); c = (W - 1) / 2; cuff = 2
    tipx = c + W * 0.30; tipy = 0.3
    s.poly([(-.2, H - cuff + .6), (W + .2, H - cuff + .6), (W * 0.80, H * 0.45), (tipx + .6, tipy + 1.2), (tipx, tipy), (c - W * 0.05, H * 0.18), (W * 0.10, H * 0.50)], NIGHT)
    by_ = int(round(H * 0.52))                                          # 中間一條白間
    for x in range(W):
        if s.m[by_, x] == NIGHT: s.m[by_, x] = WHITE
    s.rect(0, H - cuff, W - 1, H - 1, WHITE)
    for x in range(1, W - 1, 2): s.m[H - 1, x] = CREAMD
    if W >= 11:
        sx, sy = int(round(c - W * 0.08)), int(round(H * 0.32))
        if s.m[sy, sx] == NIGHT: s.px(sx, sy, GOLD)
    return s.m, ((W - 1) / 2, H - 1), (tipx, tipy + .6)
def cap_pre(fs, bodies, alist, form, clip=None):
    pts = [f["top"] for f in fs]
    for f, s in zip(fs, _swing(pts, _loop(form, clip), 6.0, 4.0, 0.55, 30.0)): f["swing"] = s
def _rot_pt(p, piv, ang):
    a = math.radians(ang); ca, sa = math.cos(a), math.sin(a); dx, dy = p[0] - piv[0], p[1] - piv[1]
    return (ca * dx - sa * dy, sa * dx + ca * dy)
def draw_nightcap(body, an, f, ref, form, prev=None):
    S = body.shape[0]; cfg = FIT["nightcap"][form]; can = np.zeros((S + 2 * PAD, S + 2 * PAD, 4), np.uint8)
    pin = cfg.get("variant") == "hatpin"; P = HEAD["nightcap"]
    if pin:
        if cfg.get("pin") == "r": cx = an["head_r"][0] - 3; cy = an["head_r"][1] - 5
        else: cx = 2 * f["em"][0] - an["head_r"][0]; cy = an["head_r"][1] - 1
        W = odd(ref["hw"] * P["pin"] * cfg["sc"] * min(max(f["ws"], .85), 1.15), 7); H = max(4, int(round(W * P["hr"])))
        ang = P["pin_ang"] + f["ang"]; bx, by = cx + cfg["dx"], cy + cfg["dy"]
    else:
        ws = min(max(f["ws"], 0.8), 1.3); hs = min(max(f["hs"], 0.8), 1.25)
        W = odd(ref["hw"] * P["k"] * cfg["sc"] * ws, P["minW"]); H = max(5, int(round(ref["hw"] * P["k"] * cfg["sc"] * P["hr"] * (0.5 + 0.5 * hs))))
        ang = f["ang"]; sink = max(1, int(round(ref["hw"] * P["sink"])))
        bx = f["top"][0] - f["u"][0] * sink + cfg["dx"]; by = f["top"][1] - f["u"][1] * sink + cfg["dy"]
    mir = pin and cfg.get("pin") == "r"                     # ACC5：月眠右邊別針版＝迷你直身睡帽（帽尖向外、尾向右下垂＋白波波），唔再似條羽毛
    if mir:
        W = odd(W * 0.75, 7); H = max(6, int(round(W * 1.05))); ang = 6 + f["ang"]
        m0, piv0, tip0 = gen_pincap(W, H, L=S >= 64)
    else: m0, piv0, tip0 = gen_nightcap(W, H, L=S >= 64)
    m, piv = rotate_labels(m0, piv0, ang)
    tdx, tdy = _rot_pt(tip0, piv0, ang)
    sw = f.get("swing", 0.0); tl = max(4.0, W * (0.55 if pin else 0.62)) * cfg.get("tail", 1.0)
    th0 = max(1.5, W * 0.11); pr = max(1.1, W * 0.085)
    if mir: tl = max(4.0, W * 0.85) * cfg.get("tail", 1.0); th0 = max(1.8, W * 0.2); pr = max(1.4, W * 0.15)
    fp = face_px(an, S); best = None
    tl0 = tl
    for tk, dphi in [(k_, d_) for k_ in (1.0, 0.75, 0.55) for d_ in (0, 15, 30, -15, 45, 60, -30)]:   # 尾撞五官／出 padding → 向外擺、再唔得就縮短條尾
        tl = tl0 * tk
        lab = np.zeros((S + 2 * PAD, S + 2 * PAD), np.int16)
        ox, oy = int(round(bx - piv[0])) + PAD, int(round(by - piv[1])) + PAD
        h_, w_ = m.shape; ys_, xs_ = np.nonzero(m)
        for yy_, xx_ in zip(ys_, xs_):
            Y, X = oy + yy_, ox + xx_
            if 0 <= Y < lab.shape[0] and 0 <= X < lab.shape[1]: lab[Y, X] = m[yy_, xx_]
        tx, ty = bx + tdx + PAD, by + tdy + PAD
        phi0 = 200 + ang + dphi; phi1 = 112 + dphi * 0.5          # 帽尖向左上 → 垂落（畫面角度：90＝向下，180＝向左）
        if mir: phi0 = 330 + ang - dphi; phi1 = 445 - dphi * 0.5    # 迷你帽：帽尖向右 → 經 0° 順時針垂落到 85°（讀得出係軟布）
        x_, y_ = tx, ty; nseg = int(math.ceil(tl * 2)); pts = []; out = False
        for i in range(nseg + 1):
            r_ = i / nseg; phi = math.radians(phi0 + (phi1 - phi0) * (r_ ** 0.7) + sw * r_)
            if i: x_ += math.cos(phi) * 0.5; y_ += math.sin(phi) * 0.5
            pts.append((x_, y_))
            th = th0 * (1 - 0.55 * r_); rr = th / 2
            for yy in range(int(math.floor(y_ - rr)), int(math.ceil(y_ + rr)) + 1):
                for xx in range(int(math.floor(x_ - rr)), int(math.ceil(x_ + rr)) + 1):
                    if (xx - x_) ** 2 + (yy - y_) ** 2 <= rr * rr + .25:
                        if not (1 <= yy < lab.shape[0] - 1 and 1 <= xx < lab.shape[1] - 1): out = True; continue
                        if lab[yy, xx] in (0, NIGHT, WHITE):
                            if mir: lab[yy, xx] = NIGHT if lab[yy, xx] != WHITE else WHITE   # 迷你帽尾：實色（唔間條）
                            else: lab[yy, xx] = WHITE if int(i / (3 if W >= 17 else 2)) % 2 else NIGHT
        ex, ey = pts[-1]
        for yy in range(int(math.floor(ey - pr - 1)), int(math.ceil(ey + pr + 1)) + 1):
            for xx in range(int(math.floor(ex - pr - 1)), int(math.ceil(ex + pr + 1)) + 1):
                if (xx - ex) ** 2 + (yy - ey) ** 2 <= pr * pr + .3:
                    if not (1 <= yy < lab.shape[0] - 1 and 1 <= xx < lab.shape[1] - 1): out = True; continue
                    lab[yy, xx] = WHITE
        img = render(lab)[1:-1, 1:-1]
        lift = 0
        if not pin:
            for _ in range(8):     # 帽身遮五官 → 升
                if not any(img[py + PAD - lift, px + PAD, 3] if 0 <= py + PAD - lift < img.shape[0] else 0 for px, py in fp): break
                lift += 1
            if lift:
                img2 = np.zeros_like(img); img2[:img.shape[0] - lift] = img[lift:]; img = img2
        hit = any(img[py + PAD, px + PAD, 3] for px, py in fp)
        if not hit and not out: best = (img, dphi, (ex - PAD, ey - PAD - lift), lift, tk); break
    if best is None: return None, {"why": "睡帽尾撞五官／出 padding"}
    img, dphi, tend, lift, tk = best
    if not pin: cut_hole(img[PAD:PAD + S, PAD:PAD + S], head_cut(body, f, full=form in CUT_FULL))
    info = {"variant": "hatpin" if pin else "cap", "W": W, "H": H, "ang": round(ang, 1), "swing": sw, "dphi": dphi, "tailK": tk,
            "tailEnd": [round(float(tend[0]), 1), round(float(tend[1]), 1)]}
    if pin: info["pos"] = [round(float(bx), 1), round(float(by), 1)]
    if mir: info["mirrored"] = True
    if not pin: info["piv"] = [round(float(bx), 1), round(float(by - lift), 1)]
    return img, info
HEAD["nightcap"] = {"gen": None, "k": 1.06, "hr": 0.56, "sink": 0.2, "minW": 9, "pin": 0.55, "pin_ang": -16}


ITEMS = {
    "straw": {"name": "草帽", "slot": "head", "anchor": "top", "draw": draw_straw, "batch": "ACC1"},
    "bow": {"name": "蝴蝶結", "slot": "side_r", "anchor": "head_r", "draw": draw_bow, "batch": "ACC1"},
    "scarf": {"name": "頸巾", "slot": "neck", "anchor": "neck", "draw": draw_scarf, "batch": "ACC1"},
    "beanie": {"name": "毛冷帽", "slot": "head", "anchor": "top", "draw": make_head_draw("beanie"), "batch": "ACC2"},
    "acorn": {"name": "橡果帽", "slot": "head", "anchor": "top", "draw": make_head_draw("acorn"), "batch": "ACC2"},
    "crown": {"name": "小皇冠", "slot": "head", "anchor": "top", "draw": make_head_draw("crown"), "batch": "ACC2"},
    "starclip": {"name": "星星髮夾", "slot": "side_l", "anchor": "head_l", "draw": make_side_draw("starclip"), "batch": "ACC3"},
    "sakura": {"name": "櫻花髮飾", "slot": "side_l", "anchor": "head_l", "draw": make_side_draw("sakura"), "batch": "ACC3"},
    "glasses": {"name": "圓框眼鏡", "slot": "face", "anchor": "eyeL/eyeR", "draw": draw_glasses, "batch": "ACC3", "pre": glasses_pre, "retry": GL_RETRY},
    "leafcollar": {"name": "葉仔領", "slot": "neck", "anchor": "neck", "draw": draw_leafcollar, "batch": "ACC4"},
    "bell": {"name": "燈泡小鈴", "slot": "bulb", "anchor": "bulb", "draw": draw_bell, "batch": "ACC4", "pre": bell_pre},
    "halo": {"name": "燈泡光環", "slot": "bulb", "anchor": "bulb", "draw": draw_halo, "batch": "ACC4"},
    "nightcap": {"name": "睡帽", "slot": "head", "anchor": "top", "draw": draw_nightcap, "batch": "ACC4", "pre": cap_pre, "sleepKeep": True},
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

def stabilise_head(fs, bodies):
    """ACC2 polish（頭飾跳幀）：① 頭頂點橫向對返頭頂 run 中點（±2px）② 頭頂點相對身體 bbox 做 3-tap 平滑
    ③ ws median-3＋夾 0.85–1.12（壓扁／轉身幀唔會突然變大帽）④ 傾角每幀變化 ≤8°（第一幀相對 idle 0°）"""
    n = len(fs); ref_pts = []
    for f, b in zip(fs, bodies):
        a = b[..., 3] > 0; h, w = a.shape; u = np.array(f["u"], float); p = np.array([u[1], -u[0]])
        q = np.array(f["top"], float) - 2 * u; ext = []
        for sg in (1, -1):
            t = 0.0
            while t < w:
                x, y = np.round(q + p * sg * (t + .5)).astype(int)
                if not (0 <= x < w and 0 <= y < h and a[y, x]): break
                t += .5
            ext.append(sg * t)
        mid = max(-2.0, min(2.0, (ext[0] + ext[1]) / 2))
        f["top"] = (f["top"][0] + p[0] * mid, f["top"][1] + p[1] * mid)
        ys, xs = np.nonzero(a); ref_pts.append(((xs.min() + xs.max()) / 2, ys.min()))
    off = [(f["top"][0] - r[0], f["top"][1] - r[1]) for f, r in zip(fs, ref_pts)]
    ws = [f["ws"] for f in fs]
    for i, f in enumerate(fs):
        w = off[max(0, i - 1):i + 2]; ox = (sum(o[0] for o in w) + off[i][0]) / (len(w) + 1); oy = (sum(o[1] for o in w) + off[i][1]) / (len(w) + 1)
        f["top"] = (round(ref_pts[i][0] + ox, 2), round(ref_pts[i][1] + oy, 2))
        f["ws"] = min(1.12, max(0.85, sorted(ws[max(0, i - 1):i + 2])[len(ws[max(0, i - 1):i + 2]) // 2]))
        if not i: f["ang"] = max(-8.0, min(8.0, f["ang"]))    # clip 第一幀由 idle（0°）接過嚟
        if i and abs(f["ang"] - fs[i - 1]["ang"]) > 8: f["ang"] = fs[i - 1]["ang"] + math.copysign(8, f["ang"] - fs[i - 1]["ang"])
        if abs(f["ang"]) < 4 and (not i or abs(fs[i - 1]["ang"]) <= 8): f["ang"] = 0.0
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
        if ITEMS[item]["slot"] == "head": stabilise_head(fs, bodies)
        if ITEMS[item].get("pre"): ITEMS[item]["pre"](fs, bodies, alist, form, clip=clip)
        why0 = None
        for adj in ITEMS[item].get("retry", (0,)):     # 例：眼鏡圈逐 0.5px 收細再試（成個 clip 一齊）
            if why and why0 is None: why0 = why
            out = []; why = None; prev = None
            for f in fs: f["adj"] = adj
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
            if not why: break
        if why: hidden[clip] = why0 or why; continue
        for n, ov, info in out: frames[n] = ov
        fits[clip] = [i for _, _, i in out]
    return frames, fits, hidden, S

# 手動收起（睇完動作 preview 決定；原因會寫入 ACCESSORIES.json）
HIDE = {k_: {"*": {"leaf_umbrella": "撐葉傘：葉蓋住頭頂，頭飾收起（避免帽畫喺葉上面）"}} for k_ in ("straw", "beanie", "acorn", "crown", "nightcap")}

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
            frames, fits, hidden, S = gen_item_form(item, form); _store_masks(item, form, frames, fits, S)
            cached_put(item, form, frames, fits, hidden, S)
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
            frames, fits, hidden, _ = cached(it, form)
            n = f"{clip}_{k:02d}"; cells.append(comp(b, frames[n]) if n in frames else bb); labs.append(ITEMS[it]["name"] + ("" if n in frames else " 隱"))
    im = sheet(cells, (len(items) + 1) * 2, 64 + 2 * PAD, scale, labs, f"飾品 × 25 形態 — {clip}_{k:02d}"); im.save(path); return path
CACHE = {}
CACHE_KEEP = None   # ACC5：CACHE 只留 preview／ref 用到嘅幀（25×13 全存 RGBA 太食記憶體）
def cached(item, form):
    global CACHE_KEEP
    if CACHE_KEEP is None: CACHE_KEEP = {"idle_01", "walk_03"} | {f"{c}_{k:02d}" for c, k in FACE_CLIPS}
    if (item, form) not in CACHE:
        fr, fi, hid, S = gen_item_form(item, form)
        if (item, form) not in MASKS: _store_masks(item, form, fr, fi, S)
        CACHE[(item, form)] = ({n: v for n, v in fr.items() if n in CACHE_KEEP}, fi, hid, S)
    return CACHE[(item, form)]
def cached_put(item, form, fr, fi, hid, S):
    global CACHE_KEEP
    if CACHE_KEEP is None: CACHE_KEEP = {"idle_01", "walk_03"} | {f"{c}_{k:02d}" for c, k in FACE_CLIPS}
    CACHE[(item, form)] = ({n: v for n, v in fr.items() if n in CACHE_KEEP}, fi, hid, S)

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
                     "visibility": "一個 clip 任何一幀 fit 唔成立／遮五官／挖空後剩 <65% → 成段收起",
                     "headL": "ACC3 side_l：head_r 以兩眼中垂線鏡像（側面眼距 <0.75×idle 或冇眼就用 fit 中軸）；撞五官向左上推，最多 6px",
                     "glasses": "ACC3 face：鏡片中心＝eyeL／eyeR＋clip 平均眼 blob 偏移；半軸＝max(idle, clip) 眼 blob 半寬／半高＋1.5；"
                                "跟兩眼連線傾角；L 級框粗 2；¾ 圓框（近口內下角開口，dot 用上半框）；faceVisible=false／冇眼成段收起；"
                                "成個 clip 逐級試（收窄／壓扁／上移／向外，再試逐幀跟眼），全部幀過晒先用",
                     "leafcollar": "ACC4 neck：同頸巾一樣嘅頸位（眼下、頸寬 run、跟傾角斜）；尖頭葉一片片（兩隻綠交替）＋前右細花；五官像素清走",
                     "bulbAnchor": "ACC4 bulb slot：燈泡玻璃半徑用手調表 BR（evo 色唔係 v3，唔可以靠色量）；evo_dot／evo_sprout 冇燈泡 → fallback 頭頂；"
                                   "lumi 系／dust／moon 個 bulb 唔喺頭頂（觸角／尾燈／月牙）→ 光環改放頭頂",
                     "bell": "ACC4 bulb：鈴（suzu 5／7／9）吊喺燈泡右下（bulb＋(0.6br, br+1)）；冇燈泡就頭頂芽右邊；"
                             "擺動＝阻尼彈簧（s=0.5s+7vx，夾 ±25°、每幀 ≤14°，loop clip 跑兩轉取第二轉，接得順）；撞五官向右上推",
                     "halo": "ACC4 bulb：橢圓環（後半 GOLDD、前半 GOLD、L 級白反光），環心喺燈泡玻璃上面 br+1.5+ry；非頭頂燈形態放頭頂最高點上 2px（保持水平）；燈泡版傾角夾 ±12°；"
                             "環洞唔描邊、透明；高跳幀貼 padding 頂（PAD 8）",
                     "nightcap": "ACC4 head：圓錐睡帽（zzz 紫＋白斜紋＋白帽邊＋L 級金星），帽尖向左，長尾由帽尖垂落＋白波波；"
                                 "尾擺＝阻尼彈簧（s=0.55s+6vx+4vy，夾 ±30°、每幀 ≤14°，loop 兩轉）；尾撞五官／出 padding → 尾向外擺（dphi）再唔得縮短（tailK）；"
                                 "shroom／moon 用細 hatpin 版；sleep_* 照戴（sleepKeep）"}
    items = {it["key"]: it for it in old.get("items", [])} if isinstance(old.get("items"), list) else dict(old.get("items", {}))
    for key, name, slot, anc, obtain, batch in ALL_ITEMS:
        e = dict(items.get(key, {})); e.update({"key": key, "name": name, "slot": slot, "anchor": anc, "obtain": obtain, "batch": batch})
        if key in summary:
            e["status"] = "done"; e["fit"] = f"items/{key}/fit_{key}.json"; e["forms"] = summary[key]
            e["ref"] = {sc: f"ref/acc_{key}_{sc}.png" for sc in ("S", "M", "L")}
            e["counts"] = {"forms": len(summary[key]), "visibleClips": sum(v["visibleClips"] for v in summary[key].values()),
                           "clips": sum(v["clips"] for v in summary[key].values()), "frames": sum(v["frames"] for v in summary[key].values())}
        else: e.setdefault("status", "planned")
        if ITEMS.get(key, {}).get("sleepKeep"): e["sleepKeep"] = True   # 睡覺 clip 照戴（其他頭飾都冇收起 sleep，呢個係明確標記）
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
            frames, _, _, S = cached(it, form)
            ov = frames["idle_01"]; ys, xs = np.nonzero(ov[..., 3])
            Image.fromarray(ov[ys.min():ys.max() + 1, xs.min():xs.max() + 1], "RGBA").save(os.path.join(rd, f"acc_{it}_{sc}.png"), optimize=True)

FACE_CLIPS = [("idle", 1), ("blink", 2), ("blink", 3), ("emo_happy", 1), ("emo_sleepy", 2), ("sleep_loop", 1), ("cheer_jump", 2), ("walk", 3), ("emo_surprised", 1), ("turn_back", 2)]
def preview_face(item, forms, path, clips=FACE_CLIPS, sc=6):
    """面部近鏡：以兩眼中點做中心，26×20 px 一格"""
    cw, ch = 26, 20; rows = []
    for form in forms:
        frames, _, _, S = cached(item, form); A = anchors(form); row = []
        for c, k in clips:
            cell = np.zeros((ch, cw, 4), np.uint8); cell[...] = (120, 120, 120, 255)
            if c in A and k <= len(A[c]):
                b = load(frame_path(form, c, k)); n = f"{c}_{k:02d}"; an = A[c][k - 1]; im = b.copy()
                if n in frames:
                    o = frames[n][PAD:PAD + S, PAD:PAD + S]; m = o[..., 3] > 0; im[m] = o[m]
                a0 = an if "eyeL" in an else A["idle"][0]; cy = a0["eyeL"][1]; cx = (a0["eyeL"][0] + a0["eyeR"][0]) // 2
                cell[...] = (245, 240, 230, 255) if n in frames else (190, 190, 190, 255)
                y0, x0 = cy - 9, cx - 13
                for yy in range(ch):
                    for xx in range(cw):
                        Y, X = y0 + yy, x0 + xx
                        if 0 <= Y < S and 0 <= X < S and im[Y, X, 3] > 0: cell[yy, xx] = im[Y, X]
            row.append(cell)
        rows.append(row)
    W = Image.new("RGBA", ((cw * sc + 4) * len(clips), (ch * sc + 4) * len(rows)), (255, 255, 255, 255))
    for j, row in enumerate(rows):
        for i, cell in enumerate(row): W.paste(Image.fromarray(cell).resize((cw * sc, ch * sc), Image.NEAREST), (i * (cw * sc + 4), j * (ch * sc + 4)))
    W.save(path, optimize=True); return path

def preview_contact(items, path, clip="idle", k=1, scale=2):
    """ACC5：25 形態（行）× 13 件（列）全表；第一列係冇戴；灰格＝呢個 clip 收起"""
    cell = 64 + 2 * PAD; lw = 120; th = 40; cs = cell * scale
    W_ = lw + (len(items) + 1) * cs; H_ = th + len(FORMS) * cs + 24
    im = Image.new("RGB", (W_, H_), (246, 240, 230)); d = ImageDraw.Draw(im); f = font(12); fb = font(14)
    d.text((6, 4), f"團絨飾品 25 形態 × {len(items)} 件 — {clip}_{k:02d}（{scale}x；灰格＝收起；第一列＝冇戴）", fill=(59, 42, 62), font=fb)
    for i, it in enumerate(["—"] + list(items)):
        d.text((lw + i * cs + 4, 22), "冇戴" if it == "—" else f"{ITEMS[it]['name']}", fill=(59, 42, 62), font=f)
    for j, form in enumerate(FORMS):
        y0 = th + j * cs; d.text((4, y0 + cs // 2 - 7), form.replace("evo_", ""), fill=(59, 42, 62), font=f)
        b = load(frame_path(form, clip, k)); S = b.shape[0]
        for i, it in enumerate([None] + list(items)):
            x0 = lw + i * cs; n = f"{clip}_{k:02d}"
            if it is None: c = np.zeros((S + 2 * PAD, S + 2 * PAD, 4), np.uint8); c[PAD:PAD + S, PAD:PAD + S] = b; hid = False
            else:
                frames, _, _, _ = cached(it, form); hid = n not in frames
                c = comp(b, frames[n]) if not hid else None
                if hid: c = np.zeros((S + 2 * PAD, S + 2 * PAD, 4), np.uint8); c[PAD:PAD + S, PAD:PAD + S] = b
            bg = (196, 192, 188) if hid else ((236, 228, 216) if (i + j) % 2 else (246, 240, 230))
            d.rectangle([x0, y0, x0 + cs - 1, y0 + cs - 1], fill=bg)
            t = Image.fromarray(c); t = t.resize((t.width * scale, t.height * scale), Image.NEAREST)
            im.paste(t, (x0 + (cs - t.width) // 2, y0 + (cs - t.height) // 2), t)
    im.save(path, optimize=True); return path
def preview_outfits(combos, path, scale=3, ov=None):
    """ACC5：同戴組合示範（每形態 3 套，規則套用後）：帽＋光環＋蝴蝶結＋頸巾＋眼鏡 等"""
    sets = [("straw", "halo", "bow", "scarf", "glasses"), ("crown", "bell", "starclip", "leafcollar", "glasses"),
            ("nightcap", "halo", "sakura", "bow", "scarf"), ("beanie", "halo", "starclip", "bow", "leafcollar"), ("acorn", "bell", "sakura", "bow", "scarf")]
    forms = ["sprout", "evo_dot", "evo_hop", "evo_guard_radiant", "evo_guard_moon", "evo_still_moon", "evo_guard_shroom", "evo_still_shroom",
             "evo_guard_dust", "evo_still_ember", "radiant", "lumi"]
    cells = []; labs = []
    for form in forms:
        b = load(frame_path(form, "idle", 1)); S = b.shape[0]
        for st in sets:
            off, hide = resolve_outfit(combos, form, list(st), "idle", ov)
            c = np.zeros((S + 2 * PAD, S + 2 * PAD, 4), np.uint8); c[PAD:PAD + S, PAD:PAD + S] = b
            for it in sorted(st, key=lambda x: SLOT_ORDER.index(ITEMS[x]["slot"])):
                if it in hide: continue
                fr, _, _, _ = cached(it, form)
                if "idle_01" not in fr: continue
                o = fr["idle_01"]; dx, dy = off[it]
                if dx or dy: o = np.roll(np.roll(o, dy, 0), dx, 1)
                m = o[..., 3] > 0; c[m] = o[m]
            cells.append(c); labs.append(form.replace("evo_", "")[:9] + " " + "".join(ITEMS[i]["name"][0] for i in st))
    im = sheet(cells, len(sets), 64 + 2 * PAD, scale, labs, "ACC5 同戴示範（idle_01，COMBOS 規則套用後）"); im.save(path, optimize=True); return path
def build_previews(items):
    os.makedirs(PREV, exist_ok=True); out = []
    half = (len(FORMS) + 1) // 2
    for bt in ("ACC1", "ACC2", "ACC3", "ACC4"):    # 每批一套：idle／walk_03 × 25 形態（A／B 兩半）
        its = [i for i in items if ITEMS[i]["batch"] == bt]
        if not its: continue
        p_ = bt.lower()
        out.append(preview_idle(its, os.path.join(PREV, f"{p_}_forms_idle_a_3x.png"), FORMS[:half]))
        out.append(preview_idle(its, os.path.join(PREV, f"{p_}_forms_idle_b_3x.png"), FORMS[half:]))
        out.append(preview_idle(its, os.path.join(PREV, f"{p_}_forms_walk03_a_3x.png"), FORMS[:half], clip="walk", k=3))
        out.append(preview_idle(its, os.path.join(PREV, f"{p_}_forms_walk03_b_3x.png"), FORMS[half:], clip="walk", k=3))
    sets = {("acc1", "straw"): (["sprout", "evo_guard_radiant", "radiant"], ["cheer_jump", "lookup_tip", "getup", "rush", "turn_back"]),
            ("acc1", "straw_b"): (["lumi", "evo_still_moon", "evo_guard_shroom"], ["cheer_jump", "lookup_tip", "getup", "picked_up", "sleep_loop"]),
            ("acc1", "bow"): (["evo_dot", "evo_guard_lumi", "soft"], ["cheer_jump", "lookup_tip", "getup", "rush", "turn_back"]),
            ("acc1", "scarf"): (["evo_hop", "radiant", "evo_guard_dust"], ["cheer_jump", "lookup_tip", "rush", "picked_up", "leaf_umbrella"]),
            ("acc2", "beanie"): (["evo_sprout", "soft", "evo_guard_lumi"], ["cheer_jump", "lookup_tip", "getup", "shiver", "turn_back"]),
            ("acc2", "acorn"): (["sprout", "evo_still_ember", "evo_guard_crystal"], ["cheer_jump", "lookup_tip", "getup", "rush", "picked_up"]),
            ("acc2", "crown"): (["evo_dot", "radiant", "lumi"], ["cheer_jump", "lookup_tip", "getup", "rush", "turn_back"]),
            ("acc2", "hatpin"): (["evo_guard_moon", "evo_still_moon", "evo_guard_shroom", "evo_still_shroom"], ["idle", "cheer_jump", "lookup_tip"]),
            ("acc3", "starclip"): (["sprout", "evo_guard_radiant", "soft"], ["cheer_jump", "lookup_tip", "getup", "rush", "turn_back"]),
            ("acc3", "sakura"): (["evo_hop", "evo_still_moon", "lumi"], ["cheer_jump", "lookup_tip", "walk", "picked_up", "sleep_loop"]),
            ("acc3", "glasses"): (["evo_guard_radiant", "radiant", "evo_sprout"], ["blink", "sleep_loop", "cheer_jump", "walk", "turn_back"]),
            ("acc4", "leafcollar"): (["sprout", "evo_still_tide", "soft"], ["cheer_jump", "lookup_tip", "rush", "picked_up", "leaf_umbrella"]),
            ("acc4", "bell"): (["sprout", "evo_dot", "radiant", "evo_guard_dust"], ["walk", "cheer_jump", "rush", "turn_back", "sleep_loop"]),
            ("acc4", "halo"): (["evo_sprout", "evo_guard_radiant", "lumi", "evo_still_moon"], ["cheer_jump", "lookup_tip", "getup", "rush", "leaf_umbrella"]),
            ("acc4", "nightcap"): (["sprout", "evo_guard_crystal", "radiant"], ["walk", "cheer_jump", "rush", "sleep_loop", "turn_back"]),
            ("acc4", "nightcap_b"): (["evo_guard_moon", "evo_still_shroom", "lumi"], ["fall_asleep", "sleep_loop", "getup", "cheer_jump", "lookup_tip"])}
    for (bt, k), (forms, clips) in sets.items():
        if k == "hatpin":
            for it in ("beanie", "acorn", "crown"):
                if it in items: out.append(preview_motion(it, forms, clips, os.path.join(PREV, f"{bt}_motion_hatpin_{it}_3x.png"), scale=3, maxf=4))
            continue
        it = k.split("_")[0]
        if it in items: out.append(preview_motion(it, forms, clips, os.path.join(PREV, f"{bt}_motion_{k}_3x.png"), scale=3, maxf=6))
    if "glasses" in items:   # 眼鏡：面部近鏡（6x），睇眨眼／閉眼／表情；灰底＝呢個 clip 收起
        out.append(preview_face("glasses", ["sprout", "evo_dot", "evo_sprout", "evo_hop", "evo_guard_radiant", "evo_still_moon", "evo_guard_shroom"],
                                os.path.join(PREV, "acc3_glasses_face_a_6x.png")))
        out.append(preview_face("glasses", ["evo_still_tide", "evo_guard_ember", "soft", "radiant", "lumi", "evo_still_lumi", "evo_guard_crystal"],
                                os.path.join(PREV, "acc3_glasses_face_b_6x.png")))
    if len(items) == len(ITEMS):   # ACC5：全表 contact sheet（idle_01／walk_03）＋同戴示範
        out.append(preview_contact(items, os.path.join(PREV, "acc5_contact_25x13_idle_2x.png")))
        out.append(preview_contact(items, os.path.join(PREV, "acc5_contact_25x13_walk03_2x.png"), clip="walk", k=3))
        cp = os.path.join(ACCD, "COMBOS.json")
        if os.path.exists(cp):
            cj = json.load(open(cp)); out.append(preview_outfits(cj["forms"], os.path.join(PREV, "acc5_outfits_idle_3x.png"), ov=cj.get("outfitOverrides")))
        out.append(preview_motion("bow", ["sprout", "evo_guard_radiant", "evo_guard_moon"], ["turn_back"], os.path.join(PREV, "acc5_backview_bow_3x.png"), scale=3, maxf=4))
        out.append(preview_motion("starclip", ["sprout", "evo_guard_radiant", "lumi"], ["turn_back"], os.path.join(PREV, "acc5_backview_starclip_3x.png"), scale=3, maxf=4))
        out.append(preview_motion("sakura", ["evo_hop", "evo_still_moon", "soft"], ["turn_back"], os.path.join(PREV, "acc5_backview_sakura_3x.png"), scale=3, maxf=4))
        out.append(preview_motion("nightcap", ["evo_guard_moon", "evo_still_moon"], ["idle", "walk", "cheer_jump", "sleep_loop"], os.path.join(PREV, "acc5_motion_nightcap_moon_3x.png"), scale=3, maxf=6))
        out.append(preview_motion("bell", ["evo_guard_dust", "evo_still_dust"], ["idle", "walk", "cheer_jump", "rush"], os.path.join(PREV, "acc5_motion_bell_dust_3x.png"), scale=3, maxf=6))
        out.append(preview_face("glasses", ["evo_dot"], os.path.join(PREV, "acc5_glasses_dot_face_6x.png")))
    # 收藏品
    cells = []; labs = []
    for key, name, cat in COL:
        for suf in ("32", "32_sil", "16", "16_sil"):
            cells.append(np.array(Image.open(os.path.join(COLD, f"col_{key}_{suf}.png")).convert("RGBA"))); labs.append(f"{name} {suf}" if suf == "32" else suf)
    im = sheet(cells, 8, 36, 4, labs, "收藏品 12 件 — 32／剪影／16／剪影（4x）"); p = os.path.join(PREV, "acc1_collectibles_4x.png"); im.save(p); out.append(p)
    return out

# ================================================================ ACC5：多 slot 同戴（COMBOS）
# 規則：每 slot 最多 1 件、全身最多 5 件（6 個 slot 唔可以全滿）。兩件交疊時，按 YIELD 次序靠前嗰件「讓位」：
#   · 底下嗰件（drawOrder 較前）俾上面嗰件遮咗 > COVER_MAX → 衝突
#   · halo 係浮喺頭頂嘅光環：同任何飾品有交疊都當衝突（要升到帽頂上面）
#   讓位＝成個 clip 用同一個整數位移（候選按 YIELD_STEPS 由細到大試）；位移後唔可以遮五官／燈泡、唔可以出 overlay 畫布；
#   試晒都唔得 → 呢個組合喺呢個 clip 收起讓位嗰件（hide）。
SLOT_ORDER = ["neck", "head", "side_r", "side_l", "face", "bulb"]        # 同 drawOrder（body, face, neck, head, side_r, side_l, face_acc, bulb）
YIELD = ["halo", "bell", "starclip", "sakura", "bow", "leafcollar", "scarf", "glasses", "straw", "beanie", "acorn", "crown", "nightcap"]
COVER_MAX = 0.30
COVER_MAX_PAIR = {"bell": 0.50}   # 鈴細粒、吊住燈泡：畫喺帽上面可以，帽要留 ≥50%
FLOAT_OK = {"halo"}               # 浮喺頭頂；其餘讓位後一定要仲貼住身體或者對方（唔可以飄走）
MAX_WORN = 5
def _steps(dirs, n):
    out = []
    for k in range(1, n + 1):
        for dx, dy in dirs: out.append((dx * k, dy * k))
    return out
YIELD_STEPS = {
    "halo": [(0, -k) for k in range(1, 9)],
    "bell": _steps([(1, 0), (1, 1), (0, 1), (1, -1)], 2),
    "starclip": _steps([(-1, 0), (-1, 1), (-1, -1), (0, 1)], 4), "sakura": _steps([(-1, 0), (-1, 1), (-1, -1), (0, 1)], 4),
    "bow": _steps([(1, 0), (1, 1), (1, -1), (0, 1)], 4),
    "leafcollar": [(0, 1), (0, 2)], "scarf": [(0, 1), (0, 2)], "glasses": [],
    "straw": [(0, -1), (0, -2)], "beanie": [(0, -1), (0, -2)], "acorn": [(0, -1), (0, -2)], "crown": [(0, -1), (0, -2)], "nightcap": [(0, -1), (0, -2)],
}
def _shift(m, dx, dy):
    """bool mask 整數位移；有像素會出畫布就回傳 None"""
    if not dx and not dy: return m
    H, W = m.shape; ys, xs = np.nonzero(m)
    if len(ys) and (ys.min() + dy < 0 or ys.max() + dy >= H or xs.min() + dx < 0 or xs.max() + dx >= W): return None
    o = np.zeros_like(m); o[ys + dy, xs + dx] = True; return o
def _under_over(a, b):
    sa, sb = SLOT_ORDER.index(ITEMS[a]["slot"]), SLOT_ORDER.index(ITEMS[b]["slot"]); return (a, b) if sa < sb else (b, a)
def _conflict(ma, mb, a, b):
    """回傳 (衝突?, 遮咗底下嗰件幾多比例)"""
    ov = int((ma & mb).sum())
    if not ov: return False, 0.0
    if "halo" in (a, b): return True, 1.0
    u, o = _under_over(a, b); mu = ma if u == a else mb
    lim = min([COVER_MAX_PAIR.get(x, COVER_MAX) for x in (a, b)] + [COVER_MAX]) if not any(x in COVER_MAX_PAIR for x in (a, b)) else max(COVER_MAX_PAIR.get(x, COVER_MAX) for x in (a, b))
    r = ov / max(1, int(mu.sum())); return r > lim, r
def _attached(m, body, other):
    """讓位後仲貼住：位移後 mask（擴 1px）掂到身體或者對方"""
    S = body.shape[0]; base = other.copy(); base[PAD:PAD + S, PAD:PAD + S] |= body[..., 3] > 0
    g = m.copy(); g[1:] |= m[:-1]; g[:-1] |= m[1:]; g[:, 1:] |= m[:, :-1]; g[:, :-1] |= m[:, 1:]
    return bool((g & base).any())
def _bad_spot(m, body, an, S):
    for x, y in face_px(an, S):
        if m[y + PAD, x + PAD]: return True
    if "bulb" in an:
        x, y = an["bulb"]
        if body[y, x, 3] and any(m[y + j + PAD, x + i + PAD] and body[y + j, x + i, 3] for i in (-1, 0, 1) for j in (-1, 0, 1)
                                 if 0 <= y + j < body.shape[0] and 0 <= x + i < body.shape[1]): return True
    return False
MASKS = {}   # (item, form) → ({frame: packbits alpha}, fits, S, shape)；build_items 順手存（慳記憶體，唔存 RGBA）
def _store_masks(item, form, frames, fits, S):
    MASKS[(item, form)] = ({n: np.packbits(ov[..., 3] > 0) for n, ov in frames.items()}, fits, S, (S + 2 * PAD, S + 2 * PAD))
def item_masks(item, form):
    if (item, form) not in MASKS:
        fr, fi, hid, S = gen_item_form(item, form); _store_masks(item, form, fr, fi, S)
    pk, fi, S, sh = MASKS[(item, form)]; n_ = sh[0] * sh[1]
    return {n: np.unpackbits(v, count=n_).reshape(sh).astype(bool) for n, v in pk.items()}, fi, S
def combo_pair(form, a, b, MA, MB, FA, FB, bodies, anl, S):
    """一對 item（唔同 slot）喺一個形態：逐 clip 搵讓位；回傳 {clip: {"yield": y, "off": [dx,dy]} | {"yield": y, "hide": True}}"""
    y_ = a if YIELD.index(a) < YIELD.index(b) else b; st = b if y_ == a else a
    MY, MS = (MA, MB) if y_ == a else (MB, MA)
    res = {}; stats = {"frames": 0, "conflictFrames": 0, "maxCover": 0.0}
    for clip in sorted(set(FA) & set(FB)):
        names = [f"{clip}_{k:02d}" for k in range(1, len(FA[clip]) + 1) if f"{clip}_{k:02d}" in MY and f"{clip}_{k:02d}" in MS]
        bad = []
        for n in names:
            c, r = _conflict(MY[n], MS[n], y_, st); stats["frames"] += 1; stats["maxCover"] = max(stats["maxCover"], r)
            if c: bad.append(n)
        if not bad: continue
        stats["conflictFrames"] += len(bad); ok = None
        for dx, dy in YIELD_STEPS[y_]:
            good = True
            for n in names:
                m2 = _shift(MY[n], dx, dy)
                if m2 is None or _conflict(m2, MS[n], y_, st)[0] or _bad_spot(m2, bodies[n], anl[n], S) or \
                   (y_ not in FLOAT_OK and not _attached(m2, bodies[n], MS[n])): good = False; break
            if good: ok = (dx, dy); break
        res[clip] = {"yield": y_, "off": list(ok)} if ok else {"yield": y_, "hide": True}
    return res, stats
def build_combos(items):
    """全部形態 × 唔同 slot 嘅 item 對；寫 accessories/COMBOS.json（只記有讓位嘅 clip）"""
    out = {}; tot = {"pairs": 0, "pairsWithRule": 0, "clipsOffset": 0, "clipsHide": 0, "frames": 0, "conflictFrames": 0}
    per_pair = {}
    for form in FORMS:
        an = anchors(form); bodies = {}; anl = {}
        for clip, alist in clips_of(form):
            for k, a_ in enumerate(alist, 1):
                n = f"{clip}_{k:02d}"; bodies[n] = load(frame_path(form, clip, k)); anl[n] = a_
        M = {}; F = {}; S = None
        for it in items: M[it], F[it], S = item_masks(it, form)
        fo = {}
        for i, a in enumerate(items):
            for b in items[i + 1:]:
                if ITEMS[a]["slot"] == ITEMS[b]["slot"]: continue
                tot["pairs"] += 1
                r, st = combo_pair(form, a, b, M[a], M[b], F[a], F[b], bodies, anl, S)
                tot["frames"] += st["frames"]; tot["conflictFrames"] += st["conflictFrames"]
                k_ = f"{a}+{b}"; pp = per_pair.setdefault(k_, {"forms": 0, "clipsOffset": 0, "clipsHide": 0, "maxCover": 0.0})
                pp["maxCover"] = round(max(pp["maxCover"], st["maxCover"]), 3)
                if r:
                    fo[k_] = r; tot["pairsWithRule"] += 1; pp["forms"] += 1
                    for v in r.values():
                        if v.get("hide"): tot["clipsHide"] += 1; pp["clipsHide"] += 1
                        else: tot["clipsOffset"] += 1; pp["clipsOffset"] += 1
        out[form] = fo
        print("combos", form, len(fo), "pairs with rules", flush=True)
    return out, tot, per_pair
def outfit_key(worn): return "+".join(sorted(worn))
def resolve_outfit(combos, form, worn, clip, ov=None):
    """引擎規則（validator 同 sim 用）：每件讓位 item 取所有相關對入面位移最大（|dx|+|dy|，同分取 YIELD 對嘅字典序先）；任何一對 hide → 收起；
    最後再套 outfitOverrides[form][outfit_key][clip]（多件疊埋先出現嘅殘留衝突 → 收起指定 item）"""
    off = {it: (0, 0) for it in worn}; hide = set((ov or {}).get(form, {}).get(outfit_key(worn), {}).get(clip, []))
    for i, a in enumerate(sorted(worn)):
        for b in sorted(worn)[i + 1:]:
            k_ = f"{a}+{b}" if f"{a}+{b}" in combos.get(form, {}) else f"{b}+{a}"
            r = combos.get(form, {}).get(k_, {}).get(clip)
            if not r: continue
            if r.get("hide"): hide.add(r["yield"]); continue
            o = tuple(r["off"]); cur = off[r["yield"]]
            if abs(o[0]) + abs(o[1]) > abs(cur[0]) + abs(cur[1]): off[r["yield"]] = o
    return off, hide
def outfits(items):
    """全部合法組合（每 slot ≤1、總數 2..MAX_WORN）"""
    by = {}
    for it in items: by.setdefault(ITEMS[it]["slot"], []).append(it)
    sl = [s_ for s_ in SLOT_ORDER if s_ in by]; res = []
    def rec(i, cur):
        if i == len(sl):
            if 2 <= len(cur) <= MAX_WORN: res.append(tuple(cur))
            return
        rec(i + 1, cur)
        for it in by[sl[i]]: rec(i + 1, cur + [it])
    rec(0, []); return res
def check_outfits(combos, items, forms=None, log=None, ov=None):
    """套用 resolve_outfit 之後，逐組合逐 clip 逐幀再驗：兩兩冇衝突、讓位件冇遮五官／燈泡、冇出畫布、仲貼住。回傳 (組合數, 驗過幀數, 殘留 list)"""
    forms = forms or FORMS; OUT = outfits(items); nchk = 0; bad = []
    for form in forms:
        fc = combos.get(form, {})
        rel = [o for o in OUT if sum(1 for i, a in enumerate(o) for b in o[i + 1:] if f"{a}+{b}" in fc or f"{b}+{a}" in fc) >= 1]
        if not rel: continue
        M = {}; F = {}; S = None
        for it in items: M[it], F[it], S = item_masks(it, form)
        an = anchors(form); bodies = {}; anl = {}
        for clip, alist in clips_of(form):
            for k, a_ in enumerate(alist, 1): n = f"{clip}_{k:02d}"; bodies[n] = None; anl[n] = a_
        def body(n):
            if bodies[n] is None: c_, k_ = n.rsplit("_", 1); bodies[n] = load(frame_path(form, c_, int(k_)))
            return bodies[n]
        for o in rel:
            for clip in sorted(set.intersection(*[set(F[it]) for it in o])) if o else []:
                off, hide = resolve_outfit(combos, form, o, clip, ov)
                if not any(off[i] != (0, 0) for i in off) and not hide: continue
                vis = [i for i in o if i not in hide]
                for k in range(1, len(F[vis[0]][clip]) + 1 if vis else 1):
                    n = f"{clip}_{k:02d}"; ms = {}
                    for it in vis:
                        m = M[it].get(n)
                        if m is None: continue
                        dx, dy = off[it]; m2 = _shift(m, dx, dy)
                        if m2 is None: bad.append((form, o, n, it, "出畫布")); continue
                        if (dx or dy) and _bad_spot(m2, body(n), anl[n], S): bad.append((form, o, n, it, "遮五官／燈泡"))
                        ms[it] = m2
                    ks = sorted(ms)
                    for i, a in enumerate(ks):
                        for b in ks[i + 1:]:
                            if ITEMS[a]["slot"] == ITEMS[b]["slot"]: continue
                            nchk += 1
                            if _conflict(ms[a], ms[b], a, b)[0]: bad.append((form, o, n, f"{a}+{b}", "殘留衝突"))
        if log: log(f"outfits {form}: {len(rel)} 組合要驗，累計殘留 {len(bad)}")
    return len(OUT), nchk, bad
def fix_outfits(combos, items, log=None, rounds=4):
    """check_outfits 有殘留 → 收起該對入面 YIELD 排先嗰件（單件問題就收起嗰件），寫入 overrides，再驗受影響 forms，直到 0"""
    ov = {}; forms = None; hist = []
    for r in range(rounds):
        n, nchk, bad = check_outfits(combos, items, forms, log, ov); hist.append((len(forms or FORMS), nchk, len(bad)))
        if not bad:   # 固定次序（唔靠 set／hash 次序 → rebuild byte-identical）
            ov = {f: {k: {c: ov[f][k][c] for c in sorted(ov[f][k])} for k in sorted(ov[f])} for f in FORMS if f in ov}
            return ov, n, hist
        touched = set()
        for form, o, fr, what, why in bad:
            clip = fr.rsplit("_", 1)[0]
            if "+" in what:
                a, b = what.split("+"); h = a if YIELD.index(a) < YIELD.index(b) else b
            else: h = what
            lst = ov.setdefault(form, {}).setdefault(outfit_key(o), {}).setdefault(clip, [])
            if h not in lst: lst.append(h); lst.sort()
            touched.add(form)
        forms = [f for f in FORMS if f in touched]
    raise SystemExit(f"outfit overrides 收唔到斂：{hist}")
def emissive_path(form, n):
    if form == "lumi": return os.path.join(LU, "emissive", f"{n}_emissive.png")
    if form in ("sprout", "radiant", "soft"): return None
    return os.path.join(EV, form, "emissive", f"{n}_emissive.png")
def emissive_stats(items):
    """ACC5：每個 item × form，飾品 alpha 蓋住幾多 emissive 像素（引擎規則：emissive 畫喺飾品之後，但用飾品 alpha 聯集遮走；燈泡 ±1 本身已挖空）"""
    out = {}
    for form in FORMS:
        an = anchors(form); em = {}
        for clip, alist in clips_of(form):
            for k in range(1, len(alist) + 1):
                n = f"{clip}_{k:02d}"; p_ = emissive_path(form, n)
                if p_ and os.path.exists(p_): em[n] = np.array(Image.open(p_).convert("RGBA"))[..., 3] > 0
        if not em: out[form] = None; continue
        fo = {}
        for it in items:
            M, F, S = item_masks(it, form); tot = cov = 0; mx = 0.0; nf = 0
            for n, m in M.items():
                e = em.get(n)
                if e is None: continue
                h, w = e.shape; c = m[PAD:PAD + h, PAD:PAD + w] & e
                t_, c_ = int(e.sum()), int(c.sum()); tot += t_; cov += c_; nf += 1
                if t_: mx = max(mx, c_ / t_)
            fo[it] = {"frames": nf, "emissivePx": tot, "coveredPx": cov, "coveredFrac": round(cov / tot, 4) if tot else 0.0, "maxFrameFrac": round(mx, 4)}
        out[form] = fo; print("emissive", form, sum(v["coveredPx"] for v in fo.values()), flush=True)
    return out
def visibility_review(summary):
    """ACC5：可見度總覆核（item × form 可見 clip／總 clip，收起原因分類）"""
    rv = {}; reasons = {}
    for it, fs in summary.items():
        r = {"visibleClips": 0, "clips": 0, "formsFull": 0, "byForm": {}}
        for form, v in fs.items():
            r["visibleClips"] += v["visibleClips"]; r["clips"] += v["clips"]; r["formsFull"] += v["visibleClips"] == v["clips"]
            r["byForm"][form] = f"{v['visibleClips']}/{v['clips']}"
            for c, why in v["hidden"].items():
                k_ = why if isinstance(why, str) else json.dumps(why, ensure_ascii=False)
                k_ = k_.split(": ", 1)[-1] if k_.startswith(c) else k_
                k_ = k_.split("（")[0].split(" ")[0][:40]
                reasons.setdefault(k_, 0); reasons[k_] += 1
        r["pct"] = round(100 * r["visibleClips"] / r["clips"], 1); rv[it] = r
    return {"items": rv, "hiddenReasons": dict(sorted(reasons.items(), key=lambda x: -x[1])),
            "total": {"visibleClips": sum(v["visibleClips"] for v in rv.values()), "clips": sum(v["clips"] for v in rv.values())}}
def write_combos(items, summary):
    """ACC5：多 slot 同戴衝突 → COMBOS.json；emissive／可見度 → ACCESSORIES.json（merge-safe）"""
    combos, tot, per_pair = build_combos(items)
    ov, n_out, hist = fix_outfits(combos, items, log=lambda m: None)
    rules = {"perSlot": 1, "maxWorn": MAX_WORN, "slotOrder": SLOT_ORDER, "yieldPriority": YIELD,
             "coverMax": COVER_MAX, "coverMaxPair": COVER_MAX_PAIR, "floatOk": sorted(FLOAT_OK),
             "yieldSteps": {k: [list(x) for x in v] for k, v in YIELD_STEPS.items()},
             "conflict": "兩件唔同 slot 嘅 item 同一幀：halo 任何重疊都算撞；其餘＝被遮嗰件（讓位件以外）被蓋 > coverMax（bell 對 0.5）",
             "pairRule": "每對只有 YIELD 排先嗰件讓位；逐 clip 試 yieldSteps（整數 px，成段 clip 全部幀都過：唔撞、唔遮五官／燈泡±1、唔出 overlay 畫布、"
                         "除 floatOk 外仲貼住身體或者對方）；全部唔得 → 嗰段 clip 收起讓位件",
             "resolve": "引擎：戴住嘅每對 (a,b) 查 forms[form][a+b][clip]；讓位件取位移最大（|dx|+|dy|，sorted 對次序先到先得）；任何 hide 贏；"
                        "最後套 outfitOverrides[form][sorted items 用 + 連][clip] 列明要收起嘅 item",
             "pairsKey": "a+b 按 ITEMS 次序；查唔到就試 b+a"}
    d = {"version": 1, "batch": "ACC5", "rules": rules, "forms": combos, "outfitOverrides": ov,
         "totals": dict(tot, outfits=n_out, overrideClips=sum(len(o) for f in ov.values() for o in f.values()),
                        overrideHides={h: sum(1 for f in ov.values() for o in f.values() for v in o.values() if h in v) for h in YIELD}),
         "outfitCheck": [{"forms": a, "pairChecks": b, "residual": c} for a, b, c in hist], "perPair": per_pair}
    d["totals"]["overrideHides"] = {k: v for k, v in d["totals"]["overrideHides"].items() if v}
    json.dump(d, open(os.path.join(ACCD, "COMBOS.json"), "w"), ensure_ascii=False, separators=(",", ":"))
    p = os.path.join(ACCD, "ACCESSORIES.json"); A = json.load(open(p))
    A["emissive"] = {"rule": "飾品本身冇 emissive 層；引擎 emissive 照畫喺飾品之後，但用（已解決讓位嘅）飾品 alpha 聯集遮走，即係發光唔會透過帽／頸巾；"
                             "燈泡 ±1 飾品層已挖空，所以燈泡光一定睇到。sprout／radiant／soft 冇 emissive。",
                     "overlap": emissive_stats(items)}
    A["visibilityReview"] = visibility_review(summary)
    A["combos"] = {"file": "COMBOS.json", "maxWorn": MAX_WORN, "perSlot": 1, "totals": d["totals"]}
    json.dump(A, open(p, "w"), ensure_ascii=False, indent=1)
    print("COMBOS", d["totals"], hist, flush=True)
def main(argv):
    what = argv[1] if len(argv) > 1 else "all"; items = [a for a in argv[2:]] or [k for k in ITEMS]
    if what in ("all", "collectibles"): build_collectibles()
    if what in ("all", "items"):
        summ = build_items(items); write_accessories_json(summ); build_refs(items)
        if set(items) == set(ITEMS): write_combos(items, summ)
    if what in ("all", "preview"): print("\n".join(build_previews(items)))
if __name__ == "__main__": main(sys.argv)
