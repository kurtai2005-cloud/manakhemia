# 《微光小圃》4b 屋仔 — 房間背景（HD-2D 分層：sky/far/mid/fore＋lightmap 等），直向 195×422 美術格、層 223×446
# 純 Pillow/numpy 逐像素程序繪製，冇 AI 生圖。由 build_house_4b.py 呼叫。
import json, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

AW, AH = 195, 422; MX, MY = 14, 12; LW, LH = AW + 2 * MX, AH + 2 * MY
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0 + 1 / 32
def A(x, y): return x + MX, y + MY

# ── 房間幾何（art 座標）──
G = dict(wall=(16, 26, 179, 238),            # 後牆 x0,y0,x1,y1（y1＝地腳線）
         rail=196,                           # 護牆板頂
         window=(30, 98, 76, 150),           # 窗洞（透明 → 見 sky 層）
         vp=(97.5, 132))                     # 透視消失點
# 材質（name, levels）；raw 色盤 ≤64
MATS = [('SKY', 6), ('CLOUD', 2), ('HILL', 2), ('TREE', 2), ('STAR', 1), ('MOON', 1),
        ('CEIL', 3), ('BEAM', 3), ('WALLP', 3), ('DOT', 2), ('SIDEW', 3), ('WAINS', 3), ('TRIM', 3),
        ('FLOOR', 4), ('SEAM', 1), ('SILL', 2), ('LEAF', 3), ('POT', 2), ('VINE', 2), ('INK', 1)]
IDX = {}; _k = 1
for n, lv in MATS: IDX[n] = list(range(_k, _k + lv)); _k += lv
NIDX = _k - 1
# 色（每材質由暗到光）；day / night 兩套
BASE = {
 'SKY': ['#7fb8e8', '#93c6ee', '#a8d4f2', '#bde0f4', '#d2eaf4', '#e6f2f0'], 'CLOUD': ['#e8eef8', '#ffffff'],
 'HILL': ['#76a878', '#92c08a'], 'TREE': ['#4e8a5a', '#68a668'], 'STAR': ['#ffffff'], 'MOON': ['#f4f0dc'],
 'CEIL': ['#c49a76', '#d6b08a', '#e4c49e'], 'BEAM': ['#7c5440', '#9c6c50', '#b88660'],
 'WALLP': ['#f2d2c0', '#f8e0cc', '#fdecd8'], 'DOT': ['#f4b8c4', '#ffd2da'],
 'SIDEW': ['#d8b4a6', '#e6c4b2', '#f0d2be'], 'WAINS': ['#a8785a', '#c2906a', '#d6a87e'], 'TRIM': ['#7a5040', '#98684e', '#e8c8a0'],
 'FLOOR': ['#a87050', '#bc8460', '#cc9670', '#dcaa80'], 'SEAM': ['#8a5a40'], 'SILL': ['#c89870', '#f0d4b0'],
 'LEAF': ['#4c8c58', '#68aa62', '#94cc7a'], 'POT': ['#c8744e', '#e89a6a'], 'VINE': ['#3e7a4a', '#5a9a58'], 'INK': ['#4a2e3a'],
}
NIGHT_SKY = {'SKY': ['#1a1f48', '#222a5a', '#2c366a', '#36427a', '#424e88', '#505c94'], 'CLOUD': ['#3c4478', '#56609a'],
             'HILL': ['#24304e', '#2e3c5c'], 'TREE': ['#1c2840', '#26344c']}

def hx(h): h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)
def tohex(c): return '#%02x%02x%02x' % tuple(int(round(v)) for v in np.clip(c, 0, 255))

class Lay:
    def __init__(s):
        s.m = np.zeros((LH, LW), np.uint8)
        Y, X = np.mgrid[0:LH, 0:LW].astype(float); s.X, s.Y = X + .5 - MX, Y + .5 - MY
        s.bay = BAYER[np.arange(LH)[:, None] % 4, np.arange(LW)[None, :] % 4]
    def put(s, mask, mat, f=0.5, dither=0.35):
        ids = IDX[mat]; n = len(ids)
        f = f[mask] if isinstance(f, np.ndarray) else np.full(int(mask.sum()), f)
        q = np.clip(np.floor(f * n + (s.bay[mask] - .5) * dither * 2), 0, n - 1).astype(int)
        s.m[mask] = np.array(ids, np.uint8)[q]; return mask
    def pmask(s, pts):
        im = Image.new('L', (LW, LH), 0); ImageDraw.Draw(im).polygon([A(*p) for p in pts], fill=1); return np.array(im).astype(bool)
    def poly(s, mat, pts, f=.5, d=.35): return s.put(s.pmask(pts), mat, f, d)
    def rect(s, mat, x0, y0, x1, y1, f=.5, d=.35):
        m = (s.X >= x0) & (s.X < x1) & (s.Y >= y0) & (s.Y < y1); return s.put(m, mat, f, d)
    def ell(s, mat, cx, cy, rx, ry, f=None, d=.35):
        dx, dy = (s.X - cx) / rx, (s.Y - cy) / ry; m = dx * dx + dy * dy <= 1
        if f is None: f = np.clip(.55 - .45 * (dx * .6 + dy * .8), 0, 1)
        return s.put(m, mat, f, d)
    def line(s, mat, pts, w=1, f=.5):
        im = Image.new('L', (LW, LH), 0); ImageDraw.Draw(im).line([A(*p) for p in pts], fill=1, width=w)
        return s.put(np.array(im).astype(bool), mat, f, 0)

def build_index(night=False):
    rng = np.random.default_rng(7)
    sky, far, mid, fore = Lay(), Lay(), Lay(), Lay()
    X, Y = sky.X, sky.Y
    wx0, wy0, wx1, wy1 = G['wall']; w0, w1, w2, w3 = G['window']
    # ── sky：窗外（全不透明）
    sky.put(np.ones_like(sky.m, bool), 'SKY', np.clip((Y - 60) / 120, 0, 1), .5)
    if night:
        sky.put((rng.random(sky.m.shape) > .97) & (Y < 140), 'STAR', 1, 0)
        m = ((X - 64) ** 2 + (Y - 108) ** 2 <= 36) & ~((X - 66.5) ** 2 + (Y - 106.5) ** 2 <= 30); sky.put(m, 'MOON', 1, 0)
    else:
        for (cx, cy, s) in [(44, 108, 1.0), (72, 122, .7)]:
            for (ox, oy, rx, ry) in [(-6, 1, 6, 3.5), (0, -2, 7, 5), (7, 1, 6, 3.5)]: sky.ell('CLOUD', cx + ox * s, cy + oy * s, rx * s, ry * s, d=0)
    y1 = 136 + 3 * np.sin(X / 9)
    sky.put(Y >= y1, 'HILL', np.clip(.6 + .3 * np.sin(X / 7) - .02 * (Y - y1), 0, 1))
    for x0 in range(20, 90, 7):
        r = 4 + 2 * abs(math.sin(x0)); sky.ell('TREE', x0, 142 - r * .3, r, r * 1.2)
    # ── far：天花、後牆、側牆（窗洞透明）
    far.poly('CEIL', [(-14, -12), (209, -12), (wx1, wy0), (wx0, wy0)], np.clip(.25 + .5 * (Y + 12) / 40, 0, 1))
    for bx in (16, 64, 112, 160):                      # 天花樑（透視）
        vx, vy = G['vp']; t0 = (-12 - vy) / (wy0 - vy)
        xb = vx + (bx + 1.5 - vx) * t0
        far.poly('BEAM', [(bx, wy0), (bx + 4, wy0), (xb + 10, -12), (xb - 6, -12)], .55)
        far.line('BEAM', [(bx, wy0), (xb - 6, -12)], 1, .05)
    far.rect('BEAM', wx0 - 2, wy0 - 2, wx1 + 2, wy0 + 3, .5, 0); far.rect('BEAM', wx0 - 2, wy0 + 2, wx1 + 2, wy0 + 3, .05, 0)
    # 後牆：牆紙（直紋＋波點）
    stripe = (((X.astype(int) - wx0) // 9) % 2 == 0)
    wf = np.clip(.78 + .12 * stripe - .22 * (X - wx0) / (wx1 - wx0) - .12 * (Y - wy0) / (G['rail'] - wy0), 0, 1)
    far.rect('WALLP', wx0, wy0 + 3, wx1, G['rail'], wf, .3)
    for yy in range(38, G['rail'] - 6, 14):
        for xx in range(wx0 + 6 + (7 if (yy // 14) % 2 else 0), wx1 - 2, 14):
            far.ell('DOT', xx, yy, 1.6, 1.6, f=.3, d=0); far.put((X >= xx - 1) & (X < xx) & (Y >= yy - 1) & (Y < yy), 'DOT', 1, 0)
    # 護牆板＋腰線＋地腳
    far.rect('WAINS', wx0, G['rail'], wx1, wy1, .6, .3)
    for xx in range(wx0 + 2, wx1, 14):
        far.rect('WAINS', xx, G['rail'] + 6, xx + 11, wy1 - 6, .85, 0); far.rect('WAINS', xx, G['rail'] + 6, xx + 11, G['rail'] + 7, .1, 0)
        far.rect('WAINS', xx, G['rail'] + 6, xx + 1, wy1 - 6, .1, 0)
    far.rect('TRIM', wx0, G['rail'] - 3, wx1, G['rail'] + 1, .55, 0); far.rect('TRIM', wx0, G['rail'] - 3, wx1, G['rail'] - 2, .95, 0)
    far.rect('TRIM', wx0, wy1 - 5, wx1, wy1, .4, 0); far.rect('TRIM', wx0, wy1 - 5, wx1, wy1 - 4, .9, 0)
    # 側牆（透視梯形）
    for (xs, xe, s) in [(-14, wx0, -1), (209, wx1, 1)]:
        top_out, bot_out = -12, 290
        far.poly('SIDEW', [(xs, top_out), (xe, wy0), (xe, wy1), (xs, bot_out)], .45 if s < 0 else .2)
        # 側牆腰線
        f = (G['rail'] - wy0) / (wy1 - wy0); yo = top_out + f * (bot_out - top_out)
        far.poly('WAINS', [(xs, yo), (xe, G['rail']), (xe, wy1), (xs, bot_out)], .45 if s < 0 else .25)
        far.line('TRIM', [(xs, yo), (xe, G['rail'] - 1)], 2, .5)
        far.line('TRIM', [(xs, bot_out - 4), (xe, wy1 - 3)], 2, .35)
        far.line('INK', [(xe, wy0), (xe, wy1)], 1)
    # 窗洞：外框＋窗台；洞透明
    far.rect('TRIM', w0 - 3, w1 - 3, w2 + 3, w3 + 3, .55, 0); far.rect('TRIM', w0 - 3, w1 - 3, w2 + 3, w1 - 2, .95, 0)
    far.rect('SILL', w0 - 6, w3 + 1, w2 + 6, w3 + 5, .7, 0); far.rect('SILL', w0 - 6, w3 + 4, w2 + 6, w3 + 5, .1, 0)
    hole = (X >= w0) & (X < w2) & (Y >= w1) & (Y < w3)
    far.m[hole] = 0
    far.rect('TRIM', (w0 + w2) / 2 - .5, w1, (w0 + w2) / 2 + 1.5, w3, .2, 0)
    far.rect('TRIM', w0, (w1 + w3) / 2 - .5, w2, (w1 + w3) / 2 + 1.5, .2, 0)
    # ── mid：地板（木條透視）
    fl = mid.pmask([(wx0, wy1), (wx1, wy1), (209, 290), (209, 434), (-14, 434), (-14, 290)])
    vx, vy = G['vp']
    # 每條木條 id：用 x 投影
    u = vx + (X - vx) * (wy1 - vy) / np.maximum(Y - vy, 1)       # 投影返後牆嘅 x
    plank = np.floor((u - wx0) / 10).astype(int)
    depth = np.clip((Y - wy1) / 120, 0, 1)
    nz = rng.random(64)
    ff = np.clip(.42 + .28 * nz[plank % 64] + .18 * depth - .08 * ((u - wx0) / (wx1 - wx0)), 0, 1)
    mid.put(fl, 'FLOOR', ff, .4)
    seam = fl & (np.abs((u - wx0) / 10 - np.round((u - wx0) / 10)) * 10 * (Y - vy) / (wy1 - vy) < .55)
    mid.put(seam, 'SEAM', 1, 0)
    # 橫向接縫（交錯）
    for i, yy in enumerate(range(252, 434, 17)):
        yy2 = yy + (yy - 238) * .25
        m = fl & (np.abs(Y - yy2) < .5) & (((plank + i) % 3) == 0)
        mid.put(m, 'SEAM', 1, 0)
    mid.put(fl & (Y < wy1 + 1), 'SEAM', 1, 0)
    # ── fore：左上吊籃植物、右下盆栽、左下小盆（唔遮活動區）
    for (ox, oy, r) in [(-6, 18, 9), (4, 24, 8), (-10, 30, 7), (2, 34, 6)]:
        fore.ell('LEAF', ox, oy, r, r * .8)
    fore.line('VINE', [(-14, -12), (-2, 10)], 1, .2); fore.line('VINE', [(10, -12), (-2, 10)], 1, .2)
    fore.ell('POT', -2, 14, 9, 5, d=0)
    for (sx, sy, ln) in [(-4, 34, 22), (6, 36, 30), (12, 30, 18)]:
        pts = [(sx + 2 * math.sin(t / 4), sy + t) for t in range(ln)]
        fore.line('VINE', pts, 1, .7)
        for t in range(3, ln, 5): fore.ell('LEAF', sx + 2 * math.sin(t / 4) + (2 if t % 10 else -2), sy + t, 2.4, 1.6, d=0)
    # 右下盆栽（大葉）
    fore.poly('POT', [(184, 330), (209, 330), (209, 360), (188, 360)], .55)
    fore.rect('POT', 182, 326, 209, 331, .95, 0)
    for (ox, oy, r, a) in [(190, 300, 11, -.5), (202, 290, 12, .2), (196, 312, 10, .9), (208, 310, 9, 0)]:
        fore.ell('LEAF', ox, oy, r * .7, r)
    fore.rect('POT', -14, 340, 6, 362, .4); fore.ell('LEAF', -4, 334, 9, 7); fore.ell('LEAF', 4, 330, 6, 5)
    return dict(sky=sky, far=far, mid=mid, fore=fore)

def palette(night):
    pal = {}
    for n, lv in MATS:
        cols = (NIGHT_SKY.get(n) if night else None) or BASE[n]
        for i, idx in enumerate(IDX[n]): pal[idx] = hx(cols[i])
    return pal

GRADE = {
 'day': dict(variant='day', name='屋仔・日間（窗光暖調）', hours='06–19', ambientTint='#fff2e2', petTint='#fff8f2', saturation=1.05, contrast=1.04,
             bloom=dict(threshold=0.8, intensity=0.35), fog=dict(color='#ffe8d0', density=0.03), dof=dict(far=0, mid=0, fore=0.8),
             vignette=0.2, rim=dict(color='#ffe2b0', intensity=0.45, dir=[-0.7, -0.7]), bulbGlowTint='#ffe9a0',
             particles=dict(type='dust_mote', area='windowBeam', rate=0.5, color='#fff2c8')),
 'night': dict(variant='night', name='屋仔・夜晚（月光＋燈）', hours='19–06', ambientTint='#b4b8e4', petTint='#f2eaff', saturation=0.96, contrast=1.06,
               bloom=dict(threshold=0.7, intensity=0.6), fog=dict(color='#2a2e5a', density=0.06), dof=dict(far=0, mid=0, fore=0.8),
               vignette=0.32, rim=dict(color='#c8d4ff', intensity=0.35, dir=[-0.7, -0.7]), bulbGlowTint='#ffe0a0',
               particles=dict(type='none')),
}
def grade_rgb(rgb, g):
    t = hx(g['ambientTint']) / 255; c = rgb * t
    l = c @ np.array([.299, .587, .114]); c = l[..., None] + (c - l[..., None]) * g['saturation']
    c = (c - 128) * g['contrast'] + 128
    return np.clip(c, 0, 255)

def lights(night):
    """lightmap（multiply）、light_add（additive）、emissive（0/255）"""
    Y, X = np.mgrid[0:LH, 0:LW].astype(float); X = X + .5 - MX; Y = Y + .5 - MY
    wx0, wy0, wx1, wy1 = G['wall']; w0, w1, w2, w3 = G['window']
    lm = np.ones((LH, LW, 3))
    # AO：天花角、牆腳、側牆暗啲、右邊少少暗（光由左上嚟）
    ao = np.exp(-np.maximum(0, Y - wy1) / 10) * (Y >= wy1) * .14
    ao += np.exp(-np.abs(Y - wy0) / 6) * .12
    ao += (np.clip((X - 100) / 140, 0, 1)) * .08
    side = ((X < wx0) | (X > wx1)) & (Y < 300)
    ao += side * .08
    ao += np.clip((Y - 330) / 140, 0, 1) * .10                                  # 前景底部收暗
    lm -= ao[..., None]
    la = np.zeros((LH, LW, 3))
    beam = Image.new('L', (LW, LH), 0); d = ImageDraw.Draw(beam)
    # 窗光：由窗洞斜落地板（左上 → 右下）
    d.polygon([A(w0, w1), A(w2, w1), A(w2 + 46, 288), A(w0 + 34, 300)], fill=120)
    d.polygon([A(w0 + 30, 266), A(w2 + 44, 262), A(w2 + 54, 300), A(w0 + 36, 306)], fill=150)
    bm = np.asarray(beam.filter(ImageFilter.GaussianBlur(5))).astype(float) / 255
    if night:
        lm *= np.array([.58, .6, .78])
        lm += bm[..., None] * np.array([.10, .12, .2])
        la += bm[..., None] * np.array([10, 14, 30])
    else:
        la += bm[..., None] * np.array([62, 46, 22])
    em = np.zeros((LH, LW), np.uint8)
    em[(X >= w0) & (X < w2) & (Y >= w1) & (Y < w3)] = 255
    emc = np.array([70, 80, 120]) if night else np.array([255, 236, 200])
    eb = np.asarray(Image.fromarray(em).filter(ImageFilter.GaussianBlur(4))).astype(float)[..., None] / 255 * emc * (.5 if night else .8)
    # vignette
    yy, xx = np.mgrid[0:AH, 0:AW].astype(float); r = np.hypot((xx - AW / 2) / (AW * .62), (yy - AH * .48) / (AH * .62))
    va = (np.clip(r - .55, 0, 1) / .45) ** 1.6 * (.32 if night else .2) * 255
    vg = np.zeros((AH, AW, 4), np.uint8); vg[..., :3] = (20, 14, 40) if night else (60, 34, 30); vg[..., 3] = va.clip(0, 255).astype(np.uint8)
    return lm.clip(0, 1), la.clip(0, 255), em, eb.clip(0, 255), vg

def build_room(out_dir):
    meta = {}
    for var in ('day', 'night'):
        night = var == 'night'; L = build_index(night); pal = palette(night); g = GRADE[var]
        d = os.path.join(out_dir, var); os.makedirs(os.path.join(d, 'raw'), exist_ok=True)
        used = set()
        for name, lay in L.items():
            rgb = np.zeros((LH, LW, 3)); a = (lay.m > 0)
            for i in np.unique(lay.m[a]): rgb[lay.m == i] = pal[int(i)]; used.add(int(i))
            raw = np.zeros((LH, LW, 4), np.uint8); raw[..., :3] = rgb.astype(np.uint8); raw[..., 3] = a * 255
            if name == 'sky': raw[..., 3] = 255
            Image.fromarray(raw).save(os.path.join(d, 'raw', f'{name}.png'))
            fin = raw.copy(); fin[..., :3] = grade_rgb(rgb, g).astype(np.uint8)
            im = Image.fromarray(fin)
            if name == 'fore':                                   # 前景輕微景深
                im = im.filter(ImageFilter.GaussianBlur(g['dof']['fore'] * .6))
            im.save(os.path.join(d, f'{name}.png'))
        lm, la, em, eb, vg = lights(night)
        Image.fromarray((lm * 255).astype(np.uint8)).save(os.path.join(d, 'lightmap.png'))
        Image.fromarray(la.astype(np.uint8)).save(os.path.join(d, 'light_add.png'))
        e = np.zeros((LH, LW, 4), np.uint8); e[em > 0] = (255, 255, 255, 255); Image.fromarray(e).save(os.path.join(d, 'emissive.png'))
        Image.fromarray(eb.astype(np.uint8)).save(os.path.join(d, 'emissive_blur.png'))
        Image.fromarray(vg).save(os.path.join(d, 'vignette.png'))
        json.dump(g, open(os.path.join(d, 'grade.json'), 'w'), ensure_ascii=False, indent=1)
        json.dump({str(i): tohex(pal[i]) for i in sorted(used)}, open(os.path.join(d, 'palette.json'), 'w'), indent=0)
        meta[var] = {'colors': len(used)}
    return meta

def compose(var, base_dir, sprites=(), offs=None, extra_add=None):
    """預覽合成（同 FORMAT.md 公式）：sprites=[(z, img RGBA np, x, y, kind)]（art 座標、mid 層之後畫）；回傳 195×422 RGB np"""
    d = os.path.join(base_dir, var); g = json.load(open(os.path.join(d, 'grade.json')))
    ld = lambda n: np.asarray(Image.open(os.path.join(d, n)).convert('RGBA')).astype(float)
    C = np.zeros((LH, LW, 3))
    def over(img):
        a = img[..., 3:4] / 255; C[:] = C * (1 - a) + img[..., :3] * a
    for n in ('sky', 'far', 'mid'): over(ld(n + '.png'))
    amb = hx(g['ambientTint']) / 255; pt = hx(g['petTint']) / 255
    for z, img, x, y, kind in sorted(sprites, key=lambda s: s[0]):
        im = img.astype(float).copy(); im[..., :3] *= amb * (pt if kind == 'pet' else 1)
        if kind == 'glow':          # additive glow（8-bit alpha）
            gx, gy = int(x + MX), int(y + MY); h, w = im.shape[:2]
            x0, y0 = max(0, gx), max(0, gy); x1, y1 = min(LW, gx + w), min(LH, gy + h)
            if x1 > x0 and y1 > y0: C[y0:y1, x0:x1] += img[y0 - gy:y1 - gy, x0 - gx:x1 - gx, :3].astype(float) * img[y0 - gy:y1 - gy, x0 - gx:x1 - gx, 3:4] / 255 * .9
            continue
        if kind == 'shadow':
            gx, gy = int(x + MX), int(y + MY); h, w = im.shape[:2]
            x0, y0 = max(0, gx), max(0, gy); x1, y1 = min(LW, gx + w), min(LH, gy + h)
            a = img[y0 - gy:y1 - gy, x0 - gx:x1 - gx, 3:4] / 255
            C[y0:y1, x0:x1] = C[y0:y1, x0:x1] * (1 - a) + np.array([60, 36, 40]) * a
            continue
        gx, gy = int(x + MX), int(y + MY); h, w = im.shape[:2]
        x0, y0 = max(0, gx), max(0, gy); x1, y1 = min(LW, gx + w), min(LH, gy + h)
        if x1 <= x0 or y1 <= y0: continue
        s = im[y0 - gy:y1 - gy, x0 - gx:x1 - gx]; m = s[..., 3] >= 128
        C[y0:y1, x0:x1][m] = s[..., :3][m]
    over(ld('fore.png'))
    lm = np.asarray(Image.open(os.path.join(d, 'lightmap.png')).convert('RGB')).astype(float) / 255
    la = np.asarray(Image.open(os.path.join(d, 'light_add.png')).convert('RGB')).astype(float)
    eb = np.asarray(Image.open(os.path.join(d, 'emissive_blur.png')).convert('RGB')).astype(float)
    C = C * lm + la + eb * g['bloom']['intensity']
    if extra_add is not None: C += extra_add
    C = C * (1 - g['fog']['density']) + hx(g['fog']['color']) * g['fog']['density']
    C = C[MY:MY + AH, MX:MX + AW]
    vg = np.asarray(Image.open(os.path.join(d, 'vignette.png'))).astype(float); a = vg[..., 3:4] / 255
    C = C * (1 - a) + vg[..., :3] * a
    return C.clip(0, 255).astype(np.uint8)
