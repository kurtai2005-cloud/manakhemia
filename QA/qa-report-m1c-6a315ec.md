# QA：Godot M1c（`6a315ec7`）

唯讀 `code/glimmer-godot` @ `6a315ec767e044e60873be647b0689407513dbfe`，tree `caa5466a0d94e4cadd6979f483448d4d0df1ba4a`。由 `2c676c6e` 快進。泡泡圖對 `art/bubble-fix1` @ `a4e4c9aa`（tree `09ed8275`）。Godot `4.7.2`。畫面用 xvfb＋opengl3。冇改 code branch，冇 merge。

截圖：`QA/shots-m1c/`。音效接線留待 M1c.1，呢輪冇跑、冇開 bug。

## 由 M1b 帶過

今次冇另寫一份 M1b 報告。音效接線（包括一鍵餵的 `sfx_feed_meal`／`sfx_feed_snack`）確認未修，M1c.1 先驗。

## 409 項

`tests/test_runner.gd`：**407 passed，2 failed**，退出碼 1。失敗只係兩條檔案路徑，見 P3。離線補時（保底、24h 封頂、光粒、回撥、唔雙重補、有變先寫）喺同一套入面，冇失敗。

## 低檔仍然 3D、直向

低檔 tier 0、1 個 `Camera3D`、`render_scale` 0.67、場景內 89 個 mesh（花園加草原）。唔係平面後備。

`project.godot:42` 只係手提直向。852×393 照畫，冇直向鎖。`QA/shots-m1c/land-852x393.png`。下面 P2。

## 草原

`HuntField` 起 57 個 `MeshInstance3D`（地、網格、遠景），原點 `(0, 0, 520)`。寵物同小怪 billboard 都係 `BILLBOARD_FIXED_Y`（直立，`HuntField.gd:189`）。`QA/shots-m1c/hunt-390x844.png` 係有地平的 3D 草地，角色企住，唔係一張平圖。

## 撲擊 miss（1 萬次，seed 20261111）

`HuntSystem.roll_is_miss`。第一次撲的 95% 區間。第二次係「第一次已 miss」之後。第三次在已 miss 兩次之後。

| 性格 | 規格 | 第 1 次 | 95% CI | 第 2 次 | 第 3 次 |
|---|---:|---:|---|---:|---:|
| 隨和 | 25% | 25.13%（2513／10000） | 24.28–25.98% | 24.99%（628／2513） | 0／628 |
| 勤力 | 20% | 20.26%（2026／10000） | 19.47–21.05% | 20.98%（425／2026） | 0／425 |
| 懶散 | 30% | 29.89%（2989／10000） | 28.99–30.79% | 30.01%（897／2989） | 0／897 |

三次都落在區間內。滿 2 次 miss 之後必中。`depart` seed 11：碎 2（`hunting.json` 1–3）、果 4（至少 2）。再強制 miss 兩次，碎同果數量不變。

## 需要泡泡

五張 `bubble_need*.png` 同 bubble-fix1 逐 byte 一樣（64×56）。`NeedBubble` 用 `bubble_%s.png`，`pixel_size` 0.62，唔再係米色圓底。四個直向都 `visible`，日間金框＋深藍底，入面食物 icon 睇得出。

| 畫面 | 框大約 |
|---|---|
| 360×640 | 63×37 px（高 5.8%） |
| 393×852 | 59×39 px（高 4.6%） |
| 412×915 | 61×42 px（高 4.6%） |
| 768×1024 | 同樣 64×56 貼圖，看得見 |

圖：`QA/shots-m1c/bubble-*.png`。

## 家具同開場碎

新存檔 `CollectionSystem.stardust()`＝25。畫面左上 ★ 25。

擺出葉床、葉地氈、樹樁檯都係貼圖（`Sprite3D`／有紋理的平面）。`wall_shoes` 仍然係色塊（`MeshInstance3D`，`Main.gd:1602-1617` 冇圖就退回色塊）。已知，唔開等級。`QA/shots-m1c/furn-393x852.png`。

## 6b／6d

`RealWorldPlugin.kt`、`Share6dPlugin.kt` 在。`DeviceLink` 桌面：RealWorld 回 `{ok:false, error:desktop}`，計步／位置回 `desktop`，分享回 desktop。剪貼簿 copy／paste 用 `DisplayServer`，測到寫入「qa」再讀返。`tools/inject_android_overlay.py:165-166` 出包時先把兩個插件寫入 manifest。倉庫裡的 `AndroidManifest.xml` 只登記 `GlimmerOverlay`。呢部機冇 Android 模擬器，插件冇在裝置上啟動。桌面路徑冇崩潰。

## P0

冇。

## P1

冇。

## P2 — 桌面橫向仍然玩到

`project.godot:42` 只係手提直向提示。852×393 照畫，冇直向鎖。

修法：橫向視窗顯示直向鎖。

負責：遊程。

## P3 — 409 項有兩條失敗，因為路徑寫死

`tests/test_runner.gd:1078-1080` 找 `/workspace/glimmer-godot/...`。乾淨樹上面兩個檔都在 `native/android/.../RealWorldPlugin.kt` 同 `Share6dPlugin.kt`，測試仍然失敗。其餘 407 項過。

修法：改為檢查專案裡的 `native/android` 路徑，唔好寫死 `/workspace`。

負責：遊程。

## 遊美

泡泡框同 bubble-fix1 一致。`wall_shoes` 色塊係已知缺圖。
