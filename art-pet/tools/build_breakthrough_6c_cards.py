#!/usr/bin/env python3
"""6c 夢卡 20 張（28×36 art）＋ 未解鎖卡背。卡面冇字（標題由 code 用 FP12 寫喺卡外／詳情頁）。
每張 ≤12 色：外描 1＋金邊 3＋主題底 2＋插畫 6。光源左上。純程序化像素。"""
import numpy as np
from bt6_px import Spr, render, over, hx, BAYER, LINE
CW, CH = 28, 36
GOLD = ('#FFF6CF', '#EDBE62', '#9C6630')
TH = {  # bg(暗,亮)  插畫 6 色
 'forest': dict(bg=('#2F4F3E', '#3F6B4A'), c='#FFF4DE', cs='#E6CFA6', a='#E2577F', ad='#9E2F55', b='#6E9A5A', p='#FF9DB8'),
 'lake':   dict(bg=('#1E3F6E', '#2E64A0'), c='#FFF4DE', cs='#E6CFA6', a='#9FD4F2', ad='#E9F6FF', b='#4E9A58', p='#FF9DB8'),
 'toy':    dict(bg=('#B98AA8', '#E6B8CF'), c='#FFF4DE', cs='#E6CFA6', a='#E2577F', ad='#3E86C8', b='#86E6DC', p='#7CC6F2'),
 'star':   dict(bg=('#1B1846', '#2C2868'), c='#FFF4DE', cs='#E6CFA6', a='#C9C0F0', ad='#7A5CD6', b='#8F85C2', p='#FF9DB8'),
}
CARDS = [('f1', '會唱歌嘅菇'), ('f2', '菇傘下避雨'), ('f3', '森林博士上堂'), ('f4', '巨型暖菇飯'), ('f5', '菇菇捉迷藏'),
         ('l1', '水珠浮浮'), ('l2', '湖底月光'), ('l3', '游水冠軍'), ('l4', '雨點合唱團'), ('l5', '倒影另一隻我'),
         ('t1', '積木城堡'), ('t2', '發條團絨'), ('t3', '波波池'), ('t4', '玩具火車'), ('t5', '拼圖少一塊'),
         ('s1', '數星星'), ('s2', '流星許願'), ('s3', '月亮韆鞦'), ('s4', '團絨星座'), ('s5', '銀河散步')]
THK = {'f': 'forest', 'l': 'lake', 't': 'toy', 's': 'star'}
WX, WY, WW, WH = 4, 4, 20, 21     # 插畫窗（內）

def mats(t):
    return {'c': (GOLD[0], t['c'], t['cs']),   # 團絨／奶白
            'a': (t['p'] if t is TH['forest'] else t['ad'] if t is TH['lake'] else GOLD[0] if t is TH['toy'] else t['c'], t['a'], t['ad'] if t is not TH['lake'] else t['a']),
            'b': (t['b'], t['b'], t['bg'][1]),
            'g': (GOLD[0], GOLD[1], GOLD[2]),
            'd': (t['ad'], t['ad'], t['ad']) if t is not TH['lake'] else (t['ad'], t['ad'], t['a']),
            'p': (t['p'], t['p'], t['p']),
            's': (t['cs'], t['cs'], t['cs'])}

def tr(s, cx, cy, r=4.5, eye='dot', mouth='dot', blush=True):
    """迷你團絨：奶白毛球＋兩隻小耳"""
    s.C(cx - r * .55, cy - r * .8, r * .38, 'c'); s.C(cx + r * .55, cy - r * .8, r * .38, 'c')
    s.E(cx, cy, r + .3, r, 'c'); s.face(int(cx), int(cy), 3, mouth, blush, eye)

def mush(s, x, y, r, face=False):
    s.R(x - max(1, r // 3), y, x + max(1, r // 3), y + r, 'c'); s.E(x + .5, y + .5, r + .5, r * .7 + .5, 'a'); s.R(x - r, y + 1, x + r, y + 1, '.')
    s.R(x - max(1, r // 3), y + 1, x + max(1, r // 3), y + 1, 'c')
    if r >= 3: s.P([(x - r // 2, y - r // 3), (x + r // 2, y - r // 2 + 1)], 'w')
    if face: s.P([(x - 1, y + 2), (x + 1, y + 2)], 'k')

def note(s, x, y): s.A(x, y, ['_kk', '_k_', 'kk_', 'kk_'])
def drop(s, x, y): s.P([(x, y), (x, y + 1)], 'a'); s.P([(x, y + 2)], 'A')

V = {}
def v(id_):
    def deco(fn): V[id_] = fn; return fn
    return deco
@v('f1')
def _(s): mush(s, 9, 9, 7, True); s.P([(9, 12)], 'k'); s.P([(9, 13)], 'k'); note(s.d, 14, 1); note(s.d, 1, 2); s.R(0, 18, 19, 20, 'b')
@v('f2')
def _(s):
    mush(s, 10, 7, 9); tr(s, 10, 15, 3.6, mouth='none'); s.R(0, 19, 19, 20, 'b')
    for (x, y) in ((1, 1), (17, 0), (3, 10), (18, 11), (14, 2)): drop(s.d, x, y)
@v('f3')
def _(s):
    s.R(1, 1, 12, 9, 'D'); s.L([(3, 3), (9, 3)], 's'); s.L([(3, 5), (7, 5)], 's'); s.L([(3, 7), (10, 7)], 's')
    mush(s, 15, 7, 4, True); s.P([(13, 9), (14, 9), (16, 9), (17, 9)], 'k'); s.P([(15, 8)], 'k')
    tr(s, 6, 16, 3.6); s.R(0, 19, 19, 20, 'b')
@v('f4')
def _(s):
    s.E(10, 14, 9, 4.5, 'a'); s.R(1, 9, 19, 13, '.'); s.R(2, 12, 18, 13, 'c'); s.E(10, 14, 9, 4.5, 'a'); s.R(1, 10, 19, 12, '.')
    s.E(10, 11, 8, 2.2, 'c'); mush(s, 10, 7, 5, False); s.R(5, 18, 15, 19, 'A')
    for x in (3, 16): s.d.L([(x, 4), (x + 1, 2), (x, 0)], 's')
@v('f5')
def _(s):
    tr(s, 14, 15, 4, mouth='none'); s.R(0, 15, 19, 20, 'b'); mush(s, 5, 8, 5, True); mush(s, 10, 13, 2)
    s.d.P([(1, 14), (3, 13), (17, 13), (19, 14)], 'a')
@v('l1')
def _(s):
    tr(s, 10, 11, 4.2); s.d.C(10, 10, 8.5, 'a'); s.d.C(10, 10, 7.6, '.'); s.d.P([(4, 6), (4, 5), (5, 4), (6, 3)], 'w'); s.C(17.5, 2, 1.6, 'a'); s.C(2, 18, 1.4, 'a')
@v('l2')
def _(s):
    s.C(10, 6, 4.5, 'g'); s.C(12, 4.5, 3.8, '.'); s.d.R(0, 11, 19, 11, 'd')
    for y, w in ((13, 6), (15, 4), (17, 3), (19, 2)): s.d.R(10 - w // 2 - 1, y, 10 + w // 2 - 1, y, 'g')
    s.d.P([(3, 14), (4, 14), (16, 16), (17, 16)], 'a')
@v('l3')
def _(s):
    s.R(0, 12, 19, 20, 'a'); s.L([(0, 12), (19, 12)], 'd'); tr(s, 9, 11, 4.2, eye='happy', mouth='open')
    s.E(9, 7.5, 4.6, 2.6, 'p'); s.R(4, 8, 14, 10, '.'); tr_ear_fix = None
    s.L([(15, 1), (17, 4), (19, 1)], 'p'); s.C(17, 6, 2.4, 'g'); s.P([(17, 6)], 'w'); s.P([(2, 15), (3, 16), (14, 16), (15, 15)], 'd')
@v('l4')
def _(s):
    for i, x in enumerate((3, 10, 17)):
        y = 6 + (i % 2) * 3; s.PG([(x, y - 5), (x + 3, y + 1), (x - 3, y + 1)], 'a'); s.C(x, y + 1.5, 3.2, 'a'); s.P([(x - 1, y + 1), (x + 1, y + 1)], 'k')
        s.P([(x, y + 3)] if i != 1 else [(x, y + 3), (x, y + 4)], 'k')
    note(s.d, 7, 15); note(s.d, 14, 16); s.R(0, 20, 19, 20, 'd')
@v('l5')
def _(s):
    tr(s, 10, 6, 4.2); s.d.R(0, 11, 19, 11, 'd')
    s.C(10 - 2.3, 16.4 + 3.4, 1.6, 'a'); s.C(10 + 2.3, 16.4 + 3.4, 1.6, 'a'); s.E(10, 16, 4.5, 4.2, 'a'); s.P([(8, 16), (11, 16), (9, 15)], 'd')
    s.d.P([(3, 13), (4, 13), (15, 18), (16, 18)], 'd')
@v('t1')
def _(s):
    s.R(2, 12, 17, 19, 'a'); s.R(8, 15, 11, 19, 'D'); s.R(2, 9, 4, 11, 'a'); s.R(8, 9, 11, 11, 'p'); s.R(15, 9, 17, 11, 'a')
    s.R(8, 5, 11, 8, 'g'); s.d.L([(10, 5), (10, 0)], 's'); s.R(11, 0, 14, 2, 'b')
@v('t2')
def _(s):
    tr(s, 9, 12, 5.5, eye='dot', mouth='dot'); s.R(14, 10, 16, 11, 'g'); s.C(18, 8, 2.2, 'g'); s.C(18, 13, 2.2, 'g'); s.P([(18, 8), (18, 13)], 'G')
    s.d.L([(2, 3), (4, 5)], 'c'); s.d.L([(2, 7), (3, 8)], 'c'); s.R(4, 18, 6, 19, 'D'); s.R(11, 18, 13, 19, 'D')
@v('t3')
def _(s):
    tr(s, 10, 9, 4.6, eye='happy', mouth='open')
    for i, (x, y) in enumerate([(2, 15), (6, 13), (10, 15), (14, 13), (18, 15), (4, 18), (8, 19), (12, 18), (16, 19), (0, 19), (19, 19)]):
        s.C(x, y, 2.4, 'agbpd'[i % 5] if 'agbpd'[i % 5] != 'p' else 'p')
@v('t4')
def _(s):
    s.R(1, 8, 9, 15, 'a'); s.R(3, 4, 7, 8, 'd'); s.R(2, 2, 8, 3, 'D'); s.R(4, 10, 7, 12, 'w')
    s.R(11, 9, 19, 15, 'b'); s.R(10, 12, 11, 12, 'k')
    for x in (3, 7, 13, 17): s.C(x, 17, 2, 'k'); s.P([(x, 17)], 's')
    s.L([(0, 20), (19, 20)], 'g')
@v('t5')
def _(s):
    s.R(1, 2, 18, 18, 'b'); s.R(10, 10, 18, 18, '.'); s.L([(10, 2), (10, 18)], 'B'); s.L([(1, 10), (18, 10)], 'B')
    s.C(10, 6, 1.6, 'B'); s.C(5.5, 10, 1.6, 'B'); s.C(14, 10, 1.6, '.')
    s.d.P([(12, 12), (14, 12), (16, 12), (12, 14), (12, 16), (14, 16), (16, 16), (16, 14)], 'c'); s.d.A(13, 13, ['ggg', '__g', '_g_'])
@v('s1')
def _(s):
    tr(s, 10, 15, 4.6, eye='dot', mouth='open')
    for (x, y) in ((3, 3), (10, 1), (17, 4), (6, 8), (14, 8)): s.d.P([(x, y), (x - 1, y + 1), (x + 1, y + 1), (x, y + 2)], 'g'); s.d.P([(x, y + 1)], 'w')
    s.R(13, 14, 15, 15, 'c'); s.R(15, 12, 16, 13, 'c')
@v('s2')
def _(s):
    s.d.L([(2, 2), (13, 7)], 'a'); s.d.L([(4, 1), (13, 6)], 'd'); s.C(15, 7, 2.4, 'g'); s.P([(15, 7)], 'w')
    tr(s, 9, 15, 4.6, eye='closed', mouth='none'); s.R(8, 18, 10, 19, 'c')
@v('s3')
def _(s):
    s.C(10, 15, 8, 'g'); s.C(12.5, 12.5, 7.5, '.'); s.d.L([(5, 0), (5, 10)], 'c'); s.d.L([(13, 0), (13, 10)], 'c'); s.R(4, 11, 14, 11, 'D')
    tr(s, 9, 7, 3.6, eye='happy')
@v('s4')
def _(s):
    pts = [(4, 4), (7, 2), (10, 4), (13, 2), (16, 4), (17, 11), (10, 17), (3, 11)]
    s.d.L(pts + [pts[0]], 'd')
    for (x, y) in pts: s.d.P([(x, y)], 'g')
    for (x, y) in ((4, 4), (10, 17), (16, 4)): s.d.P([(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)], 'g'); s.d.P([(x, y)], 'w')
    s.d.P([(8, 9), (12, 9)], 'w'); s.d.P([(10, 11)], 'g')
@v('s5')
def _(s):
    s.PG([(0, 14), (19, 3), (19, 9), (0, 20)], 'D'); s.PG([(0, 16), (19, 5), (19, 7), (0, 18)], 'a')
    for (x, y) in ((3, 16), (8, 13), (14, 9), (17, 7), (5, 3), (15, 17)): s.d.P([(x, y)], 'w')
    tr(s, 10, 8, 3.8, eye='closed', mouth='dot')

def frame(th, inner):
    t = TH[th]; a = np.zeros((CH, CW, 4), np.uint8); yy, xx = np.mgrid[0:CH, 0:CW]
    gh, gm, gl = (hx(c) for c in GOLD); b0, b1 = hx(t['bg'][0]), hx(t['bg'][1])
    cut = (abs(xx - 0) + abs(yy - 0) < 2) | (abs(xx - (CW - 1)) + abs(yy) < 2) | (abs(xx) + abs(yy - (CH - 1)) < 2) | (abs(xx - (CW - 1)) + abs(yy - (CH - 1)) < 2)
    a[:] = gm; a[(xx <= 1) | (yy <= 1)] = gh; a[(xx >= CW - 2) | (yy >= CH - 2)] = gl
    a[((xx <= 1) & (yy >= CH - 2)) | ((yy <= 1) & (xx >= CW - 2))] = gm
    edge = (xx == 0) | (yy == 0) | (xx == CW - 1) | (yy == CH - 1) | ((abs(xx) + abs(yy)) == 2) | ((abs(xx - CW + 1) + abs(yy)) == 2) | ((abs(xx) + abs(yy - CH + 1)) == 2) | ((abs(xx - CW + 1) + abs(yy - CH + 1)) == 2)
    a[edge] = LINE; a[cut] = 0
    # 窗：描線＋底（左上亮 dither）
    a[WY - 1:WY + WH + 1, WX - 1:WX + WW + 1] = LINE
    wy, wx = np.mgrid[0:WH, 0:WW]; lit = 1 - (wx + wy) / (WW + WH)
    win = np.zeros((WH, WW, 4), np.uint8); win[:] = b0; win[lit > 0.45 + 0.4 * BAYER[wy % 4, wx % 4]] = b1
    a[WY:WY + WH, WX:WX + WW] = win
    if inner is not None: over(a, inner, WX, WY)
    # 底牌：5 粒序號
    a[WY + WH + 1:CH - 3, 3:CW - 3] = LINE; a[WY + WH + 2:CH - 4, 4:CW - 4] = b0
    return a

def card(id_):
    th = THK[id_[0]]; t = TH[th]; s = Spr(WW, WH); s.d = Spr(WW, WH); V[id_](s)
    inner = render(s, mats(t), special={'k': '#24172C', 'w': GOLD[0], '*': t['p']})
    over(inner, render(s.d, {}, special={'k': '#24172C', 'w': GOLD[0], 'g': GOLD[1], 'a': t['a'], 'A': t['ad'] if th != 'lake' else t['a'], 'd': t['ad'], 's': t['cs'], 'c': t['c']}, outline=False))
    a = frame(th, inner); idx = int(id_[1]); gh, gm, gl = (hx(c) for c in GOLD); b1 = hx(t['bg'][1])
    for i in range(5):
        x = 5 + i * 4; y = WY + WH + 3
        a[y:y + 2, x:x + 2] = gm if i + 1 == idx else b1
        if i + 1 == idx: a[y, x] = gh; a[y + 1, x + 1] = gl
    return a

def card_back():
    """未解鎖：深藍＋金「？」＋小月（kit navy／gold）"""
    t = dict(bg=('#181D3C', '#28316A')); TH['_back'] = dict(t, c='#FFF4DE', cs='#E6CFA6', a='#3F4E8E', ad='#28316A', b='#6273B8', p='#FF9DB8')
    a = frame('_back', None); s = Spr(WW, WH)
    s.A(6, 4, ['_gggg_', 'gg__gg', '____gg', '___gg_', '__gg__', '__gg__', '______', '__gg__', '__gg__'])
    s.C(15, 15, 3, 'g'); s.C(16.5, 14, 2.6, '.')
    inner = render(s, {'g': GOLD}, special={})
    over(a, inner, WX, WY)
    for i in range(5):
        x = 5 + i * 4; y = WY + WH + 3; a[y:y + 2, x:x + 2] = hx('#28316A')
    return a
