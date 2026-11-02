# -*- coding: utf-8 -*-
"""第 8 批 工作場景：5 張背景 1x 層（sky／far／mid／fore）＋燈光描述。全 procedural。"""
import math
import numpy as np
from ws3_px import *

FOOT = (97, 300)      # 寵物腳底 art 座標（同 hd2d_v3 一樣喺 uiSafe 中段）

def sky_day(L, y0=-MY, y1=AH + MY, top='#6fa8e0', mid='#a9d2f2', low='#fbe6c4', seed=1, clouds=True):
    L.vgrad(-MX, y0, AW + MX - 1, y1, [(0, top), (.55, mid), (1, low)])
    if clouds:
        rnd = np.random.RandomState(seed)
        for i in range(5): cloud(L, rnd.randint(-20, 170), rnd.randint(y0 + 20, y0 + (y1 - y0) // 2), rnd.randint(30, 60), '#fdf6ea', seed + i)

# ================================================================ 郵局
def post():
    sky, far, mid, fore = Lyr(), Lyr(), Lyr(), Lyr()
    sky_day(sky, -MY, 230, seed=4)
    for i, (x, w, h) in enumerate([(-14, 30, 50), (14, 22, 70), (34, 30, 40), (62, 20, 58)]):   # 窗外屋頂＋鐘樓
        far_c = '#9db3c8'; sky.rect(x, 160 - h, x + w, 230, far_c); sky.poly([(x - 2, 160 - h), (x + w // 2, 150 - h), (x + w + 2, 160 - h)], sh(far_c, .85))
        for wy in range(166 - h, 225, 9):
            for wx in range(x + 4, x + w - 3, 7): sky.rect(wx, wy, wx + 2, wy + 3, '#e9f0f5')
    sky.rect(20, 70, 30, 95, '#8aa2b8'); sky.poly([(18, 70), (25, 58), (32, 70)], '#7b8fa6'); sky.ell(22, 75, 28, 81, '#f6efd8')
    # 牆
    far.vgrad(-MX, -MY, AW + MX - 1, 196, [(0, '#c9a77c'), (.25, '#ead6b0'), (1, '#e2c99c')])
    for y in range(70, 196, 12):                       # 牆紙直紋＋小花
        for x in range(-MX, AW + MX, 12):
            far.px(x + (y // 12) % 2 * 6, y + 4, '#d4b88a'); far.px(x + (y // 12) % 2 * 6 + 1, y + 5, '#cfae80')
    far.box(-MX, 196, AW + MX - 1, 236, '#7a4a2c', ol=False)    # 護牆板
    for x in range(-10, AW + MX, 26): far.box(x, 202, x + 20, 230, '#8a5634', ol=True)
    far.rect(-MX, 194, AW + MX - 1, 196, '#5c3420'); far.rect(-MX, 194, AW + MX - 1, 194, '#b07a4c')
    far.rect(-MX, 62, AW + MX - 1, 66, '#6b3f25'); far.rect(-MX, 66, AW + MX - 1, 66, '#a8744a')   # 天花線
    # 拱窗（挖空見 sky）
    far.box(10, 72, 78, 168, '#6b4129'); far.clear(16, 92, 72, 162); far.clear_ell(16, 76, 72, 108)
    far.rect(43, 78, 45, 162, '#6b4129'); far.rect(16, 120, 72, 121, '#6b4129'); far.rect(16, 120, 72, 120, '#a8744a')
    far.rect(8, 166, 80, 170, '#8a5634'); far.rect(8, 166, 80, 166, '#c08a58')
    for side, xs in ((0, range(4, 18)), (1, range(70, 84))):      # 窗簾
        for x in xs:
            k = 1 + .18 * math.sin((x - xs.start) * 1.1)
            far.rect(x, 70, x, 150 - (6 if side == 0 else 6) + int(4 * math.sin(x)), sh('#9c2f3a', k))
    far.rect(2, 66, 86, 70, '#c99a3c'); far.rect(2, 66, 86, 66, '#f1d08a')
    # 信格櫃（主角牆）
    X0, Y0, X1, Y1 = 92, 74, 186, 188
    far.box(X0, Y0, X1, Y1, '#6b3b22'); far.rect(X0 - 3, Y0 - 6, X1 + 3, Y0 - 1, '#7a4428'); far.rect(X0 - 3, Y0 - 6, X1 + 3, Y0 - 6, '#c08a58')
    far.rect(X0 + 30, Y0 - 16, X0 + 64, Y0 - 7, '#c99a3c'); far.rect(X0 + 31, Y0 - 15, X0 + 63, Y0 - 8, '#7a4428')
    letter(far, X0 + 41, Y0 - 14, '#f6d77a', w=12, h=5)                          # 金信封徽
    rnd = np.random.RandomState(7); cols = ['#f4ead2', '#f2c9c2', '#cfe3f0', '#f6e3a6', '#d9eccb', '#e8d7f2']
    cw, ch = 15, 18
    for r in range(6):
        for cidx in range(6):
            x, y = X0 + 3 + cidx * cw, Y0 + 3 + r * ch
            far.rect(x, y, x + cw - 3, y + ch - 3, '#3a1f12'); far.rect(x, y, x + cw - 3, y, '#26130a'); far.rect(x, y + ch - 3, x + cw - 3, y + ch - 3, '#8a5634')
            far.rect(x + 3, y + ch - 1, x + cw - 6, y + ch - 1, '#c99a3c')            # 小銅牌
            k = rnd.randint(0, 4)
            for j in range(k):
                c = cols[rnd.randint(len(cols))]; lx = x + 1 + j * 3; ly = y + 5 + rnd.randint(0, 4)
                far.rect(lx, ly, lx + 6, y + ch - 4, c); far.rect(lx, ly, lx + 6, ly, sh(c, 1.1)); far.rect(lx + 6, ly, lx + 6, y + ch - 4, sh(c, .78))
                if rnd.rand() < .3: far.px(lx + 3, ly + 2, '#c0392b')
    # 掛鐘＋郵票海報
    far.ell(54, 176, 76, 194, '#c99a3c'); far.ell(56, 178, 74, 192, '#fbf3df'); far.line([(65, 185), (65, 180)], '#3a2416'); far.line([(65, 185), (70, 186)], '#3a2416')
    far.box(18, 174, 46, 192, '#f3e6c8')
    for i, c in enumerate(['#d0574b', '#4f86b8', '#5c9a5a', '#d8a23c']):
        x = 21 + (i % 2) * 12; y = 176 + (i // 2) * 8
        far.rect(x, y, x + 9, y + 6, '#fffaf0'); far.rect(x + 1, y + 1, x + 8, y + 5, c); far.px(x + 4, y + 3, sh(c, 1.4))
    # 地板＋地氈
    planks_floor(mid, 236, AH + MY, '#9b6a43', seed=5)
    mid.rect(-MX, 236, AW + MX - 1, 238, '#4d2a18')
    mid.poly([(46, 268), (148, 268), (164, 336), (30, 336)], '#8e2733'); mid.poly([(50, 271), (144, 271), (158, 333), (36, 333)], '#a8323f')
    mid.line([(52, 274), (142, 274), (155, 330), (39, 330), (52, 274)], '#e0b04c')
    for i in range(9): x = 60 + i * 9.5; mid.px(x, 302, '#e0b04c'); mid.px(x + 1, 301, '#f2d27a')
    # 分信枱（左）
    mid.box(4, 238, 70, 248, '#8a5634'); mid.rect(2, 236, 72, 238, '#b07a4c'); mid.rect(2, 236, 72, 236, '#d9a46c')
    mid.box(8, 249, 14, 284, '#6b3b22'); mid.box(60, 249, 66, 284, '#6b3b22'); mid.rect(14, 262, 60, 264, '#5a3018')
    for i in range(4): letter(mid, 18 + i * 3, 228 - i * 2, ['#f4ead2', '#cfe3f0', '#f2c9c2', '#f6e3a6'][i], w=10, h=6)
    mid.box(52, 230, 64, 235, '#3a3f5a'); mid.rect(54, 231, 62, 233, '#5b6aa8')                     # 印台
    for i in range(3): mid.rect(6 + i * 4, 252 + i * 9, 58, 252 + i * 9, '#c99a3c') if False else None
    # 信袋＋包裹（右下 mid）
    mid.ell(160, 312, 190, 346, '#b48a5a'); mid.ell(162, 312, 188, 340, '#c99c68'); mid.rect(168, 306, 182, 314, '#9a6f45'); mid.rect(170, 304, 180, 306, '#7a5232')
    for i in range(3): letter(mid, 166 + i * 5, 300 - i * 3, ['#f4ead2', '#cfe3f0', '#f6e3a6'][i], w=8, h=5)
    mid.rect(172, 324, 178, 330, '#c99a3c'); mid.rect(173, 325, 177, 329, '#9c2f3a')
    # fore：吊燈、彩旗、角落盆栽、包裹堆
    lantern_hang(fore, 140, 66, 82, '#c99a3c'); lantern_hang(fore, 40, 66, 74, '#c99a3c')
    bunting(fore, -10, 205, 70, ['#d0574b', '#f2c94c', '#4f86b8', '#5c9a5a', '#f4ead2'], sag=10)
    plant(fore, 12, 368, 1.6, '#4f8a3a', '#a85a32', seed=3)
    for i, (x, y, w, h, c) in enumerate([(164, 352, 30, 22, '#c9955c'), (168, 336, 22, 16, '#d9aa70'), (172, 324, 14, 12, '#e8c28c')]):
        fore.box(x, y, x + w, y + h, c); fore.rect(x + w // 2 - 1, y, x + w // 2 + 1, y + h, '#9c2f3a'); fore.rect(x, y + h // 2, x + w, y + h // 2 + 1, '#9c2f3a')
    lights = dict(windows=[dict(rect=[16, 76, 72, 162], col='#fff1c8')], lamps=[dict(pos=[140, 92], col='#ffd27a', r=40), dict(pos=[40, 84], col='#ffd27a', r=26)],
                  rays=dict(src=[44, 110], toward=[110, 330], col='#ffe7b0', strength=.26, spread=.42),
                  ambient='#c8b4a0', floorPool=[[44, 250, 150, 340]], emissiveRects=[[16, 76, 72, 162, '#fff8e0', .2]], warm=True)
    return dict(sky=sky, far=far, mid=mid, fore=fore), lights

# ================================================================ 花園
def garden():
    sky, far, mid, fore = Lyr(), Lyr(), Lyr(), Lyr()
    sky_day(sky, -MY, 236, top='#5f9fe0', mid='#a6d4f4', low='#fff0cf', seed=11)
    # far：遠山＋樹＋玻璃溫室＋籬笆
    for i, (col, base, amp, f) in enumerate([('#9ec2c8', 196, 16, .05), ('#7fae8e', 212, 12, .08)]):
        for x in range(-MX, AW + MX):
            y = int(base - amp * (.6 + .4 * math.sin(x * f + i * 2)) - 6 * math.sin(x * .021 + i)); far.rect(x, y, x, 236, col)
            if x % 3 == 0: far.px(x, y, sh(col, 1.12))
    rnd = np.random.RandomState(12)
    for i in range(14):                                   # 圓樹
        x = rnd.randint(-10, 205); y = rnd.randint(176, 200); r = rnd.randint(8, 14); c = ['#4f8a3a', '#5e9b45', '#467c36'][i % 3]
        far.rect(x - 1, y, x + 1, y + r + 6, '#6b4a2c'); far.ell(x - r, y - r, x + r, y + r * .8, c); far.ell(x - r + 2, y - r + 1, x + r * .3, y, sh(c, 1.2)); far.ell(x - r * .2, y, x + r, y + r * .8, sh(c, .82))
    # 溫室
    gx0, gy0, gx1, gy1 = 8, 150, 82, 222
    far.poly([(gx0, gy0 + 20), ((gx0 + gx1) / 2, gy0), (gx1, gy0 + 20)], '#cfe6ec'); far.rect(gx0, gy0 + 20, gx1, gy1, '#bcdbe4')
    for x in range(gx0, gx1 + 1, 9):
        far.rect(x, gy0 + 20, x, gy1, '#f3f6f2')
        far.line([(x, gy0 + 20), ((gx0 + gx1) / 2, gy0)], '#f3f6f2') if abs(x - (gx0 + gx1) / 2) < 40 else None
    for y in range(gy0 + 20, gy1, 12): far.rect(gx0, y, gx1, y, '#f3f6f2')
    for i in range(10): x = rnd.randint(gx0 + 3, gx1 - 3); y = rnd.randint(gy0 + 30, gy1 - 4); far.ell(x - 3, y - 3, x + 3, y + 2, '#6fae5a'); far.px(x, y - 2, '#f2a0b8')
    for x in range(gx0 + 3, gx1, 9): far.line([(x, gy0 + 24), (x + 4, gy0 + 34)], '#ffffff')    # 玻璃反光
    far.rect(gx0 - 1, gy1, gx1 + 1, gy1 + 2, '#8a8f8a')
    # 籬笆
    for x in range(-MX, AW + MX, 7):
        far.rect(x, 214, x + 4, 240, '#f2e6d0'); far.poly([(x, 214), (x + 2, 210), (x + 4, 214)], '#f2e6d0'); far.rect(x + 4, 214, x + 4, 240, '#c9b89c')
    far.rect(-MX, 222, AW + MX - 1, 224, '#e2d4ba'); far.rect(-MX, 233, AW + MX - 1, 235, '#e2d4ba')
    # 拱門玫瑰（右）
    far.rect(150, 150, 154, 240, '#7a5a3a'); far.rect(186, 150, 190, 240, '#7a5a3a'); far.ell(150, 132, 190, 168, '#7a5a3a'); far.ell(154, 136, 186, 164, (0, 0, 0)); far.clear_ell(155, 137, 185, 163); far.clear(155, 150, 185, 240)
    far.vgrad(155, 140, 185, 240, [(0, '#a6d4f4'), (1, '#7fae8e')])
    for i in range(46):
        a = rnd.uniform(math.pi, 2 * math.pi) if i < 26 else rnd.uniform(0, 1); r = 20
        if i < 26: x, y = 170 + math.cos(a) * r, 150 + math.sin(a) * 17
        else: x, y = rnd.choice([152, 188]) + rnd.randint(-3, 3), rnd.randint(150, 236)
        far.ell(x - 2, y - 2, x + 2, y + 1, '#4f8a3a'); 
        if rnd.rand() < .5: far.rect(x - 1, y - 1, x, y, '#e86a8a'); far.px(x, y - 1, '#ffb0c4')
    # mid：草地、石徑、花圃
    mid.vgrad(-MX, 240, AW + MX - 1, AH + MY - 1, [(0, '#7fb65a'), (.4, '#6aa44a'), (1, '#4f8a3a')])
    for i in range(1400):
        x = rnd.randint(-MX, AW + MX); y = rnd.randint(242, AH + MY); c = rnd.choice(['#8cc463', '#5b9640', '#9bd070'])
        mid.px(x, y, c); 
        if rnd.rand() < .3: mid.px(x, y - 1, sh(c, 1.1))
    for i, (x, y, w) in enumerate([(92, 246, 12), (96, 260, 15), (90, 278, 18), (100, 330, 20), (88, 352, 22), (104, 376, 24), (90, 400, 26)]):
        mid.ell(x - w / 2, y - w / 5, x + w / 2, y + w / 5, '#b9b1a0'); mid.ell(x - w / 2 + 1, y - w / 5, x + w / 2 - 2, y + w / 7, '#d6cfbe'); mid.px(x - 2, y - 1, '#ece6d6')
    for side in (0, 1):                                   # 花圃
        x0 = 6 if side == 0 else 124; x1 = 70 if side == 0 else 190
        mid.box(x0, 252, x1, 262, '#8a5a36'); mid.rect(x0 + 1, 246, x1 - 1, 252, '#5a3a22')
        for i in range(24):
            x = rnd.randint(x0 + 2, x1 - 2); y = rnd.randint(232, 250); c = ['#e86a8a', '#f2c94c', '#f2f2f2', '#b48ae8', '#ff9a5a'][rnd.randint(5)]
            mid.line([(x, y + 2), (x, 252)], '#3f7a32'); mid.ell(x - 2, y - 2, x + 2, y + 2, c); mid.px(x, y, '#f9e27a'); mid.px(x - 1, y - 1, sh(c, 1.25))
            mid.px(x + 1, y + 5, '#5e9b45'); mid.px(x + 2, y + 5, '#5e9b45')
    # 工具：鋤頭靠籬、竹籃
    mid.line([(178, 226), (186, 270)], '#8a6038', 2); mid.poly([(174, 220), (184, 222), (180, 228)], '#9aa0a8')
    mid.ell(10, 320, 40, 340, '#b88a4a'); mid.ell(12, 316, 38, 330, '#d6a860'); mid.rect(12, 322, 38, 324, '#8a5a36')
    for i in range(5): mid.ell(14 + i * 5, 314, 18 + i * 5, 320, ['#e86a8a', '#f2c94c', '#ff9a5a'][i % 3])
    # fore：角落大葉＋花、頂部花枝
    for (x, y, s, sd) in ((-6, 400, 2.2, 1), (200, 404, 2.0, 2)):
        r2 = np.random.RandomState(sd)
        for i in range(16):
            a = r2.uniform(-2.9, -.2); r = r2.uniform(14, 34) * s / 2; lx, ly = x + math.cos(a) * r, y + math.sin(a) * r
            c = ['#3f7a32', '#4f8a3a', '#5e9b45'][i % 3]; fore.poly([(x, y), (lx - 4, ly), (lx, ly - 5), (lx + 4, ly)], c); fore.line([(x, y), (lx, ly - 2)], sh(c, 1.3))
            if i % 4 == 0: fore.ell(lx - 3, ly - 6, lx + 3, ly, '#f2a0b8'); fore.px(lx, ly - 3, '#fff2c8')
    pts = [(205, 64), (170, 74), (140, 70), (118, 80)]
    fore.line(pts, '#6b4a2c', 3)
    for i in range(24):
        t = rnd.rand(); x = 205 - t * 90; y = 64 + t * 16 + rnd.randint(-8, 10); fore.ell(x - 3, y - 2, x + 3, y + 2, ['#ffd0dc', '#ffb0c4', '#fff0f4'][i % 3]); fore.px(x, y, '#e86a8a')
    lights = dict(sun=[175, -20], rays=dict(src=[200, -30], toward=[80, 330], col='#fff0c0', strength=.24, spread=.5),
                  ambient='#ffffff', dapple=True, lamps=[], emissiveRects=[], warm=False)
    return dict(sky=sky, far=far, mid=mid, fore=fore), lights

# ================================================================ 瞭望台（日／夜）
def tower(night=False):
    sky, far, mid, fore = Lyr(), Lyr(), Lyr(), Lyr()
    if night:
        sky.vgrad(-MX, -MY, AW + MX - 1, 250, [(0, '#0b1230'), (.5, '#1a2a5a'), (1, '#3a4a7e')])
        rnd = np.random.RandomState(21)
        for i in range(900):                                # 銀河帶
            t = rnd.rand(); x = -20 + t * 240 + rnd.normal(0, 10); y = 40 + t * 150 + rnd.normal(0, 14)
            sky.px(x, y, mixc('#3a4a7e', '#c8c0ff', rnd.uniform(.1, .5)))
        stars_px(sky, (-MX, -MY, AW + MX, 230), 260, 22)
        sky.ell(130, 58, 154, 82, '#fff4d6'); sky.ell(136, 58, 158, 78, '#1a2a5a'); sky.ell(128, 56, 156, 84, (0, 0, 0)) if False else None
    else:
        sky.vgrad(-MX, -MY, AW + MX - 1, 250, [(0, '#4f8fd8'), (.6, '#9ccbf0'), (1, '#fde8c8')])
        for i in range(4): cloud(sky, [-10, 60, 120, 20][i], [90, 70, 120, 150][i], [50, 40, 60, 36][i], '#fdf6ea', 30 + i)
    # far：雲海＋山峰
    sea = '#2c3b6a' if night else '#f2f0ec'; peak = '#24305a' if night else '#8ea4c4'
    for j, (bx, h, w) in enumerate([(10, 46, 46), (70, 30, 40), (150, 56, 54), (196, 34, 40)]):
        far.poly([(bx - w, 220), (bx, 220 - h), (bx + w, 220)], peak); far.poly([(bx, 220 - h), (bx + w * .3, 220 - h * .55), (bx + 4, 220 - h * .6), (bx - w * .25, 220 - h * .6)], '#e9eef8' if not night else '#4a5a8a')
    rnd = np.random.RandomState(23)
    for i in range(30):
        x = rnd.randint(-20, 220); y = rnd.randint(196, 226); r = rnd.randint(6, 16)
        far.ell(x - r, y - r * .5, x + r, y + r * .4, sh(sea, rnd.uniform(.92, 1.08)))
    far.rect(-MX, 214, AW + MX - 1, 236, sea)
    far.rect(160, 172, 166, 214, '#3a4470' if night else '#b0b8cc'); far.poly([(158, 172), (163, 162), (168, 172)], '#3a4470' if night else '#a0a8bc')   # 遠塔
    if night: far.px(163, 166, '#ffd27a'); far.px(163, 167, '#ffd27a')
    # mid：石台＋欄杆＋大望遠鏡
    stone = '#5a5f7e' if night else '#c8b89c'
    mid.rect(-MX, 244, AW + MX - 1, AH + MY - 1, sh(stone, .9))
    for y in range(248, AH + MY, 14):
        off = (y // 14) % 2 * 9
        for x in range(-MX + off, AW + MX, 18):
            mid.box(x + 1, y + 1, x + 16, y + 12, sh(stone, 1.0 + .05 * ((x * 7 + y) % 3 - 1)), ol=False)
    mid.rect(-MX, 244, AW + MX - 1, 246, sh(stone, .6))
    rail = '#4a4f6e' if night else '#b0a084'
    mid.box(-MX, 206, AW + MX - 1, 212, sh(rail, 1.05)); mid.box(-MX, 236, AW + MX - 1, 244, sh(rail, .95))
    for x in range(-8, AW + MX, 14):                   # 瓶形欄杆
        mid.rect(x, 213, x + 5, 235, rail); mid.ell(x - 1, 218, x + 6, 228, sh(rail, 1.1)); mid.rect(x + 5, 213, x + 5, 235, sh(rail, .7))
    gold = '#c99a3c'
    # 大望遠鏡（右，裝飾場景件）
    mid.line([(150, 244), (160, 196)], '#6b4a2c', 2); mid.line([(178, 244), (162, 196)], '#6b4a2c', 2); mid.line([(164, 246), (162, 196)], '#5a3a22', 2)
    mid.box(156, 190, 168, 200, '#7a5232')
    tube = [(132, 150), (186, 186)]
    for i in range(7):
        t = i / 6; r = 6 - t * 2.6
        cx, cy = 132 + 54 * t, 150 + 36 * t; mid.ell(cx - r, cy - r, cx + r, cy + r, gold if i % 3 else '#a07a2c')
    mid.line([(132, 150), (186, 186)], '#f2d27a'); mid.ell(124, 142, 136, 156, '#a07a2c'); mid.ell(126, 144, 134, 154, '#1a2240' if night else '#3a4a7e'); mid.px(128, 146, '#cfe0ff')
    mid.box(156, 176, 164, 182, '#7a5232')
    # 星盤小枱（左）
    mid.box(14, 262, 50, 268, '#7a5232'); mid.box(18, 268, 22, 290, '#5a3a22'); mid.box(42, 268, 46, 290, '#5a3a22')
    mid.rect(18, 256, 46, 262, '#e9dcbc'); mid.rect(19, 257, 45, 261, '#2a3a6a'); mid.px(24, 258, '#ffffff'); mid.px(32, 260, '#ffffff'); mid.px(40, 258, '#f6d77a'); mid.line([(24, 258), (32, 260), (40, 258)], '#8aa2d8')
    # fore：石拱框＋旗＋盆
    arch = '#3a3f5e' if night else '#a89878'
    fore.rect(-MX, -MY, 6, AH + MY - 1, arch); fore.rect(AW - 7, -MY, AW + MX - 1, AH + MY - 1, arch)
    for y in range(-MY, AH + MY, 16):
        fore.rect(-MX, y, 6, y, sh(arch, .7)); fore.rect(AW - 7, y + 8, AW + MX - 1, y + 8, sh(arch, .7))
    fore.rect(6, -MY, 7, AH + MY - 1, sh(arch, 1.25)); fore.rect(AW - 8, -MY, AW - 8, AH + MY - 1, sh(arch, .6))
    for x in range(-MX, AW + MX):
        t = (x - AW / 2) / (AW / 2 + 8); y = int(76 + 26 * (t * t) - 26)
        fore.rect(x, -MY, x, y, arch); fore.px(x, y, sh(arch, 1.25)); fore.px(x, y - 3, sh(arch, .7))
    fore.rect(90, 46, 104, 58, sh(arch, 1.12)); fore.px(97, 52, gold)   # 拱心石
    plant(fore, 18, 380, 1.5, '#3f6a4a' if night else '#4f8a3a', '#7a5a8a' if night else '#a85a32', flower='#f6d77a', seed=9)
    fore.box(166, 360, 192, 384, '#7a5232'); fore.rect(168, 352, 190, 360, '#e9dcbc'); fore.rect(170, 350, 172, 362, '#c9a87a'); fore.rect(186, 350, 188, 362, '#c9a87a')
    if night:
        lights = dict(moon=[142, 70], rays=dict(src=[142, 70], toward=[97, 300], col='#9fb6ff', strength=.18, spread=.5),
                      ambient='#6a78b8', lamps=[dict(pos=[163, 167], col='#ffd27a', r=10), dict(pos=[97, 250], col='#8aa0ff', r=90, bulb=False)], emissiveRects=[[130, 58, 154, 82, '#fff4d6', .9]], warm=False, night=True)
    else:
        lights = dict(sun=[30, -30], rays=dict(src=[20, -40], toward=[120, 330], col='#fff3d0', strength=.16, spread=.45), ambient='#ffffff', lamps=[], emissiveRects=[], warm=False)
    return dict(sky=sky, far=far, mid=mid, fore=fore), lights

# ================================================================ 廚房
def kitchen():
    sky, far, mid, fore = Lyr(), Lyr(), Lyr(), Lyr()
    sky_day(sky, -MY, 236, top='#78b0e4', mid='#b4dcf4', low='#fff2d6', seed=41)
    for i in range(10): x = 14 + i * 7; sky.ell(x - 6, 140, x + 6, 156, '#6fae5a'); sky.px(x, 142, '#f2a0b8')
    # 牆：上灰泥、下花磚
    far.vgrad(-MX, -MY, AW + MX - 1, 150, [(0, '#c7a27a'), (.3, '#f0e2c6'), (1, '#e8d6b4')])
    for y in range(150, 238, 8):
        for x in range(-MX, AW + MX, 8):
            far.rect(x, y, x + 7, y + 7, '#eef2f4'); far.rect(x, y + 7, x + 7, y + 7, '#b8c4cc'); far.rect(x + 7, y, x + 7, y + 7, '#b8c4cc')
            if (x // 8 + y // 8) % 2 == 0: far.px(x + 3, y + 3, '#4f7fb8'); far.px(x + 2, y + 3, '#7fa6d4'); far.px(x + 4, y + 3, '#7fa6d4'); far.px(x + 3, y + 2, '#7fa6d4'); far.px(x + 3, y + 4, '#7fa6d4')
    far.rect(-MX, 62, AW + MX - 1, 68, '#6b4a2c'); far.rect(-MX, 68, AW + MX - 1, 68, '#a8744a')
    for x in range(-MX, AW + MX, 30): far.box(x, 62, x + 6, 72, '#5a3a22')       # 樑
    # 窗（降低，讓位俾銅鍋）
    far.box(14, 94, 78, 148, '#f2f2ea'); far.clear(18, 98, 74, 144); far.rect(45, 98, 47, 144, '#f2f2ea'); far.rect(18, 120, 74, 121, '#f2f2ea')
    far.rect(10, 148, 82, 152, '#d6cfbe'); far.rect(10, 148, 82, 148, '#ffffff')
    for i in range(3): plant(far, 24 + i * 22, 140, .7, '#4f8a3a', '#b5653a', flower=['#e86a8a', '#f2c94c', '#ffffff'][i], seed=50 + i)
    # 銅鍋掛架（窗上）
    far.rect(8, 74, 84, 75, '#6b4a2c'); far.rect(8, 74, 8, 78, '#6b4a2c'); far.rect(84, 74, 84, 78, '#6b4a2c')
    for i, (x, r) in enumerate([(18, 5), (34, 7), (52, 5), (68, 6)]):
        far.line([(x, 75), (x, 78)], '#4a3a2a'); far.ell(x - r, 78, x + r, 78 + r * 1.5, '#b86a3c'); far.ell(x - r + 2, 79, x, 77 + r, '#e09a6a'); far.rect(x + r, 81, x + r + 4, 82, '#8a4a2a')
    # 層架＋罐（窗同煙罩之間）
    for sy in (104, 132):
        far.box(84, sy, 124, sy + 3, '#8a5634'); far.poly([(86, sy + 4), (92, sy + 4), (86, sy + 10)], '#6b3b22'); far.poly([(116, sy + 4), (122, sy + 4), (122, sy + 10)], '#6b3b22')
        rnd = np.random.RandomState(sy)
        x = 86
        while x < 116:
            w = rnd.randint(6, 9); h = rnd.randint(9, 16); c = ['#cfe3f0', '#f2c9a0', '#d9eccb', '#f6e3a6', '#e8b8a8'][rnd.randint(5)]
            far.box(x, sy - h, x + w, sy - 1, c); far.rect(x, sy - h - 2, x + w, sy - h, '#9a6f45'); far.rect(x + 2, sy - h + 3, x + w - 2, sy - h + 6, '#fffaf0')
            far.px(x + 1, sy - h + 1, '#ffffff'); x += w + 3
    # mid：地磚
    for y in range(238, AH + MY, 10):
        for x in range(-MX, AW + MX, 10):
            c = '#e8dcc4' if (x // 10 + y // 10) % 2 == 0 else '#8a5a3e'; mid.rect(x, y, x + 9, y + 9, c); mid.rect(x, y, x + 9, y, sh(c, 1.08)); mid.rect(x + 9, y, x + 9, y + 9, sh(c, .82))
    mid.rect(-MX, 236, AW + MX - 1, 238, '#5a3a22')
    # 灶（右）：磚爐＋火口
    mid.box(118, 168, 192, 252, '#9c4a32')
    for y in range(170, 252, 6):
        for x in range(118 + (y // 6) % 2 * 6, 192, 12): mid.rect(x, y, x + 10, y + 4, sh('#9c4a32', 1.0 + .07 * ((x + y) % 3 - 1))); mid.rect(x, y + 5, x + 11, y + 5, '#6b2a1a')
    mid.box(114, 164, 196, 170, '#6b3b22'); mid.rect(114, 164, 196, 164, '#c08a58')
    mid.ell(136, 214, 174, 250, '#2a120a'); mid.rect(136, 232, 174, 250, '#2a120a')
    for i in range(16):
        x = 140 + i * 2; h = 6 + int(6 * abs(math.sin(i * 1.7))); mid.rect(x, 248 - h, x + 1, 248, '#ff9a3a'); mid.rect(x, 248 - h // 2, x + 1, 248, '#ffe08a')
    for x in range(140, 172, 5): mid.box(x, 246, x + 3, 249, '#5a3a22', ol=False)
    mid.rect(130, 196, 182, 200, '#3a3a40'); mid.rect(130, 196, 182, 196, '#7a7a84')       # 灶面鐵板
    mid.rect(108, 120, 196, 160, (0, 0, 0)) if False else None
    mid.poly([(134, 80), (186, 80), (196, 160), (126, 160)], '#b88a5a'); mid.rect(126, 156, 196, 160, '#8a5a36'); mid.rect(134, 80, 186, 82, '#d9aa70')   # 煙罩
    for x in range(140, 186, 8): mid.line([(x, 86), (x - 3, 154)], '#a37a4c')
    # 枱（左）
    mid.box(0, 232, 70, 240, '#d9b88a'); mid.rect(-MX, 230, 72, 232, '#f0d6aa')
    mid.box(4, 241, 66, 282, '#8a5634')
    for x in (6, 36): mid.box(x, 246, x + 26, 276, '#9a6440'); mid.rect(x + 12, 258, x + 14, 262, '#e0b04c')
    mid.box(14, 222, 40, 229, '#c9955c'); mid.ell(18, 218, 26, 226, '#e86a3a'); mid.ell(28, 220, 36, 227, '#f2c94c'); mid.rect(31, 216, 32, 220, '#4f8a3a')
    mid.ell(44, 220, 58, 230, '#f2f2ea'); mid.ell(46, 222, 56, 228, '#f6e3a6')
    # 小枱凳（中後）
    mid.box(82, 248, 112, 254, '#a8744a'); mid.box(84, 254, 87, 270, '#7a4a2c'); mid.box(107, 254, 110, 270, '#7a4a2c')
    mid.ell(88, 242, 98, 249, '#f2f2ea'); mid.ell(100, 243, 108, 249, '#c0392b')
    # fore：吊蒜／香草、菜籃、凳
    for i, x in enumerate((8, 18, 28)):
        fore.line([(x, 62), (x, 76 + i * 4)], '#8a6038')
        for j in range(3): fore.ell(x - 3, 74 + i * 4 + j * 5, x + 3, 80 + i * 4 + j * 5, '#f2ead6' if i != 1 else '#4f8a3a'); fore.px(x, 76 + i * 4 + j * 5, '#c9b89c' if i != 1 else '#7fb65a')
    fore.ell(158, 378, 200, 410, '#b88a4a'); fore.ell(160, 368, 198, 392, '#d6a860'); fore.rect(160, 380, 198, 382, '#8a5a36')
    for (x, y, c) in ((166, 366, '#e86a3a'), (176, 362, '#f2c94c'), (186, 366, '#4f8a3a'), (171, 372, '#c0392b'), (182, 372, '#b48ae8')): fore.ell(x - 5, y - 4, x + 5, y + 4, c); fore.px(x - 2, y - 2, sh(c, 1.4))
    fore.box(-4, 372, 24, 380, '#a8744a'); fore.box(-2, 380, 2, 420, '#7a4a2c'); fore.box(18, 380, 22, 420, '#7a4a2c')
    lights = dict(windows=[dict(rect=[18, 98, 74, 144], col='#fff1c8')], lamps=[dict(pos=[155, 236], col='#ff9a3a', r=46)],
                  rays=dict(src=[46, 120], toward=[100, 320], col='#ffe7b0', strength=.3, spread=.42), ambient='#c8b8a8',
                  emissiveRects=[[18, 98, 74, 144, '#fff8e0', .2], [140, 232, 172, 249, '#ffb050', 1.0]], warm=True)
    return dict(sky=sky, far=far, mid=mid, fore=fore), lights

SCENES = {'post': post, 'garden': garden, 'tower_day': lambda: tower(False), 'tower_night': lambda: tower(True), 'kitchen': kitchen}
