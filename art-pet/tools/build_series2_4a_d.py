# series2 4a 第 D 部：雙人 clip 6（攬蛋瞓、孵化第一眼、跟住行、哄喊、一齊食、一齊瞓）＋升級小場面 3 — 數據＋疊層＋GIF
# 座標：相對場景 pivot (97,292)（195×422 美術格）；團絨用 evo_still_* 現有 clip（名），細佬用 series2/actions strip。
import os, json, math
import numpy as np
from PIL import Image
import reactions_lib as L
from series2_lib import S2, ART, save, canvas, paste, rgba, WHITE
import build_series2_4a_b as BB

TRD = os.path.join(ART, "sprites/tuanrong/evo6/evo_still_{r}/frames")
SCN = os.path.join(ART, "sprites/tuanrong/species_concept/from_ref/feeltest/assets/scenes/H1")
PIV = (97, 292); SCN_OFF = (14, 12)
OUT = os.path.join(S2, "duo"); LV = os.path.join(S2, "levelup")
OLP = (52, 36, 70)
FX = L.build_fx()

# ───────── 疊層（像素） ─────────
def ov_blanket():
    a = L.auto(["...PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP...", "..PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP..", ".PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP.", "PPPPPPWPPPPPPPPWPPPPPPPPWPPPPPPPPWPPPP",
                "PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP", "PPPPPPPPPPWPPPPPPPPWPPPPPPPPWPPPPPPPPP",
                "PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP", "PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP", ".PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP."],
               outline=OLP, ramps=L.RAMP, fixed={"W": (255, 236, 160)})
    return {"frames": [a], "pivot": [a.shape[1] // 2, a.shape[0] - 1], "note": "一齊瞓：被（蓋住兩隻下半身；pivot＝底中）"}
def ov_rays(n=4):
    fr = []
    for k in range(n):
        W = 97; o = canvas(W, W); c = W // 2; Y, X = np.mgrid[0:W, 0:W]; ang = np.arctan2(Y - c, X - c); d = np.hypot(X - c, Y - c)
        m = ((np.sin(ang * 8 + k * math.pi / 8) > 0.55) & (d < 44 - (k % 2) * 3) & (d > 10))
        o[m] = (255, 244, 196, 255); o[(d < 9)] = (255, 255, 236, 255); fr.append(o)
    return {"frames": fr, "pivot": [48, 48], "note": "孵化光芒（4 幀轉；引擎可再加 additive glow）"}
def ov_shell_bits():
    g = L.auto([".SS", "SSS", "SS."], outline=OLP, fixed={"S": (250, 240, 214)}, pad=0)
    g2 = L.auto(["SS.", ".SS"], outline=OLP, fixed={"S": (240, 226, 196)}, pad=0)
    return {"frames": [g, g2], "pivot": [1, 1], "note": "蛋殼碎（兩款；引擎用拋物線飛）"}
def ov_confetti():
    cols = [(255, 146, 182), (146, 210, 250), (255, 223, 122), (189, 240, 214), (205, 180, 251)]
    rng = np.random.default_rng(7); fr = []
    pts = [(int(rng.integers(0, 60)), int(rng.integers(0, 10)), cols[i % 5], int(rng.integers(1, 3))) for i in range(22)]
    for k in range(6):
        o = canvas(60, 40)
        for (x, y, c, v) in pts:
            yy = y + k * 5 * v // 2 + k; xx = (x + int(2 * math.sin(k + x))) % 60
            if 0 <= yy < 39: o[yy, xx] = (*c, 255); o[yy + (x % 2), xx + (1 - x % 2) if xx < 59 else xx] = (*c, 255)
        fr.append(o)
    return {"frames": fr, "pivot": [30, 0], "note": "彩紙（6 幀落下，掛喺兩隻頭頂上 30px）"}
def badge(kind):
    g = {"follow": ["..YYYYYY..", ".YYYYYYYY.", "YYPPYYPPYY", "YYPPYYPPYY", "YYYYYYYYYY", "YYYPPPPYYY", "YYYPPPPYYY", ".YYYYYYYY.", "..YYYYYY..", "...R..R...", "..RR..RR.."],
         "friend": ["..YYYYYY..", ".YYYYYYYY.", "YYPPYYPPYY", "YPPPPPPPPY", "YPPPPPPPPY", "YYPPPPPPYY", "YYYPPPPYYY", ".YYYPPYYY.", "..YYYYYY..", "...R..R...", "..RR..RR.."],
         "family": ["....PP....", "...PPPP...", "..PPPPPP..", ".PPPPPPPP.", "PPPPPPPPPP", ".YYYYYYYY.", ".YYYRRYYY.", ".YYYRRYYY.", ".YYYRRYYY.", "...R..R...", "..RR..RR.."]}[kind]
    a = L.auto(g, outline=OLP, ramps=L.RAMP, fixed={"Y": (255, 223, 122), "P": (255, 146, 182), "R": (146, 210, 250)})
    return a
def ov_ribbon():
    a = L.auto([".PPP" + "W" * 52 + "PPP.", "PPPP" + "W" * 52 + "PPPP", ".PPP" + "W" * 52 + "PPP.", "..PP" + "W" * 52 + "PP..", "...P" + "W" * 52 + "P..."][0:3] +
               ["PPPP" + "W" * 52 + "PPPP", ".PPP" + "W" * 52 + "PPP."],
               outline=OLP, fixed={"P": (255, 146, 182), "W": (255, 250, 240)})
    return {"frames": [a], "pivot": [a.shape[1] // 2, a.shape[0] // 2], "note": "空白絲帶（字由引擎寫：跟班／朋友／家人）"}
def ov_heart_big():
    h = L.auto([".PP.PP.", "PPPPPPP", "PPPPPPP", ".PPPPP.", "..PPP..", "...P..."], outline=OLP, ramps=L.RAMP, fixed={"P": (255, 146, 182)})
    o = canvas(h.shape[1] + 4, h.shape[0] + 4); paste(o, h, 2, 2)
    big = np.array(Image.fromarray(h).resize((h.shape[1] * 2, h.shape[0] * 2), Image.NEAREST))
    return {"frames": pad([o, big]), "pivot": [big.shape[1] // 2, big.shape[0] - 1], "note": "大心心（0 細、1 大 2x）"}
def pad(frames):
    W = max(f.shape[1] for f in frames); H = max(f.shape[0] for f in frames); out = []
    for f in frames: o = canvas(W, H); paste(o, f, (W - f.shape[1]) // 2, H - f.shape[0]); out.append(o)
    return out

# ───────── 資源載入 ─────────
_TRC = {}
def tr_frames(clip, route="lumi"):
    key = (clip, route)
    if key not in _TRC:
        J = json.load(open(os.path.join(L.ATT, f"evo_still_{route}.json")))["clips"][clip]
        d = TRD.format(r=route); _TRC[key] = ([rgba(os.path.join(d, f"{clip}_{i:02d}.png")) for i in range(1, J["n"] + 1)], 1000 / J["fps"], J["loop"])
    return _TRC[key]
def kid_frames(k, act):
    a = rgba(os.path.join(S2, "actions", f"{k}_{act}.png")); n = a.shape[1] // 48
    ms = {"idle": None, "walk": 100, "cry": 150, "eat": 120, "sleep": 450}[act]
    fr = [a[:, i * 48:(i + 1) * 48] for i in range(n)]
    return fr, ms
IDLE_MS = [260, 180, 260, 140]
def pick(frames, ms, lt, loop=True):
    if ms is None:  # idle 4 幀不等長
        T = sum(IDLE_MS); lt = lt % T; acc = 0
        for i, m in enumerate(IDLE_MS):
            acc += m
            if lt < acc: return frames[i]
    i = int(lt // ms); return frames[i % len(frames)] if loop else frames[min(i, len(frames) - 1)]
def egg_frames():
    a = rgba(os.path.join(S2, "egg", "egg_crack.png")); return [a[:, i * 48:(i + 1) * 48] for i in range(a.shape[1] // 48)]

def actor_img(act, t):
    """act: {"who": "tr"|"kid"|"egg", "track": [{"t", "clip", "x", "y", "flip"}], ...} → (img, x, y)"""
    cur = None
    for k in act["track"]:
        if t >= k["t"]: cur = k
    nxt = next((k for k in act["track"] if k["t"] > t), None)
    x, y = cur.get("x", 0), cur.get("y", 0)
    if nxt is not None and cur.get("ease", True) and ("x" in nxt or "y" in nxt):
        u = (t - cur["t"]) / max(1, nxt["t"] - cur["t"]); x += (nxt.get("x", x) - x) * u; y += (nxt.get("y", y) - y) * u
    lt = t - cur["t"]
    if act["who"] == "tr": fr, ms, lp = tr_frames(cur["clip"]); img = pick(fr, ms, lt, cur.get("loop", lp))
    elif act["who"] == "kid": fr, ms = kid_frames(act["form"], cur["clip"]); img = pick(fr, ms, lt)
    else: img = egg_frames()[cur.get("crack", 0)]
    if cur.get("flip"): img = img[:, ::-1]
    return img, x, y

def scene_bg(W=128, H=100):
    bg = Image.new("RGBA", (223, 446))
    for n in ("sky", "far", "mid"): bg.alpha_composite(Image.open(os.path.join(SCN, n + ".png")).convert("RGBA"))
    cx, cy = PIV[0] + SCN_OFF[0], PIV[1] + SCN_OFF[1]
    return np.array(bg.crop((cx - W // 2, cy - H + 14, cx + W // 2, cy + 14))), (W // 2, H - 14)

def render_duo(D, t, OV, bg=None):
    if bg is None: bg, o = scene_bg()
    else: bg, o = bg
    out = bg.copy()
    layers = []
    for name, act in D["actors"].items(): layers.append((act.get("z", 0), "a", name, act))
    for ov in D.get("overlays", []):
        if ov["t0"] <= t < ov["t1"]: layers.append((ov.get("z", 5), "o", ov["id"], ov))
    for z, typ, name, a in sorted(layers, key=lambda l: l[0]):
        if typ == "a":
            img, x, y = actor_img(a, t); paste(out, img, int(o[0] + a["dx"] + x - 24), int(o[1] + a.get("dy", 0) + y - 45))
        else:
            F = OV[a["id"]]; fr = F["frames"]; i = int((t - a["t0"]) // a.get("ms", 150))
            img = fr[i % len(fr)] if a.get("loop", True) else fr[min(i, len(fr) - 1)]
            if "frames" in a: img = fr[a["frames"][i % len(a["frames"])] if a.get("loop", True) else a["frames"][min(i, len(a["frames"]) - 1)]]
            mv = a.get("move"); mx = my = 0
            if mv:
                lt = t - a["t0"]; mx, my = mv[-1][1], mv[-1][2]
                for p, q in zip(mv, mv[1:]):
                    if p[0] <= lt <= q[0]: u = (lt - p[0]) / max(1, q[0] - p[0]); mx = p[1] + (q[1] - p[1]) * u; my = p[2] + (q[2] - p[2]) * u; break
            paste(out, img, int(o[0] + a["x"] + mx - F["pivot"][0]), int(o[1] + a["y"] + my - F["pivot"][1]))
    return out

def ovl(i, x, y, t0, t1, ms=150, z=5, **kw):
    d = {"id": i, "x": x, "y": y, "t0": t0, "t1": t1, "ms": ms, "z": z}; d.update(kw); return d

KID = "S2"
DUO = {
 "cuddle_egg": {"title": "攬蛋瞓（蛋期每晚 21:00 後，團絨瞓覺時自動）", "durationMs": 2000, "loop": True,
   "actors": {"tr": {"who": "tr", "dx": -8, "z": 0, "track": [{"t": 0, "clip": "sleep_loop"}]},
              "egg": {"who": "egg", "dx": 10, "dy": 1, "z": 1, "track": [{"t": 0, "crack": 0}, {"t": 1000, "crack": 0, "y": -1}, {"t": 1150, "crack": 0, "y": 0}]}},
   "overlays": [ovl("fx_zzz", -2, -30, 0, 2000, ms=300), ovl("dream_slot", 18, -40, 0, 2000, z=9, note="夢泡泡 UI（ui/dream_bubbles，當日最多照顧類型）由引擎喺呢度疊，1x 約 44×44")]},
 "follow_walk": {"title": "跟住行（跟班起；細佬跟喺團絨後面 30px，慢 300ms 起步）", "durationMs": 3000, "loop": True, "followGapPx": 30, "followDelayMs": 300,
   "actors": {"tr": {"who": "tr", "dx": -10, "z": 1, "track": [{"t": 0, "clip": "walk", "x": -30}, {"t": 3000, "clip": "walk", "x": 30}]},
              "kid": {"who": "kid", "form": KID, "dx": -40, "z": 0, "track": [{"t": 0, "clip": "idle", "x": -30}, {"t": 300, "clip": "walk", "x": -30}, {"t": 3000, "clip": "walk", "x": 26}]}},
   "overlays": [ovl("fx_heart", -26, -34, 1600, 2200, ms=150)]},
 "comfort_cry": {"title": "哄喊：細佬喊 → 團絨埋去挨挨 → 收聲", "durationMs": 3600, "loop": False,
   "actors": {"kid": {"who": "kid", "form": KID, "dx": 14, "z": 0, "track": [{"t": 0, "clip": "cry"}, {"t": 2200, "clip": "idle"}]},
              "tr": {"who": "tr", "dx": -10, "z": 1, "track": [{"t": 0, "clip": "walk", "x": -14}, {"t": 700, "clip": "nuzzle", "x": 0}, {"t": 2200, "clip": "emo_happy", "x": 0}, {"t": 2700, "clip": "idle", "x": 0}]}},
   "overlays": [ovl("fx_heart", 3, -34, 1200, 2200, ms=150), ovl("fx_sparkle", 18, -30, 2200, 2800, ms=120), ovl("fx_heart", 14, -36, 2700, 3600, ms=150)]},
 "eat_together": {"title": "一齊食：餵團絨時細佬一齊食（+1 親密）", "durationMs": 1500, "loop": True,
   "actors": {"tr": {"who": "tr", "dx": -12, "z": 0, "track": [{"t": 0, "clip": "eat", "loop": True}]},
              "kid": {"who": "kid", "form": KID, "dx": 14, "z": 1, "track": [{"t": 0, "clip": "eat"}]}},
   "overlays": [ovl("food_slot", 14, -6, 0, 1500, z=9, note="細佬份食物 icon 由引擎喺細佬 chest 前畫（同團絨嗰份一樣）")]},
 "sleep_together": {"title": "一齊瞓：21:00–03:00 兩隻都瞓（+2 親密，每晚 1 次）", "durationMs": 1800, "loop": True,
   "actors": {"tr": {"who": "tr", "dx": -9, "z": 0, "track": [{"t": 0, "clip": "sleep_loop"}]},
              "kid": {"who": "kid", "form": KID, "dx": 11, "dy": 1, "z": 1, "track": [{"t": 0, "clip": "sleep"}]}},
   "overlays": [ovl("ov_blanket", 1, 1, 0, 1800, z=6), ovl("fx_zzz", -3, -30, 0, 1800, ms=300), ovl("fx_zzz", 18, -24, 450, 1800, ms=300)]},
}
LEVEL = {
 "lv_follow": {"title": "升級：跟班", "durationMs": 4000, "loop": False, "ribbonText": "跟班",
   "actors": {"tr": {"who": "tr", "dx": 0, "z": 1, "track": [{"t": 0, "clip": "idle", "x": -6}, {"t": 600, "clip": "walk", "x": -6}, {"t": 2200, "clip": "smug_pose", "x": 18}, {"t": 3000, "clip": "idle", "x": 18}]},
              "kid": {"who": "kid", "form": "S1", "dx": -26, "z": 0, "track": [{"t": 0, "clip": "idle", "x": 0}, {"t": 900, "clip": "walk", "x": 0}, {"t": 2400, "clip": "idle", "x": 22}]}},
   "overlays": [ovl("badge_follow", -4, -44, 2400, 4000, ms=120, z=8, move=[[0, 0, 8], [200, 0, -2], [320, 0, 0]]), ovl("ov_ribbon", 0, -60, 2600, 4000, z=9),
                ovl("ov_confetti", 0, -70, 2400, 3600, ms=100, loop=False)]},
 "lv_friend": {"title": "升級：朋友（親密 30）", "durationMs": 5000, "loop": False, "ribbonText": "朋友",
   "actors": {"tr": {"who": "tr", "dx": -16, "z": 0, "track": [{"t": 0, "clip": "idle"}, {"t": 900, "clip": "emo_surprised"}, {"t": 1300, "clip": "cheer_jump", "loop": False}, {"t": 2000, "clip": "nuzzle_purr"}, {"t": 3800, "clip": "emo_happy", "loop": False}]},
              "kid": {"who": "kid", "form": "S2", "dx": 16, "z": 1, "flip": 1, "track": [{"t": 0, "clip": "walk", "x": 10, "flip": 1}, {"t": 900, "clip": "idle", "x": 0, "flip": 1}, {"t": 2000, "clip": "eat", "x": -2, "flip": 1}, {"t": 2800, "clip": "idle", "x": -2, "flip": 1}]}},
   "overlays": [ovl("ov_heart_big", 0, -28, 1800, 2600, ms=200, loop=False, z=7, frames=[0, 1, 1]), ovl("badge_friend", 0, -46, 2700, 5000, z=8, move=[[0, 0, 8], [200, 0, -2], [320, 0, 0]]),
                ovl("ov_ribbon", 0, -62, 2900, 5000, z=9), ovl("ov_confetti", 0, -72, 2700, 3900, ms=100, loop=False)]},
 "lv_family": {"title": "升級：家人（屋仔解鎖）", "durationMs": 6000, "loop": False, "ribbonText": "家人",
   "actors": {"tr": {"who": "tr", "dx": -12, "z": 0, "track": [{"t": 0, "clip": "idle"}, {"t": 800, "clip": "nuzzle"}, {"t": 2600, "clip": "celebrate", "loop": False}, {"t": 3200, "clip": "idle"}]},
              "kid": {"who": "kid", "form": "S4A", "dx": 13, "z": 1, "track": [{"t": 0, "clip": "idle"}, {"t": 2600, "clip": "walk"}, {"t": 3400, "clip": "idle"}]}},
   "overlays": [ovl("fx_heart", -2, -34, 900, 2600, ms=150), ovl("badge_family", 0, -48, 3000, 6000, z=8, move=[[0, 0, 8], [200, 0, -2], [320, 0, 0]]),
                ovl("ov_ribbon", 0, -64, 3200, 6000, z=9), ovl("ov_confetti", 0, -74, 3000, 4200, ms=100, loop=False), ovl("ov_confetti", 6, -74, 4200, 5400, ms=100, loop=False)]},
}

# ───────── 孵化第一眼（全畫面 195×422，2 秒，可跳） ─────────
def hatch(OV):
    W, H = 195, 422; frames = []; ms = 100
    bgc = np.zeros((H, W, 4), np.uint8); Y = np.mgrid[0:H, 0:W][0] / H
    for i, (a, b) in enumerate(zip((60, 52, 92), (120, 104, 156))): bgc[..., i] = (a + (b - a) * Y).astype(np.uint8)
    bgc[..., 3] = 255
    eggs = egg_frames(); s1f = kid_frames("S1", "idle")[0]
    trh = tr_frames("emo_happy")[0]; trs = tr_frames("emo_surprised")[0]
    def up2(a): return np.array(Image.fromarray(a).resize((a.shape[1] * 2, a.shape[0] * 2), Image.NEAREST))
    cx, gy = 97, 292
    tl = {"0-600": "蛋震＋裂 1→3", "600-800": "閃光（rays）", "800-1300": "殼飛開，S1 出場（眨眼）", "1300-2000": "團絨由左邊探頭（驚→開心），中間心心"}
    for t in range(0, 2000, ms):
        o = bgc.copy()
        if 500 <= t < 1400:
            r = OV["ov_rays"]["frames"][(t // 100) % 4].copy()
            if t >= 1100: r[(np.indices(r.shape[:2]).sum(0) % 2 == 1)] = 0   # 收光（棋盤淡出）
            paste(o, r, cx - r.shape[1] // 2, gy - 48 - r.shape[0] // 2)
        if t < 700:
            e = eggs[min(3, t // 200)]; sh = [0, -2, 2, -1, 1][(t // 50) % 5] if t > 150 else 0
            paste(o, up2(e), cx - 48 + sh, gy - 90)
        else:
            body = s1f[3] if (t // 100) % 6 == 5 else s1f[(t // 200) % 2]
            paste(o, up2(body), cx - 48, gy - 90)
            lt = t - 700
            for j, (vx, vy, f) in enumerate(((-34, -40, 0), (30, -46, 1), (-20, -60, 1), (40, -30, 0))):
                if lt < 700:
                    x = cx + vx * lt / 500; y = gy - 50 + vy * lt / 500 + 0.00025 * lt * lt * 60
                    paste(o, up2(OV["ov_shell_bits"]["frames"][f]), int(x), int(y))
        if t >= 1300:
            lt = t - 1300; x = -70 + min(1.0, lt / 300) * 44
            img = trs[0] if lt < 300 else trh[(lt // 250) % 2]
            paste(o, up2(img), int(cx - 48 + x - 26), gy - 90)
            if lt > 300: hh = up2(FX["fx_heart"]["frames"][(lt // 150) % len(FX["fx_heart"]["frames"])]); paste(o, hh, cx - 30 - hh.shape[1] // 2, gy - 100 - (lt // 100) % 3)
        frames.append(o)
    spec = {"title": "孵化第一眼（全畫面 2 秒，可跳）", "grid": [195, 422], "durationMs": 2000, "scale": 2, "anchor": [97, 292], "timeline": tl,
            "layers": {"bg": "垂直漸層 #3C3460→#78689C（引擎畫）", "egg": "egg/egg_crack.png 2x（0–600ms 每 200ms 一格，>150ms 左右震 ±2）",
                       "rays": "duo/overlays/ov_rays.png（500–1400ms，1100ms 起淡出）", "shell": "duo/overlays/ov_shell_bits.png 2x，4 塊拋物線",
                       "kid": "actions/S1_idle.png 2x", "tr": "團絨 emo_surprised → emo_happy 2x，由左邊滑入（終點 pivot x≈47）", "heart": "3a fx_heart"},
            "skip": "撳任何位跳去最後一格"}
    return frames, spec

def main():
    OV = {"ov_blanket": ov_blanket(), "ov_rays": ov_rays(), "ov_shell_bits": ov_shell_bits(), "ov_confetti": ov_confetti(),
          "ov_ribbon": ov_ribbon(), "ov_heart_big": ov_heart_big()}
    for kd in ("follow", "friend", "family"):
        b = badge(kd); OV["badge_" + kd] = {"frames": [b], "pivot": [b.shape[1] // 2, b.shape[0] - 1], "note": f"升級徽章：{kd}"}
    for k in ("fx_zzz", "fx_heart", "fx_sparkle"): OV[k] = {"frames": FX[k]["frames"], "pivot": FX[k]["pivot"], "note": "3a 現有 FX"}
    blank = canvas(1, 1); OV["dream_slot"] = {"frames": [blank], "pivot": [0, 0], "note": "引擎位：夢泡泡"}; OV["food_slot"] = {"frames": [blank], "pivot": [0, 0], "note": "引擎位：食物"}
    od = os.path.join(OUT, "overlays"); os.makedirs(od, exist_ok=True); oidx = {}
    for k, v in OV.items():
        if k.startswith(("fx_",)) or k.endswith("_slot"): oidx[k] = {"note": v["note"]}; continue
        save(np.concatenate(pad(v["frames"]), 1), os.path.join(od, f"{k}.png"))
        oidx[k] = {"png": f"duo/overlays/{k}.png", "frames": len(v["frames"]), "frameW": pad(v["frames"])[0].shape[1], "frameH": pad(v["frames"])[0].shape[0], "pivot": v["pivot"], "note": v["note"]}
    bg = scene_bg()
    for group, defs, folder in (("duo", DUO, OUT), ("levelup", LEVEL, LV)):
        for name, D in defs.items():
            fr = [render_duo(D, t, OV, bg) for t in range(0, D["durationMs"], 100)]
            BB.write_gif(fr, os.path.join(S2, "preview", f"{group}_{name}.gif"), scale=3, ms=100)
            D["scenePivot"] = list(PIV); D["coord"] = "actor dx/dy＋track x/y＝寵物 pivot 相對場景 pivot；overlay x/y＝疊層 pivot 相對場景 pivot"
            D["actorsSpec"] = {"tr": "團絨：evo_still_<路線>/frames/<clip>_NN.png（fps 跟 attach json）", "kid": "細佬：series2/actions/<form>_<clip>.png（引擎用當時階段）", "egg": "series2/egg/egg_crack.png"}
    hf, hs = hatch(OV)
    BB.write_gif(hf, os.path.join(S2, "preview", "duo_hatch_first_glance.gif"), scale=1, ms=100)
    save(hf[-1], os.path.join(OUT, "hatch_first_glance_last.png"))
    DUO_OUT = dict(DUO); DUO_OUT["hatch_first_glance"] = hs
    os.makedirs(LV, exist_ok=True)
    json.dump({"note": "雙人 clip 6（hatch_first_glance 係全畫面）", "overlays": oidx, "clips": DUO_OUT}, open(os.path.join(OUT, "duo.json"), "w"), ensure_ascii=False, indent=1)
    json.dump({"note": "升級小場面 3（4–6 秒）；絲帶字由引擎寫 ribbonText；疊層喺 duo/overlays", "scenes": LEVEL}, open(os.path.join(LV, "levelup.json"), "w"), ensure_ascii=False, indent=1)
    print("duo ok", list(DUO_OUT), "level ok", list(LEVEL))

if __name__ == "__main__":
    main()
