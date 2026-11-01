#!/usr/bin/env python3
"""團絨 飾品「畫一次，runtime 套落全部形態／動作」— 遊美 2026-11-01（Kurt 批：「好」）。
Pillow／numpy 程式像素，冇 AI；v3 色盤；alpha 0/255。只係新增：ACC1–5 嘅 baked atlas 原封不動。

① attach：由現有 fit 規則（build_accessories.py 嘅 fit／stabilise_head／head_l／glasses_pre／neck／bulb 規則）匯出
   每形態每幀 6 個 slot 嘅掛點表 → sprites/tuanrong/accessories/attach/<form>.json ＋ attach/ATTACH.json（索引＋欄位）。冇重畫任何幀。
② source：13 件飾品轉做「每件畫一次」：front／side／back 3 個 view × S／M／L 3 個尺寸（＋部件 tail／decor），item.json 寫 slot、pivot、
   縮放規則、擺動、讓位、faceSafe → sprites/tuanrong/accessories/source/<item>/。
③ newitem：新測試飾品 櫻桃髮夾 cherry（side_r，兩粒櫻桃有擺動）— 只畫 3 個 view。
④ compare：runtime（tools/compose_accessory_runtime.py）對 baked atlas 逐幀比較 → 自動加 per-form 位移／縮放 override（只改 data）→ RUNTIME_COMPARE.json／.md。
⑤ preview：runtime 預覽（idle／walk／sleep／turn_back，3x）。
用法：python3 build_accessory_runtime.py [all|attach|source|newitem|compare|preview|meta]"""
import json, os, sys, math
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_accessories as B
ACCD = B.ACCD; ATT = os.path.join(ACCD, "attach"); SRC = os.path.join(ACCD, "source"); PREVR = os.path.join(B.PREV, "runtime")
PAD = B.PAD
ART = os.path.dirname(HERE)
def r2(v): return round(float(v), 2)
def r1(v): return round(float(v), 1)

# ================================================================ ① attach（掛點表）
HEAD_SC = {"evo_still_radiant": 0.8, "evo_still_soft": 0.9, "evo_still_ember": 0.85, "evo_guard_moon": 1.8, "evo_still_moon": 0.8}   # 頭飾共用（FIT 表抽出）
SIDE_SC = {"evo_still_moon": 0.62, "evo_guard_moon": 1.4, "evo_still_radiant": 0.8, "evo_still_ember": 0.85, "evo_still_soft": 0.9}  # 側飾共用
PIN_SIDE = {"evo_guard_moon": "r", "evo_still_moon": "r", "evo_guard_shroom": "l", "evo_still_shroom": "l"}
FIELDS = {
    "head": ["x", "y", "ux", "uy", "ang", "ws", "hs"],
    "pin": ["x", "y", "ang", "ws"],
    "side_r": ["x", "y", "ang", "ws", "mirror"],
    "side_l": ["x", "y", "ang", "ws", "mirror"],
    "face": ["lx", "ly", "rx", "ry", "bx", "by", "plx", "ply", "prx", "pry", "pbx", "pby", "eyeTopL", "eyeTopR"],
    "eyes": ["[x,y,x,y,…] 左眼 blob 像素", "右眼 blob 像素（鏡框唔可以壓）"],
    "facePts": ["[[x,y]…] eyeL／eyeR／mouth：±1 係五官保護區"],
    "glow": ["[[x,y]…] 燈／光點：飾品 ±1 挖空"],
    "bulbPt": ["x", "y"],
    "stem": ["[[y,x0,x1]…] 帽要挖空嘅芽／莖 run"],
    "facing": ["F|S|B"], "dir": ["+1|-1"],
    "neck": ["y", "cx", "ang", "xl", "xr", "rows(y=ny-4..ny+9: [x0,x1] 可畫範圍 or null)"],
    "bulb": ["hx", "hy", "fx", "fy", "fang", "fw", "ux", "uy"],
}
def facing(an, a0, f):
    """F 正面／S 側面／B 背面；dir：+1 向右／-1 向左（側面先有意義）"""
    if not an.get("faceVisible", True): return "B", 1
    if "eyeL" in an and "eyeL" in a0:
        d = math.hypot(an["eyeR"][0] - an["eyeL"][0], an["eyeR"][1] - an["eyeL"][1]); d0 = math.hypot(a0["eyeR"][0] - a0["eyeL"][0], a0["eyeR"][1] - a0["eyeL"][1])
        if d < 0.6 * d0:
            dx = f["em"][0] - f["top"][0] if f.get("ok") else 0
            return "S", (1 if dx >= 0 else -1)
    return "F", 1
def stem_spans(body, f, form):
    m = B.head_cut(body, f, full=form in B.CUT_FULL); out = []
    for y in np.nonzero(m.any(1))[0]:                    # 每行連續 run：[y, x0, x1]（同一行可以有幾段）
        xs = np.nonzero(m[y])[0]; st = xs[0]
        for a_, b_ in zip(xs, list(xs[1:]) + [None]):
            if b_ is None or b_ != a_ + 1: out.append([int(y), int(st), int(a_)]); st = b_
    return out
def eye_boxes(body, an):
    """兩隻眼 blob 像素（flat [x,y,x,y,...]）：眼鏡唔可以壓到"""
    if not an.get("faceVisible", True) or "eyeL" not in an or "eyeR" not in an: return None
    out = []
    for k in ("eyeL", "eyeR"):
        px = sorted(B.eye_blob(body, an, k)); out.append([int(v) for p_ in px for v in p_])
    return out
def halo_float(body, an, f, ref, form, S):
    """光環／浮喺頭頂嘅飾品：底部落點（bulb：玻璃頂 br+1.5；其餘：頭頂剪影最高點上 2px）＋建議闊 fw＋傾角"""
    a = body[..., 3] > 0
    if B.top_bulb(form) and "bulb" in an:
        br = B.BR[form]; rx = br + 2.0; bx, by = an["bulb"]; g = br + 1.5
        return bx + f["u"][0] * g, by + f["u"][1] * g, max(-12.0, min(12.0, f["ang"])), 2 * rx, f["u"]
    rx = max(3.5, min(ref["hw"] * 0.3, S * 0.13))
    if "eyeL" in an:
        ex, ey = an["eyeR"][0] - an["eyeL"][0], an["eyeR"][1] - an["eyeL"][1]; L_ = math.hypot(ex, ey) or 1; ue = (ey / L_, -ex / L_)
    else: ue = (0.0, -1.0)
    cx = f["em"][0] + ue[0] * ref["hh"]
    cols = a[:, max(0, int(cx - rx - 1)):min(S, int(cx + rx + 2))]; rows_ = np.nonzero(cols.any(1))[0]
    yt = rows_.min() if len(rows_) else f["top"][1]
    return cx, yt - 2, 0.0, 2 * rx, (0.0, -1.0)
def bulb_hang(an, f, ref, form):
    if "bulb" in an and not B.bell_low(form):
        bx, by = an["bulb"]; br = B.BR[form]; return bx + int(round(br * 0.6)), by + int(math.ceil(br)) + 1, 0
    base = 1 if "bulb" not in an else 2
    return f["top"][0] + f["pp"][0] * ref["hw"] * 0.22, f["top"][1] + f["pp"][1] * ref["hw"] * 0.22, base
def face_centres(body, an, f, g, form, forehead):
    """[lx,ly,rx,ry,bx,by, plx,ply,prx,pry,pbx,pby, topL,topR]：clip 平均鏡心＋clip 眼 blob 半軸；p*＝逐幀跟眼中心＋逐幀最大半軸；top＝眼 blob 頂（額頭版用）"""
    if not an.get("faceVisible", True) or "eyeL" not in an or "eyeR" not in an: return None
    cs = [np.array(an[k], float) + np.array(o) for k, o in zip(("eyeL", "eyeR"), g["off"])]
    pc = []; tops = []
    for k, o in zip(("eyeL", "eyeR"), g["off"]):
        px = B.eye_blob(body, an, k)
        if px: q = np.array(px, float); pc.append((q.min(0) + q.max(0)) / 2); tops.append(int(q[:, 1].min()))
        else: pc.append(np.array(an[k], float) + np.array(o)); tops.append(int(an[k][1] - 1))
    return [r2(cs[0][0]), r2(cs[0][1]), r2(cs[1][0]), r2(cs[1][1]), r2(g["bx"]), r2(g["by"]),
            r2(pc[0][0]), r2(pc[0][1]), r2(pc[1][0]), r2(pc[1][1]), r2(g["pbx"]), r2(g["pby"]), tops[0], tops[1]]
def neck_geom(body, an, f, ref):
    g = B._neck_geom(body, an, f, ref, {"dy": 0})
    if g is None: return None
    ny, cx, t, (xl, xr), run_at = g; rows = []
    for y in range(ny - NECK_R0, ny + NECK_R1):
        rr = run_at(y) if 0 <= y < body.shape[0] else None
        rows.append([max(rr[0], xl) - 1, min(rr[1], xr) + 1] if rr else None)
    return [int(ny), r2(cx), r1(f["ang"]), int(xl), int(xr), rows]
NECK_R0, NECK_R1 = 4, 10   # rows：每行身體 run 夾 [xl,xr] 再 ±1（y＝ny-4 … ny+9）
def attach_form(form):
    A = B.anchors(form); ref = B.ref_fit(form); b0 = B.load(B.frame_path(form, "idle", 1)); S = b0.shape[0]; a0 = A["idle"][0]
    ed0 = abs(a0["eyeR"][0] - a0["eyeL"][0]) if "eyeL" in a0 else None
    fa = B.form_anims(form); pin = PIN_SIDE.get(form)
    forehead = bool(B.FIT["glasses"][form].get("forehead"))
    out = {"version": 1, "form": form, "frameSize": S, "sizeClass": B.size_class(S), "overlayPad": PAD,
           "ref": {"top": [r2(ref["top"][0]), r2(ref["top"][1])], "hw": int(ref["hw"]), "hh": r2(ref["hh"]), "eyeDist": ed0, "neckHalf": r2(ref["neck_half"])},
           "slots": {"head": {"mode": "pin" if pin else "hat", "pinSide": pin, "sc": HEAD_SC.get(form, 1.0)},
                     "side_r": {"sc": SIDE_SC.get(form, 1.0)}, "side_l": {"sc": SIDE_SC.get(form, 1.0)},
                     "face": {"mode": "forehead" if forehead else "eyes"},
                     "neck": {"thRef": max(2, int(round(ref["hw"] / 7)))},
                     "bulb": {"br": B.BR.get(form), "topBulb": B.top_bulb(form), "hangBase": ["bulb", "top", "top_low"][bulb_hang(a0, B.fit(b0, a0, ref, form=form), ref, form)[2]]}},
           "emissiveDir": (os.path.relpath(os.path.dirname(B.emissive_path(form, "idle_01")), ART) if B.emissive_path(form, "idle_01") else None),
           "fields": FIELDS, "clips": {}}
    for clip, alist in B.clips_of(form):
        bodies = [B.load(B.frame_path(form, clip, k)) for k in range(1, len(alist) + 1)]
        fs = [B.fit(b, a, ref, form=form) for b, a in zip(bodies, alist)]
        ce = {"frameDir": os.path.relpath(os.path.dirname(B.frame_path(form, clip, 1)), ART), "fps": fa.get(clip, {}).get("fps"), "loop": bool(fa.get(clip, {}).get("loop", False)), "n": len(alist), "hidden": {}}
        bad = [k for k, f in enumerate(fs, 1) if not f["ok"]]
        if bad:
            why = f"{clip}_{bad[0]:02d}: {fs[bad[0] - 1]['why']}"
            ce["hidden"] = {s: why for s in ("head", "side_r", "side_l", "face", "neck", "bulb")}; ce["frames"] = []; out["clips"][clip] = ce; continue
        raw = [f["ang"] for f in fs]
        for i, f in enumerate(fs):
            w = raw[max(0, i - 1):i + 2]; f["ang"] = max(-28.0, min(28.0, (sum(w) + raw[i]) / (len(w) + 1)))
            if abs(f["ang"]) < 4: f["ang"] = 0.0
        hs_ = [dict(f) for f in fs]; B.stabilise_head(hs_, bodies)
        g = None
        if any(a.get("faceVisible", True) and "eyeL" in a for a in alist):
            tmp = [dict(f) for f in fs]; B.glasses_pre(tmp, bodies, alist, form, clip=clip); g = tmp[0]["gl"]
        if clip in ("leaf_umbrella",): ce["hidden"]["head"] = "撐葉傘：葉蓋住頭頂，頭飾收起（避免帽畫喺葉上面）"
        frames = []
        for k, (body, an, f, h) in enumerate(zip(bodies, alist, fs, hs_), 1):
            fc, dr = facing(an, a0, f); bk = fc == "B"
            r = {"facing": fc, "dir": dr}
            r["head"] = [r2(h["top"][0]), r2(h["top"][1]), round(h["u"][0], 4), round(h["u"][1], 4), r1(h["ang"]), round(h["ws"], 3), round(h["hs"], 3)]
            if pin:
                if pin == "r": px, py = an["head_r"][0] - 3, an["head_r"][1] - 5
                else: px, py = 2 * h["em"][0] - an["head_r"][0], an["head_r"][1] - 1
                r["pin"] = [r2(px), r2(py), r1(h["ang"]), round(h["ws"], 3)]
            hl = B.head_l(an, f, ed0); hr = an["head_r"]
            R = (hl[0], hl[1] + 1) if bk else (hr[0], hr[1] + 1); L = (hr[0], hr[1] + 1) if bk else (hl[0], hl[1] + 1)
            r["side_r"] = [r2(R[0]), r2(R[1]), r1(f["ang"]), round(f["ws"], 3), int(bk)]
            r["side_l"] = [r2(L[0]), r2(L[1]), r1(f["ang"]), round(f["ws"], 3), int(bk)]
            r["face"] = face_centres(body, an, f, g, form, forehead) if g else None
            r["eyes"] = eye_boxes(body, an)
            r["neck"] = neck_geom(body, an, f, ref)
            hx, hy, hb = bulb_hang(an, f, ref, form); fx, fy, fang, fw, fb = halo_float(body, an, f, ref, form, S)
            r["bulb"] = [r2(hx), r2(hy), r2(fx), r2(fy), r1(fang), r2(fw), round(fb[0], 4), round(fb[1], 4)]
            r["facePts"] = [list(an[k_]) for k_ in ("eyeL", "eyeR", "mouth") if k_ in an] if an.get("faceVisible", True) else []
            r["glow"] = [list(an[k_]) for k_ in B.GLOW_KEYS if k_ in an]
            r["bulbPt"] = list(an["bulb"]) if "bulb" in an else None
            r["stem"] = stem_spans(body, h, form)
            frames.append(r)
        if any(fr["neck"] is None for fr in frames):
            k = next(i for i, fr in enumerate(frames, 1) if fr["neck"] is None); ce["hidden"]["neck"] = f"{clip}_{k:02d}: 頸位冇身體"
        if any(fr["face"] is None for fr in frames):
            k = next(i for i, fr in enumerate(frames, 1) if fr["face"] is None); ce["hidden"]["face"] = f"{clip}_{k:02d}: faceVisible=false（背面／遮面）"
        ce["frames"] = frames; out["clips"][clip] = ce
    return out
def compact(o):
    """frames → 每 slot 一個 list（細啲）"""
    for c in o["clips"].values():
        fr = c.pop("frames"); c["f"] = {}
        for key in ("facing", "dir", "head", "pin", "side_r", "side_l", "face", "eyes", "neck", "bulb", "facePts", "glow", "bulbPt", "stem"):
            if fr and key in fr[0]: c["f"][key] = [x[key] for x in fr]
    return o
def build_attach(forms=None, att=None, extra_path=None):
    """forms=None → 25 個正式形態＋FORMS_EXTRA.json 登記嘅新形態（只要加 anchor data，唔使改 code）"""
    att = att or ATT; os.makedirs(att, exist_ok=True); idx = {}
    extra = register_forms(load_extra(extra_path)); allf = list(B.FORMS) + [f for f in extra if f not in B.FORMS]
    for form in forms or allf:
        o = compact(attach_form(form)); p = os.path.join(att, f"{form}.json")
        if form in extra: o["extra"] = {k: v for k, v in extra[form].items() if k in ("species", "route", "stage", "note")} or True
        json.dump(o, open(p, "w"), ensure_ascii=False, separators=(",", ":"))
        n = sum(c["n"] for c in o["clips"].values()); idx[form] = {"file": f"attach/{form}.json", "frameSize": o["frameSize"], "clips": len(o["clips"]), "frames": n}
        if form in extra: idx[form]["extra"] = True
        print("attach", form, len(o["clips"]), "clips", n, "frames", flush=True)
    if not forms:
        j = {"version": 1, "generator": "tools/build_accessory_runtime.py", "base": "da76a09（本機用 312b8838 worktree，art-pet 一致）", "overlayPad": PAD,
             "slots": ["head", "side_l", "side_r", "neck", "bulb", "face"], "fields": FIELDS, "forms": idx,
             "extraForms": {"registry": "attach/FORMS_EXTRA.json", "example": "attach/FORMS_EXTRA.example.json", "anchorSchema": ANCHOR_SCHEMA,
                            "how": "新形態（例：species_concept 嘅新種族）：準備 frames/<clip>_<kk>.png＋每幀 anchors（eyeL/eyeR/mouth/head_r/bulb/faceVisible）→ 喺 FORMS_EXTRA.json 加一項 → python3 build_accessory_runtime.py attach。飾品 source 唔使改；件件自動套。"},
             "notes": ["每 clip：f.<field>[k-1]＝第 k 幀；hidden.<slot>＝成個 clip 收起嘅原因（引擎直接唔畫）",
                       "座標＝身體 frame 像素座標（未加 overlayPad）；角度＝度，正＝順時針（畫面 y 向下）",
                       "facing：F 正面／S 側面（眼距 < 0.6×idle）／B 背面（faceVisible=false）→ 揀 item 嘅 front／side／back view",
                       "詳細用法睇 accessories/ENGINE_ATTACH.md"]}
        json.dump(j, open(os.path.join(att, "ATTACH.json"), "w"), ensure_ascii=False, indent=1)
    return idx

# ================================================================ ② source（每件畫一次：front／side／back × S/M/L）
INV = {v: k for k, v in B.LAB.items()}
def hexc(name): r, g, b = B.rgb(name)[:3]; return f"#{r:02x}{g:02x}{b:02x}"
class Mats:
    """物料表：每種 label → 唯一 key 色（＝base 色；撞色就 B 通道 +1 區分）；item.json materials＝{key: ramp}"""
    def __init__(s): s.key = {}; s.out = {}
    def k(s, lab_, extra=None):
        if lab_ in s.key: return s.key[lab_]
        sh, base, hi = B.RAMP[lab_]; r, g, b = B.rgb(base)[:3]
        while f"#{r:02x}{g:02x}{b:02x}" in s.out: b = b + 1 if b < 255 else b - 7
        kk = f"#{r:02x}{g:02x}{b:02x}"; s.key[lab_] = kk
        s.out[kk] = {"name": {v: k for k, v in B.LAB.items()}[lab_], "shade": hexc(sh), "base": hexc(base), "hi": hexc(hi)}
        if extra: s.out[kk].update(extra)
        return kk
def save_lab(d, name, m, mats, extra=None):
    """label map → lab PNG（key 色，alpha 0/255）＋ 人睇用嘅 render PNG"""
    img = np.zeros(m.shape + (4,), np.uint8)
    for lab_ in np.unique(m):
        if not lab_: continue
        kk = mats.k(int(lab_), (extra or {}).get(int(lab_))); img[m == lab_, :3] = [int(kk[i:i + 2], 16) for i in (1, 3, 5)]; img[m == lab_, 3] = 255
    Image.fromarray(img, "RGBA").save(os.path.join(d, f"lab_{name}.png"))
    rr = B.render(m)
    if B.HALOH in m: rr[np.pad(m, 1) == B.HALOH] = 0
    Image.fromarray(rr, "RGBA").save(os.path.join(d, f"{name}.png"))
    return f"lab_{name}.png"
def squash(m, piv, k=0.82, anchors=None):
    """側面 view：label 橫向 nearest 壓窄（k），pivot／錨點跟住"""
    h, w = m.shape; W2 = max(3, int(round(w * k))) | (w & 1 and 1)
    xi = np.minimum(w - 1, ((np.arange(W2) + .5) * w / W2).astype(int)); m2 = m[:, xi]
    f = lambda p: ((p[0] + .5) * W2 / w - .5, p[1])
    return m2, f(piv), ({a: f(p) for a, p in (anchors or {}).items()})
def back_of(m, repl):
    """背面 view：前面先見到嘅細節換走（repl：{label: label}）"""
    m = m.copy()
    for a, b in repl.items(): m[m == a] = b
    return m
def ladder(vals, n=3):
    lo, hi = min(vals), max(vals)
    if n == 1 or hi <= lo: return [lo]
    mid = math.sqrt(lo * hi); out = sorted(set([lo, B.odd(mid), hi]))
    return out
def form_idle(form):
    A = B.anchors(form)["idle"][0]; ref = B.ref_fit(form); S = B.load(B.frame_path(form, "idle", 1)).shape[0]; return A, ref, S
def base_item(key, slot):
    pr = B.YIELD.index(key) if key in B.YIELD else 0
    y = {"priority": pr, "steps": [list(s_) for s_ in B.YIELD_STEPS.get(key, [])], "coverMax": B.COVER_MAX_PAIR.get(key, B.COVER_MAX),
         "floatOk": key in B.FLOAT_OK, "anyOverlap": key == "halo"}
    return {"id": key, "name": B.ITEMS[key]["name"] if key in B.ITEMS else key, "slot": slot, "version": 1, "faceSafe": True,
            "render": {"outline": True, "shade": True}, "yield": y, "views": {}, "parts": {}, "formOverrides": {}}

def src_head(key):
    P = B.HEAD[key]; d = os.path.join(SRC, key); os.makedirs(d, exist_ok=True); mats = Mats(); it = base_item(key, "head")
    tg = []
    for f in B.FORMS:
        if f in B.HATFORMS: continue
        _, ref, S = form_idle(f); tg.append(B.odd(ref["hw"] * P["k"] * HEAD_SC.get(f, 1.0) * (B.FIT[key][f]["sc"] / HEAD_SC.get(f, 1.0) if key == "straw" and f == "evo_still_moon" else 1.0), P["minW"]))
    sizes = ladder(tg); names = ["S", "M", "L"][:len(sizes)] if len(sizes) == 3 else ["S", "L"][:len(sizes)]
    if len(sizes) == 2: names = ["S", "L"]
    back_repl = {"crown": {B.RED: B.GOLD, B.CYAN: B.GOLD}, "nightcap": {B.GOLD: B.NIGHT}}.get(key, {})
    for nm, W in zip(names, sizes):
        H = max(4 if key != "nightcap" else 5, int(round(W * P["hr"]))); L_ = nm == "L"
        if key == "nightcap":
            m, piv, tip = B.gen_nightcap(W, H, L=L_); anc = {"tip": [round(tip[0], 2), round(tip[1], 2)]}
        else:
            m, piv = (B.gen_straw(W, H) if key == "straw" else P["gen"](W, H, L=L_)); anc = {}
        for vn, mm, pv, an_ in (("front", m, piv, anc), ("side",) + squash(m, piv, 0.82, anc), ("back", back_of(m, back_repl), piv, anc)):
            e = {"lab": save_lab(d, f"{vn}_{nm}", mm, mats), "w": W, "h": H, "pivot": [round(pv[0], 2), round(pv[1], 2)]}
            if vn == "side": e["w"] = W   # 壓窄只係外形；縮放仍以正面闊計
            if an_: e["anchors"] = {a: [round(p[0], 2), round(p[1], 2)] for a, p in an_.items()}
            if key == "nightcap": e["parts"] = [{"id": "tail", "at": "tip", "angK": 0.5, "replace": [mats.k(B.NIGHT), mats.k(B.WHITE)]}]
            it["views"].setdefault(vn, {})[nm] = e
        if key == "nightcap":
            tm, tp = gen_tail(W, pin=False); it["parts"].setdefault("tail", {})[nm] = {"lab": save_lab(d, f"part_tail_{nm}", tm, mats), "pivot": tp}
    it["size"] = {"mode": "rel", "ref": "hw", "k": P["k"], "minW": P["minW"], "odd": True, "ws": [0.8, 1.3], "hr": P["hr"], "hs": [0.8, 1.25], "minH": 5 if key == "nightcap" else 4}
    it["place"] = {"anchor": "head", "sink": P["sink"], "faceGuard": {"step": [0, -1], "max": 8}}
    it["pin"] = {"k": P["pin"], "ang": P["pin_ang"], "minW": 7, "minH": 4 if key == "nightcap" else 3}
    if key == "straw": it["pin"]["sc"] = {"evo_still_moon": B.FIT["straw"]["evo_still_moon"]["sc"] / HEAD_SC["evo_still_moon"]}
    if key == "nightcap":
        W = 11; H = max(6, int(round(W * 1.05))); m, piv, tip = B.gen_pincap(W, H)
        it["views"]["pin_r"] = {"S": {"lab": save_lab(d, "pin_r_S", m, mats), "w": W, "h": H, "pivot": [round(piv[0], 2), round(piv[1], 2)],
                                      "anchors": {"tip": [round(tip[0], 2), round(tip[1], 2)]}, "parts": [{"id": "tail_r", "at": "tip", "angK": 0.0, "replace": [mats.k(B.NIGHT), mats.k(B.WHITE)]}]}}
        tm, tp = gen_tail(W, pin=True); it["parts"]["tail_r"] = {"S": {"lab": save_lab(d, "part_tail_r_S", tm, mats), "pivot": tp}}
        it["pin"]["r"] = {"view": "pin_r", "wK": 0.75, "hK": 1.05, "minH": 6, "ang": 6}
        it["swing"] = {"src": "head", "kx": 6.0, "ky": 4.0, "decay": 0.55, "lim": 30.0, "maxd": 14.0, "apply": "tail", "gain": 0.6}
        it["partFallback"] = [{"rot": r_, "scale": s_} for s_ in (1.0, 0.75, 0.55) for r_ in (0, 11, 22, -11, 34, 45, -22)]
        for v in it["views"].values():
            for e in v.values():
                for p_ in e.get("parts", []):
                    if p_["id"] == "tail_r": pass
    it["cutStem"] = True
    it["hideClips"] = {"*": dict(B.HIDE.get(key, {}).get("*", {}))}
    it["materials"] = mats.out; return it
def gen_tail(W, pin=False):
    """睡帽尾（同 baked 一樣嘅曲線，ang 0、冇擺）：由帽尖 (0,0) 出發；回傳 label map＋pivot（＝帽尖）"""
    if pin: tl = max(4.0, W * 0.85); th0 = max(1.8, W * 0.2); pr = max(1.4, W * 0.15); phi0, phi1 = 330, 445
    else: tl = max(4.0, W * 0.62); th0 = max(1.5, W * 0.11); pr = max(1.1, W * 0.085); phi0, phi1 = 200, 112
    R = int(tl + pr + th0 + 4); lab_ = np.zeros((2 * R + 1, 2 * R + 1), np.int16); x_, y_ = float(R), float(R); nseg = int(math.ceil(tl * 2)); pts = []
    for i in range(nseg + 1):
        r_ = i / nseg; phi = math.radians(phi0 + (phi1 - phi0) * (r_ ** 0.7))
        if i: x_ += math.cos(phi) * 0.5; y_ += math.sin(phi) * 0.5
        pts.append((x_, y_)); th = th0 * (1 - 0.55 * r_); rr = th / 2
        for yy in range(int(math.floor(y_ - rr)), int(math.ceil(y_ + rr)) + 1):
            for xx in range(int(math.floor(x_ - rr)), int(math.ceil(x_ + rr)) + 1):
                if (xx - x_) ** 2 + (yy - y_) ** 2 <= rr * rr + .25:
                    lab_[yy, xx] = B.NIGHT if pin else (B.WHITE if int(i / (3 if W >= 17 else 2)) % 2 else B.NIGHT)
    ex, ey = pts[-1]
    for yy in range(int(math.floor(ey - pr - 1)), int(math.ceil(ey + pr + 1)) + 1):
        for xx in range(int(math.floor(ex - pr - 1)), int(math.ceil(ex + pr + 1)) + 1):
            if (xx - ex) ** 2 + (yy - ey) ** 2 <= pr * pr + .3: lab_[yy, xx] = B.WHITE
    ys, xs = np.nonzero(lab_); y0, x0 = ys.min(), xs.min()
    return lab_[y0:ys.max() + 1, x0:xs.max() + 1], [R - int(x0), R - int(y0)]

SIDE_RULE = {"bow": {"k": 0.6, "rot": 12, "minW": 7, "ws": [0.8, 1.25], "guard": [1, -1], "slot": "side_r"},
             "starclip": {"k": 0.42, "rot": -14, "minW": 7, "ws": [0.85, 1.15], "guard": [-1, -1], "slot": "side_l"},
             "sakura": {"k": 0.46, "rot": -10, "minW": 7, "ws": [0.85, 1.15], "guard": [-1, -1], "slot": "side_l"}}
def side_gen(key, W, L=False):
    if key == "bow": H = B.odd(W * 0.56, 5); m, piv = B.gen_bow(W, H); return m, piv, H
    if key == "starclip": H = W + 1; m, piv = B.gen_star(W, H); return m, piv, H
    H = W; m, piv = B.gen_sakura(W, H)
    if W >= 11:
        m2 = np.zeros((H + 3, W + 4), m.dtype); m2[:H, 3:3 + W] = m; sp = B.Spr(W + 4, H + 3); sp.m = m2
        sp.ell(1.6, H - 0.2, 1.6, 1.0, B.LEAF)
        if L == "bake": sp.ell(W + 2.2, H + 0.8, 1.3, 1.3, B.PINK)
        m, piv = sp.m, (piv[0] + 3, piv[1])
    return m, piv, H
def src_side(key):
    R_ = SIDE_RULE[key]; d = os.path.join(SRC, key); os.makedirs(d, exist_ok=True); mats = Mats(); it = base_item(key, R_["slot"])
    tg = [B.odd(form_idle(f)[1]["hw"] * R_["k"] * B.FIT[key][f]["sc"], R_["minW"]) for f in B.FORMS]
    sizes = ladder(tg); names = ["S", "M", "L"] if len(sizes) == 3 else ["S", "L"]
    back_repl = {"bow": {}, "starclip": {B.WHITE: B.GOLD}, "sakura": {B.GOLD: B.PINK}}[key]
    for nm, W in zip(names, sizes):
        m, piv, H = side_gen(key, W)
        bud = key == "sakura" and W >= 11                    # 花蕾＝part：只有 L 級 frame（S≥64）先加（同 baked 一樣）
        if bud and "bud" not in it["parts"]:
            sp = B.Spr(4, 4); sp.ell(2.2, 1.8, 1.3, 1.3, B.PINK); it["parts"]["bud"] = {"*": {"lab": save_lab(d, "part_bud", sp.m, mats), "pivot": [0, 0]}}
        for vn, mm, pv, an_ in (("front", m, piv, {"bud": (W, H - 1)}), ("side",) + squash(m, piv, 0.7, {"bud": (W, H - 1)}), ("back", back_of(m, back_repl), piv, {"bud": (W, H - 1)})):
            e_ = {"lab": save_lab(d, f"{vn}_{nm}", mm, mats), "w": W, "h": H, "pivot": [round(pv[0], 2), round(pv[1], 2)]}
            if bud: e_["anchors"] = {"bud": [round(an_["bud"][0], 2), an_["bud"][1]]}; e_["parts"] = [{"id": "bud", "at": "bud", "size": "*", "angK": 1.0, "sizeClass": ["L"]}]
            it["views"].setdefault(vn, {})[nm] = e_
    it["size"] = {"mode": "rel", "ref": "hw", "k": R_["k"], "minW": R_["minW"], "odd": True, "ws": R_["ws"]}
    it["place"] = {"anchor": R_["slot"], "rot": R_["rot"], "mirrorOnBack": True, "faceGuard": {"step": R_["guard"], "max": 6, "mirrorFlipX": True}}
    it["slotScaleFrom"] = "side_r"
    for f in B.FORMS:
        c = B.FIT[key][f]; base = SIDE_SC.get(f, 1.0); o = {}
        if abs(c["sc"] / base - 1) > 1e-6: o["sc"] = round(c["sc"] / base, 4)
        if c.get("dx"): o["dx"] = c["dx"]
        if c.get("dy"): o["dy"] = c["dy"]
        if o: it["formOverrides"][f] = o
    it["materials"] = mats.out; return it

GL_FRAME = B.mat("gl_frame", "orange_dd", "orange_dd", "orange_dd"); GL_INNER = B.mat("gl_inner", "orange_d", "orange_d", "orange_d")
GL_ARM = B.mat("gl_arm", "orange_dd", "orange_dd", "orange_dd"); GL_GLINT = B.mat("gl_glint", "white", "white", "white")
def lens_view(ax, ay, th, notch, fx, fy):
    """左鏡片（同 baked draw_glasses 一樣嘅橢圓框）：鏡心 (cx,cy)＝(M+fx, N+fy)；notch＝近口嗰角（+x 下）開口；鏡腳（bodyOnly）向 −x"""
    arm = 3 if th == 2 else 2; M = int(math.ceil(ax + th + arm + 1)); N = int(math.ceil(ay + th + 2))
    cx, cy = M + fx, N + fy; W = int(math.ceil(cx + ax + th + 1)) + 1; H = int(math.ceil(cy + ay + th + 1)) + 1
    yy, xx = np.mgrid[0:H, 0:W]; uu = xx - cx; vv = -(yy - cy)
    n0 = (uu / ax) ** 2 + (vv / ay) ** 2; n1 = (uu / (ax + th)) ** 2 + (vv / (ay + th)) ** 2
    ring = (n0 >= 1) & (n1 < 1)
    if notch: ring &= ~((vv < -0.25 * ay) & (uu > 0.2 * ax))
    m = np.zeros((H, W), np.int16); m[ring] = GL_FRAME
    if th == 2: m[ring & ((uu / (ax + 1)) ** 2 + (vv / (ay + 1)) ** 2 < 1)] = GL_INNER
    st = np.array([cx - (ax + th - .5), cy - ay * 0.35])
    for t in range(1, arm + 1):
        qx, qy = int(round(st[0] - t)), int(round(st[1] - t * 0.3))
        if 0 <= qx < W and 0 <= qy < H and not m[qy, qx]: m[qy, qx] = GL_ARM
    return m, (cx, cy)
def lens_key(ax, ay, th, notch, fx, fy): return f"{ax:g}_{ay:g}_t{th}_{'n' if notch else 'o'}_{fx:g}_{fy:g}"
LENS_AX = [x / 2 for x in range(2, 13)]; LENS_AY = [y / 2 for y in range(1, 12)]
def src_glasses():
    """眼鏡＝鏡片 ladder（一張 sheet）＋引擎畫鼻橋／反光：任何眼距都用同一套鏡片（唔使逐眼距畫）"""
    d = os.path.join(SRC, "glasses"); os.makedirs(d, exist_ok=True); mats = Mats(); it = base_item("glasses", "face")
    it["render"] = {"outline": False, "shade": False}
    extra = {GL_ARM: {"bodyOnly": True}, GL_GLINT: {"bodyOnly": True}}
    cells = []
    for th in (1, 2):
        for notch in (True, False):
            for ax in LENS_AX:
                for ay in LENS_AY:
                    if not notch and (ax > 3 or ay > 2.5): continue        # 額頭版只用細圈
                    for fx in (0, .5):
                        for fy in (0, .5):
                            m, piv = lens_view(ax, ay, th, notch, fx, fy); cells.append((lens_key(ax, ay, th, notch, fx, fy), m, piv))
    cw = max(m.shape[1] for _, m, _ in cells) + 1; ch = max(m.shape[0] for _, m, _ in cells) + 1; cols = 32
    rows = (len(cells) + cols - 1) // cols; sheet = np.zeros((rows * ch, cols * cw), np.int16); idx = {}
    for i, (k, m, piv) in enumerate(cells):
        X, Y = (i % cols) * cw, (i // cols) * ch; sheet[Y:Y + m.shape[0], X:X + m.shape[1]] = m
        idx[k] = [X, Y, m.shape[1], m.shape[0], piv[0], piv[1]]
    tmp = np.zeros((3, 3), np.int16); tmp[1, 1] = GL_GLINT; save_lab(d, "_glint", tmp, mats, extra)
    it["lens"] = {"sheet": save_lab(d, "lens_sheet", sheet, mats, extra), "index": idx, "ax": LENS_AX, "ay": LENS_AY,
                  "frameKey": mats.k(GL_FRAME), "glintKey": mats.k(GL_GLINT, extra[GL_GLINT]),
                  "note": "key＝{ax}_{ay}_t{th}_{n|o}_{fx}_{fy}；rect＝[x,y,w,h,pivotX,pivotY]（左鏡片；右鏡片＝水平鏡像）。ax/ay 向下取 0.5 格，鏡心 frac 取 0／0.5"}
    os.remove(os.path.join(d, "lab__glint.png")); os.remove(os.path.join(d, "_glint.png"))
    # 展示用 front view（M：ax3 ay3.5，D10）：兩片＋鼻橋，畀美術／文件睇
    mL, pL = lens_view(3, 3.5, 1, True, .5, 0); W = mL.shape[1] * 2 + 2; demo = np.zeros((mL.shape[0], W), np.int16)
    demo[:, :mL.shape[1]] = mL; demo[:, W - mL.shape[1]:] = np.maximum(demo[:, W - mL.shape[1]:], mL[:, ::-1])
    save_lab(d, "front_demo", demo, mats, extra)
    it["views"] = {"front": {"demo": {"lab": "lab_front_demo.png", "w": W, "h": mL.shape[0], "pivot": [W / 2 - .5, pL[1]], "demoOnly": True}}}
    it["retry"] = [list(a) for a in B.GL_RETRY]
    it["glasses"] = {"rLens": "ax＝bx+1.5+r+drx，ay＝by+1.5+r+dry（r＝formOverrides.r）", "bridgeY": 0.35, "glintMinR": 3.5, "glintK": 0.62,
                     "forehead": {"ay": 1.5, "axMax": 2.5, "aboveEye": 2.5, "onBodyMin": B.FH_MIN}}
    for f in B.FORMS:
        c = B.FIT["glasses"][f]
        if c.get("r"): it["formOverrides"].setdefault(f, {})["r"] = c["r"]
    it["size"] = {"mode": "eyes", "rule": "逐 clip 試 retry（收窄／壓扁／上移／向外／逐幀跟眼）；鏡片由 ladder 揀（ax/ay 向下取 0.5）；兩片各自貼眼心、跟眼線轉；鼻橋引擎畫"}
    it["place"] = {"anchor": "face"}
    it["materials"] = mats.out; return it

def src_scarf():
    d = os.path.join(SRC, "scarf"); os.makedirs(d, exist_ok=True); mats = Mats(); it = base_item("scarf", "neck")
    tile = np.array([[B.WHITE if (c // 2) % 3 == 0 else B.RED for c in range(6)] for _ in range(6)], np.int16)
    it["neck"] = {"mode": "stripe", "tile": {"lab": save_lab(d, "band_tile", tile, mats), "period": 6, "note": "列 c＝(x−xl) mod 6；行數＝attach slots.neck.thRef＋formOverrides.th"},
                  "tail": {"sizes": {}}, "lag": True}
    for th in (2, 3, 4, 5):
        tw = max(2, th); tl = th * 2 + 1; tm = np.full((tl, tw), B.RED, np.int16); tm[tl - 2:] = B.WHITE
        it["neck"]["tail"]["sizes"][str(th)] = {"lab": save_lab(d, f"part_tail_th{th}", tm, mats)}
    for f in B.FORMS:
        c = B.FIT["scarf"][f]; o = {k: v for k, v in c.items() if v}
        if o: it["formOverrides"][f] = o
    it["views"] = {"front": {"S": {"lab": it["neck"]["tile"]["lab"], "w": 6, "h": 6, "pivot": [0, 0]}}}
    it["place"] = {"anchor": "neck"}; it["faceClear"] = True; it["materials"] = mats.out; return it
def src_leafcollar():
    d = os.path.join(SRC, "leafcollar"); os.makedirs(d, exist_ok=True); mats = Mats(); it = base_item("leafcollar", "neck")
    it["neck"] = {"mode": "leaves", "leaf": {}, "flower": {}, "flowerAt": 0.26}
    for cls, lw in (("S", 3), ("M", 4), ("L", 5)):
        shape = {3: ["xxx", "xxx", ".x."], 4: ["xxxx", "xxxx", ".xx.", ".x.."], 5: ["xxxxx", "xxxxx", ".xxxx", "..xx.", "..x.."]}[lw]
        t = np.zeros((lw, 2 * lw), np.int16)
        for i, c in ((0, B.LEAFB), (1, B.LEAFA)):
            sh = shape if i == 0 else [r[::-1] for r in shape]
            for yy, row in enumerate(sh[:lw]):
                for xx, ch in enumerate(row):
                    if ch == "x": t[yy, i * lw + xx] = c
        it["neck"]["leaf"][cls] = {"lab": save_lab(d, f"leaf_tile_{cls}", t, mats), "lw": lw}
        n = 5 if cls == "L" else 3; fm = np.zeros((n, n), np.int16); c0 = n // 2
        pet = [(-1, 0), (1, 0), (0, -1), (0, 1)] + ([(-1, -1), (1, -1), (-1, 1), (1, 1)] if cls != "S" else [])
        for dx, dy in pet: fm[c0 + dy, c0 + dx] = B.PINK
        if cls == "L":
            for dx, dy in ((0, -2), (-2, 0), (2, 0), (0, 2)): fm[c0 + dy, c0 + dx] = B.PINK
        fm[c0, c0] = B.GOLD
        it["neck"]["flower"][cls] = {"lab": save_lab(d, f"flower_{cls}", fm, mats), "pivot": [c0, c0], "dy": 1 if cls == "S" else 2}
    for f in B.FORMS:
        c = B.FIT["leafcollar"][f]; o = {k: v for k, v in c.items() if v}
        if o: it["formOverrides"][f] = o
    it["views"] = {"front": {"S": {"lab": it["neck"]["leaf"]["S"]["lab"], "w": 6, "h": 3, "pivot": [0, 0]}}}
    it["place"] = {"anchor": "neck"}; it["faceClear"] = True; it["materials"] = mats.out; return it
def src_bell():
    d = os.path.join(SRC, "bell"); os.makedirs(d, exist_ok=True); mats = Mats(); it = base_item("bell", "bulb")
    for cls, n in (("S", 5), ("M", 7), ("L", 9)):
        m = np.array([[B.BELL_LAB[c] for c in r] for r in B.BELL_TPL[n]], np.int16)
        for vn, mm in (("front", m), ("side", m), ("back", back_of(m, {B.WHITE: B.GOLD}))):
            it["views"].setdefault(vn, {})[cls] = {"lab": save_lab(d, f"{vn}_{cls}", mm, mats), "w": n, "h": m.shape[0], "pivot": [(n - 1) / 2, 0]}
    it["size"] = {"mode": "class", "rule": "S≤32→5px、≤48→7px、64→9px（唔縮放）"}
    it["place"] = {"anchor": "hang", "faceGuard": {"step": [1, -1], "max": 6}}
    it["swing"] = {"src": "bulb", "kx": 7.0, "ky": 0.0, "decay": 0.5, "lim": 25.0, "maxd": 14.0, "apply": "item"}
    for f in B.FORMS:
        c = B.FIT["bell"][f]; o = {k: v for k, v in c.items() if v}
        if o: it["formOverrides"][f] = o
    it["materials"] = mats.out; return it
def src_halo():
    d = os.path.join(SRC, "halo"); os.makedirs(d, exist_ok=True); mats = Mats(); it = base_item("halo", "bulb")
    extra = {B.HALOH: {"hole": True}}
    for rx in [3.5 + 0.5 * i for i in range(8)]:
        ry = max(1.6, rx * 0.4); m, piv = B.gen_halo(rx, ry, L=rx >= 6); nm = f"rx{rx:g}"
        it["views"].setdefault("front", {})[nm] = {"lab": save_lab(d, f"front_{nm}", m, mats, extra), "w": m.shape[1], "h": m.shape[0], "pivot": [piv[0], piv[1]],
                                                   "halo": {"rx": rx, "ry": round(ry, 2)}}
    it["size"] = {"mode": "halo", "rule": "rx＝attach bulb.fw/2 × sc，揀最近一級（0.5px 一級；環唔縮放）；中心＝浮點＋u·ry"}
    it["place"] = {"anchor": "float", "clampTop": True}
    for f in B.FORMS:
        c = B.FIT["halo"][f]; o = {k: v for k, v in c.items() if v and not (k == "sc" and v == 1.0)}
        if o: it["formOverrides"][f] = o
    it["materials"] = mats.out; return it
def head_overrides(it, key):
    for f in B.FORMS:
        c = B.FIT[key][f]; base = HEAD_SC.get(f, 1.0); o = {}
        if f not in B.HATFORMS and abs(c["sc"] / base - 1) > 1e-6: o["sc"] = round(c["sc"] / base, 4)
        if c.get("dx"): o["dx"] = c["dx"]
        if c.get("dy"): o["dy"] = c["dy"]
        if o: it["formOverrides"][f] = o
def build_sources(keys=None):
    out = {}
    for key in keys or list(B.ITEMS):
        if key in B.HEAD: it = src_head(key); head_overrides(it, key)
        elif key in SIDE_RULE: it = src_side(key)
        elif key == "glasses": it = src_glasses()
        elif key == "scarf": it = src_scarf()
        elif key == "leafcollar": it = src_leafcollar()
        elif key == "bell": it = src_bell()
        elif key == "halo": it = src_halo()
        p = os.path.join(SRC, key, "item.json")
        if os.path.exists(p):   # 保留 compare 寫入嘅 formOverrides（data-only 修正）
            old = json.load(open(p))
            for f, o in old.get("formOverrides", {}).items():
                if o.get("auto"): it["formOverrides"].setdefault(f, {}).update(o)
        json.dump(it, open(p, "w"), ensure_ascii=False, indent=1); out[key] = {k: sorted(v) for k, v in it["views"].items()}
        print("source", key, out[key], flush=True)
    return out

# ================================================================ ④ compare（runtime vs baked atlas）
def baked_layers(item, form):
    """baked atlas → {frame: RGBA (S+2PAD)²}（用 spriteSourceSize 還原）＋ hiddenClips"""
    p = os.path.join(ACCD, "items", item, f"atlas_{item}_{form}"); j = json.load(open(p + ".json")); atl = np.array(Image.open(p + ".png").convert("RGBA"))
    S = j["meta"]["frameSize"]; out = {}
    for n, e in j["frames"].items():
        fr = e["frame"]; ss = e["spriteSourceSize"]; can = np.zeros((S + 2 * PAD, S + 2 * PAD, 4), np.uint8)
        can[ss["y"] + PAD:ss["y"] + PAD + fr["h"], ss["x"] + PAD:ss["x"] + PAD + fr["w"]] = atl[fr["y"]:fr["y"] + fr["h"], fr["x"]:fr["x"] + fr["w"]]
        out[n] = can
    return out, j["hiddenClips"]
def frame_metrics(a, b):
    """a＝runtime、b＝baked（RGBA）：IoU、重心距離、面積比、像素差 %（聯集內 RGBA 唔同）"""
    ma, mb = a[..., 3] > 0, b[..., 3] > 0; u = ma | mb; i = ma & mb; nu = int(u.sum())
    if not nu: return {"iou": 1.0, "cd": 0.0, "ar": 1.0, "diff": 0.0}
    ya, xa = np.nonzero(ma); yb, xb = np.nonzero(mb)
    cd = float(math.hypot(xa.mean() - xb.mean(), ya.mean() - yb.mean())) if len(xa) and len(xb) else 99.0
    same = i & np.all(a == b, -1)
    return {"iou": round(i.sum() / nu, 3), "cd": round(cd, 2), "ar": round(ma.sum() / max(1, mb.sum()), 3), "diff": round(1 - same.sum() / nu, 3),
            "dxy": [round(float(xa.mean() - xb.mean()), 2), round(float(ya.mean() - yb.mean()), 2)] if len(xa) and len(xb) else [0, 0]}
def acceptable(m): return m["cd"] <= 2.0 and 0.6 <= m["ar"] <= 1.67 and m["iou"] >= 0.45
def compare_item_form(item, form, C):
    """回傳 per-clip 結果 list"""
    bk, bhid = baked_layers(item, form); A = attach(form) if False else C.attach(form); res = []
    for clip, c in A["clips"].items():
        L_, info = C.clip_layers(item, form, clip)
        rt_vis = L_ is not None; bk_vis = clip not in bhid
        r = {"clip": clip, "n": c["n"], "rt": rt_vis, "bk": bk_vis, "why_rt": None if rt_vis else info, "why_bk": bhid.get(clip)}
        if rt_vis and bk_vis:
            ms = [frame_metrics(L_[k], bk[f"{clip}_{k + 1:02d}"]) for k in range(c["n"])]; r["m"] = ms
        res.append(r)
    return res
def attach(form): return json.load(open(os.path.join(ATT, f"{form}.json")))

def _cmp_stats(res):
    fr = [m for r in res if "m" in r for m in r["m"]]
    return {"clips": len(res), "visAgree": sum(r["rt"] == r["bk"] for r in res), "frames": len(fr), "ok": sum(acceptable(m) for m in fr),
            "diffSum": float(sum(m["diff"] for m in fr)), "iouSum": float(sum(m["iou"] for m in fr))}
def run_compare(items=None, forms=None, autofix=True):
    """13 件 × 25 形態：runtime vs baked。autofix：ok < 95% 而且 dxy 中位數 ≥1px → 寫 formOverrides dx/dy（auto）；改完更差就還原。
    嚴重（cd>4）嘅 clip 只列入 out["severe"] 俾人手睇（唔自動 hide）"""
    import compose_accessory_runtime as C
    items = items or [k for k in B.ITEMS]; forms = forms or list(B.FORMS); out = {"items": {}, "fixes": [], "criteria": "acceptable＝重心距離 ≤2px、面積比 0.6–1.67、IoU ≥0.45"}
    for it_ in items:
        p = os.path.join(SRC, it_, "item.json"); IT = json.load(open(p)); per = {}; probs = []; vis = []
        for f in forms:
            res = compare_item_form(it_, f, C); st = _cmp_stats(res)
            if autofix and st["frames"] and st["ok"] < 0.95 * st["frames"]:
                d = np.array([m["dxy"] for r in res if "m" in r for m in r["m"] if not acceptable(m)])
                if len(d):
                    mdx, mdy = [int(round(-v)) for v in np.median(d, 0)]
                    if (mdx or mdy) and max(abs(mdx), abs(mdy)) <= 3:
                        o = IT["formOverrides"].setdefault(f, {}); old = dict(o)
                        o["dx"] = o.get("dx", 0) + mdx; o["dy"] = o.get("dy", 0) + mdy; o["auto"] = True
                        json.dump(IT, open(p, "w"), ensure_ascii=False, indent=1); C._ITEM.pop(it_, None); C._CL.clear()
                        res2 = compare_item_form(it_, f, C); st2 = _cmp_stats(res2)
                        if st2["ok"] > st["ok"] and st2["visAgree"] >= st["visAgree"]:
                            out["fixes"].append({"item": it_, "form": f, "dx": mdx, "dy": mdy, "okBefore": st["ok"], "okAfter": st2["ok"], "frames": st["frames"]}); res, st = res2, st2
                        else:
                            IT["formOverrides"][f] = old
                            if not old: IT["formOverrides"].pop(f)
                            json.dump(IT, open(p, "w"), ensure_ascii=False, indent=1); C._ITEM.pop(it_, None); C._CL.clear()
            sev = [r["clip"] for r in res if "m" in r and any(m["cd"] > 4 for m in r["m"])]
            if sev: out.setdefault("severe", []).append({"item": it_, "form": f, "clips": sev})   # cd>4：要人眼睇（多數係 baked 自己飄／傾側裁切），唔自動收
            per[f] = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in st.items()}
            for r in res:
                if r["rt"] != r["bk"]: vis.append({"form": f, "clip": r["clip"], "runtime": r["rt"], "baked": r["bk"], "whyRuntime": r["why_rt"], "whyBaked": r["why_bk"]})
                for k, m in enumerate(r.get("m", []), 1):
                    if not acceptable(m): probs.append({"form": f, "frame": f"{r['clip']}_{k:02d}", **{kk: (float(vv) if not isinstance(vv, list) else vv) for kk, vv in m.items()}})
            print("compare", it_, f, per[f]["ok"], "/", per[f]["frames"], "vis", per[f]["visAgree"], "/", per[f]["clips"], flush=True)
        T = {k: sum(v[k] for v in per.values()) for k in ("clips", "visAgree", "frames", "ok", "diffSum", "iouSum")}
        out["items"][it_] = {"clips": T["clips"], "visAgree": T["visAgree"], "visAgreePct": round(100 * T["visAgree"] / max(1, T["clips"]), 2),
                             "frames": T["frames"], "okFrames": T["ok"], "okPct": round(100 * T["ok"] / max(1, T["frames"]), 2),
                             "meanPixelDiffPct": round(100 * T["diffSum"] / max(1, T["frames"]), 2), "meanIoU": round(T["iouSum"] / max(1, T["frames"]), 3),
                             "perForm": per, "problemFrames": probs, "visibilityMismatch": vis}
    json.dump(out, open(os.path.join(ACCD, "RUNTIME_COMPARE.json"), "w"), ensure_ascii=False, indent=1, default=lambda o: o.item())
    return out

# ================================================================ ⑤ 新 item 試驗：櫻桃髮夾（只畫 3 view；跑 runtime 就套晒 25 形態）
CHERRY_W = {"S": 9, "M": 13, "L": 17}
def gen_cherry_clip(W):
    """髮夾本體（唔連櫻桃）：深莓色夾片＋兩塊葉＋莖頭結；回傳 m, pivot（夾片中心）, hang（掛櫻桃嘅點）"""
    c = (W - 1) / 2; H = max(4, int(round(W * 0.42))); s = B.Spr(W, H)
    bw = max(2, int(round(W * 0.22)))
    s.rect(int(round(c)) - bw, H - 2, int(round(c)) + bw, H - 1, B.REDD)            # 夾片（貼頭嗰塊）
    lr = max(1.3, W * 0.2); s.ell(c + lr * 0.95, H * 0.42, lr, max(1.0, lr * 0.55), B.LEAF)   # 右葉
    s.ell(c - lr * 0.7, H * 0.5, lr * 0.75, max(.9, lr * 0.45), B.LEAF)               # 左細葉
    if W >= 13: s.line(c + 0.4, H * 0.42, c + lr * 1.7, H * 0.3, B.LEAFD)               # 葉脈
    s.px(c, H - 3, B.LEAFD)                                                            # 莖頭結
    return s.m, (c, H - 1.5), (c, H - 2)
def gen_cherry_dangle(W):
    """吊墜 part：兩條莖＋兩粒櫻桃（pivot＝莖頂，擺動轉軸）"""
    r = max(1.4, W * 0.17); h = int(math.ceil(W * 0.42 + 2 * r + 1)); w = W + 2; c = (w - 1) / 2; s = B.Spr(w, h)
    L_ = (c - W * 0.24, h - r - 0.6); R_ = (c + W * 0.2, h - r - 1.6)
    for p in (L_, R_): s.line(c, 0, p[0], p[1] - r + 0.4, B.LEAFD)
    for p in (L_, R_): s.ell(p[0], p[1], r, r, B.RED)
    if W >= 13:
        for p in (L_, R_): s.px(p[0] - r * 0.45, p[1] - r * 0.45, B.WHITE)            # 反光
    return s.m, (c, 0.0)
def src_cherry():
    key = "cherry"; d = os.path.join(SRC, key); os.makedirs(d, exist_ok=True); mats = Mats(); it = base_item(key, "side_r")
    it["name"] = "櫻桃髮夾"; it["version"] = 1; it["new"] = True
    it["yield"] = {"priority": 3.5, "steps": [list(s_) for s_ in B.YIELD_STEPS["bow"]], "coverMax": B.COVER_MAX, "floatOk": False, "anyOverlap": False}
    it["parts"]["dangle"] = {}
    for nm, W in CHERRY_W.items():
        m, piv, hang = gen_cherry_clip(W); dm, dp = gen_cherry_dangle(W)
        it["parts"]["dangle"][nm] = {"lab": save_lab(d, f"part_dangle_{nm}", dm, mats), "pivot": [round(dp[0], 2), dp[1]]}
        sm, sp_, sa = squash(m, piv, 0.7, {"hang": hang})
        bm = back_of(m, {B.LEAF: B.LEAFD})                     # 背面：葉底深一級，夾片照見
        for vn, mm, pv, hg in (("front", m, piv, hang), ("side", sm, sp_, sa["hang"]), ("back", bm, piv, hang)):
            it["views"].setdefault(vn, {})[nm] = {"lab": save_lab(d, f"{vn}_{nm}", mm, mats), "w": W, "h": mm.shape[0], "pivot": [round(pv[0], 2), round(pv[1], 2)],
                                                 "anchors": {"hang": [round(hg[0], 2), hg[1]]}, "parts": [{"id": "dangle", "at": "hang", "angK": 1.0}]}
    it["size"] = {"mode": "rel", "ref": "hw", "k": 0.5, "minW": 7, "odd": True, "ws": [0.85, 1.15]}
    it["place"] = {"anchor": "side_r", "rot": 8, "mirrorOnBack": True, "faceGuard": {"step": [1, -1], "max": 6, "mirrorFlipX": True}}
    it["slotScaleFrom"] = "side_r"
    it["swing"] = {"src": "side_r", "kx": 6.0, "ky": 3.0, "decay": 0.55, "lim": 28.0, "maxd": 14.0, "apply": "dangle", "gain": 1.0}
    it["partFallback"] = [{"rot": r_, "scale": s_} for s_ in (1.0, 0.8) for r_ in (0, 12, -12, 24)]
    it["materials"] = mats.out
    json.dump(it, open(os.path.join(d, "item.json"), "w"), ensure_ascii=False, indent=1); return it

# ================================================================ ⑥ previews（3x）
def _cell(img, box, bg=(236, 232, 226)):
    h, w = img.shape[:2]; c = np.zeros((box, box, 4), np.uint8); c[..., :3] = bg; c[..., 3] = 255
    y0, x0 = (box - h) // 2, (box - w) // 2; m = img[..., 3] > 0; c[y0:y0 + h, x0:x0 + w][m] = img[m]; return c
def _label(arr, text, h=14):
    from PIL import ImageDraw
    im = Image.fromarray(arr); can = Image.new("RGBA", (im.width, im.height + h), (255, 255, 255, 255)); can.paste(im, (0, h))
    ImageDraw.Draw(can).text((3, 1), text, fill=(40, 30, 40, 255)); return np.array(can)
def build_previews(sc=3):
    import compose_accessory_runtime as C
    os.makedirs(PREVR, exist_ok=True); made = []; box = 80
    # ① 櫻桃髮夾 × 25 形態：idle／walk／sleep_loop／turn_back（逐幀，一行一個形態）
    for clip in ("idle", "walk", "sleep_loop", "turn_back"):
        rows = []
        for f in B.FORMS:
            A = C.attach(f); c = A["clips"].get(clip); use = clip
            if c is None: use = "idle"; c = A["clips"]["idle"]                       # lumi 冇 turn_back → 用 idle 頂（標明）
            cells = []
            for k in range(1, c["n"] + 1):
                im, hid = C.compose(f, use, k, ["cherry"], with_emissive=True); cells.append(_cell(im, box))
            row = np.concatenate(cells + [np.full((box, box * (8 - len(cells)), 4), 255, np.uint8)] if len(cells) < 8 else cells[:8], 1)
            rows.append(_label(np.array(Image.fromarray(row).resize((row.shape[1] * sc, row.shape[0] * sc), Image.NEAREST)),
                               f"{f}  {use}{'' if use == clip else ' (no ' + clip + ' clip -> idle shown)'}  {'HIDDEN: ' + str(hid.get('cherry')) if hid.get('cherry') else ''}"))
        sheet = np.concatenate(rows, 0); p = os.path.join(PREVR, f"cherry_{clip}_25forms_3x.png"); Image.fromarray(sheet).save(p); made.append(p)
    # ② source 3 view × S/M/L（櫻桃）
    it = C.item("cherry"); cells = []
    for vn in ("front", "side", "back"):
        for nm in ("S", "M", "L"):
            L = C._canvas(24); e = it["views"][vn][nm]; m = C.lab(it, e); C.put(L, m, 10, 6)
            pe = it["parts"]["dangle"][nm]; pm = C.lab(it, pe); hx, hy = e["anchors"]["hang"]
            C.put(L, pm, 10 + int(round(hx - pe["pivot"][0])), 6 + int(round(hy - pe["pivot"][1])))
            cells.append(_cell(C.render(L, it), 42))
    sh = np.concatenate([np.concatenate(cells[i * 3:(i + 1) * 3], 1) for i in range(3)], 0)
    p = os.path.join(PREVR, "cherry_source_views_SML_6x.png"); Image.fromarray(sh).resize((sh.shape[1] * 6, sh.shape[0] * 6), Image.NEAREST).save(p); made.append(p)
    # ③ runtime vs baked：每件 idle_01 × 25 形態（左 runtime｜右 baked）
    for key in B.ITEMS:
        cells = []
        for f in B.FORMS:
            bk, bh = baked_layers(key, f); L_, inf = C.clip_layers(key, f, "idle"); bd = C.body(f, "idle", 1); S = bd.shape[0]
            def comp(o):
                c = np.zeros((S + 2 * PAD, S + 2 * PAD, 4), np.uint8); c[PAD:PAD + S, PAD:PAD + S] = bd
                if o is not None: m = o[..., 3] > 0; c[m] = o[m]
                return c
            pair = np.concatenate([_cell(comp(L_[0] if L_ is not None else None), box), np.full((box, 3, 4), 255, np.uint8), _cell(comp(bk.get("idle_01")), box, bg=(222, 228, 236)), np.full((box, 6, 4), 255, np.uint8)], 1)
            cells.append(_label(np.array(Image.fromarray(pair).resize((pair.shape[1] * sc, pair.shape[0] * sc), Image.NEAREST)), f"{f}  runtime | baked"))
        cols = 5; w = cells[0].shape[1]; rows = []
        for i in range(0, len(cells), cols):
            r = cells[i:i + cols]; r += [np.full_like(cells[0], 255)] * (cols - len(r)); rows.append(np.concatenate(r, 1))
        p = os.path.join(PREVR, f"compare_{key}_idle_25forms_3x.png"); Image.fromarray(np.concatenate(rows, 0)).save(p); made.append(p)
    # ④ 多件即場解 combos（walk）
    for f, worn in (("sprout", ["straw", "glasses", "scarf", "cherry"]), ("evo_guard_radiant", ["crown", "glasses", "leafcollar", "bell", "cherry"]),
                    ("evo_still_moon", ["nightcap", "sakura", "scarf", "cherry"]), ("evo_hop", ["halo", "bow", "glasses", "scarf"]), ("evo_still_ember", ["beanie", "starclip", "cherry", "leafcollar"])):
        for clip in ("idle", "walk", "turn_back"):
            c = C.attach(f)["clips"][clip]; cells = []; hid = {}
            for k in range(1, c["n"] + 1):
                im, hid = C.compose(f, clip, k, worn, with_emissive=True); cells.append(_cell(im, box))
            row = np.concatenate(cells, 1); row = np.array(Image.fromarray(row).resize((row.shape[1] * sc, row.shape[0] * sc), Image.NEAREST))
            p = os.path.join(PREVR, f"combo_{f}_{'+'.join(worn)}_{clip}_3x.png"); Image.fromarray(_label(row, f"{f} {clip} {'+'.join(worn)}  hidden={hid}")).save(p); made.append(p)
    return made

def write_compare_md():
    r = json.load(open(os.path.join(ACCD, "RUNTIME_COMPARE.json"))); L = []
    tf = sum(v["frames"] for v in r["items"].values()); to = sum(v["okFrames"] for v in r["items"].values())
    tc = sum(v["clips"] for v in r["items"].values()); tv = sum(v["visAgree"] for v in r["items"].values())
    L += ["# 團絨飾品 runtime vs baked 對照（13 件 × 25 形態）", "",
          "由 `tools/build_accessory_runtime.py run_compare` 生成；數據：`RUNTIME_COMPARE.json`。", "",
          f"- 準則：{r['criteria']}",
          "- pixelDiff%＝（runtime ∪ baked 嘅 alpha 像素入面，顏色唔同嘅比例）。runtime 係用 label-map 即場 render，高光／陰影位同手調 baked 唔會逐粒一樣，所以呢個數一般 15–40%；**判斷合格睇 okPct／IoU，唔睇 pixelDiff**。",
          "- visAgree＝成個 clip 「畫／收起」決定同 baked 一致嘅比例。", "",
          f"**總計：{to}/{tf} 幀合格（{100 * to / tf:.2f}%）；clip 可見性一致 {tv}/{tc}（{100 * tv / tc:.2f}%）**", "",
          "| 件 | clips | 可見性一致 | 幀 | 合格幀 | ok% | mean pixelDiff% | mean IoU | 問題幀 | 可見性唔同 |", "|---|---|---|---|---|---|---|---|---|---|"]
    for k, v in r["items"].items():
        L.append(f"| {k} | {v['clips']} | {v['visAgree']} ({v['visAgreePct']}%) | {v['frames']} | {v['okFrames']} | {v['okPct']} | {v['meanPixelDiffPct']:.2f} | {v['meanIoU']:.3f} | {len(v['problemFrames'])} | {len(v['visibilityMismatch'])} |")
    L += ["", f"自動修正（formOverrides dx/dy）：{len(r['fixes'])} 個" + ("" if r["fixes"] else "（冇需要：每個 item×form 都 ≥95% 或者偏移唔一致）"), ""]
    L += ["## 人手審閱結論", "",
          "- **nightcap**：嚴重幀（cd≈7px，evo_dot wake／catch_reach／turn_back／lookup_tip／getup；evo_still_radiant sleep_loop 等）——baked atlas 個帽浮咗喺頭頂上 ~7px，runtime 跟 fit 頂點貼頭，**runtime 先啱**；列為 baked outlier，冇改 data。",
          "- **scarf**：soft／radiant lookup_tip、evo_guard_moon sneeze——baked 用斜切 shear，runtime 用整數角旋轉，邊緣裁法唔同（cd 2.5–4.8px），睇落可接受。",
          "- **glasses**：鏡片改用 lens ladder＋retry 之後 ~97%；21 個 clip runtime 收起（「鏡框會壓到眼」／「眼距太窄（側面）」），屬保守：寧願唔戴都唔壓眼。剩低問題幀多數係 wake／blink 閉眼幀 IoU 低（鏡片細咗 1 級），中心冇偏。",
          "- **bow**：5 個 clip（play_05／rush_03 喺幾隻 evo 形態）runtime 判「會遮五官」收起——nearest 放大 L 款（17→19）比 baked 原生 size 大少少；接受（保守）。evo_still_radiant 一組 cd≈2.5px 情緒幀屬同一原因。",
          "- **halo**：4 幀 1px 垂直差（光環梯級 round 邊界），可接受。", ""]
    if r.get("severe"):
        L += ["## 嚴重（cd>4）clip 清單", "", "| 件 | 形態 | clips |", "|---|---|---|"] + [f"| {s['item']} | {s['form']} | {', '.join(s['clips'])} |" for s in r["severe"]] + [""]
    L += ["## 問題幀（每件最多 40 行；全數見 JSON）", ""]
    for k, v in r["items"].items():
        if not v["problemFrames"] and not v["visibilityMismatch"]: continue
        L += [f"### {k}", ""]
        if v["problemFrames"]:
            L += ["| 形態 | 幀 | IoU | cd | 面積比 | dxy |", "|---|---|---|---|---|---|"]
            L += [f"| {p['form']} | {p['frame']} | {p['iou']} | {p['cd']} | {p['ar']} | {p['dxy']} |" for p in v["problemFrames"][:40]]
            if len(v["problemFrames"]) > 40: L.append(f"| … | 另外 {len(v['problemFrames']) - 40} 幀 | | | | |")
            L.append("")
        if v["visibilityMismatch"]:
            L += ["可見性唔同：", ""] + [f"- {m['form']} {m['clip']}：runtime={'畫' if m['runtime'] else '收'}（{m['whyRuntime']}）／baked={'畫' if m['baked'] else '收'}（{m['whyBaked']}）" for m in v["visibilityMismatch"]] + [""]
    open(os.path.join(ACCD, "RUNTIME_COMPARE.md"), "w").write("\n".join(L) + "\n")
    return to, tf, tv, tc

# ================================================================ ⑦ 新形態（data-only 擴充）
ANCHOR_SCHEMA = {"eyeL": "[x,y] int，必須（冇眼可以用 grab）", "eyeR": "[x,y] int，必須", "mouth": "[x,y] int（頸線用；冇就用頭高估）",
                 "head_r": "[x,y] int，頭右上邊（耳邊飾／側飾）", "bulb": "[x,y] int，可選（燈泡；冇就光環／鈴用頭頂）", "bulb2": "[x,y] 可選第二發光點",
                 "faceVisible": "bool，背面幀 false"}
EXTRA_P = os.path.join(ATT, "FORMS_EXTRA.json")
EXTRA_KEYS = {"frameDir": "幀資料夾（相對 art-pet 或者絕對），檔名 <clip>_<kk>.png", "anchors": "anchors json（{\"anchors\": {clip: [每幀 anchor]}}），相對 art-pet 或者絕對",
              "animations": "可選 {clip: {fps, loop}}", "emissiveDir": "可選 <clip>_<kk>_emissive.png 資料夾", "bulbR": "可選，燈泡玻璃半徑（預設 2.5）",
              "glassesForehead": "可選 bool：眼同口太近 → 眼鏡推上額頭", "pinSide": "可選 r/l：頭飾改用帽針（頭頂有大物件嘅形態）",
              "headSc": "可選 頭飾縮放", "sideSc": "可選 側飾縮放", "axisFromEyes": "可選 bool：燈泡唔喺頭頂（觸角／尾燈）→ 頭軸用眼線",
              "species": "可選 資料", "route": "可選", "stage": "可選"}
_EXTRA = {}
def _ap(p): return p if os.path.isabs(p) else os.path.join(ART, p)
def load_extra(path=None):
    p = path or EXTRA_P
    return json.load(open(p))["forms"] if os.path.exists(p) else {}
def register_forms(extra):
    """將 FORMS_EXTRA 嘅形態掛入 build_accessories 嘅查表（只喺記憶體，唔改 build_accessories.py）"""
    if not extra: return {}
    if not _EXTRA:
        oa, of, om, oe = B.anchors, B.frame_path, B.form_anims, B.emissive_path
        def anchors(form): return json.load(open(_ap(_EXTRA[form]["anchors"])))["anchors"] if form in _EXTRA else oa(form)
        def frame_path(form, clip, k): return os.path.join(_ap(_EXTRA[form]["frameDir"]), f"{clip}_{k:02d}.png") if form in _EXTRA else of(form, clip, k)
        def form_anims(form): return dict(_EXTRA[form].get("animations", {})) if form in _EXTRA else om(form)
        def emissive_path(form, n):
            if form not in _EXTRA: return oe(form, n)
            d = _EXTRA[form].get("emissiveDir"); return os.path.join(_ap(d), f"{n}_emissive.png") if d else None
        B.anchors, B.frame_path, B.form_anims, B.emissive_path = anchors, frame_path, form_anims, emissive_path
    for form, e in extra.items():
        if form in B.FORMS: raise SystemExit(f"FORMS_EXTRA：{form} 同正式形態撞名")
        for k in ("frameDir", "anchors"):
            if k not in e: raise SystemExit(f"FORMS_EXTRA {form}：冇 {k}")
        _EXTRA[form] = e; B.BR[form] = e.get("bulbR", 2.5)
        for it_, tab in B.FIT.items():                     # 中性預設（dx/dy 0、sc 1）；之後要微調就寫 item.json formOverrides
            ref_ = next(iter(tab.values())); tab.setdefault(form, {k: (1.0 if k == "sc" else 0) for k in ref_ if k in ("dx", "dy", "sc", "r", "th")})
        B.FIT["glasses"][form] = {"r": 0.0, **({"forehead": True} if e.get("glassesForehead") else {})}
        if e.get("axisFromEyes"): B.AXIS[form] = "eyes"
        if e.get("pinSide"): PIN_SIDE[form] = e["pinSide"]
        if e.get("headSc"): HEAD_SC[form] = e["headSc"]
        if e.get("sideSc"): SIDE_SC[form] = e["sideSc"]
        B.TOPBULB.pop(form, None)
    return extra
SPECIES_MAP = {"eyeL": "eyeL", "eyeR": "eyeR", "mouth": "mouth", "headR": "head_r", "bulb": "bulb"}
def species_extra(route, stage, out_dir, species_json=None):
    """species_concept/species.json 一個 route×stage（idle 單幀概念）→ FORMS_EXTRA 一項＋anchors／frames 寫去 out_dir（唔寫入 species_concept）。
    將來有正式 motion frames 就直接用嗰啲 frames／anchors，呢個只係示範點樣 data-only 加形態。"""
    import shutil
    sj = species_json or os.path.join(ART, "sprites", "tuanrong", "species_concept", "species.json")
    sp = json.load(open(sj))["routes"][route][stage]; an = sp["anchors"]
    a = {SPECIES_MAP[k]: [int(round(v[0])), int(round(v[1]))] for k, v in an.items() if k in SPECIES_MAP}; a["faceVisible"] = True
    if "eyeL" not in a or "eyeR" not in a: return None, f"{route}/{stage}：冇 eyeL/eyeR anchor（要補先加得）"
    S_ = int(an.get("S") or Image.open(os.path.join(os.path.dirname(sj), sp["file"])).size[0]); extra = {}
    if "bulb" in a and not (0 <= a["bulb"][0] < S_ and 0 <= a["bulb"][1] < S_): a.pop("bulb"); extra["note"] = "bulb anchor 出 frame → 唔當燈泡"
    if "bulb" in a:
        em = ((a["eyeL"][0] + a["eyeR"][0]) / 2, (a["eyeL"][1] + a["eyeR"][1]) / 2); ex, ey = a["eyeR"][0] - a["eyeL"][0], a["eyeR"][1] - a["eyeL"][1]
        d = math.degrees(math.atan2(a["bulb"][0] - em[0], -(a["bulb"][1] - em[1])) - math.atan2(ey, ex))
        if abs((d + 180) % 360 - 180) > 40: extra["axisFromEyes"] = True        # 燈唔喺頭頂（側燈／尾燈）→ 頭軸用眼線
    form = f"sp_{route}_{stage}"; fd = os.path.join(out_dir, form); os.makedirs(fd, exist_ok=True)
    shutil.copyfile(os.path.join(os.path.dirname(sj), sp["file"]), os.path.join(fd, "idle_01.png"))
    json.dump({"anchors": {"idle": [a]}}, open(os.path.join(fd, "anchors.json"), "w"), ensure_ascii=False, indent=1)
    return form, {"frameDir": fd, "anchors": os.path.join(fd, "anchors.json"), "animations": {"idle": {"fps": 6, "loop": True}},
                  "species": json.load(open(sj))["routes"][route].get("species"), "route": route, "stage": stage, **extra}
def write_extra_example():
    ex = {"note": "複製做 FORMS_EXTRA.json 就會被 build_attach 讀入（新種族／新形態）。frames 檔名 <clip>_<kk>.png；anchors 每幀一個 dict。",
          "keys": EXTRA_KEYS, "anchorSchema": ANCHOR_SCHEMA,
          "forms": {"evo_guard_newkind": {"frameDir": "sprites/tuanrong/evo6/evo_guard_newkind/frames", "anchors": "sprites/tuanrong/evo6/evo_guard_newkind/face_anchors_evo_guard_newkind.json",
                                          "animations": {"idle": {"fps": 6, "loop": True}}, "emissiveDir": None, "bulbR": 2.5, "glassesForehead": False, "pinSide": None,
                                          "species": "（例）", "route": "newkind", "stage": "guard"}}}
    json.dump(ex, open(os.path.join(ATT, "FORMS_EXTRA.example.json"), "w"), ensure_ascii=False, indent=1)
def demo_species(out=None, routes=None, item_keys=("cherry", "straw", "glasses", "scarf", "bow", "halo")):
    """dry-run：species.json 全部 route × guard/still → 臨時 attach（/tmp）→ 用現有 item render；證明新形態只要 anchors 就得"""
    import compose_accessory_runtime as C
    out = out or "/tmp/attach_species_demo"; att = os.path.join(out, "attach"); os.makedirs(att, exist_ok=True)
    sj = os.path.join(ART, "sprites", "tuanrong", "species_concept", "species.json")
    if not os.path.exists(sj):
        print("species: 冇 species_concept/species.json（未合併）→ 略過 dry-run"); return None
    R = json.load(open(sj))["routes"]
    reg = {}; skipped = []
    for r in routes or list(R):
        for st in ("guard", "still"):
            if st not in R[r]: continue
            f, e = species_extra(r, st, os.path.join(out, "frames"))
            if f is None: skipped.append(e)
            else: reg[f] = e
    json.dump({"forms": reg}, open(os.path.join(out, "FORMS_EXTRA.json"), "w"), ensure_ascii=False, indent=1)
    build_attach(forms=list(reg), att=att, extra_path=os.path.join(out, "FORMS_EXTRA.json"))
    oatt = C.ATT; C.ATT = att; C._ATT.clear(); res = {}; rows = []
    try:
        for f in reg:
            cells = []; res[f] = {}
            for key in item_keys:
                im, hid = C.compose(f, "idle", 1, [key], with_emissive=False); res[f][key] = hid.get(key) or "ok"; cells.append(_cell(im, 80))
            row = np.concatenate(cells, 1); rows.append(_label(np.array(Image.fromarray(row).resize((row.shape[1] * 3, row.shape[0] * 3), Image.NEAREST)), f"{f}  " + " ".join(item_keys)))
    finally: C.ATT = oatt; C._ATT.clear(); C._CL.clear(); C._SOLVE.clear()
    p = os.path.join(PREVR, "species_extra_demo_3x.png"); Image.fromarray(np.concatenate(rows, 0)).save(p)
    json.dump({"rendered": res, "skipped": skipped}, open(os.path.join(out, "result.json"), "w"), ensure_ascii=False, indent=1)
    return p, res, skipped

if __name__ == "__main__":
    steps = sys.argv[1:] or ["all"]
    if "all" in steps: steps = ["attach", "sources", "cherry", "compare", "previews"]
    if "attach" in steps: build_attach()
    if "sources" in steps: build_sources()
    if "cherry" in steps: src_cherry()
    if "compare" in steps: run_compare(); print(write_compare_md())
    elif "md" in steps: print(write_compare_md())
    if "previews" in steps: print(len(build_previews()), "previews")
    if "species" in steps: print(demo_species())
    if "example" in steps or "attach" in steps: write_extra_example()
