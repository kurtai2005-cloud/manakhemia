# Godot 4 強化第一批 — 景深＋調色 LUT、粒子圖

遊美交付。Kurt 2026-11-11 08:16 親口批「批」：做 Godot 4 強化第一批（A）景深＋調色表，（B）粒子圖。引擎 Godot 4，HD-2D（3D mesh 場景＋像素貼圖＋平面像素寵物）。

全部 Pillow／numpy 程序化像素／LUT，冇用 AI 圖。疊喺 `art/m1-icons-hunt @ 13a0047796cc51bfee4aa107f44b205e58f0e245`（未 merge）。今批全部新路徑 `art-pet/fx/` 同 `art-pet/tools/*godot_fx1*`／`fx1_common.py`，唔覆蓋花園 H1、M1 icon／狩獵、亦唔掂 M2 動作檔。唔 commit／push／merge。**只對 Godot 4**（舊 HTML5／three.js 已凍結，只當參考，唔再為佢交格式）。

重新生成同驗收：

```
cd <repo>
PYTHONDONTWRITEBYTECODE=1 python3 art-pet/tools/build_godot_fx1.py [--root .]
PYTHONDONTWRITEBYTECODE=1 python3 art-pet/tools/validate_godot_fx1.py [--root .]
# 預覽（唔包 zip）：
PYTHONDONTWRITEBYTECODE=1 python3 art-pet/tools/preview_godot_fx1.py [--root .] \
  [--out /workspace/game-design/godot_fx1] \
  [--garden-src art-pet/scenes/garden3d/H1] \
  [--hunt-root .]
```

驗證結果：`art-pet/fx/validation.json`。

參考：花園 `art-pet/scenes/garden3d/H1/`（FORMAT.md、lights.json、camera.json）、狩獵 `art-pet/m1_icons_hunt/` FORMAT §7、Kurt 認可嘅 `day_cam_steady.gif`／`night_lamps.gif`。

## 0. 單位同鏡頭

- **1 unit＝1 個 1x 美術 px**。Y 上，+Z 向鏡頭。同花園 H1／狩獵草原一致。
- 鏡頭：pitch 30°、dist 580、垂直 fov 40°、target `[0, 30, −72]`。
- Godot 匯入 **建議 scale＝1**。若專案用 1 unit≈1 m，import scale **0.01**，則把下面所有**距離**（DoF near／far／transition、fog_depth_begin／end、粒子速度／重力／AABB／emission extents）×0.01。`dof_blur_amount`、glow、tonemap、LUT、粒子 `scale_min/max` 同 `amount` **唔改**。

## 0.1 畫質分級（低＝開發基準）

低畫質係開發基準，但**仍然係同一個 3D 場景**（地面／mesh／寵物、前後遮擋都在），只熄**影、glow、DoF、fog**，可以降解像度；**唔可以退返平面層**。中／高檔只喺開發者模式開呢啲效果。

| 項 | low（開發基準） | mid | high |
|---|---|---|---|
| 影（DirectionalLight3D.shadow_enabled、shadowIntensity 0.3） | 關 | 開 | 開 |
| glow | 關 | 開（用 preset 值） | 開（intensity 可 ×1.15） |
| DoF（near／far enabled） | 關 | 開 | 開（距離／amount 同 mid） |
| fog（depth fog） | 關 | 開 | 開 |
| LUT／adjustment | **開**（調色成本低） | 開 | 開 |
| 粒子 | `amount_low` | `amount_mid` | `amount_high`（秋天落葉用 `amount_autumn`） |

機讀：`environments.json` → `quality.tiers` 同 `quality.field_tiers`（逐項 low／mid／high）。presets 同 camera_attributes 寫嘅係 mid／high 嘅「開」值；低檔把四項 enabled 設 false，LUT 仍指向同一張 png。

## 1. 景深（CameraAttributesPractical）

檔：`art-pet/fx/environments/environments.json` → `camera_attributes`（七套 preset 共用同一組 DoF）。

| 欄（Godot 名） | 值（art unit） | 說明 |
|---|---|---|
| `dof_blur_amount` | 0.16 | 八方式輕朦，像素唔好過糊 |
| `dof_blur_near_enabled` | true | |
| `dof_blur_near_distance` | 400 | 近於此幾乎全朦（畫面下方近景高草） |
| `dof_blur_near_transition` | 110 | 400→510 轉清晰；焦段約 510 起 |
| `dof_blur_far_enabled` | true | |
| `dof_blur_far_distance` | 720 | 中景／屋／樹後開始朦 |
| `dof_blur_far_transition` | 380 | 約 1100（遠山／天）全朦 |

對齊 dist 580：寵物／玩區約 530–650 喺焦內。玩家手拖 ±10°、自動擺 ±5° 都用同一組。`auto_exposure_enabled=false`（像素畫面要穩定）。

接入：整一份 `CameraAttributesPractical` `.tres`，掛喺 **Camera3D.attributes**（唔好只掛 WorldEnvironment，否則 3D 編輯器預覽會成日朦）。專案設定 DoF quality 用 Mobile 預設即可；若出現圈狀偽影先再提高。**低檔把 `dof_blur_near_enabled` 同 `dof_blur_far_enabled` 設 false**（或 amount＝0）；中／高先開。

## 2. Environment 同調色 LUT

檔：`environments/environments.json`（七套 preset：日、黃昏、夜、春、夏、秋、冬）、`luts/lut_<id>.png`、`luts/lut_identity.png`（匯入驗證用，畫面應不變）、`luts/luts.json`。

每套包含：tonemap、glow、depth fog、adjustment（brightness／contrast／saturation＋LUT）。SSR／SSAO／SSIL／SDFGI／Volumetric Fog **三檔都關**。建議渲染器 **Mobile 或 Forward+**；Compatibility 嘅 Glow 參數較少，DoF 請遊程確認。低檔再熄 glow／fog（LUT 仍開，見 §0.1）。

### 2.1 LUT 格式（Godot 4 官方 33³ strip）

- 尺寸 **1089×33** PNG RGB（33 個 33×33 格橫向排）。
- 佈局同官方文件 `environment_adjustments_3d_lut_template`：由左到右 33 格＝**B 0→1**；格內 **X＝R 0→1**，**Y 上→下＝G 0→1**（PNG y=0 係 G=0）。
- **匯入**：Import As **Texture3D**；Horizontal slices=**33**，Vertical=**1**；Filter **Linear**；**唔做 mipmap**；壓縮 Lossless 或 VRAM Uncompressed（避免 LUT 出區塊）。指派到 `Environment.adjustment_color_correction`。
- LUT 喺 **tonemap 之後**生效。今批 LUT 按 **Linear tonemap**（同預覽 clip 0–1）編。若改用 ACES／AgX／Filmic，要再校 LUT。
- 先用 `lut_identity.png` 驗證：畫面應同冇 LUT 一樣。若有色偏或一格格切片感，多數係 slices 或 Y 向設錯。
- 詳細機讀：`godot_import.json`。

### 2.2 七套樣子

| id | 用途 | 重點 |
|---|---|---|
| day | 日／晨光暖調 | 接近 H1 穩陣 GIF，只稍為提暖同輕對比 |
| dusk | 黃昏 | 暗位偏紫、高光金橙，整體稍暗 |
| night | 夜 | **地面要暗過而家**：遊程報 game 夜地 lum 約 55，認可 GIF 約 26；夜空約 55。LUT 把暖綠中灰（約 55）壓到約 26，藍色／中性天空保持約 55，暖色燈高光保留 |
| spring | 春（日間季節） | 嫩綠、稍亮、高光略粉 |
| summer | 夏 | 綠更飽和、金光、對比稍高 |
| autumn | 秋 | 綠轉琥珀，高光暖 |
| winter | 冬 | 去飽和、陰影偏青藍 |

季節套係**日間**季節調色；黃昏／夜係時段。而家未做「秋夜」等交叉 LUT（要再批先做 12–21 套）。季節×時段可暫時：季節 LUT 或時段 LUT 二揀一，再靠該 preset 嘅霧色／曝光微調。

**夜景接入**：請同時用 night Environment（`tonemap_exposure` 0.88、霧 `#161a28`、glow 開俾燈Bloom）＋ `lut_night.png`。只換 LUT、光參數不變，LUT 本身已處理「地 55→26、空約 55」。H1 側窗請綁 `window_side`（唔好再跟 `window`）。

## 3. 粒子

路徑：`art-pet/fx/particles/`。每款一張 PNG sprite sheet（alpha **只有 0/255**，透明 RGB=0，Nearest）＋一份 JSON（GPUParticles3D／ParticleProcessMaterial 建議參數）。索引：`particles.json`。

| id | 檔 | 格 | 用法 |
|---|---|---|---|
| fireflies | fireflies.png 64×16（8×8 格，8×2 幀） | 螢火蟲。Add＋emissive，脈衝 8 幀。H1 夜約 26 隻（mobile 16），狩獵只喺黃昏／夜、量少啲。色對齊螢火瓶 `#c8ffb0` |
| leaves | leaves.png 128×256（16×16 格；春夏秋冬各 3 形狀×8 旋轉） | 落葉。按 `season_rows`／`groups` 揀幀。秋天可用較多 `amount_autumn` |
| petals | petals.png 64×32（8×8；粉／白／淺金×8 旋轉） | 花瓣，春夏、花圃／花叢上 |
| rain | rain.png 64×32（16×16；4 部長條＋4 幀水花） | 雨。長條建議 `particle_flag_align_y`。水花可用第二個 one-shot（M1 可先淨條） |
| snow | snow.png 64×32（8×8；4 種雪花×閃爍／旋轉） | 雪，冬天 |
| grass_debris | grass_debris.png 64×16（8×8） | 撥草碎屑。`one_shot`、`explosiveness=1`，`part_grass` 開始後約 80–120ms 喺寵物腳底爆發。H1 菜畦／花盆互動同狩獵撥草共用 |

速度／重力／AABB 用 art unit。接入：每款一個 `GPUParticles3D`＋`ParticleProcessMaterial`＋`StandardMaterial3D`（Billboard＝Particle，`particles_anim_h_frames`／`v_frames` 跟 JSON，Filter Nearest，關 mipmap）。螢火蟲 `blend_mode=add`（RGB=0 即唔加）；其他 **Alpha Scissor 0.5**。數量：低檔 `amount_low`、中 `amount_mid`（＝舊 `amount_mobile`）、高 `amount_high`（＝`amount`）。低檔唔熄粒子，只減少數量。參數數字見各 `particles/<id>.json`。

## 4. 目錄

```
art-pet/fx/FORMAT.md
art-pet/fx/godot_import.json
art-pet/fx/validation.json
art-pet/fx/environments/environments.json
art-pet/fx/luts/lut_identity.png
art-pet/fx/luts/lut_{day,dusk,night,spring,summer,autumn,winter}.png
art-pet/fx/luts/luts.json
art-pet/fx/particles/{fireflies,leaves,petals,rain,snow,grass_debris}.png
art-pet/fx/particles/{…}.json
art-pet/fx/particles/particles.json
art-pet/tools/fx1_common.py
art-pet/tools/build_godot_fx1.py
art-pet/tools/validate_godot_fx1.py
art-pet/tools/preview_godot_fx1.py
```

預覽（唔包 staging zip，放 `/workspace/game-design/godot_fx1/`）：`lut_dof_garden_day.png`、`lut_dof_hunt_day.png`、`lut_dof_dusk.png`、`lut_dof_garden_night.png`、`compare_sheet.png`、`luts_strip.png`、`particles_sheet.png`，同埋每款粒子一個 GIF（<3MB）：`fireflies.gif`、`leaves.gif`（四季 2×2）、`petals.gif`、`rain.gif`、`snow.gif`、`grass_debris.gif`。預覽用現有 numpy 渲染器＋後製 DoF／LUT，**唔係 Godot 引擎畫面**。

## 5. 接入步驟（遊程）

1. 把今批解壓到 repo 根（疊 `art/m1-icons-hunt`）。
2. 用 `godot_import.json` 寫 LUT 同粒子 PNG 嘅 `.import`（LUT＝Texture3D 33×1；粒子＝Nearest、關 mipmap）。
3. 將 `environments.json` 七套轉 `Environment`＋一份共用 `CameraAttributesPractical` `.tres`；Camera3D 用呢份 attributes；各場景／時段切 WorldEnvironment。按 `quality.field_tiers` 做低／中／高三檔（或運行時開關）：**低檔熄影／glow／DoF／fog，LUT 仍開**；中／高開效果。開發基準用低檔。
4. 夜：開 H1 `intensityNight` 燈、降 ambient／曝光，加 `lut_night`（低檔都套 LUT）；中／高再加霧同燈 glow。量地面 lum 應對齊認可 GIF（約 26），天空約 55。
5. 粒子：按 JSON 建 GPUParticles3D，`amount` 跟畫質檔。螢火蟲跟 H1 夜同狩獵黃昏／夜；撥草碎屑 hook `part_grass`；落葉／花瓣／雨／雪跟季節同天氣。
6. 跑 `validate_godot_fx1.py` 應全過。
