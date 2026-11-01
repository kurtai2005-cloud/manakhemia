# series2 細佬：蛋、S1 蛋殼仔、S2 BB（全系共用）＋ S4 少年 ×8（由 from_ref 1 階拉高＋系頸巾）
import json, os
import numpy as np
from series2_lib import *

OL = (52, 38, 74)                                   # 細佬共用外框（深紫，近 from_ref 外框）
SHELL = ((255, 252, 240), (250, 238, 212), (232, 212, 182), (204, 178, 160))
SPK = [BLUSH, (140, 200, 250), (255, 214, 100)]
BODY = ((255, 250, 252), (246, 234, 250), (226, 210, 240), (198, 180, 226))   # BB：未定色（奶白淡紫）
FOOT = (232, 212, 182)
CRACK = (120, 90, 110)
LIGHT = ((255, 255, 236), (255, 236, 160), (236, 196, 120))

def zig_cut(mask, ybase, amp=2, period=4, up=True, phase=0):
    """喺 ybase 附近切鋸齒：up=True → 保留上面"""
    m = mask.copy(); h, w = m.shape
    for x in range(w):
        t = (x + phase) % period; off = (t if t <= period // 2 else period - t) * amp // (period // 2)
        yc = ybase + off - amp // 2
        if up: m[yc:, x] = False
        else: m[:yc, x] = False
    return m

def egg(crack=0):
    """新蛋：奶油殼＋三色粉彩點（暗示 8 系未定）。crack 0..3＝裂紋階段（孵化用）"""
    img = canvas(S, S)
    m = ellipse(S, S, 24, 33.5, 10.5, 13) & (np.mgrid[0:S, 0:S][0] <= GROUND)
    Y = np.mgrid[0:S, 0:S][0]
    m |= ellipse(S, S, 24, 30, 9.5, 12.5) & (Y < 33)
    shade_body(img, m, SHELL, OL)
    for (x, y), c in zip([(19, 28), (28, 25), (26, 36), (18, 38), (30, 33), (22, 22)], SPK * 2):
        put(img, x, y, c); put(img, x + 1, y, c)
        if y < 34: put(img, x, y + 1, c)
    put(img, 20, 24, WHITE); put(img, 19, 25, WHITE)
    cr = [[(24, 21), (24, 22), (23, 23), (24, 24)],
          [(25, 25), (26, 26), (25, 27), (22, 24), (21, 25)],
          [(20, 26), (19, 27), (27, 27), (28, 28), (29, 28), (18, 28)]]
    for k in range(crack):
        for (x, y) in cr[k]: put(img, x, y, CRACK)
    return img, m

def s1(frame="idle", f=0):
    """蛋殼仔：頂住上半殼（鋸齒邊）＋下半殼兜住，只露一對眼。frame: idle/blink/cry/eat/sleep 用唔同眼"""
    img = canvas(S, S); Y, X = np.mgrid[0:S, 0:S]
    body = ellipse(S, S, 24, 35.5, 9.5, 9) & (Y <= GROUND - 2)
    bodyc = canvas(S, S); shade_body(bodyc, body, (BODY[1], BODY[2], BODY[2], BODY[3]), OL, spec=False, inner_shade=False)
    draw_blush(bodyc, 15, 37); draw_blush(bodyc, 30, 37)
    # 腳仔
    feet = canvas(S, S)
    for fx in (19, 27):
        for dx in range(3): put(feet, fx + dx, GROUND, OL); put(feet, fx + dx, GROUND - 1, FOOT)
        put(feet, fx - 1, GROUND - 1, OL); put(feet, fx + 3, GROUND - 1, OL)
    paste(img, feet, 0, 0); paste(img, bodyc, 0, 0)
    # 上殼（帽）：鋸齒底 y≈31
    top = ellipse(S, S, 24, 29.5, 10.5, 10.5) & (Y < 34)
    top = zig_cut(top, 30, amp=2, period=6, up=True, phase=1)
    tc = canvas(S, S); shade_body(tc, top, SHELL, OL)
    put(tc, 20, 23, SPK[0]); put(tc, 21, 23, SPK[0]); put(tc, 28, 21, SPK[1]); put(tc, 29, 21, SPK[1]); put(tc, 25, 26, SPK[2])
    # 殼面細紋
    for (x, y) in ((17, 27), (18, 28), (31, 25), (30, 26)): put(tc, x, y, SHELL[3])
    paste(img, tc, 0, 0)
    # 下殼：鋸齒頂 y≈39
    bot = ellipse(S, S, 24, 40.5, 11, 6.5) & (Y <= GROUND - 1)
    bot = zig_cut(bot, 40, amp=2, period=6, up=False, phase=4)
    bc = canvas(S, S); shade_body(bc, bot, SHELL, OL, spec=False)
    put(bc, 18, 42, SPK[1]); put(bc, 19, 42, SPK[1]); put(bc, 29, 43, SPK[0]); put(bc, 30, 43, SPK[0])
    paste(img, bc, 0, 0)
    eyes = [(18, 33), (26, 33)]
    return img, eyes, {"bulbXY": [24, 17], "mouth": None}

def s2_base():
    """BB：圓粒＋好細手腳＋頭頂一點未定色光"""
    img = canvas(S, S); Y, X = np.mgrid[0:S, 0:S]
    body = ellipse(S, S, 24, 33.5, 12.5, 12) & (Y <= GROUND - 1)
    # 手仔（兩側細圓）
    arms = canvas(S, S)
    for ax in (11.2, 36.8):
        am = ellipse(S, S, ax, 37, 2.6, 2.3); shade_body(arms, am, BODY[1:] + (BODY[3],), OL, spec=False, inner_shade=False)
    feet = canvas(S, S)
    for fx in (18, 27):
        fm = ellipse(S, S, fx + 1.5, GROUND - 0.5, 2.6, 1.8); shade_body(feet, fm, BODY[1:] + (BODY[3],), OL, spec=False, inner_shade=False)
    paste(img, feet, 0, 0); paste(img, arms, 0, 0)
    bc = canvas(S, S); shade_body(bc, body, BODY, OL); paste(img, bc, 0, 0)
    # 頭頂光：莖＋3×3 光點
    for y in (20, 21, 22): put(img, 24, y, BODY[3])
    grid(img, [".OOO.", "OWWBO", "OWBYO", ".OYO.", "..O.."], 22, 15, {"O": OL, "W": LIGHT[0], "Y": LIGHT[1], "B": BLUSH})
    # 面
    eyes = [(17, 31), (27, 31)]
    for (x, y) in eyes: draw_eye(img, x, y)
    draw_mouth(img, 22, 37); draw_blush(img, 14, 36); draw_blush(img, 31, 36)
    return img, eyes, {"bulbXY": [24, 17], "mouth": [22, 37, 4]}

if __name__ == "__main__":
    out = canvas(S * 5, S)
    for i, c in enumerate(range(4)): paste(out, egg(c)[0], i * S, 0)
    a, e, _ = s1()
    for (x, y) in e: draw_eye(a, x, y)
    big = canvas(S * 7, S); paste(big, out, 0, 0); paste(big, a, 4 * S, 0); paste(big, s2_base()[0], 5 * S, 0)
    bg = np.zeros_like(big); bg[...] = (90, 80, 120, 255); paste(bg, big, 0, 0)
    Image.fromarray(bg[8:,:]).resize((S * 7 * 8, (S-8) * 8), 0).save("/workspace/s2scratch/forms_test2.png")

# ───────── S4 少年：from_ref 1 階 → 拉高身（插行）＋特徵拉長＋系頸巾 ─────────
SCARF = {"A": ((255, 222, 110), (226, 164, 60)), "B": ((255, 170, 196), (222, 112, 150)), "C": ((150, 214, 255), (84, 150, 225)),
         "D": ((255, 206, 96), (214, 140, 52)), "E": ((150, 232, 182), (78, 178, 128)), "F": ((255, 150, 176), (214, 92, 128)),
         "G": ((168, 236, 255), (92, 178, 226)), "H": ((255, 218, 110), (220, 160, 64))}
S4_NAME = {"A": "滴滴少年", "B": "燈燈少年", "C": "火仔少年", "D": "熔石少年", "E": "火糰少年", "F": "星彈少年", "G": "夜糰少年", "H": "月角少年"}
S4_ROWS = {r: (2, 1) for r in "ABCDEFGH"}
def _tuned(): return json.load(open(os.path.join(T48, "tuned.json")))
def _anch(): return json.load(open(os.path.join(ART, "sprites/tuanrong/reactions/anchors.json")))

def insert_rows(img, y, n):
    """喺 y 行重複 n 次，y 以上全部上移 n（腳唔郁）"""
    assert not (img[:n, :, 3] > 0).any(), "頂部唔夠位"
    idx = list(range(0, y + 1)) + [y] * n + list(range(y + 1, img.shape[0]))
    return img[idx][n:]

def s4(row):
    T = _tuned()["creatures"]; key = f"{row}1"; m = T[key]; A = _anch()[key]["anchors"]
    img = rgba(os.path.join(T48, "sprites", f"{key}_48.png"))
    n, k = S4_ROWS[row]
    ey = min(e["y"] for e in m["eyes"]); mo = (m.get("face") or {}).get("mouth")
    yb = min(max(ey + 7, (mo[1] + 2) if mo else 0), 42)
    img = insert_rows(img, yb, n)
    yf = int(A["headTop"][1]) - 2 - n
    img = insert_rows(img, yf, k)
    sh = n                                   # 眼／嘴上移 n；燈泡上移 n+k
    eyes = [dict(e, y=e["y"] - sh) for e in m["eyes"]]
    bx, by = m["bulbXY"]; bulb = [bx, by - n - k]
    mouth = [mo[0], mo[1] - sh, mo[2]] if mo else None
    # 頸巾：嘴下 2 行
    a = img[..., 3] == 255
    edge = a & ~ndi.binary_erosion(a, structure=CROSS, border_value=0)
    olc = hexc(m["outline"]); c0, c1 = SCARF[row]
    pal = np.unique(img[a][:, :3], axis=0).astype(int)
    def snap(c):
        d = np.abs(pal - np.array(c)).sum(1); i = int(np.argmin(d))
        return tuple(int(t) for t in pal[i]) if d[i] < 90 else c
    c0, c1 = snap(c0), snap(c1)
    ys = (mouth[1] + 3) if mouth else (max(e["y"] for e in eyes) + 6)
    ys = min(ys, 41)
    for x in range(S):
        for j, c in ((0, c0), (1, c1)):
            y = ys + j
            if a[y, x] and not edge[y, x]: img[y, x, :3] = c
            elif a[y, x] and edge[y, x]: img[y, x, :3] = olc
    # 結（右邊垂落三角，出身 1–2px）
    xs = np.nonzero(a[ys])[0]; xr = int(xs.max()) - 3
    knot = [".OOO.", "OaabO", "OabO.", ".OO.."]
    grid(img, knot, xr, ys + 1, {"O": olc, "a": c0, "b": c1})
    featc = add_feature(img, row, eyes, olc, bulb)
    cols = np.unique(img[img[..., 3] == 255][:, :3], axis=0)
    pink = [tuple(c) for c in cols if c[0] > 200 and c[1] < 175 and c[2] > 100 and c[0] - c[1] > 60]
    img = limit_colors(img, 12, protect=[olc, EYE_DK, WHITE, c0, c1] + pink + featc)
    meta = {"name": S4_NAME[row], "from": key, "outline": m["outline"], "eyes": eyes, "bulbXY": bulb, "bulbType": m["bulbType"],
            "face": {"mouth": mouth, "blush": m["face"]["blush"]}, "insertRows": {"body": [yb, n], "feature": [yf, k]}, "scarfRow": ys,
            "lavaVeins": 0, "veinPx": []}
    return img, meta

YEL = ((255, 230, 130), (236, 176, 64)); FLM = ((255, 214, 90), (240, 120, 50))
EAR = ["..O..", ".OaO.", "OaabO", "OabbO"]
HORN = [".O...", "OaO..", "OabO.", ".OabO", ".OabO"]
SPIKE = ["..O..", ".OaO.", ".OaO.", "OabbO"]
TAIL = ["OO....", "OaOO..", "OaabOO", ".OabbO", "..OObO", "....OO"]
def body_cols(img, eyes):
    ex = int(np.mean([e["x"] for e in eyes])) + 2; ey = int(np.mean([e["y"] for e in eyes]))
    c = img[ey - 4, ex - 1:ex + 2, :3].reshape(-1, 3); a = tuple(int(t) for t in c[1])
    return a, mix(a, (20, 10, 40), 0.25)
def _top(img, x, ylim):
    col = np.nonzero(img[ylim:, x, 3] == 255)[0]
    return ylim + int(col[0]) if len(col) else None
def stamp_grid(img, g, x, y, cmap, flip=False):
    for j, r in enumerate(g):
        rr = r[::-1] if flip else r
        for i, ch in enumerate(rr):
            if ch in cmap: put(img, x + i, y + j, cmap[ch])
def add_feature(img, row, eyes, olc, bulb):
    """系特徵提前出現（S5 嘅細版）：A 小魚尾、C 火耳、D 岩尖、E 火尾、F/G 黃角耳仔、H 角加長；B 燈莖已拉長"""
    a, b = body_cols(img, eyes)
    xl = min(e["x"] for e in eyes) - 3; xr = max(e["x"] for e in eyes) + 6
    ylim = bulb[1] + 4
    out = []
    if row == "C":
        ey = min(e["y"] for e in eyes)
        for x0, fl in ((xl - 4, False), (xr, True)):
            stamp_grid(img, HORN, x0, ey - 9, {"O": olc, "a": FLM[0], "b": FLM[1]}, fl)
        out += list(FLM)
    if row in "FG":
        col = YEL; out += list(YEL)
        for x0, fl in ((xl - 1, False), (xr - 3, True)):
            t = _top(img, x0 + 2, ylim)
            if t is not None: stamp_grid(img, EAR, x0, t - 3, {"O": olc, "a": col[0], "b": col[1]}, fl)
    if row == "D":
        for x0 in (xl, xr - 4):
            t = _top(img, x0 + 2, ylim)
            if t is not None: stamp_grid(img, SPIKE, x0, t - 3, {"O": olc, "a": (255, 214, 110), "b": a})
    if row in "AE":
        al = img[..., 3] == 255; ys, xs = np.nonzero(al[ylim:]); ys = ys + ylim
        yc = int(np.percentile(ys, 70)); xs_row = np.nonzero(al[yc])[0]
        col = (a, b) if row == "A" else FLM; out += list(col)
        stamp_grid(img, TAIL, int(xs_row.min()) - 4, yc - 3, {"O": olc, "a": col[0], "b": col[1]})
    return out
