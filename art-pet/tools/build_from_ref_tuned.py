#!/usr/bin/env python3
"""build_from_ref_tuned — Kurt [pt92u]「張圖係我搵ai畫…可以100%跟足，fine tune下再加落game試feel」。
由 Kurt 參考圖（Kurt 自己用 AI 生成，擁有權已確認）重新切 → 正式 64px 遊戲素材：
每隻 KMeans 色盤（≤22 色）→ 加權眾數降採樣 → 1px 深色外框 → 清雜點 → 同階統一體量 →
細泡泡／火星／閃粉改用程序 stamp（唔會碎）→ 柔光用暖色 tint → 頭頂燈泡（可調位＋彎莖）→ 4 幀 idle（bob／眨眼）。
全部 numpy／Pillow，冇 AI 生圖。用法：python3 build_from_ref_tuned.py [all|check]"""
import os, sys, json, math
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_from_ref as R
B = R.B
def _size():
    for i, a in enumerate(sys.argv):
        if a == "--size": return int(sys.argv[i + 1])
    return int(os.environ.get("TUNED_SIZE", "64"))
S = _size(); K = S / 64.0; FOOT = S - 3          # 最底身體像素行 = S-3 → pivot (S/2, S-3) = (w/2, h-3)
def sc(v): return int(round(v * K))
OUT = os.path.join(R.OUT, "tuned" if S == 64 else f"tuned_{S}"); SPD = os.path.join(OUT, "sprites"); IDD = os.path.join(OUT, "idle")
for d in (SPD, IDD): os.makedirs(d, exist_ok=True)
ALPHAS = (0, 60, 110, 170, 255)
MASS = {k: v * K * K for k, v in {1: 1150, 2: 1330, 3: 1500}.items()}     # 每階目標主體面積（px），令同階體量相近
NCOL = 22
# 每隻微調：mass 乘數、色數、glow tint、燈泡 (dx, dy) 相對自動位／anchor、stamp 類型
CFG = {k: {} for k in [f"{a}{b}" for a in "ABCDEFGH" for b in (1, 2, 3)]}
for k in ("B1", "F1", "G1", "H3"): CFG[k]["bulb"] = "own"
CFG["B1"]["light_xy"] = (sc(45), sc(18)); CFG["H3"]["light_xy"] = (sc(33), sc(18))   # 自帶光源中心（燈籠／光環）
CFG["F1"]["glow"] = (255, 222, 110); CFG["G1"]["glow"] = (255, 222, 110)
CFG["B1"]["glow"] = (190, 236, 255)
CFG["H2"]["glow"] = (255, 236, 150); CFG["H3"]["glow"] = (255, 240, 170)
CFG["H3"]["ncol"] = 30; CFG["H3"]["mass"] = 1.08
for k in ("A1", "A2", "A3", "B1", "B2", "B3"): CFG[k]["stamp"] = "bubble"
for k in ("C1", "C2", "C3", "D1", "D2", "D3", "E1", "E2", "E3"): CFG[k]["stamp"] = "ember"
for k in ("F1", "F2", "F3", "G1", "G2", "G3", "H1", "H2", "H3"): CFG[k]["stamp"] = "star"
# 燈泡位（相對自動頭頂位嘅偏移；side＝莖彎向）
for k, v in {"D1": (-9, 0), "D2": (-7, 0), "E3": (-11, 0), "F3": (-13, 0), "G3": (-7, 0)}.items(): CFG[k]["bdx"], CFG[k]["bdy"] = sc(v[0]), sc(v[1])
CFG["C1"]["bulb_abs"] = (sc(17), sc(13), "L")   # 唔再坐喺火焰尖：移去左邊額頭，彎莖
CFG["B3"]["bulb_abs"] = (sc(35), sc(7), "C")    # 移去中間鯨角頂上，離開兩邊珊瑚角
CFG["F1"]["star"] = True; CFG["G1"]["star"] = True   # 星星天線改程序畫（原本縮細後變一嚿）

def lum(c): c = np.asarray(c, float); return c[..., 0] * .299 + c[..., 1] * .587 + c[..., 2] * .114
def palette_of(col, body, n):
    pts = col[body].astype(np.uint8)
    q = Image.fromarray(pts.reshape(1, -1, 3)).quantize(colors=n, method=Image.Quantize.MEDIANCUT, kmeans=3)
    pal = np.array(q.getpalette()[:n * 3]).reshape(-1, 3)[:len(np.unique(np.array(q)))] if False else np.array(q.getpalette()[:n * 3]).reshape(-1, 3)
    idx = np.array(q).reshape(-1); used = np.unique(idx); remap = -np.ones(len(pal), int); remap[used] = np.arange(len(used))
    full = -np.ones(body.shape, int); full[body] = remap[idx]; return pal[used].astype(float), full
def nearest(pal, c):
    return int(np.argmin(((pal - np.asarray(c, float)) ** 2).sum(1)))

def load(key):
    z = np.load(f"/tmp/cut_{key}.npz"); return z["col"].astype(float), z["A"].astype(int)
def ensure_cache():
    if all(os.path.exists(f"/tmp/cut_{k}.npz") for k in CFG): return
    src = np.array(Image.open(R.REF).convert("RGB"))
    for k in CFG:
        c, A, _ = R.cutout(k, src); np.savez_compressed(f"/tmp/cut_{k}.npz", col=c.astype(np.float32), A=A.astype(np.uint8))

def build_one(key):
    cf = CFG[key]; st = int(key[1]); col, A = load(key); H, W = A.shape
    body = A == 255; lab, n = ndi.label(body, np.ones((3, 3))); sizes = ndi.sum(body, lab, range(1, n + 1))
    big = sizes.max(); main_ids = [i + 1 for i, s in enumerate(sizes) if s >= max(0.04 * big, 500)]
    sat_ids = [i + 1 for i, s in enumerate(sizes) if (i + 1) not in main_ids and s >= 10]
    main = np.isin(lab, main_ids)
    # 柔光：離開主體嘅獨立柔光點 = 閃粉
    soft = (A > 0) & ~body
    # ── 比例：同階同體量
    s = math.sqrt(MASS[st] * cf.get("mass", 1.0) / main.sum())
    ys, xs = np.nonzero(main | np.isin(lab, sat_ids)); top_room = sc(3) if cf.get("bulb") == "own" else sc(10)
    s = min(s, (S - 6.0) / (xs.max() - xs.min() + 1), (FOOT + 1 - top_room) / (ys.max() - ys.min() + 1))
    ym, xm = np.nonzero(main); cx = (xm.min() + xm.max() + 1) / 2; by = ym.max() + 1
    f = 1 / s
    def src_box(u, v):
        x0 = cx + (u - S / 2) * f; y0 = by + (v - FOOT - 1) * f
        return int(round(x0)), int(round(y0)), int(round(x0 + f)), int(round(y0 + f))
    pal, pidx = palette_of(col, body, cf.get("ncol", NCOL)); pl = lum(pal)
    # 外框色：邊緣環（全解析度）最常見嘅深色
    ring = body & ~ndi.binary_erosion(body, iterations=4)
    ri = pidx[ring]; dark = [i for i in range(len(pal)) if pl[i] < 85]
    if dark:
        cnt = np.bincount(ri, minlength=len(pal)); oi = max(dark, key=lambda i: cnt[i])
    else: oi = int(np.argmin(pl))
    outline = pal[oi]
    idx = -np.ones((S, S), int); cov = np.zeros((S, S)); gl = np.zeros((S, S)); glc = np.zeros((S, S, 3)); satm = np.zeros((S, S), int)
    w_dark = (pl < 70) * 0.35 + 1.0; w_bright = (pl > 215) * 0.9
    for v in range(S):
        for u in range(S):
            xa, ya, xb, yb = src_box(u, v)
            xa, ya = max(0, xa), max(0, ya); xb, yb = min(W, xb), min(H, yb)
            if xb <= xa or yb <= ya: continue
            bb = body[ya:yb, xa:xb]; tot = bb.size; c = bb.mean(); cov[v, u] = c
            if c >= 0.45:
                ii = pidx[ya:yb, xa:xb][bb]; cnt = np.bincount(ii, minlength=len(pal)).astype(float)
                score = cnt * (w_dark + w_bright); idx[v, u] = int(np.argmax(score))
                ls = lab[ya:yb, xa:xb][bb]; satm[v, u] = np.bincount(ls).argmax()
            else:
                aa = A[ya:yb, xa:xb]; sm = (aa > 0) & (aa < 255)
                if sm.mean() > 0.25 or (aa > 0).mean() > 0.3:
                    gl[v, u] = aa[aa > 0].mean() / 255 * min(1, (aa > 0).mean() / 0.5)
                    glc[v, u] = col[ya:yb, xa:xb][aa > 0].mean(0)
    # 細衛星（泡泡、火星、閃粉）：縮細後 <7px 嘅改用 stamp
    stamps = []
    for i in sat_ids:
        m = satm == i; comp = lab == i
        cy_, cx_ = ndi.center_of_mass(comp); d = math.sqrt(comp.sum()) * s
        u = (cx_ - cx) * s + S / 2; v = (cy_ - by) * s + FOOT + 1
        if m.sum() < (7 if (S == 64 or cf.get("stamp") != "bubble") else 16) * K * K and (u - S / 2) ** 2 < (40 * K) ** 2:
            idx[m] = -1; stamps.append((u, v, d, col[comp].mean(0)))
    # 獨立柔光閃粉（遠離主體）
    far = soft & ~ndi.binary_dilation(body, iterations=6)
    flab, fn = ndi.label(far, np.ones((3, 3)))
    for i in range(1, fn + 1):
        comp = flab == i
        if comp.sum() < 25: continue
        cy_, cx_ = ndi.center_of_mass(comp); u = (cx_ - cx) * s + S / 2; v = (cy_ - by) * s + FOOT + 1
        bright = col[comp][A[comp] >= 110] if (A[comp] >= 110).any() else col[comp]
        stamps.append((u, v, math.sqrt(comp.sum()) * s * 0.6, bright.mean(0), "soft"))
    bodyo = idx >= 0
    # 補 1px 洞、刪孤立點
    nb4 = sum(np.roll(np.roll(bodyo, dy, 0), dx, 1) for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)))
    for y, x in zip(*np.nonzero(bodyo & (nb4 == 0))): idx[y, x] = -1
    for y, x in zip(*np.nonzero(~bodyo & (nb4 == 4))):
        idx[y, x] = idx[y - 1, x]
    bodyo = idx >= 0
    # 清雜點：內部像素色喺 8 鄰都冇、又唔係高光 → 用鄰居眾數
    for _ in range(2):
        new = idx.copy()
        for y in range(1, S - 1):
            for x in range(1, S - 1):
                if idx[y, x] < 0: continue
                nb = idx[y - 1:y + 2, x - 1:x + 2].ravel(); nb = np.delete(nb, 4); nbv = nb[nb >= 0]
                if len(nbv) < 8 or (nbv == idx[y, x]).any(): continue
                if pl[idx[y, x]] > pl[nbv].max() + 45: continue       # 眼高光
                if pl[idx[y, x]] < pl[nbv].min() - 45: continue       # 瞳孔／細線
                vals, cnt = np.unique(nbv, return_counts=True); new[y, x] = vals[np.argmax(cnt)]
        idx = new
    if S != 64:   # 80／96 加一轮 JPEG 雜色清理：只得 ≤1 個同色鄰居、又同鄰居眾數色差 <40 嘅低對比雜點 → 眾數
        for _ in range(2):
            new = idx.copy(); nch = 0
            for y in range(1, S - 1):
                for x in range(1, S - 1):
                    if idx[y, x] < 0: continue
                    nb = np.delete(idx[y - 1:y + 2, x - 1:x + 2].ravel(), 4); nbv = nb[nb >= 0]
                    if len(nbv) < 8 or (nbv == idx[y, x]).sum() > 1: continue
                    vals, cnt = np.unique(nbv, return_counts=True); m = vals[np.argmax(cnt)]
                    if cnt.max() < 3 or np.abs(pal[m] - pal[idx[y, x]]).sum() >= 40 * 1.6: continue
                    new[y, x] = m; nch += 1
            idx = new
        NOISE[key] = NOISE.get(key, 0) + nch
    # 1px 深色外框（邊緣環，包括內洞邊）；已經夠深嘅保留原色
    edge = bodyo & ~ndi.binary_erosion(bodyo, structure=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]]), border_value=0)
    out = np.zeros((S, S, 4), np.uint8)
    for y, x in zip(*np.nonzero(bodyo)):
        c = pal[idx[y, x]]
        if edge[y, x] and pl[idx[y, x]] > lum(outline) + 28:
            c = outline if pl[idx[y, x]] < 150 or cf.get("stamp") != "ember" else (outline * 0.55 + c * 0.45)
        out[y, x] = (*np.clip(c, 0, 255).astype(int), 255)
    # 柔光：量化到 60/110/170，色用 tint
    tint = cf.get("glow")
    if tint is None:
        bm = out[..., 3] == 255; cc = out[bm][:, :3].astype(float); L = lum(cc)
        sat = cc.max(1) - cc.min(1); sel = (L > 170) & (sat > 50)
        tint = tuple(cc[sel].mean(0).astype(int)) if sel.sum() >= 3 else tuple(cc[np.argsort(L)[-5:]].mean(0).astype(int))
    tint = np.array(tint, float)
    for y, x in zip(*np.nonzero((gl > 0.12) & (out[..., 3] == 0))):
        a = 170 if gl[y, x] >= .5 else 110 if gl[y, x] >= .3 else 60
        c = glc[y, x]; csat = c.max() - c.min()
        c = tint if csat < 60 else (c * 0.4 + tint * 0.6)
        out[y, x] = (*np.clip(c, 0, 255).astype(int), a)
    for stp in stamps: stamp(out, stp, cf.get("stamp"), outline, tint)
    # 燈泡
    binfo = None; LAST.clear()
    if cf.get("star"): binfo = draw_star_antenna(out, outline)
    elif cf.get("bulb") != "own":
        binfo = place_bulb(out, key, cf)
    # 收邊：成張圖左右移入 1..62（唔郁地線）；仍然超出嘅柔光／粒子刪走
    cols = np.nonzero(out[..., 3].any(0))[0]; sh = 0
    if cols.max() > S - 2: sh = -min(cols.max() - (S - 2), cols.min() - 1)
    elif cols.min() < 1: sh = min(1 - cols.min(), (S - 2) - cols.max())
    if sh: out = np.roll(out, sh, 1)
    if "xy" in LAST: bxy = [LAST["xy"][0] + sh, LAST["xy"][1]]
    elif cf.get("light_xy"): bxy = [cf["light_xy"][0], cf["light_xy"][1]]
    else:   # 自帶光源（燈籠／光環）：上半部最亮像素重心
        Lm = lum(out[..., :3].astype(float)); a_ = out[..., 3] > 0; rows = np.nonzero(a_.any(1))[0]
        lim = rows.min() + 0.45 * (rows.max() - rows.min()); yy, xx = np.nonzero(a_ & (Lm > 200) & (np.arange(S)[:, None] < lim))
        bxy = [int(xx.mean()), int(yy.mean())] if len(xx) else [32, int(rows.min())]
    out[:, 0] = out[:, -1] = 0; out[0] = out[-1] = 0
    meta = {"scale": round(s, 4), "colors": int(len(np.unique(out[out[..., 3] == 255][:, :3], axis=0))), "outline": "#%02x%02x%02x" % tuple(int(t) for t in outline),
            "glowTint": "#%02x%02x%02x" % tuple(int(t) for t in tint), "mass": int((out[..., 3] == 255).sum()), "stamps": len(stamps), "bulb": binfo or "own light", "bulbXY": [int(bxy[0]), int(bxy[1])]}
    return out, meta, outline

def put(out, x, y, c, a=255, over=False):
    x, y = int(x), int(y)
    if 0 < x < S - 1 and 0 < y < S - 1 and (over or out[y, x, 3] < a or (a == 255 and out[y, x, 3] < 255)):
        out[y, x] = (*np.clip(c, 0, 255).astype(int), a)
def stamp(out, stp, kind, outline, tint):
    u, v, d, c = stp[:4]; soft = len(stp) > 4; x, y = int(round(u)), int(round(v))
    if not (2 <= x < S - 2 and 2 <= y < S - 2): return
    if (out[max(0, y - 1):y + 2, max(0, x - 1):x + 2, 3] == 255).sum() > 2: return      # 唔蓋主體
    c = np.array(c, float)
    if kind == "bubble" and S != 64:   # 80／96：按大細畫圓泡
        rim = np.clip(c * 0.6 + np.array([150, 220, 255]) * 0.4, 0, 255); rb = max(1.7, min(d / 2, 3.2 * K))
        R_ = int(math.ceil(rb)) + 1
        for dy in range(-R_, R_ + 1):
            for dx in range(-R_, R_ + 1):
                dd = math.hypot(dx, dy)
                if rb - 0.9 < dd <= rb + 0.3: put(out, x + dx, y + dy, rim)
                elif dd <= rb - 0.9: put(out, x + dx, y + dy, rim, 60)
        hx = x - int(round(rb * 0.4)); put(out, hx, hx - x + y, (255, 255, 255))
        return
    if kind == "bubble":
        rim = np.clip(c * 0.6 + np.array([150, 220, 255]) * 0.4, 0, 255); ol = np.clip(rim * 0.55, 0, 255)
        if d >= 4.6:   # 5×5 泡
            for dx, dy in ((1, 0), (2, 0), (3, 0), (0, 1), (4, 1), (0, 2), (4, 2), (0, 3), (4, 3), (1, 4), (2, 4), (3, 4)): put(out, x - 2 + dx, y - 2 + dy, rim)
            put(out, x - 1, y - 1, (255, 255, 255)); put(out, x, y - 1, rim, 110); put(out, x - 1, y, rim, 110)
            for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1), (1, -1), (-1, 1)): put(out, x + dx, y + dy, rim, 60)
        else:          # 4×4 泡（最細都係圓圈，唔會變點）
            for dx, dy in ((1, 0), (2, 0), (0, 1), (3, 1), (0, 2), (3, 2), (1, 3), (2, 3)): put(out, x - 1 + dx, y - 1 + dy, rim)
            put(out, x, y, (255, 255, 255)); put(out, x + 1, y, rim, 110); put(out, x, y + 1, rim, 110); put(out, x + 1, y + 1, rim, 60)
    else:              # 火星／星粉：十字 + 亮芯 + 柔光角
        core = (255, 250, 220) if kind == "star" else (255, 236, 150)
        arm = np.clip((c * 0.4 + tint * 0.6) if kind == "star" else (c * 0.5 + np.array([255, 150, 50]) * 0.5), 0, 255)
        big = d >= 2.2 or soft
        put(out, x, y, core)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)): put(out, x + dx, y + dy, arm, 255 if big else 170)
        if big:
            for dx, dy in ((1, 1), (-1, -1), (1, -1), (-1, 1)): put(out, x + dx, y + dy, arm, 60)
            if kind == "star" and d >= 3.5:
                for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)): put(out, x + dx, y + dy, arm, 110)

BULB_OL = (92, 60, 40); BULB_C1 = (255, 214, 90); BULB_C2 = (255, 244, 190); STEM = (70, 52, 84)
LAST = {}
def draw_bulb(out, x, y, ax, ay):
    LAST["xy"] = (int(x), int(y))
    if S != 64: return draw_bulb_k(out, x, y, ax, ay)
    """燈泡 5×5（深啡框、黃芯、白高光）＋莖（由 anchor (ax,ay) 畫到泡底）＋柔光"""
    # 莖
    n = max(abs(ax - x), abs(ay - (y + 3)), 1)
    for t in range(n + 1):
        px = round(ax + (x - ax) * t / n); py = round(ay + (y + 3 - ay) * t / n); put(out, px, py, STEM, over=True)
    for dy in range(-4, 5):
        for dx in range(-4, 5):
            r2 = dx * dx + dy * dy
            if 6 < r2 <= 16 and out[y + dy, x + dx, 3] == 0: put(out, x + dx, y + dy, (255, 224, 112), 60)
            elif 3 < r2 <= 6 and out[y + dy, x + dx, 3] < 255: put(out, x + dx, y + dy, (255, 224, 112), 110)
    for dx, dy in ((-1, -2), (0, -2), (1, -2), (-2, -1), (2, -1), (-2, 0), (2, 0), (-2, 1), (2, 1), (-1, 2), (0, 2), (1, 2)): put(out, x + dx, y + dy, BULB_OL, over=True)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1): put(out, x + dx, y + dy, BULB_C1, over=True)
    put(out, x - 1, y - 1, BULB_C2, over=True); put(out, x, y - 1, BULB_C2, over=True); put(out, x - 1, y, (255, 255, 255), over=True); put(out, x + 1, y + 1, (232, 168, 60), over=True)
def draw_bulb_k(out, x, y, ax, ay):
    """80／96 用：按 K 放大嘅程序燈泡（圓半徑 2K、外框、黃芯、左上高光、右下陰影、柔光 2.5K）"""
    if S == 80: return draw_bulb_80(out, x, y, ax, ay)
    r = 2.0 * K; by0 = y + int(round(r)) + 1
    n = max(abs(ax - x), abs(ay - by0), 1)
    for t in range(n + 1):
        put(out, round(ax + (x - ax) * t / n), round(ay + (by0 - ay) * t / n), STEM, over=True)
    R = int(math.ceil(r + 2.5 * K)) + 1
    for dy in range(-R, R + 1):
        for dx in range(-R, R + 1):
            d = math.hypot(dx, dy); px, py = x + dx, y + dy
            if not (0 < px < S - 1 and 0 < py < S - 1): continue
            if d <= r - 0.6:
                c = BULB_C1
                if dx + dy <= -r * 0.7: c = BULB_C2
                if dx + dy >= r * 0.9: c = (232, 168, 60)
                put(out, px, py, c, over=True)
            elif d <= r + 0.4: put(out, px, py, BULB_OL, over=True)
            elif d <= r + 1.4 * K and out[py, px, 3] < 255: put(out, px, py, (255, 224, 112), 110)
            elif d <= r + 2.5 * K and out[py, px, 3] == 0: put(out, px, py, (255, 224, 112), 60)
    hx, hy = x - int(round(r * 0.45)), y - int(round(r * 0.45)); put(out, hx, hy, (255, 255, 255), over=True)
BULB80 = ["..OOO..",
          ".OYYYO.",
          "OYWYYYO",
          "OYYYYDO",
          "OYYYDDO",
          ".OYDDO.",
          "..OOO.."]
def draw_bulb_80(out, x, y, ax, ay):
    """80px 正式版：手畫 7×7 圓燈泡（之前 r=2.5 程序圓會變方）＋ 2 圈柔光"""
    by0 = y + 4; n = max(abs(ax - x), abs(ay - by0), 1)
    for t in range(n + 1):
        put(out, round(ax + (x - ax) * t / n), round(ay + (by0 - ay) * t / n), STEM, over=True)
    for dy in range(-6, 7):
        for dx in range(-6, 7):
            d = math.hypot(dx, dy); px, py = x + dx, y + dy
            if not (0 < px < S - 1 and 0 < py < S - 1) or out[py, px, 3] == 255: continue
            if 3.4 < d <= 4.6: put(out, px, py, (255, 224, 112), 110)
            elif 4.6 < d <= 6.0 and out[py, px, 3] == 0: put(out, px, py, (255, 224, 112), 60)
    C = {"O": BULB_OL, "Y": BULB_C1, "W": (255, 255, 255), "D": (232, 168, 60)}
    for j, row in enumerate(BULB80):
        for i, ch in enumerate(row):
            if ch in C: put(out, x - 3 + i, y - 3 + j, C[ch], over=True)
def star_mask(R):
    n = int(math.ceil(R)) * 2 + 3; ss = 4; im = Image.new("L", (n * ss, n * ss), 0); c = n * ss / 2
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5; rr = (R if i % 2 == 0 else R * 0.48) * ss
        pts.append((c + rr * math.cos(ang), c + rr * math.sin(ang)))
    ImageDraw.Draw(im).polygon(pts, fill=255)
    m = np.array(im.resize((n, n), Image.BOX)) >= 110; return m, n // 2
STAR = ["....O....", "...OYO...", "...OYO...", "OOOYYYOOO", "OYYWYYYYO", ".OYYYYYO.", "..OYDYO..", ".OYDODYO.", ".OOO.OOO."]
def draw_star_antenna(out, outline):
    """F1／G1：搵天線頸（頂部最窄一行），清走上面嗰嚿，畫 9×9 像素星＋暖黃柔光"""
    a = out[..., 3] == 255; rows = np.nonzero(a.any(1))[0]; top = rows.min()
    wid = [a[y].sum() for y in range(top, top + sc(22))]
    neck = top + sc(4) + int(np.argmin(wid[sc(4):sc(16)]))
    xs = np.nonzero(a[neck])[0]; nx = int(round(xs.mean()))
    blob = a[:neck]; ys_, xs_ = np.nonzero(blob); cx = int(round(xs_.mean())); 
    out[:neck] = 0
    cy = neck - sc(7); LAST["xy"] = (int(cx), int(cy))
    for t in range(neck - sc(3), neck + 1): put(out, nx, t, (70, 52, 84), over=True)
    if S != 64:   # 按 K 放大嘅程序星
        Y = (255, 222, 110); D = (232, 168, 60); W_ = (255, 252, 230); Rg = 6.0 * K
        for dy in range(-int(Rg), int(Rg) + 1):
            for dx in range(-int(Rg), int(Rg) + 1):
                r2 = dx * dx + dy * dy
                if r2 <= Rg * Rg and out[cy + dy, cx + dx, 3] == 0: put(out, cx + dx, cy + dy, (255, 226, 120), 110 if r2 <= 0.6 * Rg * Rg else 60)
        m, h = star_mask(3.6 * K); ol = ndi.binary_dilation(m, iterations=1) & ~m
        for (j, i) in zip(*np.nonzero(ol)): put(out, cx - h + i, cy - h + j, outline, over=True)
        for (j, i) in zip(*np.nonzero(m)):
            c = D if j > h + 0.5 * K else Y
            put(out, cx - h + i, cy - h + j, c, over=True)
        put(out, cx - 1, cy - 1, W_, over=True); put(out, cx, cy - 1, W_, over=True)
        return f"星星天線 ({cx},{cy})"
    Y = (255, 222, 110); D = (232, 168, 60); W_ = (255, 252, 230)
    for dy in range(-6, 7):
        for dx in range(-6, 7):
            r2 = dx * dx + dy * dy
            if r2 <= 36 and out[cy + dy, cx + dx, 3] == 0: put(out, cx + dx, cy + dy, (255, 226, 120), 110 if r2 <= 22 else 60)
    for j, row in enumerate(STAR):
        for i, ch in enumerate(row):
            c = {"O": outline, "Y": Y, "D": D, "W": W_}.get(ch)
            if c is not None: put(out, cx - 4 + i, cy - 4 + j, c, over=True)
    return f"星星天線 ({cx},{cy})"
def place_bulb(out, key, cf):
    a = out[..., 3] == 255; ys, xs = np.nonzero(a)
    if cf.get("bulb_abs"):
        x, y, side = cf["bulb_abs"]
        ax = x + {"L": 3, "R": -3, "C": 0}[side]
        col = np.nonzero(a[:, ax])[0]; ay = col.min() - 1 if len(col) else y + 6; draw_bulb(out, x, y, ax, ay); return f"({x},{y}) 彎莖→({ax},{ay})"
    if key == "B3":   # 搵頭頂空位：喺 x 18..46 搵 5 列都冇主體高過 yt-8 嘅位置
        best = None
        for x in range(20, 45):
            tops = [np.nonzero(a[:, xx])[0].min() if a[:, xx].any() else 99 for xx in range(x - 3, x + 4)]
            occ = a[:, x - 3:x + 4]; t = min(tops); score = t   # 越低（越大 y）越多空位
            if best is None or t > best[0]: best = (t, x)
        t, x = best; colt = np.nonzero(a[:, x])[0].min(); y = max(5, colt - 6)
        draw_bulb(out, x, y, x, colt - 1); return f"({x},{y}) 自動搵空位"
    bx = int(round((xs.min() + xs.max()) / 2)) + cf.get("bdx", 0)
    colt = np.nonzero(a[:, bx])[0]; yt = colt.min() if len(colt) else ys.min()
    y = int(max(sc(5), yt - sc(6) + cf.get("bdy", 0))); draw_bulb(out, bx, y, bx, yt - 1); return f"({bx},{y})"

# ── idle：4 幀（0 原、1 壓扁 1px、2 原、3 眨眼）
NOISE = {}
# 閉眼線色：glow＝發光眼（用眼最光色做細縫），其餘用外框深色
EYE_GLOW = {80: {"B2", "H3", "D1", "D2", "E3", "G3"}}
# 80px（正式版）手放眼位：(cx, cy) 每隻眼一個 hint；自動偵測唔到／偵測錯嘅全部用手放
EYES = {80: {"A1": [(33, 57), (51, 57)], "A3": [(44, 53), (65, 53)], "B2": [(33, 36), (51, 36)], "C1": [(33, 58), (53, 58)],
             "F1": [(32, 55), (50, 55)], "H3": [(37, 55), (55, 55)], "D1": [(35, 58), (53, 56)], "D2": [(37, 53), (56, 52)],
             "E3": [(37, 55), (57, 55)], "F3": [(41, 54)], "G3": [(37, 52), (58, 52)]}}
def eyes_from_hints(out, hints):
    a = out[..., 3] == 255; res = []
    for hx, hy in hints:
        R = int(round(4.5 * K)); y0, y1, x0, x1 = hy - R, hy + R + 1, hx - R, hx + R + 1
        yy, xx = np.mgrid[0:S, 0:S]; dd = np.hypot(yy - hy, xx - hx)
        ring = a & (dd >= R + 1) & (dd <= R + 3); skin = np.median(out[ring][:, :3].astype(float), 0)
        diff = np.abs(out[..., :3].astype(float) - skin).sum(2)
        cand = a & (dd <= R) & (diff > 70)
        lab, n = ndi.label(cand, np.ones((3, 3)))
        if n == 0: continue
        # 揀最近 hint 嘅 component（同埋貼住佢嘅其他 component，例如高光）
        best = min(range(1, n + 1), key=lambda i: dd[lab == i].min()); m = lab == best; core = m.copy()
        m = m | (ndi.binary_dilation(m, iterations=1) & cand)
        m = m | (ndi.binary_dilation(m, iterations=1) & a & (diff > 35) & (dd <= R + 1))   # 眼邊反鋸齒殘色一齊清
        cy, cx = ndi.center_of_mass(core); res.append((cy, cx, int(m.sum()), m, skin, core))
    return res or None
def find_eyes(out, relax=False):
    a = out[..., 3] == 255; L = lum(out[..., :3].astype(float))
    inner = ndi.binary_erosion(a, iterations=2)
    ys, xs = np.nonzero(a); y0, y1 = ys.min(), ys.max()
    bodyL = np.median(L[inner]) if inner.any() else 100
    dark = inner & (L < (min(70, bodyL - 25) if not relax else max(95, bodyL - 45)))
    lab, n = ndi.label(dark, np.ones((3, 3))); cands = []
    for i in range(1, n + 1):
        m = lab == i; sz = m.sum()
        if not (3 <= sz <= 30 * K * K): continue
        cy, cx = ndi.center_of_mass(m)
        if not (y0 + 0.2 * (y1 - y0) < cy < y0 + 0.85 * (y1 - y0)): continue
        hl = ndi.binary_dilation(m, iterations=1) & (L > (200 if not relax else 175)) & a
        if not hl.any(): continue
        cands.append((cy, cx, sz, m | hl))
    best = None
    for i in range(len(cands)):
        for j in range(i + 1, len(cands)):
            a1, a2 = cands[i], cands[j]; dy = abs(a1[0] - a2[0]); dx = abs(a1[1] - a2[1])
            if dy <= 3 and 5 * K <= dx <= 26 * K and max(a1[2], a2[2]) <= 2.5 * min(a1[2], a2[2]):
                sc = dy + abs(a1[2] - a2[2]) * 0.3 - (a1[2] + a2[2]) * 0.2
                if best is None or sc < best[0]: best = (sc, a1, a2)
    if best is None and not relax: return find_eyes(out, True)
    return None if best is None else (best[1], best[2])
def blink_hint(out, eyes, outline, glow=None):
    """閉眼：眼位填返皮膚色，畫 1px「︶」閉眼線（深眼用外框色；發光眼用眼本身最光嘅色＝發光細縫）"""
    o = out.copy(); L = lum(out[..., :3].astype(float))
    for cy, cx, sz, m, skin, core in eyes:
        ys, xs = np.nonzero(core); eL = L[m]; bright = glow if glow is not None else np.median(eL) > lum(skin[None])[0] + 20
        lc = out[m][np.argmax(eL), :3] if bright else np.clip(outline, 0, 255).astype(int)
        o[m, :3] = skin.astype(np.uint8)
        yl = int(round(max(cy, (ys.min() + ys.max()) / 2))) + (0 if bright else 1); xa, xb = xs.min(), xs.max()
        if xb - xa < 2: xa, xb = xa - 1, xb + 1
        wmax = int(round(6 * K / 1.25))   # 80px：閉眼線最闊 6px（星眼／發光眼窩唔好拉到成條長線）
        if xb - xa + 1 > wmax: c0 = int(round(cx)); xa, xb = c0 - wmax // 2, c0 - wmax // 2 + wmax - 1
        for x in range(xa, xb + 1):
            yy = yl - 1 if (x in (xa, xb) and xb - xa >= 3) else yl
            o[yy, x] = (*lc, 255)
    return o
def blink(out, eyes, outline):
    o = out.copy(); a = out[..., 3] == 255
    for cy, cx, sz, m in eyes:
        ring = ndi.binary_dilation(m, iterations=1) & ~m & a
        L = lum(out[..., :3].astype(float)); cand = out[ring & (L > 70) & (L < 230)][:, :3]
        skin = np.median(cand, 0) if len(cand) else out[ring][:, :3].mean(0)
        ys, xs = np.nonzero(m); o[m, :3] = skin.astype(np.uint8)
        yl = int(round(cy)) + 1
        for x in range(xs.min(), xs.max() + 1): o[yl, x] = (*np.clip(outline, 0, 255).astype(int), 255)
    return o
def squash(out):
    a = out[..., 3] > 0; ys = np.nonzero(a.any(1))[0]; body = np.nonzero((out[..., 3] == 255).any(1))[0]
    cut = int(body.min() + 0.6 * (body.max() - body.min())); o = out.copy()
    o[1:cut + 1] = out[0:cut]; o[0] = 0; return o
def idle_frames(out, outline, key=None):
    h = EYES.get(S, {}).get(key)
    if h:
        ey = eyes_from_hints(out, h)
        if ey: return [out, squash(out), out, blink_hint(out, ey, outline, key in EYE_GLOW.get(S, set()))], True
    eyes = find_eyes(out); f3 = blink(out, eyes, outline) if eyes else out.copy()
    return [out, squash(out), out, f3], bool(eyes)

def build():
    ensure_cache(); IM = {}; META = {}; IDLE = {}
    names = {f"{k}{i+1}": nm[i] for k, row, colx, nm in R.LINES for i in range(3)}
    for key in CFG:
        out, meta, ol = build_one(key); IM[key] = out
        Image.fromarray(out).save(os.path.join(SPD, f"{key}_{S}.png"))
        frs, hasblink = idle_frames(out, ol, key); IDLE[key] = frs
        strip = np.concatenate(frs, 1); Image.fromarray(strip).save(os.path.join(IDD, f"{key}_idle.png"))
        meta.update(eyesHand=key in EYES.get(S, {}), noiseFixed=NOISE.get(key, 0), name=names[key], file=f"sprites/{key}_{S}.png", idle=f"idle/{key}_idle.png", blink=hasblink); META[key] = meta
        print(key, meta, flush=True)
    json.dump({"source": "Kurt 參考圖（Kurt 自己用 AI 生成，擁有權已確認 [pt92u]）", "size": [S, S], "pivot": [S // 2, FOOT], "pivotRule": "(w/2, h-3)",
               "idle": {"frames": 4, "frameW": S, "durationsMs": [260, 180, 260, 140], "note": "0 原、1 上半身壓低 1px、2 原、3 眨眼（冇眨眼＝同 0）"},
               "creatures": META}, open(os.path.join(OUT, "tuned.json"), "w"), ensure_ascii=False, indent=1)
    sheets(IM, names); return IM

def sheets(IM, names):
    BGc = (92, 84, 136); BG2 = (100, 92, 146); CAP = (247, 239, 222); f12 = B.font(12); f15 = B.font(15)
    cw = S * 4 + 16; W = 150 + 3 * cw; Ht = 40 + 8 * cw
    im = Image.new("RGB", (W, Ht), BGc); d = ImageDraw.Draw(im); d.fontmode = "1"
    d.text((10, 10), f"from_ref/{os.path.basename(OUT)}：遊戲用 {S}px（×4）— 同階同體量、地線 y={FOOT}", font=f15, fill=CAP)
    for i, (k, row, col, nm) in enumerate(R.LINES):
        y = 40 + i * cw; d.text((8, y + cw // 2 - 10), f"{k} 線", font=f15, fill=CAP)
        for st in (1, 2, 3):
            cx = 150 + (st - 1) * cw
            if (i + st) % 2: d.rectangle([cx, y, cx + cw - 1, y + cw - 1], fill=BG2)
            z = Image.fromarray(IM[f"{k}{st}"]).resize((S * 4, S * 4), Image.NEAREST); im.paste(z, (cx + 8, y + 2), z)
            d.line([cx + 8, y + 2 + (FOOT + 1) * 4, cx + 8 + S * 4 - 1, y + 2 + (FOOT + 1) * 4], fill=(130, 120, 175))
            d.text((cx + 6, y + cw - 16), f"{k}{st} {nm[st - 1]}", font=f12, fill=CAP)
    im.save(os.path.join(OUT, "lineup_4x.png"))
    # before/after：左＝舊切圖、右＝tuned（3x，淺底／深底）
    if S == 64:
        z = 192; cwb = 2 * z + 30; W = 20 + 3 * cwb; rh = z + 24; Ht = 44 + 8 * rh
        im = Image.new("RGB", (W, Ht), (40, 34, 60)); d = ImageDraw.Draw(im); d.fontmode = "1"
        d.text((12, 12), "before_after：左＝舊 from_ref 切圖／右＝tuned（×3；單數行白底、雙數行深底）", font=B.font(16), fill=CAP)
        for i, (k, row, col, nm) in enumerate(R.LINES):
            y = 44 + i * rh; bgc = (236, 238, 244) if i % 2 == 0 else (52, 48, 72)
            for st in (1, 2, 3):
                key = f"{k}{st}"; X = 20 + (st - 1) * cwb
                for j, src in enumerate((os.path.join(R.SPD, f"{key}_64.png"), os.path.join(SPD, f"{key}_{S}.png"))):
                    d.rectangle([X + j * (z + 6), y, X + j * (z + 6) + z - 1, y + z - 1], fill=bgc)
                    s = Image.open(src).convert("RGBA").resize((z, z), Image.NEAREST); im.paste(s, (X + j * (z + 6), y), s)
                d.text((X, y + z + 4), f"{key} {nm[st - 1]}  舊 → 新", font=f12, fill=CAP)
        im.save(os.path.join(OUT, "before_after_3x.png"))
    # 眨眼檢查表（×3）：每隻 幀0（開眼）｜幀3（閉眼）＋ 眼位放大 ×6
    z = 3; fz = 6; cell = 2 * S * z + 2 * 28 * fz + 30; rh = S * z + 26
    im = Image.new("RGB", (20 + 3 * cell, 44 + 8 * rh), (40, 34, 60)); d = ImageDraw.Draw(im); d.fontmode = "1"
    d.text((12, 12), f"blink check {S}px：幀0 開眼｜幀3 閉眼（×3）＋ 眼部放大（×6）— 黃字＝手放眼位", font=B.font(16), fill=CAP)
    MT = json.load(open(os.path.join(OUT, "tuned.json")))["creatures"]
    for i, (k, row, col, nm) in enumerate(R.LINES):
        for st in (1, 2, 3):
            key = f"{k}{st}"; X = 20 + (st - 1) * cell; Y = 44 + i * rh
            strip = Image.open(os.path.join(IDD, f"{key}_idle.png")).convert("RGBA")
            f0 = strip.crop((0, 0, S, S)); f3 = strip.crop((3 * S, 0, 4 * S, S))
            diff = np.abs(np.asarray(f0, int) - np.asarray(f3, int)).sum(2) > 0
            for j, fr in enumerate((f0, f3)):
                bg = Image.new("RGBA", (S, S), (92, 84, 136, 255)); bg.alpha_composite(fr)
                im.paste(bg.convert("RGB").resize((S * z, S * z), Image.NEAREST), (X + j * S * z, Y))
            if diff.any():
                ys, xs = np.nonzero(diff); cy, cx = int(ys.mean()), int(xs.mean())
                bx = (max(0, min(S - 28, cx - 14)), max(0, min(S - 14, cy - 7)))
                for j, fr in enumerate((f0, f3)):
                    bg = Image.new("RGBA", (S, S), (92, 84, 136, 255)); bg.alpha_composite(fr)
                    cr = bg.crop((bx[0], bx[1], bx[0] + 28, bx[1] + 14)).convert("RGB").resize((28 * fz, 14 * fz), Image.NEAREST)
                    im.paste(cr, (X + 2 * S * z + 10 + j * (28 * fz + 4), Y + (0 if j == 0 else 0) + j * 0 + (S * z - 14 * fz) // 2 * 0 + j * 0))
            hand = key in EYES.get(S, {})
            d.text((X + 2, Y + S * z + 4), f"{key} {nm[st - 1]}  blink={'OK' if MT[key]['blink'] else '—'}{'（手放眼位）' if hand else ''}", font=f12, fill=(255, 220, 120) if hand else CAP)
    im.save(os.path.join(OUT, "blink_check_3x.png"))
    # idle 預覽 gif（×3）
    for key in IM:
        strip = Image.open(os.path.join(IDD, f"{key}_idle.png")).convert("RGBA"); frs = []
        for fi in range(4):
            bg = Image.new("RGBA", (S, S), (70, 64, 104, 255)); fr = strip.crop((fi * S, 0, fi * S + S, S)); bg.alpha_composite(fr)
            frs.append(bg.convert("RGB").resize((3 * S, 3 * S), Image.NEAREST))
        frs[0].save(os.path.join(IDD, f"{key}_idle_3x.gif"), save_all=True, append_images=frs[1:], duration=[260, 180, 260, 140], loop=0)

def check():
    E = []
    for key in CFG:
        a = np.array(Image.open(os.path.join(SPD, f"{key}_{S}.png")).convert("RGBA"))
        if a.shape[:2] != (S, S): E.append(f"{key}: size")
        if not np.isin(a[..., 3], ALPHAS).all(): E.append(f"{key}: alpha")
        if a[0, :, 3].any() or a[-1, :, 3].any() or a[:, 0, 3].any() or a[:, -1, 3].any(): E.append(f"{key}: 貼邊")
        b = np.nonzero((a[..., 3] == 255).any(1))[0]
        if b.max() != FOOT: E.append(f"{key}: 地線 {b.max()}")
        st = np.array(Image.open(os.path.join(IDD, f"{key}_idle.png")).convert("RGBA"))
        if st.shape[:2] != (S, 4 * S): E.append(f"{key}: idle size")
    for e in E: print("ERR", e)
    print(f"tuned check: {len(E)} errors；{len(CFG)} sprites"); return E
if __name__ == "__main__":
    w = sys.argv[1] if len(sys.argv) > 1 else "all"
    if w == "all": build()
    sys.exit(1 if check() else 0)
