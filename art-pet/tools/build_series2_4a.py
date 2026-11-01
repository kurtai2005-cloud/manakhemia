# 《微光小圃》series2「細佬」batch 4a 美術 — 純 Pillow/numpy 程序生成（冇 AI 生圖）
# 重跑：cd art-pet && python3 tools/build_series2_4a.py   （輸出 sprites/series2/）
import json, os, shutil, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reactions_lib as L
import series2_forms as F
from series2_lib import *

OUT = S2
FORMS = os.path.join(OUT, "forms")
NEWF = ["S1", "S2"] + [f"S4{r}" for r in ROWS]
ALL34 = NEWF + L.NEW_KEYS                                  # 細佬每階：S1 S2 | S3=X1 S4 S5=X2 S6=X3
STAGE = {"S1": "S1 蛋殼仔", "S2": "S2 BB"}
for r in ROWS: STAGE.update({f"{r}1": f"S3 {r}", f"S4{r}": f"S4 {r} 少年", f"{r}2": f"S5 {r}", f"{r}3": f"S6 {r}"})
def series_key(k): return k[-1] if k.startswith("S4") else (k[0] if k in L.NEW_KEYS else None)

# ───────── 1. 新形態 ─────────
def eyes_meta(eyes, kind="dark"):
    return [{"x": int(x), "y": int(y), "kind": kind, "side": i, "lineC": list(EYE_DK)} for i, (x, y) in enumerate(eyes)]
def build_forms():
    os.makedirs(os.path.join(FORMS, "sprites"), exist_ok=True); os.makedirs(os.path.join(FORMS, "idle"), exist_ok=True)
    meta = {}
    # S1
    a, eyes, mm = F.s1()
    for (x, y) in eyes: draw_eye(a, x, y)
    meta["S1"] = (a, {"name": "蛋殼仔", "stage": "S1", "outline": hexs(F.OL), "eyes": eyes_meta(eyes), "bulbXY": mm["bulbXY"], "bulbType": "none",
                      "face": {"mouth": None, "blush": 3}, "note": "頂住上半殼、下半殼兜住，只露一對眼；全系共用"})
    b, eyes2, mm2 = F.s2_base()
    meta["S2"] = (b, {"name": "BB", "stage": "S2", "outline": hexs(F.OL), "eyes": eyes_meta(eyes2), "bulbXY": mm2["bulbXY"], "bulbType": "bulb",
                      "glowTint": "#fff4d0", "face": {"mouth": mm2["mouth"], "blush": 3}, "note": "圓粒＋細手腳＋頭頂未定色光（glow 交引擎）；全系共用"})
    for r in ROWS:
        img, m = F.s4(r)
        m.update(stage="S4", series=r)
        meta[f"S4{r}"] = (img, m)
    T = {"size": [S, S], "pivot": list(PIV), "groundRow": GROUND, "alpha": "0/255 only", "idle": {"frames": 4, "frameW": S, "durationsMs": [260, 180, 260, 140]},
         "creatures": {}}
    for k, (img, m) in meta.items():
        sk = [(e["x"], e["y"], ring_skin(img, e["x"], e["y"])) for e in m["eyes"]]
        fr, cut = idle_frames(img, sk)
        fr = [snap_to_palette(f, img) for f in fr]   # 眨眼幀唔准加新色
        save(img, os.path.join(FORMS, "sprites", f"{k}_48.png"))
        save(np.concatenate(fr, 1), os.path.join(FORMS, "idle", f"{k}_idle.png"))
        m.update(mass=int((img[..., 3] == 255).sum()), colors=ncolors(img), idleCut=cut)
        T["creatures"][k] = m
    json.dump(T, open(os.path.join(FORMS, "tuned.json"), "w"), ensure_ascii=False, indent=1)
    # 蛋：靜態＋裂紋 4 幀
    eg = [F.egg(c)[0] for c in range(4)]
    save(eg[0], os.path.join(OUT, "egg", "egg_48.png")); save(np.concatenate(eg, 1), os.path.join(OUT, "egg", "egg_crack.png"))
    return T

# ───────── rig（面／錨點）：新形態借 reactions_lib.rig_new ─────────
def snap_to_palette(f, ref):
    m = ref[..., 3] == 255; pal = np.unique(ref[m][:, :3], axis=0).astype(int)
    f = f.copy(); fm = f[..., 3] == 255
    for c in np.unique(f[fm][:, :3], axis=0):
        if not (pal == c).all(1).any():
            n = pal[np.argmin(((pal - c.astype(int)) ** 2).sum(1))]; sel = fm & (f[..., :3] == c).all(-1); f[sel, :3] = n
    return f

_RIG = {}
def rig_of(k):
    if k in _RIG: return _RIG[k]
    if k in L.NEW_KEYS or k in L.OLD_FORMS:
        r = L.rig(k)
    else:
        t48, so = L.T48, L.series_of
        L.T48 = FORMS
        L.series_of = lambda pid: ("s2_" + (pid[-1] if pid.startswith("S4") else "base"), L.NEW_SERIES.get(pid[-1], "star") if pid.startswith("S4") else "star")
        try: r = L.rig_new(k)
        finally: L.T48, L.series_of = t48, so
    _RIG[k] = r; return r

# 新表情（加落 reactions_lib.FACES；團絨只用 3a 現有表情）
L.FACES.update({"cry_a": ("xx", "wavy", None), "cry_b": ("xx", "open_small", None),
                "chew_o": ("arc", "open_small", "plus"), "chew_c": ("arc", "orig", "plus"),
                "happy": ("arc", "open_small", "plus"), "pout": ("open_down", "wavy", None)})
L.FACE_NOTE.update({"cry_a": "喊：> < ＋波浪口", "cry_b": "喊：> < ＋張口", "chew_o": "食：瞇眼張口", "chew_c": "食：瞇眼合口",
                    "happy": "開心：^ ^ 張口＋腮紅", "pout": "委屈：眼望低＋波浪口"})
NEW_FACES = ["cry_a", "cry_b", "chew_o", "chew_c", "happy", "pout"]

class Comp2(L.Comp):
    def __init__(self, r, assets, CW=48, CH=48, PX=24, PY=45):
        self.r, self.A, self.CW, self.CH, self.PX, self.PY = r, assets, CW, CH, PX, PY
        self.faces = {n: L.face_image(r, n)[1] for n in L.FACES}
        self.wear = {}; self.paw = [canvas(1, 1)]
        self.base_override = None
    def src_at(self, clip, t):
        img = (self.base_override if self.base_override is not None else self.r.base).copy()
        f = L.track_at(clip.get("face", []), t)
        if f: m = self.faces[f][..., 3] == 255; img[m] = self.faces[f][m]
        return img

# ───────── 2. 細佬 5 動作（所有 34 階段一律有 strip） ─────────
ACTIONS = {
 "walk": {"frames": 6, "frameMs": 100, "loop": True, "note": "跳步行（向右；向左＝flipX）。引擎每幀移 1px（約 10px/s 慢行，可調）",
          "body": [{"t": 0, "y": 0, "sx": 1.04, "sy": 0.96}, {"t": 100, "y": -1, "sx": 0.98, "sy": 1.03}, {"t": 200, "y": -2, "sx": 0.97, "sy": 1.04},
                   {"t": 300, "y": -1, "sx": 1.0, "sy": 1.0}, {"t": 400, "y": 0, "sx": 1.05, "sy": 0.95}, {"t": 500, "y": 0, "sx": 1.0, "sy": 1.0}],
          "face": [{"t": 0, "f": None}]},
 "cry": {"frames": 6, "frameMs": 150, "loop": True, "note": "喊（哄喊事件 loop；10 分鐘冇人理自己停）",
         "body": [{"t": 0, "x": 0, "sy": 0.97, "sx": 1.03}, {"t": 150, "x": -1, "sy": 1.0, "sx": 1.0}, {"t": 300, "x": 0, "sy": 0.97, "sx": 1.03},
                  {"t": 450, "x": 1, "sy": 1.0, "sx": 1.0}, {"t": 600, "x": 0, "sy": 0.97, "sx": 1.03}, {"t": 750, "x": 0, "sy": 1.0, "sx": 1.0}],
         "face": [{"t": 0, "f": ["cry_a", "cry_a", "cry_b", "cry_b"], "ms": 150}],
         "fx": [{"id": "fx2_tear", "anchor": "eyeL", "dx": -3, "dy": 1, "t0": 0, "t1": 900, "ms": 150, "move": [[0, 0, 0], [450, 0, 4]], "loopMove": 450},
                {"id": "fx2_tear", "anchor": "eyeR", "dx": 3, "dy": 1, "t0": 0, "t1": 900, "ms": 150, "move": [[0, 0, 0], [450, 0, 4]], "loopMove": 450, "mirrorX": 1}]},
 "eat": {"frames": 6, "frameMs": 120, "loop": True, "note": "食（一齊食時 loop 2–3 次；食物 icon 由引擎喺 chest 前畫）",
         "body": [{"t": 0, "y": 0, "sy": 1.0}, {"t": 120, "y": 1, "sy": 0.95, "sx": 1.04}, {"t": 240, "y": 0, "sy": 1.0, "sx": 1.0},
                  {"t": 360, "y": 1, "sy": 0.95, "sx": 1.04}, {"t": 480, "y": 0, "sy": 1.02, "sx": 0.99}, {"t": 600, "y": 0, "sy": 1.0, "sx": 1.0}],
         "face": [{"t": 0, "f": "chew_o"}, {"t": 120, "f": "chew_c"}, {"t": 240, "f": "chew_o"}, {"t": 360, "f": "chew_c"}, {"t": 480, "f": "happy"}, {"t": 600, "f": "chew_c"}]},
 "sleep": {"frames": 4, "frameMs": 450, "loop": True, "note": "瞓（呼吸）；Zzz 用 3a fx_zzz（anchor headTop, dx 6）由引擎疊",
           "body": [{"t": 0, "sx": 1.0, "sy": 1.0}, {"t": 450, "sx": 1.02, "sy": 0.97}, {"t": 900, "sx": 1.03, "sy": 0.96}, {"t": 1350, "sx": 1.02, "sy": 0.97}],
           "face": [{"t": 0, "f": "sleep"}], "engineFx": [{"id": "fx_zzz", "anchor": "headTop", "dx": 6, "dy": -1, "ms": 300}]},
}
def tear_fx():
    t = L.auto(["B", "B"], outline=None, fixed={"B": (120, 190, 250)}, pad=0)
    o = canvas(2, 3); paste(o, t, 0, 1); o[0, 0] = (*WHITE, 255)
    return {"frames": [o], "pivot": [1, 0], "note": "細佬喊：眼淚（1 色＋白點，向下流用 move）"}

def render_frame(comp, clip, t):
    """同 reactions_lib.Comp.render，但支援 loopMove（重複 move）"""
    c2 = dict(clip); fxs = []
    for f in clip.get("fx", []):
        f = dict(f)
        if f.get("loopMove") and t >= f["t0"]:
            k = (t - f["t0"]) // f["loopMove"]; f["t0"] = f["t0"] + k * f["loopMove"]
        fxs.append(f)
    c2["fx"] = fxs
    return comp.render(c2, t)

def bake_actions(A):
    os.makedirs(os.path.join(OUT, "actions"), exist_ok=True); idx = {}
    for k in ALL34:
        r = rig_of(k); comp = Comp2(r, A)
        idle_src = os.path.join(FORMS, "idle", f"{k}_idle.png") if k in NEWF else os.path.join(T48, "idle", f"{k}_idle.png")
        shutil.copy(idle_src, os.path.join(OUT, "actions", f"{k}_idle.png"))
        idx[k] = {"stage": STAGE[k], "idle": f"actions/{k}_idle.png"}
        for name, c in ACTIONS.items():
            clip = {"body": c["body"], "face": c["face"], "fx": c.get("fx", [])}
            frames = []
            for i in range(c["frames"]):
                fr = render_frame(comp, clip, i * c["frameMs"])
                prot = [r.outline, EYE_DK, WHITE, (120, 190, 250), L.TONGUE]
                frames.append(limit_colors(fr, 12, protect=prot) if k in NEWF else fr)   # 現有 24 個 from_ref 本身 >12 色：唔壓色，保持同 idle 一樣調色板
            save(np.concatenate(frames, 1), os.path.join(OUT, "actions", f"{k}_{name}.png"))
            idx[k][name] = f"actions/{k}_{name}.png"
    return idx

if __name__ == "__main__":
    T = build_forms()
    A = {"fx": L.build_fx(), "series": {}}
    A["fx"]["fx2_tear"] = tear_fx()
    idx = bake_actions(A)
    json.dump({"note": "細佬 5 動作：34 個階段（S1、S2、S4×8 新＋24 個 from_ref 1/2/3 階）一律有 strip；48×48，pivot (24,45)。clip 定義同 3a reactions schema，已烘焙；引擎直接播 strip。",
               "frameSize": 48, "pivot": [24, 45], "clips": {n: {k: v for k, v in c.items()} for n, c in ACTIONS.items()},
               "idleClip": {"frames": 4, "ms": [260, 180, 260, 140]}, "forms": idx},
              open(os.path.join(OUT, "actions", "actions.json"), "w"), ensure_ascii=False, indent=1)
    print("forms", {k: (v["mass"], v["colors"]) for k, v in T["creatures"].items()})
