"""batch3b：③ 朋友訪客（蝸牛郵差＋蘑菇婆婆＋螢火小販）＋ ④ 進化大場面＋9 名卡＋20 格 4 格漫畫。
純 Pillow/numpy 程序生成（冇 AI）。重跑：cd art-pet && python3 tools/build_batch3b.py
輸出：sprites/batch3b/（會清空重建，但唔掂其他資料夾）"""
import os, sys, json, math, shutil
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reactions_lib as L
import batch3b_paint as B
import batch3b_visitors as V
import batch3b_fx as F
from batch3b_paint import P, render, canvas, px, pxs, paste, add_outline, OL, WHITE, BLUSH

ART = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ART, "sprites/batch3b")
EVO = os.path.join(ART, "sprites/tuanrong/evo6")
HD = os.path.join(ART, "scenes/hd2d")
R3A = os.path.join(ART, "sprites/tuanrong/reactions")

def sv(a, rel):
    p = os.path.join(OUT, rel); os.makedirs(os.path.dirname(p), exist_ok=True); B.save(a, p); return rel

def sv_strip(frames, rel, n=12):
    frames = B.limit(frames, n); sv(B.strip(frames), rel); return frames

def low_row(a): return int(np.nonzero((a[..., 3] == 255).any(1))[0].max())

# ───────── 寵物幀（舊 evo atlas） ─────────
_AT = {}
def atlas(form):
    if form not in _AT:
        d = json.load(open(os.path.join(EVO, f"atlas_{form}.json"))); im = np.array(Image.open(os.path.join(EVO, d["meta"]["image"])).convert("RGBA"))
        _AT[form] = (d, im)
    return _AT[form]
def pet_frame(form, name="idle_01"):
    d, im = atlas(form); f = d["frames"].get(name) or d["frames"]["idle_01"]; r = f["frame"]
    a = im[r["y"]:r["y"] + r["h"], r["x"]:r["x"] + r["w"]].copy(); a[..., 3] = np.where(a[..., 3] > 127, 255, 0); a[a[..., 3] == 0] = 0
    pv = f.get("pivotPx", {"x": r["w"] // 2, "y": r["h"] - 3}); return a, (pv["x"], pv["y"])
def form_name(form): return atlas(form)[0]["meta"].get("name", form)
def sil(a, c=(255, 246, 218)):
    o = a.copy(); m = o[..., 3] == 255; o[m, :3] = c; return o

def put_pet(dst, form, name, foot, flip=False, silc=None):
    a, pv = pet_frame(form, name)
    if flip: a = B.flipx(a); pv = (a.shape[1] - 1 - pv[0], pv[1])
    if silc: a = sil(a, silc)
    paste(dst, a, foot[0] - pv[0], foot[1] - pv[1])

# ───────── 3a 資產 ─────────
FX3A = json.load(open(os.path.join(R3A, "fx/fx.json")))
def fx3a(fid, i=0):
    m = FX3A[fid]; im = np.array(Image.open(os.path.join(R3A, m["file"])).convert("RGBA")); w = m["frameW"]
    return im[:, i * w:(i + 1) * w], m["pivot"]
def put_fx(dst, fid, i, x, y):
    a, pv = fx3a(fid, i); paste(dst, a, x - pv[0], y - pv[1])

# ───────── 場景 ─────────
_SC = {}
def scene_layer(h, with_fore=False):
    key = (h, with_fore)
    if key not in _SC:
        c = Image.new("RGBA", (223, 446))
        for l in ["sky", "far", "mid"] + (["fore"] if with_fore else []): c.alpha_composite(Image.open(os.path.join(HD, h, f"{l}.png")).convert("RGBA"))
        a = np.array(c).astype(float); lm = np.array(Image.open(os.path.join(HD, h, "lightmap.png")).convert("RGB")).astype(float) / 255
        a[..., :3] *= lm; _SC[key] = np.clip(a, 0, 255).astype(np.uint8)
    return _SC[key]
def scene_art(h):  # 195×422 螢幕
    return scene_layer(h)[12:12 + 422, 14:14 + 195].copy()
def fore_art(h):
    return np.array(Image.open(os.path.join(HD, h, "fore.png")).convert("RGBA"))[12:12 + 422, 14:14 + 195]

def over(dst, src):
    a = src[..., 3:4].astype(float) / 255; dst[..., :3] = (dst[..., :3] * (1 - a) + src[..., :3] * a).astype(np.uint8)

# ═════════════════════════ ③ 訪客 ═════════════════════════
VIS = {
    "snail_postman": dict(name="蝸牛郵差", fn=V.snail_clips, W=V.SN_W, H=V.SN_H, piv=V.SN_PIV, speed=10, order=1,
                          gift="letter", head=[33, 8], bag=[28, 21], hit=[-18, -24, 18, 1], note="帶信＝一句日記；先做呢隻"),
    "mushroom_granny": dict(name="蘑菇婆婆", fn=V.granny_clips, W=V.MG_W, H=V.MG_H, piv=V.MG_PIV, speed=12, order=2,
                            gift="seed", head=[19, 4], bag=[19, 31], hit=[-17, -40, 17, 1], note="送 1 粒種子＋種花貼士"),
    "firefly_vendor": dict(name="螢火小販", fn=V.firefly_clips, W=V.FF_W, H=V.FF_H, piv=V.FF_PIV, speed=20, order=3,
                           gift=None, head=[25, 6], bag=[8, 22], hit=[-19, -34, 17, 1], note="只 17:00–07:00；賣擺設 10–20 碎；身體懸空，地影由引擎畫"),
}
CLIP_MS = {"idle": 180, "walk": 120, "happy": 100}

def badge(kind):
    W = 18; a = canvas(W, W); Y, X = np.mgrid[0:W, 0:W]; d = np.hypot(X - 8.5, Y - 8.5)
    rim = {"snail_postman": ((255, 196, 172), (240, 132, 122)), "mushroom_granny": ((255, 214, 226), (226, 86, 98)), "firefly_vendor": ((236, 252, 200), (104, 196, 172))}[kind]
    a[d <= 8.6] = (*F.UI_OL, 255); a[d <= 7.6] = (*WHITE, 255); a[d <= 6.2] = (*rim[1], 255); a[d <= 5.2] = (*rim[0], 255)
    g = {"snail_postman": (["..###.", ".#...#", "#..#.#", "#.#..#", ".#..#.", "######"], (194, 86, 100)),
         "mushroom_granny": ([".####.", "######", "#.##.#", "..##..", "..##.."], (226, 86, 98)),
         "firefly_vendor": ([".#..#.", "..##..", ".####.", ".#oo#.", "..oo.."], (62, 140, 138))}[kind]
    for j, r in enumerate(g[0]):
        for i, ch in enumerate(r):
            if ch == "#": px(a, 6 + i, 6 + j, g[1])
            if ch == "o": px(a, 6 + i, 6 + j, (255, 220, 90))
    pxs(a, [(4, 5), (5, 4)], WHITE)
    return a

def hearts():
    g = [".##.##.", "#######", "#######", ".#####.", "..###..", "...#..."]
    fr = []
    for full in (0, 1):
        a = canvas(9, 8)
        for j, r in enumerate(g):
            for i, ch in enumerate(r):
                if ch == "#": px(a, i + 1, j + 1, ((255, 150, 186) if j < 2 else (236, 96, 140)) if full else (255, 240, 246))
        if full: px(a, 2, 2, WHITE)
        fr.append(add_outline(a, F.UI_OL))
    return fr

def portrait(frame, piv, head, kind):
    W = 26; a = canvas(W, W); Y, X = np.mgrid[0:W, 0:W]; d = np.hypot(X - 12.5, Y - 12.5)
    bg = {"snail_postman": (255, 226, 214), "mushroom_granny": (236, 226, 255), "firefly_vendor": (214, 246, 236)}[kind]
    a[d <= 12.6] = (*F.UI_OL, 255); a[d <= 11.6] = (*WHITE, 255); a[d <= 10.2] = (*bg, 255)
    inner = d <= 10.2
    hx, hy = head
    cx = {"snail_postman": hx - 1, "mushroom_granny": hx, "firefly_vendor": hx - 3}[kind]
    cy0 = {"snail_postman": hy - 2, "mushroom_granny": hy + 2, "firefly_vendor": hy}[kind]
    crop = canvas(W, W); paste(crop, frame, 13 - cx, 3 - cy0)
    m = (crop[..., 3] == 255) & inner; a[m] = crop[m]
    return B.limit([a], 12)[0]

def decor_mailbox():
    RED = ((255, 150, 150), (230, 92, 104), (176, 56, 84)); POST = ((150, 110, 86), (110, 78, 64))
    parts = [P("rect", (7, 16, 9, 24), POST, z=0), P("ell", (8.5, 9, 7.5, 7.2), RED, z=1, clip=(0, 0, 99, 9)), P("rect", (1, 9, 15, 17), RED, z=1)]
    a, _ = render(parts, 18, 27)
    for x in range(4, 13): px(a, x, 11, (110, 40, 70))
    pxs(a, [(15, 4), (15, 5), (15, 6), (15, 7), (16, 4), (17, 4), (16, 5), (17, 5)], (255, 214, 92))   # 小旗
    pxs(a, [(5, 14), (6, 14), (11, 14), (12, 14)], (255, 236, 220)); px(a, 3, 6, WHITE)
    for x in range(4, 13): px(a, x, 25, (110, 150, 90))
    return add_outline(a)
def decor_mushlamp():
    CAP = ((255, 240, 180), (250, 206, 110), (220, 150, 80)); ST = ((255, 246, 228), (230, 210, 186))
    parts = [P("rect", (6, 11, 11, 20), ST, z=0), P("ell", (8.5, 10, 8, 7), CAP, z=1, clip=(0, 0, 99, 11)), P("ell", (8.5, 20.5, 6, 1.6), ((150, 200, 120), (104, 170, 96)), z=2)]
    a, _ = render(parts, 18, 23)
    for (x, y) in ((5, 6), (10, 4), (13, 8)): px(a, x, y, (255, 252, 230))
    pxs(a, [(7, 15), (8, 16), (9, 16), (10, 15)], (40, 26, 52))   # 細笑
    return add_outline(a)
def decor_jar():
    GL = ((236, 248, 255), (196, 222, 246), (160, 190, 226)); LID = ((206, 148, 100), (150, 98, 72))
    parts = [P("ell", (7, 13, 6, 7.5), GL, z=0), P("rect", (3, 3, 10, 5), LID, z=1)]
    a, _ = render(parts, 14, 22)
    for (x, y) in ((5, 11), (8, 14), (6, 16), (9, 10)): pxs(a, [(x, y), (x + 1, y)], (255, 230, 110)); px(a, x, y - 1, (255, 252, 200))
    pxs(a, [(7, 1), (7, 2), (6, 0), (8, 0)], LID[1])
    return add_outline(a)
def glow_mask(a, cols):
    g = np.zeros_like(a); m = np.zeros(a.shape[:2], bool)
    for c in cols: m |= np.all(a[..., :3] == c, -1) & (a[..., 3] == 255)
    g[m] = (255, 255, 255, 255); return g
def prop_letter():
    a = canvas(13, 10)
    parts = [P("rect", (1, 1, 11, 8), ((255, 255, 255), (246, 240, 230), (224, 214, 204)), z=0)]
    a, _ = render(parts, 13, 10)
    for i in range(5): px(a, 1 + i, 1 + i // 1 if i < 5 else 0, (214, 200, 196)); px(a, 11 - i, 1 + i, (214, 200, 196))
    pxs(a, [(6, 5), (5, 4), (7, 4), (6, 4)], (236, 104, 128))   # 心形火漆
    return add_outline(a)
def prop_seed():
    parts = [P("ell", (5, 6, 3.6, 4.6), ((214, 170, 120), (170, 124, 86), (128, 90, 66)), z=0)]
    a, _ = render(parts, 10, 12)
    pxs(a, [(5, 0), (5, 1), (6, 0), (4, 1)], (104, 170, 96))
    return add_outline(a)

def build_visitors(manifest):
    data = {}
    sheets = {}
    for vid, v in VIS.items():
        clips = v["fn"](); W, H = v["W"], v["H"]; piv = v["piv"]
        allfr = B.limit(clips["idle"] + clips["walk"] + clips["happy"], 12)
        allfr = [np.pad(f, ((0, 1), (0, 0), (0, 0))) for f in allfr]; H += 1      # 腳底下留 1 行（同 48px 線一致）
        clips = {"idle": allfr[0:6], "walk": allfr[6:12], "happy": allfr[12:18]}
        hover = vid == "firefly_vendor"
        piv = (piv[0], 40) if hover else (piv[0], low_row(clips["idle"][0]) - 1)
        ent = {"name": v["name"], "order": v["order"], "note": v["note"], "frameW": W, "frameH": H, "pivot": list(piv), "facing": "right（向左 = 引擎 flipX，pivot.x 鏡像 = W−1−x）",
               "clips": {}, "anchors": {"head": v["head"], "bag": v["bag"]}, "hitbox": {"rel": v["hit"], "note": "相對 pivot 嘅 [x0,y0,x1,y1]；拖禮物落呢個框＝送禮"},
               "hover": hover, "walkSpeed": v["speed"], "palette": len(B.colors_of(allfr))}
        for c in ("idle", "walk", "happy"):
            rel = sv(B.strip(clips[c]), f"visitors/{vid}/{vid}_{c}.png")
            ent["clips"][c] = {"file": rel, "frames": 6, "ms": CLIP_MS[c], "loop": c != "happy"}
            assert all(low_row(f) <= piv[1] + 1 for f in clips[c])
            if not hover and c != "happy": assert low_row(clips[c][0]) == piv[1] + 1
        if vid == "firefly_vendor":
            em = [glow_mask(f, [V.GLOWY[0], V.GLOWY[1]]) for f in allfr]
            for i, c in enumerate(("idle", "walk", "happy")):
                rel = sv(B.strip(em[i * 6:(i + 1) * 6]), f"visitors/{vid}/{vid}_{c}_emissive.png")
                ent["clips"][c]["emissive"] = rel
            ent["glow"] = {"color": "#FFE68A", "radius": 10, "anchor": [12, 30], "pulseMs": 1400, "note": "尾燈 glow：引擎 radial；emissive 白＝發光像素"}
        pt = portrait(clips["idle"][0], piv, v["head"], vid); ent["portrait"] = {"file": sv(pt, f"visitors/{vid}/{vid}_portrait.png"), "w": 26, "h": 26}
        ent["badge"] = {"file": sv(badge(vid), f"visitors/{vid}/{vid}_badge.png"), "w": 18, "h": 18, "note": "友好度滿 5 嘅徽章（spec 有提，額外加嘅小圖）"}
        data[vid] = ent; sheets[vid] = clips
    # 擺設（每位 1 件專屬，友好度滿 5 留低）
    deco = {"snail_postman": ("deco_mailbox", decor_mailbox(), "郵筒仔", None),
            "mushroom_granny": ("deco_mushroom_lamp", decor_mushlamp(), "蘑菇夜燈", [(255, 240, 180), (250, 206, 110), (255, 252, 230)]),
            "firefly_vendor": ("deco_firefly_jar", decor_jar(), "螢火瓶燈", [(255, 230, 110), (255, 252, 200)])}
    for vid, (did, img, nm, gc) in deco.items():
        img = B.limit([img], 12)[0]
        e = {"id": did, "name": nm, "file": sv(img, f"decor/{did}.png"), "w": img.shape[1], "h": img.shape[0], "pivot": [img.shape[1] // 2, low_row(img) - 1]}
        if gc: e["emissive"] = sv(glow_mask(img, gc), f"decor/{did}_emissive.png")
        data[vid]["decor"] = e
    lt = prop_letter(); sd = prop_seed(); hs = hearts()
    props = {"letter": {"file": sv(lt, "props/prop_letter.png"), "w": lt.shape[1], "h": lt.shape[0], "pivot": [6, 9], "note": "蝸牛信：由 bag 錨點彈上頭頂（move），撳 → 開日記一句（文字引擎出）"},
             "seed": {"file": sv(sd, "props/prop_seed.png"), "w": sd.shape[1], "h": sd.shape[0], "pivot": [5, 11], "note": "蘑菇婆婆送嘅種子；彈去背包"},
             "friend_heart": {"file": sv(B.strip(hs), "props/friend_heart.png"), "frameW": 9, "frameH": 8, "frames": 2, "note": "友好度格：幀0 空、幀1 滿；5 粒一行，間距 10px"}}
    return data, props, sheets, deco

# 團絨「扮大佬帶佢行一圈」— 3a clip 格式（49 隻通用）
LEAD_CLIPS = {
    "visit_lead_start": {"group": "visit", "dur": 900, "loop": False, "trigger": "訪客企定後 400ms；之後接 visit_lead_strut",
                          "body": [{"t": 0}, {"t": 180, "sx": 0.94, "sy": 1.08, "y": -1, "e": "out"}, {"t": 420, "sx": 0.96, "sy": 1.07, "rot": -4, "e": "inout"},
                                   {"t": 700, "sx": 0.96, "sy": 1.07, "rot": -4}, {"t": 900, "sx": 1, "sy": 1, "rot": 0, "e": "outBack"}],
                          "face": [{"t": 0, "f": "smug"}], "fx": [{"id": "fx_sparkle", "anchor": "headTop", "dx": 6, "dy": -2, "t0": 250, "t1": 750, "ms": 120, "loop": False}],
                          "events": [{"t": 300, "id": "line:visit_lead"}]},
    "visit_lead_strut": {"group": "visit", "dur": 600, "loop": True, "trigger": "帶路行一圈時；引擎沿 path 郁 x/y；舊形態可改用 atlas walk_happy＋smug 面",
                          "body": [{"t": 0, "sx": 1, "sy": 1}, {"t": 150, "sx": 1.05, "sy": 0.94, "y": 0, "e": "out"}, {"t": 300, "sx": 0.97, "sy": 1.05, "y": -2, "rot": -3, "e": "out"},
                                   {"t": 450, "sx": 1.05, "sy": 0.94, "y": 0, "rot": 0, "e": "in"}, {"t": 600, "sx": 0.97, "sy": 1.05, "y": -2, "rot": 3, "e": "out"}],
                          "face": [{"t": 0, "f": "smug"}]},
    "visit_gift_cheer": {"group": "visit", "dur": 700, "loop": False, "trigger": "送禮成功（友好度 +1）",
                          "body": [{"t": 0}, {"t": 120, "sx": 1.12, "sy": 0.88, "e": "out"}, {"t": 300, "sx": 0.94, "sy": 1.08, "y": -5, "e": "out"}, {"t": 520, "sx": 1.06, "sy": 0.95, "y": 0, "e": "in"}, {"t": 700, "sx": 1, "sy": 1, "e": "outBack"}],
                          "face": [{"t": 0, "f": "laugh_b"}, {"t": 600, "f": "smug"}], "fx": [{"id": "fx_heart", "anchor": "headTop", "dx": 0, "dy": -2, "t0": 200, "t1": 700, "ms": 160, "move": [[0, 0, 0], [500, 0, -8]]}]},
}
LEAD_PATH = {"note": "art 座標；團絨行頭、訪客跟尾（落後 path 距離 30px）；y 細＝遠（引擎按 y 排深淺）",
             "loop": [[97, 296], [128, 300], [150, 292], [132, 284], [97, 282], [62, 284], [44, 292], [66, 300], [97, 296]],
             "lapMs": 8000, "followGap": 30, "visitorSpeedDuringLead": "跟團絨速度（約 23px/s），walk 幀 ms ×0.7"}

# ═════════════════════════ ④ 進化大場面 ═════════════════════════
def build_evo(manifest):
    E = {}
    def put(key, frames, rel, piv, ms=None, loop=None, note="", n=12):
        frames = B.limit(frames, n); sv(B.strip(frames), rel)
        E[key] = {"file": rel, "frameW": frames[0].shape[1], "frameH": frames[0].shape[0], "frames": len(frames), "pivot": list(piv), "note": note}
        if ms: E[key]["ms"] = ms
        if loop is not None: E[key]["loop"] = loop
        return frames
    co = F.cocoon_form(); piv = (F.CPIV[0], low_row(co[-1]) - 1)
    put("evo_mote", F.motes(), "evo/evo_mote.png", (3, 3), 80, True, "聚光粒（螺旋吸入寵物）")
    put("evo_cocoon_form", co, "evo/evo_cocoon_form.png", piv, 200, False, "光繭由下包上（6 幀）；pivot 對寵物 pivot")
    put("evo_cocoon_pulse", F.cocoon_pulse(), "evo/evo_cocoon_pulse.png", piv, 150, True, "光繭呼吸 loop；配 body sx/sy keys")
    put("evo_cocoon_crack", F.cocoon_crack(), "evo/evo_cocoon_crack.png", piv, 125, False, "裂開 4 幀，最後一幀分兩邊")
    put("evo_shard", F.shards(), "evo/evo_shard.png", (4, 3), None, None, "繭碎 3 款（幀 index＝款），爆開時放射飛走")
    put("evo_rays", F.rays(), "evo/evo_rays.png", (56, 56), 90, True, "背光放射線（寵物後）；引擎可再慢慢 rotate（snap 15°）")
    put("evo_ring", F.ring(), "evo/evo_ring.png", (47, 47), 70, False, "衝擊光圈 5 幀")
    cf, kinds = F.confetti()
    put("evo_confetti", cf, "evo/evo_confetti.png", (3, 3), 140, True, f"彩紙：每款 2 幀 → {kinds}（index = 款×2 + 幀）")
    put("evo_skip_hint", F.skip_hint(), "evo/evo_skip_hint.png", (7, 7), 450, True, "2s 後右下角出，肉球 tap 印（冇字）")
    db, ctr = F.dream_bubble()
    put("omen_dream_bubble", db, "evo/omen_dream_bubble.png", (3, 32), 220, False, f"預兆怪夢泡泡：幀0→1→2 冒出；夢圖中心 = {list(ctr)}")
    ic = F.dream_icons(); keys = F.DREAM_ICONS
    put("omen_dream_icons", [ic[k] for k in keys], "evo/omen_dream_icons.png", (ic[keys[0]].shape[1] // 2, ic[keys[0]].shape[0] // 2), None, None, f"6 個怪夢（index）：{keys}")
    E["_dreamCenter"] = list(ctr)
    # 名卡
    cards = {}
    for r in ["base"] + F.ROUTES:
        tok = L.token(L.OLD_SERIES.get(r, "leaf"))
        c = B.limit([F.name_card(r, tok)], 12)[0]
        cards[r] = {"file": sv(c, f"cards/card_{r}.png"), "w": F.CARD_W, "h": F.CARD_H}
    return E, cards

ROUTE_ZH = {"tide": "潮汐", "moon": "月影", "shroom": "菇菇", "crystal": "晶石", "ember": "餘燼", "radiant": "燦光", "soft": "柔光", "dust": "微塵", "lumi": "螢光"}
NODES = [("evo_egg", "evo_dot"), ("evo_dot", "evo_sprout"), ("evo_sprout", "evo_hop"), ("evo_hop", "evo_guard_{r}"), ("evo_guard_{r}", "evo_still_{r}")]
CARD_FOR = {"evo_dot": "base", "evo_sprout": "base", "evo_hop": "base"}

TIMELINE = {
    "durMs": 8000, "skippableAfterMs": 2000, "art": "195×422；寵物 pivot art (97,292)；全畫面（HUD 收起）",
    "rules": ["唔會打斷小遊戲／拖動：有嘢做緊就排隊，做完先播", "2000ms 後撳一下 → 直接跳去 5600（現身）再 300ms 後出名卡；名卡出咗再撳 = 收"],
    "tracks": [
        {"id": "dim", "t0": 0, "t1": 600, "color": "#1E1630", "alpha": [0, 0.7], "ease": "ioSine", "note": "之後保持 0.7；5600 起 0.7→0.45（400ms）；7700–8000 →0"},
        {"id": "pet_shake", "t0": 300, "t1": 1500, "x": "round(sin(t*0.09)*k)，k 0→1.5 線性", "face": "surprised"},
        {"id": "evo_mote", "t0": 400, "t1": 2200, "count": 14, "spawnSpreadMs": 600, "lifeMs": 1100, "path": "螺旋：r = 90·(1−oCubic(u))，θ = θ0 + 2.5π·u；目標 = 寵物中心 (pivot.x, pivot.y − h/2)", "ms": 80},
        {"id": "pet_flicker", "t0": 900, "t1": 1500, "mode": "silhouette #FFF6DA 同原色交替", "intervalMs": [120, 60]},
        {"id": "pet_silhouette", "t0": 1500, "t1": 5600, "color": "#FFF6DA", "note": "canvas：drawImage → globalCompositeOperation='source-in' fillRect（offscreen）；再加 1px 描邊 #967EDC（剪影 4 方向偏 1px 先畫描邊色，再畫剪影）——唔加會同 rays 溶埋", "outline": "#967EDC"},
        {"id": "evo_cocoon_form", "t0": 1500, "t1": 2700, "anchor": "pivot"},
        {"id": "evo_cocoon_pulse", "t0": 2700, "t1": 3900, "anchor": "pivot", "body": {"t": [0, 300, 600, 900, 1200], "sx": [1, 1.04, 0.98, 1.06, 1], "sy": [1, 0.97, 1.03, 0.95, 1]}, "msRamp": [150, 90]},
        {"id": "evo_cocoon_crack", "t0": 3900, "t1": 4400, "anchor": "pivot"},
        {"id": "evo_shard", "t0": 4400, "t1": 4900, "count": 8, "path": "由繭中心放射，dist 0→40 oCubic，重力 +30px/s²，alpha 照 0/255（最後 100ms 隔幀閃）"},
        {"id": "evo_ring", "t0": 4400, "t1": 4750, "anchor": "center"},
        {"id": "evo_rays", "t0": 4400, "t1": 7000, "anchor": "center", "z": "back", "note": "6 幀 loop；6500 後隔幀閃收"},
        {"id": "silhouette_swap", "t0": 4400, "t1": 5600, "swapsAt": [4400, 4620, 4800, 4940, 5050, 5140, 5210, 5270, 5320, 5360, 5400, 5440, 5480, 5520, 5560],
         "note": "每次換：舊剪影 ↔ 新剪影，同時 squash sx 1.15/sy 0.88 → 1（90ms）；最後一個係新形態"},
        {"id": "flash", "t0": 5600, "t1": 5900, "color": "#FFFFFF", "alpha": [0.85, 0], "ease": "oCubic"},
        {"id": "pet_reveal", "t0": 5600, "t1": 6100, "body": {"t": [0, 120, 260, 380, 500], "sx": [1.3, 0.9, 1.06, 0.98, 1], "sy": [0.7, 1.12, 0.96, 1.01, 1]}, "face": "smug", "then": "新形態 celebrate（舊線 atlas）／3a smug 面"},
        {"id": "evo_confetti", "t0": 5600, "t1": 7400, "count": 28, "path": "由寵物中心向上噴：vx ±60, vy −90..−140 px/s，重力 160px/s²；各自 ms 120–180"},
        {"id": "name_card", "t0": 6000, "t1": 7700, "center": [97, 352], "pop": "MOTION.md 彈窗 sticker pop：t=[0,.45,.7,.85,1] scale=[0,1.1,.96,1.02,1] rot=[−8,4,−2,1,0]°（500ms）",
         "exit": "7500–7700：scale 1→0.6（iBack）alpha 1→0", "portraitPet": "新形態 idle 幀 0，pivot 落 card petPivot（可以凸出圓框，故意）", "text": "名（card.textBoxes.name，白字）＋呆介紹（line）；打字效果 30ms/字"},
        {"id": "evo_skip_hint", "t0": 2000, "t1": 5600, "pos": [180, 400]},
    ],
    "sfxHooks": ["evo_dim", "evo_mote_tick", "evo_cocoon_wrap", "evo_heartbeat(每次 pulse)", "evo_crack", "evo_burst", "evo_swap_tick", "evo_reveal_jingle", "card_pop"],
}
OMENS = {
    "window": "達下一階門檻前最後 24h，隨機 1 款",
    "flicker": {"everyMs": [4000, 7000], "flashes": 2, "flashMs": 80, "gapMs": 100, "color": "#FFF6DA", "alpha": 0.6, "note": "寵物剪影疊色（同進化 silhouette 一樣做法），冇新圖"},
    "appetite": {"eatMul": 1.5, "line": "line:omen_feel_strong", "note": "冇新圖；食完用 3a smug 面 600ms"},
    "dream": {"when": "瞓緊（sleep_loop）", "everyMs": 20000, "bubble": "omen_dream_bubble", "anchor": "headTop", "dx": 4, "dy": -2, "seq": "幀0 220ms → 幀1 220ms → 幀2 hold 2200ms（夢圖每 400ms 上下 1px）→ 3a fx_puff 收",
              "icons": "omen_dream_icons 隨機 1 個，畫喺 bubble 夢中心（_dreamCenter）"},
}

# ───────── 4 格漫畫 ─────────
PW, PH = 86, 78; FW, FH = PW + 6, PH + 6
def panel_bg(h, cx, top=244):
    s = scene_layer(h); return s[top:top + PH, cx - PW // 2:cx - PW // 2 + PW].copy()
def frame_panel(img):
    o = canvas(FW, FH)
    om = F._rrect(FW, FH, 0, 0, FW - 1, FH - 1, 6); wm = F._rrect(FW, FH, 1, 1, FW - 2, FH - 2, 5); im = F._rrect(FW, FH, 3, 3, FW - 4, FH - 4, 3)
    o[om] = (*F.UI_OL, 255); o[wm] = (*WHITE, 255)
    sub = o[3:3 + PH, 3:3 + PW]; m = im[3:3 + PH, 3:3 + PW]; sub[m] = img[m]; sub[m, 3] = 255
    return o

def prop_eggshell():
    a = canvas(14, 7); C = ((255, 252, 236), (250, 232, 190), (226, 196, 140))
    b, _ = render([P("ell", (7, 7, 6, 5), C, z=0, clip=(0, 2, 99, 99))], 14, 7)
    for i, x in enumerate(range(1, 13)): px(b, x, 2 + (i % 2), (0, 0, 0)) if False else None
    for x in range(1, 13, 2): b[2, x] = 0
    return add_outline(b)
def prop_seedling():
    a = canvas(12, 14)
    parts = [P("rect", (5, 6, 6, 13), (104, 170, 96), z=0, flat=True), P("ell", (3, 5, 3, 2), ((170, 230, 140), (104, 170, 96), (72, 132, 80)), z=1),
             P("ell", (9, 4, 3, 2), ((170, 230, 140), (104, 170, 96), (72, 132, 80)), z=1)]
    b, _ = render(parts, 12, 14); return add_outline(b)
def prop_mound():
    b, _ = render([P("ell", (13, 10, 13, 6), ((176, 128, 92), (140, 98, 72), (104, 72, 58)), z=0, clip=(0, 0, 99, 10))], 26, 12)
    for (x, y) in ((6, 7), (14, 5), (19, 8)): px(b, x, y, (196, 150, 110))
    return add_outline(b)
def prop_butterfly(f=0):
    b, _ = render([P("ell", (3, 3 + f, 2.6, 2.4 - f * .6), ((255, 214, 236), (246, 150, 196)), z=0), P("ell", (8, 3 + f, 2.6, 2.4 - f * .6), ((255, 214, 236), (246, 150, 196)), z=0),
                   P("rect", (5, 2, 5, 6), (90, 60, 90), z=1, flat=True)], 11, 8)
    return add_outline(b)
def prop_stick():
    b = canvas(5, 22)
    for y in range(2, 20): px(b, 2, y, (150, 100, 70)); px(b, 3, y, (110, 78, 64)) if y > 10 else None
    pxs(b, [(1, 3), (0, 2), (3, 5), (4, 4)], (104, 170, 96))
    return add_outline(b)
def prop_leaf(c=(246, 160, 80)):
    b = canvas(7, 6); pxs(b, [(1, 1), (2, 1), (3, 1), (0, 2), (1, 2), (2, 2), (3, 2), (4, 2), (1, 3), (2, 3), (3, 3), (4, 3), (3, 4), (5, 4)], c)
    return add_outline(b)

def comic_panels(route):
    """返 [(node, idx, img, routeDependent)]；route 只影響第 4、5 節點"""
    R = route; res = []
    tokimg = L.token(L.OLD_SERIES[R])
    def shrink(a, k=.72):
        im = Image.fromarray(a).resize((round(a.shape[1] * k), round(a.shape[0] * k)), Image.NEAREST); return np.array(im)
    co = [shrink(c) for c in F.cocoon_pulse()]; cr = [shrink(c) for c in F.cocoon_crack()]; ry = F.rays(); mo = F.motes()
    CPX, CPY = co[0].shape[1] // 2, low_row(co[0])
    def bg(h, cx): return panel_bg(h, cx)
    # node1 光卵→絨點（夜）
    n = []
    a = bg("H4", 60); put_pet(a, "evo_egg", "idle_01", (40, 66)); put_fx(a, "fx_sparkle", 0, 58, 40); put_fx(a, "fx_sparkle", 1, 22, 30); n.append(a)
    a = bg("H4", 60); put_pet(a, "evo_egg", "tap_02", (40, 66)); put_fx(a, "fx_question", 0, 50, 36); put_fx(a, "fx_sweat", 0, 30, 44); n.append(a)
    a = bg("H4", 60); paste(a, ry[2], 40 - 56, 56 - 56); put_pet(a, "evo_egg", "hatch_04", (40, 66), silc=None); [paste(a, mo[i % 3], x, y) for i, (x, y) in enumerate([(14, 20), (66, 26), (20, 50), (60, 54)])]; n.append(a)
    a = bg("H4", 60); put_pet(a, "evo_dot", "smug_pose_01", (42, 66)); es = prop_eggshell(); paste(a, es, 35, 42); paste(a, B.flipx(es), 58, 61); put_fx(a, "fx_sparkle", 1, 64, 30); n.append(a)
    res += [("n1", i, x, False) for i, x in enumerate(n)]
    # node2 絨點→絨芽（朝）
    n = []; sd = prop_seedling(); md = prop_mound()
    a = bg("H1", 80); paste(a, sd, 54, 53); put_pet(a, "evo_dot", "lookup_01", (34, 66)); put_fx(a, "fx_question", 0, 44, 30); n.append(a)
    a = bg("H1", 80); paste(a, sd, 58, 53); put_pet(a, "evo_dot", "act_cool_01", (34, 70)); paste(a, md, 21, 59); put_fx(a, "fx_sweat", 0, 46, 40); n.append(a)
    a = bg("H1", 80); paste(a, ry[1], 34 - 56, 56 - 56); put_pet(a, "evo_dot", "idle_01", (34, 66), silc=(255, 246, 218)); paste(a, sd, 58, 53); [paste(a, mo[i % 3], x, y) for i, (x, y) in enumerate([(10, 28), (52, 24), (14, 52)])]; n.append(a)
    a = bg("H1", 80); paste(a, sd, 60, 53); put_pet(a, "evo_sprout", "smug_pose_01", (36, 66)); put_fx(a, "fx_sparkle", 1, 18, 34); put_fx(a, "fx_sparkle", 0, 52, 30); n.append(a)
    res += [("n2", i, x, False) for i, x in enumerate(n)]
    # node3 絨芽→絨跳（日）
    n = []
    a = bg("H3", 120); put_pet(a, "evo_sprout", "lookup_01", (34, 66)); paste(a, prop_butterfly(0), 52, 22); n.append(a)
    a = bg("H3", 120); put_pet(a, "evo_sprout", "droop_03", (40, 67)); put_fx(a, "fx_puff", 0, 40, 68) if "fx_puff" in FX3A else None; paste(a, prop_butterfly(1), 60, 16); put_fx(a, "fx_sweat", 0, 50, 46); n.append(a)
    a = bg("H3", 120); paste(a, co[1], 40 - CPX, 66 - CPY); [paste(a, mo[i % 3], x, y) for i, (x, y) in enumerate([(10, 30), (70, 22), (66, 52)])]; n.append(a)
    a = bg("H3", 120); put_pet(a, "evo_hop", "cheer_jump_03", (40, 58)); paste(a, prop_butterfly(0), 62, 14); put_fx(a, "fx_sparkle", 1, 18, 28); n.append(a)
    res += [("n3", i, x, False) for i, x in enumerate(n)]
    # node4 絨跳→守夜者（夜）
    n = []; st = prop_stick(); g = f"evo_guard_{R}"
    a = bg("H4", 150); put_pet(a, "evo_hop", "lookup_01", (34, 66)); put_fx(a, "fx_question", 0, 46, 34); n.append(a)
    a = bg("H4", 150); paste(a, st, 52, 46); put_pet(a, "evo_hop", "sleep_loop_01", (36, 66)); put_fx(a, "fx_zzz", 1, 48, 40); n.append(a)
    a = bg("H4", 150); paste(a, ry[3], 40 - 56, 52 - 56); put_pet(a, "evo_hop", "idle_01", (40, 66), silc=(255, 246, 218)); paste(a, co[2], 40 - CPX, 66 - CPY); n.append(a)
    a = bg("H4", 150); paste(a, st, 64, 46); put_pet(a, g, "smug_pose_01", (38, 66)); [paste(a, tokimg, x, y) for (x, y) in ((10, 26), (60, 20), (70, 40))]; n.append(a)
    res += [("n4", 0, n[0], False), ("n4", 1, n[1], False), ("n4", 2, n[2], False), ("n4", 3, n[3], True)]
    # node5 守夜者→靜光（黃昏）
    n = []; s = f"evo_still_{R}"; lf = prop_leaf()
    a = bg("H2", 70); put_pet(a, g, "lookup_01", (40, 66)); paste(a, lf, 20, 18); paste(a, lf, 58, 30); paste(a, B.flipx(lf), 34, 8); n.append(a)
    a = bg("H2", 70); put_pet(a, g, "sleep_loop_01", (36, 66)); dbb, ctr = F.dream_bubble(); ic = F.dream_icons()
    paste(a, dbb[2], 46 - 3, 42 - 32); di = ic["walking_teacup"]; paste(a, di, 46 - 3 + ctr[0] - di.shape[1] // 2, 42 - 32 + ctr[1] - di.shape[0] // 2); n.append(a)
    a = bg("H2", 70); paste(a, ry[2], 40 - 56, 50 - 56); paste(a, cr[2], 40 - CPX, 66 - CPY); n.append(a)
    a = bg("H2", 70); put_pet(a, s, "celebrate_01", (40, 66)); [paste(a, tokimg, x, y) for (x, y) in ((8, 22), (68, 16), (72, 44))]; put_fx(a, "fx_sparkle", 1, 18, 44); n.append(a)
    res += [("n5", i, x, True) for i, x in enumerate(n)]
    return res

CAPTION_DRAFT = {   # 遊美暫擬，遊策可改；文字由引擎畫
    "n1": ["夜晚，蛋好靜。", "蛋：「我覺得我就嚟好勁。」", "光！好多光！", "「出嚟喇，好易啫。」（殼仲喺頭）"],
    "n2": ["見到棵芽仔。", "「我都種自己落泥度。」", "泥入面發光喇……", "「睇！我自己種出片葉。」"],
    "n3": ["隻蝴蝶飛得好高。", "「跳！」（撻低）", "光又嚟喇。", "「我一早識跳㗎。」"],
    "n4": ["夜晚要有人守。", "「我守緊……zzz」", "光繭包住佢。", "{route}守夜者：「完全計劃之內。」"],
    "n5": ["睇住落葉，諗嘢。", "夢見茶杯識行路。", "最後一次光。", "{route}靜光：「我一直都好醒。」"],
}

def main():
    keep = None
    if os.path.isfile(os.path.join(OUT, "BATCH3B.md")): keep = open(os.path.join(OUT, "BATCH3B.md"), encoding="utf-8").read()
    if os.path.isdir(OUT): shutil.rmtree(OUT)
    os.makedirs(OUT)
    if keep is not None: open(os.path.join(OUT, "BATCH3B.md"), "w", encoding="utf-8").write(keep)  # 手寫文件保留
    man = {}
    vis, props, sheets, deco = build_visitors(man)
    evo, cards = build_evo(man)
    # 名卡對應（9 張 = 9 路線；首 3 個節點用 base 卡，額外）
    cardmap = {}
    for a, b_ in NODES:
        for r in F.ROUTES:
            to = b_.format(r=r); cardmap[to] = cards[CARD_FOR.get(to, r)]["file"].split("/")[-1].replace(".png", "")
    # 漫畫
    panels = {}
    for r in F.ROUTES:
        for node, i, img, dep in comic_panels(r):
            key = f"{node}_p{i + 1}" + (f"_{r}" if dep else "")
            if key in panels: continue
            fr = frame_panel(img); rel = sv(fr, f"comics/{key}.png")
            panels[key] = {"file": rel, "w": FW, "h": FH, "routeDependent": dep, "route": r if dep else None}
    comics = {"panelW": FW, "panelH": FH, "inner": [3, 3, PW, PH], "layout": {"grid": "2×2", "pos": [[3, 60], [100, 60], [3, 168], [100, 168]], "captionBox": "每格下面 [x, y+86, 92, 18]，文字引擎畫",
              "note": "團絨日記頁（art 195×422）；橫向讀：左上→右上→左下→右下"},
              "nodes": {}, "captionDraft": CAPTION_DRAFT, "captionNote": "{route} = 路線中文名（ROUTE_ZH）；文案遊策定，呢度只係草稿"}
    for k, (a, b_) in enumerate(NODES):
        nid = f"n{k + 1}"; dep = k >= 3
        comics["nodes"][nid] = {"from": a, "to": b_, "unlock": f"進化節點 {k + 1}（{a} → {b_}）",
                                "panels": [f"{nid}_p{i}" + ("_{route}" if (k == 4 or (k == 3 and i == 4)) else "") for i in range(1, 5)]}
    comics["routeZh"] = ROUTE_ZH
    J = {"version": "batch3b-1", "units": "px（art 1x）；時間 ms", "generated": "2026-11-01 HKT", "tool": "tools/build_batch3b.py",
         "visitors": vis, "visitorProps": props, "visitRules": {
             "spawn": "存檔第 3 日起；每日最多 1 位；隨機一次上線時出；留 10 分鐘或到落線", "vendorHours": "firefly_vendor 只 17:00–07:00",
             "enter": "由畫面左或右邊（x −30 / 225）walk 入，企喺團絨旁 ±46px（地面 y 292）", "lead": LEAD_PATH,
             "gift": "拖散步收集品／花落 hitbox → 訪客 happy 1 次（6 幀）＋ 3a fx_heart 喺 head 錨點；團絨 visit_gift_cheer；每位每日最多 1",
             "friendshipMax": 5, "reward": "滿 5 → decor（專屬擺設）＋ badge", "leave": "walk 出畫面（反方向）"},
         "petClips3aFormat": LEAD_CLIPS,
         "evolution": {"assets": evo, "timeline": TIMELINE, "omens": OMENS,
                       "cards": {"files": cards, "w": F.CARD_W, "h": F.CARD_H, "portrait": F.CARD_PORTRAIT, "textBoxes": F.CARD_TEXT, "formToCard": cardmap,
                                 "formName": {f: form_name(f) for f in sorted(set(x.format(r=r) for p in NODES for x in p for r in F.ROUTES))}}},
         "comics": comics}
    json.dump(J, open(os.path.join(OUT, "batch3b.json"), "w"), ensure_ascii=False, indent=1)
    # 3a clip 格式另存（方便 merge 落 reactions.json）
    json.dump({"clips": LEAD_CLIPS}, open(os.path.join(OUT, "visit_pet_clips.json"), "w"), ensure_ascii=False, indent=1)
    print("visitors", list(vis), "evo assets", len(evo), "cards", len(cards), "panels", len(panels))
    return J

if __name__ == "__main__":
    main()
