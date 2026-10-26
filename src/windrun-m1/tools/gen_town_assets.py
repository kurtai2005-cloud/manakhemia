#!/usr/bin/env python3
"""程序生成《風野競走》城鎮圖塊集／道具／角色（原創；色盤取自 art/palette/env_palettes.json 苔坡色盤）。
輸出：art/town/town_tiles.png（16 欄、16px）、town_tiles.names.txt、props/*.png、char_*.png（64×96：行 d/l/r/u × 4 幀 16×24）。"""
import random, os, sys
from PIL import Image, ImageDraw
OUT = os.path.join(os.path.dirname(__file__), '..', 'art', 'town')
os.makedirs(OUT + '/props', exist_ok=True)
H = lambda s: tuple(int(s[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
INK, PLUM = H('#2B2540'), H('#4A4066')
MD, MB, MM, ML, MH = H('#244F3A'), H('#3E8250'), H('#5AA85E'), H('#8CD27A'), H('#B9EE9A')
SD, SO, PB, PL, PH = H('#5E3F3A'), H('#8A5A44'), H('#B98258'), H('#D9B98C'), H('#F0D6A8')
STD, ST, STL = H('#6B7288'), H('#9AA3B8'), H('#C8D2EE')
TD, TM, TH = H('#1F3F45'), H('#2F5F5C'), H('#477F76')
WARM, CORE, ORG = H('#FFC87A'), H('#FFFBD0'), H('#D9692F')
BLUE1, BLUE2, BLUE3 = H('#2A5E9A'), H('#4FA3D9'), H('#A6DAF2')
ROSE, ROSE2 = H('#D9667A'), H('#F28B9B')
CY, CY2 = H('#4FD0C8'), H('#A8F5E8')
SAND, SAND2 = H('#F0D6A8'), H('#D9B98C')
T0 = (0, 0, 0, 0)

def noise_tile(base, cols, p, seed):
    r = random.Random(seed); im = Image.new('RGBA', (16, 16), base); px = im.load()
    for y in range(16):
        for x in range(16):
            if r.random() < p: px[x, y] = r.choice(cols)
    return im
def new(): return Image.new('RGBA', (16, 16), T0)

tiles = {}
tiles['grass_a'] = noise_tile(MM, [MB, ML, MB], 0.18, 1)
tiles['grass_b'] = noise_tile(MM, [ML, MB, MH], 0.22, 2)
tiles['grass_c'] = noise_tile(MB, [MM, MD, MM], 0.2, 3)
tiles['grass_dark'] = noise_tile(MB, [MD, MM, MD], 0.28, 4)
tiles['dirt'] = noise_tile(PB, [PL, SO, PB], 0.2, 5)
tiles['dirt_v'] = noise_tile(PB, [PL, SO, PH], 0.2, 6)
def cobble():
    im = Image.new('RGBA', (16, 16), ST); d = ImageDraw.Draw(im)
    for (x, y, w, h) in [(0, 0, 7, 5), (8, 0, 8, 5), (0, 6, 5, 4), (6, 6, 6, 4), (13, 6, 3, 4), (0, 11, 8, 5), (9, 11, 7, 5)]:
        d.rectangle([x, y, x + w - 1, y + h - 1], fill=STL if (x + y) % 3 == 0 else ST, outline=STD)
    return im
tiles['cobble'] = cobble()
def plaza():
    im = Image.new('RGBA', (16, 16), STL); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 15, 15], outline=ST); d.rectangle([4, 4, 11, 11], outline=ST); d.point([(7, 7), (8, 8)], fill=PL)
    return im
tiles['plaza'] = plaza()
def water(f):
    im = Image.new('RGBA', (16, 16), BLUE2); d = ImageDraw.Draw(im)
    for (x, y) in ([(2, 3), (3, 3), (4, 3), (9, 10), (10, 10), (11, 10)] if f == 0 else [(4, 4), (5, 4), (6, 4), (11, 11), (12, 11), (13, 11)]):
        d.point((x, y), fill=BLUE3)
    for (x, y) in [(1, 12), (2, 12), (10, 2), (11, 2)]: d.point((x + f * 2, y), fill=BLUE1)
    return im
tiles['water'] = water(0); tiles['water_b'] = water(1)
def wall_top():
    im = Image.new('RGBA', (16, 16), STD); d = ImageDraw.Draw(im); d.rectangle([0, 0, 15, 3], fill=ST); d.line([0, 4, 15, 4], fill=INK)
    for x in range(0, 16, 5): d.line([x, 0, x, 3], fill=STD)
    d.rectangle([0, 5, 15, 15], fill=STD); return im
tiles['wall_top'] = wall_top()
def wall_face():
    im = Image.new('RGBA', (16, 16), STD); d = ImageDraw.Draw(im)
    for y in range(0, 16, 4):
        d.line([0, y, 15, y], fill=INK)
        off = 0 if (y // 4) % 2 == 0 else 4
        for x in range(off, 16, 8): d.line([x, y, x, y + 3], fill=INK)
    d.line([0, 15, 15, 15], fill=PLUM); return im
tiles['wall_face'] = wall_face()
tiles['hedge'] = noise_tile(TM, [TD, TH, TD, MB], 0.4, 7)
tiles['hedge_over'] = noise_tile(TM, [TD, TH, MD], 0.35, 8)
def wood():
    im = Image.new('RGBA', (16, 16), PB); d = ImageDraw.Draw(im)
    for y in (0, 5, 10): d.line([0, y, 15, y], fill=SO)
    d.line([0, 15, 15, 15], fill=SD)
    for (x, y) in [(3, 2), (11, 7), (6, 12)]: d.point((x, y), fill=PL)
    return im
tiles['wood'] = wood()
tiles['sand'] = noise_tile(SAND, [SAND2, SAND, PH], 0.18, 9)
def shadow():
    im = new(); d = ImageDraw.Draw(im); d.ellipse([2, 5, 13, 12], fill=(30, 20, 50, 90)); return im
tiles['shadow'] = shadow()
def dots(cols, pts):
    im = new(); d = ImageDraw.Draw(im)
    for (x, y), c in zip(pts, cols * 4): d.point((x, y), fill=c); d.point((x + 1, y), fill=c) if c != CORE else None
    return im
def flowers(c1):
    im = new(); d = ImageDraw.Draw(im)
    for (x, y) in [(3, 4), (10, 3), (7, 10), (12, 12)]:
        d.point((x, y + 1), fill=MB); d.point((x, y + 2), fill=MD); d.rectangle([x - 1, y - 1, x + 1, y], fill=c1); d.point((x, y - 1), fill=CORE)
    return im
tiles['flowers_red'] = flowers(ROSE); tiles['flowers_blue'] = flowers(BLUE3)
def pebbles():
    im = new(); d = ImageDraw.Draw(im)
    for (x, y) in [(3, 9), (9, 5), (12, 11)]: d.rectangle([x, y, x + 1, y + 1], fill=ST); d.point((x, y), fill=STL)
    return im
tiles['pebbles'] = pebbles()
def tuft():
    im = new(); d = ImageDraw.Draw(im)
    for (x, y, h) in [(4, 13, 4), (6, 13, 6), (8, 13, 5), (10, 13, 3)]: d.line([x, y, x - 1 if h > 4 else x + 1, y - h], fill=ML if h > 4 else MH)
    return im
tiles['tuft'] = tuft()
def sign():
    im = new(); d = ImageDraw.Draw(im); d.rectangle([7, 8, 8, 15], fill=SO); d.rectangle([2, 2, 13, 9], fill=PB, outline=INK); d.line([4, 5, 11, 5], fill=SD); d.line([4, 7, 9, 7], fill=SD); return im
tiles['sign'] = sign()
def crate():
    im = new(); d = ImageDraw.Draw(im); d.rectangle([2, 4, 13, 15], fill=PB, outline=INK); d.line([2, 4, 13, 15], fill=SO); d.line([13, 4, 2, 15], fill=SO); return im
tiles['crate'] = crate()
def barrel():
    im = new(); d = ImageDraw.Draw(im); d.ellipse([3, 3, 12, 15], fill=SO, outline=INK); d.line([3, 6, 12, 6], fill=SD); d.line([3, 11, 12, 11], fill=SD); d.line([6, 4, 6, 14], fill=PB); return im
tiles['barrel'] = barrel()
def fence_h():
    im = new(); d = ImageDraw.Draw(im)
    for x in (1, 7, 13): d.rectangle([x, 4, x + 1, 15], fill=PB, outline=INK)
    d.rectangle([0, 7, 15, 8], fill=PL, outline=INK); d.rectangle([0, 11, 15, 12], fill=PL, outline=INK); return im
tiles['fence_h'] = fence_h()
def fence_v():
    im = new(); d = ImageDraw.Draw(im); d.rectangle([6, 0, 9, 15], fill=PB, outline=INK); d.line([7, 0, 7, 15], fill=PL); return im
tiles['fence_v'] = fence_v()
def bush():
    im = new(); d = ImageDraw.Draw(im); d.ellipse([1, 4, 14, 15], fill=TM, outline=TD)
    for (x, y) in [(4, 7), (8, 6), (10, 10), (5, 11)]: d.point((x, y), fill=TH)
    d.point((7, 9), fill=ROSE); return im
tiles['bush'] = bush()
def mush():
    im = new(); d = ImageDraw.Draw(im); d.rectangle([7, 9, 8, 13], fill=SAND); d.ellipse([4, 5, 11, 10], fill=ROSE, outline=INK); d.point((6, 7), fill=CORE); d.point((9, 8), fill=CORE); return im
tiles['mushroom'] = mush()
def stump():
    im = new(); d = ImageDraw.Draw(im); d.rectangle([3, 8, 12, 14], fill=SO, outline=INK); d.ellipse([3, 5, 12, 10], fill=PB, outline=INK); d.arc([5, 6, 10, 9], 0, 360, fill=SO); return im
tiles['stump'] = stump()
def lantern():
    im = new(); d = ImageDraw.Draw(im); d.rectangle([7, 6, 8, 15], fill=INK); d.rectangle([4, 1, 11, 8], fill=INK); d.rectangle([5, 2, 10, 7], fill=WARM); d.rectangle([6, 3, 9, 5], fill=CORE); return im
tiles['lantern_g'] = lantern()
def rock():
    im = new(); d = ImageDraw.Draw(im); d.polygon([(2, 14), (4, 6), (9, 4), (14, 9), (14, 14)], fill=ST, outline=INK); d.line([5, 7, 9, 5], fill=STL); d.point((10, 8), fill=STL); return im
tiles['rock'] = rock()
def bench():
    im = new(); d = ImageDraw.Draw(im); d.rectangle([1, 6, 14, 8], fill=PB, outline=INK); d.rectangle([2, 9, 3, 14], fill=SO); d.rectangle([12, 9, 13, 14], fill=SO); d.rectangle([1, 2, 14, 4], fill=PL, outline=INK); return im
tiles['bench'] = bench()
def puddle():
    im = new(); d = ImageDraw.Draw(im); d.ellipse([2, 6, 13, 12], fill=BLUE2, outline=BLUE1); d.point((5, 8), fill=BLUE3); d.point((6, 8), fill=BLUE3); return im
tiles['puddle'] = puddle()
def arch(part):
    im = new(); d = ImageDraw.Draw(im)
    if part == 'l': d.rectangle([4, 0, 15, 15], fill=ST, outline=INK); d.rectangle([4, 0, 15, 3], fill=STL); d.rectangle([6, 4, 9, 15], fill=STD)
    elif part == 'r': d.rectangle([0, 0, 11, 15], fill=ST, outline=INK); d.rectangle([0, 0, 11, 3], fill=STL); d.rectangle([6, 4, 9, 15], fill=STD)
    else:
        d.rectangle([0, 0, 15, 7], fill=ST, outline=INK); d.rectangle([0, 0, 15, 2], fill=STL)
        for x in range(0, 16, 4): d.line([x, 3, x, 7], fill=STD)
        d.point((7, 8), fill=WARM); d.point((8, 8), fill=WARM)
    return im
tiles['arch_l'] = arch('l'); tiles['arch_m'] = arch('m'); tiles['arch_r'] = arch('r')
def vine():
    im = new(); d = ImageDraw.Draw(im); d.line([3, 0, 3, 12], fill=ML); d.line([9, 0, 9, 15], fill=MB); d.line([13, 0, 13, 8], fill=ML); return im
tiles['vine'] = vine()
def banner():
    im = new(); d = ImageDraw.Draw(im); d.rectangle([7, 0, 8, 2], fill=INK); d.polygon([(4, 2), (11, 2), (11, 12), (7, 9), (4, 12)], fill=ROSE, outline=INK); d.rectangle([6, 4, 9, 5], fill=CORE); return im
tiles['banner'] = banner()
def portal(f):
    im = new(); d = ImageDraw.Draw(im); c = CY if f == 0 else CY2
    for r in ([7, 4] if f == 0 else [6, 3]): d.ellipse([8 - r, 8 - r, 7 + r, 7 + r], outline=c)
    d.point((7, 7), fill=CORE); d.point((8, 8), fill=CORE); return im
tiles['portal_a'] = portal(0); tiles['portal_b'] = portal(1)

NAMES = ['grass_a', 'grass_b', 'grass_c', 'dirt', 'cobble', 'plaza', 'water', 'water_b', 'wall_top', 'wall_face', 'hedge', 'wood', 'sand', 'grass_dark', 'dirt_v', 'shadow',
         'flowers_red', 'flowers_blue', 'pebbles', 'tuft', 'sign', 'crate', 'barrel', 'fence_h', 'fence_v', 'bush', 'mushroom', 'stump', 'lantern_g', 'rock', 'bench', 'puddle',
         'arch_l', 'arch_m', 'arch_r', 'hedge_over', 'vine', 'banner', 'portal_a', 'portal_b']
assert len(NAMES) == 40 and set(NAMES) == set(tiles), set(NAMES) ^ set(tiles)
sheet = Image.new('RGBA', (256, 48), T0)
for i, n in enumerate(NAMES): sheet.paste(tiles[n], ((i % 16) * 16, (i // 16) * 16))
sheet.save(OUT + '/town_tiles.png')
open(OUT + '/town_tiles.names.txt', 'w').write('\n'.join('%d %s' % (i + 1, n) for i, n in enumerate(NAMES)) + '\n')

# ---------- 道具 ----------
def tree(w, h, seed, tall):
    im = Image.new('RGBA', (w, h), T0); d = ImageDraw.Draw(im); r = random.Random(seed)
    d.rectangle([w // 2 - 3, h - 14, w // 2 + 2, h - 1], fill=INK); d.rectangle([w // 2 - 2, h - 13, w // 2 + 1, h - 2], fill=SO)
    cy = h - (26 if tall else 22)
    for (cx, cyy, rr, col) in [(w // 2, cy - 4, 13, TD), (w // 2 - 6, cy + 2, 9, TM), (w // 2 + 7, cy + 1, 9, TM), (w // 2, cy - 1, 10, TM)]:
        d.ellipse([cx - rr, cyy - rr + 6, cx + rr, cyy + rr + 6], fill=col)
    for _ in range(26):
        x = r.randint(4, w - 5); y = r.randint(2, cy + 10)
        if im.getpixel((x, y))[3]: d.point((x, y), fill=TH)
    d.point((w // 2 - 5, cy - 5), fill=MH); d.point((w // 2 + 4, cy - 2), fill=MH)
    return im
tree('', 0, 0, 0) if False else None
tree(32, 48, 11, True).save(OUT + '/props/tree_a.png'); tree(32, 40, 12, False).save(OUT + '/props/tree_b.png')
def house(w, h, wall, roof, roof_hi, win_x, door_x, name, extra=None):
    im = Image.new('RGBA', (w, h), T0); d = ImageDraw.Draw(im)
    top = 0; roof_h = int(h * 0.42); wall_top = roof_h - 2
    d.polygon([(w // 2, top), (w - 1, roof_h), (0, roof_h)], fill=roof, outline=INK)
    mask = Image.new('L', (w, h), 0); ImageDraw.Draw(mask).polygon([(w // 2, top + 1), (w - 2, roof_h - 1), (1, roof_h - 1)], fill=255)
    st = Image.new('RGBA', (w, h), T0); sd = ImageDraw.Draw(st)
    for y in range(top + 6, roof_h, 5): sd.line([0, y, w, y], fill=roof_hi)
    im.paste(st, (0, 0), Image.composite(mask, Image.new('L', (w, h), 0), mask))
    d.rectangle([2, wall_top, w - 3, h - 1], fill=wall, outline=INK)
    d.rectangle([3, h - 4, w - 4, h - 2], fill=PL)
    d.line([2, wall_top + 1, w - 3, wall_top + 1], fill=SD)
    for x in win_x: d.rectangle([x, h - 26 if h > 66 else h - 24, x + 4, h - 17 if h > 66 else h - 15], fill=CORE, outline=INK); d.line([x + 2, h - 26 if h > 66 else h - 24, x + 2, h - 17 if h > 66 else h - 15], fill=INK)
    d.rectangle([door_x, h - 14, door_x + 8, h - 1], fill=SO, outline=INK); d.point((door_x + 6, h - 7), fill=WARM)
    if extra: extra(d, w, h)
    im.save(OUT + '/props/%s.png' % name)
house(80, 72, PL, H('#6A5BAA'), H('#A99BE0'), [12, 63], 35, 'house_a')
house(64, 64, PH, H('#D9692F'), H('#F2A65A'), [10, 49], 27, 'house_b')
def hall_extra(d, w, h): d.rectangle([40, h - 40 + 6, 55, h - 32], fill=ROSE, outline=INK); d.rectangle([44, h - 38, 51, h - 36], fill=CORE)
house(96, 80, STL, H('#D9692F'), H('#F2A65A'), [14, 77], 43, 'hall', hall_extra)
def lamp():
    im = Image.new('RGBA', (16, 32), T0); d = ImageDraw.Draw(im)
    d.rectangle([7, 8, 8, 31], fill=INK); d.rectangle([4, 1, 11, 9], fill=INK); d.rectangle([5, 2, 10, 8], fill=WARM); d.rectangle([6, 3, 9, 6], fill=CORE); d.rectangle([5, 29, 10, 31], fill=INK)
    im.save(OUT + '/props/lamp.png')
lamp()
def well():
    im = Image.new('RGBA', (32, 32), T0); d = ImageDraw.Draw(im)
    d.rectangle([4, 3, 5, 18], fill=INK); d.rectangle([26, 3, 27, 18], fill=INK); d.rectangle([2, 1, 29, 4], fill=SO, outline=INK)
    d.ellipse([3, 15, 28, 31], fill=ST, outline=INK); d.ellipse([6, 17, 25, 28], fill=BLUE1); d.ellipse([8, 19, 23, 26], fill=BLUE2); d.line([15, 4, 15, 14], fill=PB)
    im.save(OUT + '/props/well.png')
well()

# ---------- 角色 64×96：行 d,l,r,u × 4 幀（16×24）----------
def char(name, hair, shirt, pants, skin=H('#F0C8A0'), hat=None):
    im = Image.new('RGBA', (64, 96), T0)
    for row, dr in enumerate('dlru'):
        for f in range(4):
            fr = Image.new('RGBA', (16, 24), T0); d = ImageDraw.Draw(fr)
            bob = 1 if f in (1, 3) else 0
            leg = [0, 1, 0, -1][f]
            d.ellipse([3, 20, 12, 23], fill=(30, 20, 50, 80))                          # 腳影
            lx, rx = (5, 9)
            d.rectangle([lx, 16 + (leg if dr in 'du' else 0) * 0, lx + 2, 21 - (1 if leg == 1 else 0)], fill=pants); d.rectangle([rx, 16, rx + 2, 21 - (1 if leg == -1 else 0)], fill=pants)
            if dr in 'lr':
                d.rectangle([5, 16, 10, 21 - (1 if leg else 0)], fill=pants)
            d.rectangle([4, 9 - bob, 11, 16 - bob], fill=shirt, outline=INK)            # 身
            d.rectangle([4, 1 - bob, 11, 9 - bob], fill=skin, outline=INK)               # 頭
            d.rectangle([4, 0 - bob, 11, 3 - bob], fill=hair)
            if dr == 'd': d.point((6, 5 - bob), fill=INK); d.point((9, 5 - bob), fill=INK)
            elif dr == 'l': d.point((5, 5 - bob), fill=INK); d.rectangle([9, 2 - bob, 11, 8 - bob], fill=hair)
            elif dr == 'r': d.point((10, 5 - bob), fill=INK); d.rectangle([4, 2 - bob, 6, 8 - bob], fill=hair)
            else: d.rectangle([4, 0 - bob, 11, 7 - bob], fill=hair)
            if hat: d.rectangle([3, -1 - bob + 1, 12, 1 - bob + 1], fill=hat)
            im.paste(fr, (f * 16, row * 24), fr)
    im.save(OUT + '/char_%s.png' % name)
char('player', H('#5E3F3A'), H('#4FA3D9'), H('#2A5E9A'))
char('elder', H('#C8D2EE'), H('#6A5BAA'), H('#4A4066'))
char('fern', H('#2F6B45'), ROSE, H('#5E3F3A'))
char('clerk', H('#2B2540'), H('#F2A65A'), H('#6B7288'), hat=H('#D9692F'))
print('done ->', OUT, 'tiles', len(NAMES))
