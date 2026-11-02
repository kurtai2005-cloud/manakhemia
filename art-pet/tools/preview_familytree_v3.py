#!/usr/bin/env python3
"""第 7 批族譜預覽：輸出去 $GD_FAMILYTREE_V3（預設 REPO/familytree_v3），重點 sheet 抄去 ui/familytree_v3/preview/"""
import os, sys, json, glob, shutil
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); ART = os.path.dirname(HERE); REPO = os.path.dirname(ART); OUT = f'{ART}/ui/familytree_v3'; KIT = f'{ART}/ui/kit_hd2d_v3'
GD = os.environ.get('GD_FAMILYTREE_V3', f'{REPO}/familytree_v3'); os.makedirs(GD, exist_ok=True)
sys.path.insert(0, HERE); sys.dont_write_bytecode = True
import ui_hd2d_v3_lib as L
import build_familytree_v3 as B
J = json.load(open(f'{OUT}/familytree_v3.json'))
F = lambda k, s: L.F(k, s)
BG = (14, 18, 38)
def lab(d, xy, t, sz=22, col=(250, 244, 230), k='sansb'): d.text(xy, t, font=F(k, sz), fill=col)
def checker(w, h, c=16):
    a = np.zeros((h, w, 3), np.uint8) + 40; yy, xx = np.mgrid[0:h, 0:w]; a[((yy // c + xx // c) % 2) == 0] = 58; return Image.fromarray(a).convert('RGBA')
def side(names, labels, out, title):
    ims = [Image.open(n).convert('RGB') for n in names]; w = sum(i.width for i in ims) + 20 * (len(ims) + 1); h = max(i.height for i in ims) + 100
    sh = Image.new('RGB', (w, h), BG); d = ImageDraw.Draw(sh); lab(d, (20, 10), title, 26, (255, 236, 184)); x = 20
    for im, l in zip(ims, labels): sh.paste(im, (x, 82)); lab(d, (x, 50), l, 20); x += im.width + 20
    sh.save(f'{GD}/{out}', optimize=True); return out
outs = []
# 1 before／after：5a 舊 mockup vs V3-A
outs.append(side([f'{KIT}/mockups/5a_family_tree_3x.png', f"{OUT}/{J['mockups']['ft_full']['file']}", f"{OUT}/{J['mockups']['ft_full_all']['file']}"], ['之前：UI v3 5a 家族樹', '之後：族譜 V3-A（暖色＋金框）', '6 成就全開'], '01_before_after.png', '族譜：之前／之後'))
# 2 mockups 總覽
ms = list(J['mockups'].items()); cols = 4; tw_, th_ = 293, 633; sh = Image.new('RGB', (cols * (tw_ + 16) + 16, 2 * (th_ + 56) + 70), BG); d = ImageDraw.Draw(sh); lab(d, (16, 16), '族譜 V3-A mockup（疊 UI v3，585×1266 @3x 縮半）', 24, (255, 236, 184))
for i, (k, v) in enumerate(ms):
    x = 16 + (i % cols) * (tw_ + 16); y = 70 + (i // cols) * (th_ + 56); sh.paste(Image.open(f"{OUT}/{v['file']}").convert('RGB').resize((tw_, th_), Image.LANCZOS), (x, y + 30)); lab(d, (x, y), k, 20)
sh.save(f'{GD}/02_mockups.png', optimize=True); outs.append('02_mockups.png')
# 3 零件 sheet（棋盤底睇 alpha）
P = J['parts']; groups = [('節點框（團絨圓／細佬葉 × 亮／灰／選中）＋皇冠＋蛋', [k for k in P if k.startswith('node_') or k == 'egg_unhatched']),
                          ('關係章＋兄弟圓點＋同屋 icon＋遺傳箭咀', [k for k in P if k.startswith(('stamp_', 'sib_dot', 'icon_house', 'inherit_arrow'))]),
                          ('線 4 款（tile）＋箭咀＋分叉', [k for k in P if k.startswith('line_')]), ('成就徽章 6（解鎖／未解鎖）', [k for k in P if k.startswith('ach_')]),
                          ('成就獎勵', [k for k in P if k.startswith('reward_') and k != 'reward_gold_frame'])]
W_ = 1400; rows = []
for g, ks in groups:
    ims = []
    for k in ks:
        im = Image.open(f"{OUT}/{P[k]['file']}").convert('RGBA'); s = 3 if k.startswith('line_') and 'arrow' not in k and 'joint' not in k else 1
        if k.startswith('line_') and k.endswith('_h'): t = Image.new('RGBA', (im.width * 4, im.height)); [t.alpha_composite(im, (i * im.width, 0)) for i in range(4)]; im = t
        if k.startswith('line_') and k.endswith('_v'): t = Image.new('RGBA', (im.width, im.height * 4)); [t.alpha_composite(im, (0, i * im.height)) for i in range(4)]; im = t
        if s > 1: im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
        if im.width > 400: im.thumbnail((400, 300))
        ims.append((k, im))
    rows.append((g, ims))
y = 70; layout = []
for g, ims in rows:
    x = 20; layout.append((g, None, 20, y)); y += 40; rh = 0
    for k, im in ims:
        if x + im.width > W_ - 20: x = 20; y += rh + 40; rh = 0
        layout.append((k, im, x, y)); x += max(im.width, 120) + 24; rh = max(rh, im.height)
    y += rh + 40
sh = checker(W_, y + 20); d = ImageDraw.Draw(sh); d.rectangle([0, 0, W_, 60], fill=BG); lab(d, (20, 16), '族譜零件 @3x（棋盤底＝透明；UI／光影層真 alpha，sprite 0/255）', 24, (255, 236, 184))
for k, im, x, yy in layout:
    if im is None: lab(d, (x, yy + 6), k, 22, (255, 236, 184)); continue
    sh.alpha_composite(im, (x, yy)); lab(d, (x, yy + im.height + 2), k, 18, (220, 224, 240), 'sans')
sh.convert('RGB').save(f'{GD}/03_parts.png', optimize=True); outs.append('03_parts.png')
# 4 背景 normal／warm（＋light_add）
bgs = []
for k, v in J['backgrounds'].items():
    b = Image.open(f"{OUT}/{v['file']}").convert('RGBA'); la = Image.open(f"{OUT}/{v['light']}").convert('RGBA')
    a = np.asarray(b).astype(float); l = np.asarray(la).astype(float); a[:l.shape[0], :, :3] += l[..., :3] * l[..., 3:] / 255; tmp = f'/tmp/_ftbg_{k}.png'; Image.fromarray(a.clip(0, 255).astype(np.uint8)).convert('RGB').save(tmp); bgs.append(tmp)
outs.append(side(bgs, ['bg_normal＋light_add', 'bg_warm＋light_add（三代同堂解鎖）'], '04_backgrounds.png', '族譜背景（烘焙光柱、bokeh、vignette）')); [os.remove(t) for t in bgs]
# 5 petGlow：同一節點 醒／眼瞓／瞓／退休
cells = []
for nid, st, t in (('doudou', 'awake', '豆豆 醒 ×1'), ('doudou', 'sleepy', '豆豆 眼瞓 ×.6'), ('doudou', 'sleep', '豆豆 瞓 ×0'), ('bobo', 'awake', '波波 醒 ×1'), ('bobo', 'dreaming', '波波 入夢 ×0'), ('guangguang', 'awake', '光光 退休 0')):
    n = dict(next(f for f in B.FAMILY if f['id'] == nid)); n['state'] = st; bd = Image.new('RGBA', (585, 1266), BG + (255,)); B.draw_node(bd, n); cx, cy = B.pos(nid)
    cells.append((bd.crop((int(cx - 120), int(cy - 120), int(cx + 120), int(cy + 120))), t))
sh = Image.new('RGB', (6 * 260 + 20, 360), BG); d = ImageDraw.Draw(sh); lab(d, (20, 14), 'petGlow（layout_hd2d_v3.json#petGlow）：節點 aura × state；瞓覺／入夢／退休 = 0', 22, (255, 236, 184))
for i, (im, t) in enumerate(cells): sh.paste(im.convert('RGB'), (20 + i * 260, 60)); lab(d, (20 + i * 260, 310), t, 20)
sh.save(f'{GD}/05_petglow_rule.png', optimize=True); outs.append('05_petglow_rule.png')
del L.TEXTLOG[:]
# 6 關係圖例（ft_full 局部放大＋說明）
full = Image.open(f"{OUT}/{J['mockups']['ft_full']['file']}").convert('RGB'); crop = full.crop((0, 126, 585, 1044)); sh = Image.new('RGB', (585 + 520, 918 + 80), BG); sh.paste(crop, (0, 80)); d = ImageDraw.Draw(sh)
lab(d, (20, 20), '關係：線＋章（GDD §1.2）', 26, (255, 236, 184)); y = 120
for k, v in J['relations'].items():
    im = Image.open(f"{OUT}/{J['parts'][v['line'] + '_h']['file']}").convert('RGBA'); t = Image.new('RGBA', (im.width * 3, im.height), BG + (255,)); [t.alpha_composite(im, (i * im.width, 0)) for i in range(3)]
    sh.paste(t.convert('RGB').resize((t.width * 2, t.height * 2), Image.NEAREST), (610, y)); mk = v['mark']; mkf = J['parts'].get(mk if mk.startswith('stamp') else 'sib_dot_amber')['file']
    m = Image.open(f'{OUT}/{mkf}').convert('RGBA'); bgc = Image.new('RGBA', m.size, BG + (255,)); bgc.alpha_composite(m); sh.paste(bgc.convert('RGB'), (900, y - 20)); lab(d, (610, y + 40), v['zh'], 22); y += 150
sh.save(f'{GD}/06_relations.png', optimize=True); outs.append('06_relations.png')
for o in ('01_before_after.png', '02_mockups.png', '03_parts.png', '05_petglow_rule.png'):
    os.makedirs(f'{OUT}/preview', exist_ok=True); shutil.copy(f'{GD}/{o}', f'{OUT}/preview/{o}')
print('preview', GD, outs)
