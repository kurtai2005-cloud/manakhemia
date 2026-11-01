# 《微光小圃》UI 卡通可愛風格參考板（概念用）— 純 Pillow/numpy 程序繪製，無 AI。
import json, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

ROOT = '/workspace/game-design/art-pet'
OUT = f'{ROOT}/ui/style_ref'
SS = 2; S = 3; U = S * SS          # 6 SS-px per art unit; final = reduce(2) -> 3x
def P(v): return int(round(v * U))

CJK = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
FRED = '/usr/share/fonts/truetype/sand-box/google/Fredoka/Fredoka-VariableFont_wdth,wght.ttf'
BALOO = '/usr/share/fonts/truetype/sand-box/google/Baloo 2/Baloo2-VariableFont_wght.ttf'
_fc = {}
def font(kind, size_art):
    px = P(size_art); key = (kind, px)
    if key not in _fc:
        if kind == 'cjk': f = ImageFont.truetype(CJK, px, index=4)
        elif kind == 'fred':
            f = ImageFont.truetype(FRED, px); f.set_variation_by_axes([700, 100])
        else:
            f = ImageFont.truetype(BALOO, px); f.set_variation_by_axes([800])
        _fc[key] = f
    return _fc[key]

def hx(h, a=255):
    h = h.lstrip('#'); return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)
def mix(c1, c2, t):
    return tuple(int(round(c1[i] * (1 - t) + c2[i] * t)) for i in range(4))

# ---------------- themes ----------------
A = dict(key='A', acts_tilt=[0,0,0,0], name='棉花糖奶油', en='Marshmallow Cream',
    sub='粗圓角・深啡粗邊・果凍高光・軟糖陰影・彈彈 icon 有表情',
    ol=hx('#5B3A35'), ow=1.6, wob=0, sticker=0,
    panel=(hx('#FFF8EC'), hx('#FFE9D2')), inset=(hx('#FBE3CB'), hx('#F7D8BC')),
    pri=(hx('#FFA7BF'), hx('#FF7598')), sec=(hx('#A6EDD3'), hx('#6CD6B4')),
    dis=(hx('#E7DDD6'), hx('#CFC3BA')), accent=(hx('#FFE48A'), hx('#FFC24D')),
    title=(hx('#FF9BB5'), hx('#FF7398')), dock=(hx('#FFF8EC'), hx('#FFE4CC')),
    text=hx('#5B3A35'), shadow=hx('#5B3A35', 70), sh_dy=2.2, sh_blur=0.4,
    track=hx('#EBD3BD'), red=hx('#FF4F6D'), tilt=0,
    bg=(hx('#FFF1E4'), hx('#FFE2E8')), font_num='fred',
    swatch=['#FFF8EC', '#FF8FAB', '#8FE3C8', '#FFD86B', '#B9A4FF', '#5B3A35'])
B = dict(key='B', acts_tilt=[-4,3,-3,4], name='繪本貼紙', en='Storybook Stickers',
    sub='白色貼紙邊・粉彩・手繪微抖線・標籤／膠紙・紙紋',
    ol=hx('#5E4B72'), ow=1.0, wob=0.6, sticker=2.4,
    panel=(hx('#FFFDF7'), hx('#FBF4E6')), inset=(hx('#F3ECFF'), hx('#EAE0FB')),
    pri=(hx('#FFC09A'), hx('#FF9A7A')), sec=(hx('#B8E2FF'), hx('#8CC8F2')),
    dis=(hx('#ECE8EE'), hx('#D8D2DC')), accent=(hx('#FFF0A0'), hx('#FFD86A')),
    title=(hx('#CDB8F6'), hx('#AE92EE')), dock=(hx('#FFFDF7'), hx('#F6EEFF')),
    text=hx('#4E3D62'), shadow=hx('#4E3D62', 55), sh_dy=1.6, sh_blur=1.6,
    track=hx('#EDE5F5'), red=hx('#FF6B81'), tilt=1,
    bg=(hx('#F4F0FF'), hx('#FFF4EA')), font_num='baloo',
    swatch=['#FFFDF7', '#FFB08A', '#A8D8F5', '#CDB8F6', '#FFE58A', '#5E4B72'])

# ---------------- masks / primitives ----------------
def rr_points(x0, y0, x1, y1, r, wob=0.0, seed=0, n=24, tag=False):
    r = max(0.01, min(r, (x1 - x0) / 2, (y1 - y0) / 2))
    cs = [(x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)]
    pts = []
    for k, (cx, cy, a0) in enumerate(cs):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a), a))
    out = []
    perim = len(pts)
    if tag:
        cy = (y0 + y1) / 2; hh = (y1 - y0)
        pts = [(max(x, x0 + abs(y - cy) * 0.75) if x < x0 + hh * 0.5 else x, y, a) for x, y, a in pts]
    for j, (x, y, a) in enumerate(pts):
        if wob:
            t = j / perim * 2 * math.pi
            d = wob * (math.sin(t * 5 + seed) * 0.6 + math.sin(t * 13 + seed * 2.1) * 0.4)
            # push along corner normal; on straight edges normal of nearest corner ok
            x += d * math.cos(a); y += d * math.sin(a)
        out.append((x, y))
    return out

def mask_poly(size, pts, ss=2):
    m = Image.new('L', (size[0] * ss, size[1] * ss), 0)
    ImageDraw.Draw(m).polygon([(x * ss, y * ss) for x, y in pts], fill=255)
    return m.resize(size, Image.LANCZOS)

def grad(size, c0, c1):
    w, h = size
    t = np.linspace(0, 1, h)[:, None, None]
    a = np.array(c0, float)[None, None, :] * (1 - t) + np.array(c1, float)[None, None, :] * t
    a = np.repeat(a, w, axis=1)
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')

def solid(size, c): return Image.new('RGBA', size, c)

def put(dst, src, mask, xy=(0, 0)):
    """alpha-composite src (RGBA, its own alpha * mask) onto dst at xy"""
    s = src.copy()
    a = ImageChops.multiply(s.getchannel('A'), mask)
    s.putalpha(a)
    dst.alpha_composite(s, xy)

def dilate(m, r):
    if r <= 0: return m
    b = m.filter(ImageFilter.GaussianBlur(r * 0.55))
    return b.point(lambda v: min(255, int(v * 5.5)))

def chunky(th, w, h, r, fill, seed=0, gloss=True, pressed=False, shadow=True, ow=None, wob=None, sticker=None, tag=False):
    """returns (img, ox, oy) : a component box in SS px; (ox,oy)=where box origin sits in img"""
    ow = th['ow'] if ow is None else ow
    wob = th['wob'] if wob is None else wob
    st = th['sticker'] if sticker is None else sticker
    pad = P(ow + st + 6)
    W, H = P(w) + pad * 2, P(h) + pad * 2
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    def m(e, sd=seed):
        return mask_poly((W, H), rr_points(pad - P(e), pad - P(e), pad + P(w) + P(e), pad + P(h) + P(e), P(r + e), P(wob), sd, tag=tag))
    outer = m(ow + st)
    if shadow:
        dy = P(th['sh_dy'] * (0.35 if pressed else 1))
        sh = Image.new('L', (W, H), 0); sh.paste(outer, (0, dy))
        if th['sh_blur']: sh = sh.filter(ImageFilter.GaussianBlur(P(th['sh_blur'])))
        put(img, solid((W, H), th['shadow']), sh)
    put(img, solid((W, H), th['ol']), outer)
    if st:
        put(img, solid((W, H), hx('#FFFFFF')), m(st))
    inner = m(0)
    c0, c1 = fill
    if pressed: c0, c1 = mix(c0, c1, 0.6), mix(c1, hx('#000000'), 0.08)
    put(img, grad((W, H), c0, c1), inner)
    if th['key'] == 'B':
        rng = np.random.default_rng(seed + 99)
        nz = Image.fromarray((rng.random((H, W)) ** 3 * 255 * 0.22).astype(np.uint8), 'L').filter(ImageFilter.GaussianBlur(1.2))
        put(img, solid((W, H), th['ol']), ImageChops.multiply(nz, inner))
    if gloss:
        # jelly highlight band on top + sparkle dot
        gh = h * (0.30 if pressed else 0.42)
        gm = mask_poly((W, H), rr_points(pad + P(min(3, w * .12)), pad + P(1.2), pad + P(w) - P(min(3, w * .12)), pad + P(1.2 + gh), P(min(r, gh / 2)), 0, 0))
        gm = ImageChops.multiply(gm, inner)
        gl = grad((W, H), hx('#FFFFFF', 170), hx('#FFFFFF', 25))
        put(img, gl, gm)
        if not pressed and h > 8:
            d = Image.new('L', (W, H), 0); dd = ImageDraw.Draw(d)
            cx, cy = pad + P(min(r * 0.75, w * 0.2) + 1.0), pad + P(2.4)
            dd.ellipse([cx - P(1.1), cy - P(0.8), cx + P(1.1), cy + P(0.8)], fill=235)
            dd.ellipse([cx + P(1.7), cy - P(0.45), cx + P(2.5), cy + P(0.35)], fill=200)
            put(img, solid((W, H), hx('#FFFFFF')), ImageChops.multiply(d, inner))
        # bottom inner rim shade
        bm = ImageChops.subtract(inner, ImageChops.offset(inner, 0, -P(1.3)))
        put(img, solid((W, H), mix(c1, hx('#000000'), 0.18)), bm)
    return img, pad, pad

def place(board, comp, x, y, angle=0):
    img, ox, oy = comp
    if angle:
        cx, cy = img.width / 2, img.height / 2
        img = img.rotate(angle, resample=Image.BICUBIC, expand=True)
        ox += (img.width - comp[0].width) / 2; oy += (img.height - comp[0].height) / 2
    board.alpha_composite(img, (int(round(x - ox)), int(round(y - oy))))

def text(board, xy, s, size, color, kind='cjk', anchor='mm', stroke=0, stroke_col=None, shadow=None):
    d = ImageDraw.Draw(board)
    f = font(kind, size)
    x, y = xy
    if shadow is not None:
        d.text((x, y + P(0.8)), s, font=f, fill=shadow, anchor=anchor, stroke_width=P(stroke), stroke_fill=shadow)
    d.text((x, y), s, font=f, fill=color, anchor=anchor, stroke_width=P(stroke), stroke_fill=stroke_col)

# ---------------- icons ----------------
ICN = 24
class Icon:
    def __init__(self, th, n=ICN):
        self.th = th; self.n = n; self.N = P(n + 6); self.o = P(3)
        self.img = Image.new('RGBA', (self.N, self.N), (0, 0, 0, 0))
        self.ow = th['ow'] * (0.95 if th['key'] == 'A' else 1.0)
    def c(self, v): return self.o + P(v)
    def mask(self, fn):
        m = Image.new('L', (self.N * 2, self.N * 2), 0)
        fn(ImageDraw.Draw(m), lambda v: (self.o + P(v)) * 2)
        return m.resize((self.N, self.N), Image.LANCZOS)
    def part(self, fn, fill, gloss=True, outline=True, m=None, round_=0):
        m = m if m is not None else self.mask(fn)
        if round_:
            m = m.filter(ImageFilter.GaussianBlur(P(round_))).point(lambda v: 255 if v > 128 else int(v * 2 * (v / 128.0)))
        if outline:
            put(self.img, solid(self.img.size, self.th['ol']), dilate(m, P(self.ow)))
        c0, c1 = fill
        put(self.img, grad(self.img.size, c0, c1), m)
        if gloss:
            bb = m.getbbox()
            if bb:
                x0, y0, x1, y1 = bb; w = x1 - x0; h = y1 - y0
                g = Image.new('L', self.img.size, 0); gd = ImageDraw.Draw(g)
                gd.ellipse([x0 + w * .16, y0 + h * .08, x0 + w * .46, y0 + h * .30], fill=200)
                gd.ellipse([x0 + w * .52, y0 + h * .10, x0 + w * .60, y0 + h * .18], fill=170)
                g = g.filter(ImageFilter.GaussianBlur(P(0.25)))
                put(self.img, solid(self.img.size, hx('#FFFFFF')), ImageChops.multiply(g, m))
                # soft lower shade
                sh = ImageChops.subtract(m, ImageChops.offset(m, -P(1.0), -P(1.6)))
                sh = sh.filter(ImageFilter.GaussianBlur(P(0.6)))
                put(self.img, solid(self.img.size, mix(c1, hx('#000000'), 0.15)), ImageChops.multiply(sh, m))
        return m
    def face(self, cx, cy, s=1.0, mood='smile'):
        d = ImageDraw.Draw(self.img); c = self.c
        ink = hx('#3B2A2E')
        ex = 2.7 * s
        for sx in (-1, 1):
            x = cx + sx * ex
            if mood == 'sleep':
                d.arc([c(x - 1.3 * s), c(cy - 1.0 * s), c(x + 1.3 * s), c(cy + 1.2 * s)], 200, 340, fill=ink, width=P(0.55 * s))
            else:
                d.ellipse([c(x - 0.95 * s), c(cy - 1.25 * s), c(x + 0.95 * s), c(cy + 1.25 * s)], fill=ink)
                d.ellipse([c(x - 0.55 * s), c(cy - 0.95 * s), c(x - 0.05 * s), c(cy - 0.35 * s)], fill=(255, 255, 255, 255))
            d.ellipse([c(x + sx * 1.6 * s - 1.2 * s), c(cy + 1.4 * s), c(x + sx * 1.6 * s + 1.2 * s), c(cy + 2.3 * s)], fill=hx('#FF7F9E', 150))
        if mood in ('smile', 'sleep'):
            d.arc([c(cx - 0.9 * s), c(cy + 0.2 * s), c(cx + 0.9 * s), c(cy + 1.7 * s)], 20, 160, fill=ink, width=P(0.5 * s))
        elif mood == 'open':
            d.ellipse([c(cx - 0.8 * s), c(cy + 0.6 * s), c(cx + 0.8 * s), c(cy + 2.1 * s)], fill=hx('#B33B55'))
    def finish(self):
        th = self.th
        if th['sticker']:
            a = self.img.getchannel('A')
            st = dilate(a, P(th['sticker'] * 0.8))
            ol = dilate(st, P(0.7))
            base = Image.new('RGBA', self.img.size, (0, 0, 0, 0))
            sh = ImageChops.offset(ol, 0, P(1.0)).filter(ImageFilter.GaussianBlur(P(0.9)))
            put(base, solid(base.size, th['shadow']), sh)
            put(base, solid(base.size, th['ol']), ol)
            put(base, solid(base.size, hx('#FFFFFF')), st)
            base.alpha_composite(self.img)
            return base
        base = Image.new('RGBA', self.img.size, (0, 0, 0, 0))
        sh = ImageChops.offset(self.img.getchannel('A'), 0, P(1.2)).filter(ImageFilter.GaussianBlur(P(0.3)))
        put(base, solid(base.size, th['shadow']), sh)
        base.alpha_composite(self.img)
        return base

def star_pts(cx, cy, R, r, n=5, rot=-90):
    pts = []
    for i in range(n * 2):
        a = math.radians(rot + i * 180 / n); rad = R if i % 2 == 0 else r
        pts.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))
    return pts

def icon(th, kind):
    ic = Icon(th)
    E = lambda b: (lambda d, k: d.ellipse([k(b[0]), k(b[1]), k(b[2]), k(b[3])], fill=255))
    POLY = lambda pts: (lambda d, k: d.polygon([(k(x), k(y)) for x, y in pts], fill=255))
    RR = lambda b, r: (lambda d, k: d.rounded_rectangle([k(b[0]), k(b[1]), k(b[2]), k(b[3])], radius=k(r) - k(0), fill=255))
    if kind == 'feed':      # 飯糰仔
        ic.part(POLY([(12, 2.2), (22.5, 20.8), (1.5, 20.8)]), (hx('#FFFFFF'), hx('#F2ECE2')), round_=1.1)
        ic.part(RR((7.5, 14.2, 16.5, 21.3), 1.6), (hx('#4C7060'), hx('#2F4E40')), gloss=False)
        ic.face(12, 10.6, 0.8)
    elif kind == 'play':    # 波波
        m = ic.part(E((2.5, 2.5, 21.5, 21.5)), (hx('#FFB3C6'), hx('#FF7FA0')), gloss=False)
        band = ic.mask(lambda d, k: d.polygon([(k(-2), k(13)), (k(26), k(6)), (k(26), k(11)), (k(-2), k(18))], fill=255))
        put(ic.img, grad(ic.img.size, hx('#FFF1A6'), hx('#FFD860')), ImageChops.multiply(band, m))
        ic.part(None, (hx('#FFB3C6'), hx('#FF7FA0')), outline=False, m=Image.new('L', ic.img.size, 0))
        g = Image.new('L', ic.img.size, 0); ImageDraw.Draw(g).ellipse([ic.c(6), ic.c(4.5), ic.c(11), ic.c(8)], fill=210)
        put(ic.img, solid(ic.img.size, hx('#FFFFFF')), ImageChops.multiply(g, m))
        ic.face(12, 12.5, 0.85, 'open')
    elif kind == 'clean':   # 水滴
        def drop(d, k):
            d.ellipse([k(4.5), k(8.5), k(19.5), k(23)], fill=255)
            d.polygon([(k(12), k(0.8)), (k(5.2), k(13.5)), (k(18.8), k(13.5))], fill=255)
        ic.part(drop, (hx('#BDE8FF'), hx('#66BDF5')), round_=0.5)
        ic.part(E((17.5, 1.5, 22.5, 6.5)), (hx('#FFFFFF'), hx('#DDF3FF')), gloss=False)
        ic.part(E((19.5, 8.0, 22.5, 11.0)), (hx('#FFFFFF'), hx('#DDF3FF')), gloss=False)
        ic.face(12, 15.8, 0.85)
    elif kind == 'sleep':   # 瞓覺月亮
        m1 = ic.mask(E((2, 2.5, 21, 21.5))); m2 = ic.mask(E((8.5, -1.5, 25.5, 15.5)))
        ic.part(None, (hx('#FFF0A8'), hx('#FFC94A')), m=ImageChops.subtract(m1, m2))
        ic.face(8.6, 14.2, 0.62, 'sleep')
        d = ImageDraw.Draw(ic.img)
        for (x, y, sz) in [(17.5, 9.5, 5.0), (21, 4.5, 3.8)]:
            text(ic.img, (ic.c(x), ic.c(y)), 'z', sz, ic.th['ol'], 'fred', stroke=0.0)
    elif kind == 'book':    # 手帳
        ic.part(RR((3, 2.5, 21, 21.5), 3.2), (hx('#CDBBFF'), hx('#9E86F2')))
        ic.part(RR((16.5, 4.5, 20.0, 19.5), 1.0), (hx('#FFFBF0'), hx('#F1E8D6')), gloss=False)
        def heart(d, k, cx=9.6, cy=7.5, s=0.55):
            d.ellipse([k(cx - 3 * s), k(cy - 2 * s), k(cx), k(cy + 1 * s)], fill=255)
            d.ellipse([k(cx), k(cy - 2 * s), k(cx + 3 * s), k(cy + 1 * s)], fill=255)
            d.polygon([(k(cx - 2.9 * s), k(cy - 0.1 * s)), (k(cx + 2.9 * s), k(cy - 0.1 * s)), (k(cx), k(cy + 3.4 * s))], fill=255)
        ic.part(heart, (hx('#FFB9CB'), hx('#FF7FA0')), gloss=False, outline=False)
        ic.face(9.8, 14.3, 0.78)
    elif kind == 'light':   # ✦ 光粒
        ic.part(POLY([(12, 0.8), (15, 9), (23.2, 12), (15, 15), (12, 23.2), (9, 15), (0.8, 12), (9, 9)]), (hx('#E6FFF6'), hx('#7FE3CF')), round_=0.6)
        ic.face(12, 12.2, 0.62)
    elif kind == 'star':    # ⭐ 星星碎
        ic.part(POLY(star_pts(12, 13, 11.5, 5.6)), (hx('#FFF0A0'), hx('#FFB933')), round_=1.0)
        ic.face(12, 13.4, 0.75)
    elif kind == 'heart':
        def hrt(d, k):
            d.ellipse([k(1.8), k(3.0), k(12.6), k(13.8)], fill=255); d.ellipse([k(11.4), k(3.0), k(22.2), k(13.8)], fill=255)
            d.polygon([(k(2.2), k(10.2)), (k(21.8), k(10.2)), (k(12), k(22.2))], fill=255)
        ic.part(hrt, (hx('#FFA9BF'), hx('#FF5F86')), round_=0.6)
        ic.face(12, 11.6, 0.8)
    elif kind == 'gear':
        def gear(d, k):
            for i in range(8):
                a = i * math.pi / 4
                cx, cy = 12 + 8.6 * math.cos(a), 12 + 8.6 * math.sin(a)
                d.ellipse([k(cx - 3.0), k(cy - 3.0), k(cx + 3.0), k(cy + 3.0)], fill=255)
            d.ellipse([k(3.6), k(3.6), k(20.4), k(20.4)], fill=255)
        ic.part(gear, (hx('#D9F2FF'), hx('#9CC9EA')), round_=0.4)
        ic.face(12, 11.8, 0.75)
    elif kind == 'gift':
        ic.part(E((5, 1.5, 12.5, 8.5)), (hx('#FFE48A'), hx('#FFC24D')), gloss=False)
        ic.part(E((11.5, 1.5, 19, 8.5)), (hx('#FFE48A'), hx('#FFC24D')), gloss=False)
        ic.part(RR((3.5, 10, 20.5, 22), 2.4), (hx('#FFC4D3'), hx('#FF8FAE')))
        ic.part(RR((2, 6.8, 22, 11.6), 2.0), (hx('#FFD3DF'), hx('#FFA3BC')))
        ic.part(RR((10.3, 6.8, 13.7, 22), 0.6), (hx('#FFE48A'), hx('#FFC24D')), gloss=False, outline=False)
        ic.face(12, 16.3, 0.7)
    elif kind == 'sprout':  # 小圃 盆栽
        def leafL(d, k): d.ellipse([k(3), k(2.5), k(12.2), k(9.5)], fill=255)
        def leafR(d, k): d.ellipse([k(11.8), k(1.0), k(21), k(8.0)], fill=255)
        ic.part(lambda d, k: d.rounded_rectangle([k(11.2), k(5), k(12.8), k(12)], radius=k(0.8) - k(0), fill=255), (hx('#8EDB7A'), hx('#58B85A')), gloss=False)
        ic.part(leafL, (hx('#B5F09A'), hx('#64C45E')))
        ic.part(leafR, (hx('#B5F09A'), hx('#64C45E')))
        ic.part(POLY([(3.5, 11), (20.5, 11), (18.2, 22.5), (5.8, 22.5)]), (hx('#FFC09A'), hx('#EE8E66')), round_=0.6)
        ic.part(RR((2.5, 10, 21.5, 13.6), 1.6), (hx('#FFD1B0'), hx('#F4A27C')), gloss=False)
        ic.face(12, 17.2, 0.72)
    return ic.finish()

ICON_CACHE = {}
def get_icon(th, kind, size_art):
    k = (th['key'], kind)
    if k not in ICON_CACHE: ICON_CACHE[k] = icon(th, kind)
    im = ICON_CACHE[k]
    px = P(size_art * (ICN + 6) / ICN)
    return im.resize((px, px), Image.LANCZOS)
def draw_icon(board, th, kind, cx, cy, size_art):
    im = get_icon(th, kind, size_art)
    board.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

# ---------------- scene ----------------
def load(p): return Image.open(p).convert('RGBA')
def scene(H, pet_key, frame=0):
    d = f'{ROOT}/scenes/hd2d/{H}'
    g = json.load(open(f'{d}/grade.json'))
    crop = (14, 12, 14 + 195, 12 + 422)
    img = Image.new('RGBA', (195, 422))
    for L in ['sky', 'far', 'mid']:
        img.alpha_composite(load(f'{d}/{L}.png').crop(crop))
    pet = load(f'{ROOT}/sprites/tuanrong/species_concept/from_ref/tuned_48/idle/{pet_key}_idle.png').crop((48 * frame, 0, 48 * frame + 48, 48))
    pa = np.asarray(pet).astype(float)
    t = np.array(hx(g['petTint'])[:3]) / 255 * np.array(hx(g['ambientTint'])[:3]) / 255
    pa[..., :3] *= t
    pet = Image.fromarray(pa.clip(0, 255).astype(np.uint8), 'RGBA')
    fx, fy = 97, 292
    sh = Image.new('RGBA', (195, 422)); ImageDraw.Draw(sh).ellipse([fx - 13, fy - 3, fx + 13, fy + 2], fill=(30, 40, 30, 70))
    img.alpha_composite(sh)
    img.alpha_composite(pet, (fx - 24, fy - 45))
    img.alpha_composite(load(f'{d}/fore.png').crop(crop))
    a = np.asarray(img).astype(float)
    lm = np.asarray(Image.open(f'{d}/lightmap.png').convert('RGB').crop(crop)).astype(float) / 255
    la = np.asarray(Image.open(f'{d}/light_add.png').convert('RGB').crop(crop)).astype(float)
    eb = np.asarray(Image.open(f'{d}/emissive_blur.png').convert('RGB').crop(crop)).astype(float)
    a[..., :3] = a[..., :3] * lm + la + eb * g['bloom']['intensity']
    fc = np.array(hx(g['fog']['color'])[:3], float); fd = g['fog']['density']
    a[..., :3] = a[..., :3] * (1 - fd) + fc * fd
    v = np.asarray(load(f'{d}/vignette.png')).astype(float)
    va = v[..., 3:4] / 255
    a[..., :3] = a[..., :3] * (1 - va) + v[..., :3] * va
    a[..., 3] = 255
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')

# ---------------- composite widgets (art coords relative to origin X,Y in SS px) ----------------
def need_pill(board, th, X, Y, x, y, w, kind, val, col):
    h = 15
    place(board, chunky(th, w, h, h / 2, th['panel'], seed=int(x)), X + P(x), Y + P(y))
    # track
    tx0, tx1 = x + 13.5, x + w - 3.2
    place(board, chunky(th, tx1 - tx0, 5.6, 2.8, (th['track'], mix(th['track'], hx('#FFFFFF'), .3)), gloss=False, shadow=False, ow=0.6, sticker=0, wob=0), X + P(tx0), Y + P(y + 4.7))
    fw = max(5.6, (tx1 - tx0) * val)
    place(board, chunky(th, fw, 5.6, 2.8, col, shadow=False, ow=0.0, sticker=0, wob=0), X + P(tx0), Y + P(y + 4.7))
    draw_icon(board, th, kind, X + P(x + 6.8), Y + P(y + 7.2), 15)

def currency_chip(board, th, X, Y, x, y, w, kind, s):
    h = 18
    if th['key'] == 'B': place(board, chunky(th, w, h, 4, th['panel'], seed=int(x) + 3), X + P(x), Y + P(y), 2)
    else: place(board, chunky(th, w, h, h / 2, th['panel'], seed=int(x) + 3), X + P(x), Y + P(y))
    draw_icon(board, th, kind, X + P(x + 4), Y + P(y + 9), 18)
    text(board, (X + P(x + w / 2 + 6), Y + P(y + 8.6)), s, 10.5, th['text'], th['font_num'])

def red_dot(board, th, cx, cy, n=None):
    r = P(3.6 if n else 2.6)
    d = ImageDraw.Draw(board)
    d.ellipse([cx - r - P(0.9), cy - r - P(0.9), cx + r + P(0.9), cy + r + P(0.9)], fill=hx('#FFFFFF'))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=th['red'])
    d.ellipse([cx - r * .55, cy - r * .7, cx - r * .05, cy - r * .3], fill=hx('#FFFFFF', 200))
    if n: text(board, (cx, cy + P(0.2)), str(n), 6.2, hx('#FFFFFF'), 'fred')

def tag_shape(th, w, h, fill, seed=0):
    """B: label tag with notched left point + punch hole"""
    img, ox, oy = chunky(th, w, h, 3.5, fill, seed=seed, tag=True)
    d = ImageDraw.Draw(img)
    cx, cy = ox + P(h * 0.42 + 2.2), oy + P(h / 2)
    d.ellipse([cx - P(1.6), cy - P(1.6), cx + P(1.6), cy + P(1.6)], fill=th['ol'])
    d.ellipse([cx - P(1.0), cy - P(1.0), cx + P(1.0), cy + P(1.0)], fill=hx('#FFFFFF'))
    return img, ox, oy

def button(board, th, X, Y, x, y, w, h, kind, label, pressed=False, icon_k=None, ang=0):
    fill = th[kind]
    sq = 0.6 if pressed else 0
    dy = th['sh_dy'] * 0.65 if pressed else 0
    comp = chunky(th, w + sq * 2, h - sq, min(h / 2, 9), fill, seed=len(label) * 7 + int(x), gloss=(kind != 'dis'), pressed=pressed)
    place(board, comp, X + P(x - sq), Y + P(y + sq + dy), ang)
    tc = hx('#FFFFFF') if kind != 'dis' else hx('#B3A79F')
    sc = mix(fill[1], hx('#000000'), 0.35) if kind != 'dis' else None
    cx = x + w / 2 + (5 if icon_k else 0)
    if icon_k: draw_icon(board, th, icon_k, X + P(x + 9), Y + P(y + h / 2 + dy + sq / 2), 13)
    text(board, (X + P(cx), Y + P(y + h / 2 + dy + sq / 2 - 0.4)), label, 8.6, tc, 'cjk',
         stroke=(1.0 if kind != 'dis' else 0), stroke_col=sc)

def dock(board, th, X, Y, x, y, w=191, active=0, dot=2):
    h = 50
    place(board, chunky(th, w, h, 18, th['dock'], seed=11), X + P(x), Y + P(y))
    tabs = [('heart', '照顧'), ('play', '玩'), ('sprout', '小圃'), ('book', '手帳'), ('gear', '設定')]
    tw = w / 5
    for i, (k, lab) in enumerate(tabs):
        cx = x + tw * (i + .5)
        if i == active:
            bw = 34
            comp = chunky(th, bw, 40, 15, th['title'] if th['key'] == 'B' else th['pri'], seed=5)
            place(board, comp, X + P(cx - bw / 2), Y + P(y - 6), -5 if th['tilt'] else 0)
            draw_icon(board, th, k, X + P(cx), Y + P(y + 7), 22)
            text(board, (X + P(cx), Y + P(y + 25.5)), lab, 7.6, hx('#FFFFFF'), stroke=0.9, stroke_col=mix(th['pri'][1] if th['key']=='A' else th['title'][1], hx('#000000'), .35))
        else:
            draw_icon(board, th, k, X + P(cx), Y + P(y + 18), 19)
            text(board, (X + P(cx), Y + P(y + 36.5)), lab, 7.0, th['text'])
        if i == dot: red_dot(board, th, X + P(cx + 9), Y + P(y + 9), 1)
    # little 'home pill' indicator under active
    d = ImageDraw.Draw(board)
    cx = x + tw * (active + .5)
    d.rounded_rectangle([X + P(cx - 5), Y + P(y + h - 6.2), X + P(cx + 5), Y + P(y + h - 4.4)], radius=P(1), fill=th['pri'][1])

def toast(board, th, X, Y, x, y, w, msg):
    h = 19
    if th['key'] == 'B':
        place(board, tag_shape(th, w, h, th['accent'], seed=4), X + P(x), Y + P(y), 2)
        draw_icon(board, th, 'light', X + P(x + 16), Y + P(y + h / 2), 15)
        text(board, (X + P(x + w / 2 + 8), Y + P(y + h / 2)), msg, 8.2, th['text'])
    else:
        place(board, chunky(th, w, h, h / 2, th['accent'], seed=4), X + P(x), Y + P(y))
        draw_icon(board, th, 'light', X + P(x + 9), Y + P(y + h / 2 - 0.5), 17)
        text(board, (X + P(x + w / 2 + 6), Y + P(y + h / 2)), msg, 8.2, th['text'])

def speech(board, th, X, Y, x, y, w, h, msg, icon_k=None):
    comp = chunky(th, w, h, h / 2, th['panel'], seed=9, gloss=False)
    img, ox, oy = comp
    # tail
    d = ImageDraw.Draw(img)
    tx = ox + P(8)
    tail = [(tx, oy + P(h - 1)), (tx + P(7), oy + P(h - 1)), (tx - P(1), oy + P(h + 6))]
    o = P(th['ow'] + th['sticker'])
    d.polygon([(tx - o, oy + P(h - 2)), (tx + P(7) + o * 1.2, oy + P(h - 2)), (tx - P(1) - o * .6, oy + P(h + 6) + o)], fill=th['ol'])
    if th['sticker']:
        so = P(th['sticker'])
        d.polygon([(tx - so, oy + P(h - 2.5)), (tx + P(7) + so, oy + P(h - 2.5)), (tx - P(1) - so * .5, oy + P(h + 6) + so * .7)], fill=hx('#FFFFFF'))
    d.polygon(tail, fill=th['panel'][1])
    place(board, (img, ox, oy), X + P(x), Y + P(y), 2 if th['tilt'] else 0)
    if icon_k: draw_icon(board, th, icon_k, X + P(x + 8), Y + P(y + h / 2), 13)
    text(board, (X + P(x + w / 2 + (4 if icon_k else 0)), Y + P(y + h / 2 - 0.3)), msg, 7.8, th['text'])

def popup(board, th, X, Y, x, y, w=150, h=132):
    place(board, chunky(th, w, h, 16, th['panel'], seed=21, gloss=False), X + P(x), Y + P(y))
    d = ImageDraw.Draw(board)
    if th['key'] == 'B':
        # stitched inner border
        x0, y0, x1, y1 = X + P(x + 4.5), Y + P(y + 4.5), X + P(x + w - 4.5), Y + P(y + h - 4.5)
        pts = rr_points(x0, y0, x1, y1, P(12), 0)
        for i in range(0, len(pts) - 1, 3):
            d.line([pts[i], pts[i + 1]], fill=th['title'][1], width=P(0.7))
        # washi tape
        for (tx, ang, c) in [(x + 2, 32, hx('#FFC9D6', 200)), (x + w - 22, -30, hx('#BFE6FF', 200))]:
            tape = Image.new('RGBA', (P(26), P(8)), c)
            td = ImageDraw.Draw(tape)
            for k in range(0, P(26), P(3)): td.line([(k, 0), (k, P(8))], fill=hx('#FFFFFF', 60), width=P(1))
            tape = tape.rotate(ang, expand=True, resample=Image.BICUBIC)
            board.alpha_composite(tape, (X + P(tx) - P(2), Y + P(y - 6)))
        place(board, tag_shape(th, 78, 18, th['title'], seed=2), X + P(x + (w - 78) / 2), Y + P(y - 8), -2)
        text(board, (X + P(x + w / 2 + 3), Y + P(y + 0.8)), '今日委託', 9.5, hx('#FFFFFF'), stroke=1.0, stroke_col=mix(th['title'][1], hx('#000000'), .35))
    else:
        place(board, chunky(th, 84, 20, 10, th['title'], seed=2), X + P(x + (w - 84) / 2), Y + P(y - 9))
        text(board, (X + P(x + w / 2), Y + P(y + 0.6)), '今日委託', 10, hx('#FFFFFF'), stroke=1.1, stroke_col=mix(th['title'][1], hx('#000000'), .4))
        for (sx, sy, s) in [(x + 22, y - 3, 1.6), (x + w - 26, y - 6, 1.2)]:
            d.polygon([(X + P(sx + px * s), Y + P(sy + py * s)) for px, py in star_pts(0, 0, 3, 1.2, 4, -90)], fill=hx('#FFD86B'))
    # close ✕ inside top-right
    cx, cy = x + w - 13, y + 13
    place(board, chunky(th, 15, 15, 7.5, (hx('#FFB2C2'), hx('#FF7E99')) if th['key'] == 'A' else (hx('#FFCFD8'), hx('#FF98AB')), seed=8), X + P(cx - 7.5), Y + P(cy - 7.5))
    for s in (1, -1):
        d.line([(X + P(cx - 3), Y + P(cy - 3 * s)), (X + P(cx + 3), Y + P(cy + 3 * s))], fill=hx('#FFFFFF'), width=P(1.9))
        for (ex, ey) in [(cx - 3, cy - 3 * s), (cx + 3, cy + 3 * s)]:
            d.ellipse([X + P(ex - .95), Y + P(ey - .95), X + P(ex + .95), Y + P(ey + .95)], fill=hx('#FFFFFF'))
    rows = [('play', '陪佢玩 2 次', '1/2', 0.5, '+4'), ('feed', '餵佢食嘢', '完成！', 1.0, '+4'), ('clean', '幫佢沖涼', '0/1', 0.0, '+4')]
    for i, (k, lab, prog, v, rw) in enumerate(rows):
        ry = y + 22 + i * 26
        place(board, chunky(th, w - 16, 22, 8, th['inset'], seed=30 + i, gloss=False, shadow=False, ow=th['ow'] * .6, sticker=0), X + P(x + 8), Y + P(ry))
        draw_icon(board, th, k, X + P(x + 20), Y + P(ry + 11), 17)
        text(board, (X + P(x + 31), Y + P(ry + 7.5)), lab, 7.4, th['text'], anchor='lm')
        tx0 = x + 31; tw = 56
        d.rounded_rectangle([X + P(tx0), Y + P(ry + 13.5), X + P(tx0 + tw), Y + P(ry + 17)], radius=P(1.75), fill=th['track'])
        if v > 0: d.rounded_rectangle([X + P(tx0), Y + P(ry + 13.5), X + P(tx0 + tw * v), Y + P(ry + 17)], radius=P(1.75), fill=th['sec'][1])
        draw_icon(board, th, 'star', X + P(x + w - 30), Y + P(ry + 11), 13)
        text(board, (X + P(x + w - 17.5), Y + P(ry + 11)), rw, 8.5, th['text'], th['font_num'])
    button(board, th, X, Y, x + (w - 72) / 2, y + h - 30, 72, 21, 'pri', '全部領取', icon_k=None)

def home(th, H, pet_key, bubble):
    sc = scene(H, pet_key).resize((P(195), P(422)), Image.NEAREST)
    b = sc.copy(); X = Y = 0
    # --- top HUD ---
    if th['key'] == 'B':
        place(b, tag_shape(th, 96, 22, th['panel'], seed=1), P(2), P(4), -1.5)
    else:
        place(b, chunky(th, 94, 22, 11, th['panel'], seed=1), P(3), P(4))
    # pet portrait medallion
    place(b, chunky(th, 19, 19, 9.5, th['accent'], seed=3, gloss=True), P(7 if th['key']=='A' else 15), P(5.5))
    pet = load(f'{ROOT}/sprites/tuanrong/species_concept/from_ref/tuned_48/sprites/{pet_key}_48.png')
    bb = pet.getbbox(); head = pet.crop((bb[0], bb[1] + 4, bb[2], bb[1] + 4 + (bb[2] - bb[0]))).resize((P(15), P(15)), Image.NEAREST)
    px0 = 7 if th['key']=='A' else 15
    b.alpha_composite(head, (P(px0 + 2), P(7.5)))
    nx = px0 + 23
    name = {'C1': '火仔', 'A1': '滴滴'}[pet_key]
    text(b, (P(nx), P(11)), name, 9.5, th['text'], anchor='lm')
    text(b, (P(nx + 22), P(11.3)), '幼崽', 6.3, mix(th['text'], hx('#FFFFFF'), .35), anchor='lm')
    d = ImageDraw.Draw(b)
    d.rounded_rectangle([P(nx), P(17.6), P(95), P(20.6)], radius=P(1.5), fill=th['track'])
    d.rounded_rectangle([P(nx), P(17.6), P(nx + (95 - nx) * .62), P(20.6)], radius=P(1.5), fill=th['pri'][1])
    currency_chip(b, th, X, Y, 104, 5, 42, 'light', '140')
    currency_chip(b, th, X, Y, 150, 5, 41, 'star', '10')
    needs = [('feed', .62, (hx('#FFD9A0'), hx('#FFAA55'))), ('heart', .48, (hx('#FFB8CA'), hx('#FF7598'))),
             ('clean', .55, (hx('#BDE8FF'), hx('#5FB8F2'))), ('sleep', .80, (hx('#FFF0A8'), hx('#FFC94A')))]
    for i, (k, v, c) in enumerate(needs):
        need_pill(b, th, X, Y, 3 + i * 47.3, 29.5, 44, k, v, c)
    # floating quest button (replaces '⭐ 委託' chip)
    place(b, chunky(th, 24, 24, 12, th['panel'], seed=6), P(166), P(54))
    draw_icon(b, th, 'gift', P(178), P(65.5), 18)
    red_dot(b, th, P(187), P(56), 3)
    text(b, (P(178), P(83)), '委託', 6.4, hx('#FFFFFF'), stroke=0.9, stroke_col=th['text'])
    toast(b, th, X, Y, 26, 56, 120, '收到小禮物 +5')
    speech(b, th, X, Y, 104, 222, 52, 17, bubble, 'feed')
    # --- bottom: actions + dock ---
    acts = [('feed', '餵食', 'pri'), ('play', '玩耍', 'sec'), ('clean', '清潔', 'sec'), ('sleep', '瞓覺', 'sec')]
    fills = [th['pri'], th['sec'], (hx('#BDE8FF'), hx('#7CC6F5')), (hx('#D7C8FF'), hx('#A88DF0'))] if th['key'] == 'A' else \
            [th['pri'], (hx('#C9F0D8'), hx('#93D9AE')), th['sec'], th['title']]
    for i, (k, lab, _) in enumerate(acts):
        x = 6 + i * 46.5; y = 314
        comp = chunky(th, 40, 38, 14, fills[i], seed=40 + i)
        place(b, comp, P(x), P(y), th['acts_tilt'][i])
        draw_icon(b, th, k, P(x + 20), P(y + 15), 22)
        text(b, (P(x + 20), P(y + 31.5)), lab, 7.2, hx('#FFFFFF'), stroke=1.0, stroke_col=mix(fills[i][1], hx('#000000'), .4))
    dock(b, th, X, Y, 2, 368, 191, active=0, dot=2)
    return b

def board(th, H, pet_key, bubble):
    W, Hh = 1760, 1520
    bg = grad((P(W / 3), P(Hh / 3)), *th['bg'])
    bd = bg.copy()
    d = ImageDraw.Draw(bd)
    # polka dots
    if th['key'] == 'B':
        for gx in range(0, bd.width, P(8)): d.line([(gx, 0), (gx, bd.height)], fill=hx('#B9A8E0', 45), width=2)
        for gy in range(0, bd.height, P(8)): d.line([(0, gy), (bd.width, gy)], fill=hx('#B9A8E0', 45), width=2)
    rng = np.random.default_rng(3 if th['key'] == 'A' else 7)
    for _ in range(140):
        x, y = rng.uniform(0, bd.width), rng.uniform(0, bd.height); r = rng.uniform(P(1), P(3))
        d.ellipse([x - r, y - r, x + r, y + r], fill=hx('#FFFFFF', 120))
    def T(s, x, y, sz, col=th['text'], kind='cjk', anchor='la', **k): text(bd, (P(x / 3), P(y / 3)), s, sz / 3, col, kind, anchor, **k)
    T(f"風格 {th['key']}｜{th['name']}", 30, 22, 46, stroke=0)
    T(th['en'], 30 + 52 * (len(th['name']) + 5), 34, 30, mix(th['text'], hx('#FFFFFF'), .35), 'fred')
    T(th['sub'] + '　（概念參考，未係正式 UI kit）', 32, 82, 21, mix(th['text'], hx('#FFFFFF'), .25))
    # mockup
    mx, my = 30, 130
    hm = home(th, H, pet_key, bubble)
    frame = chunky(th, 195 + 6, 422 + 6, 14, (hx('#FFFFFF'), hx('#FFFFFF')), gloss=False, ow=1.0, wob=0, sticker=0)
    place(bd, frame, P((mx - 9) / 3), P((my - 9) / 3))
    m = mask_poly(hm.size, rr_points(0, 0, hm.width, hm.height, P(12)))
    put(bd, hm, m, (P(mx / 3), P(my / 3)))
    T('主畫面 195×422（×3）・HD-2D 小圃 H3 白天', mx, my + 1266 + 18, 20, mix(th['text'], hx('#FFFFFF'), .3))
    # right column (art coords via /3)
    X0 = 660; Y0 = 150
    def ax(v): return X0 / 3 + v
    def ay(v): return Y0 / 3 + v
    def lab(s, x, y): T(s, x, y, 22, mix(th['text'], hx('#FFFFFF'), .2))
    lab('彈窗（關閉掣喺面板入面右上角）', X0, Y0 - 34)
    popup(bd, th, 0, 0, ax(2), ay(10), 152, 134)
    # buttons grid
    BX = X0 + 540; lab('掣：一般 ／ 撳落（squash＋陰影收細）', BX - 20, Y0 - 34)
    rows = [('pri', '好呀！', '主要'), ('sec', '遲啲先', '次要'), ('dis', '未開放', '停用')]
    for i, (k, l, rn) in enumerate(rows):
        yy = Y0 / 3 + 8 + i * 40
        T(rn, BX - 20, (yy + 7) * 3, 22, th['text'])
        button(bd, th, 0, 0, BX / 3 + 14, yy, 58, 23, k, l, False)
        button(bd, th, 0, 0, BX / 3 + 84, yy, 58, 23, k, l, k != 'dis')
    # round icon buttons
    for i, k in enumerate(['gift', 'book', 'gear']):
        cx = BX / 3 + 22 + i * 30; cy = Y0 / 3 + 130
        place(bd, chunky(th, 24, 24, 12, th['panel'], seed=60 + i), P(cx - 12), P(cy - 12))
        draw_icon(bd, th, k, P(cx), P(cy + 0.5), 18)
    red_dot(bd, th, P(BX / 3 + 22 + 9), P(Y0 / 3 + 120), 2)
    T('圓 icon 掣＋紅點', BX + 290, Y0 + 385, 20, mix(th['text'], hx('#FFFFFF'), .3))
    # dock
    DY = Y0 + 520
    lab('底部 dock：5 分頁（照顧 active 彈高＋紅點）', X0, DY - 40)
    dock(bd, th, 0, 0, X0 / 3 + 2, DY / 3 + 10, 191, 0, 2)
    # need bars large
    NX = X0 + 640
    lab('需要條', NX, DY - 40)
    needs = [('feed', '飽腹', .62, (hx('#FFD9A0'), hx('#FFAA55'))), ('heart', '心情', .48, (hx('#FFB8CA'), hx('#FF7598'))),
             ('clean', '清潔', .55, (hx('#BDE8FF'), hx('#5FB8F2'))), ('sleep', '精力', .85, (hx('#FFF0A8'), hx('#FFC94A')))]
    for i, (k, n, v, c) in enumerate(needs):
        need_pill(bd, th, 0, 0, NX / 3, DY / 3 + 2 + i * 19, 100, k, v, c)
    # icons
    IY = DY + 250
    lab('icon（全部原創、有表情，唔再借 emoji）', X0, IY - 40)
    kinds = [('feed', '餵食'), ('play', '玩耍'), ('clean', '清潔'), ('sleep', '瞓覺'), ('book', '手帳／圖鑑'), ('sprout', '小圃'),
             ('light', '光粒'), ('star', '星星碎'), ('heart', '心情'), ('gear', '設定'), ('gift', '禮物／委託')]
    for i, (k, n) in enumerate(kinds):
        col, row = i % 6, i // 6
        cx = X0 + 80 + col * 165; cy = IY + 60 + row * 160
        draw_icon(bd, th, k, P(cx / 3), P(cy / 3), 28)
        T(n, cx, cy + 66, 20, th['text'], anchor='ma')
    # toast + speech + palette
    TY = IY + 400
    lab('提示 toast ／ 寵物對白', X0, TY - 40)
    toast(bd, th, 0, 0, X0 / 3 + 2, TY / 3 + 4, 120, '收到小禮物 +5')
    speech(bd, th, 0, 0, X0 / 3 + 136, TY / 3 + 2, 60, 18, '肚仔餓…', 'feed')
    PY = TY
    lab('色盤', X0 + 640, PY - 40)
    for i, c in enumerate(th['swatch']):
        cx = X0 + 660 + i * 76; cy = PY + 30
        place(bd, chunky(th, 18, 18, 9, (hx(c), hx(c)), seed=70 + i, gloss=True), P(cx / 3 - 9), P(cy / 3 - 9))
        T(c[1:], cx, cy + 34, 15, th['text'], 'fred', anchor='ma')
    T('字：粗黑體＋白字描邊；數字用 ' + ('Fredoka' if th['key'] == 'A' else 'Baloo 2'), X0, PY + 120, 20, th['text'])
    T('0123456789  +5  140', X0 + 520, PY + 105, 40, th['text'], th['font_num'])
    out = bd.reduce(SS)
    return out, hm.reduce(SS)

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    a, ha = board(A, 'H3', 'C1', '肚仔餓…')
    a.convert('RGB').save(f'{OUT}/board_A_3x.png', optimize=True)
    b, hb = board(B, 'H3', 'A1', '肚仔餓…')
    b.convert('RGB').save(f'{OUT}/board_B_3x.png', optimize=True)
    ha.save(f'{OUT}/home_A_3x.png'); hb.save(f'{OUT}/home_B_3x.png')
    cur = Image.open('/workspace/bundles/audit/mid-h13-main.png').convert('RGBA').resize((585, 1266), Image.LANCZOS)
    W = 30 + (585 + 30) * 3; Hh = 1266 + 170
    ba = grad((W, Hh), hx('#FFF6EE'), hx('#F3EEFF'))
    for i, (im, t) in enumerate([(cur, '而家（現行 build）'), (ha, 'A｜棉花糖奶油'), (hb, 'B｜繪本貼紙')]):
        x = 30 + i * 615
        ImageDraw.Draw(ba).rounded_rectangle([x - 6, 104, x + 591, 110 + 1266 + 6], radius=40, fill=hx('#FFFFFF'), outline=hx('#5B3A35', 120), width=3)
        m = mask_poly(im.size, rr_points(0, 0, 585, 1266, 34))
        put(ba, im, m, (x, 110))
        ImageDraw.Draw(ba).text((x + 292, 52), t, font=ImageFont.truetype(CJK, 44, index=4), fill=hx('#5B3A35'), anchor='mm')
    ImageDraw.Draw(ba).text((W // 2, Hh - 30), '同一個場景（H3 白天）、同一個位置排版；A／B 只係風格參考，未批正式 UI kit', font=ImageFont.truetype(CJK, 26, index=4), fill=hx('#8A6A62'), anchor='mm')
    ba.convert('RGB').save(f'{OUT}/before_after_3x.png', optimize=True)
    print('ok')
