# 《微光小圃》HD-2D UI kit v2 —「A ui 配 B 頭像」（遊美 → 遊程）

> 2026-11-02 · Kurt 揀：**v2 A 版排位**（金邊海軍藍頂旗、圓勳章動作＋絲帶字、A 版 dock）＋ **B 版 ×2 面部近鏡頭像**。
> v1（`ui/kit_hd2d/`）原封不動保留；v2 全部喺 `ui/kit_hd2d_v2/`。純 Pillow／numpy 程序化像素畫，冇 AI 圖。

## 0. 一句講晒
- 畫面 1x＝**195×422 art px**，出圖一律 **×3 nearest → 585×1266**（亦有 @2x）。引擎用 1x 座標 × scale，唔好用小數縮放。
- UI 座標唯一來源＝`layout_hd2d_v2.json`；零件＝`atlas/ui_hd2d_v2@3x.json`；icon＝`atlas/icons_hd2d_v2@3x.json`；字＝`fonts/fonts_v2.json`；頭像裁位＝`portrait/portrait_rects.json`（詳見 `PORTRAIT_SYNC.md`）。
- 驗證：`cd art-pet/tools && python3 validate_ui_kit_hd2d_v2.py` → `validation.json`。

## 1. 檔案
| 路徑 | 內容 |
|---|---|
| `atlas/ui_hd2d_v2@{1x,2x,3x}.png/.json` | 236 個 UI 零件（面板、按鈕、pill、勳章、bar、寶石、控件、5a/5b/5c 零件、頭像框）。1x 512×256 |
| `atlas/icons_hd2d_v2@{1x,2x,3x}.png/.json` | 72 個 16px 手點 icon + 15 個 11px mini icon。1x 512×64 |
| `icons/ic_<名>@{1x,3x}.png`、`icons/mini_<名>@{1x,3x}.png` | 逐個 icon 獨立檔（方便 Figma／美術對稿） |
| `fonts/` | Fusion Pixel 8／10／12px TTF（zh_hk proportional）＋ `OFL_fusion-pixel.txt` 授權＋1x 字形 mask `font_fp{8,10,12}@1x.png`＋`fonts_v2.json`；樣板 `fonts/text_sheet_3x.png` |
| `layout_hd2d_v2.json` | 頂旗／頭像／名牌／需求條／chips／toast／右側 rail／動作勳章／dock／泡泡／彈窗／4b 房 |
| `portrait/portrait_rects.json`、`portrait/portrait_cases_3x.png` | 59 個 form 頭像裁位＋498 個飾品處理值；8 個示範 case |
| `mockups/<畫面>_3x.png`、`mockups/<畫面>_smallphone_360w.png`、`mockups/overview_2x.png` | 14 個畫面 mockup＋細機 360 闊檢查＋總覽 |
| `validation.json` | 驗證結果 |

工具（全部喺 `art-pet/tools/`，遊美自己嘅檔）：`hd2d_v2_px.py`（像素零件庫＋寵物即場合成）、`ui_hd2d_v2_icons.py`（icon 點陣）、`ui_hd2d_v2_kit.py`（出 atlas／icon／字／頭像裁位）、`build_ui_hd2d_v2_mockups.py`（mockup＋layout json）、`build_ui_hd2d_v2_textsheet.py`、`validate_ui_kit_hd2d_v2.py`。

重跑（次序要啱，因為字集會由 mockup 原始碼收字）：
```
cd art-pet/tools
python3 ui_hd2d_v2_kit.py            # atlas / icons / fonts / portrait_rects
python3 build_ui_hd2d_v2_mockups.py  # 14 mockups + smallphone + overview + layout json + portrait_cases
python3 build_ui_hd2d_v2_textsheet.py
python3 validate_ui_kit_hd2d_v2.py
```
改咗 mockup 文案（新字）→ 要**先重跑 kit** 再出 mockup，否則會印 `missing glyphs`。

## 2. 9-slice 規則（mode＝tile，唔好 stretch）
- atlas json 每個可伸縮零件有 `slice`（`9`／`3h`／`3v`）、`nine`＝[l,t,r,b]（已乘 scale）、`mode`＝`tile`。
- **角固定、邊同中間用 tile 重複**，唔可以拉伸：材質有 8px 周期 dither／木紋／星點，拉伸會變糊。中間區已驗證係周期 ≤8 且整除，tile 冇接縫。
- 需要嘅闊度唔係整數倍時：最後一格裁走（右／下截斷），唔好縮放。
- `3h` 按鈕／pill 只係橫向伸（高固定：btn 20、btn16 16、pill 11、seg 10）。
- `fx_veil_tile`（50% 棋盤）／`fx_veil25_tile`（25%）係彈窗遮罩：成個畫面 tile，**唔用半透明 alpha**（全 kit alpha 只有 0／255）。

## 3. 字體（Fusion Pixel，OFL 1.1）
- 三個尺寸：**fp12** 標題／大數字、**fp10** 按鈕／標籤／正文、**fp8** 細字（最細，唔好再細）。
- 字形 mask 係白色 1-bit；渲染次序：① tint（兩色：上 55% `col`、下半 `col2`，例：金字＝white/g_hi）→ ② 8 鄰 1px 描邊（預設 `line` #24172C）→ ③ 再落 1px 影（描邊下移一格）。
- **規則**：10／12px 一律描邊＋影；8px 喺深色面板入面**唔描邊**（描邊會糊），淨係 pill／勳章數字／場景上面嘅 8px 先描邊、唔落影。泡泡（米白底）用 `ink` 色、唔描邊。
- `fonts_v2.json`：`lineH`；每字 x/y/w/h/xoff/yoff/adv，`yoff` 由行頂（「國」字頂）計。字集 992 字（ASCII＋標點＋kit md／series2／5x json／builder 原始碼收集到嘅中文）。runtime 如要動態文字（玩家改名）→ 直接用 `fonts/` 入面 TTF，關 AA、整數 px。
- 樣板：`fonts/text_sheet_3x.png`。

## 4. 排位（`layout_hd2d_v2.json`，1x 座標）
- 三段：top 0–42、**花園 42–348（73%，> 50% 規則）**、bottom 348–422。
- 頂旗 `banner_top` y −5、全闊 195×47（金邊海軍藍，兩粒 rivet＋中間寶石）。
- 頭像 `portrait` 52×52（x1 y6，窗 44×44 @4,4），**跌出頂旗底 16px 似勳章**；框頂外最多畫 6px（3 art 行 ×2）飾品 pop。
- 名牌＋形態 ribbon、四條需求 bar（肚餓／開心／乾淨／精神）、右上 chips（光點／星星）、toast（x58 y46 106×17）、右側 rail（委託／信／屋仔）。
- 動作勳章 4 個 d30（cy357，間距 47.7）＋絲帶字；dock y385 高 37，5 tab，選中 tab 升高＋金框。
- 彈窗 `popup` 闊 171（x12），標題 plaque 坐喺框頂中間，右上 close。

## 5. 零件清單（atlas group）
- panel：`panel_navy`／`panel_navy_flat`／`panel_paper`／`panel_inset(_sel)`；card：`card`／`card_sel`／`card_locked`／`card_paper`
- hud：`banner_top`、`dock_bar`、`dock_pillar`、`bubble(+_tail)`、`chip`、`chip_plus(_p)`、`toast`、`plaque(_pri)`
- button：`btn_{pri,sec,rose,violet,dis}(_p)` h20、`btn16_*` h16、`pill_{pri,sec,rose,violet,dis,navy}`
- label：`ribbon_{navy,violet,pri,rose,sec}`、`stage_tag`、`subtab(_on)`、`seg_bg/seg_on/seg_locked`
- bar：`bar_trough_h{5,6,7}`、`bar_fill_<色>_h*`、`bar_tip_h*`、`exp_gem_on/off`
- medal：`med<直徑>_<色>`（9–40px；28/30 有 `_p` 按下）— 所有圓勳章動作／icon 底
- ctl：`close(_p)`、`toggle_track_on/off`＋`toggle_knob_on/off`、`check_on/off`、`star_on/off`、`slider_track/knob`、`scroll_track/thumb`
- deco／fx：`gem_<色>_{5,7}`、`rivet`、`sparkle_{3,5,7}`、`red_dot(_num)`、`stamp_done`、`timeline_dot/line`、`hint_arrow`、`fx_ripple`、`fx_mote`、`fx_sweep`、veil
- 5a/5b/5c：`family_crest`、`tree_node(_sel/_gold)`、`tree_line_h/v`、`tree_joint`、`egg_card`、`room_dot_*`、`pill_fast_on/locked`、`swatch_frame`、`job_lv_badge`
- portrait：`portrait_frame`、`portrait_mask`、`portrait_bg_<心情>`、`mood_badge_<心情>`、`acc_thumb_<飾品>`

## 6. Icon（手點，16×16 1x）
72 個 16px＋15 個 mini。全部逐粒落色：左上受光三階、1px #24172C 外描、可愛臉。舊版自動轉圖嘅糊 icon（貓、兔、熊書、雞齒輪、禮物等）已全部重畫。mini（11px）用喺 toast／pill／bar 頭。命名見 `atlas/icons_hd2d_v2@1x.json`。

## 7. 畫面 mockup（全部用 kit 零件即場砌；背景用現有 H3 花園／4b 房間層）
| 畫面 | 重點 |
|---|---|
| home | A 頂旗＋B ×2 頭像（蝴蝶結 shift）、toast、rail、4 勳章動作、dock |
| popup | veil 50%、收禮物三格、信件列、睇信／收下 |
| levelup | 金 crest、光芒（棋盤 dither，唔用 alpha）、新解鎖三格 |
| settings | slider／toggle／seg（繁中／English、省電／標準／靚）、字體授權行 |
| journal_dex | 4 subtab、收集 bar、4×4 圖鑑格（頭像裁位重用）、說明卡 |
| house_4b／house_4b_decorate | 4b 房 reskin：頂 ribbon、頭像（睡帽 pop）、4 勳章；佈置 sheet（6 類 tab＋3 傢俬卡） |
| 5a_family_tree／5a_egg_choice／5a_pet_card | 家族等級 crest、族譜節點＋線、揀蛋、寵物卡（4 需求、3 動作） |
| 5b_daily_plan／5b_job_picker | 每隻細佬一行：遠足／工作／休息 seg、工作帽頭像＋等級章；工作 2×2 卡 |
| 5c_parent_pick／5c_inherit_result | 揀爸媽 2×3、花紋 swatch、快 ×2／×3 pill；傳承結果 |

細機（360 闊）：`mockups/*_smallphone_360w.png`＝1x nearest 縮到 360×779（×1.846），8px 字 ≈ 14.8 device px，仍然睇得清；冇元素出界。

## 8. 俾遊程嘅實作提醒
1. 所有 UI 位置讀 `layout_hd2d_v2.json`，乘整數 scale；唔好自己估。
2. 9-slice 一定用 tile；Unity 用 Sprite Border＋Draw Mode Tiled（Tile Mode Continuous），Filter Point、無壓縮、無 mipmap。
3. veil／光芒用棋盤 tile，唔好改成 alpha 漸變（會同像素風撞）。
4. 頭像用 `portrait_rects.json` + `PORTRAIT_SYNC.md` 規則即場裁，唔使預出圖。
5. reskin_4b：今次冇另出 v2 reskin_4b 圖包；4b 房用返 v2 atlas 零件砌（見 house_4b mockup），v1 `ui/kit_hd2d/reskin_4b/` 照用都得。
