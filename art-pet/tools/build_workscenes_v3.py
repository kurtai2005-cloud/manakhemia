# -*- coding: utf-8 -*-
"""第 8 批 工作場景 V3-A（GDD family-work-scenes-v1 §2.1）。全 procedural（Pillow/numpy），唔用 AI 圖。
輸出 art-pet/scenes/work_v3/：5 張背景（瞭望台日／夜）、8 個可撳道具、Lv3 裝飾 4、Lv5 職業帽 4×S/M/L、
24 個工作 clip（S/M/L × 4 職 × loop/done）、8 個產品 icon 48px、UI 部件、mockup（疊 UI v3）。
用法：PYTHONDONTWRITEBYTECODE=1 python3 build_workscenes_v3.py"""
import os, sys, json, math
import numpy as np
from PIL import Image, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ws3_px import *
import ws3_scenes as SC
ART = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
OUT = f'{ART}/scenes/work_v3'
S = 3; W3, H3 = LW * S, LH * S; SW3, SH3 = AW * S, AH * S
JOBS = ['post', 'garden', 'tower', 'kitchen']
JOB_ZH = {'post': '郵局', 'garden': '花園', 'tower': '瞭望台', 'kitchen': '廚房'}
SCENE_KEYS = ['post', 'garden', 'tower_day', 'tower_night', 'kitchen']

def f01(im): return np.asarray(im).astype(float) / 255
def to8(a): return (np.clip(a, 0, 1) * 255 + .5).astype(np.uint8)
def save(a, p):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if isinstance(a, Image.Image): a.save(p, optimize=True); return
    a = to8(a); Image.fromarray(a, 'RGBA' if a.shape[-1] == 4 else 'RGB').save(p, optimize=True)
def up3(im): return im.resize((im.width * S, im.height * S), Image.NEAREST)
def blur(a, s):
    """浮點高斯模糊（scipy.ndimage，逐通道）。"""
    from scipy.ndimage import gaussian_filter
    if a.ndim == 2: return gaussian_filter(a.astype(float), s, mode='nearest')
    return np.stack([gaussian_filter(a[..., i].astype(float), s, mode='nearest') for i in range(a.shape[-1])], -1)
def blur_rgba(a, s):
    pm = np.concatenate([a[..., :3] * a[..., 3:], a[..., 3:]], -1); b = blur(pm, s); al = b[..., 3:]
    return np.concatenate([b[..., :3] / np.maximum(al, 1e-4), al], -1)
def hxf(c): return np.array(hx(c), float) / 255
def L3(x, y): return ((x + MX) * S, (y + MY) * S)

# ================================================================ ① 場景烘焙
GRADE = {
 'post':        dict(name='郵局', ambient='#d8c4ae', ambientK=.80, petTint='#fff4e6', rim=dict(color='#ffe2a8', dir=[-1, -.4], intensity=.55), bloom=dict(threshold=.7, intensity=.55), fog=dict(color='#f6e2c0', density=.03), vig='#2a1608', vignette=.55, sat=1.08, warm=1.0),
 'garden':      dict(name='花園', ambient='#ffffff', ambientK=.92, petTint='#ffffff', rim=dict(color='#fff2c8', dir=[1, -.6], intensity=.6), bloom=dict(threshold=.78, intensity=.45), fog=dict(color='#f4f6e6', density=.03), vig='#1c2a14', vignette=.42, sat=1.1, warm=.8),
 'tower_day':   dict(name='瞭望台・日', ambient='#ffffff', ambientK=.94, petTint='#ffffff', rim=dict(color='#fff6dc', dir=[-1, -.5], intensity=.55), bloom=dict(threshold=.8, intensity=.4), fog=dict(color='#eef4fc', density=.04), vig='#1a2238', vignette=.4, sat=1.06, warm=.6),
 'tower_night': dict(name='瞭望台・夜', ambient='#8a98d8', ambientK=.8, petTint='#c8d0ff', rim=dict(color='#bcd0ff', dir=[.6, -1], intensity=.75), bloom=dict(threshold=.55, intensity=.8), fog=dict(color='#1a2450', density=.05), vig='#05081a', vignette=.7, sat=1.05, warm=-.3),
 'kitchen':     dict(name='廚房', ambient='#d6c2ae', ambientK=.80, petTint='#fff0e0', rim=dict(color='#ffc890', dir=[1, -.2], intensity=.6), bloom=dict(threshold=.68, intensity=.6), fog=dict(color='#f8dcc0', density=.03), vig='#2a1206', vignette=.55, sat=1.08, warm=1.1),
}
# 非瞭望台場景跟遊戲時間轉色（runtime 乘色＋加光比例＋emissive 比例）；瞭望台用日／夜兩張
TOD = {'dawn': dict(hours=[5, 8], mul='#ffd9c4', add=.8, emissive=.7), 'day': dict(hours=[8, 17], mul='#ffffff', add=1.0, emissive=.35),
       'dusk': dict(hours=[17, 20], mul='#ffbf94', add=.75, emissive=.95), 'night': dict(hours=[20, 5], mul='#6c78b4', add=.3, emissive=1.45)}
EMIT = {
 'post': [dict(type='dust', rect=[20, 90, 120, 330], max=16, tint='#fff0c8', alpha=.55, src='scenes/hd2d_v3/fx/particles_v3@3x#dust'),
          dict(type='paper', rect=[90, 80, 186, 190], max=4, tint='#ffffff', alpha=1, src='work_v3/fx/particles_work@3x#paper')],
 'garden': [dict(type='pollen', rect=[0, 120, 195, 360], max=18, tint='#fff6b0', alpha=.7, src='scenes/hd2d_v3/fx/particles_v3@3x#pollen'),
            dict(type='petal', rect=[90, 70, 195, 330], max=8, tint='#ffd0dc', alpha=1, src='scenes/hd2d_v3/fx/particles_v3@3x#petal')],
 'tower_day': [dict(type='mote', rect=[0, 100, 195, 330], max=10, tint='#ffffff', alpha=.5, src='scenes/hd2d_v3/fx/particles_v3@3x#mote')],
 'tower_night': [dict(type='twinkle', rect=[10, 70, 185, 200], max=14, tint='#ffffff', alpha=1, src='work_v3/fx/particles_work@3x#twinkle'),
                 dict(type='firefly', rect=[0, 220, 195, 340], max=8, tint='#d8ff9a', alpha=1, src='scenes/hd2d_v3/fx/particles_v3@3x#firefly')],
 'kitchen': [dict(type='steam', rect=[130, 150, 180, 230], max=8, tint='#ffffff', alpha=.8, src='work_v3/fx/particles_work@3x#steam'),
             dict(type='ember', rect=[138, 220, 172, 246], max=6, tint='#ffb050', alpha=1, src='work_v3/fx/particles_work@3x#ember'),
             dict(type='dust', rect=[10, 100, 110, 320], max=10, tint='#fff0c8', alpha=.5, src='scenes/hd2d_v3/fx/particles_v3@3x#dust')],
}

def ray_field(src, toward, strength, spread, seed=3):
    """體積光：由 src 指向 toward 嘅光錐＋條紋，@3x 解像。"""
    rnd = np.random.RandomState(seed); yy, xx = np.mgrid[0:H3, 0:W3].astype(float)
    sx, sy = L3(*src); tx, ty = L3(*toward); a0 = math.atan2(ty - sy, tx - sx)
    ang = np.arctan2(yy - sy, xx - sx) - a0; ang = (ang + np.pi) % (2 * np.pi) - np.pi; d = np.hypot(xx - sx, yy - sy)
    n = np.zeros_like(ang)
    for k in (23, 41, 67, 97, 131): n += np.sin(ang * k + rnd.rand() * 6.28) / k ** .3
    n = ((n - n.min()) / (n.max() - n.min())) ** 2.2
    win = np.clip(1 - np.abs(ang) / spread, 0, 1) ** 1.4
    L = np.hypot(tx - sx, ty - sy); fall = np.clip(1 - d / (L * 1.25), 0, 1) * np.clip(d / 60, 0, 1)
    return (.35 + .65 * n) * win * fall * strength
def radial(c, r, k=2.0):
    yy, xx = np.mgrid[0:H3, 0:W3].astype(float); cx, cy = L3(*c); d = np.hypot(xx - cx, yy - cy) / (r * S)
    return np.clip(1 - d, 0, 1) ** k
def ellpool(rect, k=1.6):
    yy, xx = np.mgrid[0:H3, 0:W3].astype(float); x0, y0 = L3(rect[0], rect[1]); x1, y1 = L3(rect[2], rect[3])
    cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
    return np.clip(1 - np.hypot((xx - cx) / rx, (yy - cy) / ry), 0, 1) ** k

def bake_scene(key):
    d = f'{OUT}/{key}'; g = GRADE[key]; layers, lt = SC.SCENES[key]()
    seeds = dict(sky=1, far=2, mid=3, fore=4); L1 = {}
    for n, l in layers.items():
        im = binarize(texturize(l.im, 5 if n != 'sky' else 3, seeds[n] + sum(map(ord, key)) % 97)); L1[n] = im; save(im, f'{d}/{n}.png')
    # ---- 光照（@3x 計，1x 版由 @3x 縮細）
    amb = hxf(g['ambient']) * g['ambientK']; lm = np.ones((H3, W3, 3)) * amb
    yy, xx = np.mgrid[0:H3, 0:W3].astype(float)
    edge = np.clip(1 - (((xx / W3 - .5) / .62) ** 2 + ((yy / H3 - .52) / .7) ** 2), 0, 1) ** .6
    lm *= (.78 + .22 * edge)[..., None]
    add = np.zeros((H3, W3, 3))
    r = lt.get('rays')
    if r:
        f = ray_field(r['src'], r['toward'], r['strength'], r['spread'], seed=len(key)); add += f[..., None] * hxf(r['col'])
        lm += (np.clip(f * 1.4, 0, .25))[..., None]
    for lp in lt.get('lamps', []):
        p = radial(lp['pos'], lp['r'], 1.6); add += p[..., None] * hxf(lp['col']) * .55; lm += p[..., None] * .18
    for rc in lt.get('floorPool', []): p = ellpool(rc); add += p[..., None] * hxf('#ffe2b0') * .16
    if lt.get('dapple'):
        rnd = np.random.RandomState(9); dp = np.zeros((H3, W3))
        for i in range(70):
            cx, cy = rnd.uniform(0, W3), rnd.uniform(L3(0, 240)[1], H3); rr = rnd.uniform(10, 30)
            dp += np.exp(-(((xx - cx) / (rr * 1.6)) ** 2 + ((yy - cy) / rr) ** 2))
        dp = np.clip(dp, 0, 1); lm *= (1 - .16 * (1 - dp))[..., None]; add += (dp * .07)[..., None] * hxf('#fff2c0')
    if lt.get('night'):
        p = radial((97, 300), 80, 1.2); lm += p[..., None] * np.array([.05, .06, .1])
    lm = np.clip(lm, 0, 1); add = np.clip(add, 0, 1)
    save(lm, f'{d}/x3/lightmap@3x.png'); save(add, f'{d}/x3/light_add@3x.png')
    save(Image.fromarray(to8(lm)).resize((LW, LH), Image.BILINEAR), f'{d}/lightmap.png'); save(Image.fromarray(to8(add)).resize((LW, LH), Image.BILINEAR), f'{d}/light_add.png')
    # ---- emissive（0/255）：窗玻璃、燈泡、爐火、月
    em = np.zeros((LH, LW, 4)); comp1 = np.zeros((LH, LW, 3))
    for n in ('sky', 'far', 'mid', 'fore'): a = f01(L1[n]); comp1 = comp1 * (1 - a[..., 3:]) + a[..., :3] * a[..., 3:]
    farA = f01(L1['far'])[..., 3]; midA = f01(L1['mid'])[..., 3]; foreA = f01(L1['fore'])[..., 3]
    for (x0, y0, x1, y1, col, k) in lt.get('emissiveRects', []):
        sl = (slice(y0 + MY, y1 + MY + 1), slice(x0 + MX, x1 + MX + 1)); hole = (foreA[sl] == 0)
        if key == 'kitchen' and col == '#ffb050': hole &= (comp1[sl] @ np.array([.3, .5, .2]) > .55)
        elif key == 'tower_night': hole &= comp1[sl].mean(-1) > .8
        else: hole &= farA[sl] == 0
        em[sl][hole, :3] = np.clip(comp1[sl][hole] * (1 - k) + hxf(col) * k, 0, 1); em[sl][hole, 3] = 1
    for lp in lt.get('lamps', []):
        if lp['r'] <= 12 or key == 'kitchen' or lp.get('bulb') is False: continue
        x, y = lp['pos']; em[y + MY - 1:y + MY + 2, x + MX - 3:x + MX + 4, :3] = hxf('#fff6d0'); em[y + MY - 1:y + MY + 2, x + MX - 3:x + MX + 4, 3] = 1
    if key == 'tower_night':
        x, y = 163, 166; em[y + MY:y + MY + 2, x + MX, :3] = hxf('#ffd27a'); em[y + MY:y + MY + 2, x + MX, 3] = 1
        st = (comp1.max(-1) > .93) & (foreA == 0) & (midA == 0) & (farA == 0); st[:, :] &= np.arange(LH)[:, None] < 236
        em[st, :3] = comp1[st]; em[st, 3] = 1
    em[..., 3] = (em[..., 3] > .5).astype(float); em[em[..., 3] == 0] = 0
    save(em, f'{d}/emissive.png')
    eb = np.clip(blur(em[..., :3] * em[..., 3:], 3) * .6 + blur(em[..., :3] * em[..., 3:], 8) * .8, 0, 1); save(eb, f'{d}/emissive_blur.png')
    # ---- @3x 層：sky 輕柔化、far DoF、mid 銳利、fore DoF
    X = {n: f01(up3(L1[n])) for n in L1}
    X['sky'] = np.concatenate([blur(X['sky'][..., :3], 1.2), X['sky'][..., 3:]], -1)
    X['far'] = blur_rgba(X['far'], 1.1 if 'tower' in key or key == 'garden' else .6)
    X['fore'] = blur_rgba(X['fore'], 1.8)
    for n in X: save(X[n], f'{d}/x3/{n}@3x.png')
    em3 = f01(up3(Image.fromarray(to8(em), 'RGBA'))); save(em3, f'{d}/x3/emissive@3x.png')
    # haze_far（遠景地平線霧）＋mist（地面低霧）
    hz = np.zeros((H3, W3, 4)); hy = L3(0, 214 if 'tower' in key else 226)[1]
    hz[..., :3] = hxf(g['fog']['color']); hz[..., 3] = np.exp(-((yy - hy) / (40 if 'tower' in key else 26)) ** 2) * (.22 if 'tower' in key else .16)
    ms = np.zeros((H3, W3, 4)); ms[..., :3] = hxf(g['fog']['color']); my = L3(0, 250)[1]
    ms[..., 3] = np.clip((yy - my) / 60, 0, 1) * np.exp(-((yy - my) / 150) ** 2) * (.07 + .03 * np.sin(xx / 47) * np.sin(yy / 23))
    save(hz, f'{d}/x3/haze_far@3x.png'); save(ms, f'{d}/x3/mist@3x.png')
    # bloom：亮位＋emissive
    comp = X['sky'][..., :3]
    for n in ('far', 'mid', 'fore'): comp = comp * (1 - X[n][..., 3:]) + X[n][..., :3] * X[n][..., 3:]
    comp = np.clip(comp * lm + add, 0, 1); t = g['bloom']['threshold']
    lum = comp @ np.array([.3, .55, .15]); br = comp * np.clip((lum - t) / (1 - t), 0, 1)[..., None] + em3[..., :3] * em3[..., 3:] * .9
    bl = np.clip(blur(br, 6) * .55 + blur(br, 20) * .6, 0, 1); save(bl, f'{d}/x3/bloom@3x.png')
    # vignette
    sy_, sx_ = np.mgrid[0:SH3, 0:SW3].astype(float); dd = ((sx_ / SW3 - .5) / .5) ** 2 + ((sy_ / SH3 - .48) / .5) ** 2
    vg = np.zeros((SH3, SW3, 4)); vg[..., :3] = hxf(g['vig']); vg[..., 3] = np.clip(np.clip((dd - .35) / .9, 0, 1) ** 1.5 * g['vignette'] * 1.0, 0, 1)
    save(vg, f'{d}/x3/vignette@3x.png'); save(Image.fromarray(to8(vg)).resize((AW, AH), Image.BILINEAR), f'{d}/vignette.png')
    # LUT 256×16（grade：飽和＋暖冷 split-tone）
    lut = np.zeros((16, 256, 3))
    for b in range(16):
        for gg in range(16):
            for rr in range(16): lut[gg, b * 16 + rr] = [rr / 15, gg / 15, b / 15]
    l = lut @ np.array([.299, .587, .114]); lut = l[..., None] + (lut - l[..., None]) * g['sat']
    lut = lut + np.array([.03, .01, -.03]) * g['warm'] * l[..., None] + np.array([-.01, 0, .025]) * (1 - l[..., None]); save(np.clip(lut, 0, 1), f'{d}/lut.png')
    gj = dict(scene=key, name=g['name'], job=key.split('_')[0], **{k: g[k] for k in ('ambient', 'petTint', 'rim', 'bloom', 'fog', 'vignette')})
    gj['ambientTint'] = '#ffffff'; gj['foot'] = list(SC.FOOT)
    if 'tower' not in key: gj['tod'] = TOD; gj['todNote'] = 'runtime：(sky→fore 合成)×tod.mul，light_add×tod.add，emissive／bloom×tod.emissive；按遊戲時鐘喺 hours 之間 600ms 漸變。'
    else: gj['variantHours'] = [6, 18] if key == 'tower_day' else [18, 6]; gj['todNote'] = '瞭望台用日／夜兩張：06–18 日、18–06 夜（夜更 21–05 必定係夜版）；換版 crossfade 1200ms。'
    gj['emitters'] = EMIT[key]
    gj['petLight'] = dict(sprite='scenes/hd2d_v3/fx/fx_glow_v3@3x.json#pet_pool', anchor='foot', offset3x=[0, 6], size3x=[240, 96], blend='lighter',
                          intensity=.55 if key != 'tower_night' else .8, multiplyBy='petGlow',
                          rule='ui/kit_hd2d_v3/layout_hd2d_v3.json#petGlow：awake 1／sleepy .6／sleep・sleepClip・dreamEnter・dreaming 0；淡出 600ms easeInQuad、淡入 400ms easeOutQuad＋150ms pulse 1→1.15→1。場景燈（窗、吊燈、爐火、月、道具燈）唔受影響。')
    gj['lights'] = lt
    json.dump(gj, open(f'{d}/grade.json', 'w'), ensure_ascii=False, indent=1)
    cols = set()
    for n in L1: a = np.asarray(L1[n]); cols |= {tuple(c) for c in a[a[..., 3] > 0][:, :3].reshape(-1, 3)[::7]}
    json.dump(dict(scene=key, approxColors=len(cols), note='procedural 繪製後加 3 級噪點紋理；sprite 層 alpha 0/255'), open(f'{d}/palette.json', 'w'), ensure_ascii=False, indent=1)
    print('scene', key, 'ok')


# ================================================================ 合成（預覽／mockup 用；同 runtime 疊法一樣）
_LD = {}
def ld(p):
    if p not in _LD: _LD[p] = f01(Image.open(p).convert('RGBA'))
    return _LD[p]
def oversp(img, sp, x0, y0):
    h, w = sp.shape[:2]; xa, ya, xb, yb = max(0, x0), max(0, y0), min(img.shape[1], x0 + w), min(img.shape[0], y0 + h)
    if xa >= xb or ya >= yb: return
    s_ = sp[ya - y0:yb - y0, xa - x0:xb - x0]; img[ya:yb, xa:xb] = img[ya:yb, xa:xb] * (1 - s_[..., 3:]) + s_[..., :3] * s_[..., 3:]
def addsp(img, sp, x0, y0, k=1.0, col=None):
    h, w = sp.shape[:2]; xa, ya, xb, yb = max(0, x0), max(0, y0), min(img.shape[1], x0 + w), min(img.shape[0], y0 + h)
    if xa >= xb or ya >= yb: return
    s_ = sp[ya - y0:yb - y0, xa - x0:xb - x0]; c = s_[..., :3] if col is None else hxf(col)
    img[ya:yb, xa:xb] += c * s_[..., 3:] * k
def compose3x(key, mids=(), fronts=(), adds=(), pet=None, pet_glow=1.0, tod=None, particles=True, seed=5, skys=(), backs=()):
    """mids：[(rgba@3x, x0, y0)] 喺 mid 之後（道具／擺設）；pet：dict(img,x0,y0,foot,size)；fronts：寵物之後 fore 之前；adds：光層（lighter）。"""
    d = f'{OUT}/{key}'; g = json.load(open(f'{d}/grade.json')); X = {n: ld(f'{d}/x3/{n}@3x.png') for n in ('sky', 'far', 'haze_far', 'mid', 'mist', 'fore')}
    img = X['sky'][..., :3].copy()
    for (sp, x0, y0) in skys: oversp(img, sp, x0, y0)
    for n in ('far', 'haze_far', 'mid'): img = img * (1 - X[n][..., 3:]) + X[n][..., :3] * X[n][..., 3:]
    for (sp, x0, y0) in mids: oversp(img, sp, x0, y0)
    img = img * (1 - X['mist'][..., 3:]) + X['mist'][..., :3] * X['mist'][..., 3:]
    if pet is not None:
        cx, cy = L3(*pet['foot']); yy, xx = np.mgrid[0:H3, 0:W3]
        shd = np.exp(-(((xx - cx) / (pet['w'] * .34)) ** 2 + ((yy - cy - 2) / 9) ** 2) ** 2) * .34; img *= 1 - shd[..., None]
        pool = fxsp('glow_pool'); k = g['petLight']['intensity'] * pet_glow
        if k > 0: addsp(img, pool, int(cx - pool.shape[1] / 2), int(cy + 6 - pool.shape[0] / 2), k * .5, g['rim']['color'])
        for (sp, x0, y0) in backs: oversp(img, sp, x0, y0)
        oversp(img, pet['img'], pet['x0'], pet['y0'])
    for (sp, x0, y0) in fronts: oversp(img, sp, x0, y0)
    img = img * (1 - X['fore'][..., 3:]) + X['fore'][..., :3] * X['fore'][..., 3:]
    T = TOD[tod] if tod else dict(mul='#ffffff', add=1, emissive=1 if 'tower' in key else (.35 if key == 'garden' else .6))
    if tod: img = img * hxf(T['mul'])
    img = img * ld(f'{d}/x3/lightmap@3x.png')[..., :3] + ld(f'{d}/x3/light_add@3x.png')[..., :3] * T['add']
    em = ld(f'{d}/x3/emissive@3x.png'); img = img * (1 - em[..., 3:] * T['emissive']) + em[..., :3] * em[..., 3:] * T['emissive']
    img += ld(f'{d}/x3/bloom@3x.png')[..., :3] * g['bloom']['intensity'] * (T['emissive'] if tod else 1)
    for (sp, x0, y0, k) in adds: addsp(img, sp, x0, y0, k)
    if particles:
        rnd = np.random.RandomState(seed)
        for e in g['emitters']:
            for i in range(e['max'] // 2 + 2):
                x, y = L3(rnd.uniform(e['rect'][0], e['rect'][2]), rnd.uniform(e['rect'][1], e['rect'][3]))
                if pet is not None and abs(x - L3(*pet['foot'])[0]) < 60 and -150 < y - L3(*pet['foot'])[1] < 0: continue
                sp = fxsp(f"{e['type']}_{1 + i % 6:02d}")
                if e['type'] in ('dust', 'pollen', 'mote', 'firefly', 'twinkle', 'ember'): addsp(img, fxsp('glow_s'), int(x - 18), int(y - 18), e['alpha'] * .5, e['tint'])
                oversp(img, sp * np.array([1, 1, 1, e['alpha']]), int(x - sp.shape[1] / 2), int(y - sp.shape[0] / 2))
    fc = hxf(g['fog']['color']); img = img * (1 - g['fog']['density']) + fc * g['fog']['density']
    img = np.clip(img, 0, 1)[MY * S:MY * S + SH3, MX * S:MX * S + SW3]
    vg = ld(f'{d}/x3/vignette@3x.png'); img = img * (1 - vg[..., 3:]) + vg[..., :3] * vg[..., 3:]
    return Image.fromarray(to8(img), 'RGB')
_FXS = {}
def fxsp(name):
    if not _FXS:
        for p in (f'{ART}/scenes/hd2d_v3/fx/particles_v3@3x', f'{ART}/scenes/hd2d_v3/fx/fx_glow_v3@3x', f'{OUT}/fx/particles_work@3x'):
            if not os.path.exists(p + '.png'): continue
            sh_ = ld(p + '.png'); js = json.load(open(p + '.json'))['frames']
            for k, f in js.items(): _FXS[k] = sh_[f['y']:f['y'] + f['h'], f['x']:f['x'] + f['w']]
        yy, xx = np.mgrid[0:96, 0:240].astype(float); a = np.clip(1 - np.hypot((xx - 120) / 120, (yy - 48) / 48), 0, 1) ** 2
        _FXS['glow_pool'] = np.dstack([np.ones((96, 240, 3)), a])
        yy, xx = np.mgrid[0:36, 0:36].astype(float); a = np.clip(1 - np.hypot(xx - 18, yy - 18) / 18, 0, 1) ** 2
        _FXS['glow_s'] = np.dstack([np.ones((36, 36, 3)), a])
    return _FXS.get(name, np.zeros((1, 1, 4)))


# ================================================================ ② sprites：道具／擺設／帽／icon／clip／粒子
import ws3_sprites as P
def im3(im): return up3(im if isinstance(im, Image.Image) else im.im)
def glow3(srcs, sigma=7, k=1.6):
    """光層（真 alpha）：1x 亮色 mask → @3x → 模糊；色＝來源色。"""
    out = []
    for g_ in srcs:
        a = f01(up3(g_ if isinstance(g_, Image.Image) else g_.im)); pm = a[..., :3] * a[..., 3:]
        b = blur(np.concatenate([pm, a[..., 3:]], -1), sigma) + blur(np.concatenate([pm, a[..., 3:]], -1), sigma * .4) * .6
        al = np.clip(b[..., 3] * k, 0, 1); col = b[..., :3] / np.maximum(b[..., 3:], 1e-4); out.append(np.dstack([np.clip(col, 0, 1), al]))
    return out
def sheet(frames, rows=1):
    """frames：list of PIL（或 list of rows）→ 橫排 sheet。"""
    rws = frames if rows > 1 else [frames]; w, h = rws[0][0].size; sh_ = Image.new('RGBA', (w * len(rws[0]), h * len(rws)), (0, 0, 0, 0))
    for r, row in enumerate(rws):
        for i, f in enumerate(row): sh_.alpha_composite(f, (i * w, r * h))
    return sh_
def sheetf(arrs):
    h, w = arrs[0].shape[:2]; o = np.zeros((h, w * len(arrs), 4))
    for i, a in enumerate(arrs): o[:, i * w:(i + 1) * w] = a
    return o
def size_classes():
    import build_ui_hd2d_v3_mockups as M3, hd2d_v2_px as X
    out = {}
    for f in M3.M.PR['forms']:
        im, inf = X.compose_pet(f, 'normal'); b = im.getbbox(); m = max(b[2] - b[0], b[3] - b[1])
        out[f] = dict(size='S' if m <= 32 else ('M' if m <= 40 else 'L'), bbox=[b[2] - b[0], b[3] - b[1]], headTop=inf['headTop'], eyes=[round(v, 1) for v in inf['eyes']], pivot=inf['pivot'])
    return out
CLIP_MS = {'loop': 110, 'done': 140}
CLIP_ZH = {('post', 'loop'): '分信入格', ('post', 'done'): '蓋印', ('garden', 'loop'): '淋水', ('garden', 'done'): '除草', ('tower', 'loop'): '望遠鏡掃天',
           ('tower', 'done'): '點燈', ('kitchen', 'loop'): '攪拌', ('kitchen', 'done'): '試味'}
def build_sprites():
    J = dict(props={}, decoLv3={}, hatsLv5={}, icons={}, clips={})
    for job, lst in P.PROPS.items():
        for name, fn in lst:
            pr = fn(); key = f'{job}_{name}'; fr = [binarize(f.im) for f in pr['frames']]
            if 'variants' in pr:
                rows = [[binarize(f.im) for f in r] for r in pr['variants']['rows']]; sh1 = sheet(rows, rows=len(rows))
            else: sh1 = sheet(fr)
            save(sh1, f'{OUT}/props/{key}.png'); save(up3(sh1), f'{OUT}/props/{key}@3x.png')
            ent = dict(zh=pr['zh'], sheet=f'props/{key}@3x.png', sheet1x=f'props/{key}.png', frames=len(fr), frameSize3x=[pr['size'][0] * S, pr['size'][1] * S],
                       anchor3x=[pr['anchor'][0] * S, pr['anchor'][1] * S], pos=pr['pos'], hit=pr['hit'], fps=pr['fps'], loop=pr['loop'], tap=pr['tap'],
                       layer=pr.get('layer', 'mid（同 mid 一齊位移；按腳底 y 同寵物 y-sort）'), effects='純視覺：唔改薪金／機率／上限，唔計委託／心情／親密', affectsGame=False)
            if 'variants' in pr: ent['variants'] = dict(ink=pr['variants']['ink'], rows=len(pr['variants']['rows']), rule='每撳一次行下一行（循環）')
            if 'glowSrc' in pr:
                gs = glow3(pr['glowSrc'], 6, 1.8); save(sheetf(gs), f'{OUT}/props/{key}_glow@3x.png'); ent['glow'] = dict(sheet=f'props/{key}_glow@3x.png', blend='lighter', note='道具燈屬場景燈：唔乘 petGlow')
            J['props'][key] = ent
        dc = P.DECOS[job](); img = binarize(dc['img'].im); save(img, f'{OUT}/deco_lv3/{job}.png'); save(up3(img), f'{OUT}/deco_lv3/{job}@3x.png')
        J['decoLv3'][job] = dict(zh=dc['zh'], img=f'deco_lv3/{job}@3x.png', pos=dc['pos'], anchor3x=[dc['anchor'][0] * S, dc['anchor'][1] * S], unlock='職業 Lv3', note=dc['note'], layer='mid（y-sort）')
        hs = {}
        for sz in ('S', 'M', 'L'):
            h_, anc = P.hat(job, sz); h_ = binarize(h_.im); save(h_, f'{OUT}/hats_lv5/{job}_{sz}.png'); save(up3(h_), f'{OUT}/hats_lv5/{job}_{sz}@3x.png')
            hs[sz] = dict(img=f'hats_lv5/{job}_{sz}@3x.png', size3x=[h_.width * S, h_.height * S], anchor3x=[anc[0] * S, anc[1] * S])
        J['hatsLv5'][job] = dict(zh=f'{JOB_ZH[job]}帽', unlock='職業 Lv5', sizes=hs, attach='帽 anchor（底中）對準寵物 headTop：x＝雙眼中點 x，y＝headTop＋5px（1x，S/M/L 一樣）；跟 clip 每幀 transform 一齊郁；寵物瞓覺唔戴（工作場景冇瞓覺）。',
                                 sizeRule='按 sizeClass 揀 S/M/L')
        b, pv, pct, pzh = P.PRODUCTS[job]
        for nm, prob in ((b, False), (pv, True)):
            ic = binarize(P.icon(nm).im); save(up3(ic), f'{OUT}/icons/{nm}@3x.png'); save(ic, f'{OUT}/icons/{nm}.png')
            e = dict(zh=P.PRODUCT_ZH[nm], img=f'icons/{nm}@3x.png', size3x=[48, 48], job=job, kind='probability' if prob else 'basic')
            if prob:
                pad = Image.new('RGBA', (24, 24), (0, 0, 0, 0)); pad.alpha_composite(ic, (4, 4)); g_ = glow3([pad], 5, 1.3)[0]; g_[..., 3] *= .8
                save(g_, f'{OUT}/icons/{nm}_glow@3x.png'); e['glow'] = dict(img=f'icons/{nm}_glow@3x.png', size3x=[72, 72], offset3x=[-12, -12], blend='lighter')
            J['icons'][nm] = e
        for sz in ('S', 'M', 'L'):
            for kind in ('loop', 'done'):
                frs = P.clip(job, sz, kind); key = f'{job}_{sz}_{kind}'
                rows = [[binarize(f['back'].im) for f in frs], [binarize(f['front'].im) for f in frs]]; sh1 = sheet(rows, 2); save(up3(sh1), f'{OUT}/clips/{key}@3x.png')
                ent = dict(zh=f'{JOB_ZH[job]}・{CLIP_ZH[(job, kind)]}（{sz}）', sheet=f'clips/{key}@3x.png', frames=len(frs), rows=['back（寵物後）', 'front（寵物前）'],
                           frameSize3x=[P.CW * S, P.CH * S], pivot3x=[P.PX * S, P.PY * S], ms=CLIP_MS[kind], loop=kind == 'loop',
                           petTransform=[f['tr'] for f in frs], transformNote='逐幀套落寵物 sprite：以腳底 pivot 為中心 scale(sx,sy)→rotate(rot°)→translate(dx,dy)（1x px，@3x ×3）；nearest，唔逐形態畫')
                gl = [f['glow'] for f in frs]
                if any(np.asarray(g_.im)[..., 3].any() for g_ in gl):
                    save(sheetf(glow3(gl, 5, 1.5)), f'{OUT}/clips/{key}_glow@3x.png'); ent['glow'] = dict(sheet=f'clips/{key}_glow@3x.png', blend='lighter', multiplyBy='petGlow（寵物身邊光點）' if not (job == 'tower' and kind == 'done') else '唔乘（小燈屬場景燈）')
                J['clips'][key] = ent
    pt = P.particles(); fr = {}; rows = []
    for r, (nm, lst) in enumerate(pt.items()):
        rows.append([binarize(f.im) for f in lst])
        for i in range(len(lst)): fr[f'{nm}_{i + 1:02d}'] = dict(x=i * 24, y=r * 24, w=24, h=24)
    save(up3(sheet(rows, len(rows))), f'{OUT}/fx/particles_work@3x.png'); json.dump(dict(frames=fr, note='8×8 1x ×3；alpha 0/255'), open(f'{OUT}/fx/particles_work@3x.json', 'w'), ensure_ascii=False, indent=1)
    J['sizeClass'] = size_classes()
    return J


# ================================================================ 寵物＋clip 合成（預覽／mockup；示範 runtime 做法）
HAT_OFF = {'S': 5, 'M': 5, 'L': 5}
_SC = {}
def size_of(form):
    if not _SC:
        if os.path.exists(f'{OUT}/workscenes_v3.json'): sc = json.load(open(f'{OUT}/workscenes_v3.json'))['sizeClass']; _SC.update(sc.get('forms', sc))
        else: _SC.update(size_classes())
    return _SC[form]['size']
def pet_frame(form, tr, state='normal', hat_job=None, tint=None, rim=None):
    """回傳 @3x RGBA ndarray（clip 畫布 CW×CH ×3，腳底＝pivot3x）。"""
    import hd2d_v2_px as X
    im, inf = X.compose_pet(form, state); cv = Image.new('RGBA', (P.CW, P.CH), (0, 0, 0, 0))
    ox, oy = P.PX - int(round(inf['pivot'][0])), P.PY - int(round(inf['pivot'][1])); cv.alpha_composite(im, (ox, oy))
    if hat_job:
        sz = size_of(form); h_, anc = P.hat(hat_job, sz); hx_ = int(round(inf['eyes'][0] + ox - anc[0])); hy_ = int(round(inf['headTop'] + oy + HAT_OFF[sz] - anc[1]))
        cv.alpha_composite(binarize(h_.im), (hx_, hy_))
    c3 = up3(cv); px, py = P.PX * S, P.PY * S
    sx, sy, rot = tr.get('sx', 1), tr.get('sy', 1), math.radians(tr.get('rot', 0)); dx, dy = tr.get('dx', 0) * S, tr.get('dy', 0) * S
    ca, sa = math.cos(rot), math.sin(rot)
    # 逆映射：out → src
    a = ca / sx; b = sa / sx; d_ = -sa / sy; e = ca / sy
    c = px - (a * (px + dx) + b * (py + dy)); f = py - (d_ * (px + dx) + e * (py + dy))
    out = c3.transform(c3.size, Image.AFFINE, (a, b, c, d_, e, f), Image.NEAREST)
    arr = f01(out); arr[..., 3] = (arr[..., 3] > .5); arr[arr[..., 3] == 0] = 0
    if tint is not None: arr[..., :3] *= tint
    if rim is not None:
        m = arr[..., 3] > .5; pp = np.pad(m, 3); inner = m & ~(pp[:-6, 3:-3] & pp[6:, 3:-3] & pp[3:-3, :-6] & pp[3:-3, 6:])
        dv = np.array(rim['dir'], float); dv /= np.linalg.norm(dv); nx = pp[3:-3, :-6].astype(float) - pp[3:-3, 6:]; ny = pp[:-6, 3:-3].astype(float) - pp[6:, 3:-3]
        w = np.clip(nx * dv[0] + ny * dv[1], 0, 1) * inner * rim['intensity']; arr[..., :3] = arr[..., :3] * (1 - w[..., None]) + hxf(rim['color']) * w[..., None]
    return arr
def clip_layers(job, size, kind, f):
    sh_ = ld(f'{OUT}/clips/{job}_{size}_{kind}@3x.png'); w, h = P.CW * S, P.CH * S
    back = sh_[0:h, f * w:(f + 1) * w]; front = sh_[h:2 * h, f * w:(f + 1) * w]
    gp = f'{OUT}/clips/{job}_{size}_{kind}_glow@3x.png'; glow = ld(gp)[:, f * w:(f + 1) * w] if os.path.exists(gp) else None
    return back, front, glow


# ================================================================ ③ UI 部件＋mockup（疊 UI v3）
def ui_mods():
    import ui_hd2d_v3_lib as L, build_ui_hd2d_v3_mockups as M3
    return L, M3
def prop_frame(key, f, row=0):
    J = SPR['props'][key]; sh_ = ld(f'{OUT}/{J["sheet"]}'); w, h = J['frameSize3x']; sp = sh_[row * h:(row + 1) * h, f * w:(f + 1) * w]
    x0, y0 = L3(*J['pos']); x0 -= J['anchor3x'][0]; y0 -= J['anchor3x'][1]; gl = None
    if 'glow' in J: gl = ld(f'{OUT}/{J["glow"]["sheet"]}')[:, f * w:(f + 1) * w]
    return sp, int(x0), int(y0), gl
def deco_sp(job):
    J = SPR['decoLv3'][job]; sp = ld(f'{OUT}/{J["img"]}'); x0, y0 = L3(*J['pos']); return sp, int(x0 - J['anchor3x'][0]), int(y0 - J['anchor3x'][1])
SPR = {}
def scene_shot(key, form=None, clip=None, props=(), deco=False, hat=False, pet_glow=1.0, tod=None, seed=5):
    """clip＝(kind, frame)；props＝[(propkey, frame, row)]"""
    job = key.split('_')[0]; g = json.load(open(f'{OUT}/{key}/grade.json')); mids, skys, adds, backs, fronts = [], [], [], [], []
    for (pk, f, row) in props:
        sp, x0, y0, gl = prop_frame(pk, f, row)
        (skys if SPR['props'][pk]['layer'].startswith('sky') else mids).append((sp, x0, y0))
        if gl is not None: adds.append((gl, x0, y0, 1.0))
    if deco: mids.append(deco_sp(job))
    mids.sort(key=lambda t: t[2] + t[0].shape[0])
    pet = None
    if form:
        sz = size_of(form); kind, f = clip; J = SPR['clips'][f'{job}_{sz}_{kind}']; tr = J['petTransform'][f]
        tint = hxf(g['petTint']) * hxf(g['ambientTint'])
        arr = pet_frame(form, tr, hat_job=job if hat else None, tint=tint, rim=dict(g['rim'], intensity=g['rim']['intensity'] * pet_glow))
        back, front, glow = clip_layers(job, sz, kind, f); fx_, fy_ = L3(*SC.FOOT); x0, y0 = int(fx_ - P.PX * S), int(fy_ - P.PY * S)
        bw = np.argwhere(arr[..., 3] > 0); w_ = (bw[:, 1].max() - bw[:, 1].min()) if len(bw) else 60
        pet = dict(img=arr, x0=x0, y0=y0, foot=SC.FOOT, w=w_); backs.append((back, x0, y0)); fronts.append((front, x0, y0))
        if glow is not None: adds.append((glow, x0, y0, (1.0 if (job == 'tower' and kind == 'done') else pet_glow)))
    return compose3x(key, mids=mids, fronts=fronts, adds=adds, pet=pet, pet_glow=pet_glow, tod=tod, seed=seed, skys=skys, backs=backs)
def build_ui_parts():
    L, M3 = ui_mods(); A = L.A; C = L.C; out = {}
    def sv(im, nm, note): save(im, f'{OUT}/ui/{nm}@3x.png'); out[nm] = dict(img=f'ui/{nm}@3x.png', size=list(im.size), note=note)
    w, h = 380, 470; im = L.new(w + 80, h + 80); m = L.rr_mask(w, h, 28)
    gl = L.glow_im(int(w * .62), A(C['gold']), .55); L.compc(im, gl.resize((w + 80, h + 80), Image.LANCZOS), (w + 80) / 2, (h + 80) / 2)
    L.comp(im, L.P('panel', w, h), 40, 40); L.comp(im, L.P('title_rule', 260, 12), 40 + w / 2 - 130, 40 + 84)
    sv(im, 'product_card_bg', '完成彈窗底（煙燻磨砂＋金幼線＋金暈；字 runtime 畫）。彈出 1.5s：scale .6→1.08→1 (220ms easeOutBack)，停 1.0s，飛入「今日成品」欄 (280ms easeInCubic)')
    yy, xx = np.mgrid[0:300, 0:300].astype(float); ang = np.arctan2(yy - 150, xx - 150); d = np.hypot(xx - 150, yy - 150) / 150
    a = (np.clip(np.cos(ang * 12) * .5 + .5, 0, 1) ** 3 * np.clip(1 - d, 0, 1) ** 1.2 * .55 + np.clip(1 - d * 1.6, 0, 1) ** 2 * .6)
    rb = np.dstack([np.ones((300, 300)) * C['goldhi'][0] / 255, np.ones((300, 300)) * C['goldhi'][1] / 255, np.ones((300, 300)) * C['goldhi'][2] / 255, np.clip(a, 0, 1)]); save(rb, f'{OUT}/ui/product_burst@3x.png')
    out['product_burst'] = dict(img='ui/product_burst@3x.png', size=[300, 300], note='產品 icon 後面金光芒（lighter，轉 12°/s）')
    sv(L.P('panel_inset', 76, 76), 'today_slot', '「今日成品」格（空）'); s2 = L.P('panel_inset_sel', 76, 76) if 'panel_inset_sel' in L.PARTS else L.P('panel_inset', 76, 76); sv(s2, 'today_slot_new', '「今日成品」格（啱啱入，閃 600ms）')
    sv(L.P('pill_navy', 236, 56), 'dayoff_tag_bg', '「今日放假」牌底（字 runtime：h2 goldhi）')
    r = L.new(120, 120); ImageDraw_ = __import__('PIL.ImageDraw', fromlist=['Draw']); dd = ImageDraw_.Draw(r); dd.ellipse([10, 10, 110, 110], outline=A(C['goldhi'], .9), width=4); r = r.filter(ImageFilter.GaussianBlur(1.2))
    sv(r, 'tap_ripple', '撳道具時嘅金圈（scale .4→1.2，alpha 1→0，350ms）')
    return out
def mock_ui(bd, key, scene_title, lv, shift, products, glow_new=False, hint=None, dayoff=False):
    L, M3 = ui_mods(); C = L.C; A = L.A; text = L.text
    bd.alpha_composite(L.vgrad(L.W, 140, (10, 14, 32, 210), (10, 14, 32, 0)))
    L.backdrop(bd, 18, 30, 56, 56, L.circ_mask(56)); L.compc(bd, L.P('back_btn'), 46, 58); L.icon(bd, 'back', 46, 58); M3.reg('back', 18, 30, 56, 56)
    text(bd, scene_title, 92, 58, 'title', C['cream'], 'lm', sh=(0, 0, 0)); tx = 92 + L.tw(scene_title, 'title') + 14
    w = int(L.tw(lv, 'label') + 28); M3.panel(bd, 'pill_navy', tx, 42, w, 32, shadow=False); text(bd, lv, tx + w / 2, 58, 'label', C['goldhi'], 'mm'); M3.reg('jobLv', tx, 42, w, 32, hit=False)
    sw = int(L.tw(shift, 'label') + 60); x = L.W - 18 - sw; M3.panel(bd, 'chip', x, 39, sw, 38, shadow=False); L.icon(bd, 'sleep' if '夜' in shift else 'light', x + 22, 58, glow=True)
    text(bd, shift, x + 42, 58, 'label', C['cream'], 'lm'); M3.reg('shift', x, 39, sw, 38, hit=False)
    if hint:
        hx_, hy_, ht = hint; w = int(L.tw(ht, 'caption') + 40); M3.panel(bd, 'label_pill', hx_ - w / 2, hy_, w, 34, shadow=False); text(bd, ht, hx_, hy_ + 17, 'caption', C['cream'], 'mm')
    y0 = 1044; bd.alpha_composite(L.vgrad(L.W, 222, (10, 14, 32, 0), (10, 14, 32, 235)), (0, y0))
    M3.panel(bd, 'panel', 18, y0 + 14, 549, 190); text(bd, '今日成品', 42, y0 + 44, 'h2', C['goldhi'], 'lm'); text(bd, f'{len(products)} 件', 545, y0 + 44, 'label', C['mute'], 'rm')
    for i in range(6):
        x = 42 + i * 86; y = y0 + 70; nm = products[i] if i < len(products) else None
        new_ = glow_new and i == len(products) - 1; L.comp(bd, Image.open(f'{OUT}/ui/{"today_slot_new" if new_ else "today_slot"}@3x.png').convert('RGBA'), x, y)
        if nm:
            e = SPR['icons'][nm]
            if 'glow' in e: L.compc(bd, Image.open(f'{OUT}/{e["glow"]["img"]}').convert('RGBA'), x + 38, y + 38)
            L.compc(bd, Image.open(f'{OUT}/{e["img"]}').convert('RGBA'), x + 38, y + 38); M3.reg(f'product:{i}', x, y, 76, 76, hit=False)
    if dayoff: text(bd, '今日冇成品', 545 - 0, y0 + 120, 'caption', C['mute'], 'rm') if False else None
    bar_y = y0 + 162; text(bd, '工作中' if not dayoff else '放假中', 42, bar_y + 9, 'label', C['cream'], 'lm')
    L.comp(bd, L.P('bar_track_h8', 380, 8), 150, bar_y + 5)
    if not dayoff: L.comp(bd, L.P('bar_fill_gold_h8', 250, 8), 150, bar_y + 5)
    text(bd, '出糧' if not dayoff else '—', 545, bar_y + 9, 'label', C['goldhi'], 'rm')
    M3.home_indicator(bd)
def to_rgba(im): return im.convert('RGBA')
def build_mockups():
    L, M3 = ui_mods(); C = L.C; A = L.A; text = L.text; shots = {}
    L.TEXTLOG.clear(); M3.LAY.clear(); M3.HITS.clear()
    def shot(name, bd, note):
        save(bd.convert('RGB'), f'{OUT}/mockups/{name}.png'); shots[name] = dict(img=f'mockups/{name}.png', note=note)
    def hitprops(job):
        for pk, e in SPR['props'].items():
            if pk.startswith(job):
                x0, y0, x1, y1 = e['hit']; M3.reg(f'prop:{pk}', x0 * S, y0 * S, (x1 - x0) * S, (y1 - y0) * S)
    # 1 郵局（Lv1，日更，分信 loop；信箱飛信中）
    L.SCREEN[0] = 'ws_post'; bd = to_rgba(scene_shot('post', 'S4C', ('loop', 2), props=[('post_mailbox', 3, 0), ('post_stamp', 0, 1)]))
    hitprops('post'); mock_ui(bd, 'post', '郵局', '職業 Lv1', '日更 10:24', ['letter', 'letter'], hint=(480, 700, '撳信箱寄信'))
    shot('ws_post', bd, '郵局 Lv1：M 體型（S4C）分信 loop 第 3 幀；信箱撳咗（第 4 幀）；印章藍色（row 1）')
    # 2 花園（Lv3 擺設；S 體型；花開＋閃）
    L.SCREEN[0] = 'ws_garden'; bd = to_rgba(scene_shot('garden', 'S2', ('loop', 4), props=[('garden_flower', 3, 0), ('garden_bucket', 0, 0)], deco=True))
    hitprops('garden'); mock_ui(bd, 'garden', '花園', '職業 Lv3', '日更 14:05', ['flowerpot', 'flowerpot', 'decoration'])
    shot('ws_garden', bd, '花園 Lv3：右下雀仔浴盆；S 體型（S2）淋水；朵花撳咗即開＋閃')
    # 3 瞭望台日
    L.SCREEN[0] = 'ws_tower_day'; bd = to_rgba(scene_shot('tower_day', 'evo_still_tide', ('loop', 2), props=[('tower_star', 0, 0), ('tower_lamp', 0, 0)]))
    hitprops('tower'); mock_ui(bd, 'tower', '瞭望台', '職業 Lv2', '日更 16:30', ['starmap_sticker'], hint=(396, 300, '撳星睇流星'))
    shot('ws_tower_day', bd, '瞭望台日版：L 體型（evo_still_tide）望遠鏡掃天；燈熄')
    # 4 瞭望台夜（夜更；Lv3＋Lv5 帽；燈著；流星）
    L.SCREEN[0] = 'ws_tower_night'; bd = to_rgba(scene_shot('tower_night', 'evo_still_tide', ('loop', 5), props=[('tower_star', 3, 0), ('tower_lamp', 3, 0)], deco=True, hat=True))
    hitprops('tower'); mock_ui(bd, 'tower', '瞭望台', '職業 Lv5', '夜更 23:40', ['starmap_sticker', 'starmap_sticker', 'starmap_rare', 'starmap_sticker'])
    shot('ws_tower_night', bd, '瞭望台夜版（夜更 21–05）：Lv3 渾天儀＋Lv5 星帽；燈著（場景燈）；流星劃過；夜更上限 8 不變')
    # 5 廚房（Lv5 帽＋Lv3）
    L.SCREEN[0] = 'ws_kitchen'; bd = to_rgba(scene_shot('kitchen', 'S4C', ('loop', 1), props=[('kitchen_pot', 3, 0), ('kitchen_spice', 2, 0)], deco=True, hat=True))
    hitprops('kitchen'); mock_ui(bd, 'kitchen', '廚房', '職業 Lv5', '日更 12:10', ['dish', 'dish', 'meal_shared'])
    shot('ws_kitchen', bd, '廚房 Lv5：廚師帽（M）＋Lv3 麵包籃；攪拌 loop；煲冒煙、香料灑粉')
    # 6 完成彈窗（郵局夜更出糧，委託信）
    L.SCREEN[0] = 'ws_done_popup'; base = scene_shot('post', 'S4C', ('done', 2), props=[('post_mailbox', 0, 0), ('post_stamp', 2, 0)], tod='night')
    bd = to_rgba(base); mock_ui(bd, 'post', '郵局', '職業 Lv3', '夜更 05:00', ['letter', 'letter', 'letter', 'letter_commission'], glow_new=True)
    bd.alpha_composite(L.vgrad(L.W, L.H, (6, 8, 20, 120), (6, 8, 20, 150)))
    card = Image.open(f'{OUT}/ui/product_card_bg@3x.png').convert('RGBA'); cx, cy = L.W // 2, 560; L.compc(bd, card, cx, cy); M3.reg('productCard', cx - 190, cy - 235, 380, 470, hit=False)
    text(bd, '今日成品！', cx, cy - 172, 'title', C['goldhi'], 'mm', sh=(0, 0, 0))
    L.compc(bd, Image.open(f'{OUT}/ui/product_burst@3x.png').convert('RGBA'), cx, cy - 20)
    e = SPR['icons']['letter_commission']; ic = Image.open(f'{OUT}/{e["img"]}').convert('RGBA').resize((144, 144), Image.NEAREST); gl = Image.open(f'{OUT}/{e["glow"]["img"]}').convert('RGBA').resize((216, 216), Image.LANCZOS)
    L.compc(bd, gl, cx, cy - 20); L.compc(bd, ic, cx, cy - 20)
    text(bd, '委託信', cx, cy + 92, 'h2', C['cream'], 'mm'); text(bd, '一封信變咗委託信！', cx, cy + 130, 'body', C['mute'], 'mm')
    w = 220; M3.panel(bd, 'pill_navy', cx - w / 2, cy + 160, w, 40, shadow=False); text(bd, '入咗「今日成品」', cx, cy + 180, 'label', C['goldhi'], 'mm')
    shot('ws_done_popup', bd, '出糧（夜更 05:00）：成品卡彈出 1.5s（5b 機率結果：委託信 25%）→ 飛入今日成品欄；郵局轉夜色（tod night）；寵物蓋印 done 第 3 幀')
    # 7 今日放假（寵物遠足）
    L.SCREEN[0] = 'ws_dayoff'; bd = to_rgba(scene_shot('garden', None, props=[('garden_flower', 0, 0), ('garden_bucket', 0, 0)], deco=True))
    mock_ui(bd, 'garden', '花園', '職業 Lv3', '日更 11:00', [], dayoff=True)
    M3.panel(bd, 'pill_navy', L.W / 2 - 130, 540, 260, 64); text(bd, '今日放假', L.W / 2, 572, 'h2', C['goldhi'], 'mm'); M3.reg('dayoffTag', L.W / 2 - 130, 540, 260, 64, hit=False)
    w = int(L.tw('團絨去咗遠足', 'caption') + 40); M3.panel(bd, 'label_pill', L.W / 2 - w / 2, 616, w, 34, shadow=False); text(bd, '團絨去咗遠足', L.W / 2, 633, 'caption', C['cream'], 'mm')
    shot('ws_dayoff', bd, '寵物唔喺度（遠足／休息）：場景淨係擺設＋「今日放假」；道具照撳得（純視覺）')
    # 8 花園夜色＋攰（sleepy → petGlow .6）
    L.SCREEN[0] = 'ws_garden_night'; bd = to_rgba(scene_shot('garden', 'S2', ('done', 3), props=[('garden_flower', 5, 0), ('garden_bucket', 0, 0)], deco=True, pet_glow=.6, tod='night'))
    mock_ui(bd, 'garden', '花園', '職業 Lv3', '夜更 22:15', ['flowerpot', 'flowerpot'])
    shot('ws_garden_night', bd, '花園夜色（tod night：場景轉色，花園燈／月光照常）；寵物 sleepy → petGlow .6（寵物光圈／光點 ×.6；場景燈唔郁）')
    json.dump(L.TEXTLOG, open(f'{OUT}/mockups/texts.json', 'w'), ensure_ascii=False, indent=0)
    return shots, dict(M3.LAY), dict(M3.HITS)
def petglow_test():
    """petGlow 規則測試：同一幀 petGlow 1 vs 0 → 只寵物光（光圈／rim／身邊光點）變；場景燈位（窗／燈／爐火）唔變。"""
    a = np.asarray(scene_shot('kitchen', 'S4C', ('done', 2), pet_glow=1.0, seed=9)).astype(float); b = np.asarray(scene_shot('kitchen', 'S4C', ('done', 2), pet_glow=0.0, seed=9)).astype(float)
    diff = np.abs(a - b).sum(-1); ys, xs = np.nonzero(diff > 3); fx_, fy_ = SC.FOOT
    win = (MX * 0 + 18) * S, 98 * S, 74 * S, 144 * S; fire = 140 * S, 232 * S, 172 * S, 249 * S
    def region(r): return float(diff[r[1]:r[3], r[0]:r[2]].max())
    return dict(changedPx=int((diff > 3).sum()), changedBBox=[int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())] if len(xs) else None,
                windowMaxDiff=region(win), fireMaxDiff=region(fire), petFoot3x=[fx_ * S, fy_ * S])

def write_entry(shots, lay, hits, ui, pgt):
    sc = {}
    for k in SCENE_KEYS:
        g = json.load(open(f'{OUT}/{k}/grade.json'))
        sc[k] = dict(zh=g['name'], job=g['job'], dir=k, layers1x={n: f'{k}/{n}.png' for n in ('sky', 'far', 'mid', 'fore', 'lightmap', 'light_add', 'emissive', 'emissive_blur', 'vignette', 'lut')},
                     layers3x={n: f'{k}/x3/{n}@3x.png' for n in ('sky', 'far', 'haze_far', 'mid', 'mist', 'fore', 'lightmap', 'light_add', 'emissive', 'bloom', 'vignette')},
                     grade=f'{k}/grade.json', palette=f'{k}/palette.json', props=[p for p in SPR['props'] if p.startswith(g['job'])], decoLv3=g['job'])
    J = dict(name='微光小圃・工作場景 V3-A（第 8 批）', version='workscenes_v3', spec='V3-A：金光海軍藍磨砂＋1.5px 金幼線；@3x 烘焙光影＋粒子；HD-2D；sprite alpha 0/255，光影層真 alpha；字 Noto CJK TC ≥18px@3x，對比 ≥4.5；procedural Pillow/numpy（冇 AI 圖）',
        gdd=dict(doc='docs-gdd/family-work-scenes-v1.md §2.1', mapping={'5 張背景（瞭望台日／夜）': 'scenes', '8 個可撳道具動畫（每場景 2）': 'props', 'Lv3 多 1 件擺設': 'decoLv3', 'Lv5 寵物戴職業帽': 'hatsLv5', '24 個工作 clip（4 職業×S/M/L×loop/done）': 'clips', '成品 icon 8 個（4 基本＋4 機率版）48px': 'icons', '完成彈出 1.5s／今日成品欄': 'ui.product_card_bg＋mockups.ws_done_popup', '寵物唔喺度→今日放假': 'ui.dayoff_tag_bg＋mockups.ws_dayoff', '夜更 21–05': 'tower_night＋tod night'}),
        numbersUnchanged='純美術：薪金、機率（郵局委託 25%、花園裝飾 15%、…）、夜更上限 8、心情／親密全部照 5b 原數，撳道具唔影響任何數值。',
        canvas=dict(art1x=[195, 422], layer1x=[LW, LH], margin1x=[MX, MY], layer3x=[W3, H3], screen3x=[SW3, SH3], crop3x=[MX * S, MY * S], map='L3(x,y)=((x+14)*3,(y+12)*3)', parallax='layer1x 四邊留 14／12px 俾 parallax／鏡頭 sway（同 hd2d_v3 格式）', foot1x=list(SC.FOOT)),
        bands3x=dict(top=[0, 126], bottom=[1044, 1266]),
        stack=['sky', 'skyProps（瞭望台星）', 'far', 'haze_far', 'mid＋props／decoLv3（y-sort）', 'mist', 'pet shadow', 'petLight（×petGlow）', 'clip back', 'pet（＋Lv5 帽）', 'clip front', 'fore', '×tod.mul（非瞭望台）', '×lightmap', '+light_add×tod.add', 'emissive／bloom×tod.emissive', 'prop glow（場景燈）＋clip glow（×petGlow）', 'particles', 'fog', 'crop', 'vignette', 'UI v3'],
        scenes=sc, props=SPR['props'], decoLv3=SPR['decoLv3'], hatsLv5=SPR['hatsLv5'], icons=SPR['icons'], clips=SPR['clips'],
        sizeClass=dict(rule='自定（GDD 冇講）：compose_pet bbox max(w,h)：S ≤32、M ≤40、L >40（1x px）', forms=SPR['sizeClass'], counts={z: sum(1 for v in SPR['sizeClass'].values() if v['size'] == z) for z in 'SML'}),
        fx=dict(work='fx/particles_work@3x.json', reuse=['scenes/hd2d_v3/fx/particles_v3@3x.json', 'scenes/hd2d_v3/fx/fx_glow_v3@3x.json']),
        petGlow=dict(ref='ui/kit_hd2d_v3/layout_hd2d_v3.json#petGlow', values=dict(awake=1, sleepy=.6, sleep=0, sleepClip=0, dreamEnter=0, dreaming=0), fadeOut='600ms easeInQuad', fadeIn='400ms easeOutQuad＋150ms pulse 1→1.15→1',
                     appliesTo=['petLight（grade.json）', 'clips *_glow（除咗 tower_*_done 盞燈＝場景燈）', '寵物 rim'], notAffected=['場景 emissive／bloom', 'props *_glow（道具燈／星）', 'lightmap／light_add', '環境粒子'], test=pgt),
        ui=ui, mockups=shots, layout=lay, hits=hits, texts='mockups/texts.json',
        tools=['tools/ws3_px.py', 'tools/ws3_scenes.py', 'tools/ws3_sprites.py', 'tools/build_workscenes_v3.py', 'tools/preview_workscenes_v3.py', 'tools/validate_workscenes_v3.py'])
    json.dump(J, open(f'{OUT}/workscenes_v3.json', 'w'), ensure_ascii=False, indent=1)
    if os.path.exists(f'{OUT}/_sprites_tmp.json'): os.remove(f'{OUT}/_sprites_tmp.json')

if __name__ == '__main__' and 'all' in sys.argv[1:]:
    for k in SCENE_KEYS: bake_scene(k)
    SPR.update(build_sprites()); ui = build_ui_parts(); sh_, lay, hits = build_mockups(); write_entry(sh_, lay, hits, ui, petglow_test()); print('all ok', len(sh_))
if __name__ == '__main__' and 'scenes' in sys.argv[1:]:
    for k in SCENE_KEYS: bake_scene(k)
if __name__ == '__main__' and 'sprites' in sys.argv[1:]:
    J = build_sprites(); json.dump(J, open(f'{OUT}/_sprites_tmp.json', 'w'), ensure_ascii=False, indent=1); print('sprites ok', {k: len(v) for k, v in J.items()})
if __name__ == '__main__' and 'mock' in sys.argv[1:]:
    SPR.update(json.load(open(f'{OUT}/_sprites_tmp.json'))); build_ui_parts(); sh_, lay, hits = build_mockups(); print('mock', list(sh_))
