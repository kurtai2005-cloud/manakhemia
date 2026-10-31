#!/usr/bin/env python3
"""build_systems12_b1_ui.py — systems12 第 1 批：天氣疊層／四季 LUT／UI 素材（由 build_systems12_b1.py ui|docs|preview 調用）。
Pillow + numpy 程式逐像素繪製，原創，無 AI。
- UI：v3 色盤（motion/palette.json 31 色）、alpha 0/255、無 AA → ui/systems12/
- 天氣（陰／霧）：H3 預烘層（同 rain 做法：H3/overcast/*、H3/fog/*＋grade_*.json＋lut）＋可疊任何時段嘅雲帶／霧帶 tile（scenes/hd2d/weather/）
- 四季：scenes/hd2d/seasons/<season>/H#/{sky,far,mid,fore,lightmap}.png＋lut.png＋grade.json（香港月份：春 3–5、夏 6–8、秋 9–11、冬 12–2）
"""
import json, os, sys, math, glob
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_tuanrong as bt
from build_tuanrong import IDX
import build_hd2d_scenes as B
ROOT = os.path.normpath(os.path.join(HERE, ".."))
UI = os.path.join(ROOT, "ui", "systems12"); SCN = B.OUT
WXD = os.path.join(SCN, "weather"); SEA = os.path.join(SCN, "seasons")
PREV = os.path.join(ROOT, "sprites", "tuanrong", "preview", "systems12")
MOT = os.path.join(ROOT, "sprites", "tuanrong", "motion"); LV = os.path.join(MOT, "liveliness")
PAL = json.load(open(os.path.join(MOT, "palette.json")))
RGB = [(0, 0, 0)] + [tuple(int(c["hex"][i:i + 2], 16) for i in (1, 3, 5)) for c in PAL["colors"]]
NAMES = [c["name"] for c in PAL["colors"]]
assert all(IDX[n] == i + 1 for i, n in enumerate(NAMES))

def to_img(a):
    o = np.zeros(a.shape + (4,), np.uint8)
    for i, c in enumerate(RGB):
        if i: o[a == i, :3] = c; o[a == i, 3] = 255
    return Image.fromarray(o, "RGBA")

class Ic:
    def __init__(s, w, h=None):
        s.w, s.h = w, h or w; s.im = Image.new("L", (s.w, s.h), 0); s.d = ImageDraw.Draw(s.im)
    def c(s, col): return IDX[col] if isinstance(col, str) else col
    def ell(s, x0, y0, x1, y1, col): s.d.ellipse([x0, y0, x1, y1], fill=s.c(col))
    def rect(s, x0, y0, x1, y1, col): s.d.rectangle([x0, y0, x1, y1], fill=s.c(col))
    def rrect(s, x0, y0, x1, y1, r, col): s.d.rounded_rectangle([x0, y0, x1, y1], r, fill=s.c(col))
    def poly(s, pts, col): s.d.polygon(pts, fill=s.c(col))
    def line(s, pts, col, w=1): s.d.line(pts, fill=s.c(col), width=w)
    def px(s, x, y, col):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < s.w and 0 <= y < s.h: s.im.putpixel((x, y), s.c(col))
    def arr(s): return np.array(s.im, np.uint8)
    def put(s, a): s.im = Image.fromarray(a.astype(np.uint8), "L"); s.d = ImageDraw.Draw(s.im)

def ring(m):
    d = np.zeros_like(m); d[1:] |= m[:-1]; d[:-1] |= m[1:]; d[:, 1:] |= m[:, :-1]; d[:, :-1] |= m[:, 1:]
    return d & ~m
def outline(a, col="outline"):
    o = a.copy(); o[ring(a != 0)] = IDX[col]; return o
def sticker(a):
    """貼紙：白色 die-cut 邊（1px）＋外描邊"""
    o = a.copy(); r1 = ring(o != 0); o[r1] = IDX["white"]; r2 = ring(o != 0); o[r2] = IDX["outline"]; return o
def paint(a, mask, col): a[mask & (a != 0)] = IDX[col]

def poly_mask(n, pts, ss=1.0):
    yy, xx = np.mgrid[:n, :n].astype(float) + .5; m = np.zeros((n, n), bool); P = np.array(pts, float); k = len(P)
    j = k - 1
    for i in range(k):
        xi, yi = P[i]; xj, yj = P[j]
        cond = ((yi > yy) != (yj > yy)) & (xx < (xj - xi) * (yy - yi) / (yj - yi + 1e-12) + xi)
        m ^= cond; j = i
    return m

# ============================================================ icons
def star_shard(n):
    """星星碎：胖五角星，左上亮右下暗，右下崩咗一角（碎），金色描邊"""
    c = (n - 1) / 2; R = n * 0.47; r = R * 0.50
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5; rr = R if i % 2 == 0 else r
        pts.append((c + .5 + rr * math.cos(ang), c + .5 + n * 0.03 + rr * math.sin(ang)))
    # 崩角：右下角尖削走一截
    bx, by = pts[4]; cx_, cy_ = pts[3]; pts[4] = (bx + (cx_ - bx) * 0.28, by + (cy_ - by) * 0.28 - n * 0.02)
    m = poly_mask(n, pts)
    # 縮一圈畫描邊（描邊喺形狀入面，唔出界）
    a = np.zeros((n, n), np.uint8); a[m] = IDX["glow_mid"]
    edge = m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))
    yy, xx = np.mgrid[:n, :n].astype(float)
    side = (xx - c) * 0.6 + (yy - c) * 0.8      # >0 右下（暗）
    a[m & (side > n * 0.08)] = IDX["glow"]
    a[m & (side > n * 0.26)] = IDX["egg_shade"]
    a[m & (side < -n * 0.10)] = IDX["glow_core"]
    a[edge] = IDX["egg_dark"]
    # 中間刻面線（由中心去上尖）
    for t in np.linspace(0, 1, n * 2):
        x = c + (pts[0][0] - .5 - c) * t * 0.75; y = c + n * 0.06 + (pts[0][1] - .5 - c - n * 0.06) * t * 0.75
        xi, yi = int(round(x)), int(round(y))
        if m[yi, xi] and not edge[yi, xi]: a[yi, xi] = IDX["glow_core"] if n < 24 else IDX["cream4"]
    if n >= 24:   # 32px：高光＋碎粒＋閃點
        a[int(c - n * .12), int(c - n * .16)] = IDX["white"]; a[int(c - n * .12) + 1, int(c - n * .16)] = IDX["white"]
    o = outline(a)
    if n >= 24:
        for (x, y) in ((int(n * .84), int(n * .80)), (int(n * .90), int(n * .70))):
            if o[y, x] == 0: o[y, x] = IDX["glow_mid"]
        x, y = int(n * .86), int(n * .74)
        if o[y, x] == 0: o[y, x] = IDX["egg_dark"]
    return o

def icon_feed():
    o = Ic(16)
    o.poly([(1, 8), (14, 8), (12, 13), (3, 13)], "orange"); o.poly([(9, 8), (14, 8), (12, 13), (9, 13)], "orange_d")
    o.rect(5, 13, 10, 14, "orange_dd")
    o.ell(1, 6, 14, 9, "cream3"); o.ell(3, 7, 12, 9, "cream2")
    o.rect(2, 10, 12, 10, "cream3")   # 碗身條紋
    o.ell(5, 2, 10, 7, "berry"); o.ell(8, 4, 10, 7, "berry_d"); o.px(6, 3, "white"); o.px(7, 3, "cream4")
    o.px(8, 2, "leaf"); o.px(9, 2, "leaf"); o.px(9, 1, "leaf_d"); o.px(7, 2, "leaf_d")
    return outline(o.arr())

def icon_water():
    o = Ic(16)
    o.rrect(3, 6, 10, 13, 1, "drop"); o.rect(8, 6, 10, 13, "drop_d")
    o.rect(4, 5, 9, 5, "drop_d"); o.rect(5, 4, 8, 4, "drop")
    o.line([(10, 9), (13, 5)], "drop_d", 2); o.px(14, 4, "drop_d"); o.px(14, 5, "drop")
    o.line([(3, 7), (1, 7), (1, 11), (3, 11)], "drop_d")
    o.rect(4, 7, 4, 11, "white"); o.px(5, 7, "white")
    a = outline(o.arr())
    for x, y, c in ((14, 7, "drop"), (13, 9, "drop"), (14, 11, "drop_d")):
        if a[y, x] == 0: a[y, x] = IDX[c]
    return a

def icon_play():
    o = Ic(16)
    o.ell(2, 2, 13, 13, "blush"); o.ell(6, 6, 13, 13, "blush_d"); o.ell(3, 3, 11, 11, "blush")
    o.rect(2, 7, 13, 8, "white"); o.rect(7, 7, 13, 8, "cream2")
    o.line([(7, 2), (7, 13)], "berry", 1)
    o.px(4, 4, "cream4"); o.px(5, 4, "cream4"); o.px(4, 5, "cream4")
    a = outline(o.arr())
    return a

def icon_remind_water():
    o = Ic(16)
    o.poly([(3, 7), (12, 7), (11, 14), (4, 14)], "white"); o.poly([(4, 10), (11, 10), (11, 14), (4, 14)], "drop")
    o.rect(9, 10, 11, 14, "drop_d"); o.rect(4, 9, 11, 9, "cream4")
    o.px(5, 11, "white"); o.px(5, 12, "white")
    # 水滴（上面）
    o.poly([(8, 1), (10, 3), (6, 3)], "drop"); o.ell(6, 2, 10, 6, "drop"); o.px(9, 4, "drop_d"); o.px(9, 5, "drop_d"); o.px(7, 3, "white")
    return outline(o.arr())

def icon_remind_sleep():
    o = Ic(16)
    o.ell(1, 2, 12, 14, "glow_mid")
    a = o.arr(); cut = Ic(16); cut.ell(5, 0, 15, 11, 1); a[cut.arr() > 0] = 0; o.put(a)
    a = o.arr(); yy, xx = np.mgrid[:16, :16]
    a[(a != 0) & (xx + yy > 15)] = IDX["glow"]; a[(a != 0) & (xx + yy > 19)] = IDX["egg_shade"]
    a[(a != 0) & (xx < 4) & (yy < 9)] = IDX["glow_core"]
    a = outline(a)
    for (x, y) in ((11, 1), (12, 1), (13, 1), (12, 2), (11, 3), (12, 3), (13, 3)):  # z
        a[y, x] = IDX["zzz"]
    for (x, y) in ((13, 6), (14, 6), (13, 7), (14, 7)):
        if a[y, x] == 0: a[y, x] = IDX["zzz"] if (x + y) % 2 else IDX["white"]
    return a

# ---- stickers 24×24 (日記貼紙)
def st_sun():
    o = Ic(24); c = 11.5
    for i in range(8):
        ang = i * math.pi / 4; x1, y1 = c + 9 * math.cos(ang), c + 9 * math.sin(ang); x0, y0 = c + 6 * math.cos(ang), c + 6 * math.sin(ang)
        o.line([(x0, y0), (x1, y1)], "glow" if i % 2 else "orange", 2)
    o.ell(5, 5, 18, 18, "glow_mid"); o.ell(9, 9, 18, 18, "glow"); o.ell(6, 6, 14, 14, "glow_mid"); o.px(8, 8, "glow_core"); o.px(9, 8, "glow_core"); o.px(8, 9, "glow_core")
    o.px(9, 12, "outline"); o.px(14, 12, "outline"); o.rect(10, 14, 13, 14, "orange_d"); o.px(8, 13, "blush"); o.px(15, 13, "blush")
    return sticker(_pad(o.arr(), 24))

def _pad(a, n):
    """把內容縮入 n×n 中間，留 2px 俾貼紙邊"""
    ys, xs = np.nonzero(a)
    if not len(ys): return a
    sub = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]; h, w = sub.shape
    assert h <= n - 4 and w <= n - 4, (h, w)
    o = np.zeros((n, n), np.uint8); y0 = (n - h) // 2; x0 = (n - w) // 2; o[y0:y0 + h, x0:x0 + w] = sub; return o

def st_rain():
    o = Ic(24)
    o.ell(2, 6, 10, 13, "white"); o.ell(6, 2, 16, 11, "white"); o.ell(11, 5, 19, 13, "white"); o.rrect(3, 8, 18, 13, 3, "white")
    o.ell(12, 8, 19, 13, "cream2"); o.rect(5, 12, 17, 13, "cream2"); o.ell(11, 5, 18, 11, "white")
    o.px(8, 4, "cream4"); o.px(9, 3, "cream4"); o.px(7, 5, "cream4")
    for x, y in ((6, 16), (11, 17), (16, 16)):
        o.px(x + 1, y, "white"); o.px(x, y + 1, "drop"); o.px(x, y + 2, "drop"); o.px(x - 1, y + 3, "drop_d")
    return sticker(_pad(o.arr(), 24))

def st_food():
    o = Ic(24)
    # 飯糰＋紫菜
    o.poly([(10, 2), (18, 14), (16, 18), (4, 18), (2, 14)], "white"); o.ell(2, 10, 18, 19, "white")
    o.rect(6, 13, 14, 19, "outline"); o.rect(7, 14, 13, 19, "leaf_d")
    o.px(8, 7, "outline"); o.px(12, 7, "outline"); o.px(6, 9, "blush"); o.px(14, 9, "blush"); o.px(10, 9, "berry_d")
    o.px(7, 4, "cream4"); o.px(8, 3, "cream4")
    a = o.arr(); a[(a == IDX["white"]) & (np.mgrid[:24, :24][1] > 13) & (np.mgrid[:24, :24][0] < 13)] = IDX["cream2"]
    return sticker(_pad(a, 24))

def st_heart():
    o = Ic(24)
    o.ell(2, 3, 11, 12, "blush"); o.ell(9, 3, 18, 12, "blush"); o.poly([(2, 9), (18, 9), (10, 18)], "blush")
    a = o.arr(); yy, xx = np.mgrid[:24, :24]
    a[(a != 0) & (xx + yy > 22)] = IDX["blush_d"]
    o.put(a); o.px(5, 5, "white"); o.px(6, 5, "white"); o.px(5, 6, "white"); o.px(13, 5, "cream4")
    return sticker(_pad(o.arr(), 24))

def st_evolve():
    o = Ic(24)
    a = np.zeros((24, 24), np.uint8)
    s = star_shard(16); a[3:19, 3:19][s != 0] = s[s != 0]
    o.put(a)
    for (x, y, r) in ((19, 4, 2), (4, 18, 1), (19, 17, 1)):
        o.px(x, y, "glow_core")
        for k in range(1, r + 1):
            for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)): o.px(x + dx, y + dy, "glow_mid")
    o.px(20, 20, "cyan"); o.px(2, 6, "cyan")
    return sticker(_pad(o.arr(), 24))

def st_sleep():
    o = Ic(24)
    o.ell(2, 3, 17, 18, "zzz"); cut = Ic(24); cut.ell(7, 0, 22, 14, 1)
    a = o.arr(); a[cut.arr() > 0] = 0
    yy, xx = np.mgrid[:24, :24]; a[(a != 0) & (xx + yy > 20)] = IDX["outline"] * 0 + IDX["zzz"]
    a[(a != 0) & (xx < 6) & (yy < 12)] = IDX["white"]
    o.put(a)
    for (x, y) in ((14, 3), (15, 3), (16, 3), (15, 4), (14, 5), (15, 5), (16, 5)): o.px(x, y, "glow_mid")
    for (x, y) in ((18, 8), (19, 8), (19, 9), (18, 10), (19, 10)): o.px(x, y, "glow_mid")
    o.px(9, 13, "outline"); o.px(10, 14, "outline"); o.px(11, 14, "outline")   # 瞓覺眼（合埋）
    return sticker(_pad(o.arr(), 24))

# ---- frames (9-slice)
def nine_meta(w, h, l, t, r, b, note):
    return {"size": [w, h], "slice": {"left": l, "top": t, "right": r, "bottom": b}, "center": "tile", "edges": "tile", "note": note}

def panel_commission():
    W = H = 48; o = Ic(W, H)
    o.rrect(0, 0, W - 1, H - 1, 6, "outline"); o.rrect(1, 1, W - 2, H - 2, 5, "cream3")
    o.rect(2, H - 4, W - 3, H - 3, "cream2"); o.px(2, H - 4, "cream3"); o.px(W - 3, H - 4, "cream3")
    # 頭帶（葉綠）
    a = o.arr(); hdr = Ic(W, H); hdr.rrect(1, 1, W - 2, 12, 5, 1); m = hdr.arr() > 0
    a[m & (a == IDX["cream3"])] = IDX["leaf"]; a[3, 5:W - 5] = np.where(a[3, 5:W - 5] == IDX["leaf"], IDX["cream4"], a[3, 5:W - 5]) * 0 + a[3, 5:W - 5]
    a[12, 1:W - 1] = np.where(a[12, 1:W - 1] != IDX["outline"], IDX["leaf_d"], a[12, 1:W - 1])
    a[2, 6:W - 6] = IDX["cream4"] * (a[2, 6:W - 6] == IDX["leaf"]) + a[2, 6:W - 6] * (a[2, 6:W - 6] != IDX["leaf"])
    # 縫線（虛線，週期 4 → tile 得）
    for x in range(4, W - 4):
        if x % 4 < 2: a[H - 6, x] = IDX["cream1"]
    # 四角釘
    for (x, y) in ((4, 16), (W - 5, 16), (4, H - 9), (W - 5, H - 9)): a[y, x] = IDX["cream1"]
    return a, nine_meta(W, H, 12, 18, 12, 12, "每日委託面板：頭帶 13px（top slice 18 包埋上面兩粒釘）（標題「每日小委託」由引擎寫字，leaf 底 cream4 字）；中間 tile；建議 179×96 放 3 行")

def row_slot():
    W, H = 24, 20; o = Ic(W, H)
    o.rrect(0, 0, W - 1, H - 1, 3, "cream1"); o.rrect(1, 1, W - 2, H - 2, 2, "cream4"); o.rect(2, H - 3, W - 3, H - 3, "cream2")
    return o.arr(), nine_meta(W, H, 6, 6, 6, 6, "委託一行底（icon 16 喺左 x=4、文字、右邊 checkbox＋星星碎 ×5）")

def checkbox(done):
    o = Ic(12); o.rrect(0, 0, 11, 11, 2, "outline"); o.rrect(1, 1, 10, 10, 1, "cream4"); o.rect(2, 9, 9, 9, "cream2")
    if done:
        o.rrect(1, 1, 10, 10, 1, "leaf"); o.rect(2, 9, 9, 9, "leaf_d")
        for (x, y) in ((3, 6), (4, 7), (5, 8), (6, 7), (7, 6), (8, 5), (9, 4), (4, 6), (5, 7), (8, 4)): o.px(x, y, "white")
    return o.arr()

def bubble_frame():
    W = H = 32; o = Ic(W, H)
    o.rrect(2, 3, W - 3, H - 4, 5, "white")
    yy, xx = np.mgrid[:H, :W].astype(float) + .5; m = np.array(o.im) > 0
    for (cx, cy, r) in ((4.5, 9.5, 4.2), (9.5, 4.5, 4.2), (W - 4.5, 9.5, 4.2), (W - 9.5, 4.5, 4.2),
                        (4.5, H - 10.5, 4.2), (9.5, H - 5.5, 4.2), (W - 4.5, H - 10.5, 4.2), (W - 9.5, H - 5.5, 4.2)):
        m |= (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r
    m[:, 0] = m[:, -1] = False; m[0, :] = m[-1, :] = False
    a = np.where(m, IDX["white"], 0).astype(np.uint8)
    bot = m & ~np.roll(m, -1, 0); a[bot] = IDX["cream4"]; a[np.roll(bot, -1, 0) & m & (yy[..., ] > H / 2)] = IDX["cream4"]
    a[(xx > W - 3.5) & m] = IDX["cream4"]
    a = outline(a)
    return a, nine_meta(W, H, 11, 11, 11, 11, "心聲泡：四角雲朵（角 11px）、直邊；中間 tile；字用 outline 色；尾巴 bubble_tail（右下出，指去團絨頭）")

def bubble_tail():
    o = Ic(14, 12)
    o.ell(6, 0, 12, 5, "white"); o.ell(2, 5, 6, 9, "white"); o.ell(0, 9, 2, 11, "white")
    a = o.arr(); a[(a != 0) & (np.mgrid[:12, :14][0] >= 4) & (np.mgrid[:12, :14][0] == 4)] = a[(a != 0) & (np.mgrid[:12, :14][0] == 4)]
    # 先描邊再縮回（尾巴要有 1px 透明邊界 → 畫喺 16×14）
    b = np.zeros((14, 16), np.uint8); b[1:13, 1:15] = a
    return outline(b)

def diary_page(special=False):
    W = H = 64; o = Ic(W, H)
    o.rect(0, 0, W - 1, H - 1, "outline"); o.rect(1, 1, W - 2, H - 2, "cream4")
    a = o.arr()
    a[H - 3:H - 1, 1:W - 1] = IDX["cream2"]; a[1:H - 1, W - 3:W - 1] = IDX["cream2"]
    a[H - 2, W - 2] = IDX["cream1"]
    # 橫線（每 8px，中間 tile 32 = 4 條）
    for y in range(16, H - 8, 8): a[y, 18:W - 4] = IDX["cream2"]
    # 左邊紅 margin 線（直）
    a[1:H - 3, 15] = IDX["blush"]
    # 釘裝孔＋環（每 8px）
    for y in range(4, H - 3, 8):
        a[y:y + 2, 5:7] = IDX["outline"]; a[y - 1, 3:8] = IDX["cream1"] if False else a[y - 1, 3:8]
        a[y, 1:5] = IDX["white"]; a[y + 1, 1:5] = IDX["cream2"]
    # 右上摺角（只喺角 slice）
    for k in range(7):
        for j in range(7 - k): a[1 + k, W - 2 - j] = 0 if j < 7 - k - 1 else IDX["outline"]
    for k in range(6):
        for j in range(k + 1): a[1 + 6 - k + j - j, W - 8 + j] = a[1 + 6 - k + j - j, W - 8 + j]
    for k in range(1, 7):
        a[k, W - 8 + k - 1] = IDX["outline"]; a[7, W - 8 + k] = IDX["outline"] if k < 7 else a[7, W - 8 + k]
        for j in range(k - 1): a[k, W - 8 + j] = IDX["cream2"]
    if special:   # 進化／化光特別頁：金邊＋四角星
        a[1, 1:W - 9] = IDX["glow"]; a[1:H - 1, 1] = np.where(a[1:H - 1, 1] == IDX["white"], IDX["white"], IDX["glow"])
        a[H - 2, 1:W - 1] = IDX["glow"]; a[8:H - 1, W - 2] = IDX["glow"]
        a[2, 2:W - 10] = IDX["glow_mid"]; a[H - 3, 2:W - 3] = IDX["glow_mid"]
        for (x, y) in ((11, 5), (W - 6, H - 7), (11, H - 6)):
            a[y, x] = IDX["glow_core"]; a[y - 1, x] = a[y + 1, x] = a[y, x - 1] = a[y, x + 1] = IDX["glow_mid"]
    return a, nine_meta(W, H, 18, 12, 10, 12, "日記頁：左邊釘裝孔＋紅 margin（left 18px；中間 40px＝tile 週期 8 嘅倍數）、右上摺角；中間橫線 tile（週期 8）" + ("；特別頁（進化／化光嗰日）金邊" if special else ""))

# ============================================================ UI build
UI_ITEMS = {}
def save_ui(name, a, meta=None):
    os.makedirs(UI, exist_ok=True); to_img(a).save(os.path.join(UI, name + ".png")); UI_ITEMS[name] = dict(meta or {}, size=[a.shape[1], a.shape[0]])

def build_ui():
    save_ui("icon_star_shard_16", star_shard(16), {"kind": "icon", "use": "星星碎（貨幣）16px：HUD／委託獎勵"})
    save_ui("icon_star_shard_32", star_shard(32), {"kind": "icon", "use": "星星碎 32px：入帳彈出／懸浮掉落"})
    save_ui("icon_commission_feed", icon_feed(), {"kind": "icon", "use": "委託：餵食（例：餵 2 次）"})
    save_ui("icon_commission_water", icon_water(), {"kind": "icon", "use": "委託：淋水（例：淋水 1 次）"})
    save_ui("icon_commission_play", icon_play(), {"kind": "icon", "use": "委託：陪玩（例：陪玩 1 次）"})
    a, m = panel_commission(); save_ui("panel_commission_9s", a, {"kind": "nineSlice", **m})
    a, m = row_slot(); save_ui("panel_commission_row_9s", a, {"kind": "nineSlice", **m})
    save_ui("checkbox_empty", checkbox(False), {"kind": "icon", "use": "委託未完成"})
    save_ui("checkbox_done", checkbox(True), {"kind": "icon", "use": "委託完成（剔）"})
    a, m = bubble_frame(); save_ui("bubble_thought_9s", a, {"kind": "nineSlice", **m})
    save_ui("bubble_thought_tail", bubble_tail(), {"kind": "piece", "use": "心聲泡尾巴（3 粒細泡），pivot 左下 (1,12) 對準團絨 head_r 錨點"})
    a, m = diary_page(False); save_ui("diary_page_9s", a, {"kind": "nineSlice", **m})
    a, m = diary_page(True); save_ui("diary_page_special_9s", a, {"kind": "nineSlice", **m})
    for nm, fn, use in (("sun", st_sun, "晴"), ("rain", st_rain, "落雨"), ("food", st_food, "食咗乜（飯糰）"), ("heart", st_heart, "心情好／親密度"),
                        ("evolve", st_evolve, "進化／化光"), ("sleep", st_sleep, "瞓覺／早瞓")):
        save_ui(f"sticker_{nm}", fn(), {"kind": "sticker", "use": "日記貼紙：" + use})
    save_ui("icon_remind_water", icon_remind_water(), {"kind": "icon", "use": "飲水提醒（懸浮，可設 1–3h）"})
    save_ui("icon_remind_sleep", icon_remind_sleep(), {"kind": "icon", "use": "早瞓提醒（懸浮，可設時間）"})
    # atlas（padding 2、extrude 1）
    names = list(UI_ITEMS); ims = {n: np.array(Image.open(os.path.join(UI, n + ".png")).convert("RGBA")) for n in names}
    x = y = 2; rowh = 0; W = 256; pos = {}
    for n in sorted(names, key=lambda n: -ims[n].shape[0]):
        h, w = ims[n].shape[:2]
        if x + w + 2 > W: x = 2; y += rowh + 4; rowh = 0
        pos[n] = (x + 1, y + 1, w, h); x += w + 4; rowh = max(rowh, h + 2)
    H = 1 << int(math.ceil(math.log2(y + rowh + 4)))
    at = np.zeros((H, W, 4), np.uint8); fr = {}
    for n, (x0, y0, w, h) in pos.items():
        e = ims[n]; at[y0:y0 + h, x0:x0 + w] = e
        at[y0 - 1, x0:x0 + w] = e[0]; at[y0 + h, x0:x0 + w] = e[-1]; at[y0:y0 + h, x0 - 1] = e[:, 0]; at[y0:y0 + h, x0 + w] = e[:, -1]
        fr[n] = {"frame": {"x": x0, "y": y0, "w": w, "h": h}, "rotated": False, "trimmed": False, "sourceSize": {"w": w, "h": h}, **{k: v for k, v in UI_ITEMS[n].items() if k != "size"}}
    Image.fromarray(at, "RGBA").save(os.path.join(UI, "atlas_systems12_ui.png"))
    json.dump({"frames": fr, "meta": {"image": "atlas_systems12_ui.png", "size": {"w": W, "h": H}, "format": "RGBA8888", "padding": 2, "extrude": 1,
               "palette": "../../sprites/tuanrong/motion/palette.json", "spec": "docs-gdd/systems12-v1.md 遊美素材清單 第 1 批",
               "rules": "v3 31 色、alpha 0/255、無 AA；整數倍放大、Nearest；9-slice center／edges 用 tile（唔好 stretch）"}},
              open(os.path.join(UI, "atlas_systems12_ui.json"), "w"), indent=1, ensure_ascii=False)
    return UI_ITEMS

# ============================================================ weather (陰／霧) + seasons
def tohex(c): return B.tohex(c)
def hx(h): return B.hx(h)

def final_grade(base, tint, sat, con, **over):
    g = json.loads(json.dumps(base))
    g["ambientTint"] = tohex(hx(base["ambientTint"]) * hx(tint)); g["saturation"] = round(base["saturation"] * sat, 3); g["contrast"] = round(base["contrast"] * con, 3)
    for k, v in over.items(): g[k] = v
    return g

WEATHER = {
 "overcast": dict(name="陰", tint="#d8dee6", sat=0.80, con=0.93, over=dict(fog=dict(color="#d0d8e0", density=0.08), bloom=dict(threshold=0.92, intensity=0.08),
                  vignette=0.16, rim=dict(color="#4e5c78", intensity=0.5, dir=[0.6, 0.8]), petTint="#eee2d4", dof=dict(far=1.4, mid=0.6, fore=2.2)),
                  particles_rate=0.15, note="陰天（20%）最終值；sky/far/mid/fore 用 H3/overcast/*；lightmap 沿用 H3（引擎可 globalAlpha 0.7 收淡陰影＝散射光）；light_add globalAlpha 0.4；雲帶 weather/overcast_clouds.png 疊喺 sky 之上、far 之下"),
 "fog": dict(name="霧", tint="#e8edf0", sat=0.70, con=0.82, over=dict(fog=dict(color="#e2e8ea", density=0.24), bloom=dict(threshold=0.95, intensity=0.06),
                  vignette=0.12, rim=dict(color="#7a8aa0", intensity=0.35, dir=[0.6, 0.8]), petTint="#f2e8dc", dof=dict(far=2.4, mid=1.0, fore=2.6)),
                  particles_rate=0.0, note="霧天（5%）最終值；sky/far/mid/fore 用 H3/fog/*（遠景已預烘淡出）；lightmap 沿用 H3（globalAlpha 0.5）；light_add globalAlpha 0.25；霧帶 weather/fog_bank.png 兩層（遠：far 之後；近：fore 之前）橫向慢飄"),
}

def far_fade(raw, nm, amt, col):
    """霧：遠景按層深度向霧色收（far 多、mid 少、sky 最多）— 喺 raw 上做，之後先過 LUT"""
    k = {"sky": amt, "far": amt * 0.8, "mid": amt * 0.35, "fore": amt * 0.1}[nm]
    out = raw.copy(); out[..., :3] = raw[..., :3] * (1 - k) + hx(col) * k; return out

def cloud_band(W=223, H=96, seed=12):
    """陰天雲帶：橫向無縫（wrap）、3 色、alpha 0/255"""
    rng = np.random.default_rng(seed); yy, xx = np.mgrid[:H, :W].astype(float)
    v = np.zeros((H, W))
    for i in range(16):
        cx, cy, rx, ry = rng.uniform(0, W), rng.uniform(H * .25, H * .75), rng.uniform(18, 40), rng.uniform(8, 16)
        for off in (-W, 0, W):
            v = np.maximum(v, 1 - (((xx - cx - off) / rx) ** 2 + ((yy - cy) / ry) ** 2))
    m = v > 0.0; core = v > 0.35; top = np.roll(v, 3, 0) <= 0.0
    a = np.zeros((H, W, 4), np.uint8)
    C = {"lit": (230, 235, 240), "mid": (196, 204, 214), "shade": (163, 173, 186)}
    a[m] = (*C["shade"], 255); a[core] = (*C["mid"], 255); a[m & top] = (*C["lit"], 255); a[core & (np.roll(v, 2, 0) < 0.35)] = (*C["lit"], 255)
    return a, C

def fog_bank(W=223, H=72, seed=5, k=0):
    """霧帶：橫向無縫、Bayer 抖色（alpha 0/255）、上薄下厚"""
    yy, xx = np.mgrid[:H, :W].astype(float)
    """上下兩邊都淡出（無硬邊）；波浪令頂邊高低起伏"""
    wv = 0.10 * np.sin(2 * math.pi * (xx / W) * 2 + k) + 0.06 * np.sin(2 * math.pi * (xx / W) * 5 + 1.7 + k * 0.5)
    t = np.clip((yy / (H - 1) - wv) / (1 - 0.0), 0, 1)
    prof = np.where(t < 0.55, np.clip(np.sin(np.pi / 2 * np.minimum(t / 0.55, 1)), 0, 1) ** 1.5, np.clip(np.cos(np.pi / 2 * np.clip((t - 0.55) / 0.45, 0, 1)), 0, 1) ** 1.2)
    env = np.clip(np.minimum(yy, H - 1 - yy) / 4.0, 0, 1)   # 上下最尾幾行一定淡到 0（冇硬邊）
    dens = np.clip(prof, 0, 1) * 0.72 * env
    th = np.tile(B.BAYER, (H // 4 + 1, W // 4 + 1))[:H, :W]
    on = dens > th; deep = dens > 0.55
    a = np.zeros((H, W, 4), np.uint8); C = {"thin": (238, 242, 244), "thick": (223, 230, 234)}
    a[on] = (*C["thin"], 255); a[on & deep] = (*C["thick"], 255)
    return a, C

def load_rgba(p): return np.asarray(Image.open(p).convert("RGBA")).astype(float) / 255

def bake_set(key, g2, raw_fn, outdir, lutname):
    os.makedirs(outdir, exist_ok=True)
    lut = B.make_lut(g2); B.save_rgb(lut, os.path.join(outdir, lutname)); layers = {}
    d = os.path.join(SCN, key)
    for nm in ("sky", "far", "mid", "fore"):
        raw = load_rgba(os.path.join(d, "raw", f"{nm}.png")); raw = raw_fn(raw, nm)
        layers[nm] = B.bake(raw, g2, nm, lut); B.save_rgba(layers[nm], os.path.join(outdir, f"{nm}.png"))
    return layers, lut

def pet_frame_loader(frame_map):
    """mockup 用：B.comp_pet 由 motion/frames 讀；天氣 clip 喺 liveliness/frames"""
    orig = B.load_frame
    def lf(form, name="idle_01"):
        if name.startswith(("leaf_umbrella", "shiver")):
            return np.asarray(Image.open(os.path.join(LV, "frames", form, f"{name}.png")).convert("RGBA")).astype(float) / 255
        return orig(form, name)
    B.load_frame = lf

def build_weather():
    os.makedirs(WXD, exist_ok=True); pet_frame_loader(None)
    base = json.load(open(os.path.join(SCN, "H3", "grade.json")))
    out = {}
    d3 = os.path.join(SCN, "H3")
    lm = np.asarray(Image.open(os.path.join(d3, "lightmap.png"))).astype(float) / 255
    add0 = np.asarray(Image.open(os.path.join(d3, "light_add.png"))).astype(float) / 255
    vg = load_rgba(os.path.join(d3, "vignette.png"))
    cb, CC = cloud_band(); Image.fromarray(cb, "RGBA").save(os.path.join(WXD, "overcast_clouds.png"))
    fbs = []
    for k in range(2):
        fb, FC = fog_bank(seed=5, k=k * math.pi); fbs.append(fb)
    Image.fromarray(np.concatenate([fbs[0], fbs[1]], 0), "RGBA").save(os.path.join(WXD, "fog_bank.png"))
    json.dump({"overcast_clouds": {"image": "overcast_clouds.png", "size": [223, 96], "wrapX": True, "colors": {k: "#%02x%02x%02x" % v for k, v in CC.items()},
               "draw": "陰天：疊喺 sky 之上、far 之下（parallax 同 sky 0.15）；art y −6 起（層座標 y 6）；橫向慢飄 2 px/s 循環；globalAlpha 0.85；唔食 lightmap",
               "anyVariant": "H1–H4 都可以疊（H4 夜晚 globalAlpha 0.35＋multiply #6a70a0）"},
               "fog_bank": {"image": "fog_bank.png", "size": [223, 144], "frames": {"far": [0, 0, 223, 72], "near": [0, 72, 223, 72]}, "wrapX": True,
                            "colors": {k: "#%02x%02x%02x" % v for k, v in FC.items()},
                            "draw": "霧天：far 帶畫喺 far 之後（art y 200–272，0.35 parallax，飄 3 px/s，globalAlpha 0.7）；near 帶畫喺 fore 之前（art y 300–372，飄 6 px/s 反方向，globalAlpha 0.45）；Bayer 抖色 alpha 0/255",
                            "anyVariant": "H1 晨霧最啱；H4 夜霧 multiply #8088b0"},
               "spec": "docs-gdd/systems12-v1.md 系統 7 天氣：晴60／陰20／雨15／霧5%（雨已有：rain/）",
               "weights": {"clear": 60, "overcast": 20, "rain": 15, "fog": 5}},
              open(os.path.join(WXD, "weather.json"), "w"), indent=1, ensure_ascii=False)
    for wk, W_ in WEATHER.items():
        g2 = dict(baseVariant="H3", note=W_["note"]); g2.update(final_grade(base, W_["tint"], W_["sat"], W_["con"], **W_["over"]))
        g2.pop("variant", None); g2.pop("name", None); g2.pop("hours", None)
        g2["particles"] = dict(base["particles"]); g2["particles"]["rate"] = W_["particles_rate"]
        json.dump(g2, open(os.path.join(d3, f"grade_{wk}.json"), "w"), ensure_ascii=False, indent=1)
        sub = os.path.join(d3, wk)
        fn = (lambda r, nm: far_fade(r, nm, 0.45, "#e2e8ea")) if wk == "fog" else (lambda r, nm: far_fade(r, nm, 0.38, "#c8d0da") if nm == "sky" else r)
        layers, lut = bake_set("H3", g2, fn, sub, f"lut_{wk}.png")
        add = add0 * (0.4 if wk == "overcast" else 0.25); eb = np.zeros_like(add)
        lmw = 1 - (1 - lm) * (0.7 if wk == "overcast" else 0.5)
        def fx(img, wk=wk):
            if wk == "overcast":
                c = cb.astype(float) / 255; a_ = np.zeros((B.AH, B.AW, 1)); col = np.zeros((B.AH, B.AW, 3))
                h = min(96, B.AH); a_[:h] = c[:h, 14:14 + B.AW, 3:] * 0.85; col[:h] = c[:h, 14:14 + B.AW, :3]
                return img * (1 - a_) + col * a_
            for fb, y0, al in ((fbs[0], 200, 0.7), (fbs[1], 300, 0.45)):
                c = fb.astype(float) / 255; a_ = c[:, :B.AW, 3:] * al; img[y0:y0 + 72] = img[y0:y0 + 72] * (1 - a_) + c[:, :B.AW, :3] * a_
            return img
        for form in B.FORMS:
            frame = "idle_01" if wk == "overcast" else "shiver_02"
            im = compose_w(layers, lmw, add, eb, vg, g2, form, frame, fx)
            B.save_rgb(im, os.path.join(sub, f"mockup_{wk}_{form}.png"))
            Image.fromarray(B.to8(im)).resize((B.AW * 2, B.AH * 2), Image.NEAREST).save(os.path.join(sub, f"mockup_{wk}_{form}_2x.png"))
        out[wk] = g2
    return out

def compose_w(layers, lm, add, eb, vg, g, form, frame, fx):
    """同 B.compose 一樣，不過天氣疊層喺 sky 後（雲）或者 far／fore 前（霧）— mockup 示意"""
    img = B.crop(layers["sky"])[..., :3]
    for nm in ("far", "mid"): img = B.over(img, B.crop(layers[nm]))
    pet, bulb = B.comp_pet("H3", g, form, frame)
    yy, xx = np.mgrid[0:B.AH, 0:B.AW].astype(float); S = B.FORMS[form]
    sh = (((xx - B.FOOT[0]) / (S * 0.36)) ** 2 + ((yy - B.FOOT[1] - 0.5) / (S * 0.07 + 1)) ** 2 <= 1)
    img = img * (1 - 0.22 * sh[..., None]); img = B.over(img, pet); img = B.over(img, B.crop(layers["fore"]))
    img = img * B.crop(lm) + B.crop(add) + B.crop(eb) * g["bloom"]["intensity"]
    bx, by = bulb; r = np.hypot(xx - bx, yy - by)
    img = img + (np.exp(-(r / (10 if S > 32 else 6)) ** 2) * 0.35 * 0.6)[..., None] * hx(g["bulbGlowTint"])
    img = fx(img)
    fc = hx(g["fog"]["color"]); img = img * (1 - g["fog"]["density"]) + fc * g["fog"]["density"]
    return np.clip(B.over(np.clip(img, 0, 1), vg), 0, 1)

SEASONS = {   # 香港月份
 "spring": dict(name="春", months=[3, 4, 5], tint="#fff4f4", sat=1.04, con=1.00, green=("#8fd07a", 0.25), lift=0.0, shadow="#f2e8f4", shadowK=1.0,
                particles=("petal", "#ffe0ec"), note="春（3–5 月）：微粉暖、嫩綠；花瓣粒子"),
 "summer": dict(name="夏", months=[6, 7, 8], tint="#fffae6", sat=1.12, con=1.06, green=("#4fb04a", 0.30), lift=0.0, shadow="#e8ecf8", shadowK=1.12,
                particles=("mote", "#fff6c8"), note="夏（6–8 月）：高飽和、暖白日光、深綠、陰影實啲；光塵粒子"),
 "autumn": dict(name="秋", months=[9, 10, 11], tint="#fff0dc", sat=1.00, con=1.03, green=("#e0963c", 0.62), lift=0.0, shadow="#f4e4d8", shadowK=1.0,
                particles=("gold", "#ffc878"), note="秋（9–11 月）：綠葉轉琥珀橙、暖調；金色飄粒"),
 "winter": dict(name="冬", months=[12, 1, 2], tint="#eef2ff", sat=0.80, con=0.96, green=("#9ab4ae", 0.45), lift=0.035, shadow="#dce4f8", shadowK=0.85,
                particles=("mote", "#f4f8ff"), note="冬（12–2 月）：冷藍、低飽和、綠轉灰青、稍為光啲（冬日薄光）；白色細粒（似霜塵）；團絨打冷震 clip 機率加大"),
}

def season_fn(c, S):
    """季節色調（喺 variant grade 之後）：tint → 綠色選擇性轉色（保亮度）→ 對比 → 飽和 → lift"""
    c = c * hx(S["tint"])
    tgt, k = S["green"]; t = hx(tgt); W_ = np.array([0.2126, 0.7152, 0.0722])
    w = np.clip((c[..., 1] - np.maximum(c[..., 0], c[..., 2])) * 5.0, 0, 1)[..., None] * k
    lum = (c @ W_)[..., None]; tl = float(t @ W_)
    c = c * (1 - w) + (t * lum / max(tl, 1e-6)) * w
    c = (c - 0.5) * S["con"] + 0.5
    lum = (c @ W_)[..., None]; c = lum + (c - lum) * S["sat"]
    c = c + S["lift"] * (1 - c)
    return np.clip(c, 0, 1)

def season_lut(g, S):
    return season_fn(B.make_lut(g), S)

def season_lightmap(lm, S):
    sh = (1 - lm.mean(-1, keepdims=True))
    out = 1 - (1 - lm) * S["shadowK"]
    out = out * (1 - sh * (1 - hx(S["shadow"])) * 0.8)
    return np.clip(out, 0, 1)

def build_seasons():
    os.makedirs(SEA, exist_ok=True); pet_frame_loader(None); res = {}
    for sk, S in SEASONS.items():
        for key in ("H1", "H2", "H3", "H4"):
            d = os.path.join(SCN, key); od = os.path.join(SEA, sk, key); os.makedirs(od, exist_ok=True)
            g = json.load(open(os.path.join(d, "grade.json")))
            lut = season_lut(g, S); B.save_rgb(lut, os.path.join(od, "lut.png"))
            layers = {}
            for nm in ("sky", "far", "mid", "fore"):
                raw = load_rgba(os.path.join(d, "raw", f"{nm}.png"))
                layers[nm] = B.bake(raw, g, nm, lut); B.save_rgba(layers[nm], os.path.join(od, f"{nm}.png"))
            lm = np.asarray(Image.open(os.path.join(d, "lightmap.png"))).astype(float) / 255
            lms = season_lightmap(lm, S); B.save_rgb(lms, os.path.join(od, "lightmap.png"))
            g2 = dict(baseVariant=key, note=f"{S['name']}（{'／'.join(str(m) for m in S['months'])} 月）× {key}：sky/far/mid/fore/lightmap 用 seasons/{sk}/{key}/*；"
                      "lut.png ＝ season_fn(variant grade)（見 FORMAT §SYS12）；light_add／emissive／vignette 沿用 variant")
            gg = json.loads(json.dumps(g)); [gg.pop(k, None) for k in ("variant", "name", "hours")]
            g2.update(gg)
            g2["ambientTint"] = tohex(hx(g["ambientTint"]) * hx(S["tint"])); g2["petTint"] = tohex(np.clip(hx(g["petTint"]) * (0.5 + 0.5 * hx(S["tint"])), 0, 1))
            if key != "H4": g2["particles"] = dict(type=S["particles"][0], rate=g["particles"]["rate"], color=S["particles"][1])
            json.dump(g2, open(os.path.join(od, "grade.json"), "w"), ensure_ascii=False, indent=1)
            res[(sk, key)] = dict(layers=layers, lm=lms, g=g2)
    json.dump({"version": 1, "spec": "docs-gdd/systems12-v1.md 系統 7：季節跟香港月份換場景色調",
               "seasons": {sk: dict(name=S["name"], months=S["months"], dir=f"seasons/{sk}/", note=S["note"],
                                    params={k: S[k] for k in ("tint", "sat", "con", "lift", "shadow", "shadowK")} | {"green": list(S["green"])}) for sk, S in SEASONS.items()},
               "variants": ["H1", "H2", "H3", "H4"],
               "files": "seasons/<season>/<H#>/{sky,far,mid,fore}.png（223×446 RGBA，已預烘 LUT＋DoF）、lightmap.png（multiply）、lut.png（256×16）、grade.json",
               "weatherRule": "天氣層（H3 rain／overcast／fog）優先：落雨／陰／霧時用 H3/<weather>/*，季節只影響 ambientTint／petTint／粒子；晴天先用季節層",
               "crossfade": "換季（每月 1 號 00:00 跨季）→ 3s crossfade；同 crossfade/ 時段轉換一樣做法"},
              open(os.path.join(SEA, "seasons.json"), "w"), indent=1, ensure_ascii=False)
    return res

def season_preview(res):
    """4 季 × 4 時段 mockup（radiant idle），1x 縮半 → 預覽"""
    pet_frame_loader(None)
    cells = []
    for sk in SEASONS:
        row = []
        for key in ("H1", "H2", "H3", "H4"):
            r = res[(sk, key)]; d = os.path.join(SCN, key)
            add = np.asarray(Image.open(os.path.join(d, "light_add.png"))).astype(float) / 255
            eb = np.asarray(Image.open(os.path.join(d, "emissive_blur.png"))).astype(float) / 255
            vg = load_rgba(os.path.join(d, "vignette.png"))
            im = B.compose(key, r["layers"], r["lm"], add, eb, vg, r["g"], "radiant", particles=False)
            row.append(Image.fromarray(B.to8(im)))
        cells.append(row)
    W_, H_ = B.AW, B.AH; sheet = Image.new("RGB", (4 * W_ + 5 * 4, 4 * H_ + 5 * 4 + 0), (40, 36, 52))
    for j, row in enumerate(cells):
        for i, im in enumerate(row): sheet.paste(im, (4 + i * (W_ + 4), 4 + j * (H_ + 4)))
    os.makedirs(PREV, exist_ok=True); p = os.path.join(PREV, "seasons_4x4_1x.png"); sheet.save(p); return p

def run_ui():
    items = build_ui(); w = build_weather(); s = build_seasons(); sp = season_preview(s)
    json.dump({"ui": list(items), "weather": list(w), "seasons": [f"{a}/{b}" for a, b in s]}, open("/workspace/_sys12/stats_ui.json", "w"), indent=1, ensure_ascii=False)
    print("ui", len(items), "weather", list(w), "seasons", len(s), sp)

# ============================================================ docs (merge-safe：寫之前即刻重讀)
TRD = os.path.join(ROOT, "sprites", "tuanrong")
def _atomic(path, text):
    import tempfile
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".tmp_sys12_")
    with os.fdopen(fd, "w", encoding="utf-8") as fh: fh.write(text)
    os.chmod(tmp, 0o644); os.replace(tmp, path)

def _stats():
    ev = json.load(open("/workspace/_sys12/stats_evo.json"))
    for p in sorted(glob.glob("/workspace/_sys12/stats_evo_*.json"), key=os.path.getmtime):
        if os.path.getmtime(p) > os.path.getmtime("/workspace/_sys12/stats_evo.json"): ev.update(json.load(open(p)))
    ev.pop("fit", None)
    return (json.load(open("/workspace/_sys12/stats_base.json")), json.load(open("/workspace/_sys12/stats_lumi.json")), ev,
            json.load(open("/workspace/_sys12/stats_ui.json")))

def _section(md, a_, b_, sec, after=None):
    if a_ in md: md = md[:md.index(a_)].rstrip() + "\n\n" + md[md.index(b_) + len(b_):].lstrip()
    anchor = next((m for m in (after or []) if m in md), None)
    if anchor: i = md.index(anchor) + len(anchor); return md[:i] + "\n\n" + sec + md[i:]
    return md.rstrip() + "\n\n" + sec

def run_docs():
    import build_systems12_b1 as S1
    WX = S1.WX; base, lumi, ev, ui = _stats()
    FAB = json.load(open(os.path.join(LV, "face_anchors.json")))["anchors"]
    FAL = json.load(open(os.path.join(TRD, "lumi", "face_anchors_lumi.json")))["anchors"]
    FAE = {f: json.load(open(os.path.join(TRD, "evo6", f, f"face_anchors_{f}.json")))["anchors"] for f in ev}
    LOOPR = {"leaf_umbrella": [2, 5], "shiver": [0, 3]}
    p = os.path.join(MOT, "CLIPS.json"); D = json.load(open(p, encoding="utf-8"))   # 即刻重讀
    for c in WX:
        fps, loop, lf, pri, intr, cd, nxt, item, trig, notes = S1.WX_META[c]
        nf = S1.WX_SPEC[c]
        ent = {"name": c, "status": "已交付（systems12 第 1 批）", "category": "天氣", "item": item, "frames": nf, "fps": fps, "loop": loop,
               "priority": pri, "interruptible": intr, "trigger": trig, "cooldown_s": cd, "next": nxt, "notes": notes, "attachments": [],
               "layers": {"noface": f"liveliness/layers/<form>/{c}_NN_noface.png", "faceov": f"liveliness/layers/<form>/{c}_NN_faceov.png",
                          "full": f"liveliness/frames/<form>/{c}_NN.png", "nofaceClip": f"{c}_noface", "atlas": "liveliness/atlas_<form>_live_wx.json",
                          "kitAtlas": "liveliness/atlas_<form>_live.json（eyes_*/mouth_*/bulb_*）", "previewStrip": "../preview/systems12/"},
               "anchors": {**{f: FAB[f][c] for f in ("sprout", "radiant", "soft")}, "lumi": FAL[c], **{f: FAE[f][c] for f in ev}},
               "batch": "systems12-b1", "loopRange": LOOPR[c]}
        if lf: ent["loopFrom"] = lf
        ent["lumi"] = {"frames": nf, "full": f"../lumi/frames/{c}_NN.png", "noface": f"../lumi/layers/{c}_NN_noface.png", "faceov": f"../lumi/layers/{c}_NN_faceov.png",
                       "emissive": f"../lumi/emissive/{c}_NN_emissive.png", "atlasClip": c, "nofaceClip": f"{c}_noface", "atlas": "../atlas_lumi.json"}
        for f in ev:
            ent[f] = {"frames": nf, "full": f"../evo6/{f}/frames/{c}_NN.png", "noface": f"../evo6/{f}/layers/{c}_NN_noface.png",
                      "faceov": f"../evo6/{f}/layers/{c}_NN_faceov.png", "emissive": f"../evo6/{f}/emissive/{c}_NN_emissive.png",
                      "atlasClip": c, "nofaceClip": f"{c}_noface", "atlas": f"../evo6/atlas_{f}.json"}
        i = next((k for k, x in enumerate(D["clips"]) if x["name"] == c), None)
        if i is None: D["clips"].append(ent)
        else: D["clips"][i] = ent
    for f in ("sprout", "radiant", "soft"):
        la = D["forms"][f].setdefault("liveAtlas", [])
        if f"atlas_{f}_live_wx.png" not in la: la.append(f"atlas_{f}_live_wx.png")
    fl = D["forms"]["lumi"]
    for c in WX:
        if c not in fl["clips"]: fl["clips"].append(c)
    fl["frames"] = lumi["total"]; fl["atlasPieces"] = lumi["atlas"][2]; fl["atlasSize"] = lumi["atlas"][:2]; fl["weather"] = list(WX)
    for f, st in ev.items():
        fe = D["forms"][f]
        for c in WX:
            if c not in fe["clips"]: fe["clips"].append(c)
        fe["weather"] = list(WX); fe["frames"] = st["total"]; fe["atlasSize"] = st["atlas"][:2]; fe["atlasPieces"] = st["atlas"][2]
    D["systems12B1"] = {
        "tool": "tools/build_systems12_b1.py（clip：base｜lumi｜evo）＋ tools/build_systems12_b1_ui.py（UI／天氣／季節／docs／preview）",
        "validator": "tools/validate_systems12_b1.py ＋ validate_liveliness／validate_lumi／validate_evo6_anim／validate_hd2d_scenes",
        "spec": "docs-gdd/systems12-v1.md 遊美素材清單 第 1 批（Kurt 2026-11-01 01:15 批：「兩個動作全部體型都做」）",
        "clips": {c: {"frames": S1.WX_SPEC[c], "fps": S1.WX_META[c][0], "loopRange": LOOPR[c]} for c in WX},
        "forms": ["sprout", "radiant", "soft", "lumi"] + list(ev), "eggExcluded": True,
        "atlases": {"sprout/radiant/soft": "liveliness/atlas_<form>_live_wx.png/json（新開；舊 live/live_s2/live_s3 版面不變）",
                    "lumi": "../atlas_lumi.png（重排，加 2 clip）", "evo6": "../evo6/atlas_<form>.png（重排，加 2 clip；evo_hop 連 route_clarity bulbmask／bulb_<id> ×8 重出）"},
        "leafChoice": {f: v.get("leafChoice") for f, v in {**base, **ev}.items() if isinstance(v, dict) and "leafChoice" in v},
        "leafNote": "片葉只畫落身後空白位（唔遮面／燈）；月眠（evo_guard_moon／evo_still_moon）頂帽佔滿上方，所以片葉撐喺膊頭側（leafChoice 5）＝刻意",
        "ui": "../../ui/systems12/（atlas_systems12_ui.png/json；9-slice 用 tile）",
        "weather": "../../scenes/hd2d/weather/weather.json ＋ H3/grade_{overcast,fog}.json ＋ H3/{overcast,fog}/*",
        "seasons": "../../scenes/hd2d/seasons/seasons.json（4 季 × H1–H4）",
        "preview": "../preview/systems12/",
        "runtime": {"rain": "H3 落雨 → leaf_umbrella（懸浮團絨都用）", "fog_or_winter": "霧天／冬（12–2 月）→ shiver 抽中率加大",
                    "rule": "天氣優先於季節：雨／陰／霧用 H3/<weather>/*；晴天用 seasons/<season>/<H#>/*"}}
    _atomic(p, json.dumps(D, indent=1, ensure_ascii=False))
    # CLIPS.md
    mp = os.path.join(MOT, "CLIPS.md"); md = open(mp, encoding="utf-8").read()
    a_, b_ = "<!-- SYS12B1-START -->", "<!-- SYS12B1-END -->"
    sec = (f"{a_}\n## systems12 第 1 批 — 天氣 clip＋UI\n"
           "| clip | 幀 | fps | loop | 用途 |\n|---|---|---|---|---|\n"
           + "\n".join(f"| `{c}` | {S1.WX_SPEC[c]} | {S1.WX_META[c][0]} | {LOOPR[c]} | {S1.WX_META[c][8]} |" for c in WX) +
           f"\n\n- 形態：sprout／radiant／soft（`liveliness/atlas_<form>_live_wx`）、lumi（`../atlas_lumi`）、evo6 全部 {len(ev)} 個（`../evo6/atlas_<form>`）；光卵唔做。\n"
           "- std：noface＋faceov＝完整、kit 合成＝完整、emissive、anchors（bulb＝燈中心）、atlas。葉／雨點／震線／白氣烙入身體層，只畫落空白位。\n"
           "- 月眠兩款頂帽佔滿上方 → 片葉撐喺膊頭（刻意）。\n"
           f"- UI {len(ui['ui'])} 件：`../../ui/systems12/`；天氣 陰／霧：`../../scenes/hd2d/weather/`＋`H3/{{overcast,fog}}/`；季節 4 套：`../../scenes/hd2d/seasons/`。\n{b_}\n")
    _atomic(mp, _section(md, a_, b_, sec, ["<!-- EVO6G-END -->"]))
    lp = os.path.join(ROOT, "ASSET_LOG.md"); lg = open(lp, encoding="utf-8").read()
    a_, b_ = "<!-- SYS12B1-LOG-START -->", "<!-- SYS12B1-LOG-END -->"
    nfr = 10 * (4 + len(ev))
    ent = (f"{a_}\n## 2026-11-01 — systems12 第 1 批素材\n"
           f"- 團絨天氣 clip：leaf_umbrella（撐葉 6 幀）＋ shiver（打冷震 4 幀）× {4 + len(ev)} 形態（sprout／radiant／soft／lumi＋evo6 {len(ev)}）＝ {nfr} 幀；新 atlas `atlas_<form>_live_wx` ×3，atlas_lumi＋evo6 atlas 重排（evo_hop 連 route_clarity 重出）；舊幀像素冇改（載入對拍）。\n"
           f"- UI（`ui/systems12/`）：委託面板 9-slice＋行底＋checkbox ×2、委託 icon ×3（餵／淋水／陪玩）、星星碎 16／32、心聲泡框＋尾、日記頁框（普通／特別）、日記貼紙 ×6、提醒 icon ×2；`atlas_systems12_ui`。\n"
           "- 天氣：`scenes/hd2d/H3/{overcast,fog}/`＋`grade_{overcast,fog}.json`＋`weather/{overcast_clouds,fog_bank}.png`＋`weather.json`（雨沿用 rain/）。\n"
           "- 季節：`scenes/hd2d/seasons/<spring|summer|autumn|winter>/H1–H4/`（LUT＋預烘層＋lightmap＋grade）＋`seasons.json`（香港月份）。\n"
           f"- 預覽 `sprites/tuanrong/preview/systems12/`；工具 `tools/build_systems12_b1.py`＋`tools/build_systems12_b1_ui.py`；驗證 `tools/validate_systems12_b1.py`；備份 `_backups/pre_systems12_b1_20261101/`。Pillow/numpy 程式繪製，無 AI。\n{b_}\n")
    _atomic(lp, _section(lg, a_, b_, ent))
    fp = os.path.join(SCN, "FORMAT.md"); fm = open(fp, encoding="utf-8").read()
    a_, b_ = "<!-- SYS12-START -->", "<!-- SYS12-END -->"
    W_ = json.load(open(os.path.join(WXD, "weather.json")))
    sec = (f"{a_}\n## SYS12. 天氣（陰／霧）＋季節（systems12 第 1 批）\n"
           "- 天氣權重：晴 60／陰 20／雨 15／霧 5（雨＝§7 `rain/`，唔變）。只 H3 戶外有天氣層。\n"
           "- 陰：`H3/grade_overcast.json`＋`H3/overcast/{sky,far,mid,fore}.png`（已預烘 `lut_overcast.png`）＋ `weather/overcast_clouds.png`：" + W_["overcast_clouds"]["draw"] + "\n"
           "- 霧：`H3/grade_fog.json`＋`H3/fog/{sky,far,mid,fore}.png`（遠景預烘淡出）＋ `weather/fog_bank.png`（far／near 兩帶）：" + W_["fog_bank"]["draw"] + "\n"
           "- 季節（香港月份：春 3–5／夏 6–8／秋 9–11／冬 12–2）：`seasons/<season>/<H#>/{sky,far,mid,fore,lightmap}.png`＋`lut.png`（256×16）＋`grade.json`（同 §5 schema）。晴天先用季節層；雨／陰／霧時用 H3/<weather>/*。換季 3s crossfade。\n"
           "- 團絨：落雨 → `leaf_umbrella`；霧／冬 → `shiver` 抽中率加大（CLIPS.json `systems12B1`）。\n"
           f"{b_}\n")
    _atomic(fp, _section(fm, a_, b_, sec))
    print("docs ok")

# ============================================================ preview（contact sheets）
def _nine(a, l, t, r, b, W, H):
    h, w = a.shape[:2]; out = np.zeros((H, W, 4), np.uint8)
    xs = list(range(l)) + [l + (i % (w - l - r)) for i in range(W - l - r)] + list(range(w - r, w))
    ys = list(range(t)) + [t + (i % (h - t - b)) for i in range(H - t - b)] + list(range(h - b, h))
    return a[np.ix_(ys, xs)]

def _ld(p): return np.array(Image.open(p).convert("RGBA"))
def _paste(dst, src, x, y):
    h, w = src.shape[:2]; m = src[..., 3] > 0; dst[y:y + h, x:x + w][m] = src[m]

def run_preview():
    import build_systems12_b1 as S1
    os.makedirs(PREV, exist_ok=True); base, lumi, ev, ui = _stats(); out = []
    forms = [("sprout", os.path.join(LV, "frames", "sprout")), ("radiant", os.path.join(LV, "frames", "radiant")), ("soft", os.path.join(LV, "frames", "soft")),
             ("lumi", os.path.join(TRD, "lumi", "frames"))] + [(f, os.path.join(TRD, "evo6", f, "frames")) for f in ev]
    BG = (196, 214, 226, 255); BG2 = (176, 196, 212, 255); Z = 3; C = 64
    for part, sel in (("a", forms[:9]), ("b", forms[9:17]), ("c", forms[17:])):
        cols = sum(S1.WX_SPEC.values()) + 1
        sheet = Image.new("RGBA", ((cols * (C + 4)) * Z, len(sel) * (C + 4) * Z), BG)
        for r, (f, d) in enumerate(sel):
            k = 0
            for c in S1.WX:
                for i in range(1, S1.WX_SPEC[c] + 1):
                    im = Image.open(os.path.join(d, f"{c}_{i:02d}.png")).convert("RGBA")
                    cell = Image.new("RGBA", (C, C), BG2 if c == "leaf_umbrella" else BG); cell.alpha_composite(im, ((C - im.width) // 2, C - im.height))
                    sheet.paste(cell.resize((C * Z, C * Z), Image.NEAREST), ((k * (C + 4) + 2) * Z, (r * (C + 4) + 2) * Z)); k += 1
                k += 0
        p = os.path.join(PREV, f"weather_clips_{part}_3x.png"); sheet.save(p); out.append(p)
    # UI contact（6x 單件）＋ mock 組合（3x）
    names = ui["ui"]; ims = {n: _ld(os.path.join(UI, n + ".png")) for n in names}
    x = y = 4; rowh = 0; W = 240; pos = []
    for n in names:
        h, w = ims[n].shape[:2]
        if x + w > W: x = 4; y += rowh + 6; rowh = 0
        pos.append((n, x, y)); x += w + 6; rowh = max(rowh, h)
    sh = np.zeros((y + rowh + 4, W, 4), np.uint8); sh[:] = (150, 176, 160, 255)
    for n, x0, y0 in pos: _paste(sh, ims[n], x0, y0)
    p = os.path.join(PREV, "ui_items_6x.png"); Image.fromarray(sh).resize((W * 6, sh.shape[0] * 6), Image.NEAREST).save(p); out.append(p)
    meta = json.load(open(os.path.join(UI, "atlas_systems12_ui.json")))["frames"]
    def nn(n, W_, H_):
        s = meta[n]["slice"]; return _nine(ims[n], s["left"], s["top"], s["right"], s["bottom"], W_, H_)
    M = np.zeros((260, 420, 4), np.uint8); M[:] = (150, 176, 160, 255)
    pan = nn("panel_commission_9s", 179, 96); _paste(M, pan, 6, 6)
    for k, ic in enumerate(("icon_commission_feed", "icon_commission_water", "icon_commission_play")):
        row = nn("panel_commission_row_9s", 163, 20); _paste(M, row, 14, 26 + k * 22)
        _paste(M, ims[ic], 18, 28 + k * 22)
        for j in range(3 + k % 2): M[34 + k * 22, 40 + j * 10:46 + j * 10] = (*RGB[IDX["cream1"]], 255)   # 字位示意
        _paste(M, ims["checkbox_done" if k == 0 else "checkbox_empty"], 120, 30 + k * 22)
        _paste(M, ims["icon_star_shard_16"], 136, 28 + k * 22)
    _paste(M, ims["icon_star_shard_32"], 150, 160)
    bub = nn("bubble_thought_9s", 120, 44); _paste(M, bub, 200, 10); _paste(M, ims["bubble_thought_tail"], 214, 52)
    for j in range(5): M[28, 214 + j * 14:224 + j * 14] = (*RGB[IDX["outline"]], 255)
    pet = _ld(os.path.join(LV, "frames", "radiant", "idle_01.png")) if os.path.exists(os.path.join(LV, "frames", "radiant", "idle_01.png")) else _ld(os.path.join(MOT, "frames", "radiant", "idle_01.png"))
    _paste(M, pet, 186, 60)
    for k, sp in enumerate((False, True)):
        pg = nn("diary_page_special_9s" if sp else "diary_page_9s", 100, 128); px0 = 6 + k * 108 if k == 0 else 300; py0 = 110 if k == 0 else 100
        if k == 1: px0, py0 = 310, 110
        _paste(M, pg, px0 if k == 0 else 316, 120 if k == 0 else 120)
    _paste(M, ims["sticker_sun"], 30, 132); _paste(M, ims["sticker_food"], 60, 160); _paste(M, ims["sticker_heart"], 30, 196)
    _paste(M, ims["sticker_evolve"], 340, 140); _paste(M, ims["sticker_rain"], 372, 190); _paste(M, ims["sticker_sleep"], 340, 200)
    _paste(M, ims["icon_remind_water"], 150, 210); _paste(M, ims["icon_remind_sleep"], 176, 210)
    p = os.path.join(PREV, "ui_mock_3x.png"); Image.fromarray(M).resize((420 * 3, 260 * 3), Image.NEAREST).save(p); out.append(p)
    # 天氣＋季節（H3 radiant）
    panels = [os.path.join(SCN, "H3", "mockup_radiant.png"), os.path.join(SCN, "H3", "overcast", "mockup_overcast_radiant.png"),
              os.path.join(SCN, "H3", "rain", "mockup_rain_radiant.png"), os.path.join(SCN, "H3", "fog", "mockup_fog_radiant.png")]
    panels = [Image.open(q).convert("RGB") for q in panels if os.path.exists(q)]
    sp = Image.open(os.path.join(PREV, "seasons_4x4_1x.png")).convert("RGB")
    panels += [sp.crop((4 + 2 * 199, 4 + j * 426, 4 + 2 * 199 + 195, 4 + j * 426 + 422)) for j in range(4)]
    s = Image.new("RGB", (len(panels) * 199 + 4, 430), (30, 30, 40))
    for i, im in enumerate(panels): s.paste(im, (4 + i * 199, 4))
    p = os.path.join(PREV, "weather_seasons_H3_1x.png"); s.save(p); out.append(p)
    print("\n".join(out)); return out
