#!/usr/bin/env python3
"""validate_ui_kit_hd2d_v3.py — 《微光小圃》UI kit v3（V3-A HD-2D）驗收。只用 Pillow／numpy。
用法：python3 art-pet/tools/validate_ui_kit_hd2d_v3.py   → 寫 kit_hd2d_v3/validation.json；有 FAIL 就 exit 1"""
import os, sys, json, glob
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(f'{HERE}/../..'); ART = f'{ROOT}/art-pet'
KIT = f'{ART}/ui/kit_hd2d_v3'; V2 = f'{ART}/ui/kit_hd2d_v2'
W, H = 585, 1266; MIN_PX = 18; MIN_CR = 4.5
SCREENS = ['home', 'popup', 'levelup', 'settings', 'journal_dex', 'house_4b', 'house_4b_decorate', '5a_family_tree', '5a_egg_choice', '5a_pet_card', '5b_daily_plan', '5b_job_picker', '5c_parent_pick', '5c_inherit_result', '6b_walk', '6c_dream', '6d_share']
EXTRA_ICONS = {'walk', 'dream', 'dreambook', 'friend', 'share', 'copy', 'paste', 'photo', 'qr', 'egg_code', 'friend_badge'}
RES = []
def chk(name, ok, detail=''): RES.append(dict(check=name, ok=bool(ok), detail=detail)); return ok
J = lambda p: json.load(open(p, encoding='utf-8'))
def run():
    # 1 檔案
    need = ['atlas/ui_hd2d_v3@3x.png', 'atlas/ui_hd2d_v3@3x.json', 'atlas/ui_hd2d_v3@2x.png', 'atlas/ui_hd2d_v3@2x.json', 'atlas/icons_hd2d_v3@3x.png', 'atlas/icons_hd2d_v3@3x.json', 'atlas/icons_hd2d_v3@6x.png', 'atlas/icons_hd2d_v3@6x.json',
            'atlas/icons_glow_hd2d_v3@3x.png', 'atlas/icons_glow_hd2d_v3@3x.json', 'atlas/v2_to_v3_map.json', 'layout_hd2d_v3.json', 'UI_KIT_V3.md', 'portrait/portrait_rects.json', 'portrait/PORTRAIT_SYNC.md',
            'fonts/charset_v3.txt', 'fonts/fonts_v3.json', 'fonts/OFL_noto-cjk.txt', 'mockups/overview.png', 'mockups/texts.json', 'mockups/icons_v2_v3_compare.png'] + [f'mockups/{s}_3x.png' for s in SCREENS]
    miss = [p for p in need if not os.path.exists(f'{KIT}/{p}')]
    chk('files_exist', not miss, f'{len(need) - len(miss)}/{len(need)}' + (f' missing {miss}' if miss else ''))
    if miss: return
    chk('v2_kit_untouched', os.path.exists(f'{V2}/layout_hd2d_v2.json') and os.path.exists(f'{V2}/atlas'), 'kit_hd2d_v2 保留')
    # 2 atlas
    for nm in ('ui_hd2d_v3@3x', 'ui_hd2d_v3@2x', 'icons_hd2d_v3@3x', 'icons_hd2d_v3@6x', 'icons_glow_hd2d_v3@3x'):
        a = J(f'{KIT}/atlas/{nm}.json'); im = Image.open(f'{KIT}/atlas/{nm}.png'); bad = []; boxes = []
        for k, f in a['frames'].items():
            if f['x'] < 0 or f['y'] < 0 or f['x'] + f['w'] > im.width or f['y'] + f['h'] > im.height: bad.append(k)
            boxes.append((f['x'], f['y'], f['x'] + f['w'], f['y'] + f['h'], k))
        boxes.sort(); ov = []
        for i, b in enumerate(boxes):
            for c in boxes[i + 1:]:
                if c[0] >= b[2]: break
                if c[1] < b[3] and b[1] < c[3]: ov.append((b[4], c[4]))
        chk(f'atlas_{nm}', not bad and not ov and im.mode == 'RGBA', f'{len(a["frames"])} frames {im.size}' + (f' OOB {bad[:5]}' if bad else '') + (f' overlap {ov[:5]}' if ov else ''))
        if nm.startswith('ui_'):
            nb = [k for k, f in a['frames'].items() if f.get('nine') and not (f['nine'][0] + f['nine'][2] < f['w'] and f['nine'][1] + f['nine'][3] < f['h'])]
            chk(f'nine_valid_{nm}', not nb, f'{sum(1 for f in a["frames"].values() if f.get("nine"))} 9-slice' + (f' bad {nb}' if nb else ''))
    ui = J(f'{KIT}/atlas/ui_hd2d_v3@3x.json')['frames']
    # 3 v2 → v3 map
    m = J(f'{KIT}/atlas/v2_to_v3_map.json')['map']; v2f = J(glob.glob(f'{V2}/atlas/ui_hd2d_v2*@3x.json')[0])['frames'] if glob.glob(f'{V2}/atlas/ui_hd2d_v2*@3x.json') else {}
    icf = J(f'{KIT}/atlas/icons_hd2d_v3@3x.json')['frames']
    unres = [k for k, v in m.items() if not v['ok'] or not ((v['v3'][5:] in icf) if v['v3'].startswith('icon:') else (v['v3'] in ui))]
    chk('v2_map_100pct', not unres and (not v2f or set(v2f) <= set(m)), f'{len(m) - len(unres)}/{len(m)}' + (f' unresolved {unres[:8]}' if unres else ''))
    # 4 icons
    v2ic = J(glob.glob(f'{V2}/atlas/icons*@3x.json')[0])['frames'] if glob.glob(f'{V2}/atlas/icons*@3x.json') else {}
    v2names = {k for k in v2ic}; want = v2names | EXTRA_ICONS
    chk('icons_cover_v2_and_6bcd', want <= set(icf), f'{len(icf)} icons（v2 {len(v2names)} + 6b/6c/6d {len(EXTRA_ICONS)}）' + (f' missing {sorted(want - set(icf))}' if want - set(icf) else ''))
    bad_a, bad_d, no_g, no_c = [], [], [], []
    for k, f in icf.items():
        p = f'{KIT}/icons/{k}@3x.png'
        if not os.path.exists(p): bad_d.append(k); continue
        im = Image.open(p).convert('RGBA'); al = np.array(im)[..., 3]
        if not set(np.unique(al).tolist()) <= {0, 255}: bad_a.append(k)
        if list(im.size) != [2 * f['src'][0], 2 * f['src'][1]]: bad_d.append(k)
        if not os.path.exists(f'{KIT}/icons/glow/{k}_glow@3x.png'): no_g.append(k)
        if not f['colors_v3'] > f['colors_v2']: no_c.append(k)
    chk('icons_alpha_0_255', not bad_a, f'{len(icf)} sprite' + (f' bad {bad_a[:8]}' if bad_a else ''))
    chk('icons_dims_2x_src', not bad_d, 'EPX ×2' + (f' bad {bad_d[:8]}' if bad_d else ''))
    chk('icons_glow_layer', not no_g, f'{len(icf) - len(no_g)}/{len(icf)}')
    chk('icons_more_detail_than_v2', not no_c, f'色數 v3>v2：{len(icf) - len(no_c)}/{len(icf)}' + (f' {no_c[:8]}' if no_c else ''))
    # 5 文字
    T = J(f'{KIT}/mockups/texts.json')['texts']
    small = [t for t in T if t['px'] < MIN_PX]; low = [t for t in T if t['contrast'] < MIN_CR]
    chk('text_min_px_18', not small, f'{len(T)} 段字，最細 {min(t["px"] for t in T)}px@3x' + (f' {[(t["screen"], t["text"]) for t in small[:5]]}' if small else ''))
    chk('text_contrast_4_5', not low, f'最低 {min(t["contrast"] for t in T):.2f}' + (f' {[(t["screen"], t["text"], t["contrast"]) for t in low[:8]]}' if low else ''))
    chk('text_fonts_noto', all(t['font'] in ('sans', 'sansb', 'serif') for t in T), 'Noto Sans／Serif CJK TC')
    cs = set(open(f'{KIT}/fonts/charset_v3.txt', encoding='utf-8').read()); used = set(''.join(t['text'] for t in T)) - {' ', '\n'}
    chk('charset_covers_used', used <= cs, f'charset {len(cs)}；用到 {len(used)}' + (f' missing {"".join(sorted(used - cs))}' if used - cs else ''))
    fj = J(f'{KIT}/fonts/fonts_v3.json'); fbad = []
    for r, f in fj['fonts'].items():
        p = f'{KIT}/fonts/{f["file"]}'
        if not os.path.exists(p): fbad.append(f['file']); continue
        try:
            from PIL import ImageFont
            fo = ImageFont.truetype(p, 18); [fo.getmask(ch) for ch in '團絨升級喇夢遊族譜']
        except Exception as e: fbad.append(f'{f["file"]}:{e}')
    chk('font_subsets_load', not fbad, f'{len(fj["fonts"])} 個 .otf' + (f' {fbad}' if fbad else ''))
    # 6 layout
    Lj = J(f'{KIT}/layout_hd2d_v3.json')
    chk('bands_ratio', Lj['bands'] == {'top': [0, 126], 'garden': [126, 1044], 'bottom': [1044, 1266]} and abs(Lj['gardenRatio'] - (1044 - 126) / H) < .001 and Lj['design'] in ([W, H], {'w': W, 'h': H}) , f'{Lj["bands"]} ratio {Lj["gardenRatio"]}')
    oob, small_h, nosc = [], [], [s for s in SCREENS if s not in Lj['screens']]
    for s, d in Lj['screens'].items():
        for k, (x, y, w, h) in d['elements'].items():
            if x < -1 or y < -1 or x + w > W + 1 or y + h > H + 1: oob.append(f'{s}:{k}')
        for k, x, y, w, h in d['hits']:
            if w < 66 or h < 66: small_h.append(f'{s}:{k}')
            if x < 0 or y < 0 or x + w > W or y + h > H: oob.append(f'{s}:hit:{k}')
    chk('layout_screens_17', not nosc and len(Lj['screens']) == len(SCREENS), f'{len(Lj["screens"])} screens' + (f' missing {nosc}' if nosc else ''))
    chk('layout_in_bounds', not oob, f'{sum(len(d["elements"]) for d in Lj["screens"].values())} elements' + (f' OOB {oob[:8]}' if oob else ''))
    chk('hit_area_66', not small_h, f'{sum(len(d["hits"]) for d in Lj["screens"].values())} hits ≥66px@3x（22pt）' + (f' small {small_h[:8]}' if small_h else ''))
    pu = Lj['partsUsed']; pu = list(pu) if isinstance(pu, (list, dict)) else []
    chk('parts_used_in_atlas', set(pu) <= set(ui), f'{len(pu)} parts used / {len(ui)} in atlas' + (f' missing {sorted(set(pu) - set(ui))}' if set(pu) - set(ui) else ''))
    iu = list(Lj['iconsUsed']); chk('icons_used_in_atlas', set(iu) <= set(icf), f'{len(iu)} icons used' + (f' missing {sorted(set(iu) - set(icf))}' if set(iu) - set(icf) else ''))
    rail = [k for k in Lj['screens']['home']['elements'] if k.startswith('rail:')]
    chk('rail_has_dex_kid', {'rail:dex', 'rail:egg_kid'} <= set(rail), f'{rail}')
    # 7 petGlow 規則
    pg = Lj.get('petGlow', {}); st = pg.get('states', {})
    ok = all(st.get(k) == 0 for k in ('sleep', 'sleepClip', 'dreamEnter', 'dreaming')) and st.get('awake') == 1 and pg.get('fadeOut', {}).get('to') == 0 and pg.get('fadeIn', {}).get('to') == 1 and pg.get('keyframes')
    md = open(f'{KIT}/UI_KIT_V3.md', encoding='utf-8').read(); v3md = f'{ART}/ui/style_ref/hd2d_v3/V3.md'
    ok = ok and 'petGlow' in md and os.path.exists(v3md) and '除左佢訓就會關' in open(v3md, encoding='utf-8').read()
    chk('pet_glow_sleep_off', ok, f'states {st}；fadeOut {pg.get("fadeOut", {}).get("ms")}ms／fadeIn {pg.get("fadeIn", {}).get("ms")}ms')
    # 8 portrait
    pr = J(f'{KIT}/portrait/portrait_rects.json'); fbad = [k for k, f in pr['forms'].items() if not all(x in f for x in ('frame', 'eyes', 'rect', 'acc'))]
    chk('portrait_rects_59', len(pr['forms']) == 59 and not fbad and pr.get('v3', {}).get('window') == 110, f'{len(pr["forms"])} forms；v3 window {pr.get("v3", {}).get("window")}')
    # 9 mockups
    bad = [s for s in SCREENS if Image.open(f'{KIT}/mockups/{s}_3x.png').size != (W, H)]
    chk('mockups_585x1266', not bad, f'{len(SCREENS)} 張' + (f' bad {bad}' if bad else ''))
    # 10 衛生
    junk = [p for p in glob.glob(f'{KIT}/**', recursive=True) + glob.glob(f'{ART}/ui/style_ref/hd2d_v3/**', recursive=True) if '_backups' in p or '__pycache__' in p or p.endswith(('.pyc', '.DS_Store'))]
    chk('no_backups_pycache', not junk, f'{junk[:5]}' if junk else 'clean')
    names = list(ui); chk('part_names_unique', len(names) == len(set(names)) and not (set(ui) & set(f'icon:{k}' for k in icf)), f'{len(names)} parts')
def main():
    try: run()
    except Exception as e: import traceback; chk('validator_crash', False, traceback.format_exc()[-600:])
    n = sum(r['ok'] for r in RES); out = dict(kit='kit_hd2d_v3', passed=n, total=len(RES), allPass=n == len(RES), results=RES)
    json.dump(out, open(f'{KIT}/validation.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for r in RES: print(('PASS ' if r['ok'] else 'FAIL ') + r['check'] + ' — ' + r['detail'])
    print(f'{n}/{len(RES)} pass'); sys.exit(0 if n == len(RES) else 1)
if __name__ == '__main__': main()
