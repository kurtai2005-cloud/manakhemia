#!/usr/bin/env python3
"""preview_hunt3d.py — 草原預覽（純 numpy 光線投射；對齊花園 H1 preview_garden3d）。
地面 @3x 取樣（3 texels/unit）、太陽 shadow map（intensity 0.3）、fill、霧。
靜態 600×844 裁 (0,190,600,590)＝600×400；hunt_cam_steady.gif 6 秒穩陣跟拍。
"""
import os, sys, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from m1_common import V3

ROOT = SRC = PV = ART = None
J = LJ = CJ = None
MESH, TEX, SM = {}, {}, {}
FONT_PATH = None

def hx(h):
    h = h.lstrip('#'); return np.array([int(h[i:i+2], 16) for i in (0, 2, 4)], float) / 255

def img(p, mode='RGBA'):
    return np.array(Image.open(f'{SRC}/{p}').convert(mode)).astype(float) / 255

def tex(p):
    if p not in TEX:
        TEX[p] = img(p)
    return TEX[p]

def font(sz=18):
    global FONT_PATH
    if FONT_PATH is None:
        import glob
        cands = [
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc',
        ] + glob.glob('/usr/share/fonts/**/*CJK*Regular*.ttc', recursive=True)
        FONT_PATH = next((p for p in cands if os.path.isfile(p)), None)
    if FONT_PATH:
        try:
            return ImageFont.truetype(FONT_PATH, sz, index=0)
        except Exception:
            try:
                return ImageFont.truetype(FONT_PATH, sz)
            except Exception:
                pass
    return ImageFont.load_default()

def label(d, xy, s, sz=18, fill=(255, 255, 255), bg=(20, 22, 34)):
    f = font(sz)
    b = d.textbbox(xy, s, font=f)
    d.rectangle((b[0] - 4, b[1] - 3, b[2] + 4, b[3] + 3), fill=bg)
    d.text(xy, s, font=f, fill=fill)

def load(root, src=None, out=None):
    global ROOT, SRC, PV, ART, J, LJ, CJ
    ROOT = os.path.abspath(root)
    ART = f'{ROOT}/art-pet'
    SRC = os.path.abspath(src or f'{ART}/scenes/hunt3d/prairie')
    PV = out
    TEX.clear(); MESH.clear(); SM.clear()
    J = json.load(open(f'{SRC}/objects.json'))
    LJ = json.load(open(f'{SRC}/lights.json'))
    CJ = json.load(open(f'{SRC}/camera.json'))
    for o in J['objects']:
        if o.get('type') == 'mesh':
            MESH[o['id']] = mesh_prep(json.load(open(f"{SRC}/{o['mesh']}")), o)
    shadow_map()

def mesh_prep(MJ, o):
    off = np.array([o['x'], o.get('y', 0), o['z']], float)
    a = math.radians(o.get('yawDeg', 0)); ca, sa = math.cos(a), math.sin(a)
    R = np.array([[ca, 0, sa], [0, 1, 0], [-sa, 0, ca]])
    P = np.array(MJ['positions'], float).reshape(-1, 3) @ R.T + off
    N = np.array(MJ['normals'], float).reshape(-1, 3) @ R.T
    UV = np.array(MJ['uvs'], float).reshape(-1, 2)
    I = np.array(MJ['indices'], int).reshape(-1, 3)
    v0, v1, v2 = P[I[:, 0]], P[I[:, 1]], P[I[:, 2]]
    g = np.cross(v1 - v0, v2 - v0); ln = np.linalg.norm(g, axis=1, keepdims=True); ln = np.where(ln < 1e-12, 1, ln); g = g / ln
    ns = N[I].mean(1); ln = np.linalg.norm(ns, axis=1, keepdims=True); ln = np.where(ln < 1e-12, 1, ln); ns = ns / ln
    return dict(json=MJ, O=v0, U=v1 - v0, V=v2 - v0, uv0=UV[I[:, 0]], du=UV[I[:, 1]] - UV[I[:, 0]],
                dv=UV[I[:, 2]] - UV[I[:, 0]], g=g, ns=ns, T=tex(MJ['texture']),
                E=tex(MJ['emissive']) if MJ.get('emissive') else None,
                cast=o.get('castShadow', True), Pv=P)

def bary(C, D, O, U, V):
    pv = np.cross(D, V); det = pv @ U; det = np.where(np.abs(det) < 1e-12, 1e-12, det); tv = C - O
    s = (tv * pv).sum(-1) / det; q = np.cross(tv, U); r = (D * q).sum(-1) / det; t = (q @ V) / det
    return t, s, r

def msamp(M, k, s, r, T=None):
    T = M['T'] if T is None else T
    h, w = T.shape[:2]
    uv = M['uv0'][k] + s[:, None] * M['du'][k] + r[:, None] * M['dv'][k]
    return T[np.clip(((1 - uv[:, 1]) * h).astype(int), 0, h - 1), np.clip((uv[:, 0] * w).astype(int), 0, w - 1)]

def shadow_map(res=.5):
    sd = np.array(LJ['sun']['dir'], float)
    a = np.cross(sd, [0, 1, 0]); a /= np.linalg.norm(a); b = np.cross(a, sd)
    Ms = [M for M in MESH.values() if M['cast']]
    SM.clear()
    if not Ms:
        return
    allP = np.concatenate([M['Pv'] for M in Ms])
    A0, B0 = (allP @ a).min() - 2, (allP @ b).min() - 2
    Wm = int(((allP @ a).max() - A0 + 2) / res) + 1
    Hm = int(((allP @ b).max() - B0 + 2) / res) + 1
    dm = np.full((Hm, Wm), np.inf)
    for M in Ms:
        for k in range(len(M['O'])):
            V3 = np.stack([M['O'][k], M['O'][k] + M['U'][k], M['O'][k] + M['V'][k]])
            pa, pb = (V3 @ a - A0) / res, (V3 @ b - B0) / res
            i0, i1 = max(int(pa.min()), 0), min(int(pa.max()) + 2, Wm)
            j0, j1 = max(int(pb.min()), 0), min(int(pb.max()) + 2, Hm)
            if i1 <= i0 or j1 <= j0:
                continue
            jj, ii = np.mgrid[j0:j1, i0:i1]
            X = A0 + (ii.ravel() + .5) * res; Y = B0 + (jj.ravel() + .5) * res
            Cs = np.outer(X, a) + np.outer(Y, b) - 4000 * sd
            t, s_, r_ = bary(Cs, np.broadcast_to(sd, Cs.shape), M['O'][k], M['U'][k], M['V'][k])
            ins = (s_ >= 0) & (r_ >= 0) & (s_ + r_ <= 1)
            if not ins.any():
                continue
            ix = np.where(ins)[0]
            al = msamp(M, np.full(len(ix), k), s_[ix], r_[ix])[:, 3] > .5
            ix = ix[al]
            np.minimum.at(dm, (jj.ravel()[ix], ii.ravel()[ix]), t[ix])
    SM.update(a=a, b=b, sd=sd, A0=A0, B0=B0, res=res, dm=dm)

def in_shadow(P, bias=1.2):
    if not SM:
        return np.zeros(P.shape[:-1], bool)
    i = ((P @ SM['a'] - SM['A0']) / SM['res']).astype(int)
    j = ((P @ SM['b'] - SM['B0']) / SM['res']).astype(int)
    dm = SM['dm']
    ok = (i >= 0) & (i < dm.shape[1]) & (j >= 0) & (j < dm.shape[0])
    d = (P @ SM['sd']) + 4000
    out = np.zeros(P.shape[:-1], bool)
    out[ok] = d[ok] > dm[j[ok], i[ok]] + bias
    return out

def _sprite01(arr):
    a = arr.astype(float)
    if a.max() > 1.5:
        a = a / 255.0
    if a.ndim == 2:
        a = np.stack([a, a, a, np.ones_like(a)], -1)
    if a.shape[-1] == 3:
        a = np.concatenate([a, np.ones(a.shape[:2] + (1,))], -1)
    return a

def load_pet_clip(cid, fi, size='L'):
    """hunt clip 第 fi 幀（1-based 或 0-based 都接受），回 (c,n,e,pivot_norm)。"""
    hd = f'{ART}/sprites/tuanrong/motion/hunt'
    idx = json.load(open(f'{hd}/clips.json'))
    stem = os.path.splitext(os.path.basename(idx['atlases'][size][cid]))[0]
    Jt = json.load(open(f'{hd}/{stem}.json'))
    nfr = idx['clips'][cid]['frames']
    i = fi if fi >= 1 else fi + 1
    i = max(1, min(nfr, i))
    nm = f'{cid}_{i:02d}'
    fr = Jt['frames'][nm]['frame']
    x, y, w, h = fr['x'], fr['y'], fr['w'], fr['h']
    def cut(path, fallback=None):
        if not os.path.exists(path):
            return fallback if fallback is not None else np.zeros((h, w, 4), float)
        return _sprite01(np.array(Image.open(path).convert('RGBA')))[y:y + h, x:x + w]
    c = cut(f'{hd}/{stem}.png')
    n = cut(f'{hd}/{stem}_n.png', np.dstack([np.full((h, w), 0.5), np.full((h, w), 0.5), np.ones((h, w)), np.ones((h, w))]))
    e = cut(f'{hd}/{stem}_emissive.png', np.zeros((h, w, 4), float))
    pv = Jt['frames'][nm].get('pivotPx') or {'x': Jt.get('meta', {}).get('pivotPx', [w // 2, h - 3])[0],
                                              'y': Jt.get('meta', {}).get('pivotPx', [w // 2, h - 3])[1]}
    if isinstance(pv, dict):
        px, py = pv['x'], pv['y']
    else:
        px, py = pv
    return c, n, e, (px / w, py / h)

def load_idle_pet():
    """優先 radiant idle（花園同款 L 64）；冇就用撥草第 1 幀。"""
    try:
        from m1_common import frame_radiant
        fr = frame_radiant('idle_01')
        # frame_radiant 可能回 numpy 或者 (im, pivot)
        if isinstance(fr, tuple):
            im, pv = fr[0], fr[1] if len(fr) > 1 else (32, 61)
            c = _sprite01(im)
            return c, np.dstack([np.full(c.shape[:2], .5), np.full(c.shape[:2], .5), np.ones(c.shape[:2]), c[..., 3]]), np.zeros_like(c), (pv[0] / c.shape[1], pv[1] / c.shape[0])
        c = _sprite01(fr)
        return c, np.dstack([np.full(c.shape[:2], .5), np.full(c.shape[:2], .5), np.ones(c.shape[:2]), c[..., 3]]), np.zeros_like(c), (32 / c.shape[1], 61 / c.shape[0])
    except Exception:
        return load_pet_clip('part_grass', 1, 'L')

def _critter_frame(sp, ani='idle'):
    cj = json.load(open(f'{ART}/sprites/hunt/critters/{sp["id"]}.json'))
    atl = _sprite01(np.array(Image.open(f'{ART}/sprites/hunt/critters/{cj["atlas"]["image"]}').convert('RGBA')))
    frn = cj['animations'][ani]['frames'][0]
    fr = cj['atlas']['frames'][frn]['frame']
    spr = atl[fr['y']:fr['y'] + fr['h'], fr['x']:fr['x'] + fr['w']]
    pv = cj['pivotPx']
    npath = f'{ART}/sprites/hunt/critters/{sp["id"]}_n.png'
    # atlas may include normal? skip, use bent
    return spr, (pv[0] / spr.shape[1], pv[1] / spr.shape[0])

def _fruit_frame(fid):
    F = json.load(open(f'{ART}/sprites/hunt/fruits/fruits.json'))
    atl = _sprite01(np.array(Image.open(f'{ART}/sprites/hunt/fruits/atlas_fruits.png').convert('RGBA')))
    fr = F['atlas']['frames'][fid]['frame']
    spr = atl[fr['y']:fr['y'] + fr['h'], fr['x']:fr['x'] + fr['w']]
    pv = F['atlas']['frames'][fid].get('pivotPx') or {'x': F['pivotPx'][0], 'y': F['pivotPx'][1]}
    if isinstance(pv, dict):
        return spr, (pv['x'] / spr.shape[1], pv['y'] / spr.shape[0])
    return spr, (pv[0] / spr.shape[1], pv[1] / spr.shape[0])

def render(yaw, W=600, H=844, cam=None, pet='default', show_critters=True, show_fruits=True):
    CJ_ = dict(CJ, **(cam or {}))
    tg = np.array(CJ_['target'], float); p = math.radians(CJ_['pitchDeg']); yw = math.radians(yaw)
    C = tg + CJ_['dist'] * np.array([math.sin(yw) * math.cos(p), math.sin(p), math.cos(yw) * math.cos(p)])
    fw = (tg - C) / np.linalg.norm(tg - C); rt = np.cross(fw, [0, 1, 0]); rt /= np.linalg.norm(rt); up = np.cross(rt, fw)
    tv = math.tan(math.radians(CJ_['fovDeg']) / 2); th = tv * W / H
    jj, ii = np.mgrid[0:H, 0:W].astype(float)
    D = fw + ((2 * (ii + .5) / W - 1) * th)[..., None] * rt - ((2 * (jj + .5) / H - 1) * tv)[..., None] * up
    D /= np.linalg.norm(D, axis=-1, keepdims=True)
    sun = LJ['sun']; sd = np.array(sun['dir']); SI = sun.get('shadowIntensity', .3)
    sI = sun['intensity']; sc = hx(sun['color'])
    amb = hx(sun['ambient']['color']) * sun['ambient']['intensity']
    fl = LJ.get('fill'); fd = np.array(fl['dir']) if fl else np.zeros(3)
    fI = fl['intensity'] if fl else 0; fc = hx(fl['color']) if fl else 0
    if pet == 'default':
        c_, n_, e_, pv_ = load_idle_pet()
        pet = dict(x=J['pet']['x'], z=J['pet']['z'], frame=(c_, n_, e_, pv_), flip=False)
    depth = np.full((H, W), np.inf); col = np.zeros((H, W, 3))
    # 地面 @3x（同 H1：u=((X+128)*3)）
    g1 = tex(J['ground'].get('file3x') or J['ground']['image3x'])
    ao_p = J['ground'].get('ao3x') or J['ground'].get('ao')
    ao = img(ao_p, 'L')
    if ao.ndim == 3:
        ao = ao[..., 0]
    ot = J['ground'].get('outerTile') or {}
    tl = tex(ot.get('file3x') or J['ground']['tile3x'])
    dy = D[..., 1]; hit = dy < -1e-4
    t = np.where(hit, -C[1] / np.where(hit, dy, -1), np.inf)
    P = C + D * t[..., None]; X, Z = P[..., 0], P[..., 2]
    inp = hit & (np.abs(X) < 128) & (np.abs(Z) < 128)
    u = np.clip(((X + 128) * 3).astype(int), 0, g1.shape[1] - 1)
    v = np.clip(((Z + 128) * 3).astype(int), 0, g1.shape[0] - 1)
    tu = (((X + 128) % 64) * 3).astype(int) % tl.shape[1]
    tvv = (((Z + 128) % 64) * 3).astype(int) % tl.shape[0]
    alb = np.where(inp[..., None], g1[v, u, :3], tl[tvv, tu, :3])
    aoo = np.where(inp, ao[np.clip(v, 0, ao.shape[0] - 1), np.clip(u, 0, ao.shape[1] - 1)], 1.)
    sh = np.ones((H, W))
    blobs = []
    if pet:
        blobs.append(dict(id='pet', x=pet['x'], z=pet['z'], r=13))
    if show_critters:
        for sp in J['critters']['spawn']:
            r = 16 if sp.get('big') else 10
            blobs.append(dict(id=sp['id'], x=sp['x'], z=sp['z'], r=r))
    if show_fruits:
        for sp in J.get('fruits', {}).get('spawn', []):
            blobs.append(dict(id=sp['id'], x=sp['x'], z=sp['z'], r=8))
    for o in blobs:
        r = o['r']
        ox, oz = o['x'] + sd[0] / -sd[1] * r * .5, o['z'] + sd[2] / -sd[1] * r * .5
        sh *= 1 - .38 * np.exp(-(((X - ox) / r) ** 2 + ((Z - oz) / (r * .6)) ** 2) * 2)
    if MESH:
        gi = np.where(hit & (np.abs(X) < 700) & (Z > -600) & (Z < 400))
        if len(gi[0]):
            sg = in_shadow(P[gi]); sh[gi[0][sg], gi[1][sg]] *= 1 - SI
    nG = np.zeros(P.shape); nG[..., 1] = 1
    litg = amb + (sI * max(0, -sd[1]) * sh)[..., None] * sc + fI * max(0, -fd[1]) * fc
    gcol = alb * aoo[..., None] * litg
    m = hit; col[m] = gcol[m]; depth[m] = t[m]

    # backdrops + 角色 billboard
    items = []
    cz_cam = CJ_['target'][2] + CJ_['dist'] * math.cos(math.radians(CJ_['pitchDeg']))
    for bd in J.get('backdrops', []):
        wpx, hpx = bd['sizePx']
        scu = (cz_cam - bd['z']) / CJ_['dist']
        items.append(dict(id=bd['id'], kind='backdrop', x=0, z=bd['z'], y=0,
                          w=wpx * scu, h=hpx * scu, pivot=(0.5, 1.0), face='fixed',
                          unlit=True, file3x=bd['file3x'], yawDeg=0))
    if show_critters:
        for sp in J['critters']['spawn']:
            spr, pv = _critter_frame(sp)
            items.append(dict(id='c_' + sp['id'], kind='sprite', x=sp['x'], z=sp['z'], y=0,
                              w=spr.shape[1], h=spr.shape[0], pivot=pv, face='cyl',
                              unlit=False, spr=spr, shadow=True))
    if show_fruits:
        for sp in J.get('fruits', {}).get('spawn', []):
            spr, pv = _fruit_frame(sp['id'])
            items.append(dict(id='f_' + sp['id'], kind='sprite', x=sp['x'], z=sp['z'], y=0,
                              w=spr.shape[1], h=spr.shape[0], pivot=pv, face='cyl',
                              unlit=False, spr=spr, shadow=True))
    if pet:
        pc, pn, pe, ppv = pet['frame']
        if pet.get('flip'):
            pc, pe = pc[:, ::-1], pe[:, ::-1]
            pn = pn[:, ::-1].copy(); pn[..., 0] = 1 - pn[..., 0]
        items.append(dict(id='pet', kind='pet', x=pet['x'], z=pet['z'], y=0,
                          w=pc.shape[1], h=pc.shape[0], pivot=list(ppv), face='cyl',
                          unlit=False, pc=pc, pn=pn, pe=pe))
    # 遠→近（z 細嘅先，但實際用 depth 測）
    items.sort(key=lambda o: o['z'])
    for o in items:
        O = np.array([o['x'], o.get('y', 0), o['z']], float)
        if o['face'] == 'cyl':
            n = np.array([C[0] - O[0], 0, C[2] - O[2]]); n /= max(np.linalg.norm(n), 1e-9)
        else:
            a = math.radians(o.get('yawDeg', 0)); n = np.array([math.sin(a), 0, math.cos(a)])
        rv = np.array([n[2], 0, -n[0]])
        dn = D @ n; tt = ((O - C) @ n) / np.where(np.abs(dn) < 1e-6, 1e-6, dn)
        Pb = C + D * tt[..., None]; s = (Pb - O) @ rv; hh = Pb[..., 1] - O[1]
        uu = s + o['pivot'][0] * o['w']; vv = o['pivot'][1] * o['h'] - hh
        ins = (tt > 0) & (uu >= 0) & (uu < o['w']) & (vv >= 0) & (vv < o['h']) & (tt < depth)
        if not ins.any():
            continue
        if o['kind'] == 'pet':
            iu = uu[ins].astype(int); iv = vv[ins].astype(int)
            c = o['pc'][iv, iu]; nn = o['pn'][iv, iu]; e = o['pe'][iv, iu]
        elif o['kind'] == 'sprite':
            iu = np.clip(uu[ins].astype(int), 0, o['spr'].shape[1] - 1)
            iv = np.clip(vv[ins].astype(int), 0, o['spr'].shape[0] - 1)
            c = o['spr'][iv, iu]; e = None; nn = None
        else:
            T = tex(o['file3x']); sc3 = T.shape[1] / o['w']
            iu = np.clip((uu[ins] * sc3).astype(int), 0, T.shape[1] - 1)
            iv = np.clip((vv[ins] * T.shape[0] / o['h']).astype(int), 0, T.shape[0] - 1)
            c = T[iv, iu]; e = None; nn = None
        a = c[:, 3] > .5
        if not a.any():
            continue
        idx = np.where(ins); sel = (idx[0][a], idx[1][a]); c = c[a]
        if o.get('unlit'):
            out = c[:, :3]
        else:
            if o['kind'] == 'pet' and nn is not None:
                nt = nn[a, :3] * 2 - 1
                nw = nt[:, :1] * rv + nt[:, 1:2] * np.array([0, 1, 0]) + nt[:, 2:3] * n
                ln = np.linalg.norm(nw, axis=-1, keepdims=True); nw = nw / np.maximum(ln, 1e-6)
            else:
                nw = np.tile(.7 * n + .55 * np.array([0., 1, 0]), (len(c), 1))
                nw /= np.linalg.norm(nw, axis=-1, keepdims=True)
            lam = np.clip(nw @ -sd, 0, 1) * .8 + .2
            lf = np.clip(nw @ -fd, 0, 1)
            out = c[:, :3] * (amb + (sI * lam)[:, None] * sc + (fI * lf)[:, None] * fc)
            if o['kind'] == 'pet' and e is not None:
                out = out + e[a][:, :3] * (e[a][:, 3:4]) * .6
        col[sel] = out; depth[sel] = tt[sel]

    # mesh 三角
    for o in J['objects']:
        if o.get('type') != 'mesh':
            continue
        M = MESH[o['id']]
        for k in range(len(M['O'])):
            V3 = np.stack([M['O'][k], M['O'][k] + M['U'][k], M['O'][k] + M['V'][k]])
            dz = (V3 - C) @ fw
            if (dz < 1).any():
                continue
            # project for bbox
            d = V3 - C; z = d @ fw; x = d @ rt; y = d @ up
            pi_ = ((x / z) / th + 1) / 2 * W - .5
            pj_ = (1 - (y / z) / tv) / 2 * H - .5
            i0, i1 = max(int(pi_.min()) - 1, 0), min(int(pi_.max()) + 2, W)
            j0, j1 = max(int(pj_.min()) - 1, 0), min(int(pj_.max()) + 2, H)
            if i1 <= i0 or j1 <= j0:
                continue
            Ds = D[j0:j1, i0:i1]
            if (Ds.reshape(-1, 3) @ M['g'][k]).min() >= 0:
                continue
            tt, s_, r_ = bary(C, Ds, M['O'][k], M['U'][k], M['V'][k])
            ins = (tt > 0) & (s_ >= 0) & (r_ >= 0) & (s_ + r_ <= 1) & (tt < depth[j0:j1, i0:i1] - 1e-3) & ((Ds @ M['g'][k]) < 0)
            if not ins.any():
                continue
            lj, li = np.where(ins); kk = np.full(len(lj), k)
            c = msamp(M, kk, s_[ins], r_[ins]); a = c[:, 3] > .5
            if not a.any():
                continue
            lj, li, c = lj[a], li[a], c[a]; sel = (lj + j0, li + i0)
            Pq = C + D[sel] * tt[ins][a][:, None]; n = M['ns'][k]
            shk = (~in_shadow(Pq + M['g'][k] * .3)).astype(float) if (sI > 0) else np.ones(len(Pq))
            lam = np.clip(n @ -sd, 0, 1) * (1 - min(1., SI / .42) * (1 - shk))
            lf = max(0., float(n @ -fd))
            sky = .75 + .25 * n[1]
            out = c[:, :3] * (amb * sky + (sI * lam)[:, None] * sc + fI * lf * fc)
            col[sel] = out; depth[sel] = tt[ins][a]

    fg = LJ['fog']
    fk = np.clip((depth - fg['near']) / (fg['far'] - fg['near']), 0, 1) * .45
    fcol = hx(fg['color'])
    col = np.where(np.isfinite(depth)[..., None], col * (1 - fk[..., None]) + fcol * fk[..., None], fcol)
    # 未擊中（純天空方向）用霧色偏藍桃——其實 backdrop 應該已覆蓋；剩餘用 sky 底
    miss = ~np.isfinite(depth)
    if miss.any():
        col[miss] = hx('#87bde0')
    return (np.clip(col, 0, 1) * 255 + .5).astype(np.uint8)

CROP = (0, 190, 600, 590)

def crop_still(im, title=None, crop=CROP):
    pil = Image.fromarray(im).crop(crop)
    if title:
        dd = ImageDraw.Draw(pil)
        label(dd, (8, 8), title, 18)
    return pil

def scene_stills(out, yaw0=-5.0):
    os.makedirs(out, exist_ok=True)
    # 主圖：H1 穩陣構圖 600×400，寵物用撥草中段（場面有動作感）
    c, n, e, pv = load_pet_clip('part_grass', 3, 'L')
    pet = dict(x=J['pet']['x'], z=J['pet']['z'], frame=(c, n, e, pv), flip=False)
    im = render(yaw0, W=600, H=844, pet=pet)
    still = crop_still(im, f'日間 穩定鏡 {yaw0:+.1f}°  撥草', CROP)
    still.save(f'{out}/hunt_scene.png')
    # 0° 大圖同樣裁切
    im0 = render(0, W=600, H=844, pet=pet)
    crop_still(im0, '日間 穩定鏡 +0.0°  撥草', CROP).save(f'{out}/hunt_scene_0deg.png')
    # ±10°／0° 三聯（同一裁切）
    panels = []
    for yw in (-10, 0, 10):
        im = render(yw, W=600, H=844, pet=pet)
        panels.append(crop_still(im, f'{yw:+.1f}°', CROP))
    strip = Image.new('RGB', (8 + 3 * (600 + 8), 400 + 36), (18, 24, 48))
    d = ImageDraw.Draw(strip)
    label(d, (10, 8), '狩獵草原（H1 穩陣鏡 −10°／0°／+10°；前景／中景小怪＋果／遠丘樹林）', 16, fill=(255, 236, 184))
    for i, p in enumerate(panels):
        strip.paste(p, (8 + i * (600 + 8), 32))
    strip.save(f'{out}/hunt_scene_yaws.png')
    return f'{out}/hunt_scene.png'

def steady_gif(out, fn='hunt_cam_steady.gif', W=600, crop=CROP, colors=96):
    """6 秒：撥草→撲→抱果行→歡呼；鏡頭參數同 H1 穩陣版。"""
    os.makedirs(out, exist_ok=True)
    A = CJ.get('swayAmplitudeDeg', 5); dmp = CJ.get('followDamping', 2.)
    wx, wz = CJ.get('followWeight', [.25, .3])
    ox, oz = CJ.get('followOffset', [-20, 0]); gx, gz = CJ.get('followOrigin', [0, 0])
    dt = 0.1; N = 60
    # 動作時間軸（秒）
    # 0.0–1.2 撥草（8fps，6 幀）於起點
    # 1.2–2.4 撲，移向果／露珠偶
    # 2.4–4.8 抱果行（10fps loop，2 units/frame）
    # 4.8–6.0 歡呼
    p0 = (0.0, 0.0)
    p1 = (10.0, -16.0)   # 撲完靠近 dewpear／dewlet
    p2 = (22.0, 28.0)    # 抱果行向鏡頭右側（+Z 近）
    seq = []  # (x,z,cid,frame_1based,zh)
    for f in range(N):
        t = f * dt
        if t < 1.2:
            x, z = p0
            fi = min(6, 1 + int(t * 8))
            seq.append((x, z, 'part_grass', fi, '撥草'))
        elif t < 2.4:
            u = (t - 1.2) / 1.2
            x = p0[0] + (p1[0] - p0[0]) * u
            z = p0[1] + (p1[1] - p0[1]) * u
            fi = min(6, 1 + int((t - 1.2) * 8))
            seq.append((x, z, 'pounce', fi, '撲'))
        elif t < 4.8:
            u = (t - 2.4) / 2.4
            x = p1[0] + (p2[0] - p1[0]) * u
            z = p1[1] + (p2[1] - p1[1]) * u
            fi = 1 + int((t - 2.4) * 10) % 6
            seq.append((x, z, 'carry_fruit', fi, '抱果行'))
        else:
            x, z = p2
            fi = min(6, 1 + int((t - 4.8) * 10))
            seq.append((x, z, 'cheer', fi, '歡呼'))

    # cache clip frames
    cache = {}
    def fr(cid, fi):
        k = (cid, fi)
        if k not in cache:
            cache[k] = load_pet_clip(cid, fi, 'L')
        return cache[k]

    tg0 = np.array(CJ['target'], float); cx = cz = None
    frames = []; log = []
    for f_, (x, z, cid, fi, zh) in enumerate(seq):
        yw = -A * math.cos(math.pi * f_ / (N - 1))
        dx_, dz_ = ox + wx * (x - gx), oz + wz * (z - gz)
        if cx is None:
            cx, cz = dx_, dz_
        else:
            al = 1 - math.exp(-dmp * dt); cx += (dx_ - cx) * al; cz += (dz_ - cz) * al
        c, nn, e, pv = fr(cid, fi)
        im = render(yw, W=W, cam=dict(target=[tg0[0] + cx, tg0[1], tg0[2] + cz]),
                    pet=dict(x=x, z=z, frame=(c, nn, e, pv), flip=False))
        pil = crop_still(im, f'日間 穩定鏡 {yw:+.1f}°  {zh}', crop)
        frames.append(pil)
        log.append((round(yw, 2), round(cx, 1), round(cz, 1)))
        print(f'  gif {f_+1}/{N} {zh} yaw={yw:+.1f}', flush=True)
    # 共同調色盤（同 H1）
    big = Image.new('RGB', (frames[0].width, frames[0].height * len(frames[::4])))
    for i_, f in enumerate(frames[::4]):
        big.paste(f, (0, i_ * f.height))
    palimg = big.quantize(colors, method=Image.Quantize.MEDIANCUT)
    pal = [f.quantize(palette=palimg, dither=Image.Dither.NONE) for f in frames]
    path = f'{out}/{fn}'
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=int(dt * 1000), loop=0, optimize=True)
    sz = os.path.getsize(path)
    if sz >= 3 * 1024 * 1024:
        # 再壓 80 色
        palimg = big.quantize(80, method=Image.Quantize.MEDIANCUT)
        pal = [f.quantize(palette=palimg, dither=Image.Dither.NONE) for f in frames]
        pal[0].save(path, save_all=True, append_images=pal[1:], duration=int(dt * 1000), loop=0, optimize=True)
        sz = os.path.getsize(path)
    if sz >= 3 * 1024 * 1024:
        raise SystemExit(f'GIF 太大 {sz}')
    return dict(file=path, frames=N, secs=6.0, bytes=sz, size=frames[0].size)

def compare_before_after(out):
    before = f'{out}/hunt_scene_before.png'
    after = f'{out}/hunt_scene.png'
    if not os.path.exists(before) or not os.path.exists(after):
        return None
    a = Image.open(before).convert('RGB')
    b = Image.open(after).convert('RGB')
    # 統一高度 400，寬按比例
    def fit_h(im, H=400):
        w, h = im.size
        W = max(1, int(round(w * H / h)))
        return im.resize((W, H), Image.NEAREST)
    a2, b2 = fit_h(a), fit_h(b)
    pad, head, gap = 10, 36, 12
    W = pad + a2.width + gap + b2.width + pad
    H = head + a2.height + pad
    canvas = Image.new('RGB', (W, H), (18, 24, 48))
    d = ImageDraw.Draw(canvas)
    label(d, (pad, 8), '改前 hunt_scene', 16, fill=(255, 200, 180))
    label(d, (pad + a2.width + gap, 8), '改後 hunt_scene（H1 穩陣構圖）', 16, fill=(255, 236, 184))
    canvas.paste(a2, (pad, head))
    canvas.paste(b2, (pad + a2.width + gap, head))
    path = f'{out}/hunt_scene_compare.png'
    canvas.save(path)
    return path

def build(root, out):
    load(root, out=out)
    scene_stills(out)
    info = steady_gif(out)
    cmp = compare_before_after(out)
    print('hunt preview', info, 'compare', cmp)
    return info, cmp

if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else '/workspace/m1-icons-hunt-src'
    out = sys.argv[2] if len(sys.argv) > 2 else '/workspace/game-design/m1_icons_hunt'
    load(root, out=out)
    scene_stills(out)
    print('stills ok')
