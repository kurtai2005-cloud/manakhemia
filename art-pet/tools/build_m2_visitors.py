#!/usr/bin/env python3
"""build_m2_visitors.py — 3 位訪客各 1 個招牌動作（§3.1／3b：蝸牛郵差、蘑菇婆婆、螢火小販）。
程序化像素，造型同已有 3b 訪客一致但新畫招牌勢；png＋_n（OpenGL Y+）＋emissive＋atlas json。"""
import os, sys, json, math
import numpy as np
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from m1_common import (
    V3, PAL, rgba, pset, fill_rect, fill_ellipse, outline_sel, harden_alpha,
    blit, shift, save_png, pack_atlas, normal_from_sprite,
)

OL = (59, 42, 62)

def disc(im, cx, cy, r, col, a=255):
    fill_ellipse(im, cx, cy, r, r, col, a)

def finish(im, ol=OL):
    outline_sel(im, ol)
    return harden_alpha(im)

# 既有 3b 色（保持認得出，新畫招牌勢）
SNAIL = dict(shell=(242, 166, 150), shell_l=(255, 214, 196), shell_d=(214, 120, 110),
             body=(246, 221, 176), body_l=(255, 239, 196),
             cap=(66, 90, 168), cap_l=(110, 140, 210), bag=(70, 110, 190), bag_l=(140, 180, 230))
GRAN = dict(cap=(214, 72, 86), cap_l=(240, 126, 150), spot=(255, 244, 230),
            face=(255, 239, 196), body=(190, 150, 200), body_d=(150, 110, 168),
            cane=(122, 86, 58), cane_l=(176, 126, 72))
FLY = dict(body=(120, 206, 176), body_l=(180, 240, 210), body_d=(70, 150, 130),
           wing=(200, 230, 240), wing_l=(230, 248, 255),
           lamp=(255, 233, 138), lamp_d=(242, 166, 90), box=(176, 126, 72), box_l=(222, 180, 116))

def eyes(im, x, y, kind='idle'):
    if kind == 'happy':
        for dx in (0, 6):
            pset(im, x + dx, y, OL)
            pset(im, x + dx + 1, y, OL)
            pset(im, x + dx - 1, y + 1, OL)
            pset(im, x + dx + 2, y + 1, OL)
        return
    if kind == 'closed':
        for dx in (0, 6):
            pset(im, x + dx, y, OL)
            pset(im, x + dx + 1, y, OL)
        return
    for dx in (0, 6):
        pset(im, x + dx, y, (40, 32, 48))
        pset(im, x + dx + 1, y, (40, 32, 48))
        pset(im, x + dx, y + 1, (40, 32, 48))
        pset(im, x + dx + 1, y + 1, (40, 32, 48))
        pset(im, x + dx, y, PAL['white'])

def blush(im, x, y):
    pset(im, x, y, PAL['blush']); pset(im, x + 7, y, PAL['blush'])

# ---------- 蝸牛郵差招牌：鞠躬遞信 ----------
def snail_deliver(i, W=48, H=40):
    im = rgba(H, W)
    bob = [0, 0, -1, -2, -1, 0][i]          # 鞠躬下壓
    sway = [0, 1, 0, -1, 0, 1][i]
    # 殼
    cx, cy = 18 + sway, 20 + bob
    fill_ellipse(im, cx, cy, 11, 10, SNAIL['shell_d'])
    fill_ellipse(im, cx, cy, 10, 9, SNAIL['shell'])
    fill_ellipse(im, cx - 2, cy - 2, 5, 4, SNAIL['shell_l'])
    # 螺旋
    pset(im, cx, cy, SNAIL['shell_d']); pset(im, cx + 2, cy + 1, SNAIL['shell_d'])
    # 身體＋頭
    hx, hy = 30 + sway, 22 + bob
    fill_ellipse(im, hx, hy + 4, 8, 6, SNAIL['body'])
    fill_ellipse(im, hx + 1, hy, 7, 6, SNAIL['body_l'])
    # 帽
    fill_ellipse(im, hx + 1, hy - 5, 6, 4, SNAIL['cap'])
    fill_ellipse(im, hx + 1, hy - 6, 5, 3, SNAIL['cap_l'])
    # 觸角
    pset(im, hx - 1, hy - 10, SNAIL['cap']); pset(im, hx - 1, hy - 11, SNAIL['cap'])
    disc(im, hx - 1, hy - 12, 1, SNAIL['cap_l'])
    pset(im, hx + 3, hy - 10, SNAIL['cap']); pset(im, hx + 3, hy - 11, SNAIL['cap'])
    disc(im, hx + 3, hy - 12, 1, SNAIL['cap_l'])
    eyes(im, hx - 2, hy - 1, 'happy' if i in (3, 4) else 'idle')
    blush(im, hx - 3, hy + 2)
    # 信袋（身側）
    fill_rect(im, hx - 2, hy + 3, hx + 4, hy + 9, SNAIL['bag'])
    fill_rect(im, hx - 1, hy + 4, hx + 3, hy + 8, SNAIL['bag_l'])
    # 遞出嘅信（越鞠躬越向前／上）
    lx = hx + 6 + [0, 1, 3, 5, 4, 2][i]
    ly = hy + 2 + [2, 1, 0, -1, 0, 1][i]
    fill_rect(im, lx, ly, lx + 6, ly + 7, V3['navy3'])
    fill_rect(im, lx + 1, ly + 1, lx + 5, ly + 6, V3['navy2'])
    pset(im, lx + 3, ly + 3, V3['goldhi'])
    return finish(im)

# ---------- 蘑菇婆婆招牌：奉上種子、點頭 ----------
def granny_seed(i, W=40, H=48):
    im = rgba(H, W)
    nod = [0, 1, 2, 1, 0, 0][i]
    # 菇傘
    cx, cy = 20, 14 + nod
    fill_ellipse(im, cx, cy, 16, 10, GRAN['cap'])
    fill_ellipse(im, cx, cy - 2, 14, 8, GRAN['cap_l'])
    for sx, sy in ((12, 10), (20, 8), (26, 11), (16, 13), (24, 14)):
        disc(im, sx, sy + nod, 2, GRAN['spot'])
    # 身體
    fill_ellipse(im, 20, 30 + nod // 2, 9, 8, GRAN['body_d'])
    fill_ellipse(im, 20, 28 + nod // 2, 8, 7, GRAN['face'])
    fill_ellipse(im, 20, 34 + nod // 2, 8, 6, GRAN['body'])
    eyes(im, 16, 26 + nod // 2, 'happy' if i in (2, 3) else 'idle')
    blush(im, 15, 29 + nod // 2)
    # 手杖（右側）
    for y in range(22 + nod, 46):
        pset(im, 32, y, GRAN['cane'])
        pset(im, 33, y, GRAN['cane_l'])
    fill_ellipse(im, 32, 22 + nod, 3, 2, GRAN['cane_l'])
    # 種子捧喺胸前，遞出
    sx = 20 + [0, 0, 1, 2, 1, 0][i]
    sy = 36 + nod // 2 - [0, 1, 2, 2, 1, 0][i]
    fill_ellipse(im, sx, sy, 3, 4, PAL['egg_dark'])
    fill_ellipse(im, sx, sy - 1, 2, 3, PAL['egg_shade'])
    pset(im, sx, sy - 4, PAL['leaf'])
    pset(im, sx, sy - 5, PAL['leaf_d'])
    return finish(im)

# ---------- 螢火小販招牌：搖螢火瓶展示貨物 ----------
def vendor_show(i, W=48, H=48):
    im = rgba(H, W)
    hover = [0, -1, -2, -1, 0, -1][i]
    # 箱（左側貨物）
    fill_rect(im, 4, 24 + hover, 16, 38 + hover, FLY['box'])
    fill_rect(im, 5, 25 + hover, 15, 37 + hover, FLY['box_l'])
    fill_rect(im, 4, 24 + hover, 16, 26 + hover, (143, 86, 47))
    # 身
    cx, cy = 28, 26 + hover
    fill_ellipse(im, cx, cy, 10, 11, FLY['body_d'])
    fill_ellipse(im, cx, cy - 1, 9, 10, FLY['body'])
    fill_ellipse(im, cx - 2, cy - 3, 4, 4, FLY['body_l'])
    eyes(im, cx - 4, cy - 2, 'happy' if i in (2, 3, 4) else 'idle')
    blush(im, cx - 5, cy + 2)
    # 翼（搧）
    wf = [0, 2, 0, -2, 0, 2][i]
    fill_ellipse(im, cx - 8, cy - 8 + wf, 7, 5, FLY['wing'])
    fill_ellipse(im, cx - 8, cy - 8 + wf, 5, 3, FLY['wing_l'])
    fill_ellipse(im, cx + 8, cy - 9 - wf, 6, 5, FLY['wing'])
    fill_ellipse(im, cx + 8, cy - 9 - wf, 4, 3, FLY['wing_l'])
    # 螢火瓶（右手搖）
    jx = cx + 10 + [0, 1, 2, 0, -1, 1][i]
    jy = cy + 2 + [-1, 0, -2, 1, 0, -1][i]
    fill_ellipse(im, jx, jy, 5, 7, (180, 200, 210))
    fill_ellipse(im, jx, jy, 4, 6, (220, 240, 230))
    disc(im, jx, jy + 1, 3, FLY['lamp'])
    disc(im, jx - 1, jy, 2, FLY['lamp_d'] if i % 2 else V3['goldhi'])
    pset(im, jx - 1, jy - 1, V3['goldhi'])
    # 瓶蓋
    fill_rect(im, jx - 2, jy - 7, jx + 3, jy - 5, FLY['box'])
    return finish(im)

VISITORS = [
    dict(id='snail_postman', zh='蝸牛郵差', clip='snail_deliver', clip_zh='鞠躬遞信',
         size=(48, 40), pivot=(22, 37), fps=8, loop=True, draw=snail_deliver,
         note='3b 訪客；招牌：鞠躬遞出信件。'),
    dict(id='mushroom_granny', zh='蘑菇婆婆', clip='granny_seed', clip_zh='奉上種子',
         size=(40, 48), pivot=(20, 45), fps=8, loop=True, draw=granny_seed,
         note='3b 訪客；招牌：點頭奉上種子。'),
    dict(id='firefly_vendor', zh='螢火小販', clip='vendor_show', clip_zh='搖瓶展示',
         size=(48, 48), pivot=(24, 44), fps=8, loop=True, draw=vendor_show,
         note='3b 訪客（夜間 17:00–07:00）；招牌：飛住搖螢火瓶展示貨物。'),
]

def emissive_of(f, firefly=False):
    e = np.zeros_like(f)
    if firefly:
        # 黃／暖白燈
        glow = (f[..., 3] > 0) & (f[..., 0] >= 230) & (f[..., 1] >= 180) & (f[..., 2] <= 180)
        e[glow] = f[glow]
        # 翼淡光
        wing = (f[..., 3] > 0) & (f[..., 2] >= 220) & (f[..., 1] >= 220) & (f[..., 0] >= 180)
        e[wing] = (f[wing].astype(np.int16) // 2).astype(np.uint8)
        e[wing, 3] = 255
    else:
        glow = (f[..., 3] > 0) & (f[..., 0] >= 250) & (f[..., 1] >= 220) & (f[..., 2] <= 200)
        e[glow] = f[glow]
    return harden_alpha(e)

def build(out_root):
    vd = os.path.join(out_root, 'art-pet/sprites/visitors/m2')
    os.makedirs(vd, exist_ok=True)
    index_items = []
    for meta in VISITORS:
        w, h = meta['size']
        # 畫布用 2 次方 cell 方便 atlas：統一 48×48，底對齊
        cell = 48
        frs, names = [], []
        for i in range(6):
            raw = meta['draw'](i)
            canvas = rgba(cell, cell)
            # 底對齊、水平置中
            y = cell - raw.shape[0]
            x = (cell - raw.shape[1]) // 2
            canvas[y:y + raw.shape[0], x:x + raw.shape[1]] = raw
            # pivot 跟住平移
            frs.append(harden_alpha(canvas))
            names.append(f"{meta['clip']}_{i+1:02d}")
        # 調整 pivot：原 pivot 相對原畫布，加上偏移
        ox = (cell - w) // 2
        oy = cell - h
        pivot = (meta['pivot'][0] + ox, meta['pivot'][1] + oy)
        norms = [normal_from_sprite(f) for f in frs]
        ems = [emissive_of(f, firefly=(meta['id'] == 'firefly_vendor')) for f in frs]
        atl, fj, W, H = pack_atlas(frs, names, pad=2, cols=6)
        natl, _, _, _ = pack_atlas(norms, names, pad=2, cols=6, bg_n=True)
        eatl, _, _, _ = pack_atlas(ems, names, pad=2, cols=6)
        stem = f"atlas_{meta['id']}_{meta['clip']}"
        save_png(f'{vd}/{stem}.png', atl)
        save_png(f'{vd}/{stem}_n.png', natl)
        save_png(f'{vd}/{stem}_emissive.png', eatl)
        for n, rec in fj.items():
            rec['pivotPx'] = {'x': pivot[0], 'y': pivot[1]}
        js = dict(format='m2.visitorclip.atlas/1', id=meta['id'], zh=meta['zh'],
                  clip=meta['clip'], clip_zh=meta['clip_zh'],
                  frameSize=cell, pivotPx=list(pivot), srcSize=list(meta['size']),
                  frames=fj, fps=meta['fps'], loop=meta['loop'], frameCount=6,
                  facing='朝右；朝左＝scaleX −1，法線 R→255−R',
                  alpha='0/255', normal='OpenGL Y+（綠＝上）',
                  billboard=True, note=meta['note'],
                  meta=dict(image=f'{stem}.png', normal=f'{stem}_n.png', emissive=f'{stem}_emissive.png',
                            size={'w': W, 'h': H}, padding=2, frameSize=cell, pivotPx=list(pivot)))
        json.dump(js, open(f'{vd}/{stem}.json', 'w'), ensure_ascii=False, indent=1)
        index_items.append(dict(id=meta['id'], zh=meta['zh'], clip=meta['clip'], clip_zh=meta['clip_zh'],
                                atlas=f'{stem}.json', pivotPx=list(pivot), frameSize=cell,
                                fps=meta['fps'], loop=meta['loop'], note=meta['note']))
        print('  visitor', meta['id'], flush=True)
    idx = dict(format='m2.visitors/1', count=3,
               note='§3.1 訪客招牌動作 × 每位 1。三位即 3b 朋友訪客（蝸牛郵差、蘑菇婆婆、螢火小販）。',
               items=index_items)
    json.dump(idx, open(f'{vd}/visitors.json', 'w'), ensure_ascii=False, indent=1)
    return idx

if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else '/workspace/m2-actions-src'
    build(root)
    print('m2 visitors ok')
