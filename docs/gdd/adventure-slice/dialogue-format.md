# 對話資料格式 dialogue/v1

> 遊策｜週 1｜草稿 v1｜全原創｜給：遊程（解析器／對話框）、遊美（頭像／對話框）、遊測（分支驗證）
> 對話以「節點圖」存成 JSON（每個 NPC 一檔，建議路徑 `data/dialogue/<npc_id>.json`）。對話內容見 npc-dialogue.md；本檔只定格式。

## 1. 檔案結構

| 欄位 | 型別 | 必填 | 說明 |
|---|---|---|---|
| `schema` | string | ✓ | 固定 `"dialogue/v1"` |
| `id` | string | ✓ | 對話集 id，如 `d_sang_hub` |
| `npc` | string | | 對應地圖物件 id（如 `npc_sang`） |
| `entry` | array | ✓ | 入口規則，由上而下，第一個 `cond` 成立者勝；最後一條必須無 `cond`（保底） |
| `nodes` | object | ✓ | key＝節點 id（全檔唯一） |

`entry` 項：`{ "cond": <條件，可省略>, "goto": "<節點 id>" }`

## 2. 節點欄位

| 欄位 | 型別 | 說明 |
|---|---|---|
| `speaker` | string | 說話者 id：`narrator`／`player`／`elder`／`fern`／`sang`（對應 `portrait_id`，見下方說話者表）；`system` 表示純邏輯節點（無文字） |
| `emote` | string | 頭像表情（5 個）：`neutral`／`smile`／`surprise`／`serious`／`worried`；省略＝`neutral`。對應美術 `expression`（art-wind/ASSET_SPEC_TOWN.md §N.3，每位 NPC 5 張）：`neutral`→`neutral`、`smile`→`happy`、`surprise`→`surprised`、`serious`→`serious`、`worried`→`worried`；未知表情回退 `neutral`。頭像以 `portrait_id`（＝`npc_id`）＋`expression` 引用（見下方說話者表） |
| `text` | string | 對白；支援 `{player}`、`{leaf}`、`{fee}`、`{var:<名>}`；`\n` 換行；≤38 字 |
| `next` | string／null | 下一節點；`null` 或省略＝對話結束 |
| `choices` | array | 選項（≤3）；有 `choices` 時忽略 `next` |
| `branch` | array | 僅邏輯節點用：`[{ "cond": …, "goto": … }, …]`，由上而下，最後一條無 `cond` |
| `on_enter` | array | 進入節點時依序執行的事件（見 §4） |
| `on_exit` | array | 離開節點時執行（選擇後、跳下一節前） |
| `once` | bool | `true`＝整個存檔只會顯示一次（再入時直接走 `next`） |
| `autoadvance_ms` | int | 自動推進毫秒（旁白用）；省略＝等點擊 |

`choices` 項：

| 欄位 | 說明 |
|---|---|
| `id` | 選項 id（遙測用） |
| `text` | 顯示文字，≤16 字，可含 `{fee}` |
| `cond` | 可選；不成立時隱藏（`hide`）或灰化（`disabled_hint` 有值） |
| `disabled_hint` | 灰化時的原因提示（≤14 字） |
| `next` | 目標節點；`null`＝結束 |
| `on_choose` | 事件陣列 |

**說話者表**（音效 id 對應遊音現有 `sfx_dialog_blip_*`，頭像由遊美出，每位 5 表情：`neutral`／`happy`／`worried`／`surprised`／`serious`）：

| `speaker` | `portrait_id` | 顯示名 | 逐字 blip | 備註 |
|---|---|---|---|---|
| `narrator` | — | （無名，斜體框） | 無 | 旁白 |
| `player` | — | `{player}` | `sfx_dialog_blip_b` | 無頭像，只顯示文字框 |
| `elder` | `npc_elder` | 老鐘 | `sfx_dialog_blip_a`（低、暖） | |
| `fern` | `npc_fern` | 蕨生 | `sfx_dialog_blip_b` | |
| `sang` | `npc_sang` | 桑姨 | `sfx_dialog_blip_c`（略輕） | 只在 `arena_windrun` 大廳 |
| 其他 NPC | 見 NPC 表 | 見 NPC 表 | 預設 `blip_b` | |

對話框音效：打開 `sfx_dialog_open`、推進 `sfx_dialog_next`、關閉 `sfx_dialog_close`、選項游標 `sfx_menu_move`（建議；BGM 於對話期間壓低約 3 dB，遊音建議值）。

## 3. 條件語法（`cond`）

JSON 物件，單一運算子 key：

| 寫法 | 意義 |
|---|---|
| `{"flag":"met_fern"}` | 旗標為 true |
| `{"not":{…}}` | 反轉 |
| `{"all":[{…},{…}]}` | 全部成立 |
| `{"any":[{…},{…}]}` | 任一成立 |
| `{"var":"leaf","op":">=","value":20}` | 變數比較；`op`：`== != < <= > >=` |
| `{"var":"leaf","op":">=","var2":"fee"}` | 與另一變數比較 |
| `{"has_value":"registered_match"}` | 字串變數非空 |
| `{"seen":"sang_first"}` | 該節點曾顯示 |

**變數與旗標**：旗標＝bool（`set_flag`／`clear_flag`）；內建變數：`leaf`、`party_size`、`seals`、`registered_match`（字串）、`last_town_door`（字串）；變數＝int 或 string（`set_var`／`add_var`）。作用域＝存檔（全域）。未定義的旗標視為 false、未定義的數值變數視為 0；**載入時遇到未知的旗標名要警告（lint）**，唔好 silent 吞。

**唯讀變數**：`party_size` 由引擎按隊伍人數自動維護，**唯讀、引擎維護**，事件／對話唔可改寫。`last_town_door` 係字串變數，用 `set_var` 設值（`door_arena`／`door_registry`），唔係旗標。

## 4. 事件動作（`on_enter`／`on_exit`／`on_choose`）

| `do` | 參數 | 說明 |
|---|---|---|
| `set_flag` / `clear_flag` | `flag` | 設／清旗標 |
| `set_var` | `var`, `value` | 賦值 |
| `add_var` | `var`, `delta` | 加減（`leaf` 不得低於 0） |
| `give_spirit` | `species`, `lv`, `nickname_prompt` | 發放野靈（序章：`mochi` Lv3） |
| `register_match` | `match` | 扣報名費、設 `registered_match`、`formation_done=false`；失敗（葉幣不足）則不執行並回 `sang_no_leaf` |
| `set_objective` | `id` | 更新任務提示 |
| `show_hint` | `id` | 顯示一次性教學提示（`once` 由 hint 表管） |
| `teleport` | `scene`, `x`, `y`, `dir` | 切換地圖 |
| `npc_move` / `npc_face` | `npc`, `x`,`y` / `dir` | NPC 走位／轉向 |
| `camera` | `cmd`（`pan_to`／`zoom`／`shake`／`reset`）, 參數 | 鏡頭 |
| `play_sfx` / `play_bgm` / `stop_bgm` | `id` | 音效 id 見 cue-table.md |
| `wait` | `ms` | 等待 |
| `autosave` | — | 自動存檔 |
| `open_ui` | `name`（`naming`／`formation`） | 開介面 |
| `start_match` / `begin_capture` | `match` | 進入賽事／結緣戰 |

事件按陣列順序同步執行；`wait`／`camera pan_to`／`npc_move` 屬阻塞型（對話暫停至完成），其餘即時。

## 5. 驗證（lint，遊程在匯入器實作，遊測用同一套檢查）

1. 所有 `goto`／`next` 指向存在的節點；`entry` 最後一條無 `cond`。
2. 節點 id 全檔唯一；無法到達的節點出警告。
3. `choices` ≤3；`text` ≤38 字；選項 `text` ≤16 字。
4. 圖無「必然無限迴圈」（沿 `next` 走必須能到 `null`，或經 `choices` 離開）。
5. `speaker` 與 `emote` 存在於資源表；`do` 在 §4 列表內；旗標名在 `flags.json` 內。

## 6. 完整範例：桑姨（`d_sang_hub`，縮略版，可直接當解析器測試輸入）

```json
{
  "schema": "dialogue/v1",
  "id": "d_sang_hub",
  "npc": "npc_sang",
  "entry": [
    { "cond": { "flag": "c1r1_won" }, "goto": "sang_won" },
    { "cond": { "all": [ { "flag": "c1r1_lost_last" }, { "not": { "has_value": "registered_match" } } ] }, "goto": "sang_lost" },
    { "cond": { "has_value": "registered_match" }, "goto": "sang_registered" },
    { "cond": { "not": { "flag": "met_sang" } }, "goto": "sang_first" },
    { "goto": "sang_menu" }
  ],
  "nodes": {
    "sang_first": {
      "speaker": "sang", "emote": "smile",
      "text": "歡迎嚟迴風場。我係桑姨，管報名。你係老鐘封信嗰位新人？",
      "on_enter": [ { "do": "set_flag", "flag": "met_sang" } ],
      "next": "sang_first_2"
    },
    "sang_first_2": {
      "speaker": "sang", "emote": "neutral",
      "text": "初葉盃對新手開放，冇資格要求。有咩想問？",
      "next": "sang_menu"
    },
    "sang_menu": {
      "speaker": "sang", "emote": "neutral",
      "text": "想做咩？",
      "choices": [
        { "id": "register", "text": "報名初葉盃・初戰（{fee} 葉幣）", "next": "sang_reg_check" },
        { "id": "info", "text": "報名須知", "next": "sang_info" },
        { "id": "bye", "text": "冇嘢喇", "next": null }
      ]
    },
    "sang_reg_check": {
      "speaker": "system",
      "on_enter": [ { "do": "set_var", "var": "fee", "value": 20 } ],
      "branch": [
        { "cond": { "var": "party_size", "op": "<", "value": 2 }, "goto": "sang_need_two" },
        { "cond": { "var": "leaf", "op": "<", "var2": "fee" }, "goto": "sang_no_leaf" },
        { "goto": "sang_reg_ok" }
      ]
    },
    "sang_need_two": {
      "speaker": "sang", "emote": "serious",
      "text": "你而家得一隻野靈，接力要兩隻。小徑有野生嘅，結緣一隻再嚟啦。",
      "next": "sang_menu"
    },
    "sang_no_leaf": {
      "speaker": "sang", "emote": "neutral",
      "text": "葉幣唔夠喎。不如問下老鐘，佢一向好疼新人。",
      "next": "sang_menu"
    },
    "sang_reg_ok": {
      "speaker": "sang", "emote": "smile",
      "text": "好，初葉盃・初戰，報名費 {fee} 葉幣，簽咗名喇。",
      "on_enter": [
        { "do": "register_match", "match": "c1_r1" },
        { "do": "set_objective", "id": "c1_enter" },
        { "do": "play_sfx", "id": "sfx_register_confirm" },
        { "do": "autosave" }
      ],
      "next": "sang_reg_ok_2"
    },
    "sang_reg_ok_2": {
      "speaker": "sang", "emote": "neutral",
      "text": "閘口開咗。行過通道，喺看台佈陣，再行去起跑線就開賽。",
      "on_enter": [ { "do": "show_hint", "id": "fast_entry" } ],
      "next": "sang_reg_ok_3"
    },
    "sang_reg_ok_3": { "speaker": "sang", "emote": "smile", "text": "加油，{player}。", "next": null },
    "sang_info": {
      "speaker": "sang", "emote": "neutral",
      "text": "接力每邊最少兩隻、最多六隻。賽前喺看台揀邊隻先跑，其餘排後備。",
      "next": "sang_menu"
    },
    "sang_registered": {
      "speaker": "sang", "emote": "neutral",
      "text": "你已經報咗名，閘口喺前面，入去佈陣啦。",
      "next": null
    },
    "sang_won": {
      "speaker": "sang", "emote": "smile",
      "text": "恭喜贏出！獎金收好。複賽暫時未開放，等風起再嚟。",
      "next": null
    },
    "sang_lost": {
      "speaker": "sang", "emote": "smile",
      "text": "唔緊要，再報一次就得。下次睇住下一段地形再換人。",
      "next": "sang_menu"
    }
  }
}
```

## 7. 範例：帶選項＋事件（蕨生首次見面節選）

```json
{
  "schema": "dialogue/v1",
  "id": "d_fern_first",
  "npc": "npc_fern",
  "entry": [
    { "cond": { "all": [ { "flag": "prologue_done" }, { "not": { "flag": "met_fern" } } ] }, "goto": "ff1" },
    { "goto": "fi1" }
  ],
  "nodes": {
    "ff1": { "speaker": "fern", "emote": "smile", "text": "喂，你就係今日新到嘅見習生？我係蕨生，同你一樣想賽初葉盃。", "next": "ff3" },
    "ff3": {
      "speaker": "fern", "emote": "serious", "text": "決賽見真章，你想點？",
      "choices": [
        { "id": "rival", "text": "我會贏你", "on_choose": [ { "do": "set_var", "var": "fern_attitude", "value": "rival" } ], "next": "ff5" },
        { "id": "friendly", "text": "一齊加油", "on_choose": [ { "do": "set_var", "var": "fern_attitude", "value": "friendly" } ], "next": "ff5" }
      ]
    },
    "ff5": {
      "speaker": "fern", "emote": "neutral", "text": "我再去練習。得閒嚟睇我點換棒啦。",
      "on_enter": [ { "do": "set_flag", "flag": "met_fern" }, { "do": "autosave" } ],
      "next": null
    },
    "fi1": { "speaker": "fern", "emote": "smile", "text": "報名要搵桑姨，唔係搵我㗎，哈哈。", "next": null }
  }
}
```

（此範例為縮略版，完整分支以 npc-dialogue.md 為準；`fern_attitude` 為 string 變數。）

## 8. 存檔與本地化提示

- 存檔只記旗標／變數／`seen` 節點 id，不存文字。
- 文字另可抽成 `text_key`（M2 本地化再做）；M1 直接用 `text`。
- 同一 NPC 分多個對話集（`d_fern_first`／`d_fern_prematch`／`d_fern_after_r1`），由地圖事件（maps-and-events.md）決定載入哪個。
