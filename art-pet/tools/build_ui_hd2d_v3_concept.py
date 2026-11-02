# 《微光小圃》HD-2D v3 概念（現代 2026 HD-2D）— 遊美 2026-11-02
# 場景／團絨／icon 保持像素（1x art ×3 nearest），之上疊 @3x 原生：景深、體積光、bloom、粒子、光點、調色；
# UI = @3x 原生平滑（漸變、柔陰影、磨砂玻璃、幼線、Noto Sans/Serif CJK TC［OFL］）。只係概念，唔郁正式 kit。
# 純 Pillow／numpy 程序化，冇 AI 圖。
import os, sys, json, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_ui_hd2d_v2_mockups as M
import build_ui_hd2d_v2_concept as CC
import ui_hd2d_kit as K
import hd2d_v2_px as X
OUT = f'{X.ART}/ui/style_ref/hd2d_v3'; os.makedirs(OUT, exist_ok=True)
S = 3; W, H = 195 * S, 422 * S; SS = 4
FD = '/usr/share/fonts/opentype/noto'
def F(kind, sz):
    f = {'sans': 'NotoSansCJK-Regular.ttc', 'sansb': 'NotoSansCJK-Bold.ttc', 'serif': 'NotoSerifCJK-Bold.ttc', 'serifr': 'NotoSerifCJK-Regular.ttc'}[kind]
    return ImageFont.truetype(f'{FD}/{f}', sz, index=3)   # index 3 = TC
# ---------------- 字級（@3x mock px；CSS px = px×(360/585) 細機 / ×(390/585) 標準機）
TYPE = {
 'title':   ('serif', 30, '名／標題'),
 'h2':      ('sansb', 24, '彈窗標題'),
 'body':    ('sans', 21, '內文／泡泡'),
 'value':   ('sansb', 21, '數值'),
 'button':  ('sansb', 20, '按鈕字'),
 'caption': ('sans', 18, '細字／標籤（最細）'),
}
def tf(role, kind=None): k, sz, _ = TYPE[role]; return F(kind or k, sz)
# ---------------- 色
C = dict(ink=(36, 34, 52), ink2=(88, 86, 108), cream=(250, 244, 230), gold=(232, 200, 128), gold2=(196, 156, 84), goldhi=(255, 236, 184),
         navy=(18, 24, 48), navy2=(30, 40, 74), rose=(240, 126, 150), sky=(110, 190, 230), amber=(246, 176, 72), violet=(156, 132, 230), mint=(120, 206, 160), red=(232, 84, 84))
NEED = [('feed', 'amber', .22), ('heart', 'rose', .60), ('clean', 'sky', .55), ('sleep', 'violet', .15)]
CONTRAST = []
def lum(c):
    c = np.asarray(c, float)[..., :3] / 255; c = np.where(c <= .03928, c / 12.92, ((c + .055) / 1.055) ** 2.4); return c @ np.array([.2126, .7152, .0722])
# ---------------- 基本畫具
def A(c, a): return tuple(c[:3]) + (int(a * 255),)
def rr_mask(w, h, r):
    m = Image.new('L', (w * SS, h * SS)); ImageDraw.Draw(m).rounded_rectangle([0, 0, w * SS - 1, h * SS - 1], r * SS, fill=255); return m.resize((w, h), Image.LANCZOS)
def circ_mask(d):
    m = Image.new('L', (d * SS, d * SS)); ImageDraw.Draw(m).ellipse([0, 0, d * SS - 1, d * SS - 1], fill=255); return m.resize((d, d), Image.LANCZOS)
def vgrad(w, h, c0, c1):
    t = np.linspace(0, 1, h)[:, None, None]; a = np.array(c0, float) * (1 - t) + np.array(c1, float) * t
    return Image.fromarray(np.repeat(a, w, 1).clip(0, 255).astype(np.uint8), 'RGBA')
def paste_mask(bd, im, mask, xy):
    im = im.copy(); a = np.array(im); a[..., 3] = (a[..., 3].astype(float) * np.array(mask) / 255).astype(np.uint8); bd.alpha_composite(Image.fromarray(a), (int(xy[0]), int(xy[1])))
def shadow(bd, mask, xy, blur=10, dy=6, a=.35):
    pad = blur * 3; w, h = mask.size; m = Image.new('L', (w + 2 * pad, h + 2 * pad)); m.paste(mask, (pad, pad)); m = m.filter(ImageFilter.GaussianBlur(blur))
    sh = Image.new('RGBA', m.size, (8, 10, 24, 0)); sh.putalpha(m.point(lambda v: int(v * a))); bd.alpha_composite(sh, (int(xy[0] - pad), int(xy[1] - pad + dy)))
def stroke(bd, box, fn):
    x0, y0, x1, y1 = [int(v) for v in box]; w, h = x1 - x0, y1 - y0
    L = Image.new('RGBA', (w * SS, h * SS)); fn(ImageDraw.Draw(L), SS, w, h); bd.alpha_composite(L.resize((w, h), Image.LANCZOS), (x0, y0))
def hair_rr(bd, box, r, col, lw=1.5, inset=0):
    stroke(bd, box, lambda d, s, w, h: d.rounded_rectangle([inset * s + lw * s / 2, inset * s + lw * s / 2, (w - inset) * s - lw * s / 2 - 1, (h - inset) * s - lw * s / 2 - 1], (r - inset) * s, outline=col, width=max(1, int(lw * s))))
def hair_circ(bd, cx, cy, d, col, lw=1.5):
    stroke(bd, (cx - d / 2 - 2, cy - d / 2 - 2, cx + d / 2 + 2, cy + d / 2 + 2), lambda dr, s, w, h: dr.ellipse([2 * s + lw * s / 2, 2 * s + lw * s / 2, (d + 2) * s - lw * s / 2, (d + 2) * s - lw * s / 2], outline=col, width=max(1, int(lw * s))))
def arc(bd, cx, cy, d, col, lw, a0, a1):
    stroke(bd, (cx - d / 2 - 2, cy - d / 2 - 2, cx + d / 2 + 2, cy + d / 2 + 2), lambda dr, s, w, h: dr.arc([2 * s, 2 * s, (d + 2) * s, (d + 2) * s], a0, a1, fill=col, width=int(lw * s)))
def hline(bd, x0, x1, y, col, lw=1.5, fade=True):
    w = int(x1 - x0); L = Image.new('RGBA', (w, 4)); a = np.zeros((4, w, 4), np.uint8); a[..., :3] = col[:3]
    t = np.linspace(0, 1, w); f = np.minimum(1, np.minimum(t, 1 - t) * 8) if fade else np.ones(w)
    base = col[3] if len(col) > 3 else 255; a[1, :, 3] = (base * f).astype(np.uint8); a[2, :, 3] = (base * f * (lw - 1)).clip(0, 255).astype(np.uint8)
    bd.alpha_composite(Image.fromarray(a), (int(x0), int(y - 1.5)))
def diamond(bd, cx, cy, r, col):
    stroke(bd, (cx - r - 1, cy - r - 1, cx + r + 2, cy + r + 2), lambda d, s, w, h: d.polygon([((r + 1) * s, 1 * s), ((2 * r + 1) * s, (r + 1) * s), ((r + 1) * s, (2 * r + 1) * s), (1 * s, (r + 1) * s)], fill=col))
def glow(bd, cx, cy, r, col, a=.6):
    d = int(r * 2); g = np.zeros((d, d, 4)); yy, xx = np.mgrid[0:d, 0:d]; q = np.exp(-(((xx - r) ** 2 + (yy - r) ** 2) / (r * r / 2.5)))
    g[..., :3] = col[:3]; g[..., 3] = q * a * 255; bd.alpha_composite(Image.fromarray(g.astype(np.uint8)), (int(cx - r), int(cy - r)))
def flare(bd, cx, cy, r, col, a=.6):  # 四芒星光（@3x 幼）
    L = Image.new('RGBA', (int(r * 2 + 4), int(r * 2 + 4)), A(col, 0)); d = ImageDraw.Draw(L); c = r + 2
    for i in range(int(r)):
        al = int(255 * a * (1 - i / r) ** 2); d.point([(c + i, c), (c - i, c), (c, c + i), (c, c - i)], fill=A(col, al / 255))
    bd.alpha_composite(L.filter(ImageFilter.GaussianBlur(.7)), (int(cx - c), int(cy - c)))
def addlight(bd, rgb_add):  # 加色（additive）
    a = np.array(bd).astype(float); a[..., :3] += rgb_add; bd.paste(Image.fromarray(np.dstack([a[..., :3].clip(0, 255), a[..., 3]]).astype(np.uint8)))
def text(bd, t, x, y, role='body', col=C['cream'], anchor='la', kind=None, sh=None, check=True):
    f = tf(role, kind); d = ImageDraw.Draw(bd); bb = d.textbbox((x, y), t, font=f, anchor=anchor)
    bg = np.array(bd.crop(bb))[..., :3]
    if sh:  # 柔陰影（現代：模糊 drop shadow，唔係硬描邊）
        L = Image.new('RGBA', bd.size); ImageDraw.Draw(L).text((x, y + 2), t, font=f, anchor=anchor, fill=sh); bd.alpha_composite(L.filter(ImageFilter.GaussianBlur(2.2)))
        L2 = Image.new('RGBA', bd.size); ImageDraw.Draw(L2).text((x, y + 1), t, font=f, anchor=anchor, fill=A(sh, .55)); bd.alpha_composite(L2)
    d.text((x, y), t, font=f, anchor=anchor, fill=col)
    if check and bg.size:
        cr = (max(lum(col), lum(bg).max()) + .05) / (min(lum(col), lum(bg).max()) + .05)
        cr = np.percentile((np.maximum(lum(col), lum(bg)) + .05) / (np.minimum(lum(col), lum(bg)) + .05), 5)
        CONTRAST.append((STYLE[0], t, role, TYPE[role][1], round(float(cr), 2)))
    return bb
STYLE = ['?']
def px(im, k): return im.resize((im.width * k, im.height * k), Image.NEAREST)
def icon(name, k=2): return px(M.IC(name), k)
def putc(bd, im, cx, cy): bd.alpha_composite(im, (int(round(cx - im.width / 2)), int(round(cy - im.height / 2))))

# ================================================================ 場景：像素層 ×3 + @3x 原生後期
def layers_1x(state='hungry'):
    g = json.load(open(f'{K.H3}/grade.json'))
    lm = np.asarray(Image.open(f'{K.H3}/lightmap.png').convert('RGB')).astype(float) / 255
    la = np.asarray(Image.open(f'{K.H3}/light_add.png').convert('RGB')).astype(float)
    eb = np.asarray(Image.open(f'{K.H3}/emissive_blur.png').convert('RGB')).astype(float)
    tint = np.array(K.hx(g['petTint'])[:3]) / 255 * np.array(K.hx(g['ambientTint'])[:3]) / 255
    def lit(im): a = np.asarray(im).astype(float); a[..., :3] *= tint; return Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')
    pets = []; m, mi = X.compose_pet(CC.MAIN['form'], state, CC.MAIN['acc']); pets.append((lit(m), mi, 97, 292))
    k, ki = X.compose_pet(CC.KID['form'], 'happy', pattern_from=CC.KID['pattern_from']); pets.append((lit(k), ki, 58, 300))
    out = {}
    for L in ['sky', 'far', 'mid', 'fore']:
        im = K._ld(f'{K.H3}/{L}.png')
        if L == 'mid':
            for (p, inf, fx, fy) in sorted(pets, key=lambda t: t[3]): im.alpha_composite(p, (int(round(fx + 14 - inf['pivot'][0])), int(round(fy + 12 - inf['pivot'][1]))))
        a = np.asarray(im).astype(float); a[..., :3] = a[..., :3] * lm + la + eb * g['bloom']['intensity']
        out[L] = Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA').crop((14, 12, 14 + 195, 12 + 422))
    return out, pets
def grade(a, warm=1.0, lift=0.0, sat=1.08, contrast=1.06):
    a = a / 255.; l = a @ np.array([.299, .587, .114]); a = l[..., None] + (a - l[..., None]) * sat
    a = (a - .5) * contrast + .5
    sh = np.array([-.01, .0, .03]); hi = np.array([.05, .02, -.04]) * warm; t = l[..., None]
    a = a + sh * (1 - t) + hi * t; a = a * (1 - lift) + lift; return (a.clip(0, 1) * 255)
def rays(w, h, src, col, strength, seed=3, spread=(.2, 1.4), falloff=1100):
    rnd = np.random.RandomState(seed); yy, xx = np.mgrid[0:h, 0:w].astype(float); ang = np.arctan2(yy - src[1], xx - src[0]); d = np.hypot(xx - src[0], yy - src[1])
    n = np.zeros_like(ang)
    for k in (9, 17, 31, 53, 77): n += np.sin(ang * k + rnd.rand() * 6.28) * (1 / k ** .3)
    n = ((n - n.min()) / (n.max() - n.min())) ** 3
    win = np.clip((ang - spread[0]) / .2, 0, 1) * np.clip((spread[1] - ang) / .2, 0, 1)
    f = n * win * np.exp(-d / falloff) * strength; return f[..., None] * np.array(col, float)
def screen(a, b): a = a.clip(0, 255) / 255; b = b.clip(0, 255) / 255; return (1 - (1 - a) * (1 - b)) * 255
def bloom(a, thr=.72, r=(6, 22), k=(.35, .45), tint=(1, .93, .8)):
    l = (a @ np.array([.299, .587, .114])) / 255; m = np.clip((l - thr) / (1 - thr), 0, 1)[..., None] * a
    im = Image.fromarray(m.clip(0, 255).astype(np.uint8)); add = 0
    for rr_, kk in zip(r, k): add = add + np.asarray(im.filter(ImageFilter.GaussianBlur(rr_))).astype(float) * kk
    return add * np.array(tint)
def particles(bd, rect, n, seed, cols, rmin=1.2, rmax=3.2, bokeh=0, bmin=10, bmax=26, glowa=.55):
    rnd = random.Random(seed); x0, y0, x1, y1 = rect; L = Image.new('RGBA', bd.size, cols[0] + (0,)); d = ImageDraw.Draw(L)
    for i in range(bokeh):  # 失焦大光圈
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1); r = rnd.uniform(bmin, bmax); c = rnd.choice(cols)
        d.ellipse([x - r, y - r, x + r, y + r], fill=A(c, rnd.uniform(.06, .16)), outline=A(c, rnd.uniform(.12, .22)), width=2)
    bd.alpha_composite(L.filter(ImageFilter.GaussianBlur(1.6)))
    G = Image.new('RGBA', bd.size, cols[0] + (0,)); P = Image.new('RGBA', bd.size, (255, 255, 240, 0)); dg = ImageDraw.Draw(G); dp = ImageDraw.Draw(P)
    for i in range(n):  # 光點：核心 + 柔光暈
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1); r = rnd.uniform(rmin, rmax); c = rnd.choice(cols)
        dg.ellipse([x - r * 4, y - r * 4, x + r * 4, y + r * 4], fill=A(c, glowa * rnd.uniform(.4, 1)))
        dp.ellipse([x - r, y - r, x + r, y + r], fill=A((255, 255, 240), rnd.uniform(.7, 1)))
    bd.alpha_composite(G.filter(ImageFilter.GaussianBlur(5))); bd.alpha_composite(P.filter(ImageFilter.GaussianBlur(.6)))
def vignette(a, k=.28, cx=.5, cy=.45):
    h, w = a.shape[:2]; yy, xx = np.mgrid[0:h, 0:w]; d = np.hypot((xx / w - cx) * 1.2, (yy / h - cy)) ; v = 1 - k * np.clip((d - .3) / .5, 0, 1) ** 1.6
    return a * v[..., None]
def garden3x(mood='A', state='hungry', pet_glow=1.0):
    L, pets = layers_1x(state); g = json.load(open(f'{K.H3}/grade.json'))
    dof = {'sky': 0, 'far': 0, 'mid': 0, 'fore': 0}
    bd = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    for k in ['sky', 'far', 'mid', 'fore']:
        im = px(L[k], S)
        if dof[k]: im = im.filter(ImageFilter.GaussianBlur(dof[k]))
        bd.alpha_composite(im)
    # 前景失焦：底部 15% 漸進 tilt-shift，頂部（樹冠）都柔少少 → 鏡頭感
    a = np.asarray(bd).astype(float); bl = np.asarray(bd.filter(ImageFilter.GaussianBlur(5))).astype(float)
    yy = np.arange(H)[:, None, None] / H; m = np.clip((yy - .86) / .1, 0, 1) * .85
    a = a * (1 - m) + bl * m
    fc = np.array(K.hx(g['fog']['color'])[:3], float)
    # 高度霧（遠景位置）
    hz = np.exp(-((yy[..., 0] - .50) / .09) ** 2)[..., None] * (.06 if mood == 'A' else .10); a[..., :3] = a[..., :3] * (1 - hz) + fc * hz
    a3 = a[..., :3]
    sk = np.clip(1 - yy[..., 0] / .42, 0, 1)[..., None] ** 1.5
    a3 = a3 * (1 - sk * .45) + sk * .45 * (np.array([96, 150, 214]) if mood == 'A' else np.array([120, 186, 236]))
    if mood == 'A':   # 午後金光：暖色、高對比、強體積光
        a3 = grade(a3, warm=2.2, sat=1.14, contrast=1.14)
        a3 = screen(a3, rays(W, H, (-120, -160), (255, 214, 150), .38, seed=4, spread=(.45, 1.25), falloff=1300))
        a3 = screen(a3, bloom(a3, thr=.86, k=(.22, .3), tint=(1, .9, .72)))
    else:             # 晨光清透：輕微提亮、冷暖平衡、柔光
        a3 = grade(a3, warm=.9, lift=.04, sat=1.04, contrast=1.02)
        a3 = screen(a3, rays(W, H, (W + 160, -200), (230, 240, 255), .26, seed=9, spread=(1.75, 2.75), falloff=1400))
        a3 = screen(a3, bloom(a3, thr=.88, k=(.18, .24), tint=(.95, .98, 1)))
    a3 = vignette(a3, .30 if mood == 'A' else .2)
    bd = Image.fromarray(np.dstack([a3.clip(0, 255), np.full((H, W), 255)]).astype(np.uint8), 'RGBA')
    # 寵物 rim light（@3x 幼邊光）+ 地面柔光圈
    for (p, inf, fx, fy) in pets:
        cx, cy = fx * S, fy * S; glow(bd, cx, cy - 4, 70, (255, 226, 170) if mood == 'A' else (220, 238, 255), .22 * pet_glow)   # petGlow：瞓覺＝0（Kurt「除左佢訓就會關」）
    BULBS = [(47, 120), (71, 141), (96, 153), (120, 159), (144, 156)]
    for (bx, by) in BULBS:
        glow(bd, bx * S, by * S + 4, 46, (255, 196, 110), .55 if mood == 'A' else .35); glow(bd, bx * S, by * S + 4, 14, (255, 244, 210), .9)
        flare(bd, bx * S, by * S + 4, 26, (255, 236, 190), .55)
    glow(bd, 24 * S, 243 * S, 60, (255, 210, 140), .5); glow(bd, 24 * S, 243 * S, 16, (255, 250, 220), .9); flare(bd, 24 * S, 243 * S, 40, (255, 240, 200), .7)
    glow(bd, 165 * S, 197 * S, 50, (255, 220, 160), .35 if mood == 'A' else .2)
    # 螢火光點 + 花粉
    warm = [(255, 220, 150), (255, 240, 200), (255, 200, 120)] if mood == 'A' else [(235, 245, 255), (255, 240, 220), (200, 230, 255)]
    particles(bd, (0, 180, W, 700), 16, 11 if mood == 'A' else 12, warm, bokeh=7, bmin=8, bmax=18)
    particles(bd, (0, 760, W, 1000), 18, 21, warm + [(200, 255, 200)], rmin=1, rmax=2.2, bokeh=2, bmin=18, bmax=30)
    particles(bd, (0, 1040, W, H), 0, 31, warm, bokeh=6, bmin=30, bmax=60)
    return bd

# ================================================================ 頭像（B ×2 face crop × v3 平滑框；同 PORTRAIT_SYNC）
STATE_BG = {'hungry': ((255, 214, 150), (246, 150, 80)), 'happy': ((255, 210, 222), (236, 120, 150)), 'normal': ((200, 232, 255), (110, 170, 226)),
            'sleepy': ((214, 204, 255), (132, 112, 214)), 'sleep': ((190, 186, 240), (96, 86, 180)), 'sick': ((206, 240, 214), (110, 186, 140))}
STATE_IC = {'hungry': 'mini_feed', 'happy': 'mini_heart', 'normal': 'mini_light', 'sleepy': 'mini_sleep', 'sleep': 'mini_sleep', 'sick': 'mini_clean'}
def face(form, state, acc=None, k=6):
    f = M.PR['aliases'].get(form, form); R = M.PR['forms'][f]; x0, y0, n = R['rect']; mm = R['acc'].get(acc, {}) if acc else {}
    sh, pop = mm.get('shift', 0), mm.get('pop', 0); c, info = M.pet_canvas(f, state, acc); T = 40; yc = y0 - sh + T
    body = px(c.crop((x0, yc, x0 + n, yc + n)), k); popim = None
    if pop:
        c0, _ = M.pet_canvas(f, state, None); a1 = np.array(c); a0 = np.array(c0)
        dm = (a1[..., 3] > 0) & ((a0[..., 3] == 0) | (np.abs(a1[..., :3].astype(int) - a0[..., :3]).sum(-1) > 0)); ac = a1.copy(); ac[~dm] = 0
        popim = px(Image.fromarray(ac).crop((x0, yc - pop, x0 + n, yc + 3)), k)
    return body, popim, pop * k
def portrait_v3(bd, x, y, d, form='evo_still_tide', state='hungry', acc='bow', style='A', xp=.62):
    n = M.PR['forms'][M.PR['aliases'].get(form, form)]['rect'][2]; k = max(1, round(d / n)); d = n * k
    body, popim, po = face(form, state, acc, k)
    c0, c1 = STATE_BG[state]
    mask = rr_mask(d, d, 30) if style == 'A' else circ_mask(d)
    shadow(bd, mask, (x, y), 12, 8, .45)
    bg = vgrad(d, d, c0 + (255,), c1 + (255,)); a = np.array(bg).astype(float)
    yy, xx = np.mgrid[0:d, 0:d]; rad = np.exp(-(((xx - d * .35) ** 2 + (yy - d * .3) ** 2) / (d * d * .12)))[..., None]; a[..., :3] += rad * 60
    bg = Image.fromarray(a.clip(0, 255).astype(np.uint8)); bg.alpha_composite(body); hl = vgrad(d, d // 2, (255, 255, 255, 70), (255, 255, 255, 0)); bg.alpha_composite(hl)
    paste_mask(bd, bg, mask, (x, y))
    if style == 'A':
        hair_rr(bd, (x - 5, y - 5, x + d + 5, y + d + 5), 34, A(C['gold'], 1), 1.5); hair_rr(bd, (x, y, x + d, y + d), 30, A(C['goldhi'], .9), 2)
        for cx, cy in ((x + d / 2, y - 5), (x + d / 2, y + d + 5)): diamond(bd, cx, cy, 5, A(C['gold'], 1))
    else:
        hair_circ(bd, x + d / 2, y + d / 2, d, A((255, 255, 255), .95), 3); arc(bd, x + d / 2, y + d / 2, d + 12, A((255, 255, 255), .35), 3, 0, 360)
        arc(bd, x + d / 2, y + d / 2, d + 12, A(C['gold2'], 1), 3.5, -90, -90 + 360 * xp)
    if popim is not None: bd.alpha_composite(popim, (int(x), int(y - po)))
    # 狀態徽章（平滑圓 + 像素 mini icon）
    bx, by = x + d - 14, y + d - 14; m = circ_mask(36); shadow(bd, m, (bx - 18, by - 18), 4, 2, .4)
    paste_mask(bd, vgrad(36, 36, c1 + (255,), tuple(int(v * .7) for v in c1) + (255,)), m, (bx - 18, by - 18)); hair_circ(bd, bx, by, 36, A((255, 255, 255), .9), 2)
    putc(bd, icon(STATE_IC[state], 2), bx, by)

# ================================================================ 面板
def smoked(bd, box, r=18, a0=.80, a1=.70, line=True, blur=14):   # V3-A：煙燻深藍磨砂 + 金幼線
    x0, y0, x1, y1 = [int(v) for v in box]; w, h = x1 - x0, y1 - y0; m = rr_mask(w, h, r); shadow(bd, m, (x0, y0), 10, 6, .35)
    bgc = bd.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(blur)); bgc.alpha_composite(vgrad(w, h, A(C['navy2'], a0), A(C['navy'], a1 + .1)))
    bgc.alpha_composite(vgrad(w, max(2, h // 2), (255, 255, 255, 22), (255, 255, 255, 0))); paste_mask(bd, bgc, m, (x0, y0))
    if line: hair_rr(bd, box, r, A(C['gold'], .9), 1.5); hair_rr(bd, (x0 + 4, y0 + 4, x1 - 4, y1 - 4), r - 4, A(C['gold'], .22), 1)
def glass(bd, box, r=26, a=.62, line=True, blur=16, tint=(255, 255, 255)):  # V3-B：白磨砂玻璃 + 幼金線
    x0, y0, x1, y1 = [int(v) for v in box]; w, h = x1 - x0, y1 - y0; m = rr_mask(w, h, r); shadow(bd, m, (x0, y0), 16, 10, .22)
    bgc = bd.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(blur)); bgc.alpha_composite(Image.new('RGBA', (w, h), A(tint, a)))
    bgc.alpha_composite(vgrad(w, h, (255, 255, 255, 60), (255, 255, 255, 0))); paste_mask(bd, bgc, m, (x0, y0))
    hair_rr(bd, box, r, A((255, 255, 255), .95), 2)
    if line: hair_rr(bd, (x0 + 3, y0 + 3, x1 - 3, y1 - 3), r - 3, A(C['gold2'], .75), 1.2)
def bar(bd, x, y, w, h, v, col, track=(255, 255, 255, 50), lowc=None):
    m = rr_mask(w, h, h / 2); paste_mask(bd, Image.new('RGBA', (w, h), track), m, (x, y)); fw = max(h, int(w * v))
    c = lowc or col; g = vgrad(fw, h, tuple(min(255, int(v_ * 1.15) + 20) for v_ in c) + (255,), tuple(int(v_ * .85) for v_ in c) + (255,))
    paste_mask(bd, g, rr_mask(fw, h, h / 2), (x, y)); glow(bd, x + fw, y + h / 2, h * 1.6, c, .5)

# ================================================================ V3-A 主畫面
def homeA():
    STYLE[0] = 'V3-A'; bd = garden3x('A')
    # 頂部漸層 scrim（冇硬框）
    bd.alpha_composite(vgrad(W, 112, A(C['navy'], .9), A(C['navy'], .82))); bd.alpha_composite(vgrad(W, 90, A(C['navy'], .82), A(C['navy'], 0)), (0, 112))
    hline(bd, 160, 572, 128, A(C['gold'], .9), 1.5); diamond(bd, 572, 128, 4, A(C['gold'], 1))
    portrait_v3(bd, 22, 20, 120, style='A')
    text(bd, '團絨', 166, 16, 'title', C['cream'], sh=(0, 0, 0))
    bb = ImageDraw.Draw(bd).textbbox((166, 16), '團絨', font=tf('title')); tx = bb[2] + 12
    hair_rr(bd, (tx, 24, tx + 62, 50), 13, A(C['gold'], 1), 1.5); text(bd, '靜光', tx + 31, 37, 'caption', C['goldhi'], 'mm')
    text(bd, 'Lv.12', tx + 74, 37, 'caption', (214, 220, 236), 'lm')
    bar(bd, 166, 64, 236, 5, .62, C['gold'], track=(255, 255, 255, 40))
    for i, (k, c, v) in enumerate(NEED):
        x = 166 + (i % 2) * 124; y = 80 + (i // 2) * 24; putc(bd, icon('mini_' + k, 2), x + 11, y + 11)
        bar(bd, x + 28, y + 8, 84, 6, v, C[c], lowc=C['red'] if v < .2 else None)
        if v < .2: glow(bd, x + 116, y + 11, 9, C['red'], .9)
    for j, (k, v) in enumerate((('light', '140'), ('star', '10'))):
        y = 30 + j * 44; putc(bd, icon(k, 2), 440, y); text(bd, v, 530, y, 'value', C['cream'], 'rm', sh=(0, 0, 0))
        hair_circ(bd, 556, y, 26, A(C['gold'], .9), 1.5); text(bd, '+', 556, y - 1, 'button', C['goldhi'], 'mm', check=False)
    hline(bd, 420, 572, 52, A(C['gold'], .35), 1)
    # toast
    smoked(bd, (166, 150, 452, 192), 21); putc(bd, icon('mini_star', 2), 192, 171); glow(bd, 192, 171, 18, C['gold'], .35)
    text(bd, '收到小禮物', 214, 171, 'body', C['cream'], 'lm'); text(bd, '+5', 436, 171, 'value', C['goldhi'], 'rm')
    # 右邊 rail
    for i, (k, lb, badge) in enumerate((('gift', '委託', '3'), ('mail', '信', '•'), ('house', '屋仔', None))):
        cx, cy = 538, 238 + i * 112; m = circ_mask(64); smoked(bd, (cx - 32, cy - 32, cx + 32, cy + 32), 32, line=False)
        hair_circ(bd, cx, cy, 64, A(C['gold'], .95), 1.5); putc(bd, icon(k, 2), cx, cy)
        smoked(bd, (cx - 30, cy + 38, cx + 30, cy + 64), 13, line=False); text(bd, lb, cx, cy + 51, 'caption', C['cream'], 'mm')
        if badge == '3':
            m2 = circ_mask(26); paste_mask(bd, vgrad(26, 26, (214, 62, 72, 255), (176, 38, 50, 255)), m2, (cx + 14, cy - 36)); text(bd, '3', cx + 27, cy - 23, 'caption', (255, 255, 255), 'mm', kind='sansb')
        elif badge: glow(bd, cx + 24, cy - 22, 10, C['red'], 1)
    # 泡泡
    glass(bd, (300, 676, 470, 718), 21, .9, line=False); putc(bd, icon('mini_feed', 2), 324, 697); text(bd, '肚仔餓…', 342, 697, 'body', C['ink'], 'lm')
    stroke(bd, (318, 716, 336, 732), lambda d, s, w, h: d.polygon([(0, 0), (w * s, 0), (2 * s, h * s)], fill=(255, 255, 255, 236)))
    # 行動掣：煙燻圓 + 色環 + 柔光
    for i, (k, c, lb) in enumerate((('feed', 'amber', '餵食'), ('play_cat', 'rose', '玩耍'), ('clean', 'sky', '清潔'), ('sleep', 'violet', '瞓覺'))):
        cx, cy = 92 + i * 134, 1022; d = 78
        if i == 0: glow(bd, cx, cy, 70, C['amber'], .45)
        smoked(bd, (cx - d / 2, cy - d / 2, cx + d / 2, cy + d / 2), d / 2, line=False)
        arc(bd, cx, cy, d - 8, A(C[c], 1), 3, 0, 360); hair_circ(bd, cx, cy, d + 6, A(C['gold'], .8), 1.2); putc(bd, icon(k, 2), cx, cy)
        smoked(bd, (cx - 40, cy + 46, cx + 40, cy + 74), 14, line=False, a0=.72, a1=.62); text(bd, lb, cx, cy + 60, 'button', C['cream'], 'mm')
        if i == 0: diamond(bd, cx, cy - d / 2 - 8, 4, A(C['goldhi'], 1))
    # dock：深色漸層 + 金幼線 + 選中柔光
    bd.alpha_composite(vgrad(W, 150, A(C['navy'], 0), A(C['navy'], .55)), (0, H - 150 - 0))
    smoked(bd, (12, 1120, W - 12, 1236), 28)
    tabs = (('heart_bunny', '照顧'), ('play_cat', '玩'), ('sprout', '小圃'), ('book_bear', '手帳'), ('gear_chick', '設定'))
    tw_ = (W - 24) / 5
    for i, (k, lb) in enumerate(tabs):
        cx = 12 + tw_ * (i + .5)
        if i == 0:
            glow(bd, cx, 1158, 46, C['gold'], .5); putc(bd, icon(k, 2), cx, 1156); text(bd, lb, cx, 1200, 'caption', C['goldhi'], 'mm', kind='sansb')
            hline(bd, cx - 26, cx + 26, 1222, A(C['gold'], 1), 2); diamond(bd, cx, 1124, 4, A(C['goldhi'], 1))
        else:
            putc(bd, icon(k, 2), cx, 1156); text(bd, lb, cx, 1200, 'caption', (206, 212, 230), 'mm')
        if i == 3: glow(bd, cx + 20, 1138, 9, C['red'], 1)
    paste_mask(bd, Image.new('RGBA', (140, 6), (255, 255, 255, 200)), rr_mask(140, 6, 3), (W / 2 - 70, 1252))
    return bd

# ================================================================ V3-B 主畫面
def homeB():
    STYLE[0] = 'V3-B'; bd = garden3x('B')
    glass(bd, (14, 16, 571, 132), 30, .70)
    portrait_v3(bd, 30, 26, 112, style='B')
    text(bd, '團絨', 168, 28, 'title', C['ink'], kind='sansb')
    bb = ImageDraw.Draw(bd).textbbox((168, 28), '團絨', font=tf('title', 'sansb')); tx = bb[2] + 12
    paste_mask(bd, vgrad(64, 26, A(C['goldhi'], 1), A(C['gold'], 1)), rr_mask(64, 26, 13), (tx, 33)); text(bd, '靜光', tx + 32, 46, 'caption', (88, 60, 20), 'mm', kind='sansb')
    text(bd, 'Lv.12', tx + 76, 46, 'caption', C['ink2'], 'lm')
    for i, (k, c, v) in enumerate(NEED):  # 環形量表
        cx, cy = 190 + i * 52, 98; d = 40; low = v < .2
        arc(bd, cx, cy, d, A(C['ink'], .12), 4, 0, 360); arc(bd, cx, cy, d, A(C['red'] if low else C[c], 1), 4, -90, -90 + 360 * v)
        putc(bd, icon('mini_' + k, 2), cx, cy)
        if low: glow(bd, cx + 16, cy - 16, 8, C['red'], 1)
    for j, (k, v) in enumerate((('light', '140'), ('star', '10'))):
        y = 52 + j * 46; x0 = 432; glass(bd, (x0, y - 19, 556, y + 19), 19, .55, line=False); putc(bd, icon('mini_' + k, 2), x0 + 22, y)
        text(bd, v, x0 + 92, y, 'value', C['ink'], 'rm'); text(bd, '+', 540, y - 1, 'button', C['gold2'], 'mm', check=False)
    glass(bd, (168, 150, 440, 192), 21, .78, line=False); putc(bd, icon('mini_star', 2), 192, 171)
    text(bd, '收到小禮物', 212, 171, 'body', C['ink'], 'lm'); text(bd, '+5', 424, 171, 'value', (112, 74, 8), 'rm')
    for i, (k, lb, badge) in enumerate((('gift', '委託', '3'), ('mail', '信', '•'), ('house', '屋仔', None))):
        cx, cy = 532, 248 + i * 106; glass(bd, (cx - 36, cy - 42, cx + 36, cy + 42), 22, .72, line=False)
        putc(bd, icon(k, 2), cx, cy - 10); text(bd, lb, cx, cy + 24, 'caption', C['ink'], 'mm')
        if badge == '3':
            paste_mask(bd, vgrad(26, 26, (214, 62, 72, 255), (176, 38, 50, 255)), circ_mask(26), (cx + 22, cy - 52)); text(bd, '3', cx + 35, cy - 39, 'caption', (255, 255, 255), 'mm', kind='sansb')
        elif badge: glow(bd, cx + 30, cy - 36, 10, C['red'], 1)
    glass(bd, (300, 676, 470, 718), 21, .9, line=False); putc(bd, icon('mini_feed', 2), 324, 697); text(bd, '肚仔餓…', 342, 697, 'body', C['ink'], 'lm')
    stroke(bd, (318, 716, 336, 732), lambda d, s, w, h: d.polygon([(0, 0), (w * s, 0), (2 * s, h * s)], fill=(255, 255, 255, 236)))
    # 行動：一條浮動玻璃膠囊
    glass(bd, (34, 984, 551, 1092), 54, .66)
    for i, (k, c, lb) in enumerate((('feed', 'amber', '餵食'), ('play_cat', 'rose', '玩耍'), ('clean', 'sky', '清潔'), ('sleep', 'violet', '瞓覺'))):
        cx = 34 + 517 / 4 * (i + .5); cy = 1022
        if i == 0:
            paste_mask(bd, vgrad(104, 92, A(C['goldhi'], .95), A(C['gold'], .9)), rr_mask(104, 92, 40), (cx - 52, 992))
        m = circ_mask(50); paste_mask(bd, vgrad(50, 50, A(C[c], .35), A(C[c], .55)), m, (cx - 25, cy - 25)); putc(bd, icon(k, 2), cx, cy)
        text(bd, lb, cx, 1066, 'button', (70, 46, 10) if i == 0 else C['ink'], 'mm')
    glass(bd, (0, 1116, W, H + 40), 36, .80, line=False); hline(bd, 40, W - 40, 1118, A(C['gold2'], .8), 1.2)
    tabs = (('heart_bunny', '照顧'), ('play_cat', '玩'), ('sprout', '小圃'), ('book_bear', '手帳'), ('gear_chick', '設定'))
    for i, (k, lb) in enumerate(tabs):
        cx = W / 5 * (i + .5); on = i == 0
        if on: paste_mask(bd, Image.new('RGBA', (88, 92), A(C['goldhi'], .55)), rr_mask(88, 92, 24), (cx - 44, 1130))
        putc(bd, icon(k, 2), cx, 1160); text(bd, lb, cx, 1204, 'caption', C['ink'] if on else C['ink2'], 'mm', kind='sansb' if on else None)
        if i == 3: glow(bd, cx + 20, 1140, 9, C['red'], 1)
    paste_mask(bd, Image.new('RGBA', (140, 6), (30, 30, 40, 200)), rr_mask(140, 6, 3), (W / 2 - 70, 1252))
    return bd

# ================================================================ 屋仔 v3（V3-A 語言）：窗光體積光、浮塵、地板反射、燈暖光
def room_pets():
    return (('evo_still_tide', 'sleepy', 96, 300),)
def house_scene3x(pet_glow=.6, furn=('bed_leaf', 'table_stump', 'rug_round', 'wall_shelf', 'win_curtain', 'lamp_mushroom'), pets=None):
    """屋仔場景（冇 HUD）；pet_glow：寵物光（sleepy＝0.6，sleep＝0）"""
    pets = room_pets() if pets is None else pets
    full = M.room('day', furn=furn, pets=pets)
    a = np.asarray(px(full, S)).astype(float)[..., :3]
    # 窗 = 上半部最光區域
    l = a @ np.array([.299, .587, .114]); win = (l > 225) & (np.arange(H)[:, None] < 560) & (np.arange(W)[None, :] < 300)
    ys, xs = np.nonzero(win); wx0, wx1, wy0, wy1 = xs.min(), xs.max(), ys.min(), ys.max()
    # 地板反射：鏡像地板以上（地板由 y≈720 開始），淡入
    fy = 830; refl = a[::-1][H - fy - (H - fy):H - fy][: H - fy] if False else a[fy - (H - fy):fy][::-1]
    t = np.linspace(.13, 0, H - fy)[:, None, None]; a[fy:] = a[fy:] * (1 - t) + refl * t * 1.05
    # 調色：暖室內
    a = grade(a, warm=1.8, sat=1.06, contrast=1.08)
    # 窗光：斜向體積光柱（由窗射落地板右下）
    yy, xx = np.mgrid[0:H, 0:W].astype(float); cx = (wx0 + wx1) / 2; cy = (wy0 + wy1) / 2
    dirv = np.array([.62, .78]); px_ = xx - cx; py_ = yy - cy; along = px_ * dirv[0] + py_ * dirv[1]; perp = -px_ * dirv[1] + py_ * dirv[0]
    half = (wx1 - wx0) * .45; beam = np.clip(1 - np.abs(perp) / half, 0, 1) ** 1.2 * (along > 0) * np.exp(-along / 900)
    stripes = .65 + .35 * np.cos(perp / half * math.pi * 2.0) ** 2  # 窗框分格影
    a = a + (beam * stripes)[..., None] * np.array([255, 216, 150]) * .2
    # 地板光斑（窗格投影）
    fl = np.exp(-(((xx - (cx + 260)) / 150) ** 2 + ((yy - 900) / 70) ** 2)); a = a + fl[..., None] * np.array([255, 210, 140]) * .22
    a = screen(a, bloom(a, thr=.80, r=(8, 26), k=(.3, .4), tint=(1, .88, .7)))
    a = vignette(a, .34, .5, .5)
    bd = Image.fromarray(np.dstack([a.clip(0, 255), np.full((H, W), 255)]).astype(np.uint8), 'RGBA')
    glow(bd, 76, 560, 110, (255, 196, 120), .4); glow(bd, 76, 556, 30, (255, 240, 210), .7); flare(bd, 76, 556, 34, (255, 236, 200), .6)   # 蘑菇燈
    glow(bd, cx, cy, 170, (255, 236, 190), .25)
    # 浮塵：只喺光柱入面密
    rnd = random.Random(5); G = Image.new('RGBA', bd.size, (255, 230, 180, 0)); P = Image.new('RGBA', bd.size, (255, 250, 230, 0)); dg = ImageDraw.Draw(G); dp = ImageDraw.Draw(P)
    n = 0
    while n < 110:
        x, y = rnd.uniform(0, W), rnd.uniform(wy0, 1050)
        if beam[int(y), int(x)] < .25 and rnd.random() > .08: continue
        r = rnd.uniform(.8, 2.4); dg.ellipse([x - r * 4, y - r * 4, x + r * 4, y + r * 4], fill=(255, 230, 180, int(90 * rnd.uniform(.4, 1)))); dp.ellipse([x - r, y - r, x + r, y + r], fill=(255, 250, 230, int(255 * rnd.uniform(.6, 1)))); n += 1
    bd.alpha_composite(G.filter(ImageFilter.GaussianBlur(4))); bd.alpha_composite(P.filter(ImageFilter.GaussianBlur(.5)))
    particles(bd, (0, 1000, W, H), 0, 8, [(255, 210, 150)], bokeh=6, bmin=30, bmax=60)
    if pet_glow > 0:
        for (_, _, fx, fy) in pets: glow(bd, fx * S, fy * S - 30, 70, (220, 210, 255), .22 * pet_glow)
    return bd
def house3x():
    STYLE[0] = 'V3-A 屋仔'
    bd = house_scene3x()
    # HUD（V3-A 語言）
    bd.alpha_composite(vgrad(W, 170, A(C['navy'], .7), A(C['navy'], 0)))
    m = circ_mask(56); smoked(bd, (18, 18, 74, 74), 28, line=False); hair_circ(bd, 46, 46, 56, A(C['gold'], .95), 1.5); putc(bd, icon('back', 2), 46, 46)
    text(bd, '團絨嘅屋仔', W / 2, 46, 'title', C['cream'], 'mm', sh=(0, 0, 0)); hline(bd, W / 2 - 150, W / 2 + 150, 76, A(C['gold'], .9), 1.5); diamond(bd, W / 2, 76, 4, A(C['gold'], 1))
    putc(bd, icon('star', 2), 470, 46); text(bd, '36', 540, 46, 'value', C['cream'], 'rm', sh=(0, 0, 0)); hair_circ(bd, 562, 46, 24, A(C['gold'], .9), 1.5); text(bd, '+', 562, 45, 'button', C['goldhi'], 'mm', check=False)
    portrait_v3(bd, 22, 108, 108, 'evo_still_tide', 'sleepy', 'nightcap', style='A')
    glass(bd, (302, 744, 476, 786), 21, .9, line=False); putc(bd, icon('mini_sleep', 2), 326, 765); text(bd, '好攰呀…', 344, 765, 'body', C['ink'], 'lm')
    stroke(bd, (318, 784, 336, 800), lambda d, s, w, h: d.polygon([(0, 0), (w * s, 0), (2 * s, h * s)], fill=(255, 255, 255, 236)))
    smoked(bd, (12, 1110, W - 12, 1236), 28)
    for i, (k, c, lb) in enumerate((('sleep', 'violet', '瞓覺'), ('play_cat', 'rose', '玩'), ('feed', 'amber', '餵食'), ('decorate', 'gold', '佈置'))):
        cx = 12 + (W - 24) / 4 * (i + .5); cy = 1156; d = 62
        if i == 0: glow(bd, cx, cy, 52, C['violet'], .45)
        arc(bd, cx, cy, d, A(C[c], 1), 2.5, 0, 360); putc(bd, icon(k, 2), cx, cy); text(bd, lb, cx, 1210, 'caption', C['goldhi'] if i == 0 else C['cream'], 'mm', kind='sansb' if i == 0 else None)
    paste_mask(bd, Image.new('RGBA', (140, 6), (255, 255, 255, 200)), rr_mask(140, 6, 3), (W / 2 - 70, 1252))
    return bd

# ================================================================ 輸出
def label(bd, t, x, y, sz=26, col=(240, 236, 226), anchor='la', kind='sansb'):
    ImageDraw.Draw(bd).text((x, y), t, font=F(kind, sz), fill=col, anchor=anchor)
if __name__ == '__main__':
    v2 = Image.open(f'{X.ART}/ui/kit_hd2d_v2/mockups/home_3x.png').convert('RGBA')
    hA = homeA(); hA.save(f'{OUT}/home_v3A_3x.png')
    hB = homeB(); hB.save(f'{OUT}/home_v3B_3x.png')
    hs = house3x(); hs.save(f'{OUT}/house_v3A_3x.png')
    v2h = Image.open(f'{X.ART}/ui/kit_hd2d_v2/mockups/house_4b_3x.png').convert('RGBA')
    g = 30; top = 110; cw = W * 3 + g * 4; cmp_ = Image.new('RGBA', (cw, H + top + 40), (22, 24, 34, 255))
    for i, (im, t, s) in enumerate(((v2, '而家 v2（像素框＋點陣字）', 'FP 點陣字・粗像素框・棋盤 dither'), (hA, 'V3-A 金光現代 HD-2D', '煙燻磨砂＋金幼線＋明朝標題・午後體積光'), (hB, 'V3-B 晨光玻璃極簡', '白磨砂卡＋環形量表・清透晨光'))):
        x = g + i * (W + g); cmp_.alpha_composite(im, (x, top)); label(cmp_, t, x, 22, 30); label(cmp_, s, x, 64, 20, (180, 184, 200), kind='sans')
    cmp_.convert('RGB').save(f'{OUT}/compare_v2_v3A_v3B.png')
    ch = Image.new('RGBA', (W * 2 + g * 3, H + top + 40), (22, 24, 34, 255))
    for i, (im, t) in enumerate(((v2h, '而家 v2 屋仔'), (hs, 'V3-A 屋仔（窗光體積光・浮塵・地板反射）'))):
        x = g + i * (W + g); ch.alpha_composite(im, (x, top)); label(ch, t, x, 30, 26)
    ch.convert('RGB').save(f'{OUT}/compare_house_v2_v3A.png')
    # ---- 字級表
    STYLE[0] = 'type'; rows = list(TYPE.items()); rh = 92; tsw = 1500; ts = Image.new('RGBA', (tsw, 150 + rh * (len(rows) + 1) + 40), (22, 24, 34, 255))
    label(ts, 'v3 字級表（@3x mock px；CSS = 細機 360w ×0.615／標準 390w ×0.667）', 30, 30, 30); label(ts, 'Noto Sans CJK TC／Noto Serif CJK TC（SIL OFL 1.1）・最細 18px = 11.1／12 CSS px', 30, 80, 20, (180, 184, 200), kind='sans')
    hx_ = [30, 230, 420, 860]; y0 = 130
    for j, t in enumerate(('角色', 'px @3x → CSS', 'V3-A（煙燻深底）', 'V3-B（白玻璃）')): label(ts, t, hx_[j], y0, 20, (200, 190, 150))
    for i, (r, (kind, sz, zh)) in enumerate(rows):
        y = y0 + 40 + i * rh; label(ts, f'{r}', hx_[0], y + 10, 22); label(ts, zh, hx_[0], y + 44, 18, (170, 174, 190), kind='sans')
        label(ts, f'{sz}px → {sz * 360 / 585:.1f}／{sz * 390 / 585:.1f}', hx_[1], y + 24, 20, (220, 224, 236), kind='sans')
        a = vgrad(420, rh - 10, A(C['navy2'], 1), A(C['navy'], 1)); ts.alpha_composite(a, (hx_[2], y)); b = Image.new('RGBA', (600, rh - 10), (250, 248, 244, 255)); ts.alpha_composite(b, (hx_[3], y))
        samp = {'title': '團絨・靜光', 'h2': '今日計劃', 'body': '肚仔餓…想食嘢', 'value': '140  10  +5', 'button': '餵食  確定', 'caption': '委託  屋仔  Lv.12'}[r]
        kA = 'serif' if r == 'title' else kind; kB = 'sansb' if r == 'title' else kind
        ImageDraw.Draw(ts).text((hx_[2] + 20, y + (rh - 10) / 2), samp, font=F(kA, sz), fill=C['cream'], anchor='lm'); ImageDraw.Draw(ts).text((hx_[3] + 20, y + (rh - 10) / 2), samp, font=F(kB, sz), fill=C['ink'], anchor='lm')
    y = y0 + 40 + len(rows) * rh; label(ts, '而家 v2', hx_[0], y + 10, 22, (240, 150, 150)); label(ts, 'FP12 點陣×描邊', hx_[0], y + 44, 18, (170, 174, 190), kind='sans')
    label(ts, '36px → 22／24 CSS', hx_[1], y + 24, 20, (240, 150, 150), kind='sans')
    t2 = px(M.text_img('團絨・肚仔餓…', 12), 3); ts.alpha_composite(vgrad(1030, rh - 10, A(C['navy2'], 1), A(C['navy'], 1)), (hx_[2], y)); ts.alpha_composite(t2, (hx_[2] + 20, int(y + (rh - 10 - t2.height) / 2)))
    ts.convert('RGB').save(f'{OUT}/type_scale.png')
    # ---- 細部特寫（×2 nearest，睇真幼線／漸變／像素 icon）
    crops = [('頂部：頭像框＋名＋數值條', (0, 0, 585, 200)), ('行動掣＋泡泡', (0, 660, 585, 1100)), ('Dock', (0, 1100, 585, 1266))]
    cw2 = 585 * 2; tot = sum((b[3] - b[1]) * 2 + 60 for _, b in crops); dc = Image.new('RGBA', (cw2 * 2 + 90, tot + 80), (22, 24, 34, 255))
    for c_, (im, nm) in enumerate(((hA, 'V3-A'), (hB, 'V3-B'))):
        x = 30 + c_ * (cw2 + 30); y = 20; label(dc, nm, x, y, 30); y += 60
        for t, b in crops:
            label(dc, t, x, y, 22, (200, 190, 150), kind='sans'); y += 36; cr = px(im.crop(b), 2); dc.alpha_composite(cr, (x, y)); y += cr.height + 24
    dc.convert('RGB').save(f'{OUT}/detail_closeup_2x.png')
    json.dump(CONTRAST, open(f'{OUT}/contrast.json', 'w'), ensure_ascii=False, indent=0)
    print('min contrast', min(c[-1] for c in CONTRAST)); print([c for c in CONTRAST if c[-1] < 4.5])
