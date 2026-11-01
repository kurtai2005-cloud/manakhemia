"""batch3b 進化大場面 FX、名卡、跳過提示、預兆夢泡泡。全部 alpha 0/255、≤12 色；發光由引擎加。"""
import math
import numpy as np
from PIL import Image, ImageDraw
from batch3b_paint import P, render, canvas, px, pxs, add_outline, OL, WHITE, BLUSH, limit, paste

LAV = (206, 188, 255)       # 光物件外框（淺紫，唔用深框，似光）
LAV_D = (150, 126, 220)
L0, L1, L2 = (255, 255, 250), (255, 244, 196), (248, 214, 120)   # 光繭三階
GOLD_D = (226, 170, 80)
UI_OL = (107, 86, 131)      # B2 貼紙描邊 #6B5683
CREAMUI = (255, 249, 238)

# ───────── 光點（聚光） ─────────
def motes():
    f0 = canvas(7, 7); pxs(f0, [(3, 2), (2, 3), (3, 3), (4, 3), (3, 4)], L1); px(f0, 3, 3, L0)
    f1 = canvas(7, 7); pxs(f1, [(3, 0), (3, 1), (3, 5), (3, 6), (0, 3), (1, 3), (5, 3), (6, 3)], L2); pxs(f1, [(3, 2), (2, 3), (4, 3), (3, 4)], L1); px(f1, 3, 3, L0)
    f2 = canvas(7, 7); pxs(f2, [(2, 2), (4, 2), (2, 4), (4, 4)], L2); px(f2, 3, 3, L0)
    return [f0, f1, f2]

# ───────── 光繭 ─────────
CW, CH = 64, 72; CPIV = (32, 69)
def _cocoon_base(shift=0.0, cover=1.0, weave=True, seam=0.0, split=0.0, bright=0):
    W, H = CW, CH; cx, cy, rx, ry = 32, 41.5, 22, 28
    Y, X = np.mgrid[0:H, 0:W].astype(float) + .5
    u, v = (X - cx) / rx, (Y - cy) / ry; r2 = u * u + v * v
    # 頂尖少少（似繭）
    r2 = np.where(v < 0, u * u / (1 + v * .25) ** 2 + v * v, r2)
    inside = r2 <= 1
    nz = np.sqrt(np.clip(1 - r2, 0, 1)); Lt = np.array([-.5, -.6, .62]); Lt /= np.linalg.norm(Lt)
    I = u * Lt[0] + v * Lt[1] + nz * Lt[2]
    b1 = ((Y - cy) * .9 + (X - cx) * .6 + shift) % 9
    b2 = ((Y - cy) * .9 - (X - cx) * .6 - shift * .7) % 11
    rib = (b1 < 5.2) | ((b2 < 3.2) if weave else False)
    if cover < 1:
        ylim = (CPIV[1] + 1) - cover * (H + 4)
        wave = 2.5 * np.sin(X * .45 + shift)
        rib &= Y > ylim + wave
        inside_cov = inside & (Y > ylim + wave - 1)
    else:
        inside_cov = inside
        pass
    m = inside_cov & (rib | (seam > 0))
    img = canvas(W, H)
    col = np.where((I > .62 + bright * .1)[..., None], np.array(L0), np.where((I > .2)[..., None], np.array(L1), np.array(L2)))
    img[m, :3] = col[m].astype(np.uint8); img[m, 3] = 255
    if seam > 0:   # 包實：帶與帶之間＝金色縫
        g = inside & ~rib; img[g, :3] = np.where((I[g] > .55)[:, None], np.array(L2), np.array(GOLD_D)).astype(np.uint8)
    # 帶邊界暗少少
    edge = m & ~np.roll(m, -1, 1)
    img[edge & (I < .55), :3] = GOLD_D
    return img, m, (cx, cy, rx, ry)

def cocoon_form():
    fr = []
    for i, c in enumerate([.18, .34, .5, .66, .84, 1.0]):
        img, m, _ = _cocoon_base(shift=i * 1.3, cover=c)
        fr.append(add_outline(img, LAV))
    return fr

def cocoon_pulse():
    fr = []
    for i in range(4):
        img, m, _ = _cocoon_base(shift=i * 2.25, cover=1.0, seam=1, bright=(i == 1))
        fr.append(add_outline(img, LAV))
    return fr

def _crack_path(seed=3):
    rng = np.random.default_rng(seed); pts = [(32, 41)]; up = [(32, 41)]
    x, y = 32, 41
    for k in range(9): x += rng.integers(-1, 2); y -= 2; up.append((x, y))
    x, y = 32, 41
    for k in range(10): x += rng.integers(-1, 2); y += 2; pts.append((x, y))
    return up, pts

def cocoon_crack():
    fr = []; up, dn = _crack_path()
    for i in range(4):
        img, m, _ = _cocoon_base(shift=9, cover=1.0, seam=1)
        n = [3, 6, 10, 10][i]
        path = up[:n] + dn[:n]
        if i < 3:
            for (x, y) in path:
                for dy in (0, 1): px(img, x, y + dy, WHITE)
            # 小橫裂
            if i >= 1:
                for (x, y) in path[2:n:3]: pxs(img, [(x + 1, y), (x + 2, y - 1), (x - 1, y + 1), (x - 2, y + 1)], WHITE)
            fr.append(add_outline(img, LAV))
        else:  # 分開兩邊
            o = canvas(CW, CH)
            xs_split = np.array([p[0] for p in sorted(path, key=lambda p: p[1])]); Y = np.arange(CH)
            for y in range(CH):
                # 搵最近 y 嘅裂位 x
                cand = [p for p in path if abs(p[1] - y) <= 1]
                sx = cand[0][0] if cand else 32
                for x in range(CW):
                    if img[y, x, 3] == 255:
                        nx = x - 4 if x < sx else x + 4
                        if 0 <= nx < CW: o[y, nx] = img[y, x]
            # 中間白芯
            for y in range(18, 66):
                for x in range(29, 36):
                    if (x - 32) ** 2 / 9 + (y - 42) ** 2 / 560 <= 1: px(o, x, y, WHITE)
            fr.append(add_outline(o, LAV))
    return fr

def shards():
    out = []
    for g in ([".##", "###", "##."], ["##.", "###", ".#.", ".#."], [".#..", "####", "..##"]):
        h = len(g); w = max(len(r) for r in g); a = canvas(w + 2, h + 2)
        for j, r in enumerate(g):
            for i, ch in enumerate(r):
                if ch == "#": px(a, i + 1, j + 1, L1 if (i + j) % 3 else L0)
        out.append(add_outline(a, LAV))
    W = max(a.shape[1] for a in out); H = max(a.shape[0] for a in out); fr = []
    for a in out:
        c = canvas(W, H); paste(c, a, 0, 0); fr.append(c)
    return fr

# ───────── 爆光（光線＋光圈＋彩紙） ─────────
def rays():
    S = 112; c = S / 2; fr = []
    for i, (L, wd, rot) in enumerate([(18, 3, 0), (34, 4, 5), (48, 5, 10), (54, 4, 15), (50, 3, 20), (38, 2, 25)]):
        im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        for k in range(8):
            a = math.radians(rot + k * 45); ln = L * (1 if k % 2 == 0 else .62)
            pa = (c + math.cos(a) * 9, c + math.sin(a) * 9); pb = (c + math.cos(a) * ln, c + math.sin(a) * ln)
            n = (-math.sin(a) * wd / 2, math.cos(a) * wd / 2)
            d.polygon([(pa[0] + n[0], pa[1] + n[1]), (pb[0], pb[1]), (pa[0] - n[0], pa[1] - n[1])], fill=L1 + (255,))
            d.line([pa, ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)], fill=L0 + (255,), width=1)
        a = np.array(im); a[..., 3] = np.where(a[..., 3] > 127, 255, 0); a[a[..., 3] == 0] = 0
        fr.append(add_outline(a, LAV) if i < 5 else a)
    return fr

def ring():
    S = 96; c = S / 2 - .5; fr = []
    for r, t in [(8, 3), (16, 3), (26, 2), (36, 2), (44, 1)]:
        Y, X = np.mgrid[0:S, 0:S]; d = np.hypot(X - c, Y - c); a = canvas(S, S)
        m = (d >= r - t / 2) & (d <= r + t / 2); a[m] = (*L1, 255); a[(d >= r - .6) & (d <= r + .6)] = (*L0, 255)
        a[(d > r + t / 2) & (d <= r + t / 2 + 1)] = (*LAV, 255)
        fr.append(a)
    return fr

def confetti():
    shapes = {"star": ["..#..", ".###.", "#####", ".#.#."], "heart": [".#.#.", "#####", ".###.", "..#.."],
              "diamond": ["..#..", ".###.", "#####", ".###.", "..#.."], "dot": [".##.", "####", "####", ".##."]}
    cols = {"star": ((255, 236, 140), (240, 196, 80)), "heart": ((255, 170, 196), (236, 110, 150)),
            "diamond": ((190, 230, 255), (120, 180, 240)), "dot": ((214, 196, 255), (160, 136, 230))}
    fr = []
    for k, g in shapes.items():
        for flip in (0, 1):
            a = canvas(7, 7); hi, sh = cols[k]
            for j, r in enumerate(g):
                for i, ch in enumerate(r):
                    if ch == "#": px(a, i + 1, j + 1, hi if (j < 2) ^ flip else sh)
            if flip: a = np.ascontiguousarray(a[::-1]) if k != "dot" else a
            fr.append(a)
    return fr, list(shapes)

# ───────── 跳過提示（細手指 tap） ─────────
def skip_hint():
    """肉球 tap 印（B2 爪仔 doodle）：幀0 提起、幀1 按落＋閃"""
    fr = []; PAD = ((255, 250, 244), (255, 214, 226), (236, 160, 186))
    for i in range(2):
        parts = [P("ell", (7.5, 10 + i * .5, 4.2, 3.4 - i * .4), PAD, z=1)]
        for (x, y) in ((3.2, 5.2), (6.2, 3.6), (9.2, 3.6), (12, 5.4)):
            parts.append(P("ell", (x + (x - 7.5) * .08 * i, y + i, 1.6, 1.7), PAD, z=1, line=False))
        b, _ = render(parts, 15, 15, outline=UI_OL)
        if i == 1:
            for (x, y) in [(2, 3), (1, 2), (12, 3), (13, 2), (7, 0)]: px(b, x, y, (255, 214, 92))
        fr.append(b)
    return fr

# ───────── 預兆：怪夢泡泡＋6 個怪夢 ─────────
def dream_bubble():
    W, H = 34, 34; fr = []
    for k in range(3):
        a = canvas(W, H)
        pts = [(3, 31, 1.6)] + ([(7, 26, 2.4)] if k >= 1 else []) + ([(19, 13, 13.5)] if k >= 2 else [])
        parts = []
        for (x, y, r) in pts:
            if r > 10:
                for (dx, dy, rr) in [(0, 0, r), (-8, 2, 6.5), (8, 3, 6.5), (-3, -7, 7), (5, -6, 7)]:
                    parts.append(P("ell", (x + dx, y + dy, rr, rr * .78), ((255, 255, 255), (246, 240, 255), (222, 210, 250)), z=1, line=False))
            else: parts.append(P("ell", (x, y, r, r), ((255, 255, 255), (246, 240, 255), (222, 210, 250)), z=1, line=False))
        b, _ = render(parts, W, H, outline=LAV_D)
        fr.append(b)
    return fr, (19, 13)   # 夢內容中心

DREAM_ICONS = ["square_sun", "fish_hat", "flying_shoe", "walking_teacup", "upside_moon", "cake_mountain"]
def dream_icons():
    G = {
        "square_sun": (["#.#.#.#", ".#####.", "##ooo##", ".#ooo#.", "##ooo##", ".#####.", "#.#.#.#"], {"#": (248, 196, 70), "o": (255, 236, 150)}),
        "fish_hat": (["...kk.....", "..kkkk....", ".kkkkkk...", "..bbbbb..#", ".bbbbbbb##", "bebbbbbbb#", ".bbbbbbb##", "..bbbbb..#"], {"k": (70, 70, 110), "b": (130, 190, 240), "e": (40, 26, 52), "#": (100, 160, 220)}),
        "flying_shoe": (["w.......", "ww......", "wwwrr...", ".wrrrrr.", "..rrrrrr", "..dddddd"], {"w": (255, 255, 255), "r": (236, 104, 96), "d": (150, 100, 70)}),
        "walking_teacup": (["..s.s...", ".......", "cccccc..", "cppppcc.", "cccccc.c", ".cccccc.", "..d..d..", ".d....d."], {"c": (255, 246, 228), "p": (196, 140, 96), "s": (220, 220, 240), "d": (150, 100, 70)}),
        "upside_moon": (["yyyyyyy", "yyyyyyy", ".yy.yy.", "..y.y..", "........", ".z..z.."], {"y": (255, 226, 120), "z": (170, 150, 230)}),
        "cake_mountain": (["...c...", "..pcp..", ".ppppp.", ".wwwww.", "ppppppp", "wwwwwww", "bbbbbbb"], {"c": (236, 104, 96), "p": (255, 180, 200), "w": (255, 250, 240), "b": (200, 150, 110)}),
    }
    out = {}
    for k, (g, cm) in G.items():
        h = len(g); w = max(len(r) for r in g); a = canvas(w + 2, h + 2)
        for j, r in enumerate(g):
            for i, ch in enumerate(r):
                if ch in cm: px(a, i + 1, j + 1, cm[ch])
        if k == "upside_moon": pass
        out[k] = add_outline(a, OL)
    W = max(a.shape[1] for a in out.values()); H = max(a.shape[0] for a in out.values())
    res = {}
    for k, a in out.items():
        c = canvas(W, H); paste(c, a, (W - a.shape[1]) // 2, (H - a.shape[0]) // 2); res[k] = c
    return res

# ───────── 名卡 ─────────
ROUTES = ["tide", "moon", "shroom", "crystal", "ember", "radiant", "soft", "dust", "lumi"]
ROUTE_COL = {   # (淺, 中, 深)
    "base": ((255, 230, 200), (246, 186, 140), (206, 136, 104)),
    "tide": ((206, 236, 255), (110, 180, 236), (64, 124, 196)),
    "moon": ((222, 214, 255), (140, 128, 214), (90, 78, 166)),
    "shroom": ((255, 214, 226), (226, 120, 150), (170, 70, 110)),
    "crystal": ((214, 248, 250), (120, 210, 222), (78, 150, 186)),
    "ember": ((255, 222, 190), (246, 140, 80), (196, 82, 60)),
    "radiant": ((255, 244, 190), (250, 204, 80), (206, 146, 50)),
    "soft": ((255, 226, 236), (246, 160, 196), (206, 110, 154)),
    "dust": ((236, 232, 244), (178, 170, 198), (126, 118, 150)),
    "lumi": ((236, 252, 200), (170, 220, 110), (104, 164, 80)),
}
CARD_W, CARD_H = 168, 64
CARD_PORTRAIT = {"cx": 33, "cy": 32, "r": 25, "petPivot": [33, 54]}
CARD_TEXT = {"name": [66, 9, 158, 25], "line": [66, 31, 158, 55]}
def _rrect(W, H, x0, y0, x1, y1, r):
    im = Image.new("L", (W, H), 0); ImageDraw.Draw(im).rounded_rectangle([x0, y0, x1, y1], r, fill=1); return np.array(im) > 0
def name_card(route, token_img=None):
    W, H = CARD_W, CARD_H; lt, md, dk = ROUTE_COL[route]
    a = canvas(W, H)
    outer = _rrect(W, H, 0, 2, W - 1, H - 1, 10); white = _rrect(W, H, 1, 3, W - 2, H - 2, 9); inner = _rrect(W, H, 3, 5, W - 4, H - 4, 7)
    a[outer] = (*UI_OL, 255); a[white] = (*WHITE, 255); a[inner] = (*CREAMUI, 255)
    # 斜紋底（淺色）
    Y, X = np.mgrid[0:H, 0:W]
    st = inner & (((X + Y) // 4) % 4 == 0) & (X > 60)
    a[st] = (*lt, 255)
    # 頭像窗
    c = CARD_PORTRAIT; d = np.hypot(X - c["cx"] + .5, Y - c["cy"] + .5)
    a[d <= c["r"] + 1.5] = (*UI_OL, 255); a[d <= c["r"] + .5] = (*WHITE, 255); a[d <= c["r"] - 1.5] = (*md, 255); a[d <= c["r"] - 3] = (*lt, 255)
    dots = (d <= c["r"] - 3) & (((X // 3) + (Y // 3)) % 3 == 0) & ((X % 3) == 1) & ((Y % 3) == 1)
    a[dots] = (*WHITE, 255)
    # 名牌（彩帶）
    x0, y0, x1, y1 = CARD_TEXT["name"]
    rb = _rrect(W, H, x0 - 2, y0 - 1, x1 + 2, y1 + 1, 4); a[rb] = (*dk, 255)
    rb2 = _rrect(W, H, x0 - 1, y0, x1 + 1, y1, 3); a[rb2] = (*md, 255)
    a[y0 + 1, x0 + 1:x1] = (*lt, 255)
    for (tx, sgn) in ((x0 - 2, -1), (x1 + 2, 1)):     # 彩帶尾
        for k in range(4):
            for j in range(y0 + 3 + k // 2, y1 - k // 2 + 1): px(a, tx + sgn * (k + 1), j, dk)
    # 介紹行（虛線）
    lx0, ly0, lx1, ly1 = CARD_TEXT["line"]
    for yy in (ly0 + 10, ly1):
        for xx in range(lx0, lx1, 3): px(a, xx, yy, lt); px(a, xx + 1, yy, lt)
    # 角落閃閃
    for (sx, sy) in ((W - 9, 4), (62, H - 8)):
        pxs(a, [(sx, sy - 2), (sx, sy - 1), (sx - 2, sy), (sx - 1, sy), (sx + 1, sy), (sx + 2, sy), (sx, sy + 1), (sx, sy + 2)], (255, 214, 92)); px(a, sx, sy, WHITE)
    if token_img is not None:
        paste(a, token_img, W - 6 - token_img.shape[1], H - 6 - token_img.shape[0])
    return a
