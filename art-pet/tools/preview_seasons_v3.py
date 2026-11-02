#!/usr/bin/env python3
"""第 5 批預覽：四季 16 款 V3（前 v2 季節 vs 後 V3、疊 UI v3）、細佬 series2 petglow、屋仔修正前後。"""
import os, sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_seasons_v3 as SS
G = SS.G; B = G.B; hx = B.hx; S = 3; SW3, SH3, MX, MY = G.SW3, G.SH3, G.MX, G.MY
GD = '/workspace/game-design/seasons_v3'; PV = f'{SS.OUTS}/preview'
def font(sz, b=True):
    import ui_hd2d_v3_lib as UL
    return ImageFont.truetype(UL.FONT_SRC['sansb' if b else 'sans'], sz, index=UL.FONT_TTC_INDEX)
def particles(img, sk, H, seed=3, n=None):
    P = SS.pfx(); F = G.fx(); rnd = np.random.RandomState(seed); a = np.asarray(img).astype(float) / 255
    for t in P['_types'][sk]:
        k = t['emitter']['perVariant'][H] * (.75 if H == 'H4' else 1)
        cnt = int(round((n or t['emitter']['max']) * k))
        for i in range(cnt):
            v = t['variants'][i % len(t['variants'])]; fr = t['anims'][v][rnd.randint(0, len(t['anims'][v]))]
            x, y = rnd.uniform(0, SW3), rnd.uniform(0, SH3 * (.75 if t['name'] in ('firefly',) else .95))
            if t['name'] == 'firefly': y = rnd.uniform(SH3 * .5, SH3 * .8)
            if 'glow' in t: G.addsp(a, F[t['glow']['sprite'].split('#')[1]], x, y, t['glow']['tint'], t['glow']['add'] * (.8 if H != 'H4' else 1))
            G.oversp(a, P[fr], int(x - 12), int(y - 12))
    return Image.fromarray(G.to8(np.clip(a, 0, 1)), 'RGB')
def season3x(sk, H, pet=True, pet_glow=1.0):
    return particles(G.compose3x(f'seasons/{sk}/{H}', with_pet=pet, pet_glow=pet_glow), sk, H)
def v2season(sk, H):
    """v2 季節（1x 預烘層 ×3 nearest，加 lightmap）"""
    d = f'{SS.V2}/seasons/{sk}/{H}'; L = {n: SS.ld(f'{d}/{n}.png') for n in ('sky', 'far', 'mid', 'fore')}
    img = L['sky'][..., :3].copy()
    for n in ('far', 'mid', 'fore'): img = img * (1 - L[n][..., 3:]) + L[n][..., :3] * L[n][..., 3:]
    img = img * SS.ld(f'{d}/lightmap.png')[..., :3] + SS.ld(f'{SS.V2}/{H}/light_add.png')[..., :3]
    img = np.clip(img, 0, 1)[MY:MY + G.AH, MX:MX + G.AW]
    return Image.fromarray(G.to8(img), 'RGB').resize((SW3, SH3), Image.NEAREST)
def ui_garden(scene):
    import build_ui_hd2d_v3_mockups as M3, ui_hd2d_v3_lib as UL
    key = [k for k in M3._SC if k[0] == 'g'] if hasattr(M3, '_SC') else []
    M3._SC.clear(); M3._SC[('g', 'awake', 1.0)] = scene.convert('RGBA')
    return M3, UL
def sheet(cols, title, scale):
    w, h = int(SW3 * scale), int(SH3 * scale); S_ = Image.new('RGB', (20 + len(cols) * (w + 16), h + 110), (14, 16, 30)); d = ImageDraw.Draw(S_)
    d.text((20, 12), title, font=font(24), fill=(255, 236, 184))
    for i, (im, t) in enumerate(cols):
        S_.paste(im.resize((w, h), Image.LANCZOS), (20 + i * (w + 16), 92)); d.text((20 + i * (w + 16), 58), t, font=font(17, False), fill=(240, 230, 200))
    return S_
# ---------------------------------------------------------------- 細佬 petglow
import build_kid_petglow_v3 as KP
_KG = {}
def kg(k):
    if k not in _KG:
        J = json.load(open(f'{KP.OUT}/{k}.json')); sj = json.load(open(f"{KP.OUT}/{J['sheet']}")); sh = SS.ld(f"{KP.OUT}/{sj['image']}")
        _KG[k] = (J, {n: sh[f['y']:f['y'] + f['h'], f['x']:f['x'] + f['w']] for n, f in sj['frames'].items()})
    return _KG[k]
def draw_kid(img, g, k, clip, i, foot, glow, ss, scene_lit=True, seed=4):
    """img：@3x 層座標 float RGB。回傳 post（lightmap 後先畫嘅自發光）"""
    fr = KP.strip(k, clip)[i].copy(); J, FR = kg(k)
    if scene_lit:
        tint = hx(g['petTint']) * hx(g['ambientTint']); fr[..., :3] *= tint
    sp3 = G.up3(fr); cx, cy = (foot[0] + MX) * S, (foot[1] + MY) * S
    yy, xx = np.mgrid[0:img.shape[0], 0:img.shape[1]]
    shd = np.exp(-(((xx - cx) / (sp3.shape[1] * .26)) ** 2 + ((yy - cy - 2) / 7) ** 2) ** 2) * .3; img *= 1 - shd[..., None]
    pool = G.fx()['pet_pool']; pool = np.asarray(Image.fromarray(G.to8(pool)).resize(tuple(J['pool']['size3x']), Image.BICUBIC)).astype(float) / 255
    pl = g['v3']['petLight']; pool[..., :3] = G.mix(hx(pl['tint']), hx(J['pool']['tint']), .5)
    import build_petglow_v3 as PG
    PG.addc(img, pool, cx, cy + 4, pl['intensity'] * .35 * glow * (1 + ss * .4))
    G.oversp(img, sp3, int(cx - KP.PV[0] * S), int(cy - KP.PV[1] * S))
    def post(I):
        if glow <= 0: return
        fn = f'{clip}_{i + 1:02d}'; fd = J['frames'][fn]; fd = J['frames'][fd['same']] if 'same' in fd else fd
        for dx, dy, r, wt in fd['a']:
            hn = 'halo_s' if r <= 24 else 'halo_m' if r <= 40 else 'halo_l'; PG.addc(I, FR[hn], cx + dx, cy + dy, wt * fd['e'] * ss * glow * .8)
        a0 = fd['a'][0]; PG.addc(I, FR['core_12'], cx + a0[0], cy + a0[1], .7 * glow * ss)
        em = J['emitter']; rnd = np.random.RandomState(seed)
        for n in range(em['max']):
            t = rnd.rand(); px = cx + a0[0] + rnd.uniform(-1, 1) * em['spread3'] + rnd.uniform(*em['vx3']) * t * 2; py = cy + a0[1] + rnd.uniform(-1, 1) * em['spread3'] * .6 + rnd.uniform(*em['vy3']) * t * 2
            PG.addc(I, FR['halo_s'], px, py, em['glowAlpha'] * ss * glow); G.oversp(I, FR[em['frames'][n % 4]], int(px - 10), int(py - 10))
    return post
def kid_grid():
    idx = json.load(open(f'{KP.OUT}/index.json')); forms = [f['form'] for f in idx['forms']]
    cell = 150; cols_ = [('idle', 0, 1.0, '醒 idle'), ('walk', 2, 1.0, '行 walk'), ('eat', 1, 1.0, '食 eat'), ('sleep', 0, 0.0, '瞓 sleep＝0')]
    W = 20 + 3 * (len(cols_) * cell + 30); rows = (len(forms) + 2) // 3; H = 100 + rows * (cell + 26)
    sheet = Image.new('RGB', (W, H), (14, 16, 30)); d = ImageDraw.Draw(sheet); d.text((20, 12), '細佬 series2 有光源形態 petglow v3（33 款）— 醒／行／食＝光、瞓＝熄（Kurt：「除左佢訓就會關」）', font=font(22), fill=(255, 236, 184))
    g = json.load(open(f'{SS.V3}/H4/grade.json'))
    for n, k in enumerate(forms):
        gx, gy = 20 + (n % 3) * (len(cols_) * cell + 30), 70 + (n // 3) * (cell + 26)
        d.text((gx, gy), f"{k} {kg(k)[0]['name']}（{kg(k)[0]['lightType']}）", font=font(15, False), fill=(240, 230, 200))
        for j, (clip, i, glow, t) in enumerate(cols_):
            img = np.zeros((G.H3, G.W3, 3)) + np.array([.07, .08, .16])
            foot = (60, 80); post = draw_kid(img, g, k, clip, i, foot, glow, 1.0, scene_lit=False); post(img)
            cx, cy = (foot[0] + MX) * S, (foot[1] + MY) * S; c = Image.fromarray(G.to8(np.clip(img, 0, 1)), 'RGB').crop((cx - 75, cy - 120, cx + 75, cy + 30))
            sheet.paste(c, (gx + j * cell, gy + 22))
    return sheet
def ui_overlay(scene):
    import build_ui_hd2d_v3_mockups as M3, ui_hd2d_v3_lib as UL
    M3._SC.clear(); M3._SC[('g', 'hungry', 1.0)] = scene.convert('RGBA'); UL.SCREEN[0] = 'garden_season'
    return M3.s_home().convert('RGB')
def kid_in(final, g, k, clip, i, foot, glow, ss):
    a = np.zeros((G.H3, G.W3, 3)); a[MY * S:MY * S + SH3, MX * S:MX * S + SW3] = np.asarray(final).astype(float) / 255
    post = draw_kid(a, g, k, clip, i, foot, glow, ss); post(a)
    return Image.fromarray(G.to8(np.clip(a[MY * S:MY * S + SH3, MX * S:MX * S + SW3], 0, 1)), 'RGB')
SZH = {'spring': '春', 'summer': '夏', 'autumn': '秋', 'winter': '冬'}; HZH = {'H1': 'H1 晨光暖調', 'H2': 'H2 黃昏電影感', 'H3': 'H3 清新冷調', 'H4': 'H4 夜燈'}
def main(tmp='/tmp/icv3/pv'):
    os.makedirs(GD, exist_ok=True); os.makedirs(PV, exist_ok=True); os.makedirs(tmp, exist_ok=True)
    out = []
    def save(im, n, key=False):
        im.save(f'{GD}/{n}', optimize=True); out.append(n)
        if key: im.save(f'{PV}/{n}', optimize=True)
    V3 = {}
    for sk in SS.SEASONS:
        cols = []
        for H in ('H1', 'H2', 'H3', 'H4'):
            V3[sk, H] = season3x(sk, H); V3[sk, H].save(f'{tmp}/{sk}_{H}.png')
            save(V3[sk, H], f'{sk}_{H}_v3_3x.png')
            cols += [(v2season(sk, H), f'{HZH[H]} 前 v2'), (V3[sk, H], f'{HZH[H]} 後 V3')]
        save(sheet(cols, f'{SZH[sk]}（{sk}）H1–H4：前 v2 季節 vs 後 V3（HD-2D）', .32), f'compare_{sk}.png', True)
    w, h = int(SW3 * .3), int(SH3 * .3); ov = Image.new('RGB', (40 + 4 * (w + 12), 110 + 4 * (h + 40)), (14, 16, 30)); d = ImageDraw.Draw(ov)
    d.text((20, 14), '四季 16 款 V3 總覽（列＝季節，欄＝H1–H4）', font=font(26), fill=(255, 236, 184))
    for r, sk in enumerate(SS.SEASONS):
        for c, H in enumerate(('H1', 'H2', 'H3', 'H4')):
            x, y = 20 + c * (w + 12), 70 + r * (h + 40); d.text((x, y), f'{SZH[sk]} {HZH[H]}', font=font(18, False), fill=(240, 230, 200)); ov.paste(V3[sk, H].resize((w, h), Image.LANCZOS), (x, y + 28))
    save(ov, 'overview_16.png', True)
    save(sheet([(ui_overlay(V3[sk, 'H2']), f'{SZH[sk]} H2 + UI v3') for sk in SS.SEASONS], '四季 V3 疊 UI kit v3（主畫面）', .4), 'ui_v3_seasons.png', True)
    save(kid_grid(), 'kid_petglow_grid.png', True)
    # 細佬喺場景：花園 H4 醒 vs 瞓；屋仔夜 醒 vs 瞓
    import build_house_v3 as HV, preview_house_v3 as PH
    gH4 = json.load(open(f'{SS.V3}/H4/grade.json')); base = G.compose3x('H4', with_pet=False)
    cols = []
    for k in ('S4C', 'A1', 'F1'):
        cols += [(kid_in(base, gH4, k, 'idle', 0, (112, 340), 1.0, 1.0), f'花園 H4 {k} 醒＝1'), (kid_in(base, gH4, k, 'sleep', 0, (112, 340), 0.0, 1.0), f'{k} 瞓＝0')]
    gn = json.load(open(f'{HV.OUT}/rooms/room1/night/grade.json')); hn = HV.compose('room1', 'night', HV.SET['A'], [])
    for k in ('S4C', 'F1'):
        cols += [(kid_in(hn, gn, k, 'idle', 0, (100, 300), 1.0, 1.0), f'屋仔夜 {k} 醒'), (kid_in(hn, gn, k, 'sleep', 0, (100, 300), 0.0, 1.0), f'{k} 瞓')]
    save(sheet(cols, '細佬喺場景：醒＝光、瞓＝熄（場景燈照開）', .3), 'kid_in_scene.png', True)
    # 屋仔修正前後
    T = '/tmp/icv3'
    cols = [(Image.open(f'{T}/hb_day.png'), '日間 前'), (Image.open(f'{T}/ha_day.png'), '日間 後（暖啲＋寵物唔過曝）'),
            (Image.open(f'{T}/hb_night.png'), '夜晚 前'), (Image.open(f'{T}/ha_night.png'), '夜晚 後（燈光圈加大）'),
            (Image.open(f'{T}/hb_sv.png'), '手信 前（彩虹疊盆栽）'), (Image.open(f'{T}/ha_sv.png'), '手信 後（改 floor_2）')]
    save(sheet(cols, '屋仔已知問題修正 前 vs 後', .34), 'house_fix_before_after.png', True)
    cols = []
    for r in ('room2', 'room3', 'room4'): cols += [(Image.open(f'{T}/hb_{r}.png'), f'{r} 日 前'), (Image.open(f'{T}/ha_{r}.png'), f'{r} 日 後')]
    save(sheet(cols, '屋仔其他房日間色調 前 vs 後', .34), 'house_fix_rooms_day.png')
    return out
if __name__ == '__main__':
    print(main())
