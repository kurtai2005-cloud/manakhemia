# 存檔 JSON v1（plan 6H／A.1）

實作：`src/save.js`（`WR.Save`，DOM-free，Node／瀏覽器通用）；測試：`node tests/save.test.js`（3438 項斷言）。

## 1. 原則
1. **讀永不拋錯**：`normalize/sanitize` 對任何輸入（壞 JSON、缺欄位、越界值、型別錯、`__proto__`）都回傳合法 v1 存檔或明確錯誤碼。
2. **版本只升不降**：存檔 `version` 大於程式支援 → `{ok:false, reason:'too_new'}`，**唔准覆寫**（避免舊客戶端毀新存檔）。
3. **遷移鏈**：`MIGRATIONS[n]` 係 vN→vN+1 嘅純函數，逐級串接；每步加測試固定輸入／輸出。
4. **規範化序列化**：鍵排序 JSON（同內容同字串），方便校驗、diff、雲端比較。
5. 存檔只放「玩家狀態」，**唔放可由 PARAMS／素材重算嘅資料**（屬性值由 species＋lv＋bonus 計）。

## 2. 欄位表
| 路徑 | 型別／範圍 | 預設 | 說明 |
|---|---|---|---|
| `format` | `"windrun-save"` | | 固定 |
| `version` | int（現 1） | 1 | 遷移依據 |
| `rev` | int 0..1e9 | 0 | 每次 `Store.save` +1；衝突判斷用 |
| `deviceId` | `[A-Za-z0-9_-]{3,40}` | 隨機 `dev-xxxxxxxx` | 區分裝置 |
| `createdAt`／`savedAt` | int ms epoch | 0 | |
| `player.name` | ≤12 字（Unicode 碼點） | 旅人 | 去除控制字元 |
| `player.leaf` | int 0..99999999 | 0 | 貨幣（暫名「葉」，待設計定名） |
| `player.seals` | `seal_1..3` 子集（排序去重） | [] | 三枚印記 |
| `player.pos` | `{map,x,y,dir}`；x,y 0..4096（格，可小數）；dir ∈ d/l/r/u | town_morningmoss(20,22,u) | 離開前位置 |
| `player.appearance` | id | default | |
| `party` | ≤6 隻 creature | [] | 隨行隊伍 |
| `habitat` | ≤60 隻 | [] | 棲息地（後備） |
| `presets` | 3 組 × ≤3 個 iid | [[],[],[]] | 組隊預設；引用不存在 iid 會被剔除 |
| `seq` | int | 1 | 下一個 iid 序號；必 > 現有最大 iid |
| `dex.seen／owned` | species id 排序去重（≤200） | [] | owned ⊇ 持有者；持有者自動補入 |
| `cleared` | matchId 排序去重（≤200） | [] | 已通關比賽，例 `cup.fernshade.m1` |
| `flags` | `{旗標名: bool｜int｜string≤32}`，≤400 個 | {} | 故事／事件旗標（命名見 §5） |
| `chapter` | `{id, step}` | ch1／start | 主線進度 |
| `stats` | races, wins, playSec, ribbons, turn, actionsLeft | 0,0,0,0,1,3 | 養成回合沿用 MVP |
| `settings` | sound(bool)、lang(zh-HK/en/ja)、touchMode(tap/joystick)、fxQuality(auto/off/low/mid/high)、textSpeed(1–3) | | |

**creature**：`{iid, species, nick≤12, lv 1..99, exp, bonus{speed,power,calm,stamina 0..999}, cond 0..100, skills[≤4], evo{done[], flags[]}, caught{map,t}}`。非法 creature（缺／錯 `species`、`iid`）整隻丟棄；重複 `iid` 保留第一隻。

### id 規則（正規表示式）
| 類 | 規則 |
|---|---|
| species／map／chapter／step | `^[a-z][a-z0-9_]{0,31}$` |
| iid | `^c[0-9]{1,8}$`（實例序號，唔重用） |
| skill／appearance | `^[a-z][a-z0-9_]{0,23}$` |
| flag | `^[a-z][a-z0-9_]*(\.[a-z0-9_]+){0,4}$`（第 2 週起單段 snake_case 合法，對齊遊策 `prologue_done` 等；仍容許最多 5 段點分） |
| 一次性事件 key（evKey） | `^[a-z][a-z0-9_:.]{0,47}$`，例 `ev:town:ev_elder_intro`、`match:trai:cap_trail_badger` |
| matchId | 同 flag 但容許單段 |

## 3. 遷移與相容
- **v0（MVP 舊存檔）**：`{v:1, creatures:{id:{lv,exp,bonus,cond}}, ribbons, turn, actionsLeft, cleared:{"1":true}, races, sound}`（舊鍵 `windrun_save_v1`）→ v1：creature 按 id 排序重編 `c1…`，前 6 隻入 `party`、其餘入 `habitat`；`cleared` 轉為 `legacy.stage<N>`；寫入旗標 `meta.migrated_from_v0=true`；`deviceId` 為 `dev-migrated`。
- 無法辨識嘅輸入 → 回新存檔並帶 `warnings:['unrecognized']`、`fresh:true`（由呼叫方決定係咪提示玩家）。
- 新增欄位原則：只加唔刪；加欄位但語義向下相容可唔升版（sanitize 補預設）；改語義／改型別必升版並加遷移。

## 4. 存檔碼（跨裝置手動搬運）
`WRS1.<base64url(規範化 JSON 的 UTF-8)>.<FNV-1a 8 位 hex>`。`toCode / fromCode`。校驗只防複製殘缺（`checksum`、`bad_code`），**不防作弊**——防作弊靠後端重算（plan 6／後端週）。解碼後仍經 `normalize` 清洗。

## 5. 命名慣例（接 plan Q13）
旗標：小寫＋底線，點分命名空間，例如 `story.ch1.met_elder`、`npc.fern.talked`、`cup.fernshade.m1`、`meta.migrated_from_v0`。型別：bool（一次性事件）、int（計數／階段）、短 string（分支選擇）。**只增唔改名**；改名要寫遷移。

### 5.1 第 2 週對齊（遊策 dialogue-format／match-data-format）
- 旗標、變數、事件 key 都存於 `flags`（見 `docs/flags.md`）；`registered_match`、`fern_attitude`、`elder_gift_count`、`last_town_door` 係存檔 var（`last_town_door` 為字串變數，`set_var`）。
- `party_size`、`seals`、`leaf` 係**派生值**（party.length／player.seals.length／player.leaf），唔存；`add_var party_size` 靜默忽略（引擎按隊伍人數自動維護）。
- `chapter.step` ＝當前任務 id（`objective` var／`set_objective`）。
- 隊伍由 `save.party` 派生；`spirit_follow` 按 `got_mochi` 旗標生成並跟隊首野靈。
- 返鎮落點由 `last_town_door` 決定：door_arena → (20,9)、door_registry → (30,9)。

## 6. 儲存轉接器 `Store(adapter, key)`
- `adapter = {getItem,setItem,removeItem}`（`localStorage` 或測試假物件）。
- `load(now)`：依序嘗試主檔 `windrun_save` → 備份 `windrun_save.bak` → MVP 舊鍵 `windrun_save_v1` → 新存檔；回 `{save, source, warnings, from}`；若遇 `too_new` 回 `{tooNew:true}`（呼叫方必須唔寫入）。
- `save(s, now)`：`rev+1`，先經 `normalize`；寫主檔前將**有效**舊主檔複製為備份（壞檔唔會覆蓋好備份）；quota／例外 → `{ok:false, reason:'storage'}`，唔拋錯。
- 限制：localStorage 約 5 MB（**待核實**各瀏覽器）；v1 存檔實測遠小於此（見測試輸出）。iOS Safari 長期未使用可能清理網站資料（**待核實**）→ 需「存檔碼」同日後雲端存檔做保險。

## 7. 雲端衝突（plan 4.5）— 判斷輔助 `conflict(local, remote)`
1. 同 `deviceId`：`rev` 大者勝（`same_device_rev`）。
2. 不同裝置：一邊嘅 `cleared／seals／dex.owned` 為另一邊嘅超集 → 取超集者（`superset`）；互為超集 → 取 `progressScore` 高者。
3. 否則 `winner:'ask'`（`diverged`，附兩邊分數）：**兩份都保留，由玩家揀**，絕不自動覆寫。
`progressScore = cleared×1000 + seals×5000 + dex.owned×50 + Σlv×3 + races + flags數×5`（粗略指標，可調）。

## 8. 已知缺口
- 未做：存檔加密／簽名（不需要，後端權威）、增量／差異同步、雲端 API（後端週）。
- `player.leaf` 等貨幣欄位名待設計確認；若加入物品欄（背包）需 v2 或擴充欄位。
