# QA：Godot M1c.2（`d2ddd47f`）

唯讀 `code/glimmer-godot` @ `d2ddd47f95da678bef78a28b783bfdc0cbc39a51`，tree `0569b3ade7e1d505990b9f4a7f221f093a8d0580`。由 `76a2de2c` 快進（`76a2de2c` 由 `6a315ec7` 快進）。Godot `4.7.2`。畫面用 xvfb＋opengl3。冇改 code branch，冇 merge。

截圖：`QA/shots-m1c2/`。回歸：`test/qa/test_audio_wiring.gd`（GUT 9.5.0，5／7 過，見下面兩項未收）。

## 帶過

`6a315ec7`（tree `caa5466a`）：407／409。兩條失敗係測試路徑寫死 `/workspace/glimmer-godot`，檔案其實在 `native/android/...`。草原已係 3D、寵物直立。撲擊 1 萬次（seed `20261111`）同下面再跑的數字一樣。新局 25 碎。泡泡五張同 bubble-fix1 `a4e4c9aa` 逐 byte 一樣。桌面橫向照玩。

`76a2de2c`（tree `018f4678`）四項音效當時未過：腳步 `play` 加 `sfx_cue` 播兩次；進出狩獵用錯小節長；`sfx_codex_*` 落 SFX；`bgm_hunt_loop.ogg.import` 係 `loop=false`。花盆、燈柱、床、屋、工作點仍入狩獵畫面。今次 M1c.2 收這四項同點名的道具。下面只記而家的結果。

## 536／538

`tests/test_runner.gd`：**536 passed，2 failed**，退出碼 1。失敗仍然只係 `tests/test_runner.gd:1104-1106` 的 `/workspace/glimmer-godot/...`。`RealWorldPlugin.kt`、`Share6dPlugin.kt` 在 `native/android/src/main/java/hk/vizard/glimmer/fpet/`。離線補時在同一套，冇失敗。

## 四項音效（而家過）

GUT `test_footstep_emits_once`、`test_different_tempo_starts_at_zero`、`test_codex_hooks_use_ui_bus`，同套件 `_test_m1c2_audio_fixes`，都過。

1. 腳步只 emit。`Walker.gd:334-336` 唔再叫 `AudioManager.play`。落地一幀 `sfx_pet_step_hop` 入 log 一次。
2. 拍速不同唔對位，新曲由 0 起。`AudioManager.gd:316-319` 改旗標之前先捉 outgoing bar；`AudioManager.gd:357-359` 兩條 bar 唔相等就 `start_sec = 0`。實測進入：outgoing bar `3.5294`（照顧 68 BPM 4／4），`last_bgm_start_sec = 0`，播放頭 `0.003`。離開：outgoing bar `2.222`，一樣由 0 起。
3. `sfx_codex_page_flip`、`_a`、`_b`、`sfx_codex_new_entry` 的 `bus_for` 都係 UI。`AudioManager.gd:184-185`。`sfx_furn_buy` 仍然 SFX。
4. `audio/bgm/bgm_hunt_loop.ogg.import:15` 係 `loop=true`。載入後的 Ogg 亦 `loop`。

聲池 6。同時播撲（0.430s）、變身（0.390s）、滾（0.260s），再按捕捉時間 0／100／120 ms 疊上，第一條聲冇被後面的 `stop` 掉。`sfx_mg_catch` 長 0.200s。只記錄，唔當失敗。

## 圖同檔

`wall_shoes.png` blob `208a393b` 同 `art/furn-fix1` @ `68d25799`（tree `d2f63d64`）一樣，50×36。`sfx_kitchen_stir_loop.ogg` blob `b48c489c` 同 `audio/pet-plan-a` @ `55616629`（tree `b3e5703f`）一樣。舊檔 `sfx_kitchen_stir.ogg` 冇咗。`AudioManager.gd:645`、`:652` 用 `sfx_kitchen_stir_loop`。GUT 掃到 AudioManager 引用 18 個 id，全部有 ogg。map 每個 id 都有檔。

`m1b_sfx_map.json` 有兩行 `collection.unlocked` 的 `sfx_codex_new_entry` 仍然寫 bus `SFX`（events 約 `:248`，entries 約 `:701`），`bus_for` 回 UI。其餘行的 bus 同碼一致。GUT `test_map_bus_and_files` 因此失敗。見 P3。

`sfx_kitchen_stir_loop.ogg.import:15` 仍然 `loop=false`。其餘 `bgm_*` 同 `*_loop` import 都係 `loop=true`。`start_loop` 會強制 loop，所以播得出仍然循環；import 本身未改。見 P3。

## 草原

`HuntField` 58 個 mesh，原點 `(0, 0, 520)`。寵物同小怪 billboard 都係 `BILLBOARD_FIXED_Y`。四個直向都入狩獵。

已收埋（`visible=false`，唔在畫面）：`/root/Main/cottage`、`tree`、`lanterns`、`lamp`、`pot_L`、`pot_R`、`pot_S`。`data/m1c.json:52-70` 的 hide 清單亦包括床、欄、菇、罐、側樹。`Main.gd:1698-1705` 再收 `Furniture`、`Warehouse`、工作點。這幾類冇再投影入四個直向。

四個直向仍然投影入狩獵鏡頭、又唔屬於 `HuntField` 的節點：

| 路徑 | 類 |
|---|---|
| `/root/Main/Kid/@Sprite3D` | 細佬 |
| `/root/Main/Kid/BlobShadow` | 影 |
| `/root/Main/Visitor/@Sprite3D` | 訪客 |
| `/root/Main/Visitor/BlobShadow` | 影 |
| `/root/Main/Poops/Poop_0/@Sprite3D` | 一粒便 |
| `/root/Main/Ground256` | 花園中心地面 |
| `/root/Main/GroundAO` | 地面 AO |
| `/root/Main/GroundTile` | 外圍草地（伸到草原下面） |
| `/root/Main/bg_sky` | 天空卡 |

`/root/Main/Pet` 係帶去草原的寵物，唔算漏。圖：`QA/shots-m1c2/hunt-360x640.png`、`hunt-393x852.png`、`hunt-412x915.png`、`hunt-768x1024.png`。見 P2。

## 撲擊（再跑 1 萬，seed 20261111）

同 `6a315ec7`。第三次在已 miss 兩次之後。

| 性格 | 規格 | 第 1 次 | 95% CI | 第 2 次 | 第 3 次 |
|---|---:|---:|---|---:|---:|
| 隨和 | 25% | 25.13%（2513／10000） | 24.28–25.98% | 24.99%（628／2513） | 0／628 |
| 勤力 | 20% | 20.26%（2026／10000） | 19.47–21.05% | 20.98%（425／2026） | 0／425 |
| 懶散 | 30% | 29.89%（2989／10000） | 28.99–30.79% | 30.01%（897／2989） | 0／897 |

`depart` seed 11：碎 2（json 1–3）、果 4（2–4）。再 miss 兩次，數量不變。

## 泡泡、碎、低檔、直向

泡泡四個直向都 `visible`，貼圖 64×56，`pixel_size` 0.62。這次 diff 冇改泡泡 png。新局碎 25。低檔 tier 0、1 個相機、`render_scale` 0.67、`max_fps` 30、場景 90 mesh，仍然 3D。

`project.godot:42` 只係手提直向。852×393 照畫。`QA/shots-m1c2/land-852x393.png`。見 P2。

## 牆鞋

`Furn_wall_shoes` 係 `Sprite3D`，貼 `wall_shoes.png`，本地同世界 `y = 16`（牆槽 `Main.gd:1379` `Vector3(86, 16, -44)`）。唔係色塊，唔係貼地。冇圖的 id `no_such_furn_xyz` 仍然退回色塊，並保住槽的 y。`QA/shots-m1c2/furn-393x852.png` 對住屋牆。葉床、樹樁檯係 `Sprite3D`，葉地氈係有貼圖的平面。

## 6b／6d

桌面 `DeviceLink`：RealWorld `{ok:false, error:desktop}`，剪貼簿寫入「qa」再讀返，分享同計步回 desktop。`tools/inject_android_overlay.py` 出包時寫入 RealWorld 同 Share6d。呢部機冇 Android 模擬器，服務未在裝置上啟動。桌面路徑冇崩潰。

已知靜音，唔開等級：`furn_pickup`、冇攪拌動作所以唔起 stir loop、圖鑑翻頁、結算卡的幣／印／數字滾、入場帷幕。

## P0

冇。

## P1

冇。

## P2 — 狩獵畫面仍有花園角色同中心地面

點名的屋、大樹、燈、花盆、床、工作點已收。四個直向仍然見到細佬、訪客、一粒便，以及花園中心地面 `Ground256`／`GroundAO`。路徑見上表。`Main.gd:1691-1705` 的隱藏清單未包括佢哋。

修法：進入 `PHASE_HUNT` 時一併隱藏 `Kid`、`Visitor`、`Poops`，同花園中心地面 `Ground256`、`GroundAO`。

負責：遊程。

## P2 — 桌面橫向仍然玩到

`project.godot:42` 只係手提直向。852×393 照畫，冇直向鎖。

修法：橫向視窗顯示直向鎖。

負責：遊程。

## P3 — 圖鑑新格的 map 仍寫 SFX

`audio/m1b_sfx_map.json` 的 `events` 同 `entries` 裡，`collection.unlocked`／`sfx_codex_new_entry` 的 bus 係 `SFX`。`AudioManager.gd:184` 已將所有 `sfx_codex_*` 送到 UI。`hunt.collect` 那行已經係 UI，同碼一致。GUT `test/qa/test_audio_wiring.gd` 的 `test_map_bus_and_files` 失敗。

修法：把這兩行 bus 改成 `UI`。

負責：遊音。

## P3 — 攪拌 loop 的 import 未循環

`audio/sfx/sfx_kitchen_stir_loop.ogg.import:15` 係 `loop=false`。其他 `bgm_*` 同 `*_loop` 都係 `loop=true`。`AudioManager.start_loop` 會在播放時強制 loop，所以而家聽落仍會循環；import 未跟。GUT `test_bgm_and_loop_imports_loop` 失敗。

修法：把該 import 的 `loop` 改成 `true`。

負責：遊音。

## P3 — 套件兩條路徑仍然寫死

`tests/test_runner.gd:1104-1106`。其餘 536 項過。

修法：檢查專案裡的 `native/android` 路徑，唔好寫死 `/workspace`。

負責：遊程。
