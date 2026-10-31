#!/usr/bin/env python3
"""懸浮狀態圖示 atlas（Kurt 10-31 批：同步心情／瞌覺／需求）。全部用遊戲現有素材，唔畫新美術：
- zzz／heart／sweat／exclaim：遊美 art/atlas_props（頭頂 prop）
- need_hunger／need_mood／need_clean／need_energy：遊戲 HUD 按鈕 icon（src/ui.js ICONS feed／play／clean／sleep，10×10 像素）
輸出 pet_fx.png/json（同 PetAtlas 格式，frameSize 24）。Usage: bake_fx_atlas.py <glimmer-a dir> <pet_dir>"""
import json, sys, os, re
from PIL import Image
root, out = sys.argv[1], sys.argv[2]
S = 24; cols = 8
props = json.load(open(os.path.join(root, 'art/atlas_props.json'))); pim = Image.open(os.path.join(root, 'art/atlas_props.png')).convert('RGBA')
cells = []; clips = {}
def add(name, frames, fps, loop):
    fr = []
    for im, (px, py) in frames:
        c = Image.new('RGBA', (S, S)); ox = (S - im.width) // 2 if im.width < S else 0; oy = S - im.height - 1 if im.height < S else 0
        c.alpha_composite(im, (ox, oy)); fr.append({'i': len(cells), 'px': px + ox, 'py': py + oy}); cells.append(c)
    clips[name] = {'fps': fps, 'loop': loop, 'pivot': 'feet', 'frames': fr}
for p in ['zzz', 'heart', 'sweat', 'exclaim']:
    an = props['animations'][p]; fl = []
    for n in an['frames']:
        f = props['frames'][n]; r = f['frame']; fl.append((pim.crop((r['x'], r['y'], r['x'] + r['w'], r['y'] + r['h'])), (f['pivotPx']['x'], f['pivotPx']['y'])))
    add(p, fl, an.get('fps', 4), True)
ui = open(os.path.join(root, 'src/ui.js'), encoding='utf-8').read()
def icon(key):
    m = re.search(r"\n\s+" + key + r": \[\[(.*?)\], \{(.*?)\}\]", ui); rows = re.findall(r"'([^']*)'", m.group(1)); pal = dict(re.findall(r"(\w): '(#[0-9a-fA-F]{6})'", m.group(2)))
    im = Image.new('RGBA', (10, 10))
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch in pal: h = pal[ch]; im.putpixel((i, j), (int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16), 255))
    return im
for need, key in [('hunger', 'feed'), ('mood', 'play'), ('clean', 'clean'), ('energy', 'sleep')]:
    add('need_' + need, [(icon(key), (5, 9))], 1, True)
rows = (len(cells) + cols - 1) // cols; im = Image.new('RGBA', (cols * S, rows * S))
for k, c in enumerate(cells): im.paste(c, ((k % cols) * S, (k // cols) * S))
for c in clips.values():
    for f in c['frames']: f['x'] = (f['i'] % cols) * S; f['y'] = (f['i'] // cols) * S
im.save(os.path.join(out, 'pet_fx.png'))
json.dump({'form': 'fx', 'frameSize': S, 'facing': 'right', 'clips': clips, 'source': 'art/atlas_props（zzz／heart／sweat／exclaim）＋src/ui.js ICONS（feed／play／clean／sleep）'}, open(os.path.join(out, 'pet_fx.json'), 'w'), ensure_ascii=False, indent=1)
print('pet_fx', len(cells), 'cells', im.size, sorted(clips))
