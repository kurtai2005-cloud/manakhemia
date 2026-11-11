# QA：Godot M1d（`12a36f71`）

唯讀 `code/glimmer-godot` @ `12a36f7171eca25676beee913ffab9bf185b0f0f`，tree `a7cce9e1602b4e89713e9fc2afb5d238ce62e115`。由 `2fb68ffa` 快進。腳圖對 `art/m1d-feet` @ `de7b1103`（tree `6cdee185`）。音圖對 `audio/pet-plan-a` 最新 `2056d048`（tree `6d1f7b2a`，同 M1c.3）。Godot `4.7.2`。畫面用 xvfb＋opengl3。冇改 code branch，冇 merge。

截圖：`QA/shots-m1d/`（390×844、360×800，日同 21:00；室內日／夜；另加跟拍同橫向提示）。

## 過咗

- 撳屋入室內、即時離開都唔會黑屏卡住。`enter_house(true)` 之後 fade alpha 係 0，`in_interior=true`；`exit_house(true)` 之後返花園，小屋再可見，寵物 y=0。左上有「返回」，`Hud.gd:89-93` 叫 `exit_house`。
- 入出時序的數字對得上 `data/m1d.json:211-223`：開門 0–400、dolly 450、fade 由 310 起到 710 先 cut 同 `enter_interior`，再 fade in，共 1110。出屋 `exit_interior` 在 0、fade 0–400、400 cut 同 `door_close`，關到 800。`Main.gd:2079-2169`。
- 室內 AMB：入屋 −12 dB 加 900 Hz 低通，出屋還原。`AudioManager.gd:734-772`。
- 小屋 scale `(2, 2, 2)`。門在未放大前 28×48，乘 2 係 56×96（`Main.gd:2260`、`data/m1d.json:137-138`）。390 全景見到成個屋頂。
- 郵局在 `(-150, 0, 40)`，離門 275，冇擋門。
- 商店 8 件、總價 190 仍在 `data/economy.json:204-207`。傢俬 zone 是室內（套件過）。
- 跟拍寵物高 21.9%。全景 6.16%（已知，唔當 bug）。
- 圖鑑掣已到左上 `(16, 64)`，冇蓋住 ★ 25 那行。
- 四個 activity 都係 portrait：`GodotApp`、`SettingsActivity`、`PowerGuideActivity`、`ProcessPhoenix`（`AndroidManifest.xml:22-43`）。852×393 出「請轉為直向」，HUD 隱藏。套件有 `_test_m1d_rotate_overlay`、`_test_m1d_process_phoenix`。
- 低檔 92 個 mesh、scale 0.67，花園仍然 3D。
- 套件冇 `/workspace/glimmer-godot`。
- 迴歸：撲空 1 萬次 seed `20261111` 仍係 2513／2026／2989，第 3 下 0 miss。9 個 loop import 都係 `loop=true`。map 同 `2056d048` 逐 byte 一樣。新局 25 碎。離線補時在套件裡，冇失敗。`PetOverlayService.kt` 在。

## 測試

指定 695。`tests/test_runner.gd` headless：**688 passed，8 failed**，一共 696 個斷言。冇 skip。失敗就是下面的腳點同室內牆。

## P0

冇。

## P1 — 室內牆同地台冇起出嚟

`art/garden3d/H1/interior/` 唔在這棵樹。`InteriorRoom.gd:132-155` 讀唔到 mesh 就跳過，所以冇 `floor`／`wall_back`／`wall_L`／`wall_R`，厚度量度係 `(0,0,0)`。畫面係深色空房加一張 3D 床盒，寵物企在床外。低檔改唔到「冇 mesh」。`QA/shots-m1d/interior-day-390x844.png`。

修法：把遊美 interior1 的 mesh 放進 `art/garden3d/H1/interior/`，`solidify_mesh` 先有 3wu 厚牆。

負責：遊美。

## P2 — 室內寵物高未到 20%

390×844 室內可見高 16.8%，360×800 係 14.1%。`Main.gd:2172` 入屋之後用全景鏡頭，冇拉到 20%。

修法：室內鏡頭跟 `follow_pet_min_frac` 收到 ≥20%。

負責：遊程。

## P2 — 八件傢俬冇人去用

商店八件（雲朵床、樹樁檯、圓檯、層架、鞋架、圓地氈、葉地氈、窗簾）同預設葉床都冇「行過去播 clip」的碼。入屋只 `go_to` 一個隨機點（`Main.gd:2188`）。

| 槽 | 預期 clip | 而家 |
|---|---|---|
| 床 | `sleep_loop`／`fall_asleep` | 冇 |
| 檯 | `eat` | 冇 |
| 地氈 | 碌（現有 clip 未接） | 冇 |
| 鞋架 | 出門前停 | 冇 |
| 窗簾 | 望窗 | 冇 |
| 層架／相框 | 未寫 | 冇 |

修法：按槽把寵物行到傢俬再播上表的 clip。

負責：遊程。

## P2 — 21:00 唔會自己入屋

`hour_band` 的 night 由 22:00 起（`Main.gd:829`）。模擬 21:00，`tod=evening`，`in_interior=false`，寵物仍在花園 `(-60.5, 0, 5.8)`。唯一入屋路徑係撳屋（`Main.gd:688-691`）。

修法：21:00 之後叫寵物行去 `cottage_door_world()`，入到門口再 `enter_house`，室內播 `sleep_loop` 並對準床。

負責：遊程。

## P2 — 花園仲有側樹同灌木

點名要留的花盆、燈、籬、大樹、菜畦、蘑菇、花灑、螢火瓶、串燈都在。另外仲可見 `bush_bL`、`bush_bL2`、`bush_bR`、`trees_bL`、`trees_bR`。

修法：日間花園隱藏這五個側景，或者移出畫面。

負責：遊程。

## P2 — 圖鑑掣高 44，未到 48

`Hud.gd:62-65` 圖鑑是 120×44，`_btn` 的最小尺寸是 100×40（`Hud.gd:260`）。返回掣同一高度。

修法：這兩粒掣的高改到至少 48。

負責：遊程。

## P2 — 入屋五個音效檔唔在

`sfx_door_open`、`sfx_door_close`、`sfx_enter_interior`、`sfx_exit_interior`、`sfx_interior_footstep` 都冇 ogg。hook 有接，播出來係靜音。腳步靜音本身唔當 bug，但檔案仍然要在。`2056d048` 都冇這五個檔。

修法：把五個 ogg 放進 `audio/sfx/`。

負責：遊音。

## P2 — 腳圖 commit 未進這棵樹

`de7b1103` 的 `actor_anim.json`、`atlas_radiant_live.png`、`CLIPS.json` 同 `12a36f71` 唔同 blob。套件要的腳點係訪客 `(24, 40)`、蝸牛 `(22, 40)`、螢火 `(24, 36)`（`tests/test_runner.gd:569`、`:695`、`:697`）。樹裡係 `(24, 45)`、`(22, 45)`、`(24, 44)`（`data/actor_anim.json:33-72`）。世界座標 y 仍是 0，細佬冇播到團絨的 `walk_happy`（物種測試冇失敗）。

修法：把 `de7b1103` 的腳點同圖集放進這棵樹。

負責：遊美。

## 方法

今次入屋之後用鏡頭量可見寵物高，再對磁碟查 `art/garden3d/H1/interior/` 在唔在，避免把「厚度測試失敗」誤當成只是 AABB 算錯；腳點則用 art commit 的 blob 對這棵樹，而唔係只睇測試期望值。
