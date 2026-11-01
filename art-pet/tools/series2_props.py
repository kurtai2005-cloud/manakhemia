# series2 4a：8 教錯課道具（像素疊層，畀團絨／細佬拎）＋新 FX — 純程序
import numpy as np
import reactions_lib as L
from series2_lib import canvas, paste, WHITE

OLP = (52, 36, 70)
R = dict(L.RAMP)
R.update({"T": ((170, 236, 255), (104, 196, 244), (60, 140, 214)),       # 水壺藍
          "K": ((168, 120, 84), (132, 90, 62), (96, 64, 46)),             # 木
          "N": ((255, 120, 100), (226, 64, 64), (170, 36, 52)),           # 辣椒紅
          "A": ((214, 208, 222), (176, 168, 192), (132, 124, 152)),       # 石灰
          "V": ((216, 196, 255), (170, 140, 236), (120, 96, 196))})       # 望遠鏡紫
def A_(rows, **kw): return L.auto(rows, outline=OLP, ramps=R, **kw)
def flipx(a): return a[:, ::-1].copy()
def flipy(a): return a[::-1].copy()
def pad_to(frames):
    W = max(f.shape[1] for f in frames); H = max(f.shape[0] for f in frames); out = []
    for f in frames:
        o = canvas(W, H); paste(o, f, (W - f.shape[1]) // 2, H - f.shape[0]); out.append(o)
    return out

PROP_SERIES = {"A": ("can", "水壺"), "B": ("wand", "泡泡棒"), "C": ("match", "火柴"), "D": ("pebble", "石仔"),
               "E": ("chili", "辣椒"), "F": ("scope", "望遠鏡"), "G": ("book", "書"), "H": ("moonlamp", "月亮燈")}

def props():
    P = {}
    can = A_(["...KKK.......", "..K...K......", ".TTTTTTT....T", "TTTTTTTTT..T.", "TTTTTTTTTTT..", "TTTTTTTTT....", ".TTTTTTT....."])
    can_t = A_(["....KKK...", "...K...K..", "..TTTTTTT.", ".TTTTTTTTT", ".TTTTTTTTT", "TTTTTTTTT.", ".TTTTTTT..", "...TT.....", "..T.......", ".T........"])
    P["can"] = {"frames": pad_to([can, can_t]), "note": "水壺：0 企、1 倒水（嘴向左下）", "grip": "handle"}
    wand = A_([".PPP.", "P...P", "P...P", ".PPP.", "..K..", "..K..", "..K..", "..K.."])
    wand[2:4, 2:5][wand[2:4, 2:5, 3] == 0] = 0
    P["wand"] = {"frames": [wand], "note": "泡泡棒（粉紅圈＋木柄）"}
    m0 = A_(["N", "N", "C", "C", "C", "C", "C", "C"], fixed={"N": (226, 64, 64), "C": (242, 222, 180)})
    flame = L.auto(["..Y..", ".YOY.", ".YOY.", "..O.."], outline=None, fixed={"Y": (255, 236, 130), "O": (255, 150, 60)}, pad=0)
    m1 = canvas(m0.shape[1] + 4, m0.shape[0] + 4); paste(m1, m0, 2, 4); paste(m1, flame, 0, 0)
    P["match"] = {"frames": pad_to([m0, m1]), "note": "火柴：0 未點、1 着咗"}
    peb = A_(["..AAAA..", ".AAAAAA.", "AAAAAAAA", "AAAAAAAA", ".AAAAAA."])
    P["pebble"] = {"frames": [peb], "note": "石仔（放地上孵）"}
    chili = A_(["..M..", "..MM.", ".NN..", "NNN..", "NNN..", "NNN..", ".NN..", "..N.."], fixed={"M": (104, 170, 96)})
    P["chili"] = {"frames": [chili], "note": "辣椒（團絨當士多啤梨）"}
    scope = A_(["YY.......", "YVVVVVVYY", "YVVVVVVYY", "YY......."], fixed={"Y": (255, 214, 110)})
    P["scope"] = {"frames": [scope, flipx(scope)], "note": "望遠鏡：0 正（大頭向左）、1 倒轉（細頭向眼）"}
    bk = L.build_fx()["fx_book"]["frames"]
    b0 = canvas(bk[0].shape[1], bk[0].shape[0] + 3); paste(b0, bk[0], 0, 0)
    for j in range(3): b0[bk[0].shape[0] - 1 + j, bk[0].shape[1] // 2 + 2] = (226, 64, 64, 255)   # 書籤絲帶（正常向下）
    P["book"] = {"frames": pad_to([b0, flipy(b0), bk[2]]), "note": "書：0 打開、1 拎倒轉、2 合埋跌低（同 3a fx_book 一套）"}
    moon_off = A_(["..YYY.", ".YY...", "YY....", "YY....", "YY....", ".YY...", "..YYY.", "..KK..", ".KKKK."], fixed={"Y": (226, 206, 150)})
    moon_on = A_(["..YYY.", ".YY...", "YY....", "YY....", "YY....", ".YY...", "..YYY.", "..KK..", ".KKKK."])
    P["moonlamp"] = {"frames": [moon_off, moon_on], "note": "月亮燈：0 熄、1 着（glow 交引擎）"}
    for k, v in P.items():
        f = v["frames"][0]; v["pivot"] = [f.shape[1] // 2, f.shape[0] - 1]
    return P

def fx2():
    """新 FX（3a 冇嘅）"""
    F = {}
    drop = L.auto([".W.", "BWB", "BBB", ".B."], outline=None, fixed={"B": (110, 190, 250), "W": (200, 238, 255)}, pad=0)
    o = canvas(13, 12)
    for (x, y) in ((1, 0), (6, 3), (10, 1)): paste(o, drop, x, y)
    o2 = canvas(13, 12)
    for (x, y) in ((1, 5), (6, 8), (10, 6)): paste(o2, drop, x, y)
    o3 = canvas(13, 12)
    for (x, y) in ((3, 2), (8, 6)): paste(o3, drop, x, y)
    F["fx2_drops"] = {"frames": [o, o2, o3], "pivot": [6, 11], "note": "水滴落（3 幀 loop）"}
    sp = L.auto(["B...B", ".B.B.", "B...B"], outline=None, fixed={"B": (150, 210, 250)}, pad=0)
    sp2 = canvas(21, 7); paste(sp2, sp, 0, 2); paste(sp2, sp, 16, 2); sp2[0, 10] = (150, 210, 250, 255)
    F["fx2_splash"] = {"frames": [sp2], "pivot": [10, 6], "note": "甩水（身兩邊）"}
    bub = []
    for rr in (4, 7, 12):
        n = rr * 2 + 3; b = canvas(n, n); Y, X = np.mgrid[0:n, 0:n]; d = np.hypot(X - n // 2, Y - n // 2)
        ring = (d <= rr + .5) & (d > rr - .7); b[ring] = (170, 230, 255, 255)
        b[n // 2 - rr // 2, n // 2 - rr // 2] = (*WHITE, 255); b[n // 2 - rr // 2 + 1, n // 2 - rr // 2] = (*WHITE, 255)
        bub.append(b)
    pop = L.auto(["B...B", ".....", "..W..", ".....", "B...B"], outline=None, fixed={"B": (170, 230, 255), "W": WHITE}, pad=0)
    bub.append(pop)
    bub = [_center(f, 27) for f in bub]
    F["fx2_bubble"] = {"frames": bub, "pivot": [13, 13], "note": "泡泡：0 細、1 中、2 大（包住身）、3 爆"}
    fire = [L.auto(["......YY...", "...YYYOOY..", "YYYOOOOOOY.", "YOOOOOOOOOY", "YYYOOOOOOY.", "...YYYOOY..", "......YY..."], outline=None, fixed={"Y": (255, 236, 130), "O": (255, 140, 60)}, pad=0),
            L.auto(["....YY.....", "..YYOOYYY..", "YYOOOOOOOYY", "YOOOOOOOOOO", "YYOOOOOOOYY", "..YYOOYYY..", "....YY....."], outline=None, fixed={"Y": (255, 236, 130), "O": (255, 140, 60)}, pad=0)]
    F["fx2_fire"] = {"frames": pad_to(fire), "pivot": [0, 3], "note": "噴火（向右；左用 mirrorX）"}
    st = L.auto(["W.", ".W", "W.", ".W"], outline=None, fixed={"W": (236, 232, 244)}, pad=0)
    st2 = canvas(7, 6); paste(st2, st, 0, 1); paste(st2, st, 4, 0)
    F["fx2_steam"] = {"frames": [st2, np.roll(st2, -1, 0)], "pivot": [3, 5], "note": "頭頂冒煙（2 幀）"}
    tiny = L.auto(["..Y..", ".YWY.", "..Y.."], outline=None, fixed={"Y": (255, 222, 110), "W": WHITE}, pad=0)
    F["fx2_tiny"] = {"frames": [tiny], "pivot": [2, 2], "note": "望遠鏡入面嘅細細粒星"}
    return F

def _center(a, n):
    o = canvas(n, n); paste(o, a, (n - a.shape[1]) // 2, (n - a.shape[0]) // 2); return o
