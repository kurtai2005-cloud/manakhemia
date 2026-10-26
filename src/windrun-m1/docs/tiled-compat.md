# Tiled 相容性報告（遊美 tilemap／遊策生成圖 ↔ 引擎）

自動檢查：`node tests/tiled-compat.test.js`（6000+ 斷言，實測）；`src/tiled.js` 的 `check()` 產生 error／warning／info。**collision firstgid 一律由 tilemap 的 `tilesets` 讀出**（名為 `collision` 的 tileset），值＝`gid − firstgid + 1`；唔寫死。

## 1. 結果
| 檔 | 尺寸 | tilesets（firstgid） | collision firstgid | error | warning |
|---|---|---|---|---|---|
| tilemap_corner.json（舊） | 20×15 | morningmoss@1、collision@193 | **193** | 0 | 6（W_TBD×3、W_VOCAB_ART_ONLY×3） |
| tilemap_town.json（batch2） | 40×30 | morningmoss@1、morningmoss_b2@193、landmarks@385、collision@545 | **545** | 0 | 4（W_VOCAB_ART_ONLY） |
| 遊策生成 town／arena／trail | 40×30／40×15／60×16 | morningmoss_extruded@1、collision@193、placeholder@197 | 193 | 0 | 0 |

batch2 collision 值分佈（walk/block/water/trigger/slow）＝582/569/42/5/2〔實測〕。若按舊 193 解碼 batch2，會出現越界值——測試有明確斷言。

## 2. batch2 專項驗證〔實測〕
- 溝＋木橋：row27 溝格 x=10,11,12,18,22,23 → collision=2（阻擋）；木橋 (19..21,27)＝0（可走）。spawn → 溝南 (20,28) 可達；**封橋後不可達**＝木橋係唯一過溝路徑。
- spawn 可達全部 19 個 warp／npc_spawn／interact／trigger（四鄰格亦計）。
- 屋頂／樹冠在 `occlusion` 層：268 格，sort_y 全部有限（同欄向下有 collision=1 基座）。
- landmarks：22 對 day↔lit（`swap_day_to_lit`），旗／風標 4 幀動畫（共 28 個動畫 tile）。
- `door_registry → arena_windrun / spawn_from_town`；`npc_registry` (32,9)（面向上；站位格 collision=0；周邊有可達互動格）；`npc_elder` 正名老鐘。
- 返鎮落點 (20,9)／(30,9)、trail 返鎮 (38,13) 全部可走（town-map 測試）。

## 3. 欄位／規格問題
1. **事件詞彙兩套**：遊美 spawn/warp/interact/npc_spawn/trigger/light；遊策 spawn/touch/interact/auto/npc。引擎兩套都收（W_VOCAB_ART_ONLY 係提示），建議統一。
2. `cond`：遊美係表達式字串（`prologue_done and not met_fern`），遊策係 JSON 字串。引擎兩種都解析（`Tiled.condOf`）。
3. collision 層存 gid（545–548）而非 0–4；遊策 §5 寫 0／1 兩值，遊美 §C 有 0–4（含 water／trigger／slow）→ 以遊美 0–4 為準。slow 格速度倍率（遊策無）暫用 ×0.6〔估〕。
4. 無 `objects` 層（遊策 §5 要求 y-sort 建築）、無 `lights` 層（改用 `light` 事件）；建築／樹由 deco＋occlusion＋逐格 sort_y 處理。
5. 圖塊集 **非 extruded**；引擎自動換同名 `_extruded` 版（`b2_extruded.tsj` 已存在）以避免非整數縮放滲色。
6. `npc_spawn` 無 sprite／顯示名／對話 id（只有 dialog_node 及 radius）。遊程以 overlay 補（`data/overlay/town_morningmoss.json`）；NPC 圖集 id＝事件名 `npc_<id>`。
7. 互動半徑：Fern、registry radius=1.0 小過 tuning interact_range 1.5 格，引擎取 1.5。
8. 碰撞盒：遊策 11:25 定案 12×8 px（`world.js` `HW=6, HH=4`，腳底中心）。
9. `mist_zone`（trigger）已解析，**未渲染**。
10. 遊策生成嘅 arena／trail 仍用舊 placeholder tileset；待遊美出同風格圖塊。
11. 遊策 maps-and-events 嘅 events 表仍有 TBD 文字；遊程用 `d_objects_town`（遊策 npc-dialogue §4）填 6 個互動旁白。
12. （已定案 11:25／11:27）`npc_registry`＝背景職員角色，interact 走 `registry_counter_01`（同 `registry_counter`），無獨立對白；旁白為單句「櫃台後有位職員低頭整理名冊，見你近前，點頭示意：想報名，就入迴風場。」（遊策 npc-dialogue.md；舊稿「櫃台前沒有人」及第二句「窗口牌子…」已刪）。
