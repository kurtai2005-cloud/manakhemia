#!/usr/bin/env python3
"""validate_lumi.py — 螢絨 (lumi) 動畫交付驗證（獨立於 build；validate_liveliness.py 結尾會調用）。
檢查：lumi 31 色、alpha 0/255、64×64、clip／幀數（std23 23 clip ＋ picked_up ＝ 24/102；MVP 12/46）、邊界唔掂 64px 邊、
錨點齊全＋界內、noface+faceov == 完整幀、picked_up 完整幀 == noface + kit（按錨點）、
emissive == 完整幀內 fly/fly_core 像素（白／透明）、atlas ≤1024²／padding 2／extrude 1／無重疊／像素＝散檔、
pivotPx（身體 (32,61)；picked_up＝grab）、atlas_lumi_emissive 同 layout 且像素＝ emissive 散檔、
CLIPS.json anchors.lumi == face_anchors_lumi.json、pose 參數＝radiant（同名 clip 同幀數）。"""
import json, os, sys, glob
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
TR = os.path.normpath(os.path.join(HERE, "..", "sprites", "tuanrong")); MOT = os.path.join(TR, "motion"); LU = os.path.join(TR, "lumi")
MVP = {"idle": 4, "blink": 4, "walk": 6, "play": 6, "eat": 4, "sleep_loop": 4, "emo_happy": 2, "emo_hungry": 2, "emo_sleepy": 2, "celebrate": 4, "droop": 6, "sick": 2}
EXTRA = {"picked_up": 6, "fall_asleep": 4, "wake": 4}
STD23_ADD = {"sway": 4, "yawn": 4, "emo_wantplay": 2, "emo_cuddly": 2, "emo_surprised": 2, "cheer_jump": 6, "catch_reach": 6, "sunbathe": 8, "pot_bump": 8}
WANT = {**MVP, **EXTRA, **STD23_ADD}   # std23 全套 23 clip ＋ picked_up ＝ 24 clip／102 幀
KEYS = ("eyeL", "eyeR", "mouth", "head_r", "bulb", "faceVisible", "face")
MOVING = ("neutral", "surprised", "squint", "angry", "sad")
S = 64; PIV = (32, 61)

def run():
    fails = []; info = []; F = fails.append
    load = lambda p: np.array(Image.open(p).convert("RGBA"))
    pal = json.load(open(os.path.join(LU, "palette_lumi.json")))
    cols = pal["colors"]
    PAL = {tuple(int(c["hex"][i:i + 2], 16) for i in (1, 3, 5)) for c in cols}
    if len(cols) != 31: F(f"palette size {len(cols)}")
    EM = {tuple(int(c["hex"][i:i + 2], 16) for i in (1, 3, 5)) for c in cols if c.get("emissive")}
    if not EM:   # fallback by name
        EM = {tuple(int(c["hex"][i:i + 2], 16) for i in (1, 3, 5)) for c in cols if c["name"] in ("fly", "fly_core")}
    def chk(p, size=None, emissive=False):
        im = Image.open(p)
        if im.mode != "RGBA": F(f"mode {im.mode} {p}")
        a = np.array(im.convert("RGBA"))
        if not set(np.unique(a[..., 3]).tolist()) <= {0, 255}: F(f"alpha {p}")
        px = a[a[..., 3] == 255][:, :3]
        if len(px):
            got = {tuple(c) for c in np.unique(px, axis=0).tolist()}
            bad = got - ({(255, 255, 255)} if emissive else PAL)
            if bad: F(f"offpalette {os.path.relpath(p, TR)} {sorted(bad)[:2]}")
        if size and im.size != size: F(f"size {p} {im.size}")
        return a
    n = 0
    for p in glob.glob(LU + "/**/*.png", recursive=True):
        rel = os.path.relpath(p, LU)
        if rel.startswith(("preview", "contact", "compare")): continue
        top = rel.split("/")[0]
        chk(p, (S, S) if top in ("frames", "layers", "emissive") else None, emissive=top == "emissive"); n += 1
    info.append(f"[lumi] PNG 檢查 {n} 個（lumi 色盤／alpha／尺寸）")
    CL = json.load(open(os.path.join(MOT, "CLIPS.json")))
    FAJ = json.load(open(os.path.join(LU, "face_anchors_lumi.json"))); FA = FAJ["anchors"]
    if "lumi" not in CL.get("forms", {}): F("CLIPS.json forms.lumi missing")
    byname = {c["name"]: c for c in CL["clips"]}
    for cn, nf in WANT.items():
        if cn not in FA: F(f"missing clip {cn}"); continue
        if len(FA[cn]) != nf: F(f"frame count {cn} {len(FA[cn])}!={nf}")
        if byname.get(cn, {}).get("anchors", {}).get("lumi") != FA[cn]: F(f"CLIPS anchors.lumi != face_anchors_lumi {cn}")
        if byname[cn]["frames"] != nf: F(f"radiant pose frame count differs {cn}")
    extra = set(FA) - set(WANT)
    if extra: F(f"unexpected clips {extra}")
    tot = sum(len(v) for v in FA.values())
    info.append(f"[lumi] clip {len(FA)}／幀 {tot}（MVP {sum(len(FA[c]) for c in MVP if c in FA)} 幀；std23 補 {sum(len(FA[c]) for c in STD23_ADD if c in FA)} 幀）")
    std23 = CL["forms"].get("lumi", {}).get("std23", [])
    if std23 and set(std23) - set(FA): F(f"std23 clips missing {set(std23) - set(FA)}")
    # kit
    aj = json.load(open(os.path.join(TR, "atlas_lumi.json")))
    kit = {os.path.basename(p)[:-4]: load(p) for p in glob.glob(LU + "/kit/*.png")}
    kpiv = {k: (aj["frames"][k]["pivotPx"]["x"], aj["frames"][k]["pivotPx"]["y"]) for k in kit}
    def place(img, name, at):
        a = kit[name]; x0, y0 = at[0] - kpiv[name][0], at[1] - kpiv[name][1]
        for yy, xx in zip(*np.nonzero(a[..., 3])):
            if 0 <= y0 + yy < S and 0 <= x0 + xx < S: img[y0 + yy, x0 + xx] = a[yy, xx]
    recon = recon_new = em_ok = 0
    for cn, A in FA.items():
        for k, an in enumerate(A, 1):
            for key in KEYS:
                if key not in an: F(f"missing {key} {cn} {k}")
            if cn == "picked_up" and "grab" not in an: F(f"missing grab {cn} {k}")
            for key in ("eyeL", "eyeR", "mouth", "head_r", "bulb", "bulb2", "tail") + (("grab",) if "grab" in an else ()):
                if key not in an: continue
                x, y = an[key]
                if not (isinstance(x, int) and isinstance(y, int) and 0 <= x < S and 0 <= y < S): F(f"anchor out {cn} {k} {key} {an[key]}")
            fr = os.path.join(LU, "frames", f"{cn}_{k:02d}.png")
            nf = os.path.join(LU, "layers", f"{cn}_{k:02d}_noface.png"); ov = os.path.join(LU, "layers", f"{cn}_{k:02d}_faceov.png")
            ef = os.path.join(LU, "emissive", f"{cn}_{k:02d}_emissive.png")
            if not all(os.path.exists(x) for x in (fr, nf, ov, ef)): F(f"missing file {cn} {k}"); continue
            full = load(fr); body = load(nf); o = load(ov)
            al = full[..., 3] > 0
            if al[0].any() or al[:, 0].any() or al[:, -1].any(): F(f"frame touches edge {cn} {k}")
            comp = body.copy(); m = o[..., 3] == 255; comp[m] = o[m]
            if np.array_equal(comp, full): recon += 1
            else: F(f"noface+faceov != full {cn} {k}")
            # emissive mask == fly/fly_core pixels of full frame
            want = np.zeros(full.shape[:2], bool)
            for c in EM: want |= (full[..., 3] == 255) & (full[..., :3] == c).all(-1)
            e = load(ef)
            if np.array_equal(e[..., 3] == 255, want) and (e[e[..., 3] == 255][:, :3] == 255).all(): em_ok += 1
            else: F(f"emissive mismatch {cn} {k}")
            if not want.any() and cn != "sick": F(f"no glow {cn} {k}")
            if cn == "picked_up":
                fa = an["face"]; img = body.copy()
                if fa and an["faceVisible"]:
                    g = fa.get("gaze", "C"); eL = fa["eyes"]; eR = fa.get("eyesR", eL)
                    nm = lambda st, sd: f"eyes_{st}_{g if st in MOVING else 'C'}_{sd}"
                    place(img, nm(eL, "l"), an["eyeL"]); place(img, nm(eR, "r"), an["eyeR"]); place(img, "mouth_" + fa["mouth"], an["mouth"])
                if np.array_equal(img, full): recon_new += 1
                else: F(f"kit compose != full {cn} {k}")
    info.append(f"[lumi] noface+faceov＝完整幀 {recon}；picked_up kit 合成＝完整幀 {recon_new}；emissive 遮罩吻合 {em_ok}")
    # glow animates: tail/dots differ across idle frames
    em_idle = [load(os.path.join(LU, "emissive", f"idle_{k:02d}_emissive.png"))[..., 3].sum() for k in range(1, 5)]
    if len(set(em_idle)) < 2: F("idle emissive static (no pulse/twinkle)")
    # atlases
    for png, em in (("atlas_lumi.png", False), ("atlas_lumi_emissive.png", True)):
        im = load(os.path.join(TR, png)); H, W = im.shape[:2]
        if W != 1024 or H > 1024: F(f"atlas size {png} {W}x{H}")
        if not em:
            if aj["meta"].get("padding") != 2 or aj["meta"].get("extrude") != 1: F("atlas meta pad/extrude")
        rects = [(k, v["frame"]) for k, v in aj["frames"].items()]
        for i, (k, r) in enumerate(rects):
            x, y, w, h = r["x"], r["y"], r["w"], r["h"]
            if x < 2 or y < 2 or x + w > W - 2 or y + h > H - 2: F(f"bounds {k}")
            if not em:
                for k2, r2 in rects[i + 1:]:
                    if not (x + w + 2 <= r2["x"] or r2["x"] + r2["w"] + 2 <= x or y + h + 2 <= r2["y"] or r2["y"] + r2["h"] + 2 <= y): F(f"overlap {k} {k2}")
            if "_noface_" in k:
                c, nn = k.rsplit("_noface_", 1); src = os.path.join(LU, "layers", f"{c}_{nn}_noface.png")
                if em: src = os.path.join(LU, "emissive", f"{c}_{nn}_noface_emissive.png")
            elif k.startswith(("eyes_", "mouth_", "bulb_")):
                src = os.path.join(LU, "kit", k + ".png")
            else:
                src = os.path.join(LU, "frames", k + ".png")
                if em: src = os.path.join(LU, "emissive", k + "_emissive.png")
            s = load(src)
            if em and k.startswith(("eyes_", "mouth_", "bulb_")):
                m = np.zeros_like(s)
                for c in EM: m[(s[..., 3] == 255) & (s[..., :3] == c).all(-1)] = (255, 255, 255, 255)
                s = m
            if not np.array_equal(im[y:y + h, x:x + w], s): F(f"atlas px != src {png} {k}")
            if not np.array_equal(im[y - 1, x:x + w], s[0]) or not np.array_equal(im[y:y + h, x - 1], s[:, 0]) \
               or not np.array_equal(im[y + h, x:x + w], s[-1]) or not np.array_equal(im[y:y + h, x + w], s[:, -1]): F(f"extrude {png} {k}")
            if not em and not k.startswith(("eyes_", "mouth_", "bulb_")):
                base = k.rsplit("_noface_", 1)[0] if "_noface_" in k else k.rsplit("_", 1)[0]
                fi = int(k.rsplit("_", 1)[1]) - 1
                want = tuple(FA[base][fi]["grab"]) if base == "picked_up" else PIV
                pv = aj["frames"][k]["pivotPx"]
                if (pv["x"], pv["y"]) != want: F(f"pivot {k} {pv} want {want}")
        info.append(f"[lumi] {png} {W}x{H} {len(rects)} 塊")
    for an_name, a in aj["animations"].items():
        for fr in a["frames"]:
            if fr not in aj["frames"]: F(f"anim frame missing {an_name} {fr}")
    if aj["animations"].get("picked_up", {}).get("pivot") != "grab": F("picked_up anim pivot != grab")
    return fails, info

if __name__ == "__main__":
    fails, info = run()
    print("\n".join(info)); print("FAIL", len(fails)); [print(" -", f) for f in fails[:40]]
    print("ALL PASS" if not fails else "FAILED"); sys.exit(1 if fails else 0)
