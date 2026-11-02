#!/usr/bin/env python3
"""breakthrough 6c 夢境探索 — 美術總 builder（遊美 2026-11-02）
輸出 art/breakthrough/6c/：tileset ×4、fog、夢碎片 ×4、rail icon ×2、夢卡 ×20＋卡背、入夢／出夢 transition、dream_bg、
49 形態 dream_walk（閉眼夢遊，幀大小／pivot＝idle）、睡帽 overlay S/M/L＋逐幀位置、dream6c.json、preview_6c_3x.png。
規矩：純 Pillow／numpy 程序化；alpha 0／255；新畫嘅嘢 ≤12 色；光左上；全部有 @3x（nearest ×3）。"""
import os, sys, json
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reactions_lib as L
import build_breakthrough_6b_walk as W6
import build_breakthrough_6c_tiles as TL
import build_breakthrough_6c_cards as CD
from bt6_px import save, ncol, cols, hx, BAYER, LINE, over, rgba, Spr, render

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "art/breakthrough/6c")
NC_DIR = os.path.join(ROOT, "art-pet/sprites/tuanrong/accessories/source/nightcap")
SW, SH = 195, 422
WALK_FPS, NF = 6, 6
TR_FPS, TR_NF = 8, 10

def save2(a, rel):
    p = os.path.join(OUT, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    save(a, p); save(a, p.replace(".png", "@3x.png"), 3)
    return {"1x": rel, "3x": rel.replace(".png", "@3x.png"), "size": [int(a.shape[1]), int(a.shape[0])], "colors": ncol(a)}

# ------------------------------------------------------------------ 睡帽（沿用 accessories/nightcap：front＋tail 合成）
def nightcap(sz):
    it = json.load(open(os.path.join(NC_DIR, "item.json")))
    v = it["views"]["front"][sz]; pt = it["parts"]["tail"][sz]
    fr = rgba(os.path.join(NC_DIR, f"front_{sz}.png")); tl = rgba(os.path.join(NC_DIR, f"part_tail_{sz}.png"))
    tx = int(round(v["anchors"]["tip"][0])) - pt["pivot"][0]; ty = int(round(v["anchors"]["tip"][1])) - pt["pivot"][1]
    ox, oy = max(0, -tx), max(0, -ty)
    Wc = max(fr.shape[1] + ox, tx + ox + tl.shape[1]); Hc = max(fr.shape[0] + oy, ty + oy + tl.shape[0])
    a = np.zeros((Hc, Wc, 4), np.uint8); over(a, tl, tx + ox, ty + oy); over(a, fr, ox, oy)
    piv = (int(round(v["pivot"][0])) + 1 + ox, int(round(v["pivot"][1])) + 1 + oy)           # 帽簷底中（png 有 1px 外描 pad）
    return a, piv, v["w"]

# ------------------------------------------------------------------ dream walk
def close_eyes(r):
    b = r.base.copy()
    for e in r.eyes:
        sk = np.array(list(e["skin"]) + [255], np.uint8); ink = np.array(list(e["ink"]) + [255], np.uint8)
        for (x, y) in e["pix"]: b[y, x] = sk
        x0, y0, x1, y1 = e["box"]; ym = (y0 + y1) // 2
        if x1 - x0 >= 2:
            b[ym, x0] = ink; b[ym, x1] = ink; b[ym + 1, x0 + 1:x1] = ink        # ‿
        else:
            b[ym + 1, x0:x1 + 1] = ink
    return b

def dream_frames(r, base):
    H, Wd = base.shape[:2]; m = base[..., 3] == 255
    ys, xs = np.where(m); top = ys.min(); right = xs.max()
    split = int(round((ys.min() + ys.max()) / 2)); maxup = top; canlean = right < Wd - 1
    feet = W6.find_feet(r.base, r.pivot)
    fr, mv = [], []
    if feet:
        Lm, Rm, _ = feet
        footL = np.where(Lm[..., None], base, 0).astype(np.uint8); footR = np.where(Rm[..., None], base, 0).astype(np.uint8)
        body = base.copy(); body[Lm | Rm] = 0
        for bdy, lean, (ldx, ldy), (rdx, rdy) in W6.FEET_SEQ:
            bdy = max(bdy, -maxup); lean = lean if canlean else 0
            f = np.zeros_like(base)
            for ft, dx, dy in ((footL, ldx, ldy), (footR, rdx, rdy)):
                W6.over(f, W6.shift(ft, dx, dy))
                if bdy < dy: W6.over(f, W6.shift(ft, dx, bdy))
            W6.over(f, W6.body_frame(body, bdy, lean, split)); fr.append(f); mv.append((lean, bdy))
        mode = "feet"
    else:
        for bdy, lean in W6.HOP_SEQ:
            bdy = max(bdy, -maxup); lean = lean if canlean else 0
            fr.append(W6.body_frame(base, bdy, lean, split)); mv.append((lean, bdy))
        mode = "hop"
    return fr, mv, mode

def head_width(base, y):
    row = np.where(base[min(base.shape[0] - 1, max(0, y)), :, 3] == 255)[0]
    return int(row.max() - row.min() + 1) if len(row) else 0

# ------------------------------------------------------------------ transition（入夢：外圍向中心收窄嘅夜幕 iris＋星；出夢＝倒播）
TRP = dict(n0='#0C0920', n1='#181D3C', n2='#28316A', n3='#3F4E8E', st='#FFE08A', sth='#FFF6CF', mo='#FFD45A', lv='#C9C0F0')
def transition():
    yy, xx = np.mgrid[0:SH, 0:SW]; bay = BAYER[yy % 4, xx % 4]; P = {k: hx(v) for k, v in TRP.items()}
    cx, cy = SW / 2, SH * 0.45; d = np.hypot((xx - cx) * 1.0, (yy - cy) * 0.62); dmax = d.max() + 4
    rng = np.random.RandomState(6); stars = [(rng.randint(4, SW - 4), rng.randint(4, SH - 4), rng.rand()) for _ in range(46)]
    frames = []
    for i in range(TR_NF):
        t = (i + 1) / TR_NF; R = dmax * (1 - t) ** 1.15           # 未覆蓋半徑（最後一幀＝0，全黑夜）
        a = np.zeros((SH, SW, 4), np.uint8)
        cover = (d > R + 10 * bay) if i < TR_NF - 1 else np.ones_like(d, bool)   # Bayer 鋸齒邊（冇半透明）；最後一幀全滿
        a[cover] = P['n1']
        a[cover & (d > max(R + 26, dmax * .62)) & (bay < .5)] = P['n0']   # 四角暗角（Bayer）
        a[cover & (d < R + 16)] = P['n2']; a[cover & (d < R + 6 + 4 * bay)] = P['n3']
        for (sx, sy, k) in stars:
            if cover[sy, sx] and d[sy, sx] > R + 14:
                a[sy, sx] = P['sth'] if k > .7 else P['st'] if k > .35 else P['lv']
                if k > .8 and 0 < sx < SW - 1: a[sy, sx - 1] = a[sy, sx + 1] = a[sy - 1, sx] = a[sy + 1, sx] = P['st']
        if i >= TR_NF - 3:                                         # 月亮喺中間浮現（最尾 3 幀）
            mr = 6 + 4 * (i - (TR_NF - 3)); md = np.hypot(xx - cx, yy - cy); mc = np.hypot(xx - cx - mr * .5, yy - cy + mr * .35)
            moon = (md <= mr) & (mc > mr * .82); a[moon] = P['mo']; a[moon & (md < mr - 1) & (xx - cx < -mr * .3) & (yy - cy < 0)] = P['sth']
            ring = (md > mr) & (md <= mr + 1) & (mc > mr * .82 + 1); a[ring] = LINE
        frames.append(a)
    return frames

# ------------------------------------------------------------------ dream_bg（夢境地圖底，195×422：夜空 gradient＋星＋底雲）
BGP = dict(n0='#0C0920', n1='#10132A', n2='#1B1846', n3='#2C2868', vi='#574F8A', st='#FFE08A', sth='#FFF6CF', c0='#8F85C2', c1='#C9C0F0', c2='#F3EEFA', mo='#FFD45A')
def dream_bg():
    yy, xx = np.mgrid[0:SH, 0:SW]; bay = BAYER[yy % 4, xx % 4]; P = {k: hx(v) for k, v in BGP.items()}
    a = np.zeros((SH, SW, 4), np.uint8); t = yy / SH + 0.08 * np.sin(xx / 23.0)
    a[:] = P['n0']; a[t > .18 + .12 * bay] = P['n1']; a[t > .42 + .12 * bay] = P['n2']; a[t > .7 + .12 * bay] = P['n3']
    nb = (np.hypot(xx - 150, (yy - 80) * 1.6) < 40 + 10 * np.sin(xx / 6.0)) & (bay > .55); a[nb & (t < .42)] = P['n2']   # 淡星雲
    rng = np.random.RandomState(9)
    for _ in range(90):
        x, y = rng.randint(2, SW - 2), rng.randint(2, SH - 70); k = rng.rand()
        a[y, x] = P['sth'] if k > .85 else P['st'] if k > .6 else P['c0'] if k > .3 else P['vi']
        if k > .94: a[y, x - 1] = a[y, x + 1] = a[y - 1, x] = a[y + 1, x] = P['st']
    md = np.hypot(xx - 28, yy - 24); mc = np.hypot(xx - 33, yy - 20); moon = (md <= 10) & (mc > 9)
    a[moon] = P['mo']; a[moon & (xx < 24) & (yy < 26)] = P['sth']
    a[(md > 10) & (md <= 11) & (mc > 10)] = LINE
    for (cx, cy, rx, ry) in ((30, 404, 44, 14), (100, 412, 60, 14), (170, 402, 40, 14), (-5, 392, 26, 10), (198, 388, 24, 10)):
        e = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1; a[e] = P['c1']
        a[e & (((xx - cx + 3) / rx) ** 2 + ((yy - cy + 3) / ry) ** 2 > 1)] = P['c2']
        a[e & (((xx - cx - 2) / rx) ** 2 + ((yy - cy - 3) / ry) ** 2 > 1)] = P['c0']
    return a

# ------------------------------------------------------------------ main
def main():
    os.makedirs(OUT, exist_ok=True)
    J = {"version": 1, "batch": "breakthrough 6c 夢境探索", "spec": "docs-gdd/breakthrough-6a6d-spec.md §6c", "screen": [SW, SH],
         "keys": {}, "cards": {}, "pets": {}}
    K = J["keys"]
    # tiles
    for th in TL.THEMES:
        ts = TL.tileset(th); strip = np.concatenate(ts, 1)
        K[f"6c:tile_{th}"] = dict(save2(strip, f"tiles/tile_{th}.png"), tile=[TL.T, TL.T], variants=TL.NV,
                                  note="橫條 4 款；款 v 喺 x＝v×56；建議 variant＝(i＋theme seed)%4；中間留空俾團絨企")
    K["6c:fog"] = dict(save2(TL.fog(), "tiles/fog.png"), tile=[TL.T, TL.T], note="未揭開格；75% 棋盤實色（取代 rgba(10,8,26,.82)），透出去係 dream_bg")
    for n, a in TL.icons().items():
        key = "6c:" + n.replace("frag_", "frag_") if n.startswith("frag") else "icon_" + n[3:]
        K[key] = dict(save2(a, f"icons/{n}.png"), note="16×16，同 kit_hd2d_v2 ic_* 同規格" + ("；碎片：顯示 48 css＝16 art ×3" if n.startswith("frag") else "；rail icon"))
    # cards
    for cid, title in CD.CARDS:
        K[f"6c:card_{cid}"] = dict(save2(CD.card(cid), f"cards/card_{cid}.png"), theme=CD.THK[cid[0]], title=title)
        J["cards"][cid] = {"title": title, "theme": CD.THK[cid[0]], "index": int(cid[1]), "key": f"6c:card_{cid}"}
    K["6c:card_back"] = dict(save2(CD.card_back(), "cards/card_back.png"), note="未解鎖卡")
    # transition
    tf = transition(); strip = np.concatenate(tf, 1)
    K["6c:transition"] = dict(save2(strip, "fx/transition_in.png"), frames=TR_NF, fps=TR_FPS, durationMs=TR_NF * 1000 // TR_FPS, frame=[SW, SH],
                              enter="0→9 順播（夜幕由外圍收埋，最後一幀全黑夜＋月）", exit="9→0 倒播", loop=False,
                              note="alpha 0／255；未覆蓋部分透明，畫喺現實畫面上面")
    K["6c:dream_bg"] = save2(dream_bg(), "fx/dream_bg.png")
    # nightcap
    caps = {}
    for sz in ("S", "M", "L"):
        a, piv, w = nightcap(sz); caps[sz] = (a, piv, w)
        K[f"6c:nightcap_{sz}"] = dict(save2(a, f"nightcap/nightcap_{sz}.png"), pivot=list(piv), brimW=w,
                                      note="由 accessories/nightcap front＋tail 合成；pivot＝帽簷底中")
    # dream walk
    modes = {}
    for pid in L.ALL_PETS:
        r = L.rig(pid); base = close_eyes(r); fr, mv, mode = dream_frames(r, base); modes[pid] = mode
        Hh, Ww = r.base.shape[:2]; strip = np.concatenate(fr, 1)
        hx_, hy_ = r.anchors["headTop"]; hw = head_width(r.base, int(round(hy_)) + 2)
        sz = "S"
        for s_ in ("M", "L"):
            if caps[s_][2] <= hw + 4: sz = s_
        ca, (pvx, pvy), _ = caps[sz]
        bx, by = int(round(hx_)), int(round(hy_)) + 3
        capxy = [[bx - pvx + dx, by - pvy + dy] for (dx, dy) in mv]
        d = f"per_pet/{pid}"
        info = save2(strip, f"{d}/dream_walk.png")
        J["pets"][pid] = {"frameSize": [Ww, Hh], "pivot": list(r.pivot), "frames": NF, "fps": WALK_FPS, "loop": True, "mode": mode,
                          "1x": info["1x"], "3x": info["3x"], "colors": info["colors"], "idleColors": ncol(r.base),
                          "nightcap": {"size": sz, "key": f"6c:nightcap_{sz}", "xy": capxy, "z": "above",
                                       "note": "xy＝帽圖左上角喺該幀嘅 art 座標（可以係負數＝出幀）；向左行：x'＝frameW−x−capW 並 flipX"}}
    K["6c:dream_walk"] = {"perPet": "per_pet/<pid>/dream_walk.png", "frames": NF, "fps": WALK_FPS, "durationMs": NF * 1000 // WALK_FPS,
                          "facing": "right（向左 flipX，pivot x 鏡像：W−1−px）", "layout": "橫條，幀 i 喺 x＝i×frameW；幀大小／pivot＝該形態 idle",
                          "method": "idle 幀 0 → 閉眼（眼 pix 填返 skin＋ink 畫 ‿）→ 6b 步序（feet／hop）只搬像素", "pets": len(L.ALL_PETS)}
    J["grid"] = {"cols": 3, "rows": 5, "tileArt": TL.T, "tileCss": TL.T * 2,
                 "note": "遊程 st_long6c.js：TX＝23＋c·116 css → art x＝11.5＋58c（半格），建議 TX 改 22 或 24 css 保持整數 art 像素"}
    json.dump(J, open(os.path.join(OUT, "dream6c.json"), "w"), ensure_ascii=False, indent=1)
    print("modes", {m: sum(1 for v in modes.values() if v == m) for m in ("feet", "hop")})
    preview(J, caps)

# ------------------------------------------------------------------ preview（3x）
def font():
    import hd2d_v2_px as X; return X
def preview(J, caps):
    X = font()
    bg = dream_bg().copy()
    # 3×5 grid：tile 56 art，gap 2，x0 11（建議值），y0 64
    order = ['forest', 'lake', 'toy', 'star', 'forest', 'star', 'lake', 'toy', 'forest', 'toy', 'star', 'lake', 'fog', 'fog', 'fog']
    sets = {th: TL.tileset(th) for th in TL.THEMES}; fogt = TL.fog()
    for i, th in enumerate(order):
        x, y = 11 + (i % 3) * 58, 64 + (i // 3) * 58
        over(bg, fogt if th == 'fog' else sets[th][i % 4], x, y)
    # 團絨（sprout）喺格 4 夢遊＋睡帽
    pid = 'sprout'; r = L.rig(pid); fr, mv, _ = dream_frames(r, close_eyes(r)); p = J["pets"][pid]
    ca = caps[p["nightcap"]["size"]][0]; f = fr[1].copy(); Hh, Ww = f.shape[:2]
    can = np.zeros((Hh + 12, Ww + 16, 4), np.uint8); over(can, f, 8, 12); cx, cy = p["nightcap"]["xy"][1]; over(can, ca, cx + 8, cy + 12)
    over(bg, can, 11 + 58 + 28 - (Ww + 16) // 2, 64 + 58 + 40 - Hh - 12)
    over(bg, TL.icons()['frag_star'], 11 + 2 * 58 + 20, 64 + 58 + 20)
    # 頂：碎片計數 pill（文字 FP12）
    t = np.array(X.text_img("夢碎片 3／6", 12).convert("RGBA"))          # FP12，kit 自帶外描＋影
    over(bg, t, (SW - t.shape[1]) // 2, 20)
    big = np.repeat(np.repeat(bg, 3, 0), 3, 1)
    # 右邊 sheet：tiles／cards／transition／dream walk 49
    sheet = sheet_img(J, caps)
    Hc = max(big.shape[0], sheet.shape[0]); out = np.zeros((Hc, big.shape[1] + 24 + sheet.shape[1], 4), np.uint8); out[:] = (40, 36, 64, 255)
    out[:big.shape[0], :big.shape[1]] = big; over(out, sheet, big.shape[1] + 24, 0)
    Image.fromarray(out).save(os.path.join(OUT, "preview_6c_3x.png"), optimize=True)

def outline_text(t):
    """白字＋1px #24172C 外描（8 鄰）"""
    m = t[..., 3] > 127; H, Wd = m.shape; o = np.zeros((H + 2, Wd + 2, 4), np.uint8); mm = np.zeros((H + 2, Wd + 2), bool)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1): mm[1 + dy:H + 1 + dy, 1 + dx:Wd + 1 + dx] |= m
    o[mm] = LINE; o[1:H + 1, 1:Wd + 1][m] = (255, 246, 207, 255); return o

def sheet_img(J, caps):
    rows = []
    pad = lambda a, p=2: np.pad(a, ((p, p), (p, p), (0, 0)))
    for th in TL.THEMES: rows.append(np.concatenate([pad(t) for t in TL.tileset(th)] + [pad(TL.fog())], 1))
    tiles = np.concatenate(rows, 0)
    cards = np.concatenate([np.concatenate([pad(CD.card(c)) for c, _ in CD.CARDS[r * 5:r * 5 + 5]] + ([pad(CD.card_back())] if r == 0 else [np.zeros((40, 32, 4), np.uint8)]), 1) for r in range(4)], 0)
    ic = np.concatenate([pad(a) for a in TL.icons().values()] + [pad(caps[s][0]) for s in "SML"] if False else [pad(a) for a in TL.icons().values()], 1)
    # 49 形態夢遊：每隻顯示 frame 0 ＋睡帽（48 格）
    cells = []
    for pid in L.ALL_PETS:
        r = L.rig(pid); fr, mv, _ = dream_frames(r, close_eyes(r)); p = J["pets"][pid]; ca = caps[p["nightcap"]["size"]][0]
        c = np.zeros((64, 64, 4), np.uint8); f = fr[1]; Hh, Ww = f.shape[:2]; ox, oy = (64 - Ww) // 2, 64 - Hh
        over(c, f, ox, oy); x, y = p["nightcap"]["xy"][1]; over(c, ca, ox + x, oy + y); cells.append(c)
    while len(cells) % 7: cells.append(np.zeros((64, 64, 4), np.uint8))
    pets = np.concatenate([np.concatenate(cells[i:i + 7], 1) for i in range(0, len(cells), 7)], 0)
    tr = transition(); trs = np.concatenate([pad(t[::4, ::4], 1) for t in tr], 1)          # 縮細 ¼ 只係 preview
    parts = [tiles, cards, ic, pets, trs]
    Wm = max(p.shape[1] for p in parts) * 2
    out = []
    for p in parts:
        k = 3 if p.shape[1] * 3 <= 1400 else 2
        b = np.repeat(np.repeat(p, k, 0), k, 1); bb = np.zeros((b.shape[0] + 12, 1400, 4), np.uint8); over(bb, b, 0, 6); out.append(bb)
    return np.concatenate(out, 0)

if __name__ == "__main__":
    main()
