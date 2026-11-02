#!/usr/bin/env python3
"""第 5 批 validator：四季 16 款 V3＋細佬 series2 petglow v3。寫 scenes/hd2d_v3/seasons/validation.json。"""
import os, sys, json, glob
import numpy as np
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SD = f'{ROOT}/scenes/hd2d_v3/seasons'; KD = f'{ROOT}/sprites/series2/petglow_v3'
LAY = json.load(open(f'{ROOT}/ui/kit_hd2d_v3/layout_hd2d_v3.json'))['petGlow']
errs, checks = [], 0
def ok(c, m):
    global checks; checks += 1
    if not c: errs.append(m)
def A(p): return np.asarray(Image.open(p).convert('RGBA'))[..., 3]
L1 = ('sky', 'far', 'mid', 'fore', 'lightmap', 'light_add', 'emissive', 'emissive_blur')
X3 = ('sky', 'far', 'haze_far', 'mid', 'mist', 'fore', 'lightmap', 'light_add', 'bloom', 'emissive')
SJ = json.load(open(f'{SD}/seasons_v3.json'))
ok(sorted(SJ.get('seasons', {})) == ['autumn', 'spring', 'summer', 'winter'], 'seasons_v3.json seasons')
n = 0
for sk in ('spring', 'summer', 'autumn', 'winter'):
    for H in ('H1', 'H2', 'H3', 'H4'):
        d = f'{SD}/{sk}/{H}'; ok(os.path.isdir(d), f'missing {d}')
        if not os.path.isdir(d): continue
        n += 1
        for l in L1: p = f'{d}/{l}.png'; ok(os.path.exists(p) and Image.open(p).size == (223, 446), f'{sk}/{H}/{l} 1x size')
        for l in X3: p = f'{d}/x3/{l}@3x.png'; ok(os.path.exists(p) and Image.open(p).size == (669, 1338), f'{sk}/{H}/x3/{l} size')
        ok(Image.open(f'{d}/x3/vignette@3x.png').size == (585, 1266), f'{sk}/{H} vignette3x size')
        ok(Image.open(f'{d}/vignette.png').size == (195, 422), f'{sk}/{H} vignette 1x（螢幕尺寸）size')
        for p in glob.glob(f'{d}/raw/*.png'):
            if p.endswith('_index.png'): continue
            ok(set(np.unique(A(p))) <= {0, 255}, f'{p} raw alpha not 0/255')
        ok(len(glob.glob(f'{d}/raw/*.png')) > 0, f'{sk}/{H} raw empty')
        g = json.load(open(f'{d}/grade.json')); v = g.get('v3', {})
        for k in ('stack', 'bloom3x', 'emitters', 'seasonParticles', 'petLight', 'seasonLight', 'layerSize3x', 'screenSize3x'): ok(k in v, f'{sk}/{H} grade v3 missing {k}')
        ok(g.get('season') == sk and g.get('variant') == H, f'{sk}/{H} grade season/variant')
        pl = v.get('petLight', {}); ok(pl.get('multiplyBy') == 'petGlow', f'{sk}/{H} petLight multiplyBy')
        ok(os.path.exists(f'{d}/palette.json'), f'{sk}/{H} palette')
        if sk != 'spring': ok(not any(e.get('type') in ('petal', 'pollen') for e in v.get('emitters', [])), f'{sk}/{H} petal/pollen outside spring')
        if sk == 'winter': ok(not any(e.get('type') == 'firefly' for e in v.get('emitters', [])), f'{sk}/{H} firefly in winter')
ok(n == 16, f'variants {n} != 16')
fx = f'{SD}/fx/particles_seasons_v3@3x'
ok(os.path.exists(fx + '.png') and os.path.exists(fx + '.json'), 'season fx sheet')
if os.path.exists(fx + '.png'):
    ok(set(np.unique(A(fx + '.png'))) <= {0, 255}, 'season fx alpha 0/255'); FJ = json.load(open(fx + '.json'))
    W, Hh = Image.open(fx + '.png').size
    for nm, f in FJ['frames'].items(): ok(f['x'] + f['w'] <= W and f['y'] + f['h'] <= Hh, f'fx frame {nm} out of sheet')
# 細佬 petglow
idx = json.load(open(f'{KD}/index.json')); forms = [f['form'] for f in idx['forms']]
ok(len(forms) == 33, f'kid forms {len(forms)} != 33'); ok('S1' not in forms, 'S1 should have no light')
ok(idx['clipGlow']['sleep']['value'] == 0, 'index sleep clipGlow != 0')
ACT = json.load(open(f'{ROOT}/sprites/series2/actions/actions.json'))
NF = dict({c: v['frames'] for c, v in ACT['clips'].items()}, idle=ACT['idleClip']['frames'])
miss = {}
for k in forms:
    J = json.load(open(f'{KD}/{k}.json'))
    cg = J['clipGlow']; ok(cg['sleep']['value'] == 0 and cg['sleep']['fadeOut']['ms'] == LAY['fadeOut']['ms'] and cg['sleep']['fadeIn']['ms'] == LAY['fadeIn']['ms'], f'{k} sleep clipGlow/fade')
    ok(cg['sleep']['fadeIn']['pulse']['scale'] == LAY['fadeIn']['pulse']['scale'], f'{k} pulse')
    for c in ('idle', 'walk', 'cry', 'eat'): ok(cg[c]['value'] == 1.0, f'{k} {c} glow != 1')
    ok(J['petGlow'].get('states', LAY['states']) == LAY['states'] if isinstance(J['petGlow'], dict) else True, f'{k} petGlow states != layout')
    for c, nf in NF.items():
        for i in range(nf):
            fn = f'{c}_{i + 1:02d}'; ok(fn in J['frames'], f'{k} frame {fn} missing')
            if fn in J['frames']:
                fd = J['frames'][fn]
                if 'same' in fd: ok(fd['same'] in J['frames'] and 'same' not in J['frames'][fd['same']], f'{k} {fn} bad same')
                else: ok(len(fd['a']) >= 1 and 0 <= fd['e'] <= 1.5, f'{k} {fn} anchors')
    sj = f"{KD}/{J['sheet']}"; ok(os.path.exists(sj), f'{k} sheet json')
    if os.path.exists(sj):
        S = json.load(open(sj)); ok(os.path.exists(f"{KD}/{S['image']}"), f'{k} sheet png')
    if J.get('trackMiss'): miss[k] = J['trackMiss']
for d in (SD, KD):
    for r, ds, fs in os.walk(d): ok('__pycache__' not in ds and '_backups' not in ds, f'{r} has __pycache__/_backups')
res = dict(ok=not errs, checks=checks, errors=errs, variants=n, kidForms=len(forms), kidTrackMiss=miss)
json.dump(res, open(f'{SD}/validation.json', 'w'), ensure_ascii=False, indent=1)
print('OK' if not errs else 'FAIL', checks, 'checks', len(errs), 'errors'); [print(' -', e) for e in errs[:30]]
sys.exit(0 if not errs else 1)
