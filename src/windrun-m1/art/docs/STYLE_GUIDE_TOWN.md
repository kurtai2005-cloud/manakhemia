# 《風野競走》晨苔鎮 HD-2D 風格補充 v0.1（遊美）
> 2026-10-26｜M1 冒險切片 週1｜補充 `STYLE_GUIDE.md`（唔取代）｜全原創、全程式化自製（Pillow／numpy；無第三方素材、無 AI 生成圖）
> 風格板：`tracks/town/style_board_morningmoss_corner.png`（晨／黃昏／夜／無後處理）｜重跑：`cd tools && python3 build_town_palette.py && python3 build_town_tiles.py && python3 build_player.py && python3 build_narrowcat_town48.py && python3 build_town_board.py`

## 1. 一句講晒
**夜燈絨毛感嘅清晨版**：同一套像素＋後處理，但將「冷藍夜＋暖燈」換成「**暖金低角度日光＋涼藍陰影＋晨霧＋露珠**」。苔石屋、青瓦、泥路、小溝。硬邊 1px 外框（ink #2B2540，唔用純黑）、無抗鋸齒、3 階 cel；地面細節要「靜」（高頻雜訊細），角色／可互動物件要「醒」（外框＋高明度）。

## 2. 晨苔鎮色盤（≤32 色；`palette/town_palette.json`／`.png`）
> 環境色盤獨立 32 色；人物、野靈仍用 `wind_palette.SPIRIT` 32 色（玩家用 20 色、town 貓 16 色），兩盤共用 ink／plum／棕／燈黃等色，所以同畫面唔會色差。
| 組 | HEX（暗→亮） |
|---|---|
| 墨／深紫 | #2B2540 ink、#4A4066 plum |
| 苔草 | #244F3A、#3E8250、#5AA85E、#8CD27A、#B9EE9A |
| 泥／木 | #5E3F3A、#8A5A44、#B98258、#D9B98C、#F0D6A8 |
| 苔石 | #4F5673、#6B7288、#9AA3B8、#C8D2EE |
| 青瓦屋頂 | #2F5F5C、#477F76、#6A9C92 |
| 水 | #2A5E9A、#4FA3D9、#A6DAF2 |
| 燈／窗光 | #D9692F、#FFC87A、#FFFBD0 |
| 花 | #D9667A、#F28B9B、#FFD45E、#A99BE0 |
| 其他 | #F3F6FF 霜白、#2E8F93 布幡青、#FBEBCB 紙 |
實測：tileset 恰好 32 色（另有 1 格半透明 shadow_soft alpha=80）。

### 2.1 四時段光色（引擎調色參數；同一套圖切換，唔另出貼圖）
| 時段 | 色調乘數 RGB | 亮度 | 日／月光色 | 環境（陰影）色 | 霧色 | bloom | 霧量 | 光軸 | 窗／燈 |
|---|---|---|---|---|---|---|---|---|---|
| **morning**（預設） | 1.07／0.96／0.82 | 1.00 | #FFD08A | #9FC3D6 | #E3EDEA | 0.34 | 0.72 | 0.95 | 窗部分亮（早餐）、燈籠微亮 |
| noon | 1.00／1.00／0.97 | 1.04 | #FFF3D6 | #8FB4E8 | #EAF2F4 | 0.18 | 0.06 | 0.10 | 窗熄 |
| dusk | 1.00／0.76／0.70 | 0.86 | #FFA55C | #7A5FA8 | #E8B8A8 | 0.42 | 0.16 | 0.35 | 窗全亮（換 `window_*_lit`）、燈籠 |
| night | 0.56／0.62／1.00 | 1.02 | #7FA8FF | #1E2347 | #6E80C0 | 0.62 | 0.14 | 0 | 窗全亮、燈籠強 |
另：morning 飽和度 ×0.90（令綠唔過艷）。數值源：`tools/town_palette.py` 嘅 `TOD`，亦寫入 `palette/town_palette.json`。

## 3. 光照規則
1. **晨霧層**：低處濃、高處淡；水溝一帶最濃。2 層橫向拉長嘅雜訊（慢速反向漂移），顏色＝霧色，alpha 上限 ~0.6×霧量。霧要「蓋喺地面同矮物」之上、「高處屋頂／樹冠」只淡淡一層（板內 0.65×）。
2. **穿簷光軸（volumetric shafts）**：低角度日光由**右上→左下**（morning；dusk 反向）。斜條光柱，寬 60–170px（4x 後），向下遞減；**被牆體／屋頂／樹冠遮擋（用 deco+occlusion 嘅剪影做 mask）**，所以光柱先會「穿過屋簷同樹縫」。加性疊加日光色（強度 0.36×光軸量），再模糊 5px＋慢速雜訊閃爍；光柱內放少量塵粒。
3. **窗光／燈光**：窗中心橢圓溢光（r≈46×34 邏輯px）＋窗下方地面溢光（暖橙，貼地橢圓）；路燈 r≈78×66＋貼地光池。morning 只亮標記為 lit 嘅窗（早餐感），dusk／night 全部改用 `*_lit` 瓦片。燈芯亮點交俾 bloom。
4. **投影**：烘焙式「剪切投影」—— 每個 caster（屋／樹／燈柱／告示板）剪影按高度沿 (dx,dy) 倒向地面，只暗化地面，色用環境色。morning dx=-0.62（向左）、dusk dx=+0.85（向右）、night 弱（α 0.18）。角色用橢圓 blob（α≈0.35，寬 ≈ 腳寬）。**人物／野靈 sprite 本身唔畫投影。**
5. **遮擋順序（由下到上）**：`ground` → 投影 → `deco` → **實體（人／貓／NPC，按腳底 y 排序）** → `occlusion`（樹冠、燈頭、煙囪、告示板頂）→ 後處理。高物件拆開：底座入 deco（有 collision），上半入 occlusion，令人行到樹後面先會被樹冠遮到。
6. **後處理次序**（板內實作，引擎照做）：調色→光軸→光圖相加→晨霧→露珠／塵粒→煙囪煙→bloom（亮部 >175、兩層模糊）→tilt-shift（對焦帶＝畫面 y≈60%±22%，外圍模糊 4px）→vignette。
7. **可讀性鐵則**（延續 `STYLE_GUIDE.md` §1）：①玩家永遠係畫面最高對比（橙帽＋青披風，同苔綠／泥／石唔撞色）；②跑道／路面比草更乾淨；③互動物件（門、告示板、燈）有暖色點；④冇文字靠光色提示。

## 4. 尺寸規格
| 項 | 決定 | 理由 |
|---|---|---|
| **tile** | **16x16** | ①玩家 32px＝2 tile 高、town 貓 48px＝3 tile、arena 野靈 64px＝4 tile，**全部係 16 嘅整數倍**，足部同 collision 格天然對齊；②480x270 邏輯畫面（×4＝1080p）有 30x17 格，一個街角有足夠空間；③同 `STYLE_GUIDE` 「場景像素密度＝野靈一半」一致，角色「浮」喺較細緻嘅微縮場景上；④32px tile 會令人物只得 1 tile 高、美術量×4、地圖小一半。 |
| 邏輯解像度 | **480x270**（板為 30x17 格＝480x272，輸出裁 270 或保留 272） | 整數倍：2x=960x540、3x=1440x810、**4x=1920x1080（參考）**、5x=2400x1350。非整數縮放必須用 `tileset_morningmoss_extruded.png`（margin 1／spacing 2／extrude 1）避免 bleeding。 |
| 視角 | 3/4 俯視（輕微正面）；牆面見到 2 行、屋頂 3 行、人物見正面／側面／背面 | 人物 pivot＝腳底。 |
| 人物 | **32x32 canvas**，實身 ≈ 28 高（帽頂 y=2，腳底行 y=30），頭 ≈ 10 寬；**pivot (16,31)**＝腳底接地線 | 同 64px 野靈 pivot (32,61) 同語意。 |
| 野靈（town） | **48x48**（town 跟隨）；**64x64**（賽道 arena，沿用現有 20 幀） | 48：實身約 30x28，約 1.7 tile 寬，細過／近似人高，跟喺玩家後面唔搶畫面，4x 後 192px；64：arena 要表情／技能光環，細節多。**town 用 48、arena 用 64，兩者各自獨立資產。** pivot：48→(24,47)、64→(32,61)。 |
| 頭像 | **64x64**（對話框用，每人 4 表情＝256x64 sheet） | 見 §7。 |

## 5. Tileset／圖集規格（Tiled-JSON 友好）
- 圖集 `tileset_morningmoss.png`：**256x192、16 欄×12 列＝192 格（已用 158）**，firstgid=1，無 margin／spacing；`tileset_morningmoss.tsj`（Tiled 1.10）逐 tile 有自訂屬性：`name`、`kind`（ground／deco／occlusion）、`solid`（0/1/2）、`water`、`seamless`；水 4 格有 2 幀動畫（600ms）。
- 衍生：`_emissive.png`（同位置，只含光源像素，供 bloom）、`_extruded.png`（288x216，margin 1／spacing 2／extrude 1，配 `_extruded.tsj`）、`tileset_collision.png`（64x16，4 個語意色塊）、`_names.json`（名→索引）。
- **命名**：`<類>_<變體|方位mask>`，全小寫英文＋底線。自動接邊 tile 用 **4-bit mask（N=1 E=2 S=4 W=8）**：`path_00..15`（泥路接草）、`cobble_edge_00..15`、`ditch_00..15`（水溝）、`pond_00..15`。例：`path_05`＝南北直路。建築：`roof_top|mid|eave_{l,m,r}`、`wall_upper|lower[_l|_r][_b]`、`window_{a,b}_{day,lit}`、`door_{00,01,10,11}`（2x2）。高物件：`tree_big_{行}{列}`（3x4）、`tree_small_*`（2x3）、`lantern_{top,mid,base}`、`board_{tl,tr,bl,br}`、`chimney_{top,base}`。
- **無縫地面**：`grass_a..d`、`dirt_a/b`、`cobble_a..d`、`water_a1/a2/b1/b2`（x、y 皆可平鋪；亂數變體用坐標 hash 揀，避免重複感）。
- **圖層約定（Tiled JSON，20x15 示範 `tilemap_corner.json`）**
  | 層 | 類型 | 內容 | 渲染 |
  |---|---|---|---|
  | `ground` | tilelayer | 草／泥／石／水／橋 | 實體之下 |
  | `deco` | tilelayer | 牆、屋頂、門窗、小物、高物件底座、花 | 實體之下 |
  | `collision` | tilelayer（`role=logic`，唔渲染） | 0 通行｜1 阻擋｜2 水（步行者阻擋）｜3 trigger｜4 慢速 | 邏輯 |
  | `occlusion` | tilelayer | 樹冠、燈頭、煙囪、告示板頂 | **實體之上** |
  | `events` | objectgroup | `spawn`／`warp`／`interact`／`npc_spawn`／`trigger`，自訂屬性見 `ASSET_SPEC_TOWN.md` §D | 邏輯 |
  地圖屬性：`scene`、`tod_default=morning`、`reference_scale=4`、`y_sort_entities=true`。

## 6. 人物（玩家＋NPC 共用規格）
- 32x32、**4 向（down／left／right／up）× 4 步行 ＋ 1 idle**；`left` 係 `right` 水平鏡像（已烘焙成獨立幀，亦可用 flipX）。walk 8fps（一個週期 0.5s≈2 tile，建議移速 4 tile/s＝64 邏輯 px/s）；idle 1 幀（引擎可加 1px 呼吸）。
- **玩家（原創）**：**寬簷橙帽＋青綠披風**＝遠望剪影（帽簷比身闊、披風側面拖尾）；深紫發、奶色束腰上衣、藍灰褲、棕靴；帽帶後插一根黃羽。唔似任何現有 IP 主角（無鴨舌帽、無紅白、無頭巾）。
- NPC 同規格：`tools/charkit.py` 嘅 `render_char(spec, dir, phase)` 以 7 組色階（hat／hair／cape／tunic／pants／boots／skin）參數化，換色＋換帽型即成新 NPC，仍用 SPIRIT 色盤。
- 規則：外框 ink；光源左上；高光偏暖、陰影偏紫；每人 ≤24 色。

## 7. 頭像尺寸（建議 **64x64**）
- 對話框係 480x270 邏輯畫面入面，64px＝畫面高 24%，4x 後 256px，夠睇表情而唔霸佔畫面；96px＝35% 畫面高，對話框要放大、遮住場景。
- 64＝32px 人物 ×2，風格（外框 1px、3 階 cel）直接沿用；每個表情筆畫量約 96 版嘅 44%，3 個 NPC×4 表情仍可控。
- 每人 sheet 256x64（normal／smile／surprise／worry）；色盤同人物，≤24 色；背景透明；對話框襯底由 UI 負責。

## 8. 野靈 48 vs 64 用法
- **48x48：town 跟隨**（`sprites/narrowcat/town48/`）：idle 2、walk 4，朝右、左右鏡像；上下行走沿用側面（3/4 俯視下可接受，若要 4 向另計）。跟隨距離 ≈ 玩家身後 20–28px、延遲 3–5 幀。
- **64x64：賽道 arena**：現有 `sprites/narrowcat/` 20 幀（run/idle/skill/win/lose）。
- 兩者共用同一 SPIRIT 色盤、同一造型語言（石板藍毛、青風巾、條紋、奶色爪）；town48 係**幾何重畫**（唔係位圖縮小）所以線條乾淨。

## 9. 已知取捨
- 側面行走嘅腿／披風喺 8x 下略忙，1x–4x 閱讀正常；
- town48 貓喺晨間 bloom 下毛色偏白，建議 bloom 對 sprite 降 30%；
- 大型地標（例如登記處）如需多於 32 色，要擴充環境色盤，請先同遊美確認。
