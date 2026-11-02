# -*- coding: utf-8 -*-
"""第 8 批 工作場景：道具動畫、Lv3 擺設、Lv5 職業帽、產品 icon、工作 clip 道具疊層、粒子。全部 1x 像素畫（alpha 0/255），出 @3x 用 nearest。"""
import math
import numpy as np
from PIL import Image
from ws3_px import Lyr, sh, hx, mixc, outline, binarize

def C(w, h): return Lyr(w, h, 0, 0)
INK = '#2a1a14'
def ol(L, col=INK): L.im = outline(L.im, col); L.d = __import__('PIL.ImageDraw', fromlist=['Draw']).Draw(L.im); return L
def star(L, cx, cy, r, col, ri=None):
    ri = ri or r * .45; pts = []
    for i in range(10): a = -math.pi / 2 + i * math.pi / 5; rr = r if i % 2 == 0 else ri; pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    L.poly(pts, col)
def spark(L, x, y, r, col):
    L.line([(x - r, y), (x + r, y)], col); L.line([(x, y - r), (x, y + r)], col)
    if r >= 3: L.px(x - 1, y - 1, col); L.px(x + 1, y + 1, col); L.px(x + 1, y - 1, col); L.px(x - 1, y + 1, col)
def letter_s(L, x, y, w=8, h=5, col='#f6eedc', seal='#c0392b'):
    L.rect(x, y, x + w, y + h, col); L.line([(x, y), (x + w / 2, y + h * .6), (x + w, y)], sh(col, .7)); L.rect(x, y + h, x + w, y + h, sh(col, .65))
    if seal: L.rect(x + w // 2 - 1, y + h // 2, x + w // 2, y + h // 2 + 1, seal)
def heart(L, cx, cy, r, col):
    L.ell(cx - r, cy - r, cx, cy, col); L.ell(cx, cy - r, cx + r, cy, col); L.poly([(cx - r, cy - r / 2), (cx + r, cy - r / 2), (cx, cy + r)], col)

# ================================================================ 可撳道具（8 個，每個 4–6 幀）
# 每個回傳 dict(frames=[Lyr…], glow=[None|強度 mask 用 bright 色]，size, anchor(底中), pos(art 腳底), hit)
def prop_mailbox():
    W, H = 44, 64; fr = []
    for f in range(6):
        L = C(W, H); x0, y0 = 10, 28
        L.box(x0 + 2, y0 + 30, x0 + 20, y0 + 34, '#3a2a2a')                     # 底座
        L.rect(x0, y0 + 6, x0 + 22, y0 + 30, '#c4382e'); L.ell(x0, y0 - 2, x0 + 22, y0 + 14, '#c4382e')
        L.rect(x0, y0 + 6, x0 + 3, y0 + 30, '#e05a48'); L.rect(x0 + 19, y0 + 6, x0 + 22, y0 + 30, '#8a2420'); L.ell(x0 + 3, y0, x0 + 12, y0 + 8, '#e86a58')
        L.rect(x0 - 1, y0 + 6, x0 + 23, y0 + 7, '#c99a3c'); L.rect(x0 - 1, y0 + 6, x0 + 23, y0 + 6, '#f2d27a')
        L.rect(x0 + 7, y0 + 18, x0 + 15, y0 + 22, '#f2d27a'); L.rect(x0 + 8, y0 + 19, x0 + 14, y0 + 21, '#c4382e'); L.px(x0 + 11, y0 + 20, '#f2d27a')   # 徽
        flap = {0: 0, 1: 2, 2: 3, 3: 3, 4: 1, 5: 0}[f]
        L.rect(x0 + 4, y0 + 10, x0 + 18, y0 + 13, '#2a1210')
        L.rect(x0 + 3, y0 + 9 - flap, x0 + 19, y0 + 9 - flap + 1, '#3a3a40'); L.rect(x0 + 3, y0 + 9 - flap, x0 + 19, y0 + 9 - flap, '#8a8a94')
        if f == 1: letter_s(L, x0 + 7, y0 + 7, 8, 4)
        if f == 2: letter_s(L, x0 + 12, y0 - 6, 9, 5); L.px(x0 + 10, y0 - 1, '#fff2c8')
        if f == 3: letter_s(L, x0 + 22, y0 - 20, 9, 5); spark(L, x0 + 18, y0 - 10, 2, '#fff2c8'); L.px(x0 + 14, y0 - 3, '#fff2c8')
        if f == 4: letter_s(L, x0 + 30, y0 - 27, 8, 5); spark(L, x0 + 25, y0 - 17, 2, '#fff2c8'); spark(L, x0 + 18, y0 - 8, 1, '#fff2c8')
        if f == 5: spark(L, x0 + 33, y0 - 26, 2, '#fff2c8')
        fr.append(ol(L))
    return dict(frames=fr, size=[W, H], anchor=[22, 63], pos=[160, 300], hit=[146, 262, 176, 302], fps=12, loop=False,
                tap='寄信：信箱口打開，一封信飛出去（純視覺）', zh='信箱')
STAMP_INK = ['#c0392b', '#2f6fb0', '#3f8a4a', '#c99a3c']
def prop_stamp(ink):
    W, H = 28, 30; fr = []
    for f in range(5):
        L = C(W, H); press = {0: 0, 1: 4, 2: 0, 3: 0, 4: 0}[f]; by = 10 + press
        if f >= 2: L.rect(6, 25, 19, 27, ink); L.rect(8, 25, 17, 25, sh(ink, 1.3)); L.px(12, 26, '#fff6e0')            # 印痕
        L.rect(4, 27, 22, 28, '#e9dcbc') if f < 2 else None
        L.box(8, by + 8, 18, by + 12, ink)                                     # 印面（印色）
        L.box(9, by + 4, 17, by + 8, '#8a5634'); L.rect(12, by - 4, 14, by + 4, '#a8744a'); L.ell(9, by - 9, 17, by - 2, '#c08a58'); L.ell(10, by - 8, 13, by - 5, '#e0b07c')
        if f == 2: spark(L, 4, 18, 2, '#fff2c8'); spark(L, 22, 16, 2, '#fff2c8')
        if f == 3: spark(L, 3, 12, 1, '#fff2c8'); spark(L, 24, 10, 2, sh(ink, 1.5))
        fr.append(ol(L))
    return fr
def prop_stamp_all():
    rows = [prop_stamp(c) for c in STAMP_INK]
    return dict(frames=rows[0], variants=dict(ink=STAMP_INK, rows=rows), size=[28, 30], anchor=[14, 29], pos=[30, 237], hit=[18, 210, 44, 240], fps=12, loop=False,
                tap='印章：按落去，換下一隻印色（紅→藍→綠→金循環，純視覺）', zh='印章')
def prop_flower():
    W, H = 28, 36; fr = []; pet = '#ff7aa0'
    for f in range(6):
        L = C(W, H); L.line([(14, 34), (14, 16)], '#3f7a32'); L.ell(6, 24, 13, 28, '#4f8a3a'); L.ell(15, 20, 22, 24, '#5e9b45'); L.px(9, 25, '#7fb65a')
        L.ell(9, 33, 19, 36, '#5a3a22')
        if f == 0: L.ell(11, 9, 17, 17, '#5e9b45'); L.ell(12, 8, 16, 13, pet)
        elif f == 1: L.ell(9, 8, 19, 17, pet); L.ell(11, 10, 17, 16, sh(pet, .8)); L.ell(12, 13, 16, 18, '#5e9b45')
        else:
            r = {2: 7, 3: 9, 4: 9, 5: 8}[f]
            for i in range(6):
                a = i * math.pi / 3 + .3; cx, cy = 14 + math.cos(a) * r * .6, 12 + math.sin(a) * r * .6
                L.ell(cx - r * .45, cy - r * .45, cx + r * .45, cy + r * .45, pet if i % 2 else sh(pet, 1.12))
            L.ell(11, 9, 17, 15, '#f9d24a'); L.px(13, 11, '#fff6c0'); L.px(14, 12, '#e0a020')
        if f == 3: spark(L, 3, 5, 2, '#fff6c0'); spark(L, 25, 8, 2, '#fff6c0'); spark(L, 22, 1, 1, '#ffffff')
        if f == 4: spark(L, 2, 10, 1, '#fff6c0'); spark(L, 26, 3, 2, '#ffffff'); spark(L, 6, 1, 2, '#fff6c0')
        fr.append(ol(L))
    return dict(frames=fr, size=[W, H], anchor=[14, 35], pos=[146, 296], hit=[132, 258, 160, 298], fps=12, loop=False,
                tap='朵花：即刻開花＋閃光（純視覺；過幾秒慢慢合返）', zh='花')
def prop_bucket():
    W, H = 40, 40; fr = []; wat = '#7cc4f0'
    for f in range(5):
        L = C(W, H); tilt = {0: 0, 1: 2, 2: 0, 3: 0, 4: 0}[f]
        L.poly([(10, 22 - tilt), (28, 22 + tilt), (26, 38), (12, 38)], '#8aa0b0'); L.rect(10, 22 - tilt, 28, 23, '#c8d4dc')
        L.line([(12, 30), (26, 30)], '#6a7f90'); L.line([(11, 26), (27, 26)], '#6a7f90')
        L.line([(10, 22), (14, 14), (24, 14), (28, 22)], '#5a6470')
        L.ell(12, 20, 26, 24, wat); L.px(16, 21, '#d8f0ff')
        drops = {1: [(14, 14), (22, 12), (18, 10)], 2: [(8, 6), (30, 4), (18, 1), (12, 10), (26, 9)], 3: [(5, 14), (33, 12), (20, 8)], 4: []}.get(f, [])
        for (x, y) in drops: L.rect(x, y, x + 1, y + 2, wat); L.px(x, y, '#d8f0ff')
        if f == 3: L.ell(4, 36, 14, 39, wat); L.ell(26, 36, 36, 39, wat)
        if f == 4: L.ell(2, 37, 12, 39, sh(wat, .9)); L.ell(28, 37, 38, 39, sh(wat, .9))
        fr.append(ol(L))
    return dict(frames=fr, size=[W, H], anchor=[20, 39], pos=[44, 312], hit=[28, 280, 60, 314], fps=12, loop=False, tap='水桶：濺水花（純視覺）', zh='水桶')
def prop_star():
    W, H = 72, 44; fr = []; glow = []
    for f in range(6):
        L = C(W, H); G = C(W, H)
        if f == 0: star(L, 60, 10, 4, '#fff2b0'); L.px(60, 10, '#ffffff'); star(G, 60, 10, 6, '#fff2b0')
        if f == 1: star(L, 60, 10, 5, '#fff6c8'); spark(L, 60, 10, 7, '#fff6c8'); star(G, 60, 10, 9, '#fff6c8')
        if f in (2, 3, 4):
            hx_ = {2: 48, 3: 30, 4: 12}[f]; hy = {2: 16, 3: 25, 4: 34}[f]; ln = {2: 12, 3: 22, 4: 26}[f]
            for i in range(ln):
                t = i / ln; x, y = hx_ + i * 1.9, hy - i; c = mixc('#ffffff', '#7a9aff', t)
                if f == 4 and i < 6: continue
                L.px(x, y, c); L.px(x, y + 1, c) if t < .4 else None; G.px(x, y, c); G.px(x, y + 1, c); G.px(x, y - 1, c) if t < .5 else None
            star(L, hx_, hy, 3, '#ffffff'); star(G, hx_, hy, 6, '#fff6c8')
        if f == 5: L.px(60, 10, '#c8c0a0'); G.px(60, 10, '#fff2b0'); spark(L, 8, 38, 2, '#cfe0ff'); spark(G, 8, 38, 3, '#cfe0ff')
        fr.append(L); glow.append(G)
    return dict(frames=fr, glowSrc=glow, size=[W, H], anchor=[60, 43], pos=[132, 120], hit=[120, 96, 144, 124], fps=12, loop=False,
                tap='星：一粒流星劃過（純視覺；日版星淡啲）', zh='星', layer='sky（喺 far 之前）')
def prop_lamp():
    W, H = 22, 64; fr = []; glow = []
    for f in range(4):
        L = C(W, H); G = C(W, H); on = f >= 2
        L.box(8, 22, 12, 60, '#3a3f5a'); L.box(5, 59, 15, 63, '#2a2e44'); L.rect(9, 22, 9, 58, '#6a7090')
        L.poly([(3, 10), (11, 3), (19, 10)], '#2a2e44'); L.rect(10, 1, 12, 3, '#c99a3c')
        glass = {0: '#3a4466', 1: '#a8884a', 2: '#ffe08a', 3: '#fff2b8'}[f]
        L.rect(5, 10, 17, 21, glass); L.rect(5, 10, 5, 21, '#2a2e44'); L.rect(17, 10, 17, 21, '#2a2e44'); L.rect(11, 10, 11, 21, '#2a2e44'); L.rect(4, 21, 18, 23, '#2a2e44')
        if f >= 1: L.rect(9, 14, 13, 19, {1: '#ffb050', 2: '#fff6d0', 3: '#ffffff'}[f])
        if on or f == 1: L.rect(6, 11, 10, 20, glass); L.rect(12, 11, 16, 20, glass); L.rect(9, 14, 13, 19, '#ffffff' if on else '#ffb050')
        if on: G.rect(5, 10, 17, 21, '#ffd27a')
        if f == 1: G.rect(9, 14, 13, 19, '#ff9a3a')
        fr.append(ol(L)); glow.append(G)
    return dict(frames=fr, glowSrc=glow, size=[W, H], anchor=[11, 63], pos=[24, 248], hit=[12, 182, 36, 250], fps=10, loop=False,
                tap='燈：開／關（關→0、開＝1→2→3；再撳由 3 倒播返 0）；燈光屬場景燈，唔受 petGlow 影響', zh='燈')
def prop_pot():
    W, H = 40, 52; fr = []
    for f in range(6):
        L = C(W, H)
        L.ell(6, 30, 34, 50, '#3a3a44'); L.rect(6, 34, 34, 42, '#3a3a44'); L.ell(6, 28, 34, 38, '#5a5a66'); L.ell(9, 30, 31, 36, '#c87a3a'); L.ell(12, 31, 22, 34, '#e8a060')
        L.rect(2, 36, 6, 38, '#2a2a30'); L.rect(34, 36, 38, 38, '#2a2a30'); L.rect(8, 38, 10, 46, '#4a4a56')
        lid = {0: 0, 1: 2, 2: 4, 3: 3, 4: 1, 5: 0}[f]
        if lid: L.rect(12, 26 - lid, 28, 28 - lid, '#6a6a76'); L.rect(18, 23 - lid, 22, 25 - lid, '#8a8a96')
        puffs = {1: [(20, 18, 4)], 2: [(18, 12, 6), (24, 18, 4)], 3: [(16, 4, 7), (24, 10, 6), (20, 18, 4)], 4: [(14, 0, 6), (26, 4, 5)], 5: [(24, 0, 3)]}.get(f, [])
        for (x, y, r) in puffs: L.ell(x - r, y, x + r, y + r * 1.4, '#f4f4f8'); L.ell(x - r + 1, y, x + r - 2, y + r * .8, '#ffffff'); L.px(x + r - 2, y + r, '#c8ccd8')
        fr.append(ol(L, '#1a1a20'))
    return dict(frames=fr, size=[W, H], anchor=[20, 51], pos=[156, 210], hit=[136, 160, 176, 212], fps=12, loop=False, tap='煲：冒一嚿蒸氣（純視覺）', zh='煲')
def prop_spice():
    W, H = 34, 44; fr = []; pw = '#e8a040'
    for f in range(5):
        L = C(W, H); rot = {0: 0, 1: 1, 2: 2, 3: 1, 4: 0}[f]; x0 = 12 + rot * 2; y0 = 18 - rot * 3
        L.box(x0, y0 + 6, x0 + 9, y0 + 20, '#cfe3f0'); L.rect(x0 + 1, y0 + 12, x0 + 8, y0 + 19, pw); L.rect(x0 + 2, y0 + 9, x0 + 7, y0 + 11, '#fffaf0')
        L.box(x0 - 1, y0 + 2, x0 + 10, y0 + 5, '#b86a3c'); L.px(x0 + 2, y0 + 3, '#2a1a14'); L.px(x0 + 5, y0 + 3, '#2a1a14'); L.px(x0 + 8, y0 + 3, '#2a1a14')
        dots = {1: [(12, 10), (16, 12)], 2: [(10, 4), (14, 7), (18, 2), (8, 10), (20, 9)], 3: [(6, 12), (12, 16), (22, 14), (16, 20), (4, 22)], 4: [(8, 28), (14, 32), (20, 30), (24, 34)]}.get(f, [])
        for (x, y) in dots: L.rect(x, y, x + 1, y + 1, pw); L.px(x, y, sh(pw, 1.25))
        L.rect(2, 40, 32, 43, '#f2f2ea'); L.rect(4, 41, 30, 41, '#ffffff')
        if f == 4: L.rect(8, 39, 26, 40, pw)
        fr.append(ol(L))
    return dict(frames=fr, size=[W, H], anchor=[17, 43], pos=[48, 232], hit=[32, 190, 64, 234], fps=12, loop=False, tap='香料：搖一搖灑粉（純視覺）', zh='香料')
PROPS = {'post': [('mailbox', prop_mailbox), ('stamp', prop_stamp_all)], 'garden': [('flower', prop_flower), ('bucket', prop_bucket)],
         'tower': [('star', prop_star), ('lamp', prop_lamp)], 'kitchen': [('pot', prop_pot), ('spice', prop_spice)]}

# ================================================================ Lv3 擺設（4）
def deco_post():
    L = C(40, 44)
    L.box(6, 36, 34, 42, '#5a3a22'); L.box(17, 22, 23, 36, '#c99a3c'); L.box(4, 18, 36, 22, '#e0b04c')
    L.ell(12, 4, 28, 20, '#c99a3c'); L.ell(14, 6, 26, 18, '#fbf3df'); L.line([(20, 12), (24, 8)], '#c0392b'); L.px(20, 12, '#2a1a14')
    for a in range(0, 360, 45): L.px(20 + math.cos(math.radians(a)) * 5, 12 + math.sin(math.radians(a)) * 5, '#8a6a3a')
    L.box(8, 10, 16, 17, '#c9955c'); L.rect(11, 10, 12, 17, '#9c2f3a'); L.box(26, 12, 34, 17, '#d9aa70'); L.rect(29, 12, 30, 17, '#3f6aa0')
    return dict(img=ol(L), pos=[34, 318], anchor=[20, 43], zh='銅磅＋包裹', note='郵局 Lv3：分信枱前多咗個銅磅')
def deco_garden():
    L = C(40, 46)
    L.box(14, 22, 26, 40, '#b9b1a0'); L.box(8, 40, 32, 45, '#a8a090'); L.ell(2, 12, 38, 26, '#c8c0ae'); L.ell(5, 14, 35, 22, '#7cc4f0'); L.ell(8, 15, 20, 18, '#d8f0ff')
    for x in (3, 37): L.ell(x - 3, 18, x + 3, 24, '#4f8a3a')
    L.ell(22, 4, 32, 12, '#4f86d0'); L.ell(29, 3, 35, 8, '#4f86d0'); L.px(32, 5, '#ffffff'); L.px(33, 5, '#2a1a14'); L.poly([(35, 6), (38, 7), (35, 8)], '#f2a03c')
    L.poly([(22, 8), (16, 6), (20, 11)], '#3a66b0'); L.ell(24, 8, 30, 12, '#f2a0a0')
    for i, x in enumerate((10, 16)): L.ell(x - 2, 38, x + 2, 42, ['#e86a8a', '#f2c94c'][i])
    return dict(img=ol(L), pos=[166, 352], anchor=[20, 45], zh='雀仔浴盆', note='花園 Lv3：右下多咗個石浴盆（藍雀仔）')
def deco_tower():
    L = C(40, 50)
    L.box(14, 34, 26, 44, '#6a6f8e'); L.box(9, 44, 31, 49, '#5a5f7e'); L.rect(19, 26, 21, 34, '#a07a2c')
    L.d.ellipse([4, 4, 36, 34], outline=(201, 154, 60, 255)); L.d.ellipse([12, 4, 28, 34], outline=(201, 154, 60, 255)); L.d.ellipse([4, 14, 36, 24], outline=(242, 210, 122, 255))
    L.line([(6, 28), (34, 10)], '#e0b04c'); L.ell(17, 16, 23, 22, '#4f7fd8'); L.px(18, 17, '#cfe0ff'); star(L, 20, 2, 2, '#f6d77a')
    return dict(img=ol(L), pos=[176, 330], anchor=[20, 49], zh='渾天儀', note='瞭望台 Lv3：右側多咗座渾天儀', glint=[[20, 2], [6, 28]])
def deco_kitchen():
    L = C(40, 44)
    L.box(6, 32, 34, 42, '#9a6440'); L.rect(6, 36, 34, 36, '#7a4a2c')
    L.ell(4, 22, 36, 34, '#c9955c'); L.ell(6, 22, 34, 30, '#e0b07c')
    for (x, y) in ((10, 20), (18, 18), (26, 20)): L.ell(x - 5, y - 3, x + 5, y + 4, '#d9a060'); L.line([(x - 3, y), (x + 3, y - 1)], '#a86a30'); L.px(x - 2, y - 2, '#f2c890')
    L.ell(28, 12, 38, 22, '#c0392b'); L.px(31, 14, '#ff8a7a'); L.rect(33, 9, 34, 12, '#4f8a3a')
    for x in (8, 12, 16): L.line([(x, 22), (x - 2, 10)], '#3f7a32'); L.ell(x - 4, 8, x, 12, '#5e9b45')
    return dict(img=ol(L), pos=[178, 330], anchor=[20, 43], zh='麵包籃＋香草', note='廚房 Lv3：右下多咗籃新鮮麵包')
DECOS = {'post': deco_post, 'garden': deco_garden, 'tower': deco_tower, 'kitchen': deco_kitchen}

# ================================================================ Lv5 職業帽（4 × S/M/L）
HAT_W = {'S': 12, 'M': 16, 'L': 20}
def hat(job, size):
    w = HAT_W[size]; L = C(w + 8, w + 6); cx = (w + 8) // 2; b = w + 4      # b＝帽底線 y
    if job == 'post':
        L.ell(cx - w / 2, b - w * .62, cx + w / 2, b - 1, '#2a3a6a'); L.rect(cx - w / 2, b - w * .3, cx + w / 2, b - 1, '#2a3a6a')
        L.rect(cx - w / 2, b - 3, cx + w / 2, b - 2, '#c99a3c'); L.ell(cx - 1, b - w * .5, cx + 2, b - w * .5 + 3, '#f2d27a')
        L.poly([(cx - 1, b - 1), (cx + w / 2 + 4, b - 1), (cx + w / 2 + 2, b + 1), (cx - 1, b + 1)], '#1a2240'); L.rect(cx - w / 2 + 1, b - w * .55, cx - w / 4, b - w * .5, '#4a5a9a')
    elif job == 'garden':
        L.ell(cx - w / 2 - 3, b - 4, cx + w / 2 + 3, b + 1, '#e8c878'); L.ell(cx - w / 3, b - w * .55, cx + w / 3, b - 1, '#e8c878')
        L.rect(cx - w / 3, b - 4, cx + w / 3, b - 3, '#5e9b45'); L.ell(cx + w / 3 - 3, b - 7, cx + w / 3 + 1, b - 3, '#ff7aa0'); L.px(cx + w / 3 - 1, b - 5, '#f9d24a')
        for x in range(int(cx - w / 2 - 2), int(cx + w / 2 + 3), 3): L.px(x, b - 1, '#c8a050')
    elif job == 'tower':
        L.poly([(cx - w / 2, b - 1), (cx + 1, b - w - 1), (cx + w / 2, b - 1)], '#2a2a6a'); L.rect(cx - w / 2 - 1, b - 2, cx + w / 2 + 1, b, '#3a3a8a')
        star(L, cx + 1, b - w * .55, max(2, w / 6), '#f6d77a'); L.px(cx - w / 5, b - w * .3, '#ffffff'); L.px(cx + w / 4, b - w * .2, '#cfe0ff')
        L.ell(cx, b - w - 3, cx + 3, b - w, '#f6d77a')
    elif job == 'kitchen':
        L.rect(cx - w / 3, b - w * .5, cx + w / 3, b - 1, '#ffffff'); L.rect(cx - w / 3, b - 3, cx + w / 3, b - 1, '#e8e8f0')
        for dx in (-w / 3, 0, w / 3): L.ell(cx + dx - w / 4, b - w * .9, cx + dx + w / 4, b - w * .45, '#ffffff')
        L.ell(cx - w / 4, b - w - 1, cx + w / 4, b - w * .55, '#ffffff'); L.rect(cx - w / 3, b - w * .5, cx - w / 3, b - 1, '#c8c8d8')
    return ol(L), [cx, b]

# ================================================================ 產品 icon（8；16×16 1x → 48 @3x）
def icon(name):
    L = C(16, 16); gold = '#e0b04c'
    if name == 'letter': letter_s(L, 1, 4, 13, 8, '#f6eedc', '#c0392b')
    elif name == 'letter_commission':
        L.rect(1, 3, 14, 12, '#fff4d6'); L.rect(1, 3, 14, 3, gold); L.rect(1, 12, 14, 12, gold); L.rect(1, 3, 1, 12, gold); L.rect(14, 3, 14, 12, gold)
        L.line([(1, 3), (7.5, 8), (14, 3)], '#c9a060'); L.ell(5, 6, 10, 11, '#c0392b'); L.px(7, 8, '#ffd27a'); L.px(6, 7, '#ff8a7a')
        L.line([(9, 11), (12, 15)], '#c0392b'); L.line([(7, 11), (5, 15)], '#c0392b')
    elif name == 'flowerpot':
        L.box(4, 10, 11, 14, '#c0663a'); L.rect(3, 9, 12, 10, '#e0864a'); L.line([(7, 9), (7, 5)], '#3f7a32'); L.ell(3, 5, 7, 8, '#5e9b45')
        L.ell(5, 1, 11, 7, '#ff7aa0'); L.ell(7, 3, 9, 5, '#f9d24a')
    elif name == 'decoration':
        L.rect(7, 0, 8, 2, gold); L.box(4, 3, 11, 12, '#c4382e'); L.rect(5, 4, 10, 11, '#ffd27a'); L.rect(7, 4, 8, 11, '#fff6d0'); L.rect(3, 2, 12, 3, gold); L.rect(3, 12, 12, 13, gold)
        L.line([(7, 13), (7, 15)], '#c4382e'); L.line([(8, 13), (8, 15)], '#c4382e')
    elif name == 'starmap_sticker':
        L.ell(1, 1, 14, 14, '#ffffff'); L.ell(2, 2, 13, 13, '#24346e'); L.line([(4, 9), (7, 5), (10, 7), (11, 11)], '#8fb0ff')
        for (x, y, c) in ((4, 9, '#ffffff'), (7, 5, '#ffffff'), (10, 7, '#f6d77a'), (11, 11, '#ffffff')): L.rect(x, y, x, y, c); L.px(x - 1, y, sh(c, .8)) if x == 10 else None
        L.poly([(10, 14), (14, 10), (14, 14)], '#cfd8f0'); L.line([(10, 14), (14, 10)], '#8a94b0')
    elif name == 'starmap_rare':
        L.ell(1, 1, 14, 14, '#c99a3c'); L.ell(2, 2, 13, 13, '#f2d27a'); star(L, 7.5, 8, 5, '#fff6c8'); star(L, 7.5, 8, 3, '#ffffff'); L.px(4, 4, '#ffffff'); L.px(11, 3, '#bfe8ff'); L.px(3, 11, '#ffc8f0')
        L.poly([(11, 14), (14, 11), (14, 14)], '#fff4d6')
    elif name == 'dish':
        L.ell(0, 7, 15, 14, '#f2f2ea'); L.ell(2, 8, 13, 12, '#ffffff'); L.ell(3, 6, 12, 11, '#f6c84a'); L.ell(4, 6, 9, 9, '#ffe08a'); L.px(10, 8, '#c0392b'); L.px(5, 5, '#4f8a3a')
        for x in (5, 8, 11): L.px(x, 1 + (x % 2), '#e8e8f0'); L.px(x, 3, '#e8e8f0')
    elif name == 'meal_shared':
        L.ell(0, 8, 8, 14, '#f2f2ea'); L.ell(1, 8, 7, 11, '#f6c84a'); L.ell(7, 9, 15, 15, '#f2f2ea'); L.ell(8, 9, 14, 12, '#e86a3a')
        heart(L, 8, 4, 3, '#ff6a8a'); L.px(6, 2, '#ffd0dc')
    return ol(L, '#2a1a14')
PRODUCTS = {'post': ('letter', 'letter_commission', .25, '委託信'), 'garden': ('flowerpot', 'decoration', .15, '裝飾'),
            'tower': ('starmap_sticker', 'starmap_rare', None, '稀有星圖貼紙'), 'kitchen': ('dish', 'meal_shared', None, '共飯套餐')}
PRODUCT_ZH = {'letter': '一封信', 'letter_commission': '委託信', 'flowerpot': '一盆花', 'decoration': '花園裝飾', 'starmap_sticker': '星圖貼紙',
              'starmap_rare': '金星圖貼紙', 'dish': '一碟餸', 'meal_shared': '共飯套餐'}

# ================================================================ 工作 clip 道具疊層（S/M/L × 4 職 × loop/done）
SZ = {'S': dict(bw=13, bh=28, k=.8), 'M': dict(bw=17, bh=38, k=1.0), 'L': dict(bw=21, bh=46, k=1.2)}
CW, CH, PX, PY = 104, 96, 52, 88       # clip 畫布 1x，腳底 pivot (52,88)
def clip(job, size, kind):
    z = SZ[size]; bw, bh, k = z['bw'], z['bh'], z['k']; n = 8 if kind == 'loop' else 4
    frames = []
    for f in range(n):
        B, F, G = C(CW, CH), C(CW, CH), C(CW, CH); t = f / n; tr = dict(dx=0, dy=0, sx=1, sy=1, rot=0)
        if job == 'post' and kind == 'loop':
            rx = PX + bw + 4; ry = PY - int(bh * .55)                          # 信格架（右）
            F.box(rx, ry - int(16 * k), rx + int(14 * k), PY - 1, '#7a4428')
            for j in range(3): yy = ry - int(16 * k) + 2 + j * int(5 * k); F.rect(rx + 2, yy, rx + int(14 * k) - 2, yy + int(3 * k), '#3a1f12')
            for j in range(3):
                if (f // 2 + j) % 4 != 0: yy = ry - int(16 * k) + 2 + j * int(5 * k); F.rect(rx + 3, yy + 1, rx + 6 + j, yy + int(3 * k), ['#f6eedc', '#cfe3f0', '#f2c9c2'][j])
            lx = PX - bw - int(12 * k); B.box(lx, PY - int(8 * k), lx + int(10 * k), PY - 1, '#c9955c')   # 信堆（左）
            for j in range(3): letter_s(B, lx + 1, PY - int(8 * k) - 2 - j * 2, int(8 * k), 3, ['#f6eedc', '#f6e3a6', '#cfe3f0'][j], None)
            u = (f % 4) / 3; ax, ay = lx + 4, PY - int(10 * k); bx, by = rx + 4, ry - int(10 * k) + (f // 4) * int(5 * k)
            x = ax + (bx - ax) * u; y = ay + (by - ay) * u - math.sin(u * math.pi) * (bh * .6)
            letter_s(F, x - 4, y - 2, int(8 * k), max(3, int(5 * k)), ['#f6eedc', '#cfe3f0', '#f2c9c2', '#f6e3a6'][f // 2 % 4])
            tr = dict(dx=[-1, -1, 0, 1, 1, 1, 0, -1][f], dy=[0, -1, -2, -1, 0, -1, -2, -1][f], sx=1, sy=[1, 1.02, 1.03, 1.02, 1, 1.02, 1.03, 1.02][f], rot=[-4, -2, 2, 4, 3, 1, -1, -3][f])
        elif job == 'post':
            px = PX + bw + int(9 * k); fy = PY - 1
            letter_s(F, px - int(7 * k), fy - int(5 * k), int(14 * k), int(6 * k), '#f6eedc', None)
            sy = {0: fy - bh - 8, 1: fy - int(14 * k), 2: fy - int(16 * k), 3: fy - int(22 * k)}[f]
            F.box(px - int(4 * k), sy + int(7 * k), px + int(4 * k), sy + int(10 * k), '#c0392b'); F.box(px - int(3 * k), sy + int(3 * k), px + int(3 * k), sy + int(7 * k), '#8a5634')
            F.ell(px - int(4 * k), sy - int(3 * k), px + int(4 * k), sy + int(3 * k), '#c08a58')
            if f >= 2: F.rect(px - int(3 * k), fy - int(3 * k), px + int(2 * k), fy - int(1 * k), '#c0392b'); spark(G, px - int(9 * k), fy - int(10 * k), 3, '#fff2c8'); spark(G, px + int(9 * k), fy - int(14 * k), 3, '#fff2c8')
            if f == 2: spark(F, px - int(9 * k), fy - int(10 * k), 2, '#fff6d0'); spark(F, px + int(9 * k), fy - int(14 * k), 2, '#fff6d0')
            tr = [dict(dx=-1, dy=-3, sx=.97, sy=1.05, rot=-3), dict(dx=2, dy=1, sx=1.08, sy=.9, rot=6), dict(dx=1, dy=0, sx=1.04, sy=.96, rot=3), dict(dx=0, dy=-1, sx=1, sy=1.02, rot=0)][f]
        elif job == 'garden' and kind == 'loop':
            cx = PX + bw + int(6 * k); cy = PY - int(bh * .5); tilt = [0, 1, 2, 3, 3, 2, 1, 0][f]
            F.poly([(cx - int(6 * k), cy - int(4 * k) + tilt), (cx + int(5 * k), cy - int(4 * k) - tilt), (cx + int(5 * k), cy + int(5 * k) - tilt), (cx - int(6 * k), cy + int(5 * k) + tilt)], '#5aa0c8')
            F.line([(cx + int(5 * k), cy - tilt), (cx + int(12 * k), cy + int(2 * k) - tilt)], '#3a7aa0', 2); F.line([(cx - int(6 * k), cy - int(3 * k) + tilt), (cx - int(2 * k), cy - int(9 * k)), (cx + int(3 * k), cy - int(4 * k))], '#3a7aa0')
            F.rect(cx - int(5 * k), cy, cx + int(4 * k), cy, '#9ad0f0')
            if tilt >= 2:
                for j in range(4 + tilt): dy_ = (j * 5 + f * 3) % 22; F.rect(cx + int(12 * k) + j % 2, cy + 3 + dy_, cx + int(12 * k) + j % 2, cy + 4 + dy_, '#9ad8ff')
                F.ell(cx + int(8 * k), PY - 2, cx + int(16 * k), PY, '#7cc4f0')
            B.line([(cx + int(12 * k), PY - 1), (cx + int(12 * k), PY - int(8 * k))], '#3f7a32'); B.ell(cx + int(9 * k), PY - int(12 * k), cx + int(15 * k), PY - int(7 * k), '#ff7aa0' if f >= 4 else '#5e9b45')
            tr = dict(dx=0, dy=[0, -1, -1, 0, 0, -1, -1, 0][f], sx=1, sy=[1, 1.02, 1.02, 1, .99, 1.02, 1.02, 1][f], rot=[1, 2, 3, 4, 4, 3, 2, 1][f])
        elif job == 'garden':
            wx = PX - bw - int(4 * k); wy = PY - 1; up = [0, 3, 12, 6][f]
            B.ell(wx - int(5 * k), wy - 2, wx + int(5 * k), wy + 1, '#6a4a2c')
            if f < 3:
                for j in range(3): B.line([(wx, wy - up), (wx - 4 + j * 4, wy - up - int(8 * k))], '#4f8a3a'); B.ell(wx - 6 + j * 4, wy - up - int(10 * k), wx - 2 + j * 4, wy - up - int(7 * k), '#5e9b45')
                if f >= 1: B.line([(wx, wy - up), (wx, wy - up + 4)], '#c8a070')
            if f >= 2:
                for (dx, dy) in ((-6, -8), (4, -10), (-2, -14)): B.rect(wx + dx, wy + dy - up // 2, wx + dx + 1, wy + dy - up // 2 + 1, '#6a4a2c')
            if f == 3:
                for j in range(3): F.line([(wx - 10, wy - 24), (wx - 14 + j * 4, wy - 32)], '#4f8a3a')
                spark(F, wx + 2, wy - 10, 2, '#fff6c0'); spark(G, wx + 2, wy - 10, 4, '#fff6c0')
            tr = [dict(dx=-2, dy=0, sx=1, sy=.96, rot=-6), dict(dx=-1, dy=0, sx=.96, sy=1.04, rot=-3), dict(dx=1, dy=-3, sx=.96, sy=1.06, rot=4), dict(dx=0, dy=-1, sx=1.02, sy=.98, rot=0)][f]
        elif job == 'tower' and kind == 'loop':
            ang = math.radians(-150 + 30 * math.sin(t * 2 * math.pi)); ex, ey = PX - int(bw * .75), PY - int(bh * .5)
            for j in range(int(16 * k)):
                x, y = ex + math.cos(ang) * j, ey + math.sin(ang) * j; r = 1 + (j > 8 * k)
                F.rect(x - r / 2, y - r / 2, x + r / 2, y + r / 2, '#c99a3c' if j % 5 else '#a07a2c')
            x, y = ex + math.cos(ang) * 16 * k, ey + math.sin(ang) * 16 * k; F.rect(x - 1, y - 1, x + 1, y + 1, '#f2d27a')
            if f in (2, 6): spark(F, x + math.cos(ang) * 10, y + math.sin(ang) * 10, 2, '#fff6c8'); spark(G, x + math.cos(ang) * 10, y + math.sin(ang) * 10, 4, '#fff6c8')
            tr = dict(dx=[0, -1, -1, 0, 1, 1, 0, 0][f], dy=-1, sx=1, sy=1.02, rot=round(-6 * math.sin(t * 2 * math.pi), 1))
        elif job == 'tower':
            lx = PX + bw + int(8 * k); ly = PY - 1; on = f >= 2
            B.box(lx - int(4 * k), ly - int(12 * k), lx + int(4 * k), ly - 1, '#3a3f5a'); B.rect(lx - int(3 * k), ly - int(10 * k), lx + int(3 * k), ly - int(3 * k), '#ffe08a' if on else ('#a8884a' if f == 1 else '#3a4466'))
            B.poly([(lx - int(5 * k), ly - int(12 * k)), (lx, ly - int(16 * k)), (lx + int(5 * k), ly - int(12 * k))], '#2a2e44')
            if on: G.rect(lx - int(3 * k), ly - int(10 * k), lx + int(3 * k), ly - int(3 * k), '#ffd27a'); spark(F, lx + int(6 * k), ly - int(16 * k), 2, '#fff6c8')
            if f == 1: F.rect(lx - 1, ly - int(18 * k), lx + 1, ly - int(16 * k), '#ffb050'); G.rect(lx - 2, ly - int(19 * k), lx + 2, ly - int(15 * k), '#ffb050')
            tr = [dict(dx=2, dy=0, sx=1.04, sy=.96, rot=3), dict(dx=3, dy=-4, sx=.96, sy=1.06, rot=5), dict(dx=2, dy=0, sx=1.06, sy=.94, rot=2), dict(dx=1, dy=-1, sx=1, sy=1.02, rot=0)][f]
        elif job == 'kitchen' and kind == 'loop':
            pw = int(10 * k); px, py = PX + bw + pw - 2, PY + 1
            F.ell(px - pw, py - int(10 * k), px + pw, py, '#3a3a44'); F.rect(px - pw, py - int(10 * k), px + pw, py - int(5 * k), '#3a3a44'); F.ell(px - pw, py - int(13 * k), px + pw, py - int(7 * k), '#5a5a66')
            F.ell(px - pw + 2, py - int(12 * k), px + pw - 2, py - int(8 * k), '#e8a050'); F.rect(px - pw - 3, py - int(9 * k), px - pw, py - int(8 * k), '#2a2a30'); F.rect(px + pw, py - int(9 * k), px + pw + 3, py - int(8 * k), '#2a2a30')
            a = t * 2 * math.pi; sx_, sy_ = px + math.cos(a) * pw * .5, py - int(10 * k) + math.sin(a) * 1.5
            F.line([(sx_, sy_), (sx_ - 7 * k, sy_ - 12 * k)], '#c08a58', 2); F.ell(sx_ - 2, sy_ - 1, sx_ + 2, sy_ + 1, '#a8744a')
            if f % 4 in (1, 2):
                for (dx, dy, r) in ((-4, -18, 3), (3, -24, 4)): r = int(r * k); B.ell(px + dx - r, py + dy * k - r, px + dx + r, py + dy * k + r, '#f4f4f8')
            tr = dict(dx=1 + round(math.cos(a) * 1.5), dy=-1, sx=1, sy=round(1 + .02 * math.sin(a * 2), 3), rot=round(3 + 3 * math.cos(a), 1))
        else:   # kitchen done：試味
            pw = int(10 * k); px, py = PX + bw + pw - 2, PY + 1
            F.ell(px - pw, py - int(10 * k), px + pw, py, '#3a3a44'); F.rect(px - pw, py - int(10 * k), px + pw, py - int(5 * k), '#3a3a44'); F.ell(px - pw, py - int(13 * k), px + pw, py - int(7 * k), '#5a5a66'); F.ell(px - pw + 2, py - int(12 * k), px + pw - 2, py - int(8 * k), '#e8a050')
            sy_ = [py - int(12 * k), py - int(bh * .45), py - int(bh * .5), py - int(bh * .45)][f]; sx_ = [px, PX + bw + 2, PX + bw, PX + bw + 2][f]
            F.line([(sx_, sy_), (sx_ + 8 * k, sy_ + 8 * k)], '#c08a58', 2); F.ell(sx_ - 3, sy_ - 2, sx_ + 2, sy_ + 1, '#a8744a'); F.px(sx_ - 1, sy_ - 1, '#e8a050')
            if f >= 2: heart(F, PX, PY - bh - 6 - (f - 2) * 3, int(3 * k) + 1, '#ff6a8a'); heart(G, PX, PY - bh - 6 - (f - 2) * 3, int(5 * k) + 1, '#ff8aa8'); spark(F, PX - bw - 2, PY - bh, 2, '#fff6c8')
            tr = [dict(dx=1, dy=0, sx=1, sy=1, rot=4), dict(dx=1, dy=-1, sx=.98, sy=1.03, rot=6), dict(dx=0, dy=-4, sx=.94, sy=1.08, rot=0), dict(dx=0, dy=0, sx=1.06, sy=.95, rot=0)][f]
        frames.append(dict(back=ol(B), front=ol(F), glow=G, tr=tr))
    return frames

# ================================================================ 粒子（8×8 1x × 6 幀）
def particles():
    out = {}
    for name in ('paper', 'twinkle', 'steam', 'ember', 'splash', 'sparkle', 'spice'):
        fr = []
        for f in range(6):
            L = C(8, 8)
            if name == 'paper': w = [5, 4, 2, 4, 5, 3][f]; L.rect(4 - w // 2, 3, 4 + w // 2, 5, '#f6eedc'); L.px(4, 4, '#c8b89c')
            if name == 'twinkle': r = [0, 1, 2, 3, 2, 1][f]; spark(L, 4, 4, r, '#ffffff') if r else L.px(4, 4, '#cfe0ff')
            if name == 'steam': r = [1, 2, 2, 3, 3, 2][f]; L.ell(4 - r, 6 - r - f // 2, 4 + r, 6 + r - f // 2, '#f4f4f8') if f < 5 else L.px(4, 2, '#e8e8f0')
            if name == 'ember': L.rect(3 + f % 2, 6 - f, 4 + f % 2, 7 - f, ['#ffe08a', '#ffb050', '#ff8a3a', '#ffb050', '#ff8a3a', '#c8502a'][f])
            if name == 'splash': L.rect(3, 6 - [0, 2, 4, 5, 4, 2][f], 4, 7 - [0, 2, 4, 5, 4, 2][f], '#9ad8ff')
            if name == 'sparkle': r = [1, 2, 3, 2, 1, 0][f]; spark(L, 4, 4, r, '#fff6c8') if r else L.px(4, 4, '#fff6c8')
            if name == 'spice': L.px(2 + f % 3, 1 + f, '#e8a040'); L.px(5 - f % 2, f + 2, '#f2c070')
            fr.append(L)
        out[name] = fr
    return out
