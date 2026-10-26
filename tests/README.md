# tests/ 總覽（遊測；全部原創、無私人／第三方內容）

環境：Node＋`playwright-core`（`/workspace/tools/pw/node_modules`，可用 `PW_PATH` 覆寫）、`/usr/bin/google-chrome`（`CHROME` 覆寫）、Python 3。被測 proto 以 `python3 -m http.server <port>` 起喺各自目錄。

| 目錄 | 腳本 | 用途 | 對應文件 |
|---|---|---|---|
| perf/ | `fps_probe.js`、`determinism_check.js`、`trace_capture.js`、`lighthouse.sh` | 風野競走 fps／決定性／trace／Lighthouse（CDP CPU 限速：high 1×／mid 4×／low 6×） | `QA/perf-budget-wind-race.md` |
| perf/ | `pet_fps_probe.js` | 微光小圃 fps 矩陣（畫質×檔位）、`--auto 1` 量自動降級、`--hour`／`--eval` | `QA/pet-deepening-test-plan.md` §5 |
| touch/ | `mock/index.html`、`touch_move_probe.js` | CDP 真觸控；虛擬搖桿／點擊移動／碰撞／傳送／對話（`window.__qa` 協議） | `QA/touch-move-feel-test.md`、`QA/week2-test-checklist.md` |
| save/ | `save_fuzz.js` | 存檔損毀／版本／往返／quota fuzz | `QA/save-replay-test-cases.md` |
| sim/ | `balance_fengye.py`(+`fengye_harness.js`)、`decay_weiguang.py`、`offline_cases.py` | 平衡／需求衰減／離線規則模擬 | `QA/balance-fengye-mvp.md`、`QA/test-plan-weiguang-xiaopu.md` |
| pet/ | `pet_events_final.py`（定案參數；退出碼 1＝有 FAIL，v5 定案參數＝螢火散步＋彩虹 w4＋p_hit 0.34＋首次開 app 即保底＋lastSaveTime 防改時鐘（110 案例）；`--multi 8` 做多 seed 一致性；目前 FAIL＝僅上班族作息總事件 2.91（>2.9，2/8 seed））、`pet_events_sim_legacy.py`（舊提案參數，僅參考）、`pet_behavior_sim.py`（定案行為參數）、`time_band_probe.js` | 事件池／離線上限／閃光日、行為頻率、就寢建議時段 | `QA/pet-deepening-test-plan.md` §1–4 |
| art/ | `art_budget_check.py` | 貼圖尺寸／預算／atlas JSON 檢查（FAIL→退出碼 1） | `QA/pet-deepening-test-plan.md` §5 |

各 `out/` 為可重生結果；注意結果係「相對基準」（headless 軟體繪圖），真機驗收見各文件。
