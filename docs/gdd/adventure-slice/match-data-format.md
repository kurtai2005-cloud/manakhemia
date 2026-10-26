# 賽事資料格式表（A.4）：cup → 場次 → 對手隊 → 賽道 → 獎勵 → 解鎖

> 遊策｜週 1｜草稿 v1｜全原創｜給：遊程（資料載入／報名檢查）、遊測（數值驗證）、遊美（賽事名稱／結算畫面文案）
> 所有數值 **暫定、可調**。範例數字由 `windrun-m1` 模擬器（單一種子、AI 代打）粗略校準，只作方向參考，**不是平衡結論**，遊測請用多種子重跑。
> 檔案建議路徑：`data/cups/c1.json`（cup）＋ `data/matches/<match_id>.json`（場次）。兩者皆 `version` 欄位，載入時缺欄補預設、未知欄位警告但不崩潰。

## 1. 資料層次

```
cup（盃賽）──1:N──► match（場次：初戰／複賽／冠軍賽）
match ──► opponent（對手隊） + track（賽道 5 段） + req（報名資格） + reward（獎勵） + on_end（賽後旗標／解鎖）
kind = cup（盃賽） | capture（結緣戰：野生野靈） | field（野地賽：可重複練習）
```

## 2. `cup/v1` 欄位

| 欄位 | 型別 | 說明 |
|---|---|---|
| `schema` | string | `"cup/v1"` |
| `id` | string | 如 `c1` |
| `name` | string | 顯示名（初葉盃） |
| `town` | string | 所在城鎮 id（`town_morningmoss`＝晨苔鎮） |
| `venue` | string | 賽場地圖 id（`arena_windrun`＝迴風場） |
| `tier` | int | 階級（1＝tier 1） |
| `rounds` | string[] | 場次 id，依序＝初戰／複賽／冠軍賽 |
| `entry_req` | object | 整個 cup 的開放條件：`{ "seals_min": 0 }` |
| `final_reward` | object | 冠軍賽勝出額外獎勵：`{ "seal": 1, "trade_ticket": 1 }` |
| `m_milestone` | string | 計劃里程碑（`M1`／`M2`），用於資料可用性旗標 |

## 3. `match/v1` 欄位

| 欄位 | 型別 | 必填 | 說明 |
|---|---|---|---|
| `schema` | string | ✓ | `"match/v1"` |
| `id` | string | ✓ | 如 `c1_r1`；結緣戰 `cap_<路線>_<野靈>`；野地賽 `field_<路線>_<序>` |
| `kind` | enum | ✓ | `cup`／`capture`／`field` |
| `cup` | string | cup 必填 | 所屬 cup id |
| `round` | int | cup 必填 | 1＝初戰、2＝複賽、3＝冠軍賽 |
| `name` | string | ✓ | 顯示名 |
| `venue` | string | ✓ | 賽場地圖 id（`arena_windrun`／`trail_fernshadow`） |
| `m_milestone` | string | ✓ | `M1`／`M2`；未達里程碑的場次載入為「未開放」 |
| `req` | object | ✓ | 報名資格（見 §4） |
| `team` | object | ✓ | `{ "min": 2, "max": 6 }` 玩家出場人數（含後備） |
| `track` | object | ✓ | `{ "len": 1000, "segs": ["moss","gravel","moss","gravel","moss"] }`；`segs` 恆為 5 段 × 200 m，地形 id 取 `moss`／`gravel`／`shallows`／`frost`／`bridge` |
| `opponent` | object | ✓ | `{ "name", "npc", "ai", "team": [{ "species", "lv" }], "script": null }`；`ai`＝`balanced`／`conservative`／`aggressive`／`counter`（M1 只用 `balanced`）；`script` 用於影子隊預錄 |
| `handicap_m` | number | | 正數＝對手領先起跑距離（結緣戰 50）；預設 0 |
| `rules` | object | | `{ "swap": true, "skill": true, "timeout_s": 120 }` |
| `fee` | int | ✓ | 報名費（葉幣）；結緣戰＝0 |
| `reward` | object | ✓ | `{ "leaf_win", "leaf_lose", "exp_win", "exp_lose", "first_win_leaf_bonus" }`；全部整數 |
| `capture` | object | capture 必填 | 勝出可結緣：`{ "species", "lv" }` |
| `seed_policy` | enum | | `per_attempt`（每次報名抽新種子並存入重播）／`fixed`（測試用）；預設 `per_attempt` |
| `dialogue` | object | | `{ "pre": "d_fern_prematch", "post_win": "…", "post_lose": "…" }` 賽前／賽後對話集 id |
| `on_end` | object | ✓ | `{ "win": [<action>…], "lose": [<action>…] }`；action 格式同 dialogue-format.md §4 |
| `unlock` | string[] | | 勝出後解鎖的場次 id（寫入「已完成場次集合」同時開放資格） |
| `target` | object | | 遊策設計目標（給遊測，不影響執行）：`{ "winrate_pct": 85, "player_lv_rec": 3, "margin_note": "…" }` |

### 3.1 結算規則（A 層）

1. 勝負＝先到終點者勝（兩隊對跑）；記錄 `margin_m`（終點時另一隊落後距離）供結算畫面顯示。
2. `reward.leaf_win`＝勝出現金；`first_win_leaf_bonus` 只喺**首次勝出**該場時加付。
3. 經驗：每隻**出過場**（實際跑過 ≥1 段或被換入）嘅野靈各獲 `exp_win`／`exp_lose`（**不平分**）；全程未上場的後備不計。升級所需＝`exp_base + exp_per_level × lv`（見 tuning-params-v2.2.md §4 進度表）。
4. 賽事結束：先清 `registered_match`，再執行 `on_end`；勝出時加入已完成場次集合，並按 `unlock`／`final_reward` 發放；自動存檔。
5. 敗北唔卡關：`c1_r1` 敗後旗標 `c1r1_lost_last=true`，可立即重新報名（再付報名費）。

## 4. `req`（報名資格）

| 欄位 | 說明 |
|---|---|
| `seals_min` | 風印最少數量（初葉盃 0） |
| `done` | 須先勝出嘅場次 id 陣列（複賽需 `c1_r1`） |
| `flags` | 須成立嘅旗標（如 `["got_mochi"]`） |
| `party_min` | 持有／隊內野靈最少數（r1 為 2） |
| `lv_hint` | **只作提示、不阻擋**：建議等級；顯示於報名須知 |
| `not_flags` | 不可成立嘅旗標（如結緣戰已完成就唔再出現） |
| `not_done` | 不可已勝出（冠軍賽結束後不可再報；野地賽無此欄） |

資格不足時，報名處對話必須給出**去向提示**（例：「得一隻野靈，去小徑結緣」）；不得只顯示「不可報名」。

## 5. 範例

### 5.1 cup：初葉盃

```json
{
  "schema": "cup/v1",
  "id": "c1",
  "name": "初葉盃",
  "town": "town_morningmoss",
  "venue": "arena_windrun",
  "tier": 1,
  "rounds": ["c1_r1", "c1_r2", "c1_r3"],
  "entry_req": { "seals_min": 0 },
  "final_reward": { "seal": 1, "trade_ticket": 1 },
  "m_milestone": "M1"
}
```

### 5.2 初戰 `c1_r1`（M1，唯一必須可玩）

對手：鎮上見習跑手（汀羽 Lv3＋霧蕨 Lv3），賽道 苔坡/碎礫/苔坡/碎礫/苔坡。

```json
{
  "schema": "match/v1",
  "id": "c1_r1",
  "kind": "cup",
  "cup": "c1",
  "round": 1,
  "name": "初葉盃・初戰",
  "venue": "arena_windrun",
  "m_milestone": "M1",
  "req": { "seals_min": 0, "flags": ["got_mochi"], "party_min": 2, "lv_hint": 3, "not_done": true },
  "team": { "min": 2, "max": 6 },
  "track": { "len": 1000, "segs": ["moss", "gravel", "moss", "gravel", "moss"] },
  "opponent": {
    "name": "見習跑手",
    "npc": null,
    "ai": "balanced",
    "team": [ { "species": "tingyu", "lv": 3 }, { "species": "mistfern", "lv": 3 } ],
    "script": null
  },
  "handicap_m": 0,
  "rules": { "swap": true, "skill": true, "timeout_s": 120 },
  "fee": 20,
  "reward": { "leaf_win": 45, "leaf_lose": 10, "exp_win": 100, "exp_lose": 45, "first_win_leaf_bonus": 0 },
  "seed_policy": "per_attempt",
  "dialogue": { "pre": "d_fern_prematch", "post_win": "d_fern_after_r1", "post_lose": "d_fern_after_r1" },
  "on_end": {
    "win":  [ { "do": "set_flag", "flag": "c1r1_won" }, { "do": "clear_flag", "flag": "c1r1_lost_last" }, { "do": "set_objective", "id": "c1_done_m1" } ],
    "lose": [ { "do": "set_flag", "flag": "c1r1_lost_last" }, { "do": "set_objective", "id": "c1_enter" } ]
  },
  "unlock": ["c1_r2"],
  "target": { "winrate_pct": 85, "player_lv_rec": 3, "margin_note": "苔團3＋碎石獾3：AI 代打約領先 55 m；全程唔換人約落後 12 m（換棒決策可決定勝負）" }
}
```

> 設計意圖：玩家不換人會輸（落後約 12 m）、會換人會贏（約領先 55 m），令首場即教會「換棒有用」。賽後經驗：兩隻出場者各 +100（苔團3 約升到 Lv4／5，見 tuning-params-v2.2.md §4）。

### 5.3 結緣戰 `cap_trail_badger`（M1，蕨影小徑）

野生碎石獾 Lv4 先跑 50 m；玩家**單隻**出戰（苔團 Lv3），必須用「回氣」。賽道 苔坡/苔坡/碎礫/碎礫/苔坡。

```json
{
  "schema": "match/v1",
  "id": "cap_trail_badger",
  "kind": "capture",
  "name": "結緣：碎石獾",
  "venue": "trail_fernshadow",
  "m_milestone": "M1",
  "req": { "flags": ["got_mochi"], "not_flags": ["captured_badger"], "lv_hint": 3 },
  "team": { "min": 1, "max": 1 },
  "track": { "len": 1000, "segs": ["moss", "moss", "gravel", "gravel", "moss"] },
  "opponent": {
    "name": "野生碎石獾",
    "npc": "npc_wild_badger",
    "ai": "balanced",
    "team": [ { "species": "gravelbadger", "lv": 4 } ],
    "script": null
  },
  "handicap_m": 50,
  "rules": { "swap": false, "skill": true, "timeout_s": 120 },
  "fee": 0,
  "reward": { "leaf_win": 0, "leaf_lose": 0, "exp_win": 60, "exp_lose": 25, "first_win_leaf_bonus": 0 },
  "capture": { "species": "gravelbadger", "lv": 4 },
  "seed_policy": "per_attempt",
  "dialogue": { "pre": "d_capture_intro", "post_win": "d_capture_win", "post_lose": "d_capture_lose" },
  "on_end": {
    "win":  [ { "do": "give_spirit", "species": "gravelbadger", "lv": 4, "nickname_prompt": true },
              { "do": "set_flag", "flag": "captured_badger" },
              { "do": "add_var", "var": "party_size", "delta": 1 },
              { "do": "set_objective", "id": "c1_register" } ],
    "lose": [ { "do": "set_objective", "id": "c1_capture_retry" } ]
  },
  "unlock": [],
  "target": { "winrate_pct": 70, "player_lv_rec": 3, "margin_note": "苔團3 單打：放『回氣』勝約 +17 m；唔放技能勝約 +0.5 m（極險）→ 教曉玩家用技能時機；唔可以換人" }
}
```

> 結緣戰輸咗：免費、無冷卻，可即刻再挑戰（M1 唔做「重複失敗保底」，列入 §7 待調）。

### 5.4 冠軍賽 `c1_r3`（M2 範例，驗證 `script`／蕨生隊／風印欄位）

對手：蕨生（苔團＋碎石獾＋風鼬，全 Lv6），賽道 苔坡/碎礫/碎礫/苔坡/碎礫。M2 內容，此處只作格式驗證。

```json
{
  "schema": "match/v1",
  "id": "c1_r3",
  "kind": "cup",
  "cup": "c1",
  "round": 3,
  "name": "初葉盃・冠軍賽",
  "venue": "arena_windrun",
  "m_milestone": "M2",
  "req": { "seals_min": 0, "done": ["c1_r2"], "party_min": 3, "lv_hint": 6, "not_done": true },
  "team": { "min": 3, "max": 6 },
  "track": { "len": 1000, "segs": ["moss", "gravel", "gravel", "moss", "gravel"] },
  "opponent": {
    "name": "蕨生",
    "npc": "npc_fern",
    "ai": "aggressive",
    "team": [ { "species": "mochi", "lv": 6 }, { "species": "gravelbadger", "lv": 6 }, { "species": "windweasel", "lv": 6 } ],
    "script": null
  },
  "handicap_m": 0,
  "rules": { "swap": true, "skill": true, "timeout_s": 120 },
  "fee": 45,
  "reward": { "leaf_win": 110, "leaf_lose": 25, "exp_win": 170, "exp_lose": 70, "first_win_leaf_bonus": 30 },
  "seed_policy": "per_attempt",
  "dialogue": { "pre": "d_fern_final_pre", "post_win": "d_fern_final_win", "post_lose": "d_fern_final_lose" },
  "on_end": {
    "win":  [ { "do": "add_var", "var": "seals", "delta": 1 }, { "do": "set_flag", "flag": "c1_cup_won" }, { "do": "set_objective", "id": "ch2_start" } ],
    "lose": [ { "do": "set_flag", "flag": "c1r3_lost_last" } ]
  },
  "unlock": ["c2_r1"],
  "target": { "winrate_pct": 60, "player_lv_rec": 7, "margin_note": "玩家 苔團／碎石獾／霧蕨：Lv5 輸約 2.8 m、Lv6 輸約 0.9 m、Lv7 贏約 0.6 m（單種子，極接近）；唔換人落後約 75–85 m" }
}
```

### 5.5 野地賽 `field_trail_01`（M2 範例，可重複）

```json
{
  "schema": "match/v1",
  "id": "field_trail_01",
  "kind": "field",
  "name": "小徑練習賽",
  "venue": "trail_fernshadow",
  "m_milestone": "M2",
  "req": { "done": ["c1_r1"], "party_min": 2 },
  "team": { "min": 2, "max": 3 },
  "track": { "len": 1000, "segs": ["moss", "gravel", "moss", "gravel", "moss"] },
  "opponent": {
    "name": "路過的跑手",
    "npc": null,
    "ai": "balanced",
    "team": [ { "species": "tingyu", "lv": "avg-1" }, { "species": "mistfern", "lv": "avg-1" } ],
    "script": null
  },
  "handicap_m": 0,
  "rules": { "swap": true, "skill": true, "timeout_s": 120 },
  "fee": 5,
  "reward": { "leaf_win": 14, "leaf_lose": 2, "exp_win": 40, "exp_lose": 20, "first_win_leaf_bonus": 0 },
  "seed_policy": "per_attempt",
  "on_end": { "win": [], "lose": [] },
  "unlock": [],
  "target": { "winrate_pct": 75, "player_lv_rec": 3, "margin_note": "低獎金（=盃賽 × field_race_prize_mult 0.3）；對手等級 = 隊伍平均 −1，鉗制 2–8" }
}
```

> `lv` 可為整數或字串 `"avg-N"`／`"avg+N"`（相對玩家出場隊平均等級），載入時解析並鉗制在 [2, `level_cap`]。

### 5.6 初葉盃全三場總表（`c1_r2` 為摘要，M2 時展開成完整 JSON）

| 場次 | 資格 | 賽道（5 段） | 對手隊 | 報名費 | 勝獎 | 敗獎 | 經驗 勝／敗 | 建議等級 | 目標勝率 |
|---|---|---|---|---|---|---|---|---|---|
| `c1_r1` 初戰 | 持 ≥2 野靈 | 苔／礫／苔／礫／苔 | 見習跑手：汀羽3＋霧蕨3 | 20 | 45 | 10 | 100／45 | 3 | 85% |
| `c1_r2` 複賽 | 勝 `c1_r1` | 苔／礫／苔／苔／礫 | 霧蕨4＋風鼬4（鎮上選手） | 30 | 75 | 15 | 130／55 | ≥4 | 70% |
| `c1_r3` 冠軍賽 | 勝 `c1_r2` | 苔／礫／礫／苔／礫 | 蕨生：苔團＋碎石獾＋風鼬（Lv6） | 45 | 110（首勝 +30） | 25 | 170／70 | ≥6–7 | 55–65% |

`c1_r2` 校準提示：玩家雙隻 Lv4，AI 代打約領先 44 m；唔換人落後約 43 m。

## 6. 載入驗證（lint，遊程實作、遊測同用）

1. `kind=cup` 必有 `cup`／`round`；`kind=capture` 必有 `capture`；`capture` 場 `fee=0`。
2. `track.segs` 長度＝5，地形 id 在 5 種之內；`track.len`＝1000（M1 固定）。
3. `opponent.team` 長度 ≥1、≤6；`species` 存在於野靈表；`lv` 整數 1–`level_cap`（20）或 `avg±N`。
4. `team.min ≤ team.max ≤ 6`；`req.party_min ≥ team.min`（資格唔可低過出場最少人數）。
5. `reward.leaf_win ≥ fee + 5`（勝出必淨賺）、`leaf_lose ≤ fee`（輸唔會賺）。
6. `unlock`／`req.done` 指向存在的場次，且無環。
7. `dialogue.*` 指向存在的對話集 id（**範例中 `d_capture_win`／`d_capture_lose`、`d_wild_badger_win`／`_lose`、`d_fern_final_*` 為佔位，對話集 M1 已交 `d_fern_prematch`、`d_fern_after_r1`，`d_capture_intro`（野生碎石獾 3 句）由遊策週 2 補；缺失時 lint 警告而非阻擋**）；`on_end` 的 `do` 在 dialogue-format.md §4 列表內。
8. 旗標名須在 `flags.json` 登記（`c1r1_won`、`c1r1_lost_last`、`captured_badger`、`got_mochi`、`registered_match`…）。

## 7. 待遊測／遊程確認

- `r1_min_team`（2）：若令新手卡關，改 1＋老鐘借野靈（見 tuning-params-v2.2.md）。
- 結緣戰保底：連敗 3 次後 `handicap_m` −10？（M1 暫唔做，觀察）。
- `first_win_leaf_bonus` 是否需要；出場判定（跑過 ≥1 段）是否過鬆。
- 種子策略：`per_attempt` 時重播要存種子；M1 驗收「同一種子重播一致」用 `fixed` 即可。
