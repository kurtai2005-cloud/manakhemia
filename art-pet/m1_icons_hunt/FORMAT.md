# M1 icon ＋ 狩獵精簡版（草原 1 區）— 格式

遊美交付，Kurt 2026-11-11 07:41 全批：「icon、M2 動作同狩獵精簡版入 M1，遊美可以開畫」。今批只做 **M1 icon（34）＋夢泡泡框＋狩獵 M1 lite**。M2 動作（投信、招牌 idle×6、小動作×4、指相框、訪客動作）留下一批。

全部 Pillow／numpy 程序化像素畫，冇用 AI 圖。只借 Chiikawa 氛圍（細細隻、可愛、柔和），造型／名／配色組合全部原創。風格跟 V3-A：金光深藍磨砂＋金幼線；sprite alpha 只有 0／255（透明 RGB＝0）；UI／光影層（夢泡泡框）可用真 alpha。

重新生成同驗收：

```
cd <repo>
PYTHONDONTWRITEBYTECODE=1 python3 art-pet/tools/build_m1_icons_hunt.py [--root .] [--preview /workspace/game-design/m1_icons_hunt]
PYTHONDONTWRITEBYTECODE=1 python3 art-pet/tools/validate_m1_icons_hunt.py [--root .]
```

疊喺 `code/glimmer-3d-h1` 最新（本機 `1bf1cb3ae`，遲過 `ed28e28a`）。美術係新路徑，唔覆蓋花園 H1 mesh。唔 commit／push／merge。

## 0. 單位

- **1 unit＝1 個 1x 美術 px**。Y 向上，地面喺 XZ 平面，+Z 向鏡頭。
- 寵物／小怪／果 billboard：1 px＝1 unit，`pivotPx` 對準世界座標 `(x, 0, z)`。
- 同 3D 花園 H1（`scenes/garden3d/H1/FORMAT.md`）一致，相機數字可以直接對照。
- Godot 4 建議 import scale 見第 7 節。

## 1. M1 icon（34）＋夢泡泡框

路徑：`art-pet/ui/m1_icons/`。規格：`icons.json`。

| 組 | 數量 | id 前綴 | 用途（§3／§3.1） |
|---|---|---|---|
| 需要 | 4 | `need_eat`／`need_play`／`need_sleep`／`need_pet` | 頭頂需要泡泡（想食／想玩／想瞓／想摸） |
| 性格表情 | 6 | `expr_lively`／`expr_quiet`／`expr_diligent`／`expr_lazy`／`expr_clingy`／`expr_indep` | 活潑／文靜／勤力／懶散／黐人／獨立 |
| 心情 | 4 | `mood_happy`／`mood_ok`／`mood_sad`／`mood_sleepy` | 開心／普通／唔開心／眼瞓 |
| 事件 | 20 | `ev_*` | 離線故事頭頂 icon、夢境日記兩件「尋日事件」 |

事件 20 包括：現有 9 個世界事件（禮物、蝴蝶、流星、彩虹、螢火、夢話、鬧脾氣、尋寶、閃光日）＋ 11 個日常／離線（食、玩、瞓、行、返工、落雨、訪客、狩獵、傢俬、新蛋、步數）。每項有中文名喺 `icons.json`。

- 每個 icon：**32×32 @3x**（同 `kit_hd2d_v3`：喺 @3x 1:1 顯示），散檔 `icons/<id>@3x.png`，圖集 `atlas/icons_m1@3x.png`＋json 幀（padding 2、extrude 1）。
- pivot `(16, 16)`。alpha 0／255。整數倍放大、Nearest、關平滑。
- 最細可讀：32px 主體外框清楚，validator 查不透明像素數。

### 夢泡泡框 `bubble_dream@3x.png`

- 96×72、**真 alpha**（UI 層，磨砂深藍＋金幼線）。
- 兩格事件槽：`event_a` (14,16) 32×32、`event_b` (42,16) 32×32，重叠 4px，表示「兩件尋日事件撞埋」。
- 引擎把兩張 32px 事件 icon（Nearest）畫入槽；框本身可呼吸 opacity。

## 2. 銅證 icon（狩獵，4）

路徑：`art-pet/ui/m1_icons/badges/`。規格：`badges.json`。

| id | 對應小怪 |
|---|---|
| `badge_copper_dewlet` | 露珠偶 |
| `badge_copper_loambun` | 泥包包 |
| `badge_copper_seedfluff` | 穗綿 |
| `badge_copper_mossback` | 苔丘（大隻） |

32×32 @3x，V3-A 銅章＋剪影。銀／金證留 M2。

## 3. 草原 3D 場景（M1 lite：1 區）

路徑：`art-pet/scenes/hunt3d/prairie/`。格式跟花園 `garden3d.mesh/2`。

- `objects.json`：mesh 實例、backdrop、pet／critter billboard 欄、地面。
- `meshes/<id>.json`＋**同內容 `.glb`（glTF 2.0）**＋像素貼圖 1x／@3x（2 次方，alpha 0／255，1px gutter）。
- `ground/ground.png` 256²、`ground_ao.png`、`ground_tile.png` 64²（外圍無縫鋪）。
- `backdrop/bg_sky.png`、`bg_hills.png`（`type:backdrop`，unlit、far）。
- `lights.json`：日間太陽＋fill（唔投影）；`sun.shadowIntensity` 0.3（即時光影，同花園 H1）。M1 以日間為主。fill 唔投影。霧色 `#ffe8c8`。
- `camera.json`：**同花園 H1 穩陣鏡頭**：pitch 30°、fov 40 垂直、dist 580、target `[0,30,-72]`（寵物落畫面下半）、`followOffset [-20,0]`、`followOrigin [0,0]`、手拖 ±10°；自動擺鏡 `swayAmplitudeDeg` 5、`swayHalfPeriodSec` 6、`easeInOutSine`、`followDamping` 2.0。預覽 `hunt_cam_steady.gif`：600×844 再裁 `(0,190,600,590)`＝600×400、60 幀、6 秒。

### mesh 欄位（同花園，遊程原定）

`positions[]`、`normals[]`、`uvs[]`（**JSON：V 上 0–1**）、`indices[]`（逆時針＝正面）、`texture`（2 次方 png）、可選 `emissive`／`alphaTest` 0.5。每件 ≤300 三角。原點＝物件底中。`footprint` 局部＋`objects.json` 世界座標。

`.glb`：幾何同 json；**uv V 已翻做 glTF 慣例（V 下）**；`alphaMode=MASK`、`alphaCutoff=0.5`、sampler `NEAREST`（9728）；PNG 內嵌。`emissiveFactor=1` 時引擎要再乘燈強度（呢批草原件暫冇 emissive）。

物件：草叢變體（含前景高草）、蘆葦、野花、石、採集灌木、苔丘、**木拱門**（遠景入口標，唔擋寵物）、**木牌**、枯木、遠樹林剪影卡。角色（寵物、小怪、果）係 billboard，唔做 mesh。

地面貼圖對齊 H1：可平鋪 value noise 草簇＋Bayer 柔和 4 級草／苔／泥／石，小路＋泥位＋踏石分區；**冇全畫面重複斜線**。UV `u=(x+128)/256，v=(z+128)/256`，外圍 tile 以 `(−128,−128)` 對齊；`@3x` 取樣 texel 密度＝3／unit（同 H1）。

**呢批場景 mesh 係靜態，冇 3D 動畫。** 如果日後有 3D 動畫，會寫入同一個 `.glb` 嘅 Animation clip，名同下面 2D clip id 對齊（例如 `part_grass`）。而家寵物／小怪動作用 2D atlas。

## 4. 小怪 4 ＋ 果 6（billboard）

### 小怪 `art-pet/sprites/hunt/critters/`

全部原創造型（細細隻、圓身、柔和），唔抄任何現有 IP。

| id | 中文 | 畫布 | pivot | 大隻 | 變成果 |
|---|---|---|---|---|---|
| `dewlet` | 露珠偶 | 32 | (16,29) | 否 | `dewpear` 露梨 |
| `loambun` | 泥包包 | 32 | (16,29) | 否 | `sunkaki` 陽柿 |
| `seedfluff` | 穗綿 | 32 | (16,29) | 否 | `goldgrain` 金穗果 |
| `mossback` | 苔丘 | 48 | (24,45) | **係**（驚嚇位） | `moonplum` 月李 |

每個 `<id>.json`＋`atlas_<id>.png`／`_n.png`。動畫：

| clip | 幀 | fps | loop |
|---|---|---|---|
| `idle` | 4 | 4 | 是 |
| `scared` | 4 | 6 | 是 |
| `tofruit` | 6 | 8 | 否（抖→縮→成果→碌走） |

小怪唔會死；撲中就播 `tofruit` 然後碌走。其餘兩款果（星莓、霧葡）由撥草取得。

### 果 `art-pet/sprites/hunt/fruits/`

32×32，pivot `(16, 28)`（接地）。`fruits.json`＋`atlas_fruits.png`／`_n.png`＋散檔。

星莓／露梨／金穗果／月李／陽柿／霧葡。

## 5. 寵物狩獵 clip（4 × S／M／L）

路徑：`art-pet/sprites/tuanrong/motion/hunt/`。形態：**radiant**（同 dir4 試點）。§6 冇寫死 S／M／L 像素同幀數，今批按現有體型表同 CLIPS 語言定：

| 體型 | 畫布 | pivot | 對應 |
|---|---|---|---|
| S | 32×32 | (16, 29) | 絨芽級 |
| M | 48×48 | (24, 45) | 長老 evo_still 級 |
| L | 64×64 | (32, 61) | 花園 radiant／dir4 級 |

| clip | 中文 | 幀 | fps | loop |
|---|---|---|---|---|
| `part_grass` | 撥草 | 6 | 8 | 否 |
| `pounce` | 撲 | 6 | 8 | 否 |
| `carry_fruit` | 抱果行 | 6 | 10 | 是 |
| `cheer` | 歡呼 | 6 | 10 | 否 |

檔：`atlas_radiant_<clip>_<S|M|L>.png`＋`_n`＋`_emissive`＋`.json`。padding 2、extrude 1。朝右；朝左＝`scaleX −1`，**法線 R → 255−R**（同 dir4）。

`pounce`／`cheer` 由現有 `play`／`cheer_jump` 幀出發；`part_grass`／`carry_fruit` 喺現有姿勢上加草／果。S／M 由 L 像素縮放並對齊 pivot。

索引：`clips.json`。

## 6. 法線 `_n`

- Tangent space，**OpenGL（Y+，綠＝上）**。RGB＝n×0.5+0.5。alpha 同色圖逐 px；透明處 RGB＝(128,128,255)。
- 單位長 ±0.03，向外 B≥128，每幀頂部 G＞底部 G（validator 查）。
- Godot 4 **唔好 Invert Y**（見第 7 節）。

## 7. Godot 4 匯入注意

M1 起引擎轉 Godot 4。呢批 3D 物件交 **glTF 2.0 `.glb`**；2D sprite／icon 仍係 PNG＋atlas JSON。

### 7.1 單位同 import scale

美術世界 **1 unit＝1 art px**（64px 寵物＝64 unit，相機 dist 580）。兩種接法：

1. **建議先用 scale＝1**（Import → glTF → `meshes/scale` 或匯入後 root `scale = (1,1,1)`）。`camera.json`／`lights.json`／footprint 數字可以直接用，同花園 H1 試點一致。
2. 若專案想 1 Godot unit ≈ 1 m：用 **import scale 0.01**（1 art px ＝ 1 cm；64px 寵物 ≈ 0.64 m，夠「細細隻」）。屆時將 `dist`、`target`、燈座標、fog near／far、footprint **全部 ×0.01**（例如 dist 5.8、target y 0.30）。

Y 向上，同 Godot 預設；**唔使轉軸**。glTF 匯入時維持 Y-up。

### 7.2 像素貼圖（mesh 內嵌 PNG、地面、backdrop）

對每張 albedo／emissive（包括 glb 內嵌同外部 png）：

| 項 | Godot 4 設定 |
|---|---|
| Filter | **Nearest**（`texture_filter = TEXTURE_FILTER_NEAREST`；Import：`Compress` 可 Lossless／VRAM uncompressed，**Filter Nearest**） |
| Mipmaps | **關**（`generate_mipmaps = false`；Import 取消 Generate Mipmaps） |
| Alpha 0／255 | 材質 **Alpha Scissor**（`transparency = ALPHA_SCISSOR`，`alpha_scissor_threshold = 0.5`，同 glb 嘅 `MASK`／0.5）。唔好用 Alpha Blend（會漏邊） |
| Color space | albedo sRGB；唔好當 linear data |

場景材質已喺 glb 寫咗 `alphaMode=MASK`、`sampler NEAREST`。匯入後請檢查冇被 importer 改成 linear＋mip＋filter。可喺匯入插件或 `.import` 鎖定。

地面 `ground_ao.png` 係灰階遮罩（255＝冇遮蔽），乘法叠喺 albedo；當 **Non-Color** 資料匯入。

### 7.3 法線圖（`*_n.png`）

| 項 | 設定 |
|---|---|
| 類型 | Import 為 **Normal Map** |
| 慣例 | **OpenGL（Y+，綠＝上）**。Godot 4 預設即係呢個，**唔好勾 Invert Y / Flip Green** |
| Filter | Nearest，mipmaps 關 |
| Color | Non-Color / Normal Map（唔要 sRGB） |
| 透明 | alpha 同色圖；透明像素 RGB＝(128,128,255)＝平法線。Shader 應用色圖 alpha 做 scissor，唔好用法線 alpha 當高度 |

朝左鏡像 sprite 時，除咗 `scale.x = -1`，要把法線 **R 通道翻轉**（`normal.r = 1.0 - normal.r` 或 `normal.x *= -1` 喺 tangent space）。

### 7.4 2D atlas（icon、clip、小怪、果）

- 用 `AtlasTexture` 或自家讀 json `frames.<name>.frame`（`x,y,w,h`）＋`pivotPx`。
- `Sprite3D`／`AnimatedSprite3D`／自寫 Quad：`texture_filter = NEAREST`，`alpha_cut = ENABLED`（或 shader `ALPHA_SCISSOR` 0.5），`billboard = Y-billboard` 或圆柱（寵物 `face:"cyl"`：只繞 Y 對鏡頭）。
- 錨點：把 `pivotPx` 放到地面接觸點。公式同花園：腳底 ≈ pivot，64px 形態 pivot (32,61)。
- icon 只整數倍縮放（32 或 64）；@3x 裝置 1:1。
- 夢泡泡框用普通 UI `TextureRect`，可以開 alpha blend（真 alpha）。
- 動畫 fps／loop 見各 json `animations` 或 clip 表。clip 名就係 contract（`part_grass`、`pounce`、`carry_fruit`、`cheer`、小怪 `idle`／`scared`／`tofruit`）。

### 7.5 鏡頭、光、影

- `camera.json`：垂直 fov 40°、pitch 30°（固定，Octopath 式）、yaw 緩擺 ±5°、手拖 ±10°。跟拍公式：`cam += (desired − cam) * (1 − exp(−followDamping * dt))`。
- 太陽 `dir` 係**光行進方向**（由太陽指向場景，已正規化，Y 為負）。Godot `DirectionalLight3D` 嘅 −Z 要對準呢個向量（或 `look_at(dir)` 視實作）。
- `shadowIntensity` 0.3 → 對應陰影色／`shadow_opacity` 類參數。
- `fill` 第二盞 DirectionalLight，**shadow 關**，夜晚 intensity 0。
- 寵物 emissive × `petGlow`（醒 1、眼瞓 0.6、瞓 0），規則同花園／UI kit v3。

### 7.6 參考匯入表

`art-pet/m1_icons_hunt/godot_import.json` 用機讀寫低上述預設，方便批次寫 `.import` 或匯入插件。

## 8. 接入注意（通則）

- 觀察模式（§0.5）野外狩獵共用：撳寵物鏡頭跟住；3 秒淡 UI。
- 成年家人最多 3 隻組隊。同一寵物當日打工或狩獵二揀一。
- 抱果行：而家星莓烙入幀內；引擎可改用 attach（果 atlas＋手位）換其他果。
- 窄屏：草原比花園開揚，丘同木拱門可能要靠跟拍先同時入畫。預覽用 H1 同一裁切 600×400。
- 碰撞：寵物半徑 `pet.radius`（10），唔入 footprint 外擴 pad＋radius。灌木／丘／石／石柱有 footprint，草卡／花較細。

## 9. 目錄

```
art-pet/m1_icons_hunt/FORMAT.md
art-pet/m1_icons_hunt/godot_import.json
art-pet/m1_icons_hunt/validation.json
art-pet/ui/m1_icons/          icons.json、icons/*@3x.png、atlas/、bubble_dream@3x.png、badges/
art-pet/scenes/hunt3d/prairie/  objects／lights／camera、meshes/*.json+glb+png、ground/、backdrop/
art-pet/sprites/hunt/critters/
art-pet/sprites/hunt/fruits/
art-pet/sprites/tuanrong/motion/hunt/
art-pet/tools/build_m1_icons_hunt.py
art-pet/tools/validate_m1_icons_hunt.py
art-pet/tools/garden3d_mesh.py   # 共用寫 json＋glb
```

預覽（唔包入 staging zip，放 `/workspace/game-design/m1_icons_hunt/`）：`icons_sheet.png`、`hunt_scene.png`、每個 clip 一張 `_strip.png` 同一個 `.gif`（<3MB）。
