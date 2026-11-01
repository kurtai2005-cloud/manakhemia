# 《微光小圃》4b 屋仔 — 預覽（3x）＋GIF：森林組／夢幻組房、兩隻寵物住喺入面、行→坐埋→整蠱 GIF
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import house_4b_room as R
import reactions_lib as L
import build_series2_4a as B
import build_house_4b_actions as HA
from series2_lib import ART

OUT = os.path.join(ART, "sprites/series2_house"); PV = os.path.join(OUT, "preview"); os.makedirs(PV, exist_ok=True)
J = json.load(open(os.path.join(OUT, "house.json")))
TR, KID = "evo_still_lumi", "F3"
FX = L.build_fx(); FXA = {"fx": FX, "series": {}}
ld = lambda p: np.asarray(Image.open(os.path.join(OUT, p)).convert("RGBA"))

def pet_frames(k, name):
    r = B.rig_of(k); H, W = r.base.shape[:2]; px, py = r.pivot
    c = B.ACTIONS.get(name) or HA.CLIPS[name]; pw, pt = HA.PAD_X, HA.PAD_TOP
    comp = B.Comp2(r, FXA, CW=W + 2 * pw, CH=H + pt, PX=px + pw, PY=py + pt)
    clip = {"body": c["body"], "face": c["face"], "fx": c.get("fx", [])}
    return [B.render_frame(comp, clip, i * c["frameMs"]) for i in range(c["frames"])], (px + pw, py + pt), H

def flip(img, piv): return img[:, ::-1].copy(), (img.shape[1] - 1 - piv[0], piv[1])

def shadow(w, h):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(im).ellipse((0, 0, w - 1, h - 1), fill=(60, 36, 40, 70)); return np.asarray(im)

def room(var, items, pets=(), extra=()):
    """items: {slot: fid}; pets: [(img, piv, x, y, sortY)]"""
    S = []; night = var == "night"
    for slot, fid in items.items():
        if not fid: continue
        f = J["furniture"][fid]; ax, ay = J["slots"][slot]["anchor"]; px, py = f["pivot"]; x, y = ax - px, ay - py
        lay = J["slots"][slot]["layer"]; img = ld(f["png"])
        z = {"wall": -1000, "floor": -500}.get(lay, ay)
        S.append((z, img, x, y, "furn"))
        if "shadow" in f:
            w, h = f["shadow"]; S.append((-400, shadow(w, h), ax - w // 2, ay - h // 2 - 1, "shadow"))
        if slot == "bed": S.append((ay + 0.1, ld(f["front"]), x, y, "furn"))
        if slot == "lamp" and night:
            g = ld(f["glow"]); gx, gy = f["glowCenter"]; S.append((9999, g, x + gx - g.shape[1] // 2, y + gy - g.shape[0] // 2, "glow"))
    for img, piv, x, y, sy in pets:
        S.append((sy, img, x - piv[0], y - piv[1], "pet"))
        if sy is not None: S.append((-399, shadow(20, 5), x - 10, y - 3, "shadow"))
    S += list(extra)
    return R.compose(var, OUT + "/room", S)

x3 = lambda a: Image.fromarray(a).resize((a.shape[1] * 3, a.shape[0] * 3), Image.NEAREST)
def label(im, s, y=6):
    from PIL import ImageFont
    d = ImageDraw.Draw(im); f = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", 28, index=2)
    d.rectangle((0, y - 4, im.width, y + 40), fill=(40, 28, 36)); d.text((14, y), s, font=f, fill=(255, 240, 220)); return im

def fx_img(fid, i=0): return FX[fid]["frames"][i % len(FX[fid]["frames"])]

SA, SB = J["sets"]["A"]["items"], J["sets"]["B"]["items"]
def main():
    trw, trp, trh = pet_frames(TR, "walk"); kw, kp, kh = pet_frames(KID, "walk")
    trs, _, _ = pet_frames(TR, "sit"); ks, _, _ = pet_frames(KID, "sit")
    trz, _, _ = pet_frames(TR, "sleep"); kz, _, _ = pet_frames(KID, "sleep")
    rug = J["slots"]["rug"]["anchor"]; bed = J["slots"]["bed"]["anchor"]; ss = J["furniture"]["bed_leaf"]["sleepSpots"]
    def sit_pets(i):
        a = (trs[i], trp, rug[0] - 18, rug[1] + 2, rug[1] + 2); b = (*flip(ks[i], kp), rug[0] + 18, rug[1] + 2, rug[1] + 2)
        return [a, (b[0], b[1], b[2], b[3], b[4])]
    # 1 房 A／B（日＋夜）
    for sid, items in (("A", SA), ("B", SB)):
        ims = [label(x3(room(v, items)), f"屋仔 {sid} {J['sets'][sid]['zh']}（{'日' if v == 'day' else '夜'}）") for v in ("day", "night")]
        sheet = Image.new("RGB", (585 * 2 + 12, 1266), (40, 28, 36)); sheet.paste(ims[0], (0, 0)); sheet.paste(ims[1], (597, 0))
        sheet.save(os.path.join(PV, f"room_set{sid}_3x.png")); ims[0].save(os.path.join(PV, f"room_set{sid}_day_3x.png"))
    empty = label(x3(room("day", {})), "屋仔 初始（空房）"); empty.save(os.path.join(PV, "room_empty_day_3x.png"))
    # 2 兩隻住喺入面：行／坐埋／同床瞓
    p1 = room("day", SB, [(trw[2], trp, 84, 302, 302), (*flip(kw[4], kp), 150, 286, 286)])
    p2 = room("day", SB, sit_pets(3), [(9000, fx_img("fx_heart"), rug[0] - 4, rug[1] - 40, "furn")])
    zz = fx_img("fx_zzz")
    p3 = room("night", SA, [(trz[1], trp, bed[0] + ss[0][0], bed[1] + ss[0][1], bed[1]), (*flip(kz[2], kp), bed[0] + ss[1][0], bed[1] + ss[1][1], bed[1])],
              [(9000, zz, bed[0] - 14, bed[1] - 52, "furn"), (9000, zz, bed[0] + 26, bed[1] - 50, "furn")])
    tl = ["行吓（夢幻組・日）", "坐埋一齊（地氈）", "同一張床瞓（森林組・夜）"]
    sheet = Image.new("RGB", (585 * 3 + 24, 1266), (40, 28, 36))
    for i, p in enumerate((p1, p2, p3)): sheet.paste(label(x3(p), tl[i]), (i * 597, 0))
    sheet.save(os.path.join(PV, "living_two_pets_3x.png"))
    # 3 GIF（2x）：行 → 坐埋 → 整蠱
    fr, du = [], []
    def add(a, ms): fr.append(Image.fromarray(a).resize((390, 844), Image.NEAREST)); du.append(ms)
    tx, kx = 40, 168; ty, ky = 304, 280; gx, gy = rug[0] - 18, rug[1] + 2; hx_, hy = rug[0] + 18, rug[1] + 2
    for i in range(22):
        t = i / 21; a = (trw[i % 6], trp, round(tx + (gx - tx) * t), round(ty + (gy - ty) * t), round(ty + (gy - ty) * t))
        bimg, bp = flip(kw[i % 6], kp); b = (bimg, bp, round(kx + (hx_ - kx) * t), round(ky + (hy - ky) * t), round(ky + (hy - ky) * t))
        add(room("day", SB, [a, b]), 100)
    seq = [0, 1, 2, 3, 4, 5, 2, 3, 4, 5, 2, 3, 4, 5]
    for j, i in enumerate(seq):
        ex = [(9000, fx_img("fx_heart", j), rug[0] - 4, rug[1] - 40 - j % 3, "furn")] if 6 <= j <= 10 else []
        add(room("day", SB, sit_pets(i), ex), 150)
    # 細佬行去團絨後面（團絨企起向右）
    tr_base = B.rig_of(TR).base; trb = np.zeros_like(trw[0]); h, w = tr_base.shape[:2]
    trb[HA.PAD_TOP:HA.PAD_TOP + h, HA.PAD_X:HA.PAD_X + w] = tr_base
    vx, vy = gx + 16, gy; start = vx - 24
    for i in range(12):
        t = i / 11; kxx = round(hx_ + (start - 6 - hx_) * t)
        img, p = (flip(kw[i % 6], kp) if i < 11 else (kw[0], kp))
        add(room("day", SB, [(trb, trp, vx, vy, vy), (img, p, kxx, vy + 1, vy + 1)]), 100)
    pd, _, _ = pet_frames(KID, "prank_do"); pg, _, _ = pet_frames(TR, "prank_got")
    for i in range(8):
        add(room("day", SB, [(pg[i], trp, vx, vy, vy), (pd[i], kp, start - 6 + 2 * min(i, 3), vy + 1, vy + 1)]), 120 if i != 4 else 360)
    for j in range(4):
        add(room("day", SB, [(pg[6 + j % 2], trp, vx, vy, vy), (pd[6 + j % 2], kp, start, vy + 1, vy + 1)]), 160)
    add(room("day", SB, [(pg[7], trp, vx, vy, vy), (pd[7], kp, start, vy + 1, vy + 1)]), 900)
    fr[0].save(os.path.join(PV, "house_two_pets.gif"), save_all=True, append_images=fr[1:], duration=du, loop=0, disposal=1)
    print("frames", len(fr))

if __name__ == "__main__": main()
