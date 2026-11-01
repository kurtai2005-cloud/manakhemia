#!/usr/bin/env python3
"""build_from_ref_engine80 — from_ref/tuned_80（正式版 80px，Kurt [pt94u]）→ 引擎交付：
atlas/pets_idle_80.png（4 欄×24 行）＋ atlas/pets_idle_80.json（frame rect／pivot／durations）、
bulb_anchors_80.json（每隻燈泡 glow 錨點，逐幀）、lineup_80_4x.png。純 Pillow／numpy。
用法：python3 build_from_ref_engine80.py（先跑 build_from_ref_tuned.py all --size 80）"""
import os, json, shutil
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ART = os.path.dirname(HERE)
D = os.path.join(ART, "sprites/tuanrong/species_concept/from_ref/tuned_80"); S = 80
def main():
    T = json.load(open(os.path.join(D, "tuned.json"))); C = T["creatures"]; keys = list(C)
    piv = T["pivot"]; dur = T["idle"]["durationsMs"]; os.makedirs(os.path.join(D, "atlas"), exist_ok=True)
    atlas = Image.new("RGBA", (4 * S, len(keys) * S), (0, 0, 0, 0)); frames = {}; anims = {}; bulbs = {}
    for r, k in enumerate(keys):
        st = Image.open(os.path.join(D, "idle", f"{k}_idle.png")).convert("RGBA"); atlas.paste(st, (0, r * S))
        names = []
        for f in range(4):
            n = f"{k}_idle_{f}"; names.append(n)
            frames[n] = {"frame": {"x": f * S, "y": r * S, "w": S, "h": S}, "pivot": {"x": piv[0], "y": piv[1]}, "pivotNorm": {"x": piv[0] / S, "y": piv[1] / S}, "durationMs": dur[f]}
        anims[f"{k}_idle"] = names
        # 幀 1 係上半身（主體高度 60% 以上）落 1px → 燈泡喺 cut 以上就跟住落 1px
        a = np.array(st.crop((0, 0, S, S)))[..., 3] == 255; body = np.nonzero(a.any(1))[0]
        cut = int(body.min() + 0.6 * (body.max() - body.min())); bx, by = C[k]["bulbXY"]
        per = [[bx, by], [bx, by + (1 if by <= cut else 0)], [bx, by], [bx, by]]
        kind = "own" if "own" in str(C[k]["bulb"]) else "star" if "星" in str(C[k]["bulb"]) else "bulb"
        bulbs[k] = {"name": C[k]["name"], "anchor": [bx, by], "perFrame": per, "fromFoot": [bx - piv[0], by - piv[1]], "type": kind, "glowTint": C[k]["glowTint"]}
    atlas.save(os.path.join(D, "atlas", "pets_idle_80.png"), optimize=True)
    json.dump({"meta": {"image": "pets_idle_80.png", "size": {"w": atlas.width, "h": atlas.height}, "format": "RGBA8888", "frameSize": S,
                        "pivot": piv, "pivotRule": "bottom-centre (w/2, h-3)；地線 y=77", "filter": "nearest", "layout": "每行一隻（A1..H3），4 欄＝idle 幀 0..3"},
               "frames": frames, "animations": anims}, open(os.path.join(D, "atlas", "pets_idle_80.json"), "w"), ensure_ascii=False, indent=1)
    json.dump({"size": S, "pivot": piv, "coord": "sprite 左上角 (0,0)、px；fromFoot＝相對 pivot", "glowRadiusPx": 14,
               "creatures": bulbs}, open(os.path.join(D, "bulb_anchors_80.json"), "w"), ensure_ascii=False, indent=1)
    shutil.copy(os.path.join(D, "lineup_4x.png"), os.path.join(D, "lineup_80_4x.png"))
    print("engine80 ok:", len(keys), "pets; atlas", atlas.size)
if __name__ == "__main__": main()
