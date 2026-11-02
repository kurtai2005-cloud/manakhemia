#!/usr/bin/env python3
"""preview_garden3d.py — 3D 花園預覽（純 numpy 光線投射；照 objects／lights／camera.json＋mesh json 砌，驗證格式同擺位，非引擎畫面）。
用法：PYTHONDONTWRITEBYTECODE=1 python3 tools/preview_garden3d.py [--src 場景目錄] [--out 輸出目錄] [--cmp billboard 版場景] [--only gif,assembled,occlusion,compare,closeups,meshes,backfill,ground,dir4,normals]
  預設 --src＝$GARDEN3D_SRC 或 art-pet/scenes/garden3d/H1；--out＝$GARDEN3D_OUT 或 /workspace/game-design/pilot3d_h1_mesh；--cmp＝$GARDEN3D_CMP
  mesh 用 garden3d.mesh/2（positions／normals／uvs／indices）；太陽 shadow map（alpha 測試）；寵物係唯一 billboard（dir4 方向幀）。
可 import：load(src) → render(yaw, night, W, H, exclude=…, cam=…, pet=dict(x, z, frame, flip))；blocked(x, z) 查 footprint 碰撞。
"""
import os, sys, json, math, argparse
import numpy as np
from PIL import Image, ImageDraw
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import ui_hd2d_v3_lib as L
ART = os.path.abspath(f'{HERE}/..')
DEF_SRC = os.environ.get('GARDEN3D_SRC') or f'{ART}/scenes/garden3d/H1'
DEF_OUT = os.environ.get('GARDEN3D_OUT') or '/workspace/game-design/pilot3d_h1_mesh'
SRC = PV = None; J = LJ = CJ = None; MESH = {}; TEX = {}
def hx(h): h = h.lstrip('#'); return np.array([int(h[i:i+2], 16) for i in (0, 2, 4)], float)/255
def img(p, mode='RGBA'): return np.array(Image.open(f'{SRC}/{p}').convert(mode)).astype(float)/255
def tex(p):
    if p not in TEX: TEX[p] = img(p)
    return TEX[p]
def load(src=None, out=None):
    """讀場景（objects／lights／camera＋每個 type:mesh 嘅 mesh json）。"""
    global SRC, PV, J, LJ, CJ
    SRC = os.path.abspath(src or DEF_SRC); PV = out or DEF_OUT; TEX.clear(); MESH.clear()
    J = json.load(open(f'{SRC}/objects.json')); LJ = json.load(open(f'{SRC}/lights.json')); CJ = json.load(open(f'{SRC}/camera.json'))
    for o in J['objects']:
        if o.get('type') == 'mesh': MESH[o['id']] = mesh_prep(json.load(open(f"{SRC}/{o['mesh']}")), o)
    shadow_map()
def label(d, xy, s, sz=20, fill=(255, 255, 255), bg=(20, 22, 34)):
    f = L.F('sansb', sz); b = d.textbbox(xy, s, font=f); d.rectangle((b[0]-4, b[1]-3, b[2]+4, b[3]+3), fill=bg); d.text(xy, s, font=f, fill=fill)

def pet_frame(form='radiant', base='sprites/tuanrong/motion/atlas_radiant', fn='idle_01'):
    A = json.load(open(f'{ART}/{base}.json')); f = A['frames'][fn]['frame']; x, y, w, h = f['x'], f['y'], f['w'], f['h']
    c = np.array(Image.open(f'{ART}/{base}.png').convert('RGBA'))[y:y+h, x:x+w].astype(float)/255
    n = np.array(Image.open(f'{ART}/{base}_n.png').convert('RGBA'))[y:y+h, x:x+w].astype(float)/255
    ep = f'{ART}/{base}_emissive.png'
    e = np.array(Image.open(ep).convert('RGBA'))[y:y+h, x:x+w].astype(float)/255 if os.path.exists(ep) else np.zeros_like(c)
    pv = A['frames'][fn].get('pivotPx') or {'x': A['meta']['pivotPx'][0], 'y': A['meta']['pivotPx'][1]}
    return c, n, e, (pv['x']/w, pv['y']/h)

# ---------------------------------------------------------------- mesh（garden3d.mesh/2：positions／normals／uvs／indices，一件一張貼圖）
def mesh_prep(MJ, o):
    """局部三角 → 世界：O,U,V＋uv 基底（V 上）＋幾何法線（剔除）＋著色法線（頂點 normal 平均）。"""
    off = np.array([o['x'], o.get('y', 0), o['z']], float); a = math.radians(o.get('yawDeg', 0)); ca, sa = math.cos(a), math.sin(a)
    R = np.array([[ca, 0, sa], [0, 1, 0], [-sa, 0, ca]])
    P = np.array(MJ['positions'], float).reshape(-1, 3) @ R.T + off; N = np.array(MJ['normals'], float).reshape(-1, 3) @ R.T
    UV = np.array(MJ['uvs'], float).reshape(-1, 2); I = np.array(MJ['indices'], int).reshape(-1, 3)
    v0, v1, v2 = P[I[:, 0]], P[I[:, 1]], P[I[:, 2]]; g = np.cross(v1 - v0, v2 - v0); g /= np.linalg.norm(g, axis=1, keepdims=True)
    ns = N[I].mean(1); ns /= np.linalg.norm(ns, axis=1, keepdims=True)
    return dict(json=MJ, O=v0, U=v1 - v0, V=v2 - v0, uv0=UV[I[:, 0]], du=UV[I[:, 1]] - UV[I[:, 0]], dv=UV[I[:, 2]] - UV[I[:, 0]], g=g, ns=ns,
                T=tex(MJ['texture']), E=tex(MJ['emissive']) if MJ.get('emissive') else None, cast=o.get('castShadow', True), light=o.get('emissiveLight'), Pv=P)
def bary(C, D, O, U, V):
    """射線 C＋tD 同三角 O,U,V → t, s, r（Möller–Trumbore）。"""
    pv = np.cross(D, V); det = pv @ U; det = np.where(np.abs(det) < 1e-12, 1e-12, det); tv = C - O
    s = (tv*pv).sum(-1)/det; q = np.cross(tv, U); r = (D*q).sum(-1)/det; t = (q @ V)/det
    return t, s, r
def msamp(M, k, s, r, T=None):
    T = M['T'] if T is None else T; h, w = T.shape[:2]; uv = M['uv0'][k] + s[:, None]*M['du'][k] + r[:, None]*M['dv'][k]
    return T[np.clip(((1 - uv[:, 1])*h).astype(int), 0, h-1), np.clip((uv[:, 0]*w).astype(int), 0, w-1)]
SM = {}
def shadow_map(res=.5):
    """太陽正交 shadow map（同引擎做法；alpha 測試，葉片卡都投影）。"""
    sd = np.array(LJ['sun']['dir'], float); a = np.cross(sd, [0, 1, 0]); a /= np.linalg.norm(a); b = np.cross(a, sd)
    Ms = [M for M in MESH.values() if M['cast']]
    if not Ms: SM.clear(); return
    allP = np.concatenate([M['Pv'] for M in Ms]); A0, B0 = (allP @ a).min() - 2, (allP @ b).min() - 2
    Wm, Hm = int(((allP @ a).max() - A0 + 2)/res) + 1, int(((allP @ b).max() - B0 + 2)/res) + 1
    dm = np.full((Hm, Wm), np.inf)
    for M in Ms:
        for k in range(len(M['O'])):
            V3 = np.stack([M['O'][k], M['O'][k] + M['U'][k], M['O'][k] + M['V'][k]])
            pa, pb = (V3 @ a - A0)/res, (V3 @ b - B0)/res
            i0, i1 = max(int(pa.min()), 0), min(int(pa.max()) + 2, Wm); j0, j1 = max(int(pb.min()), 0), min(int(pb.max()) + 2, Hm)
            if i1 <= i0 or j1 <= j0: continue
            jj, ii = np.mgrid[j0:j1, i0:i1]; X = A0 + (ii.ravel() + .5)*res; Y = B0 + (jj.ravel() + .5)*res
            Cs = np.outer(X, a) + np.outer(Y, b) - 4000*sd
            t, s_, r_ = bary(Cs, np.broadcast_to(sd, Cs.shape), M['O'][k], M['U'][k], M['V'][k])
            ins = (s_ >= 0) & (r_ >= 0) & (s_ + r_ <= 1)
            if not ins.any(): continue
            ix = np.where(ins)[0]; al = msamp(M, np.full(len(ix), k), s_[ix], r_[ix])[:, 3] > .5; ix = ix[al]
            jj_, ii_ = jj.ravel()[ix], ii.ravel()[ix]; np.minimum.at(dm, (jj_, ii_), t[ix])
    SM.update(a=a, b=b, sd=sd, A0=A0, B0=B0, res=res, dm=dm)
def in_shadow(P, bias=1.2):
    if not SM: return np.zeros(P.shape[:-1], bool)
    i = ((P @ SM['a'] - SM['A0'])/SM['res']).astype(int); j = ((P @ SM['b'] - SM['B0'])/SM['res']).astype(int); dm = SM['dm']
    ok = (i >= 0) & (i < dm.shape[1]) & (j >= 0) & (j < dm.shape[0]); d = (P @ SM['sd']) + 4000
    out = np.zeros(P.shape[:-1], bool); out[ok] = d[ok] > dm[j[ok], i[ok]] + bias; return out

# ---------------------------------------------------------------- render
DIR4 = {}
def pet_dir4(name):
    """dir4 atlas 幀（front_/back_/side_ idle／walk）→ c, n, e, pivot。"""
    if not DIR4:
        base = f"{ART}/sprites/tuanrong/motion/dir4/atlas_radiant_dir4"; DIR4['J'] = json.load(open(f'{base}.json'))
        for k, s_ in (('c', ''), ('n', '_n'), ('e', '_emissive')): DIR4[k] = np.array(Image.open(f'{base}{s_}.png').convert('RGBA')).astype(float)/255
    f = DIR4['J']['frames'][name]['frame']; x, y, w, h = f['x'], f['y'], f['w'], f['h']; pv = DIR4['J']['meta']['pivotPx']
    return tuple(DIR4[k][y:y+h, x:x+w] for k in 'cne') + ((pv[0]/w, pv[1]/h),)
def render(yaw, night=False, W=390, H=844, exclude=(), cam=None, want_depth=False, pet='default'):
    """pet＝'default'（idle 喺原點）／None（冇寵物）／dict(x, z, frame=(c,n,e,pivot), flip, glow＝petGlow 0–1)。"""
    CJ_ = dict(CJ, **(cam or {}))
    tg = np.array(CJ_['target'], float); p = math.radians(CJ_['pitchDeg']); yw = math.radians(yaw)
    C = tg + CJ_['dist']*np.array([math.sin(yw)*math.cos(p), math.sin(p), math.cos(yw)*math.cos(p)])
    fw = (tg-C)/np.linalg.norm(tg-C); rt = np.cross(fw, [0, 1, 0]); rt /= np.linalg.norm(rt); up = np.cross(rt, fw)
    tv = math.tan(math.radians(CJ_['fovDeg'])/2); th = tv*W/H
    camd = dict(C=C, fw=fw, rt=rt, up=up, tv=tv, th=th, W=W, H=H)
    jj, ii = np.mgrid[0:H, 0:W].astype(float)
    D = fw + ((2*(ii+.5)/W-1)*th)[..., None]*rt - ((2*(jj+.5)/H-1)*tv)[..., None]*up
    D /= np.linalg.norm(D, axis=-1, keepdims=True)
    sun = LJ['sun']; sd = np.array(sun['dir']); SI = sun.get('shadowIntensity', .42); sI = (LJ['night']['sun'] if night else sun['intensity']); sc = hx(sun['color'])
    amb = hx(LJ['night']['ambient'])*LJ['night']['ambientIntensity'] if night else hx(sun['ambient']['color'])*sun['ambient']['intensity']
    fl = LJ.get('fill'); fd = np.array(fl['dir']) if fl else np.zeros(3); fI = (fl['intensityNight'] if night else fl['intensity']) if fl else 0; fc = hx(fl['color']) if fl else 0
    lights = [(np.array([l['x'], l['y'], l['z']], float), hx(l['color']), l['radius'], l['intensityNight'] if night else l['intensity']) for l in LJ['lights']]
    LI = {l['id']: (l['intensityNight'] if night else l['intensity']) for l in LJ['lights']}
    def points(P, nrm, wrap=0.):
        acc = np.zeros(P.shape)
        for lp, lc, r, I in lights:
            if I <= 0: continue
            Lv = lp - P; d = np.linalg.norm(Lv, axis=-1); att = np.clip(1-(d/r)**2, 0, 1)**2
            ndl = np.clip(((nrm*Lv).sum(-1)/np.maximum(d, 1e-3) + wrap)/(1+wrap), 0, 1)
            acc += (att*ndl*I)[..., None]*lc
        return acc
    objs = [o for o in J['objects'] if o['id'] not in exclude]
    if pet == 'default': c_, n_, e_, pv_ = pet_frame(); pet = dict(x=J['pet']['x'], z=J['pet']['z'], frame=(c_, n_, e_, pv_), flip=False)
    depth = np.full((H, W), np.inf); col = np.zeros((H, W, 3))
    # 地面（256 片＋外圍 tile）
    g1 = tex(J['ground']['file3x']); ao = img(J['ground']['ao3x'], 'L'); tl = tex(J['ground']['outerTile']['file3x'])
    dy = D[..., 1]; hit = dy < -1e-4; t = np.where(hit, -C[1]/np.where(hit, dy, -1), np.inf)
    P = C + D*t[..., None]; X, Z = P[..., 0], P[..., 2]
    inp = hit & (np.abs(X) < 128) & (np.abs(Z) < 128)
    u = np.clip(((X+128)*3).astype(int), 0, 767); v = np.clip(((Z+128)*3).astype(int), 0, 767)
    tu = (((X+128) % 64)*3).astype(int) % 192; tvv = (((Z+128) % 64)*3).astype(int) % 192
    alb = np.where(inp[..., None], g1[v, u, :3], tl[tvv, tu, :3]); aoo = np.where(inp, ao[v, u], 1.)
    sh = np.ones((H, W))
    blobs = [o for o in objs if o.get('type', 'billboard') == 'billboard' and o.get('shadow') and not o.get('y')]
    if pet: blobs.append(dict(id='pet', x=pet['x'], z=pet['z'], w=40, h=40, face='cyl'))
    for o in blobs:                    # billboard（只剩寵物）用軟影
        if o['face'] == 'cyl':
            r = max(5, min(o['w']*.45, 18)) if o['id'] != 'pet' else 13
            ox, oz = o['x'] + sd[0]/-sd[1]*r*.5, o['z'] + sd[2]/-sd[1]*r*.5
            sh *= 1 - .38*np.exp(-(((X-ox)/r)**2 + ((Z-oz)/(r*.6))**2)*2)
        else:
            x0 = o['x'] - o['w']*o['pivot'][0]; k = (X > x0) & (X < x0+o['w'])
            sh *= 1 - .3*k*np.exp(-(((Z-o['z']-6)/7)**2))
    if any(o.get('type') == 'mesh' for o in objs):
        gi = np.where(hit & (np.abs(X) < 700) & (Z > -600) & (Z < 400)); sg = in_shadow(P[gi]); sh[gi[0][sg], gi[1][sg]] *= 1 - SI
    nG = np.zeros(P.shape); nG[..., 1] = 1
    litg = amb + (sI*max(0, -sd[1])*sh)[..., None]*sc + fI*max(0, -fd[1])*fc
    gcol = alb*aoo[..., None]*litg + alb*points(P, nG)
    m = hit; col[m] = gcol[m]; depth[m] = t[m]
    # billboards（背景板）＋寵物
    items = [o for o in objs if o.get('type', 'billboard') in ('billboard', 'backdrop')]
    if pet:
        pc, pn, pe, ppv = pet['frame']
        if pet.get('flip'): pc, pe = pc[:, ::-1], pe[:, ::-1]; pn = pn[:, ::-1].copy(); pn[..., 0] = 1 - pn[..., 0]
        items.append(dict(id='pet', x=pet['x'], z=pet['z'], w=pc.shape[1], h=pc.shape[0], pivot=list(ppv), face='cyl', layer='mid'))
    for o in items:
        O = np.array([o['x'], o.get('y', 0), o['z']], float)
        if o['face'] == 'cyl':
            n = np.array([C[0]-O[0], 0, C[2]-O[2]]); n /= np.linalg.norm(n)
        else:
            a = math.radians(o.get('yawDeg', 0)); n = np.array([math.sin(a), 0, math.cos(a)])
        rv = np.array([n[2], 0, -n[0]])
        dn = D @ n; tt = ((O-C) @ n)/np.where(np.abs(dn) < 1e-6, 1e-6, dn)
        Pb = C + D*tt[..., None]; s = (Pb-O) @ rv; hh = Pb[..., 1]-O[1]
        uu = s + o['pivot'][0]*o['w']; vv = o['pivot'][1]*o['h'] - hh
        ins = (tt > 0) & (uu >= 0) & (uu < o['w']) & (vv >= 0) & (vv < o['h']) & (tt < depth)
        if not ins.any(): continue
        if o['id'] == 'pet':
            iu = uu[ins].astype(int); iv = vv[ins].astype(int); c = pc[iv, iu]; nn = pn[iv, iu]; e = pe[iv, iu]
        else:
            T = tex(o['file3x']); sc3 = T.shape[1]/o['w']
            iu = np.clip((uu[ins]*sc3).astype(int), 0, T.shape[1]-1); iv = np.clip((vv[ins]*T.shape[0]/o['h']).astype(int), 0, T.shape[0]-1)
            c = T[iv, iu]; e = tex(o['emissive3x'])[iv, iu] if o.get('emissive3x') else None
        a = c[:, 3] > .5; idx = np.where(ins); sel = (idx[0][a], idx[1][a]); c = c[a]
        if o.get('unlit'):
            out = c[:, :3]*(np.array([.22, .26, .42]) if night else 1)
        else:
            if o['id'] == 'pet':
                nt = nn[a, :3]*2-1; nw = nt[:, :1]*rv + nt[:, 1:2]*np.array([0, 1, 0]) + nt[:, 2:3]*n
            else:
                nw = np.tile(.7*n + .55*np.array([0, 1, 0]), (len(c), 1)); nw /= np.linalg.norm(nw, axis=-1, keepdims=True)
            lam = np.clip(nw @ -sd, 0, 1)*.8 + .2
            out = c[:, :3]*(amb + (sI*lam)[:, None]*sc) + c[:, :3]*points(Pb[sel], nw, .5)
            if o['id'] == 'pet':
                out = out + e[a][:, :3]*(e[a][:, 3:4])*.6*pet.get('glow', 1.)          # petGlow（awake 1）
            elif e is not None:
                out = out + e[a][:, :3]*e[a][:, 3:4]*LI.get(o.get('emissiveLight'), 0)
        col[sel] = out; depth[sel] = tt[sel]
    # 立體 mesh（逐三角：螢幕包圍盒內先做射線測試＝光柵化）
    for o in objs:
        if o.get('type') != 'mesh': continue
        M = MESH[o['id']]; Ei = LI.get(M['light'], 0)
        for k in range(len(M['O'])):
            V3 = np.stack([M['O'][k], M['O'][k] + M['U'][k], M['O'][k] + M['V'][k]])
            dz = (V3 - C) @ fw
            if (dz < 1).any(): continue
            pi_, pj_, _ = project(camd, V3)
            i0, i1 = max(int(pi_.min()) - 1, 0), min(int(pi_.max()) + 2, W); j0, j1 = max(int(pj_.min()) - 1, 0), min(int(pj_.max()) + 2, H)
            if i1 <= i0 or j1 <= j0: continue
            Ds = D[j0:j1, i0:i1]
            if (Ds.reshape(-1, 3) @ M['g'][k]).min() >= 0: continue          # 背面剔除
            tt, s_, r_ = bary(C, Ds, M['O'][k], M['U'][k], M['V'][k])
            ins = (tt > 0) & (s_ >= 0) & (r_ >= 0) & (s_ + r_ <= 1) & (tt < depth[j0:j1, i0:i1] - 1e-3) & ((Ds @ M['g'][k]) < 0)
            if not ins.any(): continue
            lj, li = np.where(ins); kk = np.full(len(lj), k); c = msamp(M, kk, s_[ins], r_[ins]); a = c[:, 3] > .5
            if not a.any(): continue
            lj, li, c = lj[a], li[a], c[a]; sel = (lj + j0, li + i0); Pq = C + D[sel]*tt[ins][a][:, None]; n = M['ns'][k]
            shk = (~in_shadow(Pq + M['g'][k]*.3)).astype(float) if (sI > 0) else np.ones(len(Pq))
            lam = np.clip(n @ -sd, 0, 1)*(1 - min(1., SI/.42)*(1 - shk)); lf = max(0., float(n @ -fd))
            sky = .75 + .25*n[1]; nb = np.broadcast_to(n, Pq.shape)
            out = c[:, :3]*(amb*sky + (sI*lam)[:, None]*sc + fI*lf*fc) + c[:, :3]*points(Pq, nb)
            if M['E'] is not None and Ei > 0:
                e = msamp(M, kk[a], s_[ins][a], r_[ins][a], M['E']); out = out + e[:, :3]*e[:, 3:4]*Ei
            col[sel] = out; depth[sel] = tt[ins][a]
    # 霧
    fg = LJ['fog']; fk = np.clip((depth-fg['near'])/(fg['far']-fg['near']), 0, 1)*(.25 if night else .45)
    fcol = hx(fg['color']) if not night else np.array([.16, .2, .36])
    col = np.where(np.isfinite(depth)[..., None], col*(1-fk[..., None]) + fcol*fk[..., None], fcol)
    out = (np.clip(col, 0, 1)*255+.5).astype(np.uint8)
    return (out, dict(camd, depth=depth)) if want_depth else out
def project(cam, P):
    """世界點 (N,3) → 螢幕 (i, j, 距離)；配合 render(want_depth=True) 嘅 cam。"""
    d = P - cam['C']; z = d @ cam['fw']; x = d @ cam['rt']; y = d @ cam['up']
    i = ((x/z)/cam['th'] + 1)/2*cam['W'] - .5; j = (1 - (y/z)/cam['tv'])/2*cam['H'] - .5
    return i, j, np.linalg.norm(d, axis=-1)
def visible_frac(cam, x, z, w, h):
    """一塊面向鏡頭嘅 w×h 板（底中 x,z）有幾多比例冇被擋（用 depth）。"""
    uu, vv = np.meshgrid(np.linspace(-w/2+1, w/2-1, 9), np.linspace(1, h-1, 7)); P = np.stack([x + uu.ravel(), vv.ravel(), np.full(uu.size, z)], 1)
    i, j, dist = project(cam, P); ii, jj = np.round(i).astype(int), np.round(j).astype(int)
    on = (ii >= 0) & (ii < cam['W']) & (jj >= 0) & (jj < cam['H'])
    vis = np.zeros(len(P), bool); vis[on] = dist[on] < cam['depth'][jj[on], ii[on]] - 1
    return vis.mean(), on.mean()

# ---------------------------------------------------------------- 碰撞（footprint）
def fp_dist(o, x, z):
    """點 (x,z) 去物件 footprint 嘅距離（入面＝負）；冇 footprint → inf。"""
    f = o.get('footprint')
    if not f: return math.inf
    if f['type'] == 'rect':
        (x0, x1), (z0, z1) = f['x'], f['z']; dx = max(x0 - x, 0, x - x1); dz = max(z0 - z, 0, z - z1)
        return math.hypot(dx, dz) if (dx or dz) else -min(x - x0, x1 - x, z - z0, z1 - z)
    P = np.array(f['points'], float); Q = np.roll(P, -1, 0); d = math.inf; ins = False
    for (ax, az), (bx, bz) in zip(P, Q):
        ex, ez = bx - ax, bz - az; t = np.clip(((x-ax)*ex + (z-az)*ez)/max(ex*ex + ez*ez, 1e-9), 0, 1); d = min(d, math.hypot(x - ax - t*ex, z - az - t*ez))
        if (az > z) != (bz > z) and x < ax + (z - az)*ex/(ez or 1e-9): ins = not ins
    return -d if ins else d
def blocked(x, z, r=None):
    """寵物（半徑 r，預設 objects.json pet.radius）企 (x,z) 會唔會撞任何 footprint（含 pad）。回撞到嘅 id list。"""
    r = J['pet'].get('radius', 10) if r is None else r
    return [o['id'] for o in J['objects'] if fp_dist(o, x, z) < o.get('footprint', {}).get('pad', 0) + r]

# ---------------------------------------------------------------- 預覽圖
def views():
    a, b = CJ['orbitMinDeg'], CJ['orbitMaxDeg']
    return [(a, False, f'擺鏡 {a:+g}°'), (0, False, '0°（預設）'), (b, False, f'擺鏡 {b:+g}°'), (0, True, '夜間燈光 0°')]
def sheet(rows, title, W=390, H=844, lab=0):
    """rows＝[(行名, [(圖, 格名)…])]"""
    pad = 12; top = 64; n = max(len(r[1]) for r in rows)
    sh = Image.new('RGB', (lab + n*(W+pad)+pad, top + len(rows)*(H+pad)), (24, 26, 38)); d = ImageDraw.Draw(sh); label(d, (pad, 14), title, 22)
    for i, (rn, cells) in enumerate(rows):
        y = top + i*(H+pad)
        if rn: label(d, (pad, y + H//2 - 14), rn, 20)
        for j, (im, s) in enumerate(cells):
            x = lab + pad + j*(W+pad); sh.paste(Image.fromarray(im), (x, y)); label(d, (x+8, y+8), s, 18 if len(s) > 14 else 20)
    return sh
def assembled():
    cells = [(render(yw, nt), s) for yw, nt, s in views()]
    sheet([('', cells)], '3D 花園 H1（全 mesh 版：寵物 billboard，其餘立體）— 照 objects／lights／camera.json＋meshes/*.json 砌（numpy 預覽，非引擎）').save(f'{PV}/assembled_3d.png', optimize=True)
OCC = [(-80, -8, -10, '樹前 −10°'), (-90, -72, -10, '行到樹＋籬笆後 −10°'), (-90, -72, 0, '同位 0°')]
def occlusion():
    """寵物行到樹後被遮：前／後／後＋擺鏡；每格右下 ×2 放大。"""
    cells = []; c, n, e, pv = pet_dir4('front_idle_01'); out = []
    for x, z, yw, s in OCC:
        hit = blocked(x, z); assert not hit, (x, z, hit)
        im, cam = render(yw, pet=dict(x=x, z=z, frame=(c, n, e, pv)), want_depth=True)
        _, cam0 = render(yw, pet=None, want_depth=True); vf, on = visible_frac(cam0, x, z, 30, 30); vf = vf/max(on, 1e-6); out.append(round(vf, 2))
        i, j, _ = project(cam, np.array([[x, 22, z]], float)); i, j = int(np.clip(i[0], 60, 329)), int(np.clip(j[0], 60, 783))
        crop = Image.fromarray(im).crop((i-60, j-60, i+60, j+60)).resize((240, 240), Image.NEAREST)
        pil = Image.fromarray(im); d = ImageDraw.Draw(pil); d.rectangle((i-60, j-60, i+60, j+60), outline=(255, 70, 200), width=2)
        pil.paste(crop, (390-250, 844-250)); d.rectangle((390-251, 844-251, 390-10, 844-10), outline=(255, 70, 200), width=2)
        cells.append((np.array(pil), f'{s}｜可見 {int(vf*100)}%'))
    sheet([('', cells)], '寵物喺 XZ 行：行到樹幹／籬笆後面被 mesh 深度遮住（洋紅框＝放大 ×2；footprint 已驗唔撞）').save(f'{PV}/occlusion_pet_tree.png', optimize=True)
    return out
def compare(cmp_src):
    """同一鏡頭：billboard 版（5831554a 場景）對 mesh 版。"""
    vs = views(); mesh = [(render(yw, nt), s) for yw, nt, s in vs]
    keep = SRC; load(cmp_src, PV); bb = [(render(yw, nt), s) for yw, nt, s in vs]; load(keep, PV)
    sheet([('billboard', bb), ('mesh 版', mesh)], '對比：上＝billboard 版（art/garden3d-h1 @ 5831554a）；下＝全 mesh 版（今次）— 0° 構圖應一樣，擺鏡先見立體', lab=120).save(f'{PV}/compare_billboard_vs_mesh.png', optimize=True)
def closeups():
    for oid, cy, dist in (('cottage', 55, 300), ('tree', 110, 360)):
        o = next(o for o in J['objects'] if o['id'] == oid); MJ = MESH[oid]['json']
        cam = dict(target=[o['x'], cy, o['z'] + 20], dist=dist); a, z = CJ['orbitMinDeg'], CJ['orbitMaxDeg']
        cells = [(render(y, n, 330, 420, cam=cam, pet=None), s) for y, n, s in ((a, False, f'{a:+g}°'), (0, False, '0°'), (z, False, f'{z:+g}°'), (0, True, '夜間'))]
        sheet([('', cells)], f"{MJ['zh']} 特寫（鏡頭拉近 dist {dist}；pitch 同正式；{MJ['triangleCount']} 三角）", 330, 420).save(f'{PV}/closeup_{oid}.png', optimize=True)
def meshes_sheet():
    """每件 mesh 嘅貼圖 atlas（×2）＋三角數＋footprint。"""
    ms = [o for o in J['objects'] if o.get('type') == 'mesh']; W = 1560; zm = 2; x = 24; y = 80; rowh = 0; cells = []
    for o in ms:
        MJ = MESH[o['id']]['json']; im = Image.open(f"{SRC}/{MJ['texture']}").convert('RGBA'); im = im.resize((im.width*zm, im.height*zm), Image.NEAREST)
        w = max(im.width, 230) + 24
        if x + w > W: x = 24; y += rowh; rowh = 0
        cells.append((o, MJ, im, x, y)); x += w; rowh = max(rowh, im.height + 96)
    sh = Image.new('RGB', (W, y + rowh + 20), (52, 58, 76)); d = ImageDraw.Draw(sh)
    label(d, (24, 20), f'meshes/*.json＋.glb（garden3d.mesh/2）— 每件一張 2 次方像素 atlas（×2 顯示；黃框＝有 _emissive）；總三角 {sum(MESH[o["id"]]["json"]["triangleCount"] for o in ms)}', 22)
    for o, MJ, im, X0, Y0 in cells:
        d.rectangle((X0-1, Y0-1, X0+im.width, Y0+im.height), fill=(70, 76, 96)); sh.paste(im, (X0, Y0), im)
        if MJ.get('emissive'): d.rectangle((X0-2, Y0-2, X0+im.width+1, Y0+im.height+1), outline=(255, 214, 90), width=2)
        tw, th = MJ['textureSize'] if isinstance(MJ['textureSize'], list) else (im.width//zm, im.height//zm)
        label(d, (X0, Y0 + im.height + 10), f"{o['id']} {MJ['triangleCount']}△ {tw}×{th}", 18)
        label(d, (X0, Y0 + im.height + 44), ('有 footprint' if o.get('footprint') else '冇碰撞') + ('／補位' if o.get('backfill') else ''), 18)
    sh.save(f'{PV}/meshes_sheet.png', optimize=True)
def backfill():
    bf = tuple(o['id'] for o in J['objects'] if o.get('backfill'))
    if not bf: return
    a, b = CJ['orbitMinDeg'], CJ['orbitMaxDeg']; rows = []
    for nm, ex in (('冇補位', bf), ('有補位', ())):
        rows.append((nm, [(render(a, False, exclude=ex), f'{a:+g}°'), (render(b, False, exclude=ex), f'{b:+g}°')]))
    z0 = render(0, False, exclude=bf); z1 = render(0, False); dif = np.abs(z0.astype(int) - z1.astype(int)).max(-1) > 0
    hm = (z1*.35).astype(np.uint8); hm[dif] = [255, 40, 200]
    rows[0][1].append((z0, '0° 冇補位')); rows[1][1].append((hm, f'0° 差異 {int(dif.sum())} px'))
    sheet(rows, '屋後補位（矮樹叢＋遠樹林剪影 mesh 卡，擺鏡先見）：上＝冇、下＝有；右下＝0° 差異（洋紅＝有變）', lab=110).save(f'{PV}/backfill_check.png', optimize=True)
    return int(dif.sum())
def ground_top():
    g = Image.open(f"{SRC}/{J['ground']['file3x']}").convert('RGB'); ao = Image.open(f"{SRC}/{J['ground']['ao3x']}").convert('L')
    ga = (np.array(g).astype(float)*(np.array(ao).astype(float)[..., None]/255)).astype(np.uint8)
    W = 768*2 + 72; sh = Image.new('RGB', (W, 768+120), (30, 32, 44)); d = ImageDraw.Draw(sh)
    label(d, (24, 18), '地面 768×768（@3x）：左＝ground＋AO＋footprint（碰撞）＋GIF 行路；右＝ground_ao', 22)
    a = Image.fromarray(ga); da = ImageDraw.Draw(a); T = lambda x, z: ((x+128)*3, (z+128)*3)
    for o in J['objects']:
        if o.get('type') == 'backdrop': continue
        f = o.get('footprint'); cx, cz = T(o['x'], o['z'])
        if f and f['type'] == 'rect':
            da.rectangle((*T(f['x'][0], f['z'][0]), *T(f['x'][1], f['z'][1])), outline=(255, 200, 60), width=3)
            p_ = f['pad']; da.rectangle((*T(f['x'][0]-p_, f['z'][0]-p_), *T(f['x'][1]+p_, f['z'][1]+p_)), outline=(255, 120, 40), width=1)
        elif f:
            da.polygon([T(*q) for q in f['points']], outline=(255, 200, 60), width=3)
        if -128 < o['x'] < 128 and -128 < o['z'] < 128:
            da.ellipse((cx-6, cz-6, cx+6, cz+6), outline=(255, 255, 255), width=2)
            fnt = L.F('sansb', 18); da.text((cx+8, cz-24), o['id'], font=fnt, fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
    pts = [T(x, z) for x, z in LOOP + LOOP[:1]]; da.line(pts, fill=(80, 220, 255), width=3)
    for x, z, _, _ in OCC: q = T(x, z); r = J['pet'].get('radius', 10)*3; da.ellipse((q[0]-r, q[1]-r, q[0]+r, q[1]+r), outline=(255, 70, 200), width=3)
    sh.paste(a, (24, 72)); sh.paste(ao.convert('RGB'), (24+768+24, 72))
    label(d, (24, 72+768+14), '黃框＝footprint；橙細框＝外擴 pad；青線＝GIF 行一圈路線；洋紅圈＝遮擋格寵物位（半徑 10）；上＝−Z（遠）', 18)
    sh.save(f'{PV}/ground_top.png', optimize=True)
def dir4_sheet():
    """radiant 4 方向：front／back／side（右）／side 鏡像（左）× idle 4＋walk 6；每格色圖＋法線。"""
    zoom = 3; fs = 64*zoom; rows = [('front', 'front', False), ('back', 'back', False), ('side 右', 'side', False), ('side 左（鏡像）', 'side', True)]
    fns = [f'idle_0{i}' for i in range(1, 5)] + [f'walk_0{i}' for i in range(1, 7)]
    W = 200 + 10*(fs+8); H = 70 + len(rows)*(2*(fs+6)+24)
    sh = Image.new('RGB', (W, H), (40, 44, 60)); d = ImageDraw.Draw(sh); y = 70
    label(d, (24, 18), '團絨 radiant 4 方向（64px；pivot (32,61)；alpha 0/255）：每方向上＝色圖、下＝_n 法線；左＝右鏡像＋R 反轉', 22)
    for nm, k, flip in rows:
        label(d, (24, y + fs//2), nm, 18)
        for j, fn in enumerate(fns):
            c, n, e, pv = pet_dir4(f'{k}_{fn}')
            if flip: c = c[:, ::-1]; n = n[:, ::-1].copy(); n[..., 0] = np.where(n[..., 3] > 0, 1 - n[..., 0], 0)
            for r, arr in enumerate((c, n)):
                im = Image.fromarray((arr*255+.5).astype(np.uint8)).resize((fs, fs), Image.NEAREST); X0 = 196 + j*(fs+8); Y0 = y + r*(fs+6)
                d.rectangle((X0, Y0, X0+fs-1, Y0+fs-1), fill=(64, 70, 92)); sh.paste(im, (X0, Y0), im)
                d.line((X0 + pv[0]*fs - 6, Y0 + pv[1]*fs, X0 + pv[0]*fs + 6, Y0 + pv[1]*fs), fill=(255, 60, 60))
        y += 2*(fs+6) + 24
    sh.save(f'{PV}/pet_dir4_sheet.png', optimize=True)
LOOP = [(-22, -4), (16, -4), (16, 24), (-22, 24)]          # 寵物行一圈（逆時針睇落：右→前→左→後）
def walk_path(step=2.):
    pts = []
    for (ax, az), (bx, bz) in zip(LOOP, LOOP[1:] + LOOP[:1]):
        L_ = math.hypot(bx-ax, bz-az); n = int(round(L_/step))
        for i in range(n): pts.append((ax + (bx-ax)*i/n, az + (bz-az)*i/n, bx-ax, bz-az))
    return pts
def dir_of(dx, dz):
    """移動方向 → (方向幀前綴, 鏡像)：|dx|≥|dz| 用 side（向左鏡像）；+Z 向鏡頭＝front；−Z＝back。"""
    if abs(dx) >= abs(dz): return 'side', dx < 0
    return ('front', False) if dz > 0 else ('back', False)
def walk_gif(yaw=0, crop=(0, 300, 390, 760), scale=1):
    """GIF：寵物沿 LOOP 行一圈，按方向換 front／back／side（左＝鏡像），walk 10fps（每格 100ms，每格行 2 unit）；頭尾各 idle 4 格。"""
    pts = walk_path(); frames = []; info = []
    for x, z, _, _ in pts:
        hit = blocked(x, z); assert not hit, (x, z, hit)
    seq = [(LOOP[0][0], LOOP[0][1], 'front', False, f'idle_0{i}') for i in (1, 2, 3, 4)]
    for i, (x, z, dx, dz) in enumerate(pts):
        k, fl = dir_of(dx, dz); seq.append((x, z, k, fl, f'walk_0{i % 6 + 1}'))
    for x, z, k, fl, fn in seq:
        c, n, e, pv = pet_dir4(f'{k}_{fn}'); im = render(yaw, pet=dict(x=x, z=z, frame=(c, n, e, pv), flip=fl))
        pil = Image.fromarray(im).crop(crop)
        if scale != 1: pil = pil.resize((pil.width*scale, pil.height*scale), Image.NEAREST)
        dd = ImageDraw.Draw(pil); label(dd, (8, 8), f"{k}{'（鏡像）' if fl else ''} {fn}", 18); frames.append(pil); info.append(k + ('L' if fl else ''))
    pal = [f.convert('P', palette=Image.ADAPTIVE, colors=128) for f in frames]
    pal[0].save(f'{PV}/pet_walk_loop.gif', save_all=True, append_images=pal[1:], duration=[250]*4 + [100]*(len(pal)-4), loop=0, optimize=True, disposal=1)
    strip = [frames[i] for i in range(0, len(frames), max(1, len(frames)//8))][:8]
    st = Image.new('RGB', (sum(f.width for f in strip) + 8*len(strip), strip[0].height), (24, 26, 38)); xx = 0
    for f in strip: st.paste(f, (xx, 0)); xx += f.width + 8
    st.save(f'{PV}/pet_walk_loop_strip.png', optimize=True)
    return dict(frames=len(frames), dirs={k: info.count(k) for k in set(info)})

def normals_pets():
    PJ = json.load(open(f'{SRC}/pets_normals.json'))['pets']; zoom = 4
    rows = []
    for p in PJ:
        base = p['color'][:-4]; A = json.load(open(f'{ART}/{base}.json'))
        fns = [f'idle_0{i}' for i in range(1, 5)] + [f'walk_0{i}' for i in range(1, 7)]
        rows.append((p, base, A, fns))
    fs = max(r[2]['frames']['idle_01']['frame']['w'] for r in rows)*zoom
    W = 24 + 140 + 10*(fs+8); Hh = 70 + len(rows)*(3*(fs+8)+50)
    sh = Image.new('RGB', (W, Hh), (40, 44, 60)); d = ImageDraw.Draw(sh)
    label(d, (24, 18), '團絨法線 _n（idle×4＋walk×6）：每形態三行＝色圖／法線（OpenGL 綠＝上）／重打光（左上光）', 22)
    y = 70; Ld = np.array([-.55, .6, .58]); Ld /= np.linalg.norm(Ld)
    for p, base, A, fns in rows:
        label(d, (24, y), f"{p['form']}（{A['meta'].get('frameSize')}px）", 18); y += 40
        C = np.array(Image.open(f'{ART}/{base}.png').convert('RGBA')); N = np.array(Image.open(f'{ART}/{base}_n.png').convert('RGBA'))
        for j, fn in enumerate(fns):
            f = A['frames'][fn]['frame']; x0, y0, w, h = f['x'], f['y'], f['w'], f['h']
            c = C[y0:y0+h, x0:x0+w].astype(float)/255; n = N[y0:y0+h, x0:x0+w].astype(float)/255
            nn = n[..., :3]*2-1; lam = np.clip(nn @ Ld, 0, 1)
            lit = c.copy(); lit[..., :3] = np.clip(c[..., :3]*(.35 + .85*lam[..., None]), 0, 1)
            for r, arr in enumerate((c, n, lit)):
                im = Image.fromarray((arr*255+.5).astype(np.uint8)).resize((w*zoom, h*zoom), Image.NEAREST)
                X0 = 164 + j*(fs+8); Y0 = y + r*(fs+8); d.rectangle((X0, Y0, X0+fs-1, Y0+fs-1), fill=(64, 70, 92))
                sh.paste(im, (X0, Y0), im)
        for r, s in enumerate(('色圖', '法線', '重打光')): label(d, (24, y + r*(fs+8) + fs//2 - 12), s, 18)
        y += 3*(fs+8) + 10
    sh.save(f'{PV}/normals_pets.png', optimize=True)


# ---------------------------------------------------------------- 動態 GIF（鏡頭跟寵物＋慢擺；夜間燈＋螢火蟲）
ROUTE2 = [(-104, -14), (-132, -14), (-132, -76), (-70, -76)]   # 樹前 → 繞籬笆尾 → 行到樹幹＋籬笆後（被遮）→ 原路返
def route_pts(route, n):
    """來回路線平均切 n 點 → [(x, z, dx, dz, 已行距離)]。"""
    R = route + route[-2::-1]; seg = [(a, b, math.dist(a, b)) for a, b in zip(R, R[1:])]; tot = sum(s_[2] for s_ in seg); out = []
    for i in range(n):
        d = tot*i/n; acc = 0
        for a, b, L_ in seg:
            if d <= acc + L_ or (a, b, L_) == seg[-1]:
                t = (d - acc)/L_; out.append((a[0] + (b[0]-a[0])*t, a[1] + (b[1]-a[1])*t, b[0]-a[0], b[1]-a[1], d)); break
            acc += L_
    return out, tot
FLIES = np.random.default_rng(7).uniform([-165, 10, -110], [95, 70, 40], (26, 3)); FPH = np.random.default_rng(8).uniform(0, 2*math.pi, (26, 3))
def fireflies(im, cam, t):
    """螢火蟲：世界座標飄（sin 漂移），投影＋深度測試；1px 亮芯＋十字微光（只預覽，未入 lights）。"""
    P = FLIES + np.stack([9*np.sin(t*1.3 + FPH[:, 0]), 5*np.sin(t*1.9 + FPH[:, 1]), 7*np.sin(t*1.1 + FPH[:, 2])], 1)
    i, j, dist = project(cam, P); out = im.astype(float); blink = .55 + .45*np.sin(t*5 + FPH[:, 0]*3)
    for k in range(len(P)):
        ii, jj = int(round(i[k])), int(round(j[k]))
        if not (1 <= ii < cam['W']-1 and 1 <= jj < cam['H']-1) or dist[k] > cam['depth'][jj, ii]: continue
        b = blink[k]; c = np.array([255, 246, 150.])
        for dj in range(-2, 3):
            for di in range(-2, 3):
                r2 = di*di + dj*dj; w = 1. if r2 == 0 else (.6 if r2 == 1 else (.25 if r2 <= 2 else (.1 if r2 <= 4 else 0)))
                if w and 0 <= jj+dj < cam['H'] and 0 <= ii+di < cam['W']:
                    out[jj+dj, ii+di] = out[jj+dj, ii+di]*(1 - w*b) + c*w*b
    return out.astype(np.uint8)
def route_gif(fn, night=False, flies=False, secs=4.0, ms=70, crop=(0, 250, 390, 690), colors=96, W=390, follow=(.8, 0., .45)):
    """寵物來回 ROUTE2（dir4 轉身、樹幹／籬笆遮）＋鏡頭 −10°→+10°→−10° 慢擺；鏡頭 target 跟寵物（Octopath 式跟拍，pitch 固定）。"""
    n = int(round(secs*1000/ms)); pts, tot = route_pts(ROUTE2, n); a0, a1 = CJ['orbitMinDeg'], CJ['orbitMaxDeg']
    for x, z, _, _, _ in pts:
        hit = blocked(x, z); assert not hit, (x, z, hit)
    frames = []; tg0 = np.array(CJ['target'], float); fx = fz = None
    for k, (x, z, dx, dz, d) in enumerate(pts):
        tt = k/n; yw = (a0 + a1)/2 - (a1 - a0)/2*math.cos(2*math.pi*tt)
        dk, fl = dir_of(dx, dz); fn_ = f'{dk}_walk_0{int(d/2) % 6 + 1}'
        tx, tz = follow[0]*x + follow[1], follow[2]*z      # 跟拍（緩和）
        fx = tx if fx is None else fx + (tx - fx)*.35; fz = tz if fz is None else fz + (tz - fz)*.35
        cam = dict(target=[tg0[0] + fx, tg0[1], tg0[2] + fz])
        c, nn, e, pv = pet_dir4(fn_)
        im, cm = render(yw, night, W=W, cam=cam, want_depth=True, pet=dict(x=x, z=z, frame=(c, nn, e, pv), flip=fl, glow=1.))
        if flies: im = fireflies(im, cm, tt*secs)
        pil = Image.fromarray(im).crop(crop); dd = ImageDraw.Draw(pil)
        label(dd, (8, 8), f"{'夜間' if night else '日間'} 擺鏡 {yw:+.0f}°｜{dk}{'（鏡像）' if fl else ''}", 18); frames.append(pil)
    big = Image.new('RGB', (frames[0].width, frames[0].height*len(frames[::4])))
    for i_, f in enumerate(frames[::4]): big.paste(f, (0, i_*f.height))
    palimg = big.quantize(colors, method=Image.Quantize.MEDIANCUT)
    pal = [f.quantize(palette=palimg, dither=Image.Dither.NONE) for f in frames]
    pal[0].save(f'{PV}/{fn}', save_all=True, append_images=pal[1:], duration=ms, loop=0, optimize=True)
    return dict(file=fn, frames=n, secs=n*ms/1000, bytes=os.path.getsize(f'{PV}/{fn}'), route_units=round(tot, 1))
def day_sway(): return route_gif('day_cam_sway.gif')
def night_lamps(): return route_gif('night_lamps.gif', night=True, flies=True, ms=80, W=480, crop=(0, 250, 480, 690), follow=(.25, -10., .3))   # 闊啲、跟拍弱啲：燈柱＋燈籠＋螢火瓶＋小屋窗同框

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[1]); ap.add_argument('--src', default=DEF_SRC); ap.add_argument('--out', default=DEF_OUT)
    ap.add_argument('--cmp', default=os.environ.get('GARDEN3D_CMP'), help='billboard 版場景目錄（對比圖用；冇就跳過 compare）')
    ap.add_argument('--only', default='gif,daysway,nightlamps,assembled,occlusion,compare,closeups,meshes,backfill,ground,dir4,normals'); a = ap.parse_args(argv)
    load(a.src, a.out); os.makedirs(PV, exist_ok=True); r = {}
    fn = {'gif': walk_gif, 'assembled': assembled, 'occlusion': occlusion, 'compare': lambda: compare(a.cmp) if a.cmp else 'skip（冇 --cmp）',
          'closeups': closeups, 'daysway': day_sway, 'nightlamps': night_lamps, 'meshes': meshes_sheet, 'backfill': backfill, 'ground': ground_top, 'dir4': dir4_sheet, 'normals': normals_pets}
    for k in a.only.split(','): r[k] = fn[k]()
    print('ok', PV, sorted(os.listdir(PV)), {k: v for k, v in r.items() if v is not None})

if __name__ == '__main__':
    main()
