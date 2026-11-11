#!/usr/bin/env python3
"""build_m2_props.py — §3.1 三件道具：信封、明信片、手信（billboard ＋ 薄片 glb）；另加腳印貼地。"""
import os, sys, json
import numpy as np
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import garden3d_mesh as GM
from m1_common import (
    V3, PAL, rgba, pset, fill_rect, fill_ellipse, outline_sel, harden_alpha,
    save_png, pack_atlas, normal_from_sprite,
)

def disc(im, cx, cy, r, col):
    fill_ellipse(im, cx, cy, r, r, col)

def finish(im, ol=(59, 42, 62)):
    outline_sel(im, ol)
    return harden_alpha(im)

def tex_envelope():
    """32×32，pivot (16,28)。"""
    im = rgba(32)
    # 信封 24×16 置於下部
    x0, y0, w, h = 4, 12, 24, 16
    fill_rect(im, x0, y0, x0 + w, y0 + h, PAL['cream1'])
    fill_rect(im, x0 + 1, y0 + 1, x0 + w - 1, y0 + h - 1, PAL['cream4'])
    # 蓋
    for i in range(w // 2):
        pset(im, x0 + i, y0 + 1 + i // 2, V3['gold'])
        pset(im, x0 + w - 1 - i, y0 + 1 + i // 2, V3['gold'])
        if i > 2:
            pset(im, x0 + i, y0 + 2 + i // 2, V3['goldhi'])
    # V3-A 蠟印
    disc(im, 16, 22, 3, V3['navy2'])
    disc(im, 16, 22, 2, V3['navy3'])
    pset(im, 16, 22, V3['goldhi'])
    return finish(im)

def tex_postcard():
    """32×32 明信片：原創遠足小景（丘＋日＋小路），唔抄真實地標。"""
    im = rgba(32)
    fill_rect(im, 3, 6, 29, 28, V3['navy2'])
    fill_rect(im, 4, 7, 28, 27, PAL['cream4'])
    # 天
    for y in range(8, 16):
        t = (y - 8) / 8
        col = tuple(int(135 * (1 - t) + 255 * t) for _ in range(1))
        # blue to peach
        r = int(135 + t * 80); g = int(189 - t * 20); b = int(224 - t * 60)
        for x in range(5, 27):
            im[y, x] = (r, g, b, 255)
    # 日
    disc(im, 21, 11, 3, V3['goldhi'])
    disc(im, 21, 11, 2, V3['amber'])
    # 遠丘
    for x in range(5, 27):
        y0 = 15 + int(2 * np.sin((x - 5) * 0.5) + 1 * np.sin((x) * 0.9))
        for y in range(y0, 22):
            col = (62, 78, 42) if y == y0 else (51, 69, 31)
            im[y, x] = (*col, 255)
    # 近草
    for x in range(5, 27):
        for y in range(21, 26):
            col = (103, 129, 53) if (x + y) % 5 else (150, 184, 70)
            im[y, x] = (*col, 255)
    # 小路
    for z, cx in enumerate(range(14, 20)):
        for dx in range(-1, 2):
            pset(im, 16 + dx + z // 2, 22 + z // 2, PAL['cream0'])
    # 邊框
    fill_rect(im, 4, 7, 28, 8, PAL['cream3'])
    fill_rect(im, 4, 26, 28, 27, PAL['cream3'])
    return finish(im)

def tex_letter():
    """手信：摺好嘅信紙＋葉印。"""
    im = rgba(32)
    fill_rect(im, 6, 8, 26, 26, PAL['cream1'])
    fill_rect(im, 7, 9, 25, 25, PAL['cream4'])
    # 摺痕
    for x in range(7, 25):
        pset(im, x, 16, PAL['cream2'])
    # 手寫線（抽象，唔寫字）
    for y, w in ((11, 14), (13, 11), (18, 13), (20, 9)):
        for x in range(10, 10 + w):
            pset(im, x, y, V3['ink'] if x % 3 else (66, 40, 4))
    # 葉印
    fill_ellipse(im, 20, 22, 4, 3, PAL['leaf_d'])
    fill_ellipse(im, 20, 21, 3, 2, PAL['leaf'])
    pset(im, 20, 22, V3['golddk'])
    return finish(im)

def tex_footprints():
    """64×32 貼地：一串兩對團絨腳印（左前右後）。"""
    im = rgba(32, 64)
    def pawprint(cx, cy, s=1.0, ang=0):
        # 掌＋三趾，深泥色
        rx, ry = int(5 * s), int(4 * s)
        fill_ellipse(im, cx, cy, rx, ry, (90, 58, 36))
        fill_ellipse(im, cx, cy, max(1, rx - 1), max(1, ry - 1), (122, 86, 58))
        for dx, dy in ((-3, -4), (0, -5), (3, -4)):
            fill_ellipse(im, cx + int(dx * s), cy + int(dy * s), max(1, int(2 * s)), max(1, int(2 * s)), (90, 58, 36))
    pawprint(14, 20, 1.0)
    pawprint(28, 14, 0.95)
    pawprint(42, 22, 1.0)
    pawprint(54, 15, 0.9)
    return finish(im, ol=(55, 26, 20))

def pad_pot(im, tw, th):
    """置中貼入 2 次方面。"""
    out = rgba(th, tw)
    h, w = im.shape[:2]
    blit = out
    y = th - h  # 底對齊
    x = (tw - w) // 2
    out[max(0, y):max(0, y) + h, max(0, x):max(0, x) + w] = im[:h, :w]
    # if y negative, skip
    if y < 0 or x < 0:
        out[:] = 0
        yy, xx = max(0, (th - h) // 2), max(0, (tw - w) // 2)
        hh, ww = min(h, th), min(w, tw)
        out[yy:yy + hh, xx:xx + ww] = im[:hh, :ww]
    return harden_alpha(out)

def card_mesh(mid, tex, zh, w_u, h_u, thick=2):
    """薄卡片／信封：前卡＋淺擠出。"""
    mb = GM.MB(mid)
    # 貼圖要 2 次方
    h, w = tex.shape[:2]
    side = 1 << int(np.ceil(np.log2(max(w, h, 8))))
    pot = pad_pot(tex, side, side) if (w, h) != (side, side) else tex
    if pot.shape[0] != side:
        pot = pad_pot(tex, side, side)
    ti = mb.add_tex(pot)
    hw, hh = w_u / 2, h_u
    # 正面（朝 +Z）
    mb.card((-hw, 0, thick / 2), (w_u, 0, 0), (0, hh, 0), ti, None, (0, 0.2, 0.98))
    # 背面
    mb.card((hw, 0, -thick / 2), (-w_u, 0, 0), (0, hh, 0), ti, None, (0, 0.2, -0.98))
    # 用盒做厚度
    # 已有前後卡足夠；加頂／側會超預算。薄件得。
    return mb, pot

def write_billboard(dir_, pid, zh, im, pivot, extra=None):
    os.makedirs(dir_, exist_ok=True)
    n = normal_from_sprite(im)
    save_png(f'{dir_}/{pid}.png', im)
    save_png(f'{dir_}/{pid}_n.png', n)
    rec = dict(id=pid, zh=zh, file=f'{pid}.png', normal=f'{pid}_n.png',
               sizePx=[int(im.shape[1]), int(im.shape[0])],
               pivotPx=list(pivot), alpha='0/255', normalConv='OpenGL Y+（綠＝上）',
               billboard=True)
    if extra:
        rec.update(extra)
    return rec, im, n

def build(out_root):
    art = os.path.join(out_root, 'art-pet')
    bd = os.path.join(art, 'sprites/props/m2')
    md = os.path.join(art, 'scenes/m2_props/meshes')
    os.makedirs(bd, exist_ok=True)
    os.makedirs(md, exist_ok=True)

    env = tex_envelope()
    post = tex_postcard()
    letter = tex_letter()
    feet = tex_footprints()

    items = []
    frames, names, norms = [], [], []
    for pid, zh, im, pv, note in (
        ('prop_envelope', '信封', env, (16, 28), '投信用；寵物 clip 已烙一封作示範，場景可再生成。'),
        ('prop_postcard', '明信片', post, (16, 28), '蝸牛郵差送到門口信箱；卡面係原創遠足小景。'),
        ('prop_letter', '手信', letter, (16, 28), '鄰居探訪完留低。'),
        ('decal_footprints', '腳印貼地', feet, (32, 28), '同手信一組：門口一串腳印。貼地 decal，唔使陰影。'),
    ):
        rec, im2, n = write_billboard(bd, pid, zh, im, pv, dict(note=note,
            type='decal' if pid.startswith('decal') else 'prop'))
        items.append(rec)
        frames.append(im if im.shape[1] == 32 else im)  # footprints 64 wide — pack separately
        names.append(pid)
        norms.append(n)

    # 32×32 三件一圖集；腳印獨立
    f32, n32, nm32 = [], [], []
    for rec, im, n in zip(items, [env, post, letter, feet], [normal_from_sprite(x) for x in (env, post, letter, feet)]):
        if im.shape[1] == 32 and im.shape[0] == 32:
            f32.append(im); n32.append(n); nm32.append(rec['id'])
    atl, fj, W, H = pack_atlas(f32, nm32, pad=2, cols=4)
    natl, _, _, _ = pack_atlas(n32, nm32, pad=2, cols=4, bg_n=True)
    save_png(f'{bd}/atlas_props.png', atl)
    save_png(f'{bd}/atlas_props_n.png', natl)
    for k, rec in fj.items():
        rec['pivotPx'] = {'x': 16, 'y': 28}

    # 3D 薄片（三件道具；腳印只做貼地 2D）
    meshes = {}
    src = os.path.join(art, 'scenes/m2_props')
    for mid, zh, tex, wu, hu in (
        ('prop_envelope', '信封', env, 24, 16),
        ('prop_postcard', '明信片', post, 24, 20),
        ('prop_letter', '手信', letter, 20, 20),
    ):
        mb, pot = card_mesh(mid, tex, zh, wu, hu, thick=2)
        fp = dict(rect=dict(x=[-wu / 2, wu / 2], z=[-1, 1]), pad=1)
        MJ = GM.write(mb, src, 'meshes', zh, fp, cast=True, recv=True)
        meshes[mid] = dict(json=f'meshes/{mid}.json', glb=f'meshes/{mid}.glb',
                           triangles=MJ['triangleCount'], textureSize=MJ['textureSize'])
        # 對應 billboard 記錄
        for it in items:
            if it['id'] == mid:
                it['glb'] = f'scenes/m2_props/meshes/{mid}.glb'
                it['mesh'] = f'scenes/m2_props/meshes/{mid}.json'
                it['units'] = '1 unit＝1 art px；薄片立喺 Y，pivot 底中'

    spec = dict(
        format='m2.props/1',
        count=len(items),
        alpha='0/255',
        normal='OpenGL Y+（綠＝上）',
        note='§3.1 三件：信封、明信片、手信。細件 billboard，同時出薄片 glb 俾 3D 場景擺。腳印貼地係 3.1 另一項，一併交付。',
        items=items,
        atlas=dict(image='atlas_props.png', normal='atlas_props_n.png',
                   size={'w': W, 'h': H}, padding=2, frames=fj,
                   note='只包 32×32 三件；腳印見 decal_footprints.png'),
        meshes=meshes,
        godot='billboard：Sprite3D Y-billboard、Nearest、Alpha Scissor 0.5。glb：同花園，MASK＋NEAREST，建議 import scale＝1。',
    )
    json.dump(spec, open(f'{bd}/props.json', 'w'), ensure_ascii=False, indent=1)
    json.dump(dict(format='m2.props.scene/1', meshes=meshes,
                   units='1 unit＝1 art px；Y 上'),
              open(f'{src}/index.json', 'w'), ensure_ascii=False, indent=1)
    return spec

if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else '/workspace/m2-actions-src'
    build(root)
    print('m2 props ok')
