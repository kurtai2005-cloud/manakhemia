#!/usr/bin/env python3
"""第 8 批工作場景 V3-A validator：python3 validate_workscenes_v3.py → scenes/work_v3/validation.json（exit 1＝有 FAIL）"""
import os, sys, json, glob
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ART = os.path.dirname(HERE); OUT = f'{ART}/scenes/work_v3'; KIT = f'{ART}/ui/kit_hd2d_v3'
R = []
def chk(name, ok, note=''): R.append(dict(check=name, ok=bool(ok), note=note)); print(('PASS' if ok else 'FAIL'), name, note)
def im(p): return Image.open(f'{OUT}/{p}')
def alpha01(p): a = np.asarray(im(p).convert('RGBA'))[..., 3]; return set(np.unique(a).tolist()) <= {0, 255}
J = json.load(open(f'{OUT}/workscenes_v3.json')); LAYG = json.load(open(f'{KIT}/layout_hd2d_v3.json'))
need = ['name', 'spec', 'gdd', 'numbersUnchanged', 'canvas', 'bands3x', 'stack', 'scenes', 'props', 'decoLv3', 'hatsLv5', 'icons', 'clips', 'sizeClass', 'fx', 'petGlow', 'ui', 'mockups', 'layout', 'hits', 'texts', 'tools']
chk('json_keys', all(k in J for k in need), str([k for k in need if k not in J] or f'{len(need)} keys'))
chk('canvas_bands', J['canvas']['layer3x'] == [669, 1338] and J['canvas']['screen3x'] == [585, 1266] and J['bands3x'] == dict(top=[0, 126], bottom=[1044, 1266]) and LAYG['bands']['top'] == [0, 126] and LAYG['bands']['bottom'] == [1044, 1266], str(J['canvas']['screen3x']))
# GDD §2.1 清單
S, P, D, H, I, C = J['scenes'], J['props'], J['decoLv3'], J['hatsLv5'], J['icons'], J['clips']; jobs = ['post', 'garden', 'tower', 'kitchen']
chk('gdd_scenes_5', sorted(S) == sorted(['post', 'garden', 'tower_day', 'tower_night', 'kitchen']), ', '.join(S))
chk('gdd_props_8', len(P) == 8 and all(sum(k.startswith(j) for k in P) == 2 for j in jobs) and all(4 <= v['frames'] <= 6 for v in P.values()), str({k: v['frames'] for k, v in P.items()}))
chk('gdd_deco_lv3_4', sorted(D) == sorted(jobs) and all(v['unlock'] == '職業 Lv3' for v in D.values()), ', '.join(v['zh'] for v in D.values()))
chk('gdd_hats_lv5_12', sorted(H) == sorted(jobs) and all(sorted(v['sizes']) == ['L', 'M', 'S'] for v in H.values()), f"{sum(len(v['sizes']) for v in H.values())} 頂")
ck = [f'{j}_{z}_{k}' for j in jobs for z in 'SML' for k in ('loop', 'done')]
chk('gdd_clips_24', sorted(C) == sorted(ck) and all((v['frames'] in (6, 7, 8)) if k.endswith('loop') else v['frames'] == 4 for k, v in C.items()) and all(len(v['petTransform']) == v['frames'] for v in C.values()), f'{len(C)} clips')
chk('gdd_icons_8_48px', len(I) == 8 and sum(v['kind'] == 'basic' for v in I.values()) == 4 and all(im(v['img']).size == (48, 48) for v in I.values()), ', '.join(I))
chk('gdd_night_tower', S['tower_night'] and json.load(open(f"{OUT}/tower_night/grade.json"))['variantHours'] == [18, 6], '瞭望台夜 18–06（夜更 21–05 包住）')
chk('gdd_tod_others', all('tod' in json.load(open(f"{OUT}/{k}/grade.json")) for k in ('post', 'garden', 'kitchen')), 'dawn/day/dusk/night')
chk('gdd_mockups', {'ws_done_popup', 'ws_dayoff'} <= set(J['mockups']) and len(J['mockups']) >= 7, ', '.join(J['mockups']))
chk('numbers_unchanged', all(v.get('affectsGame') is False for v in P.values()) and '25%' in J['numbersUnchanged'], '道具 affectsGame=false')
# 檔案／尺寸／alpha
miss, bsz, ba = [], [], []
for k, v in S.items():
    for n, p in v['layers1x'].items():
        if not os.path.exists(f'{OUT}/{p}'): miss.append(p); continue
        if n != 'lut' and im(p).size != ((195, 422) if n == 'vignette' else (223, 446)): bsz.append(p)
        if n in ('sky', 'far', 'mid', 'fore', 'emissive') and not alpha01(p): ba.append(p)
    for n, p in v['layers3x'].items():
        if not os.path.exists(f'{OUT}/{p}'): miss.append(p); continue
        if im(p).size != ((585, 1266) if n == 'vignette' else (669, 1338)): bsz.append(p)
        if n in ('sky', 'mid', 'emissive') and not alpha01(p): ba.append(p)
chk('scene_layers', not miss and not bsz, f'{sum(len(v["layers1x"]) + len(v["layers3x"]) for v in S.values())} 層' + str(miss[:3] + bsz[:3] or ''))
spr = []
for v in P.values():
    spr.append(v['sheet']); g = im(v['sheet']).size; fw, fh = v['frameSize3x']
    if g[0] != fw * v['frames'] or g[1] % fh: bsz.append(v['sheet'])
spr += [v['img'] for v in D.values()] + [z['img'] for v in H.values() for z in v['sizes'].values()] + [v['img'] for v in I.values()]
for v in C.values():
    spr.append(v['sheet']); g = im(v['sheet']).size
    if g != (v['frameSize3x'][0] * v['frames'], v['frameSize3x'][1] * len(v['rows'])): bsz.append(v['sheet'])
for p in spr:
    if not os.path.exists(f'{OUT}/{p}'): miss.append(p)
    elif not alpha01(p): ba.append(p)
chk('sprite_files_sizes', not miss and not bsz, f'{len(spr)} 張 sprite' + str(miss[:3] + bsz[:3] or ''))
chk('sprite_alpha_0_255', not ba, 'sprite／solid 層 alpha 只有 0/255' + str(ba[:4] or ''))
ga = [v['glow']['sheet'] for v in list(P.values()) + list(C.values()) if 'glow' in v] + [v['glow']['img'] for v in I.values() if 'glow' in v]
chk('glow_true_alpha', all(os.path.exists(f'{OUT}/{p}') for p in ga) and sum(len(np.unique(np.asarray(im(p).convert('RGBA'))[..., 3])) > 2 for p in ga) == len(ga), f'{len(ga)} glow 層真 alpha')
chk('hat_sizes_SML', all(H[j]['sizes'][z]['size3x'][0] < H[j]['sizes'][y]['size3x'][0] for j in jobs for z, y in (('S', 'M'), ('M', 'L'))), 'S<M<L')
sc = J['sizeClass']; chk('size_class_all_forms', sum(sc['counts'].values()) == len(sc['forms']) == 59 and set(v['size'] for v in sc['forms'].values()) == {'S', 'M', 'L'}, str(sc['counts']))
# 字＋對比
T = json.load(open(f"{OUT}/{J['texts']}")); small = [t for t in T if t['px'] < 18]; low = [t for t in T if t['contrast'] is None or t['contrast'] < 4.5]
chk('text_min_18px', not small and T, f'{len(T)} 段字，最細 {min(t["px"] for t in T)}px')
chk('text_contrast_4_5', not low, f'最低 {min(t["contrast"] for t in T):.2f}' + (str([(t["screen"], t["text"], t["contrast"]) for t in low[:5]]) if low else ''))
chk('text_font_noto', all(t['font'] in ('sans', 'sansb', 'serif') for t in T), 'Noto Sans/Serif CJK TC')
chk('ui_parts_no_text', all(os.path.exists(f"{OUT}/{v['img']}") for v in J['ui'].values()), f"{len(J['ui'])} 件（字 runtime 畫）")
chk('mockup_sizes', all(im(v['img']).size == (585, 1266) for v in J['mockups'].values()), f"{len(J['mockups'])} 張 585×1266")
# petGlow
pg = J['petGlow']; g_ok = all(json.load(open(f'{OUT}/{k}/grade.json'))['petLight']['multiplyBy'] == 'petGlow' for k in S)
t = pg['test']; bb = t['changedBBox']; fx, fy = t['petFoot3x']
chk('petglow_rule', pg['values'] == dict(awake=1, sleepy=.6, sleep=0, sleepClip=0, dreamEnter=0, dreaming=0) and pg['ref'].endswith('#petGlow') and 'petGlow' in LAYG and g_ok, 'awake 1／sleepy .6／瞓 0；grade.petLight×petGlow')
chk('petglow_scene_lights_fixed', bb and t['windowMaxDiff'] == 0 and t['fireMaxDiff'] == 0 and bb[0] > fx - 42 - 160 and bb[2] < fx - 42 + 160 and bb[1] > fy - 36 - 260, f'petGlow 1→0 只郁寵物附近 bbox {bb}')
chk('clip_glow_hook', all(('petGlow' in v['glow'].get('multiplyBy', '')) or 'tower' in k for k, v in C.items() if 'glow' in v), 'clip glow ×petGlow')
# 雜檔
junk = [p for p in glob.glob(f'{OUT}/**/*', recursive=True) if '__pycache__' in p or '_backups' in p or p.endswith(('.pyc', '_tmp.json'))] + glob.glob(f'{HERE}/__pycache__')
chk('no_junk', not junk, str(junk[:3] or 'clean'))
big = [p for p in glob.glob(f'{OUT}/**/*', recursive=True) if os.path.isfile(p) and os.path.getsize(p) >= 20 << 20]
chk('file_lt_20mb', not big, f"{sum(os.path.getsize(p) for p in glob.glob(f'{OUT}/**/*', recursive=True) if os.path.isfile(p)) / 1e6:.1f}MB")
nf = sum(1 for p in glob.glob(f'{OUT}/**/*', recursive=True) if os.path.isfile(p))
ok = all(r['ok'] for r in R); json.dump(dict(ok=ok, pass_=sum(r['ok'] for r in R), total=len(R), files=nf, results=R), open(f'{OUT}/validation.json', 'w'), ensure_ascii=False, indent=1)
print(f'{sum(r["ok"] for r in R)}/{len(R)} PASS'); sys.exit(0 if ok else 1)
