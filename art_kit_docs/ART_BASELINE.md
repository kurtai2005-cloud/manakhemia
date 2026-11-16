# ART_BASELINE — 0.6.18-pilot vc27 rear-ground r1

時間：2026-11-16 19:50 Asia/Shanghai UTC+8
來源版本：凍結 zip SHA-256 `2da14bc862b491906c1fbec80506af2dfa12152e0359080eba59d4c406e0e6a4`（`godot_hd2d_v6/`，Godot 4.7.2-stable）
接受範圍：parent 窄幅 still-accept + independent 30s night Low 19:9 walk PASS；Kurt t377u「Ok 可以去下步」。

單位：世界單位 wu。`PRESET/HD2D_RECIPE.md` 寫住 **1 wu = 1 game pixel**（歷史文件；今次冇重新量度）。Shader 距離／區域若無另註，當 wu。gain 0.3 係無單位倍率。dapple `speed` 用 shader TIME，單位唔另行換算。

## 風格（只記已接受事實，唔寫色彩理論）

- 日／夜已接受外觀要保留。**唔好改 environment 去「優化」。**
- 夜填光方法（已接受）：`EMISSION += ALBEDO * cool sky irradiance`（log：`path=emission*albedo`）。保留草紋同陰影，唔係一塊藍地板。
- 日路徑：`HD2D_NIGHT_TOE` 喺日間回傳 0；rear-ground patch 聲稱日路徑不變。今次 **冇** 喺 rear_r1 重拍日 still。包內日圖來自 continuity 回歸拍攝，只作對照。
- 測視：已接受畫面係 Low、540×1140（19:9）、`--rendering-method mobile`。

## 已接受、唔好改嘅關鍵參數

Night toe / sky（`scenes/art_depth.gd` `_night_toe_gain`；shader uniform `night_toe_gain` / `night_sky_rgb`）：

- `HD2D_NIGHT_TOE` **unset** → 預設 **0.3**
- `HD2D_NIGHT_TOE=0` → 關閉（vc25 對照）
- 明確數值仍可覆蓋；範圍 clamp 0.0–2.0（源碼如此）
- 預設 sky RGB `(0.70, 0.92, 1.00)`（實際 bind log 寫過 `sky=(0.7, 0.92, 1.0)`）

Dapple 步調（vc25 已接受，後續版本保持；`shaders/ground_dapple.gdshader` 預設）：

- `speed = 1.15`
- drift 用 `0.65 * wind(...)`
- 第二層取樣用 `drift * 0.25`
- **唔好改呢組步調。**

前景 macro／bake 覆蓋（源碼現值，單位 wu）：

- NearLawn / night_region：`Vector4(-340, -120, 340, 330)`（x0, z0, x1, z1）— macro 範圍。`near_macro` 喺 z=-120 結束，後便地面延伸更遠（記錄約到 -480）。
- 8 wu world-border 過渡（120–128）：macro 蓋唔到嘅內場最後 8 wu，淡入對應 outer tile。
- 夜：outer tile 草保持 `sky × 0.3`，**唔好**喺 macro 外面把 albedo 置零（呢個就係 t376u 後便黑窿修正）。
- `blade_mean = vec3(0.0544, 0.0841, 0.0150)`（源碼註：`lawn_blades_v614.png` 線性平均）

19:9 測試開機 override（只用於擷取測試，唔係遊戲預設）：

- SHA-256 `b2e6782d92e20e3be91c5205e130e1b55af25fe7edf7824f57bffaeb05175d11`
- `window/size/viewport_width=540` / `height=1140`
- 開機前複製做 `override.cfg`，用完刪；`project.godot` 保持 1080×1920。

## 整合（唔係 plug-and-play）

Texture、shader、PRESET `.tres` 單獨複製到新場景 **唔保證** 重現已接受外觀。`art_depth.gd` 負責綁定 GroundInner / GroundOuter / NearLawn／tuft、夜 uniform、macro／outer。`capture.gd` / `capture.tscn` 係遊程擁有入口。細節見 `runtime_wiring/README.md`。

`PRESET/hd2d_env_*.tres` 同 `hd2d_camera_attrs_*.tres` 存在於樹內，但歷史 `HD2D_RECIPE.md` 已寫過後期代碼可能覆寫 preset。**唔好當 drop-in 就等於而家嘅已接受光。** 非平凡 shader 邏輯調查交云端，呢份只記錄已見預設同已知配方。

## UI

`art/ui/` 現存只有字型 `GenWanMin2TC-R.subset.otf` 同 OFL 文本。**未確立 UI 標準，冇鎖定 icon 尺寸。** 唔好當已鎖定。

## 出處同授權（只根據樹內證據）

- 專案 `CREDITS.md` 最後註明段落係 **v6.13**。其後加入嘅檔（例如 `lawn_blades_v614.png`）喺 CREDITS **冇**專項，標未核證。
- 專案美術：**冇**另外找到正式授權檔。CREDITS 自稱原作／AI 輔助再手修，呢次不當商業授權或 AI 署名發明。
- 列明過嘅 GenerateImage 底圖：CREDITS 引用 xAI 條款；呢次包 **冇** 重新核對條款頁。
- 字型：`OFL_GenWanMin2.txt` 寫 SIL OFL 1.1，Reserved Font Name `Source`。只適用呢個字型檔。
- Octopath 截圖：CREDITS 寫只作學習／直方圖參考，無複製像素。截圖本身 **唔喺** 呢個包。

## 唔做

唔好繼續拋光已接受場景、唔好發明新玩法或新場景資產清單、唔好改 capture／遊程 HANDOFF、唔好 APK、唔好 merge 去 main。
