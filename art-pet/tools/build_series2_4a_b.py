# series2 4a 第 B 部：8 道具、新 FX、團絨教錯 8 段（~3s）、細佬照抄錯 8 段（~2s）、預覽 GIF
import os, json, copy
import numpy as np
from PIL import Image
import reactions_lib as L
import build_series2_4a as B
import series2_props as P
from series2_lib import S2, save, canvas, paste, limit_colors, WHITE, EYE_DK

OUT = S2
TR_DEFAULT = "evo_still_lumi"
OLD_FACES = ["blink", "squint", "squint_blush", "laugh_a", "laugh_b", "dizzy_a", "dizzy_b", "sleepy", "sleep", "surprised", "smug", "embarrassed", "lookup"]

def assets():
    A = {"fx": L.build_fx(), "series": {}}
    A["fx"]["fx2_tear"] = B.tear_fx()
    A["fx"].update(P.fx2())
    PR = P.props()
    for k, v in PR.items(): A["fx"]["prop_" + k] = {"frames": v["frames"], "pivot": v["pivot"], "note": v["note"]}
    return A, PR

def hold(pid, t0, t1, anchor="side_r", dx=3, dy=0, frames=None, ms=200, move=None, z="front", mirrorX=0):
    f = {"id": "prop_" + pid, "anchor": anchor, "dx": dx, "dy": dy, "t0": t0, "t1": t1, "ms": ms, "z": z}
    if frames is not None: f["frames"] = frames; f["loop"] = True
    if move: f["move"] = move
    if mirrorX: f["mirrorX"] = 1
    return f
def fx(i, a, t0, t1, dx=0, dy=0, ms=150, loop=True, frames=None, **kw):
    f = {"id": i, "anchor": a, "dx": dx, "dy": dy, "t0": t0, "t1": t1, "ms": ms, "loop": loop}
    if frames is not None: f["frames"] = frames
    f.update(kw); return f

# ───────── 團絨教錯（3000ms；團絨只用 3a 表情） ─────────
DEMO = {
 "A": {"prop": "can", "title": "淋花 → 淋自己個頭", "body": [
        {"t": 0}, {"t": 600, "y": -1, "sy": 1.03}, {"t": 900, "y": 0, "sy": 0.95, "sx": 1.04}, {"t": 1800, "sy": 0.96, "sx": 1.03},
        {"t": 1900, "x": -1, "sy": 1, "sx": 1}, {"t": 2000, "x": 1}, {"t": 2100, "x": -1}, {"t": 2200, "x": 1}, {"t": 2300, "x": 0}, {"t": 2500, "y": -1}, {"t": 3000, "y": 0}],
       "face": [{"t": 0, "f": "smug"}, {"t": 900, "f": "squint"}, {"t": 1300, "f": "surprised"}, {"t": 1850, "f": ["dizzy_a", "dizzy_b"], "ms": 100}, {"t": 2400, "f": "smug"}],
       "fx": [hold("can", 0, 700, frames=[0]), hold("can", 700, 1800, anchor="headTop", dx=7, dy=-3, frames=[1]),
              fx("fx2_drops", "headTop", 900, 1800, dx=-1, dy=-1, ms=120), fx("fx2_splash", "center", 1850, 2350, dy=2, ms=100),
              fx("fx_sparkle", "headTop", 2400, 3000, dx=8, dy=-2, ms=120)]},
 "B": {"prop": "wand", "title": "吹泡泡 → 自己入咗泡泡", "body": [
        {"t": 0}, {"t": 700, "sy": 1.04, "sx": 0.97}, {"t": 1300, "sy": 1, "sx": 1}, {"t": 1500, "y": -6, "e": "out"}, {"t": 2200, "y": -8},
        {"t": 2350, "y": 0, "e": "in"}, {"t": 2450, "sy": 0.9, "sx": 1.08}, {"t": 2600, "sy": 1, "sx": 1}, {"t": 3000}],
       "face": [{"t": 0, "f": "squint"}, {"t": 700, "f": "blink"}, {"t": 1300, "f": "surprised"}, {"t": 2350, "f": ["dizzy_a", "dizzy_b"], "ms": 100}, {"t": 2650, "f": "smug"}],
       "fx": [hold("wand", 0, 1300, anchor="mouth", dx=5, dy=1), fx("fx2_bubble", "center", 700, 2350, ms=300, loop=False, frames=[0, 1, 2, 2, 2, 2]),
              fx("fx2_bubble", "center", 2350, 2550, frames=[3]), fx("fx_sparkle", "headTop", 2650, 3000, dx=8, ms=120)]},
 "C": {"prop": "match", "title": "點火柴 → 用個頭擦", "body": [
        {"t": 0}, {"t": 500, "sy": 0.97}, {"t": 600, "x": -1}, {"t": 700, "x": 1}, {"t": 800, "x": -1}, {"t": 900, "x": 1}, {"t": 1000, "x": 0, "sy": 1},
        {"t": 1300, "y": -5, "e": "out"}, {"t": 1500, "y": 0, "e": "in"}, {"t": 1600, "sy": 0.92, "sx": 1.06}, {"t": 1800, "sy": 1, "sx": 1}, {"t": 3000}],
       "face": [{"t": 0, "f": "smug"}, {"t": 550, "f": "squint"}, {"t": 1150, "f": "surprised"}, {"t": 1700, "f": "embarrassed"}, {"t": 2400, "f": "smug"}],
       "fx": [hold("match", 0, 550, frames=[0]), hold("match", 550, 1100, anchor="headTop", dx=0, dy=-2, frames=[0], move=[[0, -4, 0], [100, 4, 0], [200, -4, 0], [300, 4, 0], [400, -4, 0], [550, 3, 0]]),
              hold("match", 1100, 2400, anchor="side_r", dx=3, frames=[1], ms=120), fx("fx_puff", "headTop", 1100, 1500, dy=-2, ms=100, loop=False),
              fx("fx2_steam", "headTop", 1500, 3000, dy=-2, ms=200), fx("fx_sweat", "headTop", 1700, 2400, dx=-8, dy=4, ms=150)]},
 "D": {"prop": "pebble", "title": "孵蛋 → 坐喺石仔上面孵", "body": [
        {"t": 0}, {"t": 600, "x": 0, "y": 0}, {"t": 800, "y": -6, "e": "out"}, {"t": 1000, "y": -4, "sy": 0.94, "sx": 1.05, "e": "in"},
        {"t": 1800, "y": -4, "sy": 0.96, "sx": 1.04}, {"t": 2000, "rot": -6}, {"t": 2300, "rot": -6}, {"t": 2500, "rot": 0}, {"t": 3000, "y": -4}],
       "rotStep": 3,
       "face": [{"t": 0, "f": "smug"}, {"t": 1000, "f": "squint_blush"}, {"t": 1950, "f": "lookup"}, {"t": 2500, "f": "smug"}],
       "fx": [hold("pebble", 0, 700, anchor="side_r", dx=2, dy=2), fx("prop_pebble", "pivot", 700, 3000, dy=1, follow=False, z="back"),
              fx("fx_question", "headTop", 1950, 2500, dx=8, dy=-3, ms=150), fx("fx_heart", "headTop", 2550, 3000, dx=-8, ms=150)]},
 "E": {"prop": "chili", "title": "食辣椒 → 當士多啤梨", "body": [
        {"t": 0}, {"t": 700, "sy": 1.04}, {"t": 800, "sy": 0.94, "sx": 1.05}, {"t": 1100, "sy": 1, "sx": 1}, {"t": 1300, "y": -4, "e": "out"},
        {"t": 1500, "x": -1, "y": -3}, {"t": 1600, "x": 1}, {"t": 1700, "x": -1}, {"t": 1800, "x": 1}, {"t": 1900, "x": -1}, {"t": 2000, "x": 1}, {"t": 2200, "x": 0, "y": 0, "e": "in"}, {"t": 3000}],
       "face": [{"t": 0, "f": "squint_blush"}, {"t": 800, "f": ["laugh_b", "squint"], "ms": 120}, {"t": 1150, "f": "surprised"}, {"t": 1400, "f": "laugh_a"}, {"t": 2300, "f": "smug"}],
       "fx": [hold("chili", 0, 800, anchor="chest", dx=6, dy=-4), fx("fx_exclaim", "headTop", 1150, 1500, dx=8, dy=-4),
              fx("fx2_fire", "mouth", 1400, 2300, dx=4, dy=-1, ms=100), fx("fx_sweat", "headTop", 1400, 2300, dx=-8, dy=4, ms=150), fx("fx2_steam", "headTop", 2300, 3000, dy=-2, ms=200)]},
 "F": {"prop": "scope", "title": "望遠鏡 → 拎倒轉睇", "body": [
        {"t": 0}, {"t": 1600}, {"t": 1800, "x": 4}, {"t": 2000, "x": 7}, {"t": 2050, "x": 5, "sx": 0.92}, {"t": 2200, "x": 4, "sx": 1}, {"t": 2700, "x": 2}, {"t": 3000, "x": 0}],
       "face": [{"t": 0, "f": "smug"}, {"t": 600, "f": "lookup"}, {"t": 2050, "f": ["dizzy_a", "dizzy_b"], "ms": 100}, {"t": 2600, "f": "smug"}],
       "fx": [hold("scope", 0, 600, anchor="side_r", dx=2, frames=[0]), hold("scope", 600, 2050, anchor="eyeR", dx=7, dy=1, frames=[1]),
              fx("fx2_tiny", "eyeR", 900, 1600, dx=17, dy=0, ms=200), fx("fx_star_orbit", "headTop", 2050, 2600, dy=-2, ms=100)]},
 "G": {"prop": "book", "title": "讀故仔 → 拎倒轉本書，讀到瞓著", "body": [
        {"t": 0}, {"t": 1600, "sy": 1.0}, {"t": 2000, "y": 1, "sy": 0.96, "sx": 1.03}, {"t": 2400, "sy": 0.97}, {"t": 2700, "sy": 0.96}, {"t": 3000, "sy": 0.97}],
       "face": [{"t": 0, "f": "smug"}, {"t": 700, "f": "lookup"}, {"t": 1300, "f": "sleepy"}, {"t": 1900, "f": "sleep"}],
       "fx": [hold("book", 0, 1900, anchor="chest", dx=0, dy=-3, frames=[1]), hold("book", 1900, 3000, anchor="pivot", dx=10, dy=0, frames=[2]),
              fx("fx_zzz", "headTop", 2000, 3000, dx=7, dy=-1, ms=300)]},
 "H": {"prop": "moonlamp", "title": "月亮燈 → 當帽戴", "body": [
        {"t": 0}, {"t": 700, "y": -3, "e": "out"}, {"t": 900, "y": 0, "e": "in"}, {"t": 1300}, {"t": 1500, "x": -2}, {"t": 1800, "x": 2}, {"t": 2100, "x": 0},
        {"t": 2300, "sy": 0.95}, {"t": 2500, "sy": 1}, {"t": 3000}],
       "face": [{"t": 0, "f": "smug"}, {"t": 900, "f": "squint_blush"}, {"t": 2250, "f": "embarrassed"}, {"t": 2650, "f": "smug"}],
       "fx": [hold("moonlamp", 0, 700, anchor="side_r", dx=3, frames=[0]), hold("moonlamp", 700, 3000, anchor="headTop", dx=0, dy=1, frames=[1],
              move=[[0, 0, 0], [1550, 0, 0], [1700, 0, 9], [2300, 0, 9]]), fx("fx_sparkle", "headTop", 1000, 1500, dx=10, dy=-6, ms=120)]},
}
FACE_COPY = {"smug": "happy", "embarrassed": "pout", "lookup": "surprised"}   # 細佬冇 lookup／smug 嘅感覺 → 換成佢自己嘅表情

def scale_clip(c, k):
    c = copy.deepcopy(c)
    for b in c["body"]: b["t"] = int(round(b["t"] * k))
    for f in c["face"]:
        f["t"] = int(round(f["t"] * k))
        if isinstance(f["f"], str): f["f"] = FACE_COPY.get(f["f"], f["f"])
    for f in c["fx"]:
        f["t0"] = int(round(f["t0"] * k)); f["t1"] = int(round(f["t1"] * k)); f["ms"] = max(80, int(f.get("ms", 150) * k))
        if f.get("move"): f["move"] = [[int(m[0] * k), m[1], m[2]] for m in f["move"]]
    return c

def clip_frames(comp, clip, dur, step=100):
    return [B.render_frame(comp, clip, t) for t in range(0, dur, step)]

def write_gif(frames, path, scale=3, ms=100, bg=(92, 84, 120)):
    ims = []
    for f in frames:
        o = Image.new("RGBA", (f.shape[1], f.shape[0]), bg + (255,)); o.alpha_composite(Image.fromarray(f))
        ims.append(o.convert("RGB").resize((f.shape[1] * scale, f.shape[0] * scale), Image.NEAREST))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=ms, loop=0)

def main():
    A, PR = assets()
    od = os.path.join(OUT, "lessons"); os.makedirs(od, exist_ok=True)
    # 道具＋新 FX 圖
    pidx = {}
    for row, (pid, zh) in P.PROP_SERIES.items():
        v = PR[pid]; fr = v["frames"]
        save(np.concatenate(fr, 1), os.path.join(od, "props", f"prop_{pid}.png"))
        pidx[row] = {"id": "prop_" + pid, "zh": zh, "png": f"lessons/props/prop_{pid}.png", "frameW": fr[0].shape[1], "frameH": fr[0].shape[0],
                     "frames": len(fr), "pivot": v["pivot"], "note": v["note"]}
    fx2 = {}
    for k, v in P.fx2().items():
        save(np.concatenate(v["frames"], 1), os.path.join(od, "fx", f"{k}.png"))
        fx2[k] = {"png": f"lessons/fx/{k}.png", "frameW": v["frames"][0].shape[1], "frameH": v["frames"][0].shape[0], "frames": len(v["frames"]), "pivot": v["pivot"], "note": v["note"]}
    save(np.concatenate(A["fx"]["fx2_tear"]["frames"], 1), os.path.join(od, "fx", "fx2_tear.png"))
    fx2["fx2_tear"] = {"png": "lessons/fx/fx2_tear.png", "frameW": 2, "frameH": 3, "frames": 1, "pivot": [1, 0], "note": A["fx"]["fx2_tear"]["note"]}
    # 細佬新表情 patch（S1／S2／S4×8；團絨只用 3a 現有表情）
    face_idx = {}
    for k in B.NEWF:
        r = B.rig_of(k); comp = B.Comp2(r, A); strip = []
        names = OLD_FACES + B.NEW_FACES
        for n in names: strip.append(comp.faces[n])
        save(np.concatenate(strip, 1), os.path.join(OUT, "faces", f"{k}_faces.png"))
        face_idx[k] = {"png": f"faces/{k}_faces.png", "order": names, "note": "patch：只得同 idle 幀 0 唔同嘅像素；引擎疊上去"}
    # 教錯 + 抄錯
    tr = L.rig_old(TR_DEFAULT); ctr = B.Comp2(tr, A)
    s2 = B.rig_of("S2"); cs2 = B.Comp2(s2, A)
    demos, copies = {}, {}
    for row, d in DEMO.items():
        dclip = {"durationMs": 3000, "loop": False, "who": "團絨（任何 evo_still_* 靜光形態）", "title": d["title"], "prop": "prop_" + d["prop"],
                 "body": d["body"], "face": d["face"], "fx": d["fx"]}
        if "rotStep" in d: dclip["rotStep"] = d["rotStep"]
        cclip = scale_clip(dclip, 2 / 3); cclip.update({"durationMs": 2000, "who": "細佬 S2 BB（其他階段同一份 JSON 用 rig 錨點都得）", "title": "照抄：" + d["title"]})
        for c in (dclip, cclip):
            for f in c["face"]:
                for n in (f["f"] if isinstance(f["f"], list) else [f["f"]]): assert n in L.FACES, n
        assert all(f["f"] in OLD_FACES or isinstance(f["f"], list) for f in dclip["face"])
        demos[row] = dclip; copies[row] = cclip
        df = clip_frames(ctr, dclip, 3000)   # 預覽唔壓色（道具係引擎疊層，唔計入 sprite 12 色）
        cf = clip_frames(cs2, cclip, 2000)
        # 預覽：團絨教（左），細佬學（右）
        seq = []
        idle_s2 = B.Comp2(s2, A)
        for i, f in enumerate(df):
            o = canvas(104, 56); paste(o, f, 4, 6)
            paste(o, B.render_frame(idle_s2, {"body": [{"t": 0}], "face": [{"t": 0, "f": "surprised" if i > 10 else None}]}, 0), 52, 6); seq.append(o)
        for i, f in enumerate(cf):
            o = canvas(104, 56); paste(o, B.render_frame(ctr, {"body": [{"t": 0}], "face": [{"t": 0, "f": "smug" if i < 14 else "embarrassed"}]}, 0), 4, 6)
            paste(o, f, 52, 6); seq.append(o)
        write_gif(seq, os.path.join(OUT, "preview", f"lesson_{row}.gif"))
        save(np.concatenate(df[::3], 1), os.path.join(od, "_preview", f"demo_{row}_contact.png"))
    json.dump({"note": "團絨示範（錯）＋細佬照抄（錯）。座標同 3a reactions clip schema 一樣（body/face/fx，anchor 用 rig 錨點）。道具係 fx id prop_*。",
               "propsBySeries": pidx, "fx2": fx2, "demo": demos, "copy": copies},
              open(os.path.join(od, "lessons.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(face_idx, open(os.path.join(OUT, "faces", "faces.json"), "w"), ensure_ascii=False, indent=1)
    print("lessons ok", list(demos))

if __name__ == "__main__":
    main()
