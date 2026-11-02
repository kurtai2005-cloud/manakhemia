#!/usr/bin/env python3
"""驗證屋仔 V3-A（第 4 批）：尺寸、像素 alpha 0/255、光影層齊、grade v3 欄位、petGlow 瞓覺＝0、冇 _backups/__pycache__。輸出 sprites/series2_house/v3/validation.json"""
import os, sys, json
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ART = os.path.dirname(HERE)
V3 = f'{ART}/sprites/series2_house/v3'; ERR = []; N = dict(png=0, json=0)
def err(m): ERR.append(m)
def im(p):
    N['png'] += 1; return Image.open(p)
def binary(p):
    a = np.asarray(im(p).convert('RGBA'))[..., 3]; u = set(np.unique(a).tolist())
    if not u <= {0, 255}: err(f'alpha 非 0/255: {os.path.relpath(p, ART)}')
def size(p, wh):
    s = im(p).size
    if s != wh: err(f'尺寸 {s}≠{wh}: {os.path.relpath(p, ART)}')
L1, L3, SC3 = (223, 446), (669, 1338), (585, 1266)
HJ = json.load(open(f'{V3}/house_v3.json')); N['json'] += 1
for room, r in HJ['rooms'].items():
    for var in ('day', 'night'):
        d = f'{V3}/rooms/{room}/{var}'
        for k in ('sky', 'far', 'mid', 'fore', 'lightmap', 'light_add', 'emissive', 'emissive_blur'): size(f'{d}/{k}.png', L1) if os.path.exists(f'{d}/{k}.png') else err(f'缺 {room}/{var}/{k}.png')
        if not os.path.exists(f'{d}/lut.png'): err(f'缺 {room}/{var}/lut.png')
        for k in ('sky', 'far', 'mid', 'fore', 'lightmap', 'light_add', 'emissive', 'floor_reflect', 'bloom'):
            p = f'{d}/x3/{k}@3x.png'; size(p, L3) if os.path.exists(p) else err(f'缺 {room}/{var}/x3/{k}@3x.png')
        for p in (f'{d}/x3/vignette@3x.png',): size(p, SC3) if os.path.exists(p) else err(f'缺 {p}')
        g = json.load(open(f'{d}/grade.json')); N['json'] += 1
        for k in ('ambientTint', 'petTint', 'saturation', 'contrast', 'v3'):
            if k not in g: err(f'{room}/{var} grade 缺 {k}')
        v = g.get('v3', {})
        for k in ('windowBeam', 'flares', 'emitters', 'lamps', 'reflection', 'petLight', 'stack'):
            if k not in v: err(f'{room}/{var} grade.v3 缺 {k}')
        pl = v.get('petLight', {})
        if pl.get('multiplyBy') != 'petGlow' or 'houseScale' not in pl or '除左佢訓就會關' not in pl.get('rule', ''): err(f'{room}/{var} petLight 未接 petGlow 規則')
FJ = json.load(open(f'{V3}/furniture_v3.json')); N['json'] += 1
for k, f in FJ['furniture'].items():
    binary(f"{V3}/{f['x3']}")
    if f.get('x3Front'): binary(f"{V3}/{f['x3Front']}")
    if f.get('ao'): a = np.asarray(im(f"{V3}/{f['ao']['png']}").convert('RGBA'))
    for part in ('lift', 'halo', 'pool'):
        if k.startswith('lamp_') and not os.path.exists(f"{V3}/furniture/{k}_{part}@3x.png"): err(f'缺燈 {k}_{part}')
for wi in ('none', 'win_curtain', 'win_star'):
    for part in ('beam', 'patch'):
        p = f'{V3}/light/{wi}_{part}@3x.png'; size(p, L3) if os.path.exists(p) else err(f'缺 {p}')
SJ = json.load(open(f'{V3}/souvenir_v3.json')); N['json'] += 1
for k, s in SJ['souvenirs'].items(): binary(f"{V3}/{s['x3']}")
# petGlow：同 source of truth 一致、瞓覺 0
LJ = json.load(open(f'{ART}/ui/kit_hd2d_v3/layout_hd2d_v3.json'))['petGlow']['states']; pg = HJ['petGlow']['house']
for k in ('sleep', 'sleepClip', 'dreamEnter', 'dreaming'):
    if LJ[k] != 0: err(f'layout petGlow.{k}≠0')
if pg['sleep_bed'] != 0 or pg['sleep_together'] != 0 or pg['awake'] != LJ['awake'] or pg['sleepy'] != LJ['sleepy']: err('house petGlow 映射唔夾 layout')
if '除左佢訓就會關' not in HJ['petGlow']['rule']: err('house_v3.json 缺瞓覺關光規則')
# 雜物
for root, ds, fs in [w for d0 in (V3, HERE) for w in os.walk(d0)]:  # 只查今批輸出（repo 原有 art-pet/_backups 係 tracked，唔關今批）
    for x in ds:
        if x in ('__pycache__', '_backups'): err(f'有 {os.path.relpath(os.path.join(root, x), ART)}')
res = dict(ok=not ERR, errors=ERR, checked=N, rooms=list(HJ['rooms']), furniture=len(FJ['furniture']), souvenirs=len(SJ['souvenirs']))
json.dump(res, open(f'{V3}/validation.json', 'w'), ensure_ascii=False, indent=1)
print('house v3', 'OK' if not ERR else 'FAIL', N, *ERR[:20], sep='\n'); sys.exit(1 if ERR else 0)
