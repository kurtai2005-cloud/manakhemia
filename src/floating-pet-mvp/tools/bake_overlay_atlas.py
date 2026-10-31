#!/usr/bin/env python3
"""Bake overlay atlas for Android floating pet: noface + faceov + bulb_base (soft form).
Usage: bake_overlay_atlas.py <liveliness_dir> <out_dir> [form]"""
import json, sys, os
from PIL import Image
src, out = sys.argv[1], sys.argv[2]
form = sys.argv[3] if len(sys.argv) > 3 else 'soft'
clips_json = json.load(open(os.path.join(src, '..', 'CLIPS.json')))
clipmeta = {c['name']: c for c in clips_json['clips']}
atlas = json.load(open(os.path.join(src, f'atlas_{form}_live.json')))
atlas_img = Image.open(os.path.join(src, f'atlas_{form}_live.png')).convert('RGBA')
def piece(name):
    f = atlas['frames'][name]; r = f['frame']
    return atlas_img.crop((r['x'], r['y'], r['x']+r['w'], r['y']+r['h'])), f['pivotPx']
bulb, bulbpv = piece('bulb_base')
WANT = ['idle', 'walk', 'turn_back', 'picked_up', 'emo_happy', 'sleep_loop', 'fall_asleep', 'wake']
S = atlas['meta']['frameSize']; cols = 8
cells = []; out_clips = {}
for name in WANT:
    nf = atlas['animations'][name + '_noface']
    meta = clipmeta.get(name, {})
    anchors = meta.get('anchors', {}).get(form, [])
    frames = []
    for i, fname in enumerate(nf['frames']):
        idx = i + 1
        body = Image.open(os.path.join(src, 'layers', form, f'{name}_{idx:02d}_noface.png')).convert('RGBA')
        fo = os.path.join(src, 'layers', form, f'{name}_{idx:02d}_faceov.png')
        if os.path.exists(fo):
            body.alpha_composite(Image.open(fo).convert('RGBA'))
        a = anchors[i] if i < len(anchors) else {}
        if 'bulb' in a:
            bx, by = a['bulb'][0] - bulbpv['x'], a['bulb'][1] - bulbpv['y']
            layer = Image.new('RGBA', body.size); layer.paste(bulb, (bx, by)); body.alpha_composite(layer)
        pv = atlas['frames'][fname]['pivotPx']
        frames.append({'i': len(cells), 'px': pv['x'], 'py': pv['y']})
        cells.append(body)
    out_clips[name] = {'fps': nf['fps'], 'loop': nf['loop'], 'pivot': nf.get('pivot', 'feet'), 'frames': frames}
# picked_up 第一個循環：faceOnEnter surprised（gaze D）用 kit 疊落 noface
fe = clipmeta['picked_up'].get('faceOnEnter', {'eyes': 'surprised', 'gaze': 'D', 'mouth': 'surprised'})
nf = atlas['animations']['picked_up_noface']; anchors = clipmeta['picked_up']['anchors'][form]; frames = []
for i, fname in enumerate(nf['frames']):
    body = Image.open(os.path.join(src, 'layers', form, f'picked_up_{i+1:02d}_noface.png')).convert('RGBA')
    a = anchors[i]
    for key, pname in (('eyeL', f"eyes_{fe['eyes']}_{fe['gaze']}_l"), ('eyeR', f"eyes_{fe['eyes']}_{fe['gaze']}_r"), ('mouth', f"mouth_{fe['mouth']}"), ('bulb', 'bulb_base')):
        pc, pv = piece(pname)
        layer = Image.new('RGBA', body.size); layer.paste(pc, (a[key][0] - pv['x'], a[key][1] - pv['y'])); body.alpha_composite(layer)
    pv = atlas['frames'][fname]['pivotPx']
    frames.append({'i': len(cells), 'px': pv['x'], 'py': pv['y']}); cells.append(body)
out_clips['picked_up_enter'] = {'fps': nf['fps'], 'loop': False, 'pivot': 'grab', 'frames': frames}
rows = (len(cells) + cols - 1) // cols
img = Image.new('RGBA', (cols*S, rows*S))
for k, c in enumerate(cells):
    img.paste(c, ((k % cols)*S, (k//cols)*S))
os.makedirs(out, exist_ok=True)
img.save(os.path.join(out, f'pet_{form}.png'))
for c in out_clips.values():
    for f in c['frames']:
        f['x'] = (f['i'] % cols)*S; f['y'] = (f['i']//cols)*S
json.dump({'form': form, 'frameSize': S, 'facing': 'right', 'clips': out_clips,
           'source': 'art-pet liveliness (遊美) noface+faceov+bulb_base'}, open(os.path.join(out, f'pet_{form}.json'), 'w'), ensure_ascii=False, indent=1)
print(len(cells), 'frames', img.size)
