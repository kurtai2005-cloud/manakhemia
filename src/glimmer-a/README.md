# 《微光小圃》合併版（glimmer-combo）— 生命感第一段＋HD-2D 場景＋隱藏開發者模式

> 以 `code/glimmer-liveliness` @ 497404f（2700494 之上再加 R4：`rainbowPityLeadH` 30、行為測試唔再中途 `process.exit`）為底對齊：彩虹 240h 冷卻、drawChance 0.33、grumpy_tap 獨立事件（自己 48h 冷卻、守全域 20 分鐘間隔、唔改 lastAt）、.ibtn ≥44px（layout() 按縮放寫 inline 尺寸）、日記「2 日後作廢」全部沿用 repo 實作，冇重複一套。

- 單檔：`dist/glimmer-combo.html`（base64 內嵌全部 art／audio，雙擊 file:// 即玩）；重 build：`python3 tools/build-single.py dist/glimmer-combo.html`
- HD-2D：H1 晨／H2 黃昏／H3 日／H3rain 雨／H4 夜，2 秒 crossfade；`?hd2d=0` 回舊程序化背景；`?scene=H3rain` 指定；`?hdcache=0` 關靜態層 cache（對照用）
- 開發者模式：`?dev=1`，或 **1.5 秒內連點 5 下左上角**：名牌 chip（「守夜者／柔光形態」嗰格）或者畫面左上 72×72 CSS px 範圍
- 遊測 s1：⚙️／📖 熱區 ≥44 CSS px（360 闊都得）；觸控橫向顯示「請轉直向」（`?orient=landscape` 桌面強制）；按短邊 fit＋模糊延伸背景（冇黑邊）；HD-2D 靜態層 cache；拖動手指眼神跟；短 tap <300ms 先回頭；寵物熱區貼身但 ≥44px；開心閉眼頭部微轉
- H3 雨層細雨環境聲 v2（遊音 `audio/amb/`，loop sha256 307d0eb3…、short f5ffc6d5…）：落雨播 short（6s），1.5s 後等功率 crossfade（1.5s）入 loop（AudioBufferSourceNode.loop＝true，loopEnd＝buffer 長）；停雨 loop 淡出 1.75s；開發模式切「H3 雨」同 Auto 天氣都觸發
- 測試：`node tests/{sim,events,behavior,audio}.test.js`；瀏覽器：`PW=…/playwright-core BASE=http://localhost:PORT/index.html OUT=…/screens/ node tests/{e2e-s1,e2e-a,e2e-hd2d,e2e-playwright,e2e-live}.js`；效能：`node tests/bench-combo.js`

# 微光小圃（Glimmer Garden）— glimmer-live（生命感第一段 S1）

> 呢個資料夾由 PR #17 修好版 glimmer-a 複製（10:57 HKT 版），之後只喺度加「生命感」。第一段改動集中喺 **寵物繪製（render.js `drawPetBeh`＋新 `loadLive`／`liveFrame`／`liveAnchors`／`bulb*`）／behavior／main（`__qa.pet`）／ui（debug 面板）**，背景／場景繪製未郁（方便之後合併 glimmer-hd2d 嘅 HD-2D 場景模組）。

## 生命感第一段（F1＋F2＋A1＋D2）
- **玩法**：本機 `python3 -m http.server 8138` → `http://localhost:8138/index.html?debug=1`；或者雙擊 **`dist/glimmer-live-s1.html`**（單檔，資產＋音效 base64 內嵌，file:// 可開，手機可用）。重 build：`python3 tools/build-single.py`。
- **F1 表情 overlay**：遊美 `art/liveliness/atlas_<form>_live`（`<clip>_noface` 身體）喺 `tmpPet` 先合成身體＋eyeL／eyeR／mouth（逐幀 `face_anchors.json` 錨點，位置＝anchor − piece.pivotPx），之後先 **tint 一次**；朝左成個合成 scaleX −1。閉眼款（happy／sleepy／wink）只用 `_C_`；wink＝左 `eyes_neutral_<g>_l`＋右 `eyes_wink_C_r`。`faceVisible=false`（turn_back 第 0 幀背面）唔畫臉。容錯：缺 piece → 色塊 placeholder；缺 anchors → 由 `FORMS.headR` 推算；未有 noface 嘅 clip → idle_noface＋程序化變形；整套載唔到 → 返回 PR #17 原 atlas。
- **燈泡**：`bulb_base` 喺 tint 前（跟時段光），`bulb_glow` 喺 tint 後按情緒（happy／neutral／sleepy／hungry／grumpy，CLIPS.json bulb 表）上色＋呼吸，0.4 秒漸變；sick 唔顯示。頂部道具（attach props）改用逐幀 `head_r` 錨點。
- **F2 gaze／A1 邊行邊望**：目標＝行路方向／觸點／花盆／螢火／鏡頭，平滑後量化 L/CL/C/CR/R/U/D，換格最少停 0.25 秒；walk 時跟方向，偶爾望鏡頭。
- **D2 點一下回頭**：點寵物背後 → 轉向觸點＋播 `turn_back` clip（4 幀 8fps）＋隨機 `sfx_pet_turn_huh_a/b`（經 audio.js，跟 pet bus 音量／1.5 秒冷卻）；點前面只 gaze 望觸點。16 個生命感音效全部已 copy＋註冊，第一段只觸發 turn_huh。
- **URL**：`?live=0`（停用生命感，用回原 atlas）、`?face=off|native`、`?bulb=0`。
- **debug 面板**（`?debug=1` → DBG）：臉 mode（auto／native／off）、眼款 8 款、口款 8 款、gaze 7 格（＋自動）、觸摸（點背後／前面／頭頂）、燈泡開關；資訊欄顯示 face／look。
- **`__qa.pet` 新增**：`gaze()`（q, ql, src, x, y, tx, ty, force, dir, turn）、`face()`（eyes, mouth, gaze, clip, frame, faceVisible, live, pieces, placeholder, bulb, stat{draws,tints,overlays,faceDrawn,faceHidden,placeholder,bulb}）、`tap(x,y)`、`setGaze(q|null)`、`setFace({eyes,mouth}|null)`、`faceMode(m)`、`faceStatReset()`。`tapPet()` 改為點寵物前面（唔觸發 D2）。
- **測試**：`node tests/e2e-live.js`（45 項，BASE 預設 8138；`BASE=file:///…/dist/glimmer-live-s1.html` 可測單檔版）。

---

# （以下沿用 PR #17 README）微光小圃（Glimmer Garden）— MVP 原型

原創養成遊戲《微光小圃》嘅可玩最小原型：HTML5 Canvas + 原生 JS，**無 build、無依賴、無外部素材**。
所有像素美術都係用程式喺 canvas 即時生成（原創）。設計依據：`game-design/docs-gdd/pet-one-pager.md`（第 12 節 MVP 範圍）。

## 點樣玩／運行
- 直接開 `index.html`（file:// 都得），或者喺本資料夾開任何靜態伺服器：`python3 -m http.server 8125` → `http://localhost:8125/`
- 手機（直向 390×844 最佳）用觸控；桌面用滑鼠。畫面會自動以整數倍像素縮放至適合視窗。
- **光卵**：輕點（8 下可孵化，亦會隨時間自然孵化）。
- **餵食**（星屑餅／暖菇飯／暖湯）、**玩耍**（逗玩／接星屑）、**清潔**（沖洗；輕點便便清走）、**關燈**（睡眠，精力每小時 +12，衰減 ×0.3；精力滿自動醒）。
- **接星屑**：45 秒，拖動籃子接星屑，避開暗石。光粒 = floor(分數/10)，上限 20；心情 +8／+20；每日首 5 次全額，之後減半。
- 芽崽成長滿 24 小時（可調）後按照顧品質 CQ 分支：燦光（≥70）／柔光（40–69）／微塵（<40）。
- 離線：離開 ≥5 分鐘再返嚟會按第 7 節公式推算（有效離線 E、需求保底 20、成長 ×50%、不會死亡），顯示 3 句回歸摘要＋光粒禮物；日常事件按實時日補抽最多 14 日（2 個彈窗，其餘入日記）。
- 睡眠中點寵物：輕喚醒（開燈起身＋睏睏表情 4 秒），唔鬧脾氣、唔扣需求。
- 設定（⚙）：畫質 高／中／低／關（存檔）、就寢建議提示、重設存檔（兩步確認）。

## 畫面與後處理
- 4 層視差：星空／遠景剪影 → 中景樹＋燈籠 → 主場景（地台、團絨、物件）→ 前景草葉＋螢火。以指標位置／裝置傾斜／慢速漂移產生視差。
- 後處理（皆為降解析度模糊，只作用喺遠景與前景，寵物保持清晰）：
  | 畫質 | 內容 |
  |---|---|
  | 高 | 遠／前景景深（每幀）＋ bloom（4 級）＋ 傾斜移軸 ＋ 暈影 |
  | 中 | 景深（每 3 幀更新）＋ bloom（3 級）＋ 暈影 |
  | 低 | 暈影 ＋ 光暈精靈圖 |
  | 關 | 無後處理（仍有光暈精靈圖同環境色調） |
- 燈籠色溫隨本機時間變化；需求狀態以光色反映（飢餓→團絨微光變暗、睡眠→月光＋燈籠暗、不適→灰綠）。
- 非 debug 模式下，若連續掉幀（>26 ms 超過 ~90 幀）會自動降一級畫質並提示。

## Debug（`?debug=1`）
- 左上「DBG」按鈕開關面板：時間倍率 ×1／60／600／3600、快進 +1h／+6h／+24h、模擬離線 6h／12h／30h、需求設定、CQ 80／55／20、芽崽將完成／孵化、本地時刻覆寫（04／09／14／18／23）。
- 其他參數：`&dbg=open`（預設打開面板）、`&hour=N`（鎖定本地時刻）、`&q=high|mid|low|off`（覆寫畫質）。
- `window.__glimmer`：`state`、`fastForward(sec)`、`simOffline(h)`、`setQuality(q)`、`bench(q,n)`、`hourOverride`、`timeScale` 等。

## 結構
```
index.html        版面、樣式、DOM 層（HUD／按鈕／彈窗）
src/data.js       PARAMS（全部可調參數，對應 GDD 第 14 節）、常數、色盤
src/sim.js        模擬核心：DOM-free、可設種子 RNG、Node 可 require（可直接搬去其他引擎／後端）
src/render.js     程序化像素美術、4 層視差、光源、後處理
src/ui.js         HUD、行動、彈窗、迷你遊戲流程、輸入、debug 面板
src/main.js       存檔／離線／主迴圈／縮放／自動降畫質／window.__qa.pet
src/lighting.js   時段光（早 07–11／午 11–17／晚 17–23／夜 23–07）hook
src/events.js     日常事件（DOM-free、種子 RNG）：抽選／冷卻／保底／閃光日／日記／lastSaveTime 回撥保護
src/behavior.js   寵物行為狀態機（DOM-free、固定步長 1/60、可設種子）
src/audio.js      Director（純邏輯，Node 可測）＋ WebAudio Engine（BGM 小節線 crossfade、sample-accurate loop）
art/              遊美 atlas（egg／sprout／radiant／soft／props／events，全部 ≤1024×1024）＋ CLIPS.json／CLIPS.md／EVENT_ICONS.md
art/daylight/     遊美 daylight.json＋bg／light_{early,noon,dusk,night}.png（480×270）
audio/            遊音音訊（原檔，不改）
docs/clip-format.md        clip／atlas 格式規格（遊美格式為標準）＋格式問題清單
docs/integration-check.md  整合檢查
tests/sim.test.js          Node 單元測試（無依賴）：node tests/sim.test.js
tests/e2e-playwright.js    端到端（playwright-core + 系統 Chrome）
tests/last-run-*.txt       最近一次測試輸出
screens/*.png              390×844 截圖（各狀態、各畫質、日夜、離線摘要…）
docs/engine-eval.md        引擎評估（Godot／Unity／Web）
```

## 測試
```
node tests/sim.test.js                                   # 85 項
node tests/events.test.js                                # 事件／保底／閃光日已領／lastSaveTime 回撥／PR #19 P0–P1＋離線唔計上限＋PR #17 QA 修正（157 項）
node tests/behavior.test.js                              # 行為（含 atlas、23 clip、daylight hook、輕喚醒＋生命感 gaze 量化／dwell／A1／D2／F1 款式／資產齊全，96 項）
node tests/audio.test.js                                 # 音訊 Director＋檔案 sha256 對照 staging＋生命感 16 音效（27 項）
node tests/sim-report.js                                 # PR #19 自跑模擬（14 日離線條數／彩虹日數／螢火傍晚佔比）
node tests/e2e-a.js                                      # 方案 A 端到端（93 項，~150 秒）
node tests/e2e-live.js                                   # 生命感第一段（45 項，截圖 screens/live-*.png）
python3 -m http.server 8137 &                            # 於本資料夾（方案 A 用 8137；8125 係別個 agent 用）
node tests/e2e-playwright.js                             # 需 playwright-core 與 /usr/bin/google-chrome（可用 PW／CHROME／BASE 覆寫）
```
e2e 流程：新遊戲 → 光卵輕點孵化 → 餵食／玩耍／清潔／睡眠 → 接星屑（約 50 秒真實時間）→ 快進分支（燦光／柔光／微塵）→ 設定 → 改 `lastSeen` 後重載驗證離線摘要與存檔 → 縮放視窗 → 畫質幀時間量度；全程檢查 console 無 error／warning。

## 與 GDD 嘅差異／假設
- 藝術網格為 195×422（×2＝390×844），所以 sprite 以「藝術像素」計比 GDD 嘅 32／48／64 px 細，視覺大小約為 GDD 數字×2 後嘅合理尺寸，待美術確認。
- 完整生病流程、推送、變現、多寵物、「老」階段、化光繼承不在 MVP（按 GDD 第 12 節）。`sickHoursToSick`、`sickChance`、`weakAfterH`、`weakGrowthPenalty` 等參數已列入 PARAMS 但未使用。
- 不適（任何需求 <15）時成長暫停、CQ 每小時 −1；長期完全不理會會令團絨卡喺芽崽階段（不會死亡）——見「已知問題」。
- 動態光源以預製光暈精靈圖疊加（≤4 盞思路），體積光為偽造光柱＋光塵，非真 3D 光影。

## 已知問題／未做
- 幀時間只喺 headless 軟件渲染環境量度，**唔代表真機**；未喺實體低階 Android 測試。
- 微塵形態需要「有照顧但品質低」先會出現（完全忽略會令成長停止）——平衡待遊測決定係咪要放寬。
- 無音效／BGM；無 PWA manifest／service worker（見 docs/engine-eval.md）。
- 迷你遊戲難度、數值未經真人遊測。

## 可調參數（給遊測；全部喺 `src/data.js` 的 `PARAMS`，改完即生效，唔使動邏輯）

### events（遊策 v4 定案＋PR #19 P0／P1 對齊 QA v5.1）
| 參數 | 值 | 說明 |
|---|---|---|
| drawEveryH | [2,4] | 每 2–4 小時抽一次（上線＝實時；離線＝按實時日補抽） |
| **drawChance** | **0.33** | 每次抽取命中率 p_hit（QA：0.34→0.33，六種作息池抽取仍 2.2–2.4／日） |
| minGapSec | 1200 | 全域事件間隔 ≥20 分鐘（鬧脾氣亦受限） |
| cooldownH／cooldownRareH | 24／72 | 單事件冷卻；稀有流星夜 72h；**彩虹 `cooldownH:240`**（`rainbowCooldownH`）；鬧脾氣 `cooldownH:48`；**保底都唔打穿冷卻** |
| repeatWeightMul | 0.25 | 防重複（上一個事件權重 ×0.25，軟性） |
| dailyMax | 4 | 線上抽選每日上限（保底／閃光額外） |
| **offlineIgnoreDailyMax** | **true** | 遊策 10-31：離線補抽**唔計** dailyMax（對齊 QA v5.1）；冷卻／全域間隔照計；返嚟彈窗仍最多 2，其餘只入日記；線上＋離線日均實測 2.70 ≤ 2.95 |
| guaranteeHour／**guaranteeOpens** | 16／**1** | 當日第 1 次開 app（或 16:00 後）仍冇事件 → 保底：只揀「條件＋時段＋冷卻已過」嘅池事件，條件唔合就退一步只睇時段＋冷卻；**全部冷卻中 → 今次落空，下次開 app 再試**（`stats.guaranteeFail`）；離線唔觸發 |
| flashDayRate | 0.03 | 閃光日＝`hash(存檔種子, 本機日期) < 3%`；**claimedFlashDates** 按日期記「已領」；離線日唔判閃光 |
| grumpyLowNeed／grumpyLowSec | 30／7200 | 需求鬧脾氣**唔入池**（`cond`，id `grumpy`）：任一需求 <30 持續 ≥2h，冷卻 48h，有獎勵。**10 秒連點 5 下**係獨立事件 `grumpy_tap`：唔計每日上限、冇光粒／心情、唔共用 `grumpy` 冷卻同文案（自己 48h）；瞓緊點＝輕喚醒，唔鬧 |
| offlinePopupMax | 2 | 離線返嚟彈窗＝**稀有度最高 2 個，同級取最新**；其餘入日記 |
| **offlineMaxDays／offlineStepSec** | **14／600** | 離線按實時日逐 10 分鐘補抽，最多補最近 14 日（鐘點／日界用本機時間；條件用離開前需求、每項至少 `offlineNeedAssume 50`） |
| offlineMaxEvents | 120 | 單次離線補抽硬上限（保險） |
| diaryKeepDays／diaryWarnDays／**diaryMax** | 14／12／**50** | 日記留 14 日，第 12 日起提示；最多保存 50 條（14 日離線實測 p95 37、最多 41） |
| diaryGrains／diaryClaimMax | 3／60 | 日記每條 +3 光粒（**包括螢火散步，唔係 +5**）、同類合併、一鍵領取單次上限 60 |
| pendingMax／historyLen／cardSec | 2／12／5 | 排隊上限／近期歷史／提示卡秒數 |

**壞存檔回退（events.repair）**：`evs` 唔係 object → 重建；`diary／pending／hist／log／claimedFlashDates` 唔係 array → 清空；日記條目非 object／未知 id → 剔走，`ts` 壞 → 0，grains／mood 統一 3／0；缺 `stats`／`stats.byId`／`cd` → 重建；修補數記 `stats.repaired`。

**lastSaveTime（防改系統時間；全部以 UTC ms 比較）**：每次存檔記低 `lastSaveTime`（只增唔減）。
1. 系統時間比 lastSaveTime 早 **≤120 秒** 唔判篡改（網絡校時；`lastSaveTolSec`）；早逾 120 秒 → 標記 `evs.noDrawDay`＝回撥嗰日（UTC 日序號），**當日唔判閃光日、唔抽事件、唔保底**（有效時間照走），即使時間之後追過 lastSaveTime 都仍當日有效；翌 UTC 日恢復。
2. `lastSaveTime > now + 24h`（`lastSaveMaxAheadH`）視為無效：重設為 now，`lastSeen` 同步設為 now → **該段唔派離線獎**（`rep.tampered=true`、`state.saveTimeResets++`）。
3. 前撥（≤24h）／改時區：**M1 唔處理**（UTC ms 比較，時區改變唔影響；前撥只係令之後正常時間顯得「回撥」，由 ①②兜底）。

### 事件池（9 個＝7 個入池＋鬧脾氣（條件）＋閃光日；權重對齊 QA v5.1）
| id | 權重 | 時段 | 稀有 | 獎勵（光粒／心情） | 備註 |
|---|---|---|---|---|---|
| gift 禮物 | **22** | 07–23 | — | 2–4／2–4 | fallback；心情 ≥35 |
| butterfly 蝴蝶 | **20** | 07–17 | — | 1–2／4–6 | 精力 ≥30 |
| meteor 流星夜 | **10** | 19–05 | 是（72h） | 3–4／3–5 | |
| rainbow 彩虹 | **1**（維持） | 17–23 | 是（**240h**） | 3–4／4–6 | pity：距上次 ≥14 日−30h 起（26h 時最長 14.05 日，超約 1h），窗內必出、唔打穿 240h 冷卻 → ≤14.00 日一次。3000 日×六種作息：平均 12.66–12.88 日，最長 13.10–13.15 日 |
| firefly_walk 螢火散步 | **14** | 17–23（唔喺睡眠時） | — | 5／10 | PR #19 由 20 降到 14；用 play clip；音效暫借蝴蝶提示音降 3 半音 |
| sleeptalk 夢話 | **11** | 23–07 | — | 1／1–2 | |
| treasure 寶藏 | **18** | 08–22 | — | 3–6／2–3 | fallback；精力 ≥25 |
| grumpy 鬧脾氣 | 0（cond，唔入池） | — | — | 1／3–4 | 只係需求 <30 ≥2h；冷卻 48h。連點 5 下＝`grumpy_tap`（唔入池、冇獎勵、唔共用呢行文案／冷卻） |
| flash 閃光日 | 特殊 | — | 是 | 8／8–10 | 3%/日，已領旗標 |

自跑模擬（`node tests/sim-report.js`；offlineIgnoreDailyMax=true，p_hit 0.33，彩虹冷卻 240h，pity 提前 30h）：14 日離線入日記平均 31.0（中位 31、p95 37、最多 45；連彈窗共 33.0，2.36 個/日；冷卻違反 0）；每日 4／5 次開 app：事件 2.67／2.69 個/日（≤2.95）、彩虹每 13.4／13.4 日一次；④ 六種作息 × 300 種子 × 56 日：池抽取 2.25–2.30／日、彩虹最長間隔 13.94 日；⑤ 每種作息 4×750＝3000 日：池抽取 2.256–2.361／日，彩虹平均 12.66–12.88 日、最長 ≤13.15 日、240h 違反 0。

### QA 修正（PR #17）
- **P0 回撥當日（noDrawDay）**：`offlineReplay` 開頭先 `checkRollback`；每次補抽前 `noDrawAt(t)`（UTC 回撥日或早過 lastSaveTime−120s）→ 唔出。121 秒個 case：同一 UTC 日稍後再開，補抽＋保底都係 0。
- **P1 時鐘超前重設**：`sanitizeSaveTime` 記 `saveResetAt`；`resetToday` 當日跳過保底（stats.resetSkipGuarantee）。`G.save` 同 `SIM.applyOffline` 都只將 `lastSeen` 向前（max），重設係唯一例外。
- **P1 早鳥**：`events.earlyBird {hours [5,9], hitMul 1.1}`（本機 05–09 p_hit×1.1）→ 早鳥作息池抽取 2.32／日（目標 2.2–2.4）。
- **P1 彩虹 pity**：`rainbowPityDays 14`、`rainbowPityLeadH 30`（原 26；3000 日最長間隔 14.05 日，超 pity 約 1h）、彩虹權重維持 1；另加 `rainbowCooldownH 240`（距上次 240h 內唔出）。pity 只喺 17–23 窗、唔打穿冷卻／間隔／每日上限／回撥日。30h 令到期早過窗開：3000 日模擬平均 12.66–12.88 日，最長 13.10–13.15 日（≤14.00）。
- **P2 drawChance**：0.34→**0.33**。六種作息池抽取／日（3000 日，pity 提前 30h）：勤力 2.257、一般 2.279、上班族 2.263、輕度 2.304、早鳥 2.256、隔日 2.361（全部 2.2–2.4）。
- **P2 日記提示**：「就快過期」改為「2 日後作廢」。`.ibtn` 熱區按畫面縮放放大，360 闊直向（含 dpr）縮放後 ≥44 CSS px。
- **P2 閃光日 72h**：`flashCooldownH 72`（flash `cooldownH: 72`）；`rollFlash` 用實時 ms 判 72h，未夠就當日唔開（stats.flashCdSkip）。

### beh（行為）／light／quality／audio
見 `PARAMS.beh`、`PARAMS.light`、`PARAMS.quality`、`PARAMS.audio`。重點：
- beh：`envCooldown 260`（曬太陽／撞花盆共用冷卻）、`stateWeights {stay40, walk15, jump4, play8, nap12, sunbathe10, bump6}`、`personality {sticky .9, sleepy .8, timid .7}`、`tap {rapidCount 5, rapidWindow 10, cuddlyCount 3, cuddlyWindow 2, sleepyHold 4, grumpyDur 3.2, grumpyCooldown 8}`、`variantEvery [6,15]`、`variantWeights {blink50, sway30, yawn20}`。
- light：`periodStarts {morning 7, noon 11, evening 17, night 23}`，各時段 `beh` 倍率。
- quality：rAF 幀間隔窗口 `windowFrames 120`、`slowMs 28`、連續 `slowWindows 2` 窗平均超標 → 降一級；低端機（核心 ≤4 或 deviceMemory ≤4）新存檔預設 `low`；`?debug=1` 唔自動降。
- audio：`bus`、`xfadeSec 1.5`、`petMinGap 4`、`petRate [0.95,1.05]`、`needWarnEvery 90`、`eventBlockPet 0.5`；小節長 `barSec = 240/68 = 3.5294s`。

### window.__qa.pet（遊測）
`seed`／`log`（行為日誌）／`clearLog()`／`reseed(n)`／`clock.{use,set,advance,real,now,setHour}`（假時鐘）／`pause(b)`／`step(sec)`／`state()`／`force(state)`／`forceEvent(id)`／`tapPet(n)`（模擬點寵物；瞓緊＝輕喚醒）／`lightWake()`／`events()`／`eventLog()`（事件觸發紀錄，含 firefly_walk）／`claimedFlashDates()`／`flashToday()`／`pool()`（事件池權重表）／`lastSaveTime()`／`suppressed()`（時間回撥保護狀態）／`audio()`／`audioLog()`。
URL：`?debug=1&seed=7&hour=19&q=high&ev=0`（`ev=0` 關閉自然事件，方便測試）。

## 光卵（egg）圖集
egg 用遊美 `art/atlas_egg.png/json`（`atlas_legacy`，1024×64，32×32 幀，`egg_idle` ×4／`egg_glow` ×2；進度 ≥50% 或輕點時播 glow；atlas 無 pivot → 按遊美標準 (w/2, h-3)）。舊 `pet_tuanrong_atlas.png`（2048×134）已棄用，glimmer-a 內冇檔案冇引用（`tests/behavior.test.js` 掃描＋e2e 檢查網絡請求）。

## 遊美素材整合（團絨全套）
- **motion/**：23 clip 全 `ready:true`（sprout／radiant／soft atlas 已覆蓋重打；props 不變）。冇美術嘅額外 clip jump／grumpy／lookup／dig、dirty、dust 仍用 placeholder。`play` 位移為 0 → render 層 frame4–5 加 root-motion（64px +4／32px +2，`PARAMS.art.playRootMotion`）。
- **fx/events/**：`atlas_events` 9 個事件 icon（動畫），喺事件提示卡（48px）同寵物頭頂（事件頭 5 秒）播放；`iconPlaceholder`／`◌` 已移除。
- **scenes/daylight/**：`lighting.js` 讀 `daylight.json`（`LIGHT.setDaylight`）：早→early／午→noon／晚→dusk／夜→night（遊策時段 07／11／17／23 為界，JSON 嘅 hours 只作參考），新時段後 `blendSeconds`（1800）內淡入。花園模式：ambientMultiply 整屏 multiply（`PARAMS.light.dlAmbient` 0.6）、bloom／vignette 倍率（`dlBloomRef` 0.4／`dlVigRef` 0.3）、寵物 sprite 套 multiply＋add＋1px rim。可選房間皮膚（`?room=1`／`PARAMS.art.daylightBg`）用 bg＋light overlay（480×270 橫向，同直向花園唔配，見 docs/clip-format.md §9–10）。`__qa.pet.daylight()` 可讀現時狀態。
