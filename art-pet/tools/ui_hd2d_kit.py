# 《微光小圃》UI HD-2D 風格（概念比較稿）— 純 Pillow/numpy 程序繪製，無 AI。
# 金邊玻璃面板・寶石掣・內發光・烘焙 bloom・景深；icon 沿用 B2 小動物（有表情）再加金框光暈。
import importlib.util, math, os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

_here = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location('uiv2', os.path.join(_here, 'ui_v2_kit.py'))
v2 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(v2)
k = v2.k
P, hx, mix, put, solid, grad = k.P, k.hx, k.mix, k.put, k.solid, k.grad
ROOT = k.ROOT
OUT = f'{ROOT}/ui/style_ref/hd2d'
U = k.U

# ---------------- palette ----------------
C = dict(
    navy=(hx('#34427C', 236), hx('#181D3C', 242)), navy_in=(hx('#222A52', 235), hx('#141834', 240)),
    paper=(hx('#FFF9EA'), hx('#F4E4C4')),
    pri=(hx('#FFE29A'), hx('#F28B3E')), sec=(hx('#A8F0E6'), hx('#3797B4')), rose=(hx('#FFB4C8'), hx('#E2577F')),
    dis=(hx('#8C92AE'), hx('#565C7A')), gem=(hx('#FFB0BE'), hx('#E43A62')), violet=(hx('#D6C2FF'), hx('#7A5CD6')),
    g_hi=hx('#FFF6CF'), g_mid=hx('#EDBE62'), g_lo=hx('#9C6630'), line=hx('#24172C'),
    glow=hx('#FFDC8C'), cyan=hx('#A6F4FF'), cream=hx('#FFF5DC'), ink=hx('#3A2840'), dim=hx('#141A36'),
    track=(hx('#0E1128'), hx('#262C52')), red=hx('#FF4D6D'))
SWATCH = ['#34427C', '#181D3C', '#EDBE62', '#FFF6CF', '#F28B3E', '#3797B4', '#E2577F', '#FFF5DC', '#A6F4FF']

CJK_SANS = k.CJK
CJK_SERIF = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
CINZEL = '/usr/share/fonts/truetype/sand-box/google/Cinzel/Cinzel-VariableFont_wght.ttf'
_fc = {}
def font(kind, size_art, scale=None):
    px = int(round(size_art * (U if scale is None else scale))); key = (kind, px)
    if key not in _fc:
        if kind == 'serif': f = ImageFont.truetype(CJK_SERIF, px, index=4)
        elif kind == 'sans': f = ImageFont.truetype(CJK_SANS, px, index=4)
        elif kind == 'cin':
            f = ImageFont.truetype(CINZEL, px); f.set_variation_by_axes([900])
        else:
            f = ImageFont.truetype(k.FRED, px); f.set_variation_by_axes([700, 100])
        _fc[key] = f
    return _fc[key]

def gauss(m, r): return m.filter(ImageFilter.GaussianBlur(r)) if r > 0 else m
def amul(m, a): return m.point(lambda v: int(v * a))
def vgrad(size, stops):
    """multi-stop vertical gradient; stops = [(t, rgba), ...]"""
    w, h = size; t = np.linspace(0, 1, h)
    out = np.zeros((h, 4))
    ts = [s[0] for s in stops]; cs = np.array([s[1] for s in stops], float)
    for c in range(4): out[:, c] = np.interp(t, ts, cs[:, c])
    a = np.repeat(out[:, None, :], w, axis=1)
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')
def gold_grad(size): return vgrad(size, [(0, C['g_hi']), (0.45, C['g_mid']), (1, C['g_lo'])])

def rrm(W, H, x0, y0, x1, y1, r):
    return k.mask_poly((W, H), k.rr_points(x0, y0, x1, y1, max(1, r), 0))

def outline_pts(img, pts, col, width):
    d = ImageDraw.Draw(img); d.line(pts + [pts[0]], fill=col, width=width, joint='curve')

# ---------------- frame: the core HD-2D element ----------------
def frame(w, h, r, style='panel', pressed=False, glow=1.0, ornate=None, rim=1.2):
    """returns (img, ox, oy) like k.chunky (SS px)."""
    pad = P(9); W, H = P(w) + pad * 2, P(h) + pad * 2
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    def m(e): return rrm(W, H, pad - P(e), pad - P(e), pad + P(w) + P(e), pad + P(h) + P(e), P(r + e))
    m_dark, m_gold, m_in = m(rim + 0.55), m(rim), m(0)
    if isinstance(style, str): fill = C['navy'] if style == 'panel' else C[style]
    else:
        fill = style
        style = 'panel' if fill is C['navy'] else 'navy_in' if fill is C['navy_in'] else 'paper' if fill is C['paper'] else 'btn'
    gcol = C['glow'] if style in ('panel', 'paper', 'navy_in') else mix(fill[0], C['glow'], .4)
    # outer bloom halo
    if glow > 0:
        g = amul(gauss(m_dark, P(2.6 if not pressed else 1.4)), 0.55 * glow * (0.5 if pressed else 1))
        put(img, solid((W, H), gcol), g)
    # drop shadow (depth)
    dy = P(0.6 if pressed else 1.8)
    sh = Image.new('L', (W, H), 0); sh.paste(m_dark, (0, dy)); sh = gauss(sh, P(1.3))
    put(img, solid((W, H), hx('#080A1C', 150)), sh)
    put(img, solid((W, H), C['line']), m_dark)
    put(img, gold_grad((W, H)) if not pressed else vgrad((W, H), [(0, C['g_mid']), (1, C['g_lo'])]), m_gold)
    # top bevel highlight on the gold
    bev = ImageChops.subtract(m_gold, ImageChops.offset(m_gold, 0, P(0.45)))
    put(img, solid((W, H), hx('#FFFFFF', 210)), bev)
    put(img, solid((W, H), C['line']), m(0.35))
    c0, c1 = fill
    if pressed: c0, c1 = mix(c0, c1, .55), mix(c1, hx('#000000', c1[3]), .12)
    put(img, vgrad((W, H), [(0, c0), (1, c1)]), m_in)
    # lattice pattern on glass panels
    if style in ('panel', 'navy_in'):
        pat = Image.new('L', (W, H), 0); pd = ImageDraw.Draw(pat); s = P(7)
        for x in range(-H, W + H, s):
            pd.line([(x, 0), (x + H, H)], fill=16, width=max(1, P(0.25)))
            pd.line([(x, H), (x + H, 0)], fill=16, width=max(1, P(0.25)))
        put(img, solid((W, H), C['glow']), ImageChops.multiply(pat, m_in))
    # inner rim glow (light caught on the edge)
    er = gauss(m_in, P(1.6)); edge = ImageChops.subtract(m_in, er)
    put(img, solid((W, H), mix(c0, hx('#FFFFFF'), .5) if style not in ('panel', 'navy_in') else C['glow']), amul(edge, 0.55 if style in ('panel', 'navy_in') else 0.8))
    # glass sheen
    if not pressed:
        gh = min(h * 0.46, 22)
        sm = rrm(W, H, pad + P(1.5), pad + P(1.0), pad + P(w) - P(1.5), pad + P(gh), P(min(r, gh / 2)))
        sm = ImageChops.multiply(sm, m_in)
        a0 = 120 if style not in ('panel', 'navy_in') else 46
        put(img, vgrad((W, H), [(0, hx('#FFFFFF', a0)), (gh / (h + 18) * 1.0 + pad / H, hx('#FFFFFF', 0)), (1, hx('#FFFFFF', 0))]), sm)
    # inner gold hairline
    if style in ('panel', 'paper', 'navy_in') and min(w, h) > 26:
        pts = k.rr_points(pad + P(2.4), pad + P(2.4), pad + P(w - 2.4), pad + P(h - 2.4), P(max(1, r - 2.4)), 0)
        outline_pts(img, pts, hx('#F2C46A', 150), max(1, P(0.35)))
    if ornate is None: ornate = style in ('panel', 'paper') and min(w, h) > 40
    if ornate:
        for (cx, cy) in [(pad + P(2.2), pad + P(2.2)), (pad + P(w - 2.2), pad + P(2.2)), (pad + P(2.2), pad + P(h - 2.2)), (pad + P(w - 2.2), pad + P(h - 2.2))]:
            gem(img, cx, cy, 2.6, C['sec'])
    return img, pad, pad

def gem(img, cx, cy, R, fill=None, glow=True, star=True):
    """4-point gold star with a jewel at the centre (SS coords, R art units)."""
    fill = fill or C['sec']; W, H = img.size
    if glow:
        g = Image.new('L', (W, H), 0); ImageDraw.Draw(g).ellipse([cx - P(R * 1.6), cy - P(R * 1.6), cx + P(R * 1.6), cy + P(R * 1.6)], fill=150)
        put(img, solid((W, H), C['glow']), gauss(g, P(R * 0.7)))
    d = ImageDraw.Draw(img)
    if star:
        pts = [(cx + P(R * (1.25 if i % 2 == 0 else .38)) * math.cos(math.radians(-90 + i * 45)), cy + P(R * (1.25 if i % 2 == 0 else .38)) * math.sin(math.radians(-90 + i * 45))) for i in range(8)]
        d.polygon([(x, y) for x, y in pts], fill=C['line'])
        pts2 = [(cx + P(R * (1.0 if i % 2 == 0 else .3)) * math.cos(math.radians(-90 + i * 45)), cy + P(R * (1.0 if i % 2 == 0 else .3)) * math.sin(math.radians(-90 + i * 45))) for i in range(8)]
        d.polygon(pts2, fill=C['g_mid'])
    rr = P(R * 0.48)
    d.ellipse([cx - rr - P(.25), cy - rr - P(.25), cx + rr + P(.25), cy + rr + P(.25)], fill=C['line'])
    d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=fill[1])
    d.ellipse([cx - rr * .6, cy - rr * .7, cx + rr * .1, cy - rr * .05], fill=fill[0])
    d.ellipse([cx - rr * .45, cy - rr * .55, cx - rr * .1, cy - rr * .25], fill=hx('#FFFFFF', 230))

def place(board, comp, x, y, angle=0): k.place(board, comp, x, y, angle)

# ---------------- text ----------------
def text(board, xy, s, size, color=None, kind='sans', anchor='mm', stroke=0.9, stroke_col=None, glow=0.0):
    color = C['cream'] if color is None else color
    stroke_col = hx('#1A1230') if stroke_col is None else stroke_col
    f = font(kind, size)
    if glow:
        L = Image.new('L', board.size, 0)
        ImageDraw.Draw(L).text(xy, s, font=f, fill=255, anchor=anchor, stroke_width=P(stroke + 0.6))
        put(board, solid(board.size, C['glow']), amul(gauss(L, P(1.4)), glow))
    ImageDraw.Draw(board).text(xy, s, font=f, fill=color, anchor=anchor, stroke_width=P(stroke) if stroke else 0, stroke_fill=stroke_col)

def gold_text(board, xy, s, size, kind='cin', anchor='mm', glow=0.6, stroke=1.0, fill=None):
    """gradient-filled number/text with dark rim + bloom"""
    f = font(kind, size)
    W, H = board.size
    L = Image.new('L', (W, H), 0); ImageDraw.Draw(L).text(xy, s, font=f, fill=255, anchor=anchor)
    bb = L.getbbox()
    if not bb: return
    Ls = Image.new('L', (W, H), 0); ImageDraw.Draw(Ls).text(xy, s, font=f, fill=255, anchor=anchor, stroke_width=P(stroke))
    if glow: put(board, solid((W, H), C['glow']), amul(gauss(Ls, P(1.5)), glow))
    put(board, solid((W, H), C['line']), Ls)
    g = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    stops = fill or [(0, C['g_hi']), (0.5, hx('#FFE08A')), (1, hx('#E59A3E'))]
    gg = vgrad((W, bb[3] - bb[1] + 2), stops); g.paste(gg, (0, bb[1]))
    put(board, g, L)
    hl = ImageChops.subtract(L, ImageChops.offset(L, 0, P(0.5)))
    put(board, solid((W, H), hx('#FFFFFF', 200)), hl)

# ---------------- icons (B2 cute animals, HD finish: gold rim + halo) ----------------
HD_TH = dict(v2.B2); HD_TH.update(key='H', ol=hx('#3A2840'), ow=0.95, sticker=0, shadow=hx('#080A1C', 120))
_IC = {}
def icon_raw(kind):
    if kind not in _IC:
        base = k.icon(HD_TH, kind)
        a = base.getchannel('A').point(lambda v: 255 if v > 90 else int(v * 2.8))
        W, H = base.size
        ring = k.dilate(a, P(0.75)); outer = k.dilate(ring, P(0.55))
        out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        put(out, solid((W, H), C['glow']), amul(gauss(outer, P(1.6)), 0.6))
        put(out, solid((W, H), C['line']), outer)
        put(out, gold_grad((W, H)), ring)
        out.alpha_composite(base)
        # cool rim light from top-left (HD-2D key light)
        rim = ImageChops.subtract(a, ImageChops.offset(a, P(0.7), P(0.7)))
        put(out, solid((W, H), hx('#FFFFFF', 140)), rim)
        _IC[kind] = out
    return _IC[kind]
def icon(board, kind, cx, cy, size_art):
    im = icon_raw(kind); px = P(size_art * (k.ICN + 6) / k.ICN)
    im = im.resize((px, px), Image.LANCZOS)
    board.alpha_composite(im, (int(cx - px / 2), int(cy - px / 2)))

def medallion(board, cx, cy, d, fill=None, kind=None, isz=None, pressed=False, glow=1.0):
    fill = fill or C['navy']
    comp = frame(d, d, d / 2, fill, pressed=pressed, glow=glow, ornate=False, rim=1.1)
    place(board, comp, cx - P(d / 2), cy - P(d / 2) + (P(0.9) if pressed else 0))
    if kind: icon(board, kind, cx, cy + (P(0.9) if pressed else 0), isz or d * 0.78)

# ---------------- widgets (art coords -> SS by P) ----------------
def red_dot(board, cx, cy, n=None):
    """ruby gem badge"""
    R = 3.9 if n else 2.9
    W, H = board.size
    g = Image.new('L', (W, H), 0); ImageDraw.Draw(g).ellipse([cx - P(R + 2.2), cy - P(R + 2.2), cx + P(R + 2.2), cy + P(R + 2.2)], fill=200)
    put(board, solid((W, H), hx('#FF7A90')), gauss(g, P(1.5)))
    d = ImageDraw.Draw(board)
    for rr, col in [(R + 1.25, C['line']), (R + 0.85, C['g_mid']), (R + 0.2, C['line'])]:
        d.ellipse([cx - P(rr), cy - P(rr), cx + P(rr), cy + P(rr)], fill=col)
    gem_l = vgrad((P(R * 2) + 1, P(R * 2) + 1), [(0, hx('#FF9AAE')), (1, hx('#C8204A'))])
    mk = Image.new('L', gem_l.size, 0); ImageDraw.Draw(mk).ellipse([0, 0, gem_l.width - 1, gem_l.height - 1], fill=255)
    gem_l.putalpha(mk); board.alpha_composite(gem_l, (int(cx - P(R)), int(cy - P(R))))
    d.ellipse([cx - P(R * .62), cy - P(R * .72), cx - P(R * .02), cy - P(R * .28)], fill=hx('#FFFFFF', 210))
    if n: text(board, (cx, cy + P(0.15)), str(n), 6.0, hx('#FFFFFF'), 'fred', stroke=0.7, stroke_col=hx('#6A0A24'))

def button(board, x, y, w, h, kind, label, pressed=False, icon_k=None):
    fill = C[kind]
    comp = frame(w, h, min(h / 2, 8), fill, pressed=pressed, glow=0 if kind == 'dis' else 1.0, ornate=False, rim=1.1)
    dy = 1.1 if pressed else 0
    place(board, comp, P(x), P(y + dy))
    tc = hx('#FFFFFF') if kind != 'dis' else hx('#C9CCDB')
    sc = mix(fill[1], hx('#000000'), .45)
    cx = x + w / 2 + (5 if icon_k else 0)
    if icon_k: icon(board, icon_k, P(x + 10), P(y + h / 2 + dy), 14)
    text(board, (P(cx), P(y + h / 2 + dy - 0.3)), label, 8.4, tc, 'serif', stroke=1.0, stroke_col=sc)
    if kind != 'dis' and not pressed:
        for (sx, sy) in [(x + 4.5, y + 3.2)]: gem(board, P(sx), P(sy), 1.6, C['sec'], glow=True, star=True)

def need_bar(board, x, y, w, kind, val, col):
    h = 12
    place(board, frame(w, h, h / 2, C['navy_in'], glow=0.4, ornate=False, rim=0.8), P(x), P(y))
    tx0, tx1 = x + 11, x + w - 2.6
    d = ImageDraw.Draw(board)
    d.rounded_rectangle([P(tx0), P(y + 3.6), P(tx1), P(y + 8.4)], radius=P(2.4), fill=hx('#0B0E24'))
    fw = max(4.8, (tx1 - tx0) * val)
    W, H = board.size
    seg = vgrad((P(fw), P(4.2)), [(0, mix(col[0], hx('#FFFFFF'), .35)), (0.5, col[0]), (1, col[1])])
    mk = Image.new('L', seg.size, 0); ImageDraw.Draw(mk).rounded_rectangle([0, 0, seg.width - 1, seg.height - 1], radius=P(2.1), fill=255)
    seg.putalpha(mk); board.alpha_composite(seg, (P(tx0 + .3), P(y + 3.9)))
    # glowing tip
    g = Image.new('L', (W, H), 0); ImageDraw.Draw(g).ellipse([P(tx0 + fw - 2.6), P(y + 3.0), P(tx0 + fw + 1.0), P(y + 9.0)], fill=230)
    put(board, solid((W, H), mix(col[0], hx('#FFFFFF'), .6)), gauss(g, P(1.0)))
    medallion(board, P(x + 4.6), P(y + h / 2), 13.2, C['navy'], kind, 12.5, glow=0.5)

def chip(board, x, y, w, kind, val):
    h = 16
    place(board, frame(w, h, h / 2, C['navy'], glow=0.6, ornate=False, rim=1.0), P(x), P(y))
    icon(board, kind, P(x + 3), P(y + h / 2), 17)
    gold_text(board, (P(x + w / 2 + 6), P(y + h / 2 + 0.2)), str(val), 9.6, 'cin')
    # "+" tab
    medallion(board, P(x + w - 0.5), P(y + h / 2), 8, C['pri'], glow=0.4)
    text(board, (P(x + w - 0.5), P(y + h / 2 - 0.2)), '+', 6.6, hx('#FFFFFF'), 'fred', stroke=0.6, stroke_col=hx('#7A3A10'))

def plaque(board, cx, y, w, label, fill=None, size=9.2):
    """title ribbon with gem crest + swallow tails"""
    fill = fill or C['violet']; h = 17
    W, H = board.size
    for sx in (-1, 1):   # tails
        tl = Image.new('L', (W, H), 0); td = ImageDraw.Draw(tl)
        x0 = cx + sx * (w / 2 - 4); x1 = cx + sx * (w / 2 + 9)
        pts = [(P(x0), P(y + 4)), (P(x1), P(y + 4)), (P(x1 - sx * 3.5), P(y + 9.5)), (P(x1), P(y + 15)), (P(x0), P(y + 15))]
        td.polygon(pts, fill=255)
        put(board, solid((W, H), C['line']), k.dilate(tl, P(0.7)))
        put(board, vgrad((W, H), [(0, mix(fill[1], hx('#000000'), .2)), (1, mix(fill[1], hx('#000000'), .45))]), tl)
    place(board, frame(w, h, 6, fill, glow=1.0, ornate=False, rim=1.1), P(cx - w / 2), P(y))
    gem(board, P(cx), P(y - 1.0), 3.0, C['gem'])
    text(board, (P(cx), P(y + h / 2 + 0.6)), label, size, hx('#FFFFFF'), 'serif', stroke=1.1, stroke_col=mix(fill[1], hx('#000000'), .55), glow=0.35)

def close_btn(board, cx, cy, d=15):
    medallion(board, cx, cy, d, C['rose'], glow=0.8)
    dd = ImageDraw.Draw(board)
    for s in (1, -1):
        dd.line([(cx - P(2.7), cy - P(2.7 * s)), (cx + P(2.7), cy + P(2.7 * s))], fill=hx('#5A0F2A'), width=P(2.6))
    for s in (1, -1):
        dd.line([(cx - P(2.7), cy - P(2.7 * s)), (cx + P(2.7), cy + P(2.7 * s))], fill=hx('#FFFFFF'), width=P(1.5))

def toggle(board, x, y, on=True):
    w, h = 26, 13
    place(board, frame(w, h, h / 2, C['sec'] if on else C['navy_in'], glow=0.6 if on else 0.2, ornate=False, rim=0.9), P(x), P(y))
    kx = x + (w - 6.5 if on else 6.5)
    medallion(board, P(kx), P(y + h / 2), 11, C['paper'], glow=0.5)
    gem(board, P(kx), P(y + h / 2), 1.8, C['pri'] if on else C['dis'], glow=False, star=False)

def toast(board, x, y, w, msg, kind='light'):
    h = 18
    W, H = board.size
    # light streaks behind (banner feel)
    for sx in (-1, 1):
        g = Image.new('L', (W, H), 0); ImageDraw.Draw(g).polygon([(P(x + w / 2 + sx * w * .3), P(y + 6)), (P(x + w / 2 + sx * (w * .5 + 22)), P(y + h / 2)), (P(x + w / 2 + sx * w * .3), P(y + 12))], fill=180)
        put(board, solid((W, H), C['glow']), gauss(g, P(1.2)))
    place(board, frame(w, h, h / 2, C['navy'], glow=1.2, ornate=False, rim=1.1), P(x), P(y))
    medallion(board, P(x + 4), P(y + h / 2), 19, C['pri'], kind, 15)
    text(board, (P(x + w / 2 + 6), P(y + h / 2 - 0.2)), msg, 8.0, C['cream'], 'sans', stroke=0.9)

def speech(board, x, y, w, h, msg, kind=None):
    W, H = board.size
    comp = frame(w, h, h / 2, C['paper'], glow=0.7, ornate=False, rim=0.9)
    img, ox, oy = comp; d = ImageDraw.Draw(img)
    tx = ox + P(9)
    d.polygon([(tx - P(1.6), oy + P(h - 1)), (tx + P(8.6), oy + P(h - 1)), (tx - P(1.6), oy + P(h + 7.6))], fill=C['line'])
    d.polygon([(tx - P(0.6), oy + P(h - 1.6)), (tx + P(7.0), oy + P(h - 1.6)), (tx - P(0.6), oy + P(h + 6.0))], fill=C['g_mid'])
    d.polygon([(tx + P(0.4), oy + P(h - 2.2)), (tx + P(5.4), oy + P(h - 2.2)), (tx + P(0.4), oy + P(h + 4.0))], fill=C['paper'][1])
    place(board, comp, P(x), P(y))
    if kind: icon(board, kind, P(x + 8), P(y + h / 2), 12)
    text(board, (P(x + w / 2 + (4 if kind else 0)), P(y + h / 2 - 0.3)), msg, 7.6, C['ink'], 'sans', stroke=0)

def card(board, x, y, w, h, kind, label, sub=None, locked=False):
    place(board, frame(w, h, 6, C['navy_in'] if not locked else (hx('#3A3F62', 235), hx('#23263E', 240)), glow=0.5 if not locked else 0.15, ornate=False, rim=1.0), P(x), P(y))
    W, H = board.size
    g = Image.new('L', (W, H), 0); ImageDraw.Draw(g).ellipse([P(x + w / 2 - 12), P(y + 4), P(x + w / 2 + 12), P(y + 28)], fill=170)
    put(board, solid((W, H), C['cyan'] if not locked else hx('#6A7090')), amul(gauss(g, P(3)), 1 if not locked else .5))
    if locked:
        gold_text(board, (P(x + w / 2), P(y + 16)), '?', 13, 'cin', glow=0.2, fill=[(0, hx('#C9CEE6')), (1, hx('#7D84A0'))])
    else:
        icon(board, kind, P(x + w / 2), P(y + 16), 20)
    text(board, (P(x + w / 2), P(y + h - 8)), label, 6.6, C['cream'] if not locked else hx('#E2E4EE'), 'sans', stroke=0.8)

# ---------------- scene (layered so we can parallax) ----------------
H3 = f'{ROOT}/scenes/hd2d/H3'
def _ld(p): return Image.open(p).convert('RGBA')
def scene_layers(pet_key='A1', frame_i=0):
    g = json.load(open(f'{H3}/grade.json'))
    lm = np.asarray(Image.open(f'{H3}/lightmap.png').convert('RGB')).astype(float) / 255
    la = np.asarray(Image.open(f'{H3}/light_add.png').convert('RGB')).astype(float)
    eb = np.asarray(Image.open(f'{H3}/emissive_blur.png').convert('RGB')).astype(float)
    pet = _ld(f'{ROOT}/sprites/tuanrong/species_concept/from_ref/tuned_48/idle/{pet_key}_idle.png').crop((48 * frame_i, 0, 48 * frame_i + 48, 48))
    pa = np.asarray(pet).astype(float)
    pa[..., :3] *= np.array(hx(g['petTint'])[:3]) / 255 * np.array(hx(g['ambientTint'])[:3]) / 255
    pet = Image.fromarray(pa.clip(0, 255).astype(np.uint8), 'RGBA')
    out = {}
    for L in ['sky', 'far', 'mid', 'fore']:
        im = _ld(f'{H3}/{L}.png')
        if L == 'mid':
            fx, fy = 97 + 14, 292 + 12
            sh = Image.new('RGBA', im.size); ImageDraw.Draw(sh).ellipse([fx - 13, fy - 3, fx + 13, fy + 2], fill=(30, 40, 30, 70))
            im.alpha_composite(sh); im.alpha_composite(pet, (fx - 24, fy - 45))
        a = np.asarray(im).astype(float)
        a[..., :3] = a[..., :3] * lm + la + eb * g['bloom']['intensity']
        out[L] = Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')
    out['grade'] = g
    return out

def scene_compose(layers, offs=None, zoom=None):
    """offs: dict layer->(dx,dy) in art px (float ok); returns 195x422 RGBA at 1x"""
    offs = offs or {}; zoom = zoom or {}
    img = Image.new('RGBA', (195, 422), (0, 0, 0, 255))
    for L in ['sky', 'far', 'mid', 'fore']:
        im = layers[L]; dx, dy = offs.get(L, (0, 0)); z = zoom.get(L, 1.0)
        if z != 1.0:
            W, H = im.size; nw, nh = int(round(W * z)), int(round(H * z))
            im2 = im.resize((nw, nh), Image.BICUBIC)
            ox = (nw - W) / 2 + (97 + 14) * (z - 1) - (nw - W) / 2; oy = (H * 0) + (292 + 12) * (z - 1)
            ox0, oy0 = (97 + 14) * (z - 1), (292 + 12) * (z - 1)   # zoom about pet pivot
            im = im2.crop((int(ox0), int(oy0), int(ox0) + W, int(oy0) + H))
        x0, y0 = 14 - dx, 12 - dy
        cropped = im.transform((195, 422), Image.AFFINE, (1, 0, x0, 0, 1, y0), resample=Image.BILINEAR)
        img.alpha_composite(cropped)
    g = layers['grade']
    a = np.asarray(img).astype(float)
    fc = np.array(hx(g['fog']['color'])[:3], float); fd = g['fog']['density']
    a[..., :3] = a[..., :3] * (1 - fd) + fc * fd
    v = np.asarray(_ld(f'{H3}/vignette.png')).astype(float); va = v[..., 3:4] / 255
    a[..., :3] = a[..., :3] * (1 - va) + v[..., :3] * va; a[..., 3] = 255
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')

# ---------------- baked bloom ----------------
def bloom(img, thr=0.80, radius=3.0, strength=0.55, tint=None):
    a = np.asarray(img).astype(float) / 255
    lum = (a[..., 0] * .3 + a[..., 1] * .55 + a[..., 2] * .15) * a[..., 3]
    m = np.clip((lum - thr) / (1 - thr), 0, 1)
    br = np.zeros_like(a); br[..., :3] = a[..., :3] * m[..., None]; br[..., 3] = m
    bi = Image.fromarray((br * 255).astype(np.uint8), 'RGBA').filter(ImageFilter.GaussianBlur(P(radius)))
    b = np.asarray(bi).astype(float) / 255
    tint = np.array((tint or hx('#FFE6B0'))[:3], float) / 255
    out = a.copy()
    add = b[..., :3] * b[..., 3:4] * tint * strength
    out[..., :3] = np.clip(out[..., :3] + add, 0, 1)
    out[..., 3] = np.clip(np.maximum(out[..., 3], b[..., 3] * strength * 0.8), 0, 1)
    return Image.fromarray((out * 255).astype(np.uint8), 'RGBA')

# ---------------- screen pieces ----------------
TABS = [('heart_bunny', '照顧'), ('play_cat', '玩'), ('sprout', '小圃'), ('book_bear', '手帳'), ('gear_chick', '設定')]
DOCK = dict(x=3, y=370, w=189, h=46)
def tab_cx(i): return DOCK['x'] + DOCK['w'] / 5 * (i + .5)
def dock(board, active=0, dot=2, act_glow=1.0, act_lift=1.0):
    x, y, w, h = DOCK['x'], DOCK['y'], DOCK['w'], DOCK['h']
    place(board, frame(w, h, 14, C['navy'], glow=1.0, ornate=True), P(x), P(y))
    d = ImageDraw.Draw(board)
    for i in range(1, 5):   # gold dividers with tiny gem
        dx = x + w / 5 * i
        d.line([(P(dx), P(y + 9)), (P(dx), P(y + h - 9))], fill=hx('#F2C46A', 90), width=P(0.4))
    for i, (kd, lab) in enumerate(TABS):
        cx = tab_cx(i)
        if i == active:
            W, H = board.size
            # light pillar + halo
            g = Image.new('L', (W, H), 0); gd = ImageDraw.Draw(g)
            gd.rounded_rectangle([P(cx - 13), P(y - 14), P(cx + 13), P(y + h - 4)], radius=P(12), fill=int(150 * act_glow))
            put(board, solid((W, H), C['glow']), gauss(g, P(4)))
            ly = y - 7 * act_lift
            medallion(board, P(cx), P(ly + 13), 30, C['pri'], kd, 24, glow=1.4 * act_glow)
            text(board, (P(cx), P(y + 33)), lab, 7.6, hx('#FFFFFF'), 'serif', stroke=1.0, stroke_col=hx('#6A3410'), glow=0.6 * act_glow)
            gem(board, P(cx), P(y + h - 4.2), 2.0, C['gem'], glow=True)
        else:
            medallion(board, P(cx), P(y + 17), 22, C['navy_in'], kd, 18, glow=0.25)
            text(board, (P(cx), P(y + 35)), lab, 6.8, hx('#E9DEC4'), 'sans', stroke=0.8)
        if i == dot and i != active: red_dot(board, P(cx + 8.5), P(y + 8), 1)

ACTS = [('feed', '餵食', 'pri'), ('play_cat', '玩耍', 'rose'), ('clean', '清潔', 'sec'), ('sleep', '瞓覺', 'violet')]
def act_btn(board, i, pressed=False):
    kd, lab, fk = ACTS[i]
    cx = 26 + i * 47.7; cy = 330
    medallion(board, P(cx), P(cy), 34, C[fk], kd, 25, pressed=pressed, glow=1.0)
    py = cy + 13 + (0.9 if pressed else 0)
    place(board, frame(30, 11, 5.5, C['navy'], glow=0.4, ornate=False, rim=0.8), P(cx - 15), P(py))
    text(board, (P(cx), P(py + 5.3)), lab, 6.9, C['cream'], 'serif', stroke=0.8)

NEEDS = [('feed', .62, (hx('#FFE6A8'), hx('#FF9E3E'))), ('heart_bunny', .48, (hx('#FFC8D8'), hx('#FF5C8E'))),
         ('clean', .55, (hx('#C8F2FF'), hx('#3FAEEA'))), ('sleep', .80, (hx('#FFF4B8'), hx('#FFC23A')))]

def nameplate(board, pet_key='A1', name='滴滴', stage='幼崽', prog=.62):
    place(board, frame(98, 24, 9, C['navy'], glow=0.8, ornate=False), P(3), P(3))
    medallion(board, P(14), P(15), 23, C['paper'], glow=0.8)
    pet = k.load(f'{ROOT}/sprites/tuanrong/species_concept/from_ref/tuned_48/sprites/{pet_key}_48.png')
    bb = pet.getbbox(); head = pet.crop((bb[0], bb[1] + 3, bb[2], bb[1] + 3 + (bb[2] - bb[0]))).resize((P(16), P(16)), Image.NEAREST)
    board.alpha_composite(head, (P(6), P(7.5)))
    nx = 28
    text(board, (P(nx), P(10.5)), name, 9.2, C['cream'], 'serif', anchor='lm', stroke=0.9, glow=0.25)
    place(board, frame(19, 8, 4, C['violet'], glow=0, ornate=False, rim=0.6), P(nx + 23), P(6.6))
    text(board, (P(nx + 32.5), P(10.6)), stage, 5.6, hx('#FFFFFF'), 'sans', stroke=0.6, stroke_col=hx('#3A2470'))
    d = ImageDraw.Draw(board)
    d.rounded_rectangle([P(nx), P(18.2), P(96), P(21.4)], radius=P(1.6), fill=hx('#0B0E24'))
    seg_w = (96 - nx) * prog
    seg = vgrad((P(seg_w), P(2.6)), [(0, C['g_hi']), (1, hx('#E59A3E'))])
    board.alpha_composite(seg, (P(nx + .3), P(18.5)))
    # milestone gems on the exp bar
    for t in (.33, .66):
        gem(board, P(nx + (96 - nx) * t), P(19.8), 1.5, C['sec'] if t < prog else C['dis'], glow=t < prog, star=False)

def hud(board):
    nameplate(board)
    chip(board, 104, 5, 36, 'light', 140)
    chip(board, 153, 5, 34, 'star', 10)
    for i, (kd, v, col) in enumerate(NEEDS):
        need_bar(board, 4 + i * 47.4, 32, 44, kd, v, col)

def quest_btn(board, dot=True):
    medallion(board, P(178), P(66), 24, C['navy'], 'gift', 19, glow=1.0)
    if dot: red_dot(board, P(187), P(56.5), 3)
    text(board, (P(178), P(82.5)), '委託', 6.4, C['cream'], 'serif', stroke=0.9)

def ui_layer(skip=(), active=0):
    """all home HUD on a transparent SS canvas (so motion can move it)"""
    L = Image.new('RGBA', (P(195), P(422)), (0, 0, 0, 0))
    if 'hud' not in skip: hud(L)
    if 'quest' not in skip: quest_btn(L)
    if 'toast' not in skip: toast(L, 34, 56, 116, '收到小禮物 +5')
    if 'speech' not in skip: speech(L, 104, 222, 54, 16, '肚仔餓…', 'feed')
    if 'acts' not in skip:
        for i in range(4): act_btn(L, i)
    if 'dock' not in skip: dock(L, active=active)
    return L

def scene_ss(layers, **kw):
    return scene_compose(layers, **kw).resize((P(195), P(422)), Image.NEAREST)

POP_ROWS = [('play_cat', '陪佢玩 2 次', 0.5, '1/2'), ('feed', '餵佢食嘢', 1.0, '完成'), ('clean', '幫佢沖涼', 0.0, '0/1')]
def popup_layer(x=19, y=110, w=157, h=132, parts=('frame', 'rows', 'btn')):
    L = Image.new('RGBA', (P(195), P(422)), (0, 0, 0, 0))
    if 'frame' in parts:
        place(L, frame(w, h, 12, C['navy'], glow=1.3, ornate=True), P(x), P(y))
        plaque(L, x + w / 2, y - 9, 78, '今日委託')
        close_btn(L, P(x + w - 2), P(y + 2))
    if 'rows' in parts:
        for i in range(3): popup_row(L, x, y, w, i)
    if 'btn' in parts:
        button(L, x + (w - 76) / 2, y + h - 30, 76, 20, 'pri', '全部領取')
    return L

def popup_row(L, x, y, w, i, dx=0, a=1.0):
    kd, lab, v, prog = POP_ROWS[i]
    ry = y + 16 + i * 30
    tmp = Image.new('RGBA', L.size, (0, 0, 0, 0))
    place(tmp, frame(w - 18, 25, 7, C['navy_in'], glow=0.25, ornate=False, rim=0.8), P(x + 9 + dx), P(ry))
    medallion(tmp, P(x + 21 + dx), P(ry + 12.5), 19, C['paper'], kd, 16, glow=0.4)
    text(tmp, (P(x + 34 + dx), P(ry + 8)), lab, 7.3, C['cream'], 'sans', anchor='lm', stroke=0.8)
    tx0 = x + 34 + dx; tw = 58
    d = ImageDraw.Draw(tmp)
    d.rounded_rectangle([P(tx0), P(ry + 14.5), P(tx0 + tw), P(ry + 18.5)], radius=P(2), fill=hx('#0B0E24'))
    if v > 0:
        seg = vgrad((P(tw * v), P(3.4)), [(0, hx('#C8F7EE')), (1, hx('#3797B4'))]); tmp.alpha_composite(seg, (P(tx0 + .3), P(ry + 14.8)))
    text(tmp, (P(tx0 + tw + 1.5), P(ry + 16.4)), prog, 5.4, hx('#F2E6C8'), 'fred' if prog.isascii() else 'sans', anchor='lm', stroke=0.6)
    icon(tmp, 'star', P(x + w - 30 + dx), P(ry + 12.5), 13)
    gold_text(tmp, (P(x + w - 18 + dx), P(ry + 12.8)), '+4', 8.0, 'cin', glow=0.4)
    if v >= 1.0:   # 完成 stamp glow
        gem(tmp, P(x + w - 12 + dx), P(ry + 3.5), 2.2, C['pri'])
    if a < 1: tmp.putalpha(amul(tmp.getchannel('A'), a))
    L.alpha_composite(tmp)

def dim_blur(scene_img_ss, amt=1.0):
    """DoF + dim for modal background (SS image)"""
    small = scene_img_ss.reduce(6)
    b = small.filter(ImageFilter.GaussianBlur(1.6 * amt)).resize(scene_img_ss.size, Image.BICUBIC)
    out = Image.blend(scene_img_ss, b, min(1, amt))
    ov = Image.new('RGBA', out.size, hx('#141A36', int(110 * amt)))
    out.alpha_composite(ov)
    return out

def motes(L, seed=0, n=18, t=0.0, area=(10, 60, 185, 360)):
    rng = np.random.default_rng(seed); W, H = L.size
    g = Image.new('L', (W, H), 0); d = ImageDraw.Draw(g)
    for i in range(n):
        x = rng.uniform(area[0], area[2]); y0 = rng.uniform(area[1], area[3]); sp = rng.uniform(8, 20); ph = rng.uniform(0, 6.28)
        y = area[1] + ((y0 - area[1] - sp * t * 3) % (area[3] - area[1]))
        x += 2.5 * math.sin(t * 3 + ph)
        r = rng.uniform(0.5, 1.1) * (0.6 + 0.4 * math.sin(t * 6 + ph))
        a = int(200 * (0.5 + 0.5 * math.sin(t * 5 + ph)))
        d.ellipse([P(x - r), P(y - r), P(x + r), P(y + r)], fill=a)
    put(L, solid((W, H), C['glow']), gauss(g, P(0.6)))
    put(L, solid((W, H), hx('#FFFFFF')), amul(g, 0.8))
