# series2 4a 驗證：alpha 0/255、每幀 ≤12 色、幀尺寸、pivot/腳、JSON 參照檔存在、clip 時長＋表情名
import os, sys, json, glob
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from series2_lib import S2
import reactions_lib as L
import build_series2_4a as B

ERR, WARN = [], []
def A(p): return np.array(Image.open(p).convert("RGBA"))
def ncol(a): m = a[..., 3] > 0; return len(np.unique(a[m][:, :3].reshape(-1, 3), axis=0)) if m.any() else 0
def chk(c, msg): (None if c else ERR.append(msg))

pix = [p for p in glob.glob(os.path.join(S2, "**", "*.png"), recursive=True) if "/ui/" not in p and "/preview/" not in p and "/_preview/" not in p and not p.endswith("_last.png")]
for p in pix:
    a = A(p); al = np.unique(a[..., 3]); chk(set(al.tolist()) <= {0, 255}, f"alpha 唔係 0/255：{p}")
# 48 strip：幀 ≤12 色、高 48、闊 48 倍數
strips = glob.glob(os.path.join(S2, "actions", "*.png")) + glob.glob(os.path.join(S2, "forms", "**", "*.png"), recursive=True) + glob.glob(os.path.join(S2, "egg", "*.png"))
def pal(a): m = a[..., 3] > 0; return set(map(tuple, a[m][:, :3].reshape(-1, 3).tolist()))
for p in strips:
    a = A(p); chk(a.shape[0] == 48 and a.shape[1] % 48 == 0, f"尺寸錯 {a.shape}：{p}")
    key = os.path.basename(p).split("_")[0]
    if key in B.NEWF or "/egg/" in p:
        for i in range(a.shape[1] // 48):
            n = ncol(a[:, i * 48:(i + 1) * 48]); chk(n <= 12, f"{n} 色 > 12：{p} 幀 {i}")
    else:   # 現有 from_ref（本身 >12 色）：新動作唔可以加超過 6 隻 idle 冇嘅色（表情／眼淚）
        base = pal(A(os.path.join(S2, "actions", f"{key}_idle.png")))
        extra = pal(a) - base; chk(len(extra) <= 6, f"{p} 加咗 {len(extra)} 隻新色")
# 腳 y=46（idle 幀 0）
for k in B.NEWF:
    a = A(os.path.join(S2, "forms", "sprites", f"{k}_48.png")); ys = np.nonzero(a[..., 3].any(1))[0]
    want = 46
    if k.startswith("S4"):   # 少年跟返佢 1 階嘅腳（B1 水母觸鬚本身喺 y=45）
        r = np.array(Image.open(os.path.join(B.T48, "idle", f"{k[-1]}1_idle.png")).convert("RGBA"))[:, :48]; want = np.nonzero(r[..., 3].any(1))[0].max()
    chk(ys.max() == want, f"{k} 腳 y={ys.max()}（要 {want}）")
# 34 階段 × 5 動作
J = json.load(open(os.path.join(S2, "actions", "actions.json")))
chk(len(J["forms"]) == 34, f"actions 只有 {len(J['forms'])} 個階段")
for k, v in J["forms"].items():
    for a in ("idle", "walk", "cry", "eat", "sleep"): chk(os.path.exists(os.path.join(S2, v.get(a, "?"))), f"缺 {k} {a}")
# 道具／FX 疊層 ≤12 色
for p in glob.glob(os.path.join(S2, "lessons", "props", "*.png")) + glob.glob(os.path.join(S2, "lessons", "fx", "*.png")) + glob.glob(os.path.join(S2, "duo", "overlays", "*.png")):
    chk(ncol(A(p)) <= 12, f"疊層 >12 色：{p}")
# lessons
LS = json.load(open(os.path.join(S2, "lessons", "lessons.json")))
OLD = set(["blink", "squint", "squint_blush", "laugh_a", "laugh_b", "dizzy_a", "dizzy_b", "sleepy", "sleep", "surprised", "smug", "embarrassed", "lookup"])
chk(len(LS["propsBySeries"]) == 8 and len(LS["demo"]) == 8 and len(LS["copy"]) == 8, "教錯課唔夠 8")
for r, v in LS["propsBySeries"].items(): chk(os.path.exists(os.path.join(S2, v["png"])), f"缺道具 {v['png']}")
for r, v in LS["fx2"].items(): chk(os.path.exists(os.path.join(S2, v["png"])), f"缺 fx {v['png']}")
fxids = set(L.build_fx()) | set(LS["fx2"]) | {v["id"] for v in LS["propsBySeries"].values()}
for grp, dur, faces in (("demo", 3000, OLD), ("copy", 2000, set(L.FACES) | set(B.NEW_FACES))):
    for r, c in LS[grp].items():
        chk(c["durationMs"] == dur, f"{grp} {r} 時長 {c['durationMs']}")
        for f in c["face"]:
            for n in (f["f"] if isinstance(f["f"], list) else [f["f"]]): chk(n in faces, f"{grp} {r} 表情 {n} 唔喺可用表")
        for f in c["fx"]: chk(f["id"] in fxids, f"{grp} {r} fx {f['id']} 冇定義"); chk(0 <= f["t0"] < f["t1"] <= dur, f"{grp} {r} fx 時間超出")
FJ = json.load(open(os.path.join(S2, "faces", "faces.json")))
for k, v in FJ.items(): chk(os.path.exists(os.path.join(S2, v["png"])), f"缺表情 {v['png']}")
# UI
U = json.load(open(os.path.join(S2, "ui", "ui_series2_4a.json")))
chk(len(U["props"]) == 8 and len(U["dreams"]) == 8, "UI 唔夠 8+8")
for g in ("props", "dreams"):
    for r, v in U[g].items(): chk(os.path.exists(os.path.join(S2, v["png"])), f"缺 UI {v['png']}")
# duo / levelup
D = json.load(open(os.path.join(S2, "duo", "duo.json")))
chk(set(D["clips"]) == {"cuddle_egg", "hatch_first_glance", "follow_walk", "comfort_cry", "eat_together", "sleep_together"}, "雙人 clip 唔啱 6 個")
for k, v in D["overlays"].items():
    if "png" in v: chk(os.path.exists(os.path.join(S2, v["png"])), f"缺疊層 {v['png']}")
h = D["clips"]["hatch_first_glance"]; chk(h["grid"] == [195, 422] and h["durationMs"] == 2000, "孵化第一眼規格錯")
TRCL = set(json.load(open(os.path.join(L.ATT, "evo_still_lumi.json")))["clips"])
LV = json.load(open(os.path.join(S2, "levelup", "levelup.json")))
chk(len(LV["scenes"]) == 3, "升級場面唔夠 3")
for grp, clips in (("duo", {k: v for k, v in D["clips"].items() if k != "hatch_first_glance"}), ("levelup", LV["scenes"])):
    for name, c in clips.items():
        if grp == "levelup": chk(4000 <= c["durationMs"] <= 6000, f"{name} 時長 {c['durationMs']}")
        for a in c["actors"].values():
            for k in a["track"]:
                if a["who"] == "tr": chk(k["clip"] in TRCL, f"{name} 團絨 clip {k['clip']} 唔存在")
                if a["who"] == "kid": chk(k["clip"] in ("idle", "walk", "cry", "eat", "sleep"), f"{name} 細佬 clip {k['clip']}")
        for o in c.get("overlays", []): chk(o["id"] in D["overlays"], f"{name} 疊層 {o['id']} 冇定義")
for n in ("lineup_4x.png", "ui_props_dreams.png", "duo_hatch_first_glance.gif"): chk(os.path.exists(os.path.join(S2, "preview", n)), f"缺預覽 {n}")
chk(not glob.glob(os.path.join(S2, "**", "_backups"), recursive=True), "有 _backups")
print(f"檢查 PNG {len(pix)} 個（strip {len(strips)}）")
if ERR:
    print("FAIL", len(ERR)); [print(" -", e) for e in ERR[:40]]; sys.exit(1)
print("PASS 0 error")
