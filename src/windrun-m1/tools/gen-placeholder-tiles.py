#!/usr/bin/env python3
"""產生 art/adventure/tileset_placeholder.png（16 欄 × 2 列，16px 圖塊）＋ tileset_placeholder.tsj。
遊美圖塊集未覆蓋（室內地板／迴風場牆／櫃台／長凳／閘口／起跑線／風車／水井／告示牌／倒木／出口）嘅佔位圖塊。
全部由本腳本以幾何圖形繪出，**無任何第三方素材**；色票沿用 mossy_slope 暖暗色系。僅作內部步行 build，交由遊美出正式圖塊後替換。"""
import json, os
from PIL import Image, ImageDraw
OUT = os.path.join(os.path.dirname(__file__), '..', 'art', 'adventure')
os.makedirs(OUT, exist_ok=True)
NAMES = ['ph_floor_a','ph_floor_b','ph_wall_stone','ph_rock','ph_counter_l','ph_counter_m','ph_counter_r','ph_bench_l','ph_bench_m','ph_bench_r','ph_gate_closed','ph_gate_open','ph_startline','ph_formation','ph_regmark','ph_exit',
         'ph_well_00','ph_well_01','ph_well_10','ph_well_11','ph_mill_00','ph_mill_01','ph_mill_10','ph_mill_11','ph_sign','ph_notice','ph_scout','ph_door_plain','ph_log_00','ph_log_01','ph_log_10','ph_log_11']
C = dict(wood=(138,106,69,255), wood2=(122,92,59,255), wd=(86,62,40,255), stone=(104,100,96,255), stone2=(84,80,78,255), rock=(48,46,52,255), rock2=(36,34,42,255), white=(238,232,214,255), yellow=(255,214,106,255),
         green=(86,132,78,255), grass=(94,140,84,255), cyan=(120,226,214,255), steel=(150,156,168,255), blue=(70,110,170,255), red=(190,80,70,255), cloth=(214,200,160,255), clear=(0,0,0,0))
img = Image.new('RGBA', (16 * 16, 2 * 16), C['clear'])
def tile(i):
    t = Image.new('RGBA', (16, 16), C['clear']); return t, ImageDraw.Draw(t)
def put(i, t): img.paste(t, ((i % 16) * 16, (i // 16) * 16))
for i, n in enumerate(NAMES):
    t, d = tile(i)
    if n.startswith('ph_floor'):
        d.rectangle([0, 0, 15, 15], fill=C['wood'] if n.endswith('a') else C['wood2'])
        for y in (0, 5, 10): d.line([0, y, 15, y], fill=C['wd'])
        d.line([5 if n.endswith('a') else 11, 0, 5 if n.endswith('a') else 11, 4], fill=C['wd'])
    elif n == 'ph_wall_stone':
        d.rectangle([0, 0, 15, 15], fill=C['stone']);
        for y in (0, 5, 10): d.line([0, y, 15, y], fill=C['stone2'])
        for x, y in ((4, 1), (11, 6), (3, 11)): d.line([x, y, x, y + 4], fill=C['stone2'])
    elif n == 'ph_rock':
        d.rectangle([0, 0, 15, 15], fill=C['rock']); d.rectangle([2, 3, 6, 7], fill=C['rock2']); d.rectangle([9, 9, 13, 13], fill=C['rock2'])
    elif n.startswith('ph_counter'):
        d.rectangle([0, 2, 15, 7], fill=C['wood']); d.rectangle([0, 8, 15, 15], fill=C['wd']); d.line([0, 2, 15, 2], fill=C['cloth'])
        if n.endswith('l'): d.line([0, 2, 0, 15], fill=C['wd'])
        if n.endswith('r'): d.line([15, 2, 15, 15], fill=C['wd'])
    elif n.startswith('ph_bench'):
        d.rectangle([0, 6, 15, 9], fill=C['wood']); d.rectangle([1, 10, 2, 14], fill=C['wd']); d.rectangle([13, 10, 14, 14], fill=C['wd'])
        if n.endswith('l'): d.rectangle([0, 6, 0, 9], fill=C['wd'])
    elif n == 'ph_gate_closed':
        d.rectangle([5, 0, 10, 15], fill=C['steel']); [d.line([x, 0, x, 15], fill=C['stone2']) for x in (6, 8, 10)]
    elif n == 'ph_gate_open':
        d.rectangle([0, 0, 3, 15], fill=C['steel']); d.rectangle([12, 0, 15, 15], fill=C['steel'])
    elif n == 'ph_startline':
        for y in range(16):
            for x in range(4, 8): d.point((x, y), fill=C['white'] if (x + y) % 2 == 0 else C['rock'])
    elif n == 'ph_formation':
        d.ellipse([2, 2, 13, 13], outline=C['cyan']); d.ellipse([6, 6, 9, 9], fill=C['cyan'])
    elif n == 'ph_regmark':
        d.ellipse([3, 3, 12, 12], outline=C['yellow']); d.line([7, 5, 7, 10], fill=C['yellow']); d.line([5, 7, 10, 7], fill=C['yellow'])
    elif n == 'ph_exit':
        for k in range(3): d.line([3 + k * 4, 4, 7 + k * 4 - 4 + 4, 8], fill=C['yellow']); 
        d.polygon([(2, 7), (9, 7), (9, 4), (14, 8), (9, 12), (9, 9), (2, 9)], fill=C['yellow'])
    elif n.startswith('ph_well'):
        r, c = int(n[-2]), int(n[-1])
        d.rectangle([0, 0, 15, 15], fill=C['stone'] if r == 1 else C['clear'])
        if r == 0: d.rectangle([0 if c == 0 else 0, 6, 15, 15], fill=C['wd']); d.rectangle([7 if c == 0 else 0, 0, 8 if c == 0 else 8, 15], fill=C['wd'])
        else: d.rectangle([0, 0, 15, 4], fill=C['stone2']); d.rectangle([2 if c == 0 else 0, 5, 15 if c == 0 else 13, 15], fill=C['blue'])
    elif n.startswith('ph_mill'):
        r, c = int(n[-2]), int(n[-1])
        d.rectangle([3 if c == 0 else 0, 0, 15 if c == 0 else 12, 15], fill=C['cloth']); d.line([8, 0, 8, 15], fill=C['wd'])
        if r == 0: d.polygon([(0, 15), (8, 0), (15, 15)], fill=C['red'])
    elif n == 'ph_sign':
        d.rectangle([7, 7, 8, 15], fill=C['wd']); d.rectangle([2, 2, 13, 8], fill=C['wood']); d.line([4, 5, 11, 5], fill=C['wd'])
    elif n == 'ph_notice':
        d.rectangle([2, 1, 13, 9], fill=C['wood']); d.rectangle([4, 3, 7, 6], fill=C['white']); d.rectangle([9, 3, 11, 7], fill=C['white']); d.rectangle([3, 10, 4, 15], fill=C['wd']); d.rectangle([11, 10, 12, 15], fill=C['wd'])
    elif n == 'ph_scout':
        d.rectangle([7, 5, 8, 15], fill=C['wd']); d.ellipse([4, 1, 11, 7], fill=C['yellow'], outline=C['wd'])
    elif n == 'ph_door_plain':
        d.rectangle([2, 0, 13, 15], fill=C['wd']); d.rectangle([4, 2, 11, 15], fill=C['wood']); d.point((10, 9), fill=C['yellow'])
    elif n.startswith('ph_log'):
        r, c = int(n[-2]), int(n[-1]); d.rectangle([0, 3, 15, 13], fill=C['wd']); d.line([0, 8, 15, 8], fill=C['wood2'])
        if c == 0: d.ellipse([0, 3, 6, 13], fill=C['wood'])
        else: d.ellipse([9, 3, 15, 13], fill=C['wood'])
    put(i, t)
img.save(os.path.join(OUT, 'tileset_placeholder.png'))
tsj = {'columns': 16, 'image': 'tileset_placeholder.png', 'imageheight': 32, 'imagewidth': 256, 'margin': 0, 'spacing': 0, 'name': 'placeholder', 'tilecount': 32, 'tilewidth': 16, 'tileheight': 16, 'type': 'tileset', 'version': '1.10', 'tiledversion': '1.10.2',
       'properties': [{'name': 'note', 'type': 'string', 'value': '佔位圖塊（幾何圖形，原創）。正式圖塊由遊美出。'}],
       'tiles': [{'id': i, 'properties': [{'name': 'name', 'type': 'string', 'value': n}, {'name': 'kind', 'type': 'string', 'value': 'placeholder'}]} for i, n in enumerate(NAMES)]}
json.dump(tsj, open(os.path.join(OUT, 'tileset_placeholder.tsj'), 'w'), ensure_ascii=False, indent=1)
json.dump({'tile_size': 16, 'columns': 16, 'names': {n: i for i, n in enumerate(NAMES)}, 'note': 'id 為 tileset 內 0 起索引（gid = firstgid + id）'}, open(os.path.join(OUT, 'tileset_placeholder_names.json'), 'w'), ensure_ascii=False, indent=1)
# 放大預覽
img.resize((img.width * 4, img.height * 4), Image.NEAREST).save(os.path.join(OUT, 'tileset_placeholder_preview_4x.png'))
print('ok', len(NAMES))
