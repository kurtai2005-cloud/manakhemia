#!/usr/bin/env python3
"""驗 6b 散步美術（art/breakthrough/6b）。python3 art-pet/tools/validate_breakthrough_6b.py"""
import os, sys, json
import numpy as np
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(ROOT, "art/breakthrough/6b")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
res = []
def chk(name, ok, info=""):
    res.append(ok); print(("PASS " if ok else "FAIL ") + name + (f" — {info}" if info else ""))
def rgba(p): return np.array(Image.open(os.path.join(D, p)).convert("RGBA"))
def cols(a): m = a[..., 3] == 255; return {tuple(c) for c in a[m][:, :3]}
def up3(a1, a3): return a3.shape[0] == a1.shape[0] * 3 and np.array_equal(np.repeat(np.repeat(a1, 3, 0), 3, 1), a3)

J = json.load(open(os.path.join(D, "walk6b.json")))
pngs = [os.path.relpath(os.path.join(dp, f), D) for dp, _, fs in os.walk(D) for f in fs if f.endswith(".png")]
chk("1 alpha 只得 0／255（全部 PNG）", all(set(np.unique(rgba(p)[..., 3])) <= {0, 255} for p in pngs), f"{len(pngs)} png")
missing = [v[k] for v in list(J["keys"].values()) + list(J["pets"].values()) for k in ("1x", "3x") if not os.path.exists(os.path.join(D, v[k]))]
chk("2 json 列嘅檔全部存在", not missing, str(missing[:3]))
bg, bg3 = rgba("walk_bg.png"), rgba("walk_bg@3x.png")
chk("3 walk_bg 100×120、@3x 300×360", bg.shape[:2] == (120, 100) and bg3.shape[:2] == (360, 300))
chk("4 walk_bg ≤12 色、全幅不透明", len(cols(bg)) <= 12 and (bg[..., 3] == 255).all(), f"{len(cols(bg))} 色")
chk("5 walk_bg @3x＝1x 最近鄰 ×3", up3(bg, bg3))
NAMES = ["pebble", "maple_leaf", "acorn", "feather", "snail_shell", "clover4", "button", "ribbon"]
chk("6 deco 8 件齊（key 6b:deco_*）", all(f"6b:deco_{n}" in J["keys"] for n in NAMES))
ic = {n: (rgba(f"deco/deco_{n}.png"), rgba(f"deco/deco_{n}@3x.png")) for n in NAMES}
ic["icon_walk"] = (rgba("ic_walk@1x.png"), rgba("ic_walk@3x.png"))
chk("7 icon 16×16＋@3x 48×48＝×3", all(a.shape[:2] == (16, 16) and up3(a, b) for a, b in ic.values()))
chk("8 icon 每件 ≤12 色", all(len(cols(a)) <= 12 for a, _ in ic.values()), str({k: len(cols(a)) for k, (a, _) in ic.items()}))
kit = os.path.join(ROOT, "art-pet/ui/kit_hd2d_v2/icons/ic_expedition@1x.png")
ksz = Image.open(kit).size if os.path.exists(kit) else (16, 16)
chk("9 icon_walk 同 kit rail icon 同尺寸", ic["icon_walk"][0].shape[1::-1] == ksz, f"kit {ksz}")
LINE = (0x24, 0x17, 0x2C)
def lit_ok(a):
    """邊緣光向：貼住外描嘅像素，外描喺左／上嗰啲（受光邊）平均光度要 > 外描喺右／下嗰啲（背光邊）"""
    sol = a[..., 3] == 255; ln = sol & np.all(a[..., :3] == LINE, -1); fill = sol & ~ln
    pad = np.pad(ln | ~sol, 1, constant_values=True)
    upL = pad[:-2, 1:-1] | pad[1:-1, :-2]; dnR = pad[2:, 1:-1] | pad[1:-1, 2:]
    lum = a[..., :3] @ np.array([.299, .587, .114])
    A = fill & upL & ~dnR; B = fill & dnR & ~upL
    return A.any() and B.any() and lum[A].mean() > lum[B].mean()
chk("10 icon 左上受光（受光邊平均光度 > 背光邊）", all(lit_ok(a) for a, _ in ic.values()),
    str([k for k, (a, _) in ic.items() if not lit_ok(a)]))
chk("11 icon 有 #24172C 外描", all(np.all(a[..., :3] == LINE, -1).any() for a, _ in ic.values()))
F6 = json.load(open(os.path.join(ROOT, "art/breakthrough/6a/faces6a.json")))["pets"]
chk("12 49 隻形態同 6a per_pet 一致", sorted(J["pets"]) == sorted(F6) and len(J["pets"]) == 49, f"{len(J['pets'])}")
c = J["clip"]
chk("13 clip 4–6 幀、fps 有設", 4 <= c["frames"] <= 6 and c["fps"] > 0, f"{c['frames']}f @{c['fps']}fps")
import reactions_lib as L
bad = {k: [] for k in ("size", "pivot", "colors", "empty", "static", "ground", "count", "3x")}
for pid, e in J["pets"].items():
    r = L.rig(pid); base = r.base; H, W = base.shape[:2]
    s1, s3 = rgba(e["1x"]), rgba(e["3x"])
    if s1.shape[:2] != (H, W * e["frames"]) or e["frameSize"] != [W, H]: bad["size"].append(pid)
    if e["pivot"] != list(r.pivot) or e["pivot"] != F6[pid]["pivot"]: bad["pivot"].append(pid)
    if not cols(s1) <= cols(base): bad["colors"].append(pid)
    if not up3(s1, s3): bad["3x"].append(pid)
    fr = [s1[:, i * W:(i + 1) * W] for i in range(e["frames"])]
    n0 = int((base[..., 3] == 255).sum())
    if any((f[..., 3] == 255).sum() == 0 for f in fr): bad["empty"].append(pid)
    if len({f.tobytes() for f in fr}) < 3: bad["static"].append(pid)
    gb = np.where((base[..., 3] == 255).any(1))[0].max()
    if not any(np.where((f[..., 3] == 255).any(1))[0].max() == gb for f in fr): bad["ground"].append(pid)
    if any(abs(int((f[..., 3] == 255).sum()) - n0) > 0.12 * n0 for f in fr): bad["count"].append(pid)
chk("14 clip 條大小＝idle 幀×幀數", not bad["size"], str(bad["size"]))
chk("15 clip pivot＝idle／6a pivot", not bad["pivot"], str(bad["pivot"]))
chk("16 clip 冇新色（只用 idle 幀 0 嘅色）", not bad["colors"], str(bad["colors"]))
chk("17 clip @3x＝1x ×3", not bad["3x"], str(bad["3x"]))
chk("18 clip 每幀非空、≥3 款唔同幀", not bad["empty"] and not bad["static"], str(bad["empty"] + bad["static"]))
chk("19 clip 有幀腳踏地（底行＝idle 底行）", not bad["ground"], str(bad["ground"]))
chk("20 clip 冇走樣（每幀像素數 ±12% idle）", not bad["count"], str(bad["count"]))
chk("21 冇 _backups", not any("_backups" in p for p in pngs))
print(f"{sum(res)}/{len(res)} passed")
sys.exit(0 if all(res) else 1)
