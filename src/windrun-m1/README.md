# 風野競走（Windrun）— 可玩最小原型

純 HTML5 Canvas＋原生 JavaScript，**無建置、無依賴**。直向手機版（設計尺寸 540×960，自動縮放貼合畫面），支援觸控同滑鼠。
設計依據：`wind-race-one-pager-v2.md`（遊策）。所有美術係 Canvas 即時繪畫嘅原創向量圖形；音效係 WebAudio 嘟嘟聲（可喺主頁關閉）。

## 點樣行

```bash
cd windrun-proto
python3 -m http.server 8000
# 瀏覽器開 http://localhost:8000/   （手機：同一 Wi-Fi 開 http://<電腦IP>:8000/）
```
亦可直接雙擊 `index.html`（file://）開，存檔用 localStorage。

## 點樣玩
主頁 → **養成**（每回合 3 個行動：餵食／訓練／休息）→ **組隊**（揀關卡、揀 2–3 隻、排首發＋後備）→ **比賽**（自動跑，你只揀幾時換人、幾時放技能）→ **結算**（經驗、彩帶、升級）→ 返回養成。
- 點下方後備頭像＝換人；點大按鈕＝放技能（每隻每場一次，交棒／入場期間唔得）。
- 右上角 `1x／2x 速度` 切換比賽速度。
- 每段地形下面有「我方現役／對手現役」適性圖示（4 級訊號格，乘風＝金色星）。
- 3 關：①苔坡入門賽（2 隻隊）②灘霜盃 ③懸橋峽谷賽（影子隊，固定預錄腳本）。通關解鎖下一關。

## 檔案
```
index.html            入口（MVP）
src/data.js           PARAMS 全部可調參數＋地形／野靈／技能／關卡（Node／瀏覽器通用）
src/sim.js            比賽邏輯（無 DOM）：固定步長、可種子 RNG、hashState
src/api.js            模擬／表現薄 API＋重播錄製／回放／驗證（docs/replay-format.md）
src/ui.js, main.js    Canvas 繪圖／輸入／音效；遊戲狀態、存檔、主迴圈（只經 Api 操作比賽）
src/fx.js, fx-lab.html     後處理實驗（procedural）；4 檔位 off/low/mid/high
src/save.js           存檔 JSON v1（docs/save-format.md）
src/town-map.js       城鎮圖生成（Tiled JSON 子集）＋格子碰撞＋A*（DOM-free）
src/town.js, town-lab.html 城鎮實驗頁（圖塊／光／遮擋／景深／點擊移動／搖桿／傳送）
art/                  美術包（art-wind 副本）＋ art/town/（程序生成示範圖塊、道具、角色、地圖 JSON）
tools/                gen_town_assets.py、gen-town-json.js、godot-bench/（Godot 4 基準）
tests/                sim／replay／save／town-map 單元測試；town-e2e、e2e-*（Playwright）；fx-bench、town-bench
docs/                 engine-eval.md（Q1–13）、replay-format.md、save-format.md
screens/              驗證截圖
```

## 測試
```bash
node tests/sim.test.js          # 公式＋200 場 AI vs AI＋關卡難度
node tests/replay.test.js 200   # 重播（log／regen）＋純度＋確定性
node tests/save.test.js         # 存檔 v1（清洗／遷移／存檔碼／Store／衝突）
node tests/town-map.test.js     # 地圖生成／碰撞／A*＋batch2 專項
# 瀏覽器測試（需 Playwright；先 python3 -m http.server 8131）
BASE=http://localhost:8131/ node tests/town-e2e.js
node tests/fx-bench.js ; node tests/town-bench.js     # 無頭桌面 Chrome 基準（非真機）
```

## M1 第 2 週：冒險切片（walk → talk → 報名）
```
walk.html             可玩切片：晨苔鎮（遊美 batch2 tilemap）→ 老鐘序章 → 蕨影小徑結緣（占位面板）→ 返鎮報名（Sang）。⚙ 為開發面板（非遊戲內容）
town-lab.html         同一 tilemap 嘅渲染／光／遮擋實驗（?map=corner|adv 為 fallback）；town-lab-gen.html＝舊程序生成頁
src/tiled.js          Tiled JSON 解碼＋相容性檢查（collision firstgid 由 tilemap 讀）
src/scene-events.js   事件正規化（遊美＋遊策兩套詞彙）＋ overlay（data/overlay/*.json）
src/world.js          場景／玩家／NPC（遊美圖集，腳底 y 排序）／碰撞／光／互動
src/dialogue.js, dialogue-ui.js   dialogue/v1 執行＋lint；UI（打字機／頭像／選項／skip）
src/logic.js          旗標／變數／actions（match/v1 §3.1 finishMatch）
src/adventure.js      host：資料載入、場景切換、存檔、占位戰鬥面板
data/                 tuning、flags（登記表）、cups、matches、dialogue（遊策匯入）、overlay
docs/                 flags.md、tiled-compat.md、dialogue-import-notes.md、save-format.md、engine-eval.md
```
```bash
node tests/dialogue.test.js ; node tests/tiled-compat.test.js
BASE=http://localhost:8131/ node tests/walk-e2e.js     # 約 2 分鐘；需 Playwright＋ /usr/bin/google-chrome
```

## 參數表（`src/data.js` → `PARAMS`，名稱對應一頁設計第 12 節）
| 參數 | 預設 | 說明 |
|---|---|---|
| `speed_scale_K` | 0.15 | 速度 = 基礎速度 × K × A × C × G × S |
| `aptitude_mult[4]` | 0.65／0.90／1.00／1.12 | 陌路／識路／熟路／乘風 |
| `catchup_per_m`／`catchup_cap`／`catchup_cap_bonus_trait` | 0.004／0.08／0.03 | 只作用落後方；「韌性」上限 +3% |
| `track_len`／`segment_len` | 1000／200 | 5 段 |
| `stamina_drain{}` | 苔坡 1.6／碎礫 2.0／淺灘 2.4／霜面 2.0／懸橋 2.8 | 每秒；再乘 (1 − 力量 × `power_drain_coeff`) |
| `stamina_max_range` | [60, 200] | 耐力上限鉗制 |
| `power_drain_coeff` | 0.002 | 力量用途（一頁設計未定義，遊程補充） |
| `bench_regen` | 0.5 | 後備每秒回耐力 |
| `gusto_thresholds`／`gusto_values` | 30%、10%／1.0、0.9、0.8、0.7 | >30% 1.0；30→10% 線性降至 0.9；≤10% 降至 0.8；耗盡 0.7 |
| `swap_out_base`／`swap_out_calm_coeff`／`swap_out_min` | 1.4／0.006／0.5 | 交棒時間 = clamp(1.4 − 冷靜×0.006, 0.5, 1.4) 秒 |
| `swap_out_gusto`／`swap_in_time`／`swap_in_gusto_start` | 0.6／1.5／0.7 | 交棒期 G＝0.6；入場 1.5 秒 G 由 0.7 升至 1.0 |
| `swap_cooldown` | 4 | 由按下換人起計 |
| `skill_duration{}`／`skill_mult{}`／`stamina_restore_skill` | 3／3／5 秒；1.25／0.8；20 | 疾風衝／絆草／風罩；回氣 |
| `exp_base`／`exp_per_level`／`level_cap` | 30／12／20 | 升級所需 = 30 + 12×等級 |
| `growth_per_level{}`／`growth_star_mult[]` | 速度 0.4、力量 0.8、冷靜 0.8、耐力 1.5／0.85、1.0、1.2 | 每級成長（乘成長星級） |
| `train_gain{}`／`feed_gain`／`train_cap{}` | 速度 1、力量 2、冷靜 2／耐力 +3／上限 10、30、30、40 | 養成 |
| `action_exp{}`／`actions_per_turn` | 餵食 12、訓練 20、休息 8／3 | 行動經驗；每回合行動數 |
| `rest_restore`／`cond_cost_per_race`／`cond_regen_per_turn`／`cond_stamina_floor` | 40／15／10／0.6 | 「狀態」：影響起跑耐力（狀態 0＝60%） |
| `team_size_max`／`team_size_mvp` | 6／3 | |
| `ai_swap_stamina_pct`／`ai_swap_apt_gap` | 0.30／2 | 對手 AI：耐力 <30% 或下一段適性差 ≥2 級就換人 |
| `ai_swap_lead_m`／`ai_no_swap_last_m`／`ai_bench_min_pct`／`ai_think_interval`／`ai_skill_delay`／`ai_force_skill_m` | 20／60／0.4／0.5／6／150 | AI 細節 |
| `shadow_counter_window` | 2 | 影子隊：對手放技後 2 秒內反制 |
| `sim_dt`／`race_timeout` | 1/30／300 | 固定步長（結果可重現） |

## 已知缺口（MVP）
- 未做：結緣追越賽（關卡 2 首次結緣）、進化試煉、配對、好友借用、每日賽票／挑戰、廣告／季票、彩帶用途（只顯示累計）。
- 關卡 1 用 2 隻隊（依一頁設計第 7 節）；其餘 3 隻。
- 影子隊係固定腳本（按距離觸發換人／技能＋2 秒反制），非真實玩家快照。
- 音效只係簡單嘟嘟聲，無 BGM。
- 技能對勝負影響偏低（見測試數字），交遊測平衡。
