# 《微光小圃》HD-2D UI kit validator — 檢查 atlas/JSON/9-slice/字體/icon/佈局/對比度/文件引用/SFX 名。
# 用法：cd art-pet && python3 tools/validate_ui_kit_hd2d.py  → 印 PASS/FAIL，寫 ui/kit_hd2d/validation.json
import json, os, re, sys
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); KIT = os.path.normpath(os.path.join(HERE, '..', 'ui', 'kit_hd2d'))
ERR, WARN, INFO = [], [], {}
def err(m): ERR.append(m)
def hx(s): s = s.lstrip('#'); return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
def lum(c):
    c = [v / 255 for v in c[:3]]; c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
def cr(a, b): la, lb = sorted([lum(a), lum(b)], reverse=True); return (la + 0.05) / (lb + 0.05)

# ---- atlases ----
A = {}
for s in (3, 2):
    for kind in ('ui_hd2d', 'icons_hd2d'):
        jp, pp = f'{KIT}/atlas/{kind}@{s}x.json', f'{KIT}/atlas/{kind}@{s}x.png'
        if not (os.path.exists(jp) and os.path.exists(pp)): err(f'missing {kind}@{s}x'); continue
        J = json.load(open(jp)); im = Image.open(pp)
        if im.mode != 'RGBA': err(f'{pp} not RGBA')
        if list(im.size) != J['size']: err(f'{kind}@{s}x size mismatch')
        if max(im.size) > 2048: err(f'{kind}@{s}x > 2048')
        fr = J.get('frames') or J.get('icons'); A[(kind, s)] = (J, im, fr)
        a = np.asarray(im)[..., 3]; occ = np.zeros(a.shape, bool)
        for n, f in fr.items():
            x, y, w, h = f['x'], f['y'], f['w'], f['h']
            if x < 0 or y < 0 or x + w > im.width or y + h > im.height: err(f'{kind}@{s}x {n} out of bounds'); continue
            if occ[y:y + h, x:x + w].any(): err(f'{kind}@{s}x {n} overlaps')
            occ[y:y + h, x:x + w] = True
            if a[y:y + h, x:x + w].max() == 0: err(f'{kind}@{s}x {n} empty')
            bx, by, bw, bh = f['box']
            if bw <= 0 or bh <= 0: err(f'{n} bad box')
            if 'nine' in f:
                l, t, r, b = f['nine']; sl = f.get('slice')
                if sl not in ('9', '3h', '3v'): err(f'{n} bad slice {sl}')
                if l + r >= w and sl != '3v': err(f'{kind}@{s}x {n} nine l+r >= w')
                if t + b >= h and sl != '3h': err(f'{kind}@{s}x {n} nine t+b >= h')
                if sl in ('9', '3h') and (l < bx * 0.99 or r < (w - bx - bw) * 0.99): err(f'{kind}@{s}x {n} nine inset inside glow pad (l/r)')
            if f.get('group') == 'label':
                if f['font'] == 'serif' and f['size_art'] < 9: err(f'{n} serif label < 9 art')
                if f['font'] == 'sans' and f['size_art'] < 7: err(f'{n} sans label < 7 art')
        INFO[f'{kind}@{s}x'] = dict(size=im.size, count=len(fr))
if ('ui_hd2d', 3) in A and ('ui_hd2d', 2) in A and set(A[('ui_hd2d', 3)][2]) != set(A[('ui_hd2d', 2)][2]): err('@3x/@2x frame names differ')
if ('icons_hd2d', 3) in A and ('icons_hd2d', 2) in A and set(A[('icons_hd2d', 3)][2]) != set(A[('icons_hd2d', 2)][2]): err('@3x/@2x icon names differ')
FR = A[('ui_hd2d', 3)][2]; IC = A[('icons_hd2d', 3)][2]; AIM = A[('ui_hd2d', 3)][1]

# ---- required inventory (audit + stubs) ----
REQ = ['panel_glass', 'panel_paper', 'panel_inset', 'panel_inset_sel', 'banner_event', 'sheet_handle', 'card', 'card_sel', 'card_locked', 'card_qmark',
       'btn_pri', 'btn_pri_p', 'btn_sec', 'btn_rose', 'btn_violet', 'btn_dis', 'btn16_pri', 'pill_pri', 'pill_sec', 'pill_dis', 'subtab', 'subtab_on',
       'close', 'close_p', 'chip', 'chip_plus', 'nameplate', 'stage_tag', 'need_trough', 'need_fill_feed', 'need_fill_mood', 'need_fill_clean', 'need_fill_energy', 'need_fill_low',
       'exp_trough', 'exp_fill', 'exp_gem_on', 'exp_gem_off', 'prog_trough', 'prog_fill_teal', 'dock_bar', 'dock_pillar', 'dock_gem', 'label_plate',
       'red_dot', 'red_dot_num', 'toast', 'toast_wing_l', 'bubble', 'bubble_tail', 'thought_dots', 'plaque', 'plaque_tail_l', 'plaque_tail_r', 'plaque_gem',
       'toggle_track_on', 'toggle_track_off', 'toggle_knob_on', 'check_on', 'check_off', 'seg_bg', 'seg_on', 'scroll_thumb', 'divider', 'star_on', 'star_off',
       'stamp_done', 'timeline_dot', 'hint_arrow', 'fx_ripple', 'fx_spark', 'fx_mote', 'fx_sweep', 'fx_veil',
       'med28_pri', 'med28_pri_p', 'med24_navy', 'med22_navy', 'med25_pri', 'med18_navy_in', 'med16_navy', 'med20_pri', 'med19_paper', 'med11_navy', 'med30_pri',
       # part 2
       'med24_dis', 'pill_navy', 'scroll_fade_top', 'scroll_fade_bot', 'scroll_glow_top', 'scroll_glow_bot',
       'lbl_pill_pri_擺上去', 'lbl_pill_sec_擺緊', 'lbl_pill_navy_清空', 'lbl_pill_dis_委託獎', 'lbl_pill_dis_訪客禮', 'lbl_act_佈置', 'lbl_title_升級啦']
for n in REQ:
    if n not in FR: err(f'missing frame {n}')
STUB5A = ['family_crest', 'tree_node', 'tree_node_sel', 'tree_line_h', 'tree_line_v', 'tree_joint']
for n in STUB5A:
    if n not in FR or not FR[n].get('stub'): err(f'5a stub {n} missing/not flagged')
ICREQ = ['feed', 'clean', 'sleep', 'light', 'star', 'gift', 'heart_bunny', 'play_cat', 'book_bear', 'gear_chick', 'sprout', 'dex', 'diary', 'bond', 'surprise', 'minigame',
         'cabinet', 'badge', 'mail', 'info', 'lock', 'check', 'sound', 'quality', 'water', 'bedtime', 'reset', 'hint', 'mg_tease', 'mg_stardust', 'mg_leaf', 'mg_hide', 'mg_firefly',
         'house', 'decorate', 'furniture', 'family_tree', 'family_level', 'back', 'plus', 'clear']
for n in ICREQ:
    if n not in IC: err(f'missing icon {n}')
    elif not os.path.exists(f'{KIT}/icons/ic_{n}@3x.png'): err(f'missing icons/ic_{n}@3x.png')

# ---- fonts ----
FJ = json.load(open(f'{KIT}/fonts/fonts_hd2d.json'))['fonts']
for nm, F in FJ.items():
    im = Image.open(f'{KIT}/fonts/{F["image"]}'); a = np.asarray(im.convert('RGBA'))[..., 3]
    if F['scale'] == 1 and not set(np.unique(a)) <= {0, 255}: err(f'font {nm} pixel font has partial alpha')
    for ch, g in F['glyphs'].items():
        if g['adv'] <= 0: err(f'font {nm} {ch!r} adv<=0')
        if g['w'] and (g['x'] + g['w'] > im.width or g['y'] + g['h'] > im.height): err(f'font {nm} {ch!r} out of bounds')
    need = '0123456789+-/' if nm != 'round' else '0123456789+'
    if nm in ('gold', 'px7', 'px7_ol'): need += '✦'
    for ch in need:
        if ch not in F['glyphs']: err(f'font {nm} missing {ch!r}')
INFO['fonts'] = {k: len(v['glyphs']) for k, v in FJ.items()}

# ---- layout ----
LJ = json.load(open(f'{KIT}/layout_hd2d.json'))
if LJ['top']['h'] > 52: err('top UI > 52')
if LJ['bottom']['h'] > 100: err('bottom UI > 100')
if LJ['garden']['h'] / 422 <= 0.5: err('garden+pet area <= 50%')
if LJ['top']['h'] + LJ['garden']['h'] + LJ['bottom']['h'] != 422: err('layout bands != 422')
INFO['layout'] = dict(top=LJ['top']['h'], garden=LJ['garden']['h'], bottom=LJ['bottom']['h'], garden_pct=LJ['garden']['pct'])

# ---- contrast (sample sprite centre over game navy) ----
def centre(n):
    f = FR[n]; x, y = f['x'] + f['box'][0], f['y'] + f['box'][1]; w, h = f['box'][2], f['box'][3]
    reg = np.asarray(AIM.crop((x + w * 3 // 8, y + h * 3 // 8, x + w * 5 // 8, y + h * 5 // 8))).astype(float)
    bg = np.array(hx('#1E2448'), float); a = reg[..., 3:4] / 255
    return tuple((reg[..., :3] * a + bg * (1 - a)).reshape(-1, 3).mean(0))
CT = []
def chk(name, fg, bg, need):
    r = cr(fg, bg); CT.append(dict(pair=name, ratio=round(r, 2), need=need, ok=bool(r >= need)))
    if r < need: err(f'contrast {name} {r:.2f} < {need}')
for kd, st in (('pri', '#7A3A10'), ('sec', '#0F4A5E'), ('rose', '#7A1838'), ('violet', '#3A2470')):
    chk(f'btn_{kd} 字描邊 vs 掣底', hx(st), centre(f'btn_{kd}'), 3.0); chk(f'btn_{kd} 白字 vs 描邊', hx('#FFFFFF'), hx(st), 7.0)
chk('btn_dis 深字 vs 停用底', hx('#262A48'), centre('btn_dis'), 4.5)
chk('pill_dis 深字 vs 停用底', hx('#262A48'), centre('pill_dis'), 4.5)
chk('card_locked 字 vs 底', hx('#F4F5FC'), centre('card_locked'), 4.5)
chk('card_locked 底 vs 面板底（可分辨）', centre('card_locked'), centre('panel_glass'), 1.4)
chk('正文 cream vs panel_glass', hx('#FFF5DC'), centre('panel_glass'), 7.0)
chk('正文 cream vs panel_inset', hx('#FFF5DC'), centre('panel_inset'), 7.0)
chk('ink vs panel_paper', hx('#3A2840'), centre('panel_paper'), 7.0)
chk('分頁字 vs dock', hx('#EFE6D0'), centre('dock_bar'), 7.0)
for nk in ('feed', 'mood', 'clean', 'energy', 'low'): chk(f'need_fill_{nk} vs 槽', centre(f'need_fill_{nk}'), hx('#0B0E24'), 3.0)
chk('prog_fill_teal vs 槽', centre('prog_fill_teal'), hx('#0B0E24'), 3.0)
for kd, st in (('pri', '#7A3A10'), ('sec', '#0F4A5E')): chk(f'pill_{kd} 字描邊 vs pill 底', hx(st), centre(f'pill_{kd}'), 3.0)
chk('pill_navy cream 字 vs pill 底', hx('#FFF5DC'), centre('pill_navy'), 7.0)
chk('med24_dis 鎖 icon 白 vs 停用底（形狀可讀）', hx('#F4F5FC'), centre('med24_dis'), 1.5)
chk('med24_dis vs med24_navy（一眼分到停用）', centre('med24_dis'), centre('med24_navy'), 2.0)
chk('px7_ol 字 vs 描邊', hx('#FFF5DC'), hx('#1A1230'), 7.0)

# ---- docs reference check ----
DOCS = {}
for d in ('UI_KIT.md', 'MOTION_HD2D.md'):
    p = f'{KIT}/{d}'
    if not os.path.exists(p): err(f'missing {d}'); continue
    DOCS[d] = open(p).read()
SFX = set()
rd = '/workspace/遊音-staging/audio/README.md'
if os.path.exists(rd): SFX = set(re.findall(r'sfx_ui8_[a-z_]+[a-z]', open(rd).read()))
else: SFX = {'sfx_ui8_' + s for s in 'tab_switch_a tab_switch_b btn_press_a btn_press_b btn_sparkle popup_open popup_close toast_in badge_wiggle transition_heart_close transition_heart_open confirm cancel error toggle_on toggle_off tap_a tap_b coin'.split()}
PFX = ('panel_', 'card', 'btn_', 'btn16_', 'pill_', 'subtab', 'close', 'chip', 'nameplate', 'stage_tag', 'need_', 'bar_tip', 'exp_', 'prog_', 'dock_', 'label_plate', 'red_dot',
       'toast', 'bubble', 'thought_', 'plaque', 'toggle_', 'check_', 'seg_', 'slider_', 'scroll_', 'divider', 'star_', 'stamp_', 'timeline_', 'hint_', 'fx_', 'family_crest', 'tree_', 'sheet_', 'banner_', 'med')
refs = 0
for d, t in DOCS.items():
    for tok in re.findall(r'`([^`]+)`', t):
        for part in re.split(r'[ /,，、+＋]+', tok):
            if part.startswith('ic:'):
                refs += 1
                if part[3:] not in IC: err(f'{d}: unknown icon {part}')
            elif part.startswith('sfx_ui8_'):
                pass
            elif re.fullmatch(r'[a-z0-9_]+', part) and part.startswith(PFX) and not part.endswith('_') and '*' not in part:
                refs += 1
                if part not in FR: err(f'{d}: unknown frame `{part}`')
    for line in t.splitlines():
        for s_ in re.findall(r'sfx_ui8_[a-z_]+[a-z]', line):
            if s_ not in SFX and '建議' not in line and '→' not in line: err(f'{d}: sfx {s_} not in 遊音 README')
INFO['doc_refs_checked'] = refs

# ---- folder hygiene ----
for root, dirs, files in os.walk(KIT):
    if '_backups' in root.split(os.sep) or '_backups' in dirs: err('_backups found in kit')
# ---- 4b re-skin pack (part 2) ----
RS = f'{KIT}/reskin_4b'; H4 = os.path.normpath(f'{KIT}/../../sprites/series2_house')
if not os.path.exists(f'{RS}/reskin_map.json'): err('missing reskin_4b/reskin_map.json')
else:
    RM = json.load(open(f'{RS}/reskin_map.json')); base = os.path.normpath(f'{KIT}/../..')
    for it in RM['items']:
        o, r = f"{base}/{it['orig']}", f"{base}/{it['reskin']}"
        if not os.path.exists(o): err(f"reskin orig missing {it['orig']}"); continue
        if not os.path.exists(r): err(f"reskin png missing {it['reskin']}"); continue
        so, sr = Image.open(o).size, Image.open(r).size
        if so != sr or list(sr) != it['size']: err(f"reskin size mismatch {it['id']} {so} vs {sr}")
    import hashlib
    for f, h in RM.get('untouched4bSha1', {}).items():
        p_ = f'{H4}/ui/{f}'
        if not os.path.exists(p_) or hashlib.sha1(open(p_, 'rb').read()).hexdigest() != h: err(f'4b ui file changed since reskin build: {f}')
    INFO['reskin_items'] = len(RM['items'])
for m in ('mockups/home_3x.png', 'mockups/popup_3x.png', 'mockups/levelup_3x.png', 'overview_3x.png'):
    if not os.path.exists(f'{KIT}/{m}'): err(f'missing {m}')
    else:
        w, h = Image.open(f'{KIT}/{m}').size
        if m.startswith('mockups') and (w, h) != (585, 1266): err(f'{m} not 3x (585x1266)')

res = dict(result='PASS' if not ERR else 'FAIL', errors=ERR, warnings=WARN, info=INFO, contrast=CT)
json.dump(res, open(f'{KIT}/validation.json', 'w'), ensure_ascii=False, indent=1, default=str)
print(res['result'], f'{len(ERR)} error', INFO.get('layout'), f'contrast {sum(c["ok"] for c in CT)}/{len(CT)}')
for e in ERR[:40]: print(' -', e)
sys.exit(1 if ERR else 0)
