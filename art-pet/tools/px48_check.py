"""px48 crack 檢查：自動揾 (1) 單像素異色點 (2) 身體內透明洞 (3) 外框斷口（邊緣像素唔係深色） (4) 細碎獨立件"""
import numpy as np
from scipy import ndimage as ndi
CROSS = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool)
def lum(c): c = np.asarray(c, float); return c[..., 0] * .299 + c[..., 1] * .587 + c[..., 2] * .114
def check(img, meta):
    a = img[..., 3] == 255; L = lum(img[..., :3]); S = a.shape[0]
    lab, n = ndi.label(a, np.ones((3, 3))); sz = ndi.sum(a, lab, range(1, n + 1)); mainid = int(np.argmax(sz)) + 1
    main = lab == mainid
    # 特徵區（眼、燈泡）唔計
    feat = np.zeros_like(a)
    for e in meta.get("eyes", []): feat[max(0, e["y"] - 1):e["y"] + 6, max(0, e["x"] - 1):e["x"] + 6] = True
    if meta.get("featBox"): fb = meta["featBox"]; feat[fb[1]:fb[3], fb[0]:fb[2]] = True
    bx, by = meta["bulbXY"]; feat[max(0, by - 4):by + 7, max(0, bx - 4):bx + 5] = True
    issues = {"speck": [], "hole": [], "gap": [], "frag": [], "noise": [], "soft": [tuple(p) for p in np.argwhere((img[..., 3] > 0) & (img[..., 3] < 255))]}
    holes = ndi.binary_fill_holes(a) & ~a
    hl, hn = ndi.label(holes)
    for i in range(1, hn + 1):
        c = hl == i
        if c.sum() <= 6 and ndi.binary_dilation(c)[main].any() and not (ndi.binary_dilation(c) & a & ~main).any(): issues["hole"] += [tuple(p) for p in np.argwhere(c)]
    rgb = img[..., :3].astype(int)
    for vx, vy in meta.get("veinPx", []): feat[vy, vx] = True
    for y, x in zip(*np.nonzero(main & ~feat)):
        if not (0 < y < S - 1 and 0 < x < S - 1): continue
        nb = [(y + dy, x + dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy or dx)]
        if not all(a[p] for p in nb): continue
        d = [np.abs(rgb[y, x] - rgb[p]).sum() for p in nb]
        if min(d) > 90: issues["speck"].append((y, x))
        elif min(d) > 45: issues["noise"].append((y, x))   # 冇任何相近色鄰居（JPEG 碎色）
    edge = a & ~ndi.binary_erosion(a, structure=CROSS, border_value=0)
    ol = np.array([int(meta["outline"][i:i + 2], 16) for i in (1, 3, 5)])
    for y, x in zip(*np.nonzero(edge & main & ~feat)):
        inn = [(y + dy, x + dx) for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= y + dy < S and 0 <= x + dx < S and a[y + dy, x + dx] and not edge[y + dy, x + dx]]
        ref = max([L[p] for p in inn]) if inn else L[y, x] + 99
        if L[y, x] > lum(ol) + 45 and L[y, x] > ref - 20: issues["gap"].append((y, x))
    for i in range(1, n + 1):
        if i == mainid: continue
        c = lab == i
        if 1 < c.sum() < 6 and not feat[c].any():
            pass   # 粒子 stamp（1/4/5/8px）屬設計
        if 6 <= c.sum() < 12 and c.sum() != 9 and not feat[c].any(): issues["frag"] += [tuple(p) for p in np.argwhere(c)]
    return issues
