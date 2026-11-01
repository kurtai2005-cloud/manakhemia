# 《微光小圃》HD-2D UI Kit（production，part 1）

- 風格：`ui/style_ref/hd2d/`（Kurt 揀「UI 用 HD-2D」）：深藍玻璃面板＋金邊＋柔光（bloom 已 bake 入 PNG）、圓章掣、可愛小動物 icon（有表情，保留）。
- 全部純 Pillow/numpy 程序生成，冇 AI 圖。重跑：`cd art-pet && python3 tools/build_ui_kit_hd2d.py && python3 tools/build_ui_kit_hd2d_mock.py && python3 tools/validate_ui_kit_hd2d.py`
- 目標：Canvas2D，冇 shader；畫面格 195×422 art 單位；資源 @3x（1 art＝3 px），另有 @2x。

## 0. 檔案
| 路徑 | 內容 |
|---|---|
| `atlas/ui_hd2d@3x.png/.json`、`@2x` | 143 個 frame（面板、掣、圓章、HUD、dock、紅點、toast、泡泡、標題帶、控件、FX、5a stub）＋63 個預渲染字牌 `lbl_*`（part 2 數） |
| `atlas/icons_hd2d@3x.png/.json`、`@2x` | 56 個 icon（24 art 方格，含光暈 pad）；`icons/ic_<名>@3x.png` 單張版 |
| `fonts/font_px7@1x.png`、`font_px7_ol@1x.png` | 5×7 像素數字字（1x 原生，整數倍 nearest 放大）；`_ol`＝1px 深描邊版 |
| `fonts/font_gold@3x.png`、`font_round@3x.png`、`fonts_hd2d.json` | 金色標題數字（Cinzel Black 12 art）、紅點數字（Fredoka 6.5，白字玫瑰描邊）＋ metrics（adv、yoff、lineH、base） |
| `layout_hd2d.json` | 主畫面所有座標（art 單位）＝本文 §1 |
| `mockups/home_3x.png`、`popup_3x.png`、`settings_3x.png`、`journal_dex_3x.png`、`stubs_4b_5a_3x.png`、`levelup_3x.png`（part 2） | 3x mockup（全部由 atlas 拼出，唔係另外畫） |
| `mockups/*_smallphone_360w.png` | 細機 1x 預覽（360px 闊，約 1.85 px/art） |
| `overview_3x.png` | 全 kit 總覽板 |
| `MOTION_HD2D.md` | 6 種動態＋SFX 對照＋§10 升級／list 邊緣 |
| `reskin_4b/` | 4b 屋仔 UI 重砌包＋`reskin_map.json`＋前後對比圖（§6） |
| `validation.json` | validator 結果 |

## 1. 佈局（slim 版，最終高度）
**頂部 UI 帶＝38 art（0–38）；花園＋寵物＝310 art（38–348，佔 73.5%）；底部 UI 帶＝74 art（348–422，其中 dock＝34）。**

| 元素 | 位置（art） | sprite |
|---|---|---|
| 名牌 | (3,3) 92×20；頭像圓 cx13 cy13 d19；名 serif 9；階段 tag (62,4.4) 24×10；exp 條 (25,15.2) w66 h5 | `nameplate`＋`med19_paper`＋`stage_tag`＋`exp_trough`/`exp_fill`/`exp_gem_on`/`exp_gem_off` |
| 貨幣 chip ×2 | (99,5) w44、(151,5) w38，h16；icon d16 左凸；「＋」在右端 | `chip`＋`chip_plus`/`chip_plus_p`；數字 `px7_ol` ×3 |
| 需要值 ×4 | y26 h10，x＝3＋i×47.5，w45.5；左邊 d11 icon 圓章 | `need_trough`＋`med11_navy`＋`need_fill_feed`/`need_fill_mood`/`need_fill_clean`/`need_fill_energy`；<20% 換 `need_fill_low`；端點 `bar_tip` |
| 右欄 | 委託 d22 (180,52) 字 y65.5；信件 d20 (180,81) 冇字；屋仔 d24 (178,104) 字 y120.5（＝4b 原位） | `med22_navy`、`med19_navy`（d20 用 med19 放大 1.05 或 `med20_pri`）、`med24_navy`＋`red_dot`/`red_dot_num` |
| toast | (31.5,44) w132 h18 | `toast`＋`toast_wing_l`/`toast_wing_r`＋icon 圓章 `med16_pri` |
| 寵物泡泡 | 例 (56,236) w60 h20 | `bubble`（9-slice）＋`bubble_tail`；諗緊＝`thought_dots` |
| 動作掣 ×4 | d28 cy362，cx＝26＋i×47.7；字牌 28×10 y372 | `med28_pri`/`med28_rose`/`med28_sec`/`med28_violet`（＋`_p`）、停用 `med28_dis`；字牌 `label_plate`＋`lbl_act_*` |
| dock | (3,386) 189×34；5 tab | `dock_bar`（3h）＋`dock_div`＋`dock_gem` |
| dock tab 未選 | d18 cy398，icon 14，字 y414 | `med18_navy_in`＋`lbl_tab_*` |
| dock tab 已選 | d24 cy393，icon 19，背後光柱 | `med24_pri`＋`dock_pillar`＋`lbl_tab_on_*` |
| 彈窗 | (19,104) 157×148；標題帶 y95；✕ 右上內 (−11,+11)；列 (9,18) 139×27 gap30；主掣 84×20 底 −28 | `panel_glass`＋`plaque`＋`plaque_tail_l`/`plaque_tail_r`＋`plaque_gem`＋`close`＋`panel_inset` |

細機：mockups 360w 版（1 art≈1.85 px）字仍然清楚；正文最細 7 art＝13 px。

## 2. Audit 元素 → sprite 對照
| Audit 元素（UI-audit.md） | sprite／狀態 | 尺寸（art） | 動態 | SFX |
|---|---|---|---|---|
| 頂 bar／名牌（P0-2、P0-4 修疊位） | `nameplate`、`stage_tag`、`med19_paper` | 92×20 | exp 滿＝`fx_sweep` 掃一次 | — |
| 貨幣 chip（P0-6 單一貨幣都得） | `chip`、`chip_plus` 常態／`chip_plus_p` 按下 | h16 | 數字 +N：§MOTION 5 toast 同步彈 1.15× | `sfx_ui8_coin` |
| 需要條（P1-4 加 icon） | `need_trough`＋`need_fill_*`；低值 `need_fill_low` | 45.5×10 | 補滿閃一閃（`fx_sweep`） | — |
| 進度／exp 條 | `prog_trough`＋`prog_fill_teal`/`prog_fill_gold`；`exp_trough`＋`exp_fill` | h6／h5 | fill 寬度 ease-out 300ms | — |
| 底 dock 5 tab（P0-2） | `dock_bar`、`med18_navy_in` → `med24_pri`＋`dock_pillar` | 189×34 | MOTION 1 tab switch | `sfx_ui8_tab_switch_a`/`sfx_ui8_tab_switch_b` 交替 |
| 主掣 3 級（P1-1） | 主 `btn_pri`、次 `btn_sec`、警告 `btn_rose`、特別 `btn_violet`、停用 `btn_dis`；按下 `_p` | h20（3h，任意闊）；細版 `btn16_pri` 等 h16 | MOTION 3 button press | `sfx_ui8_btn_press_a`/`sfx_ui8_btn_press_b`；主掣確認 `sfx_ui8_confirm`；停用撳 `sfx_ui8_error` |
| 圓章掣（行動、右欄） | `med28_*`、`med24_*`、`med22_navy`、`med30_pri`、`med34_pri` ＋ `_p` | d16–34 | MOTION 3 | `sfx_ui8_tap_a`/`sfx_ui8_tap_b` |
| 彈窗／面板（P1-1 一套樣式） | `panel_glass`（9-slice）、`panel_glass_plain`（sheet）、`panel_paper`（羊皮紙版）、`panel_inset`/`panel_inset_sel`、`banner_event`（事件 banner ≤1/6 畫面，P0-4） | 任意 | MOTION 2 popup | `sfx_ui8_popup_open`/`sfx_ui8_popup_close` |
| 關閉 ✕（一律右上內） | `close`／`close_p` | d15 | press | `sfx_ui8_cancel` |
| 委託列 | `panel_inset`＋`med19_paper` icon＋`prog_trough`＋`star_on`；完成 `panel_inset_sel`＋`stamp_done` | 139×27 | 完成蓋印：`stamp_done` scale 1.6→0.9→1，160ms | `sfx_ui8_confirm` |
| toast（P0-1 隊列） | `toast`＋`toast_wing_l`/`toast_wing_r` | h18 | MOTION 4 | `sfx_ui8_toast_in` |
| 紅點（P0-1「📬 2」） | `red_dot`、`red_dot_num`＋`round` 字 | d5.7／d8.3 | MOTION 5 wiggle | `sfx_ui8_badge_wiggle`（冷卻 ≥5s） |
| icon（P1-4 統一） | `atlas/icons_hd2d`；每個小遊戲專屬：`ic:mg_tease` `ic:mg_stardust` `ic:mg_leaf` `ic:mg_hide` `ic:mg_firefly` | 24（顯示 11–24） | — | — |
| toggle | `toggle_track_on`/`toggle_track_off`＋`toggle_knob_on`/`toggle_knob_off` | 26×13 | knob 滑 120ms ease-out-back | `sfx_ui8_toggle_on`/`sfx_ui8_toggle_off` |
| 數字字 | `px7`（細數 1/2、22:30）、`px7_ol`（HUD 數）、`gold`（大數、等級）、`round`（紅點） | px7＝7 art 高 | — | — |
| 卡框（圖鑑／收藏／家具） | `card`、`card_sel`、`card_locked`＋`card_qmark`＋`ic:lock`、底光 `card_spot` | 36×44 9-slice | 選中：金框光 fade 150ms | `sfx_ui8_tap_a` |
| 子分頁（手帳 › 委託／日記／親密／徽章／圖鑑） | `subtab`、`subtab_on`、`subtab_p` | h15 | 同 tab switch（無 veil） | `sfx_ui8_tab_switch_a` |
| 泡泡（心聲） | `bubble`、`bubble_tail`、`thought_dots` | h20+ | scale 0.6→1.05→1，220ms | — |
| 設定列＋分段 | `panel_inset` 列＋`med19_*` icon；`seg_bg`＋`seg_on`＋`seg_div`；`slider_track` | 列 h22；seg h16 | seg_on 滑 140ms | `sfx_ui8_tap_a` |
| 清單列／捲動 | `panel_inset`、`divider`、`scroll_track`＋`scroll_thumb`、`timeline_dot`＋`timeline_line`（日記時間線，P0-3） | — | — | — |
| 星級／勾選 | `star_on`/`star_off`、`check_on`/`check_off` | 9／12 | — | `sfx_ui8_toggle_on` |
| 教學提示（P1-2） | `hint_arrow`、`fx_ripple` | — | 上下 2 art 浮動 1s loop | — |
| 標題 | `plaque`（紫）/`plaque_pri`（橙）＋`lbl_title_*`（serif ≥9.2） | h17 | 隨 popup | — |
| 畫面轉場 | `fx_veil`、`fx_sweep`、`fx_mote`、`fx_spark` | — | MOTION 6 | `sfx_ui8_transition_veil_close`/`sfx_ui8_transition_veil_open` |

## 3. 字同對比度（修「細字睇唔到」）
| 用途 | 字 | 大小（art） | 顏色 | 對比 |
|---|---|---|---|---|
| 標題 | serif（Noto Serif HK Black）或 `lbl_title_*` | ≥9 | 白＋紫/橙描邊 | — |
| 掣字 | sans Bold（`lbl_btn_*`） | 9.0 | 白＋深色描邊 0.9 | 白:描邊 ≥8.6；描邊:掣底 ≥4.3 |
| 正文／列字 | `fillText` sans | ≥7（建議 7.4） | `#FFF5DC` on 玻璃 | 11.8:1 |
| 羊皮紙正文 | sans | ≥7 | `#3A2840` | 13.3:1 |
| 停用掣 | `btn_dis`（`#CDD1E3→#9AA0BC`）字 `#262A48`，冇描邊 | 9 | | 7.2:1 |
| 上鎖卡 | `card_locked`（`#363C66`）字 `#F4F5FC` | ≥7 | | 8.1:1（同面板底仍分得出） |
| 細數字 | `px7`/`px7_ol` 1x 原生，×3 nearest | 7 | `#FFF5DC`/描邊 `#1A1230` | 16.5:1 |
| dock 字 | `lbl_tab_*` sans 7.2 | | `#EFE6D0` on dock | 10.2:1 |
| 需要條填色 vs 槽 | | | | 全部 ≥11:1；條底加深色下唇 |

`fillText` 字型堆疊：`"Noto Sans HK","Noto Sans TC","PingFang HK","Microsoft JhengHei",sans-serif`，weight 700；標題 `"Noto Serif HK","Noto Serif TC",serif` 900。字號 = art × 3（@3x canvas）。描邊先 `strokeText`（lineJoin round）再 `fillText`。

## 4. 引擎畫法
- 座標：atlas JSON `frames[name]`：`x,y,w,h`（atlas 內 px）、`box`＝sprite 內「邏輯框」（光暈外 pad 唔計），`pivot`（預設 box 中心）。擺位用 box 對齊 layout，唔好用 w/h。
- `slice`: `9`＝9-slice，`nine=[l,t,r,b]`（由 sprite 邊計 px，已包光暈）；`3h`＝固定高、橫拉中段；`3v`＝固定闊、直拉。目標闊＝邏輯闊＋(w−box.w)。
- `ctx.imageSmoothingEnabled=true` 畫 UI（8-bit alpha 光暈/玻璃）；畫 `px7` 字時關 smoothing 並用整數倍。
- 按下狀態 `_p` 已 bake 向下 1.1 art＋光減半，邏輯框唔變（唔使再位移）。
- 冇 shader：DoF＝背景 canvas `filter='blur(2px)'`（唔支援就略）再蓋 `#141A36` α110/255。
- @2x 用 `ui_hd2d@2x`，同名同 box 比例（÷1.5）。

## 5. 預留：4b 屋仔佈置／5a 家族
- 4b 用現有零件（唔另開 frame）：`med24_navy`＋`ic:house`（入口）、`med22_navy`（返回）、`med30_pri`＋`ic:decorate`（佈置）、`med16_navy`/`med20_pri`（pin）、`med22_navy`/`med25_pri`（家具分類 tab）、`panel_glass_plain`＋`sheet_handle`（sheet）、`card`/`card_sel`/`card_locked`＋`pill_pri`/`pill_sec`/`pill_dis`、`btn16_pri`（完成）、`plaque`＋`lbl_title_屋仔佈置`。Icon：`ic:house` `ic:decorate` `ic:furniture` `ic:rotate` `ic:flip` `ic:store` `ic:lock` `ic:check`。
- 5a stub（JSON 有 `stub:true`）：`family_crest`（家族等級＋`gold` 數字）、`tree_node`/`tree_node_sel`、`tree_line_h`/`tree_line_v`/`tree_joint`；icon `ic:family_tree` `ic:family_level`；標題 `lbl_title_家族樹`。見 `mockups/stubs_4b_5a_3x.png`。

## 6. 對齊 4b（`sprites/series2_house/ui/layout.json`，只讀，冇改）
| 4b 位置 | 4b 數值 | kit 對應 |
|---|---|---|
| gardenEntry | cx178 cy104 d24，字 y120.5 | `med24_navy`；layout_hd2d 右欄 house 同位 |
| houseHud.back | cx16 cy18 d22 | `med22_navy`（＋`_p`） |
| houseHud.title | w70 y8 | `plaque`（3h 拉 70）＋tails |
| houseHud.decorate | cx172 cy392 d30 | `med30_pri`/`med30_pri_p` |
| decorate.pins | d16／選中 d20 | `med16_navy`／`med20_pri` |
| decorate.sheet | (4,280) 187×138 r10 | `panel_glass_plain`＋`sheet_handle` |
| decorate.tabs | cy297 d22／d25，6 個 | `med22_navy`／`med25_pri` |
| decorate.cards | 54×66，pill y379 h11 | `card`/`card_sel`/`card_locked`＋`pill_sec`（擺緊）/`pill_pri`（擺上去、價錢）/`pill_dis`（委託獎） |
| decorate.done | (62,398) 71×16 pri | `btn16_pri`＋sans「完成」 |
| toastFirst | (34,140) w128 | `toast` |

**4b re-skin 包（part 2 做咗；4b 檔一個都冇改）：** `reskin_4b/`，對照表 `reskin_4b/reskin_map.json`，前後對比 `reskin_4b/preview_before_after_3x.png`，重跑 `python3 tools/build_ui_reskin_4b.py`。
- 33 個 PNG，**同 4b 原檔同名、同 canvas 尺寸、同中心** → 遊程將路徑由 `orig` 換 `reskin` 就得，layout.json 數字唔使改。
- btn_done → `btn16_pri`＋`lbl_btn_pri_完成`；sheet_panel → `panel_glass_plain`＋`sheet_handle`。
- `card_*_example` → `card`/`card_sel`/`card_locked`＋`card_spot`＋家具縮圖（只讀 4b furniture）＋sans 名＋`pill_sec`/`pill_pri`/`pill_dis`/`pill_navy`（新 `lbl_pill_*` 字）；買＝`ic:star`＋gold 價錢；鎖＝暗剪影＋`ic:lock`；收起＝`ic:clear`。
- `tab_*` → `med22_navy`/`med25_pri`＋4b 家具類別 icon（保留）；`pin_*` → `med16_navy`/`med20_pri`（選中加 `fx_ripple`）＋`ic:plus`。
- btn_back/btn_house/btn_decorate → `med22_navy`＋`ic:back`／`med24_navy`＋`ic:house`／`med30_pri`＋`ic:decorate`＋`label_plate`＋`lbl_act_佈置`。
- btn_house_locked → 新 `med24_dis`＋`ic:house`（α.55）＋`ic:lock`。
- `icon_back/plus/clear/lock/house/decorate`：kit 版（map 標 optional，用唔用由遊程/4b 話事）；`icon_bed/table/wall/rug/window/lamp` 照用 4b。

## 6b. Part 2 新零件
| 零件 | 用途 |
|---|---|
| `med24_dis` | 停用／上鎖圓章（屋仔未解鎖）；疊 `ic:house` α.55＋`ic:lock` 右下 |
| `ic:back`、`ic:plus`、`ic:clear` | 返回、加、清空（同 4b 意思一樣，kit 畫風） |
| `scroll_fade_top`/`scroll_fade_bot` | 長 list 上下仲有內容嘅漸隱邊（3h slice）；見 MOTION §10.2 |
| `scroll_glow_top`/`scroll_glow_bot` | overscroll 金光 |
| `pill_navy` | 中性動作 pill（清空） |
| `lbl_pill_*`（擺上去／擺緊／清空／委託獎／訪客禮）、`lbl_act_佈置`/屋仔/委託、`lbl_title_佈置屋仔`/屋仔 | 預烤字 |
| 字 `✦` | gold／px7／px7_ol 都有（程序畫四角星）；用喺光粒獎勵「✦+20」、升級「✦ LV.4 ✦」、chip 數字前綴 |
| `ic:reset` | 箭頭頭修正（↻ 清楚） |
| `mockups/levelup_3x.png` | 升級 popup 全版；動態 MOTION §10.1 |

## 7. 已知限制（part 3 可做）
- 升級 popup 嘅寵物用 48px 概念 sprite 放大（nearest），正式版要 4c 嘅大頭像。
- `ic:decorate` 係調色板；4b 自己嘅掃把＋星 icon 都夾，二揀一由遊程/Kurt 定。
- 5a 家族仍係 stub；`fx_veil` 喺深底下好淡（設計如此，engine 可加 α）。
