#!/usr/bin/env python3
"""validate_garden3d.py — 驗 art-pet/scenes/garden3d/H1（garden3d.mesh/2＋.glb、footprint 碰撞、燈、鏡頭；格式見 FORMAT.md）＋團絨 _n／dir4 atlas。
用法：PYTHONDONTWRITEBYTECODE=1 python3 tools/validate_garden3d.py [--src 場景目錄]  → 印結果＋寫 <場景>/validation.json
  --src 預設＝$GARDEN3D_SRC 或 art-pet/scenes/garden3d/H1
"""
import os, sys, json, re
import numpy as np
from PIL import Image
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__)); ART = os.path.abspath(f'{HERE}/..'); D = os.environ.get('GARDEN3D_SRC') or f'{ART}/scenes/garden3d/H1'
if '--src' in sys.argv: D = sys.argv[sys.argv.index('--src') + 1]
D = os.path.abspath(D)
R = []
def chk(name, ok, info=''): R.append(dict(check=name, ok=bool(ok), info=str(info)[:300]))
def A(p, mode=None):
    im = Image.open(p); return np.array(im.convert(mode) if mode else im)
def up3(a): return np.repeat(np.repeat(a, 3, 0), 3, 1)
HEX = re.compile(r'^#[0-9a-f]{6}$')
try:
    J = json.load(open(f'{D}/objects.json')); LJ = json.load(open(f'{D}/lights.json')); CJ = json.load(open(f'{D}/camera.json')); PJ = json.load(open(f'{D}/pets_normals.json'))
    chk('json 讀得', True)
except Exception as e:
    chk('json 讀得', False, e); J = None
used = {'objects.json', 'lights.json', 'camera.json', 'pets_normals.json', 'FORMAT.md', 'validation.json'}
if J:
    g = J['ground']
    for k, sz, mode in (('file', 256, 'RGB'), ('file3x', 768, 'RGB'), ('ao', 256, 'L'), ('ao3x', 768, 'L')):
        p = f"{D}/{g[k]}"; used.add(g[k]); im = Image.open(p)
        chk(f'地面 {k} 尺寸 {sz}', im.size == (sz, sz), im.size); chk(f'地面 {k} 色彩模式 {mode}', im.mode == mode, im.mode)
    g1, g3 = A(f"{D}/{g['file']}"), A(f"{D}/{g['file3x']}"); chk('地面 @3x＝1x 最近鄰 ×3', np.array_equal(up3(g1), g3))
    ao = A(f"{D}/{g['ao']}").astype(int); chk('AO 範圍合理（min≥60、中位≥250）', ao.min() >= 60 and np.median(ao) >= 250, (ao.min(), np.median(ao)))
    t = g['outerTile']; used.update([t['file'], t['file3x']]); t1 = A(f"{D}/{t['file']}")
    chk('外圍 tile 64×64、@3x 192', t1.shape[:2] == (64, 64) and A(f"{D}/{t['file3x']}").shape[:2] == (192, 192))
    tt = np.tile(t1, (4, 4, 1)); ring = np.zeros((256, 256), bool); ring[:4] = ring[-4:] = True; ring[:, :4] = ring[:, -4:] = True
    chk('256 片邊 4px 同 tile 一致（無縫）', np.mean(np.all(g1[ring] == tt[ring], -1)) >= .98, np.mean(np.all(g1[ring] == tt[ring], -1)))
    ids = set(); LAYERS = {'near', 'mid', 'far'}; LID = {l['id'] for l in LJ['lights']}
    meshes = []
    for o in J['objects']:
        oid = o['id']; chk(f'{oid} id 唯一', oid not in ids); ids.add(oid)
        chk(f'{oid} type 合法（mesh／backdrop；寵物係唯一 billboard、唔喺 objects）', o.get('type') in ('mesh', 'backdrop'), o.get('type'))
        if o.get('type') == 'mesh': meshes.append(o); continue
        need = ['id', 'file', 'file3x', 'x', 'z', 'w', 'h', 'pivot', 'face', 'layer', 'unitsPerPx']
        chk(f'{oid} 背景板欄位齊', all(k in o for k in need), [k for k in need if k not in o])
        p1, p3 = f"{D}/{o['file']}", f"{D}/{o['file3x']}"; used.update([o['file'], o['file3x']]); a1, a3 = A(p1), A(p3)
        chk(f'{oid} RGBA、@3x＝1x×3 最近鄰', a1.ndim == 3 and a1.shape[2] == 4 and np.array_equal(up3(a1), a3))
        al = set(np.unique(a1[..., 3]).tolist()); chk(f'{oid} 背景板 layer far、z ≤ −300、alpha 0/255', o['layer'] == 'far' and o['z'] <= -300 and al <= {0, 255}, (o['z'], al))
        chk(f'{oid} 尺寸＝px×unitsPerPx', abs(o['w'] - a1.shape[1]*o['unitsPerPx']) < 1 and abs(o['h'] - a1.shape[0]*o['unitsPerPx']) < 1)
    # ---- 立體 mesh（garden3d.mesh/2；格式見 FORMAT.md）
    sys.path.insert(0, HERE); import garden3d_mesh as GM
    chk('全部場景件係 mesh（≥15 件，有 cottage／tree／fence）', len(meshes) >= 15 and {'cottage', 'tree', 'fence'} <= {m['id'] for m in meshes}, len(meshes))
    def pow2(n): return n > 0 and n & (n - 1) == 0
    for o in meshes:
        oid = o['id']; need = ['id', 'type', 'zh', 'mesh', 'glb', 'x', 'z', 'yawDeg', 'castShadow', 'receiveShadow', 'layer', 'triangles']
        chk(f'{oid} objects entry 欄位齊', all(k in o for k in need) and o['layer'] in LAYERS and isinstance(o['castShadow'], bool) and isinstance(o['receiveShadow'], bool), [k for k in need if k not in o])
        used.update([o['mesh'], o['glb']]); MJ = json.load(open(f"{D}/{o['mesh']}"))
        chk(f'{oid} format garden3d.mesh/2、id', MJ.get('format') == 'garden3d.mesh/2' and MJ.get('id') == oid, (MJ.get('format'), MJ.get('id')))
        P = np.array(MJ['positions'], float); N = np.array(MJ['normals'], float); UV = np.array(MJ['uvs'], float); I = np.array(MJ['indices'], int)
        nv = len(P)//3; nt = len(I)//3
        okl = len(P) % 3 == 0 and len(N) == len(P) and len(UV) == 2*nv and len(I) % 3 == 0 and I.min() >= 0 and I.max() < nv
        chk(f'{oid} 陣列長度／index 範圍', okl and MJ['vertexCount'] == nv and MJ['triangleCount'] == nt == o['triangles'], (nv, nt))
        chk(f'{oid} 三角 ≤ 300', nt <= 300, nt)
        P, N, UV, I = P.reshape(-1, 3), N.reshape(-1, 3), UV.reshape(-1, 2), I.reshape(-1, 3)
        chk(f'{oid} normals 單位長', np.abs(np.linalg.norm(N, axis=1) - 1).max() < 1e-3)
        chk(f'{oid} uv 0..1（V 上）', UV.min() >= -1e-6 and UV.max() <= 1 + 1e-6, (UV.min(), UV.max()))
        g = np.cross(P[I[:, 1]] - P[I[:, 0]], P[I[:, 2]] - P[I[:, 0]]); ar = np.linalg.norm(g, axis=1)
        chk(f'{oid} 冇退化三角', ar.min() > 1e-6, ar.min())
        dots = ((g/ar[:, None])*N[I].mean(1)).sum(1)
        chk(f'{oid} 逆時針＝正面（幾何法線同頂點 normal 同向）', dots.min() > .1, round(float(dots.min()), 3))
        b0, b1 = np.array(MJ['bounds']['min']), np.array(MJ['bounds']['max'])
        chk(f'{oid} bounds 啱、底 y≈0（原點＝底中）', np.allclose(P.min(0), b0, atol=1e-3) and np.allclose(P.max(0), b1, atol=1e-3) and abs(b0[1]) < 1e-3, (b0, b1))
        tx = A(f"{D}/{MJ['texture']}"); t3 = A(f"{D}/{MJ['texture3x']}"); used.update([MJ['texture'], MJ['texture3x']])
        chk(f'{oid} 貼圖 RGBA、2 次方、size 啱、@3x＝1x×3', tx.ndim == 3 and tx.shape[2] == 4 and pow2(tx.shape[0]) and pow2(tx.shape[1]) and [tx.shape[1], tx.shape[0]] == MJ['textureSize'] and np.array_equal(up3(tx), t3), tx.shape)
        al = set(np.unique(tx[..., 3]).tolist()); chk(f'{oid} 貼圖 alpha 只有 0/255、透明處 RGB=0', al <= {0, 255} and not tx[tx[..., 3] == 0, :3].any(), al)
        h_, w_ = tx.shape[:2]; emp = 0
        for t_ in UV[I]:
            u0, u1 = int(t_[:, 0].min()*w_), int(np.ceil(t_[:, 0].max()*w_)); v0, v1 = int((1 - t_[:, 1].max())*h_), int(np.ceil((1 - t_[:, 1].min())*h_))
            emp += not tx[v0:max(v1, v0+1), u0:max(u1, u0+1), 3].any()
        chk(f'{oid} 每個三角 uv 範圍都有像素（冇空三角）', emp == 0, emp)
        chk(f'{oid} alphaTest／doubleSided／material', MJ.get('alphaTest') == .5 and MJ.get('doubleSided') is False and MJ['material'].get('filter') == 'nearest')
        if MJ.get('emissive'):
            e1, e3 = A(f"{D}/{MJ['emissive']}"), A(f"{D}/{MJ['emissive3x']}"); used.update([MJ['emissive'], MJ['emissive3x']])
            chk(f'{oid} emissive 同尺寸、@3x、⊂ alpha', e1.shape == tx.shape and np.array_equal(up3(e1), e3) and not np.any((e1[..., 3] > 0) & (tx[..., 3] == 0)))
            chk(f'{oid} emissiveLight 指向 lights', o.get('emissiveLight') in LID, o.get('emissiveLight'))
        fp = o.get('footprint'); lf = MJ.get('footprint')
        if o.get('backfill') or o.get('y'):
            chk(f'{oid} 補位／吊件冇 footprint（唔阻寵物）', fp is None and lf is None)
            if o.get('backfill'): chk(f'{oid} 補位件喺外圍草地（|x|≤640、z −480…−95）、唔投影', abs(o['x']) <= 640 and -480 <= o['z'] <= -95 and not o['castShadow'], (o['x'], o['z']))
        else:
            okf = fp is not None and lf is not None and fp.get('pad', -1) >= 0 and fp['pad'] == lf['pad']
            if okf and fp['type'] == 'rect':
                okf = fp['x'][0] < fp['x'][1] and fp['z'][0] < fp['z'][1] and np.allclose([fp['x'][0] - o['x'], fp['x'][1] - o['x'], fp['z'][0] - o['z'], fp['z'][1] - o['z']], lf['rect']['x'] + lf['rect']['z'], atol=.01)
            elif okf:
                pts = np.array(fp['points']); lp = np.array(lf['poly']); okf = len(pts) >= 3 and np.allclose(pts - [o['x'], o['z']], lp, atol=.02)
            chk(f'{oid} footprint（世界）合法、同 mesh 局部一致', okf, fp)
            chk(f'{oid} 喺 256 地面內', abs(o['x']) <= 128 and abs(o['z']) <= 128, (o['x'], o['z']))
        # glb
        try:
            G = GM.read_glb(f"{D}/{o['glb']}"); gl = G['json']
            okg = np.allclose(G['P'], P, atol=1e-3) and np.allclose(G['N'], N, atol=1e-4) and np.allclose(G['UV'][:, 0], UV[:, 0], atol=1e-5) and np.allclose(G['UV'][:, 1], 1 - UV[:, 1], atol=1e-5) and np.array_equal(G['I'].reshape(-1, 3), I)
            mt = gl['materials'][0]; smp = gl['samplers'][0]
            okm = mt.get('alphaMode') == 'MASK' and smp.get('magFilter') == 9728 and smp.get('minFilter') == 9728 and len(gl['images']) == 1 + bool(MJ.get('emissive')) and bool(mt.get('emissiveTexture')) == bool(MJ.get('emissive'))
            chk(f'{oid} .glb（glTF 2.0）幾何／uv（V 翻）／index 同 json 一致', okg)
            chk(f'{oid} .glb 材質 MASK＋NEAREST＋內嵌貼圖（＋emissive）', okm, (mt.get('alphaMode'), smp))
        except Exception as e:
            chk(f'{oid} .glb 讀得', False, e)
    # ---- 寵物 billboard＋行路
    pt = J['pet']; chk('寵物 billboard 欄位（billboard、radius、dir4）', pt.get('billboard') is True and pt.get('radius', 0) > 0 and os.path.exists(f"{ART}/{pt.get('dir4', '')}"), pt)
    try:
        import preview_garden3d as PG; PG.load(D, '/dev/null')
        bad = [(round(x, 1), round(z, 1), PG.blocked(x, z)) for x, z, _, _ in PG.walk_path() if PG.blocked(x, z)] + [(x, z, PG.blocked(x, z)) for x, z, _, _ in PG.OCC if PG.blocked(x, z)]
        chk('寵物原點／GIF 行路／遮擋格都唔撞 footprint（含 pad＋radius）', not PG.blocked(pt['x'], pt['z']) and not bad, bad)
        chk('碰撞自測：企入樹幹／屋會被擋', 'tree' in PG.blocked(-88, -44) and 'cottage' in PG.blocked(82, -72) and 'pot_S' in PG.blocked(49, 22))
    except Exception as e:
        chk('寵物行路檢查', False, e)
    d4 = json.load(open(f"{ART}/{pt['dir4']}")); d4d = os.path.dirname(f"{ART}/{pt['dir4']}"); m4 = d4['meta']
    c4 = A(f"{d4d}/{m4['image']}", 'RGBA'); n4 = A(f"{d4d}/{m4['normal']}", 'RGBA'); e4 = A(f"{d4d}/{m4['emissive']}", 'RGBA')
    chk('dir4 atlas 色圖／_n／emissive 同尺寸', c4.shape == n4.shape == e4.shape and [c4.shape[1], c4.shape[0]] == [m4['size']['w'], m4['size']['h']], c4.shape)
    chk('dir4 alpha 只有 0/255、_n alpha＝色圖 alpha、emissive ⊂ alpha', set(np.unique(c4[..., 3]).tolist()) <= {0, 255} and np.array_equal(n4[..., 3], c4[..., 3]) and not np.any((e4[..., 3] > 0) & (c4[..., 3] == 0)))
    want = [f'{d}_{c}_0{i}' for d in ('front', 'back', 'side') for c, n in (('idle', 4), ('walk', 6)) for i in range(1, n + 1)]
    chk('dir4 有 front／back／side × idle 4＋walk 6（30 幀）', sorted(d4['frames']) == sorted(want), len(d4['frames']))
    base = json.load(open(f"{ART}/sprites/tuanrong/motion/atlas_radiant.json")); bf = base['frames']['idle_01']['frame']
    sz = {(f['frame']['w'], f['frame']['h']) for f in d4['frames'].values()}
    chk('dir4 幀尺寸／pivot 同現有 atlas_radiant 一致', sz == {(bf['w'], bf['h'])} and list(m4['pivotPx']) == [base['frames']['idle_01']['pivotPx']['x'], base['frames']['idle_01']['pivotPx']['y']], (sz, m4['pivotPx']))
    gs = []; fl = []
    for fn, f in d4['frames'].items():
        fr = f['frame']; sub = n4[fr['y']:fr['y']+fr['h'], fr['x']:fr['x']+fr['w']]; a = sub[..., 3] > 0; rows = np.where(a.any(1))[0]; q = max(1, len(rows)//4)
        gs.append(sub[rows[:q]][a[rows[:q]], 1].mean() > sub[rows[-q:]][a[rows[-q:]], 1].mean()); fl.append(a.any() and a[-3:].any() if False else a.any())
        v = sub[a][:, :3].astype(float)/255*2 - 1; fl[-1] = fl[-1] and np.abs(np.linalg.norm(v, axis=1) - 1).max() < .03 and sub[a][:, 2].min() >= 128
    chk('dir4 _n：每幀有像素、法線單位長、向外（B≥128）', all(fl), f'{sum(fl)}/{len(fl)}')
    chk('dir4 _n OpenGL 綠＝上（每幀頂部 G＞底部 G）', all(gs), f'{sum(gs)}/{len(gs)}')
    def fr_(nm): f = d4['frames'][nm]['frame']; return c4[f['y']:f['y']+f['h'], f['x']:f['x']+f['w']]
    chk('dir4 back 幀同 front 唔同（新畫）、side＝現有 walk 原樣', not np.array_equal(fr_('back_walk_01'), fr_('front_walk_01')) and np.array_equal(fr_('side_walk_01'), A(f"{ART}/sprites/tuanrong/motion/atlas_radiant.png", 'RGBA')[base['frames']['walk_01']['frame']['y']:][:bf['h'], base['frames']['walk_01']['frame']['x']:][:, :bf['w']]))
    ws = {l['id']: l for l in LJ['lights']}.get('window_side')
    chk('側窗燈 window_side：intensity 0、intensityNight＞0', ws is not None and ws['intensity'] == 0 and ws.get('intensityNight', 0) > 0, ws)
    fl = LJ.get('fill')
    chk('補光 fill：dir 正規化、color、intensity／intensityNight', fl is not None and abs(np.linalg.norm(fl['dir']) - 1) < 1e-3 and HEX.match(fl['color']) and fl['intensity'] >= 0 and fl['intensityNight'] >= 0, fl)
    chk('camera 擺鏡 ±10°（Octopath 式固定 pitch）', CJ['orbitMinDeg'] == -10 and CJ['orbitMaxDeg'] == 10 and CJ['pitchDeg'] == 30, (CJ['orbitMinDeg'], CJ['orbitMaxDeg']))
    # lights
    for l in LJ['lights']:
        ok = all(k in l for k in ('id', 'x', 'y', 'z', 'color', 'radius', 'intensity', 'flicker')) and HEX.match(l['color']) and l['radius'] > 0 and l['intensity'] >= 0 and 0 <= l['flicker'] <= 1
        chk(f"light {l['id']} 欄位／範圍", ok, l)
    s = LJ['sun']; dv = np.array(s['dir'])
    chk('sun dir 正規化、向下', abs(np.linalg.norm(dv)-1) < 1e-3 and dv[1] < 0, s['dir']); chk('sun color／ambient', HEX.match(s['color']) and HEX.match(s['ambient']['color']))
    chk('sun shadowIntensity 0–1', isinstance(s.get('shadowIntensity'), (int, float)) and 0 <= s['shadowIntensity'] <= 1, s.get('shadowIntensity'))
    chk('camera 自動擺鏡／阻尼跟拍（patch2）', 0 < CJ.get('swayAmplitudeDeg', 0) <= CJ['orbitMaxDeg'] and CJ.get('swayHalfPeriodSec', 0) >= 3 and CJ.get('swayEasing') == 'easeInOutSine'
        and 0.5 <= CJ.get('followDamping', 0) <= 8 and len(CJ.get('followWeight', [])) == 2 and all(0 <= w <= 1 for w in CJ['followWeight'])
        and len(CJ.get('followOffset', [])) == 2 and len(CJ.get('followOrigin', [])) == 2, {k: CJ.get(k) for k in ('swayAmplitudeDeg', 'swayHalfPeriodSec', 'followDamping', 'followWeight')})
    chk('camera 欄位', all(k in CJ for k in ('target', 'pitchDeg', 'dist', 'orbitMinDeg', 'orbitMaxDeg')) and 25 <= CJ['pitchDeg'] <= 35 and CJ['orbitMinDeg'] < CJ['orbitMaxDeg'] and CJ['dist'] > 0, CJ)
    big = [x for x in used if os.path.exists(f'{D}/{x}') and os.path.getsize(f'{D}/{x}') >= 20*2**20]
    chk('每個檔 <20MB', not big, big); chk('FORMAT.md 存在', os.path.exists(f'{D}/FORMAT.md'))
    # 法線
    for p in PJ['pets']:
        c = A(f"{ART}/{p['color']}", 'RGBA'); n = A(f"{ART}/{p['normal']}"); f = p['form']
        chk(f'{f} _n 尺寸＝色圖', n.shape == c.shape, (n.shape, c.shape)); chk(f'{f} _n alpha＝色圖 alpha', np.array_equal(n[..., 3], c[..., 3]))
        k = c[..., 3] > 0; v = n[..., :3].astype(float)/255*2-1; L = np.linalg.norm(v, axis=-1)
        chk(f'{f} 法線單位長（±0.03）', np.abs(L[k]-1).max() < .03, np.abs(L[k]-1).max()); chk(f'{f} 法線向外（B≥128）', n[k, 2].min() >= 128, n[k, 2].min())
        aj = json.load(open(f"{ART}/{p['atlasJson']}")); gs = []
        for fn in [x for x in aj['frames'] if x.startswith(('idle_', 'walk_'))]:
            fr = aj['frames'][fn]['frame']; sub = n[fr['y']:fr['y']+fr['h'], fr['x']:fr['x']+fr['w']]; a = sub[..., 3] > 0
            rows = np.where(a.any(1))[0]; q = max(1, len(rows)//4)
            gs.append(sub[rows[:q]][a[rows[:q]], 1].mean() > sub[rows[-q:]][a[rows[-q:]], 1].mean())
        chk(f'{f} OpenGL 綠＝上（idle/walk 每幀頂部 G＞底部 G）', all(gs) and len(gs) >= 10, f'{sum(gs)}/{len(gs)}')
        if p.get('emissive'):
            e = A(f"{ART}/{p['emissive']}", 'RGBA'); chk(f'{f} emissive 同尺寸、⊂ alpha', e.shape == c.shape and not np.any((e[..., 3] > 0) & ~k))
    # 雜檔
    junk = []
    for root, dirs, files in os.walk(D):
        for fn in files:
            rel = os.path.relpath(f'{root}/{fn}', D)
            if rel not in used: junk.append(rel)
        junk += [d for d in dirs if d in ('__pycache__', '_backups')]
    chk('冇雜檔（全部檔案都有被 json 引用）', not junk, junk)
    chk('tools 冇 __pycache__', not os.path.exists(f'{HERE}/__pycache__'))
okn = sum(r['ok'] for r in R)
for r in R:
    if not r['ok']: print('FAIL', r['check'], r['info'])
print(f'{okn}/{len(R)} 通過')
json.dump(dict(passed=okn, total=len(R), results=R), open(f'{D}/validation.json', 'w'), ensure_ascii=False, indent=1)
sys.exit(0 if okn == len(R) else 1)
