# tests/ 測試說明

目前 repo 尚未決定引擎（HTML5／Godot／Unity 未定），所以本文件列出兩個方案；定案後只保留對應方案。

## 方案 A：HTML5／網頁版
- **冒煙測試**：Playwright —— 開啟遊戲頁面，確認載入成功及無 console error。
- **效能**：Lighthouse（Chrome DevTools 或 `npx lighthouse <url> --view`）檢查 Performance、載入時間、主執行緒阻塞；FPS／記憶體用 Chrome Performance 面板另行記錄。
- 範例指令（遊戲頁面有 `package.json` 後）：
  ```
  npm i -D @playwright/test
  npx playwright install --with-deps chromium
  GAME_URL=http://localhost:8080 npx playwright test
  ```
- 之後可在 `tests/` 加入 `smoke.spec.js` 及 `playwright.config.js`（引擎定案為 HTML5 時才加）。

## 方案 B：Godot
- 單元／整合測試：**GUT** 或 **GdUnit4**（二選一），測試放 `tests/`（例如 `tests/unit/test_*.gd`）。
- 命令列執行（headless）及 CI 設定待有 Godot 專案後補充。

## 方案 C：Unity
- Unity Test Framework（EditMode／PlayMode），待定案後補充。

## 其他
- 手動測試及上架前檢查：見 `QA/release-checklist.md`；bug 記錄：見 `QA/bug-list.md`。
- 公開 repo：請勿放入私人資料或第三方版權素材。
