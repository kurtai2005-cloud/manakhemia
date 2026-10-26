#!/usr/bin/env python3
"""art-audit.py — 對遊美素材做客觀量度（只讀 art/，輸出 docs/art-audit.json）。Pillow＋numpy。
量度：①lowfx 預模糊等效 σ（對 raw 做 wrap-aware 高斯擬合）②層左右接縫連續性 ③fore 螢火位置 ④野靈／貓／玩家 pivot vs 實際腳底 ⑤天空 Bayer 週期。"""
import json, os, sys
import numpy as np
from PIL import Image, ImageFilter
R = os.path.join(os.path.dirname(__file__), '..', 'art')
T = os.path.join(R, 'tracks', 'mossy_slope')
def load(p): return Image.open(p).convert('RGBA')
def premul(im):
    a = np.array(im).astype(np.float32); a[..., :3] *= a[..., 3:] / 255; return a
def wrapblur(im, s):
    w, h = im.size; a = Image.new('RGBA', (w * 3, h))
    for i in range(3): a.paste(im, (i * w, 0))
    pm = Image.fromarray(premul(a).clip(0, 255).astype(np.uint8), 'RGBA')
    return np.array(pm.filter(ImageFilter.GaussianBlur(s)).crop((w, 0, 2 * w, h))).astype(np.float32)
out = {}
# ① σ 擬合（art px；1080p 螢幕 px = ×2）
for name, lo, grid in (('mid', 'mid_lowfx', [1 + .25 * i for i in range(9)]), ('fore', 'fore_lowfx', [3 + .5 * i for i in range(5)])):
    raw = load(f'{T}/{name}.png'); low = premul(load(f'{T}/{lo}.png'))
    best = min((float(np.abs(wrapblur(raw, s) - low).mean()), s) for s in grid)
    out.setdefault('lowfx_sigma_fit', {})[lo] = {'sigma_art_px': best[1], 'sigma_1080p_px': best[1] * 2, 'residual_mean_abs': round(best[0], 3), 'spec_sigma_1080p_px': {'mid': 2.6, 'fore': 7}[name]}
# ② 接縫：左右邊界相鄰欄差 vs 內部相鄰欄差
seam = {}
for n in ['sky_far_night', 'sky_far_day', 'sky_far_dusk', 'mid', 'mid_lowfx', 'track', 'fore', 'fore_lowfx', 'lightmap_cool', 'lightmap_warm', 'lightmap_track', 'emissive_mid']:
    a = premul(load(f'{T}/{n}.png')); w = a.shape[1]
    edge = float(np.abs(a[:, 0] - a[:, w - 1]).mean()); inner = float(np.abs(a[:, 1:] - a[:, :-1]).mean())
    seam[n] = {'edge_diff': round(edge, 2), 'avg_adjacent_col_diff': round(inner, 2), 'ratio': round(edge / max(inner, 1e-6), 2)}
out['seam'] = seam
# ③ fore 螢火（黃白亮點）連通塊
f = np.array(load(f'{T}/fore.png')); m = (f[..., 3] > 200) & (f[..., 0] > 230) & (f[..., 1] > 220) & (f[..., 2] > 100)
from collections import deque
seen = np.zeros(m.shape, bool); ff = []
H, W = m.shape
for y in range(H):
    for x in range(W):
        if m[y, x] and not seen[y, x]:
            q = deque([(y, x)]); seen[y, x] = True; pts = []
            while q:
                cy, cx = q.popleft(); pts.append((cx, cy))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < H and 0 <= nx < W and m[ny, nx] and not seen[ny, nx]: seen[ny, nx] = True; q.append((ny, nx))
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; ff.append({'x': round(sum(xs) / len(xs), 1), 'y': round(sum(ys) / len(ys), 1), 'n': len(pts)})
out['fore_fireflies'] = {'count': len(ff), 'items': ff, 'note': '螢火烙入 fore.png，無獨立圖層／座標表；此為由像素偵測所得（建議遊美輸出 fireflies.json）'}
# ④ pivot vs 腳底
def feet(atlas, png, key=None):
    a = json.load(open(atlas)); im = np.array(load(png)); res = {}
    for n, fr in a['frames'].items():
        r = fr.get('frame', fr); sub = im[r['y']:r['y'] + r['h'], r['x']:r['x'] + r['w'], 3]
        ys = np.where(sub.max(1) > 0)[0]; xs = np.where(sub.max(0) > 0)[0]
        if len(ys) == 0: continue
        row = np.where(sub[ys.max()] > 0)[0]
        res[n] = {'bottom_row': int(ys.max()), 'top_row': int(ys.min()), 'x0': int(xs.min()), 'x1': int(xs.max()), 'feet_x': [int(row.min()), int(row.max())], 'touches_left_edge': bool(xs.min() == 0), 'touches_right_edge': bool(xs.max() == r['w'] - 1)}
    return a['meta'], res
A = os.path.join(R, 'sprites')
m1, cat = feet(f'{A}/narrowcat/spirit_narrowcat_atlas.json', f'{A}/narrowcat/spirit_narrowcat_atlas.png')
m2, c48 = feet(f'{A}/narrowcat/town48/spirit_narrowcat_town48_atlas.json', f'{A}/narrowcat/town48/spirit_narrowcat_town48_sheet.png')
m3, pl = feet(f'{A}/player/player_atlas.json', f'{A}/player/player_sheet.png')
out['pivot'] = {'narrowcat64': {'declared': m1.get('anchor_px'), 'frames': {k.replace('spirit_narrowcat_', ''): v for k, v in cat.items()}},
                'narrowcat_town48': {'declared': m2.get('pivot'), 'frames': {k.replace('spirit_narrowcat_town48_', ''): v for k, v in c48.items()}},
                'player32': {'declared': m3.get('pivot'), 'frames': {k.replace('player_', ''): v for k, v in pl.items()}}}
# ⑤ Bayer：sky 逐列高通殘差的自相關，lag 2/4 vs lag 3/5
s = np.array(load(f'{T}/sky_far_night.png').convert('L')).astype(np.float32)[10:110, 100:900]
hp = s - np.array(Image.fromarray(s.astype(np.uint8)).filter(ImageFilter.BoxBlur(8))).astype(np.float32)
def ac(a, lag): return float((a[:, :-lag] * a[:, lag:]).mean() / (a * a).mean())
out['bayer'] = {'region': 'sky_far_night y10-110 x100-900', 'hp_rms': round(float(hp.std()), 3), 'autocorr_x': {str(l): round(ac(hp, l), 3) for l in (1, 2, 3, 4, 5, 8)}}
json.dump(out, open(os.path.join(R, '..', 'docs', 'art-audit.json'), 'w'), indent=1, ensure_ascii=False)
print(json.dumps({k: out[k] for k in ('lowfx_sigma_fit', 'bayer')}, indent=1, ensure_ascii=False)); print('fireflies', out['fore_fireflies']['count']); print({k: v['ratio'] for k, v in seam.items()})
