#!/usr/bin/env python3
"""《微光小圃》HD-2D 正式場景 H1–H4（直向 195×422 美術格；層 223×446）。
純 Python（Pillow／numpy）程式逐像素繪製，無 AI，全原創。
用法：python3 build_hd2d_scenes.py [layers|H1|H2|H3|H4|rain|particles|crossfade|all]
- 共用索引圖：scenes/hd2d/index/{sky,far,mid,fore}_index.png（L 模式，值＝materials.json 嘅 index；0＝透明）
- 每款：scenes/hd2d/H#/  raw/（色盤鎖定 ≤64 色、alpha 0/255）、sky/far/mid/fore.png（已預烘 LUT＋DoF）、
        lightmap.png、light_add.png、emissive.png、emissive_blur.png、vignette.png、grade.json、lut.png、palette.json、mockup_<form>(_2x).png
引擎係 canvas2D（冇 shader）：LUT／飽和／對比／DoF 全部預烘入場景層；寵物唔過 LUT。
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'scenes', 'hd2d')
SPR = os.path.join(ROOT, 'sprites', 'tuanrong', 'motion')
AW, AH = 195, 422            # 美術格
MX, MY = 14, 12              # 層邊距（視差）
LW, LH = AW + 2*MX, AH + 2*MY  # 223×446
FOOT = (97, 292)             # 團絨腳底（art）
FORMS = {'sprout': 32, 'radiant': 64, 'soft': 64}
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]])/16.0 + 1/32

def hx(h): h = h.lstrip('#'); return np.array([int(h[i:i+2], 16) for i in (0, 2, 4)], float)/255
def tohex(c): c = np.clip(np.round(np.asarray(c, float)*255), 0, 255).astype(int); return '#%02x%02x%02x' % tuple(c)
def mix(a, b, t): return a*(1-t) + b*t
def L2A(x, y): return x - MX, y - MY
def A(x, y): return x + MX, y + MY          # art → layer 座標

# ======================= 材質表（共用 index）=======================
MATS = [  # name, levels, base hex, layer-hint
 ('SKY', 7, None), ('CLOUD', 2, '#FFFFFF'), ('SUN', 1, '#FFF2C8'), ('MOON', 1, '#F4F0DC'), ('STAR', 1, '#FFFFFF'),
 ('HILL_FAR', 2, '#9CB8AA'), ('HILL_NEAR', 2, '#7EA67A'), ('TREE_FAR', 2, '#6A9A66'), ('FAR_HOUSE', 1, '#B8907A'), ('FAR_WIN', 1, '#C8D8E0'),
 ('TRUNK', 2, '#8C6448'), ('LEAF', 3, '#68AA56'), ('WOOD', 3, '#BC8A5C'), ('WALL', 2, '#DDB88E'), ('ROOF', 2, '#BC5A4C'),
 ('WIN', 2, '#9CCAE0'), ('METAL', 2, '#5C5A6C'), ('LAMP', 1, '#D8E4E4'), ('LANTERN', 2, '#E8845A'),
 ('GRASS', 3, '#86C26A'), ('MOSS', 2, '#9CCC74'), ('SOIL', 2, '#7C543A'), ('SPROUT', 2, '#7CC260'), ('POT', 2, '#C8744E'),
 ('FLOWER_P', 1, '#F59CB2'), ('FLOWER_Y', 1, '#FFD45C'), ('STONE', 2, '#C8C0B0'), ('CAN', 2, '#5CB8B0'), ('MUSH', 2, '#F0956A'),
 ('MUSH_ST', 1, '#F0E0C0'), ('FLEAF', 2, '#4C9050'), ('FFLOWER', 1, '#F4A2C0'), ('FGRASS', 2, '#5A9C4C')]
IDX = {}; k = 1
for n, lv, _ in MATS:
    IDX[n] = list(range(k, k+lv)); k += lv
NIDX = k - 1
assert NIDX <= 64, NIDX
EMISSIVE_MATS = {'SUN', 'MOON', 'STAR', 'FAR_WIN', 'WIN', 'LAMP', 'LANTERN'}

class Lay:
    def __init__(s):
        s.m = np.zeros((LH, LW), np.uint8)
        Y, X = np.mgrid[0:LH, 0:LW].astype(float); s.X, s.Y = X+0.5-MX, Y+0.5-MY   # art 座標
        s.bay = BAYER[np.arange(LH)[:, None] % 4, np.arange(LW)[None, :] % 4]
    def put(s, mask, mat, f=0.5, dither=0.35):
        ids = IDX[mat]; n = len(ids)
        f = f[mask] if isinstance(f, np.ndarray) else np.full(mask.sum(), f)
        q = np.clip(np.floor(f*n + (s.bay[mask]-0.5)*dither*2), 0, n-1).astype(int)
        s.m[mask] = np.array(ids, np.uint8)[q]; return mask
    def ell(s, mat, cx, cy, rx, ry, f=None, L=(-0.55, -0.7, 0.45), dither=0.35):
        dx, dy = (s.X-cx)/rx, (s.Y-cy)/ry; m = dx*dx+dy*dy <= 1
        if f is None: f = 0.5+0.5*lightv(np.clip(dx, -1, 1), np.clip(dy, -1, 1), L)
        return s.put(m, mat, f, dither)
    def mask_poly(s, pts):
        im = Image.new('L', (LW, LH), 0); ImageDraw.Draw(im).polygon([A(*p) for p in pts], fill=1); return np.array(im).astype(bool)
    def poly(s, mat, pts, f=0.5, dither=0.35): return s.put(s.mask_poly(pts), mat, f, dither)
    def rect(s, mat, x0, y0, x1, y1, f=0.5, dither=0.35):
        m = (s.X >= x0) & (s.X < x1) & (s.Y >= y0) & (s.Y < y1); return s.put(m, mat, f, dither)
    def line(s, mat, pts, w, f=0.5):
        im = Image.new('L', (LW, LH), 0); ImageDraw.Draw(im).line([A(*p) for p in pts], fill=1, width=w)
        return s.put(np.array(im).astype(bool), mat, f, 0)

def lightv(dx, dy, L):
    L = np.array(L, float); L /= np.linalg.norm(L)
    nz = np.sqrt(np.clip(1-dx*dx-dy*dy, 0, 1)); return dx*L[0]+dy*L[1]+nz*L[2]

def vnoise(cell, seed, ang=0.0, stretch=1.0):
    g = np.random.default_rng(seed).random((96, 96))
    Y, X = np.mgrid[0:LH, 0:LW].astype(float); ca, sa = math.cos(ang), math.sin(ang)
    u = (X*ca+Y*sa)/(cell*stretch)+200; v = (-X*sa+Y*ca)/cell+200
    i0, j0 = np.floor(u).astype(int), np.floor(v).astype(int); fu, fv = u-i0, v-j0
    fu = fu*fu*(3-2*fu); fv = fv*fv*(3-2*fv); G = lambda i, j: g[j % 96, i % 96]
    return (G(i0, j0)*(1-fu)+G(i0+1, j0)*fu)*(1-fv) + (G(i0, j0+1)*(1-fu)+G(i0+1, j0+1)*fu)*fv

# ======================= 佈局（art 座標）=======================
HORIZON = 250
LAYOUT = {
 'tree': {'trunk': [2, 16, 58, 262], 'canopy_center': [22, 74]},
 'cottage': {'wall': [150, 168, 209, 262], 'roof_peak': [181, 132], 'window': [157, 190, 175, 210], 'door': [183, 214, 199, 262]},
 'fence': {'x': [-14, 150], 'y': [232, 260]},
 'lanternString': {'from': [36, 104], 'to': [156, 150], 'sag': 22, 'lanterns': 5},
 'lampPost': {'base': [24, 306], 'head': [24, 246]},
 'bed': [18, 262, 82, 278],
 'pots': {'pot_L': [16, 336], 'pot_R': [178, 326], 'pot_S': [146, 306]},
 'mushrooms': [168, 304], 'can': [58, 318],
 'stones': [[97, 326, 11, 3.5], [82, 344, 9, 3], [106, 361, 10, 3.2]],
}
def lantern_pos():
    (x0, y0), (x1, y1) = LAYOUT['lanternString']['from'], LAYOUT['lanternString']['to']; sag = LAYOUT['lanternString']['sag']
    n = LAYOUT['lanternString']['lanterns']; out = []
    for i in range(n):
        t = (i+0.5)/n; out.append((round(x0+(x1-x0)*t), round(y0+(y1-y0)*t+sag*math.sin(math.pi*t))+4))
    return out

def build_index(variant_feats):
    """回傳 dict(sky,far,mid,fore) Lay；variant_feats 控制天空特徵（按款微調）。"""
    rng = np.random.default_rng(5)
    sky, far, mid, fore = Lay(), Lay(), Lay(), Lay()
    X, Y = sky.X, sky.Y
    # ---- sky（全不透明）
    t = np.clip((Y+MY)/(HORIZON+MY+6), 0, 1)
    sky.put(np.ones_like(sky.m, bool), 'SKY', t**0.9, dither=0.5)
    vf = variant_feats
    if vf.get('stars'):
        st = (rng.random(sky.m.shape) > 0.988) & (Y < 200)
        sky.put(st, 'STAR', 1.0, 0)
    if vf.get('moon'):
        mx, my = vf['moon']
        m = ((X-mx)**2+(Y-my)**2 <= 9.5**2) & ~((X-mx-4.5)**2+(Y-my+3)**2 <= 8.5**2); sky.put(m, 'MOON', 1, 0)
    if vf.get('sun'):
        sx, sy, R = vf['sun']; sky.put((X-sx)**2+(Y-sy)**2 <= R*R, 'SUN', 1, 0)
    for (cx, cy, s) in vf.get('clouds', []):
        for (ox, oy, rx, ry) in [(-12, 2, 10, 5), (0, -3, 12, 8), (13, 1, 10, 6), (3, 4, 18, 4)]:
            sky.ell('CLOUD', cx+ox*s, cy+oy*s, rx*s, ry*s, L=vf.get('cloudL', (-0.3, -0.9, 0.3)), dither=0)
    # ---- far（地平線以下不透明）
    y1 = 214 + 7*np.sin(X/31+0.6) + 3*np.sin(X/13)
    far.put(Y >= y1, 'HILL_FAR', np.clip(0.55+0.25*np.sin(X/24)-0.004*(Y-y1), 0, 1))
    fh = LAYOUT
    # 遠方小屋
    far.rect('FAR_HOUSE', 130, 222, 146, 234, 0.5); far.poly('FAR_HOUSE', [(128, 223), (138, 215), (148, 223)], 0.5)
    far.rect('FAR_WIN', 134, 226, 136, 229, 1); far.rect('FAR_WIN', 140, 226, 142, 229, 1)
    y2 = 232 + 5*np.sin(X/22+2) + 2*np.sin(X/9)
    for x0 in range(-14, 212, 8):
        yy = 233 + 5*math.sin(x0/22+2) + 2*math.sin(x0/9); r = 5 + 3*abs(math.sin(x0*1.7))
        far.ell('TREE_FAR', x0, yy-2, r, r*1.25, L=(-0.6, -0.6, 0.4))
    far.put(Y >= y2, 'HILL_NEAR', np.clip(0.5+0.25*np.sin(X/17+1), 0, 1))
    # ---- mid（遊玩層）
    nz = vnoise(5, 1); nz2 = vnoise(2.2, 2, ang=0.3, stretch=3)
    gm = Y >= 256
    gf = np.clip(0.55 + 0.25*(nz-0.5) + 0.3*(nz2-0.5) - 0.0016*(Y-256), 0, 1)
    mid.put(gm, 'GRASS', gf)
    # 籬笆＋灌木
    for x0 in range(-12, 150, 14):
        mid.poly('WOOD', [(x0, 262), (x0, 236), (x0+2, 232), (x0+4, 236), (x0+4, 262)], 0.45)
        mid.rect('WOOD', x0, 236, x0+1, 262, 0.9, 0)
    for yy in (240, 252):
        mid.rect('WOOD', -14, yy, 150, yy+3, 0.55, 0); mid.rect('WOOD', -14, yy, 150, yy+1, 0.95, 0)
    for x0 in range(-8, 152, 15):
        r = 7 + 3*abs(math.sin(x0*0.7)); mid.ell('LEAF', x0, 259, r*1.4, r*0.9, L=(-0.5, -0.8, 0.4))
    # 小屋（右）
    wx0, wy0, wx1, wy1 = LAYOUT['cottage']['wall']
    mid.rect('WALL', wx0, wy0, wx1, wy1, 0.75 - 0.6*((((Y-wy0).astype(int)) % 8) == 0), 0)
    mid.rect('WALL', wx0, wy0, wx0+3, wy1, 0.15, 0)
    px_, py_ = LAYOUT['cottage']['roof_peak']
    mid.poly('ROOF', [(wx0-8, wy0+3), (px_, py_), (wx1+16, wy0+3)], 0.35)
    mid.poly('ROOF', [(wx0-8, wy0+3), (px_, py_), (px_, py_+4), (wx0-2, wy0+4)], 0.9)
    mid.rect('WOOD', wx0-8, wy0+1, wx1+16, wy0+4, 0.2, 0)
    a, b, c, d = LAYOUT['cottage']['window']
    mid.rect('WOOD', a-2, b-2, c+2, d+2, 0.7, 0)
    mid.rect('WIN', a, b, c, d, 0.25 + 0.75*(((X-a)+(d-Y)) > 18), 0)
    mid.rect('WOOD', (a+c)//2, b, (a+c)//2+1, d, 0.4, 0); mid.rect('WOOD', a, (b+d)//2, c, (b+d)//2+1, 0.4, 0)
    a, b, c, d = LAYOUT['cottage']['door']
    mid.rect('WOOD', a, b, c, d, 0.1, 0); mid.rect('WOOD', a, b, a+1, d, 0.5, 0); mid.rect('METAL', a+3, 240, a+5, 242, 0.9, 0)
    # 大樹（左）
    t0, t1, ty0, ty1 = LAYOUT['tree']['trunk']
    mid.rect('TRUNK', t0, ty0, t1, ty1, 0.3 + 0.6*(X < t0+5) + 0.05*np.sin(Y/3))
    mid.poly('TRUNK', [(t0-6, ty1), (t0, ty1-14), (t1, ty1-14), (t1+7, ty1)], 0.3)
    cx, cy = LAYOUT['tree']['canopy_center']
    for (ox, oy, r) in [(-10, -6, 30), (22, -2, 24), (6, -30, 26), (36, -22, 16), (-14, 22, 20), (16, 22, 18), (44, 4, 14)]:
        mid.ell('LEAF', cx+ox, cy+oy, r, r*0.9, L=(-0.6, -0.75, 0.35), dither=0.45)
    for (ox, oy, r) in [(-4, -34, 9), (26, -26, 8), (10, -12, 8), (40, -4, 6), (-18, -10, 8), (0, 14, 7)]:
        m = ((X-cx-ox)**2+(Y-cy-oy)**2 <= r*r) & np.isin(mid.m, IDX['LEAF'])
        mid.put(m, 'LEAF', 0.95, 0.3)
    # 串燈
    (x0, y0), (x1, y1) = LAYOUT['lanternString']['from'], LAYOUT['lanternString']['to']; sag = LAYOUT['lanternString']['sag']
    pts = [(x0+(x1-x0)*t, y0+(y1-y0)*t+sag*math.sin(math.pi*t)) for t in np.linspace(0, 1, 120)]
    mid.line('METAL', pts, 1, 0.2)
    for (lx, ly) in lantern_pos():
        mid.rect('METAL', lx-1, ly-4, lx+1, ly-2, 0.2, 0)
        mid.ell('LANTERN', lx, ly+1, 2.6, 3.4, L=(-0.6, -0.5, 0.6), dither=0)
        mid.rect('METAL', lx-1, ly+4, lx+2, ly+5, 0.2, 0)
    # 地面：寵物舞台（苔窩＋邊石）
    gx, gy = FOOT[0], FOOT[1]+4
    d = ((X-gx)/80)**2 + ((Y-gy)/21)**2
    mid.put(d <= 1, 'GRASS', np.clip(gf+0.18, 0, 1))
    for i in range(30):
        an = i/30*2*math.pi; sx, sy = gx+math.cos(an)*81, gy+3+math.sin(an)*22
        if sy < 280: continue
        mid.ell('STONE', sx, sy, 2.2, 1.4, L=(-0.3, -0.9, 0.3), dither=0)
    mid.ell('MOSS', gx, gy, 30, 8, f=np.clip(0.75-0.5*np.hypot((X-gx)/30, (Y-gy)/8)+0.15*(nz-0.5), 0, 1), dither=0.5)
    # 草叢點綴
    tuft = (rng.random(mid.m.shape) > 0.972) & gm & (Y > 262)
    for (yy, xx) in zip(*np.where(tuft)):
        h = 2 + int(rng.random()*3); ax, ay = xx-MX, yy-MY
        mid.rect('GRASS', ax, ay-h, ax+1, ay+1, 0.05, 0); mid.rect('GRASS', ax+1, ay-h+1, ax+2, ay-h+2, 0.98, 0)
    # 菜畦（後排）
    b0, b1, b2, b3 = LAYOUT['bed']
    mid.rect('SOIL', b0, b1, b2, b3-5, 0.35 + 0.5*(((Y.astype(int)-b1) % 4) == 0), 0)
    mid.rect('WOOD', b0-2, b3-6, b2+2, b3, 0.4, 0); mid.rect('WOOD', b0-2, b3-6, b2+2, b3-5, 0.95, 0)
    for i, xx in enumerate(range(b0+6, b2-2, 11)):
        if i % 2 == 0:
            for (ox, oy, rr) in [(-3, -1, 3.2), (3, -1, 3.2), (0, -4, 3.6)]: mid.ell('SPROUT', xx+ox, b1+3+oy, rr, rr*0.8, L=(-0.5, -0.8, 0.4), dither=0)
        else:
            mid.line('SPROUT', [(xx, b1+4), (xx, b1-8)], 1, 0.3)
            for (ox, oy) in [(-2, 0), (2, 0), (0, -2), (0, 2)]: mid.ell('FLOWER_P', xx+ox, b1-9+oy, 1.9, 1.9, f=1.0, dither=0)
            mid.ell('FLOWER_Y', xx, b1-9, 1.1, 1.1, f=1, dither=0)
    # 燈柱（左）
    lbx, lby = LAYOUT['lampPost']['base']; lhx, lhy = LAYOUT['lampPost']['head']
    mid.rect('METAL', lbx-1, lhy+8, lbx+2, lby, 0.3 + 0.6*(X < lbx))
    mid.rect('METAL', lbx-4, lby-3, lbx+5, lby, 0.25, 0)
    mid.poly('METAL', [(lhx-6, lhy-5), (lhx+7, lhy-5), (lhx+4, lhy-9), (lhx-3, lhy-9)], 0.6)
    mid.rect('LAMP', lhx-4, lhy-5, lhx+5, lhy+6, 1, 0)
    mid.rect('METAL', lhx-5, lhy+6, lhx+6, lhy+8, 0.3, 0); mid.rect('METAL', lhx, lhy-5, lhx+1, lhy+6, 0.2, 0)
    # 花盆
    for nm, (px, py) in LAYOUT['pots'].items():
        s = 0.7 if nm == 'pot_S' else 1.0
        w0, w1, h = 9*s, 7*s, 11*s
        mid.poly('POT', [(px-w0, py-h), (px+w0, py-h), (px+w1, py), (px-w1, py)], 0.35 + 0.6*(X < px-1))
        mid.rect('POT', px-w0-1, py-h-2, px+w0+1, py-h+1, 0.9, 0)
        mid.rect('SOIL', px-w0+1, py-h-3, px+w0-1, py-h-1, 0.2, 0)
        fl = 'FLOWER_Y' if nm == 'pot_R' else 'FLOWER_P'
        for k_, (ox, oy) in enumerate([(-4*s, -h-8*s), (3*s, -h-12*s), (6*s, -h-6*s)]):
            mid.line('SPROUT', [(px+ox*0.4, py-h-2), (px+ox, py+oy)], 1, 0.2)
            mid.ell('SPROUT', px+ox-2, py+oy+3, 2.2*s, 1.3, f=0.8, dither=0)
            for (qx, qy) in [(-1.6, 0), (1.6, 0), (0, -1.6), (0, 1.6)]: mid.ell(fl, px+ox+qx*s, py+oy+qy*s, 1.6*s+0.3, 1.6*s+0.3, f=1, dither=0)
            mid.rect('FLOWER_Y' if fl == 'FLOWER_P' else 'FLOWER_P', px+ox, py+oy, px+ox+1, py+oy+1, 1, 0)
    # 蘑菇
    mx0, my0 = LAYOUT['mushrooms']
    for (dx, dy, r) in [(-8, 0, 3.6), (0, 2, 5.2), (9, -1, 3), (4, -6, 2.6)]:
        mid.rect('MUSH_ST', mx0+dx-1, my0+dy-r+2, mx0+dx+2, my0+dy+1, 1, 0)
        mid.poly('MUSH', [(mx0+dx-r-1, my0+dy-r+2), (mx0+dx-r*0.6, my0+dy-r*1.7), (mx0+dx+r*0.6, my0+dy-r*1.7), (mx0+dx+r+1, my0+dy-r+2)], 0.3)
        mid.ell('MUSH', mx0+dx-r*0.3, my0+dy-r*1.3, r*0.45, r*0.3, f=0.95, dither=0)
    # 花灑
    cx_, cy_ = LAYOUT['can']
    mid.ell('CAN', cx_, cy_-5, 7, 5.5, L=(-0.6, -0.6, 0.5)); mid.rect('CAN', cx_-6, cy_-6, cx_+7, cy_, 0.4, 0)
    mid.ell('CAN', cx_, cy_-9.5, 6, 1.6, f=0.95, dither=0)
    mid.line('CAN', [(cx_+6, cy_-3), (cx_+14, cy_-10)], 2, 0.5); mid.ell('CAN', cx_+15, cy_-11, 2, 2, f=0.9, dither=0)
    mid.line('METAL', [(cx_-4, cy_-10), (cx_, cy_-15), (cx_+4, cy_-10)], 1, 0.4)
    # 踏腳石
    for (sx, sy, rx, ry) in LAYOUT['stones']:
        mid.ell('STONE', sx, sy, rx, ry, L=(-0.3, -0.9, 0.35), dither=0.3)
        mid.ell('STONE', sx, sy+ry*0.55, rx*0.95, ry*0.5, f=0.05, dither=0)
        mid.ell('STONE', sx, sy-ry*0.15, rx*0.9, ry*0.75, L=(-0.3, -0.9, 0.35), dither=0.3)
    # 下半地面小花
    for i in range(22):
        x = 8 + (i*37) % 180 + int(rng.random()*6); y = 330 + int(rng.random()*48)
        if abs(x-97) < 16 and y < 370: continue
        mid.rect('FGRASS', x, y, x+1, y+3, 0.1, 0)
        fl = 'FLOWER_Y' if i % 3 else 'FLOWER_P'
        mid.rect(fl, x-1, y-1, x+2, y, 1, 0); mid.rect(fl, x, y-2, x+1, y+1, 1, 0)
    # ---- fore（遮擋層，只喺邊緣，唔遮寵物活動帶）
    for (bx, by, tx, ty, wdt) in [(-16, 452, 30, 372, 18), (-16, 440, 52, 404, 14), (214, 446, 168, 380, 16), (214, 420, 188, 356, 11)]:
        ang = math.atan2(ty-by, tx-bx); nx_, ny_ = -math.sin(ang), math.cos(ang); P = []
        for tt in np.linspace(0, 1, 24): P.append((bx+(tx-bx)*tt + nx_*wdt*math.sin(math.pi*tt), by+(ty-by)*tt + ny_*wdt*math.sin(math.pi*tt)))
        for tt in np.linspace(1, 0, 24): P.append((bx+(tx-bx)*tt - nx_*wdt*math.sin(math.pi*tt)*0.7, by+(ty-by)*tt - ny_*wdt*math.sin(math.pi*tt)*0.7))
        fore.poly('FLEAF', P, 0.2 + 0.7*((X-bx)*nx_+(Y-by)*ny_ > 0), 0)
        fore.line('FLEAF', [(bx, by), (tx, ty)], 1, 0.95)
    for (tx, ty, r) in [(176, 398, 7), (190, 412, 6)]:
        fore.line('FGRASS', [(tx+4, 450), (tx, ty)], 2, 0.2)
        for k_ in range(6):
            an = k_*math.pi/3; fore.ell('FFLOWER', tx+math.cos(an)*r*0.6, ty+math.sin(an)*r*0.6, r*0.55, r*0.55, dither=0.3)
        fore.ell('FLOWER_Y', tx, ty, r*0.35, r*0.35, f=1, dither=0)
    for x0 in range(-14, 212, 4):
        h = 10 + 9*abs(math.sin(x0*0.37)) + (0 if 40 < x0 < 150 else 14)
        lean = 3*math.sin(x0*0.9)
        fore.poly('FGRASS', [(x0-2, 435), (x0+lean, 435-h), (x0+3, 435)], 0.2 + 0.6*abs(math.sin(x0)), 0)
    fore.rect('FGRASS', -14, 432, 210, 435, 0.1, 0)
    # 頂部垂葉（左上，HUD 後面）
    for i, (hx_, hl) in enumerate([(-6, 40), (6, 54), (20, 34), (34, 46), (50, 26)]):
        for j in range(hl):
            yy = -12 + j; xx = hx_ + 4*math.sin(j/9+i)
            w = 3 if j % 7 < 4 else 2
            fore.rect('FLEAF', xx-w, yy, xx+w, yy+1, 0.3 + 0.6*(j % 7 < 2), 0)
    return dict(sky=sky, far=far, mid=mid, fore=fore)

# ======================= 每款參數 =======================
VAR = {
 'H1': dict(name='晨光暖調', hours='06–10',
    sky=['#86BCEA', '#BFDCEE', '#F4E6CC', '#FFDDB0'], light='#FFE6B0', shadow='#8A6A9A', lo=0.55, hi=1.0, lift=0.10,
    feats=dict(sun=(38, 112, 9), clouds=[(120, 92, 1.0), (60, 150, 0.8), (168, 60, 0.7)]),
    pal_over={'LAMP': '#DCE2DA', 'LANTERN': ['#C07A5A', '#E09A72'], 'WIN': ['#9CC4D8', '#E8F4F4'], 'FAR_WIN': '#C8D4D8', 'SUN': '#FFF4D0', 'CLOUD': ['#F6DCC4', '#FFF8EA']},
    emissive={'SUN': 1.0},
    grade=dict(ambientTint='#fff4e6', petTint='#fff8f0', saturation=1.06, contrast=1.04,
        bloom=dict(threshold=0.78, intensity=0.45), fog=dict(color='#ffe8c8', density=0.05),
        dof=dict(far=1.6, mid=1.0, fore=3.0), vignette=0.22,
        rim=dict(color='#ffe2a8', intensity=0.55, dir=[-0.7, -0.7]), bulbGlowTint='#ffe9a0',
        particles=dict(type='mote', rate=0.8, color='#fff2c0'), rain=dict(saturation=0.85, contrast=0.92, tint='#dfe8f0')),
    vig='#5a3a30', lm=dict(base='#fff6ea', shadow='#b49aa8', sky_amb=1.0), shafts=0.22),
 'H2': dict(name='黃昏電影感', hours='16–19',
    sky=['#2E2A68', '#7E4C94', '#E8786C', '#FFC070'], light='#FFB070', shadow='#4A3478', lo=0.38, hi=0.92, lift=0.04,
    feats=dict(sun=(112, 226, 13), clouds=[(140, 120, 1.0), (50, 168, 0.9), (110, 70, 0.7)], cloudL=(0.2, 0.9, 0.35)),
    pal_over={'LAMP': '#FFE6A8', 'LANTERN': ['#F08850', '#FFD08A'], 'WIN': ['#E0A070', '#FFD490'], 'FAR_WIN': '#FFD08A', 'SUN': '#FFF0B8',
              'CLOUD': ['#B0607E', '#FFB27A']},
    emissive={'SUN': 1.0, 'LANTERN': 0.8, 'LAMP': 0.6, 'FAR_WIN': 0.8, 'WIN': 0.35},
    grade=dict(ambientTint='#ffd8c4', petTint='#f4dcd8', saturation=1.12, contrast=1.10,
        bloom=dict(threshold=0.66, intensity=0.75), fog=dict(color='#9a5a8a', density=0.07),
        dof=dict(far=2.6, mid=1.6, fore=4.5), vignette=0.48,
        rim=dict(color='#ffc070', intensity=0.85, dir=[0.2, -0.98]), bulbGlowTint='#ffb860',
        particles=dict(type='gold', rate=0.6, color='#ffd27a'), rain=dict(saturation=0.8, contrast=0.95, tint='#c8b0c8')),
    vig='#1a0e28', lm=dict(base='#ffe2cc', shadow='#6e5a8e', sky_amb=1.0), shafts=0.0),
 'H3': dict(name='清新冷調', hours='10–16（晴／雨後）',
    sky=['#8ED2F0', '#BFE6F2', '#E4F6F4', '#F4FCF6'], light='#F2FFF8', shadow='#6AA6B8', lo=0.62, hi=1.0, lift=0.16,
    feats=dict(clouds=[(130, 84, 1.1), (44, 128, 0.9), (172, 168, 0.7), (80, 50, 0.6)]),
    pal_over={'LAMP': '#E0ECEC', 'LANTERN': ['#D88A6A', '#F0B090'], 'WIN': ['#8EC8E0', '#F0FCFF'], 'FAR_WIN': '#D0E4EC', 'CLOUD': ['#D6ECF2', '#FFFFFF']},
    emissive={},
    grade=dict(ambientTint='#f2fbff', petTint='#ecdcc8', saturation=0.94, contrast=1.08,
        bloom=dict(threshold=0.9, intensity=0.2), fog=dict(color='#e4f6f8', density=0.04),
        dof=dict(far=1.2, mid=0.6, fore=2.2), vignette=0.10,
        rim=dict(color='#5a6a8a', intensity=0.6, dir=[0.6, 0.8]), bulbGlowTint='#fff2b0',
        particles=dict(type='petal', rate=0.5, color='#ffe0ec'), rain=dict(saturation=0.72, contrast=0.9, tint='#c8d8e4')),
    vig='#4a6a78', lm=dict(base='#ffffff', shadow='#a8c4cc', sky_amb=1.0), shafts=0.0),
 'H4': dict(name='夜燈', hours='19–06',
    sky=['#080C24', '#141C48', '#262E62', '#3A3A70'], light='#B8C0F0', shadow='#3A4890', lo=0.22, hi=0.62, lift=0.0,
    feats=dict(stars=True, moon=(150, 76), clouds=[(70, 140, 0.9), (170, 180, 0.7)], cloudL=(-0.2, -0.9, 0.3)),
    pal_over={'LAMP': '#FFF0B8', 'LANTERN': ['#FF9A50', '#FFE0A0'], 'WIN': ['#FFC870', '#FFEDB0'], 'FAR_WIN': '#FFD890',
              'MOON': '#F4F0D8', 'STAR': '#FFF8E0', 'CLOUD': ['#2A3062', '#4A4C80']},
    emissive={'MOON': 0.9, 'STAR': 0.5, 'LAMP': 1.0, 'LANTERN': 1.0, 'WIN': 0.9, 'FAR_WIN': 1.0},
    grade=dict(ambientTint='#c8ccf0', petTint='#fff2e4', saturation=1.05, contrast=1.06,
        bloom=dict(threshold=0.6, intensity=1.0), fog=dict(color='#1a2050', density=0.06),
        dof=dict(far=2.0, mid=1.2, fore=3.5), vignette=0.40,
        rim=dict(color='#ffd890', intensity=0.8, dir=[-0.85, -0.5]), bulbGlowTint='#ffd070',
        particles=dict(type='firefly', rate=0.7, color='#e4ff8c'), rain=dict(saturation=0.75, contrast=0.95, tint='#8890c0')),
    vig='#060818', lm=dict(base='#a8b0e0', shadow='#5a6098', sky_amb=1.0), shafts=0.0),
}

def variant_palette(key):
    v = VAR[key]; pal = {}
    lt, st = hx(v['light']), hx(v['shadow'])
    skyc = [hx(c) for c in v['sky']]
    for n, lv, base in MATS:
        ids = IDX[n]
        if n == 'SKY':
            for i, ix in enumerate(ids):
                t = i/(lv-1)*(len(skyc)-1); j = min(int(t), len(skyc)-2); pal[ix] = tohex(mix(skyc[j], skyc[j+1], t-j))
            continue
        ov = v['pal_over'].get(n)
        if ov is not None:
            ov = ov if isinstance(ov, list) else [ov]*lv
            for i, ix in enumerate(ids): pal[ix] = ov[i] if ov[i].startswith('#') else ov[i]
            continue
        b = hx(base)
        dark = b*mix(np.ones(3), st, 0.7)*v['lo']; light = b*lt*v['hi']; light = light + (1-light)*v['lift']
        if n in ('HILL_FAR', 'HILL_NEAR', 'TREE_FAR', 'FAR_HOUSE'):   # 空氣透視：遠景偏向地平線天色
            hz = skyc[-1] if key != 'H4' else skyc[-2]; k_ = {'HILL_FAR': 0.5, 'TREE_FAR': 0.35, 'HILL_NEAR': 0.25, 'FAR_HOUSE': 0.4}[n]
            dark, light = mix(dark, hz, k_), mix(light, hz, k_*0.8)
        for i, ix in enumerate(ids):
            t = 0.5 if lv == 1 else 0.15 + 0.85*i/(lv-1)
            pal[ix] = tohex(mix(dark, light, t))
    return pal

# ======================= grade／LUT =======================
def grade_fn(rgb, g, rain=None):
    c = rgb*hx(g['ambientTint'])
    con, sat = g['contrast'], g['saturation']
    if rain: c = c*hx(rain['tint']); con *= rain['contrast']; sat *= rain['saturation']
    c = (c-0.5)*con + 0.5
    lum = (c @ np.array([0.2126, 0.7152, 0.0722]))[..., None]
    c = lum + (c-lum)*sat
    return np.clip(c, 0, 1)

def make_lut(g, rain=None):
    r = np.arange(16)/15.0
    R, G, B = np.meshgrid(r, r, r, indexing='xy')     # shape (g,r,b)? 用明確迴圈避免混亂
    lut = np.zeros((16, 256, 3))
    for b in range(16):
        for gy in range(16):
            for rx in range(16):
                lut[gy, b*16+rx] = (rx/15, gy/15, b/15)
    lut = grade_fn(lut, g, rain)
    return lut

def apply_lut(img, lut):
    """img float [..,3] 0–1；三線性插值取樣 256×16 strip（x = b*16 + r，y = g）。"""
    s = np.clip(img, 0, 1)*15
    i0 = np.floor(s).astype(int); i1 = np.minimum(i0+1, 15); f = s - i0
    def at(r, g, b): return lut[g, b*16 + r]
    out = 0
    for dr in (0, 1):
        for dg in (0, 1):
            for db in (0, 1):
                r = i1[..., 0] if dr else i0[..., 0]; gg = i1[..., 1] if dg else i0[..., 1]; b = i1[..., 2] if db else i0[..., 2]
                w = (f[..., 0] if dr else 1-f[..., 0])*(f[..., 1] if dg else 1-f[..., 1])*(f[..., 2] if db else 1-f[..., 2])
                out = out + at(r, gg, b)*w[..., None]
    return out

# ======================= 模糊 =======================
def box(a, r):
    if r < 1: return a
    p = np.pad(a, ((0, 0), (r+1, r), (0, 0)), mode='edge'); c = np.cumsum(p, axis=1); a = (c[:, 2*r+1:] - c[:, :-2*r-1])/(2*r+1)
    p = np.pad(a, ((r+1, r), (0, 0), (0, 0)), mode='edge'); c = np.cumsum(p, axis=0); return (c[2*r+1:] - c[:-2*r-1])/(2*r+1)
def gblur(a, s):
    if s <= 0.3: return a
    r = max(1, int(round(s*0.87)))
    for _ in range(3): a = box(a, r)
    return a
def blur_rgba(l, s):
    if s <= 0.3: return l
    pm = np.concatenate([l[..., :3]*l[..., 3:], l[..., 3:]], -1); b = gblur(pm, s); a = b[..., 3:]
    return np.concatenate([b[..., :3]/np.maximum(a, 1e-4), a], -1)
def blur_rgba_var(l, smap, levels):
    """按每行 sigma（smap: (LH,)）混合幾級模糊 → 移軸式 mid DoF。"""
    outs = [l] + [blur_rgba(l, s) for s in levels]
    lv = np.array([0] + list(levels)); out = np.zeros_like(l)
    for y in range(l.shape[0]):
        s = smap[y]; j = np.searchsorted(lv, s)
        if j == 0: out[y] = outs[0][y]; continue
        if j >= len(lv): out[y] = outs[-1][y]; continue
        t = (s-lv[j-1])/(lv[j]-lv[j-1]); out[y] = outs[j-1][y]*(1-t) + outs[j][y]*t
    return out

def mid_dof_map(sig):
    y = np.arange(LH) - MY + 0.5    # art y
    d = np.where(y < 262, (262-y)/90, np.where(y > 340, (y-340)/70, 0))
    return np.clip(d, 0, 1)*sig

# ======================= 光照 =======================
def lighting(key, idx):
    v = VAR[key]; lay = Lay(); X, Y = lay.X, lay.Y
    base, shc = hx(v['lm']['base']), hx(v['lm']['shadow'])
    shadow = np.zeros((LH, LW))
    nz = vnoise(3.5, 9); nzb = vnoise(9, 11)
    # 樹冠陰影（左）＋斑駁
    cx, cy = LAYOUT['tree']['canopy_center']
    if key in ('H1', 'H3', 'H2'):
        off = {'H1': 30, 'H3': 6, 'H2': -4}[key]
        tsh = np.exp(-(((X-cx-off)/48)**2 + ((Y-300)/34)**2)) * (Y > 254)
        dap = np.clip((nz-0.42)*3, 0, 1)
        shadow = np.maximum(shadow, tsh*(0.55 + 0.45*dap)*(0.8 if key != 'H3' else 0.5))
    # 樹冠自身底部陰影（葉底）
    shadow = np.maximum(shadow, np.clip((Y-(cy-10))/70, 0, 1)*np.isin(idx['mid'].m, IDX['LEAF'])*(X < 80)*0.35)
    # 小屋投影
    wx0 = LAYOUT['cottage']['wall'][0]
    if key == 'H1': shadow = np.maximum(shadow, ((X > wx0-2-(Y-262)*0.6) & (Y > 262) & (Y < 300))*0.45)
    if key == 'H3': shadow = np.maximum(shadow, ((X > wx0+6) & (Y > 262) & (Y < 276))*0.35)
    shadow = np.maximum(shadow, ((X > wx0) & (Y > 170) & (Y < 262) & (key == 'H2'))*0.3)
    # 接觸 AO：物件底
    def ao(x, y, rx, ry, s): return np.exp(-(((X-x)/rx)**2+((Y-y)/ry)**2))*s
    aos = [ao(*LAYOUT['lampPost']['base'], 8, 3, 0.55), ao(LAYOUT['mushrooms'][0], LAYOUT['mushrooms'][1]+2, 14, 3, 0.5), ao(LAYOUT['can'][0], LAYOUT['can'][1], 9, 2.5, 0.5),
           ao(50, 279, 40, 3, 0.4), ao(70, 262, 120, 3, 0.45)]
    for nm, (px, py) in LAYOUT['pots'].items(): aos.append(ao(px, py, 9, 2.5, 0.55))
    for a_ in aos: shadow = np.maximum(shadow, a_)
    # 下方前景壓暗（HD-2D 微縮感）
    grad = np.clip((Y-360)/90, 0, 1)*{'H1': 0.25, 'H2': 0.55, 'H3': 0.15, 'H4': 0.4}[key]
    shadow = np.maximum(shadow, grad)
    if key == 'H2':   # 逆光：前景整體壓暗
        shadow = np.maximum(shadow, np.clip((Y-262)/200, 0, 1)*0.45)
    shadow = gblur(shadow[..., None], 1.5)[..., 0]
    lm = mix(base[None, None], shc[None, None], np.clip(shadow, 0, 1)[..., None])
    # 光源：lightmap 提亮（multiply 最多到 1）＋ light_add
    add = np.zeros((LH, LW, 3))
    def pool(x, y, rx, ry, col, a, p=2.0): 
        w = np.exp(-((((X-x)/rx)**2+((Y-y)/ry)**2))**(p/2)); return w[..., None]*hx(col)*a
    lamp = LAYOUT['lampPost']['head']
    if key == 'H4':
        lit = np.zeros((LH, LW))
        lit = np.maximum(lit, np.exp(-(((X-lamp[0])/40)**2+((Y-lamp[1]-50)/46)**2)))
        lit = np.maximum(lit, np.exp(-(((X-lamp[0])/16)**2+((Y-lamp[1])/16)**2)))
        for (lx, ly) in lantern_pos(): lit = np.maximum(lit, 0.8*np.exp(-(((X-lx)/18)**2+((Y-ly)/18)**2)))
        a, b, c, d = LAYOUT['cottage']['window']
        lit = np.maximum(lit, 0.7*np.exp(-(((X-(a+c)/2)/14)**2+((Y-(b+d)/2)/13)**2)))
        lit = np.maximum(lit, 0.6*np.exp(-(((X-(a+c)/2+8)/22)**2+((Y-275)/8)**2)))    # 窗光落地
        mx, my = VAR['H4']['feats']['moon']
        lit = np.maximum(lit, 0.35*np.exp(-(((X-mx)/40)**2+((Y-my)/40)**2)))
        lit = np.maximum(lit, 0.35*np.exp(-(((X-FOOT[0])/30)**2+((Y-FOOT[1]+6)/14)**2)))  # 寵物燈泡範圍（基線，引擎再加動態）
        lm = mix(lm, hx('#fff0d8')[None, None], np.clip(lit, 0, 1)[..., None]*0.95)
        add += pool(lamp[0]+6, lamp[1]+58, 40, 14, '#ffa048', 0.42)
        add += pool(lamp[0], lamp[1], 12, 12, '#ffd890', 0.5)
        for (lx, ly) in lantern_pos(): add += pool(lx, ly, 10, 10, '#ff9a50', 0.36)
        add += pool((a+c)/2, 276, 20, 6, '#ffb860', 0.28)
        add += pool(mx, my, 26, 26, '#a0b0ff', 0.12)
    if key == 'H1':
        p = X + 0.62*Y
        sh = sum(np.exp(-((p-c_)/w_)**2) for c_, w_ in [(150, 10), (200, 16), (262, 8), (300, 14)])
        sh = sh*np.clip((Y-60)/120, 0, 1)*np.clip((420-Y)/140, 0, 1)
        add += sh[..., None]*hx('#ffd890')*v['shafts']
        sx, sy, _ = v['feats']['sun']; add += pool(sx, sy, 50, 50, '#ffcc80', 0.22)
    if key == 'H2':
        sx, sy, _ = v['feats']['sun']
        add += pool(sx, sy, 70, 46, '#ff9050', 0.42) + pool(sx, sy, 22, 18, '#fff0b0', 0.4)
        ang = np.arctan2(Y-sy, X-sx); r = np.hypot(X-sx, Y-sy)
        rays = (0.5+0.5*np.cos(ang*9))**4*np.exp(-r/120)*(Y < sy+6)
        add += rays[..., None]*hx('#ffb070')*0.22
        lam = lantern_pos()
        for (lx, ly) in lam: add += pool(lx, ly, 8, 8, '#ff9a50', 0.25)
        add += pool(lamp[0], lamp[1], 10, 10, '#ffd890', 0.22)
        # 地平線暖光帶
        add += (np.exp(-((Y-236)/22)**2)*0.18)[..., None]*hx('#ff8a50')
    if key == 'H3':
        add += pool(200, -10, 120, 120, '#e8fff8', 0.18)
        add += (np.clip((300-Y)/300, 0, 1)*0.04)[..., None]*hx('#ffffff')
    return np.clip(lm, 0, 1), np.clip(add, 0, 1)

# ======================= 輸出 =======================
def to8(a): return (np.clip(a, 0, 1)*255+0.5).astype(np.uint8)
def save_rgba(a, p): Image.fromarray(to8(a), 'RGBA').save(p)
def save_rgb(a, p): Image.fromarray(to8(a), 'RGB').save(p)

def raw_rgba(m, pal):
    lut = np.zeros((256, 4)); 
    for ix, h in pal.items(): lut[ix, :3] = hx(h); lut[ix, 3] = 1
    return lut[m]

def feats_for(key): return VAR[key]['feats']

def build_layers_only():
    """共用索引層（用 H1 天空特徵做預設；sky 按款另出）＋ materials.json ＋ layout.json"""
    d = os.path.join(OUT, 'index'); os.makedirs(d, exist_ok=True)
    idx = build_index({'clouds': VAR['H1']['feats']['clouds']})
    for nm in ('sky', 'far', 'mid', 'fore'):
        Image.fromarray(idx[nm].m, 'L').save(os.path.join(d, f'{nm}_index.png'))
    # 每款 sky 索引（按款微調：太陽／月／星／雲位）
    for key in VAR:
        ik = build_index(feats_for(key))
        Image.fromarray(ik['sky'].m, 'L').save(os.path.join(d, f'sky_index_{key}.png'))
    json.dump({'note': 'index 0＝透明；每個 material 佔連續 index（level 0 暗 → 高 亮）。每款色盤 = H#/palette.json（index→hex）。',
               'count': NIDX, 'materials': [{'name': n, 'levels': lv, 'index': IDX[n], 'emissiveCandidate': n in EMISSIVE_MATS} for n, lv, _ in MATS]},
              open(os.path.join(d, 'materials.json'), 'w'), ensure_ascii=False, indent=1)
    lay = {
     'version': 1, 'layerSize': [LW, LH], 'artSize': [AW, AH], 'layerOffset': [MX, MY],
     'coords': 'art 座標（層座標＝art＋layerOffset）；所有層同 lightmap／light_add／emissive／emissive_blur 都係 223×446，對齊 mid；vignette.png 係 195×422 螢幕座標。',
     'layers': ['sky', 'far', 'mid', 'fore'],
     'parallaxSuggest': {'sky': 0.15, 'far': 0.35, 'mid': 1.0, 'fore': 1.6},
     'pet': {'foot': list(FOOT), 'groundY': FOOT[1], 'rangeX': [FOOT[0]-62, FOOT[0]+62], 'rangeXRel': [-62, 62],
             'sizes': {'sprout': 32, 'radiant': 64, 'soft': 64}, 'pivotRule': '(w/2, h-3)', 'clearBox': [30, 210, 165, 300]},
     'ground': {'lineY': FOOT[1], 'stageEllipse': {'c': [FOOT[0], FOOT[1]+4], 'r': [80, 21]}, 'walkable': [[17, 278], [178, 278], [178, 318], [17, 318]], 'horizonY': HORIZON},
     'pots': {k_: {'base': v_} for k_, v_ in LAYOUT['pots'].items()},
     'props': {'bed': LAYOUT['bed'], 'mushrooms': LAYOUT['mushrooms'], 'wateringCan': LAYOUT['can'], 'stones': [s[:2] for s in LAYOUT['stones']],
               'poopSlotsEngine': [[50, 304], [146, 302], [118, 318]]},
     'lights': {'lampPost': {'pos': LAYOUT['lampPost']['head'], 'radius': 46, 'color': '#ffd890'},
                'lanterns': [{'pos': list(p), 'radius': 18, 'color': '#ff9a50'} for p in lantern_pos()],
                'window': {'rect': LAYOUT['cottage']['window'], 'color': '#ffc870'}, 'farWindows': [[135, 227], [141, 227]],
                'sun': {k_: list(VAR[k_]['feats']['sun'][:2]) for k_ in VAR if 'sun' in VAR[k_]['feats']},
                'moon': list(VAR['H4']['feats']['moon']),
                'perVariantOn': {k_: sorted(VAR[k_]['emissive']) for k_ in VAR}},
     'uiSafe': {'hudTop': [0, 0, AW, 62], 'actionBar': [0, 378, AW, AH], 'popPanel': [0, 330, AW, 378], 'note': '頂 HUD／底按鈕位只放天空、樹葉、草，唔放互動物件。'},
    }
    json.dump(lay, open(os.path.join(OUT, 'layout.json'), 'w'), ensure_ascii=False, indent=1)
    # 預覽：索引層（H1 色盤 raw 疊）
    pal = variant_palette('H1'); comp = np.zeros((LH, LW, 3))
    for nm in ('sky', 'far', 'mid', 'fore'):
        r = raw_rgba(idx[nm].m, pal); comp = comp*(1-r[..., 3:]) + r[..., :3]*r[..., 3:]
    im = Image.fromarray(to8(comp)); dr = ImageDraw.Draw(im)
    dr.rectangle([MX, MY, MX+AW-1, MY+AH-1], outline=(255, 0, 255))
    for (x0, y0, x1, y1) in (lay['uiSafe']['hudTop'], lay['uiSafe']['actionBar']): dr.rectangle([x0+MX, y0+MY, x1+MX-1, y1+MY-1], outline=(255, 60, 60))
    dr.line([MX+FOOT[0]-62, MY+FOOT[1], MX+FOOT[0]+62, MY+FOOT[1]], fill=(0, 255, 255))
    im.resize((LW*2, LH*2), Image.NEAREST).save(os.path.join(OUT, 'layout_preview_2x.png'))
    print('layers ok', NIDX)

def load_frame(form, name='idle_01'):
    return np.asarray(Image.open(os.path.join(SPR, 'frames', form, f'{name}.png')).convert('RGBA')).astype(float)/255

def rim_from_alpha(a):
    """1px 內緣 mask＋外向法線（同 build_tuanrong_rim.py 一致）"""
    m = a > 0.5; p = np.pad(m, 1)
    inner = m & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])
    nx = p[1:-1, :-2].astype(float) - p[1:-1, 2:]; ny = p[:-2, 1:-1].astype(float) - p[2:, 1:-1]
    n = np.hypot(nx, ny); n[n == 0] = 1
    return inner, nx/n, ny/n

def comp_pet(key, g, form, frame='idle_01', mir=1, rimdir=None):
    """寵物合成（引擎做法）：sprite × petTint × ambientTint ＋ rim（方向加權）。回傳 art 大小 RGBA。"""
    S = FORMS[form]; f = load_frame(form, frame)
    if mir < 0: f = f[:, ::-1]
    c = f[..., :3]*hx(g['petTint'])*hx(g['ambientTint'])
    inner, nx, ny = rim_from_alpha(f[..., 3])
    d = np.array(g['rim']['dir'], float); d /= np.linalg.norm(d)
    w = np.clip(nx*d[0] + ny*d[1], 0, 1)*inner*g['rim']['intensity']
    c = c*(1-w[..., None]) + hx(g['rim']['color'])*w[..., None]
    out = np.zeros((AH, AW, 4)); x0, y0 = FOOT[0]-S//2, FOOT[1]-(S-3)
    out[y0:y0+S, x0:x0+S, :3] = c; out[y0:y0+S, x0:x0+S, 3] = f[..., 3]
    return out, (FOOT[0], FOOT[1]-S+6 if S > 32 else FOOT[1]-S+4)

def over(dst, src): a = src[..., 3:]; return dst*(1-a) + src[..., :3]*a
def crop(a): return a[MY:MY+AH, MX:MX+AW]

PART = None
def particle_frames():
    """4 款 8×8、6 幀；回傳 {type: [RGBA uint8 frames]}"""
    T = {}
    def blank(): return np.zeros((8, 8, 4), np.uint8)
    def put(fr, x, y, col): 
        if 0 <= x < 8 and 0 <= y < 8: fr[y, x] = (*[int(round(v*255)) for v in hx(col)], 255)
    # mote：光塵，閃爍十字
    fr = []
    for i, s in enumerate([0, 1, 2, 2, 1, 0]):
        a = blank(); put(a, 3, 3, '#fff8e0'); put(a, 4, 4, '#fff2c0') if s else None
        if s >= 1: put(a, 4, 3, '#ffe6a0'); put(a, 3, 4, '#ffe6a0')
        if s >= 2: put(a, 3, 2, '#ffe6a0'); put(a, 5, 4, '#ffe6a0'); put(a, 2, 3, '#ffd890'); put(a, 4, 5, '#ffd890')
        fr.append(a)
    T['mote'] = fr
    # gold：金塵，菱形旋轉閃
    fr = []
    shapes = [[(3, 3), (4, 4)], [(3, 3), (4, 3), (3, 4), (4, 4)], [(3, 2), (2, 3), (3, 3), (4, 3), (3, 4), (5, 4), (4, 5), (4, 4)],
              [(4, 2), (3, 3), (4, 3), (5, 3), (4, 4), (3, 5)], [(3, 3), (4, 4), (4, 3)], [(4, 4)]]
    for sh in shapes:
        a = blank()
        for j, (x, y) in enumerate(sh): put(a, x, y, '#fff0a0' if j % 3 == 0 else '#ffc860')
        fr.append(a)
    T['gold'] = fr
    # petal：花瓣翻轉
    fr = []
    pet = [[(2, 3), (3, 3), (4, 3), (3, 4), (4, 4), (5, 4)], [(3, 2), (3, 3), (4, 3), (4, 4), (5, 5)], [(3, 2), (4, 3), (4, 4), (4, 5)],
           [(4, 2), (4, 3), (3, 4), (4, 4), (2, 5)], [(5, 3), (4, 3), (3, 3), (4, 4), (3, 4), (2, 4)], [(2, 4), (3, 4), (4, 4), (5, 3)]]
    for sh in pet:
        a = blank()
        for j, (x, y) in enumerate(sh): put(a, x, y, '#ffe6f0' if j < 2 else '#f8b4cc')
        fr.append(a)
    T['petal'] = fr
    # firefly：螢火呼吸
    fr = []
    for s in [0, 1, 2, 3, 2, 1]:
        a = blank(); put(a, 3, 3, '#f4ffc0' if s >= 2 else '#c8f070')
        if s >= 1: put(a, 4, 3, '#c8f070'); put(a, 3, 4, '#c8f070'); put(a, 4, 4, '#a8d860')
        if s >= 3: put(a, 2, 3, '#88c050'); put(a, 5, 4, '#88c050'); put(a, 3, 2, '#88c050'); put(a, 4, 5, '#88c050'); put(a, 4, 3, '#f4ffc0')
        fr.append(a)
    T['firefly'] = fr
    return T

def draw_particles_on(img, key, seed=3, n=14):
    T = particle_frames(); kind = VAR[key]['grade']['particles']['type']; rng = np.random.default_rng(seed)
    for i in range(n):
        x, y = int(rng.uniform(20, 180)), int(rng.uniform(80, 300))
        if 60 < x < 135 and 220 < y < 296: continue
        fr = T[kind][i % 6].astype(float)/255
        a = fr[..., 3:]; img[y:y+8, x:x+8] = img[y:y+8, x:x+8]*(1-a) + fr[..., :3]*a
    return img

def build_variant(key, rain=False):
    v = VAR[key]; g = dict(v['grade']); d = os.path.join(OUT, key); os.makedirs(os.path.join(d, 'raw'), exist_ok=True)
    idx = build_index(feats_for(key)); pal = variant_palette(key)
    lut = make_lut(g)
    layers = {}; raws = {}
    for nm in ('sky', 'far', 'mid', 'fore'):
        r = raw_rgba(idx[nm].m, pal); raws[nm] = r
        save_rgba(r, os.path.join(d, 'raw', f'{nm}.png'))
        gr = r.copy(); gr[..., :3] = apply_lut(r[..., :3], lut)
        if nm == 'far': gr = blur_rgba(gr, g['dof']['far'])
        if nm == 'mid':
            sig = g['dof']['mid']; gr = blur_rgba_var(gr, mid_dof_map(sig), [sig*0.5, sig]) if sig > 0.3 else gr
        if nm == 'fore': gr = blur_rgba(gr, g['dof']['fore'])
        gr[..., 3] = np.where(gr[..., 3] < 1/255, 0, gr[..., 3])
        layers[nm] = gr; save_rgba(gr, os.path.join(d, f'{nm}.png'))
    # 光照
    lm, add = lighting(key, idx)
    save_rgb(lm, os.path.join(d, 'lightmap.png')); save_rgb(add, os.path.join(d, 'light_add.png'))
    # emissive：sky/far/mid 可見嘅發光材質（fore 遮住嘅位除外）
    em = np.zeros((LH, LW, 4)); fore_a = raws['fore'][..., 3] > 0
    for nm in ('sky', 'far', 'mid'):
        m = idx[nm].m
        for mat, s in v['emissive'].items():
            mk = np.isin(m, IDX[mat]) & ~fore_a
            if nm != 'mid':   # 被前面層遮住嘅唔計
                for nm2 in ('far', 'mid')[('sky', 'far').index(nm):]: mk &= raws[nm2][..., 3] == 0
            col = raws[nm][..., :3]*s
            em[mk, :3] = col[mk]; em[mk, 3] = 1
    em_out = em.copy(); em_out[..., 3] = (em[..., 3] > 0).astype(float)
    save_rgba(em_out, os.path.join(d, 'emissive.png'))
    t = g['bloom']['threshold']; e = em[..., :3]
    lum = e @ np.array([0.3, 0.55, 0.15]); bright = e*np.clip((lum-t*0.5)/(1-t*0.5+1e-6), 0, 1)[..., None] + e*0.25
    eb = gblur(bright, 3)*0.5 + gblur(bright, 9)*0.5
    eb = np.clip(eb*1.6, 0, 1)
    save_rgb(eb, os.path.join(d, 'emissive_blur.png'))
    # vignette（螢幕 195×422）
    yy, xx = np.mgrid[0:AH, 0:AW].astype(float)
    dd = ((xx/AW-0.5)/0.5)**2 + ((yy/AH-0.48)/0.5)**2
    va = np.clip((dd-0.35)/0.9, 0, 1)**1.5*g['vignette']*1.6
    vg = np.zeros((AH, AW, 4)); vg[..., :3] = hx(v['vig']); vg[..., 3] = np.clip(va, 0, 1)
    save_rgba(vg, os.path.join(d, 'vignette.png'))
    # LUT
    save_rgb(lut, os.path.join(d, 'lut.png'))
    # grade.json
    gj = dict(variant=key, name=v['name'], hours=v['hours']); gj.update(g)
    json.dump(gj, open(os.path.join(d, 'grade.json'), 'w'), ensure_ascii=False, indent=1)
    used = sorted({int(i) for nm in ('sky', 'far', 'mid', 'fore') for i in np.unique(idx[nm].m) if i})
    json.dump({'variant': key, 'count': len(pal), 'usedIndex': len(used), 'usedColors': len({pal[i] for i in used}),
               'colors': [{'index': i, 'material': next(n for n in IDX if i in IDX[n]), 'hex': pal[i]} for i in sorted(pal)]},
              open(os.path.join(d, 'palette.json'), 'w'), ensure_ascii=False, indent=1)
    # mockups
    for form in FORMS:
        im = compose(key, layers, lm, add, eb, vg, g, form)
        save_rgb(im, os.path.join(d, f'mockup_{form}.png'))
        Image.fromarray(to8(im)).resize((AW*2, AH*2), Image.NEAREST).save(os.path.join(d, f'mockup_{form}_2x.png'))
    print(key, 'ok', 'raw colors', len({pal[i] for i in used}))
    return dict(layers=layers, lm=lm, add=add, eb=eb, vg=vg, g=g)

def compose(key, layers, lm, add, eb, vg, g, form, frame='idle_01', rain=None, rframe=0, particles=True):
    img = crop(layers['sky'])[..., :3]
    for nm in ('far', 'mid'): img = over(img, crop(layers[nm]))
    pet, bulb = comp_pet(key, g, form, frame)
    # blob 影（引擎做；mockup 示意）
    yy, xx = np.mgrid[0:AH, 0:AW].astype(float); S = FORMS[form]
    sh = (((xx-FOOT[0])/(S*0.36))**2 + ((yy-FOOT[1]-0.5)/(S*0.07+1))**2 <= 1)
    img = img*(1-0.28*sh[..., None])
    img = over(img, pet)
    img = over(img, crop(layers['fore']))
    img = img*crop(lm)
    img = img + crop(add)
    img = img + crop(eb)*g['bloom']['intensity']
    # 寵物燈泡 glow（引擎動態；mockup 示意）
    bx, by = bulb; r = np.hypot(xx-bx, yy-by)
    img = img + (np.exp(-(r/(10 if S > 32 else 6))**2)*0.35*{'H4': 1.4, 'H2': 1.0}.get(key, 0.6))[..., None]*hx(g['bulbGlowTint'])
    if rain is not None: img = rain(img)
    if particles: img = draw_particles_on(img, key)
    fc = hx(g['fog']['color']); img = img*(1-g['fog']['density']) + fc*g['fog']['density']
    img = over(np.clip(img, 0, 1), vg)
    return np.clip(img, 0, 1)

if __name__ == '__main__':
    what = sys.argv[1:] or ['all']
    if 'layers' in what or 'all' in what: build_layers_only()
    for k_ in ('H1', 'H3', 'H4', 'H2'):
        if k_ in what or 'all' in what: build_variant(k_)

# ======================= 雨層（H3 落雨中）=======================
def bake(raw, g, nm, lut):
    gr = raw.copy(); gr[..., :3] = apply_lut(raw[..., :3], lut)
    if nm == 'far': gr = blur_rgba(gr, g['dof']['far'])
    if nm == 'mid':
        sig = g['dof']['mid']; gr = blur_rgba_var(gr, mid_dof_map(sig), [sig*0.5, sig]) if sig > 0.3 else gr
    if nm == 'fore': gr = blur_rgba(gr, g['dof']['fore'])
    gr[..., 3] = np.where(gr[..., 3] < 1/255, 0, gr[..., 3]); return gr

RAIN_C = ['#e4f0f8', '#a8c4d8']
def rain_tiles():
    rng = np.random.default_rng(21); S = 64; base = np.zeros((S, S), np.uint8)
    for i in range(22):
        x, y, l = int(rng.integers(0, S)), int(rng.integers(0, S)), int(rng.integers(4, 8))
        for j in range(l):
            yy = (y+j) % S; xx = (x + (1 if j >= l//2 and i % 3 == 0 else 0)) % S
            base[yy, xx] = 1 if j < l-2 else 2
    frames = [np.roll(base, 16*k, axis=0) for k in range(4)]
    out = []
    for f in frames:
        a = np.zeros((S, S, 4), np.uint8)
        for v_, c in ((1, RAIN_C[0]), (2, RAIN_C[1])): a[f == v_] = (*[int(round(t*255)) for t in hx(c)], 255)
        out.append(a)
    return out

def ripple_frames():
    out = []
    for k, (rx, ry, dash) in enumerate([(1.5, 0.8, 1), (3.5, 1.6, 1), (5.5, 2.5, 2), (7.2, 3.3, 3)]):
        a = np.zeros((8, 16, 4), np.uint8)
        for t in np.linspace(0, 2*math.pi, 80, endpoint=False):
            x, y = int(round(7.5+rx*math.cos(t))), int(round(4+ry*math.sin(t)))
            if dash > 1 and int(t/(2*math.pi)*16) % dash: continue
            if 0 <= x < 16 and 0 <= y < 8: a[y, x] = (*[int(round(v*255)) for v in hx(RAIN_C[0] if k < 2 else RAIN_C[1])], 255)
        if k == 0: a[4, 7:9] = (*[int(round(v*255)) for v in hx('#ffffff')], 255)
        out.append(a)
    return out

def sheet(frames, names, path_png, path_json, pad=2):
    h, w = frames[0].shape[:2]; W_ = len(frames)*(w+pad)+pad; H_ = h+2*pad
    sh = np.zeros((H_, W_, 4), np.uint8); J = {'frames': {}}
    for i, (f, n) in enumerate(zip(frames, names)):
        x = pad + i*(w+pad); sh[pad:pad+h, x:x+w] = f
        J['frames'][n] = {'frame': {'x': x, 'y': pad, 'w': w, 'h': h}, 'sourceSize': {'w': w, 'h': h}}
    J['meta'] = {'image': os.path.basename(path_png), 'size': {'w': W_, 'h': H_}, 'format': 'RGBA8888', 'padding': pad}
    Image.fromarray(sh, 'RGBA').save(path_png); return J

def build_rain():
    rd = os.path.join(OUT, 'rain'); os.makedirs(rd, exist_ok=True)
    tf = rain_tiles(); J = sheet(tf, [f'rain_{i+1:02d}' for i in range(4)], os.path.join(rd, 'rain_tile.png'), None)
    J['meta'].update(tile=[64, 64], fps=12, loop=True, note='可平鋪；每幀向下 16px，4 幀循環無縫。建議 globalAlpha 0.55，畫喺 emissive_blur 之後、fog 之前；可疊兩層（1x 速／0.6x 速、偏移 32px）做深度。')
    json.dump(J, open(os.path.join(rd, 'rain_tile.json'), 'w'), ensure_ascii=False, indent=1)
    rf = ripple_frames(); J2 = sheet(rf, [f'ripple_{i+1:02d}' for i in range(4)], os.path.join(rd, 'ripple.png'), None)
    J2['meta'].update(fps=10, loop=False, pivot=[8, 4], note='隨機落喺 layout.json ground.walkable；每 0.1–0.3 秒生一個，播完即消失。')
    json.dump(J2, open(os.path.join(rd, 'ripple.json'), 'w'), ensure_ascii=False, indent=1)
    Image.fromarray(np.concatenate([np.tile(tf[0], (2, 2, 1))], 1)).resize((256, 256), Image.NEAREST).save(os.path.join(rd, 'rain_tile_tiled_preview_2x.png'))
    # H3 落雨 grade（最終值）
    g = json.loads(json.dumps(VAR['H3']['grade'])); r = g['rain']
    g2 = dict(baseVariant='H3', note='落雨中最終值（已套 rain 倍數）；sky/far/mid/fore 用 H3/rain/*；lightmap 沿用 H3；light_add 建議 globalAlpha 0.3。')
    g2.update(g)
    g2['ambientTint'] = tohex(hx(g['ambientTint'])*hx(r['tint'])); g2['saturation'] = round(g['saturation']*r['saturation'], 3)
    g2['contrast'] = round(g['contrast']*r['contrast'], 3); g2['fog'] = dict(color='#c8d6e0', density=0.12)
    g2['bloom'] = dict(threshold=0.92, intensity=0.1); g2['vignette'] = 0.2; g2['rim'] = dict(color='#4a5a7a', intensity=0.5, dir=[0.6, 0.8])
    g2['petTint'] = '#f0e2d0'; g2['particles'] = dict(type='petal', rate=0.0, color='#ffe0ec'); g2['dof'] = dict(far=1.8, mid=0.8, fore=2.6)
    d = os.path.join(OUT, 'H3'); os.makedirs(os.path.join(d, 'rain'), exist_ok=True)
    json.dump(g2, open(os.path.join(d, 'grade_rain.json'), 'w'), ensure_ascii=False, indent=1)
    lut = make_lut(g2); save_rgb(lut, os.path.join(d, 'rain', 'lut_rain.png'))
    layers = {}
    for nm in ('sky', 'far', 'mid', 'fore'):
        raw = np.asarray(Image.open(os.path.join(d, 'raw', f'{nm}.png')).convert('RGBA')).astype(float)/255
        layers[nm] = bake(raw, g2, nm, lut); save_rgba(layers[nm], os.path.join(d, 'rain', f'{nm}.png'))
    lm = np.asarray(Image.open(os.path.join(d, 'lightmap.png'))).astype(float)/255
    add = np.asarray(Image.open(os.path.join(d, 'light_add.png'))).astype(float)/255*0.3
    eb = np.zeros_like(add); vg = np.asarray(Image.open(os.path.join(d, 'vignette.png')).convert('RGBA')).astype(float)/255
    def rainfx(img, k=0):
        t = tf[k].astype(float)/255; T = np.tile(t, (8, 4, 1))[:AH, :AW]; a = T[..., 3:]*0.55
        img = img*(1-a) + T[..., :3]*a
        rng = np.random.default_rng(4)
        for i in range(7):
            x, y = int(rng.uniform(20, 170)), int(rng.uniform(300, 370)); f = rf[(i+k) % 4].astype(float)/255
            aa = f[..., 3:]*0.8; img[y:y+8, x:x+16] = img[y:y+8, x:x+16]*(1-aa) + f[..., :3]*aa
        return img
    for form in FORMS:
        im = compose('H3', layers, lm, add, eb, vg, g2, form, rain=rainfx, particles=False)
        save_rgb(im, os.path.join(d, 'rain', f'mockup_rain_{form}.png'))
        Image.fromarray(to8(im)).resize((AW*2, AH*2), Image.NEAREST).save(os.path.join(d, 'rain', f'mockup_rain_{form}_2x.png'))
    print('rain ok')

if __name__ == '__main__' and ('rain' in sys.argv[1:] or 'all' in sys.argv[1:]): build_rain()

# ======================= 粒子 atlas =======================
PART_META = {'mote': dict(variant='H1', name='光塵', fps=6, loop=True, motion='上升 2–4 px/s＋左右輕擺，壽命 6s，淡入淡出'),
             'gold': dict(variant='H2', name='金塵', fps=8, loop=True, motion='斜向右上 3–5 px/s，閃爍，壽命 5s'),
             'petal': dict(variant='H3', name='花瓣', fps=6, loop=True, motion='斜落 8–12 px/s＋左右擺 ±6px，壽命 8s'),
             'firefly': dict(variant='H4', name='螢火', fps=6, loop=True, motion='隨機漂 2–6 px/s，明暗呼吸，lighter 疊加')}
def build_particles():
    pd = os.path.join(OUT, 'particles'); os.makedirs(pd, exist_ok=True); T = particle_frames()
    fr, nm = [], []
    for k in ('mote', 'gold', 'petal', 'firefly'):
        for i, f in enumerate(T[k]): fr.append(f); nm.append(f'{k}_{i+1:02d}')
    pad = 2; cols = 6; rows = 4; W_ = cols*(8+pad)+pad; H_ = rows*(8+pad)+pad
    sh = np.zeros((H_, W_, 4), np.uint8); J = {'frames': {}}
    for r_, k in enumerate(('mote', 'gold', 'petal', 'firefly')):
        for i, f in enumerate(T[k]):
            x, y = pad+i*(8+pad), pad+r_*(8+pad); sh[y:y+8, x:x+8] = f
            J['frames'][f'{k}_{i+1:02d}'] = {'frame': {'x': x, 'y': y, 'w': 8, 'h': 8}, 'sourceSize': {'w': 8, 'h': 8}}
    J['types'] = {k: dict(frames=[f'{k}_{i+1:02d}' for i in range(len(T[k]))], **PART_META[k]) for k in PART_META}
    J['meta'] = {'image': 'particles.png', 'size': {'w': W_, 'h': H_}, 'format': 'RGBA8888', 'padding': pad}
    Image.fromarray(sh, 'RGBA').save(os.path.join(pd, 'particles.png'))
    json.dump(J, open(os.path.join(pd, 'particles.json'), 'w'), ensure_ascii=False, indent=1)
    bg = np.zeros((H_, W_, 4), np.uint8); bg[...] = (40, 44, 70, 255)
    pv = Image.alpha_composite(Image.fromarray(bg, 'RGBA'), Image.fromarray(sh, 'RGBA')).resize((W_*8, H_*8), Image.NEAREST)
    pv.save(os.path.join(pd, 'particles_preview_8x.png')); print('particles ok', {k: len(v) for k, v in T.items()})

if __name__ == '__main__' and ('particles' in sys.argv[1:] or 'all' in sys.argv[1:]): build_particles()

# ======================= 時段 crossfade 預覽 GIF =======================
def load_variant(key):
    d = os.path.join(OUT, key); L = lambda n, m='RGBA': np.asarray(Image.open(os.path.join(d, n)).convert(m)).astype(float)/255
    layers = {n: L(f'{n}.png') for n in ('sky', 'far', 'mid', 'fore')}
    g = json.load(open(os.path.join(d, 'grade.json')))
    return layers, L('lightmap.png', 'RGB'), L('light_add.png', 'RGB'), L('emissive_blur.png', 'RGB'), L('vignette.png'), g

def build_crossfade(form='radiant', hold=8, fade=10):
    cd = os.path.join(OUT, 'crossfade'); os.makedirs(cd, exist_ok=True)
    seq = ['H1', 'H3', 'H2', 'H4']; idle = [f'idle_{i:02d}' for i in range(1, 5)]
    C = {}
    for k in seq:
        V_ = load_variant(k)
        C[k] = [compose(k, *V_[:5], V_[5], form, frame=f, particles=True) for f in idle]
    frames = []; t = 0
    for i, k in enumerate(seq):
        n = seq[(i+1) % 4]
        for _ in range(hold): frames.append(C[k][(t//2) % 4]); t += 1
        for j in range(fade):
            a = (j+1)/(fade+1); a = a*a*(3-2*a)
            frames.append(C[k][(t//2) % 4]*(1-a) + C[n][(t//2) % 4]*a); t += 1
    ims = [Image.fromarray(to8(f)).quantize(colors=255, method=Image.MEDIANCUT, dither=Image.NONE) for f in frames]
    p = os.path.join(cd, 'crossfade_H1-H3-H2-H4.gif')
    ims[0].save(p, save_all=True, append_images=ims[1:], duration=110, loop=0, disposal=1)
    ims2 = [Image.fromarray(to8(f)).resize((AW*2, AH*2), Image.NEAREST).quantize(colors=255, method=Image.MEDIANCUT, dither=Image.NONE) for f in frames]
    ims2[0].save(os.path.join(cd, 'crossfade_H1-H3-H2-H4_2x.gif'), save_all=True, append_images=ims2[1:], duration=110, loop=0, disposal=1)
    strip = np.concatenate([C[k][0] for k in seq], 1); save_rgb(strip, os.path.join(cd, 'crossfade_keys_strip.png'))
    print('crossfade ok', len(frames), 'frames')

if __name__ == '__main__' and ('crossfade' in sys.argv[1:] or 'all' in sys.argv[1:]): build_crossfade()
