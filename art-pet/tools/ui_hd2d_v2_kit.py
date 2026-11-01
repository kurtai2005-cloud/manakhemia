# 《微光小圃》HD-2D v2 UI kit builder（Kurt 揀「A ui 配 b 頭像」）— 遊美 2026-11-02
# 出：ui/kit_hd2d_v2/atlas（ui＋icons，@1x/@2x/@3x）、icons/、fonts/（Fusion Pixel 字 atlas）、portrait/（頭像框＋portrait_rects.json）
# 全部 1x 像素原生（alpha 0/255），@2x/@3x＝nearest 整數放大。純 Pillow／numpy，冇 AI 圖。
# 重跑：cd art-pet && python3 tools/ui_hd2d_v2_kit.py && python3 tools/build_ui_hd2d_v2_mockups.py && python3 tools/validate_ui_kit_hd2d_v2.py
import os, sys, json, re, glob, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import hd2d_v2_px as X
from hd2d_v2_px import P, FILLS, new, put, putc, medal, frame, chamfer_mask, circle_mask, gem, rivet, sparkle, erode, dilate, dgrad, hx, img
import ui_hd2d_v2_icons as ICN
ART = X.ART; KIT = f'{ART}/ui/kit_hd2d_v2'
FD = f'{KIT}/fonts'
for d in ('atlas', 'fonts', 'icons', 'portrait'): os.makedirs(f'{KIT}/{d}', exist_ok=True)
FILLS['dis'] = [hx('#E6E8F2'), hx('#B9BED4'), hx('#8C92AE'), hx('#5E6484')]
FILLS['gold'] = [hx('#FFF6CF'), hx('#FFE29A'), hx('#EDBE62'), hx('#9C6630')]
NAVY = [FILLS['navy'][1], FILLS['navy'][2]]

def hard(im):
    a = np.array(im.convert('RGBA')); a[..., 3] = np.where(a[..., 3] >= 128, 255, 0); a[a[..., 3] == 0] = 0; return img(a)

FR = {}   # name -> dict(img, slice, nine, group, note, mode)
def add(name, im, group, slice_=None, nine=None, mode=None, **kw):
    assert name not in FR, name
    FR[name] = dict(img=hard(im), group=group, slice=slice_, nine=nine, mode=mode, **kw)

# ---------------------------------------------------------------- 面板（9-slice，中間同邊 tile；紋理周期 8）
def flatpanel(w, h, ch, fill, gold=2, band=None, inner_line=True, glass=True):
    """9-slice 安全面板：內面平色（只有周期 8 紋理），可選頂部受光帶（只喺 top inset 入面）"""
    if isinstance(fill, str):
        cols = [FILLS['navy'][2]] * 2 if fill == 'navy' else [FILLS[fill][1]] * 2
    else: cols = list(fill)
    im = frame(chamfer_mask(w, h, ch), cols, gold=gold, glass=False, tex=True, rim_glints=False, inner_line=inner_line, sheen=False)
    a = np.array(im)
    if band:
        c0, c1, n = band; inn = chamfer_mask(w, h, ch)
        for _ in range(1 + (gold >= 1) + (gold >= 2) + inner_line): inn = erode(inn)
        ys = np.where(inn.any(1))[0]; y0 = ys[0] + 2
        yy = np.mgrid[0:h, 0:w][0]; t = np.clip((yy - y0) / n, 0, 1)
        g = dgrad(t, [c0, c1]); msk = inn & (yy >= y0) & (yy < y0 + n)
        a[msk] = g[msk]
    return img(a)

def P9(nine, ch, fill, gold=2, band=None, inner_line=True, h=None, cw=8):
    l, t, r, b = nine; return flatpanel(l + r + cw, h if h else t + b + cw, ch, fill, gold, band, inner_line)

def panels():
    # 主面板（彈窗／sheet）：chamfer 6，金 2 圈，頂 8 行玻璃受光
    add('panel_navy', P9([10, 16, 10, 10], 6, 'navy', 2, band=(FILLS['navy'][0], FILLS['navy'][2], 10)), 'panel', '9', [10, 16, 10, 10], 'tile', note='主面板／彈窗；中間＋邊 tile（周期 8）')
    add('panel_navy_flat', P9([10, 10, 10, 10], 6, 'navy', 2), 'panel', '9', [10, 10, 10, 10], 'tile')
    add('panel_paper', P9([9, 9, 9, 9], 5, 'paper', 2), 'panel', '9', [9, 9, 9, 9], 'tile', note='羊皮紙（日記內頁）')
    add('panel_inset', P9([6, 6, 6, 6], 3, [FILLS['navy'][3], FILLS['navy'][3]], gold=1, inner_line=True), 'panel', '9', [6, 6, 6, 6], 'tile', note='列／內格')
    add('panel_inset_sel', P9([7, 7, 7, 7], 3, [FILLS['navy'][1], FILLS['navy'][1]], gold=2), 'panel', '9', [7, 7, 7, 7], 'tile')
    add('banner_top', P9([10, 18, 10, 10], 6, 'navy', 2, band=(FILLS['navy'][0], FILLS['navy'][2], 12)), 'hud', '9', [10, 18, 10, 10], 'tile', note='A 版頂旗（全闊，y −5）')
    add('card', P9([6, 6, 6, 6], 4, [FILLS['navy'][2], FILLS['navy'][2]], gold=1), 'card', '9', [6, 6, 6, 6], 'tile')
    add('card_sel', P9([7, 7, 7, 7], 4, [FILLS['navy'][1], FILLS['navy'][1]], gold=2), 'card', '9', [7, 7, 7, 7], 'tile')
    add('card_locked', P9([6, 6, 6, 6], 4, [hx('#2A2F52'), hx('#2A2F52')], gold=0), 'card', '9', [6, 6, 6, 6], 'tile')
    add('card_paper', P9([6, 6, 6, 6], 4, 'paper', 1), 'card', '9', [6, 6, 6, 6], 'tile')
    # dock 條
    add('dock_bar', P9([9, 14, 9, 9], 5, 'navy', 2, band=(FILLS['navy'][0], FILLS['navy'][2], 8)), 'hud', '9', [9, 14, 9, 9], 'tile')
    add('dock_pillar', P9([6, 10, 6, 6], 4, 'pri', 1), 'hud', '9', [6, 10, 6, 6], 'tile', note='已選 tab 光柱')
    # 泡泡
    b = flatpanel(16, 16, 2, 'paper', 0, inner_line=False); add('bubble', b, 'hud', '9', [4, 4, 4, 4], 'tile')
    T = new(5, 5); tail = ["oo...", "oWo..", ".oWo.", "..oo.", "....."]
    for y, r in enumerate(tail):
        for x, ch in enumerate(r):
            if ch != '.': T.putpixel((x, y), P['line'] if ch == 'o' else FILLS['paper'][2])
    add('bubble_tail', T, 'hud', note='貼 bubble 底邊（x＝6，y＝h−1）')
    # 佔位：分隔線
    dv = new(16, 3); a = np.array(dv); a[1, ::2] = P['g_mid']; a[0, ::2] = P['g_lo']; a[1, 1::2] = P['g_lo']; add('divider', img(a), 'panel', '3h', [0, 0, 0, 0], 'tile')

# ---------------------------------------------------------------- 3h：掣、pill、緞帶、chip、toast、標題
def button(fill, h, pressed=False, ch=4):
    F = FILLS[fill]; cols = [F[1], F[2], F[3]] if not pressed else [F[2], F[2], F[3]]
    m = chamfer_mask(24, h, ch); a = np.zeros((h, 24, 4), np.uint8); a[m] = P['line']
    m1 = erode(m); m2 = erode(m1)
    X.bevel_ring(a, m1 & ~m2, m1, P['g_hi'], P['g_mid'], P['g_lo']) if not pressed else X.bevel_ring(a, m1 & ~m2, m1, P['g_mid'], P['g_lo'], P['g_dk'])
    a[m2 & ~erode(m2)] = P['line']; inn = erode(m2)
    yy, xx = np.mgrid[0:h, 0:24]; ys = np.where(inn.any(1))[0]; t = (yy - ys[0]) / max(1, ys[-1] - ys[0])
    g = dgrad(t, cols); a[inn] = g[inn]
    top = inn & ~np.roll(inn, 1, 0)
    if not pressed:
        a[top] = F[0]; a[top & ((xx % 2) == 0)] = P['white']
    else:
        a[top] = F[3]; a[inn & ~np.roll(inn, 2, 0) & ~top] = F[3]
    bot = inn & ~np.roll(inn, -1, 0); a[bot] = F[3]
    return img(a)

def chips_btns():
    for f in ('pri', 'sec', 'rose', 'violet', 'dis'):
        add(f'btn_{f}', button(f, 20), 'button', '3h', [8, 0, 8, 0], 'tile', note='h20 主／次／警告／特別／停用')
        add(f'btn_{f}_p', button(f, 20, True), 'button', '3h', [8, 0, 8, 0], 'tile')
    for f in ('pri', 'sec', 'violet', 'rose', 'dis'):
        add(f'btn16_{f}', button(f, 16, ch=3), 'button', '3h', [8, 0, 8, 0], 'tile')
        add(f'btn16_{f}_p', button(f, 16, True, ch=3), 'button', '3h', [8, 0, 8, 0], 'tile')
    for f in ('pri', 'sec', 'rose', 'violet', 'dis'):
        add(f'pill_{f}', button(f, 11, ch=3), 'button', '3h', [5, 0, 5, 0], 'tile')
    add('pill_navy', P9([5, 0, 5, 0], 3, [FILLS['navy'][1], FILLS['navy'][1]], gold=1, h=11), 'button', '3h', [5, 0, 5, 0], 'tile')
    for f in ('navy', 'violet', 'pri', 'rose', 'sec'):
        col = [FILLS['navy'][2]] * 2 if f == 'navy' else [FILLS[f][2]] * 2
        add(f'ribbon_{f}', flatpanel(18, 14, 3, col, gold=1), 'label', '3h', [5, 0, 5, 0], 'tile', note='字牌／階段 tag（字 10px 置中）')
    add('chip', P9([6, 0, 6, 0], 3, [FILLS['navy'][2]] * 2, gold=1, h=13), 'hud', '3h', [6, 0, 6, 0], 'tile', note='貨幣 chip；左端疊 med13_navy＋icon，右端 chip_plus')
    pl = medal(9, 'pri', ring=1, spec=False); pa = np.array(pl); pa[4, 2:7] = P['white']; pa[2:7, 4] = P['white']; add('chip_plus', img(pa), 'hud')
    pl = medal(9, 'pri', ring=1, spec=False); pa = np.array(pl); pa[1:, :] = pa[:-1, :].copy(); pa[0] = 0; pa[5, 2:7] = P['white']; pa[3:8, 4] = P['white']; add('chip_plus_p', img(pa), 'hud')
    # toast：兩頭 cap 已含寶石
    t = P9([12, 0, 12, 0], 4, 'navy', 2, h=17); ta = t.copy(); ta.alpha_composite(gem('rose', 5), (4, 6)); ta.alpha_composite(gem('rose', 5), (ta.width - 9, 6))
    add('toast', ta, 'hud', '3h', [12, 0, 12, 0], 'tile', note='h17；兩端 cap 已含寶石')
    # 標題 plaque（紫）＋尾
    for f, nm in (('violet', 'plaque'), ('pri', 'plaque_pri')):
        add(nm, flatpanel(22, 17, 4, [FILLS[f][2]] * 2, gold=2), 'label', '3h', [7, 0, 7, 0], 'tile', note='彈窗標題帶 h17')
    tl = new(8, 13); a = np.array(tl); m = np.zeros((13, 8), bool)
    for y in range(13):
        w_ = 8 - abs(6 - y) // 2 if y < 13 else 0; m[y, 8 - max(2, w_):] = True
    m[:, :2] &= np.array([abs(6 - y) < 2 for y in range(13)])[:, None]
    a[m] = P['line']; inn = erode(m); a[inn] = FILLS['violet'][3]; a[inn & ~np.roll(inn, 1, 0)] = FILLS['violet'][2]
    add('plaque_tail_l', img(a), 'label'); add('plaque_tail_r', img(a[:, ::-1].copy()), 'label')
    # 子分頁
    add('subtab', P9([5, 0, 5, 0], 3, [FILLS['navy'][3]] * 2, gold=1, h=15), 'button', '3h', [5, 0, 5, 0], 'tile')
    add('subtab_on', button('pri', 15, ch=3), 'button', '3h', [6, 0, 6, 0], 'tile')
    # 分段控件
    add('seg_bg', P9([5, 0, 5, 0], 3, [FILLS['navy'][3]] * 2, gold=1, h=14), 'ctl', '3h', [5, 0, 5, 0], 'tile')
    add('seg_on', button('pri', 10, ch=2), 'ctl', '3h', [4, 0, 4, 0], 'tile')
    add('seg_locked', button('dis', 10, ch=2), 'ctl', '3h', [4, 0, 4, 0], 'tile')
    add('stage_tag', P9([5, 0, 5, 0], 3, [FILLS['violet'][2]] * 2, gold=1, h=12), 'label', '3h', [5, 0, 5, 0], 'tile')

# ---------------------------------------------------------------- 條
def bars():
    for h in (5, 6, 7):
        m = chamfer_mask(12, h, 1); a = np.zeros((h, 12, 4), np.uint8); a[m] = P['line']
        m1 = erode(m); m2 = erode(m1); X.bevel_ring(a, m1 & ~m2, m1, P['g_hi'], P['g_mid'], P['g_lo']); a[m2] = P['trough']
        a[m2 & ~np.roll(m2, 1, 0)] = P['line']
        add(f'bar_trough_h{h}', img(a), 'bar', '3h', [3, 0, 3, 0], 'tile', note=f'條槽 h{h}；填色 = bar_fill_*_h{h}，由 x2 起，闊＝(w−4)×值')
        ih = h - 4
        for f in ('pri', 'rose', 'sec', 'violet', 'green', 'gold'):
            F = FILLS[f]; seg = 5; fa = np.zeros((ih, seg, 4), np.uint8); fa[:] = F[2]; fa[0] = F[0]
            if ih >= 3: fa[1] = F[1]
            fa[-1] = F[3]; fa[1:, seg - 1] = F[3]
            add(f'bar_fill_{f}_h{h}', img(fa), 'bar', '3h', [0, 0, 0, 0], 'tile', note='每 5px 一格，tile')
        tip = np.zeros((ih, 1, 4), np.uint8); tip[:] = P['white']; add(f'bar_tip_h{h}', img(tip), 'bar', note='填色尾光 1px')
    for g in ('on', 'off'):
        add(f'exp_gem_{g}', gem('pri' if g == 'on' else 'navy', 5), 'bar')

# ---------------------------------------------------------------- 圓章／寶石／FX
def medals():
    spec = {'navy': (11, 13, 16, 17, 18, 20, 22, 24, 28), 'pri': (13, 15, 16, 17, 20, 22, 24, 25, 28, 30, 34), 'rose': (9, 11, 13, 15, 17, 28, 30), 'sec': (9, 13, 17, 28, 30, 34),
            'violet': (13, 17, 22, 28, 30), 'paper': (11, 13, 16, 20, 24), 'green': (13, 17), 'dis': (24, 28, 30), 'gold': (24, 40)}
    for f, ds in spec.items():
        for d in ds:
            ring = 1 if d <= 18 else 2
            add(f'med{d}_{f}', medal(d, f, ring=ring, spec=d >= 16), 'medal', note=f'd{d}')
            if (f in ('pri', 'rose', 'sec', 'violet') and d in (28, 30)) or (f == 'navy' and d in (22, 24)) or (f == 'pri' and d == 22):
                m = np.array(medal(d, f, ring=ring, spec=False)); inn = m.copy(); out = np.zeros_like(m); out[1:] = m[:-1]
                F = FILLS[f]; msk = out[..., 3] > 0; core = erode(erode(erode(msk)))
                out[core] = (out[core].astype(int) * .78).astype(np.uint8); out[..., 3] = np.where(msk, 255, 0)
                add(f'med{d}_{f}_p', img(out), 'medal', note='按下：向下 1px＋暗 22%')
    for k in ('rose', 'sec', 'pri', 'violet', 'green'):
        add(f'gem_{k}_5', gem(k, 5), 'deco'); add(f'gem_{k}_7', gem(k, 7), 'deco')
    add('rivet', rivet(), 'deco')
    for n in (3, 5, 7): add(f'sparkle_{n}', sparkle(n), 'fx')
    # 紅點
    add('red_dot', medal(9, 'rose', ring=1, spec=False), 'hud', note='d9；字用 font 8 白')
    add('red_dot_num', medal(11, 'rose', ring=1, spec=False), 'hud')
    # 關閉 ✕
    for p_ in (False, True):
        c = np.array(medal(15, 'rose', ring=1, spec=False))
        for i in range(5): c[5 + i, 5 + i] = c[5 + i, 9 - i] = P['white']
        for i in range(5): c[5 + i, 6 + i if i < 4 else 9] = P['white']; c[5 + i, 8 - i if i < 4 else 5] = P['white']
        if p_: c2 = np.zeros_like(c); c2[1:] = c[:-1]; c = c2
        add('close' + ('_p' if p_ else ''), img(c), 'button', note='✕ 一律右上內')
    # toggle
    for on in (True, False):
        tr = flatpanel(22, 11, 4, [FILLS['sec'][2] if on else FILLS['navy'][3]] * 2, gold=1, glass=False); add(f'toggle_track_{"on" if on else "off"}', tr, 'ctl')
        add(f'toggle_knob_{"on" if on else "off"}', medal(11, 'paper' if on else 'dis', ring=1, spec=False), 'ctl')
    # check
    for on in (True, False):
        c = np.array(flatpanel(11, 11, 2, [FILLS['navy'][3]] * 2, gold=1, glass=False))
        if on:
            for (x, y) in ((3, 5), (4, 6), (5, 7), (6, 6), (7, 5), (8, 4), (4, 5), (5, 6), (6, 5), (7, 4)): c[y, x] = FILLS['green'][1]
        add(f'check_{"on" if on else "off"}', img(c), 'ctl')
    # 星
    for on in (True, False):
        S = ICN.Ic(); S.PG([(4.5, 0), (5.8, 3), (9, 3.3), (6.6, 5.4), (7.4, 8.8), (4.5, 7), (1.6, 8.8), (2.4, 5.4), (0, 3.3), (3.2, 3)], 'e' if on else 's')
        add(f'star_{"on" if on else "off"}', ICN.render(S).crop((0, 0, 11, 11)), 'ctl')
    # slider／scroll
    add('slider_track', bar_simple(12, 5), 'ctl', '3h', [3, 0, 3, 0], 'tile')
    add('slider_knob', medal(11, 'pri', ring=1, spec=False), 'ctl')
    sc = np.zeros((12, 4, 4), np.uint8); sc[:, 1:3] = P['nv4']; sc[:, 0] = sc[:, 3] = P['line']; add('scroll_track', img(sc), 'ctl', '3v', [0, 2, 0, 2], 'tile')
    st = np.zeros((12, 4, 4), np.uint8); st[:, :] = P['g_mid']; st[:, 0] = P['g_hi']; st[:, 3] = P['g_lo']; st[0, :] = st[-1, :] = P['line']; add('scroll_thumb', img(st), 'ctl', '3v', [0, 2, 0, 2], 'tile')
    # 蓋印
    sd = np.array(medal(24, 'rose', ring=1, spec=False)); yy, xx = np.mgrid[0:24, 0:24]
    ring = (np.sqrt((xx - 11.5) ** 2 + (yy - 11.5) ** 2) < 8.6) & (np.sqrt((xx - 11.5) ** 2 + (yy - 11.5) ** 2) > 7.4); sd[ring] = P['white']
    for (x, y) in ((8, 12), (9, 13), (10, 14), (11, 13), (12, 12), (13, 11), (14, 10), (15, 9), (9, 12), (10, 13), (11, 12), (12, 11), (13, 10), (14, 9)): sd[y, x] = P['white']
    add('stamp_done', img(sd), 'fx', note='完成蓋印')
    # 時間線
    add('timeline_dot', gem('pri', 7), 'list'); tl = np.zeros((4, 3, 4), np.uint8); tl[::2, 1] = P['g_mid']; add('timeline_line', img(tl), 'list', '3v', [0, 0, 0, 0], 'tile')
    # 提示箭嘴
    ha = ICN.Ic(); ha.PG([(1, 2), (14, 2), (7.5, 11)], 'y'); add('hint_arrow', ICN.render(ha).crop((0, 0, 16, 13)), 'fx')
    # FX
    rp = np.zeros((19, 19, 4), np.uint8); yy, xx = np.mgrid[0:19, 0:19]; r = np.sqrt((xx - 9) ** 2 + (yy - 9) ** 2)
    rp[(r > 7.6) & (r <= 8.6)] = P['g_br']; rp[(r > 8.6) & (r <= 9.4) & ((xx + yy) % 2 == 0)] = P['g_mid']; add('fx_ripple', img(rp), 'fx')
    mo = np.zeros((3, 3, 4), np.uint8); mo[1, 1] = P['white']; mo[0, 1] = mo[1, 0] = mo[2, 1] = mo[1, 2] = P['g_br']; add('fx_mote', img(mo), 'fx')
    vt = np.zeros((4, 4, 4), np.uint8); vt[(X.BAYER < .5)] = P['nv4']; add('fx_veil_tile', img(vt), 'fx', '9', [0, 0, 0, 0], 'tile', note='全畫面 tile＝50% 抖色暗幕（冇半透明）')
    vt2 = np.zeros((4, 4, 4), np.uint8); vt2[(X.BAYER < .25)] = P['nv4']; add('fx_veil25_tile', img(vt2), 'fx', '9', [0, 0, 0, 0], 'tile')
    sw = np.zeros((12, 6, 4), np.uint8)
    for y in range(12):
        for x in range(6):
            if (x + y // 2) % 6 in (0, 1) and (x + y) % 2 == 0: sw[y, x] = P['white']
    add('fx_sweep', img(sw), 'fx')
    sh = np.zeros((4, 24, 4), np.uint8); m = chamfer_mask(24, 4, 1); sh[m] = P['line']; sh[erode(m)] = FILLS['dis'][1]; sh[1, 2:22] = FILLS['dis'][0]; add('sheet_handle', img(sh), 'panel')
    sf = np.zeros((6, 4, 4), np.uint8)
    for y in range(6): sf[y][(X.BAYER[y % 4] < (1 - y / 6))] = P['nv3']
    add('scroll_fade_top', img(sf), 'list', '3h', [0, 0, 0, 0], 'tile'); add('scroll_fade_bot', img(sf[::-1].copy()), 'list', '3h', [0, 0, 0, 0], 'tile')

def bar_simple(w, h):
    m = chamfer_mask(w, h, 1); a = np.zeros((h, w, 4), np.uint8); a[m] = P['line']; m1 = erode(m); a[m1] = P['trough']; a[m1 & ~np.roll(m1, -1, 0)] = P['nv1']; return img(a)

# ---------------------------------------------------------------- 4b／5a／5b／5c 零件
def extras():
    add('family_crest', medal(40, 'gold', ring=2), 'family', note='家族等級大章（中間 gold 字）')
    for nm, f in (('tree_node', 'navy'), ('tree_node_sel', 'pri'), ('tree_node_gold', 'gold')):
        add(nm, flatpanel(22, 22, 5, [FILLS['navy'][2]] * 2 if f == 'navy' else ([FILLS['navy'][1]] * 2), gold=2 if f != 'navy' else 1), 'family', '9', [7, 7, 7, 7], 'tile')
    th = np.zeros((3, 4, 4), np.uint8); th[0] = P['g_hi']; th[1] = P['g_mid']; th[2] = P['g_lo']; add('tree_line_h', img(th), 'family', '3h', [0, 0, 0, 0], 'tile')
    tv = np.zeros((4, 3, 4), np.uint8); tv[:, 0] = P['g_hi']; tv[:, 1] = P['g_mid']; tv[:, 2] = P['g_lo']; add('tree_line_v', img(tv), 'family', '3v', [0, 0, 0, 0], 'tile')
    add('tree_joint', gem('pri', 5), 'family')
    add('egg_card', P9([7, 7, 7, 7], 5, [FILLS['navy'][1]] * 2, gold=2), 'family', '9', [7, 7, 7, 7], 'tile')
    for nm in ('room_dot_cur', 'room_dot_open', 'room_dot_locked'):
        add(nm, gem({'room_dot_cur': 'pri', 'room_dot_open': 'sec', 'room_dot_locked': 'violet'}[nm], 5) if nm != 'room_dot_locked' else img(np.where(np.array(gem('sec', 5))[..., 3:4] > 0, np.array(hx('#5E6484')), 0).astype(np.uint8)), 'family')
    for f, nm in (('pri', 'pill_fast_on'), ('dis', 'pill_fast_locked')): add(nm, button(f, 11, ch=3), 'inherit', '3h', [5, 0, 5, 0], 'tile')
    add('swatch_frame', flatpanel(12, 12, 2, [FILLS['navy'][3]] * 2, gold=1, glass=False), 'inherit', note='花紋色塊框（內 6×6 由引擎填父母 tint）')
    add('job_lv_badge', medal(13, 'pri', ring=1, spec=False), 'job', note='Lv 章（字 8 白）')

# ---------------------------------------------------------------- 頭像（A 頂旗槽 × B ×2 近鏡）
PORT = dict(n=22, scale=2, eyefrac=.5, frame=4, chamfer=5, maxShift=4, maxPop=3)
def portrait_parts():
    n, s = PORT['n'], PORT['scale']; win = n * s; fr = win + 8
    mk = chamfer_mask(fr, fr, PORT['chamfer'])
    F = np.array(frame(mk, fill=[FILLS['sec'][0], FILLS['sec'][1]], gold=2, glass=False, tex=False, rim_glints=False))
    inner = erode(erode(erode(erode(mk))))
    F[inner] = 0
    # 框頂內 2 行抖色陰影（實心像素、冇半透明）
    yy, xx = np.mgrid[0:fr, 0:fr]; top2 = inner & ~np.roll(inner, 2, 0)
    F[top2 & ((xx + yy) % 2 == 0)] = P['nv3']
    F[1, 6:fr - 6:9] = P['white']
    add('portrait_frame', img(F), 'portrait', note=f'{fr}×{fr}；內窗 {win}×{win} @(4,4)；寵物 crop ×{s}')
    mm = np.zeros((fr, fr, 4), np.uint8); mm[inner] = (255, 255, 255, 255); add('portrait_mask', img(mm), 'portrait', note='白＝畫得寵物（destination-in）')
    base3 = [np.array(hx('#EAF6FF')), np.array(hx('#C4E4F4')), np.array(hx('#8FBCDD'))]
    for st, (fk, _) in X.MOOD.items():
        bgc = [tuple((b * .62 + np.array(FILLS[fk][j]) * .38).astype(int)) for j, b in enumerate(base3)] if st != 'normal' else [tuple(b) for b in base3]
        if st == 'sleep': bgc = [FILLS['violet'][1], FILLS['violet'][2], FILLS['navy'][1]]
        t = (yy - 4) / win; g = dgrad(t * .85, bgc); B = np.zeros((fr, fr, 4), np.uint8); B[inner] = g[inner]
        ring = inner & (((xx - fr / 2) / (win * .45)) ** 2 + ((yy - fr * .5) / (win * .45)) ** 2 < 1) & ((xx + yy) % 2 == 0)
        B[ring] = np.clip(B[ring].astype(int) + 18, 0, 255)
        add(f'portrait_bg_{st}', img(B), 'portrait')
        gk = {'normal': 'sec', 'happy': 'rose', 'hungry': 'pri', 'sleepy': 'violet', 'sick': 'green', 'sleep': 'violet'}[st]
        mg = X.MOOD[st][1]
        if mg:
            b = medal(13, fk, ring=1, spec=False); bb = new(13, 13); bb.alpha_composite(b); putc(bb, X.mood_glyph(mg), 6.5, 6.5); add(f'mood_badge_{st}', bb, 'portrait')


def fit11(im, lim=11):
    a = np.array(im); m = a[..., 3] > 0; ys, xs = np.where(m); im = im.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    s = int(np.ceil(max(im.size) / lim))
    if s > 1:  # 縮細：每格揀最實嘅像素（唔用 BOX，避免半透明／糊色）
        a = np.array(im); h, w = a.shape[:2]; H2, W2 = -(-h // s), -(-w // s); o = np.zeros((H2, W2, 4), np.uint8)
        for y in range(H2):
            for x in range(W2):
                blk = a[y * s:(y + 1) * s, x * s:(x + 1) * s].reshape(-1, 4); op = blk[blk[:, 3] > 0]
                if len(op) * 2 >= len(blk) or (len(op) and s * s - len(op) <= 1): o[y, x] = op[len(op) // 2]
        im = img(o)
    return hard(im)

def acc_thumbs():
    """頭像飾品細章用嘅縮圖（≤11px）：舊線 14 件用 source front 最細一張；新線 wear_hat／5b 工作帽用 A2 合成差分"""
    src = f'{ART}/sprites/tuanrong/accessories/source'
    for it in sorted(os.listdir(src)):
        fs = sorted(glob.glob(f'{src}/{it}/front_S.png')) or sorted(glob.glob(f'{src}/{it}/front*.png')) or sorted(glob.glob(f'{src}/{it}/flower_M.png')) or sorted(glob.glob(f'{src}/{it}/part_tail*.png'))
        add(f'acc_thumb_{it}', fit11(Image.open(fs[0]).convert('RGBA')), 'portrait', note='頭像飾品細章（疊 med13_paper 中間）')
    base, info = X.compose_pet('A2', 'normal'); b = np.array(base)
    def diff(c):
        c = np.array(c); d = (c[..., 3] > 0) & ((b[..., 3] == 0) | (np.abs(c[..., :3].astype(int) - b[..., :3]).sum(-1) > 0)); c[~d] = 0; return img(c)
    p, _ = X.compose_pet('A2', 'normal', wear='hat'); add('acc_thumb_wear_hat', fit11(diff(p)), 'portrait')
    for job in ('chef', 'garden', 'post', 'watch'):
        hb, hp = job_hat('A2', job); add(f'acc_thumb_hat_{job}', fit11(hb), 'portrait')

# ---------------------------------------------------------------- icons
def icons():
    out = {}
    for n in ICN.ORDER:
        im = ICN.build(n); out[n] = im
        im.save(f'{KIT}/icons/ic_{n}@1x.png'); X.up(im, 3).save(f'{KIT}/icons/ic_{n}@3x.png')
    for n, rows in ICN.MINI.items():
        im = ICN.render_mini(rows); out[f'mini_{n}'] = im; im.save(f'{KIT}/icons/mini_{n}@1x.png'); X.up(im, 3).save(f'{KIT}/icons/mini_{n}@3x.png')
    return out

# ---------------------------------------------------------------- 打包
def pack(items, maxw=512, pad=1):
    names = sorted(items, key=lambda n: (-items[n].height, n)); x = y = rowh = 0; pos = {}
    for n in names:
        w, h = items[n].size
        if x + w + pad > maxw: x = 0; y += rowh + pad; rowh = 0
        pos[n] = (x, y); x += w + pad; rowh = max(rowh, h)
    H = y + rowh; H = 1 << (H - 1).bit_length(); A = new(maxw, H)
    for n, (px, py) in pos.items(): A.alpha_composite(items[n], (px, py))
    return A, pos

def write_atlas(kind, imgs, meta):
    A, pos = pack(imgs)
    for s in (1, 2, 3):
        J = dict(image=f'{kind}@{s}x.png', scale=s, size=[A.width * s, A.height * s], note='1x 原生像素；@2x/@3x nearest。nine＝[l,t,r,b] 喺 sprite px（×scale）；mode tile＝中段／邊用 tile（唔好拉伸）', frames={})
        for n, (x, y) in pos.items():
            w, h = imgs[n].size; d = dict(x=x * s, y=y * s, w=w * s, h=h * s)
            m = meta.get(n, {})
            for k in ('group', 'slice', 'mode', 'note'):
                if m.get(k): d[k] = m[k]
            if m.get('nine') is not None: d['nine'] = [v * s for v in m['nine']]
            J['frames'][n] = d
        (A if s == 1 else X.up(A, s)).save(f'{KIT}/atlas/{kind}@{s}x.png')
        json.dump(J, open(f'{KIT}/atlas/{kind}@{s}x.json', 'w'), ensure_ascii=False, indent=0)
    return A, pos

# ---------------------------------------------------------------- 字（Fusion Pixel 點陣 → 1x 白色 mask atlas）
def charset():
    S = set(chr(c) for c in range(0x20, 0x7F))
    S |= set('　，。、！？：；（）「」『』《》〈〉…—～・＋－×÷＝％／＃＆＠★☆✦♥◆●○▲▼←→↑↓·\'"')
    srcs = glob.glob(f'{ART}/ui/kit_hd2d/*.md') + glob.glob(f'{ART}/sprites/series2*/**/*.md', recursive=True) + glob.glob(f'{ART}/sprites/series2*/**/layout.json', recursive=True)
    srcs += glob.glob(f'{ART}/sprites/series2_long/*/long_5*.json') + [f'{HERE}/build_ui_hd2d_v2_mockups.py', f'{HERE}/build_ui_hd2d_v2_concept.py', f'{HERE}/ui_hd2d_v2_kit.py', f'{HERE}/build_ui_hd2d_v2_textsheet.py']
    srcs += glob.glob(f'{ART}/sprites/series2_house/house.json') + glob.glob(f'{ART}/sprites/series2/lessons/*.json')
    for p in srcs:
        if os.path.exists(p):
            for ch in open(p, encoding='utf-8', errors='ignore').read():
                if '\u3000' <= ch <= '\u9fff' or '\uff00' <= ch <= '\uffef': S.add(ch)
    return sorted(S)

def fonts():
    chars = charset(); res = {}
    for sz in (8, 10, 12):
        f = ImageFont.truetype(f'{FD}/fusion-pixel-{sz}px-proportional-zh_hk.ttf', sz)
        gt = f.getbbox('國')[1]; gb = max(f.getbbox('國gy')[3], f.getbbox('國')[3]); lh = gb - gt
        glyphs = {}; ims = {}
        for ch in chars:
            try: bb = f.getbbox(ch)
            except Exception: continue
            adv = int(round(f.getlength(ch)))
            if ch == ' ' or ch == '　' or bb[2] <= bb[0]:
                glyphs[ch] = dict(x=0, y=0, w=0, h=0, xoff=0, yoff=0, adv=adv); continue
            W_, H_ = bb[2] - bb[0], lh + 2
            m = Image.new('L', (W_ + 2, H_ + 2), 0); d = ImageDraw.Draw(m); d.fontmode = '1'; d.text((1 - bb[0], 1 - gt), ch, font=f, fill=255)
            M = np.array(m) > 127
            if not M.any(): glyphs[ch] = dict(x=0, y=0, w=0, h=0, xoff=0, yoff=0, adv=adv); continue
            ys, xs = np.where(M); x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
            a = np.zeros((y1 - y0, x1 - x0, 4), np.uint8); a[M[y0:y1, x0:x1]] = (255, 255, 255, 255)
            ims[ch] = img(a); glyphs[ch] = dict(xoff=int(x0 - 1 + bb[0]), yoff=int(y0 - 1), adv=adv)
        keys = {f'g{ord(c):05x}': c for c in ims}
        A, pos = pack({k: ims[c] for k, c in keys.items()}, maxw=1024 if sz == 12 else 512)
        for k, c in keys.items():
            x, y = pos[k]; glyphs[c].update(x=x, y=y, w=ims[c].width, h=ims[c].height)
        A.save(f'{FD}/font_fp{sz}@1x.png')
        res[f'fp{sz}'] = dict(image=f'font_fp{sz}@1x.png', ttf=f'fusion-pixel-{sz}px-proportional-zh_hk.ttf', size=sz, lineH=lh, scale=1, glyphs=glyphs)
    json.dump(dict(note='Fusion Pixel（OFL 1.1，見 OFL_fusion-pixel.txt）點陣字 1x 白色 mask；yoff＝由行頂（國字頂）計；引擎：tint→8 鄰描邊→1px 影（見 UI_KIT_V2.md §3）', fonts=res),
              open(f'{FD}/fonts_v2.json', 'w'), ensure_ascii=False)
    return res

# ---------------------------------------------------------------- 頭像裁位（全部 59 形態＋飾品）
OLD_ITEMS = sorted(os.listdir(f'{ART}/sprites/tuanrong/accessories/source'))
L5B = json.load(open(f'{ART}/sprites/series2_long/5b/long_5b.json'))
def job_hat(form, job, tier='t1'):
    """5b 工作帽 base 行 → (img, (dx,dy))：row.pivot 對齊 pet pivot"""
    J = L5B['jobs']['forms'].get(form, {}).get(job)
    if not J: return None
    r = [q for q in J['rows'] if q['clip'] in ('base', 'idle') and q['tier'] == tier][0]
    im = Image.open(f"{ART}/sprites/series2_long/5b/{J['png']}").convert('RGBA').crop((0, r['y'], r['frameW'], r['y'] + r['frameH']))
    return im, r['pivot']

def acc_rows(base, comp, x0):
    d = (comp[..., 3] > 0) & ((base[..., 3] == 0) | (np.abs(comp[..., :3].astype(int) - base[..., :3]).sum(-1) > 0))
    d = d[:, max(0, x0):x0 + PORT['n']]; r = np.where(d.any(1))[0]
    return (int(r[0]), int(r[-1])) if len(r) else None

def mitig(y0, rows):
    """飾品頂出框處理：shift（裁位上移 ≤4 行；眼由 50% → ≤68%）＋ pop（框頂外多畫 ≤3 行）；都唔夠 → badge（頭像角落出飾品細章）"""
    if rows is None: return dict(shift=0, pop=0, cut=0, vis=0, badge=False, note='飾品唔喺頭像欄位內')
    at, ab = rows; need = max(0, y0 - at)
    shift = min(need, PORT['maxShift']); pop = min(need - shift, PORT['maxPop']); cut = need - shift - pop
    top_vis = y0 - shift - pop; vis = max(0, min(ab, y0 - shift + PORT['n'] - 1) - max(at, top_vis) + 1); hgt = ab - at + 1
    badge = need > 0 and vis < max(3, hgt * .5)
    if need == 0 and ab > y0 + PORT['n'] - 1: return dict(shift=0, pop=0, cut=0, vis=int(vis), h=int(hgt), badge=False, note='頸飾喺框底以下：頭像唔加處理')
    return dict(shift=int(shift), pop=int(pop), cut=int(cut), vis=int(vis), h=int(hgt), badge=bool(badge))

def portrait_rects():
    import compose_accessory_runtime as C
    out = dict(version=2, note='頭像裁位（B ×2 近鏡，放喺 A 頂旗 52×52 框）。座標＝sprite px，已含 PAD 8（合成 canvas＝frame＋16）。'
               'rect＝[x0,y0,n]（無飾品）；acc.<item>＝{shift,pop,cut,vis,h,badge}：有嗰件飾品時 y0−＝shift，框頂外加畫 pop 行（×2）；badge＝飾品大部分出咗框 → 頭像右上角加飾品細章',
               params=PORT, pad=X.PAD, forms={}, aliases={})
    for form, an in X.ANCH.items():
        pet, info = X.compose_pet(form, 'normal'); ex, ey = info['eyes']; n = PORT['n']
        x0 = int(round(ex - n / 2)); y0 = int(round(ey - n * PORT['eyefrac'])); rec = dict(line=an['line'] if an['line'] == 'old' else 'from_ref', frame=info['frame'], eyes=[round(v, 2) for v in info['eyes']], rect=[x0, y0, n], acc={})
        piv = info['pivot']
        if an['line'] == 'old':
            NF = C.attach(form)['clips']['idle']['n']; S = info['frame']; bases = []
            for k in range(1, NF + 1):
                a = np.zeros((S + 16, S + 16, 4), np.uint8); a[8:8 + S, 8:8 + S] = C.body(form, 'idle', k); bases.append(a)
            for it in OLD_ITEMS:
                rs = []; hidden = False
                for k in range(1, NF + 1):
                    c, hid = C.compose(form, 'idle', k, [it]); hidden |= bool(hid); rs.append(acc_rows(bases[k - 1], c, x0))
                if hidden: rec['acc'][it] = dict(hidden=True); continue
                rs = [q for q in rs if q]; rec['acc'][it] = mitig(y0, (min(q[0] for q in rs), max(q[1] for q in rs)) if rs else None)
        else:
            b = np.array(pet)
            for w in ('hat', 'glasses'):
                p, _ = X.compose_pet(form, 'normal', wear=w); rec['acc'][f'wear_{w}'] = mitig(y0, acc_rows(b, np.array(p), x0))
        for job in ('chef', 'garden', 'post', 'watch'):
            jh = job_hat(form, job)
            if jh:
                hb, hp = jh; q = pet.copy(); q2 = new(q.width + 80, q.height + 80); q2.alpha_composite(q, (40, 40)); q2.alpha_composite(hb, (int(piv[0] - hp[0] + 40), int(piv[1] - hp[1] + 40)))
                qa = np.array(q2)[40:40 + q.height, 40:40 + q.width]; top_extra = np.array(q2)[:40, 40:40 + q.width]
                r = acc_rows(np.array(pet), qa, x0)
                ex_rows = np.where((top_extra[:, max(0, x0):x0 + n, 3] > 0).any(1))[0]
                if r and len(ex_rows): r = (int(ex_rows[0]) - 40, r[1])
                rec['acc'][f'hat_{job}'] = mitig(y0, r)
        out['forms'][form] = rec
    for form in X.S2T:
        pet, info = X.compose_pet(form, 'normal'); ex, ey = info['eyes']; n = PORT['n']
        out['forms'][form] = dict(line='series2', frame=48, eyes=[round(v, 2) for v in info['eyes']], rect=[int(round(ex - n / 2)), int(round(ey - n * PORT['eyefrac'])), n], acc={})
    for L in 'ABCDEFGH':
        for st, k in (('S3', 1), ('S5', 2), ('S6', 3)): out['aliases'][f'{st}{L}'] = f'{L}{k}'
    out['aliasNote'] = '細佬 S3／S5／S6 用返 from_ref 1／2／3 階 sprite（S3A＝A1 …）→ 用 alias 指去嗰個 form 嘅裁位；S5／S6 有 5b 工作帽'
    json.dump(out, open(f'{KIT}/portrait/portrait_rects.json', 'w'), ensure_ascii=False, indent=1)
    return out

if __name__ == '__main__':
    panels(); chips_btns(); bars(); medals(); extras(); portrait_parts(); acc_thumbs()
    ics = icons()
    ui_imgs = {n: f['img'] for n, f in FR.items()}
    write_atlas('ui_hd2d_v2', ui_imgs, FR)
    write_atlas('icons_hd2d_v2', ics, {n: dict(group='icon') for n in ics})
    F = fonts()
    PR = portrait_rects()
    print('frames', len(FR), 'icons', len(ics), 'fonts', {k: len(v['glyphs']) for k, v in F.items()}, 'portrait forms', len(PR['forms']))
