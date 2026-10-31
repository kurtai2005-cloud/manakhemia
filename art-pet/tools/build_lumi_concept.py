#!/usr/bin/env python3
"""build_lumi_concept.py — 團絨隱藏稀有成年形態「螢絨」(lumi) idle 概念草圖。
Pillow + numpy 程式逐像素繪製，無 AI。重用 build_tuanrong.py 嘅 Cv / round_s 骨架參數。
Output -> ../sprites/tuanrong/lumi_concept/
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_tuanrong as bt

ROOT = os.path.normpath(os.path.join(HERE, ".."))
OUT = os.path.join(ROOT, "sprites", "tuanrong", "lumi_concept")
H4 = os.path.join(ROOT, "scenes", "hd2d", "H4")

# ---- lumi palette: shared 31 色，換 6 個 lumi 用唔著嘅槽（peach×3 = 柔光專用, egg_shade/egg_dark = 光卵專用, cyan = 未用）
SWAP = {
 "peach0": ("lumi_fur0", "#A99FD8"),
 "peach1": ("lumi_fur1", "#C6BDEA"),
 "peach2": ("lumi_fur2", "#E2DCF6"),
 "egg_dark": ("fly_d", "#8FCB4E"),
 "egg_shade": ("fly", "#CFF26A"),
 "cyan": ("fly_core", "#F2FFB8"),
}
PAL = {}
for n, h in bt.PAL.items():
    if n in SWAP: nn, hh = SWAP[n]; PAL[nn] = hh
    else: PAL[n] = h
NAMES = list(PAL.keys()); assert len(NAMES) == 31
IDX = {n: i + 1 for i, n in enumerate(NAMES)}
RGB = [(0, 0, 0)] + [tuple(int(PAL[n][i:i + 2], 16) for i in (1, 3, 5)) for n in NAMES]
bt.IDX.clear(); bt.IDX.update(IDX)          # Cv 用新名
GLOW = {IDX["fly_d"], IDX["fly"], IDX["fly_core"]}
EMIS = {IDX["fly"], IDX["fly_core"]}        # emissive = 亮兩級

RAMP = ["zzz", "lumi_fur0", "lumi_fur1", "lumi_fur2"]   # 暗→亮（夜藍紫絨）
TH = bt.TH
bt.RAMPS["lumi"] = RAMP
bt.RAMPS["sun_lumi"] = ["lumi_fur0", "lumi_fur1", "lumi_fur2", "cream4"]   # 曬太陽：亮部暖光（sunbathe）
# round_s 骨架：同燦光 rx/ry/G/pivot；N/rb = lumi 外觀（較順滑「蟲殼」絨）
bt.FORMS["lumi"] = dict(S=64, rx=19.0, ry=16.0, G=61, ramp="lumi", N=14, rb=3.0, big=True, stem=7)
FACE_DX = 2                                   # 面整體右移 2px（向右睇）；anchors 亦 +2
CMF = {"#": "outline", "w": "fly_core", "r": "blush_d", "t": "blush"}
DOTS = ((-13, -3, 1), (-7, -10, 1), (-15, 4, 0), (-9, 3, 0), (-2, -12, 0), (5, -11, 1), (-12, 9, 0), (12, -6, 0))
ANT = ((1, 0.55, 10), (6, 0.85, 9))           # (base dx, lean, length)；第 2 條＝前觸角（bulb 錨點）

def _rot_ell(cv, cx, cy, a, b, ang):
    d = (math.cos(math.radians(ang)), -math.sin(math.radians(ang)))
    X = cv.xx + .5 - cx; Y = cv.yy + .5 - cy
    u = X * d[0] + Y * d[1]; v = -X * d[1] + Y * d[0]
    return (u / a) ** 2 + (v / b) ** 2 <= 1.0, d

def antenna_pts(p, cx, cy, ry):
    """兩條觸角點列（未 shear）；sway 擺、droop 垂（同燦光莖嘅參數語義）"""
    sway = p.get("sway", 0); droop = p.get("droop", 0)
    out = []
    for (bo, lean, ln) in ANT:
        bx = cx + bo; y0 = cy - ry + 1.5; pts = []
        for j in range(ln + 1):
            t = j / ln
            pts.append((bx + lean * j * 0.9 + 2.2 * t * t + sway * t + droop * t * t * 3.0,
                        y0 - j + 1.8 * t * t + droop * t * t * 4.5))
        out.append(pts)
    return out

def tail_center(cx, cy, rx, ry):
    return cx - min(rx, 19.0) - 1.0, cy + ry * 0.42

def glow_level(p):
    """尾燈脈衝 0/1/2：bud 定基準（瞓覺暗、興奮亮）＋逐幀相位"""
    bud = p.get("bud", 1.0)
    base = 0 if bud < 0.75 else (2 if bud >= 1.15 else 1)
    return int(np.clip(base + [0, 1, 0, -1][p.get("_k", 0) % 4], 0, 2))

def render_lumi(p=None):
    """螢絨 parametric renderer — 同 bt.render_pet 參數語義（sx/sy/lift/dx/sway/droop/bud/fluff/twinkle/eyes/mouth/
    blush/arms/feet_in/flift/extras/sick），round_s 骨架，只換外觀層。"""
    p = p or {}
    f = bt.FORMS["lumi"]; S = 64
    sick = p.get("sick", False)
    ramp = "sick" if sick else f["ramp"]
    rcols = np.array([IDX[c] for c in bt.RAMPS[ramp]], np.uint8)
    sx, sy = p.get("sx", 1.0), p.get("sy", 1.0)
    rx, ry = f["rx"] * sx, f["ry"] * sy
    lift = p.get("lift", 0.0)
    cx = S / 2 + p.get("dx", 0.0); bottom = f["G"] - 1.0 - lift; cy = bottom - ry
    cv = bt.Cv(S)
    fl = p.get("fluff", 0.0); k = p.get("_k", 0); tw = p.get("twinkle", k)
    # --- 翼（身後：中／下背，向左後上斜出；身體之後會蓋住內半，只露出輪廓外一截）
    flap = 7.0 * math.sin(fl * 2.0)
    rxa = min(rx, 19.0)   # 附肢（翼／尾燈）錨喺「靜止身寬」：身體橫壓時收埋入身後，唔會撞 64px 邊
    for (bxo, byo, a, b, ang) in ((-0.78, -0.10, 7.8, 3.3, 166), (-0.66, -0.36, 7.0, 2.9, 142)):
        bx0, by0 = cx + bxo * rxa, cy + byo * ry
        aa = ang + flap
        dvec = (math.cos(math.radians(aa)), -math.sin(math.radians(aa)))
        wc = (bx0 + dvec[0] * a * 0.62, by0 + dvec[1] * a * 0.62)
        m, _ = _rot_ell(cv, wc[0], wc[1], a, b, aa)
        cv.paint(m, "drop"); cv.solid |= m
        hi, _ = _rot_ell(cv, wc[0] + dvec[0] * 1.0 - 0.6, wc[1] + dvec[1] * 1.0 - 0.6, a - 2.2, b - 1.6, aa)
        cv.paint(m & hi, "white")
        for s_ in (a * 0.2, a * 0.9):   # 翼脈
            cv.put(wc[0] + dvec[0] * s_ * 0.9 - dvec[1] * 0.3, wc[1] + dvec[1] * s_ * 0.9, "drop_d")
    # --- 尾燈（左後下，螢火蟲腹部）
    tx, ty = tail_center(cx, cy, rx, ry)
    tail = cv.ell(tx, ty, 7.4, 6.6)
    cv.paint(tail, "fly_d" if not sick else "sick0"); cv.solid |= tail
    # --- 腳（同 render_pet）
    fx = rx * 0.45; foot_squash = p.get("feet_in", 0.0); flift = p.get("flift", (0, 0))
    for i, sgn in enumerate((-1, 1)):
        m = cv.ell(cx + sgn * fx * (1 - foot_squash), bottom + 0.35 - flift[i], 2.6, 2.0)
        cv.paint(m, "orange"); cv.solid |= m
        cv.paint(m & (cv.yy >= int(bottom + 0.6)), "orange_d")
    # --- 手
    arms = p.get("arms", "down")
    acol = (RAMP[1] if not sick else bt.ramp_color(ramp, 0.2, TH))
    if arms != "none":
        for sgn in (-1, 1):
            if arms == "down": ax, ay = cx + sgn * (rx - 0.2), cy + ry * 0.2
            elif arms == "up": ax, ay = cx + sgn * (rx - 0.4), cy - ry * 0.35 - 1
            else: ax, ay = cx + sgn * (rx - 0.6), cy + ry * (0.1 if sgn < 0 else 0.0)
            m = cv.ell(ax, ay, 2.3, 2.3); cv.paint(m, acol); cv.solid |= m
    # --- 身（絨毛 bump）
    bm = cv.ell(cx, cy, rx, ry)
    N, rb = f["N"], f["rb"]
    for i in range(N):
        th = 2 * math.pi * (i + 0.5) / N; sn = math.sin(th)
        if sn > 0.78: continue
        wob = 0.3 * math.sin(fl * 2 + min(i, N - 1 - i) * 1.3)
        r_b = rb * (1 + 0.08 * math.cos(2 * th))
        bm |= cv.ell(cx + (rx - r_b * 0.45 + wob) * math.cos(th), cy + (ry - r_b * 0.45 + wob) * sn, r_b, r_b)
    nx = (cv.xx + .5 - cx) / rx; ny = (cv.yy + .5 - cy) / ry
    r2 = np.clip(nx * nx + ny * ny, 0, 1.4)
    sv = -(0.55 * nx + 0.8 * ny) - 0.38 * r2 + 0.15
    kk = np.clip(sum((sv > t).astype(int) for t in TH), 0, 3)
    cv.a[bm] = rcols[kk][bm]; cv.solid |= bm
    bl = cv.ell(cx + 2, cy + ry * 0.34, rx * 0.5, ry * 0.45) & bm
    cv.a[bl & (kk <= 1)] = rcols[2]
    tick = bt.RAMPS[ramp][0]
    for (a_, b_) in [(-0.62, 0.15), (-0.35, 0.62), (0.52, 0.45), (0.68, -0.05), (0.15, 0.78)]:
        px, py = cx + a_ * rx * .95, cy + b_ * ry * .95
        cv.put(px, py, tick); cv.put(px + 1, py + 1, tick)
    if not sick:
        hx, hy = cx - rx * 0.30, cy - ry * 0.58
        for dx, dy in ((0, 0), (1, 0), (2, 0), (-1, 1), (0, -1), (1, -1)): cv.put(hx + dx, hy + dy, "white")
    # --- 觸角（取代芽莖）
    ants = antenna_pts(p, cx, cy, ry)
    for pts in ants:
        for (x, y) in pts:
            xi, yi = int(round(x)), int(round(y))
            if 0 <= xi < S and 0 <= yi < S: cv.a[yi, xi] = IDX["outline"]; cv.solid[yi, xi] = True
    cv.outline()
    # --- 尾燈分節＋發光層次（脈衝）
    seg = tail & ~bm
    for ox in (-0.5, 2.8):
        cv.a[seg & (np.abs(cv.xx + .5 - (tx + ox) - (cv.yy + .5 - ty) * 0.35) < 0.6)] = IDX["outline"]
    lv = glow_level(p)
    free = seg & (cv.a != IDX["outline"])
    if sick:
        cv.a[cv.ell(tx - 1.6, ty + 0.4, 3.6, 3.2) & free] = IDX["sick1"]
    else:
        cr = [(3.8, 3.4, 0.0), (4.8, 4.4, 2.4), (5.4, 5.0, 3.2)][lv]
        cv.a[cv.ell(tx - 1.6, ty + 0.4, cr[0], cr[1]) & free] = IDX["fly"]
        if cr[2]: cv.a[cv.ell(tx - 2.6, ty, cr[2], cr[2]) & free] = IDX["fly_core"]
        else: cv.put(tx - 3, ty, "fly_core")
    # --- 觸角燈頭
    bud = p.get("bud", 1.0)
    for pts in ants:
        x, y = pts[-1]
        r = 2.2 * (0.85 + 0.15 * min(bud, 1.3))
        m = cv.ell(x + .4, y - .6, r, r)
        cv.paint(m, "fly" if not sick else "sick1")
        if not sick:
            cv.put(x, y - 1, "fly_core")
            if bud >= 0.75: cv.put(x + 1, y - 1, "fly_core")
            if bud >= 1.15: cv.put(x, y - 2, "fly_core")
        cv.a[bt_ring(m) & (cv.a == 0)] = IDX["outline"]
    # --- 身上光點（閃爍；跟身體位置／縮放）
    if not sick:
        for i, (dx, dy, big) in enumerate(DOTS):
            x, y = cx + dx * rx / 19.0, cy + dy * ry / 16.0
            xi, yi = int(round(x)), int(round(y))
            if not (0 <= xi < S and 0 <= yi < S) or not bm[yi, xi] or cv.a[yi, xi] == IDX["outline"]: continue
            st = (tw + i) % 4
            if st == 2: cv.put(x, y, "fly_d"); continue
            cv.put(x, y, "fly_core")
            if big and st == 0:
                for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = xi + ox, yi + oy
                    if bm[yy, xx] and cv.a[yy, xx] != IDX["outline"]: cv.a[yy, xx] = IDX["fly"]
    # --- 面（向右：整體右移 FACE_DX）
    fcx = cx + FACE_DX; ey = cy + ry * 0.08; eoff = rx * 0.40
    face = p.get("eyes", "open")
    if face == "sick":
        bt.draw_tmpl_c(cv, fcx - eoff, ey, bt.EYE[True]["sickL"], CMF); bt.draw_tmpl_c(cv, fcx + eoff, ey, bt.EYE[True]["sickR"], CMF)
    else:
        t = bt.EYE[True][face]
        bt.draw_tmpl_c(cv, fcx - eoff, ey, t, CMF); bt.draw_tmpl_c(cv, fcx + eoff, ey, t, CMF)
    bt.draw_tmpl_c(cv, fcx, ey + ry * 0.38, bt.MOUTH[True][p.get("mouth", "smile")], CMF)
    if p.get("blush", True):
        for sgn in (-1, 1):
            mb = cv.ell(fcx + sgn * rx * 0.62, ey + ry * 0.26, 2.4, 1.4)
            cv.a[mb & bm] = IDX["blush" if not sick else "sick0"]
    for fx_ in p.get("extras", []):
        fx_(cv, cx + (FACE_DX if getattr(fx_, "face", False) else 0), cy, rx, ry)
    return cv.a

def bt_ring(m):
    d = np.zeros_like(m); d[1:] |= m[:-1]; d[:-1] |= m[1:]; d[:, 1:] |= m[:, :-1]; d[:, :-1] |= m[:, 1:]
    return d & ~m

def to_img(a):
    rgba = np.zeros(a.shape + (4,), np.uint8)
    for i, c in enumerate(RGB):
        if i: rgba[a == i, :3] = c; rgba[a == i, 3] = 255
    return Image.fromarray(rgba, "RGBA")

def emissive(a):
    m = np.isin(a, list(EMIS))
    o = np.zeros(a.shape + (4,), np.uint8); o[m] = (255, 255, 255, 255)
    return Image.fromarray(o, "RGBA")

def f01(im): return np.asarray(im.convert("RGBA"), float) / 255
def hx(h): return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float) / 255

def h4_panel(sprite, emis):
    """H4 夜景 64×64 crop（art 腳底 (97,292)），按 FORMAT.md 公式簡化合成＋lumi 自身 glow。"""
    g = json.load(open(os.path.join(H4, "grade.json")))
    MX, MY = 14, 12; fx, fy = 97 + MX, 292 + MY
    x0, y0 = fx - 32, fy - 61
    box = (x0, y0, x0 + 64, y0 + 64)
    C = f01(Image.open(os.path.join(H4, "sky.png")).crop(box))[..., :3]
    def over(C, l): a = l[..., 3:]; return C * (1 - a) + l[..., :3] * a
    for n in ("far", "mid"): C = over(C, f01(Image.open(os.path.join(H4, n + ".png")).crop(box)))
    s = f01(sprite); tint = hx(g["petTint"]) * hx(g["ambientTint"])
    ps = s.copy(); ps[..., :3] = s[..., :3] * tint
    em = np.asarray(emis, float)[..., 3:] / 255
    ps[..., :3] = ps[..., :3] * (1 - em) + s[..., :3] * em      # 發光像素唔食夜色 tint
    # 影
    yy, xx = np.mgrid[0:64, 0:64]
    sh = np.exp(-(((xx - 32) / 16) ** 2 + ((yy - 61) / 2.2) ** 2)) * 0.45
    C = C * (1 - sh[..., None])
    C = over(C, ps)
    C = over(C, f01(Image.open(os.path.join(H4, "fore.png")).crop(box)))
    C = C * f01(Image.open(os.path.join(H4, "lightmap.png")).convert("RGBA").crop(box))[..., :3]
    C = C + f01(Image.open(os.path.join(H4, "light_add.png")).convert("RGBA").crop(box))[..., :3]
    C = C + f01(Image.open(os.path.join(H4, "emissive_blur.png")).convert("RGBA").crop(box))[..., :3] * g["bloom"]["intensity"]
    # lumi glow：emissive 模糊（螢光綠）＋ 1px 核
    gl = np.asarray(emis.split()[3].filter(ImageFilter.GaussianBlur(3.0)), float) / 255
    C = C + gl[..., None] * hx("#cff26a") * 1.4
    gl2 = np.asarray(emis.split()[3].filter(ImageFilter.GaussianBlur(1.0)), float) / 255
    C = C + gl2[..., None] * hx("#f2ffb8") * 0.35
    fog = hx(g["fog"]["color"]); d = g["fog"]["density"]; C = C * (1 - d) + fog * d
    return Image.fromarray((np.clip(C, 0, 1) * 255 + .5).astype(np.uint8), "RGB").convert("RGBA")

def main():
    os.makedirs(OUT, exist_ok=True)
    a = render_lumi()
    spr = to_img(a); em = emissive(a)
    spr.save(os.path.join(OUT, "lumi_idle_64.png")); em.save(os.path.join(OUT, "lumi_idle_emissive_64.png"))
    # 驗證
    arr = np.asarray(spr); assert set(np.unique(arr[..., 3])) <= {0, 255}
    cols = {tuple(c) for c in arr[arr[..., 3] > 0][:, :3]}
    assert cols <= set(RGB[1:]), "off-palette"
    fr = os.path.join(ROOT, "sprites", "tuanrong", "frames")
    bg = Image.new("RGBA", (64, 64), (58, 56, 78, 255))
    panels = []
    for im in (Image.open(os.path.join(fr, "pet_tuanrong_radiant_idle_01.png")),
               Image.open(os.path.join(fr, "pet_tuanrong_soft_idle_01.png")), spr):
        b = bg.copy(); b.alpha_composite(im.convert("RGBA")); panels.append(b)
    panels.append(h4_panel(spr, em))
    G = 8; pad = 8
    sheet = Image.new("RGBA", (4 * 64 * G + 5 * pad, 64 * G + 2 * pad), (24, 22, 34, 255))
    for i, pnl in enumerate(panels):
        sheet.paste(pnl.resize((64 * G, 64 * G), Image.NEAREST), (pad + i * (64 * G + pad), pad))
    sheet.save(os.path.join(OUT, "lumi_concept_8x.png"))
    json.dump({"form": "lumi", "name": "螢絨", "count": 31, "swapped": {k: v[0] for k, v in SWAP.items()},
               "colors": [{"index": IDX[n], "name": n, "hex": PAL[n]} for n in NAMES],
               "used_in_sketch": sorted({NAMES[i - 1] for i in np.unique(a) if i})},
              open(os.path.join(OUT, "palette_lumi.json"), "w"), ensure_ascii=False, indent=1)
    print("ok colours used:", len(cols), "emissive px:", int((np.asarray(em)[..., 3] > 0).sum()))

if __name__ == "__main__":
    main()
