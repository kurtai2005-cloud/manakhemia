# QA：Godot M1b（`2c676c6e`）

唯讀 `code/glimmer-godot` @ `2c676c6e2d64eb0920572c05127b21a1dde3143a`，tree `574dc5df90dc017fd2d3ec858e19d917621e2167`。由 `8da4d168` 快進。Godot `4.7.2`。畫面用 xvfb＋opengl3。冇改 code branch，冇 merge。M1a 的檢查併在這份，冇另寫 M1a 報告。

截圖：`QA/shots-m1b/`（四個直向 × 日／黃昏／夜，另加跟拍、總結卡、草原、圖鑑、橫向）。

## 測試

`tests/test_runner.gd`：**326 passed，0 failed**，對住預期 326（M1a 的 275 次斷言，加這次 51 個新 `ok()`）。再跑一次仍然 326／0。36 個測試函式全部有呼叫（32 舊 + 4 新：人手照顧、需求警告、狩獵／派工／收藏、overlay）。51 個新斷言每個都跑到一次，包括 `if pet` 裡面的餵同摸。冇 skip，冇漏跑。離線補時（保底 20、成長封頂 24h、光粒只係離線禮物、時鐘回撥、唔雙重補、有變先寫）在同一套，冇失敗。

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

## Audio wiring

對住 `2c676c6e` 的碼同一次 headless 探測。GUT 在 `test/qa/test_audio_wiring.gd` 的 `test_m1b_*`：8 項裡 2 過（開局解鎖、需求警告），其餘失敗，同下面的 FAIL 一致。

1. **FAIL，P2。** `Walker.gd:247-249`：`_fire_sfx` 先 `sfx_cue.emit`，再自己 `AudioManager.play`。`AudioManager.gd:54-55` 已經把 `sfx_cue` 接到 `_on_sfx_cue`，那裡再 `play` 一次（`:213-217`）。抓癢 cue（frame 2）聲池 +2，兩次都出聲。噴嚏只聽到一次，因為有聲線的 4 秒閘把第二次收成靜音，唔係只播一次。腳步 `Walker.gd:318-321` 同一個寫法，聲池 +2。修法：`_fire_sfx` 同 `_maybe_footstep` 只 emit，唔好再直接 `play`。負責：遊音。

2. **FAIL，P2。** 掣的字串寫死 `sfx_ui8_btn_press_a`（圖鑑開鍵 `Hud.gd:67`，一鍵列 `Hud.gd:504`，另外十處）。`play()` 會剝 `_a` 再交 `AudioStreamRandomizer`，模式係 `PLAYBACK_RANDOM_NO_REPEATS`（`AudioManager.gd:346-348`），所以聽到的唔係釘死 `_a`。`last_play.stream` 仍然永遠記 `_a`，睇唔到抽中邊條。圖鑑「關閉」`Hud.gd:336-341` 冇聲。商店每一行 `Hud.gd:390-405` 冇聲。「一鍵擺家具」`Hud.gd:343-345` 有聲。修法：商店列同關閉掣播共用的 `sfx_ui8_btn_press`，唔好寫死 `_a`。負責：遊音。

3. **FAIL，P2。** `Hud.gd:502-504` 一鍵列一按就播 `sfx_ui8_btn_press_a`，之後先做狩獵／派工。失敗回 `{ok:false}` 時 `_on_care`（`:563-566`）直接返回，冇 `sfx_ui8_error`。探測：冇 Main 時 hunt 同 dispatch 都只剩 `sfx_ui8_btn_press_a`。修法：失敗改播 `sfx_ui8_error`，唔好播按下聲。負責：遊音。

4. **FAIL，P2。** `AudioManager.gd:243-247`：`stop_loop` 的 `fade` 冇用，播放中就 `stop()`。睡眠呼吸 loop 停之前音量 −3，停完即刻唔再播，音量仍係 −3。`sync_bgm`（`:250-275`）只識照顧時段，小節長只用 `BAR_SEC` 3.5294。冇 `PHASE_HUNT`，工程裡亦冇 `bgm_hunt_loop.ogg`。修法：`stop_loop` 按 `fade` 把音量收完先停；狩獵相位改播 2.222 秒一節的狩獵 loop，唔好用 68 BPM 的 `BAR_SEC`。負責：遊音。

5. **FAIL，P2。** `WorkSystem` 有 `dispatched`／`work_ready`／`collected`，`HuntSystem` 有 `hunt_started`／`hunt_phase`／`hunt_collected`，`CollectionSystem` 有 `unlocked`。`AudioManager` 一個都冇接。開 Main 之後，`Main.gd:1286-1289` 只把 `hunt_phase` 同 `dispatched` 接到自己的行路，唔係音效。探測時空載入，這七個信號的連接數都是 0。修法：在 `AudioManager._ready` 把這三個系統的信號接到對應的 `play`。負責：遊音。

6. **PASS。** `Main.gd:1277-1278` 開局 `unlock_form`／`unlock_kid`。`CollectionSystem.gd:127-146` 只改存檔並 `unlocked.emit`，冇人播 `sfx_codex_new_entry`。這個檔在 M1b 根本不存在。探測聲池增量 0。唔使改。

7. **FAIL，P2（打唔中那半駁回）。** `HuntField.gd` 冇 `AudioManager`，亦冇 `sfx_mg_miss`（打唔中唔會播出失敗聲，這半符合 §6）。捉到 `_pounce_critter`（`:249-268`）只換成果圖，冇 `sfx_mg_catch`。修法：捉到播 `sfx_mg_catch`，繼續不要播 `sfx_mg_miss`。負責：遊音。

8. **PASS。** `AudioManager.gd:362-391`。欣賞模式 `reason=appreciate`、唔播。同一瞬間第二隻係 `same_moment`。同一隻 8 秒內係 `pet_cooldown`（`NEED_WARN_PET_COOLDOWN` 8.0，`:32`）。套件 `_test_m1b_need_warning` 這三條已過。a／b 走同一個 no-repeat randomizer。欣賞開關在 `Hud.gd:458-460`。唔使改。

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
