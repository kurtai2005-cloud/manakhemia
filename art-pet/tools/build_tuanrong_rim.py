#!/usr/bin/env python3
"""團絨 rim mask（HD-2D 輪廓光用）— 遊美
由 motion/atlas_<form>.png 每個 frame rect 自動出 1px 內緣 mask：
  rim/rim_<form>.png  ＝同 atlas 同尺寸、同 rect（json 幀名／rect 直接抄 atlas）
  rim/rim_<form>.json
  rim/<form>/<frame>.png 單幀
像素：內緣 alpha 255；RGB＝外向法線 R=(nx*.5+.5)*255, G=(ny*.5+.5)*255, B=255（y 向下）。
可重跑（覆蓋 rim/ 自己嘅輸出，唔掂其他資料夾）。之後有新 atlas（例如新 clip）：
  python3 build_tuanrong_rim.py path/to/atlas_xxx.json [...]   → 出 rim/rim_xxx.*
唔處理 motion/liveliness/（另一單工作進行中）同 egg。"""
import os, sys, json
import numpy as np
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPR = os.path.join(ROOT, 'sprites', 'tuanrong', 'motion')
RIM = os.path.join(ROOT, 'sprites', 'tuanrong', 'rim')
DIRS = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]

def rim_frame(a):
    """a: HxW alpha(0/255) → (mask bool, nx, ny)"""
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

def build(atlas_json, name=None):
    J = json.load(open(atlas_json)); base = os.path.dirname(atlas_json)
    img = np.asarray(Image.open(os.path.join(base, J['meta']['image'])).convert('RGBA'))
    name = name or os.path.splitext(os.path.basename(atlas_json))[0].replace('atlas_', '')
    out = np.zeros_like(img); fd = os.path.join(RIM, name); os.makedirs(fd, exist_ok=True)
    R = {'frames': {}, 'animations': J.get('animations', {}), 'meta': dict(J['meta'])}
    for k, f in J['frames'].items():
        r = f['frame']; x, y, w, h = r['x'], r['y'], r['w'], r['h']
        e, nx, ny = rim_frame(img[y:y+h, x:x+w, 3]); px = encode(e, nx, ny)
        out[y:y+h, x:x+w] = px; Image.fromarray(px, 'RGBA').save(os.path.join(fd, f'{k}.png'))
        R['frames'][k] = json.loads(json.dumps(f))
    R['meta'].update(image=f'rim_{name}.png', sourceAtlas=os.path.relpath(atlas_json, os.path.dirname(RIM)),
                     encoding='edge 1px inner; alpha 255 = rim; R=nx*0.5+0.5, G=ny*0.5+0.5 (screen y down), B=255; scaleX -1 → flip nx',
                     usage='w = max(0, nx*dir.x + ny*dir.y) → rim.color × rim.intensity × w；或者直接當 mask 用（全邊）')
    R['meta'].pop('extrude', None); R['meta']['extrude'] = 0
    Image.fromarray(out, 'RGBA').save(os.path.join(RIM, f'rim_{name}.png'))
    json.dump(R, open(os.path.join(RIM, f'rim_{name}.json'), 'w'), ensure_ascii=False, indent=1)
    return name, len(R['frames'])

if __name__ == '__main__':
    os.makedirs(RIM, exist_ok=True)
    targets = sys.argv[1:] or [os.path.join(SPR, f'atlas_{f}.json') for f in ('sprout', 'radiant', 'soft')]
    for t in targets:
        if 'liveliness' in t or 'egg' in os.path.basename(t): print('skip', t); continue
        print('rim', *build(t))
    # 預覽：每款 idle_01 原圖＋rim（左上光 dir[-0.7,-0.7] 示意）
    tiles = []
    for f in ('sprout', 'radiant', 'soft'):
        p = os.path.join(SPR, 'frames', f, 'idle_01.png'); q = os.path.join(RIM, f, 'idle_01.png')
        if not (os.path.exists(p) and os.path.exists(q)): continue
        s = np.asarray(Image.open(p).convert('RGBA')).astype(float); m = np.asarray(Image.open(q)).astype(float)
        nx, ny = m[..., 0]/127.5-1, m[..., 1]/127.5-1; w = np.clip(nx*-0.707+ny*-0.707, 0, 1)*(m[..., 3] > 0)
        c = s.copy(); c[..., :3] = c[..., :3]*(1-0.8*w[..., None]) + np.array([255, 226, 168])*0.8*w[..., None]
        bg = np.zeros((64, 64*3, 4)); bg[...] = (40, 44, 70, 255); h, wd = s.shape[:2]
        for i, im in enumerate((s, m, c)):
            a = im[..., 3:]/255; reg = bg[64-h:, i*64+(64-wd)//2:i*64+(64-wd)//2+wd]; reg[..., :3] = reg[..., :3]*(1-a)+im[..., :3]*a
        tiles.append(bg)
    if tiles:
        Image.fromarray(np.concatenate(tiles, 0).astype(np.uint8)).resize((64*3*4, 64*len(tiles)*4), Image.NEAREST).save(os.path.join(RIM, 'rim_preview_4x.png'))
