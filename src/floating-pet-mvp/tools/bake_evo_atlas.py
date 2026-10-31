#!/usr/bin/env python3
"""evo6 懸浮 atlas（Kurt 10-31 22:50：懸浮團絨要同遊戲一樣）。

由遊戲本身用緊嘅 evo6 美術（glimmer-a/art/evo6/atlas_evo_<form>.json/png＋face_anchors_evo_<form>.json）
烤出懸浮窗用嘅 PetAtlas（assets/pet/evo/pet_evo_<form>.webp/json），每個 evoForm 一套。
唔生新圖：只係由遊戲 atlas 抽幀、重新排版；有燈芽嘅形態（data.js FORMS bulb:true）照遊戲 render.js
疊一粒 bulb_glow（借芽崽 kit，同遊戲一樣），用 neutral 心情 tint #FFEFC4 × 0.8。

clip 對應：懸浮用嘅 clip 名＝遊戲 clip 名（evo 全幀 <clip>_NN，已含預設五官）；形態冇呢個 clip → 唔寫入，
Kotlin PetAtlas.clip() 自動 fallback 同形態 idle（json fallbackIdle 列出）。光卵 tap → emo_happy（遊戲點光卵播 tap）。

用法：python3 tools/bake_evo_atlas.py [glimmer-a 路徑] [輸出 assets/pet/evo]
"""
import json, os, re, sys
from PIL import Image

SRC = sys.argv[1] if len(sys.argv) > 1 else '/workspace/live-s2/src/glimmer-a'
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), '../android/app/src/main/assets/pet/evo')
EVO = os.path.join(SRC, 'art/evo6')

# 懸浮窗 PetOverlayService 用到嘅 clip（同舊 atlas 一樣；picked_up_enter 冇 evo 全幀 → fallback picked_up）
CLIPS = ['idle', 'walk', 'turn_back', 'picked_up', 'emo_happy', 'sleep_loop', 'fall_asleep', 'wake',
         'sniff', 'swat', 'cheer_jump', 'droop', 'emo_hungry']
ALIAS = {'evo_egg': {'emo_happy': 'tap'}}      # 光卵：點一下＝tap（遊戲 behavior 光卵輕點）
GLOW_TINT, GLOW_I = (0xFF, 0xEF, 0xC4), 0.8   # data.js face.bulb.moods.neutral
COLS = 16


def forms_from_data():
    txt = open(os.path.join(SRC, 'src/data.js'), encoding='utf-8').read()
    out = {}
    for m in re.finditer(r"(evo_\w+): \{ atlas: 'atlas_(evo_\w+)', evo: true, frameSize: (\d+), pivot: \[(\d+), (\d+)\].*?bulb: (true|false) \}", txt):
        out[m.group(1)] = {'frameSize': int(m.group(3)), 'pivot': [int(m.group(4)), int(m.group(5))], 'bulb': m.group(6) == 'true'}
    return out


def glow_piece():
    j = json.load(open(os.path.join(SRC, 'art/liveliness/atlas_sprout_live.json')))
    f = j['frames']['bulb_glow']; r = f['frame']
    im = Image.open(os.path.join(SRC, 'art/liveliness', j['meta']['image'])).convert('RGBA').crop((r['x'], r['y'], r['x'] + r['w'], r['y'] + r['h']))
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            p = px[x, y]
            px[x, y] = (p[0] * GLOW_TINT[0] // 255, p[1] * GLOW_TINT[1] // 255, p[2] * GLOW_TINT[2] // 255, round(p[3] * GLOW_I))
    return im, f['pivotPx']['x'], f['pivotPx']['y']


def bake(form, F, glow):
    j = json.load(open(os.path.join(EVO, 'atlas_%s.json' % form)))
    an = j['animations']; fr = j['frames']; meta = j['meta']; S = meta['frameSize']
    sheet = Image.open(os.path.join(EVO, meta['image'])).convert('RGBA')
    fa_p = os.path.join(EVO, 'face_anchors_%s.json' % form)
    anchors = json.load(open(fa_p))['anchors'] if os.path.exists(fa_p) else {}
    cells, keyIdx, clips, fallback = [], {}, {}, []
    for name in CLIPS:
        src = ALIAS.get(form, {}).get(name, name)
        if src not in an: fallback.append(name); continue
        A = an[src]; out = []
        for k, fn in enumerate(A['frames']):
            f = fr[fn]; r = f['frame']
            cell = Image.new('RGBA', (S, S), (0, 0, 0, 0))
            cell.paste(sheet.crop((r['x'], r['y'], r['x'] + r['w'], r['y'] + r['h'])), (f['spriteSourceSize']['x'], f['spriteSourceSize']['y']))
            L = anchors.get(src) or []
            a = L[k % len(L)] if L else None
            if F['bulb'] and glow and a and a.get('bulb'):   # render.js：燈泡 glow 疊喺 anchors.bulb（＋bulb2）
                for b in ('bulb', 'bulb2'):
                    if a.get(b): cell.alpha_composite(glow[0], (a[b][0] - glow[1], a[b][1] - glow[2])) if 0 <= a[b][0] - glow[1] and a[b][0] - glow[1] + glow[0].width <= S and 0 <= a[b][1] - glow[2] and a[b][1] - glow[2] + glow[0].height <= S else None
            key = cell.tobytes()
            if key not in keyIdx: keyIdx[key] = len(cells); cells.append(cell)
            i = keyIdx[key]
            out.append({'i': i, 'x': (i % COLS) * S, 'y': (i // COLS) * S, 'px': f['pivotPx']['x'], 'py': f['pivotPx']['y']})
        clips[name] = {'fps': A['fps'], 'loop': bool(A.get('loop')), 'pivot': 'grab' if A.get('pivot') == 'grab' else 'feet', 'frames': out}
        if src != name: clips[name]['src'] = src
    rows = (len(cells) + COLS - 1) // COLS
    atlas = Image.new('RGBA', (COLS * S if len(cells) >= COLS else len(cells) * S, rows * S), (0, 0, 0, 0))
    for i, c in enumerate(cells): atlas.paste(c, ((i % COLS) * S, (i // COLS) * S))
    atlas.save(os.path.join(OUT, 'pet_%s.webp' % form), 'WEBP', lossless=True, quality=100, method=6, exact=True)
    js = {'form': form, 'name': meta.get('name'), 'frameSize': S, 'facing': 'right', 'image': 'pet_%s.webp' % form,
          'source': 'glimmer-a art/evo6/%s（遊戲 evo6 全幀 <clip>_NN）' % meta['image'] + ('＋bulb_glow neutral' if F['bulb'] else ''),
          'fallbackIdle': fallback, 'clips': clips}
    json.dump(js, open(os.path.join(OUT, 'pet_%s.json' % form), 'w'), ensure_ascii=False, separators=(',', ':'))
    return len(cells), atlas.size, fallback


def main():
    os.makedirs(OUT, exist_ok=True)
    forms = forms_from_data(); glow = glow_piece()
    assert len(forms) == 12, forms.keys()
    for form, F in sorted(forms.items()):
        n, sz, fb = bake(form, F, glow)
        print('%-18s cells=%3d atlas=%dx%d webp=%5dB fallbackIdle=%s' % (form, n, sz[0], sz[1], os.path.getsize(os.path.join(OUT, 'pet_%s.webp' % form)), fb))


if __name__ == '__main__':
    main()
