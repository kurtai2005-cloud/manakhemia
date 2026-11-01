#!/usr/bin/env python3
"""build_from_ref_px48_out — tuned_48 → 引擎交付＋檢查圖：
atlas/pets_idle_48.png＋json、bulb_anchors_48.json、idle/*_idle_3x.gif、
lineup_48_6x.png、before_after_80_vs_48.png、crack_check_8x.png、blink_check_6x.png、scene_old_vs_new.png、crack_report.json。
純 Pillow／numpy。用法：python3 build_from_ref_px48_out.py（先跑 build_from_ref_px48.py）"""
import os, sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); ART = os.path.dirname(HERE)
import px48_check as CK
FR = os.path.join(ART, "sprites/tuanrong/species_concept/from_ref"); D = os.path.join(FR, "tuned_48"); D80 = os.path.join(FR, "tuned_80")
EVO = os.path.join(ART, "sprites/tuanrong/evo6"); SCN = os.path.join(FR, "feeltest/assets/scenes")
S = 48; BG = (92, 84, 136)
FB = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"; FRg = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
def font(n, b=True): return ImageFont.truetype(FB if b else FRg, n)
def rgba(p): return Image.open(p).convert("RGBA")
def zoom(im, z): return im.resize((im.width * z, im.height * z), Image.NEAREST)
def on_bg(im, bg=BG):
    b = Image.new("RGBA", im.size, (*bg, 255)); b.alpha_composite(im); return b

def engine(T):
    C = T["creatures"]; keys = list(C); piv = T["pivot"]; dur = T["idle"]["durationsMs"]; C80 = json.load(open(os.path.join(D80, "tuned.json")))["creatures"]
    os.makedirs(os.path.join(D, "atlas"), exist_ok=True)
    atlas = Image.new("RGBA", (4 * S, len(keys) * S), (0, 0, 0, 0)); frames = {}; anims = {}; bulbs = {}
    for r, k in enumerate(keys):
        st = rgba(os.path.join(D, "idle", f"{k}_idle.png")); atlas.paste(st, (0, r * S)); names = []
        for f in range(4):
            n = f"{k}_idle_{f}"; names.append(n)
            frames[n] = {"frame": {"x": f * S, "y": r * S, "w": S, "h": S}, "pivot": {"x": piv[0], "y": piv[1]}, "pivotNorm": {"x": piv[0] / S, "y": round(piv[1] / S, 4)}, "durationMs": dur[f]}
        anims[f"{k}_idle"] = names
        cut = C[k]["idleCut"]; bx, by = C[k]["bulbXY"]
        per = [[bx, by], [bx, by + (1 if by <= cut else 0)], [bx, by], [bx, by]]
        kind = {"own": "own", "star": "star"}.get(C[k]["bulbType"], "bulb")
        bulbs[k] = {"name": C[k]["name"], "anchor": [bx, by], "perFrame": per, "fromFoot": [bx - piv[0], by - piv[1]], "type": kind, "glowTint": C80[k]["glowTint"]}
        # 3x gif 預覽
        fr = [on_bg(zoom(st.crop((i * S, 0, (i + 1) * S, S)), 3)).convert("P", palette=Image.ADAPTIVE) for i in range(4)]
        fr[0].save(os.path.join(D, "idle", f"{k}_idle_3x.gif"), save_all=True, append_images=fr[1:], duration=dur, loop=0)
    atlas.save(os.path.join(D, "atlas", "pets_idle_48.png"), optimize=True)
    json.dump({"meta": {"image": "pets_idle_48.png", "size": {"w": atlas.width, "h": atlas.height}, "format": "RGBA8888", "frameSize": S,
                        "pivot": piv, "pivotRule": "bottom-centre (w/2, h-3)＝(24,45)，同舊 evo6 evo_still_* atlas pivotPx 一樣；腳最底一行 y=46", "filter": "nearest",
                        "alpha": "0/255 only", "layout": "每行一隻（A1..H3），4 欄＝idle 幀 0..3"},
               "frames": frames, "animations": anims}, open(os.path.join(D, "atlas", "pets_idle_48.json"), "w"), ensure_ascii=False, indent=1)
    json.dump({"size": S, "pivot": piv, "coord": "sprite 左上角 (0,0)、px；fromFoot＝相對 pivot", "glowRadiusPx": 9,
               "creatures": bulbs}, open(os.path.join(D, "bulb_anchors_48.json"), "w"), ensure_ascii=False, indent=1)
    return bulbs

def lineup(T):
    C = T["creatures"]; keys = list(C); z = 6; cw = S * z; lh = 34
    im = Image.new("RGBA", (6 * cw, 4 * (cw + lh) + 50), (*BG, 255)); dr = ImageDraw.Draw(im)
    dr.text((10, 8), "tuned_48（舊寵尺寸：48×48、pivot (24,45)）×6　每行：一線三階（細→大）", font=font(26), fill=(255, 255, 255))
    for i, k in enumerate(keys):
        x = (i % 6) * cw; y = 50 + (i // 6) * (cw + lh)
        im.alpha_composite(zoom(rgba(os.path.join(D, "sprites", f"{k}_48.png")), z), (x, y))
        dr.text((x + 8, y + cw + 2), f"{k} {C[k]['name']}　{C[k]['mass']}px", font=font(22, False), fill=(235, 235, 245))
    im.save(os.path.join(D, "lineup_48_6x.png"))

def naive80(k):
    a = rgba(os.path.join(D80, "sprites", f"{k}_80.png")).resize((S, S), Image.NEAREST)
    return a
def before_after(T):
    C = T["creatures"]; keys = list(C); z = 4; cw = S * z; pad = 14; lh = 52
    W = 4 * (2 * cw + pad) ; H = 6 * (cw + lh) + 70
    im = Image.new("RGBA", (W, H), (*BG, 255)); dr = ImageDraw.Draw(im)
    dr.text((10, 8), "左：80px 直接縮落 48（nearest）　右：新 tuned_48（像素清理）　×4", font=font(26), fill=(255, 255, 255))
    dr.text((10, 40), "細字＝自動 crack 檢查：雜點／外框斷口／洞 嘅像素數", font=font(18, False), fill=(220, 220, 235))
    rep = {}
    for i, k in enumerate(keys):
        x = (i % 4) * (2 * cw + pad); y = 70 + (i // 4) * (cw + lh)
        nv = naive80(k); new = rgba(os.path.join(D, "sprites", f"{k}_48.png"))
        rn = CK.check(np.array(nv).astype(int), {"eyes": [], "bulbXY": [200, 200], "outline": "#202020"})
        r2 = CK.check(np.array(new).astype(int), C[k])
        im.alpha_composite(zoom(nv, z), (x, y)); im.alpha_composite(zoom(new, z), (x + cw, y))
        dr.line([(x + cw, y + 4), (x + cw, y + cw - 4)], fill=(150, 140, 190), width=1)
        f = lambda r: f"{len(r['speck'])}/{len(r['gap'])}/{len(r['hole'])}"
        dr.text((x + 6, y + cw + 2), f"{k}  80縮 {f(rn)}  →  48 {f(r2)}", font=font(19, False), fill=(240, 240, 250))
        rep[k] = {"naive80to48": {a: len(b) for a, b in rn.items()}, "tuned48": {a: len(b) for a, b in r2.items()}}
    im.save(os.path.join(D, "before_after_80_vs_48_4x.png")); return rep

def crack_sheet(T):
    C = T["creatures"]; keys = list(C); z = 8; cw = S * z; lh = 30
    im = Image.new("RGBA", (6 * cw, 4 * (cw + lh) + 60), (*BG, 255)); dr = ImageDraw.Draw(im)
    dr.text((10, 8), "crack 檢查 ×8（格線＝1px）：紅框＝單點雜色、橙框＝外框斷口、青框＝身體內細洞；黃線＝刻意熔岩脈", font=font(24), fill=(255, 255, 255))
    tot = {}
    for i, k in enumerate(keys):
        x0 = (i % 6) * cw; y0 = 60 + (i // 6) * (cw + lh)
        sp = rgba(os.path.join(D, "sprites", f"{k}_48.png")); im.alpha_composite(zoom(sp, z), (x0, y0))
        for g in range(S + 1):
            dr.line([(x0 + g * z, y0), (x0 + g * z, y0 + cw)], fill=(0, 0, 0, 40)); dr.line([(x0, y0 + g * z), (x0 + cw, y0 + g * z)], fill=(0, 0, 0, 40))
        r = CK.check(np.array(sp).astype(int), C[k]); tot[k] = {a: len(b) for a, b in r.items()}
        for kind, colr in (("speck", (255, 40, 40)), ("gap", (255, 150, 0)), ("hole", (0, 230, 255))):
            for (y, x) in r[kind]: dr.rectangle([x0 + x * z, y0 + y * z, x0 + x * z + z - 1, y0 + y * z + z - 1], outline=colr, width=2)
        for vx, vy in C[k].get("veinPx", []): dr.line([(x0 + vx * z + 2, y0 + vy * z + z - 2), (x0 + vx * z + z - 2, y0 + vy * z + z - 2)], fill=(255, 255, 0), width=1)
        dr.rectangle([x0, y0, x0 + cw - 1, y0 + cw - 1], outline=(60, 54, 96))
        dr.text((x0 + 6, y0 + cw + 2), f"{k}  雜點 {tot[k]['speck']}  斷口 {tot[k]['gap']}  洞 {tot[k]['hole']}", font=font(19, False), fill=(240, 240, 250))
    im.save(os.path.join(D, "crack_check_8x.png")); return tot

def blink_sheet(T):
    C = T["creatures"]; keys = list(C); z = 6; cw = S * z; lh = 30
    im = Image.new("RGBA", (4 * (2 * cw + 10), 6 * (cw // 2 + lh) + 50), (*BG, 255)); dr = ImageDraw.Draw(im)
    dr.text((10, 8), "眨眼檢查 ×6：左＝幀 0、右＝幀 3（眨眼）；只顯示上半到腳", font=font(24), fill=(255, 255, 255))
    for i, k in enumerate(keys):
        st = rgba(os.path.join(D, "idle", f"{k}_idle.png")); ey = min(e["y"] for e in C[k]["eyes"]) if C[k]["eyes"] else 24
        top = max(0, min(S - 24, ey - 10))
        x = (i % 4) * (2 * cw + 10); y = 50 + (i // 4) * (cw // 2 + lh)
        for f, dx in ((0, 0), (3, cw)):
            im.alpha_composite(zoom(st.crop((f * S, top, (f + 1) * S, top + 24)), z), (x + dx, y))
        dr.text((x + 6, y + cw // 2 + 2), f"{k} {C[k]['name']}  眼：{'／'.join(e['kind'] for e in C[k]['eyes'])}", font=font(18, False), fill=(240, 240, 250))
    im.save(os.path.join(D, "blink_check_6x.png"))

def scene(h, pets):
    """pets: [(RGBA img, (px,py), footx)]；返 195×422 art grid"""
    L = {n: rgba(os.path.join(SCN, h, f"{n}.png")) for n in ("sky", "far", "mid", "fore")}
    c = Image.new("RGBA", (195, 422), (0, 0, 0, 255))
    for n in ("sky", "far", "mid"): c.alpha_composite(L[n].crop((14, 12, 14 + 195, 12 + 422)))
    for img, (px, py), fx, shw in pets:
        sh = Image.new("RGBA", c.size, (0, 0, 0, 0)); d = ImageDraw.Draw(sh)
        for dy in range(-3, 4):
            w = int(round(shw * (1 - dy * dy / 16) ** 0.5)); d.rectangle([fx - w, 292 - 1 + dy, fx + w - 1, 292 - 1 + dy], fill=(10, 20, 20, 90))
        c.alpha_composite(sh); c.alpha_composite(img, (fx - px, 292 - py))
    c.alpha_composite(L["fore"].crop((14, 12, 14 + 195, 12 + 422)))
    return c
def scene_compare():
    old = lambda f: rgba(os.path.join(EVO, f, "frames", "idle_01.png"))
    new = lambda k: rgba(os.path.join(D, "sprites", f"{k}_48.png"))
    P = [("H1", "成年：舊 evo_guard_ember 44 vs 新 C2", [(old("evo_guard_ember"), (22, 41), 66, 16), (new("C2"), (24, 45), 130, 17)]),
         ("H3", "跳跳期：舊 evo_hop 38 vs 新 A1", [(old("evo_hop"), (19, 35), 66, 14), (new("A1"), (24, 45), 130, 15)]),
         ("H4", "最終：舊 evo_still_moon 48 vs 新 G3", [(old("evo_still_moon"), (24, 45), 66, 17), (new("G3"), (24, 45), 130, 18)]),
         ("H2", "對照：而家 APK 80px C2 vs 新 48 C2", [(rgba(os.path.join(D80, "sprites", "C2_80.png")), (40, 77), 60, 21), (new("C2"), (24, 45), 140, 17)])]
    z = 2; zz = 4; cw = 195 * z; crop = (20, 200, 175, 306); cwz = (crop[2] - crop[0]) * zz // 2
    W = len(P) * (cw + 12); H = 60 + 422 * z + 50 + (crop[3] - crop[1]) * zz // 2 * 2 + 40
    im = Image.new("RGBA", (W, H), (24, 22, 36, 255)); dr = ImageDraw.Draw(im)
    dr.text((10, 10), "場景對比（同一腳點 y=292、同一 pivot 規則；左＝舊寵、右＝新寵）　上：全畫面 ×2　下：寵物區 ×4", font=font(24), fill=(255, 255, 255))
    for i, (h, t, pets) in enumerate(P):
        c = scene(h, pets); x = i * (cw + 12)
        im.alpha_composite(zoom(c, z), (x, 60))
        dr.text((x + 4, 60 + 422 * z + 6), f"{h}｜{t}", font=font(18), fill=(240, 240, 250))
        cz = zoom(c.crop(crop), 2)
        cz = cz.resize((cz.width * 2 // 2 * 1, cz.height), Image.NEAREST)
        im.alpha_composite(zoom(c.crop(crop), 2), (x, 60 + 422 * z + 40))
    im.save(os.path.join(D, "scene_old_vs_new.png"))
    # 寵物區大圖 ×4（2×2）
    big = Image.new("RGBA", (2 * (crop[2] - crop[0]) * zz + 10, 2 * ((crop[3] - crop[1]) * zz + 36) + 50), (24, 22, 36, 255)); db = ImageDraw.Draw(big)
    db.text((10, 8), "寵物區 ×4（左＝舊、右＝新；腳點 y=292）", font=font(24), fill=(255, 255, 255))
    for i, (h, t, pets) in enumerate(P):
        c = scene(h, pets); x = (i % 2) * ((crop[2] - crop[0]) * zz + 10); y = 50 + (i // 2) * ((crop[3] - crop[1]) * zz + 36)
        big.alpha_composite(zoom(c.crop(crop), zz), (x, y)); db.text((x + 6, y + (crop[3] - crop[1]) * zz + 4), f"{h}｜{t}", font=font(20), fill=(240, 240, 250))
    big.save(os.path.join(D, "scene_old_vs_new_petarea_4x.png"))

def main():
    T = json.load(open(os.path.join(D, "tuned.json")))
    b = engine(T); lineup(T); rep = before_after(T); tot = crack_sheet(T); blink_sheet(T); scene_compare()
    json.dump({"note": "自動 crack 檢查（px48_check.py）：speck＝8 鄰全部色差 >90 嘅單點；gap＝外框位唔夠深；hole＝身體內 ≤6px 透明洞；frag＝6–11px 獨立碎件（9px 泡泡除外）",
               "compare": rep}, open(os.path.join(D, "crack_report.json"), "w"), ensure_ascii=False, indent=1)
    print("out ok", sum(v["speck"] + v["gap"] + v["hole"] for v in tot.values()), "issues in 48;", sum(v["naive80to48"]["speck"] + v["naive80to48"]["gap"] + v["naive80to48"]["hole"] for v in rep.values()), "in naive")
if __name__ == "__main__": main()
