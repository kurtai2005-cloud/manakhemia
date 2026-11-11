#!/usr/bin/env python3
"""文靜 idle_quiet：坐低草稿（Kurt 已批）程序化落地，6 幀呼吸＋眨眼。"""
from __future__ import annotations
import math
import numpy as np
from m1_common import (
    PAL, rgba, pset, fill_ellipse, outline_sel, harden_alpha, shift, scale_to,
    pack_atlas, normal_from_sprite, save_png, SIZES,
)

OL = PAL['outline']
C0, C1, C2, C3 = PAL['cream0'], PAL['cream1'], PAL['cream2'], PAL['cream3']
BLUSH_D = (237, 161, 144)
BLUSH_L = (243, 175, 164)
FOOT = PAL['peach1']
FOOT_D = PAL['cream0']
GLOW, GLOW_M, GLOW_C = PAL['glow'], PAL['glow_mid'], PAL['glow_core']

# lighting fit on approved draft: t = 0.03x + 0.054y
_LIGHT_A, _LIGHT_B = 0.03, 0.054
_TH = (2.6480520498587983, 3.2271229410002995, 3.8056673854447434)


def _disc(im, cx, cy, r, col):
    fill_ellipse(im, cx, cy, r, r, col)


def _star(im, cx, cy, on=True):
    if not on:
        return
    pset(im, cx, cy, GLOW_C)
    pset(im, cx - 1, cy, GLOW)
    pset(im, cx + 1, cy, GLOW)
    pset(im, cx, cy - 1, GLOW)
    pset(im, cx, cy + 1, GLOW)


def _cream_at(x, y):
    t = _LIGHT_A * x + _LIGHT_B * y
    if t < _TH[0]:
        return C0
    if t < _TH[1]:
        return C1
    if t < _TH[2]:
        return C2
    return C3


def _paint_body():
    """Rest-pose sitting body + outline, no face / bulb / feet."""
    im = rgba(64, 64)
    # Main sit body + a flatter cushion so cream reaches y=58 between the feet.
    yy, xx = np.mgrid[0:64, 0:64]
    inside = np.zeros((64, 64), bool)
    for cx, cy, rx, ry in (
        (32.5, 41.2, 22.6, 16.2),
        (32.5, 52.5, 17.5, 6.2),  # sit cushion
    ):
        dx = (xx + 0.5 - cx) / rx
        dy = (yy + 0.5 - cy) / ry
        inside |= (dx * dx + dy * dy) <= 1.0
    inside[59:] = False
    inside[:25] = False
    for y, x in zip(*np.where(inside)):
        im[y, x, :3] = _cream_at(int(x), int(y))
        im[y, x, 3] = 255
    return im


def _paint_feet(im):
    # left / right short sit-feet, draft coords
    for xs, shadow_xs in (((24, 25, 26), (24, 25, 26)), ((38, 39, 40), (38, 39, 40))):
        pass
    # y57: 24-26 and 38-40; y58-59: 23-27 and 37-41; y60 shadow 24-26 and 38-40
    for x in range(23, 28):
        for y in range(57, 60):
            if y == 57 and x in (23, 27):
                continue
            pset(im, x, y, FOOT)
        if 24 <= x <= 26:
            pset(im, x, 60, FOOT_D)
    for x in range(37, 42):
        for y in range(57, 60):
            if y == 57 and x in (37, 41):
                continue
            pset(im, x, y, FOOT)
        if 38 <= x <= 40:
            pset(im, x, 60, FOOT_D)
    return im


def _paint_face(im, eyes='soft'):
    """eyes: soft (draft squint), blink (tighter), open (tiny peek)."""
    # blush diamonds
    for cx, cols in ((21, (BLUSH_D, BLUSH_D)), (43, (BLUSH_L, BLUSH_L))):
        col = cols[0]
        pset(im, cx, 41, col)
        for x in range(cx - 1, cx + 2):
            pset(im, x, 42, col)
        for x in range(cx - 2, cx + 3):
            pset(im, x, 43, col)
        for x in range(cx - 1, cx + 2):
            pset(im, x, 44, col)
        pset(im, cx, 45, col)
    # mouth: gentle soft curve (center higher than corners, y-down = slight smile)
    for x in (31, 32, 33):
        pset(im, x, 46, OL)
    for x in (29, 30, 34, 35):
        pset(im, x, 47, OL)
    # eyes
    if eyes == 'blink':
        # fully closed line
        for x in range(24, 29):
            pset(im, x, 40, OL)
        for x in range(36, 41):
            pset(im, x, 40, OL)
    elif eyes == 'open':
        # slightly more open: 2px tall
        for x in range(25, 28):
            pset(im, x, 39, OL)
            pset(im, x, 40, OL)
        for x in range(37, 40):
            pset(im, x, 39, OL)
            pset(im, x, 40, OL)
        pset(im, 25, 39, PAL['white'])
        pset(im, 37, 39, PAL['white'])
    else:
        # approved soft squint
        for x in range(25, 28):
            pset(im, x, 39, OL)
        for x in range(24, 29):
            pset(im, x, 40, OL)
        for x in range(37, 40):
            pset(im, x, 39, OL)
        for x in range(36, 41):
            pset(im, x, 40, OL)
    return im


def _paint_bulb(im, dy=0, twinkle=(True, True, True)):
    """Small quiet bulb sitting on the head, plus 3 sparkles."""
    by = 0 + dy
    # 7x7 rounded bulb centred at (32, 21), matching approved draft
    # row pattern: ACCCA / CBBBCA / CBBBBC x3 / CBBBCA / ACCCA
    cx, cy = 32, 21 + by
    for yoff, xs, colmap in (
        (-3, range(30, 35), 'rim'),
        (-2, range(29, 36), 'outer'),
        (-1, range(29, 36), 'mid'),
        (0, range(29, 36), 'mid'),
        (1, range(29, 36), 'mid'),
        (2, range(29, 36), 'outer'),
        (3, range(30, 35), 'rim'),
    ):
        for x in xs:
            y = cy + yoff
            if colmap == 'rim' or x in (xs[0], xs[-1]):
                c = GLOW
            elif x in (xs[0] + 1, xs[-1] - 1) and colmap != 'mid':
                c = GLOW_M
            elif abs(x - cx) <= 1 and abs(yoff) <= 1:
                c = GLOW_C
            elif abs(x - cx) <= 2 and abs(yoff) <= 2:
                c = GLOW_C if abs(yoff) <= 1 else GLOW_M
            else:
                c = GLOW_M
            pset(im, x, y, c)
    # core overwrite
    fill_ellipse(im, cx, cy, 2.2, 2.2, GLOW_C)
    # short stem is the head outline touching the bulb (outline_sel after body)
    # sparkles (draft positions, shifted with bulb)
    # (36,15), (24,18), (41,20)
    if twinkle[0]:
        _star(im, 36, 15 + by)
    if twinkle[1]:
        _star(im, 24, 18 + by)
    if twinkle[2]:
        _star(im, 41, 20 + by)
    return im


def _squash_keep_feet(im, cy, sy, pin_foot=60):
    """Vertical squash around cy; then pin the lowest pixel to pin_foot."""
    if abs(sy - 1.0) < 1e-4:
        return im
    h, w = im.shape[:2]
    out = rgba(h, w)
    sy = sy if abs(sy) > 1e-6 else 1.0
    for yy in range(h):
        y = int(round(cy + (yy - cy) / sy))
        if not (0 <= y < h):
            continue
        for xx in range(w):
            if im[y, xx, 3]:
                out[yy, xx] = im[y, xx]
    a = out[..., 3] > 0
    if a.any() and pin_foot is not None:
        foot = int(np.where(a.any(1))[0][-1])
        dy = pin_foot - foot
        if dy:
            out = shift(out, dy=dy)
    return out


def pose_idle_quiet(i: int) -> np.ndarray:
    """6-frame loop, fps 6. Frame 0 ≈ approved sitting draft."""
    # breath: 0 rest, 1 inhale, 2 peak+blink, 3 blink+exhale start, 4 exhale, 5 settle
    breath = [0.0, 0.55, 1.0, 0.35, -0.6, -0.15][i]
    eyes = ['soft', 'soft', 'blink', 'blink', 'soft', 'soft'][i]
    tw = [
        (True, True, True),
        (True, False, True),
        (False, True, True),
        (True, True, False),
        (True, False, True),
        (False, True, True),
    ][i]
    bulb_dy = [0, -1, -1, 0, 1, 0][i]
    body = _paint_body()
    body = _paint_face(body, eyes=eyes)
    sy = 1.0 + 0.035 * breath
    if abs(sy - 1.0) > 1e-4:
        body = _squash_keep_feet(body, 56, sy, pin_foot=58)
    im = body
    # stamp sit base so cream sits between the feet (y=58) and underside exists (y=59)
    for x in range(27, 38):
        pset(im, x, 58, _cream_at(x, 58))
    for x in range(28, 37):
        pset(im, x, 59, _cream_at(x, 59))
    im = _paint_feet(im)
    im = outline_sel(im, OL)
    im = _paint_feet(im)  # keep foot interiors peach after outline
    for x in range(28, 37):
        pset(im, x, 59, OL)
    for x in range(24, 27):
        pset(im, x, 60, FOOT_D)
    for x in range(38, 41):
        pset(im, x, 60, FOOT_D)
    im = _paint_bulb(im, dy=bulb_dy, twinkle=tw)
    return harden_alpha(im)


def anchors_of(im: np.ndarray, eyes='soft') -> dict:
    """eyeL/eyeR/mouth in frame-local px, from painted features (fallback: detect)."""
    # Prefer detection: OL clusters in face band
    ol = (im[..., 0] == OL[0]) & (im[..., 1] == OL[1]) & (im[..., 2] == OL[2]) & (im[..., 3] > 0)
    # eyes around y 35-44, two clusters
    ys, xs = np.where(ol)
    eye_pts = [(int(x), int(y)) for x, y in zip(xs, ys) if 35 <= y <= 44 and 18 <= x <= 46]
    mouth_pts = [(int(x), int(y)) for x, y in zip(xs, ys) if 44 <= y <= 52 and 24 <= x <= 40]
    def centroid(pts, default):
        if not pts:
            return default
        return [int(round(sum(p[0] for p in pts) / len(pts))),
                int(round(sum(p[1] for p in pts) / len(pts)))]
    left = [p for p in eye_pts if p[0] < 32]
    right = [p for p in eye_pts if p[0] >= 32]
    # mouth only the lower cluster (exclude leftover eye if any)
    return {
        'eyeL': centroid(left, [26, 40]),
        'eyeR': centroid(right, [38, 40]),
        'mouth': centroid(mouth_pts, [32, 47]),
    }


if __name__ == '__main__':
    from PIL import Image
    draft = np.array(Image.open(
        '/workspace/game-design/visual_qa/drafts/idle_quiet_sit/idle_quiet_sit_draft_L_1x.png'))
    im = pose_idle_quiet(0)
    # compare body region
    d = np.abs(im.astype(int) - draft.astype(int))
    mask = (draft[..., 3] > 0) | (im[..., 3] > 0)
    print('disagree px', int((d.sum(-1) > 0).sum()), 'of', int(mask.sum()))
    print('mean abs rgb where both opaque',
          float(d[(im[...,3]>0)&(draft[...,3]>0),:3].mean()) if ((im[...,3]>0)&(draft[...,3]>0)).any() else 'n/a')
    # aspect
    a = im[..., 3] > 0
    ys, xs = np.where(a)
    print('bbox', xs.min(), ys.min(), xs.max(), ys.max(),
          'wh', xs.max()-xs.min()+1, ys.max()-ys.min()+1,
          'aspect', (xs.max()-xs.min()+1)/(ys.max()-ys.min()+1))
    Image.fromarray(im).resize((512, 512), Image.NEAREST).save('/tmp/art_fix1_dev/sit0_8x.png')
    # side by side vs draft
    pair = Image.new('RGBA', (64*8*2+16, 64*8), (20, 22, 40, 255))
    pair.paste(Image.fromarray(draft).resize((512,512), Image.NEAREST), (0,0))
    pair.paste(Image.fromarray(im).resize((512,512), Image.NEAREST), (512+16,0))
    pair.save('/tmp/art_fix1_dev/sit0_vs_draft.png')
    print('wrote compare')


# ----- build atlases -----
def resize_pet(im64, size, pivot):
    """Return (image, scale, dx, dy). Anchors: round(L * scale) + (dx, dy)."""
    if size == 64:
        return im64, 1.0, 0, 0
    scaled = scale_to(im64, size, size)
    a = scaled[..., 3] > 0
    if not a.any():
        return scaled, size / 64.0, 0, 0
    rows = np.where(a.any(1))[0]
    foot = rows[-1]
    target_foot = min(size - 1, pivot[1] + 2)
    # Same rule as other m2 clips: S/M foot = pivot+2 (S 31, M 47). L is native, foot 60.
    dy = target_foot - foot
    if dy:
        scaled = shift(scaled, dy=dy)
    dx = 0
    a = scaled[..., 3] > 0
    if a.any():
        xs = np.where(a.any(0))[0]
        cx = (xs[0] + xs[-1]) / 2
        dx = int(round(pivot[0] - cx))
        if dx:
            scaled = shift(scaled, dx=dx)
    return harden_alpha(scaled), size / 64.0, dx, dy


def map_anchors(anc, scale, dx, dy, size):
    out = {}
    for k, v in anc.items():
        x = int(round(v[0] * scale + dx))
        y = int(round(v[1] * scale + dy))
        out[k] = [max(0, min(size - 1, x)), max(0, min(size - 1, y))]
    return out


def emissive_of(f):
    e = np.zeros_like(f)
    glow = (f[..., 3] > 0) & (
        ((f[..., 0] >= 250) & (f[..., 1] >= 200) & (f[..., 2] <= 160)) |
        ((f[..., 0] >= 255) & (f[..., 1] >= 230) & (f[..., 2] >= 180) & (f[..., 2] <= 230))
    )
    e[glow] = f[glow]
    return e


CLIP_QUIET = dict(zh='招牌·文靜', frames=6, fps=6, loop=True, kind='idle', personality='quiet')


def build_idle_quiet(out_root: str) -> dict:
    import os, json
    hd = os.path.join(out_root, 'art-pet/sprites/tuanrong/motion/m2')
    os.makedirs(hd, exist_ok=True)
    written = []
    for sz, szm in SIZES.items():
        frs, ancs = [], []
        for i in range(CLIP_QUIET['frames']):
            im_l = pose_idle_quiet(i)
            im, sc, dx, dy = resize_pet(im_l, szm['size'], szm['pivot'])
            frs.append(im)
            ancs.append(map_anchors(anchors_of(im_l), sc, dx, dy, szm['size']))
        names = [f'idle_quiet_{i+1:02d}' for i in range(CLIP_QUIET['frames'])]
        norms = [normal_from_sprite(f) for f in frs]
        ems = [emissive_of(f) for f in frs]
        atl, fj, W, H = pack_atlas(frs, names, pad=2, cols=6)
        natl, _, _, _ = pack_atlas(norms, names, pad=2, cols=6, bg_n=True)
        eatl, _, _, _ = pack_atlas(ems, names, pad=2, cols=6)
        stem = f'atlas_radiant_idle_quiet_{sz}'
        save_png(f'{hd}/{stem}.png', atl)
        save_png(f'{hd}/{stem}_n.png', natl)
        save_png(f'{hd}/{stem}_emissive.png', eatl)
        for n, rec in fj.items():
            rec['pivotPx'] = {'x': szm['pivot'][0], 'y': szm['pivot'][1]}
        for n, anc in zip(names, ancs):
            fj[n]['anchors'] = anc
        js = dict(
            format='m2.petclip.atlas/1', form='radiant', size=sz,
            frameSize=szm['size'], pivotPx=list(szm['pivot']),
            clip='idle_quiet', zh=CLIP_QUIET['zh'],
            frames=fj, fps=CLIP_QUIET['fps'], loop=CLIP_QUIET['loop'],
            frameCount=CLIP_QUIET['frames'], kind=CLIP_QUIET['kind'],
            personality=CLIP_QUIET['personality'],
            pose='sit', poseNote='文靜改為坐低收腳（Kurt 2026-11-11 批坐低草稿）',
            meta=dict(image=f'{stem}.png', normal=f'{stem}_n.png',
                      emissive=f'{stem}_emissive.png',
                      size={'w': W, 'h': H}, padding=2, form='radiant',
                      frameSize=szm['size'], pivotPx=list(szm['pivot'])),
        )
        json.dump(js, open(f'{hd}/{stem}.json', 'w'), ensure_ascii=False, indent=1)
        written += [f'{hd}/{stem}.png', f'{hd}/{stem}_n.png',
                    f'{hd}/{stem}_emissive.png', f'{hd}/{stem}.json']
        print(f'  idle_quiet {sz}', flush=True)
    return dict(written=written)
