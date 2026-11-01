# 5c 預覽：花紋 8 款喺新蛋（團絨蛋／細佬蛋）、喺各形態（成長線＋團絨）、idle GIF
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import long_5abc_lib as LB
import long_5abc_ui as U
import long_5c_patterns as PT
import long_5c_build as B5
from series2_lib import ART
O5 = os.path.join(LB.OUTL, "5c"); PV = os.path.join(O5, "preview"); os.makedirs(PV, exist_ok=True)
D = json.load(open(os.path.join(O5, "long_5c.json"))); PN = [p["id"] for p in D["patterns"]]; PZ = {p["id"]: p["zh"] for p in D["patterns"]}
PARENT = {"wave": "A3", "bubble": "B3", "spark": "C3", "spot": "D3", "flame": "E3", "star": "F3", "diamond": "G3", "crescent": "H3"}
_C = {}
def ld(p):
    if p not in _C: _C[p] = np.asarray(Image.open(p).convert("RGBA"))
    return _C[p]
def put(dst, src, x, y):
    h, w = src.shape[:2]; x0, y0 = max(0, x), max(0, y); x1, y1 = min(dst.shape[1], x + w), min(dst.shape[0], y + h)
    if x1 <= x0 or y1 <= y0: return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]; m = s[..., 3] > 0; dst[y0:y1, x0:x1][m] = s[m]
def pat_frame(k, p, clip, i):
    rw = [r for r in D["overlay"]["forms"][k]["rows"] if r["pattern"] == p and r["clip"] == clip][0]; a = ld(os.path.join(O5, D["overlay"]["forms"][k]["png"])); i %= rw["frames"]
    return a[rw["y"]:rw["y"] + rw["frameH"], i * rw["frameW"]:(i + 1) * rw["frameW"]], tuple(rw["pivot"])
def pet_pat(k, p, parent, clip="sit", i=0, W=64, Hh=60):
    f, piv, _ = U.strip_frame(k, clip, i); o, op = pat_frame(k, p, clip, i); hi, lo = B5.tint_pair(parent, k)
    c = np.zeros((Hh, W, 4), np.uint8); px, py = W // 2, Hh - 4
    put(c, f, px - piv[0], py - piv[1]); put(c, PT.colorize(o, hi, lo), px - op[0], py - op[1]); return c
def egg_pat(eid, p, parent, i=0):
    e = D["overlay"]["eggs"][eid]; rw = [r for r in e["rows"] if r["pattern"] == p][0]
    src = ld(os.path.join(ART, "sprites", rw["eggPng"]))[:, i * rw["frameW"]:(i + 1) * rw["frameW"]].copy()
    m = ld(os.path.join(O5, e["png"]))[rw["y"]:rw["y"] + rw["frameH"], i * rw["frameW"]:(i + 1) * rw["frameW"]]
    hi, lo, _ = PT.tint_for_parent(parent); put(src, PT.colorize(m, hi, lo), 0, 0); return src
def up(a, s=3): return Image.fromarray(a).resize((a.shape[1] * s, a.shape[0] * s), Image.NEAREST)
BG = (40, 34, 58, 255); F = LB.font

def egg_sheet():
    cw = 60; im = Image.new("RGBA", ((90 + 9 * cw) * 3, (40 + 3 * 60) * 3), BG); dr = ImageDraw.Draw(im)
    dr.text((10, 40 * 3 - 30), "冇花紋", fill=(220, 220, 240), font=F(24))
    for n, p in enumerate(PN): dr.text(((90 + (n + 1) * cw) * 3 + 6, 20), f"{PZ[p]}\n上一代 {PARENT[p]}", fill=(255, 240, 200), font=F(24))
    for r_, (eid, lab, fr) in enumerate((("egg_tr", "團絨蛋", 0), ("egg_kid", "細佬蛋", 0), ("egg_kid_crack", "細佬蛋（裂）", 2))):
        dr.text((10, (40 + r_ * 60 + 24) * 3), lab, fill=(220, 220, 240), font=F(28))
        e = D["overlay"]["eggs"][eid]; src = ld(os.path.join(ART, "sprites", e["rows"][0]["eggPng"]))[:, fr * e["rows"][0]["frameW"]:(fr + 1) * e["rows"][0]["frameW"]]
        s = 3 if eid == "egg_tr" else 2
        def cell(a, c):
            cc = np.zeros((56, 56, 4), np.uint8); bb = Image.fromarray(a).resize((a.shape[1] * s // 2 * 1, a.shape[0] * s // 2), Image.NEAREST) if False else None
            put(cc, a, 28 - a.shape[1] // 2, 54 - a.shape[0]); im.alpha_composite(up(cc), ((90 + c * cw) * 3, (40 + r_ * 60) * 3))
        cell(src, 0)
        for n, p in enumerate(PN): cell(egg_pat(eid, p, PARENT[p], fr), n + 1)
    im.save(os.path.join(PV, "inherit_eggs_3x.png"))

LINE = ["S1", "S2", "S4A", "A1", "A2", "A3"]
def forms_sheet(name, forms, parents=None, clip="sit"):
    cw, ch = 64, 60; im = Image.new("RGBA", ((90 + len(forms) * cw) * 3, (30 + len(PN) * ch) * 3), BG); dr = ImageDraw.Draw(im)
    for c, k in enumerate(forms): dr.text(((90 + c * cw) * 3 + 8, 12), k.replace("evo_still_", "靜光").replace("evo_guard_", "守護"), fill=(255, 240, 200), font=F(26))
    for r_, p in enumerate(PN):
        par = (parents or PARENT)[p]; dr.text((10, (30 + r_ * ch + 20) * 3), f"{PZ[p]}\n←{par.replace('evo_still_', '靜光')}", fill=(220, 220, 240), font=F(26))
        for c, k in enumerate(forms): im.alpha_composite(up(pet_pat(k, p, par, clip if k in LB.KID34 or clip != "idle" else "sit")), ((90 + c * cw) * 3, (30 + r_ * ch) * 3))
    im.save(os.path.join(PV, name))

def all59():
    per = 10; cw, ch = 64, 60; rows = (59 + per - 1) // per; im = Image.new("RGBA", (per * cw * 3, rows * (ch + 10) * 3), BG); dr = ImageDraw.Draw(im)
    for n, k in enumerate(LB.ALL59):
        p = PN[n % 8]; c = pet_pat(k, p, PARENT[p]); x, y = (n % per) * cw * 3, (n // per) * (ch + 10) * 3
        im.alpha_composite(up(c), (x, y + 30)); dr.text((x + 6, y + 4), f"{k.replace('evo_', '')}・{PZ[p]}", fill=(255, 240, 200), font=F(22))
    im.save(os.path.join(PV, "inherit_all59_3x.png"))

def gif():
    forms = [("S2", "wave", "A3"), ("A2", "crescent", "H3"), ("E1", "star", "evo_still_radiant"), ("evo_guard_moon", "bubble", "B3"), ("C3", "diamond", "G3")]
    fr = []
    for clip, n in (("idle", 4), ("walk", 8), ("sit", 6), ("interact", 8)):
        for rep in range(2 if clip == "idle" else 1):
            for i in range(n):
                row = np.zeros((70, 72 * len(forms), 4), np.uint8)
                for j, (k, p, par) in enumerate(forms):
                    cl = clip if (k in LB.KID34 or clip not in ("idle", "walk")) else "sit"
                    put(row, pet_pat(k, p, par, cl, i, 72, 70), j * 72, 0)
                im = Image.new("RGBA", (row.shape[1] * 3, row.shape[0] * 3 + 54), BG); im.alpha_composite(up(row), (0, 54))
                ImageDraw.Draw(im).text((12, 10), f"遺傳花紋跟住動：{clip}", fill=(255, 240, 200), font=F(30)); fr.append(im)
    LB.save_gif(fr, os.path.join(PV, "inherit_forms.gif"), 140)

if __name__ == "__main__":
    egg_sheet(); forms_sheet("inherit_growth_line_3x.png", LINE + ["S4C", "C1", "C3"])
    forms_sheet("inherit_tuanrong_3x.png", ["sprout", "evo_dot", "evo_hop", "evo_guard_tide", "evo_guard_ember", "evo_still_soft", "evo_still_crystal"])
    all59(); gif(); print("ok")
