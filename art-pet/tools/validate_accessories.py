#!/usr/bin/env python3
"""validate_accessories — 團絨飾品＋收藏品（ACC 批次）。檢查：
schema／13 件總表／slot；每個 done item × 25 形態都有 atlas＋json；身體每一幀都要有 overlay，除非個 clip 喺 hiddenClips（有原因）；
atlas 像素 v3＋alpha 0/255；幀 rect 喺 atlas 內；唔遮五官（eyeL/eyeR/mouth ±1，faceVisible）；唔遮燈泡（bulb/bulb2 ±1）；
overlay 同 fit 一致（head slot 通用：草帽／毛冷帽／橡果帽／小皇冠；ACC2 起加傾角每幀 ≤8°、ws 0.85–1.12；帽底中心 ≤3px／蝴蝶結中心 ≤3px／頸巾頂行 = fit.ny；ACC3 side_l 中心跟 head_l；眼鏡 faceVisible＋跟兩眼中點同傾角＋L 級框粗 2＋唔壓眼 blob；ACC4 葉仔領頂行 = fit.ny、鈴中心跟 fit＋喺燈泡下＋擺 ≤25°／每幀 ≤14°、光環中心跟 fit＋喺燈泡／頭頂上、睡帽位跟 fit＋傾角每幀 ≤8°＋尾擺 ≤30°／每幀 ≤14°＋尾端有波波）；動畫 frames 對得上身體 clip 幀數；counts；
ACC5：dot 額頭眼鏡（中心喺兩眼上、貼頭 ≥FH_MIN、框底唔落眼位）；背面幀 side_r／side_l 鏡像（蝴蝶結喺左、髮飾喺右）；
dust 低燈形態鈴用 top_low；moon 帽針 pincap 鏡像；COMBOS.json（schema、讓位件、yieldSteps、由 atlas 重算一致、594 個同戴組合 0 殘留）；emissive overlap＋visibilityReview；
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
def masks_from_atlas(it, form, e):
    """由 atlas 還原 overlay alpha（同 build 一樣嘅 S+2PAD 畫布），塞入 B.MASKS，等 build_combos／check_outfits 用 repo 入面嘅成品再驗"""
    jp = os.path.join(B.ACCD, e["forms"][form]["atlas"]); aj = json.load(open(jp)); atl = np.array(Image.open(jp[:-5] + ".png"))[..., 3] > 0
    S = aj["meta"]["frameSize"]; sh = (S + 2 * B.PAD, S + 2 * B.PAD); pk = {}
    for n, fr in aj["frames"].items():
        r = fr["frame"]; ss = fr["spriteSourceSize"]; m = np.zeros(sh, bool)
        m[ss["y"] + B.PAD:ss["y"] + B.PAD + r["h"], ss["x"] + B.PAD:ss["x"] + B.PAD + r["w"]] = atl[r["y"]:r["y"] + r["h"], r["x"]:r["x"] + r["w"]]
        pk[n] = np.packbits(m)
    fits = {c: [None] * len(aj["animations"][c]["frames"]) for c in aj["animations"]}
    B.MASKS[(it, form)] = (pk, fits, S, sh)
def chk_combos(d, items):
    """ACC5 COMBOS.json：schema、每 slot ≤1／最多 5 件、讓位件＝YIELD 排先、位移喺 yieldSteps、clip 兩件都睇到；
    用 atlas 重算全部對（未列明嘅衝突＝錯；列明嘅規則要一模一樣）＋全部同戴組合套規則後 0 殘留；emissive／可見度總覆核齊"""
    cp = os.path.join(B.ACCD, "COMBOS.json")
    if not os.path.exists(cp): err("冇 COMBOS.json"); return
    C = json.load(open(cp)); R = C.get("rules", {})
    for k in ("rules", "forms", "outfitOverrides", "totals", "outfitCheck", "perPair"):
        if k not in C: err(f"COMBOS.json 缺 {k}")
    if R.get("perSlot") != 1 or R.get("maxWorn") != 5: err("COMBOS rules：perSlot 1／maxWorn 5 唔啱")
    if R.get("yieldPriority") != B.YIELD or sorted(R.get("yieldPriority", [])) != sorted(items): err("COMBOS yieldPriority 唔等於 13 件")
    if sorted(C.get("forms", {})) != sorted(B.FORMS): err("COMBOS forms ≠ 25 形態")
    for form, fo in C.get("forms", {}).items():
        for pk_, cl in fo.items():
            a, b = pk_.split("+")
            if items[a]["slot"] == items[b]["slot"]: err(f"COMBOS {form}/{pk_}: 同 slot 唔應該有對")
            y_ = a if B.YIELD.index(a) < B.YIELD.index(b) else b
            for clip, r in cl.items():
                if r.get("yield") != y_: err(f"COMBOS {form}/{pk_}/{clip}: 讓位件 {r.get('yield')} ≠ {y_}")
                if clip in items[a]["forms"][form]["hidden"] or clip in items[b]["forms"][form]["hidden"]: err(f"COMBOS {form}/{pk_}/{clip}: clip 本身已收起")
                if not r.get("hide") and tuple(r.get("off", ())) not in [tuple(x) for x in B.YIELD_STEPS[y_]]: err(f"COMBOS {form}/{pk_}/{clip}: 位移 {r.get('off')} 唔喺 yieldSteps")
    for form, fo in C.get("outfitOverrides", {}).items():
        for ok_, cl in fo.items():
            w = ok_.split("+"); sl = [items[x]["slot"] for x in w]
            if len(set(sl)) != len(sl) or not 2 <= len(w) <= 5: err(f"COMBOS override {form}/{ok_}: 唔係合法組合")
            for clip, hs in cl.items():
                if not set(hs) <= set(w): err(f"COMBOS override {form}/{ok_}/{clip}: 收起件唔喺組合入面")
    B.MASKS.clear()
    for it in items:
        for form in B.FORMS: masks_from_atlas(it, form, items[it])
    combos, tot, _ = B.build_combos(list(B.ITEMS))
    if combos != C.get("forms"):
        diff = [(f, k) for f in B.FORMS for k in set(combos.get(f, {})) | set(C["forms"].get(f, {})) if combos.get(f, {}).get(k) != C["forms"].get(f, {}).get(k)]
        err(f"COMBOS 同 atlas 重算唔一致（{len(diff)} 對，例 {diff[:3]}）——有未列明衝突或者規則過時")
    n, nchk, bad = B.check_outfits(C.get("forms", {}), list(B.ITEMS), ov=C.get("outfitOverrides"))
    if n != 594: err(f"同戴組合 {n} ≠ 594")
    for b_ in bad[:10]: err(f"同戴殘留：{b_}")
    if bad: err(f"同戴殘留共 {len(bad)}")
    print(f"combos: pairs {tot['pairs']}，有規則 {tot['pairsWithRule']}，位移 clip {tot['clipsOffset']}，收起 clip {tot['clipsHide']}；同戴 {n} 組合 {nchk} 對幀驗過，殘留 {len(bad)}；override {C['totals'].get('overrideClips')}")
    em = d.get("emissive", {}); vr = d.get("visibilityReview", {})
    if "rule" not in em or sorted(em.get("overlap", {})) != sorted(B.FORMS): err("ACCESSORIES.json emissive 唔齊")
    for f in ("sprout", "radiant", "soft"):
        if em.get("overlap", {}).get(f) is not None: err(f"emissive {f} 應該係 null（冇 emissive）")
    if sorted(vr.get("items", {})) != sorted(items): err("visibilityReview 唔齊 13 件")
    for it, v in vr.get("items", {}).items():
        vis = sum(items[it]["forms"][f]["visibleClips"] for f in B.FORMS)
        if v.get("visibleClips") != vis: err(f"visibilityReview {it}: {v.get('visibleClips')} ≠ {vis}")
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
                    head = B.ITEMS.get(it, {}).get("slot") == "head"
                    if it == "nightcap":   # ACC4 睡帽：帽位跟 fit、尾擺有限、尾端有白波波
                        if abs(fi.get("swing", 0)) > 30.01: err(f"{it}/{form}/{n}: 尾擺 {fi.get('swing')} 超 ±30°")
                        if k > 1 and abs(fi.get("swing", 0) - fl[k - 2].get("swing", 0)) > 14.01: err(f"{it}/{form}/{n}: 尾擺每幀跳 >14°")
                        if fi.get("variant") == "cap":
                            pa = fl[k - 2]["ang"] if k > 1 else 0.0
                            if abs(fi["ang"] - pa) > 8.01: err(f"{it}/{form}/{n}: 傾角跳 {pa}→{fi['ang']}（>8°）")
                        px_, py_ = fi["piv"] if fi.get("variant") == "cap" else fi["pos"]
                        if not (xs.min() - 3 <= px_ <= xs.max() + 3 and ys.min() - 3 <= py_ <= ys.max() + 3): err(f"{it}/{form}/{n}: 睡帽位 {fi.get('piv') or fi.get('pos')} 唔喺 overlay 範圍")
                        ex, ey = fi["tailEnd"]; X0, Y0 = int(round(ex)) + B.PAD, int(round(ey)) + B.PAD
                        win = ov[max(0, Y0 - 2):Y0 + 3, max(0, X0 - 2):X0 + 3]
                        if not (win[..., 3] > 0).any(): err(f"{it}/{form}/{n}: 尾端冇波波")
                    elif it == "bell":     # ACC4 鈴：吊喺燈泡下／頭頂、擺幅有限
                        cx, cy = fi["pos"]; bw = fi["W"]
                        if abs((xs.min() + xs.max()) / 2 - cx) > 2 + bw / 2 or abs((ys.min() + ys.max()) / 2 - cy) > 2 + bw / 2: err(f"{it}/{form}/{n}: 鈴位同 fit 唔一致")
                        if abs(fi.get("swing", 0)) > 25.01: err(f"{it}/{form}/{n}: 鈴擺 {fi.get('swing')} 超 ±25°")
                        if k > 1 and abs(fi.get("swing", 0) - fl[k - 2].get("swing", 0)) > 14.01: err(f"{it}/{form}/{n}: 鈴擺每幀跳 >14°")
                        if fi.get("base") == "bulb" and "bulb" in a and cy < a["bulb"][1]: err(f"{it}/{form}/{n}: 鈴喺燈泡上面")
                    elif it == "halo":     # ACC4 光環：環心跟 fit，喺燈泡／頭頂上面
                        cx, cy = fi["c"]
                        if abs((xs.min() + xs.max()) / 2 - cx) > 1.6 or abs((ys.min() + ys.max()) / 2 - cy) > 1.6: err(f"{it}/{form}/{n}: 光環中心同 fit 唔一致")
                        if fi.get("base") == "bulb" and "bulb" in a and cy >= a["bulb"][1]: err(f"{it}/{form}/{n}: 光環唔喺燈泡上面")
                        if fi.get("base") == "top" and cy >= fi["top"][1]: err(f"{it}/{form}/{n}: 光環唔喺頭頂上面")
                    elif head and fi.get("variant") == "hat":
                        if fi.get("ws", 1) > 1.1201 or fi.get("ws", 1) < 0.8499: err(f"{it}/{form}/{n}: ws {fi.get('ws')} 出 0.85–1.12（頭飾闊度跳）")
                        pa = fl[k - 2]["ang"] if k > 1 and fl[k - 2].get("variant") == "hat" else 0.0
                        if abs(fi["ang"] - pa) > 8.01: err(f"{it}/{form}/{n}: 傾角跳 {pa}→{fi['ang']}（>8°）")
                        bx, by = fi["piv"]
                        if abs(np.median(xs) - bx) > max(3, 0.25 * fi["W"]) or abs(ys.max() - by) > 4 + 0.5 * fi["W"] * abs(np.sin(np.radians(fi["ang"]))): err(f"{it}/{form}/{n}: 帽位同 fit 唔一致 ({np.median(xs):.1f},{ys.max()}) vs {fi['piv']}")
                    elif head:
                        cx, cy = fi["pos"]
                        if abs(np.median(xs) - cx) > 6 or abs(np.median(ys) - cy) > 6: err(f"{it}/{form}/{n}: 帽針位唔一致")
                    elif it == "bow":
                        cx, cy = fi["pos"]
                        if abs((xs.min() + xs.max()) / 2 - cx) > 4 + 0.3 * fi["W"] or abs((ys.min() + ys.max()) / 2 - cy) > 4 + 0.3 * fi["W"]: err(f"{it}/{form}/{n}: 結位同 head_r 唔一致")
                    elif B.ITEMS.get(it, {}).get("slot") == "side_l":   # ACC3 髮夾／髮飾：中心跟 head_l（撞五官最多推開 6px）
                        cx, cy = fi["pos"]
                        if abs((xs.min() + xs.max()) / 2 - cx) > 6 + 0.3 * fi["W"] or abs((ys.min() + ys.max()) / 2 - cy) > 6 + 0.3 * fi["W"]: err(f"{it}/{form}/{n}: 髮飾位同 head_l 唔一致")
                    elif B.ITEMS.get(it, {}).get("slot") == "face":     # ACC3 眼鏡：faceVisible、跟兩眼、唔壓眼
                        if not a.get("faceVisible", True) or "eyeL" not in a or "eyeR" not in a: err(f"{it}/{form}/{n}: faceVisible=false／冇眼都畫咗眼鏡")
                        else:
                            (lx, ly), (rx, ry) = fi["c"]; mx, my = (lx + rx) / 2, (ly + ry) / 2
                            emx, emy = (a["eyeL"][0] + a["eyeR"][0]) / 2, (a["eyeL"][1] + a["eyeR"][1]) / 2
                            if fi.get("forehead"):   # ACC5 dot：推上額頭（全圓框喺眼上面、大部分貼頭）
                                if abs(mx - emx) > 2.5 or my >= emy - 1: err(f"{it}/{form}/{n}: 額頭眼鏡中心 ({mx:.1f},{my:.1f}) 唔喺兩眼上面")
                                if fi.get("onHead", 0) < B.FH_MIN - 1e-6: err(f"{it}/{form}/{n}: 額頭眼鏡貼頭 {fi.get('onHead')} < {B.FH_MIN}")
                                bd_ = B.load(B.frame_path(form, clip, k))
                                for kk in ("eyeL", "eyeR"):
                                    bl = B.eye_blob(bd_, a, kk)
                                    if not bl: continue
                                    bx0, bx1, by0 = min(x for x, y in bl), max(x for x, y in bl), min(y for x, y in bl)
                                    if ((xs >= bx0) & (xs <= bx1) & (ys >= by0)).any(): err(f"{it}/{form}/{n}: 額頭眼鏡框底落到 {kk} 位"); break
                            elif abs(mx - emx) > 2.5 or abs(my - emy) > 2.5: err(f"{it}/{form}/{n}: 鏡片中心 ({mx:.1f},{my:.1f}) 離兩眼中點太遠")
                            ea = np.degrees(np.arctan2(a["eyeR"][1] - a["eyeL"][1], a["eyeR"][0] - a["eyeL"][0])); ga = np.degrees(np.arctan2(ry - ly, rx - lx))
                            if abs(ea - ga) > 12: err(f"{it}/{form}/{n}: 鏡框傾角 {ga:.0f}° 唔跟眼 {ea:.0f}°")
                            if abs((xs.min() + xs.max()) / 2 - mx) > 2 + 0.5 * fi.get("th", 1) + 3: err(f"{it}/{form}/{n}: 眼鏡位同 fit 唔一致")
                            if fi.get("th") != (2 if S >= 64 else 1): err(f"{it}/{form}/{n}: 鏡框粗 {fi.get('th')}（L 級要 2）")
                            body = B.load(B.frame_path(form, clip, k))
                            for kk in ("eyeL", "eyeR"):
                                if any(ov[y + B.PAD, x + B.PAD, 3] for x, y in B.eye_blob(body, a, kk)): err(f"{it}/{form}/{n}: 鏡框壓到眼 {kk}"); break
                    elif it in ("scarf", "leafcollar"):
                        if abs(ys.min() - (fi["ny"] - 1)) > 3 + abs(fi["ang"]) * 0.4: err(f"{it}/{form}/{n}: 頸巾頂 {ys.min()} vs ny {fi['ny']}")
                    # ACC5：背面（faceVisible=false）左右 slot 鏡像；dust 鈴改頭頂；moon 帽針鏡像
                    slot_ = B.ITEMS.get(it, {}).get("slot")
                    if slot_ in ("side_r", "side_l") and not a.get("faceVisible", True):
                        bx_ = np.nonzero(B.load(B.frame_path(form, clip, k))[..., 3].any(0))[0]; bc = (bx_.min() + bx_.max()) / 2
                        if not fi.get("mirrored"): err(f"{it}/{form}/{n}: 背面 {slot_} 冇鏡像")
                        ic = (xs.min() + xs.max()) / 2
                        if slot_ == "side_r" and ic >= bc: err(f"{it}/{form}/{n}: 背面蝴蝶結應該喺左邊（{ic:.1f} vs 身體中 {bc:.1f}）")
                        if slot_ == "side_l" and ic <= bc: err(f"{it}/{form}/{n}: 背面髮飾應該喺右邊（{ic:.1f} vs 身體中 {bc:.1f}）")
                    if it == "bell" and B.bell_low(form) and fi.get("base") != "top_low": err(f"{it}/{form}/{n}: 低燈形態鈴應該用 top_low（而家 {fi.get('base')}）")
                    if it == "nightcap" and form in ("evo_guard_moon", "evo_still_moon") and not fi.get("mirrored"): err(f"{it}/{form}/{n}: moon 帽針版冇用鏡像 pincap")
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
    if len(done) == 13: chk_combos(d, items)
    cl = json.load(open(os.path.join(B.MOT, "CLIPS.json")))
    if "accessories" not in cl: err("CLIPS.json 冇 accessories key")
    for k in ("nuzzle_purr", "reunion_happy"):
        if k not in cl.get("clips", {}) and k not in json.dumps(cl.get("clips")): err(f"CLIPS.json s3 entry {k} 唔見咗")
    print(f"done items: {done}; atlases {tot['atlases']}; overlay frames {tot['frames']}; clips {tot['clips']}（hidden {tot['hidden']}）")
main()
for e in E[:40]: print("ERR", e)
print(f"validate_accessories: {len(E)} errors")
sys.exit(1 if E else 0)
