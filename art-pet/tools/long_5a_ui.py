# 《微光小圃》5a UI（HD-2D）：家族等級 chip／升級彈窗／揀蛋（二揀一）／寵物卡「做主養」／房間切換／族譜（普通＋Lv10 金色）
# 純 Pillow/numpy，冇 AI。零件 3x；layout art 座標 195×422。
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import long_5abc_ui as U
import long_5abc_lib as LB
import long_5c_patterns as PT
from series2_lib import ART
H = U.H; P = U.P; C = U.C; hx = U.hx; mix = U.mix
O5 = os.path.join(LB.OUTL, "5a"); UO = os.path.join(O5, "ui"); PV = os.path.join(O5, "preview")
D5 = json.load(open(os.path.join(O5, "long_5a.json")))
LV = D5["familyLevel"]["thresholds"]
LS = json.load(open(os.path.join(ART, "sprites/series2/lessons/lessons.json")))
ROOMS = {"room1": "屋仔", "room2": "森林閣樓", "room3": "星夜書房", "room4": "海風小屋"}
UNL_ICON = {"room2": "house", "room3": "house", "room4": "house", "visitor_new": "visitor", "inherit_fast": "fast", "furniture_pack1": "furniture",
            "furniture_pack2": "furniture", "kid_series_E": "egg_kid", "job_cap_plus1": "job_lv", "family_title": "title", "tree_gold": "family_tree"}

L = {"style": "HD-2D（ui/style_ref/hd2d）；零件 3x（1 art 單位＝3px）", "assets": {},
 "houseHud": {
   "back": {"cx": 16, "cy": 18, "d": 22, "icon": "back(4b)"}, "title": {"cx": 97.5, "y": 8, "w": 70, "label": "房名（屋仔／森林閣樓／星夜書房／海風小屋）"},
   "familyChip": {"x": 136, "y": 9, "w": 54, "h": 17, "icon": "family_level", "bar": {"x": 152, "y": 20.5, "w": 34, "h": 4}, "tap": "開族譜"},
   "roomDots": {"cx": 97.5, "y": 30, "gap": 7, "d": 4, "note": "4 粒；而家間＝金、已開＝白、未開＝灰鎖"},
   "arrows": {"l": {"cx": 11, "cy": 214, "d": 18}, "r": {"cx": 184, "cy": 214, "d": 18}, "note": "左右撳／橫掃切房（300ms 橫向 parallax：far 0.6、mid 1.0、fore 1.3）；冇下一間＝唔顯示；下一間未開＝灰＋鎖，撳出 toast「家族 LvN 開」"},
   "capacity": {"x": 6, "y": 33, "w": 42, "h": 13, "icon": "pets", "fmt": "{n}/4 隻"},
   "tree": {"cx": 23, "cy": 392, "d": 30, "icon": "family_tree", "label": "族譜", "labelY": 411},
   "decorate": {"cx": 172, "cy": 392, "d": 30, "note": "沿用 4b 佈置掣"}},
 "petCard": {"panel": {"x": 20, "y": 112, "w": 155, "h": 168}, "portrait": {"cx": 97.5, "cy": 152, "d": 50}, "name": {"y": 186}, "tags": {"y": 199},
   "info": {"y": 214}, "btnMain": {"x": 32, "y": 232, "w": 131, "h": 18, "label": "做主養", "icon": "crown", "kind": "pri"},
   "btnGreet": {"x": 32, "y": 254, "w": 63, "h": 15, "label": "打招呼", "kind": "sec"}, "btnMove": {"x": 100, "y": 254, "w": 63, "h": 15, "label": "搬房", "kind": "violet"},
   "close": {"cx": 168, "cy": 117}, "isMain": "已經係主養：主養掣變 dis「主養緊」＋portrait 金冠",
   "note": "屋內撳成年寵物出；做主養＝佢做浮動寵物（只限團絨系；細佬系做主養會留喺屋，但花園主養位用佢）— 見 open question"},
 "levelUp": {"rays": {"cx": 97.5, "cy": 150, "r": 70}, "medal": {"cx": 97.5, "cy": 150, "d": 56}, "lv": {"y": 150}, "plaque": {"y": 98, "w": 92, "label": "家族升級！"},
   "unlockCard": {"x": 26, "y": 196, "w": 143, "h": 54}, "btn": {"x": 57, "y": 262, "w": 81, "h": 18, "label": "好嘢！"}, "anim": "medal scale 0.6→1.08→1（easeOutBack 420ms）；rays 慢轉 8s/圈；金粉 motes"},
 "eggChoice": {"panel": {"x": 14, "y": 104, "w": 167, "h": 196}, "plaque": {"y": 96, "w": 104, "label": "新蛋嚟咗！"}, "sub": {"y": 124, "text": "揀一隻嚟養（最多養 2 隻）"},
   "cards": {"x": [22, 101], "y": 134, "w": 72, "h": 128}, "egg": {"cy": 180}, "name": {"y": 222}, "desc": {"y": 234}, "pill": {"y": 244, "h": 13},
   "disabled": "細佬蛋：有細佬養緊 → 灰卡＋鎖＋「細佬養緊」", "note": "團絨蛋 egg sheet 第 1 格 32px ×2；細佬蛋 egg_48 ×2（crop）"},
 "tree": {"bg": "navy 漸變＋星塵；金色版（Lv10）＝金邊 ornate 框＋暖金底＋金連線發光", "topBar": {"back": {"cx": 16, "cy": 18}, "title": {"cx": 97.5, "y": 8, "w": 70, "label": "族譜"}},
   "levelCard": {"x": 8, "y": 32, "w": 179, "h": 40}, "rows": {"y0": 92, "dy": 74, "label": "第 N 代（金字，左上）"},
   "node": {"w": 84, "h": 56, "portrait": {"dx": 20, "dy": 26, "d": 34}, "name": {"dx": 40, "dy": 12}, "tag": {"dx": 40, "dy": 23}, "chips": {"dx": 40, "dy": 34, "note": "花紋色塊（上一代遺落）＋教錯咗乜道具（lesson prop pixel ×2）"},
            "raising": "養緊＝藍綠框＋「養緊」細 pill；主養＝金冠"},
   "link": "金線：上一代 node 底中 → 下一代 node 頂中（直角折）", "legend": {"y": 400}}}

def save(im, name):
    p = f"ui/{name}@3x.png"; U.x3(U.crop(im)).save(os.path.join(O5, p)); L["assets"][name] = p; return p

def lv_of(xp):
    lv = 1
    for i, t in enumerate(LV):
        if xp >= t: lv = i + 1
    return lv

def family_chip(b, lv, xp):
    c = L["houseHud"]["familyChip"]
    H.place(b, H.frame(c["w"], c["h"], c["h"] / 2, C['navy'], glow=.6, ornate=False, rim=1.0), P(c["x"]), P(c["y"]))
    U.icon(b, "family_level", P(c["x"] + 2), P(c["y"] + c["h"] / 2), 19)
    H.gold_text(b, (P(c["x"] + 32), P(c["y"] + 6)), f"Lv{lv}", 7.4, 'cin', glow=.4)
    lo, hi = LV[lv - 1], (LV[lv] if lv < 10 else LV[-1]); v = 1 if lv == 10 else (xp - lo) / (hi - lo)
    br = c["bar"]; U.bar(b, br["x"], br["y"], br["w"], br["h"], v)

def hud(b, room="room2", lv=4, xp=330, n=3, unlocked=("room1", "room2")):
    hh = L["houseHud"]
    U.medal(b, P(16), P(18), 22, C['navy'], "arrow_l", 14)
    H.plaque(b, 97.5, 8, 70, ROOMS[room])
    family_chip(b, lv, xp)
    rd = hh["roomDots"]; order = list(ROOMS)
    for i, rr in enumerate(order):
        x = rd["cx"] + (i - 1.5) * rd["gap"]; cur = rr == room
        if cur: U.glow_spot(b, P(x), P(rd["y"]), 3.5, a=.8)
        H.gem(b, P(x), P(rd["y"]), 1.9 if cur else 1.5, C['pri'] if cur else (C['paper'] if rr in unlocked else C['dis']), glow=False, star=False)
    cp = hh["capacity"]; H.place(b, H.frame(cp["w"], cp["h"], cp["h"] / 2, C['navy_in'], glow=.4, ornate=False, rim=.9), P(cp["x"]), P(cp["y"]))
    U.icon(b, "pets", P(cp["x"] + 5), P(cp["y"] + cp["h"] / 2), 13); H.text(b, (P(cp["x"] + 26), P(cp["y"] + cp["h"] / 2 - .2)), f"{n}/4 隻", 6.0, C['cream'], 'serif', stroke=.8)
    i = order.index(room)
    for side, j in (("l", i - 1), ("r", i + 1)):
        if 0 <= j < 4:
            a = hh["arrows"][side]; locked = order[j] not in unlocked
            U.medal(b, P(a["cx"]), P(a["cy"]), a["d"], C['dis'] if locked else C['navy'], "arrow_" + side, 13, glow=.3 if locked else .9, dim=locked)
            if locked: U.icon(b, "lock", P(a["cx"] + 5), P(a["cy"] + 5), 8)
    t = hh["tree"]; U.medal(b, P(t["cx"]), P(t["cy"]), 30, C['navy'], "family_tree", 24); H.text(b, (P(t["cx"]), P(t["labelY"])), "族譜", 6.4, C['cream'], 'serif', stroke=.9)
    U.medal(b, P(172), P(392), 30, C['navy'], "decorate", 24); H.text(b, (P(172), P(411)), "佈置", 6.4, C['cream'], 'serif', stroke=.9)

SET_A = {"bed": "bed_leaf", "table": "table_stump", "wall": "wall_shelf", "rug": "rug_leaf", "window": "win_curtain", "lamp": "lamp_mushroom"}
SET_B = {kk: v for kk, v in json.load(open(os.path.join(ART, "sprites/series2_house/house.json")))["sets"]["B"]["items"].items()}
def pets_in(room_pets, fi=0):
    out = []
    for (k, clip, x, y, fl) in room_pets:
        f, piv, g = U.strip_frame(k, clip, fi, fl); out.append((f, piv, x, y, y))
    return out
DEMO_PETS = {"room2": [("A3", "sit", 70, 300, False), ("evo_still_moon", "sit", 128, 300, True), ("F3", "interact", 98, 330, False)],
             "room3": [("evo_still_radiant", "sit", 92, 300, False), ("H3", "sit", 132, 318, True)],
             "room4": [("C3", "sit", 80, 306, False), ("evo_still_tide", "sit", 126, 306, True), ("G3", "sit", 60, 336, False), ("evo_still_soft", "sit", 146, 336, True)]}
def mock_room(room, var="day", lv=4, xp=330, unlocked=("room1", "room2"), items=None, fi=3):
    pets = DEMO_PETS.get(room, [])
    bg = U.room_ss(room, var, items if items is not None else SET_A, pets_in(pets, fi))
    ui = U.board(); hud(ui, room, lv, xp, len(pets), unlocked); bg.alpha_composite(ui); return bg

def pet_card(b, k="evo_still_moon", name="月月", tag="團絨・月光", room="森林閣樓", is_main=False):
    c = L["petCard"]; pn = c["panel"]
    U.panel(b, pn["x"], pn["y"], pn["w"], pn["h"], 10)
    U.portrait(b, k, P(c["portrait"]["cx"]), P(c["portrait"]["cy"]), c["portrait"]["d"])
    if is_main: U.icon(b, "crown", P(c["portrait"]["cx"]), P(c["portrait"]["cy"] - 27), 15)
    H.gold_text(b, (P(97.5), P(c["name"]["y"])), name, 9.0, 'serif', glow=.4)
    U.pill(b, 97.5 - 30, c["tags"]["y"] - 5.5, 60, 11, 'violet', tag, size=5.6)
    H.text(b, (P(97.5), P(c["info"]["y"])), f"成年・住喺{room}・第 2 代", 5.8, hx('#C9D0F0'), 'sans', stroke=.6)
    bm = c["btnMain"]
    if is_main: U.pill(b, bm["x"], bm["y"], bm["w"], bm["h"], 'dis', "主養緊", "crown", 7.0)
    else: U.pill(b, bm["x"], bm["y"], bm["w"], bm["h"], 'pri', "做主養", "crown", 7.0)
    for kk in ("btnGreet", "btnMove"):
        q = c[kk]; U.pill(b, q["x"], q["y"], q["w"], q["h"], q["kind"], q["label"], size=6.0)
    H.close_btn(b, P(c["close"]["cx"]), P(c["close"]["cy"]))
def mock_pet_card(is_main=False):
    bg = U.dim(mock_room("room2"), .5); ui = U.board(); pet_card(ui, is_main=is_main); bg.alpha_composite(ui); return bg

def unlock_row(b, x, y, w, ids, title):
    U.panel(b, x, y, w, 54, 8, C['navy_in'], glow=.6, ornate=False)
    H.text(b, (P(x + w / 2), P(y + 9)), title, 6.0, hx('#C9D0F0'), 'sans', stroke=.6)
    n = len(ids)
    for i, u in enumerate(ids):
        cx = x + w / 2 + (i - (n - 1) / 2) * 64
        U.medal(b, P(cx - 20), P(y + 31), 24, C['pri'], UNL_ICON[u], 19)
        zh = next(z["zh"] for z in D5["familyLevel"]["unlocks"][str(LVX)] if z["id"] == u) if False else UNLOCK_ZH[u]
        parts = zh.split("（"); H.text(b, (P(cx + 4), P(y + 28)), parts[0], 6.4 if n == 1 else 5.6, C['cream'], 'serif', anchor='lm', stroke=.8)
        if len(parts) > 1: H.text(b, (P(cx + 4), P(y + 37)), parts[1].rstrip("）"), 5.4, hx('#AEE6F0'), 'sans', anchor='lm', stroke=.6)
UNLOCK_ZH = {u["id"]: u["zh"] for v in D5["familyLevel"]["unlocks"].values() for u in v}

def rays(b, cx, cy, r, n=14, a=.6, colr=None):
    W, Hh = b.size; g = Image.new('L', (W, Hh), 0); d = ImageDraw.Draw(g)
    import math
    for i in range(n):
        t0 = i * 2 * math.pi / n; t1 = t0 + math.pi / n * .55
        d.polygon([(P(cx), P(cy)), (P(cx + r * math.cos(t0)), P(cy + r * math.sin(t0))), (P(cx + r * math.cos(t1)), P(cy + r * math.sin(t1)))], fill=150)
    m = U.gauss(g, P(2)); rad = Image.new('L', (W, Hh), 0); ImageDraw.Draw(rad).ellipse([P(cx - r), P(cy - r), P(cx + r), P(cy + r)], fill=255)
    U.put(b, U.solid((W, Hh), colr or C['glow']), U.amul(Image.fromarray((np.asarray(m).astype(float) * np.asarray(U.gauss(rad, P(r * .3))) / 255).astype(np.uint8)), a))

def mock_levelup(lv=5):
    bg = U.dim(mock_room("room2"), .62); b = U.board(); c = L["levelUp"]
    rays(b, 97.5, 150, 78); U.glow_spot(b, P(97.5), P(150), 30, a=.9)
    U.medal(b, P(97.5), P(150), 56, C['violet'], "family_level", 46, glow=1.6)
    H.plaque(b, 97.5, 92, 96, "家族升級！")
    H.gold_text(b, (P(97.5), P(186)), f"Lv {lv}", 15, 'cin', glow=.9)
    unlock_row(b, 22, 198, 151, [u["id"] for u in D5["familyLevel"]["unlocks"][str(lv)]], "解鎖咗")
    H.button(b, 57, 262, 81, 18, 'pri', '好嘢！')
    for i, (x, y) in enumerate([(40, 120), (150, 112), (30, 176), (164, 182), (60, 98), (136, 210)]):
        U.icon(b, "xp", P(x), P(y), 7 + (i % 3) * 2)
    bg.alpha_composite(b); return bg

def egg_img(kind, frame=0):
    if kind == "tr":
        a = np.asarray(Image.open(os.path.join(ART, "sprites/tuanrong/pet_tuanrong_egg_sheet.png")).convert("RGBA"))[:, frame * 32:(frame + 1) * 32]
    else:
        a = np.asarray(Image.open(os.path.join(ART, "sprites/series2/egg/egg_48.png")).convert("RGBA"))
    ys, xs = np.nonzero(a[..., 3]); return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
def egg_card(b, x, y, kind, disabled=False, sel=False):
    c = L["eggChoice"]["cards"]; w, h = c["w"], c["h"]
    fill = (hx('#3A3F62', 235), hx('#23263E', 240)) if disabled else C['navy_in']
    H.place(b, H.frame(w, h, 7, fill, glow=1.3 if sel else (.15 if disabled else .6), ornate=False, rim=1.0), P(x), P(y))
    U.glow_spot(b, P(x + w / 2), P(y + 44), 22, C['cyan'] if not disabled else hx('#6A7090'), .6 if not disabled else .3)
    U.paste_px(b, egg_img(kind), P(x + w / 2), P(y + 66), 2.0 if kind == "tr" else 1.6667, anchor='b', dark=disabled)
    if disabled: U.icon(b, "lock", P(x + w / 2), P(y + 48), 16)
    nm = "團絨蛋" if kind == "tr" else "細佬蛋"
    H.gold_text(b, (P(x + w / 2), P(y + 82)), nm, 8.4, 'serif', glow=.3, fill=None if not disabled else [(0, hx('#C9CEE6')), (1, hx('#7D84A0'))])
    ds = ("孵出團絨（主養）", "會浮出嚟陪你") if kind == "tr" else ("孵出細佬", "可以學嘢、遺傳")
    for i, s in enumerate(ds): H.text(b, (P(x + w / 2), P(y + 93 + i * 8)), s, 5.4, hx('#C9D0F0') if not disabled else hx('#9AA0B8'), 'sans', stroke=.6)
    if disabled: U.pill(b, x + 6, y + h - 19, w - 12, 13, 'dis', "細佬養緊", size=6.0)
    else: U.pill(b, x + 6, y + h - 19, w - 12, 13, 'pri', "揀呢隻", size=6.4)
def mock_egg(kid_disabled=False):
    bg = U.dim(mock_room("room1" if False else "room2"), .6); b = U.board(); e = L["eggChoice"]; pn = e["panel"]
    U.panel(b, pn["x"], pn["y"], pn["w"], pn["h"], 11, ornate=True)
    H.plaque(b, 97.5, 94, 104, "新蛋嚟咗！")
    H.text(b, (P(97.5), P(124)), "揀一隻嚟養（最多同時養 2 隻）", 6.0, hx('#C9D0F0'), 'sans', stroke=.6)
    egg_card(b, 22, 134, "tr", sel=not kid_disabled); egg_card(b, 101, 134, "kid", disabled=kid_disabled, sel=False)
    H.text(b, (P(97.5), P(281)), "揀咗之後會問邊隻做「上一代」", 5.6, hx('#FFE6A8'), 'sans', stroke=.6)
    bg.alpha_composite(b); return bg

# ───────── 族譜 ─────────
TREE = [  # (id, form, name, gen, parent, raising)
 ("g1", "evo_still_lumi", "光光", 1, None, False),
 ("g2a", "A3", "滴滴", 2, "g1", False), ("g2b", "evo_still_tide", "潮潮", 2, "g1", False),
 ("g3a", "F3", "星仔", 3, "g2a", False), ("g3b", "B3", "泡泡", 3, "g2b", False),
 ("g4", "S2", "BB", 4, "g3a", True)]
MAIN = "g2b"
def tag_of(k):
    s = PT.series_of(k)
    if k in LB.KID34: return f"細佬 {s} 系" if s and len(s) == 1 else "細佬"
    zh = {"tide": "潮汐", "moon": "月光", "shroom": "菇菇", "crystal": "水晶", "ember": "餘燼", "radiant": "光芒", "soft": "軟綿", "dust": "星塵", "lumi": "微光"}
    return f"團絨・{zh.get(s, s)}"
def lesson_prop(k):
    """教錯咗乜：細佬系＝佢系列嗰課（佢學咗嘅）；團絨＝冇（佢係老師）→ None"""
    s = PT.series_of(k)
    if k in LB.KID34 and s and len(s) == 1:
        p = LS["propsBySeries"][s]; a = np.asarray(Image.open(os.path.join(ART, "sprites/series2", p["png"])).convert("RGBA"))[:, :p["frameW"]]
        ys, xs = np.nonzero(a[..., 3]); return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1], p["zh"], LS["copy"][s]["title"].replace("照抄：", "")
    return None
def swatch(b, cx, cy, pat, hi, lo, d=11):
    """花紋色塊：圓章內鋪該花紋（hi/lo 染色）"""
    n = 12; m = PT.motif(pat, n, n, 0, 0, n - 1, n - 1)
    a = np.zeros((n, n, 4), np.uint8); a[..., :3] = mix(U.hx(lo), U.hx("#1A1230"), .55)[:3]; a[..., 3] = 255
    a[m == 255, :3] = PT.LB_hex(hi); a[m == 128, :3] = PT.LB_hex(lo)
    im = Image.fromarray(a).resize((P(d), P(d)), Image.NEAREST); mk = Image.new('L', im.size, 0); ImageDraw.Draw(mk).ellipse([0, 0, im.width - 1, im.height - 1], fill=255)
    dd = ImageDraw.Draw(b); dd.ellipse([cx - P(d / 2 + .9), cy - P(d / 2 + .9), cx + P(d / 2 + .9), cy + P(d / 2 + .9)], fill=C['g_mid'], outline=C['line'], width=P(.5))
    b.paste(im, (int(cx - P(d / 2)), int(cy - P(d / 2))), mk)
def node(b, x, y, nd, byid, gold=False):
    nid, k, nm, gen, par, raising = nd; w, h = 84, 56
    fill = C['navy_in'] if not gold else (hx('#6A4A2E', 235), hx('#3E2A1C', 240))
    H.place(b, H.frame(w, h, 7, fill, glow=1.2 if raising or gold else .5, ornate=False, rim=1.0), P(x), P(y))
    if raising: ImageDraw.Draw(b).rounded_rectangle([P(x - 1.4), P(y - 1.4), P(x + w + 1.4), P(y + h + 1.4)], radius=P(8), outline=C['sec'][0], width=P(.9))
    U.portrait(b, k, P(x + 20), P(y + 26), 34, fill=C['navy'] if not gold else (hx('#8A6238'), hx('#4E3420')))
    if nid == MAIN: U.icon(b, "crown", P(x + 20), P(y + 7), 12)
    H.gold_text(b, (P(x + 41), P(y + 11)), nm, 7.6, 'serif', anchor='lm', glow=.3)
    H.text(b, (P(x + 41), P(y + 21.5)), tag_of(k), 5.0, hx('#C9D0F0') if not gold else hx('#FFE9C0'), 'sans', anchor='lm', stroke=.6)
    if par:
        pk = byid[par][1]; pat = PT.pattern_for_parent(pk); hi, lo, _ = PT.tint_for_parent(pk)
        swatch(b, P(x + 47), P(y + 34), pat, hi, lo)
        lp = lesson_prop(k)
        if lp is not None:
            dd = ImageDraw.Draw(b); dd.ellipse([P(x + 55.5), P(y + 28.5), P(x + 66.5), P(y + 39.5)], fill=C['paper'][1], outline=C['line'], width=P(.5))
            arr = lp[0]; s = 1.0 if max(arr.shape[:2]) <= 9 else .6667
            U.paste_px(b, arr, P(x + 61), P(y + 34), s)
        if lp: t = "錯：" + lp[2].split("→")[-1].strip().split("，")[0][:6]
        elif k in LB.KID34: t = "未學嘢（養緊）" if raising else "冇學過"
        else: t = "團絨＝老師"
        H.text(b, (P(x + 41), P(y + 46)), t, 4.8, hx('#FFE6A8'), 'sans', anchor='lm', stroke=.5)
    else:
        H.text(b, (P(x + 41), P(y + 34)), "初代", 6.0, hx('#FFE6A8'), 'serif', anchor='lm', stroke=.6)
    if raising: U.pill(b, x + 52, y - 5, 30, 10, 'sec', "養緊", size=5.4)

def tree_bg(gold=False):
    W, Hh = P(195), P(422)
    stops = [(0, hx('#2A2F5E')), (1, hx('#10132E'))] if not gold else [(0, hx('#5A3E22')), (.5, hx('#3A2614')), (1, hx('#22160C'))]
    bg = H.vgrad((W, Hh), stops).convert('RGBA'); rng = np.random.default_rng(7 if not gold else 9); d = ImageDraw.Draw(bg)
    for _ in range(90):
        x, y = rng.uniform(0, 195), rng.uniform(0, 422); r_ = rng.choice([.4, .6, .9])
        c = (255, 240, 200, int(rng.uniform(80, 200))) if gold else (200, 220, 255, int(rng.uniform(60, 180)))
        d.ellipse([P(x - r_), P(y - r_), P(x + r_), P(y + r_)], fill=c)
    return bg
def mock_tree(gold=False, lv=4, xp=330):
    bg = tree_bg(gold); b = U.board()
    if gold:
        H.place(b, H.frame(187, 414, 12, (hx('#7A5430', 90), hx('#3A2614', 90)), glow=1.6, ornate=True, rim=1.4), P(4), P(4))
    U.medal(b, P(16), P(18), 22, C['navy'], "arrow_l", 14)
    H.plaque(b, 97.5, 8, 70, "族譜", fill=C['pri'] if gold else None)
    lc = L["tree"]["levelCard"]
    U.panel(b, lc["x"], lc["y"], lc["w"], lc["h"], 8, C['navy_in'] if not gold else (hx('#6A4A2E', 235), hx('#3E2A1C', 240)), glow=.7, ornate=False)
    U.medal(b, P(lc["x"] + 17), P(lc["y"] + 20), 30, C['violet'] if not gold else C['pri'], "family_level" if not gold else "title", 24)
    if gold:
        H.gold_text(b, (P(lc["x"] + 36), P(lc["y"] + 12)), "微光之家", 9.0, 'serif', anchor='lm', glow=.7)
        H.text(b, (P(lc["x"] + 36), P(lc["y"] + 22)), "家族 Lv10・家族稱號已解鎖", 5.6, hx('#FFE9C0'), 'sans', anchor='lm', stroke=.6)
        U.bar(b, lc["x"] + 36, lc["y"] + 28, 134, 6, 1.0, label="MAX")
    else:
        H.gold_text(b, (P(lc["x"] + 36), P(lc["y"] + 11)), f"家族 Lv{lv}", 8.6, 'serif', anchor='lm', glow=.4)
        nxt = D5["familyLevel"]["unlocks"].get(str(lv + 1), [])
        H.text(b, (P(lc["x"] + 171), P(lc["y"] + 11)), f"下一級：{nxt[0]['zh'].split('（')[0]}" if nxt else "", 5.4, hx('#AEE6F0'), 'sans', anchor='rm', stroke=.6)
        lo, hi = LV[lv - 1], LV[lv]; U.bar(b, lc["x"] + 36, lc["y"] + 21, 134, 7, (xp - lo) / (hi - lo), label=f"{xp - lo}/{hi - lo}")
        H.text(b, (P(lc["x"] + 36), P(lc["y"] + 34)), "養大一隻 +50・新圖鑑 +10・新家具 +5・遠足 +3", 4.6, hx('#9AA4D0'), 'sans', anchor='lm', stroke=0)
    byid = {n[0]: n for n in TREE}; pos = {}
    cols = {1: [55.5], 2: [8, 103], 3: [8, 103], 4: [55.5]}
    seen = {}
    for nd in TREE:
        g = nd[3]; i = seen.get(g, 0); seen[g] = i + 1
        x = cols[g][i] if len(cols[g]) > i else 8 + i * 95; y = 92 + (g - 1) * 74; pos[nd[0]] = (x, y)
    for nd in TREE:      # 連線（先畫）
        if nd[4]:
            px, py = pos[nd[4]]; cx_, cy_ = pos[nd[0]]; a = (px + 42, py + 56); bb = (cx_ + 42, cy_); my = (a[1] + bb[1]) / 2
            if gold:
                W, Hh = b.size; g = Image.new('L', (W, Hh), 0); ImageDraw.Draw(g).line([(P(a[0]), P(a[1])), (P(a[0]), P(my)), (P(bb[0]), P(my)), (P(bb[0]), P(bb[1]))], fill=220, width=P(4))
                U.put(b, U.solid((W, Hh), C['glow']), U.gauss(g, P(2)))
            U.gold_line(b, [a, (a[0], my), (bb[0], my), bb], 1.6 if gold else 1.2)
            H.gem(b, P(a[0]), P(my), 1.6, C['gem'] if not gold else C['pri'], glow=False, star=False)
    for g in range(1, 5):
        y = 92 + (g - 1) * 74
        H.gold_text(b, (P(10), P(y - 6)), f"第 {g} 代", 6.0, 'serif', anchor='lm', glow=.2)
    for nd in TREE: node(b, *pos[nd[0]], nd, byid, gold)
    lg = 402
    swatch(b, P(18), P(lg), "star", "#fff0a8", "#c08a3a", 9); H.text(b, (P(25), P(lg)), "遺傳花紋", 5.4, C['cream'], 'sans', anchor='lm', stroke=.5)
    dd = ImageDraw.Draw(b); dd.ellipse([P(64), P(lg - 4.5), P(73), P(lg + 4.5)], fill=C['paper'][1], outline=C['line'], width=P(.5))
    H.text(b, (P(76), P(lg)), "教錯咗乜", 5.4, C['cream'], 'sans', anchor='lm', stroke=.5)
    U.icon(b, "crown", P(116), P(lg), 9); H.text(b, (P(122), P(lg)), "主養", 5.4, C['cream'], 'sans', anchor='lm', stroke=.5)
    U.pill(b, 145, lg - 5, 26, 10, 'sec', "養緊", size=5.2)
    bg.alpha_composite(b); return bg

def components():
    b = U.board(70, 30); family_chip(b, 4, 330); save(b, "chip_family_level")
    b = U.board(70, 30); family_chip(b, 10, 1620); save(b, "chip_family_level_max")
    for side in "lr":
        for st in ("idle", "locked"):
            b = U.board(30, 30); lk = st == "locked"
            U.medal(b, P(15), P(15), 18, C['dis'] if lk else C['navy'], "arrow_" + side, 13, glow=.3 if lk else .9, dim=lk)
            if lk: U.icon(b, "lock", P(20), P(20), 8)
            save(b, f"btn_room_{side}_{st}")
    b = U.board(60, 20); H.place(b, H.frame(42, 13, 6.5, C['navy_in'], glow=.4, ornate=False, rim=.9), P(4), P(4)); U.icon(b, "pets", P(9), P(10.5), 13); save(b, "chip_capacity_bg")
    b = U.board(44, 44); U.medal(b, P(22), P(18), 30, C['navy'], "family_tree", 24); H.text(b, (P(22), P(37)), "族譜", 6.4, C['cream'], 'serif', stroke=.9); save(b, "btn_tree")
    for st in ("cur", "open", "locked"):
        b = U.board(10, 10); H.gem(b, P(5), P(5), 1.9 if st == "cur" else 1.5, {"cur": C['pri'], "open": C['paper'], "locked": C['dis']}[st], glow=False, star=False); save(b, f"dot_room_{st}")
    b = U.board(200, 200); pet_card(b); save(b, "pet_card_example")
    for kk in ("crown", "egg_tr", "egg_kid", "pets", "xp", "visitor", "title", "fast", "family_level", "family_tree"):
        b = U.board(30, 30); U.medal(b, P(15), P(15), 24, C['navy'], kk, 19); save(b, f"icon_{kk}")
    b = U.board(100, 150); egg_card(b, 4, 4, "tr", sel=True); save(b, "egg_choice_tr")
    b = U.board(100, 150); egg_card(b, 4, 4, "kid"); save(b, "egg_choice_kid")
    b = U.board(100, 150); egg_card(b, 4, 4, "kid", disabled=True); save(b, "egg_choice_kid_disabled")
    byid = {n[0]: n for n in TREE}
    for gold in (False, True):
        for nd in (TREE[1], TREE[5]):
            b = U.board(96, 70); node(b, 6, 8, nd, byid, gold); save(b, f"tree_node_{nd[0]}{'_gold' if gold else ''}")
    for pat, _ in PT.PATTERNS:
        b = U.board(16, 16); swatch(b, P(8), P(8), pat, "#ffe6a8", "#c0803a"); save(b, f"swatch_{pat}")
    b = U.board(140, 22); U.bar(b, 3, 3, 134, 7, .55, label="165/270"); save(b, "bar_xp")

def main():
    os.makedirs(UO, exist_ok=True); os.makedirs(PV, exist_ok=True)
    components()
    ims = {"house_room2_hud_day": mock_room("room2", "day"), "house_room3_hud_night": mock_room("room3", "night", 5, 470, ("room1", "room2", "room3"), SET_B),
           "house_room4_hud_day": mock_room("room4", "day", 8, 1120, tuple(ROOMS), SET_B),
           "pet_card_make_main": mock_pet_card(False), "pet_card_is_main": mock_pet_card(True), "levelup_lv5": mock_levelup(5), "levelup_lv10": mock_levelup(10),
           "egg_choice": mock_egg(False), "egg_choice_kid_disabled": mock_egg(True), "family_tree": mock_tree(False), "family_tree_gold_lv10": mock_tree(True)}
    out = {}
    for n, im in ims.items():
        p = os.path.join(PV, n + "_HD2D_3x.png"); U.x3(im).convert('RGB').save(p); out[n] = U.x3(im)
    U.strip_sheet([out[n] for n in ("house_room2_hud_day", "pet_card_make_main", "levelup_lv5", "egg_choice", "egg_choice_kid_disabled")],
                  ["屋內 HUD（家族 Lv＋切房）", "寵物卡・做主養", "家族升級 Lv5", "揀蛋（二揀一）", "揀蛋・細佬養緊"], os.path.join(PV, "ui_5a_sheet_HD2D_3x.png"))
    U.strip_sheet([out["family_tree"], out["family_tree_gold_lv10"]], ["族譜（Lv4）", "族譜・金色（Lv10）"], os.path.join(PV, "family_tree_sheet_HD2D_3x.png"))
    U.parts_sheet(list(L["assets"].values()), os.path.join(PV, "ui_parts_5a_HD2D_3x.png"), O5)
    LB.jdump(L, os.path.join(UO, "layout.json")); print("ui 5a ok", len(L["assets"]))

if __name__ == "__main__": main()
