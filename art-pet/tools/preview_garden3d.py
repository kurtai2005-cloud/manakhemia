#!/usr/bin/env python3
"""preview_garden3d.py — 3D 花園試點 H1 預覽（純 numpy 光線投射，照 objects/lights/camera.json 砌，驗證格式同擺位）。
輸出：/workspace/game-design/pilot3d_h1/{parts_sheet,assembled_3d,ground_top,normals_pets}.png
"""
import os, sys, json, math
import numpy as np
from PIL import Image, ImageDraw
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import ui_hd2d_v3_lib as L
ART = os.path.abspath(f'{HERE}/..'); SRC = f'{ART}/scenes/garden3d/H1'; PV = '/workspace/game-design/pilot3d_h1'
J = json.load(open(f'{SRC}/objects.json')); LJ = json.load(open(f'{SRC}/lights.json')); CJ = json.load(open(f'{SRC}/camera.json'))
def hx(h): h = h.lstrip('#'); return np.array([int(h[i:i+2], 16) for i in (0, 2, 4)], float)/255
def img(p, mode='RGBA'): return np.array(Image.open(f'{SRC}/{p}').convert(mode)).astype(float)/255
TEX = {}
def tex(p):
    if p not in TEX: TEX[p] = img(p)
    return TEX[p]
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

def render(yaw, night=False, W=390, H=844):
    tg = np.array(CJ['target'], float); p = math.radians(CJ['pitchDeg']); yw = math.radians(yaw)
    C = tg + CJ['dist']*np.array([math.sin(yw)*math.cos(p), math.sin(p), math.cos(yw)*math.cos(p)])
    fw = (tg-C)/np.linalg.norm(tg-C); rt = np.cross(fw, [0, 1, 0]); rt /= np.linalg.norm(rt); up = np.cross(rt, fw)
    tv = math.tan(math.radians(CJ['fovDeg'])/2); th = tv*W/H
    jj, ii = np.mgrid[0:H, 0:W].astype(float)
    D = fw + ((2*(ii+.5)/W-1)*th)[..., None]*rt - ((2*(jj+.5)/H-1)*tv)[..., None]*up
    D /= np.linalg.norm(D, axis=-1, keepdims=True)
    sun = LJ['sun']; sd = np.array(sun['dir']); sI = (LJ['night']['sun'] if night else sun['intensity']); sc = hx(sun['color'])
    amb = hx(LJ['night']['ambient'])*LJ['night']['ambientIntensity'] if night else hx(sun['ambient']['color'])*sun['ambient']['intensity']
    lights = [(np.array([l['x'], l['y'], l['z']], float), hx(l['color']), l['radius'], l['intensityNight'] if night else l['intensity']) for l in LJ['lights']]
    def points(P, nrm, wrap=0.):
        acc = np.zeros(P.shape)
        for lp, lc, r, I in lights:
            if I <= 0: continue
            Lv = lp - P; d = np.linalg.norm(Lv, axis=-1); att = np.clip(1-(d/r)**2, 0, 1)**2
            ndl = np.clip(((nrm*Lv).sum(-1)/np.maximum(d, 1e-3) + wrap)/(1+wrap), 0, 1)
            acc += (att*ndl*I)[..., None]*lc
        return acc
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
    for o in J['objects'] + [dict(J['pet'], id='pet', w=40, h=40)]:
        if not o.get('shadow') or o.get('y'): continue
        if o['face'] == 'cyl':
            r = {'tree': 26}.get(o['id'], max(5, min(o['w']*.45, 18)))
            ox, oz = o['x'] + sd[0]/-sd[1]*r*.5, o['z'] + sd[2]/-sd[1]*r*.5
            sh *= 1 - .38*np.exp(-(((X-ox)/r)**2 + ((Z-oz)/(r*.6))**2)*2)
        else:
            x0 = o['x'] - o['w']*o['pivot'][0]; k = (X > x0) & (X < x0+o['w'])
            sh *= 1 - .3*k*np.exp(-(((Z-o['z']-6)/7)**2))
    nG = np.zeros(P.shape); nG[..., 1] = 1
    litg = amb + (sI*max(0, -sd[1])*sh)[..., None]*sc
    gcol = alb*aoo[..., None]*litg + alb*points(P, nG)
    m = hit; col[m] = gcol[m]; depth[m] = t[m]
    # billboards／背景板／寵物
    pc, pn, pe, ppv = pet_frame()
    items = J['objects'] + [dict(id='pet', x=0, z=0, w=pc.shape[1], h=pc.shape[0], pivot=list(ppv), face='cyl', layer='mid')]
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
                out = out + pe[iv, iu][a][:, :3]*(pe[iv, iu][a][:, 3:4])*(1.0 if not night else 1.0)*.6
            elif e is not None:
                ln = o.get('emissiveLight'); I = 0
                for l in LJ['lights']:
                    if l['id'] == ln: I = l['intensityNight'] if night else l['intensity']
                if o['id'] == 'lanterns': I = max(I, 0)
                out = out + e[a][:, :3]*e[a][:, 3:4]*I
        col[sel] = out; depth[sel] = tt[sel]
    # 霧
    fg = LJ['fog']; fk = np.clip((depth-fg['near'])/(fg['far']-fg['near']), 0, 1)*(.25 if night else .45)
    fc = hx(fg['color']) if not night else np.array([.16, .2, .36])
    col = np.where(np.isfinite(depth)[..., None], col*(1-fk[..., None]) + fc*fk[..., None], fc)
    return (np.clip(col, 0, 1)*255+.5).astype(np.uint8)

def assembled():
    views = [(-25, False, '軌道 −25°'), (0, False, '軌道 0°（預設）'), (25, False, '軌道 +25°'), (0, True, '夜間燈光測試 0°')]
    W, H = 390, 844; pad = 12; top = 64
    sheet = Image.new('RGB', (len(views)*(W+pad)+pad, H+top+pad), (24, 26, 38)); d = ImageDraw.Draw(sheet)
    label(d, (pad, 14), '3D 花園試點 H1 — 照 objects／lights／camera.json 砌（numpy 光線投射預覽，非引擎畫面）', 22)
    for i, (yw, nt, s) in enumerate(views):
        im = Image.fromarray(render(yw, nt, W, H)); sheet.paste(im, (pad+i*(W+pad), top)); label(d, (pad+i*(W+pad)+8, top+8), s, 20)
    sheet.save(f'{PV}/assembled_3d.png', optimize=True)

def parts_sheet():
    objs = [o for o in J['objects'] if o['layer'] != 'far']
    W = 1500; sc = 2; x = y = 0; rows = []; cur = []; rowh = 0; mw = 150
    for o in objs:
        w = max(o['w']*sc, mw) + 24
        if x + w > W-24 and cur: rows.append((cur, rowh)); cur = []; x = 0; rowh = 0
        cur.append((o, x)); x += w; rowh = max(rowh, o['h']*sc + 64)
    rows.append((cur, rowh))
    bgs = [o for o in J['objects'] if o['layer'] == 'far']
    Htot = 80 + sum(r[1] for r in rows) + 2*130 + 60
    sh = Image.new('RGB', (W, Htot), (52, 58, 76)); d = ImageDraw.Draw(sh)
    label(d, (24, 20), '3D 花園 H1 — billboard 件（1x ×2 顯示；紅點＝pivot；黃框＝有 emissive）', 22)
    yy = 80
    for cur, rh in rows:
        for o, xx in cur:
            im = Image.open(f"{SRC}/{o['file']}").convert('RGBA'); im = im.resize((im.width*sc, im.height*sc), Image.NEAREST)
            X0, Y0 = 24+xx, yy+rh-40-im.height; sh.paste(im, (X0, Y0), im)
            px, py = X0 + o['pivot'][0]*im.width, Y0 + o['pivot'][1]*im.height; d.ellipse((px-4, py-4, px+4, py+4), fill=(255, 60, 60))
            if o.get('emissive'): d.rectangle((X0-2, Y0-2, X0+im.width+1, Y0+im.height+1), outline=(255, 214, 90), width=2)
            label(d, (X0, yy+rh-32), f"{o['id']} {o['w']}×{o['h']}", 18)
        yy += rh
    for o in bgs:
        im = Image.open(f"{SRC}/{o['file']}").convert('RGBA'); k = (W-48)/im.width; im = im.resize((W-48, max(1, int(im.height*k))), Image.NEAREST)
        im = im.crop((0, max(0, im.height-110), im.width, im.height)); sh.paste(im, (24, yy+10), im)
        label(d, (32, yy+16), f"{o['id']}  z={o['z']}  {o['w']}×{o['h']} units（圖 ×{o['unitsPerPx']}）— 只顯示底部", 18); yy += 130
    sh.save(f'{PV}/parts_sheet.png', optimize=True)

def ground_top():
    g = Image.open(f"{SRC}/{J['ground']['file3x']}").convert('RGB'); ao = Image.open(f"{SRC}/{J['ground']['ao3x']}").convert('L')
    ga = (np.array(g).astype(float)*(np.array(ao).astype(float)[..., None]/255)).astype(np.uint8)
    W = 768*2 + 72; sh = Image.new('RGB', (W, 768+120), (30, 32, 44)); d = ImageDraw.Draw(sh)
    label(d, (24, 18), '地面 768×768（@3x）：左＝ground＋AO 乘埋＋物件腳位；右＝ground_ao', 22)
    a = Image.fromarray(ga); da = ImageDraw.Draw(a)
    for o in J['objects']:
        if o['layer'] == 'far': continue
        cx, cz = (o['x']+128)*3, (o['z']+128)*3
        if o['face'] == 'fixed':
            x0 = (o['x'] - o['w']*o['pivot'][0] + 128)*3; da.line((x0, cz, x0+o['w']*3, cz), fill=(255, 80, 80), width=3)
        da.ellipse((cx-6, cz-6, cx+6, cz+6), outline=(255, 255, 255), width=2)
        f = L.F('sansb', 18); da.text((cx+8, cz-24), o['id'], font=f, fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
    da.line((384-12, 384, 384+12, 384), fill=(80, 200, 255), width=2); da.line((384, 384-12, 384, 384+12), fill=(80, 200, 255), width=2)
    sh.paste(a, (24, 72)); sh.paste(ao.convert('RGB'), (24+768+24, 72))
    label(d, (24, 72+768+14), '十字＝原點（寵物）；上＝−Z（遠，屋／籬笆）；下＝+Z（向鏡頭）；紅線＝fixed 板位置', 18)
    sh.save(f'{PV}/ground_top.png', optimize=True)

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

if __name__ == '__main__':
    os.makedirs(PV, exist_ok=True)
    parts_sheet(); ground_top(); normals_pets(); assembled(); print('ok', sorted(os.listdir(PV)))
