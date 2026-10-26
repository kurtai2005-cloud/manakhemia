# 《風野競走》效能預算＋手感測試＋基準量度（遊測）v2

> 依據：`game-design/docs-gdd/wind-race-modern-plan.md` **v2**（M1＝冒險垂直切片；第 8 節驗收①–⑧、第 9 節技術待辦 4／7／9、第 10 節首 2 週、第 11 節風險）。取代我早前按 v1 寫嘅預算草稿。
> 配套文件：`QA/touch-move-feel-test.md`（觸控移動手感）、`QA/save-replay-test-cases.md`（存檔／重播）、`QA/week2-test-checklist.md`（週 2 首輪測試清單）。腳本：`tests/perf/`、`tests/touch/`、`tests/save/`。
> 全原創、無第三方內容、無私人資料。數值皆為**提案／暫定**，等遊程 build 出嚟後以基準修正。

## 0. 結論先講
| 級 | 發現 | 建議 |
|---|---|---|
| **P0** | **「一場 ≤120 秒」要同 M1 演出一齊守**：驗收③寫明「一場賽 ≤120 秒且含入場／換棒／技能／衝線演出」。現時模擬最長 **106.8 s**（300 場隨機 3v3，全部 5 張賽道）；關 1 示範局 98.3 s。再加倒數 3.2 s＋入場 ≤5 s ＝ **≈115 s，只剩 ≈5 s** 俾所有換棒／技能／衝線演出 | 演出一律**唔暫停模擬**（只做表現層）；若要停（衝線特寫），計入時長並設硬上限；或遊策明確「120 s 只計開賽至衝線」（待確認，第 7 節） |
| **P0** | **「同種子重播一致」模擬層已達標，但 UI 層未接駁**：`determinism_check.js` 300 場：同種子、30／60／144／47 fps 切片、輸入日誌重播、JSON 往返全部一致；跨檔位（60fps／6× 限速＋4× 倍速）同一場結果逐位相同。**但** `main.js` 開賽種子取 `Date.now()`，冇記錄種子同輸入 → 實際遊玩**無法重播** | 4.1 一定要：開賽時寫入 `{seed, 隊伍快照, 輸入日誌}`；種子由存檔 RNG 派生 |
| **P1** | 現有 MVP（純 2D canvas）極輕：`UI.draw` 0.49 ms／幀（1×）；6× 限速仍 ≈47 fps，20× 限速 ≈13 fps → **安全邊際約 15×**，但亦代表 **HD-2D 疊加（景深／bloom／tilt-shift／光圖／多層視差）先係真正風險，現階段無法量** | 週 1 實驗 build（遊程第 9 節 7）出嚟即用 `fps_probe.js --eval` 量同一張晨苔鎮圖，作 go/no-go |
| P1 | Lighthouse（mobile 模擬）：FCP 1.68 s、**CLS 0.14**（>0.1 偏高，疑似 canvas／DOM 調整大小）、無 LCP（純 canvas 頁面，Lighthouse 報 `NO_LCP`，score 顯示 0） | 加 DOM 載入畫面；查 CLS 來源 |
| P1 | 冒險切片新增三類效能風險：①圖塊地圖多層＋遮擋排序＋視差／光圖（探索場景）②場景傳送載入（3 個場景共 ≈40×30、60×16 圖塊）③對話／選單長時間靜止畫面仍全幅重繪（電量） | 見第 1 節預算；靜止畫面限 30 fps 或髒矩形 |

## 1. 效能預算（M1：晨苔鎮＋迴風場＋蕨影小徑，賽事＝HD-2D 賽道）
### 1.1 裝置檔位（提案；實機型號待確認）
| 檔位 | 代表裝置（類型，非指定型號） | 用途 |
|---|---|---|
| 高 | 近 3 年旗艦 Android／桌面 Chrome（8 GB+，90／120 Hz 螢幕亦以 **60 fps 為上限**，因模擬固定步長） | 上限驗證、最高畫質 |
| 中 | 3–4 GB RAM、中階 SoC Android，Chrome 近 2 年 | **主驗收檔**（驗收⑦「中階 Android 或桌面 60 fps」） |
| 低 | 2 GB RAM／4 年以上舊機；或中階機開省電模式 | 驗收⑦「低檔 ≥30 fps」；自動降至低畫質（關後處理、預烘焙光圖） |
| 備 | iOS Safari（WebGL／音訊解鎖／安全區行為不同） | 發佈次序待遊策定（第 9 節 19）；先做 smoke test |

### 1.2 fps／frame time（探索、對話、賽事三類場景）
| 指標 | 高 | 中（主驗收） | 低 |
|---|---|---|---|
| 平均 fps（探索：晨苔鎮行走） | ≥58 | **≥58** | **≥30**（穩定 30，唔好 30↔60 跳） |
| 平均 fps（賽事：含演出） | ≥58 | **≥58** | **≥30** |
| 1% low fps | ≥50 | ≥45 | ≥24 |
| p95 frame time | ≤18 ms | ≤20 ms | ≤40 ms |
| 長幀（>33.3 ms）佔比 | ≤0.5% | ≤1% | ≤5% |
| 凍結幀（>100 ms）每 5 分鐘 | 0 | 0 | ≤2（傳送／載入除外） |
| 畫質預設 | 高 | 中 | 低（關景深／bloom／tilt-shift，光圖預烘焙） |

### 1.3 每幀預算（中檔，60 fps＝16.7 ms）— 供遊程做 HD-2D 取捨
| 項目 | 預算 | 備註 |
|---|---|---|
| 邏輯（輸入、移動、碰撞、NPC、對話、事件） | ≤2.0 ms | 探索場景；模擬層賽事步進現時 ≈0.01 ms，預算 ≤0.5 ms |
| 繪圖 CPU（圖塊批次、精靈、UI） | ≤6 ms | 靜態圖層預先合成成 chunk／圖集；draw call ≤150／幀 |
| GPU（含後處理） | ≤8 ms | 後處理 ≤3 ms（模糊用 ¼ 解析度；沿用 pet-one-pager 第 10 節做法） |
| 餘裕 | ≥1.5 ms | GC／系統波動 |
| 動態光 | ≤4 盞 | 沿用一頁式設計；低檔 0 盞（光圖疊加） |
| 粒子 | 高 300／中 150／低 60 | 地形粒子＋技能光效合計 |
| 同屏精靈 | ≤200 | 含 NPC、野靈、粒子貼圖 |
| 整數縮放 | 圖塊／像素角色一律整數倍（16 px 圖塊、32 px 人物、48／64 px 野靈） | 避免插值模糊、減少 shader |

### 1.4 記憶體／載入／電量／包體
| 項目 | 高 | 中 | 低 | 量度方法 |
|---|---|---|---|---|
| JS heap 峰值 | ≤150 MB | ≤150 MB | ≤100 MB | `performance.memory`（`--enable-precise-memory-info`）／Android Chrome DevTools Memory |
| 紋理／GPU 記憶體 | ≤128 MB | ≤96 MB | ≤64 MB | DevTools Layers／`adb shell dumpsys meminfo`（Graphics） |
| 整個遊戲程序總記憶體 | ≤500 MB | ≤350 MB | ≤250 MB | `adb shell dumpsys meminfo <chrome>`；低檔 OOM 殺頁面＝fail |
| **15 分鐘 soak**（城鎮→小路→賽事 循環） | heap 增長 ≤5 MB／10 分鐘；fps 唔隨時間下降 >10% | 同左 | 同左 | `fps_probe.js --eval`＋腳本循環；真機另加溫度 |
| 冷啟動到可互動（Wi-Fi／4G） | ≤2 s／≤3 s | ≤3 s／≤4 s | ≤5 s／≤6 s | Lighthouse TTI／`fps_probe.js` loadMs；真機用 DevTools Performance |
| 場景傳送（觸發→新場景可操作，含淡出） | ≤400 ms | **≤600 ms** | ≤1000 ms | `touch_move_probe.js` M7a（mock 現為 331 ms） |
| 開賽（行入起跑區→倒數開始） | ≤1 s | ≤1.5 s | ≤2.5 s | 事件日誌時間戳 |
| 快速入場：報名→開賽 | **≤30 s**（設計紅線，驗收②）| 同 | 同 | 計時＋步數（≤8 次點擊） |
| 首次完整流程 | **≤3 分鐘**（驗收②） | 同 | 同 | 新手試玩計時（≥3 人） |
| 初始下載 | ≤8 MB（M1，壓縮後） | 同 | 同 | Lighthouse `total-byte-weight`（MVP 現 76 KB）；其餘按場景懶載入，單場景 ≤3 MB |
| 音訊 | BGM 2 首＋SFX ≈20 個，總 ≤3 MB | 同 | 同 | 退背景必須停止 rAF／音訊 |
| 電量（前台 10 分鐘混合：行走＋對話＋1 場賽） | ≤4% | ≤4% | ≤5% | 真機 `adb shell dumpsys batterystats`／電量曲線 |
| 熱 | 15 分鐘後 fps 跌幅 ≤20%（熱降頻） | 同 | 同 | 真機 soak |
| 靜止畫面（對話、選單） | ≤30 fps 或僅重繪髒矩形 | 同 | 同 | 看 `UI.draw` 次數／幀 |
| 存檔寫入 | ≤20 ms／次（主執行緒） | 同 | ≤50 ms | `performance.now` 包 `persist()` |

### 1.5 驗收①–⑧ 與測試對應（M1，第 8 節）
| 驗收 | 內容 | 對應測試 |
|---|---|---|
| ① | 觸控喺晨苔鎮行去報名處，同 ≥3 NPC 對話（1 段推劇情） | `touch-move-feel-test.md` T-A／T-D；週 2 清單 W2-MOVE／W2-DLG |
| ② | 賽前流程每步可行；首次 ≤3 分鐘；快速入場 ≤30 秒 | 本檔 1.4；`week2-test-checklist.md` W2-FLOW |
| ③ | 一場賽 ≤120 秒（含演出） | `determinism_check.js` 時長項＋第 0 節 P0；實機計時 |
| ④ | 小路結緣賽、捕獲、入隊 | W2-CAPT（M1 後段）；存檔檢查見 `save-replay-test-cases.md` |
| ⑤ | 存檔→讀檔後位置、隊伍、旗標一致 | `save_fuzz.js` R01＋冒險 build 探針（`save-replay-test-cases.md` §2） |
| ⑥ | 同種子重播一致 | `determinism_check.js`（已 PASS）＋UI 接駁（P0） |
| ⑦ | 中階 60 fps／低檔 ≥30 fps | 1.2；`fps_probe.js`＋真機 |
| ⑧ | Kurt 試玩評分 | 非自動化；遊測整理問卷（可玩性、觸控、載入） |

## 2. 手感測試表（賽事＋流程；觸控移動見 `touch-move-feel-test.md`）
M1 範圍：5 隻跑動、換棒（基本）、2 個技能、跟拍＋衝線特寫、結算；**手感／震動、慢鏡、餘下技能特效已推到 M2／M3，本表唔測**。
| # | 項目 | pass 準則 | 量度方法 | 級 |
|---|---|---|---|---|
| F1 | 換棒按鈕：點擊→畫面首次反應（高亮／交棒者減速） | 端到端 ≤100 ms（頁面層 ≤67 ms） | Playwright 觸控＋rAF 時間戳；真機 240 fps 高速攝影 | P0 |
| F2 | 換棒冷卻（4 秒）提示 | 冷卻中點擊有明確「未可換」反饋（色／震動 M2）；倒數與模擬冷卻誤差 ≤0.1 s；結束瞬間可再用 | 讀 `race.sides[0].cooldown` 對比 UI | P0 |
| F3 | 換棒演出長度 | ≤1.5 s，且**唔暫停模擬**（第 0 節 P0）；期間再點換棒唔重複觸發 | 事件日誌＋模擬 t 連續性 | P0 |
| F4 | 技能按鈕（疾風衝等 2 個）：點擊→蓄力開始 | ≤100 ms 端到端；蓄力 0.3 s＋爆發＋持續光環，模擬效果於**固定 sim step** 生效（唔隨幀率） | 重播日誌對比不同 fps 下生效 step | P0 |
| F5 | 技能被擋（風罩）／被絆 | 有獨立可辨識反饋（色＋圖示，唔靠文字），≤1 s 內睇得明 | 眼看＋截圖；色盲模擬（deuteranopia）仍可分辨 | P1 |
| F6 | 換棒／技能誤觸防護 | 按鈕 ≥48 dp、離邊 ≥16 dp、間距 ≥8 dp；同時間點兩個按鈕唔會觸發兩個 | 版面檢查＋雙指測試 | P1 |
| F7 | 跟拍鏡頭 | 鏡頭位移逐幀抖動 ≤1 px（整數像素對齊）；換棒時過渡 ≤0.4 s | 逐幀取樣鏡頭座標 | P1 |
| F8 | 衝線特寫（最後 100 m 或差距 <3 m） | 觸發條件正確；特寫**唔改變勝負**；佔用時間計入 120 s | 同種子開／關特寫，勝負與終點差必須一致 | P0 |
| F9 | 入場介紹（≤5 秒） | 點擊即跳過（≤100 ms 響應）；跳過後狀態與唔跳過一致 | 觸控測試＋狀態對比 | P1 |
| F10 | 倒數→開賽 | 倒數 3.2 s 內可見；「行入起跑區站定」觸發 ≤1 幀判定；觸發後輸入鎖定防誤動 | 事件日誌 | P1 |
| F11 | 結算畫面 | 數字滾動 ≤1.2 s、點擊可跳；名次／經驗／風印與存檔一致（驗收⑤） | 讀存檔對比 | P1 |
| F12 | 退背景／來電／鎖屏 | 賽中回前台＝暫停狀態，模擬 `dt` 上限 0.1 s（現 `main.js` 已有）→ 唔瞬移、唔跳演出；音訊停 | Playwright `page.evaluate` 觸發 `visibilitychange`；真機實測 | P0 |
| F13 | 低檔 30 fps 手感 | 觸控端到端 ≤150 ms；演出時序按模擬時間，**唔因掉幀拖長** | 6× 限速跑 F1／F4 | P1 |
| F14 | 賽事效能 | 1.2 節三檔 fps；演出峰值（2 技能＋換棒同時）最長幀 ≤50 ms | `fps_probe.js` 加峰值段 | P0 |

## 3. 基準 fps 量度方法（HTML5）
### 3.1 已落地腳本（`tests/perf/`，詳見 `tests/perf/README.md`）
| 腳本 | 量咩 | 一行用法 |
|---|---|---|
| `fps_probe.js` | rAF 間隔 → avg fps、p50／p95／p99、1% low、>33／>50 ms 佔比；`UI.draw`／`G.tick` 耗時；JS heap；載入；賽事時長；pass/fail | `node fps_probe.js --url <build> --tier mid`；探索場景：`--eval "<JS：傳送到晨苔鎮並開始自動行路>" --duration 30` |
| `trace_capture.js` | Chrome Performance trace（拖入 DevTools） | `node trace_capture.js --url <build> --seconds 20 --cpu 4` |
| `lighthouse.sh` | FCP／TBT／TTI／CLS／傳輸量（mobile＋desktop） | `./lighthouse.sh <url>`（純 canvas 會 `NO_LCP`，睇其餘） |
| `determinism_check.js` | 同種子重播、幀率無關、輸入日誌重播、JSON 往返、純函數掃描、≤120 s | `node determinism_check.js <windrun/src> 300` |

### 3.2 手動：Chrome DevTools Performance（含真機）
1. 桌面：開 build → F12 → **Performance** → 齒輪設 **CPU：4× slowdown**（模擬中檔）／6×（低檔）→ **Network：Fast 4G**。
2. Rendering 面板勾 **Frame Rendering Stats**（即時 fps／GPU 記憶體）。
3. 錄 20–30 秒（探索：沿固定路線行；賽事：整場），停止後睇 **Frames** 泳道（紅＝掉幀）、**Main** 火焰圖（`UI.draw`、後處理、GC）、**GPU**。
4. 記錄：avg fps、最長幀、`Long task` 數、`Minor GC` 頻率。同一路線至少 3 次取中位數。
5. **真機 Android**：USB 偵錯 → 桌面 Chrome `chrome://inspect` → Inspect 遠端分頁 → 同上錄 Performance；電量／記憶體用 `adb shell dumpsys batterystats --reset` → 玩 10 分鐘 → `dumpsys batterystats`；`adb shell dumpsys meminfo <chrome package>`。
6. 結果填 3.4 表。

### 3.3 Lighthouse（載入基準）
`./lighthouse.sh http://localhost:8124/index.html`（mobile＝Moto G Power 模擬＋Slow 4G＋4× CPU；devtools 限速）。記 FCP、TBT、TTI、CLS、total byte weight。**局限**：唔量賽中 fps；canvas 頁無 LCP。

### 3.4 基準結果（遊測於 box，MVP 純 2D canvas，Chrome headless＋軟體繪圖，390×844@2，關 1 示範局 98.3 s；**只作相對基準，唔代表真機**）
| 檔位（CPU 限速） | avg fps | p95 frame | 1% low | >33 ms 佔比 | `UI.draw` 平均／p95 | heap | 載入 |
|---|---|---|---|---|---|---|---|
| 高（1×） | 60.0 | 16.7 ms | 59.5 | 0% | 0.49／0.70 ms | 3.0 MB | 22 ms |
| 中（4×） | 59.0 | 16.8 ms | 24.7 | 0.5% | 1.86／2.70 ms | 2.8 MB | 44 ms |
| 低（6×） | 47.4 | 33.4 ms | 21.2 | 5.62% | 2.77／3.90 ms | 2.2 MB | 210 ms |
| 極限（20×，較早一次量度） | 12.9 | 100 ms | 7.5 | 99.2% | 10.7／15.5 ms | 3.5 MB | 607 ms |
解讀：MVP 中檔幾乎滿分；低檔（6×）已有 5.6% 長幀（>33 ms）、1% low 21 fps（兩次量度 4.1–5.6%，有 run-to-run 波動），預算可行但邊際唔大——HD-2D 加落去前就要有降級方案。重現：`node tests/perf/fps_probe.js --tier {high|mid|low}`；原始 JSON 喺 `tests/perf/out/`。
Lighthouse（同 build）：mobile FCP 1,682 ms／CLS 0.139／TBT 0／傳輸 76 KB；desktop FCP 73 ms。
重播一致：同一場（凍結種子）喺「高檔 4× 倍速」同「低檔 6× 限速 1×」得出相同結果（勝方、時長 98.2918 s、終點 987.587／1000.077、換人次數逐位相同）。

### 3.5 CI 化建議
`determinism_check.js`（秒級）＋`save_fuzz.js`（約 10 秒）＋`touch_move_probe.js`（約 25 秒）每次 PR 跑；`fps_probe.js` 三檔夜間跑，結果 JSON 入 artifact，`pass` 全 true 先綠燈；真機 fps／電量每個里程碑手動一次。

## 4. 真機驗收（自動化代替唔到）
- 至少 1 部中階＋1 部低階 Android 實機（型號待 Kurt 提供，第 7 節）；每部跑：fps（3.2）、15 分鐘 soak、電量 10 分鐘、觸控延遲（240 fps 高速攝影，由觸碰到畫面變化數幀）。
- 觸控物理：手汗、保護貼、單手拇指可及範圍；系統手勢列（返回手勢）與畫面邊緣按鈕衝突。

## 5. 缺漏輸入（需遊策／遊程／Kurt）
1. 「120 秒」計算範圍：只開賽至衝線，抑或包括入場／倒數／演出（驗收③字面包含入場）？
2. 目標實機型號（中／低檔各至少 1 部）；iOS 是否 M1 範圍。
3. 引擎／框架決定（第 9 節 1、7）：若離開 HTML5，`fps_probe.js` 需改用原生量度（Godot Profiler／Unity Profiler／`adb gfxinfo`）。
4. 冒險 build 需暴露 `window.__qa`／`__wr` 測試鉤（協議見 `touch-move-feel-test.md` §0）；`G.race.sim` 需記錄種子＋輸入日誌。
5. 存檔 key 同欄位表（第 9 節 12）。
