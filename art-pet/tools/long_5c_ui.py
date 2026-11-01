# 《微光小圃》5c UI（HD-2D）：揀上一代、遺傳預覽／孵化結果、族譜（沿用 5a）
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import long_5abc_ui as U
import long_5abc_lib as LB
import long_5a_ui as A5
import long_5c_patterns as PT
import long_5c_build as B5
from series2_lib import ART
H = U.H; P = U.P; C = U.C; hx = U.hx
O5 = os.path.join(LB.OUTL, "5c"); UO = os.path.join(O5, "ui"); PV = os.path.join(O5, "preview")
D = json.load(open(os.path.join(O5, "long_5c.json"))); PZ = {p["id"]: p["zh"] for p in D["patterns"]}
LS = A5.LS

L = {"style": "HD-2D；零件 3x", "assets": {},
 "parentPick": {"when": "揀蛋（5a 二揀一）之後即刻出；屋內冇成年＝跳過（冇遺傳）", "panel": {"x": 10, "y": 60, "w": 175, "h": 300}, "plaque": {"y": 52, "w": 104, "label": "揀上一代"},
   "egg": {"cx": 30, "cy": 92}, "sub": {"x": 50, "y": 86, "text": "邊隻做 BB 嘅上一代？"},
   "cards": {"x": [18, 101], "y0": 112, "dy": 60, "w": 76, "h": 54, "portrait": {"dx": 19, "dy": 25, "d": 30}, "name": {"dx": 36, "dy": 12},
             "swatch": {"dx": 41, "dy": 30, "d": 11}, "trick": {"dx": 55, "dy": 30, "d": 11}, "tag": {"dx": 36, "dy": 44}},
   "preview": {"x": 18, "y": 296, "w": 159, "h": 30, "note": "會遺傳：花紋 swatch＋名、招式道具＋名、（家族 Lv3＋細佬蛋）快 20% pill"},
   "btn": {"x": 57, "y": 332, "w": 81, "h": 18, "label": "就佢喇！"}, "rule": "揀咗嘅卡＝金光；主養都可以揀；遠足中都可以揀（唔使喺屋）"},
 "inheritResult": {"rays": {"cx": 97.5, "cy": 150}, "pet": {"cx": 97.5, "cy": 168, "scale": 4}, "plaque": {"y": 86, "w": 104, "label": "遺傳咗！"},
   "rows": {"x": 26, "y": [206, 232], "w": 143, "h": 22}, "fast": {"y": 262}, "btn": {"x": 57, "y": 290, "w": 81, "h": 18, "label": "好可愛！"},
   "anim": "蛋裂 → 白光 → 新 BB 出（花紋由底向上 300ms 掃入）→ 兩行逐行彈出 120ms 間隔"}}

def save(im, name):
    p = f"ui/{name}@3x.png"; U.x3(U.crop(im)).save(os.path.join(O5, p)); L["assets"][name] = p; return p

def trick_of(k):
    lp = A5.lesson_prop(k)
    if lp: return lp
    s = {"moon": "H", "tide": "A", "radiant": "F", "soft": "B", "crystal": "G", "ember": "C", "shroom": "D", "dust": "E", "lumi": "F"}.get(PT.series_of(k), "A")
    p = LS["propsBySeries"][s]; a = np.asarray(Image.open(os.path.join(ART, "sprites/series2", p["png"])).convert("RGBA"))[:, :p["frameW"]]
    ys, xs = np.nonzero(a[..., 3]); return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1], p["zh"], LS["copy"][s]["title"].replace("照抄：", "")
def prop_chip(b, cx, cy, arr, d=11):
    dd = ImageDraw.Draw(b); dd.ellipse([P(cx - d / 2), P(cy - d / 2), P(cx + d / 2), P(cy + d / 2)], fill=C['paper'][1], outline=C['line'], width=P(.5))
    U.paste_px(b, arr, P(cx), P(cy), 1.0 if max(arr.shape[:2]) <= 9 else .6667)

PARENTS = [("A3", "滴滴"), ("evo_still_moon", "月月"), ("F3", "星仔"), ("H2", "夜夜"), ("evo_still_soft", "棉棉"), ("C3", "火火")]
def parent_card(b, x, y, k, nm, sel=False, dim=False):
    c = L["parentPick"]["cards"]; w, h = c["w"], c["h"]
    H.place(b, H.frame(w, h, 7, C['navy_in'], glow=1.4 if sel else .5, ornate=False, rim=1.0), P(x), P(y))
    if sel: ImageDraw.Draw(b).rounded_rectangle([P(x - 1.3), P(y - 1.3), P(x + w + 1.3), P(y + h + 1.3)], radius=P(8), outline=C['g_hi'], width=P(.9))
    U.portrait(b, k, P(x + 19), P(y + 25), 30, dark=dim)
    H.gold_text(b, (P(x + 36), P(y + 11)), nm, 7.0, 'serif', anchor='lm', glow=.3)
    pat = PT.pattern_for_parent(k); hi, lo, _ = PT.tint_for_parent(k)
    A5.swatch(b, P(x + 41), P(y + 29), pat, hi, lo); prop_chip(b, x + 55, y + 29, trick_of(k)[0])
    H.text(b, (P(x + 36), P(y + 44)), f"{PZ[pat]}・{trick_of(k)[1]}", 5.0, hx('#FFE6A8'), 'sans', anchor='lm', stroke=.5)
    H.text(b, (P(x + 36), P(y + 50)), A5.tag_of(k), 4.6, hx('#C9D0F0'), 'sans', anchor='lm', stroke=.5) if False else None
def preview_bar(b, k, egg="kid", lv=4, y=296):
    pat = PT.pattern_for_parent(k); hi, lo, _ = PT.tint_for_parent(k); tp = trick_of(k)
    H.place(b, H.frame(159, 30, 7, C['navy'], glow=.7, ornate=False, rim=1.0), P(18), P(y))
    H.text(b, (P(24), P(y + 8)), "會遺傳", 5.6, hx('#C9D0F0'), 'sans', anchor='lm', stroke=.6)
    A5.swatch(b, P(30), P(y + 19), pat, hi, lo, 10); H.text(b, (P(37), P(y + 19)), PZ[pat] + "花紋", 6.0, C['cream'], 'serif', anchor='lm', stroke=.7)
    prop_chip(b, 74, y + 19, tp[0], 10); H.text(b, (P(81), P(y + 19)), tp[2].split("→")[0].strip()[:5], 6.0, C['cream'], 'serif', anchor='lm', stroke=.7)
    fast = egg == "kid" and lv >= 3
    U.pill(b, 122, y + 12.5, 50, 13, 'sec' if fast else 'dis', "成長快 20%" if fast else ("團絨蛋唔加速" if egg == "tr" else "家族 Lv3 開"), "fast", 5.2)
def mock_pick(egg="kid", sel=0, lv=4):
    bg = U.dim(A5.mock_room("room2"), .6); b = U.board(); c = L["parentPick"]; pn = c["panel"]
    U.panel(b, pn["x"], pn["y"], pn["w"], pn["h"], 11, ornate=True); H.plaque(b, 97.5, 52, 104, "揀上一代")
    U.glow_spot(b, P(30), P(92), 12, C['cyan'], .6); U.paste_px(b, A5.egg_img("tr" if egg == "tr" else "kid"), P(30), P(102), 1.0 if egg == "tr" else .6667, anchor='b')
    H.text(b, (P(52), P(88)), "邊隻做 BB 嘅上一代？", 6.6, C['cream'], 'serif', anchor='lm', stroke=.8)
    H.text(b, (P(52), P(99)), "佢嘅花紋同招式會傳落去", 5.4, hx('#C9D0F0'), 'sans', anchor='lm', stroke=.6)
    for n, (k, nm) in enumerate(PARENTS): parent_card(b, c["cards"]["x"][n % 2], 112 + (n // 2) * 60, k, nm, sel=n == sel)
    preview_bar(b, PARENTS[sel][0], egg, lv); H.button(b, 57, 332, 81, 18, 'pri', "就佢喇！"); bg.alpha_composite(b); return bg

def born_px(child, parent, clip=None):
    clip = clip or ("idle" if child in LB.KID34 else "sit")
    f, piv, _ = U.strip_frame(child, clip, 0)
    rw = [r for r in D["overlay"]["forms"][child]["rows"] if r["pattern"] == PT.pattern_for_parent(parent) and r["clip"] == clip][0]
    a = np.asarray(Image.open(os.path.join(O5, D["overlay"]["forms"][child]["png"])).convert("RGBA"))[rw["y"]:rw["y"] + rw["frameH"], :rw["frameW"]]
    hi, lo = B5.tint_pair(parent, child); o = PT.colorize(a, hi, lo); out = f.copy(); m = o[..., 3] > 0; out[m] = o[m]
    ys, xs = np.nonzero(out[..., 3]); return out[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
def mock_result(child="S1", parent="A3", egg="kid", lv=4, name="BB"):
    bg = U.dim(A5.mock_room("room2"), .66); b = U.board(); A5.rays(b, 97.5, 150, 80); U.glow_spot(b, P(97.5), P(150), 32, a=.9)
    H.plaque(b, 97.5, 86, 104, "遺傳咗！"); U.paste_px(b, born_px(child, parent), P(97.5), P(184), 2.0, anchor='b')
    H.gold_text(b, (P(97.5), P(194)), f"{name}（第 4 代）", 8.0, 'serif', glow=.5)
    pat = PT.pattern_for_parent(parent); hi, lo, _ = PT.tint_for_parent(parent); tp = trick_of(parent)
    for i, (y, draw, t1, t2) in enumerate(((206, "sw", PZ[pat] + "花紋", f"上一代 {dict(PARENTS).get(parent, parent)} 嘅色"), (232, "tr", "家傳招式", tp[2]))):
        H.place(b, H.frame(143, 22, 6, C['navy_in'], glow=.5, ornate=False, rim=.9), P(26), P(y))
        if draw == "sw": A5.swatch(b, P(38), P(y + 11), pat, hi, lo, 13)
        else: prop_chip(b, 38, y + 11, tp[0], 13)
        H.gold_text(b, (P(50), P(y + 7.5)), t1, 6.6, 'serif', anchor='lm', glow=.2); H.text(b, (P(50), P(y + 16)), t2, 5.2, hx('#C9D0F0'), 'sans', anchor='lm', stroke=.6)
    fast = egg == "kid" and lv >= 3
    U.pill(b, 52, 258, 91, 14, 'sec' if fast else 'dis', "頭 2 階成長快 20%" if fast else "團絨蛋：唔加速", "fast", 5.8)
    H.button(b, 57, 290, 81, 18, 'pri', "好可愛！"); bg.alpha_composite(b); return bg

def components():
    for k, nm in PARENTS[:2]:
        b = U.board(84, 62); parent_card(b, 4, 4, k, nm, sel=k == "A3"); save(b, f"parent_card_{k}")
    for p, _ in PT.PATTERNS:
        for k in ("A3",):
            pass
    for kk in ("inherit", "trick", "pattern", "fast"):
        b = U.board(30, 30); U.medal(b, P(15), P(15), 24, C['navy'], kk, 19); save(b, f"icon_{kk}")
    for s, pr in LS["propsBySeries"].items():
        b = U.board(16, 16); k = f"{s}3"; prop_chip(b, 8, 8, A5.lesson_prop(k)[0], 13); save(b, f"chip_trick_{s}")
    for p, _ in PT.PATTERNS:
        par = {v: f"{k_}3" for k_, v in PT.BY_SERIES.items()}[p]; hi, lo, _ = PT.tint_for_parent(par)
        b = U.board(18, 18); A5.swatch(b, P(9), P(9), p, hi, lo, 13); save(b, f"swatch_{p}_{par}")
    b = U.board(195, 40); preview_bar(b, "A3", y=4); save(b, "inherit_preview_bar")
    for egg, lv in (("kid", 4), ("tr", 4), ("kid", 2)):
        b = U.board(60, 20); fast = egg == "kid" and lv >= 3
        U.pill(b, 3, 3, 52, 13, 'sec' if fast else 'dis', "成長快 20%" if fast else ("團絨蛋唔加速" if egg == "tr" else "家族 Lv3 開"), "fast", 5.2); save(b, f"pill_fast_{'on' if fast else ('tr' if egg == 'tr' else 'locked')}")

def main():
    os.makedirs(UO, exist_ok=True); os.makedirs(PV, exist_ok=True); components()
    ims = {"parent_pick": mock_pick("kid", 0, 4), "parent_pick_tr_egg": mock_pick("tr", 3, 4), "inherit_result_S1": mock_result("S1", "A3"),
           "inherit_result_tr": mock_result("sprout", "H2", "tr", 4, "光仔"), "family_tree_ref": None}
    out = {}
    for n, im in ims.items():
        if im is None: continue
        U.x3(im).convert('RGB').save(os.path.join(PV, n + "_HD2D_3x.png")); out[n] = U.x3(im)
    tree = Image.open(os.path.join(LB.OUTL, "5a/preview/family_tree_HD2D_3x.png")).convert("RGBA")
    U.strip_sheet([out["parent_pick"], out["parent_pick_tr_egg"], out["inherit_result_S1"], out["inherit_result_tr"], tree],
                  ["揀上一代（細佬蛋）", "揀上一代（團絨蛋）", "遺傳咗！（細佬 S1）", "遺傳咗！（團絨 sprout）", "族譜（5a，顯示代／系／上一代／教錯咗乜）"], os.path.join(PV, "ui_5c_sheet_HD2D_3x.png"))
    U.parts_sheet(list(L["assets"].values()), os.path.join(PV, "ui_parts_5c_HD2D_3x.png"), O5)
    LB.jdump(L, os.path.join(UO, "layout.json")); print("ui 5c ok", len(L["assets"]))
if __name__ == "__main__": main()
