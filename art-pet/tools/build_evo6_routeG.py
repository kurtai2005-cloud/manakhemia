#!/usr/bin/env python3
"""build_evo6_routeG.py — 團絨 evo6 batch G「路線清晰化」（pet-template-v1.md §7 路線清晰化，Kurt 2026-11-01 01:03）。
1) 跳跳期（絨跳 evo_hop）頭頂燈泡「慢慢轉做而家領先路線嘅顏色」：8 條路各一個燈色 ramp（螢絨唔顯示＝保持原燈黃）。
   交付＝palette_route_bulbs.json（tint spec＋ramp）＋每路 palette_evo_hop_<id>.json（31 色，只換燈 3 色）＋
   atlas_evo_hop_bulbmask.png（同 atlas_evo_hop.png layout；R/G/B＝glow/glow_mid/glow_core 燈像素）＋每路已換色 atlas_evo_hop_bulb_<id>.png。
   現有 evo_hop 散檔一粒像素都冇改（只係 atlas 重新排咗加 tell clip）。emissive 遮罩唔變（燈 glow_mid/glow_core 位照舊發光，色跟 albedo）。
2) 圖鑑未解鎖剪影 ×9：靜光 48（完全體）idle_01 實心剪影（去走 aura 碎點），原尺寸 48px；collection_route.json 帶一句提示。
3) 判定前 12h「預告」小動作 ×9：由絨跳（跳跳期，判定前嗰個形態）播；tell_<id>，同 std 標準：frames／layers（_noface／_faceov）／emissive／anchors（含 bulb）／atlas。
Pillow＋numpy 程式逐像素繪製，原創，無 AI。用法：python3 build_evo6_routeG.py [--no-docs]
"""
import json, math, os, sys, shutil
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_evo6_animF as F5      # 註冊晒 9 條支線靜光（BC＋F）
A, L, M, EC, bt, BC = F5.A, F5.L, F5.M, F5.EC, F5.bt, F5.BC
IDX = A.IDX if hasattr(A, "IDX") else BC.IDX
OUT, PRV, MOT, ROOT, TR = A.OUT, A.PRV, A.MOT, A.ROOT, A.TR
RC = os.path.join(OUT, "route_clarity"); os.makedirs(RC, exist_ok=True)
FORM = "evo_hop"; HD = os.path.join(OUT, FORM)

# ============================================================ 路線＋燈色（§7 一句提示照抄）
PATHS = [  # id, 名, 提示, (glow, glow_mid, glow_core) or None, 色名
 ("tide", "水珠", "「朝早 6–9 點照顧，或者成日淋水」", ("#2FA0DC", "#6CD8F4", "#D8F8FF"), "水藍"),
 ("moon", "月眠", "「夜晚 9 點至凌晨 3 點陪佢」", ("#5562E0", "#8D98FF", "#DDE1FF"), "夜藍紫"),
 ("shroom", "菇傘", "「餵得最多」", ("#46B536", "#8AE466", "#DDFBC8"), "草綠"),
 ("crystal", "晶角", "「執得最乾淨」", ("#A24CDC", "#CD88FF", "#F2DEFF"), "晶紫"),
 ("ember", "火苗", "「玩得最多（包括小遊戲）」", ("#E2402C", "#FF7A4A", "#FFD2BC"), "火紅"),
 ("radiant", "燦光", "「樣樣都照顧好」", ("#EE8A14", "#FFB443", "#FFE6B4"), "金橙"),
 ("soft", "柔光", "「普通照顧」", ("#EC5A9A", "#FF9AC4", "#FFE2EF"), "粉紅"),
 ("dust", "微塵", "「好少理佢」", ("#8C8682", "#BAB4AD", "#ECE8E2"), "塵灰"),
 ("lumi", "螢絨", "隱藏：「？？？」", None, "唔顯示（保持原燈黃）"),
]
SLOTS = ("glow", "glow_mid", "glow_core")
BASE_PAL = json.load(open(os.path.join(OUT, "palette_base.json")))
hx = lambda h: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
BASE_RGB = {c["name"]: hx(c["hex"]) for c in BASE_PAL["colors"]}

# ============================================================ tell clips（絨跳，std 渲染路徑）
def ex_pts(pts):
    def f(cv, cx, cy, rx, ry):
        for (dx, dy, c) in pts: cv.put(cx + dx, cy + dy, c)
    return f
def drops(k):     # 水珠：甩水（水點向兩邊飛；每粒＝白高光＋drop＋drop_d 3px）
    D = [[], [(14, -8), (-14, -6), (15, -1)], [(-14, -9), (13, -4), (-16, -2)], [(15, -10), (-15, -6), (14, -1), (-12, -13)],
         [(16, -3), (-16, -2), (12, 3)], []][k]
    pts = []
    for (x, y) in D: pts += [(x, y - 1, "white"), (x, y, "drop"), (x + (1 if x > 0 else -1), y, "drop"), (x, y + 1, "drop_d")]
    return ex_pts(pts)
def zz(k):        # 月眠：z 字（zzz 色）
    Z = [(0, 0), (1, 0), (2, 0), (1, 1), (0, 2), (1, 2), (2, 2)]
    pos = [None, None, (11, -15), (12, -17), (13, -19), (12, -17)][k]
    if not pos: return ex_pts([])
    pts = [(pos[0] + x, pos[1] + y, "zzz") for x, y in Z]
    if k >= 4: pts += [(pos[0] - 3 + x // 2, pos[1] + 6 + y // 2, "zzz") for x, y in ((0, 0), (2, 0), (0, 2), (2, 2))]
    return ex_pts(pts)
def sparks(k):    # 晶角：身上閃點（執乾淨）
    S = [[], [(-6, -3)], [(5, -5), (-8, 2)], [(7, 1), (-3, -6)], [(-7, -2), (6, -4), (2, 4)], [(-6, -4), (6, -3)]][k]
    pts = []
    for (x, y) in S: pts += [(x, y, "white"), (x - 1, y, "cyan"), (x + 1, y, "cyan"), (x, y - 1, "cyan"), (x, y + 1, "cyan")]
    return ex_pts(pts)
def rays(k):      # 燦光：太陽光點圍身（唔近燈，唔入燈遮罩）
    R = [[], [(-15, -2), (15, -2)], [(-15, -6), (15, -6), (-13, 3), (13, 3)], [(-16, -8), (16, -8), (-14, 1), (14, 1)],
         [(-15, -4), (15, -4)], []][k]
    pts = []
    for (x, y) in R: pts += [(x, y, "cream4"), (x, y - 1, "egg_shade"), (x, y + 1, "egg_shade")]
    return ex_pts(pts)
def heart(k):     # 柔光：細心心
    if k not in (3, 4): return ex_pts([])
    oy = -16 - (k - 3)
    H = [(0, 0), (2, 0), (-1, 1), (0, 1), (1, 1), (2, 1), (3, 1), (0, 2), (1, 2), (2, 2), (1, 3)]
    return ex_pts([(11 + x, oy + y, "blush") for x, y in H] + [(11, oy, "white")])
def dustpuff(k):  # 微塵：打乞嗤噴塵（小塵雲）
    def cloud(x, y, big):
        P = [(0, 0, "cream1"), (1, 0, "cream2"), (0, 1, "cream2"), (1, 1, "cream0"), (-1, 1, "cream1")]
        if big: P += [(2, 1, "cream1"), (1, -1, "cream1"), (2, 0, "cream2"), (0, 2, "cream0"), (1, 2, "cream1")]
        return [(x + a, y + b, c) for a, b, c in P]
    P = [[], [], [], cloud(11, 0, False), cloud(12, -1, True) + cloud(-14, -10, False), cloud(14, -3, True) + [(-15, -12, "cream1")]][k]
    return ex_pts(P)
def firefly(k):   # 螢絨（隱藏）：細螢火點
    P = [[], [], [(12, -12, "leaf")], [(13, -14, "leaf"), (13, -15, "cyan")], [(11, -16, "leaf"), (11, -17, "cyan")], []][k]
    return ex_pts(P)

def TELLS(C):
    E = lambda c, i: list(C[c][i].get("extras", []))
    T = {}
    T["tell_tide"] = [dict(eyes="open", mouth="smile"),
                      dict(eyes="blink", mouth="flat", shear=1, sway=1, sx=1.02, extras=[drops(1)]),
                      dict(eyes="blink", mouth="flat", shear=-1, sway=-1, sx=1.02, extras=[drops(2)]),
                      dict(eyes="blink", mouth="flat", shear=1, sway=1, sx=1.02, extras=[drops(3)]),
                      dict(eyes="happy", mouth="open", lift=1, sy=1.04, bud=1.15, extras=[drops(4)]),
                      dict(eyes="happy", mouth="smile")]
    T["tell_moon"] = [dict(eyes="half", mouth="o", sy=1.04, sx=.98),
                      dict(eyes="sleep", mouth="yawn", sy=1.08, sx=.96, arms="upx", bud=1.2),
                      dict(eyes="sleep", mouth="yawn", sy=1.10, sx=.95, arms="upx", bud=1.25, sway=1, extras=[zz(2)]),
                      dict(eyes="half", mouth="o", sy=.97, sx=1.03, extras=[zz(3)]),
                      dict(eyes="blink", mouth="flat", sx=1.04, sy=.93, droop=1, bud=.8, fdy=1, extras=[zz(4)]),
                      dict(eyes="half", mouth="flat", sy=.97, bud=.9, extras=[zz(5)])]
    T["tell_shroom"] = [dict(eyes="wide", mouth="o", fdy=1, bud=1.15),
                        dict(eyes="shine", mouth="open", dx=1, shear=1, fdx=1, fdy=1),
                        dict(eyes="open", mouth="open", arms="eat", sy=1.03, sway=1, extras=E("eat", 1)),
                        dict(eyes="happy", mouth="flat", arms="eat", sx=1.05, sy=.97, extras=E("eat", 2)),
                        dict(eyes="happy", mouth="flat", arms="eat", sx=1.0, sy=1.0, sway=-1, extras=E("eat", 3)),
                        dict(eyes="happy", mouth="cat", sx=1.04, sy=.96)]
    T["tell_crystal"] = [dict(eyes="open", mouth="flat"),
                         dict(eyes="blink", mouth="flat", arms="side", shear=1, extras=[sparks(1)]),
                         dict(eyes="blink", mouth="flat", arms="side", shear=-1, extras=[sparks(2)]),
                         dict(eyes="open", mouth="smile", arms="side", shear=1, extras=[sparks(3)]),
                         dict(eyes="shine", mouth="smile", sx=.98, sy=1.03, bud=1.15, extras=[sparks(4)]),
                         dict(eyes="happy", mouth="smile", extras=[sparks(5)])]
    T["tell_ember"] = [dict(eyes="shine", mouth="open", sx=1.12, sy=.84),
                       dict(eyes="shine", mouth="open", arms="upx", lift=2, sx=.94, sy=1.07),
                       dict(eyes="happy", mouth="open", arms="upx", lift=3, sx=.98, sy=1.02, sway=1),
                       dict(eyes="happy", mouth="smile", sx=1.14, sy=.82),
                       dict(eyes="shine", mouth="open", arms="upx", lift=2, sx=.94, sy=1.07),
                       dict(eyes="happy", mouth="open", arms="upx", lift=3, sx=.98, sy=1.02, sway=-1),
                       dict(eyes="happy", mouth="smile", sx=1.14, sy=.82),
                       dict(eyes="happy", mouth="smile", bud=1.1)]
    T["tell_radiant"] = [dict(eyes="open", mouth="smile"),
                         dict(eyes="shine", mouth="open", arms="upx", sy=1.06, sx=.97, bud=1.2, extras=[rays(1)]),
                         dict(eyes="shine", mouth="open", arms="upx", sy=1.08, sx=.96, bud=1.25, lift=1, extras=[rays(2)]),
                         dict(eyes="happy", mouth="open", arms="upx", sy=1.08, sx=.96, bud=1.25, lift=1, extras=[rays(3)]),
                         dict(eyes="happy", mouth="smile", sy=1.02, bud=1.15, extras=[rays(4)]),
                         dict(eyes="happy", mouth="smile")]
    T["tell_soft"] = [dict(eyes="open", mouth="smile"),
                      dict(eyes="happy", mouth="cat", sx=1.04, sy=.96, dx=-1, shear=-1, fdx=-1, extras=E("emo_cuddly", 0)),
                      dict(eyes="happy", mouth="cat", sx=1.04, sy=.96, dx=1, shear=1, fdx=1, extras=E("emo_cuddly", 1)),
                      dict(eyes="happy", mouth="cat", sx=1.04, sy=.96, dx=-1, shear=-1, fdx=-1, extras=E("emo_cuddly", 0) + [heart(3)]),
                      dict(eyes="blink", mouth="smile", sx=1.02, sy=.98, extras=[heart(4)]),
                      dict(eyes="happy", mouth="smile")]
    T["tell_dust"] = [dict(eyes="half", mouth="flat", sy=.97, droop=1, bud=.75),
                      dict(eyes="half", mouth="o", sy=1.04, sx=.98, bud=.8, fdy=-1),
                      dict(eyes="blink", mouth="o", sy=1.07, sx=.96, bud=.8, fdy=-1),
                      dict(eyes="blink", mouth="open", sx=1.1, sy=.88, dx=1, shear=1, fdx=1, extras=[dustpuff(3)]),
                      dict(eyes="half", mouth="flat", sx=1.04, sy=.95, droop=1, bud=.7, extras=[dustpuff(4)]),
                      dict(eyes="half", mouth="frown", sy=.96, droop=1, bud=.7, extras=[dustpuff(5)])]
    T["tell_lumi"] = [dict(eyes="open", mouth="smile", bud=.5, fdy=-1),
                      dict(eyes="shine", mouth="o", bud=1.25, fdy=-1),
                      dict(eyes="open", mouth="o", bud=.5, fdy=-1, extras=[firefly(2)]),
                      dict(eyes="shine", mouth="open", bud=1.25, fdy=-1, extras=[firefly(3)]),
                      dict(eyes="happy", mouth="smile", bud=1.1, extras=[firefly(4)]),
                      dict(eyes="happy", mouth="smile")]
    return T
TELL_FPS = {"tell_tide": 8, "tell_moon": 6, "tell_shroom": 8, "tell_crystal": 8, "tell_ember": 10, "tell_radiant": 6,
            "tell_soft": 6, "tell_dust": 6, "tell_lumi": 6}
TELL_NOTE = {"tell_tide": "甩水：左右擰身甩走頭頂水點（朝早露水／淋水），甩完笑。",
             "tell_moon": "打喊路：伸手打大喊路，頭頂飄 z，點一點頭似瞓唔瞓（月眠）。",
             "tell_shroom": "見嘢就話食得：望地下一嘢、撲埋去扮咬落口、咀嚼完滿足 ω。",
             "tell_crystal": "執乾淨：雙手掃身，身上逐粒閃光點，執完挺胸（晶角）。",
             "tell_ember": "原地跳：連跳兩下（壓扁→彈起），好興奮（火苗）。",
             "tell_radiant": "曬太陽伸懶腰：雙手舉高，四圍閃太陽光點（燦光：樣樣都好）。",
             "tell_soft": "軟綿綿：左右挨身、合眼笑 ω、飄細心心（柔光）。",
             "tell_dust": "冇人理：嘆氣垂耳、打乞嗤噴啲塵（微塵）。",
             "tell_lumi": "（隱藏）燈泡一閃一閃、望上面，有粒細螢火飛過（螢絨；UI 唔顯示路線）。"}
ORDER_T = [f"tell_{p[0]}" for p in PATHS]
for c in ORDER_T: M.META[c] = (TELL_FPS[c], False, 0, 3, True)

def load_idx(path):
    a = np.array(Image.open(path).convert("RGBA")); out = np.zeros(a.shape[:2], np.uint8)
    for i, c in enumerate(A.RGB):
        if i: out[(a[..., 3] == 255) & (a[..., :3] == c).all(-1)] = i
    assert ((a[..., 3] == 255) == (out > 0)).all(), path
    return out

def build_tells():
    A.CUR[0] = FORM; C = M.clips(FORM); T = TELLS(C); res = {}
    for clip in ORDER_T:
        c = dict(noface=[], full=[], overlay=[], anchors=[], new=False)
        for k, p in enumerate(T[clip]):
            p = dict(p); p["_k"] = k; p.setdefault("twinkle", k)
            p = M.render_fit(FORM, p, f"{clip}_{k + 1:02d}")
            full = M.render(FORM, p); body = M.render(FORM, L.noface_params(p))
            an = A.evo_anchors(FORM, p, True)
            eo = p.get("eyes", "open"); mo = p.get("mouth", "smile")
            an["face"] = dict(eyes=L.OLD_EYE.get(eo, eo), gaze="C", mouth=L.OLD_MOUTH.get(mo, mo), src=f"{eo}/{mo}")
            ov = np.where(full != body, full, 0).astype(np.uint8)
            assert not A.touches(full), (clip, k)
            c["noface"].append(body); c["full"].append(full); c["overlay"].append(ov); c["anchors"].append(an)
        res[clip] = c
    A.CUR[0] = None
    return res

def write_tells(T):
    for clip, c in T.items():
        for k in range(len(c["full"])):
            n = f"{clip}_{k + 1:02d}"
            A.to_img(c["full"][k]).save(os.path.join(HD, "frames", n + ".png"))
            A.to_img(c["noface"][k]).save(os.path.join(HD, "layers", n + "_noface.png"))
            A.to_img(c["overlay"][k]).save(os.path.join(HD, "layers", n + "_faceov.png"))
            A.emis_img(c["full"][k]).save(os.path.join(HD, "emissive", n + "_emissive.png"))
            A.emis_img(c["noface"][k]).save(os.path.join(HD, "emissive", n + "_noface_emissive.png"))
    p = os.path.join(HD, f"face_anchors_{FORM}.json"); fa = json.load(open(p))
    for clip, c in T.items(): fa["anchors"][clip] = c["anchors"]
    fa["tellClips"] = ORDER_T
    fa["tellNote"] = "tell_<路線>＝判定前 12h 預告小動作（§7 路線清晰化），由絨跳播；錨點同 std clip（bulb＝燈芽中心）"
    with open(p, "w") as fh:
        head = {k_: v for k_, v in fa.items() if k_ != "anchors"}
        fh.write(json.dumps(head, ensure_ascii=False)[:-1] + ',\n "anchors":{\n')
        fh.write(',\n'.join('  ' + json.dumps(cl) + ':[\n' + ',\n'.join('   ' + json.dumps(a, ensure_ascii=False, separators=(",", ":")) for a in lst) + ']'
                            for cl, lst in fa["anchors"].items()) + '}}\n')
    return fa

def load_existing():
    fa = json.load(open(os.path.join(HD, f"face_anchors_{FORM}.json")))
    CL = json.load(open(os.path.join(MOT, "CLIPS.json"))); order = list(CL["forms"][FORM]["clips"])
    clips = {}
    for clip in order:
        n = len(fa["anchors"][clip]); c = dict(full=[], noface=[], anchors=fa["anchors"][clip])
        for k in range(n):
            c["full"].append(load_idx(os.path.join(HD, "frames", f"{clip}_{k + 1:02d}.png")))
            c["noface"].append(load_idx(os.path.join(HD, "layers", f"{clip}_{k + 1:02d}_noface.png")))
        clips[clip] = c
    kit = {}
    aj = json.load(open(os.path.join(OUT, f"atlas_{FORM}.json")))
    for kp in sorted(os.listdir(os.path.join(HD, "kit"))):
        nm = kp[:-4]; pv = aj["frames"][nm]["pivotPx"]; kit[nm] = (load_idx(os.path.join(HD, "kit", kp)), (pv["x"], pv["y"]))
    return order, clips, kit

# ============================================================ bulb mask / recolour
def bulb_mask(a, an):
    """燈泡像素（glow/glow_mid/glow_core，離 bulb 錨點 ≤3.6px）→ slot 0/1/2，其餘 -1"""
    S = a.shape[0]; yy, xx = np.mgrid[:S, :S]; out = -np.ones(a.shape, np.int8)
    if not an or "bulb" not in an: return out
    bx, by = an["bulb"]; near = np.hypot(xx - bx, yy - by) <= 3.6
    for i, s in enumerate(SLOTS): out[near & (a == IDX[s])] = i
    return out
def kit_mask(a):
    out = -np.ones(a.shape, np.int8)
    for i, s in enumerate(SLOTS): out[a == IDX[s]] = i
    return out
def recolor(img_rgba, mask, ramp):
    o = img_rgba.copy()
    for i in range(3): o[mask == i, :3] = hx(ramp[i])
    return o
def mask_img(mask):
    o = np.zeros(mask.shape + (4,), np.uint8)
    for i in range(3): o[mask == i, i] = 255; o[mask == i, 3] = 255
    return o

def write_route_atlases(order_all, clips, kit):
    aj = json.load(open(os.path.join(OUT, f"atlas_{FORM}.json"))); W, H = aj["meta"]["size"]["w"], aj["meta"]["size"]["h"]
    base = np.array(Image.open(os.path.join(OUT, f"atlas_{FORM}.png")).convert("RGBA"))
    masks = {}
    for clip in order_all:
        c = clips[clip]
        for k in range(len(c["full"])):
            masks[f"{clip}_{k + 1:02d}"] = bulb_mask(c["full"][k], c["anchors"][k])
            masks[f"{clip}_noface_{k + 1:02d}"] = bulb_mask(c["noface"][k], c["anchors"][k])
    for nm, (a, pv) in kit.items(): masks[nm] = kit_mask(a) if nm.startswith("bulb_") else -np.ones(a.shape, np.int8)
    MA = -np.ones((H, W), np.int8)
    for nm, r in aj["frames"].items():
        x, y, w, h = r["frame"]["x"], r["frame"]["y"], r["frame"]["w"], r["frame"]["h"]; m = masks[nm]
        MA[y:y + h, x:x + w] = m
        MA[y - 1, x:x + w] = m[0]; MA[y + h, x:x + w] = m[-1]; MA[y:y + h, x - 1] = m[:, 0]; MA[y:y + h, x + w] = m[:, -1]
    Image.fromarray(mask_img(MA), "RGBA").save(os.path.join(RC, f"atlas_{FORM}_bulbmask.png"))
    nfr = sum(1 for k, m in masks.items() if not k.startswith(("eyes_", "mouth_", "bulb_")) and (m >= 0).any())
    tot = sum(1 for k in masks if not k.startswith(("eyes_", "mouth_", "bulb_")))
    for pid, nm, hint, ramp, cn in PATHS:
        if not ramp: continue
        Image.fromarray(recolor(base, MA, ramp), "RGBA").save(os.path.join(RC, f"atlas_{FORM}_bulb_{pid}.png"))
        pal = json.loads(json.dumps(BASE_PAL))
        for c in pal["colors"]:
            if c["name"] in SLOTS: c["hex"] = ramp[SLOTS.index(c["name"])]
        pal["route"] = pid; pal["routeName"] = nm
        pal["note"] = f"絨跳燈色換做「{nm}」({cn})：只換 glow/glow_mid/glow_core 3 色，只用喺燈泡像素（atlas_{FORM}_bulbmask.png），其他 28 色同 palette_base.json 一樣"
        json.dump(pal, open(os.path.join(RC, f"palette_{FORM}_{pid}.json"), "w"), indent=1, ensure_ascii=False)
    return nfr, tot

def write_route_palette():
    spec = {"version": 1, "form": FORM, "spec": "docs-gdd/pet-template-v1.md §7 路線清晰化（跳跳期頭頂燈泡慢慢轉做而家領先路線嘅顏色；螢絨唔顯示）",
            "slots": list(SLOTS), "base": {s: BASE_PAL["colors"][[c["name"] for c in BASE_PAL["colors"]].index(s)]["hex"] for s in SLOTS},
            "baseNote": "原燈黃＝未有領先路線／螢絨（隱藏）",
            "mask": f"route_clarity/atlas_{FORM}_bulbmask.png（同 atlas_{FORM}.png layout；R＝glow、G＝glow_mid、B＝glow_core；alpha 255＝燈像素；連 extrude）",
            "tint": "每個燈像素：color = lerp(base[slot], path[slot], t)；t＝領先程度 0→1（遊戲決定，建議跳跳期期內按領先分數慢慢升，判定時＝1）；唔改 alpha；emissive 遮罩照用 atlas_evo_hop_emissive.png（燈 glow_mid/glow_core 位置唔變）",
            "noShader": f"冇 shader：t≥0.5 時直接換 route_clarity/atlas_{FORM}_bulb_<id>.png（同 layout，只燈像素唔同）",
            "paths": {}}
    for pid, nm, hint, ramp, cn in PATHS:
        spec["paths"][pid] = {"name": nm, "hint": hint, "colorName": cn, "hidden": ramp is None,
                              "ramp": dict(zip(SLOTS, ramp)) if ramp else None,
                              "atlas": f"route_clarity/atlas_{FORM}_bulb_{pid}.png" if ramp else None,
                              "palette": f"route_clarity/palette_{FORM}_{pid}.json" if ramp else None}
    json.dump(spec, open(os.path.join(RC, "palette_route_bulbs.json"), "w"), indent=1, ensure_ascii=False)
    return spec

# ============================================================ silhouettes
SIL_COL = (59, 42, 62)   # outline #3B2A3E
def silhouette(form):
    a = np.array(Image.open(os.path.join(OUT, form, "frames", "idle_01.png")).convert("RGBA"))[..., 3] > 0
    from scipy import ndimage as ndi
    lab, n = ndi.label(a, structure=np.ones((3, 3), int)); sz = ndi.sum(a, lab, range(1, n + 1))
    keep = np.isin(lab, [i + 1 for i, s in enumerate(sz) if s >= 25])
    keep = ndi.binary_fill_holes(keep)
    o = np.zeros(a.shape + (4,), np.uint8); o[keep] = SIL_COL + (255,)
    return o, int(n), int(keep.sum())
def write_silhouettes():
    d = os.path.join(RC, "silhouette"); os.makedirs(d, exist_ok=True); col = {"version": 1, "spec": "§7 圖鑑：未解鎖顯示剪影＋一句提示；解鎖後顯示名＋圖",
        "silhouetteColor": "#3B2A3E（outline 色；實心，alpha 0/255）", "source": "靜光 48（完全體）idle_01，去走 <25px 嘅 aura／閃點碎粒、填實內洞", "size": 48, "paths": {}}
    for pid, nm, hint, ramp, cn in PATHS:
        form = f"evo_still_{pid}"; o, n, px = silhouette(form)
        fn = f"sil_{pid}_48.png"; Image.fromarray(o, "RGBA").save(os.path.join(d, fn))
        col["paths"][pid] = {"name": nm, "hint": hint, "hidden": ramp is None, "lockedName": "？？？", "silhouette": f"route_clarity/silhouette/{fn}",
                             "unlocked": {"form": form, "atlas": f"atlas_{form}.png", "clip": "idle"}, "pixels": px}
    json.dump(col, open(os.path.join(RC, "collection_route.json"), "w"), indent=1, ensure_ascii=False)
    return col

# ============================================================ preview
def contact(T, spec, col):
    Z = 4; CW = 38 * Z + 6; LW = 210; ncol = 8
    H = 70 + len(PATHS) * (CW + 26) + 30 + 48 * 4 + 60
    W = LW + ncol * CW + 30 + 48 * Z + 20
    cs = Image.new("RGBA", (W, H), A.BG); dr = ImageDraw.Draw(cs); ft = A.font
    dr.text((8, 8), "團絨 evo6 batch G — §7 路線清晰化：絨跳燈色（8 路，螢絨唔顯示）＋判定前預告 tell_<路線>（絨跳）＋圖鑑剪影（靜光 48）", fill=(255, 248, 224, 255), font=ft(15))
    dr.text((8, 32), "每行：路線名／一句提示／燈色 swatch（glow／mid／core）→ 預告幀（燈已換做該路色，示範判定時 t=1）→ 右邊＝未解鎖剪影＋解鎖後靜光", fill=(200, 196, 230, 255), font=ft(13))
    for r, (pid, nm, hint, ramp, cn) in enumerate(PATHS):
        y0 = 62 + r * (CW + 26); clip = f"tell_{pid}"; c = T[clip]
        dr.text((8, y0 + 6), f"{nm} {pid}", fill=(255, 248, 224, 255), font=ft(17))
        dr.text((8, y0 + 30), hint, fill=(200, 196, 230, 255), font=ft(11))
        dr.text((8, y0 + 48), cn, fill=(200, 196, 230, 255), font=ft(12))
        rr = ramp or tuple(spec["base"][s] for s in SLOTS)
        for i, h in enumerate(rr): dr.rectangle((8 + i * 34, y0 + 70, 8 + i * 34 + 30, y0 + 100), fill=hx(h) + (255,), outline=(30, 20, 30, 255))
        if ramp: dr.text((8, y0 + 104), " ".join(rr), fill=(200, 196, 230, 255), font=ft(10))
        for k in range(min(ncol, len(c["full"]))):
            a = c["full"][k]; img = np.array(A.to_img(a))
            if ramp: img = recolor(img, bulb_mask(a, c["anchors"][k]), ramp)
            x0 = LW + k * CW
            cs.alpha_composite(Image.fromarray(img).resize((38 * Z, 38 * Z), Image.NEAREST), (x0, y0))
            dr.text((x0 + 4, y0 + 38 * Z + 2), f"{clip}_{k + 1:02d}", fill=(200, 196, 230, 255), font=ft(10))
        xs = LW + ncol * CW + 20
        sil = Image.open(os.path.join(RC, "silhouette", f"sil_{pid}_48.png")).resize((48 * 2, 48 * 2), Image.NEAREST)
        bg = Image.new("RGBA", (96, 96), (210, 204, 226, 255)); bg.alpha_composite(sil); cs.alpha_composite(bg, (xs, y0 + 4))
        st = Image.open(os.path.join(OUT, f"evo_still_{pid}", "frames", "idle_01.png")).convert("RGBA").resize((96, 96), Image.NEAREST)
        cs.alpha_composite(st, (xs + 100, y0 + 4))
        dr.text((xs, y0 + 104), "？？？ → " + nm, fill=(200, 196, 230, 255), font=ft(11))
    # 燈色一覽：絨跳 idle_01 × 9 色
    y0 = 62 + len(PATHS) * (CW + 26) + 10
    dr.text((8, y0), "絨跳 idle_01 燈色一覽（原 → 8 路）", fill=(255, 248, 224, 255), font=ft(15))
    a = load_idx(os.path.join(HD, "frames", "idle_01.png")); an = json.load(open(os.path.join(HD, f"face_anchors_{FORM}.json")))["anchors"]["idle"][0]
    mk = bulb_mask(a, an); base_img = np.array(A.to_img(a))
    for i, (pid, nm, hint, ramp, cn) in enumerate([("base", "原燈黃", "", None, "")] + [p for p in PATHS if p[3]]):
        img = recolor(base_img, mk, ramp) if ramp else base_img
        x0 = 8 + i * (38 * 4 + 8)
        cs.alpha_composite(Image.fromarray(img).resize((38 * 4, 38 * 4), Image.NEAREST), (x0, y0 + 24))
        dr.text((x0 + 4, y0 + 24 + 38 * 4), nm, fill=(255, 248, 224, 255), font=ft(13))
    p = os.path.join(PRV, "evo6_batchG_route_clarity_4x.png"); cs = cs.crop((0, 0, W, y0 + 24 + 38 * 4 + 24)); cs.save(p); return p

# ============================================================ docs
def update_docs(T, ainfo, spec, col, nfr, tot):
    p = os.path.join(MOT, "CLIPS.json"); D = json.load(open(p, encoding="utf-8"))
    fe = D["forms"][FORM]; W, H, n = ainfo
    fe["atlasSize"] = [W, H]; fe["atlasPieces"] = n
    fe["tells"] = ORDER_T
    fe["routeBulb"] = {"spec": "route_clarity/palette_route_bulbs.json", "mask": f"route_clarity/atlas_{FORM}_bulbmask.png",
                       "atlases": {pid: f"../evo6/route_clarity/atlas_{FORM}_bulb_{pid}.png" for pid, *_r in PATHS if _r[2]}}
    tc = {}
    for clip in ORDER_T:
        pid = clip[5:]; nm = next(x[1] for x in PATHS if x[0] == pid); c = T[clip]
        tc[clip] = {"name": clip, "status": "已交付（evo6 batch G 路線清晰化）", "category": "路線預告", "route": pid, "routeName": nm,
                    "frames": len(c["full"]), "fps": TELL_FPS[clip], "loop": False, "priority": 3, "interruptible": True,
                    "trigger": "跳跳期：判定前 12h 內播一次「而家領先路線」嘅預告（§7）；螢絨（隱藏）領先時都照播 tell_lumi，但 UI 唔講路線",
                    "cooldown_s": 0, "next": "idle", "notes": TELL_NOTE[clip], "forms": [FORM],
                    "anchors": {FORM: c["anchors"]},
                    FORM: {"frames": len(c["full"]), "full": f"../evo6/{FORM}/frames/{clip}_NN.png", "noface": f"../evo6/{FORM}/layers/{clip}_NN_noface.png",
                           "faceov": f"../evo6/{FORM}/layers/{clip}_NN_faceov.png", "emissive": f"../evo6/{FORM}/emissive/{clip}_NN_emissive.png",
                           "atlasClip": clip, "nofaceClip": f"{clip}_noface", "atlas": f"../evo6/atlas_{FORM}.json"}}
    D["evo6G"] = {"tool": "tools/build_evo6_routeG.py", "validator": "tools/validate_route_clarity.py ＋ tools/validate_evo6_anim.py",
                  "spec": "docs-gdd/pet-template-v1.md §7 路線清晰化（Kurt 2026-11-01 01:03）",
                  "note": "tell clip 放喺 evo6G.tellClips（唔入頂層 clips[]，因為只得絨跳一個形態有）；forms.evo_hop.tells 列出；atlas_evo_hop 已包埋",
                  "tellClips": tc, "routeBulb": "../evo6/route_clarity/palette_route_bulbs.json", "collection": "../evo6/route_clarity/collection_route.json",
                  "bulbFramesWithLamp": f"{nfr}/{tot}",
                  "paths": {pid: {"name": nm, "hint": hint, "colorName": cn, "ramp": dict(zip(SLOTS, ramp)) if ramp else None} for pid, nm, hint, ramp, cn in PATHS},
                  "preview": "../preview/evo6/evo6_batchG_route_clarity_4x.png"}
    BC.atomic_write(p, json.dumps(D, indent=1, ensure_ascii=False))
    mp = os.path.join(MOT, "CLIPS.md"); md = open(mp, encoding="utf-8").read()
    a_, b_ = "<!-- EVO6G-START -->", "<!-- EVO6G-END -->"
    if a_ in md: md = md[:md.index(a_)].rstrip() + "\n\n" + md[md.index(b_) + len(b_):].lstrip()
    rows = "\n".join(f"| {nm} `{pid}` | {hint} | {cn} | " + (" / ".join(ramp) if ramp else "—") + f" | `tell_{pid}` {len(T['tell_' + pid]['full'])} 幀 {TELL_FPS['tell_' + pid]}fps：{TELL_NOTE['tell_' + pid]} |"
                     for pid, nm, hint, ramp, cn in PATHS)
    sec = (f"{a_}\n## 進化 6 階 batch G — §7 路線清晰化\n"
           "- 燈色：絨跳燈泡跟領先路線慢慢轉色（`../evo6/route_clarity/palette_route_bulbs.json`：lerp(base, path, t)；遮罩 `atlas_evo_hop_bulbmask.png`；冇 shader 版 `atlas_evo_hop_bulb_<id>.png`）。螢絨唔顯示。\n"
           "- 預告：`tell_<id>` 由絨跳播（判定前 12h 一次），std 標準：frames／layers／emissive／anchors（bulb）＋ atlas_evo_hop。定義喺 CLIPS.json `evo6G.tellClips`（唔入頂層 clips[]）。\n"
           "- 圖鑑：`../evo6/route_clarity/silhouette/sil_<id>_48.png`（靜光 48 實心剪影 #3B2A3E）＋ `collection_route.json` 一句提示。\n\n"
           "| 路線 | 提示 | 燈色 | glow / mid / core | 預告 |\n|---|---|---|---|---|\n" + rows + f"\n{b_}\n")
    anchor = next((m for m in ("<!-- EVO6F-END -->", "<!-- EVO6E-END -->") if m in md), None)
    if anchor: i = md.index(anchor) + len(anchor); md = md[:i] + "\n\n" + sec + md[i:]
    else: md = md.rstrip() + "\n\n" + sec
    BC.atomic_write(mp, md)
    lp = os.path.join(ROOT, "ASSET_LOG.md"); lg = open(lp, encoding="utf-8").read()
    a_, b_ = "<!-- EVO6G-LOG-START -->", "<!-- EVO6G-LOG-END -->"
    if a_ in lg: lg = lg[:lg.index(a_)].rstrip() + "\n\n" + lg[lg.index(b_) + len(b_):].lstrip()
    ent = (f"{a_}\n## 2026-11-01 — 團絨 evo6 batch G（§7 路線清晰化）\n"
           f"- 絨跳燈色 8 路（螢絨唔顯示）：`sprites/tuanrong/evo6/route_clarity/palette_route_bulbs.json`＋`palette_evo_hop_<id>.json` ×8＋`atlas_evo_hop_bulbmask.png`＋`atlas_evo_hop_bulb_<id>.png` ×8；現有 evo_hop 散檔像素冇改。\n"
           f"- 預告 tell_<id> ×9（絨跳）：{sum(len(c['full']) for c in T.values())} 幀；atlas_evo_hop 重排（{W}×{H}，{n} 塊）。\n"
           "- 圖鑑剪影 ×9：`route_clarity/silhouette/sil_<id>_48.png`＋`collection_route.json`。\n"
           "- 預覽 `sprites/tuanrong/preview/evo6/evo6_batchG_route_clarity_4x.png`；工具 `tools/build_evo6_routeG.py`；驗證 `tools/validate_route_clarity.py`；備份 `_backups/pre_evo6_route_clarity_20261101/`。Pillow/numpy 程式繪製，無 AI。\n{b_}\n")
    BC.atomic_write(lp, lg.rstrip() + "\n\n" + ent)

def main():
    order, clips, kit = load_existing()
    T = build_tells(); write_tells(T)
    allc = dict(clips)
    for k_, c in T.items(): allc[k_] = c
    order_all = order + ORDER_T
    ainfo = A.write_atlas(FORM, order_all, allc, kit)
    nfr, tot = write_route_atlases(order_all, allc, kit)
    spec = write_route_palette(); col = write_silhouettes()
    pv = contact(T, spec, col)
    if "--no-docs" not in sys.argv: update_docs(T, ainfo, spec, col, nfr, tot)
    print("tells", {k: len(v["full"]) for k, v in T.items()}, "atlas", ainfo, "bulb frames", nfr, "/", tot, "preview", pv)
if __name__ == "__main__": main()
