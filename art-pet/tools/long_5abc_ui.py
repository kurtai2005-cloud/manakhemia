# 《微光小圃》5a–5c HD-2D UI 共用（跟 ui/style_ref/hd2d；ui_hd2d_kit／ui_hd2d_icons 只讀，新 icon 喺記憶體登記，唔改佢哋個檔）
# 純 Pillow 程序繪製，冇 AI。座標：art 195×422；SS＝P(v)（6x）；成品 ÷2＝3x
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageChops
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ui_hd2d_kit as H
try:
    import ui_hd2d_icons as I          # 另一位同事嘅 kit icon（家族／屋仔等）；import 後 k.icon 識得
    EXTRA = I.EXTRA
except Exception:                      # 佢改緊檔都唔好塞住
    I = None; EXTRA = {}
    _p = H.k.icon
    def _icon3(th, kind):
        if kind not in EXTRA: return _p(th, kind)
        ic = H.k.Icon(th); EXTRA[kind](ic); return ic.finish()
    H.k.icon = _icon3
import long_5abc_lib as LB
from series2_lib import ART
k = H.k; P = H.P; hx = H.hx; C = H.C; put, solid, gauss, amul, mix = H.put, H.solid, H.gauss, H.amul, H.mix
E = lambda b: (lambda d, q: d.ellipse([q(b[0]), q(b[1]), q(b[2]), q(b[3])], fill=255))
POLY = lambda pts: (lambda d, q: d.polygon([(q(x), q(y)) for x, y in pts], fill=255))
RR = lambda b, r: (lambda d, q: d.rounded_rectangle([q(b[0]), q(b[1]), q(b[2]), q(b[3])], radius=q(r) - q(0), fill=255))
def col(a, b): return (hx(a), hx(b))
PINK = col('#FFB9CF', '#FF7FA6'); GOLD = col('#FFF2A6', '#FFC34A'); MINT = col('#C9F7DA', '#5CC48A'); SKY = col('#D4F2FF', '#6CC2EE')
LILAC = col('#E4D6FF', '#A88BF4'); PEACH = col('#FFE0C4', '#FF9F6A'); CREAM = col('#FFFBF0', '#F1E2C6'); WOOD = col('#F4CFA2', '#C98A55')
GREEN = col('#D2F5A8', '#6FC65E'); CORAL = col('#FFB8A6', '#F0705A'); GREY = col('#E8EAF4', '#AEB3CC'); LEATHER = col('#E8B07A', '#A8663C')
NAVY = col('#9AB0F0', '#4A5CB0'); STRAW = col('#FFEBA8', '#E0B054'); WHITE = col('#FFFFFF', '#E4E0EE'); BROWN = col('#D9A57A', '#8A5634')
def star_pts(cx, cy, R_, r, n=5, rot=-90):
    return [(cx + (R_ if i % 2 == 0 else r) * math.cos(math.radians(rot + i * 180 / n)), cy + (R_ if i % 2 == 0 else r) * math.sin(math.radians(rot + i * 180 / n))) for i in range(2 * n)]
def line(ic, pts, c, w): ImageDraw.Draw(ic.img).line([(ic.c(x), ic.c(y)) for x, y in pts], fill=c, width=P(w), joint='curve')
def reg(name):
    def deco(fn):
        if name in EXTRA and name in KIT_HAS: return fn       # kit 有就用 kit 嘅
        EXTRA[name] = fn; return fn
    return deco
KIT_HAS = set(EXTRA)

# ───────── 5a icon ─────────
@reg('crown')
def _(ic):
    ic.part(POLY([(2, 8), (7, 13), (12, 4), (17, 13), (22, 8), (20, 20), (4, 20)]), GOLD, round_=0.4)
    for x, y, c in ((2, 8, PINK), (12, 4, SKY), (22, 8, PINK)): ic.part(E((x - 2, y - 2, x + 2, y + 2)), c, gloss=False)
    ic.part(RR((5, 15.5, 19, 18.5), 1), PEACH, gloss=False, outline=False)
@reg('egg_tr')
def _(ic):
    ic.part(E((4.5, 2, 19.5, 23)), CREAM)
    for x, y in ((8, 9), (15, 7), (12, 15), (16, 17)): ic.part(E((x - 1.6, y - 1.6, x + 1.6, y + 1.6)), PINK, gloss=False, outline=False)
    ic.face(12, 13.5, 0.55)
@reg('egg_kid')
def _(ic):
    ic.part(E((4.5, 2, 19.5, 23)), SKY)
    ic.part(POLY([(4.8, 12), (8, 9.5), (11, 12.5), (14, 9.5), (17, 12.5), (19.4, 10.5), (19.5, 14), (4.6, 14.5)]), CREAM, gloss=False, outline=False)
    ic.face(12, 17, 0.55)
@reg('arrow_l')
def _(ic): ic.part(POLY([(15.5, 3), (5, 12), (15.5, 21), (18, 18), (10.5, 12), (18, 6)]), GOLD, round_=0.5)
@reg('arrow_r')
def _(ic): ic.part(POLY([(8.5, 3), (19, 12), (8.5, 21), (6, 18), (13.5, 12), (6, 6)]), GOLD, round_=0.5)
@reg('pets')
def _(ic):
    ic.part(E((1, 8, 13, 20)), PINK); ic.part(E((11, 6, 23, 19)), SKY); ic.face(6.8, 14, 0.45); ic.face(17, 12.4, 0.45, 'happy')
@reg('xp')
def _(ic):
    ic.part(POLY(star_pts(12, 12.5, 11, 5)), GOLD, round_=0.5); ic.face(12, 13, 0.5, 'happy')
@reg('visitor')
def _(ic):
    ic.part(RR((3, 9, 21, 22), 2), WOOD); ic.part(POLY([(1, 10), (12, 2), (23, 10)]), CORAL, round_=0.6)
    ic.part(RR((9, 13, 15, 22), 3), BROWN, gloss=False); ic.part(E((13, 17, 14.4, 18.4)), GOLD, gloss=False, outline=False)
@reg('title')
def _(ic):
    ic.part(POLY([(6, 14), (3, 23), (8, 20.5), (10, 23.5), (11, 15)]), PINK, gloss=False)
    ic.part(POLY([(18, 14), (21, 23), (16, 20.5), (14, 23.5), (13, 15)]), PINK, gloss=False)
    ic.part(E((3.5, 1.5, 20.5, 18.5)), GOLD); ic.part(POLY(star_pts(12, 10.2, 5.5, 2.4)), CREAM, gloss=False, outline=False)

# ───────── 5b icon ─────────
@reg('expedition')
def _(ic):
    ic.part(RR((4, 5, 20, 23), 5), LEATHER)
    ic.part(RR((7, 3, 17, 8), 3), BROWN, gloss=False)
    ic.part(RR((3.5, 6, 20.5, 12.5), 4.5), LEATHER, gloss=False)
    ic.part(RR((10.5, 10.5, 13.5, 14), .8), GOLD, gloss=False)
    ic.part(RR((6.5, 15.5, 17.5, 21.5), 2), PEACH, gloss=False)
    ic.part(POLY([(18.5, 13), (23, 11), (22.5, 16.5)]), GREEN, gloss=False)
@reg('job_post')
def _(ic):
    ic.part(RR((2, 10, 22, 21), 1.6), CREAM, gloss=False); line(ic, [(2.5, 10.8), (12, 17), (21.5, 10.8)], hx('#C9A97A'), 1.1)
    ic.part(E((14.5, 1.5, 23, 10)), NAVY); ic.part(RR((13, 7, 23.8, 9.6), 1), NAVY, gloss=False)
    ic.part(HEART := (lambda d, q: d.polygon([(q(12), q(17.6)), (q(9.6), q(15.2)), (q(10.4), q(14)), (q(12), q(15)), (q(13.6), q(14)), (q(14.4), q(15.2))], fill=255)), PINK, gloss=False, outline=False)
@reg('job_garden')
def _(ic):
    ic.part(E((1, 11, 23, 19)), STRAW); ic.part(E((6, 5, 18, 15)), STRAW)
    ic.part(RR((6, 11, 18, 13.5), .8), CORAL, gloss=False, outline=False)
    line(ic, [(12, 6), (12, 2.6)], hx('#4E9A44'), 1.2); ic.part(E((12, .8, 17, 4.6)), GREEN, gloss=False); ic.part(E((7.6, 1.6, 12.2, 5.0)), GREEN, gloss=False)
@reg('job_watch')
def _(ic):
    ic.part(POLY([(2, 18), (9, 4), (16, 2), (21, 7), (20, 13), (18, 9), (14, 8), (21, 18)]), NAVY, round_=0.8)
    ic.part(RR((1.5, 16.5, 22, 21.5), 2.5), CREAM, gloss=False)
    ic.part(E((18, 10.5, 23.5, 16)), GOLD, gloss=False)
    ic.part(POLY(star_pts(9.5, 10, 2.6, 1.1)), GOLD, gloss=False, outline=False)
@reg('job_chef')
def _(ic):
    def puff(d, q):
        for b in ((2, 4, 11, 13), (7, 1, 17, 11), (13, 4, 22, 13), (4, 7, 20, 15)): d.ellipse([q(b[0]), q(b[1]), q(b[2]), q(b[3])], fill=255)
    ic.part(puff, WHITE, round_=0.4); ic.part(RR((5, 13, 19, 21.5), 1.4), WHITE)
    line(ic, [(9, 15), (9, 20)], hx('#D6D0E0'), .8); line(ic, [(15, 15), (15, 20)], hx('#D6D0E0'), .8)
@reg('rest')
def _(ic):
    ic.part(RR((1.5, 11, 22.5, 21.5), 4.5), LILAC)
    ic.part(E((5, 8, 19, 17)), PINK); ic.face(12, 12.6, 0.55, 'sleep')
    for x, y, s in ((17, 5.8, 2.6), (20.5, 2.2, 1.8)):
        line(ic, [(x - s, y - s), (x + s, y - s), (x - s, y + s), (x + s, y + s)], hx('#7A5CD6'), .9)
@reg('shards')
def _(ic):
    ic.part(POLY([(12, 1), (19, 9), (12, 23), (5, 9)]), SKY, round_=0.3)
    ic.part(POLY([(5.5, 9), (18.5, 9), (12, 22)]), col('#B6E4FF', '#4C9EE0'), gloss=False, outline=False)
    ic.part(POLY(star_pts(18.5, 5, 3, 1.2)), GOLD, gloss=False, outline=False)
@reg('job_lv')
def _(ic):
    ic.part(POLY([(12, 1), (21.5, 6), (21.5, 17), (12, 23), (2.5, 17), (2.5, 6)]), GOLD, round_=0.5)
    ic.part(POLY([(12, 6), (16, 12.5), (12, 18), (8, 12.5)]), PINK, gloss=False)

# 手信 10 件
SOUV = [("sv_shell", "七彩貝殼"), ("sv_pinecone", "松果"), ("sv_starstone", "星星石"), ("sv_feather", "藍羽毛"), ("sv_mushroom", "細蘑菇"),
        ("sv_maple", "紅楓葉"), ("sv_bottle", "樽中信"), ("sv_cloud", "雲朵糖"), ("sv_lantern", "螢火燈"), ("sv_rainbow", "彩虹糖")]
@reg('sv_shell')
def _(ic):
    ic.part(POLY([(12, 21), (2, 10), (5, 4), (12, 2), (19, 4), (22, 10)]), PINK, round_=0.9)
    for a in (-50, -25, 0, 25, 50):
        x = 12 + 9 * math.sin(math.radians(a)); y = 21 - 16 * math.cos(math.radians(a)); line(ic, [(12, 20), (x, y)], hx('#E36A92'), .7)
    ic.part(RR((9, 18.5, 15, 22.5), 1.5), PINK, gloss=False)
@reg('sv_pinecone')
def _(ic):
    ic.part(E((5, 5, 19, 23)), BROWN)
    for y in (9, 13, 17):
        for x in (8.5, 12, 15.5): ic.part(POLY([(x - 1.8, y), (x, y + 2.4), (x + 1.8, y)]), WOOD, gloss=False, outline=False)
    ic.part(E((8, .8, 13, 6)), GREEN, gloss=False); ic.part(E((11.5, 1.6, 16.5, 6.4)), GREEN, gloss=False)
@reg('sv_starstone')
def _(ic):
    ic.part(E((2, 6, 22, 22)), GREY); ic.part(POLY(star_pts(12, 14, 6, 2.6)), GOLD, gloss=False)
    ic.part(POLY(star_pts(19, 4, 2.8, 1.1)), GOLD, gloss=False, outline=False)
@reg('sv_feather')
def _(ic):
    ic.part(POLY([(5, 21), (8, 12), (14, 4), (20, 1.5), (19, 8), (14, 15), (7, 20)]), SKY, round_=0.9)
    line(ic, [(3.5, 22.5), (9, 15), (18.5, 3)], hx('#3A6FB0'), .8)
@reg('sv_mushroom')
def _(ic):
    ic.part(RR((9, 12, 15, 22), 2.2), CREAM); ic.part(POLY([(1.5, 13.5), (4, 6), (12, 2), (20, 6), (22.5, 13.5)]), CORAL, round_=1.0)
    for x, y in ((7, 8), (12.5, 5.5), (17, 9)): ic.part(E((x - 1.7, y - 1.7, x + 1.7, y + 1.7)), CREAM, gloss=False, outline=False)
    ic.face(12, 16.4, 0.4)
@reg('sv_maple')
def _(ic):
    pts = [(12, 1), (14, 6), (19, 4), (17.5, 9.5), (23, 10), (18, 14), (19.5, 17.5), (13, 16), (12.6, 22.5), (11.4, 22.5), (11, 16), (4.5, 17.5), (6, 14), (1, 10), (6.5, 9.5), (5, 4), (10, 6)]
    ic.part(POLY(pts), CORAL, round_=0.3); line(ic, [(12, 21), (12, 7)], hx('#B83A30'), .6)
@reg('sv_bottle')
def _(ic):
    ic.part(RR((5, 8, 19, 23), 4), col('#DDF7F2', '#8CCFC8')); ic.part(RR((9, 3, 15, 9), 1.2), col('#E6F8F4', '#9CD6CF'), gloss=False)
    ic.part(RR((9.4, 1, 14.6, 4.2), 1), WOOD, gloss=False)
    ic.part(RR((7.6, 12, 16.4, 19), 1), CREAM, gloss=False, outline=False); line(ic, [(9, 14.5), (15, 14.5)], hx('#C88070'), .5); line(ic, [(9, 16.6), (13.5, 16.6)], hx('#C88070'), .5)
@reg('sv_cloud')
def _(ic):
    def cl(d, q):
        for b in ((1.5, 8, 11, 17), (6, 3.5, 17, 14), (12.5, 7, 22.5, 17), (4, 10, 20, 18.5)): d.ellipse([q(b[0]), q(b[1]), q(b[2]), q(b[3])], fill=255)
    line(ic, [(12, 17), (12, 23)], hx('#C98A55'), 1.3); ic.part(cl, col('#FFFFFF', '#FFC6DC'), round_=0.4); ic.face(12, 11.2, 0.45, 'happy')
@reg('sv_lantern')
def _(ic):
    line(ic, [(12, 1), (12, 4)], hx('#6A4A30'), .9); ic.part(RR((8, 3, 16, 6), 1), WOOD, gloss=False)
    ic.part(RR((5, 5.5, 19, 20), 5), col('#FFFCD6', '#FFE27A')); ic.part(RR((8, 19.5, 16, 22.5), 1), WOOD, gloss=False)
    for x, y in ((10, 10), (14.5, 13), (10.5, 16)): ic.part(E((x - 1.5, y - 1.5, x + 1.5, y + 1.5)), col('#F6FFB0', '#B8E04C'), gloss=False, outline=False)
@reg('sv_rainbow')
def _(ic):
    line(ic, [(12, 15), (12, 23)], hx('#F4F0FA'), 1.6)
    for i, c in enumerate(('#FF7FA6', '#FFB45A', '#FFE27A', '#8CDC7A', '#7CC4F4', '#A88BF4')):
        r_ = 10 - i * 1.5
        ic.part(E((12 - r_, 10 - r_, 12 + r_, 10 + r_)), (hx(c), mix(hx(c), hx('#000000'), .15)), gloss=(i == 0), outline=(i == 0))

# ───────── 5c icon ─────────
@reg('inherit')
def _(ic):
    ic.part(E((6, 6, 20, 23.5)), CREAM)
    for x, y in ((10, 12), (15, 15), (11, 19)): ic.part(E((x - 1.6, y - 1.6, x + 1.6, y + 1.6)), LILAC, gloss=False, outline=False)
    ic.part(lambda d, q: d.polygon([(q(6), q(9.5)), (q(1.6), q(5.2)), (q(2.4), q(1.6)), (q(6), q(3.6)), (q(9.6), q(1.6)), (q(10.4), q(5.2))], fill=255), PINK, gloss=False)
@reg('trick')
def _(ic):
    line(ic, [(3, 21), (14, 10)], hx('#8A5634'), 2.0)
    ic.part(POLY(star_pts(16, 8, 7, 3)), GOLD, round_=0.4); ic.face(16, 8.6, 0.38, 'happy')
    ic.part(POLY(star_pts(5, 6, 2.6, 1.0)), PINK, gloss=False, outline=False)
@reg('pattern')
def _(ic):
    ic.part(E((3, 3, 21, 21)), LILAC)
    for x, y in ((9, 8), (15, 10), (9, 15), (15, 16)): ic.part(E((x - 2, y - 2, x + 2, y + 2)), CREAM, gloss=False, outline=False)
@reg('fast')
def _(ic):
    for i, y in enumerate((6, 12, 18)): line(ic, [(1.5 + i, y), (8 + i, y)], hx('#FFFFFF'), 1.2)
    ic.part(POLY([(9, 2), (22, 12), (9, 22)]), GOLD, round_=0.7)

# ───────── 共用 widget ─────────
_IC = {}
def icon(board, kind, cx, cy, size_art, dim=False):
    if dim:
        im = H.icon_raw(kind); px = P(size_art * (k.ICN + 6) / k.ICN); im = im.resize((px, px), Image.LANCZOS)
        a = im.getchannel('A'); g = im.convert('L').point(lambda v: int(v * .55 + 40)); im = Image.merge('RGBA', (g, g, g.point(lambda v: min(255, v + 18)), a))
        board.alpha_composite(im, (int(cx - px / 2), int(cy - px / 2)))
    else: H.icon(board, kind, cx, cy, size_art)
def medal(board, cx, cy, d, fill, kind=None, isz=None, glow=1.0, dim=False):
    H.place(board, H.frame(d, d, d / 2, fill, glow=glow, ornate=False, rim=1.1), cx - P(d / 2), cy - P(d / 2))
    if kind: icon(board, kind, cx, cy, isz or d * 0.78, dim)
def board(w=195, h=422): return Image.new('RGBA', (P(w), P(h)), (0, 0, 0, 0))
def x3(im): return im.resize((im.width // 2, im.height // 2), Image.LANCZOS)
def crop(b):
    bb = b.getbbox(); return b.crop(bb) if bb else b
def pill(b, x, y, w, h, kind, label, icon_k=None, size=6.4):
    H.place(b, H.frame(w, h, h / 2, C[kind], glow=0 if kind == 'dis' else .8, ornate=False, rim=0.9), P(x), P(y))
    tc = hx('#FFFFFF') if kind != 'dis' else hx('#D6D8E4'); sc = mix(C[kind][1], hx('#000000'), .45)
    if icon_k:
        icon(b, icon_k, P(x + 7), P(y + h / 2), min(12, h + 1), dim=kind == 'dis')
        H.text(b, (P(x + w / 2 + 4), P(y + h / 2 - .2)), label, size, tc, 'serif', stroke=0.8, stroke_col=sc)
    else: H.text(b, (P(x + w / 2), P(y + h / 2 - .3)), label, size, tc, 'serif', stroke=0.8, stroke_col=sc)
def bar(b, x, y, w, h, val, cols=None, label=None):
    """HD 進度條（金邊凹槽＋漸變填＋高光）"""
    H.place(b, H.frame(w, h, h / 2, C['track'], glow=.3, ornate=False, rim=.8), P(x), P(y))
    fw = max(h, w * val); cols = cols or (hx('#FFF0A8'), hx('#F2A23E'))
    H.place(b, H.frame(fw - 1.6, h - 1.6, (h - 1.6) / 2, cols, glow=.9, ornate=False, rim=0.01), P(x + .8), P(y + .8))
    W, Hh = b.size; g = Image.new('L', (W, Hh), 0); ImageDraw.Draw(g).rounded_rectangle([P(x + 2), P(y + 1.3), P(x + fw - 2), P(y + h * .42)], radius=P(h / 4), fill=150)
    put(b, solid((W, Hh), hx('#FFFFFF')), gauss(g, P(.3)))
    if label: H.text(b, (P(x + w / 2), P(y + h / 2 - .2)), label, h * .72, hx('#FFFFFF'), 'cin', stroke=.8)
def panel(b, x, y, w, h, r=10, fill='panel', glow=1.0, ornate=None): H.place(b, H.frame(w, h, r, fill, glow=glow, ornate=ornate), P(x), P(y))

def pet_px(k, clip="interact", frame=0):
    """形態 pixel 圖（RGBA ndarray，已 crop bbox）— 用 5a interact strip（59 形態都有，有表情）"""
    g = LB._geo(k, clip); a = np.asarray(Image.open(os.path.join(ART, "sprites", g["png"])).convert("RGBA"))
    f = a[:, frame * g["CW"]:(frame + 1) * g["CW"]]
    ys, xs = np.nonzero(f[..., 3]); return f[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
def paste_px(b, arr, cx, cy, s=1.0, anchor='c', dark=False):
    """pixel 圖 nearest 放大貼上 SS board；s＝每 pixel 幾多 art 單位（P(s) 要整數）"""
    im = Image.fromarray(arr if not isinstance(arr, Image.Image) else np.asarray(arr)); n = max(1, int(round(P(s))))
    im = im.resize((im.width * n, im.height * n), Image.NEAREST)
    if dark:
        a = im.getchannel('A'); im = Image.new('RGBA', im.size, hx('#3A3F62')); im.putalpha(a)
    x = cx - im.width / 2; y = cy - im.height / 2 if anchor == 'c' else cy - im.height
    b.alpha_composite(im, (int(x), int(y)))
def portrait(b, k, cx, cy, d, fill=None, glow=1.0, ring=None, s=None, frame=0, dark=False):
    """圓章頭像：金邊玻璃圓＋pet pixel（底部對齊）"""
    fill = fill or C['navy_in']; medal(b, cx, cy, d, fill, glow=glow)
    W, Hh = b.size; g = Image.new('L', (W, Hh), 0); ImageDraw.Draw(g).ellipse([cx - P(d * .36), cy - P(d * .36), cx + P(d * .36), cy + P(d * .36)], fill=140)
    put(b, solid((W, Hh), C['cyan']), amul(gauss(g, P(d * .12)), .55))
    a = pet_px(k, frame=frame); sc = s or max(1 / 6, math.floor(P(d * .74) / max(a.shape) * 1) / 6)
    sc = max(1, int(P(d * .74) / max(a.shape))) / 6 if s is None else s
    paste_px(b, a, cx, cy + P(d * .36), sc, anchor='b', dark=dark)
    if ring:
        dd = ImageDraw.Draw(b); dd.ellipse([cx - P(d / 2 + 1.4), cy - P(d / 2 + 1.4), cx + P(d / 2 + 1.4), cy + P(d / 2 + 1.4)], outline=ring, width=P(1.1))
def glow_spot(b, cx, cy, r, colr=None, a=1.0):
    W, Hh = b.size; g = Image.new('L', (W, Hh), 0); ImageDraw.Draw(g).ellipse([cx - P(r), cy - P(r), cx + P(r), cy + P(r)], fill=200)
    put(b, solid((W, Hh), colr or C['glow']), amul(gauss(g, P(r * .45)), a))
def gold_line(b, pts, w=1.4):
    d = ImageDraw.Draw(b); pp = [(P(x), P(y)) for x, y in pts]
    d.line(pp, fill=C['line'], width=P(w + 1.0), joint='curve'); d.line(pp, fill=C['g_lo'], width=P(w + .3), joint='curve'); d.line(pp, fill=C['g_mid'], width=P(w * .6), joint='curve')
def dim(bg, a=0.55):
    o = Image.new('RGBA', bg.size, (14, 16, 38, int(255 * a))); bg = bg.copy(); bg.alpha_composite(o); return bg

def label_im(im, s):
    im = im.convert('RGB'); o = Image.new('RGB', (im.width, im.height + 46), (40, 28, 36)); o.paste(im, (0, 46))
    ImageDraw.Draw(o).text((14, 6), s, font=LB.font(28), fill=(255, 240, 220)); return o
def strip_sheet(ims, titles, path, gap=12):
    ims = [label_im(im, t) for im, t in zip(ims, titles)]; Hm = max(i.height for i in ims)
    sh = Image.new('RGB', (sum(i.width for i in ims) + gap * (len(ims) - 1), Hm), (40, 28, 36)); x = 0
    for i in ims: sh.paste(i, (x, 0)); x += i.width + gap
    sh.save(path); return sh
def parts_sheet(paths, out, base):
    ims = [Image.open(os.path.join(base, p)).convert('RGBA') for p in paths]; W = 1200; x = y = 10; rowh = 0; pos = []
    for im in ims:
        if x + im.width > W - 10: x = 10; y += rowh + 10; rowh = 0
        pos.append((x, y)); x += im.width + 10; rowh = max(rowh, im.height)
    sh = Image.new('RGBA', (W, y + rowh + 10), (28, 30, 56, 255))
    for im, p in zip(ims, pos): sh.alpha_composite(im, p)
    sh.convert('RGB').save(out)

# ───────── 房間合成（同 4b preview.room，但可指定房）─────────
HJ = json.load(open(os.path.join(ART, "sprites/series2_house/house.json")))
def _ld(p): return np.asarray(Image.open(os.path.join(ART, "sprites/series2_house", p)).convert("RGBA"))
def _shadow(w, h):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(im).ellipse((0, 0, w - 1, h - 1), fill=(60, 36, 40, 70)); return np.asarray(im)
def room_arr(room, var, items, pets=(), extra=()):
    import house_4b_room as R
    base = os.path.join(ART, "sprites/series2_house/room") if room == "room1" else os.path.join(LB.OUTL, "5a/rooms", room)
    S = []; night = var == "night"
    for slot, fid in items.items():
        if not fid: continue
        f = HJ["furniture"][fid]; ax, ay = HJ["slots"][slot]["anchor"]; px, py = f["pivot"]; x, y = ax - px, ay - py
        z = {"wall": -1000, "floor": -500}.get(HJ["slots"][slot]["layer"], ay); S.append((z, _ld(f["png"]), x, y, "furn"))
        if "shadow" in f: w, h = f["shadow"]; S.append((-400, _shadow(w, h), ax - w // 2, ay - h // 2 - 1, "shadow"))
        if slot == "bed": S.append((ay + 0.1, _ld(f["front"]), x, y, "furn"))
        if slot == "lamp" and night:
            g = _ld(f["glow"]); gx, gy = f["glowCenter"]; S.append((9999, g, x + gx - g.shape[1] // 2, y + gy - g.shape[0] // 2, "glow"))
    for img, piv, x, y, sy in pets:
        S.append((sy, img, x - piv[0], y - piv[1], "pet"))
        if sy is not None: S.append((-399, _shadow(20, 5), x - 10, y - 3, "shadow"))
    S += list(extra)
    return R.compose(var, base, S)
def room_ss(room, var, items, pets=(), extra=(), dy=0):
    im = Image.fromarray(room_arr(room, var, items, pets, extra)).convert('RGBA')
    if dy:
        o = Image.new('RGBA', im.size, (20, 16, 30, 255)); o.paste(im, (0, dy)); im = o
    return im.resize((P(195), P(422)), Image.NEAREST)
def strip_frame(k, clip, i, flip=False):
    g = LB._geo(k, clip); a = np.asarray(Image.open(os.path.join(ART, "sprites", g["png"])).convert("RGBA"))
    n = a.shape[1] // g["CW"]; f = a[:, (i % n) * g["CW"]:((i % n) + 1) * g["CW"]].copy(); piv = (g["PX"], g["PY"])
    if flip: f = f[:, ::-1].copy(); piv = (g["CW"] - 1 - piv[0], piv[1])
    return f, piv, g
