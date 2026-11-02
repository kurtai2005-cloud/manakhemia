# 《微光小圃》UI kit v3（Kurt 揀 V3-A 金光現代 HD-2D）共用庫 — 遊美 2026-11-02
# UI 層＝@3x 原生平滑（真 alpha：漸變、柔陰影、煙燻磨砂、1.5px 金幼線、Noto CJK TC）；
# 像素層（場景／團絨／icon）＝整數倍 nearest，alpha 0／255。純 Pillow／numpy，冇 AI 圖。
import os, sys, json, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.abspath(f'{HERE}/../..'); ART = f'{ROOT}/art-pet'; KIT = f'{ART}/ui/kit_hd2d_v3'
W, H = 585, 1266; SS = 4
BANDS = {'top': [0, 126], 'garden': [126, 1044], 'bottom': [1044, 1266]}
# ---------------------------------------------------------------- 字（Noto Sans/Serif CJK TC，OFL 1.1）
FONT_SRC = {'sans': '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 'sansb': '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
            'serif': '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'}
FONT_TTC_INDEX = 3   # TC
TYPE = {'title': ('serif', 30), 'h2': ('sansb', 24), 'body': ('sans', 21), 'value': ('sansb', 21), 'button': ('sansb', 20), 'label': ('sansb', 18), 'caption': ('sans', 18)}
MIN_PX = 18
_FC = {}
def F(kind, sz):
    k = (kind, sz)
    if k not in _FC: _FC[k] = ImageFont.truetype(FONT_SRC[kind], sz, index=FONT_TTC_INDEX)
    return _FC[k]
# ---------------------------------------------------------------- 色 token
C = dict(ink=(36, 34, 52), ink2=(88, 86, 108), cream=(250, 244, 230), mute=(206, 212, 230), gold=(232, 200, 128), gold2=(196, 156, 84), goldhi=(255, 236, 184),
         golddk=(66, 40, 4), navy=(18, 24, 48), navy2=(30, 40, 74), navy3=(44, 58, 104), rose=(240, 126, 150), sky=(110, 190, 230), amber=(246, 176, 72),
         violet=(156, 132, 230), mint=(120, 206, 160), red=(214, 62, 72), red2=(176, 38, 50), paper=(250, 246, 236), dis=(84, 88, 108))
ACCENT = {'pri': 'amber', 'sec': 'sky', 'rose': 'rose', 'violet': 'violet', 'mint': 'mint', 'gold': 'gold', 'dis': 'dis'}
def A(c, a=1.0): return tuple(int(v) for v in c[:3]) + (int(a * 255),)
def lum(c):
    c = np.asarray(c, float)[..., :3] / 255; c = np.where(c <= .03928, c / 12.92, ((c + .055) / 1.055) ** 2.4); return c @ np.array([.2126, .7152, .0722])
# ---------------------------------------------------------------- 基本畫具（全部 SS×4 超取樣）
def new(w, h, c=(0, 0, 0, 0)): return Image.new('RGBA', (int(w), int(h)), c)
def rr_mask(w, h, r):
    w, h = int(w), int(h); m = Image.new('L', (w * SS, h * SS)); ImageDraw.Draw(m).rounded_rectangle([0, 0, w * SS - 1, h * SS - 1], min(r, h / 2, w / 2) * SS, fill=255); return m.resize((w, h), Image.LANCZOS)
def circ_mask(d):
    d = int(d); m = Image.new('L', (d * SS, d * SS)); ImageDraw.Draw(m).ellipse([0, 0, d * SS - 1, d * SS - 1], fill=255); return m.resize((d, d), Image.LANCZOS)
def vgrad(w, h, c0, c1):
    w, h = max(1, int(w)), max(1, int(h)); t = np.linspace(0, 1, h)[:, None, None]; a = np.array(A(c0, c0[3] / 255 if len(c0) > 3 else 1), float) * (1 - t) + np.array(A(c1, c1[3] / 255 if len(c1) > 3 else 1), float) * t
    return Image.fromarray(np.repeat(a, w, 1).clip(0, 255).astype(np.uint8), 'RGBA')
def masked(im, mask):
    im = im.copy(); a = np.array(im); a[..., 3] = (a[..., 3].astype(float) * np.array(mask) / 255).astype(np.uint8); return Image.fromarray(a)
def comp(bd, im, x, y): bd.alpha_composite(im, (int(round(x)), int(round(y))))
def compc(bd, im, cx, cy): comp(bd, im, cx - im.width / 2, cy - im.height / 2)
def stroke_layer(w, h, fn):
    w, h = int(w), int(h); L = Image.new('RGBA', (w * SS, h * SS), (255, 255, 255, 0)); fn(ImageDraw.Draw(L), SS, w, h); return L.resize((w, h), Image.LANCZOS)
def hair_rr_im(w, h, r, col, lw=1.5, inset=0):
    return stroke_layer(w, h, lambda d, s, w_, h_: d.rounded_rectangle([inset * s + lw * s / 2, inset * s + lw * s / 2, (w_ - inset) * s - lw * s / 2 - 1, (h_ - inset) * s - lw * s / 2 - 1], max(0, r - inset) * s, outline=col, width=max(1, int(lw * s))))
def ring_im(d, col, lw=1.5, a0=0, a1=360, pad=2):
    D = d + 2 * pad
    return stroke_layer(D, D, lambda dr, s, w, h: dr.arc([pad * s + lw * s / 2, pad * s + lw * s / 2, (pad + d) * s - lw * s / 2, (pad + d) * s - lw * s / 2], a0, a1, fill=col, width=max(1, int(lw * s))))
def diamond_im(r, col):
    D = 2 * r + 3; return stroke_layer(D, D, lambda d, s, w, h: d.polygon([((r + 1.5) * s, 1.5 * s), ((2 * r + 1.5) * s, (r + 1.5) * s), ((r + 1.5) * s, (2 * r + 1.5) * s), (1.5 * s, (r + 1.5) * s)], fill=col))
def hline_im(w, col, lw=1.5, fade=True):
    w = int(w); a = np.zeros((4, w, 4), np.uint8); a[..., :3] = col[:3]; t = np.linspace(0, 1, w); f = np.minimum(1, np.minimum(t, 1 - t) * 8) if fade else np.ones(w)
    base = col[3] if len(col) > 3 else 255; a[1, :, 3] = (base * f).astype(np.uint8); a[2, :, 3] = (base * f * max(0, lw - 1)).clip(0, 255).astype(np.uint8); return Image.fromarray(a)
def glow_im(r, col, a=.6):
    d = int(r * 2); yy, xx = np.mgrid[0:d, 0:d]; q = np.exp(-(((xx - r) ** 2 + (yy - r) ** 2) / (r * r / 2.5))); g = np.zeros((d, d, 4)); g[..., :3] = col[:3]; g[..., 3] = q * a * 255
    return Image.fromarray(g.astype(np.uint8))
def flare_im(r, col, a=.6):
    r = int(r); L = Image.new('RGBA', (2 * r + 5, 2 * r + 5), A(col, 0)); d = ImageDraw.Draw(L); c = r + 2
    for i in range(r):
        al = (1 - i / r) ** 2 * a; d.point([(c + i, c), (c - i, c), (c, c + i), (c, c - i)], fill=A(col, al))
    return L.filter(ImageFilter.GaussianBlur(.7))
def shadow_im(mask, blur=10, a=.35):
    pad = blur * 3; w, h = mask.size; m = Image.new('L', (w + 2 * pad, h + 2 * pad)); m.paste(mask, (pad, pad)); m = m.filter(ImageFilter.GaussianBlur(blur))
    sh = Image.new('RGBA', m.size, (8, 10, 24, 0)); sh.putalpha(m.point(lambda v: int(v * a))); return sh, pad
def drop_shadow(bd, mask, x, y, blur=10, dy=6, a=.35):
    sh, pad = shadow_im(mask, blur, a); comp(bd, sh, x - pad, y - pad + dy)
def backdrop(bd, x, y, w, h, mask, blur=14):
    """磨砂：引擎用預先烘焙嘅模糊場景圖；呢度即場 blur 背景（效果一樣）"""
    x, y, w, h = int(x), int(y), int(w), int(h); b = bd.crop((x, y, x + w, y + h)).filter(ImageFilter.GaussianBlur(blur)); comp(bd, masked(b, mask), x, y)

# ================================================================ 零件（PARTS：atlas 同 mockup 用同一套函數）
PARTS = {}   # name -> dict(fn, size, slice, nine, group, note)
def part(name, size, slice_=None, nine=None, group='misc', note='', backdrop_=False):
    def deco(fn): PARTS[name] = dict(fn=fn, size=size, slice=slice_, nine=nine, group=group, note=note, backdrop=backdrop_); return fn
    return deco
def P(name, w=None, h=None):
    d = PARTS[name]; w = w or d['size'][0]; h = h or d['size'][1]; USED.add(name); return d['fn'](int(w), int(h))
USED = set()
# ---- 面板（煙燻磨砂：引擎先畫 backdrop blur，再疊呢層）
def _smoked(w, h, r, a0=.80, a1=.80, line=True, inner=True):
    m = rr_mask(w, h, r); L = vgrad(w, h, A(C['navy2'], a0), A(C['navy'], min(1, a1 + .1))); L.alpha_composite(vgrad(w, max(2, h // 2), (255, 255, 255, 22), (255, 255, 255, 0)))
    L = masked(L, m)
    if line: L.alpha_composite(hair_rr_im(w, h, r, A(C['gold'], .9), 1.5))
    if line and inner and min(w, h) > 30: L.alpha_composite(hair_rr_im(w, h, r, A(C['gold'], .22), 1, 4))
    return L
for nm, r, note in (('panel', 24, '主面板／彈窗'), ('panel_r16', 16, '細面板'), ('card', 18, '卡')):
    part(nm, (120, 120), '9', [r + 6] * 4, 'panel', note, True)(lambda w, h, r=r: _smoked(w, h, r))
part('panel_flat', (120, 120), '9', [24] * 4, 'panel', '冇金線版（行內分組）', True)(lambda w, h: _smoked(w, h, 20, .55, .55, line=False))
part('panel_inset', (120, 60), '9', [16] * 4, 'panel', '凹入行（設定／需求）', False)(lambda w, h: _inset(w, h, False))
def _inset(w, h, sel):
    L = masked(vgrad(w, h, A((8, 12, 28), .55), A((8, 12, 28), .32)), rr_mask(w, h, 14)); L.alpha_composite(hair_rr_im(w, h, 14, A((255, 255, 255), .10), 1))
    if sel: L.alpha_composite(hair_rr_im(w, h, 14, A(C['gold'], .95), 1.5)); L.alpha_composite(masked(vgrad(w, h, A(C['gold'], .16), A(C['gold'], .04)), rr_mask(w, h, 14)))
    return L
part('panel_inset_sel', (120, 60), '9', [16] * 4, 'panel', '選中行（金幼線＋暖光）')(lambda w, h: _inset(w, h, True))
def _paper(w, h):
    L = masked(vgrad(w, h, A((255, 251, 242), .96), A((246, 238, 222), .96)), rr_mask(w, h, 18)); L.alpha_composite(hair_rr_im(w, h, 18, A(C['gold2'], .85), 1.5)); return L
part('panel_paper', (120, 90), '9', [22] * 4, 'panel', '米白紙（說明／信）')(_paper)
def _card_sel(w, h):
    L = new(w, h); L.alpha_composite(_smoked(w, h, 18, .82, .82, False)); L.alpha_composite(masked(vgrad(w, h, A(C['gold'], .22), A(C['gold'], .05)), rr_mask(w, h, 18)))
    L.alpha_composite(hair_rr_im(w, h, 18, A(C['goldhi'], 1), 2)); L.alpha_composite(hair_rr_im(w, h, 18, A(C['gold'], .5), 1, 4)); return L
part('card_sel', (120, 150), '9', [24] * 4, 'panel', '選中卡', True)(_card_sel)
def _card_locked(w, h):
    L = masked(vgrad(w, h, A((40, 44, 62), .78), A((24, 26, 40), .85)), rr_mask(w, h, 18)); L.alpha_composite(hair_rr_im(w, h, 18, A((160, 164, 186), .45), 1.2)); return L
part('card_locked', (120, 150), '9', [24] * 4, 'panel', '未解鎖卡', True)(_card_locked)
part('card_paper', (120, 150), '9', [22] * 4, 'panel', '紙卡')(_paper)
def _egg_card(w, h):
    L = _card_sel(w, h); g = glow_im(min(w, h) * .45, C['goldhi'], .35); L.alpha_composite(g, (int(w / 2 - g.width / 2), int(h * .32 - g.height / 2))); return masked(L, rr_mask(w, h, 18))
part('egg_card', (216, 336), '9', [24] * 4, 'panel', '揀蛋卡（暖光）', True)(_egg_card)
# ---- HUD
def _scrim_top(w, h): L = vgrad(w, int(h * .56), A(C['navy'], .9), A(C['navy'], .82)); L2 = new(w, h); L2.alpha_composite(L); L2.alpha_composite(vgrad(w, h - L.height, A(C['navy'], .82), A(C['navy'], 0)), (0, L.height)); return L2
part('scrim_top', (585, 200), '3v', [0, 112, 0, 0], 'hud', '頂部漸層遮罩（取代 v2 banner_top）')(_scrim_top)
part('scrim_bottom', (585, 150), '3v', [0, 0, 0, 0], 'hud', '底部漸層')(lambda w, h: vgrad(w, h, A(C['navy'], 0), A(C['navy'], .55)))
part('dock', (561, 116), '9', [34] * 4, 'hud', '懸浮 dock（取代 dock_bar）', True)(lambda w, h: _smoked(w, h, 28))
def _dock_on(w, h):
    L = new(w, h); g = glow_im(w * .5, C['gold'], .5); compc(L, g, w / 2, h * .36); L.alpha_composite(hline_im(52, A(C['gold'], 1), 2), (int(w / 2 - 26), h - 12)); return L
part('dock_on', (100, 110), None, None, 'hud', '選中 tab 光（取代 dock_pillar）')(_dock_on)
def _pill(w, h, a=.80, line=True):
    return _smoked(w, h, h / 2, a, a - .1, line, inner=False)
part('toast', (286, 42), '3h', [24, 0, 24, 0], 'hud', 'toast', True)(lambda w, h: _pill(w, h))
part('label_pill', (60, 26), '3h', [14, 0, 14, 0], 'hud', '場景上細字底（rail 標籤等）', True)(lambda w, h: _pill(w, h, .74, False))
def _bubble(w, h):
    L = masked(vgrad(w, h, A((255, 255, 255), .93), A((248, 246, 242), .93)), rr_mask(w, h, h / 2)); L.alpha_composite(hair_rr_im(w, h, h / 2, A((255, 255, 255), 1), 2)); return L
part('bubble', (170, 42), '3h', [22, 0, 22, 0], 'hud', '泡泡（白玻璃）', True)(_bubble)
part('bubble_tail', (18, 16), None, None, 'hud', '泡泡尾')(lambda w, h: stroke_layer(w, h, lambda d, s, w_, h_: d.polygon([(0, 0), (w_ * s, 0), (2 * s, h_ * s)], fill=(255, 255, 255, 236))))
def _plaque(w, h):  # 畫面標題：金幼線＋菱形（冇框）
    L = new(w, h); L.alpha_composite(hline_im(w, A(C['gold'], .95), 1.5), (0, h - 4)); compc(L, diamond_im(4, A(C['gold'], 1)), w / 2, h - 2.5); return L
part('title_rule', (300, 12), '3h', [20, 0, 20, 0], 'hud', '標題下金線（取代 plaque／ribbon）')(_plaque)
part('divider', (300, 6), '3h', [20, 0, 20, 0], 'hud', '分隔金線（兩頭淡出）')(lambda w, h: hline_im(w, A(C['gold'], .55), 1.2))
part('stage_tag', (62, 26), '3h', [14, 0, 14, 0], 'label', '形態 tag（金幼線膠囊）')(lambda w, h: hair_rr_im(w, h, h / 2, A(C['gold'], 1), 1.5))
def _chip(w, h): return _pill(w, h, .7, False)
part('chip', (150, 38), '3h', [20, 0, 20, 0], 'hud', '貨幣／計數 chip', True)(_chip)
part('chip_plus', (28, 28), None, None, 'ctl', '＋（金幼線圓）')(lambda w, h: _plus(w, False))
part('chip_plus_p', (28, 28), None, None, 'ctl', '＋按下')(lambda w, h: _plus(w, True))
def _plus(d, p):
    L = new(d, d)
    if p: L.alpha_composite(masked(new(d, d, A(C['gold'], .45)), circ_mask(d)))
    L.alpha_composite(ring_im(d - 4, A(C['gold'], .95), 1.5)); L.alpha_composite(stroke_layer(d, d, lambda dr, s, w, h: (dr.line([(w * s / 2, 8 * s), (w * s / 2, (h - 8) * s)], fill=A(C['goldhi']), width=int(1.6 * s)), dr.line([(8 * s, h * s / 2), ((w - 8) * s, h * s / 2)], fill=A(C['goldhi']), width=int(1.6 * s)))))
    return L
# ---- 按鈕（3h）
def _btn(w, h, acc, pressed=False, dis=False):
    c = C[ACCENT[acc]] if not dis else C['dis']; top = tuple(min(255, int(v * 1.12) + 18) for v in c); bot = tuple(int(v * (.78 if dis else .9)) for v in c)
    if pressed: top, bot = bot, tuple(int(v * .95) for v in c)
    m = rr_mask(w, h, h / 2); L = masked(vgrad(w, h, A(top), A(bot)), m)
    if not pressed: L.alpha_composite(masked(vgrad(w, h // 2, (255, 255, 255, 70), (255, 255, 255, 0)), rr_mask(w, h // 2, h / 4)), (0, 2))
    L.alpha_composite(hair_rr_im(w, h, h / 2, A(C['goldhi'] if not dis else (200, 200, 210), .95), 1.5)); return L
for acc in ('pri', 'sec', 'rose', 'violet', 'dis'):
    for sz, hh in (('', 60), ('_s', 48)):
        part(f'btn{sz}_{acc}', (160, hh), '3h', [hh // 2 + 4, 0, hh // 2 + 4, 0], 'button', f'按鈕 h{hh}')(lambda w, h, a=acc: _btn(w, h, a, dis=a == 'dis'))
        part(f'btn{sz}_{acc}_p', (160, hh), '3h', [hh // 2 + 4, 0, hh // 2 + 4, 0], 'button', f'按鈕 h{hh} 按下')(lambda w, h, a=acc: _btn(w, h, a, True, dis=a == 'dis'))
def _pillc(w, h, acc):
    if acc == 'navy': return _pill(w, h, .8, True)
    c = C[ACCENT[acc]]; L = masked(vgrad(w, h, A(tuple(min(255, int(v * 1.1) + 10) for v in c), .95), A(tuple(int(v * .93) for v in c), .97)), rr_mask(w, h, h / 2)); L.alpha_composite(hair_rr_im(w, h, h / 2, A((255, 255, 255), .6), 1)); return L
for acc in ('pri', 'sec', 'rose', 'violet', 'dis', 'navy'):
    part(f'pill_{acc}', (80, 32), '3h', [16, 0, 16, 0], 'label', '膠囊標籤')(lambda w, h, a=acc: _pillc(w, h, a))
# ---- 圓掣（行動／rail／返回／關閉）
def _round(d, acc=None, pressed=False, ring=True):
    L = new(d + 12, d + 12); o = 6; m = circ_mask(d)
    s = _smoked(d, d, d / 2, .82, .82, line=False)
    if pressed: s.alpha_composite(masked(new(d, d, A(C[ACCENT[acc]] if acc else C['gold'], .30)), m))
    L.alpha_composite(s, (o, o))
    if acc: L.alpha_composite(ring_im(d - 8, A(C[ACCENT[acc]], 1), 3), (o + 2, o + 2))
    if ring: L.alpha_composite(ring_im(d + 6, A(C['gold'], .85), 1.2), (o - 5, o - 5))
    return L
for acc in ('pri', 'sec', 'rose', 'violet', 'mint', 'gold', 'dis'):
    part(f'act_{acc}', (90, 90), None, None, 'button', '行動圓掣 d78（色環）')(lambda w, h, a=acc: _round(78, a))
    part(f'act_{acc}_p', (90, 90), None, None, 'button', '行動圓掣 按下')(lambda w, h, a=acc: _round(78, a, True))
part('act_glow', (140, 140), None, None, 'fx', '建議動作光暈（真 alpha）')(lambda w, h: glow_im(w / 2, C['amber'], .45))
part('rail_btn', (76, 76), None, None, 'button', '右 rail 圓掣 d64')(lambda w, h: _round(64, None, False))
part('rail_btn_p', (76, 76), None, None, 'button', 'rail 按下')(lambda w, h: _round(64, 'gold', True))
part('back_btn', (68, 68), None, None, 'button', '返回 d56')(lambda w, h: _round(56))
def _close(w, h, p=False):
    L = _round(44, None, p, True); L.alpha_composite(stroke_layer(56, 56, lambda d, s, w_, h_: (d.line([(21 * s, 21 * s), (35 * s, 35 * s)], fill=A(C['goldhi']), width=int(2 * s)), d.line([(35 * s, 21 * s), (21 * s, 35 * s)], fill=A(C['goldhi']), width=int(2 * s))))); return L
part('close', (56, 56), None, None, 'ctl', '關閉 d44')(_close)
part('close_p', (56, 56), None, None, 'ctl', '關閉按下')(lambda w, h: _close(w, h, True))
def _medal(d, acc='navy'):
    L = new(d, d); m = circ_mask(d)
    if acc == 'navy': L.alpha_composite(_smoked(d, d, d / 2, .85, .85, False))
    else: c = C[ACCENT[acc]]; L.alpha_composite(masked(vgrad(d, d, A(tuple(min(255, int(v * 1.1) + 20) for v in c), .9), A(tuple(int(v * .7) for v in c), .9)), m))
    L.alpha_composite(ring_im(d - 4, A(C['gold'], .9), 1.2)); return L
for d in (36, 48, 60):
    for acc in ('navy', 'pri', 'sec', 'rose', 'violet', 'gold'):
        part(f'med{d}_{acc}', (d, d), None, None, 'medal', f'icon 底圓 d{d}')(lambda w, h, a=acc: _medal(w, a))
# ---- 數值條
def _track(w, h): return masked(new(w, h, (255, 255, 255, 46)), rr_mask(w, h, h / 2))
def _fill(w, h, acc):
    c = C[acc]; return masked(vgrad(w, h, A(tuple(min(255, int(v * 1.15) + 20) for v in c)), A(tuple(int(v * .85) for v in c))), rr_mask(w, h, h / 2))
for hh in (5, 6, 8):
    part(f'bar_track_h{hh}', (60, hh), '3h', [hh // 2 + 1, 0, hh // 2 + 1, 0], 'bar', '條底')(_track)
    for acc in ('amber', 'rose', 'sky', 'violet', 'mint', 'gold', 'red'):
        part(f'bar_fill_{acc}_h{hh}', (60, hh), '3h', [hh // 2 + 1, 0, hh // 2 + 1, 0], 'bar', '條身（頭會加 bar_tip 光點）')(lambda w, h, a=acc: _fill(w, h, a))
for acc in ('amber', 'rose', 'sky', 'violet', 'mint', 'gold', 'red'):
    part(f'bar_tip_{acc}', (20, 20), None, None, 'bar', '條頭光點（真 alpha）')(lambda w, h, a=acc: glow_im(10, C[a], .6))
def _ringg(d, acc, v, lw=4):
    L = new(d + 4, d + 4); L.alpha_composite(ring_im(d, A((255, 255, 255), .16), lw)); L.alpha_composite(ring_im(d, A(C[acc]), lw, -90, -90 + 360 * v)); return L
part('ring_gauge', (44, 44), None, None, 'bar', '環形量表（runtime 用 arc 畫；呢張係樣）')(lambda w, h: _ringg(40, 'amber', .6))
part('exp_gem_on', (14, 14), None, None, 'bar', '經驗刻度（亮）')(lambda w, h: diamond_im(5, A(C['goldhi'])))
part('exp_gem_off', (14, 14), None, None, 'bar', '經驗刻度（暗）')(lambda w, h: diamond_im(5, A((150, 150, 170), .6)))
# ---- 標籤／分頁
def _subtab(w, h, on):
    if on: L = masked(vgrad(w, h, A(C['gold'], .30), A(C['gold'], .10)), rr_mask(w, h, h / 2)); L.alpha_composite(hair_rr_im(w, h, h / 2, A(C['gold'], 1), 1.5)); return L
    return hair_rr_im(w, h, h / 2, A((255, 255, 255), .18), 1)
part('subtab', (90, 40), '3h', [20, 0, 20, 0], 'label', '分頁')(lambda w, h: _subtab(w, h, False))
part('subtab_on', (90, 40), '3h', [20, 0, 20, 0], 'label', '分頁選中')(lambda w, h: _subtab(w, h, True))
part('seg_bg', (240, 40), '3h', [20, 0, 20, 0], 'label', '分段底')(lambda w, h: masked(new(w, h, A((8, 12, 28), .5)), rr_mask(w, h, h / 2)))
part('seg_on', (80, 34), '3h', [17, 0, 17, 0], 'label', '分段選中')(lambda w, h: _btn(w, h, 'pri'))
part('seg_locked', (80, 34), '3h', [17, 0, 17, 0], 'label', '分段鎖')(lambda w, h: hair_rr_im(w, h, h / 2, A((160, 164, 186), .5), 1))
# ---- 控件
def _toggle(on):
    w, h = 64, 34; L = masked(vgrad(w, h, A(C['amber'] if on else (70, 76, 100), .95), A(tuple(int(v * .8) for v in (C['amber'] if on else (70, 76, 100))), .95)), rr_mask(w, h, h / 2)); L.alpha_composite(hair_rr_im(w, h, h / 2, A(C['goldhi'] if on else (180, 180, 200), .8), 1.2)); return L
part('toggle_track_on', (64, 34), None, None, 'ctl', '開關（開）')(lambda w, h: _toggle(True))
part('toggle_track_off', (64, 34), None, None, 'ctl', '開關（關）')(lambda w, h: _toggle(False))
def _knob(d, on=True):
    L = new(d + 8, d + 8); drop_shadow(L, circ_mask(d), 4, 4, 2, 1, .4); L.alpha_composite(masked(vgrad(d, d, A((255, 255, 255)), A((236, 232, 224))), circ_mask(d)), (4, 4)); return L
part('toggle_knob', (36, 36), None, None, 'ctl', '開關掣粒')(lambda w, h: _knob(28))
part('slider_track', (200, 8), '3h', [5, 0, 5, 0], 'ctl', '滑桿')(_track)
part('slider_knob', (36, 36), None, None, 'ctl', '滑桿掣粒')(lambda w, h: _knob(28))
def _check(on):
    d = 34; L = new(d, d)
    if on: L.alpha_composite(masked(vgrad(d, d, A(C['goldhi']), A(C['gold2'])), circ_mask(d))); L.alpha_composite(stroke_layer(d, d, lambda dr, s, w, h: dr.line([(9 * s, 17 * s), (15 * s, 23 * s), (25 * s, 11 * s)], fill=A(C['golddk']), width=int(3 * s), joint='curve')))
    else: L.alpha_composite(ring_im(d - 4, A((255, 255, 255), .6), 1.5))
    return L
part('check_on', (34, 34), None, None, 'ctl', '剔（金）')(lambda w, h: _check(True))
part('check_off', (34, 34), None, None, 'ctl', '未剔')(lambda w, h: _check(False))
def _star(on, d=30):
    pts = [((d / 2 + math.cos(-math.pi / 2 + i * math.pi / 5) * (d / 2 - 2 if i % 2 == 0 else d / 4.6)), (d / 2 + 1 + math.sin(-math.pi / 2 + i * math.pi / 5) * (d / 2 - 2 if i % 2 == 0 else d / 4.6))) for i in range(10)]
    def fn(dr, s, w, h): dr.polygon([(x * s, y * s) for x, y in pts], fill=A(C['goldhi']) if on else A((90, 96, 120), .8), outline=A(C['gold2']) if on else A((160, 164, 186), .6), width=int(1.2 * s))
    return stroke_layer(d, d, fn)
part('star_on', (30, 30), None, None, 'ctl', '星（亮）')(lambda w, h: _star(True))
part('star_off', (30, 30), None, None, 'ctl', '星（暗）')(lambda w, h: _star(False))
part('scroll_track', (6, 120), '3v', [0, 4, 0, 4], 'ctl', '捲軸')(lambda w, h: masked(new(w, h, (255, 255, 255, 30)), rr_mask(w, h, 3)))
part('scroll_thumb', (6, 40), '3v', [0, 4, 0, 4], 'ctl', '捲軸粒')(lambda w, h: masked(new(w, h, A(C['gold'], .8)), rr_mask(w, h, 3)))
part('scroll_fade_top', (540, 30), '3h', [0, 0, 0, 0], 'ctl', '捲動淡出（頂）')(lambda w, h: vgrad(w, h, A(C['navy'], .85), A(C['navy'], 0)))
part('scroll_fade_bot', (540, 30), '3h', [0, 0, 0, 0], 'ctl', '捲動淡出（底）')(lambda w, h: vgrad(w, h, A(C['navy'], 0), A(C['navy'], .85)))
def _reddot(d, num=False):
    L = new(d, d); L.alpha_composite(masked(vgrad(d, d, A(C['red']), A(C['red2'])), circ_mask(d))); L.alpha_composite(ring_im(d - 4, A((255, 255, 255), .9), 1.5)); return L
part('red_dot', (18, 18), None, None, 'deco', '紅點')(lambda w, h: _reddot(18))
part('red_dot_num', (28, 28), None, None, 'deco', '紅點＋數字（字 label 18 白，對比 5.05）')(lambda w, h: _reddot(28, True))
# ---- 裝飾／fx（真 alpha）
part('diamond', (11, 11), None, None, 'deco', '金菱形')(lambda w, h: diamond_im(4, A(C['gold'])))
part('diamond_hi', (13, 13), None, None, 'deco', '亮金菱形')(lambda w, h: diamond_im(5, A(C['goldhi'])))
for r in (12, 20, 34):
    part(f'flare_{r}', (2 * r + 5, 2 * r + 5), None, None, 'fx', '四芒星光')(lambda w, h, r=r: flare_im(r, (255, 240, 200), .7))
for r in (10, 24, 48, 80):
    part(f'glow_{r}', (2 * r, 2 * r), None, None, 'fx', '柔光暈（可 tint）')(lambda w, h, r=r: glow_im(r, (255, 236, 190), .6))
def _mote(w, h):
    L = new(w, h); compc(L, glow_im(w / 2, (255, 230, 170), .5), w / 2, h / 2); L.alpha_composite(masked(new(6, 6, (255, 252, 236, 255)), circ_mask(6)).filter(ImageFilter.GaussianBlur(.6)), (w // 2 - 3, h // 2 - 3)); return L
part('fx_mote', (24, 24), None, None, 'fx', '光點粒子')(_mote)
def _bokeh(w, h):
    d = w; L = new(d, d); L.alpha_composite(masked(new(d, d, (255, 236, 200, 34)), circ_mask(d))); L.alpha_composite(ring_im(d - 4, (255, 236, 200, 60), 2)); return L.filter(ImageFilter.GaussianBlur(1.5))
part('fx_bokeh', (48, 48), None, None, 'fx', '失焦光圈')(_bokeh)
def _ripple(w, h):
    L = new(w, h)
    for i, a in ((0, .6), (14, .35), (28, .18)): L.alpha_composite(ring_im(w - 4 - 2 * i, A(C['goldhi'], a), 1.5), (i, i))
    return L
part('fx_ripple', (120, 120), None, None, 'fx', '波紋（揀蛋／傳承）')(_ripple)
def _rays(w, h):
    yy, xx = np.mgrid[0:h, 0:w].astype(float); ang = np.arctan2(yy - h / 2, xx - w / 2); r = np.hypot(yy - h / 2, xx - w / 2) / (w / 2)
    v = (np.cos(ang * 12) * .5 + .5) ** 3 * np.exp(-r * 2.2) * (r < 1); g = np.zeros((h, w, 4)); g[..., :3] = (255, 226, 160); g[..., 3] = v * 200; return Image.fromarray(g.astype(np.uint8))
part('fx_rays', (420, 420), None, None, 'fx', '升級光芒（取代棋盤 dither 光芒）')(_rays)
part('fx_sweep', (80, 60), None, None, 'fx', '掃光（斜白漸層）')(lambda w, h: Image.fromarray(np.dstack([np.full((h, w, 3), 255), (np.clip(1 - np.abs(np.arange(w)[None, :] - np.arange(h)[:, None] * .6 - w * .3) / 14, 0, 1) * 110)]).astype(np.uint8)))
part('veil', (8, 8), '9', [0, 0, 0, 0], 'fx', '彈窗遮罩（navy 55%；真 alpha，取代棋盤 veil）')(lambda w, h: new(w, h, A(C['navy'], .55)))
part('veil_light', (8, 8), '9', [0, 0, 0, 0], 'fx', '輕遮罩（navy 30%）')(lambda w, h: new(w, h, A(C['navy'], .30)))
def _stamp(w, h):
    L = new(w, h); L.alpha_composite(ring_im(w - 8, A(C['rose'], .9), 2.5)); L.alpha_composite(ring_im(w - 18, A(C['rose'], .6), 1.2), (5, 5))
    ImageDraw.Draw(L).text((w / 2 + 2, h / 2 + 2), '完成', font=F('sansb', 20), fill=A(C['rose'], .95), anchor='mm'); return L.rotate(-12, Image.BICUBIC)
part('stamp_done', (78, 78), None, None, 'deco', '完成印（玫瑰色）')(_stamp)
part('timeline_dot', (16, 16), None, None, 'deco', '時間線點')(lambda w, h: (lambda L: (L.alpha_composite(masked(new(10, 10, A(C['goldhi'])), circ_mask(10)), (3, 3)), L)[1])(glow_im(8, C['gold'], .5)))
part('timeline_line', (4, 60), '3v', [0, 2, 0, 2], 'deco', '時間線')(lambda w, h: Image.fromarray(np.dstack([np.full((h, w, 3), C['gold']), np.tile(np.array([0, 140, 140, 0])[None, :], (h, 1))]).astype(np.uint8)))
def _hint(w, h): return stroke_layer(w, h, lambda d, s, w_, h_: d.polygon([(w_ * s / 2, h_ * s), (2 * s, 4 * s), ((w_ - 2) * s, 4 * s)], fill=A(C['goldhi'])))
part('hint_arrow', (24, 20), None, None, 'deco', '提示箭咀（上下浮動 4px）')(_hint)
# ---- 頭像（B ×2 近鏡；V3-A 圓角方 + 雙金線）
PORT_D = 110   # = 22 sprite px × 5
STATE_BG = {'hungry': ((255, 214, 150), (246, 150, 80)), 'happy': ((255, 210, 222), (236, 120, 150)), 'normal': ((200, 232, 255), (110, 170, 226)),
            'sleepy': ((214, 204, 255), (132, 112, 214)), 'sleep': ((190, 186, 240), (96, 86, 180)), 'sick': ((206, 240, 214), (110, 186, 140))}
STATE_IC = {'hungry': 'mini_feed', 'happy': 'mini_heart', 'normal': 'mini_light', 'sleepy': 'mini_sleep', 'sleep': 'mini_sleep', 'sick': 'mini_clean'}
def _pbg(state, d=PORT_D):
    c0, c1 = STATE_BG[state]; a = np.array(vgrad(d, d, A(c0), A(c1))).astype(float); yy, xx = np.mgrid[0:d, 0:d]
    a[..., :3] += np.exp(-(((xx - d * .35) ** 2 + (yy - d * .3) ** 2) / (d * d * .12)))[..., None] * 60; return Image.fromarray(a.clip(0, 255).astype(np.uint8))
for st in STATE_BG:
    part(f'portrait_bg_{st}', (PORT_D, PORT_D), None, None, 'portrait', '頭像底（心情色漸層）')(lambda w, h, s=st: _pbg(s, w))
part('portrait_mask', (PORT_D, PORT_D), None, None, 'portrait', '頭像窗遮罩（圓角 30；白＋alpha）')(lambda w, h: masked(new(w, h, (255, 255, 255, 255)), rr_mask(w, h, 30)))
def _pframe(w, h):  # 外加 6px 邊
    L = new(w, h); d = w - 12; L.alpha_composite(hair_rr_im(w - 2, h - 2, 34, A(C['gold']), 1.5), (1, 1)); L.alpha_composite(hair_rr_im(d, d, 30, A(C['goldhi'], .9), 2), (6, 6))
    L.alpha_composite(masked(vgrad(d, d // 2, (255, 255, 255, 70), (255, 255, 255, 0)), rr_mask(d, d // 2, 30)), (6, 6))
    for cy in (0, h - 11): L.alpha_composite(diamond_im(4, A(C['gold'])), (int(w / 2 - 5.5), cy))
    return L
part('portrait_frame', (PORT_D + 12, PORT_D + 12), None, None, 'portrait', '頭像框（窗 @6,6）')(_pframe)
def _mood(st):
    d = 36; c1 = STATE_BG[st][1]; L = new(d, d); L.alpha_composite(masked(vgrad(d, d, A(c1), A(tuple(int(v * .7) for v in c1))), circ_mask(d))); L.alpha_composite(ring_im(d - 4, A((255, 255, 255), .9), 2)); return L
for st in STATE_BG:
    part(f'mood_badge_{st}', (36, 36), None, None, 'portrait', '心情章底（mini icon runtime 疊）')(lambda w, h, s=st: _mood(s))
part('acc_badge', (34, 34), None, None, 'portrait', '飾品細章底（大部分出框嗰類，例如光環）')(lambda w, h: _medal(34, 'navy'))
# ---- 5a／5b／5c
def _crest(w, h):
    L = new(w, h); compc(L, glow_im(w / 2, C['gold'], .5), w / 2, h / 2); d = int(w * .7); m = circ_mask(d)
    L.alpha_composite(masked(vgrad(d, d, A(C['goldhi']), A(C['gold2'])), m), ((w - d) // 2, (h - d) // 2)); L.alpha_composite(ring_im(d - 10, A(C['golddk'], .6), 1.5), ((w - d) // 2 + 3, (h - d) // 2 + 3))
    for i in range(8):
        a = i * math.pi / 4; compc(L, diamond_im(4, A(C['goldhi'])), w / 2 + math.cos(a) * (d / 2 + 8), h / 2 + math.sin(a) * (d / 2 + 8))
    return L
part('family_crest', (130, 130), None, None, '5x', '家族徽（金章＋光暈）')(_crest)
def _node(w, h, kind):
    L = new(w, h); d = w - 8
    if kind == 'gold': L.alpha_composite(glow_im(w / 2, C['gold'], .45))
    L.alpha_composite(_smoked(d, d, d / 2, .85, .85, False), (4, 4)); L.alpha_composite(ring_im(d - 4, A(C['goldhi'] if kind != 'n' else C['gold'], 1 if kind != 'n' else .8), 2 if kind != 'n' else 1.5), (4, 4))
    if kind == 'sel': L.alpha_composite(ring_im(d + 2, A(C['goldhi'], .5), 1), (1, 1))
    return L
for k, nm in (('n', 'tree_node'), ('sel', 'tree_node_sel'), ('gold', 'tree_node_gold')):
    part(nm, (96, 96), None, None, '5x', '族譜節點（頭像窗 d80 @8,8）')(lambda w, h, k=k: _node(w, h, k))
part('tree_line_h', (60, 4), '3h', [0, 0, 0, 0], '5x', '族譜橫線')(lambda w, h: hline_im(w, A(C['gold'], .85), 1.5, fade=False))
part('tree_line_v', (4, 60), '3v', [0, 0, 0, 0], '5x', '族譜直線')(lambda w, h: hline_im(h, A(C['gold'], .85), 1.5, fade=False).rotate(90, expand=True))
part('tree_joint', (13, 13), None, None, '5x', '族譜接點')(lambda w, h: diamond_im(5, A(C['goldhi'])))
for k, nm in (('cur', 'room_dot_cur'), ('open', 'room_dot_open'), ('locked', 'room_dot_locked')):
    part(nm, (16, 16), None, None, '5x', '房間頁點')(lambda w, h, k=k: _dot(k))
def _dot(k):
    L = new(16, 16); d = 12 if k == 'cur' else 9; c = C['goldhi'] if k == 'cur' else ((230, 230, 240) if k == 'open' else (110, 114, 136))
    if k == 'cur': L.alpha_composite(glow_im(8, C['gold'], .6))
    L.alpha_composite(masked(new(d, d, A(c)), circ_mask(d)), ((16 - d) // 2, (16 - d) // 2)); return L
part('pill_fast_on', (100, 34), '3h', [17, 0, 17, 0], '5x', '快 ×2（開）')(lambda w, h: _btn(w, h, 'violet'))
part('pill_fast_locked', (100, 34), '3h', [17, 0, 17, 0], '5x', '快 ×3（鎖）')(lambda w, h: hair_rr_im(w, h, h / 2, A((160, 164, 186), .6), 1.2))
part('swatch_frame', (26, 26), None, None, '5x', '花紋色板框')(lambda w, h: hair_rr_im(w, h, 7, A(C['gold']), 1.5))
def _joblv(w, h):
    L = new(w, h); L.alpha_composite(masked(vgrad(w, h, A(C['goldhi']), A(C['gold2'])), circ_mask(w))); L.alpha_composite(ring_im(w - 4, A((255, 255, 255), .8), 1.2)); return L
part('job_lv_badge', (28, 28), None, None, '5x', '工作等級章（字 label 18 golddk）')(_joblv)
part('sheet_handle', (60, 8), None, None, 'panel', '底 sheet 拉柄')(lambda w, h: masked(new(w, h, (255, 255, 255, 110)), rr_mask(w, h, 4)))
# ---- 6b／6c／6d
def _qr(w, h):
    L = new(w, h); L.alpha_composite(masked(new(w, h, (255, 255, 255, 255)), rr_mask(w, h, 16))); L.alpha_composite(hair_rr_im(w, h, 16, A(C['gold']), 2)); L.alpha_composite(hair_rr_im(w, h, 16, A(C['gold'], .4), 1, 5)); return L
part('qr_frame', (198, 198), '9', [24] * 4, '6d', '6d QR 框（白位 inset 12）')(_qr)
def _field(w, h, on):
    L = masked(vgrad(w, h, A((8, 12, 28), .7), A((8, 12, 28), .5)), rr_mask(w, h, 14)); L.alpha_composite(hair_rr_im(w, h, 14, A(C['goldhi'] if on else (255, 255, 255), 1 if on else .25), 1.5 if on else 1))
    if on: L.alpha_composite(masked(vgrad(w, h, A(C['gold'], .14), A(C['gold'], 0)), rr_mask(w, h, 14)))
    return L
part('code_field', (300, 56), '3h', [18, 0, 18, 0], '6d', '6d 輸入格')(lambda w, h: _field(w, h, False))
part('code_field_on', (300, 56), '3h', [18, 0, 18, 0], '6d', '6d 輸入格 focus')(lambda w, h: _field(w, h, True))
def _sharebg(w, h):
    L = _smoked(w, h, 28, .95, .95); compc(L, glow_im(w * .45, C['gold'], .25), w / 2, h * .2)
    for (x, y, r) in ((40, 60, 12), (w - 50, 110, 20), (60, h - 120, 12)): compc(L, flare_im(r, (255, 236, 200), .6), x, y)
    return L
part('share_card_bg', (495, 756), None, None, '6d', '6d 分享名片底（存相 @3x 495×756；整張唔切）')(_sharebg)
def _dreamframe(w, h):
    L = new(w, h); L.alpha_composite(glow_im(w / 2, C['violet'], .35).resize((w, h))); L.alpha_composite(hair_rr_im(w - 16, h - 16, 18, A((214, 204, 255)), 2), (8, 8)); L.alpha_composite(hair_rr_im(w - 26, h - 26, 14, A(C['goldhi'], .6), 1), (13, 13)); return L
part('dream_card_frame', (196, 268), '9', [30] * 4, '6c', '6c 夢卡外框光（疊喺 card 圖外）')(_dreamframe)
def _walkbar(w, h):
    L = _track(w, h); return L
part('walk_track', (300, 8), '3h', [5, 0, 5, 0], '6b', '6b 散步進度（配 bar_fill_mint）')(_walkbar)
def _stone(w, h):
    L = new(w, h); L.alpha_composite(ring_im(w - 6, A(C['mint'], .9), 1.5), (1, 1)); return L
part('walk_step', (22, 22), None, None, '6b', '6b 踏腳石格（已行：配 glow）')(_stone)

# ================================================================ 文字（記錄字級＋對比）
TEXTLOG = []; SCREEN = ['?']
def text(bd, t, x, y, role='body', col=None, anchor='la', kind=None, sh=None, check=True):
    col = col or C['cream']; k, sz = TYPE[role]; f = F(kind or k, sz); d = ImageDraw.Draw(bd); bb = d.textbbox((x, y), t, font=f, anchor=anchor)
    bb = (max(0, bb[0]), max(0, bb[1]), min(bd.width, bb[2]), min(bd.height, bb[3]))
    if sh:   # 柔陰影（shadowBlur）屬背景一部分：喺量對比之前畫
        L = Image.new('RGBA', bd.size, A(sh, 0)); ImageDraw.Draw(L).text((x, y + 2), t, font=f, anchor=anchor, fill=A(sh, 1)); bd.alpha_composite(L.filter(ImageFilter.GaussianBlur(2.2)))
    bg = np.array(bd.crop(bb))[..., :3]
    d.text((x, y), t, font=f, anchor=anchor, fill=A(col))
    cr = None
    if check and bg.size:
        lf = lum(col); lb = lum(bg); cr = float(np.percentile((np.maximum(lf, lb) + .05) / (np.minimum(lf, lb) + .05), 5))
    TEXTLOG.append(dict(screen=SCREEN[0], text=t, role=role, px=sz, font=kind or k, contrast=None if cr is None else round(cr, 2)))
    return bb
def tw(t, role='body', kind=None): k, sz = TYPE[role]; return ImageDraw.Draw(new(1, 1)).textlength(t, font=F(kind or k, sz))

# ================================================================ icon（v3 像素，@3x 原生 32px／mini 22px／badge 64px）
_IC = {}
def IC(name):
    if name not in _IC:
        p = f'{KIT}/icons/{name}@3x.png'; g = f'{KIT}/icons/glow/{name}_glow@3x.png'
        _IC[name] = (Image.open(p).convert('RGBA'), Image.open(g).convert('RGBA') if os.path.exists(g) else None)
    return _IC[name]
ICONS_USED = set()
def icon(bd, name, cx, cy, glow=False, scale=1):
    sp, gl = IC(name); ICONS_USED.add(name)
    if scale != 1: sp = sp.resize((sp.width * scale, sp.height * scale), Image.NEAREST); gl = gl.resize((gl.width * scale, gl.height * scale), Image.LANCZOS) if gl else None
    if glow and gl is not None: compc(bd, gl, cx, cy)
    compc(bd, sp, cx, cy)
