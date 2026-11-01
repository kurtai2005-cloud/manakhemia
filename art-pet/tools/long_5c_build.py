# 《微光小圃》5c 遺傳 — 花紋 8 款 overlay mask atlas（59 形態 ＋ 團絨蛋／細佬蛋）、上一代染色表、教錯招式對照、long_5c.json
# 純 Pillow/numpy，冇 AI。mask 灰階：R=255 → 染 hi、R=128 → 染 lo（引擎 runtime 染上一代色）。
import json, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import long_5abc_lib as LB
import long_5c_patterns as PT
from series2_lib import ART, save
O5 = os.path.join(LB.OUTL, "5c")
LS = json.load(open(os.path.join(ART, "sprites/series2/lessons/lessons.json")))
PN = [p for p, _ in PT.PATTERNS]
EGGS = {"egg_tr": ("tuanrong/pet_tuanrong_egg_sheet.png", 32, 6), "egg_kid": ("series2/egg/egg_48.png", 48, 1), "egg_kid_crack": ("series2/egg/egg_crack.png", 48, 4)}

def form_atlas(k):
    clips = LB.clips_of(k); blocks, rows_all, y, cnt = [], [], 0, {}
    for p in PN:
        m = PT.mask_base(k, p); cnt[p] = int((m > 0).sum())
        atlas, rows = LB.overlay_atlas(k, PT.mask_rgba(m), (0, 0), clips, pad=(0, 0))
        atlas[atlas[..., 3] == 0] = 0
        for rw in rows: rw["y"] += y; rw["pattern"] = p
        y += atlas.shape[0]; blocks.append(atlas); rows_all += rows
    Wt = max(b.shape[1] for b in blocks); A = np.zeros((y, Wt, 4), np.uint8); yy = 0
    for b in blocks: A[yy:yy + b.shape[0], :b.shape[1]] = b; yy += b.shape[0]
    # mask 一定喺 pet 實色入面（xform 可能偶爾出界 1px）→ 用 pet strip 剪
    for rw in rows_all:
        if not rw["petPng"]: continue
        pet = np.asarray(Image.open(os.path.join(ART, "sprites", rw["petPng"])).convert("RGBA"))
        reg = A[rw["y"]:rw["y"] + rw["frameH"], :rw["frames"] * rw["frameW"]]
        if pet.shape[:2] == reg.shape[:2]: reg[pet[..., 3] == 0] = 0
    save(A, os.path.join(O5, "patterns", f"{k}_pattern.png"))
    return {"png": f"patterns/{k}_pattern.png", "rows": rows_all, "maskPx": cnt}

def egg_atlas(eid):
    src, fw, n = EGGS[eid]; a = np.asarray(Image.open(os.path.join(ART, "sprites", src)).convert("RGBA")); rows = []; out = []
    for j, p in enumerate(PN):
        fr = []
        for i in range(n):
            f = a[:, i * fw:(i + 1) * fw]; m = PT.egg_mask(f, p); fr.append(PT.mask_rgba(m))
        out.append(np.concatenate(fr, 1)); rows.append({"pattern": p, "y": j * a.shape[0], "frames": n, "frameW": fw, "frameH": a.shape[0], "eggPng": src})
    A = np.concatenate(out, 0); A[A[..., 3] == 0] = 0; save(A, os.path.join(O5, "patterns", f"{eid}_pattern.png"))
    return {"png": f"patterns/{eid}_pattern.png", "rows": rows}

def dom(k):
    return PT.tint_for_parent(k)[2]
def dist(a, b): return float(np.abs(np.array(PT.LB_hex(a)) - np.array(PT.LB_hex(b))).sum())
def tint_pair(parent, child=None):
    """上一代色（hi, lo）；如果細佬自己主色太近（|ΔRGB|<90）→ hi 推白、lo 壓深，等花紋睇得到"""
    hi, lo, base = PT.tint_for_parent(parent)
    if child and dist(base, dom(child)) < 90:
        h = np.array(PT.LB_hex(hi)); l = np.array(PT.LB_hex(lo))
        hi = PT._hx(h + (255 - h) * .6); lo = PT._hx(l * .7)
    return hi, lo

def tricks():
    out = {}
    for s, pr in LS["propsBySeries"].items():
        c = LS["copy"][s]; out[s] = {"lesson": s, "title": c["title"].replace("照抄：", ""), "prop": pr["id"], "propZh": pr["zh"], "propPng": pr["png"],
                                     "clip": f"series2/lessons/lessons.json#copy.{s}", "durationMs": c["durationMs"]}
    return out

def data(forms, eggs):
    adults = LB.ADULTS
    return {"version": "5c-1.0", "spec": "docs-gdd/series2-4a4b-spec.md v1.1 §5c",
     "rules": {"parentPick": "新蛋孵之前揀屋內一隻成年做「上一代」（可揀團絨靜光或細佬 S5/S6）", "inherit": ["pattern ×1（跟上一代系／路線）", "trick ×1（上一代學過嗰課嘅招式）"],
               "fastGrow": {"fromFamilyLv": 3, "stages": 2, "speedup": 0.2, "excludeEgg": "tr", "note": "家族 Lv3 起，細佬蛋孵出嘅頭 2 階快 20%；團絨蛋唔計"},
               "tree": ["代", "系", "上一代", "教錯咗乜"]},
     "patterns": [{"id": p, "zh": z, "pid": PT.PID[p]} for p, z in PT.PATTERNS],
     "patternBySeries": PT.BY_SERIES, "patternByRoute": PT.BY_ROUTE,
     "parents": {k: {"series": PT.series_of(k), "pattern": PT.pattern_for_parent(k), "tint": dict(zip(("hi", "lo", "base"), PT.tint_for_parent(k))),
                     "trick": (PT.series_of(k) if PT.series_of(k) in LS["copy"] else None)} for k in adults},
     "parentTrickNote": "細佬上一代：招式＝佢自己個系嘅 lesson（A–H）。團絨靜光上一代：佢冇學過嘢（佢係老師）→ 傳畀細佬嘅係佢「示範」嗰課 = runtime 記錄（json null → 用嗰次 lesson 嘅 id）",
     "tricks": tricks(),
     "tint": {"rule": "mask R≥190 → hi、其餘 → lo；alpha 照 mask", "contrast": "如果上一代主色同細佬主色 |ΔRGB| <90：hi＝hi 再推白 60%、lo＝lo×0.7（long_5c_build.tint_pair）",
              "childDominant": {k: dom(k) for k in LB.ALL59}},
     "overlay": {"atlas": "每形態一張：8 個 pattern block（順序同 patterns），每 block 每 clip 一行；rows[].pattern／clip／y／frames／frameW／frameH／pivot／petPng",
                 "draw": "pet strip 第 i 格之後即刻畫（喺 FX／道具／帽之前），用同一 pivot", "forms": forms, "eggs": eggs,
                 "eggNote": "蛋冇 rig：egg_tr＝tuanrong egg sheet 6 格（32）、egg_kid＝egg_48、egg_kid_crack＝egg_crack 4 格；同蛋 PNG 同大小直接疊"}}

if __name__ == "__main__":
    os.makedirs(os.path.join(O5, "patterns"), exist_ok=True)
    forms = {k: form_atlas(k) for k in LB.ALL59}; print("forms", len(forms))
    eggs = {e: egg_atlas(e) for e in EGGS}; print("eggs", len(eggs))
    LB.jdump(data(forms, eggs), os.path.join(O5, "long_5c.json")); print("ok")
