# G0 筆記

## 浮動團絨（Android overlay）— 唔入 G0

舊 HTML5 app（`hk.vizard.glimmer.fpet`）用 Capacitor + Kotlin overlay 喺其他 app 上面顯示團絨。G0 套件名改咗做 `hk.vizard.glimmer.fpet.godot`，兩款並排安裝；舊 app 繼續負責浮動窗。

之後若要喺 Godot 版做浮動窗，建議：

1. 用 Godot Android 外掛（AAR／Gradle）開 SYSTEM_ALERT_WINDOW，用獨立 WindowManager View 畫 2D 寵物（唔好整個 Godot 主視窗當 overlay）。
2. 需求／睡眠推算可以重用 `Sim.gd`／`TimeService.gd` 嘅純邏輯（而家已經同畫面分開）；或者把狀態寫入共享檔／ContentProvider 俾 Kotlin overlay 讀。
3. 舊 app 嘅 overlay snapshot 欄位（moodBand、urgent、rate、floor、wakeAt）可以喺 Sim 加一個 `overlay_status()` 對齊。

## §7 進化

階段時長、離線最多升 1 階、靜光 fadeReady（要玩家確認化光）已移植。G0 未做照顧／路線互動，入成體只按 CQ 判燦光／柔光／微塵；五路線分（潮／菇／晶／月／火）同螢絨條件留待下一階段。

## 低畫質（Kurt 11-11 08:20）

低檔仍然渲染完整 3D 花園：同一場景、鏡頭、mesh、NavigationRegion3D、深度遮擋。只減成本——唔開 shadow map（腳底 blob 得）、唔開 glow／DoF／fog、`scaling_3d_scale` 0.67、粒子預算 0。永遠唔退回分層 2D。
