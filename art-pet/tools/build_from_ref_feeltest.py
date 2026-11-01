#!/usr/bin/env python3
"""build_from_ref_feeltest — 將 from_ref/tuned 24 隻放入《微光小圃》HD-2D 場景（H1–H4）做 canvas2D 手感測試頁。
抄場景層＋寵物 idle strip（64／80／96 三個尺寸：assets/pets{S}/）入 feeltest/assets（自足，可直接開 index.html），寫 data.js。用法：python3 build_from_ref_feeltest.py"""
import os, json, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); ART = os.path.dirname(HERE)
FR = os.path.join(ART, "sprites/tuanrong/species_concept/from_ref"); TU = os.path.join(FR, "tuned"); FT = os.path.join(FR, "feeltest")
SC = os.path.join(ART, "scenes/hd2d")
LAY = ("sky", "far", "mid", "fore", "lightmap", "light_add", "emissive_blur", "vignette")
def main():
    A = os.path.join(FT, "assets")
    if os.path.isdir(A): shutil.rmtree(A)
    scenes = {}
    for h in ("H1", "H2", "H3", "H4"):
        os.makedirs(os.path.join(A, "scenes", h), exist_ok=True)
        for l in LAY: shutil.copy(os.path.join(SC, h, l + ".png"), os.path.join(A, "scenes", h, l + ".png"))
        g = json.load(open(os.path.join(SC, h, "grade.json")))
        scenes[h] = {k: g[k] for k in ("name", "ambientTint", "petTint", "bloom", "fog", "bulbGlowTint", "particles")}
    T = json.load(open(os.path.join(TU, "tuned.json"))); pets = []; sizes = {}
    for k, m in T["creatures"].items():
        pets.append({"key": k, "name": m["name"], "bulb": m["bulbXY"], "glow": m["glowTint"], "blink": m["blink"]})
    for S in (64, 80, 96):
        D = os.path.join(FR, "tuned" if S == 64 else f"tuned_{S}"); TS = json.load(open(os.path.join(D, "tuned.json")))
        os.makedirs(os.path.join(A, f"pets{S}"), exist_ok=True)
        for k in TS["creatures"]: shutil.copy(os.path.join(D, "idle", f"{k}_idle.png"), os.path.join(A, f"pets{S}", f"{k}_idle.png"))
        sizes[S] = {"pivot": TS["pivot"], "bulb": {k: m["bulbXY"] for k, m in TS["creatures"].items()},
                    "blink": {k: m["blink"] for k, m in TS["creatures"].items()}}
    L = json.load(open(os.path.join(SC, "layout.json")))
    data = {"art": L["artSize"], "layer": L["layerSize"], "off": L["layerOffset"], "parallax": L["parallaxSuggest"],
            "foot": L["pet"]["foot"], "pivot": T["pivot"], "idleMs": T["idle"]["durationsMs"], "sizes": sizes, "scenes": scenes, "pets": pets}
    open(os.path.join(FT, "data.js"), "w").write("window.FEEL = " + json.dumps(data, ensure_ascii=False) + ";\n")
    print("feeltest assets ok:", len(pets), "pets,", len(scenes), "scenes")
if __name__ == "__main__": main()
