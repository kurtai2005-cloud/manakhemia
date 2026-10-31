#!/usr/bin/env python3
"""build_tuanrong_live_s3.py — 團絨生命感第三段（s3）：nuzzle_purr、reunion_happy（sprout／radiant／soft）。
Pillow + numpy 程式逐像素繪製，原創，無 AI；31 色盤、alpha 0/255、無 AA、朝右。
重用 build_tuanrong_liveliness（L）嘅 renderer／face kit／anchors／atlas writer —— 唔改 L、唔郁第一／二段檔案。
輸出（liveliness/）：layers/<form>/<clip>_NN_{noface,faceov}.png、frames/<form>/<clip>_NN.png、
atlas_<form>_live_s3.png/json、preview/<form>/<clip>_strip_8x.png／_8x.gif、live_s3_contact_4x.png；
face_anchors.json／CLIPS.json／CLIPS.md／ASSET_LOG.md 只「加」s3 key（重讀即寫、temp+rename，冪等）。
用法：python3 build_tuanrong_live_s3.py [--no-docs]
"""
import json, os, sys, tempfile, datetime
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_tuanrong_liveliness as L
import build_tuanrong_motion as M
import build_tuanrong as bt
from build_tuanrong import IDX, FORMS, to_img

OUT = L.OUT; MOT = L.MOT; ROOT = os.path.normpath(os.path.join(HERE, ".."))
FORM_LIST = L.FORM_LIST
F = L.F
S3_ORDER = ["nuzzle_purr", "reunion_happy"]
S3_SPEC = {"nuzzle_purr": (4, 6), "reunion_happy": (5, 8)}
# fps, loop, loopFrom, priority, interruptible, cooldown, next, item, trigger, notes
S3_META = {
 "nuzzle_purr": (6, True, 0, 4, True, 0, "idle", "S3 磨蹭到呼嚕（D3 長按升級）",
                 "nuzzle 連續 ≥1.2s（長按未放）→ 由 nuzzle 當前幀切去 nuzzle_purr 循環，直至放手",
                 "挨住右邊手指、合眼笑（eyes happy＋ω 口），身體細細震（sx/sy 交替＋shear 1px），背後呼嚕震線 ( ( 烙入幀（第 1/3 幀近、第 2/4 幀遠），"
                 "第 2–4 幀頭頂右邊細心心升起（烙入幀）；放手播完當前幀 → idle（或 act_cool 30%：扮冇事）。可配 6fps 呼嚕 loop 音效。"),
 "reunion_happy": (8, False, 0, 6, False, 0, "idle", "S3 久別重逢（rush 衝過頭之後）",
                   "rush（煞停）→ 衝過頭 → act_cool → reunion_happy（D5 久別重逢鏈最後一步）",
                   "蠢蠢地但覺得自己好醒：第 1 幀扮冷靜側眼回望（ft 向後、gaze L）、第 2 幀破功（壓扁、驚喜眼）、"
                   "第 3 幀彈起舉手（細心心）、第 4 幀最高點大心心 pop＋閃光、第 5 幀落地得意 ω 臉（細心心飄高）。"
                   "引擎：播之前按玩家位置設 scaleX（衝過頭即係玩家喺後面 → 鏡像），第 1 幀先『望返轉頭』。心心烙入幀。"),
}

# ------------------------------------------------------------ extras (baked into body; not face)
HEARTS = {  # X blush, d blush_d, w white   (outline added only on empty px)
 3: ["X.X", "XXX", ".X."],
 5: ["XX.XX", "XwXXX", "XXXXd", ".XXd.", "..X.."],
 7: [".XX.XX.", "XwwXXXX", "XwXXXXd", "XXXXXXd", ".XXXXd.", "..XXd..", "...X..."],
}
HC = {"X": "blush", "d": "blush_d", "w": "white"}

def ex_heart(form, size, dx=0.55, dy=1.2, rise=0):
    """baked heart above head-right; size 3/5/7; anchored at its centre"""
    def f(cv, cx, cy, rx, ry):
        T = HEARTS[size]; h, w = len(T), len(T[0])
        x0 = int(round(cx + rx * dx - w / 2)); y0 = int(round(cy - ry * dy - h / 2 - rise))
        m = np.zeros_like(cv.a, bool)
        for j, r in enumerate(T):
            for i, ch in enumerate(r):
                x, y = x0 + i, y0 + j
                if ch in HC and 0 <= x < cv.n and 0 <= y < cv.n: cv.a[y, x] = IDX[HC[ch]]; m[y, x] = True
        rg = L._ring(m) & (cv.a == 0)
        cv.a[rg] = IDX["outline"]
    return f

def ex_purr(form, k):
    """purr vibration arcs '( (' behind the back (left side); k 0 near / 1 one px further out"""
    big = FORMS[form]["big"]
    def f(cv, cx, cy, rx, ry):
        y = cy + ry * 0.05
        if big:
            arc = [(1, -3), (0, -2), (0, -1), (0, 0), (0, 1), (1, 2)]
            for off, c in ((3 + k, "white"), (6 + k, "cream3")):
                for ax, ay in arc: L._put_empty(cv, cx - rx - off + ax, y + ay, c)
        else:
            arc = [(1, -1), (0, 0), (1, 1)]
            for off, c in ((3 + k, "white"),):
                for ax, ay in arc: L._put_empty(cv, cx - rx - off + ax, y + ay, c)
    return f

def s3_clips(form):
    big = FORMS[form]["big"]; u = 2 if big else 1; j = 4 if big else 2
    C = {}; FACE = {}
    hs = 5 if big else 3; hb = 7 if big else 5
    # a. nuzzle_purr: lean into finger (right), eyes closed, tiny vibration (alternating squash 1px + shear wobble)
    V = [(.97, 1.03, 2 * u, u), (.985, 1.015, 2 * u - 1, u), (.97, 1.03, 2 * u, u), (.985, 1.015, 2 * u - 1, u)]
    NP = []
    for k, (sy, sx, sh, sw) in enumerate(V):
        ex = [ex_purr(form, k % 2)]
        if k >= 1: ex.append(ex_heart(form, hs if k < 3 else hb, dx=.66, dy=1.05, rise=(k - 1) * u))
        NP.append(dict(shear=sh, dx=u // 2 if big else 0, fdx=u, fdy=0, sy=sy, sx=sx, sway=sw, bud=1.1 + .05 * (k % 2), fluff=k * .5, twinkle=k, extras=ex))
    C["nuzzle_purr"] = NP
    FACE["nuzzle_purr"] = [F("happy", "C", "squint")] * 4
    # b. reunion_happy: cool side-glance back -> cool breaks (squash) -> hop w/ arms up + heart -> peak big heart pop -> land smug
    C["reunion_happy"] = [
        dict(ft=-.30, feoff=.70, sway=-u, shear=-u, bud=1.0, fdy=-1),
        dict(sy=.86, sx=1.10, sway=u, bud=1.15, fdy=1),
        dict(sy=1.08, sx=.95, lift=j // 2, arms="upx", bud=1.2, sway=-u, fluff=.6, extras=[ex_heart(form, hs, dx=.75, dy=1.2)]),
        dict(sy=1.05, sx=.97, lift=j, arms="upx", bud=1.3, sway=u, fluff=1.2, twinkle=2, extras=[ex_heart(form, hb, dx=.85, dy=1.3), L.ex_sparkle(form, 0)]),
        dict(sy=.94, sx=1.05, bud=1.1, fluff=1.6, fdy=-1, extras=[ex_heart(form, hs, dx=.70, dy=1.55)]),
    ]
    FACE["reunion_happy"] = [F("squint", "L", "neutral"), F("surprised", "C", "surprised"), F("happy", "C", "happy"),
                             F("happy", "C", "happy"), F("sleepy", "C", "squint")]
    if not big:
        for cn in C:
            for p_ in C[cn]:
                if p_.get("lift", 0) > 0: p_["bud"] = min(p_.get("bud", 1.0), 1.0)
    return C, FACE

# ------------------------------------------------------------ build
def build():
    L.init_head_k(); res = {}
    for form in FORM_LIST:
        S = FORMS[form]["S"]; piv = (S // 2, S - 3)
        kit = L.build_kit(form)
        # kit must equal delivered kit files (五官 kit 仍喺 atlas_<form>_live)
        for n, (a, pv) in kit.items():
            kp = os.path.join(OUT, "kit", form, n + ".png")
            if not np.array_equal(np.array(to_img(a)), np.array(Image.open(kp).convert("RGBA"))): raise SystemExit(f"kit drift {form} {n}")
        C, FACE = s3_clips(form); clips = {}
        for clip in S3_ORDER:
            c = clips[clip] = dict(noface=[], full=[], overlay=[], anchors=[])
            for k, p in enumerate(C[clip]):
                p = M.render_fit(form, p, f"{clip}_{k + 1:02d}")
                body = L.body_render(form, p)
                an = L.rot_anchors(form, p, L.anchors(form, p, True))
                face = FACE[clip][k]; an["face"] = dict(face)
                full = L.compose_face(body, an, face, kit)
                ov = np.where(full != body, full, 0).astype(np.uint8)
                c["noface"].append(body); c["full"].append(full); c["overlay"].append(ov); c["anchors"].append(an)
        items = []; anims = {}
        for clip, c in clips.items():
            for k in range(len(c["noface"])):
                to_img(c["noface"][k]).save(os.path.join(OUT, "layers", form, f"{clip}_{k + 1:02d}_noface.png"))
                to_img(c["overlay"][k]).save(os.path.join(OUT, "layers", form, f"{clip}_{k + 1:02d}_faceov.png"))
                to_img(c["full"][k]).save(os.path.join(OUT, "frames", form, f"{clip}_{k + 1:02d}.png"))
            fps, loop = S3_META[clip][0], S3_META[clip][1]
            nf = [f"{clip}_noface_{k + 1:02d}" for k in range(len(c["noface"]))]
            ff = [f"{clip}_{k + 1:02d}" for k in range(len(c["full"]))]
            for n, a in zip(nf, c["noface"]): items.append((n, a, piv))
            for n, a in zip(ff, c["full"]): items.append((n, a, piv))
            anims[f"{clip}_noface"] = {"frames": nf, "fps": fps, "loop": loop}
            anims[clip] = {"frames": ff, "fps": fps, "loop": loop}
        files = L.write_atlas(form, items, anims, {"form": form, "frameSize": S, "phase": 3, "pivotRule": "body frames bottom-center (w/2, h-3)",
                              "note": "團絨生命感第三段：<clip>_noface 無臉身體＋完整幀；五官 kit 用 atlas_<form>_live.json 嘅 eyes_*/mouth_*/bulb_*；心心／呼嚕線烙入幀"},
                              base=f"atlas_{form}_live_s3")
        res[form] = dict(clips=clips, kit=kit, atlas=files)
    return res

def previews(res):
    for form, R in res.items():
        pdir = os.path.join(OUT, "preview", form)
        for clip in S3_ORDER:
            c = R["clips"][clip]; fps = S3_META[clip][0]
            fr = [L.big_img(c["full"][k], 8, pad=2) for k in range(len(c["full"]))]
            L.save_gif(os.path.join(pdir, f"{clip}_8x.gif"), fr, fps, loops=3, hold_last_ms=250 if clip == "reunion_happy" else 0)
            L.s2_strip(form, c, R["kit"], pdir, clip)
    Z = 4; cell = 64 * Z + 8; maxn = max(len(res["radiant"]["clips"][c]["full"]) for c in S3_ORDER)
    W = 8 + len(FORM_LIST) * (maxn * cell + 16); H = 8 + len(S3_ORDER) * cell
    img = Image.new("RGBA", (W, H), L.BG)
    for r, clip in enumerate(S3_ORDER):
        for fi, form in enumerate(FORM_LIST):
            c = res[form]["clips"][clip]; S = FORMS[form]["S"]; z = Z * (64 // S)
            for k, a in enumerate(c["full"]):
                img.alpha_composite(to_img(a).resize((S * z, S * z), Image.NEAREST), (8 + fi * (maxn * cell + 16) + k * cell, 8 + r * cell))
    img.save(os.path.join(OUT, "live_s3_contact_4x.png"))

# ------------------------------------------------------------ docs: additions only, re-read right before write, atomic
def atomic_write(path, text):
    d = os.path.dirname(path); fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp_s3_")
    with os.fdopen(fd, "w", encoding="utf-8") as fh: fh.write(text)
    os.chmod(tmp, 0o644); os.replace(tmp, path)

def write_face_anchors(res):
    p = os.path.join(OUT, "face_anchors.json"); fa = json.load(open(p))
    for form in FORM_LIST:
        for clip in S3_ORDER: fa["anchors"][form][clip] = res[form]["clips"][clip]["anchors"]
    out = ('{"version":' + json.dumps(fa["version"]) + ',\n "coords":' + json.dumps(fa["coords"], ensure_ascii=False) + ',\n "pivotPx":' + json.dumps(fa["pivotPx"]) +
           ',\n "keys":' + json.dumps(fa["keys"], ensure_ascii=False) + ',\n "pivotOverride":' + json.dumps(fa["pivotOverride"]) + ',\n "anchors":{\n')
    fl = []
    for form in fa["anchors"]:
        cl = ['   ' + json.dumps(clip) + ':[\n' + ',\n'.join('    ' + json.dumps(a, ensure_ascii=False, separators=(",", ":")) for a in lst) + ']'
              for clip, lst in fa["anchors"][form].items()]
        fl.append('  ' + json.dumps(form) + ':{\n' + ',\n'.join(cl) + '}')
    out += ',\n'.join(fl) + '}}\n'
    assert json.loads(out) == fa
    atomic_write(p, out)

def clip_entry(clip, res):
    fps, loop, lf, pri, intr, cd, nxt, item, trig, notes = S3_META[clip]
    return {"name": clip, "status": "已交付（liveliness s3）", "category": "生命感", "item": item, "frames": S3_SPEC[clip][0], "fps": fps, "loop": loop,
            "priority": pri, "interruptible": intr, "trigger": trig, "cooldown_s": cd, "next": nxt, "notes": notes, "attachments": [],
            "layers": {"noface": f"liveliness/layers/<form>/{clip}_NN_noface.png", "faceov": f"liveliness/layers/<form>/{clip}_NN_faceov.png",
                       "full": f"liveliness/frames/<form>/{clip}_NN.png", "nofaceClip": f"{clip}_noface", "atlas": "liveliness/atlas_<form>_live_s3.json",
                       "kitAtlas": "liveliness/atlas_<form>_live.json（eyes_*/mouth_*/bulb_*）", "previewStrip": f"liveliness/preview/<form>/{clip}_strip_8x.png"},
            "anchors": {f: res[f]["clips"][clip]["anchors"] for f in FORM_LIST}, "phase": 3,
            **({"loopRange": [0, 3]} if loop else {})}

MD_A = "<!-- LIVE-S3-START -->"; MD_B = "<!-- LIVE-S3-END -->"
def write_docs(res):
    # CLIPS.json — re-read immediately before write; only touch our keys
    p = os.path.join(MOT, "CLIPS.json"); D = json.load(open(p, encoding="utf-8"))
    names = [c["name"] for c in D["clips"]]
    for clip in S3_ORDER:
        e = clip_entry(clip, res)
        if clip in names:
            old = D["clips"][names.index(clip)]
            keep = {k: v for k, v in old.items() if k.startswith("evo_") or k == "lumi"}   # other workers' per-form additions
            anc = {k: v for k, v in old.get("anchors", {}).items() if k not in FORM_LIST}
            e.update(keep); e["anchors"].update(anc); D["clips"][names.index(clip)] = e
        else: D["clips"].append(e)
    for form in FORM_LIST:
        la = D["forms"][form].setdefault("liveAtlas", [])
        if f"atlas_{form}_live_s3.png" not in la: la.append(f"atlas_{form}_live_s3.png")
    D.setdefault("liveliness", {})["s3"] = {"clips": S3_ORDER, "atlas": "liveliness/atlas_<form>_live_s3.png/json（五官 kit 仍喺 atlas_<form>_live）",
                                           "tool": "tools/build_tuanrong_live_s3.py", "notes": "liveliness/LIVE_S3_NOTES.md",
                                           "rebuildNote": "build_tuanrong_liveliness_docs.py 重砌 CLIPS.json 之後要再跑 build_tuanrong_live_s3.py（再加返 s3 段）"}
    atomic_write(p, json.dumps(D, indent=1, ensure_ascii=False))
    # CLIPS.md — marked section, replaced idempotently
    mp = os.path.join(MOT, "CLIPS.md"); md = open(mp, encoding="utf-8").read()
    if MD_A in md: md = md[:md.index(MD_A)].rstrip() + "\n\n" + md[md.index(MD_B) + len(MD_B):].lstrip()
    rows = "\n".join(f"| {c} | {S3_SPEC[c][0]}／{S3_SPEC[c][1]}fps | {'循環' if S3_META[c][1] else '單次'} | {S3_META[c][3]} | {S3_META[c][8]} | {S3_META[c][9]} |" for c in S3_ORDER)
    sec = (f"{MD_A}\n## 生命感第三段（s3）— 遊美 2026-10-31\n\n"
           "3 form（sprout 32×32 pivot (16,29)／radiant、soft 64×64 pivot (32,61)）；atlas `liveliness/atlas_<form>_live_s3.png/json`（1024 寬、pad 2、extrude 1、pivotPx）；"
           "五官 kit 仍喺 `atlas_<form>_live`；錨點 `clips[].anchors[form]`＝`liveliness/face_anchors.json`。詳見 `liveliness/LIVE_S3_NOTES.md`。\n\n"
           "| clip | 幀／fps | loop | 優先 | 觸發 | 備註 |\n|---|---|---|---|---|---|\n" + rows + f"\n{MD_B}\n")
    atomic_write(mp, md.rstrip() + "\n\n" + sec)

def write_log(res):
    lp = os.path.join(ROOT, "ASSET_LOG.md"); txt = open(lp, encoding="utf-8").read()
    A = "<!-- LIVE-S3-LOG-START -->"; B = "<!-- LIVE-S3-LOG-END -->"
    if A in txt: txt = txt[:txt.index(A)].rstrip() + "\n\n" + txt[txt.index(B) + len(B):].lstrip()
    nfr = sum(S3_SPEC[c][0] for c in S3_ORDER)
    sec = (f"{A}\n## 2026-10-31 — 團絨生命感第三段（s3）\n"
           f"- nuzzle_purr 4幀/6fps 循環、reunion_happy 5幀/8fps；sprout／radiant／soft 各 {nfr} 幀（noface＋faceov＋full＋anchors）。\n"
           "- `sprites/tuanrong/motion/liveliness/atlas_<form>_live_s3.png/json`；預覽 `preview/<form>/<clip>_strip_8x.png`、`live_s3_contact_4x.png`。\n"
           "- 工具 `tools/build_tuanrong_live_s3.py`（Pillow/numpy 程式繪製，無 AI）；驗證 `tools/validate_liveliness.py`（加 s3 檢查）。\n"
           "- 微塵（dust）現有尺寸冇身體美術 → 未出 live atlas（見 LIVE_S3_NOTES.md 建議）。\n" + B + "\n")
    atomic_write(lp, txt.rstrip() + "\n\n" + sec)

if __name__ == "__main__":
    res = build(); previews(res)
    write_face_anchors(res)
    if "--no-docs" not in sys.argv: write_docs(res); write_log(res)
    print("ok", {f: {c: len(v["full"]) for c, v in R["clips"].items()} for f, R in res.items()}, "fit", [x for x in M.FIT_LOG if x[1].split("_")[0] in ("nuzzle", "reunion")])
