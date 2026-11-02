#!/usr/bin/env python3
"""《微光小圃》屋仔 → V3-A 光影（第 4 批）— 遊美 2026-11-02
以 4b 屋仔（series2_house/room）＋ 5a 擴房 3 間（series2_long/5a/rooms/room2–4）raw 層做底，跟概念 ui/style_ref/hd2d_v3/house_v3A_3x.png：
  ① 1x 像素層唔改（色盤、alpha 0/255 同 4b／5a 一樣）；出 223×446 相容層（v3 調色）＋ @3x 669×1338 烘焙層
  ② @3x 烘焙：室內暖光 lightmap（AO／牆腳接觸影／窗邊反光）、窗光體積光＋窗格地板光斑（按窗 slot 家具：冇／蕾絲窗簾／星星窗）、
     地板反射（木地板光澤，鏡像牆身＋窗）、bloom、暗角、split-tone LUT
  ③ 即時層：浮塵（只喺光柱入面密）、燈具光（lightmap lift＋光暈＋星芒）、家具／寵物地板倒影、紀念品（5b 手信）擺設光、寵物光（× petGlow）
家具 sprite 唔改（alpha 0/255），@3x 用 nearest；光影層先用真 alpha。純 Pillow／numpy，冇 AI 圖。
用法：python3 art-pet/tools/build_house_v3.py [rooms furniture souvenir json preview]（預設全部）"""
import os, sys, json, math, copy
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_garden_hd2d_v3 as G
import house_4b_room as R
B = G.B; ART = G.ART; S = 3
HS = f'{ART}/sprites/series2_house'; OUT = f'{HS}/v3'; S5 = f'{ART}/sprites/series2_long'
MX, MY, LW, LH, AW, AH = R.MX, R.MY, R.LW, R.LH, R.AW, R.AH
W3, H3, SW3, SH3 = LW * S, LH * S, AW * S, AH * S
hx, mix, gblur, to8, up3, smooth3 = G.hx, G.mix, G.gblur, G.to8, G.up3, G.smooth3
def save(a, p): G.save(a, p)
def ld(p): return G.ld(p)
def jdump(o, p):
    os.makedirs(os.path.dirname(p), exist_ok=True); json.dump(o, open(p, 'w'), ensure_ascii=False, indent=1)
HJ = json.load(open(f'{HS}/house.json'))
ROOMS = {'room1': dict(zh='屋仔（4b）', src=f'{HS}/room', srcRel='sprites/series2_house/room'),
         'room2': dict(zh='森林閣樓（5a）', src=f'{S5}/5a/rooms/room2', srcRel='sprites/series2_long/5a/rooms/room2'),
         'room3': dict(zh='星夜書房（5a）', src=f'{S5}/5a/rooms/room3', srcRel='sprites/series2_long/5a/rooms/room3'),
         'room4': dict(zh='海風小屋（5a）', src=f'{S5}/5a/rooms/room4', srcRel='sprites/series2_long/5a/rooms/room4')}
WIN = R.G['window']; WALL = R.G['wall']; BASE_Y = WALL[3]          # 窗洞 (30,98)–(76,150)；地腳線 y238
# ================================================================ 調色（每房 × 日夜）
P0 = {'day': dict(amb='#ffe4c2', pet='#fff4e8', sat=1.12, con=1.08, split=('#70509a', '#ffc884', .13), bloom=(.82, .30), fog=('#ffd8b0', .035),
                  vig=.26, vigc='#5a2814', rim=('#ffd49a', .5), bulb='#ffe9a0', lm='#ffe6c6', lmK=1.0, winBoost=.16,
                  beam='#ffd294', beamI=.24, patch='#ffdca4', patchI=.32, bounce='#ffc890', bounceI=.12, refl=.17, petI=.32, dust=1.0, lampK=.35),
      'night': dict(amb='#aab0e4', pet='#f2eaff', sat=.98, con=1.08, split=('#283070', '#ffd090', .11), bloom=(.66, .75), fog=('#2a2e5a', .05),
                    vig=.36, vigc='#140e30', rim=('#c8d4ff', .4), bulb='#ffe0a0', lm='#7a80b8', lmK=1.0, winBoost=.10,
                    beam='#a8c0ff', beamI=.22, patch='#b8ccff', patchI=.36, bounce='#8898e0', bounceI=.05, refl=.13, petI=.9, dust=.35, lampK=1.0)}
PR = {'room1': {}, 'room2': {'day': dict(amb='#fcebc8', split=('#4a6a70', '#f4e8a0', .09), beam='#fff0a8', patch='#fff2b8', bounce='#e8f0a8', lm='#f8f4dc'),
                             'night': dict(lm='#6e84a8', beam='#b0d0e8', patch='#c0e0f0')},
      'room3': {'day': dict(amb='#fde4d4', split=('#5a4aa0', '#ffd8c0', .10), beam='#ffe2c8', patch='#ffe8d0', lm='#f8ecec'),
                'night': dict(amb='#b0a8e8', lm='#7c74c0', beam='#c8b8ff', beamI=.26, patch='#d0c4ff', patchI=.42, bloom=(.62, .85), split=('#302070', '#ffd890', .12))},
      'room4': {'day': dict(amb='#fbf0e2', sat=1.06, split=('#3a6aa0', '#fff2d8', .08), beam='#fff8e0', beamI=.28, patch='#fffae8', patchI=.4, bounce='#d8f0ff', lm='#f4f8fc'),
                'night': dict(amb='#a4b8e8', lm='#6a84b8', beam='#98ccff', patch='#a8d8ff', split=('#1a3a70', '#ffe0a0', .10))}}
def params(room, var):
    p = copy.deepcopy(P0[var]); p.update(PR[room].get(var, {})); return p
def grade_h(rgb, p):
    """rgb 0–1：× ambientTint → 飽和 → 對比 → split-tone（同 garden v3 公式）"""
    c = rgb * hx(p['amb'])
    l = (c @ np.array([.299, .587, .114]))[..., None]; c = l + (c - l) * p['sat']; c = (c - .5) * p['con'] + .5
    sh, hi, a = hx(p['split'][0]), hx(p['split'][1]), p['split'][2]; l = (np.clip(c, 0, 1) @ np.array([.2126, .7152, .0722]))[..., None]
    return np.clip(c + (sh - .5) * a * (1 - l) ** 2 + (hi - .5) * a * l ** 2, 0, 1)
def make_lut(p):
    lut = np.zeros((16, 256, 3))
    for b in range(16):
        for gy in range(16):
            for rx in range(16): lut[gy, b * 16 + rx] = (rx / 15, gy / 15, b / 15)
    return grade_h(lut, p)
def lut_apply(rgba, lut): o = rgba.copy(); o[..., :3] = B.apply_lut(rgba[..., :3], lut); return o
# ================================================================ 幾何 mask（4b／5a 同一幾何 → 用 4b index）
_GEO = {}
def geo():
    if not _GEO:
        L = R.build_index(False); m = L['mid'].m; f = L['far'].m
        _GEO['floor'] = np.isin(m, R.IDX['FLOOR'] + R.IDX['SEAM']); _GEO['seam'] = np.isin(m, R.IDX['SEAM'])
        _GEO['wallp'] = np.isin(f, R.IDX['WALLP'] + R.IDX['DOT']); _GEO['wains'] = np.isin(f, R.IDX['WAINS'] + R.IDX['TRIM'])
        _GEO['sill'] = np.isin(f, R.IDX['SILL'])
    return _GEO
def A3():   # @3x 格每點嘅 art 座標
    yy, xx = np.mgrid[0:H3, 0:W3].astype(float); return (xx + .5) / S - MX, (yy + .5) / S - MY
def hole_mask(far_raw):
    a = far_raw[..., 3] == 0; m = np.zeros_like(a); x0, y0, x1, y1 = WIN; m[y0 + MY:y1 + MY, x0 + MX:x1 + MX] = a[y0 + MY:y1 + MY, x0 + MX:x1 + MX]; return m
# ================================================================ 窗光：體積光柱＋地板光斑（按窗家具 gobo）
WIN_ITEMS = {'none': dict(zh='冇窗家具（淨窗）', opacity=0), 'win_curtain': dict(zh='蕾絲窗簾', opacity=.62, lace=True), 'win_star': dict(zh='星星窗', opacity=.92)}
PATCH = dict(dx=30, skew=40, yFar=312, yNear=250, note='窗洞 (u,v)（u 左→右、v 上→下）→ 地板 (x＝60＋46u＋40(1−v)，y＝312−62v)：窗頂投到地板前面（近鏡頭），窗底近牆腳（光由左上高角度射入）')
def transmission(item, far_raw):
    """窗洞 46×52（art px）透光率 0–1：洞（far alpha 0）× 家具遮擋（窗簾＝蕾絲半透）"""
    x0, y0, x1, y1 = WIN; t = hole_mask(far_raw)[y0 + MY:y1 + MY, x0 + MX:x1 + MX].astype(float)
    it = WIN_ITEMS[item]
    if it['opacity'] > 0:
        f = HJ['furniture'][item]; sp = np.asarray(Image.open(f"{HS}/{f['png']}").convert('RGBA'))
        ax, ay = HJ['slots']['window']['anchor']; px, py = f['pivot']; ox, oy = ax - px, ay - py
        a = sp[y0 - oy:y1 - oy, x0 - ox:x1 - ox, 3] > 0
        blk = a * it['opacity']
        if it.get('lace'):   # 蕾絲：細孔 → 部分光漏
            yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]; blk = blk * (1 - .35 * (((xx + yy) % 3) == 0))
        t = t * (1 - blk)
    return t
def tex_sample(T, u, v):
    h, w = T.shape; ok = (u >= 0) & (u < 1) & (v >= 0) & (v < 1)
    uu = np.clip(u * w - .5, 0, w - 1); vv = np.clip(v * h - .5, 0, h - 1)
    i0, j0 = np.floor(vv).astype(int), np.floor(uu).astype(int); i1, j1 = np.minimum(i0 + 1, h - 1), np.minimum(j0 + 1, w - 1); fi, fj = vv - i0, uu - j0
    s = T[i0, j0] * (1 - fi) * (1 - fj) + T[i1, j0] * fi * (1 - fj) + T[i0, j1] * (1 - fi) * fj + T[i1, j1] * fi * fj
    return s * ok
def window_light(item, far_raw):
    """回傳 (beam, patch) @3x 白色 alpha（0–1）。引擎：lighter，tint／強度跟 grade.v3.windowBeam"""
    T = transmission(item, far_raw); X, Y = A3(); x0, y0, x1, y1 = WIN; ww, wh = x1 - x0, y1 - y0
    # 地板光斑（窗格投影）
    v = (PATCH['yFar'] - Y) / (PATCH['yFar'] - PATCH['yNear']); u = (X - 60 - PATCH['skew'] * (1 - v)) / ww
    pt = tex_sample(T, u, v) * (Y >= BASE_Y)
    patch = gblur(pt[..., None], 2.2)[..., 0] * .75 + gblur(pt[..., None], 9)[..., 0] * .35
    # 體積光柱：逐列 ray band（窗列 → 地板列），亮度＝該列平均透光；由窗口向地板淡出
    im = Image.new('L', (W3, H3), 0); col = T.mean(0)
    for i in range(ww * S):
        uu = (i + .5) / (ww * S); c = col[min(ww - 1, int(uu * ww))]
        if c <= .01: continue
        xw = x0 + uu * ww; q = [(xw, y0), (xw + 1 / S, y0), (xw + 1 / S, y1), (xw, y1),
                                 (60 + uu * ww + 1 / S, PATCH['yNear']), (60 + uu * ww + PATCH['skew'] + 1 / S, PATCH['yFar']), (60 + uu * ww + PATCH['skew'], PATCH['yFar'])]
        pts = [((qx + MX) * S, (qy + MY) * S) for qx, qy in q]
        lay = Image.new('L', (W3, H3), 0); ImageDraw.Draw(lay).polygon(pts, fill=int(255 * c)); im = Image.fromarray(np.maximum(np.asarray(im), np.asarray(lay)))
    bm = np.asarray(im).astype(float) / 255
    dist = np.clip((Y - y0) / (PATCH['yFar'] - y0), 0, 1); fade = (1 - dist) ** 1.3 * .8 + .2
    near_win = np.exp(-np.hypot(X - (x0 + x1) / 2, Y - (y0 + y1) / 2) / 40) * .2
    beam = gblur(bm[..., None], 4)[..., 0] * .6 + gblur(bm[..., None], 14)[..., 0] * .55
    beam = beam * (fade + near_win) * (1 - (Y < y0)) * ~((X > x0) & (X < x1) & (Y > y0) & (Y < y1))   # 窗洞入面唔加（bloom 處理）
    return np.clip(beam, 0, 1), np.clip(patch, 0, 1)
def beam_polygon():
    x0, y0, x1, y1 = WIN; return [[x0, y0], [x1, y0], [x1 + 30 + 10, PATCH['yNear']], [x1 + 30 + PATCH['skew'], PATCH['yFar']], [60 + PATCH['skew'], PATCH['yFar']], [x0, y1]]
# ================================================================ 室內 lightmap／light_add／反射
def interior(p, var):
    X, Y = A3(); g = geo(); night = var == 'night'
    lm = np.ones((H3, W3, 3)) * hx(p['lm'])[None, None] * p['lmK']
    ao = np.zeros((H3, W3))
    ao += np.exp(-np.abs(Y - WALL[1]) / 7) * .16                                         # 天花角
    ao += np.where(Y >= BASE_Y, np.exp(-(Y - BASE_Y) / 7) * .22, np.exp(-(BASE_Y - Y) / 3.5) * .12)  # 牆腳接觸影
    ao += ((X < WALL[0]) | (X > WALL[2])) * (Y < 300) * .10                                # 側牆
    ao += np.exp(-np.minimum(np.abs(X - WALL[0]), np.abs(X - WALL[2])) / 8) * (Y < BASE_Y) * .08   # 牆角
    ao += np.clip((Y - 330) / 120, 0, 1) * .14 + np.clip((X - 110) / 160, 0, 1) * .05      # 前景收暗／光由左嚟
    lm = lm * (1 - ao[..., None])
    cx, cy = (WIN[0] + WIN[2]) / 2, (WIN[1] + WIN[3]) / 2; d = np.hypot((X - cx) / 1.2, Y - cy)
    lm = lm * (1 + p['winBoost'] * np.exp(-d / 70)[..., None] * (1.2 if not night else .9))   # 窗邊較光
    add = np.zeros((H3, W3, 3))
    bc = hx(p['bounce'])
    add += np.exp(-((d - 36) / 18) ** 2)[..., None] * bc * p['bounceI'] * (Y < BASE_Y)[..., None]   # 窗框周圍牆身反光
    add += np.exp(-((X - 110) / 60) ** 2 - ((Y - 285) / 40) ** 2)[..., None] * bc * p['bounceI'] * .7 * g['floor'].repeat(S, 0).repeat(S, 1)[..., None]  # 地板受光
    add += np.exp(-((X - cx) / 26) ** 2 - ((Y - 153) / 3) ** 2)[..., None] * bc * p['bounceI'] * 1.6   # 窗台高光
    return np.clip(lm, 0, 1.2), np.clip(add, 0, 1)
def floor_reflect(comp3, p):
    """地板反射：鏡像地腳線以上（牆／窗）→ 地板，向前淡出；夾縫（SEAM）唔反射；回傳 RGBA"""
    g = geo(); by = (BASE_Y + MY) * S; o = np.zeros((H3, W3, 4)); n = min(H3 - by, by)
    src = comp3[by - n:by][::-1]
    o[by:by + n, :, :3] = gblur(src, 2.0) * .6 + gblur(src, 6) * .4
    yy = np.arange(n)[:, None] / S; fade = np.exp(-yy / 48) * p['refl']
    fl = up3(g['floor'] & ~g['seam'])[by:by + n].astype(float)
    plank = .75 + .25 * np.cos((np.arange(W3)[None, :] / S) * .9) ** 2                         # 木紋光澤唔均
    o[by:by + n, :, 3] = fade * fl * plank
    return o
def vignette3(p):
    yy, xx = np.mgrid[0:SH3, 0:SW3].astype(float); dd = ((xx / SW3 - .5) / .5) ** 2 + ((yy / SH3 - .46) / .52) ** 2
    o = np.zeros((SH3, SW3, 4)); o[..., :3] = hx(p['vigc']); o[..., 3] = np.clip(np.clip((dd - .32) / .9, 0, 1) ** 1.6 * p['vig'] * 1.7, 0, .9); return o
def grade_json(room, var, p, src_g):
    g = copy.deepcopy(src_g)
    g.update(name=f"{ROOMS[room]['zh'].split('（')[0]}・{'日間' if var == 'day' else '夜晚'}（V3-A）", ambientTint=p['amb'], petTint=p['pet'], saturation=p['sat'], contrast=p['con'],
             bloom=dict(threshold=p['bloom'][0], intensity=p['bloom'][1]), fog=dict(color=p['fog'][0], density=p['fog'][1]), vignette=p['vig'],
             rim=dict(color=p['rim'][0], intensity=p['rim'][1], dir=[-.7, -.7]), bulbGlowTint=p['bulb'], splitTone=dict(shadow=p['split'][0], highlight=p['split'][1], amount=p['split'][2]))
    x0, y0, x1, y1 = WIN
    g['v3'] = dict(
        note='V3-A 屋仔：@3x 烘焙層喺 x3/（669×1338＝層 223×446 ×3，同 4b 一樣 art＋(14,12)）；vignette@3x 係螢幕 585×1266。家具／寵物／紀念品同即時光唔烘焙。',
        layerSize3x=[W3, H3], screenSize3x=[SW3, SH3], layerOffset3x=[MX * S, MY * S], stack='../../../house_v3.json#stack',
        windowBeam=dict(beam=f'light/<window item 或 none>_beam@3x.png', patch=f'light/<window item 或 none>_patch@3x.png', tint=p['beam'], intensity=p['beamI'],
                        patchTint=p['patch'], patchIntensity=p['patchI'], blend='lighter', shimmer=dict(hz=.15, amp=.06, note='窗外雲影：intensity 慢慢 ±6%'),
                        rule='窗 slot 擺咩就揀邊張（none／win_curtain／win_star）；場景光，唔跟 petGlow',
                        petAtten=.6, petAttenNote='寵物 sprite 覆蓋位 beam/patch × (1-.7×petAlpha)，避免寵物喺光斑入面過曝'),
        flares=[dict(pos=[x0 + 4, y0 + 6], size='m' if var == 'day' else 's', tint='#fff4d8' if var == 'day' else '#d8e4ff', fps=2, phase=0, intensity=.55 if var == 'day' else .35, note='窗角光芒'),
                dict(pos=[x1 - 6, y1 - 4], size='s', tint='#fff8e8' if var == 'day' else '#e0e8ff', fps=3, phase=.5, intensity=.35 if var == 'day' else .2)],
        emitters=[dict(type='dust', glow='glow_12', tint='#fff2c8' if var == 'day' else '#d8e0ff', polygon=beam_polygon(), rate=1.4 * p['dust'], life=[5, 9], vy=[-2, 1], vx=[-1, 1], sway=3,
                       max=int(18 * p['dust']) + 2, add=.6 if var == 'day' else .35, note='浮塵：只喺窗光柱入面生（polygon art 座標）'),
                  dict(type='dust', glow='glow_12', tint='#ffe8c8' if var == 'day' else '#c8d0ff', rect=[16, 60, 179, 320], rate=.3, life=[6, 10], vy=[-2, 0], sway=3, max=5, add=.25, alpha=.5, note='房內零星浮塵')],
        lamps=dict(scale=p['lampK'], note='燈 slot 擺咗燈：furniture_v3.json lamps × 呢個 scale（日間 .35，夜晚 1）；場景燈唔跟 petGlow'),
        reflection=dict(baked='x3/floor_reflect@3x.png', realtime=dict(mirrorY=BASE_Y, alpha=round(p['refl'] * .9, 3), fadePx3=150, blur3=2, applyTo=['ysort 家具', '寵物', '紀念品（地板／檯面以外）'],
                        note='即時倒影：sprite 上下反轉，pivot y 鏡像到 2×地腳線… 實際做法：倒影頂＝sprite 底（pivot），alpha 由 alpha 向下 fadePx3 淡到 0；畫喺地氈之前（地氈唔反光）')),
        petLight=dict(sprite='scenes/hd2d_v3/fx/fx_glow_v3@3x.json#pet_pool', anchor='foot', offset3x=[0, 6], size3x=[240, 96], tint=p['bulb'], intensity=p['petI'], blend='lighter',
                      multiplyBy='petGlow', formLight='sprites/tuanrong/petglow_v3/<form>.json（逐幀 anchor）；sceneScale 用 houseScale', houseScale=dict(day=.5, night=1.0)[var],
                      rule='ui/kit_hd2d_v3/layout_hd2d_v3.json#petGlow — Kurt：「除左佢訓就會關」。屋仔：瞓床（sleep_same_bed／sleep_loop）＝0、sleepy＝.6、其餘醒＝1；fadeOut 600ms easeInQuad、醒返 fadeIn 400ms easeOutQuad＋150ms pulse 1→1.15→1。燈、窗光、紀念品光唔受影響。'),
        petPop=dict(contactShadow=dict(alpha=.34, rx=.30, ry=.06), rim='同花園 v3（sprites/tuanrong/rim，rim.intensity ×1.15）'))
    return g
# ================================================================ ① 房間
def build_room(room):
    src = ROOMS[room]['src']; out = {}
    for var in ('day', 'night'):
        d = f'{OUT}/rooms/{room}/{var}'; p = params(room, var); lut = make_lut(p)
        raws = {n: ld(f'{src}/{var}/raw/{n}.png') for n in ('sky', 'far', 'mid', 'fore')}
        L1 = {}
        for n, r in raws.items():
            a = lut_apply(r, lut); a[..., 3] = r[..., 3]; L1[n] = a; save(a, f'{d}/{n}.png')
        save(lut, f'{d}/lut.png')
        lm3, add3 = interior(p, var)
        lm1 = np.asarray(Image.fromarray(to8(np.clip(lm3, 0, 1))).resize((LW, LH), Image.BOX)).astype(float) / 255
        ad1 = np.asarray(Image.fromarray(to8(add3)).resize((LW, LH), Image.BOX)).astype(float) / 255
        bm, pt = window_light('none', raws['far'])
        b1 = np.asarray(Image.fromarray(to8(bm * p['beamI'] + pt * p['patchI'])).resize((LW, LH), Image.BOX)).astype(float)[..., None] / 255 * hx(p['beam'])
        save(np.clip(lm1, 0, 1), f'{d}/lightmap.png'); save(np.clip(ad1 + b1, 0, 1), f'{d}/light_add.png')   # 1x 相容：已含淨窗光
        hm = hole_mask(raws['far']); em = np.zeros((LH, LW, 4)); em[hm] = 1; save(em, f'{d}/emissive.png')
        L3 = {}
        for n in ('sky', 'far', 'mid', 'fore'):
            a = up3(L1[n])
            if n == 'fore': a = G.blur3(a, 2.4); a[..., 3] = np.where(a[..., 3] < 1 / 255, 0, a[..., 3])
            L3[n] = a; save(a, f'{d}/x3/{n}@3x.png')
        save(np.clip(lm3, 0, 1), f'{d}/x3/lightmap@3x.png'); save(add3, f'{d}/x3/light_add@3x.png')
        em3 = up3(em); save(em3, f'{d}/x3/emissive@3x.png')
        comp = L3['sky'][..., :3]
        for n in ('far', 'mid'): comp = comp * (1 - L3[n][..., 3:]) + L3[n][..., :3] * L3[n][..., 3:]
        fr = floor_reflect(comp, p); save(fr, f'{d}/x3/floor_reflect@3x.png')
        c2 = comp * (1 - fr[..., 3:]) + fr[..., :3] * fr[..., 3:]
        c2 = np.clip(c2 * np.clip(lm3, 0, 1.2) + add3 + (bm * p['beamI'] + pt * p['patchI'])[..., None] * hx(p['beam']), 0, 1)
        gb = dict(bloom=dict(threshold=p['bloom'][0], intensity=p['bloom'][1])); bl = G.bloom3(em3 * np.array([1, 1, 1, .9 if var == 'day' else .5]), c2, gb); save(bl, f'{d}/x3/bloom@3x.png')
        e1 = np.asarray(Image.fromarray(to8(bl)).resize((LW, LH), Image.BOX)).astype(float) / 255; save(e1, f'{d}/emissive_blur.png')
        vg = vignette3(p); save(vg, f'{d}/x3/vignette@3x.png')
        save(np.asarray(Image.fromarray(to8(vg)).resize((AW, AH), Image.BOX)).astype(float) / 255, f'{d}/vignette.png')
        g = grade_json(room, var, p, json.load(open(f'{src}/{var}/grade.json'))); jdump(g, f'{d}/grade.json')
        out[var] = dict(dir=f'rooms/{room}/{var}', src=f"{ROOMS[room]['srcRel']}/{var}/raw")
        print(room, var, 'ok')
    return out
# ================================================================ ② 家具光（全房共用）
LAMPS = {'lamp_mushroom': dict(tint='#ffc27a', halo='#ffd8a0', liftR=120, liftK=1.35, pool=(82, 19), flare='m', flicker=dict(type='breathe', hz=.25, amp=.05),
                               emitter=None),
         'lamp_firefly': dict(tint='#d8f890', halo='#e8ff b0'.replace(' ', ''), liftR=108, liftK=1.2, pool=(72, 17), flare='s', flicker=dict(type='firefly', hz=.9, amp=.18),
                              emitter=dict(type='firefly', glow='glow_12', tint='#d8ff90', around=[0, -2], radius=10, rate=.8, life=[2, 4], max=4, add=.8, note='瓶入面螢火蟲飄出少少再返入去'))}
def radial(sz, p=1.6, sx=1.0, sy=1.0):
    yy, xx = np.mgrid[0:sz[1], 0:sz[0]].astype(float); r = np.hypot((xx - sz[0] / 2 + .5) / (sz[0] / 2 * sx), (yy - sz[1] / 2 + .5) / (sz[1] / 2 * sy))
    return np.clip(1 - r, 0, 1) ** p
def build_furniture():
    d = f'{OUT}/furniture'; js = {}
    for k, f in HJ['furniture'].items():
        e = dict(slot=f['slot'], x3=f'furniture/x3/{k}@3x.png')
        for key in ('png', 'front', 'emissive'):
            if key in f:
                a = ld(f"{HS}/{f[key]}"); a[..., 3] = (a[..., 3] > .5); nm = os.path.basename(f[key])[:-4]; save(up3(a), f'{d}/x3/{nm}@3x.png')
        if 'front' in f: e['x3Front'] = f'furniture/x3/{k}_front@3x.png'
        # 接觸 AO（軟影，真 alpha）：取代 4b 硬橢圓 shadow
        if 'shadow' in f or f['slot'] == 'rug':
            sw, sh_ = f.get('shadow', (f['size'][0] - 4, 5)); W_, H_ = int(sw * S * 1.3) + 12, int(max(sh_, 4) * S * 2.4) + 12
            a = radial((W_, H_), 1.2) * .55 + radial((W_, H_), 3, .7, .55) * .45; o = np.zeros((H_, W_, 4)); o[..., :3] = hx('#3c2428')
            o[..., 3] = np.clip(a, 0, 1) * (.42 if f['slot'] != 'rug' else .22); save(o, f'{d}/{k}_ao@3x.png')
            e['ao'] = dict(png=f'furniture/{k}_ao@3x.png', center='anchor（底中）＋(0,+1) art', blend='source-over', alpha=1, note='取代 4b shadow 橢圓；× lightmap')
        if f['slot'] in ('bed', 'table', 'lamp'): e['reflect'] = True
        if k in LAMPS:
            L = LAMPS[k]; gc = f['glowCenter']; px_, py_ = f['pivot']; e['lightCenter'] = [gc[0] - px_, gc[1] - py_]
            r3 = L['liftR'] * S; lift = np.zeros((2 * r3, 2 * r3, 4)); lift[..., :3] = hx(L['tint']); lift[..., 3] = (radial((2 * r3, 2 * r3), 1.0) * .95 + radial((2 * r3, 2 * r3), 3) * .6) * L['liftK']
            save(lift, f'{d}/{k}_lift@3x.png')
            hs = 96 * S // 2 * 2; halo = np.zeros((hs, hs, 4)); halo[..., :3] = hx(L['halo']); halo[..., 3] = radial((hs, hs), 2.2) * .8 + radial((hs, hs), 6, .35, .35) * .6
            save(np.clip(halo, 0, 1), f'{d}/{k}_halo@3x.png')
            pw, ph = L['pool'][0] * S * 2, L['pool'][1] * S * 2; pool = np.zeros((ph, pw, 4)); pool[..., :3] = hx(L['tint']); pool[..., 3] = radial((pw, ph), 1.2) * .9
            save(pool, f'{d}/{k}_pool@3x.png')
            e['light'] = dict(lift=dict(png=f'furniture/{k}_lift@3x.png', at='lightCenter', blend='lighter 落 lightmap（multiply 之前）', alpha='grade.v3.lamps.scale'),
                              halo=dict(png=f'furniture/{k}_halo@3x.png', at='lightCenter', blend='lighter（lightmap 之後）', alpha='0.4 × lamps.scale × flicker'),
                              pool=dict(png=f'furniture/{k}_pool@3x.png', at='anchor＋(0,−1)', blend='lighter（lightmap 之後、ysort 之前）', alpha='0.85 × lamps.scale'),
                              flare=dict(size=L['flare'], tint=L['halo'], fps=3, intensity=.8, at='lightCenter'), bloom=dict(src=f'furniture/x3/{k}_emissive@3x.png', note='入 bloom pass'),
                              flicker=L['flicker'], emitter=L['emitter'], tint=L['tint'], petGlow=False, note='場景燈：唔跟 petGlow（Kurt 規則只熄寵物光）；取代 4b _glow.png')
        if f['slot'] == 'window':
            e['windowLight'] = dict(beam=f'light/{k}_beam@3x.png', patch=f'light/{k}_patch@3x.png', transmission=WIN_ITEMS[k]['opacity'], note=WIN_ITEMS[k]['zh'] + '：窗光經過家具 gobo')
        js[k] = e
    for it in WIN_ITEMS:
        far = ld(f'{HS}/room/day/raw/far.png'); bm, pt = window_light(it, far)
        for nm, a in (('beam', bm), ('patch', pt)):
            o = np.ones((H3, W3, 4)); o[..., 3] = a; save(o, f'{OUT}/light/{it}_{nm}@3x.png')
    jdump(dict(note='家具 V3：sprite 唔改（alpha 0/255），x3/ 係 nearest ×3；AO／燈光／窗光係真 alpha 光影層。座標同 4b house.json（slot anchor − pivot）。', furniture=js,
               windowNone=dict(beam='light/none_beam@3x.png', patch='light/none_patch@3x.png', note='窗 slot 空：淨窗（只有中間直窗框）'),
               patchMapping=PATCH, beamPolygon=beam_polygon()), f'{OUT}/furniture_v3.json')
    print('furniture ok', len(js))
    return js
# ================================================================ ③ 紀念品（5b 手信）擺設
SV_LIGHT = {'sv_lantern': dict(glow='#ffd070', r=16, a=.75, flicker=dict(type='breathe', hz=.6, amp=.15), flare='s'),
            'sv_starstone': dict(glow='#fff2a0', r=12, a=.55, flicker=dict(type='twinkle', hz=1.2, amp=.3), flare='s'),
            'sv_rainbow': dict(glow='#ffc8f0', r=10, a=.35, flicker=None, flare=None),
            'sv_shell': dict(glow='#e0f4ff', r=8, a=.25, flicker=dict(type='glint', hz=.3, amp=1.0), flare='s'),
            'sv_bottle': dict(glow='#d8f0ff', r=8, a=.2, flicker=dict(type='glint', hz=.25, amp=1.0), flare='s'),
            'sv_cloud': dict(glow='#fff0fa', r=8, a=.18, flicker=None, flare=None)}
def sv_spots():
    """擺位（art 座標，pivot＝底中）；requires＝需要邊個 slot 擺咗咩"""
    sp = []
    for i, x in enumerate((36, 48, 70)): sp.append(dict(id=f'sill_{i}', pos=[x, 151], requires=dict(window=None), note='窗台（窗 slot 空先用；窗簾／星星窗有花盆箱遮住）'))
    sp += [dict(id='table_0', pos=[32, 283], requires=dict(table='table_stump')), dict(id='table_1', pos=[57, 283], requires=dict(table='table_stump')),
           dict(id='table_0r', pos=[30, 281], requires=dict(table='table_round')), dict(id='table_1r', pos=[56, 281], requires=dict(table='table_round')),
           # 舊 shelf_0 (152,92) 同層架第 3 盆盆栽重疊：層架 3 盆已佔滿板面（板 x116–163，盆 119–160），冇位擺手信 → 取消，改加 floor_2

           dict(id='floor_0', pos=[170, 318], requires={}, note='右下牆角地板（永遠可用）'), dict(id='floor_1', pos=[176, 300], requires={}), dict(id='floor_2', pos=[150, 346], requires={}, note='右前地板（取代舊 shelf_0）')]
    return sp
def build_souvenir():
    d = f'{OUT}/souvenir'; L5 = json.load(open(f'{S5}/5b/long_5b.json'))['souvenirs']; js = {}
    for s in L5:
        k = s['id']; a = ld(f"{S5}/5b/{s['px']}"); a[..., 3] = a[..., 3] > .5; save(up3(a), f'{d}/x3/{k}@3x.png')
        e = dict(zh=s['zh'], px=f"sprites/series2_long/5b/{s['px']}", x3=f'souvenir/x3/{k}@3x.png', pivot=s['pxPivot'], ao=dict(png='souvenir/sv_ao@3x.png', alpha=.8), reflect=True)
        if k in SV_LIGHT:
            L = SV_LIGHT[k]; r3 = L['r'] * S * 2; o = np.zeros((r3, r3, 4)); o[..., :3] = hx(L['glow']); o[..., 3] = radial((r3, r3), 2.0) * L['a']
            save(o, f'{d}/{k}_glow@3x.png'); e['light'] = dict(glow=f'souvenir/{k}_glow@3x.png', at='pivot 上 5px（art）', blend='lighter（lightmap 之後）', flicker=L['flicker'], flare=L['flare'],
                                                             dayScale=.5, nightScale=1.0, petGlow=False, note='擺設光＝場景光，唔跟 petGlow')
        js[k] = e
    o = np.zeros((10 * S, 18 * S, 4)); o[..., :3] = hx('#3c2428'); o[..., 3] = radial((18 * S, 10 * S), 1.4) * .5; save(o, f'{d}/sv_ao@3x.png')
    jdump(dict(note='5b 遠足手信喺屋仔擺設（V3）：pixel sprite 唔改（alpha 0/255；x3 nearest），加 AO、倒影、發光手信嘅光暈＋星芒。', souvenirs=js, spots=sv_spots(),
               rules=dict(maxShown=5, order='最新攞返嚟嘅優先；spot 按表序揀第一個 requires 符合嘅空位', ysort='floor_* 參與 ysort（sortY＝pos y）；sill／table／shelf 跟住佢下面嗰件家具 sortY＋0.05')),
          f'{OUT}/souvenir_v3.json')
    print('souvenir ok', len(js)); return js
# ================================================================ house_v3.json
STACK = [
 dict(layer='sky', file='x3/sky@3x.png', fallback1x='sky.png', blend='source-over', parallax=.5, baked=True, note='窗外景'),
 dict(layer='far', file='x3/far@3x.png', fallback1x='far.png', blend='source-over', parallax=1.0, baked=True),
 dict(layer='wall_items', realtime=True, note='window／wall slot 家具 x3（× ambientTint）'),
 dict(layer='mid', file='x3/mid@3x.png', fallback1x='mid.png', blend='source-over', parallax=1.0, baked=True),
 dict(layer='floor_reflect', file='x3/floor_reflect@3x.png', blend='source-over', parallax=1.0, baked=True, note='地板反射（牆＋窗）'),
 dict(layer='reflections', realtime=True, note='ysort 家具／寵物／紀念品倒影（grade.v3.reflection.realtime）'),
 dict(layer='rug', realtime=True, note='rug slot（地氈唔反光，蓋住倒影）'),
 dict(layer='ao', realtime=True, note='furniture_v3 *_ao@3x ＋ 寵物 contact shadow ＋ 紀念品 sv_ao'),
 dict(layer='lamp_pool', realtime=True, blend='lighter', note='燈地面光池（× lamps.scale）'),
 dict(layer='ysort', realtime=True, note='燈、床 back、檯、寵物（sprite × petTint × ambientTint＋rim；寵物光池 × petGlow 喺寵物前畫）、紀念品；床 front sortY＝床 y＋0.1'),
 dict(layer='fore', file='x3/fore@3x.png', fallback1x='fore.png', blend='source-over', parallax=1.3, baked=True),
 dict(layer='lightmap', file='x3/lightmap@3x.png', fallback1x='lightmap.png', blend='multiply', baked=True, note='燈 lift（*_lift@3x）先 lighter 疊落 lightmap 再 multiply'),
 dict(layer='light_add', file='x3/light_add@3x.png', fallback1x='light_add.png', blend='lighter', baked=True, note='窗邊反光、地板受光、窗台高光（1x fallback 已含淨窗光）'),
 dict(layer='window_light', realtime=True, file='../../../light/<item>_{beam,patch}@3x.png', blend='lighter', note='grade.v3.windowBeam（tint × intensity）；窗 slot 換家具就換張'),
 dict(layer='bloom', file='x3/bloom@3x.png', fallback1x='emissive_blur.png', blend='lighter', baked=True, alpha='grade.bloom.intensity'),
 dict(layer='lamp_halo', realtime=True, blend='lighter', note='燈光暈＋星芒＋燈 emissive bloom；紀念品光'),
 dict(layer='pet_glow', realtime=True, blend='lighter', note='petglow_v3 逐幀 halo／core／粒子 × petGlow × houseScale'),
 dict(layer='flares', realtime=True, blend='lighter', sprite='scenes/hd2d_v3/fx/fx_glow_v3@3x.json#flare_*', note='grade.v3.flares'),
 dict(layer='particles', realtime=True, sprite='scenes/hd2d_v3/fx/particles_v3@3x.json＋fx_glow_v3@3x.json', note='grade.v3.emitters（浮塵 polygon＝窗光柱）'),
 dict(layer='fog', realtime=True, blend='source-over', note='fillRect grade.fog'),
 dict(layer='vignette', file='x3/vignette@3x.png', fallback1x='vignette.png', blend='source-over', screen=True, baked=True)]
def build_json(rooms):
    jdump(dict(version='house-v3-1.0', by='遊美 2026-11-02（第 4 批）', concept='ui/style_ref/hd2d_v3/house_v3A_3x.png（V3-A）',
               note='屋仔 4b room1＋5a room2–4 全部房（日／夜）轉 V3-A。幾何、slot、行走區、家具 pivot 全部同 4b house.json；只換光影。',
               rooms={k: dict(zh=ROOMS[k]['zh'], variants=v) for k, v in rooms.items()}, layers3x=['sky', 'far', 'mid', 'fore', 'lightmap', 'light_add', 'floor_reflect', 'bloom', 'emissive', 'vignette'],
               layers1x=['sky', 'far', 'mid', 'fore', 'lightmap', 'light_add', 'emissive', 'emissive_blur', 'vignette', 'lut', 'grade.json'], stack=STACK,
               furniture='furniture_v3.json', souvenirs='souvenir_v3.json', fx='scenes/hd2d_v3/fx（flare／glow／dust／pet_pool 共用花園 v3）',
               petGlow=dict(source='ui/kit_hd2d_v3/layout_hd2d_v3.json#petGlow', house=dict(awake=1.0, sleepy=.6, sleep_bed=0.0, sleep_together=0.0, sit=1.0, prank=1.0),
                            rule='Kurt：「除左佢訓就會關」— 寵物自己嘅光（光池、halo、core、粒子、emissive）瞓覺即熄（600ms easeInQuad），醒返 400ms easeOutQuad＋pulse；燈／窗光／紀念品光唔熄'),
               crossfade='同 4b：19:00／06:00 日夜 crossfade 2–4 秒（所有 x3 層＋grade 數值一齊 lerp）'), f'{OUT}/house_v3.json')
# ================================================================ 預覽合成（@3x 螢幕 585×1266；同 stack 公式）
def oversp(img, sp, x0, y0): G.oversp(img, sp, int(round(x0)), int(round(y0)))
def addc(img, sp, cx, cy, a):
    h, w = sp.shape[:2]; x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(img.shape[1], x0 + w), min(img.shape[0], y0 + h)
    if xa < xb and ya < yb: s = sp[ya - y0:yb - y0, xa - x0:xb - x0]; img[ya:yb, xa:xb] += s[..., :3] * s[..., 3:] * a
_C = {}
def C(p):
    if p not in _C: _C[p] = ld(p)
    return _C[p]
def furn_sprite(k, part='png'):
    f = HJ['furniture'][k]; nm = os.path.basename(f[part])[:-4]; return C(f'{OUT}/furniture/x3/{nm}@3x.png'), f['pivot']
def pet_sprite(form, fn):
    import build_petglow_v3 as PG
    d, AT, EM = PG.atlas(form); fi = d['frames'][fn]; f = fi['frame']; pv = (fi['pivotPx']['x'], fi['pivotPx']['y'])
    return up3(AT[f['y']:f['y'] + f['h'], f['x']:f['x'] + f['w']]), pv
def L3(x, y): return (x + MX) * S, (y + MY) * S
def reflect(img, sp, px3, py3, alpha, fade=150):
    """sp 已 tint；倒影：上下反轉，頂貼 pivot（腳底）"""
    fl = sp[::-1].copy(); h = fl.shape[0]
    # sprite 底部空白行（pivot 下面）唔要
    fl[..., 3] *= alpha * np.clip(1 - np.arange(h)[:, None] / fade, 0, 1); fl = G.blur3(fl, 2) if fl[..., 3].max() > 0 else fl
    oversp(img, fl, px3, py3)
def poly_points(poly, n, rnd):
    im = Image.new('L', (AW, AH), 0); ImageDraw.Draw(im).polygon([tuple(p) for p in poly], fill=1); m = np.asarray(im); ys, xs = np.nonzero(m)
    i = rnd.randint(0, len(xs), n); return xs[i] + rnd.rand(n), ys[i] + rnd.rand(n)
def compose(room, var, furn, pets=(), svs=(), seed=5):
    """furn: {slot: item}；pets: [dict(form, frame, foot, glow, bed=False)]；svs: [(sv_id, spot_id)]"""
    import build_petglow_v3 as PG
    d = f'{OUT}/rooms/{room}/{var}'; g = json.load(open(f'{d}/grade.json')); v3 = g['v3']; amb = hx(g['ambientTint']); F = G.fx()
    Lx = {n: C(f'{d}/x3/{n}@3x.png') for n in ('sky', 'far', 'mid', 'fore', 'floor_reflect')}
    img = Lx['sky'][..., :3].copy()
    def over(a): nonlocal img; img = img * (1 - a[..., 3:]) + a[..., :3] * a[..., 3:]
    def tinted(sp): o = sp.copy(); o[..., :3] *= amb; return o
    over(Lx['far'])
    for sl in ('window', 'wall'):
        k = furn.get(sl)
        if k: sp, pv = furn_sprite(k); ax, ay = HJ['slots'][sl]['anchor']; x, y = L3(ax - pv[0], ay - pv[1]); oversp(img, tinted(sp), x, y)
    over(Lx['mid']); over(Lx['floor_reflect'])
    SVJ = json.load(open(f'{OUT}/souvenir_v3.json')); spots = {s['id']: s for s in SVJ['spots']}
    ys = []   # (sortY, kind, payload)
    for sl in ('lamp', 'bed', 'table'):
        k = furn.get(sl)
        if k: ys.append((HJ['slots'][sl]['anchor'][1], 'furn', (sl, k, 'png')))
    if furn.get('bed'): ys.append((HJ['slots']['bed']['anchor'][1] + .1, 'furn', ('bed', furn['bed'], 'front')))
    for pt in pets: ys.append(((HJ['slots']['bed']['anchor'][1] + .05) if pt.get('bed') else pt['foot'][1], 'pet', pt))
    for sv, sid in svs:
        s = spots[sid]; base = s['id'].split('_')[0]
        sy = s['pos'][1] if base == 'floor' else (HJ['slots']['table']['anchor'][1] + .05 if base == 'table' else -1)
        ys.append((sy, 'sv', (sv, s)))
    ys.sort(key=lambda t: t[0])
    # 倒影（畫喺地氈之前）
    ra = v3['reflection']['realtime']['alpha']
    for sy, kind, pl in ys:
        if kind == 'furn' and pl[2] == 'png':
            sp, pv = furn_sprite(pl[1]); ax, ay = HJ['slots'][pl[0]]['anchor']; x, y = L3(ax - pv[0], ay); reflect(img, tinted(sp)[:pv[1] * S + S], x, y, ra)
        if kind == 'pet' and not pl.get('bed'):
            sp, pv = pet_sprite(pl['form'], pl['frame']); fx_, fy = pl['foot']; x, y = L3(fx_ - pv[0], fy); reflect(img, tinted(sp)[:pv[1] * S + S], x, y, ra * .9)
    if furn.get('rug'):
        sp, pv = furn_sprite(furn['rug']); ax, ay = HJ['slots']['rug']['anchor']; x, y = L3(ax - pv[0], ay - pv[1]); oversp(img, tinted(sp), x, y)
    FJ = json.load(open(f'{OUT}/furniture_v3.json'))['furniture']
    for sl in ('rug', 'lamp', 'bed', 'table'):
        k = furn.get(sl)
        if k and 'ao' in FJ[k]: ax, ay = HJ['slots'][sl]['anchor']; a = C(f"{OUT}/{FJ[k]['ao']['png']}"); h, w = a.shape[:2]; cx, cy = L3(ax, ay + 1); oversp(img, a, cx - w / 2, cy - h / 2)
    lk = v3['lamps']['scale']; lamp = furn.get('lamp')
    if lamp:
        ax, ay = HJ['slots']['lamp']['anchor']; cx, cy = L3(ax, ay - 1); addc(img, C(f'{OUT}/furniture/{lamp}_pool@3x.png'), cx, cy, .85 * lk)
    posts = []; petm = np.zeros(img.shape[:2])
    for sy, kind, pl in ys:
        if kind == 'furn':
            sl, k, part = pl; sp, pv = furn_sprite(k, part); ax, ay = HJ['slots'][sl]['anchor']; x, y = L3(ax - pv[0], ay - pv[1]); oversp(img, tinted(sp), x, y)
        elif kind == 'pet':
            foot = pl['foot']
            img, post = PG.draw_pet(img, 'house', g, (pl['form'], pl['frame']), pl['glow'], seed, foot=foot, ss=v3['petLight']['houseScale']); posts += post
            if not pl.get('bed'):
                psp, ppv = pet_sprite(pl['form'], pl['frame']); px0, py0 = L3(foot[0] - ppv[0], foot[1] - ppv[1]); px0, py0 = int(round(px0)), int(round(py0))
                hh, ww = psp.shape[:2]; y0_, x0_ = max(py0, 0), max(px0, 0)
                petm[y0_:py0 + hh, x0_:px0 + ww] = np.maximum(petm[y0_:py0 + hh, x0_:px0 + ww], psp[y0_ - py0:min(hh, petm.shape[0] - py0), x0_ - px0:min(ww, petm.shape[1] - px0), 3])
        else:
            sv, s = pl; sp = C(f'{OUT}/souvenir/x3/{sv}@3x.png'); pv = SVJ['souvenirs'][sv]['pivot']; x, y = L3(s['pos'][0], s['pos'][1])
            a = C(f'{OUT}/souvenir/sv_ao@3x.png'); oversp(img, a, x - a.shape[1] / 2, y - a.shape[0] / 2 + 1)
            if s['id'].startswith('floor'): reflect(img, tinted(sp)[:pv[1] * S + S], x - pv[0] * S, y, ra)
            oversp(img, tinted(sp), x - pv[0] * S, y - pv[1] * S)
    over(Lx['fore'])
    lm = C(f'{d}/x3/lightmap@3x.png')[..., :3].copy()
    if lamp:
        lc = FJ[lamp]['lightCenter']; ax, ay = HJ['slots']['lamp']['anchor']; lx, ly = L3(ax + lc[0], ay + lc[1]); addc(lm, C(f'{OUT}/furniture/{lamp}_lift@3x.png'), lx, ly, lk)
    img = img * lm + C(f'{d}/x3/light_add@3x.png')[..., :3]
    wi = furn.get('window') or 'none'; wb = v3['windowBeam']
    pk = (1 - wb.get('petAtten', .6) * petm)[..., None]   # 寵物喺窗光光斑入面唔好過曝：寵物身上 beam/patch 只加 40%
    img += (C(f'{OUT}/light/{wi}_beam@3x.png')[..., 3:] * hx(wb['tint']) * wb['intensity'] + C(f'{OUT}/light/{wi}_patch@3x.png')[..., 3:] * hx(wb['patchTint']) * wb['patchIntensity']) * pk
    img += C(f'{d}/x3/bloom@3x.png')[..., :3] * g['bloom']['intensity']
    rnd = np.random.RandomState(seed)
    if lamp:
        L = FJ[lamp]['light']; addc(img, C(f'{OUT}/furniture/{lamp}_halo@3x.png'), lx, ly, .4 * lk)
        em = C(f'{OUT}/furniture/x3/{lamp}_emissive@3x.png'); sp, pv = furn_sprite(lamp); x, y = L3(ax - pv[0], ay - pv[1])
        e = em.copy(); e[..., :3] = hx(L['tint']); e = G.blur3(e, 5); addc(img, e, x + e.shape[1] / 2, y + e.shape[0] / 2, .5 * lk)
        G.addsp(img, F[f"flare_{L['flare']['size']}_0{1 + rnd.randint(0, 6)}"], lx, ly, L['flare']['tint'], L['flare']['intensity'] * lk)
        if L.get('emitter'):
            em_ = L['emitter']
            for i in range(em_['max']):
                px_, py_ = lx + rnd.uniform(-1, 1) * em_['radius'] * S, ly + rnd.uniform(-1, .6) * em_['radius'] * S
                G.addsp(img, F[em_['glow']], px_, py_, em_['tint'], em_['add'] * lk); img[int(py_) - 1:int(py_) + 2, int(px_) - 1:int(px_) + 2] = np.maximum(img[int(py_) - 1:int(py_) + 2, int(px_) - 1:int(px_) + 2], hx('#f4ffc0'))
    for sv, sid in svs:
        e = SVJ['souvenirs'][sv]
        if 'light' in e:
            s = spots[sid]; x, y = L3(s['pos'][0], s['pos'][1] - 5); sc = .5 if var == 'day' else 1.0; addc(img, C(f"{OUT}/{e['light']['glow']}"), x, y, sc)
            if e['light']['flare']: G.addsp(img, F[f"flare_s_0{2 + rnd.randint(0, 3)}"], x + 3, y - 3, '#ffffff', .5 * sc)
    for fn in posts: fn(img)
    for f in v3['flares']: G.addsp(img, F[f"flare_{f['size']}_{1 + rnd.randint(0, 6):02d}"], *L3(*f['pos']), f['tint'], f['intensity'])
    for e in v3['emitters']:
        n = e['max']
        if 'polygon' in e: xs, ys_ = poly_points(e['polygon'], n, rnd)
        else: xs, ys_ = rnd.uniform(e['rect'][0], e['rect'][2], n), rnd.uniform(e['rect'][1], e['rect'][3], n)
        for i in range(n):
            x, y = L3(xs[i], ys_[i]); G.addsp(img, F[e['glow']], x, y, e['tint'], e['add'] * .8 * e.get('alpha', 1))
            dsp = F[f'dust_{1 + i % 6:02d}'].copy(); dsp[..., 3] *= e.get('alpha', 1) * (.6 + .4 * rnd.rand()); oversp(img, dsp, x - 12, y - 12)
    fc = hx(g['fog']['color']); img = img * (1 - g['fog']['density']) + fc * g['fog']['density']
    img = np.clip(img, 0, 1)[MY * S:MY * S + SH3, MX * S:MX * S + SW3]; vg = C(f'{d}/x3/vignette@3x.png'); img = img * (1 - vg[..., 3:]) + vg[..., :3] * vg[..., 3:]
    return Image.fromarray(to8(img), 'RGB')
def compose_v2(room, var, furn, pets=()):
    """前：4b／5a 原本 1x 合成（house_4b_room.compose）→ ×3 nearest"""
    import build_petglow_v3 as PG
    sp = []
    for sl, k in furn.items():
        if not k: continue
        f = HJ['furniture'][k]; s = HJ['slots'][sl]; ax, ay = s['anchor']; im = np.array(Image.open(f"{HS}/{f['png']}").convert('RGBA')); pv = f['pivot']
        z = {'floor': 0, 'wall': 1}.get(s['layer'], 2 + ay / 1000); sp.append((z, im, ax - pv[0], ay - pv[1], 'furn'))
        if 'front' in f: sp.append((2 + (ay + .1) / 1000, np.array(Image.open(f"{HS}/{f['front']}").convert('RGBA')), ax - pv[0], ay - pv[1], 'furn'))
        if 'glow' in f and var == 'night':
            gl = np.array(Image.open(f"{HS}/{f['glow']}").convert('RGBA')); gc = f['glowCenter']; sp.append((9, gl, ax - pv[0] + gc[0] - gl.shape[1] // 2, ay - pv[1] + gc[1] - gl.shape[0] // 2, 'glow'))
    for pt in pets:
        d, AT, EM = PG.atlas(pt['form']); fi = d['frames'][pt['frame']]; f = fi['frame']; a = (AT[f['y']:f['y'] + f['h'], f['x']:f['x'] + f['w']] * 255).astype(np.uint8)
        fx_, fy = pt['foot']; zz = 2 + ((HJ['slots']['bed']['anchor'][1] + .05) if pt.get('bed') else fy) / 1000
        sp.append((zz, a, fx_ - fi['pivotPx']['x'], fy - fi['pivotPx']['y'], 'pet'))
    return Image.fromarray(R.compose(var, ROOMS[room]['src'], sp)).resize((SW3, SH3), Image.NEAREST)
SET = {k: v['items'] for k, v in HJ['sets'].items()}
def main():
    what = sys.argv[1:] or ['furniture', 'souvenir', 'rooms', 'json', 'preview']
    if 'furniture' in what: build_furniture()
    if 'souvenir' in what: build_souvenir()
    rooms = {}
    if 'rooms' in what:
        for r in ROOMS: rooms[r] = build_room(r)
    for r in ROOMS:
        if r in what: rooms[r] = build_room(r)
    if 'json' in what:
        build_json({r: dict(day=f'rooms/{r}/day', night=f'rooms/{r}/night', src=ROOMS[r]['srcRel']) for r in ROOMS})
    if 'preview' in what:
        import preview_house_v3 as PV; PV.run()
if __name__ == '__main__':
    main()
