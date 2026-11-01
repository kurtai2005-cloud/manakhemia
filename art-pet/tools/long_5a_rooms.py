# 《微光小圃》5a 擴房背景 3 間（直向，HD-2D 分層同 4b 屋仔一樣）。純 Pillow/numpy，冇 AI 生圖。
# 幾何（牆、窗洞、地板、6 擺位）同 4b 第 1 間房完全一樣 → house.json slots／家具／行走區直接重用；只換材質色同牆紙圖案。
import copy, json, math, os
import numpy as np
from PIL import Image, ImageFilter
import house_4b_room as R

THEMES = {
 "room2": dict(zh="森林閣樓", unlockLv=2, motif="leaf",
   base={'WALLP': ['#c9dfb2', '#d8eac2', '#e6f2d2'], 'DOT': ['#7fb86c', '#a8d48c'], 'CEIL': ['#b08a64', '#c49c74', '#d6b088'],
         'BEAM': ['#5e4030', '#7a5440', '#96684e'], 'WAINS': ['#7e5838', '#9a6e48', '#b4865c'], 'TRIM': ['#5e3e2c', '#7c5238', '#e0c498'],
         'SIDEW': ['#b8cc9e', '#c8daae', '#d6e6be'], 'FLOOR': ['#9a6a44', '#ae7c54', '#c08e64', '#d0a074'], 'SEAM': ['#7a5034']}),
 "room3": dict(zh="星夜書房", unlockLv=5, motif="star",
   base={'WALLP': ['#c6b8e2', '#d4c8ec', '#e2d8f4'], 'DOT': ['#f0c860', '#fff0b0'], 'CEIL': ['#8c7ca8', '#a090bc', '#b4a6cc'],
         'BEAM': ['#4e3a5e', '#664c78', '#7e6090'], 'WAINS': ['#684478', '#80588e', '#9a6ea4'], 'TRIM': ['#4c3058', '#684472', '#ecd0a4'],
         'SIDEW': ['#ae9ece', '#bcaed8', '#cabee2'], 'FLOOR': ['#6e5064', '#806074', '#927284', '#a28494'], 'SEAM': ['#58404e']}),
 "room4": dict(zh="海風小屋", unlockLv=8, motif="wave",
   base={'WALLP': ['#c4e4ec', '#d4eef2', '#e4f6f6'], 'DOT': ['#6cb8d8', '#9ad4e8'], 'CEIL': ['#c8b8a0', '#d8cab2', '#e6dac6'],
         'BEAM': ['#7a8a96', '#94a4ae', '#aebcc4'], 'WAINS': ['#94b4c6', '#acc8d6', '#c4dce6'], 'TRIM': ['#56768c', '#7290a6', '#f2f4ee'],
         'SIDEW': ['#b0d0da', '#c0dce4', '#d0e8ee'], 'FLOOR': ['#bca88e', '#cab89e', '#d8c8b0', '#e4d6c2'], 'SEAM': ['#9a8670'],
         'HILL': ['#4f9ed2', '#74bce6'], 'TREE': ['#6aae6e', '#8cc884']},
   night_sky={'HILL': ['#1c2c58', '#26386a'], 'TREE': ['#1c3040', '#26404c']}),
}

def motif(far, kind):
    """喺後牆牆紙位畫主題圖案（用 DOT 材質）；先清走 4b 原波點"""
    X, Y = far.X, far.Y; wx0, wy0, wx1, wy1 = R.G['wall']; rail = R.G['rail']
    dots = np.isin(far.m, R.IDX['DOT']); far.m[dots] = R.IDX['WALLP'][2]
    w0, w1, w2, w3 = R.G['window']
    def ok(x, y): return wx0 + 4 <= x <= wx1 - 4 and wy0 + 8 <= y <= rail - 7 and not (w0 - 6 <= x <= w2 + 6 and w1 - 6 <= y <= w3 + 8)
    def px(x, y, f):
        m = (X >= x) & (X < x + 1) & (Y >= y) & (Y < y + 1); far.put(m, 'DOT', f, 0)
    for j, yy in enumerate(range(40, rail - 6, 15)):
        for xx in range(wx0 + 7 + (7 if j % 2 else 0), wx1 - 3, 15):
            if not ok(xx, yy): continue
            if kind == "leaf":           # 細葉仔（斜兩格＋柄）
                for (dx, dy, f) in [(0, 0, .2), (1, -1, .2), (2, -1, .9), (1, 0, .9), (-1, 1, .2)]: px(xx + dx, yy + dy, f)
            elif kind == "star":         # 十字星＋閃
                for (dx, dy, f) in [(0, 0, .95), (-1, 0, .2), (1, 0, .2), (0, -1, .2), (0, 1, .2)]: px(xx + dx, yy + dy, f)
                if (xx + yy) % 3 == 0: px(xx + 4, yy - 3, .95)
            elif kind == "wave":         # 細波浪
                for (dx, dy, f) in [(-2, 0, .2), (-1, -1, .2), (0, -1, .9), (1, 0, .2), (2, 0, .2), (3, -1, .9)]: px(xx + dx, yy + dy, f)
    # 主題掛旗（天花樑下，每間唔同）：森林＝葉仔、星夜＝金星旗、海風＝藍白旗
    for seg in range(2):
        xa, xb = (wx0 + 2, 97) if seg == 0 else (98, wx1 - 2)
        for x in range(int(xa), int(xb) + 1):
            u = (x - xa) / (xb - xa); y = 32 + 7 * 4 * u * (1 - u)
            px(x, int(round(y)), .1) if False else far.put((X >= x) & (X < x + 1) & (Y >= int(round(y))) & (Y < int(round(y)) + 1), 'TRIM', .1, 0)
            if (x - int(xa)) % 8 == 4:
                yy0 = int(round(y)) + 1
                mat, f = {"leaf": ('LEAF', .55), "star": ('DOT', .4), "wave": (('WAINS', .3) if ((x // 8) % 2) else ('TRIM', .95))}[kind]
                for dy in range(5):
                    w = max(0, 2 - dy // 2)
                    m = (X >= x - w) & (X < x + w + 1) & (Y >= yy0 + dy) & (Y < yy0 + dy + 1); far.put(m, mat, f if dy else min(1, f + .4), 0)
    if kind == "star":                   # 星夜書房：牆上大月亮貼紙（右上，唔撞 wall slot 140,104 ±）
        m = ((X - 168) ** 2 + (Y - 46) ** 2 <= 30) & ~((X - 170.5) ** 2 + (Y - 44.5) ** 2 <= 24); far.put(m, 'DOT', .95, 0)

def build_room(theme, out_dir):
    T = THEMES[theme]; base0, ns0 = R.BASE, R.NIGHT_SKY
    R.BASE = {**copy.deepcopy(base0), **T["base"]}; R.NIGHT_SKY = {**copy.deepcopy(ns0), **T.get("night_sky", {})}
    meta = {}
    try:
        for var in ('day', 'night'):
            night = var == 'night'; Ls = R.build_index(night); motif(Ls['far'], T["motif"])
            pal = R.palette(night); g = dict(R.GRADE[var]); g['name'] = f"{T['zh']}・{'日間' if not night else '夜晚'}"
            d = os.path.join(out_dir, var); os.makedirs(os.path.join(d, 'raw'), exist_ok=True); used = set()
            for name, lay in Ls.items():
                rgb = np.zeros((R.LH, R.LW, 3)); a = lay.m > 0
                for i in np.unique(lay.m[a]): rgb[lay.m == i] = pal[int(i)]; used.add(int(i))
                raw = np.zeros((R.LH, R.LW, 4), np.uint8); raw[..., :3] = rgb.astype(np.uint8); raw[..., 3] = a * 255
                if name == 'sky': raw[..., 3] = 255
                Image.fromarray(raw).save(os.path.join(d, 'raw', f'{name}.png'))
                fin = raw.copy(); fin[..., :3] = R.grade_rgb(rgb, g).astype(np.uint8); im = Image.fromarray(fin)
                if name == 'fore': im = im.filter(ImageFilter.GaussianBlur(g['dof']['fore'] * .6))
                im.save(os.path.join(d, f'{name}.png'))
            lm, la, em, eb, vg = R.lights(night)
            Image.fromarray((lm * 255).astype(np.uint8)).save(os.path.join(d, 'lightmap.png'))
            Image.fromarray(la.astype(np.uint8)).save(os.path.join(d, 'light_add.png'))
            e = np.zeros((R.LH, R.LW, 4), np.uint8); e[em > 0] = (255, 255, 255, 255); Image.fromarray(e).save(os.path.join(d, 'emissive.png'))
            Image.fromarray(eb.astype(np.uint8)).save(os.path.join(d, 'emissive_blur.png'))
            Image.fromarray(vg).save(os.path.join(d, 'vignette.png'))
            json.dump(g, open(os.path.join(d, 'grade.json'), 'w'), ensure_ascii=False, indent=1)
            json.dump({str(i): R.tohex(pal[i]) for i in sorted(used)}, open(os.path.join(d, 'palette.json'), 'w'), indent=0)
            meta[var] = {'colors': len(used)}
    finally:
        R.BASE, R.NIGHT_SKY = base0, ns0
    return meta
