# 遊美 art r1 接入規格（工作規格，非 Kurt 畫面接受）

日期：2026-11-16 20:17 HKT；r1.1 修正 2026-11-16 20:25 HKT（Asia/Hong_Kong）  
性質：**首輪可接素材與建議版面**，不是 Kurt 視覺接受、不是遊戲已實裝證明、不是新渲染、不是已鎖定的全遊戲 UI 標準。可逆。  
官方共享 GAPS：`/home/box/keep/遊程/GAPS_vc27_gameplay_r1.md`（本包只追加「遊美 art r1 接入」節；唔改遊程正文）。  
本包唔改場景、凍結基準、PC、repo／shader、APK，亦唔編 need 數值。UI 接入由遊程管：`godot_hd2d_v6/gameplay/m1_care.gd`（M1CareUi）；本包唔改工程碼。

參考視口：已認可 Low 19:9 截圖 **540×1140**。官方 `project.godot` 仍為 1080×1920（剛好 2× 此視口）。

## 1. 源像素／顯示／觸控（務必分開）

舊檔名 `@3x` **唔等於** 96px。本包已核：重用嘅 kit／M1 icon 真實像素全部係 **32×32**。

| 元件 | 源像素（檔案） | 540×1140 顯示（×2 Nearest） | 1080×1920 顯示（×4 Nearest） | 建議觸控（540） | 建議觸控（1080） |
|---|---|---|---|---|---|
| 照顧／欣賞圖示 | 32×32 | 64×64 | 128×128 | — | — |
| 按鈕底板／合成掣 | 40×40 | 80×80 | 160×160 | **96×96**（顯示仍 80；向外墊觸控，**唔好放大貼圖**） | **192×192**（顯示仍 160；同樣只墊觸控） |
| need 安靜框／合成泡泡 | 48×48 | 96×96 | 192×192 | 非主要觸控；若要點散，跟顯示框即可 | 同左 ×2 |
| 可選 9-slice 面板 | 24×24 | 按需整數倍 | 按需整數倍 | — | — |

- 過濾：**Nearest**（`TEXTURE_FILTER_NEAREST`），只准 **整數倍** 縮放。
- 淡出：用 `CanvasItem.modulate`（或等效）做 3 秒淡出；**唔好把淡出烘焙入貼圖或 3D 場景**。遊程接線。
- 觀察／欣賞模式：**隱藏全部**照顧掣、欣賞掣、need 泡泡。退出方式由遊程定；本包不另做退出專用圖。
- 底板同圖示分開提供，亦提供已合成 normal／pressed／disabled，遊程可揀組合或用合成檔。

## 2. 建議版面（540×1140 座標，可逆，非全遊戲標準）

安全區：左右 inset 24、上下 inset 28。

| 元件 | 位置（左上，540 座標） | 顯示大小 | 備註 |
|---|---|---|---|
| 四照顧掣（餵、淋水、執屎、摸） | 起點 (98, 1032)，間距 8，由左至右 | 各顯示 80×80，觸控 96×96 | 底欄置中，落在前景草皮。淋水預覽用 disabled 表示 **inactive／pending mapping**，不可聲稱功能已完成。第4掣係手掌「摸」，對應現有 pet/touch hook（不是玩、不是食物）。 |
| 欣賞 | (436, 28) | 80×80 | 右上天空，低干擾 |
| need 泡泡（示範 want 食） | 追隨寵物頭頂；預覽用頭頂上方、略偏右（避開日景掛燈） | 96×96 | 由遊程做頭頂 billboard／overlay；本預覽係靜態合成 |

預覽裏嘅中文標籤、尺寸註記、觸控虛線 **只存在於 `*_guides.png`／表**，**無烘焙入按鈕或泡泡 PNG**。

## 3. Godot 接入建議（唔寫入 repo）

- `TextureButton` 或 `TextureRect` + 獨立觸控區；`ignore_texture_size`，`custom_minimum_size` 跟觸控列。
- 直向 19:9 anchor：底欄 `bottom` 置中；欣賞 `top-right`。
- 圖層放 UI Canvas，唔改 vc27 3D 場景同凍結基準。獨立工作副本接 Sim／Save 屬遊程。
- need 優先用 **32×32 M1 icon**；可選套本包安靜框。**今輪唔搬** 主線世界 64×56 舊 V3-A 框。96×72 dream 泡泡亦唔等同 need。

## 4. 檔案語意

可接根目錄：`/workspace/gameplay_art_r1/assets/`

**操作掣（唔好用 need_* 當操作 icon）**

| 行為 | 圖示來源 | 合成掣（normal／pressed／disabled） |
|---|---|---|
| 餵 | 重用 kit `feed`（飯糰）`icons/icon_care_feed_32.png` | `buttons/btn_care_feed_*.png` |
| 淋水 | 重用 kit `water`（灑水壺）`icon_care_water_32.png`。**素材保留；狀態 inactive／pending mapping**（遊程：need 效果未定暫唔接）。不可聲稱已完成。預覽以 disabled 示未接。唔由美術決定 need 數值。 | `btn_care_water_*.png`（三態齊，含 disabled） |
| 執屎 | **新畫** 三層糞形＋鏟子 `icon_care_poop_32.png` | `btn_care_poop_*.png` |
| 摸 | **新畫** 張開手掌 `icon_care_pat_32.png`。對應現有 pet／touch hook。遊程：玩無明確玩家入口，本掣**唔代表玩**。r1 曾誤用 kit 粉紅糖果，已撤下，唔再食物硬映射。現成 `need_pet` 係「想摸」氣泡、唔當操作掣；`ev_play` 係球／事件，本掣改用手掌。 | `btn_care_pat_*.png` |
| 欣賞 | **新畫** 安靜眼睛 `icon_admire_32.png` | `btn_admire_*.png` |

**need_*（想要氣泡，不是操作掣）**

| id | 語意 | 32px 原圖（重用 M1） | 可選合成泡泡（安靜框＋原 icon） |
|---|---|---|---|
| need_eat | 想食 | `icons/icon_need_eat_32.png` | `bubbles/bubble_need_eat.png` |
| need_play | 想玩 | `icon_need_play_32.png` | `bubble_need_play.png` |
| need_sleep | 想瞓 | `icon_need_sleep_32.png` | `bubble_need_sleep.png` |
| need_pet | 想摸 | `icon_need_pet_32.png` | `bubble_need_pet.png` |

框：`frames/bubble_need_quiet_48.png`（低干擾，可選）。遊程可只用 32px icon 做 billboard。  
底板：`frames/btn_plate_40_{normal,pressed,disabled}.png`。  
可選九宮格：`frames/panel_9slice_24.png`，建議 slice margin **6px**。SVG 只係 chrome 參考，像素正本係 PNG。

## 5. 自檢（美術預覽，非實裝）

合成底圖：日 `vc27_continuity_verify/caps/day_low__GODOT_LOW.png`；夜 `hd2d-vc27-rear-ground-r1/caps/night_still__GODOT_NIGHT.png`（皆已認可 540×1140，無新 GPU 渲染）。

- 文字：guides 註記可讀；正式 UI 預覽為 icon-only。
- 唔遮主寵臉、小屋發光窗、左燈柱、頭頂掛燈、燈串。
- 夜景保留暖燈焦點；底板用暗暖色＋暗金褐邊，唔同燈搶光。
- 觀察預覽：`previews/layout_observe_hidden_*.png`（只留說明字，UI 全隱藏）。

## 6. 本包不做／缺項

- 郵局、廚房、一鍵總結卡、圖鑑、傢俬、狩獵、M2、expr／mood／事件 icon：唔入首輪。
- 淋水／玩等**數值**不在本包，美術唔自行決定 need 數值。淋水功能未完成（mapping pending）。
- r1 之 kit 糖果「玩／摸」圖已撤；檔名 `icon_care_play_32`／`btn_care_play_*` 已刪，改為 `icon_care_pat_32`／`btn_care_pat_*`。
- 長按地面執屎無另畫手勢圈（可重用執屎 icon 作提示）。
- 無退出觀察專用圖。
- 未接引擎、未改場景、未出 APK。Kurt 尚未對呢套 UI 做畫面接受。
