"""batch3b 訪客：蝸牛郵差／蘑菇婆婆／螢火小販 — idle／walk／happy 幀＋頭像＋擺設＋小道具。全部面向右，引擎 flip 向左。"""
import math
import numpy as np
from batch3b_paint import P, render, canvas, px, pxs, blush, OL, WHITE, BLUSH, add_outline, limit, paste
import batch3b_paint as _BP
EYE = OL
def eye(img, x, y, h=3, w=2, mode="open", c=OL): _BP.eye(img, x, y, h, w, mode, c)
def remap(img, a, b):
    m = np.all(img[..., :3] == a, -1) & (img[..., 3] == 255); img[m, :3] = b; return img

# ───── 共用色 ─────
CREAM = ((255, 242, 212), (246, 214, 166), (214, 168, 122))
CORAL = ((255, 196, 172), (240, 132, 122), (194, 86, 100))
NAVY = ((84, 104, 178), (48, 58, 118))
GOLD = (255, 214, 92)

# ═════════════════ 蝸牛郵差 snail postman ═════════════════
SN_W, SN_H = 44, 36; SN_PIV = (22, 33)


def snail(st):
    """st: dict(stretch, head_dx, head_dy, shell_dy, feel(左右觸鬚角度偏移), eyes, mouth, squash, hop)"""
    W, H = SN_W, SN_H
    s = st.get("stretch", 0); hd = st.get("head_dx", 0); hy = st.get("head_dy", 0); sd = st.get("shell_dy", 0)
    sq = st.get("squash", 0); hop = st.get("hop", 0)
    by = 29 - hop
    parts = []
    # 腳（身）：長橢圓
    parts.append(P("ell", (22 + s * .5, by + sq * .3, 17 + s, 4.6 - sq * .4), CREAM, z=1))
    # 尾尖
    parts.append(P("ell", (7 - s * .5, by + 1.5, 4, 2.6), CREAM, z=1))
    # 頸／頭
    hx, hyy = 33 + hd + s * .6, 19 + hy - hop + sq
    parts.append(P("ell", (hx - 1, hyy + 5.5, 5.4, 6.5), CREAM, z=2, line=False))
    parts.append(P("ell", (hx, hyy, 7.2, 7.0 - sq * .3), CREAM, z=3, line=False))
    # 殼
    sx, sy = 16 - s * .3, 18.5 + sd - hop + sq * .6
    parts.append(P("ell", (sx, sy, 11, 10.2 - sq * .5), CORAL, z=4))
    # 郵差帽（頂）＋帽簷
    cy = hyy - 6.2
    parts.append(P("ell", (hx - .5, cy, 6.6, 3.6), NAVY, z=6, clip=(0, 0, 99, int(cy + 1.5))))
    parts.append(P("rect", (int(hx - 6), int(cy + 1.5), int(hx + 7), int(cy + 2.5)), NAVY[1], z=6, flat=True))
    # 郵差袋（喺身前近頭）
    bx = int(25 + s * .5); bty = int(by - 6)
    parts.append(P("rect", (bx, bty, bx + 6, bty + 6), NAVY, z=5))
    img, pid = render(parts, W, H)
    # 殼螺旋
    spiral = []
    for k in range(0, 60):
        a = k * .23; r = 1.0 + a * 1.05
        if r > 8.6: break
        spiral.append((round(sx + 0.5 + r * math.cos(a + 2.2)), round(sy + .5 + r * .92 * math.sin(a + 2.2))))
    for x, y in spiral:
        if 0 <= y < H and 0 <= x < W and img[y, x, 3] == 255 and (abs(x - sx) ** 2 / 121 + abs(y - sy) ** 2 / 100) < .85:
            px(img, x, y, CORAL[2])
    # 殼高光
    px(img, int(sx - 6), int(sy - 6), WHITE); px(img, int(sx - 5), int(sy - 7), WHITE)
    # 帽徽 ＋ 袋扣 ＋ 信角 ＋ 斜孭帶
    px(img, int(hx), int(cy), GOLD)
    for i in range(7): px(img, bx + i, bty + 2, NAVY[1])
    px(img, bx + 3, bty + 3, GOLD)
    if st.get("letter", True):
        for i in range(3): px(img, bx + 1 + i, bty - 1, WHITE)
        px(img, bx + 4, bty - 1, CREAM[1]); px(img, bx + 1, bty - 2, WHITE); px(img, bx + 2, bty - 2, WHITE)
    for i in range(5):
        px(img, int(hx - 6 + i * .2) - i, int(hyy + 3 + i), NAVY[1]) if False else None
    # 帶：由袋右上去頸
    for k in range(4): px(img, bx + 6 + (k > 1), bty - 1 - k, NAVY[1])
    # 觸鬚（帽兩邊伸出）
    f = st.get("feel", 0)
    for side, base in ((-1, (hx - 4, cy - 2)), (1, (hx + 3, cy - 2))):
        ang = -90 + side * 28 + f * side
        for k in range(1, 5):
            x = base[0] + math.cos(math.radians(ang)) * k; y = base[1] + math.sin(math.radians(ang)) * k
            px(img, round(x), round(y), CREAM[2])
        tx = base[0] + math.cos(math.radians(ang)) * 5.5; ty = base[1] + math.sin(math.radians(ang)) * 5.5
        px(img, round(tx), round(ty), CREAM[0]); px(img, round(tx) + 1, round(ty), CREAM[1]); px(img, round(tx), round(ty) - 1, CREAM[0])
    # 面
    ex, ey = int(hx - 3), int(hyy - 1)
    em = st.get("eyes", "open")
    eye(img, ex, ey, 3, 2, em); eye(img, ex + 5, ey, 3, 2, em)
    blush(img, ex - 2, ey + 4); blush(img, ex + 7, ey + 4)
    mo = st.get("mouth", "w")
    mx, my = ex + 3, ey + 4
    if mo == "w": pxs(img, [(mx - 1, my), (mx, my + 1), (mx + 1, my)], EYE)
    elif mo == "open": pxs(img, [(mx - 1, my), (mx, my), (mx + 1, my), (mx - 1, my + 1), (mx + 1, my + 1)], EYE); px(img, mx, my + 1, BLUSH)
    elif mo == "dot": px(img, mx, my + 1, EYE)
    img = add_outline(img)
    return img


def snail_clips():
    idle = [dict(feel=0), dict(feel=4, head_dy=0), dict(feel=6, head_dy=-1, shell_dy=0), dict(feel=4, head_dy=-1, eyes="closed"),
            dict(feel=0, head_dy=0), dict(feel=-3, head_dy=0)]
    walk = [dict(stretch=0, feel=0), dict(stretch=1, head_dx=1, feel=3), dict(stretch=2, head_dx=2, feel=5, shell_dy=-1),
            dict(stretch=1, head_dx=1, feel=3, shell_dy=-1), dict(stretch=0, feel=0), dict(stretch=-1, head_dx=-1, feel=-2, shell_dy=1)]
    happy = [dict(squash=2, eyes="happy", mouth="open", feel=-6), dict(hop=3, eyes="happy", mouth="open", feel=10, head_dy=-1),
             dict(hop=5, eyes="happy", mouth="open", feel=14, head_dy=-1), dict(hop=3, eyes="happy", mouth="open", feel=10),
             dict(squash=2, eyes="happy", mouth="w", feel=-4), dict(eyes="happy", mouth="w", feel=4)]
    return {"idle": [snail(s) for s in idle], "walk": [snail(s) for s in walk], "happy": [snail(s) for s in happy]}


# ═════════════════ 蘑菇婆婆 mushroom granny ═════════════════
MG_W, MG_H = 38, 44; MG_PIV = (19, 41)
RED = ((255, 150, 150), (226, 86, 98), (170, 52, 78))
STEM = ((255, 246, 228), (240, 222, 196), (204, 178, 156))
LILAC = ((190, 168, 234), (130, 106, 186))
WOOD = (150, 100, 70)


def granny(st):
    W, H = MG_W, MG_H
    b = st.get("bob", 0); sq = st.get("squash", 0); lean = st.get("lean", 0); hop = st.get("hop", 0)
    cane_dx = st.get("cane", 0)
    y0 = -hop
    parts = []
    # 腳仔
    lf, rf = st.get("feet", (0, 0))
    parts.append(P("ell", (14.5 + lf, 39.5 + y0 + min(0, lf * 0) , 3.2, 2.0), STEM, z=1))
    parts.append(P("ell", (23.5 + rf, 39.5 + y0, 3.2, 2.0), STEM, z=1))
    # 身（莖）
    parts.append(P("ell", (19 + lean * .5, 30 + y0 + b * .5 + sq * .5, 9.2 + sq * .5, 9.4 - sq * .5), STEM, z=2))
    # 披肩
    parts.append(P("ell", (19 + lean * .5, 31 + y0 + b * .5 + sq * .6, 10.2 + sq * .5, 5.4), LILAC, z=3, clip=(0, int(29 + y0 + b * .5 + sq * .6), 99, 99)))
    # 菇帽
    cy = 15 + y0 + b + sq
    parts.append(P("ell", (19 + lean, cy, 17, 11.5 - sq * .3), RED, z=5, clip=(0, 0, 99, int(cy + 3))))
    parts.append(P("rect", (int(5 + lean), int(cy + 3), int(33 + lean), int(cy + 4)), RED[2], z=5, flat=True))
    # 枴杖
    parts.append(P("rect", (31 + cane_dx, int(26 + y0), 32 + cane_dx, 40 + min(0, -hop)), WOOD, z=6, flat=False))
    img, pid = render(parts, W, H)
    # 杖頭彎位
    pxs(img, [(30 + cane_dx, int(25 + y0)), (29 + cane_dx, int(25 + y0)), (31 + cane_dx, int(25 + y0)), (32 + cane_dx, int(25 + y0))], WOOD)
    # 菇帽白點
    cx = 19 + lean
    for (dx, dy, r) in ((-9, -2, 2), (1, -7, 2), (9, -2, 2), (-3, 0, 1), (5, 1, 1), (-13, 2, 1), (13, 1, 1)):
        for j in range(-r + 1, r):
            for i in range(-r + 1, r):
                if i * i + j * j <= (r - .5) ** 2 + .3: px(img, cx + dx + i, cy + dy + j, STEM[0])
        if r == 1: px(img, cx + dx, cy + dy, STEM[0])
    # 面
    fy = int(28 + y0 + b * .5 + sq * .3); fx = int(19 + lean * .5)
    em = st.get("eyes", "open")
    # 眼鏡圈（金）
    for gx in (fx - 5, fx + 2):
        pxs(img, [(gx, fy - 1), (gx + 1, fy - 1), (gx + 2, fy - 1), (gx - 1, fy), (gx + 3, fy), (gx - 1, fy + 1), (gx + 3, fy + 1), (gx, fy + 2), (gx + 1, fy + 2), (gx + 2, fy + 2)], GOLD)
    px(img, fx, fy, GOLD); px(img, fx + 1, fy, GOLD)
    if em == "open":
        px(img, fx - 4, fy, EYE); px(img, fx - 4, fy + 1, EYE); px(img, fx - 3, fy, EYE); px(img, fx - 3, fy + 1, EYE); px(img, fx - 4, fy, WHITE)
        px(img, fx + 3, fy, EYE); px(img, fx + 3, fy + 1, EYE); px(img, fx + 4, fy, EYE); px(img, fx + 4, fy + 1, EYE); px(img, fx + 3, fy, WHITE)
    elif em in ("closed", "happy"):
        if em == "happy":
            pxs(img, [(fx - 5 + 1, fy + 1), (fx - 4 + 1, fy), (fx - 3 + 1, fy + 1)], EYE); pxs(img, [(fx + 2 + 1, fy + 1), (fx + 3 + 1, fy), (fx + 4 + 1, fy + 1)], EYE)
        else:
            pxs(img, [(fx - 4, fy + 1), (fx - 3, fy + 1)], EYE); pxs(img, [(fx + 3, fy + 1), (fx + 4, fy + 1)], EYE)
    blush(img, fx - 7, fy + 3); blush(img, fx + 5, fy + 3)
    mo = st.get("mouth", "smile")
    if mo == "smile": pxs(img, [(fx - 1, fy + 4), (fx, fy + 5), (fx + 1, fy + 5), (fx + 2, fy + 4)], EYE)
    else: pxs(img, [(fx - 1, fy + 4), (fx, fy + 4), (fx + 1, fy + 4), (fx + 2, fy + 4), (fx, fy + 5), (fx + 1, fy + 5)], EYE); px(img, fx, fy + 5, BLUSH); px(img, fx + 1, fy + 5, BLUSH)
    # 披肩扣
    px(img, fx, int(31 + y0 + b * .5 + sq * .6) - 3 + 3, GOLD)
    return remap(add_outline(img), WHITE, STEM[0])


def granny_clips():
    idle = [dict(), dict(bob=0), dict(bob=1), dict(bob=1, eyes="closed"), dict(bob=1), dict(bob=0)]
    walk = [dict(feet=(-1, 1), cane=0), dict(feet=(0, 0), bob=1, cane=1), dict(feet=(1, -1), cane=1, lean=1),
            dict(feet=(0, 0), bob=1, cane=0, lean=1), dict(feet=(-1, 1), cane=-1), dict(feet=(0, 0), bob=1, cane=0)]
    happy = [dict(squash=2, eyes="happy", mouth="open"), dict(hop=2, eyes="happy", mouth="open"), dict(hop=3, eyes="happy", mouth="open", lean=1),
             dict(hop=2, eyes="happy", mouth="open", lean=-1), dict(squash=1, eyes="happy"), dict(eyes="happy")]
    return {"idle": [granny(s) for s in idle], "walk": [granny(s) for s in walk], "happy": [granny(s) for s in happy]}


# ═════════════════ 螢火小販 firefly vendor ═════════════════
FF_W, FF_H = 42, 42; FF_PIV = (21, 39)
TEAL = ((182, 240, 212), (104, 196, 172), (62, 140, 138))
WING = ((236, 248, 255), (196, 222, 246))
GLOWY = ((255, 252, 200), (255, 230, 110), (236, 178, 60))
BOX = ((206, 148, 100), (150, 98, 72))


def firefly(st):
    W, H = FF_W, FF_H
    fy = st.get("fly", 0); wing = st.get("wing", 0); sq = st.get("squash", 0); tilt = st.get("tilt", 0)
    y0 = -fy
    parts = []
    # 翼（後）
    wy = 15 + y0
    if wing == 0:
        parts.append(P("ell", (14, wy - 3, 5, 7), WING, z=0, line=False))
    elif wing == 1:
        parts.append(P("ell", (11, wy, 7, 4), WING, z=0, line=False))
    else:
        parts.append(P("ell", (13, wy + 3, 6, 4), WING, z=0, line=False))
    # 背包貨架（後面）
    parts.append(P("rect", (3, int(17 + y0), 13, int(29 + y0)), BOX, z=1))
    # 發光尾
    parts.append(P("ell", (12, 30 + y0 + sq * .3, 6.5, 5.5), GLOWY, z=2, glow=True))
    # 身
    parts.append(P("ell", (21, 27 + y0 + sq * .5, 8, 8 - sq * .4), TEAL, z=3))
    # 頭
    hx, hy = 25 + tilt, 17 + y0 + sq
    parts.append(P("ell", (hx, hy, 9, 8.2 - sq * .3), TEAL, z=4))
    # 腳仔（懸空時縮埋）
    for fx_ in (18, 23):
        parts.append(P("rect", (fx_, int(34 + y0), fx_ + 1, int(35 + y0)), TEAL[2], z=2, flat=True))
    img, pid = render(parts, W, H)
    # 架上瓶仔（兩個發光樽）
    for bx, by in ((4, int(18 + y0)), (8, int(22 + y0))):
        pxs(img, [(bx, by), (bx + 1, by), (bx + 2, by)], WING[1])
        pxs(img, [(bx, by + 1), (bx + 2, by + 1), (bx, by + 2), (bx + 2, by + 2)], WING[0]); px(img, bx + 1, by + 1, GLOWY[1]); px(img, bx + 1, by + 2, GLOWY[1])
    for i in range(11): px(img, 3 + i, int(21 + y0), BOX[1]) if i % 5 != 0 else None
    # 頭帶仔＋觸鬚
    for side, (ax, ay) in ((-1, (hx - 4, hy - 7)), (1, (hx + 3, hy - 7))):
        a = st.get("ant", 0)
        pts = [(ax + side * 0, ay - 1), (ax + side * 1, ay - 2), (ax + side * 1 + (a if side > 0 else -a) * 0, ay - 3)]
        pxs(img, pts, OL); px(img, pts[-1][0] + side, pts[-1][1] - 1, GLOWY[1]); px(img, pts[-1][0], pts[-1][1] - 1, GLOWY[0])
    # 面
    em = st.get("eyes", "open"); ex, ey = int(hx - 4), int(hy - 1)
    eye(img, ex, ey, 3, 2, em); eye(img, ex + 6, ey, 3, 2, em)
    blush(img, ex - 2, ey + 4); blush(img, ex + 8, ey + 4)
    mo = st.get("mouth", "w"); mx, my = ex + 4, ey + 4
    if mo == "w": pxs(img, [(mx - 1, my), (mx, my + 1), (mx + 1, my)], EYE)
    else: pxs(img, [(mx - 1, my), (mx, my), (mx + 1, my), (mx - 1, my + 1), (mx + 1, my + 1)], EYE); px(img, mx, my + 1, BLUSH)
    # 細翼（前）
    if wing == 0: parts2 = [P("ell", (19, wy - 4, 3.5, 6), WING, z=0)]
    elif wing == 1: parts2 = [P("ell", (17, wy - 1, 6, 3), WING, z=0)]
    else: parts2 = [P("ell", (18, wy + 2, 5, 3), WING, z=0)]
    fw, _ = render(parts2, W, H, outline=None)
    m = (fw[..., 3] == 255) & (pid < 0)
    img[m] = fw[m]
    img = remap(add_outline(img), WHITE, WING[0])
    return img


def ff_glow_mask(img):
    g = np.zeros_like(img); m = np.all(img[..., :3] == GLOWY[1], -1) | np.all(img[..., :3] == GLOWY[0], -1)
    g[m] = img[m]; return g


def firefly_clips():
    idle = [dict(fly=3, wing=0), dict(fly=4, wing=1), dict(fly=4, wing=2), dict(fly=3, wing=1, eyes="closed"), dict(fly=2, wing=0), dict(fly=2, wing=1)]
    walk = [dict(fly=5, wing=0, tilt=1), dict(fly=6, wing=1, tilt=1), dict(fly=6, wing=2, tilt=1), dict(fly=5, wing=1, tilt=1),
            dict(fly=4, wing=0, tilt=1), dict(fly=4, wing=1, tilt=1)]
    happy = [dict(fly=1, wing=2, squash=2, eyes="happy", mouth="open"), dict(fly=5, wing=0, eyes="happy", mouth="open"),
             dict(fly=8, wing=1, eyes="happy", mouth="open"), dict(fly=7, wing=2, eyes="happy", mouth="open"),
             dict(fly=4, wing=0, eyes="happy"), dict(fly=3, wing=1, eyes="happy")]
    return {"idle": [firefly(s) for s in idle], "walk": [firefly(s) for s in walk], "happy": [firefly(s) for s in happy]}
