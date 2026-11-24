# HD-2D 方法筆記（微光小圃測試）

我哋只係借 Octopath Traveler 嘅**質感同光影做法**，建築同繪圖仍然用《微光小圃》自己嘅 V3-A 小屋／園圃，唔抄佢哋半木架村。以下係開源 Godot 專案同公開技術學返嚟嘅對應，唔係抄 Square Enix 資產。

## Octopath 做緊咩 → Godot 點對

| 做法 | Godot 節點／設定 |
|---|---|
| 2D 像素角色企喺 3D 場景 | `Sprite3D`，`pixel_size=1`，`BILLBOARD_FIXED_Y`，pivot 對腳（團絨 64px、pivot 32,61），`ALPHA_CUT_OPAQUE_PREPASS` 先可以投影 |
| 低面數建築 + 手繪像素貼圖 | 現有 garden3d GLB；`TEXTURE_FILTER_NEAREST`、唔生成 mipmap、alpha scissor 0.5；官方 atlas 用 `SHADING_MODE_PER_VERTEX`（法線已按面畫好）。地面／新道具用逐粒手繪 tile + 可選 texel snap shader |
| 真光真影 | `DirectionalLight3D`（H1「晨光暖調」方向／色），`shadow_enabled`；夜晚再開 `OmniLight3D`（燈籠／窗／燈柱／螢火瓶，用 `intensityNight`） |
| 暖高光、冷陰影 | 陽光 `#ffe6b8`；環境光偏冷（官方 `#cfe0f0`，我哋略減能量令形體同影讀到）；貼圖高光偏暖、暗部偏冷，但中間調跟 V3-A 原色，albedo **唔烘**方向光 |
| Tilt-shift 景深 | `CameraAttributesPractical`：近／遠都只虛畫面上下邊緣，寵物同小屋保持實。Forward+ 先會真係模糊；Compatibility 可能無效 |
| Bloom | `Environment.glow_*`，門檻提高，只讓高光同夜燈開花 |
| 體積霧／大氣 | Forward+：`volumetric_fog` 低密度、中性偏冷（唔用官方暖黃 `#ffe8c8`，避免中景變黃）。Compatibility 改用 `FOG_MODE_DEPTH`（begin≈520，end≈1600） |
| 固定鏡頭 | `Camera3D`：pitch 30°、fov 40°、dist 580、target `(0,30,-72)`，同 H1 `camera.json` |

## 畫質分級（同一 3D 場景）

- **High（Forward+，真 GPU）**：影、glow、volumetric fog、SSAO、CameraAttributes DOF 全開。
- **Low**：同一批 mesh／貼圖／燈方向，只關影、glow、霧、DOF、SSAO。
- **Compatibility / 呢部 box 嘅 llvmpipe**：有 glow、傳統 depth fog、方向光陰影（品質有限）。**無** volumetric fog、SSAO、SDFGI、真 DOF。Capture 會印 `rendering_method` / `driver`。

## 點樣學（只 MIT／方法，唔搬藝術）

- t3ssel8r 像素 3D：把光照取樣扣去 texel 中心（我哋 `shaders/texel_lit.gdshader` 係自己寫，手法歸功 t3ssel8r／Jettelly／David Holland／tentabrobpy）。
- [CBerry22/3d-Pixel-Art-In-Godot-4](https://github.com/CBerry22/3d-Pixel-Art-In-Godot-4)（MIT）— 後製像素化，同 Octopath「高解像 3D + 像素貼圖」唔同，我哋唔用呢條路。
- [KavyaJP/Godot-Hybrid2D3D-Renderer-GDExtension](https://github.com/KavyaJP/Godot-Hybrid2D3D-Renderer-GDExtension)（MIT）— Y-billboard、nearest、alpha scissor、底中錨點。
- [leopeltola/Godot-3d-pixelart-demo](https://github.com/leopeltola/Godot-3d-pixelart-demo)（MIT）、[Robert-K/godot-3d-pixel-art](https://github.com/Robert-K/godot-3d-pixel-art)（MIT）、[astrellon/godot-3d-pixel-art](https://github.com/astrellon/godot-3d-pixel-art)（MIT）。
- [voithos/godot-smooth-pixel-camera-demo](https://github.com/voithos/godot-smooth-pixel-camera-demo)（MIT）— texel 對齊鏡頭。
- [kanaworksai-hue/tobidasu](https://github.com/kanaworksai-hue/tobidasu)（MIT，Godot 4.7+）。

godotshaders.com 有篇 texel quantization，頁面沒清楚標執照，所以**無**逐字搬嗰段 shader。

## 貼圖約定

先出 `TEXTURE_SHEET.png`（1× + 8× nearest、標名、2×2 接縫），先至舖入場。八種物料（磚、瓦、護牆板、梁、灰泥、石頭路、草、室內地板）各 3 款 16×16，4–5 階色依 V3-A 中間調，高光偏暖、暗部偏冷。官方 GLB atlas（窗、藤、門等獨有位）保持原圖，唔好用平鋪木紋蓋過去。地面 `textures/ground_composed.png`（512²，2 px/wu）由手繪草／石磚同官方 AO 合成。

詳細出處見 `CREDITS.md`。


### 4j (v6.11) 影要跟物件真形狀；光柱要由雲出
- **假影 blob 嘅源頭唔一定喺 bake：** v6.4 合成嘅 `ground_composed.png` 本身畫咗圓形陰影，疊喺真 bake 上面就變「貼上去嘅波波」。先清底圖（`tools/ground_deblob_v6_11.py`），再 bake。near lawn macro 亦有隨機「冷色陰影池」，一併拎走。
- **Bake 解像度先係形狀：** High atlas + 2 splits 喺 bake 等於 ~0.3 wu texel → 鋸齒再 blur 成 blob。bake 用一張 8192 orthogonal map（~0.06 wu），軟度用物理半影 σ ≈ 0.12 + 0.0045·d。
- **Sun-view silhouette 重投影（理論上最準）要小心：** 佢會顯示遊戲入面根本唔 cast 嘅 mesh（voxel tree 部件）→ 多咗大塊假影。以引擎 shadow map 為準，Low bake 先會同 High live 一樣形狀。
- **形狀啱 ≠ 鏡頭睇得出：** 主樹真影蓋住大半空地 + 物件影太淺 → 欄杆／燈柱喺鏡頭入面淡。下一步加深細物件、收窄深度圖 blur。
- **光柱由雲出：** 用天空自己嘅雲 mask（同 dome 一樣嘅 view-direction 映射）喺光柱 shader 做遮擋 + 雲隙最光，冇起始線；雲邊向太陽面加金邊。
- **每樣「免費」都要量：** 一盞無影 bounce directional light 喺 Mobile 都要 +0.047 ms → Low 預設關。

### 4k (v6.12) 影要「睇得到」：手機比例下判斷，唔係淨係啱
- 樹影淺啲、有斑駁（0.72–0.88），物件影深啲（prop 0.38／cottage 0.42／fence、post 0.62），咁物件影先疊得喺樹影上面；class 深度圖 blur 0.9 wu、接觸 AO 0.42。
- 檢查「數值 vs 畫面」：mover shade 係顯示比例，shader 要 pow 2.2 解（線性讀法令 0.50 變 0.73）。底圖自帶嘅畫筆明暗會食咗影 → 底圖細節留 40%，影照舊。
- 光柱：alpha ×1.4、break_boost 1.25，雲遮 0.92 照留 → 由雲隙出、冇硬邊。
- 中景：Low 曝光 1.50、後草地 ×0.84、clump 空氣霧 0.30；量度用 PC Mobile 手機比例分帶平均（400–560／560–800／800–1140）。
- 樹冠：lobe 數 clamp(r/20, 2, 5)，大塊明暗，間隙深 0.22。

### 4l (v6.13) 用「睇落係乜」判斷，唔好淨睇平均色
- 0.6.12 平均 RGB 啱晒，但草地睇落係泥地：橄欖色 albedo × 金色陽光 × R 增益 → R ≥ G → 啡色。
- 草要用飽和嘅綠做 albedo，等金光將佢變暖綠金（唔係赭啡）；草尖黃綠、斑駁光塊、細花、三葉草，唔要深色枝。
- 陰影顏色係冷綠橄欖，唔係藍紫或啡。
- 花槽頂：bake 時將接收面升到花槽頂（y 6）、收埋花槽，就得到「落喺花槽上」嘅影。
- 每次都同 concept 同 0.6.9 並排睇質感，邊度差過 0.6.9 就要記低、跟住修。

