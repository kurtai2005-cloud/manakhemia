# 地圖草圖與事件點（M1：晨苔鎮／迴風場／蕨影小徑）

> 遊策｜週 1｜草稿 v1.1（晨苔鎮已同步遊美實作圖 `art-wind/tiles/morningmoss/tilemap_town.json`，**晨苔鎮以該 JSON 為準**；迴風場、蕨影小徑仍為暫定草圖）｜給：遊程（地圖載入／事件）、遊美（圖塊／美術範圍）、遊測（路徑測試）
> 格仔 = 16 px 圖塊；座標 `(x,y)` 以左上為 `(0,0)`，x 向右、y 向下。ASCII 只表示**碰撞／事件／大概佈局**，唔代表最終美術。

## 1. 圖例（三張圖共用）

| 符號 | 意思 | 碰撞 | 備註 |
|---|---|---|---|
| `#` | 邊界／岩壁／室內牆 | ✔ | |
| `Y` | 樹（樹幹格） | ✔ | 樹冠畫喺**上方 1–2 格**嘅遮擋層（唔碰撞），角色行近樹後會被樹冠遮住 |
| `B` | 建築（牆＋屋頂） | ✔ | 屋頂畫入遮擋層；按底線 y-sort |
| `D` | 門／入口 | 事件（門下格可行走＋傳送） | 見事件表（M1 可入：迴風場門、報名處門；其餘鎖門） |
| `W` | 水井（2×2） | ✔ | 可互動 |
| `~` | 水面 | ✔ | 池塘；岸邊加水光動畫 |
| `=` | 石徑／泥徑／隧道地面 | ✘ | 腳步音按地面物料（見 cue-table.md） |
| `.` | 草地／空地／室內地板 | ✘ | |
| `,` | 苔叢／蕨叢（高草） | ✘ | 可行走；上半部入遮擋層（蕨影效果），可加輕微搖曳 |
| `C` | 報名櫃台 | ✔ | 職員站喺櫃台後 |
| `b` | 長凳／看台座位 | ✔ | |
| `G` | 入場閘口 | 條件 | 未報名＝碰撞；已報名＝開放（見 `ev_gate_entry`） |
| `S` | 起跑線（觸發線） | 事件 | 6 格高 |
| `F` | 佈陣點 | 事件 | |
| `P` | 玩家出生點 | — | |
| `E` | 場景出口（傳送觸發） | 事件 | |
| `x` | 倒塌樹幹路障 | ✔ | M2 才移除 |
| `s` | 告示牌 | ✔ | 可互動 |
| `n` | 告示板 | ✔ | M3 每日賽事入口（M1 只顯示文字） |
| `i` | 情報位 | ✔ | M2／M3 偵察入口（M1 佔位） |
| `r` | 報名互動格 | 事件 | 玩家站呢格同桑姨對話 |
| `1` `2` `3` | NPC：老鐘／蕨生／桑姨 | ✔ | 站位＝初始位置 |
| `o` | 對手站位（賽前）；晨苔鎮圖內＝小物件（花壇、灑水壺、箱、桶、灌木、郵箱等） | ✔ | 晨苔鎮用法見第 2 節；無事件 |
| `*` | 野生野靈（可見） | ✔ | 互動觸發結緣賽 |
| `H` | 木橋（晨苔鎮南溝，3 格闊） | ✘ | 新增地物：溝＋木橋（見第 2 節） |
| `f` | 籬笆／樹籬／矮牆 | ✔ | |
| `l` | 燈柱底座 | ✔ | 燈頭在上方 2 格（`light` 事件、occlusion 層） |
| `T` | 市集攤檔 | ✔ | |
| `m` | 慢速斜坡（collision=4） | ✘ | 移動速度降低 |
| `V` | 南邊推回觸發格（collision=3） | 事件 | `ev_town_south` |

## 2. 場景一：晨苔鎮 `town_morningmoss`（40×30 圖塊）

> **來源**：遊美 `art-wind/tiles/morningmoss/tilemap_town.json`（Tiled，16 px，圖層 `ground／deco／collision／occlusion／events`，events 共 40 個，其中 20 個為 `light`）。ASCII 由 `collision`＋`deco` 名稱＋events 重新整理，**與 JSON 衝突時以 JSON 為準**。遊策 v1 舊版（風車、雜貨舖在東北、`door_house`）已取代。
> 預設時段 `morning`；全圖 `mist_zone` 霧（見事件表）。

```
    0         1         2         3         
    0123456789012345678901234567890123456789
 0  ########################################
 1  #YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY#
 2  #YY..................................YY#
 3  #YY.BBBBBB....BBBBBBBBBBBB...........YY#
 4  #YY.BBBBBB....BBBBBBBBBBBB..BBBBBB...YY#
 5  #YY.BBBBBB....BBBBBBBBBBBB..BBBBBB...YY#
 6  #YY.BBBBBBooo.BBBBBBBBBBBB..BBBBBB...YY#
 7  #YY.BBBBBB.bb.BBBBBBBBBBBB..BBBBBB...YY#
 8  #YY.BBDDBBo..oBBBBBDBBBBBB..BBDDCn...YY#
 9  #YY.ff=off........l===l.....ff==.fff.YY#
10  #YY...=........o...==2........=....o.YY#
11  #YY...=.....,.....s===....,,.........YY#
12  #YY...=.nnooTTT..l=====l..TTTo......sYY#
13  #YY...===========bboo=bb===============E
14  #YY...============oWW1=================E
15  #YY...=..........=======...............#
16  #YY...=.....YY...l=====l..........,,...#
17  #YY...=............===....YY......o..YY#
18  #YY.BBBBBB.........===........BBBBBB.YY#
19  #YY.BBBBBB.....,,..===........BBBBBB.YY#
20  #YY.BBBBBB.oo..o...===.#bb..omBBBBBB.YY#
21  #YY.BBBBBBo........===.#..o..mBBBBBB.YY#
22  #YY.BBDDBB.o..o....===.#==####BBDDBBoYY#
23  #YY.ff=off.........===.......off=.ff.YY#
24  #YY...=............===..........=....YY#
25  #YY...===========================....YY#
26  #YY.........,......=P=..~~~~~~~~~~~~.YY#
27  #YY~~~~~~~~~~~~~~~~HHH~~~~~~~~~~~~~~.YY#
28  #YYffffffffffffffff===fffffffffffffffYY#
29  ###################VVV##################
```

**碰撞值（JSON `collision` 層，code＝gid−544）**：0 通行｜1 阻擋｜2 水（步行者阻擋）｜3 trigger（配合 events）｜4 慢速。晨苔鎮用到：水＝南溝＋水塘；trigger＝東出口 (39,13–14)、南邊 (19–21,29)；慢速＝斜坡 (29,20–21)。

**佈局要點（以 JSON 為準）**
- 玩家由**南門外路**（出生 `P` (20,26)，面向北；跟隨野靈位 (20,27)）北行，過南溝木橋 `H` (19–21,27)，沿主路行到廣場（17–23, 12–16，7×5 石板、風渦徽章）；水井 `W` (19–20,13–14)，老鐘 `1` 企喺井東 (21,14)，**一眼睇到**。
- 北面（由西至東）：**老鐘屋（House A，村長家）** (4–9, 3–8)，門 (6–7,8)，鎖；**迴風場正面（門樓）** (14–25, 3–8)，門洞 (19,8) 1 格闊，兩旁旗桿＋燈籠；**報名處** (28–33, 3–8)，**東北**，門 (30–31,8)，櫃台 `C` (32,8)、告示 `n` (33,8)。
- 南面：**蕨生家（House B）** (4–9, 18–22)，門 (6–7,22)，鎖；**商店（House C）** (30–35, 18–22)，**東南**，門 (32–33,22)，鎖（M2 開放）。
- 兩條街：南北主路 x 19–21；東西街 y 13–14。市集攤檔 `T`：(12–14,12)、(26–28,12)。告示板 `n` (8–9,12)；路標 `s` (18,11)（迴風場↑／報名處→）；東路標 `s` (36,12)。
- **花壇＋長椅（取代舊風車位）**：舊風車位 (11–12,6–7) 現為花壇 (11–12,6)＋長椅 (11–12,7)＋灑水壺 (10,6)，**無事件**。另有**東南院子** (23–29, 20–22)：長椅 (24–25,20)、花壇 (28,20)、石階入口 (24–25,22)、斜坡 (29,20–21)＝慢速；**無事件**。
- **新增：溝＋木橋＋水塘**：南溝 y=27（x 3–18、22–35）與水塘 (24–35, 26–27)，皆阻擋；木橋 (19–21,27) 係通往南門唯一通道。南邊界 y=28 為籬笆（唔用樹，避免樹冠蓋住溝）。
- 東出口 `E` (39,13–14) 通蕨影小徑。
- 北面背巷 y=2（x 3–36）保留作 y-sort 示範（人物行過建築後面會被屋頂遮住）；M1 無事件。**M1 唔做風車**：舊 `M` 物件、`obj_windmill`、`windmill_rpm` 全部移除／標為 M2+（序章改以迴風場門樓旗表現「風弱」，見 prologue-script.md）。

**事件點（town_morningmoss；位置＝格 `(x,y)` 左上，`w×h` 為格數）**

| id | 位置 | JSON 類型 → 觸發 | 條件 | 動作 | M |
|---|---|---|---|---|---|
| `spawn_start` | (20,26) | spawn | 新遊戲 | 面向北；序章鏡頭由南門慢推；教學提示「點地面移動」 | M1 |
| `spirit_follow` | (20,27) | spawn（跟隨） | — | **定案**：`got_mochi` 後才生成，物種＝隊首野靈（序章後＝苔團）。JSON 內 `narrowcat`／`spirit_narrowcat_town48` 只係遊美示範佔位，引擎唔照用 | M1 |
| `ev_town_south` | (19,29) 3×1 | trigger（`push_back`，`push_tiles=2`） | 任何 | 提示氣泡「來時路，唔回頭」，推返 2 格 | M1 |
| `ev_elder_intro` | (17,12) 7×5 | trigger（`auto_dialog`，`once`） | `not prologue_done` | 起動 `d_elder_intro`（序章，見 prologue-script.md） | M1 |
| `npc_elder` | (21,14)，半徑 1.5 | npc_spawn（面向下） | 按 flags 選對話 | `d_elder_hub`（見 npc-dialogue.md） | M1 |
| `ev_fern_first` | (17,9) 7×3 | trigger（`auto_dialog`，`once`） | `prologue_done` 且 `not met_fern` | 起動 `d_fern_first`；蕨生由 (21,10) 轉身 | M1 |
| `npc_fern` | (21,10)，半徑 **1.0** | npc_spawn（面向下） | — | `d_fern_idle`（JSON 預設節點）；flag `c1r1_won` 後改為 `d_fern_after_r1` | M1 |
| `door_arena` | (19,8) 1×1 | warp → `arena_windrun`，entry `spawn_from_town` | `prologue_done` | 傳送至賽場大廳 (6,13)；否則氣泡「先同老鐘傾下偈」。JSON `hint`＝「迴風場」（地標 `arena_gate`） | M1 |
| `door_registry` | (30,8) 2×1（x 30–31） | warp → `interior_registry`，entry `door` | — | **報名處**，可入。**定案**：`interior_registry`＝`arena_windrun` 入口大廳（同一室內，唔另做室內圖）；entry `door`＝`spawn_from_town` (6,13)。JSON `hint`＝「報名處」（地標 `registry`） | M1 |
| `registry_counter` | (32,8) | interact（`dialog=registry_counter_01`） | — | 旁白 `registry_counter_01`（見 npc-dialogue.md §4） | M1 |
| `registry_notice` | (33,8) | interact（`dialog=registry_notice_01`） | — | 旁白 `registry_notice_01`（見 npc-dialogue.md §4） | M1 |
| `door_elder` | (6,8) 2×1 | warp，`locked` | — | 老鐘屋門；氣泡「鎖咗門」 | M1 |
| `door_fernhome` | (6,22) 2×1 | warp，`locked` | — | 氣泡「鎖咗門」 | M1 |
| `door_store` | (32,22) 2×1 | warp，`locked` | — | 氣泡「鎖咗門（M2 開放）」；M2 起商店開放 | M1／M2 |
| `obj_well` | (19,13) 2×2 | interact（`obj_well_01`） | — | 旁白 `obj_well_01`（見 npc-dialogue.md §4） | M1 |
| `obj_notice_board` | (8,12) 2×1 | interact（`obj_notice_board_01`） | — | 旁白 `obj_notice_board_01`（見 npc-dialogue.md §4）；M3 改為每日賽事入口 | M1／M3 |
| `obj_sign_arena` | (18,11) | interact（`sign_arena_01`） | — | 旁白 `sign_arena_01`（見 npc-dialogue.md §4）：路標「迴風場 ↑／報名處 →」 | M1 |
| `obj_sign_east` | (36,12) | interact（`obj_sign_east_01`） | — | 旁白 `obj_sign_east_01`（見 npc-dialogue.md §4）：「東：蕨影小徑 → 石磯港」 | M1 |
| `ev_town_east` | (39,13) 1×2 | warp → `trail_fernshadow`，entry `west`，`autosave` | `prologue_done` | 傳送至小徑西端 (1,7)；自動存檔 | M1 |
| `mist_zone` | (0,15) 40×15 | trigger（`mist`，`strength=0.35`） | — | 純視覺：下半鎮薄霧（低處較濃）；唔影響操作 | M1 |
| `light_*`（20 個） | 見 JSON | light | — | HD-2D 光點：路燈 `lantern`×6（(17,10)(23,10)(17,14)(23,14)(18,7)(22,7)）、窗 `window`×8、煙囪 `chimney` (8,2)、地標光×5（報名處招牌 (29,7)、報名處燈 (32,7)、迴風場門 (19,8)、迴風場門燈 (17,7)(21,7)）；窗有 `lit_default`；夜間全開 | M1 |

> 刪除（相對 v1）：`obj_windmill`、`door_house`（舊 (32,22) 民居門，現為商店門 `door_store`）；舊 `door_store`（(30,8) 雜貨舖）現為 `door_registry`。

**NPC 站位／行為（M1）**：老鐘 (21,14)、蕨生 (21,10) 原地待機（轉向面向玩家）；M2 起加巡邏路線（用同一套事件資料）；路人 M1 唔做。

**報名處入口（定案）**：晨苔鎮 `door_registry`（JSON 目標 `interior_registry`）與 `door_arena` 進入**同一個**室內場景＝`arena_windrun` 入口大廳（桑姨 `npc_sang`、報名流程不變，見第 3 節），唔另做室內圖。載入器把 `interior_registry` 視為 `arena_windrun` 別名，entry `door`＝`spawn_from_town` (6,13)（兩個入口同一出生點）。兩道門傳送時各設一次 flag `last_town_door`（`door_arena`／`door_registry`）；賽場 `door_town` 按它返回：`door_arena`→晨苔鎮 (20,9)；`door_registry`→晨苔鎮 (30,9)。（JSON 內 `interior_registry`／`door` 字樣可留待遊美下次更新時改為 `arena_windrun`／`spawn_from_town`，唔影響實作。）

## 3. 場景二：迴風場 `arena_windrun`（40×15 圖塊）

```
    0         1         2         3         
    0123456789012345678901234567890123456789
 0  ########################################
 1  ########################################
 2  #............########..................#
 3  #.....3......########..................#
 4  #..CCCCCCC...########.bbbbb............#
 5  #..i..r....n.########.............S....#
 6  #............########.i...........S....#
 7  #............G=======.............S.o..#
 8  #............G=======...F.........S....#
 9  #............G=======.............S....#
10  #............########.............S....#
11  #..bb.....bb.########.bbbbb...2........#
12  #............########..................#
13  #............########..................#
14  ######D#################################
```

**空間流程**（對應賽前流程 ①②④⑤）：
`大廳報名處 (6,5) → 入場閘口 G (13,7–9) → 入場通道 (14–20,7–9) → 看台／佈陣 F (24,8) → 起跑區 → 起跑線 S (34,5–10)`

| 區域 | 範圍 | 說明 |
|---|---|---|
| 入口大廳（報名處；晨苔鎮 `door_arena`、`door_registry` 兩個入口共用同一大廳） | (1–12, 2–13) | 桑姨 `3` 喺櫃台 `C`（3–9, 4）**後方** (6,3)；玩家喺櫃台**前方**互動格 `r` (6,5) 同佢對話 |
| 入場通道 | (14–20, 7–9) | 3 格闊；閘口 `G` 喺大廳東牆 (13,7–9) |
| 看台 | (21–27, 2–13) | 兩排長凳（y=4、y=11）；佈陣點 `F` (24,8)；情報位 `i` (22,6)（M3 偵察佔位） |
| 起跑區 | (28–38, 2–13) | 起跑線 `S` x=34、y=5–10；對手站位 `o` (36,7)；蕨生旁觀位 `2` (30,11) |

**事件點（arena_windrun）**

| id | 位置 | 類型／觸發 | 條件 | 動作 | M |
|---|---|---|---|---|---|
| `spawn_from_town` | (6,13) | 出生（entry `spawn_from_town`／`door` 同點） | 由 `door_arena` 或 `door_registry`（晨苔鎮） | 鏡頭定喺大廳；BGM 保持城鎮 BGM | M1 |
| `door_town` | (6,14) | touch | — | 傳送 → `town_morningmoss`：按 `last_town_door`＝`door_arena` → (20,9)；`door_registry` → (30,9)（見第 2 節「報名處入口」）；自動存檔 | M1 |
| `npc_sang` | (6,3)，互動格 `r` (6,5) | interact | 按 flags | `d_sang_hub`（報名／資格／說明，見 npc-dialogue.md） | M1 |
| `obj_board_daily` | (11,5) | interact | — | M1：「每日賽事：暫未開放」；M3 起每日賽事入口 | M1／M3 |
| `obj_scout_hall` ／ `obj_scout_stand` | (3,5)／(22,6) | interact | — | M1 提示「情報位暫未開放」；M3 偵察 UI | M1／M3 |
| `ev_gate_entry` | 閘口 (13,7–9) | touch | `registered_match` 有值 | 閘口打開 → 入場演出 `cue_entry_tunnel`（可跳過）；否則氣泡「未報名」並提示去桑姨 | M1 |
| `ev_stand_intro` | 區域 (21–27,2–13) | auto（每場首次進入） | `registered_match` | 隊伍介紹 ≤5 秒（`cue_team_intro`，可跳過） | M1 |
| `ev_formation` | `F` (24,8) | interact | `registered_match` | 開佈陣介面（首發＋後備排序）；完成後 `formation_done=true` | M1 |
| `ev_fern_prematch` | 區域 (28–32,9–13) | auto（首次） | `registered_match=c1_r1` 且 `not seen_fern_prematch` | `d_fern_prematch`（蕨生喺旁觀位） | M1 |
| `ev_fast_entry` | UI 按鈕（唔係格仔） | 按鈕「快速入場」 | `registered_match` 且曾完成同一場 | 傳送玩家至 (31,7)、跳過通道同隊伍介紹；若 `not formation_done` 先開佈陣介面 | M1 |
| `ev_start_line` | 起跑線 `S` (34,5–10) | touch | `registered_match` 且 `formation_done` | 起動 `cue_countdown` → 開賽（`start_match`） | M1 |
| `ev_start_line_warn` | 起跑線 `S` | touch | `registered_match` 且 `not formation_done` | 提示「未佈陣」＋按鈕 [去佈陣]／[用預設] | M1 |
| `ev_after_match` | 賽後 | auto | 結算完成 | 玩家放喺 (30,8)；`c1r1_won` 時觸發 `d_fern_after_r1`；之後可行出大門回城 | M1 |

> 賽前流程總時限（驗收：快速入場 ≤30 秒；首次完整 ≤3 分鐘）見 tuning-params-v2.2.md G 組。

## 4. 場景三：蕨影小徑 `trail_fernshadow`（60×16 圖塊）

```
    0         1         2         3         4         5         
    012345678901234567890123456789012345678901234567890123456789
 0  ############################################################
 1  #YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY#
 2  #YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY#
 3  #.......................,,,,..........*.....,,,,,..........#
 4  #.....,,,,,.............,,,,................,,,,,..........#
 5  #.....,,,,,.............,,,=============....,,,,,..........#
 6  #..s....................===================.............s..#
 7  E=...................======.............======............xx
 8  E====.............======...................======.........xx
 9  #.===================.........................=============#
10  #....=============,,..........,,,,,.....~~~~~~~..==========#
11  #.............,,,,,,..........,,,,,.....~~~~~~~...,,,,,,...#
12  #.......................................~~~~~~~............#
13  #YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY#
14  #YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY#
15  ############################################################
```

**佈局要點**
- 西端 `E` (0,7–8) 回晨苔鎮；東端 `x` 路障 (58–59,7–8)＝通往石磯港嘅路，M1 封住（告示牌 `s` (56,6)）。
- 路徑為自然彎曲（y 約 5–10），兩旁蕨叢 `,` 營造「蕨影」：蕨叢上半入遮擋層，角色行入會半隱，並加光斑（HD-2D 光柱）。
- 野生碎石獾 `*` 喺小空地 (36–41, 3–4)，位置 (38,3)，由路徑東行可以**遠遠睇到**（唔設隨機遇敵）。
- 池塘 (40–46, 10–12) 作地標，亦示範水面反射光。

**事件點（trail_fernshadow）**

| id | 位置 | 類型／觸發 | 條件 | 動作 | M |
|---|---|---|---|---|---|
| `west` | (1,7) | 出生（**舊稱 `spawn_from_town`＝`west`**，統一用 JSON 的 `west`；賽場大廳的 `spawn_from_town` 係另一場景，保持不變） | 由 `ev_town_east`（entry `west`） | 鏡頭向右微移；小徑 BGM（M1 可沿用城鎮 BGM） | M1 |
| `ev_trail_west` | (0,7–8) | touch | — | 傳送 → `town_morningmoss` (38,13)（東出口 (39,13–14) 西側一格）；自動存檔 | M1 |
| `obj_sign_hint` | (3,6) | interact | — | 「前方空地有野靈，走近點一下可結緣」（提示，可關） | M1 |
| `npc_wild_badger` | (38,3) | interact（半徑 2） | `not captured_badger` | `d_capture_intro` → 確認後 `begin_capture`（結緣賽 `cap_trail_badger`，見 match-data-format.md） | M1 |
| `ev_capture_retry` | (38,3) | interact | 結緣失敗後 | 冷卻 `capture_retry_cd` 秒內顯示「牠仲喺度喘氣」；之後可重試 | M1 |
| `obj_sign_east` | (56,6) | interact | — | 「前往石磯港（風停咗，路暫時未通）」 | M1 |
| `ev_trail_block` | (58–59,7–8) | interact／touch | — | 氣泡「倒塌嘅樹幹擋住路」（M2 換成劇情事件並開路） | M1 |

捕獲成功後：野生野靈消失；`captured_badger=true`；彈出命名（可略過）→入隊；自動存檔。

## 5. 層次與碰撞（給遊程／遊美嘅匯出規格）

**圖層名稱（地圖編輯器匯出 JSON，三場景一致）**

> 晨苔鎮已按遊美 JSON 實作（五層）；迴風場／蕨影小徑出圖時沿用同一套層名與 code。

| 層（JSON 名） | 內容 | 備註 |
|---|---|---|
| `ground` | 地面圖塊（草、泥、石徑、水、橋、地板） | 最底 |
| `deco` | 地面裝飾＋建築牆身／門窗、樹幹、籬笆、物件（碰撞由 `collision` 層決定） | 實體按底線 y-sort；v1 的獨立 `objects` 層已併入此層 |
| `occlusion` | 屋頂、樹冠、旗、燈頭、蕨叢上半 | 畫喺角色上面；角色行入「背面」即被遮（v1 名 `occlude`） |
| `collision` | 純邏輯格（值＝gid−544）：`0` 通行／`1` 阻擋／`2` 水／`3` trigger／`4` 慢速 | 16 px 格；玩家碰撞盒 12×8 px、貓 16×8 px（腳底中心，遊美 ASSET_SPEC_TOWN）；**唔係淨係 0／1**；引擎應由 tmj 內 `tilesets[].name=='collision'` 讀 firstgid（晨苔鎮＝545） |
| `events` | Tiled objectgroup：`name`（＝事件 id）、`type`（`spawn`／`warp`／`trigger`／`npc_spawn`／`interact`／`light`）、矩形（像素，÷16＝格）、`properties`（`cond`、`dialog`／`dialog_node`、`target`／`entry`、`hint`、`locked`、`autosave`、`once`…） | `cond` 為簡單布林字串（解析規則同對話格式，見 dialogue-format.md 第 4、5 節；詳細語法由遊程定）。v1 的 `touch／auto／npc` 對應：warp＝touch 傳送；trigger（`auto_dialog`）＝auto；`npc_spawn`＝npc |
| （光點） | v1 的獨立 `lights` 層**改為 `events` 內 `type=light` 物件**：`kind`（`lantern／window／chimney／landmark`）、`color`、`radius`（格）、`lit_default` | HD-2D 動態光；夜間全開；低畫質檔改用預烘焙光圖；日夜圖塊以 `tileset_all_gids.json#swap_day_to_lit` 替換 |

**規則**
- **碰撞**：格子制；高物件（樹、燈柱、告示板）只喺底座格設 1；玩家碰撞盒細過一格，可貼牆滑行（唔卡角）。NPC 同野生野靈佔 1 格。
- **y-sort**：角色、NPC、`objects` 以腳底 y 排序；`occlude` 層永遠喺角色上方。
- **觸控**：互動物件嘅可點擊範圍 **≥44 px（螢幕實際尺寸）**，同圖塊大小無關；點擊 NPC 後自動尋路到相鄰格再觸發互動。
- **事件觸發**：`touch`＝玩家碰撞盒進入矩形；`interact`＝玩家喺互動半徑內（預設 1.5 格）點擊或按互動鍵；`auto`＝進入矩形即觸發（可設 once／once-per-match）。
- **傳送**：`teleport` 動作＝（目標場景 id、目標座標、朝向、轉場 0.3 秒、是否自動存檔）。
- **鏡頭**：跟隨玩家，地圖邊緣鉗制；晨苔鎮／迴風場畫面細過地圖；小徑橫向捲動。
- **規模對照計劃上限**：城鎮 40×30 ✔（上限約 40×30）；小徑 60×16 ✔；迴風場 40×15（賽場屬單層小場景）。

## 6. 給各隊嘅提示

- **遊程**：碰撞用格子制，尋路 A*（4 向，可試 8 向）；`events` 層嘅 `cond`／`actions` 同對話共用同一解析器。
- **遊美**：晨苔鎮建築立面已交付 5 類（老鐘屋 House A、迴風場門樓、報名處、蕨生家 House B、商店 House C；**唔做風車**）；迴風場室內大廳／賽場與蕨影小徑仍需出圖；樹／蕨叢／屋頂要分開出「遮擋層」圖塊。
- **遊測**：路徑測試案例＝「出生→老鐘→蕨生→（小徑結緣）→入場→報名→入場→佈陣→起跑線」；每張圖都要測**貼牆滑行**、**觸控誤點容錯**、**場景傳送後座標**。
