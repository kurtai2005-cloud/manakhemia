#!/usr/bin/env python3
"""build_garden3d.py — 3D 花園試點 H1（方案 C，Three.js）美術產出。
由 H1 V3 程序化索引（build_index_v3）逐物件重畫抽出 billboard（無遮擋洞），
再生俯視地面、外圍草地 tile、背景板、lights/camera json，同團絨法線 atlas（_n）。
用法：PYTHONDONTWRITEBYTECODE=1 python3 tools/build_garden3d.py all
"""
import os, sys, json, math, inspect
import numpy as np
from PIL import Image
from scipy import ndimage as nd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import build_hd2d_scenes as B
import build_garden_hd2d_v3 as G
import garden3d_house as GH
import garden3d_mesh as GM
import garden3d_props as GP
ART = os.path.abspath(f'{HERE}/..'); OUT = f'{ART}/scenes/garden3d/H1'
KEY = 'H1'; S = 3; PADX = 64            # 加闊畫布（4 嘅倍數 → Bayer 抖動同原圖一致）
FOOT = B.FOOT; GROUND_LINE = 262         # 後排物件（籬笆／屋／樹）接地 art y
ZK = 1.6                                 # 前排 art y → 世界 z：z = (y − 292) × 1.6
CAM = dict(target=[0, 30, -72], pitchDeg=30, dist=580, fovDeg=40, yawDeg=0, orbitMinDeg=-10, orbitMaxDeg=10, near=10, far=4000)

def save(a, p):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    Image.fromarray(a).save(p, optimize=True)
def up3(a): return np.repeat(np.repeat(a, S, 0), S, 1)
def hx(h): h = h.lstrip('#'); return np.array([int(h[i:i+2], 16) for i in (0, 2, 4)], float)/255

# ---------------------------------------------------------------- 色盤（H1 V3 調色，無光照）
def graded_lut():
    pal = B.variant_palette(KEY); lut = np.zeros((256, 3)); ok = np.zeros(256, bool)
    for ix, h in pal.items(): lut[ix] = hx(h); ok[ix] = True
    lut = G.grade_fn3(lut[None], G.grade_v3(KEY))[0]
    return (np.clip(lut, 0, 1)*255+.5).astype(np.uint8), ok

# ---------------------------------------------------------------- ① 逐物件捕捉
MARK_B = [('# 籬笆＋灌木', 'fence'), ('# 小屋（右）', 'cottage'), ('# 大樹（左）', 'tree'), ('# 串燈', 'lanterns'),
          ('# 地面：寵物舞台', 'ground'), ('# 草叢點綴', 'ground'), ('# 菜畦（後排）', 'bed'), ('# 燈柱（左）', 'lamp'),
          ('# 花盆', 'pots'), ('# 蘑菇', 'mushrooms'), ('# 花灑', 'can'), ('# 踏腳石', 'ground'), ('# 下半地面小花', 'ground'), ('# ---- fore', None)]
MARK_G = [('# --- 燈泡串', 'lanterns'), ('# --- 籬笆長春藤', 'fence'), ('# --- 小屋', 'cottage'), ('# --- 大樹', 'tree'), ('# --- 菜畦', 'bed'),
          ('# --- 螢火瓶', 'jar'), ('# --- 三葉草叢', 'ground'), ('# --- 草地', 'ground'), ('# --- far', None)]
def _ranges(fn, marks):
    lines, l0 = inspect.getsourcelines(fn); out = []
    for i, ln in enumerate(lines):
        for mk, tag in marks:
            if ln.strip().startswith(mk): out.append((l0+i, tag))
    assert len(out) == len(marks), (fn.__name__, len(out), len(marks))
    return out
def capture():
    """回傳 {tag: index map}（加闊畫布）＋ idx（sky/far/mid/fore）。"""
    saved = (B.LW, B.MX, G.LW, G.MX)
    B.LW = B.LW + 2*PADX; B.MX = B.MX + PADX; G.LW, G.MX = B.LW, B.MX
    rngs = {B.build_index.__code__: _ranges(B.build_index, MARK_B), G.build_index_v3.__code__: _ranges(G.build_index_v3, MARK_G)}
    cap = {}; orig = B.Lay.put
    def put(self, mask, mat, f=0.5, dither=0.35):
        r = orig(self, mask, mat, f, dither); fr = sys._getframe(1)
        while fr is not None and fr.f_code not in rngs: fr = fr.f_back
        if fr is not None and fr.f_locals.get('mid') is self:
            tag = None
            for ln, t in rngs[fr.f_code]:
                if fr.f_lineno >= ln: tag = t
            if tag not in (None, 'ground'):
                O = cap.setdefault(tag, np.zeros_like(self.m)); O[mask] = self.m[mask]
        return r
    B.Lay.put = put
    try:
        G.BULBS.clear(); idx = G.build_index_v3(KEY)
    finally:
        B.Lay.put = orig
    meta = dict(LW=B.LW, MX=B.MX, MY=B.MY)
    B.LW, B.MX, G.LW, G.MX = saved
    # 花盆拆三個
    p = cap.pop('pots'); xs = np.arange(p.shape[1]) - meta['MX']
    for nm, (a, b) in {'pot_L': (-99, 100), 'pot_S': (100, 162), 'pot_R': (162, 999)}.items():
        q = p.copy(); q[:, ~((xs >= a) & (xs < b))] = 0; cap[nm] = q
    # 菜畦：泥面交俾地面（直立 billboard 唔要泥牆）
    cap['bed'][np.isin(cap['bed'], B.IDX['SOIL'])] = 0
    return cap, idx, meta

# 物件設定：groundY＝接地 art y；baseX＝接地中心 art x（None＝bbox 中心）；z＝世界 z
OBJ = {
 'tree':      dict(zh='大樹（連鳥屋、垂藤）', groundY=262, baseX=9,   z=-44, face='cyl',   shadow=True,  layer='mid', light=None),
 'fence':     dict(zh='籬笆＋灌木＋長春藤',   groundY=262, baseX=None, z=-52, face='fixed', shadow=True,  layer='mid', light=None),
 'cottage':   dict(zh='小屋（連窗台花箱）',   groundY=262, baseX=179.5, z=-50, face='fixed', shadow=True, layer='mid', light='window', mesh=True),  # 立體 mesh：見 garden3d_house.py
 'lanterns':  dict(zh='旗串燈籠＋小燈泡',     groundY=None, baseX=None, z=-46, face='fixed', shadow=False, layer='mid', light='lantern_1'),
 'bed':       dict(zh='菜畦（木框＋苗）',     groundY=278, baseX=50,  z=None, face='fixed', shadow=True,  layer='mid', light=None),
 'lamp':      dict(zh='燈柱',                 groundY=306, baseX=24.5, z=None, face='cyl',  shadow=True,  layer='mid', light='lamp'),
 'pot_L':     dict(zh='花盆 L',               groundY=336, baseX=16,  z=None, face='cyl',   shadow=True,  layer='near', light=None),
 'pot_R':     dict(zh='花盆 R',               groundY=326, baseX=178, z=None, face='cyl',   shadow=True,  layer='near', light=None),
 'pot_S':     dict(zh='花盆 S',               groundY=306, baseX=146, z=None, face='cyl',   shadow=True,  layer='mid', light=None),
 'mushrooms': dict(zh='蘑菇叢',               groundY=307, baseX=168, z=None, face='cyl',   shadow=True,  layer='mid', light=None),
 'can':       dict(zh='花灑',                 groundY=318, baseX=58,  z=None, face='cyl',   shadow=True,  layer='near', light=None),
 'jar':       dict(zh='螢火瓶',               groundY=306, baseX=132, z=None, face='cyl',   shadow=True,  layer='mid', light='jar'),
}
EMI_COL = {'LAMP': '#ffd890', 'LANTERN': '#ff9a50', 'WIN': '#ffc870', 'BULB': '#ffe9a0', 'JAR': '#c8ffb0'}
def zof(y): return int(round((y - FOOT[1]) * ZK))

def billboards(cap, meta, lut, ok, write=False):
    """逐物件抽 2D 像素（同舊 billboard 一樣）→ parts[oid]＝(rgba, idx, emis, ent)，畀 garden3d_props 起 mesh；write＝True 先寫舊 billboard png。"""
    objs = []; parts = {}
    MX, MY = meta['MX'], meta['MY']
    for oid, M in OBJ.items():
        if M.get('mesh'): continue                             # 大型建築改做立體 mesh（garden3d_house）
        m = cap[oid]; al = (m > 0) & ok[m]
        ys, xs = np.where(al); r0, r1, c0, c1 = ys.min(), ys.max()+1, xs.min(), xs.max()+1
        sub = m[r0:r1, c0:c1]; a = al[r0:r1, c0:c1]
        rgba = np.zeros(sub.shape + (4,), np.uint8); rgba[..., :3] = lut[sub]; rgba[..., 3] = a*255; rgba[~a, :3] = 0
        h, w = sub.shape; ax0, ay0 = c0 - MX, r0 - MY        # bbox 左上 art 座標
        bx = (ax0 + w/2) if M['baseX'] is None else M['baseX']
        pvx = round((bx - ax0)/w, 4)
        if M['groundY'] is None:                               # 吊喺半空（串燈）：底＝bbox 底，y＝離地高
            pvy = 1.0; yel = GROUND_LINE - (ay0 + h)
        else:
            pvy = round((M['groundY'] - ay0)/h, 4); yel = 0
        z = M['z'] if M['z'] is not None else zof(M['groundY'])
        e = np.zeros_like(rgba); has_e = False
        for mat, col in EMI_COL.items():
            if mat not in B.IDX: continue
            k = np.isin(sub, B.IDX[mat]) & a
            if k.any(): e[k, :3] = (hx(col)*255+.5).astype(np.uint8); e[k, 3] = 255; has_e = True
        f1 = f'objects/{oid}.png'
        if write: save(rgba, f'{OUT}/{f1}'); save(up3(rgba), f'{OUT}/objects/{oid}@3x.png')
        ent = dict(id=oid, type='billboard', zh=M['zh'], file=f1, file3x=f'objects/{oid}@3x.png', x=round(bx - FOOT[0], 1), z=z, w=int(w), h=int(h),
                   pivot=[pvx, pvy], face=M['face'], shadow=M['shadow'], layer=M['layer'])
        if M['face'] == 'fixed': ent['yawDeg'] = 0
        if yel: ent['y'] = int(yel)
        if has_e:
            if write: save(e, f'{OUT}/objects/{oid}_emissive.png'); save(up3(e), f'{OUT}/objects/{oid}_emissive@3x.png')
            ent['emissive'] = f'objects/{oid}_emissive.png'; ent['emissive3x'] = f'objects/{oid}_emissive@3x.png'; ent['emissiveLight'] = M['light']
        ent['srcArt'] = dict(x0=int(ax0), y0=int(ay0), groundY=M['groundY'])
        objs.append(ent); parts[oid] = (rgba, sub, e if has_e else None, ent)
    return objs, parts

# ---------------------------------------------------------------- ② 地面（俯視 256×256 units）
BAY = B.BAYER
def mput(m, mask, mat, f, dither=0.35):
    ids = np.array(B.IDX[mat], np.uint8); n = len(ids)
    H, W = m.shape; bay = BAY[np.arange(H)[:, None] % 4, np.arange(W)[None, :] % 4]
    f = f[mask] if isinstance(f, np.ndarray) else np.full(mask.sum(), f)
    q = np.clip(np.floor(f*n + (bay[mask]-0.5)*dither*2), 0, n-1).astype(int); m[mask] = ids[q]
def pnoise(N, cells, seed):
    """可平鋪 value noise（週期 N px，cells 格）。"""
    g = np.random.default_rng(seed).random((cells, cells)); c = N/cells
    u = (np.arange(N)+.5)/c; i0 = np.floor(u).astype(int); fu = u - i0; fu = fu*fu*(3-2*fu)
    i0 %= cells; i1 = (i0+1) % cells
    a = g[i0][:, i0]*(1-fu)[None, :] + g[i0][:, i1]*fu[None, :]
    b = g[i1][:, i0]*(1-fu)[None, :] + g[i1][:, i1]*fu[None, :]
    return a*(1-fu)[:, None] + b*fu[:, None]
TILE = 64
def grass_tile():
    n1 = pnoise(TILE, 8, 11); n2 = pnoise(TILE, 16, 12); n3 = pnoise(TILE, 4, 13)
    gf = np.clip(0.55 + 0.25*(n1-.5) + 0.3*(n2-.5) + .15*(n3-.5), 0, 1)
    m = np.zeros((TILE, TILE), np.uint8); mput(m, np.ones_like(m, bool), 'GRASS', gf)
    rng = np.random.default_rng(21)
    for (y, x) in zip(*np.where(rng.random((TILE, TILE)) > .975)):       # 草葉高光（俯視：短斜線）
        m[y, x] = B.IDX['GRASS'][-1]; m[(y+1) % TILE, (x+1) % TILE] = B.IDX['GRASS'][0]
    for (y, x) in zip(*np.where(rng.random((TILE, TILE)) > .992)): m[y, x] = B.IDX['MOSS'][-1]
    return m, gf
def ground():
    N = 256; T, gf_t = grass_tile(); m = np.tile(T, (4, 4)); gf = np.tile(gf_t, (4, 4))
    Z, X = np.mgrid[0:N, 0:N].astype(float) + .5 - 128          # 行＝z（上＝−z，遠），列＝x
    rng = np.random.default_rng(7); ao = np.ones((N*S, N*S))
    edge = np.minimum(np.minimum(X+128, 128-X), np.minimum(Z+128, 128-Z))   # 離邊距離
    busy = np.zeros((N, N), bool)
    def ell(cx, cz, rx, rz): return ((X-cx)/rx)**2 + ((Z-cz)/rz)**2 <= 1
    # 寵物舞台（淺草＋苔窩＋邊石）
    gz = (4)*ZK; st = ell(0, gz, 80, 34); mput(m, st, 'GRASS', np.clip(gf+.18, 0, 1)); busy |= ell(0, gz, 36, 16)
    r = np.hypot(X/30, (Z-gz)/13); mput(m, r <= 1, 'MOSS', np.clip(.75-.5*r + .15*(pnoise(N, 32, 3)-.5), 0, 1), .5)
    # 小路：舞台 → 小屋門口
    pts = [(28, -2), (52, -16), (74, -30), (90, -40), (94, -48)]
    path = np.zeros((N, N), bool); pn = pnoise(N, 64, 5)
    for (x0, z0), (x1, z1) in zip(pts[:-1], pts[1:]):
        for t in np.linspace(0, 1, 40):
            cx, cz = x0+(x1-x0)*t, z0+(z1-z0)*t; path |= np.hypot(X-cx, Z-cz) <= 4.6 + 1.6*(pn-.5)*2
    mput(m, path, 'SOIL', np.clip(.62 + .3*(pnoise(N, 48, 6)-.5), 0, 1), .5)
    grav = path & (rng.random((N, N)) > .9); mput(m, grav, 'STONE', .8, 0)
    busy |= nd.binary_dilation(path, iterations=3)
    # 菜畦泥面（俯視：條紋）
    bx0, bx1 = 16-FOOT[0], 84-FOOT[0]; bz0, bz1 = -40, zof(278)
    bed = (X >= bx0) & (X < bx1) & (Z >= bz0) & (Z < bz1)
    mput(m, bed, 'SOIL', .35 + .5*((Z.astype(int) % 4) == 0), 0); busy |= nd.binary_dilation(bed, iterations=3)
    # 門口石板＋屋前碎石帶
    door = (X >= 86) & (X < 102) & (Z >= -49) & (Z < -42); mput(m, door, 'STONE', .55 + .3*(((X.astype(int)) % 5) == 0), 0)
    fnd = (X >= 52) & (X < 114) & (Z >= -53) & (Z < -50); mput(m, fnd, 'STONE', .35, .5)
    busy |= (Z < -40) & (X > 48)
    # 樹頭：根部苔＋泥
    tr = ell(-88, -44, 14, 9); mput(m, tr, 'MOSS', np.clip(.45 + .4*(pnoise(N, 32, 8)-.5), 0, 1), .5)
    mput(m, ell(-88, -44, 6, 3.5), 'SOIL', .5, .3); busy |= ell(-88, -44, 16, 11)
    # 籬笆底：深啲嘅草帶
    fb = (Z >= -56) & (Z < -49) & (X >= -112) & (X < 54); mput(m, fb, 'GRASS', np.clip(gf-.22, 0, 1)); busy |= fb
    # 踏腳石（地面貼花，唔做 billboard）
    for (sx, sy, rx, ry) in B.LAYOUT['stones']:
        cx, cz = sx-FOOT[0], zof(sy); rz = rx*.78
        k = ell(cx, cz, rx, rz); rr = np.hypot((X-cx)/rx, (Z-cz)/rz)
        mput(m, k, 'STONE', np.clip(.72 - .35*rr**2 + .12*(pnoise(N, 64, int(sx))-.5), 0, 1), .3)
        ring = ell(cx, cz, rx+1.5, rz+1.5) & ~k & (rng.random((N, N)) > .55); mput(m, ring, 'MOSS', .7, 0)
        busy |= ell(cx, cz, rx+3, rz+3)
    # 舞台邊石（全圈）
    ring_st = []
    for i in range(30):
        an = i/30*2*math.pi; sx, sz = math.cos(an)*81, gz + math.sin(an)*35
        if np.hypot(sx-28, sz+2) < 10: continue                 # 留小路口
        k = ell(sx, sz, 2.6, 2.2); rr = np.hypot((X-sx)/2.6, (Z-sz)/2.2); mput(m, k, 'STONE', np.clip(.85-.5*rr, 0, 1), 0); ring_st.append((sx, sz))
    busy |= st & ~ell(0, gz, 70, 26) | ell(0, gz, 36, 16)
    fade = np.clip((edge-6)/14, 0, 1)                            # 近邊漸少 → 同外圍 tile 接得順
    ok = ~busy & (rng.random((N, N)) < fade)
    # 三葉草叢
    for _ in range(26):
        cx, cz = rng.uniform(-118, 118), rng.uniform(-118, 118)
        for k_ in range(10):
            x, z = int(cx + rng.integers(-6, 7) + 128), int(cz + rng.integers(-5, 6) + 128)
            if 1 <= x < N-1 and 1 <= z < N-1 and ok[z, x]:
                m[z, x] = B.IDX['CLOVER'][-1]; m[z, x-1] = B.IDX['CLOVER'][0]; m[z+1, x] = B.IDX['CLOVER'][0]
    # 小花
    fl = ['FLOWER_B', 'FLOWER_W', 'FLOWER_W', 'FLOWER_P', 'FLOWER_Y']
    for i in range(150):
        x, z = int(rng.integers(2, N-2)), int(rng.integers(2, N-2))
        if not ok[z, x]: continue
        mat = fl[i % 5]; m[z+1, x] = B.IDX['FGRASS'][0]
        for (dx, dz) in ([(0, 0)] if i % 3 else [(0, 0), (1, 0), (-1, 0), (0, -1)]): m[z+dz, x+dx] = B.IDX[mat][0]
        if i % 3 == 0: m[z, x] = B.IDX['FLOWER_Y'][0]
    # 細石
    for i in range(40):
        x, z = int(rng.integers(2, N-2)), int(rng.integers(2, N-2))
        if ok[z, x]: m[z, x] = B.IDX['STONE'][-1]; m[z, x+1] = B.IDX['STONE'][1]
    # ---- AO（@3x 計，灰階；255＝無遮蔽）
    Z3, X3 = np.mgrid[0:N*S, 0:N*S].astype(float)/S + 1/(2*S) - 128
    occ = np.zeros_like(Z3)
    def blob(cx, cz, rx, rz, a): occ[:] = np.maximum(occ, a*np.exp(-(((X3-cx)/rx)**2 + ((Z3-cz)/rz)**2)*1.6))
    return m, ring_st, (X3, Z3, occ, blob)

def ground_ao(objs, ring_st, aoctx):
    X3, Z3, occ, blob = aoctx
    for o in objs:
        if o['layer'] == 'far' or o.get('y'): continue
        if o.get('type') == 'mesh':                            # 立體 mesh：footprint 四周接地 AO（多邊形用外接矩形）
            if o.get('backfill') or not o.get('footprint'): continue
            fp = o['footprint']
            if fp['type'] == 'rect': fx, fz = fp['x'], fp['z']
            else: P_ = np.array(fp['points']); fx, fz = [P_[:, 0].min(), P_[:, 0].max()], [P_[:, 1].min(), P_[:, 1].max()]
            dx = np.maximum(np.maximum(fx[0] - X3, X3 - fx[1]), 0); dz = np.maximum(np.maximum(fz[0] - Z3, Z3 - fz[1]), 0)
            occ[:] = np.maximum(occ, .5*np.exp(-np.hypot(dx, dz)/3.2)); continue
        if o['face'] == 'cyl':
            rx = {'tree': 11}.get(o['id'], max(4, min(o['w']*.42, 14))); blob(o['x'], o['z'], rx, rx*.7, .45)
        else:
            x0 = o['x'] - o['w']*o['pivot'][0]; x1 = x0 + o['w']
            k = (X3 >= x0) & (X3 < x1); band = np.exp(-((Z3 - o['z'])/3.2)**2)*.42*k
            occ[:] = np.maximum(occ, band)
    for (sx, sy, rx, ry) in B.LAYOUT['stones']:
        cx, cz = sx-FOOT[0], zof(sy); rz = rx*.78
        d = np.hypot((X3-cx)/rx, (Z3-cz)/rz); occ[:] = np.maximum(occ, .28*np.exp(-((d-1.0)/.12)**2))
    for (sx, sz) in ring_st: blob(sx, sz, 3.2, 2.8, .25)
    ao3 = 1 - nd.gaussian_filter(occ, 1.5)
    ao3 = (np.clip(ao3, 0, 1)*255+.5).astype(np.uint8)
    ao1 = (ao3.reshape(256, S, 256, S).astype(float).mean((1, 3))+.5).astype(np.uint8)
    return ao1, ao3

# ---------------------------------------------------------------- ③ 背景板
def backdrops(idx, meta, lut, ok):
    MX, MY = meta['MX'], meta['MY']
    sky = idx['sky'].m.copy(); far = idx['far'].m.copy()
    r1 = GROUND_LINE + MY                                  # 截到地平線（art y 262）
    sky, far = sky[:r1], far[:r1]
    def tile3(m, nosun=False):
        side = m[:, ::-1].copy()
        if nosun:
            k = np.isin(side, B.IDX['SUN'])
            ys, xs = np.where(k); side[ys, xs] = side[ys, np.clip(xs+24, 0, side.shape[1]-1)]
        return np.concatenate([side, m, side], 1)
    sky = tile3(sky, True); far = tile3(far)
    out = {}
    for nm, m in (('bg_sky', sky), ('bg_hills', far)):
        a = (m > 0) & ok[m]; rgba = np.zeros(m.shape+(4,), np.uint8); rgba[..., :3] = lut[m]; rgba[..., 3] = a*255; rgba[~a, :3] = 0
        if nm == 'bg_hills':                               # 只留山：上面透明（已係）；裁走頂部全透明行
            rows = np.where(a.any(1))[0]; rgba = rgba[rows.min():]
        save(rgba, f'{OUT}/backdrop/{nm}.png'); save(up3(rgba), f'{OUT}/backdrop/{nm}@3x.png'); out[nm] = rgba
    # 擺位：企喺地面（y=0），按鏡頭距離放大到同原 2D 構圖一致
    cz_cam = CAM['target'][2] + CAM['dist']*math.cos(math.radians(CAM['pitchDeg']))
    ents = []
    for nm, z, zh in (('bg_sky', -470, '天空背景板（左右鏡像延伸，旁邊兩格冇太陽）'), ('bg_hills', -380, '遠山＋遠樹＋遠屋背景板')):
        h_px, w_px = out[nm].shape[:2]; sc = round((cz_cam - z)/CAM['dist'], 3)
        ents.append(dict(id=nm, zh=zh, file=f'backdrop/{nm}.png', file3x=f'backdrop/{nm}@3x.png', x=0, z=z, w=round(w_px*sc, 1), h=round(h_px*sc, 1),
                         pivot=[0.5, 1.0], face='fixed', yawDeg=0, shadow=False, layer='far', unitsPerPx=sc, unlit=True, type='backdrop'))
    return ents, out


# ---------------------------------------------------------------- ③b 屋後補位（擺鏡 ±10° 先會露出：矮樹叢＋遠樹林剪影）
# 0° 時全部被屋／樹／籬笆擋住（preview 會出 0° 差異圖驗證），所以 0° 構圖同平面版一樣。
BACKFILL = [  # id, kind, w, h, x, z, seed（位置用 preview 嘅可見度搜尋揀：0° 完全被擋／出框，±10° 露出）
    ('bush_bR', 'bush', 32, 19, 82, -198, 11), ('trees_bR', 'trees', 46, 40, 95, -228, 21),     # 屋後（−10° 喺屋左邊露出）
    ('bush_bL', 'bush', 28, 17, -132, -206, 12), ('bush_bL2', 'bush', 24, 15, -126, -176, 13),  # 大樹後（+10° 喺畫面左邊露出）
    ('trees_bL', 'trees', 60, 48, -150, -262, 22),
]
def _bush(w, h, seed):
    rng = np.random.default_rng(seed); m = np.zeros((h, w), np.uint8); Y, X = np.mgrid[0:h, 0:w].astype(float)
    shape = np.zeros((h, w), bool); k = int(max(3, w//8))
    for i in range(k):
        cx = (i + .5)/k*w + rng.uniform(-2, 2); r = rng.uniform(.30, .45)*min(w, 2*h)*(.75 + .5*math.sin(math.pi*(i + .5)/k))
        cy = h - r*.75; shape |= ((X + .5 - cx)/r)**2 + ((Y + .5 - cy)/(r*.85))**2 <= 1
    shape[-2:] |= (X[-2:] > w*.08) & (X[-2:] < w*.92)
    n = pnoise(max(w, h), max(4, max(w, h)//5), seed)[:h, :w]
    f = np.clip(.25 + .55*(1 - Y/h) + .35*(n - .5), 0, 1)
    mput(m, shape, 'LEAF', f, .5)
    hl = shape & (rng.random((h, w)) < .06) & (Y < h*.6); mput(m, hl, 'LEAF', 1., 0)
    if seed % 2: mput(m, shape & (rng.random((h, w)) < .025) & (Y < h*.7), 'BERRY', .6, 0)
    return m
def _trees(w, h, seed):
    rng = np.random.default_rng(seed); m = np.zeros((h, w), np.uint8); Y, X = np.mgrid[0:h, 0:w].astype(float); shape = np.zeros((h, w), bool)
    x = rng.uniform(4, 10)
    while x < w - 4:
        r = rng.uniform(8, 13)*min(1, h/48); top = rng.uniform(0, h*.35) + r; cy = top
        shape |= ((X + .5 - x)/r)**2 + ((Y + .5 - cy)/(r*1.1))**2 <= 1
        shape |= (np.abs(X + .5 - x) < r*.92) & (Y >= cy) & (Y < h)
        x += r*rng.uniform(1.0, 1.5)
    n = pnoise(max(w, h), 10, seed)[:h, :w]
    mput(m, shape, 'LEAF', np.clip(.02 + .4*(1 - Y/h) + .3*(n - .5), 0, 1), .5)
    mput(m, shape & (rng.random((h, w)) < .03) & (Y < h*.5), 'LEAF', .6, 0)
    return m
def backfill(lut, ok):
    ents = {}
    for oid, kind, w, h, x, z, seed in BACKFILL:
        m = (_bush if kind == 'bush' else _trees)(w, h, seed); a = (m > 0) & ok[m]
        rgba = np.zeros(m.shape + (4,), np.uint8); rgba[..., :3] = lut[m]; rgba[..., 3] = a*255; rgba[~a, :3] = 0
        e = dict(id=oid, type='billboard', zh=('屋後矮樹叢（±10° 先見）' if kind == 'bush' else '屋後遠樹林剪影（±10° 先見）'),
                 file=f'objects/{oid}.png', file3x=f'objects/{oid}@3x.png', x=x, z=z, w=w, h=h, pivot=[0.5, 1.0],
                 face='cyl' if kind == 'bush' else 'fixed', shadow=False, layer='mid', backfill=True)
        if kind != 'bush': e['yawDeg'] = 0
        ents[oid] = (rgba, e)
    return ents

# ---------------------------------------------------------------- ④ lights / camera
def lights_json(objs):
    o = {e['id']: e for e in objs}
    def top(e): return e['h']*e['pivot'][1]
    L = []
    lamp = o['lamp']; L.append(dict(id='lamp', zh='燈柱燈頭', x=lamp['x'], y=round(B.LAYOUT['lampPost']['base'][1]-B.LAYOUT['lampPost']['head'][1], 1), z=lamp['z']+1,
                                    color='#ffd890', radius=70, intensity=0.0, intensityNight=1.2, flicker=0.04))
    lan = o['lanterns']
    for i, (lx, ly) in enumerate(B.lantern_pos()):
        L.append(dict(id=f'lantern_{i+1}', zh=f'旗串燈籠 {i+1}', x=lx-FOOT[0], y=GROUND_LINE-(ly+1), z=lan['z']+1, color='#ff9a50', radius=28,
                      intensity=0.0, intensityNight=0.7, flicker=0.12))
    a, b, c, d = B.LAYOUT['cottage']['window']
    L.append(dict(id='window', zh='小屋窗', x=(a+c)/2-FOOT[0], y=GROUND_LINE-(b+d)/2, z=GH.ZF+2, color='#ffc870', radius=48, intensity=0.0, intensityNight=0.8, flicker=0.02))
    L.append(dict(GH.LIGHT_SIDE))
    j = o['jar']; L.append(dict(id='jar', zh='螢火瓶', x=j['x'], y=5, z=j['z']+1, color='#c8ffb0', radius=22, intensity=0.0, intensityNight=0.6, flicker=0.25))
    sun = dict(dir=[0.42, -0.72, 0.55], color='#ffe6b8', intensity=1.0, ambient=dict(color='#cfe0f0', intensity=0.55),
               note='dir＝光行進方向（由太陽射向場景），已正規化；H1 太陽喺左後上方。')
    v = np.array(sun['dir']); sun['dir'] = [round(float(t), 4) for t in v/np.linalg.norm(v)]
    fd = np.array([0.2, -0.12, -0.97]); fill = dict(dir=[round(float(t), 4) for t in fd/np.linalg.norm(fd)], color='#ffe2c4', intensity=0.38, intensityNight=0.0,
        note='補光（方向光，唔投影）：由鏡頭方向略低照入去，補返背光嘅前牆（太陽喺左後上）；全場景 lit 物件都受，唔烘入貼圖')
    return dict(variant=KEY, name='晨光暖調', lights=L, sun=sun, fill=fill,
                night=dict(note='夜間測試用：sun.intensity 0.12、ambient #4a5a90 0.35、燈用 intensityNight', sun=0.12, ambient='#4a5a90', ambientIntensity=0.35),
                fog=dict(color='#ffe8c8', near=420, far=1400))

# ---------------------------------------------------------------- ⑤ 團絨法線（_n）
PETS = [('radiant', 'sprites/tuanrong/motion/atlas_radiant'), ('sprout', 'sprites/tuanrong/motion/atlas_sprout'),
        ('evo_still_radiant', 'sprites/tuanrong/evo6/atlas_evo_still_radiant')]
U = 4
def frame_normals(rgba):
    a = rgba[..., 3] > 0; h, w = a.shape
    if not a.any(): return np.zeros((h, w, 3))
    A4 = np.kron(a, np.ones((U, U), bool))
    lab, n = nd.label(a, np.ones((3, 3))); lab4 = np.kron(lab, np.ones((U, U), int))
    d = nd.distance_transform_edt(np.pad(A4, 1))[1:-1, 1:-1]; H = np.zeros_like(d)
    for i in range(1, n+1):
        k = lab4 == i; dm = max(d[k].max(), 1e-3); t = np.clip(d[k]/dm, 0, 1); H[k] = dm*np.sqrt(1-(1-t)**2)
    lum = (rgba[..., :3].astype(float)/255) @ np.array([.299, .587, .114])
    L4 = np.kron(lum, np.ones((U, U))); H = H + 1.6*U/3*nd.gaussian_filter(L4, 2.5)*A4
    H = nd.gaussian_filter(H, 3)
    gy, gx = np.gradient(H)
    N = np.stack([-gx, gy, np.full_like(H, .9)], -1)           # OpenGL：y 向上 → +dH/dy_img
    N = N.reshape(h, U, w, U, 3).mean((1, 3)); N /= np.linalg.norm(N, axis=-1, keepdims=True)
    N[~a] = (0, 0, 1); return N
def pet_normals():
    rep = []
    for form, base in PETS:
        J = json.load(open(f'{ART}/{base}.json')); im = np.array(Image.open(f'{ART}/{base}.png').convert('RGBA'))
        A = im[..., 3] > 0; Nm = np.zeros(im.shape[:2]+(3,)); filled = np.zeros(A.shape, bool)
        for fn, fr in J['frames'].items():
            f = fr['frame']; x, y, w, h = f['x'], f['y'], f['w'], f['h']
            Nm[y:y+h, x:x+w] = frame_normals(im[y:y+h, x:x+w]); filled[y:y+h, x:x+w] = True
        miss = A & ~filled                                      # extrude 邊：抄最近幀內像素
        if miss.any():
            _, (iy, ix) = nd.distance_transform_edt(~(filled & A), return_indices=True); Nm[miss] = Nm[iy[miss], ix[miss]]
        out = np.zeros_like(im); out[..., :3] = np.clip(np.round((Nm*.5+.5)*255), 0, 255).astype(np.uint8)
        out[..., 3] = im[..., 3]; out[~A, :3] = (128, 128, 255)
        save(out, f'{ART}/{base}_n.png'); rep.append(dict(form=form, color=f'{base}.png', normal=f'{base}_n.png', atlasJson=f'{base}.json',
                                                         size=list(im.shape[1::-1]), frameSize=J['meta'].get('frameSize'), frames=len(J['frames'])))
        if form == 'radiant':                                   # 頭頂太陽 emissive（motion atlas 原本冇）
            r, g, b = [im[..., i].astype(int) for i in range(3)]
            core = A & (r > 240) & (g > 180) & (b < 165)
            e = np.zeros_like(im)
            for fn, fr in J['frames'].items():
                f = fr['frame']; x, y, w, h = f['x'], f['y'], f['w'], f['h']
                sub = np.zeros(A.shape, bool); sub[y-1:y+int(h*.5), x-1:x+w+1] = True
                k = core & sub; k2 = nd.binary_dilation(k) & A & sub & (r > 240) & (g > 230) & (b < 215)
                e[k | k2] = im[k | k2]; e[k | k2, 3] = 255
            save(e, f'{ART}/{base}_emissive.png'); rep[-1]['emissive'] = f'{base}_emissive.png'
        else:
            em = J['meta'].get('emissive')
            if em: rep[-1]['emissive'] = f'{os.path.dirname(base)}/{em}'
    return rep

# ---------------------------------------------------------------- main
def build_all():
    lut, ok = graded_lut()
    cap, idx, meta = capture()
    import shutil
    for d in ('objects', 'mesh', GP.REL):                     # 舊 billboard／舊 house_mesh 全部由 meshes/ 取代
        if os.path.isdir(f'{OUT}/{d}'): shutil.rmtree(f'{OUT}/{d}')
    _, parts = billboards(cap, meta, lut, ok)
    parts['_backfill'] = backfill(lut, ok)
    X = GP.Ctx(B, lut, ok, mput, pnoise); X.OUT = OUT
    objs = GP.build_all(X, parts, GH.build_mesh(cap, meta, lut, ok, mput, GM))
    gm, ring_st, aoctx = ground(); T, _ = grass_tile()
    g1 = lut[gm]; save(g1, f'{OUT}/ground/ground.png'); save(up3(g1), f'{OUT}/ground/ground@3x.png')
    ao1, ao3 = ground_ao(objs, ring_st, aoctx); save(ao1, f'{OUT}/ground/ground_ao.png'); save(ao3, f'{OUT}/ground/ground_ao@3x.png')
    t1 = lut[T]; save(t1, f'{OUT}/ground/ground_tile.png'); save(up3(t1), f'{OUT}/ground/ground_tile@3x.png')
    bents, _ = backdrops(idx, meta, lut, ok)
    pets = pet_normals()
    J = dict(variant=KEY, units='1 unit = 1 個 1x 美術 px；Y 上；地面 XZ；原點＝寵物預設企位；+X 右；+Z 向鏡頭',
             ground=dict(file='ground/ground.png', file3x='ground/ground@3x.png', ao='ground/ground_ao.png', ao3x='ground/ground_ao@3x.png',
                         size=[256, 256], center=[0, 0], uv='u=(x+128)/256，v=(z+128)/256（圖頂＝z −128，遠）', lit=True,
                         outerTile=dict(file='ground/ground_tile.png', file3x='ground/ground_tile@3x.png', size=[64, 64],
                                        note='256 片外圍用：以 (−128,−128) 對齊每 64 units 平鋪，同 256 片無縫（256 片底色就係呢個 tile ×4）；建議外圍平面 ≥ x ±640、z −480…+320')),
             pet=dict(x=0, z=0, face='cyl', shadow=True, layer='mid', billboard=True, radius=10,
                      dir4='sprites/tuanrong/motion/dir4/atlas_radiant_dir4.json',
                      note='團絨係唯一 billboard（面向鏡頭）；用 atlas pivotPx 對準 (x,0,z)；1 px＝1 unit；可喺 XZ 自由行，唔可以入任何 footprint（外擴 pad＋radius）；4 方向幀見 dir4（按移動方向揀 front／back／side，向左 scaleX −1）'),
             objects=objs + bents)
    for p, d in (('objects.json', J), ('lights.json', lights_json(objs)), ('camera.json', dict(CAM, note='target＝鏡頭望住嘅點（寵物略前方，令寵物落喺畫面下半）；pitchDeg 向下俯角；dist＝target→鏡頭距離；fovDeg＝垂直 FOV（40° 時 target 處畫面高≈422 units＝2D 美術格高）；orbit 繞 Y 軸'))):
        with open(f'{OUT}/{p}', 'w') as f: json.dump(d, f, ensure_ascii=False, indent=1)
    with open(f'{OUT}/pets_normals.json', 'w') as f: json.dump(dict(convention='tangent space，OpenGL（綠＝上，Y+），RGB＝n×0.5+0.5；alpha＝色圖 alpha；alpha 0 處 RGB=(128,128,255)', pets=pets,
                                                                  petGlow='emissive × petGlow：awake 1／sleepy .6／sleep・sleepClip・dreamEnter・dreaming 0；淡出 600ms easeInQuad，淡入 400ms easeOutQuad＋150ms pulse 1→1.15→1；場景燈唔受影響'),
                                                             f, ensure_ascii=False, indent=1)
    print('objects', [o['id'] for o in objs], 'backdrops', [b['id'] for b in bents]); print('pets', [p['form'] for p in pets])

if __name__ == '__main__':
    if sys.argv[1:] == ['all']: build_all()
    else: print(__doc__)
