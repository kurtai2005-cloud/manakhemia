# 《微光小圃》5b 遠足同工作 — 出發／返屋 strip（成年 33）、背囊、手信 10（HD icon＋1x pixel）、工作帽 4 款 × 4 級 overlay atlas、long_5b.json
# 純 Pillow/numpy，冇 AI。唔改 4a/4b 檔。
import json, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import long_5abc_lib as LB
import reactions_lib as L
from series2_lib import ART, save, paste, ncolors, limit_colors
O5 = os.path.join(LB.OUTL, "5b")
OL = (46, 30, 40)
LEATH = {"L": ((226, 168, 112), (186, 124, 74), (140, 86, 52)), "F": ((206, 146, 92), (164, 104, 62), (122, 74, 44))}

# ───────── 背囊（貼喺身左邊，畫喺身後）─────────
def backpack(r, full=False):
    hw = r.headHW; bw = int(np.clip(round(hw * 0.75), 7, 12)) + (2 if full else 0); bh = bw + 2 + (1 if full else 0)
    rows = []
    for j in range(bh):
        if j == 0: rows.append("." + "F" * (bw - 2) + ".")
        elif j < 3: rows.append("F" * bw)                       # 蓋
        else: rows.append("L" * bw)
    a = L.auto(rows, outline=OL, ramps=LEATH, hi=True)
    cx = a.shape[1] // 2; a[3, cx] = (255, 214, 110, 255); a[4, cx] = (200, 150, 60, 255)   # 金扣
    a[bh - 1, 2] = (120, 200, 110, 255); a[bh, 2] = (80, 160, 80, 255)                       # 葉仔吊飾
    if full:   # 脹晒：頂露出樹枝＋星星
        top = np.zeros((4, a.shape[1], 4), np.uint8)
        for y, x, c in ((3, cx - 2, (150, 104, 60)), (2, cx - 3, (150, 104, 60)), (1, cx - 3, (110, 190, 90)), (0, cx - 4, (110, 190, 90)),
                        (3, cx + 2, (255, 226, 120)), (2, cx + 2, (255, 240, 170)), (3, cx + 1, (255, 226, 120)), (3, cx + 3, (255, 226, 120))):
            top[y, x] = (*c, 255)
        a = np.concatenate([top, a], 0)
    sx, sy = [int(round(v)) for v in r.anchors["side_l"]]
    ys, xs = np.nonzero(r.base[..., 3])
    X = max(0, min(sx - a.shape[1] + 4, xs.min() - a.shape[1] + 5)); Y = sy - a.shape[0] // 2 - 1
    return a, X, Y
def with_pack(r, full):
    a, X, Y = backpack(r, full); o = np.zeros_like(r.base); paste(o, a, X, Y)
    out = o.copy(); m = r.base[..., 3] > 0; out[m] = r.base[m]               # 身喺前面
    # 肩帶：1px 由背囊頂斜落身（喺身上面畫）
    sx, sy = [int(round(v)) for v in r.anchors["side_l"]]
    for i in range(3):
        x, y = sx + 1 + i, Y + 2 + i
        if 0 <= y < out.shape[0] and 0 <= x < out.shape[1] and r.base[y, x, 3] and (x, y) not in r.protect: out[y, x] = (140, 86, 52, 255)
    return out

def bake_trips():
    meta = {}
    for k in LB.ADULTS:
        r = LB.rig(k); meta[k] = {}
        for name, full in (("depart", False), ("return", True)):
            strip, g = LB.bake_clip(k, name, base_override=with_pack(r, full))
            assert set(np.unique(strip[..., 3])) <= {0, 255}
            save(strip, os.path.join(O5, "actions", f"{k}_{name}.png"))
            meta[k][name] = {"png": f"actions/{k}_{name}.png", "frameW": g["CW"], "frameH": g["CH"], "pivot": [g["PX"], g["PY"]]}
        meta[k]["headTop"] = [float(v) for v in r.anchors["headTop"]]
    return meta

# ───────── 手信 10：HD icon（UI 用）＋1x pixel（返屋 clip 頭頂／屋內擺設）─────────
def souvenirs():
    import long_5abc_ui as U
    os.makedirs(os.path.join(O5, "souvenir"), exist_ok=True); out = []
    for sid, zh in U.SOUV:
        b = U.board(30, 30); U.medal(b, U.P(15), U.P(15), 26, U.C['navy'], sid, 21); U.x3(U.crop(b)).save(os.path.join(O5, f"souvenir/{sid}_medal@3x.png"))
        b = U.board(30, 30); U.icon(b, sid, U.P(15), U.P(15), 24); U.x3(U.crop(b)).save(os.path.join(O5, f"souvenir/{sid}@3x.png"))
        px = pixel_souv(sid); save(px, os.path.join(O5, f"souvenir/{sid}_1x.png"))
        out.append({"id": sid, "zh": zh, "icon": f"souvenir/{sid}@3x.png", "medal": f"souvenir/{sid}_medal@3x.png", "px": f"souvenir/{sid}_1x.png",
                    "pxPivot": [px.shape[1] // 2, px.shape[0] - 1], "colors": int(ncolors(px))})
    return out
SV_RAMP = {"P": ((255, 214, 228), (250, 150, 186), (206, 96, 140)), "B": ((214, 168, 112), (160, 110, 64), (112, 72, 42)), "G": ((170, 230, 120), (100, 180, 84), (60, 130, 60)),
           "Y": ((255, 244, 170), (250, 206, 90), (210, 150, 50)), "S": ((236, 236, 250), (190, 194, 220), (140, 144, 180)), "C": ((190, 230, 255), (110, 170, 236), (70, 112, 190)),
           "R": ((255, 160, 140), (234, 90, 80), (176, 52, 60)), "W": ((255, 255, 255), (244, 240, 236), (214, 206, 206)), "T": ((210, 250, 240), (150, 220, 214), (96, 170, 170)),
           "K": ((255, 222, 240), (246, 186, 220), (210, 140, 190)), "O": ((255, 200, 120), (246, 150, 70), (200, 100, 40)), "V": ((210, 180, 255), (160, 120, 236), (110, 80, 190)),
           "N": ((140, 110, 80), (110, 84, 60), (80, 60, 44))}
SV_PX = {
 "sv_shell": ["...PPPPP...", "..PPWPPWP..", ".PWPPWPPWP.", "PPWPPWPPWPP", "PPWPPWPPWPP", ".PPWPWPWPP.", "..PPPPPPP..", "...PPPPP...", "....PPP...."],
 "sv_pinecone": ["....GG.G...", ".....GG....", "....BBBB...", "...BNBBNB..", "...BBNBBB..", "..BNBBNBB..", "..BBNBBNB..", "...BNBBNB..", "....BBBB...", ".....BB...."],
 "sv_starstone": ["...SSSSS...", "..SSSYSSS..", ".SSSYYYSSS.", ".SSYYYYYSS.", ".SSSYYYSSS.", ".SSYYSYYSS.", "..SSSSSSS..", "...SSSSS..."],
 "sv_feather": [".......CC", "......CCC", ".....CCWC", "....CCWC.", "...CCWCC.", "..CCWCC..", ".CCWCC...", ".CWCC....", "NN.......", "N........"],
 "sv_mushroom": ["...RRRRR...", ".RRWRRRWRR.", "RRRRRWRRRRR", "RRWRRRRRWRR", ".RRRRRRRRR.", "...WWWWW...", "...WWWWW...", "...WWWWW...", "....WWW...."],
 "sv_maple": [".....R.....", "..R..R..R..", "..RRRRRRR..", "RRRRRRRRRRR", ".RRRRRRRRR.", "..RRRRRRR..", ".RR.RRR.RR.", ".....N.....", ".....N....."],
 "sv_bottle": ["....NN....", "....TT....", "...TTTT...", "..TTTTTT..", "..TWWWWT..", "..TWYYWT..", "..TWWWWT..", "..TTTTTT..", "...TTTT..."],
 "sv_cloud": ["...KKK.....", "..KKKKKKK..", ".KKKKKKKKK.", "KKKKKKKKKKK", "KKKKKKKKKKK", ".KKKKKKKKK.", ".....N.....", ".....N.....", ".....N....."],
 "sv_lantern": ["....NNN....", "...NNNNN...", "..YYYYYYY..", ".YYGYYYGYY.", ".YYYYGYYYY.", ".YYGYYYGYY.", "..YYYYYYY..", "...NNNNN...", "....NNN...."],
 "sv_rainbow": ["...RRRRR...", "..ROOOOOR..", ".ROYYYYYOR.", ".ROYGGGYOR.", ".ROYGCGYOR.", ".ROYGGGYOR.", ".ROYYYYYOR.", "..ROOOOOR..", "...RRRRR...", ".....N.....", ".....N....."]}
def pixel_souv(sid):
    fixed = {ch: SV_RAMP[ch][1] for ch in "ROYGC"} if sid == "sv_rainbow" else None
    a = L.auto(SV_PX[sid], outline=OL, ramps=SV_RAMP, hi=True, fixed=fixed)
    if sid == "sv_rainbow": a[2, 4] = (255, 255, 255, 255)
    return limit_colors(a, 12) if ncolors(a) > 12 else a

# ───────── 工作帽 ─────────
JOBS = [("post", "郵差助手", "job_post"), ("garden", "園丁", "job_garden"), ("watch", "守夜", "job_watch"), ("chef", "廚師", "job_chef")]
TIERS = [("t1", "Lv1–2", [1, 2]), ("t2", "Lv3–4 金邊", [3, 4]), ("t3", "Lv5 金星章", [5]), ("t4", "Lv6 金星＋寶石", [6])]
RAMPS = {"N": ((120, 150, 230), (78, 100, 186), (52, 66, 136)), "S": ((255, 236, 160), (236, 196, 108), (196, 150, 70)),
         "W": ((255, 255, 255), (236, 232, 244), (200, 194, 214)), "M": ((96, 104, 190), (70, 74, 150), (48, 50, 108)),
         "R": ((255, 150, 140), (226, 96, 96), (170, 60, 70)), "G": ((160, 226, 120), (100, 180, 84), (60, 130, 60)), "E": ((255, 255, 250), (246, 240, 226), (214, 204, 186))}
GOLD = [(255, 234, 150), (232, 184, 84), (176, 124, 52)]
RAMPS["B"] = ((90, 112, 200), (60, 76, 150), (40, 50, 110)); RAMPS["Y"] = ((255, 244, 190), (246, 214, 128), (214, 170, 84))
def _grid(H, W): return np.full((H, W), ".", dtype="<U1")
def _ell(g, ch, cx, cy, rx, ry, top_only=False):
    yy, xx = np.mgrid[:g.shape[0], :g.shape[1]]; m = ((xx - cx) / max(rx, .5)) ** 2 + ((yy - cy) / max(ry, .5)) ** 2 <= 1.0
    if top_only: m &= yy <= cy
    g[m] = ch
def hat_grid(job, w):
    """回傳 char grid（冇外框）＋ 帽底（band）行號；w＝帽身闊度（單數）"""
    c = (w - 1) / 2
    if job == "post":      # 圓頂帽＋向右帽舌＋白帶
        hh = max(4, w // 2); g = _grid(hh + 2, w + 3); _ell(g, "N", c, hh, c + .3, hh - .2, True)
        g[hh, :w] = "E"; g[hh + 1, int(c):w + 3] = "B"; return g, hh
    if job == "garden":    # 草帽：圓頂＋紅帶＋闊邊
        cw = max(7, w - 4) | 1; cc = c + 2; hh = max(3, cw // 2); g = _grid(hh + 3, w + 4)
        _ell(g, "S", cc, hh, cw / 2 - .2, hh - .2, True); g[hh - 1, int(cc - cw / 2 + 1):int(cc + cw / 2)] = "R"
        g[hh, :] = "Y"; g[hh + 1, 1:-1] = "Y"; g[hh + 2, 3:-3] = "."; return g, hh + 1
    if job == "watch":     # 睡帽：圓錐歪右＋白毛邊
        hh = max(6, int(w * 0.8)); g = _grid(hh + 2, w + 5)
        for j in range(hh):
            t = j / hh; half = c * (0.15 + 0.85 * t); off = (1 - t) ** 1.6 * 4.5
            x0 = int(round(c - half + off)); x1 = int(round(c + half + off)); g[j, max(0, x0):x1 + 1] = "M"
        g[hh, :w] = "E"; g[hh + 1, 1:w - 1] = "E"; return g, hh + 1
    # chef：三泡頂＋高身＋白帶
    r = max(2.0, w / 5.0); top = int(r) + 1; hh = max(top + 3, int(w * 0.7)); g = _grid(hh + 2, w + 2)
    _ell(g, "W", c + 1, r + .6, r + 1.0, r + .6)                     # 中間大泡
    for bx in (r + .6, w + .4 - r): _ell(g, "W", bx, r + 2.0, r, r)  # 兩邊細泡
    g[top + 1:hh, 1:w + 1] = "W"; g[hh:hh + 2, 1:w + 1] = "E"
    for bx in (int(round(c + 1 - r - .6)), int(round(c + 1 + r + .6))):   # 泡之間摺痕
        for y in range(top, top + 3):
            if g[y, bx] != ".": g[y, bx] = "E"
    return g, hh + 1
def hat_img(job, tier, w):
    g, band = hat_grid(job, w)
    a = L.auto(["".join(r) for r in g], outline=OL, ramps=RAMPS, hi=True); H_, W_ = a.shape[:2]; band += 1   # auto pad=1
    solid = lambda y, x: 0 <= y < H_ and 0 <= x < W_ and a[y, x, 3] and tuple(a[y, x, :3]) != OL
    cx = int(round((w - 1) / 2)) + 1
    if job == "post":      # 正面信封章
        for dy in (0, 1):
            for dx in (-1, 0, 1):
                if solid(band - 3 + dy, cx + dx): a[band - 3 + dy, cx + dx] = (250, 246, 236, 255)
        if solid(band - 2, cx): a[band - 2, cx] = (226, 96, 120, 255)
    if job == "garden":    # 頂出芽仔
        ys, xs = np.nonzero(a[..., 3]); top = ys.min(); x = int(np.median(xs[ys == top])); ext = np.zeros((3, W_, 4), np.uint8)
        a = np.concatenate([ext, a], 0); band += 3; H_ += 3; top += 3
        a[top - 1, x] = (*OL, 255); a[top - 2, x] = (90, 150, 70, 255); a[top - 3, x - 1] = (130, 210, 100, 255); a[top - 3, x + 1] = (130, 210, 100, 255)
        a[top - 2, x - 1] = (*OL, 255); a[top - 2, x + 1] = (*OL, 255); a[top - 3, x] = (*OL, 255)
    if job == "watch":     # 尖端吊住月亮仔、帽身兩粒星
        ys, xs = np.nonzero(a[..., 3]); top = ys.min(); tx = xs[ys == top].max()
        for (yy, xx, cc) in ((top, tx + 1, (255, 226, 120)), (top + 1, tx + 1, (255, 226, 120)), (top + 1, tx + 2, (255, 240, 170)), (top + 2, tx + 1, (214, 170, 84))):
            if 0 <= yy < H_ and xx < W_: a[yy, xx] = (*cc, 255)
        for (yy, xx) in ((band - 3, cx - 2), (band - 5, cx + 1)):
            if solid(yy, xx): a[yy, xx] = (255, 240, 170, 255)
    # 級：t2 金帶、t3 加金星章、t4 再加粉紅寶石
    if tier != "t1":
        y = band - (2 if job in ("garden",) else 1) if job != "post" else band - 1
        xs_ = [x for x in range(W_) if solid(y, x)]
        for x in xs_: a[y, x] = (*GOLD[1], 255)
        if xs_: a[y, xs_[0]] = (*GOLD[0], 255); a[y, xs_[-1]] = (*GOLD[2], 255)
    if tier in ("t3", "t4"):
        sx_, sy_ = cx - max(2, w // 4), band - 3
        for (dy, dx, cc) in ((0, 0, (255, 255, 230)), (-1, 0, GOLD[0]), (0, -1, GOLD[1]), (0, 1, GOLD[1]), (1, 0, GOLD[2])):
            if 0 <= sy_ + dy < H_ and 0 <= sx_ + dx < W_ and a[sy_ + dy, sx_ + dx, 3]: a[sy_ + dy, sx_ + dx] = (*cc, 255)
    if tier == "t4":
        gx, gy = cx + max(2, w // 4), band - 3
        if solid(gy, gx): a[gy, gx] = (255, 110, 160, 255)
        if solid(gy - 1, gx): a[gy - 1, gx] = (255, 206, 224, 255)
    if ncolors(a) > 12: a = limit_colors(a, 12, protect=[OL, *GOLD, (255, 110, 160), (255, 206, 224), (250, 246, 236), (226, 96, 120), (255, 255, 230)])
    return a, band
HPAD = (6, 20)   # hat overlay padding（左右、頂）
def hat_patch(r, job, tier):
    S, W0 = r.base.shape[:2]; o = np.zeros((S + HPAD[1], W0 + 2 * HPAD[0], 4), np.uint8)
    hx_, hy = [int(round(v)) for v in r.anchors["headTop"]]
    w = int(np.clip(round(r.headHW * 1.3), 9, 19)); w += (w % 2 == 0)
    a, band = hat_img(job, tier, w); H_, W_ = a.shape[:2]
    m = r.base[..., 3] > 0                              # 頭頂：headTop 附近 3 欄最高實色（唔計燈泡）
    for (x, y) in r.protect: m[y, x] = False
    xa, xb = max(0, hx_ - w // 2), min(m.shape[1], hx_ + w // 2 + 1)
    cnt = m[:, xa:xb].sum(1); ok = np.nonzero(cnt >= max(3, (xb - xa) * 0.45))[0]   # 第一行夠闊（≥45% 帽闊）先當頭頂，唔會企喺尖角上
    top = int(ok[0]) if len(ok) else hy
    if r.eyes: top = min(top, min(e['box'][1] for e in r.eyes) - 6)   # 帽邊永遠喺眼上面 ≥3px
    lx = {"post": 1, "garden": 3, "watch": 1, "chef": 2}[job]     # 帽身中心喺 grid 嘅 x
    X = hx_ - (w - 1) // 2 - lx + HPAD[0]; Y = top + 3 - band + HPAD[1]
    paste(o, a, X, Y)
    for (x, y) in r.protect:      # 燈泡永遠喺帽上面露出
        o[y + HPAD[1], x + HPAD[0]] = 0
    return o

def hats():
    meta = {}
    for k in LB.ADULTS:
        r = LB.rig(k); meta[k] = {}; clips = LB.clips_of(k)
        for jid, jzh, _ in JOBS:
            blocks = []; rows_all = []; y = 0
            for tid, _, _ in TIERS:
                patch = hat_patch(r, jid, tid)
                atlas, rows = LB.overlay_atlas(k, patch, HPAD, clips, pad=HPAD)
                for rw in rows: rw["y"] += y; rw["tier"] = tid
                y += atlas.shape[0]; blocks.append(atlas); rows_all += rows
            Wt = max(b.shape[1] for b in blocks); A = np.zeros((y, Wt, 4), np.uint8); yy = 0
            for b in blocks: A[yy:yy + b.shape[0], :b.shape[1]] = b; yy += b.shape[0]
            save(A, os.path.join(O5, "hats", f"{k}_hat_{jid}.png"))
            meta[k][jid] = {"png": f"hats/{k}_hat_{jid}.png", "rows": rows_all}
    return meta

def data(trips, sv, hm):
    c = LB.CLIPS5
    return {"version": "5b-1.0", "spec": "docs-gdd/series2-4a4b-spec.md v1.1 §5b",
     "daily": {"who": "主養以外嘅屋內成年", "choose": ["expedition", "job", "rest"], "perDay": 1, "shardCapPerDay": 12, "capNote": "遠足＋工作合共每日最多 12 碎"},
     "expedition": {"maxPerDay": 2, "durationH": 24, "shards": [5, 10], "furnitureChance": 0.3, "souvenirPool": [s["id"] for s in sv], "diary": "團絨日記一格故事",
                    "clips": {n: {kk: c[n][kk] for kk in ("frames", "frameMs", "loop", "note")} for n in ("depart", "return")},
                    "clipData": {n: {kk: c[n][kk] for kk in ("body", "face", "fx")} for n in ("depart", "return")},
                    "souvenirOnReturn": c["return"]["souvenir"], "forms": trips,
                    "engine": "depart：播完第 3 格之後每格 x+2px 向房門（右），7–9 格 alpha 1→0；return：0–3 格由右邊入（每格 x−2px），第 5–9 格喺 headTop（跟變形）上 10px 畫手信 1x，bob 0/−1/0/1/0"},
     "souvenirs": sv,
     "jobs": {"list": [{"id": j, "zh": z, "icon": f"ui/icon_{ic}@3x.png"} for j, z, ic in JOBS], "levels": {"min": 1, "max": 5, "maxWithFamilyLv7": 6, "daysPerLevel": 5, "shardsPerDay": "= 等級（Lv1＝1 碎 … Lv6＝6 碎）"},
              "tiers": [{"id": t, "zh": z, "levels": lv} for t, z, lv in TIERS],
              "hat": {"pad": list(HPAD), "atlas": "每形態 × 工作一張；行＝tier × clip（rows[].tier／clip／y／frames／frameW／frameH／pivot／petPng）", "draw": "pet strip 第 i 格之後，用 row.pivot 對齊 pet pivot 畫 overlay 第 i 格"},
              "forms": hm}}

if __name__ == "__main__":
    os.makedirs(os.path.join(O5, "actions"), exist_ok=True); os.makedirs(os.path.join(O5, "hats"), exist_ok=True)
    tr = bake_trips(); print("trips", len(tr))
    sv = souvenirs(); print("souvenirs", len(sv))
    hm = hats(); print("hats", len(hm) * 4)
    LB.jdump(data(tr, sv, hm), os.path.join(O5, "long_5b.json")); print("ok")
