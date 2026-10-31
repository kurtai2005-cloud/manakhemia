#!/usr/bin/env python3
"""生命感 live atlas 嘅 rim mask（HD-2D 輪廓光）：算法同遊美 art-pet/tools/build_tuanrong_rim.py 一致
（1px 內緣、R/G＝外向法線、B=255），輸出 art/rim/rim_<form>_live.png/json（同 live atlas 同尺寸、同 rect、同幀名）。
只寫 glimmer-live/art/rim/，唔掂 game-design。用法：python3 tools/build-rim-live.py"""
import os, json
import numpy as np
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVE = os.path.join(ROOT, 'art', 'liveliness'); RIM = os.path.join(ROOT, 'art', 'rim')
DIRS = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
def rim_frame(a):
    inside = a > 127; H, W = inside.shape; P = np.pad(inside, 1)
    nx = np.zeros((H, W)); ny = np.zeros((H, W)); edge = np.zeros((H, W), bool)
    for dx, dy in DIRS:
        out = ~P[1+dy:1+dy+H, 1+dx:1+dx+W]
        if dx == 0 or dy == 0: edge |= out & inside
        w = 1.0 if (dx == 0 or dy == 0) else 0.7071
        nx += out*dx*w; ny += out*dy*w
    n = np.hypot(nx, ny); z = n < 1e-6
    nx = np.where(z, 0, nx/np.maximum(n, 1e-6)); ny = np.where(z, -1, ny/np.maximum(n, 1e-6))
    return edge, nx, ny
def encode(edge, nx, ny):
    o = np.zeros(edge.shape+(4,), np.uint8)
    o[..., 0] = np.round((nx*0.5+0.5)*255); o[..., 1] = np.round((ny*0.5+0.5)*255); o[..., 2] = 255; o[..., 3] = 255
    o[~edge] = 0; return o
os.makedirs(RIM, exist_ok=True)
for form in ('sprout', 'radiant', 'soft'):
    J = json.load(open(os.path.join(LIVE, f'atlas_{form}_live.json')))
    img = np.asarray(Image.open(os.path.join(LIVE, J['meta']['image'])).convert('RGBA'))
    out = np.zeros_like(img); fr = {}
    for k, f in J['frames'].items():
        if '_noface' not in k: continue          # 只做身體幀（五官件喺身體輪廓入面）
        r = f['frame']; x, y, w, h = r['x'], r['y'], r['w'], r['h']
        out[y:y+h, x:x+w] = encode(*rim_frame(img[y:y+h, x:x+w, 3])); fr[k] = {'frame': r}
    Image.fromarray(out, 'RGBA').save(os.path.join(RIM, f'rim_{form}_live.png'), optimize=True)
    json.dump({'frames': fr, 'meta': {'image': f'rim_{form}_live.png', 'size': J['meta']['size'], 'sourceAtlas': f'liveliness/atlas_{form}_live.json',
               'encoding': 'edge 1px inner; R=nx*0.5+0.5, G=ny*0.5+0.5, B=255; scaleX -1 → flip nx'}}, open(os.path.join(RIM, f'rim_{form}_live.json'), 'w'), separators=(',', ':'))
    print(form, len(fr), 'frames')
