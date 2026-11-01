"""batch3b 程序像素畫筆：形狀 → 球面上光（左上光）→ 3 色階 → 部件內線 → 1px 深色外框。
純 numpy/Pillow，冇 AI。俾 build_batch3b.py 用。"""
import math
import numpy as np
from PIL import Image, ImageDraw

OL = (46, 30, 64)            # 同 3a／from_ref 一致嘅深紫外框
EYE = (40, 26, 52)
WHITE = (255, 255, 255)
BLUSH = (240, 128, 150)
LIGHT = np.array([-0.55, -0.68, 0.48]); LIGHT = LIGHT / np.linalg.norm(LIGHT)


def canvas(w, h): return np.zeros((h, w, 4), np.uint8)


class P:
    """一個部件。kind: ell(cx,cy,rx,ry) / poly(pts) / rect(x0,y0,x1,y1) / pix(list)。
    mat = (hi, mid, sh) 或單色 tuple；z 大＝喺前；line＝同後面部件交界畫內線；flat＝唔上光。
    clip = (x0,y0,x1,y1) 只保留呢個框入面。"""
    def __init__(self, kind, args, mat, z=0, line=True, flat=False, clip=None, th=(0.70, 0.22), glow=False):
        self.kind, self.args, self.mat, self.z, self.line, self.flat, self.clip, self.th, self.glow = kind, args, mat, z, line, flat, clip, th, glow

    def mask_normal(self, W, H):
        Y, X = np.mgrid[0:H, 0:W].astype(float); X += .5; Y += .5
        if self.kind == "ell":
            cx, cy, rx, ry = self.args
            u, v = (X - cx) / max(rx, .01), (Y - cy) / max(ry, .01); r2 = u * u + v * v
            m = r2 <= 1.0
            nz = np.sqrt(np.clip(1 - r2, 0, 1)); n = np.stack([u, v, nz], -1)
        else:
            im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im)
            if self.kind == "poly": d.polygon([tuple(p) for p in self.args], fill=1)
            elif self.kind == "rect": d.rectangle(self.args, fill=1)
            elif self.kind == "pix":
                for x, y in self.args:
                    if 0 <= x < W and 0 <= y < H: im.putpixel((int(x), int(y)), 1)
            elif self.kind == "line":
                d.line([tuple(p) for p in self.args[0]], fill=1, width=self.args[1])
            m = np.array(im) > 0
            ys, xs = np.nonzero(m)
            if len(xs):
                cx, cy = (xs.min() + xs.max() + 1) / 2, (ys.min() + ys.max() + 1) / 2
                rx, ry = max(1, (xs.max() - xs.min() + 1) / 2), max(1, (ys.max() - ys.min() + 1) / 2)
            else: cx = cy = rx = ry = 1
            u, v = (X - cx) / rx * .8, (Y - cy) / ry * .8; r2 = np.clip(u * u + v * v, 0, 1)
            n = np.stack([u, v, np.sqrt(1 - r2)], -1)
        if self.clip:
            x0, y0, x1, y1 = self.clip; c = np.zeros_like(m); c[max(0, y0):y1 + 1, max(0, x0):x1 + 1] = True; m &= c
        return m, n


def tones(mat):
    if isinstance(mat[0], (int, np.integer)): return (mat, mat, mat)
    if len(mat) == 2: return (mat[0], mat[0], mat[1])
    return mat


def render(parts, W, H, outline=OL, edge8=False):
    """返 (rgba, partid map)。"""
    img = canvas(W, H); pid = np.full((H, W), -1, int); zb = np.full((H, W), -1e9)
    order = sorted(range(len(parts)), key=lambda i: parts[i].z)
    glow = np.zeros((H, W), bool)
    for i in order:
        p = parts[i]; m, n = p.mask_normal(W, H); m &= p.z >= zb
        hi, mid, sh = tones(p.mat)
        if p.flat: col = np.broadcast_to(np.array(mid, np.uint8), (H, W, 3))
        else:
            I = (n @ LIGHT)
            col = np.where((I > p.th[0])[..., None], np.array(hi, np.uint8), np.where((I > p.th[1])[..., None], np.array(mid, np.uint8), np.array(sh, np.uint8)))
        img[m, :3] = col[m]; img[m, 3] = 255; pid[m] = i; zb[m] = p.z; glow[m] = p.glow
    # 部件內線：後面部件喺前面部件旁邊嗰格 → 後面部件嘅暗色
    out = img.copy()
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        nb = np.full_like(pid, -1); ys = slice(max(0, dy), H + min(0, dy)); yd = slice(max(0, -dy), H + min(0, -dy))
        xs = slice(max(0, dx), W + min(0, dx)); xd = slice(max(0, -dx), W + min(0, -dx))
        nb[yd, xd] = pid[ys, xs]
        for i in range(len(parts)):
            if not parts[i].line: continue
            sel = (nb == i)
            if not sel.any(): continue
            me = pid
            behind = sel & (me >= 0) & (me != i)
            if not behind.any(): continue
            for j in np.unique(me[behind]):
                if parts[j].z >= parts[i].z or tones(parts[j].mat)[2] == tones(parts[i].mat)[2]: continue
                mm = behind & (me == j); out[mm, :3] = tones(parts[j].mat)[2]
    img = out
    if outline is not None: img = add_outline(img, outline, edge8)
    return img, pid


def add_outline(img, outline=OL, edge8=False):
    solid = img[..., 3] == 255; p = np.pad(solid, 1)
    nb = p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
    if edge8: nb |= p[:-2, :-2] | p[:-2, 2:] | p[2:, :-2] | p[2:, 2:]
    ring = nb & ~solid; o = img.copy(); o[ring] = (*outline, 255); return o


def px(img, x, y, c):
    x, y = int(x), int(y)
    if 0 <= x < img.shape[1] and 0 <= y < img.shape[0]: img[y, x] = (*c[:3], 255)


def pxs(img, pts, c):
    for x, y in pts: px(img, x, y, c)


def eye(img, x, y, h=3, w=2, mode="open", c=EYE):
    """x,y＝眼左上。open：深色塊＋左上白高光；closed：一條線；happy：^ 形；glasses 另外畫"""
    if mode == "open":
        for j in range(h):
            for i in range(w): px(img, x + i, y + j, c)
        px(img, x, y, WHITE)
    elif mode == "closed":
        for i in range(w + 1): px(img, x - (1 if w > 1 else 0) + i, y + h - 1, c)
    elif mode == "happy":   # ^
        px(img, x - 1 + 0, y + h - 1, c); px(img, x, y + h - 2, c); px(img, x + w - 1, y + h - 2, c); px(img, x + w, y + h - 1, c)
    elif mode == "wide":
        for j in range(h + 1):
            for i in range(w): px(img, x + i, y - 1 + j, c)
        px(img, x, y - 1, WHITE); px(img, x + 1, y, WHITE)


def blush(img, x, y, w=2): [px(img, x + i, y, BLUSH) for i in range(w)]


def ncolors(img):
    m = img[..., 3] == 255
    return len(np.unique(img[m][:, :3], axis=0)) if m.any() else 0


def colors_of(frames):
    allc = np.concatenate([f[f[..., 3] == 255][:, :3] for f in frames if (f[..., 3] == 255).any()])
    return np.unique(allc, axis=0)


def limit(frames, n=12):
    """整條 strip 共用 ≤n 色（MAXCOVERAGE 量化，只改實色）"""
    cols = colors_of(frames)
    if len(cols) <= n: return frames
    strip = np.concatenate(frames, 1)
    im = Image.fromarray(strip[..., :3].copy()).quantize(colors=n, method=Image.Quantize.MAXCOVERAGE).convert("RGB")
    q = np.array(im); o = strip.copy(); m = strip[..., 3] == 255; o[m, :3] = q[m]
    W = frames[0].shape[1]; return [o[:, i * W:(i + 1) * W] for i in range(len(frames))]


def strip(frames): return np.concatenate(frames, 1)


def save(a, path): Image.fromarray(a).save(path, optimize=True)


def paste(dst, src, x, y):
    h, w = src.shape[:2]; x, y = int(x), int(y)
    X0, Y0 = max(0, x), max(0, y); X1, Y1 = min(dst.shape[1], x + w), min(dst.shape[0], y + h)
    if X1 <= X0 or Y1 <= Y0: return
    s = src[Y0 - y:Y1 - y, X0 - x:X1 - x]; m = s[..., 3] == 255
    d = dst[Y0:Y1, X0:X1]; d[m] = s[m]


def flipx(a): return a[:, ::-1].copy()


def scale_nn(a, k):
    return np.repeat(np.repeat(a, k, 0), k, 1)
