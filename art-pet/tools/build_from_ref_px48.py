#!/usr/bin/env python3
"""build_from_ref_px48 — Kurt [pt98u]「用舊既size，同新寵好似有d圖唔太仔細crack左咁」。
新寵縮返舊 evo 寵物尺寸：48×48 canvas、pivot (24,45)、身體最底行 46（同 evo6 evo_still_* 一樣），
每階體量對標舊寵：tier1≈evo_hop(38)、tier2≈evo_guard(44)、tier3≈evo_still(48)。
唔係直接縮細：12 色盤 → 加權眾數降採樣 → 補洞／刪孤島／削尖刺 → 同色細碎塊合併 → 熔岩裂紋改成少量乾淨發光脈 →
1px 閉合外框 → 右下 1px 暗邊（統一左上光）→ 手繪眼（3×4＋高光）／眨眼 → 細燈泡 → 粒子 ≤4 粒、離身 ≥2px。
alpha 只得 0／255（同舊 evo 一樣；柔光交返引擎 glowR）。全部 numpy／Pillow，冇 AI 生圖。
用法：python3 build_from_ref_px48.py"""
import os, sys, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_from_ref as R

S = 48; GROUND = 46; PIV = (24, 45)            # 舊 evo：pivotPx (w/2, h-3)，腳底像素行 h-2
FR = os.path.join(R.OUT)                         # .../species_concept/from_ref
OUT = os.path.join(FR, "tuned_48"); SPD = os.path.join(OUT, "sprites"); IDD = os.path.join(OUT, "idle")
for d in (SPD, IDD): os.makedirs(d, exist_ok=True)
T80 = json.load(open(os.path.join(FR, "tuned_80", "tuned.json")))["creatures"]
EYES80 = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "from_ref_eyes80.json")))   # 80px 眼中心／框（由 80 眨眼幀差計；F3 右眼 wink 手加）
KEYS = [f"{a}{b}" for a in "ABCDEFGH" for b in (1, 2, 3)]
# 舊寵實測（idle_01 不透明 px）：evo_hop 621、evo_guard 659–832（中位 ~735）、evo_still 838–1091（中位 ~900）
OLD_REF = {1: ("evo_hop", 38, 621), 2: ("evo_guard_*", 44, 735), 3: ("evo_still_*", 48, 900)}
MASS = {1: 590, 2: 690, 3: 850}                  # 主體目標 px（加埋外框／燈泡／粒子 ≈ 舊寵總量）
NCOL = 12
CFG = {k: {} for k in KEYS}
for k in ("B1", "H3"): CFG[k]["bulb"] = "own"
for k in ("F1", "G1"): CFG[k]["bulb"] = "star"
CFG["H3"]["ncol"] = 10; CFG["H3"]["mass"] = 0.9; CFG["H3"]["speck"] = 3
for k in ("A1", "A2", "A3", "B1", "B2", "B3"): CFG[k]["stamp"] = "bubble"
for k in ("C1", "C2", "C3", "D1", "D2", "D3", "E1", "E2", "E3"): CFG[k]["stamp"] = "ember"
for k in ("F1", "F2", "F3", "G1", "G2", "G3", "H1", "H2", "H3"): CFG[k]["stamp"] = "star"
LAVA = {"D1": 3, "D2": 4, "E3": 4}               # 熔岩裂紋 → 最多 N 條乾淨發光脈
# 眼型：dark＝深色 3×4＋高光；glow＝發光眼（angry＝內上角削走）；arc＝閉眼 ^；half＝瞓眼（眼皮線＋半眼）；star＝四角星
EYE = {k: "dark" for k in KEYS}
EYE.update({"A3": "arc", "B2": "glow", "C3": "glow_angry", "D1": "glow_angry", "D2": "glow_angry", "E3": "glow_angry",
            "F1": "half", "F2": "half", "G1": "half", "H2": "half", "G3": "glow", "H3": "star", "D3": "dark_angry", "C2": "dark"})
EYE_ONE = {"F3": ["dark", "wink"]}               # F3：一隻開一隻 wink（按 x 由左至右）
NAMES = {k: v.get("name", k) for k, v in T80.items()}

def lum(c): c = np.asarray(c, float); return c[..., 0] * .299 + c[..., 1] * .587 + c[..., 2] * .114
def load(key):
    p = f"/tmp/cut_{key}.npz"
    if not os.path.exists(p):
        src = np.array(Image.open(R.REF).convert("RGB")); c, A, _ = R.cutout(key, src)
        np.savez_compressed(p, col=c.astype(np.float32), A=A.astype(np.uint8))
    z = np.load(p); return z["col"].astype(float), z["A"].astype(int)
def palette_of(col, body, n):
    pts = col[body].astype(np.uint8)
    q = Image.fromarray(pts.reshape(1, -1, 3)).quantize(colors=n, method=Image.Quantize.MEDIANCUT, kmeans=3)
    pal = np.array(q.getpalette()[:n * 3]).reshape(-1, 3)
    idx = np.array(q).reshape(-1); used = np.unique(idx); remap = -np.ones(len(pal), int); remap[used] = np.arange(len(used))
    full = -np.ones(body.shape, int); full[body] = remap[idx]; return pal[used].astype(float), full
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1)); CROSS = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool)
def nb_mode(idx, y, x, excl=None, r=1):
    nb = idx[max(0, y - r):y + r + 1, max(0, x - r):x + r + 1].ravel(); nb = nb[nb >= 0]
    if excl is not None: nb = nb[~np.isin(nb, excl)]
    if not len(nb): return -1
    v, c = np.unique(nb, return_counts=True); return int(v[np.argmax(c)])

FIX = {}
def cleanup(idx, pal, key, protect=None, smax=2):
    """真像素清理：補洞、刪孤島／尖刺、補凹位、同色細碎塊合併"""
    pl = lum(pal); n = {"holes": 0, "islands": 0, "spurs": 0, "notch": 0, "specks": 0}
    for it in range(3):
        m = idx >= 0
        # 1) 細洞（≤6px）補返
        holes = ndi.binary_fill_holes(m) & ~m; hl, hn = ndi.label(holes)
        for i in range(1, hn + 1):
            c = hl == i
            if c.sum() <= 6:
                for y, x in zip(*np.nonzero(c)): idx[y, x] = nb_mode(idx, y, x); n["holes"] += 1
        m = idx >= 0
        # 2) 孤島（<6px 嘅獨立身體碎）刪走
        lab, ln = ndi.label(m, np.ones((3, 3))); sz = ndi.sum(m, lab, range(1, ln + 1))
        for i, s_ in enumerate(sz):
            if s_ < 6: idx[lab == i + 1] = -1; n["islands"] += int(s_)
        m = idx >= 0
        # 3) 1px 尖刺（4 鄰只得 ≤1 個身體）刪；凹位（4 鄰 ≥3 個身體）補
        nb4 = sum(np.roll(np.roll(m, dy, 0), dx, 1) for dy, dx in N4)
        for y, x in zip(*np.nonzero(m & (nb4 <= 1))): idx[y, x] = -1; n["spurs"] += 1
        m = idx >= 0; nb4 = sum(np.roll(np.roll(m, dy, 0), dx, 1) for dy, dx in N4)
        for y, x in zip(*np.nonzero(~m & (nb4 >= 3))):
            if 0 < y < S - 1 and 0 < x < S - 1: idx[y, x] = nb_mode(idx, y, x); n["notch"] += 1
    # 4) 同色細碎塊：1px 塊一律併入鄰居眾數；2px 塊低對比（色差 <90）都併
    for it in range(3):
        ch = 0
        for ci in range(len(pal)):
            lab, ln = ndi.label(idx == ci, CROSS)
            for i in range(1, ln + 1):
                c = lab == i; s_ = int(c.sum())
                if s_ > smax: continue
                if protect is not None and (c & protect).any(): continue
                ring = ndi.binary_dilation(c, np.ones((3, 3), bool)) & ~c & (idx >= 0)
                if not ring.any(): continue
                v, cnt = np.unique(idx[ring], return_counts=True); mo = int(v[np.argmax(cnt)])
                if s_ >= 2 and s_ == smax == 2 and np.abs(pal[mo] - pal[ci]).sum() >= 90: continue
                idx[c] = mo; ch += 1
        n["specks"] += ch
        if not ch: break
    FIX[key] = {k: FIX.get(key, {}).get(k, 0) + v for k, v in n.items()}
    return idx

def lava_veins(idx, pal, key, nmax):
    """熔岩：亮橙／黃色塊分類 → 頂部大火焰保留；身上裂紋只留最長 N 條，重畫成 1px 亮脈（中間最亮、兩頭橙）"""
    pl = lum(pal); sat = pal.max(1) - pal.min(1)
    hot = [i for i in range(len(pal)) if pal[i][0] > 60 and pal[i][0] - pal[i][2] > 40 and pal[i][0] >= pal[i][1]]   # 紅／橙／黃（連暗紅裂縫）
    if not hot: return idx, []
    rock = [i for i in range(len(pal)) if i not in hot]
    H = np.isin(idx, hot); lab, ln = ndi.label(H, np.ones((3, 3), bool))
    m = idx >= 0; rows = np.nonzero(m.any(1))[0]; top = rows.min(); hgt = rows.max() - top
    keep_flame = np.zeros_like(H); veins = []
    for i in range(1, ln + 1):
        c = lab == i; ys, xs = np.nonzero(c)
        if c.sum() >= 14 and ys.min() <= top + 0.35 * hgt:   # 頭頂火焰：只留火焰行範圍內／夠亮嘅部分，下面拖落嚟嘅暗紅裂縫當裂紋
            fl = c & ((np.arange(S)[:, None] <= top + 0.3 * hgt) | (pl[np.maximum(idx, 0)] > 150))
            fl = ndi.binary_opening(fl, np.ones((2, 2), bool)) | (fl & (np.arange(S)[:, None] <= top + 0.3 * hgt))
            keep_flame |= fl; rest = c & ~fl
            if rest.sum(): veins.append((int(rest.sum()), rest))
            continue
        if c.sum() >= 14 and ys.max() >= rows.max() - 3 and len(np.unique(ys)) <= 4: keep_flame |= c; continue   # 底部熔岩口
        veins.append((int(c.sum()), c))
    # 全部非火焰亮色 → 岩石色
    for _, c in veins:
        for y, x in zip(*np.nonzero(c)): idx[y, x] = nb_mode(idx, y, x, excl=hot, r=2)
    veins.sort(key=lambda t: -t[0]); kept = []
    eye_zone = np.zeros_like(H)
    for sz, c in veins:
        if len(kept) >= nmax or sz < 3: break
        ys, xs = np.nonzero(c); cy, cx = ys.mean(), xs.mean()
        if len(xs) >= 2:
            cov = np.cov(np.vstack([xs, ys])); w, v = np.linalg.eigh(cov); d = v[:, np.argmax(w)]
        else: d = np.array([1.0, 0.0])
        proj = (xs - cx) * d[0] + (ys - cy) * d[1]; L = min(max(proj.max() - proj.min(), 3), 7)
        pts = []
        for t in np.linspace(-L / 2, L / 2, int(L * 2) + 1):
            p = (int(round(cy + t * d[1])), int(round(cx + t * d[0])))
            if p not in pts: pts.append(p)
        # 只畫喺身體內、唔貼外框（離邊 ≥2）
        inner = ndi.binary_erosion(idx >= 0, iterations=2)
        pts = [p for p in pts if inner[p]]
        if len(pts) < 3: continue
        kept.append(pts)
    return idx, kept

def outline_and_shade(idx, pal, key, outline, flame=None):
    m = idx >= 0; pl = lum(pal)
    edge = m & ~ndi.binary_erosion(m, structure=CROSS, border_value=0)
    out = np.zeros((S, S, 4), np.uint8)
    # 光向：左上。右下內邊 1px 暗 16%，左上內邊亮 8%（只限中亮色；少過 3px 嘅短段唔做，免得變雜點）
    inner = m & ~edge; inner_edge = inner & ~ndi.binary_erosion(inner, structure=CROSS, border_value=0)
    gy, gx = np.gradient(ndi.gaussian_filter(m.astype(float), 1.2))
    shade = np.zeros_like(m); hi = np.zeros_like(m)
    for y, x in zip(*np.nonzero(inner_edge)):
        if not (70 < pl[idx[y, x]] < 230): continue
        nx, ny = -gx[y, x], -gy[y, x]; nn = math.hypot(nx, ny) or 1; dot = (nx + ny) / nn / math.sqrt(2)
        if dot > 0.45: shade[y, x] = True
        elif dot < -0.6: hi[y, x] = True
    for mk in (shade, hi):
        lb, nb_ = ndi.label(mk, np.ones((3, 3), bool))
        for i in range(1, nb_ + 1):
            if (lb == i).sum() < 3: mk[lb == i] = False
    for y, x in zip(*np.nonzero(m)):
        c = pal[idx[y, x]].copy()
        if edge[y, x]:
            if pl[idx[y, x]] > lum(outline) + 28:
                hotc = pl[idx[y, x]] > 150 and (pal[idx[y, x]].max() - pal[idx[y, x]].min()) > 90   # 亮黃／火焰／月：選擇性外框（深一截同色）
                c = outline * (0.55 if flame else 0.68) + c * (0.45 if flame else 0.32) if hotc else outline
        elif shade[y, x]: c = c * 0.84
        elif hi[y, x]: c = np.minimum(255, c * 1.08 + 10)
        out[y, x] = (*np.clip(c, 0, 255).astype(int), 255)
    return out

def put(out, x, y, c):
    x, y = int(x), int(y)
    if 0 < x < S - 1 and 0 < y < S - 1: out[y, x] = (*np.clip(np.asarray(c, float), 0, 255).astype(int), 255)

# 細泡／火星／星粉（離身 ≥2px、最多 N 粒）
def stamp(out, kind, x, y, big, c, outline):
    if kind == "bubble":
        rim = np.clip(np.asarray(c, float) * 0.5 + np.array([150, 220, 255]) * 0.5, 0, 255)
        if big:   # 4×4 圈
            for dx, dy in ((1, 0), (2, 0), (0, 1), (3, 1), (0, 2), (3, 2), (1, 3), (2, 3)): put(out, x - 1 + dx, y - 1 + dy, rim)
            put(out, x, y, (255, 255, 255))
        else:     # 3×3 圈（中空）
            for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)): put(out, x + dx, y + dy, rim)
            put(out, x - 1 + 0, y - 1, (255, 255, 255)) if False else None
    elif kind == "ember":
        put(out, x, y, (255, 236, 150))
        if big: put(out, x, y + 1, (255, 150, 60)); put(out, x - 1, y, (255, 150, 60))
    else:
        core = (255, 250, 220); arm = (255, 222, 120)
        put(out, x, y, core)
        if big:
            for dx, dy in N4: put(out, x + dx, y + dy, arm)
def stamp_mask(kind, x, y, big):
    if kind == "bubble": return [(x - 1 + dx, y - 1 + dy) for dx in range(4) for dy in range(4)] if big else [(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]
    if kind == "ember": return [(x, y), (x, y + 1), (x - 1, y)]
    return [(x, y)] + ([(x + dx, y + dy) for dx, dy in N4] if big else [])

BULB_OL = (92, 60, 40); BULB_C1 = (255, 214, 90); BULB_C2 = (255, 244, 190); BULB_D = (232, 168, 60); STEM = (70, 52, 84)
BULB48 = [".OOO.",
          "OWYYO",
          "OYYDO",
          ".ODO.",
          "..O.."]
STAR48 = ["...O...",
          "..OYO..",
          "OOOYOOO",
          "OYWYYYO",
          ".OYYDO.",
          "OYDODYO",
          "OO...OO"]
def draw_bulb(out, x, y):
    """5×5 細燈泡（舊寵燈泡大細）＋ 莖垂直落到頭頂"""
    a = out[..., 3] == 255
    col = np.nonzero(a[y + 3:, x])[0]; yt = y + 3 + (col.min() if len(col) else 3)
    for t in range(y + 3, yt): put(out, x, t, STEM)
    C = {"O": BULB_OL, "Y": BULB_C1, "W": BULB_C2, "D": BULB_D}
    for j, row in enumerate(BULB48):
        for i, ch in enumerate(row):
            if ch in C: put(out, x - 2 + i, y - 2 + j, C[ch])
    put(out, x - 1, y - 1, (255, 255, 255))
def draw_star(out, outline):
    """F1／G1：頂部天線嗰嚿清走，畫 7×7 像素星＋莖"""
    a = out[..., 3] == 255; rows = np.nonzero(a.any(1))[0]; top = rows.min()
    wid = [a[y].sum() if a[y].any() else 99 for y in range(top, top + 16)]
    neck = top + 3 + int(np.argmin(wid[3:12]))
    xs = np.nonzero(a[neck])[0]; nx = int(round(xs.mean())) if len(xs) else 24
    ys_, xs_ = np.nonzero(a[:neck]); cx = int(round(xs_.mean())) if len(xs_) else nx
    out[:neck] = 0
    cy = max(4, neck - 5)
    for t in range(cy + 3, neck + 1): put(out, nx, t, STEM)
    C = {"O": outline, "Y": (255, 222, 110), "W": (255, 252, 230), "D": (232, 168, 60)}
    for j, row in enumerate(STAR48):
        for i, ch in enumerate(row):
            if ch in C: put(out, cx - 3 + i, cy - 3 + j, C[ch])
    return cx, cy

# 眼
EYE_DK = (34, 26, 44); EYE_HI = (255, 255, 255)
EYEPAT = {
    "dark":   [".DD.", "DDHD", "DDDD", ".DD."],
    "dark_angry0": ["DD..", "DDHD", "DDDD", ".DD."], "dark_angry1": ["..DD", "DHDD", "DDDD", ".DD."],
    "glow":   [".GG.", "GHGG", ".BB."],
    "glow_angry0": ["GG..", "GHGG", ".BBB"], "glow_angry1": ["..GG", "GGHG", "BBB."],
    "half":   ["LLLL", "DDHD", ".DD."],
    "arc":    [".DD.", "D..D"], "wink": [".DD.", "D..D"],
    "star":   [".G.", "GHG", ".G."],
}
def eye_cells(kind, side):
    """返 [(dx,dy,code)]，原點＝眼框左上。code: D 深 H 高光 G 發光 B 發光暗 L 眼皮"""
    p = EYEPAT.get(kind) or EYEPAT[kind + str(side)]
    off = 1 if kind in ("glow", "glow_angry", "half", "arc", "wink") else 0
    if kind == "star": return [(dx + 1, dy + 1, ch) for dy, r in enumerate(p) for dx, ch in enumerate(r) if ch != "."]
    return [(dx, dy + off, ch) for dy, r in enumerate(p) for dx, ch in enumerate(r) if ch != "."]
def blink_cells(kind):
    if kind in ("arc", "wink"): return [(0, 2, "D"), (1, 2, "D"), (2, 2, "D"), (3, 2, "D")]   # ^ 壓平
    if kind == "half": return [(0, 2, "D"), (1, 2, "D"), (2, 2, "D"), (3, 2, "D")]
    if kind == "star": return [(1, 2, "D"), (2, 2, "D"), (3, 2, "D")]
    return [(0, 1, "D"), (1, 2, "D"), (2, 2, "D"), (3, 1, "D")]                               # ︶

def build_one(key):
    cf = CFG[key]; st = int(key[1]); col, A = load(key); Hh, Ww = A.shape
    body = A == 255; lab, n = ndi.label(body, np.ones((3, 3))); sizes = ndi.sum(body, lab, range(1, n + 1))
    big = sizes.max(); main_ids = [i + 1 for i, s_ in enumerate(sizes) if s_ >= max(0.04 * big, 500)]
    sat_ids = [i + 1 for i, s_ in enumerate(sizes) if (i + 1) not in main_ids and s_ >= 10]
    main = np.isin(lab, main_ids)
    if key == "H3":   # 光環同魔杖喺原圖黐住個頭：用開運算削走幼件（光環之後程序重畫）
        main = ndi.binary_opening(main, structure=CROSS, iterations=6)
        ll, nl = ndi.label(main); main = ll == (np.argmax(ndi.sum(main, ll, range(1, nl + 1))) + 1)
        body = body & (main | ~np.isin(lab, main_ids))
    s = math.sqrt(MASS[st] * cf.get("mass", 1.0) / main.sum())
    ys, xs = np.nonzero(main); top_room = 2 if cf.get("bulb") == "own" else 7
    s = min(s, (S - 6.0) / (xs.max() - xs.min() + 1), (GROUND + 1 - top_room) / (ys.max() - ys.min() + 1))
    cx = (xs.min() + xs.max() + 1) / 2; by = ys.max() + 1; f = 1 / s
    pal, pidx = palette_of(col, body, cf.get("ncol", NCOL)); pl = lum(pal)
    ring = body & ~ndi.binary_erosion(body, iterations=4)
    dark = [i for i in range(len(pal)) if pl[i] < 85]
    cnt = np.bincount(pidx[ring], minlength=len(pal)); oi = max(dark, key=lambda i: cnt[i]) if dark else int(np.argmin(pl))
    outline = pal[oi] * 0.85
    while lum(outline) > 50: outline = outline * 0.85   # 外框一定要夠深（舊寵風格）
    idx = -np.ones((S, S), int)
    w = (pl < 70) * 0.35 + 1.0 + (pl > 215) * 0.9
    for v in range(S):
        for u in range(S):
            x0 = cx + (u - S / 2) * f; y0 = by + (v - GROUND - 1) * f
            xa, ya, xb, yb = max(0, int(round(x0))), max(0, int(round(y0))), min(Ww, int(round(x0 + f))), min(Hh, int(round(y0 + f)))
            if xb <= xa or yb <= ya: continue
            bb = main[ya:yb, xa:xb]
            if bb.mean() >= 0.45:
                ii = pidx[ya:yb, xa:xb][bb]; idx[v, u] = int(np.argmax(np.bincount(ii, minlength=len(pal)) * w))
    # 衛星（泡、火星、星粉、大件分離部件例如月亮／光環）
    sats = []
    for i in sat_ids:
        comp = lab == i; cy_, cx_ = ndi.center_of_mass(comp); d = math.sqrt(comp.sum()) * s
        u = (cx_ - cx) * s + S / 2; v = (cy_ - by) * s + GROUND + 1
        if d >= 6 and key == "H3": continue   # H3：光環程序畫、魔杖太幼刪走
        if d >= 6:   # 大件（光環、月亮、燈籠）照降採樣
            for vv in range(S):
                for uu in range(S):
                    x0 = cx + (uu - S / 2) * f; y0 = by + (vv - GROUND - 1) * f
                    xa, ya, xb, yb = max(0, int(round(x0))), max(0, int(round(y0))), min(Ww, int(round(x0 + f))), min(Hh, int(round(y0 + f)))
                    if xb <= xa or yb <= ya: continue
                    bb = comp[ya:yb, xa:xb]
                    if bb.mean() >= 0.45: idx[vv, uu] = int(np.argmax(np.bincount(pidx[ya:yb, xa:xb][bb], minlength=len(pal)) * w))
        else: sats.append((d, u, v, col[comp].mean(0)))
    # 眼位（由 80px 眨眼差異位映射）
    s80 = T80[key]["scale"]; r = s / s80
    eyes = []
    for e in sorted(EYES80[key]):
        ex = (e[0] - 40) * r + 24; ey = (e[1] - 78) * r + GROUND + 1
        bw = (e[4] - e[2] + 1) * r; bh = (e[5] - e[3] + 1) * r
        eyes.append([ex, ey, bw, bh])
    # 擦走降採樣出嚟嘅眼（之後手繪）：眼框 ±1 內同皮膚差好遠嘅像素 → 皮膚色
    protect = np.zeros((S, S), bool)
    for ex, ey, bw, bh in eyes:
        x0, x1 = int(math.floor(ex - bw / 2)) - 1, int(math.ceil(ex + bw / 2)) + 1
        y0, y1 = int(math.floor(ey - bh / 2)) - 1, int(math.ceil(ey + bh / 2)) + 1
        box = np.zeros((S, S), bool); box[max(0, y0):y1 + 1, max(0, x0):x1 + 1] = True
        rng = ndi.binary_dilation(box, iterations=2) & ~box & (idx >= 0)
        if not rng.any(): continue
        rv = idx[rng]; rv = rv[pl[rv] > 60] if (pl[rv] > 60).any() else rv
        vv, cc = np.unique(rv, return_counts=True); skin = int(vv[np.argmax(cc)])
        for y, x in zip(*np.nonzero(box & (idx >= 0))):
            if np.abs(pal[idx[y, x]] - pal[skin]).sum() > 70: idx[y, x] = skin
    if key == "H3":   # 光環殘留金色 → 身體色
        gold = [i for i in range(len(pal)) if pal[i][0] > 190 and pal[i][1] > 150 and pal[i][2] < 170]
        rows = np.nonzero((idx >= 0).any(1))[0]; lim = rows.min() + 0.3 * (rows.max() - rows.min())
        for y, x in zip(*np.nonzero(np.isin(idx, gold))):
            if y < lim: idx[y, x] = nb_mode(idx, y, x, excl=gold, r=2)
    idx = cleanup(idx, pal, key, smax=CFG[key].get("speck", 2))
    veins = []
    if key in LAVA: idx, veins = lava_veins(idx, pal, key, LAVA[key]); idx = cleanup(idx, pal, key)
    out = outline_and_shade(idx, pal, key, outline, flame=cf.get("stamp") == "ember")
    # 淨係外框色、身邊冇內部色嘅幼線／尖枝（例如火焰頂黑煙枝）→ 刪（會讀成裂痕／頭髮）
    ocol = np.clip(outline, 0, 255).astype(int)
    for _ in range(4):
        a = out[..., 3] == 255; isol = a & (np.abs(out[..., :3].astype(int) - ocol).sum(2) <= 6)
        interior = a & ~isol; near = ndi.binary_dilation(interior, np.ones((3, 3), bool))
        kill = isol & ~near
        if not kill.any(): break
        out[kill] = 0; FIX[key]["olOnly"] = FIX[key].get("olOnly", 0) + int(kill.sum())
    if key == "H3":   # 程序光環：頭頂橢圓金圈（前半亮、後半暗金、外圈深框）
        a = out[..., 3] == 255; rows = np.nonzero(a.any(1))[0]; cols = np.nonzero(a.any(0))[0]
        hx = (42.5 - 40) * r + 24; hy = rows.min() - 1.5; rx = 34 / 2 * r * 0.95; ry = 2.4
        ring, outer = [], []
        for y in range(int(hy - ry - 2), int(hy + ry + 3)):
            for x in range(int(hx - rx - 2), int(hx + rx + 3)):
                d = math.hypot((x - hx) / rx, (y - hy) / ry)
                dd = math.hypot((x - hx) / (rx + 1), (y - hy) / (ry + 1))
                if 0.62 <= d <= 1.08: ring.append((x, y))
                elif dd <= 1.08 and d > 1.08: outer.append((x, y))
        for x, y in outer:
            if 0 < y < S and out[y, x, 3] == 0: put(out, x, y, outline)
        for x, y in ring: put(out, x, y, (255, 230, 130) if y >= hy else (214, 168, 70))
        CFG[key]["light_xy"] = (int(round(hx)), int(round(hy)))
    # 熔岩脈：1px 亮線，中段最亮，兩頭橙
    for pts in veins:
        nn = len(pts)
        for j, (y, x) in enumerate(pts):
            t = abs(j - (nn - 1) / 2) / max(1, (nn - 1) / 2)
            put(out, x, y, (255, 240, 160) if t < 0.5 else (255, 168, 56))
    # 手繪眼
    eye_draw = []
    kinds = EYE_ONE.get(key, [EYE[key]] * len(eyes))
    for j, (ex, ey, bw, bh) in enumerate(eyes):
        kind = kinds[j] if j < len(kinds) else EYE[key]
        side = 0 if ex < 24 else 1
        x0 = int(round(ex - 2)); y0 = int(round(ey - 2))
        # 眼色
        glowc = np.array((255, 222, 96)) if key != "B2" else np.array((150, 255, 190))
        if key == "G3": glowc = np.array((255, 226, 120))
        if key == "H3": glowc = np.array((255, 224, 110))
        C = {"D": EYE_DK if kind not in ("arc", "wink") else np.clip(outline * 0.8, 0, 255), "H": EYE_HI if "glow" not in kind and kind != "star" else (255, 255, 235),
             "G": glowc, "B": glowc * 0.78, "L": np.clip(outline * 0.8, 0, 255)}
        if kind == "half": C["H"] = (190, 200, 230)
        for dx, dy, code in eye_cells(kind, side): put(out, x0 + dx, y0 + dy, C[code])
        eye_draw.append({"x": x0, "y": y0, "kind": kind, "side": side, "lineC": [int(t) for t in (glowc if "glow" in kind or kind == "star" else C["L"] if kind == "half" else EYE_DK)]})
    # 嘴＋腮紅（跟舊寵：眼底下 1 行起 3×2 粉紅腮、‿ 細嘴）
    face = {"mouth": None, "blush": 0}
    if len(eye_draw) == 2:
        L_, R_ = sorted(eye_draw, key=lambda e: e["x"])
        bot = max(e["y"] + max(c[1] for c in eye_cells(e["kind"], e["side"])) for e in eye_draw)
        a = out[..., 3] == 255; inner = ndi.binary_erosion(a, structure=CROSS, iterations=1)
        vset = {(y, x) for pts in veins for (y, x) in pts}
        ok = lambda x, y: 0 <= x < S and 0 <= y < S and inner[y, x] and (y, x) not in vset
        mx = (L_["x"] + R_["x"] + 3) / 2; my = bot + 2
        zone = [(x, y) for y in range(bot + 1, bot + 5) for x in range(int(mx) - 4, int(mx) + 5) if ok(x, y)]
        if zone:
            zc = np.array([out[y, x, :3] for x, y in zone]).astype(int); vv, cc = np.unique(zc, axis=0, return_counts=True); skin = vv[np.argmax(cc)]
            for x, y in zone:   # 先清走縮細後殘留嘅半截嘴
                if lum(out[y, x, :3].astype(float)[None])[0] < lum(skin.astype(float)[None])[0] - 50: out[y, x, :3] = skin
        k0 = L_["kind"]
        if k0 not in ("glow_angry",):
            gap = R_["x"] - (L_["x"] + 3)
            pat = [(0, 0), (3, 0), (1, 1), (2, 1)] if gap >= 6 else [(0, 0), (2, 0), (1, 1)]
            sx = int(round(mx - (2 if gap >= 6 else 1.5)))
            if k0 == "dark_angry": pat = [(1, 1), (2, 1)] if gap >= 6 else [(1, 1)]
            mcol = EYE_DK if lum(np.array(skin, float)[None])[0] > 90 else np.clip(outline * 0.6, 0, 255) if zone else EYE_DK
            if all(ok(sx + dx, my + dy) for dx, dy in pat):
                for dx, dy in pat: put(out, sx + dx, my + dy, mcol)
                face["mouth"] = [sx, my, len(pat)]
        if k0 not in ("glow_angry", "dark_angry") and key not in ("B2",):
            for xs in ((L_["x"] - 2, L_["x"] - 1, L_["x"]), (R_["x"] + 3, R_["x"] + 4, R_["x"] + 5)):
                cells = [(x, y) for y in (bot + 1, bot + 2) for x in xs]
                if sum(ok(x, y) for x, y in cells) >= 5:
                    for x, y in cells:
                        if ok(x, y):
                            base = out[y, x, :3].astype(float); put(out, x, y, np.clip(np.array((242, 139, 155)) * 0.8 + base * 0.2, 0, 255)); face["blush"] += 1
    FACE[key] = face
    # 燈泡
    bxy = None; binfo = "own light"
    if cf.get("bulb") == "star":
        bxy = draw_star(out, outline); binfo = f"星星天線 {bxy}"
    elif cf.get("bulb") != "own":
        b80 = T80[key]["bulbXY"]; bx = int(round((b80[0] - 40) * r + 24)); byy = int(round((b80[1] - 78) * r + GROUND + 1))
        a = out[..., 3] == 255
        # 燈泡固定喺頭頂上 5px（2px 莖），唔再沿用 80px 長莖
        tops = [np.nonzero(a[:, xx])[0].min() for xx in range(bx - 2, bx + 3) if a[:, xx].any()]
        yt = min(tops) if tops else byy + 5
        byy = yt - 5
        byy = max(3, byy); draw_bulb(out, bx, byy); bxy = (bx, byy); binfo = f"({bx},{byy})"
    elif cf.get("light_xy"): bxy = cf["light_xy"]
    else:
        Lm = lum(out[..., :3].astype(float)); a_ = out[..., 3] > 0; rows = np.nonzero(a_.any(1))[0]
        lim = rows.min() + 0.45 * (rows.max() - rows.min()); yy, xx = np.nonzero(a_ & (Lm > 190) & (np.arange(S)[:, None] < lim))
        bxy = (int(xx.mean()), int(yy.mean())) if len(xx) else (24, int(rows.min()))
    # 衛星 stamp：大到細揀，離身 ≥2px，最多 tier+1 粒
    kind = cf.get("stamp"); used = 0; amask = out[..., 3] == 255
    near = ndi.binary_dilation(amask, iterations=2)
    for d, u, v, c in sorted(sats, key=lambda t: -t[0]):
        if used >= st + 1: break
        x, y = int(round(u)), int(round(v)); bigs = d >= 3.2
        pts = stamp_mask(kind, x, y, bigs)
        if any(not (2 <= px < S - 2 and 2 <= py < S - 2) or near[py, px] for px, py in pts):
            # 試向外推 1–2px
            ok = False
            for k_ in (1, 2):
                dx = int(np.sign(x - 24)) * k_; pts2 = stamp_mask(kind, x + dx, y, bigs)
                if all(2 <= px < S - 2 and 2 <= py < S - 2 and not near[py, px] for px, py in pts2): x += dx; ok = True; break
            if not ok: continue
        stamp(out, kind, x, y, bigs, c, outline); used += 1
        near = ndi.binary_dilation(out[..., 3] == 255, iterations=2)
    # 最後一輪：單點異色（8 鄰全部色差 >90、唔係眼／燈泡／熔岩脈）→ 鄰居眾數
    prot = np.zeros((S, S), bool)
    for e in eye_draw: prot[max(0, e["y"] - 1):e["y"] + 6, max(0, e["x"] - 1):e["x"] + 6] = True
    if bxy: prot[max(0, bxy[1] - 4):bxy[1] + 7, max(0, bxy[0] - 4):bxy[0] + 5] = True
    for pts in veins:
        for (y, x) in pts: prot[y, x] = True
    if key == "H3": prot[:max(0, CFG[key]["light_xy"][1] + 5)] = True
    a = out[..., 3] == 255; rgb = out[..., :3].astype(int); nfix = 0
    for y, x in zip(*np.nonzero(a & ~prot)):
        if not (0 < y < S - 1 and 0 < x < S - 1): continue
        nb = [(y + dy, x + dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx]
        if not all(a[q] for q in nb): continue
        if min(np.abs(rgb[y, x] - rgb[q]).sum() for q in nb) > 90:
            cols, cnt = np.unique(np.array([rgb[q] for q in nb]), axis=0, return_counts=True); out[y, x, :3] = cols[np.argmax(cnt)]; nfix += 1
    FIX[key]["finalSpeck"] = nfix
    featBox = [0, 0, S, CFG[key]["light_xy"][1] + 5] if key == "H3" else None
    # 左右收入 1..46
    cols = np.nonzero(out[..., 3].any(0))[0]; sh = 0
    if cols.max() > S - 2: sh = -(cols.max() - (S - 2))
    elif cols.min() < 1: sh = 1 - cols.min()
    if sh:
        out = np.roll(out, sh, 1); bxy = (bxy[0] + sh, bxy[1])
        for e in eye_draw: e["x"] += sh
    out[:, 0] = out[:, -1] = 0; out[0] = out[-1] = 0
    meta = {"scale": round(s, 4), "colors": int(len(np.unique(out[out[..., 3] == 255][:, :3], axis=0))), "outline": "#%02x%02x%02x" % tuple(int(t) for t in outline),
            "mass": int((out[..., 3] == 255).sum()), "bulb": binfo, "bulbXY": [int(bxy[0]), int(bxy[1])], "bulbType": cf.get("bulb", "bulb"),
            "eyes": eye_draw, "lavaVeins": len(veins), "veinPx": [[int(x) + 0, int(y)] for pts in veins for (y, x) in pts], "fixes": FIX.get(key, {}), "name": NAMES[key], "featBox": featBox, "face": FACE[key]}
    return out, meta

FACE = {}
def idle_frames(out, meta):
    a = out[..., 3] == 255; rows = np.nonzero(a.any(1))[0]; cut = int(rows.min() + 0.6 * (rows.max() - rows.min()))
    f1 = out.copy(); f1[1:cut + 1] = out[0:cut]; f1[0] = 0
    f3 = out.copy()
    for e in meta["eyes"]:
        x0, y0, kind = e["x"], e["y"], e["kind"]
        if kind == "wink": continue
        cells = eye_cells(kind, e["side"]); ys_ = [y0 + c[1] for c in cells]; xs_ = [x0 + c[0] for c in cells]
        # 皮膚＝眼框外一圈眾數
        ring = []
        for y in range(min(ys_) - 1, max(ys_) + 2):
            for x in range(min(xs_) - 1, max(xs_) + 2):
                if (x - x0, y - y0) in [(c[0], c[1]) for c in cells]: continue
                if out[y, x, 3] == 255: ring.append(tuple(out[y, x, :3]))
        vals, cnt = np.unique(np.array(ring), axis=0, return_counts=True); skin = vals[np.argmax(cnt)]
        for dx, dy, _ in cells: f3[y0 + dy, x0 + dx, :3] = skin
        for dx, dy, _ in blink_cells(kind): f3[y0 + dy, x0 + dx] = (*e["lineC"], 255)
    return [out, f1, out.copy(), f3], cut

def main():
    meta = {}; frames = {}
    for k in KEYS:
        out, m = build_one(k); fr, cut = idle_frames(out, m); m["idleCut"] = cut
        Image.fromarray(out).save(os.path.join(SPD, f"{k}_48.png"))
        strip = np.concatenate(fr, 1); Image.fromarray(strip).save(os.path.join(IDD, f"{k}_idle.png"))
        meta[k] = m; frames[k] = fr
        print(k, m["mass"], m["colors"], m["bulb"], m["fixes"], "veins", m["lavaVeins"], [e["kind"] for e in m["eyes"]])
    json.dump({"source": "Kurt 參考圖（Kurt 自己用 AI 生成，擁有權已確認 [pt92u]）", "size": [S, S], "pivot": list(PIV), "groundRow": GROUND,
               "pivotRule": "(w/2, h-3)，身體最底行 h-2（同舊 evo6 evo_still／guard／hop 一樣）", "alpha": "0/255 only（柔光交引擎）",
               "massRef": {str(k): {"oldForm": v[0], "oldCanvas": v[1], "oldMassPx": v[2]} for k, v in OLD_REF.items()},
               "idle": {"frames": 4, "frameW": S, "durationsMs": [260, 180, 260, 140], "note": "0 原、1 上半壓落 1px、2 原、3 眨眼"},
               "creatures": meta}, open(os.path.join(OUT, "tuned.json"), "w"), ensure_ascii=False, indent=1)
    return meta, frames
if __name__ == "__main__":
    main()
