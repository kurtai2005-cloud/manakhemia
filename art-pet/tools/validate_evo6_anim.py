#!/usr/bin/env python3
"""validate_evo6_anim.py — 團絨 evo6 動畫交付驗證（獨立於 build，只讀檔案）。
batch A（光卵／絨點／絨芽／絨跳）必驗；batch B（守夜者 44 ×4）／C（靜光 48 ×4 MVP）喺 CLIPS.json 有 evo6B／evo6C 段就必驗齊 4 分支
（分支各自色盤＝atlas meta palette；emissive 色＝meta emissiveColors；燈 bulb 錨點：絨跳＋守夜者＋靜光必有，bulb2／tail 可選）。
檢查：基本 31 色（palette.json）、alpha 0/255（無 AA）、尺寸（24/28/32/38）、pivot（身體 (w/2,h-3)；picked_up＝grab）、
錨點齊全＋界內（bulb 只限絨跳；光卵 faceVisible=false）、幀數 == CLIPS.json == face_anchors、CLIPS anchors == face_anchors、
noface+faceov == 完整幀、生命感新 clip 完整幀 == noface + kit（按錨點，含 bulb）、emissive == glow_core/glow_mid 像素、
atlas 1024 闊／padding 2／extrude 1／無重疊／像素＝散檔／pivotPx、emissive atlas 同 layout、frame 唔掂邊（四邊）。"""
import json, os, sys, glob
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
TR = os.path.normpath(os.path.join(HERE, "..", "sprites", "tuanrong")); MOT = os.path.join(TR, "motion"); EV = os.path.join(TR, "evo6")
SIZES = {"evo_egg": 24, "evo_dot": 28, "evo_sprout": 32, "evo_hop": 38}
BRANCHES = ("lumi", "radiant", "soft", "dust")
GUARD = {f"evo_guard_{b}": 44 for b in BRANCHES}; STILL = {f"evo_still_{b}": 48 for b in BRANCHES}
STILL_MVP = ["idle", "blink", "emo_happy", "fall_asleep", "sleep_loop", "wake", "picked_up"]
S3 = ["nuzzle_purr", "reunion_happy"]
EGG_WANT = {"idle": 4, "glow": 2, "tap": 4, "hatch": 6, "picked_up": 4}
LIVE_S2 = ("smug_pose", "act_cool", "lookup_tip", "getup", "sniff_itch")
MOVING = ("neutral", "surprised", "squint", "angry", "sad")
KIT_PREFIX = ("eyes_", "mouth_", "bulb_")
load = lambda p: np.array(Image.open(p).convert("RGBA"))

def run():
    fails = []; info = []; F = fails.append
    pp = next((p for p in (os.path.join(MOT, "palette.json"), os.path.join(TR, "palette.json")) if os.path.exists(p)), None)
    if not pp: return [f"palette.json not found (motion/ or tuanrong/)"], info
    pal = json.load(open(pp))["colors"]
    hx = lambda h: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
    PAL = {hx(c["hex"]) for c in pal}
    EM = {hx(c["hex"]) for c in pal if c["name"] in ("glow_core", "glow_mid")}
    if len(pal) != 31: F(f"palette size {len(pal)}")
    if len(EM) != 2: F("emissive colours not found in palette")
    CL = json.load(open(os.path.join(MOT, "CLIPS.json"))); byname = {c["name"]: c for c in CL["clips"]}
    for k in ("evo6",):
        if k not in CL: F("CLIPS.json evo6 section missing")
    if "evo6B" in CL: SIZES.update(GUARD)
    if "evo6C" in CL: SIZES.update(STILL)
    BASE_PAL, BASE_EM = PAL, EM
    def load_pal(fn, emn):
        """分支色盤（evo6/<palette>）＋emissive 色名 → (PAL, EM)"""
        if not fn or fn == "palette_base.json" and not os.path.exists(os.path.join(EV, fn)): return BASE_PAL, BASE_EM
        p_ = os.path.join(EV, fn)
        if not os.path.exists(p_): F(f"palette file missing evo6/{fn}"); return BASE_PAL, BASE_EM
        cl = json.load(open(p_))["colors"]
        if len(cl) != 31: F(f"palette size {fn} {len(cl)}")
        em_ = {hx(c["hex"]) for c in cl if c["name"] in emn}
        if len(em_) != len(emn): F(f"emissive colours {emn} not in {fn}")
        return {hx(c["hex"]) for c in cl}, em_
    def chk(p, size=None, emissive=False, PAL=None):
        PAL = PAL or BASE_PAL
        im = Image.open(p)
        if im.mode != "RGBA": F(f"mode {im.mode} {p}")
        a = np.array(im.convert("RGBA"))
        if not set(np.unique(a[..., 3]).tolist()) <= {0, 255}: F(f"alpha not 0/255 {os.path.relpath(p, TR)}")
        px = a[a[..., 3] == 255][:, :3]
        if len(px):
            got = {tuple(c) for c in np.unique(px, axis=0).tolist()}
            bad = got - ({(255, 255, 255)} if emissive else PAL)
            if bad: F(f"offpalette {os.path.relpath(p, TR)} {sorted(bad)[:2]}")
        if size and im.size != (size, size): F(f"size {os.path.relpath(p, TR)} {im.size}")
        return a
    total_png = 0
    for form, S in SIZES.items():
        D = os.path.join(EV, form); PIV = (S // 2, S - 3); egg = form == "evo_egg"; tag = f"[{form}]"
        adult = form in GUARD or form in STILL; still = form in STILL; hasbulb = form == "evo_hop" or adult
        fe = CL.get("forms", {}).get(form)
        if not fe: F(f"CLIPS.json forms.{form} missing"); continue
        aj = json.load(open(os.path.join(EV, f"atlas_{form}.json")))
        PAL, EM = load_pal(aj["meta"].get("palette"), tuple(aj["meta"].get("emissiveColors", ("glow_core", "glow_mid"))))
        if adult and fe.get("palette") != "../evo6/" + aj["meta"].get("palette", ""): F(f"{tag} CLIPS palette != atlas meta palette")
        if fe.get("frameSize") != S or tuple(fe.get("pivotPx", ())) != PIV: F(f"{tag} CLIPS frameSize/pivot")
        n = 0
        for p in glob.glob(D + "/**/*.png", recursive=True):
            top = os.path.relpath(p, D).split("/")[0]
            chk(p, S if top in ("frames", "layers", "emissive") else None, emissive=top == "emissive", PAL=PAL); n += 1
        total_png += n
        FAJ = json.load(open(os.path.join(D, f"face_anchors_{form}.json"))); FA = FAJ["anchors"]
        if FAJ.get("frameSize") != S or tuple(FAJ.get("pivotPx", ())) != PIV: F(f"{tag} face_anchors frameSize/pivot")
        # expected clips / frame counts from CLIPS.json
        if egg:
            want = {c: d["frames"] for c, d in fe["clipDefs"].items()}
            if want != EGG_WANT: F(f"{tag} egg clip set {want}")
            for c, d in fe["clipDefs"].items():
                if d["anchors"] != FA.get(c): F(f"{tag} CLIPS clipDefs anchors != face_anchors {c}")
        else:
            want = {}
            for c in fe["clips"]:
                ent = byname.get(c, {}).get(form)
                if not ent: F(f"{tag} CLIPS clips[{c}].{form} missing"); continue
                want[c] = ent["frames"]
                if byname[c].get("anchors", {}).get(form) != FA.get(c): F(f"{tag} CLIPS anchors.{form} != face_anchors {c}")
                if byname[c]["frames"] != ent["frames"] and not byname[c].get("perForm"): pass
            if still and "mvp" in fe:   # batch C（MVP）；batch D 起靜光＝全套
                if fe.get("mvp") != STILL_MVP or set(fe["clips"]) != set(STILL_MVP): F(f"{tag} 靜光 MVP clip set {fe.get('clips')}")
            else:
                if still and fe.get("s3") != S3: F(f"{tag} 靜光全套要有 s3 {fe.get('s3')}")
                need = set(fe.get("std23", [])) | set(fe.get("liveliness", [])) | set(fe.get("s3", []))
                if len(fe.get("std23", [])) != 23: F(f"{tag} std23 count {len(fe.get('std23', []))}")
                if "picked_up" not in need or not set(LIVE_S2) <= need: F(f"{tag} liveliness s1/s2 incomplete")
                if form == "evo_guard_dust" and fe.get("s3") != S3: F(f"{tag} 微塵 s3 clips missing {fe.get('s3')}")
                if need != set(fe["clips"]): F(f"{tag} clip list != std23+liveliness(+s3)")
        if set(want) != set(FA): F(f"{tag} clip set CLIPS vs face_anchors {set(want) ^ set(FA)}")
        for c, nf in want.items():
            if len(FA.get(c, [])) != nf: F(f"{tag} frame count {c} {len(FA.get(c, []))} != {nf}")
        live = set() if egg else set(fe.get("liveliness", [])) | set(fe.get("s3", []))
        # kit
        kit = {os.path.basename(p)[:-4]: load(p) for p in glob.glob(D + "/kit/*.png")}
        if egg and kit: F(f"{tag} egg should have no kit")
        if not egg:
            if not any(k.startswith("eyes_") for k in kit) or not any(k.startswith("mouth_") for k in kit): F(f"{tag} kit incomplete")
            hasb = any(k.startswith("bulb_") for k in kit)
            if hasb != (form == "evo_hop"): F(f"{tag} bulb kit presence wrong")
        kpiv = {k: (aj["frames"][k]["pivotPx"]["x"], aj["frames"][k]["pivotPx"]["y"]) for k in kit if k in aj["frames"]}
        if len(kpiv) != len(kit): F(f"{tag} kit pieces missing from atlas")
        def place(img, name, at, strict=True):
            if name == "mouth_none": return True
            if name not in kit:
                if strict: F(f"{tag} kit piece missing {name}")
                return False
            a = kit[name]; x0, y0 = at[0] - kpiv[name][0], at[1] - kpiv[name][1]
            for yy, xx in zip(*np.nonzero(a[..., 3])):
                if 0 <= y0 + yy < S and 0 <= x0 + xx < S: img[y0 + yy, x0 + xx] = a[yy, xx]
            return True
        recon = kit_ok = kit_n = em_ok = edge = lamp_ok = 0; std_kit = [0, 0]
        for cn, A in FA.items():
            for k, an in enumerate(A, 1):
                req = ("head_r", "faceVisible", "face") + (() if egg else ("eyeL", "eyeR", "mouth"))
                for key in req:
                    if key not in an: F(f"{tag} missing {key} {cn} {k}")
                if hasbulb and "bulb" not in an: F(f"{tag} missing bulb {cn} {k}")
                if not hasbulb and ("bulb" in an or "bulb2" in an or "tail" in an): F(f"{tag} unexpected bulb {cn} {k}")
                if egg and (an.get("faceVisible") or an.get("face") is not None): F(f"{tag} egg face rig present {cn} {k}")
                if cn == "picked_up" and "grab" not in an: F(f"{tag} missing grab {cn} {k}")
                for key in ("eyeL", "eyeR", "mouth", "head_r", "bulb", "bulb2", "tail", "grab", "crack"):
                    if key not in an: continue
                    x, y = an[key]
                    if not (isinstance(x, int) and isinstance(y, int) and 0 <= x < S and 0 <= y < S): F(f"{tag} anchor out {cn} {k} {key} {an[key]}")
                nm_ = f"{cn}_{k:02d}"
                fr = os.path.join(D, "frames", nm_ + ".png"); nf = os.path.join(D, "layers", nm_ + "_noface.png")
                ov = os.path.join(D, "layers", nm_ + "_faceov.png"); ef = os.path.join(D, "emissive", nm_ + "_emissive.png")
                nef = os.path.join(D, "emissive", nm_ + "_noface_emissive.png")
                if not all(os.path.exists(x) for x in (fr, nf, ov, ef, nef)): F(f"{tag} missing file {cn} {k}"); continue
                full = load(fr); body = load(nf); o = load(ov); al = full[..., 3] > 0
                if not al.any(): F(f"{tag} empty frame {cn} {k}")
                if form.endswith("_dust") and adult and "bulb" in an:   # 微塵手燈：bulb 錨點要落喺燈（emissive）上
                    bx, by = an["bulb"]; em = load(ef)[max(0, by - 1):by + 2, max(0, bx - 1):bx + 2, 3]
                    if cn == "sick": em = full[max(0, by - 1):by + 2, max(0, bx - 1):bx + 2, 3]   # 病：燈熄（唔發光）但仍要喺燈上
                    if (em > 0).any(): lamp_ok += 1
                    else: F(f"{tag} 微塵 bulb 錨點唔喺燈上 {cn} {k} {an['bulb']}")
                if al[0].any() or al[-1].any() or al[:, 0].any() or al[:, -1].any(): F(f"{tag} frame touches edge {cn} {k}"); edge += 1
                comp = body.copy(); m = o[..., 3] == 255; comp[m] = o[m]
                if np.array_equal(comp, full): recon += 1
                else: F(f"{tag} noface+faceov != full {cn} {k}")
                for img, epath in ((full, ef), (body, nef)):
                    w = np.zeros(img.shape[:2], bool)
                    for c in EM: w |= (img[..., 3] == 255) & (img[..., :3] == c).all(-1)
                    e = load(epath)
                    if np.array_equal(e[..., 3] == 255, w) and (e[e[..., 3] == 255][:, :3] == 255).all(): em_ok += 1
                    else: F(f"{tag} emissive mismatch {os.path.basename(epath)}")
                if not egg and an.get("faceVisible") and an.get("face"):
                    fa = an["face"]; img = body.copy(); g = fa.get("gaze", "C"); eL = fa["eyes"]; eR = fa.get("eyesR", eL)
                    nm = lambda st, sd: f"eyes_{st}_{g if st in MOVING else 'C'}_{sd}"
                    st = cn in live   # std23 臉＝原 renderer（sick 等「保留原幀」），只作 info
                    okp = all([place(img, nm(eL, "l"), an["eyeL"], st), place(img, nm(eR, "r"), an["eyeR"], st), place(img, "mouth_" + fa["mouth"], an["mouth"], st)])
                    ok = okp and np.array_equal(img, full)
                    if st:
                        kit_n += 1
                        if ok: kit_ok += 1
                        else: F(f"{tag} kit compose != full {cn} {k}")
                    else:
                        std_kit[1] += 1; std_kit[0] += ok
        if not egg:
            if kit_n == 0: F(f"{tag} no kit-composed frames checked")
            # kit alignment sanity: neutral preset on idle_01 noface reproduces the std23 idle_01 face
            an = FA["idle"][0]; img = load(os.path.join(D, "layers", "idle_01_noface.png")); full = load(os.path.join(D, "frames", "idle_01.png"))
            place(img, "eyes_neutral_C_l", an["eyeL"]); place(img, "eyes_neutral_C_r", an["eyeR"]); place(img, "mouth_" + an["face"]["mouth"], an["mouth"])
            diff = int((img != full).any(-1).sum())
            if diff: F(f"{tag} kit alignment: idle_01 neutral compose differs by {diff}px")
        if hasbulb:
            em_idle = [load(os.path.join(D, "emissive", f"idle_{k:02d}_emissive.png"))[..., 3].sum() for k in range(1, 5)]
            if not all(em_idle): F(f"{tag} idle has no glow")
        if egg:
            em_glow = [load(os.path.join(D, "emissive", f"glow_{k:02d}_emissive.png"))[..., 3].sum() for k in range(1, 3)]
            if len(set(em_glow)) < 2: F(f"{tag} glow clip emissive static")
        tot = sum(len(v) for v in FA.values())
        info.append(f"{tag} {S}px pivot {PIV}：PNG {n}；clip {len(FA)}／幀 {tot}；noface+faceov＝完整 {recon}；emissive 吻合 {em_ok}；"
                    + ("光卵冇 face rig" if egg else f"生命感 kit 合成＝完整 {kit_ok}/{kit_n}；std23 face≈kit {std_kit[0]}/{std_kit[1]}（info）") + f"；掂邊 {edge}" + (f"；微塵 bulb 喺燈上 {lamp_ok}" if lamp_ok else ""))
        # atlases
        for png, em in ((f"atlas_{form}.png", False), (f"atlas_{form}_emissive.png", True)):
            pth = os.path.join(EV, png); chk(pth, emissive=em, PAL=PAL); im = load(pth); H, W = im.shape[:2]
            if W != 1024 or H > 1024: F(f"{tag} atlas size {png} {W}x{H}")
            if aj["meta"].get("padding") != 2 or aj["meta"].get("extrude") != 1: F(f"{tag} atlas meta pad/extrude")
            if aj["meta"].get("size") != {"w": W, "h": H}: F(f"{tag} atlas meta size")
            rects = [(k, v["frame"]) for k, v in aj["frames"].items()]
            names = set(aj["frames"])
            for c, nf_ in want.items():
                for i in range(1, nf_ + 1):
                    if f"{c}_{i:02d}" not in names: F(f"{tag} atlas missing {c}_{i:02d}")
                    if not egg and f"{c}_noface_{i:02d}" not in names: F(f"{tag} atlas missing {c}_noface_{i:02d}")
            for i, (k, r) in enumerate(rects):
                x, y, w, h = r["x"], r["y"], r["w"], r["h"]
                if x < 2 or y < 2 or x + w > W - 2 or y + h > H - 2: F(f"{tag} bounds {k}")
                if not em:
                    for k2, r2 in rects[i + 1:]:
                        if not (x + w + 2 <= r2["x"] or r2["x"] + r2["w"] + 2 <= x or y + h + 2 <= r2["y"] or r2["y"] + r2["h"] + 2 <= y): F(f"{tag} overlap {k} {k2}")
                kitp = k.startswith(KIT_PREFIX)
                if "_noface_" in k:
                    c, nn = k.rsplit("_noface_", 1)
                    src = os.path.join(D, "emissive", f"{c}_{nn}_noface_emissive.png") if em else os.path.join(D, "layers", f"{c}_{nn}_noface.png")
                elif kitp: src = os.path.join(D, "kit", k + ".png")
                else: src = os.path.join(D, "emissive", k + "_emissive.png") if em else os.path.join(D, "frames", k + ".png")
                s = load(src)
                if em and kitp:
                    mm = np.zeros_like(s)
                    for c in EM: mm[(s[..., 3] == 255) & (s[..., :3] == c).all(-1)] = (255, 255, 255, 255)
                    s = mm
                if s.shape[:2] != (h, w): F(f"{tag} atlas rect size {k}"); continue
                if not np.array_equal(im[y:y + h, x:x + w], s): F(f"{tag} atlas px != src {png} {k}")
                if not np.array_equal(im[y - 1, x:x + w], s[0]) or not np.array_equal(im[y:y + h, x - 1], s[:, 0]) \
                   or not np.array_equal(im[y + h, x:x + w], s[-1]) or not np.array_equal(im[y:y + h, x + w], s[:, -1]): F(f"{tag} extrude {png} {k}")
                if not em and not kitp:
                    base = k.rsplit("_noface_", 1)[0] if "_noface_" in k else k.rsplit("_", 1)[0]
                    fi = int(k.rsplit("_", 1)[1]) - 1
                    wantp = tuple(FA[base][fi]["grab"]) if base == "picked_up" else PIV
                    pv = aj["frames"][k]["pivotPx"]
                    if (pv["x"], pv["y"]) != wantp: F(f"{tag} pivot {k} {pv} want {wantp}")
                    if (w, h) != (S, S): F(f"{tag} atlas frame size {k}")
            if not em: info.append(f"{tag} {png} {W}x{H} {len(rects)} 塊")
        for an_name, a in aj["animations"].items():
            for fr in a["frames"]:
                if fr not in aj["frames"]: F(f"{tag} anim frame missing {an_name} {fr}")
        if aj["animations"].get("picked_up", {}).get("pivot") != "grab": F(f"{tag} picked_up anim pivot != grab")
    info.append(f"形態 {len(SIZES)}：{'、'.join(SIZES)}")
    info.append(f"PNG 總數 {total_png}（＋atlas {2 * len(SIZES)} 張）")
    return fails, info

if __name__ == "__main__":
    fails, info = run()
    print("\n".join(info)); print("FAIL", len(fails)); [print(" -", f) for f in fails[:60]]
    print("ALL PASS" if not fails else "FAILED"); sys.exit(1 if fails else 0)
