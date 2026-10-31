#!/usr/bin/env python3
"""validate_accessories — 團絨飾品＋收藏品（ACC 批次）。檢查：
schema／13 件總表／slot；每個 done item × 25 形態都有 atlas＋json；身體每一幀都要有 overlay，除非個 clip 喺 hiddenClips（有原因）；
atlas 像素 v3＋alpha 0/255；幀 rect 喺 atlas 內；唔遮五官（eyeL/eyeR/mouth ±1，faceVisible）；唔遮燈泡（bulb/bulb2 ±1）；
overlay 同 fit 一致（帽底中心 ≤3px／蝴蝶結中心 ≤3px／頸巾頂行 = fit.ny）；動畫 frames 對得上身體 clip 幀數；counts；
收藏品 12 件 × 16／32＋剪影、atlas、v3／alpha；CLIPS.json additive accessories key。"""
import json, os, sys, math
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_accessories as B
E = []; W = []
def err(m): E.append(m)
def chk_px(arr, where):
    a = arr[..., 3]
    if not np.isin(a, (0, 255)).all(): err(f"{where}: alpha 唔係 0/255")
    op = arr[a == 255][:, :3]
    if len(op):
        cols = {tuple(int(v) for v in c) for c in np.unique(op, axis=0)}
        bad = cols - B.V3
        if bad: err(f"{where}: 非 v3 色 {sorted(bad)[:3]}")
def main():
    p = os.path.join(B.ACCD, "ACCESSORIES.json")
    if not os.path.exists(p): err("冇 ACCESSORIES.json"); return
    d = json.load(open(p))
    for k in ("version", "slots", "drawOrder", "sizeClasses", "items", "forms", "overlayPad", "fitRules"):
        if k not in d: err(f"ACCESSORIES.json 缺 {k}")
    if d.get("forms") != B.FORMS: err("forms 唔等於 25 個可穿戴形態")
    if len(B.FORMS) != 25: err(f"可穿戴形態 {len(B.FORMS)} ≠ 25")
    items = d.get("items", {})
    if len(items) != 13: err(f"items {len(items)} ≠ 13")
    for k, e in items.items():
        if e.get("slot") not in d.get("slots", {}): err(f"{k}: slot {e.get('slot')} 唔喺 slots")
    sc = d.get("sizeClasses", {}); allf = sum((v["forms"] for v in sc.values()), [])
    if sorted(allf) != sorted(B.FORMS): err("sizeClasses 冇覆蓋晒 25 形態")
    if "lumi" not in sc.get("L", {}).get("forms", []): err("lumi 應該係 L（64px）")
    done = [k for k, e in items.items() if e.get("status") == "done"]
    tot = {"atlases": 0, "frames": 0, "clips": 0, "hidden": 0}
    for it in done:
        e = items[it]; fitp = os.path.join(B.ACCD, e["fit"])
        if not os.path.exists(fitp): err(f"{it}: 冇 fit 檔"); continue
        fits = json.load(open(fitp))
        for sc_ in ("S", "M", "L"):
            rp = os.path.join(B.ACCD, e["ref"][sc_])
            if not os.path.exists(rp): err(f"{it}: 冇 ref {sc_}")
            else: chk_px(np.array(Image.open(rp).convert("RGBA")), f"{it} ref {sc_}")
        for form in B.FORMS:
            fe = e["forms"].get(form)
            if not fe: err(f"{it}/{form}: ACCESSORIES.json 冇 entry"); continue
            jp = os.path.join(B.ACCD, fe["atlas"]); ip = jp[:-5] + ".png"
            if not (os.path.exists(jp) and os.path.exists(ip)): err(f"{it}/{form}: atlas 檔唔齊"); continue
            aj = json.load(open(jp)); atl = np.array(Image.open(ip).convert("RGBA")); tot["atlases"] += 1
            chk_px(atl, f"{it}/{form} atlas")
            an = B.anchors(form); S = aj["meta"]["frameSize"]; hid = aj.get("hiddenClips", {})
            if hid != fe["hidden"]: err(f"{it}/{form}: hiddenClips 同 ACCESSORIES.json 唔一致")
            for c, why in hid.items():
                if not why: err(f"{it}/{form}/{c}: hidden 冇原因")
            for clip, alist in an.items():
                tot["clips"] += 1
                if clip in hid: tot["hidden"] += 1; continue
                anim = aj["animations"].get(clip)
                if not anim or len(anim["frames"]) != len(alist): err(f"{it}/{form}/{clip}: 動畫幀數唔對"); continue
                fl = fits[form]["clips"].get(clip)
                if not fl or len(fl) != len(alist): err(f"{it}/{form}/{clip}: fit 幀數唔對"); continue
                for k, a in enumerate(alist, 1):
                    n = f"{clip}_{k:02d}"; fr = aj["frames"].get(n)
                    if not fr: err(f"{it}/{form}/{n}: 冇 atlas entry"); continue
                    r = fr["frame"]; ss = fr["spriteSourceSize"]
                    if r["x"] < 0 or r["y"] < 0 or r["x"] + r["w"] > atl.shape[1] or r["y"] + r["h"] > atl.shape[0]: err(f"{it}/{form}/{n}: rect 出界"); continue
                    if ss["x"] < -B.PAD or ss["y"] < -B.PAD or ss["x"] + ss["w"] > S + B.PAD or ss["y"] + ss["h"] > S + B.PAD: err(f"{it}/{form}/{n}: 出 padding")
                    t = atl[r["y"]:r["y"] + r["h"], r["x"]:r["x"] + r["w"]]
                    ov = np.zeros((S + 2 * B.PAD, S + 2 * B.PAD, 4), np.uint8)
                    ov[ss["y"] + B.PAD:ss["y"] + B.PAD + r["h"], ss["x"] + B.PAD:ss["x"] + B.PAD + r["w"]] = t
                    if B.overlaps_face(ov, a, S): err(f"{it}/{form}/{n}: 遮五官")
                    for g in B.GLOW_KEYS:
                        if g in a:
                            x, y = a[g]
                            if ov[max(0, y - 1 + B.PAD):y + 2 + B.PAD, max(0, x - 1 + B.PAD):x + 2 + B.PAD, 3].any(): err(f"{it}/{form}/{n}: 遮 {g}")
                    # 同 fit 一致（跟變形）
                    fi = fl[k - 1]; ys, xs = np.nonzero(ov[..., 3]); xs = xs - B.PAD; ys = ys - B.PAD
                    if it == "straw" and fi.get("variant") == "hat":
                        bx, by = fi["piv"]
                        if abs(np.median(xs) - bx) > max(3, 0.25 * fi["W"]) or abs(ys.max() - by) > 4 + 0.5 * fi["W"] * abs(np.sin(np.radians(fi["ang"]))): err(f"{it}/{form}/{n}: 帽位同 fit 唔一致 ({np.median(xs):.1f},{ys.max()}) vs {fi['piv']}")
                    elif it == "straw":
                        cx, cy = fi["pos"]
                        if abs(np.median(xs) - cx) > 6 or abs(np.median(ys) - cy) > 6: err(f"{it}/{form}/{n}: 帽針位唔一致")
                    elif it == "bow":
                        cx, cy = fi["pos"]
                        if abs((xs.min() + xs.max()) / 2 - cx) > 4 + 0.3 * fi["W"] or abs((ys.min() + ys.max()) / 2 - cy) > 4 + 0.3 * fi["W"]: err(f"{it}/{form}/{n}: 結位同 head_r 唔一致")
                    elif it == "scarf":
                        if abs(ys.min() - (fi["ny"] - 1)) > 3 + abs(fi["ang"]) * 0.4: err(f"{it}/{form}/{n}: 頸巾頂 {ys.min()} vs ny {fi['ny']}")
                    tot["frames"] += 1
            extra = set(aj["frames"]) - {f"{c}_{k:02d}" for c, al in an.items() if c not in hid for k in range(1, len(al) + 1)}
            if extra: err(f"{it}/{form}: 多咗 frames {sorted(extra)[:3]}")
        cnt = e.get("counts", {})
        if cnt.get("forms") != 25: err(f"{it}: counts.forms ≠ 25")
    # 收藏品
    cj = os.path.join(B.COLD, "collectibles.json")
    if not os.path.exists(cj): err("冇 collectibles.json")
    else:
        cm = json.load(open(cj))["items"]
        if len(cm) != 12: err(f"收藏品 {len(cm)} ≠ 12")
        for c in cm:
            for f_, n in (("icon16", 16), ("icon32", 32), ("silhouette16", 16), ("silhouette32", 32)):
                pp = os.path.join(B.COLD, c[f_])
                if not os.path.exists(pp): err(f"收藏品 {c['key']} 缺 {f_}"); continue
                im = np.array(Image.open(pp).convert("RGBA"))
                if im.shape[:2] != (n, n): err(f"{c[f_]}: 尺寸 {im.shape[:2]}")
                chk_px(im, c[f_])
                if not im[..., 3].any(): err(f"{c[f_]}: 空")
            a16 = np.array(Image.open(os.path.join(B.COLD, c["icon32"])).convert("RGBA"))[..., 3]
            s32 = np.array(Image.open(os.path.join(B.COLD, c["silhouette32"])).convert("RGBA"))[..., 3]
            if (a16 != s32).any(): err(f"{c['key']}: 剪影 alpha 同 icon 唔一致")
            for k in ("name", "category", "rarity", "obtain"):
                if not c.get(k): err(f"收藏品 {c['key']} 缺 {k}")
        aj = json.load(open(os.path.join(B.COLD, "atlas_collectibles.json"))); atl = np.array(Image.open(os.path.join(B.COLD, "atlas_collectibles.png")).convert("RGBA"))
        chk_px(atl, "atlas_collectibles")
        if len(aj["frames"]) != 48: err(f"收藏品 atlas frames {len(aj['frames'])} ≠ 48")
        for n, fr in aj["frames"].items():
            r = fr["frame"]; ref = np.array(Image.open(os.path.join(B.COLD, n + ".png")).convert("RGBA"))
            if (atl[r["y"]:r["y"] + r["h"], r["x"]:r["x"] + r["w"]] != ref).any(): err(f"atlas {n} 同單檔唔一致")
    cl = json.load(open(os.path.join(B.MOT, "CLIPS.json")))
    if "accessories" not in cl: err("CLIPS.json 冇 accessories key")
    for k in ("nuzzle_purr", "reunion_happy"):
        if k not in cl.get("clips", {}) and k not in json.dumps(cl.get("clips")): err(f"CLIPS.json s3 entry {k} 唔見咗")
    print(f"done items: {done}; atlases {tot['atlases']}; overlay frames {tot['frames']}; clips {tot['clips']}（hidden {tot['hidden']}）")
main()
for e in E[:40]: print("ERR", e)
print(f"validate_accessories: {len(E)} errors")
sys.exit(1 if E else 0)
