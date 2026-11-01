#!/usr/bin/env python3
"""systems12b：散步收集 18 件「佔位 icon」（遊美美術未有前用）。原創、程式生成（色塊圓形＋斜紋＝佔位標記）。
用法：python3 tools/gen-placeholder-collectibles.py  → art/collectibles/col_<k>_{16,32,16_sil,32_sil}.png
遊美出正式圖後直接覆蓋同名檔案，再喺 data.js 刪走 ph: true。"""
import os
from PIL import Image, ImageDraw
OUT = os.path.join(os.path.dirname(__file__), '..', 'art', 'collectibles')
ITEMS = {  # k: 主色（路線色／天氣季節色）
    'dewglass': (90, 180, 255), 'mushcap': (196, 106, 90), 'crystalchip': (143, 224, 232), 'stardust': (127, 141, 224),
    'warmstone': (255, 138, 58), 'goldleaf': (255, 211, 90), 'cloudfluff': (240, 220, 240), 'dustball': (150, 140, 130),
    'glowpowder': (180, 255, 140),
    'raindrop': (110, 160, 210), 'fogbead': (200, 205, 215), 'seedhusk': (190, 150, 90), 'sakurabud': (255, 170, 200),
    'cicadawing': (170, 220, 200), 'ginkgo': (240, 200, 60), 'icicle': (200, 235, 255), 'glowstone': (150, 255, 200),
    'dewleaf': (110, 200, 120),
}
def icon(col):
    im = Image.new('RGBA', (32, 32), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    dark = tuple(max(0, int(c * 0.55)) for c in col)
    d.ellipse([5, 5, 26, 26], fill=col + (255,), outline=dark + (255,))
    for x in range(-32, 32, 6):  # 斜紋＝佔位
        d.line([(x, 32), (x + 32, 0)], fill=dark + (70,), width=1)
    mask = Image.new('L', (32, 32), 0); ImageDraw.Draw(mask).ellipse([6, 6, 25, 25], fill=255)
    base = Image.new('RGBA', (32, 32), (0, 0, 0, 0)); ImageDraw.Draw(base).ellipse([5, 5, 26, 26], fill=col + (255,), outline=dark + (255,))
    base.paste(im, (0, 0), mask)
    ImageDraw.Draw(base).rectangle([10, 10, 12, 12], fill=(255, 255, 255, 200))
    return base
def sil(im):
    a = im.split()[3]; s = Image.new('RGBA', im.size, (60, 46, 36, 0)); s.putalpha(a.point(lambda v: 150 if v > 0 else 0)); return s
for k, col in ITEMS.items():
    i32 = icon(col); i16 = i32.resize((16, 16), Image.NEAREST)
    i32.save(os.path.join(OUT, f'col_{k}_32.png')); i16.save(os.path.join(OUT, f'col_{k}_16.png'))
    sil(i32).save(os.path.join(OUT, f'col_{k}_32_sil.png')); sil(i16).save(os.path.join(OUT, f'col_{k}_16_sil.png'))
print(len(ITEMS) * 4, 'files')
