#!/usr/bin/env python3
"""garden3d_house.py — 3D 花園 H1 立體小屋（大型建築做 mesh，細件保持 billboard）。
由 build_garden3d.build_all() 叫：build(out, cap, meta, lut, ok, mput) → 寫 mesh/cottage/*.png＋house_mesh.json，回傳 objects.json 用嘅 entry。
格式：FORMAT.md「立體建築 mesh」；驗證：validate_garden3d.py。全部程序化（numpy），冇 AI 圖。
"""
import os, json, math
import numpy as np
from PIL import Image
import build_hd2d_scenes as B

MESH_DIR = 'mesh/cottage'
# ---------------------------------------------------------------- 幾何（世界 units；1 unit＝1x px）
X0, X1 = 53.0, 112.0; WW = X1 - X0; CX = (X0 + X1)/2     # 牆身 x（＝2D 牆 art x 150..209 − 97）
ZF, ZB = -50.0, -94.0; DP = ZF - ZB                       # 前牆 z（＝舊 billboard z）、後牆 z
HW, HR = 94.0, 130.0                                      # 牆高、屋脊高（2D 262−168、262−132）
OX, OZ, TH = 6.0, 4.0, 3.0                                # 屋簷左右出、前後出、厚
TAN = (HR - HW)/(WW/2); YE = HW - OX*TAN
SLOPE = np.array([WW/2 + OX, HR - YE, 0.]); SL = float(np.linalg.norm(SLOPE)); SD = SLOPE/SL
FH = int(HR)                                              # 前／後貼圖高 130
WIN = (7, 25, 52, 72); DOOR = (33, 49, 0, 48); PLANT = (4, 28, 46, 50)   # 前牆 face 座標 (x0,x1,y0,y1)，y 由地起
SWIN = (16, 28, 50, 64); BWIN = (24, 35, 56, 66)
CHIM = (94., 102., -82., -74., 142.)                      # 煙囪 x0,x1,z0,z1,頂
FOOTPRINT = dict(x=[X0, X1], z=[ZB, ZF], pad=4)
LIGHT_SIDE = dict(id='window_side', zh='小屋側窗', x=X1 + 2, y=(SWIN[2] + SWIN[3])/2, z=ZF - (SWIN[0] + SWIN[1])/2,
                  color='#ffc870', radius=40, intensity=0.0, intensityNight=0.7, flicker=0.02)

def up3(a): return np.repeat(np.repeat(a, 3, 0), 3, 1)
def _rect(shape, x0, x1, r0, r1):
    k = np.zeros(shape, bool); k[max(int(r0), 0):max(int(r1), 0), max(int(x0), 0):max(int(x1), 0)] = True; return k

# ---------------------------------------------------------------- 貼圖（索引圖 → V3 H1 調色；冇烘方向光）
class Tex:
    def __init__(s, mput): s.mput = mput
    def planks(s, h, w, gable=0, seed=0, pitch=8):
        """橫木板牆：每塊板色調唔同、板縫、木紋、釘、近地濺泥；gable＞0 → 頂部三角山牆直板。"""
        m = np.zeros((h, w), np.uint8); rng = np.random.default_rng(seed); Y, X = np.mgrid[0:h, 0:w]
        ya = h - 1 - Y; band = ya // pitch; tone = rng.random(band.max() + 2)*.16 - .08
        grain = rng.random((h, w)) < .012; grain = grain | np.roll(grain, 1, 1) | np.roll(grain, 2, 1)
        f = .72 + tone[band] - .55*((ya % pitch) == pitch - 1) - .1*grain*((ya % pitch) != pitch - 1)
        f -= .12*((ya % pitch) == pitch - 2)
        f += .05*np.clip((ya - 3)/14, 0, 1) - .05                       # 近地濺泥略深
        s.mput(m, np.ones((h, w), bool), 'WALL', np.clip(f, 0, 1), .3)
        if gable:
            g = Y < gable; vb = ((X % 6) == 0); bat = ((X % 6) == 1)
            s.mput(m, g, 'WALL', np.clip(.66 + tone[(X//6) % len(tone)]*.8 - .55*vb + .12*bat, 0, 1), .3)
            half = (w/2)*(Y + .5)/gable; m[g & ~(np.abs(X + .5 - w/2) <= half)] = 0
            edge = g & (np.abs(np.abs(X + .5 - w/2) - half) < 1.2) & (m > 0)
            s.mput(m, edge, 'WOOD', .25, 0)                               # 山牆封邊木
        return m
    def trims(s, m, gable=0):
        h, w = m.shape; k = np.zeros(m.shape, bool); k[gable:, [0, 1, w-2, w-1]] = True; k &= m > 0
        s.mput(m, k, 'WOOD', .3, 0)
        nail = np.zeros(m.shape, bool); nail[gable::8, [1, w-2]] = True; nail &= k; s.mput(m, nail, 'METAL', .2, 0)
        return m
    def foundation(s, m, n=3):
        h, w = m.shape; Y, X = np.mgrid[0:h, 0:w]; k = (Y >= h - n) & (m > 0); rng = np.random.default_rng(3)
        f = .5 + .25*rng.random((h, w)) - .3*(((X + 3*((Y - h) % 2)) % 7) == 0) - .2*(Y == h - n)
        s.mput(m, k, 'STONE', np.clip(f, 0, 1), .3); return m
    def window(s, m, x0, x1, y0, y1, H, sill=True):
        r0, r1 = H - y1, H - y0; sh = m.shape
        s.mput(m, _rect(sh, x0-2, x1+2, r0-2, r1+2), 'WOOD', .72, 0)
        s.mput(m, _rect(sh, x0-2, x1+2, r0-2, r0-1), 'WOOD', .9, 0)
        if sill: s.mput(m, _rect(sh, x0-3, x1+3, r1+1, r1+3), 'WOOD', .5, 0)
        Y, X = np.mgrid[0:sh[0], 0:sh[1]]; gl = _rect(sh, x0, x1, r0, r1)
        s.mput(m, gl, 'WIN', np.clip(.25 + .75*(((X - x0) + (Y - r0)) > (x1 - x0)*.9) + .2*(((X - x0) - (Y - r0)) % 9 == 0), 0, 1), 0)
        cx, cy = (x0 + x1)//2, (r0 + r1)//2
        s.mput(m, _rect(sh, cx, cx+1, r0, r1), 'WOOD', .45, 0); s.mput(m, _rect(sh, x0, x1, cy, cy+1), 'WOOD', .45, 0)
    def vent(s, m, cx, cy, r):
        Y, X = np.mgrid[0:m.shape[0], 0:m.shape[1]]; d = np.hypot(X + .5 - cx, Y + .5 - cy)
        s.mput(m, d <= r, 'WOOD', .65, 0); s.mput(m, d <= r - 1.2, 'WOOD', .08, 0)
        s.mput(m, (d <= r - 1.2) & ((Y % 2) == 0), 'WOOD', .35, 0)
    def ivy(s, m, x, top, seed, H, flowers=True):
        rng = np.random.default_rng(seed)
        for j in range(top):
            yy = H - 1 - j; xx = int(x + 2.2*math.sin(j/5 + seed))
            if not (0 <= xx < m.shape[1]) or not m[yy, xx]: continue
            s.mput(m, _rect(m.shape, xx, xx+1, yy, yy+1), 'IVY', .3 + .6*((j//3) % 2), 0)
            if j % 4 == 0: s.mput(m, _rect(m.shape, xx+1, xx+3, yy-1, yy+1) & (m > 0), 'IVY', .9, 0)
            if j % 4 == 2: s.mput(m, _rect(m.shape, xx-2, xx, yy-1, yy+1) & (m > 0), 'IVY', .6, 0)
            if flowers and j % 9 == 4 and rng.random() < .6: s.mput(m, _rect(m.shape, xx-1, xx, yy, yy+1) & (m > 0), 'FLOWER_P', 1, 0)
    def fill(s, h, w, mat, f, d=.3):
        m = np.zeros((h, w), np.uint8); s.mput(m, np.ones((h, w), bool), mat, f, d); return m

def textures(cap, meta, mput):
    t = Tex(mput); MX, MY = meta['MX'], meta['MY']; T = {}; c = cap['cottage']
    # 前：牆＋山牆 59×130；窗、門、花箱、長春藤由 2D H1 小屋索引搬過嚟
    f = t.planks(FH, int(WW), int(HR - HW), seed=1)
    sub = c[132+MY:262+MY, 150+MX:209+MX]
    keep = (sub > 0) & ~np.isin(sub, B.IDX['ROOF'] + B.IDX['WALL'])
    keep &= (np.arange(FH)[:, None] + 132) >= 172                     # 2D 屋簷木條唔要（3D 有真屋簷）
    f[keep] = sub[keep]
    t.trims(f, int(HR - HW)); t.foundation(f); t.vent(f, WW/2, 20, 4.5)
    hd = np.zeros(f.shape, bool); hd[FH-DOOR[3]-2:FH-DOOR[3], DOOR[0]-2:DOOR[1]+2] = True; mput(f, hd, 'WOOD', .7, 0)   # 門楣
    T['front'] = f
    sL = t.planks(int(HW), int(DP), seed=2); t.trims(sL); t.foundation(sL)
    t.ivy(sL, 30, 70, 2, int(HW)); t.ivy(sL, 9, 40, 5, int(HW)); T['side_L'] = sL
    sR = t.planks(int(HW), int(DP), seed=3); t.trims(sR); t.foundation(sR); t.window(sR, *SWIN, int(HW))
    pb = _rect(sR.shape, SWIN[0]-2, SWIN[1]+2, HW-SWIN[2]+4, HW-SWIN[2]+8); mput(sR, pb, 'WOOD', .55, 0)   # 側窗細花槽（平面）
    for i, x in enumerate(range(SWIN[0]-1, SWIN[1]+1, 2)): mput(sR, _rect(sR.shape, x, x+1, HW-SWIN[2]+3, HW-SWIN[2]+4), ('FLOWER_Y', 'IVY', 'FLOWER_W')[i % 3], 1, 0)
    T['side_R'] = sR
    bk = t.planks(FH, int(WW), int(HR - HW), seed=4); t.trims(bk, int(HR - HW)); t.foundation(bk)
    t.window(bk, *BWIN, FH); t.vent(bk, WW/2, 20, 4.5); t.ivy(bk, 48, 60, 7, FH); T['back'] = bk
    # 屋頂 52×57（第 0 行＝屋脊）：交錯瓦片、每片色調、屋脊蓋、青苔
    rw, rh = int(DP + 2*OZ), int(math.ceil(SL)); Y, X = np.mgrid[0:rh, 0:rw]; rng = np.random.default_rng(6)
    row = Y // 4; colx = (X + 3*(row % 2)) // 6; tone = rng.random((row.max()+1, colx.max()+2))*.22 - .11
    fr = .5 + tone[row, colx] + .22*((Y % 4) == 0) - .32*((Y % 4) == 3) - .25*(((X + 3*(row % 2)) % 6) == 0)*((Y % 4) != 0)
    r = np.zeros((rh, rw), np.uint8); mput(r, np.ones((rh, rw), bool), 'ROOF', np.clip(fr, 0, 1), .3)
    mput(r, Y < 3, 'ROOF', .12 + .2*(Y == 0), 0); mput(r, (Y < 3) & ((X % 5) == 0), 'ROOF', .0, 0)
    mput(r, Y == rh - 1, 'ROOF', .05, 0)
    for _ in range(9):
        x, y = int(rng.integers(2, rw-6)), int(rng.integers(rh//2, rh-3)); w = int(rng.integers(2, 5))
        mput(r, _rect(r.shape, x, x+w, y, y+1) | _rect(r.shape, x+1, x+w-1, y-1, y), 'MOSS', .55, 0)
    T['roof'] = r
    # 細件
    Y, X = np.mgrid[0:6, 0:64]; T['trim'] = t.fill(6, 64, 'WOOD', np.clip(.35 + .25*(Y == 0) - .15*(Y == 5) - .12*((X % 16) == 0), 0, 1), .2)
    Y, X = np.mgrid[0:64, 0:32]; T['reveal'] = t.fill(64, 32, 'WOOD', np.clip(.1 + .08*((X % 4) == 0) + .05*((Y % 8) == 0), 0, 1), .25)
    Y, X = np.mgrid[0:64, 0:64]; T['soffit'] = t.fill(64, 64, 'WOOD', np.clip(.22 - .14*((X % 5) == 4) + .04*((Y % 11) == 0), 0, 1), .25)
    pt = t.fill(3, 24, 'SOIL', .25, 0)
    for i, x in enumerate(range(1, 24, 2)): mput(pt, _rect(pt.shape, x, x+1, i % 3, i % 3 + 1), ('FLOWER_P', 'FLOWER_W', 'FLOWER_B', 'FLOWER_Y', 'IVY')[i % 5], 1, 0)
    T['planter_top'] = pt
    Y, X = np.mgrid[0:32, 0:10]; ch = t.fill(32, 10, 'STONE', np.clip(.55 - .4*((Y % 4) == 3) - .35*(((X + 2*((Y//4) % 2)) % 5) == 0), 0, 1), .3)
    mput(ch, Y < 2, 'METAL', .3, 0); mput(ch, (Y >= 2) & (Y < 3), 'STONE', .2, 0); T['chimney'] = ch
    return T

# ---------------------------------------------------------------- 面
CEN = np.array([CX, HW/2, (ZF + ZB)/2])
def Q(fid, O, U, V, tex, uvpx, outward, tri=False):
    """平行四邊形（或三角形 O, O+U, O+V）。uvpx＝(u0,u1,vb,vt) 像素：s 沿 U 由 u0→u1，r 沿 V 由 vb→vt（行，圖頂＝0）。"""
    O, U, V = (np.array(a, float) for a in (O, U, V)); n = np.cross(U, V); n /= np.linalg.norm(n)
    if n @ np.array(outward, float) < 0: n = -n
    return dict(id=fid, O=O, U=U, V=V, tex=tex, uvpx=uvpx, n=n, tri=tri)
def _recess(pfx, fr, depth, H):
    x0, x1, y0, y1 = fr; ex = np.array([1., 0, 0]); ez = np.array([0, 0, 1.]); base = np.array([X0, 0, ZF]) - ez*depth; qs = []
    qs.append(Q(f'{pfx}_inner', base + ex*x0 + [0, y0, 0], ex*(x1-x0), [0, y1-y0, 0], 'front', (x0, x1, H-y0, H-y1), ez))
    for side, xx, ow in (('L', x0, ex), ('R', x1, -ex)):
        qs.append(Q(f'{pfx}_rev{side}', base + ex*xx + [0, y0, 0], ez*depth, [0, y1-y0, 0], 'reveal', (0, depth, 64, 64-(y1-y0)), ow))
    qs.append(Q(f'{pfx}_revT', base + ex*x0 + [0, y1, 0], ex*(x1-x0), ez*depth, 'reveal', (0, x1-x0, depth, 0), [0, -1, 0]))
    if y0 > 0: qs.append(Q(f'{pfx}_revB', base + ex*x0 + [0, y0, 0], ex*(x1-x0), ez*depth, 'reveal', (0, x1-x0, depth, 0), [0, 1, 0]))
    return qs
def _rects(W, H, holes):
    xs = sorted({0, W} | {h[0] for h in holes} | {h[1] for h in holes}); out = []
    for a, b in zip(xs[:-1], xs[1:]):
        ys = sorted({0, H} | {v for h in holes if h[0] <= a and h[1] >= b for v in (h[2], h[3])})
        for c, d in zip(ys[:-1], ys[1:]):
            if not any(h[0] <= a and h[1] >= b and h[2] <= c and h[3] >= d for h in holes): out.append((a, b, c, d))
    return out
def faces():
    H = FH; qs = []; ez = [0, 0, 1]
    for (a, b, c, d) in _rects(WW, HW, [WIN, DOOR]):
        qs.append(Q(f'front_{a:g}_{c:g}', [X0+a, c, ZF], [b-a, 0, 0], [0, d-c, 0], 'front', (a, b, H-c, H-d), ez))
    gh = HR - HW
    qs.append(Q('front_gable', [X0, HW, ZF], [WW, 0, 0], [WW/2, gh, 0], 'front', None, ez, tri=True))
    qs += _recess('win', WIN, 2, H); qs += _recess('door', DOOR, 3, H)
    a, b, c, d = PLANT; pd = 3
    qs.append(Q('planter_front', [X0+a, c, ZF+pd], [b-a, 0, 0], [0, d-c, 0], 'front', (a, b, H-c, H-d), ez))
    qs.append(Q('planter_top', [X0+a, d, ZF+pd], [b-a, 0, 0], [0, 0, -pd], 'planter_top', (0, 24, 3, 0), [0, 1, 0]))
    qs.append(Q('planter_L', [X0+a, c, ZF], [0, 0, pd], [0, d-c, 0], 'trim', (0, pd, 6, 6-(d-c)), [-1, 0, 0]))
    qs.append(Q('planter_R', [X0+b, c, ZF+pd], [0, 0, -pd], [0, d-c, 0], 'trim', (0, pd, 6, 6-(d-c)), [1, 0, 0]))
    qs.append(Q('side_L', [X0, 0, ZB], [0, 0, DP], [0, HW, 0], 'side_L', (0, DP, HW, 0), [-1, 0, 0]))
    qs.append(Q('side_R', [X1, 0, ZF], [0, 0, -DP], [0, HW, 0], 'side_R', (0, DP, HW, 0), [1, 0, 0]))
    qs.append(Q('back', [X1, 0, ZB], [-WW, 0, 0], [0, HW, 0], 'back', (0, WW, H, H-HW), [0, 0, -1]))
    qs.append(Q('back_gable', [X1, HW, ZB], [-WW, 0, 0], [-WW/2, gh, 0], 'back', None, [0, 0, -1], tri=True))
    L = DP + 2*OZ; vL = SD*SL; vR = np.array([-SD[0], SD[1], 0])*SL
    eL = np.array([X0-OX, YE, ZB-OZ]); eR = np.array([X1+OX, YE, ZF+OZ])
    qs.append(Q('roof_L', eL, [0, 0, L], vL, 'roof', (0, L, SL, 0), [-1, 1, 0]))
    qs.append(Q('roof_R', eR, [0, 0, -L], vR, 'roof', (0, L, SL, 0), [1, 1, 0]))
    for zz, nm, oz in ((ZF+OZ, 'front', 1), (ZB-OZ, 'back', -1)):
        for side, e0, v in (('L', [X0-OX, YE, zz], vL), ('R', [X1+OX, YE, zz], vR)):
            qs.append(Q(f'fascia_{nm}_{side}', np.array(e0) - [0, TH, 0], v, [0, TH, 0], 'trim', (0, SL, 6, 6-TH), [0, 0, oz]))
    qs.append(Q('eave_L', [X0-OX, YE-TH, ZB-OZ], [0, 0, L], [0, TH, 0], 'trim', (0, L, 6, 6-TH), [-1, 0, 0]))
    qs.append(Q('eave_R', [X1+OX, YE-TH, ZF+OZ], [0, 0, -L], [0, TH, 0], 'trim', (0, L, 6, 6-TH), [1, 0, 0]))
    # 屋簷底（soffit）：左右兩條＋前後四塊（沿斜面）
    so = OX*math.hypot(1, TAN)
    qs.append(Q('soffit_L', [X0-OX, YE-TH, ZB-OZ], [0, 0, L], [OX, OX*TAN, 0], 'soffit', (0, L, 64, 64-so), [-.3, -1, 0]))
    qs.append(Q('soffit_R', [X1+OX, YE-TH, ZF+OZ], [0, 0, -L], [-OX, OX*TAN, 0], 'soffit', (0, L, 64, 64-so), [.3, -1, 0]))
    for zz, nm, dz in ((ZF, 'front', OZ), (ZB, 'back', -OZ)):
        for side, e0, v in (('L', [X0-OX, YE-TH, zz], vL), ('R', [X1+OX, YE-TH, zz], vR)):
            qs.append(Q(f'soffit_{nm}_{side}', e0, [0, 0, dz], v, 'soffit', (0, OZ, 64, 64-SL), [0, -1, 0]))
    cx0, cx1, cz0, cz1, ytop = CHIM; yb = HR - (cx0 - CX)*TAN - 2
    for nm, O_, U_, ow in (('S', [cx0, yb, cz1], [cx1-cx0, 0, 0], [0, 0, 1]), ('N', [cx1, yb, cz0], [cx0-cx1, 0, 0], [0, 0, -1]),
                            ('W', [cx0, yb, cz0], [0, 0, cz1-cz0], [-1, 0, 0]), ('E', [cx1, yb, cz1], [0, 0, cz0-cz1], [1, 0, 0])):
        qs.append(Q(f'chimney_{nm}', O_, U_, [0, ytop-yb, 0], 'chimney', (0, 8, 32, 32-(ytop-yb)), ow))
    qs.append(Q('chimney_top', [cx0, ytop, cz1], [cx1-cx0, 0, 0], [0, 0, cz0-cz1], 'chimney', (1, 9, 10, 2), [0, 1, 0]))
    return qs

def _r(v, k=3): return [round(float(x), k) for x in v]
def face_json(q, size):
    w, h = size; O, U, V = q['O'], q['U'], q['V']
    if q['tri']:     # 山牆：三頂點；uv 直接由 face 像素位計（前／後貼圖頂部三角）
        vs = [O, O + U, O + V]
        def uvp(p):
            if q['id'] == 'front_gable': px, py = p[0] - X0, HR - p[1]
            else: px, py = X1 - p[0], HR - p[1]
            return [px/w, 1 - py/h]
        uv = [uvp(p) for p in vs]
    else:
        u0, u1, vb, vt = q['uvpx']; vs = [O, O + U, O + U + V, O + V]
        uv = [[u0/w, 1 - vb/h], [u1/w, 1 - vb/h], [u1/w, 1 - vt/h], [u0/w, 1 - vt/h]]
    nw = np.cross(vs[1] - vs[0], vs[-1] - vs[0])
    if nw @ q['n'] < 0: vs, uv = vs[::-1], uv[::-1]
    return dict(id=q['id'], tex=q['tex'], verts=[_r(p, 3) for p in vs], uv=[_r(p, 5) for p in uv], normal=_r(q['n'], 4))

TEX_LIGHT = {'front': 'window', 'back': 'window', 'side_R': 'window_side'}
def build(out, cap, meta, lut, ok, mput, save):
    T = textures(cap, meta, mput); D = f'{out}/{MESH_DIR}'; os.makedirs(D, exist_ok=True); tex = {}
    for k, m in T.items():
        a = (m > 0) & ok[m]; im = np.zeros(m.shape + (4,), np.uint8); im[..., :3] = lut[m]; im[..., 3] = a*255; im[~a, :3] = 0
        save(im, f'{D}/{k}.png'); save(up3(im), f'{D}/{k}@3x.png')
        e = dict(file=f'{MESH_DIR}/{k}.png', file3x=f'{MESH_DIR}/{k}@3x.png', size=[m.shape[1], m.shape[0]])
        w = np.isin(m, B.IDX['WIN']) & a
        if w.any():
            em = np.zeros_like(im); em[w, :3] = (np.array([0xff, 0xc8, 0x70])).astype(np.uint8); em[w, 3] = 255
            save(em, f'{D}/{k}_emissive.png'); save(up3(em), f'{D}/{k}_emissive@3x.png')
            e.update(emissive=f'{MESH_DIR}/{k}_emissive.png', emissive3x=f'{MESH_DIR}/{k}_emissive@3x.png', emissiveLight=TEX_LIGHT[k])
        tex[k] = e
    qs = faces(); fj = [face_json(q, tex[q['tex']]['size']) for q in qs]
    allv = np.array([v for f in fj for v in f['verts']])
    MJ = {'format': 'garden3d.house_mesh/1', 'id': 'cottage', 'zh': '小屋（立體盒：牆盒＋人字屋頂＋屋簷＋門窗凹位＋花箱＋煙囪）',
          'units': '1 unit＝1x px；Y 上；XZ 地面；+Z 向鏡頭；座標已係世界座標（同 objects.json），唔使再 offset',
          'paths': '相對場景根（H1/），同 objects.json 一樣',
          'bounds': {'min': _r(allv.min(0), 2), 'max': _r(allv.max(0), 2)},
          'footprint': dict(FOOTPRINT, note='碰撞矩形（XZ）：寵物／鏡頭唔入；pad＝外擴 units'),
          'castShadow': True, 'receiveShadow': True,
          'material': {'filter': 'nearest', 'mipmaps': False, 'alphaTest': 0.5, 'side': 'front', 'lit': True, 'colorSpace': 'srgb',
                       'note': '貼圖已套 V3 H1 調色、冇烘方向光／AO；光由引擎 sun＋fill＋點燈計'},
          'textures': tex, 'faces': fj}
    with open(f'{D}/house_mesh.json', 'w') as f: json.dump(MJ, f, ensure_ascii=False, indent=1)
    ent = dict(id='cottage', type='mesh', zh=MJ['zh'], mesh=f'{MESH_DIR}/house_mesh.json', x=CX, z=ZF, footprint=FOOTPRINT,
               shadow=True, layer='mid', emissiveLight='window',
               note='立體 mesh（取代舊 billboard cottage）；x/z＝前牆底中點，只作參考，mesh 頂點已係世界座標')
    return ent, T


def build_mesh(cap, meta, lut, ok, mput, GM):
    """garden3d.mesh/2：小屋所有面打包成一張 atlas、局部座標（原點＝footprint 底中）。"""
    T = textures(cap, meta, mput); mb = GM.MB('cottage'); ti = {}; size = {}
    for k, m in T.items():
        a = (m > 0) & ok[m]; im = np.zeros(m.shape + (4,), np.uint8); im[..., :3] = lut[m]; im[..., 3] = a*255; im[~a, :3] = 0
        w = np.isin(m, B.IDX['WIN']) & a; em = None
        if w.any(): em = np.zeros_like(im); em[w, :3] = (0xff, 0xc8, 0x70); em[w, 3] = 255
        ti[k] = mb.add_tex(im, em); size[k] = (m.shape[1], m.shape[0])
    ox, oz = (X0 + X1)/2, (ZF + ZB)/2
    for q in faces():
        f = face_json(q, size[q['tex']]); w, h = size[q['tex']]
        vs = [np.array(v) - (ox, 0, oz) for v in f['verts']]; tx = [(u*w, (1 - v)*h) for u, v in f['uv']]
        mb.poly(vs, tx, ti[q['tex']])
    fpl = {'rect': {'x': [FOOTPRINT['x'][0] - ox, FOOTPRINT['x'][1] - ox], 'z': [FOOTPRINT['z'][0] - oz, FOOTPRINT['z'][1] - oz]}, 'pad': FOOTPRINT['pad']}
    hent = dict(zh='小屋（立體盒：牆盒＋人字屋頂＋屋簷＋屋簷底＋門窗凹位＋花箱＋煙囪）', x=ox, z=oz, fpLocal=fpl, fp=FOOTPRINT)
    return mb, hent
