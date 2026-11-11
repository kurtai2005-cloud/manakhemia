# QA：Godot M1c.3（`2fb68ffa`）

唯讀 `code/glimmer-godot` @ `2fb68ffa3f9b094f3e051407502479428c2e6999`，tree `9989f9f89e660afe1cedb58b0728d07032162940`。由 `d2ddd47f` 快進。音圖對 PR #16 `audio/pet-plan-a` @ `2056d048`（tree `6d1f7b2a`）。Godot `4.7.2`。畫面用 xvfb＋opengl3。冇改 code branch，冇 merge。

截圖：`QA/shots-m1c3/`。

## 過咗

1. 狩獵場四個直向都睇唔到 `Kid`、`Visitor`、`Poop_0`、`Ground256`、`GroundAO`（`visible=false`）。地板節點係 `PrairieGround`，可見，58 個 mesh，仍然 3D。`Main.gd:1706-1714` 收角色、便便同兩塊花園地面；`HuntField.gd:117` 自己叫 `PrairieGround`。離開之後呢啲節點同屋、樹、燈、花盆都 `visible=true`。`QA/shots-m1c3/hunt-*.png`、`garden-back-393x852.png`。鏡頭仍然掃到外圍草地 `/root/Main/GroundTile`（唔係今次點名的兩塊地面）。

2. 三個 activity 都係 portrait。呢部機冇 aapt、冇現成 APK，用 `native/android/src/main/AndroidManifest.xml`：`GodotApp` `:22`、`SettingsActivity` `:27`、`PowerGuideActivity` `:33` 都係 `android:screenOrientation="portrait"`。`tools/inject_android_overlay.py:104` 出包時再鎖 GodotApp。`PetOverlayService` 係 service，唔係 activity。

3. 9 個 `bgm_*` 同 `*_loop` 的 `.import` 都係 `loop=true`，包括 `audio/sfx/sfx_kitchen_stir_loop.ogg.import:15`。

4. `tests/test_runner.gd` 冇 `/workspace/glimmer-godot`。插件改為 `ProjectSettings.globalize_path`（`:1109-1111`）。headless 再跑：**585 passed，0 failed**。指定 584；套件實際跑出 585 個斷言，冇 skip、冇失敗。

5. 工程裡的 `audio/m1b_sfx_map.json` 同 `2056d048` 逐 byte 一樣。`collection.unlocked` 的 `sfx_codex_new_entry` 在 events（`:248`）同 entries（`:701`）都係 UI，`bus_for` 回 UI。map 每個 id 都有檔、bus 都啱（0 行唔符）。`AudioManager` 引用 13 個 id，全部有 ogg。

抽查（M1c.2 已過，再跑）：撲空 1 萬次 seed `20261111`，隨和 25.13%（CI 24.28–25.98）、勤力 20.26%（19.47–21.05）、懶散 29.89%（28.99–30.79），第 3 下 0 miss。撲先 `sfx_hunt_pounce`，打唔中 `sfx_critter_startle` 然後 `sfx_critter_shake`（`HuntField.gd:524-538`），捉到 `sfx_mg_catch`，`sfx_mg_miss` 只出現在「不要播」。鞋架 `Sprite3D` y=16。新局 25 碎。低檔 tier 0、90 mesh、1 個相機、scale 0.67。離線補時在 585 項裡面，冇失敗。`PetOverlayService.kt` 在，manifest `:39` 有登記。

## P0

冇。

## P1

冇。

## P2 — 桌面 852×393 仍然係橫向版面

三個 Android activity 已鎖直向。Godot 視窗打橫仍然照畫橫向：`project.godot:42` 只係手提提示，`Main.gd:760` 的 `set_shot_size` 接受任何闊高。實測視窗 `(852, 393)`，欣賞同開發者分左右。`QA/shots-m1c3/land-852x393.png`。

修法：闊大於高時顯示直向鎖，唔好把 HUD 鋪成橫向。

負責：遊程。

## 方法

今次先對 PR #16 的 map 做逐 byte 比較，再在跑緊的遊戲裡讀 `bus_for` 同檔案，而唔係只睇 `bus_for` 的分支；狩獵場則在進入同離開各印一次可見性，對住點名的五個節點。
