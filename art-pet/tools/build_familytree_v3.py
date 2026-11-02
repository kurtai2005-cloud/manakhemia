#!/usr/bin/env python3
"""《微光小圃》第 7 批：族譜 V3-A（金光深藍磨砂＋1.5px 金幼線）。依 docs-gdd/family-work-scenes-v1.md §1、§2.1 族譜部分。
零件：節點框 2 款（團絨圓框／細佬葉框 × 亮／灰／選中）＋皇冠、關係章 3 個（傳／祖／屋）＋兄弟同色圓點、線 4 款（直系金實線＋箭咀／兄弟銀虛線／同屋淺藍點線／祖輩淡金＋細星）、
成就徽章 6 個＋成就框（族譜金框、兄弟合照框、九光齊光環、八系齊葉形邊、祖傳牌）、背景（普通＋暖色版）、光影＋粒子。
頭像用現有寵物 sprite（build_ui_hd2d_v3_mockups.face，跟實際形態）；寵物光跟 layout_hd2d_v3.json#petGlow（瞓覺 0）。
Pillow／numpy 程序化，冇 AI 圖；字只用 Noto CJK TC（最細 18@3x）；唔用 Fusion Pixel。sprite（皇冠、粒子、頭像）alpha 0/255；UI／光影層真 alpha。
用法：python3 build_familytree_v3.py"""
import os, sys, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import ui_hd2d_v3_lib as L
from ui_hd2d_v3_lib import C, A, P, W, H, text, tw, icon, comp, compc, new
import build_ui_hd2d_v3_mockups as M3
ART = L.ART; OUT = f'{ART}/ui/familytree_v3'; LAYG = json.load(open(f'{L.KIT}/layout_hd2d_v3.json'))
PG = LAYG['petGlow']; BANDS = LAYG['bands']
def save(im, rel):
    p = f'{OUT}/{rel}'; os.makedirs(os.path.dirname(p), exist_ok=True); im.save(p, optimize=True); return rel
def hx(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def arr(im): return np.asarray(im).astype(float)
def toim(a): return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')
def binarize(im, t=128):
    a = np.array(im.convert('RGBA')); a[..., 3] = np.where(a[..., 3] >= t, 255, 0); return Image.fromarray(a)
def soft_glow(w, h, col, a=.6, p=2.0):
    yy, xx = np.mgrid[0:h, 0:w].astype(float); d = np.hypot((xx - (w - 1) / 2) / (w / 2), (yy - (h - 1) / 2) / (h / 2)); g = np.zeros((h, w, 4)); g[..., :3] = col[:3]; g[..., 3] = np.clip(1 - d, 0, 1) ** p * a * 255; return toim(g)
SS = 4
def draw_ss(w, h, fn):
    im = Image.new('RGBA', (w * SS, h * SS), (0, 0, 0, 0)); fn(ImageDraw.Draw(im), SS); return im.resize((w, h), Image.LANCZOS)
REL = dict(gen=dict(zh='上一代／下一代', line='line_gen', mark='stamp_chuan', col=C['gold']), sib=dict(zh='兄弟姊妹', line='line_sib', mark='sib_dot', col=(214, 220, 236)),
           house=dict(zh='同屋（冇血緣）', line='line_house', mark='stamp_wu', col=(140, 206, 246)), anc=dict(zh='祖輩（隔 2 代或以上）', line='line_anc', mark='stamp_zu', col=C['gold']))
# ============================================================== 1. 節點框
ND = 132; WIN = 96   # 框外徑；頭像窗（sprite 24px×4）
def leaf_mask(d, ss=SS):
    """葉形：TL／BR 尖、TR／BL 大圓角（細佬）"""
    D = d * ss; m = Image.new('L', (D, D)); dr = ImageDraw.Draw(m); r = int(D * .44); s = int(D * .04); q = int(D * .1)
    dr.rounded_rectangle([s, s, D - s, D - s], r, fill=255)
    dr.rounded_rectangle([s, s, D // 2, D // 2], q, fill=255); dr.rounded_rectangle([D // 2, D // 2, D - s, D - s], q, fill=255)   # TL／BR 尖（細圓角）
    return m.resize((d, d), Image.LANCZOS)
def shape_mask(kind, d): return L.circ_mask(d) if kind == 'round' else leaf_mask(d)
def outline_of(mask, lw):
    a = arr(mask) / 255; inner = np.asarray(mask.filter(ImageFilter.MinFilter(int(lw * 2) | 1))).astype(float) / 255; return np.clip(a - inner, 0, 1)
def node_frame(kind, state):
    """kind round|leaf；state live|gray|sel。UI 層（真 alpha）。窗＝中心 WIN×WIN（頭像 runtime 疊 + 用 node_<kind>_mask）"""
    d = ND; o = np.zeros((d, d, 4)); fd = d - 16; off = 8
    m = shape_mask(kind, fd); ma = arr(m) / 255
    gold = np.array(C['goldhi'] if state != 'gray' else (168, 172, 190)); gold2 = np.array(C['gold'] if state != 'gray' else (120, 124, 146))
    # 磨砂底（深藍）
    base = np.zeros((fd, fd, 4)); t = np.linspace(0, 1, fd)[:, None]; base[..., :3] = (np.array(C['navy2']) * (1 - t[..., None]) + np.array(C['navy']) * t[..., None]); base[..., 3] = ma * (.88 * 255)
    o[off:off + fd, off:off + fd] = base
    # 外金線 1.5px＋內細線
    ol = outline_of(m, 2); il = outline_of(Image.fromarray((np.asarray(m.resize((fd - 12, fd - 12), Image.LANCZOS)))), 1.2)
    def addline(lm, col, a, x0, y0):
        h_, w_ = lm.shape; seg = o[y0:y0 + h_, x0:x0 + w_]; al = lm * a; seg[..., :3] = seg[..., :3] * (1 - al[..., None]) + col * al[..., None]; seg[..., 3] = np.maximum(seg[..., 3], al * 255)
    yy = np.linspace(0, 1, fd)[:, None] * np.ones((1, fd)); shade = 1.1 - .3 * yy   # 金線上亮下暗（光由上）
    addline(ol * np.clip(shade, 0, 1), gold, 1, off, off); addline(il, gold2, .45, off + 6, off + 6)
    # 頂高光弧
    hl = np.zeros((fd, fd)); hl[:fd // 2] = np.linspace(.22, 0, fd // 2)[:, None]; seg = o[off:off + fd, off:off + fd]; seg[..., :3] += (hl * ma)[..., None] * 255 * .5
    if state == 'sel':   # 外金光＋外圈亮線（同形）
        full = Image.fromarray(np.pad(np.asarray(m), ((off, off), (off, off))))
        dil = full.filter(ImageFilter.MaxFilter(7)); ring = np.clip(arr(dil) / 255 - arr(full.filter(ImageFilter.MaxFilter(3))) / 255, 0, 1) * .9
        gl = arr(full.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(5))) / 255 * (1 - arr(full) / 255) * .75
        for lm, col in ((gl, np.array(C['gold'])), (ring, np.array(C['goldhi']))):
            al = lm[..., None]; oa = o[..., 3:] / 255; na = al + oa * (1 - al)
            o[..., :3] = np.where(na > 0, (col * al + o[..., :3] * oa * (1 - al)) / np.maximum(na, 1e-6), 0); o[..., 3] = na[..., 0] * 255
    if kind == 'leaf':   # 葉柄＋葉脈裝飾（右上）
        dec = draw_ss(d, d, lambda dr, s: (dr.line([(d * .80 * s, d * .20 * s), (d * .93 * s, d * .07 * s)], fill=A(tuple(gold), .95), width=int(2 * s)),
                                         dr.line([(d * .86 * s, d * .14 * s), (d * .93 * s, d * .17 * s)], fill=A(tuple(gold2), .9), width=int(1.4 * s))))
        da = arr(dec); al = da[..., 3:] / 255; o[..., :3] = o[..., :3] * (1 - al) + da[..., :3] * al; o[..., 3] = np.maximum(o[..., 3], da[..., 3])
    else:   # 圓框：上下菱形
        for cy in (off - 1, d - off - 10):
            dm = arr(L.diamond_im(4, A(tuple(gold)))); h_, w_ = dm.shape[:2]; x0 = d // 2 - w_ // 2; seg = o[cy:cy + h_, x0:x0 + w_]; al = dm[..., 3:] / 255
            seg[..., :3] = seg[..., :3] * (1 - al) + dm[..., :3] * al; seg[..., 3] = np.maximum(seg[..., 3], dm[..., 3])
    return toim(o)
def win_mask(kind): m = shape_mask(kind, WIN); return m
# 皇冠（像素 sprite，0/255）
CROWN = ["....g.....g.....g....", "...gwg...gwg...gwg...", "....g.....g.....g....", "....gg...ggg...gg....", "....ggg.ggrgg.ggg....", "....ggggggggggggg....",
         "....gdgdgbgbgdgdg....", "....ggggggggggggg....", "....ddddddddddddd...."]
def crown():
    pal = {'g': (255, 214, 92), 'w': (255, 250, 220), 'r': (230, 70, 96), 'b': (96, 180, 255), 'd': (176, 112, 30)}
    h_, w_ = len(CROWN), len(CROWN[0]); a = np.zeros((h_, w_, 4), np.uint8)
    for y, row in enumerate(CROWN):
        for x, ch in enumerate(row):
            if ch in pal: a[y, x] = pal[ch] + (255,)
    return Image.fromarray(a).resize((w_ * 3, h_ * 3), Image.NEAREST)
# ============================================================== 2. 關係章／圓點／icon
SEAL = {'chuan': ('傳', (196, 48, 52), (255, 246, 232)), 'zu': ('祖', (120, 80, 30), (255, 240, 206)), 'wu': ('屋', (40, 108, 170), (240, 250, 255))}
def stamp(k, d=60):
    ch, bg, fg = SEAL[k]; f = L.F('serif', 34)
    def fn(dr, s):
        dr.rounded_rectangle([3 * s, 3 * s, (d - 3) * s, (d - 3) * s], 9 * s, fill=A(bg, .96)); dr.rounded_rectangle([6.5 * s, 6.5 * s, (d - 6.5) * s, (d - 6.5) * s], 6 * s, outline=A(fg, .9), width=int(1.5 * s))
    im = draw_ss(d, d, fn); ImageDraw.Draw(im).text((d / 2, d / 2 + 1), ch, font=f, fill=A(fg), anchor='mm')
    a = arr(im); rnd = np.random.RandomState(ord(ch) % 97); n = rnd.rand(d, d); a[..., 3] *= np.where(n > .955, .55, 1)   # 印泥斑駁
    if k == 'wu':   # 屋：右上加小屋 icon 細角
        hs = draw_ss(d, d, lambda dr, s: dr.polygon([((d - 14) * s, 2 * s), ((d - 2) * s, 12 * s), ((d - 26) * s, 12 * s)], fill=A(C['goldhi'])))
        ha = arr(hs); al = ha[..., 3:] / 255; a[..., :3] = a[..., :3] * (1 - al) + ha[..., :3] * al; a[..., 3] = np.maximum(a[..., 3], ha[..., 3])
    return toim(a).rotate(-8, Image.BICUBIC, expand=False), ch, bg, fg
SIB_COLS = {'rose': C['rose'], 'mint': C['mint'], 'sky': C['sky'], 'amber': C['amber'], 'violet': C['violet']}
def sib_dot(col, d=22):
    im = new(d, d); im.alpha_composite(soft_glow(d, d, col, .55, 1.2)); c = draw_ss(d, d, lambda dr, s: (dr.ellipse([6 * s, 6 * s, (d - 6) * s, (d - 6) * s], fill=A(col)),
                                                                                                         dr.ellipse([6 * s, 6 * s, (d - 6) * s, (d - 6) * s], outline=A((255, 255, 255), .9), width=int(1.5 * s))))
    im.alpha_composite(c); return im
def house_icon(d=30):
    return draw_ss(d, d, lambda dr, s: (dr.polygon([(d / 2 * s, 3 * s), ((d - 3) * s, 14 * s), (3 * s, 14 * s)], fill=A((140, 206, 246))), dr.rectangle([7 * s, 14 * s, (d - 7) * s, (d - 4) * s], fill=A((140, 206, 246))),
                                        dr.rectangle([(d / 2 - 3) * s, 19 * s, (d / 2 + 3) * s, (d - 4) * s], fill=A(C['navy'])), dr.polygon([(d / 2 * s, 3 * s), ((d - 3) * s, 14 * s), (3 * s, 14 * s)], outline=A((230, 246, 255)), width=int(1.2 * s))))
def inherit_arrow(d=26):
    """遺傳自：細箭咀（向上彎，指返出處）"""
    return draw_ss(d, d, lambda dr, s: (dr.arc([4 * s, 6 * s, (d - 4) * s, (d + 10) * s], 200, 330, fill=A(C['goldhi']), width=int(2 * s)),
                                        dr.polygon([((d - 6) * s, 4 * s), ((d - 1) * s, 12 * s), ((d - 11) * s, 12 * s)], fill=A(C['goldhi']))))
# ============================================================== 3. 線 4 款（tile；UI 光層，真 alpha）
def line_tile(kind, orient):
    """orient h：w=48 tile、h=12；v：轉 90°。核心 1.5px＋柔光"""
    w, h = 48, 12; a = np.zeros((h, w, 4)); cy = h / 2 - .5; yy = np.arange(h)[:, None].astype(float)
    core = np.clip(1.25 - np.abs(yy - cy) / .9, 0, 1) * np.ones((1, w)); halo = np.exp(-((yy - cy) / 2.6) ** 2) * np.ones((1, w))
    xx = np.arange(w)[None, :].astype(float)
    if kind == 'gen': col = np.array(C['goldhi']); m_core, m_halo, glow = core, halo * .35, C['gold']
    elif kind == 'sib': col = np.array((222, 226, 240)); on = ((xx % 16) < 9).astype(float); m_core, m_halo, glow = core * on, halo * .18 * on, (200, 210, 240)
    elif kind == 'house':
        col = np.array((150, 214, 250)); dd = np.hypot((xx % 12) - 5.5, yy - cy); m_core = np.clip(2.2 - dd, 0, 1); m_halo = np.exp(-(dd / 3) ** 2) * .3; glow = (140, 206, 246)
    else:   # anc：淡金＋每 48px 細星
        col = np.array(C['gold']); m_core, m_halo, glow = core * .45, halo * .14, C['gold']
    a[..., :3] = col; a[..., 3] = np.clip(m_core + m_halo, 0, 1) * 255
    if kind == 'gen': a[..., :3] = a[..., :3] * (m_core[..., None] > .3) + np.array(glow) * (m_core[..., None] <= .3)
    im = toim(a)
    if kind == 'anc':
        st = L.flare_im(5, A(C['goldhi']), .95); im.alpha_composite(st, (24 - st.width // 2, int(cy) - st.height // 2 + 1)); im = im.crop((0, 0, w, h)) if im.height > h else im
    return im if orient == 'h' else im.rotate(90, expand=True)
def arrow_head(col=C['goldhi'], d=22):
    return draw_ss(d, d, lambda dr, s: dr.polygon([(d / 2 * s, (d - 3) * s), (3 * s, 6 * s), (d / 2 * s, 10 * s), ((d - 3) * s, 6 * s)], fill=A(col)))
def joint(col=C['goldhi']): im = new(18, 18); im.alpha_composite(soft_glow(18, 18, C['gold'], .5)); im.alpha_composite(L.diamond_im(5, A(col)), (2, 2)); return im
# ============================================================== 4. 成就徽章 6＋框
ACH = [('first_home', '第一個家', '第 1 隻成家人', '族譜金框'), ('three_gen', '三代同堂', '族譜有 3 代', '「三代」徽章＋族譜背景變暖色'), ('brothers', '兄弟情', '同一上一代有 2 隻', '兄弟合照框'),
       ('nine_light', '九光齊', '團絨 9 條路線都出過', '族譜頂部光環'), ('eight_series', '八系齊', '細佬 A–H 都出過', '族譜葉形邊'), ('move_heir', '招式傳人', '同一招式連傳 3 代', '招式名加「祖傳」')]
ROUTE9 = ['#62CFEF', '#c8b8ff', '#ff9ab0', '#a6eefa', '#ff9a5a', '#ffe46a', '#ffd0e8', '#e8d8b0', '#b8ffd0']
SER8 = ['#ff8a8a', '#ffb86a', '#ffe46a', '#9ae07a', '#6ad0c8', '#7aaaff', '#b48aff', '#ff8ad0']
def badge(k, locked=False, d=120):
    im = new(d, d); gcol = C['gold'] if not locked else (130, 134, 156)
    if not locked: im.alpha_composite(soft_glow(d, d, C['gold'], .5, 1.6))
    r0 = 12
    def base(dr, s):
        dr.ellipse([r0 * s, r0 * s, (d - r0) * s, (d - r0) * s], fill=A(C['navy2'] if not locked else (54, 58, 78), .95))
        dr.ellipse([r0 * s, r0 * s, (d - r0) * s, (d - r0) * s], outline=A(C['goldhi'] if not locked else (170, 174, 192)), width=int(1.5 * s))
        dr.ellipse([(r0 + 6) * s, (r0 + 6) * s, (d - r0 - 6) * s, (d - r0 - 6) * s], outline=A(gcol, .45), width=int(1 * s))
        for i in range(12):   # 鋸齒金邊（勳章）
            a = i * math.pi / 6; cx, cy = d / 2 + math.cos(a) * (d / 2 - 9), d / 2 + math.sin(a) * (d / 2 - 9); dr.ellipse([(cx - 2.2) * s, (cy - 2.2) * s, (cx + 2.2) * s, (cy + 2.2) * s], fill=A(gcol))
    im.alpha_composite(draw_ss(d, d, base)); c = d / 2; g = C['goldhi'] if not locked else (186, 190, 206)
    def sym(dr, s):
        S = lambda *p: [(x * s, y * s) for x, y in p]
        if k == 'first_home':
            dr.polygon(S((c, c - 24), (c + 24, c - 2), (c - 24, c - 2)), fill=A(g)); dr.rectangle([(c - 17) * s, (c - 2) * s, (c + 17) * s, (c + 22) * s], fill=A(g))
            hc = (230, 90, 120) if not locked else (120, 124, 146); dr.ellipse([(c - 9) * s, (c + 2) * s, (c - 1) * s, (c + 10) * s], fill=A(hc)); dr.ellipse([(c + 1) * s, (c + 2) * s, (c + 9) * s, (c + 10) * s], fill=A(hc))
            dr.polygon(S((c - 9, c + 7), (c + 9, c + 7), (c, c + 17)), fill=A(hc))
        elif k == 'three_gen':
            for i, (x, y) in enumerate(((c, c - 18), (c - 15, c + 2), (c + 15, c + 2), (c - 15, c + 20))):
                dr.ellipse([(x - 7) * s, (y - 7) * s, (x + 7) * s, (y + 7) * s], fill=A(g))
            dr.line(S((c, c - 11), (c, c - 6), (c - 15, c - 6), (c - 15, c - 5)), fill=A(g), width=int(2 * s)); dr.line(S((c, c - 6), (c + 15, c - 6), (c + 15, c - 5)), fill=A(g), width=int(2 * s))
            dr.line(S((c - 15, c + 9), (c - 15, c + 13)), fill=A(g), width=int(2 * s))
        elif k == 'brothers':
            for x in (c - 13, c + 13):
                dr.ellipse([(x - 12) * s, (c - 16) * s, (x + 12) * s, (c + 8) * s], fill=A(g)); dr.ellipse([(x - 4) * s, (c - 7) * s, (x - 1) * s, (c - 3) * s], fill=A(C['navy'])); dr.ellipse([(x + 1) * s, (c - 7) * s, (x + 4) * s, (c - 3) * s], fill=A(C['navy']))
            dr.rounded_rectangle([(c - 26) * s, (c + 10) * s, (c + 26) * s, (c + 22) * s], 6 * s, fill=A(g))
        elif k == 'nine_light':
            for i in range(9):
                a = -math.pi / 2 + i * 2 * math.pi / 9; col = hx(ROUTE9[i]) if not locked else (150, 154, 172); x, y = c + math.cos(a) * 24, c + math.sin(a) * 24; dr.ellipse([(x - 5) * s, (y - 5) * s, (x + 5) * s, (y + 5) * s], fill=A(col))
            dr.ellipse([(c - 10) * s, (c - 10) * s, (c + 10) * s, (c + 10) * s], fill=A(g))
        elif k == 'eight_series':
            for i in range(8):
                a = i * math.pi / 4; col = hx(SER8[i]) if not locked else (150, 154, 172); ca, sa = math.cos(a), math.sin(a)
                pts = [(c + ca * 6 - sa * 0, c + sa * 6 + ca * 0), (c + ca * 18 - sa * 7, c + sa * 18 + ca * 7), (c + ca * 30, c + sa * 30), (c + ca * 18 + sa * 7, c + sa * 18 - ca * 7)]
                dr.polygon([(x * s, y * s) for x, y in pts], fill=A(col))
            dr.ellipse([(c - 6) * s, (c - 6) * s, (c + 6) * s, (c + 6) * s], fill=A(g))
        else:   # move_heir：卷軸
            dr.rounded_rectangle([(c - 24) * s, (c - 14) * s, (c + 24) * s, (c + 16) * s], 4 * s, fill=A(g)); dr.ellipse([(c - 30) * s, (c - 16) * s, (c - 18) * s, (c + 18) * s], fill=A(gcol)); dr.ellipse([(c + 18) * s, (c - 16) * s, (c + 30) * s, (c + 18) * s], fill=A(gcol))
    im.alpha_composite(draw_ss(d, d, sym))
    if k == 'three_gen' or k == 'move_heir':
        t = '三代' if k == 'three_gen' else '傳'; f = L.F('serif', 22 if k == 'three_gen' else 26)
        if k == 'three_gen':
            dr = ImageDraw.Draw(im); dr.rounded_rectangle([c - 26, d - 36, c + 26, d - 10], 8, fill=A(C['red2'] if not locked else (90, 94, 112))); dr.text((c, d - 23), t, font=f, fill=A((255, 246, 232)), anchor='mm')
        else: ImageDraw.Draw(im).text((c, c + 1), t, font=f, fill=A((120, 60, 20) if not locked else (70, 74, 92)), anchor='mm')
    if locked:
        lk = L.IC('lock')[0]; im.alpha_composite(lk, (d - lk.width - 6, d - lk.height - 6))
    return im
def gold_frame(w=585, h=918):
    """族譜金框（成就：第一個家）：內容區雙金線＋四角花飾（UI 層）"""
    def fn(dr, s):
        dr.rounded_rectangle([6 * s, 6 * s, (w - 6) * s, (h - 6) * s], 22 * s, outline=A(C['goldhi'], .95), width=int(1.5 * s))
        dr.rounded_rectangle([13 * s, 13 * s, (w - 13) * s, (h - 13) * s], 16 * s, outline=A(C['gold'], .55), width=int(1 * s))
        for (cx, cy, sx, sy) in ((6, 6, 1, 1), (w - 6, 6, -1, 1), (6, h - 6, 1, -1), (w - 6, h - 6, -1, -1)):
            for r in (18, 30):
                dr.arc([(cx - r) * s if sx > 0 else (cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s], 0, 360, fill=A(C['gold'], .0))
            pts = [(cx + sx * 4, cy + sy * 30), (cx + sx * 14, cy + sy * 14), (cx + sx * 30, cy + sy * 4)]; dr.line([(x * s, y * s) for x, y in pts], fill=A(C['goldhi']), width=int(2 * s))
            dr.ellipse([(cx + sx * 14 - 4) * s, (cy + sy * 14 - 4) * s, (cx + sx * 14 + 4) * s, (cy + sy * 14 + 4) * s], fill=A(C['goldhi']))
    im = new(w, h); g = draw_ss(w, h, fn); im.alpha_composite(g.filter(ImageFilter.GaussianBlur(4)).point(lambda v: v)); im.alpha_composite(g); return im
def sibling_frame(w=300, h=190):
    """兄弟合照框：兩個頭像窗＋緞帶（UI 層）；窗中心 (w*.3,h*.46)／(w*.7,h*.46) d=96"""
    def fn(dr, s):
        dr.rounded_rectangle([4 * s, 4 * s, (w - 4) * s, (h - 4) * s], 20 * s, fill=A(C['paper'], .96), outline=A(C['gold2']), width=int(2 * s))
        dr.rounded_rectangle([10 * s, 10 * s, (w - 10) * s, (h - 10) * s], 15 * s, outline=A(C['gold'], .7), width=int(1.2 * s))
        for cx in (w * .3, w * .7): dr.ellipse([(cx - 52) * s, (h * .46 - 52) * s, (cx + 52) * s, (h * .46 + 52) * s], fill=A(C['gold'], .9))
        dr.polygon([((w / 2 - 54) * s, (h - 30) * s), ((w / 2 + 54) * s, (h - 30) * s), ((w / 2 + 62) * s, (h - 18) * s), ((w / 2 + 54) * s, (h - 6) * s), ((w / 2 - 54) * s, (h - 6) * s), ((w / 2 - 62) * s, (h - 18) * s)], fill=A(C['rose']))
    im = draw_ss(w, h, fn)
    for cx in (w * .3, w * .7):   # 挖窗
        a = arr(im); m = arr(L.circ_mask(96)) / 255; x0, y0 = int(cx - 48), int(h * .46 - 48); a[y0:y0 + 96, x0:x0 + 96, 3] *= (1 - m); im = toim(a)
    ImageDraw.Draw(im).text((w / 2, h - 18), '兄弟', font=L.F('sansb', 18), fill=A(C['ink']), anchor='mm'); return im
def halo_top(w=585, h=240):
    """九光齊：族譜頂部光環（光層，真 alpha）：九色光珠弧＋柔光"""
    a = np.zeros((h, w, 4)); yy, xx = np.mgrid[0:h, 0:w].astype(float); cx, cy, R = w / 2, -300, 380
    d = np.hypot(xx - cx, yy - cy); ring = np.exp(-((d - R) / 10) ** 2); glow = np.exp(-((d - R) / 40) ** 2) * .45
    ang = np.arctan2(yy - cy, xx - cx); col = np.zeros((h, w, 3))
    for i, c in enumerate(ROUTE9):
        t = math.pi / 2 + (i - 4) * .155; wgt = np.exp(-((ang - t) / .1) ** 2); col += wgt[..., None] * np.array(hx(c))
    nrm = col.max(-1, keepdims=True); col = np.where(nrm > 1, col / np.maximum(nrm, 1) * 255, 255)
    a[..., :3] = col * .6 + np.array(C['goldhi']) * .4; a[..., 3] = np.clip(ring * .9 + glow, 0, 1) * 255 * np.clip((h - yy) / 60, 0, 1) * np.clip(yy / 24, 0, 1)
    im = toim(a)
    for i, c in enumerate(ROUTE9):
        t = math.pi / 2 + (i - 4) * .155; x, y = cx + math.cos(t) * R, cy + math.sin(t) * R; g = soft_glow(40, 40, hx(c), .9, 1.6); im.alpha_composite(g, (int(x - 20), int(y - 20)))
        im.alpha_composite(draw_ss(14, 14, lambda dr, s, c=c: dr.ellipse([2 * s, 2 * s, 12 * s, 12 * s], fill=A(hx(c)), outline=A((255, 255, 255)), width=int(1.2 * s))), (int(x - 7), int(y - 7)))
    return im
def leaf_border(h=120, w=40):
    """八系齊：葉形邊（直 tile，左右邊各一條；右邊 flipX）"""
    def fn(dr, s):
        dr.line([(w * .5 * s, 0), (w * .5 * s, h * s)], fill=A(C['gold'], .8), width=int(1.5 * s))
        for i, y in enumerate((15, 45, 75, 105)):
            c = hx(SER8[(i * 2) % 8]); sx = 1 if i % 2 == 0 else -1; x0 = w * .5
            pts = [(x0, y), (x0 + sx * 10, y - 9), (x0 + sx * 18, y - 4), (x0 + sx * 10, y + 3)]; dr.polygon([(x * s, yy * s) for x, yy in pts], fill=A(c, .95), outline=A(C['goldhi'], .9))
    return draw_ss(w, h, fn)
def heir_tag(w=96, h=32):
    im = new(w, h); im.alpha_composite(L._btn(w, h, 'pri')); ImageDraw.Draw(im).text((w / 2, h / 2), '祖傳', font=L.F('sansb', 18), fill=A(C['ink']), anchor='mm'); return im
# ============================================================== 5. 背景＋光影＋粒子
def background(warm):
    """585×1266；深藍金光（普通）／暖色（三代同堂）。烘焙：上方柔光柱、bokeh、vignette"""
    h, w = H, W; yy, xx = np.mgrid[0:h, 0:w].astype(float); t = yy / h
    if not warm: top, mid, bot, beam = np.array((26, 34, 70)), np.array((18, 24, 52)), np.array((10, 14, 32)), np.array(C['gold'])
    else: top, mid, bot, beam = np.array((84, 50, 46)), np.array((52, 32, 40)), np.array((24, 16, 26)), np.array((255, 196, 120))
    c = np.where(t[..., None] < .5, top * (1 - t[..., None] * 2) + mid * t[..., None] * 2, mid * (2 - t[..., None] * 2) + bot * (t[..., None] * 2 - 1))
    rnd = np.random.RandomState(7 if warm else 3); n = np.zeros((h, w))
    for cell, k in ((160, .5), (60, .3), (24, .2)):
        r = rnd.rand(h // cell + 2, w // cell + 2); n += np.asarray(Image.fromarray((r * 255).astype(np.uint8)).resize(((w // cell + 2) * cell, (h // cell + 2) * cell), Image.BICUBIC)).astype(float)[:h, :w] / 255 * k
    c *= (.9 + .2 * n[..., None])
    ang = np.arctan2(xx - w / 2, yy + 200); beams = (np.sin(ang * 23) * .5 + .5) ** 6 * np.exp(-(yy + 200) / 900) * np.exp(-(ang / .5) ** 2)
    c += beams[..., None] * beam * (.22 if not warm else .3)
    c += np.exp(-(((xx - w / 2) / 260) ** 2 + ((yy - 140) / 220) ** 2))[..., None] * beam * (.14 if not warm else .2)   # 頂柔光
    for i in range(26):   # bokeh
        x, y, r = rnd.uniform(0, w), rnd.uniform(140, h - 200), rnd.uniform(6, 22); dd = np.hypot(xx - x, yy - y)
        c += (np.clip(1 - dd / r, 0, 1) ** 1.5 * rnd.uniform(.05, .14))[..., None] * (beam if rnd.rand() < .7 else np.array((170, 190, 255)))
    vg = np.clip((((xx / w - .5) / .5) ** 2 + ((yy / h - .45) / .55) ** 2 - .35) / .9, 0, 1) ** 1.5 * .55; c *= (1 - vg[..., None])
    a = np.dstack([np.clip(c, 0, 255), np.full((h, w), 255)]); return toim(a)
def light_add(warm):
    """runtime 光層（lighter）：頂光柱（緩慢 sway）"""
    h, w = 700, W; yy, xx = np.mgrid[0:h, 0:w].astype(float); col = np.array(C['goldhi'] if not warm else (255, 210, 150))
    ang = np.arctan2(xx - w / 2, yy + 260); b = (np.sin(ang * 17 + 1) * .5 + .5) ** 5 * np.exp(-(yy + 260) / 600) * np.exp(-(ang / .45) ** 2)
    a = np.zeros((h, w, 4)); a[..., :3] = col; a[..., 3] = np.clip(b * .55, 0, 1) * 255; return toim(a)
def particles():
    """粒子 sprite（0/255）：金塵 mote 6 幀、細星 twinkle 6 幀、心心（摸肖像）6 幀；每格 24×24"""
    sh = new(24 * 6, 72)
    for i in range(6):
        t = math.sin(i / 5 * math.pi); a = np.zeros((24, 24, 4), np.uint8); r = 1 + int(round(t * 2)); c = 12
        a[c - r:c + r + 1, c - r:c + r + 1] = (255, 236, 184, 255); a[c - r - 1:c + r + 2, c] = (255, 220, 140, 255); a[c, c - r - 1:c + r + 2] = (255, 220, 140, 255); a[c, c] = (255, 255, 240, 255)
        sh.paste(Image.fromarray(a), (i * 24, 0))
        b = np.zeros((24, 24, 4), np.uint8); L_ = 2 + int(round(t * 6))
        b[c, c - L_:c + L_ + 1] = (255, 246, 220, 255); b[c - L_:c + L_ + 1, c] = (255, 246, 220, 255); b[c - 1:c + 2, c - 1:c + 2] = (255, 255, 255, 255); sh.paste(Image.fromarray(b), (i * 24, 24))
        hrt = [".xx.xx.", "xxxxxxx", "xxxxxxx", ".xxxxx.", "..xxx..", "...x..."]; hh = np.zeros((24, 24, 4), np.uint8); k = 2 if i < 4 else 2; dy = 12 - i * 1
        for y, row in enumerate(hrt):
            for x, ch in enumerate(row):
                if ch == 'x': hh[max(0, dy - 6 + y * k):max(0, dy - 6 + y * k) + k, 5 + x * k:5 + x * k + k] = (240, 110, 140, 255) if i < 5 else (255, 170, 190, 255)
        sh.paste(Image.fromarray(hh), (i * 24, 48))
    return sh
# ============================================================== 6. demo 家族（family.json 欄位，GDD §1.6）＋關係推導
FAMILY = [
    dict(id='guangguang', name='光光', line='tuanrong', parentId=None, gen=0, bornDay=1, adultDay=9, route='still_moon', form='evo_still_moon', pattern='月紋', move='月光波', story=['第 1 日喺光圃出世', '第 9 日成年，走靜光月路', '教識全屋人瞓覺前望月', '而家喺月光山谷退休'], frozen=True, state='awake', alive=False),
    dict(id='tuanrong', name='團絨', line='tuanrong', parentId='guangguang', gen=1, bornDay=12, adultDay=20, route='still_tide', form='evo_still_tide', pattern='月紋', move='月光波', story=['喺光光身邊孵出', '第 20 日成年，走靜光潮路', '帶大咗波波同火仔', '最鍾意幫手淋花'], frozen=False, state='awake', alive=True),
    dict(id='yueyue', name='月月', line='tuanrong', parentId='guangguang', gen=1, bornDay=13, adultDay=22, route='guard_shroom', form='evo_guard_shroom', pattern='菇點', move='守護圈', story=['同團絨一齊孵出', '第 22 日成年，走守護菇路', '成日守住花圃門口', '第 40 日去咗森林小屋'], frozen=True, state='awake', alive=False),
    dict(id='huozai', name='火仔', line='pet2', parentId='tuanrong', gen=2, bornDay=30, adultDay=None, series='C', form='S4C', pattern='火紋', move='小火花', story=['比波波遲兩日出世', '少年期，走 C 系', '最鍾意追螢火蟲', '未成年，仲喺度學嘢'], frozen=False, state='awake', alive=True),
    dict(id='bobo', name='波波', line='pet2', parentId='tuanrong', gen=2, bornDay=28, adultDay=36, series='A', form='A3', pattern='月紋', move='月光波', story=['團絨嘅第一隻細佬', '第 36 日成年，走 A 系', '學識咗祖傳月光波', '而家係屋企主寵'], frozen=False, state='awake', alive=True, main=True),
    dict(id='axing', name='阿星', line='tuanrong', parentId=None, gen=2, bornDay=31, adultDay=38, route='hop', form='evo_hop', pattern='星點', move='彈彈跳', story=['喺花圃執返嚟嘅蛋', '同波波一齊住咗好耐', '第 38 日成年，走跳跳路', '成日同火仔玩捉迷藏'], frozen=False, state='awake', alive=True),
    dict(id='doudou', name='豆豆', line='pet2', parentId='bobo', gen=3, bornDay=50, adultDay=None, series='A', form='S2', pattern='月紋', move='月光波', story=['波波嘅第一隻細佬', '童年期，瞓覺時間最長', '已經識少少月光波', '今晚喺屋企瞓緊'], frozen=False, state='sleep', alive=True),
    dict(id='egg_mie', name='咩咩', line='pet2', parentId=None, gen=3, bornDay=None, adultDay=None, series=None, form='egg', pattern=None, move=None, story=['未孵', '等你揀上一代', '', ''], frozen=False, state='egg', alive=False, egg=True),
]
MAIN = 'bobo'
def derive(fam):
    byid = {n['id']: n for n in fam}
    def anc(i):
        out = []; p = byid[i]['parentId']
        while p: out.append(p); p = byid[p]['parentId']
        return out
    rel = dict(parent=[], sibling=[], ancestor=[], house=[])
    for n in fam:
        if n['parentId']: rel['parent'].append([n['parentId'], n['id']])
    for a in fam:
        for b in fam:
            if a['id'] < b['id'] and a['parentId'] and a['parentId'] == b['parentId']: rel['sibling'].append(sorted([a['id'], b['id']]))
    for n in fam:
        for k, a in enumerate(anc(n['id'])):
            if k >= 1: rel['ancestor'].append([a, n['id'], k + 1])
    # 同屋：同時喺屋企（alive，非蛋）、唔同上一代、冇直系關係；只計主寵視角（GDD：由「我」睇出去）
    me = byid[MAIN]; mine = set(anc(MAIN))
    for n in fam:
        if n['id'] == MAIN or n.get('egg') or not n['alive']: continue
        if n['parentId'] == me['parentId'] or n['id'] in mine or MAIN in anc(n['id']): continue
        rel['house'].append([MAIN, n['id']])
    return rel
REL_D = derive(FAMILY)
# 位置（@3x，族譜區 126–1044）
ROWS = {0: 236, 1: 446, 2: 656, 3: 866}
XS = {'guangguang': 300, 'tuanrong': 205, 'yueyue': 440, 'huozai': 105, 'bobo': 300, 'axing': 480, 'doudou': 300, 'egg_mie': 480}
POSMODE = ['full']
def pos(i): n = next(f for f in FAMILY if f['id'] == i); return (292 if POSMODE[0] == 'direct' else XS[i]), ROWS[n['gen']]
SIB_COL = {'guangguang': None, 'tuanrong': 'mint', 'yueyue': 'mint', 'huozai': 'amber', 'bobo': 'amber'}
def tint_of(form):
    for p in (f'{ART}/sprites/series2/petglow_v3/{form}.json', f'{ART}/sprites/tuanrong/petglow_v3/{form}.json'):
        if os.path.exists(p): return json.load(open(p))['tints']['outer'], os.path.relpath(p, ART)
    return None, None
def glow_level(n):
    if n.get('egg') or not n['alive']: return 0.0
    return PG['states'].get(n['state'], 1.0)
# ============================================================== 7. 節點合成（runtime 同一套：aura → 框 → 窗底 → 頭像 sprite → 皇冠／章）
_FR = {}
def frame(kind, st):
    k = (kind, st)
    if k not in _FR: _FR[k] = node_frame(kind, st)
    return _FR[k]
def egg_sprite(k=4):
    rows = ["....xxxx....", "...xwwxxx...", "..xwwxxxxx..", "..xwxxxxxx..", ".xxxxxsxxxx.", ".xxxxsssxxx.", ".xxxxxsxxxx.", ".xxxxxxxxxx.", ".xxxxxxxxxx.", "..xxxxxxxx..", "...xxxxxx..."]
    pal = {'x': (232, 226, 210), 'w': (255, 255, 248), 's': (200, 180, 230)}; a = np.zeros((len(rows), 12, 4), np.uint8)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch in pal: a[y, x] = pal[ch] + (255,)
    return Image.fromarray(a).resize((12 * k * 2 // 2 * 1, len(rows) * k), Image.NEAREST)
def gray(im, k=.45):
    a = arr(im); g = a[..., :3] @ np.array([.3, .59, .11]); a[..., :3] = (g[..., None] * .8 + np.array((60, 66, 96)) * .2) * (1 - k) + np.array((40, 46, 72)) * k * .0 + g[..., None] * k * .55; return toim(a)
def avatar(n):
    """頭像 sprite（0/255）：用現有寵物 sprite，跟實際形態、實際狀態（瞓覺用 sleep 幀）"""
    if n.get('egg'): return egg_sprite()
    body = M3.face(n['form'], 'sleep' if n['state'] == 'sleep' else 'normal', k=4)[0]; return binarize(body)
def node_aura_layer(n):
    """寵物光 aura（光影層）＝ node_aura × petglow outer tint × petGlow(state)；瞓覺／入夢／退休／蛋 → None（0）"""
    g = glow_level(n); tint, _ = tint_of(n['form'])
    if g <= 0 or not tint: return None
    return soft_glow(ND + 110, ND + 110, hx(tint), .8 * g, 1.5)
def draw_node(bd, n, sel=False, dim=False, show_stamp=None, sib=None):
    cx, cy = pos(n['id']); kind = 'round' if n['line'] == 'tuanrong' else 'leaf'; live = n['alive'] and not n.get('egg')
    lay = new(ND + 120, ND + 120); oc = (ND + 120) // 2
    au = node_aura_layer(n)
    if au is not None: compc(lay, au, oc, oc)
    st = 'sel' if sel else ('live' if live else 'gray'); compc(lay, frame(kind, st), oc, oc)
    win = L._pbg('sleep' if n['state'] == 'sleep' else 'normal', WIN) if live else L._pbg('sleep', WIN)
    av = avatar(n); win.alpha_composite(av, ((WIN - av.width) // 2, (WIN - av.height) // 2 + 4))
    win = L.masked(win, win_mask(kind));
    if not live: win = gray(win)
    compc(lay, win, oc, oc)
    if n['state'] == 'sleep': lay.alpha_composite(L.IC('mini_sleep')[0] if os.path.exists(f'{L.KIT}/icons/mini_sleep@3x.png') else L.IC('sleep')[0], (oc + 26, oc - 60))
    if n.get('main'): cr = crown(); lay.alpha_composite(cr, (oc - cr.width // 2, oc - ND // 2 - cr.height + 8))
    if show_stamp:
        sp = stamp(show_stamp)[0].resize((44, 44), Image.LANCZOS); lay.alpha_composite(sp, (oc + ND // 2 - 34, oc - ND // 2 - 4))
    if sib: lay.alpha_composite(sib_dot(SIB_COLS[sib]), (oc - ND // 2 - 2, oc - ND // 2 + 2))
    if n.get('egg'): ImageDraw.Draw(lay).text((oc + 34, oc + 30), '?', font=L.F('sansb', 30), fill=A(C['goldhi']), anchor='mm')
    if dim: a = arr(lay); a[..., :3] = a[..., :3] * .38 + np.array(C['navy']) * .2; a[..., 3] *= .55; lay = toim(a)
    compc(bd, lay, cx, cy)
    sub = '未孵' if n.get('egg') else ('退休' if not n['alive'] else ('瞓緊' if n['state'] == 'sleep' else ''))
    nm = n['name'] + (f'・{sub}' if sub else '')
    if not dim: text(bd, nm, cx, cy + ND // 2 + 16, 'label', C['goldhi'] if n.get('main') else C['cream'], 'mm', sh=(0, 0, 0))
    M3.reg(f"node:{n['id']}", cx - ND / 2, cy - ND / 2, ND, ND)
# ============================================================== 8. 連線
def tile_line(bd, kind, x0, y0, x1, y1, alpha=1.0):
    """直／橫段，用 tile 鋪"""
    if y0 == y1:
        t = line_tile(kind, 'h'); xa, xb = sorted((x0, x1)); seg = new(int(xb - xa) + 1, t.height)
        for x in range(0, seg.width, t.width): seg.alpha_composite(t, (x, 0))
        if alpha < 1: seg = toim(arr(seg) * np.array([1, 1, 1, alpha]))
        comp(bd, seg, xa, y0 - t.height / 2)
    else:
        t = line_tile(kind, 'v'); ya, yb = sorted((y0, y1)); seg = new(t.width, int(yb - ya) + 1)
        for y in range(0, seg.height, t.height): seg.alpha_composite(t, (0, y))
        if alpha < 1: seg = toim(arr(seg) * np.array([1, 1, 1, alpha]))
        comp(bd, seg, x0 - t.width / 2, ya)
def gen_link(bd, pid, cid, alpha=1.0, kind='gen'):
    (px, py), (cx, cy) = pos(pid), pos(cid); my = (py + cy) / 2 + 8; y0 = py + ND / 2 + 34; y1 = cy - ND / 2 - 2
    my = max(my, y0 + 10)
    tile_line(bd, kind, px, y0, px, my, alpha); tile_line(bd, kind, px, my, cx, my, alpha); tile_line(bd, kind, cx, my, cx, y1 - 8, alpha)
    if alpha > .5: compc(bd, joint(), px, my); ah = arrow_head(); compc(bd, ah if alpha >= 1 else toim(arr(ah) * np.array([1, 1, 1, alpha])), cx, y1 - 8)
def sib_link(bd, a, b, alpha=1.0):
    (ax, ay), (bx, by) = pos(a), pos(b); xa, xb = sorted((ax, bx)); tile_line(bd, 'sib', xa + ND / 2, ay, xb - ND / 2, ay, alpha)
def house_link(bd, a, b, alpha=1.0):
    (ax, ay), (bx, by) = pos(a), pos(b); xa, xb = sorted((ax, bx)); tile_line(bd, 'house', xa + ND / 2, ay, xb - ND / 2, ay, alpha)
    if alpha > .5: compc(bd, house_icon(), (xa + xb) / 2, ay - 22)
def anc_link(bd, a, b, alpha=1.0):
    (ax, ay), (bx, by) = pos(a), pos(b); x = (ax + bx) / 2 + 0; tile_line(bd, 'anc', x, ay + ND / 2 + 60, x, by - ND / 2 - 30, alpha)
    for yy in np.linspace(ay + ND / 2 + 80, by - ND / 2 - 46, 4): compc(bd, L.flare_im(6, A(C['goldhi']), .9 * alpha), x, yy)
# ============================================================== 9. 畫面
def ui_top(bd, toggle='全家'):
    bd.alpha_composite(L.vgrad(W, 126, (10, 14, 32, 200), (10, 14, 32, 0)))
    L.backdrop(bd, 18, 30, 56, 56, L.circ_mask(56)); compc(bd, P('back_btn'), 46, 58); icon(bd, 'back', 46, 58); M3.reg('back', 18, 30, 56, 56)
    text(bd, '族譜', 122, 58, 'title', C['cream'], 'lm', sh=(0, 0, 0))
    x, y, w, h = 300, 34, 266, 48; L.backdrop(bd, x, y, w, h, L.rr_mask(w, h, h / 2)); comp(bd, P('seg_bg', w, h), x, y)
    on = 0 if toggle == '全家' else 1; comp(bd, P('seg_on', w // 2 - 4, h - 8), x + 4 + on * (w // 2), y + 4)
    for i, t in enumerate(('全家', '只睇直系')): text(bd, t, x + w / 4 + i * w / 2, y + h / 2, 'button', C['ink'] if i == on else C['cream'], 'mm')
    M3.reg('toggle', x, y, w, h)
def ui_bottom(bd, unlocked):
    y0 = 1044; bd.alpha_composite(L.vgrad(W, 222, (10, 14, 32, 0), (10, 14, 32, 230)), (0, y0))
    text(bd, f'族譜成就 {len(unlocked)}／6', 26, y0 + 22, 'label', C['goldhi'], 'lm', sh=(0, 0, 0))
    for i, (k, *_r) in enumerate(ACH):
        b = badge(k, k not in unlocked).resize((72, 72), Image.LANCZOS); compc(bd, b, 52 + i * 96, y0 + 82); M3.reg(f'ach:{k}', 52 + i * 96 - 36, y0 + 46, 72, 72)
    M3.button(bd, '截圖', 26, y0 + 142, 160, 'sec', small=True, ic='photo'); M3.button(bd, '叫佢出嚟', 206, y0 + 142, 200, 'pri', small=True, ic='heart'); M3.button(bd, '成就', 426, y0 + 142, 134, 'violet', small=True, ic='star')
def tree(bd, mode='full', focus=None, rewards=()):
    fam = FAMILY; byid = {n['id']: n for n in fam}
    direct = set([MAIN]); p = byid[MAIN]['parentId']
    while p: direct.add(p); p = byid[p]['parentId']
    direct |= {n['id'] for n in fam if n['parentId'] == MAIN}
    show = {n['id'] for n in fam} if mode == 'full' else direct; POSMODE[0] = mode
    rel_of = None
    if focus:
        rel_of = {focus}; [rel_of.update(e) for e in REL_D['parent'] + REL_D['sibling'] if focus in e]; [rel_of.update(e[:2]) for e in REL_D['ancestor'] + REL_D['house'] if focus in e]
    al = lambda a, b: 1.0 if (focus is None or (a in (focus,) or b in (focus,))) else .22
    if 'halo' in rewards: comp(bd, halo_top(), 0, 126)
    for a, b in REL_D['parent']:
        if a in show and b in show: gen_link(bd, a, b, al(a, b))
    for a, b in REL_D['sibling']:
        if a in show and b in show and byid[a]['gen'] == 2: sib_link(bd, a, b, al(a, b))
    if mode == 'full':
        for a, b in REL_D['house']: house_link(bd, a, b, al(a, b))
    for a, b, g in REL_D['ancestor']:
        if b == MAIN and a in show and mode == 'full': anc_link(bd, a, b, al(a, b))
    for n in fam:
        if n['id'] not in show: continue
        stp = 'zu' if n['id'] == 'guangguang' else ('chuan' if n['id'] in ('tuanrong', 'bobo') else ('wu' if [MAIN, n['id']] in REL_D['house'] else None))
        draw_node(bd, n, sel=(n['id'] == focus) or (focus is None and n.get('main') and mode == 'direct'), dim=bool(focus) and n['id'] not in rel_of, show_stamp=stp, sib=SIB_COL.get(n['id']) if mode == 'full' else None)
    if 'gold_frame' in rewards: comp(bd, gold_frame(), 0, 126)
    POSMODE[0] = 'full'
    if 'leaf' in rewards:
        lb = leaf_border()
        for y in range(146, 1044 - lb.height, lb.height): comp(bd, lb, 2, y); comp(bd, lb.transpose(Image.FLIP_LEFT_RIGHT), W - lb.width - 2, y)
def screen(name, warm, fn):
    L.SCREEN[0] = name; bd = BG[warm].copy(); bd.alpha_composite(LIGHT[warm]); fn(bd); return bd
def s_full(bd, rewards=('gold_frame',), unlocked=('first_home', 'three_gen', 'brothers')):
    ui_top(bd); tree(bd, 'full', rewards=rewards); ui_bottom(bd, unlocked)
    if 'three_gen' in unlocked: compc(bd, badge('three_gen').resize((64, 64), Image.LANCZOS), 540, 160)
def s_direct(bd): ui_top(bd, '只睇直系'); tree(bd, 'direct', rewards=('gold_frame',)); ui_bottom(bd, ('first_home', 'three_gen', 'brothers'))
def s_focus(bd):
    ui_top(bd); tree(bd, 'full', focus='tuanrong', rewards=('gold_frame',))
    y = 1010; x, w, h = 18, 549, 238; M3.panel(bd, 'panel', x, y, w, h)
    M3.mini_face(bd, x + 64, y + 66, 'evo_still_tide', 'normal', k=3); text(bd, '團絨', x + 120, y + 46, 'h2', C['goldhi'], 'lm'); text(bd, '第 1 代・靜光潮路・仲喺屋企', x + 120, y + 82, 'caption', C['mute'], 'lm')
    text(bd, '上一代：光光　下一代：波波、火仔', x + 26, y + 130, 'body', C['cream'], 'lm'); text(bd, '兄弟姊妹：月月', x + 26, y + 164, 'body', C['cream'], 'lm')
    M3.button(bd, '睇佢一生', x + w - 196, y + 22, 176, 'pri', small=True, ic='family_tree')
def s_card(bd):
    ui_top(bd); tree(bd, 'full', rewards=('gold_frame',)); M3.veil(bd)
    x, y, w, h = 18, 150, 549, 940; M3.panel(bd, 'panel', x, y, w, h); M3.close_btn(bd, x + w - 34, y + 34)
    M3.portrait(bd, x + 26, y + 30, 'A3', 'happy', k=5); compc(bd, crown(), x + 92, y + 30)
    text(bd, '波波', x + 166, y + 56, 'title', C['goldhi'], 'lm'); text(bd, '第 2 代・A 系・主寵', x + 166, y + 100, 'caption', C['mute'], 'lm')
    text(bd, '遺傳自：團絨', x + 166, y + 136, 'value', C['cream'], 'lm'); comp(bd, stamp('chuan')[0].resize((44, 44), Image.LANCZOS), x + 330, y + 112)
    yy = y + 196; comp(bd, P('hairline', w - 52, 2) if 'hairline' in L.PARTS else L.hline_im(w - 52, A(C['gold'], .6)), x + 26, yy)
    rows = [('pattern', '花紋', '月紋', '團絨'), ('trick', '招式', '月光波', '光光')]
    for i, (ic, k, v, src) in enumerate(rows):
        ry = yy + 44 + i * 58; icon(bd, ic, x + 46, ry); text(bd, k, x + 76, ry, 'label', C['mute'], 'lm'); text(bd, v, x + 150, ry, 'value', C['cream'], 'lm')
        ex = x + 150 + tw(v, 'value') + 10
        if ic == 'trick': comp(bd, heir_tag(), ex, ry - 16); ex += 106
        compc(bd, inherit_arrow(), ex + 14, ry); text(bd, f'出自 {src}', ex + 32, ry, 'caption', C['goldhi'], 'lm')
    sy = yy + 170; text(bd, '佢嘅故事', x + 26, sy, 'h2', C['goldhi'], 'lm')
    for i, s in enumerate(FAMILY[4]['story']): compc(bd, L.diamond_im(4, A(C['gold'])), x + 36, sy + 44 + i * 40); text(bd, s, x + 52, sy + 44 + i * 40, 'body', C['cream'], 'lm')
    ly = sy + 230; text(bd, '睇佢一生', x + 26, ly, 'h2', C['goldhi'], 'lm')
    for i, f in enumerate(('egg', 'S1', 'S2', 'S4A', 'A1', 'A3')):
        cx = x + 64 + i * 84; fy = ly + 128; compc(bd, soft_glow(84, 22, C['gold'], .5, 1.2), cx, fy)
        sp = full_body(f)
        sil = sp if i == 5 else toim(np.dstack([np.zeros(sp.size[::-1] + (3,)) + np.array((214, 190, 130)), arr(sp)[..., 3]]))   # 剪影（金），最後一格＝而家（彩色）
        comp(bd, sil, cx - sil.width / 2, fy - sil.height + 4); text(bd, ('蛋', '幼年', '童年', '少年', '成年', '而家')[i], cx, fy + 30, 'caption', C['mute'], 'mm')
    by = y + h - 92; M3.button(bd, '叫佢出嚟', x + 26, by, 240, 'pri', ic='heart'); M3.button(bd, '玩招式', x + 286, by, 237, 'sec', ic='trick')
def full_body(f, k=2):
    """全身 sprite（0/255）：寵物 canvas 裁 alpha bbox ×k"""
    if f == 'egg': return egg_sprite(2)
    c, _ = M3.M.pet_canvas(f, 'normal'); c = binarize(c); c = c.crop(c.getbbox()); return c.resize((c.width * k, c.height * k), Image.NEAREST)
def _sil_disc(d=74):
    im = new(d, d); im.alpha_composite(L.masked(L.vgrad(d, d, A(C['navy3'], .9), A(C['navy'], .9)), L.circ_mask(d))); im.alpha_composite(L.ring_im(d - 4, A(C['gold'], .7), 1.2)); return im
def s_achievements(bd):
    ui_top(bd); tree(bd, 'full', rewards=('gold_frame',)); M3.veil(bd)
    x, y, w, h = 18, 136, 549, 1110; M3.panel(bd, 'panel', x, y, w, h); M3.title(bd, '族譜成就', W / 2, y + 48); M3.close_btn(bd, x + w - 34, y + 34)
    un = ('first_home', 'three_gen', 'brothers')
    for i, (k, zh, cond, rew) in enumerate(ACH):
        cx0 = x + 22 + (i % 2) * 258; cy0 = y + 100 + (i // 2) * 330; cw, ch = 248, 316; M3.panel(bd, 'panel_inset_sel' if k in un else 'panel_inset', cx0, cy0, cw, ch, shadow=False)
        compc(bd, badge(k, k not in un), cx0 + cw / 2, cy0 + 76); text(bd, zh, cx0 + cw / 2, cy0 + 156, 'h2', C['goldhi'] if k in un else C['cream'], 'mm')
        text(bd, cond, cx0 + cw / 2, cy0 + 192, 'caption', C['mute'], 'mm')
        text(bd, '獎勵', cx0 + cw / 2, cy0 + 232, 'label', C['gold'], 'mm'); lines = [rew] if tw(rew, 'caption') < cw - 24 else [rew[:len(rew) // 2 + 1], rew[len(rew) // 2 + 1:]]
        for j, t in enumerate(lines): text(bd, t, cx0 + cw / 2, cy0 + 262 + j * 26, 'caption', C['cream'], 'mm')
        if k in un: compc(bd, P('stamp_done'), cx0 + cw - 34, cy0 + 30) if 'stamp_done' in L.PARTS else None
def s_full_all(bd): s_full(bd, rewards=('gold_frame', 'halo', 'leaf'), unlocked=tuple(k for k, *_ in ACH))
def s_normal(bd): s_full(bd, rewards=(), unlocked=('first_home',))
def s_egg_pick(bd):
    ui_top(bd); tree(bd, 'full', rewards=('gold_frame',)); M3.veil(bd)
    x, y, w, h = 18, 700, 549, 548; M3.panel(bd, 'panel', x, y, w, h); M3.title(bd, '揀咩咩嘅上一代', W / 2, y + 48); M3.close_btn(bd, x + w - 34, y + 34)
    for i, f in enumerate(('bobo', 'tuanrong', 'axing')):
        n = next(q for q in FAMILY if q['id'] == f); cx = x + 96 + i * 178; cy = y + 190
        compc(bd, frame('round' if n['line'] == 'tuanrong' else 'leaf', 'sel' if i == 0 else 'live'), cx, cy)
        win = L._pbg('normal', WIN); av = avatar(n); win.alpha_composite(av, ((WIN - av.width) // 2, (WIN - av.height) // 2 + 4)); compc(bd, L.masked(win, win_mask('round' if n['line'] == 'tuanrong' else 'leaf')), cx, cy)
        text(bd, n['name'], cx, cy + 92, 'label', C['goldhi'] if i == 0 else C['cream'], 'mm'); text(bd, f"{n['pattern']}・{n['move']}", cx, cy + 122, 'caption', C['mute'], 'mm')
    text(bd, '揀咗之後唔可以改，佢會遺傳花紋同招式。', W / 2, y + 384, 'caption', C['mute'], 'mm'); M3.button(bd, '就揀波波', x + 124, y + 430, 300, 'pri', ic='egg_kid')
SCREENS = [('ft_full', True, s_full, '全家（暖色背景，三代同堂已解鎖；金框）'), ('ft_direct', True, s_direct, '只睇直系'), ('ft_focus', True, s_focus, '撳節點：關係線高亮、其他變暗＋底部資料'),
           ('ft_card', True, s_card, '寵物卡：遺傳自＋箭咀、祖傳、4 行故事、睇佢一生 6 剪影'), ('ft_achievements', True, s_achievements, '6 成就（3 解鎖／3 未解鎖）'),
           ('ft_full_all', True, s_full_all, '6 成就全開：光環＋葉形邊＋金框'), ('ft_normal', False, s_normal, '未三代同堂：普通深藍背景'), ('ft_egg_pick', True, s_egg_pick, '未孵蛋揀上一代')]
# ============================================================== 10. 輸出
def main():
    global BG, LIGHT
    import shutil
    for sub in ('parts', 'bg', 'fx', 'mockups'):
        if os.path.isdir(f'{OUT}/{sub}'): shutil.rmtree(f'{OUT}/{sub}')
    parts = {}
    def P_(name, im, layer, desc, nine=None, **kw):
        parts[name] = dict(file=save(im, f'parts/{name}@3x.png'), size=list(im.size), layer=layer, desc=desc, **({'nineSlice': nine} if nine else {}), **kw)
    for kind, zh in (('round', '團絨圓框'), ('leaf', '細佬葉框')):
        for st, sz in (('live', '仲喺屋企（亮）'), ('gray', '退休／未出（灰）'), ('sel', '撳中（金光）')): P_(f'node_{kind}_{st}', node_frame(kind, st), 'ui', f'{zh}・{sz}；頭像窗中心 {WIN}×{WIN}')
        m = win_mask(kind); mi = new(WIN, WIN, (255, 255, 255, 255)); mi.putalpha(m); P_(f'node_{kind}_mask', mi, 'ui', f'{zh}頭像窗遮罩（窗底＋頭像用）')
    P_('node_crown', crown(), 'sprite', '主寵皇冠（像素 ×3，0/255）')
    P_('node_aura', soft_glow(ND + 110, ND + 110, (255, 255, 255), .8, 1.5), 'light', '寵物光 aura（白；runtime tint＝petglow outer × petGlow）')
    stamps_meta = {}
    for k in SEAL:
        im, ch, bg, fg = stamp(k); P_(f'stamp_{k}', im, 'ui', f'關係章「{ch}」'); stamps_meta[k] = dict(char=ch, bg=list(bg), fg=list(fg), contrast=round((max(L.lum(fg), L.lum(bg)) + .05) / (min(L.lum(fg), L.lum(bg)) + .05), 2))
    for k, c in SIB_COLS.items(): P_(f'sib_dot_{k}', sib_dot(c), 'ui', f'兄弟同色圓點（{k}）')
    P_('icon_house', house_icon(), 'ui', '同屋細屋 icon（線中間）')
    P_('inherit_arrow', inherit_arrow(), 'ui', '遺傳自：細箭咀（指返出處）')
    for k in ('gen', 'sib', 'house', 'anc'):
        for o in ('h', 'v'): P_(f'line_{k}_{o}', line_tile(k, o), 'light', f"{REL[k]['zh']}線 tile（{'橫' if o == 'h' else '直'}，repeat）", tile=o)
    P_('line_arrow', arrow_head(), 'ui', '直系線箭咀（向下）'); P_('line_joint', joint(), 'ui', '直系線分叉菱形')
    for k, zh, cond, rew in ACH:
        P_(f'ach_{k}', badge(k), 'ui', f'成就徽章「{zh}」'); P_(f'ach_{k}_locked', badge(k, True), 'ui', f'成就徽章「{zh}」未解鎖')
    P_('reward_gold_frame', gold_frame(), 'ui', '第一個家：族譜金框（9-slice，蓋族譜區 126–1044）', nine=[40, 40, 40, 40])
    P_('reward_sibling_frame', sibling_frame(), 'ui', '兄弟情：兄弟合照框（兩個窗 d96，中心 (90,87)／(210,87)）')
    P_('reward_halo_top', halo_top(), 'light', '九光齊：族譜頂光環（九路線色）')
    P_('reward_leaf_border', leaf_border(), 'ui', '八系齊：葉形邊 tile（左；右邊 flipX）', tile='v')
    P_('reward_ancestral_tag', heir_tag(), 'ui', '招式傳人：招式名後「祖傳」牌')
    P_('egg_unhatched', egg_sprite(), 'sprite', '未孵蛋頭像（像素 ×4，0/255）')
    BG = {False: background(False), True: background(True)}; LIGHT = {False: light_add(False), True: light_add(True)}
    bgs = {}
    for warm, nm in ((False, 'bg_normal'), (True, 'bg_warm')):
        bgs[nm] = dict(file=save(BG[warm].convert('RGB'), f'bg/{nm}@3x.png'), light=save(LIGHT[warm], f'bg/{nm}_light_add@3x.png'), lightBlend='lighter', lightSway=dict(px=6, sec=9))
    bgs['bg_warm']['unlock'] = 'three_gen'
    fx = save(particles(), 'fx/particles@3x.png')
    emit = dict(sheet=fx, cell=[24, 24], rows=dict(mote=0, twinkle=1, heart=2), emitters=[
        dict(name='bg_mote', row='mote', rate=0.8, life=[4, 7], area=[0, 126, 585, 918], vy=[-10, -4], fps=6, alpha=.8, petGlow=False, note='場景粒子，唔受 petGlow'),
        dict(name='line_flow', row='twinkle', rate=1.2, life=[1.2, 1.6], along='line_gen', speed=60, fps=8, note='直系線上金光流動（撳節點時只喺高亮線）'),
        dict(name='node_aura_mote', row='mote', rate=.5, life=[2, 3], around='node', radius=74, petGlow=True, note='寵物光點 × petGlow（瞓覺 0）'),
        dict(name='portrait_heart', row='heart', burst=5, life=[.8, 1.1], vy=[-60, -30], fps=8, trigger='touch_portrait', petGlow=False, note='摸肖像：眨眼＋心心')])
    json.dump(emit, open(f'{OUT}/fx/emitters.json', 'w'), ensure_ascii=False, indent=1)
    # demo family.json
    fam_out = []
    for n in FAMILY:
        d = {k: n.get(k) for k in ('id', 'line', 'parentId', 'gen', 'bornDay', 'adultDay', 'pattern', 'move', 'story', 'frozen')}
        d['route' if n['line'] == 'tuanrong' else 'series'] = n.get('route') if n['line'] == 'tuanrong' else n.get('series')
        d.update(name=n['name'], form=n['form'], state=n['state'], alive=n['alive'], main=bool(n.get('main')), egg=bool(n.get('egg'))); fam_out.append(d)
    json.dump(dict(note='demo（GDD §1.6 欄位；兄弟／祖輩由 parentId 推，同屋由主寵視角推）', main=MAIN, nodes=fam_out, derived=REL_D), open(f'{OUT}/family_demo.json', 'w'), ensure_ascii=False, indent=1)
    # mockups
    L.TEXTLOG.clear(); M3.LAY.clear(); M3.HITS.clear(); shots = {}
    for nm, warm, fn, desc in SCREENS:
        im = screen(nm, warm, fn); assert im.size == (W, H); shots[nm] = dict(file=save(im.convert('RGB'), f'mockups/{nm}_3x.png'), bg='bg_warm' if warm else 'bg_normal', desc=desc); print('ok', nm)
    json.dump(L.TEXTLOG, open(f'{OUT}/mockups/texts.json', 'w'), ensure_ascii=False, indent=0)
    nodes_glow = {n['id']: dict(state=n['state'], petGlow=glow_level(n), tint=tint_of(n['form'])[0], tintSrc=tint_of(n['form'])[1]) for n in FAMILY}
    entry = dict(
        name='familytree_v3', batch=7, spec='V3-A：金光深藍磨砂＋1.5px 金幼線；Noto CJK TC（最細 18@3x）；對比 ≥4.5；@3x 烘焙光影＋粒子；sprite 0/255，UI／光影層真 alpha；唔用 Fusion Pixel',
        gdd='docs-gdd/family-work-scenes-v1.md §1、§2.1（族譜）', canvas=[W, H], scale=3, bands=BANDS, split=[0, 42, 348, 422],
        layers=['bg', 'bg_light_add(lighter)', 'line(light)', 'node_aura(light×petGlow)', 'node frame(ui)', 'window bg＋avatar sprite', 'crown／stamp／dot', 'labels', 'ui top/bottom', 'fx'],
        inPartText=[dict(part=f'stamp_{k}', text=v['char'], fg=v['fg'], bg=v['bg'], px=34) for k, v in stamps_meta.items()] + [
            dict(part='ach_three_gen', text='三代', fg=[255, 246, 232], bg=list(C['red2']), px=22), dict(part='ach_move_heir', text='傳', fg=[120, 60, 20], bg=list(C['goldhi']), px=26),
            dict(part='reward_ancestral_tag', text='祖傳', fg=list(C['ink']), bg=list(C[L.ACCENT['pri']]), px=18), dict(part='reward_sibling_frame', text='兄弟', fg=list(C['ink']), bg=list(C['rose']), px=18)],
        parts=parts, backgrounds=bgs, fx='fx/emitters.json', stamps=stamps_meta,
        relations={k: dict(zh=v['zh'], line=f"line_{k}", mark=v['mark']) for k, v in REL.items()},
        nodeRules=dict(sizePx=ND, windowPx=WIN, avatar='現有寵物 sprite（build_ui_hd2d_v3_mockups.face k=4，跟實際形態＋狀態；瞓覺用 sleep 幀）', frame=dict(tuanrong='node_round_*', pet2='node_leaf_*'),
                       state=dict(live='alive 且已孵', gray='退休（frozen 或 alive=false）或未孵蛋：框灰＋窗去飽和', sel='撳中'), crown='main=true', dimOthers=dict(alpha=.55, rgbMul=.38, lineAlpha=.22, note='撳節點：佢嘅關係線同節點保持，其他變暗'),
                       stamp=dict(chuan='有上一代（傳）—由主寵視角：上一代／自己', zu='祖輩（隔 ≥2 代）', wu='同屋（冇血緣）'), siblingDot='同上一代＝同色圓點'),
        petGlow=dict(source='ui/kit_hd2d_v3/layout_hd2d_v3.json#petGlow', states=PG['states'], fadeOut=PG['fadeOut'], fadeIn=PG['fadeIn'], appliesTo=['node_aura', 'node_aura_mote'],
                     grayNodes=0.0, note='族譜節點 aura＝寵物光；瞓覺／入夢 0，退休／蛋 0；背景、線光、成就光環屬場景光，唔受影響', nodes=nodes_glow),
        toggle=dict(options=['全家', '只睇直系'], direct='主寵＋上一代鏈＋下一代'),
        achievements=[dict(id=k, zh=zh, cond=cond, reward=rew, badge=f'ach_{k}', locked=f'ach_{k}_locked') for k, zh, cond, rew in ACH],
        rewards=dict(first_home='reward_gold_frame', three_gen=['ach_three_gen', 'bg_warm'], brothers='reward_sibling_frame', nine_light='reward_halo_top', eight_series='reward_leaf_border', move_heir='reward_ancestral_tag'),
        actions=['撳節點（高亮關係）', '摸肖像（眨眼＋心心 portrait_heart）', '玩遺傳招式', '叫佢出嚟', '未孵蛋揀上一代', '截圖'], forbidden=['刪節點', '改名', '改關係'],
        demo='family_demo.json', mockups=shots, layout=M3.LAY, hits=M3.HITS, texts='mockups/texts.json')
    json.dump(entry, open(f'{OUT}/familytree_v3.json', 'w'), ensure_ascii=False, indent=1)
    print('parts', len(parts), 'mockups', len(shots), 'texts', len(L.TEXTLOG))
if __name__ == '__main__': main()
