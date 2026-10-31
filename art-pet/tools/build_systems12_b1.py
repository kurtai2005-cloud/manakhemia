#!/usr/bin/env python3
"""build_systems12_b1.py — systems12 第 1 批美術（docs-gdd/systems12-v1.md「遊美素材清單」第 1 批）。
Pillow + numpy 程式逐像素繪製，原創，無 AI；跟 v3 色盤（motion/palette.json 31 色＝evo6 palette_base.json），alpha 0/255、無 AA、朝右。

團絨兩個天氣 clip（全部體型，蛋除外）：
  leaf_umbrella（撐葉，落雨）6 幀 6fps loop（loopFrom 2）、shiver（打冷震，冬天／大風）4 幀 10fps loop。
  片葉喺 extras 入面「只畫落空白像素」→ 永遠喺身後，唔遮面、唔遮燈（燈／臉 kit 照舊）。
子命令（每個分開 process 跑；lumi 會原地改 bt.IDX）：
  base  sprout/radiant/soft → motion/liveliness/{layers,frames}/<form>/<clip>_NN*、atlas_<form>_live_wx.png/json、face_anchors.json（加 key）
  lumi  螢絨 → lumi/{frames,layers,emissive}/<clip>_NN*、face_anchors_lumi.json（加 key）、atlas_lumi(+_emissive) 重砌（舊幀由檔案讀返，逐像素不變）
  evo   21 個 evo6 形態（蛋除外）→ evo6/<form>/…、face_anchors_<form>.json（加 key）、atlas_evo_<form> 重砌；絨跳連 route_clarity 燈色 atlas 一齊重砌
  ui    天氣疊層（陰／霧）、四季 LUT、委託面板＋icon、星星碎、心聲泡框、日記頁框＋貼紙、提醒 icon
  docs  CLIPS.json／CLIPS.md／ASSET_LOG.md 只「加」SYS12B1 key／段落（重讀即寫，冪等）
  preview  contact sheets
用法：python3 build_systems12_b1.py base|lumi|evo|ui|docs|preview|all
"""
import json, os, sys, math, tempfile, datetime, subprocess
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.normpath(os.path.join(HERE, ".."))
TR = os.path.join(ROOT, "sprites", "tuanrong"); MOT = os.path.join(TR, "motion"); LV = os.path.join(MOT, "liveliness")
EVO = os.path.join(TR, "evo6"); LUMI = os.path.join(TR, "lumi")
SYS = os.path.join(ROOT, "ui", "systems12"); SCN = os.path.join(ROOT, "scenes", "hd2d")
TMP = "/workspace/_sys12"; os.makedirs(TMP, exist_ok=True)

WX = ["leaf_umbrella", "shiver"]
WX_SPEC = {"leaf_umbrella": 6, "shiver": 4}
# fps, loop, loopFrom, priority, interruptible, cooldown, next, item, trigger, notes
WX_META = {
 "leaf_umbrella": (6, True, 2, 3, True, 0, "idle", "systems12 天氣：落雨撐葉（H3 雨天）",
     "天氣＝雨（15%）＋團絨喺 H3 戶外：idle 抽中 → 播 1 次第 1–2 幀（拎葉出嚟→舉過頭），之後第 3–6 幀循環到雨停／被打斷；雨停 → 收葉 → idle",
     "蠢蠢地但覺得自己好醒：第 1 幀喺身側拎出一塊大葉（望天），第 2 幀舉過頭開心，第 3–6 幀撐住葉左右擺、雨點滴落葉面濺白水花，"
     "第 6 幀得意瞇眼（覺得自己好醒，其實尾巴仲淋緊）。片葉只畫落身後空白位，唔遮面／燈；燈 emissive 照舊。"),
 "shiver": (10, True, 0, 3, True, 0, "idle", "systems12 天氣／季節：打冷震（冬天 12–2 月、霧天）",
     "季節＝冬（12–2 月）或天氣＝霧：idle 抽中機率加大；連播 2–3 個循環（約 1–1.2s）→ idle",
     "縮埋一嚿（sy 0.95、毛脹起 fluff）、身體左右 1px 震、兩邊藍色震線交替、第 2／4 幀呼白氣；表情瞇眼＋扁嘴 → 驚驚口。"),
}
WX_FACE = None   # filled lazily (needs L.F)

# ============================================================ shared clip params (used by all renderers)
def _cfg():
    import build_tuanrong as bt
    import build_tuanrong_liveliness as L
    return bt.IDX, L
def _S(form):
    import build_tuanrong_liveliness as L
    return L._geo(form, {})[1]

LEAF_CHOICE = {}
LEAF_CAND = [  # ox(×rx), oy(×ry), dtilt(rad), awidth(×rx)
    (0.10, -1.22, 0.00, 1.02), (0.12, -0.98, 0.00, 1.05), (0.30, -0.92, -0.22, 0.98), (0.48, -0.82, -0.40, 0.90),
    (0.62, -0.70, -0.55, 0.82), (0.74, -0.58, -0.70, 0.74)]

def _leaf_mask(n, lx, ly, a, b, t, curv):
    yy, xx = np.mgrid[:n, :n].astype(float); yy += .5; xx += .5
    c, s = math.cos(t), math.sin(t)
    X = (xx - lx) * c + (yy - ly) * s; Y = -(xx - lx) * s + (yy - ly) * c
    q = np.clip(X / a, -1.5, 1.5); Yc = Y - curv * b * q * q         # 兩邊垂低（傘形）
    m = (np.abs(q) <= 1) & (np.abs(Yc) <= b * (1 - q ** 4) * 0.98 + 0.35)
    return m, Yc, X

def ex_leaf(form, mode, tilt, rain=None):
    """大葉：只畫落空白像素（身後）；mode side（喺身側拎住）／over（舉過頭）；rain=幀號 → 雨點＋水花"""
    IDX, L = _cfg(); S = _S(form); u = 2 if S >= 60 else 1
    def f(cv, cx, cy, rx, ry):
        n = cv.n; empty0 = (cv.a == 0)
        def place(ci, dyfix=0.0):
            if mode == "side":
                lx, ly, a, b, t, curv = cx + 1.00 * rx, cy - 0.40 * ry, 0.62 * rx, max(1.6, 0.24 * ry), -1.05, 0.25
            else:
                ox, oy, dt, aw = LEAF_CAND[ci]
                lx, ly, a, b, t, curv = cx + ox * rx, cy + oy * ry - 1.2 * u + dyfix, aw * rx + u, max(1.9, 0.30 * ry), tilt + dt, 0.8
            return lx, ly, a, b, t, curv
        def build(ci):
            lx, ly, a, b, t, curv = place(ci)
            for _ in range(40):   # 夾返入格（1px 邊）
                m, Yc, X = _leaf_mask(n, lx, ly, a, b, t, curv)
                if not m.any(): break
                ys, xs = np.nonzero(m)
                if ys.min() < 2: ly += 2 - ys.min(); continue
                if xs.max() > n - 3: lx -= xs.max() - (n - 3); continue
                if xs.min() < 2: lx += 2 - xs.min(); continue
                break
            return (lx, ly, a, b, t, curv), m, Yc, X
        if mode == "over":
            if form not in LEAF_CHOICE:
                best = None
                for ci in range(len(LEAF_CAND)):
                    g, m, Yc, X = build(ci); vis = (m & empty0).sum() / max(1, m.sum())
                    if best is None or vis > best[1] + 1e-9: best = (ci, vis)
                    if vis >= 0.72: best = (ci, vis); break
                LEAF_CHOICE[form] = best[0]
            ci = LEAF_CHOICE[form]
        else: ci = 0
        (lx, ly, a, b, t, curv), m, Yc, X = build(ci)
        leaf = m & empty0
        cv.a[leaf & (Yc < -0.2)] = IDX["leaf"]; cv.a[leaf & (Yc >= -0.2)] = IDX["leaf_d"]
        rib = leaf & (np.abs(Yc + 0.1 * b) < 0.6) & (np.abs(X) < 0.8 * a)
        cv.a[rib] = IDX["leaf_d"]
        hl = leaf & (Yc < -0.55 * b) & (X < -0.1 * a) & (X > -0.6 * a)   # 葉面高光
        cv.a[hl] = IDX["cream4"] if S < 40 else IDX["leaf"]
        # 葉柄：由手（身右下）去葉底中心
        hx_, hy_ = cx + 0.90 * rx, cy + 0.10 * ry
        if mode == "side": tx_, ty_ = lx - 0.2 * a * math.cos(t), ly + 0.6 * b
        else: tx_, ty_ = lx + 0.1 * a, ly + 0.55 * b
        stem = np.zeros_like(leaf)
        for s_ in np.linspace(0, 1, 4 * n):
            x = int(math.floor(hx_ + (tx_ - hx_) * s_)); y = int(math.floor(hy_ + (ty_ - hy_) * s_))
            for dx_ in range(u):
                if 1 <= x + dx_ < n - 1 and 1 <= y < n - 1: stem[y, x + dx_] = True
        stem &= (cv.a == 0)
        cv.a[stem] = IDX["leaf_d"]
        rg = L._ring(leaf | stem) & (cv.a == 0)
        rg[0, :] = rg[-1, :] = rg[:, 0] = rg[:, -1] = False
        cv.a[rg] = IDX["outline"]
        if rain is None: return
        # 雨點（白高光＋drop＋drop_d）＋葉面水花（white）— 只入空白、唔掂邊
        def put(x, y, c):
            x, y = int(round(x)), int(round(y))
            if 1 <= x < n - 1 and 1 <= y < n - 1 and cv.a[y, x] == 0: cv.a[y, x] = IDX[c]
        def drop(x, y):
            col = ["white", "drop", "drop_d"] if u == 1 else ["white", "drop", "drop", "drop_d"]
            for j, c in enumerate(col): put(x, y + j, c)
        ys, xs = np.nonzero(m)
        top = {}
        for y, x in zip(ys, xs): top[x] = min(top.get(x, 99), y)
        if not top: return
        xl, xr = min(top), max(top)
        k = rain % 4
        # 落緊嘅雨（葉上面）兩粒，逐幀落低
        for i, fx in enumerate((0.30, 0.70)):
            x = xl + fx * (xr - xl) + (i * 2 - 1) * u
            yt = top.get(int(round(x)), 2)
            y = yt - (4 + 3 * u) + ((k + 2 * i) % 4) * u
            if y >= 1: drop(x, y)
        # 葉邊滴水（左右尖）
        for x0, sgn in ((xl, -1), (xr, 1)):
            yt = max(top[x0], 1)
            yy_ = np.nonzero(m[:, x0])[0]; yb = yy_.max() if len(yy_) else yt
            drop(x0 + sgn * 0, yb + 2 + ((k + (sgn > 0) * 2) % 3) * u)
        # 水花（葉頂 ˄ 白點）
        xs_ = xl + (0.25 + 0.5 * ((k // 2) % 2)) * (xr - xl)
        x0 = int(round(xs_)); yt = top.get(x0, None)
        if yt is not None:
            put(x0 - u, yt - 1, "white"); put(x0 + u, yt - 1, "white"); put(x0, yt - 1 - (k % 2), "white")
    return f

def ex_shiver(form, k):
    """打冷震：兩邊藍色震線（交替遠近）＋第 2／4 幀呼白氣。
    位置自動揀：由身體（連飾物／aura）最外邊再出 1–2px；兩邊冇位就逐步上移到頭位（較窄）；只畫落空白位。"""
    IDX, L = _cfg(); S = _S(form); u = 2 if S >= 60 else 1
    def f(cv, cx, cy, rx, ry):
        n = cv.n; occ = cv.a != 0
        def free(x, y): return 1 <= x < n - 1 and 1 <= y < n - 1 and cv.a[y, x] == 0
        if k % 2 == 1:   # 呼白氣（口右邊；冇位就搵附近空位）＋描邊
            pts = [(0, 0), (1, 0), (0, -1), (1, -1), (2, -1), (2, -2)] if u == 1 else \
                  [(0, 0), (1, 0), (2, 0), (0, -1), (1, -1), (2, -1), (3, -1), (1, -2), (2, -2), (3, -2), (4, -2), (3, -3), (4, -3), (5, -3), (4, -4)]
            ok_at = None
            for strict in (True, False):   # 先試同身體隔 1px；冇位先容許貼住（空白位照計）
                fit = (lambda x, y: not occ[y - 1:y + 2, x - 1:x + 2].any()) if strict else (lambda x, y: not occ[y, x])
                for side in (1, -1):
                    for dyy in [0.15 * ry, 0.35 * ry, -0.1 * ry, -0.35 * ry, -0.6 * ry, -0.85 * ry]:
                        by = int(round(cy + dyy))
                        x0 = int(round(cx + side * (0.95 * rx + 2 * u)))
                        for bx in (range(x0, n - 2) if side > 0 else range(x0, 2, -1)):
                            cells = [(bx + side * dx_, by + dy_) for dx_, dy_ in pts]
                            if all(2 <= x < n - 2 and 2 <= y < n - 2 and fit(x, y) for x, y in cells):
                                ok_at = cells; break
                        if ok_at: break
                    if ok_at: break
                if ok_at: break
            if ok_at:
                m = np.zeros_like(cv.a, bool)
                for x, y in ok_at: cv.a[y, x] = IDX["white"]; m[y, x] = True
                rg = L._ring(m) & (cv.a == 0); rg[0, :] = rg[-1, :] = rg[:, 0] = rg[:, -1] = False
                cv.a[rg] = IDX["cream3"] if "cream3" in IDX else IDX["outline"]
        occ = cv.a != 0
        L_ = 3 if u == 1 else 5
        for sgn in (-1, 1):
            gap = 1 + ((k + (sgn > 0)) % 2)          # 交替遠近＝震
            done = False
            for dy in [0.35 * ry * t for t in (1.0, 1.4, 1.8, 2.2, 0.6, 0.2)]:
                y0 = int(round(cy - dy))
                if y0 < 1 or y0 + L_ + 2 * u > n - 1: continue
                rows = range(max(1, y0 - 1), min(n - 1, y0 + L_ + 2 * u + 1))
                xs = [x for yy in rows for x in np.nonzero(occ[yy])[0]]
                if not xs: continue
                edge = max(xs) if sgn > 0 else min(xs)
                x = edge + sgn * (gap + 1)
                if not all(free(x, y0 + j) for j in range(L_)): continue
                for j in range(L_): cv.a[y0 + j, x] = IDX["drop_d"]
                x2 = x + sgn * 2 * u
                if all(free(x2, y0 + 2 * u + j) for j in range(L_ - 1)):
                    for j in range(L_ - 1): cv.a[y0 + 2 * u + j, x2] = IDX["drop"]
                done = True; break
    return f

def wx_clips(form):
    import build_tuanrong_liveliness as L
    F = L.F; S = _S(form); u = 2 if S >= 60 else 1
    C = {}; FACE = {}
    C["leaf_umbrella"] = [
        dict(sy=.97, sx=1.02, bud=1.0, twinkle=0, extras=[ex_leaf(form, "side", 0.0)]),
        dict(sy=1.0, sx=.99, bud=1.05, twinkle=1, fluff=.3, extras=[ex_leaf(form, "over", 0.0)]),
        dict(sy=.96, sx=1.02, sway=u, bud=1.0, twinkle=2, extras=[ex_leaf(form, "over", -0.10, rain=0)]),
        dict(sy=.96, sx=1.02, sway=0, bud=1.05, twinkle=3, extras=[ex_leaf(form, "over", -0.03, rain=1)]),
        dict(sy=.96, sx=1.02, sway=-u, bud=1.0, twinkle=4, extras=[ex_leaf(form, "over", 0.05, rain=2)]),
        dict(sy=.96, sx=1.02, sway=0, bud=1.05, twinkle=5, extras=[ex_leaf(form, "over", -0.03, rain=3)]),
    ]
    FACE["leaf_umbrella"] = [F("neutral", "U", "neutral"), F("happy", "C", "happy"), F("neutral", "U", "neutral"),
                             F("happy", "C", "happy"), F("neutral", "U", "neutral"), F("squint", "C", "happy")]
    C["shiver"] = [
        dict(dx=-1, sx=1.03, sy=.95, droop=1, fluff=1.0, bud=.95, twinkle=0, extras=[ex_shiver(form, 0)]),
        dict(dx=1, sx=1.01, sy=.96, droop=1, fluff=1.3, bud=.9, twinkle=1, extras=[ex_shiver(form, 1)]),
        dict(dx=-1, sx=1.03, sy=.95, droop=1, fluff=1.0, bud=.95, twinkle=2, extras=[ex_shiver(form, 2)]),
        dict(dx=1, sx=1.01, sy=.96, droop=1, fluff=1.3, bud=.9, twinkle=3, extras=[ex_shiver(form, 3)]),
    ]
    FACE["shiver"] = [F("squint", "C", "sad"), F("sad", "C", "surprised"), F("squint", "C", "sad"), F("sad", "C", "surprised")]
    return C, FACE

def register_meta():
    import build_tuanrong_motion as M
    for c in WX: M.META[c] = tuple(WX_META[c][:5])

def atomic_write(path, text):
    d = os.path.dirname(path); fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp_sys12_")
    with os.fdopen(fd, "w", encoding="utf-8") as fh: fh.write(text)
    os.chmod(tmp, 0o644); os.replace(tmp, path)

def write_fa_file(p, fa):
    head = {k_: v for k_, v in fa.items() if k_ != "anchors"}
    out = json.dumps(head, ensure_ascii=False)[:-1] + ',\n "anchors":{\n' + ',\n'.join(
        '  ' + json.dumps(cl) + ':[\n' + ',\n'.join('   ' + json.dumps(a, ensure_ascii=False, separators=(",", ":")) for a in lst) + ']'
        for cl, lst in fa["anchors"].items()) + '}}\n'
    assert json.loads(out) == fa
    atomic_write(p, out)

def load_idx(path, rgb):
    a = np.array(Image.open(path).convert("RGBA")); out = np.zeros(a.shape[:2], np.uint8)
    for i, c in enumerate(rgb):
        if i: out[(a[..., 3] == 255) & (a[..., :3] == tuple(c)).all(-1) & (out == 0)] = i
    assert ((a[..., 3] == 255) == (out > 0)).all(), path
    return out

def save_stats(name, d):
    json.dump(d, open(os.path.join(TMP, f"stats_{name}.json"), "w"), indent=1, ensure_ascii=False)

# ============================================================ base (sprout / radiant / soft)
def run_base():
    import build_tuanrong_liveliness as L, build_tuanrong_motion as M
    from build_tuanrong import FORMS, to_img
    register_meta(); L.init_head_k(); st = {}
    fa_p = os.path.join(LV, "face_anchors.json"); fa = json.load(open(fa_p))
    for form in L.FORM_LIST:
        S = FORMS[form]["S"]; piv = (S // 2, S - 3)
        kit = L.build_kit(form)
        for n, (a, pv) in kit.items():
            kp = os.path.join(LV, "kit", form, n + ".png")
            if not np.array_equal(np.array(to_img(a)), np.array(Image.open(kp).convert("RGBA"))): raise SystemExit(f"kit drift {form} {n}")
        C, FACE = wx_clips(form); clips = {}
        for clip in WX:
            c = clips[clip] = dict(noface=[], full=[], overlay=[], anchors=[])
            for k, p in enumerate(C[clip]):
                p = dict(p); p["_k"] = k
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
                to_img(c["noface"][k]).save(os.path.join(LV, "layers", form, f"{clip}_{k + 1:02d}_noface.png"))
                to_img(c["overlay"][k]).save(os.path.join(LV, "layers", form, f"{clip}_{k + 1:02d}_faceov.png"))
                to_img(c["full"][k]).save(os.path.join(LV, "frames", form, f"{clip}_{k + 1:02d}.png"))
            fps, loop, lf = WX_META[clip][:3]
            nf = [f"{clip}_noface_{k + 1:02d}" for k in range(len(c["noface"]))]
            ff = [f"{clip}_{k + 1:02d}" for k in range(len(c["full"]))]
            for n_, a in zip(nf, c["noface"]): items.append((n_, a, piv))
            for n_, a in zip(ff, c["full"]): items.append((n_, a, piv))
            ex = {"loopFrom": lf} if lf else {}
            anims[f"{clip}_noface"] = {"frames": nf, "fps": fps, "loop": loop, **ex}
            anims[clip] = {"frames": ff, "fps": fps, "loop": loop, **ex}
            fa["anchors"][form][clip] = c["anchors"]
        files = L.write_atlas(form, items, anims, {"form": form, "frameSize": S, "phase": "systems12-b1", "pivotRule": "body frames bottom-center (w/2, h-3)",
                              "note": "systems12 第 1 批天氣 clip：leaf_umbrella（撐葉）／shiver（打冷震）；<clip>_noface 無臉身體＋完整幀；五官 kit 用 atlas_<form>_live.json 嘅 eyes_*/mouth_*/bulb_*；葉／雨點／震線／白氣烙入身體層（葉只喺身後空白位）"},
                              base=f"atlas_{form}_live_wx")
        st[form] = dict(frames={c: len(clips[c]["full"]) for c in WX}, atlas=[os.path.basename(x) for x in files] if files else None,
                        leafChoice=LEAF_CHOICE.get(form))
    # face_anchors.json (same layout as S3.write_face_anchors)
    out = ('{"version":' + json.dumps(fa["version"]) + ',\n "coords":' + json.dumps(fa["coords"], ensure_ascii=False) + ',\n "pivotPx":' + json.dumps(fa["pivotPx"]) +
           ',\n "keys":' + json.dumps(fa["keys"], ensure_ascii=False) + ',\n "pivotOverride":' + json.dumps(fa["pivotOverride"]) + ',\n "anchors":{\n')
    fl = []
    for form in fa["anchors"]:
        cl = ['   ' + json.dumps(clip) + ':[\n' + ',\n'.join('    ' + json.dumps(a, ensure_ascii=False, separators=(",", ":")) for a in lst) + ']'
              for clip, lst in fa["anchors"][form].items()]
        fl.append('  ' + json.dumps(form) + ':{\n' + ',\n'.join(cl) + '}')
    out += ',\n'.join(fl) + '}}\n'
    assert json.loads(out) == fa
    atomic_write(fa_p, out)
    st["fit"] = [x for x in M.FIT_LOG if x[1].split("_0")[0] in WX or any(x[1].startswith(w) for w in WX)]
    save_stats("base", st); print("base", st)

# ============================================================ lumi
def run_lumi():
    import build_lumi as BL
    import build_tuanrong_liveliness as L, build_tuanrong_motion as M
    register_meta()
    L.init_head_k() if not L.HEAD_K else None
    if "lumi" not in L.HEAD_K: L.HEAD_K["lumi"] = L.HEAD_K["radiant"]
    FORM = "lumi"; rgb = BL.RGB
    kit = BL.build_kit()
    for n, (a, pv) in kit.items():
        kp = os.path.join(LUMI, "kit", n + ".png")
        if not np.array_equal(np.array(BL.to_img(a)), np.array(Image.open(kp).convert("RGBA"))): raise SystemExit(f"lumi kit drift {n}")
    fa_p = os.path.join(LUMI, "face_anchors_lumi.json"); fa = json.load(open(fa_p))
    old = [c for c in BL.ORDER if c not in WX]
    clips = {}
    for clip in old:
        n = len(fa["anchors"][clip]); c = dict(full=[], noface=[], anchors=fa["anchors"][clip])
        for k in range(n):
            pf = os.path.join(LUMI, "frames", f"{clip}_{k + 1:02d}.png"); pn = os.path.join(LUMI, "layers", f"{clip}_{k + 1:02d}_noface.png")
            a = load_idx(pf, rgb); b = load_idx(pn, rgb)
            assert np.array_equal(np.array(BL.to_img(a)), np.array(Image.open(pf).convert("RGBA"))), pf
            em = np.array(Image.open(os.path.join(LUMI, "emissive", f"{clip}_{k + 1:02d}_emissive.png")).convert("RGBA"))
            assert np.array_equal(np.array(BL.emis_img(a)), em), ("emis roundtrip", pf)
            c["full"].append(a); c["noface"].append(b)
        clips[clip] = c
    C, FACE = wx_clips(FORM)
    for clip in WX:
        c = clips[clip] = dict(noface=[], full=[], overlay=[], anchors=[])
        for k, p in enumerate(C[clip]):
            p = dict(p); p["_k"] = k
            p = M.render_fit(FORM, p, f"{clip}_{k + 1:02d}")
            body = L.body_render(FORM, p)
            an = BL.lumi_anchors(p, True)
            face = FACE[clip][k]; an["face"] = dict(face)
            full = L.compose_face(body, an, face, kit)
            ov = np.where(full != body, full, 0).astype(np.uint8)
            c["noface"].append(body); c["full"].append(full); c["overlay"].append(ov); c["anchors"].append(an)
            nn = f"{clip}_{k + 1:02d}"
            BL.to_img(full).save(os.path.join(LUMI, "frames", nn + ".png"))
            BL.to_img(body).save(os.path.join(LUMI, "layers", nn + "_noface.png"))
            BL.to_img(ov).save(os.path.join(LUMI, "layers", nn + "_faceov.png"))
            BL.emis_img(full).save(os.path.join(LUMI, "emissive", nn + "_emissive.png"))
            BL.emis_img(body).save(os.path.join(LUMI, "emissive", nn + "_noface_emissive.png"))
        fa["anchors"][clip] = c["anchors"]
    write_fa_file(fa_p, fa)
    BL.ORDER[:] = old + WX
    W, H, ni = BL.write_atlas(clips, kit)
    # stats file (lumi/_stats.json) — 加 key
    sp = os.path.join(LUMI, "_stats.json")
    if os.path.exists(sp):
        sd = json.load(open(sp)); sd["systems12_b1"] = {c: len(clips[c]["full"]) for c in WX}
        atomic_write(sp, json.dumps(sd, indent=1, ensure_ascii=False))
    st = dict(frames={c: len(clips[c]["full"]) for c in WX}, atlas=[W, H, ni], total=sum(len(c["full"]) for c in clips.values()), leafChoice=LEAF_CHOICE.get(FORM))
    save_stats("lumi", st); print("lumi", st)

# ============================================================ evo6 (21 forms, egg excluded)
def run_evo(only=None):
    import build_evo6_animF as Fm   # registers every evo form + patches
    import build_evo6_animBC as BC, build_evo6_anim as A
    import build_tuanrong_liveliness as L, build_tuanrong_motion as M
    import build_evo6_routeG as G   # tell_* meta（絨跳 G 預告 clip）＋ route atlas writer
    register_meta()
    CL = json.load(open(os.path.join(MOT, "CLIPS.json")))
    forms = [f for f in CL["forms"] if f.startswith("evo_") and f != "evo_egg"]
    if only: forms = [f for f in forms if f in only]
    st = {}
    for form in forms:
        fe = CL["forms"][form]; d = os.path.join(EVO, form)
        rgb = BC.pal_rgb(form); to_img = (lambda a, form=form: BC.to_img(a, form)); emis = (lambda a, form=form: BC.emis_img(a, form))
        order = [c for c in fe["clips"] if c not in WX] + [c for c in fe.get("tells", []) if c not in WX]
        fa_p = os.path.join(d, f"face_anchors_{form}.json"); fa = json.load(open(fa_p))
        clips = {}
        for clip in order:
            n = len(fa["anchors"][clip]); c = dict(full=[], noface=[], anchors=fa["anchors"][clip])
            for k in range(n):
                pf = os.path.join(d, "frames", f"{clip}_{k + 1:02d}.png"); pn = os.path.join(d, "layers", f"{clip}_{k + 1:02d}_noface.png")
                a = load_idx(pf, rgb); b = load_idx(pn, rgb)
                assert np.array_equal(np.array(to_img(a)), np.array(Image.open(pf).convert("RGBA"))), pf
                em = np.array(Image.open(os.path.join(d, "emissive", f"{clip}_{k + 1:02d}_emissive.png")).convert("RGBA"))
                assert np.array_equal(np.array(emis(a)), em), ("emis roundtrip", pf)
                c["full"].append(a); c["noface"].append(b)
            clips[clip] = c
        aj = json.load(open(os.path.join(EVO, f"atlas_{form}.json"))); kit = {}
        for kp in sorted(os.listdir(os.path.join(d, "kit"))):
            nm = kp[:-4]; pv = aj["frames"][nm]["pivotPx"]; kit[nm] = (load_idx(os.path.join(d, "kit", kp), rgb), (pv["x"], pv["y"]))
        # kit on disk must equal the generator kit
        gk = BC.build_kit(form)
        for nm, (a, pv) in gk.items():
            assert nm in kit and np.array_equal(a, kit[nm][0]) and tuple(pv) == tuple(kit[nm][1]), (form, "kit drift", nm)
        A.CUR[0] = form
        C, FACE = wx_clips(form); branch = A.FORMS[form].get("branch") if hasattr(A, "FORMS") else None
        branch = (BC.FORMS[form].get("branch") if form in BC.NEW else None)
        for clip in WX:
            c = clips[clip] = dict(noface=[], full=[], overlay=[], anchors=[])
            for kf, p in enumerate(C[clip]):
                p = dict(p); p["_k"] = kf; tag = f"{clip}_{kf + 1:02d}"
                p = M.render_fit(form, p, tag)
                body = L.body_render(form, p)
                for _ in range(8):
                    if not A.touches(body): break
                    ys = np.nonzero(body.any(1))[0]; S_ = body.shape[0]
                    if ys.max() >= S_ - 1 and ys.min() >= 2: p["lift"] = p.get("lift", 0) + 1; tagf = "lift+1"
                    elif ys.min() <= 0 and branch == "radiant" and p.get("sunk", 1.0) > 0.6: p["sunk"] = p.get("sunk", 1.0) - 0.1; tagf = "sunk"
                    elif ys.min() <= 0: p["lift"] = p.get("lift", 0) - 1; tagf = "lift-1"
                    else: break
                    M.FIT_LOG.append((form, tag, [tagf])); body = L.body_render(form, p)
                assert not A.touches(body), (form, tag, "touches edge")
                an = A.pend_rot(form, p, BC.anchors(form, p, True), False)
                face = FACE[clip][kf]; an["face"] = dict(face)
                full = L.compose_face(body, an, face, kit)
                ov = np.where(full != body, full, 0).astype(np.uint8)
                c["noface"].append(body); c["full"].append(full); c["overlay"].append(ov); c["anchors"].append(an)
                to_img(full).save(os.path.join(d, "frames", tag + ".png"))
                to_img(body).save(os.path.join(d, "layers", tag + "_noface.png"))
                to_img(ov).save(os.path.join(d, "layers", tag + "_faceov.png"))
                emis(full).save(os.path.join(d, "emissive", tag + "_emissive.png"))
                emis(body).save(os.path.join(d, "emissive", tag + "_noface_emissive.png"))
            fa["anchors"][clip] = c["anchors"]
        A.CUR[0] = None
        fa["weatherClips"] = WX
        fa["weatherNote"] = "systems12 第 1 批天氣 clip（leaf_umbrella 撐葉／shiver 打冷震）；錨點同 std clip（bulb＝燈中心；葉只喺身後空白位，唔遮燈）"
        write_fa_file(fa_p, fa)
        order_all = order + WX
        ainfo = BC.write_atlas(form, order_all, clips, kit) if form in BC.NEW else A.write_atlas(form, order_all, clips, kit)
        rinfo = None
        if form == "evo_hop":
            rinfo = G.write_route_atlases(order_all, clips, kit)
        st[form] = dict(frames={c: len(clips[c]["full"]) for c in WX}, atlas=list(ainfo) if ainfo else None, route=rinfo,
                        total=sum(len(clips[c]["full"]) for c in order_all), leafChoice=LEAF_CHOICE.get(form))
        print(form, st[form], flush=True)
    st["fit"] = [x for x in M.FIT_LOG if any(x[1].startswith(w) for w in WX)]
    save_stats("evo" + ("_" + "_".join(only) if only else ""), st)

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd == "base": run_base()
    elif cmd == "lumi": run_lumi()
    elif cmd == "evo": run_evo(sys.argv[2:] or None)
    elif cmd in ("ui", "docs", "preview"):
        import build_systems12_b1_ui as U
        getattr(U, "run_" + cmd)()
    elif cmd == "all":
        for c in ("base", "lumi", "evo", "ui", "docs", "preview"):
            subprocess.check_call([sys.executable, os.path.abspath(__file__), c])
