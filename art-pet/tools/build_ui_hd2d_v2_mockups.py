# 《微光小圃》HD-2D v2 kit mockups（A 版頂旗＋B ×2 頭像）— 遊美 2026-11-02
# 只用 kit_hd2d_v2 atlas（ui／icons／font）砌 UI；背景（花園／房）＝現有 H3／4b 房間層即場合成。1x 195×422 → ×3 nearest 585×1266。
# 同時寫 layout_hd2d_v2.json（UI 座標唯一來源）。純 Pillow／numpy，冇 AI 圖。
import os, sys, json
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import hd2d_v2_px as X
from hd2d_v2_px import P, FILLS, new, put, putc, up, hx, img
ART = X.ART; KIT = f'{ART}/ui/kit_hd2d_v2'; MO = f'{KIT}/mockups'; os.makedirs(MO, exist_ok=True)
W, H = 195, 422

# ================================================================ 引擎（模擬 runtime：atlas 1x 畫）
class Atlas:
    def __init__(s, kind):
        s.J = json.load(open(f'{KIT}/atlas/{kind}@1x.json'))['frames']; s.A = Image.open(f'{KIT}/atlas/{kind}@1x.png').convert('RGBA'); s.c = {}
    def __call__(s, n):
        if n not in s.c:
            f = s.J[n]; s.c[n] = s.A.crop((f['x'], f['y'], f['x'] + f['w'], f['y'] + f['h']))
        return s.c[n]
UI = Atlas('ui_hd2d_v2'); IC = Atlas('icons_hd2d_v2')
def _map(n, l, r, src):
    mid = src - l - r
    return np.array([x if x < l else (src - (n - x) if x >= n - r else l + (x - l) % mid) for x in range(n)])
def nine(name, w, h):
    """9-slice：角原封、邊同中間 tile（唔拉伸）"""
    f = UI.J[name]; s = np.array(UI(name)); l, t, r, b = f.get('nine', [0, 0, 0, 0]); sl = f.get('slice')
    cm = _map(int(w), l, r, s.shape[1]); rm = _map(int(h), t, b, s.shape[0]) if sl == '9' else (np.arange(s.shape[0]) if sl == '3h' else _map(int(h), t, b, s.shape[0]))
    if sl == '3v': cm = np.arange(s.shape[1])
    return img(s[rm][:, cm])
def h3(name, w): return nine(name, w, UI(name).height)

FJ = json.load(open(f'{KIT}/fonts/fonts_v2.json'))['fonts']; FA = {k: np.array(Image.open(f'{KIT}/fonts/{v["image"]}'))[..., 3] > 0 for k, v in FJ.items()}
MISSING = set()
def text_img(t, sz=10, col='cream', col2=None, outline='line', shadow=True, ol=None):
    if ol is None: ol = sz > 8 or not shadow   # 8px 正文喺面板入面唔描邊（描邊會糊）；徽章／pill 上嘅字（shadow=False）照描邊
    F = FJ[f'fp{sz}']; G = F['glyphs']; lh = F['lineH']; A = FA[f'fp{sz}']
    wsum = 0
    for ch in t:
        if ch not in G: MISSING.add(ch); continue
        wsum += G[ch]['adv']
    Wd = wsum + 4; Hd = lh + 4; M = np.zeros((Hd, Wd), bool); x = 2
    for ch in t:
        g = G.get(ch)
        if not g: continue
        if g['w']:
            M[2 + g['yoff']:2 + g['yoff'] + g['h'], x + g['xoff']:x + g['xoff'] + g['w']] |= A[g['y']:g['y'] + g['h'], g['x']:g['x'] + g['w']]
        x += g['adv']
    a = np.zeros((Hd + 1, Wd, 4), np.uint8); MM = np.pad(M, ((0, 1), (0, 0)))
    C1 = np.array(P[col] if isinstance(col, str) else col); C2 = np.array(P[col2] if isinstance(col2, str) else (col2 if col2 else C1))
    if ol:
        O = X.dilate(MM)
        if shadow: a[np.roll(O, 1, axis=0)] = P['line']
        a[O] = P[outline] if isinstance(outline, str) else outline
    ys = np.where(MM.any(1))[0]
    if len(ys):
        yy = np.mgrid[0:Hd + 1, 0:Wd][0]; mid = ys[0] + (ys[-1] - ys[0]) * .55; a[MM] = C1; a[MM & (yy > mid)] = C2
    return img(a)
def text(bd, t, x, y, sz=10, anchor='l', **kw):
    im = text_img(t, sz, **kw)
    if anchor == 'm': x -= im.width / 2; x += 1
    elif anchor == 'r': x -= im.width - 3
    put(bd, im, x - 1, y - im.height / 2); return im.width - 4
def tw(t, sz=10): return sum(FJ[f'fp{sz}']['glyphs'].get(c, {'adv': 0})['adv'] for c in t)

def ic(n): return IC(n)
def icm(n): return IC('mini_' + n)
def medal_ic(d, fill, icon, mini=False, pressed=False):
    m = UI(f'med{d}_{fill}' + ('_p' if pressed else '')).copy(); i = icm(icon) if mini else ic(icon); putc(m, i, d / 2, d / 2 + (1 if pressed else 0)); return m
def ribbon(t, w=None, fill='navy', sz=10):
    w = w or tw(t, sz) + 10; r = h3(f'ribbon_{fill}', w); text(r, t, w / 2, 7, sz, 'm'); return r
def pill(t, fill='pri', w=None, icon=None):
    w = w or tw(t, 8) + 10 + (10 if icon else 0); p = h3(f'pill_{fill}', w)
    if icon: putc(p, icm(icon), 7, 5.5)
    text(p, t, w / 2 + (5 if icon else 0), 5.5, 8, 'm', col='white', ol=True, outline='line', shadow=False); return p
def button(t, w, fill='pri', h=20, icon=None, pressed=False):
    nm = (f'btn_{fill}' if h == 20 else f'btn16_{fill}') + ('_p' if pressed else ''); b = h3(nm, w)
    tx = w / 2 + (6 if icon else 0)
    if icon: putc(b, icm(icon), tx - tw(t, 10) / 2 - 8, h / 2 + (1 if pressed else 0))
    text(b, t, tx, h / 2 + (1 if pressed else 0) - .5, 10, 'm', col='white', col2='g_hi' if fill == 'pri' else 'cream', outline='line'); return b
def bar(w, v, fill='pri', h=7, low=False):
    b = h3(f'bar_trough_h{h}', w); fw = int(round((w - 4) * v))
    if fw > 0:
        f = h3(f'bar_fill_{"rose" if low else fill}_h{h}', fw); b.alpha_composite(f, (2, 2)); b.alpha_composite(UI(f'bar_tip_h{h}'), (2 + fw - 1, 2))
    return b
def chip(w, icon, val):
    c = h3('chip', w); put(c, UI('med13_navy'), 0, 0); putc(c, icm(icon), 6.5, 6.5)
    text(c, str(val), (w + 13) / 2 - 2, 6.5, 10, 'm', col='g_hi', col2='g_br'); return c
def red_dot(bd, cx, cy, n=None):
    if n is None: putc(bd, UI('red_dot'), cx, cy)
    else: putc(bd, UI('red_dot_num'), cx, cy); text(bd, str(n), cx + .5, cy, 8, 'm', col='white', shadow=False)
def veil(bd, k='fx_veil_tile'):
    v = nine(k, W, H); bd.alpha_composite(v); return bd
def panel(name, w, h): return nine(name, w, h)
def close_btn(bd, x, y): put(bd, UI('close'), x, y)
def title_plaque(bd, t, cx, y, fill='plaque'):
    w = tw(t, 12) + 20; p = h3(fill, w); text(p, t, w / 2, 8, 12, 'm', col='white', col2='g_hi')
    put(bd, UI('plaque_tail_l'), cx - w / 2 - 6, y + 2); put(bd, UI('plaque_tail_r'), cx + w / 2 - 2, y + 2); put(bd, p, cx - w / 2, y)

# ================================================================ 頭像（B ×2 face crop × A 頂旗槽；PORTRAIT_SYNC.md）
PR = json.load(open(f'{KIT}/portrait/portrait_rects.json'))
import ui_hd2d_v2_kit as KB
def pet_canvas(form, state='normal', acc=None, wear=None, job=None, pattern_from=None, top=40):
    """合成（同花園）→ 加頂 top px 空位（帽可以高過 PAD）"""
    p, info = X.compose_pet(form, state, (acc,) if acc else (), wear, pattern_from)
    c = new(p.width, p.height + top); c.alpha_composite(p, (0, top))
    if job:
        hb, hp = KB.job_hat(form, job); piv = info['pivot']; c.alpha_composite(hb, (int(piv[0] - hp[0]), int(piv[1] - hp[1] + top)))
    return c, info
def acc_key(acc, wear, job): return acc if acc else (f'wear_{wear}' if wear else (f'hat_{job}' if job else None))
def portrait(form, state='normal', acc=None, wear=None, job=None, pattern_from=None, dim=False):
    f = PR['aliases'].get(form, form); R = PR['forms'][f]; x0, y0, n = R['rect']; k = acc_key(acc, wear, job)
    m = R['acc'].get(k, {}) if k else {}; sh, pop = m.get('shift', 0), m.get('pop', 0)
    c, info = pet_canvas(f, state, acc, wear, job, pattern_from); T = 40
    yc = y0 - sh + T; cr = c.crop((x0, yc - pop, x0 + n, yc + n)); big = up(cr, 2); po = pop * 2
    fr = 52; L = new(fr + 2, fr + po + 4)
    win = new(fr, fr); win.alpha_composite(UI(f'portrait_bg_{state}')); petl = new(fr, fr); petl.alpha_composite(big.crop((0, po, 44, po + 44)), (4, 4))
    pa = np.array(petl); pa[np.array(UI('portrait_mask'))[..., 3] == 0] = 0; win.alpha_composite(img(pa)); win.alpha_composite(UI('portrait_frame'))
    if dim: win.alpha_composite(nine('fx_veil_tile', fr, fr)); a = np.array(win); a[np.array(UI('portrait_frame'))[..., 3] == 0 & (np.array(UI('portrait_mask'))[..., 3] == 0)] = 0
    put(L, win, 1, po)
    if po:  # 出框：裁位頂 pop 行（×2）＋穿過框頂 4px — 只畫飾品像素（身體照裁，框邊唔會被身體蓋走）
        c0, _ = pet_canvas(f, state, None, None, None, pattern_from); a1 = np.array(c); a0 = np.array(c0)
        dm = (a1[..., 3] > 0) & ((a0[..., 3] == 0) | (np.abs(a1[..., :3].astype(int) - a0[..., :3]).sum(-1) > 0))
        ac = a1.copy(); ac[~dm] = 0; ab = up(img(ac).crop((x0, yc - pop, x0 + n, yc + n)), 2)
        L.alpha_composite(ab.crop((0, 0, 44, po + 6)), (5, 0))
    gk = {'normal': 'sec', 'happy': 'rose', 'hungry': 'pri', 'sleepy': 'violet', 'sick': 'green', 'sleep': 'violet'}[state]
    putc(L, UI(f'gem_{gk}_7'), (fr + 2) / 2, po + fr - 1)
    if f'mood_badge_{state}' in UI.J: put(L, UI(f'mood_badge_{state}'), fr - 12, po + fr - 14)
    if m.get('badge'):  # 飾品大部分出框 → 右上角飾品細章（飾品本身縮圖）
        b = UI('med13_paper').copy(); putc(b, UI(f'acc_thumb_{k}'), 6.5, 6.5)
        put(L, b, fr - 12, po + 1)
    return L, po

# ================================================================ 場景
import build_ui_hd2d_v2_concept as CC
_SC = {}
def garden(state='hungry'):
    if state not in _SC: _SC[state] = CC.scene(state)
    return _SC[state].copy()
import house_4b_room as HR
HJ = json.load(open(f'{ART}/sprites/series2_house/house.json'))
def room(var='day', furn=('bed_leaf', 'table_stump', 'rug_round', 'wall_shelf', 'win_curtain', 'lamp_mushroom'), pets=(('evo_still_tide', 'normal', 96, 300),), base=f'{ART}/sprites/series2_house/room'):
    sp = []
    for k in furn:
        it = HJ['furniture'].get(k)
        if not it: continue
        sl = HJ['slots'][it['slot']]; ax, ay = sl['anchor']; im = np.array(Image.open(f"{ART}/sprites/series2_house/{it['png']}").convert('RGBA'))
        pv = it['pivot']; z = {'floor': 0, 'wall': 1}.get(sl['layer'], 2 + ay / 1000)
        sp.append((z, im, ax - pv[0], ay - pv[1], 'furn'))
    for (f, st, px, py) in pets:
        p, info = X.compose_pet(f, st); sp.append((2 + py / 1000, np.array(p), px - info['pivot'][0], py - info['pivot'][1], 'pet'))
    return Image.fromarray(HR.compose(var, base, sp)).convert('RGBA')

# ================================================================ layout（唯一來源 → layout_hd2d_v2.json）
L = {
 'art': [W, H], 'scale': 3, 'bands': {'top': [0, 42], 'garden': [42, 348], 'bottom': [348, 422]},
 'banner': {'frame': 'banner_top', 'x': 0, 'y': -5, 'w': W, 'h': 47, 'rivets': [[24, 39], [171, 39]], 'gem': [97.5, 40.5]},
 'portrait': {'x': 1, 'y': 6, 'w': 52, 'h': 52, 'win': [4, 4, 44, 44], 'popMaxPx': 6, 'note': '頂旗槽：框頂 y6（高過頂旗底 36px、出底 16px 似勳章）；pop 向上畫（y≥0）'},
 'nameplate': {'name': [58, 9], 'nameSize': 12, 'stage': [90, 3], 'xp': [57, 16, 76, 5]},
 'needs': {'x': 57, 'y': 22, 'dx': 41, 'dy': 10, 'w': 39, 'order': ['feed', 'heart', 'clean', 'sleep']},
 'chips': [{'icon': 'light', 'x': 143, 'y': 4, 'w': 47, 'plus': [189, 10.5]}, {'icon': 'star', 'x': 143, 'y': 19, 'w': 47, 'plus': [189, 25.5]}],
 'toast': {'x': 58, 'y': 46, 'w': 106, 'h': 17},
 'rail': [{'icon': 'gift', 'x': 166, 'y': 50, 'label': '委託', 'badge': 3}, {'icon': 'mail', 'x': 166, 'y': 92, 'dot': True}, {'icon': 'house', 'x': 166, 'y': 122, 'label': '屋仔'}],
 'acts': {'cy': 357, 'cx0': 26, 'dx': 47.7, 'd': 30, 'ribbonY': 375, 'ribbonW': 32, 'items': [['feed', 'pri', '餵食'], ['play_cat', 'rose', '玩耍'], ['clean', 'sec', '清潔'], ['sleep', 'violet', '瞓覺']]},
 'dock': {'frame': 'dock_bar', 'x': 1, 'y': 385, 'w': 193, 'h': 37, 'tabs': [['heart_bunny', '照顧'], ['play_cat', '玩'], ['sprout', '小圃'], ['book_bear', '手帳'], ['gear_chick', '設定']]},
 'bubble': {'anchor': 'pet.headTop', 'dy': -8},
 'popup': {'w': 171, 'x': 12, 'titleH': 17, 'close': 'top-right inset 4'},
 'house4b': {'back': [16, 18, 22], 'title': [97.5, 8, 70], 'decorate': [172, 392, 30], 'sheet': [4, 280, 187, 138], 'tabsCy': 297, 'cards': [[8.5, 328], [70.5, 328], [132.5, 328]], 'cardWH': [54, 66], 'done': [62, 398, 71, 16]},
}

# ================================================================ HUD 共用
def hud_top(bd, form='evo_still_tide', state='hungry', acc='bow', wear=None, job=None, name='團絨', stage='靜光', xp=.62, needs=(.22, .6, .55, .15)):
    b = L['banner']; put(bd, nine(b['frame'], b['w'], b['h']), b['x'], b['y'])
    for r in b['rivets']: putc(bd, UI('rivet'), *r)
    putc(bd, UI('gem_rose_7'), *b['gem'])
    np_ = L['nameplate']; text(bd, name, *np_['name'], 12, col='white', col2='g_hi')
    put(bd, ribbon(stage, fill='violet'), np_['stage'][0] + tw(name, 12) - 24 + 2, np_['stage'][1] - 1)
    x, y, w, h = np_['xp']; put(bd, bar(w, xp, 'sec', 5), x, y)
    for t in (.33, .66): putc(bd, UI('gem_pri_5'), x + w * t, y + 2.5)
    n = L['needs']
    for i, (k, v, f) in enumerate(zip(n['order'], needs, ('pri', 'rose', 'sec', 'violet'))):
        xx = n['x'] + (i % 2) * n['dx']; yy = n['y'] + (i // 2) * n['dy']
        put(bd, bar(n['w'] - 7, v, f, 7, low=v < .2), xx + 8, yy + 2); put(bd, UI('med11_paper'), xx, yy); putc(bd, icm(k), xx + 5.5, yy + 5.5)
        if v < .2: put(bd, UI('gem_rose_5'), xx + n['w'] - 3, yy - 1)
    for c in L['chips']:
        put(bd, chip(c['w'] - 4, c['icon'], 140 if c['icon'] == 'light' else 10), c['x'], c['y']); putc(bd, UI('chip_plus'), *c['plus'])
    p = L['portrait']; pt, po = portrait(form, state, acc, wear, job); put(bd, pt, p['x'] - 1, p['y'] - po)
def hud_rail(bd):
    for r in L['rail']:
        c = nine('panel_inset_sel', 24, 24); putc(c, ic(r['icon']), 12, 12.5); put(bd, c, r['x'] + 3, r['y'] + 3); put(bd, UI('gem_sec_5'), r['x'] + 12.5, r['y'])
        if r.get('badge'): red_dot(bd, r['x'] + 26, r['y'] + 4, r['badge'])
        if r.get('dot'): red_dot(bd, r['x'] + 26, r['y'] + 5)
        if r.get('label'): putc(bd, ribbon(r['label']), r['x'] + 15, r['y'] + 34)
def hud_toast(bd, t='收到小禮物', v='+5'):
    T = L['toast']; c = h3('toast', T['w']); putc(c, UI('med15_pri'), 16, 8.5); putc(c, icm('star'), 16, 8.5)
    text(c, t, 26, 8.5, 10); text(c, v, T['w'] - 12, 8.5, 10, 'r', col='g_hi', col2='g_mid'); put(bd, c, T['x'], T['y'])
def hud_acts(bd, pressed=-1):
    A = L['acts']
    for i, (k, f, lb) in enumerate(A['items']):
        cx = A['cx0'] + i * A['dx']; putc(bd, medal_ic(A['d'], f, k, pressed=i == pressed), cx, A['cy']); putc(bd, ribbon(lb, A['ribbonW']), cx, A['ribbonY'])
        if i == 0: putc(bd, UI('sparkle_7'), cx + 14, A['cy'] - 11); putc(bd, UI('sparkle_5'), cx - 15, A['cy'] - 5)
def hud_dock(bd, active=0, dot=3):
    D = L['dock']; x0, y, w, h = D['x'], D['y'], D['w'], D['h']; put(bd, nine(D['frame'], w, h), x0, y); twd = w / 5
    for i, (k, lb) in enumerate(D['tabs']):
        cx = x0 + twd * (i + .5)
        if i:
            dx = int(round(x0 + twd * i))
            for yy in range(y + 8, y + h - 7): bd.putpixel((dx, yy), P['nv4'] if yy % 2 else P['g_lo'])
            putc(bd, UI('rivet'), dx + .5, y + 6)
        if i == active:
            put(bd, nine('dock_pillar', int(twd) - 4, h - 4), cx - (int(twd) - 4) / 2, y + 2)
            putc(bd, medal_ic(22, 'pri', k), cx, y + 10); text(bd, lb, cx, y + 27, 10, 'm', col='white', col2='g_hi', outline='g_dk')
            putc(bd, UI('gem_rose_7'), cx, y - 1)
            for sx, sy in ((cx - 15, y + 3), (cx + 15, y + 6)): putc(bd, UI('sparkle_5'), sx, sy)
        else:
            putc(bd, medal_ic(20, 'navy', k), cx, y + 12); text(bd, lb, cx, y + 27, 10, 'm', col='cream', col2='paper1')
    if dot is not None and dot != active: red_dot(bd, x0 + twd * (dot + .5) + 9, y + 5)
def bubble(bd, t, icon, x, y):
    w = tw(t, 10) + 20; b = nine('bubble', w, 16); putc(b, icm(icon), 8, 8); text(b, t, 15, 8, 10, col='ink', ol=False, shadow=False)
    put(bd, b, x, y); put(bd, UI('bubble_tail'), x + 6, y + 15)

def home(state='hungry', **kw):
    bd = garden(state); hud_top(bd, state=state, **kw); hud_rail(bd); hud_toast(bd)
    bubble(bd, '肚仔餓…', 'feed', 101, 240); hud_acts(bd); hud_dock(bd, 0)
    for (sx, sy, n) in ((8, 66, 5), (160, 150, 5), (30, 200, 3), (175, 300, 5)): putc(bd, UI(f'sparkle_{n}'), sx, sy)
    return bd

# ================================================================ 彈窗／升級／設定／手帳
def popup_base(bd, h, title, y=None, close=True):
    P_ = L['popup']; y = y if y is not None else (H - h) / 2 - 10; x = P_['x']; w = P_['w']
    veil(bd); put(bd, panel('panel_navy', w, h), x, y); title_plaque(bd, title, W / 2, y - 7)
    if close: close_btn(bd, x + w - 19, y + 4)
    return x, y, w
def popup():
    bd = home(); x, y, w = popup_base(bd, 178, '收到小禮物')
    text(bd, '鄰居松鼠送咗嘢俾團絨！', W / 2, y + 24, 10, 'm')
    for i, (k, f, v) in enumerate((('light', 'sec', '×30'), ('star', 'pri', '×2'), ('furniture', 'rose', '×1'))):
        cx = x + 33 + i * 52; c = nine('card', 44, 54); putc(c, medal_ic(28, f, k), 22, 20); text(c, v, 22, 44, 10, 'm', col='g_hi', col2='g_br'); put(bd, c, cx - 22, y + 36)
        if i == 2: put(bd, pill('新', 'rose', 18), cx + 8, y + 32)
    putc(bd, UI('sparkle_7'), x + 22, y + 38); putc(bd, UI('sparkle_5'), x + w - 20, y + 86)
    put(bd, nine('panel_inset', w - 20, 24), x + 10, y + 98); putc(bd, medal_ic(16, 'paper', 'mail', True), x + 23, y + 110); text(bd, '附上一封信：「多謝你嘅花！」', x + 33, y + 110, 8)
    put(bd, button('收下', 70, 'pri', icon='check'), x + w - 82, y + 140); put(bd, button('睇信', 62, 'sec', icon='mail'), x + 14, y + 140)
    putc(bd, UI('hint_arrow'), x + w - 47, y + 128)
    return bd
def levelup():
    bd = garden('happy'); veil(bd)
    # 放射光（抖色實心像素）
    a = np.array(bd); yy, xx = np.mgrid[0:H, 0:W]; ang = np.arctan2(yy - 150, xx - 97.5); r = np.hypot(yy - 150, xx - 97.5)
    wedge = (np.floor((ang + np.pi) / (np.pi / 10)) % 2) == 0
    a[wedge & (r < 84) & (r > 22) & ((xx % 2) == 0) & ((yy % 2) == 0)] = P['g_lo']; a[wedge & (r < 50) & (r > 22) & (((xx + yy) % 2) == 0)] = P['g_lo']
    a[(r < 28) & (r > 23) & (((xx + yy) % 2) == 0)] = P['g_mid']; bd = img(a)
    putc(bd, UI('family_crest'), 97.5, 150); text(bd, 'Lv', 97.5, 143, 8, 'm', col='g_dk', ol=False, shadow=False); text(bd, '5', 97.5, 154, 12, 'm', col='white', col2='g_hi', outline='g_dk')
    title_plaque(bd, '升級喇！', W / 2, 96, 'plaque_pri')
    pt, po = portrait('evo_still_tide', 'happy', 'crown'); putc(bd, pt, 97.5, 210)
    text(bd, '團絨 Lv4 → Lv5', W / 2, 246, 12, 'm', col='white', col2='g_hi')
    for i in range(3): putc(bd, UI('star_on'), 80 + i * 17.5, 262)
    x, y, w = 22, 274, 151; put(bd, panel('panel_navy_flat', w, 62), x, y); text(bd, '新解鎖', x + 12, y + 13, 10, col='g_hi', col2='g_br')
    for i, (k, t) in enumerate((('decorate', '新家具'), ('mg_firefly', '螢火蟲遊戲'), ('gift', '委託 +1'))):
        cx = x + 28 + i * 48; putc(bd, medal_ic(24, 'navy', k), cx, y + 33); text(bd, t, cx, y + 52, 8, 'm')
    put(bd, button('好嘢！', 90, 'pri', icon='star'), W / 2 - 45, 346)
    for (sx, sy, n) in ((40, 110, 7), (156, 124, 7), (60, 190, 5), (140, 196, 5), (30, 250, 3), (170, 240, 3)): putc(bd, UI(f'sparkle_{n}'), sx, sy)
    return bd
def settings():
    bd = garden('normal'); hud_top(bd, state='normal', acc=None); veil(bd, 'fx_veil25_tile'); hud_dock(bd, 4, None)
    x, y, w, h = 8, 70, 179, 256; put(bd, panel('panel_navy', w, h), x, y); title_plaque(bd, '設定', W / 2, y - 7); close_btn(bd, x + w - 19, y + 4)
    rows = [('sound', '音樂', ('slider', .7)), ('sound', '音效', ('slider', .45)), ('bond', '震動', ('toggle', True)), ('bedtime', '瞓覺提醒', ('toggle', False)),
            ('info', '語言', ('seg', ['繁中', 'English'], 0)), ('quality', '畫質', ('seg', ['省電', '標準', '靚'], 1))]
    yy = y + 22
    for k, t, ctl in rows:
        put(bd, nine('panel_inset', w - 16, 24), x + 8, yy); putc(bd, medal_ic(16, 'navy', k, True) if False else UI('med16_navy'), x + 20, yy + 12); putc(bd, ic(k).crop((2, 2, 14, 14)), x + 20, yy + 12)
        text(bd, t, x + 32, yy + 12, 10)
        if ctl[0] == 'slider':
            sw = 64; put(bd, h3('slider_track', sw), x + w - 18 - sw, yy + 10); fw = int((sw - 4) * ctl[1]); put(bd, h3('bar_fill_sec_h5', fw), x + w - 16 - sw, yy + 11)
            putc(bd, UI('slider_knob'), x + w - 16 - sw + fw, yy + 12)
        elif ctl[0] == 'toggle':
            on = ctl[1]; tx = x + w - 40; put(bd, UI(f'toggle_track_{"on" if on else "off"}'), tx, yy + 7); put(bd, UI(f'toggle_knob_{"on" if on else "off"}'), tx + (11 if on else 0), yy + 7)
            text(bd, '開' if on else '關', tx - 6, yy + 12, 8, 'r', col='cream' if on else 'paper2')
        else:
            opts, sel = ctl[1], ctl[2]; ow = [tw(o, 8) + 10 for o in opts]; sw = sum(ow) + 4; sx = x + w - 14 - sw
            put(bd, h3('seg_bg', sw), sx, yy + 5); cx = sx + 2
            for i, o in enumerate(opts):
                if i == sel: put(bd, h3('seg_on', ow[i]), cx, yy + 7)
                text(bd, o, cx + ow[i] / 2, yy + 12, 8, 'm', col='white' if i == sel else 'paper2', ol=(i == sel), shadow=False); cx += ow[i]
        yy += 28
    put(bd, h3('divider', w - 24), x + 12, yy + 2)
    for i, (t, f, k) in enumerate((('存檔', 'sec', 'check'), ('通知', 'violet', 'mail'), ('重置', 'rose', 'reset'))):
        put(bd, button(t, 50, f, 16, icon=k if k in ('check', 'mail') else None), x + 12 + i * 53, yy + 12)
    text(bd, '字型：Fusion Pixel（OFL 1.1）', W / 2, y + h - 22, 8, 'm', col='paper2', shadow=False)
    text(bd, '版本 v0.5.2', W / 2, y + h - 12, 8, 'm', col='paper2', shadow=False)
    return bd
DEX = ['sprout', 'radiant', 'soft', 'lumi', 'evo_hop', 'evo_guard_tide', 'evo_still_moon', 'A1', 'B2', 'C3', 'D1', 'S1', 'S4C', None, None, None]
def journal_dex():
    bd = garden('normal'); veil(bd, 'fx_veil25_tile'); hud_dock(bd, 3, None)
    x, y, w, h = 6, 14, 183, 362; put(bd, panel('panel_navy', w, h), x, y); title_plaque(bd, '手帳', W / 2, y - 7); close_btn(bd, x + w - 19, y + 4)
    tabs = ['圖鑑', '日記', '成就', '家族']; tx = x + 10
    for i, t in enumerate(tabs):
        tw_ = tw(t, 10) + 14; put(bd, h3('subtab_on' if i == 0 else 'subtab', tw_), tx, y + 20); text(bd, t, tx + tw_ / 2, y + 27, 10, 'm', col='white' if i == 0 else 'paper2'); tx += tw_ + 3
    red_dot(bd, tx - 6, y + 21)
    text(bd, '已收集 13／48', x + 12, y + 46, 8, col='g_hi'); put(bd, bar(84, 13 / 48, 'pri', 6), x + w - 96, y + 43)
    cw, ch = 40, 52
    for i, f in enumerate(DEX):
        cx = x + 10 + (i % 4) * (cw + 3); cy = y + 56 + (i // 4) * (ch + 4)
        if f:
            c = nine('card_sel' if i == 6 else 'card', cw, ch); p, info = X.compose_pet(f, 'normal'); ex, ey = info['eyes']
            cr = p.crop((int(ex - 16), int(ey - 20), int(ex + 16), int(ey + 12))); put(c, cr, 4, 5)
            nm = {'sprout': '芽仔', 'radiant': '光光', 'soft': '軟軟', 'lumi': '螢螢', 'evo_hop': '跳跳', 'evo_guard_tide': '潮守', 'evo_still_moon': '月靜', 'A1': '團A1', 'B2': '團B2', 'C3': '團C3', 'D1': '團D1', 'S1': '細佬', 'S4C': '火仔'}[f]
            text(c, nm, cw / 2, ch - 9, 8, 'm'); put(bd, c, cx, cy)
            if i == 6: put(bd, pill('新', 'rose', 18), cx + cw - 16, cy - 3)
        else:
            c = nine('card_locked', cw, ch); putc(c, icm('lock'), cw / 2, ch / 2 - 4); text(c, '？？？', cw / 2, ch - 9, 8, 'm', col='paper2', shadow=False); put(bd, c, cx, cy)
    by = y + 56 + 4 * (ch + 4) + 2; put(bd, nine('panel_paper', w - 20, 56), x + 10, by)
    text(bd, '月靜（靜光・月）', x + 20, by + 12, 10, col='ink', ol=False, shadow=False)
    text(bd, '夜晚會喺窗邊發出淡淡月光，', x + 20, by + 27, 8, col='ink', ol=False, shadow=False); text(bd, '最鍾意聽故事。', x + 20, by + 38, 8, col='ink', ol=False, shadow=False)
    put(bd, UI('stamp_done'), x + w - 40, by + 18)
    return bd

# ================================================================ 4b 屋仔
def house_hud(bd, title='團絨嘅屋仔', deco=True):
    h = L['house4b']; cx, cy, d = h['back']; putc(bd, medal_ic(d, 'navy', 'back'), cx, cy)
    tx, ty, tw_ = h['title']; w_ = max(tw_, tw(title, 10) + 16); r = h3('ribbon_navy', w_); text(r, title, w_ / 2, 7, 10, 'm'); put(bd, r, tx - w_ / 2, ty)
    put(bd, chip(43, 'star', 36), 146, 6)
    if deco:
        cx, cy, d = h['decorate']; putc(bd, medal_ic(d, 'pri', 'decorate'), cx, cy); putc(bd, ribbon('佈置', 30), cx, cy + 19)
def house_4b():
    bd = room(); house_hud(bd)
    pt, po = portrait('evo_still_tide', 'sleepy', 'nightcap'); put(bd, pt, 2, 34 - po)
    bubble(bd, '好攰呀…', 'sleep', 104, 252)
    for i, (k, f, lb) in enumerate((('sleep', 'violet', '瞓覺'), ('play_cat', 'rose', '玩'), ('feed', 'pri', '餵食'))):
        cx = 26 + i * 44; putc(bd, medal_ic(28, f, k), cx, 392); putc(bd, ribbon(lb, 30), cx, 410)
    putc(bd, UI('sparkle_5'), 150, 380)
    return bd
def house_4b_decorate():
    bd = room(furn=('bed_cloud', 'table_round', 'rug_leaf', 'wall_frame', 'win_star', 'lamp_firefly')); house_hud(bd, '佈置屋仔', deco=False)
    h = L['house4b']; sx, sy, sw, sh = h['sheet']; put(bd, panel('panel_navy', sw, sh + 6), sx, sy); putc(bd, UI('sheet_handle'), W / 2, sy + 5)
    for i, (k, t) in enumerate((('furniture', '床'), ('light', '燈'), ('cabinet', '檯'), ('decorate', '牆'), ('house', '窗'), ('star', '地氈'))):
        cx = 22 + i * 30; on = i == 0; putc(bd, medal_ic(25 if on else 22, 'pri' if on else 'navy', k) if (on or True) else None, cx, h['tabsCy'])
    cw, ch = h['cardWH']
    for i, ((cx, cy), (nm, st, price)) in enumerate(zip(h['cards'], (('bed_leaf', 'own', '已擁有'), ('bed_cloud', 'sel', '使用中'), (None, 'lock', '40')))):
        c = nine('card_sel' if st == 'sel' else ('card_locked' if st == 'lock' else 'card'), cw, ch)
        if nm:
            im = Image.open(f'{ART}/sprites/series2_house/furniture/{nm}.png').convert('RGBA'); im = im.resize((im.width // 2, im.height // 2), Image.NEAREST); putc(c, im, cw / 2, 24)
            text(c, HJ['furniture'][nm]['zh'], cw / 2, 46, 8, 'm')
        else:
            putc(c, icm('lock'), cw / 2, 22); text(c, '星星床', cw / 2, 46, 8, 'm', col='paper2', shadow=False)
        p = pill(price, 'sec' if st == 'sel' else ('pri' if st == 'lock' else 'navy'), icon='check' if st == 'sel' else ('star' if st == 'lock' else None)); putc(c, p, cw / 2, 58)
        put(bd, c, cx, cy)
    dx, dy, dw, dh = h['done']; put(bd, button('完成', dw, 'pri', 16, icon='check'), dx, dy)
    return bd

# ================================================================ 5a／5b／5c
FAM = [('evo_still_tide', '團絨', '靜光', 'Lv8'), ('A3', '波波', '成年', 'Lv5'), ('S4C', '火仔', '少年', 'Lv3'), ('S1', '豆豆', '幼年', 'Lv1'), ('B1', '咩咩', '蛋', '—')]
def sheet_bg(): bd = room('day', pets=()); veil(bd); return bd
def family_tree():
    bd = sheet_bg(); x, y, w, h = 6, 14, 183, 394; put(bd, panel('panel_navy', w, h), x, y); title_plaque(bd, '家族樹', W / 2, y - 7); close_btn(bd, x + w - 19, y + 4)
    putc(bd, UI('family_crest'), 40, y + 46); text(bd, 'Lv', 40, y + 39, 8, 'm', col='g_dk', ol=False, shadow=False); text(bd, '6', 40, y + 50, 12, 'm', col='white', col2='g_hi', outline='g_dk')
    text(bd, '家族等級', 66, y + 32, 10, col='g_hi', col2='g_br'); put(bd, bar(104, .58, 'gold', 7), 66, y + 42); text(bd, '58／100 XP', 66, y + 56, 8, col='paper2', shadow=False)
    text(bd, '家族 Lv7 解鎖 Lv6 工作', 66, y + 68, 8, col='vi0')
    nodes = [(97.5, y + 110, 0), (52, y + 186, 1), (143, y + 186, 2), (52, y + 262, 3), (143, y + 262, 4)]
    for (ax, ay), (bx, by) in (((97.5, y + 136), (52, y + 160)), ((97.5, y + 136), (143, y + 160)), ((52, y + 212), (52, y + 236)), ((143, y + 212), (143, y + 236))):
        my = (ay + by) / 2; put(bd, nine('tree_line_v', 3, my - ay), ax - 1, ay); put(bd, h3('tree_line_h', abs(bx - ax) + 3), min(ax, bx) - 1, my - 1); put(bd, nine('tree_line_v', 3, by - my), bx - 1, my); putc(bd, UI('tree_joint'), ax, my)
    for (cx, cy, i) in nodes:
        f, nm, st, lv = FAM[i]; c = nine('tree_node_gold' if i == 0 else ('tree_node_sel' if i == 2 else 'tree_node'), 60, 52)
        if f != 'B1':
            pt, po = portrait(f, 'happy' if i == 0 else 'normal', 'crown' if i == 0 else None); pt = pt.resize((pt.width // 2 + (pt.width % 2), pt.height // 2), Image.NEAREST) if False else pt
            sm = pt.crop((0, po, 54, po + 54)).resize((27, 27), Image.NEAREST); put(c, sm, 4, 5)
        else: putc(c, ic('egg_tr'), 17, 18)
        text(c, nm, 34, 12, 10); put(c, ribbon(st, None, 'violet' if i == 0 else 'navy', 8), 31, 20); text(c, lv, 34, 42, 8, col='g_hi', shadow=False)
        put(bd, c, cx - 30, cy - 26)
        if i == 0: putc(bd, ic('crown'), cx - 18, cy - 28)
    for i, (k, t, n) in enumerate((('pets', '成員', '5／6'), ('egg_tr', '蛋', '1'), ('inherit', '傳承', '2'))):
        cx = x + 30 + i * 62; putc(bd, medal_ic(24, 'navy', k), cx, y + 316); text(bd, t, cx + 15, y + 312, 8); text(bd, n, cx + 15, y + 322, 8, col='g_hi')
    put(bd, button('孵新蛋', 100, 'pri', icon='plus'), W / 2 - 50, y + 350)
    return bd
def egg_choice():
    bd = sheet_bg(); x, y, w = popup_base(bd, 214, '揀一隻蛋', y=90)
    text(bd, '家族 Lv6：可以孵第 5 隻', W / 2, y + 24, 8, 'm', col='paper1')
    for i, (k, t, d, ok) in enumerate((('egg_tr', '團絨蛋', '會進化做靜光', True), ('egg_kid', '細佬蛋', '花紋跟父母', True))):
        cx = x + 44 + i * 83; c = nine('egg_card' if i == 0 else 'card', 72, 112)
        putc(c, UI('fx_ripple'), 36, 36); putc(c, medal_ic(34, 'pri' if i == 0 else 'sec', k), 36, 36)
        text(c, t, 36, 64, 10, 'm', col='white', col2='g_hi'); text(c, d, 36, 78, 8, 'm', col='paper2', shadow=False)
        put(c, pill('揀呢隻' if i == 0 else '揀', 'pri' if i == 0 else 'navy', 52 if i == 0 else 30), 36 - (26 if i == 0 else 15), 92); put(bd, c, cx - 36, y + 36)
    putc(bd, UI('sparkle_7'), x + 14, y + 44); putc(bd, UI('sparkle_5'), x + w - 14, y + 120)
    put(bd, button('孵化！', 92, 'pri', icon='sprout'), W / 2 - 46, y + 160); text(bd, '孵化要 3 日', W / 2, y + 190, 8, 'm', col='paper2', shadow=False)
    return bd
def pet_card():
    bd = sheet_bg(); x, y, w = popup_base(bd, 262, '寵物卡', y=74)
    pt, po = portrait('A3', 'happy', wear='hat'); putc(bd, pt, x + 36, y + 50 - po / 2)
    text(bd, '波波', x + 68, y + 30, 12, col='white', col2='g_hi'); put(bd, ribbon('成年', None, 'violet'), x + 70 + tw('波波', 12), y + 22)
    put(bd, pill('主養', 'pri', 30, 'star'), x + 68, y + 42); text(bd, '團絨線・A 系', x + 102, y + 47, 8, col='paper2', shadow=False)
    put(bd, bar(76, .7, 'sec', 6), x + 68, y + 58); text(bd, 'Lv5', x + 148, y + 61, 8, col='g_hi')
    yy = y + 84
    for k, t, v, f in (('feed', '肚餓', .8, 'pri'), ('heart', '開心', .9, 'rose'), ('clean', '乾淨', .4, 'sec'), ('sleep', '精神', .6, 'violet')):
        put(bd, nine('panel_inset', w - 20, 20), x + 10, yy); put(bd, UI('med13_paper'), x + 15, yy + 3); putc(bd, icm(k), x + 21.5, yy + 9.5); text(bd, t, x + 34, yy + 10, 10); put(bd, bar(70, v, f, 7), x + 70, yy + 7); text(bd, f'{int(v * 100)}', x + w - 16, yy + 10, 8, 'r', col='g_hi'); yy += 22
    put(bd, h3('divider', w - 30), x + 15, yy + 2)
    for i, (k, t) in enumerate((('pattern', '花紋'), ('trick', '把戲'), ('family_tree', '族譜'))):
        cx = x + 32 + i * 54; putc(bd, medal_ic(24, 'navy', k), cx, yy + 22); text(bd, t, cx, yy + 40, 8, 'm')
    put(bd, button('設為主養', 92, 'sec', icon='check'), x + 10, yy + 52); put(bd, button('放生', 52, 'dis'), x + w - 62, yy + 52)
    return bd
PLAN = [('evo_still_tide', '團絨', 'exp', '遠足中…返嚟 18:00', None), ('A3', '波波', 'job', '園丁 Lv3・+3 碎', 'garden'), ('A2', '咩咩', 'rest', '休息：精神 +20', None), ('S5B', '細佬', 'job', '廚師 Lv1・+1 碎', 'chef')]
def daily_plan():
    bd = sheet_bg(); x, y, w, h = 6, 14, 183, 394; put(bd, panel('panel_navy', w, h), x, y); title_plaque(bd, '今日安排', W / 2, y - 7); close_btn(bd, x + w - 19, y + 4)
    put(bd, chip(60, 'gift', '遠足 1/2'), x + 12, y + 20); put(bd, chip(60, 'star', '碎 4/12'), x + 80, y + 20)
    yy = y + 42
    for f, nm, mode, st, job in PLAN:
        r = nine('panel_inset_sel' if mode == 'exp' else 'panel_inset', w - 16, 76); put(bd, r, x + 8, yy)
        pt, po = portrait(f, 'normal', job=job, dim=mode == 'exp'); put(bd, pt, x + 10, yy + 12 - po)
        if mode == 'exp': putc(bd, medal_ic(17, 'violet', 'expedition'), x + 52, yy + 18)
        text(bd, nm, x + 70, yy + 12, 10, col='white', col2='g_hi'); text(bd, st, x + 70, yy + 26, 8, col='paper2', shadow=False)
        sx = x + 66; put(bd, h3('seg_bg', 108), sx, yy + 40)
        for i, (k, t, key) in enumerate((('expedition', '遠足', 'exp'), ('job_chef', '工作', 'job'), ('rest', '休息', 'rest'))):
            cx = sx + 2 + i * 34.7; on = key == mode; locked = key == 'exp' and mode != 'exp' and nm == '細佬'
            if on: put(bd, h3('seg_on', 35), cx, yy + 42)
            elif locked: put(bd, h3('seg_locked', 35), cx, yy + 42)
            text(bd, t, cx + 17.5, yy + 47, 8, 'm', col='white' if on else 'paper2', ol=on or locked, shadow=False)
        if job: put(bd, UI('job_lv_badge'), x + 48, yy + 46); text(bd, '3' if job == 'garden' else '1', x + 54.5, yy + 52.5, 8, 'm', col='white', shadow=False)
        yy += 80
    text(bd, '遠足每日最多 2 次・細佬未成年唔去得', W / 2, yy + 6, 8, 'm', col='paper2', shadow=False)
    return bd
JOBS = [('job_chef', '廚師', 1, .2, '+1 碎'), ('mail', '郵差助手', 2, .6, '+2 碎'), ('sprout', '園丁', 3, .4, '+3 碎'), ('bedtime', '守夜', 5, 1, '+5 碎')]
def job_picker():
    bd = sheet_bg(); x, y, w = popup_base(bd, 268, '揀工作', y=64)
    pt, po = portrait('A3', 'normal', job='garden'); put(bd, pt, x + 10, y + 18 - po); text(bd, '波波 想做咩？', x + 70, y + 32, 10); text(bd, '每 5 日升 1 級', x + 70, y + 46, 8, col='paper2', shadow=False)
    for i, (k, t, lv, v, out) in enumerate(JOBS):
        cx = x + 10 + (i % 2) * 77; cy = y + 78 + (i // 2) * 84; sel = i == 2; c = nine('card_sel' if sel else 'card', 74, 80)
        putc(c, medal_ic(28, 'pri' if sel else 'navy', k), 22, 20); put(c, UI('job_lv_badge'), 34, 24); text(c, str(lv), 40.5, 30.5, 8, 'm', col='white', shadow=False)
        text(c, t, 47, 14, 8, 'm' if False else 'l') if False else text(c, t, 37 + (0 if len(t) < 3 else -2), 12, 8)
        put(c, bar(62, v, 'gold' if lv >= 5 else 'pri', 6), 6, 44); text(c, '封頂' if lv >= 5 else f'Lv{lv}→{lv + 1}', 37, 56, 8, 'm', col='g_hi' if lv >= 5 else 'paper2', shadow=False)
        text(c, f'每日 {out}', 37, 68, 8, 'm'); put(bd, c, cx, cy)
        if sel: putc(bd, UI('check_on'), cx + 66, cy + 6)
    put(bd, button('確認', 84, 'pri', icon='check'), W / 2 - 42, y + 244)
    return bd
PZH = {'wave': '波紋', 'crescent': '月牙', 'spot': '斑點', 'diamond': '菱格', 'spark': '火花', 'stripe': '條紋', 'star': '星星', 'leaf': '葉紋', 'dot': '點點', 'heart': '心心'}
PARENTS = [('evo_still_tide', '團絨', 'tide'), ('A3', '波波', 'A3'), ('evo_still_moon', '月靜', 'moon'), ('C3', '咕咕', 'C3'), ('evo_still_ember', '火火', 'ember'), (None, '？', None)]
def parent_pick():
    bd = sheet_bg(); x, y, w, h = 6, 14, 183, 394; put(bd, panel('panel_navy', w, h), x, y); title_plaque(bd, '揀爸爸媽媽', W / 2, y - 7); close_btn(bd, x + w - 19, y + 4)
    text(bd, '揀 2 隻成年：細佬會傳承花紋', W / 2, y + 22, 8, 'm', col='paper2', shadow=False)
    L5C = X.L5C['parents']; pk = list(L5C.keys())
    for i, (f, nm, _) in enumerate(PARENTS):
        cx = x + 10 + (i % 2) * 83; cy = y + 34 + (i // 2) * 92; sel = i in (0, 3); c = nine('card_sel' if sel else ('card_locked' if not f else 'card'), 80, 88)
        if f:
            pt, po = portrait(f, 'happy' if sel else 'normal'); put(c, pt.crop((0, po, 54, po + 56)), 13, 4)
            text(c, nm, 40, 66, 10, 'm'); put(c, UI('swatch_frame'), 8, 72)
            pp = L5C[pk[i % len(pk)]]; sa = np.array(c); sa[75:81, 11:17] = hx(pp['tint']['lo']); sa[75:78, 11:17] = hx(pp['tint']['hi']); c = img(sa)
            text(c, PZH.get(pp['pattern'], pp['pattern']), 22, 78, 8)
            if sel: put(c, UI('check_on'), 64, 4)
        else: putc(c, icm('lock'), 40, 36); text(c, '未成年', 40, 66, 8, 'm', col='paper2', shadow=False)
        put(bd, c, cx, cy)
    yy = y + 316; put(bd, nine('panel_inset_sel', w - 16, 44), x + 8, yy); putc(bd, medal_ic(22, 'violet', 'inherit'), x + 24, yy + 22)
    text(bd, '傳承：花紋 50％・顏色 50％', x + 40, yy + 13, 8); put(bd, h3('pill_fast_on', 44), x + 40, yy + 24); text(bd, '快 ×2', x + 62, yy + 29.5, 8, 'm', col='white', ol=True, shadow=False)
    put(bd, h3('pill_fast_locked', 44), x + 88, yy + 24); text(bd, '快 ×3', x + 110, yy + 29.5, 8, 'm', col='paper2', ol=True, shadow=False); putc(bd, icm('lock'), x + 140, yy + 29.5)
    put(bd, button('孵細佬蛋', 100, 'pri', icon='plus'), W / 2 - 50, y + 366)
    return bd
def inherit_result():
    bd = sheet_bg(); x, y, w = popup_base(bd, 236, '傳承結果', y=86, close=False)
    for i, f in enumerate(('evo_still_tide', 'C3')):
        pt, po = portrait(f, 'normal'); sm = pt.crop((0, po, 54, po + 54)).resize((27, 27), Image.NEAREST); put(bd, sm, x + 18 + i * 110, y + 26)
    put(bd, h3('tree_line_h', 64), x + 52, y + 38); putc(bd, UI('tree_joint'), W / 2, y + 39)
    putc(bd, UI('fx_ripple'), W / 2, y + 78); pt, po = portrait('S4C', 'happy', pattern_from='evo_still_tide'); putc(bd, pt, W / 2, y + 86 - po / 2)
    for (sx, sy, n) in ((W / 2 - 34, y + 60, 7), (W / 2 + 32, y + 96, 5), (W / 2 + 28, y + 54, 3)): putc(bd, UI(f'sparkle_{n}'), sx, sy)
    text(bd, '細佬「火仔」出世喇！', W / 2, y + 128, 10, 'm', col='white', col2='g_hi')
    for i, (k, t, v) in enumerate((('pattern', '花紋', '波紋（爸爸）'), ('d_spark', '顏色', '火橙（媽媽）'))):
        yy = y + 142 + i * 22; put(bd, nine('panel_inset', w - 24, 20), x + 12, yy); putc(bd, ic(k), x + 24, yy + 10); text(bd, t, x + 36, yy + 10, 10); text(bd, v, x + w - 18, yy + 10, 8, 'r', col='g_hi')
    put(bd, button('好！', 72, 'pri', icon='heart'), W / 2 - 36, y + 196)
    return bd

# ================================================================ 頭像飾品處理示範（PORTRAIT_SYNC.md 用）
def portrait_cases():
    cases = [('evo_still_tide', None, None, None, '冇飾品'), ('evo_still_tide', 'bow', None, None, '蝴蝶結'), ('sprout', 'crown', None, None, '皇冠'),
             ('evo_still_tide', 'nightcap', None, None, '睡帽'), ('A2', None, 'hat', None, '新線帽'), ('A3', None, None, 'watch', '守夜帽'), ('radiant', 'halo', None, None, '光環→細章'), ('S5B', None, None, 'chef', 'S5 廚師帽')]
    cw, ch = 62, 92; S = new(len(cases) // 2 * cw + 8, 2 * ch + 22, P['nv3']); text(S, '頭像 × 飾品（×1 art；mockup 再 ×3）', 4, 8, 8)
    for i, (f, a, w_, j, lab) in enumerate(cases):
        cx = 4 + (i % 4) * cw; cy = 18 + (i // 4) * ch; bg = nine('banner_top', cw - 4, 50); put(S, bg, cx, cy)
        pt, po = portrait(f, 'normal', a, w_, j); put(S, pt, cx + 3, cy + 22 - po)
        text(S, lab, cx + (cw - 4) / 2, cy + 84, 8, 'm')
        k = acc_key(a, w_, j); m = PR['forms'][PR['aliases'].get(f, f)]['acc'].get(k, {}) if k else {}
        text(S, f"s{m.get('shift', 0)} p{m.get('pop', 0)}{' 章' if m.get('badge') else ''}", cx + (cw - 4) / 2, cy + 8, 8, 'm', col='g_hi', shadow=False)
    return S

SCREENS = [('home', home), ('popup', popup), ('levelup', levelup), ('settings', settings), ('journal_dex', journal_dex), ('house_4b', house_4b), ('house_4b_decorate', house_4b_decorate),
           ('5a_family_tree', family_tree), ('5a_egg_choice', egg_choice), ('5a_pet_card', pet_card), ('5b_daily_plan', daily_plan), ('5b_job_picker', job_picker),
           ('5c_parent_pick', parent_pick), ('5c_inherit_result', inherit_result)]
if __name__ == '__main__':
    only = sys.argv[1:]
    json.dump(L, open(f'{KIT}/layout_hd2d_v2.json', 'w'), ensure_ascii=False, indent=1)
    outs = {}
    for n, fn in SCREENS:
        if only and n not in only: continue
        im = fn().convert('RGBA'); a = np.array(im); a[..., 3] = 255; im = img(a); outs[n] = im
        up(im, 3).save(f'{MO}/{n}_3x.png'); im.resize((360, 779), Image.NEAREST).save(f'{MO}/{n}_smallphone_360w.png')
    if not only or 'cases' in only:
        S = portrait_cases(); up(S, 3).save(f'{KIT}/portrait/portrait_cases_3x.png')
    if not only:
        th = [up(outs[n], 1) for n, _ in SCREENS]; cols = 7; ov = new(cols * (W + 6) + 6, 2 * (H + 16) + 6, P['nv4'])
        for i, (n, _) in enumerate(SCREENS):
            ox = 6 + (i % cols) * (W + 6); oy = 6 + (i // cols) * (H + 16); ov.alpha_composite(outs[n], (ox, oy)); text(ov, n, ox + W / 2, oy + H + 7, 8, 'm')
        up(ov, 2).save(f'{MO}/overview_2x.png')
    print('missing glyphs:', ''.join(sorted(MISSING)) or 'none')
