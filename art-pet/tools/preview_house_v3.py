#!/usr/bin/env python3
"""《微光小圃》屋仔 V3 預覽（第 4 批）：前後對比、疊 UI v3、寵物光瞓覺熄規則、家具光、紀念品擺設。由 build_house_v3.py preview 呼叫。"""
import os, sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_house_v3 as H
SW3, SH3 = H.SW3, H.SH3
PV = f'{H.OUT}/preview'; GD = '/workspace/game-design/house_v3'
def font(sz, b=True):
    import ui_hd2d_v3_lib as UL
    return ImageFont.truetype(UL.FONT_SRC['sansb' if b else 'sans'], sz, index=UL.FONT_TTC_INDEX)
def ui_house(scene, deco=False, furn=None):
    import build_ui_hd2d_v3_mockups as M3, ui_hd2d_v3_lib as UL
    if deco: M3._SC[('h', tuple(furn), (), .6)] = scene.convert('RGBA'); UL.SCREEN[0] = 'house_deco'; return M3.s_house_deco().convert('RGB')
    M3._SC[('h', None, None, .6)] = scene.convert('RGBA'); UL.SCREEN[0] = 'house'; return M3.s_house().convert('RGB')
def sheet(cols, title, sub=None, scale=1.0):
    w, h = int(SW3 * scale), int(SH3 * scale); n = len(cols); S_ = Image.new('RGB', (20 + n * (w + 20), h + 120), (14, 16, 30)); d = ImageDraw.Draw(S_)
    d.text((20, 14), title, font=font(26), fill=(255, 236, 184))
    for i, (im, t) in enumerate(cols):
        S_.paste(im.resize((w, h), Image.LANCZOS) if scale != 1 else im, (20 + i * (w + 20), 100)); d.text((20 + i * (w + 20), 62), t, font=font(19, False), fill=(240, 230, 200))
    return S_
def stack_rows(rows, gap=10):
    W = max(r.width for r in rows); Ht = sum(r.height for r in rows) + gap * (len(rows) - 1); o = Image.new('RGB', (W, Ht), (14, 16, 30)); y = 0
    for r in rows: o.paste(r, (0, y)); y += r.height + gap
    return o
PET_DAY = dict(form='evo_still_tide', frame='emo_sleepy_01', foot=(96, 300), glow=.6)
PET_N = dict(form='evo_still_lumi', frame='idle_01', foot=(100, 296), glow=1.0)
ROOMSET = {'room1': 'A', 'room2': 'A', 'room3': 'B', 'room4': 'B'}
def run():
    os.makedirs(PV, exist_ok=True); os.makedirs(GD, exist_ok=True); allv3 = []
    for room, st in ROOMSET.items():
        furn = H.SET[st]; rows = []
        for var, pet in (('day', PET_DAY), ('night', PET_N)):
            v2 = H.compose_v2(room, var, furn, [pet]); v3 = H.compose(room, var, furn, [pet]); ui = ui_house(v3)
            v3.save(f'{GD}/{room}_{var}_v3_3x.png', optimize=True); ui.save(f'{GD}/{room}_{var}_v3_ui_3x.png', optimize=True); allv3.append((room, var, v3))
            rows.append(sheet([(v2, '前：v2（4b／5a 1x ×3）'), (v3, '後：V3-A 光影 @3x'), (ui, '後＋UI kit v3')], f"{H.ROOMS[room]['zh']}・{'日間' if var == 'day' else '夜晚'} — 組合 {st}（{H.HJ['sets'][st]['zh']}）", scale=.6))
        s = stack_rows(rows); s.save(f'{GD}/compare_{room}.png', optimize=True); s.save(f'{PV}/compare_{room}.png', optimize=True); print('preview', room)
    # 總覽
    k = 3; tw, th = SW3 // k, SH3 // k; ov = Image.new('RGB', (20 + 8 * (tw + 10), th + 110), (14, 16, 30)); d = ImageDraw.Draw(ov)
    d.text((20, 12), '《微光小圃》屋仔 V3-A — 4 間房 × 日／夜', font=font(26), fill=(255, 236, 184))
    for i, (room, var, im) in enumerate(allv3):
        ov.paste(im.resize((tw, th), Image.LANCZOS), (20 + i * (tw + 10), 90)); d.text((20 + i * (tw + 10), 60), f"{room} {var}", font=font(17, False), fill=(240, 230, 200))
    ov.save(f'{GD}/overview.png', optimize=True); ov.save(f'{PV}/overview.png', optimize=True)
    # 寵物光：瞓覺關（同一隻 lumi，屋仔夜晚）
    A = H.SET['A']; cols = []
    for t, pet in (('醒（petGlow 1）', dict(PET_N)), ('眼瞓 sleepy（.6）', dict(PET_N, frame='emo_sleepy_01', glow=.6)),
                   ('瞓床 sleep_loop（0＝熄）', dict(form='evo_still_lumi', frame='sleep_loop_01', foot=(118, 252), glow=0.0, bed=True))):
        cols.append((H.compose('room1', 'night', A, [pet]).crop((0, 560, 585, 1060)), t))
    s = sheet([(c, t) for c, t in cols], '屋仔寵物光 × petGlow（Kurt：「除左佢訓就會關」）— 燈／窗光唔熄', scale=1.0).crop((0, 0, 20 + 3 * 605, 100 + 500 + 20))
    s.save(f'{GD}/petglow_sleep_rule.png', optimize=True); s.save(f'{PV}/petglow_sleep_rule.png', optimize=True)
    # 家具光：窗 3 款（日）＋燈 2 款／冇燈（夜）
    cols = []
    for wi in (None, 'win_curtain', 'win_star'):
        f = dict(A, window=wi); cols.append((H.compose('room1', 'day', f, []).crop((0, 200, 585, 1000)), f"窗：{H.WIN_ITEMS[wi or 'none']['zh']}（日）"))
    for la in ('lamp_mushroom', 'lamp_firefly', None):
        f = dict(A, lamp=la); cols.append((H.compose('room1', 'night', f, []).crop((0, 200, 585, 1000)), f"燈：{H.HJ['furniture'][la]['zh'] if la else '冇燈'}（夜）"))
    s = sheet(cols, '家具光：窗光 gobo（窗 slot）＋燈具 lightmap lift／光暈／光池', scale=.62); s = s.crop((0, 0, s.width, 100 + int(800 * .62) + 20))
    s.save(f'{GD}/furniture_lights.png', optimize=True)
    # 紀念品擺設
    f = dict(A, window=None, table='table_stump', wall='wall_shelf')
    svs = [('sv_lantern', 'sill_0'), ('sv_shell', 'sill_1'), ('sv_starstone', 'sill_2'), ('sv_bottle', 'table_0'), ('sv_pinecone', 'table_1'), ('sv_rainbow', 'floor_2'), ('sv_mushroom', 'floor_0'), ('sv_cloud', 'floor_1')]
    cols = [(H.compose('room1', v, f, [], svs), f"紀念品（5b 手信）擺設・{'日' if v == 'day' else '夜'}") for v in ('day', 'night')]
    s = sheet(cols, '紀念品擺設 V3：窗台／檯面／層架／地板（發光手信＝場景光）', scale=.8); s.save(f'{GD}/souvenirs_display.png', optimize=True)
    # 佈置 UI（組合 B）
    fB = dict(bed='bed_cloud', table='table_round', rug='rug_leaf', wall='wall_frame', window='win_star', lamp='lamp_firefly'); sc = H.compose('room1', 'day', fB, []); ui = ui_house(sc, deco=True, furn=[fB[k] for k in ('bed', 'table', 'rug', 'wall', 'window', 'lamp')])
    ui.save(f'{GD}/house_deco_v3_ui_3x.png', optimize=True)
    # 同概念對照
    con = Image.open(f'{H.ART}/ui/style_ref/hd2d_v3/house_v3A_3x.png').convert('RGB').resize((SW3, SH3))
    s = sheet([(con, '概念 house_v3A（第 1 批）'), (Image.open(f'{GD}/room1_day_v3_ui_3x.png'), '實裝 V3（今批）＋UI v3')], '屋仔 V3-A：概念 vs 實裝', scale=.6)
    s.save(f'{GD}/concept_vs_build.png', optimize=True)
    print('preview ok')
if __name__ == '__main__': run()
