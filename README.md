# 微光小圃 — Godot 4 移植（M1a）

M1 用 Godot 4 重做。舊 HTML5／three.js（`code/glimmer-3d-h1`）凍結作參考，唔刪。

- 引擎：Godot 4.7.2.stable
- 開發基線：低畫質（穩定 30fps）。低檔仍係完整 3D 花園（同一場景／鏡頭／mesh／nav／遮擋），只關 shadow map、glow／DoF／fog，並降低 3D render scale；永遠唔退回分層 2D。
- applicationId：`hk.vizard.glimmer.fpet.godot`（同舊 app 並排安裝）
- versionName `2.0.0-m1a`，versionCode 3

G0／G0.1：載入遊策 JSON、存檔、離線成長補時、核心需求／成長模擬、3D 花園、最簡 HUD。

M1a（可玩）：個性驅動 Beehave 自主行為同家庭互動、點寵物跟拍放大、需求氣泡、底部一鍵餵／執／摸＋摘要卡。Android 有 PetOverlayService（浮動團絨）；用 `bash tools/export_android.sh` 出包（keystore 喺 repo 外，會注入 overlay 並把 GLES `required=false`）。

執行：`/home/box/tools/godot/godot --path /workspace/glimmer-godot`

測試：`bash tools/run_tests.sh`
