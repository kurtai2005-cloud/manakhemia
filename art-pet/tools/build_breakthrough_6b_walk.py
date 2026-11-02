#!/usr/bin/env python3
"""6b 現實世界連動：散步美術。
- walk_bg：散步路背景（直向 100×120 art px，@3x 300×360），≤12 色、左上光、棋盤 dither（冇半透明）。
- walk_clip：49 隻形態各一條 6 幀散步 loop，由 idle 幀 0 逐粒搬位衍生（唔縮放、唔加新色），幀大小／pivot＝idle。
- deco_*：8 件散步小物 16×16（+@3x），同 v2 kit icon 一樣嘅渲染（左上三階光＋#24172C 外描＋可愛臉）。
- icon_walk：rail「散步」icon 16×16（+@3x），同 kit ic_* 規格。
純 Pillow／numpy，冇 AI 圖；alpha 只得 0／255。重跑：python3 art-pet/tools/build_breakthrough_6b_walk.py"""
import os, sys, json
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reactions_lib as L
import ui_hd2d_v2_icons as UI

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "art/breakthrough/6b")
FPS = 10
NF = 6

def save(a, path, k=1):
    im = Image.fromarray(a, "RGBA") if isinstance(a, np.ndarray) else a
    if k != 1: im = im.resize((im.width * k, im.height * k), Image.NEAREST)
    im.save(path, optimize=True)

def ncol(a):
    m = a[..., 3] == 255
    return len({tuple(c) for c in a[m][:, :3]})

# ======================================================================== walk clip
# 腳模式（有分開嘅腳）：身 bob＋左右腳交替提起／前後 1px；冇腳嘅形態（水滴／火苗等）用彈跳模式。
FEET_SEQ = [  # (bodyDy, lean, (Ldx,Ldy), (Rdx,Rdy))  — 向右行，R 係前腳
    (0, 0, (-1, 0), (1, 0)),
    (-1, 1, (0, -2), (0, 0)),
    (-1, 0, (1, -1), (-1, 0)),
    (0, 0, (1, 0), (-1, 0)),
    (-1, 1, (0, 0), (0, -2)),
    (-1, 0, (-1, 0), (1, -1)),
]
HOP_SEQ = [(0, 0), (-1, 1), (-2, 1), (-2, 0), (-1, 0), (0, 0)]  # (bodyDy, lean)

def find_feet(base, pivot):
    m = base[..., 3] == 255
    ys = np.where(m.any(1))[0]; ybot = ys.max()
    px = pivot[0]
    for k in (4, 3, 2):
        y0 = ybot - k + 1
        band = m[y0:ybot + 1]
        lab, n = ndimage.label(band, structure=np.ones((3, 3)))
        comps = []
        for i in range(1, n + 1):
            yy, xx = np.where(lab == i)
            if yy.max() < k - 2: continue                      # 要掂到底兩行
            comps.append((len(yy), xx.mean(), i))
        comps.sort(reverse=True)
        if len(comps) >= 2 and comps[1][0] >= 3:
            a, b = comps[0], comps[1]
            if (a[1] - px) * (b[1] - px) < 0:
                left, right = (a, b) if a[1] < b[1] else (b, a)
                Lm = np.zeros_like(m); Rm = np.zeros_like(m)
                Lm[y0:ybot + 1] = lab == left[2]; Rm[y0:ybot + 1] = lab == right[2]
                return Lm, Rm, y0
    return None

def shift(a, dx, dy):
    H, W = a.shape[:2]; o = np.zeros_like(a)
    xs0, xs1 = max(0, -dx), min(W, W - dx); ys0, ys1 = max(0, -dy), min(H, H - dy)
    o[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx] = a[ys0:ys1, xs0:xs1]
    return o

def over(dst, src):
    m = src[..., 3] == 255; dst[m] = src[m]

def body_frame(body, dy, lean, split):
    """lean：split 行以上（上半身）向前（右）推 1px，逐行搬位唔縮放"""
    b = shift(body, 0, dy)
    if lean:
        s = split + dy
        top = b.copy(); top[s:] = 0
        bot = b.copy(); bot[:s] = 0
        b = bot; over(b, shift(top, lean, 0))
    return b

def walk_frames(r):
    base = r.base; H, W = base.shape[:2]
    m = base[..., 3] == 255
    ys, xs = np.where(m); top = ys.min(); right = xs.max()
    split = int(round((ys.min() + ys.max()) / 2))
    maxup = top                                            # 唔可以頂出幀
    canlean = right < W - 1
    feet = find_feet(base, r.pivot)
    frames = []
    if feet:
        Lm, Rm, fy0 = feet
        footL = np.where(Lm[..., None], base, 0).astype(np.uint8)
        footR = np.where(Rm[..., None], base, 0).astype(np.uint8)
        body = base.copy(); body[Lm | Rm] = 0
        for bdy, lean, (ldx, ldy), (rdx, rdy) in FEET_SEQ:
            bdy = max(bdy, -maxup); lean = lean if canlean else 0
            f = np.zeros_like(base)
            for ft, dx, dy in ((footL, ldx, ldy), (footR, rdx, rdy)):
                over(f, shift(ft, dx, dy))
                if bdy < dy: over(f, shift(ft, dx, bdy))          # 身升咗：腳頂補一格（腳伸長），唔留罅
            over(f, body_frame(body, bdy, lean, split))
            frames.append(f)
        mode = "feet"
    else:
        for bdy, lean in HOP_SEQ:
            bdy = max(bdy, -maxup); lean = lean if canlean else 0
            frames.append(body_frame(base, bdy, lean, split))
        mode = "hop"
    return frames, mode

# ======================================================================== walk_bg
def hexc(h): h = h.lstrip("#"); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)] + [255], np.uint8)
BGP = {  # 12 色（取自 H1 palette＋v2 kit 金）
    "sky": "#a2ccec", "peach": "#fae2be", "cloud": "#FFF8EA", "hill": "#a2ac74",
    "leafD": "#334729", "leafM": "#55753c", "grassM": "#698446", "grassL": "#92b75b",
    "path": "#e0c08a", "pathS": "#a87c50", "ink": "#432c23", "flower": "#FF8FB0",
}

def build_bg():
    W, H = 100, 120
    P = {k: hexc(v) for k, v in BGP.items()}
    a = np.zeros((H, W, 4), np.uint8)
    yy, xx = np.mgrid[0:H, 0:W]
    chk = (xx + yy) % 2 == 0
    HOR = 30
    # 天空：上藍下桃，中間棋盤 dither（左上太陽暖光）
    B4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
    bay = B4[yy % 4, xx % 4]
    a[:] = P["sky"]
    tsky = np.clip((yy - 5) / 15.0, 0, 1)                 # 5→20 行：藍→桃（Bayer 4×4 dither）
    a[tsky > bay] = P["peach"]
    # 太陽暈（左上）
    d = np.hypot(xx - 31, yy - 7)
    a[d < 9] = P["peach"]; a[(d >= 9) & (d < 12) & chk] = P["peach"]
    a[d < 5] = P["cloud"]; a[(d >= 5) & (d < 6.5) & chk] = P["cloud"]
    # 雲（右上）
    for cx, cy, rx, ry in ((72, 8, 9, 3), (80, 6, 6, 3), (65, 9, 5, 2), (52, 16, 6, 2), (58, 15, 4, 2)):
        e = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1
        a[e] = P["cloud"]
        bot = e & ~np.roll(e, -1, 0); a[bot & chk] = P["peach"]
    # 遠山：兩層（sage），頂邊 dither 做空氣透視
    h1 = (HOR - 6 + 3 * np.sin(xx[0] / 9.0) + 2 * np.sin(xx[0] / 4.3 + 1)).astype(int)
    for x in range(W):
        a[h1[x]:HOR + 2, x] = P["hill"]
    # 近樹叢線
    h2 = (HOR - 1 + 2 * np.sin(xx[0] / 3.1) + np.sin(xx[0] / 1.7)).astype(int)
    for x in range(W):
        a[h2[x]:HOR + 4, x] = P["leafM"]
        a[h2[x] + 2:HOR + 4, x] = P["leafD"] if (x // 3) % 2 else P["leafM"]
    # 草地
    a[yy >= HOR + 3] = P["grassM"]
    # 草地光：左上受光（左邊＋遠處較亮），棋盤 dither 過渡
    # 左上斜照光斑（HD-2D 光束落地）：平滑亮度場＋Bayer dither，冇半透明
    lit = (W - xx) / W * 0.55 + (H - yy) / H * 0.35 + 0.12 * np.sin(xx / 7.0 + yy / 11.0) + 0.08 * np.sin(yy / 5.0 - xx / 13.0)
    tl = np.clip((lit - 0.48) / 0.22, 0, 1)
    a[(yy >= HOR + 3) & (tl > bay)] = P["grassL"]
    # 小路：S 形由底（闊 38）收窄到地平線（闊 6），透視
    path = np.zeros((H, W), bool); edgeR = np.zeros((H, W), bool)
    cxs = {}
    for y in range(HOR + 3, H):
        t = (y - (HOR + 3)) / (H - 1 - (HOR + 3))              # 0 遠 → 1 近
        w = 5 + 36 * t ** 1.3
        cx = 50 + 14 * np.sin(t * 3.2 + 0.4) * (0.4 + 0.6 * t) - 6 * t
        cxs[y] = cx
        x0, x1 = int(round(cx - w / 2)), int(round(cx + w / 2))
        path[y, max(0, x0):min(W, x1 + 1)] = True
        if 0 <= x1 < W: edgeR[y, max(0, x1 - (1 if t > .4 else 0)):x1 + 1] = True
    a[path] = P["path"]
    # 路面陰影：右邊緣同中間車轍（光左上 → 右邊暗）
    a[edgeR] = P["pathS"]
    for y in range(HOR + 3, H):
        t = (y - (HOR + 3)) / (H - 1 - (HOR + 3))
        if t > .25 and y % 2 == 0:
            for off in (-0.18, 0.12):
                x = int(round(cxs[y] + off * (5 + 36 * t ** 1.3)))
                if path[y, x] and (y // 2) % 3 != 0: a[y, x] = P["pathS"]
    # 路邊草邊：路兩邊一行深草（左邊）＋草 tuft 蓋入路
    pl = path & ~np.roll(path, 1, 1); pr = path & ~np.roll(path, -1, 1)
    a[np.roll(pl, -1, 1) & ~path & (yy > HOR + 4)] = P["grassL"]
    a[np.roll(pr, 1, 1) & ~path & (yy > HOR + 4)] = P["leafM"]
    # 路上石仔（踏腳石）：每格 1 粒，左上亮右下暗
    rng = np.random.RandomState(6)
    stones = []
    for y in (44, 54, 66, 80, 96, 112):
        t = (y - (HOR + 3)) / (H - 1 - (HOR + 3)); w = 5 + 36 * t ** 1.3
        sx = int(round(cxs[y])); rx = max(1.5, w * 0.16); ry = max(1, rx * 0.45)
        e = ((xx - sx) / rx) ** 2 + ((yy - y) / ry) ** 2 <= 1
        a[e] = P["cloud"]
        sh = e & ~np.roll(e, -1, 0) | (e & ~np.roll(e, -1, 1)); a[sh] = P["pathS"]
        stones.append([sx, y])
    # 草紋：短 tuft（ink-free，用深綠），近大遠細
    for _ in range(170):
        y = rng.randint(HOR + 4, H); x = rng.randint(0, W)
        if path[y, x]: continue
        t = (y - HOR) / (H - HOR)
        c = P["leafM"] if rng.rand() < .55 else P["leafD"]
        a[y, x] = c
        if t > .45 and y - 1 >= 0 and not path[y - 1, x]: a[y - 1, x] = c
        if t > .7 and x + 1 < W and not path[y, x + 1] and not path[y - 1, x + 1]: a[y - 1, x + 1] = P["grassL"]
    # 小花（粉＋白芯）
    for _ in range(26):
        y = rng.randint(HOR + 6, H - 1); x = rng.randint(1, W - 1)
        if path[y - 1:y + 2, x - 1:x + 2].any(): continue
        a[y, x] = P["flower"]
        if (y - HOR) / (H - HOR) > .5:
            a[y - 1, x] = P["flower"]; a[y, x - 1] = P["flower"]; a[y, x + 1] = P["flower"]; a[y + 1, x] = P["leafD"]
            a[y, x] = P["cloud"]
    # 左邊大樹（前景，裁出畫面）：樹幹＋樹冠，左上光
    tr = (xx >= 2) & (xx <= 7) & (yy >= 14) & (yy < 86)
    a[tr] = P["ink"]; a[tr & (xx <= 3)] = P["pathS"]
    a[(xx >= 0) & (xx <= 9) & (yy >= 84) & (yy <= 87) & ((xx + yy) % 3 != 0)] = P["ink"]
    for cx, cy, r_ in ((4, 8, 13), (16, 4, 9), (-2, 22, 10), (12, 17, 7)):
        c = np.hypot(xx - cx, yy - cy) <= r_
        a[c] = P["leafM"]
        hl = np.hypot(xx - cx + r_ * .35, yy - cy + r_ * .35) <= r_ * .55
        a[c & hl] = P["grassL"]
        a[c & hl & ~(np.hypot(xx - cx + r_ * .35, yy - cy + r_ * .35) <= r_ * .4) & chk] = P["leafM"]
        sh = c & ~(np.hypot(xx - cx - 1.5, yy - cy - 1.5) <= r_ - 1.5)
        a[sh & (xx - cx + yy - cy > 0)] = P["leafD"]
    # 右邊細樹叢（中景）
    for cx, cy, r_ in ((92, 40, 7), (99, 36, 6), (86, 43, 4)):
        c = np.hypot(xx - cx, (yy - cy) * 1.2) <= r_
        a[c] = P["leafM"]; a[c & (np.hypot(xx - cx + 2, yy - cy + 2) <= r_ * .5)] = P["grassL"]
        a[c & (xx - cx + yy - cy > r_ * .6)] = P["leafD"]
    # 前景草（底角，深色框住畫面，HD-2D 景深）
    for x in range(W):
        hgt = int(4 + 3 * abs(np.sin(x * 1.7)) + (3 if x < 14 or x > 88 else 0) * abs(np.sin(x / 2.3)))
        if 18 < x < 82: hgt = int(1 + abs(np.sin(x * 1.3)) * 2)
        for y in range(H - hgt, H):
            a[y, x] = P["leafD"]
        if hgt > 3: a[H - hgt, x] = P["leafM"]
    # 小木牌（右下，散步起點）：ink 柱＋path 牌面
    a[92:104, 84:86] = P["ink"]
    a[88:95, 78:93] = P["ink"]; a[89:94, 79:92] = P["path"]; a[93, 79:92] = P["pathS"]; a[89, 79:91] = P["cloud"]
    a[91, 81:90:2] = P["pathS"]
    return a, {"horizonY": HOR, "pathCenter": {str(y): round(float(c), 1) for y, c in cxs.items() if y % 4 == 0},
               "stones": stones}

# ======================================================================== deco + icon_walk
UI.MAT.setdefault("l", ("#FFD9A0", "#F28A4A", "#C24A2E"))   # 紅葉橙紅
DECO = {}
def deco(name):
    def d(fn): DECO[name] = fn; return fn
    return d

@deco("pebble")
def _(i):
    i.E(8, 9.5, 6.6, 4.8, "s"); i.E(6, 7, 2, 1, "s"); i.P([(4, 7), (5, 6)], "w"); i.face(8, 10, 3)
@deco("maple_leaf")
def _(i):
    i.PG([(8, 0.5), (9.8, 4.5), (13.5, 3), (12.3, 7), (15.5, 8), (11.5, 10.5), (12.2, 13), (8.6, 11.6),
          (7.4, 11.6), (3.8, 13), (4.5, 10.5), (0.5, 8), (3.7, 7), (2.5, 3), (6.2, 4.5)], "l")
    i.L([(8, 4), (8, 15)], "N"); i.L([(8, 8), (11, 6)], "L"); i.L([(8, 8), (5, 6)], "L")
    i.P([(7, 8), (9, 8)], "k"); i.P([(6, 9), (10, 9)], "*")
@deco("acorn")
def _(i):
    i.E(8, 10, 5, 5.2, "o"); i.E(8, 5.5, 6.2, 3.2, "n"); i.R(2, 6, 14, 7, "n")
    i.P([(4, 4), (7, 3), (10, 4), (6, 6), (9, 6), (12, 6), (3, 6)], "N"); i.R(7, 0, 8, 2, "N")
    i.face(8, 10, 3)
@deco("feather")
def _(i):
    i.PG([(14, 1), (11, 2), (6, 6), (3, 10), (3, 12), (5, 12), (9, 9), (13, 5)], "c")
    i.PG([(14, 1), (13, 5), (11, 6), (12, 2)], "b")
    i.L([(1, 15), (13, 2)], "n"); i.P([(6, 8), (9, 6)], "C")
@deco("snail_shell")
def _(i):
    i.C(8, 8.5, 6.4, "p"); i.C(8.6, 8.8, 4, "P"); i.C(8.6, 8.8, 3, "p"); i.C(9.2, 9.2, 1.6, "P"); i.P([(9, 9)], "p")
    i.P([(4, 5), (5, 4)], "w")
@deco("clover4")
def _(i):
    for cx, cy in ((5, 5), (11, 5), (5, 10), (11, 10)): i.C(cx, cy, 3.1, "g")
    i.R(7, 7, 8, 8, "g"); i.L([(9, 10), (13, 15)], "G"); i.face(8, 8, 3)
@deco("button")
def _(i):
    i.C(8, 8, 6.8, "r"); i.C(8, 8, 4.6, "R"); i.C(8, 8, 3.8, "r")
    i.P([(6, 6), (9, 6), (6, 9), (9, 9)], "K"); i.P([(4, 4), (3, 5)], "w")
@deco("ribbon")
def _(i):
    i.PG([(7, 6), (1, 2), (0.5, 9), (7, 8)], "p"); i.PG([(9, 6), (15, 2), (15.5, 9), (9, 8)], "p")
    i.PG([(7, 9), (4, 15), (6, 15), (8, 11)], "P"); i.PG([(9, 9), (12, 15), (10, 15), (8, 11)], "P")
    i.R(6, 5, 9, 9, "r", cut=1); i.P([(2, 4), (2, 5)], "w")

def icon_walk(i):
    """散步：小波鞋（向右）＋鞋帶＋動作線＋可愛臉"""
    i.R(3, 6, 9, 12, "r", cut=1); i.PG([(5, 8), (14, 9), (15, 12), (5, 12)], "r")
    i.R(2, 12, 15, 13, "c"); i.R(3, 5, 9, 6, "c")
    i.P([(6, 8), (8, 8), (7, 9)], "w")
    i.P([(0, 7), (1, 7), (0, 9), (1, 10)], "K")
    i.face(11, 10, 2)

def icon(fn):
    ic = UI.Ic(); fn(ic); return np.array(UI.render(ic))

# ======================================================================== main
def main():
    os.makedirs(OUT, exist_ok=True)
    J = {"version": 1, "batch": "breakthrough 6b 散步（現實世界連動）", "keys": {}, "pets": {}}
    bg, meta = build_bg()
    save(bg, os.path.join(OUT, "walk_bg.png")); save(bg, os.path.join(OUT, "walk_bg@3x.png"), 3)
    J["keys"]["6b:walk_bg"] = {"1x": "walk_bg.png", "3x": "walk_bg@3x.png", "size": [100, 120], "colors": ncol(bg), **meta}
    os.makedirs(os.path.join(OUT, "deco"), exist_ok=True)
    for n, fn in DECO.items():
        a = icon(fn)
        save(a, os.path.join(OUT, "deco", f"deco_{n}.png")); save(a, os.path.join(OUT, "deco", f"deco_{n}@3x.png"), 3)
        J["keys"][f"6b:deco_{n}"] = {"1x": f"deco/deco_{n}.png", "3x": f"deco/deco_{n}@3x.png", "size": [16, 16], "colors": ncol(a)}
    a = icon(icon_walk)
    save(a, os.path.join(OUT, "ic_walk@1x.png")); save(a, os.path.join(OUT, "ic_walk@3x.png"), 3)
    J["keys"]["icon_walk"] = {"1x": "ic_walk@1x.png", "3x": "ic_walk@3x.png", "size": [16, 16], "colors": ncol(a),
                              "note": "rail「散步」icon，同 kit_hd2d_v2 icons/ic_*@{1x,3x} 同規格；可放入 icons atlas"}
    modes = {}
    for pid in L.ALL_PETS:
        r = L.rig(pid); fr, mode = walk_frames(r); modes[pid] = mode
        Hh, Ww = r.base.shape[:2]
        strip = np.concatenate(fr, 1)
        d = os.path.join(OUT, "per_pet", pid); os.makedirs(d, exist_ok=True)
        save(strip, os.path.join(d, "walk.png")); save(strip, os.path.join(d, "walk@3x.png"), 3)
        J["pets"][pid] = {"frameSize": [Ww, Hh], "pivot": list(r.pivot), "frames": NF, "fps": FPS, "loop": True,
                          "mode": mode, "line": r.line, "1x": f"per_pet/{pid}/walk.png", "3x": f"per_pet/{pid}/walk@3x.png",
                          "idleColors": ncol(r.base), "walkColors": ncol(strip)}
    J["clip"] = {"key": "6b:walk_clip", "frames": NF, "fps": FPS, "durationMs": NF * 1000 // FPS, "facing": "right（向左 flipX，pivot x 鏡像：W−1−px）",
                 "layout": "橫條 strip，幀 i 喺 x＝i×frameW；幀大小＝該形態 idle 幀大小，pivot 同 idle 一樣",
                 "feetSeq": FEET_SEQ, "hopSeq": HOP_SEQ}
    json.dump(J, open(os.path.join(OUT, "walk6b.json"), "w"), ensure_ascii=False, indent=1)
    print("bg colours", ncol(bg), "modes", {m: sum(1 for v in modes.values() if v == m) for m in ("feet", "hop")})
    print("hop:", [p for p, m in modes.items() if m == "hop"])
    preview(bg)

def preview(bg):
    K = 3
    pets = ["evo_still_radiant", "radiant", "sprout", "evo_guard_tide", "A1", "B3", "C1", "F2", "H1", "D3"]
    J = json.load(open(os.path.join(OUT, "walk6b.json")))
    BGC = (44, 48, 66, 255)
    cell = 64
    W = 4 + 100 * K + 8 + NF * cell * K // 2 + 4
    rowsH = len(pets) * (cell * K // 2 + 2)
    H = max(120 * K + 8 + 16 * K * 2 + 24, rowsH) + 8
    sheet = Image.new("RGBA", (W, H), BGC)
    dr = ImageDraw.Draw(sheet)
    bgim = Image.fromarray(bg).resize((300, 360), Image.NEAREST)
    # 背景＋喺路上放一隻（幀 0）
    comp = Image.fromarray(bg.copy())
    p = J["pets"]["evo_still_radiant"]; st = Image.open(os.path.join(OUT, p["1x"]))
    fw, fh = p["frameSize"]; f0 = st.crop((fw * 1, 0, fw * 2, fh))
    stone = J["keys"]["6b:walk_bg"]["stones"][-2]
    comp.alpha_composite(f0, (stone[0] - p["pivot"][0], stone[1] - p["pivot"][1]))
    sheet.alpha_composite(comp.resize((300, 360), Image.NEAREST), (4, 4))
    # 8 deco＋icon_walk（3x）
    x = 4; y = 4 + 360 + 8
    for n in DECO:
        im = Image.open(os.path.join(OUT, "deco", f"deco_{n}@3x.png")); sheet.alpha_composite(im, (x, y)); x += 48 + 4
        if x + 48 > 304: x = 4; y += 52
    dr.rectangle([x - 2, y - 2, x + 49, y + 49], outline=(242, 182, 64, 255))
    sheet.alpha_composite(Image.open(os.path.join(OUT, "ic_walk@3x.png")), (x, y))
    # clips：每隻 6 幀，1.5x（每格 64→96 px）
    X0 = 4 + 300 + 8; ch = cell * K // 2
    for j, pid in enumerate(pets):
        p = J["pets"][pid]; st = Image.open(os.path.join(OUT, p["1x"])); fw, fh = p["frameSize"]
        for i in range(NF):
            c = Image.new("RGBA", (cell, cell), (0, 0, 0, 0))
            c.alpha_composite(st.crop((fw * i, 0, fw * (i + 1), fh)), (32 - p["pivot"][0], 60 - p["pivot"][1]))
            cx = X0 + i * ch; cy = 4 + j * (ch + 2)
            dr.rectangle([cx, cy, cx + ch - 1, cy + ch - 1], fill=(58, 64, 86, 255) if (i + j) % 2 else (52, 57, 78, 255))
            dr.line([cx, cy + 60 * ch // cell, cx + ch - 1, cy + 60 * ch // cell], fill=(90, 96, 120, 255))
            sheet.alpha_composite(c.resize((ch, ch), Image.NEAREST), (cx, cy))
    sheet.save(os.path.join(OUT, "preview_6b_3x.png"))

if __name__ == "__main__":
    main()
