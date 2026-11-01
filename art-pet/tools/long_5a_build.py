# 《微光小圃》5a 家族同屋擴建 — 互動 strip（59 形態）＋擴房 3 間＋long_5a.json。純 Pillow/numpy，冇 AI。
# 唔改 4a/4b 任何檔；只寫 sprites/series2_long/5a/
import json, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import long_5abc_lib as LB
import long_5a_rooms as RM
from series2_lib import ART, save, ncolors
O5 = os.path.join(LB.OUTL, "5a")

LEVELS = [0, 60, 150, 270, 420, 600, 810, 1050, 1320, 1620]
UNLOCK = {2: ["room2"], 3: ["visitor_new", "inherit_fast"], 4: ["furniture_pack1"], 5: ["room3"], 6: ["kid_series_E"],
          7: ["job_cap_plus1"], 8: ["room4"], 9: ["furniture_pack2"], 10: ["family_title", "tree_gold"]}
UNLOCK_ZH = {"room2": "第 2 間房（森林閣樓）", "visitor_new": "新訪客", "inherit_fast": "遺傳加速（細佬頭 2 階段快 20%）", "furniture_pack1": "6 件新家具",
             "room3": "第 3 間房（星夜書房）", "kid_series_E": "細佬 E 系", "job_cap_plus1": "工作等級上限 +1（Lv6）", "room4": "第 4 間房（海風小屋）",
             "furniture_pack2": "6 件新家具", "family_title": "家族稱號", "tree_gold": "金色族譜"}

def actions():
    meta = {}
    for k in LB.ALL59:
        strip, g = LB.bake_clip(k, "interact")
        assert set(np.unique(strip[..., 3])) <= {0, 255}
        save(strip, os.path.join(O5, "actions", f"{k}_interact.png"))
        meta[k] = {"png": f"actions/{k}_interact.png", "frameW": g["CW"], "frameH": g["CH"], "pivot": [g["PX"], g["PY"]], "colors": int(max(ncolors(f) for f in LB.strip_frames(strip, g["CW"])))}
    c = LB.CLIPS5["interact"]
    return {"clip": {kk: c[kk] for kk in ("frames", "frameMs", "loop", "note")}, "schema": "3a body/face/fx（已烘焙；runtime 亦可用 clip 重現）",
            "clipData": {kk: c[kk] for kk in ("body", "face", "fx")},
            "duo": {"gapPx": "max(22, (兩隻 sit 第 0 格 bbox 闊相加)/2 − 4)", "rule": "兩隻面對面（左邊嗰隻正向、右邊 flipX），同時播；結束各自 sit／walk", "trigger": "屋內兩隻閒住隨機 1/90s；或撳寵物卡「打招呼」"},
            "forms": meta}

def rooms():
    out = {}
    for t, T in RM.THEMES.items():
        m = RM.build_room(t, os.path.join(O5, "rooms", t))
        out[t] = {"zh": T["zh"], "unlockLv": T["unlockLv"], "motif": T["motif"], "dir": f"rooms/{t}", "variants": ["day", "night"],
                  "layers": ["sky", "far", "mid", "fore", "lightmap", "light_add", "emissive", "emissive_blur", "vignette", "grade.json", "palette.json"], "colors": m,
                  "geometry": "同 4b room1 一樣（house.json grid／slots／walk 直接用）", "capacity": 4}
    return out

def data(act, rms):
    return {"version": "5a-1.0", "spec": "docs-gdd/series2-4a4b-spec.md v1.1 §5a；series2-egg-v1.md v1.4+",
     "raising": {"max": 2, "slots": ["main", "kid"], "note": "最多 2 隻養緊（1 主養＋1 細佬）；成年搬入屋"},
     "eggChoice": {"options": [{"id": "egg_tr", "zh": "團絨蛋", "png": "ui/egg_choice_tr@3x.png"}, {"id": "egg_kid", "zh": "細佬蛋", "png": "ui/egg_choice_kid@3x.png", "requires": "冇細佬養緊（否則灰＋「細佬養緊」）"}], "pick": 1},
     "makeMain": {"zh": "做主養", "where": "屋內撳成年 → 寵物卡", "rule": "揀咗嘅成年做主養（浮動寵物只顯示團絨系）"},
     "floatingPet": "只顯示團絨系",
     "familyLevel": {"max": 10, "thresholds": LEVELS, "xp": {"raise_one": 50, "dex_new_form": 10, "furniture_new": 5, "expedition_return": 3},
                     "unlocks": {str(k): [{"id": u, "zh": UNLOCK_ZH[u]} for u in v] for k, v in UNLOCK.items()}},
     "rooms": {"room1": {"zh": "屋仔（4b）", "unlockLv": 1, "dir": "../../series2_house/room", "capacity": 4, "note": "4b 原房；house.json defaultState（bed_leaf 預設床）"}, **rms},
     "roomRules": {"capacity": 4, "furniture": "每間房各自 6 slot；家具通用（house.json furniture，擁有一件可以喺任何一間擺；同一件同時只擺一間）", "defaultOnUnlock": "新房開咗全空（冇送床）"},
     "actions": {"interact": act}, "note4b": "sit／prank 用 4b series2_house/actions（已有，冇重整）"}

if __name__ == "__main__":
    act = actions(); print("interact", len(act["forms"]))
    rms = rooms(); print("rooms", list(rms))
    LB.jdump(data(act, rms), os.path.join(O5, "long_5a.json")); print("ok")
