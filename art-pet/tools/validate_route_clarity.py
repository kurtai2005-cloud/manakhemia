#!/usr/bin/env python3
"""validate_route_clarity.py — evo6 batch G（§7 路線清晰化）驗證：燈色 spec／palette／遮罩／換色 atlas／剪影／collection／tell clip。"""
import json, os, sys, math
import numpy as np
from PIL import Image
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
EV = os.path.join(ROOT, "sprites/tuanrong/evo6"); RC = os.path.join(EV, "route_clarity"); MOT = os.path.join(ROOT, "sprites/tuanrong/motion")
fails, info = [], []
F = fails.append
hx = lambda h: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
load = lambda p: np.array(Image.open(p).convert("RGBA"))
IDS = ["tide", "moon", "shroom", "crystal", "ember", "radiant", "soft", "dust", "lumi"]
HINT = {"tide": "「朝早 6–9 點照顧，或者成日淋水」", "moon": "「夜晚 8 點後陪佢、哄佢瞓」", "shroom": "「落雨陰天陪佢食多啲」", "crystal": "「一返嚟就執乾淨」",
        "ember": "「玩得最多（包括小遊戲）」", "radiant": "「樣樣都照顧好」", "soft": "「普通照顧」", "dust": "「好少理佢」", "lumi": "隱藏：「？？？」"}
SLOTS = ("glow", "glow_mid", "glow_core")
def lab(rgb):
    def f(c):
        c /= 255; return ((c + .055) / 1.055) ** 2.4 if c > .04045 else c / 12.92
    r, g, b = (f(float(x)) for x in rgb)
    X, Y, Z = (r * .4124 + g * .3576 + b * .1805) / .95047, r * .2126 + g * .7152 + b * .0722, (r * .0193 + g * .1192 + b * .9505) / 1.08883
    t = lambda v: v ** (1 / 3) if v > .008856 else 7.787 * v + 16 / 116
    return (116 * t(Y) - 16, 500 * (t(X) - t(Y)), 200 * (t(Y) - t(Z)))
dE = lambda a, b: math.dist(lab(a), lab(b))
base_pal = json.load(open(os.path.join(EV, "palette_base.json")))
BASE = {c["name"]: c["hex"] for c in base_pal["colors"]}
spec = json.load(open(os.path.join(RC, "palette_route_bulbs.json")))
if list(spec["paths"]) != IDS: F(f"paths {list(spec['paths'])}")
if spec["base"] != {s: BASE[s] for s in SLOTS}: F("base ramp != palette_base")
ramps = {}
for pid, p in spec["paths"].items():
    if p["hint"] != HINT[pid]: F(f"hint {pid}")
    if pid == "lumi":
        if not p["hidden"] or p["ramp"] is not None: F("lumi 要隱藏冇燈色")
        continue
    r = p["ramp"]; ramps[pid] = [hx(r[s]) for s in SLOTS]
    L = [lab(c)[0] for c in ramps[pid]]
    if not (L[0] < L[1] < L[2]): F(f"ramp 光度唔遞增 {pid} {L}")
cols = dict(ramps); cols["base"] = [hx(BASE[s]) for s in SLOTS]
mind = min((dE(cols[a][0], cols[b][0]), a, b) for a in cols for b in cols if a < b)
mindm = min((dE(cols[a][1], cols[b][1]), a, b) for a in cols for b in cols if a < b)
if mind[0] < 15 or mindm[0] < 12: F(f"燈色太近 glow {mind} mid {mindm}")
info.append(f"燈色 8 路＋原燈黃：glow 最近 ΔE {mind[0]:.1f}（{mind[1]}/{mind[2]}），mid 最近 ΔE {mindm[0]:.1f}（{mindm[1]}/{mindm[2]}）")
# palettes
for pid, r in ramps.items():
    pal = json.load(open(os.path.join(RC, f"palette_evo_hop_{pid}.json")))
    if [c["name"] for c in pal["colors"]] != [c["name"] for c in base_pal["colors"]]: F(f"palette names {pid}")
    for c in pal["colors"]:
        exp = spec["paths"][pid]["ramp"][c["name"]] if c["name"] in SLOTS else BASE[c["name"]]
        if c["hex"] != exp: F(f"palette {pid} {c['name']}")
# mask + recoloured atlases
base = load(os.path.join(EV, "atlas_evo_hop.png")); mk = load(os.path.join(RC, "atlas_evo_hop_bulbmask.png"))
if mk.shape != base.shape: F("mask size")
on = mk[..., 3] == 255
slot = np.full(on.shape, -1)
for i in range(3): slot[on & (mk[..., i] == 255)] = i
if ((slot >= 0) != on).any() or (on & ((mk[..., :3] == 255).sum(-1) != 1)).any(): F("mask 唔係單一 slot")
for i, s in enumerate(SLOTS):
    m = slot == i
    if not (base[m][:, :3] == hx(BASE[s])).all() or not (base[m][:, 3] == 255).all(): F(f"mask slot {s} 落喺非 {s} 像素")
aj = json.load(open(os.path.join(EV, "atlas_evo_hop.json")))
nolamp = []
for k, v in aj["frames"].items():
    if k.startswith(("eyes_", "mouth_")): continue
    f = v["frame"]
    if not on[f["y"]:f["y"] + f["h"], f["x"]:f["x"] + f["w"]].any(): nolamp.append(k)
for pid, r in ramps.items():
    im = load(os.path.join(RC, f"atlas_evo_hop_bulb_{pid}.png"))
    if im.shape != base.shape: F(f"atlas size {pid}"); continue
    d = (im != base).any(-1)
    if (d & ~on).any(): F(f"{pid} 燈以外像素有改 {(d & ~on).sum()}")
    for i in range(3):
        if not (im[slot == i][:, :3] == r[i]).all(): F(f"{pid} slot {i} 色錯")
info.append(f"bulbmask 燈像素 {int(on.sum())}；冇燈嘅 frame 塊 {len(nolamp)}：{sorted(set(n.rsplit('_', 1)[0] for n in nolamp))}（病＝灰燈 sick1；bulb_glow＝白/cream4 高光蓋，唔換色）")
if any(not n.startswith(("sick_", "sick_noface_", "bulb_glow")) for n in nolamp): F(f"非病幀冇燈 {[n for n in nolamp if not n.startswith('sick')]}")
# silhouettes + collection
col = json.load(open(os.path.join(RC, "collection_route.json")))
if list(col["paths"]) != IDS: F("collection ids")
sils = {}
for pid in IDS:
    c = col["paths"][pid]
    if c["hint"] != HINT[pid]: F(f"collection hint {pid}")
    p = os.path.join(EV, c["silhouette"])
    a = load(p)
    if a.shape != (48, 48, 4): F(f"sil size {pid} {a.shape}")
    al = a[..., 3]
    if not set(np.unique(al)) <= {0, 255}: F(f"sil alpha {pid}")
    if not (a[al == 255][:, :3] == hx("#3B2A3E")).all(): F(f"sil colour {pid}")
    if al[0].any() or al[-1].any() or al[:, 0].any() or al[:, -1].any(): F(f"sil edge {pid}")
    src = load(os.path.join(EV, c["unlocked"]["form"], "frames", "idle_01.png"))[..., 3] > 0
    ov = ((al == 255) & src).sum() / max(1, src.sum())
    if ov < .9: F(f"sil 同靜光 idle_01 唔夾 {pid} {ov:.2f}")
    sils[pid] = al == 255
mx = max(((sils[a] & sils[b]).sum() / (sils[a] | sils[b]).sum(), a, b) for a in IDS for b in IDS if a < b)
if mx[0] > .95: F(f"剪影太相似 {mx}")
info.append(f"剪影 9 張 48px 實心 #3B2A3E；最相似 IoU {mx[0]:.2f}（{mx[1]}/{mx[2]}）")
# tells
CL = json.load(open(os.path.join(MOT, "CLIPS.json"))); G = CL.get("evo6G", {}); TC = G.get("tellClips", {})
if set(TC) != {f"tell_{p}" for p in IDS}: F(f"tellClips {set(TC)}")
if CL["forms"]["evo_hop"].get("tells") != [f"tell_{p}" for p in IDS]: F("forms.evo_hop.tells")
if any(c["name"].startswith("tell_") for c in CL["clips"]): F("tell 唔應該入頂層 clips[]")
an = aj.get("animations", {})
nfr = 0
for c, e in TC.items():
    n = e["frames"]; nfr += n
    if e["loop"] or e["next"] != "idle" or e["route"] != c[5:]: F(f"tell meta {c}")
    for k in range(1, n + 1):
        for nm in (f"{c}_{k:02d}", f"{c}_noface_{k:02d}"):
            if nm not in aj["frames"]: F(f"atlas missing {nm}")
    for key in (c, f"{c}_noface"):
        a_ = an.get(key)
        if not a_ or len(a_["frames"]) != n or a_.get("fps") != e["fps"]: F(f"atlas anim {key}")
info.append(f"tell clip {len(TC)} 個／{nfr} 幀（evo_hop atlas 已包）")
# 提示字（§7 v10 補充／v10.1）：CLIPS.json evo6G.paths＋CLIPS.md 表要同 HINT 一樣；舊字唔准再出現
for pid in IDS:
    if G.get("paths", {}).get(pid, {}).get("hint") != HINT[pid]: F(f"CLIPS.json evo6G hint {pid}")
STALE = ("餵得最多", "夜晚 9 點至凌晨 3 點", "執得最乾淨")
md_ = open(os.path.join(MOT, "CLIPS.md"), encoding="utf-8").read()
for nm_, txt in (("CLIPS.md", md_), ("CLIPS.json", json.dumps(CL, ensure_ascii=False)),
                 ("palette_route_bulbs.json", json.dumps(spec, ensure_ascii=False)), ("collection_route.json", json.dumps(col, ensure_ascii=False))):
    for st in STALE:
        if st in txt: F(f"{nm_} 仲有舊提示「{st}」")
info.append("提示字：菇傘／月眠 v10.1、晶角 v6（冇舊字）")
print("\n".join(info))
if fails: print("FAIL", len(fails)); print("\n".join(fails[:40])); sys.exit(1)
print("OK validate_route_clarity")
