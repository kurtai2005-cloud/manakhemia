#!/usr/bin/env python3
"""build_hunt_sprites.py — 狩獵小怪 4（idle／驚／變果碌走）、果 6、銅證 4、寵物 clip×S/M/L。
程序化像素；寵物以現有 radiant 幀變形，連 _n（OpenGL 綠＝上）。全部原創，只借細細隻可愛氛圍。"""
import os, sys, json, math
import numpy as np
from PIL import Image
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from m1_common import (
    V3, PAL, HUNT, rgba, pset, fill_rect, fill_ellipse, outline_sel, harden_alpha,
    glints, blit, shift, save_png, pack_atlas, normal_from_sprite, scale_to,
    frame_radiant, find_radiant_frames, SIZES, CLIPS, CRITTERS, FRUITS,
)

def disc(im, cx, cy, r, col, a=255):
    fill_ellipse(im, cx, cy, r, r, col, a)

def finish_spr(im, ol=(59, 42, 62)):
    outline_sel(im, ol)
    return harden_alpha(im)

# ---------------- 果 6（32×32，pivot 16,28 接地）----------------
def fruit_starberry(im=None, cx=16, cy=20, s=1.0):
    im = im if im is not None else rgba(32)
    r = max(2, int(6 * s))
    disc(im, cx, cy, r, PAL['berry'])
    disc(im, cx - 1, cy - 1, max(1, r - 2), PAL['blush'])
    # 星
    pset(im, cx, cy - r + 1, V3['goldhi'])
    for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1), (-1, -1), (1, -1)):
        pset(im, cx + dx, cy + dy - 1, V3['gold'])
    pset(im, cx, cy - r - 1, PAL['leaf']); pset(im, cx + 1, cy - r, PAL['leaf_d'])
    return im

def fruit_dewpear(im=None, cx=16, cy=20, s=1.0):
    im = im if im is not None else rgba(32)
    fill_ellipse(im, cx, cy, int(5 * s) + 1, int(7 * s) + 1, HUNT['dew_d'])
    fill_ellipse(im, cx, cy, int(4 * s) + 1, int(6 * s) + 1, HUNT['dew'])
    fill_ellipse(im, cx - 1, cy - 2, 2, 3, PAL['cyan'])
    pset(im, cx, cy - int(7 * s) - 1, PAL['leaf_d'])
    pset(im, cx + 1, cy - int(7 * s), PAL['leaf'])
    pset(im, cx, cy - 1, PAL['white'])
    return im

def fruit_goldgrain(im=None, cx=16, cy=20, s=1.0):
    im = im if im is not None else rgba(32)
    # 三粒穀
    for i, (dx, dy) in enumerate(((-3, 1), (0, -2), (3, 1))):
        fill_ellipse(im, cx + dx, cy + dy, 3, 5, PAL['egg_dark'] if i else PAL['orange_d'])
        fill_ellipse(im, cx + dx, cy + dy - 1, 2, 3, PAL['glow'] if i == 1 else PAL['egg_shade'])
    pset(im, cx, cy - 8, PAL['leaf_d']); pset(im, cx + 1, cy - 7, PAL['leaf'])
    return im

def fruit_moonplum(im=None, cx=16, cy=20, s=1.0):
    im = im if im is not None else rgba(32)
    r = max(3, int(6 * s))
    disc(im, cx, cy, r, HUNT['plum_d'])
    disc(im, cx, cy, r - 1, HUNT['plum'])
    disc(im, cx - 1, cy - 1, r - 3, HUNT['plum_l'])
    # 月牙斑
    disc(im, cx + 1, cy, 3, HUNT['plum_l'])
    disc(im, cx + 2, cy - 1, 2, HUNT['plum'])
    pset(im, cx, cy - r - 1, PAL['leaf']); pset(im, cx - 1, cy - r, PAL['leaf_d'])
    return im

def fruit_sunkaki(im=None, cx=16, cy=20, s=1.0):
    im = im if im is not None else rgba(32)
    fill_ellipse(im, cx, cy, int(7 * s), int(6 * s), PAL['orange_dd'])
    fill_ellipse(im, cx, cy, int(6 * s), int(5 * s), PAL['orange'])
    fill_ellipse(im, cx - 1, cy - 1, 3, 2, PAL['glow'])
    # 蒂
    fill_rect(im, cx - 1, cy - int(6 * s) - 1, cx + 2, cy - int(5 * s) + 1, PAL['leaf_d'])
    pset(im, cx - 2, cy - int(6 * s), PAL['leaf']); pset(im, cx + 2, cy - int(6 * s), PAL['leaf'])
    return im

def fruit_mistgrape(im=None, cx=16, cy=20, s=1.0):
    im = im if im is not None else rgba(32)
    disc(im, cx - 3, cy - 1, 4, HUNT['grape_d']); disc(im, cx - 3, cy - 1, 3, HUNT['grape'])
    disc(im, cx + 3, cy - 1, 4, HUNT['grape_d']); disc(im, cx + 3, cy - 1, 3, HUNT['grape_l'])
    disc(im, cx, cy + 3, 4, HUNT['grape_d']); disc(im, cx, cy + 3, 3, HUNT['grape'])
    pset(im, cx - 4, cy - 2, PAL['drop']); pset(im, cx + 2, cy - 2, PAL['white'])
    pset(im, cx, cy - 6, PAL['leaf_d']); pset(im, cx + 1, cy - 5, PAL['leaf'])
    return im

FRUIT_DRAW = {
    'starberry': fruit_starberry, 'dewpear': fruit_dewpear, 'goldgrain': fruit_goldgrain,
    'moonplum': fruit_moonplum, 'sunkaki': fruit_sunkaki, 'mistgrape': fruit_mistgrape,
}

# ---------------- 小怪 ----------------
def _eyes(im, x, y, kind='idle'):
    if kind == 'idle':
        pset(im, x, y, PAL['outline']); pset(im, x + 5, y, PAL['outline'])
        pset(im, x + 1, y, PAL['white']); pset(im, x + 6, y, PAL['white'])
    elif kind == 'scared':
        # 圓眼
        pset(im, x - 1, y - 1, PAL['outline']); pset(im, x, y - 1, PAL['outline']); pset(im, x + 1, y - 1, PAL['outline'])
        pset(im, x - 1, y, PAL['outline']); pset(im, x, y, PAL['white']); pset(im, x + 1, y, PAL['outline'])
        pset(im, x + 4, y - 1, PAL['outline']); pset(im, x + 5, y - 1, PAL['outline']); pset(im, x + 6, y - 1, PAL['outline'])
        pset(im, x + 4, y, PAL['outline']); pset(im, x + 5, y, PAL['white']); pset(im, x + 6, y, PAL['outline'])
    else:
        pset(im, x, y, PAL['outline']); pset(im, x + 5, y, PAL['outline'])

def draw_dewlet(im, ox=16, oy=24, phase=0, kind='idle', silhouette=False):
    """薄荷圓身，頭頂隔 1px 掛一粒藍露珠（避免睇成藥瓶）。"""
    col_b = HUNT['moss'] if silhouette else HUNT['moss']
    col = (40, 40, 48) if silhouette else HUNT['moss_l']
    col_h = (40, 40, 48) if silhouette else PAL['cyan']
    bob = 0 if kind == 'scared' else (0, -1, 0, 1, 0, 0)[phase % 6]
    sc = 1 if kind == 'scared' else 0
    fill_ellipse(im, ox, oy + bob + sc, 8, 6 - sc, col_b)
    fill_ellipse(im, ox, oy + bob + sc, 7, 5 - sc, col)
    fill_ellipse(im, ox - 2, oy - 1 + bob, 3, 2, col_h)
    if not silhouette:
        _eyes(im, ox - 3, oy - 1 + bob + sc, 'scared' if kind == 'scared' else 'idle')
        fill_ellipse(im, ox - 3, oy + 2 + bob, 2, 1, PAL['blush'])
        fill_ellipse(im, ox + 2, oy + 2 + bob, 2, 1, PAL['blush'])
        pset(im, ox + 6, oy - 3 + bob, PAL['leaf'])
    # 露珠：同身體隔 1 行，藍色水珠
    dy = -10 + bob + (2 if kind == 'scared' else 0)
    dcol = (40, 40, 48) if silhouette else PAL['drop_d']
    disc(im, ox, oy + dy, 3, dcol)
    if not silhouette:
        disc(im, ox, oy + dy, 2, PAL['drop'])
        pset(im, ox - 1, oy + dy - 1, PAL['white'])
    return im

def draw_loambun(im, ox=16, oy=22, phase=0, kind='idle', silhouette=False):
    bob = 0 if kind == 'scared' else (0, 0, -1, 0, 0, 1)[phase % 6]
    sq = 1 if kind == 'scared' else 0
    c0 = (40, 40, 48) if silhouette else HUNT['bun_d']
    c1 = (40, 40, 48) if silhouette else HUNT['bun']
    c2 = (40, 40, 48) if silhouette else HUNT['bun_l']
    fill_ellipse(im, ox, oy + bob + sq, 8, 6 - sq, c0)
    fill_ellipse(im, ox, oy + bob + sq, 7, 5 - sq, c1)
    fill_ellipse(im, ox, oy - 2 + bob, 6, 4, c2)
    if not silhouette:
        # 芝麻
        for dx, dy in ((-3, 0), (2, -1), (0, 2), (4, 1), (-4, 2)):
            pset(im, ox + dx, oy + dy + bob, PAL['outline'])
        _eyes(im, ox - 3, oy - 1 + bob, 'scared' if kind == 'scared' else 'idle')
        fill_ellipse(im, ox, oy + 3 + bob, 2, 1, PAL['blush'])
    # 腳
    fill_ellipse(im, ox - 4, oy + 6 + bob, 2, 1, c0)
    fill_ellipse(im, ox + 4, oy + 6 + bob, 2, 1, c0)
    return im

def draw_seedfluff(im, ox=16, oy=22, phase=0, kind='idle', silhouette=False):
    bob = 0 if kind == 'scared' else (0, -1, -1, 0, 1, 0)[phase % 6]
    flap = (phase % 2) if kind != 'scared' else 0
    c0 = (40, 40, 48) if silhouette else HUNT['fluff_d']
    c1 = (40, 40, 48) if silhouette else HUNT['fluff']
    wcol = (40, 40, 48) if silhouette else HUNT['wing']
    # 翼
    wy = -1 - flap if kind != 'scared' else 1
    fill_ellipse(im, ox - 8, oy + wy + bob, 5, 3 + flap, wcol)
    fill_ellipse(im, ox + 8, oy + wy + bob, 5, 3 + flap, wcol)
    if kind == 'scared':
        fill_ellipse(im, ox, oy + 1, 5, 6, c0)  # 翼收
    fill_ellipse(im, ox, oy + bob, 6, 6, c0)
    fill_ellipse(im, ox, oy + bob, 5, 5, c1)
    if not silhouette:
        fill_ellipse(im, ox - 1, oy - 1 + bob, 2, 2, PAL['cream4'])
        _eyes(im, ox - 3, oy + bob, 'scared' if kind == 'scared' else 'idle')
        pset(im, ox, oy + 3 + bob, PAL['peach0'])
    # 頂上小穗
    pset(im, ox, oy - 7 + bob, PAL['egg_shade'] if not silhouette else (40, 40, 48))
    pset(im, ox - 1, oy - 6 + bob, PAL['egg_dark'] if not silhouette else (40, 40, 48))
    pset(im, ox + 1, oy - 6 + bob, PAL['egg_dark'] if not silhouette else (40, 40, 48))
    return im

def draw_mossback(im, ox=24, oy=36, phase=0, kind='idle', silhouette=False):
    """大隻，畫喺 48×48 畫布，pivot (24,45)。"""
    bob = 0 if kind == 'scared' else (0, 0, -1, 0, 0, 0)[phase % 6]
    sh = 2 if kind == 'scared' else 0
    c0 = (40, 40, 48) if silhouette else HUNT['stone_d']
    c1 = (40, 40, 48) if silhouette else HUNT['stone']
    m0 = (40, 40, 48) if silhouette else HUNT['moss_d']
    m1 = (40, 40, 48) if silhouette else HUNT['moss']
    m2 = (40, 40, 48) if silhouette else HUNT['moss_l']
    # 石身
    fill_ellipse(im, ox, oy + bob + sh, 16, 10 - sh, c0)
    fill_ellipse(im, ox, oy + bob + sh, 14, 8 - sh, c1)
    # 苔蓋
    fill_ellipse(im, ox, oy - 6 + bob, 14, 8, m0)
    fill_ellipse(im, ox, oy - 7 + bob, 12, 6, m1)
    fill_ellipse(im, ox - 3, oy - 8 + bob, 5, 3, m2)
    # 小花
    if not silhouette:
        pset(im, ox + 6, oy - 10 + bob, V3['rose']); pset(im, ox - 7, oy - 9 + bob, V3['gold'])
        _eyes(im, ox - 4, oy - 1 + bob + sh, 'scared' if kind == 'scared' else 'idle')
        fill_ellipse(im, ox, oy + 3 + bob, 3, 2, PAL['blush'])
    # 腳
    fill_ellipse(im, ox - 8, oy + 9 + bob, 4, 2, c0)
    fill_ellipse(im, ox + 8, oy + 9 + bob, 4, 2, c0)
    return im

CRITTER_DRAW = dict(dewlet=draw_dewlet, loambun=draw_loambun, seedfluff=draw_seedfluff, mossback=draw_mossback)

def critter_frames(cid):
    """idle×4、scared×4、tofruit×6（變成果再碌走）。大隻 48、細 32。"""
    meta = next(c for c in CRITTERS if c['id'] == cid)
    size = meta['size']
    draw = CRITTER_DRAW[cid]
    fruit_fn = FRUIT_DRAW[meta['fruit']]
    ox = size // 2
    oy = size - 4 if size == 32 else size - 3  # 接近 pivot 下 3
    frames, names, kinds = [], [], []
    # idle 4
    for i in range(4):
        im = rgba(size)
        draw(im, ox=ox, oy=oy, phase=i, kind='idle')
        frames.append(finish_spr(im)); names.append(f'{cid}_idle_{i+1:02d}'); kinds.append('idle')
    # scared 4
    for i in range(4):
        im = rgba(size)
        draw(im, ox=ox, oy=oy, phase=i, kind='scared')
        frames.append(finish_spr(im)); names.append(f'{cid}_scared_{i+1:02d}'); kinds.append('scared')
    # tofruit 6：1–2 抖、3 縮、4 成果、5–6 碌（果左右移）
    for i in range(6):
        im = rgba(size)
        if i <= 1:
            dx = (1, -1)[i]
            draw(im, ox=ox + dx, oy=oy, phase=i, kind='scared')
        elif i == 2:
            # 縮小怪
            tmp = rgba(size)
            draw(tmp, ox=ox, oy=oy, phase=0, kind='scared')
            # 垂直壓扁
            for y in range(size):
                yy = int(oy + (y - oy) * 0.55)
                if 0 <= yy < size:
                    row = tmp[y]
                    m = row[..., 3] > 0
                    im[yy, m] = row[m]
        else:
            fx = ox + (0, 4, 8)[i - 3]
            fy = oy + (0, 1, 2)[i - 3]
            # 果可能滾出畫布右邊，夾住
            fruit_fn(im, cx=min(size - 6, fx), cy=min(size - 4, fy), s=1.0)
        frames.append(finish_spr(im)); names.append(f'{cid}_tofruit_{i+1:02d}'); kinds.append('tofruit')
    return frames, names

# ---------------- 銅證 ----------------
def badge_copper(cid):
    im = rgba(32)
    disc(im, 16, 16, 15, HUNT['copper_d'])
    disc(im, 16, 16, 13, HUNT['copper'])
    disc(im, 16, 16, 11, HUNT['copper_l'])
    disc(im, 16, 16, 10, V3['navy2'])
    tmp = rgba(32); disc(tmp, 16, 16, 10, HUNT['copper_hi'])
    hole = rgba(32); disc(hole, 16, 16, 9, (255, 255, 255))
    keep = (tmp[..., 3] > 0) & (hole[..., 3] == 0)
    im[keep] = tmp[keep]
    sil = rgba(32)
    if cid == 'mossback':
        raw = rgba(48)
        draw_mossback(raw, ox=24, oy=36, phase=0, kind='idle', silhouette=True)
        small = scale_to(finish_spr(raw, (40, 40, 48)), 22, 22)
        m = small[..., 3] > 127
        small[m, :3] = HUNT['copper_hi']
        blit(im, small, 5, 7)
    else:
        CRITTER_DRAW[cid](sil, ox=16, oy=20, phase=0, kind='idle', silhouette=True)
        # 剪影改銅亮
        m = sil[..., 3] > 127
        sil[m, :3] = HUNT['copper_hi']
        blit(im, sil, 0, 0)
    outline_sel(im, (48, 28, 56))
    glints(im, [(9, 8), (11, 6)], V3['goldhi'])
    return harden_alpha(im)

# ---------------- 寵物 clip ----------------
def _squash(im, cy, sy, sx=1.0):
    """以 cy 為錨垂直／水平擠壓（像素）。"""
    h, w = im.shape[:2]
    out = rgba(h, w)
    for y in range(h):
        yy = int(round(cy + (y - cy) * sy))
        if not (0 <= yy < h): continue
        for x in range(w):
            if im[y, x, 3] == 0: continue
            xx = int(round(w / 2 + (x - w / 2) * sx))
            if 0 <= xx < w:
                out[yy, xx] = im[y, x]
    return out

def _lean(im, shear, pivot_y):
    """水平 shear（正＝上方向右）。"""
    h, w = im.shape[:2]
    out = rgba(h, w)
    for y in range(h):
        dx = int(round((pivot_y - y) * shear))
        for x in range(w):
            xx = x + dx
            if 0 <= xx < w and im[y, x, 3]:
                out[y, xx] = im[y, x]
    return out

def _grass_tuft(w=18, h=16, phase=0):
    im = rgba(h, w)
    cx = w // 2
    for i, (dx, ht, col) in enumerate(((-6, 10, PAL['leaf_d']), (-3, 14, PAL['leaf']), (0, 15, PAL['leaf_d']),
                                       (3, 13, PAL['leaf']), (6, 11, PAL['leaf_d']))):
        sway = (0, 1, 1, 0, -1, -1)[phase % 6] if i % 2 else 0
        x = cx + dx + sway
        for t in range(ht):
            pset(im, x + (1 if t > ht // 2 else 0), h - 1 - t, col)
            if t > ht - 4:
                pset(im, x - 1, h - 1 - t, PAL['leaf'])
    return harden_alpha(im)

def pose_part_grass(i):
    """撥草：蹲 → 伸手撥 → 草分開 → 探頭。用 pot_bump／idle 變形。"""
    try:
        base = frame_radiant('pot_bump_0%d' % (min(i + 1, 6) if i < 5 else 1) if i < 4 else 'idle_01')
    except Exception:
        base = frame_radiant('idle_01')
    # 穩陣：一律由 idle／walk 變形，避免缺幀
    idle = frame_radiant('idle_01')
    # 嘗試 pot_bump
    try:
        if i == 0: base = frame_radiant('pot_bump_01')
        elif i == 1: base = frame_radiant('pot_bump_02')
        elif i == 2: base = frame_radiant('pot_bump_03')
        elif i == 3: base = frame_radiant('pot_bump_04')
        elif i == 4: base = frame_radiant('pot_bump_05')
        else: base = frame_radiant('idle_02')
    except Exception:
        # fallback 程序化
        sq = (1.0, 0.88, 0.92, 1.05, 1.0, 1.0)[i]
        sh = (0, 0.04, 0.12, 0.18, 0.06, 0)[i]
        base = _lean(_squash(idle, 50, sq, 1.05 if sq < 1 else 0.96), sh, 50)
    im = rgba(64)
    blit(im, base, 0, 0)
    # 草叢喺右側（朝右撥）
    phase = min(i, 5)
    g = _grass_tuft(18, 16, phase)
    # 撥開：後期草左右分開
    gx = 42 + (0, 0, 1, 3, 4, 5)[i]
    gy = 48 - (0, 0, 0, 1, 1, 0)[i]
    blit(im, g, gx, gy)
    if i >= 3:
        g2 = _grass_tuft(12, 14, phase + 3)
        blit(im, g2, gx + 8, gy + 2)
    return finish_spr(im)

def pose_pounce(i):
    try:
        return finish_spr(frame_radiant(f'play_0{i+1}'))
    except Exception:
        idle = frame_radiant('idle_01')
        # 蹲→扭→彈→撲→落地
        sy = (0.86, 0.9, 1.12, 1.04, 0.92, 1.0)[i]
        sx = (1.1, 1.06, 0.9, 0.95, 1.08, 1.0)[i]
        dy = (2, 1, -8, -4, 1, 0)[i]
        sh = (0, 0.08, 0.15, 0.2, 0.05, 0)[i]
        im = shift(_lean(_squash(idle, 50, sy, sx), sh, 50), dx=(0, 1, 3, 5, 3, 0)[i], dy=dy)
        return finish_spr(im)

def pose_carry(i):
    try:
        wlk = frame_radiant(f'walk_0{i+1}')
    except Exception:
        wlk = frame_radiant('idle_01')
        wlk = shift(wlk, dy=(0, -1, 0, 0, -1, 0)[i])
    im = wlk.copy()
    # 抱住星莓喺胸前（大約 28, 40）
    fr = rgba(32)
    fruit_starberry(fr, 16, 20, 0.85)
    # 貼到寵物身前
    blit(im, fr, 26, 32 + (0, -1, 0, 0, -1, 0)[i])
    return finish_spr(im)

def pose_cheer(i):
    try:
        return finish_spr(frame_radiant(f'cheer_jump_0{i+1}'))
    except Exception:
        idle = frame_radiant('idle_01')
        dy = (0, -3, -10, -8, -2, 0)[i]
        sy = (0.95, 1.08, 1.12, 1.06, 0.92, 1.0)[i]
        im = shift(_squash(idle, 50, sy, 0.95 if sy > 1 else 1.05), dy=dy)
        return finish_spr(im)

POSE = dict(part_grass=pose_part_grass, pounce=pose_pounce, carry_fruit=pose_carry, cheer=pose_cheer)

def resize_pet(im64, size, pivot):
    """64 pivot (32,61) → 目標尺寸，腳底對齊新 pivot。"""
    if size == 64:
        return im64
    scaled = scale_to(im64, size, size)
    # scale_to 係整幅縮，pivot 大約跟比例。檢查腳底
    # 64 嘅 pivot y=61，縮放後希望 pivot 喺指定位。用腳底不透明最低行對齊。
    a = scaled[..., 3] > 0
    if not a.any():
        return scaled
    rows = np.where(a.any(1))[0]
    foot = rows[-1]
    # 希望 foot ≈ pivot[1] + 2（腳掌低過 pivot 約 2px，同 CLIPS.md）
    target_foot = min(size - 1, pivot[1] + 2)
    dy = target_foot - foot
    if dy != 0:
        scaled = shift(scaled, dy=dy)
    # 水平：不透明質心對齊 pivot x
    a = scaled[..., 3] > 0
    if a.any():
        xs = np.where(a.any(0))[0]
        cx = (xs[0] + xs[-1]) / 2
        dx = int(round(pivot[0] - cx))
        if dx:
            scaled = shift(scaled, dx=dx)
    return harden_alpha(scaled)

def build(out_root):
    art = os.path.join(out_root, 'art-pet')
    # 果
    fd = os.path.join(art, 'sprites/hunt/fruits')
    os.makedirs(fd, exist_ok=True)
    fframes, fnames, fitems = [], [], []
    for fr in FRUITS:
        im = finish_spr(FRUIT_DRAW[fr['id']]())
        save_png(f'{fd}/{fr["id"]}.png', im)
        n = normal_from_sprite(im)
        save_png(f'{fd}/{fr["id"]}_n.png', n)
        fframes.append(im); fnames.append(fr['id'])
        fitems.append(dict(id=fr['id'], zh=fr['zh'], size=32, pivotPx=[16, 28],
                           file=f'{fr["id"]}.png', normal=f'{fr["id"]}_n.png'))
    atl, fj, W, H = pack_atlas(fframes, fnames, pad=2, cols=6)
    ns = [normal_from_sprite(f) for f in fframes]
    natl, _, _, _ = pack_atlas(ns, fnames, pad=2, cols=6, bg_n=True)
    save_png(f'{fd}/atlas_fruits.png', atl)
    save_png(f'{fd}/atlas_fruits_n.png', natl)
    for k, rec in fj.items():
        rec['pivotPx'] = {'x': 16, 'y': 28}
    fruit_spec = dict(format='hunt.fruit/1', size=32, pivotPx=[16, 28], alpha='0/255',
                      normal='OpenGL Y+（綠＝上）', count=6, items=fitems,
                      atlas=dict(image='atlas_fruits.png', normal='atlas_fruits_n.png',
                                 size={'w': W, 'h': H}, padding=2, frames=fj))
    json.dump(fruit_spec, open(f'{fd}/fruits.json', 'w'), ensure_ascii=False, indent=1)

    # 小怪
    cd = os.path.join(art, 'sprites/hunt/critters')
    os.makedirs(cd, exist_ok=True)
    c_spec_items = []
    for meta in CRITTERS:
        frames, names = critter_frames(meta['id'])
        size = meta['size']
        pivot = (size // 2, size - 3)
        norms = [normal_from_sprite(f) for f in frames]
        cols = 8
        atl, fj, W, H = pack_atlas(frames, names, pad=2, cols=cols)
        natl, _, _, _ = pack_atlas(norms, names, pad=2, cols=cols, bg_n=True)
        save_png(f'{cd}/atlas_{meta["id"]}.png', atl)
        save_png(f'{cd}/atlas_{meta["id"]}_n.png', natl)
        anims = {
            'idle': dict(frames=[n for n in names if n.endswith and '_idle_' in n], fps=4, loop=True),
            'scared': dict(frames=[n for n in names if '_scared_' in n], fps=6, loop=True),
            'tofruit': dict(frames=[n for n in names if '_tofruit_' in n], fps=8, loop=False),
        }
        for n, rec in fj.items():
            rec['pivotPx'] = {'x': pivot[0], 'y': pivot[1]}
        spec = dict(format='hunt.critter/1', id=meta['id'], zh=meta['zh'], size=size,
                    pivotPx=list(pivot), big=meta['big'], fruit=meta['fruit'],
                    alpha='0/255', normal='OpenGL Y+（綠＝上）',
                    note=meta['note'],
                    atlas=dict(image=f'atlas_{meta["id"]}.png', normal=f'atlas_{meta["id"]}_n.png',
                               size={'w': W, 'h': H}, padding=2, frames=fj),
                    animations=anims)
        json.dump(spec, open(f'{cd}/{meta["id"]}.json', 'w'), ensure_ascii=False, indent=1)
        c_spec_items.append(spec)
        # 散幀唔出，靠 atlas
    json.dump(dict(format='hunt.critters/1', count=4, items=[{k: c[k] for k in ('id', 'zh', 'size', 'big', 'fruit')} for c in c_spec_items]),
              open(f'{cd}/critters.json', 'w'), ensure_ascii=False, indent=1)

    # 銅證
    bd = os.path.join(art, 'ui/m1_icons/badges')
    os.makedirs(bd, exist_ok=True)
    bframes, bnames, bitems = [], [], []
    for meta in CRITTERS:
        im = badge_copper(meta['id'])
        save_png(f'{bd}/badge_copper_{meta["id"]}@3x.png', im)
        bframes.append(im); bnames.append(f'badge_copper_{meta["id"]}')
        bitems.append(dict(id=f'badge_copper_{meta["id"]}', zh=f'銅證・{meta["zh"]}',
                           size=32, file=f'badge_copper_{meta["id"]}@3x.png', pivotPx=[16, 16],
                           critter=meta['id']))
    atl, fj, W, H = pack_atlas(bframes, bnames, pad=2, cols=4)
    save_png(f'{bd}/atlas_badges_copper@3x.png', atl)
    for n, rec in fj.items():
        rec['pivotPx'] = {'x': 16, 'y': 16}
    badge_spec = dict(format='hunt.badge/1', tier='copper', count=4, size=32, scale='@3x',
                      style='V3-A 銅章＋小怪剪影', alpha='0/255', items=bitems,
                      atlas=dict(image='atlas_badges_copper@3x.png', size={'w': W, 'h': H}, padding=2, frames=fj))
    json.dump(badge_spec, open(f'{bd}/badges.json', 'w'), ensure_ascii=False, indent=1)

    # 寵物 clip
    hd = os.path.join(art, 'sprites/tuanrong/motion/hunt')
    os.makedirs(hd, exist_ok=True)
    if find_radiant_frames() is None:
        raise SystemExit('搵唔到 radiant 幀，無法出狩獵 clip')
    clip_index = dict(format='hunt.petclip/1', form='radiant', sizes=SIZES, clips=CLIPS,
                      facing='全部朝右；朝左＝scaleX −1，法線 R→255−R',
                      normal='OpenGL Y+（綠＝上）', alpha='0/255',
                      atlases={})
    built = {}
    for sz, szm in SIZES.items():
        for cid, cm in CLIPS.items():
            frs = []
            for i in range(cm['frames']):
                im64 = POSE[cid](i)
                im = resize_pet(im64, szm['size'], szm['pivot'])
                frs.append(im)
            names = [f'{cid}_{i+1:02d}' for i in range(cm['frames'])]
            norms = [normal_from_sprite(f) for f in frs]
            # emissive：從原幀光芽色（glow）提取
            ems = []
            for f in frs:
                e = np.zeros_like(f)
                glow = (f[..., 3] > 0) & (
                    ((f[..., 0] >= 250) & (f[..., 1] >= 200) & (f[..., 2] <= 160)) |
                    ((f[..., 0] >= 255) & (f[..., 1] >= 230) & (f[..., 2] >= 180) & (f[..., 2] <= 230))
                )
                e[glow] = f[glow]
                ems.append(e)
            cols = 6
            atl, fj, W, H = pack_atlas(frs, names, pad=2, cols=cols)
            natl, _, _, _ = pack_atlas(norms, names, pad=2, cols=cols, bg_n=True)
            eatl, _, _, _ = pack_atlas(ems, names, pad=2, cols=cols)
            stem = f'atlas_radiant_{cid}_{sz}'
            save_png(f'{hd}/{stem}.png', atl)
            save_png(f'{hd}/{stem}_n.png', natl)
            save_png(f'{hd}/{stem}_emissive.png', eatl)
            for n, rec in fj.items():
                rec['pivotPx'] = {'x': szm['pivot'][0], 'y': szm['pivot'][1]}
            js = dict(format='hunt.petclip.atlas/1', form='radiant', size=sz, frameSize=szm['size'],
                      pivotPx=list(szm['pivot']), clip=cid, zh=cm['zh'],
                      frames=fj, fps=cm['fps'], loop=cm['loop'], frameCount=cm['frames'],
                      meta=dict(image=f'{stem}.png', normal=f'{stem}_n.png', emissive=f'{stem}_emissive.png',
                                size={'w': W, 'h': H}, padding=2, form='radiant', frameSize=szm['size'],
                                pivotPx=list(szm['pivot'])))
            json.dump(js, open(f'{hd}/{stem}.json', 'w'), ensure_ascii=False, indent=1)
            clip_index['atlases'].setdefault(sz, {})[cid] = f'{stem}.json'
            built[(sz, cid)] = (frs, names, cm)
    json.dump(clip_index, open(f'{hd}/clips.json', 'w'), ensure_ascii=False, indent=1)
    return dict(fruits=fruit_spec, badges=badge_spec, clips=clip_index, built=built)

if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else '/workspace/m1-icons-hunt-src'
    build(root)
    print('sprites ok')
