#!/usr/bin/env python3
"""validate_liveliness.py — 團絨生命感交付驗證。
檢查：色盤（31 色）、alpha 0/255、尺寸、pivot、錨點齊全、noface+faceov == 原幀（逐像素）、
新 clip 完整幀 == noface + kit（按錨點）、atlas ≤1024／無重疊／padding 2／extrude 1／像素同散檔一致、
舊 open/smile 幀用 kit neutral 重疊嘅吻合度。"""
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
    if rel.startswith(("preview", "contact", "kit_")) or "_backup" in rel: continue
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
info.append(f"pivot override：{PIVOT_OV}；atlas 幀 pivotPx＝grab 已核 {pov_n[0]} 塊")
info.append(f"錨點 {anc_n} 幀；noface+faceov＝原幀 {recon}；新 clip kit 合成＝完整幀 {recon_new}")
if kitfit:
    v = [x[3] for x in kitfit]
    info.append(f"舊 open/smile 幀用 kit neutral 重疊吻合度：{len(v)} 幀，100% {sum(1 for t in v if t == 1.0)}，最低 {min(v)}（shear 幀預期 <1）")
print("\n".join(info))
print("FAIL", len(fails)); [print(" -", f) for f in fails[:40]]
print("ALL PASS" if not fails else "FAILED")
sys.exit(1 if fails else 0)
