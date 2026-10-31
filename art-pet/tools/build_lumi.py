#!/usr/bin/env python3
"""build_lumi.py — 團絨隱藏稀有成年形態「螢絨」(lumi) 動畫（MVP 12 clip／46 幀 + picked_up + fall_asleep/sleep_loop/wake）。
Pillow + numpy 程式逐像素繪製，原創，無 AI。round_s 骨架：直接重用燦光 (radiant) 嘅 clip 姿勢參數
（build_tuanrong_motion.clips / build_tuanrong_liveliness.new_clips），只換外觀層（build_lumi_concept.render_lumi）。
64×64、pivot (32,61)、lumi 31 色、alpha 0/255、無 AA、向右。每幀 emissive 遮罩（白＝發光）。
唔改／唔覆蓋 motion/、liveliness/ 現有檔（只喺 CLIPS.json／CLIPS.md 加 lumi 段，冪等）。
輸出：sprites/tuanrong/atlas_lumi.png/.json、atlas_lumi_emissive.png、sprites/tuanrong/lumi/…
用法：python3 build_lumi.py
"""
import json, math, os, shutil, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_tuanrong as bt
import build_tuanrong_motion as M
import build_tuanrong_liveliness as L
import build_lumi_concept as LC          # lumi palette swap (mutates bt.IDX in place) + render_lumi + h4_panel
from build_tuanrong import FORMS, IDX

FORM = "lumi"
TR = bt.OUT                               # sprites/tuanrong
OUT = os.path.join(TR, "lumi")
MOT = M.OUT
BG = (92, 88, 128, 255)
RGB = LC.RGB
EMIS = sorted(LC.EMIS)

# ---- dispatch: bt.render_pet("lumi", p) -> lumi appearance (all motion/liveliness pose code reused unchanged)
_orig_render_pet = bt.render_pet
def _render_pet(form, p):
    return LC.render_lumi(p) if form == FORM else _orig_render_pet(form, p)
bt.render_pet = _render_pet
M.ANCH[FORM] = dict(M.ANCH["radiant"])     # head_r / pot / sun anchors = radiant (same skeleton)

MVP = ["idle", "blink", "walk", "play", "eat", "sleep_loop", "emo_happy", "emo_hungry", "emo_sleepy", "celebrate", "droop", "sick"]
EXTRA = ["picked_up", "fall_asleep", "wake"]
ORDER = MVP[:5] + ["fall_asleep", "sleep_loop", "wake"] + MVP[6:] + ["picked_up"]
STD23_REMAIN = [c for c in M.ORDER if c not in ORDER]

def to_img(a):
    rgba = np.zeros(a.shape + (4,), np.uint8)
    for i, c in enumerate(RGB):
        if i: rgba[a == i, :3] = c; rgba[a == i, 3] = 255
    return Image.fromarray(rgba, "RGBA")

def emis_arr(a): return np.isin(a, EMIS)
def emis_img(a):
    o = np.zeros(a.shape + (4,), np.uint8); o[emis_arr(a)] = (255, 255, 255, 255)
    return Image.fromarray(o, "RGBA")

# ---------------------------------------------------------------- anchors
def lumi_anchors(p, face_visible=True):
    an = L.anchors(FORM, p, face_visible)
    f, S, big, rx, ry, cx, cy = L._geo(FORM, p)
    for key in ("eyeL", "eyeR", "mouth"):            # face drawn FACE_DX right of skeleton centre
        x, y = an[key]; an[key] = [x + LC.FACE_DX, y]
    ants = LC.antenna_pts(p, cx, cy, ry)
    x, y = ants[1][-1]; bx, by = int(round(x)), int(round(y - 1))     # bulb = 前觸角燈頭（glow point）
    an["bulb"] = [bx + L._shear_x(FORM, p, by), by]
    x, y = ants[0][-1]; bx, by = int(round(x)), int(round(y - 1))
    an["bulb2"] = [bx + L._shear_x(FORM, p, by), by]                  # 後觸角燈頭（附加）
    tx, ty = LC.tail_center(cx, cy, rx, ry); tx, ty = int(round(tx - 2)), int(round(ty))
    an["tail"] = [tx + L._shear_x(FORM, p, ty), ty]                   # 尾燈中心（引擎 glow 用）
    return an

def pend_more(p, an):
    """pend_anchors only shifts the std keys; also shift lumi extras"""
    gx, gy = L.grab_point(FORM, p); amt = p.get("pend", 0); S = 64; ref = (S - 3) - gy
    for key in ("bulb2", "tail"):
        x, y = an[key]; an[key] = [x + L._pend_dx(y, gy, ref, amt), y]
    return an

# ---------------------------------------------------------------- kit (existing 64px face kit; eye highlight -> fly_core)
def build_kit():
    kit = L.build_kit("radiant")                     # 64px kit shapes identical to radiant/soft
    out = {}
    for name, (a, piv) in kit.items():
        if name.startswith("bulb_"): continue
        b = a.copy()
        if name.startswith("eyes_"): b[a == IDX["cream4"]] = IDX["fly_core"]
        out[name] = (b, piv)
    # bulb = antenna glow tip: base ring (fly) + glow core (white/cream4 -> engine tint)
    base, glow = {}, {}
    for y in range(-3, 4):
        for x in range(-3, 4):
            d = math.hypot(x - 0.4, y + 0.4)
            if d <= 1.0: glow[(x, y)] = "white"
            elif d <= 1.6: glow[(x, y)] = "cream4"
            elif d <= 2.5: base[(x, y)] = "fly"
    bb = L.bbox_of([base, glow])
    out["bulb_base"] = L.piece_arr(base, bb); out["bulb_glow"] = L.piece_arr(glow, bb)
    return out

# ---------------------------------------------------------------- build frames
def build():
    L.init_head_k() if not L.HEAD_K else None
    if FORM not in L.HEAD_K: L.HEAD_K[FORM] = L.HEAD_K["radiant"]
    kit = build_kit()
    C = M.clips(FORM)
    NC, NFACE, NVIS = L.new_clips(FORM)
    clips = {}
    for clip in ORDER:
        new = clip in NC
        src = NC[clip] if new else C[clip]
        c = dict(noface=[], full=[], overlay=[], anchors=[], new=new)
        for k, p in enumerate(src):
            p = dict(p); p["_k"] = k
            if clip not in ("idle", "eat", "celebrate", "sick"): p = M.render_fit(FORM, p, f"{clip}_{k + 1:02d}")
            if new:
                body = L.body_render(FORM, p)
                an = lumi_anchors(p, NVIS.get(clip, [True] * 99)[k])
                if clip in L.PIVOT_OVERRIDE: an = pend_more(p, L.pend_anchors(FORM, p, an))
                face = NFACE[clip][k]; an["face"] = dict(face) if face else None
                full = L.compose_face(body, an, face, kit)
            else:
                full = M.render(FORM, p); body = M.render(FORM, L.noface_params(p))
                an = lumi_anchors(p, True)
                eo = p.get("eyes", "open"); mo = p.get("mouth", "smile")
                an["face"] = dict(eyes=L.OLD_EYE.get(eo, eo), gaze="C", mouth=L.OLD_MOUTH.get(mo, mo), src=f"{eo}/{mo}")
            ov = np.where(full != body, full, 0).astype(np.uint8)
            c["noface"].append(body); c["full"].append(full); c["overlay"].append(ov); c["anchors"].append(an)
        clips[clip] = c
    return clips, kit

def meta(clip):
    if clip in L.NEW_META:
        fps, loop, lf, pr, intr = L.NEW_META[clip][:5]
    else:
        fps, loop, lf, pr, intr = M.META[clip]
    return fps, loop, lf

# ---------------------------------------------------------------- atlas (sprite + emissive, same layout)
def write_atlas(clips, kit):
    piv = (32, 61); items = []; anims = {}
    for clip in ORDER:
        c = clips[clip]; fps, loop, lf = meta(clip)
        pov = L.PIVOT_OVERRIDE.get(clip)
        pv = (lambda k, c=c, pov=pov: tuple(c["anchors"][k][pov])) if pov else (lambda k: piv)
        extra = {"pivot": pov} if pov else {}
        if loop and lf: extra["loopFrom"] = lf
        ff = [f"{clip}_{k + 1:02d}" for k in range(len(c["full"]))]
        nf = [f"{clip}_noface_{k + 1:02d}" for k in range(len(c["full"]))]
        for k in range(len(ff)):
            items.append((ff[k], c["full"][k], pv(k))); items.append((nf[k], c["noface"][k], pv(k)))
        anims[clip] = {"frames": ff, "fps": fps, "loop": loop, **extra}
        anims[clip + "_noface"] = {"frames": nf, "fps": fps, "loop": loop, **extra}
    for name, (a, pv) in kit.items(): items.append((name, a, pv))
    pages = L.pack_pages(items)
    assert len(pages) == 1, "atlas_lumi must fit one 1024² page"
    W, H, pos = pages[0]
    lut = {n: (a, pv) for n, a, pv in items}
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); emi = Image.new("RGBA", (W, H), (0, 0, 0, 0)); jf = {}
    def paste_ex(dst, im, x, y, w, h):
        e = np.array(im); dst.paste(im, (x, y))
        dst.paste(Image.fromarray(e[:1], "RGBA"), (x, y - 1)); dst.paste(Image.fromarray(e[-1:], "RGBA"), (x, y + h))
        dst.paste(Image.fromarray(e[:, :1], "RGBA"), (x - 1, y)); dst.paste(Image.fromarray(e[:, -1:], "RGBA"), (x + w, y))
    for name, (x, y, w, h) in pos.items():
        a, pv = lut[name]
        paste_ex(img, to_img(a), x, y, w, h); paste_ex(emi, emis_img(a), x, y, w, h)
        jf[name] = {"frame": {"x": x, "y": y, "w": w, "h": h}, "rotated": False, "trimmed": False,
                    "spriteSourceSize": {"x": 0, "y": 0, "w": w, "h": h}, "sourceSize": {"w": w, "h": h},
                    "pivot": {"x": round(pv[0] / w, 4), "y": round(pv[1] / h, 4)}, "pivotPx": {"x": int(pv[0]), "y": int(pv[1])}}
    img.save(os.path.join(TR, "atlas_lumi.png")); emi.save(os.path.join(TR, "atlas_lumi_emissive.png"))
    m = {"image": "atlas_lumi.png", "emissive": "atlas_lumi_emissive.png", "size": {"w": W, "h": H}, "scale": 1, "format": "RGBA8888",
         "padding": 2, "extrude": 1, "form": FORM, "name": "螢絨", "rarity": "rare", "skeleton": "round_s", "frameSize": 64, "pivotPx": [32, 61],
         "palette": "lumi/palette_lumi.json",
         "pivotRule": "body frames bottom-center (32,61)；picked_up* pivotPx = anchors.grab（頭頂拎點）；kit pieces pivotPx = anchor point",
         "note": "螢絨：<clip>_NN 完整幀、<clip>_noface_NN 無臉身體、五官 eyes_*/mouth_*（64px kit，眼高光＝fly_core）、bulb_base/bulb_glow（觸角燈頭）。atlas_lumi_emissive.png 同 layout，白＝發光。"}
    json.dump({"frames": jf, "animations": anims, "meta": m}, open(os.path.join(TR, "atlas_lumi.json"), "w"), indent=1, ensure_ascii=False)
    return W, H, len(items)

# ---------------------------------------------------------------- files
def write_files(clips, kit):
    if os.path.isdir(OUT): shutil.rmtree(OUT)
    for d in ("frames", "layers", "emissive", "kit", "preview", "preview/strips"):
        os.makedirs(os.path.join(OUT, d), exist_ok=True)
    for clip, c in clips.items():
        for k in range(len(c["full"])):
            n = f"{clip}_{k + 1:02d}"
            to_img(c["full"][k]).save(os.path.join(OUT, "frames", n + ".png"))
            to_img(c["noface"][k]).save(os.path.join(OUT, "layers", n + "_noface.png"))
            to_img(c["overlay"][k]).save(os.path.join(OUT, "layers", n + "_faceov.png"))
            emis_img(c["full"][k]).save(os.path.join(OUT, "emissive", n + "_emissive.png"))
            emis_img(c["noface"][k]).save(os.path.join(OUT, "emissive", n + "_noface_emissive.png"))
    for name, (a, pv) in kit.items():
        to_img(a).save(os.path.join(OUT, "kit", name + ".png"))
    shutil.copy(os.path.join(TR, "lumi_concept", "palette_lumi.json"), os.path.join(OUT, "palette_lumi.json"))
    # anchors (same structure as liveliness/face_anchors.json)
    fa = {"version": 1, "form": FORM, "coords": "frame-local px, origin = frame top-left, y down",
          "pivotPx": [32, 61], "pivotOverride": L.PIVOT_OVERRIDE,
          "keys": "eyeL/eyeR/mouth = 五官錨點（已含面右移 2px）; head_r = 頭右上圖示; bulb = 前觸角燈頭（glow point，bulb_base/bulb_glow pivot）; bulb2 = 後觸角燈頭; tail = 尾燈中心; faceVisible; face = 預設表情; grab = 頭頂拎點（picked_up，亦係 pivot）",
          "anchors": {clip: c["anchors"] for clip, c in clips.items()}}
    with open(os.path.join(OUT, "face_anchors_lumi.json"), "w") as fh:
        head = {k: v for k, v in fa.items() if k != "anchors"}
        fh.write(json.dumps(head, ensure_ascii=False)[:-1] + ',\n "anchors":{\n')
        fh.write(',\n'.join('  ' + json.dumps(cl) + ':[\n' + ',\n'.join('   ' + json.dumps(a, ensure_ascii=False, separators=(",", ":")) for a in lst) + ']'
                            for cl, lst in fa["anchors"].items()) + '}}\n')
    json.load(open(os.path.join(OUT, "face_anchors_lumi.json")))
    return fa

# ---------------------------------------------------------------- previews
def big(a, Z=8, pad=2, bg=BG):
    m = Image.new("RGBA", (a.shape[1] + 2 * pad, a.shape[0] + 2 * pad), bg); m.alpha_composite(to_img(a), (pad, pad))
    return m.resize((m.width * Z, m.height * Z), Image.NEAREST)

def night(a, Z=8):
    return LC.h4_panel(to_img(a), emis_img(a)).resize((64 * Z, 64 * Z), Image.NEAREST)

_PROPS = None
def _props():
    global _PROPS
    if _PROPS is None:
        d = json.load(open(os.path.join(MOT, "atlas_props.json"))); _PROPS = {}
        for an, v in d["animations"].items():
            ims = [Image.open(os.path.join(MOT, "props", f + ".png")).convert("RGBA") for f in v["frames"]]
            pp = d["frames"][v["frames"][0]]["pivotPx"]
            _PROPS[an] = (ims, (pp["x"], pp["y"]), v["loop"])
    return _PROPS

def with_props(clip, k, a, Z=8):
    """pet + shared props (zzz/sweat/... from motion/atlas_props, shared palette) at head_r anchor — preview only"""
    TOP = 14
    m = Image.new("RGBA", (64, 64 + TOP), BG)
    m.alpha_composite(to_img(a), (0, TOP))
    for (pn, anc, st, behind) in M.ATT.get(clip, []):
        if k < st: continue
        ims, piv, loop = _props()[pn]
        kk = (k - st) % len(ims) if loop else min(k - st, len(ims) - 1)
        ox, oy = M.ANCH[FORM][anc]
        m.alpha_composite(ims[kk], (int(32 + ox - piv[0]), int(TOP + 61 + oy - piv[1])))
    return m.resize((m.width * Z, m.height * Z), Image.NEAREST)

def previews(clips, kit):
    P = os.path.join(OUT, "preview"); Z = 8
    for clip in ORDER:
        c = clips[clip]; fps = meta(clip)[0]; n = len(c["full"])
        fr = [with_props(clip, k, c["full"][k]) for k in range(n)]
        L.save_gif(os.path.join(P, f"{clip}_8x.gif"), fr, fps, loops=(3 if n <= 4 else 2), hold_last_ms=250)
        # strip 8x: row1 full, row2 emissive (white on dark), row3 H4 night
        cell = 64 * Z
        st = Image.new("RGBA", (cell * n, cell * 3), (24, 22, 34, 255))
        for k in range(n):
            st.paste(big(c["full"][k], Z, pad=0), (k * cell, 0))
            em = Image.new("RGBA", (64, 64), (24, 22, 34, 255)); em.alpha_composite(emis_img(c["full"][k]))
            st.paste(em.resize((cell, cell), Image.NEAREST), (k * cell, cell))
            st.paste(night(c["full"][k], Z), (k * cell, 2 * cell))
        st.save(os.path.join(P, "strips", f"{clip}_strip_8x.png"))
    # picked_up grab-aligned preview (red px = grab pivot, preview only)
    L.to_img_backup = L.to_img; L.to_img = to_img
    try: L.pickup_preview(FORM, clips["picked_up"], kit, P)
    finally: L.to_img = L.to_img_backup
    # H4 night GIF (glow) — idle, walk, emo_happy, celebrate, fall_asleep, sleep_loop, wake
    seq = []; durs = []
    for clip, loops in (("idle", 3), ("blink", 1), ("walk", 2), ("emo_happy", 2), ("celebrate", 1), ("fall_asleep", 1), ("sleep_loop", 3), ("wake", 1)):
        fps = meta(clip)[0]
        for _ in range(loops):
            for a in clips[clip]["full"]: seq.append(night(a, Z)); durs.append(int(1000 / fps))
    L.save_gif(os.path.join(P, "H4_night_glow_8x.gif"), seq, 6, loops=1, durs=durs)
    # face presets on idle + bulb moods (rig check)
    fr = []; durs = []
    for nm in ["neutral", "happy", "sleepy", "surprised", "hungry", "cuddly", "grumpy", "curious", "wink"]:
        for k in range(4):
            c = clips["idle"]; fr.append(big(L.compose_face(c["noface"][k], c["anchors"][k], L.PRESETS[nm], kit), Z)); durs.append(160)
    L.save_gif(os.path.join(P, "face_presets_on_idle_8x.gif"), fr, 6, loops=1, durs=durs)
    # main contact sheet (4x): one row per clip + H4 night row
    Zc = 4; cell = 64 * Zc + 8; cols = 6
    rows = [[clips[c]["full"][k] for k in range(len(clips[c]["full"]))] for c in ORDER]
    Hn = len(rows) + 1
    cs = Image.new("RGBA", (cols * cell + 8, Hn * cell + 8), BG)
    for r, row in enumerate(rows):
        for k, a in enumerate(row):
            cs.alpha_composite(to_img(a).resize((64 * Zc, 64 * Zc), Image.NEAREST), (8 + k * cell, 8 + r * cell))
    for k, (clip, i) in enumerate((("idle", 0), ("idle", 1), ("walk", 2), ("emo_happy", 1), ("sleep_loop", 0), ("picked_up", 1))):
        a = clips[clip]["full"][i]
        cs.paste(LC.h4_panel(to_img(a), emis_img(a)).resize((64 * Zc, 64 * Zc), Image.NEAREST), (8 + k * cell, 8 + len(rows) * cell))
    cs.save(os.path.join(OUT, "contact_lumi_4x.png"))
    # compare radiant vs lumi (same pose, 8x): idle_01, walk_03, play_04, picked_up_02
    rad = os.path.join(MOT, "frames", "radiant"); radl = os.path.join(MOT, "liveliness", "frames", "radiant")
    picks = [("idle", 1), ("walk", 3), ("play", 4), ("emo_happy", 2), ("sleep_loop", 1), ("picked_up", 2)]
    cmp_ = Image.new("RGBA", (len(picks) * (64 * 4 + 8) + 8, 2 * (64 * 4 + 8) + 8), BG)
    for i, (clip, k) in enumerate(picks):
        rp = os.path.join(rad if clip != "picked_up" else radl, f"{clip}_{k:02d}.png")
        if os.path.exists(rp): cmp_.alpha_composite(Image.open(rp).convert("RGBA").resize((256, 256), Image.NEAREST), (8 + i * 264, 8))
        cmp_.alpha_composite(to_img(clips[clip]["full"][k - 1]).resize((256, 256), Image.NEAREST), (8 + i * 264, 8 + 264))
    cmp_.save(os.path.join(OUT, "compare_radiant_vs_lumi_4x.png"))

# ---------------------------------------------------------------- docs: CLIPS.json / CLIPS.md (idempotent lumi section)
MD_MARK = "<!-- LUMI-START -->"
def update_docs(clips, atlas_info):
    W, H, nitems = atlas_info
    p = os.path.join(MOT, "CLIPS.json"); D = json.load(open(p))
    D["forms"][FORM] = {"name": "螢絨", "rarity": "rare", "stage": "adult", "skeleton": "round_s（同 radiant）", "frameSize": 64, "pivotPx": [32, 61],
                        "atlas": "../atlas_lumi.png", "json": "../atlas_lumi.json", "emissive": "../atlas_lumi_emissive.png",
                        "atlasSize": [W, H], "atlasPieces": nitems, "frames": sum(len(c["full"]) for c in clips.values()),
                        "headRightAnchor": list(M.ANCH[FORM]["head_r"]), "potAnchor": list(M.ANCH[FORM]["pot"]), "sunAnchor": [0, 0],
                        "palette": "../lumi/palette_lumi.json", "faceAnchors": "../lumi/face_anchors_lumi.json",
                        "clips": ORDER, "mvp": MVP, "extra": EXTRA, "std23Remaining": STD23_REMAIN,
                        "emissiveRule": "白＝發光（palette fly #CFF26A、fly_core #F2FFB8）：尾燈、觸角燈頭、身上光點、眼高光。發光像素唔食場景 petTint×ambientTint；glow = emissive Gaussian σ3 × #cff26a ×1.4 ＋ σ1 × #f2ffb8 ×0.35",
                        "note": "姿勢參數同 radiant 一樣（round_s），只換外觀層；尾燈脈衝（bud＋幀相位）、光點閃爍已烙入幀。"}
    for c in D["clips"]:
        n = c["name"]
        if n in clips:
            c.setdefault("anchors", {})[FORM] = clips[n]["anchors"]
            c.setdefault("forms", None)
            c["lumi"] = {"frames": len(clips[n]["full"]), "full": f"../lumi/frames/{n}_NN.png", "noface": f"../lumi/layers/{n}_NN_noface.png",
                         "faceov": f"../lumi/layers/{n}_NN_faceov.png", "emissive": f"../lumi/emissive/{n}_NN_emissive.png",
                         "atlasClip": n, "nofaceClip": f"{n}_noface", "atlas": "../atlas_lumi.json"}
            if c.get("forms") is None: c.pop("forms")
        else:
            c.get("anchors", {}).pop(FORM, None); c.pop("lumi", None)
    json.dump(D, open(p, "w"), indent=1, ensure_ascii=False)
    # md
    mp = os.path.join(MOT, "CLIPS.md"); md = open(mp, encoding="utf-8").read()
    if MD_MARK in md: md = md[:md.index(MD_MARK)].rstrip() + "\n"
    tot = sum(len(clips[c]["full"]) for c in ORDER); mvpn = sum(len(clips[c]["full"]) for c in MVP)
    rows = "\n".join(f"| {c} | {len(clips[c]['full'])} | {meta(c)[0]} | {'loop' if meta(c)[1] else 'once'} | {'MVP' if c in MVP else '加（浮動／睡眠）'} |" for c in ORDER)
    md += f"""
{MD_MARK}
## 螢絨 lumi（隱藏稀有成年形態，round_s）
- atlas：`../atlas_lumi.png/.json`（{W}×{H}，{nitems} 塊，padding 2、extrude 1）＋ `../atlas_lumi_emissive.png`（同 layout，白＝發光）
- 64×64、pivot (32,61)、lumi 31 色（`../lumi/palette_lumi.json`）、alpha 0/255、向右。姿勢＝radiant 同名 clip（只換外觀層）。
- 五官：`<clip>_noface` ＋ kit（eyes_*/mouth_*，64px，眼高光 fly_core），錨點 `../lumi/face_anchors_lumi.json`（＝本檔 clips[].anchors.lumi）；bulb＝前觸角燈頭、另有 bulb2／tail。
- picked_up：pivot＝anchors.grab（同 radiant）。
- 共 {len(ORDER)} clip／{tot} 幀（MVP 12 clip／{mvpn} 幀＋picked_up、fall_asleep、wake）。

| clip | 幀 | fps | | 類 |
|---|---|---|---|---|
{rows}

未做（std23 餘下）：{"、".join(STD23_REMAIN)}
"""
    open(mp, "w", encoding="utf-8").write(md)

def main():
    clips, kit = build()
    write_files(clips, kit)
    info = write_atlas(clips, kit)
    previews(clips, kit)
    update_docs(clips, info)
    st = {c: len(clips[c]["full"]) for c in ORDER}
    edge = [f"{c}_{k + 1:02d}" for c in ORDER for k, a in enumerate(clips[c]["full"]) if a[0].any() or a[:, 0].any() or a[:, -1].any()]
    json.dump({"clips": st, "frames": sum(st.values()), "mvpFrames": sum(st[c] for c in MVP), "atlas": info[:2], "pieces": info[2],
               "fit_adjustments": [f"{a}:{b}:{'/'.join(c)}" for a, b, c in M.FIT_LOG if a == FORM], "edgeTouch": edge,
               "std23Remaining": STD23_REMAIN}, open(os.path.join(OUT, "_stats.json"), "w"), indent=1, ensure_ascii=False)
    print("clips", st, "total", sum(st.values()), "mvp", sum(st[c] for c in MVP)); print("atlas", info); print("edge", edge)
    print("fit", [x for x in M.FIT_LOG if x[0] == FORM])

if __name__ == "__main__":
    main()
