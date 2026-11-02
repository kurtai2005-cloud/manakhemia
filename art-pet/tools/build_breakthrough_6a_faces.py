#!/usr/bin/env python3
"""6a 團絨記得你：表情疊層 2 款（得意 smug、委屈 pout）。
沿用 3a reactions_lib 嘅 rig（眼 blob／嘴錨點／clean 底／keep 腮紅），每隻寵物出一張全幀 patch（同 idle 幀 0 一樣大、同 pivot）。
純 Pillow／numpy 程序繪製，冇 AI 圖；alpha 只得 0／255。重跑：python3 art-pet/tools/build_breakthrough_6a_faces.py"""
import os, sys, json
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reactions_lib as L

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "art/breakthrough/6a")
DEFAULT = "evo_still_radiant"
TEAR_L = (206, 236, 255); TEAR = (150, 210, 250); TEAR_D = (90, 150, 225)
STAR_Y = (255, 226, 120); WHITE = (255, 255, 255)
put = L._put

def _ink(r, e):
    return e["ink"] if L.lum(e["skin"]) <= 90 else r.mouthInk

def eye_smug(img, r, e, side, mask):
    """半眼得意：眼皮落 50%（用墨色），外眼角向上翹 1px（貓眼 flick）"""
    x0, y0, x1, y1 = e["box"]; h = y1 - y0 + 1
    cut = y0 + max(1, int(round(h * 0.5)))
    ink = _ink(r, e)
    for (x, y), c in e["pix"].items():
        if y >= cut: put(img, x, y, c, mask)
    for x in range(x0, x1 + 1): put(img, x, cut - 1, ink, mask)
    ox = x0 - 1 if side == 0 else x1 + 1
    put(img, ox, cut - 2, ink, mask)
    # 半眼都留一粒光（左上光源）：可見瞳孔最頂一行、左起第 2 粒
    dark = sorted(p for p, c in e["pix"].items() if p[1] == cut and L.lum(c[:3]) < 110)
    if len(dark) >= 3 and L.lum(e["skin"]) > 90: put(img, dark[1][0], cut, WHITE, mask)

def eye_pout(img, r, e, side, mask):
    """委屈：原眼＋眼底一行淚光（淺藍）＋多一粒白高光＋眉尾向內翹（擔心眉）"""
    x0, y0, x1, y1 = e["box"]; w = x1 - x0 + 1
    for (x, y), c in e["pix"].items(): put(img, x, y, c, mask)
    # 眼底淚光：最低一行實色眼像素改淺藍（留外框）
    dark = [p for p, c in e["pix"].items() if L.lum(c[:3]) < 110]
    if dark:
        by = max(p[1] for p in dark)
        row = sorted(p[0] for p in dark if p[1] == by)
        for x in row[1:-1] if len(row) > 2 else row: put(img, x, by, TEAR, mask)
        # 第二粒白高光（右下）
        hy = by - 1; hx = max(p[0] for p in dark if p[1] == hy) if any(p[1] == hy for p in dark) else None
        if hx is not None and w >= 3: put(img, hx - (1 if w >= 4 else 0), hy, WHITE, mask)
    # 擔心眉：內高外低 2px，喺眼框上 2 行
    ink = _ink(r, e)
    if side == 0: pts = [(x1 - 1, y0 - 2), (x1, y0 - 3)] if w >= 3 else [(x1, y0 - 2)]
    else:         pts = [(x0 + 1, y0 - 2), (x0, y0 - 3)] if w >= 3 else [(x0, y0 - 2)]
    if w >= 4:
        pts.append((x1 - 2, y0 - 2) if side == 0 else (x0 + 2, y0 - 2))
    for x, y in pts: put(img, x, y, ink, mask)

def mouth_grid(img, r, g, mask, dy=0, cmap=None):
    L._grid(img, g, r.mouthPt[0], r.mouthPt[1] + dy, cmap or {"M": r.mouthInk}, mask)

def blush_line(img, r, i, e, mask, extra=0):
    x0, y0, x1, y1 = e["box"]; yb = y1 + 2
    xs = range(x0 - 2 - extra, x0 + 1) if i == 0 else range(x1, x1 + 3 + extra)
    for x in xs: put(img, x, yb, L.BLUSH, mask)

def face_smug(r):
    img = r.clean.copy(); mask = L.body_mask(r)
    for (x, y), c in r.keep.items(): put(img, x, y, c, mask)
    for i, e in enumerate(r.eyes): eye_smug(img, r, e, i, mask)
    small = r.eyeDist < 9
    g = ["..M", "MM."] if small else ["....M", "M..M.", ".MM.."]     # 歪咀笑（右邊翹）
    mouth_grid(img, r, g, mask, dy=0 if small else 0.5)
    for i, e in enumerate(r.eyes): blush_line(img, r, i, e, mask)
    # ✦ 小閃星：右眼右上（唔受身體 mask 限）
    e = r.eyes[-1]; sx = e["box"][2] + 3; sy = e["box"][1] - 3
    S = r.base.shape[0]
    sx = min(sx, S - 3); sy = max(sy, 2)
    for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)): put(img, sx + dx, sy + dy, STAR_Y)
    put(img, sx, sy, WHITE)
    return img

def face_pout(r):
    img = r.clean.copy(); mask = L.body_mask(r)
    for (x, y), c in r.keep.items(): put(img, x, y, c, mask)
    for i, e in enumerate(r.eyes): eye_pout(img, r, e, i, mask)
    small = r.eyeDist < 9
    g = [".M.", "M.M"] if small else [".MM.", "M..M"]                # ︵ 扁嘴
    mouth_grid(img, r, g, mask, dy=0.5)
    # 鼓腮：右邊腮 3×2 腮紅＋左上一粒光；左邊照舊一行
    blush_line(img, r, 0, r.eyes[0], mask)
    e = r.eyes[-1]; x1, y1 = e["box"][2], e["box"][3]
    for yy in (y1 + 1, y1 + 2):
        for xx in range(x1, x1 + 3): put(img, xx, yy, L.BLUSH, mask)
    put(img, x1 + 1, y1 + 3, L.BLUSH_D, mask); put(img, x1 + 2, y1 + 3, L.BLUSH_D, mask)
    put(img, x1, y1 + 1, (255, 214, 226), mask)
    # 眼角淚珠（左眼外下）
    e0 = r.eyes[0]; tx = e0["box"][0]; ty = e0["box"][3]
    put(img, tx, ty + 1, TEAR_L, mask); put(img, tx, ty + 2, TEAR, mask)
    # 汗滴：頭右上，身外都畫（淺藍＋深藍邊）
    S = r.base.shape[0]
    hx = int(min(S - 4, e["box"][2] + 4)); hy = int(max(1, e["box"][1] - 6))
    drop = {(1, 0): TEAR_D, (0, 1): TEAR_D, (1, 1): TEAR_L, (2, 1): TEAR_D,
            (0, 2): TEAR_D, (1, 2): TEAR, (2, 2): TEAR_D, (1, 3): TEAR_D}
    for (dx, dy), c in drop.items():
        x, y = hx + dx, hy + dy
        if not (0 <= x < S and 0 <= y < S): continue
        if r.base[y, x, 3] == 255 and not mask[y, x]: continue
        put(img, x, y, c)
    return img

def patch_of(r, img):
    diff = np.any(img != r.base, -1)
    p = np.zeros_like(img); p[diff] = img[diff]; p[diff, 3] = 255
    return p

def ncol(a):
    m = a[..., 3] == 255
    return len({tuple(c) for c in a[m][:, :3]})

def save(a, path, k=1):
    im = Image.fromarray(a, "RGBA")
    if k != 1: im = im.resize((im.width * k, im.height * k), Image.NEAREST)
    im.save(path, optimize=True)

def main():
    os.makedirs(OUT, exist_ok=True)
    J = {"version": 1, "batch": "breakthrough 6a 團絨記得你", "faces": {
            "smug": "得意：半眼（外眼角翹）＋歪咀笑＋腮紅＋✦。用喺『幾日唔見之後第一下撚』",
            "pout": "委屈：淚光眼＋擔心眉＋︵扁嘴＋右邊鼓腮＋眼角淚珠＋汗滴。用喺『3 日（或以上）唔見』"},
         "mode": "全幀 patch（同該形態 idle 幀 0 一樣大、同 pivot），喺 body transform 之前蓋落 base；同 3a faces 一樣嘅疊法",
         "default": DEFAULT, "pets": {}}
    rep = []
    for pid in L.ALL_PETS:
        r = L.rig(pid); d = os.path.join(OUT, "per_pet", pid); os.makedirs(d, exist_ok=True)
        ent = {"frameSize": list(r.base.shape[1::-1]), "pivot": list(r.pivot), "anchors": r.anchors, "line": r.line, "files": {}}
        for name, fn in (("smug", face_smug), ("pout", face_pout)):
            full = fn(r); p = patch_of(r, full)
            save(p, os.path.join(d, f"face_{name}.png")); save(p, os.path.join(d, f"face_{name}@3x.png"), 3)
            ent["files"][name] = {"1x": f"per_pet/{pid}/face_{name}.png", "3x": f"per_pet/{pid}/face_{name}@3x.png",
                                  "patchColors": ncol(p), "patchPx": int((p[..., 3] == 255).sum())}
            rep.append((pid, name, ncol(p), ncol(full)))
            if pid == DEFAULT:
                save(p, os.path.join(OUT, f"face_{name}.png")); save(p, os.path.join(OUT, f"face_{name}@3x.png"), 3)
        J["pets"][pid] = ent
    json.dump(J, open(os.path.join(OUT, "faces6a.json"), "w"), ensure_ascii=False, indent=1)
    bad = [x for x in rep if x[2] > 12]
    print("pets", len(L.ALL_PETS), "max patch colours", max(x[2] for x in rep), "over12", bad)
    preview()

def preview():
    pets = ["evo_still_radiant", "evo_still_soft", "evo_still_lumi", "evo_still_ember", "evo_guard_tide", "evo_hop",
            "sprout", "radiant", "A1", "B2", "E2", "H3"]
    K = 3; CW = 64; cols = 3; BG = (44, 48, 66, 255)
    rows = len(pets)
    sheet = Image.new("RGBA", (cols * 2 * CW * K + 8, rows * CW * K // 1 + 8), BG)
    # 每格 64×64（1x），寵物腳底對齊 (32,60)
    from PIL import ImageDraw
    dr = ImageDraw.Draw(sheet)
    for j, pid in enumerate(pets):
        r = L.rig(pid)
        for i, kind in enumerate(["neutral", "smug", "pout"]):
            if kind == "neutral": full = r.base.copy()
            else:
                p = np.array(Image.open(os.path.join(OUT, "per_pet", pid, f"face_{kind}.png")))
                full = r.base.copy(); m = p[..., 3] == 255; full[m] = p[m]
            cell = Image.new("RGBA", (CW, CW), (0, 0, 0, 0))
            cell.alpha_composite(Image.fromarray(full), (32 - r.pivot[0], 60 - r.pivot[1]))
            big = cell.resize((CW * K, CW * K), Image.NEAREST)
            x = 4 + i * CW * K; y = 4 + j * CW * K
            dr.rectangle([x, y, x + CW * K - 1, y + CW * K - 1], fill=(58, 64, 86, 255) if (i + j) % 2 else (52, 57, 78, 255))
            sheet.alpha_composite(big, (x, y))
            # 近鏡：面部 24×24 放大 4x 喺右邊
            fx, fy = r.anchors["face"]
            ox = int(round(fx)) - 12 + (32 - r.pivot[0]); oy = int(round(fy)) - 11 + (60 - r.pivot[1])
            crop = cell.crop((ox, oy, ox + 24, oy + 24)).resize((24 * 8, 24 * 8), Image.NEAREST)
            x2 = 4 + (3 + i) * CW * K
            dr.rectangle([x2, y, x2 + CW * K - 1, y + CW * K - 1], fill=(36, 40, 56, 255))
            sheet.alpha_composite(crop, (x2, y))
    sheet.save(os.path.join(OUT, "preview_faces_3x.png"))

if __name__ == "__main__":
    main()
