# 《微光小圃》HD-2D v2 概念 — 像素 UI 零件庫（全部 1x 畫，之後 ×3 nearest）＋寵物即場合成／頭像裁切
# 遊美 2026-11-02。純 Pillow／numpy，冇 AI 圖。字體：Fusion Pixel（OFL）點陣字。
import os, sys, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ART = os.path.dirname(HERE)
sys.path.insert(0, HERE)
OUT = f'{ART}/ui/style_ref/hd2d_v2'
FD = f'{OUT}/fonts'
def hx(h, a=255):
    h = h.lstrip('#'); return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)
P = dict(line=hx('#24172C'), g_hi=hx('#FFF6CF'), g_mid=hx('#EDBE62'), g_lo=hx('#9C6630'), g_dk=hx('#6A3F22'), g_br=hx('#FFE29A'),
         nv0=hx('#4A5A9C'), nv1=hx('#34427C'), nv2=hx('#262F60'), nv3=hx('#181D3C'), nv4=hx('#10132A'),
         cream=hx('#FFF5DC'), ink=hx('#3A2840'), paper0=hx('#FFF9EA'), paper1=hx('#F4E4C4'), paper2=hx('#DEC59A'),
         gem0=hx('#FFD6DE'), gem1=hx('#FF7F9C'), gem2=hx('#C42E57'), tl0=hx('#D6FFF8'), tl1=hx('#5FD3D0'), tl2=hx('#1F7F99'),
         vi0=hx('#EEE2FF'), vi1=hx('#A98BF0'), vi2=hx('#5C3FB0'), red=hx('#FF4D6D'), white=hx('#FFFFFF'), trough=hx('#0B0E22'))
FILLS = {  # 3 tone + 高光
    'pri': [hx('#FFF1C2'), hx('#FFD06A'), hx('#F28B3E'), hx('#B5551F')],
    'rose': [hx('#FFE1EA'), hx('#FF9DB8'), hx('#E2577F'), hx('#9E2F55')],
    'sec': [hx('#E2FFF9'), hx('#86E6DC'), hx('#3797B4'), hx('#1E5E80')],
    'violet': [hx('#F1E8FF'), hx('#BFA5FF'), hx('#7A5CD6'), hx('#4A3392')],
    'navy': [hx('#6273B8'), hx('#3F4E8E'), hx('#28316A'), hx('#181D3C')],
    'paper': [hx('#FFFFFF'), hx('#FFF6E2'), hx('#F0DDB6'), hx('#C9A877')],
    'green': [hx('#E8FFD6'), hx('#A6E27A'), hx('#4E9E4A'), hx('#2C6334')],
}
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0 + 1 / 32

def new(w, h, c=(0, 0, 0, 0)): return Image.new('RGBA', (w, h), c)
def arr(im): return np.array(im)
def img(a): return Image.fromarray(a.astype(np.uint8), 'RGBA')
def up(im, s=3): return im.resize((im.width * s, im.height * s), Image.NEAREST)

def erode(m):
    o = m.copy(); o[1:] &= m[:-1]; o[:-1] &= m[1:]; o[:, 1:] &= m[:, :-1]; o[:, :-1] &= m[:, 1:]
    o[0, :] = False; o[-1, :] = False; o[:, 0] = False; o[:, -1] = False; return o
def dilate(m, diag=True):
    o = m.copy(); o[1:] |= m[:-1]; o[:-1] |= m[1:]; o[:, 1:] |= m[:, :-1]; o[:, :-1] |= m[:, 1:]
    if diag: o[1:, 1:] |= m[:-1, :-1]; o[:-1, :-1] |= m[1:, 1:]; o[1:, :-1] |= m[:-1, 1:]; o[:-1, 1:] |= m[1:, :-1]
    return o

def dgrad(t, cols, ox=0, oy=0):
    """t: HxW 0..1 → 用 Bayer 4x4 喺 cols（list RGBA）之間抖色，返 HxWx4"""
    h, w = t.shape; n = len(cols) - 1; v = np.clip(t, 0, 1) * n
    i0 = np.floor(v).astype(int); fr = v - i0
    th = np.tile(BAYER, (h // 4 + 2, w // 4 + 2))[oy % 4: oy % 4 + h, ox % 4: ox % 4 + w]
    idx = np.clip(i0 + (fr > th), 0, n)
    C = np.array(cols); return C[idx]

def chamfer_mask(w, h, c):
    m = np.ones((h, w), bool)
    for i in range(c):
        k = c - i
        m[i, :k] = m[i, w - k:] = m[h - 1 - i, :k] = m[h - 1 - i, w - k:] = False
    return m
def circle_mask(d):
    r = d / 2; yy, xx = np.mgrid[0:d, 0:d]; return (xx + .5 - r) ** 2 + (yy + .5 - r) ** 2 <= (r - .15) ** 2
def octo_mask(w, h, c): return chamfer_mask(w, h, c)

def bevel_ring(a, ring, outer, hi, mid, lo):
    """ring 像素：外邊向上／左 → hi，向下／右 → lo，其餘 mid（光源左上）"""
    h, w = ring.shape
    up_ = np.zeros_like(ring); up_[1:] = ~outer[:-1]; lf = np.zeros_like(ring); lf[:, 1:] = ~outer[:, :-1]
    dn = np.zeros_like(ring); dn[:-1] = ~outer[1:]; rt = np.zeros_like(ring); rt[:, :-1] = ~outer[:, 1:]
    up_[0] = True; lf[:, 0] = True; dn[-1] = True; rt[:, -1] = True
    a[ring] = mid
    a[ring & (dn | rt)] = lo
    a[ring & (up_ | lf)] = hi

def frame(mask, fill='navy', gold=2, glass=True, tex=True, rim_glints=True, seed=0, inner_line=True, sheen=True):
    """通用金框面板：mask（HxW bool）→ RGBA。外 1px 深線、gold px 金斜角、內 1px 深線、內面抖色漸變＋紋理＋內陰影＋玻璃反光"""
    h, w = mask.shape; a = np.zeros((h, w, 4), np.uint8)
    m0 = mask; a[m0] = P['line']
    m1 = erode(m0)
    if gold >= 1:
        m2 = erode(m1); bevel_ring(a, m1 & ~m2, m1, P['g_hi'], P['g_mid'], P['g_lo']); cur = m2
        if gold >= 2:
            m3 = erode(m2); ring = m2 & ~m3; a[ring] = P['g_mid']
            # 第二圈：上半亮、下半暗少少
            yy = np.mgrid[0:h, 0:w][0]; a[ring & (yy > h * .55)] = P['g_lo']; a[ring & (yy < h * .3)] = P['g_br']; cur = m3
    else: cur = m1
    if inner_line: a[cur & ~erode(cur)] = P['line']; inn = erode(cur)
    else: inn = cur
    yy, xx = np.mgrid[0:h, 0:w]
    ys = np.where(inn.any(1))[0]; y0, y1 = (ys[0], ys[-1]) if len(ys) else (0, h)
    t = (yy - y0) / max(1, (y1 - y0))
    fk = fill if isinstance(fill, str) else 'navy'
    if isinstance(fill, str) and fill in FILLS:
        cols = FILLS[fill][::-1] if fill not in ('navy',) else [FILLS['navy'][1], FILLS['navy'][2], FILLS['navy'][3], P['nv4']]
        if fill != 'navy': cols = [FILLS[fill][1], FILLS[fill][2], FILLS[fill][3]]
        g = dgrad(t * .95 + .02, cols)
    else: g = dgrad(t, fill)
    a[inn] = g[inn]
    # 內陰影：內面頂 2 行深一級、左 1 列
    sh = inn & ~erode(inn)
    top2 = inn & ~np.roll(inn, 2, axis=0)
    dark = np.array(P['nv4'] if fk == 'navy' else FILLS[fk][3])
    a[(top2) & inn] = (a[(top2) & inn] * .55 + dark * .45).astype(np.uint8)
    a[sh & (np.roll(~inn, 1, axis=1))] = (a[sh & (np.roll(~inn, 1, axis=1))] * .7 + dark * .3).astype(np.uint8)
    # 底內緣 1px 微光（反射）
    bot = inn & ~np.roll(inn, -1, axis=0)
    lift = np.array(P['nv0'] if fk == 'navy' else FILLS[fk][1])
    a[bot] = (a[bot] * .5 + lift * .5).astype(np.uint8)
    if tex:  # 布紋／玻璃顆粒：斜格 4px 一點，亮一級
        pat = ((xx + yy) % 4 == 0) & ((xx - yy) % 8 == 0) & inn & ~top2
        a[pat] = np.clip(a[pat].astype(int) + [14, 16, 26, 0], 0, 255).astype(np.uint8)
    if glass and sheen:  # 左上斜反光帶（50% checker）
        band = ((xx * 0.55 + yy) > (y0 + 1)) & ((xx * 0.55 + yy) < (y0 + 1 + max(3, (y1 - y0) * .28))) & inn & ((xx + yy) % 2 == 0) & ~top2
        band &= xx < w * .6
        a[band] = np.clip(a[band].astype(int) + [22, 24, 34, 0], 0, 255).astype(np.uint8)
    if rim_glints and gold:
        rng = np.random.default_rng(seed)
        topr = np.where(m1[1] if h > 2 else m1[0])[0]
        for x in rng.choice(topr, size=min(len(topr), max(1, w // 14)), replace=False):
            if 0 < x < w - 1: a[1, x] = P['white']
    return img(a)

def gem(kind='rose', size=5):
    """菱形寶石 5/7px：外框＋三色＋白點高光"""
    s = size; c = s // 2; a = np.zeros((s, s, 4), np.uint8)
    yy, xx = np.mgrid[0:s, 0:s]; m = (abs(xx - c) + abs(yy - c)) <= c
    a[m] = P['line']; inn = (abs(xx - c) + abs(yy - c)) <= c - 1
    F = FILLS[kind]; a[inn] = F[2]; a[inn & (xx + yy < s - 1)] = F[1]; a[inn & (xx + yy > s)] = F[3]
    a[c - 1 if s > 5 else c - 1, c - 1 if s > 5 else c] = P['white']
    if s >= 7: a[c - 2, c] = F[0]
    return img(a)

def rivet():
    a = np.zeros((3, 3, 4), np.uint8); a[:] = 0
    a[0, 1] = a[1, 0] = P['g_hi']; a[1, 1] = P['g_mid']; a[1, 2] = a[2, 1] = P['g_lo']; a[0, 0] = a[0, 2] = a[2, 0] = a[2, 2] = (0, 0, 0, 0)
    return img(a)

def sparkle(n=5, col='cream'):
    a = np.zeros((n, n, 4), np.uint8); c = n // 2; C = P[col] if col in P else col
    for i in range(n):
        a[c, i] = C; a[i, c] = C
    a[c, 0] = a[c, -1] = a[0, c] = a[-1, c] = P['g_mid'] if n >= 5 else C
    if n >= 7: a[c, 1] = a[c, -2] = a[1, c] = a[-2, c] = P['g_br']
    a[c, c] = P['white']; return img(a)

def medal(d, fill='pri', ring=2, spec=True):
    m = circle_mask(d); a = np.zeros((d, d, 4), np.uint8); a[m] = P['line']
    m1 = erode(m); yy, xx = np.mgrid[0:d, 0:d]; cx = cy = (d - 1) / 2
    ang = np.arctan2(yy - cy, xx - cx)  # -pi..pi；左上 = -3pi/4
    lit = np.cos(ang + 3 * np.pi / 4)  # 1 = 左上
    cur = m1
    for r in range(ring):
        nx = erode(cur); rg = cur & ~nx
        if r == 0:
            a[rg] = P['g_mid']; a[rg & (lit > .35)] = P['g_hi']; a[rg & (lit < -.35)] = P['g_lo']
        else:
            a[rg] = P['g_br']; a[rg & (lit < -.2)] = P['g_mid']; a[rg & (lit < -.7)] = P['g_lo']
        cur = nx
    a[cur & ~erode(cur)] = P['line']; inn = erode(cur)
    F = FILLS[fill]; r = d / 2
    dist = np.sqrt((xx - (cx - r * .3)) ** 2 + (yy - (cy - r * .35)) ** 2) / (r * 1.25)
    g = dgrad(dist, [F[0], F[1], F[2], F[3]]); a[inn] = g[inn]
    # 內陰影（下右）＋ 頂反光弧
    edge = inn & ~erode(inn)
    a[edge & (lit < -.1)] = F[3]
    if spec:
        sp = inn & (np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) > r - 5.2) & (np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) < r - 3.6) & (lit > .55)
        a[sp] = F[0]
        a[sp & ((xx + yy) % 2 == 0)] = P['white']
    return img(a)

# ---------------------------------------------------------------- 字
_FONT = {}
def font(sz):
    if sz not in _FONT: _FONT[sz] = ImageFont.truetype(f'{FD}/fusion-pixel-{sz}px-proportional-zh_hk.ttf', sz)
    return _FONT[sz]
def text_img(t, sz=12, col='cream', col2=None, outline='line', shadow=True, ol=True):
    f = font(sz); bb = f.getbbox(t); gt = f.getbbox('國')[1]; gb = max(f.getbbox('國gy')[3], f.getbbox('國')[3])
    W = bb[2] - bb[0] + 4; H = gb - gt + 4
    m = Image.new('L', (W, H), 0); d = ImageDraw.Draw(m); d.fontmode = '1'; d.text((2 - bb[0], 2 - gt), t, font=f, fill=255)
    M = np.array(m) > 127
    ys = np.where(M.any(1))[0]
    a = np.zeros((H + 1, W, 4), np.uint8)
    C1 = np.array(P[col] if isinstance(col, str) else col); C2 = np.array(P[col2] if isinstance(col2, str) else (col2 if col2 else C1))
    if ol:
        O = dilate(np.pad(M, ((0, 1), (0, 0))))
        if shadow: S = np.roll(O, 1, axis=0); a[S] = P['line']
        a[O] = P[outline] if isinstance(outline, str) else outline
    MM = np.pad(M, ((0, 1), (0, 0)))
    if len(ys):
        yy = np.mgrid[0:H + 1, 0:W][0]; mid = ys[0] + (ys[-1] - ys[0]) * .55
        a[MM] = C1; a[MM & (yy > mid)] = C2
    return img(a)
def put(bd, im, x, y): bd.alpha_composite(im, (int(round(x)), int(round(y))))
def putc(bd, im, cx, cy): put(bd, im, cx - im.width / 2, cy - im.height / 2)
def text(bd, t, x, y, sz=12, anchor='l', **kw):
    im = text_img(t, sz, **kw)
    if anchor == 'm': x -= im.width / 2
    elif anchor == 'r': x -= im.width
    put(bd, im, x - 1, y - im.height / 2); return im.width

# ---------------------------------------------------------------- icon 像素化（kit 3x icon → 1x 像素、≤12 色、重新描邊）
ICD = f'{ART}/ui/kit_hd2d/icons'
_IC = {}
def icon_px(name, size, outline=True, ncol=12):
    key = (name, size)
    if key in _IC: return _IC[key]
    im = Image.open(f'{ICD}/ic_{name}@3x.png').convert('RGBA'); A = np.array(im)
    m = A[..., 3] > 150; ys, xs = np.where(m); im = im.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    s = size / max(im.size); tw, th = max(1, round(im.width * s)), max(1, round(im.height * s))
    inner = size - 2 if outline else size; s2 = inner / max(im.size); tw, th = max(1, round(im.width * s2)), max(1, round(im.height * s2))
    sm = im.resize((tw, th), Image.BOX); a = np.array(sm)
    msk = a[..., 3] > 150
    rgb = Image.fromarray(a[..., :3]).quantize(ncol, method=Image.MEDIANCUT).convert('RGB'); a[..., :3] = np.array(rgb); a[..., 3] = np.where(msk, 255, 0)
    # 暗化最外一圈（原 icon 已有描邊，用 line 色統一）
    out = np.zeros((th + 2, tw + 2, 4), np.uint8); out[1:-1, 1:-1] = a; M = out[..., 3] > 0
    if outline:
        O = dilate(M, diag=False) & ~M; out[O] = P['line']
    _IC[key] = img(out); return _IC[key]

# ---------------------------------------------------------------- bar
def bar(w, h, v, fill='pri', seg=5, icon=None, low=False):
    """需要值條：金細框＋深槽＋三色填充＋分格＋尾光"""
    m = chamfer_mask(w, h, 1); a = np.zeros((h, w, 4), np.uint8); a[m] = P['line']
    m1 = erode(m); m2 = erode(m1); bevel_ring(a, m1 & ~m2, m1, P['g_hi'], P['g_mid'], P['g_lo'])
    a[m2] = P['trough']; inn = erode(m2)
    a[m2 & ~np.roll(m2, 1, 0)] = P['line']
    F = FILLS['rose' if low else fill]
    ys, xs = np.where(m2); x0, x1 = xs.min(), xs.max(); y0, y1 = ys.min(), ys.max()
    fw = int(round((x1 - x0 + 1) * v))
    if fw > 0:
        a[y0:y1 + 1, x0:x0 + fw] = F[2]
        a[y0, x0:x0 + fw] = F[0]
        if y1 - y0 >= 2: a[y0 + 1, x0:x0 + fw] = F[1]
        a[y1, x0:x0 + fw] = F[3]
        for sx in range(x0 + seg, x0 + fw, seg): a[y0 + 1:y1 + 1, sx] = F[3]
        a[y0:y1, min(x0 + fw - 1, x1)] = P['white']
    return img(a)

# ---------------------------------------------------------------- 寵物合成（同花園一樣）＋頭像
SP = f'{ART}/sprites'
ANCH = json.load(open(f'{SP}/tuanrong/reactions/anchors.json'))
S2T = json.load(open(f'{SP}/series2/forms/tuned.json'))['creatures']
S2F = json.load(open(f'{SP}/series2/faces/faces.json'))
L5C = json.load(open(f'{SP}/series2_long/5c/long_5c.json'))
OLD_CLIP = dict(normal=('idle', 1), happy=('emo_happy', 2), hungry=('emo_hungry', 2), sleepy=('emo_sleepy', 2), sick=('sick', 2), sleep=('sleep_loop', 2))
NEW_FACE = dict(normal=None, happy='laugh_a', hungry='lookup', sleepy='sleepy', sick='dizzy_a', sleep='sleep')
S2_FACE = dict(normal=None, happy='happy', hungry='pout', sleepy='sleepy', sick='dizzy_a', sleep='sleep')
PAD = 8
def _strip(p, i, fw=48, fh=48): return Image.open(p).convert('RGBA').crop((i * fw, 0, i * fw + fw, fh))

def compose_pet(form, state='normal', acc=(), wear=None, pattern_from=None):
    """回傳 (RGBA 已加 PAD 8, info)；同引擎畫花園一樣：身體 → 面 → 花紋 → 穿戴／飾品"""
    if form in ANCH and ANCH[form]['line'] == 'old':
        import compose_accessory_runtime as C
        clip, k = OLD_CLIP[state]
        if acc: a, hid = C.compose(form, clip, k, list(acc))
        else:
            S = C.attach(form)['frameSize']; a = np.zeros((S + 2 * PAD, S + 2 * PAD, 4), np.uint8); a[PAD:PAD + S, PAD:PAD + S] = C.body(form, clip, k)
        im = img(a); an = ANCH[form]['anchors']; S = ANCH[form]['frameSize'][0]
        eyes = (np.array(an['eyeL']) + an['eyeR']) / 2 + PAD
        return im, dict(eyes=eyes.tolist(), headTop=an['headTop'][1] + PAD, eyeDist=ANCH[form]['eyeDist'], pivot=[an['pivot'][0] + PAD, an['pivot'][1] + PAD], frame=S, line='old')
    base = new(48 + 2 * PAD, 48 + 2 * PAD)
    if form in ANCH:  # 新蛋線 A1–H3
        body = _strip(f'{SP}/tuanrong/species_concept/from_ref/tuned_48/idle/{form}_idle.png', 0)
        fc = NEW_FACE[state]; order = ANCH[form]['faces']['order']
        base.alpha_composite(body, (PAD, PAD))
        if fc: base.alpha_composite(_strip(f'{SP}/tuanrong/reactions/faces/{form}_faces.png', order.index(fc)), (PAD, PAD))
        an = ANCH[form]['anchors']; eyes = (np.array(an['eyeL']) + an['eyeR']) / 2; ed = ANCH[form]['eyeDist']; piv = an['pivot']; ht = an['headTop'][1]
    else:  # 細佬 series2
        body = _strip(f'{SP}/series2/actions/{form}_idle.png', 0); base.alpha_composite(body, (PAD, PAD))
        fc = S2_FACE[state]; order = S2F[form]['order']
        if fc: base.alpha_composite(_strip(f'{SP}/series2/{S2F[form]["png"]}', order.index(fc)), (PAD, PAD))
        e = S2T[form]['eyes']; eyes = np.array([(e[0]['x'] + e[1]['x']) / 2 + .5, (e[0]['y'] + e[1]['y']) / 2 + .5]); ed = abs(e[1]['x'] - e[0]['x']); piv = [24, 45]
        ba = np.array(body)[..., 3] > 0; ht = float(np.where(ba.any(1))[0][0]) + 2
    if pattern_from:  # 5c 花紋 overlay（mask R≥190→hi，其餘→lo）
        pt = L5C['parents'][pattern_from]; row = [r for r in L5C['overlay']['forms'][form]['rows'] if r['clip'] == 'idle' and r['pattern'] == pt['pattern']][0]
        pm = Image.open(f'{SP}/series2_long/5c/{L5C["overlay"]["forms"][form]["png"]}').convert('RGBA').crop((0, row['y'], 48, row['y'] + 48))
        q = np.array(pm); hi = np.array(hx(pt['tint']['hi'])); lo = np.array(hx(pt['tint']['lo']))
        o = np.zeros_like(q); m = q[..., 3] > 0; o[m] = lo; o[m & (q[..., 0] >= 190)] = hi
        base.alpha_composite(img(o), (PAD, PAD))
    if wear: base.alpha_composite(_strip(f'{SP}/tuanrong/reactions/wear/{form}_{wear}.png', 0), (PAD, PAD))
    eyes = (np.array(eyes) + PAD).tolist()
    return base, dict(eyes=eyes, headTop=ht + PAD, eyeDist=ed, pivot=[piv[0] + PAD, piv[1] + PAD], frame=48, line='new' if form in ANCH else 's2')

def bust_rect(info, n):
    """頭像裁切框（sprite px，已含 PAD）：眼中點做錨，n×n；眼喺框 66% 高度（見到頭頂輪廓）"""
    ex, ey = info['eyes']; ht = info.get('headTop', ey - n * .6)
    above = min(max(ey - ht + 1.5, n * .5), n * .68)   # 頭頂盡量入框，但眼唔低過 68%
    x0 = int(round(ex - n / 2)); y0 = int(round(ey - above)); return (x0, y0, x0 + n, y0 + n)

MOOD = {'normal': ('sec', None), 'happy': ('rose', 'heart'), 'hungry': ('pri', 'feed'), 'sleepy': ('violet', 'sleep'), 'sick': ('green', 'sick'), 'sleep': ('violet', 'zz')}
def mood_glyph(kind):
    G = {
        'heart': ["..o.o..", ".oRoRo.", "oRRRRRo", "oRRRRRo", ".oRRRo.", "..oRo..", "...o..."],
        'feed': ["...o...", "..oWo..", ".oWWWo.", ".oWWWo.", "oWKKKWo", "oWKKKWo", "ooooooo"],
        'sleep': ["ooooo..", "...o...", "..o....", ".o.ooo.", "ooooo.o", "....o..", "...ooo."],
        'zz': ["ooooo..", "...o...", "..o....", ".o.ooo.", "ooooo.o", "....o..", "...ooo."],
        'sick': ["..ooo..", ".oGGGo.", "oGGWGGo", "oGWWWGo", "oGGWGGo", ".oGGGo.", "..ooo.."],
    }[kind]
    cm = {'o': P['line'], 'R': FILLS['rose'][2], 'W': P['white'], 'K': hx('#2E4A3A'), 'G': FILLS['green'][2]}
    if kind in ('sleep', 'zz'): cm['o'] = P['white']
    a = np.zeros((7, 7, 4), np.uint8)
    for y, r in enumerate(G):
        for x, ch in enumerate(r):
            if ch != '.': a[y, x] = cm[ch]
    im = img(a)
    if kind in ('sleep', 'zz'):  # 白字加深色描邊
        M = a[..., 3] > 0; b = np.zeros((9, 9, 4), np.uint8); MM = np.pad(M, 1); b[dilate(MM)] = P['vi2'] if True else P['line']; b[1:-1, 1:-1][M] = P['white']; im = img(b)
    return im

def portrait(form, state='normal', acc=(), wear=None, pattern_from=None, n=22, scale=2, shape='octo', pop=0, eyefrac=.56):
    """頭像：即場合成幀 → bust 裁 n×n（＋頂 pop 行出框）→ ×scale nearest → 框 mask → 金框＋寶石（色＝心情）＋心情章
    回傳 (RGBA, info, rect)；rect＝(x0,y0,x1,y1) sprite px（含 PAD 8），框內窗＝rect 頂 pop 行以下"""
    pet, info = compose_pet(form, state, acc, wear, pattern_from)
    ex, ey = info['eyes']; x0 = int(round(ex - n / 2)); y0 = int(round(ey - n * eyefrac)); x1, y1 = x0 + n, y0 + n
    pa = np.array(pet)[..., 3] > 0
    colm = pa[:, max(0, x0):x1]; rows = np.where(colm.any(1))[0]
    top = rows[0] if len(rows) else y0
    pp = int(min(pop, max(0, y0 - top)))      # 頭頂／帽要出框幾多行
    cr = new(n, n + pp); cr.alpha_composite(pet.crop((max(0, x0), max(0, y0 - pp), x1, y1)), (max(0, -x0), 0))
    win = n * scale; fr = win + 8; po = pp * scale  # 4px 框（線＋金2＋線）
    mk = chamfer_mask(fr, fr, 5 if shape == 'octo' else 3) if shape != 'round' else circle_mask(fr)
    F = frame(mk, fill=[FILLS['sec'][0], FILLS['sec'][1], FILLS['navy'][0]] if state != 'sleep' else [FILLS['violet'][1], FILLS['violet'][2], FILLS['navy'][2]], gold=2, glass=False, tex=False, seed=3)
    # 背景：心情色抖色（上淺下深）
    fill = MOOD[state][0]; inner = erode(erode(erode(erode(mk))))
    yy = np.mgrid[0:fr, 0:fr][0]; t = (yy - 4) / win
    base3 = [np.array(hx('#EAF6FF')), np.array(hx('#C4E4F4')), np.array(hx('#8FBCDD'))]
    bgc = [tuple((b * .62 + np.array(FILLS[fill][j]) * .38).astype(int)) for j, b in enumerate(base3)] if state != 'normal' else [tuple(b) for b in base3]
    g = dgrad(t * .85, bgc); A = arr(F); A[inner] = g[inner]
    # 地台光圈
    cx = fr / 2; xx = np.mgrid[0:fr, 0:fr][1]
    ring = inner & (((xx - cx) / (win * .45)) ** 2 + ((yy - fr * .5) / (win * .45)) ** 2 < 1) & ((xx + yy) % 2 == 0)
    A[ring] = np.clip(A[ring].astype(int) + 18, 0, 255)
    F = img(A)
    big = up(cr, scale); L = new(fr, fr); L.alpha_composite(big.crop((0, po, win, po + win)), (4, 4))
    la = arr(L); la[~inner] = 0
    F.alpha_composite(img(la))
    fa = arr(F); topr = inner & ~np.roll(inner, 2, 0); fa[topr] = (fa[topr] * .6 + np.array(P['nv3']) * .4).astype(np.uint8); F = img(fa)
    # pop-out：頭頂／帽／蝴蝶結出框（只要寵物像素；描邊本身係 sprite 外框）
    if po:
        popl = big.crop((0, 0, win, po)); ext = new(fr, po + 4); ext.alpha_composite(popl, (4, 0))
        # 同框內一行接駁：框頂 4 行嗰度都用寵物像素蓋（只係 alpha>0）
        seam = big.crop((0, po, win, po + 4)); ext.alpha_composite(seam, (4, po))
        F2 = new(fr, fr + po); F2.alpha_composite(F, (0, po)); F2.alpha_composite(ext, (0, 0)); F = F2
    # 寶石（心情色）＋ 心情章
    out = new(fr + 4, fr + 6 + po); out.alpha_composite(F, (2, 2)); fr_y = po
    gk = {'normal': 'sec', 'happy': 'rose', 'hungry': 'pri', 'sleepy': 'violet', 'sick': 'green', 'sleep': 'violet'}[state]
    putc(out, gem(gk, 7), (fr + 4) / 2, fr + 2 + po)
    mg = MOOD[state][1]
    if mg:
        b = medal(13, MOOD[state][0], ring=1, spec=False); gl = mood_glyph(mg)
        bb = new(13, 13); bb.alpha_composite(b); putc(bb, gl, 6.5, 6.5); put(out, bb, fr - 11, fr - 13 + po)
    info['pop'] = pp; info['popPx'] = po
    return out, info, (x0, y0 - pp, x1, y1)
