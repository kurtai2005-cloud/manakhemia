# 《微光小圃》5c 遺傳花紋 8 款 — 每形態 mask（base 座標，避開描邊／面／燈泡），2 色調（255＝hi、128＝lo），引擎用上一代色染。
import math, os
import numpy as np
from PIL import Image
import long_5abc_lib as LB

PATTERNS = [("wave", "波紋"), ("bubble", "泡泡"), ("spark", "火花"), ("spot", "斑點"), ("flame", "火焰"), ("star", "星星"), ("diamond", "菱格"), ("crescent", "月牙")]
PID = {p: i + 1 for i, (p, _) in enumerate(PATTERNS)}
BY_SERIES = {"A": "wave", "B": "bubble", "C": "spark", "D": "spot", "E": "flame", "F": "star", "G": "diamond", "H": "crescent"}
BY_ROUTE = {"tide": "wave", "soft": "bubble", "ember": "spark", "dust": "spark", "shroom": "spot", "radiant": "star", "lumi": "star", "crystal": "diamond", "moon": "crescent"}
ROUTES = ["tide", "moon", "shroom", "crystal", "ember", "radiant", "soft", "dust", "lumi"]

def series_of(k):
    if k in LB.KID34:
        if k.startswith("S4"): return k[2]
        if k[0] in "ABCDEFGH": return k[0]
        return None
    for r_ in ROUTES:
        if k.endswith("_" + r_) or k == r_: return r_
    return None
def pattern_for_parent(k):
    s = series_of(k)
    return BY_SERIES.get(s) or BY_ROUTE.get(s) or "spot"

def _hx(c): return '#%02x%02x%02x' % tuple(int(v) for v in c[:3])
def tint_for_parent(k):
    """上一代主色 → (hi, lo)。主色＝base 最多嘅非描邊色（夠飽和優先）"""
    r = LB.rig(k); a = r.base; m = a[..., 3] > 0
    px = a[m][:, :3].astype(int); ol = np.array(r.outline[:3])
    px = px[np.abs(px - ol).sum(1) > 40]; lum = px @ [0.3, 0.59, 0.11]; px = px[(lum > 70) & (lum < 245)]
    cols, cnt = np.unique(px, axis=0, return_counts=True)
    sat = cols.max(1) - cols.min(1); score = cnt * (0.4 + sat / 255)
    c = cols[np.argmax(score)].astype(float)
    if (c.max() - c.min()) < 50:          # 主色太灰（例如 E3 炭色）→ 用最多嘅鮮色配色（火焰橙等）
        ok = (sat >= 80) & (cnt >= 6)
        if ok.any(): c = cols[np.argmax(np.where(ok, cnt, -1))].astype(float)
    hi = c + (255 - c) * 0.45; lo = c * 0.72
    lum = lambda v: float(v @ [0.3, 0.59, 0.11])
    if lum(lo) < 80: lo = lo + (np.array([255, 255, 255]) - lo) * ((80 - lum(lo)) / max(1, 255 - lum(lo)))
    if lum(hi) < 165: hi = hi + (np.array([255, 255, 255]) - hi) * ((165 - lum(hi)) / max(1, 255 - lum(hi)))
    # 確保 hi 有返啲飽和（唔好變灰白）
    return _hx(hi), _hx(lo), _hx(c)

def _dom(a, ol):
    m = a[..., 3] > 0; px = a[m][:, :3].astype(int)
    px = px[np.abs(px - ol).sum(1) > 60]; cols, cnt = np.unique(px, axis=0, return_counts=True)
    return cols[np.argmax(cnt)].astype(int)
def interior(k, tight=False):
    """可畫花紋嘅 base pixel：不透明、身體主色系（唔畫落帽／葉／鰭等配件）、非描邊、內縮 1px、避開面（眼口腮）、燈泡 protect"""
    r = LB.rig(k); a = r.base; H, W = a.shape[:2]; m = a[..., 3] > 0
    ol = np.array(r.outline[:3]); rgb = a[..., :3].astype(int)
    dark = np.abs(rgb - ol).sum(2) < 70
    dom = np.array(r.eyes[0]['skin'][:3]) if r.eyes and 'skin' in r.eyes[0] else _dom(a, ol); body = np.abs(rgb - dom).sum(2) < 110
    er = m.copy()
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)): er &= np.roll(np.roll(m, dy, 0), dx, 1)
    er &= ~dark & body
    ex0 = int(min(r.anchors["eyeL"][0], r.anchors["eyeR"][0]) - 4); ex1 = int(max(r.anchors["eyeL"][0], r.anchors["eyeR"][0]) + 5)
    ey0 = int(min(r.anchors["eyeL"][1], r.anchors["eyeR"][1]) - 3); ey1 = int(r.anchors["mouth"][1] + 3)
    # 只要同個面相連嘅身體色塊（帽／火焰／鰭等配件唔畫）
    from scipy import ndimage
    lab, n = ndimage.label(m & body & ~dark)
    ring = np.zeros_like(m); ring[max(0, ey0 - 2):ey1 + 3, max(0, ex0 - 2):ex1 + 3] = True
    keep = set(np.unique(lab[ring & (lab > 0)]))
    if keep: er &= np.isin(lab, list(keep))
    if not tight: er[max(0, ey0):ey1 + 1, max(0, ex0):ex1 + 1] = False
    else:                                # 細隻形態：只避開眼（±1）、口、腮
        for e in r.eyes:
            x0_, y0_, x1_, y1_ = e["box"]; er[max(0, y0_ - 2):y1_ + 3, max(0, x0_ - 2):x1_ + 3] = False
        mx, my = r.anchors["mouth"]; er[int(my) - 1:int(my) + 3, int(mx) - 3:int(mx) + 4] = False
    for (x, y) in r.protect:
        er[max(0, y - 1):y + 2, max(0, x - 1):x + 2] = False
    # 細碎孤立點唔要（4 鄰少過 2）
    nb = sum(np.roll(np.roll(er, dy, 0), dx, 1).astype(int) for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)))
    er &= nb >= 2
    return er

def motif(name, H, W, x0, y0, x1, y1):
    """回傳 HxW uint8：255 hi、128 lo（喺 bbox 入面鋪；1 art px 都睇得清：每個圖案 ≥3px）"""
    o = np.zeros((H, W), np.uint8); bh = y1 - y0 + 1
    def put(x, y, v):
        if 0 <= x < W and 0 <= y < H: o[y, x] = max(o[y, x], v)
    def grid(sp, fn, jit=None):
        for j, yy in enumerate(range(y0 + 2, y1 + 1, sp)):
            for xx in range(x0 + 2 + ((sp // 2) if j % 2 else 0), x1 + 1, sp): fn(xx, yy)
    if name == "wave":
        for j, yy in enumerate(range(y0 + 2, y1 + 1, 5)):
            for x in range(x0, x1 + 1):
                y = yy + int(round(1.4 * math.sin((x - x0) * math.pi / 3 + j * 1.5)))
                put(x, y, 255); put(x, y + 1, 128)
    elif name == "bubble":
        def f(x, y):
            for dx, dy in ((0, -2), (-1, -1), (-2, 0), (1, -1)): put(x + dx, y + dy, 255)
            for dx, dy in ((2, 0), (1, 1), (0, 2), (-1, 1)): put(x + dx, y + dy, 128)
            put(x - 1, y - 1, 255)
        grid(7, f)
    elif name == "spark":
        def f(x, y):
            put(x, y, 255)
            for d in (1, 2): put(x, y - d, 255); put(x - d, y, 255); put(x + d, y, 128); put(x, y + d, 128)
        grid(7, f)
    elif name == "spot":
        def f(x, y):
            for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1), (0, -1), (-1, 0), (1, -1), (-1, 1)): put(x + dx, y + dy, 255)
            for dx, dy in ((2, 0), (2, 1), (0, 2), (1, 2)): put(x + dx, y + dy, 128)
        grid(7, f)
    elif name == "flame":                 # 細火苗（3 闊 4 高）：尖＝hi、底＝lo
        def f(x, y):
            for dx, dy in ((0, -2), (-1, -1), (0, -1), (-1, 0), (0, 0), (1, 0)): put(x + dx, y + dy, 255)
            for dx, dy in ((-1, 1), (0, 1), (1, 1)): put(x + dx, y + dy, 128)
        grid(7, f)
    elif name == "star":
        def f(x, y):
            for dx, dy in ((0, 0), (0, -1), (0, -2), (-1, 0), (1, 0), (-2, 0), (2, 0)): put(x + dx, y + dy, 255)
            put(x, y + 1, 255); put(x - 1, y + 2, 128); put(x + 1, y + 2, 128)
        grid(8, f)
    elif name == "diamond":
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                u, v = (x - x0 + y - y0) % 7, (x - x0 - (y - y0)) % 7
                if u == 0: put(x, y, 255)
                elif v == 0: put(x, y, 128)
    elif name == "crescent":
        def f(x, y):
            for dx, dy in ((0, -2), (-1, -2), (-2, -1), (-2, 0), (-2, 1), (-1, 2), (0, 2)): put(x + dx, y + dy, 255)
            put(-1 + x, y - 1, 255); put(x - 1, y + 1, 128); put(x - 1, y, 128)
        grid(7, f)
    return o

def mask_base(k, name):
    """base 座標 mask（HxW uint8 0/128/255）"""
    it = interior(k)
    if it.sum() < 45: it = interior(k, tight=True)
    H, W = it.shape; ys, xs = np.nonzero(it)
    if not len(ys): return np.zeros((H, W), np.uint8)
    m = motif(name, H, W, xs.min(), ys.min(), xs.max(), ys.max()); m[~it] = 0
    return m

def mask_rgba(m):
    a = np.zeros(m.shape + (4,), np.uint8); a[..., 0] = a[..., 1] = a[..., 2] = m; a[..., 3] = (m > 0) * 255; return a

def colorize(overlay, hi, lo):
    """overlay RGBA（R＝255／128）→ 染色"""
    o = overlay.copy(); h = np.array(LB_hex(hi)); l = np.array(LB_hex(lo))
    sel = o[..., 3] > 0; v = o[..., 0]
    o[sel & (v > 190), :3] = h; o[sel & (v <= 190), :3] = l; return o
def LB_hex(s): s = s.lstrip('#'); return [int(s[i:i + 2], 16) for i in (0, 2, 4)]

def egg_mask(frame, name):
    """蛋：直接由每格蛋殼 alpha 推內部（蛋冇 rig 變形）"""
    a = frame; m = a[..., 3] > 0; H, W = m.shape
    lum = a[..., :3].astype(int).sum(2); dark = lum < 200
    er = m.copy()
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0), (2, 0), (0, 2), (0, -2)): er &= np.roll(np.roll(m, dy, 0), dx, 1)
    er &= ~dark
    ys, xs = np.nonzero(er)
    if not len(ys): return np.zeros((H, W), np.uint8)
    o = motif(name, H, W, xs.min(), ys.min(), xs.max(), ys.max()); o[~er] = 0; return o
