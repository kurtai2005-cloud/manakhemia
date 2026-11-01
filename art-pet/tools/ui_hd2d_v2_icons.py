# 《微光小圃》HD-2D v2 kit — 手點像素 icon（16×16 art，1x 原生；冇縮圖、冇 AA）
# 遊美 2026-11-02。做法：每個 icon 用像素級形狀（圓／橢圓／多邊形／矩形／線／ASCII 點）逐粒落色，
# 之後統一：材質自動左上受光（hi／base／shade 三階）、1px #24172C 外描線、可愛表情（眼＋腮紅＋口）。純 numpy／Pillow。
import numpy as np
from PIL import Image, ImageDraw

def hx(h): h = h.lstrip('#'); return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)
LINE = hx('#24172C')
# 材質：hi, base, shade
MAT = {
    'r': ('#FFC2D3', '#FF7F9E', '#D04A72'),   # 玫瑰紅（心）
    'p': ('#FFE3EC', '#FFB3CA', '#E57EA2'),   # 粉
    'o': ('#FFE0C2', '#FFA868', '#DD6E38'),   # 蜜桃橙
    'y': ('#FFF6C0', '#FFD45A', '#E09A2A'),   # 金黃
    'g': ('#DDF8B8', '#86D068', '#4C9A48'),   # 草綠
    'm': ('#4E7A5A', '#2F5240', '#1E3A2E'),   # 紫菜深綠
    't': ('#D8FFF6', '#7FE0D4', '#3A9EB4'),   # 薄荷青
    'b': ('#DDF2FF', '#7CC6F2', '#3E86C8'),   # 天藍
    'v': ('#EEE4FF', '#B39BF6', '#7458CC'),   # 淡紫
    'n': ('#F2CC9C', '#C98A55', '#8E5A34'),   # 木啡
    'c': ('#FFFFFF', '#FFF4DE', '#E6CFA6'),   # 奶白
    's': ('#F4F5FC', '#C5C9DC', '#8C91AE'),   # 銀灰
    'u': ('#8A98D8', '#56619E', '#353D70'),   # 深藍
    'e': ('#FFE9A8', '#F2B640', '#B87418'),   # 深金（皇冠／星）
}
SPECIAL = {'k': hx('#2A1A30'), 'w': hx('#FFFFFF'), '*': hx('#FF8FB0'), 'K': LINE, 'h': hx('#FFFFFF')}
N = 16

class Ic:
    def __init__(s): s.m = np.full((N, N), '.', dtype='<U1'); s.yy, s.xx = np.mgrid[0:N, 0:N]
    def set(s, mask, mat): s.m[mask] = mat; return s
    def C(s, cx, cy, r, mat): return s.set((s.xx + .5 - cx) ** 2 + (s.yy + .5 - cy) ** 2 <= r * r, mat)
    def E(s, cx, cy, rx, ry, mat): return s.set(((s.xx + .5 - cx) / rx) ** 2 + ((s.yy + .5 - cy) / ry) ** 2 <= 1, mat)
    def R(s, x0, y0, x1, y1, mat, cut=0):
        m = (s.xx >= x0) & (s.xx <= x1) & (s.yy >= y0) & (s.yy <= y1)
        if cut:
            for (cx, cy) in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
                m &= ~((abs(s.xx - cx) + abs(s.yy - cy)) < cut)
        return s.set(m, mat)
    def PG(s, pts, mat):
        im = Image.new('L', (N, N), 0); ImageDraw.Draw(im).polygon([(x, y) for x, y in pts], fill=255); return s.set(np.array(im) > 0, mat)
    def L(s, pts, mat, w=1):
        im = Image.new('L', (N, N), 0); ImageDraw.Draw(im).line([(x, y) for x, y in pts], fill=255, width=w); return s.set(np.array(im) > 0, mat)
    def P(s, pts, mat):
        for x, y in pts:
            if 0 <= x < N and 0 <= y < N: s.m[y, x] = mat
        return s
    def A(s, x, y, rows):
        for j, r in enumerate(rows):
            for i, ch in enumerate(r):
                if ch != ' ' and ch != '_': s.m[y + j, x + i] = '.' if ch == '-' else ch
        return s
    def face(s, cx, cy, gap=3, mouth='dot', blush=True, eye='dot'):
        """cx：兩眼中間（左眼 x＝cx−gap//2−?）；眼 1px，腮紅喺眼外下"""
        lx, rx = cx - (gap + 1) // 2, cx + gap // 2
        if eye == 'dot': s.P([(lx, cy), (rx, cy)], 'k')
        elif eye == 'tall': s.P([(lx, cy), (rx, cy), (lx, cy - 1), (rx, cy - 1)], 'k'); s.P([(lx, cy - 1), (rx, cy - 1)], 'k')
        elif eye == 'happy': s.P([(lx - 1, cy), (lx, cy - 1), (lx + 1, cy), (rx - 1, cy), (rx, cy - 1), (rx + 1, cy)], 'k')
        elif eye == 'closed': s.P([(lx - 1, cy), (lx, cy), (rx, cy), (rx + 1, cy)], 'k')
        if blush: s.P([(lx - 1, cy + 1), (rx + 1, cy + 1)], '*')
        if mouth == 'dot': s.P([(cx - (1 if gap % 2 == 0 else 0) if False else (lx + rx) // 2, cy + 1)], 'k')
        elif mouth == 'w': mx = (lx + rx) // 2; s.P([(mx, cy + 1), (mx + 1, cy + 1)], 'k')
        elif mouth == 'open': mx = (lx + rx) // 2; s.P([(mx, cy + 1), (mx, cy + 2)], 'r')
        return s

def render(ic, spec=True):
    m = ic.m; a = np.zeros((N, N, 4), np.uint8)
    solid = m != '.'
    for ch in np.unique(m):
        if ch == '.': continue
        msk = m == ch
        if ch in SPECIAL: a[msk] = SPECIAL[ch]; continue
        key = ch.lower(); hi, base, sh = (hx(c) for c in MAT[key])
        if ch.isupper(): a[msk] = sh; continue
        a[msk] = base
        same = msk
        dn = np.zeros_like(msk); dn[:-1] = ~same[1:] & ~np.isin(m[1:], list('kw*h')); dn[-1] = True
        rt = np.zeros_like(msk); rt[:, :-1] = ~same[:, 1:] & ~np.isin(m[:, 1:], list('kw*h')); rt[:, -1] = True
        upo = np.zeros_like(msk); upo[1:] = ~solid[:-1]; upo[0] = True
        lfo = np.zeros_like(msk); lfo[:, 1:] = ~solid[:, :-1]; lfo[:, 0] = True
        a[msk & (dn | rt)] = sh
        a[msk & (upo | lfo) & ~(dn | rt)] = hi
    # 外描線（4 鄰）
    M = solid.copy(); O = np.zeros_like(M)
    O[1:] |= M[:-1]; O[:-1] |= M[1:]; O[:, 1:] |= M[:, :-1]; O[:, :-1] |= M[:, 1:]; O &= ~M
    a[O] = LINE
    return Image.fromarray(a, 'RGBA')

ICONS = {}
def reg(name):
    def d(fn): ICONS[name] = fn; return fn
    return d

# ------------------------------------------------------------------ 照顧
@reg('feed')        # 飯糰
def _(i):
    i.PG([(7.5, 1.5), (14.5, 13.5), (0.5, 13.5)], 'c'); i.R(2, 12, 13, 13, 'c')
    i.R(5, 9, 10, 13, 'm'); i.face(7, 7, 3, 'w')
@reg('clean')       # 水滴＋泡
def _(i):
    i.PG([(6.5, 1), (11.5, 8), (1.5, 8)], 'b'); i.C(6.5, 9.5, 5, 'b'); i.C(12.5, 3, 2, 'c'); i.P([(12, 2)], 'w'); i.P([(4, 6), (4, 7)], 'w')
    i.face(6, 10, 3, 'dot')
@reg('sleep')       # 月亮＋z
def _(i):
    i.C(7, 8.5, 6.2, 'y'); i.C(10.6, 6, 5, '.'); i.P([(3, 11), (5, 12)], 'k'); i.P([(2, 12), (6, 13)], '*')
    i.A(11, 0, ['wwww', '__w_', '_w__', 'wwww'])
@reg('play')        # 波波
def _(i):
    i.C(7.5, 8, 6.6, 'p'); i.PG([(1, 9), (14, 4), (14, 8), (1, 13)], 'y'); i.face(7, 7, 4, 'w')
@reg('play_cat')    # 貓頭（修正：清晰三角耳＋大眼）
def _(i):
    i.PG([(1, 1), (6, 5), (1, 8)], 'y'); i.PG([(15, 1), (10, 5), (15, 8)], 'y')
    i.E(8, 9, 6.8, 5.2, 'y'); i.P([(2, 3), (3, 4), (13, 3), (12, 4)], 'p')
    i.face(7, 9, 4, 'w', eye='tall'); i.P([(1, 10), (2, 10), (13, 10), (14, 10)], 'K')
@reg('heart')
def _(i):
    i.C(4.8, 5.5, 3.8, 'r'); i.C(10.2, 5.5, 3.8, 'r'); i.PG([(1, 6.5), (14, 6.5), (7.5, 14)], 'r'); i.P([(3, 4)], 'w'); i.face(7, 7, 4)
@reg('heart_bunny') # 兔耳心
def _(i):
    i.E(4.5, 3, 1.6, 3.2, 'c'); i.E(10.5, 3, 1.6, 3.2, 'c'); i.P([(4, 2), (4, 3), (10, 2), (10, 3)], 'p')
    i.C(4.8, 8, 3.6, 'p'); i.C(10.2, 8, 3.6, 'p'); i.PG([(1.2, 8.5), (13.8, 8.5), (7.5, 15)], 'p'); i.face(7, 9, 4)
@reg('bond')        # 雙心
def _(i):
    i.C(3.8, 5, 2.8, 'p'); i.C(7.6, 5, 2.8, 'p'); i.PG([(1, 5.5), (10.4, 5.5), (5.7, 11)], 'p')
    i.C(8.3, 8, 2.9, 'r'); i.C(12.2, 8, 2.9, 'r'); i.PG([(5.5, 8.5), (15, 8.5), (10.2, 14.5)], 'r'); i.face(10, 9, 3, 'dot')
@reg('bedtime')     # 鬧鐘
def _(i):
    i.C(3, 3, 2.2, 'y'); i.C(13, 3, 2.2, 'y'); i.C(8, 8.5, 6, 'o'); i.C(8, 8.5, 4.4, 'c')
    i.L([(8, 5), (8, 9), (10, 9)], 'k'); i.P([(3, 14), (12, 14)], 'n')
@reg('water')       # 水杯
def _(i):
    i.R(2, 3, 11, 14, 'c', cut=2); i.R(12, 6, 14, 11, 'c', cut=1); i.R(12, 8, 12, 9, '.')
    i.R(4, 7, 9, 12, 'b', cut=1); i.face(6, 9, 3)
# ------------------------------------------------------------------ 貨幣／系統
@reg('light')       # 光粒：四角星
def _(i):
    i.PG([(7.5, 0.5), (9.6, 5.4), (14.5, 7.5), (9.6, 9.6), (7.5, 14.5), (5.4, 9.6), (0.5, 7.5), (5.4, 5.4)], 't'); i.P([(6, 6), (7, 5)], 'w')
@reg('star')
def _(i):
    i.PG([(7.5, 0.5), (9.7, 5.2), (14.8, 5.6), (10.9, 9), (12.2, 14.4), (7.5, 11.6), (2.8, 14.4), (4.1, 9), (0.2, 5.6), (5.3, 5.2)], 'e'); i.face(7, 8, 3)
@reg('gift')
def _(i):
    i.R(1, 6, 14, 14, 'r', cut=1); i.R(1, 5, 14, 7, 'p'); i.R(7, 5, 8, 14, 'y'); i.C(5, 3, 2.2, 'y'); i.C(10.5, 3, 2.2, 'y'); i.P([(5, 3), (10, 3)], 'Y')
    i.face(7, 10, 5, 'dot')
@reg('mail')
def _(i):
    i.R(1, 3, 14, 12, 'c', cut=1); i.L([(1, 4), (7.5, 9), (14, 4)], 'S'); i.C(7.5, 9, 2, 'r'); i.P([(7, 8)], 'p')
@reg('house')
def _(i):
    i.PG([(7.5, 0.5), (15, 7.5), (0, 7.5)], 'o'); i.R(2, 7, 13, 14, 'c'); i.R(9, 9, 11, 14, 'n'); i.P([(12, 2), (12, 3), (12, 4)], 'n')
    i.face(5, 10, 3)
@reg('lock')
def _(i):
    i.R(3, 1, 12, 8, 's', cut=2); i.R(5, 3, 10, 8, '.'); i.R(2, 6, 13, 14, 'y', cut=1); i.A(7, 9, ['kk', 'kk', '_k']); i.P([(7, 12)], 'k')
@reg('check')
def _(i):
    i.C(7.5, 7.5, 7, 'g'); i.L([(3.5, 7.5), (6.5, 10.5), (11.5, 4.5)], 'w', 2)
@reg('clear')
def _(i):
    i.L([(2, 2), (13, 13)], 'v', 4); i.L([(13, 2), (2, 13)], 'v', 4); i.face(7, 8, 3)
@reg('plus')
def _(i):
    i.R(5, 1, 10, 14, 't', cut=1); i.R(1, 5, 14, 10, 't', cut=1); i.face(7, 7, 3)
@reg('back')
def _(i):
    i.PG([(0.5, 7.5), (7, 1), (7, 14)], 'o'); i.R(6, 5, 14, 10, 'o', cut=1); i.face(9, 7, 3)
@reg('info')
def _(i):
    i.C(7.5, 7.5, 7, 'b'); i.R(7, 3, 8, 4, 'w'); i.R(7, 6, 8, 12, 'w')
@reg('hint')        # 燈泡
def _(i):
    i.C(7.5, 6, 5.6, 'y'); i.R(5, 10, 10, 14, 's', cut=1); i.R(5, 12, 10, 12, 'S'); i.face(7, 6, 3, 'dot')
@reg('sound')
def _(i):
    i.R(1, 5, 5, 10, 'v'); i.PG([(4, 5), (9, 1), (9, 14), (4, 10)], 'v'); i.L([(11, 5), (12, 7), (12, 8), (11, 10)], 'c'); i.L([(13, 2), (14, 5), (14, 10), (13, 13)], 'c')
@reg('gear')
def _(i):
    for k in range(8):
        a = k * np.pi / 4; i.C(7.5 + 5.4 * np.cos(a), 7.5 + 5.4 * np.sin(a), 1.9, 'b')
    i.C(7.5, 7.5, 5.2, 'b'); i.face(7, 7, 3)
@reg('gear_chick')  # 齒輪小雞（設定 tab）
def _(i):
    for k in range(8):
        a = k * np.pi / 4 + np.pi / 8; i.C(7.5 + 5.3 * np.cos(a), 8 + 5.3 * np.sin(a), 1.9, 'y')
    i.C(7.5, 8, 5.2, 'y'); i.P([(7, 1), (8, 0), (6, 0)], 'y'); i.face(7, 8, 3, 'w'); i.P([(7, 9), (8, 9)], 'o')
@reg('reset')       # ↻
def _(i):
    i.C(7.5, 8, 6.2, 'o'); i.C(7.5, 8, 3.6, '.'); i.R(7, 1, 14, 6, '.'); i.PG([(7, 0), (12, 3.5), (7, 7)], 'o')
@reg('rotate')
def _(i):
    i.C(7.5, 8, 6.2, 'b'); i.C(7.5, 8, 3.6, '.'); i.R(1, 1, 8, 6, '.'); i.PG([(8, 0), (3, 3.5), (8, 7)], 'b')
@reg('flip')
def _(i):
    i.PG([(6.5, 1), (6.5, 14), (0.5, 14)], 'b'); i.PG([(8.5, 1), (8.5, 14), (14.5, 14)], 'p'); i.R(7, 0, 7, 15, 'K')
@reg('quality')     # 寶石
def _(i):
    i.PG([(3, 2), (12, 2), (15, 6), (7.5, 14.5), (0, 6)], 'b'); i.L([(0, 6), (15, 6)], 'B'); i.PG([(5, 2.5), (10, 2.5), (11.5, 5.5), (3.5, 5.5)], 't'); i.face(7, 8, 3)
@reg('lightning')   # 加速（fast）
def _(i):
    i.PG([(9, 0.5), (2, 9), (7, 9), (5, 15), (13, 6), (8, 6), (11, 0.5)], 'y')
ICONS['fast'] = ICONS['lightning']
# ------------------------------------------------------------------ 手帳
@reg('book')
def _(i):
    i.R(2, 1, 13, 14, 'v', cut=1); i.R(10, 2, 12, 13, 'c'); i.R(3, 13, 12, 14, 'V'); i.face(6, 7, 3)
@reg('book_bear')   # 熊仔手帳（手帳 tab）
def _(i):
    i.C(3.5, 2.5, 2, 'n'); i.C(11.5, 2.5, 2, 'n'); i.R(2, 3, 13, 14, 'v', cut=1); i.R(10, 4, 12, 13, 'c'); i.E(6, 9, 3.6, 3, 'c'); i.face(6, 8, 3)
@reg('diary')       # 打開本書
def _(i):
    i.PG([(0, 3), (7, 4.5), (7, 14), (0, 12.5)], 'c'); i.PG([(8, 4.5), (15, 3), (15, 12.5), (8, 14)], 'c'); i.R(7, 4, 7, 14, 'S')
    i.R(11, 1, 12, 7, 'r'); i.P([(11, 7)], '.'); i.face(4, 8, 3)
@reg('dex')         # 放大鏡
def _(i):
    i.L([(10, 10), (14, 14)], 'r', 3); i.C(6.5, 6.5, 5.6, 'y'); i.C(6.5, 6.5, 4, 'b'); i.face(6, 7, 3)
@reg('cabinet')
def _(i):
    i.R(1, 1, 14, 14, 'n', cut=1); i.R(3, 3, 12, 7, 'c'); i.R(3, 9, 12, 12, 'c'); i.P([(5, 5), (9, 5)], 'r'); i.P([(7, 4), (10, 4)], 'y'); i.P([(7, 10), (8, 10)], 'K')
@reg('badge')
def _(i):
    i.PG([(3, 0), (6, 0), (9, 6), (6, 6)], 't'); i.PG([(9, 0), (12, 0), (9, 6), (6, 6)], 'p'); i.C(7.5, 9.5, 5.2, 'y'); i.face(7, 9, 3, 'w')
@reg('ev_treasure') # 寶箱
def _(i):
    i.R(1, 3, 14, 7, 'n', cut=2); i.R(1, 7, 14, 14, 'n', cut=1); i.R(7, 3, 8, 14, 'y'); i.R(1, 7, 14, 7, 'N'); i.C(7.5, 8, 2, 'r'); i.face(4, 10, 3, 'dot', blush=False)
@reg('surprise')    # 驚喜盒
def _(i):
    i.PG([(7.5, 0), (9, 3), (12, 3.5), (9.5, 5.5), (10, 8), (7.5, 6.5), (5, 8), (5.5, 5.5), (3, 3.5), (6, 3)], 'e'); i.R(2, 8, 13, 14, 'p', cut=1); i.R(7, 8, 8, 14, 'y'); i.face(7, 11, 5)
@reg('minigame')    # 手掣
def _(i):
    i.R(0, 4, 15, 12, 't', cut=3); i.R(2, 7, 5, 8, 'c'); i.R(3, 6, 4, 9, 'c'); i.C(11, 6.5, 1.1, 'r'); i.C(12.5, 9, 1.1, 'y'); i.face(7, 9, 2, 'dot', blush=False)
# ------------------------------------------------------------------ 圖鑑分類 d_*
@reg('d_cloud')
def _(i):
    i.C(4.5, 9, 3.6, 'c'); i.C(8, 6.5, 4.4, 'c'); i.C(11.5, 9, 3.4, 'c'); i.R(2, 9, 13, 12, 'c', cut=1); i.face(8, 9, 3)
@reg('d_heart')
def _(i): ICONS['heart'](i)
@reg('d_leaf')
def _(i):
    i.PG([(14, 1), (11, 9), (5, 14), (1, 14), (1, 10), (6, 4)], 'g'); i.L([(2, 13), (11, 4)], 'G'); i.P([(10, 3), (11, 2)], 'g')
@reg('d_paw')
def _(i):
    i.E(7.5, 11, 4.4, 3.4, 'p'); i.C(2.2, 6.2, 1.7, 'p'); i.C(5.5, 3, 1.7, 'p'); i.C(9.5, 3, 1.7, 'p'); i.C(12.8, 6.2, 1.7, 'p'); i.face(7, 11, 3)
@reg('d_spark')
def _(i):
    i.PG([(7.5, 0), (9, 6), (15, 7.5), (9, 9), (7.5, 15), (6, 9), (0, 7.5), (6, 6)], 't'); i.P([(7, 6)], 'w')
@reg('d_star')
def _(i): ICONS['star'](i)
# ------------------------------------------------------------------ 屋仔 4b
@reg('decorate')    # 調色板
def _(i):
    i.E(7.5, 8, 7, 6, 'n'); i.C(10.5, 11, 1.6, '.'); i.C(4, 6, 1.4, 'r'); i.C(7, 4, 1.4, 'y'); i.C(10.5, 5, 1.4, 't'); i.C(4.5, 10, 1.4, 'v')
@reg('furniture')   # 梳化
def _(i):
    i.R(2, 3, 13, 9, 'p', cut=2); i.R(0, 7, 15, 12, 'p', cut=1); i.R(3, 9, 12, 11, 'r'); i.P([(1, 13), (14, 13)], 'n'); i.face(7, 6, 3)
@reg('store')       # 紙箱
def _(i):
    i.R(1, 3, 14, 14, 'n', cut=1); i.R(1, 3, 14, 5, 'N'); i.PG([(7.5, 6), (11, 9.5), (9, 9.5), (9, 13), (6, 13), (6, 9.5), (4, 9.5)], 'c')
# ------------------------------------------------------------------ 5a 家族
@reg('family_tree')
def _(i):
    i.R(7, 9, 8, 14, 'n'); i.C(7.5, 6.5, 5.5, 'g'); i.C(4, 5, 1.6, 'y'); i.C(11, 4, 1.6, 'p'); i.C(9.5, 9, 1.4, 't'); i.face(7, 6, 3, 'dot', blush=False)
@reg('family_level')
def _(i):
    i.PG([(1, 4), (14, 4), (14, 9), (7.5, 15), (1, 9)], 'v'); i.PG([(2, 0), (5, 3), (7.5, 0), (10, 3), (13, 0), (13, 4), (2, 4)], 'e'); i.face(7, 8, 3)
@reg('crown')
def _(i):
    i.PG([(0.5, 3), (4.5, 7), (7.5, 1), (10.5, 7), (14.5, 3), (13, 13), (2, 13)], 'e'); i.R(2, 11, 13, 13, 'Y'); i.C(7.5, 1.5, 1.4, 'r'); i.P([(4, 12), (11, 12)], 't'); i.P([(7, 12)], 'r')
@reg('egg_tr')      # 團絨蛋（奶油＋光點）
def _(i):
    i.E(7.5, 8.5, 5.8, 6.8, 'c'); i.P([(5, 6), (9, 4), (10, 10), (6, 11)], 'y'); i.P([(4, 4)], 'w')
@reg('egg_kid')     # 細佬蛋（藍斑）
def _(i):
    i.E(7.5, 8.5, 5.8, 6.8, 'b'); i.C(5, 6, 1.2, 'c'); i.C(10, 9, 1.4, 'c'); i.C(6, 12, 1, 'c'); i.P([(4, 4)], 'w')
@reg('pets')        # 兩隻寵物
def _(i):
    i.E(5, 9.5, 4.6, 4.2, 't'); i.P([(3, 5), (2, 4)], 't'); i.face(5, 10, 3)
    i.E(11, 10, 4, 3.8, 'p'); i.P([(13, 6), (14, 5)], 'p'); i.face(11, 11, 3)
@reg('visitor')     # 揮手小人＋星
def _(i):
    i.C(7.5, 9.5, 5.4, 'o'); i.C(12.5, 3, 2.2, 'y'); i.P([(2, 5), (3, 6)], 'o'); i.face(7, 9, 3, 'w', eye='happy')
@reg('xp')
def _(i):
    i.PG([(7.5, 0.5), (13.5, 4), (13.5, 11), (7.5, 14.5), (1.5, 11), (1.5, 4)], 'v'); i.PG([(7.5, 3), (11.5, 7.5), (9, 7.5), (9, 12), (6, 12), (6, 7.5), (3.5, 7.5)], 'w')
@reg('title')       # 稱號緞帶
def _(i):
    i.PG([(0, 4), (3, 4), (3, 11), (0, 11), (1.5, 7.5)], 'R'); i.PG([(15, 4), (12, 4), (12, 11), (15, 11), (13.5, 7.5)], 'R'); i.R(2, 3, 13, 10, 'r', cut=1); i.R(5, 6, 10, 7, 'y')
# ------------------------------------------------------------------ 5b 每日
@reg('expedition')  # 背囊
def _(i):
    i.R(3, 1, 12, 3, 'N', cut=1); i.R(4, 2, 11, 2, '.'); i.R(2, 3, 13, 14, 'n', cut=2); i.R(4, 8, 11, 13, 'o', cut=1); i.R(7, 8, 8, 9, 'y')
@reg('rest')        # 枕頭＋zz
def _(i):
    i.R(0, 6, 13, 13, 'c', cut=3); i.P([(4, 9), (7, 9)], 'k'); i.P([(3, 10), (8, 10)], '*'); i.A(11, 0, ['wwww', '__w_', '_w__', 'wwww'])
@reg('shards')      # 星石碎
def _(i):
    i.PG([(4, 1), (8, 5), (5, 11), (1, 6)], 'v'); i.PG([(11, 3), (14, 8), (11, 14), (8, 9)], 't'); i.P([(4, 4), (11, 6)], 'w')
@reg('job_chef')
def _(i):
    i.C(4.5, 4, 3, 'c'); i.C(8, 3, 3.2, 'c'); i.C(11, 4, 3, 'c'); i.R(3, 5, 12, 12, 'c', cut=1); i.R(3, 11, 12, 13, 'S'); i.face(7, 8, 3)
# ------------------------------------------------------------------ 5c 傳承
@reg('inherit')     # 蛋＋箭嘴光
def _(i):
    i.E(9, 9.5, 5, 5.6, 'c'); i.P([(8, 8), (11, 11), (7, 12)], 'y'); i.PG([(0, 4), (4, 0), (4, 2), (7, 2), (7, 6), (4, 6), (4, 8)], 'y')
@reg('pattern')     # 花紋色塊
def _(i):
    i.R(1, 1, 14, 14, 'b', cut=2); i.L([(1, 6), (4, 4), (8, 7), (11, 4), (14, 6)], 'c', 2); i.L([(1, 11), (4, 9), (8, 12), (11, 9), (14, 11)], 'c', 2)
@reg('trick')       # 招式：魔法棒
def _(i):
    i.L([(2, 13), (9, 6)], 'n', 2); i.PG([(11, 0), (12.3, 3.2), (15.5, 4.5), (12.3, 5.8), (11, 9), (9.7, 5.8), (6.5, 4.5), (9.7, 3.2)], 'y'); i.P([(3, 4), (14, 11)], 'w')
# ------------------------------------------------------------------ 花園／小遊戲
@reg('sprout')      # 盆栽（小圃 tab）
def _(i):
    i.C(4.5, 4, 3, 'g'); i.C(10.5, 4, 3, 'g'); i.R(7, 5, 8, 8, 'G'); i.PG([(2, 8), (13, 8), (12, 14), (3, 14)], 'o'); i.R(2, 8, 13, 9, 'O'); i.face(7, 11, 3)
@reg('seed')
def _(i):
    i.E(7.5, 9, 4.8, 5.8, 'n'); i.PG([(7, 0), (11, 2), (8, 4)], 'g'); i.face(7, 9, 3)
@reg('mg_tease')    # 逗貓羽毛
def _(i):
    i.PG([(14, 1), (12, 8), (6, 13), (2, 14), (3, 10), (8, 4)], 'p'); i.L([(1, 15), (12, 3)], 'R'); i.face(8, 7, 2, 'dot', blush=False)
@reg('mg_stardust')
def _(i):
    i.PG([(9.5, 0.5), (11, 4), (15, 4.4), (12, 7), (13, 11), (9.5, 9), (6, 11), (7, 7), (4, 4.4), (8, 4)], 'e'); i.P([(2, 12), (4, 14), (5, 11)], 't'); i.P([(1, 9)], 'y'); i.face(9, 6, 2, 'dot', blush=False)
@reg('mg_leaf')
def _(i):
    i.PG([(14, 1), (13, 8), (7, 13), (1, 13), (3, 7), (9, 2)], 'g'); i.L([(1, 14), (9, 6)], 'G'); i.face(9, 7, 3)
@reg('mg_hide')     # 草叢＋眼睛
def _(i):
    i.C(4, 9, 4, 'g'); i.C(11, 9, 4, 'g'); i.C(7.5, 6.5, 4.6, 'g'); i.R(1, 9, 14, 14, 'g', cut=1); i.C(12.5, 3, 1.6, 'p'); i.P([(5, 8), (9, 8)], 'k')
@reg('mg_firefly')
def _(i):
    i.E(4, 4, 3, 2.4, 'c'); i.E(11, 4, 3, 2.4, 'c'); i.C(7.5, 9, 4, 'g'); i.C(7.5, 13, 2, 'y'); i.face(7, 9, 3, 'dot', blush=False)

ORDER = list(ICONS)

# ------------------------------------------------------------------ 9×9 mini（HUD 細 icon，逐粒點）
MINI = {
    'feed': ["....c....", "...ccc...", "..ccccc..", "..ckckc..", ".ccccccc.", ".cmmmmmc.", "ccmmmmmcc", "ccmmmmmcc", "........."],
    'heart': [".rr...rr.", "rrrr.rrrr", "rhrrrrrrr", "rrkrrrkrr", "rrrrrrrrr", ".rrrrrrr.", "..rrrrr..", "...rrr...", "....r...."],
    'clean': ["....b....", "...bb....", "...bbb...", "..bhbbb..", "..bbbbb..", ".bkbbkbb.", ".bbbbbbb.", "..bbbbb..", "...bbb..."],
    'sleep': ["..yyy....", ".yyy.....", "yyy......", "yyy...kkk", "yyy....k.", "yyyy..kkk", ".yyyyyy..", "..yyyyy..", "........."],
    'light': ["....t....", "....t....", "...ttt...", "tttthtttt", ".ttttttt.", "...ttt...", "...t.t...", "....t....", "........."],
    'star': ["....e....", "...eee...", "eeeeeeeee", ".eekeke..", "..eeeee..", "..eeeee..", ".ee...ee.", ".e.....e.", "........."],
    'plus': ["...ttt...", "...ttt...", "ttttttttt", "ttttttttt", "ttttttttt", "...ttt...", "...ttt...", ".........", "........."],
    'lock': ["..sssss..", ".ss...ss.", ".s.....s.", "yyyyyyyyy", "yyyykyyyy", "yyyykyyyy", "yyyyyyyyy", ".yyyyyyy.", "........."],
    'check': ["........g", ".......gg", "g.....gg.", "gg...gg..", ".gg.gg...", "..ggg....", "...g.....", ".........", "........."],
    'gift': ["..y...y..", "...yyy...", "rrrryrrrr", "pppypyppp", "rrrryrrrr", "rrrryrrrr", "rrrryrrrr", ".........", "........."],
    'mail': ["ccccccccc", "cSccccScc", "ccSccScc.", "cccSScccc", "ccccrcccc", "ccccccccc", ".........", ".........", "........."],
    'sprout': ["..gg.....", ".gggg.gg.", ".gggggggg", "..gg.ggg.", "....g....", "....g....", "..ooooo..", "..ooooo..", "...ooo..."],
    'reset': ["...ttt...", ".tt...tt.", "t.....ttt", "t......t.", "t........", "t.......t", ".tt...tt.", "...ttt...", "........."],
    'back': ["...t.....", "..tt.....", ".ttttttt.", "tttttttt.", ".ttttttt.", "..tt.....", "...t.....", ".........", "........."],
    'house': ["....o....", "...ooo...", "..ooooo..", ".ooooooo.", "ooooooooo", ".ccccccc.", ".ckccnnc.", ".ccccnnc.", "........."],
}
def render_mini(rows):
    a = np.zeros((11, 11, 4), np.uint8); m = np.full((11, 11), '.', dtype='<U1')
    for y, r in enumerate(rows):
        for x, ch in enumerate(r): m[y + 1, x + 1] = ch
    ic = Ic.__new__(Ic); ic.m = np.full((N, N), '.', dtype='<U1'); ic.m[:11, :11] = m
    im = render(ic); return im.crop((0, 0, 11, 11))

def build(name):
    i = Ic(); ICONS[name](i); return render(i)

if __name__ == '__main__':
    import sys
    S = 6; cols = 10; names = ORDER
    sheet = Image.new('RGBA', (cols * (N + 4) * S, ((len(names) + cols - 1) // cols) * (N + 4) * S), (40, 44, 80, 255))
    for k, n in enumerate(names):
        im = build(n).resize((N * S, N * S), Image.NEAREST); sheet.alpha_composite(im, ((k % cols) * (N + 4) * S + 2 * S, (k // cols) * (N + 4) * S + 2 * S))
    sheet.save(sys.argv[1] if len(sys.argv) > 1 else '/tmp/pv/icons_v2.png'); print(len(names))
