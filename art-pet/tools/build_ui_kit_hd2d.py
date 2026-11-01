# 《微光小圃》HD-2D production UI kit — 純 Pillow/numpy 程序生成，無 AI 圖。
# 輸出：ui/kit_hd2d/ atlas(@3x/@2x)+JSON(frames/9-slice/anchors)、icons、bitmap fonts、labels。
# 重跑：cd art-pet && python3 tools/build_ui_kit_hd2d.py && python3 tools/build_ui_kit_hd2d_mock.py && python3 tools/validate_ui_kit_hd2d.py
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import ui_hd2d_kit as K
import ui_hd2d_icons as I
k, v2 = K.k, K.v2
P, hx, mix, put, solid = k.P, k.hx, k.mix, k.put, k.solid
C, frame, gem, medallion, text, gold_text, place, gauss, amul, vgrad = K.C, K.frame, K.gem, K.medallion, K.text, K.gold_text, K.place, K.gauss, K.amul, K.vgrad
OUT = f'{K.ROOT}/ui/kit_hd2d'
os.makedirs(OUT, exist_ok=True)
for d in ('atlas', 'icons', 'fonts', 'labels'): os.makedirs(f'{OUT}/{d}', exist_ok=True)

# ---------- contrast fixes (Kurt: disabled / locked 要清楚) ----------
C['dis'] = (hx('#CDD1E3'), hx('#9AA0BC'))           # lighter slate; label uses dark ink (#262A48) -> >=4.5:1
C['locked'] = (hx('#4E5584', 238), hx('#363C66', 242))  # lifted off the navy bg; label/"?" near-white
INK_DIS = hx('#262A48'); LOCK_FG = hx('#F4F5FC')
NEED_COL = {'feed': (hx('#FFE6A8'), hx('#FF9E3E')), 'mood': (hx('#FFC8D8'), hx('#FF5C8E')),
            'clean': (hx('#C8F2FF'), hx('#3FAEEA')), 'energy': (hx('#FFF4B8'), hx('#FFC23A'))}

REG = {}   # name -> dict(img3=..., box, art, nine, slice, group, stub, note, pivot)
def comp(name, w, h, fn, group, nine=None, slice_=None, pad=10, stub=False, note='', pivot=None, bloom=True):
    """fn(L, o): draw on SS canvas with art origin (o,o). nine = corner art units (l,t,r,b) measured from the logical box."""
    W, H = P(w + 2 * pad), P(h + 2 * pad)
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    fn(L, pad)
    if bloom: L = K.bloom(L, thr=0.82, radius=1.6, strength=0.35)
    im = L.reduce(2)
    a = np.asarray(im)[..., 3]
    ys, xs = np.where(a > 3)
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    im = im.crop((x0, y0, x1, y1))
    bx, by = pad * 3 - x0, pad * 3 - y0
    bw, bh = round(w * 3), round(h * 3)
    e = dict(img=im, box=[int(bx), int(by), bw, bh], art=[w, h], group=group, stub=stub, note=note, slice=None, nine=None)
    if nine:
        l, t, r, b = nine
        sw, sh = im.size
        e['nine'] = [int(bx + round(l * 3)) if l else 0, int(by + round(t * 3)) if t else 0,
                     int(sw - bx - bw + round(r * 3)) if r else 0, int(sh - by - bh + round(b * 3)) if b else 0]
        e['slice'] = slice_ or ('9' if (t and l) else '3h' if l else '3v')
    e['pivot'] = pivot or [int(bx + bw / 2), int(by + bh / 2)]
    REG[name] = e
    return e

def F(w, h, r, fill, **kw):
    def fn(L, o): place(L, frame(w, h, r, fill, **kw), P(o), P(o))
    return fn
def FP(w, h, r, fill, dy=1.1, **kw):     # pressed: baked downward shift, logical box unchanged
    def fn(L, o): place(L, frame(w, h, r, fill, pressed=True, **kw), P(o), P(o + dy))
    return fn

# ================= PANELS =================
comp('panel_glass', 64, 64, F(64, 64, 12, C['navy'], glow=1.3, ornate=True), 'panel', nine=(14, 14, 14, 14), note='主彈窗（委託／設定／手帳）；角寶石已烘焙')
comp('panel_glass_plain', 48, 48, F(48, 48, 10, C['navy'], glow=1.0, ornate=False), 'panel', nine=(12, 12, 12, 12), note='底部 sheet／側欄／托盤')
comp('panel_paper', 56, 56, F(56, 56, 10, C['paper'], glow=0.9, ornate=True), 'panel', nine=(12, 12, 12, 12), note='羊皮紙：日記內頁／說明（文字用 ink）')
comp('panel_inset', 40, 28, F(40, 28, 7, C['navy_in'], glow=0.25, ornate=False, rim=0.8), 'panel', nine=(9, 9, 9, 9), note='列表列／設定列／任務列')
comp('panel_inset_sel', 40, 28, F(40, 28, 7, C['navy_in'], glow=1.3, ornate=False, rim=1.1), 'panel', nine=(9, 9, 9, 9), note='已選／可領取列（金光）')
comp('banner_event', 72, 36, F(72, 36, 10, C['navy'], glow=1.4, ornate=False), 'panel', nine=(12, 12, 12, 12), note='事件卡（P0-4：細橫幅 ≤1/6 屏）')
def handle(L, o):
    d = ImageDraw.Draw(L); d.rounded_rectangle([P(o - .6), P(o - .6), P(o + 22.6), P(o + 3.6)], radius=P(2.1), fill=C['line'])
    L.alpha_composite(K.vgrad((P(22), P(3)), [(0, C['g_hi']), (1, C['g_lo'])]), (P(o), P(o)))
comp('sheet_handle', 22, 3, handle, 'panel', note='bottom sheet 頂把手')
# ================= CARDS =================
comp('card', 36, 44, F(36, 44, 6, C['navy_in'], glow=0.5, ornate=False, rim=1.0), 'card', nine=(8, 8, 8, 8), note='圖鑑／收藏／小圃花卡')
comp('card_sel', 36, 44, F(36, 44, 6, C['navy_in'], glow=1.5, ornate=False, rim=1.3), 'card', nine=(8, 8, 8, 8), note='已選／新解鎖')
comp('card_locked', 36, 44, F(36, 44, 6, C['locked'], glow=0.15, ornate=False, rim=1.0), 'card', nine=(8, 8, 8, 8), note='未解鎖（提高對比：底較亮、字近白）')
def spot(colr, a):
    def fn(L, o):
        g = Image.new('L', L.size, 0); ImageDraw.Draw(g).ellipse([P(o), P(o), P(o + 24), P(o + 24)], fill=int(170 * a))
        put(L, solid(L.size, colr), gauss(g, P(3)))
    return fn
comp('card_spot', 24, 24, spot(C['cyan'], 1), 'card', note='卡內 icon 後光')
def qmark(L, o): gold_text(L, (P(o + 6), P(o + 8)), '?', 13, 'cin', glow=0.2, fill=[(0, LOCK_FG), (1, hx('#C9CEE6'))])
comp('card_qmark', 12, 16, qmark, 'card', note='未解鎖「?」')

# ================= BUTTONS =================
BTN_STROKE = {'pri': hx('#7A3A10'), 'sec': hx('#0F4A5E'), 'rose': hx('#7A1838'), 'violet': hx('#3A2470'), 'dis': None}
for kd in ('pri', 'sec', 'rose', 'violet', 'dis'):
    gl = 0 if kd == 'dis' else 1.0
    def mk(pressed, kd=kd, gl=gl):
        def fn(L, o):
            place(L, frame(44, 20, 8, C[kd], pressed=pressed, glow=gl, ornate=False, rim=1.1), P(o), P(o + (1.1 if pressed else 0)))
            if kd != 'dis' and not pressed: gem(L, P(o + 4.5), P(o + 3.2), 1.6, C['sec'], glow=True, star=True)
        return fn
    comp(f'btn_{kd}', 44, 20, mk(False), 'button', nine=(10, 0, 10, 0), note='主要／次要／危險／特別／停用' if kd == 'pri' else '')
    if kd != 'dis': comp(f'btn_{kd}_p', 44, 20, mk(True), 'button', nine=(10, 0, 10, 0), note='按下：下沉 1.1px、光減半、冇 sheen')
for kd in ('pri', 'sec', 'rose', 'dis'):
    comp(f'btn16_{kd}', 40, 16, F(40, 16, 7, C[kd], glow=0 if kd == 'dis' else 1.0, ornate=False, rim=1.0), 'button', nine=(8.5, 0, 8.5, 0), note='細掣 h16（4b「完成」同款）' if kd == 'pri' else '')
    if kd != 'dis': comp(f'btn16_{kd}_p', 40, 16, FP(40, 16, 7, C[kd], dy=0.9, glow=.5, ornate=False, rim=1.0), 'button', nine=(8.5, 0, 8.5, 0))
for nm, fill, gl in (('subtab', C['navy_in'], .3), ('subtab_on', C['pri'], 1.0)):
    comp(nm, 32, 15, F(32, 15, 7, fill, glow=gl, ornate=False, rim=0.9), 'button', nine=(8, 0, 8, 0), note='手帳子分頁／細掣')
comp('subtab_p', 32, 15, FP(32, 15, 7, C['navy_in'], dy=0.8, glow=.2, ornate=False, rim=0.9), 'button', nine=(8, 0, 8, 0))

# ================= MEDALLIONS =================
def med(d, fill, pressed=False, glow=1.0):
    def fn(L, o): medallion(L, P(o + d / 2), P(o + d / 2), d, fill, pressed=pressed, glow=glow)
    return fn
MEDS = [(28, ['pri', 'rose', 'sec', 'violet', 'dis'], True), (34, ['pri'], False), (30, ['pri'], True), (24, ['navy', 'pri', 'rose', 'dis'], True),
        (25, ['pri'], False), (22, ['navy'], True), (20, ['pri'], False), (18, ['navy_in'], False), (16, ['navy', 'pri'], False),
        (19, ['paper', 'navy', 'pri', 'sec', 'violet'], False), (11, ['navy'], False), (26, ['paper', 'violet'], False)]
for d, fills, pr in MEDS:
    for f in fills:
        gl = 0 if f == 'dis' else (0.5 if d <= 13 else 0.25 if f == 'navy_in' else 1.0)
        comp(f'med{d}_{f}', d, d, med(d, C[f], glow=gl), 'medallion', note='停用／上鎖圓章（part 2；icon α.55＋ic:lock 右下）' if f == 'dis' else '圓章底（icon 另疊）')
        if pr and f != 'dis': comp(f'med{d}_{f}_p', d, d, med(d, C[f], True, gl), 'medallion', note='按下（已含 0.9px 下沉）')

def close(pressed):
    def fn(L, o):
        cx, cy = P(o + 7.5), P(o + 7.5 + (0.9 if pressed else 0))
        medallion(L, P(o + 7.5), P(o + 7.5), 15, C['rose'], pressed=pressed, glow=0.8)
        dd = ImageDraw.Draw(L)
        for cfill, wd in ((hx('#5A0F2A'), 2.6), (hx('#FFFFFF'), 1.5)):
            for s in (1, -1): dd.line([(cx - P(2.7), cy - P(2.7 * s)), (cx + P(2.7), cy + P(2.7 * s))], fill=cfill, width=P(wd))
    return fn
comp('close', 15, 15, close(False), 'button', note='P1-1：✕ 放面板內右上；觸控區 ≥24×24 art')
comp('close_p', 15, 15, close(True), 'button')
def plus(pressed):
    def fn(L, o):
        medallion(L, P(o + 4), P(o + 4), 8, C['pri'], pressed=pressed, glow=0.4)
        text(L, (P(o + 4), P(o + 3.8 + (0.9 if pressed else 0))), '+', 6.6, hx('#FFFFFF'), 'fred', stroke=0.6, stroke_col=hx('#7A3A10'))
    return fn
comp('chip_plus', 8, 8, plus(False), 'hud'); comp('chip_plus_p', 8, 8, plus(True), 'hud')

# ================= HUD =================
comp('nameplate', 92, 20, F(92, 20, 8, C['navy'], glow=0.7, ornate=False), 'hud', nine=(10, 0, 10, 0), note='頂左名牌（瘦身 h20；頭像用 med19_paper）')
comp('stage_tag', 22, 10, F(22, 10, 4.5, C['violet'], glow=0, ornate=False, rim=0.6), 'hud', nine=(5.5, 0, 5.5, 0), note='階段（幼崽…）字 7.0 sans')
comp('chip', 36, 16, F(36, 16, 8, C['navy'], glow=0.6, ornate=False, rim=1.0), 'hud', nine=(9, 0, 9, 0), note='貨幣 chip（光粒／星星碎）')
def trough(w, h, r, glow=.4, groove=None):
    def fn(L, o):
        place(L, frame(w, h, r, C['navy_in'], glow=glow, ornate=False, rim=0.8), P(o), P(o))
        if groove:
            gx0, gy0, gx1, gy1, gr = groove
            ImageDraw.Draw(L).rounded_rectangle([P(o + gx0), P(o + gy0), P(o + gx1), P(o + gy1)], radius=P(gr), fill=hx('#0B0E24'))
    return fn
comp('need_trough', 44, 10, trough(44, 10, 5, .35, (10, 2.6, 41.8, 7.4, 2.4)), 'hud', nine=(12.5, 0, 3.5, 0), note='需要值槽（瘦身 h10）；左 10 art 為 icon 位（med11_navy）；色條 y+3')
def fillbar(w, h, c0, c1, r):
    def fn(L, o):
        seg = vgrad((P(w), P(h)), [(0, mix(c0, hx('#FFFFFF'), .35)), (0.5, c0), (1, c1)])
        mk = Image.new('L', seg.size, 0); ImageDraw.Draw(mk).rounded_rectangle([0, 0, seg.width - 1, seg.height - 1], radius=P(r), fill=255)
        seg.putalpha(mk); L.alpha_composite(seg, (P(o), P(o)))
        ed = ImageChops.subtract(mk, ImageChops.offset(mk, 0, -P(0.5))); edl = Image.new('L', L.size, 0); edl.paste(ed, (P(o), P(o)))
        put(L, solid(L.size, mix(c1, hx('#000000'), .45)), edl)   # dark lower lip = contrast vs groove
        hl = Image.new('L', L.size, 0); ImageDraw.Draw(hl).rounded_rectangle([P(o + r * .6), P(o + .5), P(o + w - r * .6), P(o + h * .38)], radius=P(r * .4), fill=110)
        put(L, solid(L.size, hx('#FFFFFF')), hl)
    return fn
NEED_COL['low'] = (hx('#FFB0A0'), hx('#F0303C'))
for nk, (c0, c1) in NEED_COL.items():
    comp(f'need_fill_{nk}', 24, 4, fillbar(24, 4, c0, c1, 2), 'hud', nine=(2.2, 0, 2.2, 0), note='飽腹/心情/清潔/精力 色條', bloom=False)
def tip(colr):
    def fn(L, o):
        g = Image.new('L', L.size, 0); ImageDraw.Draw(g).ellipse([P(o), P(o), P(o + 4), P(o + 6)], fill=230)
        put(L, solid(L.size, mix(colr, hx('#FFFFFF'), .6)), gauss(g, P(1.0)))
    return fn
comp('bar_tip', 4, 6, tip(hx('#FFE6A8')), 'hud', note='進度條尖端光（engine 可 tint）', bloom=False)
comp('exp_trough', 40, 5, trough(40, 5, 2.5, 0.2), 'hud', nine=(3.4, 0, 3.4, 0), note='名牌經驗條／家族經驗條')
comp('exp_fill', 24, 3, fillbar(24, 3, C['g_hi'], hx('#E59A3E'), 1.5), 'hud', nine=(1.6, 0, 1.6, 0), bloom=False)
def mgem(fill, glow):
    def fn(L, o): gem(L, P(o + 2), P(o + 2), 1.5, fill, glow=glow, star=False)
    return fn
comp('exp_gem_on', 4, 4, mgem(C['sec'], True), 'hud', note='P2-3 里程碑（已達）')
comp('exp_gem_off', 4, 4, mgem(C['dis'], False), 'hud', note='P2-3 里程碑（未達）')
comp('prog_trough', 40, 6, trough(40, 6, 3, 0.15), 'hud', nine=(3.6, 0, 3.6, 0), note='任務／小遊戲進度')
comp('prog_fill_teal', 24, 4, fillbar(24, 4, hx('#C8F7EE'), hx('#3797B4'), 2), 'hud', nine=(2.2, 0, 2.2, 0), bloom=False)
comp('prog_fill_gold', 24, 4, fillbar(24, 4, C['g_hi'], hx('#E59A3E'), 2), 'hud', nine=(2.2, 0, 2.2, 0), bloom=False)

# ================= DOCK =================
comp('dock_bar', 80, 34, F(80, 34, 12, C['navy'], glow=1.0, ornate=True), 'dock', nine=(14, 0, 14, 0), note='P0-2 底部 5 分頁（瘦身 h34）')
def pillar(L, o):
    g = Image.new('L', L.size, 0); ImageDraw.Draw(g).rounded_rectangle([P(o), P(o), P(o + 26), P(o + 36)], radius=P(12), fill=150)
    put(L, solid(L.size, C['glow']), gauss(g, P(4)))
comp('dock_pillar', 26, 36, pillar, 'dock', pad=14, note='已選分頁光柱；opacity 動畫', bloom=False)
def divider_v(L, o): ImageDraw.Draw(L).line([(P(o), P(o)), (P(o), P(o + 20))], fill=hx('#F2C46A', 90), width=P(0.4))
comp('dock_div', 1, 20, divider_v, 'dock', bloom=False)
def gem_s(fill, R, glow=True, star=True):
    def fn(L, o): gem(L, P(o + R * 1.3), P(o + R * 1.3), R, fill, glow=glow, star=star)
    return fn
comp('dock_gem', 5.2, 5.2, gem_s(C['gem'], 2.0), 'dock', note='已選分頁底寶石')
comp('label_plate', 28, 10, F(28, 10, 5, C['navy'], glow=0.4, ornate=False, rim=0.8), 'hud', nine=(6, 0, 6, 0), note='動作掣字牌／樹節點名牌')
for kd in ('pri', 'sec', 'dis', 'rose', 'navy'):
    comp(f'pill_{kd}', 40, 11, F(40, 11, 5.5, C[kd], glow=0 if kd == 'dis' else .5, ornate=False, rim=.8), 'button', nine=(6.5, 0, 6.5, 0), note='卡底 pill（4b「擺緊／擺上去／價錢」同款）' if kd == 'pri' else '')

# ================= BADGES / TOAST / BUBBLE =================
def rdot(n):
    def fn(L, o):
        R = 3.9 if n else 2.9
        K.red_dot(L, P(o + R), P(o + R), None)
        if n:   # re-draw larger gem without number (number from font_round)
            pass
    return fn
def rdot2(R):
    def fn(L, o):
        cx = cy = P(o + R); W, H = L.size
        g = Image.new('L', (W, H), 0); ImageDraw.Draw(g).ellipse([cx - P(R + 2.2), cy - P(R + 2.2), cx + P(R + 2.2), cy + P(R + 2.2)], fill=200)
        put(L, solid((W, H), hx('#FF7A90')), gauss(g, P(1.5)))
        d = ImageDraw.Draw(L)
        for rr, cl in [(R + 1.25, C['line']), (R + 0.85, C['g_mid']), (R + 0.2, C['line'])]:
            d.ellipse([cx - P(rr), cy - P(rr), cx + P(rr), cy + P(rr)], fill=cl)
        gl = vgrad((P(R * 2) + 1, P(R * 2) + 1), [(0, hx('#FF9AAE')), (1, hx('#C8204A'))])
        mk = Image.new('L', gl.size, 0); ImageDraw.Draw(mk).ellipse([0, 0, gl.width - 1, gl.height - 1], fill=255)
        gl.putalpha(mk); L.alpha_composite(gl, (int(cx - P(R)), int(cy - P(R))))
        d.ellipse([cx - P(R * .62), cy - P(R * .72), cx - P(R * .02), cy - P(R * .28)], fill=hx('#FFFFFF', 210))
    return fn
comp('red_dot', 5.8, 5.8, rdot2(2.9), 'badge', note='紅點（冇數字）')
comp('red_dot_num', 8.4, 8.4, rdot2(4.2), 'badge', note='紅點＋數字（數字用 font_round 6）')
comp('toast', 72, 18, F(72, 18, 9, C['navy'], glow=1.2, ornate=False, rim=1.1), 'toast', nine=(10, 0, 10, 0), note='toast 底（左 icon 用 med19_pri）')
def wing(sx):
    def fn(L, o):
        g = Image.new('L', L.size, 0)
        pts = [(P(o + (0 if sx > 0 else 26)), P(o)), (P(o + (26 if sx > 0 else 0)), P(o + 3)), (P(o + (0 if sx > 0 else 26)), P(o + 6))]
        ImageDraw.Draw(g).polygon(pts, fill=180); put(L, solid(L.size, C['glow']), gauss(g, P(1.2)))
    return fn
comp('toast_wing_r', 26, 6, wing(1), 'toast', note='toast 兩邊光束；pivot=接 toast 邊', bloom=False)
comp('toast_wing_l', 26, 6, wing(-1), 'toast', bloom=False)
comp('bubble', 40, 22, F(40, 22, 8, C['paper'], glow=0.7, ornate=False, rim=0.9), 'bubble', nine=(10, 10, 10, 10), note='寵物說話泡泡（字 ink 7.6 sans）')
def btail(L, o):
    d = ImageDraw.Draw(L); tx, ty = P(o + 1.6), P(o)
    d.polygon([(tx - P(1.6), ty), (tx + P(8.6), ty), (tx - P(1.6), ty + P(8.6))], fill=C['line'])
    d.polygon([(tx - P(0.6), ty - P(0.6)), (tx + P(7.0), ty - P(0.6)), (tx - P(0.6), ty + P(7.0))], fill=C['g_mid'])
    d.polygon([(tx + P(0.4), ty - P(1.2)), (tx + P(5.4), ty - P(1.2)), (tx + P(0.4), ty + P(5.0))], fill=C['paper'][1])
comp('bubble_tail', 10, 8.6, btail, 'bubble', note='泡泡尾；box 左上 = 泡泡底邊 x+7.4', pivot=None, bloom=False)
def thought(L, o):
    for (x, y, r) in ((1.8, 7.0, 1.8), (6.0, 3.4, 2.4)):
        place(L, frame(r * 2, r * 2, r, C['paper'], glow=0.4, ornate=False, rim=0.6), P(o + x - r), P(o + y - r))
comp('thought_dots', 9, 10, thought, 'bubble', note='心聲泡泡（P1-2：同 bubble 合併做雲朵款）')
def plq(L, o):
    place(L, frame(64, 17, 6, C['violet'], glow=1.0, ornate=False, rim=1.1), P(o), P(o))
comp('plaque', 64, 17, plq, 'title', nine=(8, 0, 8, 0), note='彈窗標題緞帶（字 serif 9.2）')
comp('plaque_pri', 64, 17, F(64, 17, 6, C['pri'], glow=1.0, ornate=False, rim=1.1), 'title', nine=(8, 0, 8, 0), note='獎勵／升級標題')
def ptail(sx, fill):
    def fn(L, o):
        W, H = L.size; tl = Image.new('L', (W, H), 0)
        x0 = o + (0 if sx > 0 else 13); x1 = o + (13 if sx > 0 else 0)
        ImageDraw.Draw(tl).polygon([(P(x0), P(o)), (P(x1), P(o)), (P(x1 - sx * 3.5), P(o + 5.5)), (P(x1), P(o + 11)), (P(x0), P(o + 11))], fill=255)
        put(L, solid((W, H), C['line']), k.dilate(tl, P(0.7)))
        put(L, vgrad((W, H), [(0, mix(fill[1], hx('#000000'), .2)), (1, mix(fill[1], hx('#000000'), .45))]), tl)
    return fn
comp('plaque_tail_r', 13, 11, ptail(1, C['violet']), 'title', note='放 plaque 右邊 x=w-4, y=+4', bloom=False)
comp('plaque_tail_l', 13, 11, ptail(-1, C['violet']), 'title', bloom=False)
comp('plaque_gem', 7.8, 7.8, gem_s(C['gem'], 3.0), 'title', note='標題頂寶石（y-1）')

# ================= CONTROLS =================
def tgl_track(on):
    return F(26, 13, 6.5, C['sec'] if on else C['navy_in'], glow=0.6 if on else 0.2, ornate=False, rim=0.9)
comp('toggle_track_on', 26, 13, tgl_track(True), 'control', note='開關軌（knob 另疊，可郁）')
comp('toggle_track_off', 26, 13, tgl_track(False), 'control')
def knob(on):
    def fn(L, o):
        medallion(L, P(o + 5.5), P(o + 5.5), 11, C['paper'], glow=0.5)
        gem(L, P(o + 5.5), P(o + 5.5), 1.8, C['pri'] if on else C['dis'], glow=False, star=False)
    return fn
comp('toggle_knob_on', 11, 11, knob(True), 'control', note='knob 中心：on x=w-6.5 / off x=6.5')
comp('toggle_knob_off', 11, 11, knob(False), 'control')
def cbox(on):
    def fn(L, o):
        place(L, frame(12, 12, 3.2, C['pri'] if on else C['navy_in'], glow=0.8 if on else 0.2, ornate=False, rim=0.9), P(o), P(o))
        if on:
            d = ImageDraw.Draw(L)
            pts = [(P(o + 2.8), P(o + 6.2)), (P(o + 5.2), P(o + 8.6)), (P(o + 9.4), P(o + 3.4))]
            d.line(pts, fill=hx('#5A2A08'), width=P(2.4), joint='curve'); d.line(pts, fill=hx('#FFFFFF'), width=P(1.3), joint='curve')
    return fn
comp('check_off', 12, 12, cbox(False), 'control', note='任務 checkbox')
comp('check_on', 12, 12, cbox(True), 'control')
comp('seg_bg', 48, 16, F(48, 16, 8, C['navy_in'], glow=0.25, ornate=False, rim=0.9), 'control', nine=(9, 0, 9, 0), note='分段選項底（畫質 4／音量 3／早瞓 5）')
comp('seg_on', 24, 12, F(24, 12, 6, C['pri'], glow=0.9, ornate=False, rim=0.8), 'control', nine=(7, 0, 7, 0), note='分段已選 pill（滑動）')
comp('seg_div', 1, 8, lambda L, o: ImageDraw.Draw(L).line([(P(o), P(o)), (P(o), P(o + 8))], fill=hx('#F2C46A', 110), width=P(0.4)), 'control', bloom=False)
comp('slider_track', 40, 8, trough(40, 8, 4, 0.2), 'control', nine=(5, 0, 5, 0), note='（備用）連續音量')
comp('scroll_track', 4, 30, lambda L, o: ImageDraw.Draw(L).rounded_rectangle([P(o), P(o), P(o + 4), P(o + 30)], radius=P(2), fill=hx('#0B0E24', 200)), 'control', nine=(0, 3, 0, 3), slice_='3v', bloom=False)
def thumb(L, o):
    d = ImageDraw.Draw(L); d.rounded_rectangle([P(o - .4), P(o - .4), P(o + 4.4), P(o + 16.4)], radius=P(2.2), fill=C['line'])
    L.alpha_composite(vgrad((P(4), P(16)), [(0, C['g_hi']), (1, C['g_lo'])]), (P(o), P(o)))
    mk = Image.new('L', L.size, 0)
def sfade(top):
    def fn(L, o):
        W, H = L.size; h = P(10); x0, y0 = P(o), P(o)
        ys = np.linspace(0, 1, h)[:, None] if top else np.linspace(1, 0, h)[:, None]
        a = (np.clip(1 - ys, 0, 1) ** 1.5 * 235).astype(np.uint8)
        arr = np.zeros((h, P(40), 4), np.uint8); arr[..., :3] = C['navy'][1][:3]; arr[..., 3] = np.repeat(a, P(40), 1)
        L.alpha_composite(Image.fromarray(arr, 'RGBA'), (x0, y0))
        ly = y0 if top else y0 + h - P(0.6)
        g = Image.new('L', (W, H), 0); ImageDraw.Draw(g).rectangle([x0 + P(3), ly, x0 + P(37), ly + P(0.6)], fill=150)
        put(L, solid((W, H), C['glow']), gauss(g, P(0.6)))
    return fn
comp('scroll_fade_top', 40, 10, sfade(True), 'control', nine=(4, 0, 4, 0), note='part 2：捲動列表頂邊淡出（列表可再上捲先顯示；clip 內最上）', bloom=False)
comp('scroll_fade_bot', 40, 10, sfade(False), 'control', nine=(4, 0, 4, 0), note='part 2：捲動列表底邊淡出（仲有內容喺下面）', bloom=False)
def sglow(top):
    def fn(L, o):
        W, H = L.size; g = Image.new('L', (W, H), 0)
        cy = o if top else o + 8
        ImageDraw.Draw(g).ellipse([P(o + 2), P(cy - 6), P(o + 38), P(cy + 6)], fill=200)
        m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).rectangle([P(o), P(o), P(o + 40), P(o + 8)], fill=255)
        put(L, solid((W, H), C['glow']), ImageChops.multiply(gauss(g, P(2.2)), m))
        put(L, solid((W, H), hx('#FFFFFF', 200)), ImageChops.multiply(amul(gauss(g, P(0.8)), .35), m))
    return fn
comp('scroll_glow_top', 40, 8, sglow(True), 'fx', nine=(8, 0, 8, 0), note='part 2：overscroll 金光（拉過頂；α=拉距/24，放手 200ms 淡走）', bloom=False)
comp('scroll_glow_bot', 40, 8, sglow(False), 'fx', nine=(8, 0, 8, 0), note='part 2：overscroll 金光（拉過底）', bloom=False)
comp('scroll_thumb', 4, 16, thumb, 'control', nine=(0, 3, 0, 3), slice_='3v', note='捲動拇指（金）')
def divider(L, o):
    d = ImageDraw.Draw(L); d.line([(P(o), P(o + 2)), (P(o + 40), P(o + 2))], fill=C['line'], width=P(1.2))
    d.line([(P(o), P(o + 2)), (P(o + 40), P(o + 2))], fill=C['g_mid'], width=P(0.5))
comp('divider', 40, 4, divider, 'control', nine=(2, 0, 2, 0), note='金分隔線（中間可疊 dock_gem）', bloom=False)
def star(on):
    def fn(L, o):
        pts = [(P(o + 4.5 + x - 12) , P(o + 4.5 + y - 12)) for x, y in []]
        sp = k.star_pts(P(o + 4.5), P(o + 4.8), P(4.6), P(2.2))
        d = ImageDraw.Draw(L)
        sp2 = k.star_pts(P(o + 4.5), P(o + 4.8), P(5.4), P(2.8)); d.polygon(sp2, fill=C['line'])
        L2 = Image.new('L', L.size, 0); ImageDraw.Draw(L2).polygon(sp, fill=255)
        put(L, vgrad(L.size, [(0, C['g_hi']), (1, hx('#E59A3E'))]) if on else vgrad(L.size, [(0, hx('#6A7098')), (1, hx('#454B72'))]), L2)
        if on:
            g = gauss(L2, P(1.2)); put(L, solid(L.size, C['glow']), amul(g, .5))
    return fn
comp('star_on', 9, 9, star(True), 'control', note='小遊戲評分 ★')
comp('star_off', 9, 9, star(False), 'control')
comp('stamp_done', 16, 16, med(16, (hx('#C9F7DA'), hx('#3FA86E')), glow=1.0), 'control', note='「完成」印章底（疊 check icon）')
comp('timeline_dot', 6.5, 6.5, gem_s(C['sec'], 2.5), 'control', note='日記時間軸點')
comp('timeline_line', 2, 12, lambda L, o: ImageDraw.Draw(L).rectangle([P(o + .6), P(o), P(o + 1.4), P(o + 12)], fill=hx('#F2C46A', 150)), 'control', nine=(0, 2, 0, 2), slice_='3v', bloom=False)
def chevron(L, o):
    d = ImageDraw.Draw(L)
    for wd, cl in ((3.4, C['line']), (1.8, C['g_hi'])):
        d.line([(P(o + 1), P(o + 1.5)), (P(o + 5), P(o + 5.5)), (P(o + 9), P(o + 1.5))], fill=cl, width=P(wd), joint='curve')
    g = Image.new('L', L.size, 0); ImageDraw.Draw(g).ellipse([P(o - 1), P(o - 2), P(o + 11), P(o + 8)], fill=120); put(L, solid(L.size, C['glow']), gauss(g, P(1.6)))
comp('hint_arrow', 10, 7, chevron, 'fx', note='教學指示（「輕點光卵」上下 bob）')

# ================= FX =================
def ripple(L, o):
    W, H = L.size; m = Image.new('L', (W, H), 0); d = ImageDraw.Draw(m)
    d.ellipse([P(o), P(o), P(o + 30), P(o + 30)], fill=255); d.ellipse([P(o + 2.2), P(o + 2.2), P(o + 27.8), P(o + 27.8)], fill=0)
    put(L, solid((W, H), C['glow']), gauss(m, P(0.8))); put(L, solid((W, H), hx('#FFFFFF', 200)), amul(m, .6))
comp('fx_ripple', 30, 30, ripple, 'fx', note='按掣漣漪（scale 0.4→1.2，α 1→0）', bloom=False)
def spark(L, o):
    pts = [(P(o + 5 + (5 if i % 2 == 0 else 1.2) * math.cos(math.radians(-90 + i * 45))), P(o + 5 + (5 if i % 2 == 0 else 1.2) * math.sin(math.radians(-90 + i * 45)))) for i in range(8)]
    m = Image.new('L', L.size, 0); ImageDraw.Draw(m).polygon(pts, fill=255)
    put(L, solid(L.size, C['glow']), gauss(m, P(1.0))); put(L, solid(L.size, hx('#FFFFFF')), m)
comp('fx_spark', 10, 10, spark, 'fx', note='四角星閃（領取／升級）', bloom=False)
def mote(L, o):
    g = Image.new('L', L.size, 0); ImageDraw.Draw(g).ellipse([P(o + 1), P(o + 1), P(o + 5), P(o + 5)], fill=255)
    put(L, solid(L.size, C['glow']), gauss(g, P(1.0))); put(L, solid(L.size, hx('#FFFFFF')), amul(gauss(g, P(.3)), .8))
comp('fx_mote', 6, 6, mote, 'fx', note='光塵（彈窗開／轉場）', bloom=False)
def sweep(L, o):
    g = Image.new('L', L.size, 0); ImageDraw.Draw(g).polygon([(P(o + 10), P(o)), (P(o + 22), P(o)), (P(o + 12), P(o + 40)), (P(o), P(o + 40))], fill=150)
    put(L, solid(L.size, hx('#FFFFFF')), gauss(g, P(1.6)))
comp('fx_sweep', 22, 40, sweep, 'fx', note='金光掃過（掣／卡；source-atop）', bloom=False)
def veil(L, o):
    W, H = L.size; yy, xx = np.mgrid[0:H, 0:W]; cx = cy = P(o + 32); r = np.hypot(xx - cx, yy - cy) / P(32)
    a = np.clip(1 - r, 0, 1) ** 1.6 * 255
    arr = np.zeros((H, W, 4), np.uint8); arr[..., 0], arr[..., 1], arr[..., 2] = 255, 236, 190; arr[..., 3] = a.astype(np.uint8)
    L.alpha_composite(Image.fromarray(arr, 'RGBA'))
comp('fx_veil', 64, 64, veil, 'fx', note='轉場光幕（scale 0→9 由分頁位置擴散）', bloom=False)

# ================= STUBS 4b / 5a =================
def crest(L, o):
    W, H = L.size
    for sx in (-1, 1):
        wm = Image.new('L', (W, H), 0); cx = o + 22
        pts = [(cx + sx * 12, o + 12), (cx + sx * 22, o + 6), (cx + sx * 19, o + 15), (cx + sx * 22, o + 20), (cx + sx * 12, o + 26)]
        ImageDraw.Draw(wm).polygon([(P(x), P(y)) for x, y in pts], fill=255)
        put(L, solid((W, H), C['line']), k.dilate(wm, P(.7))); put(L, K.gold_grad((W, H)), wm)
    medallion(L, P(o + 22), P(o + 18), 30, C['violet'], glow=1.3)
    gem(L, P(o + 22), P(o + 2.6), 2.8, C['gem'])
comp('family_crest', 44, 34, crest, 'stub_5a', stub=True, note='5a 家族等級徽（中間疊 font_gold 等級數字）')
comp('tree_node', 26, 26, med(26, C['paper']), 'stub_5a', stub=True, note='5a 族譜節點（頭像）')
comp('tree_node_sel', 26, 26, med(26, C['pri'], glow=1.5), 'stub_5a', stub=True)
def tline(horiz):
    def fn(L, o):
        d = ImageDraw.Draw(L)
        if horiz:
            d.rectangle([P(o), P(o + .2), P(o + 12), P(o + 1.8)], fill=C['line']); d.rectangle([P(o), P(o + .6), P(o + 12), P(o + 1.4)], fill=C['g_mid'])
        else:
            d.rectangle([P(o + .2), P(o), P(o + 1.8), P(o + 12)], fill=C['line']); d.rectangle([P(o + .6), P(o), P(o + 1.4), P(o + 12)], fill=C['g_mid'])
    return fn
comp('tree_line_h', 12, 2, tline(True), 'stub_5a', nine=(2, 0, 2, 0), stub=True, bloom=False)
comp('tree_line_v', 2, 12, tline(False), 'stub_5a', nine=(0, 2, 0, 2), slice_='3v', stub=True, bloom=False)
comp('tree_joint', 6.5, 6.5, gem_s(C['pri'], 2.5), 'stub_5a', stub=True, note='族譜連線交點')

# ================= ICONS =================
BASE_ICONS = ['feed', 'clean', 'sleep', 'light', 'star', 'gift', 'sprout', 'play', 'book', 'gear', 'heart',
              'heart_bunny', 'play_cat', 'book_bear', 'gear_chick', 'd_star', 'd_heart', 'd_spark', 'd_leaf', 'd_paw', 'd_cloud']
ICONS = BASE_ICONS + list(I.EXTRA)
ICON_NOTE = {'feed': '餵食／飽腹', 'clean': '清潔', 'sleep': '瞓覺／精力／關燈', 'light': '光粒貨幣', 'star': '星星碎貨幣',
             'gift': '委託／禮物', 'sprout': '小圃分頁', 'play': '球（舊）', 'book': '書（舊）', 'gear': '齒輪（舊）', 'heart': '心（舊）',
             'heart_bunny': '照顧分頁／心情', 'play_cat': '玩分頁／玩耍', 'book_bear': '手帳分頁', 'gear_chick': '設定分頁',
             'dex': '圖鑑', 'diary': '日記', 'bond': '親密', 'surprise': '小驚喜', 'minigame': '小遊戲', 'cabinet': '收藏', 'badge': '徽章',
             'mail': '📬 通知佇列（P0-1）', 'info': 'ⓘ 規則', 'lock': '鎖', 'check': '完成', 'sound': '聲音', 'quality': '畫質',
             'water': '飲水提醒', 'bedtime': '早瞓時間', 'reset': '重設', 'hint': '提示', 'mg_tease': '逗玩', 'mg_stardust': '接星屑',
             'mg_leaf': '彈彈葉', 'mg_hide': '花園捉迷藏', 'mg_firefly': '追螢火', 'ev_treasure': '尋寶事件', 'seed': '種子',
             'house': '4b 屋仔', 'decorate': '4b 佈置', 'furniture': '4b 傢俬', 'rotate': '4b 轉向', 'flip': '4b 鏡像', 'store': '4b 收起',
             'family_tree': '5a 族譜', 'family_level': '5a 家族等級', 'back': '返回（part 2）', 'plus': '加／空 slot（part 2）', 'clear': '清空／收起（part 2）'}
def hd_icon(kind):
    base = k.icon(K.HD_TH, kind)            # P(30) canvas, 24-art icon centred
    W0 = base.width; pad = P(3); W = W0 + 2 * pad
    b = Image.new('RGBA', (W, W), (0, 0, 0, 0)); b.alpha_composite(base, (pad, pad))
    a = b.getchannel('A').point(lambda v: 255 if v > 90 else int(v * 2.8))
    ring = k.dilate(a, P(0.75)); outer = k.dilate(ring, P(0.55))
    out = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    put(out, solid((W, W), C['glow']), amul(gauss(outer, P(1.6)), 0.6))
    put(out, solid((W, W), C['line']), outer); put(out, K.gold_grad((W, W)), ring)
    out.alpha_composite(b)
    rim = ImageChops.subtract(a, ImageChops.offset(a, P(0.7), P(0.7))); put(out, solid((W, W), hx('#FFFFFF', 140)), rim)
    return out.reduce(2)                     # 3x: 36 art canvas -> 108 px; logical 24 art = 72 px at (18,18)
ICO = {}
for kd in ICONS:
    im = hd_icon(kd)
    a = np.asarray(im)[..., 3]; ys, xs = np.where(a > 3)
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    im = im.crop((x0, y0, x1, y1))
    ICO[kd] = dict(img=im, box=[int(18 - x0), int(18 - y0), 72, 72], art=[24, 24], note=ICON_NOTE.get(kd, ''),
                   stub=kd in ('house', 'decorate', 'furniture', 'rotate', 'flip', 'store', 'family_tree', 'family_level'))
    im.save(f'{OUT}/icons/ic_{kd}@3x.png')

# ================= LABELS (static CJK, pre-rendered; dynamic text = fillText, see UI_KIT.md) =================
LAB = []
def lab(key, s, kind, size, fg, stroke, scol, glow=0.0, use=''):
    LAB.append((key, s, kind, size, fg, stroke, scol, glow, use))
for s in ('今日委託', '設定', '手帳', '圖鑑', '日記', '親密', '小驚喜', '小遊戲', '小圃', '收藏', '徽章', '玩耍', '屋仔佈置', '家族樹', '升級啦'):
    lab(f'title_{s}', s, 'serif', 9.2, hx('#FFFFFF'), 1.1, hx('#2E1A52'), .35, '標題（serif ≥9）')
for s in ('照顧', '玩', '小圃', '手帳', '設定'):
    lab(f'tab_{s}', s, 'sans', 7.2, hx('#EFE6D0'), 0.8, hx('#141834'), 0, '分頁未選')
    lab(f'tab_on_{s}', s, 'sans', 7.8, hx('#FFFFFF'), 1.0, hx('#6A3410'), .6, '分頁已選')
for s in ('餵食', '玩耍', '清潔', '瞓覺', '關燈'):
    lab(f'act_{s}', s, 'sans', 7.2, C['cream'], 0.8, hx('#141834'), 0, '動作掣字牌')
for kd, ss in (('pri', ('好呀', '確定', '領取', '全部領取', '去完成', '開始', '完成', '擺上去')), ('sec', ('遲啲先', '取消', '關閉', '返回', '擺緊')), ('rose', ('重設', '刪除')), ('violet', ('佈置', '升級'))):
    for s in ss: lab(f'btn_{kd}_{s}', s, 'sans', 9.0, hx('#FFFFFF'), 1.0, BTN_STROKE[kd], 0, f'btn_{kd} 字')
for kd, ss in (('pri', ('擺上去',)), ('sec', ('擺緊',)), ('navy', ('清空',))):
    for s in ss: lab(f'pill_{kd}_{s}', s, 'sans', 7.6, hx('#FFFFFF'), 0.9, BTN_STROKE.get(kd) or hx('#141834'), 0, f'pill_{kd} 字（part 2，4b 卡）')
lab('pill_dis_委託獎', '委託獎', 'sans', 7.6, INK_DIS, 0, None, 0, 'pill_dis 字（深字冇描邊）')
lab('pill_dis_訪客禮', '訪客禮', 'sans', 7.6, INK_DIS, 0, None, 0, 'pill_dis 字')
for s in ('佈置', '屋仔', '委託'):
    lab(f'act_{s}', s, 'sans', 7.2, C['cream'], 0.8, hx('#141834'), 0, '圓章下字牌（part 2）')
lab('title_佈置屋仔', '佈置屋仔', 'serif', 9.2, hx('#FFFFFF'), 1.1, hx('#2E1A52'), .35, '4b 佈置模式標題')
lab('title_屋仔', '屋仔', 'serif', 9.2, hx('#FFFFFF'), 1.1, hx('#2E1A52'), .35, '4b 屋內標題')
for s in ('未解鎖', '未完成'):
    lab(f'btn_dis_{s}', s, 'sans', 9.0, INK_DIS, 0, None, 0, 'btn_dis 字（深字冇描邊）')
for s in ('飽腹', '心情', '清潔', '精力'):
    lab(f'need_{s}', s, 'sans', 7.0, C['cream'], 0.8, hx('#141834'), 0, '需要值名（長按提示）')
LBL = {}
for key, s, kind, size, fg, stroke, scol, glow, use in LAB:
    f = K.font(kind, size); bb = f.getbbox(s, anchor='mm', stroke_width=P(stroke))
    w = (bb[2] - bb[0]) / 6 + 4; h = (bb[3] - bb[1]) / 6 + 3
    def fn(L, o, s=s, kind=kind, size=size, fg=fg, stroke=stroke, scol=scol, glow=glow, w=w, h=h):
        text(L, (P(o + w / 2), P(o + h / 2)), s, size, fg, kind, stroke=stroke, stroke_col=scol, glow=glow)
    e = comp('lbl_' + key, round(w, 2), round(h, 2), fn, 'label', pad=4, bloom=False)
    REG.pop('lbl_' + key); e.update(text=s, font=kind, size=size, use=use); LBL['lbl_' + key] = e

# ================= BITMAP FONTS =================
PX5 = {
 '0': [" ### ","#   #","#   #","#   #","#   #","#   #"," ### "], '1': ["  #  "," ##  ","  #  ","  #  ","  #  ","  #  "," ### "],
 '2': [" ### ","#   #","    #","   # ","  #  "," #   ","#####"], '3': ["#####","   # ","  #  ","   # ","    #","#   #"," ### "],
 '4': ["   # ","  ## "," # # ","#  # ","#####","   # ","   # "], '5': ["#####","#    ","#### ","    #","    #","#   #"," ### "],
 '6': ["  ## "," #   ","#    ","#### ","#   #","#   #"," ### "], '7': ["#####","    #","   # ","  #  "," #   "," #   "," #   "],
 '8': [" ### ","#   #","#   #"," ### ","#   #","#   #"," ### "], '9': [" ### ","#   #","#   #"," ####","    #","   # "," ##  "],
 'A': [" ### ","#   #","#   #","#####","#   #","#   #","#   #"], 'B': ["#### ","#   #","#   #","#### ","#   #","#   #","#### "],
 'C': [" ### ","#   #","#    ","#    ","#    ","#   #"," ### "], 'D': ["#### ","#   #","#   #","#   #","#   #","#   #","#### "],
 'E': ["#####","#    ","#    ","#### ","#    ","#    ","#####"], 'F': ["#####","#    ","#    ","#### ","#    ","#    ","#    "],
 'G': [" ### ","#   #","#    ","# ###","#   #","#   #"," ####"], 'H': ["#   #","#   #","#   #","#####","#   #","#   #","#   #"],
 'I': ["###"," # "," # "," # "," # "," # ","###"], 'J': ["  ###","   # ","   # ","   # ","   # ","#  # "," ##  "],
 'K': ["#   #","#  # ","# #  ","##   ","# #  ","#  # ","#   #"], 'L': ["#    ","#    ","#    ","#    ","#    ","#    ","#####"],
 'M': ["#   #","## ##","# # #","# # #","#   #","#   #","#   #"], 'N': ["#   #","#   #","##  #","# # #","#  ##","#   #","#   #"],
 'O': [" ### ","#   #","#   #","#   #","#   #","#   #"," ### "], 'P': ["#### ","#   #","#   #","#### ","#    ","#    ","#    "],
 'Q': [" ### ","#   #","#   #","#   #","# # #","#  # "," ## #"], 'R': ["#### ","#   #","#   #","#### ","# #  ","#  # ","#   #"],
 'S': [" ####","#    ","#    "," ### ","    #","    #","#### "], 'T': ["#####","  #  ","  #  ","  #  ","  #  ","  #  ","  #  "],
 'U': ["#   #","#   #","#   #","#   #","#   #","#   #"," ### "], 'V': ["#   #","#   #","#   #","#   #","#   #"," # # ","  #  "],
 'W': ["#   #","#   #","#   #","# # #","# # #","# # #"," # # "], 'X': ["#   #","#   #"," # # ","  #  "," # # ","#   #","#   #"],
 'Y': ["#   #","#   #"," # # ","  #  ","  #  ","  #  ","  #  "], 'Z': ["#####","    #","   # ","  #  "," #   ","#    ","#####"],
 'v': ["     ","     ","#   #","#   #","#   #"," # # ","  #  "], 'x': ["     ","     ","#   #"," # # ","  #  "," # # ","#   #"],
 'm': ["     ","     ","## # ","# # #","# # #","#   #","#   #"], 's': ["    ","    "," ###","#   "," ## ","   #","### "],
 'h': ["#   ","#   ","### ","#  #","#  #","#  #","#  #"], 'd': ["   #","   #"," ###","#  #","#  #","#  #"," ###"],
 '+': ["     ","  #  ","  #  ","#####","  #  ","  #  ","     "], '-': ["    ","    ","    ","####","    ","    ","    "],
 '/': ["    #","    #","   # ","  #  "," #   ","#    ","#    "], '%': ["##   ","##  #","   # ","  #  "," #   ","#  ##","   ##"],
 ':': [" ","#"," "," "," ","#"," "], '.': [" "," "," "," "," "," ","#"], ',': [" "," "," "," "," ","#","#"],
 '!': ["#","#","#","#","#"," ","#"], '?': [" ### ","#   #","    #","   # ","  #  ","     ","  #  "],
 '(': ["  #"," # ","#  ","#  ","#  "," # ","  #"], ')': ["#  "," # ","  #","  #","  #"," # ","#  "],
 '✦': ["  #  ","  #  "," ### ","#####"," ### ","  #  ","  #  "], '×': ["     ","#   #"," # # ","  #  "," # # ","#   #","     "], ' ': ["  "] * 7,
}
def pack(items, maxw=1024, gap=2):
    """items: dict name->img; returns (W,H, pos dict)"""
    order = sorted(items, key=lambda n: (-items[n].height, -items[n].width, n))
    x = y = gap; rowh = 0; pos = {}
    for n in order:
        w, h = items[n].size
        if x + w + gap > maxw: x = gap; y += rowh + gap; rowh = 0
        pos[n] = (x, y); x += w + gap; rowh = max(rowh, h)
    H = y + rowh + gap; H = 1 << (H - 1).bit_length()
    return maxw, H, pos
def save_atlas(items, png, maxw=1024):
    W, H, pos = pack(items, maxw)
    at = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for n, im in items.items(): at.alpha_composite(im, pos[n])
    at.save(png, optimize=True)
    return W, H, pos

def build_px_font():
    glyphs = {}
    for ch, rows in PX5.items():
        w = len(rows[0]); a = np.zeros((7, w), np.uint8)
        for j, r in enumerate(rows):
            for i, c in enumerate(r):
                if c == '#': a[j, i] = 1
        glyphs[ch] = a
    fonts = {}
    for var in ('px7', 'px7_ol'):
        items, meta = {}, {}
        for ch, a in glyphs.items():
            h, w = a.shape
            if var == 'px7':
                im = np.zeros((h, w, 4), np.uint8); im[a == 1] = (255, 255, 255, 255); xo, yo = 0, -7
            else:
                o = np.zeros((h + 2, w + 2), np.uint8)
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1): o[1 + dy:1 + dy + h, 1 + dx:1 + dx + w] |= a
                im = np.zeros((h + 2, w + 2, 4), np.uint8); im[o == 1] = (26, 18, 48, 255)
                im[1:1 + h, 1:1 + w][a == 1] = (255, 245, 220, 255); xo, yo = -1, -8
            items[ch] = Image.fromarray(im, 'RGBA'); meta[ch] = dict(xoff=xo, yoff=yo, adv=w + 1 if ch != ' ' else 3)
        W, H, pos = save_atlas(items, f'{OUT}/fonts/font_{var}@1x.png', 128)
        fonts[var] = dict(image=f'font_{var}@1x.png', scale=1, alpha='0/255 (pixel)', lineHeight=9 if var == 'px7' else 10, base=7 if var == 'px7' else 8,
                          size=[W, H], smoothing=False, tint=var == 'px7',
                          note='1x 像素字：用 imageSmoothingEnabled=false 整數倍放大；細數字（1/2、22:30、LV.3、x3）用呢套，唔再用 5–6px 襯線',
                          glyphs={ch: dict(x=pos[ch][0], y=pos[ch][1], w=items[ch].width, h=items[ch].height, **meta[ch]) for ch in items})
    return fonts

def sparkle_glyph(L, cx, cy, R):
    """✦（光粒）— Cinzel 冇呢個字，程序畫：4 角星、金漸變、深邊、bloom（同 gold_text 一樣嘅處理）"""
    W, H = L.size; pts = []
    for i in range(8):
        t = math.radians(-90 + i * 45); r = R if i % 2 == 0 else R * 0.34
        pts.append((cx + r * math.cos(t), cy + r * math.sin(t)))
    m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).polygon(pts, fill=255)
    ms = k.dilate(m, P(1.0))
    put(L, solid((W, H), C['glow']), amul(gauss(ms, P(1.5)), 0.6)); put(L, solid((W, H), C['line']), ms)
    put(L, vgrad((W, H), [(0, C['g_hi']), (0.5, hx('#FFE08A')), (1, hx('#E59A3E'))]), m)
    hl = Image.new('L', (W, H), 0); ImageDraw.Draw(hl).ellipse([cx - R * .22, cy - R * .5, cx + R * .08, cy - R * .1], fill=200); put(L, solid((W, H), hx('#FFFFFF')), ImageChops.multiply(hl, m))
def build_vec_font(name, chars, kind, size, style):
    items, meta = {}, {}
    f = K.font(kind, size)
    asc = P(size * 1.1); padx = P(3)
    for ch in chars:
        W, H = P(size * 1.6) + 2 * padx, P(size * 1.9)
        L = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        if style == 'gold' and ch == '✦': sparkle_glyph(L, padx + P(size * 0.42), asc - P(size * 0.36), P(size * 0.42))
        elif style == 'gold': gold_text(L, (padx, asc), ch, size, kind, anchor='ls', glow=0.6, stroke=1.0)
        else: text(L, (padx, asc), ch, size, hx('#FFFFFF'), kind, anchor='ls', stroke=0.8, stroke_col=hx('#6A0A24'))
        im = L.reduce(2); a = np.asarray(im)[..., 3]; ys, xs = np.where(a > 3)
        x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
        items[ch] = im.crop((x0, y0, x1, y1))
        adv = (P(size * 0.92) / 2) if ch == '✦' else f.getlength(ch) / 2 + (P(0.4) / 2 if style == 'gold' else 0)
        meta[ch] = dict(xoff=int(x0 - padx / 2), yoff=int(y0 - asc / 2), adv=round(adv))
    sp = round(f.getlength(' ') / 2)
    W, H, pos = save_atlas(items, f'{OUT}/fonts/font_{name}@3x.png', 512)
    g = {ch: dict(x=pos[ch][0], y=pos[ch][1], w=items[ch].width, h=items[ch].height, **meta[ch]) for ch in items}
    g[' '] = dict(x=0, y=0, w=0, h=0, xoff=0, yoff=0, adv=sp)
    return dict(image=f'font_{name}@3x.png', scale=3, alpha='8-bit', size_art=size, lineHeight=round(size * 1.35 * 3), base=round(size * 3),
                size=[W, H], smoothing=True, glyphs=g)

FONTS = build_px_font()
FONTS['gold'] = build_vec_font('gold', '0123456789+-×/%:.,!?LVx✦', 'cin', 12, 'gold')
FONTS['gold']['note'] = 'Cinzel Black 金漸變＋深邊＋bloom：貨幣、獎勵、等級（×0.75 = 9 art 都得）；✦＝光粒符號（part 2 程序畫），用法：「✦+12」「✦ LV.4 ✦」；L/V/x 俾 LV.4、x3'
FONTS['round'] = build_vec_font('round', '0123456789+-×/!x', 'fred', 6.5, 'round')
FONTS['round']['note'] = 'Fredoka 白字玫瑰深邊：紅點數字、飄字 +5'

# ================= PACK ATLASES =================
def emit(scale):
    f = scale / 3
    items, frames = {}, {}
    for n, e in list(REG.items()) + list(LBL.items()):
        im = e['img'] if scale == 3 else e['img'].resize((max(1, round(e['img'].width * f)), max(1, round(e['img'].height * f))), Image.LANCZOS)
        items[n] = im
    tag = f'@{scale}x'
    W, H, pos = save_atlas(items, f'{OUT}/atlas/ui_hd2d{tag}.png', 1024 if scale == 3 else 1024)
    for n, e in list(REG.items()) + list(LBL.items()):
        im = items[n]; sx = im.width / e['img'].width; sy = im.height / e['img'].height
        R = lambda v, s: int(round(v * s))
        fr = dict(x=pos[n][0], y=pos[n][1], w=im.width, h=im.height, box=[R(e['box'][0], sx), R(e['box'][1], sy), R(e['box'][2], sx), R(e['box'][3], sy)],
                  art=e['art'], pivot=[R(e['pivot'][0], sx), R(e['pivot'][1], sy)], group=e['group'])
        if e.get('nine'): fr['nine'] = [R(e['nine'][0], sx), R(e['nine'][1], sy), R(e['nine'][2], sx), R(e['nine'][3], sy)]; fr['slice'] = e['slice']
        if e.get('stub'): fr['stub'] = True
        if e.get('note'): fr['note'] = e['note']
        if 'text' in e: fr.update(text=e['text'], font=e['font'], size_art=e['size'], use=e['use'])
        frames[n] = fr
    # icons atlas
    iitems = {n: (e['img'] if scale == 3 else e['img'].resize((round(e['img'].width * f), round(e['img'].height * f)), Image.LANCZOS)) for n, e in ICO.items()}
    IW, IH, ipos = save_atlas(iitems, f'{OUT}/atlas/icons_hd2d{tag}.png', 1024)
    icons = {}
    for n, e in ICO.items():
        im = iitems[n]; sx = im.width / e['img'].width
        icons[n] = dict(x=ipos[n][0], y=ipos[n][1], w=im.width, h=im.height, box=[round(v * sx) for v in e['box']], art=[24, 24], note=e['note'])
        if e['stub']: icons[n]['stub'] = True
    return dict(image=f'ui_hd2d{tag}.png', size=[W, H], scale=scale, frames=frames), dict(image=f'icons_hd2d{tag}.png', size=[IW, IH], scale=scale, icons=icons)

META = dict(version='hd2d-kit-1.1 (part 2)', generated='2026-11-01 HKT', generator='tools/build_ui_kit_hd2d.py (Pillow/numpy, no AI)',
            art_grid=[195, 422], top_ui_max=52, bottom_ui_max=100, coords='frame x/y/w/h = atlas px; box = logical art rect inside sprite (px); '
            'nine = [l,t,r,b] px from sprite edges (0 = 唔切嗰邊); slice 9 | 3h (固定高) | 3v (固定闊); pivot = sprite px; art = logical size in art px',
            draw='drawImage(atlas, x,y,w,h, dx - box[0]/s*a, dy - box[1]/s*a, w/s*a, h/s*a)  where s = atlas scale, a = art->device px',
            alpha='8-bit alpha (glow/glass/antialias) — 同寵物 sprite 嘅 0/255 唔同；pixel 字體係 0/255',
            colors={k_: ('#%02X%02X%02X' % tuple(v[:3]) if isinstance(v[0], int) else ['#%02X%02X%02X' % tuple(c[:3]) for c in v]) for k_, v in C.items()})
for s in (3, 2):
    A, IC = emit(s)
    json.dump(dict(meta=META, **A), open(f'{OUT}/atlas/ui_hd2d@{s}x.json', 'w'), ensure_ascii=False, indent=1)
    json.dump(dict(meta=META, **IC), open(f'{OUT}/atlas/icons_hd2d@{s}x.json', 'w'), ensure_ascii=False, indent=1)
json.dump(dict(meta=META, fonts=FONTS), open(f'{OUT}/fonts/fonts_hd2d.json', 'w'), ensure_ascii=False, indent=1)
print('frames', len(REG), 'labels', len(LBL), 'icons', len(ICO), 'fonts', list(FONTS))
