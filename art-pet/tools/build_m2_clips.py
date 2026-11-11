#!/usr/bin/env python3
"""build_m2_clips.py — M2 寵物動作：投信、招牌 idle×6、小動作×4、指相框，各 ×S/M/L。
程序化像素；以現有 radiant 幀變形＋道具疊加。_n OpenGL Y+、emissive、atlas json。"""
import os, sys, json, math
import numpy as np
from PIL import Image
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from m1_common import (
    V3, PAL, rgba, pset, fill_rect, fill_ellipse, outline_sel, harden_alpha,
    blit, shift, save_png, pack_atlas, normal_from_sprite, scale_to,
    frame_radiant, find_radiant_frames, SIZES,
)

def disc(im, cx, cy, r, col, a=255):
    fill_ellipse(im, cx, cy, r, r, col, a)

def finish_spr(im, ol=(59, 42, 62)):
    outline_sel(im, ol)
    return harden_alpha(im)

def fr(name, fallback='idle_01'):
    try:
        return frame_radiant(name)
    except Exception:
        return frame_radiant(fallback)

def _squash(im, cy, sy, sx=1.0):
    """逆映射擠壓，避免散點造成橫間條。"""
    h, w = im.shape[:2]
    out = rgba(h, w)
    sy = sy if abs(sy) > 1e-6 else 1.0
    sx = sx if abs(sx) > 1e-6 else 1.0
    for yy in range(h):
        y = int(round(cy + (yy - cy) / sy))
        if not (0 <= y < h):
            continue
        for xx in range(w):
            x = int(round(w / 2 + (xx - w / 2) / sx))
            if 0 <= x < w and im[y, x, 3]:
                out[yy, xx] = im[y, x]
    return out

def _lean(im, shear, pivot_y):
    """逆映射 shear（正＝上方向右）。"""
    h, w = im.shape[:2]
    out = rgba(h, w)
    for y in range(h):
        dx = int(round((pivot_y - y) * shear))
        for xx in range(w):
            x = xx - dx
            if 0 <= x < w and im[y, x, 3]:
                out[y, xx] = im[y, x]
    return out

def paw(im, cx, cy, rx=4, ry=3, col=None):
    col = col or PAL['cream2']
    fill_ellipse(im, cx, cy, rx, ry, PAL['outline'])
    fill_ellipse(im, cx, cy, max(1, rx - 1), max(1, ry - 1), col)
    pset(im, cx - 1, cy - 1, PAL['cream4'])

def envelope(w=14, h=10):
    im = rgba(h, w)
    fill_rect(im, 0, 0, w, h, PAL['cream3'])
    fill_rect(im, 1, 1, w - 1, h - 1, PAL['cream4'])
    # 三角蓋
    for i in range(w // 2):
        pset(im, i, 1 + i // 2, V3['gold'])
        pset(im, w - 1 - i, 1 + i // 2, V3['gold'])
    # 蠟印
    disc(im, w // 2, h // 2 + 1, 2, V3['navy3'])
    pset(im, w // 2, h // 2 + 1, V3['goldhi'])
    return harden_alpha(im)

def leaf_bit(w=8, h=8):
    im = rgba(h, w)
    fill_ellipse(im, 4, 4, 4, 3, PAL['leaf_d'])
    fill_ellipse(im, 4, 3, 3, 2, PAL['leaf'])
    pset(im, 4, 4, PAL['outline'])
    return harden_alpha(im)

# -------------------- 招牌 idle ×6（循環，一眼認出性格）--------------------
def pose_idle_lively(i):
    """活潑：原地蹦蹦跳，身體彈、芽亮。"""
    hop = [0, -2, -9, -6, -1, 0][i]
    names = ['idle_01', 'play_02', 'cheer_jump_03', 'play_03', 'play_05', 'idle_02']
    base = fr(names[i])
    sy = [0.96, 1.06, 1.12, 1.08, 0.92, 1.0][i]
    im = shift(_squash(base, 50, sy, 0.96 if sy > 1 else 1.06), dy=hop)
    return finish_spr(im)

def pose_idle_quiet(i):
    """文靜：坐低收腳（Kurt 批坐低草稿，2026-11-11），輕輕呼吸、偶爾眨眼。"""
    from art_fix1_sit import pose_idle_quiet as _sit
    return _sit(i)

def pose_idle_diligent(i):
    """勤力：彎腰執落葉，執起再擺好。"""
    # 彎 → 伸手 → 執到 → 企起 → 睇一眼 → 放低準備再執
    names = ['pot_bump_02', 'pot_bump_03', 'pot_bump_04', 'idle_02', 'idle_01', 'pot_bump_01']
    base = fr(names[i])
    sy = [0.88, 0.84, 0.90, 1.0, 1.0, 0.92][i]
    sh = [0.04, 0.10, 0.08, 0.0, 0.0, 0.03][i]
    im = _lean(_squash(base, 52, sy, 1.08 if sy < 1 else 1.0), sh, 52)
    lf = leaf_bit()
    # 葉：地下 → 手中 → 側邊
    pos = [(40, 54), (42, 48), (38, 40), (34, 36), (28, 38), (22, 54)][i]
    blit(im, lf, pos[0], pos[1])
    return finish_spr(im)

def pose_idle_lazy(i):
    """懶散：攤喺地、半瞇眼，中段打個小小呵欠。"""
    # 全程用晒太陽／瞓姿，保持「攤平」剪影（頭頂芽喺上，法線綠＝上先穩）
    names = ['sunbathe_01', 'sunbathe_02', 'sunbathe_04', 'sunbathe_05', 'sunbathe_06', 'sunbathe_03']
    base = fr(names[i])
    if i == 3:
        # 中段小小呵欠，仍然躺
        yawn = fr('yawn_02')
        base = shift(_squash(yawn, 54, 0.85, 1.15), dy=6)
    else:
        base = shift(_squash(base, 54, 0.90, 1.08), dy=3)
    return finish_spr(base)

def pose_idle_clingy(i):
    """黐人：伸手跟住你／鏡頭，向前傾、想抱。"""
    names = ['catch_reach_01', 'catch_reach_02', 'catch_reach_03',
             'catch_reach_04', 'emo_cuddly_01', 'catch_reach_02']
    base = fr(names[i])
    bob = [0, -1, -2, -1, 0, -1][i]
    lean = [0.06, 0.10, 0.14, 0.12, 0.08, 0.10][i]
    im = shift(_lean(base, lean, 52), dy=bob, dx=[0, 1, 2, 2, 1, 1][i])
    # 額外一隻爪向鏡頭（畫面偏上）
    if i >= 1:
        paw(im, 40 + (i % 2), 28 - bob, 5, 4)
    return finish_spr(im)

def pose_idle_indep(i):
    """獨立：自己企一邊望天／望遠，手搭額，唔靠人。"""
    names = ['sway_01', 'sway_02', 'idle_03', 'sway_03', 'sway_04', 'idle_01']
    base = fr(names[i])
    # 微仰頭（上半拉長）＋身體稍側
    sy = 1.04 + 0.03 * math.sin(i * math.pi / 3)
    im = _lean(_squash(base, 40, sy, 0.98), -0.06, 50)
    # 手搭喺額前望遠
    paw(im, 22, 22 + (i % 2), 4, 3)
    return finish_spr(im)

# -------------------- 小動作 ×4（一次過）--------------------
def pose_scratch_head(i):
    """抓頭。"""
    names = ['idle_01', 'idle_02', 'idle_03', 'idle_02', 'idle_04', 'idle_01']
    base = fr(names[i])
    im = base.copy()
    # 爪由身側提到頭側再撓
    xs = [36, 38, 30, 28, 30, 34]
    ys = [40, 32, 20, 18, 20, 38]
    if i >= 1:
        paw(im, xs[i], ys[i], 5, 4)
        if i in (2, 3, 4):
            # 撓：爪左右晃，加兩條短線
            pset(im, xs[i] + 4, ys[i] - 3, PAL['cream4'])
            pset(im, xs[i] + 5, ys[i] - 1, PAL['cream3'])
    return finish_spr(im)

def pose_stretch(i):
    """伸懶腰：踮腳、雙手向上拉長，再回落。"""
    names = ['idle_01', 'yawn_01', 'yawn_02', 'yawn_03', 'yawn_04', 'idle_02']
    base = fr(names[i])
    sy = [1.0, 1.08, 1.18, 1.16, 1.04, 1.0][i]
    dy = [0, -1, -4, -3, 0, 0][i]
    im = shift(_squash(base, 58, sy, 0.90 if sy > 1.05 else 1.0), dy=dy)
    # 雙手向上
    if 1 <= i <= 4:
        paw(im, 22, 16 + dy, 4, 5)
        paw(im, 42, 14 + dy, 4, 5)
    return finish_spr(im)

def pose_look_sky(i):
    """望天：仰頭、手搭額、望一阵再收回。"""
    names = ['idle_01', 'sway_02', 'idle_03', 'sway_03', 'sway_04', 'idle_01']
    base = fr(names[i])
    tilt = [0, 0.04, 0.10, 0.10, 0.05, 0][i]
    sy = [1.0, 1.04, 1.10, 1.10, 1.04, 1.0][i]
    im = _lean(_squash(base, 38, sy, 0.98), -tilt, 48)
    if 1 <= i <= 4:
        paw(im, 24, 20 - (1 if i in (2, 3) else 0), 4, 3)
    return finish_spr(im)

def pose_proud_hips(i):
    """叉腰得意（覺得自己好醒）：胸膛一挺、兩爪叉腰、得意面。"""
    names = ['idle_01', 'celebrate_01', 'celebrate_02', 'celebrate_03', 'celebrate_02', 'idle_02']
    base = fr(names[i])
    puff = [1.0, 1.08, 1.14, 1.12, 1.10, 1.02][i]
    im = _squash(base, 50, puff, 1.10 if puff > 1.05 else 1.0)
    # 叉腰：兩隻爪貼喺腰側
    if i >= 1:
        paw(im, 18, 42, 4, 4)
        paw(im, 46, 42, 4, 4)
    return finish_spr(im)

# -------------------- 投信／指相框 --------------------
def pose_mail_post(i):
    """投信：拎信封行近、舉起、塞入（向前伸）、拍拍手。"""
    names = ['walk_01', 'walk_03', 'walk_05', 'idle_02', 'catch_reach_03', 'idle_01']
    base = fr(names[i])
    im = base.copy()
    env = envelope()
    # 信封位置：胸前 → 提高 → 向前伸（右側）
    pos = [(28, 38), (30, 36), (32, 32), (34, 24), (44, 22), (36, 40)][i]
    blit(im, env, pos[0], pos[1])
    if i == 4:
        # 伸手勢
        paw(im, 42, 28, 4, 3)
    if i == 5:
        # 拍完手，信封唔見（已投入）；兩爪喺胸前
        paw(im, 26, 40, 3, 3)
        paw(im, 36, 40, 3, 3)
        # 唔好再畫信封：上面已經 blit 喺腰側當收勢，改為清掉偏前嗰封
    return finish_spr(im)

def pose_point_frame(i):
    """指相框：行近、轉側、伸臂指向（右上），望住、維持、收回。"""
    names = ['walk_02', 'idle_01', 'idle_02', 'catch_reach_04', 'catch_reach_05', 'idle_03']
    base = fr(names[i])
    sh = [0, 0.04, 0.08, 0.10, 0.10, 0.02][i]
    im = _lean(base, sh, 50)
    # 指向右上嘅臂＋爪
    if i >= 2:
        ax, ay = [(0, 0), (0, 0), (38, 30), (46, 22), (48, 20), (36, 34)][i]
        # 短臂
        for t in range(6):
            pset(im, ax - 3 + t, ay + 4 - t // 2, PAL['cream1'])
            pset(im, ax - 3 + t, ay + 5 - t // 2, PAL['cream0'])
        paw(im, ax + 3, ay - 1, 4, 3)
        if i in (3, 4):
            # 指引短線
            pset(im, ax + 7, ay - 4, PAL['cream4'])
            pset(im, ax + 8, ay - 6, PAL['cream3'])
    return finish_spr(im)

CLIPS = {
    'mail_post':      dict(zh='投信',     frames=6, fps=8, loop=False, kind='action'),
    'idle_lively':    dict(zh='招牌·活潑', frames=6, fps=8, loop=True,  kind='idle', personality='lively'),
    'idle_quiet':     dict(zh='招牌·文靜', frames=6, fps=6, loop=True,  kind='idle', personality='quiet'),
    'idle_diligent':  dict(zh='招牌·勤力', frames=6, fps=8, loop=True,  kind='idle', personality='diligent'),
    'idle_lazy':      dict(zh='招牌·懶散', frames=6, fps=5, loop=True,  kind='idle', personality='lazy'),
    'idle_clingy':    dict(zh='招牌·黐人', frames=6, fps=8, loop=True,  kind='idle', personality='clingy'),
    'idle_indep':     dict(zh='招牌·獨立', frames=6, fps=6, loop=True,  kind='idle', personality='indep'),
    'scratch_head':   dict(zh='抓頭',     frames=6, fps=8, loop=False, kind='fidget'),
    'stretch':        dict(zh='伸懶腰',   frames=6, fps=8, loop=False, kind='fidget'),
    'look_sky':       dict(zh='望天',     frames=6, fps=8, loop=False, kind='fidget'),
    'proud_hips':     dict(zh='叉腰得意', frames=6, fps=8, loop=False, kind='fidget'),
    'point_frame':    dict(zh='指相框',   frames=6, fps=8, loop=False, kind='action'),
}

POSE = {
    'mail_post': pose_mail_post,
    'idle_lively': pose_idle_lively,
    'idle_quiet': pose_idle_quiet,
    'idle_diligent': pose_idle_diligent,
    'idle_lazy': pose_idle_lazy,
    'idle_clingy': pose_idle_clingy,
    'idle_indep': pose_idle_indep,
    'scratch_head': pose_scratch_head,
    'stretch': pose_stretch,
    'look_sky': pose_look_sky,
    'proud_hips': pose_proud_hips,
    'point_frame': pose_point_frame,
}

def resize_pet(im64, size, pivot):
    if size == 64:
        return im64
    scaled = scale_to(im64, size, size)
    a = scaled[..., 3] > 0
    if not a.any():
        return scaled
    rows = np.where(a.any(1))[0]
    foot = rows[-1]
    target_foot = min(size - 1, pivot[1] + 2)
    dy = target_foot - foot
    if dy:
        scaled = shift(scaled, dy=dy)
    a = scaled[..., 3] > 0
    if a.any():
        xs = np.where(a.any(0))[0]
        cx = (xs[0] + xs[-1]) / 2
        dx = int(round(pivot[0] - cx))
        if dx:
            scaled = shift(scaled, dx=dx)
    return harden_alpha(scaled)

def emissive_of(f):
    e = np.zeros_like(f)
    glow = (f[..., 3] > 0) & (
        ((f[..., 0] >= 250) & (f[..., 1] >= 200) & (f[..., 2] <= 160)) |
        ((f[..., 0] >= 255) & (f[..., 1] >= 230) & (f[..., 2] >= 180) & (f[..., 2] <= 230))
    )
    e[glow] = f[glow]
    return e

def build(out_root):
    if find_radiant_frames() is None:
        raise SystemExit('搵唔到 radiant 幀')
    hd = os.path.join(out_root, 'art-pet/sprites/tuanrong/motion/m2')
    os.makedirs(hd, exist_ok=True)
    sizes_out = {k: dict(size=v['size'], pivot=list(v['pivot']), zh=v['zh']) for k, v in SIZES.items()}
    index = dict(format='m2.petclip/1', form='radiant', sizes=sizes_out, clips=CLIPS,
                 facing='全部朝右；朝左＝scaleX −1，法線 R→255−R',
                 normal='OpenGL Y+（綠＝上）', alpha='0/255',
                 atlases={})
    for sz, szm in SIZES.items():
        for cid, cm in CLIPS.items():
            frs = [resize_pet(POSE[cid](i), szm['size'], szm['pivot']) for i in range(cm['frames'])]
            names = [f'{cid}_{i+1:02d}' for i in range(cm['frames'])]
            norms = [normal_from_sprite(f) for f in frs]
            ems = [emissive_of(f) for f in frs]
            atl, fj, W, H = pack_atlas(frs, names, pad=2, cols=6)
            natl, _, _, _ = pack_atlas(norms, names, pad=2, cols=6, bg_n=True)
            eatl, _, _, _ = pack_atlas(ems, names, pad=2, cols=6)
            stem = f'atlas_radiant_{cid}_{sz}'
            save_png(f'{hd}/{stem}.png', atl)
            save_png(f'{hd}/{stem}_n.png', natl)
            save_png(f'{hd}/{stem}_emissive.png', eatl)
            for n, rec in fj.items():
                rec['pivotPx'] = {'x': szm['pivot'][0], 'y': szm['pivot'][1]}
            js = dict(format='m2.petclip.atlas/1', form='radiant', size=sz, frameSize=szm['size'],
                      pivotPx=list(szm['pivot']), clip=cid, zh=cm['zh'],
                      frames=fj, fps=cm['fps'], loop=cm['loop'], frameCount=cm['frames'],
                      kind=cm.get('kind'), personality=cm.get('personality'),
                      meta=dict(image=f'{stem}.png', normal=f'{stem}_n.png', emissive=f'{stem}_emissive.png',
                                size={'w': W, 'h': H}, padding=2, form='radiant', frameSize=szm['size'],
                                pivotPx=list(szm['pivot'])))
            json.dump(js, open(f'{hd}/{stem}.json', 'w'), ensure_ascii=False, indent=1)
            index['atlases'].setdefault(sz, {})[cid] = f'{stem}.json'
            print(f'  clip {sz} {cid}', flush=True)
    json.dump(index, open(f'{hd}/clips.json', 'w'), ensure_ascii=False, indent=1)
    return index

if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else '/workspace/m2-actions-src'
    build(root)
    print('m2 clips ok')
