#!/usr/bin/env python3
"""build_m1_icons.py — M1 需要／表情／事件 icon（34）＋夢泡泡框＋狩獵銅證 4。
V3-A：金光深藍、金幼線、像素打光。sprite alpha 0/255；泡泡框可用真 alpha。@3x＝32px 1:1（同 kit v3）。"""
import os, sys, json, math
import numpy as np
from PIL import Image
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from m1_common import (V3, PAL, HUNT, rgba, pset, fill_rect, fill_ellipse,
                       outline_sel, harden_alpha, glints, blit, save_png, pack_atlas)

# ---------- 低階筆 ----------
def disc(im, cx, cy, r, col, a=255):
    fill_ellipse(im, cx, cy, r, r, col, a)

def tri(im, pts, col, a=255):
    """填充凸三角形（掃描線）。"""
    pts = [(int(x), int(y)) for x, y in pts]
    ys = [p[1] for p in pts]
    for y in range(min(ys), max(ys) + 1):
        xs = []
        for i in range(3):
            x0, y0 = pts[i]; x1, y1 = pts[(i + 1) % 3]
            if y0 == y1: continue
            if (y0 <= y < y1) or (y1 <= y < y0):
                t = (y - y0) / (y1 - y0)
                xs.append(int(round(x0 + t * (x1 - x0))))
        if len(xs) >= 2:
            fill_rect(im, min(xs), y, max(xs) + 1, y + 1, col, a)

def line(im, x0, y0, x1, y1, col, a=255):
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx - dy
    while True:
        pset(im, x0, y0, col, a)
        if x0 == x1 and y0 == y1: break
        e2 = 2 * err
        if e2 > -dy: err -= dy; x0 += sx
        if e2 < dx: err += dx; y0 += sy

def gold_ring(im, cx, cy, r, t=1):
    # 外圈金深、內圈金亮
    for rr, c in ((r, V3['golddk']), (r - 0.4, V3['gold']), (r - 1, V3['goldhi'])):
        if rr <= 0: continue
        tmp = rgba(*im.shape[:2])
        disc(tmp, cx, cy, rr, c)
        if rr - t > 0:
            disc(tmp, cx, cy, rr - t, (0, 0, 0, 0), 0)
        m = tmp[..., 3] > 0
        im[m] = tmp[m]

def plate(im, cx=16, cy=16, r=15, navy=True):
    """可選深藍底圓（部分 icon 用透明底，保持同 v3 icon 多數做法：透明底＋深外框）。呢度預設唔鋪滿底，只畫主體。"""
    return im

def finish(im, glint_pts=None, outline=True):
    if outline:
        outline_sel(im, (48, 28, 56))
    if glint_pts:
        glints(im, glint_pts, V3['goldhi'])
    return harden_alpha(im)

# ---------- 34 icon＋銅證＋泡泡 ----------
def ic_need_eat():
    im = rgba(32)
    # 碗
    fill_ellipse(im, 16, 20, 11, 6, V3['navy3'])
    fill_ellipse(im, 16, 19, 10, 5, V3['cream'])
    fill_ellipse(im, 16, 18, 9, 4, PAL['cream2'])
    # 湯
    fill_ellipse(im, 16, 17, 8, 3, PAL['orange'])
    fill_ellipse(im, 16, 16, 6, 2, PAL['glow'])
    # 蒸汽 3 縷
    for x, y in ((11, 10), (16, 8), (21, 10)):
        pset(im, x, y, V3['mute']); pset(im, x, y - 1, V3['cream']); pset(im, x + 1, y - 2, V3['mute'])
    # 匙
    line(im, 23, 8, 20, 16, V3['gold']); pset(im, 23, 7, V3['goldhi']); fill_ellipse(im, 19, 17, 2, 2, V3['gold'])
    return finish(im, [(13, 16), (18, 15)])

def ic_need_play():
    im = rgba(32)
    # 斜放絨球（原創，唔抄現有 play 菱形）
    disc(im, 15, 17, 9, PAL['peach1'])
    disc(im, 13, 15, 7, PAL['cream2'])
    disc(im, 12, 14, 3, PAL['cream4'])
    # 小葉芽
    fill_ellipse(im, 15, 8, 3, 4, PAL['leaf'])
    pset(im, 15, 5, PAL['leaf_d']); pset(im, 16, 6, PAL['leaf'])
    # 星星玩具
    pts = [(24, 10), (26, 16), (20, 13), (28, 13), (22, 16)]
    for x, y in pts:
        pset(im, x, y, V3['amber'])
    pset(im, 24, 13, V3['goldhi'])
    return finish(im, [(11, 13), (25, 11)])

def ic_need_sleep():
    im = rgba(32)
    # 月牙
    disc(im, 14, 16, 10, V3['gold'])
    disc(im, 18, 14, 8, (0, 0, 0, 0), 0)
    # 把被挖走嘅再清 alpha
    m = (im[..., 3] > 0) & (im[..., 0] < 8)
    im[m] = 0
    # 重畫月（用遮罩）
    im[:] = 0
    tmp = rgba(32); disc(tmp, 14, 16, 10, V3['gold']); disc(tmp, 19, 13, 8, (0, 0, 0, 0), 0)
    # 挖空：以第二圓為洞
    base = rgba(32); disc(base, 14, 16, 10, V3['gold'])
    hole = rgba(32); disc(hole, 19, 13, 8, (255, 255, 255))
    keep = (base[..., 3] > 0) & (hole[..., 3] == 0)
    im[keep] = base[keep]
    # 月亮邊
    for x, y in ((8, 12), (7, 16), (9, 20), (12, 22)):
        if im[y, x, 3]: im[y, x, :3] = V3['goldhi']
    # zzz
    def zed(x, y, s, col):
        fill_rect(im, x, y, x + s, y + 1, col)
        line(im, x + s - 1, y, x, y + s - 1, col)
        fill_rect(im, x, y + s - 1, x + s, y + s, col)
    zed(20, 8, 5, V3['violet']); zed(24, 4, 4, PAL['zzz']); zed(18, 5, 3, V3['mute'])
    return finish(im, [(10, 14)])

def ic_need_pet():
    im = rgba(32)
    # 手掌輕摸
    fill_ellipse(im, 16, 20, 10, 7, PAL['peach1'])
    fill_ellipse(im, 16, 19, 8, 5, PAL['peach2'])
    # 四指
    for x in (9, 13, 19, 23):
        fill_ellipse(im, x, 12, 3, 5, PAL['peach1'])
        fill_ellipse(im, x, 10, 2, 3, PAL['peach2'])
    # 心
    disc(im, 14, 8, 3, V3['rose']); disc(im, 18, 8, 3, V3['rose'])
    tri(im, [(11, 9), (21, 9), (16, 16)], V3['rose'])
    pset(im, 15, 8, V3['cream'])
    return finish(im, [(15, 8), (12, 18)])

def _face_base(im, cx=16, cy=18, r=10, body=None):
    body = body or PAL['cream2']
    disc(im, cx, cy, r, body)
    disc(im, cx - 2, cy - 2, r - 3, PAL['cream3'])
    # 腮
    fill_ellipse(im, cx - 5, cy + 2, 2, 1, PAL['blush'])
    fill_ellipse(im, cx + 5, cy + 2, 2, 1, PAL['blush'])
    return im

def ic_expr_lively():
    im = rgba(32)
    _face_base(im)
    # 笑眼 ^ ^
    line(im, 10, 16, 12, 14, PAL['outline']); line(im, 12, 14, 14, 16, PAL['outline'])
    line(im, 18, 16, 20, 14, PAL['outline']); line(im, 20, 14, 22, 16, PAL['outline'])
    # 口
    fill_ellipse(im, 16, 21, 3, 2, PAL['berry'])
    # 雙臂舉起
    line(im, 6, 16, 4, 10, PAL['cream1']); disc(im, 4, 9, 2, PAL['cream2'])
    line(im, 26, 16, 28, 10, PAL['cream1']); disc(im, 28, 9, 2, PAL['cream2'])
    # 火花
    pset(im, 8, 6, V3['amber']); pset(im, 24, 5, V3['goldhi']); pset(im, 16, 4, V3['amber'])
    return finish(im, [(14, 13)])

def ic_expr_quiet():
    im = rgba(32)
    _face_base(im, body=PAL['cream1'])
    # 柔眼 —
    fill_rect(im, 11, 16, 14, 17, PAL['outline'])
    fill_rect(im, 18, 16, 21, 17, PAL['outline'])
    # 小口
    fill_rect(im, 15, 21, 18, 22, PAL['blush_d'])
    # 坐姿小腳
    fill_ellipse(im, 11, 28, 3, 2, PAL['cream0'])
    fill_ellipse(im, 21, 28, 3, 2, PAL['cream0'])
    return finish(im, [(13, 14)])

def ic_expr_diligent():
    im = rgba(32)
    _face_base(im)
    # 專心眼
    pset(im, 12, 16, PAL['outline']); pset(im, 13, 16, PAL['outline'])
    pset(im, 20, 16, PAL['outline']); pset(im, 21, 16, PAL['outline'])
    fill_rect(im, 15, 20, 18, 21, PAL['outline'])
    # 小葉掃／工具
    fill_rect(im, 6, 14, 8, 26, HUNT['straw'])
    fill_ellipse(im, 7, 12, 4, 3, PAL['leaf'])
    fill_ellipse(im, 7, 11, 3, 2, PAL['leaf_d'])
    return finish(im, [(13, 13), (8, 11)])

def ic_expr_lazy():
    im = rgba(32)
    _face_base(im, cy=20, r=9)
    # 瞓眼
    fill_rect(im, 11, 19, 14, 20, PAL['outline'])
    fill_rect(im, 18, 19, 21, 20, PAL['outline'])
    fill_ellipse(im, 16, 23, 2, 1, PAL['blush'])
    # z
    pset(im, 22, 10, PAL['zzz']); pset(im, 23, 11, PAL['zzz'])
    pset(im, 24, 8, V3['violet']); pset(im, 25, 9, V3['violet']); pset(im, 26, 7, V3['violet'])
    return finish(im, [(13, 16)])

def ic_expr_clingy():
    im = rgba(32)
    _face_base(im, cx=14, cy=18, r=8)
    # 第二粒細身挨住
    disc(im, 22, 20, 7, PAL['peach1'])
    disc(im, 21, 18, 3, PAL['peach2'])
    pset(im, 20, 19, PAL['outline']); pset(im, 23, 19, PAL['outline'])
    # 主臉眼
    pset(im, 11, 16, PAL['outline']); pset(im, 16, 16, PAL['outline'])
    fill_ellipse(im, 14, 20, 2, 1, PAL['berry'])
    # 心
    pset(im, 16, 8, V3['rose']); pset(im, 15, 7, V3['rose']); pset(im, 17, 7, V3['rose']); pset(im, 16, 9, V3['rose'])
    return finish(im, [(12, 14), (16, 7)])

def ic_expr_indep():
    im = rgba(32)
    _face_base(im, cx=16, cy=17, r=9)
    # 望側
    pset(im, 13, 16, PAL['outline']); pset(im, 19, 15, PAL['outline']); pset(im, 20, 15, PAL['white'])
    fill_rect(im, 15, 20, 17, 21, PAL['outline'])
    # 望遠小旗／地平
    fill_rect(im, 4, 26, 28, 27, HUNT['grass_d'])
    fill_rect(im, 24, 10, 25, 26, V3['golddk'])
    fill_rect(im, 25, 10, 30, 14, V3['sky'])
    return finish(im, [(14, 13), (26, 11)])

def ic_mood_happy():
    im = rgba(32)
    # 太陽笑臉（金）
    disc(im, 16, 16, 8, V3['amber'])
    disc(im, 16, 16, 6, V3['goldhi'])
    for a in range(8):
        ang = a * math.pi / 4
        x0 = int(round(16 + 9 * math.cos(ang))); y0 = int(round(16 + 9 * math.sin(ang)))
        x1 = int(round(16 + 13 * math.cos(ang))); y1 = int(round(16 + 13 * math.sin(ang)))
        line(im, x0, y0, x1, y1, V3['gold'])
    line(im, 12, 15, 14, 17, PAL['outline']); line(im, 14, 17, 15, 15, PAL['outline'])
    line(im, 17, 15, 18, 17, PAL['outline']); line(im, 18, 17, 20, 15, PAL['outline'])
    fill_ellipse(im, 16, 20, 3, 2, PAL['berry'])
    return finish(im, [(13, 13)])

def ic_mood_ok():
    im = rgba(32)
    disc(im, 16, 16, 10, PAL['cream2'])
    disc(im, 14, 14, 5, PAL['cream3'])
    pset(im, 12, 15, PAL['outline']); pset(im, 20, 15, PAL['outline'])
    fill_rect(im, 14, 20, 19, 21, PAL['outline'])
    return finish(im, [(13, 13)])

def ic_mood_sad():
    im = rgba(32)
    disc(im, 16, 17, 10, PAL['cream1'])
    disc(im, 15, 15, 4, PAL['cream2'])
    # 下垂眼
    line(im, 11, 15, 14, 17, PAL['outline']); line(im, 18, 17, 21, 15, PAL['outline'])
    fill_ellipse(im, 16, 22, 2, 2, PAL['blush_d'])
    # 淚
    pset(im, 11, 18, PAL['drop']); pset(im, 11, 20, PAL['drop_d'])
    return finish(im, [(14, 14)])

def ic_mood_sleepy():
    im = rgba(32)
    disc(im, 16, 18, 10, PAL['cream1'])
    fill_rect(im, 11, 17, 14, 18, PAL['outline'])
    fill_rect(im, 18, 17, 21, 18, PAL['outline'])
    fill_ellipse(im, 16, 21, 2, 1, PAL['blush'])
    # 月＋zzz 角
    disc(im, 24, 8, 4, V3['gold']); disc(im, 26, 7, 3, (0, 0, 0, 0), 0)
    base = rgba(32); disc(base, 24, 8, 4, V3['gold'])
    hole = rgba(32); disc(hole, 26, 7, 3, (255, 255, 255))
    keep = (base[..., 3] > 0) & (hole[..., 3] == 0)
    # 清先前 disc 洞殘渣
    im[hole[..., 3] > 0] = 0
    im[keep] = base[keep]
    pset(im, 8, 7, PAL['zzz']); pset(im, 9, 6, PAL['zzz'])
    return finish(im, [(13, 14), (23, 7)])


def ic_ev_gift():
    im = rgba(32)
    fill_rect(im, 8, 14, 24, 27, V3['rose'])
    fill_rect(im, 9, 15, 23, 26, PAL['blush'])
    fill_rect(im, 15, 14, 17, 27, V3['gold'])
    fill_rect(im, 8, 18, 24, 20, V3['gold'])
    # 蓋
    fill_rect(im, 7, 11, 25, 15, PAL['berry'])
    fill_rect(im, 8, 12, 24, 14, V3['rose'])
    # 結
    disc(im, 13, 11, 3, V3['gold']); disc(im, 19, 11, 3, V3['gold'])
    pset(im, 16, 10, V3['goldhi'])
    # 光粒
    pset(im, 10, 8, V3['goldhi']); pset(im, 16, 6, V3['amber']); pset(im, 22, 8, V3['goldhi'])
    return finish(im, [(16, 10), (11, 16)])

def ic_ev_butterfly():
    im = rgba(32)
    # 原創：薄荷＋杏黃翅，紫唔做主（避免似某角色配色）
    fill_ellipse(im, 10, 14, 6, 8, HUNT['wing'])
    fill_ellipse(im, 22, 14, 6, 8, HUNT['wing'])
    fill_ellipse(im, 10, 14, 3, 4, PAL['cream3'])
    fill_ellipse(im, 22, 14, 3, 4, PAL['cream3'])
    fill_ellipse(im, 10, 22, 4, 5, PAL['leaf'])
    fill_ellipse(im, 22, 22, 4, 5, PAL['leaf'])
    fill_rect(im, 15, 12, 17, 24, PAL['outline'])
    disc(im, 16, 11, 2, PAL['outline'])
    pset(im, 14, 9, PAL['outline']); pset(im, 18, 9, PAL['outline'])
    return finish(im, [(9, 12), (23, 12)])

def ic_ev_meteor():
    im = rgba(32)
    # 斜落金流星
    for i, col in enumerate((V3['navy3'], V3['golddk'], V3['gold'], V3['goldhi'])):
        line(im, 8 + i, 24 - i, 20 + i // 2, 10, col)
    disc(im, 22, 8, 4, V3['goldhi']); disc(im, 22, 8, 2, PAL['white'])
    pset(im, 6, 8, PAL['cream3']); pset(im, 10, 6, V3['gold']); pset(im, 26, 16, PAL['cream3'])
    return finish(im, [(22, 7), (21, 8)])

def ic_ev_rainbow():
    im = rgba(32)
    cols = [PAL['berry'], PAL['orange'], V3['gold'], PAL['leaf'], PAL['drop'], V3['violet']]
    for i, c in enumerate(cols):
        tmp = rgba(32); fill_ellipse(tmp, 16, 20, 13 - i, 10 - i, c)
        hole = rgba(32); fill_ellipse(hole, 16, 20, 12 - i, 9 - i, (255, 255, 255))
        keep = (tmp[..., 3] > 0) & (hole[..., 3] == 0) & (np.arange(32)[:, None] <= 20)
        im[keep] = tmp[keep]
    # 雲
    disc(im, 6, 20, 4, PAL['white']); disc(im, 9, 21, 3, PAL['white'])
    disc(im, 25, 20, 4, PAL['white']); disc(im, 22, 21, 3, PAL['white'])
    return finish(im, [(16, 12)])

def ic_ev_firefly():
    im = rgba(32)
    disc(im, 16, 16, 4, PAL['leaf_d'])
    disc(im, 16, 18, 3, PAL['glow'])
    disc(im, 16, 18, 2, PAL['glow_core'])
    # 翅
    fill_ellipse(im, 11, 14, 4, 3, PAL['cyan']); fill_ellipse(im, 21, 14, 4, 3, PAL['cyan'])
    pset(im, 10, 10, PAL['glow']); pset(im, 22, 8, PAL['glow_core']); pset(im, 24, 18, PAL['glow'])
    pset(im, 8, 20, PAL['glow_mid']); pset(im, 18, 6, PAL['glow'])
    return finish(im, [(16, 17), (22, 8)])

def ic_ev_sleeptalk():
    im = rgba(32)
    # 對話泡
    disc(im, 16, 14, 11, V3['navy2'])
    disc(im, 16, 14, 9, V3['cream'])
    tri(im, [(12, 22), (16, 22), (11, 28)], V3['navy2'])
    tri(im, [(13, 22), (15, 22), (12, 26)], V3['cream'])
    # 月
    disc(im, 14, 13, 4, V3['gold'])
    disc(im, 16, 12, 3, V3['cream'])
    # 清被蓋住嘅月洞：重畫
    # 星
    pset(im, 20, 10, V3['amber']); pset(im, 22, 14, V3['gold']); pset(im, 19, 16, V3['amber'])
    return finish(im, [(13, 11)])

def ic_ev_tantrum():
    im = rgba(32)
    # 怒筋四瓣（紅）＋煙
    disc(im, 16, 16, 8, V3['red'])
    disc(im, 16, 16, 5, PAL['berry'])
    # X 眼符號
    line(im, 11, 13, 15, 17, V3['cream']); line(im, 15, 13, 11, 17, V3['cream'])
    line(im, 17, 13, 21, 17, V3['cream']); line(im, 21, 13, 17, 17, V3['cream'])
    fill_rect(im, 14, 20, 19, 21, V3['navy'])
    pset(im, 8, 8, V3['dis']); pset(im, 7, 10, V3['mute']); pset(im, 24, 7, V3['dis']); pset(im, 25, 9, V3['mute'])
    return finish(im, [])

def ic_ev_treasure():
    im = rgba(32)
    fill_rect(im, 8, 16, 24, 27, HUNT['copper_d'])
    fill_rect(im, 9, 17, 23, 26, HUNT['copper'])
    fill_rect(im, 7, 14, 25, 18, HUNT['copper_l'])
    fill_rect(im, 8, 15, 24, 17, HUNT['copper'])
    # 開蓋光芒
    fill_rect(im, 6, 10, 26, 14, HUNT['copper_d'])
    fill_rect(im, 7, 8, 25, 12, HUNT['copper'])
    disc(im, 16, 14, 3, PAL['cyan']); pset(im, 16, 14, PAL['glow_core'])
    pset(im, 16, 6, V3['goldhi']); pset(im, 12, 8, V3['amber']); pset(im, 20, 8, V3['amber'])
    return finish(im, [(16, 14), (16, 6)])

def ic_ev_flash():
    im = rgba(32)
    # 大四芒星
    tri(im, [(16, 2), (19, 16), (13, 16)], V3['goldhi'])
    tri(im, [(16, 30), (19, 16), (13, 16)], V3['gold'])
    tri(im, [(2, 16), (16, 13), (16, 19)], V3['gold'])
    tri(im, [(30, 16), (16, 13), (16, 19)], V3['goldhi'])
    disc(im, 16, 16, 4, PAL['white'])
    pset(im, 8, 8, V3['amber']); pset(im, 24, 8, V3['amber']); pset(im, 8, 24, V3['amber']); pset(im, 24, 24, V3['amber'])
    return finish(im, [(16, 16)])

def ic_ev_eat():
    im = rgba(32)
    # 漿果串
    disc(im, 14, 18, 5, PAL['berry']); disc(im, 20, 16, 5, PAL['berry'])
    disc(im, 17, 22, 4, PAL['berry_d'])
    pset(im, 13, 16, PAL['blush']); pset(im, 19, 14, PAL['blush'])
    fill_rect(im, 16, 8, 18, 14, PAL['leaf_d'])
    fill_ellipse(im, 20, 9, 4, 2, PAL['leaf'])
    return finish(im, [(13, 16), (19, 14)])

def ic_ev_play():
    im = rgba(32)
    # 小球
    disc(im, 16, 18, 8, V3['sky'])
    disc(im, 14, 16, 4, PAL['cyan'])
    fill_ellipse(im, 16, 18, 8, 2, V3['navy3'])
    fill_ellipse(im, 16, 18, 2, 8, V3['navy3'])
    return finish(im, [(13, 15)])

def ic_ev_sleep():
    im = rgba(32)
    # 枕頭＋zzz
    fill_ellipse(im, 16, 20, 11, 6, V3['mute'])
    fill_ellipse(im, 16, 19, 9, 4, V3['cream'])
    fill_rect(im, 10, 16, 22, 20, PAL['zzz'])
    fill_rect(im, 11, 17, 21, 19, V3['violet'])
    pset(im, 20, 10, PAL['zzz']); pset(im, 22, 8, V3['violet']); pset(im, 24, 6, PAL['white'])
    return finish(im, [(13, 18)])

def ic_ev_walk():
    im = rgba(32)
    # 腳印兩隻（浅銅／奶油，深底都睇到）
    fill_ellipse(im, 11, 20, 4, 6, HUNT['copper'])
    disc(im, 9, 15, 2, HUNT['copper_l']); disc(im, 12, 14, 2, HUNT['copper_l']); disc(im, 14, 16, 2, HUNT['copper'])
    fill_ellipse(im, 21, 14, 4, 6, PAL['cream1'])
    disc(im, 19, 9, 2, PAL['cream2']); disc(im, 22, 8, 2, PAL['cream2']); disc(im, 24, 10, 2, PAL['cream1'])
    return finish(im, [])

def ic_ev_work():
    im = rgba(32)
    # 信封／邮局袋原創小包
    fill_rect(im, 7, 12, 25, 26, V3['navy3'])
    fill_rect(im, 8, 13, 24, 25, V3['cream'])
    tri(im, [(8, 13), (24, 13), (16, 20)], V3['navy2'])
    tri(im, [(9, 13), (23, 13), (16, 19)], V3['gold'])
    pset(im, 16, 21, V3['amber'])
    return finish(im, [(16, 16)])

def ic_ev_rain():
    im = rgba(32)
    disc(im, 12, 10, 6, V3['dis']); disc(im, 20, 9, 7, V3['navy3'])
    disc(im, 16, 8, 6, V3['mute'])
    for x, y in ((10, 18), (14, 22), (18, 18), (22, 23), (12, 26), (20, 20)):
        pset(im, x, y, PAL['drop']); pset(im, x, y + 1, PAL['drop_d']); pset(im, x, y + 2, PAL['drop_d'])
    return finish(im, [(14, 6)])

def ic_ev_visit():
    im = rgba(32)
    # 門＋小影
    fill_rect(im, 8, 8, 24, 28, HUNT['soil_d'])
    fill_rect(im, 10, 10, 22, 28, HUNT['bun_l'])
    fill_rect(im, 14, 16, 18, 28, HUNT['soil'])
    disc(im, 16, 22, 1, V3['gold'])
    #  knocker / 小花歡迎
    disc(im, 16, 14, 2, V3['rose'])
    return finish(im, [(16, 11)])

def ic_ev_hunt():
    im = rgba(32)
    # 草叢＋果
    fill_ellipse(im, 10, 22, 6, 8, PAL['leaf_d'])
    fill_ellipse(im, 16, 20, 7, 10, PAL['leaf'])
    fill_ellipse(im, 22, 22, 6, 8, PAL['leaf_d'])
    disc(im, 16, 16, 4, PAL['berry']); pset(im, 15, 15, PAL['blush'])
    return finish(im, [(15, 15)])

def ic_ev_furniture():
    im = rgba(32)
    fill_rect(im, 8, 14, 24, 18, HUNT['bun'])
    fill_rect(im, 10, 18, 12, 26, HUNT['bun_d'])
    fill_rect(im, 20, 18, 22, 26, HUNT['bun_d'])
    fill_rect(im, 9, 12, 23, 15, HUNT['bun_l'])
    # 小花瓶
    fill_rect(im, 15, 8, 17, 12, PAL['drop_d'])
    pset(im, 16, 6, PAL['leaf']); pset(im, 15, 7, V3['rose']); pset(im, 17, 7, V3['gold'])
    return finish(im, [(16, 13)])

def ic_ev_egg():
    im = rgba(32)
    fill_ellipse(im, 16, 18, 8, 11, PAL['cream3'])
    fill_ellipse(im, 14, 16, 5, 7, PAL['cream4'])
    pset(im, 18, 14, PAL['glow']); pset(im, 13, 20, PAL['glow_mid'])
    fill_ellipse(im, 16, 18, 8, 11, PAL['cream3'])  # 保外形
    # 斑點
    pset(im, 12, 18, PAL['peach0']); pset(im, 20, 20, PAL['peach0']); pset(im, 16, 24, PAL['peach1'])
    # 裂光
    pset(im, 16, 10, PAL['glow_core']); line(im, 16, 12, 16, 16, PAL['glow'])
    return finish(im, [(13, 15), (16, 10)])

def ic_ev_steps():
    im = rgba(32)
    # 小徑＋步數感（三個石）
    fill_ellipse(im, 16, 24, 12, 4, HUNT['path_d'])
    disc(im, 10, 20, 3, HUNT['stone']); disc(im, 16, 16, 3, HUNT['stone_l']); disc(im, 22, 12, 3, HUNT['stone'])
    pset(im, 16, 8, V3['amber']); pset(im, 15, 7, V3['gold']); pset(im, 17, 7, V3['gold'])
    return finish(im, [(16, 15)])

def ic_badge(critter_draw, zh):
    im = rgba(32)
    # 銅章圓
    disc(im, 16, 16, 15, HUNT['copper_d'])
    disc(im, 16, 16, 13, HUNT['copper'])
    disc(im, 16, 16, 11, HUNT['copper_l'])
    disc(im, 16, 16, 10, V3['navy2'])
    # 內圈金銅線
    tmp = rgba(32); disc(tmp, 16, 16, 10, HUNT['copper_hi']); disc(tmp, 16, 16, 9, (0, 0, 0, 0), 0)
    # punch
    hole = rgba(32); disc(hole, 16, 16, 9, (255, 255, 255))
    keep = (tmp[..., 3] > 0) & (hole[..., 3] == 0)
    im[keep] = tmp[keep]
    # 剪影
    sil = rgba(32)
    critter_draw(sil, ox=16, oy=18, scale=1.0, silhouette=True)
    blit(im, sil, 0, 0)
    return finish(im, [(10, 10), (12, 8)])

# 泡泡框（真 alpha，@3x 96×72）
def bubble_dream():
    W, H = 96, 72
    im = rgba(H, W)
    # 磨砂深藍圓角矩形（真 alpha）
    def rrect(dst, x0, y0, x1, y1, r, col, a):
        fill_rect(dst, x0 + r, y0, x1 - r, y1, col, a)
        fill_rect(dst, x0, y0 + r, x1, y1 - r, col, a)
        disc(dst, x0 + r, y0 + r, r, col, a)
        disc(dst, x1 - r - 1, y0 + r, r, col, a)
        disc(dst, x0 + r, y1 - r - 1, r, col, a)
        disc(dst, x1 - r - 1, y1 - r - 1, r, col, a)
    # 影
    rrect(im, 6, 8, 94, 66, 12, V3['navy'], 80)
    rrect(im, 4, 4, 92, 62, 12, V3['navy'], 200)
    rrect(im, 6, 6, 90, 60, 10, V3['navy2'], 220)
    # 金幼線
    # 用較淡金描一圈
    border = rgba(H, W)
    rrect(border, 5, 5, 91, 61, 11, V3['gold'], 255)
    inner = rgba(H, W)
    rrect(inner, 7, 7, 89, 59, 9, (255, 255, 255), 255)
    keep = (border[..., 3] > 0) & (inner[..., 3] == 0)
    im[keep, :3] = V3['gold']
    im[keep, 3] = 255
    # 內高光
    fill_rect(im, 16, 8, 80, 10, V3['goldhi'], 120)
    # 兩個 icon 槽（32×32），輕微重叠「撞埋」
    def slot(x, y, a=180):
        fill_rect(im, x, y, x + 32, y + 32, V3['navy'], a)
        # 金角
        fill_rect(im, x, y, x + 32, y + 1, V3['gold'], 200)
        fill_rect(im, x, y + 31, x + 32, y + 32, V3['gold'], 160)
        fill_rect(im, x, y, x + 1, y + 32, V3['gold'], 200)
        fill_rect(im, x + 31, y, x + 32, y + 32, V3['gold'], 160)
    slot(12, 16, 160)
    slot(52, 16, 160)  # 重叠 12+32=44，52-44=8px 空隙；再移近啲
    # 再畫一次更近：左 14、右 46（重叠 32-32? 14+32=46，剛好相接）。改為右 42 重叠 4px
    # 清掉舊槽範圍重新
    # 其實第一次 slot 52 太開，覆蓋重畫
    slot(14, 16, 170)
    slot(42, 16, 170)
    # 尾（朝下）
    tri(im, [(40, 60), (56, 60), (36, 70)], V3['navy2'] + (220,))
    # 上句 tri 對 RGBA 可能唔啱，手動
    for y in range(60, 71):
        t = (y - 60) / 10.0
        x0 = int(40 + (36 - 40) * t)
        x1 = int(56 + (36 - 56) * t)
        for x in range(x0, x1 + 1):
            if 0 <= x < W and 0 <= y < H:
                im[y, x] = (*V3['navy2'], 220)
    # 尾金邊
    line(im, 40, 60, 36, 70, V3['gold'], 255)
    line(im, 56, 60, 36, 70, V3['gold'], 200)
    # 兩槽中間「撞」閃光
    pset(im, 46, 28, V3['goldhi'], 255); pset(im, 47, 30, V3['amber'], 255)
    pset(im, 45, 32, V3['gold'], 255)
    # 星點裝飾
    pset(im, 10, 12, V3['goldhi'], 200); pset(im, 84, 14, V3['gold'], 200)
    return im  # 真 alpha，唔 harden 成 0/255

# ICON 表
ICONS = [
    # 需要 4
    ('need_eat', '想食', 'need', ic_need_eat),
    ('need_play', '想玩', 'need', ic_need_play),
    ('need_sleep', '想瞓', 'need', ic_need_sleep),
    ('need_pet', '想摸', 'need', ic_need_pet),
    # 表情 10（6 性格＋4 心情）
    ('expr_lively', '活潑', 'expr', ic_expr_lively),
    ('expr_quiet', '文靜', 'expr', ic_expr_quiet),
    ('expr_diligent', '勤力', 'expr', ic_expr_diligent),
    ('expr_lazy', '懶散', 'expr', ic_expr_lazy),
    ('expr_clingy', '黐人', 'expr', ic_expr_clingy),
    ('expr_indep', '獨立', 'expr', ic_expr_indep),
    ('mood_happy', '開心', 'mood', ic_mood_happy),
    ('mood_ok', '普通', 'mood', ic_mood_ok),
    ('mood_sad', '唔開心', 'mood', ic_mood_sad),
    ('mood_sleepy', '眼瞓', 'mood', ic_mood_sleepy),
    # 事件 20
    ('ev_gift', '帶禮物回來', 'event', ic_ev_gift),
    ('ev_butterfly', '蝴蝶訪客', 'event', ic_ev_butterfly),
    ('ev_meteor', '流星夜', 'event', ic_ev_meteor),
    ('ev_rainbow', '雨後彩虹', 'event', ic_ev_rainbow),
    ('ev_firefly', '螢火散步', 'event', ic_ev_firefly),
    ('ev_sleeptalk', '夢話', 'event', ic_ev_sleeptalk),
    ('ev_tantrum', '鬧脾氣', 'event', ic_ev_tantrum),
    ('ev_treasure', '尋寶', 'event', ic_ev_treasure),
    ('ev_flash', '閃光日', 'event', ic_ev_flash),
    ('ev_eat', '食過', 'event', ic_ev_eat),
    ('ev_play', '玩過', 'event', ic_ev_play),
    ('ev_sleep', '瞓過', 'event', ic_ev_sleep),
    ('ev_walk', '行過', 'event', ic_ev_walk),
    ('ev_work', '返過工', 'event', ic_ev_work),
    ('ev_rain', '落雨', 'event', ic_ev_rain),
    ('ev_visit', '有訪客', 'event', ic_ev_visit),
    ('ev_hunt', '去過狩獵', 'event', ic_ev_hunt),
    ('ev_furniture', '擺咗新傢俬', 'event', ic_ev_furniture),
    ('ev_egg', '新蛋到咗', 'event', ic_ev_egg),
    ('ev_steps', '行咗好多步', 'event', ic_ev_steps),
]

def build(out_root):
    d = os.path.join(out_root, 'art-pet/ui/m1_icons')
    os.makedirs(f'{d}/icons', exist_ok=True)
    os.makedirs(f'{d}/atlas', exist_ok=True)
    frames, names, items = [], [], []
    for iid, zh, grp, fn in ICONS:
        im = fn()
        assert im.shape == (32, 32, 4), (iid, im.shape)
        assert set(np.unique(im[..., 3]).tolist()) <= {0, 255}, iid
        save_png(f'{d}/icons/{iid}@3x.png', im)
        frames.append(im); names.append(iid)
        items.append(dict(id=iid, zh=zh, group=grp, size=32, file=f'icons/{iid}@3x.png',
                          pivotPx=[16, 16], alpha='0/255'))
    atlas, fj, W, H = pack_atlas(frames, names, pad=2, cols=8)
    save_png(f'{d}/atlas/icons_m1@3x.png', atlas)
    for n, rec in fj.items():
        rec['pivotPx'] = {'x': 16, 'y': 16}
    spec = dict(
        format='m1.icons/1', size=32, scale='@3x（1:1 顯示，同 kit_hd2d_v3）',
        style='V3-A 金光深藍、金幼線、像素打光',
        alpha='sprite 0/255；透明 RGB=0',
        count=len(items),
        items=items,
        atlas=dict(image='atlas/icons_m1@3x.png', size={'w': W, 'h': H}, padding=2, extrude=1, frames=fj),
        bubble=dict(id='bubble_dream', zh='夢泡泡框', file='bubble_dream@3x.png',
                    size=[96, 72], alpha='true-alpha（UI 層）',
                    slots=[{'id': 'event_a', 'x': 14, 'y': 16, 'w': 32, 'h': 32},
                           {'id': 'event_b', 'x': 42, 'y': 16, 'w': 32, 'h': 32}],
                    note='兩格事件 icon 相接／重叠 4px，表示「兩件尋日事件撞埋」'),
        note='需要 4＋表情 10＋事件 20＝34；夢泡泡框另計。M2 動作未畫。',
    )
    bub = bubble_dream()
    save_png(f'{d}/bubble_dream@3x.png', bub)
    json.dump(spec, open(f'{d}/icons.json', 'w'), ensure_ascii=False, indent=1)
    return spec, {n: f for n, f in zip(names, frames)}, bub

if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else '/workspace/m1-icons-hunt-src'
    build(root)
    print('icons ok')
