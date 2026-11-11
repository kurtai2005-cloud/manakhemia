#!/usr/bin/env python3
"""validate_m1_icons_hunt.py — 驗 M1 icon（34＋泡泡＋銅證）同狩獵 lite（草原 mesh／glb、小怪、果、寵物 clip）。
用法：PYTHONDONTWRITEBYTECODE=1 python3 tools/validate_m1_icons_hunt.py [--root DIR]
預設 root＝art-pet 上一層（repo 根）。結果寫入 art-pet/m1_icons_hunt/validation.json。"""
import os, sys, json, math, re
import numpy as np
from PIL import Image
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import garden3d_mesh as GM

R = []
def chk(name, ok, info=None):
    R.append(dict(check=name, ok=bool(ok), info=None if ok else (info if not isinstance(info, (np.ndarray,)) else str(info))))
    return bool(ok)

def A(p, mode='RGBA'):
    return np.array(Image.open(p).convert(mode))


def _norm_ok(n, c):
    k = c[..., 3] > 0
    if not k.any():
        return False
    v = n[..., :3].astype(float) / 255 * 2 - 1
    L = np.linalg.norm(v, axis=-1)
    return np.abs(L[k] - 1).max() < 0.03 and n[k, 2].min() >= 128

def main():
    root = os.path.abspath(os.path.join(HERE, '../..'))
    if '--root' in sys.argv:
        root = os.path.abspath(sys.argv[sys.argv.index('--root') + 1])
    art = f'{root}/art-pet'
    icond = f'{art}/ui/m1_icons'
    prairie = f'{art}/scenes/hunt3d/prairie'
    fruitsd = f'{art}/sprites/hunt/fruits'
    critd = f'{art}/sprites/hunt/critters'
    clipd = f'{art}/sprites/tuanrong/motion/hunt'
    badged = f'{art}/ui/m1_icons/badges'
    used = set()

    def mark(*ps):
        for p in ps:
            used.add(os.path.relpath(p, art) if p.startswith(art) else p)

    # ----- icons -----
    spec = json.load(open(f'{icond}/icons.json'))
    items = spec['items']
    chk('icon 數量 34', len(items) == 34, len(items))
    groups = {}
    for it in items:
        groups.setdefault(it['group'], 0); groups[it['group']] += 1
    chk('需要 4＋表情 6＋心情 4＋事件 20', groups.get('need') == 4 and groups.get('expr') == 6 and groups.get('mood') == 4 and groups.get('event') == 20, groups)
    ids = [it['id'] for it in items]
    chk('icon id 無重複', len(ids) == len(set(ids)))
    alphas_ok, sizes_ok, exist = True, True, True
    colors_min = True
    for it in items:
        p = f"{icond}/{it['file']}"
        if not os.path.exists(p):
            exist = False; continue
        im = A(p)
        if im.shape[0] != 32 or im.shape[1] != 32: sizes_ok = False
        if set(np.unique(im[..., 3]).tolist()) - {0, 255}: alphas_ok = False
        if (im[..., 3] == 0).any() and im[im[..., 3] == 0, :3].any(): alphas_ok = False
        if (im[..., 3] > 0).sum() < 40: colors_min = False
        mark(p)
    chk('每個 icon 檔存在 @3x 32×32', exist and sizes_ok)
    chk('icon sprite alpha 只有 0/255，透明 RGB=0', alphas_ok)
    chk('每個 icon 有足夠不透明像素（可讀）', colors_min)
    atl = A(f"{icond}/{spec['atlas']['image']}")
    mark(f"{icond}/{spec['atlas']['image']}")
    chk('icons atlas 存在、2 次方寬高', atl is not None and (atl.shape[1] & (atl.shape[1] - 1)) == 0 and (atl.shape[0] & (atl.shape[0] - 1)) == 0, atl.shape)
    # atlas 幀
    af_ok = True
    for it in items:
        fr = spec['atlas']['frames'][it['id']]['frame']
        sub = atl[fr['y']:fr['y'] + fr['h'], fr['x']:fr['x'] + fr['w']]
        one = A(f"{icond}/{it['file']}")
        if not np.array_equal(sub, one):
            af_ok = False
    chk('atlas 幀同散檔一致', af_ok)
    bub_p = f"{icond}/{spec['bubble']['file']}"
    bub = A(bub_p); mark(bub_p)
    chk('夢泡泡框 96×72、有真 alpha、有不透明像素', bub.shape[1] == 96 and bub.shape[0] == 72 and bub[..., 3].min() < 255 and (bub[..., 3] > 200).any(), bub.shape)
    slots = spec['bubble']['slots']
    chk('泡泡兩格 32×32 并且重叠或相接（撞埋）', len(slots) == 2 and slots[0]['w'] == 32 and
        slots[1]['x'] < slots[0]['x'] + slots[0]['w'] + 1, slots)

    # badges
    B = json.load(open(f'{badged}/badges.json')); mark(f'{badged}/badges.json')
    chk('銅證 4 張', B['count'] == 4 and len(B['items']) == 4)
    for it in B['items']:
        p = f"{badged}/{it['file']}"
        im = A(p); mark(p)
        chk(f"{it['id']} 32×32 alpha 0/255", im.shape[:2] == (32, 32) and set(np.unique(im[..., 3])) <= {0, 255})

    # ----- fruits -----
    F = json.load(open(f'{fruitsd}/fruits.json')); mark(f'{fruitsd}/fruits.json')
    chk('果 6 種', F['count'] == 6 and len(F['items']) == 6)
    fatl = A(f"{fruitsd}/{F['atlas']['image']}"); fn = A(f"{fruitsd}/{F['atlas']['normal']}")
    mark(f"{fruitsd}/{F['atlas']['image']}", f"{fruitsd}/{F['atlas']['normal']}")
    chk('果 atlas／_n 同尺寸', fatl.shape == fn.shape)
    for it in F['items']:
        p = f"{fruitsd}/{it['file']}"; n = A(f"{fruitsd}/{it['normal']}")
        im = A(p); mark(p, f"{fruitsd}/{it['normal']}")
        chk(f"果 {it['id']} 32×32 alpha 0/255", im.shape[:2] == (32, 32) and set(np.unique(im[..., 3])) <= {0, 255})
        chk(f"果 {it['id']} _n alpha＝色圖、單位長、向外 B≥128",
            np.array_equal(n[..., 3], im[..., 3]) and _norm_ok(n, im))

    # ----- critters -----
    C = json.load(open(f'{critd}/critters.json')); mark(f'{critd}/critters.json')
    chk('小怪 4 種（1 隻大）', C['count'] == 4 and sum(1 for i in C['items'] if i.get('big')) == 1, C)
    for it in C['items']:
        J = json.load(open(f"{critd}/{it['id']}.json")); mark(f"{critd}/{it['id']}.json")
        atl = A(f"{critd}/{J['atlas']['image']}"); nrm = A(f"{critd}/{J['atlas']['normal']}")
        mark(f"{critd}/{J['atlas']['image']}", f"{critd}/{J['atlas']['normal']}")
        chk(f"{it['id']} atlas／_n 同尺寸、alpha 0/255", atl.shape == nrm.shape and set(np.unique(atl[..., 3])) <= {0, 255})
        for ani, need in (('idle', 4), ('scared', 4), ('tofruit', 6)):
            frs = J['animations'][ani]['frames']
            chk(f"{it['id']} {ani} {need} 幀", len(frs) == need, len(frs))
        ok_n, ok_g = True, True
        for fn, fr in J['atlas']['frames'].items():
            r = fr['frame']
            sub = nrm[r['y']:r['y'] + r['h'], r['x']:r['x'] + r['w']]
            col = atl[r['y']:r['y'] + r['h'], r['x']:r['x'] + r['w']]
            if not np.array_equal(sub[..., 3], col[..., 3]): ok_n = False
            if not _norm_ok(sub, col): ok_n = False
            a = sub[..., 3] > 0
            if a.any():
                rows = np.where(a.any(1))[0]
                q = max(1, len(rows) // 4)
                if not (sub[rows[:q]][a[rows[:q]], 1].mean() > sub[rows[-q:]][a[rows[-q:]], 1].mean()):
                    ok_g = False
        chk(f"{it['id']} _n 單位長／向外／alpha 一致", ok_n)
        chk(f"{it['id']} _n OpenGL 綠＝上（頂 G＞底 G）", ok_g)
        chk(f"{it['id']} size／pivot", J['size'] == it['size'] and J['pivotPx'][0] == J['size'] // 2)

    # ----- pet clips -----
    CI = json.load(open(f'{clipd}/clips.json')); mark(f'{clipd}/clips.json')
    want_sz = {'S': (32, (16, 29)), 'M': (48, (24, 45)), 'L': (64, (32, 61))}
    want_cl = {'part_grass': (6, 8, False), 'pounce': (6, 8, False), 'carry_fruit': (6, 10, True), 'cheer': (6, 10, False)}
    chk('clip 指數有 S/M/L × 4', all(s in CI['atlases'] for s in want_sz) and all(c in CI['atlases']['L'] for c in want_cl))
    for sz, (fs, pv) in want_sz.items():
        for cid, (nf, fps, loop) in want_cl.items():
            rel = CI['atlases'][sz][cid]
            J = json.load(open(f'{clipd}/{os.path.basename(rel) if not rel.startswith("atlas") else rel}'))
            # path may be just filename
            jp = f'{clipd}/{os.path.basename(rel)}'
            J = json.load(open(jp)); mark(jp)
            chk(f'{sz} {cid} 幀數／fps／loop／尺寸／pivot',
                J['frameCount'] == nf and J['fps'] == fps and J['loop'] is loop and J['frameSize'] == fs and tuple(J['pivotPx']) == pv,
                (J['frameCount'], J['fps'], J['loop'], J['frameSize'], J['pivotPx']))
            img = A(f"{clipd}/{J['meta']['image']}")
            nrm = A(f"{clipd}/{J['meta']['normal']}")
            em = A(f"{clipd}/{J['meta']['emissive']}")
            mark(f"{clipd}/{J['meta']['image']}", f"{clipd}/{J['meta']['normal']}", f"{clipd}/{J['meta']['emissive']}")
            chk(f'{sz} {cid} 色／_n／emissive 同尺寸', img.shape == nrm.shape == em.shape)
            chk(f'{sz} {cid} alpha 0/255、_n alpha＝色、emissive ⊂ alpha',
                set(np.unique(img[..., 3])) <= {0, 255} and np.array_equal(nrm[..., 3], img[..., 3]) and not np.any((em[..., 3] > 0) & (img[..., 3] == 0)))
            ok_n, ok_g, ok_px = True, True, True
            for fn, frv in J['frames'].items():
                r = frv['frame']
                col = img[r['y']:r['y'] + r['h'], r['x']:r['x'] + r['w']]
                sub = nrm[r['y']:r['y'] + r['h'], r['x']:r['x'] + r['w']]
                if col.shape[:2] != (fs, fs): ok_px = False
                if (col[..., 3] > 0).sum() < 8: ok_px = False
                if not _norm_ok(sub, col): ok_n = False
                a = sub[..., 3] > 0
                if a.any():
                    rows = np.where(a.any(1))[0]
                    q = max(1, len(rows) // 4)
                    if not (sub[rows[:q]][a[rows[:q]], 1].mean() > sub[rows[-q:]][a[rows[-q:]], 1].mean()):
                        ok_g = False
            chk(f'{sz} {cid} 每幀有像素、尺寸 {fs}', ok_px)
            chk(f'{sz} {cid} _n 單位長／向外', ok_n)
            chk(f'{sz} {cid} _n OpenGL 綠＝上', ok_g)

    # ----- prairie mesh -----
    OBJ = json.load(open(f'{prairie}/objects.json'))
    LJ = json.load(open(f'{prairie}/lights.json'))
    CJ = json.load(open(f'{prairie}/camera.json'))
    mark(f'{prairie}/objects.json', f'{prairie}/lights.json', f'{prairie}/camera.json')
    chk('場景 format hunt3d.scene/1、有 objects／pet／critters／ground',
        OBJ.get('format') == 'hunt3d.scene/1' and OBJ.get('objects') and OBJ.get('pet', {}).get('billboard') and OBJ.get('ground'))
    HEX = re.compile(r'^#[0-9a-fA-F]{6}$')
    g = OBJ['ground']
    for k in ('image', 'image3x', 'ao', 'ao3x', 'tile', 'tile3x'):
        p = f"{prairie}/{g[k]}"
        chk(f'地面 {k} 存在', os.path.exists(p), p); mark(p)
    gi, g3 = A(f"{prairie}/{g['image']}"), A(f"{prairie}/{g['image3x']}")
    chk('地面 256、@3x＝nearest×3、alpha 0/255', gi.shape[:2] == (256, 256) and np.array_equal(np.repeat(np.repeat(gi, 3, 0), 3, 1), g3) and set(np.unique(gi[..., 3])) <= {0, 255})
    tile = A(f"{prairie}/{g['tile']}")
    chk('tile 64×64', tile.shape[:2] == (64, 64))
    for bd in OBJ['backdrops']:
        for k in ('file', 'file3x'):
            p = f"{prairie}/{bd[k]}"; chk(f"backdrop {bd['id']} {k}", os.path.exists(p)); mark(p)
        chk(f"backdrop {bd['id']} unlit／far", bd.get('unlit') is True and bd.get('layer') == 'far')

    sun = LJ['sun']; dv = np.array(sun['dir'])
    chk('sun dir 正規化、向下', abs(np.linalg.norm(dv) - 1) < 1e-3 and dv[1] < 0, sun['dir'])
    chk('sun color／ambient／shadowIntensity', HEX.match(sun['color']) and HEX.match(sun['ambient']['color']) and 0 <= sun['shadowIntensity'] <= 1)
    fl = LJ['fill']; fd = np.array(fl['dir'])
    chk('fill 正規化、唔投影注記', abs(np.linalg.norm(fd) - 1) < 1e-3 and fl['intensity'] >= 0)
    chk('camera pitch 約 30、orbit ±10、穩陣擺鏡', CJ['pitchDeg'] == 30 and CJ['orbitMinDeg'] == -10 and CJ['orbitMaxDeg'] == 10
        and 0 < CJ.get('swayAmplitudeDeg', 0) <= 10 and CJ.get('swayEasing') == 'easeInOutSine' and CJ.get('followDamping', 0) >= 0.5, CJ)

    ids = [o['id'] for o in OBJ['objects']]
    chk('物件 id 無重複', len(ids) == len(set(ids)))
    chk('最少 8 件場景 mesh 實例（草原唔可以太空）', len(OBJ['objects']) >= 8, len(OBJ['objects']))
    for o in OBJ['objects']:
        chk(f"{o['id']} type=mesh、有 json／glb", o['type'] == 'mesh' and os.path.exists(f"{prairie}/{o['mesh']}") and os.path.exists(f"{prairie}/{o['glb']}"))
        mark(f"{prairie}/{o['mesh']}", f"{prairie}/{o['glb']}")
        MJ = json.load(open(f"{prairie}/{o['mesh']}"))
        chk(f"{o['id']} format garden3d.mesh/2", MJ.get('format') == 'garden3d.mesh/2')
        P = np.array(MJ['positions']).reshape(-1, 3)
        N = np.array(MJ['normals']).reshape(-1, 3)
        UV = np.array(MJ['uvs']).reshape(-1, 2)
        I = np.array(MJ['indices']).reshape(-1, 3)
        ntri = len(I)
        chk(f"{o['id']} ≤300 三角、指數一致", ntri <= 300 and ntri == MJ['triangleCount'] == o['triangles'], ntri)
        # 逆時針／法線
        ok_w = True
        for t in I:
            v = P[t]; n = np.cross(v[1] - v[0], v[2] - v[0]); ln = np.linalg.norm(n)
            if ln < 1e-8: continue
            n = n / ln
            if np.dot(n, N[t[0]]) < -0.1: ok_w = False
        chk(f"{o['id']} 逆時針正面（幾何法線同頂點 normal 同向）", ok_w)
        nlen = np.linalg.norm(N, axis=1)
        chk(f"{o['id']} 法線單位長", np.abs(nlen - 1).max() < 0.02, float(np.abs(nlen - 1).max()))
        chk(f"{o['id']} uv 0–1", UV.min() >= -0.01 and UV.max() <= 1.01, (float(UV.min()), float(UV.max())))
        tx = A(f"{prairie}/{MJ['texture']}"); t3 = A(f"{prairie}/{MJ['texture3x']}")
        mark(f"{prairie}/{MJ['texture']}", f"{prairie}/{MJ['texture3x']}")
        chk(f"{o['id']} 貼圖 2 次方、@3x＝×3、alpha 0/255",
            (tx.shape[0] & (tx.shape[0] - 1)) == 0 and (tx.shape[1] & (tx.shape[1] - 1)) == 0
            and tx.shape[:2] == tuple(MJ['textureSize'][::-1])  # size is [w,h]
            and np.array_equal(np.repeat(np.repeat(tx, 3, 0), 3, 1), t3)
            and set(np.unique(tx[..., 3])) <= {0, 255})
        # actually textureSize is [w,h] and tx.shape is (h,w)
        chk(f"{o['id']} textureSize 對得準", list(MJ['textureSize']) == [int(tx.shape[1]), int(tx.shape[0])])
        chk(f"{o['id']} material nearest、alphaTest 0.5、doubleSided false",
            MJ.get('alphaTest') == 0.5 and MJ.get('doubleSided') is False and MJ['material'].get('filter') == 'nearest')
        # glb
        try:
            G = GM.read_glb(f"{prairie}/{o['glb']}")
            okg = np.allclose(G['P'], P, atol=1e-3) and np.allclose(G['N'], N, atol=1e-4) \
                and np.allclose(G['UV'][:, 0], UV[:, 0], atol=1e-5) and np.allclose(G['UV'][:, 1], 1 - UV[:, 1], atol=1e-5) \
                and np.array_equal(G['I'].reshape(-1, 3), I)
            gl = G['json']; mt = gl['materials'][0]; smp = gl['samplers'][0]
            okm = mt.get('alphaMode') == 'MASK' and smp.get('magFilter') == 9728 and smp.get('minFilter') == 9728
            chk(f"{o['id']} .glb 幾何／uv（V 翻）／index 同 json", okg)
            chk(f"{o['id']} .glb MASK＋NEAREST＋glTF 2.0", okm and gl['asset']['version'] == '2.0', (mt.get('alphaMode'), smp))
        except Exception as e:
            chk(f"{o['id']} .glb 讀得", False, str(e))
        if o.get('footprint'):
            fp = o['footprint']
            chk(f"{o['id']} footprint 世界座標合法", fp['type'] == 'rect' and fp['x'][0] < fp['x'][1] and fp['z'][0] < fp['z'][1])

    chk('寵物 billboard＋dir4 路徑欄位、huntClips', OBJ['pet'].get('billboard') is True and OBJ['pet'].get('radius', 0) > 0 and 'huntClips' in OBJ['pet'])
    chk('4 隻小怪 spawn（1 大）', len(OBJ['critters']['spawn']) == 4 and sum(1 for s in OBJ['critters']['spawn'] if s.get('big')) == 1)

    # FORMAT
    fmt = f'{art}/m1_icons_hunt/FORMAT.md'
    chk('FORMAT.md 存在', os.path.exists(fmt)); mark(fmt) if os.path.exists(fmt) else None
    if os.path.exists(fmt):
        t = open(fmt, encoding='utf-8').read()
        chk('FORMAT 有 Godot 4 匯入注意一節', 'Godot 4' in t and ('Nearest' in t or 'nearest' in t) and ('alpha scissor' in t or 'ALPHA_SCISSOR' in t or 'Alpha Scissor' in t))
        chk('FORMAT 寫明 OpenGL（Y+／綠＝上）法線', 'OpenGL' in t and ('Y+' in t or '綠＝上' in t))
        chk('FORMAT 寫明單位／import scale', '1 unit' in t and ('import' in t.lower() or '0.01' in t))

    # 雜檔：只檢查我哋目錄內未被引用？太嚴可能誤傷 FORMAT／tools。只警告 meshes 目錄。
    junk = []
    for folder in (f'{prairie}/meshes', f'{prairie}/ground', f'{prairie}/backdrop'):
        for fn in os.listdir(folder):
            rel = os.path.relpath(f'{folder}/{fn}', art)
            # used 存咗絕對或相對
            ok = False
            for u in used:
                if u.endswith(fn) or u.endswith(rel) or rel.endswith(u):
                    ok = True
            # @3x / json / glb / png should be referenced
            if not ok and not fn.startswith('.'):
                # allow meshes_index later
                junk.append(rel)
    # meshes_index 同 FORMAT 在 prairie 根
    for fn in os.listdir(prairie):
        if fn in ('meshes', 'ground', 'backdrop', 'objects.json', 'lights.json', 'camera.json', 'meshes_index.json', 'FORMAT.md', 'validation.json'):
            continue
        junk.append(fn)
    chk('草原目錄冇明顯雜檔（__pycache__／_backups）', not os.path.exists(f'{prairie}/__pycache__') and not os.path.exists(f'{prairie}/_backups') and '__pycache__' not in junk and '_backups' not in junk, junk)

    outd = f'{art}/m1_icons_hunt'
    os.makedirs(outd, exist_ok=True)
    okn = sum(r['ok'] for r in R)
    rec = dict(passed=okn, total=len(R), results=R)
    json.dump(rec, open(f'{outd}/validation.json', 'w'), ensure_ascii=False, indent=1)
    # 失敗列表
    fails = [r for r in R if not r['ok']]
    for r in fails:
        print('FAIL', r['check'], r.get('info'))
    print(f'{okn}/{len(R)} 通過')
    return 0 if okn == len(R) else 1

if __name__ == '__main__':
    # 先定義 _norm_ok 喺 module 層，避免 main 入面順序問題
    sys.exit(main())
