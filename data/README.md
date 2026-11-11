# 《微光小圃》Godot M1 資料表

給遊程直接載入 Godot 4。鍵用英文 snake_case；顯示名用繁中。每個區塊有 `_src`。找不到嘅數值係 `null`，列喺該檔頂嘅 `_missing`。code 同文件唔一致時以 code 為準，差異寫喺 `_doc_vs_code`。

| 檔 | 主要鍵 | 單位 |
|---|---|---|
| `economy.json` | `stardust_daily_caps`, `day_change`, `jobs`, `trips`, `steps_6b`, `furniture`, `vendor_decorations`, `family_level`, `dream_6c`, `minigame_ember` | 星星碎；家族 XP；鐘點（本機）；夢碎片（唔入碎上限）；火苗路線分；秒；張／片 |
| `evolution.json` | `routes`, `stages`, `care_windows`, `scoring`, `thresholds`, `series2` | 路線分 pt；CQ 0–100；%；秒／日；親密點；系分（夢 +1／堂 +1） |
| `personality.json` | `axes`, `types`, `birth`, `daily_shift`, `inheritance`, `idle_weight`, `m1_motion`, `needs`, `spontaneous`, `family_interactions` | 軸 −10…+10；%；秒／分鐘；需求 0–100；每小時／每日次數 |
| `hunting.json` | `team`, `hunt`, `long_trip_unchanged`, `badges`, `hunt_level`, `areas`, `team_carry` | 星星碎；果（粒）；小時；每日次數；討伐證張數；狩獵 Lv |

來源：`/workspace/glimmer-3d-h1/src/glimmer-a/src/`（long6c 同 6d.1 `7068c2520` 一致）同 `/home/box/keep/docs-gdd/`、`/workspace/game-design/docs-gdd/`。未讀 `monster-race-ps1-analysis.md`。`QA/qa-econ-6c-dream.md` 喺呢部機搵唔到，夢境數字以 `long6c.js` 為準。
