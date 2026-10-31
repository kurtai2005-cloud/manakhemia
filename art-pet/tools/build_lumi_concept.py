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

def render_lumi(p=None):
    p = p or {}
    S = 64; rx, ry = 19.0 * p.get("sx", 1), 16.0 * p.get("sy", 1)   # round_s：同燦光 rx/ry、pivot (32,61)
    cv = bt.Cv(S)
    cx = S / 2; bottom = 61 - 1.0; cy = bottom - ry
    # --- 翅膀（身後，左上背）：細半透明感用 white/drop
    for (wx, wy, wrx, wry) in ((cx - 12, cy - ry - 0.5, 6.0, 3.6), (cx - 6, cy - ry - 2.5, 5.0, 3.2)):
        m = cv.ell(wx, wy, wrx, wry); cv.paint(m, "drop"); cv.solid |= m
        cv.paint(m & cv.ell(wx - 0.8, wy - 0.8, wrx - 1.4, wry - 1.3), "white")
    # --- 尾燈（左後下，螢火蟲腹部）
    tx, ty = cx - rx - 1.0, cy + ry * 0.42
    tail = cv.ell(tx, ty, 7.4, 6.6)
    cv.paint(tail, "fly_d"); cv.solid |= tail
    # --- 腳
    fx = rx * 0.45
    for sgn in (-1, 1):
        m = cv.ell(cx + sgn * fx, bottom + 0.35, 2.6, 2.0)
        cv.paint(m, "orange"); cv.solid |= m
        cv.paint(m & (cv.yy >= int(bottom + 0.6)), "orange_d")
    # --- 手
    for sgn in (-1, 1):
        m = cv.ell(cx + sgn * (rx - 0.2), cy + ry * 0.2, 2.3, 2.3)
        cv.paint(m, "lumi_fur0"); cv.solid |= m
    # --- 身（絨毛 bump；比燦光少啲、細啲 = 更順滑「蟲殼」感）
    bm = cv.ell(cx, cy, rx, ry)
    N, rb = 14, 3.0
    for i in range(N):
        th = 2 * math.pi * (i + 0.5) / N; sn = math.sin(th)
        if sn > 0.78: continue
        bm |= cv.ell(cx + (rx - rb * 0.45) * math.cos(th), cy + (ry - rb * 0.45) * sn, rb, rb)
    nx = (cv.xx + .5 - cx) / rx; ny = (cv.yy + .5 - cy) / ry
    r2 = np.clip(nx * nx + ny * ny, 0, 1.4)
    sv = -(0.55 * nx + 0.8 * ny) - 0.38 * r2 + 0.15
    kk = np.clip(sum((sv > t).astype(int) for t in TH), 0, 3)
    rc = np.array([IDX[c] for c in RAMP], np.uint8)
    cv.a[bm] = rc[kk][bm]; cv.solid |= bm
    # 背脊深色「殼紋」：左後半一條弧帶（區分柔光／燦光嘅純色絨）
    # 肚
    bl = cv.ell(cx + 2, cy + ry * 0.34, rx * 0.5, ry * 0.45) & bm
    cv.a[bl & (kk <= 1)] = IDX["lumi_fur1"]
    # 毛紋
    for (a, b) in [(-0.62, 0.15), (-0.35, 0.62), (0.52, 0.45), (0.68, -0.05), (0.15, 0.78)]:
        px, py = cx + a * rx * .95, cy + b * ry * .95
        cv.put(px, py, "zzz"); cv.put(px + 1, py + 1, "zzz")
    # 高光
    hx, hy = cx - rx * 0.30, cy - ry * 0.58
    for dx, dy in ((0, 0), (1, 0), (2, 0), (-1, 1), (0, -1), (1, -1)):
        cv.put(hx + dx, hy + dy, "white")
    # --- 觸角（取代芽莖）：兩條向右前彎
    ant_tips = []
    for (bx, lean, ln) in ((cx + 1, 0.55, 10), (cx + 6, 0.85, 9)):
        y0 = cy - ry + 1.5
        last = None
        for j in range(ln + 1):
            t = j / ln
            x = bx + lean * j * 0.9 + 2.2 * t * t; y = y0 - j + 1.8 * t * t
            cv.put(x, y, "outline"); cv.solid[int(round(y)), int(round(x))] = True
            last = (x, y)
        ant_tips.append(last)
    cv.outline()
    # 尾燈分節（深帶）＋發光層次（outline 之後畫）
    seg = tail & ~bm
    for k, ox in enumerate((-0.5, 2.8)):
        cv.a[seg & (np.abs(cv.xx + .5 - (tx + ox) - (cv.yy + .5 - ty) * 0.35) < 0.6)] = IDX["outline"]
    core = cv.ell(tx - 1.6, ty + 0.4, 4.8, 4.4) & seg & (cv.a != IDX["outline"])
    cv.a[core] = IDX["fly"]
    cv.a[cv.ell(tx - 2.6, ty + 0.0, 2.4, 2.4) & seg & (cv.a != IDX["outline"])] = IDX["fly_core"]
    # 觸角燈頭
    for (x, y) in ant_tips:
        m = cv.ell(x + .4, y - .6, 2.2, 2.2)
        cv.paint(m, "fly"); cv.put(x, y - 1, "fly_core"); cv.put(x + 1, y - 1, "fly_core")
        ring = np.zeros_like(m); ring[1:] |= m[:-1]; ring[:-1] |= m[1:]; ring[:, 1:] |= m[:, :-1]; ring[:, :-1] |= m[:, 1:]
        cv.a[ring & ~m & (cv.a == 0)] = IDX["outline"]
    # 身上光點（集中背／後半，越近尾越密）
    for (dx, dy, big) in ((-13, -3, 1), (-7, -10, 1), (-15, 4, 0), (-9, 3, 0), (-2, -12, 0), (5, -11, 1), (-12, 9, 0), (12, -6, 0)):
        x, y = cx + dx, cy + dy
        if bm[int(y), int(x)]:
            cv.put(x, y, "fly_core")
            if big:
                for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)): cv.put(x + ox, y + oy, "fly")
    # --- 面（向右：整體右移 2px）
    fcx = cx + 2; ey = cy + ry * 0.08; eoff = rx * 0.38
    for sgn in (-1, 1): bt.draw_tmpl_c(cv, fcx + sgn * eoff, ey, bt.EYE[True]["open"], {"#": "outline", "w": "fly_core"})
    bt.draw_tmpl_c(cv, fcx, ey + ry * 0.38, bt.MOUTH[True]["smile"], {"#": "outline"})
    for sgn in (-1, 1):
        mb = cv.ell(fcx + sgn * rx * 0.6, ey + ry * 0.26, 2.4, 1.4)
        cv.a[mb & bm] = IDX["blush"]
    return cv.a

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
