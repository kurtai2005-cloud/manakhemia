# tests/perf — 風野競走 效能／fps 基準工具

配合 `QA/perf-budget-wind-race.md`。全部只用 Node + `playwright-core` + Chrome，無私人資料。

| 檔案 | 用途 | 需要 |
|---|---|---|
| `fps_probe.js` | 自動開一場賽，用 rAF 取 fps／frame time 百分位、`UI.draw`／`G.tick` 耗時、JS heap、載入時間；按檔位（CPU 限速）對預算判 pass/fail，輸出 `out/fps-<tier>.json` | 頁面暴露 `window.__wr`（`G`／`UI`／`Sim`／`Data`） |
| `trace_capture.js` | 自動錄 Chrome Performance trace（`out/trace.json`），拖入 DevTools → Performance 睇火焰圖 | 同上 |
| `lighthouse.sh` | 載入基準（FCP／TBT／TTI／CLS／傳輸大小），mobile＋desktop | 網絡（npx lighthouse） |
| `determinism_check.js` | 「同種子重播一致」「與幀率無關」「輸入日誌重播一致」「一場 ≤120 秒」（純 Node，無 DOM） | `windrun-proto/src`（`data.js`／`sim.js`） |

## 快速開始
```bash
# 1) 起靜態伺服器（windrun-proto 目錄）
cd windrun-proto && python3 -m http.server 8124 &
# 2) 確定性＋時長（秒級）
node tests/perf/determinism_check.js windrun-proto/src 300
# 3) fps：三個檔位各跑一場（每場約 100 秒；--mul 4 可 4 倍速 smoke test，但唔可用嚟出正式數）
for t in high mid low; do node tests/perf/fps_probe.js --url http://localhost:8124/index.html --tier $t; done
# 4) Chrome trace／Lighthouse
node tests/perf/trace_capture.js --url http://localhost:8124/index.html --seconds 20 --cpu 4
tests/perf/lighthouse.sh http://localhost:8124/index.html
```
環境變數：`CHROME_PATH`（預設 `/usr/bin/google-chrome`）、`PW_PATH`（`playwright-core` 路徑；預設試 `/workspace/tools/pw/node_modules/playwright-core` 再試全域）。

## 限制（務必睇）
- 檔位用 CDP `Emulation.setCPUThrottlingRate`（high 1×／mid 4×／low 6×）＝**相對**限速，唔等於真機；headless 嘅 GPU 係軟體繪圖。**正式驗收一定要真機**（見預算文件第 4 節）。
- `fps_probe.js` 量嘅係 `requestAnimationFrame` 間隔；headless Chrome 嘅 rAF 鎖 60 Hz，高更新率螢幕（90／120 Hz）要用真機。
- Lighthouse 對純 canvas 頁面會出 `NO_LCP`（performance score 顯示 0）：屬已知限制，睇 FCP／TBT／TTI／CLS／傳輸量即可；若要 LCP，頁面需有 DOM 載入畫面（例如標題或 logo `<img>`）。
- `out/` 內係生成結果，可重生，唔需要入庫。

---
其他測試工具（touch／save／pet／art／pet_fps_probe）見上層 `tests/README.md`。
