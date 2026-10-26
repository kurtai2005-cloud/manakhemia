# 遊策對白匯入備註（`tools/gen-dialogue-data.py` → `data/dialogue/*.json`）

- 12 個對白集；`node tests/dialogue.test.js`：173 斷言通過；lint 0 error、10 個 `W_UNREACHABLE`（預期）。
- **`d_objects_town`** 係「節點入口集」：6 個互動物件（obj_well_01 等）各 2 句旁白，由 interact 事件以 `{do:'dialog', id:'d_objects_town', node}` 直接進入某節點；所以 lint 對非入口節點報 `W_UNREACHABLE` 屬設計如此。
- 文字改動（相對遊策舊稿）：序章「風車」→「門樓旗」（M1 無風車）；部分 P2 台詞超過 `dialog_max_chars` 38，已拆句（不改字）。
- 占位（遊程自擬、需遊策確認）：`d_capture_intro`、`d_opponent_misc`、`fp3`。
- （遊策 11:25 定案、11:27 npc-dialogue.md 同步）`d_elder_intro`（序章 P2/P3）同 `d_elder_hub`（常駐）係**兩個獨立對話集，唔做 alias**；overlay `dialog_alias` 已移除。`tools/gen-dialogue-data.py` 由同一節點表拆成兩集：`d_elder_intro`（`e_p2_*`／`e_give`／`e_got`／`e_react`／`e_rA`／`e_rB`／`e_p2b_*`／`e_p3_*`／`p3_end`，29 節點）同 `d_elder_hub`（`elder_*`，9 節點）。`npc_elder` 對話清單喺 overlay 按 cond 揀（`not prologue_done` → `d_elder_intro`，否則 `d_elder_hub`）；trigger `ev_elder_intro`（`dialog_node=d_elder_intro`）直接解析。`d_opponent_misc`、`fp3` 保留；`d_capture_intro` 暫留 placeholder。
- 注意：遊策 npc-dialogue.md 檔頭寫「`d_elder_hub` 入口優先 1 轉入 `d_elder_intro`」；dialogue/v1 無跨集跳轉，故改用 overlay cond 達到同一效果（行為等價）。
- `add_var party_size`：data 已刪；舊資料如有，引擎靜默忽略（見 docs/flags.md §4）。
- 對白 UI：`src/dialogue-ui.js`（打字機 30 cps、tap 完成再進下一句、長按 ≥0.4 s 快轉、選項按鈕 ≥48 px、Esc／Skip 跳過、鍵盤 1–9 選項）。頭像由 `portrait_id`＋`expression`；遊程 emote→expression 對照〔估〕：neutral→neutral、smile→happy、surprise→surprised、serious→worried；未知表情落回 neutral。
- speaker → portrait_id：elder→npc_elder、fern→npc_fern；其他 speaker（桑姨等）尚無頭像（UI 無頭像時只顯示名字）。
