#!/usr/bin/env python3
"""validate_godot_fx1.py — 驗 Godot FX1（LUT、Environment、粒子圖）。
用法：PYTHONDONTWRITEBYTECODE=1 python3 art-pet/tools/validate_godot_fx1.py [--root DIR]
結果寫入 art-pet/fx/validation.json。"""
import os, sys, json, hashlib
import numpy as np
from PIL import Image
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fx1_common as C

R = []
def chk(name, ok, info=None):
    R.append(dict(check=name, ok=bool(ok), info=None if ok else (info if not isinstance(info, (np.ndarray,)) else str(info))))
    return bool(ok)

def A(p, mode=None):
    im = Image.open(p)
    if mode:
        im = im.convert(mode)
    return np.array(im)

def luma_u8(rgb):
    return C.luma(np.asarray(rgb, dtype=np.float64))

def main():
    root = os.path.abspath(os.path.join(HERE, '../..'))
    if '--root' in sys.argv:
        root = os.path.abspath(sys.argv[sys.argv.index('--root') + 1])
    fx = os.path.join(root, 'art-pet', 'fx')
    lutd = os.path.join(fx, 'luts')
    pard = os.path.join(fx, 'particles')

    # files
    need = [
        'FORMAT.md', 'godot_import.json', 'validation.json',
        'environments/environments.json', 'luts/luts.json', 'particles/particles.json',
    ]
    for n in ['identity', 'day', 'dusk', 'night', 'spring', 'summer', 'autumn', 'winter']:
        need.append(f'luts/lut_{n}.png')
    for n in ['fireflies', 'leaves', 'petals', 'rain', 'snow', 'grass_debris']:
        need.append(f'particles/{n}.png')
        need.append(f'particles/{n}.json')
    miss = [n for n in need if n != 'validation.json' and not os.path.isfile(os.path.join(fx, n))]
    chk('必備檔齊', not miss, miss)

    # LUT geometry + identity
    ident = A(os.path.join(lutd, 'lut_identity.png'), 'RGB')
    chk('lut_identity 1089×33', ident.shape[0] == 33 and ident.shape[1] == 1089, ident.shape)
    expect = C.identity_lut()
    chk('lut_identity 係官方佈局中性立方（最大誤差 ≤1）',
        ident.shape == expect.shape and int(np.abs(ident.astype(int) - expect.astype(int)).max()) <= 1,
        int(np.abs(ident.astype(int) - expect.astype(int)).max()) if ident.shape == expect.shape else 'shape')
    # sample corners
    s = 33
    chk('slice0 四角 R／G 軸正確',
        ident[0, 0].tolist() == [0, 0, 0] and ident[0, s-1].tolist() == [255, 0, 0]
        and ident[s-1, 0].tolist() == [0, 255, 0] and ident[s-1, s-1].tolist() == [255, 255, 0],
        dict(tl=ident[0, 0].tolist(), tr=ident[0, s-1].tolist(), bl=ident[s-1, 0].tolist(), br=ident[s-1, s-1].tolist()))
    last = 32 * s
    chk('最後 slice B=255 四角正確',
        ident[0, last].tolist() == [0, 0, 255] and ident[s-1, last+s-1].tolist() == [255, 255, 255],
        ident[0, last].tolist())

    hashes = {}
    for n in ['day', 'dusk', 'night', 'spring', 'summer', 'autumn', 'winter']:
        p = os.path.join(lutd, f'lut_{n}.png')
        arr = A(p, 'RGB')
        ok_sz = arr.shape[0] == 33 and arr.shape[1] == 1089
        chk(f'lut_{n} 1089×33 RGB', ok_sz, arr.shape)
        h = hashlib.sha1(arr.tobytes()).hexdigest()[:12]
        hashes[n] = h
        # not identical to identity
        if ok_sz:
            chk(f'lut_{n} 唔係中性（有調色）', not np.array_equal(arr, expect))
    chk('七套季節／時段 LUT 內容互唔相同', len(set(hashes.values())) == 7, hashes)

    # identity apply
    ramp = np.zeros((8, 256, 3), np.uint8)
    ramp[:] = np.arange(256)[None, :, None]
    ident_lut = ident
    back = C.apply_lut(ramp, ident_lut)
    chk('中性 LUT 套用灰階誤差 ≤2', int(np.abs(back.astype(int) - ramp.astype(int)).max()) <= 2,
        int(np.abs(back.astype(int) - ramp.astype(int)).max()))

    # night targets
    night = A(os.path.join(lutd, 'lut_night.png'), 'RGB')
    # engine-bright ground (chromaticity of GIF ground 19,24,15 lifted to L≈55)
    g0 = np.array([19.0, 24.0, 15.0])
    L0 = C.luma(g0)
    g_eng = g0 * (55.0 / L0)
    sky = np.array([51.0, 51.0, 49.0])
    lamp = np.array([218.0, 203.0, 162.0])
    already = g0.copy()  # already-correct dark ground
    def map_col(c):
        img = np.array([[c]], dtype=np.uint8) if c.dtype == np.uint8 or c.max() > 1.5 else None
        if img is None:
            img = np.array([[np.clip(c, 0, 255)]], dtype=np.uint8)
        o = C.apply_lut(img, night)[0, 0]
        return o, float(C.luma(o.astype(np.float64)))
    ge, Le = map_col(g_eng)
    sk, Ls = map_col(sky)
    lp, Ll = map_col(lamp)
    ad, La = map_col(already)
    chk('夜 LUT：引擎過亮地面（L≈55 暖綠）→ L 18–32', 18 <= Le <= 32, dict(out=ge.tolist(), L=round(Le, 1)))
    chk('夜 LUT：夜空中性（L≈51）保持 45–65', 45 <= Ls <= 65, dict(out=sk.tolist(), L=round(Ls, 1)))
    chk('夜 LUT：燈高光仍然亮（L≥140）', Ll >= 140, dict(out=lp.tolist(), L=round(Ll, 1)))
    chk('夜 LUT：已暗地面（L≈22）唔再大幅壓暗（L 16–30）', 16 <= La <= 30, dict(out=ad.tolist(), L=round(La, 1)))

    # environments
    env = json.load(open(os.path.join(fx, 'environments', 'environments.json')))
    chk('environments format', env.get('format') == 'godot_fx1.environment/1')
    ids = [p['id'] for p in env['presets']]
    chk('7 個 preset：日暮夜春夏秋冬', ids == ['day', 'dusk', 'night', 'spring', 'summer', 'autumn', 'winter'], ids)
    ca = env['camera_attributes']
    chk('CameraAttributesPractical 有 near／far DoF 距離同 amount',
        ca.get('resource') == 'CameraAttributesPractical'
        and ca.get('dof_blur_far_enabled') and ca.get('dof_blur_near_enabled')
        and ca.get('dof_blur_amount', 0) > 0
        and ca.get('dof_blur_far_distance', 0) > ca.get('dof_blur_near_distance', 0),
        {k: ca[k] for k in ca if k.startswith('dof')})
    # dist alignment: far > 580, near < 580
    chk('DoF 對齊 dist 580（near < 580 < far）',
        ca['dof_blur_near_distance'] < 580 < ca['dof_blur_far_distance'],
        (ca['dof_blur_near_distance'], ca['dof_blur_far_distance']))
    for p in env['presets']:
        e = p['environment']
        chk(f"{p['id']} 有 glow／fog depth／tonemap Linear／adjustment＋LUT",
            e.get('glow_enabled') is not None and e.get('fog_mode') == 'depth'
            and e.get('tonemap_mode') == 'Linear' and e.get('adjustment_enabled')
            and e.get('adjustment_color_correction', '').endswith(f"lut_{p['id']}.png")
            and e.get('fog_depth_end', 0) > e.get('fog_depth_begin', 0),
            {k: e.get(k) for k in ('tonemap_mode', 'fog_mode', 'adjustment_color_correction')})
        chk(f"{p['id']} 關 SSR／SSAO／SDFGI（手機）",
            not e.get('ssr_enabled') and not e.get('ssao_enabled') and not e.get('sdfgi_enabled'))

    gi = json.load(open(os.path.join(fx, 'godot_import.json')))
    chk('godot_import LUT slices 33×1 Texture3D',
        gi.get('lut', {}).get('slices_horizontal') == 33 and gi['lut'].get('import_as') == 'Texture3D')

    q = env.get('quality') or {}
    chk('quality.baseline＝low', q.get('baseline') == 'low', q.get('baseline'))
    tiers = q.get('tiers') or {}
    chk('有 low／mid／high 三檔', set(tiers) >= {'low', 'mid', 'high'}, list(tiers))
    low, mid, high = tiers.get('low') or {}, tiers.get('mid') or {}, tiers.get('high') or {}
    def off(d):
        return (d.get('shadow_enabled') is False and d.get('glow_enabled') is False
                and d.get('dof_enabled') is False and d.get('fog_enabled') is False
                and d.get('adjustment_enabled') is True and d.get('lut') is True)
    def on(d):
        return (d.get('shadow_enabled') is True and d.get('glow_enabled') is True
                and d.get('dof_enabled') is True and d.get('fog_enabled') is True
                and d.get('lut') is True)
    chk('low：熄影／glow／DoF／fog，LUT 仍開', off(low), low)
    chk('mid：影／glow／DoF／fog／LUT 開', on(mid), mid)
    chk('high：影／glow／DoF／fog／LUT 開', on(high), high)
    ft = q.get('field_tiers') or {}
    for key in ('glow_enabled', 'fog_enabled', 'dof_blur_near_enabled', 'dof_blur_far_enabled', 'shadow_enabled'):
        v = ft.get(key) or {}
        chk(f'field_tiers.{key} low=false、mid/high=true',
            v.get('low') is False and v.get('mid') is True and v.get('high') is True, v)
    lut_t = ft.get('adjustment_color_correction') or {}
    chk('field_tiers LUT 三檔都開', lut_t.get('low') is True and lut_t.get('mid') is True and lut_t.get('high') is True, lut_t)

    # particles
    pj = json.load(open(os.path.join(pard, 'particles.json')))
    chk('particles 6 款', len(pj.get('items', [])) == 6, len(pj.get('items', [])))
    ids_p = [it['id'] for it in pj['items']]
    chk('粒子 id 齊', ids_p == ['fireflies', 'leaves', 'petals', 'rain', 'snow', 'grass_debris'], ids_p)
    for it in pj['items']:
        sid = it['id']
        spec = json.load(open(os.path.join(pard, f'{sid}.json')))
        png = os.path.join(pard, os.path.basename(spec['image']))
        im = A(png, 'RGBA')
        h, w = im.shape[:2]
        chk(f'{sid} 圖存在、寬高 2 次方', C.pot(w) and C.pot(h), (w, h))
        uniq = set(np.unique(im[..., 3]).tolist())
        chk(f'{sid} alpha 只有 0/255', uniq <= {0, 255}, uniq)
        if (im[..., 3] == 0).any():
            chk(f'{sid} 透明 RGB=0', not im[im[..., 3] == 0, :3].any())
        chk(f'{sid} 有足夠不透明像素', int((im[..., 3] > 0).sum()) >= 8, int((im[..., 3] > 0).sum()))
        cell = spec['cell']
        chk(f'{sid} 格尺寸整除（至少一格）', w >= cell and h >= cell and w % cell == 0, (w, h, cell))
        chk(f'{sid} 有 GPUParticles／ProcessMaterial 參數',
            'gpu_particles' in spec and 'process_material' in spec and 'material' in spec)
        # Nearest material
        chk(f'{sid} material Filter Nearest', spec['material'].get('texture_filter') == 'Nearest')
        if sid == 'fireflies':
            chk('螢火蟲 blend add + emissive', spec['material'].get('blend_mode') == 'add' and spec['material'].get('emissive') is True)
            chk('螢火蟲 amount 配合 H1（16–40）', 16 <= spec['gpu_particles']['amount'] <= 40, spec['gpu_particles']['amount'])
        if sid == 'leaves':
            chk('落葉有四季 groups', all(k in spec.get('season_rows', {}) or any(g.startswith(k) for g in spec.get('groups', {})) for k in ('spring', 'summer', 'autumn', 'winter')))
        if sid == 'grass_debris':
            chk('撥草碎屑 one_shot＋explosiveness 1',
                spec['gpu_particles'].get('one_shot') is True and spec['gpu_particles'].get('explosiveness') == 1.0)
        gp = spec['gpu_particles']
        al, am, ah = gp.get('amount_low'), gp.get('amount_mid'), gp.get('amount_high', gp.get('amount'))
        chk(f'{sid} 有 amount_low／mid／high，且 low≤mid≤high、low≥1',
            isinstance(al, int) and isinstance(am, int) and isinstance(ah, int)
            and 1 <= al <= am <= ah, dict(low=al, mid=am, high=ah))

    # tools exist
    for t in ('fx1_common.py', 'build_godot_fx1.py', 'validate_godot_fx1.py', 'preview_godot_fx1.py'):
        chk(f'工具 {t}', os.path.isfile(os.path.join(root, 'art-pet', 'tools', t)))

    outp = os.path.join(fx, 'validation.json')
    summary = dict(total=len(R), passed=sum(1 for x in R if x['ok']), failed=sum(1 for x in R if not x['ok']), checks=R)
    dump_ok = True
    with open(outp, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
        f.write('\n')
    failed = [x for x in R if not x['ok']]
    print('validation', summary['passed'], '/', summary['total'], 'failed', len(failed))
    for x in failed:
        print(' FAIL', x['check'], x['info'])
    return 0 if not failed else 1

if __name__ == '__main__':
    sys.exit(main())
