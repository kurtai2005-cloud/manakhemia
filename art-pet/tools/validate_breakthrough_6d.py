#!/usr/bin/env python3
"""驗 6d 社交美術（art/breakthrough/6d）。python3 art-pet/tools/validate_breakthrough_6d.py"""
import os, sys, json
import numpy as np
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(ROOT, "art/breakthrough/6d"); KIT = os.path.join(ROOT, "art-pet/ui/kit_hd2d_v2")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
res = []
def chk(name, ok, info=""):
    res.append(bool(ok)); print(("PASS " if ok else "FAIL ") + name + (f" — {info}" if info else ""))
def rgba(p): return np.array(Image.open(os.path.join(D, p)).convert("RGBA"))
def cols(a): m = a[..., 3] == 255; return {tuple(int(v) for v in c) for c in a[m][:, :3]}
def up3(a1, a3): return a3.shape[0] == a1.shape[0] * 3 and np.array_equal(np.repeat(np.repeat(a1, 3, 0), 3, 1), a3)
LINE = (0x24, 0x17, 0x2C)
def lit_ok(a):
    sol = a[..., 3] == 255; ln = sol & np.all(a[..., :3] == LINE, -1); fill = sol & ~ln
    pad = np.pad(ln | ~sol, 1, constant_values=True)
    upL = pad[:-2, 1:-1] | pad[1:-1, :-2]; dnR = pad[2:, 1:-1] | pad[1:-1, 2:]
    lum = a[..., :3] @ np.array([.299, .587, .114]); A = fill & upL & ~dnR; B = fill & dnR & ~upL
    return A.any() and B.any() and lum[A].mean() > lum[B].mean()
def outlined(a):
    sol = a[..., 3] == 255; p = np.pad(sol, 1, constant_values=False)
    edge = sol & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])
    return np.all(a[edge][:, :3] == LINE, -1).all()
def lumw(c):
    c = np.array(c[:3]) / 255; c = np.where(c <= .03928, c / 12.92, ((c + .055) / 1.055) ** 2.4); return c @ np.array([.2126, .7152, .0722])
def contrast(a, b): la, lb = sorted((lumw(a), lumw(b)), reverse=True); return (la + .05) / (lb + .05)

J = json.load(open(os.path.join(D, "share6d.json"))); K = J["keys"]
pngs = [os.path.relpath(os.path.join(dp, f), D) for dp, _, fs in os.walk(D) for f in fs if f.endswith(".png")]
chk("1 alpha 只得 0／255（全部 PNG）", all(set(np.unique(rgba(p)[..., 3])) <= {0, 255} for p in pngs), f"{len(pngs)} png")
missing = [v[k] for v in K.values() for k in ("1x", "3x") if not os.path.exists(os.path.join(D, v[k]))] + [v for v in J["mockups"].values() if not os.path.exists(os.path.join(D, v))]
chk("2 json 列嘅檔全部存在", not missing, str(missing[:3]))
p1 = [p for p in pngs if "@3x" not in p and not p.endswith("_3x.png")]
chk("3 每個 1x 都有 @3x，而且＝最近鄰 ×3", all(os.path.exists(os.path.join(D, p.replace(".png", "@3x.png"))) and up3(rgba(p), rgba(p.replace(".png", "@3x.png"))) for p in p1), f"{len(p1)} 對")
badsz = [k for k, v in K.items() if list(rgba(v["1x"]).shape[1::-1]) != v["size"]]
chk("4 json size＝實際尺寸", not badsz, str(badsz))
new = [k for k in K if k != "6d:share_card_bg"]
over12 = {k: len(cols(rgba(K[k]["1x"]))) for k in new if len(cols(rgba(K[k]["1x"]))) > 12}
chk("5 新畫嘅嘢每件 ≤12 色", not over12, str(over12) or f"{len(new)} 件")
kitc = cols(np.array(Image.open(os.path.join(KIT, "atlas/ui_hd2d_v2@1x.png")).convert("RGBA")))
newc = set().union(*[cols(rgba(K[k]["1x"])) for k in ("6d:qr_frame", "6d:code_field", "6d:code_field_on")])
extra = cols(rgba(K["6d:share_card_bg"]["1x"])) - kitc - newc
chk("6 share_card_bg 只用 kit 零件色＋6d 零件色（kit 砌，冇自創色）", not extra, f"{len(extra)} 隻外來色")
nine = {k: v for k, v in K.items() if "slice" in v}
chk("7 9-slice 零件有 slice／nine／mode＝tile，nine 唔超出", all(v["mode"] == "tile" and v["nine"][0] + v["nine"][2] < v["size"][0] and v["nine"][1] + v["nine"][3] <= v["size"][1] for v in nine.values()), str(list(nine)))
q = rgba(K["6d:qr_frame"]["1x"]); inner = q[4:-4, 4:-4]
chk("8 qr_frame 中間 quiet zone 全白、實色", (inner[..., 3] == 255).all() and np.all(inner[..., :3] == 255))
sm = rgba(K["6d:shadow_mask"]["1x"]); yy, xx = np.mgrid[0:4, 0:4]
chk("9 shadow_mask 4×4 50% 棋盤（取代半透明）", sm.shape[:2] == (4, 4) and np.array_equal(sm[..., 3] == 255, (xx + yy) % 2 == 0))
ic = {k: rgba(v["1x"]) for k, v in K.items() if k.startswith("icon_")}
chk("10 icon ×7：16×16、受光、外描", len(ic) == 7 and all(a.shape[:2] == (16, 16) and lit_ok(a) and outlined(a) for a in ic.values()), str({k: (lit_ok(a), outlined(a)) for k, a in ic.items()}))
kitic = {f.split("@")[0] for f in os.listdir(os.path.join(KIT, "icons"))}
clash = [k for k in ic if "ic_" + k[5:] in kitic]
chk("11 新 icon 名唔撞 kit 現有 icon", not clash, str(clash))
fb = rgba(K["6d:friend_badge"]["1x"])
chk("12 朋友牌 32×32、受光、外描、≤12 色", fb.shape[:2] == (32, 32) and lit_ok(fb) and outlined(fb) and len(cols(fb)) <= 12, f"{len(cols(fb))} 色")
TL = J["text"]
chk("13 所有字 ≥FP12", TL and all(t["size"] >= 12 for t in TL), f"{len(TL)} 段，最細 {min(t['size'] for t in TL)}")
cmin = min(min(contrast(t["fg"], t["outline"]), contrast(t["fg2"], t["outline"])) for t in TL)
chk("14 字有描邊，字色對描邊對比 ≥4.5", cmin >= 4.5, f"最低 {cmin:.2f}")
dark = [t for t in TL if lumw(t["bg"]) < .2]
cdark = min(min(contrast(t["fg"], t["bg"]), contrast(t["fg2"], t["bg"])) for t in dark)
chk("15 深色底上嘅字對底色 ≥4.5", cdark >= 4.5, f"{len(dark)} 段，最低 {cdark:.2f}")
ms = {k: np.array(Image.open(os.path.join(D, v))) for k, v in J["mockups"].items() if v.endswith("_3x.png")}
chk("16 4 個 mockup 585×1266（195×422 ×3）", len(ms) == 4 and all(m.shape[:2] == (1266, 585) for m in ms.values()), str(list(ms)))
S = K["6d:share_card_bg"]["slots"]; w, h = K["6d:share_card_bg"]["size"]; qq = S["qr"]
chk("17 share card slot 喺卡內、QR 白位 ≥ 49 module＋4×2 quiet", qq["x"] + qq["w"] <= w and qq["y"] + qq["h"] <= h and qq["inner"][2] >= 57 - 8 + 8 and S["code"]["y"] < h, f"card {w}×{h}")
ttf = [f for f in os.listdir(os.path.join(KIT, "fonts")) if f.lower().endswith(".ttf")]
chk("18 Fusion Pixel TTF 喺 kit fonts", any("12" in f for f in ttf), str(ttf))
chk("19 preview_6d_3x.png 存在", os.path.exists(os.path.join(D, "preview_6d_3x.png")))
chk("20 冇 _backups", not any("_backups" in dp for dp, _, _ in os.walk(D)))
print(f"{sum(res)}/{len(res)} passed")
sys.exit(0 if all(res) else 1)
