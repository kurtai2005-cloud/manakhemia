#!/usr/bin/env python3
"""第 7 批族譜 V3-A validator：python3 validate_familytree_v3.py → ui/familytree_v3/validation.json（exit 1＝有 FAIL）"""
import os, sys, json, glob
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ART = os.path.dirname(HERE); OUT = f'{ART}/ui/familytree_v3'; KIT = f'{ART}/ui/kit_hd2d_v3'
R = []
def chk(name, ok, note=''): R.append(dict(check=name, ok=bool(ok), note=note)); print(('PASS' if ok else 'FAIL'), name, note)
def lum(c):
    c = np.asarray(c, float)[..., :3] / 255; c = np.where(c <= .03928, c / 12.92, ((c + .055) / 1.055) ** 2.4); return c @ np.array([.2126, .7152, .0722])
def cr(a, b): la, lb = lum(a), lum(b); return (max(la, lb) + .05) / (min(la, lb) + .05)
J = json.load(open(f'{OUT}/familytree_v3.json')); LAYG = json.load(open(f'{KIT}/layout_hd2d_v3.json')); FAM = json.load(open(f'{OUT}/family_demo.json'))
# 1 json 入口
need = ['name', 'spec', 'gdd', 'canvas', 'bands', 'split', 'layers', 'parts', 'backgrounds', 'fx', 'stamps', 'relations', 'nodeRules', 'petGlow', 'toggle', 'achievements', 'rewards', 'actions', 'forbidden', 'demo', 'mockups', 'layout', 'hits', 'texts', 'inPartText']
chk('json_keys', all(k in J for k in need), f'{len(need)} keys' + str([k for k in need if k not in J] or ''))
chk('canvas_bands', J['canvas'] == [585, 1266] and J['bands'] == LAYG['bands'] and [v * 3 for v in J['split']] == [0, 126, 1044, 1266] and LAYG['bands']['top'] == [0, 126] and LAYG['bands']['bottom'] == [1044, 1266], f"split {J['split']}×3 → 0/126/1044/1266")
# 2 GDD §2.1 族譜清單
P = J['parts']; cnt = dict(frames=len({k.split('_')[1] for k in P if k.startswith('node_') and k.endswith('_live')}), stamps=len([k for k in P if k.startswith('stamp_')]),
                          lines=len({k.split('_')[1] for k in P if k.startswith('line_') and k.endswith('_h')}), ach=len([k for k in P if k.startswith('ach_') and not k.endswith('_locked')]), warm=int('bg_warm' in J['backgrounds']))
chk('gdd_2_1_list', cnt == dict(frames=2, stamps=3, lines=4, ach=6, warm=1), str(cnt))
chk('gdd_rewards_6', set(J['rewards']) == {a['id'] for a in J['achievements']} and len(J['achievements']) == 6, ', '.join(J['rewards']))
# 3 檔案＋尺寸＋alpha
bad_sz, bad_a, true_a, missing = [], [], 0, []
for k, v in P.items():
    f = f"{OUT}/{v['file']}"
    if not os.path.exists(f): missing.append(k); continue
    im = Image.open(f)
    if list(im.size) != v['size']: bad_sz.append(k)
    a = np.asarray(im.convert('RGBA'))[..., 3]; u = set(np.unique(a).tolist())
    if v['layer'] == 'sprite' and not u <= {0, 255}: bad_a.append(k)
    if v['layer'] in ('ui', 'light') and len(u - {0, 255}): true_a += 1
chk('parts_exist_size', not missing and not bad_sz, f'{len(P)} parts' + (f' missing {missing}' if missing else '') + (f' size {bad_sz}' if bad_sz else ''))
chk('sprite_alpha_0_255', not bad_a, f"sprite parts {[k for k, v in P.items() if v['layer'] == 'sprite']}；UI／光影層真 alpha {true_a} 個（容許）" + (f' bad {bad_a}' if bad_a else ''))
fx = json.load(open(f"{OUT}/{J['fx']}")); fxim = Image.open(f"{OUT}/{fx['sheet']}").convert('RGBA'); u = set(np.unique(np.asarray(fxim)[..., 3]).tolist())
chk('particles_alpha_0_255', u <= {0, 255} and fxim.size == (24 * 6, 72) and len(fx['emitters']) >= 3, f"{fxim.size} {len(fx['emitters'])} emitters")
bgok = all(Image.open(f"{OUT}/{b['file']}").size == (585, 1266) and Image.open(f"{OUT}/{b['file']}").mode == 'RGB' and Image.open(f"{OUT}/{b['light']}").size[0] == 585 for b in J['backgrounds'].values())
chk('backgrounds', bgok and set(J['backgrounds']) == {'bg_normal', 'bg_warm'}, 'bg_normal／bg_warm 585×1266 RGB＋light_add')
# 4 頭像 sprite（現有寵物 sprite，0/255）
sys.path.insert(0, HERE); sys.dont_write_bytecode = True
import build_familytree_v3 as B
badav = []
for n in B.FAMILY:
    a = np.asarray(B.avatar(n))[..., 3]
    if not set(np.unique(a).tolist()) <= {0, 255}: badav.append(n['id'])
forms_ok = all((n.get('egg') or n['form'] in B.M3.M.PR['forms'] or n['form'] in B.M3.M.PR['aliases']) for n in B.FAMILY)
chk('avatars_pet_sprites_0_255', not badav and forms_ok, f"{len(B.FAMILY)} 頭像（{', '.join(n['form'] for n in B.FAMILY)}）" + (f' bad {badav}' if badav else ''))
# 5 關係推導（獨立重算）
nodes = {n['id']: n for n in FAM['nodes']}
def anc(i):
    out = []; p = nodes[i]['parentId']
    while p: out.append(p); p = nodes[p]['parentId']
    return out
par = sorted([[n['parentId'], n['id']] for n in nodes.values() if n['parentId']]); sib = sorted([sorted([a, b]) for a in nodes for b in nodes if a < b and nodes[a]['parentId'] and nodes[a]['parentId'] == nodes[b]['parentId']])
an = sorted([[a, i, k + 1] for i in nodes for k, a in enumerate(anc(i)) if k >= 1]); D = FAM['derived']
gens_ok = all(n['gen'] == (len(anc(i))) for i, n in nodes.items() if n['parentId']) and max(n['gen'] for n in nodes.values()) - min(n['gen'] for n in nodes.values()) + 1 >= 3
main = FAM['main']; hs = D['house']; hs_ok = all(nodes[b]['parentId'] != nodes[main]['parentId'] and b not in anc(main) and main not in anc(b) and nodes[b]['alive'] for a, b in hs) and len(hs) >= 1
chk('relations_derive', sorted(D['parent']) == par and sorted(map(sorted, D['sibling'])) == sib and sorted(D['ancestor']) == an and gens_ok and hs_ok,
    f"傳 {len(par)}／兄弟 {len(sib)}／祖 {len(an)}／同屋 {len(hs)}；{max(n['gen'] for n in nodes.values()) + 1} 代")
f16 = ['id', 'line', 'parentId', 'gen', 'bornDay', 'adultDay', 'pattern', 'move', 'story', 'frozen']
chk('family_fields_gdd_1_6', all(all(k in n for k in f16) and ('route' in n or 'series' in n) and len(n['story']) == 4 and n['line'] in ('tuanrong', 'pet2') for n in FAM['nodes']), f'{len(FAM["nodes"])} nodes；欄位 {len(f16)}＋route|series；story×4')
# 6 petGlow
pg = J['petGlow']; L0 = LAYG['petGlow']
chk('petglow_rule_sync', pg['states'] == L0['states'] and pg['fadeOut'] == L0['fadeOut'] and pg['fadeIn'] == L0['fadeIn'] and pg['states']['sleep'] == 0 and pg['states']['sleepy'] == .6,
    'awake 1／sleepy .6／sleep・sleepClip・dreamEnter・dreaming 0；fadeOut 600 easeInQuad／fadeIn 400 easeOutQuad＋pulse 150')
badg = [i for i, v in pg['nodes'].items() if (nodes[i]['state'] in ('sleep', 'sleepClip', 'dreamEnter', 'dreaming') or not nodes[i]['alive'] or nodes[i]['egg']) and v['petGlow'] != 0]
badw = [i for i, v in pg['nodes'].items() if nodes[i]['alive'] and not nodes[i]['egg'] and v['petGlow'] != L0['states'].get(nodes[i]['state'], 1)]
chk('petglow_nodes', not badg and not badw, f"瞓緊 {[i for i in nodes if nodes[i]['state'] == 'sleep']}＝0；退休／蛋＝0；其他＝states 值" + (f' bad {badg + badw}' if badg + badw else ''))
# 實際畫：瞓覺 aura 冇光（同灰節點一樣 0）；醒時有
def aura_energy(nid, state):
    n = dict(next(f for f in B.FAMILY if f['id'] == nid)); n['state'] = state; im = B.node_aura_layer(n)
    return 0.0 if im is None else float(np.asarray(im)[..., 3].astype(float).sum() / 255)
e_sleep, e_awake, e_sleepy, e_gray, e_egg = aura_energy('doudou', 'sleep'), aura_energy('doudou', 'awake'), aura_energy('bobo', 'sleepy'), aura_energy('guangguang', 'awake'), aura_energy('egg_mie', 'awake')
e_bobo = aura_energy('bobo', 'awake'); src = open(f'{HERE}/build_familytree_v3.py').read()
chk('petglow_render_sleep_off', e_awake > 0 and e_sleep == 0 and e_gray == 0 and e_egg == 0 and aura_energy('bobo', 'dreaming') == 0 and abs(e_sleepy / e_bobo - .6) < .02 and 'au = node_aura_layer(n)' in src,
    f'aura 能量：豆豆瞓 {e_sleep:.0f}（醒時 {e_awake:.0f}）／波波醒 {e_bobo:.0f}／波波眼瞓 {e_sleepy:.0f}（×{e_sleepy / e_bobo:.2f}）／光光退休 {e_gray:.0f}／蛋 {e_egg:.0f}；draw_node 只經 node_aura_layer')
# 7 mockups＋文字
ms = J['mockups']; badm = [k for k, v in ms.items() if Image.open(f"{OUT}/{v['file']}").size != (585, 1266)]
chk('mockups_585x1266', len(ms) == 8 and not badm, f'{len(ms)} 張：' + ', '.join(ms))
T = json.load(open(f"{OUT}/{J['texts']}")); small = [t for t in T if t['px'] < 18]; low = [t for t in T if t['contrast'] is None or t['contrast'] < 4.5]
chk('text_min_18', not small, f'{len(T)} 段字，最細 {min(t["px"] for t in T)}px')
chk('text_contrast_4_5', not low, f'最低 {min(t["contrast"] for t in T):.2f}' + (f' bad {[(t["screen"], t["text"], t["contrast"]) for t in low[:5]]}' if low else ''))
ip = [(t['part'], round(float(cr(t['fg'], t['bg'])), 2)) for t in J['inPartText']]
chk('in_part_text', all(c >= 4.5 for _, c in ip) and all(t['px'] >= 18 for t in J['inPartText']), str(ip))
fonts = {t['font'] for t in T}; src = open(f'{HERE}/ui_hd2d_v3_lib.py').read()
fus = [f for f in glob.glob(f'{OUT}/**/*', recursive=True) if 'fusion' in os.path.basename(f).lower() or f.lower().endswith(('.ttf', '.otf', '.ttc'))]
chk('font_noto_only', fonts <= {'serif', 'sans', 'sansb'} and 'Noto' in src and not fus , f'fonts {sorted(fonts)}（Noto CJK TC）；Fusion Pixel 冇用')
scr = {t['screen'] for t in T}; chk('text_screens', scr == set(ms), f'{len(scr)} screens')
# 8 衛生
junk = [p for p in glob.glob(f'{OUT}/**/*', recursive=True) + glob.glob(f'{HERE}/*') if os.path.basename(p) in ('__pycache__', '_backups') or p.endswith('.pyc')]
big = [p for p in glob.glob(f'{OUT}/**/*', recursive=True) if os.path.isfile(p) and os.path.getsize(p) >= 20 * 1024 * 1024]
chk('no_pycache_backups', not junk, f'{len(junk)} junk' + (f' {junk[:3]}' if junk else ''))
chk('files_lt_20MB', not big, f"最大 {max(os.path.getsize(p) for p in glob.glob(f'{OUT}/**/*', recursive=True) if os.path.isfile(p)) / 1e6:.2f}MB")
md = f'{OUT}/FAMILYTREE_V3.md'; chk('readme', os.path.exists(md) and 'petGlow' in open(md).read(), 'FAMILYTREE_V3.md')
ok = all(r['ok'] for r in R); json.dump(dict(ok=ok, n=len(R), passed=sum(r['ok'] for r in R), checks=R), open(f'{OUT}/validation.json', 'w'), ensure_ascii=False, indent=1)
print(f"{'ALL PASS' if ok else 'FAIL'} {sum(r['ok'] for r in R)}/{len(R)}"); sys.exit(0 if ok else 1)
