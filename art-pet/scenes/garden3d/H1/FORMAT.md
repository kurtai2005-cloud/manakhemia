# 3D 花園試點 H1 — 格式（全 mesh 版，Three.js）

由 `tools/build_garden3d.py all` 生成（mesh 工具：`tools/garden3d_mesh.py`；各件砌法：`tools/garden3d_props.py`；小屋：`tools/garden3d_house.py`），`tools/validate_garden3d.py` 驗證，`tools/preview_garden3d.py` 出預覽（預設 `/workspace/game-design/pilot3d_h1_mesh/`）。

**方案（Kurt 改方向，跟八方旅人）：除咗寵物（團絨／細佬係 billboard），場景全部係立體 mesh（低面數＋像素貼圖，alpha 0/255）。** 鏡頭固定 pitch 30°，最多擺 ±10°；寵物喺 XZ 自由行，行到物件後面會被深度遮住，每件有 footprint 碰撞。
- 做法：每件嘅**正面＝原 2D 美術 1:1**（同一組 V3 H1 調色像素），所以 0° 構圖同平面版一樣；厚度靠像素擠出／盒／錐台／交叉卡。
- 來源係 H1 V3 程序化花園（`build_garden_hd2d_v3.build_index_v3('H1')`），逐件重畫抽出。全部程序化（numpy／Pillow），冇用 AI 圖。

## 座標同單位
- **1 unit＝1 個 1x 美術 px**。Y 向上，地面喺 XZ 平面。
- 原點＝寵物預設企位（2D 腳底 art (97,292)）。+X 向右，+Z 向鏡頭。
- 由 2D 搬過嚟嘅規則：
  - x＝art x − 97。
  - 前排物件：z＝(art y − 292) × 1.6。
  - 後排（籬笆、屋、樹、串燈）手擺 z −44…−52，保留 2D 前後次序：樹喺籬笆前，屋喺籬笆前。
  - 立體屋前牆 z −50（＝舊 billboard 位），向後深 44（到 z −94）；其他件正面喺原 billboard 位，向後（樹、菜畦）或者對稱（細件）加厚。

## 地面 `ground/`
- `ground.png` 256×256，`ground@3x.png` 768×768（最近鄰 ×3）。PNG sRGB，純俯視，**冇光影**。
  - 覆蓋 x、z 各 −128…+128，以原點為中心。
  - UV：u＝(x+128)/256，v＝(z+128)/256。圖頂＝z −128（遠，即屋同籬笆嗰邊）。
- `ground_ao.png` / `ground_ao@3x.png`：灰階 L，同尺寸，255＝冇遮蔽。內容有：
  - 物件接地 AO：每件 mesh 沿 footprint（rect／poly 外接矩形）四周一圈（約 3 units 衰減）；補位件、串燈冇。
  - 踏腳石邊、舞台邊石。
  - 用法：乘落地面 albedo。動態影仍然由引擎出。
- `ground_tile.png` 64×64（@3x 192）：**外圍草地 tile**。
  - pitch 30° 嘅直版畫面喺地上大約望到 −1250…+240 咁深，256 片唔夠，外圍要用 tile 鋪。
  - 以 (−128,−128) 對齊，每 64 units 鋪一格。
  - 256 片嘅底色本身就係呢個 tile ×4，近邊 6–20 units 冇點綴，所以接位無縫（validator 有驗）。
  - 建議外圍平面至少：x ±640、z −480…+320。
- 地面貼花（平貼喺地，唔係 mesh）：
  - 踏腳石 3 塊、舞台淺草圈＋苔窩＋邊石、小路（舞台去門口）。
  - 菜畦泥面、門口石板、樹頭苔、籬笆底深草帶。
  - 三葉草、小花、細石。

## 立體 mesh `meshes/` 同 `objects.json`
### mesh json（`format:"garden3d.mesh/2"`，遊程定嘅格式；每件一個 `meshes/<id>.json`＋同內容 `meshes/<id>.glb`）
| 欄 | 說明 |
|---|---|
| `format` `id` `zh` | 格式版本；id 同 objects.json 一致 |
| `units` | **1 unit＝1x art px；Y 上；原點＝物件底中（局部座標）**；+Z 向鏡頭。放置用 objects.json 嘅 `x`／`z`（／`y`）＋`yawDeg` |
| `positions[]` | 扁平 float 陣列 x,y,z,…（局部） |
| `normals[]` | 扁平，每頂點一個單位法線。實心件＝flat（每面頂點各自一份）。葉片／花苗卡用「向上＋向鏡頭」著色法線（0,.55,.83；側卡 .45,.5,.74），令打光同 billboard 時一致 |
| `uvs[]` | 扁平 u,v，**0–1，V 上**（three.js 慣例，原點左下） |
| `indices[]` | 三角 index；**逆時針＝正面**（validator 驗幾何法線同頂點 normal 同向） |
| `texture` `texture3x` `textureSize` | 一件一張像素 atlas（1x＋@3x 最近鄰），**2 次方尺寸**，每塊之間 1px 擠邊 gutter。alpha 只有 0/255，透明處 RGB＝0 |
| `emissive` `emissive3x` | 選填；同 atlas 對齊嘅發光圖（RGB＝燈色，alpha＝遮罩，⊂ 本體 alpha） |
| `alphaTest` | 0.5（葉片／籬笆縫／燈籠邊靠佢切形） |
| `doubleSided` | false。卡片已經自帶反向背面三角（背面睇到係鏡像），唔使開雙面 |
| `material` | `filter nearest`、冇 mipmap、lit、sRGB；貼圖冇烘方向光／AO |
| `bounds{min,max}` | 局部 AABB（底 y＝0；埋落地底嘅卡片行已裁走） |
| `footprint` | 局部碰撞：`{rect:{x:[x0,x1],z:[z0,z1]},pad}` 或 `{poly:[[x,z]…],pad}` |
| `castShadow` `receiveShadow` `vertexCount` `triangleCount` | 每件 ≤ 300 三角（build 時 assert） |

- `.glb`（glTF 2.0，單 mesh 單 primitive）：同 json 一樣嘅頂點／法線／index；**uv V 已翻做 glTF 慣例（V 下，0 喺頂）**；材質 `alphaMode MASK`、`alphaCutoff 0.5`、sampler `NEAREST`（9728）、PNG 內嵌（有 emissive 就加 `emissiveTexture`，emissiveFactor 1——引擎要按 `emissiveLight` 嗰盞燈嘅 intensity 乘，日間＝0；直接丟入 glTF viewer 會見到長開）；footprint 放喺 node `extras`。validator 會讀返 glb 對比 json。
- Three.js 用法：`GLTFLoader` 讀 glb → `texture.magFilter = minFilter = NearestFilter`、`generateMipmaps=false`、`colorSpace=SRGBColorSpace`；或者自己讀 json 砌 `BufferGeometry`（`position`／`normal`／`uv`＋`setIndex`）。

### `objects.json` → `objects[]`
| 欄 | 說明 |
|---|---|
| `id` `type:"mesh"` `zh` | |
| `mesh` `glb` | 路徑（相對場景根 H1/），兩樣內容一樣，揀一樣用 |
| `x` `z` `y` `yawDeg` | 世界擺位（局部原點＝底中）。`y` 只有 `lanterns` 有（吊喺 99） |
| `castShadow` `receiveShadow` | 補位件同串燈唔投影 |
| `layer` | near／mid／far |
| `triangles` | 三角數（同 mesh 一致） |
| `footprint` | **世界座標碰撞**：`{type:"rect", x:[x0,x1], z:[z0,z1], pad}` 或 `{type:"poly", points:[[x,z]…], pad}`。寵物（半徑 `pet.radius`）唔可以入「footprint 外擴 pad＋radius」。串燈（吊）同補位件冇 footprint |
| `emissiveLight` | 有發光貼圖先有：發光強度跟 `lights.json` 呢盞燈（日 0，夜 `intensityNight`） |
| `backfill` | `true`＝擺鏡補位件 |

- 件清單（17 件，總 ≈1100 三角，meshes/ 約 0.5MB）：

| id | 三角 | atlas | 砌法 |
|---|---|---|---|
| tree | 32 | 256² | 樹幹立體盒（樹皮）＋鳥屋擠出＋樹冠前卡（＝原樹冠）＋後卡（鏡像上半，擺鏡見厚度） |
| fence | 206 | 256×128 | 木板／柱像素擠出（厚 3）＋灌木長春藤前後卡 |
| cottage | 84 | 256² | 牆盒＋人字屋頂＋屋簷／簷底＋門窗凹位＋花箱＋煙囪；窗發光（`window`） |
| lanterns | 290 | 128² | 燈籠／燈泡擠出（厚 2–5，發光 `lantern_1`）＋鐵線旗（厚 1）；y 99 |
| bed | 18 | 128² | 木框盒＋泥面頂＋苗卡兩排 |
| lamp | 80 | 64×128 | 按行寬分段擠出；燈頭發光（`lamp`） |
| mushrooms | 92 | 32×64 | 每朵擠出 |
| can | 124 | 64² | 擠出（壺身厚、壺嘴薄） |
| jar | 20 | 32² | 擠出；發光（`jar`） |
| pot_L／pot_R／pot_S | 32 | 32×64／32² | 八角錐台（盆身正投影 uv）＋泥面＋花苗交叉卡；八邊形 footprint |
| bush_bR／bush_bL／bush_bL2／trees_bR／trees_bL | 8 | ≤64² | 屋後／樹後補位（矮樹叢＋遠樹林剪影）交叉卡 |

- **擺鏡補位件**（`backfill:true`）：位置用預覽可見度搜尋揀，**0° 時完全被屋／樹擋住或喺畫面外**（預覽 0° 差異＝0 px），擺到 ±10° 先露出；唔投影、冇 AO、冇 footprint。
- **背景板**（唯一仍然係平面嘅場景件，`type:"backdrop"`）：`bg_sky`（z −470）、`bg_hills`（z −380）。`layer far`、`fixed`、`unlit:true`、`unitsPerPx`＝(鏡頭到板距離)/dist，喺預設鏡頭同 2D 構圖一樣大。
- 光：太陽喺左後上，正面背光由 `lights.json` 嘅 `fill` 補，**唔烘入貼圖**。陰影交引擎 shadow map（預覽用同方向正交 shadow map＋alpha 測試）。

## 寵物（唯一 billboard）`objects.json → pet`
- `{x, z, face:"cyl", billboard:true, radius:10, dir4, shadow}`：面向鏡頭（cyl），用 atlas `pivotPx` 對準 (x,0,z)，1 px＝1 unit，深度同 mesh 一齊比（所以會被樹幹、籬笆遮）。影用軟 blob。
- **4 方向**：`sprites/tuanrong/motion/dir4/atlas_radiant_dir4.png`（＋`_n`、`_emissive`、`.json`）：
  - 64px 格、pivot (32,61)，同 `atlas_radiant` 一致；alpha 0/255；_n 同色圖 alpha 一致（OpenGL 綠＝上）。
  - `front_idle_01–04`（＝現有 idle）、`front_walk_01–06`（新）、`back_idle_01–04`／`back_walk_01–06`（新：冇面、背毛、左右腳對調）、`side_walk_01–06`／`side_idle_01–04`（＝現有 walk／idle，向右）。
  - **向左＝side 幀 scaleX −1**；法線 R 要反（R→255−R）。
  - 揀方向：移動向量 (dx,dz)，|dx|≥|dz| → side（dx<0 鏡像）；dz>0（向鏡頭）→ front；dz<0 → back。停低用該方向 idle。fps：idle 4、walk 10（每 6 幀行 12 units）。

## `lights.json`
- `lights[]`：`id, x, y, z, color #rrggbb, radius, intensity, flicker`。
  - 加咗 `intensityNight`（夜間測試值）同 `zh`。
  - H1 係早晨，2D V3 H1 冇開燈，所以 `intensity` 全部 0；夜景／測試用 `intensityNight`。
  - flicker＝0–1 嘅閃爍幅度（建議 2–4Hz 噪聲）。
  - 燈：lamp ×1、lantern_1…5、window、**window_side**（立體屋右側窗，x 114／y 57／z −72，r 40，intensityNight .7）、jar。
- `sun`：
  - `dir`＝光行進方向（由太陽射向場景，已正規化；左後上方 → [0.42,−0.72,0.55]）。
  - `color`、`intensity`、`ambient{color,intensity}`。
- `fill`（新）：補光方向光 `{dir, color, intensity, intensityNight}`，**唔投影**。dir＝[0.2,−0.12,−0.97]（由鏡頭方向略低照入去），#ffe2c4，日 0.38、夜 0。
  - 用途：補返全部 mesh 背光嘅正面，令 0° 構圖光暗接近平面版。全場景 lit 物件都受。
- 另有 `fog{color,near,far}`、`night{...}`（只係預覽參考）。

## `camera.json`
- `target [0,30,−72]`（令寵物落喺畫面下半）、`pitchDeg 30`、`dist 580`、`fovDeg 40`（垂直）。
- `orbitMinDeg −10` / `orbitMaxDeg 10`（繞 Y 軸，以 target 為心；Octopath 式：pitch 固定 30°，只係輕輕擺）。
- 40° 時，target 處畫面高 ≈422 units，即 2D 美術格高（直版 195×422 嘅比例）。

## 團絨法線 `_n`（放喺色圖隔籬，`pets_normals.json` 有清單）
| 形態 | 色圖 | 法線 |
|---|---|---|
| radiant（標準 64px） | `sprites/tuanrong/motion/atlas_radiant.png` | `atlas_radiant_n.png` |
| sprout（細隻 32px） | `sprites/tuanrong/motion/atlas_sprout.png` | `atlas_sprout_n.png` |
| evo_still_radiant（成年有光環 48px，stage 6） | `sprites/tuanrong/evo6/atlas_evo_still_radiant.png` | `atlas_evo_still_radiant_n.png` |

- Tangent space，**OpenGL（綠＝上）**，RGB＝n×0.5+0.5。alpha 同色圖逐 px 一樣；alpha 0 處 RGB＝(128,128,255)。
- 同色圖共用 atlas json（尺寸、排位、padding／extrude 都一樣）。
  - idle＋walk 逐幀檢查過（validator：每幀頂部 G＞底部 G）。
  - 為咗 alpha 全圖一致，其他 clip 都自動計埋，但未逐幀睇。
  - 面部疊圖、飾品冇做。
- 法線點計：
  - alpha → 每個連通件 4× 距離場做半球高度，加少少亮度起伏，再 gaussian。
  - 求梯度，4×4 平均落返 1x。
- 發光：
  - radiant 新出 `atlas_radiant_emissive.png`（頭頂太陽）。
  - evo_still_radiant 用原有 `atlas_evo_still_radiant_emissive.png`。
  - sprout 冇發光。
- **petGlow 規則照跟**：
  - 寵物 emissive × petGlow：awake 1、sleepy .6、sleep / sleepClip / dreamEnter / dreaming 0。
  - 淡出 600ms easeInQuad；淡入 400ms easeOutQuad＋150ms pulse 1→1.15→1。
  - 場景燈唔受影響。

## 重新生成
```
cd art-pet
PYTHONDONTWRITEBYTECODE=1 python3 tools/build_pet_dir4.py            # 團絨 4 方向 atlas
PYTHONDONTWRITEBYTECODE=1 python3 tools/build_garden3d.py all          # 場景（meshes/*.json＋glb、地面、燈、鏡頭）
PYTHONDONTWRITEBYTECODE=1 python3 tools/validate_garden3d.py [--src 場景目錄]
PYTHONDONTWRITEBYTECODE=1 python3 tools/preview_garden3d.py [--src 場景目錄] [--out 輸出目錄] [--cmp billboard 版場景] [--only …]
```
- env：`GARDEN3D_SRC`、`GARDEN3D_OUT`、`GARDEN3D_CMP`；預設 src＝本目錄，out＝`/workspace/game-design/pilot3d_h1_mesh`。
- preview 出：`pet_walk_loop.gif`（寵物行一圈、按方向換幀）＋`_strip.png`、`assembled_3d.png`（−10°／0°／+10°／夜）、`occlusion_pet_tree.png`（行到樹後被遮）、`compare_billboard_vs_mesh.png`（要 `--cmp`）、`closeup_cottage.png`／`closeup_tree.png`、`meshes_sheet.png`、`backfill_check.png`、`ground_top.png`（footprint＋行路）、`pet_dir4_sheet.png`、`normals_pets.png`。
- 其他工具可以 `import preview_garden3d as P; P.load(src); P.render(yaw, night, W, H, pet=dict(x, z, frame, flip)); P.blocked(x, z)`（唔好複製渲染）。預覽只係驗格式同擺位，**唔係引擎畫面**。
