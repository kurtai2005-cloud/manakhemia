# NPC 對話表：第 1 章首段（老鐘／蕨生／桑姨）＋晨苔鎮互動物件旁白

> 遊策｜週 1｜草稿 v1｜全原創｜給：遊程（匯入對話資料）、遊美（頭像表情）、遊測（分支／旗標測試）
> 格式說明見 dialogue-format.md。每節點文字 ≤38 字（2 行 × 19 字）；連續節點 ≤6 句。口吻：老鐘＝慢、暖；蕨生＝快、好勝；桑姨＝利落、有耐性。表情 id 用 `neutral`／`smile`／`surprise`／`serious`／`worried`（每位 5 張頭像）；對應美術 `expression`：`smile`→`happy`、`surprise`→`surprised`、`serious`→`serious`、`worried`→`worried`、`neutral` 不變（見 dialogue-format.md §2；頭像以 `portrait_id`＋`expression` 引用；`portrait_id`：老鐘＝`npc_elder`、蕨生＝`npc_fern`、桑姨＝`npc_sang`）。
> 旗標／變數：`prologue_done`、`got_mochi`、`captured_badger`、`registered_match`、`formation_done`、`c1r1_won`、`c1r1_lost_last`、`met_fern`、`met_sang`、`fern_attitude`（`rival`／`friendly`）、變數 `leaf`、`party_size`、`elder_gift_count`（老鐘贈款次數，上限 3，見 tuning-params-v2.2.md D 組）。
> 序章 `d_elder_intro`（見 prologue-script.md）同井邊常駐 `d_elder_hub` 係**兩個獨立節點**（`d_elder_hub` 入口優先 1 只係序章未完成時轉入 `d_elder_intro`）。
> 角色歸屬：老鐘＝第 1 章村長（`npc_elder`）；石伯＝第 2 章石磯港老領隊，另一角色，唔好混用。

## 1. 老鐘（`d_elder_hub`，廣場井邊 (21,14)）

入口分流（由上而下，第一個符合者）：

| 優先 | 條件 | 進入節點 |
|---|---|---|
| 1 | `not prologue_done` | `d_elder_intro`（序章） |
| 2 | `c1r1_won` | `elder_won` |
| 3 | `registered_match` 有值 | `elder_registered` |
| 4 | `captured_badger` | `elder_ready` |
| 5 | （其他） | `elder_capture` |

| 節點 | 說話者（表情） | 文字 | 下一節／選項 | 條件／事件 |
|---|---|---|---|---|
| `elder_capture` | 老鐘（smile） | 出鎮向東行，蕨影小徑空地度有隻碎石獾，同佢跑一場就結到緣。 | → `elder_capture_2` | |
| `elder_capture_2` | 老鐘（neutral） | 苔團識得「回氣」，耐力低嗰陣先用，唔好太早放。 | → `elder_capture_3` | |
| `elder_capture_3` | 老鐘（smile） | 輸咗都唔使驚，佢唔會走，歇一陣再試就得。 | 結束 | |
| `elder_ready` | 老鐘（smile） | 有兩隻啦。去迴風場搵桑姨報名，佢喺櫃台後面。 | → `elder_ready_menu` | |
| `elder_ready_menu` | 老鐘（neutral） | 報名費要二十葉幣，你身上夠唔夠？ | 〔夠，多謝〕→ 結束；〔唔夠喎〕→ `elder_gift`（條件：`leaf < 20` 且 `elder_gift_count < 3`） | 〔唔夠喎〕只喺 `leaf < 20` 顯示 |
| `elder_gift` | 老鐘（smile） | 拎去，當係老人家嘅見面禮。 | 結束 | 事件：`add_var leaf +20`、`add_var elder_gift_count +1` |
| `elder_registered` | 老鐘（neutral） | 報咗名就好。行過閘口，喺看台佈好陣，再行去起跑線就開賽。 | 結束 | |
| `elder_won` | 老鐘（surprise） | 贏咗？好！苔蘚同碎礫呢兩種路，你已經識得用。 | → `elder_won_2` | |
| `elder_won_2` | 老鐘（smile） | 複賽仲未開，等風再起啦。 | 結束 | |

## 2. 蕨生（同齡對手，開朗好勝）

| 節點 | 說話者（表情） | 文字 | 下一節／選項 | 條件／事件 |
|---|---|---|---|---|
| `d_fern_first` → `ff1` | 蕨生（smile） | 喂，你就係今日新到嘅見習生？我係蕨生，同你一樣想賽初葉盃。 | → `ff2` | 入口：`prologue_done` 且 `not met_fern` |
| `ff2` | 蕨生（neutral） | 我兩年前就跟老鐘學接力。你隻苔團……睇落好乖喎。 | → `ff3` | |
| `ff3` | 蕨生（serious） | 決賽見真章，你想點？ | 〔我會贏你〕→ `ff4a`；〔一齊加油〕→ `ff4b` | |
| `ff4a` | 蕨生（smile） | 好！有膽。決賽見，唔好中途就跌出去。 | → `ff5` | 事件：`set_var fern_attitude="rival"` |
| `ff4b` | 蕨生（smile） | 哈，客氣咩。不過決賽我唔會讓你。 | → `ff5` | 事件：`set_var fern_attitude="friendly"` |
| `ff5` | 蕨生（neutral） | 我再去練習。得閒嚟睇我點換棒啦。 | 結束 | 事件：`set_flag met_fern`、`autosave` |
| `d_fern_idle` → `fi1` | 蕨生（smile） | 報名要搵桑姨，唔係搵我㗎，哈哈。 | 結束 | `met_fern` 且 `not captured_badger` |
| `fi2` | 蕨生（surprise） | 有第二隻啦？嗰隻碎石獾好跑得喎，下一場見真章。 | 結束 | `captured_badger` 且 `not c1r1_won` |
| `d_fern_prematch` → `fp1` | 蕨生（smile） | 你報咗名？好！我企喺旁邊睇你比賽。 | → `fp2` | 入場後首次靠近起跑區；`registered_match=c1_r1` |
| `fp2` | 蕨生（serious） | 對手係鎮上嘅見習跑手，換棒好穩。你睇住佢幾時換人。 | 結束 | 事件：`set_flag seen_fern_prematch` |
| `d_fern_after_r1` → `fw1` | 蕨生（surprise） | 贏咗？唔錯。你換棒嗰下，我睇到有啲野。 | → `fw2` | 賽後；`c1r1_won` |
| `fw2` | 蕨生（smile） | 我嘅初戰都贏咗。決賽，我哋跑過先知。 | 結束 | |
| `fl1` | 蕨生（neutral） | 輸咗唔緊要，我第一場都輸過。睇下你邊度換遲咗？ | → `fl2` | 賽後；`c1r1_lost_last` |
| `fl2` | 蕨生（smile） | 再報一次啦，今次我陪你睇。 | 結束 | |

## 3. 桑姨（報名處職員，迴風場大廳 (6,3)，利落有耐性）

入口分流（由上而下）：

| 優先 | 條件 | 進入節點 |
|---|---|---|
| 1 | `c1r1_won` | `sang_won` |
| 2 | `c1r1_lost_last` 且 `registered_match` 無值 | `sang_lost` |
| 3 | `registered_match` 有值 | `sang_registered` |
| 4 | `not met_sang` | `sang_first` |
| 5 | （其他） | `sang_menu` |

| 節點 | 說話者（表情） | 文字 | 下一節／選項 | 條件／事件 |
|---|---|---|---|---|
| `sang_first` | 桑姨（smile） | 歡迎嚟迴風場。我係桑姨，管報名。你係老鐘封信嗰位新人？ | → `sang_first_2` | 事件：`set_flag met_sang` |
| `sang_first_2` | 桑姨（neutral） | 初葉盃對新手開放，冇資格要求。有咩想問？ | → `sang_menu` | |
| `sang_menu` | 桑姨（neutral） | 想做咩？ | 〔報名初葉盃・初戰（{fee} 葉幣）〕→ `sang_reg_check`；〔報名須知〕→ `sang_info`；〔冇嘢喇〕→ 結束 | `{fee}`＝20 |
| `sang_reg_check` | （系統分支） | — | `party_size < 2` → `sang_need_two`；`leaf < {fee}` → `sang_no_leaf`；否則 → `sang_reg_ok` | 純邏輯節點（無文字） |
| `sang_need_two` | 桑姨（serious） | 你而家得一隻野靈，接力要兩隻。小徑有野生嘅，結緣一隻再嚟啦。 | → `sang_menu` | |
| `sang_no_leaf` | 桑姨（neutral） | 葉幣唔夠喎。不如問下老鐘，佢一向好疼新人。 | → `sang_menu` | |
| `sang_reg_ok` | 桑姨（smile） | 好，初葉盃・初戰，報名費 {fee} 葉幣，簽咗名喇。 | → `sang_reg_ok_2` | 事件：`register_match c1_r1`（扣葉幣、設 `registered_match`、`formation_done=false`、`objective=c1_enter`） |
| `sang_reg_ok_2` | 桑姨（neutral） | 閘口開咗。行過通道，喺看台佈陣，再行去起跑線就開賽。 | → `sang_reg_ok_3` | 事件：`show_hint fast_entry`（下次可用「快速入場」） |
| `sang_reg_ok_3` | 桑姨（smile） | 加油，{player}。 | 結束 | |
| `sang_info` | 桑姨（neutral） | 接力每邊最少兩隻、最多六隻。賽前喺看台揀邊隻先跑，其餘排後備。 | → `sang_info_2` | |
| `sang_info_2` | 桑姨（neutral） | 贏咗獎金一定高過報名費，輸咗都有少少安慰獎。 | → `sang_info_3` | |
| `sang_info_3` | 桑姨（smile） | 懶得再行路？第二次起可以按「快速入場」，一下子到起跑區。 | → `sang_menu` | |
| `sang_registered` | 桑姨（neutral） | 你已經報咗名，閘口喺前面，入去佈陣啦。 | 結束 | |
| `sang_won` | 桑姨（smile） | 恭喜贏出！獎金收好。複賽暫時未開放，等風起再嚟。 | 結束 | |
| `sang_lost` | 桑姨（smile） | 唔緊要，再報一次就得。下次睇住下一段地形再換人。 | → `sang_menu` | |

## 4. 晨苔鎮互動物件旁白（M1）

> 對應 maps-and-events.md 第 2 節事件表嘅 6 個 `interact` 物件（JSON `properties.dialog`）。全部係 `narrator` 旁白，每個物件 2 句（`registry_counter_01` 例外：1 句），每句 ≤38 字；唔設選項、唔設旗標。
> **載入慣例**：`dialog` 屬性值＝節點 id，全部放同一對話集 `d_objects_town`（建議路徑 `data/dialogue/d_objects_town.json`）；格式見 dialogue-format.md（`entry` 為必填，此集只放保底 `goto`，實際由地圖事件直接指定起始節點）。節點 `<id>` 後接 `<id>_b`，點擊推進，結束即關閉。旁白框用斜體、無頭像、無逐字 blip。

| 節點 id | 地圖事件 | 對白（2 句） |
|---|---|---|
| `obj_well_01` | `obj_well`（廣場井） | 井水清得見底，水面浮著幾片細小的苔葉。／井底傳來很輕的水聲，像是風在下面打了個轉。 |
| `obj_notice_board_01` | `obj_notice_board`（告示板 (8,12)） | 告示板上寫著：「喚風祭・初葉盃報名中」。／角落有張舊紙：「今年風弱，跑手請多保重。」 |
| `sign_arena_01` | `obj_sign_arena`（路標 (18,11)） | 木牌寫著：「↑ 迴風場　→ 報名處」。／字旁畫了一面小旗，旗尖指向東邊。 |
| `obj_sign_east_01` | `obj_sign_east`（東路標 (36,12)） | 木牌寫著：「東：蕨影小徑 → 石磯港」。／牌腳長滿了苔，看來有一陣子沒人經過。 |
| `registry_counter_01` | `registry_counter`（報名處櫃台 (32,8)；晨苔鎮無職員 spawn） | 櫃台後面空無一人，只有一本攤開嘅名冊。報名要入迴風場搵桑姨。 |
| `registry_notice_01` | `registry_notice`（報名處告示 (33,8)） | 初葉盃：新手直接報名，沒有資格要求。／報名費二十葉幣，贏了獎金一定更高。 |

M3 起 `obj_notice_board_01` 改為每日賽事入口（M1 只顯示上列旁白）。

**JSON（可直接當解析器測試輸入；已用 Python `json.loads` 驗證，`next` 全部指向存在節點／`null`）**

```json
{
  "schema": "dialogue/v1",
  "id": "d_objects_town",
  "entry": [
    {
      "goto": "obj_well_01"
    }
  ],
  "nodes": {
    "obj_well_01": {
      "speaker": "narrator",
      "text": "井水清得見底，水面浮著幾片細小的苔葉。",
      "next": "obj_well_01_b"
    },
    "obj_well_01_b": {
      "speaker": "narrator",
      "text": "井底傳來很輕的水聲，像是風在下面打了個轉。",
      "next": null
    },
    "obj_notice_board_01": {
      "speaker": "narrator",
      "text": "告示板上寫著：「喚風祭・初葉盃報名中」。",
      "next": "obj_notice_board_01_b"
    },
    "obj_notice_board_01_b": {
      "speaker": "narrator",
      "text": "角落有張舊紙：「今年風弱，跑手請多保重。」",
      "next": null
    },
    "sign_arena_01": {
      "speaker": "narrator",
      "text": "木牌寫著：「↑ 迴風場　→ 報名處」。",
      "next": "sign_arena_01_b"
    },
    "sign_arena_01_b": {
      "speaker": "narrator",
      "text": "字旁畫了一面小旗，旗尖指向東邊。",
      "next": null
    },
    "obj_sign_east_01": {
      "speaker": "narrator",
      "text": "木牌寫著：「東：蕨影小徑 → 石磯港」。",
      "next": "obj_sign_east_01_b"
    },
    "obj_sign_east_01_b": {
      "speaker": "narrator",
      "text": "牌腳長滿了苔，看來有一陣子沒人經過。",
      "next": null
    },
    "registry_counter_01": {
      "speaker": "narrator",
      "text": "櫃台後面空無一人，只有一本攤開嘅名冊。報名要入迴風場搵桑姨。",
      "next": null
    },
    "registry_notice_01": {
      "speaker": "narrator",
      "text": "初葉盃：新手直接報名，沒有資格要求。",
      "next": "registry_notice_01_b"
    },
    "registry_notice_01_b": {
      "speaker": "narrator",
      "text": "報名費二十葉幣，贏了獎金一定更高。",
      "next": null
    }
  }
}
```

## 5. 野生碎石獾（`d_capture_intro`，蕨影小徑 `npc_wild_badger` (38,3)）

> 野靈唔講嘢；全部 `narrator` 旁白，3 句，每句 ≤38 字，口語粵語。碎石獾＝懶洋洋發呆嘅野靈：玩家靠近 → 對視 → 開跑。第 3 句後接系統確認（「要唔要挑戰？」，唔計句數）→ `begin_capture`（結緣賽 `cap_trail_badger`，見 maps-and-events.md／match-data-format.md）。

| 節點 | 說話者 | 文字 | 下一節 |
|---|---|---|---|
| `cap1` | 旁白 | 一隻碎石獾攤喺草地上發呆，連尾巴都懶得擺。 | → `cap2` |
| `cap2` | 旁白 | 你行近，牠慢慢抬起頭，同你四目相對。 | → `cap3` |
| `cap3` | 旁白 | 牠打咗個呵欠，忽然彈起身，沿小徑飛跑——追上去！ | 結束 |

```json
{
  "schema": "dialogue/v1",
  "id": "d_capture_intro",
  "entry": [
    {
      "goto": "cap1"
    }
  ],
  "nodes": {
    "cap1": {
      "speaker": "narrator",
      "text": "一隻碎石獾攤喺草地上發呆，連尾巴都懶得擺。",
      "next": "cap2"
    },
    "cap2": {
      "speaker": "narrator",
      "text": "你行近，牠慢慢抬起頭，同你四目相對。",
      "next": "cap3"
    },
    "cap3": {
      "speaker": "narrator",
      "text": "牠打咗個呵欠，忽然彈起身，沿小徑飛跑——追上去！",
      "next": null
    }
  }
}
```

## 6. 遊程占位（暫收，待替換）

> 以下由遊程自擬（`windrun-m1/data/dialogue/`），**暫收為占位**，之後可由遊策重寫；字數均 ≤38。`fp3` 屬 `d_fern_prematch`（`fp1` 已顯示過 `seen_fern_prematch` 後重入）；`d_elder_intro` 同 `d_elder_hub` 係兩個獨立節點（見檔頭）。

| 節點 | 說話者（表情） | 文字 | 條件 |
|---|---|---|---|
| `d_opponent_misc` → `op1` | 對手見習跑手（neutral） | 賽道上見。我哋唔會留手㗎。 | 預設（`not c1r1_won`） |
| `op_after` | 對手見習跑手（smile） | 你換棒好準。下次我都要練返。 | `c1r1_won` |
| `fp3` | 蕨生（neutral） | 開賽前記得佈陣，揀好邊隻先跑。 | `d_fern_prematch` 且 `seen_fern_prematch` |

**字數統計**：本檔漢字約 1,000（連條件／事件欄）；純對白約 700 字，連序章 P2 約 1,500 字，低於 M1 劇情字數上限（≈2,000 字）。

**旗標生命週期**：賽事結束時 `registered_match` 清空；勝＝`c1r1_won=true`、`c1r1_lost_last=false`；敗＝`c1r1_lost_last=true`。（見 match-data-format.md 的 `on_end`）

## 7. 賽場／小徑互動物件旁白（M1）

> 對應遊美 `tilemap_arena.json`（迴風場 3 個）、`tilemap_trail.json`（蕨影小徑 2 個）嘅 `interact` 物件 `properties.dialog`；**節點 id 以 tilemap 現有值為準**（文檔跟 tilemap）。全部 `narrator` 旁白，每個物件 1 句、≤38 字；唔設選項、唔設旗標；風格同 §4。
> **載入慣例**：同 §4。迴風場 3 個放對話集 `d_objects_arena`（`data/dialogue/d_objects_arena.json`），小徑 2 個放 `d_objects_trail`（`data/dialogue/d_objects_trail.json`）；`entry` 只放保底 `goto`。
> **唔屬本節**：`ev_capture_retry`（「牠仲喺度喘氣」）、`ev_trail_block`（「倒塌嘅樹幹擋住路」）兩個 tilemap 物件只有氣泡 `text`、無 `dialog` id，維持氣泡提示。迴風場 9 格擺設（盆栽 (1,2)(12,2)(21,2)(1,13)(12,13)、獎盃 (1,6)、木桶 (21,13)(38,2)、木箱 (38,13)）tilemap 無互動事件 id，**唔補旁白**。

| 節點 id | 地圖事件（場景） | 對白（1 句） |
|---|---|---|
| `obj_board_daily_01` | `obj_board_daily`（迴風場，告示板 (11,5)；M3 起改為每日賽事入口） | 「每日賽事」的告示板還是空的，要等風再起，才會貼上新單。 |
| `obj_scout_hall_01` | `obj_scout_hall`（迴風場大廳，情報位 (3,5)；M3 偵察 UI） | 情報桌上蓋著一塊舊布，今天沒有人當值。 |
| `obj_scout_stand_01` | `obj_scout_stand`（迴風場看台，情報位 (22,6)；M3 偵察 UI） | 看台邊的情報位空著，只留下一張落了灰的小凳。 |
| `obj_sign_hint_01` | `obj_sign_hint`（蕨影小徑，告示牌 (3,6)） | 木牌寫著：「前方空地有野靈，走近輕點一下，或許能結緣。」 |
| `obj_sign_east_trail_01` | `obj_sign_east`（蕨影小徑，東路標 (56,6)） | 木牌寫著：「前往石磯港」，下面一行小字：風停了，路暫時未通。 |

**JSON（已用 Python `json.loads` 驗證，`next` 全部為 `null`）**

```json
{
  "schema": "dialogue/v1",
  "id": "d_objects_arena",
  "entry": [ { "goto": "obj_board_daily_01" } ],
  "nodes": {
    "obj_board_daily_01": { "speaker": "narrator", "text": "「每日賽事」的告示板還是空的，要等風再起，才會貼上新單。", "next": null },
    "obj_scout_hall_01": { "speaker": "narrator", "text": "情報桌上蓋著一塊舊布，今天沒有人當值。", "next": null },
    "obj_scout_stand_01": { "speaker": "narrator", "text": "看台邊的情報位空著，只留下一張落了灰的小凳。", "next": null }
  }
}
```

```json
{
  "schema": "dialogue/v1",
  "id": "d_objects_trail",
  "entry": [ { "goto": "obj_sign_hint_01" } ],
  "nodes": {
    "obj_sign_hint_01": { "speaker": "narrator", "text": "木牌寫著：「前方空地有野靈，走近輕點一下，或許能結緣。」", "next": null },
    "obj_sign_east_trail_01": { "speaker": "narrator", "text": "木牌寫著：「前往石磯港」，下面一行小字：風停了，路暫時未通。", "next": null }
  }
}
```
