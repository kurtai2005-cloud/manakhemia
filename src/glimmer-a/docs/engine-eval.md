# 引擎評估（GDD 第 11 節）— Godot／Unity／Web

> 說明：以下**體積、fps、時間為估算**（標「估」），未喺實機驗證；授權費用條款易變，標「待核實」者請以官方最新條款為準。
> 本原型已用 Web（Canvas 2D）實作，headless Chrome 軟件渲染下 195×422 藝術網格、390×844 輸出：關／低 約 2.6 ms／幀、中 約 7 ms、高 約 9 ms（**非真機**）。

## 比較表

| 題目 | Godot 4（2D） | Unity（URP 2D） | Web（Canvas 2D／WebGL／PixiJS） |
|---|---|---|---|
| 1. HD-2D 後處理 | 可行：CanvasItem shader 做景深／移軸、WorldEnvironment glow 做 bloom、Light2D 做動態光；體積光用偽造光柱。難度中 | 最成熟：URP 2D Light、Volume 後處理、Shader Graph；體積光偽造。難度中低，但專案較重 | 可行：Canvas 2D 以降解析度模糊鏈做景深／bloom／移軸（本原型已做）；WebGL／Pixi filter 更省、更靈活。難度中 |
| 2. APK／包體（估） | 空專案約 20–30 MB（匯出模板）；加素材＋後處理估 30–45 MB | 空專案約 25–40 MB；加素材＋後處理估 40–70 MB | PWA／網頁：本原型原始碼約 100 KB 級、零素材；Capacitor 包 APK 估 5–15 MB（含 WebView 殼） |
| 3. 中低階 Android 效能（估） | 2D 60 fps 可期；後處理需降檔；發熱中 | 2D 尚可，後處理＋URP 喺 3–4GB RAM 機要降檔；耗電較高 | Canvas 2D 降解析度後處理約可 30–60 fps；WebView 受機種影響大，發熱同耗電視乎後處理檔位。已有 高／中／低／關 與自動降檔 |
| 4. 1–2 週 MVP 風險／上手 | 低–中：GDScript 易學，需熟編輯器；團隊若無經驗要學習 | 中：功能強但專案設定同包體管理較繁；C# 成熟 | 低：零工具鏈、即改即見；本 MVP 已可玩。風險在 WebView 效能與長期工程化 |
| 5. 部署／日後推送連線 | Web 匯出（WASM）體積大、載入慢；APK 直接匯出；推送需第三方外掛／原生橋 | WebGL 匯出體積大；APK／IPA 成熟；推送／連線有官方／第三方服務 | 網頁即玩；PWA 加到主畫面；APK 用 Capacitor／TWA；推送見下 |
| 6. 授權／費用 | MIT，無授權費、無 runtime fee | 個人版有收入／資金門檻、runtime fee 條款近年有變動 —— **待核實**官方最新條款 | 瀏覽器技術免費；PixiJS 等函式庫為開源（MIT，使用前核實）；Capacitor 為開源 |

## 建議
**MVP 用 HTML5（Canvas/JS）**：零安裝、即時分享連結俾 Kurt／善哥試玩，迭代最快。`src/sim.js` 為 DOM-free、可設種子 RNG、Node 可跑，已有 82 項測試；日後若改 Godot／Unity，只需移植 sim（邏輯短、參數集中喺 `PARAMS`）同重做渲染層。
若遊測後確認要上架商店且後處理要更重（真 3D 光影、更多光源），再評估 Godot（授權最簡單）。

## PWA／Capacitor（APK）路徑
1. 加 `manifest.webmanifest` ＋ service worker（離線快取）→ 可「加到主畫面」，達到近 app 體驗（估 0.5–1 日）。
2. 用 Capacitor 包 WebView 殼出 APK／AAB（估 1–2 日含簽名、圖示）；高階後處理建議預設「中」，由自動降檔保底。
3. 上架 Google Play 需開發者帳戶（費用待核實）。

## 推送通知路徑
- 網頁／PWA：Web Push（需 service worker＋推送伺服器；Android Chrome 支援，iOS 需 16.4+ 且已加到主畫面）—— 兼容性待核實。
- Capacitor：用原生推送外掛（如 FCM）；亦可用本機排程通知（離線推算結果已可預測「需求將跌至 20」等時間點，毋須後端）。
- GDD 第 12 節 MVP 不含推送；`PARAMS.notify*` 已預留參數。
