#!/usr/bin/env python3
"""validate_m2_actions.py — 驗 M2 動作（12 clip×S/M/L）、3 道具＋腳印、3 訪客招牌、FORMAT／glb。"""
import os, sys, json, re
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

def _g_up(sub):
    a = sub[..., 3] > 0
    if not a.any():
        return False
    rows = np.where(a.any(1))[0]
    q = max(1, len(rows) // 4)
    return sub[rows[:q]][a[rows[:q]], 1].mean() > sub[rows[-q:]][a[rows[-q:]], 1].mean()

def main():
    root = os.path.abspath(os.path.join(HERE, '../..'))
    if '--root' in sys.argv:
        root = os.path.abspath(sys.argv[sys.argv.index('--root') + 1])
    art = f'{root}/art-pet'
    clipd = f'{art}/sprites/tuanrong/motion/m2'
    propd = f'{art}/sprites/props/m2'
    visd = f'{art}/sprites/visitors/m2'
    mesh_root = f'{art}/scenes/m2_props'
    used = set()

    def mark(*ps):
        for p in ps:
            used.add(os.path.abspath(p))

    want_sz = ('S', 'M', 'L')
    want_cl = ('mail_post', 'idle_lively', 'idle_quiet', 'idle_diligent', 'idle_lazy',
               'idle_clingy', 'idle_indep', 'scratch_head', 'stretch', 'look_sky',
               'proud_hips', 'point_frame')
    piv = dict(S=(16, 29), M=(24, 45), L=(32, 61))
    fs_of = dict(S=32, M=48, L=64)

    chk('clips.json 存在', os.path.exists(f'{clipd}/clips.json'))
    CI = json.load(open(f'{clipd}/clips.json')); mark(f'{clipd}/clips.json')
    chk('format m2.petclip/1、有 S/M/L × 12 clip',
        CI.get('format') == 'm2.petclip/1' and all(s in CI['atlases'] for s in want_sz)
        and all(c in CI['atlases']['L'] for c in want_cl), list(CI.get('atlases', {}).get('L', {})))
    chk('寫明 OpenGL Y+ 法線', 'OpenGL' in CI.get('normal', '') and 'Y+' in CI.get('normal', ''))

    for sz in want_sz:
        for cid in want_cl:
            rel = CI['atlases'][sz][cid]
            jp = f'{clipd}/{os.path.basename(rel)}'
            chk(f'{sz} {cid} json 存在', os.path.exists(jp), jp)
            if not os.path.exists(jp):
                continue
            J = json.load(open(jp)); mark(jp)
            cm = CI['clips'][cid]
            fs, pv = fs_of[sz], piv[sz]
            chk(f'{sz} {cid} 幀數／fps／loop／尺寸／pivot',
                J['frameCount'] == cm['frames'] and J['fps'] == cm['fps'] and J['loop'] is cm['loop']
                and J['frameSize'] == fs and tuple(J['pivotPx']) == pv,
                (J.get('frameCount'), J.get('fps'), J.get('loop'), J.get('frameSize'), J.get('pivotPx')))
            img = A(f"{clipd}/{J['meta']['image']}")
            nrm = A(f"{clipd}/{J['meta']['normal']}")
            em = A(f"{clipd}/{J['meta']['emissive']}")
            mark(f"{clipd}/{J['meta']['image']}", f"{clipd}/{J['meta']['normal']}", f"{clipd}/{J['meta']['emissive']}")
            chk(f'{sz} {cid} 色／_n／emissive 同尺寸', img.shape == nrm.shape == em.shape)
            trans = img[..., 3] == 0
            chk(f'{sz} {cid} alpha 0/255、透明 RGB=0、_n alpha＝色、emissive ⊂ alpha',
                set(np.unique(img[..., 3])) <= {0, 255}
                and (not trans.any() or not img[trans, :3].any())
                and np.array_equal(nrm[..., 3], img[..., 3])
                and not np.any((em[..., 3] > 0) & (img[..., 3] == 0)))
            ok_n, ok_g, ok_px = True, True, True
            for fn, frv in J['frames'].items():
                r = frv['frame']
                col = img[r['y']:r['y'] + r['h'], r['x']:r['x'] + r['w']]
                sub = nrm[r['y']:r['y'] + r['h'], r['x']:r['x'] + r['w']]
                if col.shape[:2] != (fs, fs):
                    ok_px = False
                if (col[..., 3] > 0).sum() < 8:
                    ok_px = False
                if not _norm_ok(sub, col):
                    ok_n = False
                if not _g_up(sub):
                    ok_g = False
            chk(f'{sz} {cid} 每幀有像素、尺寸 {fs}', ok_px)
            chk(f'{sz} {cid} _n 單位長／向外', ok_n)
            chk(f'{sz} {cid} _n OpenGL 綠＝上', ok_g)

    # ----- props -----
    chk('props.json 存在', os.path.exists(f'{propd}/props.json'))
    P = json.load(open(f'{propd}/props.json')); mark(f'{propd}/props.json')
    want_props = ('prop_envelope', 'prop_postcard', 'prop_letter')
    ids = [it['id'] for it in P['items']]
    chk('三件道具（信封／明信片／手信）', all(i in ids for i in want_props), ids)
    chk('腳印貼地一併交付', 'decal_footprints' in ids)
    for it in P['items']:
        p = f"{propd}/{it['file']}"; n = f"{propd}/{it['normal']}"
        chk(f"{it['id']} png／_n 存在", os.path.exists(p) and os.path.exists(n), (p, n))
        if not (os.path.exists(p) and os.path.exists(n)):
            continue
        im, nrm = A(p), A(n)
        mark(p, n)
        chk(f"{it['id']} 色／_n 同尺寸、alpha 0/255、透明 RGB=0",
            im.shape == nrm.shape and set(np.unique(im[..., 3])) <= {0, 255}
            and not im[im[..., 3] == 0, :3].any())
        chk(f"{it['id']} _n 單位長／向外／alpha 一致／綠＝上",
            np.array_equal(nrm[..., 3], im[..., 3]) and _norm_ok(nrm, im) and _g_up(nrm))
        if it['id'] in want_props:
            chk(f"{it['id']} 有 glb／mesh", 'glb' in it and 'mesh' in it, it.keys())

    # glb
    for mid in want_props:
        mj = f'{mesh_root}/meshes/{mid}.json'
        gj = f'{mesh_root}/meshes/{mid}.glb'
        chk(f'{mid} mesh json／glb 存在', os.path.exists(mj) and os.path.exists(gj))
        if not os.path.exists(mj):
            continue
        MJ = json.load(open(mj)); mark(mj, gj)
        chk(f'{mid} format garden3d.mesh/2', MJ.get('format') == 'garden3d.mesh/2')
        Pv = np.array(MJ['positions']).reshape(-1, 3)
        N = np.array(MJ['normals']).reshape(-1, 3)
        UV = np.array(MJ['uvs']).reshape(-1, 2)
        I = np.array(MJ['indices']).reshape(-1, 3)
        chk(f'{mid} ≤300 三角、指數一致', len(I) <= 300 and len(I) == MJ['triangleCount'])
        nlen = np.linalg.norm(N, axis=1)
        chk(f'{mid} 法線單位長、uv 0–1', np.abs(nlen - 1).max() < 0.02 and UV.min() >= -0.01 and UV.max() <= 1.01)
        tx = A(f"{mesh_root}/{MJ['texture']}")
        t3 = A(f"{mesh_root}/{MJ['texture3x']}")
        mark(f"{mesh_root}/{MJ['texture']}", f"{mesh_root}/{MJ['texture3x']}")
        chk(f'{mid} 貼圖 2 次方、@3x＝×3、alpha 0/255',
            (tx.shape[0] & (tx.shape[0] - 1)) == 0 and (tx.shape[1] & (tx.shape[1] - 1)) == 0
            and np.array_equal(np.repeat(np.repeat(tx, 3, 0), 3, 1), t3)
            and set(np.unique(tx[..., 3])) <= {0, 255})
        chk(f'{mid} nearest、alphaTest 0.5', MJ.get('alphaTest') == 0.5 and MJ['material'].get('filter') == 'nearest')
        try:
            G = GM.read_glb(gj)
            okg = np.allclose(G['P'], Pv, atol=1e-3) and np.allclose(G['N'], N, atol=1e-4) \
                and np.allclose(G['UV'][:, 0], UV[:, 0], atol=1e-5) and np.allclose(G['UV'][:, 1], 1 - UV[:, 1], atol=1e-5) \
                and np.array_equal(G['I'].reshape(-1, 3), I)
            gl = G['json']; mt = gl['materials'][0]; smp = gl['samplers'][0]
            chk(f'{mid} .glb 幾何／uv V 翻／index', okg)
            chk(f'{mid} .glb MASK＋NEAREST＋glTF 2.0',
                mt.get('alphaMode') == 'MASK' and smp.get('magFilter') == 9728 and smp.get('minFilter') == 9728
                and gl['asset']['version'] == '2.0')
        except Exception as e:
            chk(f'{mid} .glb 讀得', False, str(e))

    # ----- visitors -----
    chk('visitors.json 存在', os.path.exists(f'{visd}/visitors.json'))
    V = json.load(open(f'{visd}/visitors.json')); mark(f'{visd}/visitors.json')
    want_v = ('snail_postman', 'mushroom_granny', 'firefly_vendor')
    vids = [it['id'] for it in V['items']]
    chk('三位訪客各 1 個招牌動作', V.get('count') == 3 and all(i in vids for i in want_v), vids)
    for it in V['items']:
        jp = f"{visd}/{it['atlas']}"
        chk(f"{it['id']} atlas json 存在", os.path.exists(jp))
        if not os.path.exists(jp):
            continue
        J = json.load(open(jp)); mark(jp)
        img = A(f"{visd}/{J['meta']['image']}")
        nrm = A(f"{visd}/{J['meta']['normal']}")
        em = A(f"{visd}/{J['meta']['emissive']}")
        mark(f"{visd}/{J['meta']['image']}", f"{visd}/{J['meta']['normal']}", f"{visd}/{J['meta']['emissive']}")
        chk(f"{it['id']} 6 幀／loop／色 _n emissive 同尺寸",
            J['frameCount'] == 6 and J['loop'] is True and img.shape == nrm.shape == em.shape)
        trans = img[..., 3] == 0
        chk(f"{it['id']} alpha 0/255、透明 RGB=0、_n alpha＝色、emissive ⊂ alpha",
            set(np.unique(img[..., 3])) <= {0, 255}
            and (not trans.any() or not img[trans, :3].any())
            and np.array_equal(nrm[..., 3], img[..., 3])
            and not np.any((em[..., 3] > 0) & (img[..., 3] == 0)))
        ok_n, ok_g, ok_px = True, True, True
        fs = J['frameSize']
        for fn, frv in J['frames'].items():
            r = frv['frame']
            col = img[r['y']:r['y'] + r['h'], r['x']:r['x'] + r['w']]
            sub = nrm[r['y']:r['y'] + r['h'], r['x']:r['x'] + r['w']]
            if col.shape[:2] != (fs, fs) or (col[..., 3] > 0).sum() < 8:
                ok_px = False
            if not _norm_ok(sub, col):
                ok_n = False
            if not _g_up(sub):
                ok_g = False
        chk(f"{it['id']} 每幀有像素、尺寸 {fs}", ok_px)
        chk(f"{it['id']} _n 單位長／向外", ok_n)
        chk(f"{it['id']} _n OpenGL 綠＝上", ok_g)

    # FORMAT
    fmt = f'{art}/m2_actions/FORMAT.md'
    chk('FORMAT.md 存在', os.path.exists(fmt)); mark(fmt) if os.path.exists(fmt) else None
    if os.path.exists(fmt):
        t = open(fmt, encoding='utf-8').read()
        chk('FORMAT 有 Godot 4 匯入注意一節', 'Godot 4' in t and ('Nearest' in t or 'nearest' in t)
            and ('alpha scissor' in t or 'ALPHA_SCISSOR' in t or 'Alpha Scissor' in t))
        chk('FORMAT 寫明 OpenGL（Y+／綠＝上）法線', 'OpenGL' in t and ('Y+' in t or '綠＝上' in t))
        chk('FORMAT 寫明單位／import scale', '1 unit' in t and ('import' in t.lower() or '0.01' in t))
        gi = f'{art}/m2_actions/godot_import.json'
        chk('godot_import.json 存在', os.path.exists(gi))
        if os.path.exists(gi):
            mark(gi)

    outd = f'{art}/m2_actions'
    os.makedirs(outd, exist_ok=True)
    okn = sum(r['ok'] for r in R)
    rec = dict(passed=okn, total=len(R), results=R)
    json.dump(rec, open(f'{outd}/validation.json', 'w'), ensure_ascii=False, indent=1)
    fails = [r for r in R if not r['ok']]
    for r in fails:
        print('FAIL', r['check'], r.get('info'))
    print(f'{okn}/{len(R)} 通過')
    return 0 if okn == len(R) else 1

if __name__ == '__main__':
    sys.exit(main())
