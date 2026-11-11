#!/usr/bin/env python3
"""build_hunt3d.py — 狩獵 M1 lite 草原 1 區 3D 場景（最低畫質）。
場景物件＝立體 mesh（garden3d.mesh/2 ＋ glTF 2.0 .glb）；角色 billboard。
程序化像素貼圖，Pillow／numpy，冇 AI 圖。地面／鏡頭／光影對齊花園 H1。"""
import os, sys, json, math, shutil
import numpy as np
from PIL import Image, ImageFilter
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import garden3d_mesh as GM
from m1_common import V3, PAL, HUNT, rgba, pset, fill_rect, fill_ellipse, harden_alpha, save_png

def disc(im, cx, cy, r, col):
    fill_ellipse(im, cx, cy, r, r, col)

def clamp(v, a, b):
    return a if v < a else b if v > b else v

# ----- H1 式可平鋪 value noise ＋ Bayer 量化（柔和色階，唔用規則斜線 hash）-----
BAY = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], float) + 0.5) / 16.0
MAT = {
    'GRASS': np.array([(57, 74, 38), (103, 129, 53), (150, 184, 70), (174, 192, 76)], np.uint8),
    'MOSS':  np.array([(35, 58, 26), (51, 69, 31), (68, 78, 41)], np.uint8),
    'SOIL':  np.array([(55, 26, 20), (143, 86, 47), (222, 180, 116)], np.uint8),
    'STONE': np.array([(92, 72, 69), (181, 148, 117)], np.uint8),
    'CLOVER': np.array([(51, 69, 31), (137, 175, 62)], np.uint8),
    'LEAF':  np.array([(40, 52, 32), (51, 69, 31), (62, 78, 42), (78, 98, 50)], np.uint8),
    'WOOD':  np.array([(55, 26, 20), (143, 86, 47), (176, 126, 72), (222, 180, 116)], np.uint8),
}

def pnoise(N, cells, seed):
    """可平鋪 value noise（週期 N px，cells 格）。"""
    g = np.random.default_rng(seed).random((cells, cells)); c = N / cells
    u = (np.arange(N) + .5) / c; i0 = np.floor(u).astype(int); fu = u - i0; fu = fu * fu * (3 - 2 * fu)
    i0 %= cells; i1 = (i0 + 1) % cells
    a = g[i0][:, i0] * (1 - fu)[None, :] + g[i0][:, i1] * fu[None, :]
    b = g[i1][:, i0] * (1 - fu)[None, :] + g[i1][:, i1] * fu[None, :]
    return a * (1 - fu)[:, None] + b * fu[:, None]

def mput(rgb, mask, mat, f, dither=0.35):
    pal = MAT[mat]; n = len(pal)
    H, W = rgb.shape[:2]
    bay = BAY[np.arange(H)[:, None] % 4, np.arange(W)[None, :] % 4]
    fv = f[mask] if isinstance(f, np.ndarray) else np.full(int(mask.sum()), f)
    q = np.clip(np.floor(fv * n + (bay[mask] - 0.5) * dither * 2), 0, n - 1).astype(int)
    rgb[mask] = pal[q]

def ids_to_rgba(m, lut_from_mat=None):
    """legacy helper unused — we paint RGB directly."""
    pass

TILE = 64

def grass_tile():
    """H1 同款：Perlin 簇＋Bayer 量化到 4 級草；偶發短高光，唔鋪滿斜線。"""
    n1, n2, n3 = pnoise(TILE, 8, 11), pnoise(TILE, 16, 12), pnoise(TILE, 4, 13)
    gf = np.clip(0.55 + 0.25 * (n1 - .5) + 0.3 * (n2 - .5) + .15 * (n3 - .5), 0, 1)
    rgb = np.zeros((TILE, TILE, 3), np.uint8)
    mput(rgb, np.ones((TILE, TILE), bool), 'GRASS', gf)
    rng = np.random.default_rng(21)
    for (y, x) in zip(*np.where(rng.random((TILE, TILE)) > .975)):
        rgb[y, x] = MAT['GRASS'][-1]
        rgb[(y + 1) % TILE, (x + 1) % TILE] = MAT['GRASS'][0]
    for (y, x) in zip(*np.where(rng.random((TILE, TILE)) > .992)):
        rgb[y, x] = MAT['MOSS'][-1]
    return rgb, gf

def paint_ground():
    """256×256 俯視：tile×4 底＋舞台淺草／小路／泥位／踏石／苔叢／花，邊 6–20px 淡出接 tile。"""
    N = 256
    T, gf_t = grass_tile()
    rgb = np.tile(T, (4, 4, 1))
    gf = np.tile(gf_t, (4, 4))
    Z, X = np.mgrid[0:N, 0:N].astype(float) + .5 - 128
    rng = np.random.default_rng(7)
    edge = np.minimum(np.minimum(X + 128, 128 - X), np.minimum(Z + 128, 128 - Z))
    busy = np.zeros((N, N), bool)

    def ell(cx, cz, rx, rz):
        return ((X - cx) / rx) ** 2 + ((Z - cz) / rz) ** 2 <= 1

    # 寵物出發淺草舞台（原點附近）
    st = ell(0, 8, 70, 36)
    mput(rgb, st, 'GRASS', np.clip(gf + .16, 0, 1))
    r = np.hypot(X / 22, (Z - 8) / 12)
    mput(rgb, r <= 1, 'MOSS', np.clip(.7 - .45 * r + .15 * (pnoise(N, 32, 3) - .5), 0, 1), .5)

    # 小路：近處舞台 → 右後方木拱門方向（彎、闊窄唔規則）
    pts = [(4, 28), (10, 8), (18, -16), (28, -40), (40, -64), (52, -88), (62, -108)]
    path = np.zeros((N, N), bool)
    pn = pnoise(N, 64, 5)
    for (x0, z0), (x1, z1) in zip(pts[:-1], pts[1:]):
        for t in np.linspace(0, 1, 48):
            cx, cz = x0 + (x1 - x0) * t, z0 + (z1 - z0) * t
            path |= np.hypot(X - cx, Z - cz) <= 5.2 + 1.8 * (pn - .5) * 2
    mput(rgb, path, 'SOIL', np.clip(.62 + .3 * (pnoise(N, 48, 6) - .5), 0, 1), .5)
    grav = path & (rng.random((N, N)) > .9)
    mput(rgb, grav, 'STONE', .8, 0)
    # 簡單 dilation（唔靠 scipy）
    dil = path.copy()
    dil[1:] |= path[:-1]; dil[:-1] |= path[1:]; dil[:, 1:] |= path[:, :-1]; dil[:, :-1] |= path[:, 1:]
    dil[1:] |= dil[:-1]; dil[:-1] |= dil[1:]; dil[:, 1:] |= dil[:, :-1]; dil[:, :-1] |= dil[:, 1:]
    busy |= dil

    # 採集泥位（幾笪清出嚟嘅泥地）
    for cx, cz, rx, rz, seed in ((-36, -18, 12, 9, 11), (32, -42, 11, 8, 12), (8, -8, 9, 7, 13), (44, -70, 10, 7, 14)):
        k = ell(cx, cz, rx, rz)
        mput(rgb, k, 'SOIL', np.clip(.5 + .35 * (pnoise(N, 32, seed) - .5), 0, 1), .45)
        busy |= k

    # 左後苔丘底
    tr = ell(-78, -100, 30, 18)
    mput(rgb, tr, 'MOSS', np.clip(.45 + .4 * (pnoise(N, 32, 8) - .5), 0, 1), .5)
    mput(rgb, ell(-78, -100, 10, 6), 'SOIL', .5, .3)
    busy |= ell(-78, -100, 32, 20)

    # 踏腳石（沿路）
    stones = [(2, 22, 5, 4), (8, 4, 4.5, 3.5), (16, -14, 5, 4), (26, -38, 4.5, 3.6),
              (38, -62, 5, 4), (50, -86, 4.8, 3.8), (-12, -30, 4, 3.2)]
    for cx, cz, rx, rz in stones:
        k = ell(cx, cz, rx, rz)
        rr = np.hypot((X - cx) / rx, (Z - cz) / rz)
        mput(rgb, k, 'STONE', np.clip(.72 - .35 * rr ** 2 + .12 * (pnoise(N, 64, int(cx + 50)) - .5), 0, 1), .3)
        ring = ell(cx, cz, rx + 1.5, rz + 1.5) & ~k & (rng.random((N, N)) > .55)
        mput(rgb, ring, 'MOSS', .7, 0)
        busy |= ell(cx, cz, rx + 3, rz + 3)

    fade = np.clip((edge - 6) / 14, 0, 1)
    ok = ~busy & (rng.random((N, N)) < fade)
    # 三葉草叢
    for _ in range(22):
        cx, cz = rng.uniform(-118, 118), rng.uniform(-118, 118)
        for _k in range(10):
            x, z = int(cx + rng.integers(-6, 7) + 128), int(cz + rng.integers(-5, 6) + 128)
            if 1 <= x < N - 1 and 1 <= z < N - 1 and ok[z, x]:
                rgb[z, x] = MAT['CLOVER'][-1]
                rgb[z, x - 1] = MAT['CLOVER'][0]
                rgb[z + 1, x] = MAT['CLOVER'][0]
    # 小花
    flowers = [V3['rose'], V3['gold'], (255, 244, 230), V3['violet'], (240, 126, 150)]
    for i in range(140):
        x, z = int(rng.integers(2, N - 2)), int(rng.integers(2, N - 2))
        if not ok[z, x]:
            continue
        col = flowers[i % len(flowers)]
        rgb[z + 1, x] = MAT['CLOVER'][0]
        rgb[z, x] = col
        if i % 3 == 0:
            rgb[z, x + 1] = col
    # 細石
    for i in range(36):
        x, z = int(rng.integers(2, N - 2)), int(rng.integers(2, N - 2))
        if ok[z, x]:
            rgb[z, x] = MAT['STONE'][-1]
            rgb[z, x + 1] = MAT['STONE'][0]

    im = np.zeros((N, N, 4), np.uint8)
    im[..., :3] = rgb
    im[..., 3] = 255
    return harden_alpha(im)

def paint_tile():
    rgb, _ = grass_tile()
    im = np.zeros((TILE, TILE, 4), np.uint8)
    im[..., :3] = rgb
    im[..., 3] = 255
    return harden_alpha(im)

def paint_ao(objects):
    """@3x 計柔和 footprint AO，再平均回 256（同 H1 思路）。"""
    S, N = 3, 256
    occ = np.zeros((N * S, N * S), np.float32)
    Z3, X3 = np.mgrid[0:N * S, 0:N * S].astype(np.float32) / S + 1 / (2 * S) - 128
    for o in objects:
        if o.get('layer') == 'far' and o.get('id', '').startswith('tree'):
            continue
        fp = o.get('footprint')
        if not fp:
            continue
        if fp['type'] == 'rect':
            fx, fz = fp['x'], fp['z']
        else:
            P_ = np.array(fp['points']); fx, fz = [P_[:, 0].min(), P_[:, 0].max()], [P_[:, 1].min(), P_[:, 1].max()]
        dx = np.maximum(np.maximum(fx[0] - X3, X3 - fx[1]), 0)
        dz = np.maximum(np.maximum(fz[0] - Z3, Z3 - fz[1]), 0)
        occ = np.maximum(occ, .5 * np.exp(-np.hypot(dx, dz) / 3.2))
    # 輕高斯（PIL）
    occ_u = np.clip(occ * 255, 0, 255).astype(np.uint8)
    blur = np.array(Image.fromarray(occ_u).filter(ImageFilter.GaussianBlur(radius=1.5)), np.float32) / 255.0
    ao3 = (np.clip(1 - blur, 0, 1) * 255 + .5).astype(np.uint8)
    ao1 = (ao3.reshape(N, S, N, S).astype(np.float32).mean((1, 3)) + .5).astype(np.uint8)
    def to_rgba(a):
        out = np.stack([a, a, a, np.full_like(a, 255)], -1)
        return out
    return to_rgba(ao1), to_rgba(ao3)

# ----- 像素貼圖＋ mesh -----
def tex_grass_card(seed=0, w=24, h=32):
    im = rgba(h, w)
    rng = np.random.RandomState(seed)
    for i in range(w):
        ht = int(h * (0.55 + 0.45 * rng.rand()))
        col = HUNT['grass'] if rng.rand() > 0.4 else (HUNT['grass_d'] if rng.rand() > 0.5 else HUNT['grass_l'])
        sway = int(1.5 * math.sin(i * 0.8 + seed))
        for t in range(ht):
            xx = clamp(i + (1 if t > ht * 0.6 else 0) + sway, 0, w - 1)
            yy = h - 1 - t
            im[yy, xx] = (*col, 255)
            if t > ht - 5 and rng.rand() < 0.3:
                pset(im, xx, yy, HUNT['grass_y'])
    return harden_alpha(im)

def tex_reed(w=8, h=48):
    im = rgba(h, w)
    for y in range(h):
        x = 3 + int(1.5 * math.sin(y * 0.2))
        col = HUNT['straw'] if y < h * 0.25 else (HUNT['grass_d'] if y % 3 == 0 else HUNT['grass'])
        pset(im, x, y, col); pset(im, x + 1, y, HUNT['straw'] if y < 8 else HUNT['grass_l'])
    fill_ellipse(im, 4, 5, 3, 5, PAL['egg_dark'])
    fill_ellipse(im, 4, 5, 2, 4, PAL['egg_shade'])
    return harden_alpha(im)

def tex_flower(col, w=16, h=24):
    im = rgba(h, w)
    for y in range(8, h):
        pset(im, 8, y, PAL['leaf_d']); pset(im, 7, y, PAL['leaf'])
    fill_ellipse(im, 5, 16, 4, 2, PAL['leaf']); fill_ellipse(im, 12, 14, 3, 2, PAL['leaf'])
    disc(im, 8, 6, 5, col)
    disc(im, 8, 6, 2, V3['goldhi'])
    return harden_alpha(im)

def tex_rock(w=24, h=16, seed=1):
    im = rgba(h, w)
    rng = np.random.RandomState(seed)
    cx, cy, rx, ry = w // 2, h // 2 + 1, w // 2 - 1, h // 2 - 1
    fill_ellipse(im, cx, cy, rx, ry, HUNT['stone'])
    fill_ellipse(im, cx - 2, cy - 1, rx - 4, ry - 3, HUNT['stone_l'])
    for _ in range(8):
        x, y = rng.randint(2, w - 2), rng.randint(2, h - 2)
        if im[y, x, 3]:
            pset(im, x, y, HUNT['stone_d'] if rng.rand() < 0.5 else HUNT['stone_l'])
    fill_ellipse(im, cx + 3, cy - 2, 3, 2, HUNT['moss'])
    return harden_alpha(im)

def tex_bush(w=32, h=28, seed=4):
    im = rgba(h, w)
    for cx, cy, r, c in ((10, 16, 10, HUNT['grass_d']), (20, 14, 11, HUNT['grass']),
                         (16, 18, 9, HUNT['moss']), (8, 20, 7, HUNT['grass_d'])):
        fill_ellipse(im, cx, cy, r, int(r * 0.85), c)
    pset(im, 12, 10, V3['rose']); pset(im, 22, 8, V3['gold']); pset(im, 16, 12, V3['violet'])
    return harden_alpha(im)

def tex_knoll(w=64, h=32):
    im = rgba(h, w)
    fill_ellipse(im, 32, 22, 30, 14, HUNT['grass_d'])
    fill_ellipse(im, 32, 20, 26, 12, HUNT['grass'])
    fill_ellipse(im, 28, 16, 14, 8, HUNT['moss_l'])
    fill_ellipse(im, 44, 22, 6, 4, HUNT['stone'])
    return harden_alpha(im)

def tex_log(w=40, h=12):
    im = rgba(h, w)
    fill_ellipse(im, 20, 6, 19, 5, HUNT['wood_d'])
    fill_ellipse(im, 20, 6, 17, 4, HUNT['wood'])
    fill_ellipse(im, 20, 5, 10, 2, HUNT['wood_l'])
    fill_ellipse(im, 3, 6, 3, 4, HUNT['wood_d'])
    fill_ellipse(im, 3, 6, 2, 3, HUNT['path'])
    pset(im, 28, 3, HUNT['moss']); pset(im, 16, 2, HUNT['moss_l'])
    return harden_alpha(im)

def tex_wood(w=32, h=32, seed=3):
    """直紋木紋（盒面用），Bayer 色階，冇斜線重複。"""
    im = rgba(h, w)
    n1 = pnoise(max(w, h), 8, seed)[:h, :w]
    n2 = pnoise(max(w, h), 16, seed + 1)[:h, :w]
    # 直紋（沿 Y）
    xs = (np.arange(w)[None, :] + n1 * 3)
    f = np.clip(0.45 + 0.2 * np.sin(xs * 0.9) + 0.25 * (n2 - .5), 0, 1)
    mput(im[..., :3], np.ones((h, w), bool), 'WOOD', f, .4)
    im[..., 3] = 255
    return harden_alpha(im)

def tex_sign_board(w=32, h=64):
    """木牌：柱＋木板＋簡單葉紋（POT 32×64）。"""
    im = rgba(h, w)
    # 柱
    fill_rect(im, 14, 20, 18, 64, HUNT['wood_d'])
    fill_rect(im, 15, 20, 17, 64, HUNT['wood'])
    # 板
    fill_rect(im, 4, 8, 28, 28, HUNT['wood_d'])
    fill_rect(im, 5, 9, 27, 27, HUNT['wood'])
    fill_rect(im, 6, 10, 26, 26, HUNT['wood_l'])
    # 葉標
    fill_ellipse(im, 16, 18, 6, 5, HUNT['grass_d'])
    fill_ellipse(im, 16, 17, 4, 3, HUNT['grass_l'])
    pset(im, 16, 18, HUNT['wood_d'])
    # 橫樑釘
    pset(im, 8, 11, HUNT['stone']); pset(im, 24, 11, HUNT['stone'])
    return harden_alpha(im)

def tex_tree(w=64, h=64, seed=22):
    """遠景樹林剪影（深葉簇＋細幹）。"""
    rng = np.random.default_rng(seed)
    rgb = np.zeros((h, w, 3), np.uint8)
    Y, X = np.mgrid[0:h, 0:w].astype(float)
    shape = np.zeros((h, w), bool)
    x = rng.uniform(6, 12)
    while x < w - 6:
        r = rng.uniform(9, 14)
        top = rng.uniform(2, h * 0.28) + r * 0.4
        cy = top
        shape |= ((X + .5 - x) / r) ** 2 + ((Y + .5 - cy) / (r * 1.15)) ** 2 <= 1
        # 冠下填充
        shape |= (np.abs(X + .5 - x) < r * 0.95) & (Y >= cy) & (Y < cy + r * 0.8)
        # 幹
        tw = max(1.2, r * 0.16)
        shape |= (np.abs(X + .5 - x) < tw) & (Y >= cy) & (Y < h - 1)
        x += r * rng.uniform(1.05, 1.45)
    n = pnoise(max(w, h), 10, seed)[:h, :w]
    mput(rgb, shape, 'LEAF', np.clip(.08 + .45 * (1 - Y / h) + .3 * (n - .5), 0, 1), .5)
    mput(rgb, shape & (rng.random((h, w)) < .03) & (Y < h * .5), 'LEAF', .7, 0)
    # 幹加深
    trunk = shape & (Y > h * 0.55) & (np.abs(X - w / 2) < w * 0.4)
    # 只把窄柱部分漆成木色：用 LEAF 深色已夠剪影；加少少幹
    im = np.zeros((h, w, 4), np.uint8)
    im[..., :3] = rgb
    im[..., 3] = np.where(shape, 255, 0)
    return harden_alpha(im)

def tex_sky(w=512, h=128):
    """H1 晨光：上藍下暖桃，軟雲。闊板覆蓋 ±10° 擺鏡。"""
    im = rgba(h, w)
    for y in range(h):
        t = y / max(h - 1, 1)
        # 上 2/3 藍→淺，近地平線轉桃
        if t < 0.62:
            tt = t / 0.62
            a, b = HUNT['sky_t'], (200, 214, 220)
            col = tuple(int(a[i] * (1 - tt) + b[i] * tt) for i in range(3))
        else:
            tt = (t - 0.62) / 0.38
            a, b = (200, 214, 220), HUNT['sky_b']
            col = tuple(int(a[i] * (1 - tt) + b[i] * tt) for i in range(3))
        im[y, :, :3] = col
        im[y, :, 3] = 255
    # 軟雲（量化塊，暖白）
    for cx, cy, r in ((80, 36, 22), (110, 30, 16), (240, 28, 26), (280, 34, 14),
                      (400, 40, 20), (430, 32, 12), (160, 48, 10)):
        fill_ellipse(im, cx, cy, r, r // 2 + 3, (255, 244, 230))
        fill_ellipse(im, cx + 6, cy + 2, r - 4, r // 2, (255, 236, 210))
    return harden_alpha(im)

def tex_hills(w=512, h=56):
    """遠丘＋矮樹剪影（同 H1 矮：脊線低，上沿大量透明，等天空漸層入 600×400 裁切）。"""
    im = rgba(h, w)
    # 三層由遠到近；脊線主要喺下半（約 20–40px），高峰偶發伸到頂。
    layers = (
        (28, (40, 52, 32), 8, 0.2, 0.016),
        (34, (51, 69, 31), 6, 1.3, 0.026),
        (40, (62, 78, 42), 5, 2.1, 0.038),
    )
    for base, col, amp, ph, freq in layers:
        for x in range(w):
            y0 = int(base - amp * math.sin(x * freq + ph) - 3 * math.sin(x * freq * 0.35 + ph * 2)
                     - 2 * math.sin(x * 0.09 + ph))
            bump = int(6 * max(0, math.sin(x * 0.065 + ph * 1.7)) ** 2)
            y0 -= bump
            for y in range(max(0, y0), h):
                im[y, x] = (*col, 255)
    return harden_alpha(im)

def mesh_cross_card(mid, tex, w_u, h_u, depth_card=True):
    mb = GM.MB(mid)
    ti = mb.add_tex(tex)
    hw, hh = w_u / 2, h_u
    n_f = (0, 0.55, 0.83)
    mb.card((-hw, 0, 0), (w_u, 0, 0), (0, hh, 0), ti, None, n_f)
    if depth_card:
        n_s = (0.45, 0.5, 0.74)
        mb.card((0, 0, hw), (0, 0, -w_u), (0, hh, 0), ti, None, n_s)
    return mb

def mesh_front_card(mid, tex, w_u, h_u):
    mb = GM.MB(mid)
    ti = mb.add_tex(tex)
    hw, hh = w_u / 2, h_u
    mb.card((-hw, 0, 0), (w_u, 0, 0), (0, hh, 0), ti, None, (0, 0.4, 0.92))
    return mb

def mesh_extrude_tex(mid, tex, depth, px0=None, py0=None):
    mb = GM.MB(mid)
    h, w = tex.shape[:2]
    px0 = w / 2 if px0 is None else px0
    py0 = h if py0 is None else py0
    mask = tex[..., 3] > 127
    mb.extrude(tex, mask, depth, px0, py0, zc=0.0, min_run=1)
    return mb

def local_fp_rect(x0, x1, z0, z1, pad=0):
    return dict(rect=dict(x=[x0, x1], z=[z0, z1]), pad=pad)

def world_fp_rect(x, z, lx0, lx1, lz0, lz1, pad=0):
    return dict(type='rect', x=[round(x + lx0, 2), round(x + lx1, 2)],
                z=[round(z + lz0, 2), round(z + lz1, 2)], pad=pad)

def mesh_arch():
    """清楚嘅木拱門：兩柱＋橫梁（盒），放中遠景當入口標。"""
    mb = GM.MB('arch')
    wood = tex_wood(32, 32, 4)
    ti = mb.add_tex(wood)
    # 柱 8×52×8，相距約 36
    mb.box(-22, -14, 0, 52, -4, 4, dict(all=ti), bottom=False)
    mb.box(14, 22, 0, 52, -4, 4, dict(all=ti), bottom=False)
    # 橫梁
    mb.box(-24, 24, 46, 54, -5, 5, dict(all=ti), bottom=False)
    # 小掛牌
    board = tex_sign_board()[8:28, 4:28]
    # pad to 32x32 for POT if used as tex; use wood already
    # 加一塊薄板做門楣裝飾
    mb.box(-10, 10, 38, 46, -2, 2, dict(all=ti), bottom=False)
    return mb

def mesh_sign():
    mb = GM.MB('sign')
    tex = tex_sign_board()
    # 擠出木牌（清晰道具）
    h, w = tex.shape[:2]
    mb.extrude(tex, tex[..., 3] > 127, 6, w / 2, h, zc=0.0, min_run=1)
    return mb, tex

def build(out_root):
    src = os.path.join(out_root, 'art-pet/scenes/hunt3d/prairie')
    os.makedirs(f'{src}/meshes', exist_ok=True)
    os.makedirs(f'{src}/ground', exist_ok=True)
    os.makedirs(f'{src}/backdrop', exist_ok=True)
    # 清走舊 mesh（避免入口石柱殘檔入 zip）
    for fn in os.listdir(f'{src}/meshes'):
        os.remove(f'{src}/meshes/{fn}')

    ground = paint_ground()
    tile = paint_tile()
    save_png(f'{src}/ground/ground.png', ground)
    save_png(f'{src}/ground/ground@3x.png', np.repeat(np.repeat(ground, 3, 0), 3, 1))
    save_png(f'{src}/ground/ground_tile.png', tile)
    save_png(f'{src}/ground/ground_tile@3x.png', np.repeat(np.repeat(tile, 3, 0), 3, 1))

    sky = tex_sky(); hills = tex_hills()
    save_png(f'{src}/backdrop/bg_sky.png', sky)
    save_png(f'{src}/backdrop/bg_sky@3x.png', np.repeat(np.repeat(sky, 3, 0), 3, 1))
    save_png(f'{src}/backdrop/bg_hills.png', hills)
    save_png(f'{src}/backdrop/bg_hills@3x.png', np.repeat(np.repeat(hills, 3, 0), 3, 1))

    meshes = {}
    def add_mesh(mb, zh, fp, cast=True, recv=True):
        MJ = GM.write(mb, src, 'meshes', zh, fp, cast, recv)
        meshes[mb.id] = MJ
        return MJ

    for i, seed in enumerate((0, 2, 5)):
        tex = tex_grass_card(seed, 24, 32)
        mb = mesh_cross_card(f'grass_{i}', tex, 24, 32)
        add_mesh(mb, f'草叢{i + 1}', local_fp_rect(-6, 6, -6, 6, pad=1), True, False)

    # 前景遮擋用高草
    tex_t = tex_grass_card(9, 32, 48)
    mb = mesh_cross_card('grass_tall', tex_t, 32, 48)
    add_mesh(mb, '高草叢', local_fp_rect(-8, 8, -8, 8, pad=1), True, False)

    tex_r = tex_reed()
    mb = mesh_cross_card('reed', tex_r, 8, 48, True)
    add_mesh(mb, '蘆葦', local_fp_rect(-2, 2, -2, 2, pad=1), True, False)

    for name, col in (('flower_rose', V3['rose']), ('flower_gold', V3['gold'])):
        mb = mesh_cross_card(name, tex_flower(col), 16, 24, True)
        add_mesh(mb, '野花', local_fp_rect(-3, 3, -3, 3, pad=1), True, False)

    for i, seed in enumerate((1, 7)):
        tex = tex_rock(24 if i == 0 else 32, 16 if i == 0 else 20, seed)
        mb = mesh_extrude_tex(f'rock_{i}', tex, depth=10 if i == 0 else 14)
        h, w = tex.shape[:2]
        add_mesh(mb, '石', local_fp_rect(-w / 2, w / 2, -6, 6, pad=1), True, True)

    mb = mesh_cross_card('bush', tex_bush(), 32, 28, True)
    add_mesh(mb, '採集灌木', local_fp_rect(-10, 10, -8, 8, pad=2), True, False)

    kn = tex_knoll()
    mb = GM.MB('knoll')
    ti = mb.add_tex(kn)
    mb.card((-32, 0, 6), (64, 0, 0), (0, 32, 0), ti, None, (0, 0.55, 0.83))
    soil = rgba(16, 32)
    soil[..., :3] = HUNT['grass_d']; soil[..., 3] = 255
    tj = mb.add_tex(soil)
    mb.box(-28, 28, 0, 10, -16, 16, dict(all=tj), bottom=False)
    add_mesh(mb, '苔丘', local_fp_rect(-28, 28, -16, 16, pad=2), True, True)

    mb = mesh_arch()
    add_mesh(mb, '木拱門', local_fp_rect(-24, 24, -5, 5, pad=2), True, True)

    mb, _ = mesh_sign()
    add_mesh(mb, '木牌', local_fp_rect(-8, 8, -3, 3, pad=1), True, True)

    mb = mesh_extrude_tex('log', tex_log(), depth=8)
    add_mesh(mb, '枯木', local_fp_rect(-20, 20, -4, 4, pad=1), True, True)

    for i, seed in enumerate((22, 28)):
        tex = tex_tree(64, 64, seed)
        mb = mesh_front_card(f'tree_{i}', tex, 64, 64)
        add_mesh(mb, '遠樹林剪影', local_fp_rect(-16, 16, -4, 4, pad=0), cast=False, recv=False)

    placements = []
    def place(oid, x, z, yaw=0, layer='mid', **kw):
        MJ = meshes[oid]
        fp_l = MJ.get('footprint')
        fp = None
        if fp_l and 'rect' in fp_l:
            r = fp_l['rect']
            fp = world_fp_rect(x, z, r['x'][0], r['x'][1], r['z'][0], r['z'][1], fp_l.get('pad', 0))
        o = dict(id=f'{oid}_{len(placements)}', type='mesh', zh=MJ['zh'], mesh=f'meshes/{oid}.json',
                 glb=f'meshes/{oid}.glb', x=x, z=z, y=0, yawDeg=yaw,
                 castShadow=MJ['castShadow'], receiveShadow=MJ['receiveShadow'],
                 layer=layer, triangles=MJ['triangleCount'])
        if fp: o['footprint'] = fp
        o.update(kw)
        placements.append(o)
        return o

    # —— 構圖（H1 密度）：前景遮擋（兩側）／中景小怪＋果叢／遠景丘＋樹林＋拱門 ——
    # 前景兩側（+Z，近鏡；避開寵物 x≈0）
    place('grass_tall', -88, 68, layer='near')
    place('grass_tall', -72, 50, layer='near')
    place('bush', -96, 44, layer='near')
    place('grass_0', -60, 42, layer='near')
    place('grass_tall', 90, 62, layer='near')
    place('bush', 102, 48, layer='near')
    place('grass_1', 74, 40, layer='near')
    place('log', 82, 28, layer='near')
    place('reed', 110, 36, layer='near')
    place('reed', 118, 22, layer='near')

    # 中景草／花／石／灌木（小怪＋果附近）
    for x, z, g in ((-28, 22, 'grass_0'), (30, 22, 'grass_1'),
                    (-22, -32, 'grass_1'), (22, -40, 'grass_2'),
                    (-62, -48, 'grass_0'), (68, -56, 'grass_1'), (-14, -58, 'grass_2'),
                    (14, -72, 'grass_0'), (-78, 14, 'grass_1'), (80, -24, 'grass_2'),
                    (-24, -88, 'grass_0'), (24, -96, 'grass_1'), (0, -130, 'grass_2')):
        place(g, x, z, layer='near' if z > 16 else 'mid')
    for x, z, f in ((-34, 8, 'flower_rose'), (26, -8, 'flower_gold'),
                    (-18, -40, 'flower_rose'), (12, 16, 'flower_gold'),
                    (48, -64, 'flower_rose'), (-42, -22, 'flower_gold'),
                    (36, 6, 'flower_rose')):
        place(f, x, z)
    place('rock_0', -48, -28)
    place('rock_1', 44, -58)
    place('rock_0', -16, -80, layer='far')
    # 採集灌木（中景，唔擋寵物）
    place('bush', -36, -28)
    place('bush', 28, -52)
    place('bush', 8, -18)
    place('bush', -54, -68)
    # 蘆葦右中
    for x, z in ((88, -36), (96, -48), (84, -58), (104, -28), (92, -70)):
        place('reed', x, z, layer='mid')

    # 遠：苔丘（左）＋木拱門（右後，唔擋寵物）＋木牌（路旁）
    place('knoll', -78, -108, layer='far')
    place('arch', 70, -122, layer='far')
    place('sign', -52, -74, layer='mid')

    # 遠樹林剪影：兩側成叢，中央留空俾遠丘＋天空漸層入畫（同 H1 屋／樹唔封死地平線）
    place('tree_0', -140, -200, layer='far')
    place('tree_1', -100, -228, layer='far')
    place('tree_0', -176, -236, layer='far')
    place('tree_1', 140, -206, layer='far')
    place('tree_0', 96, -232, layer='far')
    place('tree_1', 168, -224, layer='far')
    place('bush', -148, -184, layer='far')
    place('bush', 118, -190, layer='far')

    ao1, ao3 = paint_ao(placements)
    save_png(f'{src}/ground/ground_ao.png', ao1)
    save_png(f'{src}/ground/ground_ao@3x.png', ao3)

    # 小怪／果擺位：中景、對齊 S/M/L 體積（32／32／32／48），同寵物 (0,0) L=64 對讀
    critter_spawn = [
        dict(id='dewlet', x=-58, z=8, near='bush', zh='露珠偶'),
        dict(id='loambun', x=66, z=-18, near='bush', zh='泥包包'),
        dict(id='seedfluff', x=50, z=10, near='flower', zh='穗綿'),
        dict(id='mossback', x=-78, z=-100, big=True, near='knoll', zh='苔丘'),
    ]
    fruit_spawn = [
        dict(id='starberry', x=-26, z=14),
        dict(id='dewpear', x=-50, z=-10),
        dict(id='goldgrain', x=22, z=16),
        dict(id='sunkaki', x=44, z=-14),
        dict(id='mistgrape', x=6, z=6),
        dict(id='moonplum', x=-60, z=-88),
    ]

    objects = dict(
        format='hunt3d.scene/1',
        id='prairie', zh='草原 1 區',
        units='1 unit＝1x art px；Y 上；+Z 向鏡頭；原點＝隊伍出發位',
        objects=placements,
        backdrops=[
            dict(id='bg_sky', type='backdrop', zh='天空', file='backdrop/bg_sky.png',
                 file3x='backdrop/bg_sky@3x.png', z=-470, layer='far', fixed=True, unlit=True,
                 sizePx=[int(sky.shape[1]), int(sky.shape[0])],
                 unitsPerPx='(cz_cam−z)/dist，同花園 H1'),
            dict(id='bg_hills', type='backdrop', zh='遠丘＋遠樹剪影', file='backdrop/bg_hills.png',
                 file3x='backdrop/bg_hills@3x.png', z=-380, layer='far', fixed=True, unlit=True,
                 sizePx=[int(hills.shape[1]), int(hills.shape[0])]),
        ],
        pet=dict(x=0, z=0, face='cyl', billboard=True, radius=10,
                 dir4='sprites/tuanrong/motion/dir4/atlas_radiant_dir4.json',
                 huntClips='sprites/tuanrong/motion/hunt/clips.json',
                 shadow=True,
                 note='寵物係主要 billboard（小怪／果亦係 billboard）。pivot 對準 (x,0,z)。出發位原點，對齊 H1 鏡頭。'),
        critters=dict(billboard=True, atlasDir='sprites/hunt/critters/', spawn=critter_spawn),
        fruits=dict(billboard=True, atlas='sprites/hunt/fruits/atlas_fruits.png',
                    spawn=fruit_spawn,
                    note='場景預覽放咗示範果實；撥草或撲中後引擎可再生成。抱果行 clip 已烙入星莓。'),
        ground=dict(image='ground/ground.png', image3x='ground/ground@3x.png',
                    file='ground/ground.png', file3x='ground/ground@3x.png',
                    ao='ground/ground_ao.png', ao3x='ground/ground_ao@3x.png',
                    tile='ground/ground_tile.png', tile3x='ground/ground_tile@3x.png',
                    cover=[-128, 128, -128, 128], size=[256, 256], center=[0, 0],
                    outerTile=dict(file='ground/ground_tile.png', file3x='ground/ground_tile@3x.png', size=[64, 64],
                                   note='256 片外圍用：以 (−128,−128) 對齊每 64 units 平鋪，同 H1；外圍 ≥ x ±640、z −480…+320'),
                    tileExtent=dict(x=[-640, 640], z=[-480, 320]),
                    uv='u=(x+128)/256，v=(z+128)/256，圖頂＝z −128；@3x 取樣 texel 密度＝3／unit，同 H1',
                    lit=True),
    )
    json.dump(objects, open(f'{src}/objects.json', 'w'), ensure_ascii=False, indent=1)

    # 光：對齊 H1（sun 影 0.3、fill 唔投影、暖霧）
    sun_dir = np.array([0.4206, -0.721, 0.5507], float)
    sun_dir = sun_dir / np.linalg.norm(sun_dir)
    fill_dir = np.array([0.2005, -0.1203, -0.9723], float)
    fill_dir = fill_dir / np.linalg.norm(fill_dir)
    lights = dict(
        format='hunt3d.lights/1',
        lights=[],
        sun=dict(dir=[round(float(x), 4) for x in sun_dir], color='#ffe6b8', intensity=1.0,
                 ambient=dict(color='#cfe0f0', intensity=0.55), shadowIntensity=0.3,
                 note='同花園 H1：太陽喺左後上方；shadowIntensity 0.3 即時光影，唔烘入貼圖'),
        fill=dict(dir=[round(float(x), 4) for x in fill_dir], color='#ffe2c4', intensity=0.38,
                  intensityNight=0.0, note='唔投影；由鏡頭方向略低補光'),
        fog=dict(color='#ffe8c8', near=380, far=1200),
        night=dict(note='M1 lite 以日間為主；夜值預留', ambient=dict(color='#1a2438', intensity=0.28)),
    )
    json.dump(lights, open(f'{src}/lights.json', 'w'), ensure_ascii=False, indent=1)

    camera = dict(
        format='hunt3d.camera/1',
        target=[0, 30, -72],
        pitchDeg=30, dist=580, fovDeg=40,
        orbitMinDeg=-10, orbitMaxDeg=10,
        swayAmplitudeDeg=5, swayHalfPeriodSec=6, swayEasing='easeInOutSine',
        followDamping=2.0, followWeight=[0.25, 0.3], followOffset=[-20, 0], followOrigin=[0, 0],
        note='同花園 H1 穩陣鏡頭：pitch 30°、dist 580、target [0,30,-72]（寵物落畫面下半）、±5° 緩入緩出、阻尼跟拍；玩家手拖仍 ±10°。預覽 600×844 再裁 (0,190,600,590)＝600×400。',
        godot='pitch 30°、fov 40 垂直；如果 import_scale=0.01，將 dist／target／fog 全部 ×0.01。',
    )
    json.dump(camera, open(f'{src}/camera.json', 'w'), ensure_ascii=False, indent=1)

    summary = dict(meshCount=len(meshes), instanceCount=len(placements),
                   trianglesUnique=sum(m['triangleCount'] for m in meshes.values()),
                   trianglesInstanced=sum(o['triangles'] for o in placements),
                   meshes={k: dict(triangles=v['triangleCount'], textureSize=v['textureSize']) for k, v in meshes.items()})
    json.dump(summary, open(f'{src}/meshes_index.json', 'w'), ensure_ascii=False, indent=1)
    return src, objects, lights, camera, meshes, placements

if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else '/workspace/m1-icons-hunt-src'
    build(root)
    print('hunt3d ok')
