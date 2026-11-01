# 《微光小圃》HD-2D v2 UI kit 驗證 — 遊美 2026-11-02
# 用法：cd art-pet/tools && python3 validate_ui_kit_hd2d_v2.py   → 寫 ui/kit_hd2d_v2/validation.json；有 FAIL 就 exit 1
import os, sys, json, re, glob, hashlib
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import hd2d_v2_px as X
ART = X.ART; K = f'{ART}/ui/kit_hd2d_v2'; OLD = f'{ART}/ui/kit_hd2d'
res = []
def chk(name, ok, detail=''):
    res.append(dict(check=name, ok=bool(ok), detail=detail)); print(('PASS ' if ok else 'FAIL ') + name + (f' — {detail}' if detail else ''))

# 1 atlas：bounds／overlap／@2x @3x 一致／nine
REQ_UI = ['banner_top', 'panel_navy', 'panel_paper', 'panel_inset', 'card', 'card_sel', 'card_locked', 'dock_bar', 'bubble', 'divider',
          'btn_pri', 'btn_sec', 'btn_rose', 'btn_violet', 'btn_dis', 'btn_pri_p', 'btn16_pri', 'pill_pri', 'pill_violet', 'pill_navy',
          'ribbon_navy', 'chip', 'toast', 'plaque', 'subtab', 'subtab_on', 'seg_bg', 'seg_on', 'seg_locked', 'bar_trough_h6', 'bar_fill_pri_h6',
          'exp_gem_on', 'med28_pri', 'med28_pri_p', 'med24_navy', 'med13_paper', 'gem_rose_5', 'red_dot', 'red_dot_num', 'close', 'toggle_track_on', 'toggle_track_off',
          'check_on', 'star_on', 'slider_track', 'slider_knob', 'scroll_track', 'stamp_done', 'hint_arrow', 'fx_veil_tile', 'sheet_handle',
          'family_crest', 'tree_node', 'tree_node_gold', 'egg_card', 'pill_fast_on', 'pill_fast_locked', 'swatch_frame', 'job_lv_badge',
          'portrait_frame', 'portrait_mask', 'portrait_bg_normal', 'mood_badge_happy']
for at in ('ui_hd2d_v2', 'icons_hd2d_v2'):
    J1 = json.load(open(f'{K}/atlas/{at}@1x.json')); im1 = Image.open(f'{K}/atlas/{at}@1x.png'); F = J1['frames']
    oob = [n for n, f in F.items() if f['x'] < 0 or f['y'] < 0 or f['x'] + f['w'] > im1.width or f['y'] + f['h'] > im1.height]
    occ = np.zeros((im1.height, im1.width), np.int16); ov = []
    for n, f in F.items():
        s = occ[f['y']:f['y'] + f['h'], f['x']:f['x'] + f['w']]
        if (s > 0).any(): ov.append(n)
        s += 1
    chk(f'{at} bounds+overlap', not oob and not ov, f'{len(F)} frames, {im1.size}' + (f' oob={oob[:5]} ov={ov[:5]}' if oob or ov else ''))
    bad = []
    for sc in (2, 3):
        J = json.load(open(f'{K}/atlas/{at}@{sc}x.json')); im = Image.open(f'{K}/atlas/{at}@{sc}x.png')
        if im.size != (im1.width * sc, im1.height * sc) or set(J['frames']) != set(F): bad.append(f'@{sc}x size/keys'); continue
        a1 = np.array(im1.convert('RGBA')); a = np.array(im.convert('RGBA'))
        if not np.array_equal(a[::sc, ::sc], a1): bad.append(f'@{sc}x != nearest(@1x)')
        for n, f in F.items():
            g = J['frames'][n]
            if any(g[k] != f[k] * sc for k in ('x', 'y', 'w', 'h')) or ('nine' in f and g.get('nine') != [v * sc for v in f['nine']]): bad.append(f'{n}@{sc}x'); break
    chk(f'{at} @2x/@3x = nearest ×s', not bad, ', '.join(bad))
    if at == 'ui_hd2d_v2':
        nb = []; A1 = np.array(im1.convert('RGBA'))
        def per(c, ax):  # 中間區沿 ax 方向嘅最細周期（要整除中間闊度，tile 先冇接縫）
            n = c.shape[ax]
            for p_ in range(1, n + 1):
                if n % p_: continue
                if np.array_equal(np.take(c, range(0, n - p_), ax), np.take(c, range(p_, n), ax)): return p_
            return None
        for n, f in F.items():
            if 'nine' not in f: continue
            l, t, r, b = f['nine']; sl = f.get('slice', '9')
            if f.get('mode') != 'tile': nb.append(f'{n}:mode')
            fr = A1[f['y']:f['y'] + f['h'], f['x']:f['x'] + f['w']]
            if sl in ('9', '3h'):
                if l + r >= f['w']: nb.append(f'{n}:w'); continue
                c = fr[:, l:f['w'] - r]; p_ = per(c, 1)
                if p_ is None or p_ > 8: nb.append(f'{n}:x周期{p_}/{c.shape[1]}')
            if sl in ('9', '3v'):
                if t + b >= f['h']: nb.append(f'{n}:h'); continue
                c = fr[t:f['h'] - b, :]; p_ = per(c, 0)
                if p_ is None or p_ > 8: nb.append(f'{n}:y周期{p_}/{c.shape[0]}')
        chk('9-slice insets valid + 中間 tile 周期整除（≤8，無接縫）', not nb, ', '.join(nb[:8]))
        miss = [n for n in REQ_UI if n not in F]; chk('required UI frames', not miss, f'{len(REQ_UI)} required' + (f' missing={miss}' if miss else ''))
        UIF = F
    else:
        ICF = F; chk('icons ≥ 60 手點', len([n for n in F if not n.startswith('mini_')]) >= 60, f'{len(F)} icons（16px {len([n for n in F if not n.startswith("mini_")])} + mini {len([n for n in F if n.startswith("mini_")])}）')

# 2 alpha 0/255（mockups 例外：全不透明）
bad = []; npng = 0
for p in glob.glob(f'{K}/**/*.png', recursive=True):
    a = np.array(Image.open(p).convert('RGBA'))[..., 3]; npng += 1
    if '/mockups/' in p or p.endswith('text_sheet_3x.png') or p.endswith('portrait_cases_3x.png'):
        if a.min() != 255: bad.append(os.path.relpath(p, K) + ':not opaque')
    elif not np.isin(a, (0, 255)).all(): bad.append(os.path.relpath(p, K))
chk('alpha 0/255（sprite／atlas／icon／font）', not bad, f'{npng} png' + (f' bad={bad[:5]}' if bad else ''))

# 3 icons 獨立檔
miss = [n for n in ICF if not (os.path.exists(f'{K}/icons/{"" if n.startswith("mini_") else "ic_"}{n}@1x.png') and os.path.exists(f'{K}/icons/{"" if n.startswith("mini_") else "ic_"}{n}@3x.png'))]
chk('icons/ 每個 icon 有 @1x @3x', not miss, ', '.join(miss[:6]))

# 4 字體：OFL、glyph 範圍、mockup 原始碼字元覆蓋
FJ = json.load(open(f'{K}/fonts/fonts_v2.json'))['fonts']; fb = []
for k, f in FJ.items():
    im = Image.open(f'{K}/fonts/{f["image"]}'); 
    if not os.path.exists(f'{K}/fonts/{f["ttf"]}'): fb.append(f'{k}:ttf')
    for ch, g in f['glyphs'].items():
        if g['w'] and (g['x'] + g['w'] > im.width or g['y'] + g['h'] > im.height): fb.append(f'{k}:{ch}'); break
chk('font atlas glyph bounds + TTF', not fb, ', '.join(fb) or ', '.join(f'{k} {len(f["glyphs"])} 字 lineH {f["lineH"]}' for k, f in FJ.items()))
ofl = open(f'{K}/fonts/OFL_fusion-pixel.txt', encoding='utf-8').read()
chk('OFL licence 喺 fonts/', 'SIL OPEN FONT LICENSE' in ofl.upper(), 'OFL_fusion-pixel.txt')
src = ''
for p in ('build_ui_hd2d_v2_mockups.py', 'build_ui_hd2d_v2_textsheet.py'):
    s = open(f'{HERE}/{p}', encoding='utf-8').read()
    s = re.sub(r"'note':\s*'[^'\n]*'", '', s); s = re.sub(r'#.*', '', s)
    src += ''.join(re.findall(r"'([^'\n]*)'", s))
need = {c for c in src if ord(c) > 0x2000 and not c.isspace()}
G = set(FJ['fp8']['glyphs']) & set(FJ['fp10']['glyphs']) & set(FJ['fp12']['glyphs'])
mm = sorted(need - G); chk('mockup 字串 CJK 全部有 glyph（8/10/12）', not mm, f'{len(need)} 字' + (f' missing={"".join(mm[:20])}' if mm else ''))

# 5 layout
L = json.load(open(f'{K}/layout_hd2d_v2.json')); b = L['bands']; W, H = L['art']
ok = b['top'][0] == 0 and b['top'][1] == b['garden'][0] and b['garden'][1] == b['bottom'][0] and b['bottom'][1] == H == 422
gfrac = (b['garden'][1] - b['garden'][0]) / H
chk('layout bands 0→422 連續 + 花園 > 50%', ok and gfrac > .5, f'top {b["top"]} garden {b["garden"]}（{gfrac:.0%}） bottom {b["bottom"]}')
oob = []
def walk(o, path=''):
    if isinstance(o, dict):
        if all(k in o for k in ('x', 'y', 'w', 'h')) and all(isinstance(o[k], (int, float)) for k in ('x', 'y', 'w', 'h')):
            if o['x'] < -8 or o['y'] < -8 or o['x'] + o['w'] > W + 8 or o['y'] + o['h'] > H + 8: oob.append(path)
        for k, v in o.items(): walk(v, f'{path}.{k}')
    elif isinstance(o, list):
        for i, v in enumerate(o): walk(v, f'{path}[{i}]')
walk(L); chk('layout rect 喺畫面內（容許出血 8）', not oob, ', '.join(oob[:6]))

# 6 portrait_rects
R = json.load(open(f'{K}/portrait/portrait_rects.json')); P_ = R['params']; forms = R['forms']
exp = set(X.ANCH) | set(X.S2T); missf = sorted(exp - set(forms))
chk('portrait_rects 覆蓋全部 form', not missf and len(forms) == len(exp), f'{len(forms)} forms（old {sum(f["line"] == "old" for f in forms.values())} / from_ref 48 {sum(f["line"] == "from_ref" for f in forms.values())} / series2 {sum(f["line"] == "series2" for f in forms.values())}）' + (f' missing={missf}' if missf else ''))
ba = [a for a, t in R['aliases'].items() if t not in forms]; chk('aliases 指向存在 form', not ba, f'{len(R["aliases"])} aliases' + (f' bad={ba}' if ba else ''))
pb = []; badge_keys = set(); nacc = 0; nbadge = 0; hidden = 0
for fn, f in forms.items():
    x0, y0, n = f['rect']
    if n != P_['n'] or x0 < 0 or y0 < 0 or x0 + n > f['frame'] + 2 * R['pad'] or y0 + n > f['frame'] + 2 * R['pad']: pb.append(f'{fn}:rect')
    for it, a in f['acc'].items():
        nacc += 1
        if a.get('hidden'): hidden += 1; continue
        if a['shift'] > P_['maxShift'] or a['pop'] > P_['maxPop'] or a['shift'] < 0 or a['pop'] < 0: pb.append(f'{fn}.{it}')
        if a['badge']: nbadge += 1; badge_keys.add(it)
chk('portrait rect 喺 canvas 內 + shift ≤ 4 + pop ≤ 3', not pb, f'{nacc} acc entries, badge {nbadge}, hidden {hidden}' + (f' bad={pb[:6]}' if pb else ''))
mk = sorted(k for k in badge_keys if f'acc_thumb_{k}' not in UIF); chk('每個 badge 飾品有 acc_thumb_<key>', not mk, ', '.join(mk))

# 7 mockups 尺寸
SC = ['home', 'popup', 'levelup', 'settings', 'journal_dex', 'house_4b', 'house_4b_decorate', '5a_family_tree', '5a_egg_choice', '5a_pet_card', '5b_daily_plan', '5b_job_picker', '5c_parent_pick', '5c_inherit_result']
mb = []
for n in SC:
    for suf, sz in (('_3x', (585, 1266)), ('_smallphone_360w', (360, 779))):
        p = f'{K}/mockups/{n}{suf}.png'
        if not os.path.exists(p) or Image.open(p).size != sz: mb.append(n + suf)
chk('mockups 585×1266 + smallphone 360×779（14 畫面）', not mb, ', '.join(mb))
# smallphone：細字 8px @360w ≈ 1.85 device px／art px → 最細字高 ≈ 14.8 device px
chk('smallphone 360w 比例 = 360/195', abs(360 / 195 - 779 / 422) < .01, f'×{360 / 195:.3f}；8px 字 ≈ {8 * 360 / 195:.1f}px 高')

# 8 docs 反引號路徑存在
db = []
for d in ('UI_KIT_V2.md', 'PORTRAIT_SYNC.md'):
    p = f'{K}/{d}'
    if not os.path.exists(p): db.append(d + ':missing'); continue
    for ref in re.findall(r'`([^`\s]+\.(?:png|json|py|txt|ttf|md))`', open(p, encoding='utf-8').read()):
        if '<' in ref or '*' in ref or '{' in ref: continue
        cands = [f'{K}/{ref}', f'{ART}/{ref}', f'{HERE}/{ref}', f'{ART}/../{ref}']
        if not any(os.path.exists(c) for c in cands) and not glob.glob(f'{K}/**/{os.path.basename(ref)}', recursive=True): db.append(f'{d}:{ref}')
chk('docs 存在 + 反引號引用檔案存在', not db, ', '.join(db[:8]))

# 9 衞生
bk = [p for p in glob.glob(f'{K}/**/*', recursive=True) if '_backup' in p or p.endswith('~') or p.endswith('.bak')]
chk('冇 _backups／暫存檔', not bk, ', '.join(bk[:5]))
v2start = min(os.path.getmtime(f'{HERE}/{p}') for p in ('ui_hd2d_v2_kit.py', 'build_ui_hd2d_v2_mockups.py'))
oldf = [p for p in glob.glob(f'{OLD}/**/*', recursive=True) if os.path.isfile(p)]
newer = [os.path.relpath(p, OLD) for p in oldf if os.path.getmtime(p) >= 1793548800]  # 2026-11-02 00:00 HKT
chk('kit_hd2d（v1）冇改到', not newer, f'{len(oldf)} 檔，最新 mtime 早過 2026-11-02' if not newer else ', '.join(newer[:5]))

ok = all(r['ok'] for r in res)
json.dump(dict(kit='kit_hd2d_v2', date='2026-11-02', pass_=ok, passed=sum(r['ok'] for r in res), total=len(res), checks=res), open(f'{K}/validation.json', 'w'), ensure_ascii=False, indent=1)
print(f'\n{"ALL PASS" if ok else "FAIL"} {sum(r["ok"] for r in res)}/{len(res)}'); sys.exit(0 if ok else 1)
