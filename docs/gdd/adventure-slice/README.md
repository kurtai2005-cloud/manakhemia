# 《風野競走》冒險切片規格（遊策 週 1）

> 遊策｜週 1｜草稿 v1｜依據 `../wind-race-modern-plan.md`（新版：A 結構骨架＋⑥冒險模式，重點第 6、8、10 節）及 `../wind-race-one-pager-v2.md`
> 範圍：M1 冒險垂直切片 —— 晨苔鎮 → 迴風場（報名／入場／佈陣／開賽／結算）→ 蕨影小徑（結緣）。
> 全原創；無第三方名稱／文字／數值；無私人檔內容。**所有數值暫定、可調**；模擬數字（單一種子、AI 代打）只作方向參考。

## 檔案清單與交付對象

| # | 檔案 | 內容 | 主要交付對象 | 計劃項 |
|---|---|---|---|---|
| 1 | [`match-data-format.md`](match-data-format.md) | 賽事資料格式（cup／match schema、資格、獎勵、解鎖、lint）＋範例：初戰、結緣戰、冠軍賽、野地賽 | **遊程**（載入／報名檢查）、**遊測**（數值驗證） | A.4 |
| 2 | [`maps-and-events.md`](maps-and-events.md) | 晨苔鎮／迴風場／蕨影小徑 ASCII 草圖、事件點（傳送／NPC／報名處／入場／起跑線）、碰撞與圖層規則 | **遊程**（地圖引擎）、**遊美**（圖塊美術）、**遊測**（觸控手感） | 6.1／6.3a／6.4a／6.5a |
| 3 | [`prologue-script.md`](prologue-script.md) | 序章劇本（約 1,000 字）：主角、世界觀、首場目標賽事 | **遊策／遊美**（鏡頭與表情）、**遊音**（BGM／stinger 提示）、**遊測**（跳過／斷點） | 6.7a |
| 4 | [`dialogue-format.md`](dialogue-format.md) | 對話 JSON 格式 `dialogue/v1`（節點／說話者／文字／選項／條件／事件）＋完整範例＋lint | **遊程**（對話系統／匯入器）、**遊測** | 6.2 |
| 5 | [`npc-dialogue.md`](npc-dialogue.md) | 第 1 章首段 3 個 NPC 對話表（老鐘／蕨生／桑姨，約 1,000 字）＋旗標生命週期 | **遊程**（匯入）、**遊美**（頭像表情）、**遊測**（分支） | 6.7a／6.3a |
| 6 | [`cue-table.md`](cue-table.md) | 演出 cue 表：入場／換棒／技能／衝線／結算（id、觸發、鏡頭、特效、音效 id）＋新增音效清單 | **遊音**（核對 `windrun-audio` 暫定對應）、**遊美**、**遊程**、**遊測** | 1.2a／1.3a／1.4a／1.6／6.4a |
| 7 | [`tuning-params-v2.2.md`](tuning-params-v2.2.md) | 參數表 v2.2：v2 核心沿用、冒險／結緣／cup 經濟新增、進度表、目標勝率與校準、流程時限 | **遊測**（平衡）、**遊程**（參數載入） | A.4／6.4a |

（任務原列 6 項；對話表另獨立成 `npc-dialogue.md`，序章只保留劇情。）

## 各角色快速入口

- **遊程**：先讀 `dialogue-format.md`、`match-data-format.md`（資料載入）→ `maps-and-events.md`（地圖 id、事件 id、圖層）→ `cue-table.md` §1（賽前觸發）。範例 JSON 可直接當單元測試輸入（已用 Python `json.loads` 驗證可解析）。
- **遊美**：`maps-and-events.md` 的圖塊／圖層與碰撞規則、`npc-dialogue.md` 的表情清單（每位 NPC 4 張頭像：美術 `neutral`／`happy`／`worried`／`surprised`，與對話 `emote` 對照見 dialogue-format.md §2）、`cue-table.md` 特效欄。
- **遊音**：`cue-table.md`（音效 id 已對照 `windrun-audio/README.md`；**§8 列出 ★ 建議新增**，M1 必須者：`stinger_entry`、`sfx_countdown_tick`、`jingle_capture`）、`dialogue-format.md` §2 說話者 blip 對應。
- **遊測**：`tuning-params-v2.2.md` F／H 組（校準＋待測）、`match-data-format.md` §6 lint、`cue-table.md` §9 檢查清單、`maps-and-events.md` 觸控／碰撞提示。

## 全切片共用名稱（統一 id）

| 類別 | id |
|---|---|
| 城鎮／場景 | `town_morningmoss`（晨苔鎮）、`arena_windrun`（迴風場）、`trail_fernshadow`（蕨影小徑） |
| NPC | `npc_elder`（老鐘）、`npc_fern`（蕨生）、`npc_sang`（桑姨）、`npc_wild_badger`（野生碎石獾） |
| 賽事 | `c1`（初葉盃）、`c1_r1`（初戰）、`cap_trail_badger`（結緣戰） |
| 主要旗標 | `prologue_done`、`got_mochi`、`captured_badger`、`registered_match`（字串變數）、`formation_done`、`c1r1_won`、`c1r1_lost_last`、`met_fern`、`met_sang`、`seen_fern_prematch` |
| 主要變數 | `leaf`、`party_size`（唯讀、引擎維護）、`seals`、`elder_gift_count`、`fern_attitude`、`last_town_door`（字串，`set_var`） |

> 場景 id 全切片統一（地圖檔與賽事資料一致）。
> 角色歸屬：老鐘＝第 1 章村長（`npc_elder`）；石伯＝第 2 章石磯港老領隊，另一角色，唔好混用。
> `party_size` 由引擎按隊伍人數自動維護，**唯讀**；`last_town_door` 係字串變數（值 `door_arena`／`door_registry`），用 `set_var`，唔係旗標。

## M1 玩家主線（一圖睇晒）

```
序章(P0–P3) → 取得苔團 → [老鐘：去小徑結緣] → 蕨影小徑：結緣戰 cap_trail_badger → 得碎石獾（party_size=2）
            → 迴風場：桑姨報名 c1_r1（20 葉幣）→ 入場通道 → 看台（隊伍介紹／佈陣）→ 起跑線 → 倒數 → 賽事（約 90 s）
            → 結算（葉幣／經驗／升級）→ 蕨生賽後對話 → 回城
```

## 已知限制／待確認

1. 模擬數字來自 `windrun-m1/src/sim.js`（單一種子為主；換種子後差距幾乎不變，隨機性低）。真正勝率要靠玩家行為模型或實測。
2. 配置不變前提下，M1 驗收「碎石獾必須先結緣才可報名初戰」；`r1_min_team` 正式流程維持 2；走路切片／dev 可用 dev 旗標放寬，唔加借野靈對白（見 tuning-params-v2.2.md C 組）。
3. 蕨生冠軍賽、複賽、野地賽等 M2 內容只以資料範例展示格式，不在 M1 範圍。
4. 劇情字數：序章約 1,000 字＋NPC 約 700 字（純對白），低於 M1 上限（≈2,000 字）。
5. 本目錄只含文字設計文件，無美術／音訊檔；**未推送 GitHub、未發佈、無花費**。

## 原創性自查

- [x] 名稱：風谷／風脈／喚風祭／風印／葉幣／晨苔鎮／迴風場／蕨影小徑／老鐘／蕨生／桑姨／苔團／碎石獾等全部自擬；無沿用第三方遊戲名稱、角色、對白、地圖或數值
- [x] 全部對白、劇本、參數、資料範例為自行撰寫／設定；數值列為可調
- [x] 無引用任何私人檔案內容或路徑（僅引用本 repo 的 `wind-race-*.md`、`windrun-m1`、`windrun-audio` 作對照）
- [ ] 待辦（上線前）：商標檢索（地名／角色名／cup 名）、劇情／對白原創性複查（遊測＋Kurt）
