#!/usr/bin/env python3
"""《微光小圃》第 6 批：6b 散步＋6c 夢遊 轉 V3-A 光影（同花園／屋仔 V3 一樣：@3x 疊層＋grade json）。
原 1x／@3x key 同尺寸唔郁（art/breakthrough/6b、6c 原檔＝底，commit a1a6e9a2／af5b4821）；V3 全部放喺 6b/v3/、6c/v3/。
Pillow／numpy／scipy 程序化，冇 AI 圖。sprite（deco／卡／tile 底）alpha 0/255；光／霧／過場／UI 光層可以真 alpha。
夢遊中寵物光＝0（layout_hd2d_v3.json#petGlow dreaming／dreamEnter＝0）；場景光（月光、星、菇燈）照常。
用法：python3 build_walkdream_v3.py [walk] [dream] [json]   （冇參數＝全部）"""
import os, sys, json, copy, hashlib
import numpy as np
from PIL import Image
from scipy import ndimage as ND
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_hd2d_scenes as B
ART = os.path.abspath(f'{HERE}/..'); REPO = os.path.dirname(ART); BT = f'{REPO}/art/breakthrough'
O6B = f'{BT}/6b/v3'; O6C = f'{BT}/6c/v3'
LAY = json.load(open(f'{ART}/ui/kit_hd2d_v3/layout_hd2d_v3.json'))['petGlow']
SRC_COMMIT = {'6b': 'a1a6e9a2', '6c': 'af5b4821'}
hx, mix = B.hx, B.mix
S = 3
def to8(a): return (np.clip(a, 0, 1) * 255 + .5).astype(np.uint8)
def save(a, p):
    os.makedirs(os.path.dirname(p), exist_ok=True); a = to8(a); Image.fromarray(a, 'RGBA' if a.shape[-1] == 4 else 'RGB').save(p, optimize=True)
def ld(p): return np.asarray(Image.open(p).convert('RGBA')).astype(float) / 255
def up3(a, k=S): return np.repeat(np.repeat(a, k, 0), k, 1)
def smooth(a, W, H):
    return np.stack([np.asarray(Image.fromarray(to8(a[..., i])).resize((W, H), Image.BICUBIC)).astype(float) / 255 for i in range(a.shape[-1])], -1)
def gb(a, s):
    if s <= 0: return a.copy()
    return ND.gaussian_filter(a, (s, s, 0)) if a.ndim == 3 else ND.gaussian_filter(a, s)
def blur_rgba(a, s):
    if s <= 0: return a.copy()
    pm = a[..., :3] * a[..., 3:]; pa = gb(a[..., 3], s); pc = gb(pm, s)
    o = np.zeros_like(a); o[..., 3] = pa; o[..., :3] = np.where(pa[..., None] > 1e-4, pc / np.maximum(pa[..., None], 1e-4), a[..., :3]); return o
def lum(c): return c[..., :3] @ np.array([.2126, .7152, .0722])
def jdump(o, p):
    os.makedirs(os.path.dirname(p), exist_ok=True); json.dump(o, open(p, 'w'), ensure_ascii=False, indent=1)
def noise(W, H, cell, seed):
    r = np.random.RandomState(seed).rand(H // cell + 2, W // cell + 2)
    return np.asarray(Image.fromarray(to8(r)).resize(((W // cell + 2) * cell, (H // cell + 2) * cell), Image.BICUBIC)).astype(float)[:H, :W] / 255
def fbm(W, H, seed, cells=(64, 32, 16, 8), w=(.45, .28, .17, .1)):
    return sum(noise(W, H, c, seed + i) * k for i, (c, k) in enumerate(zip(cells, w)))
def radial(w, h, p=1.6):
    yy, xx = np.mgrid[0:h, 0:w].astype(float); d = np.hypot((xx - (w - 1) / 2) / (w / 2), (yy - (h - 1) / 2) / (h / 2)); return np.clip(1 - d, 0, 1) ** p
def rays(W, H, src, col, strength, spread, falloff, seed, k=(9, 17, 31, 53, 77), sharp=3):
    rnd = np.random.RandomState(seed); yy, xx = np.mgrid[0:H, 0:W].astype(float)
    ang = np.arctan2(yy - src[1], xx - src[0]); d = np.hypot(xx - src[0], yy - src[1]); n = np.zeros_like(ang)
    for kk in k: n += np.sin(ang * kk + rnd.rand() * 6.28) / kk ** .3
    n = ((n - n.min()) / (n.max() - n.min())) ** sharp
    win = np.clip((ang - spread[0]) / .18, 0, 1) * np.clip((spread[1] - ang) / .18, 0, 1)
    return (n * win * np.exp(-d / falloff) * strength)[..., None] * hx(col)
def grade(rgb, p):
    """同屋仔 V3 grade_h：× ambient → 飽和 → 對比 → split-tone"""
    c = rgb * hx(p['amb']); l = (c @ np.array([.299, .587, .114]))[..., None]; c = l + (c - l) * p['sat']; c = (c - .5) * p['con'] + .5
    sh, hi, a = hx(p['split'][0]), hx(p['split'][1]), p['split'][2]; l = (np.clip(c, 0, 1) @ np.array([.2126, .7152, .0722]))[..., None]
    return np.clip(c + (sh - .5) * a * (1 - l) ** 2 + (hi - .5) * a * l ** 2, 0, 1)
def lut_png(p):
    lut = np.zeros((16, 256, 3))
    for b in range(16):
        for gy in range(16):
            for rx in range(16): lut[gy, b * 16 + rx] = (rx / 15, gy / 15, b / 15)
    return grade(lut, p)
def gr(rgba, p): o = rgba.copy(); o[..., :3] = grade(rgba[..., :3], p); return o
def rim(rgba, col, k, d=(-.7, -.7)):
    """方向 rim（左上光）：只改內緣色，alpha 唔郁"""
    inner, nx, ny = B.rim_from_alpha(rgba[..., 3]); dv = np.array(d) / np.linalg.norm(d)
    w = (np.clip(nx * dv[0] + ny * dv[1], 0, 1) * inner * k)[..., None]; o = rgba.copy(); o[..., :3] = o[..., :3] * (1 - w) + hx(col) * w; return o
def addc(img, sp, cx, cy, a=1.0, col=None):
    h, w = sp.shape[:2]; x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(img.shape[1], x0 + w), min(img.shape[0], y0 + h)
    if xa >= xb or ya >= yb: return
    s = sp[ya - y0:yb - y0, xa - x0:xb - x0]; c = hx(col) if col else s[..., :3]
    img[ya:yb, xa:xb, :3] += s[..., 3:] * c * a
def over(img, sp, x0, y0):
    x0, y0 = int(round(x0)), int(round(y0)); h, w = sp.shape[:2]
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(img.shape[1], x0 + w), min(img.shape[0], y0 + h)
    if xa >= xb or ya >= yb: return
    s = sp[ya - y0:yb - y0, xa - x0:xb - x0]; img[ya:yb, xa:xb, :3] = img[ya:yb, xa:xb, :3] * (1 - s[..., 3:]) + s[..., :3] * s[..., 3:]
def glow_sprite(sz, col, p=1.8, core=.0):
    o = np.zeros((sz, sz, 4)); o[..., :3] = hx(col); o[..., 3] = np.clip(radial(sz, sz, p) + core * radial(sz, sz, 6), 0, 1); return o
def bloom(src, k=((4, .5), (12, .35), (30, .3))):
    return np.clip(sum(gb(src, s) * w for s, w in k), 0, 1)
def vignette(W, H, col, amt, cy=.47):
    yy, xx = np.mgrid[0:H, 0:W].astype(float); dd = ((xx / W - .5) / .5) ** 2 + ((yy / H - cy) / .5) ** 2
    o = np.zeros((H, W, 4)); o[..., :3] = hx(col); o[..., 3] = np.clip(np.clip((dd - .3) / .9, 0, 1) ** 1.6 * amt * 1.7, 0, .92); return o
def rgba(col, a): o = np.zeros(a.shape + (4,)); o[..., :3] = hx(col) if isinstance(col, str) else col; o[..., 3] = np.clip(a, 0, 1); return o
def fill_under(layer, need):
    """layer 冇像素但 need 嘅位：用最近像素色補（俾上層 DoF 邊緣唔會見穿）"""
    have = layer[..., 3] > .5
    if not have.any(): return layer
    idx = ND.distance_transform_edt(~have, return_distances=False, return_indices=True)
    o = layer.copy(); f = need & ~have; o[f, :3] = layer[idx[0][f], idx[1][f], :3]; o[f, 3] = 1; return o
def petglow_ref(pid):
    """per_pet id → petglow_v3 檔（第 3 批團絨／第 5 批細佬）"""
    if (pid[:1] in 'ABCDEFGH') and pid[1:].isdigit(): p = f'sprites/series2/petglow_v3/{pid}.json'
    else:
        f = {'sprout': 'evo_sprout'}.get(pid, pid if pid.startswith('evo_') else f'evo_still_{pid}'); p = f'sprites/tuanrong/petglow_v3/{f}.json'
    return p if os.path.exists(f'{ART}/{p}') else None

# ==================================================================== 6b 散步 walk_bg
WW, WH = 100, 120; W3, H3 = WW * S, WH * S; HOR = 30
WV = {   # 三個時段（現實時間連動：06–17 day、17–19 dusk、19–06 night）
 'day': dict(zh='日間', hours=[6, 17], amb='#fff2e2', sat=1.1, con=1.07, split=('#5a5aa0', '#ffd8a0', .1), bloom=(.8, .3), fog=('#fff0d8', .03), vig=.22, vigc='#3a3020',
             rim=('#fff0c8', .55), lm='#fff6ea', shade='#8a9ab8', sunCol='#ffe6b0', rayK=.26, haze='#fff2dc', hazeK=.14, mistK=.06, petTint='#fff8f0', petScale=.5,
             skyMap=None, emit='pollen'),
 'dusk': dict(zh='黃昏', hours=[17, 19], amb='#ffd8b8', sat=1.12, con=1.08, split=('#5a3a80', '#ffb070', .14), bloom=(.72, .45), fog=('#ffc8a0', .05), vig=.3, vigc='#3a1830',
              rim=('#ffb878', .7), lm='#ffe2c8', shade='#7a6aa8', sunCol='#ffb070', rayK=.38, haze='#ffc8a0', hazeK=.24, mistK=.08, petTint='#fff0e0', petScale=.8,
              skyMap={'#a2ccec': '#e8a0a0', '#fae2be': '#ffc890', '#FFF8EA': '#fff0c8'}, emit='gold'),
 'night': dict(zh='夜晚', hours=[19, 6], amb='#a8b0e8', sat=.98, con=1.08, split=('#202868', '#ffd890', .12), bloom=(.62, .8), fog=('#283060', .05), vig=.4, vigc='#0c0a28',
               rim=('#c0d0ff', .45), lm='#7c86c4', shade='#3a4078', sunCol='#d8e4ff', rayK=.16, haze='#4a5490', hazeK=.24, mistK=.14, petTint='#fff0e4', petScale=1.0,
               skyMap={'#a2ccec': '#1c2458', '#fae2be': '#2e3670', '#FFF8EA': '#7a80b8'}, emit='firefly')}
def walk_geo():
    yy, xx = np.mgrid[0:WH, 0:WW]; x = np.arange(WW)
    h1 = (HOR - 6 + 3 * np.sin(x / 9.0) + 2 * np.sin(x / 4.3 + 1)).astype(int)
    path = np.zeros((WH, WW), bool)
    for y in range(HOR + 3, WH):
        t = (y - (HOR + 3)) / (WH - 1 - (HOR + 3)); w = 5 + 36 * t ** 1.3; cx = 50 + 14 * np.sin(t * 3.2 + .4) * (.4 + .6 * t) - 6 * t
        path[y, max(0, int(round(cx - w / 2))):min(WW, int(round(cx + w / 2)) + 1)] = True
    tree = ((xx >= 2) & (xx <= 7) & (yy >= 14) & (yy < 86)) | ((xx <= 9) & (yy >= 84) & (yy <= 87))
    for cx, cy, r_ in ((4, 8, 13), (16, 4, 9), (-2, 22, 10), (12, 17, 7)): tree |= np.hypot(xx - cx, yy - cy) <= r_
    bush = np.zeros_like(tree)
    for cx, cy, r_ in ((92, 40, 7), (99, 36, 6), (86, 43, 4)): bush |= np.hypot(xx - cx, (yy - cy) * 1.2) <= r_
    fg = np.zeros_like(tree)
    for xi in range(WW):
        hgt = int(4 + 3 * abs(np.sin(xi * 1.7)) + (3 if xi < 14 or xi > 88 else 0) * abs(np.sin(xi / 2.3)))
        if 18 < xi < 82: hgt = int(1 + abs(np.sin(xi * 1.3)) * 2)
        fg[WH - hgt:, xi] = True
    sign = np.zeros_like(tree); sign[92:104, 84:86] = True; sign[88:95, 78:93] = True
    fore = tree | fg
    sky = (yy < h1[None, :]) & ~fore
    far = ~sky & ~fore & ~bush & (yy <= HOR + 3)
    mid = ~sky & ~far & ~fore
    return dict(yy=yy, xx=xx, h1=h1, path=path, tree=tree, bush=bush, fg=fg, sign=sign, sky=sky, far=far, mid=mid, fore=fore)
LANTERN = (88, 86)   # 夜晚 V3 加：木牌頂小燈籠（art 座標，底中）
def lantern_px():
    """3×4 小燈籠（夜晚加落 mid 層；alpha 0/255）：ink 頂、暖黃芯"""
    p = np.zeros((5, 3, 4)); ink = np.r_[hx('#432c23'), 1]; p[0, 1] = ink; p[1, :] = ink; p[2:4, :] = np.r_[hx('#ffd88a'), 1]; p[2, 1] = np.r_[hx('#fff4c8'), 1]; p[4, :] = ink; return p
def walk_layers(var):
    p = WV[var]; src = ld(f'{BT}/6b/walk_bg.png'); Gm = walk_geo()
    if p['skyMap']:
        for a_, b_ in p['skyMap'].items():
            m = Gm['sky'] & (np.abs(src[..., :3] - hx(a_)).sum(-1) < .02); src[m, :3] = hx(b_)
    L = {}
    for n in ('sky', 'far', 'mid', 'fore'):
        a = src.copy(); a[..., 3] = Gm[n].astype(float); L[n] = a
    L['sky'][..., 3] = 1; L['sky'] = fill_under(L['sky'], np.ones((WH, WW), bool)) if False else L['sky']
    sk = src.copy(); sk[..., 3] = Gm['sky']; L['sky'] = fill_under(sk, np.ones((WH, WW), bool))   # 天空全幅（樹／山後面補天色）
    L['far'] = fill_under(L['far'], Gm['fore'] & (Gm['yy'] <= HOR + 3) & ~Gm['sky'])
    L['mid'] = fill_under(L['mid'], Gm['fore'] & (Gm['yy'] > HOR + 3))
    if var == 'night':
        lp = lantern_px(); x0, y0 = LANTERN[0] - 1, LANTERN[1] - 5; L['mid'][y0:y0 + 5, x0:x0 + 3][lp[..., 3] > 0] = lp[lp[..., 3] > 0]
    return L, Gm, src
def walk_light(var, Gm):
    """art 空間光照（1x float）→ @3x 平滑；左上光"""
    p = WV[var]; yy, xx = Gm['yy'].astype(float), Gm['xx'].astype(float); base = hx(p['lm']); sh = hx(p['shade'])
    s = np.zeros((WH, WW))
    s += np.exp(-(((xx - 22) / 22) ** 2 + ((yy - 90) / 9) ** 2)) * .55          # 大樹投影（向右下）
    s += np.exp(-(((xx - 9) / 10) ** 2 + ((yy - 50) / 30) ** 2)) * .35 * (yy > HOR)   # 樹冠下
    s += np.exp(-(((xx - 95) / 8) ** 2 + ((yy - 47) / 3) ** 2)) * .5               # 樹叢腳
    s += np.exp(-(((xx - 89) / 8) ** 2 + ((yy - 104) / 2.5) ** 2)) * .45           # 木牌影
    s += np.clip((yy - 100) / 20, 0, 1) * .3                                         # 近鏡頭前景暗啲（框畫面）
    s += np.clip((xx - 70) / 30, 0, 1) * .15 * (yy > HOR)                            # 右邊背光
    s = np.clip(s, 0, .85)
    lm = base[None, None] * (1 - s[..., None]) + sh[None, None] * s[..., None] * mix(base, np.ones(3), .0)
    lm = np.clip(lm * (1 - .25 * s[..., None]) + 0, 0, 1)
    lm3 = smooth(lm, W3, H3)
    if var != 'night':   # 葉隙光斑（樹影入面）
        n = noise(W3, H3, 6, 17) * .6 + noise(W3, H3, 14, 18) * .4; spot = np.clip((n - .56) * 9, 0, 1)
        w = smooth(s[..., None], W3, H3)[..., 0]; w = np.clip(w * 2.2, 0, 1) * (.6 if var == 'day' else .35)
        lm3 = np.clip(lm3 * (1 - w[..., None]) + mix(lm3, base[None, None], .8) * (w * spot)[..., None] + lm3 * (w * (1 - spot))[..., None], 0, 1)
    else:   # 月光＋燈籠暖光池
        lx, ly = (LANTERN[0] + .5) * S, (LANTERN[1] - 2) * S; yy3, xx3 = np.mgrid[0:H3, 0:W3].astype(float)
        d = np.hypot((xx3 - lx) / 1.0, (yy3 - ly) / .8) / (34 * S); lm3 = lm3 + (np.clip(1 - d, 0, 1) ** 1.4 * 1.1)[..., None] * hx('#ffc27a')
        lm3 = np.clip(lm3 + (np.clip(1 - np.hypot(xx3 / W3, yy3 / H3) * 1.1, 0, 1) ** 2 * .25)[..., None] * hx('#a8b8ff'), 0, 1.4)
    return lm3
SUN = (31, 7)
def walk_variant(var):
    p = WV[var]; d = f'{O6B}/walk_bg/{var}'; L, Gm, src = walk_layers(var)
    # 1x 烘焙（fallback；同原 walk_bg 一樣 100×120 全幅）
    comp1 = L['sky'].copy()
    for n in ('far', 'mid', 'fore'): comp1[..., :3] = comp1[..., :3] * (1 - L[n][..., 3:]) + L[n][..., :3] * L[n][..., 3:]
    lm3 = walk_light(var, Gm)
    lm1 = np.asarray(Image.fromarray(to8(np.clip(lm3, 0, 1))).resize((WW, WH), Image.BOX)).astype(float) / 255
    # @3x 層
    X = {n: up3(gr(L[n], p)) for n in L}
    X['far'] = blur_rgba(X['far'], 2.2); X['fore'] = blur_rgba(X['fore'], 1.6)
    X['fore'][..., 3] = np.where(X['fore'][..., 3] < 1 / 255, 0, X['fore'][..., 3]); X['far'][..., 3] = np.where(X['far'][..., 3] < 1 / 255, 0, X['far'][..., 3])
    X['mid'][..., 3] = (X['mid'][..., 3] > .5).astype(float)
    sx, sy = (SUN[0] + .5) * S, (SUN[1] + .5) * S
    yy3 = np.mgrid[0:H3, 0:W3][0].astype(float) / S
    air = np.clip((HOR + 70 - yy3) / 50, .3, 1)[..., None]
    if var == 'night':
        add = rays(W3, H3, (sx, sy), '#b8c8ff', p['rayK'], (.1, 1.4), 520, 6) * air
        lx, ly = (LANTERN[0] + .5) * S, (LANTERN[1] - 2) * S
        add += (np.exp(-np.hypot(np.mgrid[0:H3, 0:W3][1] - lx, np.mgrid[0:H3, 0:W3][0] - ly) / (7 * S)) * .35)[..., None] * hx('#ffc070')
    else:
        add = rays(W3, H3, (sx, sy), p['sunCol'], p['rayK'], (.05, 1.45), 420, 4) * air + rays(W3, H3, (sx, sy), '#ffffff', p['rayK'] * .35, (.25, 1.2), 700, 8, sharp=5) * air
    yy, xx = np.mgrid[0:H3, 0:W3].astype(float); dsun = np.hypot(xx - sx, yy - sy)
    add += (np.exp(-dsun / (16 * S)) * (.35 if var != 'night' else .18))[..., None] * hx(p['sunCol'])      # 日／月暈
    add += (np.exp(-((yy / S - HOR) / 5) ** 2) * (.12 if var == 'dusk' else .06))[..., None] * hx(p['haze'])   # 地平線光
    add = np.clip(add, 0, 1)
    # emissive：日／月盤、夜晚燈籠、夜晚花仔微光
    em = np.zeros((H3, W3, 4)); disc = (np.hypot(xx - sx, yy - sy) < (6.5 if var != 'night' else 4.5) * S)
    em[disc] = np.r_[hx(p['sunCol']), 1]
    if var == 'night':
        lxa, lya = LANTERN[0] - 1, LANTERN[1] - 3; em[lya * S:(lya + 2) * S, lxa * S:(lxa + 3) * S] = np.r_[hx('#ffd88a'), 1]
        fl = (np.abs(src[..., :3] - hx('#FF8FB0')).sum(-1) < .03) & Gm['mid']; e1 = np.zeros((WH, WW, 4)); e1[fl] = np.r_[hx('#ffb0d0'), .35]; em = np.maximum(em, up3(e1))
    comp3 = X['sky'][..., :3].copy()
    for n in ('far', 'mid', 'fore'): comp3 = comp3 * (1 - X[n][..., 3:]) + X[n][..., :3] * X[n][..., 3:]
    comp3 = np.clip(comp3 * lm3 + add, 0, 1)
    t = p['bloom'][0]; hi = comp3 * np.clip((lum(comp3) - t) / (1 - t + 1e-6), 0, 1)[..., None] * .55
    bl = bloom(np.clip(em[..., :3] * em[..., 3:] + hi, 0, 1), ((3, .5), (9, .35), (22, .3)))
    far = np.exp(-((yy / S - (HOR - 2)) / 7) ** 2) * p['hazeK']; mist = np.exp(-((yy / S - (HOR + 12)) / 9) ** 2) * p['mistK'] * (.6 + .8 * noise(W3, H3, 40, 23))
    vg = vignette(W3, H3, p['vigc'], p['vig'])
    for n in ('sky', 'far', 'mid', 'fore'): save(X[n], f'{d}/x3/{n}@3x.png'); save(gr(L[n], p), f'{d}/{n}.png')
    save(np.clip(lm3, 0, 1), f'{d}/x3/lightmap@3x.png'); save(add, f'{d}/x3/light_add@3x.png'); save(bl, f'{d}/x3/bloom@3x.png'); save(em, f'{d}/x3/emissive@3x.png')
    save(rgba(p['haze'], far), f'{d}/x3/haze_far@3x.png'); save(rgba(mix(hx(p['fog'][0]), np.ones(3), .3), mist), f'{d}/x3/mist@3x.png'); save(vg, f'{d}/x3/vignette@3x.png')
    save(lm1, f'{d}/lightmap.png'); save(np.asarray(Image.fromarray(to8(add)).resize((WW, WH), Image.BOX)).astype(float) / 255, f'{d}/light_add.png')
    save(lut_png(p), f'{d}/lut.png')
    J = json.load(open(f'{BT}/6b/walk6b.json'))['keys']['6b:walk_bg']; stones = J['stones']
    emit = {'pollen': dict(type='pollen', sprite='scenes/hd2d_v3/fx/particles_v3@3x.json#pollen_01..06', glow='glow_12', tint='#fff4c8', rect=[0, 0, 100, 80], max=10, rate=.8, life=[4, 8], vy=[-1, 1], vx=[1, 3], add=.45, note='日光柱入面花粉／浮塵'),
            'gold': dict(type='gold', sprite='scenes/hd2d_v3/fx/particles_v3@3x.json#gold_01..06', glow='glow_12', tint='#ffd890', rect=[0, 10, 100, 90], max=12, rate=1.0, life=[3, 6], vy=[-3, -1], add=.6, note='黃昏金塵'),
            'firefly': dict(type='firefly', sprite='scenes/hd2d_v3/fx/particles_v3@3x.json#firefly_01..06', glow='glow_12', tint='#d8ff90', rect=[4, 40, 96, 112], max=10, rate=.6, life=[3, 6], vy=[-1, 1], sway=4, add=.9, note='夜晚螢火蟲（草地；避開路中）')}[p['emit']]
    g = dict(variant=var, name=f'散步路・{p["zh"]}（V3-A）', hours=p['hours'], ambientTint=p['amb'], petTint=p['petTint'], saturation=p['sat'], contrast=p['con'],
             bloom=dict(threshold=p['bloom'][0], intensity=p['bloom'][1]), fog=dict(color=p['fog'][0], density=p['fog'][1]), vignette=p['vig'],
             rim=dict(color=p['rim'][0], intensity=p['rim'][1], dir=[-.7, -.7]), splitTone=dict(shadow=p['split'][0], highlight=p['split'][1], amount=p['split'][2]),
             v3=dict(note='6b walk_bg V3：@3x 層 300×360（＝原 walk_bg@3x 尺寸，可直接頂替喺同一個 300×360 框）；1x 層 100×120 係 fallback。原 walk_bg.png／@3x 唔郁。',
                     layerSize3x=[W3, H3], layerSize1x=[WW, WH], stack='../../walk6b_v3.json#stack', sun=dict(pos=list(SUN), kind='moon' if var == 'night' else 'sun'),
                     flares=[dict(pos=list(SUN), size='m', tint=p['sunCol'], intensity=.6 if var != 'night' else .3, fps=2)] + ([dict(pos=[LANTERN[0], LANTERN[1] - 2], size='s', tint='#ffd890', intensity=.5, fps=3)] if var == 'night' else []),
                     emitters=[emit], lantern=dict(pos=list(LANTERN), flicker=dict(type='breathe', hz=.3, amp=.08)) if var == 'night' else None,
                     stoneGlow=dict(sprite='stone_glow@3x.png', stones=stones, tint='#fff0c0' if var != 'night' else '#c8d8ff', blend='lighter', alpha=.7 if var != 'night' else .9, pulse=dict(hz=.6, amp=.25),
                                    note='而家行到嗰格（第 n 粒踏腳石）底下發光；已行過嘅格 alpha .3'),
                     petLight=dict(sprite='scenes/hd2d_v3/fx/fx_glow_v3@3x.json#pet_pool', anchor='foot', size3x=[150, 60], tint='#ffe2a8', intensity=round(.35 * p['petScale'] / .5, 2) if var != 'day' else .3,
                                   multiplyBy='petGlow', walkScale=p['petScale'], formLight='walk6b_v3.json#pets.<pid>.petglow（逐形態光暈 anchor；walk clip 用 idle_01 anchor＋bob dy）',
                                   rule='散步＝醒（petGlow 1）；layout_hd2d_v3.json#petGlow：瞓覺／sleepClip／入夢＝0。場景光（日、月、燈籠）唔受影響。'),
                     petPop=dict(contactShadow=dict(alpha=.32 if var != 'night' else .4, rx=.3, ry=.07), rim=dict(color=p['rim'][0], intensity=p['rim'][1]))))
    jdump(g, f'{d}/grade.json')
    return d
def deco_v3():
    J = json.load(open(f'{BT}/6b/walk6b.json'))['keys']; out = {}
    for k in [k for k in J if k.startswith('6b:deco_')]:
        n = k.split(':')[1]; a = ld(f"{BT}/6b/{J[k]['1x']}"); a[..., 3] = (a[..., 3] > .5).astype(float)
        r = rim(a, '#fff4dc', .55); x3 = up3(r)
        # 主色（最多像素、唔係 ink）
        cs = a[a[..., 3] > .5][:, :3]; cs = cs[lum(cs) > .25]; q = np.round(cs * 15).astype(int) @ np.array([1, 16, 256]) if len(cs) else None
        col = cs[np.argmax(q == np.bincount(q).argmax())] if len(cs) else hx('#fff0c0')
        glow = np.zeros((72, 72, 4)); glow[..., :3] = mix(col, np.ones(3), .45); glow[..., 3] = radial(72, 72, 2.0) * .85
        save(x3, f'{O6B}/deco/{n}_v3@3x.png'); save(glow, f'{O6B}/deco/{n}_glow@3x.png')
        out[k] = dict(v3=f'deco/{n}_v3@3x.png', glow=f'deco/{n}_glow@3x.png', size3x=[48, 48], glowSize3x=[72, 72], glowTint='#%02x%02x%02x' % tuple(to8(mix(col, np.ones(3), .45))),
                      note='rim（左上光）已烘入 sprite（alpha 0/255）；撿到時 glow lighter＋sparkle')
    ao = np.zeros((20, 54, 4)); ao[..., 3] = radial(54, 20, 1.4) * .45; ao[..., :3] = hx('#1a1420'); save(ao, f'{O6B}/deco/deco_ao@3x.png')
    sg = np.zeros((60, 120, 4)); sg[..., :3] = 1; sg[..., 3] = np.clip(radial(120, 60, 1.6) * .9 + radial(120, 60, 5) * .4, 0, 1); save(sg, f'{O6B}/walk_bg/stone_glow@3x.png')
    sp = np.zeros((24, 24 * 6, 4))   # 撿到 sparkle 6 幀（十字星，真 alpha 光層）
    for i in range(6):
        t = i / 5; r = 2 + 9 * np.sin(t * np.pi); c = 12; yy, xx = np.mgrid[0:24, 0:24].astype(float)
        a = np.clip(1 - np.abs(xx - c) / 1.2, 0, 1) * np.clip(1 - np.abs(yy - c) / r, 0, 1) + np.clip(1 - np.abs(yy - c) / 1.2, 0, 1) * np.clip(1 - np.abs(xx - c) / r, 0, 1)
        a = np.clip(a + radial(24, 24, 3) * np.sin(t * np.pi), 0, 1) * (1 - t * .3); sp[:, i * 24:(i + 1) * 24, :3] = 1; sp[:, i * 24:(i + 1) * 24, 3] = a
    save(sp, f'{O6B}/deco/sparkle@3x.png')
    return out
def walk_json(deco):
    J6 = json.load(open(f'{BT}/6b/walk6b.json'))
    pets = {pid: dict(petglow=petglow_ref(pid), **({} if petglow_ref(pid) else dict(formLightNote='呢個形態冇自身光源（petglow_v3 index notLight）→ 只用通用 pet_pool 光池')), walkClip=v['3x'], frameSize=v['frameSize'], pivot=v['pivot'], note='walk clip 本身唔郁；光暈用 petglow idle_01 anchor＋bob（feet 0/−1；hop 0/−1/−2/−2/−1/0）') for pid, v in J6['pets'].items()}
    stack = [dict(layer='sky', file='x3/sky@3x.png', fallback1x='sky.png', parallax=.1), dict(layer='far', file='x3/far@3x.png', fallback1x='far.png', parallax=.3, note='DoF 已烘'),
             dict(layer='haze_far', file='x3/haze_far@3x.png', parallax=.3), dict(layer='mid', file='x3/mid@3x.png', fallback1x='mid.png', parallax=1.0, note='路、石、木牌（夜晚含燈籠）'),
             dict(layer='stone_glow', realtime=True, blend='lighter', note='grade.v3.stoneGlow'), dict(layer='mist', file='x3/mist@3x.png', parallax=1.0, drift3x=2),
             dict(layer='pet', realtime=True, note='walk clip × petTint × ambientTint＋rim；contact shadow；petLight（× petGlow）'),
             dict(layer='deco', realtime=True, note='撿到嘅 deco：deco/<n>_v3@3x＋deco_ao＋glow（lighter）＋sparkle'),
             dict(layer='fore', file='x3/fore@3x.png', fallback1x='fore.png', parallax=1.5, note='大樹＋前景草，DoF 已烘'),
             dict(layer='lightmap', file='x3/lightmap@3x.png', fallback1x='lightmap.png', blend='multiply'), dict(layer='light_add', file='x3/light_add@3x.png', fallback1x='light_add.png', blend='lighter', note='god rays＋日月暈'),
             dict(layer='bloom', file='x3/bloom@3x.png', blend='lighter', alpha='grade.bloom.intensity'), dict(layer='emissive_flicker', file='x3/emissive@3x.png', blend='lighter', realtime=True),
             dict(layer='flares', realtime=True, sprite='scenes/hd2d_v3/fx/fx_glow_v3@3x.json#flare_*'), dict(layer='particles', realtime=True, note='grade.v3.emitters'),
             dict(layer='fog', realtime=True, note='fillRect grade.fog'), dict(layer='vignette', file='x3/vignette@3x.png', note='300×360 框內 vignette')]
    o = dict(version=3, batch='第 6 批 6b 散步 V3-A', source=dict(dir='art/breakthrough/6b', commit=SRC_COMMIT['6b'], note='原 1x／@3x key、尺寸、walk6b.json 冇郁；V3 喺 v3/'),
             keys={'6b:walk_bg_v3': dict(dir='walk_bg/<variant>', variants={k: dict(zh=v['zh'], hours=v['hours'], grade=f'walk_bg/{k}/grade.json') for k, v in WV.items()},
                                         size3x=[W3, H3], size1x=[WW, WH], replaces='6b:walk_bg（同尺寸；揀 variant 跟現實時間）', stoneGlow='walk_bg/stone_glow@3x.png')},
             deco=deco, decoShared=dict(ao='deco/deco_ao@3x.png', sparkle=dict(file='deco/sparkle@3x.png', frames=6, frame=[24, 24], fps=12)),
             stack=stack, pets=pets, petGlow=dict(source='ui/kit_hd2d_v3/layout_hd2d_v3.json#petGlow', walk='awake＝1', states=LAY['states']))
    jdump(o, f'{O6B}/walk6b_v3.json')
def compose_walk(var, pid='A3', fi=2, stone=-2, deco=None, seed=5):
    """預覽合成（300×360 @3x）"""
    d = f'{O6B}/walk_bg/{var}'; g = json.load(open(f'{d}/grade.json')); X = {n: ld(f'{d}/x3/{n}@3x.png') for n in ('sky', 'far', 'haze_far', 'mid', 'mist', 'fore')}
    img = X['sky'][..., :3].copy()
    def ov(a): nonlocal img; img = img * (1 - a[..., 3:]) + a[..., :3] * a[..., 3:]
    for n in ('far', 'haze_far', 'mid'): ov(X[n])
    sv = g['v3']['stoneGlow']; sg = ld(f'{O6B}/walk_bg/stone_glow@3x.png')
    st = sv['stones']; cur = st[stone]
    for i, (sx, sy) in enumerate(st):
        if st.index([sx, sy]) <= st.index(cur): addc(img, sg, (sx + .5) * S, (sy + .5) * S, sv['alpha'] * (1 if [sx, sy] == cur else .3), sv['tint'])
    ov(X['mist'])
    J6 = json.load(open(f'{BT}/6b/walk6b.json'))['pets'][pid]; clip = ld(f"{BT}/6b/{J6['3x']}"); fw, fh = J6['frameSize'][0] * S, J6['frameSize'][1] * S
    fr = clip[:, fi * fw:(fi + 1) * fw].copy(); fr[..., :3] *= hx(g['petTint']) * hx(g['ambientTint'])
    a1 = fr[::S, ::S]; a1 = rim(a1, g['rim']['color'], min(1, g['rim']['intensity'] * 1.1)); fr = up3(a1)
    fx_, fy = 150, 300; yy, xx = np.mgrid[0:H3, 0:W3]
    sh = np.exp(-(((xx - fx_) / (fw * .3)) ** 2 + ((yy - fy - 2) / 8) ** 2) ** 2) * g['v3']['petPop']['contactShadow']['alpha']; img *= 1 - sh[..., None]
    pl = g['v3']['petLight']; pool = glow_sprite(150, pl['tint'], 1.4); pool = np.asarray(Image.fromarray(to8(pool)).resize((150, 60), Image.BICUBIC)).astype(float) / 255
    addc(img, pool, fx_, fy + 4, pl['intensity'] * .6)
    over(img, fr, fx_ - J6['pivot'][0] * S, fy - J6['pivot'][1] * S)
    if deco:
        for n, (dx, dy) in deco:
            sp = ld(f'{O6B}/deco/{n}_v3@3x.png'); gl = ld(f'{O6B}/deco/{n}_glow@3x.png'); ao = ld(f'{O6B}/deco/deco_ao@3x.png')
            over(img, ao, dx - 27, dy - 6); sp = sp.copy(); sp[..., :3] *= hx(g['ambientTint']); over(img, sp, dx - 24, dy - 46); addc(img, gl, dx, dy - 22, .5)
    ov(X['fore'])
    img = img * ld(f'{d}/x3/lightmap@3x.png')[..., :3] + ld(f'{d}/x3/light_add@3x.png')[..., :3] + ld(f'{d}/x3/bloom@3x.png')[..., :3] * g['bloom']['intensity']
    rnd = np.random.RandomState(seed); FX = fxs()
    for f in g['v3']['flares']: addc(img, FX[f"flare_{f['size']}_{1 + rnd.randint(0, 6):02d}"], (f['pos'][0] + .5) * S, (f['pos'][1] + .5) * S, f['intensity'], f['tint'])
    for e in g['v3']['emitters']:
        for i in range(e['max']):
            x, y = rnd.uniform(e['rect'][0], e['rect'][2]) * S, rnd.uniform(e['rect'][1], e['rect'][3]) * S
            addc(img, FX[e['glow']], x, y, e['add'] * .8, e['tint']); over(img, FX[f"{e['type']}_{1 + i % 6:02d}"], x - 12, y - 12)
    fc = hx(g['fog']['color']); img = img * (1 - g['fog']['density']) + fc * g['fog']['density']
    vg = ld(f'{d}/x3/vignette@3x.png'); img = np.clip(img, 0, 1); img = img * (1 - vg[..., 3:]) + vg[..., :3] * vg[..., 3:]
    return Image.fromarray(to8(img), 'RGB')
_FX = {}
def fxs():
    if not _FX:
        for nm in ('fx_glow_v3@3x', 'particles_v3@3x'):
            sh = ld(f'{ART}/scenes/hd2d_v3/fx/{nm}.png'); js = json.load(open(f'{ART}/scenes/hd2d_v3/fx/{nm}.json'))['frames']
            for k, f in js.items(): _FX[k] = sh[f['y']:f['y'] + f['h'], f['x']:f['x'] + f['w']]
    return _FX
def build_walk():
    for v in WV: walk_variant(v); print('walk', v, 'ok')
    deco = deco_v3(); walk_json(deco); print('walk json ok', len(deco))

# ==================================================================== 6c 夢遊
DW, DH = 195, 422; D3W, D3H = DW * S, DH * S
DREAM = dict(amb='#e8e4ff', sat=1.06, con=1.06, split=('#1c1650', '#ffe6b0', .12))
THEME = {'forest': dict(zh='夢森林', light='#d8ffd0', glow='#a8ff9a', amb='#e4f4ff', flicker=dict(type='breathe', hz=.35, amp=.18), note='菇菇、螢光葉微光'),
         'lake': dict(zh='星湖', light='#d0e8ff', glow='#9ad8ff', amb='#dce8ff', flicker=dict(type='shimmer', hz=.8, amp=.15), note='水面 caustic 4 幀'),
         'toy': dict(zh='玩具屋', light='#ffe8d0', glow='#ffc890', amb='#fff0e8', flicker=dict(type='breathe', hz=.25, amp=.1), note='暖燈'),
         'star': dict(zh='星空頂', light='#fff4d0', glow='#ffe890', amb='#ece6ff', flicker=dict(type='twinkle', hz=1.2, amp=.35), note='星星閃')}
MOON_C = (27.5, 24.5)
def dream_bg_v3():
    d = f'{O6C}/dream_bg'; src = ld(f'{BT}/6c/fx/dream_bg.png'); rgb = src[..., :3]
    def is_(c): return np.abs(rgb - hx(c)).sum(-1) < .02
    yy, xx = np.mgrid[0:DH, 0:DW]
    moon = (is_('#ffd45a') | is_('#24172c') | (is_('#fff6cf') & (yy < 40) & (xx < 40))) & (np.hypot(xx - MOON_C[0], yy - MOON_C[1]) < 13)
    cloud = (yy >= 376) & (is_('#c9c0f0') | is_('#f3eefa') | (is_('#8f85c2') & (yy >= 380)))
    star = (is_('#fff6cf') | is_('#ffe08a') | is_('#8f85c2') | is_('#574f8a')) & ~moon & ~cloud
    big = (is_('#fff6cf') | is_('#ffe08a')) & star
    base = src.copy(); base[..., 3] = (~(moon | cloud | star)).astype(float); sky1 = fill_under(base, np.ones((DH, DW), bool))
    sky3 = up3(gr(sky1, DREAM)); soft = smooth(gb(gr(sky1, DREAM), 3), D3W, D3H); sky3[..., :3] = sky3[..., :3] * .55 + soft[..., :3] * .45
    Y, X = np.mgrid[0:D3H, 0:D3W].astype(float)
    neb = fbm(D3W, D3H, 61, cells=(160, 80, 40, 20)); neb2 = fbm(D3W, D3H, 71, cells=(200, 100, 50, 25))
    band = np.exp(-(((Y / S) - (150 + 40 * np.sin(X / S / 31))) / 55) ** 2)            # 銀河帶（斜）
    add = (np.clip((neb - .45) * 2.4, 0, 1) * band * .3)[..., None] * hx('#9a7cff') + (np.clip((neb2 - .5) * 2.6, 0, 1) * band * .16)[..., None] * hx('#ff9ad8')
    add += (np.clip((neb - .5) * 3, 0, 1) * np.exp(-((Y / S - 300) / 60) ** 2) * .1)[..., None] * hx('#7ad8ff')
    mx, my = (MOON_C[0]) * S, (MOON_C[1]) * S; dm = np.hypot(X - mx, Y - my)
    add += (np.exp(-dm / (22 * S)) * .32)[..., None] * hx('#ffe8b0') + (np.exp(-dm / (60 * S)) * .12)[..., None] * hx('#c8b8ff')
    add += rays(D3W, D3H, (mx, my), '#fff0c8', .09, (-.2, 1.75), 700, 12, sharp=4)
    add = np.clip(add, 0, 1)
    # emissive：星（實色 0/255 pix）＋月
    em = np.zeros((DH, DW, 4)); em[star] = src[star]; em[star, 3] = 1; em[moon] = src[moon]; em[moon, 3] = 1
    moonL = np.zeros((DH, DW, 4)); moonL[moon] = src[moon]; moonL[moon, 3] = 1; moonL = rim(moonL, '#fffbe8', .6)
    em3 = up3(em); moon3 = up3(moonL)
    # 雲（前景）：月光由左上 rim；底部霧
    cl = src.copy(); cl[..., 3] = cloud.astype(float); cl = gr(cl, DREAM); cl = rim(cl, '#fff4d8', .55, d=(-.5, -.85))
    cl3 = blur_rgba(up3(cl), .8); cl3[..., 3] = np.where(cl3[..., 3] < 1 / 255, 0, cl3[..., 3])
    mist = rgba('#b8a8f0', np.exp(-((Y / S - 372) / 22) ** 2) * .32 * (.55 + .9 * noise(D3W, D3H, 60, 81)))
    lm = np.ones((D3H, D3W, 3)) * hx('#f4f0ff'); lm = lm * (1 - (np.clip((X / D3W) * .6 + (Y / D3H) * .4 - .45, 0, 1) * .14)[..., None])   # 左上（月）亮、右下暗
    hiS = np.clip(em3[..., :3] * em3[..., 3:], 0, 1); bl = bloom(hiS * .9 + moon3[..., :3] * moon3[..., 3:] * .35, ((3, .55), (10, .4), (28, .35)))
    vg = vignette(D3W, D3H, '#08061c', .3, cy=.5)
    save(sky3, f'{d}/sky@3x.png'); save(add, f'{d}/light_add@3x.png'); save(em3, f'{d}/emissive@3x.png'); save(moon3, f'{d}/moon@3x.png'); save(cl3, f'{d}/clouds@3x.png')
    save(mist, f'{d}/mist@3x.png'); save(np.clip(lm, 0, 1), f'{d}/lightmap@3x.png'); save(bl, f'{d}/bloom@3x.png'); save(vg, f'{d}/vignette@3x.png'); save(lut_png(DREAM), f'{d}/lut.png')
    # 1x fallback（195×422 烘焙）
    comp = composite_dream_bg(); save(np.asarray(comp.resize((DW, DH), Image.BOX)).astype(float) / 255, f'{d}/dream_bg_v3.png'); comp.save(f'{d}/dream_bg_v3@3x.png', optimize=True)
    ys, xs = np.where(big); rnd = np.random.RandomState(3)
    tw = [dict(x=int(x), y=int(y), hz=round(float(rnd.uniform(.3, 1.1)), 2), phase=round(float(rnd.rand()), 2), flare='s' if src[y, x, 0] > .99 else 'xs') for y, x in zip(ys, xs)]
    return dict(size3x=[D3W, D3H], size1x=[DW, DH], baked=dict(x3='dream_bg/dream_bg_v3@3x.png', x1='dream_bg/dream_bg_v3.png', note='全部層預先合成（唔做即時合成時用）'),
                stack=[dict(layer='sky', file='dream_bg/sky@3x.png', parallax=.1), dict(layer='light_add', file='dream_bg/light_add@3x.png', blend='lighter', note='星雲＋銀河帶＋月暈＋月光柱', drift3x=[3, 0], driftSec=40),
                       dict(layer='stars', file='dream_bg/emissive@3x.png', blend='lighter', twinkle='twinkle'), dict(layer='mist', file='dream_bg/mist@3x.png', drift3x=[6, 0], driftSec=12),
                       dict(layer='clouds', file='dream_bg/clouds@3x.png', parallax=1.2, bob3x=2, bobSec=6), dict(layer='lightmap', file='dream_bg/lightmap@3x.png', blend='multiply'),
                       dict(layer='vignette', file='dream_bg/vignette@3x.png'), dict(layer='moon', file='dream_bg/moon@3x.png', note='月 sprite（0/255）＋rim；喺 vignette 上面保持亮'),
                       dict(layer='bloom', file='dream_bg/bloom@3x.png', blend='lighter', alpha=.8, pulse=dict(hz=.15, amp=.1)),
                       dict(layer='grid', realtime=True, note='tiles＋glow＋fog＋pet（見 tiles／fog）'), dict(layer='particles', realtime=True)],
                twinkle=tw, moon=dict(center=list(MOON_C), flare=dict(size='m', tint='#fff0c8', intensity=.55, fps=1.5)),
                emitters=[dict(type='dreamMote', sprite='scenes/hd2d_v3/fx/particles_v3@3x.json#mote_01..06', glow='glow_12', tints=['#c8b8ff', '#ffc8e8', '#b8e8ff'], rect=[0, 40, 195, 400], max=16, rate=.8, life=[4, 9], vy=[-2, -.5], sway=5, add=.6),
                          dict(type='shootingStar', every=[6, 14], rect=[20, 10, 190, 140], len=26, angleDeg=[200, 230], durMs=650, tint='#fff6dc', width3x=3, note='程序畫：頭亮尾漸淡（lighter）')], grade=DREAM)
def composite_dream_bg():
    d = f'{O6C}/dream_bg'; L = {n: ld(f'{d}/{n}@3x.png') for n in ('sky', 'light_add', 'emissive', 'moon', 'bloom', 'mist', 'clouds', 'lightmap', 'vignette')}
    img = L['sky'][..., :3] + L['light_add'][..., :3] + L['emissive'][..., :3] * L['emissive'][..., 3:]
    img = img * (1 - L['mist'][..., 3:]) + L['mist'][..., :3] * L['mist'][..., 3:]; img = img * (1 - L['clouds'][..., 3:]) + L['clouds'][..., :3] * L['clouds'][..., 3:]
    img = np.clip(img, 0, 1) * L['lightmap'][..., :3]; img = img * (1 - L['vignette'][..., 3:]) + L['vignette'][..., :3] * L['vignette'][..., 3:]
    img = img * (1 - L['moon'][..., 3:]) + L['moon'][..., :3] * L['moon'][..., 3:]; img += L['bloom'][..., :3] * .8
    return Image.fromarray(to8(img), 'RGB')
def accent_mask(a):
    """tile 入面『自己發光』嘅細節：高飽和／高亮、唔係最常見三隻色"""
    rgb = a[..., :3]; op = a[..., 3] > .5; q = np.round(rgb * 255).astype(int) @ np.array([1, 256, 65536])
    vals, cnt = np.unique(q[op], return_counts=True); common = set(vals[np.argsort(-cnt)[:3]])
    mx, mn = rgb.max(-1), rgb.min(-1); sat = (mx - mn) / np.maximum(mx, 1e-3)
    return op & ~np.isin(q, list(common)) & (((sat > .35) & (mx > .7)) | (lum(rgb) > .82))
def tiles_v3():
    out = {}
    for th, P in THEME.items():
        a = ld(f'{BT}/6c/tiles/tile_{th}.png'); a[..., 3] = (a[..., 3] > .5).astype(float); H_, W_ = a.shape[:2]
        acc = accent_mask(a)
        x3 = up3(a); Y, X = np.mgrid[0:H_ * S, 0:W_ * S].astype(float); lx, ly = (X % (56 * S)) / (56 * S), Y / (H_ * S)
        key = 1.08 - .22 * (lx * .55 + ly * .45)                                                   # 左上 key light
        inside = ND.distance_transform_edt(x3[..., 3] > .5) / S; ao = 1 - .22 * np.clip(1 - inside / 5, 0, 1)   # 邊 AO
        pool = 1 + .1 * np.exp(-(((lx - .5) / .3) ** 2 + ((ly - .55) / .26) ** 2))               # 中心（寵物企位）月光池
        sh = (key * ao * pool)[..., None] * mix(hx(P['amb']), np.ones(3), .5)
        c = x3.copy(); c[..., :3] = np.clip(x3[..., :3] * sh, 0, 1)
        rr = rim(a, P['light'], .55); rm = up3(np.any(np.abs(rr - a) > 1e-6, -1).astype(float))[..., None]; c[..., :3] = c[..., :3] * (1 - rm) + up3(rr)[..., :3] * rm * .9 + c[..., :3] * rm * .1
        c = gr(c, dict(amb=P['amb'], sat=1.06, con=1.05, split=DREAM['split'])); c[..., 3] = x3[..., 3]
        e3 = up3(acc.astype(float)); em = np.zeros_like(c); em[..., :3] = c[..., :3]; em[..., 3] = e3
        gsrc = up3(a)[..., :3] * e3[..., None]; gl = bloom(gsrc, ((2, .7), (6, .6), (14, .5))); ga = np.clip(lum(gl) * 1.6, 0, 1)
        glow = np.zeros_like(c); glow[..., :3] = np.where(ga[..., None] > 0, np.clip(gl / np.maximum(gl.max(-1, keepdims=True), 1e-3), 0, 1) * .5 + hx(P['glow']) * .5, 0); glow[..., 3] = ga * .9
        save(c, f'{O6C}/tiles/tile_{th}_v3@3x.png'); save(glow, f'{O6C}/tiles/tile_{th}_glow@3x.png'); save(em, f'{O6C}/tiles/tile_{th}_emissive@3x.png')
        o = dict(v3=f'tiles/tile_{th}_v3@3x.png', glow=f'tiles/tile_{th}_glow@3x.png', emissive=f'tiles/tile_{th}_emissive@3x.png', size3x=[W_ * S, H_ * S], variants=4, tile3x=[168, 168],
                 zh=P['zh'], light=P['light'], glowTint=P['glow'], flicker=P['flicker'], note=P['note'] + '；key light 左上、邊 AO、中心月光池、rim 已烘（alpha 0/255）', accentPx=int(acc.sum()))
        if th == 'lake':
            water = a[..., 3] > .5; blue = (a[..., 2] > a[..., 0] + .08) & water; b3 = up3(blue.astype(float))
            fr = []
            for i in range(4):
                n = noise(W_ * S, H_ * S, 10, 200 + i) * .5 + noise(W_ * S, H_ * S, 5, 300 + i) * .5
                ca = np.clip(1 - np.abs(n - .5) * 12, 0, 1) * b3 * .55; f = np.zeros((H_ * S, W_ * S, 4)); f[..., :3] = hx('#d8f0ff'); f[..., 3] = ca; fr.append(f)
            save(np.concatenate(fr, 0), f'{O6C}/tiles/tile_lake_caustic@3x.png'); o['caustic'] = dict(file='tiles/tile_lake_caustic@3x.png', frames=4, layout='直條（每幀 672×168）', fps=4, blend='lighter')
        out[f'6c:tile_{th}_v3'] = o
    ring = np.zeros((216, 216, 4)); Y, X = np.mgrid[0:216, 0:216].astype(float); dd = np.maximum(np.abs(X - 107.5), np.abs(Y - 107.5))
    ring[..., :3] = hx('#e0d4ff'); ring[..., 3] = np.exp(-((dd - 84) / 7) ** 2) * .9 + np.clip(1 - dd / 84, 0, 1) ** 2 * .15; save(ring, f'{O6C}/tiles/tile_reveal_glow@3x.png')
    out['6c:tile_reveal_glow'] = dict(file='tiles/tile_reveal_glow@3x.png', size3x=[216, 216], blend='lighter', anim='揭開時 0→1→.25（600ms）', note='已揭格邊微光')
    return out
def fog_v3():
    f = ld(f'{BT}/6c/tiles/fog.png'); op = f[..., 3] > .5
    shape = ND.binary_fill_holes(ND.binary_closing(op, np.ones((3, 3)), iterations=2)); shape3 = up3(shape.astype(float))
    q = np.round(f[..., :3] * 255).astype(int) @ np.array([1, 256, 65536]); vals, cnt = np.unique(q[op], return_counts=True)
    det = op & (q != vals[np.argmax(cnt)]); det3 = up3(det.astype(float)); f3 = up3(f)
    inside = ND.distance_transform_edt(shape3 > .5); edge = np.clip(inside / 9, 0, 1)
    base = hx('#0d0a26'); lit = hx('#3c3482'); fr, rv = [], []
    for i in range(8):
        t = i / 8 * 2 * np.pi; n = (noise(168, 168, 42, 500) * np.cos(t) + noise(168, 168, 42, 501) * np.sin(t)) * .5 + .5
        n2 = (noise(168, 168, 18, 502) * np.cos(t * 2) + noise(168, 168, 18, 503) * np.sin(t * 2)) * .5 + .5; n = n * .65 + n2 * .35
        o = np.zeros((168, 168, 4)); w = np.clip((n - .45) * 2.5, 0, 1)[..., None]; o[..., :3] = base * (1 - w) + lit * w
        o[..., :3] = o[..., :3] * (1 - det3[..., None]) + f3[..., :3] * det3[..., None]
        o[..., 3] = shape3 * edge * np.clip(.87 + .12 * (n - .5), 0, 1); o[..., 3] = np.maximum(o[..., 3], det3 * shape3)
        r_ = np.random.RandomState(600 + i); pts = r_.randint(6, 52, (5, 2)) * S; sp = np.zeros((168, 168), bool)
        for (px, py) in pts: sp[py:py + S, px:px + S] = True
        sp &= (shape3 > .5) & (edge > .8); o[sp, :3] = mix(lit, np.ones(3), .45); fr.append(o)
    nz = noise(168, 168, 20, 700) * .6 + noise(168, 168, 7, 701) * .4; nz = (nz - nz.min()) / (nz.max() - nz.min())
    for i in range(8):
        th = i / 7 * 1.1 - .05; o = fr[0].copy(); keep = np.clip((nz - th) / .1, 0, 1); o[..., 3] *= keep
        rimw = np.exp(-((nz - th) / .04) ** 2) * shape3 * (1 if i < 7 else 0); o[..., :3] = o[..., :3] * (1 - rimw[..., None]) + hx('#e8dcff') * rimw[..., None]
        o[..., 3] = np.maximum(o[..., 3], rimw * .9); rv.append(o)
    save(np.concatenate(fr, 1), f'{O6C}/tiles/fog_v3@3x.png'); save(np.concatenate(rv, 1), f'{O6C}/tiles/fog_reveal@3x.png')
    one = fr[0]; save(np.asarray(Image.fromarray(to8(one)).resize((56, 56), Image.BOX)).astype(float) / 255, f'{O6C}/tiles/fog_v3.png')
    return {'6c:fog_v3': dict(file='tiles/fog_v3@3x.png', x1='tiles/fog_v3.png', frames=8, frame3x=[168, 168], fps=4, loop=True, alpha='真 alpha（霧＝光／霧層）', note='原 fog 外形＋細節（雲紋）保留；霧緩慢流動；入面零星微光'),
            '6c:fog_reveal': dict(file='tiles/fog_reveal@3x.png', frames=8, frame3x=[168, 168], fps=16, loop=False, durationMs=500, note='揭開：noise 溶解＋淡紫光邊；播完換 tile＋tile_reveal_glow')}
def transition_v3():
    t = ld(f'{BT}/6c/fx/transition_in.png'); fr = []
    star_add = None
    for i in range(10):
        a = t[:, i * DW:(i + 1) * DW]; x3 = up3(a); al = x3[..., 3]
        sa = np.clip(gb(al, 5) * 1.25 - .12, 0, 1) if i < 9 else al
        edge = np.clip(sa * (1 - sa) * 4, 0, 1) if i < 9 else np.zeros_like(sa)
        c = x3[..., :3].copy(); fill = fill_under(x3, np.ones(al.shape, bool))[..., :3]; c = np.where(al[..., None] > .5, c, fill)
        c = c * (1 - edge[..., None] * .7) + hx('#b8a4ff') * edge[..., None] * .7
        o = np.zeros_like(x3); o[..., :3] = c; o[..., 3] = np.maximum(sa, edge * .85); fr.append(o)
    for i, o in enumerate(fr): save(o, f'{O6C}/transition/transition_in_v3_{i:02d}@3x.png')
    return {'6c:transition_v3': dict(files='transition/transition_in_v3_{00..09}@3x.png', frames=10, fps=8, durationMs=1250, frame3x=[D3W, D3H], alpha='真 alpha（過場層）',
                                     note='原 10 幀外形；夜幕邊羽化＋淡紫光邊；最後幀全黑夜＋月。enter 0→9、exit 9→0；最後 3 幀加月 flare（json flare）',
                                     flare=dict(frames=[7, 8, 9], pos=list(MOON_C), size='m', tint='#fff0c8', intensity=[.3, .5, .6]),
                                     petGlowSync='入夢第 0 幀開始 petGlow → 0（fadeOut 600ms easeInQuad）；出夢最後一幀 → 1（fadeIn 400ms＋pulse）')}
def cards_v3():
    J = json.load(open(f'{BT}/6c/dream6c.json'))['keys']; out = {}; ks = [k for k in J if k.startswith('6c:card_')]
    a0 = ld(f"{BT}/6c/{J[ks[0]]['1x']}"); op = a0[..., 3] > .5; inner = ND.binary_erosion(op, iterations=2)
    ring = op & ~inner; r3 = up3(ring.astype(float)); Y, X = np.mgrid[0:108, 0:84].astype(float)
    g = 1 + .4 * np.clip(1 - (X / 84 * .6 + Y / 108 * .4) * 1.6, -.6, 1)       # 金框左上高光、右下暗
    sweep = np.exp(-((X + Y * .5 - 30) / 6) ** 2) * .5                          # 固定 spec 斜光
    win = 1.1 - .26 * (X / 84 * .5 + Y / 108 * .5); ins = ND.distance_transform_edt(up3(inner.astype(float)) > .5) / S; aoi = 1 - .2 * np.clip(1 - ins / 3.5, 0, 1)
    for k in ks:
        a = ld(f"{BT}/6c/{J[k]['1x']}"); a[..., 3] = (a[..., 3] > .5).astype(float); x3 = up3(a); c = x3.copy()
        c[..., :3] = np.where(r3[..., None] > 0, np.clip(x3[..., :3] * g[..., None] + sweep[..., None] * hx('#fff6d8'), 0, 1), np.clip(x3[..., :3] * (win * aoi)[..., None], 0, 1))
        c[..., 3] = x3[..., 3]; n = k.split(':')[1]; save(c, f'{O6C}/cards/{n}_v3@3x.png')
        out[k + '_v3'] = dict(v3=f'cards/{n}_v3@3x.png', size3x=[84, 108], theme=J[k].get('theme'), glow=f"cards/card_glow_{J[k].get('theme') or 'back'}@3x.png")
    sh = []
    for i in range(8):
        p = -40 + i * 26; b = np.exp(-((X - Y * .45 - p) / 5) ** 2) * .75 + np.exp(-((X - Y * .45 - p + 12) / 2) ** 2) * .35
        o = np.zeros((108, 84, 4)); o[..., :3] = hx('#fffbe8'); o[..., 3] = np.clip(b, 0, 1) * up3(op.astype(float)); sh.append(o)
    save(np.concatenate(sh, 1), f'{O6C}/cards/card_shine@3x.png')
    for th, col in (('forest', '#a8ff9a'), ('lake', '#9ad8ff'), ('toy', '#ffc890'), ('star', '#ffe890'), ('back', '#c8b8ff')):
        gl = np.zeros((168, 144, 4)); gl[..., :3] = hx(col); Yg, Xg = np.mgrid[0:168, 0:144].astype(float)
        dd = np.maximum(np.abs(Xg - 71.5) - 36, 0) ** 2 + np.maximum(np.abs(Yg - 83.5) - 48, 0) ** 2; gl[..., 3] = np.exp(-dd / 260) * .85 * (np.maximum(np.abs(Xg - 71.5) - 36, np.abs(Yg - 83.5) - 48) > -3)
        save(gl, f'{O6C}/cards/card_glow_{th}@3x.png')
    out['6c:card_shine'] = dict(file='cards/card_shine@3x.png', frames=8, frame3x=[84, 108], fps=16, blend='lighter', note='新卡／翻卡時掃一次光；mask 已跟卡外形')
    out['6c:card_glow'] = dict(files='cards/card_glow_<forest|lake|toy|star|back>@3x.png', size3x=[144, 168], offset3x=[-30, -30], blend='lighter', note='卡外圍光暈（卡中心對中）')
    return out
def dream_json(bgj, tj, fj, trj, cj):
    J6 = json.load(open(f'{BT}/6c/dream6c.json'))
    pets = {pid: dict(petglow=petglow_ref(pid), petLight=0, glow='off', moonRim=dict(color='#c8c0ff', intensity=.5, note='場景月光 rim（唔係寵物光）'), contactShadow=dict(alpha=.4, rx=.3, ry=.07))
            for pid in J6['pets']}
    st = LAY['states']
    o = dict(version=3, batch='第 6 批 6c 夢遊 V3-A', source=dict(dir='art/breakthrough/6c', commit=SRC_COMMIT['6c'], note='原 1x／@3x key、尺寸、dream6c.json 冇郁；V3 喺 v3/'),
             screen3x=[D3W, D3H], grid=dict(cols=3, rows=5, x0=11, y0=64, gap=2, tile=56, tile3x=168, note='art 座標同 dream6c.json#grid 一致；@3x＝×3'),
             dreamBg=bgj, tiles=tj, fog=fj, transition=trj, cards=cj,
             petGlow=dict(source='ui/kit_hd2d_v3/layout_hd2d_v3.json#petGlow', dreamEnter=st.get('dreamEnter'), dreaming=st.get('dreaming'), rule='夢遊中寵物光＝0（呢度所有 pets.petLight＝0）；月、星、菇燈等場景光照開；出夢先 fadeIn 400ms＋pulse'),
             pets=pets, petStack=['contactShadow', 'dream_walk（×DREAM.amb）', 'moonRim', 'nightcap（json xy）'], keep='dream_walk／nightcap／frag／icon 原樣用（V3 只加光）')
    jdump(o, f'{O6C}/dream6c_v3.json')
def build_dream():
    bgj = dream_bg_v3(); print('bg ok'); tj = tiles_v3(); print('tiles ok'); fj = fog_v3(); print('fog ok'); trj = transition_v3(); print('trans ok'); cj = cards_v3(); print('cards ok')
    dream_json(bgj, tj, fj, trj, cj)
# ---- 預覽用合成（夢遊地圖：bg＋3×5 格，部分揭開、其餘霧；寵物戴睡帽、冇寵物光）
def compose_dream_map(seed=1, pid='A3', fog_fr=0, pet_frame=0):
    img=np.asarray(Image.open(f'{O6C}/dream_bg/dream_bg_v3@3x.png')).astype(float)/255
    themes=['forest','lake','toy','star']; rnd=np.random.RandomState(seed)
    T={t:ld(f'{O6C}/tiles/tile_{t}_v3@3x.png') for t in themes}; G={t:ld(f'{O6C}/tiles/tile_{t}_glow@3x.png') for t in themes}
    fog=ld(f'{O6C}/tiles/fog_v3@3x.png'); ring=ld(f'{O6C}/tiles/tile_reveal_glow@3x.png')
    rev={(0,0),(1,0),(1,1),(2,1),(1,2),(0,3)}; th='forest'
    pet=None
    for r in range(5):
        for c in range(3):
            x=(11+c*58)*3; y=(64+r*58)*3
            if (c,r) in rev:
                v=rnd.randint(4); t=themes[(r+c)%4]; over(img,T[t][:,v*168:(v+1)*168],x,y); addc(img,G[t][:,v*168:(v+1)*168],x+84,y+84,.85); addc(img,ring,x+84,y+84,.35)
                if (c,r)==(1,2): pet=(x+84,y+130)
            else:
                f=(c*3+r+fog_fr)%8; fo=fog[:,f*168:(f+1)*168]; img[y:y+168,x:x+168]=img[y:y+168,x:x+168]*(1-fo[...,3:])+fo[...,:3]*fo[...,3:]
    J=json.load(open(f'{BT}/6c/dream6c.json')); P=J['pets'][pid]; clip=ld(f"{BT}/6c/{P['3x']}"); fw=P['frameSize'][0]*3
    fr=clip[:, pet_frame*fw:(pet_frame+1)*fw].copy(); fr[...,:3]*=hx(DREAM['amb']); fr=up3(rim(fr[::3,::3],'#c8c0ff',.5))
    yy,xx=np.mgrid[0:img.shape[0],0:img.shape[1]]; sh=np.exp(-(((xx-pet[0])/(fw*.3))**2+((yy-pet[1]-2)/8)**2)**2)*.4; img*=1-sh[...,None]
    ox,oy=pet[0]-P['pivot'][0]*3, pet[1]-P['pivot'][1]*3; over(img,fr,ox,oy)
    nc=P['nightcap']; cap=ld(f"{BT}/6c/nightcap/nightcap_{nc['size']}@3x.png"); over(img,cap,ox+nc['xy'][pet_frame][0]*3,oy+nc['xy'][pet_frame][1]*3)
    return Image.fromarray(to8(np.clip(img,0,1)),'RGB')
if __name__ == '__main__':
    a = sys.argv[1:] or ['walk', 'dream']
    if 'walk' in a: build_walk()
    if 'dream' in a: build_dream()
