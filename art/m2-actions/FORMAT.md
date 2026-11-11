# M2 動作美術格式（投信、招牌 idle、小動作、指相框、道具、訪客）

遊美交付。疊喺 **art/m1-icons-hunt @ 13a00477**（remote 底本 **code/glimmer-3d-h1 @ 56d04d14**）。全部新路徑，唔覆蓋 M1 icon／狩獵／花園 H1。

美術全程序化（Pillow／numpy），冇 AI 圖。只借 Chiikawa 氛圍（細細隻、可愛、柔和），造型／名／配色原創。形態：**radiant**。sprite alpha 0／255（透明 RGB=0）；法線 OpenGL Y+（綠＝上）。

Kurt 核心：「觀察佢哋做事、睇得出性格」——6 種招牌 idle 要一眼認得出對應性格。

## 1. 寵物 clip（12 × S／M／L）

路徑：`art-pet/sprites/tuanrong/motion/m2/`。檔名：`atlas_radiant_<clip>_<S|M|L>.png`＋`_n`＋`_emissive`＋`.json`。padding 2、extrude 1。朝右；朝左＝`scaleX −1`，**法線 R → 255−R**。

| 體型 | 畫布 | pivot | 對應 |
|---|---|---|---|
| S | 32 | (16, 29) | 絨芽級 |
| M | 48 | (24, 45) | 長老 evo_still 級 |
| L | 64 | (32, 61) | 花園 radiant／dir4 級 |

| clip | 中文 | 幀 | fps | loop | 說明 |
|---|---|---|---|---|---|
| `mail_post` | 投信 | 6 | 8 | 否 | 拎信封行近、舉起、塞入 |
| `idle_lively` | 招牌·活潑 | 6 | 8 | 是 | 原地蹦跳 |
| `idle_quiet` | 招牌·文靜 | 6 | 6 | 是 | 坐低輕呼吸、眨眼 |
| `idle_diligent` | 招牌·勤力 | 6 | 8 | 是 | 彎腰執落葉 |
| `idle_lazy` | 招牌·懶散 | 6 | 5 | 是 | 攤喺地、偶爾呵欠 |
| `idle_clingy` | 招牌·黐人 | 6 | 8 | 是 | 伸手跟住你／想抱 |
| `idle_indep` | 招牌·獨立 | 6 | 6 | 是 | 自己望天、手搭額 |
| `scratch_head` | 抓頭 | 6 | 8 | 否 | 小動作 |
| `stretch` | 伸懶腰 | 6 | 8 | 否 | 小動作 |
| `look_sky` | 望天 | 6 | 8 | 否 | 小動作（一次過仰望，同獨立 idle 有別） |
| `proud_hips` | 叉腰得意 | 6 | 8 | 否 | 「覺得自己好醒」 |
| `point_frame` | 指相框 | 6 | 8 | 否 | 伸臂指向（右上） |

索引：`clips.json`（`format: m2.petclip/1`）。json 欄位同狩獵 clip：`frames.<name>.frame {x,y,w,h}`＋`pivotPx`，`fps`／`loop`／`frameCount`。

S／M 由 L 像素縮放並對齊 pivot。

## 2. 道具（§3.1 三件 ＋ 腳印）

路徑：`art-pet/sprites/props/m2/`。細件 **billboard**（png＋`_n`＋`props.json`／`atlas_props.png`）。三件同時出 **薄片 glTF 2.0 `.glb`**（`art-pet/scenes/m2_props/meshes/`，`garden3d.mesh/2`）。

| id | 中文 | 尺寸 | pivot | 用途 |
|---|---|---|---|---|
| `prop_envelope` | 信封 | 32×32 | (16, 28) | 投信 |
| `prop_postcard` | 明信片 | 32×32 | (16, 28) | 蝸牛郵差送到；卡面原創遠足小景 |
| `prop_letter` | 手信 | 32×32 | (16, 28) | 鄰居探訪完留低 |
| `decal_footprints` | 腳印貼地 | 64×32 | (32, 28) | 同手信一組；貼地 decal，唔投影 |

1 unit＝1 art px；薄片立喺 Y，原點底中。

## 3. 訪客招牌動作（每位 1）

路徑：`art-pet/sprites/visitors/m2/`。3b 三位朋友訪客，各 1 條 6 幀循環招牌（48×48 畫布，朝右）。

| id | 中文 | clip | 中文勢 | pivot（48 畫布） |
|---|---|---|---|---|
| `snail_postman` | 蝸牛郵差 | `snail_deliver` | 鞠躬遞信 | (23, 45) 左右（見 json） |
| `mushroom_granny` | 蘑菇婆婆 | `granny_seed` | 奉上種子 | 見 json |
| `firefly_vendor` | 螢火小販 | `vendor_show` | 搖瓶展示 | 見 json；有 emissive |

索引：`visitors.json`。billboard，Y-billboard，Nearest，Alpha Scissor 0.5。

## 4. Godot 4 匯入注意

M1 起引擎轉 Godot 4。3D 薄片交 **glTF 2.0 `.glb`**（Y 上）；2D sprite／clip 仍係 PNG＋atlas JSON。詳細見 `godot_import.json`。

### 4.1 單位

美術世界 **1 unit＝1 art px**（64px 寵物＝64 unit）。兩種接法：

1. **建議先用 scale＝1**（Import → glTF → `meshes/scale` 或匯入後 root `scale = (1,1,1)`）。同花園 H1／M1 狩獵試點一致，鏡頭數字可以直接用。
2. 若專案想 1 Godot unit ≈ 1 m：用 **import scale 0.01**（1 art px ＝ 1 cm；64px 寵物 ≈ 0.64 m）。屆時將 `dist`、`target`、燈座標、fog、footprint **全部 ×0.01**。

Y 向上，同 Godot 預設；**唔使轉軸**。

### 4.2 貼圖

| 項 | Godot 4 設定 |
|---|---|
| 過濾 | **Nearest**（`TEXTURE_FILTER_NEAREST`） |
| Mipmaps | **關** |
| 透明（alpha 0/255） | **Alpha Scissor** 0.5（`alpha_cut = ENABLED` 或 shader `ALPHA_SCISSOR`） |
| 法線 | **OpenGL（Y+，綠＝上）**。Godot 4 預設即係呢個，**唔好勾 Invert Y / Flip Green** |
| 朝左 | `scale.x = -1` 時法線 **R → 255−R** |
| Emissive | 乘燈強度；螢火小販瓶／寵物光芽用 |

`.glb`：`alphaMode=MASK`、`alphaCutoff=0.5`、sampler `NEAREST`（9728）。

### 4.3 2D atlas／Sprite3D

- 用 `AtlasTexture` 或自家讀 json `frames.<name>.frame`＋`pivotPx`。
- 錨點：把 `pivotPx` 放到地面接觸點。公式同花園：腳底 ≈ pivot，64px 形態 pivot (32, 61)。
- `texture_filter = NEAREST`，`alpha_cut = ENABLED`，`billboard = Y-billboard`。
- 動畫 fps／loop 見各 json。clip 名就係 contract（上表）。

呢批 3D 薄片係**靜態**，冇 3D 動畫。日後若有，會寫入同一個 `.glb` 嘅 Animation clip，名同 2D clip id 對齊。

## 5. 預覽

唔包入 staging zip，放 `/workspace/game-design/m2_actions/`：

- `overview_sheet.png`：12 clip（L）＋3 訪客＋4 道具總覽
- 每個 clip 一張 `_strip.png` 同一個 `.gif`（S/M/L 並排，<3MB）
- 訪客各一張 strip＋gif
- `garden_idle_steady.gif`：6 秒、600×400，H1 花園穩陣鏡頭（pitch 30°、dist 580、target `[0,30,-72]`、sway ±5°、裁 `(0,190,600,590)`），示範幾隻性格 idle 同小動作

## 6. 驗證

```
PYTHONDONTWRITEBYTECODE=1 python3 art-pet/tools/validate_m2_actions.py [--root .]
```

結果：`art-pet/m2_actions/validation.json`。
