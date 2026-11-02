"""validate_petglow_v3 — 第 3 批：寵物光源 v3＋H2 光池＋H3 天氣 V3。"""
import json, os, sys
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ART = os.path.normpath(os.path.join(HERE, '..'))
PG = f'{ART}/sprites/tuanrong/petglow_v3'; EVO = f'{ART}/sprites/tuanrong/evo6'; SC = f'{ART}/scenes/hd2d_v3'
R = []
def chk(n, ok, info=''): R.append(dict(check=n, ok=bool(ok), info=str(info)[:400])); print(('PASS ' if ok else 'FAIL ') + n + ('' if ok else '  ' + str(info)[:300]))
def binA(a): return set(np.unique(np.asarray(a))) <= {0, 255}
idx = json.load(open(f'{PG}/index.json')); forms = [f['form'] for f in idx['forms']]
# 有 emissiveColors 嘅形態全部要喺度
need = []
for p in sorted(os.listdir(EVO)):
    if p.startswith('atlas_') and p.endswith('.json'):
        m = json.load(open(f'{EVO}/{p}'))['meta']
        A_ = json.load(open(f'{EVO}/{p}')); E = np.asarray(Image.open(f"{EVO}/{m['emissive']}").convert('RGBA'))[..., 3]
        fr0 = [A_['frames'][fn]['frame'] for fn in list(A_['animations'].values())[0]['frames']]
        med = float(np.median([(E[r['y']:r['y'] + r['h'], r['x']:r['x'] + r['w']] > 0).sum() for r in fr0]))
        if m.get('emissiveColors') or med > 4: need.append(m['form'])   # 絨點 1px 眼高光／絨芽 0 唔算
chk('light_forms_cover_emissive_forms', set(need) <= set(forms) and len(forms) == 20, sorted(set(need) - set(forms)))
miss = [f for f in forms if not all(os.path.exists(f'{PG}/{x}') for x in (f'{f}.json', f'{f}_glow@3x.json', f'{f}_glow@3x.png'))]
chk('form_files_exist', not miss, miss)
lay = json.load(open(f'{ART}/ui/kit_hd2d_v3/layout_hd2d_v3.json'))
def find(o):
    if isinstance(o, dict):
        if 'petGlow' in o: return o['petGlow']
        for v in o.values():
            r = find(v)
            if r: return r
pgl = find(lay)['states']
bad_cov, bad_same, bad_rng, bad_e, bad_clip, bad_sheet = [], [], [], [], [], []
for f in forms:
    J = json.load(open(f'{PG}/{f}.json')); A = json.load(open(f'{EVO}/atlas_{f}.json')); fs = A['meta']['frameSize']
    E = np.asarray(Image.open(f"{EVO}/{A['meta']['emissive']}").convert('RGBA'))[..., 3]
    allf = {fn for a in A['animations'].values() for fn in a['frames']}
    if allf - set(J['frames']): bad_cov.append((f, len(allf - set(J['frames']))))
    for fn, v in J['frames'].items():
        if 'same' in v:
            t = J['frames'].get(v['same'])
            if not t or 'same' in t: bad_same.append((f, fn))
            continue
        for dx, dy, r, w in v['a']:
            if abs(dx) > fs * 3 or dy > fs * 3 or dy < -fs * 3 * 1.2 or not (0 < w <= 1) or r <= 0: bad_rng.append((f, fn)); break
        fr = A['frames'][fn]['frame']; n = int((E[fr['y']:fr['y'] + fr['h'], fr['x']:fr['x'] + fr['w']] > 0).sum())
        if (n > 0) != (len(v['a']) > 0): bad_e.append((f, fn, n))
    for c, g in J['clipGlow'].items():
        b = c.replace('_noface', '')
        want = {'sleep_loop': 0.0, 'fall_asleep': 0.0, 'wake': 0.0, 'yawn': pgl['sleepy'], 'emo_sleepy': pgl['sleepy']}.get(b, pgl['awake'])
        if abs(g['value'] - want) > 1e-6: bad_clip.append((f, c))
        if b == 'fall_asleep' and g.get('fadeOut', {}).get('ms') != 600: bad_clip.append((f, c, 'fadeOut'))
        if b == 'wake' and (g.get('fadeIn', {}).get('ms') != 400 or g['fadeIn'].get('pulse', {}).get('scale') != [1, 1.15, 1]): bad_clip.append((f, c, 'fadeIn'))
    if pgl.get('sleep') != 0 or set(J['petGlow']['multiplies']) < {'pool', 'halo', 'particles'}: bad_clip.append((f, 'petGlow'))
    sj = json.load(open(f'{PG}/{J["sheet"]}')); im = Image.open(f'{PG}/{sj["image"]}'); Wd, Hd = im.size; a = np.asarray(im.getchannel('A'))
    for k, r in sj['frames'].items():
        if r['x'] + r['w'] > Wd or r['y'] + r['h'] > Hd: bad_sheet.append((f, k))
        cell = a[r['y']:r['y'] + r['h'], r['x']:r['x'] + r['w']]
        if k.startswith(('halo', 'core')) and binA(cell): bad_sheet.append((f, k, 'halo 應係真 alpha'))
        if not k.startswith(('halo', 'core')) and not binA(cell): bad_sheet.append((f, k, '粒子應 0/255'))
    for k in ['halo_s', 'halo_m', 'halo_l', 'core_12'] + J['emitter']['frames']:
        if k not in sj['frames']: bad_sheet.append((f, k, 'missing'))
chk('every_anim_frame_has_anchor_entry', not bad_cov, bad_cov)
chk('same_refs_resolve', not bad_same, bad_same[:5])
chk('anchor_ranges_ok', not bad_rng, bad_rng[:5])
chk('anchors_match_emissive_mask', not bad_e, bad_e[:5])
chk('clipGlow_sleep_off_rule', not bad_clip, bad_clip[:5])
chk('form_sheets_alpha_and_bounds', not bad_sheet, bad_sheet[:5])
# 花園 petLight
bad = []
for k in ('H1', 'H2', 'H3', 'H4'):
    pl = json.load(open(f'{SC}/{k}/grade.json'))['v3']['petLight']
    if pl.get('multiplyBy') != 'petGlow' or 'formLight' not in pl: bad.append(k)
h2 = json.load(open(f'{SC}/H2/grade.json'))['v3']['petLight']
src = open(f'{HERE}/build_garden_hd2d_v3.py').read()
chk('garden_petLight_formLight_and_H2_boost', not bad and h2['intensity'] >= .8 and h2['size3x'][0] > 240 and 'bounce' in h2 and "'H2': 1.0" in src and h2.get('postLightmap'), (bad, h2.get('intensity')))
# H3 天氣
bad = []
for wx in ('rain', 'overcast', 'fog'):
    d = f'{SC}/H3/{wx}'
    for n in ('sky', 'far', 'mid', 'fore'):
        p = f'{d}/{n}.png'
        if not os.path.exists(p) or Image.open(p).size != (223, 446): bad.append(p)
    if Image.open(f'{d}/lut_{wx}.png').size != (256, 16): bad.append(f'{wx} lut')
    for n in ('sky', 'far', 'mid', 'fore', 'lightmap', 'light_add', 'bloom', 'haze_far', 'mist'):
        p = f'{d}/x3/{n}@3x.png'
        if not os.path.exists(p) or Image.open(p).size != (669, 1338): bad.append(p)
    if Image.open(f'{d}/x3/vignette@3x.png').size != (585, 1266): bad.append(f'{wx} vignette')
chk('weather_files_sizes', not bad, bad[:5])
bad = []
for wx in ('rain', 'overcast', 'fog'):
    g = json.load(open(f'{SC}/H3/grade_{wx}.json')); g2 = json.load(open(f'{ART}/scenes/hd2d/H3/grade_{wx}.json'))
    if [k for k in g2 if k not in g]: bad.append((wx, 'v2 keys'))
    for s in g['v3']['stack']:
        f = s.get('file')
        if not f: continue
        p = f'{ART}/{f.split("#")[0]}' if f.startswith('scenes/') else f'{SC}/H3/{f}'
        if not os.path.exists(p): bad.append((wx, f))
    if g['v3']['petLight'].get('multiplyBy') != 'petGlow': bad.append((wx, 'petLight'))
chk('weather_grade_keys_stack_resolve', not bad, bad[:5])
pv = [f'{PG}/preview/petglow_grid.png', f'{PG}/preview/H2_pool_before_after.png', f'{PG}/preview/H4_evo_still_lumi_awake_vs_sleep.png',
      f'{PG}/preview/H4_evo_still_ember_awake_vs_sleep.png', f'{SC}/preview/H3_weather_v3.png', f'{SC}/preview/H3_weather_compare.png', f'{PG}/PETGLOW_V3.md']
chk('previews_and_docs_exist', all(os.path.exists(p) for p in pv), [p for p in pv if not os.path.exists(p)])
junk = [os.path.join(dp, d) for root in (PG, SC, HERE) for dp, ds, fs in os.walk(root) for d in ds if d in ('_backups', '__pycache__')]
chk('no_backups_pycache', not junk, junk)
ok = all(r['ok'] for r in R)
json.dump(dict(ok=ok, passed=sum(r['ok'] for r in R), total=len(R), checks=R), open(f'{PG}/validation.json', 'w'), ensure_ascii=False, indent=1)
print(f"{sum(r['ok'] for r in R)}/{len(R)}", 'OK' if ok else 'FAIL'); sys.exit(0 if ok else 1)
