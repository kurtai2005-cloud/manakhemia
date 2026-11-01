# series2 4a 第 E 部：4x 陣容圖＋細佬 5 動作預覽 GIF
import os
import numpy as np
from PIL import Image, ImageDraw
from series2_lib import S2, rgba, canvas, paste
import build_series2_4a_b as BB

def frame0(k, act="idle", i=0):
    a = rgba(os.path.join(S2, "actions", f"{k}_{act}.png")); return a[:, i * 48:(i + 1) * 48]

def lineup():
    cols = ["egg", "S1", "S2", "S3", "S4", "S5", "S6"]; R = "ABCDEFGH"
    W, H = 48 * len(cols), 48 * len(R); o = canvas(W, H)
    egg = rgba(os.path.join(S2, "egg", "egg_48.png"))
    for j, r in enumerate(R):
        row = [egg, frame0("S1"), frame0("S2"), frame0(r + "1"), frame0("S4" + r), frame0(r + "2"), frame0(r + "3")]
        for i, a in enumerate(row): paste(o, a, i * 48, j * 48)
    im = Image.new("RGBA", (W * 4 + 40, H * 4 + 30), (92, 84, 120, 255))
    im.alpha_composite(Image.fromarray(o).resize((W * 4, H * 4), Image.NEAREST), (40, 30))
    d = ImageDraw.Draw(im)
    for i, c in enumerate(cols): d.text((40 + i * 192 + 84, 8), c, fill=(255, 240, 250))
    for j, r in enumerate(R): d.text((14, 30 + j * 192 + 90), r, fill=(255, 240, 250))
    p = os.path.join(S2, "preview", "lineup_4x.png"); im.convert("RGB").save(p); return p

def actions_gif(keys, name):
    acts = ["idle", "walk", "cry", "eat", "sleep"]
    strips = {(k, a): rgba(os.path.join(S2, "actions", f"{k}_{a}.png")) for k in keys for a in acts}
    ms = {"walk": 100, "cry": 150, "eat": 120, "sleep": 450}; idle = [260, 180, 260, 140]
    fr = []
    for t in range(0, 1800, 100):
        o = canvas(48 * len(acts), 48 * len(keys))
        for j, k in enumerate(keys):
            for i, a in enumerate(acts):
                s = strips[(k, a)]; n = s.shape[1] // 48
                if a == "idle":
                    lt = t % 840; acc = 0; f = 0
                    for f, m in enumerate(idle):
                        acc += m
                        if lt < acc: break
                else: f = (t // ms[a]) % n
                paste(o, s[:, f * 48:(f + 1) * 48], i * 48, j * 48)
        fr.append(o)
    BB.write_gif(fr, os.path.join(S2, "preview", name), scale=3)

if __name__ == "__main__":
    print(lineup())
    actions_gif(["S1", "S2", "S4A", "S4B", "S4C", "S4D"], "actions_new_1.gif")
    actions_gif(["S4E", "S4F", "S4G", "S4H"], "actions_new_2.gif")
    actions_gif(["A1", "B2", "C3", "D1", "E2", "F3", "G1", "H2"], "actions_existing_sample.gif")
    print("e ok")
