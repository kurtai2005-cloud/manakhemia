# 《微光小圃》生命感 第一段 QA 報告（glimmer-live-s1.html）
- 測試日期：2026-10-31（HKT）｜測試者：遊測
- 檔案：`/workspace/qa-live-s1/glimmer-live-s1.html`（raw `27f5047`，branch `code/glimmer-liveliness`，PR #20；6.56 MiB／6,881,163 bytes）；冇改過檔案
- 工具：Playwright 1.x + Headless Chromium（isMobile、hasTouch），`window.__qa.pet`（pause／step／tap／gaze／face／setFace／setGaze／clock.setHour／log／eventLog／audioLog）
- 腳本：`run2.mjs`（主測）、`run3.mjs`（表情×日光、轉身序列、低畫質效能）、`run4.mjs`（表情／眼神分佈）；原始數據：`out/results.json`、`out/results3.json`、`out/results4.json`
- 注意：box 冇 GPU（軟件繪圖），FPS 數字偏悲觀；真手感、真觸控延遲一定要真機再試

## 結果總表
| # | 項目 | 結果 | 重點數據 |
|---|---|---|---|
| 1a | 直向 360×640／390×844／412×915：溢出、捲軸、裁切 | PASS | scrollW/H＝viewport，冇元素出界，冇重疊 |
| 1b | 觸控目標 ≥44 CSS px | **FAIL** | ⚙️／📖 只得 24px（360×640@3x）、27（@2x）、34（412×915）、36（390×844） |
| 1c | 畫面利用率 | **FAIL（P1）** | 360×640@3x 畫布只得 260×563，佔螢幕 63.5%（整數倍縮放留大黑邊） |
| 1d | 橫向 844×390 | PASS（有保留） | 冇變橫向排版，保持直向置中；但冇「請轉直」提示，UI 縮到 0.33 倍（按鈕 29×25、⚙️ 12px） |
| 2a | 眼神跟觸點 | PASS | 換格 0.12–0.15s、收斂 0.15s；真觸控 rAF 取樣約 94ms 開始郁，211ms 到位 |
| 2b | 中心抖動 | PASS | 喺 C／CR 門檻（±9 art px）附近點：每次只換 1 格，0 閃爍 |
| 2c | 冇輸入後返待機 | PASS | 望觸點 1.6s 後轉返 camera／idle |
| 2d | 拖動／懸停跟眼 | 未實作（P2） | pointermove 只做視差，眼神唔跟手指拖動 |
| 3a | 點背後回頭（20 次） | PASS | 可中斷狀態 17/17 轉身＋播 turn_back＋`pet_turn_huh_a/b`；其餘 3 次：小睡→輕喚醒（正確）、play 中唔轉（設計）、1 次測點喺螢幕外（寵物行到邊） |
| 3b | 點寵物本身／正中／盒外 | PASS | 前面 0/12、正中（dx≤3）0/6、盒外地面 0/6 誤轉 |
| 3c | 連點 10 下／3 秒 | PASS | 只轉 1 次、咦聲 1 次；startle→cuddly→第 5 下 grumpy；之後約 1 秒返 stay，冇卡死 |
| 3d | 長按／拖動誤觸 | **FAIL（P2）** | 背後長按 800ms／1500ms 都即刻轉身（pointerdown 就觸發）；由背後開始拖動亦會轉身；冇 contextmenu |
| 3e | tapPet(5) 已知問題 | 部分確認 | 見 P1-3 |
| 4 | 待機小動作 3 分鐘（5 個種子） | PASS（有建議） | 3.3–5.3 次／分；最短間隔 6.5s、中位 10–15s；只有 sway／blink／yawn 3 款；同款最多連續 4 次；眼神每分鐘換格 22.7 次 |
| 5 | 表情層＋日光色調（04／09／14／18／23.6 時 × 7 款臉） | PASS | 35 張冇錯位、冇缺件、冇 placeholder；臉件跟身體一齊上色；daylight 載入 OK |
| 6a | 效能 4x CPU（高畫質） | **FAIL（P1）** | 10.3 fps，p50 100ms，30 秒 324 個 long task（最長 148ms），之後自動降畫質（有 toast） |
| 6b | 效能 4x（q=low／off） | 低畫質勉強 | low 24.6 fps（p95 50ms）；off 30.7 fps |
| 6c | 1x 基準 | — | 46.7 fps（p95 33ms）；sim 每幀 0.042ms，瓶頸係繪圖 |
| 6d | 記憶體 | PASS | JS heap 4.7–20.7 MB，DOM 304 節點 |
| 6e | 載入 | PASS（本機） | file:// load 238ms、生命感 ready 365ms；4x：1.2s／1.7s。6.9MB 經 4G（約 10Mbps）下載估計 5–6 秒（未實測） |
| 6f | Console error | PASS | 全程 0 error／0 pageerror |

## 問題清單
### P0
- 冇。

### P1
1. **細 icon 觸控目標不足 44px**：⚙️／📖 喺所有尺寸都唔夠（最細 24px）。
   修正：`.ibtn` 視覺保持 36px，外加透明 hit 區（例如 `::after` inset:-6px），或者 UI 縮放加下限 `max(scale, 1)` 只用喺 HUD。
2. **細屏大黑邊**：360×640@3x 整數倍縮放只得 4x，畫布 260px 闊（63.5%），UI 一齊縮到 0.667。
   修正：容許非整數縮放（例如 ≥3.5 倍就用 `image-rendering:pixelated` 非整數），或者畫布整數倍、HUD 唔跟畫布縮，按 viewport 排。
3. **tapPet(5)／連點鬧脾氣同「需求鬧脾氣」共用同一個事件**（部分確認開發報嘅問題）：
   - 事件紀錄本身正確：`eventLog` 係 `{id:'grumpy', kind:'tap'}`，`stats.tantrumTap=1`、`tantrumNeed` 冇加。
   - 但連點 tantrum 用嘅係 `lowNeed` 嘅 grumpy 定義：卡片文案、`event_grumpy` 音效同需求版一樣；**共用 48h 冷卻**（點一次就封住 48h 內真正嘅需求鬧脾氣）；計入每日上限同 20 分鐘全域間隔；仲派 +1 光粒、心情 +3–4（連點會有獎）。
   - 另外 `tapPet(n)` 喺同一 tick 推晒 n 下（0 秒內 5 下），同真人節奏唔同；QA 用可以，但唔好當真實輸入。
   修正：開一個獨立事件 id（例如 `tantrum_tap`），用自己嘅冷卻、唔加獎、唔計每日上限；`stats.byId` 分開記。
4. **4x 降速高畫質只得 10 fps**：每幀約 100ms。自動降畫質會救返，但第一次降之前會卡幾秒。
   修正：中低階機一開始就用 mid／low（而家只係 `pointer:coarse` 就用 mid）；bloom／暗角／tint 改成離屏快取，唔好每幀重算；降級門檻加快。真機數據要遊程同我再對。
5. **橫向冇轉直提示**：橫向唔會變排版（符合直向要求），但畫面縮到 11% 面積、按鈕 29×25 px。
   修正：`@media (orientation:landscape) and (max-height:500px)` 顯示「請轉返直向」遮罩；PWA／原生包 manifest 鎖 `portrait`。

### P2
1. **長按／拖動誤觸轉身**：pointerdown 就判定，長按 800ms 或者由背後開始拖都會轉身＋驚嚇。修正：改喺 pointerup 判定，按住 <350ms 而且移動 <10px 先算點擊；長按留俾日後「摸摸」。
2. **觸控盒比芽崽大好多**：petBox 固定 76×82 art px，但芽崽身體約 40×46；喺頭頂上面 30+ px 點都算點寵物（會轉身），寵物附近嘅地面「跟住行」範圍被食咗。修正：petBox 跟 stage／clip 尺寸（芽崽約 52×60 連 6px 寬容）。
3. **開心表情閉眼 → 眼神睇唔到**：`happy` 眼款屬閉眼（只有 C 格），需求高嗰陣（剛照顧完）閉眼比例最高 42%，點佢眼神都唔會郁。修正：被點／望觸點期間（tapLookSec）暫時用開眼款，或者加一款開眼開心眼。
4. **待機小動作款式少**：3 分鐘入面只有 sway／blink／yawn，種子 1 sway 佔 9/15、連續 4 次；眨眼每分鐘只 1–3 次，偏少。修正：同款連續上限 2；眨眼獨立計時（每 3–6 秒）唔佔小動作配額。
5. **眼神換格每分鐘 22.7 次**（約 2.6 秒一次東張西望），喺真機可能覺得眼神太「忙」。建議真機睇完再決定 `wanderEvery` 拉到 [2.5, 5]。
6. **拖動唔跟眼**：而家只係點擊先望。如果設計想「手指喺螢幕郁，佢眼跟住」，要喺 pointermove（touch 按住時）更新 tapX/tapY。
7. **04 時第一格有灰白霧**（`shots/expr_h04_auto.png`）：時鐘跳時段後第一張截圖有一層灰，之後幾張冇。可能係時段 blend／bloom 嘅第一幀，未能確認係咪 bug；真機跨時段要再睇。
8. **轉身唔喺 play 期間發生**：play 屬不可中斷，點背後只會「摸」（`pet_touch`）唔轉身。如果設計想任何時候都回頭，要另外處理；否則屬預期。

## 截圖
- 直向三尺寸：`shots/layout_360x640.png`、`shots/layout_360x640_dpr2.png`、`shots/layout_390x844.png`、`shots/layout_412x915.png`；合併：`shots/montage_layout_portrait.png`
- 橫向：`shots/layout_844x390_landscape.png`
- 回頭：`shots/turn_back_mid.png`；連點後：`shots/spam_after.png`；tapPet(5)：`shots/tapPet5_grumpy.png`
- 眼神：`shots/gaze_tap_right.png`、`shots/gaze_force_*.png`、`shots/montage_gaze.png`
- 表情×日光：`shots/montage_expr_daylight.png`（行＝04／09／14／18／23.6 時；列＝auto／neutral／angry／sad／surprised／sleepy／wink）、單張 `shots/expr_h*_*.png`、全畫面 `shots/full_h*.png`
- 效能完結：`shots/perf_4x_end.png`

## 測唔到／限制
- 真實手感（眼神順唔順、回頭節奏、咦聲時機）同真觸控延遲：headless 量唔到，要真機。
- FPS：box 冇 GPU，數字唔等於手機；4x 降速只係模擬低階 CPU，唔模擬 GPU。
- 音效：只確認 cue 有觸發同冷卻（`audioLog`），冇聽過。
- 表情×日光截圖係喺「孵化咗」彈窗半透明遮罩下影（遮罩 0.62），色調比實際暗；結構／錯位可判斷，色準要真機。
- 6.9MB 網絡下載時間係估算，冇用真網絡量。
- 冇測：小遊戲模式、事件中點擊、陀螺儀視差（deviceorientation）。
