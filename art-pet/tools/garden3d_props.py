#!/usr/bin/env python3
"""garden3d_props.py — H1 場景全部物件轉立體 mesh（八方旅人式：寵物以外全部 3D；低面數＋像素貼圖，alpha 0/255）。
每件由 H1 V3 程序化 2D 美術（同 billboard 同一份像素）起：正面＝原美術 1:1（0° 構圖同平面版一樣），再加厚度／側面／頂面。
  樹：樹幹立體盒（樹皮貼圖）＋鳥屋擠出＋樹冠前／後兩層葉片卡（側卡會喺 0° 露線，唔用）。籬笆：木板像素擠出（厚 3）＋灌木長春藤卡（前後兩層）。
  花盆：八角錐台（貼圖按正投影對位）＋泥面＋花苗交叉卡。菜畦：木框盒（泥面頂）＋苗卡兩排。燈柱／蘑菇／花灑／螢火瓶：按行寬分段像素擠出。
  旗串：燈籠＋燈泡擠出（厚 5）、鐵線同旗擠出（厚 1）。屋後補位：矮樹叢／遠樹林交叉卡。
"""
import math
import numpy as np
from scipy import ndimage as nd
import garden3d_mesh as GM
REL = 'meshes'
UPN = (0, .55, .83)          # 葉片卡著色法線（向上＋向鏡頭，同 billboard 打光一致）
SPN = (.45, .5, .74)         # 側向交叉卡著色法線（仍偏向鏡頭；同幾何法線夾角 <90°，validator 驗逆時針用）

class Ctx:
    def __init__(s, B, lut, ok, mput, pnoise): s.B, s.lut, s.ok, s.mput, s.pnoise = B, lut, ok, mput, pnoise
    def ids(s, *mats): return np.concatenate([s.B.IDX[m] for m in mats])
    def rgba(s, m):
        a = (m > 0) & s.ok[m]; im = np.zeros(m.shape + (4,), np.uint8); im[..., :3] = s.lut[m]; im[..., 3] = a*255; im[~a, :3] = 0; return im
    def fill(s, h, w, mat, f=.5, d=.35, seed=0, amp=.25, streak=None):
        m = np.zeros((h, w), np.uint8); N = max(h, w, 8)
        n = s.pnoise(N, max(2, N//6), seed)[:h, :w]
        ff = np.clip(f + amp*(n - .5)*2, 0, 1)
        if streak == 'v': ff = np.clip(ff + .18*((np.arange(w) % 5 == 0)[None, :] - .3) + .12*(s.pnoise(N, max(2, N//3), seed+1)[:h, :w]-.5), 0, 1)
        if streak == 'h': ff = np.clip(ff - .25*((np.arange(h) % 6 == 5)[:, None]), 0, 1)
        s.mput(m, np.ones((h, w), bool), mat, ff, d); return s.rgba(m)

def solid(mb, im, mask, px0, py0, emis=None, zc=0., k=.7, dmin=2, dmax=12, budget=None, fn=None, split=True):
    """按連通塊＋行寬分段擠出（燈柱、蘑菇、花灑、螢火瓶）；split＝False 每塊一段。"""
    lab, n = nd.label(mask, np.ones((3, 3))); groups = []
    for c in range(1, n+1):
        cm = lab == c; rows = np.where(cm.any(1))[0]; widths = cm.sum(1); start = rows[0]
        if not split: groups.append(cm); continue
        for i in range(1, len(rows)+1):
            if i == len(rows) or abs(int(widths[rows[i]]) - int(widths[rows[i-1]])) > 2:
                g = cm.copy(); g[:start] = False; g[rows[i-1]+1:] = False; groups.append(g)
                if i < len(rows): start = rows[i]
    budget = (budget or (GM.MAX_TRIS - mb.ntris())) - 4*len(groups); tot = sum(g.sum() for g in groups)
    for g in groups:
        w = int(g.sum(1).max()); d = int(np.clip(round(w*k), dmin, dmax))
        mb.extrude(im, g, d, px0, py0, zc, emis, budget=max(8, int(budget*g.sum()/tot)), front_normal=fn)

def build_all(X, parts, gh_mb):
    """parts[oid]＝(rgba, idx, emis or None, ent)；回傳 objects.json entries（type mesh）。"""
    out = []
    def put(mb, oid, ent, zh, fp, extra_ent=None, cast=True, origin=(0, 0)):
        MJ = GM.write(mb, X.OUT, REL, zh, fp, cast=cast)
        e = dict(id=oid, type='mesh', zh=zh, mesh=f'{REL}/{oid}.json', glb=f'{REL}/{oid}.glb', x=round(ent['x'] + origin[0], 2), z=round(ent['z'] + origin[1], 2), yawDeg=0,
                 castShadow=cast, receiveShadow=True, layer=ent.get('layer', 'mid'), triangles=MJ['triangleCount'])
        if ent.get('y'): e['y'] = ent['y']
        if fp:
            if 'rect' in fp:
                e['footprint'] = dict(type='rect', x=[round(e['x'] + fp['rect']['x'][0], 2), round(e['x'] + fp['rect']['x'][1], 2)],
                                      z=[round(e['z'] + fp['rect']['z'][0], 2), round(e['z'] + fp['rect']['z'][1], 2)], pad=fp.get('pad', 2))
            else:
                e['footprint'] = dict(type='poly', points=[[round(e['x'] + p[0], 2), round(e['z'] + p[1], 2)] for p in fp['poly']], pad=fp.get('pad', 2))
        if ent.get('emissiveLight') and MJ.get('emissive'): e['emissiveLight'] = ent['emissiveLight']
        if extra_ent: e.update(extra_ent)
        out.append(e)
    B = X.B
    # ---------------- 大樹
    im, idx, em, ent = parts['tree']; h, w = idx.shape; px0, py0 = ent['pivot'][0]*w, ent['pivot'][1]*h
    mb = GM.MB('tree'); tr = np.isin(idx, X.ids('TRUNK')); bh = np.isin(idx, X.ids('ROOF', 'WOOD', 'METAL'))
    c0, c1 = int(round(px0 - 8)), int(round(px0 + 8)); TH = 170
    core = tr.copy(); core[:, :c0] = False; core[:, c1:] = False
    bark = X.fill(TH, 16, 'TRUNK', .45, seed=31, streak='v'); fr = bark.copy(); r0 = int(py0 - TH)
    seg = im[r0:int(py0), c0:c1]; k = core[r0:int(py0), c0:c1]; fr[k] = seg[k]
    tf = mb.add_tex(fr); tb = mb.add_tex(bark); tt = mb.add_tex(X.fill(14, 16, 'TRUNK', .7, seed=32))
    mb.box(c0 - px0, c1 - px0, 0, TH, -7, 7, {'front': tf, 'all': tb, 'top': tt})
    mb.extrude(im, bh, 8, px0, py0, 7 + 4, budget=60)
    can = im.copy(); can[core | bh] = 0; ys = np.where(can[..., 3].any(1))[0]
    tc = mb.add_tex(can)
    mb.card((-px0, py0 - h, 9), (w, 0, 0), (0, h, 0), tc, None, UPN)                                   # 前卡（＝原 billboard 樹冠）
    crow = 100; cc0, cc1 = 14, 84
    mb.card((-px0 + w, py0 - crow, -12), (-w, 0, 0), (0, crow, 0), tc, (0, 0, w, crow), (0, .6, -.8))   # 後卡（鏡像，樹冠上半）
    put(mb, 'tree', ent, '大樹（樹幹立體＋鳥屋＋樹冠前後葉片卡）', {'rect': {'x': [c0 - px0 - 2, c1 - px0 + 2], 'z': [-9, 9]}, 'pad': 3})
    # ---------------- 籬笆
    im, idx, em, ent = parts['fence']; h, w = idx.shape; px0, py0 = ent['pivot'][0]*w, ent['pivot'][1]*h
    mb = GM.MB('fence'); wd = np.isin(idx, X.ids('WOOD')); lf = (im[..., 3] > 0) & ~wd
    lv = im.copy(); lv[~lf] = 0; tl = mb.add_tex(lv)
    mb.card((-px0, py0 - h, 3), (w, 0, 0), (0, h, 0), tl, None, UPN)
    bush = lv.copy(); bush[:16] = 0; tb2 = mb.add_tex(bush)
    mb.card((-px0 + w - 3, py0 - h, -4), (-w, 0, 0), (0, h, 0), tb2, None, (0, .6, -.8))
    mb.extrude(im, wd, 3, px0, py0, 0, min_run=2)
    put(mb, 'fence', ent, '籬笆（木板擠出厚 3）＋灌木／長春藤前後卡', {'rect': {'x': [-px0, w - px0], 'z': [-5, 4]}, 'pad': 2})
    # ---------------- 旗串燈籠
    im, idx, em, ent = parts['lanterns']; h, w = idx.shape; px0, py0 = ent['pivot'][0]*w, ent['pivot'][1]*h
    mb = GM.MB('lanterns'); lt = np.isin(idx, X.ids('LANTERN', 'BULB')); mt = (im[..., 3] > 0) & ~lt
    mb.extrude(im, mt, 1, px0, py0, 0, em, min_run=2, budget=90)
    solid(mb, im, lt, px0, py0, em, k=.8, dmin=2, dmax=5, split=False)
    put(mb, 'lanterns', ent, '旗串：燈籠／燈泡擠出（厚 2–5，發光）＋鐵線旗（厚 1）', None, cast=False)
    # ---------------- 菜畦
    im, idx, em, ent = parts['bed']; h, w = idx.shape; px0, py0 = ent['pivot'][0]*w, ent['pivot'][1]*h
    mb = GM.MB('bed'); wd = np.isin(idx, X.ids('WOOD')); wr = np.where(wd.any(1))[0]; HB = int(py0 - wr.min()); D = 18; zc = -D/2
    frn = X.fill(HB, w, 'WOOD', .5, seed=41, streak='h'); seg = im[wr.min():int(py0)]; k = wd[wr.min():int(py0)]; frn[k] = seg[k]
    top = X.fill(D, w, 'SOIL', .45, seed=42); tm = np.zeros((D, w), np.uint8)
    X.mput(tm, (np.arange(D)[:, None] % 4 == 1) & np.ones((D, w), bool), 'SOIL', .15, 0); top[tm > 0] = X.rgba(tm)[tm > 0]
    rim = X.fill(D, w, 'WOOD', .62, seed=43); top[:2] = rim[:2]; top[-2:] = rim[-2:]; top[:, :2] = rim[:, :2]; top[:, -2:] = rim[:, -2:]
    tf = mb.add_tex(frn); ts = mb.add_tex(X.fill(HB, D, 'WOOD', .42, seed=44, streak='h')); tbk = mb.add_tex(X.fill(HB, w, 'WOOD', .4, seed=45, streak='h')); ttp = mb.add_tex(top)
    mb.box(-px0, w - px0, 0, HB, -D/2, D/2, {'front': tf, 'back': tbk, 'left': ts, 'right': ts, 'top': ttp})
    sp = im.copy(); sp[wd] = 0; sp[int(py0 - HB):] = 0; ts2 = mb.add_tex(sp)
    mb.card((-px0, py0 - h, 4), (w, 0, 0), (0, h, 0), ts2, None, UPN)
    mb.card((-px0 + 4, py0 - h, -4), (w, 0, 0), (0, h, 0), ts2, None, UPN)
    put(mb, 'bed', ent, '菜畦（木框盒＋泥面頂＋苗卡兩排）', {'rect': {'x': [-px0, w - px0], 'z': [-D/2, D/2]}, 'pad': 2}, origin=(0, zc))
    # ---------------- 燈柱／蘑菇／花灑／螢火瓶
    for oid, zh, kk, dmax, fpz in (('lamp', '燈柱（按行寬分段擠出；燈頭發光）', .75, 10, 3), ('mushrooms', '蘑菇叢（每朵擠出：菇傘闊、菇柄細）', .4, 6, 4),
                                   ('can', '花灑（擠出；壺身厚、壺嘴薄）', .45, 11, 5), ('jar', '螢火瓶（擠出；發光）', .9, 6, 3)):
        im, idx, em, ent = parts[oid]; h, w = idx.shape; px0, py0 = ent['pivot'][0]*w, ent['pivot'][1]*h
        mb = GM.MB(oid); solid(mb, im, im[..., 3] > 0, px0, py0, em, k=kk, dmax=dmax)
        bot = np.where((im[..., 3] > 0)[int(py0) - 4:int(py0)].any(0))[0]
        x0, x1 = (bot.min() - px0, bot.max() + 1 - px0) if len(bot) else (-2, 2)
        put(mb, oid, ent, zh, {'rect': {'x': [round(x0, 2), round(x1, 2)], 'z': [-fpz, fpz]}, 'pad': 2})
    # ---------------- 花盆（八角錐台）
    for oid in ('pot_L', 'pot_R', 'pot_S'):
        im, idx, em, ent = parts[oid]; h, w = idx.shape; px0, py0 = ent['pivot'][0]*w, ent['pivot'][1]*h
        mb = GM.MB(oid); pm = np.isin(idx, X.ids('POT')); rows = np.where(pm.any(1))[0]; rt, rb = rows.min(), int(min(rows.max() + 1, py0))
        wt = pm[rt:rt+4].sum(1).max(); wb = pm[rb - 1].sum(); r1, r0 = wt/2, wb/2; Hp = rb - rt
        body = np.zeros((Hp, w, 4), np.uint8); body[pm[rt:rb]] = im[rt:rb][pm[rt:rb]]
        for yy in range(Hp):                                   # 每行擴到全闊（錐台每行按正投影取色）
            xs = np.where(pm[rt + yy])[0]
            if len(xs): body[yy, :xs.min()] = im[rt + yy, xs.min()]; body[yy, xs.max()+1:] = im[rt + yy, xs.max()]
        body[..., 3] = 255; tbody = mb.add_tex(body)
        cx = px0; n = 8
        for i in range(n):
            a0, a1 = -math.pi/2 + 2*math.pi*i/n, -math.pi/2 + 2*math.pi*(i+1)/n
            def V(r, a, y): return (r*math.sin(a), y, r*math.cos(a))
            yb, yt = py0 - rb, py0 - rt
            ub0, ub1 = cx + r0*math.sin(a0), cx + r0*math.sin(a1); ut0, ut1 = cx + r1*math.sin(a0), cx + r1*math.sin(a1)
            mb.poly([V(r0, a0, yb), V(r0, a1, yb), V(r1, a1, yt)], [(ub0, Hp), (ub1, Hp), (ut1, 0)], tbody)
            mb.poly([V(r0, a0, yb), V(r1, a1, yt), V(r1, a0, yt)], [(ub0, Hp), (ut1, 0), (ut0, 0)], tbody)
        soil = X.fill(int(2*r1) + 1, int(2*r1) + 1, 'SOIL', .4, seed=51); ts = mb.add_tex(soil)
        mb.disc(r1 - .6, py0 - rt - 1, 8, ts, (0, 0, soil.shape[1], soil.shape[0]), rot=-math.pi/2)
        pl = im.copy(); pl[rt:] = 0; pl[np.isin(idx, X.ids('SOIL'))] = 0; pr = np.where(pl[..., 3].any(1))[0]
        if len(pr):
            tp = mb.add_tex(pl[:rt + 1]); hh = rt + 1; y0 = py0 - hh
            mb.card((-px0, y0, 0), (w, 0, 0), (0, hh, 0), tp, None, UPN)
            mb.card((0, y0, w*.4), (0, 0, -w*.8), (0, hh, 0), tp, (int(w*.1), 0, int(w*.8), hh), SPN)
        put(mb, oid, ent, f"花盆 {oid[-1]}（八角錐台＋泥面＋花苗交叉卡）", {'poly': [[round(r0*math.sin(a), 2), round(r0*math.cos(a), 2)] for a in np.arange(8)*math.pi/4], 'pad': 2})
    # ---------------- 屋後補位（交叉卡）
    for oid, (im, ent) in parts['_backfill'].items():
        h, w = im.shape[:2]; mb = GM.MB(oid); t = mb.add_tex(im)
        mb.card((-w/2, 0, 0), (w, 0, 0), (0, h, 0), t, None, UPN)
        mb.card((0, 0, w*.35), (0, 0, -w*.7), (0, h, 0), t, (int(w*.15), 0, int(w*.7), h), SPN)
        put(mb, oid, ent, ent['zh'] + '（交叉卡）', None, cast=False, extra_ent=dict(backfill=True))
    # ---------------- 小屋
    hb, hent = gh_mb
    MJ = GM.write(hb, X.OUT, REL, hent['zh'], hent['fpLocal'])
    e = dict(id='cottage', type='mesh', zh=hent['zh'], mesh=f'{REL}/cottage.json', glb=f'{REL}/cottage.glb', x=hent['x'], z=hent['z'], yawDeg=0,
             castShadow=True, receiveShadow=True, layer='mid', triangles=MJ['triangleCount'], emissiveLight='window',
             footprint=dict(type='rect', x=hent['fp']['x'], z=hent['fp']['z'], pad=hent['fp']['pad']))
    out.insert(2, e)
    return out
