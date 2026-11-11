# QA：Godot M1a（`8da4d168`）

唯讀 `code/glimmer-godot` @ `8da4d168e7e693a13a4e3faf612bff1135a11e4a`，tree `5f4ccc27dc021e2c46c2d22a925889e4bda4a6c0`。由 `86769723` 快進。Godot `4.7.2.stable.official.ed1daf0bf`。畫面用 xvfb（1280×1280）＋ `--display-driver x11 --rendering-driver opengl3 --audio-driver Dummy`。冇改 code branch，冇 merge。

截圖：`QA/shots-m1a/`（倉庫煙測 19 張＋橫向 1 張）。單元測試：`res://tests/TestMain.tscn`（`tests/test_runner.gd`）。

## 275 項

`=== 275 passed, 0 failed ===`，退出碼 0。涵蓋舊離線補時（保底 20、成長封頂 24h、光粒只係離線禮物、時鐘回撥 T=0、resume／focus 唔雙重補、有變先寫檔、10 分／1h／8h／24h／48h）同 M1a：一鍵照顧、個性、需要泡泡、art-fix1、UI／Pet bus、Beehave＋家庭、鏡頭。

退出時 Beehave debugger 報 `Capture not registered: 'beehave'`，同 G0.1 一樣有 ObjectDB／resource 未放。跑測試期間冇失敗斷言。

## 五分鐘同低檔 3D

低檔開住 300.0 秒。開頭同收尾都係 25 個 `MeshInstance3D`、tier 仍然 `LOW`。期間冇 script error。退出時 Beehave 報 `Capture not registered`，同測試收尾一樣。

煙測 `Main children=42`，低檔同中檔都係同一個 3D 花園。`QualitySettings` 仍然唔准低檔退回分層 2D。冇 script error。

低檔幀（llvmpipe，唔係手機）：cap 平均 33.33 ms、p95 **33.48** ms（`Engine.max_fps=30`）。解開上限：平均 5.88、p95 **6.74**、最大 9.19（n=90）。中檔 cap p95 16.80（有一幀 187.58，所以平均 19.23）。真機 Perfetto 未做。

## 直向

`project.godot:38` 仍然係手提直向。852×393 照畫花園，冇 `PortraitLock`。`QA/shots-m1a/land-852x393-day.png`。鏡頭 dist 被夾到 80，寵物高變成 54%。下面 P2。

## 畫面（G0.1 仍然要）

390 日間地面 luma 126，夜地 16。夜空 64，日空 220。夜地同遠山都壓暗，窗同燈籠有光，時鐘顯示 23:00（跟假鐘）。日間團絨仍然係奶油色。

Omni、遠草各向異性、細佬 pivot (24, 45)、walk 10 都喺 275 項入面過。樹後／屋後而家係總覽鏡頭，天空 13.3%／12.8%，俯角留喺 42°。遊策已接受舊跟拍時 26–28%，呢輪總覽冇再頂到 50°。

## M1a 玩法

個性：出生 [−3, 3]，一日漂移夾 ±2，行路倍率 1.2／0.85。`PetBrain` 用 Beehave，`FamilyDirector.force("walk_together")` 兩邊都標到。撳寵物走 `Main.gd:1063` `set_cam_follow`。

鏡頭（390×844 低檔，`qa_framing`）：

| 模式 | 寵物高 | 腳底 | 天空 | texel | 可見闊 |
|---|---:|---:|---:|---:|---:|
| 總覽 | 10.05% | 55.2% | 14.4% | 1.17 | 228 |
| 跟拍 | 18.1% | 57.3% | 15.9% | 2.04 | 142 |

總覽過 ≥10%。跟拍 18.1%，測試容差係 20% 減 2 個百分點，所以 275 項過；大約係 20%。768 總覽 texel 1.96（×2）、寵物高 14.8%、可見闊 256。390 總覽 texel 1.17，未鎖到 ×2／×3。`Main.gd:1141-1148`：總覽只有寵物仍 ≥10% 而且花園仍見 ≥80% 先跟整數倍。下面 P3。

需要文字列已拆。頭頂改 `NeedBubble`（`Main.gd:1054`）。底欄係餵／執／摸三個 icon 掣（`Hud.gd:52-60`）。總結卡係 icon＋數字，截圖見到「×2」。時鐘 `12:00`／`23:00` 仍然係短 Label（`Hud.gd:30`），唔係舊的飢／心／潔／力長句。

`m1a-bubbles.png` 寵物頭頂有一小塊非草地像素（大約 8 行）。目視好細。已知太淡，唔開等級。

聲：86 個 ogg 仍然在。bus 係 Master、BGM、AMB、SFX、UI、Pet（`audio/default_bus_layout.tres:22-32`）。`AudioManager.bus_for`：UI hook → UI，寵物聲 → Pet（`AudioManager.gd:155-166`）。275 項過。

art-fix1：細佬 pivot (24, 45)，scratch 等 clip 讀 M 圖集；訪客蝸牛／婆婆／螢火蟲 clip 都有，唔係團絨 L。站立初始條仍然係細佬 A1（`Main.gd:345` 同 `:359`）。靜止截圖兩個藍色角色睇落一樣。下面 P3。

## 字

源雲明體係選定的界面字，唔再當錯。`Hud.gd:24` 載 `GenWanMin2TC-R.subset.otf`。

OFL：`art/fonts/OFL_GenWanMin2.txt` 在源碼，匯入之後仍然冇 `.import`，冇人 `load`。`export_presets.cfg:8-10` 係 `all_resources`、`include_filter` 空。未匯入的 txt 唔會入 PCK。匯出路徑 `../apk/微光小圃-godot-g0.1.apk` 呢部機冇檔可開。按設定，APK 唔會帶這份 OFL。下面 P3。

## 已知、未做

唔開等級。

- 浮動窗同遊戲狀態未同步。Godot 腳本冇 `overlay_status`。Kotlin `PetPrefs.kt:8` 仍然寫 snapshot 由 JS 寫、queue 由 overlay 寫。
- 需要泡泡太淡。`NeedBubble.gd:16` `pixel_size` 0.35。`m1a-bubbles.png` 頭頂只有一小塊。
- 訪客行路未做。`FamilyDirector.force` 單元測試過，截圖未見到行路循環。

## P0

冇。

## P1

冇。

## P2 — 桌面橫向仍然玩到

`project.godot:38` 只係手提直向。852×393 照畫，冇直向鎖，鏡頭 dist 夾到 80，寵物高 54%。`QA/shots-m1a/land-852x393-day.png`。

修法：橫向視窗顯示直向鎖，或者桌面都鎖直向。

負責：遊程。

## P3 — 390 總覽 texel 未到 ×2／×3

跟拍 texel 2.04，768 總覽 1.96。390 總覽 1.17。`Main.gd:1146-1148` 怕整數倍切走花園就唔跟。

修法：窄屏都鎖 ×2，或者寫明 390 總覽允許 ×1。

負責：遊程。

## P3 — 訪客站立條仍然係細佬 A1

clip 查詢用訪客 M 圖集。`Main.gd:359` 的 `setup` 仍然載 `res://art/kid/A1_idle.png`。靜止畫面同細佬條一樣。

修法：訪客站立用蝸牛（或而家的 form）M 圖集，唔好借用細佬條。

負責：遊程。

## P3 — OFL 未打入匯出

`art/fonts/OFL_GenWanMin2.txt` 冇 `.import`。`export_presets.cfg:8-10` 唔會打包未匯入的 txt。

修法：把 OFL 收成匯入資源，或者 `include_filter` 指住呢份檔，出 APK 之後再核對有這份許可。

負責：遊程。

## P3 — 冇雨

`Main` 仍然冇 `set_rain`。

修法：加雨狀態再補截圖。

負責：遊程。

## P3 — 離開月眠窗未清睡眠

`Sim.gd:364-366` 離開 20:00–03:00 的分支仍然係 `pass`。註解寫「出月眠窗自動醒」。

修法：自動瞓的，一出窗就清 `sleeping`。

負責：遊程。

## 遊美

今次冇新開給遊美的缺陷。字體維持源雲明體。art-fix1 的 M 圖集查詢測到。
