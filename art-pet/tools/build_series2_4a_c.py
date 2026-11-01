# series2 4a 第 C 部：8 道具 icon＋8 夢泡泡（B2 繪本貼紙・甜甜版，ui_v2_kit，3x）— 純 Pillow，無 AI
import os, json, math
from PIL import Image, ImageDraw, ImageChops
import ui_v2_kit as U
from series2_lib import S2
k = U.k; hx = U.hx; P = U.P; E, POLY, RR = U.E, U.POLY, U.RR
TH = U.B2
OUT = os.path.join(S2, "ui")

def ring(b, w):
    def fn(d, q):
        d.ellipse([q(b[0]), q(b[1]), q(b[2]), q(b[3])], fill=255)
        d.ellipse([q(b[0] + w), q(b[1] + w), q(b[2] - w), q(b[3] - w)], fill=0)
    return fn
def arc(b, a0, a1, w):
    return lambda d, q: d.arc([q(b[0]), q(b[1]), q(b[2]), q(b[3])], a0, a1, fill=255, width=max(1, q(w) - q(0)))
def rot_poly(cx, cy, w, h, ang):
    a = math.radians(ang); pts = []
    for x, y in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)):
        pts.append((cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)))
    return POLY(pts)
def crescent(b, off):
    def fn(d, q):
        d.ellipse([q(b[0]), q(b[1]), q(b[2]), q(b[3])], fill=255)
        d.ellipse([q(b[0] + off), q(b[1] - off * .3), q(b[2] + off), q(b[3] - off * .3)], fill=0)
    return fn

BLUE = (hx('#C8EEFF'), hx('#7FC6F6')); PINK = (hx('#FFC4D8'), hx('#FF92B6')); WOOD = (hx('#F4CDA6'), hx('#D9A070'))
YEL = (hx('#FFF2A6'), hx('#FFCF4A')); RED = (hx('#FFAFA0'), hx('#F0606A')); GRN = (hx('#C9F5AE'), hx('#7FD36E'))
GREY = (hx('#F0ECF6'), hx('#C9C0D8')); LIL = (hx('#E6D6FF'), hx('#B49BF4')); WHITE2 = (hx('#FFFFFF'), hx('#F1E8F6'))

def prop_icon(kind):
    ic = k.Icon(TH)
    if kind == "can":        # 水壺
        ic.part(arc((5, 2, 14, 12), 180, 360, 1.8), WOOD, gloss=False)
        ic.part(POLY([(15.5, 13.5), (21, 8.2), (22.2, 9.4), (16.5, 16.5)]), BLUE, gloss=False)
        ic.part(rot_poly(21.8, 8.2, 2.2, 4.4, 45), (hx('#9ED8FA'), hx('#6CB6EE')), gloss=False)
        ic.part(RR((2.5, 7, 17, 21.5), 4.5), BLUE)
        ic.face(9.6, 13.5, 0.7)
        for x, y in ((22.5, 11.5), (21, 14.2)):
            ic.part(E((x - .9, y - .9, x + .9, y + .9)), BLUE, gloss=False, outline=False)
    elif kind == "wand":     # 泡泡棒
        ic.part(RR((10.6, 11.5, 13.4, 23), 1.2), WOOD, gloss=False)
        ic.part(ring((4.5, 1, 19.5, 15.5), 2.6), PINK, gloss=False)
        for b in ((15.5, 12.5, 21.5, 18.5), (18.5, 5, 22.5, 9)):
            ic.part(ring(b, .9), (hx('#FFFFFF'), hx('#BFE8FF')), gloss=False)
    elif kind == "match":    # 火柴
        ic.part(rot_poly(12.5, 15, 3.4, 15, 18), WOOD, gloss=False)
        ic.part(E((7.6, 4.5, 13.2, 10.5)), RED)
        ic.part(POLY([(10.5, -0.5), (14.5, 3.5), (13.5, 6), (10, 7), (7.5, 4.5)]), YEL, gloss=False, round_=0.6)
    elif kind == "pebble":   # 石仔
        ic.part(E((2.5, 7, 21.5, 21.5)), GREY)
        ic.part(E((6, 15, 10, 18)), (hx('#E4DCEE'), hx('#D6CCE4')), gloss=False, outline=False)
        ic.face(13, 13.5, 0.8, 'sleep')
    elif kind == "chili":    # 辣椒
        ic.part(POLY([(9, 7), (17, 6), (19, 10), (15.5, 17), (8, 22.5), (6, 21.5), (9.5, 15), (8, 10)]), RED, round_=1.4)
        ic.part(POLY([(9, 7.5), (12.5, 4), (16, 5.5), (17, 7.5), (13, 8.8)]), GRN, gloss=False, round_=0.5)
        ic.part(RR((12, 0.5, 14, 6), 1), GRN, gloss=False)
        ic.face(13.2, 11.5, 0.6)
    elif kind == "scope":    # 望遠鏡
        ic.part(rot_poly(11, 13, 19, 6.4, -30), LIL)
        ic.part(rot_poly(4.4, 16.8, 3, 8.2, -30), YEL, gloss=False)
        ic.part(rot_poly(17.6, 9.2, 2.6, 6.2, -30), YEL, gloss=False)
        ic.part(POLY(k.star_pts(20.5, 3.5, 3.4, 1.6)), YEL, gloss=False, round_=0.3)
    elif kind == "book":     # 書（故仔書）
        ic.part(RR((1.5, 5, 22.5, 21.5), 2.5), PINK, gloss=False)
        ic.part(RR((3, 4, 11.8, 19.5), 1.5), WHITE2, gloss=False)
        ic.part(RR((12.2, 4, 21, 19.5), 1.5), WHITE2, gloss=False)
        d = ImageDraw.Draw(ic.img)
        for y in (8, 10.6, 13.2):
            d.line([(ic.c(5), ic.c(y)), (ic.c(10), ic.c(y))], fill=hx('#C9B6E0'), width=P(0.6))
        ic.part(POLY(k.star_pts(16.6, 11, 3.4, 1.6)), YEL, gloss=False, round_=0.3)
    elif kind == "moonlamp":  # 月亮燈
        ic.part(RR((7.5, 19, 16.5, 22.5), 1.5), WOOD, gloss=False)
        ic.part(RR((11, 15, 13, 20), .8), WOOD, gloss=False, outline=False)
        ic.part(crescent((3, 1, 19, 17), 5.2), YEL, round_=0.4)
        ic.face(7.8, 9.6, 0.55, 'sleep')
    return ic.finish()

def dream_bubble(kind):
    """夢泡泡：雲朵泡（白→淡紫）＋左下 2 粒細泡，入面放該道具 icon（縮細）＋夜晚小星"""
    N = P(44); img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    th = dict(TH)
    ic = k.Icon(th, n=38)
    def cloud(d, q):
        for b in ((4, 9, 20, 25), (10, 3, 26, 19), (19, 2, 35, 18), (24, 9, 38, 25), (8, 15, 33, 31), (19, 16, 35, 30)):
            d.ellipse([q(b[0]), q(b[1]), q(b[2]), q(b[3])], fill=255)
    ic.part(cloud, (hx('#FFFFFF'), hx('#EEE6FF')), gloss=False, round_=0.6)
    ic.part(E((4, 30, 9, 35)), (hx('#FFFFFF'), hx('#EEE6FF')), gloss=False)
    ic.part(E((1, 35.5, 4.2, 38.7)), (hx('#FFFFFF'), hx('#EEE6FF')), gloss=False)
    for (x, y, r) in ((8, 10, 1.6), (31, 25, 1.3)):
        ic.part(POLY(k.star_pts(x, y, r * 1.6, r * .75)), YEL, gloss=False, outline=False)
    base = ic.finish()
    pi = prop_icon(kind); s = P(23) / pi.width
    pi = pi.resize((int(pi.width * s), int(pi.height * s)), Image.LANCZOS)
    cx, cy = ic.c(21.5), ic.c(16.5)
    base.alpha_composite(pi, (int(cx - pi.width / 2), int(cy - pi.height / 2)))
    return base

def to3x(im):  # SS(6/單位) → 3x
    return im.resize((im.width // 2, im.height // 2), Image.LANCZOS)

KINDS = [("A", "can", "水壺", "淋花／飲水"), ("B", "wand", "泡泡棒", "沖涼／吹泡泡"), ("C", "match", "火柴", "取暖／點燈"), ("D", "pebble", "石仔", "執石仔／砌嘢"),
         ("E", "chili", "辣椒", "食嘢（辣）"), ("F", "scope", "望遠鏡", "睇星"), ("G", "book", "書", "講故仔"), ("H", "moonlamp", "月亮燈", "開夜燈陪瞓")]

def main():
    os.makedirs(os.path.join(OUT, "prop_icons"), exist_ok=True); os.makedirs(os.path.join(OUT, "dream_bubbles"), exist_ok=True)
    idx = {"style": "B2 繪本貼紙・甜甜版（ui/style_ref/v2），3x；icon 30 單位＝90px、夢泡泡 44 單位＝132px", "props": {}, "dreams": {}}
    icons, dreams = [], []
    for row, kind, zh, care in KINDS:
        a = to3x(prop_icon(kind)); p = f"ui/prop_icons/icon_prop_{row}_{kind}@3x.png"; a.save(os.path.join(S2, p)); icons.append(a)
        b = to3x(dream_bubble(kind)); q = f"ui/dream_bubbles/dream_{row}_{kind}@3x.png"; b.save(os.path.join(S2, q)); dreams.append(b)
        idx["props"][row] = {"png": p, "prop": "prop_" + kind, "zh": zh, "size": list(a.size)}
        idx["dreams"][row] = {"png": q, "care": care, "zh": zh, "size": list(b.size), "anchor": "團絨 headTop 右上（dx +10, dy −8 @1x）；泡泡尾（左下細泡）指向團絨"}
    json.dump(idx, open(os.path.join(OUT, "ui_series2_4a.json"), "w"), ensure_ascii=False, indent=1)
    # 預覽 sheet
    W = 8 * 140; sheet = Image.new("RGBA", (W, 290), (255, 240, 247, 255))
    for i, (a, b) in enumerate(zip(icons, dreams)):
        sheet.alpha_composite(a, (i * 140 + 25, 10)); sheet.alpha_composite(b, (i * 140 + 4, 120))
    os.makedirs(os.path.join(S2, "preview"), exist_ok=True); sheet.convert("RGB").save(os.path.join(S2, "preview", "ui_props_dreams.png"))
    print("ui ok")

if __name__ == "__main__":
    main()
