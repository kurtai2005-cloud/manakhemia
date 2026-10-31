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

## evo6 懸浮 atlas（Kurt 10-31 22:50：懸浮團絨要同遊戲一樣）

- 舊圖原因：懸浮窗一直用 `assets/pet/pet_sprout|soft|radiant`（s1 遊美 liveliness 美術烤），揀 atlas 只睇 snapshot `form`（遊戲 overlayInfo 降級成 sprout／soft／radiant 三款），snapshot 入面嘅 `evoForm` 冇用到；光卵（form=egg）更加 fallback 做 soft。
- 而家：`tools/bake_evo_atlas.py [glimmer-a] [out]` 由遊戲 `art/evo6/atlas_evo_<form>`（遊戲 render 用嘅 evo6 全幀 `<clip>_NN`）抽 13 個懸浮 clip，重排成 `assets/pet/evo/pet_<evoForm>.webp`（lossless、原生像素，Kotlin 整數放大）＋`.json`；有燈芽形態照遊戲疊 bulb_glow（neutral tint）。12 套：光卵、絨點、芽崽、跳跳期、守夜者×4（燦光／柔光／微塵／螢絨）、靜光×4。冇嘅 clip 寫入 `fallbackIdle`，Kotlin fallback 同形態 idle（光卵：tap→emo_happy，其他全部 idle；光卵唔行路）。
- `PetForm.pick(evoForm, form)`：snapshot 有 evoForm 而 APK 有嗰套 → 用 evo atlas；v1／唔認得 → 舊 atlas。

## snapshot v4：長按選單顯示遊戲狀態（Kurt 10-31 22:50）

- 遊戲 `G.evo.overlayStatus().info`（evo6 sim.overlayInfoText，只讀）：`name`（團絨）、`gen`、`stage`、`stageName`（光卵／絨點／芽崽／跳跳期／守夜者／靜光）、`sub`（同 HUD 階段副標：絨點仔／絨芽／跳跳絨／<形態>形態 · 準備化光）、`form`／`formName`、`evoForm`、`progress`、`stageH`、`leftH`、`ageSec`、`days`、`unwell`、`fadeReady`。
- fpet-bridge：有 info → `v: 4`＋`info`（v3 欄照寫）；evoForm／階段／日數／不適／準備化光一變即寫。
- 長按選單頂：名・階段名、副標＋幾日大、心情＋醒／瞓（＋不適）、四項需求（pet_fx need_* ＝遊戲 HUD icon，HUD 三色細條＋數值，用推算後數值）、階段進度條＋剩餘。只顯示，下面原有 5 個選項（沿底邊行／全畫面自由行／定點／開返遊戲／收起團絨）照舊 ≥48dp。
- fallback：v3 → 名・階段名（snapshot stage）＋心情／瞓＋需求，冇進度；v2 → 名・階段名＋「開返遊戲同步狀態」；v1 → 「團絨」。
