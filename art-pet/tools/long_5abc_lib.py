# 《微光小圃》5a–5c 長線養成 — 共用工具（純 Pillow/numpy，冇 AI 生圖）
# 重用 3a reactions_lib（rig／錨點／表情／FX）、4a build_series2_4a（Comp2、細佬 5 動作）、4b build_house_4b_actions（坐／整蠱）
import json, math, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reactions_lib as L
import build_series2_4a as B
import build_house_4b_actions as HA
from series2_lib import ART, save, canvas, paste, limit_colors, ncolors, EYE_DK, WHITE, ROWS, T48

OUTL = os.path.join(ART, "sprites/series2_long")
S2 = os.path.join(ART, "sprites/series2"); SH = os.path.join(ART, "sprites/series2_house")
KID34 = list(B.ALL34)
TR25 = list(L.OLD_FORMS)
TR_ADULT = [f for f in TR25 if f.startswith("evo_still_")]
KID_ADULT = [f"{r}{i}" for r in ROWS for i in (2, 3)]   # GDD §3：S5 成年＝現有第 2 階、S6 完全體＝第 3 階
ADULTS = TR_ADULT + KID_ADULT                    # 屋仔長住、可遠足／工作嘅成年：團絨靜光 9＋細佬 S5/S6 16 = 25
ALL59 = KID34 + TR25
NEWF = set(B.NEWF)
_FXA = None
def FXA():
    global _FXA
    if _FXA is None:
        _FXA = {"fx": L.build_fx(), "series": {}}; _FXA["fx"]["fx2_tear"] = B.tear_fx()
    return _FXA
def rig(k): return B.rig_of(k)
def who(k): return "kid" if k in KID34 else "tr"

# ───────── 5a／5b 新 clip（3a schema；全部用 3a 表情，團絨都用得）─────────
PAD5 = (6, 18)        # 新 strip padding：左右 6、頂 18（跳＋FX）
CLIPS5 = {
 "interact": {"frames": 8, "frameMs": 120, "loop": False, "pad": PAD5,
   "note": "打招呼／貼貼（屋內互動）：0–1 望對方、2–3 傾身貼過去（向右；對方喺左就 flipX）、4 心心、5–6 開心彈、7 返原位",
   "body": [{"t": 0}, {"t": 120, "sy": 1.02}, {"t": 240, "x": 1, "rot": 4, "sx": 1.03, "sy": 0.97}, {"t": 360, "x": 2, "rot": 7, "sx": 1.05, "sy": 0.95},
            {"t": 480, "x": 2, "rot": 6, "y": 0}, {"t": 600, "x": 1, "y": -3, "rot": 0, "sx": 0.96, "sy": 1.06}, {"t": 720, "y": 0, "sx": 1.06, "sy": 0.93}, {"t": 840}],
   "face": [{"t": 0, "f": None}, {"t": 240, "f": "squint"}, {"t": 480, "f": "squint_blush"}, {"t": 600, "f": "laugh_a"}, {"t": 840, "f": "blink"}],
   "fx": [{"id": "fx_heart", "anchor": "headTop", "dx": 6, "dy": -3, "t0": 480, "t1": 960, "move": [[0, 0, 0], [480, 0, -5]]}]},
 "depart": {"frames": 10, "frameMs": 120, "loop": False, "pad": PAD5, "bag": "pack",
   "note": "遠足出發：0 背囊出現（閃）、1 縮、2 跳起心心、3 落地、4–9 跳步行（向右；引擎每格移 2px 去房門／畫面邊，最後 3 格淡出）",
   "body": [{"t": 0}, {"t": 120, "sy": 0.9, "sx": 1.08}, {"t": 240, "y": -5, "sy": 1.1, "sx": 0.93}, {"t": 360, "y": 0, "sy": 0.88, "sx": 1.1},
            {"t": 480, "y": 0, "sx": 1.04, "sy": 0.96}, {"t": 600, "y": -2, "sx": 0.97, "sy": 1.04}, {"t": 720, "y": -1},
            {"t": 840, "y": 0, "sx": 1.04, "sy": 0.96}, {"t": 960, "y": -2, "sx": 0.97, "sy": 1.04}, {"t": 1080, "y": -1}],
   "face": [{"t": 0, "f": "blink"}, {"t": 120, "f": "squint"}, {"t": 240, "f": "laugh_a"}, {"t": 480, "f": None}],
   "fx": [{"id": "fx_sparkle", "anchor": "side_l", "dx": -3, "dy": -2, "t0": 0, "t1": 240, "ms": 120},
          {"id": "fx_heart", "anchor": "headTop", "dx": 5, "dy": -4, "t0": 240, "t1": 600, "move": [[0, 0, 0], [360, 0, -4]]}]},
 "return": {"frames": 10, "frameMs": 120, "loop": False, "pad": PAD5, "bag": "full",
   "note": "遠足返屋：0–3 跳步入嚟（背囊脹晒；引擎由畫面邊每格移 2px 入）、4 停、5 跳起（引擎喺 headTop 上 10px 出手信 icon）、6–7 舉住閃閃、8 縮、9 開心",
   "body": [{"t": 0, "y": 0, "sx": 1.04, "sy": 0.96}, {"t": 120, "y": -2, "sx": 0.97, "sy": 1.04}, {"t": 240, "y": -1}, {"t": 360, "y": 0, "sx": 1.04, "sy": 0.96},
            {"t": 480, "sy": 0.9, "sx": 1.08}, {"t": 600, "y": -6, "sy": 1.12, "sx": 0.92}, {"t": 720, "y": -4, "sy": 1.05}, {"t": 840, "y": -4, "sy": 1.05},
            {"t": 960, "y": 0, "sy": 0.88, "sx": 1.1}, {"t": 1080}],
   "face": [{"t": 0, "f": None}, {"t": 480, "f": "squint"}, {"t": 600, "f": "laugh_a"}, {"t": 840, "f": "laugh_b"}, {"t": 960, "f": "squint_blush"}],
   "fx": [{"id": "fx_sparkle", "anchor": "headTop", "dx": -7, "dy": -6, "t0": 600, "t1": 960, "ms": 120},
          {"id": "fx_sparkle", "anchor": "headTop", "dx": 8, "dy": -9, "t0": 720, "t1": 1080, "ms": 120}],
   "souvenir": {"anchor": "headTop", "dy": -10, "frames": [5, 6, 7, 8, 9], "bobPx": [0, -1, 0, 1, 0], "note": "手信 icon（1x 版 souvenir/<id>_1x.png，pivot 底中）跟 headTop 變形後位置畫"}},
}

# ───────── strip 幾何登記：每個形態有咩 strip、點樣重現 transform ─────────
def _geo(k, name):
    """回傳 dict(frames, frameMs, CW, CH, PX, PY, clip, kind, png) — 同已出 strip 一樣嘅 canvas／pivot"""
    r = rig(k); H, W = r.base.shape[:2]; px, py = r.pivot
    if name == "idle":
        return dict(kind="idle", frames=4, CW=48, CH=48, PX=24, PY=45, png=f"series2/actions/{k}_idle.png")
    if name in B.ACTIONS:
        c = B.ACTIONS[name]
        return dict(kind="kf", frames=c["frames"], frameMs=c["frameMs"], CW=48, CH=48, PX=24, PY=45, clip=c, png=f"series2/actions/{k}_{name}.png")
    if name in HA.CLIPS:
        c = HA.CLIPS[name]; pw, pt = (HA.PAD_X, HA.PAD_TOP) if c["pad"] else (0, 0)
        return dict(kind="kf", frames=c["frames"], frameMs=c["frameMs"], CW=W + 2 * pw, CH=H + pt, PX=px + pw, PY=py + pt, clip=c,
                    png=f"series2_house/actions/{k}_{name}.png")
    if name in CLIPS5:
        c = CLIPS5[name]; pw, pt = c["pad"]
        sub = "5a" if name == "interact" else "5b"
        return dict(kind="kf", frames=c["frames"], frameMs=c["frameMs"], CW=W + 2 * pw, CH=H + pt, PX=px + pw, PY=py + pt, clip=c,
                    png=f"series2_long/{sub}/actions/{k}_{name}.png")
    if name == "base":
        return dict(kind="base", frames=1, CW=W, CH=H, PX=px, PY=py, png=None)
    raise KeyError(name)

def clips_of(k, with5b=True):
    """呢個形態有 strip 嘅 clip（overlay atlas 每行一個）"""
    out = []
    if k in KID34: out += ["idle", "walk", "cry", "eat", "sleep"]
    else: out += ["base"]
    out += ["sit", "prank_do", "prank_got", "interact"]
    if with5b and k in ADULTS: out += ["depart", "return"]
    return out

def idle_cut(k):
    """4 格 idle：第 1 格上半（≤cut 行）落 1px；由實際 strip 推返 cut"""
    a = np.asarray(Image.open(os.path.join(ART, "sprites", _geo(k, "idle")["png"])).convert("RGBA"))
    f0, f1 = a[:, :48], a[:, 48:96]; best, bc = -1, 47
    for cut in range(10, 46):
        sh = f0.copy(); sh[1:cut + 1] = f0[0:cut]; sh[0] = 0
        ok = (sh[..., 3] == f1[..., 3]).sum()
        if ok > best: best, bc = ok, cut
    return bc

def xform(r, src, off, clip, t, CW, CH, PX, PY):
    """同 reactions_lib.Comp.body_layer 一樣嘅最近鄰變形，但 src 可以有 padding（off＝src 入面 base(0,0) 嘅位置）"""
    B_ = L.body_at(clip, t); O = r.anchors["pivot"]; pv = r.pivot
    ox = PX + (O[0] - pv[0]) + B_["x"]; oy = PY + (O[1] - pv[1]) + B_["y"]
    Y, X = np.mgrid[0:CH, 0:CW].astype(float)
    vx, vy = X - ox, Y - oy
    a = -math.radians(B_["rot"]); ux = vx * math.cos(a) - vy * math.sin(a); uy = vx * math.sin(a) + vy * math.cos(a)
    ux /= B_["sx"]; uy /= B_["sy"]
    if B_["flip"]: ux = -ux
    sxp = np.floor(O[0] + ux + .5).astype(int) + off[0]; syp = np.floor(O[1] + uy + .5).astype(int) + off[1]
    H, W = src.shape[:2]; ok = (sxp >= 0) & (sxp < W) & (syp >= 0) & (syp < H)
    lay = np.zeros((CH, CW, 4), np.uint8); lay[ok] = src[syp[ok], sxp[ok]]
    return lay

def overlay_atlas(k, patch, off, clips, pad=(0, 0)):
    """patch：base 座標嘅疊層（可有 padding，off＝base 原點喺 patch 入面位置）。
    每個 clip 一行，frame＝原 strip frame 再加 pad（左右 pad[0]、頂 pad[1]）；pivot＝原 pivot＋pad。回傳 atlas、rows meta"""
    r = rig(k); rows = []; imgs = []
    for name in clips:
        g = _geo(k, name); CW, CH = g["CW"] + 2 * pad[0], g["CH"] + pad[1]; PX, PY = g["PX"] + pad[0], g["PY"] + pad[1]
        frames = []
        if g["kind"] == "kf":
            for i in range(g["frames"]): frames.append(xform(r, patch, off, {"body": g["clip"]["body"]}, i * g["frameMs"], CW, CH, PX, PY))
        else:
            st = {"body": [{"t": 0}]}; f0 = xform(r, patch, off, st, 0, CW, CH, PX, PY)
            if g["kind"] == "idle":
                cut = idle_cut(k) + pad[1]
                f1 = f0.copy(); f1[1:cut + 1] = f0[0:cut]; f1[0] = 0
                frames = [f0, f1, f0.copy(), f0.copy()]
            else: frames = [f0]
        strip = np.concatenate(frames, 1); imgs.append(strip)
        rows.append({"clip": name, "frames": len(frames), "frameW": CW, "frameH": CH, "pivot": [PX, PY], "petPng": g["png"]})
    Wt = max(s.shape[1] for s in imgs); Ht = sum(s.shape[0] for s in imgs)
    atlas = np.zeros((Ht, Wt, 4), np.uint8); y = 0
    for s, rw in zip(imgs, rows):
        atlas[y:y + s.shape[0], :s.shape[1]] = s; rw["y"] = y; y += s.shape[0]
    return atlas, rows

def bake_clip(k, name, base_override=None, extra_protect=()):
    """烘焙 5a／5b 新 clip strip（同 4b 一樣用 Comp2）"""
    r = rig(k); g = _geo(k, name); c = CLIPS5[name]
    comp = B.Comp2(r, FXA(), CW=g["CW"], CH=g["CH"], PX=g["PX"], PY=g["PY"])
    if base_override is not None: comp.base_override = base_override
    clip = {"body": c["body"], "face": c["face"], "fx": c.get("fx", [])}
    frames = []
    for i in range(c["frames"]):
        fr = B.render_frame(comp, clip, i * c["frameMs"])
        if k in NEWF: fr = limit_colors(fr, 12, protect=[r.outline, EYE_DK, WHITE, L.TONGUE, *extra_protect])
        frames.append(fr)
    return np.concatenate(frames, 1), g

x3 = lambda a, s=3: Image.fromarray(a).resize((a.shape[1] * s, a.shape[0] * s), Image.NEAREST)
def strip_frames(a, fw): return [a[:, i * fw:(i + 1) * fw] for i in range(a.shape[1] // fw)]
def over(dst, src, x=0, y=0): paste(dst, src, x, y); return dst
def jdump(o, p):
    os.makedirs(os.path.dirname(p), exist_ok=True); json.dump(o, open(p, "w"), ensure_ascii=False, indent=1)
def font(sz, serif=False):
    from PIL import ImageFont
    return ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc" if serif else "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", sz, index=2 if not serif else 0)
def label(im, s, y=6, h=40, sz=28):
    from PIL import ImageDraw
    d = ImageDraw.Draw(im); d.rectangle((0, y - 4, im.width, y + h), fill=(40, 28, 36)); d.text((14, y), s, font=font(sz), fill=(255, 240, 220)); return im
def save_gif(frames, p, ms):
    ims = [f.convert("RGB").convert("P", palette=Image.ADAPTIVE, colors=255) for f in frames]
    ims[0].save(p, save_all=True, append_images=ims[1:], duration=ms, loop=0, disposal=2)
