#!/usr/bin/env python3
"""4a：由遊美 series2 細佬 idle 幀 0 計 rig 錨點 → art/series2/kid_anchors.json（引擎播教錯課照抄 clip／fx 用）。
   用法：cd src/glimmer-a && python3 tools/series2-anchors.py   原創代碼；只讀美術，唔改圖。"""
import json, os
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); B = os.path.join(ROOT, 'art', 'series2')
acts = json.load(open(os.path.join(B, 'actions', 'actions.json'))); tuned = json.load(open(os.path.join(B, 'forms', 'tuned.json')))['creatures']
def box(png, fw=48):
    im = Image.open(os.path.join(B, png)).convert('RGBA').crop((0, 0, fw, 48)); a = im.split()[3].load()
    pts = [(x, y) for y in range(48) for x in range(fw) if a[x, y] > 0]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; t = min(ys)
    top = [x for x, y in pts if y == t]
    return min(xs), t, max(xs), max(ys), sum(top) / len(top)
out = {'_note': 'tools/series2-anchors.py 由 idle 幀 0 計（pivot (24,45)）；eyeL/R 有 tuned.json 眼位就用', 'pivot': [24, 45], 'forms': {}}
def entry(png, k):
    l, t, r, b, tx = box(png); mid = round((t + b) / 2, 1); cx = round((l + r + 1) / 2, 1)
    ey = t + 0.55 * (b - t); eL, eR = [cx - 4, ey], [cx + 4, ey]
    c = tuned.get(k)
    if c and len(c.get('eyes', [])) >= 2:
        es = sorted(c['eyes'], key=lambda e: e['x']); eL, eR = [es[0]['x'] + 0.5, es[0]['y']], [es[1]['x'] + 0.5, es[1]['y']]
    my = round(max(eL[1], eR[1]) + 4, 1)
    return {'headTop': [round(tx, 1), t], 'side_l': [l, mid], 'side_r': [r + 1, mid], 'center': [cx, mid], 'chest': [cx, b - 4], 'face': [cx, round(eL[1], 1)],
            'eyeL': [round(eL[0], 1), round(eL[1], 1)], 'eyeR': [round(eR[0], 1), round(eR[1], 1)], 'mouth': [cx, my], 'pivot': [24, 45], 'bulb': [round(tx, 1), t], 'box': [l, t, r, b]}
for k, f in acts['forms'].items(): out['forms'][k] = entry(f['idle'], k)
out['forms']['egg'] = entry('egg/egg_48.png', 'egg')
json.dump(out, open(os.path.join(B, 'kid_anchors.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
print('wrote', len(out['forms']), 'forms')
