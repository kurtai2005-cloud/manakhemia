# QA：Godot M1b（`2c676c6e`）

唯讀 `code/glimmer-godot` @ `2c676c6e2d64eb0920572c05127b21a1dde3143a`，tree `574dc5df90dc017fd2d3ec858e19d917621e2167`。由 `8da4d168` 快進。Godot `4.7.2`。畫面用 xvfb＋opengl3。冇改 code branch，冇 merge。M1a 的檢查併在這份，冇另寫 M1a 報告。

截圖：`QA/shots-m1b/`（四個直向 × 日／黃昏／夜，另加跟拍、總結卡、草原、圖鑑、橫向）。

## 測試

`tests/test_runner.gd`：**326 passed，0 failed**。離線補時（保底 20、成長封頂 24h、光粒只係離線禮物、時鐘回撥、唔雙重補、有變先寫）在同一套，冇失敗。

低檔仍然 3D：tier 0、1 個 `Camera3D`、`render_scale` 0.67、40 個 mesh。

## 直向

手提方向仍然係提示。852×393 照畫，冇直向鎖。`QA/shots-m1b/land-852x393.png`。下面 P2。

## 寵物高度（可見像素，唔係廣告牌框）

`Walker._scan_visible` 掃貼圖裡不透明的行（`Walker.gd:560-596`）。`Main._measure_cam_metrics` 把該段投影成屏幕高（`Main.gd:1208-1216`）。`pet_h_quad` 係成個框，`pet_h_visible` 係可見像素。日間：

| 畫面 | 總覽可見 | 總覽整框 | 跟拍可見 | 跟拍整框 |
|---|---:|---:|---:|---:|
| 360×640 | 10.0% | 11.7% | 22.0% | 25.7% |
| 393×852 | 10.1% | 12.6% | 20.9% | 28.4% |
| 412×915 | 10.1% | 11.8% | 22.4% | 27.2% |
| 768×1024 | 12.6% | 14.8% | 23.8% | 32.6% |

總覽都 ≥10%。跟拍都 ≥20%。

## 總結卡

卡底邊抬到離底 250（`Hud.gd:135-144`）。四個直向同「欣賞」「開發者」相交都係 0×0。`QA/shots-m1b/card-393x852.png` 卡在按鈕上方。

## 人手照顧

餵同摸要先有寵物。`hand_feed(null)`／`hand_pat(null)` 回 `pick_pet`（`Main.gd:1390-1410`）。底欄一鍵剩執屎、收成、出發、派工（`Hud.gd:98-101`）。選中團絨之後，行為樹播 `eat`（餵）或摸的動作（`PetBrain.gd:181-186`）。`sfx_feed_meal`／`sfx_feed_snack` 在 `hand_feed` 入口播（`Main.gd:1399-1401`）。326 項在飢 40 時兩種餵食聲都過。

## 需要泡泡同警告聲

泡泡在日、黃昏、夜、四個直向都 `visible`。欣賞模式：`play_need_warning` 回 `appreciate`，`_pick` 仍然係 `need_eat`，泡泡照出。同一瞬間第二隻回 `same_moment`。同一隻 8 秒內回 `pet_cooldown`，調到 9 秒後可以再播。冷卻係 8.0 同 0.25（`AudioManager.gd:32-33`、`:362-392`）。a／b 用 `AudioStreamRandomizer` 的 `PLAYBACK_RANDOM_NO_REPEATS`（`AudioManager.gd:345-358`）。`last_play.stream` 只記 `_a` 路徑，睇唔到隨機器抽咗邊條。

泡泡框仍然係圓底加 icon，未用 bubble-fix1 的金框。已知，下面。

## 狩獵、郵局、廚房、圖鑑

草原係一塊冇貼圖的 `PlaneMesh`（420×320，`HuntField.gd:61-68`），草叢係色塊。已知留到 M1c。`QA/shots-m1b/hunt-390.png`。

`post` 同 `kitchen` 兩個工地都在。出發、收成、Lv1 工資 2 碎、同日不可再狩獵，326 項過。

圖鑑面板開到（`QA/shots-m1b/codex-393x852.png`）。預設已有 `bed_leaf`，可擺、可買 `rug_leaf`。紅點可設可清。

## 已知、唔開等級

- 草原係臨時平地，M1c 先換真場景。負責：遊程。
- 需要泡泡框等 `art/bubble-fix1`。負責：遊美。
- 浮動窗同遊戲狀態的完整同步，同 6b RealWorld、6d Share，呢份未有。M1b 只把 snapshot 寫去 `user://overlay_snapshot.json`（測試過）。負責：遊程。
- 冇落雨。`Main` 冇 `set_rain`。四個直向只有日、黃昏、夜。負責：遊程。

## P0

冇。

## P1

冇。

## P2 — 桌面橫向仍然玩到

手提方向只係提示。852×393 照畫，冇直向鎖。

修法：橫向視窗顯示直向鎖。

負責：遊程。

## 遊音

需要警告聲的冷卻、欣賞靜音、同一瞬間只播一次，都按規則過。a／b 交俾隨機器唔重複。餵食聲在入口播。
