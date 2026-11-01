# 《微光小圃》HD-2D UI kit — 新增 icon（手帳／系統／小遊戲／4b 屋仔／5a 家族），純 Pillow 程序繪製，無 AI。
# 沿用 B2 小動物 icon 語言：粗描邊、漸變、高光、有表情。import 之後 k.icon 會識得新 kind。
import math
from PIL import Image, ImageDraw, ImageChops
import ui_hd2d_kit as K
v2, k = K.v2, K.k
P, hx = k.P, k.hx
E, POLY, RR, HEART = v2.E, v2.POLY, v2.RR, v2.HEART

def col(a, b): return (hx(a), hx(b))
PINK = col('#FFB9CF', '#FF7FA6'); GOLD = col('#FFF2A6', '#FFC34A'); MINT = col('#C9F7DA', '#5CC48A')
SKY = col('#D4F2FF', '#6CC2EE'); LILAC = col('#E4D6FF', '#A88BF4'); PEACH = col('#FFE0C4', '#FF9F6A')
CREAM = col('#FFFBF0', '#F1E2C6'); WOOD = col('#F4CFA2', '#C98A55'); GREEN = col('#D2F5A8', '#6FC65E')
CORAL = col('#FFB8A6', '#F0705A'); GREY = col('#E8EAF4', '#AEB3CC')

def _line(ic, pts, colr, w):
    ImageDraw.Draw(ic.img).line([(ic.c(x), ic.c(y)) for x, y in pts], fill=colr, width=P(w), joint='curve')

def ring(b, t):
    def fn(d, q):
        d.ellipse([q(b[0]), q(b[1]), q(b[2]), q(b[3])], fill=255)
        d.ellipse([q(b[0] + t), q(b[1] + t), q(b[2] - t), q(b[3] - t)], fill=0)
    return fn

EXTRA = {}
def reg(name):
    def deco(fn): EXTRA[name] = fn; return fn
    return deco

@reg('dex')
def _(ic):
    ic.part(POLY([(13.2, 15.6), (15.6, 13.2), (22.8, 20.4), (20.4, 22.8)]), PINK, gloss=False, round_=0.4)
    ic.part(E((1.5, 1.5, 17.5, 17.5)), GOLD, gloss=False)
    ic.part(E((3.6, 3.6, 15.4, 15.4)), SKY, outline=False)
    ic.face(9.5, 9.6, 0.62)
@reg('diary')
def _(ic):
    ic.part(RR((1.0, 6.5, 23.0, 22.5), 2.5), LILAC, gloss=False)
    ic.part(POLY([(2.2, 5.0), (12, 7.2), (12, 20.5), (2.2, 19.0)]), CREAM, gloss=False)
    ic.part(POLY([(12, 7.2), (21.8, 5.0), (21.8, 19.0), (12, 20.5)]), CREAM, gloss=False)
    ic.part(POLY([(17.2, 4.0), (20.2, 3.6), (20.2, 11.5), (18.7, 10.0), (17.2, 11.8)]), PINK, gloss=False, outline=False)
    ic.face(7.2, 12.4, 0.55)
    ic.part(HEART(5.0, 3.6, 0.28), PINK, gloss=False, outline=False)
@reg('bond')
def _(ic):
    ic.part(HEART(-3.6, 1.6, 0.66), col('#FFD0DE', '#FF9AB8'))
    ic.part(HEART(3.8, -1.2, 0.66), PINK)
    ic.face(15.8, 11.0, 0.5, 'happy')
    ic.face(8.2, 13.8, 0.5)
@reg('surprise')
def _(ic):
    ic.part(POLY([(12, 0.5), (13.6, 5.2), (18.5, 5.6), (14.6, 8.6), (16.0, 13.2), (12, 10.4), (8.0, 13.2), (9.4, 8.6), (5.5, 5.6), (10.4, 5.2)]), GOLD, gloss=False, round_=0.3)
    ic.part(RR((3.0, 11.0, 21.0, 22.8), 3.0), PINK)
    ic.part(RR((10.3, 11.0, 13.7, 22.8), 0.6), GOLD, gloss=False, outline=False)
    ic.face(12, 16.6, 0.6, 'open')
@reg('minigame')
def _(ic):
    ic.part(RR((1.5, 6.0, 22.5, 19.5), 6.5), MINT)
    ic.part(RR((4.3, 11.5, 9.7, 13.5), 0.6), CREAM, gloss=False, outline=False)
    ic.part(RR((6.0, 9.8, 8.0, 15.2), 0.6), CREAM, gloss=False, outline=False)
    ic.part(E((16.0, 8.6, 18.6, 11.2)), PINK, gloss=False, outline=False)
    ic.part(E((18.0, 12.2, 20.6, 14.8)), GOLD, gloss=False, outline=False)
    ic.face(12.6, 13.2, 0.45)
@reg('cabinet')
def _(ic):
    ic.part(RR((3.0, 1.5, 21.0, 22.8), 2.5), WOOD, gloss=False)
    ic.part(RR((5.2, 3.8, 18.8, 11.4), 1.0), col('#3C4680', '#232A55'), gloss=False, outline=False)
    ic.part(RR((5.2, 13.6, 18.8, 20.6), 1.0), col('#3C4680', '#232A55'), gloss=False, outline=False)
    ic.part(POLY(k.star_pts(12, 7.8, 3.4, 1.6)), GOLD, gloss=False, outline=False)
    ic.part(E((7.0, 15.4, 11.0, 19.6)), PINK, gloss=False, outline=False)
    ic.part(E((13.0, 15.0, 17.2, 19.6)), SKY, gloss=False, outline=False)
@reg('badge')
def _(ic):
    ic.part(POLY([(6.5, 0.5), (11.0, 0.5), (13.0, 9.0), (9.0, 10.5)]), SKY, gloss=False)
    ic.part(POLY([(13.0, 0.5), (17.5, 0.5), (15.0, 10.5), (11.0, 9.0)]), PINK, gloss=False)
    ic.part(E((4.0, 7.5, 20.0, 23.5)), GOLD)
    ic.face(12, 15.6, 0.62, 'happy')
@reg('mail')
def _(ic):
    ic.part(RR((1.5, 5.0, 22.5, 20.5), 2.6), CREAM)
    ic.part(POLY([(2.4, 6.0), (21.6, 6.0), (12, 13.6)]), col('#FFD4E2', '#FFA9C4'), gloss=False)
    ic.part(HEART(0, 0.4, 0.3), PINK, gloss=False)
    ic.face(12, 16.0, 0.55)
@reg('info')
def _(ic):
    ic.part(E((2.0, 2.0, 22.0, 22.0)), SKY)
    ic.part(E((10.6, 5.0, 13.4, 7.8)), CREAM, gloss=False, outline=False)
    ic.part(RR((10.7, 9.6, 13.3, 18.8), 1.2), CREAM, gloss=False, outline=False)
@reg('lock')
def _(ic):
    ic.part(ring((6.0, 1.2, 18.0, 16.0), 2.6), GREY, gloss=False)
    ic.part(RR((3.5, 9.5, 20.5, 22.8), 3.2), GOLD)
    ic.face(12, 15.0, 0.6, 'sleep')
@reg('check')
def _(ic):
    ic.part(E((1.5, 1.5, 22.5, 22.5)), MINT)
    _line(ic, [(6.6, 12.4), (10.4, 16.2), (17.6, 7.8)], hx('#3A2840'), 3.4)
    _line(ic, [(6.6, 12.4), (10.4, 16.2), (17.6, 7.8)], hx('#FFFFFF'), 2.0)
@reg('sound')
def _(ic):
    ic.part(POLY([(2.5, 8.6), (7.5, 8.6), (13.5, 3.2), (13.5, 20.8), (7.5, 15.4), (2.5, 15.4)]), LILAC, round_=0.4)
    for r in (3.6, 7.0):
        ImageDraw.Draw(ic.img).arc([ic.c(13 - r), ic.c(12 - r), ic.c(13 + r), ic.c(12 + r)], -50, 50, fill=hx('#3A2840'), width=P(2.0))
        ImageDraw.Draw(ic.img).arc([ic.c(13 - r), ic.c(12 - r), ic.c(13 + r), ic.c(12 + r)], -46, 46, fill=hx('#FFFFFF'), width=P(1.0))
@reg('quality')
def _(ic):
    ic.part(POLY([(6.0, 3.0), (18.0, 3.0), (22.5, 9.0), (12, 22.5), (1.5, 9.0)]), SKY)
    _line(ic, [(1.8, 9.0), (22.2, 9.0)], hx('#FFFFFF', 160), 0.6)
    ic.face(12, 12.6, 0.58)
@reg('water')
def _(ic):
    ic.part(ring((14.5, 8.5, 22.5, 17.5), 2.2), CREAM, gloss=False)
    ic.part(RR((3.0, 4.5, 18.0, 22.5), 3.5), CREAM)
    ic.part(RR((4.6, 10.0, 16.4, 20.8), 2.6), SKY, gloss=False, outline=False)
    ic.face(10.5, 14.4, 0.55)
@reg('bedtime')
def _(ic):
    for b in ((2.0, 1.5, 8.5, 7.5), (15.5, 1.5, 22.0, 7.5)): ic.part(E(b), GOLD, gloss=False)
    ic.part(E((2.5, 3.5, 21.5, 22.5)), PEACH)
    ic.part(E((5.5, 6.5, 18.5, 19.5)), CREAM, gloss=False, outline=False)
    _line(ic, [(12, 8.6), (12, 13.0), (15.2, 15.0)], hx('#3A2840'), 1.2)
    ic.part(E((11.0, 12.0, 13.0, 14.0)), PINK, gloss=False, outline=False)
@reg('reset')
def _(ic):
    def arc(d, q):
        d.ellipse([q(2.5), q(2.5), q(21.5), q(21.5)], fill=255); d.ellipse([q(6.6), q(6.6), q(17.4), q(17.4)], fill=0)
        d.polygon([(q(12), q(12)), (q(24), q(1)), (q(24), q(8))], fill=0)
    ic.part(arc, PEACH, gloss=False)
    ic.part(POLY([(16.0, 0.8), (23.4, 6.4), (15.0, 9.6)]), PEACH, gloss=False)
@reg('hint')
def _(ic):
    ic.part(RR((8.0, 16.0, 16.0, 22.8), 1.6), GREY, gloss=False)
    ic.part(E((3.5, 1.0, 20.5, 18.0)), GOLD)
    ic.face(12, 9.6, 0.62, 'happy')
# --- mini-games (P1-4 unique icons) ---
@reg('mg_tease')
def _(ic):
    ic.part(POLY([(3.0, 21.5), (6.5, 12.0), (12.5, 5.0), (21.5, 1.8), (18.8, 10.5), (12.5, 17.0)]), PINK, round_=1.4)
    _line(ic, [(3.4, 21.0), (17.6, 5.4)], hx('#C64F7A'), 0.8)
    ic.face(11.2, 12.6, 0.5, 'happy')
@reg('mg_stardust')
def _(ic):
    for i, (x, y, r) in enumerate([(3.8, 20.0, 1.3), (6.6, 17.0, 1.7), (9.6, 13.8, 2.0)]):
        ic.part(E((x - r, y - r, x + r, y + r)), col('#FFFFFF', '#BDF0E2'), gloss=False, outline=False)
    ic.part(POLY(k.star_pts(15.2, 9.0, 8.6, 4.2)), GOLD, round_=0.7)
    ic.face(15.2, 9.8, 0.5)
@reg('mg_leaf')
def _(ic):
    ic.part(POLY([(3.0, 15.0), (7.0, 7.0), (14.0, 3.0), (21.5, 3.5), (19.0, 11.0), (12.0, 16.0)]), GREEN, round_=1.4)
    ImageDraw.Draw(ic.img).arc([ic.c(2), ic.c(15.5), ic.c(22), ic.c(26)], 200, 340, fill=hx('#FFFFFF', 220), width=P(1.0))
    ic.face(12.0, 9.6, 0.5, 'happy')
@reg('mg_hide')
def _(ic):
    def bush(d, q):
        for b in ((1.0, 9.0, 11.0, 19.0), (6.5, 4.0, 17.5, 15.0), (13.0, 8.0, 23.0, 18.0), (3.0, 12.0, 21.0, 22.5)):
            d.ellipse([q(b[0]), q(b[1]), q(b[2]), q(b[3])], fill=255)
    ic.part(bush, GREEN, round_=0.5)
    for x in (9.6, 14.4):
        ic.part(E((x - 1.6, 10.2, x + 1.6, 14.2)), CREAM, gloss=False, outline=False)
        ic.part(E((x - 0.8, 11.4, x + 0.8, 13.6)), col('#3B2A40', '#3B2A40'), gloss=False, outline=False)
    ic.part(E((18.0, 3.0, 22.0, 7.0)), PINK, gloss=False)
@reg('mg_firefly')
def _(ic):
    ic.part(E((2.0, 3.0, 11.5, 11.5)), col('#FFFFFF', '#D8F4FF'), gloss=False)
    ic.part(E((12.5, 3.0, 22.0, 11.5)), col('#FFFFFF', '#D8F4FF'), gloss=False)
    ic.part(E((8.5, 13.5, 15.5, 22.8)), col('#FFFBB0', '#FFD94A'), gloss=False)
    ic.part(E((6.0, 5.5, 18.0, 17.0)), col('#B8F0C8', '#4FB57A'))
    ic.face(12, 11.0, 0.55)
@reg('ev_treasure')
def _(ic):
    ic.part(RR((2.5, 10.5, 21.5, 22.5), 2.2), WOOD)
    ic.part(RR((2.5, 4.0, 21.5, 11.5), 4.0), col('#E8B07A', '#B5733E'))
    ic.part(RR((10.0, 4.0, 14.0, 22.5), 0.6), GOLD, gloss=False, outline=False)
    ic.part(E((9.6, 9.0, 14.4, 13.8)), PINK, gloss=False)
    ic.face(12, 17.0, 0.55)
@reg('seed')
def _(ic):
    ic.part(POLY([(12, 1.5), (18.0, 11.0), (19.0, 16.5), (12, 22.5), (5.0, 16.5), (6.0, 11.0)]), WOOD, round_=1.2)
    ic.part(POLY([(12, 4.5), (16.5, 1.5), (14.6, 7.0)]), GREEN, gloss=False)
    ic.face(12, 14.6, 0.6)
# --- 4b 屋仔 stub icons ---
@reg('house')
def _(ic):
    ic.part(RR((16.0, 2.0, 19.6, 9.0), 0.6), CORAL, gloss=False)
    ic.part(RR((3.5, 9.5, 20.5, 22.8), 1.6), CREAM)
    ic.part(POLY([(0.6, 11.6), (12, 1.4), (23.4, 11.6)]), CORAL, round_=0.6)
    ic.part(RR((14.6, 17.0, 18.4, 22.8), 1.4), WOOD, gloss=False, outline=False)
    ic.face(9.6, 15.0, 0.58)
@reg('decorate')
def _(ic):
    def pal(d, q):
        d.ellipse([q(1.5), q(3.5), q(22.5), q(21.5)], fill=255); d.ellipse([q(14.5), q(13.5), q(20.0), q(19.0)], fill=0)
    ic.part(pal, WOOD)
    for (x, y), c in zip([(6.0, 9.0), (10.6, 6.2), (15.6, 6.8)], (PINK, SKY, GOLD)):
        ic.part(E((x - 1.9, y - 1.9, x + 1.9, y + 1.9)), c, gloss=False, outline=False)
    ic.face(9.0, 15.0, 0.55)
@reg('furniture')
def _(ic):
    ic.part(RR((4.0, 2.5, 20.0, 15.0), 4.0), PINK)
    for b in ((1.0, 10.0, 6.0, 20.5), (18.0, 10.0, 23.0, 20.5)): ic.part(RR(b, 2.4), col('#FFC4D8', '#E87A9E'), gloss=False)
    ic.part(RR((4.5, 13.5, 19.5, 20.0), 2.6), col('#FFD8E4', '#FFA9C4'), gloss=False)
    ic.part(RR((5.0, 19.5, 7.5, 23.0), 0.6), WOOD, gloss=False); ic.part(RR((16.5, 19.5, 19.0, 23.0), 0.6), WOOD, gloss=False)
    ic.face(12, 8.4, 0.6)
@reg('rotate')
def _(ic):
    def arc(d, q):
        d.ellipse([q(2.5), q(2.5), q(21.5), q(21.5)], fill=255); d.ellipse([q(6.8), q(6.8), q(17.2), q(17.2)], fill=0)
        d.rectangle([q(0), q(12), q(12), q(24)], fill=0)
    ic.part(arc, SKY, gloss=False)
    ic.part(POLY([(0.6, 11.0), (8.8, 11.0), (4.7, 17.0)]), SKY, gloss=False)
@reg('flip')
def _(ic):
    ic.part(POLY([(10.4, 3.0), (10.4, 21.0), (1.5, 21.0)]), SKY, gloss=False)
    ic.part(POLY([(13.6, 3.0), (13.6, 21.0), (22.5, 21.0)]), PINK, gloss=False)
    _line(ic, [(12, 1.0), (12, 23.0)], hx('#FFFFFF', 200), 0.6)
@reg('store')
def _(ic):
    ic.part(RR((3.0, 9.5, 21.0, 22.5), 2.0), WOOD)
    ic.part(RR((1.5, 5.5, 22.5, 11.0), 1.6), col('#E8B07A', '#B5733E'), gloss=False)
    ic.part(POLY([(12, 11.5), (16.0, 15.5), (13.4, 15.5), (13.4, 19.5), (10.6, 19.5), (10.6, 15.5), (8.0, 15.5)]), CREAM, gloss=False, outline=False)
# --- 5a 家族 stub icons ---
@reg('family_tree')
def _(ic):
    ic.part(RR((10.2, 13.0, 13.8, 23.0), 1.0), WOOD, gloss=False)
    def crown(d, q):
        for b in ((1.0, 5.0, 11.5, 15.5), (6.5, 0.5, 17.5, 11.5), (12.5, 5.0, 23.0, 15.5), (4.0, 8.5, 20.0, 18.0)):
            d.ellipse([q(b[0]), q(b[1]), q(b[2]), q(b[3])], fill=255)
    ic.part(crown, GREEN, round_=0.4)
    for (x, y), c in zip([(5.6, 9.6), (18.4, 9.6), (12.0, 4.6)], (PINK, GOLD, SKY)):
        ic.part(E((x - 1.9, y - 1.9, x + 1.9, y + 1.9)), c, gloss=False)
    ic.face(12, 11.6, 0.5, 'happy')
@reg('family_level')
def _(ic):
    ic.part(POLY([(3.0, 6.5), (6.8, 3.0), (12, 6.0), (17.2, 3.0), (21.0, 6.5), (21.0, 13.0), (12, 23.0), (3.0, 13.0)]), LILAC, round_=0.5)
    ic.part(POLY([(6.0, 1.2), (8.6, 4.4), (12, 0.4), (15.4, 4.4), (18.0, 1.2), (17.4, 6.6), (6.6, 6.6)]), GOLD, gloss=False)
    ic.face(12, 12.6, 0.6, 'happy')

_prev = k.icon
def icon3(th, kind):
    if kind not in EXTRA: return _prev(th, kind)
    ic = k.Icon(th); EXTRA[kind](ic); return ic.finish()
k.icon = icon3
k.ICON_CACHE.clear()
