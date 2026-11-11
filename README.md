# 微光小圃 — Godot 4 移植（G0）

M1 用 Godot 4 重做。舊 HTML5／three.js（`code/glimmer-3d-h1`）凍結作參考，唔刪。

- 引擎：Godot 4.7.2.stable
- 開發基線：低畫質（穩定 30fps；無 DoF／glow）
- applicationId：`hk.vizard.glimmer.fpet.godot`（同舊 app 並排安裝）
- versionName `2.0.0-g0`，versionCode 1

G0 範圍：載入遊策 JSON、存檔、離線成長補時、核心需求／成長模擬、3D 花園（mesh＋寵物／細佬 billboard＋自主行＋執屎）、最簡 HUD。觀察模式／一鍵／狩獵／浮動團絨唔入 G0。

執行：`/home/box/tools/godot/godot --path /workspace/glimmer-godot`

測試：`bash tools/run_tests.sh`

匯出 APK：`bash tools/export_android.sh`（keystore 喺 repo 外）
