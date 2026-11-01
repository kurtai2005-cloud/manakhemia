# 《微光小圃》HD-2D v2 主畫面概念（A／B）＋頭像同步表＋零件近鏡 — 遊美 2026-11-02
# 全部 1x（195×422 art px）像素畫，最後 ×3 nearest → 585×1266。純 Pillow／numpy，冇 AI 圖。
import os, sys, json
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hd2d_v2_px as X
from hd2d_v2_px import P, FILLS, new, put, putc, text, icon_px, medal, frame, chamfer_mask, circle_mask, gem, rivet, sparkle, bar, up
import ui_hd2d_kit as K
OUT = X.OUT; os.makedirs(OUT, exist_ok=True)
W, H = 195, 422

# ---------------------------------------------------------------- 花園（H3 層＋即場合成寵物）
MAIN = dict(form='evo_still_tide', acc=('bow',))            # 主養：團絨靜光（潮）＋蝴蝶結
KID = dict(form='S4C', pattern_from='evo_still_tide')        # 細佬：火仔少年 S4，傳承波紋
STATE = 'hungry'
def scene(state=STATE):
    H3 = K.H3; g = json.load(open(f'{H3}/grade.json'))
    lm = np.asarray(Image.open(f'{H3}/lightmap.png').convert('RGB')).astype(float) / 255
    la = np.asarray(Image.open(f'{H3}/light_add.png').convert('RGB')).astype(float)
    eb = np.asarray(Image.open(f'{H3}/emissive_blur.png').convert('RGB')).astype(float)
    tint = np.array(K.hx(g['petTint'])[:3]) / 255 * np.array(K.hx(g['ambientTint'])[:3]) / 255
    def lit(im):
        a = np.asarray(im).astype(float); a[..., :3] *= tint; return Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')
    pets = []
    m, mi = X.compose_pet(MAIN['form'], state, MAIN['acc']); pets.append((lit(m), mi, 97, 292))
    k, ki = X.compose_pet(KID['form'], 'happy', pattern_from=KID['pattern_from']); pets.append((lit(k), ki, 58, 300))
    out = {}
    for L in ['sky', 'far', 'mid', 'fore']:
        im = K._ld(f'{H3}/{L}.png')
        if L == 'mid':
            for (p, inf, fx, fy) in sorted(pets, key=lambda t: t[3]):
                fx += 14; fy += 12; sh = Image.new('RGBA', im.size); hw = 13 if inf['frame'] >= 48 else 10
                ImageDraw.Draw(sh).ellipse([fx - hw, fy - 3, fx + hw, fy + 2], fill=(30, 40, 30, 70)); im.alpha_composite(sh)
                im.alpha_composite(p, (int(round(fx - inf['pivot'][0])), int(round(fy - inf['pivot'][1]))))
        a = np.asarray(im).astype(float); a[..., :3] = a[..., :3] * lm + la + eb * g['bloom']['intensity']
        out[L] = Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')
    out['grade'] = g
    return K.scene_compose(out)

# ---------------------------------------------------------------- 共用零件
def chip(w, h, icon, val):
    c = frame(chamfer_mask(w, h, 3), 'navy', gold=1, seed=w)
    putc(c, medal(h + 1, 'navy', ring=1, spec=False).crop((0, 0, h + 1, h + 1)), h / 2 + 1, h / 2)
    putc(c, icon_px(icon, h - 3), h / 2 + 1, h / 2)
    text(c, str(val), (w + h) / 2 + 1, h / 2 + .5, 10, anchor='m', col='g_hi', col2='g_br')
    # 「＋」小掣
    pl = medal(9, 'pri', ring=1, spec=False); pa = np.array(pl); pa[4, 2:7] = P['white']; pa[2:7, 4] = P['white']; pl = X.img(pa)
    return c, pl

def mini_stat(icon, v, fill, w=46):
    L = new(w, 11); b = bar(w - 8, 7, v, fill, seg=5, low=v < .2); put(L, b, 8, 2)
    m = medal(11, 'paper', ring=1, spec=False); put(L, m, 0, 0); putc(L, icon_px(icon, 9, ncol=10), 5.5, 5.5)
    if v < .2: put(L, gem('rose', 5), w - 4, -1)
    return L

def bubble(t, icon=None):
    tw = X.text_img(t, 10, col='ink', ol=False, shadow=False); w = tw.width + (14 if icon else 6) + 4; h = 16
    b = frame(chamfer_mask(w, h, 2), 'paper', gold=0, glass=False, tex=False, rim_glints=False, inner_line=False)
    if icon: putc(b, icon_px(icon, 10), 8, h / 2)
    put(b, tw, (14 if icon else 4), 3)
    L = new(w, h + 4); L.alpha_composite(b)
    tail = ["oo.", "oWo", ".oo", "..o"]
    for y, r in enumerate(tail):
        for x, ch in enumerate(r):
            if ch != '.': L.putpixel((6 + x, h - 1 + y), P['line'] if ch == 'o' else FILLS['paper'][2])
    L.putpixel((7, h - 1), FILLS['paper'][2]); L.putpixel((6, h - 1), FILLS['paper'][2])
    return L

def toast(w, t, val):
    h = 17; c = frame(chamfer_mask(w, h, 4), 'navy', gold=2, seed=7)
    for gx in (3, w - 8): put(c, gem('rose', 5), gx, h / 2 - 2.5)
    putc(c, medal(15, 'pri', ring=1), 15, h / 2); putc(c, icon_px('star', 11), 15, h / 2)
    text(c, t, 25, h / 2 + .5, 10); text(c, val, w - 12, h / 2 + .5, 10, anchor='r', col='g_hi', col2='g_mid')
    return c

def ribbon_label(t, w=None, fill='navy'):
    tw = X.text_img(t, 10); w = w or tw.width + 8; h = 14
    c = frame(chamfer_mask(w, h, 3), fill, gold=1, glass=False, tex=False, seed=len(t)); put(c, tw, (w - tw.width) / 2, 0.5); return c

def act_button(d, fill, icon, ic=None):
    L = new(d + 4, d + 4); putc(L, medal(d, fill, ring=2), (d + 4) / 2, (d + 4) / 2)
    putc(L, icon_px(icon, ic or int(d * .62)), (d + 4) / 2, (d + 4) / 2 + .5)
    return L

def rail_sq(icon, d=24, badge=None, kind='navy'):
    L = new(d + 6, d + 6); c = frame(chamfer_mask(d, d, 5), kind, gold=2, seed=d)
    put(L, c, 3, 3); putc(L, icon_px(icon, int(d * .66)), 3 + d / 2, 3 + d / 2 + .5)
    put(L, gem('sec', 5), 3 + d / 2 - 2.5, 0)
    if badge is not None: badge_dot(L, d + 1, 3, badge)
    return L

def badge_dot(L, cx, cy, n=None):
    b = medal(9 if n is None else 11, 'rose', ring=1, spec=False); putc(L, b, cx, cy)
    if n is not None: text(L, str(n), cx, cy + .5, 8, anchor='m', col='white')

def dock(y, active=0, style='A'):
    tabs = ['照顧', '玩', '小圃', '手帳', '設定']; icons = ['heart_bunny', 'play_cat', 'sprout', 'book_bear', 'gear_chick']
    if style == 'A': x0, w, h, ch = 1, 193, 37, 5
    else: x0, w, h, ch = 5, 185, 33, 7
    L = new(W, H); c = frame(chamfer_mask(w, h, ch), 'navy', gold=2, seed=11); put(L, c, x0, y)
    tw = w / 5
    for i in range(5):
        cx = x0 + tw * (i + .5)
        if i:
            dx = int(round(x0 + tw * i))
            for yy in range(y + 8, y + h - 7): L.putpixel((dx, yy), P['nv4'] if yy % 2 else P['g_lo'])
            putc(L, rivet(), dx + .5, y + 6)
        if i == active:
            if style == 'A':
                pil = frame(chamfer_mask(int(tw) - 4, h - 4, 4), 'pri', gold=1, glass=True, tex=True, seed=2); put(L, pil, cx - pil.width / 2, y + 2)
                putc(L, medal(22, 'pri', ring=2), cx, y + 9); putc(L, icon_px(icons[i], 15), cx, y + 9.5)
                text(L, tabs[i], cx, y + 27, 10, anchor='m', col='white', col2='g_hi', outline='g_dk')
                putc(L, gem('rose', 7), cx, y - 1)
                for sx, sy in ((cx - 15, y + 3), (cx + 15, y + 6)): putc(L, sparkle(5), sx, sy)
            else:
                putc(L, medal(24, 'pri', ring=2), cx, y + 6); putc(L, icon_px(icons[i], 16), cx, y + 6.5)
                for gx in (-13, 13): putc(L, gem('pri', 5), cx + gx, y + h - 9.5)
                text(L, tabs[i], cx, y + h - 9.5, 10, anchor='m', col='white', col2='g_hi', outline='g_dk')
                for sx, sy in ((cx - 14, y - 2), (cx + 13, y + 2)): putc(L, sparkle(5), sx, sy)
        else:
            iy = y + (12 if style == 'A' else 11)
            putc(L, medal(18, 'navy', ring=1, spec=False), cx, iy); putc(L, icon_px(icons[i], 13), cx, iy + .5)
            text(L, tabs[i], cx, y + (27 if style == 'A' else h - 9.5), 10, anchor='m', col='cream', col2='paper1')
    if active != 3: badge_dot(L, x0 + tw * 3.5 + 8, y + 5)
    return L

# ---------------------------------------------------------------- A：金邊頂旗（經典 HUD 升級）
def home_A(state=STATE):
    bd = scene(state)
    # 頂旗：全闊導航玻璃，底邊金斜角＋中間寶石
    ban = frame(chamfer_mask(W, 47, 6), 'navy', gold=2, seed=21); put(bd, ban, 0, -5)
    for x in (24, 171): putc(bd, rivet(), x, 39)
    putc(bd, gem('rose', 7), 97.5, 40.5)
    # 頭像 ×1 原大（成個頭＋飾品），金八角框，出框 pop
    pt, info, rect = X.portrait(MAIN['form'], state, MAIN['acc'], n=36, scale=1, eyefrac=.6, pop=6, shape='octo')
    put(bd, pt, 1, 3 - info['popPx'] + 1)
    # 名牌
    text(bd, '團絨', 52, 8, 12, col='white', col2='g_hi')
    tag = ribbon_label('靜光', fill='violet'); put(bd, tag, 79, 2)
    put(bd, bar(70, 5, .62, 'sec', seg=8), 51, 15)
    for t in (.33, .66): putc(bd, gem('pri', 5), 51 + 70 * t, 17.5)
    # 需要值 2×2
    for i, (ic, v, f) in enumerate([('feed', .22, 'pri'), ('heart_bunny', .6, 'rose'), ('clean', .55, 'sec'), ('sleep', .15, 'violet')]):
        put(bd, mini_stat(ic, v, f, 45), 50 + (i % 2) * 48, 21 + (i // 2) * 10)
    # 貨幣
    for j, (ic, v) in enumerate((('light', 140), ('star', 10))):
        c, pl = chip(46, 13, ic, v); put(bd, c, 147, 3 + j * 15); putc(bd, pl, 192, 9.5 + j * 15)
    # 右欄
    for (ic, y, lab, bdg) in (('gift', 50, '委託', 3), ('mail', 92, None, None), ('house', 122, '屋仔', None)):
        r = rail_sq(ic, 24, badge=bdg); put(bd, r, 165, y)
        if bdg is None and ic == 'mail': badge_dot(bd, 191, y + 4)
        if lab: put(bd, ribbon_label(lab), 166, y + 27)
    put(bd, toast(108, '收到小禮物', '+5'), 52, 50)
    put(bd, bubble('肚仔餓…', 'feed'), 101, 240)
    # 底：動作圓章＋緞帶字
    for i, (ic, f, lb) in enumerate([('feed', 'pri', '餵食'), ('play_cat', 'rose', '玩耍'), ('clean', 'sec', '清潔'), ('sleep', 'violet', '瞓覺')]):
        cx = 26 + i * 47.7; putc(bd, act_button(30, f, ic, 20), cx, 357)
        rl = ribbon_label(lb, 32); putc(bd, rl, cx, 375)
        if i == 0: putc(bd, sparkle(7), cx + 14, 346); putc(bd, sparkle(5), cx - 15, 352)
    bd.alpha_composite(dock(387, 0, 'A'))
    for (sx, sy, n) in ((47, 6, 5), (8, 48, 5), (160, 140, 5), (30, 200, 3), (175, 300, 5)): putc(bd, sparkle(n), sx, sy)
    return bd

# ---------------------------------------------------------------- B：浮動卡（大頭像 ×2＋需要值併入照顧卡）
def topfade(bd, h=34):
    a = np.array(bd); yy, xx = np.mgrid[0:h, 0:W]; t = 1 - yy / h
    m = (t > X.BAYER[yy % 4, xx % 4] * 1.4)
    a[:h][m] = (a[:h][m] * .72 + np.array(P['nv3']) * .28).astype(np.uint8); return X.img(a)

def care_card(ic, lab, v, fill, w=46, h=36):
    c = frame(chamfer_mask(w, h, 4), 'navy', gold=2, seed=ord(lab[0]) % 17)
    # 頂色帶（心情色）
    ca = np.array(c); ca[4:6, 6:w - 6] = FILLS[fill][2]; ca[4, 6:w - 6] = FILLS[fill][1]; c = X.img(ca)
    putc(c, medal(17, fill, ring=1), 12, 15); putc(c, icon_px(ic, 12), 12, 15.5)
    text(c, lab, 22, 15, 10)
    put(c, bar(w - 8, 6, v, fill, seg=5, low=v < .2), 4, h - 11)
    L = new(w + 4, h + 4); put(L, c, 2, 2)
    if v < .2: badge_dot(L, w - 3, 5, '!')
    return L

def home_B(state=STATE):
    bd = topfade(scene(state))
    pt, info, rect = X.portrait(MAIN['form'], state, MAIN['acc'], n=22, scale=2, eyefrac=.5, pop=0, shape='octo')
    put(bd, pt, 1, 1)
    # 名牌緞帶
    nm = frame(chamfer_mask(86, 17, 4), 'navy', gold=2, seed=5); put(bd, nm, 55, 4)
    text(bd, '團絨', 62, 12.5, 12, col='white', col2='g_hi')
    tag = ribbon_label('靜光', fill='violet'); put(bd, tag, 104, 6)
    put(bd, bar(80, 5, .62, 'sec', seg=8), 58, 22)
    for t in (.33, .66): putc(bd, gem('pri', 5), 58 + 80 * t, 24.5)
    for j, (ic, v) in enumerate((('light', 140), ('star', 10))):
        c, pl = chip(46, 13, ic, v); put(bd, c, 146, 4 + j * 15); putc(bd, pl, 191, 10.5 + j * 15)
    # 右欄：圓章＋寶石頂
    for (ic, cy, lab, bdg) in (('gift', 54, '委託', 3), ('mail', 92, None, '·'), ('house', 122, '屋仔', None)):
        d = 24 if ic != 'mail' else 20
        putc(bd, medal(d, 'navy', ring=2), 179, cy); putc(bd, icon_px(ic, int(d * .66)), 179, cy + .5)
        putc(bd, gem('sec', 5), 179, cy - d / 2 - 1)
        if bdg == 3: badge_dot(bd, 189, cy - 9, 3)
        elif bdg: badge_dot(bd, 188, cy - 7)
        if lab: putc(bd, ribbon_label(lab), 179, cy + 18)
    put(bd, toast(104, '收到小禮物', '+5'), 58, 36)
    put(bd, bubble('肚仔餓…', 'feed'), 101, 240)
    for i, (ic, lab, v, f) in enumerate([('feed', '餵食', .22, 'pri'), ('play_cat', '玩耍', .6, 'rose'), ('clean', '清潔', .55, 'sec'), ('sleep', '瞓覺', .15, 'violet')]):
        put(bd, care_card(ic, lab, v, f), -1 + i * 48.5, 346)
    putc(bd, sparkle(7), 40, 346); putc(bd, sparkle(5), 8, 352)
    bd.alpha_composite(dock(388, 0, 'B'))
    for (sx, sy, n) in ((56, 2, 5), (4, 66, 5), (166, 140, 5), (30, 200, 3), (175, 300, 5)): putc(bd, sparkle(n), sx, sy)
    return bd

# ---------------------------------------------------------------- 頭像同步表
STATES = [('normal', '平常'), ('happy', '開心'), ('hungry', '肚餓'), ('sleepy', '眼瞓'), ('sick', '病咗'), ('sleep', '瞓緊')]
OTHERS = [('A1', dict(wear='hat'), 'happy', '滴滴 A1＋四方帽'), ('S4C', dict(pattern_from='evo_still_tide'), 'happy', '細佬 S4C＋傳承波紋'),
          ('evo_guard_ember', dict(acc=('beanie',)), 'normal', '團絨守護（焰）＋冷帽'), ('radiant', dict(acc=('crown',)), 'hungry', '團絨光芒＋皇冠'),
          ('H3', dict(wear='glasses'), 'sleepy', 'H3＋眼鏡')]
def rect_outline(im, r, col):
    a = np.array(im); x0, y0, x1, y1 = [max(0, v) for v in r]; x1 = min(x1, a.shape[1]) - 1; y1 = min(y1, a.shape[0]) - 1
    for x in range(x0, x1 + 1):
        if (x % 2 == 0): a[y0, x] = col; a[y1, x] = col
    for y in range(y0, y1 + 1):
        if (y % 2 == 0): a[y, x0] = col; a[y, x1] = col
    return X.img(a)

def portrait_sheet():
    S = 3; bd = new(430, 440, P['nv4']); Wd = bd.width
    bg = np.array(bd); yy, xx = np.mgrid[0:bd.height, 0:Wd]; bg[((xx + yy) % 4 == 0) & ((xx - yy) % 8 == 0)] = P['nv3']; bd = X.img(bg)
    text(bd, '左上頭像 ＝ 即場合成嘅寵物幀（同花園同一幀）→ 裁 bust → 整數放大', 6, 8, 12, col='g_hi', col2='g_br')
    text(bd, '形態／階段／飾品／傳承花紋／表情全部自動跟；框底寶石＋右下章＝心情', 6, 22, 10, col='cream')
    y = 36; text(bd, '① 同一隻（團絨靜光＋蝴蝶結）6 個狀態　上：A 版 ×1 全頭　下：B 版 ×2 近鏡', 6, y, 10, col='g_br'); y += 10
    x = 6
    for st, zh in STATES:
        pet, inf = X.compose_pet(MAIN['form'], st, MAIN['acc'])
        p1, i1, r1 = X.portrait(MAIN['form'], st, MAIN['acc'], n=36, scale=1, eyefrac=.6, pop=6)
        p2, i2, r2 = X.portrait(MAIN['form'], st, MAIN['acc'], n=22, scale=2, eyefrac=.5)
        src = rect_outline(pet, r2, P['red']); src = rect_outline(src, r1, P['g_br'])
        cell = 66
        putc(bd, src, x + cell / 2, y + 34); put(bd, p1, x + 10, y + 66 - i1['popPx'] + 0)
        put(bd, p2, x + 6, y + 112)
        text(bd, zh, x + cell / 2, y + 2, 10, anchor='m', col='white')
        x += cell
    y += 176
    text(bd, '② 唔同寵物／形態／飾品（證明跟原物同步）', 6, y, 10, col='g_br'); y += 10; x = 6
    for f, kw, st, zh in OTHERS:
        pet, inf = X.compose_pet(f, st, **kw)
        p1, i1, r1 = X.portrait(f, st, n=36, scale=1, eyefrac=.6, pop=6, **kw)
        p2, i2, r2 = X.portrait(f, st, n=22, scale=2, eyefrac=.5, **kw)
        src = rect_outline(pet, r2, P['red']); src = rect_outline(src, r1, P['g_br'])
        cell = 79
        putc(bd, src, x + cell / 2, y + 44); put(bd, p1, x + 16, y + 80 - i1['popPx'])
        put(bd, p2, x + 12, y + 126)
        for li, part in enumerate(zh.split('＋')): text(bd, ('＋' if li else '') + part, x + cell / 2, y + 2 + li * 9, 8, anchor='m', col='white' if not li else 'g_br')
        x += cell
    y += 190
    text(bd, '金虛線＝A 版 ×1 裁位 36×36　紅虛線＝B 版 ×2 裁位 22×22', 6, y, 8, col='cream')
    text(bd, '原幀＝引擎同一幀：身體→面→花紋→穿戴／飾品（唔另外畫頭像）', 6, y + 10, 8, col='cream')
    return up(bd, S)

# ---------------------------------------------------------------- 零件近鏡
def parts_sheet():
    W, H = 262, 184
    bd = new(W, H, P['nv4']); a = np.array(bd); yy, xx = np.mgrid[0:H, 0:W]; a[((xx // 6 + yy // 6) % 2) == 0] = P['nv3']; bd = X.img(a)
    text(bd, 'v2 像素零件（1x 畫・整數放大）', 4, 6, 10, col='g_hi', col2='g_br')
    put(bd, frame(chamfer_mask(64, 36, 6), 'navy', gold=2, seed=3), 4, 18)
    for gx, gy in ((7, 21), (60, 21)): put(bd, gem('rose', 5), gx, gy)
    x = 74
    for f, ic in (('pri', 'feed'), ('rose', 'play_cat'), ('sec', 'clean'), ('violet', 'sleep')):
        put(bd, act_button(30, f, ic, 20), x, 16); x += 34
    x = 74
    for lb in ('餵食', '玩耍', '清潔', '瞓覺'): putc(bd, ribbon_label(lb, 30), x + 15, 56); x += 34
    c, pl = chip(46, 13, 'light', 140); put(bd, c, 212, 16); putc(bd, pl, 257, 22.5)
    c, pl = chip(46, 13, 'star', 10); put(bd, c, 212, 32); putc(bd, pl, 257, 38.5)
    for i, (ic, v, f) in enumerate([('feed', .22, 'pri'), ('heart_bunny', .6, 'rose'), ('clean', .55, 'sec'), ('sleep', .15, 'violet')]):
        put(bd, mini_stat(ic, v, f, 46), 212, 50 + i * 11)
    put(bd, rail_sq('gift', 24, badge=3), 4, 74); put(bd, rail_sq('house', 24), 34, 74)
    putc(bd, medal(24, 'navy', ring=2), 76, 86); putc(bd, icon_px('mail', 15), 76, 86.5); putc(bd, gem('sec', 5), 76, 73)
    put(bd, care_card('feed', '餵食', .22, 'pri'), 96, 72); put(bd, care_card('sleep', '瞓覺', .15, 'violet'), 146, 72)
    put(bd, toast(108, '收到小禮物', '+5'), 4, 110)
    put(bd, bubble('肚仔餓…', 'feed'), 124, 108)
    text(bd, '團絨', 4, 138, 12, col='white', col2='g_hi'); put(bd, ribbon_label('靜光', fill='violet'), 32, 132)
    for i, n in enumerate((3, 5, 7)): putc(bd, sparkle(n), 80 + i * 11, 139)
    for i, k in enumerate(('rose', 'sec', 'pri', 'violet', 'green')): put(bd, gem(k, 7), 124 + i * 10, 135)
    text(bd, '面板：描線＋雙層金斜角＋抖色＋布紋＋內陰影', 4, 154, 8, col='cream')
    text(bd, '1x 硬邊冇 AA；字 Fusion Pixel 12/10/8（OFL）', 4, 165, 8, col='cream')
    return bd

if __name__ == '__main__':
    A = home_A(); B = home_B()
    up(A).save(f'{OUT}/home_v2_A_3x.png'); up(B).save(f'{OUT}/home_v2_B_3x.png')
    A.save(f'{OUT}/home_v2_A_1x.png'); B.save(f'{OUT}/home_v2_B_1x.png')
    ps = portrait_sheet(); ps.save(f'{OUT}/portrait_sync_sheet_3x.png')
    pp = parts_sheet(); up(pp, 3).save(f'{OUT}/parts_closeup_3x.png'); up(pp, 6).save(f'{OUT}/parts_closeup_6x.png')
    # 對照：現行 home_3x｜A｜B
    cur = Image.open(f'{X.ART}/ui/kit_hd2d/mockups/home_3x.png').convert('RGBA')
    gap = 30; top = 60; cmp_ = new(585 * 3 + gap * 4, 1266 + top + 20, P['nv4'])
    hdr = new(cmp_.width // 3, top // 3, (0, 0, 0, 0))
    for i, t in enumerate(('現行 HD-2D kit', 'v2 A：金邊頂旗', 'v2 B：浮動卡＋照顧卡')):
        text(hdr, t, (gap + i * (585 + gap) + 292) / 3, 10, 12, anchor='m', col='g_hi', col2='g_br')
    cmp_.alpha_composite(up(hdr, 3), (0, 0))
    for i, im in enumerate((cur, up(A), up(B))): cmp_.alpha_composite(im, (gap + i * (585 + gap), top))
    cmp_.save(f'{OUT}/compare_current_A_B.png')
    # 細機睇字（360 闊）
    for n, im in (('A', A), ('B', B)): up(im, 2).resize((360, 779), Image.NEAREST).save(f'{OUT}/home_v2_{n}_smallphone_360w_check.png')
    print('ok')
