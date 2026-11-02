#!/usr/bin/env python3
"""garden3d_mesh.py — 3D 花園通用 mesh（garden3d.mesh/2）建模工具＋寫出（json＋glb＋像素貼圖 atlas）。
格式（遊程定）：units＝1x art px、Y 上、原點＝物件底中（局部座標）；positions[]／normals[]／uvs[]（V 上 0–1）／indices[]（三角，逆時針＝正面），
一件一張 texture（像素 png，2 次方），可選 emissive／alphaTest；每件 ≤ 300 三角。
基本件：quad（平行四邊形）、poly（扇形三角）、card（雙面卡）、box、extrude（像素外形擠出：正面＝原 2D 美術 1:1，側面＝邊緣像素拉條）、frustum（八角錐台）。
"""
import os, json, struct, io, math
import numpy as np
from PIL import Image
MAX_TRIS = 300
def up3(a): return np.repeat(np.repeat(a, 3, 0), 3, 1)
def _n(v): v = np.asarray(v, float); return v/np.linalg.norm(v)

class MB:
    def __init__(s, mid):
        s.id = mid; s.tex = []; s.faces = []          # faces: (verts[k,3], texel[k,2], ti, normal or None)
    def add_tex(s, rgba, emis=None):
        rgba = np.asarray(rgba, np.uint8).copy(); a = rgba[..., 3] > 127; rgba[..., 3] = a*255; rgba[~a, :3] = 0
        if emis is not None:
            emis = np.asarray(emis, np.uint8).copy(); ea = emis[..., 3] > 127; emis[..., 3] = ea*255; emis[~ea, :3] = 0
            if not ea.any(): emis = None
        s.tex.append((rgba, emis)); return len(s.tex) - 1
    def poly(s, verts, texel, ti, normal=None):
        s.faces.append((np.array(verts, float), np.array(texel, float), ti, None if normal is None else _n(normal)))
    def quad(s, p0, U, V, ti, rect=None, normal=None):
        """p0＝左下；U＝向右；V＝向上（由正面望）；rect＝(x,y,w,h) 貼圖像素（左上原點）。"""
        p0, U, V = (np.asarray(t, float) for t in (p0, U, V))
        if rect is None: h, w = s.tex[ti][0].shape[:2]; rect = (0, 0, w, h)
        x, y, w, h = rect
        s.poly([p0, p0+U, p0+U+V, p0+V], [(x, y+h), (x+w, y+h), (x+w, y), (x, y)], ti, normal)
    def card(s, p0, U, V, ti, rect=None, normal=None):
        """雙面卡（背面另加一塊反向面；背面睇到係鏡像）。normal＝正面著色法線（背面用 Z 反轉）。"""
        p0, U, V = (np.array(t, float) for t in (p0, U, V))
        if rect is None: h, w = s.tex[ti][0].shape[:2]; rect = (0, 0, w, h)
        if p0[1] < -1e-6 and abs(V[0]) < 1e-9 and abs(V[2]) < 1e-9 and V[1] > 0:   # 埋咗落地底嘅行裁走（原點＝底，y≥0）
            c = min(-p0[1], V[1] - 1); k = rect[3]/V[1]; cut = int(round(c*k)); p0[1] += cut/k; V[1] -= cut/k; rect = (rect[0], rect[1], rect[2], rect[3] - cut)
        s.quad(p0, U, V, ti, rect, normal)
        gn = _n(np.cross(U, V))
        bn = None if normal is None else _n(np.asarray(normal, float) - 2*(np.asarray(normal, float) @ gn)*gn)
        if rect is None: h, w = s.tex[ti][0].shape[:2]; rect = (0, 0, w, h)
        x, y, w, h = rect
        s.poly([p0+U, p0, p0+V, p0+U+V], [(x+w, y+h), (x, y+h), (x, y), (x+w, y)], ti, bn)
    def box(s, x0, x1, y0, y1, z0, z1, tex, bottom=False):
        """tex＝{面: ti 或 (ti, rect)}，面＝front/back/left/right/top；缺省用 'all'。"""
        def g(k):
            t = tex.get(k, tex.get('all')); return t if isinstance(t, tuple) else (t, None)
        W, Hh, D = x1-x0, y1-y0, z1-z0
        s.quad((x0, y0, z1), (W, 0, 0), (0, Hh, 0), *g('front'))
        s.quad((x1, y0, z0), (-W, 0, 0), (0, Hh, 0), *g('back'))
        s.quad((x0, y0, z0), (0, 0, D), (0, Hh, 0), *g('left'))
        s.quad((x1, y0, z1), (0, 0, -D), (0, Hh, 0), *g('right'))
        s.quad((x0, y1, z1), (W, 0, 0), (0, 0, -D), *g('top'))
        if bottom: s.quad((x0, y0, z0), (W, 0, 0), (0, 0, D), *g('top'))
    def ntris(s): return sum(len(f[0]) - 2 for f in s.faces)

    # ---- 像素擠出
    def extrude(s, rgba, mask, depth, px0, py0, zc=0., emis=None, min_run=1, front_normal=None, budget=None, back=True):
        """mask 內像素沿 Z 擠出 depth：圖像素 (u,v) → x=u−px0、y=py0−v。正／背面＝原圖（alpha＝mask），側面＝邊緣像素拉條。"""
        mask = mask.astype(bool); H, W = mask.shape; ys, xs = np.where(mask)
        if not len(ys): return
        r0, r1, c0, c1 = ys.min(), ys.max()+1, xs.min(), xs.max()+1
        img = np.zeros((r1-r0, c1-c0, 4), np.uint8); sub = mask[r0:r1, c0:c1]; img[sub] = rgba[r0:r1, c0:c1][sub]; img[sub, 3] = 255
        em = None
        if emis is not None:
            em = np.zeros_like(img); ek = sub & (emis[r0:r1, c0:c1, 3] > 127); em[ek] = emis[r0:r1, c0:c1][ek]
        ti = s.add_tex(img, em); zf, zb = zc + depth/2, zc - depth/2
        X0, X1, Y0, Y1 = c0 - px0, c1 - px0, py0 - r1, py0 - r0
        s.quad((X0, Y0, zf), (X1-X0, 0, 0), (0, Y1-Y0, 0), ti, None, front_normal)
        if back: s.quad((X1, Y0, zb), (X0-X1, 0, 0), (0, Y1-Y0, 0), ti, (img.shape[1], 0, -img.shape[1], img.shape[0]),
                        None if front_normal is None else np.asarray(front_normal)*[1, 1, -1])
        budget = (budget - 4) if budget else (MAX_TRIS - s.ntris())
        P = np.pad(mask, 1); runs = None
        for mr in range(min_run, 40):
            runs = []
            for side in ('L', 'R', 'T', 'B'):
                if side == 'L': e = P[1:-1, 1:-1] & ~P[1:-1, :-2]
                elif side == 'R': e = P[1:-1, 1:-1] & ~P[1:-1, 2:]
                elif side == 'T': e = P[1:-1, 1:-1] & ~P[:-2, 1:-1]
                else: e = P[1:-1, 1:-1] & ~P[2:, 1:-1]
                if side in 'LR':
                    for u in range(W):
                        col = e[:, u]; v = 0
                        while v < H:
                            if col[v]:
                                v1 = v
                                while v1 < H and col[v1]: v1 += 1
                                if v1 - v >= mr: runs.append((side, u, v, v1))
                                v = v1
                            else: v += 1
                else:
                    for v in range(H):
                        row = e[v]; u = 0
                        while u < W:
                            if row[u]:
                                u1 = u
                                while u1 < W and row[u1]: u1 += 1
                                if u1 - u >= mr: runs.append((side, v, u, u1))
                                u = u1
                            else: u += 1
            if 2*len(runs) <= budget - 0: break
        d = max(1, int(round(depth)))
        for side, a, b0, b1 in runs:
            L = b1 - b0
            if side in 'LR':
                u = a; strip = np.repeat(rgba[b0:b1, u][:, None], d, 1); es = None if emis is None else np.repeat(emis[b0:b1, u][:, None], d, 1)
                strip = strip.copy(); strip[..., 3] = 255; t = s.add_tex(strip, es)
                x = (u - px0) if side == 'L' else (u + 1 - px0); yb, yt = py0 - b1, py0 - b0
                if side == 'L': s.quad((x, yb, zb), (0, 0, depth), (0, yt-yb, 0), t)
                else: s.quad((x, yb, zf), (0, 0, -depth), (0, yt-yb, 0), t)
            else:
                v = a; strip = np.repeat(rgba[v, b0:b1][None], d, 0).copy(); strip[..., 3] = 255
                es = None if emis is None else np.repeat(emis[v, b0:b1][None], d, 0); t = s.add_tex(strip, es)
                xl, xr = b0 - px0, b1 - px0
                if side == 'T': y = py0 - v; s.quad((xl, y, zf), (xr-xl, 0, 0), (0, 0, -depth), t)
                else: y = py0 - v - 1; s.quad((xl, y, zb), (xr-xl, 0, 0), (0, 0, depth), t)
    def frustum(s, r0, r1, y0, y1, n, ti, rect, rot=math.pi/8):
        """n 邊錐台側面（貼圖 rect 沿圓周鋪一圈）。"""
        x, y, w, h = rect
        for i in range(n):
            a0, a1 = rot + 2*math.pi*i/n, rot + 2*math.pi*(i+1)/n
            b0 = (r0*math.sin(a0), y0, r0*math.cos(a0)); b1 = (r0*math.sin(a1), y0, r0*math.cos(a1))
            t0 = (r1*math.sin(a0), y1, r1*math.cos(a0)); t1 = (r1*math.sin(a1), y1, r1*math.cos(a1))
            u0, u1 = x + w*i/n, x + w*(i+1)/n
            s.poly([b0, b1, t1], [(u0, y+h), (u1, y+h), (u1, y)], ti); s.poly([b0, t1, t0], [(u0, y+h), (u1, y), (u0, y)], ti)
    def disc(s, r, yv, n, ti, rect, rot=math.pi/8):
        x, y, w, h = rect; cx, cy = x + w/2, y + h/2; c = (0, yv, 0)
        for i in range(n):
            a0, a1 = rot + 2*math.pi*i/n, rot + 2*math.pi*(i+1)/n
            p0 = (r*math.sin(a0), yv, r*math.cos(a0)); p1 = (r*math.sin(a1), yv, r*math.cos(a1))
            s.poly([c, p0, p1], [(cx, cy), (cx + w/2*math.sin(a0), cy - h/2*math.cos(a0)), (cx + w/2*math.sin(a1), cy - h/2*math.cos(a1))], ti)

    # ---- 打包＋寫出
    def pack(s):
        rects = [t[0].shape[:2] for t in s.tex]; order = sorted(range(len(rects)), key=lambda i: -rects[i][0])
        for AW in (32, 64, 128, 256, 512, 1024, 2048):
            pos = {}; x = y = rowh = 0; ok = True
            for i in order:
                h, w = rects[i]; h2, w2 = h + 2, w + 2
                if w2 > AW: ok = False; break
                if x + w2 > AW: x = 0; y += rowh; rowh = 0
                pos[i] = (x + 1, y + 1); x += w2; rowh = max(rowh, h2)
            if not ok: continue
            Ht = y + rowh; AH = 1 << max(4, int(math.ceil(math.log2(max(Ht, 1)))))
            if AH <= AW*2: break
        A = np.zeros((AH, AW, 4), np.uint8); E = np.zeros_like(A); hasE = False
        for i, (t, e) in enumerate(s.tex):
            x, y = pos[i]; h, w = t.shape[:2]
            for dst, src in ((A, t), (E, e)):
                if src is None: continue
                dst[y:y+h, x:x+w] = src
                dst[y-1, x:x+w] = src[0]; dst[y+h, x:x+w] = src[-1]; dst[y:y+h, x-1] = src[:, 0]; dst[y:y+h, x+w] = src[:, -1]   # 1px 邊外延（防 nearest 漏色）
            if e is not None: hasE = True
        return A, (E if hasE else None), pos
    def build(s):
        A, E, pos = s.pack(); AH, AW = A.shape[:2]; P, Nn, UV, I = [], [], [], []
        for verts, tex, ti, nrm in s.faces:
            ox, oy = pos[ti]; g = np.cross(verts[1]-verts[0], verts[-1]-verts[0])
            if len(verts) > 3: g = np.cross(verts[1]-verts[0], verts[2]-verts[0])
            g = _n(g); nn = g if nrm is None else nrm; b = len(P)
            for v, t in zip(verts, tex):
                P.append(v); Nn.append(nn); UV.append(((ox + t[0])/AW, 1 - (oy + t[1])/AH))
            for k in range(1, len(verts)-1): I += [b, b+k, b+k+1]
        return dict(P=np.array(P), N=np.array(Nn), UV=np.array(UV), I=np.array(I, int), A=A, E=E)

def r(v, k=4): return [round(float(x), k) for x in np.ravel(v)]
def write(mb, outdir, rel, zh, footprint, cast=True, recv=True, extra=None):
    """寫 meshes/<id>.json＋.glb＋.png（1x、@3x、emissive）。footprint＝局部座標 {'rect':{'x':[..],'z':[..]}} 或 {'poly':[[x,z]..]} 或 None。"""
    g = mb.build(); assert len(g['I'])//3 <= MAX_TRIS, (mb.id, len(g['I'])//3); os.makedirs(f'{outdir}/{rel}', exist_ok=True); mid = mb.id
    def sv(a, p): Image.fromarray(a).save(f'{outdir}/{rel}/{p}', optimize=True)
    sv(g['A'], f'{mid}.png'); sv(up3(g['A']), f'{mid}@3x.png')
    if g['E'] is not None: sv(g['E'], f'{mid}_emissive.png'); sv(up3(g['E']), f'{mid}_emissive@3x.png')
    P = g['P']; MJ = {'format': 'garden3d.mesh/2', 'id': mid, 'zh': zh,
        'units': '1 unit＝1x art px；Y 上；原點＝物件底中（局部座標；放置用 objects.json x／z（／y））；+Z 向鏡頭',
        'paths': '相對場景根（H1/）',
        'texture': f'{rel}/{mid}.png', 'texture3x': f'{rel}/{mid}@3x.png', 'textureSize': [int(g['A'].shape[1]), int(g['A'].shape[0])],
        'alphaTest': 0.5, 'doubleSided': False,
        'material': {'filter': 'nearest', 'mipmaps': False, 'lit': True, 'colorSpace': 'srgb', 'shading': 'flat（每個頂點 normal 已按面寫好；卡片用向上＋向外嘅著色法線）',
                     'note': '貼圖係 V3 H1 調色像素、冇烘方向光／AO；alpha 0/255'},
        'bounds': {'min': r(P.min(0), 2), 'max': r(P.max(0), 2)}, 'footprint': footprint,
        'castShadow': cast, 'receiveShadow': recv, 'vertexCount': int(len(P)), 'triangleCount': int(len(g['I'])//3),
        'positions': r(P, 3), 'normals': r(g['N'], 4), 'uvs': r(g['UV'], 6), 'indices': [int(i) for i in g['I']]}
    if g['E'] is not None: MJ.update(emissive=f'{rel}/{mid}_emissive.png', emissive3x=f'{rel}/{mid}_emissive@3x.png')
    if extra: MJ.update(extra)
    with open(f'{outdir}/{rel}/{mid}.json', 'w') as f: json.dump(MJ, f, ensure_ascii=False, separators=(',', ':'))
    write_glb(f'{outdir}/{rel}/{mid}.glb', g, mid, dict(footprint=footprint, zh=zh))
    return MJ

def _png(a): b = io.BytesIO(); Image.fromarray(a).save(b, 'PNG', optimize=True); return b.getvalue()
def write_glb(path, g, name, extras):
    P = g['P'].astype(np.float32); N = g['N'].astype(np.float32); UV = g['UV'].astype(np.float32).copy(); UV[:, 1] = 1 - UV[:, 1]   # glTF uv 原點左上
    I = g['I'].astype(np.uint16 if len(P) < 65536 else np.uint32)
    blobs = [P.tobytes(), N.tobytes(), UV.tobytes(), I.tobytes(), _png(g['A'])] + ([_png(g['E'])] if g['E'] is not None else [])
    views = []; buf = b''
    for k, bl in enumerate(blobs):
        while len(buf) % 4: buf += b'\0'
        v = {'buffer': 0, 'byteOffset': len(buf), 'byteLength': len(bl)}
        if k < 3: v['target'] = 34962
        elif k == 3: v['target'] = 34963
        views.append(v); buf += bl
    while len(buf) % 4: buf += b'\0'
    acc = [{'bufferView': 0, 'componentType': 5126, 'count': len(P), 'type': 'VEC3', 'min': P.min(0).tolist(), 'max': P.max(0).tolist()},
           {'bufferView': 1, 'componentType': 5126, 'count': len(P), 'type': 'VEC3'},
           {'bufferView': 2, 'componentType': 5126, 'count': len(P), 'type': 'VEC2'},
           {'bufferView': 3, 'componentType': 5123 if I.dtype == np.uint16 else 5125, 'count': len(I), 'type': 'SCALAR'}]
    mat = {'name': name, 'pbrMetallicRoughness': {'baseColorTexture': {'index': 0}, 'metallicFactor': 0.0, 'roughnessFactor': 1.0},
           'alphaMode': 'MASK', 'alphaCutoff': 0.5, 'doubleSided': False}
    imgs = [{'bufferView': 4, 'mimeType': 'image/png'}]; texs = [{'sampler': 0, 'source': 0}]
    if g['E'] is not None:
        imgs.append({'bufferView': 5, 'mimeType': 'image/png'}); texs.append({'sampler': 0, 'source': 1})
        mat['emissiveTexture'] = {'index': 1}; mat['emissiveFactor'] = [1.0, 1.0, 1.0]
    gl = {'asset': {'version': '2.0', 'generator': 'garden3d_mesh.py（微光小圃）'}, 'scene': 0, 'scenes': [{'nodes': [0]}],
          'nodes': [{'name': name, 'mesh': 0, 'extras': extras}],
          'meshes': [{'name': name, 'primitives': [{'attributes': {'POSITION': 0, 'NORMAL': 1, 'TEXCOORD_0': 2}, 'indices': 3, 'material': 0}]}],
          'materials': [mat], 'textures': texs, 'images': imgs,
          'samplers': [{'magFilter': 9728, 'minFilter': 9728, 'wrapS': 33071, 'wrapT': 33071}],
          'accessors': acc, 'bufferViews': views, 'buffers': [{'byteLength': len(buf)}]}
    js = json.dumps(gl, ensure_ascii=False, separators=(',', ':')).encode('utf8')
    while len(js) % 4: js += b' '
    out = struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(buf)) + struct.pack('<II', len(js), 0x4E4F534A) + js + struct.pack('<II', len(buf), 0x004E4942) + buf
    open(path, 'wb').write(out)
def read_glb(path):
    """（驗證用）讀返 glb → dict(json, P, N, UV, I)。"""
    b = open(path, 'rb').read(); mg, ver, ln = struct.unpack('<III', b[:12]); assert mg == 0x46546C67 and ver == 2 and ln == len(b)
    jl, jt = struct.unpack('<II', b[12:20]); gl = json.loads(b[20:20+jl]); o = 20 + jl; bl, bt = struct.unpack('<II', b[o:o+8]); bin_ = b[o+8:o+8+bl]
    def acc(i):
        a = gl['accessors'][i]; v = gl['bufferViews'][a['bufferView']]; dt = {5126: np.float32, 5123: np.uint16, 5125: np.uint32}[a['componentType']]
        k = {'VEC3': 3, 'VEC2': 2, 'SCALAR': 1}[a['type']]
        return np.frombuffer(bin_[v['byteOffset']:v['byteOffset']+v['byteLength']], dt).reshape(-1, k) if k > 1 else np.frombuffer(bin_[v['byteOffset']:v['byteOffset']+v['byteLength']], dt)
    pr = gl['meshes'][0]['primitives'][0]
    return dict(json=gl, P=acc(pr['attributes']['POSITION']), N=acc(pr['attributes']['NORMAL']), UV=acc(pr['attributes']['TEXCOORD_0']), I=acc(pr['indices']))
