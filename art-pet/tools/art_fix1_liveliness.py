#!/usr/bin/env python3
"""細佬（A1）同三位訪客嘅共用生命感 clip：scratch／sneeze／sniff。
48px，各自外形／色／pivot；幀數同時機跟團絨 liveliness。程序化（Pillow／numpy）。"""
from __future__ import annotations
import os, json, math
import numpy as np
from PIL import Image
from m1_common import (
    PAL, V3, rgba, pset, fill_ellipse, fill_rect, outline_sel, harden_alpha,
    blit, shift, save_png, pack_atlas, normal_from_sprite,
)

OL = PAL['outline']  # (59,42,62) visitors
A1_OL = (34, 26, 44)
A1_NAVY = (26, 48, 89)
A1_BODY = (150, 217, 247)
A1_BODY_L = (175, 236, 252)
A1_BODY_D = (108, 165, 222)
A1_BLUSH = (223, 154, 173)
A1_WHITE = (255, 255, 255)
A1_GOLD = (255, 214, 90)
A1_GOLD_D = (232, 168, 60)
A1_STEM = (92, 60, 40)

# visitor palettes (same as build_m2_visitors.py)
SNAIL = dict(shell=(242, 166, 150), shell_l=(255, 214, 196), shell_d=(214, 120, 110),
             body=(246, 221, 176), body_l=(255, 239, 196),
             cap=(66, 90, 168), cap_l=(110, 140, 210), bag=(70, 110, 190), bag_l=(140, 180, 230))
GRAN = dict(cap=(214, 72, 86), cap_l=(240, 126, 150), spot=(255, 244, 230),
            face=(255, 239, 196), body=(190, 150, 200), body_d=(150, 110, 168),
            cane=(122, 86, 58), cane_l=(176, 126, 72))
FLY = dict(body=(120, 206, 176), body_l=(180, 240, 210), body_d=(70, 150, 130),
           wing=(200, 230, 240), wing_l=(230, 248, 255),
           lamp=(255, 233, 138), lamp_d=(242, 166, 90), box=(176, 126, 72), box_l=(222, 180, 116))

LAST_ANCHORS = {'eyeL': [24, 30], 'eyeR': [28, 30], 'mouth': [24, 34]}
ANCHORS_ACCUM = []

CLIPS = {
    'scratch': dict(zh='抓癢', frames=6, fps=8, loop=False),
    'sneeze':  dict(zh='噴嚏', frames=5, fps=8, loop=False),
    'sniff':   dict(zh='嗅地', frames=4, fps=6, loop=False),
}

A1_CANDIDATES = [
    '/workspace/game-design/art-pet/sprites/series2/actions/A1_idle.png',
    '/workspace/live-s2/src/glimmer-a/art/series2/actions/A1_idle.png',
]


def disc(im, cx, cy, r, col, a=255):
    fill_ellipse(im, cx, cy, r, r, col, a)


def _squash(im, cy, sy, sx=1.0):
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
    h, w = im.shape[:2]
    out = rgba(h, w)
    for y in range(h):
        dx = int(round((pivot_y - y) * shear))
        for xx in range(w):
            x = xx - dx
            if 0 <= x < w and im[y, x, 3]:
                out[y, xx] = im[y, x]
    return out


def pin_foot(im, target, cx=None, with_delta=False):
    a = im[..., 3] > 0
    dx = dy = 0
    if a.any():
        rows = np.where(a.any(1))[0]
        dy = target - int(rows[-1])
        if dy:
            im = shift(im, dy=dy)
        if cx is not None:
            a = im[..., 3] > 0
            if a.any():
                xs = np.where(a.any(0))[0]
                mid = (int(xs[0]) + int(xs[-1])) / 2
                dx = int(round(cx - mid))
                if dx:
                    im = shift(im, dx=dx)
    im = harden_alpha(im)
    if with_delta:
        return im, dx, dy
    return im


def shift_anc(anc, dx, dy):
    return {k: [v[0] + dx, v[1] + dy] for k, v in anc.items()}


def face_anchors(im, box, ink=None):
    """Anchors from ink pixels inside box=(x0,y0,x1,y1), before outline_sel."""
    x0, y0, x1, y1 = box
    h, w = im.shape[:2]
    rgb = im[..., :3]
    a = im[..., 3] > 0
    if ink is not None:
        m = a & np.all(rgb == np.array(ink, dtype=np.uint8), axis=-1)
    else:
        # dark face ink: olive-black or visitor pupil
        m = a & (rgb[..., 0].astype(int) < 70) & (rgb[..., 1].astype(int) < 70)
    m[:max(0, y0), :] = False
    m[min(h, y1 + 1):, :] = False
    m[:, :max(0, x0)] = False
    m[:, min(w, x1 + 1):] = False
    ys, xs = np.where(m)
    mid = (x0 + x1) / 2
    pts = list(zip(xs.tolist(), ys.tolist()))
    def c(pts, default):
        if not pts:
            return default
        return [int(round(sum(p[0] for p in pts) / len(pts))),
                int(round(sum(p[1] for p in pts) / len(pts)))]
    left = [p for p in pts if p[0] < mid]
    right = [p for p in pts if p[0] >= mid]
    al = c(left, [int(mid) - 4, (y0 + y1) // 2])
    ar = c(right, [int(mid) + 4, (y0 + y1) // 2])
    mouth = [p for p in pts if p[1] >= al[1] + 3]
    am = c(mouth, [int(round(mid)), al[1] + 4])
    return {'eyeL': al, 'eyeR': ar, 'mouth': am}


def load_a1_idle0():
    for p in A1_CANDIDATES:
        if os.path.exists(p):
            im = np.array(Image.open(p).convert('RGBA'))
            return harden_alpha(im[:, 0:48].copy())
    raise SystemExit('搵唔到 A1_idle.png')


def a1_arm(im, hx, hy, phase='up'):
    """Small rounded arm + hand in A1 blues. phase: side/up/scratch_l/scratch_r/down."""
    jitter = {'side': (0, 0), 'up': (0, 0), 'scratch_l': (-1, 0),
              'scratch_r': (1, 1), 'down': (0, 1)}.get(phase, (0, 0))
    hx, hy = hx + jitter[0], hy + jitter[1]
    fill_ellipse(im, hx, hy, 4, 3, A1_BODY_D)
    fill_ellipse(im, hx, hy, 3, 2, A1_BODY)
    pset(im, hx - 1, hy - 1, A1_BODY_L)
    # fingers
    pset(im, hx + 2, hy - 2, A1_BODY)
    pset(im, hx + 3, hy - 1, A1_BODY_L)
    if phase.startswith('scratch'):
        pset(im, hx + 4, hy - 3, A1_BODY_L)
        pset(im, hx + 5, hy - 2, (195, 240, 253))
    return im


def a1_face(im, kind='idle'):
    """Replace baked face features in the drop's face band."""
    # clear A1_OL in the face box, keep blush
    for y in range(32, 43):
        for x in range(14, 36):
            p = im[y, x]
            if p[3] and tuple(p[:3]) == A1_OL:
                im[y, x, :3] = A1_BODY
    def eye_open(x, y):
        for dy in range(0, 4):
            for dx in range(0, 4):
                pset(im, x + dx, y + dy, A1_OL)
        pset(im, x, y, A1_WHITE)
        pset(im, x + 1, y, A1_WHITE)
    def eye_squint(x, y):
        for dx in range(0, 4):
            pset(im, x + dx, y + 1, A1_OL)
            pset(im, x + dx, y + 2, A1_OL)
    def eye_close(x, y):
        for dx in range(0, 4):
            pset(im, x + dx, y + 2, A1_OL)
    lx, rx, ey = 17, 29, 34
    if kind in ('idle', 'happy', 'open'):
        eye_open(lx, ey); eye_open(rx, ey)
    elif kind == 'squint':
        eye_squint(lx, ey); eye_squint(rx, ey)
    else:  # blink / sneeze
        eye_close(lx, ey); eye_close(rx, ey)
    # mouth
    if kind in ('idle', 'open'):
        pset(im, 22, 39, A1_OL); pset(im, 25, 39, A1_OL)
        pset(im, 23, 40, A1_OL); pset(im, 24, 40, A1_OL)
    elif kind == 'happy':
        pset(im, 21, 39, A1_OL); pset(im, 26, 39, A1_OL)
        pset(im, 22, 40, A1_OL); pset(im, 23, 40, A1_OL)
        pset(im, 24, 40, A1_OL); pset(im, 25, 40, A1_OL)
    elif kind == 'o':
        pset(im, 23, 39, A1_OL); pset(im, 24, 39, A1_OL)
        pset(im, 22, 40, A1_OL); pset(im, 25, 40, A1_OL)
        pset(im, 23, 41, A1_OL); pset(im, 24, 41, A1_OL)
    elif kind == 'squint':
        pset(im, 22, 40, A1_OL); pset(im, 23, 40, A1_OL)
        pset(im, 24, 40, A1_OL); pset(im, 25, 40, A1_OL)
    else:
        pset(im, 22, 40, A1_OL); pset(im, 23, 40, A1_OL)
        pset(im, 24, 40, A1_OL); pset(im, 25, 40, A1_OL)
    # blush stays (not cleared)
    return im


def a1_spray(im, i):
    """Sneeze mist to the right of the face."""
    base = [(34, 38), (36, 36), (38, 39), (40, 37), (37, 41)]
    n = [0, 0, 5, 3, 1][i] if i < 5 else 0
    cols = [(195, 240, 253), (239, 252, 254), (175, 236, 252)]
    for k, (x, y) in enumerate(base[:n]):
        disc(im, x, y, 1, cols[k % 3])
        pset(im, x + 1, y - 1, cols[(k + 1) % 3])
    return im


def pose_a1(clip, i):
    global LAST_ANCHORS
    im = load_a1_idle0().copy()
    if clip == 'scratch':
        # arm rises to the upper-right of the drop (near gold tip / head)
        phases = ['side', 'up', 'scratch_l', 'scratch_r', 'scratch_l', 'down']
        faces = ['idle', 'squint', 'squint', 'squint', 'squint', 'happy']
        pos = [(34, 36), (32, 26), (30, 20), (31, 19), (29, 20), (34, 34)]
        im = a1_face(im, faces[i])
        if i >= 1:
            a1_arm(im, pos[i][0], pos[i][1], phases[i])
        LAST_ANCHORS = face_anchors(im, (15, 28, 35, 43), ink=A1_OL)
        im = outline_sel(im, A1_OL)
        im, dx, dy = pin_foot(im, 46, 24, with_delta=True)
        LAST_ANCHORS = shift_anc(LAST_ANCHORS, dx, dy)
        return im
    if clip == 'sneeze':
        sy = [1.04, 1.08, 0.82, 0.94, 1.0][i]
        sx = [0.96, 0.92, 1.14, 1.04, 1.0][i]
        dy = [0, -1, 2, 1, 0][i]
        im = shift(_squash(im, 40, sy, sx), dy=dy)
        face = ['o', 'blink', 'o', 'squint', 'happy'][i]
        im = a1_face(im, face)
        im = a1_spray(im, i)
        LAST_ANCHORS = face_anchors(im, (15, 24, 36, 44), ink=A1_OL)
        im = outline_sel(im, A1_OL)
        im, dx, dy = pin_foot(im, 46, 24, with_delta=True)
        LAST_ANCHORS = shift_anc(LAST_ANCHORS, dx, dy)
        return im
    if clip == 'sniff':
        sy = [0.92, 0.80, 0.78, 1.0][i]
        lean = [0.04, 0.10, 0.12, 0.0][i]
        dy = [2, 4, 4, 0][i]
        im = shift(_lean(_squash(im, 40, sy, 1.06 if sy < 0.9 else 1.0), lean, 42), dy=dy)
        face = ['squint', 'squint', 'squint', 'happy'][i]
        im = a1_face(im, face)
        LAST_ANCHORS = face_anchors(im, (14, 24, 36, 45), ink=A1_OL)
        im = outline_sel(im, A1_OL)
        im, dx, dy = pin_foot(im, 46, 24, with_delta=True)
        LAST_ANCHORS = shift_anc(LAST_ANCHORS, dx, dy)
        return im
    raise ValueError(clip)


# ---------- visitors: idle-like bodies + motion ----------
def vis_eyes(im, x, y, kind='idle'):
    if kind == 'happy':
        for dx in (0, 6):
            pset(im, x + dx, y, OL); pset(im, x + dx + 1, y, OL)
            pset(im, x + dx - 1, y + 1, OL); pset(im, x + dx + 2, y + 1, OL)
        return
    if kind in ('closed', 'squint', 'blink'):
        for dx in (0, 6):
            pset(im, x + dx, y, OL); pset(im, x + dx + 1, y, OL)
        return
    for dx in (0, 6):
        pset(im, x + dx, y, (40, 32, 48))
        pset(im, x + dx + 1, y, (40, 32, 48))
        pset(im, x + dx, y + 1, (40, 32, 48))
        pset(im, x + dx + 1, y + 1, (40, 32, 48))
        pset(im, x + dx, y, PAL['white'])


def vis_blush(im, x, y):
    pset(im, x, y, PAL['blush']); pset(im, x + 7, y, PAL['blush'])


def vis_hand(im, hx, hy, col=None):
    col = col or PAL['cream2']
    hi = PAL['cream3'] if col == PAL['cream2'] else col
    fill_ellipse(im, hx, hy, 3, 3, col)
    fill_ellipse(im, hx, hy, 2, 2, hi)
    pset(im, hx - 1, hy - 1, hi)
    pset(im, hx + 2, hy - 1, col)
    pset(im, hx + 1, hy - 2, hi)


def snail_body(i, motion, face='idle'):
    """Draw snail on 48x48, visual foot ~40, pivot (22,40) = vis_bot."""
    im = rgba(48, 48)
    bob = motion.get('bob', 0)
    sway = motion.get('sway', 0)
    nod = motion.get('nod', 0)
    cx, cy = 18 + sway, 22 + bob  # shell
    fill_ellipse(im, cx, cy, 11, 10, SNAIL['shell_d'])
    fill_ellipse(im, cx, cy, 10, 9, SNAIL['shell'])
    fill_ellipse(im, cx - 2, cy - 2, 5, 4, SNAIL['shell_l'])
    pset(im, cx, cy, SNAIL['shell_d']); pset(im, cx + 2, cy + 1, SNAIL['shell_d'])
    hx, hy = 30 + sway, 24 + bob + nod
    fill_ellipse(im, hx, hy + 4, 8, 6, SNAIL['body'])
    fill_ellipse(im, hx + 1, hy, 7, 6, SNAIL['body_l'])
    fill_ellipse(im, hx + 1, hy - 5, 6, 4, SNAIL['cap'])
    fill_ellipse(im, hx + 1, hy - 6, 5, 3, SNAIL['cap_l'])
    pset(im, hx - 1, hy - 10, SNAIL['cap']); pset(im, hx - 1, hy - 11, SNAIL['cap'])
    disc(im, hx - 1, hy - 12, 1, SNAIL['cap_l'])
    pset(im, hx + 3, hy - 10, SNAIL['cap']); pset(im, hx + 3, hy - 11, SNAIL['cap'])
    disc(im, hx + 3, hy - 12, 1, SNAIL['cap_l'])
    vis_eyes(im, hx - 2, hy - 1, face)
    vis_blush(im, hx - 3, hy + 2)
    fill_rect(im, hx - 2, hy + 3, hx + 4, hy + 9, SNAIL['bag'])
    fill_rect(im, hx - 1, hy + 4, hx + 3, hy + 8, SNAIL['bag_l'])
    return im, (hx, hy)


def granny_body(i, motion, face='idle'):
    im = rgba(48, 48)
    nod = motion.get('nod', 0)
    bob = motion.get('bob', 0)
    cx, cy = 20, 14 + nod + bob
    fill_ellipse(im, cx, cy, 16, 10, GRAN['cap'])
    fill_ellipse(im, cx, cy - 2, 14, 8, GRAN['cap_l'])
    for sx, sy in ((12, 10), (20, 8), (26, 11), (16, 13), (24, 14)):
        disc(im, sx, sy + nod + bob, 2, GRAN['spot'])
    fill_ellipse(im, 20, 30 + (nod + bob) // 2, 9, 8, GRAN['body_d'])
    fill_ellipse(im, 20, 28 + (nod + bob) // 2, 8, 7, GRAN['face'])
    fill_ellipse(im, 20, 34 + (nod + bob) // 2, 8, 6, GRAN['body'])
    vis_eyes(im, 16, 26 + (nod + bob) // 2, face)
    vis_blush(im, 15, 29 + (nod + bob) // 2)
    for y in range(22 + nod + bob, 46):
        pset(im, 32, y, GRAN['cane'])
        pset(im, 33, y, GRAN['cane_l'])
    fill_ellipse(im, 32, 22 + nod + bob, 3, 2, GRAN['cane_l'])
    return im, (20, 28 + (nod + bob) // 2)


def fly_body(i, motion, face='idle'):
    im = rgba(48, 48)
    hover = motion.get('hover', -1)
    wf = motion.get('wing', 0)
    cx, cy = 24, 26 + hover
    fill_ellipse(im, cx, cy, 10, 11, FLY['body_d'])
    fill_ellipse(im, cx, cy - 1, 9, 10, FLY['body'])
    fill_ellipse(im, cx - 2, cy - 3, 4, 4, FLY['body_l'])
    vis_eyes(im, cx - 4, cy - 2, face)
    vis_blush(im, cx - 5, cy + 2)
    fill_ellipse(im, cx - 8, cy - 8 + wf, 7, 5, FLY['wing'])
    fill_ellipse(im, cx - 8, cy - 8 + wf, 5, 3, FLY['wing_l'])
    fill_ellipse(im, cx + 8, cy - 9 - wf, 6, 5, FLY['wing'])
    fill_ellipse(im, cx + 8, cy - 9 - wf, 4, 3, FLY['wing_l'])
    # jar held at side (rest, not shaking a lot)
    jx, jy = cx + 11 + motion.get('jx', 0), cy + 3 + motion.get('jy', 0)
    fill_ellipse(im, jx, jy, 5, 7, (180, 200, 210))
    fill_ellipse(im, jx, jy, 4, 6, (220, 240, 230))
    disc(im, jx, jy + 1, 3, FLY['lamp'])
    disc(im, jx - 1, jy, 2, FLY['lamp_d'] if i % 2 else V3['goldhi'])
    pset(im, jx - 1, jy - 1, V3['goldhi'])
    fill_rect(im, jx - 2, jy - 7, jx + 3, jy - 5, FLY['box'])
    return im, (cx, cy)


def _spray(im, x, y, n, cols=None):
    cols = cols or [PAL['drop'], PAL['white'], PAL['cream4']]
    pts = [(x, y), (x + 2, y - 2), (x + 4, y + 1), (x + 3, y - 3), (x + 5, y)]
    for k, (px, py) in enumerate(pts[:n]):
        disc(im, px, py, 1, cols[k % len(cols)])
    return im


def pose_visitor(who, clip, i):
    global LAST_ANCHORS
    if who == 'snail_postman':
        if clip == 'scratch':
            nod = [0, 0, -1, 0, -1, 0][i]
            face = 'squint' if 1 <= i <= 4 else 'idle'
            im, (hx, hy) = snail_body(i, dict(nod=nod), face)
            if i >= 1:
                ax, ay = hx - 1, hy - [0, 6, 9, 8, 9, 3][i]
                # short cream arm from chest to cap
                for t_ in range(6):
                    pset(im, hx - 1 + (t_ % 2), hy + 2 - t_, SNAIL['body'])
                    pset(im, hx + (t_ % 2), hy + 2 - t_, SNAIL['body_l'])
                vis_hand(im, ax + [0, 1, 0, 2, -1, 0][i], ay, SNAIL['body_l'])
        elif clip == 'sneeze':
            bob = [0, -1, 2, 1, 0][i]
            face = ['o' if k == 2 else 'closed' if k in (1, 2) else 'happy' if k == 4 else 'idle' for k in range(5)][i]
            # map o -> idle eyes + we'll just use closed/happy
            face = ['idle', 'closed', 'closed', 'idle', 'happy'][i]
            im, (hx, hy) = snail_body(i, dict(bob=bob), face)
            _spray(im, hx + 8, hy, [0, 0, 4, 2, 0][i])
        else:  # sniff
            nod = [3, 8, 9, 0][i]
            face = ['squint', 'squint', 'squint', 'happy'][i]
            im, (hx, hy) = snail_body(i, dict(nod=nod), face)
        # head is on the right of the snail; face box around hx
        LAST_ANCHORS = face_anchors(im, (22, 14, 42, 36))
        im = outline_sel(im, OL)
        im, dx, dy = pin_foot(im, 40, 24, with_delta=True)
        LAST_ANCHORS = shift_anc(LAST_ANCHORS, dx, dy)
        return im
    if who == 'mushroom_granny':
        if clip == 'scratch':
            nod = [0, 0, 1, 0, 1, 0][i]
            face = 'squint' if 1 <= i <= 4 else 'idle'
            im, (hx, hy) = granny_body(i, dict(nod=nod), face)
            if i >= 1:
                # arm from left shoulder up to cap
                for t_ in range(10):
                    pset(im, 13, hy - t_, GRAN['face'])
                    pset(im, 14, hy - t_, GRAN['face'])
                vis_hand(im, 14 + [0, 0, -1, 1, 0, 0][i], 11 + nod, GRAN['face'])
        elif clip == 'sneeze':
            bob = [0, -1, 3, 1, 0][i]
            face = ['idle', 'closed', 'closed', 'idle', 'happy'][i]
            im, (hx, hy) = granny_body(i, dict(bob=bob), face)
            _spray(im, 28, 28 + bob, [0, 0, 4, 2, 0][i])
        else:
            nod = [3, 8, 9, 0][i]
            face = ['squint', 'squint', 'squint', 'happy'][i]
            im, _ = granny_body(i, dict(nod=nod), face)
        LAST_ANCHORS = face_anchors(im, (12, 18, 28, 36))
        im = outline_sel(im, OL)
        im, dx, dy = pin_foot(im, 45, 24, with_delta=True)
        LAST_ANCHORS = shift_anc(LAST_ANCHORS, dx, dy)
        return im
    if who == 'firefly_vendor':
        hover0 = -1
        if clip == 'scratch':
            hover = [hover0, hover0 - 1, hover0, hover0 - 1, hover0, hover0][i]
            wf = [0, 2, 0, -2, 1, 0][i]
            face = 'squint' if 1 <= i <= 4 else 'idle'
            im, (cx, cy) = fly_body(i, dict(hover=hover, wing=wf), face)
            if i >= 1:
                for t_ in range(7):
                    pset(im, cx + 3, cy - 2 - t_, FLY['body'])
                    pset(im, cx + 4, cy - 2 - t_, FLY['body_l'])
                vis_hand(im, cx + 4, cy - 10 + [0, 0, -1, 1, 0, 2][i], FLY['body_l'])
        elif clip == 'sneeze':
            hover = [hover0 - 1, hover0 - 3, hover0 + 3, hover0, hover0][i]
            face = ['idle', 'closed', 'closed', 'idle', 'happy'][i]
            im, (cx, cy) = fly_body(i, dict(hover=hover, wing=[0, 1, 3, 1, 0][i]), face)
            if i == 2:
                im = _squash(im, cy or 26, 0.82, 1.12)
            _spray(im, cx + 8, cy + (4 if i == 2 else 0), [0, 0, 5, 3, 0][i])
        else:
            hover = [hover0, hover0 + 1, hover0 + 1, hover0][i]
            face = ['squint', 'squint', 'squint', 'happy'][i]
            im, _ = fly_body(i, dict(hover=hover, wing=[1, 0, 2, 1][i]), face)
        LAST_ANCHORS = face_anchors(im, (14, 16, 34, 36))
        im = outline_sel(im, OL)
        # 官方 pivot.y=36（實際 vis_bot）。嗅地只准 1px 入土，唔好跟住 vis_bot 改變 target。
        target = 36
        im, dx, dy = pin_foot(im, target, 24, with_delta=True)
        LAST_ANCHORS = shift_anc(LAST_ANCHORS, dx, dy)
        return im
    raise ValueError(who)


def anchors_detect(im, actor='A1'):
    """Per-frame eyeL/eyeR/mouth from face ink, not the silhouette outline."""
    h, w = im.shape[:2]
    a = im[..., 3] > 0
    if not a.any():
        return {'eyeL': [w // 2 - 4, h // 2], 'eyeR': [w // 2 + 4, h // 2], 'mouth': [w // 2, h // 2 + 4]}
    ys, xs = np.where(a)
    y0, y1 = int(ys.min()), int(ys.max())
    x0, x1 = int(xs.min()), int(xs.max())
    mid = (x0 + x1) / 2
    # Face ink: A1 baked outline, visitor pupil, or near-black (not the mid-navy shell/drop outline).
    rgb = im[..., :3].astype(int)
    if actor in ('A1', 'kid'):
        ink = a & (rgb[..., 0] == 34) & (rgb[..., 1] == 26) & (rgb[..., 2] == 44)
        # only interior of the drop, skip the pointed-top stem
        fy0, fy1 = y0 + int(0.35 * (y1 - y0)), y1 - 4
        fx0, fx1 = x0 + 3, x1 - 3
    else:
        pupil = a & (rgb[..., 0] == 40) & (rgb[..., 1] == 32) & (rgb[..., 2] == 48)
        closed = a & (rgb[..., 0] == OL[0]) & (rgb[..., 1] == OL[1]) & (rgb[..., 2] == OL[2])
        # visitor faces sit in the mid body, not the outer silhouette
        fy0, fy1 = y0 + int(0.30 * (y1 - y0)), y0 + int(0.70 * (y1 - y0))
        fx0, fx1 = int(mid) - 12, int(mid) + 12
        # prefer pupils; fall back to short OL segments inside the face box
        ink = pupil
        if ink.sum() < 4:
            ink = np.zeros_like(a)
            ink[fy0:fy1 + 1, max(0, fx0):min(w, fx1 + 1)] = closed[fy0:fy1 + 1, max(0, fx0):min(w, fx1 + 1)]
    band = np.zeros_like(a)
    band[fy0:fy1 + 1, max(0, fx0):min(w, fx1 + 1)] = True
    pts = [(int(x), int(y)) for y, x in zip(*np.where(ink & band))]
    def c(pts, default):
        if not pts:
            return default
        return [int(round(sum(p[0] for p in pts) / len(pts))),
                int(round(sum(p[1] for p in pts) / len(pts)))]
    left = [p for p in pts if p[0] < mid]
    right = [p for p in pts if p[0] >= mid]
    eye_y = (c(left, [0, 0])[1] + c(right, [0, 0])[1]) // 2 if (left or right) else (fy0 + fy1) // 2
    mouth_pts = [p for p in pts if p[1] >= eye_y + 3]
    al = c(left, [int(mid) - 4, eye_y])
    ar = c(right, [int(mid) + 4, eye_y])
    am = c(mouth_pts, [int(round(mid)), al[1] + 4])
    return {'eyeL': al, 'eyeR': ar, 'mouth': am}


def emissive_of(f, firefly=False, a1=False):
    e = np.zeros_like(f)
    if firefly:
        glow = (f[..., 3] > 0) & (f[..., 0] >= 230) & (f[..., 1] >= 180) & (f[..., 2] <= 180)
        e[glow] = f[glow]
        wing = (f[..., 3] > 0) & (f[..., 2] >= 220) & (f[..., 1] >= 220) & (f[..., 0] >= 180)
        e[wing] = (f[wing].astype(np.int16) // 2).astype(np.uint8)
        e[wing, 3] = 255
    elif a1:
        gold = (f[..., 3] > 0) & (f[..., 0] >= 230) & (f[..., 1] >= 160) & (f[..., 2] <= 120)
        e[gold] = f[gold]
        # bubbles / highlights
        hi = (f[..., 3] > 0) & (f[..., 0] >= 230) & (f[..., 1] >= 245) & (f[..., 2] >= 250)
        e[hi] = f[hi]
    else:
        glow = (f[..., 3] > 0) & (f[..., 0] >= 250) & (f[..., 1] >= 220) & (f[..., 2] <= 200)
        e[glow] = f[glow]
    return harden_alpha(e)


def _write_atlas(dir_, stem, frs, names, pivot, meta, fmt, firefly=False, a1=False):
    os.makedirs(dir_, exist_ok=True)
    # anchors must be collected by the caller (same order as frs) via ANCHORS_ACCUM
    ancs = list(ANCHORS_ACCUM) if ANCHORS_ACCUM else [anchors_detect(f, meta.get('id', '')) for f in frs]
    norms = [normal_from_sprite(f) for f in frs]
    ems = [emissive_of(f, firefly=firefly, a1=a1) for f in frs]
    atl, fj, W, H = pack_atlas(frs, names, pad=2, cols=len(frs))
    natl, _, _, _ = pack_atlas(norms, names, pad=2, cols=len(frs), bg_n=True)
    eatl, _, _, _ = pack_atlas(ems, names, pad=2, cols=len(frs))
    save_png(f'{dir_}/{stem}.png', atl)
    save_png(f'{dir_}/{stem}_n.png', natl)
    save_png(f'{dir_}/{stem}_emissive.png', eatl)
    for n, rec in fj.items():
        rec['pivotPx'] = {'x': pivot[0], 'y': pivot[1]}
    for n, anc in zip(names, ancs):
        fj[n]['anchors'] = anc
    js = dict(
        format=fmt, frameSize=48, pivotPx=list(pivot),
        frames=fj, frameCount=len(frs),
        alpha='0/255', normal='OpenGL Y+（綠＝上）',
        meta=dict(image=f'{stem}.png', normal=f'{stem}_n.png',
                  emissive=f'{stem}_emissive.png',
                  size={'w': W, 'h': H}, padding=2, frameSize=48, pivotPx=list(pivot)),
    )
    js.update(meta)
    json.dump(js, open(f'{dir_}/{stem}.json', 'w'), ensure_ascii=False, indent=1)
    return [f'{dir_}/{stem}.png', f'{dir_}/{stem}_n.png', f'{dir_}/{stem}_emissive.png', f'{dir_}/{stem}.json']


def build_kid(out_root):
    d = os.path.join(out_root, 'art-pet/sprites/series2/liveliness')
    written, items = [], []
    for cid, cm in CLIPS.items():
        global ANCHORS_ACCUM
        ANCHORS_ACCUM = []
        frs = []
        for i in range(cm['frames']):
            frs.append(pose_a1(cid, i))
            ANCHORS_ACCUM.append(dict(LAST_ANCHORS))
        names = [f'{cid}_{i+1:02d}' for i in range(cm['frames'])]
        stem = f'atlas_A1_{cid}'
        meta = dict(id='A1', zh='細佬', actor='kid', form='A1',
                    clip=cid, clip_zh=cm['zh'], fps=cm['fps'], loop=cm['loop'],
                    size='M', facing='朝右；朝左＝scaleX −1，法線 R→255−R',
                    note='細佬 A1 外形／色；48px；pivot (24,45)；時機同團絨 liveliness。')
        written += _write_atlas(d, stem, frs, names, (24, 45), meta,
                                'art_fix1.kid.liveliness.atlas/1', a1=True)
        items.append(dict(id='A1', clip=cid, zh=cm['zh'], atlas=f'{stem}.json',
                          pivotPx=[24, 45], frameSize=48, fps=cm['fps'],
                          loop=cm['loop'], frameCount=cm['frames']))
        print(f'  kid A1 {cid}', flush=True)
    idx = dict(format='art_fix1.kid.liveliness/1', actor='A1', zh='細佬',
               pivotPx=[24, 45], frameSize=48, size='M',
               note='抓癢／噴嚏／嗅地用細佬自己嘅 A1 水滴外形，唔好再套團絨 L。時機同團絨 scratch／sneeze／sniff。',
               clips=CLIPS, items=items)
    json.dump(idx, open(f'{d}/clips.json', 'w'), ensure_ascii=False, indent=1)
    written.append(f'{d}/clips.json')
    return written


VISITORS = [
    dict(id='snail_postman', zh='蝸牛郵差', pivot=(22, 40)),
    dict(id='mushroom_granny', zh='蘑菇婆婆', pivot=(24, 45)),
    dict(id='firefly_vendor', zh='螢火小販', pivot=(24, 36)),
]


def build_visitors(out_root):
    d = os.path.join(out_root, 'art-pet/sprites/visitors/m2')
    written, items = [], []
    for v in VISITORS:
        for cid, cm in CLIPS.items():
            global ANCHORS_ACCUM
            ANCHORS_ACCUM = []
            frs = []
            for i in range(cm['frames']):
                frs.append(pose_visitor(v['id'], cid, i))
                ANCHORS_ACCUM.append(dict(LAST_ANCHORS))
            names = [f'{cid}_{i+1:02d}' for i in range(cm['frames'])]
            stem = f"atlas_{v['id']}_{cid}"
            meta = dict(id=v['id'], zh=v['zh'], clip=cid, clip_zh=cm['zh'],
                        fps=cm['fps'], loop=cm['loop'], size='M',
                        facing='朝右；朝左＝scaleX −1，法線 R→255−R',
                        note=f"{v['zh']} 外形／色；48px；pivot {list(v['pivot'])}；時機同團絨 liveliness。")
            written += _write_atlas(d, stem, frs, names, v['pivot'], meta,
                                    'art_fix1.visitor.liveliness.atlas/1',
                                    firefly=(v['id'] == 'firefly_vendor'))
            items.append(dict(id=v['id'], zh=v['zh'], clip=cid, clip_zh=cm['zh'],
                              atlas=f'{stem}.json', pivotPx=list(v['pivot']),
                              frameSize=48, fps=cm['fps'], loop=cm['loop'],
                              frameCount=cm['frames']))
            print(f"  visitor {v['id']} {cid}", flush=True)
    idx = dict(format='art_fix1.visitor.liveliness/1', count=3,
               note='三位 M2 訪客各自外形嘅 scratch／sneeze／sniff，48px，pivot 同招牌動作一致。時機同團絨。',
               clips=CLIPS, items=items)
    json.dump(idx, open(f'{d}/liveliness_clips.json', 'w'), ensure_ascii=False, indent=1)
    written.append(f'{d}/liveliness_clips.json')
    return written
