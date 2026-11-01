# 《微光小圃》5b UI（HD-2D）：每日安排（遠足／工作／休息）、揀工作、工作 Lv 章、遠足中卡、返屋 toast、團絨日記一格故事
# 純 Pillow/numpy，冇 AI。零件 3x；layout art 座標 195×422。
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import long_5abc_ui as U
import long_5abc_lib as LB
import long_5a_ui as A5
from series2_lib import ART
H = U.H; P = U.P; C = U.C; hx = U.hx
O5 = os.path.join(LB.OUTL, "5b"); UO = os.path.join(O5, "ui"); PV = os.path.join(O5, "preview")
D = json.load(open(os.path.join(O5, "long_5b.json")))
JOBS = D["jobs"]["list"]; JZ = {j["id"]: j["zh"] for j in JOBS}; SV = {s["id"]: s for s in D["souvenirs"]}
CHO = [("expedition", "遠足", "expedition", 'pri'), ("job", "工作", "job_post", 'sec'), ("rest", "休息", "rest", 'violet')]

L = {"style": "HD-2D（ui/style_ref/hd2d）；零件 3x", "assets": {},
 "dailyPlan": {"open": "屋內 HUD 加「今日安排」掣（cx 172, cy 352, d 30, icon expedition）；每日 05:00 重置", "panel": {"x": 10, "y": 74, "w": 175, "h": 262},
   "plaque": {"y": 66, "w": 104, "label": "今日安排"}, "chips": {"y": 92, "expedition": {"x": 20, "w": 72, "fmt": "遠足 {n}/2"}, "shards": {"x": 103, "w": 72, "fmt": "今日 {n}/12 碎"}},
   "rows": {"x": 18, "y0": 110, "dy": 49, "w": 159, "h": 45, "portrait": {"dx": 22, "dy": 22.5, "d": 34}, "name": {"dx": 46, "dy": 10},
            "seg": {"dx": 44, "dy": 17, "w": 36, "h": 15, "gap": 2, "note": "3 粒 segment：遠足／工作／休息；揀咗＝亮＋金光；冇得揀＝dis＋鎖（遠足 2/2 用晒）"},
            "status": {"dx": 46, "dy": 38, "note": "細字：遠足中 hh:mm／郵差助手 Lv3（再做 2 日升級）／休息緊 zZ"}},
   "rule": "主養唔會出現（佢喺花園）；每隻每日揀 1 樣；遠足中嘅成年要等返屋先再揀", "confirm": {"x": 57, "y": 312, "w": 81, "h": 18, "label": "好！"}},
 "jobPicker": {"panel": {"x": 14, "y": 96, "w": 167, "h": 226}, "plaque": {"y": 88, "w": 96, "label": "揀工作"},
   "cards": {"x": [22, 101], "y": [116, 214], "w": 72, "h": 92, "medal": {"dy": 26, "d": 34}, "name": {"dy": 52}, "lv": {"dy": 63}, "bar": {"dy": 72, "w": 56, "h": 4}, "out": {"dy": 82}},
   "badge": "Lv 章（hex 寶石，1–6）喺 medal 右上", "lv6": "家族 Lv7 前：Lv5 滿咗 bar 變金＋「家族 Lv7 開 Lv6」", "note": "每隻寵物每款工作各自計日數（5 日升 1 級）"},
 "awayCard": {"note": "遠足中：屋內佢個位冇人；每日安排嗰行 portrait 變剪影＋背囊 icon＋倒數"},
 "returnToast": {"x": 14, "y": 46, "w": 167, "h": 40, "medal": {"dx": 20, "d": 30}, "title": {"dx": 40, "dy": 13}, "body": {"dx": 40, "dy": 27},
   "anim": "由上滑落 260ms easeOutBack，停 2.6s，撳＝開日記", "shardChip": {"dx": 132, "dy": 20}},
 "diary": {"panel": {"x": 12, "y": 70, "w": 171, "h": 250}, "plaque": {"y": 62, "w": 104, "label": "團絨日記"}, "date": {"y": 86},
   "pic": {"x": 22, "y": 96, "w": 151, "h": 112, "note": "一格故事：遠足地點 scene crop（scenes/hd2d H1–H4 輪）＋寵物返屋格＋手信 1x ×2"},
   "text": {"y": [218, 230, 242]}, "loot": {"y": 266, "note": "手信 medal ＋ 碎 chip ＋（30%）家具 chip"}, "nav": {"l": {"cx": 26, "cy": 302}, "r": {"cx": 169, "cy": 302}}}}

def save(im, name):
    p = f"ui/{name}@3x.png"; U.x3(U.crop(im)).save(os.path.join(O5, p)); L["assets"][name] = p; return p

def lv_badge(b, cx, cy, lv, d=11):
    fill = C['gem'] if lv >= 6 else (C['pri'] if lv >= 3 else C['sec'])
    H.gem(b, P(cx), P(cy), d / 5.5, fill, glow=lv >= 5, star=False)
    H.text(b, (P(cx), P(cy - .2)), str(lv), d * .62, C['cream'], 'cin', stroke=1.0)

def seg(b, x, y, w, h, sel, i, locked=False):
    cid, zh, ic, kind = CHO[i]
    U.pill(b, x, y, w, h, 'dis' if locked else (kind if sel else 'dis'), zh, ic, 5.8)
    if sel: U.glow_spot(b, P(x + w / 2), P(y + h / 2), w * .55, a=.35)
    if locked: U.icon(b, "lock", P(x + w - 3), P(y + 3), 7)

PLAN = [("A3", "滴滴", 0, "遠足中・仲有 18:24"), ("evo_still_moon", "月月", 1, "郵差助手 Lv3・再做 2 日升級"), ("F3", "星仔", 2, "休息緊 zZ"), ("evo_still_soft", "棉棉", None, "未揀")]
def plan_panel(b, used=1, shards=6, plan=PLAN, full=False):
    c = L["dailyPlan"]; pn = c["panel"]
    U.panel(b, pn["x"], pn["y"], pn["w"], pn["h"], 11, ornate=True); H.plaque(b, 97.5, 66, 104, "今日安排")
    for key, txt, ic in (("expedition", f"遠足 {used}/2", "expedition"), ("shards", f"今日 {shards}/12 碎", "shards")):
        q = c["chips"][key]; H.place(b, H.frame(q["w"], 13, 6.5, C['navy_in'], glow=.4, ornate=False, rim=.9), P(q["x"]), P(c["chips"]["y"]))
        U.icon(b, ic, P(q["x"] + 7), P(c["chips"]["y"] + 6.5), 12); H.text(b, (P(q["x"] + q["w"] / 2 + 5), P(c["chips"]["y"] + 6.3)), txt, 5.8, C['cream'], 'serif', stroke=.7)
    r = c["rows"]
    for n, (k, nm, ch, st) in enumerate(plan):
        y = r["y0"] + n * r["dy"]; away = ch == 0 and "遠足中" in st
        H.place(b, H.frame(r["w"], r["h"], 8, C['navy_in'], glow=.5, ornate=False, rim=.9), P(r["x"]), P(y))
        U.portrait(b, k, P(r["x"] + 22), P(y + 22.5), 34, dark=away)
        if away: U.medal(b, P(r["x"] + 33), P(y + 34), 14, C['pri'], "expedition", 11)
        H.gold_text(b, (P(r["x"] + 46), P(y + 10)), nm, 7.2, 'serif', anchor='lm', glow=.3)
        for i in range(3):
            lk = (i == 0 and full and ch != 0) or (away and i != 0)
            seg(b, r["x"] + 44 + i * 38, y + 17, 36, 14, ch == i, i, lk)
        H.text(b, (P(r["x"] + 46), P(y + 38)), st, 5.2, hx('#AEE6F0') if ch is not None else hx('#FFE6A8'), 'sans', anchor='lm', stroke=.6)
        if ch == 1: lv_badge(b, r["x"] + r["w"] - 10, y + 10, 3, 14)
    q = c["confirm"]; H.button(b, q["x"], q["y"], q["w"], q["h"], 'pri', q["label"])

def mock_plan(full=False):
    bg = U.dim(A5.mock_room("room2"), .58); b = U.board()
    plan = PLAN if not full else [("A3", "滴滴", 0, "遠足中・仲有 18:24"), ("evo_still_moon", "月月", 0, "遠足中・仲有 23:50"), ("F3", "星仔", None, "遠足 2/2 用晒，揀工作或休息"), ("evo_still_soft", "棉棉", 1, "園丁 Lv5・Lv6 要家族 Lv7")]
    plan_panel(b, 2 if full else 1, 9 if full else 6, plan, full); bg.alpha_composite(b); return bg

JOB_ST = {"post": (3, .6, "+3 碎/日"), "garden": (1, .2, "+1 碎/日"), "watch": (5, 1.0, "+5 碎/日"), "chef": (0, 0, "未做過")}
def job_card(b, x, y, jid, lv, prog, out, sel=False, cap=False):
    c = L["jobPicker"]["cards"]; w, h = c["w"], c["h"]
    H.place(b, H.frame(w, h, 7, C['navy_in'], glow=1.3 if sel else .6, ornate=False, rim=1.0), P(x), P(y))
    U.glow_spot(b, P(x + w / 2), P(y + 26), 18, C['cyan'], .45)
    U.medal(b, P(x + w / 2), P(y + 26), 34, C['pri'] if sel else C['navy'], f"job_{jid}", 27)
    if lv: lv_badge(b, x + w / 2 + 14, y + 13, lv)
    H.gold_text(b, (P(x + w / 2), P(y + 52)), JZ[jid], 7.4, 'serif', glow=.3)
    H.text(b, (P(x + w / 2), P(y + 62)), f"Lv{lv}" if lv else "Lv0", 5.6, hx('#C9D0F0'), 'sans', stroke=.6)
    U.bar(b, x + 8, y + 69, w - 16, 4, prog, cols=(C['g_hi'], C['g_lo']) if cap else None)
    H.text(b, (P(x + w / 2), P(y + 81)), "家族 Lv7 開 Lv6" if cap else out, 5.4, hx('#FFE6A8') if cap else C['cream'], 'sans', stroke=.6)
def mock_jobs():
    bg = U.dim(A5.mock_room("room2"), .6); b = U.board(); c = L["jobPicker"]; pn = c["panel"]
    U.panel(b, pn["x"], pn["y"], pn["w"], pn["h"], 11, ornate=True); H.plaque(b, 97.5, 88, 96, "揀工作")
    for n, j in enumerate(JOBS):
        lv, pr, out = JOB_ST[j["id"]]; job_card(b, c["cards"]["x"][n % 2], c["cards"]["y"][n // 2], j["id"], lv, pr, out, sel=j["id"] == "post", cap=j["id"] == "watch")
    H.text(b, (P(97.5), P(311)), "做滿 5 日升 1 級・每日最多 12 碎", 5.6, hx('#C9D0F0'), 'sans', stroke=.6)
    H.close_btn(b, P(176), P(100)); bg.alpha_composite(b); return bg

def toast(b, k="A3", nm="滴滴", sv="sv_pinecone", shards=7, furn=None, y=46):
    q = L["returnToast"]; x, w, h = q["x"], q["w"], q["h"]
    H.place(b, H.frame(w, h, 9, C['navy'], glow=1.0, ornate=False, rim=1.1), P(x), P(y))
    U.medal(b, P(x + 20), P(y + h / 2), 30, C['pri'], sv, 24)
    H.gold_text(b, (P(x + 40), P(y + 13)), f"{nm}返嚟喇！", 7.4, 'serif', anchor='lm', glow=.3)
    H.text(b, (P(x + 40), P(y + 27)), f"帶咗「{SV[sv]['zh']}」" + (f"＋{furn}" if furn else ""), 5.8, C['cream'], 'sans', anchor='lm', stroke=.6)
    U.pill(b, x + w - 40, y + h / 2 - 6.5, 34, 13, 'sec', f"+{shards}", "shards", 6.2)
def mock_return():
    pets = [("A3", "return", 92, 318, False), ("evo_still_moon", "sit", 132, 300, True)]
    f, piv, _ = U.strip_frame("A3", "return", 7); sv = np.asarray(Image.open(os.path.join(O5, SV["sv_pinecone"]["px"])).convert("RGBA"))
    ht = D["expedition"]["forms"]["A3"]["headTop"]; ex = [(9998, sv, 92 - 24 + int(ht[0]) - sv.shape[1] // 2, 318 - 45 + int(ht[1]) - 10 - sv.shape[0], "furn")]
    ps = [(f, piv, 92, 318, 318)] + A5.pets_in([pets[1]], 2)
    bg = U.room_ss("room2", "day", A5.SET_A, ps, ex); ui = U.board(); A5.hud(ui, "room2", 4, 333, 3); toast(ui); bg.alpha_composite(ui); return bg

def scene_pic(sc="H2", w=151, h=112, ox=36, oy=180):
    base = os.path.join(ART, "scenes/hd2d", sc); im = None
    for ly in ("sky", "far", "mid"):
        a = Image.open(os.path.join(base, f"{ly}.png")).convert("RGBA"); im = a if im is None else Image.alpha_composite(im, a)
    return np.asarray(im.crop((ox, oy, ox + w, oy + h)))
STORY = {"sv_pinecone": ("H2", ["滴滴行到森林深處，", "喺大樹腳執到一粒松果，", "仲同松鼠玩咗成個下晝。"]),
         "sv_starstone": ("H4", ["月月半夜爬上山頂，", "數星星數到瞓着咗，", "醒返手入面多咗粒星星石。"])}
def diary(b, k="A3", nm="滴滴", sv="sv_pinecone", day="第 23 日", shards=7, furn="家具：松果燈"):
    q = L["diary"]; pn = q["panel"]; sc, lines = STORY[sv]
    U.panel(b, pn["x"], pn["y"], pn["w"], pn["h"], 11, 'paper' if 'paper' in C else 'panel', ornate=True); H.plaque(b, 97.5, 62, 104, "團絨日記")
    H.text(b, (P(97.5), P(86)), f"{day}・{nm}嘅遠足", 5.8, hx('#8A6A4A'), 'sans', stroke=0)
    pc = q["pic"]; pic = scene_pic(sc, pc["w"], pc["h"]).copy()
    f, piv, _ = U.strip_frame(k, "return", 6); m = f[..., 3] > 0; x0, y0 = pc["w"] // 2 - piv[0], pc["h"] - 10 - piv[1]
    sub = pic[max(0, y0):y0 + f.shape[0], max(0, x0):x0 + f.shape[1]]; ff = f[max(0, -y0):, max(0, -x0):][:sub.shape[0], :sub.shape[1]]; mm = ff[..., 3] > 0; sub[mm] = ff[mm]
    pim = Image.fromarray(pic).resize((P(pc["w"]), P(pc["h"])), Image.NEAREST)
    H.place(b, H.frame(pc["w"] + 4, pc["h"] + 4, 4, C['navy_in'], glow=.3, ornate=False, rim=1.0), P(pc["x"] - 2), P(pc["y"] - 2)); b.alpha_composite(pim, (P(pc["x"]), P(pc["y"])))
    for i, s in enumerate(lines): H.text(b, (P(97.5), P(q["text"]["y"][i])), s, 6.4, hx('#5A4030'), 'serif', stroke=0)
    U.medal(b, P(46), P(270), 24, C['pri'], sv, 19); U.pill(b, 64, 263.5, 36, 13, 'sec', f"+{shards}", "shards", 6.0)
    if furn: U.pill(b, 104, 263.5, 70, 13, 'violet', furn, "furniture", 5.6)
    for side, cx in (("l", 26), ("r", 169)): U.medal(b, P(cx), P(302), 18, C['navy'], "arrow_" + side, 12)
    H.text(b, (P(97.5), P(302)), "3 / 12", 5.8, hx('#8A6A4A'), 'sans', stroke=0)
def mock_diary(**kw):
    bg = U.dim(A5.mock_room("room2"), .6); b = U.board(); diary(b, **kw); bg.alpha_composite(b); return bg

def components():
    for j in JOBS:
        b = U.board(30, 30); U.medal(b, P(15), P(15), 24, C['navy'], f"job_{j['id']}", 19); save(b, f"icon_job_{j['id']}")
    for kk in ("expedition", "rest", "shards", "job_lv"):
        b = U.board(30, 30); U.medal(b, P(15), P(15), 24, C['navy'], kk, 19); save(b, f"icon_{kk}")
    for lv in range(1, 7):
        b = U.board(16, 16); lv_badge(b, 8, 8, lv); save(b, f"badge_job_lv{lv}")
    for i in range(3):
        for st in ("on", "off", "locked"):
            b = U.board(42, 20); seg(b, 3, 3, 36, 14, st == "on", i, st == "locked"); save(b, f"seg_{CHO[i][0]}_{st}")
    b = U.board(86, 104); job_card(b, 4, 4, "post", 3, .6, "+3 碎/日", sel=True); save(b, "job_card_example")
    b = U.board(86, 104); job_card(b, 4, 4, "watch", 5, 1.0, "", cap=True); save(b, "job_card_capped")
    b = U.board(180, 50); toast(b, y=4); save(b, "toast_return")
    b = U.board(195, 422); diary(b); save(b, "diary_page_example")

def main():
    os.makedirs(UO, exist_ok=True); os.makedirs(PV, exist_ok=True); components()
    ims = {"daily_plan": mock_plan(False), "daily_plan_full": mock_plan(True), "job_picker": mock_jobs(), "return_toast": mock_return(),
           "diary_pinecone": mock_diary(), "diary_starstone": mock_diary(k="evo_still_moon", nm="月月", sv="sv_starstone", day="第 24 日", shards=9, furn=None)}
    out = {}
    for n, im in ims.items():
        U.x3(im).convert('RGB').save(os.path.join(PV, n + "_HD2D_3x.png")); out[n] = U.x3(im)
    U.strip_sheet([out[n] for n in ims], ["每日安排", "每日安排・遠足 2/2", "揀工作", "返屋 toast", "團絨日記（有家具）", "團絨日記"], os.path.join(PV, "ui_5b_sheet_HD2D_3x.png"))
    U.parts_sheet(list(L["assets"].values()), os.path.join(PV, "ui_parts_5b_HD2D_3x.png"), O5)
    LB.jdump(L, os.path.join(UO, "layout.json")); print("ui 5b ok", len(L["assets"]))
if __name__ == "__main__": main()
