#!/usr/bin/env python3
"""build_from_ref_sizecompare — 64／80／96 尺寸比較（《微光小圃》HD-2D H1，195×422，腳點 (97,292)）。
用 headless Chrome 影 feeltest（?size=）→ 3 欄（64/80/96）× 3 行（A1 一階細、C2 二階、B3 三階大）@3x，
疊頂部 UI ~52px／底部 UI ~100px 參考帶＋寵物 bbox＋淨空數字；另抄每個尺寸嘅 lineup。純 Pillow，冇 AI 圖。
用法：python3 build_from_ref_sizecompare.py [--noshot]"""
import os, sys, json, shutil, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ART = os.path.dirname(HERE)
FR = os.path.join(ART, "sprites/tuanrong/species_concept/from_ref"); FT = os.path.join(FR, "feeltest"); OUT = os.path.join(FR, "size_compare")
SIZES = (64, 80, 96); PETS = ("A1", "C2", "B3"); SCENE = "H1"; T = 0.5; Z = 3
AW, AH = 195, 422; FOOT = (97, 292); TOP_UI = 52; BOT_UI = AH - 100
FB = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"; FRg = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
def font(p, s):
    try: return ImageFont.truetype(p, s)
    except Exception: return ImageFont.load_default()
def tdir(S): return os.path.join(FR, "tuned" if S == 64 else f"tuned_{S}")
def shot(p, S, dst):
    url = f"file://{FT}/index.html?pet={p}&scene={SCENE}&size={S}&t={T}&ui=0&hint=0"
    for _ in range(4):   # headless 間中影到未 decode 完嘅黑畫面 → 重試
      subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                    f"--window-size={AW*Z},{AH*Z}", "--virtual-time-budget=3000", f"--screenshot={dst}", url], check=True, capture_output=True)
      if np.asarray(Image.open(dst).convert("L")).mean() > 40: return
    raise RuntimeError("screenshot blank: " + dst)
def bbox(p, S):
    """寵物喺畫面嘅 bbox（art px）：同 index.html 一樣計 sway（t=0.5 → mid 視差 mx）"""
    import math
    piv = json.load(open(os.path.join(tdir(S), "tuned.json")))["pivot"]
    a = np.array(Image.open(os.path.join(tdir(S), "sprites", f"{p}_{S}.png")))[:, :, 3] > 0; ys, xs = np.nonzero(a)
    mx = round(-14 + math.sin(T * 0.35) * 5) + 14; px, py = FOOT[0] - piv[0] + mx, FOOT[1] - piv[1]
    return px + xs.min(), py + ys.min(), px + xs.max(), py + ys.max()
def main():
    os.makedirs(os.path.join(OUT, "shots"), exist_ok=True)
    W, H = AW * Z, AH * Z; G = 30; HEAD = 150; ROWL = 0; FOOTH = 70
    f1, f2, f3 = font(FB, 64), font(FRg, 26), font(FB, 30)
    sheet = Image.new("RGB", (G + len(SIZES) * (W + G), HEAD + len(PETS) * (H + FOOTH + G)), (22, 18, 34)); d = ImageDraw.Draw(sheet)
    rows = []
    for c, S in enumerate(SIZES):
        x0 = G + c * (W + G); d.text((x0 + W // 2, 52), f"{S}px", fill=(255, 236, 190), font=f1, anchor="mm")
        d.text((x0 + W // 2, 112), {64: "現行", 80: "×1.25", 96: "×1.5"}[S], fill=(200, 190, 230), font=f2, anchor="mm")
    for r, p in enumerate(PETS):
        for c, S in enumerate(SIZES):
            fp = os.path.join(OUT, "shots", f"{p}_{S}.png")
            if "--noshot" not in sys.argv or not os.path.exists(fp) or np.asarray(Image.open(fp).convert("L")).mean() <= 40: shot(p, S, fp)
            im = Image.open(fp).convert("RGBA").crop((0, 0, W, H))
            ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); o = ImageDraw.Draw(ov)
            o.rectangle((0, 0, W, TOP_UI * Z), fill=(255, 70, 90, 70)); o.rectangle((0, BOT_UI * Z, W, H), fill=(255, 70, 90, 70))
            for xx in range(0, W, 18):
                o.line((xx, TOP_UI * Z, xx + 9, TOP_UI * Z), fill=(255, 120, 140, 230), width=3); o.line((xx, BOT_UI * Z, xx + 9, BOT_UI * Z), fill=(255, 120, 140, 230), width=3)
            o.text((10, TOP_UI * Z - 36), "頂部 UI ~52", fill=(255, 220, 225, 255), font=f2)
            o.text((10, BOT_UI * Z + 8), "底部 UI ~100", fill=(255, 220, 225, 255), font=f2)
            bx0, by0, bx1, by1 = bbox(p, S)
            o.rectangle((bx0 * Z - 2, by0 * Z - 2, (bx1 + 1) * Z + 1, (by1 + 1) * Z + 1), outline=(120, 240, 255, 220), width=2)
            im = Image.alpha_composite(im, ov); x0 = G + c * (W + G); y0 = HEAD + r * (H + FOOTH + G)
            sheet.paste(im.convert("RGB"), (x0, y0))
            top, bot, wid = by0 - TOP_UI, BOT_UI - (by1 + 1), (bx1 - bx0 + 1)
            ok = top >= 8 and bot >= 8
            d.text((x0 + W // 2, y0 + H + 34), f"{p} · 頂淨空 {top}px · 底淨空 {bot}px · 闊 {wid}px（{wid*100//AW}%）",
                   fill=(170, 240, 190) if ok else (255, 150, 150), font=f2, anchor="mm")
            rows.append({"pet": p, "size": S, "bbox": [int(bx0), int(by0), int(bx1), int(by1)], "topClear": int(top), "bottomClear": int(bot), "width": int(wid), "ok": bool(ok)})
    sheet.save(os.path.join(OUT, "size_compare_3x.png"), optimize=True)
    sheet.resize((sheet.width // 3, sheet.height // 3), Image.LANCZOS).save(os.path.join(OUT, "size_compare_preview.png"))
    for S in SIZES: shutil.copy(os.path.join(tdir(S), "lineup_4x.png"), os.path.join(OUT, f"lineup_{S}_4x.png"))
    json.dump({"scene": SCENE, "t": T, "art": [AW, AH], "foot": FOOT, "topUI": TOP_UI, "bottomUI": 100, "rows": rows},
              open(os.path.join(OUT, "size_compare.json"), "w"), ensure_ascii=False, indent=1)
    for q in rows: print(q)
if __name__ == "__main__": main()
