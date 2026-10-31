#!/usr/bin/env python3
"""懸浮互動（Kurt 10-31 批）：喺現有 pet_<form>.png/json 後面「追加」遊美已交付嘅 clip（唔郁現有格）：
sniff（聞）、swat（撥）、cheer_jump（彈）、droop（唔開心）、emo_hungry（肚餓）。
做法同 picked_up_enter：<clip>_noface 身體＋face_anchors 每幀預設五官（kit piece）＋bulb_base。
Usage: bake_extra_clips.py <liveliness_dir> <pet_dir> <form>"""
import json, sys, os
from PIL import Image
src, out, form = sys.argv[1], sys.argv[2], sys.argv[3]
EXTRA = {'sniff': None, 'swat': None, 'cheer_jump': None, 'droop': {'eyes': 'sad'}, 'emo_hungry': {'eyes': 'sad'}}
atlas = json.load(open(os.path.join(src, f'atlas_{form}_live.json')))
img = Image.open(os.path.join(src, f'atlas_{form}_live.png')).convert('RGBA')
anchors = json.load(open(os.path.join(src, 'face_anchors.json')))['anchors'][form]
def piece(name):
    f = atlas['frames'].get(name)
    if not f: return None, None
    r = f['frame']; return img.crop((r['x'], r['y'], r['x'] + r['w'], r['y'] + r['h'])), f['pivotPx']
def eyes(e, g, side):
    for n in (f'eyes_{e}_{g}_{side}', f'eyes_{e}_C_{side}', f'eyes_neutral_{g}_{side}', f'eyes_neutral_C_{side}'):
        p, pv = piece(n)
        if p is not None: return p, pv
    return None, None
pj = json.load(open(os.path.join(out, f'pet_{form}.json')))
S = pj['frameSize']; cols = 8
base = Image.open(os.path.join(out, f'pet_{form}.png')).convert('RGBA')
n0 = sum(len(c['frames']) for c in pj['clips'].values() if not c.get('extra'))
cells = []; new = {}
for name, over in EXTRA.items():
    an = atlas['animations'][name + '_noface']; fr = []
    for i, fname in enumerate(an['frames']):
        body, _ = piece(fname); body = body.copy()
        a = anchors[name][i] if i < len(anchors[name]) else anchors[name][-1]
        face = dict(a.get('face') or {'eyes': 'neutral', 'gaze': 'C', 'mouth': 'neutral'}); face.update(over or {})
        parts = []
        if a.get('faceVisible', True):
            parts += [(eyes(face['eyes'], face.get('gaze', 'C'), 'l'), a['eyeL']), (eyes(face['eyes'], face.get('gaze', 'C'), 'r'), a['eyeR']), (piece('mouth_' + face.get('mouth', 'neutral')), a['mouth'])]
        if 'bulb' in a: parts.append((piece('bulb_base'), a['bulb']))
        for (pc, pv), at in parts:
            if pc is None: continue
            layer = Image.new('RGBA', body.size); layer.paste(pc, (at[0] - pv['x'], at[1] - pv['y'])); body.alpha_composite(layer)
        pv = atlas['frames'][fname]['pivotPx']
        fr.append({'i': n0 + len(cells), 'px': pv['x'], 'py': pv['y']}); cells.append(body)
    new[name] = {'fps': an['fps'], 'loop': an['loop'], 'pivot': 'feet', 'frames': fr, 'extra': True}
total = n0 + len(cells); rows = (total + cols - 1) // cols
im = Image.new('RGBA', (cols * S, rows * S)); im.paste(base.crop((0, 0, base.width, min(base.height, rows * S))), (0, 0))
for k, c in enumerate(cells):
    i = n0 + k; im.paste(c, ((i % cols) * S, (i // cols) * S))
for c in new.values():
    for f in c['frames']: f['x'] = (f['i'] % cols) * S; f['y'] = (f['i'] // cols) * S
pj['clips'] = {k: v for k, v in pj['clips'].items() if not v.get('extra')}; pj['clips'].update(new)
pj['extraSource'] = 'bake_extra_clips.py：sniff／swat／cheer_jump／droop／emo_hungry（遊美 liveliness noface＋kit 五官＋bulb_base）'
im.save(os.path.join(out, f'pet_{form}.png'))
json.dump(pj, open(os.path.join(out, f'pet_{form}.json'), 'w'), ensure_ascii=False, indent=1)
print(form, 'base cells', n0, '+', len(cells), '→', im.size)
