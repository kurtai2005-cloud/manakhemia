# 《微光小圃》4b 屋仔 — 屋內動作 2（坐、整蠱）× 全部形態（細佬 34＋團絨 25），純 Pillow/numpy，冇 AI 生圖
# 重跑：cd art-pet && python3 tools/build_house_4b_actions.py
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reactions_lib as L
import build_series2_4a as B          # 借 4a 嘅 rig_of、Comp2、render_frame、新表情（happy／pout…）
from series2_lib import ART, save, canvas, paste, limit_colors, EYE_DK, WHITE

OUT = os.path.join(ART, "sprites/series2_house")
TR_FORMS = L.OLD_FORMS                       # 團絨 25 個可穿戴形態（3a 同一套）
KID_FORMS = B.ALL34                          # 細佬 34 階段
PAD_X, PAD_TOP = 4, 14                       # 整蠱有跳：strip 加 padding（左右各 4、頂 14）

LAUGH = [{"id": "fx_laugh_l", "anchor": "side_l", "dx": -1}, {"id": "fx_laugh_r", "anchor": "side_r", "dx": 1}]
def laugh(t0, t1): return [dict(f, t0=t0, t1=t1, ms=120) for f in LAUGH]
CLIPS = {
 "sit": {"frames": 6, "frameMs": 150, "loop": True, "loopFrom": 2, "pad": False,
         "note": "坐低：0–1 坐落（一次）、2–5 loop（每格 150ms，第 5 格眨眼）。坐埋一齊用 house.json duo.sit_together",
         "body": [{"t": 0, "sx": 1.03, "sy": 0.95}, {"t": 150, "sx": 1.1, "sy": 0.86}, {"t": 300, "sx": 1.07, "sy": 0.9},
                  {"t": 450, "sx": 1.08, "sy": 0.89}, {"t": 600, "sx": 1.07, "sy": 0.9}, {"t": 750, "sx": 1.07, "sy": 0.9}],
         "face": [{"t": 0, "f": "squint"}, {"t": 750, "f": "blink"}]},
 "prank_do": {"frames": 8, "frameMs": 120, "loop": False, "pad": True,
              "note": "整蠱人：0–2 踮腳行埋去（引擎每格移 2px 向對方）、3 縮低、4「哇！」彈起、5–7 笑到碌（同 prank_got 第 4 格對齊）",
              "body": [{"t": 0, "y": 0, "sy": 1.03, "sx": 0.98}, {"t": 120, "y": -1, "sy": 0.98, "sx": 1.02}, {"t": 240, "y": 0, "sy": 1.03, "sx": 0.98},
                       {"t": 360, "y": 0, "sy": 0.85, "sx": 1.12}, {"t": 480, "y": -6, "sy": 1.12, "sx": 0.94}, {"t": 600, "y": -3, "sy": 1.04, "sx": 0.98},
                       {"t": 720, "y": 0, "sy": 0.93, "sx": 1.07, "rot": -4}, {"t": 840, "y": 0, "sy": 1.0, "sx": 1.0, "rot": 4}],
              "face": [{"t": 0, "f": "smug"}, {"t": 480, "f": "laugh_a"}, {"t": 720, "f": "laugh_b"}, {"t": 840, "f": "laugh_a"}],
              "fx": [{"id": "fx_sparkle", "anchor": "headTop", "dx": 7, "dy": -2, "t0": 480, "t1": 600, "ms": 120}] + laugh(720, 960)},
 "prank_got": {"frames": 8, "frameMs": 120, "loop": False, "pad": True,
               "note": "被整蠱：0–3 唔知情（望前面）、4 嚇親彈高＋！、5 驚到出汗、6 落地縮、7 一齊笑",
               "body": [{"t": 0}, {"t": 120, "sy": 1.01}, {"t": 240}, {"t": 360, "sy": 1.01},
                        {"t": 480, "y": -7, "sy": 1.14, "sx": 0.9}, {"t": 600, "y": -4, "sy": 1.06, "sx": 0.96},
                        {"t": 720, "y": 0, "sy": 0.86, "sx": 1.12}, {"t": 840, "y": 0, "sy": 1.0, "sx": 1.0, "rot": 3}],
               "face": [{"t": 0, "f": None}, {"t": 360, "f": "blink"}, {"t": 480, "f": "surprised"}, {"t": 720, "f": "embarrassed"}, {"t": 840, "f": "laugh_b"}],
               "fx": [{"id": "fx_exclaim", "anchor": "headTop", "dx": 0, "dy": -3, "t0": 480, "t1": 720, "move": [[0, 0, 3], [100, 0, -1], [180, 0, 0]]},
                      {"id": "fx_sweat", "anchor": "side_r", "dx": 1, "dy": -2, "t0": 600, "t1": 840}] + laugh(840, 960)},
}

def bake():
    os.makedirs(os.path.join(OUT, "actions"), exist_ok=True)
    A = {"fx": L.build_fx(), "series": {}}
    idx = {}
    for k in KID_FORMS + TR_FORMS:
        r = B.rig_of(k); H, W = r.base.shape[:2]; px, py = r.pivot
        who = "kid" if k in KID_FORMS else "tr"
        idx[k] = {"who": who, "size": [W, H], "pivot": [px, py]}
        for name, c in CLIPS.items():
            pw, pt = (PAD_X, PAD_TOP) if c["pad"] else (0, 0)
            FW, FH = W + 2 * pw, H + pt
            comp = B.Comp2(r, A, CW=FW, CH=FH, PX=px + pw, PY=py + pt)
            clip = {"body": c["body"], "face": c["face"], "fx": c.get("fx", [])}
            frames = []
            for i in range(c["frames"]):
                fr = B.render_frame(comp, clip, i * c["frameMs"])
                if k in B.NEWF: fr = limit_colors(fr, 12, protect=[r.outline, EYE_DK, WHITE, L.TONGUE])
                frames.append(fr)
            save(np.concatenate(frames, 1), os.path.join(OUT, "actions", f"{k}_{name}.png"))
            idx[k][name] = {"png": f"actions/{k}_{name}.png", "frameW": FW, "frameH": FH, "pivot": [px + pw, py + pt]}
    meta = {"note": "屋內動作 2：坐（sit）、整蠱（prank_do 整蠱人／prank_got 被整蠱）。細佬 34 階段＋團絨 25 形態一律烘焙 strip；clip 定義用 3a reactions schema。"
                    "sit 同原 sprite 一樣大；prank 有跳，strip 每格左右 +4、頂 +14px，pivot 跟住移（見每形態 pivot）。",
            "clips": CLIPS, "forms": idx}
    json.dump(meta, open(os.path.join(OUT, "actions", "actions_house.json"), "w"), ensure_ascii=False, indent=1)
    return meta

if __name__ == "__main__":
    m = bake(); print("forms", len(m["forms"]), "strips", 3 * len(m["forms"]))
