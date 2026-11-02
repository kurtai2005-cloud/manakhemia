#!/usr/bin/env python3
"""驗 6c 夢境美術（art/breakthrough/6c）。python3 art-pet/tools/validate_breakthrough_6c.py"""
import os, sys, json
import numpy as np
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(ROOT, "art/breakthrough/6c")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
res = []
def chk(name, ok, info=""):
    res.append(bool(ok)); print(("PASS " if ok else "FAIL ") + name + (f" — {info}" if info else ""))
def rgba(p): return np.array(Image.open(os.path.join(D, p)).convert("RGBA"))
def cols(a): m = a[..., 3] == 255; return {tuple(c) for c in a[m][:, :3]}
def up3(a1, a3): return a3.shape[0] == a1.shape[0] * 3 and np.array_equal(np.repeat(np.repeat(a1, 3, 0), 3, 1), a3)
LINE = (0x24, 0x17, 0x2C)
def lit_ok(a):
    sol = a[..., 3] == 255; ln = sol & np.all(a[..., :3] == LINE, -1); fill = sol & ~ln
    pad = np.pad(ln | ~sol, 1, constant_values=True)
    upL = pad[:-2, 1:-1] | pad[1:-1, :-2]; dnR = pad[2:, 1:-1] | pad[1:-1, 2:]
    lum = a[..., :3] @ np.array([.299, .587, .114])
    A = fill & upL & ~dnR; B = fill & dnR & ~upL
    return A.any() and B.any() and lum[A].mean() > lum[B].mean()
def outlined(a):
    """所有貼住透明（或圖邊）嘅不透明像素都係 #24172C"""
    sol = a[..., 3] == 255; p = np.pad(sol, 1, constant_values=False)
    edge = sol & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])
    return np.all(a[edge][:, :3] == LINE, -1).all()

J = json.load(open(os.path.join(D, "dream6c.json"))); K = J["keys"]
pngs = [os.path.relpath(os.path.join(dp, f), D) for dp, _, fs in os.walk(D) for f in fs if f.endswith(".png") and not os.path.relpath(dp, D).split(os.sep)[0] == "v3"]   # v3/＝第 6 批 V3-A 疊層（真 alpha 光層），由 validate_walkdream_v3.py 驗
chk("1 alpha 只得 0／255（全部 PNG）", all(set(np.unique(rgba(p)[..., 3])) <= {0, 255} for p in pngs), f"{len(pngs)} png")
ents = [v for v in K.values() if "1x" in v] + list(J["pets"].values())
missing = [v[k] for v in ents for k in ("1x", "3x") if not os.path.exists(os.path.join(D, v[k]))]
chk("2 json 列嘅檔全部存在", not missing, str(missing[:3]))
p1 = [p for p in pngs if "@3x" not in p and not p.startswith("preview")]
chk("3 每個 1x 都有 @3x，而且＝最近鄰 ×3", all(os.path.exists(os.path.join(D, p.replace(".png", "@3x.png"))) and up3(rgba(p), rgba(p.replace(".png", "@3x.png"))) for p in p1), f"{len(p1)} 對")
badsz = [k for k, v in K.items() if "1x" in v and list(rgba(v["1x"]).shape[1::-1]) != v["size"]]
chk("4 json size＝實際尺寸", not badsz, str(badsz))
new = [k for k in K if "1x" in K[k] and not k.startswith("6c:nightcap")]
over12 = {k: len(cols(rgba(K[k]["1x"]))) for k in new if len(cols(rgba(K[k]["1x"]))) > 12}
chk("5 新畫嘅嘢每件 ≤12 色（tileset 條、fog、icon、卡、transition 條、dream_bg）", not over12, str(over12) or f"{len(new)} 件")
TH = ["forest", "lake", "toy", "star"]
chk("6 4 主題 tileset：56×56 ×4 款", all(K[f"6c:tile_{t}"]["size"] == [224, 56] for t in TH))
tiles = {f"{t}{v}": rgba(K[f"6c:tile_{t}"]["1x"])[:, v * 56:(v + 1) * 56] for t in TH for v in range(4)}
chk("7 tile 左上受光", all(lit_ok(a) for a in tiles.values()), str([k for k, a in tiles.items() if not lit_ok(a)]))
chk("8 tile 外描 #24172C", all(outlined(a) for a in tiles.values()), str([k for k, a in tiles.items() if not outlined(a)]))
fog = rgba(K["6c:fog"]["1x"])
chk("9 fog 56×56、實色棋盤（覆蓋 60–85%）", fog.shape[:2] == (56, 56) and .6 <= (fog[..., 3] == 255).mean() <= .85, f"{(fog[..., 3] == 255).mean():.2f}")
IDS = [f"{t}{i}" for t in "flts" for i in range(1, 6)]
chk("10 20 張夢卡 id 齊（f1–s5，同遊程 CARDS 一致）", sorted(J["cards"]) == sorted(IDS) and all(f"6c:card_{i}" in K for i in IDS))
cards = {i: rgba(K[f"6c:card_{i}"]["1x"]) for i in IDS}; cards["back"] = rgba(K["6c:card_back"]["1x"])
chk("11 卡 28×36（56×72 css）", all(a.shape[:2] == (36, 28) for a in cards.values()))
chk("12 卡左上受光＋外描", all(lit_ok(a) and outlined(a) for a in cards.values()), str([k for k, a in cards.items() if not (lit_ok(a) and outlined(a))]))
chk("13 卡之間唔重複", len({a.tobytes() for a in cards.values()}) == 21)
icn = {k: rgba(v["1x"]) for k, v in K.items() if k.startswith("6c:frag_") or k.startswith("icon_")}
chk("14 碎片 ×4＋rail icon ×2：16×16、≤12 色、受光、外描", len(icn) == 6 and all(a.shape[:2] == (16, 16) and len(cols(a)) <= 12 and lit_ok(a) and outlined(a) for a in icn.values()),
    str({k: (len(cols(a)), lit_ok(a), outlined(a)) for k, a in icn.items()}))
t = K["6c:transition"]; tr = rgba(t["1x"]); n = t["frames"]; fw, fh = t["frame"]
cov = [(tr[:, i * fw:(i + 1) * fw, 3] == 255).mean() for i in range(n)]
chk("15 transition 195×422 ×N 幀、覆蓋單調遞增、最後一幀全滿", tr.shape[:2] == (fh, fw * n) and [fw, fh] == [195, 422] and all(cov[i] < cov[i + 1] for i in range(n - 1)) and cov[-1] == 1.0,
    f"{n}f @{t['fps']}fps cov {cov[0]:.2f}→{cov[-1]:.2f}")
bg = rgba(K["6c:dream_bg"]["1x"])
chk("16 dream_bg 195×422 全幅不透明", bg.shape[:2] == (422, 195) and (bg[..., 3] == 255).all())
F6 = json.load(open(os.path.join(ROOT, "art/breakthrough/6a/faces6a.json")))["pets"]
chk("17 49 隻形態同 6a per_pet 一致", sorted(J["pets"]) == sorted(F6) and len(J["pets"]) == 49, f"{len(J['pets'])}")
import reactions_lib as L
bad = {k: [] for k in ("size", "pivot", "colors", "empty", "static", "ground", "count", "eyes", "cap")}
for pid, e in J["pets"].items():
    r = L.rig(pid); base = r.base; H, W = base.shape[:2]; s1 = rgba(e["1x"])
    if s1.shape[:2] != (H, W * e["frames"]) or e["frameSize"] != [W, H]: bad["size"].append(pid)
    if e["pivot"] != list(r.pivot) or e["pivot"] != F6[pid]["pivot"]: bad["pivot"].append(pid)
    if not cols(s1) <= cols(base): bad["colors"].append(pid)
    fr = [s1[:, i * W:(i + 1) * W] for i in range(e["frames"])]; n0 = int((base[..., 3] == 255).sum())
    if any((f[..., 3] == 255).sum() == 0 for f in fr): bad["empty"].append(pid)
    if len({f.tobytes() for f in fr}) < 3: bad["static"].append(pid)
    gb = np.where((base[..., 3] == 255).any(1))[0].max()
    if not any(np.where((f[..., 3] == 255).any(1))[0].max() == gb for f in fr): bad["ground"].append(pid)
    if any(abs(int((f[..., 3] == 255).sum()) - n0) > 0.12 * n0 for f in fr): bad["count"].append(pid)
    f0 = fr[0]; ex = [(x, y) for ey in r.eyes for (x, y) in ey["pix"]]
    if sum(tuple(f0[y, x]) != tuple(base[y, x]) for (x, y) in ex) < len(ex) * 0.3: bad["eyes"].append(pid)   # frame0 bodyDy＝0（或 hop 0）
    nc = e["nightcap"]
    if len(nc["xy"]) != e["frames"] or nc["key"] not in K: bad["cap"].append(pid)
chk("18 dream_walk 條大小＝idle 幀×幀數", not bad["size"], str(bad["size"]))
chk("19 dream_walk pivot＝idle／6a pivot", not bad["pivot"], str(bad["pivot"]))
chk("20 dream_walk 冇新色（只用 idle 幀 0 嘅色）", not bad["colors"], str(bad["colors"]))
chk("21 dream_walk 每幀非空、≥3 款唔同幀", not bad["empty"] and not bad["static"], str(bad["empty"] + bad["static"]))
chk("22 dream_walk 有幀腳踏地", not bad["ground"], str(bad["ground"]))
chk("23 dream_walk 冇走樣（每幀像素數 ±12% idle）", not bad["count"], str(bad["count"]))
chk("24 dream_walk 閉眼（眼 pix 已改）", not bad["eyes"], str(bad["eyes"]))
chk("25 睡帽：每隻有 size＋逐幀 xy", not bad["cap"], str(bad["cap"]))
cw = J["keys"]["6c:dream_walk"]
chk("26 clip 4–6 幀、fps 有設", 4 <= cw["frames"] <= 6 and cw["fps"] > 0, f"{cw['frames']}f @{cw['fps']}fps")
caps = [rgba(K[f"6c:nightcap_{s}"]["1x"]) for s in "SML"]
chk("27 睡帽 S<M<L、≤12 色", caps[0].shape[1] < caps[1].shape[1] < caps[2].shape[1] and all(len(cols(c)) <= 12 for c in caps), str([c.shape[1::-1] for c in caps]))
pv = os.path.join(D, "preview_6c_3x.png")
chk("28 preview_6c_3x.png 存在", os.path.exists(pv))
chk("29 冇 _backups", not any("_backups" in p for p in pngs) and not any("_backups" in dp for dp, _, _ in os.walk(D)))
print(f"{sum(res)}/{len(res)} passed")
sys.exit(0 if all(res) else 1)
