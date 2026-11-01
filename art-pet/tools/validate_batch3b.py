#!/usr/bin/env python3
"""batch3b 驗證：JSON 引用檔案存在＋尺寸/幀數啱、alpha 只 0/255、每張 ≤12 色（漫畫格／預覽豁免）、
非懸空訪客最低實像素行 = pivot.y+1、冇 _backups。輸出 sprites/batch3b/check/validation.json"""
import json, os, sys
import numpy as np
from PIL import Image
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sprites", "batch3b")
ROOT = os.path.normpath(ROOT)
errs, warn, checked = [], [], set()

def load(rel):
    p = os.path.join(ROOT, rel)
    if not os.path.isfile(p): errs.append(f"缺檔 {rel}"); return None
    return np.array(Image.open(p).convert("RGBA"))

def walk(o, path=""):
    if isinstance(o, dict):
        for key in ("file", "emissive"):
            f = o.get(key)
            if isinstance(f, str) and f.endswith(".png"):
                a = load(f); checked.add(f)
                if a is None: continue
                h, w = a.shape[:2]
                if "frameW" in o and key == "file":
                    n = o.get("frames", 1)
                    if (w, h) != (o["frameW"] * n, o["frameH"]) and (w, h) != (o["frameW"], o["frameH"] * n):
                        errs.append(f"{f}: {w}x{h} ≠ {o['frameW']}x{o['frameH']}×{n}")
                elif "w" in o and "h" in o and key == "file" and (w, h) != (o["w"], o["h"]):
                    errs.append(f"{f}: {w}x{h} ≠ {o['w']}x{o['h']}")
        for k, v in o.items(): walk(v, path + "/" + k)
    elif isinstance(o, list):
        for v in o: walk(v, path)
    elif isinstance(o, str) and o.endswith(".png") and "/" in o and "{" not in o:
        if load(o) is not None: checked.add(o)

data = json.load(open(os.path.join(ROOT, "batch3b.json")))
walk(data)
# 訪客 strip：frames × frameW、pivot 底線
for vid, v in data["visitors"].items():
    W, H = v["frameW"], v["frameH"]
    for cn, c in v["clips"].items():
        a = load(c["file"])
        if a is None: continue
        if a.shape[1] != W * c["frames"] or a.shape[0] != H: errs.append(f"{c['file']} 尺寸 {a.shape[1]}x{a.shape[0]}")
        if not v.get("hover") and cn != "happy":
            for i in range(c["frames"]):
                rows = np.where(a[:, i * W:(i + 1) * W, 3].max(1) > 0)[0]
                if len(rows) and rows.max() != v["pivot"][1] + 1:
                    errs.append(f"{vid}/{cn} 幀{i} 最低實像素行 {rows.max()} ≠ pivot.y+1")
# 全部 png：alpha、色數
pngs = []
for d, _, fs in os.walk(ROOT):
    if "_backups" in d: errs.append(f"有 _backups：{d}")
    for f in fs:
        if f.endswith(".png"): pngs.append(os.path.relpath(os.path.join(d, f), ROOT))
exempt = lambda r: r.startswith(("comics/", "preview/", "check/")) or "overview" in r or r.endswith("_2x.png")
maxc = 0
for r in sorted(pngs):
    if exempt(r): continue
    a = np.array(Image.open(os.path.join(ROOT, r)).convert("RGBA"))
    al = set(np.unique(a[..., 3]).tolist())
    if not al <= {0, 255}: errs.append(f"{r}: alpha 有半透明 {sorted(al - {0, 255})[:5]}")
    n = len(np.unique(a[a[..., 3] > 0][:, :3], axis=0))
    maxc = max(maxc, n)
    if n > 12: errs.append(f"{r}: {n} 色 > 12")
    if r not in checked and not r.endswith("_emissive.png"): warn.append(f"JSON 冇引用：{r}")
# 漫畫：60 張 92×84
cp = [r for r in pngs if r.startswith("comics/")]
for r in cp:
    a = Image.open(os.path.join(ROOT, r))
    if a.size != (92, 84): errs.append(f"{r}: {a.size} ≠ 92x84")
if len(cp) != 60: errs.append(f"漫畫格 {len(cp)} ≠ 60")
cards = [r for r in pngs if r.startswith("cards/")]
if len(cards) != 10: errs.append(f"名片 {len(cards)} ≠ 10（9 路線＋base）")
res = {"ok": not errs, "pngTotal": len(pngs), "jsonReferenced": len(checked), "maxColorsNonComic": maxc,
       "comicPanels": len(cp), "cards": len(cards), "errors": errs, "warnings": warn}
os.makedirs(os.path.join(ROOT, "check"), exist_ok=True)
json.dump(res, open(os.path.join(ROOT, "check", "validation.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in res.items() if k not in ("warnings",)}, ensure_ascii=False, indent=1)); print("warnings:", len(warn), warn[:8])
sys.exit(0 if not errs else 1)
