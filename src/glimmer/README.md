# 微光小圃（Glimmer Garden）— MVP 原型

原創養成遊戲《微光小圃》嘅可玩最小原型：HTML5 Canvas + 原生 JS，**無 build、無依賴、無外部素材**。
所有像素美術都係用程式喺 canvas 即時生成（原創）。設計依據：`game-design/docs-gdd/pet-one-pager.md`（第 12 節 MVP 範圍）。

## 點樣玩／運行
- 直接開 `index.html`（file:// 都得），或者喺本資料夾開任何靜態伺服器：`python3 -m http.server 8125` → `http://localhost:8125/`
- 手機（直向 390×844 最佳）用觸控；桌面用滑鼠。畫面會自動以整數倍像素縮放至適合視窗。
- **光卵**：輕點（8 下可孵化，亦會隨時間自然孵化）。
- **餵食**（星屑餅／暖菇飯／暖湯）、**玩耍**（逗玩／接星屑）、**清潔**（沖洗；輕點便便清走）、**關燈**（睡眠，精力每小時 +12，衰減 ×0.3；精力滿自動醒）。
- **接星屑**：45 秒，拖動籃子接星屑，避開暗石。光粒 = floor(分數/10)，上限 20；心情 +8／+20；每日首 5 次全額，之後減半。
- 芽崽成長滿 24 小時（可調）後按照顧品質 CQ 分支：燦光（≥70）／柔光（40–69）／微塵（<40）。
- 離線：離開 ≥5 分鐘再返嚟會按第 7 節公式推算（有效離線 E、需求保底 20、成長 ×50%、不會死亡），顯示 3 句回歸摘要＋光粒禮物。
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
src/main.js       存檔／離線／主迴圈／縮放／自動降畫質
tests/sim.test.js          Node 單元測試（無依賴）：node tests/sim.test.js
tests/e2e-playwright.js    端到端（playwright-core + 系統 Chrome）
tests/last-run-*.txt       最近一次測試輸出
screens/*.png              390×844 截圖（各狀態、各畫質、日夜、離線摘要…）
docs/engine-eval.md        引擎評估（Godot／Unity／Web）
```

## 測試
```
node tests/sim.test.js                                   # 82 項
python3 -m http.server 8125 &                            # 於本資料夾
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
