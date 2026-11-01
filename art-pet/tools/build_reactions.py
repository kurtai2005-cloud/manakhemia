#!/usr/bin/env python3
"""batch 3a：觸摸反應 ×5（＋瞓覺／尷尬）＋ 蠢萌反應 ×6 — 兩條寵物線（舊 團絨 evo 形態 25 款 ＋ 新蛋 24 隻）
純 Pillow／numpy 程序生成。輸出 sprites/tuanrong/reactions/。重跑：python3 tools/build_reactions.py"""
import os, sys, json, math, shutil
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reactions_lib as L

OUT = os.path.join(L.TR, "reactions")
PREVIEW_PETS = ["evo_hop", "evo_still_ember", "A1", "H3"]          # 舊 2 ＋ 新 2

# ───────────── clip 定義（時間 ms；body = 變形 keyframe；缺嘅欄位沿用上一格） ─────────────
def wob(T, n, amp, key="rot", y=0):
    return [{"t": int(T * i / n), key: (amp if i % 2 else -amp) if 0 < i < n else 0, "e": "inout", **({"y": y} if y else {})} for i in range(n + 1)]
CLIPS = {
 "touch_poke": {"group": "touch", "dur": 500, "loop": False,
   "trigger": "tap（按落→放 <250ms、移動 <12px）。瞓緊 → touch_sleep_rub；蠢萌反應進行中 → touch_embarrassed",
   "body": [{"t": 0}, {"t": 60, "sx": 1.15, "sy": 0.85, "e": "out"}, {"t": 150, "sx": 0.95, "sy": 1.06, "e": "inout"}, {"t": 260, "sx": 1, "sy": 1, "e": "outBack"}],
   "face": [{"t": 0, "f": "blink"}, {"t": 150, "f": None}],
   "fx": [{"id": "fx_poke", "anchor": "touch", "t0": 0, "t1": 180, "ms": 60, "loop": False, "follow": False}]},
 "touch_pet_loop": {"group": "touch", "dur": 1200, "loop": True,
   "trigger": "長按 ≥600ms 開始 loop；放手即停（回 idle 用 120ms ease-out）。連續按滿 3000ms → event pat（計一次摸頭，之後每 3000ms 再計）",
   "events": [{"t": 3000, "id": "pat", "repeatEvery": 3000, "note": "相對 long-press 開始計（包埋前 600ms）"}],
   "body": [{"t": 0}, {"t": 300, "sx": 1.04, "sy": 0.96, "rot": -2, "e": "inout"}, {"t": 600, "sx": 1, "sy": 1, "rot": 0, "e": "inout"},
            {"t": 900, "sx": 1.04, "sy": 0.96, "rot": 2, "e": "inout"}, {"t": 1200, "sx": 1, "sy": 1, "rot": 0, "e": "inout"}],
   "face": [{"t": 0, "f": ["squint", "squint", "squint_blush", "squint_blush"], "ms": 300}],
   "fx": [{"id": "fx_heart", "anchor": "headTop", "dx": 7, "dy": -2, "t0": 200, "t1": 1100, "frames": [0, 1, 1], "ms": 300, "loop": False, "move": [[0, 0, 0], [900, 2, -9]]}]},
 "touch_tickle_laugh": {"group": "touch", "dur": 480, "loop": True,
   "trigger": "搓：1000ms 內 ≥4 次方向反轉（每段 ≥8px）→ 笑 loop，持續搓就繼續；停手 → touch_tickle_roll",
   "body": [{"t": 0, "rot": -6, "y": 0}, {"t": 120, "rot": 6, "y": -2, "e": "inout"}, {"t": 240, "rot": -6, "y": 0, "e": "inout"},
            {"t": 360, "rot": 6, "y": -2, "e": "inout"}, {"t": 480, "rot": -6, "y": 0, "e": "inout"}],
   "face": [{"t": 0, "f": ["laugh_a", "laugh_b"], "ms": 120}],
   "fx": [{"id": "fx_laugh_l", "anchor": "side_l", "dx": -1, "t0": 0, "t1": 480, "ms": 120},
          {"id": "fx_laugh_r", "anchor": "side_r", "dx": 1, "t0": 0, "t1": 480, "ms": 120},
          {"id": "fx_tear", "anchor": "eyeR", "dx": 3, "dy": 1, "t0": 0, "t1": 480, "ms": 240}]},
 "touch_tickle_roll": {"group": "touch", "dur": 3000, "loop": False, "origin": "center", "groundLock": True, "rotStep": 45,
   "trigger": "tickle_laugh 完（停搓 ≥300ms）→ 喺地上碌 3 秒：碌左一圈再碌返轉頭",
   "body": [{"t": 0}, {"t": 1400, "rot": -360, "x": -18, "e": "inout"}, {"t": 1600, "rot": -360, "x": -18}, {"t": 2850, "rot": 0, "x": 0, "e": "inout"}, {"t": 3000}],
   "face": [{"t": 0, "f": ["laugh_a", "laugh_b"], "ms": 140}, {"t": 2850, "f": "squint"}],
   "fx": [{"id": "series_puff", "anchor": "pivot", "t0": 1350, "t1": 1650, "ms": 100, "loop": False, "follow": False, "dx": -18, "z": "back"},
          {"id": "fx_sparkle", "anchor": "headTop", "t0": 2850, "t1": 3000, "ms": 50, "loop": False, "dy": -3}]},
 "touch_pull_hold": {"group": "touch", "dur": 400, "loop": True,
   "trigger": "按住拖 >40px：hold loop；引擎按拖嘅距離 d 實時加 stretch：sy *= 1+min(d/160,0.25)、sx *= 1-min(d/320,0.12)，rot 向拖方向（±12°）",
   "body": [{"t": 0, "sx": 0.92, "sy": 1.1, "y": -2}, {"t": 200, "sx": 0.9, "sy": 1.12, "y": -3, "e": "inout"}, {"t": 400, "sx": 0.92, "sy": 1.1, "y": -2, "e": "inout"}],
   "face": [{"t": 0, "f": "surprised"}],
   "fx": [{"id": "fx_sweat", "anchor": "headTop", "dx": 8, "dy": 2, "t0": 0, "t1": 400, "frames": [0], "ms": 400}]},
 "touch_pull_release": {"group": "touch", "dur": 700, "loop": False,
   "trigger": "拉住（>40px）後放手 → 彈返原位＋落地壓扁；系列煙",
   "body": [{"t": 0, "sx": 0.88, "sy": 1.18, "y": -6}, {"t": 120, "sx": 1.22, "sy": 0.8, "y": 0, "e": "in"}, {"t": 260, "sx": 0.94, "sy": 1.08, "e": "out"},
            {"t": 420, "sx": 1.03, "sy": 0.97, "e": "inout"}, {"t": 600, "sx": 1, "sy": 1, "e": "outBack"}, {"t": 700}],
   "face": [{"t": 0, "f": "surprised"}, {"t": 120, "f": "blink"}, {"t": 260, "f": None}],
   "fx": [{"id": "series_puff", "anchor": "pivot", "t0": 120, "t1": 420, "ms": 100, "loop": False, "follow": False, "dx": -11, "z": "back"},
          {"id": "series_puff", "anchor": "pivot", "t0": 120, "t1": 420, "ms": 100, "loop": False, "follow": False, "dx": 11, "mirrorX": True, "z": "back"}]},
 "touch_shake_dizzy": {"group": "touch", "dur": 2000, "loop": False,
   "trigger": "1000ms 內 2 次 >2.5g（加速度計）→ 暈 2 秒＋頭頂轉星；冷卻 30000ms（冷卻中再搖：唔觸發）。60s 內第 3 次 → touch_shake_pretend",
   "cooldownMs": 30000,
   "body": [{"t": 0, "sx": 1.1, "sy": 0.9}, {"t": 120, "sx": 1, "sy": 1, "e": "outBack"}] + [{"t": 120 + 235 * i, "rot": (7 if i % 2 else -7) if i < 8 else 0, "x": (1 if i % 2 else -1) if i < 8 else 0, "e": "inout"} for i in range(1, 9)],
   "face": [{"t": 0, "f": ["dizzy_a", "dizzy_b"], "ms": 160}, {"t": 1900, "f": "blink"}, {"t": 2000, "f": None}],
   "fx": [{"id": "series_orbit", "anchor": "headTop", "dy": -3, "t0": 0, "t1": 1900, "ms": 90},
          {"id": "fx_sweat", "anchor": "headTop", "dx": -8, "dy": 3, "t0": 400, "t1": 1300, "frames": [0, 1], "ms": 450, "loop": False, "move": [[0, 0, 0], [900, 0, 5]]}]},
 "touch_shake_pretend": {"group": "touch", "dur": 2400, "loop": False,
   "trigger": "60s 內第 3 次搖：唔暈，扮冇事發生（望天吹口哨），引擎顯示對白 line_pretend（文字由 遊策 提供）",
   "events": [{"t": 300, "id": "line:shake_pretend"}],
   "body": [{"t": 0}, {"t": 200, "x": 2, "rot": 3, "e": "out"}, {"t": 2100, "x": 2, "rot": 3}, {"t": 2400, "x": 0, "rot": 0, "e": "inout"}],
   "face": [{"t": 0, "f": "smug"}, {"t": 1200, "f": "lookup"}, {"t": 1350, "f": "smug"}],
   "fx": [{"id": "fx_sweat", "anchor": "headTop", "dx": -8, "dy": 3, "t0": 600, "t1": 2000, "frames": [0, 1], "ms": 700, "loop": False, "move": [[0, 0, 0], [1400, 0, 6]]},
          {"id": "fx_sparkle", "anchor": "headTop", "dx": 10, "dy": -4, "t0": 300, "t1": 900, "ms": 120}]},
 "touch_sleep_rub": {"group": "touch", "dur": 1600, "loop": False,
   "trigger": "瞓緊（sleep state）時任何手勢 → 揉眼、轉身（flipX）繼續瞓；唔會醒",
   "body": [{"t": 0}, {"t": 120, "sx": 1.06, "sy": 0.94, "e": "out"}, {"t": 300, "sx": 1, "sy": 1, "e": "inout"},
            {"t": 650, "sx": 0.94, "sy": 1.04, "e": "in"}, {"t": 700, "flip": 1, "sx": 1.1, "sy": 0.9, "e": "step"}, {"t": 850, "sx": 1, "sy": 1, "e": "outBack"}, {"t": 1600}],
   "face": [{"t": 0, "f": "sleepy"}, {"t": 650, "f": "sleep"}],
   "fx": [{"id": "paw", "anchor": "eyeR", "dx": -1, "dy": 1, "t0": 100, "t1": 620, "frames": [0], "ms": 520, "move": [[0, 0, 0], [130, -1, -2], [260, 0, 0], [390, -1, -2], [520, 0, 0]]},
          {"id": "fx_zzz", "anchor": "headTop", "dx": 6, "dy": -1, "t0": 900, "t1": 1600, "ms": 230}]},
 "touch_embarrassed": {"group": "touch", "dur": 1000, "loop": False,
   "trigger": "蠢萌反應進行中被戳 → 中斷該反應，播尷尬臉（之後回 idle）",
   "body": [{"t": 0}, {"t": 120, "sx": 1.06, "sy": 0.92, "y": 1, "e": "out"}, {"t": 800, "sx": 1.04, "sy": 0.94, "y": 1}, {"t": 1000, "sx": 1, "sy": 1, "y": 0, "e": "outBack"}],
   "face": [{"t": 0, "f": "embarrassed"}],
   "fx": [{"id": "fx_sweat", "anchor": "headTop", "dx": 8, "dy": 2, "t0": 100, "t1": 1000, "frames": [0, 1], "ms": 450, "loop": False, "move": [[0, 0, 0], [900, 0, 5]]}]},
 # ───────── 蠢萌（dim）×6 ─────────
 "dim_glasses_count": {"group": "dim", "dur": 4400, "loop": False,
   "trigger": "DIM（見下）：戴眼鏡數嘢 1、2、3…數唔掂 → 問號、側頭",
   "wear": [{"id": "glasses", "t0": 0, "t1": 4400, "frames": [{"t": 0, "f": 0}, {"t": 300, "f": 1}, {"t": 520, "f": 0}, {"t": 3000, "f": 1}, {"t": 3200, "f": 0}]}],
   "body": [{"t": 0, "sy": 1.06, "sx": 0.96}, {"t": 200, "sy": 1, "sx": 1, "e": "outBack"}, {"t": 800}, {"t": 900, "y": -1, "e": "out"}, {"t": 1000, "y": 0, "e": "in"},
            {"t": 1500, "y": -1, "e": "out"}, {"t": 1600, "y": 0, "e": "in"}, {"t": 2100, "y": -1, "e": "out"}, {"t": 2200, "y": 0, "e": "in"},
            {"t": 2800, "rot": 0}, {"t": 3100, "rot": -8, "e": "outBack"}, {"t": 4100, "rot": -8}, {"t": 4400, "rot": 0, "e": "inout"}],
   "face": [{"t": 0, "f": None}, {"t": 700, "f": "lookup"}, {"t": 2800, "f": "blink"}, {"t": 2950, "f": None}],
   "fx": [{"id": "fx_num_1", "anchor": "headTop", "dx": -6, "dy": -3, "t0": 800, "t1": 2700, "follow": True},
          {"id": "fx_num_2", "anchor": "headTop", "dx": 0, "dy": -5, "t0": 1400, "t1": 2700},
          {"id": "fx_num_3", "anchor": "headTop", "dx": 6, "dy": -3, "t0": 2000, "t1": 2700},
          {"id": "fx_question", "anchor": "headTop", "dx": 7, "dy": -3, "t0": 2900, "t1": 4400, "move": [[0, 0, 4], [120, 0, -2], [220, 0, 0]]}]},
 "dim_book_sleep": {"group": "dim", "dur": 5200, "loop": False,
   "trigger": "DIM：睇書 → 揭頁 → 頭耷耷 → 瞓著，本書合埋跌落地；之後交返 sleep state（或 2s 後自己醒）",
   "body": [{"t": 0}, {"t": 1800, "y": 0}, {"t": 2100, "y": 1, "rot": 3, "e": "inout"}, {"t": 2300, "y": 0, "rot": 0, "e": "out"},
            {"t": 2700, "y": 1, "rot": 4, "e": "inout"}, {"t": 2900, "y": 0, "rot": 0, "e": "out"}, {"t": 3200, "y": 2, "rot": 6, "sx": 1.05, "sy": 0.94, "e": "in"},
            {"t": 4200, "sy": 0.96}, {"t": 4700, "sy": 0.94, "e": "inout"}, {"t": 5200, "sy": 0.96, "e": "inout"}],
   "face": [{"t": 0, "f": None}, {"t": 1000, "f": "blink"}, {"t": 1150, "f": None}, {"t": 1800, "f": "sleepy"}, {"t": 3150, "f": "sleep"}],
   "fx": [{"id": "fx_book", "anchor": "chest", "dy": 4, "t0": 0, "t1": 3200, "frames": [0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0], "ms": 300, "loop": False},
          {"id": "fx_book", "anchor": "pivot", "dx": 10, "dy": 0, "t0": 3200, "t1": 5200, "frames": [2], "follow": False, "move": [[0, -8, -10], [200, 0, 0]]},
          {"id": "fx_zzz", "anchor": "headTop", "dx": 6, "dy": -1, "t0": 3400, "t1": 5200, "ms": 300}]},
 "dim_wall_bump": {"group": "dim", "dur": 3800, "loop": False, "origin": "side_r",
   "trigger": "DIM：自己行去右邊，撞埋一幅牆（牆左邊緣 = side_r.x + 11px，貼地），彈返、暈、系列星",
   "body": [{"t": 0}] + [{"t": 150 * i, "x": i, "y": -1 if i % 2 else 0, "e": "linear"} for i in range(1, 11)] +
           [{"t": 1560, "x": 10, "y": 0, "sx": 0.82, "sy": 1.08, "e": "out"}, {"t": 1700, "x": 8, "sx": 1.04, "sy": 0.97, "e": "out"},
            {"t": 1900, "x": 6, "y": -3, "sx": 1, "sy": 1, "e": "out"}, {"t": 2100, "x": 5, "y": 0, "e": "in"}, {"t": 2200, "sx": 1.08, "sy": 0.92, "e": "out"},
            {"t": 2350, "sx": 1, "sy": 1, "e": "outBack"}] + [{"t": 2350 + 240 * i, "rot": (5 if i % 2 else -5) if i < 5 else 0, "e": "inout"} for i in range(1, 6)] + [{"t": 3800}],
   "face": [{"t": 0, "f": None}, {"t": 1500, "f": "surprised"}, {"t": 1700, "f": ["dizzy_a", "dizzy_b"], "ms": 160}, {"t": 3600, "f": "blink"}, {"t": 3700, "f": None}],
   "fx": [{"id": "fx_wall", "anchor": "side_r", "dx": 11, "t0": 0, "t1": 3800, "follow": False, "atGround": True, "z": "front"},
          {"id": "series_puff", "anchor": "side_r", "dx": 9, "dy": -4, "t0": 1500, "t1": 1800, "ms": 100, "loop": False, "follow": False},
          {"id": "series_orbit", "anchor": "headTop", "dy": -3, "t0": 1750, "t1": 3500, "ms": 90}]},
 "dim_mirror": {"group": "dim", "dur": 4600, "loop": False,
   "trigger": "DIM：見到鏡，以為係另一隻寵物 → 嚇親（!）→ 眨眼、對方又一齊眨 → 側頭疑惑。倒影 = 同一幀寵物左右反轉縮細、clip 落玻璃",
   "body": [{"t": 0}, {"t": 700}, {"t": 800, "sx": 1.1, "sy": 0.9, "e": "out"}, {"t": 950, "sx": 0.94, "sy": 1.08, "y": -4, "e": "out"}, {"t": 1100, "sx": 1, "sy": 1, "y": 0, "e": "in"},
            {"t": 1200, "sx": 1.06, "sy": 0.94, "e": "out"}, {"t": 1350, "sx": 1, "sy": 1, "e": "outBack"}, {"t": 3300, "rot": 0}, {"t": 3550, "rot": 7, "e": "outBack"}, {"t": 4400, "rot": 7}, {"t": 4600, "rot": 0, "e": "inout"}],
   "face": [{"t": 0, "f": None}, {"t": 750, "f": "surprised"}, {"t": 1500, "f": None}, {"t": 2000, "f": "blink"}, {"t": 2150, "f": None}, {"t": 2700, "f": "blink"}, {"t": 2850, "f": None}, {"t": 3300, "f": "lookup"}],
   "fx": [{"id": "fx_mirror_back", "anchor": "side_r", "dx": 13, "t0": 0, "t1": 4600, "follow": False, "atGround": True, "z": "back"},
          {"id": "fx_mirror_front", "anchor": "side_r", "dx": 13, "t0": 0, "t1": 4600, "follow": False, "atGround": True, "frames": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1], "ms": 400, "z": "front"},
          {"id": "fx_exclaim", "anchor": "headTop", "dx": 0, "dy": -3, "t0": 800, "t1": 1500, "move": [[0, 0, 4], [100, 0, -1], [180, 0, 0]]},
          {"id": "fx_question", "anchor": "headTop", "dx": 6, "dy": -3, "t0": 3450, "t1": 4600, "move": [[0, 0, 4], [120, 0, -2], [220, 0, 0]]}],
   "reflection": {"of": "fx_mirror_back", "scale": 0.5, "flipX": True, "tint": [0.8, 0.88, 1.0], "add": [20, 26, 40], "mask": "fx/fx_mirror_mask.png", "footInGlass": [9, 20],
                  "note": "倒影用同一個 face 軌（所以一齊眨眼）；唔用 body 變形，只用 pet 靜態幀 bbox 縮放（目標高 ≈16px）"}},
 "dim_count_fingers": {"group": "dim", "dur": 4200, "loop": False,
   "trigger": "DIM：舉手仔數手指 1、2、…4（數錯，第 3 下叫 4）→ 得意",
   "body": [{"t": 0}, {"t": 200, "rot": -3, "e": "out"}, {"t": 3200, "rot": -3}, {"t": 3350, "rot": 0, "y": -2, "e": "out"}, {"t": 3500, "y": 0, "e": "in"}, {"t": 4200}],
   "face": [{"t": 0, "f": "lookup"}, {"t": 3200, "f": "smug"}],
   "fx": [{"id": "paw", "anchor": "side_r", "dx": -1, "dy": -3, "t0": 200, "t1": 4000, "frames": [0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3], "ms": 200, "loop": False,
           "move": [[0, 0, 2], [150, 0, 0]]},
          {"id": "fx_num_1", "anchor": "side_r", "dx": 4, "dy": -14, "t0": 600, "t1": 1400, "move": [[0, 0, 2], [100, 0, 0]]},
          {"id": "fx_num_2", "anchor": "side_r", "dx": 4, "dy": -14, "t0": 1400, "t1": 2200, "move": [[0, 0, 2], [100, 0, 0]]},
          {"id": "fx_num_4", "anchor": "side_r", "dx": 4, "dy": -14, "t0": 2200, "t1": 4000, "move": [[0, 0, 2], [100, 0, 0]]},
          {"id": "fx_sparkle", "anchor": "headTop", "dx": -8, "dy": -2, "t0": 3200, "t1": 3800, "ms": 100}]},
 "dim_professor": {"group": "dim", "dur": 4800, "loop": False,
   "trigger": "DIM：戴四方帽、拎教鞭，喺黑板寫「1+1=3」＋「雲＝棉花糖」；引擎同步出自信錯誤對白（6×3 條，由 遊策 提供）",
   "events": [{"t": 2200, "id": "line:professor"}],
   "wear": [{"id": "hat", "t0": 0, "t1": 4800, "frames": [{"t": 0, "f": [0, 1], "ms": 300}]}],
   "body": [{"t": 0, "sx": 1.06, "sy": 0.94}, {"t": 180, "sx": 1, "sy": 1, "e": "outBack"}, {"t": 2000}, {"t": 2150, "rot": -4, "e": "out"}, {"t": 2300, "rot": 0, "e": "out"},
            {"t": 2450, "rot": -4, "e": "out"}, {"t": 2600, "rot": 0, "e": "out"}, {"t": 3300, "sy": 1}, {"t": 3450, "sy": 1.06, "sx": 0.96, "y": -1, "e": "out"}, {"t": 3700, "sy": 1, "sx": 1, "y": 0, "e": "outBack"}, {"t": 4800}],
   "face": [{"t": 0, "f": "smug"}, {"t": 1600, "f": "blink"}, {"t": 1750, "f": "smug"}],
   "fx": [{"id": "fx_board", "anchor": "side_l", "dx": -14, "t0": 0, "t1": 4800, "follow": False, "atGround": True, "frames": [0, 0, 1, 1, 1, 2], "ms": 400, "loop": False, "z": "back"},
          {"id": "fx_pointer", "anchor": "side_l", "dx": 1, "dy": 0, "t0": 300, "t1": 4800, "mirrorX": True, "frames": [0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0], "ms": 175, "loop": False},
          {"id": "fx_sparkle", "anchor": "headTop", "dx": 9, "dy": -3, "t0": 3450, "t1": 4100, "ms": 110}]},
}
DIM_RULE = {"idleMinMs": 20000, "rollEveryMs": 60000, "chance": 0.25, "minGapMs": 180000, "maxPerDay": 8,
            "pick": "6 款平均隨機，唔重複上一次；瞓緊／被摸緊／UI 開住唔觸發；被戳 → touch_embarrassed 中斷"}
TOUCH_RULE = {"poke": "tap <250ms & <12px", "longPress": ">=600ms → touch_pet_loop；3000ms = 1 次 pat event",
              "tickle": "1000ms 內 >=4 次方向反轉（每段 >=8px）", "pull": "拖 >40px → touch_pull_hold；放手 → touch_pull_release",
              "shake": "1000ms 內 2 次 >2.5g → dizzy；cooldown 30000ms；60000ms 內第 3 次 → pretend", "asleep": "任何手勢 → touch_sleep_rub",
              "duringDim": "poke → touch_embarrassed（中斷 dim）"}

def assets():
    F = L.build_fx(); S = {}
    for pid in L.ALL_PETS:
        sid, tok = L.series_of(pid)
        if sid not in S: S[sid] = {"token": tok, "orbit": L.orbit_frames(tok), "puff": L.puff_frames("dust", tok)}
    return {"fx": F, "series": S}

def save_strip(frames, path):
    W, H = frames[0].shape[1], frames[0].shape[0]; o = L.canvas(W * len(frames), H)
    for i, f in enumerate(frames): L.paste(o, f, i * W, 0)
    Image.fromarray(o).save(path); return [W, H, len(frames)]

def ncolors(a):
    m = a[..., 3] == 255; return len(np.unique(a[m][:, :3], axis=0)) if m.any() else 0

def scene_bg(CW, CH, PX, PY):
    d = os.path.join(L.TR, "species_concept/from_ref/feeltest/assets/scenes/H1")
    im = Image.new("RGBA", (223, 446))
    for n in ("sky", "far", "mid"): im.alpha_composite(Image.open(os.path.join(d, n + ".png")).convert("RGBA"))
    fx, fy = 97 + 14, 292 + 12
    return np.array(im.crop((fx - PX, fy - PY - 1, fx - PX + CW, fy - PY - 1 + CH)))

def main():
    if os.path.isdir(OUT): shutil.rmtree(OUT)
    for d in ("fx", "series", "faces", "wear", "paws", "preview", "check"): os.makedirs(os.path.join(OUT, d), exist_ok=True)
    A = assets(); report = {"alpha_bad": [], "colors_over12": [], "face_outside_body": [], "neutral_diff": {}}
    # FX
    fxj = {}
    for k, v in A["fx"].items():
        if k.startswith("_"): continue
        sz = save_strip(v["frames"], os.path.join(OUT, "fx", k + ".png"))
        fxj[k] = {"file": f"fx/{k}.png", "frameW": sz[0], "frameH": sz[1], "frames": sz[2], "pivot": v["pivot"], "note": v["note"]}
        for f in v["frames"]:
            if not set(np.unique(f[..., 3])) <= {0, 255}: report["alpha_bad"].append(k)
            if ncolors(f) > 12: report["colors_over12"].append((k, ncolors(f)))
    mk = A["fx"]["_mirror_mask"]; Image.fromarray((mk * 255).astype(np.uint8)).save(os.path.join(OUT, "fx", "fx_mirror_mask.png"))
    json.dump(fxj, open(os.path.join(OUT, "fx", "fx.json"), "w"), ensure_ascii=False, indent=1)
    # 系列（每系 2 款自訂幀）
    sj = {}
    for sid, v in A["series"].items():
        o1 = save_strip(v["orbit"], os.path.join(OUT, "series", f"{sid}_orbit.png")); o2 = save_strip(v["puff"], os.path.join(OUT, "series", f"{sid}_puff.png"))
        sj[sid] = {"token": v["token"], "orbit": {"file": f"series/{sid}_orbit.png", "frameW": o1[0], "frameH": o1[1], "frames": o1[2], "pivot": [12, 6], "ms": 90, "note": "暈：頭頂轉星（後半圈變暗＝喺頭後面）"},
                   "puff": {"file": f"series/{sid}_puff.png", "frameW": o2[0], "frameH": o2[1], "frames": o2[2], "pivot": [8, 9], "ms": 100, "note": "撞／落地煙＋系列碎片"},
                   "pets": [p for p in L.ALL_PETS if L.series_of(p)[0] == sid]}
        for f in v["orbit"] + v["puff"]:
            if ncolors(f) > 12: report["colors_over12"].append((sid, ncolors(f)))
    json.dump(sj, open(os.path.join(OUT, "series", "series.json"), "w"), ensure_ascii=False, indent=1)
    # 每隻：面 atlas、穿戴、手仔、錨點
    anchors = {}; comps = {}
    for pid in L.ALL_PETS:
        r = L.rig(pid); C = L.Comp(r, A); comps[pid] = C; body = L.body_mask(r)
        names = list(L.FACES); frames = []
        for n in names:
            img, patch = L.face_image(r, n); frames.append(patch)
            pm = patch[..., 3] == 255
            if (pm & ~body).any(): report["face_outside_body"].append((pid, n, int((pm & ~body).sum())))
        neu = L.face_image(r, "neutral")[0]; report["neutral_diff"][pid] = int((neu != r.base).any(-1).sum())
        save_strip(frames, os.path.join(OUT, "faces", f"{pid}_faces.png"))
        save_strip(C.wear["glasses"], os.path.join(OUT, "wear", f"{pid}_glasses.png"))
        save_strip(C.wear["hat"], os.path.join(OUT, "wear", f"{pid}_hat.png"))
        pz = save_strip(C.paw, os.path.join(OUT, "paws", f"{pid}_paw.png"))
        for f in C.wear["glasses"] + C.wear["hat"] + C.paw + frames:
            if not set(np.unique(f[..., 3])) <= {0, 255}: report["alpha_bad"].append(pid)
        anchors[pid] = {"line": r.line, "series": r.series, "token": r.token, "frameSize": [r.base.shape[1], r.base.shape[0]], "pivot": list(r.pivot),
                        "baseFrame": (f"species_concept/from_ref/tuned_48/idle/{pid}_idle.png#0" if r.line == "new" else f"evo6|attach idle_01 ({pid})"),
                        "faceLayerSrc": getattr(r, "layerSrc", "tuned.json eyes/mouth"),
                        "anchors": {k: [float(v[0]), float(v[1])] for k, v in r.anchors.items()}, "headHW": int(r.headHW), "eyeDist": float(r.eyeDist),
                        "faces": {"file": f"faces/{pid}_faces.png", "order": names, "mode": "全幀 patch（同 base 一樣大），喺 transform 之前蓋落 base"},
                        "wear": {"glasses": f"wear/{pid}_glasses.png", "hat": f"wear/{pid}_hat.png", "mode": "全幀 patch，transform 之前蓋；hat 已挖空燈泡／莖位"},
                        "paw": {"file": f"paws/{pid}_paw.png", "frameW": pz[0], "frameH": pz[1], "frames": 4, "pivot": [0, pz[1] // 2], "order": ["fist", "1", "2", "3"]}}
    json.dump(anchors, open(os.path.join(OUT, "anchors.json"), "w"), ensure_ascii=False, indent=1)
    # reactions.json
    RJ = {"version": "batch3a-1", "units": {"time": "ms", "pos": "px（寵物原生像素，未放大）"}, "engineModel": ENGINE_MODEL,
          "touchRules": TOUCH_RULE, "dimRule": DIM_RULE, "faceNotes": L.FACE_NOTE, "clips": CLIPS}
    json.dump(RJ, open(os.path.join(OUT, "reactions.json"), "w"), ensure_ascii=False, indent=1)
    # 預覽 GIF（4 隻：舊 2 新 2）
    CW, CH, PX, PY = 128, 84, 60, 66; Z = 3
    bg = scene_bg(CW, CH, PX, PY)
    sheet_rows = []
    for cn, clip in CLIPS.items():
        dur = clip["dur"] * (2 if clip.get("loop") else 1); ts = list(range(0, dur, 40)); gif = []
        for t in ts:
            tt = t % clip["dur"]; row = []
            for pid in PREVIEW_PETS:
                C = comps[pid]; C.CW, C.CH, C.PX, C.PY = CW, CH, PX, PY
                fr = C.render(clip, tt); im = bg.copy(); L.paste(im, fr, 0, 0); row.append(im)
            gif.append(np.concatenate(row, 1))
        ims = [Image.fromarray(g[..., :3]).resize((g.shape[1] * Z, g.shape[0] * Z), Image.NEAREST) for g in gif]
        pal = [im.convert("P", palette=Image.ADAPTIVE, colors=255) for im in ims]
        pal[0].save(os.path.join(OUT, "preview", f"{cn}.gif"), save_all=True, append_images=pal[1:], duration=40, loop=0, disposal=1)
        # 合約表：每 clip 揀 6 個時間點
        picks = [int(clip["dur"] * k / 6) for k in range(6)]
        sheet_rows.append((cn, [np.concatenate([(lambda b, f: (L.paste(b, f, 0, 0), b)[1])(bg.copy(), comps[p].render(clip, t)) for p in PREVIEW_PETS[1::2]], 1) for t in picks]))
    # reactions_sheet_4x.png：每行一個 clip、6 個關鍵時間點、2 隻（舊 evo_still_ember＋新 H3）
    Z4 = 4; tw = CW * 2; th = CH; lab = 0
    sh = Image.new("RGB", (tw * 6 * Z4 // 2, len(sheet_rows) * th * Z4 // 2), (30, 26, 40))
    for i, (cn, cells) in enumerate(sheet_rows):
        for j, c in enumerate(cells):
            im = Image.fromarray(c[..., :3]).resize((c.shape[1] * Z4 // 2, c.shape[0] * Z4 // 2), Image.NEAREST)
            sh.paste(im, (j * tw * Z4 // 2, i * th * Z4 // 2))
    sh.save(os.path.join(OUT, "reactions_keyframes_2x.png"))
    # 4x 資產表：FX＋系列＋示範 4 隻嘅面／穿戴／手仔
    make_asset_sheet(A, comps, os.path.join(OUT, "reactions_sheet_4x.png"))
    make_faces_check(comps, os.path.join(OUT, "check", "faces_all_2x.png"))
    json.dump(report, open(os.path.join(OUT, "check", "validation.json"), "w"), ensure_ascii=False, indent=1)
    write_md(anchors)
    print(json.dumps({k: (v if k != "neutral_diff" else {"nonzero": {p: d for p, d in v.items() if d}}) for k, v in report.items()}, ensure_ascii=False)[:1500])

def _grid(items, Z, bgc=(92, 84, 136), W=1600, gap=6):
    x = y = rowh = 0; pos = []
    for a in items:
        w, h = a.shape[1] * Z, a.shape[0] * Z
        if x + w > W: x = 0; y += rowh + gap; rowh = 0
        pos.append((x, y)); x += w + gap; rowh = max(rowh, h)
    sh = Image.new("RGBA", (W, y + rowh), (*bgc, 255))
    for a, p in zip(items, pos): sh.alpha_composite(Image.fromarray(a).resize((a.shape[1] * Z, a.shape[0] * Z), Image.NEAREST), p)
    return sh
def make_asset_sheet(A, comps, path):
    items = [f for k, v in A["fx"].items() if not k.startswith("_") for f in v["frames"]]
    for sid, v in A["series"].items(): items += v["orbit"][:4] + v["puff"]
    top = _grid(items, 4)
    rows = []
    for pid in PREVIEW_PETS + ["sprout", "lumi", "C2", "F3"]:
        C = comps[pid]; r = C.r; cells = []
        for n in L.FACES:
            im = r.base.copy(); P = C.faces[n]; m = P[..., 3] == 255; im[m] = P[m]; cells.append(im)
        for P in C.wear["glasses"][1:] + C.wear["hat"][:1]:
            im = r.base.copy(); m = P[..., 3] == 255; im[m] = P[m]; cells.append(im)
        cells += C.paw
        rows += cells
    bot = _grid(rows, 4, bgc=(150, 190, 140))
    sh = Image.new("RGBA", (1600, top.height + bot.height + 12), (30, 26, 40, 255)); sh.alpha_composite(top, (0, 0)); sh.alpha_composite(bot, (0, top.height + 12))
    sh.convert("RGB").save(path)
def make_faces_check(comps, path):
    items = []
    for pid, C in comps.items():
        r = C.r; S = 64
        for n in ["neutral"] + [k for k in L.FACES if k != "neutral"]:
            if n not in C.faces and n != "neutral": continue
            im = r.base.copy()
            if n in C.faces: P = C.faces[n]; m = P[..., 3] == 255; im[m] = P[m]
            items.append(im)
    _grid(items, 2, bgc=(150, 190, 140), W=2400, gap=2).convert("RGB").save(path)

def write_md(anchors):
    J = lambda o: json.dumps(o, ensure_ascii=False)
    o = []; w = o.append
    w("# 團絨 反應 batch 3a — 觸摸 ×5 ＋ 蠢萌 ×6（兩條寵物線）\n")
    w("純 Pillow／numpy 程序生成（冇用 AI 圖）。重跑：`python3 tools/build_reactions.py`（約 30s；會清空重建 `sprites/tuanrong/reactions/`）。")
    w("源碼：`tools/reactions_lib.py`（rig／面／FX／系列幀／穿戴／參考合成器）＋ `tools/build_reactions.py`（clip 定義＋輸出）。\n")
    w("## 兩條線點覆蓋\n")
    w("| 線 | 寵物 | base 幀 | 面／錨點來源 |\n|---|---|---|---|")
    w(f"| 舊 團絨 evo（留喺遊戲） | {len(L.OLD_FORMS)} 款可穿戴形態：{', '.join(L.OLD_FORMS)} | evo6 / attach `idle_01` | `accessories/attach/<form>.json`（face／eyes／head／side／bulbPt）＋ `layers/idle_01_noface/_faceov`（sprout/radiant/soft 冇 → 用 ATTACH 眼 blob 自動拆） |")
    w(f"| 新蛋線 | {len(L.NEW_KEYS)} 隻 A1–H3 | `tuned_48/idle/{{KEY}}_idle.png` 幀 0（48×48，pivot 24,45） | `tuned_48/tuned.json`（eyes／mouth／bulbXY／outline） |")
    w("\n**全部 49 隻用同一套** clip（transform keyframe）＋ 通用 FX；每隻有自己嘅 面 patch、穿戴 patch（眼鏡／四方帽）、手仔，同埋按『系』嘅自訂幀（暈星 orbit、撞／落地 puff）。\n")
    w("### 系 → 自訂幀 token\n\n| 系 id | token | 寵物 |\n|---|---|---|")
    seen = {}
    for p in L.ALL_PETS: seen.setdefault(L.series_of(p), []).append(p)
    for (sid, tok), ps in seen.items(): w(f"| `{sid}` | {tok} | {', '.join(ps)} |")
    w("\n## 檔案\n")
    w("```\nsprites/tuanrong/reactions/\n  reactions.json          ← 全部 clip（引擎讀呢個）＋觸發規則＋引擎模型\n  anchors.json            ← 49 隻：pivot／錨點／headHW／面·穿戴·手仔檔路徑\n  fx/*.png + fx.json      ← 通用 FX 橫條（每幀同大），pivot＝落點；fx_mirror_mask.png（玻璃 mask）\n  series/<系>_orbit.png   ← 8 幀頭頂轉星（25×13，pivot 12,6）\n  series/<系>_puff.png    ← 3 幀撞／落地煙＋系碎片（17×10，pivot 8,9）＋ series.json\n  faces/<pet>_faces.png   ← 面 patch 橫條（每幀 = 全幀大細；次序見 anchors.json faces.order）\n  wear/<pet>_glasses.png  ← 2 幀（0 普通、1 反光）全幀 patch\n  wear/<pet>_hat.png      ← 2 幀（流蘇擺）全幀 patch；燈泡／莖位已挖空\n  paws/<pet>_paw.png      ← 4 幀手仔（拳／1／2／3），身側皮膚色＋自己外框，pivot 左中\n  preview/<clip>.gif      ← 4 隻並排：evo_hop、evo_still_ember（舊）｜A1、H3（新），H1 花園背景，3x，40ms\n  reactions_sheet_4x.png  ← 4x 資產表（FX、各系幀、8 隻嘅面／穿戴／手仔）\n  reactions_keyframes_2x.png ← 每 clip 6 個時間點（evo_still_ember＋H3）\n  check/faces_all_2x.png  ← 49 隻 × 全部面，肉眼檢查\n  check/validation.json   ← 驗證結果\n```\n")
    w("## 引擎模型（遊程 接）\n")
    for k, v in ENGINE_MODEL.items(): w(f"- **{k}**：{v if isinstance(v, str) else J(v)}")
    w("\n參考實作：`reactions_lib.Comp.render(clip, t)`（同 preview 一模一樣），可以照抄做 shader／canvas 版。\n")
    w("### 錨點（每隻見 anchors.json；座標 = base 幀像素）\n")
    w("| 錨點 | 意思 |\n|---|---|\n| pivot | 腳底（新 24,45；evo w/2,h-3；sprout 16,29；radiant/soft/lumi 32,61） |\n| face / eyeL / eyeR / mouth | 面中、兩眼中心、嘴 |\n| headTop | 頭殼頂（唔計燈泡／角／月／光環）— 四方帽、數字、轉星 |\n| bulb | 燈泡（帽唔遮） |\n| side_l / side_r | 身兩側（眼下 ~4px）— 笑紋、牆、鏡、黑板、手仔 |\n| center | bbox 中心（碌地 origin） |\n| chest | 嘴下（書） |\n| touch | 引擎傳入手指位置 |\n")
    w("示範（新 A1／舊 evo_hop）：")
    for p in ("A1", "evo_hop", "H3", "evo_still_ember"): w(f"- `{p}`：{J(anchors[p]['anchors'])}，headHW {anchors[p]['headHW']}")
    w("\n## 觸發規則\n")
    w("**觸摸**\n"); [w(f"- {k}：{v}") for k, v in TOUCH_RULE.items()]
    w("\n**蠢萌（dim）**：" + J(DIM_RULE) + "\n即：idle 滿 20s 之後，每 60s 擲一次 25%；兩次之間 ≥3 分鐘；每日最多 8 次。\n")
    w("## 面（face patch）\n"); w("| 名 | 用途 |\n|---|---|"); [w(f"| `{k}` | {v} |") for k, v in L.FACE_NOTE.items()]
    w("\n## Clips\n")
    w("| clip | 組 | 長度 ms | loop | origin | 觸發 |\n|---|---|---|---|---|---|")
    for cn, c in CLIPS.items(): w(f"| `{cn}` | {c['group']} | {c['dur']} | {'✓' if c.get('loop') else ''} | {c.get('origin', 'pivot')}{' +groundLock' if c.get('groundLock') else ''} | {c['trigger']} |")
    w("")
    for cn, c in CLIPS.items():
        w(f"### `{cn}` — {c['dur']}ms\n\n{c['trigger']}\n")
        if c.get("events"): w(f"- events：`{J(c['events'])}`")
        if c.get("wear"): w(f"- wear：`{J(c['wear'])}`")
        w(f"- face：`{J(c.get('face', []))}`")
        w("- FX（anchor ＋ dx,dy 偏移）：")
        for f in c.get("fx", []): w(f"  - `{f['id']}` @ {f['anchor']} ({f.get('dx', 0)},{f.get('dy', 0)}) {f['t0']}–{f['t1']}ms" + (" 固定（唔跟身）" if f.get("follow") is False else "") + (" 貼地" if f.get("atGround") else "") + (" 鏡像" if f.get("mirrorX") else "") + (f" z={f['z']}" if f.get("z") else ""))
        w("\n```json\n" + J({"body": c["body"], **({"origin": c["origin"]} if "origin" in c else {}), **({"rotStep": c["rotStep"]} if "rotStep" in c else {})}) + "\n```\n")
    w("## 驗證\n")
    w("- 全部 sprite／patch alpha 只有 0/255；每個 sprite ≤12 色；面 patch 全部喺身體 mask 入面；`neutral` 面重畫 = base（49 隻 diff 0 px）。見 `check/validation.json`。\n")
    w("## 未解決／注意\n")
    w("1. 四方帽／數字／轉星用 `headTop`：新線有角、月牙、光環嘅（F3、G3、H3、E3、A 系水滴尖）係估算位，帽會疊喺月牙／光環前面；如要逐隻微調，改 `anchors.json` headTop 即可（帽 patch 要重跑生成）。")
    w("2. 旋轉用最近鄰：碌地 45° 位會有鋸齒（已加 `rotStep:45` 建議；引擎可以改 90 減鋸齒）。")
    w("3. 對白（扮冇事、扮教授 6×3 條）只出 event `line:*`，文字由 遊策 文件提供，art 唔畫字。")
    w("4. 拉扯 hold 嘅實時拉長公式喺 trigger 欄，數值要真機調。搖晃 2.5g 閾值／搓 4 次都未上機試。")
    w("5. 舊線 sprout／radiant／soft 冇 idle noface layer → 用 ATTACH 眼 blob 自動拆面（已檢查 diff 0），但 evo6 kit 本身有現成表情，如要可以換返用嗰套。")
    w("6. 鏡入面倒影只係靜態縮細（跟面，所以會一齊眨眼），唔跟身體彈跳。")
    open(os.path.join(OUT, "REACTIONS.md"), "w").write("\n".join(o) + "\n")

ENGINE_MODEL = {
 "drawOrder": ["base = idle 幀 0（反應期間 idle 停）", "face patch（clip.face 軌，null = 原面）", "wear patch（glasses／hat，全幀，hat 已挖燈泡位）",
               "→ body transform（下）", "FX：z=back 喺寵物後、z=front 喺前；FX 本身唔縮放唔旋轉"],
 "transform": "keys {t, sx, sy, rot(度，順時針), x, y, flip(0/1), e}；缺欄沿用；段內 easing 用『下一格』嘅 e；origin = 錨點名（預設 pivot）；最近鄰取樣；rotStep 有就 snap 角度；groundLock = 每幀將最低實色行貼返 pivot.y（碌地用）",
 "easing": {"linear": "t", "in": "t²", "out": "1-(1-t)²", "inout": "2t² / 1-2(1-t)²", "outBack": "1+2.70158(t-1)³+1.70158(t-1)²", "step": "跳到下一格（到 t 先變）"},
 "fx": "{id, anchor, dx, dy, t0, t1, ms, loop(預設 true), frames(幀序列，選填), follow(預設 true：錨點跟 body 變形), atGround(y = pivot.y), mirrorX, z, move:[[ms,dx,dy]..] 線性}；id: fx_* = fx/fx.json；series_orbit / series_puff = series/<寵物系>.json；paw = paws/<pet>_paw.png",
 "anchors": "anchors.json 每隻：pivot, face, eyeL, eyeR, mouth, headTop, bulb, side_l, side_r, center, chest（base 幀像素座標）；touch = 引擎傳入手指位置",
 "events": "clip.events [{t, id}] — pat（摸頭計數）、line:*（對白，文字唔喺 art）",
}

if __name__ == "__main__":
    main()
