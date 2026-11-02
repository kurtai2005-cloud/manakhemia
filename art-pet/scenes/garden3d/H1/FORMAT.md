# 3D 花園試點 H1 — 格式（方案 C，Three.js）

由 `tools/build_garden3d.py all` 生成，`tools/validate_garden3d.py` 驗證，`tools/preview_garden3d.py` 出預覽（`/workspace/game-design/pilot3d_h1/`）。
來源係 H1 V3 程序化花園（`build_garden_hd2d_v3.build_index_v3('H1')`）：每件物件**逐件重畫**抽出，所以冇遮擋穿窿，背後亦冇草。全部程序化（numpy／Pillow），冇用 AI 圖。

## 座標同單位
- **1 unit＝1 個 1x 美術 px**。Y 向上，地面喺 XZ 平面。
- 原點＝寵物預設企位（2D 腳底 art (97,292)）。+X 向右，+Z 向鏡頭。
- 由 2D 搬過嚟嘅規則：
  - x＝art x − 97。
  - 前排物件：z＝(art y − 292) × 1.6。
  - 後排（籬笆、屋、樹、串燈）手擺 z −44…−52，保留 2D 前後次序：樹喺籬笆前，屋喺籬笆前。

## 地面 `ground/`
- `ground.png` 256×256，`ground@3x.png` 768×768（最近鄰 ×3）。PNG sRGB，純俯視，**冇光影**。
  - 覆蓋 x、z 各 −128…+128，以原點為中心。
  - UV：u＝(x+128)/256，v＝(z+128)/256。圖頂＝z −128（遠，即屋同籬笆嗰邊）。
- `ground_ao.png` / `ground_ao@3x.png`：灰階 L，同尺寸，255＝冇遮蔽。內容有：
  - 物件接地 AO：cyl 件係橢圓；fixed 件係沿板底一條帶。
  - 踏腳石邊、舞台邊石。
  - 用法：乘落地面 albedo。動態影仍然由引擎出。
- `ground_tile.png` 64×64（@3x 192）：**外圍草地 tile**。
  - pitch 30° 嘅直版畫面喺地上大約望到 −1250…+240 咁深，256 片唔夠，外圍要用 tile 鋪。
  - 以 (−128,−128) 對齊，每 64 units 鋪一格。
  - 256 片嘅底色本身就係呢個 tile ×4，近邊 6–20 units 冇點綴，所以接位無縫（validator 有驗）。
  - 建議外圍平面至少：x ±640、z −480…+320。
- 地面貼花（唔做 billboard）：
  - 踏腳石 3 塊、舞台淺草圈＋苔窩＋邊石、小路（舞台去門口）。
  - 菜畦泥面、門口石板、樹頭苔、籬笆底深草帶。
  - 三葉草、小花、細石。

## Billboard `objects/` 同 `objects.json`
- 每件 1x `id.png`＋`id@3x.png`（最近鄰 ×3）。RGBA，alpha 只有 0/255，透明處 RGB＝0，**冇地面陰影**。
- 已套 V3 H1 調色：飽和 1.12、對比 1.08、split-tone，即係「日間 V3 色」，冇烘任何方向光。**引擎唔好再疊同一個 V3 LUT。**
- 發光另交 `id_emissive.png`（同尺寸，@3x 亦有）。RGB＝燈色，alpha＝發光遮罩，一定喺本體 alpha 之內。
  - 強度用 `emissiveLight` 指向 `lights.json` 對應燈嘅 intensity（日間 0，夜間 `intensityNight`）。
- `objects.json` → `objects[]` 欄位：

| 欄 | 說明 |
|---|---|
| `id` `file` `file3x` | 必有 |
| `x` `z` | 接地點世界座標（units） |
| `y` | 選填（我加嘅），離地高。只有 `lanterns` 串燈係吊喺半空，y＝99 |
| `w` `h` | units；一般件＝1x px 尺寸 |
| `pivot` | [px, py]，0–1，由圖左上計；[0.5,1]＝底中。樹、燈柱、花灑嘅接地點唔喺 bbox 中間，所以 px≠0.5；籬笆底有灌木垂落地面以下，所以 py＜1 |
| `face` | `cyl`＝繞 Y 轉向鏡頭；`fixed`＝固定，用 `yawDeg`（0＝面向 +Z） |
| `shadow` | 投唔投影 |
| `layer` | `near` / `mid` / `far` |
| `emissive` `emissive3x` `emissiveLight` | 有發光先有 |
| `zh` `srcArt` | 備註（中文名、原 2D art 座標） |

- 件數：
  - tree（連鳥屋、垂藤）、fence（籬笆＋灌木＋長春藤）、cottage（連窗台花箱，窗會發光）。
  - lanterns（旗串燈籠＋小燈泡，發光）、bed（菜畦木框＋苗；泥面喺地面）。
  - lamp（發光）、pot_L、pot_R、pot_S、mushrooms、can、jar（螢火瓶，發光）。
- 背景板 `backdrop/`：`bg_sky`（z −470）、`bg_hills`（z −380；遠山＋遠樹＋遠屋，上面透明）。
  - `layer far`、`fixed`、`unlit:true`，企喺地上（pivot 底中，y＝0）。
  - `unitsPerPx`＝(鏡頭到板距離)/dist。咁樣喺預設鏡頭，板嘅大細同 2D 構圖一致。
  - 圖係原 V3 sky/far 加闊（左右各鏡像一格，旁邊兩格抹走太陽）。1x 1053×274 / 1053×57 px，@3x ×3。
  - 因為 pitch 30° 向下望，畫面只見到地平線附近嘅天，**太陽唔入鏡**，太陽感覺靠 `sun` 光。
- `pet`：寵物用 atlas 嘅 pivotPx 對準 (0,0,0)，`cyl`，`shadow:true`。

## `lights.json`
- `lights[]`：`id, x, y, z, color #rrggbb, radius, intensity, flicker`。
  - 加咗 `intensityNight`（夜間測試值）同 `zh`。
  - H1 係早晨，2D V3 H1 冇開燈，所以 `intensity` 全部 0；夜景／測試用 `intensityNight`。
  - flicker＝0–1 嘅閃爍幅度（建議 2–4Hz 噪聲）。
  - 燈：lamp ×1、lantern_1…5、window、jar。
- `sun`：
  - `dir`＝光行進方向（由太陽射向場景，已正規化；左後上方 → [0.42,−0.72,0.55]）。
  - `color`、`intensity`、`ambient{color,intensity}`。
- 另有 `fog{color,near,far}`、`night{...}`（只係預覽參考）。

## `camera.json`
- `target [0,30,−72]`（令寵物落喺畫面下半）、`pitchDeg 30`、`dist 580`、`fovDeg 40`（垂直）。
- `orbitMinDeg −30` / `orbitMaxDeg 30`（繞 Y 軸，以 target 為心）。
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
PYTHONDONTWRITEBYTECODE=1 python3 tools/build_garden3d.py all
PYTHONDONTWRITEBYTECODE=1 python3 tools/validate_garden3d.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/preview_garden3d.py
```
