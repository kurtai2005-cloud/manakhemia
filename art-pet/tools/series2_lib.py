# 《微光小圃》series2「細佬」4a — 共用像素工具（純 Pillow/numpy，冇 AI 生圖）
import json, math, os
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ART = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))           # .../art-pet
T48 = os.path.join(ART, "sprites/tuanrong/species_concept/from_ref/tuned_48")
S2 = os.path.join(ART, "sprites/series2")
S = 48; PIV = (24, 45); GROUND = 46
CROSS = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool)
ROWS = "ABCDEFGH"
EYE_DK = (34, 26, 44); WHITE = (255, 255, 255); BLUSH = (240, 128, 150)

def rgba(p): return np.array(Image.open(p).convert("RGBA"))
def save(a, p):
    os.makedirs(os.path.dirname(p), exist_ok=True); Image.fromarray(np.ascontiguousarray(a)).save(p)
def hexc(h): h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def hexs(c): return "#%02x%02x%02x" % tuple(int(t) for t in c[:3])
def lum(c): c = np.asarray(c, float); return c[..., 0] * .299 + c[..., 1] * .587 + c[..., 2] * .114
def mix(a, b, t): return tuple(int(round(a[i] * (1 - t) + b[i] * t)) for i in range(3))
def canvas(w, h): return np.zeros((h, w, 4), np.uint8)
def put(img, x, y, c):
    x, y = int(x), int(y)
    if 0 <= x < img.shape[1] and 0 <= y < img.shape[0]: img[y, x] = (*[int(v) for v in c[:3]], 255)
def paste(dst, src, x, y):
    """alpha 0/255 合成（src 255 蓋 dst）"""
    x, y = int(x), int(y); h, w = src.shape[:2]; H, W = dst.shape[:2]
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + w), min(H, y + h)
    if x0 >= x1 or y0 >= y1: return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]; m = s[..., 3] >= 128
    d = dst[y0:y1, x0:x1]; d[m] = s[m]; d[m, 3] = 255
def ncolors(a):
    m = a[..., 3] == 255
    return int(len(np.unique(a[m][:, :3], axis=0))) if m.any() else 0
def grid(img, rows, x, y, cmap):
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch in cmap: put(img, x + i, y + j, cmap[ch])

def ellipse(w, h, cx, cy, rx, ry):
    Y, X = np.mgrid[0:h, 0:w].astype(float)
    return ((X + .5 - cx) / rx) ** 2 + ((Y + .5 - cy) / ry) ** 2 <= 1.0

def shade_body(img, mask, ramp, outline, light=(-0.7, -0.75), spec=True, inner_shade=True):
    """ramp=(hi, base, mid, dark)；左上光；外框＝mask 最外 1px（同 from_ref 一樣喺 mask 內）"""
    ys, xs = np.nonzero(mask)
    if not len(ys): return img
    cx, cy = (xs.min() + xs.max() + 1) / 2, (ys.min() + ys.max() + 1) / 2
    rx, ry = max(1, (xs.max() - xs.min() + 1) / 2), max(1, (ys.max() - ys.min() + 1) / 2)
    edge = mask & ~ndi.binary_erosion(mask, structure=CROSS, border_value=0)
    inner = mask & ~edge
    inedge = inner & ~ndi.binary_erosion(inner, structure=CROSS, border_value=0)
    lx, ly = light
    for y, x in zip(ys, xs):
        u, v = (x + .5 - cx) / rx, (y + .5 - cy) / ry
        d = -(u * lx + v * ly) / math.hypot(lx, ly)          # 1 = 背光（右下）
        r2 = u * u + v * v
        val = d * 0.75 + r2 * 0.35
        c = ramp[0] if val < -0.42 else ramp[1] if val < 0.28 else ramp[2] if val < 0.62 else ramp[3]
        img[y, x] = (*c, 255)
    if inner_shade:
        gy, gx = np.gradient(ndi.gaussian_filter(mask.astype(float), 1.2))
        for y, x in zip(*np.nonzero(inedge)):
            nx, ny = -gx[y, x], -gy[y, x]; nn = math.hypot(nx, ny) or 1
            if (nx + ny) / nn / math.sqrt(2) > 0.45: img[y, x] = (*ramp[3], 255)
    if spec:
        hx_, hy_ = int(cx - rx * 0.45), int(cy - ry * 0.5)
        for dx, dy in ((0, 0), (1, 0), (0, 1)):
            if inner[hy_ + dy, hx_ + dx]: img[hy_ + dy, hx_ + dx] = (*WHITE, 255)
    for y, x in zip(*np.nonzero(edge)): img[y, x] = (*outline, 255)
    return img

EYE = {"dark": [".DD.", "DDHD", "DDDD", ".DD."]}
def draw_eye(img, x, y, kind="dark"):
    grid(img, EYE[kind], x, y, {"D": EYE_DK, "H": WHITE})
def blink_eye(img, x, y, skin):
    for j in range(4):
        for i in range(4): put(img, x + i, y + j, skin)
    for dx, dy in ((0, 1), (1, 2), (2, 2), (3, 1)): put(img, x + dx, y + dy, EYE_DK)
MOUTH4 = [(0, 0), (3, 0), (1, 1), (2, 1)]
def draw_mouth(img, x, y, ink=EYE_DK):
    for dx, dy in MOUTH4: put(img, x + dx, y + dy, ink)
def draw_blush(img, x, y):
    for dx in range(3): put(img, x + dx, y, BLUSH)

def idle_frames(out, eyes):
    """同 tuned_48：0 原、1 上半落 1px、2 原、3 眨眼。eyes=[(x,y,skin)]"""
    a = out[..., 3] == 255; rows = np.nonzero(a.any(1))[0]; cut = int(rows.min() + 0.6 * (rows.max() - rows.min()))
    f1 = out.copy(); f1[1:cut + 1] = out[0:cut]; f1[0] = 0
    f3 = out.copy()
    for (x, y, skin) in eyes: blink_eye(f3, x, y, skin)
    return [out, f1, out.copy(), f3], cut

def ring_skin(img, x, y, w=4, h=4):
    vals = []
    for yy in range(y - 1, y + h + 1):
        for xx in range(x - 1, x + w + 1):
            if x <= xx < x + w and y <= yy < y + h: continue
            if 0 <= yy < img.shape[0] and 0 <= xx < img.shape[1] and img[yy, xx, 3] == 255: vals.append(tuple(int(t) for t in img[yy, xx, :3]))
    if not vals: return (220, 220, 220)
    u, c = np.unique(np.array(vals), axis=0, return_counts=True)
    return tuple(int(t) for t in u[np.argmax(c)])

def limit_colors(a, n=12, protect=()):
    """合併最近色（保留 protect 色）直到 ≤n"""
    a = a.copy(); m = a[..., 3] == 255
    while True:
        cols, cnt = np.unique(a[m][:, :3], axis=0, return_counts=True)
        if len(cols) <= n: return a
        prot = [i for i, c in enumerate(cols) if tuple(c) in set(map(tuple, protect))]
        # 最少用嘅非保護色 → 併去最近色
        order = [i for i in np.argsort(cnt) if i not in prot]
        i = order[0]; c = cols[i].astype(int)
        d = np.abs(cols.astype(int) - c).sum(1); d[i] = 1 << 30
        j = int(np.argmin(d)); sel = m & np.all(a[..., :3] == cols[i], -1); a[sel, :3] = cols[j]
