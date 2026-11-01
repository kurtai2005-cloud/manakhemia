#!/usr/bin/env python3
"""reactions_lib — 第 3a 批 觸摸互動＋扮醒呆反應：共用美術庫＋參考合成器（engine reference）。
兩條寵物線都用同一套：
  舊團絨（25 個可穿戴型態：sprout/radiant/soft/lumi＋evo6 21 個）→ 用佢哋自己嘅 idle_01 frame、_noface／_faceov layer、
      accessories/attach/<form>.json（face／eyes／head／side／bulbPt）同 face_anchors（mouth／bulb）。
  新蛋線（from_ref tuned_48，A1–H3）→ 用 tuned_48/idle/{KEY}_idle.png 幀 0、tuned.json（eyes／mouth／bulb／outline）。
全部 numpy／Pillow 程序繪製，冇 AI 生圖。alpha 只得 0／255。"""
import os, json, math
import numpy as np
from PIL import Image

ART = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # .../art-pet
TR = os.path.join(ART, "sprites/tuanrong")
T48 = os.path.join(TR, "species_concept/from_ref/tuned_48")
ATT = os.path.join(TR, "accessories/attach")

def rgba(p): return np.array(Image.open(p).convert("RGBA"))
def hexc(h): h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def mix(a, b, t): return tuple(int(round(a[i] * (1 - t) + b[i] * t)) for i in range(3))
def lum(c): return c[0] * .299 + c[1] * .587 + c[2] * .114

# ───────────────────────── 寵物登記 ─────────────────────────
NEW_KEYS = [f"{a}{b}" for a in "ABCDEFGH" for b in (1, 2, 3)]
OLD_FORMS = ["sprout", "radiant", "soft", "lumi", "evo_dot", "evo_sprout", "evo_hop"] + \
    [f"evo_{s}_{r}" for s in ("guard", "still") for r in ("tide", "moon", "shroom", "crystal", "ember", "radiant", "soft", "dust", "lumi")]
# 系（per-series 自訂幀用）：新線 A–H；舊線按路線，未分路線＝base
NEW_SERIES = {"A": "drop", "B": "bubble", "C": "ember", "D": "pebble", "E": "flame", "F": "star", "G": "star_blue", "H": "crescent"}
OLD_SERIES = {"tide": "drop", "moon": "crescent", "shroom": "spore", "crystal": "shard", "ember": "ember", "radiant": "star",
              "soft": "fluff", "dust": "mote", "lumi": "firefly", "base": "leaf"}
def series_of(pid):
    if pid in NEW_KEYS: return "new_" + pid[0], NEW_SERIES[pid[0]]
    for r in OLD_SERIES:
        if pid.endswith("_" + r) or pid == r and r in ("radiant", "soft", "lumi"): return "old_" + r, OLD_SERIES[r]
    return "old_base", OLD_SERIES["base"]

# 新線眼型（抄 build_from_ref_px48.EYEPAT，避免 import 嗰個 build 檔嘅副作用）
EYEPAT = {
    "dark": [".DD.", "DDHD", "DDDD", ".DD."],
    "dark_angry0": ["DD..", "DDHD", "DDDD", ".DD."], "dark_angry1": ["..DD", "DHDD", "DDDD", ".DD."],
    "glow": [".GG.", "GHGG", ".BB."],
    "glow_angry0": ["GG..", "GHGG", ".BBB"], "glow_angry1": ["..GG", "GGHG", "BBB."],
    "half": ["LLLL", "DDHD", ".DD."], "arc": [".DD.", "D..D"], "wink": [".DD.", "D..D"], "star": [".G.", "GHG", ".G."]}
def eye_cells(kind, side):
    p = EYEPAT.get(kind) or EYEPAT[kind + str(side)]
    off = 1 if kind in ("glow", "glow_angry", "half", "arc", "wink") else 0
    if kind == "star": return [(dx + 1, dy + 1) for dy, r in enumerate(p) for dx, ch in enumerate(r) if ch != "."]
    return [(dx, dy + off) for dy, r in enumerate(p) for dx, ch in enumerate(r) if ch != "."]
MOUTH_PAT = {4: [(0, 0), (3, 0), (1, 1), (2, 1)], 3: [(0, 0), (2, 0), (1, 1)], 2: [(1, 1), (2, 1)], 1: [(1, 1)]}

def _mode(cols):
    if not cols: return None
    v, c = np.unique(np.array(cols), axis=0, return_counts=True); return tuple(int(t) for t in v[np.argmax(c)])
def _ring_skin(img, xs, ys, excl):
    ring = []
    for y in range(min(ys) - 1, max(ys) + 2):
        for x in range(min(xs) - 1, max(xs) + 2):
            if (x, y) in excl or not (0 <= x < img.shape[1] and 0 <= y < img.shape[0]): continue
            if img[y, x, 3] == 255: ring.append(tuple(img[y, x, :3]))
    return _mode(ring)
def outline_of(img):
    a = img[..., 3] == 255; p = np.pad(a, 1)
    edge = a & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])
    return _mode([tuple(c) for c in img[edge][:, :3]])

class Rig:
    """一隻寵物嘅『面部＋錨點』資料：base（idle 幀 0）、clean（冇眼冇嘴）、eyes、mouth、anchors。"""
    pass

def _finish(r):
    a = r.base[..., 3] == 255; ys, xs = np.nonzero(a)
    r.bbox = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    r.eyes.sort(key=lambda e: e["cx"])
    fx = np.mean([e["cx"] for e in r.eyes]); fy = np.mean([e["cy"] for e in r.eyes])
    A = r.anchors
    A["face"] = [round(fx, 1), round(fy, 1)]
    A["eyeL"] = [r.eyes[0]["cx"], r.eyes[0]["cy"]]; A["eyeR"] = [r.eyes[-1]["cx"], r.eyes[-1]["cy"]]
    A["center"] = [round((r.bbox[0] + r.bbox[2]) / 2, 1), round((r.bbox[1] + r.bbox[3]) / 2, 1)]
    A["chest"] = [round(fx, 1), round(min(r.mouthPt[1] + 4, r.pivot[1] - 3), 1)]
    if "side_r" not in A:
        yy = int(round(fy + 4)); row = np.nonzero(a[yy])[0]
        A["side_r"] = [int(row.max()), yy]; A["side_l"] = [int(row.min()), yy]
    A["pivot"] = list(r.pivot); A["mouth"] = [round(r.mouthPt[0], 1), round(r.mouthPt[1], 1)]
    r.eyeDist = round(A["eyeR"][0] - A["eyeL"][0], 1)
    return r

def rig_new(key):
    T = json.load(open(os.path.join(T48, "tuned.json"))); m = T["creatures"][key]
    strip = rgba(os.path.join(T48, "idle", f"{key}_idle.png")); S = T["size"][0]
    r = Rig(); r.pid = key; r.line = "new"; r.name = m["name"]; r.size = S; r.pivot = tuple(T["pivot"])
    r.base = strip[:, :S].copy(); r.clean = r.base.copy(); r.keep = {}
    r.outline = hexc(m["outline"]); r.series, r.token = series_of(key)
    r.eyes = []; r.anchors = {}
    allcells = set()
    for e in m["eyes"]:
        cells = [(e["x"] + dx, e["y"] + dy) for dx, dy in eye_cells(e["kind"], e["side"])]; allcells |= set(cells)
    for e in m["eyes"]:
        cells = [(e["x"] + dx, e["y"] + dy) for dx, dy in eye_cells(e["kind"], e["side"])]
        skin = _ring_skin(r.base, [c[0] for c in cells], [c[1] for c in cells], allcells)
        pix = {c: tuple(int(t) for t in r.base[c[1], c[0]]) for c in cells}
        for (x, y) in cells: r.clean[y, x, :3] = skin
        xs = [c[0] for c in cells]; ys = [c[1] for c in cells]
        ink = tuple(e["lineC"]) if ("glow" in e["kind"] or e["kind"] == "star") else (34, 26, 44)
        r.eyes.append({"pix": pix, "box": [min(xs), min(ys), max(xs), max(ys)], "cx": (min(xs) + max(xs)) / 2, "cy": (min(ys) + max(ys)) / 2,
                       "ink": ink, "kind": e["kind"], "skin": skin})
    mo = m.get("face", {}).get("mouth")
    r.mouthPix = {}
    if mo:
        sx, my, n = mo; cells = [(sx + dx, my + dy) for dx, dy in MOUTH_PAT[n]]
        skin = _ring_skin(r.base, [c[0] for c in cells], [c[1] for c in cells], set(cells))
        for (x, y) in cells: r.mouthPix[(x, y)] = tuple(int(t) for t in r.base[y, x]); r.clean[y, x, :3] = skin
        r.mouthPt = (sx + 1.5, my + 0.5)
    else:
        bot = max(e["box"][3] for e in r.eyes); r.mouthPt = (np.mean([e["cx"] for e in r.eyes]), bot + 2.5)
    r.mouthInk = (34, 26, 44) if lum(r.eyes[0]["skin"]) > 90 else mix(r.outline, (0, 0, 0), 0.4)
    if lum(r.eyes[0]["skin"]) <= 90: r.mouthInk = mix(r.eyes[0]["ink"], r.eyes[0]["skin"], 0.35) if r.eyes[0]["ink"] != (34, 26, 44) else (20, 14, 26)
    bx, by = m["bulbXY"]; r.anchors["bulb"] = [bx, by]; r.bulbType = m["bulbType"]
    # 頭頂（唔計燈泡／莖）：面中線 ±4 列最高實色
    a = r.base[..., 3] == 255; body = a.copy()
    if m["bulbType"] in ("bulb", "star"):
        R_ = 3 if m["bulbType"] == "bulb" else 4
        body[max(0, by - R_):by + R_ + 1, max(0, bx - R_):bx + R_ + 1] = False
        stem = np.all(r.base[..., :3] == (70, 52, 84), -1); body &= ~stem
    fx = int(round(np.mean([e["cx"] for e in r.eyes])))
    # 頭頂＝面中線 ±5 列入面、連續 3 行 ≥8px 實色（跳過角／火焰尖／月牙／光環等裝飾），再向上收到頭殼邊
    win = body[:, max(0, fx - 5):fx + 6]; ok = win.sum(1) >= 8
    ht = next(y for y in range(S - 3) if ok[y] and ok[y + 1] and ok[y + 2])
    for _ in range(2):
        if ht > 0 and body[ht - 1, fx - 2:fx + 3].sum() >= 4: ht -= 1
    r.anchors["headTop"] = [fx, ht]
    row = np.nonzero(body[min(ht + 3, S - 1)])[0]
    r.headHW = int((row.max() - row.min() + 1) / 2) if len(row) else 10
    r.protect = _bulb_protect(r.base, bx, by, ht, m["bulbType"])
    return _finish(r)

def _bulb_protect(base, bx, by, ht, kind):
    """燈泡／莖像素：戴帽時要喺帽上面重畫（每隻都保留頭頂燈泡）"""
    P = set()
    if kind == "own": return P
    R_ = 3 if kind != "star" else 4
    for y in range(max(0, by - R_), by + R_ + 1):
        for x in range(max(0, bx - R_), min(base.shape[1], bx + R_ + 1)):
            if base[y, x, 3] == 255: P.add((x, y))
    for y in range(by, max(by, ht) + 2):
        for x in (bx - 1, bx, bx + 1):
            if 0 <= x < base.shape[1] and base[y, x, 3] == 255 and tuple(base[y, x, :3]) == (70, 52, 84): P.add((x, y))
    return P

OLD_PIVOT = {"sprout": (16, 29), "radiant": (32, 61), "soft": (32, 61), "lumi": (32, 61)}
def rig_old(form):
    J = json.load(open(os.path.join(ATT, f"{form}.json"))); c = J["clips"]["idle"]; f = c["f"]
    fd = os.path.join(ART, c["frameDir"]); S = J["frameSize"]
    ld = fd.replace("/frames", "/layers")
    if form in ("sprout", "radiant", "soft"): ld = os.path.join(TR, "motion/layers", form)
    r = Rig(); r.pid = form; r.line = "old"; r.name = form; r.size = S
    r.pivot = OLD_PIVOT.get(form, (S // 2, S - 3))
    r.base = rgba(os.path.join(fd, "idle_01.png"))
    nof = os.path.join(ld, "idle_01_noface.png"); fov = os.path.join(ld, "idle_01_faceov.png")
    r.layerSrc = "noface/faceov"
    if os.path.exists(nof): r.clean = rgba(nof); faceov = rgba(fov)
    else: r.clean, faceov = _split_face(r.base, f["eyes"][0], _old_face_anchors(form).get("mouth")); r.layerSrc = "auto-split（冇 idle noface layer）"
    r.outline = outline_of(r.base); r.series, r.token = series_of(form)
    r.eyes = []; r.anchors = {}
    used = set()
    for blob in f["eyes"][0]:
        pts = [(blob[i], blob[i + 1]) for i in range(0, len(blob), 2)]
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        box = [min(xs) - 1, min(ys) - 1, max(xs) + 1, max(ys) + 1]
        pix = {}
        for y in range(box[1], box[3] + 1):
            for x in range(box[0], box[2] + 1):
                if 0 <= x < S and 0 <= y < S and faceov[y, x, 3] == 255: pix[(x, y)] = tuple(int(t) for t in faceov[y, x]); used.add((x, y))
        if not pix: continue
        px_ = [p[0] for p in pix]; py_ = [p[1] for p in pix]
        b2 = [min(px_), min(py_), max(px_), max(py_)]
        dark = min(pix.values(), key=lambda v: lum(v))
        skin = _mode([tuple(r.clean[y, x, :3]) for (x, y) in pix if r.clean[y, x, 3] == 255]) or (200, 200, 200)
        r.eyes.append({"pix": pix, "box": b2, "cx": (b2[0] + b2[2]) / 2, "cy": (b2[1] + b2[3]) / 2, "ink": dark[:3], "kind": "old", "skin": skin})
    FA = _old_face_anchors(form)
    mx, my = FA.get("mouth", [np.mean([e["cx"] for e in r.eyes]), max(e["box"][3] for e in r.eyes) + 3])
    r.mouthPix = {}; r.keep = {}
    ys, xs = np.nonzero(faceov[..., 3] == 255)
    for y, x in zip(ys, xs):
        if (x, y) in used: continue
        if abs(x - mx) <= 3 and abs(y - my) <= 2: r.mouthPix[(x, y)] = tuple(int(t) for t in faceov[y, x])
        else: r.keep[(x, y)] = tuple(int(t) for t in faceov[y, x])          # 腮紅等：保留
    r.mouthPt = (mx, my)
    r.mouthInk = min(r.mouthPix.values(), key=lambda v: lum(v))[:3] if r.mouthPix else (34, 26, 44)
    hd = f["head"][0]; r.anchors["headTop"] = [round(hd[0], 1), round(hd[1], 1)]
    r.anchors["side_r"] = [f["side_r"][0][0], f["side_r"][0][1]]; r.anchors["side_l"] = [f["side_l"][0][0], f["side_l"][0][1]]
    bp = (f.get("bulbPt") or [None])[0] or FA.get("bulb") or [hd[0], hd[1] - 4]
    r.anchors["bulb"] = [bp[0], bp[1]]; r.bulbType = "bulb"
    r.headHW = int(J["ref"]["hw"] * 0.5) + 2
    r.protect = _bulb_protect(r.base, int(bp[0]), int(bp[1]), int(hd[1]), "bulb") if J["slots"]["bulb"].get("topBulb") else set()
    return _finish(r)

def _split_face(base, blobs, mouth):
    """sprout／radiant／soft 冇 idle_01_noface：用 ATTACH 眼 blob＋mouth 錨點自己拆。"""
    clean = base.copy(); fov = np.zeros_like(base); S = base.shape[0]
    zones = []
    for blob in blobs:
        pts = [(blob[i], blob[i + 1]) for i in range(0, len(blob), 2)]
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        zones.append((min(xs) - 1, min(ys) - 1, max(xs) + 1, max(ys) + 1, set(pts)))
    if mouth: zones.append((int(mouth[0]) - 2, int(mouth[1]) - 1, int(mouth[0]) + 2, int(mouth[1]) + 1, set()))
    for (x0, y0, x1, y1, core) in zones:
        cells = [(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1) if 0 <= x < S and 0 <= y < S and base[y, x, 3] == 255]
        ring = [tuple(base[y, x, :3]) for y in range(y0 - 1, y1 + 2) for x in range(x0 - 1, x1 + 2)
                if 0 <= x < S and 0 <= y < S and base[y, x, 3] == 255 and not (x0 <= x <= x1 and y0 <= y <= y1)]
        skin = _mode(ring)
        for (x, y) in cells:
            c = tuple(int(t) for t in base[y, x, :3])
            if (x, y) in core or abs(lum(c) - lum(skin)) > 45:
                fov[y, x] = base[y, x]; clean[y, x, :3] = skin
    return clean, fov

def _old_face_anchors(form):
    p = os.path.join(TR, "evo6", form, f"face_anchors_{form}.json")
    if form == "lumi": p = os.path.join(TR, "lumi/face_anchors_lumi.json")
    if os.path.exists(p): return json.load(open(p))["anchors"]["idle"][0]
    d = json.load(open(os.path.join(TR, "motion/liveliness/face_anchors.json")))
    return d["anchors"][form]["idle"][0]

def rig(pid): return rig_new(pid) if pid in NEW_KEYS else rig_old(pid)
ALL_PETS = OLD_FORMS + NEW_KEYS

# ───────────────────────── 表情（face overlay） ─────────────────────────
BLUSH = (240, 128, 150); BLUSH_D = (212, 84, 118); TONGUE = (236, 104, 128); WHITE = (255, 255, 255)
SWIRL5 = [".DDD.", "D...D", "D.D.D", "D..D.", ".DD.."]
SWIRL3 = ["DDD", "D.D", ".DD"]
def _rot(g, k):
    a = np.array([list(r) for r in g]); a = np.rot90(a, k); return ["".join(r) for r in a]
def _put(img, x, y, c, mask=None):
    x, y = int(x), int(y)
    if 0 <= x < img.shape[1] and 0 <= y < img.shape[0] and (mask is None or mask[y, x]):
        img[y, x] = (*c[:3], 255)

def _draw_eye(img, e, mode, r, side, frame=0, mask=None):
    x0, y0, x1, y1 = e["box"]; w = x1 - x0 + 1; h = y1 - y0 + 1; ink = e["ink"]
    if mode.startswith("open"):
        dx, dy = {"open": (0, 0), "open_up": (0, -1), "open_upr": (1, -1), "open_down": (-1 if side == 0 else 1, 1)}[mode]
        for (x, y), c in e["pix"].items(): _put(img, x + dx, y + dy, c, mask)
        return
    if mode == "closed":                         # ︶
        yb = y0 + int(h * 0.55)
        if w >= 3:
            _put(img, x0, yb, ink, mask); _put(img, x1, yb, ink, mask)
            for x in range(x0 + 1, x1): _put(img, x, yb + 1, ink, mask)
        else:
            for x in range(x0, x1 + 1): _put(img, x, yb + 1, ink, mask)
        return
    if mode == "arc":                            # ^ 舒服瞇眼
        ym = y0 + h // 2
        if w >= 3:
            _put(img, x0, ym + 1, ink, mask); _put(img, x1, ym + 1, ink, mask)
            for x in range(x0 + 1, x1): _put(img, x, ym, ink, mask)
        else:
            _put(img, x0, ym + 1, ink, mask); _put(img, x1, ym, ink, mask) if w == 2 else None; _put(img, x0 + 1, ym + 1, ink, mask)
        return
    if mode == "xx":                             # > <
        ym = int(round(e["cy"])); a = 2 if w >= 4 else 1
        L = [(x0 + i, ym - 1) for i in range(a)] + [(x1 - i, ym) for i in range(a)] + [(x0 + i, ym + 1) for i in range(a)]
        if side == 1: L = [(x0 + x1 - x, y) for x, y in L]
        for x, y in L: _put(img, x, y, ink, mask)
        return
    if mode == "swirl":
        g = SWIRL5 if w >= 4 else SWIRL3; g = _rot(g, frame)
        n = len(g); ox = int(round(e["cx"] - (n - 1) / 2)); oy = int(round(e["cy"] - (n - 1) / 2))
        for j, row in enumerate(g):
            for i, ch in enumerate(row):
                if ch == "D": _put(img, ox + i, oy + j, ink, mask)
        return
    if mode.startswith("lid"):                   # 眼皮落：lid45＝扮醒、lid60＝眼瞓
        frac = 0.45 if mode == "lid45" else 0.6
        cut = y0 + max(1, int(round(h * frac)))
        for (x, y), c in e["pix"].items():
            if y >= cut: _put(img, x, y, c, mask)
        for x in range(x0, x1 + 1): _put(img, x, cut - 1, r.outline if lum(e["skin"]) > 90 else ink, mask)
        return

def _grid(img, g, cx, cy, cmap, mask=None):
    n = len(g[0]); ox = int(round(cx - (n - 1) / 2)); oy = int(round(cy - (len(g) - 1) / 2))
    for j, row in enumerate(g):
        for i, ch in enumerate(row):
            if ch in cmap: _put(img, ox + i, oy + j, cmap[ch], mask)

MOUTHS = {"open_big": ["MMMM", "MRRM", ".MM."], "open_small": [".MM.", "MRRM", ".MM."], "o": [".M.", "M.M", ".M."],
          "smirk": ["...M", "MMM."], "wavy": ["M.M.M", ".M.M."]}
def _mouth(img, r, mode, mask):
    if mode == "orig":
        for (x, y), c in r.mouthPix.items(): _put(img, x, y, c, mask)
        return
    if mode == "none": return
    g = MOUTHS[mode]; cmap = {"M": r.mouthInk, "R": TONGUE}
    _grid(img, g, r.mouthPt[0], r.mouthPt[1] + (0.5 if mode in ("open_big", "open_small", "o") else 0), cmap, mask)

def _blush(img, r, mode, mask):
    for i, e in enumerate(r.eyes):
        x0, y0, x1, y1 = e["box"]; yb = y1 + 2
        xs = range(x0 - 2, x0 + 1) if i == 0 else range(x1, x1 + 3)
        for x in xs:
            _put(img, x, yb, BLUSH, mask)
            if mode == "hatch": _put(img, x, yb - 1 if (x % 2) else yb, BLUSH_D, mask)

# 表情 recipe：(眼, 嘴, 腮)
FACES = {
    "blink":        ("closed", "orig", None),
    "squint":       ("arc", "orig", None),
    "squint_blush": ("arc", "orig", "plus"),
    "laugh_a":      ("xx", "open_big", "plus"),
    "laugh_b":      ("xx", "open_small", "plus"),
    "dizzy_a":      ("swirl0", "wavy", None),
    "dizzy_b":      ("swirl1", "wavy", None),
    "sleepy":       ("lid60", "orig", None),
    "sleep":        ("closed", "none", None),
    "surprised":    ("open_up", "o", None),
    "smug":         ("lid45", "smirk", None),
    "embarrassed":  ("open_down", "wavy", "hatch"),
    "lookup":       ("open_upr", "orig", None),
}
FACE_NOTE = {"blink": "眨眼（戳）", "squint": "^ ^ 舒服瞇眼（長按 loop）", "squint_blush": "瞇眼＋腮紅加深（長按 loop 第 2 格）",
             "laugh_a": "> < 大笑張大口（搔癢）", "laugh_b": "> < 笑（細口）", "dizzy_a": "@ @ 暈（搖機）", "dizzy_b": "@ @ 暈第 2 格（轉 90°）",
             "sleepy": "眼瞓半眼（睇書）", "sleep": "瞓著 ︶ ︶", "surprised": "驚訝：眼上移＋o 口（拉開／照鏡）",
             "smug": "扮醒：半眼＋得意嘴角", "embarrassed": "尷尬：眼望低＋斜線腮紅＋波浪口（呆反應做緊被戳）", "lookup": "望上諗嘢（計數）"}
def body_mask(r):
    return r.base[..., 3] == 255
def face_image(r, name):
    """返 (full image, patch)。patch＝同 base 唔同嘅像素（alpha 255），引擎疊喺 idle 幀 0 上面。"""
    em, mm, bm = FACES[name] if name != "neutral" else ("open", "orig", None)
    img = r.clean.copy(); mask = body_mask(r)
    for (x, y), c in r.keep.items(): _put(img, x, y, c, mask)
    for i, e in enumerate(r.eyes):
        if em.startswith("swirl"): _draw_eye(img, e, "swirl", r, i, int(em[-1]), mask)
        else: _draw_eye(img, e, em, r, i, 0, mask)
    _mouth(img, r, mm, mask)
    if bm: _blush(img, r, bm, mask)
    diff = np.any(img != r.base, -1)
    patch = np.zeros_like(img); patch[diff] = img[diff]; patch[diff, 3] = 255
    return img, patch

# ───────────────────────── 自動上色小精靈（FX） ─────────────────────────
OL = (46, 30, 64)
RAMP = {"Y": ((255, 248, 214), (255, 220, 110), (232, 160, 64)), "B": ((232, 248, 255), (150, 210, 250), (90, 150, 225)),
        "P": ((255, 214, 226), (246, 120, 160), (205, 70, 120)), "Z": ((252, 248, 255), (210, 200, 250), (152, 136, 216)),
        "C": ((255, 252, 240), (242, 234, 216), (206, 194, 182)), "K": ((126, 92, 70), (100, 70, 54), (74, 50, 40)),
        "R": ((236, 104, 96), (198, 66, 74), (150, 44, 60)), "G": ((78, 128, 96), (58, 102, 80), (42, 78, 64)),
        "S": ((196, 190, 214), (160, 152, 184), (122, 114, 150)), "M": ((150, 206, 120), (104, 170, 96), (72, 132, 80)),
        "W": ((255, 255, 255), (238, 244, 255), (200, 214, 240)), "O": ((255, 214, 150), (255, 160, 70), (220, 96, 40)),
        "L": ((206, 236, 255), (160, 206, 246), (118, 164, 222))}
def auto(rows, outline=OL, ramps=RAMP, hi=True, fixed=None, pad=1, edge8=True):
    """char grid → RGBA：每色區按高度三段漸變（上光）、右下 1px 暗邊、左上一粒白高光、1px 閉合外框。"""
    fixed = fixed or {}
    H = len(rows); W = max(len(r) for r in rows)
    g = np.full((H + 2 * pad, W + 2 * pad), ".", dtype="<U1")
    for j, r in enumerate(rows):
        for i, ch in enumerate(r): g[j + pad, i + pad] = ch
    out = np.zeros((*g.shape, 4), np.uint8)
    solid = g != "."
    for ch in set(g.flatten()) - {"."}:
        m = g == ch; ys, xs = np.nonzero(m)
        if ch in fixed:
            out[m] = (*fixed[ch], 255); continue
        if ch not in ramps: continue
        h0, h1 = ys.min(), ys.max(); hiC, midC, shC = ramps[ch]
        for y, x in zip(ys, xs):
            t = (y - h0) / max(1, h1 - h0)
            c = hiC if t < 0.3 else midC if t < 0.72 else shC
            if (x + 1 < g.shape[1] and g[y, x + 1] == ".") or (y + 1 < g.shape[0] and g[y + 1, x] == "."): c = mix(c, shC, 0.6)
            out[y, x] = (*c, 255)
        if hi:
            k = np.argmin(ys * 100 + xs); y, x = ys[k], xs[k]
            if m[y, x] and len(ys) > 3:
                yy, xx = (y + 1, x + 1) if (y + 1 < g.shape[0] and x + 1 < g.shape[1] and m[y + 1, x + 1]) else (y, x)
                out[yy, xx] = (255, 255, 255, 255)
    if outline is not None:
        p = np.pad(solid, 1)
        nb = p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
        if edge8: nb |= p[:-2, :-2] | p[:-2, 2:] | p[2:, :-2] | p[2:, 2:]
        ring = nb & ~solid; out[ring] = (*outline, 255)
    return out
def flipx(a): return a[:, ::-1].copy()
def canvas(w, h): return np.zeros((h, w, 4), np.uint8)
def paste(dst, src, x, y):
    """alpha 0/255 硬貼"""
    h, w = src.shape[:2]; x, y = int(x), int(y)
    X0, Y0 = max(0, x), max(0, y); X1, Y1 = min(dst.shape[1], x + w), min(dst.shape[0], y + h)
    if X1 <= X0 or Y1 <= Y0: return
    s = src[Y0 - y:Y1 - y, X0 - x:X1 - x]; m = s[..., 3] == 255
    d = dst[Y0:Y1, X0:X1]; d[m] = s[m]

# ───────────────────────── 通用 FX 疊層（兩條線共用） ─────────────────────────
DIG = {"0": ["###", "#.#", "#.#", "#.#", "###"], "1": [".#.", "##.", ".#.", ".#.", "###"], "2": ["###", "..#", "###", "#..", "###"],
       "3": ["###", "..#", ".##", "..#", "###"], "4": ["#.#", "#.#", "###", "..#", "..#"], "5": ["###", "#..", "###", "..#", "###"],
       "6": ["###", "#..", "###", "#.#", "###"], "7": ["###", "..#", ".#.", ".#.", ".#."], "8": ["###", "#.#", "###", "#.#", "###"],
       "9": ["###", "#.#", "###", "..#", "###"], "+": ["...", ".#.", "###", ".#.", "..."], "=": ["...", "###", "...", "###", "..."]}
def _c(rows, ch): return [r.replace("#", ch) for r in rows]
def _shift(a, dx, dy, W=None, H=None):
    H = H or a.shape[0] + abs(dy); W = W or a.shape[1] + abs(dx); o = canvas(W, H); paste(o, a, max(0, dx), max(0, dy)); return o
def _pad_to(frames):
    W = max(f.shape[1] for f in frames); H = max(f.shape[0] for f in frames); out = []
    for f in frames:
        o = canvas(W, H); paste(o, f, (W - f.shape[1]) // 2, H - f.shape[0]); out.append(o)
    return out
def sparkle(n):
    Y1, Y2, W_ = (255, 236, 150), (255, 250, 220), (255, 255, 255)
    g = {0: ["..#..", ".#W#.", "..#.."], 1: ["...#...", "...#...", "..#W#..", "##WWW##", "..#W#..", "...#...", "...#..."], 2: ["#...#", ".#.#.", "..W..", ".#.#.", "#...#"]}[n]
    return auto(g, outline=None, fixed={"#": Y1, "W": W_}, pad=0)

def build_fx():
    """返 {id: {"frames":[np RGBA], "pivot":[x,y], "note":..}}；pivot＝落點（貼去錨點嗰點）"""
    F = {}
    q = auto(_c([".###.", "##.##", "...##", "..##.", "..#..", ".....", "..#.."], "Y"))
    F["fx_question"] = {"frames": [q], "pivot": [q.shape[1] // 2, q.shape[0] - 1], "note": "問號（計數計唔掂）；彈出用 move"}
    ex = auto(_c(["##", "##", "##", "##", "..", "##"], "Y"))
    F["fx_exclaim"] = {"frames": [ex], "pivot": [ex.shape[1] // 2, ex.shape[0] - 1], "note": "感嘆號（照鏡嚇親）"}
    sw = auto(_c(["..#..", ".###.", "#####", "#####", ".###."], "B"), outline=(40, 60, 120))
    sw2 = auto(_c([".#.", "###", "###", ".#."], "B"), outline=(40, 60, 120))
    F["fx_sweat"] = {"frames": _pad_to([sw, sw2]), "pivot": [3, 0], "note": "汗滴：幀0 大、幀1 細（向下滑用 move）"}
    tr = auto(_c([".#.", "###", ".#."], "B"), outline=(40, 60, 120))
    F["fx_tear"] = {"frames": _pad_to([tr, _shift(tr, 0, 1)]), "pivot": [2, 0], "note": "笑出眼淚（眼角）"}
    zb = auto(_c(["#####", "...#.", "..#..", ".#...", "#####"], "Z"), outline=(52, 40, 96))
    zs = auto(_c(["####", "..#.", ".#..", "####"], "Z"), outline=(52, 40, 96))
    zz = []
    for k in range(3):
        o = canvas(18, 18)
        if k >= 0: paste(o, zs, 0, 12)
        if k >= 1: paste(o, zs, 5, 7)
        if k >= 2: paste(o, zb, 10, 0)
        zz.append(o)
    F["fx_zzz"] = {"frames": zz, "pivot": [0, 17], "note": "Zzz 3 幀（z → zz → zzZ）loop"}
    hb = auto(_c([".##.##.", "#######", "#######", ".#####.", "..###..", "...#..."], "P"), outline=(90, 30, 60))
    hs = auto(_c([".#.#.", "#####", ".###.", "..#.."], "P"), outline=(90, 30, 60))
    F["fx_heart"] = {"frames": _pad_to([hs, hb]), "pivot": [4, 7], "note": "心心（長按舒服）幀0 細 幀1 大"}
    F["fx_sparkle"] = {"frames": _pad_to([sparkle(0), sparkle(1), sparkle(2)]), "pivot": [3, 3], "note": "閃光（冇外框，柔光由引擎 glow 加）"}
    pk = [auto(_c([".#.", "#.#", ".#."], "C"), outline=OL),
          auto(_c(["..#..", ".....", "#...#", ".....", "..#.."], "C"), outline=OL),
          auto(_c(["...#...", ".......", ".......", "#.....#", ".......", ".......", "...#..."], "C"), outline=OL)]
    pk = [_center_to(f, 11) for f in pk]
    F["fx_poke"] = {"frames": pk, "pivot": [5, 5], "note": "戳點擴散 3 幀（貼喺手指位置 anchor=touch）"}
    ll = auto(_c(["..#", ".#.", "...", "##.", "...", ".#.", "..#"], "C"), outline=OL)
    ll2 = _shift(ll, 1, 0)
    F["fx_laugh_l"] = {"frames": _pad_to([ll, ll2]), "pivot": [ll2.shape[1] - 1, 4], "note": "笑紋（身左）"}
    F["fx_laugh_r"] = {"frames": [flipx(f) for f in F["fx_laugh_l"]["frames"]], "pivot": [0, 4], "note": "笑紋（身右）"}
    for d, g in DIG.items():
        nm = {"+": "plus", "=": "eq"}.get(d, d)
        a = auto(_c(g, "C"), outline=OL, hi=False)
        F[f"fx_num_{nm}"] = {"frames": [a], "pivot": [a.shape[1] // 2, a.shape[0] - 1], "note": f"數字／符號 {d}"}
    F["fx_star_orbit"] = {"frames": orbit_frames("star"), "pivot": [12, 6], "note": "通用轉星（冇系變體時用）"}
    F["fx_puff"] = {"frames": puff_frames("dust"), "pivot": [8, 9], "note": "通用撞／落地煙（冇系變體時用）"}
    # 書：打開／揭頁／合埋（瞓著跌低）
    book_open = auto(["PPPPPP..PPPPPP", "PLLLLP..PLLLLP", "PPPPPP..PPPPPP", "PLLLPP..PLLLLP", "PPPPPP..PPPPPP", "CCCCCCSSCCCCCC"],
                     outline=(74, 40, 52), fixed={"P": (250, 244, 228), "L": (170, 160, 190), "C": (198, 66, 74), "S": (150, 44, 60)}, hi=False)
    book_open[1:-1, 7:9] = 0; book_open[1:-2, 7] = (*(74, 40, 52), 255); book_open[1:-2, 8] = (*(74, 40, 52), 255)
    book_flip = book_open.copy(); flip_pg = auto(["P", "P", "P", "P", "P"], outline=(74, 40, 52), fixed={"P": (255, 252, 240)}, hi=False)
    bf = canvas(book_open.shape[1], book_open.shape[0] + 3); paste(bf, book_open, 0, 3); paste(bf, flip_pg, 7, 0)
    bo = canvas(book_open.shape[1], book_open.shape[0] + 3); paste(bo, book_open, 0, 3)
    book_shut = auto(["CCCCCCCCCCCC", "CYYYYYYYYYYC", "CCCCCCCCCCCC", "PPPPPPPPPPPP"], outline=(74, 40, 52),
                     fixed={"C": (198, 66, 74), "Y": (255, 214, 110), "P": (250, 244, 228)}, hi=False)
    bs = canvas(book_open.shape[1], book_open.shape[0] + 3); paste(bs, book_shut, 1, bo.shape[0] - book_shut.shape[0])
    F["fx_book"] = {"frames": [bo, bf, bs], "pivot": [bo.shape[1] // 2, bo.shape[0] - 1], "note": "書：0 打開、1 揭頁、2 合埋跌低（瞓著）"}
    # 教鞭
    pu = canvas(12, 12); pd = canvas(12, 12)
    for i in range(10):
        x, y = 1 + i, 10 - i; paste(pu, auto(["K"], outline=None, fixed={"K": (126, 92, 70)}, pad=0), x, y)
        x2, y2 = 1 + i, 9 - int(i * 0.35); paste(pd, auto(["K"], outline=None, fixed={"K": (126, 92, 70)}, pad=0), x2, y2)
    for a_, (x, y) in ((pu, (10, 1)), (pd, (10, 6))):
        a_[y, x] = (255, 252, 240, 255); a_[y - 1:y + 1, x - 1:x + 1][a_[y - 1:y + 1, x - 1:x + 1, 3] == 0] = (*OL, 255)
    F["fx_pointer"] = _outline_frames({"frames": [pu, pd], "pivot": [1, 10], "note": "教鞭：0 舉高、1 敲落（握點＝左下）"})
    # 黑板（扮教授）：0 空、1「1+1」、2「1+1=3」＋雲仔
    F["fx_board"] = {"frames": board_frames(), "pivot": [12, 21], "note": "細黑板（腳點＝底中）"}
    # 牆（撞牆）
    F["fx_wall"] = {"frames": [wall()], "pivot": [0, 33], "note": "花園石牆一截（pivot＝左下，左邊緣＝撞點）"}
    mb, mf, mask = mirror()
    F["fx_mirror_back"] = {"frames": [mb], "pivot": [mb.shape[1] // 2, mb.shape[0] - 1], "note": "企身鏡（底層：框＋玻璃）"}
    F["fx_mirror_front"] = {"frames": mf, "pivot": [mb.shape[1] // 2, mb.shape[0] - 1], "note": "鏡面反光（頂層：0 普通、1 閃）"}
    F["_mirror_mask"] = mask
    return F

def _center_to(a, n):
    o = canvas(n, n); paste(o, a, (n - a.shape[1]) // 2, (n - a.shape[0]) // 2); return o
def _outline_frames(d):
    out = []
    for f in d["frames"]:
        a = f[..., 3] == 255; p = np.pad(a, 1); nb = p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
        g = f.copy(); g[nb & ~a] = (*OL, 255); out.append(g)
    d["frames"] = out; return d

def board_frames():
    W, H = 25, 22; base = canvas(W, H)
    wood = (126, 92, 70); wood_d = (90, 62, 48); green = (52, 92, 78); green_d = (40, 74, 64)
    for y in range(0, 16):
        for x in range(0, W):
            edge = y in (0, 15) or x in (0, W - 1)
            base[y, x] = (*(OL if edge else wood if (y in (1, 14) or x in (1, W - 2)) else (green if y < 9 else green_d)), 255)
    for x, yy in ((4, range(16, 22)), (W - 5, range(16, 22))):
        for y in yy: base[y, x] = (*wood_d, 255); base[y, x - 1] = (*OL, 255); base[y, x + 1] = (*OL, 255)
    base[2, 2] = (255, 255, 255, 255)
    chalk = (236, 240, 230)
    def txt(img, s, x, y):
        for ch in s:
            for j, r in enumerate(DIG[ch]):
                for i, c in enumerate(r):
                    if c == "#": img[y + j, x + i] = (*chalk, 255)
            x += 4
    f1 = base.copy(); txt(f1, "1+1", 3, 3)
    f2 = f1.copy(); txt(f2, "=3", 15, 3)
    for (x, y) in ((5, 11), (6, 10), (7, 10), (8, 11), (9, 10), (10, 10), (11, 11), (5, 12), (6, 12), (7, 12), (8, 12), (9, 12), (10, 12), (11, 12)):
        f2[y, x] = (*chalk, 255)                                     # 雲（＝棉花糖，扮教授講錯嘢）
    for (x, y) in ((15, 11), (16, 10), (17, 11), (16, 12), (18, 11), (19, 11)):   # 箭嘴 → 
        f2[y, x] = (*chalk, 255)
    for (x, y) in ((21, 10), (21, 11), (21, 12), (22, 10), (22, 12)):   # 糖（棒棒糖頭）
        f2[y, x] = (255, 190, 210, 255)
    return [base, f1, f2]

def wall():
    W, H = 10, 34; o = canvas(W, H)
    st = ((196, 190, 214), (160, 152, 184), (122, 114, 150)); mort = (92, 84, 120)
    for y in range(H):
        for x in range(W):
            if x in (0, W - 1) or y == 0: o[y, x] = (*OL, 255); continue
            row = (y - 3) // 5; off = 0 if row % 2 == 0 else 4
            if y >= 3 and ((y - 3) % 5 == 0 or (x + off) % 8 == 0): o[y, x] = (*mort, 255); continue
            t = ((y - 3) % 5) / 4 if y >= 3 else 0
            o[y, x] = (*(st[0] if t < .3 else st[1] if t < .75 else st[2]), 255)
    for x in range(1, W - 1):                                      # 頂面青苔
        o[1, x] = (150, 206, 120, 255); o[2, x] = (104, 170, 96, 255) if x % 3 else (72, 132, 80, 255)
    for x in (2, 5, 7): o[0, x] = (104, 170, 96, 255)
    o[1, 1] = (255, 255, 255, 255)
    return o

def mirror():
    W, H = 19, 31; o = canvas(W, H); mask = np.zeros((H, W), bool)
    gold = ((255, 232, 150), (232, 184, 84), (176, 124, 52)); glass = ((214, 236, 255), (176, 210, 246), (140, 178, 232))
    cx, cy, rx, ry = 9, 11, 8, 10.5
    for y in range(H):
        for x in range(W):
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if d <= 1.0:
                inner = ((x - cx) / (rx - 2)) ** 2 + ((y - cy) / (ry - 2)) ** 2
                if inner <= 1.0:
                    t = y / 22; o[y, x] = (*(glass[0] if t < .3 else glass[1] if t < .7 else glass[2]), 255); mask[y, x] = True
                else:
                    t = 0 if (x < cx and y < cy) else 1 if (x < cx or y < cy) else 2; o[y, x] = (*gold[t], 255)
    for y in range(22, 28):
        for x in (8, 9, 10): o[y, x] = (*gold[1 if x < 10 else 2], 255)
    for x in range(4, 15): o[28, x] = (*gold[1], 255); o[29, x] = (*gold[2], 255)
    a = o[..., 3] == 255; p = np.pad(a, 1)
    nb = p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:] | p[:-2, :-2] | p[:-2, 2:] | p[2:, :-2] | p[2:, 2:]
    o[nb & ~a] = (*OL, 255)
    f0 = canvas(W, H); f1 = canvas(W, H)
    for (x, y) in ((5, 5), (6, 4), (5, 6)): f0[y, x] = (255, 255, 255, 255)
    for (x, y) in ((5, 5), (6, 4), (5, 6), (7, 3), (4, 7), (12, 14), (13, 13)): f1[y, x] = (255, 255, 255, 255)
    return o, [f0, f1], mask

# ───────────────────────── 每系自訂幀（轉圈 token＋煙） ─────────────────────────
TOKENS = {
    "drop": (["..#..", ".###.", "#####", ".###."], "B", (40, 60, 120)),
    "bubble": ([".##.", "#WW#", "#W.#", ".##."], None, (60, 96, 150)),
    "ember": (["..#.", ".##.", "####", ".##."], "O", (110, 40, 30)),
    "pebble": ([".##.", "####", "####"], "S", (60, 50, 70)),
    "flame": ([".#..", ".##.", "####", ".##."], "R", (100, 30, 40)),
    "star": (["..#..", ".###.", "#####", ".#.#."], "Y", (110, 70, 30)),
    "star_blue": (["..#..", ".###.", "#####", ".#.#."], "L", (36, 56, 120)),
    "crescent": ([".##", "##.", "##.", ".##"], "Y", (110, 70, 30)),
    "spore": ([".##.", "####", ".##."], "M", (40, 80, 50)),
    "shard": (["..#", ".##", "###", ".#."], "L", (40, 60, 120)),
    "fluff": ([".##.", "####", "####", ".##."], "C", (130, 120, 150)),
    "mote": (["##", "##"], "S", (70, 60, 90)),
    "firefly": ([".#.", "###", ".#."], "Y", (90, 110, 40)),
    "leaf": (["..##", ".###", "###.", "#..."], "M", (40, 80, 50)),
}
def token(name, back=False):
    g, ramp, ol = TOKENS[name]
    if ramp is None: a = auto(g, outline=ol, fixed={"#": (150, 214, 250), "W": (255, 255, 255)}, hi=False)
    else: a = auto(_c(g, ramp), outline=ol)
    if back:                                                         # 後面嗰粒：每色降一級（最多加 1 色，保 ≤12 色）
        m = a[..., 3] == 255; ol_ = np.array(ol)
        cols = sorted({tuple(int(v) for v in c) for c in a[m][:, :3] if tuple(c) != tuple(ol)}, key=lum)
        lut = {c: (cols[i - 1] if i > 0 else tuple(int(v * 0.72) for v in c)) for i, c in enumerate(cols)}
        b = a.copy()
        for y, x in zip(*np.nonzero(m)):
            c = tuple(int(v) for v in a[y, x, :3])
            if c in lut: b[y, x, :3] = lut[c]
        a = b
    return a
def orbit_frames(name, n=8, rx=9, ry=3):
    out = []
    for k in range(n):
        o = canvas(25, 13); pts = []
        for j in range(3):
            th = 2 * math.pi * (k / n + j / 3); pts.append((math.sin(th), int(round(12 + rx * math.cos(th))), int(round(6 + ry * math.sin(th)))))
        for s, x, y in sorted(pts):
            t = token(name, back=s < 0); paste(o, t, x - t.shape[1] // 2, y - t.shape[0] // 2)
        out.append(o)
    return out
PUFF_C = {"dust": ((250, 246, 255), (220, 214, 236), (180, 172, 204), (120, 110, 150))}
def puff_frames(name, accent=None):
    hi, mid, sh, ol = PUFF_C["dust"]
    ramps = dict(RAMP); ramps["Q"] = (hi, mid, sh)
    f0 = auto(["..QQ..", ".QQQQ.", "QQQQQQ"], outline=ol, ramps=ramps)
    f1 = auto(["..QQ...QQ..", ".QQQQ.QQQQ.", "QQQQQQQQQQQ", ".QQQQQQQQQ."], outline=ol, ramps=ramps)
    f2 = auto(["Q.....Q", ".......", "..Q.Q..", "Q.....Q"], outline=ol, ramps=ramps, hi=False)
    fr = _pad_to([f0, f1, f2]); fr = [_center_to_wh(f, 17, 10) for f in fr]
    if accent:
        t = token(accent)
        paste(fr[1], t, 1, 0); paste(fr[1], t, 17 - t.shape[1] - 1, 1); paste(fr[2], t, 7, 0)
        fr = [limit_colors(f, 12) for f in fr]
    return fr
def limit_colors(a, n=12):
    m = a[..., 3] == 255; cols = np.unique(a[m][:, :3], axis=0)
    if len(cols) <= n: return a
    im = Image.fromarray(a[..., :3].copy()); im = np.array(im.quantize(colors=n, method=Image.Quantize.MAXCOVERAGE).convert("RGB"))
    o = a.copy(); o[m, :3] = im[m]; return o
def _center_to_wh(a, w, h):
    o = canvas(w, h); paste(o, a, (w - a.shape[1]) // 2, h - a.shape[0]); return o

# ───────────────────────── 每隻自動「穿戴」patch（眼鏡／四方帽）＋手仔 ─────────────────────────
GL = (52, 40, 72); GL_GOLD = (232, 184, 84)
GL_RIM = (112, 72, 58)
def glasses_patch(r, glint=False):
    """圓角眼鏡圈：每隻自己眼框 ±2（唔黐眼珠）、啡框＋金橋＋鏡腳；glint=True 加反光（幀 1）。返全幀 patch"""
    S, W0 = r.base.shape[:2]; o = np.zeros_like(r.base)
    def P(x, y, c):
        if 0 <= x < W0 and 0 <= y < S: o[y, x] = (*c, 255)
    boxes = [e["box"] for e in r.eyes]
    for (x0, y0, x1, y1) in boxes:
        X0, Y0, X1, Y1 = x0 - 2, y0 - 2, x1 + 2, y1 + 1
        for x in range(X0 + 1, X1): P(x, Y0, GL_RIM); P(x, Y1, GL_RIM)
        for y in range(Y0 + 1, Y1): P(X0, y, GL_RIM); P(X1, y, GL_RIM)
        if glint: P(X1 - 1, Y0 + 1, (255, 255, 255)); P(X1 - 2, Y0 + 1, (255, 255, 255)); P(X1 - 1, Y0 + 2, (220, 236, 255))
    (a0, b0, a1, b1), (c0, d0, c1, d1) = boxes[0], boxes[-1]
    yb = min(b0, d0) - 1
    for x in range(a1 + 3, c0 - 2): P(x, yb, GL_GOLD)
    P(a0 - 3, yb + 1, GL_RIM); P(c1 + 3, yb + 1, GL_RIM)
    return o
def hat_patch(r, tassel=0):
    """四方帽：闊≈頭闊（9–19px）；坐喺 headTop；燈泡／莖位置挖空（燈泡永遠喺帽上面露出）"""
    S = r.base.shape[0]; W0 = r.base.shape[1]; o = np.zeros_like(r.base)
    hx, hy = [int(round(v)) for v in r.anchors["headTop"]]
    w = int(np.clip(round(r.headHW * 1.3), 9, 19)); w += (w % 2 == 0)
    cw = max(5, int(w * 0.55)); cw += (cw % 2 == 0)
    pad = (w - cw) // 2
    rows = ["." + "B" * (w - 2) + ".", "B" * w, "." + "D" * (w - 2) + ".", "." * pad + "C" * cw + "." * pad, "." * pad + "C" * cw + "." * pad]
    a = auto(rows, outline=(30, 24, 40), fixed={"B": (74, 70, 104), "D": (52, 48, 74), "C": (60, 56, 86)}, hi=False)
    a[2, 3] = a[2, 4] = (128, 122, 164, 255)
    H_, W_ = a.shape[:2]; X = hx - W_ // 2; Y = hy + 2 - H_          # 帽底陷入頭頂 1px
    paste(o, a, X, Y)
    G1, G2, G3 = (255, 226, 130), GL_GOLD, (176, 124, 52)
    cy = Y + 2; o[cy, hx] = (*G1, 255)
    ex = X + W_ - 3
    for x in range(hx + 1, ex + 1): o[cy, x] = (*G2, 255)
    sw = 1 if tassel else 0
    for k in range(1, 5):
        y = cy + k; x = ex + (sw if k >= 3 else 0)
        if 0 <= y < S and 0 <= x < W0: o[y, x] = (*(G2 if k < 4 else G3), 255)
    y = cy + 5; x = ex + sw
    if 0 <= y < S:
        for xx in (x - 1, x, x + 1):
            if 0 <= xx < W0: o[y, xx] = (*G3, 255)
    for (x, y) in r.protect: o[y, x] = 0
    return o
def paw_frames(r):
    """手仔 4 幀（拳／1／2／3 隻手指），顏色取自身側皮膚＋自己外框；pivot＝左中（貼 side_r 向內 2px）"""
    sx, sy = [int(round(v)) for v in r.anchors["side_r"]]
    cols = [tuple(r.base[y, x, :3]) for y in range(sy - 2, sy + 3) for x in range(sx - 5, sx - 1)
            if 0 <= x < r.base.shape[1] and 0 <= y < r.base.shape[0] and r.base[y, x, 3] == 255]
    skin = _mode(cols) or (200, 200, 200)
    if lum(skin) < 40: skin = mix(skin, (255, 255, 255), 0.15)
    ramps = dict(RAMP); ramps["H"] = (mix(skin, (255, 255, 255), 0.3), skin, mix(skin, r.outline, 0.35))
    shapes = [[".###.", "#####", "#####", ".###."],
              ["..#..", "..#..", ".###.", "#####", "#####", ".###."],
              [".#.#.", ".#.#.", ".###.", "#####", "#####", ".###."],
              ["#.#.#", "#.#.#", "#####", "#####", "#####", ".###."]]
    fr = _pad_to([auto(_c(s, "H"), outline=r.outline, ramps=ramps) for s in shapes])
    return fr, skin

# ───────────────────────── 參考合成器（= 引擎要做嘅嘢） ─────────────────────────
EASE = {"linear": lambda t: t, "in": lambda t: t * t, "out": lambda t: 1 - (1 - t) ** 2,
        "inout": lambda t: 2 * t * t if t < .5 else 1 - 2 * (1 - t) ** 2,
        "outBack": lambda t: 1 + 2.70158 * (t - 1) ** 3 + 1.70158 * (t - 1) ** 2, "step": lambda t: 0.0}
FIELDS = {"sx": 1.0, "sy": 1.0, "rot": 0.0, "x": 0.0, "y": 0.0, "flip": 0}
def norm_keys(keys):
    out = []; cur = dict(FIELDS)
    for k in keys:
        cur = {**cur, **{f: k[f] for f in FIELDS if f in k}}; out.append({"t": k["t"], "e": k.get("e", "linear"), **cur})
    return out
def body_at(clip, t):
    K = norm_keys(clip["body"])
    if t <= K[0]["t"]: return K[0]
    for a, b in zip(K, K[1:]):
        if a["t"] <= t <= b["t"]:
            u = EASE[b["e"]]((t - a["t"]) / max(1, b["t"] - a["t"]))
            v = {f: a[f] + (b[f] - a[f]) * u for f in ("sx", "sy", "rot", "x", "y")}; v["flip"] = a["flip"]
            if "rotStep" in clip: v["rot"] = round(v["rot"] / clip["rotStep"]) * clip["rotStep"]
            return v
    return K[-1]
def track_at(tr, t):
    """face／wear 軌：[{t, f}] 或 {t, f:[..], ms} 循環"""
    cur = None
    for k in tr:
        if t >= k["t"]: cur = k
    if cur is None: return None
    f = cur["f"]
    if isinstance(f, list): return f[int((t - cur["t"]) // cur.get("ms", 120)) % len(f)]
    return f
def fx_frame(fx, t, nframes):
    if "frames" in fx and isinstance(fx["frames"], list):
        seq = fx["frames"]; i = int((t - fx["t0"]) // fx.get("ms", 100))
        return seq[min(i, len(seq) - 1)] if not fx.get("loop", True) else seq[i % len(seq)]
    i = int((t - fx["t0"]) // fx.get("ms", 100))
    return min(i, nframes - 1) if not fx.get("loop", True) else i % nframes
def fx_move(fx, t):
    mv = fx.get("move"); 
    if not mv: return 0.0, 0.0
    lt = t - fx["t0"]
    if lt <= mv[0][0]: return mv[0][1], mv[0][2]
    for a, b in zip(mv, mv[1:]):
        if a[0] <= lt <= b[0]:
            u = (lt - a[0]) / max(1, b[0] - a[0]); return a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u
    return mv[-1][1], mv[-1][2]

class Comp:
    """合成一隻寵物嘅反應：canvas CW×CH，寵物 pivot 放喺 (PX,PY)。"""
    def __init__(self, r, assets, CW=96, CH=80, PX=48, PY=62):
        self.r, self.A, self.CW, self.CH, self.PX, self.PY = r, assets, CW, CH, PX, PY
        self.faces = {n: face_image(r, n)[1] for n in FACES}
        self.wear = {"glasses": [glasses_patch(r), glasses_patch(r, True)], "hat": [hat_patch(r, 0), hat_patch(r, 1)]}
        self.paw = paw_frames(r)[0]
    def anchor(self, name, touch=None):
        if name == "touch": return touch or [self.r.anchors["face"][0] + 6, self.r.anchors["face"][1] - 2]
        return self.r.anchors[name]
    def src_at(self, clip, t):
        img = self.r.base.copy()
        f = track_at(clip.get("face", []), t)
        if f: m = self.faces[f][..., 3] == 255; img[m] = self.faces[f][m]
        for w in clip.get("wear", []):
            if w["t0"] <= t < w["t1"]:
                i = track_at(w.get("frames", [{"t": 0, "f": 0}]), t - w["t0"]) or 0
                P = self.wear[w["id"]][i]; m = P[..., 3] == 255; img[m] = P[m]
        return img
    def fwd(self, clip, B, pt):
        """src 座標點 → canvas 座標（同身體一樣變形）"""
        O = self.anchor(clip.get("origin", "pivot")); pv = self.r.pivot
        dx, dy = pt[0] - O[0], pt[1] - O[1]
        if B["flip"]: dx = -dx
        dx *= B["sx"]; dy *= B["sy"]; a = math.radians(B["rot"])
        rx, ry = dx * math.cos(a) - dy * math.sin(a), dx * math.sin(a) + dy * math.cos(a)
        return self.PX + (O[0] - pv[0]) + B["x"] + rx, self.PY + (O[1] - pv[1]) + B["y"] + ry
    def body_layer(self, clip, t, src=None):
        B = body_at(clip, t); src = self.src_at(clip, t) if src is None else src
        O = self.anchor(clip.get("origin", "pivot")); pv = self.r.pivot
        ox = self.PX + (O[0] - pv[0]) + B["x"]; oy = self.PY + (O[1] - pv[1]) + B["y"]
        Y, X = np.mgrid[0:self.CH, 0:self.CW].astype(float)
        vx, vy = X + .5 - ox - .5, Y + .5 - oy - .5          # 像素中心（O 本身係像素格）
        a = -math.radians(B["rot"]); ux = vx * math.cos(a) - vy * math.sin(a); uy = vx * math.sin(a) + vy * math.cos(a)
        ux /= B["sx"]; uy /= B["sy"]
        if B["flip"]: ux = -ux
        sxp = np.floor(O[0] + ux + .5).astype(int); syp = np.floor(O[1] + uy + .5).astype(int)
        H, W = src.shape[:2]; ok = (sxp >= 0) & (sxp < W) & (syp >= 0) & (syp < H)
        lay = np.zeros((self.CH, self.CW, 4), np.uint8); lay[ok] = src[syp[ok], sxp[ok]]
        gshift = 0
        if clip.get("groundLock"):
            rows = np.nonzero((lay[..., 3] == 255).any(1))[0]
            if len(rows): gshift = (self.PY + 1) - rows.max(); lay = np.roll(lay, gshift, 0)
        return lay, B, gshift
    def render(self, clip, t, touch=None):
        lay, B, gs = self.body_layer(clip, t)
        back = canvas(self.CW, self.CH); front = canvas(self.CW, self.CH)
        for fx in clip.get("fx", []):
            if not (fx["t0"] <= t < fx["t1"]): continue
            fid = fx["id"]
            if fid == "series_orbit": frames, piv = self.A["series"][self.r.series]["orbit"], [12, 6]
            elif fid == "series_puff": frames, piv = self.A["series"][self.r.series]["puff"], [8, 9]
            elif fid == "paw": frames, piv = self.paw, [0, self.paw[0].shape[0] // 2]
            else: frames, piv = self.A["fx"][fid]["frames"], self.A["fx"][fid]["pivot"]
            i = fx_frame(fx, t, len(frames)); img = frames[i]
            if fx.get("mirrorX"): img = flipx(img); piv = [img.shape[1] - 1 - piv[0], piv[1]]
            ap = self.anchor(fx["anchor"], touch)
            if fx.get("follow", True): cx, cy = self.fwd(clip, B, ap); cy += gs
            else: cx, cy = self.PX + ap[0] - self.r.pivot[0], self.PY + ap[1] - self.r.pivot[1]
            if fx.get("atGround"): cy = self.PY
            mx, my = fx_move(fx, t)
            x = int(round(cx + fx.get("dx", 0) + mx - piv[0])); y = int(round(cy + fx.get("dy", 0) + my - piv[1]))
            if fid == "fx_mirror_back":
                paste(back, img, x, y); self._reflect(back, clip, t, x, y)
                continue
            paste(front if fx.get("z", "front") == "front" else back, img, x, y)
        out = back.copy(); paste(out, lay, 0, 0); paste(out, front, 0, 0)
        return out
    def _reflect(self, dst, clip, t, mx0, my0):
        """鏡入面嘅倒影：寵物（同一個表情）左右反轉、縮 0.5、cut 喺玻璃 mask、冷色調"""
        mask = self.A["fx"]["_mirror_mask"]; src = self.src_at(clip, t)
        a = src[..., 3] == 255; ys, xs = np.nonzero(a); y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
        crop = src[y0:y1 + 1, x0:x1 + 1][:, ::-1]
        im = Image.fromarray(crop); s = 13 / max(crop.shape[:2]) * 1.25
        im = im.resize((max(1, int(crop.shape[1] * s)), max(1, int(crop.shape[0] * s))), Image.NEAREST); rf = np.array(im)
        m = rf[..., 3] == 255; rf[m, :3] = np.clip(rf[m, :3] * np.array([0.8, 0.88, 1.0]) + np.array([20, 26, 40]), 0, 255).astype(np.uint8)
        gx = mx0 + 9 - rf.shape[1] // 2; gy = my0 + 20 - rf.shape[0] + 1
        for j in range(rf.shape[0]):
            for i in range(rf.shape[1]):
                X, Y = gx + i, gy + j; mx_, my_ = X - mx0, Y - my0
                if rf[j, i, 3] == 255 and 0 <= my_ < mask.shape[0] and 0 <= mx_ < mask.shape[1] and mask[my_, mx_] and 0 <= Y < dst.shape[0] and 0 <= X < dst.shape[1]:
                    dst[Y, X] = rf[j, i]
