# 旗標／變數規範（M1 第 2 週；`data/flags.json` 為登記表）

實作：`src/logic.js`（cond／actions 求值）、`src/save.js`（存檔）、`src/adventure.js`（host）。登記表由 `src/dialogue.js` lint 讀入（未登記名稱 → 警告）。

## 1. 命名
- **旗標 flag**：`^[a-z][a-z0-9_]*$`（扁平 snake_case，遊策 dialogue-format §5-5）。存檔 `flags` 容許再多 0–4 段點分命名空間（`save.js` RE.flag），所以日後可用 `story.ch1.x`；M1 全部扁平。bool 為主，亦可 int／短 string（≤32）。**只增唔改名**。
- **變數 var**：同命名規則；型別 int／string，有三類：
  1. *builtin* 派生自存檔（唯讀，或經專用 action 寫）：`leaf`（player.leaf）、`party_size`（party.length）、`seals`（player.seals.length）、`objective`（chapter.step）。
  2. *存檔 var*：`registered_match`、`fern_attitude`、`elder_gift_count`、`last_town_door`（**字串變數**，經 `set_var` 寫；存入 `flags`，同旗標同表）。
  3. *session／runtime*（唔入存檔）：`fee`、`capture_cd`、`r1_min_team`（tuning；預設 2；dev 旗標可於運行時放寬到 1，見 §4.3）。
- **一次性事件 key**（`once`）：`ev:<scene前4字>:<事件名>`、`match:<scene前4字>:<名>`；符合 `^[a-z][a-z0-9_:.]{0,47}$`（`save.js` RE.evKey）。前綴 `ev:`／`match:` 保證唔同遊策旗標撞名。

## 2. 已登記旗標（10）
| 旗標 | 意義 | 寫入點 |
|---|---|---|
| `intro_p1_done` | 開場字幕＋P1 已播（新遊戲只播一次；遊程新增） | d_prologue:p1_end |
| `prologue_done` | 序章 P3 完；解鎖出鎮／入迴風場 | d_elder_intro:p3_end |
| `got_mochi` | 已取得苔團；`spirit_follow` 於此後生成 | d_elder_intro:e_give |
| `captured_badger` | 已結緣碎石獾 | cap_trail_badger win |
| `formation_done` | 本場已佈陣；register_match 時重設 | open_ui formation、register_match |
| `c1r1_won`／`c1r1_lost_last` | 初戰已勝／上次敗北 | c1_r1 on_end |
| `met_fern`／`met_sang`／`seen_fern_prematch` | 首次對話旗標 | 各 d_* 節點 |

## 3. 變數（11）
`leaf`、`party_size`、`seals`、`registered_match`、`fern_attitude`（rival/friendly）、`elder_gift_count`、`fee`（session）、`r1_min_team`（tuning，預設 2）、`capture_cd`（runtime）、`objective`、`last_town_door`（enum door_arena／door_registry）。

## 4. 與規格不一致／需遊策確認
1. **（遊策 11:25 定案）`party_size`**：由引擎按隊伍人數（`party.length`）自動維護，`give_spirit` 後即 +1。data 內已刪除 `add_var party_size`（`cap_trail_badger` 勝利 actions）；若舊資料仍有，引擎**靜默忽略，唔再警告**（lint 亦唔再出 `W_DERIVED_VAR`）。
2. **（遊策 11:25 定案）`last_town_door`＝字串變數**（`set_var`，值 `door_arena`／`door_registry`，存檔 var）；唔係布林 flag。鎮→賽場嘅 warp 前置 `set_var last_town_door`，`door_town` 按它返鎮 (20,9)／(30,9)。
3. **（遊策 11:25 定案）`r1_min_team`**：正式流程＝2（tuning 預設，範圍 1–2）：先結緣碎石獾令 `party_size=2` 先可報名；**唔加**「借野靈」對白。走路切片提供 dev 旗標放寬到 1：網址 `?dev=1`，或 ⚙ 面板「報名人數放寬到 1」開關；只改運行時 tuning（唔入存檔），**預設唔放寬**。e2e（tests/walk-e2e.js）兩種模式都測：預設 1 隻被拒（§5）、dev 1 隻可報（§13）。
4. `fee` 預設取 c1_r1.fee（20）；`start_leaf` 50；報名 50→30。
5. 旗標只可由登記表內 `set_by` 寫入；dev 面板（walk.html ⚙）「+50 葉」等為開發工具，**唔係遊戲內容**。
