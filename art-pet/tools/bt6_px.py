#!/usr/bin/env python3
"""6c／6d 共用像素小工具（遊美 2026-11-02）。純 numpy／Pillow，冇 AI 圖；alpha 只得 0／255。
Spr：任意大細嘅「材質字母畫布」（同 ui_hd2d_v2_icons.Ic 一樣寫法，但唔限 16×16、材質表可以自己帶），
render() 統一：左上受光三階（hi／base／shade）＋1px #24172C 外描（4 鄰）。"""
import numpy as np
from PIL import Image, ImageDraw

def hx(h):
    h = h.lstrip('#'); return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)
LINE = hx('#24172C')
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0 + 1 / 32
SPECIAL_DEF = {'k': '#2A1A30', 'w': '#FFFFFF', '*': '#FF8FB0', 'K': '#24172C'}

class Spr:
    def __init__(s, W, H):
        s.W, s.H = W, H; s.m = np.full((H, W), '.', dtype='<U1'); s.yy, s.xx = np.mgrid[0:H, 0:W]
    def set(s, mask, mat): s.m[mask] = mat; return s
    def C(s, cx, cy, r, mat): return s.set((s.xx + .5 - cx) ** 2 + (s.yy + .5 - cy) ** 2 <= r * r, mat)
    def E(s, cx, cy, rx, ry, mat): return s.set(((s.xx + .5 - cx) / rx) ** 2 + ((s.yy + .5 - cy) / ry) ** 2 <= 1, mat)
    def R(s, x0, y0, x1, y1, mat, cut=0):
        m = (s.xx >= x0) & (s.xx <= x1) & (s.yy >= y0) & (s.yy <= y1)
        if cut:
            for (cx, cy) in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
                m &= ~((abs(s.xx - cx) + abs(s.yy - cy)) < cut)
        return s.set(m, mat)
    def PG(s, pts, mat):
        im = Image.new('L', (s.W, s.H), 0); ImageDraw.Draw(im).polygon([(x, y) for x, y in pts], fill=255); return s.set(np.array(im) > 0, mat)
    def L(s, pts, mat, w=1):
        im = Image.new('L', (s.W, s.H), 0); ImageDraw.Draw(im).line([(x, y) for x, y in pts], fill=255, width=w); return s.set(np.array(im) > 0, mat)
    def P(s, pts, mat):
        for x, y in pts:
            x, y = int(x), int(y)
            if 0 <= x < s.W and 0 <= y < s.H: s.m[y, x] = mat
        return s
    def A(s, x, y, rows):
        for j, r in enumerate(rows):
            for i, ch in enumerate(r):
                if ch not in ' _' and 0 <= y + j < s.H and 0 <= x + i < s.W: s.m[y + j, x + i] = '.' if ch == '-' else ch
        return s
    def face(s, cx, cy, gap=3, mouth='dot', blush=True, eye='dot'):
        lx, rx = cx - (gap + 1) // 2, cx + gap // 2
        if eye == 'dot': s.P([(lx, cy), (rx, cy)], 'k')
        elif eye == 'closed': s.P([(lx - 1, cy), (lx, cy + 0), (rx, cy), (rx + 1, cy)], 'k')
        elif eye == 'happy': s.P([(lx - 1, cy), (lx, cy - 1), (lx + 1, cy), (rx - 1, cy), (rx, cy - 1), (rx + 1, cy)], 'k')
        if blush: s.P([(lx - 1, cy + 1), (rx + 1, cy + 1)], '*')
        mx = (lx + rx) // 2
        if mouth == 'dot': s.P([(mx, cy + 1)], 'k')
        elif mouth == 'open': s.P([(mx, cy + 1), (mx, cy + 2)], 'k')
        return s

def render(sp, mats, special=None, outline=True, line=LINE):
    """mats：{小寫字母: (hi, base, shade)}；大寫＝強制 shade。special：{字元: hex}（唔受光）"""
    SP = dict(SPECIAL_DEF); SP.update(special or {})
    m = sp.m; H, W = m.shape; a = np.zeros((H, W, 4), np.uint8); solid = m != '.'
    flat = list(SP.keys())
    for ch in np.unique(m):
        if ch == '.': continue
        msk = m == ch
        if ch in SP: a[msk] = hx(SP[ch]); continue
        hi, base, sh = (hx(c) for c in mats[ch.lower()])
        if ch.isupper(): a[msk] = sh; continue
        a[msk] = base
        dn = np.zeros_like(msk); dn[:-1] = ~msk[1:] & ~np.isin(m[1:], flat); dn[-1] = True
        rt = np.zeros_like(msk); rt[:, :-1] = ~msk[:, 1:] & ~np.isin(m[:, 1:], flat); rt[:, -1] = True
        upo = np.zeros_like(msk); upo[1:] = ~solid[:-1]; upo[0] = True
        lfo = np.zeros_like(msk); lfo[:, 1:] = ~solid[:, :-1]; lfo[:, 0] = True
        a[msk & (dn | rt)] = sh
        a[msk & (upo | lfo) & ~(dn | rt)] = hi
    if outline:
        O = np.zeros_like(solid)
        O[1:] |= solid[:-1]; O[:-1] |= solid[1:]; O[:, 1:] |= solid[:, :-1]; O[:, :-1] |= solid[:, 1:]; O &= ~solid
        a[O] = line
    return a

def over(dst, src, x=0, y=0):
    """src RGBA（alpha 0／255）貼落 dst（就地），可以出界（自動裁）"""
    H, W = dst.shape[:2]; h, w = src.shape[:2]
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0: return dst
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]; m = s[..., 3] == 255
    d = dst[y0:y1, x0:x1]; d[m] = s[m]; return dst

def ncol(a):
    m = a[..., 3] == 255; return len({tuple(c) for c in a[m][:, :3]})
def cols(a):
    m = a[..., 3] == 255; return {tuple(c) for c in a[m][:, :3]}
def up(a, k=3): return np.repeat(np.repeat(a, k, 0), k, 1)
def save(a, path, k=1):
    if k != 1: a = up(a, k)
    Image.fromarray(np.ascontiguousarray(a), 'RGBA').save(path, optimize=True)
def rgba(p): return np.array(Image.open(p).convert('RGBA'))
