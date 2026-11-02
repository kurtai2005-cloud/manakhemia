#!/usr/bin/env python3
"""《微光小圃》花園 H1–H4 → V3-A 光影（第 2 批）— 遊美 2026-11-02
以 scenes/hd2d（H1–H4 HD-2D 層，art/glimmer-hd2d-live 來源）做底：
  ① 1x 像素層加仔細場景細節（新材質 11 個；alpha 0/255；色盤鎖定）
  ② 出 223×446 相容層（同名、同 pivot、同疊法）＋ @3x 669×1338 烘焙層
  ③ @3x 烘焙：DoF、lightmap 斑駁、體積光、bloom、遠景霧、地面薄霧、暗角、split-tone LUT
  ④ 即時層（唔烘焙）：燈泡串星芒、螢火／浮塵／光斑粒子、emissive 閃爍、寵物光池（× petGlow）
純 Pillow／numpy 程序生成，冇 AI 圖。
用法：python3 art-pet/tools/build_garden_hd2d_v3.py [H1 H2 H3 H4 fx preview]（預設全部）"""
import os, sys, json, math, copy
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_hd2d_scenes as B
ART = os.path.abspath(f'{HERE}/..'); OUT = f'{ART}/scenes/hd2d_v3'; SRC = f'{ART}/scenes/hd2d'
S = 3; LW, LH, AW, AH, MX, MY = B.LW, B.LH, B.AW, B.AH, B.MX, B.MY
W3, H3 = LW * S, LH * S; SW3, SH3 = AW * S, AH * S
hx, mix, gblur, blur_rgba = B.hx, B.mix, B.gblur, B.blur_rgba
def to8(a): return (np.clip(a, 0, 1) * 255 + .5).astype(np.uint8)
def save(a, p, mode=None):
    os.makedirs(os.path.dirname(p), exist_ok=True); a = to8(a); Image.fromarray(a, mode or ('RGBA' if a.shape[-1] == 4 else 'RGB')).save(p, optimize=True)
def up3(a): return np.repeat(np.repeat(a, S, 0), S, 1)
def smooth3(a):   # 光照類：雙三次放大（光係平滑嘅）
    ch = [np.asarray(Image.fromarray(to8(a[..., i])).resize((W3, H3), Image.BICUBIC)).astype(float) / 255 for i in range(a.shape[-1])]
    return np.stack(ch, -1)

# ================================================================ ① 新材質（加喺 64 個舊 index 之後）
NEW_MATS = [('FLOWER_B', 1, '#8CB4F0'), ('FLOWER_W', 1, '#F8F4EC'), ('BULB', 1, '#E8DCC0'), ('JAR', 2, '#C8E4DC'), ('IVY', 2, '#5E9A4C'),
            ('BIRD', 1, '#4A4458'), ('BERRY', 1, '#D8505C'), ('CLOVER', 2, '#7AB85C')]
if 'BULB' not in B.IDX:
    k = B.NIDX + 1
    for n, lv, base in NEW_MATS: B.MATS.append((n, lv, base)); B.IDX[n] = list(range(k, k + lv)); k += lv
    B.NIDX = k - 1
NIDX = B.NIDX
VAR = copy.deepcopy(B.VAR)
PO = {'H1': dict(BULB='#EADFC4', JAR=['#B8D4CC', '#EEF8F2'], BIRD='#5A5068'),
      'H3': dict(BULB='#E8E4D4', JAR=['#B4D8D4', '#F0FCF8'], BIRD='#4E5A6C'),
      'H2': dict(BULB='#FFD890', JAR=['#E8B878', '#FFE6A0'], BIRD='#3A2A48'),
      'H4': dict(BULB='#FFF0C0', JAR=['#9CE068', '#F0FFC0'], BIRD='#202440', FLOWER_W='#C8CCE8', FLOWER_B='#7084C8')}
EMI = {'H1': {}, 'H3': {}, 'H2': {'BULB': .9, 'JAR': .55}, 'H4': {'BULB': 1.0, 'JAR': 1.0}}
for k_, v in VAR.items(): v['pal_over'].update(PO[k_]); v['emissive'].update(EMI[k_])
B.VAR.update(VAR)   # variant_palette／lighting 用 B.VAR
# v3 調色（比 v2 更飽滿、對比更高、加 split-tone）
V3G = {'H1': dict(saturation=1.12, contrast=1.08, bloom=dict(threshold=.74, intensity=.6), split=dict(shadow='#5a6ab0', highlight='#ffd49a', amount=.10), vignette=.26),
       'H3': dict(saturation=1.02, contrast=1.10, bloom=dict(threshold=.86, intensity=.3), split=dict(shadow='#4a7ab0', highlight='#fff4dc', amount=.07), vignette=.14),
       'H2': dict(saturation=1.18, contrast=1.13, bloom=dict(threshold=.62, intensity=.95), split=dict(shadow='#4a3090', highlight='#ffb060', amount=.13), vignette=.52),
       'H4': dict(saturation=1.10, contrast=1.08, bloom=dict(threshold=.56, intensity=1.25), split=dict(shadow='#20307a', highlight='#ffd890', amount=.12), vignette=.44)}
def grade_v3(key):
    g = copy.deepcopy(VAR[key]['grade']); v = V3G[key]
    g.update(saturation=v['saturation'], contrast=v['contrast'], bloom=v['bloom'], vignette=v['vignette']); g['splitTone'] = v['split']; return g
def grade_fn3(rgb, g):
    c = B.grade_fn(rgb, g); st = g['splitTone']; l = (c @ np.array([.2126, .7152, .0722]))[..., None]
    sh, hi = hx(st['shadow']), hx(st['highlight']); a = st['amount']
    c = c + (sh - .5) * a * (1 - l) ** 2 + (hi - .5) * a * l ** 2
    return np.clip(c, 0, 1)
def make_lut3(g):
    lut = np.zeros((16, 256, 3))
    for b in range(16):
        for gy in range(16):
            for rx in range(16): lut[gy, b * 16 + rx] = (rx / 15, gy / 15, b / 15)
    return grade_fn3(lut, g)

# ================================================================ ② 1x 像素細節（art 座標）
BULBS = []
def bulb_pos():
    if BULBS: return BULBS
    (x0, y0), (x1, y1) = B.LAYOUT['lanternString']['from'], B.LAYOUT['lanternString']['to']; sag = B.LAYOUT['lanternString']['sag']
    lan = B.lantern_pos(); last = -99
    for t in np.linspace(0.02, .98, 400):
        x = x0 + (x1 - x0) * t; y = y0 + (y1 - y0) * t + sag * math.sin(math.pi * t)
        if x - last < 6.5 or any(abs(x - lx) < 5 for lx, _ in lan): continue
        BULBS.append((int(round(x)), int(round(y)) + 2)); last = x
    return BULBS
CLEAR = (30, 210, 165, 300)
def free(x, y, pad=0):
    x0, y0, x1, y1 = CLEAR; return not (x0 - pad <= x <= x1 + pad and y0 - pad <= y <= y1 + pad)
def build_index_v3(key):
    idx = B.build_index(B.feats_for(key)); sky, far, mid, fore = idx['sky'], idx['far'], idx['mid'], idx['fore']
    rng = np.random.default_rng(31); X, Y = mid.X, mid.Y
    def px(lay, mat, x, y, f=1.0): lay.rect(mat, x, y, x + 1, y + 1, f, 0)
    # --- 燈泡串：小燈泡（夜晚發光；星芒係即時層）
    for (bx, by) in bulb_pos():
        px(mid, 'METAL', bx, by - 1, .2); px(mid, 'BULB', bx, by); px(mid, 'BULB', bx, by + 1)
    # --- 籬笆長春藤 ＋ 灌木莓
    for i, x0 in enumerate(range(-12, 150, 14)):
        if i % 2: continue
        for j in range(5):
            yy = 236 + j * 5 + (i % 3); xx = x0 + (1 if j % 2 else 3)
            mid.rect('IVY', xx - 1, yy, xx + 1, yy + 2, .3 if j % 2 else .9, 0); px(mid, 'IVY', xx + (2 if j % 2 else -2), yy + 1, .6)
    for x0 in range(-8, 152, 15):
        for k_ in range(3):
            bx, by = x0 + int(rng.integers(-8, 8)), 255 + int(rng.integers(0, 6)); px(mid, 'BERRY', bx, by)
    # --- 小屋：牆身長春藤 ＋ 窗台花箱 ＋ 屋簷燈
    wx0, wy0, wx1, wy1 = B.LAYOUT['cottage']['wall']
    for j in range(0, 54):
        yy = 261 - j; xx = wx0 + 1 + int(2.2 * math.sin(j / 5))
        px(mid, 'IVY', xx, yy, .3 + .6 * ((j // 3) % 2))
        if j % 4 == 0: mid.rect('IVY', xx + 1, yy - 1, xx + 3, yy + 1, .9, 0)
    a, b, c, d = B.LAYOUT['cottage']['window']
    mid.rect('WOOD', a - 3, d + 2, c + 3, d + 6, .35, 0); mid.rect('WOOD', a - 3, d + 2, c + 3, d + 3, .9, 0)
    for i, xx in enumerate(range(a - 2, c + 3, 2)):
        mat = ('FLOWER_P', 'FLOWER_W', 'FLOWER_B', 'FLOWER_Y')[i % 4]; px(mid, 'IVY', xx, d + 1, .7); px(mid, mat, xx, d, 1)
        if i % 3 == 0: px(mid, 'IVY', xx, d + 7 + (i % 2), .4)
    # --- 大樹：鳥屋 ＋ 垂藤
    mid.rect('WOOD', 6, 186, 14, 196, .6, 0); mid.poly('ROOF', [(4, 187), (10, 181), (16, 187)], .4); px(mid, 'METAL', 9, 189, .05); px(mid, 'METAL', 10, 189, .05)
    mid.rect('WOOD', 9, 192, 11, 193, .95, 0)
    cx, cy = B.LAYOUT['tree']['canopy_center']
    for (vx, vl) in [(4, 26), (18, 34), (34, 22), (52, 18)]:
        for j in range(vl):
            xx = vx + int(1.5 * math.sin(j / 4 + vx)); yy = cy + 20 + j
            if np.isin(mid.m[yy + MY, xx + MX], B.IDX['LEAF']): continue
            px(mid, 'IVY', xx, yy, .2 + .7 * (j % 3 == 0))
            if j % 6 == 3: px(mid, 'FLOWER_W' if vx % 2 else 'FLOWER_P', xx + 1, yy)
    # --- 菜畦：多啲花色
    b0, b1, b2, b3 = B.LAYOUT['bed']
    for xx in range(b0 + 2, b2 - 1, 4):
        px(mid, ('FLOWER_B', 'FLOWER_W', 'BERRY')[(xx // 4) % 3], xx, b1 - 1 - (xx % 3))
    # --- 螢火瓶（花盆 S 旁）
    jx, jy = 132, 306
    mid.rect('JAR', jx - 3, jy - 8, jx + 3, jy, .2, 0); mid.rect('JAR', jx - 2, jy - 7, jx + 2, jy - 1, .95, .4)
    mid.rect('METAL', jx - 3, jy - 10, jx + 3, jy - 8, .6, 0); mid.rect('WOOD', jx - 1, jy - 11, jx + 1, jy - 10, .5, 0)
    # --- 三葉草叢 ＋ 白／藍小花（避開寵物舞台）
    for (cx_, cy_) in [(20, 296), (176, 300), (40, 352), (160, 344), (124, 372), (70, 380), (182, 368), (12, 318)]:
        for k_ in range(9):
            x, y = cx_ + int(rng.integers(-7, 8)), cy_ + int(rng.integers(-4, 5))
            if not free(x, y, 2): continue
            px(mid, 'CLOVER', x, y, .9); px(mid, 'CLOVER', x - 1, y + 1, .3); px(mid, 'CLOVER', x + 1, y + 1, .5)
        px(mid, 'FLOWER_W', cx_, cy_ - 2); px(mid, 'FLOWER_W', cx_ + 3, cy_ - 1)
    for i in range(40):
        x, y = int(rng.integers(4, 192)), int(rng.integers(304, 378))
        if not free(x, y, 6) or any(abs(x - sx) < rx + 3 and abs(y - sy) < ry + 3 for sx, sy, rx, ry in B.LAYOUT['stones']): continue
        mat = ('FLOWER_B', 'FLOWER_W', 'FLOWER_W', 'FLOWER_P')[i % 4]; px(mid, 'FGRASS', x, y + 1, .2); px(mid, mat, x, y)
        if i % 3 == 0: px(mid, mat, x + 1, y); px(mid, 'FLOWER_Y', x + 1, y - 1)
    # --- 草地：更多高光草葉 ＋ 細石
    gm = Y >= 266
    for (yy, xx) in zip(*np.where((rng.random(mid.m.shape) > .985) & gm)):
        ax, ay = xx - MX, yy - MY
        if not free(ax, ay, -6): pass
        mid.rect('GRASS', ax, ay - 2, ax + 1, ay, .98, 0); mid.rect('MOSS', ax + 1, ay - 1, ax + 2, ay, .9, 0)
    for i in range(26):
        x, y = int(rng.integers(0, 195)), int(rng.integers(310, 380))
        if free(x, y, 4): px(mid, 'STONE', x, y, .85); px(mid, 'STONE', x + 1, y, .3)
    for (sx, sy, rx, ry) in B.LAYOUT['stones']:   # 踏腳石苔
        for k_ in range(4): px(mid, 'MOSS', int(sx - rx + 1 + rng.integers(0, 2 * rx - 2)), int(sy + ry * .3), .7)
    # --- far：山邊小花、遠樹高光、遠屋煙囪
    far.rect('FAR_HOUSE', 142, 212, 145, 219, .3, 0)
    for i in range(60):
        x, y = int(rng.integers(-10, 205)), int(rng.integers(238, 252))
        if far.m[y + MY, x + MX] in B.IDX['HILL_NEAR']: px(far, ('FLOWER_P', 'FLOWER_Y', 'FLOWER_W')[i % 3], x, y)
    for (yy, xx) in zip(*np.where(np.isin(far.m, B.IDX['TREE_FAR']) & (rng.random(far.m.shape) > .9))): far.m[yy, xx] = B.IDX['TREE_FAR'][-1]
    # --- sky：雀仔（日／黃昏）、大星（夜）
    if key in ('H1', 'H3', 'H2'):
        for (bx, by) in [(118, 118), (126, 112), (131, 120)] if key != 'H2' else [(60, 196), (68, 190), (74, 199)]:
            px(sky, 'BIRD', bx - 1, by); px(sky, 'BIRD', bx + 1, by); px(sky, 'BIRD', bx, by + 1)
    if key == 'H4':
        for (sx, sy) in [(40, 30), (96, 22), (176, 40), (120, 64), (64, 92), (182, 110)]:
            px(sky, 'STAR', sx, sy); px(sky, 'STAR', sx - 1, sy, .6); px(sky, 'STAR', sx + 1, sy, .6); px(sky, 'STAR', sx, sy - 1, .6); px(sky, 'STAR', sx, sy + 1, .6)
    # --- fore：露珠（白點）、藍花、蕨
    for (yy, xx) in zip(*np.where(np.isin(fore.m, B.IDX['FGRASS']) & (rng.random(fore.m.shape) > .985))):
        if yy - MY < 420: fore.m[yy, xx] = B.IDX['FLOWER_W'][0]
    for (tx, ty) in [(6, 404), (22, 414)]:
        fore.line('FGRASS', [(tx + 2, 450), (tx, ty)], 1, .3)
        for (ox, oy) in [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]: px(fore, 'FLOWER_B' if (ox, oy) != (0, 0) else 'FLOWER_Y', tx + ox, ty + oy)
    return idx

# ================================================================ ③ 烘焙
def raw_layers(key, idx):
    pal = B.variant_palette(key); return {n: B.raw_rgba(idx[n].m, pal) for n in ('sky', 'far', 'mid', 'fore')}, pal
def emissive(key, idx, raws):
    em = np.zeros((LH, LW, 4)); fore_a = raws['fore'][..., 3] > 0
    for nm in ('sky', 'far', 'mid'):
        m = idx[nm].m
        for mat, s in VAR[key]['emissive'].items():
            mk = np.isin(m, B.IDX[mat]) & ~fore_a
            if nm != 'mid':
                for nm2 in ('far', 'mid')[('sky', 'far').index(nm):]: mk &= raws[nm2][..., 3] == 0
            em[mk, :3] = raws[nm][..., :3][mk] * s; em[mk, 3] = 1
    return em
def lighting_v3(key, idx):
    lm, add = B.lighting(key, idx); X, Y = B.Lay().X, B.Lay().Y
    def pool(x, y, rx, ry, col, a): return np.exp(-(((X - x) / rx) ** 2 + ((Y - y) / ry) ** 2))[..., None] * hx(col) * a
    if key in ('H2', 'H4'):
        k = 1 if key == 'H4' else .5
        for (bx, by) in bulb_pos(): add += pool(bx, by, 6, 6, '#ffc870', .14 * k)
        add += pool(132, 302, 14, 8, '#c8ff80' if key == 'H4' else '#ffd890', .3 * k)        # 螢火瓶光池
        lm = np.maximum(lm, mix(lm, hx('#fff0d8')[None, None], (np.exp(-(((X - 132) / 16) ** 2 + ((Y - 302) / 9) ** 2)) * .6 * k)[..., None]))
        a, b, c, d = B.LAYOUT['cottage']['window']; add += pool((a + c) / 2, d + 4, 12, 4, '#ffb860', .2 * k)
    return np.clip(lm, 0, 1), np.clip(add, 0, 1)
def bake1x(raws, g, lut):
    return {n: B.bake(raws[n], g, n, lut) for n in raws}
def lut_apply(rgba, lut): o = rgba.copy(); o[..., :3] = B.apply_lut(rgba[..., :3], lut); return o
def blur3(rgba, s): return blur_rgba(rgba, s)
def bake3x(raws, g, lut):
    out = {}
    for n in ('sky', 'far', 'mid', 'fore'):
        a = up3(lut_apply(raws[n], lut))
        if n == 'far': a = blur3(a, g['dof']['far'] * S * .85)
        if n == 'mid':
            sig = g['dof']['mid'] * S; smap = np.repeat(B.mid_dof_map(1.0), S) * sig
            a = B.blur_rgba_var(a, smap, [sig * .5, sig]) if sig > .9 else a
        if n == 'fore': a = blur3(a, g['dof']['fore'] * S)
        if n != 'sky': a[..., 3] = np.where(a[..., 3] < 1 / 255, 0, a[..., 3])
        out[n] = a
    return out
def rays(src, col, strength, spread, falloff, seed, k=(9, 17, 31, 53, 77), sharp=3):
    rnd = np.random.RandomState(seed); yy, xx = np.mgrid[0:H3, 0:W3].astype(float)
    ang = np.arctan2(yy - src[1], xx - src[0]); d = np.hypot(xx - src[0], yy - src[1]); n = np.zeros_like(ang)
    for kk in k: n += np.sin(ang * kk + rnd.rand() * 6.28) / kk ** .3
    n = ((n - n.min()) / (n.max() - n.min())) ** sharp
    win = np.clip((ang - spread[0]) / .18, 0, 1) * np.clip((spread[1] - ang) / .18, 0, 1)
    return (n * win * np.exp(-d / falloff) * strength)[..., None] * hx(col)
def L3(x, y): return ((x + MX) * S, (y + MY) * S)    # art → @3x 層座標
def volumetric(key):
    yy = np.mgrid[0:H3, 0:W3][0].astype(float) / S - MY      # art y
    air = np.clip((300 - yy) / 60, .25, 1)[..., None]           # 地面以下淡啲
    if key == 'H1':
        r = rays(L3(38, 112), '#ffd8a0', .28, (.15, 1.45), 900, 4) + rays(L3(38, 112), '#fff0d0', .1, (.35, 1.2), 1500, 8, sharp=5)
    elif key == 'H3':
        r = rays(L3(205, -20), '#eef8ff', .15, (1.85, 2.7), 900, 9, sharp=4) + rays(L3(205, -20), '#ffffff', .06, (1.95, 2.5), 1400, 13, sharp=6)
    elif key == 'H2':
        r = rays(L3(112, 226), '#ffb070', .38, (-2.95, -.2), 800, 5) + rays(L3(112, 226), '#ffe0a0', .2, (-2.6, -.55), 420, 7, sharp=5)
        air = np.clip((280 - yy) / 40, .4, 1)[..., None]
    else:
        lx, ly = B.LAYOUT['lampPost']['head']
        r = rays(L3(150, 76), '#a8b8ff', .12, (1.9, 2.6), 1100, 6) + rays(L3(lx, ly + 2), '#ffd890', .32, (1.05, 2.1), 260, 3, k=(23, 41, 67), sharp=2)
        a, b, c, d = B.LAYOUT['cottage']['window']; r += rays(L3((a + c) / 2, (b + d) / 2), '#ffc870', .2, (1.6, 2.4), 180, 11, sharp=2)
        air = 1.0
    return np.clip(r * air, 0, 1)
def dapple3(key, lm3):
    if key == 'H4': return lm3
    rnd = np.random.RandomState(17); n = rnd.rand(H3 // 6 + 1, W3 // 6 + 1)
    n = np.asarray(Image.fromarray(to8(n)).resize((W3 + 6, H3 + 6), Image.BICUBIC)).astype(float)[:H3, :W3] / 255
    n2 = np.asarray(Image.fromarray(to8(rnd.rand(H3 // 14 + 1, W3 // 14 + 1))).resize((W3 + 14, H3 + 14), Image.BICUBIC)).astype(float)[:H3, :W3] / 255
    spot = np.clip((n * .6 + n2 * .4 - .56) * 9, 0, 1)                        # 葉隙光斑
    base = hx(VAR[key]['lm']['base']); shade = np.clip(1 - (lm3 @ np.array([.3, .55, .15])) / max(base @ np.array([.3, .55, .15]), 1e-3), 0, 1)
    w = np.clip(shade * 3, 0, 1)[..., None] * {'H1': .7, 'H3': .5, 'H2': .35}[key]
    return np.clip(lm3 * (1 - w) + mix(lm3, base[None, None], .85) * w * spot[..., None] + lm3 * w * (1 - spot[..., None]), 0, 1)
def bloom3(em3, comp3, g):
    e = em3[..., :3] * em3[..., 3:]; l = comp3 @ np.array([.3, .55, .15]); t = g['bloom']['threshold']
    hi = comp3 * np.clip((l - t) / (1 - t + 1e-6), 0, 1)[..., None] * .55
    src = np.clip(e + hi, 0, 1); b = gblur(src, 4) * .5 + gblur(src, 12) * .35 + gblur(src, 30) * .3
    return np.clip(b, 0, 1)
def haze3(key, g):
    yy = np.mgrid[0:H3, 0:W3][0].astype(float) / S - MY; fc = hx(g['fog']['color'])
    far = np.exp(-((yy - 238) / 20) ** 2) * {'H1': .18, 'H3': .14, 'H2': .30, 'H4': .22}[key]
    mist = np.exp(-((yy - 300) / 16) ** 2) * {'H1': .16, 'H3': .06, 'H2': .1, 'H4': .14}[key]
    rnd = np.random.RandomState(23); n = np.asarray(Image.fromarray(to8(rnd.rand(12, 40))).resize((W3, H3), Image.BICUBIC)).astype(float) / 255
    mist = mist * (.6 + .8 * n)
    mc = mix(fc, hx('#ffffff'), .35) if key != 'H4' else hx('#7080c0')
    def rgba(c, a): o = np.zeros((H3, W3, 4)); o[..., :3] = c; o[..., 3] = np.clip(a, 0, 1); return o
    return rgba(fc, far), rgba(mc, mist)
def vignette3(key, g):
    yy, xx = np.mgrid[0:SH3, 0:SW3].astype(float); dd = ((xx / SW3 - .5) / .5) ** 2 + ((yy / SH3 - .47) / .5) ** 2
    a = np.clip((dd - .3) / .9, 0, 1) ** 1.6 * g['vignette'] * 1.7
    o = np.zeros((SH3, SW3, 4)); o[..., :3] = hx(VAR[key]['vig']); o[..., 3] = np.clip(a, 0, .92); return o

# ================================================================ ④ 即時層 sprite（全 H 共用）
def fx_sheets():
    d = f'{OUT}/fx'; os.makedirs(d, exist_ok=True); frames = {}
    def star(sz, rot, k, core):
        im = Image.new('RGBA', (sz, sz), (255, 255, 255, 0)); n = 4 * sz
        big = Image.new('L', (n, n), 0); dr = ImageDraw.Draw(big); c = n / 2
        for i in range(4):
            an = rot + i * math.pi / 2; L = c * (.98 if i % 2 == 0 else .72) * k
            p = [(c + math.cos(an) * L, c + math.sin(an) * L), (c + math.cos(an + 1.57) * n * .018, c + math.sin(an + 1.57) * n * .018),
                 (c - math.cos(an) * n * .02, c - math.sin(an) * n * .02), (c + math.cos(an - 1.57) * n * .018, c + math.sin(an - 1.57) * n * .018)]
            dr.polygon(p, fill=255)
        for i in range(4):
            an = rot + math.pi / 4 + i * math.pi / 2; L = c * .32 * k; dr.line([(c, c), (c + math.cos(an) * L, c + math.sin(an) * L)], fill=150, width=max(1, n // 80))
        sp = np.asarray(big.filter(ImageFilter.GaussianBlur(n / 120)).resize((sz, sz), Image.LANCZOS)).astype(float) / 255
        yy, xx = np.mgrid[0:sz, 0:sz]; r = np.hypot(xx - sz / 2 + .5, yy - sz / 2 + .5) / (sz / 2)
        glow = np.exp(-(r / .22) ** 2) * core + np.exp(-(r / .5) ** 2) * .25
        a = np.clip(sp * .9 + glow, 0, 1); o = np.zeros((sz, sz, 4)); o[..., :3] = 1; o[..., 3] = a
        return o
    for sz, nm in ((21, 's'), (39, 'm'), (63, 'l')):
        for f, (rot, k, core) in enumerate([(0, .7, .8), (.12, .9, .95), (.22, 1, 1), (.32, .85, .9), (.4, .6, .7), (.5, .45, .6)]):
            frames[f'flare_{nm}_{f + 1:02d}'] = star(sz, rot, k, core)
    def disc(sz, edge=.12, ring=.35):
        yy, xx = np.mgrid[0:sz, 0:sz]; r = np.hypot(xx - sz / 2 + .5, yy - sz / 2 + .5) / (sz / 2)
        a = np.clip((1 - r) / edge, 0, 1) * (.35 + ring * np.clip((r - .7) / .3, 0, 1)); o = np.zeros((sz, sz, 4)); o[..., :3] = 1; o[..., 3] = a; return o
    for sz in (24, 36, 54): frames[f'bokeh_{sz}'] = disc(sz)
    def soft(sz, p=2.0):
        yy, xx = np.mgrid[0:sz, 0:sz]; r = np.hypot(xx - sz / 2 + .5, yy - sz / 2 + .5) / (sz / 2)
        o = np.zeros((sz, sz, 4)); o[..., :3] = 1; o[..., 3] = np.clip(1 - r, 0, 1) ** p; return o
    for sz in (12, 24, 48): frames[f'glow_{sz}'] = soft(sz)
    yy, xx = np.mgrid[0:96, 0:240]; pp = np.zeros((96, 240, 4)); pp[..., :3] = 1
    pp[..., 3] = np.clip(1 - np.hypot((xx - 119.5) / 120, (yy - 47.5) / 48), 0, 1) ** 1.7; frames['pet_pool'] = pp
    glow_sheet = pack(frames, f'{d}/fx_glow_v3@3x', 'v3 光效 sprite（真 alpha，白色；引擎 tint＋lighter）。flare_* 6 幀星芒（燈泡串／燈籠／燈／窗）；bokeh_* 失焦光斑；glow_* 柔光；pet_pool 寵物光池（× petGlow）')
    # 像素核心（alpha 0/255）：舊 8×8 粒子 ×3 nearest ＋ 新 dust／pollen
    T = B.particle_frames(); px = {}
    for t, fr in T.items():
        for i, a in enumerate(fr): px[f'{t}_{i + 1:02d}'] = up3(a.astype(float) / 255)
    def dot(pts, col):
        a = np.zeros((8, 8, 4))
        for (x, y, c) in pts: a[y, x, :3] = hx(c); a[y, x, 3] = 1
        return up3(a)
    for i, s in enumerate([0, 1, 1, 2, 1, 0]):
        pts = [(3, 3, '#fffaf0')] + ([(4, 3, '#ffe8c0')] if s else []) + ([(3, 4, '#ffe8c0'), (2, 3, '#f8d8a8')] if s > 1 else [])
        px[f'dust_{i + 1:02d}'] = dot(pts, None)
    for i, s in enumerate([0, 1, 2, 1, 0, 1]):
        px[f'pollen_{i + 1:02d}'] = dot([(3 + (i % 2), 3, '#fff4a0'), (3 + (i % 2), 4, '#f0d060')] + ([(4 - (i % 2), 3, '#fffad0')] if s else []), None)
    pack(px, f'{d}/particles_v3@3x', 'v3 粒子像素核心（alpha 0/255；舊 8×8 ×3 nearest＋dust／pollen）；配 fx_glow 嘅 glow_* 做光暈')
    return frames, px
def pack(frames, base, note, pad=2):
    items = sorted(frames.items(), key=lambda kv: (-kv[1].shape[0], kv[0])); W_ = 512; x = y = rowh = 0; pos = {}
    for k, a in items:
        h, w = a.shape[:2]
        if x + w > W_: x, y, rowh = 0, y + rowh + pad, 0
        pos[k] = (x, y, w, h); x += w + pad; rowh = max(rowh, h)
    Ht = y + rowh; sheet = np.zeros((Ht, W_, 4))
    for k, a in items: x, y, w, h = pos[k]; sheet[y:y + h, x:x + w] = a
    save(sheet, base + '.png')
    json.dump(dict(image=os.path.basename(base) + '.png', scale=3, note=note, frames={k: dict(x=v[0], y=v[1], w=v[2], h=v[3]) for k, v in sorted(pos.items())}),
              open(base + '.json', 'w'), ensure_ascii=False, indent=1)
    return pos

# ================================================================ 每個 H
EMIT = {   # 即時粒子 emitter（art 座標；rate/s；life s）
 'H1': [dict(type='dust', glow='glow_12', tint='#fff2c8', rect=[0, 70, 195, 300], rate=1.2, life=[5, 8], vy=[-3, -1], sway=4, max=14, add=.55),
        dict(type='bokeh', sprite='bokeh_36', tint='#ffe0a8', rect=[0, 80, 195, 230], rate=.25, life=[6, 9], vy=[-1, 0], max=5, alpha=.18)],
 'H3': [dict(type='petal', tint='#ffe0ec', rect=[0, 40, 195, 300], rate=.6, life=[6, 9], vy=[8, 12], vx=[-4, -2], sway=6, max=8),
        dict(type='pollen', glow='glow_12', tint='#fff8d0', rect=[0, 220, 195, 340], rate=.6, life=[5, 7], vy=[-2, 0], sway=3, max=8, add=.35)],
 'H2': [dict(type='gold', glow='glow_12', tint='#ffd27a', rect=[0, 90, 195, 300], rate=1.0, life=[5, 8], vy=[-3, -1], sway=4, max=14, add=.7),
        dict(type='bokeh', sprite='bokeh_54', tint='#ffb070', rect=[20, 150, 195, 260], rate=.3, life=[6, 9], vy=[-1, 0], max=5, alpha=.22)],
 'H4': [dict(type='firefly', glow='glow_24', tint='#d8ff90', rect=[0, 180, 195, 380], rate=1.0, life=[6, 10], vx=[-4, 4], vy=[-3, 3], breathe=1.6, max=16, add=.9),
        dict(type='bokeh', sprite='bokeh_24', tint='#ffd890', rect=[0, 100, 195, 200], rate=.3, life=[6, 9], vy=[-1, 0], max=6, alpha=.2)]}
def flare_list(key):
    on = VAR[key]['emissive']; L = []
    if 'BULB' in on: L += [dict(pos=list(p), size='s', tint='#ffe6b0', fps=6, phase=round(i * .37 % 1, 2), intensity=on['BULB'] * .9) for i, p in enumerate(bulb_pos())]
    if 'LANTERN' in on: L += [dict(pos=list(p), size='m', tint='#ffb070', fps=5, phase=round(i * .23 % 1, 2), intensity=on['LANTERN'] * .8) for i, p in enumerate(B.lantern_pos())]
    if 'LAMP' in on: L.append(dict(pos=list(B.LAYOUT['lampPost']['head']), size='l', tint='#ffe2a0', fps=4, phase=0, intensity=on['LAMP']))
    if 'JAR' in on: L.append(dict(pos=[132, 302], size='m', tint='#d8ff90' if key == 'H4' else '#ffd890', fps=3, phase=.5, intensity=on['JAR'] * .7))
    if key == 'H2': L.append(dict(pos=list(VAR['H2']['feats']['sun'][:2]), size='l', tint='#fff0b0', fps=2, phase=0, intensity=.9))
    if key == 'H1': L.append(dict(pos=list(VAR['H1']['feats']['sun'][:2]), size='l', tint='#fff4d0', fps=2, phase=0, intensity=.6))
    return L
PETLIGHT = {'H1': .35, 'H3': .2, 'H2': .55, 'H4': .9}
def build_variant(key):
    d = f'{OUT}/{key}'; g = grade_v3(key); lut = make_lut3(g)
    idx = build_index_v3(key); raws, pal = raw_layers(key, idx)
    for n, r in raws.items(): save(r, f'{d}/raw/{n}.png')
    # 223×446 相容層（同名同疊法）
    L1 = bake1x(raws, g, lut)
    for n, a in L1.items(): save(a, f'{d}/{n}.png')
    lm, add = lighting_v3(key, idx); save(lm, f'{d}/lightmap.png'); save(add, f'{d}/light_add.png')
    em = emissive(key, idx, raws); emo = em.copy(); emo[..., 3] = (em[..., 3] > 0); save(emo, f'{d}/emissive.png')
    t = g['bloom']['threshold']; e = em[..., :3]; lum = e @ np.array([.3, .55, .15])
    br = e * np.clip((lum - t * .5) / (1 - t * .5 + 1e-6), 0, 1)[..., None] + e * .25; eb = np.clip((gblur(br, 3) * .5 + gblur(br, 9) * .5) * 1.6, 0, 1)
    save(eb, f'{d}/emissive_blur.png')
    yy, xx = np.mgrid[0:AH, 0:AW].astype(float); dd = ((xx / AW - .5) / .5) ** 2 + ((yy / AH - .48) / .5) ** 2
    vg = np.zeros((AH, AW, 4)); vg[..., :3] = hx(VAR[key]['vig']); vg[..., 3] = np.clip(np.clip((dd - .35) / .9, 0, 1) ** 1.5 * g['vignette'] * 1.6, 0, 1); save(vg, f'{d}/vignette.png')
    save(lut, f'{d}/lut.png')
    # @3x 烘焙
    L3_ = bake3x(raws, g, lut)
    for n, a in L3_.items(): save(a, f'{d}/x3/{n}@3x.png')
    lm3 = dapple3(key, smooth3(lm)); save(lm3, f'{d}/x3/lightmap@3x.png')
    vol = volumetric(key); add3 = np.clip(smooth3(add) + vol, 0, 1); save(add3, f'{d}/x3/light_add@3x.png')
    em3 = up3(em); em3o = em3.copy(); em3o[..., 3] = em3[..., 3] > 0; save(em3o, f'{d}/x3/emissive@3x.png')
    comp = L3_['sky'][..., :3]
    for n in ('far', 'mid'): comp = comp * (1 - L3_[n][..., 3:]) + L3_[n][..., :3] * L3_[n][..., 3:]
    comp = np.clip(comp * lm3 + add3, 0, 1); bl = bloom3(em3, comp, g); save(bl, f'{d}/x3/bloom@3x.png')
    hz, ms = haze3(key, g); save(hz, f'{d}/x3/haze_far@3x.png'); save(ms, f'{d}/x3/mist@3x.png')
    vg3 = vignette3(key, g); save(vg3, f'{d}/x3/vignette@3x.png')
    # grade.json（舊欄位全保留＋v3 block）
    gj = dict(variant=key, name=VAR[key]['name'], hours=VAR[key]['hours']); gj.update(g)
    gj['v3'] = dict(
        note='V3-A 花園：@3x 烘焙層喺 x3/（669×1338＝層 223×446 ×3；對齊 mid，同 mid 一齊位移 ×3）；vignette@3x 係螢幕 585×1266。即時層唔烘焙。',
        layerSize3x=[W3, H3], screenSize3x=[SW3, SH3], layerOffset3x=[MX * S, MY * S], pivot='同 v2：腳底 art (97,292)＝@3x 層 (333,912)；pivot (w/2, h−3)',
        stack=STACK, bloom3x=dict(intensity=g['bloom']['intensity']),
        flares=flare_list(key), emitters=EMIT[key],
        petLight=dict(sprite='fx/fx_glow_v3@3x.json#pet_pool', anchor='foot', offset3x=[0, 6], size3x=[240, 96], tint=g['bulbGlowTint'], intensity=PETLIGHT[key], blend='lighter',
                      multiplyBy='petGlow', rule='layout_hd2d_v3.json → petGlow：瞓覺／sleepClip／入夢前＝0；淡出 600ms easeInQuad、醒返淡入 400ms＋pulse。場景燈唔受影響。逐形態光暈／光點 anchor 喺第 3 批。'),
        petPop=dict(contactShadow=dict(alpha=.32, rx=.38, ry=.08), rim='用 sprites/tuanrong/rim（同 v2 FORMAT §5），rim.intensity ×1.15', focusBand='mid DoF 喺 art y 262–340 = 0 → 團絨永遠最清'),
        rawColors=len({pal[i] for i in np.unique(np.concatenate([idx[n].m.ravel() for n in idx])) if i}))
    json.dump(gj, open(f'{d}/grade.json', 'w'), ensure_ascii=False, indent=1)
    used = sorted({int(i) for n in idx for i in np.unique(idx[n].m) if i})
    json.dump(dict(variant=key, count=len(pal), usedIndex=len(used), usedColors=len({pal[i] for i in used}),
                   colors=[dict(index=i, material=next(n for n in B.IDX if i in B.IDX[n]), hex=pal[i]) for i in sorted(pal)]), open(f'{d}/palette.json', 'w'), ensure_ascii=False, indent=1)
    for n in idx: Image.fromarray(idx[n].m, 'L').save(f'{d}/raw/{n}_index.png')
    print(key, 'ok raw colors', len({pal[i] for i in used}))
STACK = [
 dict(layer='sky', file='x3/sky@3x.png', fallback1x='sky.png', blend='source-over', parallax=.15, baked=True),
 dict(layer='far', file='x3/far@3x.png', fallback1x='far.png', blend='source-over', parallax=.35, baked=True, note='已烘 DoF'),
 dict(layer='haze_far', file='x3/haze_far@3x.png', blend='source-over', parallax=.35, baked=True, note='地平線高度霧'),
 dict(layer='mid', file='x3/mid@3x.png', fallback1x='mid.png', blend='source-over', parallax=1.0, baked=True, note='移軸 DoF：art y 262–340 清'),
 dict(layer='mist', file='x3/mist@3x.png', blend='source-over', parallax=1.0, baked=True, note='地面薄霧；可橫向慢飄 2px@3x/s', drift3x=2),
 dict(layer='pet', realtime=True, note='團絨＋細佬：sprite × petTint × ambientTint ＋ rim；contact shadow；petLight pool（× petGlow）'),
 dict(layer='fore', file='x3/fore@3x.png', fallback1x='fore.png', blend='source-over', parallax=1.6, baked=True),
 dict(layer='lightmap', file='x3/lightmap@3x.png', fallback1x='lightmap.png', blend='multiply', parallax=1.0, baked=True, note='含葉隙光斑'),
 dict(layer='light_add', file='x3/light_add@3x.png', fallback1x='light_add.png', blend='lighter', parallax=1.0, baked=True, note='含體積光（god rays）'),
 dict(layer='bloom', file='x3/bloom@3x.png', fallback1x='emissive_blur.png', blend='lighter', parallax=1.0, baked=True, alpha='grade.bloom.intensity'),
 dict(layer='emissive_flicker', file='x3/emissive@3x.png', blend='lighter', parallax=1.0, realtime=True, note='mask：燈泡／燈籠／窗閃爍時 globalAlpha 0–0.25 加多次'),
 dict(layer='flares', realtime=True, blend='lighter', sprite='fx/fx_glow_v3@3x.json#flare_{s,m,l}_01..06', note='grade.v3.flares：pos（art）、size、tint、fps、phase'),
 dict(layer='particles', realtime=True, sprite='fx/particles_v3@3x.json ＋ fx/fx_glow_v3@3x.json', note='grade.v3.emitters；核心 source-over，glow lighter'),
 dict(layer='fog', realtime=True, blend='source-over', note='fillRect grade.fog（同 v2）'),
 dict(layer='vignette', file='x3/vignette@3x.png', fallback1x='vignette.png', blend='source-over', screen=True, baked=True)]

# ================================================================ 預覽合成（@3x 螢幕 585×1266）
def ld(p): return np.asarray(Image.open(p).convert('RGBA')).astype(float) / 255
def tint_sprite(sp, col, a):
    o = sp.copy(); o[..., :3] = hx(col); o[..., 3] *= a; return o
def addsp(img, sp, cx, cy, col, a):
    h, w = sp.shape[:2]; x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(img.shape[1], x0 + w), min(img.shape[0], y0 + h)
    if xa >= xb or ya >= yb: return
    s = sp[ya - y0:yb - y0, xa - x0:xb - x0]; img[ya:yb, xa:xb] += s[..., 3:] * hx(col) * a
def oversp(img, sp, x0, y0):
    h, w = sp.shape[:2]; xa, ya, xb, yb = max(0, x0), max(0, y0), min(img.shape[1], x0 + w), min(img.shape[0], y0 + h)
    if xa >= xb or ya >= yb: return
    s = sp[ya - y0:yb - y0, xa - x0:xb - x0]; img[ya:yb, xa:xb] = img[ya:yb, xa:xb] * (1 - s[..., 3:]) + s[..., :3] * s[..., 3:]
_FX = {}
def fx():
    if not _FX:
        for nm in ('fx_glow_v3@3x', 'particles_v3@3x'):
            sh = ld(f'{OUT}/fx/{nm}.png'); js = json.load(open(f'{OUT}/fx/{nm}.json'))['frames']
            for k, f in js.items(): _FX[k] = sh[f['y']:f['y'] + f['h'], f['x']:f['x'] + f['w']]
    return _FX
def pets3x(key, g, pet_glow=1.0):
    import hd2d_v2_px as X, build_ui_hd2d_v2_concept as CC
    tint = hx(g['petTint']) * hx(g['ambientTint']); out = []
    for form, st, acc, pf, (fx_, fy) in ((CC.MAIN['form'], 'hungry', CC.MAIN['acc'], None, (97, 292)), (CC.KID['form'], 'happy', (), CC.KID['pattern_from'], (48, 302))):
        im, inf = X.compose_pet(form, st, acc, pattern_from=pf) if pf else X.compose_pet(form, st, acc)
        a = np.asarray(im).astype(float) / 255; a[..., :3] *= tint
        inner, nx, ny = B.rim_from_alpha(a[..., 3]); dv = np.array(g['rim']['dir'], float); dv /= np.linalg.norm(dv)
        w = np.clip(nx * dv[0] + ny * dv[1], 0, 1) * inner * min(1, g['rim']['intensity'] * 1.15); a[..., :3] = a[..., :3] * (1 - w[..., None]) + hx(g['rim']['color']) * w[..., None]
        out.append((up3(a), inf, fx_, fy))
    return out
def compose3x(key, with_pet=True, pet_glow=1.0, seed=5):
    d = f'{OUT}/{key}'; g = json.load(open(f'{d}/grade.json')); L = {n: ld(f'{d}/x3/{n}@3x.png') for n in ('sky', 'far', 'haze_far', 'mid', 'mist', 'fore')}
    img = L['sky'][..., :3].copy()
    for n in ('far', 'haze_far', 'mid', 'mist'): img = img * (1 - L[n][..., 3:]) + L[n][..., :3] * L[n][..., 3:]
    if with_pet:
        for (sp, inf, fx_, fy) in pets3x(key, g, pet_glow):
            cx, cy = (fx_ + MX) * S, (fy + MY) * S; yy, xx = np.mgrid[0:H3, 0:W3]
            sh = np.exp(-(((xx - cx) / (sp.shape[1] * .30)) ** 2 + ((yy - cy - 2) / 9) ** 2) ** 2) * .34; img *= 1 - sh[..., None]
            addsp(img, fx()['pet_pool'], cx, cy + 6, g['bulbGlowTint'], g['v3']['petLight']['intensity'] * pet_glow * .5)
            oversp(img, sp, int(cx - inf['pivot'][0] * S), int(cy - inf['pivot'][1] * S))
    img = img * (1 - L['fore'][..., 3:]) + L['fore'][..., :3] * L['fore'][..., 3:]
    img = img * ld(f'{d}/x3/lightmap@3x.png')[..., :3] + ld(f'{d}/x3/light_add@3x.png')[..., :3] + ld(f'{d}/x3/bloom@3x.png')[..., :3] * g['bloom']['intensity']
    F = fx(); rnd = np.random.RandomState(seed)
    for f in g['v3']['flares']:
        sp = F[f"flare_{f['size']}_{1 + int(rnd.randint(0, 6)):02d}"]; addsp(img, sp, (f['pos'][0] + MX) * S, (f['pos'][1] + MY) * S, f['tint'], f['intensity'])
    for e in g['v3']['emitters']:
        for i in range(e['max'] // 2 + 2):
            x, y = (rnd.uniform(e['rect'][0], e['rect'][2]) + MX) * S, (rnd.uniform(e['rect'][1], e['rect'][3]) + MY) * S
            if with_pet and abs(x / S - MX - 97) < 26 and 240 < y / S - MY < 296: continue
            if 'sprite' in e: addsp(img, F[e['sprite']], x, y, e['tint'], e['alpha'] * 2.2); continue
            if 'glow' in e: addsp(img, F[e['glow']], x, y, e['tint'], e['add'] * .8)
            oversp(img, F[f"{e['type']}_{1 + i % 6:02d}"], int(x - 12), int(y - 12))
    fc = hx(g['fog']['color']); img = img * (1 - g['fog']['density']) + fc * g['fog']['density']
    img = np.clip(img, 0, 1)[MY * S:MY * S + SH3, MX * S:MX * S + SW3]; vg = ld(f'{d}/x3/vignette@3x.png'); img = img * (1 - vg[..., 3:]) + vg[..., :3] * vg[..., 3:]
    return Image.fromarray(to8(img), 'RGB')
def previews():
    P = f'{OUT}/preview'; os.makedirs(P, exist_ok=True)
    import build_ui_hd2d_v3_mockups as M3, ui_hd2d_v3_lib as UL
    from PIL import ImageFont
    font = ImageFont.truetype(UL.FONT_SRC['sansb'], 26, index=UL.FONT_TTC_INDEX); fs = ImageFont.truetype(UL.FONT_SRC['sans'], 20, index=UL.FONT_TTC_INDEX)
    rows = []
    for key in ('H1', 'H3', 'H2', 'H4'):
        aft = compose3x(key); aft.save(f'{P}/{key}_v3_3x.png', optimize=True)
        old = Image.open(f'{SRC}/{key}/mockup_radiant.png').convert('RGB').resize((SW3, SH3), Image.NEAREST)
        M3._SC[('g', 'hungry', 1.0)] = aft.convert('RGBA'); UL.SCREEN[0] = f'garden_{key}'
        ui = M3.s_home().convert('RGB'); ui.save(f'{P}/{key}_v3_ui_3x.png', optimize=True)
        old_ui = None
        v2m = f'{ART}/ui/kit_hd2d_v2/mockups'
        sheet = Image.new('RGB', (SW3 * 3 + 80, SH3 + 110), (14, 16, 30)); dr = ImageDraw.Draw(sheet)
        for i, (im, t) in enumerate(((old, '前：v2 HD-2D（1x ×3）'), (aft, '後：V3-A 光影 @3x'), (ui, '後＋UI kit v3'))):
            sheet.paste(im, (20 + i * (SW3 + 20), 90)); dr.text((20 + i * (SW3 + 20), 50), t, font=fs, fill=(240, 230, 200))
        dr.text((20, 12), f"《微光小圃》花園 {key} {VAR[key]['name']}（{VAR[key]['hours']}）— 前後對比", font=font, fill=(255, 236, 184))
        sheet.save(f'{P}/compare_{key}.png', optimize=True); rows.append((key, old, aft, ui))
    k = 3; tw_, th_ = SW3 // k, SH3 // k
    ov = Image.new('RGB', (40 + 4 * (tw_ * 3 + 40), th_ + 130), (14, 16, 30)); dr = ImageDraw.Draw(ov)
    dr.text((20, 12), '《微光小圃》花園 H1–H4 V3-A — 前（v2）｜後（v3）｜後＋UI v3', font=font, fill=(255, 236, 184))
    for i, (key, old, aft, ui) in enumerate(rows):
        x0 = 20 + i * (tw_ * 3 + 40)
        dr.text((x0, 56), f"{key} {VAR[key]['name']}", font=fs, fill=(240, 230, 200))
        for j, im in enumerate((old, aft, ui)): ov.paste(im.resize((tw_, th_), Image.LANCZOS), (x0 + j * (tw_ + 4), 100))
    ov.save(f'{P}/overview.png', optimize=True)
    # 細節放大（mid 1x 新細節 vs 舊）
    return rows
def detail_compare():
    P = f'{OUT}/preview'; rows = []
    for key in ('H3', 'H4'):
        o = Image.open(f'{SRC}/{key}/mockup_radiant.png').convert('RGB').crop((0, 220, 195, 330)).resize((195 * 4, 110 * 4), Image.NEAREST)
        n = Image.open(f'{P}/{key}_v3_3x.png').crop((0, 220 * 3, 585, 330 * 3)).resize((195 * 4, 110 * 4), Image.LANCZOS); rows += [o, n]
    sh = Image.new('RGB', (195 * 8 + 20, 110 * 4 * 2 + 20), (14, 16, 30))
    for i, im in enumerate(rows): sh.paste(im, ((i % 2) * (195 * 4 + 20), (i // 2) * (110 * 4 + 20)))
    sh.save(f'{P}/detail_ground_zoom.png', optimize=True)

def main():
    what = sys.argv[1:] or ['fx', 'H1', 'H2', 'H3', 'H4', 'preview']
    os.makedirs(OUT, exist_ok=True)
    if 'fx' in what: fx_sheets(); print('fx ok')
    for k_ in ('H1', 'H2', 'H3', 'H4'):
        if k_ in what: build_variant(k_)
    if 'preview' in what: previews(); detail_compare(); print('preview ok')
if __name__ == '__main__': main()
