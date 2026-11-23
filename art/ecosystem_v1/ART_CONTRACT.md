# 活生態圈 v1 · 最少可讀美術接入契約（給遊程）

寫於 2026-11-24 Asia/Hong_Kong UTC+8。  
包路徑：`/home/box/keep/godot/hd2d-pilot-v6/ecosystem_v1_minimal_kit`  
性質：**最少可讀佔位（`minimal_readable_draft`）**，唔係最終 675 精修，唔係 Kurt 畫面驗收，未接入引擎。  
對齊：`/home/box/keep/遊策/ecosystem-v1-data-draft.json`、`master-gameplay-roadmap-2026-11-24-support.md`。  
675 基準：`/home/box/keep/godot/hd2d-pilot-v6/pet_walk_art_r4/`（64×64，sole 行 62，邊 63）。  
既有 HUD：`/home/box/keep/godot/hd2d-pilot-v6/gameplay_art_r1/SPEC.md`。

---

## ① 七區命名同穩定 id

| 穩定 id（JSON 100%） | 中文 | 類型 | 本包圖示檔名 |
|---|---|---|---|
| `garden` | 花園 | 起始 | `ui/icon_zone_garden.png` |
| `cottage_yard_work` | 屋旁基礎工位 | 起始 | `ui/icon_zone_cottage_yard_work.png` |
| `prairie_edge` | 草原邊 | 起始 | `ui/icon_zone_prairie_edge.png` |
| `zone_farm` | 農圃 | 解鎖 | `ui/icon_zone_zone_farm.png` |
| `zone_workshop` | 開放工作角 | 解鎖 | `ui/icon_zone_zone_workshop.png` |
| `zone_prairie_deep` | 草原深處 | 解鎖 | `ui/icon_zone_zone_prairie_deep.png` |
| `zone_family_wall` | 家族牆空間 | 解鎖 | `ui/icon_zone_zone_family_wall.png` |

解鎖四區嘅穩定 id **本身已帶** `zone_` 前綴；圖示檔名再加一層 `icon_zone_`，所以會出現 `icon_zone_zone_farm.png` 這種雙 `zone_`。請用表對，唔好自行改名。

切區膠囊：`ui/ui_zone_pill_bg.png`／`ui/ui_zone_pill_active.png`（160×56）。  
9-slice 邊距：`left=28, right=28, top=12, bottom=12`。控制項高度**保持 56**，只准橫向拉伸（全高膠囊，垂直拉伸會變形）。  
寵物頭像切鏡框：`ui/ui_pet_portrait_frame.png`／`ui_pet_portrait_frame_active.png`（64×64，中空透明，至少 48px 觸控）。

輕戰鬥數值（JSON `combat_stats.ids` 用中文）：

| JSON id | 檔名 |
|---|---|
| 力量 | `ui/icon_stat_power.png` |
| 身手 | `ui/icon_stat_agility.png` |
| 耐力 | `ui/icon_stat_stamina.png` |

---

## ② 細佬 A–H：series2 實測、腳底錨點、縮放同 fallback

來源（本機舊套，齊檔）：`/workspace/s2art/art-pet/sprites/series2`  
規格文件：`SERIES2_4A.md`、`forms/tuned.json`、`actions/actions.json`。  
官方標稱：畫布 **48×48**，`pivot (24, 45)`，`groundRow 46`（B 系跟 B1，腳 y=45）。alpha 0/255，Nearest 像素風。

實測（全部 34 個階段 × 5 動作 strip **齊檔**，缺檔：無（A–H 各 1–3 階＋S1／S2／S4A–H，每階 idle／walk／cry／eat／sleep 齊））：

- idle／cry／sleep：多數 form 末不透明行 **46**；**B1、H3、S4B** 為 **45**（同官方 B1 例外；注意 B2／B3 已係 46，唔好成「B 系」一刀切）。
- walk：接觸／抬腳在 `idle_sole` 同 `idle_sole-2` 之間來回（例如 44–46 或 43–45），屬步態，唔係錨點漂移。
- eat：多數會瞬間落到 `idle_sole+1`（47 或 46）——食嘢下壓，**唔好**用 eat 嘅最大 Y 去算 offset，否則 idle 會浮 1px。
- 頂裁切風險（walk 有幀 `first_opaque_row == 0`）：**A3, B2, D3, S4A**。48 畫布裝唔下部分 3 階／S4 頭頂，屬舊素材邊界；認唔出就靠頭飾標記。

### 同 675 團絨對齊（跟現行 overlay 慣例，唔跟 r4 SPEC 的 `new_offset=null`）

675 行路圖：獨立幀 **64×64**，末不透明行 **62**，足底邊 **63**，`centered=true`，`pixel_size=1`，node y **29**，工程 overlay **`offset.y = +2`**，令足底邊落到世界 Y=0。

細佬建議（同一套 Sprite3D 慣例，**唔好把 48 拉到 64**）：

| 項 | 值 |
|---|---|
| 畫布／幀 | 48×48 strip（walk／cry／eat 6 幀，idle／sleep 4 幀） |
| `centered` | `true` |
| `pixel_size` | `1`（細佬約為團絨高度 48/64 = **0.75**） |
| node y | `29`（同 675） |
| `offset.y` 多數 form | **−6**（idle 足底行 46） |
| `offset.y` 例外 | **−7**：B1, H3, S4B |
| 公式 | `offset.y = idle_last_opaque_row - 52`  （等效：`sole_edge - 24 - 29`） |

**offset.y = −6 嘅 form：** A1, A2, A3, B2, B3, C1, C2, C3, D1, D2, D3, E1, E2, E3, F1, F2, F3, G1, G2, G3, H1, H2, S1, S2, S4A, S4C, S4D, S4E, S4F, S4G, S4H

機讀詳表：`series2_measurements.json`。

### Fallback 規則

1. 優先重用本機 series2 嘅 `actions/<FORM>_{idle,walk,cry,eat,sleep}.png` 跑通。
2. 若認唔出系別，或頂裁切令人困惑：喺頭頂 billboard 疊 `kids_markers/kid_marker_{A–H}.png`（48×48，透明底；建議錨在標記底邊，放喺頭頂再上約 2px）。A 水滴、B 泡泡、C 火、D 金晶、E 辣椒、F 星、G 夜書、H 新月，色同形狀互異。
3. 再唔得先用現有小號 clip，仍然加標記。
4. 675 化正式行走套、統一片幅同精修錨點：**留最後統一精修**，今次唔做。

---

## ③ 暫時合體視覺（唔新造完整形態）

對齊 JSON `fusion.type = temporary`，完咗分開、保留原兩隻同族譜。

建議（全部用現有兩隻 sprite，唔出新身體）：

| 參數 | 建議值 |
|---|---|
| 雙影偏移 | 副影相對主影 `+6 px` X（64 空間；約 `0.09 ×` 主體寬）。主影 alpha 1.0，副影 alpha **0.45** |
| 主／副深度 | 副影畫在主影後；兩隻原始寵物邏輯上仍在場，只係合體期間改用雙影呈現 |
| tint 漸層 | 暖金 `#F2D98A` → 青 `#7EC8C3`（可用 `#E8B84A`／`#4A9E9A` 做深色）。`modulate` 按正弦在兩色之間來回 |
| tint 週期 | **1.6 s**（`t = 0.5 + 0.5 * sin(2π * time / 1.6)`） |
| tint 強度 | 乘在原色上約 **0.28–0.40**（唔要整隻變成純金／純青） |
| 光圈 | 柔和橢圓環，半徑約 **0.70 ×** 身體寬；顏色跟同一金青漸層 |
| 光圈呼吸 | alpha **0.22–0.48**，週期同樣 **1.6 s**，可同相或相位差 π |
| 開始／分開 | 淡入 0.35 s；結束淡出光圈同副影 0.40 s，然後恢復兩隻獨立本體 |
| 不做 | 新合體形態、分合骨骼動畫、永久合併刪隻 |

---

## ④ 48px 觸控同 19:9 Note10+ 安全區

| 項目 | 值 |
|---|---|
| 已認可 Low 視口 | **540×1140**（19:9） |
| Note10+ 邏輯 2× | **1080×2280**（19:9；本包 UI 按呢個比例預留） |
| 官方 `project.godot` | 仍為 **1080×1920**（唔係 19:9）。真機 Note10+ 以 19:9 安全區為準，唔好只按 1080×1920 擺底欄 |
| 安全區（540 座標） | 左右 inset **24**，上下 inset **28**（見 gameplay_art_r1 SPEC） |
| 安全區（1080×2280） | 左右 **48**，上下 **56** |
| 本包觸控 | 膠囊高 **56**（≥48）；頭像框 **64**（≥48）；圖示本身 64，若做可點圖示請向外墊到至少 48，**唔好放大貼圖** |

既有照顧 HUD 圖示源像素係 **32×32、Nearest、整數倍**。本包新圖示／道具係 **抗鋸齒暖手繪**，64／128 源。同欄混用時：本包用線性過濾或獨立 Canvas 層，**唔好對本包套 `TEXTURE_FILTER_NEAREST`**，否則邊緣會花。

---

## ⑤ 本包係最少可讀佔位，最後統一 675 精修

今次只交 support 清單裏「試稿最少可讀」嗰欄：區域標、三項戰鬥小標、切鏡掣、農圃地塊＋三階段作物、露天檯灶／郵架、可見果堆、家族牆木板／相框、細佬可認標記。

**明確留最後統一精修（本包不做）：**

- 細佬 675 化正式行走套
- 廚房煮／郵局打包專用動作
- 擴建室內同正式家具位
- §6.1 包裹、正式倉堆、合力抬、坐上大件、揮手召集
- 合體正式形態同分合動畫
- 家族牆關係線同成就框
- 新獵區（林邊、溪邊、花海、山丘）同銀金證

作物檔名 `farm_crop_stage1_sprout`／`stage2_growing`／`stage3_ripe` 係完整可替換道具（每張已含地面地塊，唔好再同 `farm_plot_empty` 疊一次）。JSON 尚未列出 `crop_stages` key，建議遊策補上後再把檔名寫進數值檔。

道具錨點：`MANIFEST.json` 每件有實測 `anchor_px`、`last_opaque_row`、`sole_edge`。建議 Sprite3D `centered=true`、`pixel_size=1`、node 放在地面 Y=0 時：

`offset.y = sole_edge - H/2`

（同 675 公式，只係 node_y=0 而唔係 29。）牆類（`family_wall_board`）可改掛喺牆局部座標，唔強制貼地。

所有新 PNG 帶 tEXt：`Category=minimal_readable_draft`。聯絡表：`contact_sheet.png`。機讀清單：`MANIFEST.json`（32 件新圖）。
