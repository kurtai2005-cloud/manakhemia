# 《微光小圃》UI 繪本貼紙・甜甜版（B2）— 基於 build_ui_style_ref.py，純 Pillow/numpy，無 AI。
import importlib.util, inspect, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

_spec = importlib.util.spec_from_file_location('uiv1', os.path.join(os.path.dirname(__file__), 'build_ui_style_ref.py'))
k = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(k)
P, hx, mix, put, solid, grad, chunky0 = k.P, k.hx, k.mix, k.put, k.solid, k.grad, k.chunky
ROOT = k.ROOT
OUT = f'{ROOT}/ui/style_ref/v2'

B2 = dict(k.B)
B2.update(name='繪本貼紙・甜甜版', en='Storybook Candy',
    sub='更圓更厚貼紙邊・糖果粉彩・icon 有小動物耳仔・塗鴉星星心心葉仔',
    ol=hx('#6B5683'), ow=1.1, wob=0.45, sticker=3.0, round_boost=True,
    panel=(hx('#FFFEFA'), hx('#FFF4EC')), inset=(hx('#FFF0F6'), hx('#FCE4EF')),
    pri=(hx('#FFC4D8'), hx('#FF92B6')), sec=(hx('#C8EEFF'), hx('#92D2FA')),
    dis=(hx('#F2EEF4'), hx('#DDD6E3')), accent=(hx('#FFF6B8'), hx('#FFDF7A')),
    title=(hx('#E6D6FF'), hx('#C3A7FB')), dock=(hx('#FFFEFA'), hx('#FFEFF6')),
    text=hx('#5A4570'), shadow=hx('#6B5683', 60), sh_dy=2.0, sh_blur=1.4,
    track=hx('#F4EAF6'), red=hx('#FF6F8E'), bg=(hx('#FFF0F7'), hx('#ECF5FF')), font_num='fred',
    acts_tilt=[-4, 3, -3, 4],
    swatch=['#FFFEFA', '#FF9EBE', '#9AD6FA', '#BDF0D6', '#FFE58A', '#CDB4FB', '#6B5683'])

# ---- rounder chunky ----
def chunky(th, w, h, r, fill, *a, **kw):
    if th.get('round_boost'):
        if min(w, h) <= 60: r = min(max(r * 1.3, min(w, h) * 0.4), min(w, h) / 2)
        else: r = min(r * 1.3, 24)
    return chunky0(th, w, h, r, fill, *a, **kw)
k.chunky = chunky

# ---- cuter face ----
def face2(self, cx, cy, s=1.0, mood='smile'):
    d = ImageDraw.Draw(self.img); c = self.c
    ink = hx('#3B2A40'); ex = 2.75 * s
    for sx in (-1, 1):
        x = cx + sx * ex
        if mood == 'sleep':
            d.arc([c(x - 1.4 * s), c(cy - 1.0 * s), c(x + 1.4 * s), c(cy + 1.3 * s)], 200, 340, fill=ink, width=P(0.6 * s))
        elif mood == 'happy':
            d.arc([c(x - 1.3 * s), c(cy - 0.6 * s), c(x + 1.3 * s), c(cy + 1.8 * s)], 200, 340, fill=ink, width=P(0.65 * s))
        else:
            d.ellipse([c(x - 1.15 * s), c(cy - 1.45 * s), c(x + 1.15 * s), c(cy + 1.45 * s)], fill=ink)
            d.ellipse([c(x - 0.7 * s), c(cy - 1.15 * s), c(x - 0.05 * s), c(cy - 0.45 * s)], fill=(255, 255, 255, 255))
            d.ellipse([c(x + 0.25 * s), c(cy + 0.35 * s), c(x + 0.65 * s), c(cy + 0.75 * s)], fill=(255, 255, 255, 230))
        d.ellipse([c(x + sx * 1.7 * s - 1.4 * s), c(cy + 1.5 * s), c(x + sx * 1.7 * s + 1.4 * s), c(cy + 2.6 * s)], fill=hx('#FF7FA6', 165))
    if mood in ('smile', 'sleep', 'happy'):   # 'w' cat mouth
        for sx in (-1, 1):
            d.arc([c(cx + (sx - 1) * 0.55 * s), c(cy + 0.5 * s), c(cx + (sx + 1) * 0.55 * s), c(cy + 1.7 * s)], 20, 160, fill=ink, width=P(0.45 * s))
    elif mood == 'open':
        d.ellipse([c(cx - 0.85 * s), c(cy + 0.6 * s), c(cx + 0.85 * s), c(cy + 2.2 * s)], fill=hx('#B33B60'))
k.Icon.face = face2

_icon0 = k.icon
def E(b): return lambda d, q: d.ellipse([q(b[0]), q(b[1]), q(b[2]), q(b[3])], fill=255)
def POLY(pts): return lambda d, q: d.polygon([(q(x), q(y)) for x, y in pts], fill=255)
def RR(b, r): return lambda d, q: d.rounded_rectangle([q(b[0]), q(b[1]), q(b[2]), q(b[3])], radius=q(r) - q(0), fill=255)
def HEART(ox=0, oy=0, s=1.0):
    T = lambda x, y: (12 + (x - 12) * s + ox, 12 + (y - 12) * s + oy)
    def fn(d, q):
        for b in [(1.8, 3.0, 12.6, 13.8), (11.4, 3.0, 22.2, 13.8)]:
            a0 = T(b[0], b[1]); a1 = T(b[2], b[3]); d.ellipse([q(a0[0]), q(a0[1]), q(a1[0]), q(a1[1])], fill=255)
        d.polygon([(q(x), q(y)) for x, y in [T(2.2, 10.2), T(21.8, 10.2), T(12, 22.2)]], fill=255)
    return fn

def icon2(th, kind):
    if kind in ('feed', 'clean', 'sleep', 'light', 'star', 'gift', 'sprout', 'play', 'book', 'gear', 'heart'):
        return _icon0(th, kind)
    ic = k.Icon(th)
    pink = (hx('#FFB9CF'), hx('#FF7FA6'))
    if kind == 'heart_bunny':
        for x0 in (5.0, 13.0):
            ic.part(E((x0, -0.5, x0 + 5.5, 13)), (hx('#FFFFFF'), hx('#FFE8F0')), gloss=False)
            ic.part(E((x0 + 1.5, 1.5, x0 + 4.0, 10)), (hx('#FFC6D8'), hx('#FFA9C4')), gloss=False, outline=False)
        ic.part(HEART(0, 3.2, 0.78), pink, round_=0.5)
        ic.face(12, 13.6, 0.68)
    elif kind == 'play_cat':
        for pts in ([(3.5, 9), (5.2, 1.5), (11, 6)], [(20.5, 9), (18.8, 1.5), (13, 6)]):
            ic.part(POLY(pts), (hx('#FFE7A0'), hx('#FFC85E')), gloss=False, round_=0.4)
        m = ic.part(E((3, 4.5, 21, 22.5)), (hx('#FFE7A0'), hx('#FFC85E')), gloss=False)
        band = ic.mask(lambda d, q: d.polygon([(q(-2), q(16)), (q(26), q(10)), (q(26), q(14)), (q(-2), q(20))], fill=255))
        put(ic.img, grad(ic.img.size, hx('#FFC4D8'), hx('#FF92B6')), ImageChops.multiply(band, m))
        g = Image.new('L', ic.img.size, 0); ImageDraw.Draw(g).ellipse([ic.c(6.5), ic.c(6.5), ic.c(11), ic.c(9.5)], fill=210)
        put(ic.img, solid(ic.img.size, hx('#FFFFFF')), ImageChops.multiply(g, m))
        ic.face(12, 13.2, 0.8, 'smile')
    elif kind == 'book_bear':
        for b in ((1.5, 0.5, 8.5, 7.5), (15.5, 0.5, 22.5, 7.5)):
            ic.part(E(b), (hx('#F4CDA6'), hx('#E2A877')), gloss=False)
        ic.part(RR((3, 3.5, 21, 22.5), 4.0), (hx('#D8C6FF'), hx('#A88BF4')))
        ic.part(RR((16.6, 5.5, 20.0, 20.5), 1.0), (hx('#FFFBF0'), hx('#F1E8D6')), gloss=False)
        ic.part(E((5.5, 13.5, 14.5, 20)), (hx('#FFF3E4'), hx('#F7DEC6')), gloss=False, outline=False)
        ic.face(10, 13.0, 0.72)
    elif kind == 'gear_chick':
        def gear(d, q):
            for i in range(8):
                a = i * math.pi / 4; cx, cy = 12 + 8.4 * math.cos(a), 13 + 8.4 * math.sin(a)
                d.ellipse([q(cx - 2.9), q(cy - 2.9), q(cx + 2.9), q(cy + 2.9)], fill=255)
            d.ellipse([q(3.8), q(4.8), q(20.2), q(21.2)], fill=255)
        ic.part(E((10.5, -0.5, 13.5, 4)), (hx('#FFE27A'), hx('#FFC34A')), gloss=False)
        ic.part(gear, (hx('#FFF4B4'), hx('#FFD25E')), round_=0.4)
        ic.face(12, 12.4, 0.74)
        ic.part(POLY([(10.6, 15.2), (13.4, 15.2), (12, 17.2)]), (hx('#FFA65E'), hx('#FF8A3D')), gloss=False, outline=False)
    elif kind == 'd_star':
        ic.part(POLY(k.star_pts(12, 13, 11.5, 5.6)), (hx('#FFF2A6'), hx('#FFCF4A')), round_=1.0)
    elif kind == 'd_heart':
        ic.part(HEART(), pink, round_=0.6)
    elif kind == 'd_spark':
        ic.part(POLY([(12, 0.8), (14.6, 9.4), (23.2, 12), (14.6, 14.6), (12, 23.2), (9.4, 14.6), (0.8, 12), (9.4, 9.4)]), (hx('#FFFFFF'), hx('#BDF0E2')), round_=0.5)
    elif kind == 'd_leaf':
        ic.part(POLY([(3, 21), (6, 9), (14, 3), (21.5, 2.5), (20, 11), (13, 19)]), (hx('#C9F5AE'), hx('#7FD36E')), round_=1.6)
        ImageDraw.Draw(ic.img).line([(ic.c(4.5), ic.c(19.5)), (ic.c(18), ic.c(6))], fill=hx('#5AA65A'), width=P(0.7))
    elif kind == 'd_paw':
        ic.part(E((6, 10, 18, 21.5)), pink, gloss=False)
        for b in ((3, 6, 7.6, 11), (7.6, 2.2, 12, 7.5), (12, 2.2, 16.4, 7.5), (16.4, 6, 21, 11)):
            ic.part(E(b), pink, gloss=False)
    elif kind == 'd_cloud':
        def cl(d, q):
            for b in ((2, 10, 12, 20), (7, 5, 17, 15), (12, 9, 22, 19), (5, 12, 20, 20.5)): d.ellipse([q(b[0]), q(b[1]), q(b[2]), q(b[3])], fill=255)
        ic.part(cl, (hx('#FFFFFF'), hx('#EAF4FF')), gloss=False, round_=0.5)
        ic.face(12, 14, 0.6, 'happy')
    return ic.finish()
k.icon = icon2
k.ICON_CACHE.clear()
draw_icon, get_icon, text, place, red_dot = k.draw_icon, k.get_icon, k.text, k.place, k.red_dot

def doodle(board, kind, cx, cy, size, ang=0, th=B2):
    im = get_icon(th, kind, size)
    if ang: im = im.rotate(ang, resample=Image.BICUBIC, expand=True)
    board.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

# ---- cute header (ribbon with cat ears + bow) ----
def header(board, th, cx, y, w, label, ears=True):
    if ears:
        for sx in (-1, 1):
            ex = cx + sx * (w / 2 - 12)
            comp = chunky(th, 14, 14, 4, th['title'], seed=90 + sx, gloss=False)
            place(board, comp, P(ex - 7), P(y - 12), 45)
            dd = ImageDraw.Draw(board)
            dd.ellipse([P(ex - 2.3), P(y - 8), P(ex + 2.3), P(y - 2.5)], fill=hx('#FFC6DA'))
    place(board, chunky(th, w, 20, 10, th['title'], seed=2), P(cx - w / 2), P(y))
    text(board, (P(cx), P(y + 9.6)), label, 9.6, hx('#FFFFFF'), stroke=1.1, stroke_col=mix(th['title'][1], hx('#000000'), .38))
    # bow on the right shoulder
    bx, by = cx + w / 2 - 4, y + 2
    for sx in (-1, 1):
        place(board, chunky(th, 9, 7, 3.5, th['pri'], seed=95 + sx, gloss=False, sticker=1.2), P(bx + (sx - 1) * 4.5 + 0.0), P(by - 3.5), sx * 18)
    place(board, chunky(th, 4.5, 4.5, 2.2, th['pri'], seed=97, gloss=False, sticker=1.0), P(bx - 2.25), P(by - 2.25))

def close_btn(board, th, cx, cy, d=17):
    for sx in (-1, 1):   # tiny ears
        place(board, chunky(th, 6.5, 6.5, 3.2, (hx('#FFC4D3'), hx('#FF9AB4')), seed=80 + sx, gloss=False, sticker=1.4), P(cx + sx * 5.2 - 3.25), P(cy - d / 2 - 1.6))
    place(board, chunky(th, d, d, d / 2, (hx('#FFC4D3'), hx('#FF8FAD')), seed=8), P(cx - d / 2), P(cy - d / 2))
    dd = ImageDraw.Draw(board)
    for s in (1, -1):
        dd.line([(P(cx - 2.8), P(cy - 2.8 * s)), (P(cx + 2.8), P(cy + 2.8 * s))], fill=hx('#FFFFFF'), width=P(2.0))
        for (ex, ey) in [(cx - 2.8, cy - 2.8 * s), (cx + 2.8, cy + 2.8 * s)]:
            dd.ellipse([P(ex - 1.0), P(ey - 1.0), P(ex + 1.0), P(ey + 1.0)], fill=hx('#FFFFFF'))
    for sx in (-1, 1):
        dd.ellipse([P(cx + sx * 5.6 - 1.4), P(cy + 2.4), P(cx + sx * 5.6 + 1.4), P(cy + 4.0)], fill=hx('#FF6F96', 170))

POP_ROWS = [('play_cat', '陪佢玩 2 次', 0.5), ('feed', '餵佢食嘢', 1.0), ('clean', '幫佢沖涼', 0.0)]
def popup_frame(board, th, x, y, w=152, h=134, title='今日委託'):
    place(board, chunky(th, w, h, 18, th['panel'], seed=21, gloss=False), P(x), P(y))
    d = ImageDraw.Draw(board)
    pts = k.rr_points(P(x + 4.5), P(y + 4.5), P(x + w - 4.5), P(y + h - 4.5), P(15), 0)
    for i in range(0, len(pts) - 1, 3):
        d.line([pts[i], pts[i + 1]], fill=th['title'][1], width=P(0.7))
    header(board, th, x + w / 2, y - 9, 80, title)
    doodle(board, 'd_star', P(x + 14), P(y + h - 12), 8, 12)
    doodle(board, 'd_heart', P(x + w - 10), P(y + h - 30), 7, -10)
    close_btn(board, th, x + w - 14, y + 15)

def popup_row(board, th, x, y, i, w=152):
    kk, lab, v = POP_ROWS[i]
    ry = y + 24 + i * 26
    place(board, chunky(th, w - 18, 22, 11, th['inset'], seed=30 + i, gloss=False, shadow=False, ow=th['ow'] * .6, sticker=0), P(x + 9), P(ry))
    draw_icon(board, th, kk, P(x + 21), P(ry + 11), 18)
    text(board, (P(x + 32), P(ry + 7.5)), lab, 7.4, th['text'], anchor='lm')
    d = ImageDraw.Draw(board); tx0 = x + 32; tw = 54
    d.rounded_rectangle([P(tx0), P(ry + 13.5), P(tx0 + tw), P(ry + 17)], radius=P(1.75), fill=th['track'])
    if v > 0: d.rounded_rectangle([P(tx0), P(ry + 13.5), P(tx0 + tw * v), P(ry + 17)], radius=P(1.75), fill=th['pri'][1])
    draw_icon(board, th, 'star', P(x + w - 31), P(ry + 11), 14)
    text(board, (P(x + w - 18), P(ry + 11)), '+4', 8.6, th['text'], 'fred')

def popup_button(board, th, x, y, w=152, h=134):
    k.button(board, th, 0, 0, x + (w - 74) / 2, y + h - 31, 74, 22, 'pri', '全部領取')

def popup2(board, th, X, Y, x, y, w=150, h=132):
    # X,Y are SS offsets (0 in our use)
    popup_frame(board, th, x, y, w, h)
    for i in range(3): popup_row(board, th, x, y, i, w)
    popup_button(board, th, x, y, w, h)
k.popup = popup2

TABS = [('heart_bunny', '照顧'), ('play_cat', '玩'), ('sprout', '小圃'), ('book_bear', '手帳'), ('gear_chick', '設定')]
DOCK = dict(x=2, y=368, w=191, h=50)
def tab_cx(i): return DOCK['x'] + DOCK['w'] / 5 * (i + .5)
def dock_bar(board, th):
    place(board, chunky(th, DOCK['w'], DOCK['h'], 20, th['dock'], seed=11), P(DOCK['x']), P(DOCK['y']))
def tab_idle(board, th, i):
    kk, lab = TABS[i]; cx = tab_cx(i); y = DOCK['y']
    draw_icon(board, th, kk, P(cx), P(y + 18), 21)
    text(board, (P(cx), P(y + 37.5)), lab, 7.0, th['text'])
def tab_active(board, th, i):
    kk, lab = TABS[i]; cx = tab_cx(i); y = DOCK['y']; bw = 36
    place(board, chunky(th, bw, 41, 18, th['pri'], seed=5), P(cx - bw / 2), P(y - 7), -4)
    draw_icon(board, th, kk, P(cx), P(y + 6.5), 24)
    text(board, (P(cx), P(y + 26.5)), lab, 7.6, hx('#FFFFFF'), stroke=0.9, stroke_col=mix(th['pri'][1], hx('#000000'), .4))
def tab_dot(board, th, i, n=1):
    red_dot(board, th, P(tab_cx(i) + 10), P(DOCK['y'] + 8), n)
def dock2(board, th, X, Y, x, y, w=191, active=0, dot=2):
    # used by board()/home() with arbitrary x,y: translate via temporary DOCK
    old = dict(DOCK); DOCK.update(x=x + X / P(1), y=y + Y / P(1), w=w)
    dock_bar(board, th)
    for i in range(5):
        if i != active: tab_idle(board, th, i)
    tab_active(board, th, active)
    if dot is not None: tab_dot(board, th, dot)
    d = ImageDraw.Draw(board); cx = tab_cx(active)
    d.rounded_rectangle([P(cx - 5), P(DOCK['y'] + DOCK['h'] - 6.2), P(cx + 5), P(DOCK['y'] + DOCK['h'] - 4.4)], radius=P(1), fill=th['pri'][1])
    DOCK.clear(); DOCK.update(old)
k.dock = dock2

ACTS = [('feed', '餵食'), ('play_cat', '玩耍'), ('clean', '清潔'), ('sleep', '瞓覺')]
def act_fill(th, i): return [th['pri'], (hx('#CBF3DE'), hx('#93DCB3')), th['sec'], th['title']][i]
def act_btn(board, th, i, pressed=False, ang=None):
    x = 6 + i * 46.5; y = 314
    comp = chunky(th, 40, 38, 14, act_fill(th, i), seed=40 + i, pressed=pressed)
    place(board, comp, P(x), P(y), th['acts_tilt'][i] if ang is None else ang)
    draw_icon(board, th, ACTS[i][0], P(x + 20), P(y + 15), 23)
    text(board, (P(x + 20), P(y + 31.5)), ACTS[i][1], 7.2, hx('#FFFFFF'), stroke=1.0, stroke_col=mix(act_fill(th, i)[1], hx('#000000'), .4))

NEEDS = [('feed', .62, (hx('#FFE0A8'), hx('#FFB25E'))), ('heart_bunny', .48, (hx('#FFC4D8'), hx('#FF86AE'))),
         ('clean', .55, (hx('#C8EEFF'), hx('#78C6F5'))), ('sleep', .80, (hx('#FFF2AE'), hx('#FFCB52')))]
def need(board, th, i, v=None):
    kk, v0, c = NEEDS[i]
    k.need_pill(board, th, 0, 0, 3 + i * 47.3, 29.5, 44, kk, v0 if v is None else v, c)

def nameplate(board, th, pet_key, name):
    place(board, k.tag_shape(th, 96, 22, th['panel'], seed=1), P(2), P(4), -1.5)
    place(board, chunky(th, 19, 19, 9.5, th['accent'], seed=3), P(15), P(5.5))
    pet = k.load(f'{ROOT}/sprites/tuanrong/species_concept/from_ref/tuned_48/sprites/{pet_key}_48.png')
    bb = pet.getbbox(); head = pet.crop((bb[0], bb[1] + 4, bb[2], bb[1] + 4 + (bb[2] - bb[0]))).resize((P(15), P(15)), Image.NEAREST)
    board.alpha_composite(head, (P(17), P(7.5)))
    nx = 38
    text(board, (P(nx), P(11)), name, 9.5, th['text'], anchor='lm')
    text(board, (P(nx + 22), P(11.3)), '幼崽', 6.3, mix(th['text'], hx('#FFFFFF'), .35), anchor='lm')
    d = ImageDraw.Draw(board)
    d.rounded_rectangle([P(nx), P(17.6), P(95), P(20.6)], radius=P(1.5), fill=th['track'])
    d.rounded_rectangle([P(nx), P(17.6), P(nx + (95 - nx) * .62), P(20.6)], radius=P(1.5), fill=th['pri'][1])

def chip(board, th, which, val=None):
    if which == 0: k.currency_chip(board, th, 0, 0, 104, 5, 42, 'light', str(val or 140))
    else: k.currency_chip(board, th, 0, 0, 150, 5, 41, 'star', str(val or 10))

def quest_btn(board, th, dot=True):
    place(board, chunky(th, 24, 24, 12, th['panel'], seed=6), P(166), P(54))
    draw_icon(board, th, 'gift', P(178), P(65.5), 18)
    if dot: red_dot(board, th, P(187), P(56), 3)
    text(board, (P(178), P(83)), '委託', 6.4, hx('#FFFFFF'), stroke=0.9, stroke_col=th['text'])

def toast2(board, th, x=26, y=56, w=120, msg='收到小禮物 +5'):
    k.toast(board, th, 0, 0, x, y, w, msg)

def speech2(board, th, msg='肚仔餓…'):
    k.speech(board, th, 0, 0, 104, 222, 52, 17, msg, 'feed')

SKY_DOODLES = [('d_star', 22, 104, 9, 12), ('d_heart', 170, 112, 8, -12), ('d_spark', 132, 150, 7, 0), ('d_cloud', 58, 150, 12, 0)]
def scene_ss(H, pet_key, frame=0):
    return k.scene(H, pet_key, frame).resize((P(195), P(422)), Image.NEAREST)

PET_NAMES = {'A1': '滴滴', 'B2': '水母咪', 'C1': '火仔'}
def home2(th, H, pet_key, bubble='肚仔餓…', skip=(), frame=0, base=None):
    b = (base if base is not None else scene_ss(H, pet_key, frame)).copy()
    if 'doodles' not in skip:
        for kd, x, y, s, a in SKY_DOODLES: doodle(b, kd, P(x), P(y), s, a, th)
    if 'hud' not in skip:
        nameplate(b, th, pet_key, PET_NAMES.get(pet_key, '滴滴'))
        if 'chip0' not in skip: chip(b, th, 0)
        chip(b, th, 1)
        for i in range(4):
            if f'need{i}' not in skip: need(b, th, i)
    if 'quest' not in skip: quest_btn(b, th, dot='questdot' not in skip)
    if 'toast' not in skip: toast2(b, th)
    if 'speech' not in skip: speech2(b, th, bubble)
    for i in range(4):
        if f'act{i}' not in skip: act_btn(b, th, i)
    if 'dock' not in skip:
        dock_bar(b, th)
        act = 0
        for i in range(5):
            if f'tab{i}' in skip: continue
            if i == act: tab_active(b, th, i)
            else: tab_idle(b, th, i)
        if 'tabdot' not in skip: tab_dot(b, th, 2)
    return b
def home_wrap(th, H, pet_key, bubble):
    return home2(th, H, pet_key, bubble)
k.home = home_wrap

# ---- board: patch source of v1 board for new icon list + decoration ----
src = inspect.getsource(k.board)
src = src.replace("""kinds = [('feed', '餵食'), ('play', '玩耍'), ('clean', '清潔'), ('sleep', '瞓覺'), ('book', '手帳／圖鑑'), ('sprout', '小圃'),
             ('light', '光粒'), ('star', '星星碎'), ('heart', '心情'), ('gear', '設定'), ('gift', '禮物／委託')]""",
"""kinds = [('feed', '餵食'), ('play_cat', '玩（貓貓波）'), ('clean', '清潔'), ('sleep', '瞓覺'), ('book_bear', '手帳（熊熊）'), ('sprout', '小圃'),
             ('light', '光粒'), ('star', '星星碎'), ('heart_bunny', '照顧（兔兔）'), ('gear_chick', '設定（雞仔）'), ('gift', '禮物／委託'), ('d_cloud', '雲仔')]""")
src = src.replace("lab('icon（全部原創、有表情，唔再借 emoji）'", "lab('icon（全部原創、有表情；dock 5 個係小動物吉祥物）'")
src = src.replace("('Fredoka' if th['key'] == 'A' else 'Baloo 2')", "'Fredoka（圓波波）'")
src = src.replace("for i, c in enumerate(th['swatch']):\n        cx = X0 + 660 + i * 76", "for i, c in enumerate(th['swatch']):\n        cx = X0 + 640 + i * 68")
src = src.replace("lab('彈窗（關閉掣喺面板入面右上角）', X0, Y0 - 34)", "lab('彈窗', X0, Y0 - 34)")
src = src.replace("popup(bd, th, 0, 0, ax(2), ay(10), 152, 134)", "popup(bd, th, 0, 0, ax(2), ay(20), 152, 134)")
src = src.replace("T(c[1:], cx, cy + 34, 15,", "T(c[1:], cx, cy + 34, 12,")
src = src.replace("    out = bd.reduce(SS)", "    decorate(bd, th)\n    out = bd.reduce(SS)")
src = src.replace("def board(", "def board2(")
def decorate(bd, th):
    spots = [('d_star', 1120, 36, 14, 10), ('d_heart', 1190, 66, 11, -12), ('d_spark', 1690, 60, 12, 0), ('d_leaf', 1650, 120, 13, 20),
             ('d_paw', 1700, 640, 11, -15), ('d_heart', 1720, 1050, 10, 15), ('d_star', 1725, 1300, 12, -8), ('d_spark', 1500, 1480, 10, 0),
             ('d_leaf', 12, 1470, 12, -30), ('d_cloud', 1640, 1475, 18, 0)]
    for kd, x, y, s, a in spots: doodle(bd, kd, P(x / 3), P(y / 3), s, a, th)
k.decorate = decorate
exec(src, k.__dict__)
board2 = k.board2
