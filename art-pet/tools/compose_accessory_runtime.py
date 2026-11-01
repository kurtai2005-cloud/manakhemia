#!/usr/bin/env python3
"""團絨 飾品 runtime 參考合成器（遊美 2026-11-01）— 引擎（canvas2D、冇 shader）要做嘅嘢，一模一樣用 Python 寫一次。
只讀 data：accessories/attach/<form>.json、accessories/source/<item>/item.json＋lab PNG、身體幀、emissive。唔 import build_accessories。
流程（每 form × clip × 幀 × item）：
  1. 揀 view（facing F/S/B → front/side/back）同尺寸（S/M/L：最細一個 ≥ 目標闊；冇就最大）
  2. lab（label 圖：每種物料一隻 key 色）nearest 縮放 → 鏡像 → nearest 轉（角度取整數度，正＝順時針）
  3. 部件（尾／吊飾）跟錨點貼上，擺動（swing sim）只轉部件；頸飾用 band tile 逐列砌
  4. 成件 render：物料 ramp（上／左邊 hi、下／右邊 shade）＋ 1px 描邊；hole 物料清走
  5. faceGuard 逐 px 移開五官 → 帽挖莖（stem spans）→ 燈泡 ±1 挖空 → 檢查（≥65%、唔遮五官、唔遮燈泡、唔出 padding）
     任何一幀唔過 → 成個 clip 收起（hidden 原因）
  6. 多件：combos 即場解（讓位 steps／收起），emissive 用飾品 alpha 聯集遮走
用法（CLI）：python3 compose_accessory_runtime.py <form> <clip> <item[+item...]> [out.png] [scale]"""
import json, os, sys, math
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ART = os.path.dirname(HERE)
ACCD = os.path.join(ART, "sprites", "tuanrong", "accessories"); ATT = os.path.join(ACCD, "attach"); SRC = os.path.join(ACCD, "source")
PAD = 8
SLOT_ORDER = ["neck", "head", "side_r", "side_l", "face", "bulb"]
VIEW_OF = {"F": "front", "S": "side", "B": "back"}

# ---------------------------------------------------------------- data 讀取（cache）
_ATT = {}; _ITEM = {}; _IMG = {}; _BODY = {}
def attach(form):
    if form not in _ATT: _ATT[form] = json.load(open(os.path.join(ATT, f"{form}.json")))
    return _ATT[form]
def frame(form, clip, k):
    """attach clip 嘅 per-frame dict（展開 compact 格式）"""
    c = attach(form)["clips"][clip]; return {key: v[k - 1] for key, v in c["f"].items()}
def body(form, clip, k):
    key = (form, clip, k)
    if key not in _BODY:
        if len(_BODY) > 600: _BODY.clear()
        p = os.path.join(ART, attach(form)["clips"][clip]["frameDir"], f"{clip}_{k:02d}.png")
        _BODY[key] = np.array(Image.open(p).convert("RGBA"))
    return _BODY[key]
def emissive(form, clip, k):
    d = attach(form).get("emissiveDir")
    if not d: return None
    p = os.path.join(ART, d, f"{clip}_{k:02d}_emissive.png")
    return np.array(Image.open(p).convert("RGBA")) if os.path.exists(p) else None
def hexrgb(h): h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def item(key, src=SRC):
    if key not in _ITEM:
        d = os.path.join(src, key); it = json.load(open(os.path.join(d, "item.json"))); it["_dir"] = d
        it["_mat"] = {hexrgb(k): i + 1 for i, k in enumerate(it["materials"])}
        it["_ramp"] = {i + 1: (hexrgb(v["shade"]), hexrgb(v["base"]), hexrgb(v["hi"]), bool(v.get("hole")), bool(v.get("bodyOnly")))
                       for i, (k, v) in enumerate(it["materials"].items())}
        _ITEM[key] = it
    return _ITEM[key]
def lab(it, ent):
    """lab PNG → int label map（0＝空）"""
    p = os.path.join(it["_dir"], ent["lab"])
    if p not in _IMG:
        a = np.array(Image.open(p).convert("RGBA")); m = np.zeros(a.shape[:2], np.int16)
        for rgb_, i in it["_mat"].items(): m[(a[..., 3] > 0) & (a[..., 0] == rgb_[0]) & (a[..., 1] == rgb_[1]) & (a[..., 2] == rgb_[2])] = i
        _IMG[p] = m
    return _IMG[p]

# ---------------------------------------------------------------- 變形（nearest，snap 到 px）
def org(p, piv):
    """lab 左上角落點：round_half_even(p − pivot − 1) + 1（同 baked「render 加 1px 邊、pivot+1」一致；JS 要自己寫 half-even，唔好用 Math.round）"""
    return int(round(p - piv - 1)) + 1
def odd(x, lo=3): x = max(lo, int(round(x))); return x | 1
_XF = {}
def xform(m, piv, sx=1.0, sy=1.0, ang=0.0, mirror=False, key=None):
    """label map：nearest 縮放（out = round(w·sx)）→ 鏡像 → nearest 轉 ang°（整數度）。回傳 (map, pivot)。
    pivot：縮放後 =(p+.5)·out/w − .5；轉嘅時候軸心落喺整數格（同 baked rotate_labels 一樣）"""
    ang = int(round(ang)); ck = None
    if key is not None:
        ck = (key, round(sx, 3), round(sy, 3), ang, bool(mirror))
        if ck in _XF: return _XF[ck]
    h, w = m.shape; px, py = piv
    if abs(sx - 1) > 1e-6 or abs(sy - 1) > 1e-6:
        W2, H2 = max(1, int(round(w * sx))), max(1, int(round(h * sy)))
        xi = np.minimum(w - 1, ((np.arange(W2) + .5) * w / W2).astype(int)); yi = np.minimum(h - 1, ((np.arange(H2) + .5) * h / H2).astype(int))
        m = m[yi][:, xi]; px = (px + .5) * W2 / w - .5; py = (py + .5) * H2 / h - .5; h, w = m.shape
    if mirror: m = m[:, ::-1]; px = w - 1 - px
    if ang:
        R = int(math.ceil(math.hypot(w, h))) + 2; a = math.radians(ang); ca, sa = math.cos(a), math.sin(a)
        yy, xx = np.mgrid[0:2 * R + 1, 0:2 * R + 1]; dx, dy = xx - R, yy - R
        sxm = ca * dx + sa * dy + px; sym = -sa * dx + ca * dy + py
        xi, yi = np.round(sxm).astype(int), np.round(sym).astype(int); ok = (xi >= 0) & (xi < w) & (yi >= 0) & (yi < h)
        out = np.zeros((2 * R + 1, 2 * R + 1), m.dtype); out[ok] = m[yi[ok], xi[ok]]
        ys, xs = np.nonzero(out)
        if len(xs):
            y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max(); m = out[y0:y1 + 1, x0:x1 + 1]; px, py = R - x0, R - y0
    res = (m, (px, py))
    if ck is not None:
        if len(_XF) > 20000: _XF.clear()
        _XF[ck] = res
    return res
def xpt(p, piv, sx, sy, ang, mirror, w):
    """錨點（例：帽尖）跟住 xform 嘅位移：回傳相對 pivot 嘅 (dx,dy)"""
    x, y = (p[0] - piv[0]) * sx, (p[1] - piv[1]) * sy
    if mirror: x = -x
    a = math.radians(int(round(ang))); return (math.cos(a) * x - math.sin(a) * y, math.sin(a) * x + math.cos(a) * y)
def put(L, m, x, y, replace=None):
    """label map m 左上角放 L 嘅 (x,y)（已含 PAD＋1 邊）；replace：只可以蓋呢啲 label（None＝全部）"""
    h, w = m.shape; H, W = L.shape; x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0: return False
    sub = m[y0 - y:y1 - y, x0 - x:x1 - x]; dst = L[y0:y1, x0:x1]; sel = sub > 0
    if replace is not None: sel &= np.isin(dst, [0] + list(replace))
    dst[sel] = sub[sel]
    return (x0 == x and y0 == y and x1 == x + w and y1 == y + h)

# ---------------------------------------------------------------- render（同 baked render 一樣）
def render(L, it):
    """L：(S+2PAD+2)² label（四邊多 1 格）→ RGBA (S+2PAD)²。ramp：base；上／左邊 hi；下／右邊 shade；描邊 1px；hole 清走"""
    rd = it.get("render", {"outline": True, "shade": True}); img = np.zeros(L.shape + (4,), np.uint8)
    up = np.roll(L, 1, 0); lf = np.roll(L, 1, 1); dn = np.roll(L, -1, 0); rt = np.roll(L, -1, 1)
    holes = np.zeros(L.shape, bool)
    for lab_, (sh, base, hi, hole, _) in it["_ramp"].items():
        sel = L == lab_
        if not sel.any(): continue
        img[sel, :3] = base
        if rd.get("shade", True):
            img[sel & ((up != lab_) | (lf != lab_)), :3] = hi; img[sel & ((dn != lab_) | (rt != lab_)), :3] = sh
        img[sel, 3] = 255
        if hole: holes |= sel
    if rd.get("outline", True):
        a = img[..., 3] > 0; e = np.zeros_like(a)
        e[1:] |= a[:-1]; e[:-1] |= a[1:]; e[:, 1:] |= a[:, :-1]; e[:, :-1] |= a[:, 1:]
        e &= ~a; img[e, :3] = (59, 42, 62) if "outline" not in it else hexrgb(it["outline"]); img[e, 3] = 255
    img[holes] = 0
    return img[1:-1, 1:-1]

# ---------------------------------------------------------------- 擺動
def swing(pts, loop, kx, ky, decay, lim, maxd=14.0):
    """慣性擺：身體點向右郁 → 掛件向左拖（＋＝順時針）；loop clip 行兩轉攞第二轉；每幀變化 ≤ maxd°"""
    n = len(pts); s = 0.0; out = [0.0] * n
    for _ in range(2 if loop and n > 1 else 1):
        for k in range(n):
            if k: vx, vy = pts[k][0] - pts[k - 1][0], pts[k][1] - pts[k - 1][1]
            elif loop and n > 1: vx, vy = pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1]
            else: vx = vy = 0.0
            t = max(-lim, min(lim, decay * s + kx * vx + ky * vy)); s = s + max(-maxd, min(maxd, t - s)); out[k] = round(s, 2)
    return out

# ---------------------------------------------------------------- 選尺寸
def pick_size(variants, target, key="w"):
    """最細一個 ≥ target；冇就最大"""
    ks = sorted(variants, key=lambda k: variants[k][key])
    for k in ks:
        if variants[k][key] >= target - 1e-6: return k
    return ks[-1]
def pick_view(it, facing, slot_view=None):
    v = VIEW_OF.get(facing, "front")
    if slot_view: v = slot_view
    if v not in it["views"]: v = "front" if v != "back" or "front" not in it["views"] else "front"
    return v if v in it["views"] else None

def ov(it, form):
    return it.get("formOverrides", {}).get(form, {})

# ---------------------------------------------------------------- 單件：一個 clip
def _canvas(S): return np.zeros((S + 2 * PAD + 2, S + 2 * PAD + 2), np.int16)
def _shift_img(img, dx, dy):
    if not dx and not dy: return img, True
    o = np.zeros_like(img); H, W = img.shape[:2]; ys, xs = np.nonzero(img[..., 3])
    if len(ys) and (ys.min() + dy < 0 or ys.max() + dy >= H or xs.min() + dx < 0 or xs.max() + dx >= W): return img, False
    o[ys + dy, xs + dx] = img[ys, xs]; return o, True
def _hits(img, pts, S, r=1):
    for x, y in pts:
        for i in range(-r, r + 1):
            for j in range(-r, r + 1):
                X, Y = x + i + PAD, y + j + PAD
                if 0 <= X < img.shape[1] and 0 <= Y < img.shape[0] and img[Y, X, 3]: return True
    return False
def cut_hole(img, spans, S):
    """帽挖莖：stem spans（[y,x0,x1] 身體座標）範圍清走，執碎帽仔，洞邊補描邊（同 baked cut_hole）"""
    sub = img[PAD:PAD + S, PAD:PAD + S]; cut = np.zeros((S, S), bool)
    for y, x0, x1 in spans: cut[y, x0:x1 + 1] = True
    hole = cut & (sub[..., 3] > 0); sub[hole] = 0
    if not hole.any(): return
    for _ in range(2):
        a = sub[..., 3] > 0; nb = np.zeros(a.shape, int)
        for sh, ax in ((1, 0), (-1, 0), (1, 1), (-1, 1)): nb += ~np.roll(a, sh, ax)
        near = np.zeros_like(hole); near[1:] |= hole[:-1]; near[:-1] |= hole[1:]; near[:, 1:] |= hole[:, :-1]; near[:, :-1] |= hole[:, 1:]
        spur = a & (nb >= 3) & near; sub[spur] = 0; hole |= spur
    e = np.zeros_like(hole); e[1:] |= hole[:-1]; e[:-1] |= hole[1:]; e[:, 1:] |= hole[:, :-1]; e[:, :-1] |= hole[:, 1:]
    e &= (sub[..., 3] > 0); sub[e, :3] = (59, 42, 62)
def cut_glow(img, glow):
    for x, y in glow: img[max(0, y - 1 + PAD):y + 2 + PAD, max(0, x - 1 + PAD):x + 2 + PAD] = 0
def bulb_hit(img, bd, bp):
    if bp is None: return False
    x, y = bp
    if not bd[y, x, 3]: return False
    S = bd.shape[0]
    return any(img[y + j + PAD, x + i + PAD, 3] and bd[y + j, x + i, 3] for i in (-1, 0, 1) for j in (-1, 0, 1) if 0 <= y + j < S and 0 <= x + i < S)

def _size_rel(rule, A, ws, hs, sc):
    hw = A["ref"]["hw"]; w0 = hw * rule["k"] * sc * min(max(ws, rule["ws"][0]), rule["ws"][1])
    W = odd(w0, rule.get("minW", 3)) if rule.get("odd", True) else max(rule.get("minW", 1), int(round(w0)))
    if "hr" in rule:
        hs_ = min(max(hs, rule["hs"][0]), rule["hs"][1]) if "hs" in rule else 1.0
        H = max(rule.get("minH", 3), int(round(hw * rule["k"] * sc * rule["hr"] * (0.5 + 0.5 * hs_))))
    else: H = None
    return W, H

def draw_frame(it, form, clip, k, fr, ctx):
    """回傳 (label canvas L, info) 或 (None, why)。ctx：clip 級（swing 等）"""
    A = attach(form); S = A["frameSize"]; o = ov(it, form); slot = it["slot"]; L = _canvas(S); info = {}
    dx, dy, sc = o.get("dx", 0), o.get("dy", 0), A["slots"][slot].get("sc", 1.0) * o.get("sc", 1.0)
    if it.get("slotScaleFrom"): sc = A["slots"][it["slotScaleFrom"]].get("sc", 1.0) * o.get("sc", 1.0)
    fac = fr["facing"]
    def place_view(vname, size, sx, sy, ang, mirror, pos, parts_ang=None):
        ent = it["views"][vname][size]; m0 = lab(it, ent); piv0 = tuple(ent["pivot"])
        m, piv = xform(m0, piv0, sx, sy, ang, mirror, key=(it["id"], vname, size))
        X, Y = org(pos[0], piv[0]) + PAD + 1, org(pos[1], piv[1]) + PAD + 1
        inside = put(L, m, X, Y)
        for pt in ent.get("parts", []):
            if pt.get("sizeClass") and A["sizeClass"] not in pt["sizeClass"]: continue
            pe = it["parts"][pt["id"]][pt.get("size", size)]; pm0 = lab(it, pe); pp0 = tuple(pe["pivot"])
            ax_, ay_ = xpt(ent["anchors"][pt["at"]], piv0, sx, sy, ang, mirror, m0.shape[1])
            tip = (pos[0] + ax_, pos[1] + ay_)
            pa = (parts_ang or {}).get(pt["id"], 0.0) + pt.get("angK", 0.0) * ang
            psc = pt.get("scale", 1.0) * (parts_ang or {}).get(pt["id"] + ".scale", 1.0)
            pm, pp = xform(pm0, pp0, sx * psc, sy * psc, pa, mirror, key=(it["id"], pt["id"], size))
            put(L, pm, org(tip[0], pp[0]) + PAD + 1, org(tip[1], pp[1]) + PAD + 1, replace=[it["_mat"][hexrgb(c)] for c in pt.get("replace", [])] if pt.get("replace") is not None else None)
        return inside
    if slot == "head":
        hd = A["slots"]["head"]
        if clip in A["clips"] and "head" in A["clips"][clip]["hidden"]: return None, A["clips"][clip]["hidden"]["head"]
        x, y, ux, uy, ang, ws, hs = fr["head"]
        if hd["mode"] == "pin":
            P = it["pin"]; px, py, pang, pws = fr["pin"]; psc = sc * P.get("sc", {}).get(form, 1.0)
            W = odd(A["ref"]["hw"] * P["k"] * psc * min(max(pws, .85), 1.15), P.get("minW", 7)); H = max(P.get("minH", 3), int(round(W * it["size"]["hr"])))
            vname, a_ = "pin" if "pin" in it["views"] else "front", P["ang"] + pang
            if hd.get("pinSide") == "r" and "r" in P:
                R_ = P["r"]; W = odd(W * R_["wK"], 7); H = max(R_.get("minH", 6), int(round(W * R_["hK"]))); vname = R_["view"]; a_ = R_["ang"] + pang
            vs = it["views"][vname]; size = pick_size(vs, W); e = vs[size]
            sx, sy = W / e["w"], H / e["h"]
            ok = place_view(vname, size, sx, sy, a_, False, (px + dx, py + dy), ctx.get("parts", [{}] * 99)[k - 1])
            info.update(view=vname, size=size, W=W, H=H, ang=a_, pin=True)
        else:
            W, H = _size_rel(it["size"], A, ws, hs, sc); vname = pick_view(it, fac)
            vs = it["views"][vname]; size = pick_size(vs, W); e = vs[size]; sx, sy = W / e["w"], H / e["h"]
            sink = max(1, int(round(A["ref"]["hw"] * it["place"]["sink"])))
            pos = (x - ux * sink + dx, y - uy * sink + dy)
            ok = place_view(vname, size, sx, sy, ang, False, pos, ctx.get("parts", [{}] * 99)[k - 1])
            info.update(view=vname, size=size, W=W, H=H, ang=ang)
    elif slot in ("side_r", "side_l"):
        x, y, ang, ws, mir = fr[slot]; W, _ = _size_rel(it["size"], A, ws, 1.0, sc); vname = pick_view(it, fac)
        vs = it["views"][vname]; size = pick_size(vs, W); e = vs[size]; s_ = W / e["w"]; sg = -1 if mir else 1
        a_ = ang + it["place"].get("rot", 0) * sg
        ok = place_view(vname, size, s_, s_, a_, bool(mir), (x + dx * sg, y + dy), ctx.get("parts", [{}] * 99)[k - 1])
        info.update(view=vname, size=size, W=W, ang=a_, mirror=bool(mir))
    elif slot == "face":
        if fr["face"] is None: return None, "faceVisible=false（背面／遮面）"
        ok, why = draw_glasses(it, A, fr, L, ctx, o, info)
        if not ok: return None, why
    elif slot == "neck":
        if fr["neck"] is None: return None, "頸位冇身體"
        ok, why = draw_neck(it, A, fr, L, ctx, k, o); info["neck"] = True
        if not ok: return None, why
    elif slot == "bulb":
        hx, hy, fx, fy, fang, fw, ux, uy = fr["bulb"]; mode = it["place"]["anchor"]
        if mode == "hang":
            vname = pick_view(it, fac); size = A["sizeClass"]; e = it["views"][vname][size]
            sw = ctx["swing"][k - 1] if ctx.get("swing") else 0.0
            ok = place_view(vname, size, 1.0, 1.0, sw, False, (hx + dx, hy + dy)); info.update(view=vname, size=size, swing=sw)
        else:   # float（光環）：中心＝浮點 + u·ry；rx 由 fw
            rx_t = fw / 2 * sc; vs = it["views"]["front"]
            size = min(vs, key=lambda s_: (abs(vs[s_]["halo"]["rx"] - rx_t), vs[s_]["halo"]["rx"]))
            h_ = vs[size]["halo"]; ry = h_["ry"]; cx, cy = fx + ux * (ry + dy), fy + uy * (ry + dy)
            if not A["slots"]["bulb"]["topBulb"]: cx += dx
            m, piv = xform(lab(it, vs[size]), tuple(vs[size]["pivot"]), 1, 1, fang, False, key=(it["id"], "front", size))
            X, Y = org(cx, piv[0]), org(cy, piv[1])
            if Y + PAD < 0: Y = -PAD                                   # 跳得高：貼住 padding 頂
            if X + PAD < 0 or X + PAD + m.shape[1] > S + 2 * PAD: return None, "光環出咗 padding"
            ok = put(L, m, X + PAD + 1, Y + PAD + 1); info.update(view="front", size=size, rx=h_["rx"], ang=fang)
    else: return None, f"未知 slot {slot}"
    info["inside"] = bool(ok)
    return L, info

def _sheet_cell(it, key):
    G = it["lens"]; r = G["index"].get(key)
    if r is None: return None, None
    sh = lab(it, {"lab": G["sheet"]}); x, y, w, h, px, py = r
    return sh[y:y + h, x:x + w], (px, py)
def draw_glasses(it, A, fr, L, ctx, o, info):
    """眼鏡（同 baked draw_glasses 同一條公式）：retry adj＝(drx, dry, lift, out, pf)；兩片鏡片由 ladder 揀，各自貼鏡心、跟眼線轉；鼻橋＋反光引擎畫"""
    S = A["frameSize"]; G = it["glasses"]; th = 2 if S >= 64 else 1
    lx, ly, rx, ry, bx, by, plx, ply, prx, pry, pbx, pby, tL, tR = fr["face"]
    drx, dry, lift, out, pf = (list(ctx.get("adj") or []) + [0, 0, 0, 0, 0])[:5]
    cs = [[plx, ply], [prx, pry]] if pf else [[lx, ly], [rx, ry]]; gbx, gby = (pbx, pby) if pf else (bx, by)
    dxv, dyv = cs[1][0] - cs[0][0], cs[1][1] - cs[0][1]; dist = math.hypot(dxv, dyv); ex, ey = dxv / max(dist, 1e-6), dyv / max(dist, 1e-6); nx, ny = ey, -ex
    cs = [[cs[0][0] + nx * lift - ex * out, cs[0][1] + ny * lift - ey * out], [cs[1][0] + nx * lift + ex * out, cs[1][1] + ny * lift + ey * out]]
    r_ = o.get("r", 0.0); ax = gbx + 1.5 + r_ + drx; ay = gby + 1.5 + r_ + dry
    fh = A["slots"]["face"]["mode"] == "forehead"
    if fh:
        F = G["forehead"]; ay = F["ay"] + dry; ax = min(F["axMax"] + drx, (dist + 2 * out) / 2 - th * 0.5)
        if ay < 0.9: return False, "額頭位唔夠（眼鏡會浮出個頭）"
        Lf = max((c[1] - (t - F["aboveEye"] - ay)) / max(1e-6, -ny) for c, t in zip(cs, (tL, tR)))
        cs = [[c[0] + nx * Lf, c[1] + ny * Lf] for c in cs]; gbx = gby = -9
    lim = (dist + 2 * out) / 2 - th * 0.5
    if ax > lim: ax = lim
    if ax < gbx + 0.45 + out or ay < gby + 0.45 + lift: return False, f"眼距 {dist:.1f}px 太窄（側面），戴唔落"
    axq = max(it["lens"]["ax"][0], min(it["lens"]["ax"][-1], math.floor(ax * 2) / 2)); ayq = max(it["lens"]["ay"][0], min(it["lens"]["ay"][-1], math.floor(ay * 2) / 2))
    ang = math.degrees(math.atan2(ey, ex)); inside = True
    for i, c in enumerate(cs):
        fx, fy = (round(c[0] * 2) / 2) % 1, (round(c[1] * 2) / 2) % 1
        m0, piv0 = _sheet_cell(it, f"{axq:g}_{ayq:g}_t{th}_{'o' if fh else 'n'}_{fx:g}_{fy:g}")
        if m0 is None: return False, "冇合適鏡片（ladder 外）"
        m, piv = xform(m0, piv0, 1, 1, ang, i == 1, key=(it["id"], "lens", axq, ayq, th, fh, fx, fy))
        inside &= put(L, m, int(round(c[0] - piv[0])) + PAD + 1, int(round(c[1] - piv[1])) + PAD + 1)
    fk = it["_mat"][hexrgb(it["lens"]["frameKey"])]; gk = it["_mat"][hexrgb(it["lens"]["glintKey"])]
    a0 = (cs[0][0] + ex * (ax + th * .5) + nx * ay * G["bridgeY"], cs[0][1] + ey * (ax + th * .5) + ny * ay * G["bridgeY"])
    a1 = (cs[1][0] - ex * (ax + th * .5) + nx * ay * G["bridgeY"], cs[1][1] - ey * (ax + th * .5) + ny * ay * G["bridgeY"])
    n_ = int(max(2, math.hypot(a1[0] - a0[0], a1[1] - a0[1]) * 2)) + 1
    for j in range(n_):
        t = j / (n_ - 1); X, Y = int(round(a0[0] + (a1[0] - a0[0]) * t)) + PAD + 1, int(round(a0[1] + (a1[1] - a0[1]) * t)) + PAD + 1
        if 0 <= X < L.shape[1] and 0 <= Y < L.shape[0]: L[Y, X] = fk
    if (ax + ay) / 2 >= G["glintMinR"]:
        for c in cs:
            X, Y = int(round(c[0] - G["glintK"] * (ax - 1))) + PAD + 1, int(round(c[1] - G["glintK"] * (ay - 1))) + PAD + 1
            if 0 <= X < L.shape[1] and 0 <= Y < L.shape[0] and not L[Y, X]: L[Y, X] = gk
    info.update(view="forehead" if fh else "front", size=f"{axq:g}x{ayq:g}", ax=round(ax, 2), ay=round(ay, 2), D=round(dist, 2), adj=[drx, dry, lift, out, pf])
    return True, None

def draw_neck(it, A, fr, L, ctx, k, o):
    """頸飾：band tile 逐列砌（跟傾角 shear），每行用 attach rows 收邊；decor（尾／花）貼錨點"""
    ny, cx, ang, xl, xr, rows = fr["neck"]; S = A["frameSize"]; N = it["neck"]; t = math.tan(math.radians(ang)) if ang else 0.0
    ny += o.get("dy", 0); cls = A["sizeClass"]
    def rowclip(y):
        i = y - (fr["neck"][0] - 4)
        if 0 <= i < len(rows) and rows[i] is not None: return rows[i]
        return None
    def setp(x, y, v, clip=True):
        if clip:
            rc = rowclip(y)
            if rc is None or not (rc[0] <= x <= rc[1]): return
        X, Y = x + PAD + 1, y + PAD + 1
        if 0 <= X < L.shape[1] and 0 <= Y < L.shape[0]: L[Y, X] = v
    if N["mode"] == "stripe":
        th = A["slots"]["neck"]["thRef"] + o.get("th", 0); tile = lab(it, N["tile"]); P = tile.shape[1]
        for x in range(xl - 1, xr + 2):
            dyx = int(round(-t * (x - cx)))
            for r in range(th): setp(x, ny + dyx + r, tile[min(r, tile.shape[0] - 1), (x - xl) % P])
        tl = N["tail"]; ts = tl["sizes"].get(str(th)) or tl["sizes"][max(tl["sizes"], key=int)]
        tm = lab(it, ts); tw = tm.shape[1]; lag = ctx["lag"][k - 1] if ctx.get("lag") else 0
        x0 = xr - th - tw // 2 + 1; y0 = ny + int(round(-t * (x0 - cx))) + th
        for j in range(tm.shape[0]):
            sw = int(round(lag * j / max(tm.shape[0] - 1, 1)))
            for i in range(tw):
                if tm[j, i]: setp(x0 + i + sw, y0 + j, tm[j, i], clip=False)
    else:   # leaves：一片片葉（A/B 交替）、頂行收邊；細花
        lc = N["leaf"][cls]; tile = lab(it, lc); lw = lc["lw"]; n = max(3, int(round((xr - xl + 3) / lw))); x0 = (xl + xr + 1) / 2 - n * lw / 2
        for i in range(n):
            lx = int(round(x0 + i * lw)); yb = ny + int(round(-t * (lx + lw / 2 - cx))); cell = tile[:, (i % 2) * lw:(i % 2 + 1) * lw]
            for yy in range(cell.shape[0]):
                for xx in range(lw):
                    if cell[yy, xx]: setp(lx + xx, yb + yy, cell[yy, xx], clip=yy == 0)
        fl = N["flower"][cls]; fm = lab(it, fl); fx = int(round(cx + (xr - xl) * N["flowerAt"])); fy = ny + int(round(-t * (fx - cx))) + fl["dy"]
        px_, py_ = fl["pivot"]
        for yy in range(fm.shape[0]):
            for xx in range(fm.shape[1]):
                if fm[yy, xx]: setp(fx + xx - int(px_), fy + yy - int(py_), fm[yy, xx], clip=False)
    return True, None

def clip_layers(key, form, clip, src=SRC):
    """一件 item × 一個 clip：回傳 (layers list[RGBA (S+2PAD)²], infos) 或 (None, why)。memo"""
    ck = (key, form, clip, src)
    if ck in _CL: return _CL[ck]
    if len(_CL) > 400: _CL.clear()
    res = _clip_layers(key, form, clip, src); _CL[ck] = res; return res
_CL = {}
def _clip_layers(key, form, clip, src):
    it = item(key, src); A = attach(form); S = A["frameSize"]; c = A["clips"].get(clip)
    if c is None: return None, "冇呢個 clip"
    o = ov(it, form)
    for scope in ("*", form):
        why = it.get("hideClips", {}).get(scope, {}).get(clip)
        if why: return None, why
    if clip in o.get("hide", {}): return None, o["hide"][clip]
    if it["slot"] in c["hidden"]: return None, c["hidden"][it["slot"]]
    if not c["f"]: return None, c["hidden"].get("head", "fit 失敗")
    n = c["n"]; frs = [frame(form, clip, k) for k in range(1, n + 1)]; ctx = {}
    sw = it.get("swing")
    if sw:
        src_ = sw["src"]
        if src_ == "head": pts = [(f["head"][0], f["head"][1]) for f in frs]
        elif src_ == "bulb": pts = [tuple(f["bulbPt"]) if f["bulbPt"] else (f["bulb"][0], f["bulb"][1]) for f in frs]
        else: pts = [(f[src_][0], f[src_][1]) for f in frs]
        s_ = swing(pts, c["loop"], sw["kx"], sw["ky"], sw["decay"], sw["lim"], sw.get("maxd", 14.0))
        if sw.get("apply", "item") == "item": ctx["swing"] = s_
        else: ctx["swingPart"] = (sw["apply"], s_, sw.get("gain", 1.0))
    if it["slot"] == "neck" and it["neck"].get("lag"):
        cxs = [f["neck"][1] if f["neck"] else 0 for f in frs]
        ctx["lag"] = [0] + [int(max(-2, min(2, -(cxs[i] - cxs[i - 1])))) for i in range(1, n)]
    why0 = None
    for adj in it.get("retry", [None]):                   # 例：眼鏡（成個 clip 一齊試）
        ctx["adj"] = adj; res = _frames(it, form, clip, frs, ctx, A, S, n)
        if res[0] is not None: return res
        if why0 is None: why0 = res[1]
    return None, why0
def _frames(it, form, clip, frs, ctx, A, S, n):
    fb = it.get("partFallback", [{}])
    layers = []; infos = []
    for k, fr in enumerate(frs, 1):
        bd = body(form, clip, k); fp = fr["facePts"]; best = None; lastwhy = None
        for st in fb:
            pa = {}
            if "swingPart" in ctx:
                pid, s_, g = ctx["swingPart"]; pa[pid] = s_[k - 1] * g + st.get("rot", 0.0); pa[pid + ".scale"] = st.get("scale", 1.0)
            ctx["parts"] = [pa] * n
            L, info = draw_frame(it, form, clip, k, fr, ctx)
            if L is None: lastwhy = info; break
            img = render(L, it)
            if it["slot"] == "face":                        # bodyOnly 物料（鏡腳／反光）：只畫喺身體上
                for lab_, r_ in it["_ramp"].items():
                    if r_[4]:                                   # 身體外（或者畫布外）嘅 bodyOnly 像素清走
                        sel = L[1:-1, 1:-1] == lab_; onb = np.zeros_like(sel); onb[PAD:PAD + S, PAD:PAD + S] = bd[..., 3] > 0
                        img[sel & ~onb] = 0
                if fr["eyes"]:
                    for ev in fr["eyes"]:
                        for i in range(0, len(ev), 2):
                            if img[ev[i + 1] + PAD, ev[i] + PAD, 3]: lastwhy = "鏡框會壓到眼"; break
                if lastwhy == "鏡框會壓到眼": img = None
                if img is not None and info.get("view") == "forehead":
                    a = np.zeros(img.shape[:2], bool); a[PAD:PAD + S, PAD:PAD + S] = bd[..., 3] > 0; r_ = img[..., 3] > 0
                    if (r_ & a).sum() < it["glasses"]["forehead"]["onBodyMin"] * r_.sum(): lastwhy = "額頭位唔夠（眼鏡會浮出個頭）"; img = None
                if img is None: break
            fg = it["place"].get("faceGuard")
            if fg:
                stx, sty = fg["step"]
                if info.get("mirror") and fg.get("mirrorFlipX"): stx = -stx
                moved = 0
                for _ in range(fg["max"]):
                    if not _hits(img, fp, S): break
                    img, okm = _shift_img(img, stx, sty); moved += 1
                    if not okm: break
                info["guard"] = moved
            if it.get("faceClear"):                         # 頸飾：五官 ±1 直接清走
                for x, y in fp: img[max(0, y - 1 + PAD):y + 2 + PAD, max(0, x - 1 + PAD):x + 2 + PAD] = 0
            if len(fb) > 1:
                if _hits(img, fp, S) or not info.get("inside", True): lastwhy = "尾撞五官／出 padding"; continue
            best = (img, info); break
        if best is None: return None, f"{clip}_{k:02d}: {lastwhy}"
        img, info = best
        if it.get("cutStem") and info.get("pin") is None: cut_hole(img, fr["stem"], S)
        if not img[..., 3].any(): return None, f"{clip}_{k:02d}: 飾品完全被遮"
        n0 = int((img[..., 3] > 0).sum()); cut_glow(img, fr["glow"])
        if (img[..., 3] > 0).sum() < 0.65 * n0: return None, f"{clip}_{k:02d}: 燈泡位置喺飾品正中（挖空後剩唔夠 65%）"
        if _hits(img, fp, S): return None, f"{clip}_{k:02d}: 會遮五官"
        if bulb_hit(img, bd, fr["bulbPt"]): return None, f"{clip}_{k:02d}: 會遮燈泡"
        layers.append(img); infos.append(info)
    return layers, infos

# ---------------------------------------------------------------- 多件（combos 即場解）
def _mask_shift(m, dx, dy):
    if not dx and not dy: return m
    H, W = m.shape; ys, xs = np.nonzero(m)
    if len(ys) and (ys.min() + dy < 0 or ys.max() + dy >= H or xs.min() + dx < 0 or xs.max() + dx >= W): return None
    o = np.zeros_like(m); o[ys + dy, xs + dx] = True; return o
def _under_over(ia, ib):
    return (ia, ib) if SLOT_ORDER.index(ia["slot"]) < SLOT_ORDER.index(ib["slot"]) else (ib, ia)
def conflict(ma, mb, ia, ib):
    ov_ = int((ma & mb).sum())
    if not ov_: return False, 0.0
    if ia["yield"].get("anyOverlap") or ib["yield"].get("anyOverlap"): return True, 1.0
    u, _ = _under_over(ia, ib); mu = ma if u is ia else mb
    cm = [x["yield"].get("coverMax") for x in (ia, ib) if x["yield"].get("coverMax") is not None]
    lim = max(cm) if cm else 0.30
    r = ov_ / max(1, int(mu.sum())); return r > lim, r
def _attached(m, bd, other):
    S = bd.shape[0]; base = other.copy(); base[PAD:PAD + S, PAD:PAD + S] |= bd[..., 3] > 0
    g = m.copy(); g[1:] |= m[:-1]; g[:-1] |= m[1:]; g[:, 1:] |= m[:, :-1]; g[:, :-1] |= m[:, 1:]
    return bool((g & base).any())
def _bad_spot(m, bd, fr):
    for x, y in fr["facePts"]:
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                if m[y + j + PAD, x + i + PAD]: return True
    bp = fr["bulbPt"]
    if bp:
        x, y = bp; S = bd.shape[0]
        if bd[y, x, 3] and any(m[y + j + PAD, x + i + PAD] and bd[y + j, x + i, 3] for i in (-1, 0, 1) for j in (-1, 0, 1) if 0 <= y + j < S and 0 <= x + i < S): return True
    return False
_SOLVE = {}
def solve_outfit(worn, form, clip, src=SRC):
    """回傳 {item: (dx,dy)}, hidden{item: why}。規則同 ACC5 combos：逐對（唔同 slot）搵衝突 → 讓位件（yield priority 細＝先讓）
    試 steps（成個 clip 同一個位移；唔可以遮五官／燈泡、要貼住身體或對方，floatOk 例外）；唔得 → 收起；最後殘留衝突再收起 priority 細嗰件"""
    ck = (tuple(sorted(worn)), form, clip, src)
    if ck in _SOLVE: return _SOLVE[ck]
    its = {w: item(w, src) for w in worn}; lay = {}; hidden = {}
    for w in worn:
        L_, inf = clip_layers(w, form, clip, src)
        if L_ is None: hidden[w] = inf
        else: lay[w] = [l[..., 3] > 0 for l in L_]
    for w in list(lay):                                  # 同一個 slot 只可以戴一件：priority 大嗰件留低
        for z in list(lay):
            if z != w and its[z]["slot"] == its[w]["slot"] and its[z]["yield"]["priority"] > its[w]["yield"]["priority"]:
                hidden[w] = f"同 {z} 同一個 slot（{its[w]['slot']}）→ 收起"; lay.pop(w); break
    n = attach(form)["clips"][clip]["n"]; frs = [frame(form, clip, k) for k in range(1, n + 1)]
    off = {w: (0, 0) for w in lay}
    vis = sorted(lay, key=lambda w: its[w]["yield"]["priority"])
    def pair_ok(a, b, oa):
        ia, ib = its[a], its[b]
        for k in range(n):
            ma = _mask_shift(lay[a][k], *oa)
            if ma is None: return False
            mb = _mask_shift(lay[b][k], *off[b])
            if mb is None: return False
            if conflict(ma, mb, ia, ib)[0]: return False
            if oa != (0, 0):
                bd = body(form, clip, k + 1)
                if _bad_spot(ma, bd, frs[k]): return False
                if not ia["yield"].get("floatOk") and not _attached(ma, bd, mb): return False
        return True
    for i, a in enumerate(vis):
        for b in vis[i + 1:]:
            if its[a]["slot"] == its[b]["slot"]: continue
            if a in hidden or b in hidden: continue
            y_, st = (a, b) if its[a]["yield"]["priority"] < its[b]["yield"]["priority"] else (b, a)
            if pair_ok(y_, st, off[y_]): continue
            good = None
            for dx, dy in [tuple(s_) for s_ in its[y_]["yield"]["steps"]]:
                cand = (off[y_][0] + dx, off[y_][1] + dy) if off[y_] != (0, 0) else (dx, dy)
                if pair_ok(y_, st, cand) and all(pair_ok(y_, z, cand) if its[z]["slot"] != its[y_]["slot"] and z not in hidden and z != st else True for z in vis if z != y_):
                    good = cand; break
            if good: off[y_] = good
            else: hidden[y_] = f"同 {st} 撞（讓位都唔得）→ 收起"
    # 殘留：任何一對仲撞 → 收起 priority 細嗰件
    changed = True
    while changed:
        changed = False; vv = [w for w in vis if w not in hidden]
        for i, a in enumerate(vv):
            for b in vv[i + 1:]:
                if its[a]["slot"] == its[b]["slot"]: continue
                if not pair_ok(a, b, off[a]):
                    y_ = a if its[a]["yield"]["priority"] < its[b]["yield"]["priority"] else b; hidden[y_] = "多件殘留衝突 → 收起"; changed = True; break
            if changed: break
    res = ({w: off[w] for w in lay if w not in hidden}, hidden); _SOLVE[ck] = res
    if len(_SOLVE) > 5000: _SOLVE.clear()
    return res

def compose(form, clip, k, worn, src=SRC, with_emissive=False):
    """完整一幀：body → 飾品層（SLOT_ORDER，各自位移）→ emissive（用飾品 alpha 聯集遮走，lighter 疊）。回傳 RGBA (S+2PAD)²"""
    A = attach(form); S = A["frameSize"]; bd = body(form, clip, k)
    out = np.zeros((S + 2 * PAD, S + 2 * PAD, 4), np.uint8); out[PAD:PAD + S, PAD:PAD + S] = bd
    off, hidden = solve_outfit(worn, form, clip, src) if len(worn) > 1 else (({worn[0]: (0, 0)}, {}) if clip_layers(worn[0], form, clip, src)[0] is not None else ({}, {worn[0]: clip_layers(worn[0], form, clip, src)[1]}))
    acc = np.zeros(out.shape[:2], bool)
    for w in sorted(off, key=lambda w: SLOT_ORDER.index(item(w, src)["slot"])):
        L_, _ = clip_layers(w, form, clip, src); img = L_[k - 1]
        img, ok = _shift_img(img, *off[w]); m = img[..., 3] > 0; out[m] = img[m]; acc |= m
    if with_emissive:
        em = emissive(form, clip, k)
        if em is not None:
            e = np.zeros_like(out); e[PAD:PAD + S, PAD:PAD + S] = em; e[acc] = 0
            m = e[..., 3] > 0; out[m, :3] = np.minimum(255, out[m, :3].astype(int) + e[m, :3].astype(int) // 3)
    return out, hidden

if __name__ == "__main__":
    form, clip, worn = sys.argv[1], sys.argv[2], sys.argv[3].split("+")
    path = sys.argv[4] if len(sys.argv) > 4 else f"/tmp/{form}_{clip}_{sys.argv[3]}.png"; sc = int(sys.argv[5]) if len(sys.argv) > 5 else 4
    n = attach(form)["clips"][clip]["n"]; cells = []
    for k in range(1, n + 1):
        im, hid = compose(form, clip, k, worn, with_emissive=True); cells.append(im)
    W = sum(c.shape[1] for c in cells); H = cells[0].shape[0]; sheet = np.zeros((H, W, 4), np.uint8); x = 0
    for c in cells: sheet[:, x:x + c.shape[1]] = c; x += c.shape[1]
    Image.fromarray(sheet).resize((W * sc, H * sc), Image.NEAREST).save(path); print(path, "hidden:", hid)
