# 《微光小圃》4b 屋仔 — 家具 12 件（6 擺位×2），48px 寵物比例；alpha 0/255、每張 ≤12 色、深色外框、光由左上、柔陰影
# 純 Pillow/numpy 程序繪製，冇 AI 生圖。
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from series2_lib import shade_body, limit_colors, ncolors, canvas, put, paste, hexc, mix, ellipse

OL = (74, 44, 62)                    # 外框（同房間 INK 一致）
DK = (70, 40, 74)
def ramp(h, hi=.5, md=.2, dk=.42):
    b = hexc(h); return (mix(b, (255, 255, 255), hi), b, mix(b, DK, md), mix(b, DK, dk))
def M(w, h): return Image.new('L', (w, h), 0)
def m_ell(w, h, b): im = M(w, h); ImageDraw.Draw(im).ellipse(b, fill=1); return np.array(im).astype(bool)
def m_rr(w, h, b, r): im = M(w, h); ImageDraw.Draw(im).rounded_rectangle(b, radius=r, fill=1); return np.array(im).astype(bool)
def m_poly(w, h, pts): im = M(w, h); ImageDraw.Draw(im).polygon(pts, fill=1); return np.array(im).astype(bool)
def m_rect(w, h, b): im = M(w, h); ImageDraw.Draw(im).rectangle(b, fill=1); return np.array(im).astype(bool)
def part(img, mask, rp, spec=False, light=(-0.7, -0.75)):
    shade_body(img, mask, rp, OL, light=light, spec=spec); return img
def fin(img, n=12): return limit_colors(img, n, protect=[OL, (255, 255, 255)])

WOOD = ramp('#c88a5c'); WOOD_L = ramp('#e2b07e'); CREAM = ramp('#fff4e0', .6, .12, .26); PINK = ramp('#ff9cb8'); GREEN = ramp('#7cc46a')
WHITE_R = ((255, 255, 255), (246, 242, 252), (224, 218, 240), (196, 186, 224)); BLUE = ramp('#8ec8f4'); YEL = ramp('#ffd65c')
RED = ramp('#f2707a'); LIL = ramp('#c8b2f6'); BARK = ramp('#9a6a48')

# ───────── 床（back＝床頭＋床褥＋枕頭；front＝被＋床尾，畫喺寵物之上）─────────
BW, BH = 92, 54; BPIV = (46, 53)
def bed_leaf():
    W, H = BW, BH; back = canvas(W, H); front = canvas(W, H)
    head = m_rr(W, H, (6, 2, 85, 40), 12); part(back, head, WOOD)
    heart = m_ell(W, H, (35, 9, 46, 20)) | m_ell(W, H, (45, 9, 56, 20)) | m_poly(W, H, [(35, 16), (56, 16), (45.5, 27)])
    part(back, heart, PINK)                                                              # 床頭心心
    for x in (3, 84):
        part(back, m_rr(W, H, (x, 12, x + 5, 52), 2), WOOD)                               # 床柱
        part(back, m_ell(W, H, (x - 1, 8, x + 6, 15)), WOOD_L)
    part(back, m_rr(W, H, (5, 30, 87, 46), 4), CREAM)                                     # 床褥
    for cx in (26, 66): part(back, m_ell(W, H, (cx - 11, 24, cx + 11, 35)), WHITE_R)      # 枕頭
    # front：葉仔被（尖頭向右）＋葉脈＋床尾板
    leaf = m_poly(W, H, [(4, 38), (30, 33), (62, 33), (90, 38), (86, 46), (6, 46)]) | m_ell(W, H, (4, 34, 34, 47)) | m_ell(W, H, (56, 34, 90, 47))
    part(front, leaf, GREEN)
    for x in range(10, 84): put(front, x, 40 + int(1.2 * math.sin(x / 9)), GREEN[3])
    for x0 in range(18, 80, 14):
        for t in range(5): put(front, x0 + t, 39 - t // 2 + int(1.2 * math.sin(x0 / 9)), GREEN[3])
    part(front, m_rr(W, H, (2, 44, 89, 53), 3), WOOD)
    for x in (12, 46, 80): part(front, m_ell(W, H, (x - 3, 46, x + 3, 51)), WOOD_L)
    return fin(back), fin(front)

def bed_cloud():
    W, H = BW, BH; back = canvas(W, H); front = canvas(W, H)
    cl = np.zeros((H, W), bool)
    for (x0, y0, x1, y1) in [(4, 14, 30, 40), (18, 4, 48, 34), (42, 2, 74, 32), (62, 12, 88, 40), (10, 20, 82, 42)]: cl |= m_ell(W, H, (x0, y0, x1, y1))
    part(back, cl, WHITE_R)
    for (x, y) in [(22, 14), (60, 10), (74, 22)]: put(back, x, y, YEL[1]); put(back, x + 1, y, YEL[0])
    part(back, m_rr(W, H, (5, 30, 87, 46), 5), ramp('#d8ecff', .5, .15, .3))
    for cx in (26, 66): part(back, m_ell(W, H, (cx - 11, 24, cx + 11, 35)), ramp('#ffe0ea', .5, .12, .28))
    bl = m_rr(W, H, (3, 35, 88, 49), 6); part(front, bl, BLUE)
    for i, (x, y) in enumerate([(14, 40), (30, 43), (46, 39), (62, 43), (78, 40)]):          # 星星
        for dx, dy in ((0, -1), (-1, 0), (0, 0), (1, 0), (0, 1)): put(front, x + dx, y + dy, YEL[1])
    puffs = np.zeros((H, W), bool)
    for x in range(4, 90, 12): puffs |= m_ell(W, H, (x - 1, 45, x + 12, 54))
    part(front, puffs, WHITE_R)
    return fin(back), fin(front)

# ───────── 檯 ─────────
def table_stump():
    W, H = 42, 34; img = canvas(W, H)
    body = m_rr(W, H, (5, 10, 36, 32), 4) | m_poly(W, H, [(2, 32), (8, 24), (34, 24), (40, 32)])
    part(img, body, BARK)
    for x in (12, 19, 27, 32):
        for y in range(16, 31, 1):
            if (y + x) % 5: put(img, x, y, BARK[3])
    top = m_ell(W, H, (3, 4, 38, 16)); part(img, top, WOOD_L)
    for (rx, ry) in [(11, 3.4), (6, 2)]:
        for a in range(0, 360, 8):
            put(img, 20.5 + rx * math.cos(math.radians(a)), 10 + ry * math.sin(math.radians(a)), WOOD_L[3])
    # 杯仔
    part(img, m_rr(W, H, (23, 0, 31, 8), 2), ramp('#ffffff', .2, .1, .3))
    put(img, 32, 3, OL); put(img, 32, 4, OL); put(img, 33, 4, OL)
    for x in range(24, 30): put(img, x, 2, PINK[1])
    # 細菇
    part(img, m_ell(W, H, (31, 21, 41, 28)), RED); part(img, m_rect(W, H, (35, 27, 37, 32)), CREAM)
    put(img, 34, 23, (255, 255, 255)); put(img, 38, 24, (255, 255, 255))
    return fin(img)

def table_round():
    W, H = 44, 36; img = canvas(W, H)
    part(img, m_rect(W, H, (19, 18, 24, 33)), WOOD); part(img, m_ell(W, H, (12, 30, 32, 35)), WOOD)
    cloth = m_poly(W, H, [(2, 12), (42, 12), (40, 26), (34, 24), (28, 27), (22, 24), (16, 27), (10, 24), (4, 26)]) | m_ell(W, H, (2, 6, 42, 18))
    part(img, cloth, ramp('#ffffff', .2, .08, .22))
    ys, xs = np.nonzero(cloth)
    for y, x in zip(ys, xs):                                                             # 格仔
        if ((x // 4) + (y // 3)) % 2 == 0 and img[y, x, :3].tolist() != list(OL): img[y, x, :3] = PINK[1] if y < 18 else PINK[2]
    # 細蛋糕
    part(img, m_rr(W, H, (16, 0, 28, 9), 2), ramp('#fff0d8', .5, .12, .3)); 
    for x in range(17, 28): put(img, x, 3, PINK[1])
    put(img, 22, -0, RED[1]); put(img, 22, 1, RED[1])
    return fin(img)

# ───────── 牆 ─────────
def wall_frame():
    W, H = 36, 32; img = canvas(W, H)
    part(img, m_rr(W, H, (0, 3, 35, 31), 3), WOOD)
    pic = m_rect(W, H, (5, 8, 30, 26)); img[pic] = (*BLUE[0], 255)
    img[m_rect(W, H, (5, 20, 30, 26))] = (*GREEN[1], 255)
    for y in range(8, 27): put(img, 5, y, WOOD[3]); 
    for x in range(5, 31): put(img, x, 8, WOOD[3])
    blob = m_ell(W, H, (11, 13, 24, 25)); part(img, blob, CREAM)                             # 團絨仔
    put(img, 15, 18, OL); put(img, 20, 18, OL); put(img, 14, 20, PINK[1]); put(img, 21, 20, PINK[1])
    put(img, 17, 9, YEL[1]); put(img, 18, 10, YEL[1]); put(img, 17, 11, YEL[1])               # 燈泡仔
    for dx, dy in ((0, 0), (2, 0), (-1, 1), (0, 1), (1, 1), (2, 1), (3, 1), (0, 2), (1, 2), (2, 2), (1, 3)): put(img, 26 + dx, 11 + dy, PINK[1])
    part(img, m_ell(W, H, (15, 0, 20, 5)), YEL)                                                # 掛鈎
    return fin(img)

def wall_shelf():
    W, H = 50, 30; img = canvas(W, H)
    part(img, m_rr(W, H, (1, 20, 48, 24), 1), WOOD)
    for x in (7, 39): part(img, m_poly(W, H, [(x, 24), (x + 4, 24), (x + 4, 29)]), WOOD)
    for i, (cx, col) in enumerate([(10, PINK), (24, YEL), (38, BLUE)]):
        part(img, m_poly(W, H, [(cx - 5, 12), (cx + 5, 12), (cx + 4, 20), (cx - 4, 20)]), ramp('#e8956a'))
        if i == 0:
            for (x0, y0, x1, y1) in [(cx - 6, 2, cx, 11), (cx, 0, cx + 6, 11)]: part(img, m_ell(W, H, (x0, y0, x1, y1)), GREEN)
        elif i == 1:
            part(img, m_rect(W, H, (cx - 1, 4, cx + 1, 12)), GREEN); part(img, m_ell(W, H, (cx - 4, 0, cx + 4, 7)), YEL)
            put(img, cx, 3, (255, 255, 255))
        else:
            part(img, m_ell(W, H, (cx - 5, 3, cx + 5, 13)), ramp('#8fcf8a'))
            for y in range(5, 12, 3): put(img, cx - 2, y, (255, 255, 255)); put(img, cx + 2, y + 1, (255, 255, 255))
    return fin(img)

# ───────── 地氈（透視橢圓）─────────
def rug_round():
    W, H = 98, 28; img = canvas(W, H)
    part(img, m_ell(W, H, (0, 0, 97, 27)), PINK, light=(-0.3, -0.9))
    inner = m_ell(W, H, (10, 4, 87, 23)); ring = inner & ~m_ell(W, H, (13, 5, 84, 22))
    img[ring] = (*PINK[0], 255)
    hp = [(0, 1), (1, 0), (2, 1), (3, 0), (4, 1), (0, 2), (1, 2), (2, 2), (3, 2), (4, 2), (1, 3), (2, 3), (3, 3), (2, 4)]
    for (ox, oy) in [(46, 11), (24, 12), (68, 12)]:
        for dx, dy in hp: put(img, ox + dx, oy + dy, (255, 255, 255) if ox == 46 else PINK[0])
    for a in range(0, 360, 12):                                                              # 流蘇點
        put(img, 48.5 + 50 * math.cos(math.radians(a)), 13.5 + 14 * math.sin(math.radians(a)), PINK[3])
    return fin(img)

def rug_leaf():
    W, H = 104, 30; img = canvas(W, H)
    leaf = m_ell(W, H, (0, 2, 92, 28)) & m_poly(W, H, [(0, 15), (20, 0), (80, 0), (103, 15), (80, 30), (20, 30)])
    leaf |= m_poly(W, H, [(86, 10), (103, 15), (86, 20)])
    part(img, leaf, GREEN, light=(-0.3, -0.9))
    for x in range(8, 96): put(img, x, 15, GREEN[3])
    for x0 in range(18, 88, 12):
        for t in range(7): put(img, x0 + t, 14 - t // 2, GREEN[3]); put(img, x0 + t, 16 + t // 2, GREEN[3])
    for (x, y) in [(30, 8), (60, 21), (74, 9)]: put(img, x, y, GREEN[0]); put(img, x + 1, y, GREEN[0])
    return fin(img)

# ───────── 窗（對準牆身窗洞；中間透明）─────────
WIN_W, WIN_H = 74, 80; WIN_HOLE_C = (37, 37)            # 窗洞中心喺 sprite 內位置；房間窗洞 46×52
def _hole(W, H):
    cx, cy = WIN_HOLE_C; return m_rect(W, H, (cx - 23, cy - 26, cx + 22, cy + 25))
def win_curtain():
    W, H = WIN_W, WIN_H; img = canvas(W, H); cx, cy = WIN_HOLE_C
    part(img, m_rr(W, H, (2, 4, 71, 8), 2), WOOD)                                           # 窗簾棍
    for x in (0, 67): part(img, m_ell(W, H, (x, 2, x + 6, 10)), WOOD_L)
    for s in (-1, 1):                                                                        # 兩邊窗簾（綁住）
        x_out = cx + s * 30; x_in = cx + s * 14
        pts = [(x_out, 8), (x_in, 8), (cx + s * 22, 40), (x_in + s * 2, 62), (x_out, 64)]
        part(img, m_poly(W, H, pts), PINK)
        for t in range(3): put(img, cx + s * (24 + t * 2), 20 + t * 9, PINK[3])
        part(img, m_ell(W, H, (cx + s * 25 - 4, 36, cx + s * 25 + 4, 44)), ramp('#fff0a0'))   # 蝴蝶結
    val = np.zeros((H, W), bool)                                                              # 波浪頂幔
    for x in range(6, 68, 10): val |= m_ell(W, H, (x, 6, x + 12, 18))
    val |= m_rect(W, H, (6, 7, 67, 12)); part(img, val, PINK)
    for x in range(10, 66, 10): put(img, x + 2, 15, (255, 255, 255))
    part(img, m_rr(W, H, (10, 66, 63, 76), 2), WOOD)                                          # 花槽
    for i, x in enumerate(range(15, 60, 7)):
        col = [RED, YEL, PINK][i % 3]; part(img, m_ell(W, H, (x - 3, 60, x + 4, 67)), col)
        put(img, x, 63, (255, 255, 255))
    return fin(img)

def win_star():
    W, H = WIN_W, WIN_H; img = canvas(W, H); cx, cy = WIN_HOLE_C
    outer = m_rr(W, H, (cx - 29, cy - 34, cx + 28, cy + 30), 26) & ~m_rect(W, H, (0, cy + 31, W, H))
    inner = m_rr(W, H, (cx - 24, cy - 29, cx + 23, cy + 26), 22)
    for s in (-1, 1):
        pts = [(cx + s * 26, cy - 22), (cx + s * 15, cy - 22), (cx + s * 11, cy + 4), (cx + s * 18, cy + 28), (cx + s * 26, cy + 28)]
        part(img, m_poly(W, H, pts), BLUE)
        part(img, m_ell(W, H, (cx + s * 18 - 3, cy + 2, cx + s * 18 + 3, cy + 8)), YEL)
    part(img, outer & ~inner, ramp('#7c8ad8'))
    for i in range(9):                                                                       # 星星吊飾
        t = i / 8; x = cx - 26 + 52 * t; y = cy - 24 + 8 * math.sin(math.pi * t)
        put(img, x, y - 1, OL)
        for dx, dy in ((0, 0), (-1, 1), (0, 1), (1, 1), (0, 2), (-1, 3), (1, 3)): put(img, x + dx, y + dy, YEL[1] if i % 2 else (255, 255, 255))
    for x in range(int(cx - 26), int(cx + 27)): put(img, x, int(cy - 25 + 8 * math.sin(math.pi * (x - cx + 26) / 52)) - 1, YEL[3])
    part(img, m_rr(W, H, (cx - 30, cy + 28, cx + 29, cy + 33), 2), ramp('#7c8ad8'))
    for x in (cx - 18, cx + 16): part(img, m_ell(W, H, (x - 3, cy + 30, x + 3, cy + 36)), YEL)
    return fin(img)

# ───────── 燈（emissive mask＋glow sprite，夜晚引擎 additive 疊）─────────
LW_, LH_ = 26, 60
def _glow(col, r=34):
    S = r * 2 + 1; Y, X = np.mgrid[0:S, 0:S]; d = np.hypot(X - r, Y - r) / r
    a = (np.clip(1 - d, 0, 1) ** 2 * 200).astype(np.uint8)
    g = np.zeros((S, S, 4), np.uint8); g[..., :3] = col; g[..., 3] = a; return g
def lamp_mushroom():
    W, H = LW_, LH_; img = canvas(W, H)
    part(img, m_ell(W, H, (5, 55, 21, 59)), WOOD)
    part(img, m_rr(W, H, (10, 20, 15, 57), 2), CREAM)
    cap = m_ell(W, H, (0, 4, 25, 26)) & ~m_rect(W, H, (0, 19, W, H))
    part(img, cap, RED)
    for (x, y, r) in [(6, 9, 1.6), (13, 7, 2), (19, 11, 1.6), (10, 14, 1.2)]:
        img[m_ell(W, H, (x - r, y - r, x + r, y + r)) & cap] = (255, 255, 255, 255)
    und = m_rr(W, H, (3, 18, 22, 22), 2); part(img, und, ramp('#ffe9a0', .6, .1, .25))
    em = np.zeros((H, W), bool); em[18:23, 3:23] = und[18:23, 3:23]
    return fin(img), em, _glow((255, 214, 140)), (12, 21)
def lamp_firefly():
    W, H = LW_, LH_; img = canvas(W, H)
    part(img, m_ell(W, H, (6, 55, 20, 59)), BARK)
    part(img, m_rect(W, H, (12, 8, 14, 57)), BARK)
    part(img, m_rect(W, H, (12, 6, 22, 8)), BARK)
    for y in range(9, 13): put(img, 20, y, OL)
    jar = m_rr(W, H, (13, 13, 25, 29), 3); part(img, jar, ramp('#cdeaf0', .5, .12, .3), spec=True)
    part(img, m_rect(W, H, (14, 11, 24, 13)), WOOD)
    em = np.zeros((H, W), bool)
    for (x, y) in [(16, 18), (21, 17), (18, 23), (22, 25), (16, 26)]:
        put(img, x, y, YEL[0]); put(img, x + 1, y, YEL[1]); em[y, x] = em[y, x + 1] = True
    return fin(img), em, _glow((255, 240, 150), 30), (19, 21)

CATALOG = [  # id, slot, zh, price(碎)/None, source, fn
 ('bed_leaf', 'bed', '葉仔床', 35, 'shop', bed_leaf), ('bed_cloud', 'bed', '雲朵床', 40, 'shop', bed_cloud),
 ('table_stump', 'table', '樹樁檯', 20, 'shop', table_stump), ('table_round', 'table', '格仔布圓檯', 25, 'shop', table_round),
 ('wall_shelf', 'wall', '小盆栽層架', 18, 'shop', wall_shelf), ('wall_frame', 'wall', '團絨相框', None, 'commission', wall_frame),
 ('rug_round', 'rug', '粉粉圓地氈', 22, 'shop', rug_round), ('rug_leaf', 'rug', '葉仔地氈', 15, 'shop', rug_leaf),
 ('win_curtain', 'window', '蕾絲窗簾', 25, 'shop', win_curtain), ('win_star', 'window', '星星窗', None, 'commission', win_star),
 ('lamp_mushroom', 'lamp', '蘑菇燈', None, 'visitor:mushroom_granny', lamp_mushroom), ('lamp_firefly', 'lamp', '螢火瓶燈', None, 'visitor:firefly_vendor', lamp_firefly),
]
