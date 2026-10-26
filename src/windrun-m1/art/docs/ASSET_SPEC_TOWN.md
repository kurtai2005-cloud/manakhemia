# 資產規格（俾遊程）晨苔鎮 v0.1 — 街角垂直切片
根目錄：`/workspace/game-design/art-wind/`（暫唔入 repo）。補充 `ASSET_SPEC.md`（窄樑貓＋苔坡）。美術風格見 `STYLE_GUIDE_TOWN.md`。
重跑：`cd tools && python3 build_town_palette.py && python3 build_town_tiles.py && python3 build_player.py && python3 build_narrowcat_town48.py && python3 build_town_board.py`（Pillow＋numpy；固定種子，輸出可重現）。
**v0.2 擴充重跑**：`cd tools && python3 build_town_tiles_batch2.py && python3 build_landmarks.py && python3 build_town_map.py && python3 build_town_board_town.py && python3 validate_town.py`（次序固定；`validate_town.py` exit 0＝全過）。

## A. 檔案清單
| 路徑 | 尺寸 | 說明 |
|---|---|---|
| `tiles/morningmoss/tileset_morningmoss.png` | 256x192 | 16x16 tile，16 欄×12 列，158/192 格已用，firstgid=1 |
| `…/tileset_morningmoss.tsj` | — | Tiled 1.10 tileset；逐 tile 屬性 `name/kind/solid/water/seamless`；水有 2 幀動畫（600ms） |
| `…/tileset_morningmoss_extruded.png/.tsj` | 288x216 | margin 1、spacing 2、extrude 1；非整數縮放用 |
| `…/tileset_morningmoss_emissive.png` | 256x192 | 同位置，只含發光像素（窗、燈芯）→ bloom 輸入 |
| `…/tileset_collision.png` | 64x16 | 4 個 collision 語意色塊（編輯器顯示用） |
| `…/tileset_morningmoss_names.json` | — | `{tile_size,columns,firstgid,names[]}`，名→gid＝index+1 |
| `…/tilemap_corner.json` | 20x15 格 | Tiled JSON 示範圖（見 §C）；tileset 內嵌（morningmoss firstgid=1；collision 色塊 firstgid=193），另附外部 `.tsj` 供 Tiled 專案共用 |
| `…/tilemap_corner_1x.png`／`_preview.png`（4x）／`_debug.png` | 320x240／1280x960 | 無後處理預覽／碰撞＋事件疊圖 |
| `sprites/player/frames/player_<dir>_<walk_0..3｜idle>.png` | 32x32 | 20 幀，dir＝down／left／right／up |
| `sprites/player/player_sheet.png`＋`player_atlas.json` | 160x128 | 4 列（down,left,right,up）×5 欄（walk_0..3,idle）；atlas＝frames＋animations＋pivot |
| `sprites/player/player_preview_8x.png`／`player_walk.gif`／`player_contact_sheet.png` | — | 8x 預覽（棋盤底）／4 向走路 GIF／4 向×4 步 8x 無字（相似度檢查） |
| `sprites/narrowcat/town48/frames/spirit_narrowcat_town48_<idle｜walk>_<right｜left>_<NN>.png` | 48x48 | 12 幀（idle 2＋walk 4，左右各一） |
| `…/town48/spirit_narrowcat_town48_sheet.png`＋`_atlas.json` | 192x192 | 4 列（idle_right, walk_right, idle_left, walk_left）×4 欄 |
| `…/town48/*_preview_8x.png`／`_walk.gif` | — | 預覽／走路 GIF |
| `palette/town_palette.json／.png` | — | 環境 32 色＋四時段參數 |
| `tracks/town/style_board_morningmoss_corner.png`（亦複製於根目錄） | 1920x1440 | 主圖 morning（1920x1080）＋下排 dusk／night／無後處理 |
| `tracks/town/style_board_morningmoss_corner_{morning,dusk,night,nopost}.png` | 1920x1088 | 分時段單張（30x17 格視野＝480x272 邏輯×4） |
| `tracks/town/scale_reference.png` | — | 人 32／貓 48／野靈 64／16px 格線 同比例對照（6x） |
| `tools/*.py` | — | `build_town_palette/tiles`、`build_player`、`build_narrowcat_town48`、`build_town_board`；共用 `town_palette`／`pixkit_town`／`town_art`／`charkit` |

## B. 錨點、尺寸、動畫
| 資產 | canvas | pivot（畫布像素，下緣坐標） | 腳底行 | 動畫 |
|---|---|---|---|---|
| 玩家／NPC | 32x32 | **(16,31)** | y=30（y=31 為外框行＝接地線） | walk 4 幀 @8fps loop；idle 1 幀；方向 down/left/right/up |
| town 貓 | 48x48 | **(24,47)** | y=46（y=47 外框行） | walk 4 幀 @8fps；idle 2 幀 @2fps；朝右、left＝鏡像 |
| arena 野靈 | 64x64 | (32,61)（舊） | y=60 | 見 `ASSET_SPEC.md` |
- 引擎放置：sprite 世界座標 ＝ 腳底中心（pivot）；`sort_y ＝ pivot.y`（世界像素）。碰撞盒（人）：腳底中心 12x8（x±6，y−8..0），貓：16x8。
- 動畫 `player_atlas.json.animations`：`walk_<dir>`／`idle_<dir>`（幀名陣列）。`left` 已烘焙，毋須 flipX（想省圖集可只用 right＋flipX）。
- 走路時序：frame0／2＝踏步（身體 −1px、一腿提 2px）；frame1／3＝過渡；移速建議 64 邏輯 px/s（4 tile/s）。貓慢 5–8%，跟隨距離 20–28px，延遲 3–5 幀。

## C. 圖層／z-order／遮擋／碰撞
**地圖**：Tiled JSON（orthogonal、tilewidth/height 16、infinite=false、renderorder right-down）。
| 層 | 類型 | z（低→高） | 備註 |
|---|---|---|---|
| ground | tilelayer | 0 | 地面＋橋 |
| （引擎）投影 | — | 1 | 烘焙剪切投影，見 `STYLE_GUIDE_TOWN` §3-4；可用預烘 shadow 層或執行時生成 |
| deco | tilelayer | 2 | 牆／屋頂／門窗／小物／高物件底座 |
| **entities**（人、貓、NPC） | sprite | 3，**按 sort_y 排序** | 同 sort_y 時：玩家 > NPC > 貓 |
| occlusion | tilelayer | 4 | 樹冠、燈頭、煙囪、告示板頂 |
| 後處理 | — | 5 | 霧、光軸、光圖、bloom、tilt-shift、vignette |
| collision／events | 邏輯，唔渲染 | — | — |
- **collision 值**：0 通行；1 阻擋；2 水（步行者阻擋、可後加游泳）；3 trigger（配合 events）；4 慢速（苔／泥濘）。**高物件**只喺**底座格**設 1（樹幹格、燈柱底、告示板腳），上半（occlusion 層）無碰撞 → 玩家可行到樹冠下。屋：5 行全部 1，門下行（2 格）設 0，並放 warp event。
- **遮擋進階（建議）**：occlusion 層 tile 逐格取 `sort_y`＝同欄向下掃到第一個 collision=1 嘅格，其「底邊」世界 y；實體 `sort_y > tile.sort_y` 時畫喺該 tile 之上（令行去樹／燈後面再行返前面都正確）。最簡版：occlusion 整層永遠畫喺實體之上（板內採用）。
- 水動畫：tsj 內建 2 幀動畫，播放速度 600ms；溝 `ditch_*` 係水＋石邊，橋 `bridge_ns` 2 格寬 collision=0。

**示範圖 20x15 內容**：兩間石屋（青瓦、苔斑、窗、門）、煙囪、南北泥路＋東西街、6x4 石板廣場、小溝＋木橋、柵欄、3 盞路燈、告示板、大／小樹、花、箱／桶／石／灌木。

## D. events 物件層約定（`events`，objectgroup；x/y/width/height 為像素）
| type | name 例 | 自訂屬性 |
|---|---|---|
| `spawn` | `player_start`、`spirit_follow` | `facing`；`spirit`＋`sprite`（`spirit_narrowcat_town48`） |
| `warp` | `door_house_a/b`、`exit_north`、`exit_south_to_arena` | `target`（場景 id）、`entry`、`hint` |
| `interact` | `sign_notice` | `dialog`（節點 id）、`hint` |
| `npc_spawn` | `npc_slot_1..3` | `npc_id`（TBD）、`facing`、`dialog_node` |
| `trigger` | `mist_zone` | `effect=mist`、`strength=0.4`（進入範圍調節霧量） |
- 場景連接：`exit_north → fernshadow_path`、`exit_south_to_arena → returnwind_arena`（占位 id，待遊策確認）。

## E. 命名規範
- 資產檔：`<category>_<name>_<state|dir>_<NN>.png`（全小寫、底線）；野靈 `spirit_<id>_…`；town 變體加 `town48`。
- tile：見 `STYLE_GUIDE_TOWN` §5（`<類>_<變體|mask>`）。4-bit mask 位序：N=1、E=2、S=4、W=8；mask 15＝四面皆同類（內部）。
- 色盤：`palette/town_palette.json`；時段 id：`morning|noon|dusk|night`。

## F. 後處理建議（Pixi/Phaser，對應 `build_town_board.py`）
1. 場景先 render 到 480x270 RT，整數倍 nearest 放大（4x@1080p）；效果喺放大後做（光軸／霧／bloom 要平滑）。
2. **調色**：乘 `TOD[tod].tint×br`；morning 飽和度 0.9；陰影環境色 6% 混入。
3. **光軸**：預烘 1–2 張 shaft 貼圖（斜條、已模糊），加性疊；以 deco+occlusion alpha 做遮罩（或預烘一張遮罩）；0.36×`shaft`；慢速（~6 px/s）漂移＋0.65–1.35 閃爍。
4. **霧**：2 張可平鋪雜訊（橫向拉長），反向慢漂 3／5 px/s，alpha ≤0.6×`mist_amt`，低處（y>28%）漸濃；水溝再加一條橫帶。
5. **光圖**：窗／路燈用預烘徑向貼圖 ADD；窗光溢出下方 26px 地面橢圓；路燈 r≈78px 邏輯。dusk／night 窗瓦片換 `*_lit`（tsj 屬性 `name` 結尾 `_day`→`_lit`）。
6. **bloom**：用 `_emissive.png`＋亮部 >175，兩層模糊（9／26px@4x）加權 0.7／1.0 ×`bloom`；對 sprite 降 30%。
7. **tilt-shift**：對焦帶畫面高度 38–82%，外圍最多 4px 模糊；**vignette** 乘 `vig`。
8. 預算：全部後處理約 6 個全螢幕 pass；低階機可關 tilt-shift＋2 層霧→1 層（`mist_amt`×0.7）。
9. 露珠：晨間草地隨機 70–90 個 2–3px 十字亮點，緩慢閃（不超過 2Hz）；煙囪煙 5 個淡球，向右上飄。

## G. 相似度／來源
全部程式化原創，來源登記見 `ASSET_LOG.md`；玩家剪影（寬簷橙帽＋青披風）上線前需做以圖搜圖（見 LOG 待辦）。

---
# v0.2 擴充（2026-10-26）：batch2 tile ＋ 地標 ＋ 全鎮示範圖 `tilemap_town.json`
**舊檔一律唔改**（`tileset_morningmoss*`、`tilemap_corner*` md5 不變；`validate_town.py` 會驗）。新增全部係獨立 tileset，gid 唔衝突。

## H. 新增檔案清單
| 路徑 | 尺寸 | 說明 |
|---|---|---|
| `tiles/morningmoss/tileset_morningmoss_b2.png/.tsj` | 256x192 | batch2：181／192 格已用（12 列），**firstgid=193** |
| `…/tileset_morningmoss_b2_extruded.png/.tsj` | 288x216 | 同 b2，extruded 版（margin 1／spacing 2／extrude 1） |
| `…/tileset_morningmoss_b2_emissive.png` | 256x192 | b2 發光像素（`*_lit` 窗、燈）→ bloom 輸入 |
| `…/tileset_morningmoss_b2_names.json` | — | `{tile_size,columns,firstgid:193,tilecount,names{name:gid}}`（動畫／日夜表在 tsj 屬性與 `tileset_all_gids.json`） |
| `…/tileset_morningmoss_b2_preview_3x.png` | — | b2 圖集 3x 預覽 |
| `landmarks/tileset_landmarks.png/.tsj`（`_emissive.png`、`_names.json`） | 256x160 | 地標切片：158／160 格，**firstgid=385**；逐 tile 屬性 `landmark/layer(body｜over)/r/c/variant(day｜lit｜both)/anim` |
| `landmarks/landmarks.json` | — | 每個地標：`w,h,origin(格)、body／over 格 gid（day／lit）、collision、events、anim_tiles`；`frame_ms=150`；`swap_day_to_lit` |
| `landmarks/landmarks_atlas.png/.json` | — | 動畫圖集：每地標×day／lit×4 幀（150ms），整幅畫布（供 Phaser/Pixi 直接用 sprite 動畫，毋須逐格 tile 動畫） |
| `landmarks/frames/<id>_<day｜lit>_f<1..4>.png` | 見 json | 24 張單幀 |
| `landmarks/landmarks_preview_3x.png` | — | 3x 預覽 |
| `tiles/morningmoss/tilemap_town.json` | **40x30 格**（640x480） | 全鎮示範圖（見 §J／§K）；4 個 tileset 內嵌：morningmoss=1、b2=193、landmarks=385、**collision=545** |
| `…/tileset_all_gids.json` | — | 合併 gid 表：`tilesets[]`、`names{name:gid}`（497 個）、`swap_day_to_lit{gid:gid}`（22 對） |
| `…/tilemap_town_1x.png`／`_preview.png`（4x）／`_debug.png`（2x＋碰撞／事件疊圖） | 640x480／2560x1920／1280x960 | 無後處理預覽 |
| `tracks/town/style_board_morningmoss_town.png`（morning）／`_night`／`_nopost` | 2560x1920 | 全鎮鳥瞰 style board（HD-2D 後處理模擬） |
| `tools/town_art2.py`、`build_town_tiles_batch2.py` | — | batch2 繪製＋登記＋輸出 |
| `tools/landmark_art.py`、`build_landmarks.py` | — | 地標繪製＋輸出 |
| `tools/build_town_map.py` | — | ASCII 版面 → autotile → `tilemap_town.json`＋預覽（版面可直接改 `ASCII`） |
| `tools/build_town_board_town.py`、`validate_town.py` | — | 全鎮 board；驗證 |

**gid 分段**：`1–192` morningmoss｜`193–384` b2｜`385–544` landmarks｜`545–548` collision（code＝gid−544，即 545＝1 阻擋、546＝2 水、547＝3 trigger、548＝4 慢）。
⚠ **與舊 `tilemap_corner.json` 唔同**：舊圖 collision firstgid=193（因為當時冇 b2）。`tilemap_town.json` 為免衝突改 545；引擎若寫死 193，要改成「由 tmj 內 `tilesets[].name=='collision'` 讀 firstgid」。

## I. 命名＋動畫＋日夜約定
- b2 tile 名：`<類>_<變體|mask|方位>`，同 `STYLE_GUIDE_TOWN` §5。新類：`flagstone_a–d`、`plaza_emblem_{rc}`、`dirt_rut_{h,v}_{a,b}`、`dirt_cobble_{n,e,s,w}`、`path_inner_*`／`cobble_inner_*`、`tf_*`（House B 木框屋：`tf_upper_*`、`tf_lower_*`、`tf_door_{rc}`、`roofb_{top,mid,eave}_{l,m,r}`）、`shop_*`（House C 店舖：`shop_awn_*`、`shop_lower_*`、`shop_door_*`、`shop_win_{l,r}_{top,bot}_{day,lit}`、`shop_sign_hang`）、`stall_{awn,counter}_*`、`well_{rc}`、`hedge_00–15`（4-bit mask）、`steps_stone_*`、`bank_*`、`ramp_*`、`bridge_wood_ns_*`、`ditch_culvert_w`、`pond_inlet_w`、`flowers_*`、`flowerbed_*`、`reeds_*`、`barrel_*`、`crate_*`、`sign_*`、`mailbox_*`、`clothes_*`…（全表見 `_names.json`）。多格物件 `{rc}`＝row/col（`00` 左上）。
- 地標 tile 名：`lm_<landmark>_<body｜over>_<RC>_<day｜lit｜both>[_f1..f4]`；`both`＝日夜相同（md5 去重，同圖只存一格）。
- **動畫 tile 約定**：多幀動畫 tile 名以 `_1`、`_2`（b2：草／蕨／晾衣，450ms）或 `_f1.._f4`（地標：旗／風向標，150ms）結尾；tsj 每格有屬性 `anim`＝去掉幀號的組名，並有 Tiled 原生 `animation:[{tileid,duration}]`（只掛喺第 1 幀）。**地圖內只放第 1 幀 gid**，引擎按 tsj `animation` 播。水（舊圖集）維持 600ms 2 幀。
- **日夜約定**：`*_day` ↔ `*_lit`（亦有 `lantern_top` → `lantern_top_lit`）；對照表 `swap_day_to_lit`（`tileset_all_gids.json`、`landmarks/landmarks.json`；key＝day gid、value＝lit gid）。夜／黃昏載入時對 ground／deco／occlusion 三層逐 gid 查表替換；`*_lit` 帶 tsj 屬性 `emissive=true`、`light=#RRGGBB`，發光像素（l1／l2／frost）另存於 `*_emissive.png` 供 bloom。
- **tile 屬性**（b2）：`name/kind(ground｜wall｜deco｜roof｜water…)/solid/seamless/set/anim/emissive/light/house`。

## J. 地標（`landmarks/`）
| 地標 | canvas（格） | 地圖原點（格） | 內容 | 碰撞 |
|---|---|---|---|---|
| `registry` 報名處 | 6x6 | (28,3) | 青瓦屋頂＋橫條招牌（燈籠）＋旗（第 0 行）＋風向標＋櫃台（條紋簷）入口＋告示板；旗 4 幀（朝東飄）、風向標 4 幀 | 牆／櫃台＝1；門（2 格 @ (30–31,8)）＝0＋warp |
| `arena_gate` 迴風場入口 | 12x7 | (14,2) | 48x48 石拱門樓＋風渦徽章＋雙旗桿（4 幀旗）＋大風向標＋燈座；1 格寬門洞；`lit` 版燈亮 | 兩側柱＝1；門洞 (19,8)＝0＋warp |
| `signpost_arena` 路標 | 1x2 | (18,10) | 木路標：↑迴風場、→報名處 | 底座 (18,11)＝1；上格只 occlusion |
- 每個地標＝**body 層（→ deco）＋over 層（→ occlusion）**；動畫格全部喺 over／body 內以 tsj animation 播放；`landmarks_atlas` 為同一內容嘅整幅 sprite 版（擇一用，唔好重疊）。
- 地標內 `events`（`landmarks.json` 內 `cell` 係地標內相對格）會被 `build_town_map.py` 轉成絕對 `events` 物件（`properties.landmark=<id>`）。
- 旗統一朝東（風向：自西向東），風向標指東。

## K. 全鎮示範圖 `tilemap_town.json`（40x30）
- 圖層同 §C：`ground / deco / collision（visible=false）/ occlusion / events`。**差異**：屋頂放 **occlusion**（`tilemap_corner` 係放 deco），令玩家行到屋後面時被屋頂遮；牆身＋門窗放 deco（全 solid，門下 2 格 collision=0＋warp）。邊界一圈＝`bank_m`（collision 1）；樹冠 occlusion、樹幹 deco（collision 1）。
- 內容：晨苔鎮全貌——**報名處**（東北）、**迴風場入口**（北、石階＋路標）、元老屋（House A，西北）、蕨家（House B，西南）、商店（House C，東南）、7x5 石板廣場（井、花壇長椅、風渦徽章、4 盞路燈）、2 個市集攤（青／紅簷）、告示板、晾衣繩、小溝＋木橋＋水塘、梯台（石階／堤／斜坡）、高草（可行走、2 幀）、籬笆、花、箱桶雜物。南端入口＝玩家出生點。
- **碰撞**：由 ASCII 版面＋地標／建築 footprint 產生；已驗證從 spawn 可走到全部 warp／npc／interact（`validate_town.py`）。
- **events（`events` objectgroup）**：沿 §D，另有擴充：
| type | 本圖 name | 屬性 |
|---|---|---|
| `spawn` | `spawn_start` (20,26)、`spirit_follow` (20,27) | `facing`、`scene_note`；`spirit`、`sprite` |
| `warp` | `door_registry` (30,8)、`door_arena` (19,8)、`ev_town_east` (39,13)、`door_elder`／`door_store`／`door_fernhome`（鎖門） | `target`、`entry`、`hint`；`cond`（條件字串，例 `prologue_done`）；`locked`(bool)；`autosave`(bool)；`landmark`（所屬地標 id） |
| `npc_spawn` | `npc_elder` (21,14)、`npc_fern` (21,10) | `npc_id`、`facing`、`dialog_node`、`radius`（觸發半徑，格） |
| `interact` | `obj_well`、`obj_notice_board`、`obj_sign_east`、`obj_sign_arena`、`registry_counter`、`registry_notice` | `dialog`、`hint` |
| `trigger` | `ev_town_south`、`ev_elder_intro`、`ev_fern_first`、`mist_zone` | `effect`（`push_back`｜`auto_dialog`｜`mist`）；`push_tiles`；`dialog_node`；`cond`；`once`(bool)；`strength` |
| **`light`（新）** | `light_lantern_*`、`light_window_*`、`light_chimney_*`、`light_registry_*`、`light_arena_gate` | `kind`（`lantern｜window｜chimney｜landmark`）、`color`（#RRGGBB）、`radius`（格）、`lit_default`(bool；window) — 供引擎生成光圖；夜間全開 |
  座標 x/y/width/height 為像素（÷16＝格）。`cond` 為簡單布林表達式字串，解析由遊程決定（TBD）。

## L. 後處理補充（全鎮 board）
- `build_town_board_town.py`：同 §F 流程，輸入改為 `tilemap_town.json`；**sprite 上 bloom ×0.70（減 30%）**（以精靈 alpha mask 模糊後乘）；夜景＝對三層 gid 套 `swap_day_to_lit`＋`light` events 當光源（單盞強度 ×0.55，因全鎮燈多；`light_arena_lantern_*` 與路燈重疊，board 內略去）。
- 全鎮 2560x1920 單張後處理約 20 秒（numpy，CPU）；引擎端按 §F 預烘。

## M. 已知限制（v0.2）
- 風車唔做（原版面嘅風車位改成花壇＋長椅院子）；商店移到東南屋、報名處佔東北位（與 `STYLE_GUIDE_TOWN` 版面圖有出入，待遊策確認）。
- 蕨（`fern_*`）葉較疏；House 屋頂 B 型 `roofb_mid_moss_*` 只有 2 款。
- 溝（ditch）係新加（原版面冇）；南邊界用籬笆唔用樹，避免樹冠蓋住溝。
- 高草 2 幀動畫幅度細（避免閃）；風向標／旗同相位（同一組 4 幀）。


## N. NPC（32px）＋對話頭像（M1，v0.1；2026-10-26 遊美）
重跑：`cd tools && python3 build_npc.py && python3 build_portraits.py && python3 validate_npc.py`（exit 0＝全過；固定、可重現，已驗 md5 重跑一致）。
### N.1 人物
| npc_id | 角色 | 輪廓／識別 | 動畫（frames 數） |
|---|---|---|---|
| `npc_elder` | 老鐘（長者，水井旁；對應 `tilemap_town.json` 之 `npc_elder`，`d_elder_hub`） | 矮、駝背、圓形**石帽（頂有苔）**＋白長鬚＋**風標杖**（杖頂風車，旋轉 2 態）；石板藍長袍＋苔綠披肩 | 4 向×（idle 2＋walk 4）＝24 |
| `npc_fern` | 蕨生（對手少年，`npc_fern`，`d_fern_idle`；會巡邏） | **蕨葉髮冠**（寬扇形、剪影最闊）＋海藍頭帶＋玫瑰色圍巾（走路向後飄）＋紫外套、短褲長襪 | 4 向×（idle 2＋walk 4）＝24 |
| `npc_registry` | 報名處職員（櫃台） | **方形海藍制服帽**（風渦徽）＋**金框單片眼鏡**＋玫瑰領帶、風渦臂章；石板藍制服 | 只面向 down：idle 2＋stamp 4（蓋印）＋flip 4（翻簿）＝10 |
- **規格＝玩家**：32x32、pivot **(16,31)**、腳底 y=30、y=31 為外框行；無 AA、alpha 0/255、1px ink 外框、光源左上；色盤＝`wind_palette.SPIRIT` 32 色（與玩家相同；`town_palette` 32 色係環境用，兩盤共用 ink／plum／棕／燈黃等）。實測色數：老鐘 17／蕨生 20／職員 20（≤24）。
- 與玩家區分：玩家＝橙闊邊帽＋青綠披風（寬簷＋右後飄尾）；老鐘＝圓石帽＋白鬚＋高杖；蕨生＝闊扇蕨葉髮；職員＝方帽。`sprites/npc/npc_vs_player.png`（彩色＋純剪影）。
### N.2 檔案／命名
| 路徑 | 內容 |
|---|---|
| `sprites/npc/<npc_id>/frames/<npc_id>_<dir>_<anim>_<n>.png` | 單幀 32x32。`dir`＝down／left／right／up；`anim`＝idle／walk／stamp／flip；`n` 從 0。left＝right 鏡像（已烘焙） |
| `sprites/npc/<npc_id>/atlas_<npc_id>.png／.json` | 圖集（padding 2px、extrude 1px、無重疊）：老鐘／蕨生 138x274（8 列＝idle_down,left,right,up＋walk_×4；4 欄），職員 138x104（3 列＝idle,stamp,flip）。JSON：`meta`（pivot、padding、rows）、`frames{name:{x,y,w,h,pivot}}`、`animations{name:[frame…]}`、`anim_meta{name:{fps,loop,frames}}` |
| `…/<npc_id>_preview_8x.png`、`…_walk.gif`／`npc_registry_anim.gif` | 8x 棋盤底預覽、8x GIF |
| `sprites/npc/npc_contact_sheet.png`、`npc_vs_player.png` | 8x／6x 無字 contact sheet（相似度檢查用）；玩家對照剪影 |
- 動畫名：`idle_<dir>`（2 幀 @2fps loop；呼吸／風標轉）、`walk_<dir>`（4 幀 @8fps loop）；職員 `idle_down`（loop）、`stamp`（4 幀 @6fps，once）、`flip`（4 幀 @6fps，once）。建議職員：idle 為主，每 4–8 秒隨機播 `stamp` 或 `flip` 一次，播完回 idle；玩家走近（radius 內）可改為面向 down 固定 idle。
- 移速：老鐘慢（建議 2.5 tile/s，杖點地節奏＝walk_0/2）；蕨生 4 tile/s（同玩家）。碰撞盒同玩家 12x8。蕨生 walk 向右時圍巾向左飄（4 幀已含）。
- **sort／遮擋**：同 §B（`sort_y＝pivot.y`）。同 sort_y：玩家 > NPC > 貓。
### N.3 頭像
| 路徑 | 內容 |
|---|---|
| `portraits/<npc_id>/<npc_id>_<expr>.png` | 64x64，4 表情 `neutral／happy／worried／surprised`（完成圖） |
| `…/<npc_id>_base.png`＋`overlays/<npc_id>_<expr>_overlay.png` | 無五官底圖＋表情 overlay（眼／眉／口／紅暈／汗珠／驚嘆線）；完成圖＝base 疊 overlay（已驗證逐像素一致） |
| `…/<npc_id>_sheet.png`＋`portrait_atlas_<npc_id>.json` | 256x64 sheet（neutral,happy,worried,surprised）；JSON 有每表情 `x,y,w,h,file,label` |
| `portraits/portraits.json` | 全 NPC 總表（`portraits{npc_id:{name,sheet,atlas,expressions{expr:{file,rect}}}}`） |
| `portraits/portraits_contact_sheet.png` | 5x、無字 |
| `palette/portrait_palette.json／.png` | **48 色**＝SPIRIT 32＋16 頭像專用（皮膚深／淺／暖、苔深／中／亮、玫亮／深、紫深、海深、石板深、金深、眼白、深木、深青、深墨）。實測：老鐘 23／蕨生 26／職員 23 |
- **對話系統引用**：對話節點／行資料用 `{"portrait_id": "npc_fern", "expression": "happy"}`；`portrait_id` ＝ `npc_id`；缺省 `neutral`，未知表情回退 `neutral`。顯示：64x64 整數倍縮放（4x＝256px），nearest；背景透明，襯底由 UI。表情切換可整張換（最簡）或 base＋overlay 疊（省記憶體；兩者結果一致）。
- 表情語意：neutral＝預設；happy＝彎眼笑＋紅暈；worried＝眉內高、眼白可見＋汗珠（右上）；surprised＝大眼、眉高、O 口、金色驚嘆線（左右上）。
### N.4 已知限制（NPC／頭像）
- **老鐘 vs 石伯（已定 2026-10-26）**：npc_elder＝老鐘（第 1 章村長）；`wind-race-modern-plan.md` §6.E／6.F 內「石伯」係第 2 章（石磯港）老領隊；第 1 章村長係「老鐘」。今次依任務將晨苔鎮 `npc_elder` 作「老鐘」出圖（外形通用長者，可改名老鐘而唔洗改圖）。名字／角色歸屬請遊策確認。
- **職員場景**：`tilemap_town.json` 內報名處櫃台 (32,8)／(33,8) 係 collision=1 + interact，**冇 `npc_registry` 的 `npc_spawn`**；職員 sprite 設計為「站喺櫃台後」，需要室內場景 `interior_registry`（未做）或遊策決定站位。全身 sprite 若放喺 deco 層櫃台上，會蓋住櫃台（entities 在 deco 之上）；如要「擋住下半身」，櫃台前緣要放 occlusion 或用引擎裁切（y≥23 不畫）。
- 職員動作用「空中拿印／簿」，**無烘入櫃面／紙**（避免同櫃台 tile 對位）；蓋印落點有 2 粒霜白火花＋玫瑰印痕。
- 蕨生蕨葉髮頂 y=1（外框），走路 bob −1 時貼頂；引擎勿裁切 sprite 頂部。老鐘風標頂 y≈1–3。
- 蕨生／老鐘頭像蕨葉、苔帽為手繪近似；老鐘 up 向（背面）頭部為白髮球，細節簡化。
- 後處理對 NPC sprite 同玩家（bloom ×0.70）；NPC 色盤含白（老鐘鬚）易過曝，建議白鬚 bloom 再降。
