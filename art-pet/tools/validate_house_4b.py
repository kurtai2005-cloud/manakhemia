# 《微光小圃》4b 屋仔 validator：cd art-pet && python3 tools/validate_house_4b.py
import json, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from series2_lib import ART
D = os.path.join(ART, "sprites/series2_house"); ERR = []; N = {"png": 0}
def err(m): ERR.append(m)
def png(p):
    a = np.asarray(Image.open(os.path.join(D, p)).convert("RGBA")); N["png"] += 1; return a
def ncol(a): m = a[..., 3] > 0; return len(np.unique(a[m][:, :3].reshape(-1, 3), axis=0)) if m.any() else 0
def binary(a, p):
    if not set(np.unique(a[..., 3])) <= {0, 255}: err(f"{p}: alpha 唔係 0/255")

J = json.load(open(os.path.join(D, "house.json")))
A = json.load(open(os.path.join(D, "actions/actions_house.json")))
NEWF = ["S1", "S2"] + [f"S4{c}" for c in "ABCDEFGH"]
# 1 房間層
for v in ("day", "night"):
    for n in ("sky", "far", "mid", "fore", "lightmap", "light_add", "emissive", "emissive_blur"):
        a = png(f"room/{v}/{n}.png")
        if a.shape[:2] != (446, 223): err(f"room/{v}/{n} size {a.shape[:2]}")
    if png(f"room/{v}/vignette.png").shape[:2] != (422, 195): err(f"room/{v}/vignette size")
    for n in ("sky", "far", "mid", "fore"):
        a = png(f"room/{v}/raw/{n}.png"); binary(a, f"raw/{v}/{n}")
        if ncol(a) > 64: err(f"raw/{v}/{n} {ncol(a)} 色 >64")
    binary(png(f"room/{v}/emissive.png"), f"room/{v}/emissive")
    for f in ("grade.json", "palette.json"):
        if not os.path.exists(os.path.join(D, f"room/{v}/{f}")): err(f"缺 room/{v}/{f}")
# 2 家具
F = J["furniture"]
if len(F) != 12: err(f"家具 {len(F)} 件 ≠12")
for s in J["slotOrder"]:
    its = [f for f, e in F.items() if e["slot"] == s]
    if len(its) != 2: err(f"slot {s} {len(its)} 件 ≠2")
    if sorted(its) != sorted(J["slots"][s]["items"]): err(f"slot {s} items 唔夾")
for fid, e in F.items():
    for key in ("png", "front", "emissive"):
        if key in e:
            a = png(e[key]); binary(a, e[key])
            if ncol(a) > 12: err(f"{e[key]} {ncol(a)} 色 >12")
            if key == "png" and list(a.shape[1::-1]) != e["size"]: err(f"{fid} size 唔夾")
    if "glow" in e: png(e["glow"])
    px, py = e["pivot"]; w, h = e["size"]
    if not (0 <= px < w and 0 <= py < h): err(f"{fid} pivot 出界")
shop = [f for f, e in F.items() if e["source"] == "shop"]
if len(shop) != 7: err(f"商店 {len(shop)} 件 ≠7（葉仔床改預設）")
if J["defaultState"]["slots"].get("bed") != "bed_leaf": err("預設床唔係 bed_leaf")
tot = sum(F[f]["price"] for f in shop)
if tot != 165: err(f"商店總價 {tot} ≠165")
if any(not 15 <= F[f]["price"] <= 40 for f in shop): err("價錢出 15–40")
if sum(e["source"] == "commission" for e in F.values()) != 2: err("委託獎 ≠2")
if sum(e["source"].startswith("visitor:") for e in F.values()) != 2: err("訪客獎 ≠2")
# 3 擺位／行走
x0, y0, x1, y1 = J["walk"]["rect"]
inside = lambda x, y: x0 <= x <= x1 and y0 <= y <= y1
def blocked(x, y):
    for s, b in J["walk"]["blockers"].items():
        ax, ay = J["slots"][s]["anchor"]
        if ax + b[0] <= x <= ax + b[2] and ay + b[1] <= y <= ay + b[3]: return s
rx, ry = J["slots"]["rug"]["anchor"]
for k, a in J["duo"]["sit_together"]["actors"].items():
    x, y = rx + a["dx"], ry + a["dy"]
    if not inside(x, y) or blocked(x, y): err(f"坐埋位 {k} ({x},{y}) 唔喺行走區／撞家具")
if J["slots"]["window"]["anchor"] != [53, 124]: err("窗 anchor 唔對準窗洞中心")
for s in ("bed", "table", "lamp"):
    ax, ay = J["slots"][s]["anchor"]
    if not (y0 - 20 <= ay <= y1 + 2): err(f"{s} anchor y {ay} 離行走區太遠")
for s, sl in J["slots"].items():
    px, py = sl["pin"]
    if py + J["ui"]["decorate"]["roomOffsetY"] < 26 or py + J["ui"]["decorate"]["roomOffsetY"] > 276: err(f"pin {s} 佈置模式出咗可見區")
# 4 動作
clips = A["clips"]
if set(clips) != {"sit", "prank_do", "prank_got"}: err("clips 唔啱")
if len(A["forms"]) != 59: err(f"動作形態 {len(A['forms'])} ≠59（34+25）")
for k, f in A["forms"].items():
    for c in clips:
        e = f[c]; a = png(e["png"]); binary(a, e["png"])
        if a.shape[1] != e["frameW"] * clips[c]["frames"] or a.shape[0] != e["frameH"]: err(f"{e['png']} strip size")
        if k in NEWF:
            for i in range(clips[c]["frames"]):
                fr = a[:, i * e["frameW"]:(i + 1) * e["frameW"]]
                if ncol(fr) > 12: err(f"{e['png']} 第{i}格 {ncol(fr)} 色 >12")
# 5 UI（HD-2D only）
for n, p in J["ui"]["assets"].items():
    if not os.path.exists(os.path.join(D, p)): err(f"缺 UI {p}")
    else: png(p)
for p in ("decorate_bed_HD2D_3x", "decorate_lamp_HD2D_3x", "house_hud_HD2D_3x", "garden_entry_HD2D_3x", "garden_entry_locked_HD2D_3x"):
    im = Image.open(os.path.join(D, "preview", p + ".png"))
    if im.size != (585, 1266): err(f"{p} 唔係 585×1266")
for p in ("room_setA_3x.png", "room_setB_3x.png", "living_two_pets_3x.png", "decorate_ui_HD2D_3x.png", "house_two_pets.gif"):
    if not os.path.exists(os.path.join(D, "preview", p)): err(f"缺預覽 {p}")
# 6 雜項
for root, dirs, files in os.walk(D):
    if "_backups" in root or "_backups" in dirs: err("有 _backups")
    for f in files:
        if "B2" in f and ("/ui" in root or "/preview" in root): err(f"有 B2 檔 {f}（應只係 HD-2D）")
if not os.path.exists(os.path.join(D, "HOUSE_4B.md")): err("缺 HOUSE_4B.md")
print(f"checked {N['png']} png")
if ERR:
    print("FAIL", len(ERR)); [print(" -", e) for e in ERR]; sys.exit(1)
print("PASS")
