#!/usr/bin/env python3
"""6c 夢境：4 主題 tileset（56×56 art／格，每主題 4 款）＋ fog 格＋夢碎片 icon＋rail icon。
純 Pillow／numpy 程序化像素；alpha 0／255；每主題 ≤12 色（連外描）；光源左上。"""
import numpy as np
from bt6_px import Spr, render, over, hx, BAYER, LINE, ncol
T = 56
PAL = {
 'forest': dict(line='#24172C', g0='#233A35', g1='#2F4F3E', g2='#3F6B4A', g3='#6E9A5A', cap0='#9E2F55', cap1='#E2577F', cap2='#FF9DB8',
                stem='#F3E2C0', glow='#FFF5DC', fly='#F2E86A', vio='#2A2450'),
 'lake':   dict(line='#24172C', w0='#1E3F6E', w1='#2E64A0', w2='#4D93C8', w3='#9FD4F2', foam='#E9F6FF', lp0='#2F6B48', lp1='#4E9A58',
                lp2='#8BCB6A', fl='#FF9DB8', st0='#8C91AE', st1='#C5C9DC'),
 'toy':    dict(line='#24172C', f0='#B98AA8', f1='#E6B8CF', f2='#F8E2EC', r0='#9E2F55', r1='#E2577F', y0='#E09A2A', y1='#FFD06A',
                b0='#3E86C8', b1='#7CC6F2', mint='#86E6DC', wh='#FFFFFF'),
 'star':   dict(line='#24172C', s0='#10132A', s1='#1B1846', s2='#2C2868', c0='#8F85C2', c1='#C9C0F0', c2='#F3EEFA', st='#FFE08A',
                sth='#FFF6CF', moon='#FFD45A', vi='#7A5CD6', pk='#FF9DB8'),
}
def C(th, k): return hx(PAL[th][k])

def base_tile(th, ground, seed):
    """ground：[暗, 中, 亮, 高光] 4 個 key。底色＋左上光（Bayer）＋細紋＋外描＋斜角"""
    a = np.zeros((T, T, 4), np.uint8); yy, xx = np.mgrid[0:T, 0:T]; bay = BAYER[yy % 4, xx % 4]
    g = [C(th, k) for k in ground]
    lit = 1 - (xx + yy) / (2 * T)                               # 左上 1 → 右下 0
    a[:] = g[1]
    a[(lit * 0.9 + 0.12 * np.sin(xx / 5.0 + seed) * np.cos(yy / 6.0 + seed)) > 0.62 + 0.25 * bay] = g[2]
    a[(lit < 0.28 + 0.2 * bay)] = g[0]
    rng = np.random.RandomState(seed)
    for _ in range(34):                                         # 細紋（短橫）
        x, y = rng.randint(3, T - 6), rng.randint(3, T - 4); c = g[0] if lit[y, x] < .55 else g[2]
        a[y, x:x + rng.randint(2, 4)] = c
    # 邊：外 1px 描線、內 1px 左上高光／右下暗
    ch = 3; cm = np.zeros((T, T), bool)
    for (cx, cy) in ((0, 0), (T - 1, 0), (0, T - 1), (T - 1, T - 1)): cm |= (abs(xx - cx) + abs(yy - cy)) < ch
    edge = (xx == 0) | (yy == 0) | (xx == T - 1) | (yy == T - 1)
    ring2 = ((xx == 1) | (yy == 1)) & ~edge; ring3 = ((xx == T - 2) | (yy == T - 2)) & ~edge
    a[ring2] = g[3]; a[ring3] = g[0]; a[ring2 & ring3] = g[1]
    a[edge] = LINE
    dch = np.zeros((T, T), bool)
    for (cx, cy) in ((0, 0), (T - 1, 0), (0, T - 1), (T - 1, T - 1)): dch |= (abs(xx - cx) + abs(yy - cy)) == ch
    a[dch] = LINE; a[cm] = 0
    return a

def obj(a, th, fn, mats, special=None, dx=0, dy=0):
    s = Spr(T, T); fn(s); o = render(s, {k: tuple(PAL[th][c] for c in v) for k, v in mats.items()},
                                   special={k: PAL[th][v] for k, v in (special or {}).items()})
    over(a, o, dx, dy); return a

# ---------------------------------------------------------------- forest 蘑菇森林
FM = {'c': ('cap2', 'cap1', 'cap0'), 's': ('glow', 'stem', 'stem'), 'g': ('g3', 'g2', 'g1'), 'n': ('stem', 'g3', 'g2')}
FS = {'o': 'glow', 'y': 'fly', 'v': 'vio', 'k': 'line'}
def mush(s, x, y, r, face=False, spots=True):
    """x,y＝傘底中心；r＝傘半闊"""
    s.R(x - max(1, r // 3), y, x + max(1, r // 3), y + r + 1, 's')
    s.E(x + .5, y + .5, r + .5, r * .7 + .5, 'c'); s.R(x - r, y + 1, x + r, y + 1, '.')
    s.R(x - max(1, r // 3), y + 1, x + max(1, r // 3), y + 1, 's')
    if spots and r >= 3: s.P([(x - r // 2, y - r // 3), (x + r // 2, y - r // 2 + 1), (x, y - int(r * .55))], 'o')
    if face and r >= 2: s.P([(x - 1, y + 3), (x + 1, y + 3)], 'k')
def grass(s, x, y, h=3):
    s.L([(x, y), (x - 1, y - h)], 'g'); s.L([(x + 1, y), (x + 2, y - h + 1)], 'g'); s.P([(x, y - h + 1)], 'g')
def forest(v):
    th = 'forest'; a = base_tile(th, ['g0', 'g1', 'g2', 'g3'], 11 + v)
    yy, xx = np.mgrid[0:T, 0:T]
    # 中間淺色苔圈（團絨企位）：棋盤 dither 圈
    d = np.hypot((xx - 28) / 1.25, yy - 36)
    a[(d < 13) & ((xx + yy) % 2 == 0) & (a[..., 3] == 255) & ~np.all(a[..., :3] == LINE[:3], -1)] = C(th, 'g2')
    a[(d < 9) & (a[..., 3] == 255) & ~np.all(a[..., :3] == LINE[:3], -1)] = C(th, 'g2')
    def f(s):
        if v == 0: mush(s, 11, 13, 6, face=True); mush(s, 45, 10, 4); mush(s, 50, 44, 3); grass(s, 6, 50); grass(s, 40, 22)
        elif v == 1: mush(s, 44, 14, 8, face=True); mush(s, 9, 44, 4); mush(s, 15, 48, 2, spots=False); grass(s, 22, 12); grass(s, 50, 52)
        elif v == 2:
            for (x, y, r) in ((8, 12, 3), (20, 6, 2), (36, 6, 2), (48, 12, 3), (6, 32, 2), (50, 32, 2)): mush(s, x, y, r)
            grass(s, 10, 52); grass(s, 46, 52)
        else:
            s.E(12, 12, 9, 5, 'n'); s.R(3, 12, 21, 18, 'n'); s.E(12, 19, 9, 3, 'n'); s.E(12, 12, 6, 3, 's'); s.E(12, 12, 3, 1.4, 'n')
            mush(s, 22, 11, 3); mush(s, 46, 40, 5, face=True); grass(s, 44, 12); grass(s, 8, 50)
        for (x, y) in ((30, 8), (6, 26), (52, 24), (26, 52))[: 2 + v % 3]: s.P([(x + v, y)], 'y')
    obj(a, th, f, FM, FS)
    return a

# ---------------------------------------------------------------- lake 水珠湖
LM = {'l': ('lp2', 'lp1', 'lp0'), 's': ('st1', 'st1', 'st0'), 'b': ('foam', 'w3', 'w2'), 'f': ('foam', 'fl', 'fl')}
def lily(s, cx, cy, rx, ry, notch=True):
    s.E(cx, cy, rx, ry, 'l')
    if notch: s.PG([(cx, cy), (cx + rx + 1, cy - ry * .45), (cx + rx + 1, cy + ry * .1)], '.')
def bubble(s, x, y, r):
    s.C(x, y, r, 'b'); s.P([(int(x - r * .4), int(y - r * .4))], 'w')
def lake(v):
    th = 'lake'; a = base_tile(th, ['w0', 'w1', 'w2', 'w3'], 21 + v)
    rng = np.random.RandomState(40 + v)
    for _ in range(7):                                          # 水紋（短淺色橫線，近大遠細）
        x, y = rng.randint(4, 44), rng.randint(5, 52); a[y, x:x + rng.randint(3, 7)] = C(th, 'w3')
    def f(s):
        if v == 0: lily(s, 28, 38, 17, 9); s.E(28, 37, 12, 6, 'l'); bubble(s, 10, 10, 3); bubble(s, 18, 6, 1.6); bubble(s, 46, 14, 2.4)
        elif v == 1:
            for (x, y, r) in ((14, 46, 6), (28, 36, 8), (44, 46, 5)): s.E(x, y, r, r * .55, 's')
            bubble(s, 42, 12, 3.2); bubble(s, 12, 14, 2); s.P([(30, 10)], 'b')
        elif v == 2: lily(s, 28, 38, 16, 9); bubble(s, 47, 8, 2.6); s.C(10, 14, 3, 'f'); s.P([(10, 13)], 'w'); lily(s, 10, 18, 5, 2.5, False)
        else:
            lily(s, 28, 38, 17, 9); s.C(44, 12, 4.4, 'b'); s.C(46, 11, 4, '.'); bubble(s, 12, 10, 2.4); bubble(s, 8, 18, 1.4)
    obj(a, th, f, LM, {'w': 'foam'})
    return a

# ---------------------------------------------------------------- toy 玩具房
TM = {'r': ('r1', 'r1', 'r0'), 'y': ('y1', 'y1', 'y0'), 'b': ('b1', 'b1', 'b0'), 'm': ('wh', 'mint', 'b0'), 'f': ('wh', 'f1', 'f0')}
def block(s, x, y, n, mat, letter=None):
    s.R(x, y, x + n - 1, y + n - 1, mat)
    if n >= 6: s.R(x + 2, y + 2, x + n - 3, y + n - 3, mat.upper()); s.R(x + 3, y + 3, x + n - 4, y + n - 4, mat)
def toy(v):
    th = 'toy'; a = np.zeros((T, T, 4), np.uint8); yy, xx = np.mgrid[0:T, 0:T]
    a = base_tile(th, ['f0', 'f1', 'f2', 'wh'], 31 + v)
    # 棋盤地板（8px 格）
    chk = ((xx // 8 + yy // 8) % 2 == 0) & (a[..., 3] == 255) & ~np.all(a[..., :3] == LINE[:3], -1) & (xx > 1) & (yy > 1) & (xx < T - 2) & (yy < T - 2)
    a[chk & np.all(a[..., :3] == np.array(C(th, 'f1'))[:3], -1)] = C(th, 'f2')
    def f(s):
        if v == 0: block(s, 4, 6, 9, 'r'); block(s, 14, 9, 6, 'y'); block(s, 8, 0, 0, 'b'); s.C(46, 13, 6, 'b'); s.L([(41, 13), (51, 13)], 'y', 2); s.P([(44, 10)], 'w')
        elif v == 1:
            block(s, 40, 8, 8, 'b'); block(s, 42, 16, 6, 'y'); s.PG([(42, 7), (45.5, 3), (49, 7)], 'r')
            s.PG([(10, 42), (12, 46), (16, 46), (13, 49), (14, 53), (10, 50), (6, 53), (7, 49), (4, 46), (8, 46)], 'y'); s.P([(9, 48), (11, 48)], 'k')
        elif v == 2:
            s.L([(3, 50), (53, 50)], 'f'); s.L([(3, 53), (53, 53)], 'f')
            for x in range(5, 52, 6): s.R(x, 49, x + 1, 54, 'f')
            s.C(10, 10, 5, 'm'); s.P([(8, 8)], 'w'); block(s, 42, 6, 9, 'r')
        else:
            s.R(6, 8, 14, 16, 'y'); s.C(10, 6.5, 2.2, 'y'); s.C(15.5, 12, 2.2, 'y')   # 拼圖塊
            s.C(46, 46, 5, 'r'); s.C(46, 46, 2.5, 'y'); s.C(46, 46, 1, 'b'); block(s, 40, 6, 7, 'm')
    obj(a, th, f, TM, {'w': 'wh', 'k': 'line'})
    return a

# ---------------------------------------------------------------- star 星空
SM = {'c': ('c2', 'c1', 'c0'), 'm': ('sth', 'moon', 'moon'), 'v': ('c1', 'vi', 'vi')}
def sparkle(a, th, x, y, big=False):
    c = C(th, 'st'); h = C(th, 'sth')
    a[y, x] = h
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)): a[y + dy, x + dx] = c
    if big:
        for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)): a[y + dy, x + dx] = c
def cloud(s, cx, cy, w):
    s.E(cx, cy + 2, w, 4.5, 'c'); s.C(cx - w * .45, cy, w * .38, 'c'); s.C(cx + w * .1, cy - 2, w * .45, 'c'); s.C(cx + w * .55, cy + .5, w * .32, 'c')
def star(v):
    th = 'star'; a = base_tile(th, ['s0', 's1', 's2', 'vi'], 41 + v)
    rng = np.random.RandomState(50 + v)
    for _ in range(10):
        x, y = rng.randint(4, 52), rng.randint(4, 30); a[y, x] = C(th, 'st') if rng.rand() < .5 else C(th, 'c1')
    def f(s):
        cloud(s, 28, 40, 19)                                     # 雲台（團絨企位）
        if v == 0: s.C(12, 12, 6, 'm'); s.C(15, 10, 5, '.')
        elif v == 1: cloud(s, 46, 12, 6)
        elif v == 2: s.C(44, 12, 4.4, 'v'); s.L([(37, 13), (51, 11)], 'c')
        else: s.C(12, 12, 5, 'm'); s.C(14.5, 10.5, 4.2, '.'); cloud(s, 44, 16, 5)
    obj(a, th, f, SM, {'k': 'line'})
    for (x, y, b) in ((40, 6, True), (24, 10, False), (6, 26, False), (50, 28, True))[: 2 + v % 3]: sparkle(a, th, x, y, b)
    return a

THEMES = {'forest': forest, 'lake': lake, 'toy': toy, 'star': star}
NV = 4
def tileset(th): return [THEMES[th](v) for v in range(NV)]

# ---------------------------------------------------------------- fog（未揭開格）：75% 棋盤（冇半透明）＋雲絲
def fog():
    a = np.zeros((T, T, 4), np.uint8); yy, xx = np.mgrid[0:T, 0:T]
    dark, mid, lite = hx('#0C0920'), hx('#2A2450'), hx('#574F8A')
    m = ~(((xx % 2) == 0) & ((yy % 2) == 0))                  # 3/4 像素
    a[m] = dark
    for (cx, cy, rx) in ((18, 18, 12), (38, 36, 14)):
        e = ((xx - cx) / rx) ** 2 + ((yy - cy) / 3.2) ** 2 <= 1; a[e & m] = mid
        e2 = ((xx - cx + 2) / (rx * .6)) ** 2 + ((yy - cy + 1) / 1.4) ** 2 <= 1; a[e2 & m] = lite
    # 中間「？」（mid 色）提示可以行過去
    q = Spr(T, T); q.A(25, 22, ['_kkk_', 'k___k', '___k_', '__k__', '_____', '__k__'])
    qa = render(q, {}, special={'k': '#574F8A'}, outline=False); over(a, qa)
    for (cx, cy) in ((0, 0), (T - 1, 0), (0, T - 1), (T - 1, T - 1)): a[(abs(xx - cx) + abs(yy - cy)) < 3] = 0
    return a

# ---------------------------------------------------------------- icons（16×16，同 kit ic_* 一樣）
def icons():
    import ui_hd2d_v2_icons as UI
    UI.MAT.setdefault('d', ('#FFF6C0', '#FFD45A', '#E09A2A'))
    out = {}
    def frag_forest(i):  # 發光孢子（四角星＋菇紅芯）
        i.PG([(7.5, 1.2), (9.4, 5.6), (13.8, 7.5), (9.4, 9.4), (7.5, 13.8), (5.6, 9.4), (1.2, 7.5), (5.6, 5.6)], 'p'); i.C(7.5, 7.5, 2.6, 'r'); i.P([(6, 6)], 'w')
    def frag_lake(i):    # 水珠碎片
        i.PG([(7.5, 1.2), (12.5, 8), (2.5, 8)], 'b'); i.C(7.5, 9.5, 5, 'b'); i.P([(5, 7), (5, 8)], 'w'); i.C(13, 2.5, 1.6, 'c')
    def frag_toy(i):     # 玩具星（黃＋粉邊）
        i.PG([(7.5, 1.2), (9.6, 5.4), (13.9, 5.8), (10.7, 9), (11.8, 13.8), (7.5, 11.4), (3.2, 13.8), (4.3, 9), (1.1, 5.8), (5.4, 5.4)], 'y'); i.C(7.5, 8, 2, 'p'); i.P([(6, 5)], 'w')
    def frag_star(i):    # 星屑碎片（菱形水晶）
        i.PG([(7.5, 1.2), (13, 7.5), (7.5, 13.8), (2, 7.5)], 'v'); i.PG([(7.5, 7.5), (13, 7.5), (7.5, 13.8)], 'V'); i.P([(5, 6), (6, 5)], 'w'); i.P([(13, 1), (14, 2), (12, 2), (13, 3)], 'd')
    def ic_dream(i):     # 入夢：月亮戴睡帽＋z
        i.C(7, 9, 5.4, 'y'); i.C(10.4, 6.8, 4.6, '.'); i.PG([(1.5, 5), (6, 1.4), (9, 4)], 'v'); i.R(2, 4, 8, 5, 'c'); i.P([(9, 2), (10, 2)], 'c')
        i.face(5, 10, 2, 'dot', eye='closed'); i.A(11, 9, ['www', '_w_', 'www'])
    def ic_dreambook(i): # 夢圖鑑：書＋星
        i.R(1, 2, 14, 14, 'v', cut=1); i.R(3, 3, 12, 13, 'c'); i.R(13, 3, 13, 13, 'V')
        i.PG([(8, 4), (9.2, 7), (12.2, 7.3), (9.9, 9.2), (10.6, 12), (8, 10.5), (5.4, 12), (6.1, 9.2), (3.8, 7.3), (6.8, 7)], 'y')
    for n, fn in (('frag_forest', frag_forest), ('frag_lake', frag_lake), ('frag_toy', frag_toy), ('frag_star', frag_star), ('ic_dream', ic_dream), ('ic_dreambook', ic_dreambook)):
        ic = UI.Ic(); fn(ic); out[n] = np.array(UI.render(ic))
    return out
