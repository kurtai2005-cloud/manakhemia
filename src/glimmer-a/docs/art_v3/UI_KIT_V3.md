# 《微光小圃》UI kit v3：V3-A 金光現代 HD-2D（第 1 批）

> Kurt 揀咗「V3-A，全套連工作場景同族譜都做」。呢份係**第 1 批：UI kit v3**，覆蓋 v2 kit 全部元件同畫面，再加 6b 散步、6c 夢遊、6d 分享用到嘅 UI。
> 舊嘅 `kit_hd2d_v2/` 原封不動。所有圖都係 Pillow／numpy 程序生成，冇用 AI 圖。
> 重新生成同驗收用以下指令：
>
> ```
> python3 art-pet/tools/ui_hd2d_v3_kit.py              # 零件 atlas、icons、portrait、v2→v3 map
> python3 art-pet/tools/build_ui_hd2d_v3_mockups.py    # 17 個畫面、overview、layout、texts.json
> python3 art-pet/tools/ui_hd2d_v3_kit.py --fonts      # 字型子集、charset（要喺 mockups 之後跑）
> python3 art-pet/tools/validate_ui_kit_hd2d_v3.py     # 驗收，結果寫入 validation.json
> ```

## 1. 檔案結構

| 路徑 | 內容 |
|---|---|
| `atlas/ui_hd2d_v3@3x.png/.json` | 200 個 UI 零件，每個有 `slice`、`nine`、`group`、`note`、`backdrop` |
| `atlas/ui_hd2d_v3@2x.png/.json` | 由 @3x 用 LANCZOS 縮成，nine 數值已跟住縮 |
| `atlas/icons_hd2d_v3@3x.png/.json` | 121 個 v3 像素 icon，@3x 原生 1:1 |
| `atlas/icons_hd2d_v3@6x.png/.json` | 同一批 icon 用 nearest ×2，畀大圖示用（升級獎勵、分享卡） |
| `atlas/icons_glow_hd2d_v3@3x.png/.json` | icon 光暈層，真 alpha；每邊 pad 8 |
| `icons/<n>@3x.png`、`icons/glow/<n>_glow@3x.png` | 散檔版本 |
| `atlas/v2_to_v3_map.json` | v2 每個零件對應嘅 v3 名，236/236 都有對應（`icon:` 開頭即係喺 icons atlas） |
| `layout_hd2d_v3.json` | 版面 token、`petGlow`、17 個畫面嘅 elements／hits、partsUsed、iconsUsed |
| `portrait/portrait_rects.json` | 59 個 form 嘅臉框，加 `v3` block；跟 v2 同步 |
| `fonts/` | 3 個 .otf 子集、`charset_v3.txt`、`fonts_v3.json`、`OFL_noto-cjk.txt` |
| `mockups/` | 17 張 `*_3x.png`（585×1266）、`overview.png`、`icons_v2_v3_compare.png`、`texts.json` |
| `validation.json` | 驗收結果 |

## 2. 版面格（同 v2 一樣）

- 設計尺寸 585×1266 @3x（即 195×422pt）。
- 三條帶：
  - top 0–126
  - garden 126–1044（佔 .725）
  - bottom 1044–1266
- 四個動作掣（餵食／玩耍／清潔／瞓覺）浮喺花園底，cy 990。dock 喺 y 1108、高 116；home indicator 喺 222,1252。
- 所有可撳範圍至少 66px@3x（22pt）。實際 hit rect 寫喺 `screens.*.hits`，會夾返入螢幕範圍內。

## 3. 風格 token（V3-A）

- **面板**：煙燻深藍磨砂玻璃。做法係先 backdrop blur（14px@3x），再疊 `panel` 零件（半透明漸變、1.5px 金 hairline、角位菱形）。
  - atlas 入面 `backdrop: true` 嘅零件，引擎要先喺底下畫模糊背景。可以預先烘焙一張模糊場景圖，按 rect 取用。
- **顏色**（`ui_hd2d_v3_lib.C`）：

  | token | RGB |
  |---|---|
  | ink | 36,34,52 |
  | cream | 250,244,230 |
  | mute | 206,212,230 |
  | gold | 232,200,128 |
  | goldhi | 255,236,184 |
  | golddk | 66,40,4 |
  | navy | 18,24,48 |
  | navy2 | 30,40,74 |
  | navy3 | 44,58,104 |
  | amber | 246,176,72 |
  | sky | 110,190,230 |
  | rose | 240,126,150 |
  | violet | 156,132,230 |
  | mint | 120,206,160 |
  | red | 214,62,72 |
  | dis | 84,88,108 |

- **按鈕**：上淺下深漸變、頂部高光、內 hairline、柔和陰影。
  - 每個掣都有 `_p`（pressed）版：漸變反轉成「上深下淺」，冇咗頂部高光；圓形 act 掣按下會加一層 accent 色（α .30）。
  - 掣色 pri=amber、sec=sky、rose、violet、mint、gold、dis。
  - 有色掣上面一律用 **ink 字**；只有 dis 掣用 cream 字。
- **光影**：
  - 光暈：`glow_*`（真 alpha）。
  - 星芒：`flare_*`。
  - 粒子：`fx_mote`、`fx_bokeh`。
  - 其他效果：`fx_rays`（升級光芒）、`fx_sweep`（掃光）、`fx_ripple`。
  - 遮罩：`veil`、`veil_light`。
  - 呢啲都係 UI／光影層，**可以用真 alpha**；像素 sprite 一律 alpha 0/255。

## 4. 字型

- 字型：Noto Sans CJK TC（Regular／Bold），標題用 Noto Serif CJK TC Bold。ttc 用 index 3（TC）。全部 OFL 1.1。

| role | 字型 | px@3x |
|---|---|---|
| title | Serif Bold | 30 |
| h2 | Sans Bold | 24 |
| body | Sans | 21 |
| value | Sans Bold | 21 |
| button | Sans Bold | 20 |
| label | Sans Bold | 18 |
| caption | Sans | 18 |

- **最細 18px@3x（6pt）**。
- **對比**：每段字喺「畫完柔和字影之後」嘅實際背景 bbox 量度，取背景亮度第 95 百分位計 WCAG 對比，要求 **≥ 4.5**。
  - 量度結果寫入 `mockups/texts.json`。今批 317 段字，最低 4.55。
- **子集建議**：
  - 字表：`fonts/charset_v3.txt` 共 1073 字，包括：
    - 遊戲 `src/glimmer-a/src/*.js` 同 `index.html` 入面全部中文（872）
    - mockup 用到嘅字
    - ASCII
    - 常用全形標點
  - 已出 .otf 子集：

    | 檔案 | 大細 |
    |---|---|
    | NotoSansCJKtc-Regular.subset.otf | ~498KB |
    | NotoSansCJKtc-Bold.subset.otf | ~500KB |
    | NotoSerifCJKtc-Bold.subset.otf | ~734KB |

  - box 冇 brotli，所以未出 woff2。上線前建議轉 woff2（大約細 30–40%）：
    ```
    pip install fonttools brotli
    pyftsubset NotoSansCJK-Regular.ttc --font-number=3 --text-file=fonts/charset_v3.txt \
      --layout-features='*' --flavor=woff2 --output-file=NotoSansCJKtc-Regular.subset.woff2
    # Bold／Serif Bold 照做
    ```
  - Serif 只係標題用，可以再收窄：只放標題字，大約 200 字。
  - 改遊戲文字之後要重新跑 `ui_hd2d_v3_kit.py --fonts`；validator 會檢查 charset 有冇蓋晒用到嘅字。
  - OFL：可以隨遊戲一齊分發，要附 `OFL_noto-cjk.txt`；唔可以單獨賣字型。如果要對外改名，避開保留名「Source」。

## 5. Icon v3

- **來源**：v2 icons atlas（16px）、6b `ic_walk`、6c（dream、dreambook、frag_*）、6d（friend、share、copy、paste、photo、qr、egg_code、friend_badge）。總共 121 個。
- **做法**（`ui_hd2d_v3_icons.py`，全部係程序生成）：
  1. EPX／Scale2x 放大到 ×2。內部深色細節（眼、口）保留 nearest 2×2，唔會變形。
  2. 由 alpha 推 normal map，再打光：暖色主光由左上嚟，冷色 rim 由右下嚟，量化成 3 級，保持像素感。
  3. sel-out 外框：貼住透明位嘅深色像素，換成「鄰色 ×.30 ＋ 深紫」。
  4. 加最多 3 粒高光 glint。
  5. 光暈另外出一層 `icons/glow`：真 alpha、pad 8、blur 4。
- **規格**：
  - 32px（mini 22px）喺 @3x 1:1 顯示，只可以整數倍放大；大圖示用 @6x atlas。
  - sprite alpha 只有 0/255。
  - v3 色數一律多過 v2，validator 有查。
  - 對照圖：`mockups/icons_v2_v3_compare.png`。
- **glow 用法**：光暈層疊喺 icon 底，alpha 可以做呼吸效果（建議 0.6↔1，週期 2.4s）。寵物相關光要乘 `petGlow`，見第 8 節。

## 6. 頭像（portrait）

- 規則同 v2 一樣，只係放大一倍：
  - 由 `portrait_rects.json` 嘅 rect 取臉框：n=22，k=5，即係 110px 窗口，nearest 整數倍放大。
  - `portrait_frame` 尺寸 122，窗口喺 (6,6)。
  - 飾品 `pop` 嘅像素畫喺框之上。
  - `acc.badge = true` 嘅飾品，喺框角加 `acc_badge`。
- 狀態底色用 `portrait_bg_{hungry,happy,normal,sleepy,sleep,sick}`。右下角 `mood_badge_*`：漸變圓形＋v3 mini icon。

## 7. 畫面同元件（mockups）

| 畫面 | 對應 v2 | 重點 |
|---|---|---|
| home | home | 頂 bar（頭像、名牌、階段 tag、Lv、4 條數值條、兩粒 chip）、toast、泡泡、4 個 act 掣、dock 5 格、side rail |
| popup | 彈窗 | 收到小禮物：3 張 card、新 tag、按鈕 |
| levelup | 升級 | fx_rays、獎章、獎勵 card、星；標題底墊深藍光暈保對比 |
| settings | 設定 | toggle、slider、segmented、語言 |
| journal_dex | 手帳・圖鑑 | subtab、格仔、鎖、新 tag、詳情卡 |
| house_4b | 4b 屋仔 | 暖色室內光、窗光、蘑菇燈、寵物光（`petGlow`）、屋仔 HUD |
| house_4b_decorate | 4b 佈置 | bottom sheet、分類 tab、家具 card、swatch |
| 5a_family_tree | 5a 族譜 | crest、tree_node（gold／sel）、連線、家族統計 |
| 5a_egg_choice | 5a 揀蛋 | egg_card ×2 |
| 5a_pet_card | 5a 寵物卡 | 頭像、4 條數值、花紋／把戲／族譜、主養／放生 |
| 5b_daily_plan | 5b 今日安排 | 遠足／工作／休息 3 種模式 card |
| 5b_job_picker | 5b 揀工作 | 工作卡、job_lv_badge |
| 5c_parent_pick | 5c 揀父母 | 6 格、快 ×2 pill |
| 5c_inherit_result | 5c 傳承結果 | 傳承對照 |
| 6b_walk | 6b 散步 | walk_track、步數、拾到物件 |
| 6c_dream | 6c 夢遊 | 夢卡框、碎片計數、收入夢簿；寵物瞓緊所以 petGlow 0 |
| 6d_share | 6d 分享 | 好友名片、QR 框、code field、複製／貼上 |

- **side rail**：6 粒，由上至下：
  - 委託（gift，紅點數字 3）
  - 信（紅點）
  - 屋仔
  - **圖鑑**
  - **細佬**（egg_kid，紅點）
  - 散步
- **layout**：`layout_hd2d_v3.json → screens.<name>.elements` 係顯示 rect，`hits` 係觸控 rect。座標全部係 @3x px。

## 8. 寵物光源規則：petGlow（Kurt：「除左佢訓就會關」）

- 寵物**自己**嘅光源同特效包括：rim glow、地面光圈、身邊光點、光暈 icon、飾品發光。呢啲喺**瞓覺狀態全部關**，醒返先再亮。場景燈（燈泡、窗光、蘑菇燈）唔受影響。

| 狀態 | petGlow |
|---|---|
| awake | 1 |
| sleepy（眼瞓） | 0.6 |
| sleep／sleepClip／dreamEnter／dreaming | **0** |

- **淡出**：600ms，easeInQuad。sleep clip 第 1 幀，或者夢遊入夢 transition_in 開始之前觸發。
- **淡入**：醒（wake clip 最後一幀）之後 400ms，easeOutQuad，然後 150ms pulse（1→1.15→1）。
- keyframes：`[0,1] [600,0] … [wake,0] [wake+400,1] [wake+475,1.15] [wake+550,1]`
- 引擎做法：`petGlow` 乘落所有寵物 `*_glow` 層同寵物粒子嘅 alpha／產生率；sprite 本體唔變。烘焙底圖唔包寵物光。
- 詳細寫咗喺 `layout_hd2d_v3.json → petGlow` 同 `style_ref/hd2d_v3/V3.md`。

## 9. 引擎備註

- **9-slice**：atlas `nine = [l,t,r,b]`。93 個零件有 nine，中間會拉伸，角位唔郁。
- **pill／btn**：圓角係高度一半，橫向只拉伸中段。
- **@2x**：直接用 `ui_hd2d_v3@2x`。icon 冇 @2x，因為像素唔可以非整數縮；@2x 裝置用 @3x icon 縮 2/3 會糊，建議用 @6x ÷3，或者照用 @3x 1:1。
- **磨砂 backdrop**：每幀 blur 太貴。建議場景每次轉景先烘焙一張 blur 圖；彈窗開嘅時候用 snapshot blur 一次。
- **字**：用 runtime 字型渲染，唔烘焙入圖。字影：同字形一樣、向下偏 2px、Gaussian blur 2.2；顏色由畫面指定，量對比之前已經畫埋。
- **按下**：換 `_p` 零件；`act_glow` 係 act 掣嘅外圍光暈；按下時閃一下，時長由引擎自定（建議 120ms）。

## 10. 已知問題／下批

- @2x icon 冇原生版本（見第 9 節）。
- 字型子集係 .otf，未轉 woff2，因為 box 冇 brotli。
- 磨砂效果喺 mockup 係即場 blur，引擎要自己烘焙。
- 戴帽（hat 類）飾品喺頭像入面只有 pop 3px 露出框頂，細看似截咗，同 v2 規則一樣。
- 下一批建議次序：花園 H1–H4 → 屋仔 → 散步 → 夢遊 → 族譜 → 工作場景。
