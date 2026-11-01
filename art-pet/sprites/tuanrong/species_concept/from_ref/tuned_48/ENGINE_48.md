# ENGINE_48 — 《微光小圃》寵物正式版 48px（from_ref tuned_48）

Kurt [pt98u]「用舊既size，同新寵好似有d圖唔太仔細crack左咁」→ 由 80px 改返**舊寵尺寸 48×48**，並且由頭做一次真正嘅像素清理。純程序（Pillow／numpy），冇用 AI 生圖。取代 `tuned_80/ENGINE_80.md`（80 留作參考）。

## 點解係 48×48、pivot (24,45)
- 舊寵（`sprites/tuanrong/evo6`）喺遊戲入面係 **1x 原尺寸**畫（render.js `drawImage` 用 sprite 原本 sw／sh），pivot 一律 bottom-centre (w/2, h-3)，腳最底一行 = h-2：
  | 舊型態 | canvas | pivot | 實色 px（量度） |
  |---|---|---|---|
  | evo_sprout | 32 | (16,29) | — |
  | evo_hop | 38 | (19,35) | 621 |
  | evo_guard_* | 44 | (22,41) | 659–832（平均 ~735） |
  | evo_still_* | 48 | (24,45) | 838–1091（平均 ~900） |
- 新寵統一用最大嗰格 **48×48、pivot (24,45)、地線 y=46**（同 evo_still 一模一樣），咁引擎唔使逐階換 frame size；體量就逐階對返舊寵：
  - 一階（juvenile）≈ evo_hop：~600–630 px
  - 二階（adult）≈ evo_guard：~700–740 px
  - 三階（elder）≈ evo_still：~860–900 px
  - 實數：A1 629 A2 734 A3 900 B1 597 B2 738 B3 883 C1 610 C2 717 C3 893 D1 603 D2 707 D3 881 E1 614 E2 722 E3 880 F1 603 F2 718 F3 890 G1 603 G2 715 G3 887 H1 607 H2 710 H3 864
- 所以同一隻場景入面，新寵同舊寵一樣大（見 `scene_old_vs_new*.png`）。

## 檔案同命名
| 用途 | 路徑 |
|---|---|
| 單張靜態 | `sprites/{KEY}_48.png`（48×48 RGBA） |
| idle strip | `idle/{KEY}_idle.png`（192×48，4 幀橫排） |
| 預覽 gif | `idle/{KEY}_idle_3x.gif`（唔使入 build） |
| atlas | `atlas/pets_idle_48.png`（192×1152：每行一隻 A1→H3，4 欄＝幀 0–3）＋ `atlas/pets_idle_48.json` |
| 燈泡錨點 | `bulb_anchors_48.json` |
| 全部 metadata | `tuned.json`（名、外框色、體量、眼、嘴／腮、熔岩脈、清理統計…） |
| 檢查圖 | `lineup_48_6x.png`、`before_after_80_vs_48_4x.png`、`crack_check_8x.png`、`blink_check_6x.png`、`scene_old_vs_new.png`、`scene_old_vs_new_petarea_4x.png`、`crack_report.json` |

`KEY` = 線（A–H）＋ 階（1–3）。sprite80 patch 嘅 `tiers {juvenile:1, adult:2, elder:3}` 直接沿用。

## Pivot／座標
- Pivot **(24,45)**；腳最低一行 y=46，下面留 1px 透明（同舊 evo 一樣）。
- 場景（195×422 art grid）腳點 (97,292)：`drawX = 97 - 24`、`drawY = 292 - 45`。
- 一律 nearest／point filter、整數 px、**1x 原尺寸**畫（同舊寵），唔好再縮放。
- **Alpha 只有 0／255**。80 版畫入 sprite 嘅柔光已經拎走（細尺寸會變成霧／裂紋），燈泡光暈全部交返引擎畫。

### 由 80 改 48，引擎要改嘅數
| 設定 | 80 | 48 |
|---|---|---|
| frameSize | 80 | **48** |
| pivot | [40,77] | **[24,45]** |
| atlas | pets_idle_80 | **pets_idle_48** |
| bulb glowRadius | 14 | **~9**（feeltest：11×48/64≈8） |
| 影 shadowHalfW | — | **~13**（舊寵用 `efs*0.36`） |

## Idle（4 幀）
| 幀 | 內容 | ms |
|---|---|---|
| 0 | 原 | 260 |
| 1 | 上半身（主體高度 60% 以上，`idleCut`）落 1px（bob） | 180 |
| 2 | 原 | 260 |
| 3 | 眨眼（24 隻全部有） | 140 |
- 播法同 80：0→1→2→3 loop，或者 0↔1 每 0.9s bob、每 ~3.3s 插幀 3。
- 眼：舊寵風格 4×4 深色眼＋右上白點；火／岩系用發光眼（閉眼變發光 ︶）；F3 原圖 wink，幀 3 只閉開咗嗰隻。

## 燈泡 glow 錨點
- `anchor`＝燈泡（或星天線、自帶光）中心，sprite 左上 (0,0) 計；`frame1`＝幀 1（bob）位置；幀 0／2／3 同 `anchor`。
- 引擎 glow：radial，半徑 ~9px，`additive`／`lighter`，色用場景 `bulbGlowTint`（或下面 `glowTint`），透明度 0.42±0.18。
- `type`：`bulb` 一般燈泡（5×5 燈泡＋短莖，固定喺頭頂上 ~5px）；`star` F1／G1 星天線；`own` B1／H3 自帶光（H3 光環）。

```json
{
 "A1": {"anchor": [24, 9], "frame1": [24, 10], "type": "bulb", "glowTint": "#a0dff8"},
 "A2": {"anchor": [26, 11], "frame1": [26, 12], "type": "bulb", "glowTint": "#a2d1f5"},
 "A3": {"anchor": [26, 6], "frame1": [26, 7], "type": "bulb", "glowTint": "#adc7f3"},
 "B1": {"anchor": [25, 18], "frame1": [25, 19], "type": "own", "glowTint": "#beecff"},
 "B2": {"anchor": [24, 4], "frame1": [24, 5], "type": "bulb", "glowTint": "#9ee8df"},
 "B3": {"anchor": [26, 13], "frame1": [26, 14], "type": "bulb", "glowTint": "#aacae2"},
 "C1": {"anchor": [13, 19], "frame1": [13, 20], "type": "bulb", "glowTint": "#fdc345"},
 "C2": {"anchor": [25, 16], "frame1": [25, 17], "type": "bulb", "glowTint": "#fcc366"},
 "C3": {"anchor": [26, 13], "frame1": [26, 14], "type": "bulb", "glowTint": "#fbc559"},
 "D1": {"anchor": [18, 17], "frame1": [18, 18], "type": "bulb", "glowTint": "#face5e"},
 "D2": {"anchor": [19, 14], "frame1": [19, 15], "type": "bulb", "glowTint": "#fad566"},
 "D3": {"anchor": [24, 4], "frame1": [24, 5], "type": "bulb", "glowTint": "#fcc04b"},
 "E1": {"anchor": [24, 12], "frame1": [24, 13], "type": "bulb", "glowTint": "#f8d598"},
 "E2": {"anchor": [25, 16], "frame1": [25, 17], "type": "bulb", "glowTint": "#fbb85e"},
 "E3": {"anchor": [15, 12], "frame1": [15, 13], "type": "bulb", "glowTint": "#fac756"},
 "F1": {"anchor": [24, 14], "frame1": [24, 15], "type": "star", "glowTint": "#ffde6e"},
 "F2": {"anchor": [25, 16], "frame1": [25, 17], "type": "bulb", "glowTint": "#f1dd94"},
 "F3": {"anchor": [14, 11], "frame1": [14, 12], "type": "bulb", "glowTint": "#fbdf8c"},
 "G1": {"anchor": [21, 13], "frame1": [21, 14], "type": "star", "glowTint": "#ffde6e"},
 "G2": {"anchor": [25, 16], "frame1": [25, 17], "type": "bulb", "glowTint": "#f9e18c"},
 "G3": {"anchor": [19, 12], "frame1": [19, 13], "type": "bulb", "glowTint": "#f5e195"},
 "H1": {"anchor": [24, 18], "frame1": [24, 19], "type": "bulb", "glowTint": "#f3d396"},
 "H2": {"anchor": [24, 10], "frame1": [24, 11], "type": "bulb", "glowTint": "#ffec96"},
 "H3": {"anchor": [25, 14], "frame1": [25, 15], "type": "own", "glowTint": "#fff0aa"}
}
```
（完整版連 `fromFoot`、逐幀 `perFrame`：`bulb_anchors_48.json`）

## 像素清理做咗乜（對應「唔仔細／crack 咗」）
1. 每隻 ≤12 色（H3 10 色）調色盤，weighted-mode 縮圖（唔會 blend 出 JPEG 雜色）。
2. 3 輪清理：填 ≤6px 洞、刪 <6px 孤島、刪 1px 刺、補缺口、併 1–2px 雜色塊；最後一輪再清單點異色。
3. 封閉外框：1px 深色外框（亮黃／火焰邊用同色深一截嘅選擇性外框）；左上光、右下內邊 1px 陰影（<3px 短段唔畫，避免變雜點）。
4. D／E 線熔岩：岩身變平色，裂紋改畫成 **1px 有意圖嘅發光脈**（中間 #fff0a0、兩頭 #ffa838，3–7px 長），每隻 3–4 條；火焰只保留頂部。
5. 臉跟舊寵：手畫眼、‿ 細嘴、3×2 粉紅腮（岩／發光眼角色唔加腮）。
6. 自動檢查（`tools/px48_check.py`）：80 直接縮 48 → 雜點＋斷口＋洞＋碎件 共 547、碎色 212、半透明 1684 px；新 48 → 3、碎色 42、半透明 0。逐隻數字喺 `crack_report.json`／`before_after_80_vs_48_4x.png`。

## 重建
```
python3 tools/build_from_ref_px48.py        # 讀 tuned_80／ref → sprites／idle／tuned.json
python3 tools/build_from_ref_px48_out.py    # atlas／bulb_anchors／gif／lineup／before_after／crack_check／blink_check／scene_old_vs_new
python3 tools/build_from_ref_feeltest.py    # feeltest（預設 48；48／64／80／96 輪換）
```
眼位由 80 版眨眼幀差計（`tools/from_ref_eyes80.json`），每隻嘅眼款、燈泡款、熔岩脈數喺 builder 頂部 `CFG／EYE／LAVA`。

## 已知限制
- G3、F3、H2 燈泡要避開月／角，莖長 3–5px；G1 星天線同頭之間得 1–2px 莖。
- H3 光環係程序畫嘅橢圓（原圖光環縮細會斷），魔杖已拎走。
- 48 係細尺寸：B3 珊瑚、A3 鱗紋、H3 星雲只保留大色塊，細紋簡化咗（刻意）。
- 剩低自動檢查 3 個位都係刻意設計（光環邊／星耳尖），見 `crack_check_8x.png`。
