#!/usr/bin/env python3
"""validate_accessory_runtime — 團絨飾品 runtime（attach 表＋item source＋compositor）。檢查：
ATTACH.json index（25 形態、檔案、frameSize、clip／幀數）；每個 <form>.json schema、每個 clip 幀數同身體 frames 一致、逐幀欄位齊；
14 件 source（13 件＋cherry）：item.json schema、slot、materials 用 v3、所有 lab／預覽 PNG alpha 0/255、lab 只用 materials key 色、預覽只用 v3；
眼鏡 lens ladder index 喺 sheet 內；org() round-half-even；
cherry：3 view × S/M/L（闊 9/13/17）、side_r、rot 8、dangle 擺；25 形態全部 clip render（runtime 輸出 v3＋alpha 0/255、唔遮五官、唔出畫布）；
RUNTIME_COMPARE.json：13 件 × 25 形態、每件 ok ≥95%、可見性一致 ≥97%、總 ok ≥99%；預覽、ENGINE_ATTACH.md、RUNTIME_COMPARE.md 齊；
ACCESSORIES.json runtime key；baked atlas 仍然喺度（additive）。"""
import json, os, sys, glob
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_accessories as B
import compose_accessory_runtime as C
E = []; W = []
def err(m): E.append(m)
ACCD = C.ACCD; ATT = C.ATT; SRC = C.SRC; ART = C.ART
SLOTS = ["head", "side_l", "side_r", "neck", "bulb", "face"]
FR_KEYS = ["facing", "dir", "head", "side_r", "side_l", "face", "eyes", "neck", "bulb", "facePts", "glow", "bulbPt", "stem"]
ITEMS13 = list(B.ITEMS)
def alpha01(a, where):
    if not np.isin(a[..., 3], (0, 255)).all(): err(f"{where}: alpha 唔係 0/255")
def v3(a, where):
    op = a[a[..., 3] == 255][:, :3]
    if len(op):
        bad = {tuple(int(v) for v in c) for c in np.unique(op, axis=0)} - B.V3
        if bad: err(f"{where}: 非 v3 色 {sorted(bad)[:3]}")

# ---- org（round half even，同 baked）
for p, piv, want in ((5.5, 0, 6), (4.5, -1, 6), (3.0, 0.5, 3), (10.5, 1, 10), (2.5, 0, 2)):
    got = C.org(p, piv)
    exp = int(round(p - piv - 1)) + 1
    if got != exp: err(f"org({p},{piv})={got} ≠ {exp}")

# ---- ATTACH index＋每個形態
ip = os.path.join(ATT, "ATTACH.json")
if not os.path.exists(ip): err("冇 attach/ATTACH.json")
else:
    I = json.load(open(ip))
    for k in ("version", "slots", "fields", "forms", "overlayPad"):
        if k not in I: err(f"ATTACH.json 冇 {k}")
    if sorted(I.get("slots", [])) != sorted(SLOTS): err(f"ATTACH.json slots {I.get('slots')}")
    if set(B.FORMS) - set(I.get("forms", {})): err(f"ATTACH.json 冇齊 25 形態：{set(B.FORMS) - set(I.get('forms', {}))}")
    for f_, e in I.get("forms", {}).items():
        if f_ not in B.FORMS and not e.get("extra"): err(f"ATTACH.json {f_} 唔係正式形態又冇標 extra")
    for form, e in I.get("forms", {}).items():
        p = os.path.join(ACCD, e["file"])
        if not os.path.exists(p): err(f"{form}: 冇 {e['file']}"); continue
        A = json.load(open(p)); S = A.get("frameSize")
        for k in ("version", "form", "frameSize", "sizeClass", "overlayPad", "ref", "slots", "clips"):
            if k not in A: err(f"{form}: attach 冇 {k}")
        if S != e["frameSize"]: err(f"{form}: frameSize {S} ≠ index {e['frameSize']}")
        if A.get("overlayPad") != C.PAD: err(f"{form}: overlayPad {A.get('overlayPad')}")
        if A.get("sizeClass") not in ("S", "M", "L"): err(f"{form}: sizeClass {A.get('sizeClass')}")
        if len(A["clips"]) != e["clips"]: err(f"{form}: clips {len(A['clips'])} ≠ index {e['clips']}")
        nf = 0
        for clip, c in A["clips"].items():
            for k in ("frameDir", "fps", "loop", "n", "hidden", "f"):
                if k not in c: err(f"{form}/{clip}: 冇 {k}")
            if not isinstance(c.get("hidden"), dict): err(f"{form}/{clip}: hidden 唔係 dict")
            for s in c.get("hidden", {}):
                if s not in SLOTS: err(f"{form}/{clip}: hidden 有怪 slot {s}")
            n = c["n"]; nf += n
            fd = os.path.join(ART, c["frameDir"])
            if not all(os.path.exists(os.path.join(fd, f"{clip}_{k:02d}.png")) for k in range(1, n + 1)): err(f"{form}/{clip}: 身體 frames 唔齊 {fd}")
            if os.path.exists(os.path.join(fd, f"{clip}_{n + 1:02d}.png")): err(f"{form}/{clip}: 身體多過 n={n} 幀")
            if not c["f"]: continue
            for k in FR_KEYS:
                v = c["f"].get(k)
                if v is None: err(f"{form}/{clip}: f 冇 {k}"); continue
                if len(v) != n: err(f"{form}/{clip}: f.{k} 長度 {len(v)} ≠ {n}")
            for i, fc in enumerate(c["f"].get("facing", [])):
                if fc not in ("F", "S", "B"): err(f"{form}/{clip}_{i + 1:02d}: facing {fc}")
            for i, fa in enumerate(c["f"].get("face", [])):
                if fa is not None and len(fa) != 14: err(f"{form}/{clip}_{i + 1:02d}: face 要 14 個值")
            for fl in ("head", "side_r", "side_l"):
                for i, v in enumerate(c["f"].get(fl, [])):
                    if v is None: continue
                    x, y = v[0], v[1]
                    if not (-C.PAD <= x <= S + C.PAD and -C.PAD <= y <= S + C.PAD): err(f"{form}/{clip}_{i + 1:02d}: {fl} 出 padding ({x},{y})")
        if nf != e["frames"]: err(f"{form}: frames {nf} ≠ index {e['frames']}")

# ---- 新形態擴充（data-only）
xp = os.path.join(ATT, "FORMS_EXTRA.example.json")
if not os.path.exists(xp): err("冇 attach/FORMS_EXTRA.example.json")
else:
    X = json.load(open(xp))
    for k in ("keys", "anchorSchema", "forms"):
        if k not in X: err(f"FORMS_EXTRA.example 冇 {k}")
    for f_, e in X.get("forms", {}).items():
        for k in ("frameDir", "anchors"):
            if k not in e: err(f"FORMS_EXTRA.example {f_} 冇 {k}")
if os.path.exists(ip) and "extraForms" not in I: err("ATTACH.json 冇 extraForms 說明")
rp_ = os.path.join(ATT, "FORMS_EXTRA.json")
if os.path.exists(rp_):
    for f_ in json.load(open(rp_))["forms"]:
        if f_ not in I.get("forms", {}): err(f"FORMS_EXTRA 登記咗 {f_} 但 ATTACH.json 冇（要重跑 attach）")
EXTRA_FORMS = [f_ for f_, e in I.get("forms", {}).items() if e.get("extra")] if os.path.exists(ip) else []

# ---- item sources
srcs = sorted(d for d in os.listdir(SRC) if os.path.isdir(os.path.join(SRC, d)))
for k in ITEMS13 + ["cherry"]:
    if k not in srcs: err(f"source 冇 {k}")
for key in srcs:
    d = os.path.join(SRC, key); p = os.path.join(d, "item.json")
    if not os.path.exists(p): err(f"{key}: 冇 item.json"); continue
    it = json.load(open(p))
    for f_ in ("id", "slot", "materials", "views", "yield", "formOverrides"):
        if f_ not in it: err(f"{key}: item.json 冇 {f_}")
    if it.get("slot") not in SLOTS: err(f"{key}: slot {it.get('slot')}")
    for f_ in ("priority", "steps"):
        if f_ not in it.get("yield", {}): err(f"{key}: yield 冇 {f_}")
    keys = set()
    for hx, m in it["materials"].items():
        keys.add(C.hexrgb(hx))
        for r in ("base", "hi", "shade"):
            if C.hexrgb(m[r]) not in B.V3: err(f"{key}: material {hx}.{r} 唔係 v3")
    for f_ in it.get("formOverrides", {}):
        if f_ not in B.FORMS: err(f"{key}: formOverrides 有怪形態 {f_}")
    for png in glob.glob(os.path.join(d, "*.png")):
        a = np.array(Image.open(png).convert("RGBA")); nm = os.path.basename(png); alpha01(a, f"{key}/{nm}")
        if nm.startswith("lab_"):
            cols = {tuple(int(v) for v in c) for c in np.unique(a[a[..., 3] == 255][:, :3], axis=0)} if (a[..., 3] == 255).any() else set()
            if cols - keys: err(f"{key}/{nm}: lab 有 materials 以外嘅色 {sorted(cols - keys)[:3]}")
        else: v3(a, f"{key}/{nm}")
    def chk_ent(e, where):
        if not os.path.exists(os.path.join(d, e["lab"])): err(f"{where}: 冇 {e['lab']}")
        if "pivot" not in e: err(f"{where}: 冇 pivot")
    for vn, vs in it["views"].items():
        for sz, e in vs.items(): chk_ent(e, f"{key}.views.{vn}.{sz}")
    for pn, ps in it.get("parts", {}).items():
        for sz, e in ps.items(): chk_ent(e, f"{key}.parts.{pn}.{sz}")
    if it["slot"] in ("head", "side_r", "side_l"):
        for vn in ("front", "side", "back"):
            if set(it["views"].get(vn, {})) < {"S", "M", "L"}: err(f"{key}: {vn} view 冇齊 S/M/L")
    if it["slot"] == "face":
        G = it.get("lens", {}); sp = os.path.join(d, G.get("sheet", "?"))
        if not os.path.exists(sp): err(f"{key}: 冇 lens sheet")
        else:
            sh = Image.open(sp).size
            for kk, (x, y, w, h, px, py) in G["index"].items():
                if x < 0 or y < 0 or x + w > sh[0] or y + h > sh[1]: err(f"{key}: lens {kk} 出 sheet"); break
            if len(G["index"]) < 1000: err(f"{key}: lens ladder 得 {len(G['index'])} 格")
        if not it.get("retry"): err(f"{key}: 冇 retry")

# ---- cherry
cp = os.path.join(SRC, "cherry", "item.json")
if os.path.exists(cp):
    it = json.load(open(cp))
    if it["slot"] != "side_r": err("cherry slot 唔係 side_r")
    if it["place"].get("rot") != 8: err("cherry rot 唔係 8")
    if it.get("swing", {}).get("apply") != "dangle": err("cherry swing 唔係擺 dangle")
    for vn in ("front", "side", "back"):
        for sz, w in (("S", 9), ("M", 13), ("L", 17)):
            if it["views"][vn][sz]["w"] != w: err(f"cherry {vn}.{sz} 闊 {it['views'][vn][sz]['w']} ≠ {w}")
    C._ITEM.pop("cherry", None); tot = hid = fr = 0
    for form in list(B.FORMS) + EXTRA_FORMS:
        A = C.attach(form); S = A["frameSize"]
        for clip in A["clips"]:
            tot += 1; L_, inf = C.clip_layers("cherry", form, clip)
            if L_ is None: hid += 1; continue
            for k, img in enumerate(L_, 1):
                fr += 1
                if img.shape[:2] != (S + 2 * C.PAD, S + 2 * C.PAD): err(f"cherry {form}/{clip}_{k:02d}: 畫布 size 錯")
                if C._hits(img, C.frame(form, clip, k)["facePts"], S): err(f"cherry {form}/{clip}_{k:02d}: 遮五官")
                if k == 1 or clip in ("idle", "walk"): alpha01(img, f"cherry {form}/{clip}_{k:02d}"); v3(img, f"cherry {form}/{clip}_{k:02d}")
    if tot and hid / tot > 0.01: err(f"cherry 收起 {hid}/{tot} clip（>1%）")
    CH = (tot, hid, fr)
else: err("冇 cherry"); CH = (0, 0, 0)

# ---- compare
rp = os.path.join(ACCD, "RUNTIME_COMPARE.json")
if not os.path.exists(rp): err("冇 RUNTIME_COMPARE.json")
else:
    R = json.load(open(rp)); its = R.get("items", {})
    if set(its) != set(ITEMS13): err(f"compare items ≠ 13 件：{set(ITEMS13) ^ set(its)}")
    to = tf = 0
    for k, v in its.items():
        if len(v.get("perForm", {})) != 25: err(f"compare {k}: perForm 唔係 25 形態")
        if v["okPct"] < 95: err(f"compare {k}: ok {v['okPct']}% < 95%")
        if v["visAgreePct"] < 97: err(f"compare {k}: 可見性一致 {v['visAgreePct']}% < 97%")
        to += v["okFrames"]; tf += v["frames"]
    if tf and to / tf < 0.99: err(f"compare 總 ok {to}/{tf} < 99%")
for f_ in ("ENGINE_ATTACH.md", "RUNTIME_COMPARE.md"):
    if not os.path.exists(os.path.join(ACCD, f_)): err(f"冇 accessories/{f_}")
PR = os.path.join(B.PREV, "runtime")
for clip in ("idle", "walk", "sleep_loop", "turn_back"):
    if not os.path.exists(os.path.join(PR, f"cherry_{clip}_25forms_3x.png")): err(f"冇預覽 cherry_{clip}_25forms_3x.png")
for k in ITEMS13:
    if not os.path.exists(os.path.join(PR, f"compare_{k}_idle_25forms_3x.png")): err(f"冇預覽 compare_{k}")
if not glob.glob(os.path.join(PR, "combo_*.png")): err("冇 combo 預覽")
AJ = json.load(open(os.path.join(ACCD, "ACCESSORIES.json")))
rt = AJ.get("runtime")
if not rt: err("ACCESSORIES.json 冇 runtime key")
else:
    for k in ("attach", "source", "engineDoc", "compare", "compositor"):
        if k not in rt: err(f"ACCESSORIES.json runtime 冇 {k}")
for k in ITEMS13:
    if not glob.glob(os.path.join(ACCD, "**", f"*{k}*.png"), recursive=True): err(f"{k}: baked 檔唔見咗（runtime 係 additive）")
print(f"validate_accessory_runtime: forms {len(B.FORMS)}，sources {len(srcs)}，cherry {CH[0] - CH[1]}/{CH[0]} clip（{CH[2]} 幀）")
for w in W: print("WARN", w)
for e in E[:80]: print("ERR", e)
print("OK" if not E else f"FAIL {len(E)}")
sys.exit(1 if E else 0)
