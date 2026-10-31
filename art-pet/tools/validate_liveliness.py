#!/usr/bin/env python3
"""validate_liveliness.py — 團絨生命感交付驗證。
檢查：色盤（31 色）、alpha 0/255、尺寸、pivot、錨點齊全、noface+faceov == 原幀（逐像素）、
新 clip 完整幀 == noface + kit（按錨點）、atlas ≤1024／無重疊／padding 2／extrude 1／像素同散檔一致、
舊 open/smile 幀用 kit neutral 重疊嘅吻合度；另調用 validate_lumi.py（螢絨）。"""
import json, os, sys, glob
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
MOT = os.path.normpath(os.path.join(HERE, "..", "sprites", "tuanrong", "motion")); LV = os.path.join(MOT, "liveliness")
pal = json.load(open(os.path.join(MOT, "palette.json")))
PALSET = {tuple(int(c["hex"][i:i + 2], 16) for i in (1, 3, 5)) for c in pal["colors"]}
FORMS = {"sprout": 32, "radiant": 64, "soft": 64}
KEYS = ("eyeL", "eyeR", "mouth", "head_r", "bulb", "faceVisible")
fails = []; info = []
def F(msg): fails.append(msg)
def load(p): return np.array(Image.open(p).convert("RGBA"))
def chk_png(p, size=None):
    im = Image.open(p)
    if im.mode != "RGBA": F(f"mode {im.mode} {p}")
    a = np.array(im.convert("RGBA"))
    if not set(np.unique(a[..., 3]).tolist()) <= {0, 255}: F(f"alpha {p}")
    px = a[a[..., 3] == 255][:, :3]
    if len(px):
        bad = {tuple(c) for c in np.unique(px, axis=0).tolist()} - PALSET
        if bad: F(f"offpalette {p} {sorted(bad)[:2]}")
    if size and im.size != size: F(f"size {p} {im.size}")
    return a
def over(base, top):
    out = base.copy(); m = top[..., 3] == 255; out[m] = top[m]; return out

CL = json.load(open(os.path.join(MOT, "CLIPS.json")))
FA = json.load(open(os.path.join(LV, "face_anchors.json")))["anchors"]
PIVOT_OV = {c["name"]: c["pivot"] for c in CL["clips"] if c.get("pivot")}
FAJ = json.load(open(os.path.join(LV, "face_anchors.json")))
if FAJ.get("pivotOverride", {}) != PIVOT_OV: F(f"pivotOverride mismatch CLIPS {PIVOT_OV} vs face_anchors {FAJ.get('pivotOverride')}")
for cn, key in PIVOT_OV.items():
    if key != "grab": F(f"unknown pivot override {cn} {key}")
pov_n = [0]
pngs = 0
for p in glob.glob(LV + "/**/*.png", recursive=True):
    rel = os.path.relpath(p, LV)
    if rel.startswith(("preview", "contact", "kit_", "live_s2_contact", "live_s3_contact")) or "_backup" in rel: continue
    form = next((f for f in FORMS if f"/{f}/" in "/" + rel), None)
    sz = (FORMS[form],) * 2 if form and rel.split("/")[0] in ("layers", "frames") else None
    chk_png(p, sz); pngs += 1
info.append(f"PNG 檢查 {pngs} 個（色盤／alpha／尺寸）")

recon = 0; recon_new = 0; anc_n = 0; kitfit = []
for form, S in FORMS.items():
    piv = (S // 2, S - 3)
    kit = {}
    for p in glob.glob(f"{LV}/kit/{form}/*.png"): kit[os.path.basename(p)[:-4]] = load(p)
    aj = {}
    for js in glob.glob(f"{LV}/atlas_{form}_live*.json"): aj.update(json.load(open(js))["frames"])
    kpiv = {k: (aj[k]["pivotPx"]["x"], aj[k]["pivotPx"]["y"]) for k in kit}
    def place(img, name, at):
        a = kit[name]; x0, y0 = at[0] - kpiv[name][0], at[1] - kpiv[name][1]
        h, w = a.shape[:2]
        for yy in range(h):
            for xx in range(w):
                if a[yy, xx, 3] and 0 <= y0 + yy < S and 0 <= x0 + xx < S: img[y0 + yy, x0 + xx] = a[yy, xx]
    for c in CL["clips"]:
        n = c["name"]; A = c.get("anchors", {}).get(form)
        if A is None: F(f"no anchors {form} {n}"); continue
        if A != FA[form][n]: F(f"face_anchors mismatch {form} {n}")
        if len(A) != c["frames"]: F(f"anchor count {form} {n} {len(A)}!={c['frames']}")
        for k, an in enumerate(A, 1):
            anc_n += 1
            for key in KEYS:
                if key not in an: F(f"missing {key} {form} {n} {k}")
            if not isinstance(an["faceVisible"], bool): F(f"faceVisible type {form} {n}")
            if c.get("pivot") == "grab" and "grab" not in an: F(f"missing grab {form} {n} {k}")
            for key in KEYS[:5] + (("grab",) if "grab" in an else ()):
                x, y = an[key]
                if not (isinstance(x, int) and isinstance(y, int) and 0 <= x < S and 0 <= y < S): F(f"anchor out {form} {n} {k} {key} {an[key]}")
            nf = os.path.join(LV, "layers", form, f"{n}_{k:02d}_noface.png"); ov = os.path.join(LV, "layers", form, f"{n}_{k:02d}_faceov.png")
            if not (os.path.exists(nf) and os.path.exists(ov)): F(f"missing layer {form} {n} {k}"); continue
            body = load(nf); comp = over(body, load(ov))
            orig = os.path.join(MOT, "frames", form, f"{n}_{k:02d}.png")
            if not os.path.exists(orig): orig = os.path.join(LV, "frames", form, f"{n}_{k:02d}.png"); new = True
            else: new = False
            if not np.array_equal(comp, load(orig)): F(f"recon != original {form} {n} {k}")
            else: recon += 1
            fa = an.get("face")
            if new:   # full frame must equal noface + kit at anchors
                img = body.copy()
                if fa and an["faceVisible"]:
                    g = fa.get("gaze", "C")
                    eL, eR = fa["eyes"], fa.get("eyesR", fa["eyes"])
                    nm = lambda st, sd: f"eyes_{st}_{g if st in ('neutral','surprised','squint','angry','sad') else 'C'}_{sd}"
                    place(img, nm(eL, "l"), an["eyeL"]); place(img, nm(eR, "r"), an["eyeR"]); place(img, "mouth_" + fa["mouth"], an["mouth"])
                if np.array_equal(img, load(orig)): recon_new += 1
                else: F(f"kit compose != full {form} {n} {k}")
                if not an["faceVisible"] and (load(ov)[..., 3] > 0).any(): F(f"face drawn on hidden {form} {n} {k}")
            elif fa and fa.get("src") in ("open/smile",):
                img = body.copy(); place(img, "eyes_neutral_C_l", an["eyeL"]); place(img, "eyes_neutral_C_r", an["eyeR"]); place(img, "mouth_neutral", an["mouth"])
                o = load(orig); facepx = (load(ov)[..., 3] > 0) | ((img != body).any(-1))
                agree = (img == o).all(-1)[facepx].mean() if facepx.any() else 1.0
                kitfit.append((form, n, k, round(float(agree), 3)))
    # atlas
    for js in glob.glob(f"{LV}/atlas_{form}_live*.json"):
        d = json.load(open(js)); im = load(js.replace(".json", ".png")); H, W = im.shape[:2]
        if W > 1024 or H > 1024: F(f"atlas too big {js} {W}x{H}")
        if d["meta"].get("padding") != 2 or d["meta"].get("extrude") != 1: F("atlas meta pad/extrude")
        rects = [(k, v["frame"]) for k, v in d["frames"].items()]
        for i, (k, r) in enumerate(rects):
            if r["x"] < 2 or r["y"] < 2 or r["x"] + r["w"] > W - 2 or r["y"] + r["h"] > H - 2: F(f"bounds {k}")
            for k2, r2 in rects[i + 1:]:
                if not (r["x"] + r["w"] + 2 <= r2["x"] or r2["x"] + r2["w"] + 2 <= r["x"] or r["y"] + r["h"] + 2 <= r2["y"] or r2["y"] + r2["h"] + 2 <= r["y"]): F(f"overlap {k} {k2}")
            # pixels == source file
            if "_noface_" in k:
                clip, nn = k.rsplit("_noface_", 1); src = os.path.join(LV, "layers", form, f"{clip}_{nn}_noface.png")
            elif k.startswith(("eyes_", "mouth_", "bulb_")): src = os.path.join(LV, "kit", form, k + ".png")
            else: src = os.path.join(LV, "frames", form, k + ".png")
            s = load(src); x, y, w, h = r["x"], r["y"], r["w"], r["h"]
            if not np.array_equal(im[y:y + h, x:x + w], s): F(f"atlas px != src {k}")
            if not np.array_equal(im[y - 1, x:x + w], s[0]) or not np.array_equal(im[y:y + h, x - 1], s[:, 0]): F(f"extrude {k}")
            pv = d["frames"][k]["pivotPx"]
            if not k.startswith(("eyes_", "mouth_", "bulb_")):
                base = k.rsplit("_noface_", 1)[0] if "_noface_" in k else k.rsplit("_", 1)[0]
                fi = int(k.rsplit("_", 1)[1]) - 1
                if base in PIVOT_OV:   # clip pivot override (e.g. picked_up -> anchors.grab)
                    want = tuple(FA[form][base][fi][PIVOT_OV[base]]); pov_n[0] += 1
                else: want = piv
                if (pv["x"], pv["y"]) != want: F(f"pivot {k} {pv} want {want}")
        for an_name, a in d["animations"].items():
            for fr in a["frames"]:
                if fr not in d["frames"]: F(f"anim frame missing {an_name} {fr}")
        info.append(f"atlas {os.path.basename(js)} {W}x{H} {len(rects)} 塊")
    # pivot sanity: body feet bottom row near pivot on non-lifted new frames
# new clips listed with meta
for c in CL["clips"]:
    if c.get("category") == "生命感":
        for key in ("fps", "loop", "priority", "trigger"):
            if key not in c: F(f"meta {c['name']} {key}")
# 生命感第二段 (s2)：clip 規格、獨立 atlas、hold、fx bug
S2_SPEC = {"smug_pose": (4, 6), "act_cool": (4, 5), "lookup_tip": (4, 6), "getup": (4, 6), "sniff_itch": (2, 6)}
byname = {c["name"]: c for c in CL["clips"]}
for form, S in FORMS.items():
    s2 = {}
    for js in glob.glob(f"{LV}/atlas_{form}_live_s2*.json"): s2.update(json.load(open(js))["animations"])
    main = json.load(open(f"{LV}/atlas_{form}_live.json"))
    for n, (nf, fps) in S2_SPEC.items():
        c = byname.get(n)
        if not c: F(f"s2 clip missing in CLIPS {n}"); continue
        if c["frames"] != nf or c["fps"] != fps: F(f"s2 spec {n} {c['frames']}/{c['fps']} want {nf}/{fps}")
        if len(c["anchors"][form]) != nf: F(f"s2 anchors {form} {n}")
        for an_ in (n, n + "_noface"):
            if an_ not in s2 or len(s2[an_]["frames"]) != nf: F(f"s2 atlas anim {form} {an_}")
            if an_ in main["animations"]: F(f"s2 clip leaked into main atlas {form} {an_}")
        for k in range(1, nf + 1):
            if not os.path.exists(os.path.join(LV, "frames", form, f"{n}_{k:02d}.png")): F(f"s2 full missing {form} {n} {k}")
if byname.get("smug_pose", {}).get("holdLast_s") != 0.8: F("smug_pose holdLast_s != 0.8")
# 生命感第三段 (s3)：nuzzle_purr／reunion_happy，獨立 atlas_<form>_live_s3（build_tuanrong_live_s3.py）
S3_SPEC = {"nuzzle_purr": (4, 6, True), "reunion_happy": (5, 8, False)}
for form, S in FORMS.items():
    s3 = {}
    for js in glob.glob(f"{LV}/atlas_{form}_live_s3*.json"): s3.update(json.load(open(js))["animations"])
    if not s3: F(f"s3 atlas missing {form}"); continue
    other = dict(json.load(open(f"{LV}/atlas_{form}_live.json"))["animations"])
    for js in glob.glob(f"{LV}/atlas_{form}_live_s2*.json"): other.update(json.load(open(js))["animations"])
    for n, (nf, fps, loop) in S3_SPEC.items():
        c = byname.get(n)
        if not c: F(f"s3 clip missing in CLIPS {n}"); continue
        if c["frames"] != nf or c["fps"] != fps or c["loop"] != loop: F(f"s3 spec {n} {c['frames']}/{c['fps']}/{c['loop']} want {nf}/{fps}/{loop}")
        if c.get("category") != "生命感" or c.get("phase") != 3: F(f"s3 meta {n}")
        if len(c["anchors"][form]) != nf: F(f"s3 anchors {form} {n}")
        for an_ in (n, n + "_noface"):
            if an_ not in s3 or len(s3[an_]["frames"]) != nf or s3[an_].get("fps") != fps: F(f"s3 atlas anim {form} {an_}")
            if an_ in other: F(f"s3 clip leaked into s1/s2 atlas {form} {an_}")
        for k in range(1, nf + 1):
            if not os.path.exists(os.path.join(LV, "frames", form, f"{n}_{k:02d}.png")): F(f"s3 full missing {form} {n} {k}")
info.append(f"第三段 clip：{', '.join(f'{n} {v[0]}幀/{v[1]}fps' for n, v in S3_SPEC.items())}（3 form，atlas_<form>_live_s3）")
fxj = os.path.join(LV, "fx", "atlas_fx_live.json")
if not os.path.exists(fxj): F("fx bug atlas missing")
else:
    d = json.load(open(fxj)); im = load(fxj.replace(".json", ".png"))
    fr = d["animations"].get("fx_bug", {}).get("frames", [])
    if not (2 <= len(set(fr)) <= 3) or d["animations"]["fx_bug"].get("fps") != 10: F("fx bug anim spec")
    for k, v in d["frames"].items():
        a = chk_png(os.path.join(LV, "fx", k + ".png"), (8, 8)); r = v["frame"]
        if not np.array_equal(im[r["y"]:r["y"] + r["h"], r["x"]:r["x"] + r["w"]], a): F(f"fx atlas px {k}")
    info.append(f"fx bug：{len(d['frames'])} 幀 8×8，anim {fr}")
info.append(f"第二段 clip：{', '.join(f'{n} {v[0]}幀/{v[1]}fps' for n, v in S2_SPEC.items())}（3 form，atlas_<form>_live_s2）")
info.append(f"pivot override：{PIVOT_OV}；atlas 幀 pivotPx＝grab 已核 {pov_n[0]} 塊")
info.append(f"錨點 {anc_n} 幀；noface+faceov＝原幀 {recon}；新 clip kit 合成＝完整幀 {recon_new}")
if kitfit:
    v = [x[3] for x in kitfit]
    info.append(f"舊 open/smile 幀用 kit neutral 重疊吻合度：{len(v)} 幀，100% {sum(1 for t in v if t == 1.0)}，最低 {min(v)}（shear 幀預期 <1）")
# 螢絨 lumi（隱藏稀有成年形態）覆蓋：見 validate_lumi.py
if os.path.exists(os.path.join(MOT, "..", "atlas_lumi.json")):
    sys.path.insert(0, HERE); import validate_lumi
    lf, li = validate_lumi.run(); fails += lf; info += li
else: F("atlas_lumi.json missing (run build_lumi.py)")
print("\n".join(info))
print("FAIL", len(fails)); [print(" -", f) for f in fails[:40]]
print("ALL PASS" if not fails else "FAILED")
sys.exit(1 if fails else 0)
