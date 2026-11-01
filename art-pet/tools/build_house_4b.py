# 《微光小圃》4b 屋仔 — 房間＋家具 12＋house.json（擺位、錨點、價錢、行走區、動作、雙人）
# 重跑：cd art-pet && python3 tools/build_house_4b_actions.py && python3 tools/build_house_4b.py && python3 tools/build_house_4b_ui.py && python3 tools/build_house_4b_preview.py
# 純 Pillow/numpy 程序生成，冇 AI 生圖。
import json, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import house_4b_room as R
import house_4b_furniture as F
from series2_lib import ART, save, ncolors

OUT = os.path.join(ART, "sprites/series2_house")
# ── 擺位（art 座標 195×422；層座標＝art＋(14,12)）──
SLOTS = {
 "window": {"zh": "窗", "anchor": [53, 124], "layer": "wall", "pin": [53, 84], "note": "對準牆身窗洞 (30,98)–(76,150)；sprite pivot＝窗洞中心"},
 "wall":   {"zh": "牆", "anchor": [140, 104], "layer": "wall", "pin": [140, 80], "note": "掛牆；sprite pivot＝中心"},
 "lamp":   {"zh": "燈", "anchor": [26, 254], "layer": "ysort", "pin": [26, 186], "note": "企地燈；pivot＝底中；夜晚 glow additive"},
 "bed":    {"zh": "床", "anchor": [138, 264], "layer": "ysort", "pin": [138, 200], "note": "back 喺寵物後、front（被）喺瞓緊嘅寵物前；pivot＝底中"},
 "table":  {"zh": "檯", "anchor": [44, 308], "layer": "ysort", "pin": [44, 266], "note": "pivot＝底中"},
 "rug":    {"zh": "地氈", "anchor": [100, 290], "layer": "floor", "pin": [100, 270], "note": "平放地板；永遠喺寵物下面；pivot＝中心"},
}
SLOT_ORDER = ["bed", "table", "wall", "rug", "window", "lamp"]
SHADOW = {"bed": [88, 8], "table": [36, 6], "lamp": [16, 4]}              # 地面接觸影（橢圓 w,h；#3c2428 α70，引擎畫）
FOOT = {"bed": [-46, -26, 46, 2], "table": [-21, -12, 21, 2], "lamp": [-8, -6, 8, 2]}   # 行走阻擋（相對 anchor）
SETS = {"A": {"zh": "森林組", "items": {"bed": "bed_leaf", "table": "table_stump", "wall": "wall_shelf", "rug": "rug_leaf", "window": "win_curtain", "lamp": "lamp_mushroom"}},
        "B": {"zh": "夢幻組", "items": {"bed": "bed_cloud", "table": "table_round", "wall": "wall_frame", "rug": "rug_round", "window": "win_star", "lamp": "lamp_firefly"}}}
SOURCE_ZH = {"shop": "碎商店", "commission": "委託獎", "visitor:mushroom_granny": "蘑菇婆婆友誼 5", "visitor:firefly_vendor": "螢火小販友誼 5"}

WALK = {
 "rect": [22, 262, 174, 318], "note": "寵物 pivot（腳底）只可以喺呢個長方形入面，減去 blockers（有擺先計）",
 "blockers": {k: v for k, v in FOOT.items()},
 "ysort": "同層 ysort 物件（燈、床 back、檯、寵物）按 sortY 由細到大畫；寵物 sortY＝pivot y；家具 sortY＝anchor y。床 front sortY＝床 anchor y＋0.1，"
          "瞓緊床嘅寵物 sortY 強制＝床 anchor y（夾喺 back 同 front 中間）",
 "scale": "寵物 1x（同花園一樣，唔縮放）；團絨用原本 canvas（32/38/44/48/64）、pivot＝(w/2,h−3)；細佬 48×48 pivot (24,45)",
 "speed": "行 10px/s（同 4a walk 每幀 1px）；向左 flipX",
 "idleWander": "每 4–9 秒揀 walk.rect 入面一點行過去（避開 blockers）；到咗播 idle 2–5 秒",
 "drawOrder": ["sky", "far", "wall 層家具（window, wall）", "mid", "floor 層（rug）", "地面影（家具＋寵物）", "ysort（lamp, bed.back, table, 寵物, bed.front）", "fore",
               "lightmap(multiply)", "light_add(lighter)", "emissive_blur(lighter×bloom)", "燈 glow（夜晚，lighter）", "fog", "vignette", "UI"],
 "tint": "家具同寵物一樣唔過 LUT：家具 × ambientTint；寵物 × petTint × ambientTint（見 room/<day|night>/grade.json）",
}

def build_furniture():
    furn = {}
    for fid, slot, zh, price, src, fn in F.CATALOG:
        r = fn(); d = os.path.join(OUT, "furniture"); ent = {"slot": slot, "zh": zh, "price": price, "source": src, "sourceZh": SOURCE_ZH[src]}
        if slot == "bed":
            back, front = r; save(back, os.path.join(d, f"{fid}.png")); save(front, os.path.join(d, f"{fid}_front.png"))
            ent.update(png=f"furniture/{fid}.png", front=f"furniture/{fid}_front.png", pivot=list(F.BPIV), size=[F.BW, F.BH],
                       colors=[ncolors(back), ncolors(front)],
                       sleepSpots=[[-20, -12], [20, -12]], sleepNote="兩隻寵物 pivot＝床 anchor＋sleepSpots（左團絨、右細佬；向內 flip）；被（front）遮住下半身")
        elif slot == "lamp":
            img, em, glow, gc = r; save(img, os.path.join(d, f"{fid}.png"))
            e = np.zeros((*em.shape, 4), np.uint8); e[em] = (255, 255, 255, 255); save(e, os.path.join(d, f"{fid}_emissive.png"))
            save(glow, os.path.join(d, f"{fid}_glow.png"))
            ent.update(png=f"furniture/{fid}.png", emissive=f"furniture/{fid}_emissive.png", glow=f"furniture/{fid}_glow.png",
                       glowCenter=gc, glowNote="夜晚（及日間 0.35）用 lighter 疊 glow，中心對 sprite 內 glowCenter；glow 係 8-bit alpha（唯一例外）",
                       pivot=[F.LW_ // 2, F.LH_ - 1], size=[F.LW_, F.LH_], colors=ncolors(img))
        else:
            img = r; save(img, os.path.join(d, f"{fid}.png")); h, w = img.shape[:2]
            piv = {"window": list(F.WIN_HOLE_C), "wall": [w // 2, h // 2], "rug": [w // 2, h // 2], "table": [w // 2, h - 1]}[slot]
            ent.update(png=f"furniture/{fid}.png", pivot=piv, size=[w, h], colors=ncolors(img))
        if slot in SHADOW: ent["shadow"] = SHADOW[slot]
        furn[fid] = ent
    return furn

def house_json(furn, room_meta):
    acts = json.load(open(os.path.join(OUT, "actions", "actions_house.json")))
    slots = {}
    for s in SLOT_ORDER:
        slots[s] = dict(SLOTS[s]); slots[s]["items"] = [f for f, e in furn.items() if e["slot"] == s]
        if s in FOOT: slots[s]["blocker"] = FOOT[s]
    shop = [f for f, e in furn.items() if e["source"] == "shop"]
    J = {
     "version": "4b-1.0", "spec": "docs-gdd/series2-4a4b-spec.md §4b＋美術清單 4b",
     "grid": {"art": [195, 422], "layer": [223, 446], "layerOffset": [14, 12], "display": "×2 nearest"},
     "room": {"variants": {"day": "room/day/", "night": "room/night/"}, "switch": "同花園時段一樣 19:00／06:00 crossfade 2–4 秒",
              "files": ["sky.png", "far.png", "mid.png", "fore.png", "raw/*.png", "lightmap.png", "light_add.png", "emissive.png", "emissive_blur.png", "vignette.png", "grade.json", "palette.json"],
              "format": "同 scenes/hd2d/FORMAT.md（疊層同公式一樣）；窗洞喺 far 層透明 → 見 sky 層窗外景", "rawColors": room_meta,
              "parallaxSuggest": {"sky": 0.5, "far": 1.0, "mid": 1.0, "fore": 1.3, "note": "室內：far/mid 一齊郁（牆地唔可以錯位），只係窗外同前景有少少視差"},
              "window": {"hole": [30, 98, 76, 150]}, "safeArea": {"topHud": [0, 52], "bottomUi": [322, 422]}},
     "slots": slots, "slotOrder": SLOT_ORDER, "furniture": furn,
     "economy": {"shopItems": shop, "shopTotal": sum(furn[f]["price"] for f in shop), "range": [15, 40],
                 "note": "價錢係美術建議，遊策／遊測可改；換擺唔使碎；每件首次擺心情 +1（共用每日上限 5）"},
     "defaultState": {"slots": {s: None for s in SLOT_ORDER}, "note": "初始全部空位（只有房間背景）。冇床時夜晚一齊瞓用 4a duo.sleep_together（ov_blanket）喺地氈位"},
     "sets": SETS, "walk": WALK,
     "actions": {"file": "actions/actions_house.json", "clips": list(acts["clips"].keys()),
                 "forms": "細佬 34 階段＋團絨 25 形態全部有 strip（actions/<form>_<clip>.png）",
                 "reuse": {"tr": "團絨 walk／idle／sleep 用 evo_* 現有 clip；細佬用 series2/actions/<K>_{walk,idle,sleep}.png", "touch": "屋入面撳寵物＝3a 觸摸反應（同花園一樣）"}},
     "duo": {
      "sit_together": {"durationMs": 6000, "loop": True, "spot": "rug anchor（冇地氈就 (100,290)）",
                       "actors": {"tr": {"dx": -18, "dy": 2, "flip": False, "clip": "sit"}, "kid": {"dx": 18, "dy": 2, "flip": True, "clip": "sit"}},
                       "overlays": [{"id": "fx_heart", "anchor": "between", "dy": -30, "everyMs": 2400, "durMs": 900}],
                       "note": "兩隻行到位 → 同時播 sit（0–1 格坐落一次，之後 2–5 loop）；每 2.4 秒中間出一粒心心"},
      "sleep_same_bed": {"loop": True, "spot": "bed anchor＋sleepSpots",
                         "actors": {"tr": {"spot": 0, "flip": False, "clip": "sleep_loop（團絨現有）"}, "kid": {"spot": 1, "flip": True, "clip": "sleep（4a strip）"}},
                         "layers": ["bed.back", "tr", "kid", "bed.front"], "engineFx": [{"id": "fx_zzz", "anchor": "headTop", "dx": 6, "who": "both", "offsetMs": [0, 600]}],
                         "time": "21:00–03:00 兩隻都瞓（同 4a 一齊瞓 +2 親密，每晚 1 次）", "fallback": "冇床 → 4a duo.sleep_together（地氈位）"},
      "prank": {"durationMs": 2400, "loop": False, "who": "隨機一隻做整蠱人（細佬 70%）",
                "track": [
                  {"t": 0, "victim": "idle（背向整蠱人）", "prankster": "walk 去 victim 後面 30px"},
                  {"t": 0, "rel": "prankster 起步位＝victim.x − 30（victim 面向右）；prank_do 0–2 格每格 +2px（停喺 −24）"},
                  {"t": 0, "clip": {"prankster": "prank_do", "victim": "prank_got"}, "note": "兩條 strip 同時開始；第 4 格（480ms）一齊彈＝「哇！」"},
                  {"t": 960, "both": "laugh 完 → victim flip 面向整蠱人；兩隻播 sit 1 loop 再各自散"}],
                "rule": "每日最多 3 次；兩隻都企喺地（唔喺床）先觸發；唔加親密（純睇）"}},
     "ui": json.load(open(os.path.join(OUT, "ui", "layout.json"))) if os.path.exists(os.path.join(OUT, "ui", "layout.json")) else None,
    }
    json.dump(J, open(os.path.join(OUT, "house.json"), "w"), ensure_ascii=False, indent=1)
    return J

if __name__ == "__main__":
    meta = R.build_room(os.path.join(OUT, "room"))
    furn = build_furniture(); J = house_json(furn, meta)
    print("room", meta, "furniture", len(furn), "shopTotal", J["economy"]["shopTotal"])
