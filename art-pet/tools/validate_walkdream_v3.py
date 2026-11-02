#!/usr/bin/env python3
"""第 6 批 validator：6b 散步＋6c 夢遊 V3-A。寫 art/breakthrough/6b/v3/validation.json（同一份 copy 去 6c/v3）。
檢查：原檔（6b@a1a6e9a2、6c@af5b4821）冇郁、V3 尺寸、alpha 規則（sprite 0/255；光／霧／過場可以真 alpha）、json key、夢遊 petGlow＝0、冇 __pycache__／_backups。"""
import os, sys, json, glob, subprocess
import numpy as np
from PIL import Image
ART = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); REPO = os.path.dirname(ART); BT = f'{REPO}/art/breakthrough'
O6B, O6C = f'{BT}/6b/v3', f'{BT}/6c/v3'
LAY = json.load(open(f'{ART}/ui/kit_hd2d_v3/layout_hd2d_v3.json'))['petGlow']
errs, warns, checks = [], [], 0
def ok(c, m):
    global checks; checks += 1
    if not c: errs.append(m)
def A(p): return np.asarray(Image.open(p).convert('RGBA'))[..., 3]
def bin_(p): ok(set(np.unique(A(p))) <= {0, 255}, f'{os.path.relpath(p, BT)} alpha 唔係 0/255')
def sz(p, wh): ok(os.path.exists(p) and Image.open(p).size == tuple(wh), f'{os.path.relpath(p, BT)} size != {wh}')
# 1. 原檔冇郁
for b, c in (('6b', 'a1a6e9a2'), ('6c', 'af5b4821')):
    r = subprocess.run(['git', '-C', REPO, 'diff', '--quiet', c, '--', f'art/breakthrough/{b}', f':!art/breakthrough/{b}/v3'], capture_output=True); ok(r.returncode == 0, f'{b} 原檔同 {c} 唔同')
    ls = subprocess.run(['git', '-C', REPO, 'ls-tree', '-r', '--name-only', c, f'art/breakthrough/{b}'], capture_output=True, text=True).stdout.split()
    ok(len(ls) > 0 and all(os.path.exists(f'{REPO}/{p}') for p in ls), f'{b} 原檔缺失'); ok(not any('/v3/' in p for p in ls), f'{b} v3 唔應該喺 commit')
# 2. 6b
WJ = json.load(open(f'{O6B}/walk6b_v3.json')); J6 = json.load(open(f'{BT}/6b/walk6b.json'))
for k in ('version', 'batch', 'source', 'keys', 'deco', 'decoShared', 'stack', 'pets', 'petGlow'): ok(k in WJ, f'walk6b_v3 缺 {k}')
ok(sorted(WJ['pets']) == sorted(J6['pets']), '6b pets 唔齊'); ok(J6['keys']['6b:walk_bg']['size'] == [100, 120], '6b 原 walk_bg size key 變咗')
for v in ('day', 'dusk', 'night'):
    d = f'{O6B}/walk_bg/{v}'
    for l in ('sky', 'far', 'mid', 'fore'): sz(f'{d}/{l}.png', (100, 120)); sz(f'{d}/x3/{l}@3x.png', (300, 360))
    for l in ('lightmap', 'light_add'): sz(f'{d}/{l}.png', (100, 120))
    for l in ('haze_far', 'mist', 'lightmap', 'light_add', 'bloom', 'emissive', 'vignette'): sz(f'{d}/x3/{l}@3x.png', (300, 360))
    bin_(f'{d}/x3/mid@3x.png'); bin_(f'{d}/mid.png'); bin_(f'{d}/sky.png'); ok(A(f'{d}/x3/sky@3x.png').min() == 255, f'{v} sky 唔係全幅')
    sz(f'{d}/lut.png', (256, 16)); g = json.load(open(f'{d}/grade.json')); x = g.get('v3', {})
    for k in ('stack', 'emitters', 'flares', 'stoneGlow', 'petLight', 'petPop', 'layerSize3x'): ok(k in x, f'{v} grade.v3 缺 {k}')
    ok(x.get('petLight', {}).get('multiplyBy') == 'petGlow', f'{v} petLight multiplyBy'); ok(x.get('layerSize3x') == [300, 360], f'{v} layerSize3x')
    ok(len(x['stoneGlow']['stones']) == len(J6['keys']['6b:walk_bg']['stones']), f'{v} stones')
    if v == 'night': ok(any(e['type'] == 'firefly' for e in x['emitters']), 'night 冇螢火蟲')
    else: ok(not any(e['type'] == 'firefly' for e in x['emitters']), f'{v} 有螢火蟲')
sz(f'{O6B}/walk_bg/stone_glow@3x.png', (120, 60))
for k, dv in WJ['deco'].items():
    p = f"{O6B}/{dv['v3']}"; sz(p, (48, 48)); bin_(p); sz(f"{O6B}/{dv['glow']}", (72, 72))
    a1 = A(f"{BT}/6b/{J6['keys'][k]['1x']}") > 127; ok((A(p)[::3, ::3] > 127).tolist() == a1.tolist(), f'{k} V3 外形同原檔唔同')
ok(len(WJ['deco']) == 8, 'deco != 8'); sz(f'{O6B}/deco/sparkle@3x.png', (144, 24)); sz(f'{O6B}/deco/deco_ao@3x.png', (54, 20))
miss = [p for p, v in WJ['pets'].items() if not v.get('petglow')]
for p in miss: ok('formLightNote' in WJ['pets'][p], f'{p} 冇 petglow ref 又冇 note')
if miss: warns.append(f'6b 呢啲形態冇自身光源（設計如此，只用通用光池）：{miss}')
for p, v in WJ['pets'].items():
    if v.get('petglow'): ok(os.path.exists(f"{ART}/{v['petglow']}"), f'{p} petglow ref 唔存在')
ok(WJ['petGlow']['states'] == LAY['states'], '6b petGlow states != layout')
# 3. 6c
DJ = json.load(open(f'{O6C}/dream6c_v3.json')); J7 = json.load(open(f'{BT}/6c/dream6c.json'))
for k in ('version', 'batch', 'source', 'screen3x', 'grid', 'dreamBg', 'tiles', 'fog', 'transition', 'cards', 'petGlow', 'pets'): ok(k in DJ, f'dream6c_v3 缺 {k}')
ok(DJ['screen3x'] == [J7['screen'][0] * 3, J7['screen'][1] * 3], 'screen3x')
d = f'{O6C}/dream_bg'
for l in ('sky', 'light_add', 'emissive', 'moon', 'clouds', 'mist', 'lightmap', 'bloom', 'vignette', 'dream_bg_v3'): sz(f'{d}/{l}@3x.png', (585, 1266))
sz(f'{d}/dream_bg_v3.png', (195, 422)); bin_(f'{d}/emissive@3x.png'); bin_(f'{d}/moon@3x.png'); ok(A(f'{d}/sky@3x.png').min() == 255, 'dream sky 唔係全幅')
ok(len(DJ['dreamBg']['twinkle']) > 5, 'twinkle 太少')
for th in ('forest', 'lake', 'toy', 'star'):
    p = f'{O6C}/tiles/tile_{th}_v3@3x.png'; sz(p, (672, 168)); bin_(p); sz(f'{O6C}/tiles/tile_{th}_glow@3x.png', (672, 168)); sz(f'{O6C}/tiles/tile_{th}_emissive@3x.png', (672, 168))
    bin_(f'{O6C}/tiles/tile_{th}_emissive@3x.png'); ok((A(p)[::3, ::3] > 127).tolist() == (A(f'{BT}/6c/tiles/tile_{th}.png') > 127).tolist(), f'tile_{th} 外形唔同')
    ok(DJ['tiles'].get(f'6c:tile_{th}_v3', {}).get('accentPx', 0) > 0, f'tile_{th} 冇發光細節')
sz(f'{O6C}/tiles/tile_lake_caustic@3x.png', (672, 672)); sz(f'{O6C}/tiles/tile_reveal_glow@3x.png', (216, 216))
sz(f'{O6C}/tiles/fog_v3@3x.png', (1344, 168)); sz(f'{O6C}/tiles/fog_reveal@3x.png', (1344, 168)); sz(f'{O6C}/tiles/fog_v3.png', (56, 56))
fr = A(f'{O6C}/tiles/fog_reveal@3x.png'); ok(fr[:, -168:].max() < 8, 'fog_reveal 最後幀未清'); ok(A(f'{O6C}/tiles/fog_v3@3x.png')[:, :168].mean() > 150, 'fog 太透')
for i in range(10):
    p = f'{O6C}/transition/transition_in_v3_{i:02d}@3x.png'; sz(p, (585, 1266))
ok(A(f'{O6C}/transition/transition_in_v3_09@3x.png').min() == 255, 'transition 最後幀唔係全覆蓋')
ck = [k for k in J7['keys'] if k.startswith('6c:card_')]; ok(len(ck) == 21, 'cards != 21')
for k in ck:
    v = DJ['cards'].get(k + '_v3'); ok(v is not None, f'{k} 冇 V3')
    if v: p = f"{O6C}/{v['v3']}"; sz(p, (84, 108)); bin_(p); ok(os.path.exists(f"{O6C}/{v['glow']}"), f'{k} glow')
sz(f'{O6C}/cards/card_shine@3x.png', (672, 108))
# 夢遊 petGlow＝0
st = LAY['states']; ok(st.get('dreaming') == 0 and st.get('dreamEnter') == 0, 'layout dreaming/dreamEnter != 0')
ok(DJ['petGlow']['dreaming'] == 0 and DJ['petGlow']['dreamEnter'] == 0, 'dream6c_v3 petGlow != 0')
ok(sorted(DJ['pets']) == sorted(J7['pets']), '6c pets 唔齊'); ok(all(v['petLight'] == 0 and v['glow'] == 'off' for v in DJ['pets'].values()), '夢遊有寵物光')
ok(not any(e.get('type') in ('petLight', 'pet_pool') for e in DJ['dreamBg']['emitters']), 'dream emitters 有寵物光')
# 4. 雜項
for b in (O6B, O6C):
    for r, ds, fs in os.walk(b): ok(not any(x in ('__pycache__', '_backups') for x in ds), f'{r} 有 __pycache__／_backups')
for r, ds, fs in os.walk(f'{ART}/tools'): ok('__pycache__' not in ds, 'tools 有 __pycache__')
res = dict(batch='第 6 批 6b＋6c V3-A', ok=not errs, checks=checks, errors=errs, warnings=warns,
           files=dict(b6=sum(len(f) for _, _, f in os.walk(O6B)), c6=sum(len(f) for _, _, f in os.walk(O6C))))
for b in (O6B, O6C): json.dump(res, open(f'{b}/validation.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1)); sys.exit(1 if errs else 0)
