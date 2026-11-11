#!/usr/bin/env python3
"""m1_common.py — 《微光小圃》M1 icon／狩獵共用：色盤、像素繪製、法線、圖集、縮放。Pillow／numpy 程序化，冇 AI 圖。"""
import os, json, math, hashlib
import numpy as np
from PIL import Image

# ----- V3-A UI 色（ui_hd2d_v3_lib.C）-----
V3 = dict(
    ink=(36, 34, 52), cream=(250, 244, 230), mute=(206, 212, 230),
    gold=(232, 200, 128), goldhi=(255, 236, 184), golddk=(66, 40, 4),
    navy=(18, 24, 48), navy2=(30, 40, 74), navy3=(44, 58, 104),
    amber=(246, 176, 72), sky=(110, 190, 230), rose=(240, 126, 150),
    violet=(156, 132, 230), mint=(120, 206, 160), red=(214, 62, 72),
    dis=(84, 88, 108),
)
# 團絨 31 色盤
PAL = dict(
    outline=(59, 42, 62), cream0=(214, 154, 102), cream1=(233, 190, 132),
    cream2=(246, 221, 176), cream3=(255, 239, 196), cream4=(255, 248, 224),
    peach0=(232, 160, 116), peach1=(245, 191, 147), peach2=(251, 216, 180),
    orange=(242, 166, 90), orange_d=(224, 127, 69), orange_dd=(184, 100, 63),
    glow_core=(255, 251, 208), glow_mid=(255, 233, 138), glow=(255, 212, 94),
    glow_warm=(255, 138, 61), egg_shade=(242, 185, 60), egg_dark=(217, 143, 46),
    blush=(242, 139, 155), blush_d=(217, 102, 122), berry=(229, 88, 77),
    berry_d=(163, 63, 74), leaf=(107, 191, 106), leaf_d=(58, 125, 78),
    zzz=(143, 133, 194), white=(243, 238, 250), cyan=(127, 240, 224),
    drop=(127, 196, 232), drop_d=(79, 163, 217), sick0=(163, 176, 140),
    sick1=(201, 214, 176),
)
# 狩獵場景延伸色（原創造型用，唔抄 Chiikawa 配色組合）
HUNT = dict(
    soil=(143, 86, 47), soil_d=(55, 26, 20), soil_l=(222, 180, 116),
    grass=(103, 129, 53), grass_l=(150, 184, 70), grass_d=(57, 74, 38),
    grass_y=(174, 192, 76), straw=(186, 166, 90),
    moss=(68, 78, 41), moss_l=(137, 175, 62), moss_d=(35, 58, 26),
    stone=(92, 72, 69), stone_l=(181, 148, 117), stone_d=(55, 26, 20),
    dew=(180, 230, 210), dew_d=(90, 170, 160),
    bun=(176, 118, 74), bun_l=(214, 160, 104), bun_d=(128, 78, 48),
    fluff=(236, 220, 186), fluff_d=(198, 174, 132), wing=(186, 206, 150),
    plum=(150, 110, 168), plum_l=(190, 150, 200), plum_d=(98, 70, 120),
    grape=(96, 122, 168), grape_l=(130, 154, 196), grape_d=(62, 82, 120),
    copper=(184, 116, 58), copper_l=(220, 164, 92), copper_d=(128, 74, 36),
    copper_hi=(240, 206, 140),
    sky_t=(135, 189, 224), sky_b=(255, 224, 156),
    hill=(62, 78, 42), hill_d=(40, 52, 32),
    hill_l=(78, 98, 50),
    path=(222, 180, 116), path_d=(143, 86, 47),
    wood=(143, 86, 47), wood_l=(222, 180, 116), wood_d=(55, 26, 20), wood_m=(176, 126, 72),
)

def rgba(h, w=None):
    if w is None: w = h
    return np.zeros((h, w, 4), np.uint8)

def clamp(v, a, b): return a if v < a else b if v > b else v

def pset(im, x, y, col, a=255):
    h, w = im.shape[:2]
    if 0 <= x < w and 0 <= y < h:
        c = col if len(col) == 4 else (col[0], col[1], col[2], a)
        im[y, x] = c

def blend(im, x, y, col, a=255):
    """UI／光影層先用；sprite 最終會量化成 0/255。"""
    h, w = im.shape[:2]
    if not (0 <= x < w and 0 <= y < h): return
    src = np.array(col[:3] + (a,), np.float32)
    dst = im[y, x].astype(np.float32)
    t = src[3] / 255.0
    out = dst * (1 - t) + src * t
    out[3] = min(255, dst[3] + src[3] * (1 - dst[3] / 255.0))
    im[y, x] = np.clip(out, 0, 255).astype(np.uint8)

def fill_rect(im, x0, y0, x1, y1, col, a=255):
    h, w = im.shape[:2]
    xa, xb = clamp(int(min(x0, x1)), 0, w), clamp(int(max(x0, x1)), 0, w)
    ya, yb = clamp(int(min(y0, y1)), 0, h), clamp(int(max(y0, y1)), 0, h)
    c = col if len(col) == 4 else (col[0], col[1], col[2], a)
    im[ya:yb, xa:xb] = c

def fill_ellipse(im, cx, cy, rx, ry, col, a=255):
    h, w = im.shape[:2]
    c = col if len(col) == 4 else (col[0], col[1], col[2], a)
    xs = range(max(0, int(cx - rx) - 1), min(w, int(cx + rx) + 2))
    ys = range(max(0, int(cy - ry) - 1), min(h, int(cy + ry) + 2))
    rx2, ry2 = max(rx, 0.5) ** 2, max(ry, 0.5) ** 2
    for y in ys:
        for x in xs:
            if (x + 0.5 - cx) ** 2 / rx2 + (y + 0.5 - cy) ** 2 / ry2 <= 1.0:
                im[y, x] = c

def ring_ellipse(im, cx, cy, rx, ry, col, t=1, a=255):
    """描邊：外橢圓減內橢圓。"""
    tmp = rgba(*im.shape[:2])
    fill_ellipse(tmp, cx, cy, rx, ry, col, a)
    if rx - t > 0 and ry - t > 0:
        fill_ellipse(tmp, cx, cy, rx - t, ry - t, (0, 0, 0, 0), 0)
        # punch only where we just filled — restore already-drawn interior later via mask
    m = tmp[..., 3] > 0
    im[m] = tmp[m]


def outline_sel(im, col=(48, 28, 56), only_touch=True):
    """V3 sel-out：貼住透明位嘅深色外框。sprite 用。"""
    a = im[..., 3] > 127
    if not a.any():
        return im
    h, w = a.shape
    P = np.pad(a, 1)
    edge = a & ~(P[1:-1, 1:-1] & P[:-2, 1:-1] & P[2:, 1:-1] & P[1:-1, :-2] & P[1:-1, 2:])
    # 只改貼邊嘅現有像素（唔加一圈新像素，避免脹大）
    im[edge, :3] = col
    im[edge, 3] = 255
    return im


def harden_alpha(im, ui=False):
    """sprite：alpha 只有 0/255，透明 RGB=0。UI 光影層可保留真 alpha。"""
    out = im.copy()
    if not ui:
        m = out[..., 3] > 127
        out[..., 3] = np.where(m, 255, 0)
        out[~m, :3] = 0
    else:
        out[out[..., 3] == 0, :3] = 0
    return out


def glints(im, pts, col=(255, 248, 224)):
    for x, y in pts:
        pset(im, x, y, col, 255)
    return im


def nearest_scale(im, s):
    """整數倍 nearest。"""
    return np.repeat(np.repeat(im, s, 0), s, 1)


def scale_to(im, tw, th):
    """像素縮放：整數倍用 nearest；否則經整數倍再箱平均，量化回原色。"""
    h, w = im.shape[:2]
    if (w, h) == (tw, th):
        return im.copy()
    if tw % w == 0 and th % h == 0 and tw // w == th // h:
        return nearest_scale(im, tw // w)
    # 上採樣到 lcm 附近再平均
    up = 4
    big = nearest_scale(im, up)
    bh, bw = big.shape[:2]
    out = rgba(th, tw)
    for y in range(th):
        y0, y1 = int(y * bh / th), max(int((y + 1) * bh / th), int(y * bh / th) + 1)
        for x in range(tw):
            x0, x1 = int(x * bw / tw), max(int((x + 1) * bw / tw), int(x * bw / tw) + 1)
            tile = big[y0:y1, x0:x1]
            if tile.size == 0:
                continue
            # 多數票（含透明）：優先不透明
            flat = tile.reshape(-1, 4)
            op = flat[flat[:, 3] > 127]
            if len(op) * 2 < len(flat):
                continue
            # 最常見色
            u, c = np.unique(op, axis=0, return_counts=True)
            out[y, x] = u[c.argmax()]
    return harden_alpha(out)


def shift(im, dx=0, dy=0, fill=None):
    out = np.zeros_like(im)
    if fill is not None:
        out[...] = fill
    elif im.shape[2] == 4:
        # normal-map 背景稍後再處理
        pass
    h, w = im.shape[:2]
    ys, ye = max(0, dy), min(h, h + dy)
    xs, xe = max(0, dx), min(w, w + dx)
    ss_y, ss_x = ys - dy, xs - dx
    se_y, se_x = ss_y + (ye - ys), ss_x + (xe - xs)
    if ye > ys and xe > xs:
        out[ys:ye, xs:xe] = im[ss_y:se_y, ss_x:se_x]
    return out


def blit(dst, src, x, y, flip=False):
    s = src[:, ::-1].copy() if flip else src
    h, w = s.shape[:2]
    H, W = dst.shape[:2]
    x0, y0 = int(x), int(y)
    sx0 = 0 if x0 >= 0 else -x0
    sy0 = 0 if y0 >= 0 else -y0
    sx1 = w if x0 + w <= W else W - x0
    sy1 = h if y0 + h <= H else H - y0
    if sx1 <= sx0 or sy1 <= sy0:
        return dst
    patch = s[sy0:sy1, sx0:sx1]
    m = patch[..., 3] > 127
    region = dst[y0 + sy0:y0 + sy1, x0 + sx0:x0 + sx1]
    region[m] = patch[m]
    return dst


def pack_atlas(frames, names, cell=None, pad=2, cols=None, bg_n=False):
    """frames: list of HxWx4。回 (atlas, json_frames, W, H)。"""
    assert len(frames) == len(names)
    fh, fw = frames[0].shape[:2]
    for f in frames:
        assert f.shape[0] == fh and f.shape[1] == fw
    cell_w, cell_h = fw + 2 * pad, fh + 2 * pad
    n = len(frames)
    if cols is None:
        # 盡量 1024 寬
        cols = min(n, max(1, 1024 // cell_w))
    rows = (n + cols - 1) // cols
    W = 1 << int(math.ceil(math.log2(max(cell_w * cols, 16))))
    H = 1 << int(math.ceil(math.log2(max(cell_h * rows, 16))))
    atlas = rgba(H, W)
    if bg_n:
        atlas[..., :3] = (128, 128, 255)
    J = {}
    for i, (nm, fr) in enumerate(zip(names, frames)):
        x = (i % cols) * cell_w + pad
        y = (i // cols) * cell_h + pad
        atlas[y:y + fh, x:x + fw] = fr
        # 1px extrude
        if pad >= 1:
            atlas[y - 1, x:x + fw] = fr[0]
            atlas[y + fh, x:x + fw] = fr[-1]
            atlas[y:y + fh, x - 1] = fr[:, 0]
            atlas[y:y + fh, x + fw] = fr[:, -1]
        J[nm] = {'frame': {'x': x, 'y': y, 'w': fw, 'h': fh}}
    return atlas, J, W, H


def normal_from_sprite(rgba_im, lum_w=0.18):
    """由 alpha＋亮度做 OpenGL（綠＝上）tangent-space 法線。透明 RGB=(128,128,255)，alpha 同色圖。"""
    try:
        from scipy.ndimage import distance_transform_edt, gaussian_filter
    except ImportError:
        distance_transform_edt = None
    a = (rgba_im[..., 3] > 127)
    h, w = a.shape
    out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = (128, 128, 255)
    if not a.any():
        return out
    up = 4
    A = np.repeat(np.repeat(a.astype(np.float32), up, 0), up, 1)
    if distance_transform_edt is not None:
        dist = distance_transform_edt(A)
        height = dist.astype(np.float32)  # 以 px 距離做高度，梯度約 O(1)
    else:
        height = A.copy()
        k = np.ones((7, 7), np.float32); k /= k.sum()
        from numpy.lib.stride_tricks import sliding_window_view
        P = np.pad(A, 3)
        sw = sliding_window_view(P, (7, 7))
        height = (sw * k).sum((-1, -2)) * 8.0
    lum = rgba_im[..., :3].astype(np.float32).mean(-1) / 255.0
    L = np.repeat(np.repeat(lum, up, 0), up, 1)
    height = height + lum_w * (L - 0.5) * (A > 0) * 4.0
    if distance_transform_edt is not None:
        height = gaussian_filter(height, 1.0)
    gy, gx = np.gradient(height)  # gy = d/drow（向下）
    nx = -gx
    # 專案慣例「綠＝上」：精靈頂部（頭）G 高、腳 G 低。
    # 距離場在頂邊 dH/drow>0（向內高度升），所以 ny = +gy。
    ny = gy
    nz = np.full_like(height, 2.2)
    n = np.stack([nx, ny, nz], -1)
    nlen = np.linalg.norm(n, axis=-1, keepdims=True) + 1e-8
    n = n / nlen
    # 4×4 平均返 1x
    hh, ww = h, w
    n1 = n.reshape(hh, up, ww, up, 3).mean((1, 3))
    rgb = np.clip(n1 * 0.5 + 0.5, 0, 1)
    out[..., 0] = (rgb[..., 0] * 255 + 0.5).astype(np.uint8)
    out[..., 1] = (rgb[..., 1] * 255 + 0.5).astype(np.uint8)
    out[..., 2] = (rgb[..., 2] * 255 + 0.5).astype(np.uint8)
    out[..., 3] = np.where(a, 255, 0)
    out[~a, :3] = (128, 128, 255)
    # 單位化微調（量化後再 normalize 一次，滿足 validator ±0.03）
    k = a
    v = out[..., :3].astype(np.float32) / 255.0 * 2 - 1
    vlen = np.linalg.norm(v, axis=-1, keepdims=True)
    vlen = np.maximum(vlen, 1e-6)
    v = v / vlen
    # 保證向外 B≥128 → z≥0
    v[..., 2] = np.maximum(v[..., 2], 0.02)
    vlen = np.linalg.norm(v, axis=-1, keepdims=True)
    v = v / np.maximum(vlen, 1e-6)
    rgb = np.clip(v * 0.5 + 0.5, 0, 1)
    out[k, 0] = (rgb[k, 0] * 255 + 0.5).astype(np.uint8)
    out[k, 1] = (rgb[k, 1] * 255 + 0.5).astype(np.uint8)
    out[k, 2] = (rgb[k, 2] * 255 + 0.5).astype(np.uint8)
    return out


def flip_normal_r(nimg):
    """左右鏡像之後：法線 R → 255−R。"""
    out = nimg[:, ::-1].copy()
    m = out[..., 3] > 0
    out[m, 0] = 255 - out[m, 0]
    return out


def save_png(path, im, optimize=True):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    Image.fromarray(im).save(path, optimize=optimize)


def sha1_12(path):
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 16), b''):
            h.update(chunk)
    return h.hexdigest()[:12]


def load_png(path):
    return np.array(Image.open(path).convert('RGBA'))


def find_radiant_frames():
    """搵現有 radiant 單幀或 atlas，供狩獵 clip 變形用。"""
    cands = [
        '/workspace/game-design/art-pet/sprites/tuanrong/motion/frames/radiant',
        '/workspace/glimmer-3d-h1/art-pet/sprites/tuanrong/motion/frames/radiant',
        os.path.abspath(os.path.join(os.path.dirname(__file__), '../sprites/tuanrong/motion/frames/radiant')),
    ]
    for d in cands:
        if os.path.isdir(d) and os.path.exists(os.path.join(d, 'idle_01.png')):
            return d
    # atlas fallback
    atlases = [
        '/workspace/game-design/art-pet/sprites/tuanrong/motion/atlas_radiant.png',
        '/workspace/glimmer-3d-h1/src/glimmer-a/art/atlas_radiant.png',
    ]
    for p in atlases:
        if os.path.exists(p) and os.path.exists(p.replace('.png', '.json')):
            return p
    return None


def frame_radiant(name, src=None):
    """讀 64×64 radiant 幀（idle_01、walk_01、play_01…）。"""
    src = src or find_radiant_frames()
    if src is None:
        raise FileNotFoundError('搵唔到 radiant 幀')
    if os.path.isdir(src):
        p = os.path.join(src, f'{name}.png')
        im = load_png(p)
        if im.shape[0] != 64 or im.shape[1] != 64:
            # 可能冇 pad；置中貼入 64
            c = rgba(64, 64)
            blit(c, im, (64 - im.shape[1]) // 2, 64 - im.shape[0])
            return harden_alpha(c)
        return harden_alpha(im)
    J = json.load(open(src.replace('.png', '.json')))
    atlas = load_png(src)
    fr = J['frames'][name]['frame']
    return harden_alpha(atlas[fr['y']:fr['y'] + fr['h'], fr['x']:fr['x'] + fr['w']].copy())


SIZES = {
    'S': dict(size=32, pivot=(16, 29), zh='細體（絨芽級 32px）'),
    'M': dict(size=48, pivot=(24, 45), zh='中體（長老 evo_still 級 48px）'),
    'L': dict(size=64, pivot=(32, 61), zh='大體（花園 radiant／dir4 級 64px）'),
}

# clip 表（§6 冇寫幀數；跟現有 CLIPS 語言：環境 6 幀 8fps、行 6 幀 10fps、歡呼 6 幀 10fps）
CLIPS = {
    'part_grass': dict(zh='撥草', frames=6, fps=8, loop=False, priority=3, interruptible=False),
    'pounce': dict(zh='撲', frames=6, fps=8, loop=False, priority=4, interruptible=False),
    'carry_fruit': dict(zh='抱果行', frames=6, fps=10, loop=True, priority=2, interruptible=True),
    'cheer': dict(zh='歡呼', frames=6, fps=10, loop=False, priority=6, interruptible=False),
}

CRITTERS = [
    dict(id='dewlet', zh='露珠偶', size=32, big=False, fruit='dewpear',
         note='薄荷色圓身、頭上一粒露珠；細隻'),
    dict(id='loambun', zh='泥包包', size=32, big=False, fruit='sunkaki',
         note='暖褐包子身、芝麻斑；細隻'),
    dict(id='seedfluff', zh='穗綿', size=32, big=False, fruit='goldgrain',
         note='奶油色綿子、兩片嫩翼；細隻'),
    dict(id='mossback', zh='苔丘', size=48, big=True, fruit='moonplum',
         note='苔蘚蓋住嘅矮石丘，大隻；溫柔唔惡'),
]
FRUITS = [
    dict(id='starberry', zh='星莓', col='rose'),
    dict(id='dewpear', zh='露梨', col='mint'),
    dict(id='goldgrain', zh='金穗果', col='amber'),
    dict(id='moonplum', zh='月李', col='plum'),
    dict(id='sunkaki', zh='陽柿', col='orange'),
    dict(id='mistgrape', zh='霧葡', col='grape'),
]
