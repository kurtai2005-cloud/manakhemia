#!/usr/bin/env python3
"""validate_systems12_b1.py — systems12 第 1 批素材驗證（獨立於 build）。
檢查：
1. 天氣 clip leaf_umbrella(6)／shiver(4) × 25 形態（sprout／radiant／soft／lumi＋evo6 21，光卵除外）：檔案齊、幀數、
   CLIPS.json 頂層 entry＋anchors.<form>＝face_anchors、lumi／evo 子 entry 路徑存在、forms.*.clips 有列、atlas animations 有齊；
   葉色喺第 2–6 幀出現、五官／燈錨點冇被葉蓋；shiver 有震線（drop_d）、第 2／4 幀有白氣。
2. UI（ui/systems12）：v3 31 色、alpha 0/255、尺寸（星星碎 16／32）、9-slice 數值合理、atlas 像素＝散檔＋extrude 1。
3. 天氣 陰／霧：grade schema（同 validate_hd2d_scenes）、4 層 223×446、lut 256×16＝make_lut(grade)、sky＝LUT(霧淡出(raw))、天氣 tile alpha 0/255＋尺寸。
4. 季節 4×4：grade schema、層尺寸、lut＝season_fn(make_lut(variant grade))、sky＝LUT(raw)、lightmap 尺寸；seasons.json 月份＝香港（全年 12 個月各一次）。"""
import json, os, sys, glob
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import validate_hd2d_scenes as V
import build_hd2d_scenes as B
ROOT = os.path.normpath(os.path.join(HERE, "..")); TR = os.path.join(ROOT, "sprites", "tuanrong"); MOT = os.path.join(TR, "motion"); LV = os.path.join(MOT, "liveliness")
EV = os.path.join(TR, "evo6"); LU = os.path.join(TR, "lumi"); UI = os.path.join(ROOT, "ui", "systems12"); SCN = B.OUT
WX = {"leaf_umbrella": 6, "shiver": 4}
fails = []; info = []; F = fails.append
load = lambda p: np.array(Image.open(p).convert("RGBA"))
hx = lambda h: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
def palmap(p): return {c["name"]: hx(c["hex"]) for c in json.load(open(p))["colors"]}
V3 = palmap(os.path.join(MOT, "palette.json")); V3SET = set(V3.values())

CL = json.load(open(os.path.join(MOT, "CLIPS.json"))); byname = {c["name"]: c for c in CL["clips"]}
evo = [f for f, fe in CL["forms"].items() if fe.get("evo6") and f != "evo_egg" and "clipDefs" not in fe]
forms = ["sprout", "radiant", "soft", "lumi"] + evo
if len(forms) != 25: F(f"form count {len(forms)} != 25")
FAB = json.load(open(os.path.join(LV, "face_anchors.json")))["anchors"]; FAL = json.load(open(os.path.join(LU, "face_anchors_lumi.json")))["anchors"]
nfr = 0; leaf_ok = 0; shv_ok = 0
for form in forms:
    if form in ("sprout", "radiant", "soft"):
        fr = lambda c, k: os.path.join(LV, "frames", form, f"{c}_{k:02d}.png"); nf = lambda c, k: os.path.join(LV, "layers", form, f"{c}_{k:02d}_noface.png")
        FA = FAB[form]; pal = V3; atl = [os.path.join(LV, f"atlas_{form}_live_wx.json")]; emd = None
    elif form == "lumi":
        fr = lambda c, k: os.path.join(LU, "frames", f"{c}_{k:02d}.png"); nf = lambda c, k: os.path.join(LU, "layers", f"{c}_{k:02d}_noface.png")
        FA = FAL; pal = palmap(os.path.join(LU, "palette_lumi.json")); atl = [os.path.join(TR, "atlas_lumi.json")]; emd = os.path.join(LU, "emissive")
    else:
        D = os.path.join(EV, form)
        fr = lambda c, k, D=D: os.path.join(D, "frames", f"{c}_{k:02d}.png"); nf = lambda c, k, D=D: os.path.join(D, "layers", f"{c}_{k:02d}_noface.png")
        FAJ = json.load(open(os.path.join(D, f"face_anchors_{form}.json"))); FA = FAJ["anchors"]
        if FAJ.get("weatherClips") != list(WX): F(f"{form} face_anchors weatherClips")
        aj_ = json.load(open(os.path.join(EV, f"atlas_{form}.json"))); pal = palmap(os.path.join(EV, aj_["meta"]["palette"]))
        atl = [os.path.join(EV, f"atlas_{form}.json")]; emd = os.path.join(D, "emissive")
        fe = CL["forms"][form]
        if fe.get("weather") != list(WX) or not set(WX) <= set(fe["clips"]): F(f"{form} forms.weather/clips")
    LEAF = np.array([pal[n] for n in ("leaf", "leaf_d") if n in pal]); DROPD = pal.get("drop_d"); WHITE = pal.get("white")
    if len(LEAF) != 2 or DROPD is None or WHITE is None: F(f"{form} palette lacks leaf/leaf_d/drop_d/white")
    anims = {}
    for js in atl: anims.update(json.load(open(js))["animations"])
    for c, n in WX.items():
        ent = byname.get(c)
        if not ent: F(f"CLIPS clip {c} missing"); continue
        if ent.get("anchors", {}).get(form) != FA.get(c): F(f"{form} {c} CLIPS anchors != face_anchors")
        if form not in ("sprout", "radiant", "soft"):
            sub = ent.get(form)
            if not sub or sub.get("frames") != n: F(f"{form} {c} CLIPS sub-entry"); 
            else:
                for key in ("full", "noface", "faceov", "emissive"):
                    if not os.path.exists(os.path.normpath(os.path.join(MOT, sub[key].replace("NN", "01")))): F(f"{form} {c} sub path {key}")
        if len(FA.get(c, [])) != n: F(f"{form} {c} anchors {len(FA.get(c, []))} != {n}")
        for an in (c, c + "_noface"):
            if an not in anims or len(anims[an]["frames"]) != n: F(f"{form} atlas anim {an}")
        for k in range(1, n + 1):
            if not (os.path.exists(fr(c, k)) and os.path.exists(nf(c, k))): F(f"{form} missing {c} {k}"); continue
            if emd and not os.path.exists(os.path.join(emd, f"{c}_{k:02d}_emissive.png")): F(f"{form} missing emissive {c} {k}")
            a = load(fr(c, k)); nfr += 1; op = a[..., 3] == 255
            S = a.shape[0]; an = FA[c][k - 1]
            ispx = lambda arr_, cols: (arr_[..., :3][..., None, :] == np.array(cols)[None, None]).all(-1).any(-1) & op
            leafm = ispx(a, LEAF)
            if c == "leaf_umbrella":
                if k >= 2 and leafm.sum() < 8: F(f"{form} leaf too small {k} {leafm.sum()}")
                bad = False
                for key in ("eyeL", "eyeR", "mouth", "bulb"):
                    if key in an and an.get("faceVisible", True):
                        x, y = an[key]
                        if leafm[y, x]: bad = True; F(f"{form} leaf covers {key} {c} {k}")
                leaf_ok += not bad
            else:
                dm = ispx(a, [DROPD]); wm = ispx(a, [WHITE])
                if dm.sum() < 2: F(f"{form} shiver lines missing {k}")
                ok = dm.sum() >= 2
                if k in (2, 4):
                    # 白氣喺身體外（emissive 外）— 用 noface 層比對：白氣要喺 noface 都有
                    if not ispx(load(nf(c, k)), [WHITE]).any(): F(f"{form} shiver breath missing {k}"); ok = False
                shv_ok += ok
info.append(f"天氣 clip：{len(forms)} 形態 × 2 clip ＝ {nfr} 幀；撐葉冇遮五官／燈 {leaf_ok}；打冷震震線／白氣 {shv_ok}")
if byname.get("leaf_umbrella", {}).get("category") != "天氣" or byname.get("shiver", {}).get("category") != "天氣": F("category 天氣")
if byname.get("leaf_umbrella", {}).get("loopRange") != [2, 5] or byname.get("shiver", {}).get("loopRange") != [0, 3]: F("loopRange")
if "systems12B1" not in CL: F("CLIPS.systems12B1 missing")
for k in ("nuzzle_purr", "reunion_happy"):
    if k not in byname: F(f"s3 clip {k} lost")

# ---------------------------------------------------------------- UI
AJ = json.load(open(os.path.join(UI, "atlas_systems12_ui.json"))); AT = load(os.path.join(UI, "atlas_systems12_ui.png"))
WANT_UI = {"icon_star_shard_16": (16, 16), "icon_star_shard_32": (32, 32), "icon_commission_feed": None, "icon_commission_water": None, "icon_commission_play": None,
           "panel_commission_9s": None, "panel_commission_row_9s": None, "checkbox_empty": None, "checkbox_done": None, "bubble_thought_9s": None, "bubble_thought_tail": None,
           "diary_page_9s": None, "diary_page_special_9s": None, "sticker_sun": None, "sticker_rain": None, "sticker_food": None, "sticker_heart": None,
           "sticker_evolve": None, "sticker_sleep": None, "icon_remind_water": None, "icon_remind_sleep": None}
if set(AJ["frames"]) != set(WANT_UI): F(f"ui set {set(AJ['frames']) ^ set(WANT_UI)}")
if AJ["meta"].get("padding") != 2 or AJ["meta"].get("extrude") != 1: F("ui atlas meta")
for n, sz in WANT_UI.items():
    p = os.path.join(UI, n + ".png")
    if not os.path.exists(p): F(f"ui missing {n}"); continue
    im = Image.open(p); a = load(p)
    if im.mode != "RGBA": F(f"ui mode {n}")
    if not set(np.unique(a[..., 3]).tolist()) <= {0, 255}: F(f"ui alpha {n}")
    cs = {tuple(c) for c in np.unique(a[a[..., 3] == 255][:, :3], axis=0).tolist()}
    if cs - V3SET: F(f"ui offpalette {n}")
    if sz and im.size != sz: F(f"ui size {n} {im.size}")
    al = a[..., 3] > 0
    edge = np.zeros_like(al); edge[0] = edge[-1] = True; edge[:, 0] = edge[:, -1] = True
    ep = a[edge & al][:, :3]   # 掂邊嘅像素一定係描邊色（剪影冇被裁）
    if not n.endswith("_9s") and len(ep) and not (ep == np.array(V3["outline"])).all(-1).all(): F(f"ui clipped at edge {n}")
    fr_ = AJ["frames"].get(n)
    if fr_:
        r = fr_["frame"]; x, y, w, h = r["x"], r["y"], r["w"], r["h"]
        if not np.array_equal(AT[y:y + h, x:x + w], a): F(f"ui atlas px {n}")
        if not (np.array_equal(AT[y - 1, x:x + w], a[0]) and np.array_equal(AT[y:y + h, x - 1], a[:, 0])): F(f"ui extrude {n}")
        if n.endswith("_9s"):
            s = fr_.get("slice", {})
            if not (s and s["left"] + s["right"] < w and s["top"] + s["bottom"] < h): F(f"ui 9-slice {n} {s}")
info.append(f"UI {len(WANT_UI)} 件（v3 色盤／alpha／尺寸／atlas）")

# ---------------------------------------------------------------- weather
import build_systems12_b1_ui as U
base3 = json.load(open(os.path.join(SCN, "H3", "grade.json")))
for wk in ("overcast", "fog"):
    gp = os.path.join(SCN, "H3", f"grade_{wk}.json")
    if not os.path.exists(gp): F(f"grade_{wk} missing"); continue
    g = json.load(open(gp)); V.check_grade(g, f"H3/grade_{wk}.json")
    d = os.path.join(SCN, "H3", wk)
    for nm in ("sky", "far", "mid", "fore"):
        p = os.path.join(d, f"{nm}.png")
        if not os.path.exists(p): F(f"{wk} {nm} missing"); continue
        i_ = Image.open(p)
        if i_.size != (B.LW, B.LH) or i_.mode != "RGBA": F(f"{wk} {nm} size/mode")
        if nm == "sky" and load(p)[..., 3].min() != 255: F(f"{wk} sky not opaque")
    if Image.open(os.path.join(d, f"lut_{wk}.png")).size != (256, 16): F(f"lut_{wk} size")
    lut = np.asarray(Image.open(os.path.join(d, f"lut_{wk}.png"))).astype(float) / 255
    ref = B.make_lut(g)
    if np.abs(lut - ref).max() > 1.5 / 255: F(f"lut_{wk} != make_lut(grade_{wk}) Δ{np.abs(lut - ref).max() * 255:.2f}")
    raw = np.asarray(Image.open(os.path.join(SCN, "H3", "raw", "sky.png")).convert("RGBA")).astype(float) / 255
    raw = U.far_fade(raw, "sky", 0.45, "#e2e8ea") if wk == "fog" else U.far_fade(raw, "sky", 0.38, "#c8d0da")
    bk = np.asarray(Image.open(os.path.join(d, "sky.png")).convert("RGBA")).astype(float) / 255
    dl = np.abs(B.apply_lut(raw[..., :3], lut) - bk[..., :3]).max() * 255
    if dl > 2: F(f"{wk} sky != LUT(fade(raw)) Δ{dl:.2f}")
    for f in B.FORMS:
        for suf, sz in (("", (B.AW, B.AH)), ("_2x", (B.AW * 2, B.AH * 2))):
            p = os.path.join(d, f"mockup_{wk}_{f}{suf}.png")
            if not os.path.exists(p) or Image.open(p).size != sz: F(f"mockup {wk} {f}{suf}")
WJ = json.load(open(os.path.join(SCN, "weather", "weather.json")))
if WJ.get("weights") != {"clear": 60, "overcast": 20, "rain": 15, "fog": 5}: F("weather weights")
for k in ("overcast_clouds", "fog_bank"):
    p = os.path.join(SCN, "weather", WJ[k]["image"]); a = load(p)
    if list(Image.open(p).size) != WJ[k]["size"]: F(f"{k} size")
    if not set(np.unique(a[..., 3]).tolist()) <= {0, 255}: F(f"{k} alpha")
    if a.shape[1] != B.LW: F(f"{k} width != layer width (wrapX)")
fb = load(os.path.join(SCN, "weather", "fog_bank.png"))
for y0 in (0, 72):   # 霧帶上下 2 行要透明（冇硬邊）
    band = fb[y0:y0 + 72, :, 3]
    if band[0].any() or band[-1].any(): F(f"fog band hard edge y0={y0}")
info.append(f"天氣 陰／霧：grade＋層＋LUT＋mockup；tile {list(WJ)[:2]}")

# ---------------------------------------------------------------- seasons
SJ = json.load(open(os.path.join(SCN, "seasons", "seasons.json")))
months = sorted(m for s in SJ["seasons"].values() for m in s["months"])
if months != list(range(1, 13)): F(f"season months {months}")
if {k: v["months"] for k, v in SJ["seasons"].items()} != {"spring": [3, 4, 5], "summer": [6, 7, 8], "autumn": [9, 10, 11], "winter": [12, 1, 2]}: F("HK season months")
ns = 0
for sk in SJ["seasons"]:
    S = dict(U.SEASONS[sk])
    for key in ("H1", "H2", "H3", "H4"):
        d = os.path.join(SCN, "seasons", sk, key); g = json.load(open(os.path.join(d, "grade.json")))
        V.check_grade(g, f"seasons/{sk}/{key}/grade.json")
        vg = json.load(open(os.path.join(SCN, key, "grade.json")))
        V.check_layerset(d, key, g, "lut.png", sub=f"/seasons/{sk}")
        lut = np.asarray(Image.open(os.path.join(d, "lut.png"))).astype(float) / 255; ref = U.season_lut(vg, S)
        if lut.shape != (16, 256, 3): F(f"season lut shape {sk}/{key}")
        if np.abs(lut - ref).max() > 1.5 / 255: F(f"season lut formula {sk}/{key} Δ{np.abs(lut - ref).max() * 255:.2f}")
        raw = np.asarray(Image.open(os.path.join(SCN, key, "raw", "sky.png")).convert("RGB")).astype(float) / 255
        bk = np.asarray(Image.open(os.path.join(d, "sky.png")).convert("RGB")).astype(float) / 255
        dl = np.abs(B.apply_lut(raw, lut) - bk).max() * 255
        if dl > 2: F(f"season sky {sk}/{key} Δ{dl:.2f}")
        lm = Image.open(os.path.join(d, "lightmap.png"))
        if lm.size != (B.LW, B.LH) or lm.mode != "RGB": F(f"season lightmap {sk}/{key}")
        ns += 1
info.append(f"季節 {ns} 套（4 季 × H1–H4；香港月份）")
if V.res["FAIL"]: F(f"hd2d schema checks FAIL {V.res['FAIL']}")
info.append(f"hd2d schema 檢查 PASS {V.res['PASS']} FAIL {V.res['FAIL']}")
for i in info: print(i)
for f_ in fails[:60]: print("FAIL", f_)
print(f"FAIL {len(fails)}"); print("ALL PASS" if not fails else "HAS FAIL")
sys.exit(1 if fails else 0)
