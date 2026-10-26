# 整合檢查：現有 MVP 能否承載「行為狀態機＋事件系統」（方案 A · 第 1 週）

> 結論先行：**可以，而且唔使重寫**。現有架構（DOM-free `sim.js`＋純繪圖 `render.js`＋薄 `ui.js`）剛好有三個天然掛點。改動集中喺「加模組＋三處小接口」，冇破壞性改動。

## 1. 現有結構同掛點

| 現況 | 可唔可以承載 | 做法 |
|---|---|---|
| `sim.step(s,dt,opts)` 固定步長、`advance` 分塊推進、`applyOffline` 用有效時間 E | ✅ 事件天然應該跟「有效時間」行 | 加 **step hook**（`SIM.addStepHook`），`events.js` 註冊；`sim` 唔 `require` events，單向依賴 |
| `rd.act(name,dur)` 單一腳本動畫（eat／happy） | ⚠️ 只有「全域單一動畫」，冇位置、冇狀態 | 保留，變成狀態機最高優先級 **override**（餵食／玩耍期間行為機讓路） |
| `genPet({anim,frame,face})` 程序化像素＋cache | ✅ 加 `clip/expr/gaze`；cache key 加維度 | `clip→程序化 sprite` 函數 = 美術未到位前嘅佔位；日後換圖集只動呢個函數 |
| `render.frame(view)` 光照：`lookAt(hour)`＋`lights[]`＋post-fx | ✅ | 新 `lighting.js` 輸出 `view.light`；render 只吃參數（燈色混合、`lanternMul`、`ambient`、色調疊層） |
| `ui.pointerdown`（hit-test `petBox()`） | ⚠️ `petBox` 以 CX 固定；寵物而家會走動 | `petBox()` 加入寵物 x 偏移；點擊轉成 `Behavior.tap('pet'｜'ground')` |
| `s.ev` 事件佇列（fed／hatch…） | ✅ 概念相近 | 新事件系統獨立放 `s.evs`（會存檔），UI 用 `takePending/tickActive` 消化 |
| 存檔 v1 `deserialize` 合併預設值 | ✅ 向後相容 | `s.evs` 缺省 = null，惰性建立；舊存檔照載 |

## 2. 需要改動（最小集）

1. **新增** `behavior.js`、`events.js`、`lighting.js`（全部 DOM-free，UMD，可 Node 測）。
2. **data.js**：`PARAMS.beh / events / light`、`CLIPS`、`EXPRESSIONS`、`EXPR_RULES`、`PROP_KINDS`、`EVENTS`（全部數值入表，可調）。
3. **sim.js**：`addStepHook`；`opts.off`（離線時鐘：`hour0/T/E/done`）；`applyOffline` 收集事件 log 併入摘要（仍 ≤3 句）；`newState/deserialize` 加 `evs`。
4. **render.js**：`genPet` 吃 `clip/expr/gaze`；新增陽光斑、花盆、小道具、事件視覺、時段光照。
5. **ui/main/index.html**：接 tap、事件卡 `#evcard`、debug 按鈕、`?period=`／`?seed=`／`?ev=0`。

## 3. 風險

| 風險 | 影響 | 緩解 |
|---|---|---|
| 行為／事件用 RNG，影響存檔重現 | 測試不穩 | 全用 `makeRng`（mulberry32）種子；`evs.rs` 存檔；行為機獨立 RNG，唔食 sim 嘅 RNG；禁用 `Math.random`／`Date` |
| 固定步長累加器浮點漂移 | 多／少一步 | `acc >= FIX − 1e-9`；單幀最多 40 步 |
| 離線事件令摘要超過 3 句或帶懲罰語氣 | 違反 GDD | 摘要 L2 事件句最多列 2 個，多出以「另外 n 件小事」；事件只加光粒／心情（`max(0,…)`），離線 hook 不扣任何需求 |
| sprite cache 隨 clip×frame×expr×gaze 增長 | 記憶體 | 懶生成；估計 <400 張小圖（≤72×86）；日後換圖集後此 cache 取消 |
| 事件喺舊 e2e 流程亂入，污染截圖 | 測試 flaky | 舊流程用 `?ev=0`；新段落用 `force` |
| 日界線以「鐘點回繞」判斷，非日曆 | 極端 `?hour` 覆寫唔會跨日 | debug 覆寫下事件仍靠有效時鐘抽選；保底只喺鐘點 ≥20 先觸發 |
| 自主 nap／sunbathe 同真實睡眠混淆 | 玩家誤解 | 自主睡只係演出，**唔改** `s.sleeping`／需求；真睡（關燈）優先 |
| 行為機令寵物離開 CX，現有 UI（食物／球／便便位）錨點偏移 | 視覺錯位 | override 期間寵物自動走返 CX（`retreatSpeed`），食物／球仍以 CX 為準 |
| 光照疊層令 post-fx 成本增加 | 低階機卡 | 只加一個全屏 `fillRect`；沿用 quality 分級 |

## 4. 唔會做（本週範圍外）
真實美術圖集、天氣實裝（只留 `Light.addModifier` hook）、成就、多寵物。
