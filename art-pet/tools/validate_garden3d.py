#!/usr/bin/env python3
"""validate_garden3d.py — 驗 art-pet/scenes/garden3d/H1（格式見 FORMAT.md）＋ 團絨 _n 法線 atlas。
用法：PYTHONDONTWRITEBYTECODE=1 python3 tools/validate_garden3d.py  → 印結果＋寫 H1/validation.json
"""
import os, sys, json, re
import numpy as np
from PIL import Image
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__)); ART = os.path.abspath(f'{HERE}/..'); D = f'{ART}/scenes/garden3d/H1'
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
    ids = set(); FACES = {'cyl', 'fixed'}; LAYERS = {'near', 'mid', 'far'}
    for o in J['objects']:
        oid = o['id']; chk(f'{oid} id 唯一', oid not in ids); ids.add(oid)
        need = ['id', 'file', 'x', 'z', 'w', 'h', 'pivot', 'face', 'shadow', 'layer']
        chk(f'{oid} 欄位齊', all(k in o for k in need), [k for k in need if k not in o])
        chk(f'{oid} face／layer／shadow 合法', o['face'] in FACES and o['layer'] in LAYERS and isinstance(o['shadow'], bool) and (o['face'] != 'fixed' or 'yawDeg' in o))
        pv = o['pivot']; chk(f'{oid} pivot 0–1', 0 <= pv[0] <= 1 and 0 < pv[1] <= 1, pv)
        p1, p3 = f"{D}/{o['file']}", f"{D}/{o['file3x']}"; used.update([o['file'], o['file3x']])
        a1, a3 = A(p1), A(p3); chk(f'{oid} RGBA', a1.ndim == 3 and a1.shape[2] == 4 and a3.shape[2] == 4)
        chk(f'{oid} @3x＝1x×3 最近鄰', np.array_equal(up3(a1), a3))
        al = set(np.unique(a1[..., 3]).tolist())
        if o['layer'] == 'far':
            chk(f'{oid} 背景板 z 大負數（≤ −300）', o['z'] <= -300, o['z']); chk(f'{oid} alpha 0/255', al <= {0, 255}, al)
            chk(f'{oid} 尺寸＝px×unitsPerPx', abs(o['w'] - a1.shape[1]*o['unitsPerPx']) < 1 and abs(o['h'] - a1.shape[0]*o['unitsPerPx']) < 1)
        else:
            chk(f'{oid} alpha 只有 0/255', al <= {0, 255}, al); chk(f'{oid} w/h＝1x px（1 unit＝1 px）', (o['w'], o['h']) == (a1.shape[1], a1.shape[0]), (o['w'], o['h'], a1.shape[:2]))
            chk(f'{oid} 喺 256 地面內', abs(o['x']) <= 128 and abs(o['z']) <= 128, (o['x'], o['z']))
            bot = a1[-1, :, 3] > 0; chk(f'{oid} 底行有像素（貼地）', bot.any() or o.get('y'), '')
            chk(f'{oid} 透明處 RGB=0（無邊色滲）', not a1[a1[..., 3] == 0, :3].any())
        if o.get('emissive'):
            used.update([o['emissive'], o['emissive3x']]); e1 = A(f"{D}/{o['emissive']}"); e3 = A(f"{D}/{o['emissive3x']}")
            chk(f'{oid} emissive 同尺寸', e1.shape == a1.shape and e3.shape == a3.shape)
            chk(f'{oid} emissive ⊂ 本體 alpha', not np.any((e1[..., 3] > 0) & (a1[..., 3] == 0)))
            chk(f'{oid} emissiveLight 指向 lights', o['emissiveLight'] in {l['id'] for l in LJ['lights']}, o['emissiveLight'])
    # lights
    for l in LJ['lights']:
        ok = all(k in l for k in ('id', 'x', 'y', 'z', 'color', 'radius', 'intensity', 'flicker')) and HEX.match(l['color']) and l['radius'] > 0 and l['intensity'] >= 0 and 0 <= l['flicker'] <= 1
        chk(f"light {l['id']} 欄位／範圍", ok, l)
    s = LJ['sun']; dv = np.array(s['dir'])
    chk('sun dir 正規化、向下', abs(np.linalg.norm(dv)-1) < 1e-3 and dv[1] < 0, s['dir']); chk('sun color／ambient', HEX.match(s['color']) and HEX.match(s['ambient']['color']))
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
