# 《微光小圃》UI kit v3 icon — 遊美 2026-11-02
# v2 16px 手點 icon → v3 32px「HD 像素」：Scale2x 邊緣 → 重新打光（左上暖主光 3 階、右下冷 rim、AO）
# → sel-out 描邊（跟鄰色深化，唔再一律 #24172C）→ 高光點 → 另出真 alpha 光暈層（_glow）。
# sprite 本體 alpha 只有 0／255；光暈層先係真 alpha。純 Pillow／numpy。
import os, sys, json
import numpy as np
from PIL import Image, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.abspath(f'{HERE}/../..'); ART = f'{ROOT}/art-pet'
V2 = f'{ART}/ui/kit_hd2d_v2'
def scale2x(a):
    """EPX/Scale2x on RGBA array (H,W,4) → (2H,2W,4)"""
    h, w = a.shape[:2]; p = np.pad(a, ((1, 1), (1, 1), (0, 0)), mode='edge')
    E = p[1:-1, 1:-1]; B = p[:-2, 1:-1]; D = p[1:-1, :-2]; F = p[1:-1, 2:]; H_ = p[2:, 1:-1]
    eq = lambda x, y: np.all(x == y, axis=-1)
    c = ~eq(B, H_) & ~eq(D, F)
    E0 = np.where((c & eq(D, B))[..., None], D, E); E1 = np.where((c & eq(B, F))[..., None], F, E)
    E2 = np.where((c & eq(D, H_))[..., None], D, E); E3 = np.where((c & eq(H_, F))[..., None], F, E)
    out = np.zeros((h * 2, w * 2, 4), a.dtype); out[0::2, 0::2] = E0; out[0::2, 1::2] = E1; out[1::2, 0::2] = E2; out[1::2, 1::2] = E3
    return out
def _lum(c): return c[..., :3] @ np.array([.299, .587, .114])
def enhance(src, glow_col=None):
    """src: PIL RGBA (alpha 0/255) any size → (sprite RGBA 2x, glow RGBA 2x+pad, meta)"""
    a = np.array(src.convert('RGBA')); a[..., 3] = np.where(a[..., 3] > 127, 255, 0)
    b = scale2x(a).astype(float); nn = np.repeat(np.repeat(a, 2, 0), 2, 1).astype(float)
    m0 = a[..., 3] > 0; near0 = np.array(Image.fromarray((~m0 * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))) > 0
    feat = np.repeat(np.repeat(m0 & (_lum(a.astype(float)) < 70) & ~near0, 2, 0), 2, 1)   # 眼／口等內部深色：保持 2×2 方粒（唔俾 EPX 扭）
    featb = (b[..., 3] > 0) & (_lum(b) < 70) & ~np.repeat(np.repeat(near0, 2, 0), 2, 1)
    fix = feat | featb; b[fix] = nn[fix]
    h, w = b.shape[:2]; m = b[..., 3] > 0
    L = _lum(b); near = np.array(Image.fromarray((~m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) > 0
    outl = m & (L < 58) & near                               # 舊描邊（深色＋貼住透明）；眼等內部深色保留
    inner = m & ~outl
    # 高度場 → 法線 → 左上光
    hgt = np.array(Image.fromarray((inner * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.2))).astype(float) / 255
    gy, gx = np.gradient(hgt); n = np.dstack([-gx * 6, -gy * 6, np.ones_like(gx)]); n /= np.linalg.norm(n, axis=-1, keepdims=True)
    Ld = np.array([-.55, -.65, .52]); Ld /= np.linalg.norm(Ld); sh = (n @ Ld)
    sh = (sh - .52) * 2.2                                          # 平面 ≈ 0
    q = np.clip(np.round(sh * 2) / 2, -1, 1)                       # 3 階（-1／-.5／0／.5／1）保持像素色階
    col = b[..., :3].copy()
    warm = np.array([255, 240, 205]); cool = np.array([70, 80, 150])
    up_ = q > 0; dn = q < 0
    col[up_ & inner] = col[up_ & inner] + (warm - col[up_ & inner]) * (q[up_ & inner, None] * .32)
    col[dn & inner] = col[dn & inner] * (1 + q[dn & inner, None] * .22) + cool * (-q[dn & inner, None] * .06)
    # 右下 rim（冷紫邊光）：內部像素而右／下係描邊
    rim = inner & (np.roll(outl, -1, 1) | np.roll(outl, -1, 0)) & (q <= 0)
    col[rim] = col[rim] * .72 + np.array([170, 180, 255]) * .28
    # sel-out：描邊跟最近內部色深化；左上邊淺少少
    blur_c = np.array(Image.fromarray(np.dstack([col * inner[..., None], inner * 255]).astype(np.uint8)).filter(ImageFilter.BoxBlur(2))).astype(float)
    wgt = blur_c[..., 3:4] / 255 + 1e-6; nb = blur_c[..., :3] / wgt
    dark = nb * .30 + np.array([36, 23, 44]) * .62
    col[outl] = dark[outl]
    col[outl & (wgt[..., 0] < .02)] = [36, 23, 44]
    # 高光：每個連通內部區最左上光位 1–2 px 白點
    ys, xs = np.nonzero(inner & (q >= 1))
    if len(ys):
        s = ys + xs; idx = np.argsort(s)[:3]
        for i in idx: col[ys[i], xs[i]] = col[ys[i], xs[i]] * .25 + 255 * .75
    out = np.dstack([col.clip(0, 255), m * 255]).astype(np.uint8)
    # 光暈層（真 alpha）
    if glow_col is None:
        cc = b[inner][:, :3] if inner.any() else np.array([[255, 220, 150]]); sat = cc.max(1) - cc.min(1)
        glow_col = cc[np.argsort(sat)[-max(1, len(cc) // 5):]].mean(0) * .6 + np.array([255, 230, 170]) * .4
    pad = 8; gm = np.zeros((h + 2 * pad, w + 2 * pad)); gm[pad:-pad, pad:-pad] = m
    gm = np.array(Image.fromarray((gm * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(4))).astype(float) / 255
    g = np.zeros((h + 2 * pad, w + 2 * pad, 4)); g[..., :3] = glow_col; g[..., 3] = np.clip(gm * 1.3, 0, 1) * 200
    meta = {'colors_v2': int(len(np.unique(a[a[..., 3] > 0][:, :3], axis=0))), 'colors_v3': int(len(np.unique(out[out[..., 3] > 0][:, :3], axis=0))), 'glow': [int(v) for v in glow_col], 'pad': pad}
    return Image.fromarray(out), Image.fromarray(g.clip(0, 255).astype(np.uint8)), meta

def sources():
    """name → 1x PIL（v2 kit atlas + 6b/6c/6d 新 icon）"""
    J = json.load(open(f'{V2}/atlas/icons_hd2d_v2@1x.json'))['frames']; A = Image.open(f'{V2}/atlas/icons_hd2d_v2@1x.png').convert('RGBA')
    out = {k: A.crop((f['x'], f['y'], f['x'] + f['w'], f['y'] + f['h'])) for k, f in J.items()}
    BT = f'{ROOT}/art/breakthrough'
    extra = {'walk': '6b/ic_walk@1x.png', 'dream': '6c/icons/ic_dream.png', 'dreambook': '6c/icons/ic_dreambook.png',
             'frag_forest': '6c/icons/frag_forest.png', 'frag_lake': '6c/icons/frag_lake.png', 'frag_star': '6c/icons/frag_star.png', 'frag_toy': '6c/icons/frag_toy.png',
             'friend': '6d/icons/ic_friend.png', 'share': '6d/icons/ic_share.png', 'copy': '6d/icons/ic_copy.png', 'paste': '6d/icons/ic_paste.png',
             'photo': '6d/icons/ic_photo.png', 'qr': '6d/icons/ic_qr.png', 'egg_code': '6d/icons/ic_egg_code.png', 'friend_badge': '6d/icons/friend_badge.png'}
    for k, p in extra.items(): out[k] = Image.open(f'{BT}/{p}').convert('RGBA')
    return out
if __name__ == '__main__':
    S = sources(); os.makedirs('/tmp/icv3', exist_ok=True); sheet = Image.new('RGBA', (12 * 80, ((len(S) + 11) // 12) * 80), (24, 30, 56, 255))
    for i, (k, im) in enumerate(S.items()):
        sp, gl, meta = enhance(im); x = (i % 12) * 80 + 8; y = (i // 12) * 80 + 8
        sheet.alpha_composite(gl, (x + 16 - meta['pad'], y + 16 - meta['pad'])); sheet.alpha_composite(sp, (x + 16, y + 16))
    sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST).crop((0, 0, 1920, 640)).save('/tmp/icv3/sheet.png')
    print(len(S))
