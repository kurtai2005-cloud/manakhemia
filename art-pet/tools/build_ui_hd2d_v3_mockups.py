# 《微光小圃》UI kit v3（V3-A 金光現代 HD-2D）— mockups ＋ layout_hd2d_v3.json ＋ texts.json — 遊美 2026-11-02
# 先跑 ui_hd2d_v3_kit.py（icons／atlas），再跑呢個。純 Pillow／numpy，冇 AI 圖。
import os, sys, json, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import ui_hd2d_v3_lib as L
from ui_hd2d_v3_lib import C, A, P, W, H, text, tw, icon, comp, compc, new
import build_ui_hd2d_v3_concept as CN
M = CN.M; X = CN.X
KIT = L.KIT; OUT = f'{KIT}/mockups'; ROOT = L.ROOT; BT = f'{ROOT}/art/breakthrough'
LAY = {}      # screen -> {elements}
HITS = {}     # screen -> [[name, x, y, w, h]]
def reg(name, x, y, w, h, hit=True):
    s = L.SCREEN[0]; LAY.setdefault(s, {})[name] = [round(x, 1), round(y, 1), round(w, 1), round(h, 1)]
    if hit:
        cx, cy = x + w / 2, y + h / 2; hw, hh = max(w, 66), max(h, 66); cx = min(max(cx, hw / 2), L.W - hw / 2); cy = min(max(cy, hh / 2), L.H - hh / 2); HITS.setdefault(s, []).append([name, round(cx - hw / 2, 1), round(cy - hh / 2, 1), round(hw, 1), round(hh, 1)])
RADIUS = {'panel': 24, 'panel_r16': 16, 'card': 18, 'card_sel': 18, 'card_locked': 18, 'egg_card': 18, 'panel_flat': 20, 'dock': 28, 'toast': None, 'label_pill': None, 'bubble': None, 'chip': None, 'share_card_bg': 28}
def panel(bd, name, x, y, w, h, shadow=True, sh_a=.35):
    x, y, w, h = int(x), int(y), int(w), int(h); r = RADIUS.get(name, 18); r = h / 2 if r is None else r; m = L.rr_mask(w, h, r)
    if shadow: L.drop_shadow(bd, m, x, y, 10, 6, sh_a)
    if L.PARTS[name]['backdrop']: L.backdrop(bd, x, y, w, h, m)
    comp(bd, P(name, w, h), x, y)
# ---------------------------------------------------------------- 頭像（B ×2 face crop；k=round(d/22)）
def face(form, state, acc=None, wear=None, job=None, pattern_from=None, k=5):
    f = M.PR['aliases'].get(form, form); R = M.PR['forms'][f]; x0, y0, n = R['rect']; key = M.acc_key(acc, wear, job); mm = R['acc'].get(key, {}) if key else {}
    sh, pop = mm.get('shift', 0), mm.get('pop', 0); c, info = M.pet_canvas(f, state, acc, wear, job, pattern_from); T = 40; yc = y0 - sh + T
    body = CN.px(c.crop((x0, yc, x0 + n, yc + n)), k); popim = None
    if pop:
        c0, _ = M.pet_canvas(f, state, None, None, None, pattern_from); a1 = np.array(c); a0 = np.array(c0)
        dm = (a1[..., 3] > 0) & ((a0[..., 3] == 0) | (np.abs(a1[..., :3].astype(int) - a0[..., :3]).sum(-1) > 0)); ac = a1.copy(); ac[~dm] = 0
        popim = CN.px(Image.fromarray(ac).crop((x0, yc - pop, x0 + n, yc + 2)), k)
    return body, popim, pop * k, n, mm.get('badge')
def portrait(bd, x, y, form='evo_still_tide', state='hungry', acc=None, wear=None, job=None, pattern_from=None, k=5, dim=False, badge=True, frame=True):
    """(x,y) = 框外角（portrait_frame 左上）；窗 = (x+6, y+6, d, d)"""
    body, popim, po, n, accb = face(form, state, acc, wear, job, pattern_from, k); d = n * k
    m = L.rr_mask(d, d, 30 * d / 110); L.drop_shadow(bd, m, x + 6, y + 6, 12, 8, .45)
    win = L._pbg(state, d); win.alpha_composite(body); win.alpha_composite(L.vgrad(d, d // 2, (255, 255, 255, 60), (255, 255, 255, 0)))
    if dim: win.alpha_composite(new(d, d, A(C['navy'], .5)))
    comp(bd, L.masked(win, m), x + 6, y + 6)
    if frame:
        fr = L._pframe(d + 12, d + 12) if d != L.PORT_D else P('portrait_frame'); comp(bd, fr, x, y)
    if popim is not None: comp(bd, popim, x + 6, y + 6 - po)
    if badge:
        bx, by = x + 6 + d - 12, y + 6 + d - 12; L.drop_shadow(bd, L.circ_mask(36), bx - 18, by - 18, 4, 2, .4); compc(bd, P(f'mood_badge_{state}'), bx, by); icon(bd, L.STATE_IC[state], bx, by)
    if accb:
        ax, ay = x + 6 + d - 10, y + 10; compc(bd, P('acc_badge'), ax, ay); icon(bd, f'acc_thumb_{M.acc_key(acc, wear, job)}', ax, ay)
    return d
def mini_face(bd, cx, cy, form, state='normal', k=3, acc=None, d=None, pattern_from=None):
    body, popim, po, n, _ = face(form, state, acc, pattern_from=pattern_from, k=k); dd = n * k
    m = L.circ_mask(dd); win = L._pbg(state, dd); win.alpha_composite(body); compc(bd, L.masked(win, m), cx, cy)
    if popim is not None: comp(bd, popim, cx - dd / 2, cy - dd / 2 - po)
# ---------------------------------------------------------------- 元件
def bar(bd, x, y, w, h, v, acc, low=False):
    hh = {5: 5, 6: 6, 8: 8}.get(h, 6); comp(bd, P(f'bar_track_h{hh}', w, hh), x, y); fw = max(hh, int(w * v)); c = 'red' if low else acc
    comp(bd, P(f'bar_fill_{c}_h{hh}', fw, hh), x, y); compc(bd, P(f'bar_tip_{c}'), x + fw - 1, y + hh / 2)
def button(bd, label, x, y, w, acc='pri', small=False, ic=None, pressed=False, name=None):
    h = 48 if small else 60; nm = f"btn{'_s' if small else ''}_{acc}{'_p' if pressed else ''}"; L.drop_shadow(bd, L.rr_mask(w, h, h / 2), x, y, 8, 5, .35); comp(bd, P(nm, w, h), x, y)
    col = C['ink'] if acc != 'dis' else C['cream']; tw_ = tw(label, 'button') + (40 if ic else 0); tx = x + w / 2 - tw_ / 2   # v3：彩色掣用深墨字（對比 ≥4.5）；灰掣用米白
    if ic: icon(bd, ic, tx + 16, y + h / 2); tx += 40
    text(bd, label, tx, y + h / 2, 'button', col, 'lm')
    reg(name or f'btn:{label}', x, y, w, h)
def round_act(bd, k, acc, cx, cy, label=None, glow=False, pressed=False, lab_col=None):
    if glow: compc(bd, P('act_glow'), cx, cy)
    L.drop_shadow(bd, L.circ_mask(78), cx - 39, cy - 39, 8, 5, .4); L.backdrop(bd, cx - 39, cy - 39, 78, 78, L.circ_mask(78)); compc(bd, P(f'act_{acc}{"_p" if pressed else ""}'), cx, cy)
    icon(bd, k, cx, cy, glow=True)
    if glow: compc(bd, P('diamond_hi'), cx, cy - 50)
    if label:
        w = max(80, tw(label, 'button') + 30); panel(bd, 'label_pill', cx - w / 2, cy + 46, w, 30, shadow=False); text(bd, label, cx, cy + 61, 'button', lab_col or C['cream'], 'mm')
    reg(f'act:{k}', cx - 39, cy - 39, 78, 78)
def rail_btn(bd, k, cx, cy, label=None, badge=None, dot=False):
    L.drop_shadow(bd, L.circ_mask(64), cx - 32, cy - 32, 8, 4, .35); L.backdrop(bd, cx - 32, cy - 32, 64, 64, L.circ_mask(64)); compc(bd, P('rail_btn'), cx, cy); icon(bd, k, cx, cy, glow=True)
    if label:
        w = max(60, tw(label, 'caption') + 24); panel(bd, 'label_pill', cx - w / 2, cy + 38, w, 28, shadow=False); text(bd, label, cx, cy + 52, 'caption', C['cream'], 'mm')
    if badge: compc(bd, P('red_dot_num'), cx + 24, cy - 22); text(bd, str(badge), cx + 24, cy - 23, 'label', (255, 255, 255), 'mm')
    if dot: compc(bd, P('red_dot'), cx + 22, cy - 22)
    reg(f'rail:{k}', cx - 32, cy - 32, 64, 64)
def close_btn(bd, cx, cy): compc(bd, P('close'), cx, cy); reg('close', cx - 22, cy - 22, 44, 44)
def title(bd, t, cx, y, w=300):
    text(bd, t, cx, y, 'title', C['cream'], 'mm', sh=(0, 0, 0)); comp(bd, P('title_rule', w, 12), cx - w / 2, y + 20)
def chip(bd, k, val, x, y, w=150, plus=True, name=None):
    panel(bd, 'chip', x, y, w, 38, shadow=False); icon(bd, k, x + 22, y + 19, glow=True); text(bd, str(val), x + w - (40 if plus else 16), y + 19, 'value', C['cream'], 'rm')
    if plus: compc(bd, P('chip_plus'), x + w - 20, y + 19); reg(name or f'chip:{k}', x, y, w, 38)
def bubble(bd, t, k, x, y):
    w = int(tw(t, 'body') + 64); L.drop_shadow(bd, L.rr_mask(w, 42, 21), x, y, 10, 6, .25); L.backdrop(bd, x, y, w, 42, L.rr_mask(w, 42, 21), 16); comp(bd, P('bubble', w, 42), x, y); comp(bd, P('bubble_tail'), x + 18, y + 40)
    icon(bd, k, x + 24, y + 21); text(bd, t, x + 44, y + 21, 'body', C['ink'], 'lm')
def medal_icon(bd, k, cx, cy, d=48, acc='navy', glow=True):
    L.drop_shadow(bd, L.circ_mask(d), cx - d / 2, cy - d / 2, 4, 3, .35); compc(bd, P(f'med{d}_{acc}'), cx, cy); icon(bd, k, cx, cy, glow=glow)
def sparkles(bd, pts):
    for (x, y, r) in pts: compc(bd, P(f'flare_{r}'), x, y)
def veil(bd, light=False): bd.alpha_composite(P('veil_light' if light else 'veil', W, H))
def home_indicator(bd): comp(bd, L.masked(new(140, 6, (255, 255, 255, 200)), L.rr_mask(140, 6, 3)), W / 2 - 70, 1252)
# ---------------------------------------------------------------- 場景快取
_SC = {}
def garden(state='hungry', pet_glow=1.0):
    k = ('g', state, pet_glow)
    if k not in _SC: _SC[k] = CN.garden3x('A', state, pet_glow)
    return _SC[k].copy()
def house(furn=None, pets=None, pet_glow=.6):
    k = ('h', furn, pets, pet_glow)
    if k not in _SC: _SC[k] = CN.house_scene3x(pet_glow, furn, pets) if furn else CN.house_scene3x(pet_glow, pets=pets)
    return _SC[k].copy()
def sheet_bg(): bd = house(pets=()); veil(bd); return bd

# ================================================================ layout（@3x px，設計 585×1266；唯一來源）
LAYOUT = {
 'design': [W, H], 'scale': 3, 'unit': '@3x px（÷3＝art px；CSS 360w ×0.615）', 'bands': L.BANDS,
 'gardenRatio': round((L.BANDS['garden'][1] - L.BANDS['garden'][0]) / H, 3),
 'scrimTop': {'part': 'scrim_top', 'y': 0, 'h': 200, 'goldRule': [160, 572, 128]},
 'portrait': {'frame': [20, 14, 122, 122], 'window': [26, 20, 110, 110], 'k': 5, 'popUp': True, 'badge': 'mood_badge_<state> 中心 (124,124)'},
 'nameplate': {'name': [166, 16], 'stageTag': 'name 右 12px，62×26', 'level': 'stageTag 右 12px', 'xp': [166, 64, 236, 5]},
 'needs': {'x': 166, 'y': 80, 'dx': 124, 'dy': 24, 'icon': 22, 'bar': [28, 8, 84, 6], 'order': ['feed', 'heart', 'clean', 'sleep'], 'low': '< 0.2 → bar_fill_red + bar_tip_red'},
 'chips': [{'icon': 'light', 'x': 418, 'y': 12, 'w': 150}, {'icon': 'star', 'x': 418, 'y': 56, 'w': 150}],
 'toast': {'x': 166, 'y': 150, 'w': 286, 'h': 42},
 'rail': {'cx': 538, 'cy0': 238, 'dy': 106, 'd': 64, 'labelH': 28, 'items': [['gift', '委託', 3], ['mail', '信', 'dot'], ['house', '屋仔', None], ['dex', '圖鑑', None], ['egg_kid', '細佬', 'dot'], ['walk', '散步', None]],
          'note': 'v3 rail 6 格：委託／信／屋仔／圖鑑／細佬／散步（walk 取代借用 expedition）'},
 'bubble': {'anchor': 'pet.headTop', 'dx': -18, 'dy': -24, 'h': 42},
 'acts': {'cy': 990, 'cx0': 92, 'dx': 134, 'd': 78, 'labelDy': 46, 'items': [['feed', 'pri', '餵食'], ['play_cat', 'rose', '玩耍'], ['clean', 'sec', '清潔'], ['sleep', 'violet', '瞓覺']], 'note': '行動掣浮喺花園底（唔佔 band）'},
 'dock': {'x': 12, 'y': 1108, 'w': 561, 'h': 116, 'tabs': [['heart_bunny', '照顧'], ['play_cat', '玩'], ['sprout', '小圃'], ['book_bear', '手帳'], ['gear_chick', '設定']]},
 'homeIndicator': [222, 1252, 140, 6],
 'popup': {'x': 36, 'w': 513, 'titleY': '+44', 'close': '右上 inset 30', 'veil': 'veil（navy 55%）'},
 'house4b': {'back': [46, 46, 56], 'title': [292.5, 46], 'chip': [418, 27, 150], 'bar': [12, 1110, 561, 126], 'acts': [['sleep', 'violet', '瞓覺'], ['play_cat', 'rose', '玩'], ['feed', 'pri', '餵食'], ['decorate', 'gold', '佈置']]},
 'petGlow': {'rule': 'Kurt：「除左佢訓就會關」— 寵物自己嘅光源同特效（rim glow、地面光圈、身邊光點、光暈 icon、飾品發光）喺瞓覺狀態全部關；醒返先亮。場景燈（燈泡、窗光、蘑菇燈）唔受影響。',
             'states': {'awake': 1.0, 'sleepy': 0.6, 'sleep': 0.0, 'sleepClip': 0.0, 'dreamEnter': 0.0, 'dreaming': 0.0},
             'fadeOut': {'ms': 600, 'ease': 'easeInQuad', 'from': 'current', 'to': 0, 'trigger': 'sleep clip 第 1 幀／夢遊入夢 transition_in 開始前'},
             'fadeIn': {'ms': 400, 'ease': 'easeOutQuad', 'from': 0, 'to': 1, 'trigger': '醒（wake clip 最後一幀）', 'pulse': {'ms': 150, 'scale': [1, 1.15, 1]}},
             'keyframes': [[0, 1.0], [600, 0.0], ['wake', 0.0], ['wake+400', 1.0], ['wake+475', 1.15], ['wake+550', 1.0]],
             'engine': 'petGlow ∈ [0,1] 乘落所有 *_glow 層同寵物粒子 alpha；sprite 本體唔變'},
}
def hud_top(bd, form='evo_still_tide', state='hungry', acc='bow', name='團絨', stage='靜光', lv='Lv.12', xp=.62, needs=(.22, .6, .55, .15), chips=True):
    bd.alpha_composite(P('scrim_top', W, 200)); comp(bd, L.hline_im(412, A(C['gold'], .9), 1.5), 160, 126); compc(bd, P('diamond'), 572, 128)
    portrait(bd, 20, 14, form, state, acc); reg('portrait', 20, 14, 122, 122)
    text(bd, name, 166, 16, 'title', C['cream'], sh=(0, 0, 0)); tx = 166 + tw(name, 'title') + 12
    comp(bd, P('stage_tag', 62, 26), tx, 24); text(bd, stage, tx + 31, 37, 'caption', C['goldhi'], 'mm'); text(bd, lv, tx + 74, 37, 'caption', C['mute'], 'lm')
    bar(bd, 166, 64, 236, 5, xp, 'gold')
    for t in (.33, .66): compc(bd, P('exp_gem_on' if xp > t else 'exp_gem_off'), 166 + 236 * t, 66.5)
    for i, (k, c, v) in enumerate(zip(LAYOUT['needs']['order'], ('amber', 'rose', 'sky', 'violet'), needs)):
        x = 166 + (i % 2) * 124; y = 80 + (i // 2) * 24; icon(bd, 'mini_' + k, x + 11, y + 11); bar(bd, x + 28, y + 8, 84, 6, v, c, low=v < .2)
    if chips:
        for c in LAYOUT['chips']: chip(bd, c['icon'], 140 if c['icon'] == 'light' else 10, c['x'], c['y'], c['w'])
def hud_toast(bd, t='收到小禮物', v='+5'):
    T = LAYOUT['toast']; panel(bd, 'toast', T['x'], T['y'], T['w'], T['h']); icon(bd, 'mini_star', T['x'] + 26, T['y'] + 21, glow=True)
    text(bd, t, T['x'] + 48, T['y'] + 21, 'body', C['cream'], 'lm'); text(bd, v, T['x'] + T['w'] - 16, T['y'] + 21, 'value', C['goldhi'], 'rm')
def hud_rail(bd, n=6):
    R = LAYOUT['rail']
    for i, (k, lb, b) in enumerate(R['items'][:n]): rail_btn(bd, k, R['cx'], R['cy0'] + i * R['dy'], lb, b if isinstance(b, int) else None, b == 'dot')
def hud_acts(bd, glow_i=0):
    Aa = LAYOUT['acts']
    for i, (k, acc, lb) in enumerate(Aa['items']): round_act(bd, k, acc, Aa['cx0'] + i * Aa['dx'], Aa['cy'], lb, glow=i == glow_i)
def hud_dock(bd, active=0, dot=3):
    D = LAYOUT['dock']; bd.alpha_composite(P('scrim_bottom', W, 150), (0, H - 150)); panel(bd, 'dock', D['x'], D['y'], D['w'], D['h']); tw_ = D['w'] / 5
    for i, (k, lb) in enumerate(D['tabs']):
        cx = D['x'] + tw_ * (i + .5); on = i == active
        if on: compc(bd, P('dock_on'), cx, D['y'] + 58); compc(bd, P('diamond_hi'), cx, D['y'] + 4)
        icon(bd, k, cx, D['y'] + 44, glow=on); text(bd, lb, cx, D['y'] + 88, 'caption', C['goldhi'] if on else C['mute'], 'mm', kind='sansb' if on else None)
        if dot is not None and i == dot and not on: compc(bd, P('red_dot'), cx + 22, D['y'] + 24)
        reg(f'dock:{k}', D['x'] + tw_ * i, D['y'], tw_, D['h'])
    home_indicator(bd)

# ================================================================ 畫面
def s_home():
    bd = garden('hungry'); hud_top(bd); hud_toast(bd); hud_rail(bd); bubble(bd, '肚仔餓…', 'mini_feed', 280, 676); hud_acts(bd); hud_dock(bd, 0)
    return bd
def popup_base(bd, y, h, t, close=True, x=36, w=513):
    veil(bd); panel(bd, 'panel', x, y, w, h, sh_a=.5); title(bd, t, W / 2, y + 44)
    if close: close_btn(bd, x + w - 34, y + 34)
    return x, y, w
def s_popup():
    bd = s_home(); x, y, w = popup_base(bd, 330, 560, '收到小禮物')
    text(bd, '鄰居松鼠送咗嘢俾團絨！', W / 2, y + 104, 'body', C['cream'], 'mm')
    for i, (k, acc, v) in enumerate((('light', 'sec', '×30'), ('star', 'pri', '×2'), ('furniture', 'rose', '×1'))):
        cx = x + 96 + i * 160; panel(bd, 'card', cx - 66, y + 140, 132, 160); compc(bd, P('glow_48'), cx, y + 196); medal_icon(bd, k, cx, y + 196, 60, acc)
        text(bd, v, cx, y + 268, 'value', C['goldhi'], 'mm')
        if i == 2: comp(bd, P('pill_rose', 52, 30), cx + 26, y + 128); text(bd, '新', cx + 52, y + 143, 'label', C['ink'], 'mm')
    sparkles(bd, ((x + 40, y + 140, 20), (x + w - 34, y + 300, 12), (x + w - 70, y + 120, 12)))
    comp(bd, P('panel_inset', w - 48, 72), x + 24, y + 326); medal_icon(bd, 'mini_mail', x + 62, y + 362, 36, 'gold', glow=False)
    text(bd, '附上一封信：「多謝你嘅花！」', x + 94, y + 362, 'body', C['cream'], 'lm')
    button(bd, '睇信', x + 24, y + 444, 200, 'sec', ic='mail'); button(bd, '收下', x + w - 24 - 230, y + 444, 230, 'pri', ic='check')
    compc(bd, P('hint_arrow'), x + w - 24 - 115, y + 424)
    return bd
def s_levelup():
    bd = garden('happy'); veil(bd); compc(bd, P('fx_rays'), W / 2, 430); compc(bd, P('glow_80'), W / 2, 430)
    compc(bd, P('family_crest'), W / 2, 430); text(bd, 'Lv', W / 2, 408, 'label', C['golddk'], 'mm'); text(bd, '5', W / 2, 440, 'title', C['golddk'], 'mm')
    compc(bd, L.glow_im(150, C['navy'], .75).resize((420, 160)), W / 2, 272); title(bd, '升級喇！', W / 2, 270)
    portrait(bd, W / 2 - 61, 520, 'evo_still_tide', 'happy', 'crown')
    text(bd, '團絨 Lv4 → Lv5', W / 2, 682, 'h2', C['cream'], 'mm', sh=(0, 0, 0))
    for i in range(3): compc(bd, P('star_on'), W / 2 - 40 + i * 40, 724)
    x, y, w = 60, 760, 465; panel(bd, 'panel_flat', x, y, w, 196); text(bd, '新解鎖', x + 28, y + 30, 'h2', C['goldhi'], 'lm')
    for i, (k, t) in enumerate((('decorate', '新家具'), ('mg_firefly', '螢火蟲遊戲'), ('gift', '委託 +1'))):
        cx = x + 82 + i * 150; medal_icon(bd, k, cx, y + 100, 60, 'navy'); text(bd, t, cx, y + 156, 'caption', C['cream'], 'mm')
    button(bd, '好嘢！', W / 2 - 130, 990, 260, 'pri', ic='star')
    sparkles(bd, ((110, 330, 34), (470, 370, 34), (160, 560, 20), (430, 600, 20), (80, 740, 12), (510, 720, 12)))
    return bd
def s_settings():
    bd = garden('normal'); hud_top(bd, state='normal', acc=None, needs=(.7, .8, .6, .5)); veil(bd, True); hud_dock(bd, 4, None)
    x, y, w, h = 24, 196, 537, 880; panel(bd, 'panel', x, y, w, h); title(bd, '設定', W / 2, y + 44); close_btn(bd, x + w - 34, y + 34)
    rows = [('sound', '音樂', ('slider', .7)), ('sound', '音效', ('slider', .45)), ('bond', '震動', ('toggle', True)), ('bedtime', '瞓覺提醒', ('toggle', False)),
            ('info', '語言', ('seg', ['繁中', 'English'], 0)), ('quality', '畫質', ('seg', ['省電', '標準', '靚'], 1))]
    yy = y + 100
    for k, t, ctl in rows:
        comp(bd, P('panel_inset', w - 40, 80), x + 20, yy); medal_icon(bd, k, x + 64, yy + 40, 48, 'navy'); text(bd, t, x + 104, yy + 40, 'body', C['cream'], 'lm')
        if ctl[0] == 'slider':
            sw = 200; sx = x + w - 52 - sw; comp(bd, P('slider_track', sw, 8), sx, yy + 36); fw = int(sw * ctl[1]); comp(bd, P('bar_fill_sky_h8', fw, 8), sx, yy + 36); compc(bd, P('slider_knob'), sx + fw, yy + 40)
            reg(f'slider:{t}', sx, yy + 10, sw, 60)
        elif ctl[0] == 'toggle':
            on = ctl[1]; tx = x + w - 104; comp(bd, P(f'toggle_track_{"on" if on else "off"}'), tx, yy + 23); compc(bd, P('toggle_knob'), tx + (47 if on else 17), yy + 40)
            text(bd, '開' if on else '關', tx - 14, yy + 40, 'caption', C['goldhi'] if on else C['mute'], 'rm'); reg(f'toggle:{t}', tx, yy + 23, 64, 34)
        else:
            opts, sel = ctl[1], ctl[2]; ow = [tw(o, 'label') + 34 for o in opts]; sw = sum(ow) + 6; sx = x + w - 40 - sw
            comp(bd, P('seg_bg', sw, 44), sx, yy + 18); cx = sx + 3
            for i, o in enumerate(opts):
                if i == sel: comp(bd, P('seg_on', ow[i], 38), cx, yy + 21)
                text(bd, o, cx + ow[i] / 2, yy + 40, 'label', C['ink'] if i == sel else C['mute'], 'mm'); reg(f'seg:{t}:{o}', cx, yy + 18, ow[i], 44); cx += ow[i]
        yy += 92
    comp(bd, P('divider', w - 80, 6), x + 40, yy + 4)
    for i, (t, f, k) in enumerate((('存檔', 'sec', 'check'), ('通知', 'violet', 'mail'), ('重置', 'rose', 'reset'))):
        button(bd, t, x + 28 + i * 164, yy + 30, 152, f, True, ic=k)
    text(bd, '字型：Noto Sans／Serif CJK TC（OFL 1.1）', W / 2, y + h - 74, 'caption', C['mute'], 'mm'); text(bd, '版本 v0.6.0', W / 2, y + h - 44, 'caption', C['mute'], 'mm')
    return bd
DEX = ['sprout', 'radiant', 'soft', 'lumi', 'evo_hop', 'evo_guard_tide', 'evo_still_moon', 'A1', 'B2', 'C3', 'D1', 'S1', 'S4C', None, None, None]
DEXZH = {'sprout': '芽仔', 'radiant': '光光', 'soft': '軟軟', 'lumi': '螢螢', 'evo_hop': '跳跳', 'evo_guard_tide': '潮守', 'evo_still_moon': '月靜', 'A1': '團A1', 'B2': '團B2', 'C3': '團C3', 'D1': '團D1', 'S1': '細佬', 'S4C': '火仔'}
def s_journal():
    bd = garden('normal'); veil(bd, True); hud_dock(bd, 3, None)
    x, y, w, h = 18, 40, 549, 1050; panel(bd, 'panel', x, y, w, h); title(bd, '手帳', W / 2, y + 44); close_btn(bd, x + w - 34, y + 34)
    tx = x + 28
    for i, t in enumerate(['圖鑑', '日記', '成就', '家族']):
        tw_ = tw(t, 'button') + 44; comp(bd, P('subtab_on' if i == 0 else 'subtab', tw_, 44), tx, y + 92); text(bd, t, tx + tw_ / 2, y + 114, 'button', C['goldhi'] if i == 0 else C['mute'], 'mm'); reg(f'tab:{t}', tx, y + 92, tw_, 44); tx += tw_ + 10
    compc(bd, P('red_dot'), tx - 16, y + 94)
    text(bd, '已收集 13／48', x + 28, y + 172, 'body', C['goldhi'], 'lm'); bar(bd, x + w - 248, y + 169, 220, 6, 13 / 48, 'amber')
    cw, ch = 117, 150
    for i, f in enumerate(DEX):
        cx = x + 26 + (i % 4) * (cw + 8); cy = y + 206 + (i // 4) * (ch + 10)
        if f:
            panel(bd, 'card_sel' if i == 6 else 'card', cx, cy, cw, ch, sh_a=.25)
            p, info = X.compose_pet(f, 'normal'); ex, ey = info['eyes']; cr = CN.px(p.crop((int(ex - 16), int(ey - 20), int(ex + 16), int(ey + 12))), 3)
            comp(bd, cr, cx + cw / 2 - 48, cy + 6); text(bd, DEXZH[f], cx + cw / 2, cy + ch - 24, 'caption', C['cream'], 'mm')
            if i == 6: comp(bd, P('pill_rose', 52, 30), cx + cw - 46, cy - 10); text(bd, '新', cx + cw - 20, cy + 5, 'label', C['ink'], 'mm')
        else:
            panel(bd, 'card_locked', cx, cy, cw, ch, sh_a=.2); icon(bd, 'lock', cx + cw / 2, cy + 60); text(bd, '？？？', cx + cw / 2, cy + ch - 24, 'caption', C['mute'], 'mm')
        reg(f'dex:{i}', cx, cy, cw, ch)
    by = y + 206 + 4 * (ch + 10) + 4; comp(bd, P('panel_paper', w - 52, 190), x + 26, by)
    text(bd, '月靜（靜光・月）', x + 54, by + 40, 'h2', C['ink'], 'lm'); text(bd, '夜晚會喺窗邊發出淡淡月光，', x + 54, by + 92, 'body', C['ink'], 'lm'); text(bd, '最鍾意聽故事。', x + 54, by + 128, 'body', C['ink'], 'lm')
    compc(bd, P('stamp_done'), x + w - 86, by + 70)
    return bd
def house_hud(bd, t='團絨嘅屋仔', deco=True):
    bd.alpha_composite(P('scrim_top', W, 200).crop((0, 0, W, 170)))
    L.backdrop(bd, 18, 18, 56, 56, L.circ_mask(56)); compc(bd, P('back_btn'), 46, 46); icon(bd, 'back', 46, 46); reg('back', 18, 18, 56, 56)
    title(bd, t, W / 2, 46); chip(bd, 'star', 36, 418, 27, 150)
def s_house():
    bd = house(); house_hud(bd); portrait(bd, 16, 102, 'evo_still_tide', 'sleepy', 'nightcap'); bubble(bd, '好攰呀…', 'mini_sleep', 302, 744)
    panel(bd, 'dock', 12, 1104, W - 24, 126)
    for i, (k, c, lb) in enumerate(LAYOUT['house4b']['acts']):
        cx = 12 + (W - 24) / 4 * (i + .5); cy = 1152
        if i == 0: compc(bd, P('act_glow'), cx, cy)
        compc(bd, P(f'act_{c}'), cx, cy); icon(bd, k, cx, cy, glow=True); text(bd, lb, cx, 1208, 'caption', C['goldhi'] if i == 0 else C['cream'], 'mm', kind='sansb' if i == 0 else None); reg(f'act:{k}', cx - 39, cy - 39, 78, 78)
    home_indicator(bd)
    return bd
def s_house_deco():
    furn = ('bed_cloud', 'table_round', 'rug_leaf', 'wall_frame', 'win_star', 'lamp_firefly')
    bd = house(furn=furn, pets=()); house_hud(bd, '佈置屋仔')
    sx, sy, sw, sh = 12, 780, 561, 474; panel(bd, 'panel', sx, sy, sw, sh + 30); compc(bd, P('sheet_handle'), W / 2, sy + 16)
    for i, (k, t) in enumerate((('furniture', '床'), ('light', '燈'), ('cabinet', '檯'), ('decorate', '牆'), ('house', '窗'), ('star', '地氈'))):
        cx = sx + 52 + i * 91; on = i == 0; medal_icon(bd, k, cx, sy + 72, 60 if on else 48, 'pri' if on else 'navy', glow=on); text(bd, t, cx, sy + 124, 'caption', C['goldhi'] if on else C['mute'], 'mm'); reg(f'cat:{t}', cx - 30, sy + 42, 60, 96)
    cw, ch = 160, 212
    for i, (nm, st, price) in enumerate((('bed_leaf', 'own', '已擁有'), ('bed_cloud', 'sel', '使用中'), (None, 'lock', '40'))):
        cx = sx + 22 + i * (cw + 18); cy = sy + 150; panel(bd, {'sel': 'card_sel', 'lock': 'card_locked'}.get(st, 'card'), cx, cy, cw, ch, sh_a=.25)
        if nm:
            im = Image.open(f'{L.ART}/sprites/series2_house/{M.HJ["furniture"][nm]["png"]}').convert('RGBA'); compc(bd, P('glow_48'), cx + cw / 2, cy + 64); compc(bd, im, cx + cw / 2, cy + 64)
            text(bd, M.HJ['furniture'][nm]['zh'], cx + cw / 2, cy + 128, 'caption', C['cream'], 'mm')
        else: icon(bd, 'lock', cx + cw / 2, cy + 64); text(bd, '星星床', cx + cw / 2, cy + 128, 'caption', C['mute'], 'mm')
        pw = 116; acc = {'sel': 'sec', 'lock': 'pri'}.get(st, 'navy'); comp(bd, P(f'pill_{acc}', pw, 34), cx + cw / 2 - pw / 2, cy + 156)
        if st == 'lock': icon(bd, 'mini_star', cx + cw / 2 - 26, cy + 173)
        text(bd, price, cx + cw / 2 + (10 if st == 'lock' else 0), cy + 173, 'label', C['cream'] if st == 'own' else C['ink'], 'mm'); reg(f'furn:{i}', cx, cy, cw, ch)
    button(bd, '完成', W / 2 - 110, sy + 384, 220, 'pri', ic='check')
    home_indicator(bd)
    return bd
FAM = [('evo_still_tide', '團絨', '靜光', 'Lv8'), ('A3', '波波', '成年', 'Lv5'), ('S4C', '火仔', '少年', 'Lv3'), ('S1', '豆豆', '幼年', 'Lv1'), ('B1', '咩咩', '蛋', '—')]
def s_family_tree():
    bd = sheet_bg(); x, y, w, h = 18, 40, 549, 1180; panel(bd, 'panel', x, y, w, h); title(bd, '家族樹', W / 2, y + 44); close_btn(bd, x + w - 34, y + 34)
    compc(bd, P('family_crest'), x + 94, y + 170); text(bd, 'Lv', x + 94, y + 150, 'label', C['golddk'], 'mm'); text(bd, '6', x + 94, y + 180, 'title', C['golddk'], 'mm')
    text(bd, '家族等級', x + 176, y + 122, 'h2', C['goldhi'], 'lm'); bar(bd, x + 176, y + 152, 320, 8, .58, 'gold'); text(bd, '58／100 XP', x + 176, y + 188, 'caption', C['mute'], 'lm')
    text(bd, '家族 Lv7 解鎖 Lv6 工作', x + 176, y + 222, 'caption', (206, 196, 255), 'lm')
    nodes = [(W / 2, y + 330, 0), (W / 2 - 140, y + 590, 1), (W / 2 + 140, y + 590, 2), (W / 2 - 140, y + 850, 3), (W / 2 + 140, y + 850, 4)]
    for (ax, ay), (bx, by) in (((W / 2, y + 430), (W / 2 - 140, y + 520)), ((W / 2, y + 430), (W / 2 + 140, y + 520)), ((W / 2 - 140, y + 690), (W / 2 - 140, y + 780)), ((W / 2 + 140, y + 690), (W / 2 + 140, y + 780))):
        my = (ay + by) / 2; comp(bd, P('tree_line_v', 4, int(my - ay)), ax - 2, ay); comp(bd, P('tree_line_h', int(abs(bx - ax)) + 4, 4), min(ax, bx) - 2, my - 2); comp(bd, P('tree_line_v', 4, int(by - my)), bx - 2, my); compc(bd, P('tree_joint'), ax, my)
    for (cx, cy, i) in nodes:
        f, nm, st, lv = FAM[i]; nd = 'tree_node_gold' if i == 0 else ('tree_node_sel' if i == 2 else 'tree_node'); compc(bd, P(nd), cx, cy - 22)
        if f != 'B1': mini_face(bd, cx, cy - 22, f, 'happy' if i == 0 else 'normal', 3, 'crown' if i == 0 else None)
        else: icon(bd, 'egg_tr', cx, cy - 22, glow=True, scale=2)
        text(bd, nm, cx - 6, cy + 46, 'body', C['cream'], 'rm'); tw_ = tw(st, 'caption') + 24; comp(bd, P('stage_tag', tw_, 26), cx + 4, cy + 33); text(bd, st, cx + 4 + tw_ / 2, cy + 46, 'caption', C['goldhi'], 'mm')
        text(bd, lv, cx, cy + 80, 'caption', C['mute'], 'mm'); reg(f'node:{i}', cx - 48, cy - 70, 96, 96)
    yy = y + 1000
    for i, (k, t, n) in enumerate((('pets', '成員', '5／6'), ('egg_tr', '蛋', '1'), ('inherit', '傳承', '2'))):
        cx = x + 80 + i * 170; medal_icon(bd, k, cx, yy, 48); text(bd, t, cx + 36, yy - 14, 'caption', C['cream'], 'lm'); text(bd, n, cx + 36, yy + 14, 'value', C['goldhi'], 'lm')
    button(bd, '孵新蛋', W / 2 - 140, y + h - 90, 280, 'pri', ic='plus')
    return bd
def s_egg_choice():
    bd = sheet_bg(); x, y, w = popup_base(bd, 250, 690, '揀一隻蛋')
    text(bd, '家族 Lv6：可以孵第 5 隻', W / 2, y + 104, 'body', C['mute'], 'mm')
    for i, (k, t, d, sel) in enumerate((('egg_tr', '團絨蛋', '會進化做靜光', True), ('egg_kid', '細佬蛋', '花紋跟父母', False))):
        cx = x + 134 + i * 246; cw, ch = 216, 336; cy = y + 140; panel(bd, 'egg_card' if sel else 'card', cx - cw / 2, cy, cw, ch)
        compc(bd, P('fx_ripple'), cx, cy + 104); compc(bd, P('glow_48'), cx, cy + 104); icon(bd, k, cx, cy + 104, glow=True, scale=2)
        text(bd, t, cx, cy + 196, 'h2', C['cream'], 'mm'); text(bd, d, cx, cy + 236, 'caption', C['mute'], 'mm')
        pw = 140; comp(bd, P('pill_pri' if sel else 'pill_navy', pw, 40), cx - pw / 2, cy + 270); text(bd, '揀呢隻' if sel else '揀', cx, cy + 290, 'label', C['ink'] if sel else C['cream'], 'mm'); reg(f'egg:{i}', cx - cw / 2, cy, cw, ch)
        if sel: compc(bd, P('check_on'), cx + cw / 2 - 26, cy + 26)
    sparkles(bd, ((x + 40, y + 160, 20), (x + w - 40, y + 400, 12)))
    button(bd, '孵化！', W / 2 - 130, y + 520, 260, 'pri', ic='sprout'); text(bd, '孵化要 3 日', W / 2, y + 618, 'caption', C['mute'], 'mm')
    return bd
def s_pet_card():
    bd = sheet_bg(); x, y, w = popup_base(bd, 200, 850, '寵物卡')
    portrait(bd, x + 24, y + 96, 'A3', 'happy', wear='hat')
    text(bd, '波波', x + 172, y + 120, 'title', C['cream']); tx = x + 172 + tw('波波', 'title') + 12; comp(bd, P('stage_tag', 62, 26), tx, y + 128); text(bd, '成年', tx + 31, y + 141, 'caption', C['goldhi'], 'mm')
    comp(bd, P('pill_pri', 92, 32), x + 172, y + 176); icon(bd, 'mini_star', x + 192, y + 192); text(bd, '主養', x + 210, y + 192, 'label', C['ink'], 'lm'); text(bd, '團絨線・A 系', x + 280, y + 192, 'caption', C['mute'], 'lm')
    bar(bd, x + 172, y + 236, 230, 6, .7, 'sky'); text(bd, 'Lv5', x + w - 34, y + 239, 'value', C['goldhi'], 'rm')
    yy = y + 270
    for k, t, v, f in (('feed', '肚餓', .8, 'amber'), ('heart', '開心', .9, 'rose'), ('clean', '乾淨', .4, 'sky'), ('sleep', '精神', .6, 'violet')):
        comp(bd, P('panel_inset', w - 48, 66), x + 24, yy); medal_icon(bd, 'mini_' + k, x + 60, yy + 33, 36, 'gold', glow=False); text(bd, t, x + 92, yy + 33, 'body', C['cream'], 'lm')
        bar(bd, x + 190, yy + 30, 220, 6, v, f); text(bd, f'{int(v * 100)}', x + w - 44, yy + 33, 'value', C['goldhi'], 'rm'); yy += 76
    comp(bd, P('divider', w - 80, 6), x + 40, yy + 6)
    for i, (k, t) in enumerate((('pattern', '花紋'), ('trick', '把戲'), ('family_tree', '族譜'))):
        cx = x + 100 + i * 156; medal_icon(bd, k, cx, yy + 70, 60); text(bd, t, cx, yy + 124, 'caption', C['cream'], 'mm'); reg(f'pc:{t}', cx - 33, yy + 37, 66, 104)
    button(bd, '設為主養', x + 24, yy + 166, 280, 'sec', ic='check'); button(bd, '放生', x + w - 24 - 170, yy + 166, 170, 'dis')
    return bd
PLAN = [('evo_still_tide', '團絨', 'exp', '遠足中…返嚟 18:00', None), ('A3', '波波', 'job', '園丁 Lv3・+3 碎', 'garden'), ('A2', '咩咩', 'rest', '休息：精神 +20', None), ('S5B', '細佬', 'job', '廚師 Lv1・+1 碎', 'chef')]
def s_daily_plan():
    bd = sheet_bg(); x, y, w, h = 18, 40, 549, 1180; panel(bd, 'panel', x, y, w, h); title(bd, '今日安排', W / 2, y + 44); close_btn(bd, x + w - 34, y + 34)
    chip(bd, 'expedition', '遠足 1/2', x + 28, y + 92, 200, False); chip(bd, 'shards', '碎 4/12', x + 244, y + 92, 180, False)
    yy = y + 152
    for f, nm, mode, st, job in PLAN:
        comp(bd, P('panel_inset_sel' if mode == 'exp' else 'panel_inset', w - 40, 228), x + 20, yy)
        portrait(bd, x + 30, yy + 18, f, 'normal', job=job, k=4, dim=mode == 'exp', badge=False)
        if mode == 'exp': medal_icon(bd, 'expedition', x + 128, yy + 40, 48, 'violet')
        if job: compc(bd, P('job_lv_badge'), x + 118, yy + 110); text(bd, '3' if job == 'garden' else '1', x + 118, yy + 110, 'label', C['golddk'], 'mm')
        text(bd, nm, x + 168, yy + 46, 'h2', C['cream'], 'lm'); text(bd, st, x + 168, yy + 86, 'caption', C['mute'], 'lm')
        sx = x + 168; sw = w - 40 - 168 + 10; comp(bd, P('seg_bg', sw, 52), sx, yy + 128); ow = (sw - 6) / 3
        for i, (k, t, key) in enumerate((('expedition', '遠足', 'exp'), ('job_chef', '工作', 'job'), ('rest', '休息', 'rest'))):
            cx = sx + 3 + i * ow; on = key == mode; locked = key == 'exp' and nm == '細佬'
            if on: comp(bd, P('seg_on', int(ow), 46), cx, yy + 131)
            elif locked: comp(bd, P('seg_locked', int(ow), 46), cx, yy + 131)
            text(bd, t, cx + ow / 2 + (10 if locked else 0), yy + 154, 'label', C['ink'] if on else C['mute'], 'mm')
            if locked: icon(bd, 'mini_lock', cx + ow / 2 - 30, yy + 154)
            reg(f'plan:{nm}:{t}', cx, yy + 128, ow, 52)
        yy += 244
    text(bd, '遠足每日最多 2 次・細佬未成年唔去得', W / 2, yy + 20, 'caption', C['mute'], 'mm')
    return bd
JOBS = [('job_chef', '廚師', 1, .2, '+1 碎'), ('mail', '郵差助手', 2, .6, '+2 碎'), ('sprout', '園丁', 3, .4, '+3 碎'), ('bedtime', '守夜', 5, 1, '+5 碎')]
def s_job_picker():
    bd = sheet_bg(); x, y, w = popup_base(bd, 150, 980, '揀工作')
    portrait(bd, x + 24, y + 90, 'A3', 'normal', job='garden', badge=False); text(bd, '波波 想做咩？', x + 172, y + 128, 'h2', C['cream'], 'lm'); text(bd, '每 5 日升 1 級', x + 172, y + 170, 'caption', C['mute'], 'lm')
    cw, ch = 220, 270
    for i, (k, t, lv, v, out) in enumerate(JOBS):
        cx = x + 26 + (i % 2) * (cw + 21); cy = y + 250 + (i // 2) * (ch + 20); sel = i == 2; panel(bd, 'card_sel' if sel else 'card', cx, cy, cw, ch, sh_a=.25)
        medal_icon(bd, k, cx + 60, cy + 64, 60, 'pri' if sel else 'navy', glow=sel); compc(bd, P('job_lv_badge'), cx + 90, cy + 92); text(bd, str(lv), cx + 90, cy + 92, 'label', C['golddk'], 'mm')
        text(bd, t, cx + 112, cy + 64, 'body', C['cream'], 'lm'); bar(bd, cx + 22, cy + 142, cw - 44, 6, v, 'gold' if lv >= 5 else 'amber')
        text(bd, '封頂' if lv >= 5 else f'Lv{lv}→{lv + 1}', cx + cw / 2, cy + 180, 'caption', C['goldhi'] if lv >= 5 else C['mute'], 'mm'); text(bd, f'每日 {out}', cx + cw / 2, cy + 226, 'body', C['cream'], 'mm')
        if sel: compc(bd, P('check_on'), cx + cw - 24, cy + 24)
        reg(f'job:{t}', cx, cy, cw, ch)
    button(bd, '確認', W / 2 - 130, y + 856, 260, 'pri', ic='check')
    return bd
PZH = {'wave': '波紋', 'crescent': '月牙', 'spot': '斑點', 'diamond': '菱格', 'spark': '火花', 'stripe': '條紋', 'star': '星星', 'leaf': '葉紋', 'dot': '點點', 'heart': '心心'}
PARENTS = [('evo_still_tide', '團絨'), ('A3', '波波'), ('evo_still_moon', '月靜'), ('C3', '咕咕'), ('evo_still_ember', '火火'), (None, '？')]
def s_parent_pick():
    bd = sheet_bg(); x, y, w, h = 18, 40, 549, 1180; panel(bd, 'panel', x, y, w, h); title(bd, '揀爸爸媽媽', W / 2, y + 44); close_btn(bd, x + w - 34, y + 34)
    text(bd, '揀 2 隻成年：細佬會傳承花紋', W / 2, y + 104, 'body', C['mute'], 'mm')
    L5C = X.L5C['parents']; pk = list(L5C.keys()); cw, ch = 236, 236
    for i, (f, nm) in enumerate(PARENTS):
        cx = x + 26 + (i % 2) * (cw + 25); cy = y + 140 + (i // 2) * (ch + 16); sel = i in (0, 3); panel(bd, 'card_sel' if sel else ('card_locked' if not f else 'card'), cx, cy, cw, ch, sh_a=.25)
        if f:
            mini_face(bd, cx + cw / 2, cy + 80, f, 'happy' if sel else 'normal', 5)
            text(bd, nm, cx + cw / 2, cy + 168, 'body', C['cream'], 'mm'); pp = L5C[pk[i % len(pk)]]
            sw = new(22, 22); sw.alpha_composite(L.masked(L.vgrad(22, 22, A(CN.K.hx(pp['tint']['hi'])), A(CN.K.hx(pp['tint']['lo']))), L.rr_mask(22, 22, 6))); tx = cx + cw / 2 - (tw(PZH.get(pp['pattern'], pp['pattern']), 'caption') + 34) / 2
            comp(bd, sw, tx + 2, cy + 196); comp(bd, P('swatch_frame'), tx - 0, cy + 194); text(bd, PZH.get(pp['pattern'], pp['pattern']), tx + 34, cy + 207, 'caption', C['mute'], 'lm')
            if sel: compc(bd, P('check_on'), cx + cw - 26, cy + 26)
        else: icon(bd, 'lock', cx + cw / 2, cy + 90); text(bd, '未成年', cx + cw / 2, cy + 168, 'caption', C['mute'], 'mm')
        reg(f'parent:{i}', cx, cy, cw, ch)
    yy = y + 920; comp(bd, P('panel_inset_sel', w - 40, 130), x + 20, yy); medal_icon(bd, 'inherit', x + 70, yy + 65, 60, 'violet')
    text(bd, '傳承：花紋 50％・顏色 50％', x + 118, yy + 38, 'body', C['cream'], 'lm')
    comp(bd, P('pill_fast_on', 130, 44), x + 118, yy + 68); text(bd, '快 ×2', x + 183, yy + 90, 'label', C['ink'], 'mm'); reg('fast2', x + 118, yy + 68, 130, 44)
    comp(bd, P('pill_fast_locked', 130, 44), x + 262, yy + 68); text(bd, '快 ×3', x + 312, yy + 90, 'label', C['mute'], 'mm'); icon(bd, 'mini_lock', x + 362, yy + 90)
    button(bd, '孵細佬蛋', W / 2 - 150, y + h - 110, 300, 'pri', ic='plus')
    return bd
def s_inherit():
    bd = sheet_bg(); x, y, w = popup_base(bd, 200, 830, '傳承結果', close=False)
    for i, f in enumerate(('evo_still_tide', 'C3')): mini_face(bd, x + 96 + i * (w - 192), y + 150, f, 'normal', 3)
    comp(bd, P('tree_line_h', w - 270, 4), x + 135, y + 148); compc(bd, P('tree_joint'), W / 2, y + 150)
    text(bd, '爸爸', x + 96, y + 210, 'caption', C['mute'], 'mm'); text(bd, '媽媽', x + w - 96, y + 210, 'caption', C['mute'], 'mm')
    compc(bd, P('fx_ripple'), W / 2, y + 320); compc(bd, P('glow_80'), W / 2, y + 320); portrait(bd, W / 2 - 61, y + 250, 'S4C', 'happy', pattern_from='evo_still_tide')
    sparkles(bd, ((W / 2 - 110, y + 260, 20), (W / 2 + 104, y + 380, 12), (W / 2 + 96, y + 250, 12)))
    text(bd, '細佬「火仔」出世喇！', W / 2, y + 420, 'h2', C['goldhi'], 'mm', sh=(0, 0, 0))
    for i, (k, t, v) in enumerate((('pattern', '花紋', '波紋（爸爸）'), ('d_spark', '顏色', '火橙（媽媽）'))):
        yy = y + 466 + i * 86; comp(bd, P('panel_inset', w - 48, 74), x + 24, yy); icon(bd, k, x + 62, yy + 37, glow=True); text(bd, t, x + 94, yy + 37, 'body', C['cream'], 'lm'); text(bd, v, x + w - 46, yy + 37, 'body', C['goldhi'], 'rm')
    button(bd, '好！', W / 2 - 120, y + 690, 240, 'pri', ic='heart')
    return bd
# ---- 6b／6c／6d
def s_walk():
    bd = garden('normal'); hud_top(bd, state='normal', acc=None, needs=(.7, .8, .6, .5)); veil(bd, True)
    x, y, w, h = 36, 170, 513, 900; panel(bd, 'panel', x, y, w, h); title(bd, '散步', W / 2, y + 44); close_btn(bd, x + w - 34, y + 34)
    wb = Image.open(f'{BT}/6b/walk_bg@3x.png').convert('RGBA'); wx, wy = W / 2 - 150, y + 96
    a = np.asarray(wb).astype(float)[..., :3]; a = CN.grade(a, warm=1.8, sat=1.1, contrast=1.08); a = CN.screen(a, CN.bloom(a, thr=.84, r=(4, 12), k=(.25, .3)))
    wb = Image.fromarray(np.dstack([a.clip(0, 255), np.full(a.shape[:2], 255)]).astype(np.uint8)); m = L.rr_mask(300, 360, 20); L.drop_shadow(bd, m, wx, wy, 10, 6, .4); comp(bd, L.masked(wb, m), wx, wy)
    comp(bd, L.hair_rr_im(300, 360, 20, A(C['gold']), 1.5), wx, wy)
    clip = Image.open(f'{BT}/6b/per_pet/A3/walk@3x.png').convert('RGBA'); fw = clip.height; fr = clip.crop((fw * 2, 0, fw * 3, fw)); compc(bd, P('glow_48'), wx + 150, wy + 270); comp(bd, fr, wx + 150 - fw / 2, wy + 300 - fw)
    particles_box = (int(wx), int(wy), int(wx + 300), int(wy + 360))
    for (px_, py_) in ((wx + 40, wy + 60), (wx + 250, wy + 90), (wx + 70, wy + 200)): compc(bd, P('fx_mote'), px_, py_)
    text(bd, '今日 3,240 步', W / 2, y + 500, 'h2', C['cream'], 'mm'); comp(bd, P('walk_track', 360, 8), W / 2 - 180, y + 536); comp(bd, P('bar_fill_mint_h8', 230, 8), W / 2 - 180, y + 536); compc(bd, P('bar_tip_mint'), W / 2 + 50, y + 540)
    for i in range(6):
        cx = W / 2 - 150 + i * 60; done = i < 3
        if done: compc(bd, P('glow_10'), cx, y + 580)
        compc(bd, P('walk_step'), cx, y + 580)
    text(bd, '每 1000 步行一格', W / 2, y + 618, 'caption', C['mute'], 'mm')
    comp(bd, P('panel_inset', w - 48, 130), x + 24, y + 650); text(bd, '撿到', x + 48, y + 680, 'label', C['goldhi'], 'lm')
    for i, d in enumerate(('pebble', 'maple_leaf', 'acorn', 'feather')):
        im = Image.open(f'{BT}/6b/deco/deco_{d}@3x.png').convert('RGBA'); cx = x + 140 + i * 96; compc(bd, P('glow_24'), cx, y + 730); compc(bd, im, cx, y + 730)
    button(bd, '返屋企', W / 2 - 130, y + 806, 260, 'sec', ic='house')
    return bd
def s_dream():
    bg = Image.open(f'{BT}/6c/fx/dream_bg@3x.png').convert('RGBA'); a = np.asarray(bg).astype(float)[..., :3]
    a = CN.screen(a, CN.bloom(a, thr=.7, r=(8, 24), k=(.3, .4), tint=(.85, .8, 1))); a = CN.vignette(a, .32)
    bd = Image.fromarray(np.dstack([a.clip(0, 255), np.full((H, W), 255)]).astype(np.uint8))
    CN.particles(bd, (0, 120, W, 1100), 26, 41, [(214, 204, 255), (255, 240, 220), (170, 200, 255)], bokeh=8, bmin=10, bmax=26)
    bd.alpha_composite(P('scrim_top', W, 200).crop((0, 0, W, 170))); title(bd, '夢遊', W / 2, 46)
    L.backdrop(bd, 18, 18, 56, 56, L.circ_mask(56)); compc(bd, P('back_btn'), 46, 46); icon(bd, 'back', 46, 46); reg('back', 18, 18, 56, 56)
    for i, (k, n) in enumerate((('frag_forest', 3), ('frag_lake', 1), ('frag_star', 5), ('frag_toy', 0))):
        cx = 60 + i * 130; panel(bd, 'chip', cx - 46, 104, 112, 40, shadow=False); icon(bd, k, cx - 20, 124, glow=n > 0); text(bd, f'×{n}', cx + 50, 124, 'value', C['cream'] if n else C['mute'], 'rm')
    veil(bd, True)
    card = Image.open(f'{BT}/6c/cards/card_f3.png').convert('RGBA'); card = card.resize((card.width * 5, card.height * 5), Image.NEAREST)
    cx, cy = W / 2, 520; compc(bd, P('fx_rays'), cx, cy); compc(bd, P('glow_80'), cx, cy); fr = P('dream_card_frame', card.width + 56, card.height + 56); compc(bd, fr, cx, cy)
    L.drop_shadow(bd, L.rr_mask(card.width, card.height, 6), cx - card.width / 2, cy - card.height / 2, 10, 8, .5); compc(bd, card, cx, cy)
    sparkles(bd, ((cx - 130, cy - 120, 34), (cx + 120, cy + 90, 20), (cx + 110, cy - 140, 12)))
    title(bd, '新夢卡！', W / 2, 740); text(bd, '森林・螢火蟲之夜', W / 2, 800, 'h2', C['cream'], 'mm', sh=(0, 0, 0))
    panel(bd, 'toast', W / 2 - 170, 840, 340, 44); icon(bd, 'frag_forest', W / 2 - 140, 862); text(bd, '森林碎片 +1（3／5）', W / 2 - 116, 862, 'body', C['cream'], 'lm')
    button(bd, '收入夢簿', W / 2 - 150, 930, 300, 'violet', ic='dreambook')
    text(bd, '團絨瞓緊：寵物光已熄（petGlow 0）', W / 2, 1040, 'caption', C['mute'], 'mm', sh=(0, 0, 0))
    hud_dock(bd, 1, None)
    return bd
def qr_pattern(n=25, k=6, seed=7):
    rnd = np.random.RandomState(seed); g = rnd.rand(n, n) > .52
    for (ox, oy) in ((0, 0), (n - 7, 0), (0, n - 7)):
        g[oy:oy + 7, ox:ox + 7] = False; g[oy, ox:ox + 7] = g[oy + 6, ox:ox + 7] = g[oy:oy + 7, ox] = g[oy:oy + 7, ox + 6] = True; g[oy + 2:oy + 5, ox + 2:ox + 5] = True
    a = np.where(np.kron(g, np.ones((k, k))) > 0, 30, 255).astype(np.uint8); im = Image.fromarray(np.dstack([a, a, a + 0 * a, np.full(a.shape, 255, np.uint8)]))
    return im
def s_share():
    bd = garden('happy'); veil(bd)
    x, y, w, h = 45, 120, 495, 756; L.drop_shadow(bd, L.rr_mask(w, h, 28), x, y, 14, 10, .5); L.backdrop(bd, x, y, w, h, L.rr_mask(w, h, 28)); comp(bd, P('share_card_bg'), x, y)
    title(bd, '朋友名片', W / 2, y + 44); close_btn(bd, x + w - 34, y + 34)
    portrait(bd, x + 30, y + 92, 'A3', 'normal'); text(bd, '波波', x + 180, y + 120, 'title', C['cream'], 'lm'); icon(bd, 'mini_star', x + 192, y + 168); text(bd, '家族 Lv4', x + 212, y + 168, 'body', C['goldhi'], 'lm')
    text(bd, '形態：泡泡', x + 180, y + 208, 'body', C['cream'], 'lm')
    comp(bd, P('panel_inset', w - 60, 150), x + 30, y + 250)
    for i, t in enumerate(('第一次見到螢火蟲', '雨天一齊踩水氹', '識咗新朋友松鼠')):
        compc(bd, P('diamond'), x + 56, y + 280 + i * 44); text(bd, t, x + 74, y + 280 + i * 44, 'body', C['cream'], 'lm')
    comp(bd, P('divider', w - 120, 6), x + 60, y + 418)
    qx, qy = W / 2 - 99, y + 440; comp(bd, P('qr_frame'), qx, qy); compc(bd, qr_pattern(), qx + 99, qy + 99)
    text(bd, 'GLM1-7Q3K…9F2A', W / 2, y + 676, 'h2', C['cream'], 'mm')
    text(bd, '（QR 係示意，唔係真碼）', W / 2, y + 716, 'caption', C['mute'], 'mm')
    button(bd, '複製碼', 45, 900, 230, 'sec', ic='copy'); button(bd, '存圖', 310, 900, 230, 'pri', ic='photo')
    text(bd, '輸入朋友碼', 45, 1004, 'label', C['goldhi'], 'lm', sh=(0, 0, 0))
    comp(bd, P('code_field_on', 360, 60), 45, 1030); text(bd, 'GLM1-', 69, 1060, 'body', C['cream'], 'lm'); comp(bd, new(2, 30, A(C['goldhi'])), 69 + tw('GLM1-', 'body') + 4, 1045); reg('codeField', 45, 1030, 360, 60)
    button(bd, '貼上', 420, 1036, 120, 'violet', True, ic='paste')
    text(bd, '朋友掃描或貼上就可以探你', W / 2, 1160, 'body', C['cream'], 'mm', sh=(0, 0, 0))
    home_indicator(bd)
    return bd

SCREENS = [('home', s_home, 'v2 home'), ('popup', s_popup, 'v2 popup'), ('levelup', s_levelup, 'v2 levelup'), ('settings', s_settings, 'v2 settings'), ('journal_dex', s_journal, 'v2 journal_dex'),
           ('house_4b', s_house, 'v2 house_4b'), ('house_4b_decorate', s_house_deco, 'v2 house_4b_decorate'), ('5a_family_tree', s_family_tree, 'v2 5a'), ('5a_egg_choice', s_egg_choice, 'v2 5a'),
           ('5a_pet_card', s_pet_card, 'v2 5a'), ('5b_daily_plan', s_daily_plan, 'v2 5b'), ('5b_job_picker', s_job_picker, 'v2 5b'), ('5c_parent_pick', s_parent_pick, 'v2 5c'), ('5c_inherit_result', s_inherit, 'v2 5c'),
           ('6b_walk', s_walk, '6b 散步'), ('6c_dream', s_dream, '6c 夢遊'), ('6d_share', s_share, '6d 分享')]
ZH = {'home': '主畫面', 'popup': '彈窗', 'levelup': '升級', 'settings': '設定', 'journal_dex': '手帳・圖鑑', 'house_4b': '屋仔', 'house_4b_decorate': '佈置', '5a_family_tree': '家族樹', '5a_egg_choice': '揀蛋',
      '5a_pet_card': '寵物卡', '5b_daily_plan': '今日安排', '5b_job_picker': '揀工作', '5c_parent_pick': '揀父母', '5c_inherit_result': '傳承結果', '6b_walk': '6b 散步', '6c_dream': '6c 夢遊', '6d_share': '6d 分享'}
def overview(ims):
    tw_, th = 195, 422; cols = 6; rows = (len(ims) + cols - 1) // cols; pad = 18; top = 96
    O = Image.new('RGBA', (cols * (tw_ + pad) + pad, top + rows * (th + 56) + 20), (16, 20, 38, 255)); d = ImageDraw.Draw(O)
    d.text((pad, 26), '《微光小圃》UI kit v3（V3-A 金光現代 HD-2D）— 17 畫面 overview（@1x 縮圖）', font=L.F('sansb', 26), fill=C['goldhi'])
    d.text((pad, 62), '字：Noto Sans／Serif CJK TC（最細 18@3x，對比 ≥4.5）・icon：v3 HD 像素 32px＋光暈層・寵物瞓覺 petGlow＝0', font=L.F('sans', 18), fill=C['mute'])
    for i, (n, im) in enumerate(ims):
        x = pad + (i % cols) * (tw_ + pad); y = top + (i // cols) * (th + 56); O.alpha_composite(im.resize((tw_, th), Image.LANCZOS), (x, y))
        d.rounded_rectangle([x - 1, y - 1, x + tw_, y + th], 6, outline=A(C['gold'], .7), width=1); d.text((x + tw_ / 2, y + th + 22), ZH[n], font=L.F('sansb', 20), fill=C['cream'], anchor='mm')
    return O
def icons_compare():
    import ui_hd2d_v3_icons as I
    S = I.sources(); names = list(S.keys()); cols = 16; cw = 70; O = Image.new('RGBA', (cols * cw + 20, 70 + ((len(names) + cols - 1) // cols) * 130), (20, 26, 50, 255)); d = ImageDraw.Draw(O)
    d.text((10, 16), 'icon v2（上，16px ×2 nearest）→ v3（下，32px 重新打光＋sel-out＋高光＋光暈層）', font=L.F('sansb', 22), fill=C['goldhi'])
    for i, n in enumerate(names):
        x = 10 + (i % cols) * cw + 19; y = 60 + (i // cols) * 130; v2 = S[n]; O.alpha_composite(v2.resize((v2.width * 2, v2.height * 2), Image.NEAREST), (x, y))
        sp, gl = L.IC(n); O.alpha_composite(gl, (x - (gl.width - sp.width) // 2, y + 46 - (gl.height - sp.height) // 2)); O.alpha_composite(sp, (x, y + 46))
        d.text((x + 16, y + 110), n[:9], font=L.F('sans', 11), fill=C['mute'], anchor='mm')
    return O
def main():
    os.makedirs(OUT, exist_ok=True); ims = []
    for n, fn, src in SCREENS:
        L.SCREEN[0] = n; im = fn(); assert im.size == (W, H), (n, im.size); im.convert('RGB').save(f'{OUT}/{n}_3x.png', optimize=True); ims.append((n, im)); print('ok', n)
    overview(ims).convert('RGB').save(f'{OUT}/overview.png', optimize=True)
    icons_compare().convert('RGB').save(f'{OUT}/icons_v2_v3_compare.png')
    lay = dict(LAYOUT); lay['screens'] = {n: dict(source=src, file=f'mockups/{n}_3x.png', elements=LAY.get(n, {}), hits=HITS.get(n, [])) for n, _, src in SCREENS}
    lay['partsUsed'] = sorted(L.USED); lay['iconsUsed'] = sorted(L.ICONS_USED)
    json.dump(lay, open(f'{KIT}/layout_hd2d_v3.json', 'w'), ensure_ascii=False, indent=1)
    json.dump(dict(note='每次落字：畫面、字、角色、px@3x、字型、對比（bbox 背景第 5 百分位 WCAG）', texts=L.TEXTLOG), open(f'{KIT}/mockups/texts.json', 'w'), ensure_ascii=False, indent=1)
    cs = [t['contrast'] for t in L.TEXTLOG if t['contrast'] is not None]; print('texts', len(L.TEXTLOG), 'min contrast', min(cs), 'min px', min(t['px'] for t in L.TEXTLOG))
    bad = [t for t in L.TEXTLOG if t['contrast'] is not None and t['contrast'] < 4.5]
    for b in bad: print('LOW', b)
if __name__ == '__main__': main()
