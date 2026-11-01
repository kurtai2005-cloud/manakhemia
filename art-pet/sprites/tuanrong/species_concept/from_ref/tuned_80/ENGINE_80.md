# ENGINE_80 — 《微光小圃》寵物正式版 80px（from_ref tuned_80）

Kurt [pt94u] 揀咗 80px。呢個目錄就係正式交付（64／96 只作參考）。純程序（Pillow／numpy）由 Kurt 嘅參考圖重建，冇用 AI 生圖。

## 檔案同命名
| 用途 | 路徑 |
|---|---|
| 單張靜態 | `sprites/{KEY}_80.png`（80×80 RGBA） |
| idle strip | `idle/{KEY}_idle.png`（320×80，4 幀橫排） |
| 預覽 gif | `idle/{KEY}_idle_3x.gif`（唔使入 build） |
| atlas | `atlas/pets_idle_80.png`（320×1920：每行一隻 A1→H3，4 欄＝幀 0–3）＋ `atlas/pets_idle_80.json` |
| 燈泡錨點 | `bulb_anchors_80.json` |
| 全部 metadata | `tuned.json`（名、外框色、glowTint、blink、eyesHand…） |
| 檢查圖 | `lineup_80_4x.png`、`blink_check_3x.png` |

`KEY` = 線（A–H）＋ 階（1–3），例如 `C2`。一階＝細、三階＝大，同階同體量。

## Pivot／座標
- Pivot **(40,77)**＝bottom-centre（w/2, h-3）；地線 y=77（腳最低一行），下面留 2px 透明。
- 場景（195×422 art grid）腳點 (97,292)：`drawX = 97 - 40`、`drawY = 292 - 77`。
- 一律 nearest／point filter、整數 px，唔好 sub-pixel 縮放。
- Alpha 只有 0／60／110／170／255（柔光 3 級＋實色）。燈泡柔光同光環已經畫入 sprite。

## Idle（4 幀）
| 幀 | 內容 | strip 預設 ms |
|---|---|---|
| 0 | 原 | 260 |
| 1 | 上半身（主體高度 60% 以上）落 1px（bob） | 180 |
| 2 | 原 | 260 |
| 3 | 眨眼（24 隻全部有；11 隻手放眼位：A1 A3 B2 C1 D1 D2 E3 F1 F3 G3 H3） | 140 |

- 簡單播：0→1→2→3 loop，總長 840ms（≈4.8 fps 平均）。如果引擎要固定 fps：10 fps → 3／2／3／1 tick。
- feeltest 做法（建議）：0↔1 bob，每 0.9s 一次（幀 1 佔 0.36s）；每 ~3.3s（加少少隨機）插一次幀 3（140ms）。
- F3 原圖本身係單眼 wink，幀 3 只閉返開咗嗰隻。

## 燈泡 glow 錨點
- `anchor`＝燈泡（或者星天線、自帶光）中心，座標以 sprite 左上 (0,0) 計。`frame1`＝幀 1 時嘅位置（bob 落 1px）；幀 0、2、3 同 `anchor` 一樣。
- 引擎 glow：radial，半徑 ~14px（feeltest 用 11×1.25），`additive`／`lighter`，顏色用場景 `grade.json` 嘅 `bulbGlowTint`，透明度約 0.42±0.18（2.2 rad/s 呼吸）。
- `type`：`bulb` 一般燈泡；`star` F1／G1 星天線；`own` B1／H3 自己身上嘅光源。

```json
{
 "A1": {"anchor": [40, 12], "frame1": [40, 13], "type": "bulb", "glowTint": "#a0dff8"},
 "A2": {"anchor": [43, 17], "frame1": [43, 18], "type": "bulb", "glowTint": "#a2d1f5"},
 "A3": {"anchor": [43, 9], "frame1": [43, 10], "type": "bulb", "glowTint": "#adc7f3"},
 "B1": {"anchor": [56, 22], "frame1": [56, 23], "type": "own", "glowTint": "#beecff"},
 "B2": {"anchor": [40, 6], "frame1": [40, 7], "type": "bulb", "glowTint": "#9ee8df"},
 "B3": {"anchor": [44, 9], "frame1": [44, 10], "type": "bulb", "glowTint": "#aacae2"},
 "C1": {"anchor": [21, 16], "frame1": [21, 17], "type": "bulb", "glowTint": "#fdc345"},
 "C2": {"anchor": [42, 25], "frame1": [42, 26], "type": "bulb", "glowTint": "#fcc366"},
 "C3": {"anchor": [43, 6], "frame1": [43, 7], "type": "bulb", "glowTint": "#fbc559"},
 "D1": {"anchor": [29, 20], "frame1": [29, 21], "type": "bulb", "glowTint": "#face5e"},
 "D2": {"anchor": [31, 15], "frame1": [31, 16], "type": "bulb", "glowTint": "#fad566"},
 "D3": {"anchor": [40, 9], "frame1": [40, 10], "type": "bulb", "glowTint": "#fcc04b"},
 "E1": {"anchor": [40, 18], "frame1": [40, 19], "type": "bulb", "glowTint": "#f8d598"},
 "E2": {"anchor": [42, 25], "frame1": [42, 26], "type": "bulb", "glowTint": "#fbb85e"},
 "E3": {"anchor": [26, 22], "frame1": [26, 23], "type": "bulb", "glowTint": "#fac756"},
 "F1": {"anchor": [40, 22], "frame1": [40, 23], "type": "star", "glowTint": "#ffde6e"},
 "F2": {"anchor": [41, 25], "frame1": [41, 26], "type": "bulb", "glowTint": "#f1dd94"},
 "F3": {"anchor": [24, 36], "frame1": [24, 37], "type": "bulb", "glowTint": "#fbdf8c"},
 "G1": {"anchor": [35, 22], "frame1": [35, 23], "type": "star", "glowTint": "#ffde6e"},
 "G2": {"anchor": [42, 24], "frame1": [42, 25], "type": "bulb", "glowTint": "#f9e18c"},
 "G3": {"anchor": [31, 21], "frame1": [31, 22], "type": "bulb", "glowTint": "#f5e195"},
 "H1": {"anchor": [40, 27], "frame1": [40, 28], "type": "bulb", "glowTint": "#f3d396"},
 "H2": {"anchor": [40, 14], "frame1": [40, 15], "type": "bulb", "glowTint": "#ffec96"},
 "H3": {"anchor": [41, 22], "frame1": [41, 23], "type": "own", "glowTint": "#fff0aa"}
}
```
（完整版連 `fromFoot`、逐幀：`bulb_anchors_80.json`）

## 重建
```
python3 tools/build_from_ref_tuned.py all --size 80     # sprites／idle／tuned.json／lineup／blink_check
python3 tools/build_from_ref_engine80.py               # atlas／bulb_anchors／lineup_80_4x
python3 tools/build_from_ref_feeltest.py               # feeltest（預設 80）
```
`build_from_ref_tuned.py` 入面 `EYES[80]` 係手放眼位（每隻眼一個 (cx,cy) hint），`EYE_GLOW[80]` 決定閉眼線用發光色定深色。

## 已知限制
- 細節由 JPEG 參考圖抽出：80px 已加一輪低對比雜點清理（每隻 8–41px），但大面積漸變（H3 星雲、A3 鱗）仍有少少顆粒，係刻意保留嘅質感。
- 閉眼係 1px「︶」線，發光眼（B2 D1 D2 E3 G3 H3）用眼本身最光嘅色做細縫。
