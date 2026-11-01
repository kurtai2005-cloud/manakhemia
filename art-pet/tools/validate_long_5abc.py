# 《微光小圃》5a–5c 長線養成 validator：cd art-pet && python3 tools/validate_long_5abc.py [5a|5b|5c ...]
import json, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from series2_lib import ART
import long_5abc_lib as LB
D = LB.OUTL; ERR = []; N = {"png": 0, "json": 0}; INFO = []
def err(m): ERR.append(m)
def png(p):
    a = np.asarray(Image.open(os.path.join(D, p)).convert("RGBA")); N["png"] += 1; return a
def ncol(a): m = a[..., 3] > 0; return len(np.unique(a[m][:, :3].reshape(-1, 3), axis=0)) if m.any() else 0
def binary(a, p):
    if not set(np.unique(a[..., 3])) <= {0, 255}: err(f"{p}: alpha 唔係 0/255")
def js(p): N["json"] += 1; return json.load(open(os.path.join(D, p)))
def exists(p):
    if not os.path.exists(os.path.join(D, p)): err(f"缺 {p}"); return False
    return True
NEWF = LB.NEWF

def strip_ok(p, fw, fh, frames, tag, limit12):
    a = png(p); binary(a, p)
    if a.shape[:2] != (fh, fw * frames): err(f"{p} size {a.shape[1]}×{a.shape[0]} ≠ {fw * frames}×{fh}"); return a
    for i in range(frames):
        fr = a[:, i * fw:(i + 1) * fw]
        if not fr[..., 3].any(): err(f"{p} 第{i}格空")
        if limit12 and ncol(fr) > 12: err(f"{p} 第{i}格 {ncol(fr)} 色 >12")
    return a

def v5a():
    J = js("5a/long_5a.json"); fl = J["familyLevel"]; t = fl["thresholds"]
    if t != [0, 60, 150, 270, 420, 600, 810, 1050, 1320, 1620]: err("家族等級門檻同 spec 唔一樣")
    if fl["xp"] != {"raise_one": 50, "dex_new_form": 10, "furniture_new": 5, "expedition_return": 3}: err("XP 來源同 spec 唔一樣")
    if sorted(map(int, fl["unlocks"])) != list(range(2, 11)): err("解鎖要 Lv2–10 每級有")
    want = {"2": "room2", "5": "room3", "8": "room4", "6": "kid_series_E", "7": "job_cap_plus1", "10": "tree_gold"}
    for lv, u in want.items():
        if u not in [x["id"] for x in fl["unlocks"][lv]]: err(f"Lv{lv} 冇 {u}")
    A = J["actions"]["interact"]
    if set(A["forms"]) != set(LB.ALL59): err(f"interact 形態 {len(A['forms'])} ≠59")
    mx = 0
    for k, m in A["forms"].items():
        g = LB._geo(k, "interact")
        if [g["CW"], g["CH"]] != [m["frameW"], m["frameH"]] or m["pivot"] != [g["PX"], g["PY"]]: err(f"{k} interact geo 唔啱")
        a = strip_ok("5a/" + m["png"], m["frameW"], m["frameH"], 8, k, k in NEWF)
        if k not in NEWF: mx = max(mx, max(ncol(a[:, i * m["frameW"]:(i + 1) * m["frameW"]]) for i in range(8)))
    INFO.append(f"interact 59 形態；舊形態（4a 已上線色數）每格最多 {mx} 色")
    for r, m in J["rooms"].items():
        if r == "room1": continue
        for v in ("day", "night"):
            for n in ("sky", "far", "mid", "fore", "lightmap", "light_add", "emissive", "emissive_blur"):
                a = png(f"5a/rooms/{r}/{v}/{n}.png")
                if a.shape[:2] != (446, 223): err(f"{r}/{v}/{n} size {a.shape[:2]}")
            if png(f"5a/rooms/{r}/{v}/vignette.png").shape[:2] != (422, 195): err(f"{r}/{v}/vignette size")
            for n in ("sky", "far", "mid", "fore"):
                a = png(f"5a/rooms/{r}/{v}/raw/{n}.png"); binary(a, f"{r}/raw/{v}/{n}")
                if ncol(a) > 64: err(f"{r}/raw/{v}/{n} {ncol(a)} 色 >64")
            binary(png(f"5a/rooms/{r}/{v}/emissive.png"), f"{r}/{v}/emissive")
            for f in ("grade.json", "palette.json"): exists(f"5a/rooms/{r}/{v}/{f}")
        if m["capacity"] != 4: err(f"{r} capacity ≠4")
    # 擴房幾何同 4b 一樣：far 層 wall 位置一致（牆框 alpha 同 4b room1 一樣）
    a1 = np.asarray(Image.open(os.path.join(ART, "sprites/series2_house/room/day/raw/mid.png")))[..., 3]
    for r in ("room2", "room3", "room4"):
        a2 = png(f"5a/rooms/{r}/day/raw/mid.png")[..., 3]
        if (a1 != a2).mean() > 0.01: err(f"{r} mid 層形狀同 4b 差 >1%（slots／walk 會唔啱）")
    Lj = js("5a/ui/layout.json")
    for n, p in Lj["assets"].items():
        if exists("5a/" + p):
            im = Image.open(os.path.join(D, "5a", p)); N["png"] += 1
            if im.mode != "RGBA": err(f"{p} 唔係 RGBA")
    for p in ("family_tree_HD2D_3x.png", "family_tree_gold_lv10_HD2D_3x.png", "levelup_lv5_HD2D_3x.png", "egg_choice_HD2D_3x.png", "egg_choice_kid_disabled_HD2D_3x.png",
              "pet_card_make_main_HD2D_3x.png", "house_room2_hud_day_HD2D_3x.png", "rooms_5a_3x.png", "interact_duo_room2.gif", "interact_forms.gif"):
        if exists("5a/preview/" + p) and p.endswith("HD2D_3x.png"):
            if Image.open(os.path.join(D, "5a/preview", p)).size != (585, 1266): err(f"{p} 唔係 585×1266")
    INFO.append(f"5a ui 零件 {len(Lj['assets'])}")

def v5b():
    import long_5b_build as B5
    J = js("5b/long_5b.json"); dl, ex, jb = J["daily"], J["expedition"], J["jobs"]
    if dl["shardCapPerDay"] != 12 or dl["choose"] != ["expedition", "job", "rest"]: err("每日規則同 spec 唔一樣")
    if ex["maxPerDay"] != 2 or ex["durationH"] != 24 or ex["shards"] != [5, 10] or ex["furnitureChance"] != 0.3: err("遠足數值同 spec 唔一樣")
    if [j["id"] for j in jb["list"]] != ["post", "garden", "watch", "chef"]: err("工作 4 款唔啱")
    lv = jb["levels"]
    if (lv["max"], lv["maxWithFamilyLv7"], lv["daysPerLevel"]) != (5, 6, 5): err("工作等級規則唔啱")
    if sorted(sum([t["levels"] for t in jb["tiers"]], [])) != [1, 2, 3, 4, 5, 6]: err("帽 tier 要覆蓋 Lv1–6")
    if set(ex["forms"]) != set(LB.ADULTS) or set(jb["forms"]) != set(LB.ADULTS): err(f"成年形態數唔啱（要 {len(LB.ADULTS)}）")
    for k in LB.ADULTS:
        for n in ("depart", "return"):
            m = ex["forms"][k][n]; g = LB._geo(k, n)
            if [g["CW"], g["CH"]] != [m["frameW"], m["frameH"]] or m["pivot"] != [g["PX"], g["PY"]]: err(f"{k} {n} geo 唔啱")
            strip_ok("5b/" + m["png"], m["frameW"], m["frameH"], LB.CLIPS5[n]["frames"], k, k in NEWF)
        r = LB.rig(k); clips = LB.clips_of(k)
        for jid in ("post", "garden", "watch", "chef"):
            hm = jb["forms"][k][jid]; a = png("5b/" + hm["png"]); binary(a, hm["png"])
            for t in ("t1", "t2", "t3", "t4"):
                ys = [rw["y"] for rw in hm["rows"] if rw["tier"] == t]; ye = max(rw["y"] + rw["frameH"] for rw in hm["rows"] if rw["tier"] == t)
                if ncol(a[min(ys):ye]) > 12: err(f"{hm['png']} {t} {ncol(a[min(ys):ye])} 色 >12")
            if sorted({rw["tier"] for rw in hm["rows"]}) != ["t1", "t2", "t3", "t4"]: err(f"{hm['png']} tier 唔齊")
            if {rw["clip"] for rw in hm["rows"]} != set(clips): err(f"{hm['png']} clip 行唔齊 {set(clips) ^ {rw['clip'] for rw in hm['rows']}}")
            for rw in hm["rows"]:
                if rw["petPng"]:
                    pw = Image.open(os.path.join(ART, "sprites", rw["petPng"])).size[0] // LB._geo(k, rw["clip"])["CW"]
                    if pw != rw["frames"]: err(f"{k} {jid} {rw['clip']} 格數 {rw['frames']} ≠ pet {pw}")
                for i in range(rw["frames"]):
                    if not a[rw["y"]:rw["y"] + rw["frameH"], i * rw["frameW"]:(i + 1) * rw["frameW"], 3].any(): err(f"{hm['png']} {rw['tier']} {rw['clip']} 第{i}格冇帽"); break
            for t in ("t1", "t4"):
                pa = B5.hat_patch(r, jid, t)[B5.HPAD[1]:, B5.HPAD[0]:B5.HPAD[0] + r.base.shape[1], 3] > 0
                if any(pa[y, x] for (x, y) in r.protect): err(f"{k} {jid} 帽蓋住燈泡")
                for e in r.eyes:
                    x0, y0, x1, y1 = e["box"]
                    if pa[y0:y1 + 1, x0:x1 + 1].any(): err(f"{k} {jid} 帽蓋住眼")
    S = J["souvenirs"]
    if len(S) != 10: err("手信唔係 10 款")
    for sv in S:
        a = png("5b/" + sv["px"]); binary(a, sv["px"])
        if ncol(a) > 12: err(f"{sv['px']} {ncol(a)} 色")
        for q in ("icon", "medal"): exists("5b/" + sv[q])
        if sv["id"] not in ex["souvenirPool"]: err(f"{sv['id']} 唔喺 pool")
    Lj = js("5b/ui/layout.json")
    for n, p in Lj["assets"].items():
        if exists("5b/" + p):
            im = Image.open(os.path.join(D, "5b", p)); N["png"] += 1
            if im.mode != "RGBA": err(f"{p} 唔係 RGBA")
    for p in ("daily_plan_HD2D_3x.png", "daily_plan_full_HD2D_3x.png", "job_picker_HD2D_3x.png", "return_toast_HD2D_3x.png", "diary_pinecone_HD2D_3x.png", "diary_starstone_HD2D_3x.png",
              "trip_A3_depart_3x.png", "trip_A3_return_3x.png"):
        if exists("5b/preview/" + p) and Image.open(os.path.join(D, "5b/preview", p)).size != (585, 1266): err(f"{p} 唔係 585×1266")
    for p in ("trip_A3_room2.gif", "trip_evo_still_moon_room3.gif", "job_hats_on_pets.gif", "job_hats_kid_3x.png", "job_hats_tuanrong_3x.png", "trip_all_adults_3x.png", "souvenirs_sheet.png"): exists("5b/preview/" + p)
    INFO.append(f"5b 成年 {len(LB.ADULTS)}：出發／返屋 strip {2 * len(LB.ADULTS)}、帽 atlas {4 * len(LB.ADULTS)}（每張 4 tier）、手信 10、ui 零件 {len(Lj['assets'])}")

def v5c():
    J = js("5c/long_5c.json"); R = J["rules"]; PNs = [p["id"] for p in J["patterns"]]
    if len(PNs) != 8: err("花紋唔係 8 款")
    fg = R["fastGrow"]
    if (fg["fromFamilyLv"], fg["stages"], fg["speedup"], fg["excludeEgg"]) != (3, 2, 0.2, "tr"): err("加速規則同 spec 唔一樣")
    if R["tree"] != ["代", "系", "上一代", "教錯咗乜"]: err("族譜欄位唔啱")
    if set(J["parents"]) != set(LB.ADULTS): err("上一代表唔齊")
    for k, v in J["parents"].items():
        if v["pattern"] not in PNs: err(f"{k} 花紋 {v['pattern']} 唔存在")
        if not all(isinstance(v["tint"][q], str) and v["tint"][q].startswith("#") for q in ("hi", "lo", "base")): err(f"{k} 染色唔啱")
    if sorted(J["tricks"]) != list("ABCDEFGH"): err("招式 A–H 唔齊")
    F = J["overlay"]["forms"]
    if set(F) != set(LB.ALL59): err(f"花紋 overlay 形態 {len(F)} ≠59")
    low = []
    for k, m in F.items():
        a = png("5c/" + m["png"]); binary(a, m["png"])
        vals = set(np.unique(a[a[..., 3] > 0][:, 0])) if a[..., 3].any() else set()
        if not vals <= {128, 255}: err(f"{m['png']} mask 值唔係 128/255")
        if sorted({rw["pattern"] for rw in m["rows"]}) != sorted(PNs): err(f"{m['png']} pattern 唔齊")
        if {rw["clip"] for rw in m["rows"]} != set(LB.clips_of(k)): err(f"{m['png']} clip 唔齊")
        for p in PNs:
            if m["maskPx"][p] < 2: err(f"{k} {p} mask 得 {m['maskPx'][p]}px")
            if m["maskPx"][p] < 8: low.append(f"{k}:{p}")
        for rw in m["rows"]:
            if not rw["petPng"]: continue
            pet = np.asarray(Image.open(os.path.join(ART, "sprites", rw["petPng"])).convert("RGBA"))
            reg = a[rw["y"]:rw["y"] + rw["frameH"], :rw["frames"] * rw["frameW"], 3] > 0
            if pet.shape[:2] != reg.shape: err(f"{k} {rw['clip']} overlay 格同 pet strip 唔同大小"); continue
            if (reg & (pet[..., 3] == 0)).any(): err(f"{k} {rw['pattern']} {rw['clip']} 花紋出咗 pet 外面")
            for i in range(rw["frames"]):
                if not reg[:, i * rw["frameW"]:(i + 1) * rw["frameW"]].any() and m["maskPx"][rw["pattern"]] >= 8: err(f"{k} {rw['pattern']} {rw['clip']} 第{i}格冇花紋"); break
    for e, m in J["overlay"]["eggs"].items():
        a = png("5c/" + m["png"]); binary(a, m["png"]); src = np.asarray(Image.open(os.path.join(ART, "sprites", m["rows"][0]["eggPng"])).convert("RGBA"))
        if a.shape[:2] != (src.shape[0] * 8, src.shape[1]): err(f"{e} egg atlas size 唔啱")
        for rw in m["rows"]:
            reg = a[rw["y"]:rw["y"] + src.shape[0], :, 3] > 0
            if (reg & (src[..., 3] == 0)).any(): err(f"{e} {rw['pattern']} 出咗蛋外面")
            if not reg.any(): err(f"{e} {rw['pattern']} 冇花紋")
    Lj = js("5c/ui/layout.json")
    for n, p in Lj["assets"].items():
        if exists("5c/" + p):
            im = Image.open(os.path.join(D, "5c", p)); N["png"] += 1
            if im.mode != "RGBA": err(f"{p} 唔係 RGBA")
    for p in ("parent_pick_HD2D_3x.png", "parent_pick_tr_egg_HD2D_3x.png", "inherit_result_S1_HD2D_3x.png", "inherit_result_tr_HD2D_3x.png"):
        if exists("5c/preview/" + p) and Image.open(os.path.join(D, "5c/preview", p)).size != (585, 1266): err(f"{p} 唔係 585×1266")
    for p in ("inherit_eggs_3x.png", "inherit_growth_line_3x.png", "inherit_tuanrong_3x.png", "inherit_all59_3x.png", "inherit_forms.gif", "ui_5c_sheet_HD2D_3x.png"): exists("5c/preview/" + p)
    INFO.append(f"5c 花紋 overlay 59 形態 × 8 ＋ 蛋 3 款；mask <8px 嘅組合 {len(low)} 個（細形態，睇 open question）：{' '.join(low[:12])}")
    INFO.append(f"5c ui 零件 {len(Lj['assets'])}")

PARTS = {"5a": v5a, "5b": v5b, "5c": v5c}
def main():
    want = sys.argv[1:] or [p for p in ("5a", "5b", "5c") if os.path.exists(os.path.join(D, p, f"long_{p}.json"))]
    for p in want:
        try: PARTS[p]()
        except KeyError: err(f"未有 {p} validator")
    for i in INFO: print("・", i)
    print(f"檢查 {N['png']} PNG／{N['json']} JSON；部份：{' '.join(want)}")
    if ERR:
        print(f"✗ {len(ERR)} 個問題"); [print("  -", e) for e in ERR[:60]]; sys.exit(1)
    print("✓ 全部 OK")
if __name__ == "__main__": main()
