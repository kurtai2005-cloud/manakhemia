# 浮動團絨 Android MVP（微光小圃）
- Capacitor 6 殼：www/index.html = /workspace/bundles/glimmer-combo.html + tools/fpet-bridge.js（`python3 tools/build_www.py`）
- 原生：android/app/src/main/java/hk/vizard/glimmer/fpet/（PetOverlayService 前景服務＋overlay、PetView Canvas、SettingsActivity、PowerGuideActivity、FloatingPetPlugin）
- 素材：`python3 tools/bake_overlay_atlas.py <liveliness_dir> android/app/src/main/assets/pet <form>`（sprout／radiant／soft）
- Build：`source env.sh; npm i; python3 tools/build_www.py; npx cap sync android; cd android; ./gradlew assembleDebug`

## 狀態同步（snapshot v3）
- `tools/fpet-bridge.js` 寫 `CapacitorStorage` → `glimmer.snapshot`：v1/v2 欄位照舊，加 `moodBand`（happy/ok/sad）、`sleeping`、`egg`、`needs{urgent,level,warnAt,vals,rate,rateAwake,floor,wakeAt}`。
- 心情／瞓覺／最急需求一變即寫（每 2 秒比對），30 秒定時寫照舊。
- Kotlin `PetStatus.project()` 用每小時變化率由 `ts` 推算而家嘅數值；v1/v2 舊 snapshot → 唔顯示狀態，其他照舊。
- 頭頂提示用 `assets/pet/pet_fx.*`（Zzz／心心／汗／! ＋遊戲 UI 需求 icon），由 `tools/bake_fx_atlas.py` 由遊戲現有素材砌；額外動作（sniff／swat／cheer_jump／droop／emo_hungry）由 `tools/bake_extra_clips.py` 加落各形態 atlas 尾，原有格唔郁。

## 互動
- 拋：快速拖放有慣性，撞邊彈返（沿底邊模式會跌返落底）。
- 沿底邊模式間中行去角落坐；自由行間中去左右邊坐。
- 玩圖示：設定揀主畫面格（4×6 預設／4×5／5×5／5×6／唔玩），遊戲唔喺前景時間中走去估計嘅 icon 格坐／聞／撥／彈。只用螢幕尺寸估格位，唔讀其他 app、唔需要無障礙／錄影／QUERY_ALL_PACKAGES。
- 瞓覺 2fps、企定 ~7fps，郁先 15fps。
