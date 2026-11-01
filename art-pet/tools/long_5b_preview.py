# 5b 預覽：出發／返屋 GIF（房內）、成年戴工作帽（每款 × 每級）sheet＋GIF、手信 sheet
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import long_5abc_lib as LB
import long_5abc_ui as U
from series2_lib import ART
O5 = os.path.join(LB.OUTL, "5b"); PV = os.path.join(O5, "preview"); os.makedirs(PV, exist_ok=True)
D = json.load(open(os.path.join(O5, "long_5b.json")))
_C = {}
def ld(p):
    if p not in _C: _C[p] = np.asarray(Image.open(p).convert("RGBA"))
    return _C[p]
def hat_frame(k, job, tier, clip, i):
    rows = [r for r in D["jobs"]["forms"][k][job]["rows"] if r["tier"] == tier and r["clip"] == clip][0]
    a = ld(os.path.join(O5, D["jobs"]["forms"][k][job]["png"])); i %= rows["frames"]
    return a[rows["y"]:rows["y"] + rows["frameH"], i * rows["frameW"]:(i + 1) * rows["frameW"]], tuple(rows["pivot"]), rows["frames"]
def put(dst, src, x, y):
    h, w = src.shape[:2]; x0, y0 = max(0, x), max(0, y); x1, y1 = min(dst.shape[1], x + w), min(dst.shape[0], y + h)
    if x1 <= x0 or y1 <= y0: return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]; m = s[..., 3] > 0; dst[y0:y1, x0:x1][m] = s[m]
def pet_with_hat(k, job, tier, clip, i):
    f, piv, g = U.strip_frame(k, clip, i); h, hp, _ = hat_frame(k, job, tier, clip, i)
    W, Hh = 80, 86; o = np.zeros((Hh, W, 4), np.uint8); px, py = 40, 82
    put(o, f, px - piv[0], py - piv[1]); put(o, h, px - hp[0], py - hp[1]); return o
def up(a, s=3): return Image.fromarray(a).resize((a.shape[1] * s, a.shape[0] * s), Image.NEAREST)
JOBS = [j["id"] for j in D["jobs"]["list"]]; TIERS = [t["id"] for t in D["jobs"]["tiers"]]

def hats_sheet(forms, name, tiers=TIERS):
    cw, ch = 80, 86; cols = len(JOBS) * len(tiers)
    sheet = Image.new("RGBA", ((cols * cw + 60) * 3, (len(forms) * ch + 24) * 3), (40, 34, 58, 255)); dr = ImageDraw.Draw(sheet)
    for j, job in enumerate(JOBS):
        for t, tier in enumerate(tiers):
            c = j * len(tiers) + t; dr.text(((60 + c * cw + 4) * 3, 6), D['jobs']['list'][j]['zh'] + '\n' + D['jobs']['tiers'][TIERS.index(tier)]['zh'].split()[0], fill=(255, 240, 200), font=LB.font(24))
    for r_, k in enumerate(forms):
        dr.text((6, (24 + r_ * ch + 36) * 3), k.replace("evo_still_", "靜光"), fill=(220, 220, 240), font=LB.font(22))
        for j, job in enumerate(JOBS):
            for t, tier in enumerate(tiers):
                c = j * len(tiers) + t; sheet.alpha_composite(up(pet_with_hat(k, job, tier, "sit", 0)), ((60 + c * cw) * 3, (24 + r_ * ch) * 3))
    sheet.save(os.path.join(PV, name))

def hats_gif():
    forms = ["A3", "evo_still_tide", "E2", "evo_still_moon"]; fr = []
    for job in JOBS:
        for tier in TIERS:
            for i in range(6):
                row = np.zeros((86, 80 * len(forms), 4), np.uint8)
                for n, k in enumerate(forms): put(row, pet_with_hat(k, job, tier, "sit", i), n * 80, 0)
                im = Image.new("RGBA", (row.shape[1] * 3, row.shape[0] * 3 + 60), (40, 34, 58, 255)); im.alpha_composite(up(row), (0, 60))
                ImageDraw.Draw(im).text((12, 12), f"{D['jobs']['list'][JOBS.index(job)]['zh']}  {D['jobs']['tiers'][TIERS.index(tier)]['zh']}", fill=(255, 240, 200), font=LB.font(30)); fr.append(im)
    LB.save_gif(fr, os.path.join(PV, "job_hats_on_pets.gif"), 180)

SET = {"bed": "bed_leaf", "table": "table_stump", "wall": "wall_shelf", "rug": "rug_leaf", "window": "win_curtain", "lamp": "lamp_mushroom"}
def trip_gif(k="A3", room="room2", sv="sv_pinecone"):
    fr = []; svpx = ld(os.path.join(O5, f"souvenir/{sv}_1x.png")); ht = D["expedition"]["forms"][k]["headTop"]
    X0, Y0 = 100, 330
    def frame(clip, i, dx, alpha=1.0, souv=None, cap=""):
        if clip is None:
            im = U.room_ss(room, "day", SET).resize((585, 1266), Image.LANCZOS)
            ImageDraw.Draw(im).text((24, 1190), cap, fill=(255, 255, 255), font=LB.font(34), stroke_width=3, stroke_fill=(40, 30, 50)); return im
        f, piv, g = U.strip_frame(k, clip, i)
        if alpha < 1: f = f.copy(); f[..., 3] = np.where(np.random.RandomState(i).rand(*f.shape[:2]) < alpha, f[..., 3], 0)
        ex = []
        if souv is not None:
            sx = X0 + dx - 24 + int(ht[0]) - svpx.shape[1] // 2; sy = Y0 - 45 + int(ht[1]) - 10 - svpx.shape[0] + souv
            ex.append((9998, svpx, sx, sy, "furn"))
        im = U.room_ss(room, "day", SET, [(f, piv, X0 + dx, Y0, Y0)], ex)
        im = im.resize((585, 1266), Image.LANCZOS); ImageDraw.Draw(im).text((24, 1190), cap, fill=(255, 255, 255), font=LB.font(34), stroke_width=3, stroke_fill=(40, 30, 50)); return im
    for i in range(10):
        dx = max(0, i - 3) * 2; fr.append(frame("depart", i, dx, 1.0 if i < 7 else (9 - i) / 3 + 0.05, cap="出發：背住背囊行去門口"))
    for _ in range(3): fr.append(frame(None, 0, 0, cap="（遠足中 24 小時）"))
    bob = [0, -1, 0, 1, 0]
    for i in range(10):
        dx = max(0, 3 - i) * 2; fr.append(frame("return", i, dx, souv=bob[(i - 5) % 5] if i >= 5 else None, cap="返屋：背囊脹晒，頭頂出手信"))
    for _ in range(4): fr.append(frame("return", 9, 0, souv=0, cap="返屋：背囊脹晒，頭頂出手信"))
    LB.save_gif(fr, os.path.join(PV, f"trip_{k}_{room}.gif"), 120); fr[5].save(os.path.join(PV, f"trip_{k}_depart_3x.png")); fr[-1].save(os.path.join(PV, f"trip_{k}_return_3x.png"))

def trip_sheet():
    forms = LB.ADULTS; cw, ch = 74, 82; per = 9
    rows = (len(forms) + per - 1) // per
    sheet = Image.new("RGBA", (per * 2 * cw * 3, rows * (ch + 14) * 3), (40, 34, 58, 255)); dr = ImageDraw.Draw(sheet)
    for n, k in enumerate(forms):
        for m, (clip, i) in enumerate((("depart", 2), ("return", 6))):
            f, piv, _ = U.strip_frame(k, clip, i); o = np.zeros((ch, cw, 4), np.uint8); put(o, f, cw // 2 - piv[0], ch - 4 - piv[1])
            x = ((n % per) * 2 + m) * cw * 3; y = (n // per) * (ch + 14) * 3; sheet.alpha_composite(up(o), (x, y + 14 * 3))
        dr.text((((n % per) * 2) * cw * 3 + 8, (n // per) * (ch + 14) * 3 + 6), k.replace("evo_still_", "靜光"), fill=(255, 240, 200), font=LB.font(26))
    sheet.save(os.path.join(PV, "trip_all_adults_3x.png"))

def souv_sheet():
    sv = D["souvenirs"]; im = Image.new("RGBA", (5 * 220, 2 * 260), (40, 34, 58, 255)); dr = ImageDraw.Draw(im)
    for n, s in enumerate(sv):
        x, y = (n % 5) * 220, (n // 5) * 260
        a = Image.open(os.path.join(O5, s["medal"])); a.thumbnail((120, 120)); im.alpha_composite(a, (x + 10, y + 10))
        p = Image.open(os.path.join(O5, s["px"])); p = p.resize((p.width * 6, p.height * 6), Image.NEAREST); im.alpha_composite(p, (x + 130, y + 30))
        dr.text((x + 12, y + 200), s["zh"], fill=(255, 240, 200), font=LB.font(30))
    im.save(os.path.join(PV, "souvenirs_sheet.png"))

if __name__ == "__main__":
    hats_sheet(["A3", "A2", "B3", "C3", "D3", "E2", "F3", "G3", "H3"], "job_hats_kid_3x.png")
    hats_sheet(LB.TR_ADULT, "job_hats_tuanrong_3x.png")
    hats_gif(); trip_gif(); trip_gif("evo_still_moon", "room3", "sv_starstone"); trip_sheet(); souv_sheet(); print("ok")
