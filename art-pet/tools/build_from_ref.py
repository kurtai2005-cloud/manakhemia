#!/usr/bin/env python3
"""build_from_ref — Kurt [pt91u]「直接用佢張圖」：由 Kurt 參考圖第 3–6 行（左右兩欄，8 線 × 3 格 = 24 隻）直接切出做 64px 素材。
步驟：切格 → 估背景（平滑模型）→ 前景／柔光分類 → 去角落小 icon → 全解析度 median-cut 量化（≤48 色／隻）
→ 眾數降採樣到 64×64（地線 y=60、置中）→ 加細燈泡（已有光源嘅隻當燈泡）。
來源：Kurt 自己用 AI 生成嘅圖，擁有權已確認 [pt92u]。用法：python3 build_from_ref.py [all|check]"""
import os, sys, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_species_concept as B
REF = "/cursor/stores/store-cce94a57-d559-4a17-ab80-2559c952f0df/grok-bot/agents/0b1b82b5-13e1-41f0-8002-1cc212757e1b/attachments/01M6AFS04N0ZB2Q3XNFWD1GXN8.jpg"
OUT = os.path.join(B.OUT, "from_ref"); SPD = os.path.join(OUT, "sprites"); PVD = os.path.join(OUT, "preview")
for d in (SPD, PVD): os.makedirs(d, exist_ok=True)
COLS = {"L": [(22, 323), (327, 627), (631, 932)], "R": [(955, 1256), (1259, 1561), (1564, 1865)]}
ROWS = {3: (775, 1084), 4: (1135, 1444), 5: (1494, 1804), 6: (1854, 2164)}
LINES = [("A", 3, "L", ("滴滴", "泡泡鰭", "紋紋鰭")), ("B", 3, "R", ("燈燈滴", "水母咪", "珊瑚角鯨")),
         ("C", 4, "L", ("火仔", "火角獸", "焦焦獸")), ("D", 4, "R", ("熔熔石", "尖尖岩", "火翼仔")),
         ("E", 5, "L", ("紅火糰", "火尾鬼", "熔岩獸")), ("F", 5, "R", ("星星彈", "星耳咪", "月亮糰")),
         ("G", 6, "L", ("夜夜糰", "舉星咪", "月角咪")), ("H", 6, "R", ("月角仔", "環月精", "銀河靈"))]
ALPHAS = (0, 60, 110, 170, 255); OUTS = 64; GROUND = 60
T_BODY = 40.0; T_SOFT = 16.0
CFG = {k + "1": {"icon": (90, 90)} for k in "ABCDEFGH"}
for k, v in {"D1": -9, "D2": -7, "E3": -11, "F3": -13, "G3": -7}.items(): CFG.setdefault(k, {})["bdx"] = v
for k in ("B1", "F1", "G1", "H3"): CFG.setdefault(k, {})["bulb"] = "own"   # 已有光源 = 燈泡   # 每隻微調：{"tb":..., "ts":..., "icon":(x1,y1), "bulb":(x,y) or None/"own", "f":...}

def cell(key):
    for k, row, col, names in LINES:
        if k == key[0]:
            st = int(key[1]); x0, x1 = COLS[col][st - 1]; y0, y1 = ROWS[row]; m = 7; return (x0 + m, y0 + m, x1 - m, y1 - m)
def masked_blur(img, m, r):
    w = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r)); w = np.array(w, float) / 255 + 1e-6
    out = np.zeros_like(img)
    for c in range(3):
        v = Image.fromarray(np.clip(img[..., c] * m, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r)); out[..., c] = np.array(v, float) / w
    return out
def label(m):
    """4 連通標記（純 numpy／BFS）"""
    H, W = m.shape; lab = np.zeros((H, W), int); n = 0
    ys, xs = np.nonzero(m)
    for y, x in zip(ys, xs):
        if lab[y, x]: continue
        n += 1; st = [(y, x)]; lab[y, x] = n
        while st:
            cy, cx = st.pop()
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = cy + dy, cx + dx
                if 0 <= ny < H and 0 <= nx < W and m[ny, nx] and not lab[ny, nx]: lab[ny, nx] = n; st.append((ny, nx))
    return lab, n
def dilate(m, r):
    return np.array(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(2 * r + 1))) > 0
def erode(m, r):
    return np.array(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(2 * r + 1))) > 0

def cutout(key, src):
    cf = CFG.get(key, {}); x0, y0, x1, y1 = cell(key); C = src[y0:y1, x0:x1].astype(float); H, W = C.shape[:2]
    border = np.zeros((H, W), bool); border[:6] = border[-6:] = True; border[:, :6] = border[:, -6:] = True
    med = np.median(C[border], 0); d0 = np.linalg.norm(C - med, axis=2)
    bgm = d0 < 30; lb0, _ = label(bgm); ids = set(np.unique(lb0[border])) - {0}; bgm = np.isin(lb0, list(ids))   # 只取同邊界相連
    icon = cf.get("icon") if key[1] == "1" else None
    if icon: bgm[:icon[1], :icon[0]] = False
    passes = cf.get("passes", 2); res = None
    for ps in range(passes):
        if res is not None:
            bgm = (res[1] == 0) & ~dilate(res[1] > 0, 8)
            if icon: bgm[:icon[1], :icon[0]] = False
        res = seg(C, bgm, icon, cf, H, W, border)
    return res

def seg(C, bgm, icon, cf, H, W, border):
    bg = masked_blur(C, bgm, 22)
    if icon:   # 角落 icon 框：用框內近邊位估框底色
        ix, iy = icon; strip = C[3:iy - 3, 3:9].reshape(-1, 3); boxc = np.median(strip, 0); bg[:iy, :ix] = boxc
    diff = np.linalg.norm(C - bg, axis=2)
    tb = cf.get("tb", T_BODY); ts = cf.get("ts", T_SOFT)
    strong = diff > tb
    strong = erode(dilate(strong, 1), 1)   # 補細縫
    closed = erode(dilate(strong, cf.get("close", 3)), cf.get("close", 3))   # 只用嚟判斷「封閉」
    strong |= closed & (diff > tb * 0.55)
    # 背景：由邊界連通嘅非 closed
    lab, n = label(~closed); edge_ids = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    body = strong.copy()
    for i in range(1, n + 1):
        if i in edge_ids: continue
        hole = lab == i
        if diff[hole].mean() >= 22 or hole.sum() < 6: body |= hole
    body |= closed & ~dilate(np.isin(lab, list(edge_ids)), 0) & (diff > ts)
    # 去 icon：icon 框內嘅元件，如果冇同框外接駁就刪；框線（細長）刪
    lb, nb = label(body)
    keep = np.zeros_like(body)
    for i in range(1, nb + 1):
        comp = lb == i; sz = comp.sum(); ys, xs = np.nonzero(comp)
        if sz < cf.get("minc", 14): continue
        if icon and xs.max() < icon[0] + 12 and ys.max() < icon[1] + 12: continue
        keep |= comp
    body = keep
    if icon:   # 框內剩低嘅：只留同主體大元件相連、且 diff 夠大
        reg = np.zeros_like(body); reg[:icon[1] + 3, :icon[0] + 3] = True
        thin = body & reg & ~dilate(erode(body, 2), 2); body &= ~thin
    # 柔光：近主體、diff 介乎 ts..tb
    near = dilate(body, 9)
    soft = (~body) & near & (diff > ts) & (diff <= tb * 1.3)
    if icon: soft[:icon[1] + 12, :icon[0] + 12] &= dilate(body, 4)[:icon[1] + 12, :icon[0] + 12]
    lev = np.where(diff > tb * 0.85, 170, np.where(diff > (ts + tb) / 2, 110, 60))
    A = np.where(body, 255, np.where(soft, lev, 0))
    a = A[..., None] / 255.0
    col = np.where(a > 0, np.clip(bg + (C - bg) / np.maximum(a, 1e-3), 0, 255), 0)   # 反混合背景
    col = np.where(body[..., None], C, col)
    return col, A, diff

def quantize_body(col, A, n=48):
    bm = A == 255; pts = col[bm].astype(np.uint8)
    if len(pts) == 0: return col
    im = Image.fromarray(pts.reshape(1, -1, 3)); q = im.quantize(colors=n, method=Image.Quantize.MEDIANCUT)
    pal = np.array(q.getpalette()[:n * 3]).reshape(-1, 3); idx = np.array(q).reshape(-1)
    out = col.copy(); out[bm] = pal[idx]; return out, pal

def downsample(col, A, key, f0=300 / 64):
    cf = CFG.get(key, {}); body = A == 255; ys, xs = np.nonzero(body)
    f = cf.get("f", f0)
    bw, bh = (xs.max() - xs.min() + 1), (ys.max() - ys.min() + 1)
    top = 2.0 if cf.get("bulb") == "own" else 10.0   # 加燈泡嘅預留頂位
    need = max(bw / 58.0, bh / (GROUND - top)); f = max(f, need)
    cx = (xs.min() + xs.max() + 1) / 2 + cf.get("dx", 0) * f; by = ys.max() + 1
    out = np.zeros((OUTS, OUTS, 4), np.uint8); Hs, Ws = A.shape
    colk = (col[..., 0].astype(int) << 16) | (col[..., 1].astype(int) << 8) | col[..., 2].astype(int)
    for v in range(OUTS):
        sy0 = by + (v - GROUND) * f; sy1 = sy0 + f
        for u in range(OUTS):
            sx0 = cx + (u - OUTS / 2) * f; sx1 = sx0 + f
            ya, yb, xa, xb = int(round(sy0)), int(round(sy1)), int(round(sx0)), int(round(sx1))
            if yb <= 0 or xb <= 0 or ya >= Hs or xa >= Ws: continue
            ya, xa = max(0, ya), max(0, xa); yb, xb = min(Hs, yb), min(Ws, xb)
            if yb <= ya or xb <= xa: continue
            aa = A[ya:yb, xa:xb]; tot = aa.size; nb = (aa == 255).sum()
            if nb >= 0.42 * tot:
                ks = colk[ya:yb, xa:xb][aa == 255]; vals, cnt = np.unique(ks, return_counts=True)
                # 深色（outline）優先少少：揀 count×(1+暗度加權)
                lum = ((vals >> 16) & 255) * 0.3 + ((vals >> 8) & 255) * 0.59 + (vals & 255) * 0.11
                score = cnt * (1 + 0.6 * (lum < 70)); kk = vals[np.argmax(score)]
                out[v, u] = ((kk >> 16) & 255, (kk >> 8) & 255, kk & 255, 255)
            else:
                sm = aa > 0
                if sm.sum() >= 0.3 * tot:
                    al = np.median(aa[sm]); al = min(ALPHAS[1:4], key=lambda t: abs(t - al))
                    c = col[ya:yb, xa:xb][sm].mean(0); out[v, u] = (*np.clip(c, 0, 255).astype(int), al)
    return out, f

def clean(out):
    """去單點孤立像素、補 1px 洞"""
    a = out[..., 3] == 255; H, W = a.shape
    nbc = sum(np.roll(np.roll(a, dy, 0), dx, 1) for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)))
    iso = a & (nbc == 0); out[iso, 3] = 0
    hole = (~a) & (nbc >= 4)
    for y, x in zip(*np.nonzero(hole)):
        nb = [out[(y + dy) % H, (x + dx) % W, :3] for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))]; out[y, x, :3] = nb[0]; out[y, x, 3] = 255
    return out

def add_bulb(out, x, y):
    """細燈泡（跟參考圖風格：深色調外框、黃芯、白高光、柔光）"""
    OL = (92, 60, 40); C1 = (255, 214, 90); C2 = (255, 244, 190); STEM = (70, 52, 84)
    def put(px, py, c, al=255):
        if 0 <= px < OUTS and 0 <= py < OUTS and (al == 255 or out[py, px, 3] < al): out[py, px] = (*c, al)
    for dy in range(1, 4): put(x, y + 2 + dy - 1, STEM)
    for dx, dy in ((-2, -1), (-2, 0), (-2, 1), (2, -1), (2, 0), (2, 1), (-1, -2), (0, -2), (1, -2), (-1, 2), (0, 2), (1, 2)):
        put(x + dx, y + dy, (255, 224, 112), 60) if False else None
    # 柔光
    for dy in range(-4, 5):
        for dx in range(-4, 5):
            r2 = dx * dx + dy * dy
            if 6 < r2 <= 16: put(x + dx, y + dy, (255, 224, 112), 60)
            elif 3 < r2 <= 6: put(x + dx, y + dy, (255, 224, 112), 110)
    for dx, dy in ((-1, -2), (0, -2), (1, -2), (-2, -1), (2, -1), (-2, 0), (2, 0), (-2, 1), (2, 1), (-1, 2), (0, 2), (1, 2)): put(x + dx, y + dy, OL)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1): put(x + dx, y + dy, C1)
    put(x - 1, y - 1, C2); put(x, y - 1, C2); put(x - 1, y, (255, 255, 255)); put(x + 1, y + 1, (232, 168, 60))

def build_one(key, src):
    col, A, diff = cutout(key, src); qcol, pal = quantize_body(col, A, CFG.get(key, {}).get("ncol", 48))
    out, f = downsample(qcol, A, key); out = clean(out)
    b = CFG.get(key, {}).get("bulb", "auto")
    if b == "auto":
        a = out[..., 3] == 255; ys, xs = np.nonzero(a); bx = int(round((xs.min() + xs.max()) / 2)) + CFG.get(key, {}).get("bdx", 0)
        col_top = np.nonzero(a[:, bx])[0]; yt = col_top.min() if len(col_top) else ys.min()
        b = (int(bx), int(max(5, yt - 5 + CFG.get(key, {}).get("bdy", 0)))); CFG.setdefault(key, {})["bulb_at"] = b
    if isinstance(b, tuple): add_bulb(out, *b)
    return out, f, A
def cut_preview(key, src, A):
    x0, y0, x1, y1 = cell(key); C = src[y0:y1, x0:x1].copy()
    chk = ((np.indices(A.shape).sum(0) // 8) % 2)[..., None] * 30 + 200
    v = np.where((A > 0)[..., None], C, chk).astype(np.uint8); return Image.fromarray(v)

def build(keys=None):
    src = np.array(Image.open(REF).convert("RGB")); IM = {}; meta = {}; used = {}
    for k, row, col, names in LINES:
        for st in (1, 2, 3):
            key = f"{k}{st}"
            if keys and key not in keys: continue
            out, f, A = build_one(key, src); IM[key] = out
            fn = f"{key}_64.png"; Image.fromarray(out).save(os.path.join(SPD, fn))
            for z in (2, 4): Image.fromarray(out).resize((64 * z, 64 * z), Image.NEAREST).save(os.path.join(PVD, f"{key}_64_{z}x.png"))
            cut_preview(key, src, A).save(f"/tmp/fromref_mask_{key}.png")
            nb = len(np.unique(out[out[..., 3] == 255][:, :3], axis=0))
            meta[key] = {"name": names[st - 1], "ref": f"row{row}{col} cell{st}", "srcBox": list(cell(key)), "scale": round(1 / f, 4), "bodyColors": int(nb),
                         "bulb": "own light" if CFG.get(key, {}).get("bulb") == "own" else ("added at " + str(CFG.get(key, {}).get("bulb_at", CFG.get(key, {}).get("bulb")))), "file": f"sprites/{fn}"}
    if keys: return IM
    json.dump({"source": "Kurt 參考圖（Kurt 自己用 AI 生成，擁有權已確認 [pt92u]）", "creatures": meta}, open(os.path.join(OUT, "from_ref.json"), "w"), ensure_ascii=False, indent=1)
    sheets(src, IM); return IM
def sheets(src, IM):
    BGc = (92, 84, 136); BG2 = (100, 92, 146); CAP = (247, 239, 222); f12 = B.font(12); f15 = B.font(15)
    cell_w = 64 * 4 + 16; W = 150 + 3 * cell_w; Ht = 40 + len(LINES) * cell_w
    im = Image.new("RGB", (W, Ht), BGc); d = ImageDraw.Draw(im); d.fontmode = "1"
    d.text((10, 10), "from_ref：Kurt 參考圖直接切出（64px ×4）— 擁有權已確認", font=f15, fill=CAP)
    for i, (k, row, col, names) in enumerate(LINES):
        y = 40 + i * cell_w; d.text((8, y + cell_w // 2 - 10), f"{k} 第{row}行{'左' if col == 'L' else '右'}", font=f15, fill=CAP)
        for st in (1, 2, 3):
            cx = 150 + (st - 1) * cell_w
            if (i + st) % 2: d.rectangle([cx, y, cx + cell_w - 1, y + cell_w - 1], fill=BG2)
            z = Image.fromarray(IM[f"{k}{st}"]).resize((256, 256), Image.NEAREST); im.paste(z, (cx + 8, y + 2), z); d.text((cx + 6, y + cell_w - 16), f"{k}{st} {names[st - 1]}", font=f12, fill=CAP)
    im.save(os.path.join(OUT, "lineup_4x.png"))
    # ref vs cut：每格原圖（縮到 192）＋切出 64×3（深底同淺底各一）
    cw = 192; W = 20 + 3 * (cw * 2 + 24) + 10; rh = 192 + 26; Ht = 44 + len(LINES) * (rh + 8)
    im = Image.new("RGB", (W, Ht), (40, 34, 60)); d = ImageDraw.Draw(im); d.fontmode = "1"
    d.text((12, 12), "ref_vs_cut：左＝Kurt 原圖格（縮放顯示）／右＝切出 64px ×3", font=B.font(16), fill=CAP)
    for i, (k, row, col, names) in enumerate(LINES):
        y = 44 + i * (rh + 8)
        for st in (1, 2, 3):
            key = f"{k}{st}"; x0, y0, x1, y1 = cell(key); rc = Image.fromarray(src[y0:y1, x0:x1]).resize((cw, cw), Image.LANCZOS)
            X = 20 + (st - 1) * (cw * 2 + 24); im.paste(rc, (X, y))
            d.rectangle([X + cw + 4, y, X + 2 * cw + 3, y + cw - 1], fill=(60, 56, 70) if i % 2 else (190, 200, 210))
            z = Image.fromarray(IM[key]).resize((cw, cw), Image.NEAREST); im.paste(z, (X + cw + 4, y), z)
            d.text((X, y + cw + 4), f"{key} {names[st - 1]}", font=f12, fill=CAP)
    im.save(os.path.join(OUT, "ref_vs_cut_3x.png"))
def check():
    E = []
    fs = sorted(f for f in os.listdir(SPD) if f.endswith(".png"))
    for f in fs:
        a = np.array(Image.open(os.path.join(SPD, f)).convert("RGBA"))
        if a.shape[:2] != (64, 64): E.append(f"{f}: size")
        if not np.isin(a[..., 3], ALPHAS).all(): E.append(f"{f}: alpha")
        nb = len(np.unique(a[a[..., 3] == 255][:, :3], axis=0))
        if nb > 48 + 12: E.append(f"{f}: body colours {nb}")
        if a[0, :, 3].any() or a[:, 0, 3].any() or a[:, -1, 3].any(): E.append(f"{f}: 貼邊")
    for e in E: print("ERR", e)
    print(f"from_ref check: {len(E)} errors；{len(fs)} sprites"); return E
if __name__ == "__main__":
    w = sys.argv[1] if len(sys.argv) > 1 else "all"
    if w == "all": build()
    sys.exit(1 if check() else 0)
