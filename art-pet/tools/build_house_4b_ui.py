# 《微光小圃》4b 屋仔 UI — HD-2D 風格（Kurt 揀咗 HD-2D；B2 版冇整）。純 Pillow/numpy，無 AI。
# 出：屋仔 icon（花園入口＋上鎖）、6 個擺位 icon、佈置 UI 零件、整頁 mock（3x）＋ ui/layout.json（亦寫入 house.json "ui"）
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageChops
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ui_hd2d_kit as H
import house_4b_room as R
from series2_lib import ART
k = H.k; P = H.P; hx = H.hx; C = H.C; put, solid, gauss, amul = H.put, H.solid, H.gauss, H.amul
OUT = os.path.join(ART, "sprites/series2_house"); UO = os.path.join(OUT, "ui"); PV = os.path.join(OUT, "preview")
J = json.load(open(os.path.join(OUT, "house.json")))
E = lambda b: (lambda d, q: d.ellipse([q(b[0]), q(b[1]), q(b[2]), q(b[3])], fill=255))
POLY = lambda pts: (lambda d, q: d.polygon([(q(x), q(y)) for x, y in pts], fill=255))
RR = lambda b, r: (lambda d, q: d.rounded_rectangle([q(b[0]), q(b[1]), q(b[2]), q(b[3])], radius=q(r) - q(0), fill=255))
def rot_poly(cx, cy, w, h, ang):
    a = math.radians(ang)
    return POLY([(cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)) for x, y in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))])
BLUE = (hx('#C8EEFF'), hx('#7FC6F6')); PINK = (hx('#FFC4D8'), hx('#FF92B6')); WOOD = (hx('#F4CDA6'), hx('#D9A070'))
YEL = (hx('#FFF2A6'), hx('#FFCF4A')); RED = (hx('#FFAFA0'), hx('#F0606A')); GRN = (hx('#C9F5AE'), hx('#7FD36E'))
CREAM = (hx('#FFFBEF'), hx('#F3E2C4')); WHITE2 = (hx('#FFFFFF'), hx('#EDE6F4')); GREY = (hx('#F0ECF6'), hx('#C9C0D8'))

def draw_icon(kind):
    ic = k.Icon(H.HD_TH)
    if kind == "house":          # 屋仔（有面）
        ic.part(RR((9.5, 3, 12.5, 9), .8), RED, gloss=False)
        ic.part(RR((3.5, 10, 20.5, 22), 2), CREAM)
        ic.part(POLY([(1, 12), (12, 1.8), (23, 12)]), RED, round_=0.9)
        ic.part(RR((14, 14.5, 18.5, 22), 1.6), WOOD, gloss=False)
        ic.face(8.6, 15.6, 0.72)
    elif kind == "bed":
        ic.part(RR((1.5, 5.5, 7, 21.5), 2), WOOD, gloss=False)
        ic.part(RR((3, 12, 22.5, 19.5), 2), WHITE2, gloss=False)
        ic.part(RR((9.5, 11, 22.5, 20), 2.2), PINK)
        ic.part(E((3.5, 8.8, 10.5, 13.6)), WHITE2, gloss=False)
        ic.part(RR((19.5, 19, 21.5, 22.5), .6), WOOD, gloss=False)
        ic.face(15.8, 14.6, 0.6, 'sleep')
    elif kind == "table":
        ic.part(RR((10.5, 11, 13.5, 21), 1), WOOD, gloss=False)
        ic.part(E((6.5, 19, 17.5, 22.5)), WOOD, gloss=False)
        ic.part(E((1.5, 7, 22.5, 14)), PINK)
        ic.part(RR((9, 2.5, 15, 8.5), 1.5), WHITE2, gloss=False)
        ic.part(E((14.2, 3.6, 17.2, 6.8)), WHITE2, gloss=False)
    elif kind == "wall":         # 掛牆相框
        ic.part(POLY([(12, 0.8), (6, 5.5), (18, 5.5)]), YEL, gloss=False)
        ic.part(RR((2.5, 5, 21.5, 21.5), 2), WOOD)
        ic.part(RR((5.5, 8, 18.5, 18.5), 1), BLUE, gloss=False)
        ic.part(E((4.5, 13.5, 19.5, 23)), GRN, gloss=False, outline=False, m=None) if False else None
        ic.part(E((9, 9.5, 15, 15.5)), WHITE2, gloss=False)
        ic.face(12, 12.4, 0.45)
    elif kind == "rug":
        ic.part(E((1, 8, 23, 21)), PINK)
        ic.part(E((5.5, 11, 18.5, 18)), (hx('#FFE3EC'), hx('#FFC0D4')), gloss=False)
        for x in (8.5, 12, 15.5):
            ic.part(E((x - 1, 13.6, x + 1, 15.6)), WHITE2, gloss=False, outline=False)
    elif kind == "window":
        ic.part(RR((2.5, 2.5, 21.5, 21.5), 4), WOOD, gloss=False)
        ic.part(RR((5, 5, 19, 19), 2.5), BLUE)
        ic.part(RR((11.2, 5, 12.8, 19), .3), WOOD, gloss=False, outline=False)
        ic.part(RR((5, 11.2, 19, 12.8), .3), WOOD, gloss=False, outline=False)
        ic.part(POLY([(2, 2), (8, 2), (5, 14), (2, 16)]), PINK, gloss=False, round_=0.4)
        ic.part(POLY([(22, 2), (16, 2), (19, 14), (22, 16)]), PINK, gloss=False, round_=0.4)
    elif kind == "lamp":
        ic.part(E((6.5, 19.5, 17.5, 23)), WOOD, gloss=False)
        ic.part(RR((10.3, 9, 13.7, 21), 1.2), CREAM, gloss=False)
        ic.part(lambda d, q: d.pieslice([q(2), q(1.5), q(22), q(19)], 180, 360, fill=255), RED)
        for b in ((6, 5, 9, 8), (13, 3.5, 16.5, 7), (17, 7.5, 19.5, 10)):
            ic.part(E(b), WHITE2, gloss=False, outline=False)
    elif kind == "decorate":     # 掃（佈置）
        ic.part(rot_poly(10.5, 10.5, 3.2, 17, -40), WOOD, gloss=False)
        ic.part(rot_poly(17.2, 17.2, 7.4, 6.2, -40), PINK)
        ic.part(POLY(k.star_pts(5.5, 18, 4.2, 1.9)), YEL, gloss=False, round_=0.3)
        ic.part(POLY(k.star_pts(19.5, 5, 3, 1.4)), YEL, gloss=False, round_=0.3)
    elif kind == "back":
        ic.part(POLY([(3, 12), (12, 3.5), (12, 8.5), (21, 8.5), (21, 15.5), (12, 15.5), (12, 20.5)]), CREAM, round_=0.6)
    elif kind == "clear":        # 收起
        ic.part(rot_poly(12, 12, 4.4, 20, 45), GREY, gloss=False)
        ic.part(rot_poly(12, 12, 4.4, 20, -45), GREY, gloss=False)
    elif kind == "plus":
        ic.part(RR((9.8, 3, 14.2, 21), 1.8), CREAM, gloss=False)
        ic.part(RR((3, 9.8, 21, 14.2), 1.8), CREAM, gloss=False)
    elif kind == "lock":
        ic.part(lambda d, q: d.arc([q(6.5), q(2), q(17.5), q(15)], 180, 360, fill=255, width=q(2.6) - q(0)), GREY, gloss=False)
        ic.part(RR((5.5, 2 + 6.5, 6.5 + 2.6, 13), .6), GREY, gloss=False, outline=False)
        ic.part(RR((14.9, 8.5, 17.5, 13), .6), GREY, gloss=False, outline=False)
        ic.part(RR((3.5, 10.5, 20.5, 22), 2.5), YEL)
        ic.part(E((10.3, 13.5, 13.7, 16.9)), (hx('#6A4A30'), hx('#4A3020')), gloss=False, outline=False)
    return ic.finish()

_IC = {}
def hd_icon(kind):
    """同 ui_hd2d_kit.icon_raw：金邊＋暖光暈＋左上 rim light"""
    if kind not in _IC:
        base = draw_icon(kind); a = base.getchannel('A').point(lambda v: 255 if v > 90 else int(v * 2.8)); W, Hh = base.size
        ring = k.dilate(a, P(0.75)); outer = k.dilate(ring, P(0.55)); out = Image.new('RGBA', (W, Hh), (0, 0, 0, 0))
        put(out, solid((W, Hh), C['glow']), amul(gauss(outer, P(1.6)), 0.6)); put(out, solid((W, Hh), C['line']), outer)
        put(out, H.gold_grad((W, Hh)), ring); out.alpha_composite(base)
        rim = ImageChops.subtract(a, ImageChops.offset(a, P(0.7), P(0.7))); put(out, solid((W, Hh), hx('#FFFFFF', 140)), rim)
        _IC[kind] = out
    return _IC[kind]
def icon(board, kind, cx, cy, size_art, dim=False):
    im = hd_icon(kind); px = P(size_art * (k.ICN + 6) / k.ICN); im = im.resize((px, px), Image.LANCZOS)
    if dim:
        a = im.getchannel('A'); g = im.convert('L').point(lambda v: int(v * .55 + 40)); im = Image.merge('RGBA', (g, g, g.point(lambda v: min(255, v + 18)), a))
    board.alpha_composite(im, (int(cx - px / 2), int(cy - px / 2)))
def medal(board, cx, cy, d, fill, kind=None, isz=None, glow=1.0, dim=False):
    H.place(board, H.frame(d, d, d / 2, fill, glow=glow, ornate=False, rim=1.1), cx - P(d / 2), cy - P(d / 2))
    if kind: icon(board, kind, cx, cy, isz or d * 0.78, dim)

# ── 共用 layout（art 座標 195×422；中心點除非註明）──
SLOT_ICON = {s: s for s in J["slotOrder"]}
TAB_X = [4 + 187 / 6 * (i + .5) for i in range(6)]
L = {
 "style": "HD-2D（ui/style_ref/hd2d；Kurt 已揀）。零件 3x（1 art 單位＝3px）；B2 版冇整",
 "gardenEntry": {"btn": {"cx": 178, "cy": 104, "d": 24, "icon": "house", "label": "屋仔", "labelY": 120.5, "png": "ui/btn_house@3x.png", "lockedPng": "ui/btn_house_locked@3x.png"},
                 "note": "花園 HUD 右邊、委託掣下面；家人未解鎖＝上鎖版（灰＋鎖），撳出 toast「同細佬做咗家人就可以一齊住」；解鎖第一次出紅點"},
 "houseHud": {"back": {"cx": 16, "cy": 18, "d": 22, "icon": "back", "to": "garden"}, "title": {"cx": 97.5, "y": 8, "w": 70, "label": "屋仔"},
              "decorate": {"cx": 172, "cy": 392, "d": 30, "icon": "decorate", "label": "佈置", "labelY": 411},
              "note": "屋內平時：返花園、標題、右下「佈置」；撳寵物＝3a 觸摸反應"},
 "decorate": {
   "roomOffsetY": -36, "enterMs": 300, "ease": "easeOutBack（sheet 由下滑上；房間同步上移）",
   "topBar": {"back": {"cx": 16, "cy": 18, "d": 22, "icon": "back"}, "title": {"cx": 97.5, "y": 8, "w": 84, "label": "佈置屋仔"}, "chip": {"x": 147, "y": 10, "w": 40, "kind": "star", "note": "碎"}},
   "pins": {"d": 16, "dSel": 20, "note": "每個 slot 喺房入面（slot.pin＋roomOffsetY）一個圓章：已擺＝該 slot icon、未擺＝＋；揀中＝大啲＋金光＋上下浮 2px/1s；撳 pin＝跳去該 tab"},
   "sheet": {"x": 4, "y": 280, "w": 187, "h": 138, "r": 10},
   "tabs": {"cy": 297, "cx": TAB_X, "d": 22, "dSel": 25, "labelY": 313, "order": J["slotOrder"], "selFill": "pri", "idleFill": "navy"},
   "titleRow": {"x": 14, "y": 321, "hintX": 181},
   "cards": {"x": [8.5, 70.5, 132.5], "y": 328, "w": 54, "h": 66, "thumb": {"cy": 348, "maxW": 46, "maxH": 30, "note": "家具 PNG nearest 整數倍縮放"},
             "nameY": 372, "pill": {"y": 379, "h": 11, "inset": 4},
             "states": {"equipped": "藍綠 pill「擺緊」＋金框光＋右上寶石", "owned": "橙 pill「擺上去」", "buy": "橙 pill 星星碎 icon＋價錢（唔夠碎＝灰）", "locked": "灰卡＋暗剪影＋鎖＋來源（委託獎／訪客禮）",
                        "clear": "第 3 張：收起（清空呢個 slot）"}},
   "done": {"x": 62, "y": 398, "w": 71, "h": 16, "label": "完成", "kind": "pri"},
   "toastFirst": {"x": 34, "y": 140, "w": 128, "msg": "第一次擺：心情 +1", "icon": "decorate"},
   "buyConfirm": "撳價錢 pill → 用現有 HD popup（ui/style_ref/hd2d/home_popup）問「用 N 碎買？」；唔夠碎 pill 變灰、撳出 toast「碎唔夠」"},
 "assets": {}}

def x3(im): return im.resize((im.width // 2, im.height // 2), Image.LANCZOS)
def save_comp(im, name):
    p = f"ui/{name}@3x.png"; x3(im).save(os.path.join(OUT, p)); L["assets"][name] = p; return p
def crop_board(board):
    bb = board.getbbox(); return board.crop(bb) if bb else board
def board(w=195, h=422): return Image.new('RGBA', (P(w), P(h)), (0, 0, 0, 0))

def pill(b, x, y, w, h, kind, label, icon_k=None):
    H.place(b, H.frame(w, h, h / 2, C[kind], glow=0 if kind == 'dis' else .8, ornate=False, rim=0.9), P(x), P(y))
    tc = hx('#FFFFFF') if kind != 'dis' else hx('#D6D8E4'); sc = H.mix(C[kind][1], hx('#000000'), .45)
    if icon_k:
        H.icon(b, icon_k, P(x + 7), P(y + h / 2), 12)
        H.text(b, (P(x + w / 2 + 4), P(y + h / 2 - .2)), label, 6.6, tc, 'fred', stroke=0.8, stroke_col=sc)
    else: H.text(b, (P(x + w / 2), P(y + h / 2 - .3)), label, 6.2, tc, 'serif', stroke=0.8, stroke_col=sc)

def thumb(b, fid, cx, cy, mw=46, mh=30, dark=False):
    f = J["furniture"][fid]; im = Image.open(os.path.join(OUT, f["png"])).convert('RGBA')
    if f["slot"] == "bed": im.alpha_composite(Image.open(os.path.join(OUT, f["front"])).convert('RGBA'))
    bb = im.getbbox(); im = im.crop(bb); s = max(1, int(min(P(mw) / im.width, P(mh) / im.height)))
    im = im.resize((im.width * s, im.height * s), Image.NEAREST)
    if dark:
        a = im.getchannel('A'); im = Image.new('RGBA', im.size, hx('#3A3F62')); im.putalpha(a)
    b.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

SRC_SHORT = {"commission": "委託獎", "visitor:mushroom_granny": "訪客禮", "visitor:firefly_vendor": "訪客禮"}
def fcard(b, x, y, fid, state, shards=60):
    c = L["decorate"]["cards"]; w, h = c["w"], c["h"]
    locked = state == "locked"
    fill = (hx('#3A3F62', 235), hx('#23263E', 240)) if locked else C['navy_in']
    H.place(b, H.frame(w, h, 6, fill, glow=1.3 if state == "equipped" else (0.15 if locked else 0.5), ornate=False, rim=1.0), P(x), P(y))
    W_, H_ = b.size; g = Image.new('L', (W_, H_), 0); ImageDraw.Draw(g).ellipse([P(x + w / 2 - 20), P(y + 6), P(x + w / 2 + 20), P(y + 36)], fill=150)
    put(b, solid((W_, H_), C['cyan'] if not locked else hx('#6A7090')), amul(gauss(g, P(4)), .7 if not locked else .35))
    cy = c["thumb"]["cy"] - c["y"] + y
    if fid == "clear":
        icon(b, "clear", P(x + w / 2), P(cy), 18); name = "收起"
    else:
        thumb(b, fid, P(x + w / 2), P(cy), dark=locked); name = J["furniture"][fid]["zh"]
        if locked: icon(b, "lock", P(x + w / 2), P(cy + 2), 15)
    H.text(b, (P(x + w / 2), P(c["nameY"] - c["y"] + y)), name, 6.0, C['cream'] if not locked else hx('#C9CCDB'), 'sans', stroke=0.8)
    py, ph, ins = c["pill"]["y"] - c["y"] + y, c["pill"]["h"], c["pill"]["inset"]
    if fid == "clear": pill(b, x + ins, py, w - 2 * ins, ph, 'navy', "清空")
    elif state == "equipped":
        pill(b, x + ins, py, w - 2 * ins, ph, 'sec', "擺緊")
        H.gem(b, P(x + w - 3), P(y + 3), 2.6, C['gem'])
    elif state == "owned": pill(b, x + ins, py, w - 2 * ins, ph, 'pri', "擺上去")
    elif state == "buy":
        pr = J["furniture"][fid]["price"]; pill(b, x + ins, py, w - 2 * ins, ph, 'pri' if shards >= pr else 'dis', str(pr), 'star')
    elif state == "locked": pill(b, x + ins, py, w - 2 * ins, ph, 'dis', SRC_SHORT[J["furniture"][fid]["source"]])

def room_ss(var, items, dy=0, pets=()):
    import build_house_4b_preview as PVm
    a = PVm.room(var, items, pets)
    im = Image.fromarray(a).convert('RGBA')
    if dy:
        o = Image.new('RGBA', im.size, (20, 16, 30, 255)); o.paste(im, (0, dy)); im = o
    return im.resize((P(195), P(422)), Image.NEAREST)

def pins(b, items, sel, dy):
    for s in J["slotOrder"]:
        px, py = J["slots"][s]["pin"]; py += dy; on = sel == s; d = 20 if on else 16
        if on:
            W_, H_ = b.size; g = Image.new('L', (W_, H_), 0); ImageDraw.Draw(g).ellipse([P(px - 15), P(py - 15), P(px + 15), P(py + 15)], fill=200)
            put(b, solid((W_, H_), C['glow']), gauss(g, P(3)))
        medal(b, P(px), P(py), d, C['pri'] if on else C['navy'], s if items.get(s) else "plus", d * (0.8 if items.get(s) else 0.55), glow=1.2 if on else .6)

def decorate_ui(b, sel, items, owned, shards):
    D = L["decorate"]; tb = D["topBar"]
    medal(b, P(tb["back"]["cx"]), P(tb["back"]["cy"]), 22, C['navy'], "back", 15)
    H.plaque(b, tb["title"]["cx"], tb["title"]["y"], tb["title"]["w"], tb["title"]["label"])
    H.chip(b, tb["chip"]["x"], tb["chip"]["y"], tb["chip"]["w"], 'star', shards)
    s = D["sheet"]; H.place(b, H.frame(s["w"], s["h"], s["r"], 'panel', glow=1.0, ornate=None), P(s["x"]), P(s["y"]))
    T = D["tabs"]
    for i, sl in enumerate(T["order"]):
        on = sl == sel; d = T["dSel"] if on else T["d"]
        medal(b, P(T["cx"][i]), P(T["cy"] - (1.5 if on else 0)), d, C['pri'] if on else C['navy'], sl, d * .8, glow=1.1 if on else .5)
        H.text(b, (P(T["cx"][i]), P(T["labelY"])), J["slots"][sl]["zh"], 5.8, C['cream'] if on else hx('#AEB4D8'), 'serif', stroke=0.8)
    tr = D["titleRow"]
    H.gold_text(b, (P(tr["x"]), P(tr["y"])), f"{J['slots'][sel]['zh']}・{len(J['slots'][sel]['items'])} 件", 7.2, 'serif', anchor='lm', glow=.4)
    H.text(b, (P(tr["hintX"]), P(tr["y"])), "撳一下就擺，換擺唔使碎", 5.4, hx('#C9D0F0'), 'sans', anchor='rm', stroke=0.6)
    c = D["cards"]
    for i, fid in enumerate(J["slots"][sel]["items"] + ["clear"]):
        if fid == "clear": st = "clear"
        elif items.get(sel) == fid: st = "equipped"
        elif fid in owned: st = "owned"
        elif J["furniture"][fid]["source"] == "shop": st = "buy"
        else: st = "locked"
        fcard(b, c["x"][i], c["y"], fid, st, shards)
    dn = D["done"]; H.button(b, dn["x"], dn["y"], dn["w"], dn["h"], dn["kind"], dn["label"])

def mock_decorate(sel, items, owned, shards, var="day", toast=False):
    bg = room_ss(var, items, L["decorate"]["roomOffsetY"])
    ui = board(); pins(ui, items, sel, L["decorate"]["roomOffsetY"]); decorate_ui(ui, sel, items, owned, shards)
    if toast: H.toast(ui, **{kk: L["decorate"]["toastFirst"][kk] for kk in ("x", "y", "w")}, msg=L["decorate"]["toastFirst"]["msg"], kind='heart' if 'heart' in dir() else 'light')
    bg.alpha_composite(ui); return x3(bg)

def mock_house(items, var="day"):
    import build_house_4b_preview as PVm
    trw, trp, _ = PVm.pet_frames(PVm.TR, "sit"); kw, kp, _ = PVm.pet_frames(PVm.KID, "sit"); rug = J["slots"]["rug"]["anchor"]
    pets = [(trw[3], trp, rug[0] - 18, rug[1] + 2, rug[1] + 2), (*PVm.flip(kw[3], kp), rug[0] + 18, rug[1] + 2, rug[1] + 2)]
    bg = room_ss(var, items, 0, pets); ui = board(); hh = L["houseHud"]
    medal(ui, P(hh["back"]["cx"]), P(hh["back"]["cy"]), 22, C['navy'], "back", 15)
    H.plaque(ui, hh["title"]["cx"], hh["title"]["y"], hh["title"]["w"], hh["title"]["label"])
    dc = hh["decorate"]; medal(ui, P(dc["cx"]), P(dc["cy"]), dc["d"], C['navy'], "decorate", 24)
    H.text(ui, (P(dc["cx"]), P(dc["labelY"])), dc["label"], 6.4, C['cream'], 'serif', stroke=0.9)
    bg.alpha_composite(ui); return x3(bg)

def mock_garden_entry(locked=False):
    g = Image.open(os.path.join(ART, "ui/style_ref/hd2d/home_HD2D_3x.png")).convert('RGBA').resize((P(195), P(422)), Image.LANCZOS)
    ui = board(); e = L["gardenEntry"]["btn"]
    medal(ui, P(e["cx"]), P(e["cy"]), e["d"], C['dis'] if locked else C['navy'], "house", 19, glow=.3 if locked else 1.0, dim=locked)
    if locked: icon(ui, "lock", P(e["cx"] + 7), P(e["cy"] + 7), 10)
    else: H.red_dot(ui, P(e["cx"] + 9), P(e["cy"] - 9.5))
    H.text(ui, (P(e["cx"]), P(e["labelY"])), e["label"], 6.4, C['cream'] if not locked else hx('#C9CCDB'), 'serif', stroke=0.9)
    g.alpha_composite(ui); return x3(g)

def components():
    os.makedirs(UO, exist_ok=True)
    for kd in J["slotOrder"] + ["house", "decorate", "back", "clear", "plus", "lock"]:
        save_comp(hd_icon(kd), f"icon_{kd}")
    for locked in (False, True):
        b = board(30, 30); medal(b, P(15), P(15), 24, C['dis'] if locked else C['navy'], "house", 19, glow=.3 if locked else 1.0, dim=locked)
        if locked: icon(b, "lock", P(22), P(22), 10)
        save_comp(crop_board(b), "btn_house_locked" if locked else "btn_house")
    for s in J["slotOrder"]:
        for on in (False, True):
            b = board(34, 34); d = 25 if on else 22; medal(b, P(17), P(17), d, C['pri'] if on else C['navy'], s, d * .8, glow=1.1 if on else .5)
            save_comp(crop_board(b), f"tab_{s}_{'sel' if on else 'idle'}")
    for kind, on in (("plus", False), ("plus", True), ("filled", False), ("filled", True)):
        b = board(30, 30); d = 20 if on else 16; medal(b, P(15), P(15), d, C['pri'] if on else C['navy'], "plus" if kind == "plus" else None, d * .55, glow=1.2 if on else .6)
        save_comp(crop_board(b), f"pin_{kind}_{'sel' if on else 'idle'}")
    b = board(200, 150); s = L["decorate"]["sheet"]; H.place(b, H.frame(s["w"], s["h"], s["r"], 'panel', glow=1.0), P(6), P(6)); save_comp(crop_board(b), "sheet_panel")
    for st, fid in (("equipped", "bed_leaf"), ("owned", "lamp_mushroom"), ("buy", "bed_cloud"), ("locked", "win_star"), ("clear", "clear")):
        b = board(62, 74); fcard(b, 4, 4, fid, st); save_comp(crop_board(b), f"card_{st}_example")
    b = board(80, 24); H.button(b, 4, 4, 71, 16, 'pri', '完成'); save_comp(crop_board(b), "btn_done")
    b = board(40, 44); dc = L["houseHud"]["decorate"]; medal(b, P(20), P(18), 30, C['navy'], "decorate", 24); H.text(b, (P(20), P(37)), "佈置", 6.4, C['cream'], 'serif', stroke=0.9)
    save_comp(crop_board(b), "btn_decorate")
    b = board(30, 30); medal(b, P(15), P(15), 22, C['navy'], "back", 15); save_comp(crop_board(b), "btn_back")

def label(im, s):
    from PIL import ImageFont
    im = im.convert('RGB'); o = Image.new('RGB', (im.width, im.height + 46), (40, 28, 36)); o.paste(im, (0, 46))
    ImageDraw.Draw(o).text((14, 6), s, font=ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", 28, index=2), fill=(255, 240, 220)); return o

def main():
    components()
    A = J["sets"]["A"]["items"]
    st1 = {"bed": "bed_leaf", "rug": "rug_round", "window": "win_curtain"}
    m1 = mock_decorate("bed", st1, {"bed_leaf", "rug_round", "win_curtain"}, 60, toast=True)
    m2 = mock_decorate("lamp", st1, {"bed_leaf", "rug_round", "win_curtain", "lamp_mushroom"}, 12)
    m3 = mock_house(A); g0 = mock_garden_entry(False); g1 = mock_garden_entry(True)
    os.makedirs(PV, exist_ok=True)
    for im, n in ((m1, "decorate_bed_HD2D_3x"), (m2, "decorate_lamp_HD2D_3x"), (m3, "house_hud_HD2D_3x"), (g0, "garden_entry_HD2D_3x"), (g1, "garden_entry_locked_HD2D_3x")):
        im.convert('RGB').save(os.path.join(PV, n + ".png"))
    tl = ["佈置・床（擺緊／買）", "佈置・燈（擁有／上鎖）", "屋仔平時", "花園入口", "花園入口（上鎖）"]
    ims = [label(im, t) for im, t in zip((m1, m2, m3, g0, g1), tl)]
    sh = Image.new('RGB', (len(ims) * 597 - 12, ims[0].height), (40, 28, 36))
    for i, im in enumerate(ims): sh.paste(im, (i * 597, 0))
    sh.save(os.path.join(PV, "decorate_ui_HD2D_3x.png"))
    # 零件 sheet
    names = list(L["assets"].values()); ims = [Image.open(os.path.join(OUT, p)) for p in names]
    W = 1200; x = y = 10; rowh = 0; pos = []
    for im in ims:
        if x + im.width > W - 10: x = 10; y += rowh + 10; rowh = 0
        pos.append((x, y)); x += im.width + 10; rowh = max(rowh, im.height)
    sheet = Image.new('RGBA', (W, y + rowh + 10), (28, 30, 56, 255))
    for im, p in zip(ims, pos): sheet.alpha_composite(im.convert('RGBA'), p)
    sheet.convert('RGB').save(os.path.join(PV, "ui_parts_HD2D_3x.png"))
    json.dump(L, open(os.path.join(UO, "layout.json"), "w"), ensure_ascii=False, indent=1)
    J2 = json.load(open(os.path.join(OUT, "house.json"))); J2["ui"] = L; json.dump(J2, open(os.path.join(OUT, "house.json"), "w"), ensure_ascii=False, indent=1)
    print("ui ok", len(L["assets"]))

if __name__ == "__main__": main()
