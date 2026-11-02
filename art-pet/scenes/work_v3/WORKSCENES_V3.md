# 微光小圃・工作場景 V3-A（第 8 批）

來源：`docs-gdd/family-work-scenes-v1.md` §2.1 工作場景（Kurt 已批）。規格跟 V3-A（金光海軍藍磨砂＋1.5px 金幼線、@3x 烘焙光影＋粒子、HD-2D）。全部 procedural Pillow/numpy，冇用 AI 圖。
入口：`scenes/work_v3/workscenes_v3.json`。驗證：`python3 tools/validate_workscenes_v3.py` → `validation.json`。

## 重建
```
PYTHONDONTWRITEBYTECODE=1 python3 tools/build_workscenes_v3.py all     # 場景＋sprite＋UI 部件＋mockup＋json（大約 1 分鐘，固定 seed）
PYTHONDONTWRITEBYTECODE=1 python3 tools/preview_workscenes_v3.py       # 預覽 → $GD_WORKSCENES_V3（預設 /workspace/game-design/workscenes_v3/）
PYTHONDONTWRITEBYTECODE=1 python3 tools/validate_workscenes_v3.py
```
Helper：`ws3_px.py`（像素畫筆、HD-2D 色相陰影、紋理）、`ws3_scenes.py`（4 個場景嘅層）、`ws3_sprites.py`（道具、擺設、帽、icon、clip、粒子）。

## GDD 清單 → 檔案
| GDD | 檔案 |
|---|---|
| 5 張背景（郵局／花園／瞭望台日／瞭望台夜／廚房） | `<scene>/` 1x 層＋`x3/` @3x 層＋`grade.json`／`palette.json`／`lut.png` |
| 8 個可撳道具動畫（每場景 2 個，4–6 幀） | `props/<job>_<prop>@3x.png`（＋1x，星／燈有 `_glow@3x`）。印章 4 行＝4 隻墨色 |
| Lv3 多 1 件擺設 | `deco_lv3/<job>@3x.png`：銅磅＋包裹／雀仔浴盆／渾天儀／麵包籃＋香草 |
| Lv5 職業帽 | `hats_lv5/<job>_<S|M|L>@3x.png`（12 頂） |
| 24 個工作 clip | `clips/<job>_<S|M|L>_<loop|done>@3x.png`：loop 8 幀 110ms；done 4 幀 140ms。分 back／front 兩行，有啲有 `_glow` |
| 8 個成品 icon 48px | `icons/<name>@3x.png`（48×48）＋`_glow@3x`（72×72） |
| 完成彈出／今日成品／今日放假 | `ui/*@3x.png`（底圖冇字，字由 runtime 畫）＋`mockups/` |

## 圖層同合成
- 畫布：1x 圖層 223×446（美術 195×422，四邊留 14／12px）；@3x 圖層 669×1338，裁切位 (42,36) → 畫面 585×1266。座標換算 `L3(x,y)=((x+14)*3,(y+12)*3)`；寵物腳底 1x (97,300)。
- 合成次序：sky → 天空道具（瞭望台星）→ far → haze_far → mid＋道具／擺設（按 y 排）→ mist → 寵物影 → petLight → clip back → 寵物（＋帽）→ clip front → fore → ×tod.mul → ×lightmap → +light_add → emissive／bloom → 道具 glow＋clip glow → 粒子 → fog → 裁切 → vignette → UI v3。
- 時段：郵局、花園、廚房用 `grade.json#tod`：dawn 5–8、day 8–17、dusk 17–20、night 20–5，600ms 漸變。瞭望台用日（06–18）同夜（18–06）兩張圖，crossfade 1200ms；夜更 21–05 一定係夜版。
- 粒子：沿用 `scenes/hd2d_v3/fx/particles_v3@3x`（dust／firefly／gold／mote／petal／pollen）同 `fx_glow_v3@3x`。新加 `fx/particles_work@3x`：paper／twinkle／steam／ember／splash／sparkle／spice。
- Sprite 嘅 alpha 只有 0／255；glow、lightmap、bloom、mist、vignette 呢類光影層用真 alpha。

## 體型 S/M/L（自定）
GDD 冇講點分。我按 compose_pet 嘅 bbox max(w,h) 分：S ≤32（7 個形態）、M ≤40（37 個）、L >40（15 個）。
- clip 嘅 `petTransform` 逐幀記 dx／dy／sx／sy／rot，以腳底做 pivot。
- 帽嘅底部中點對準雙眼中點 x，y＝headTop＋5px（1x），跟 clip 一齊郁。

## petGlow
跟 `ui/kit_hd2d_v3/layout_hd2d_v3.json#petGlow`：awake 1、sleepy .6，sleep／sleepClip／dreamEnter／dreaming 0。淡出 600ms easeInQuad；淡入 400ms easeOutQuad，再加 150ms pulse 1→1.15→1。
- 會乘 petGlow：`grade.json#petLight`（腳下光池）、寵物 rim、clip `_glow`（寵物身邊光點）。
- 唔受影響：場景燈（窗、吊燈、爐火、月亮）、道具 glow（星、燈）、瞭望台 done 嗰盞小燈（屬場景燈）。
- 測試記錄喺 `petGlow.test`：petGlow 由 1 變 0，只有寵物附近嘅像素變，窗同爐火嘅差值係 0。

## 數值
純美術改動。薪金、機率（郵局委託信 25%、花園裝飾 15% 等）、夜更上限 8、心情、親密度全部照 5b 原數。撳道具只係視覺效果（`affectsGame=false`）。

## Mockup（疊 UI v3）
ws_post、ws_garden（Lv3）、ws_tower_day、ws_tower_night（夜更＋Lv3＋Lv5 帽）、ws_kitchen（Lv3＋Lv5）、ws_done_popup（出糧彈窗：委託信）、ws_dayoff（今日放假）、ws_garden_night（夜色＋sleepy petGlow .6）。
版面同撳得嘅範圍喺 `layout`／`hits`；文字記錄喺 `mockups/texts.json`（全部 ≥18px，對比 ≥4.5）。

## 已知問題
- S/M/L 係自己定嘅分法，Kurt 可以再調。
- 郵局 Lv3 個銅磅細細個，望落有少少似鐘。
- 道具 glow 同 clip glow 係預烘 sheet，runtime 要用 lighter blend。
