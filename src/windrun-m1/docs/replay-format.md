# 重播格式 `windrun-replay` v1（M1 · 4.1）

實作：`src/api.js`（`Api.getReplay / createPlayback / verifyReplay`）、雜湊：`src/sim.js` 嘅 `hashState`。測試：`node tests/replay.test.js 200`。

## 1. 設計
- 模擬係固定步長（`PARAMS.sim_dt` = 1/30 s）、可種子 RNG（mulberry32）、**無 DOM／Date／Math.random**（`sim.js`、`api.js` 由測試靜態掃描＋執行時封鎖）。
- 一場比賽 ＝ `setup`（種子、地形、隊伍、控制器種類）＋ 一串**決策**（在第 k 步開始前套用）。同樣輸入 → 逐步狀態雜湊完全一致。
- 表現層（`ui.js`／`main.js`）只可經 `Api` 操作；幀率唔影響結果（`Api.advance` 用累加器跑 0..N 個固定步；測試用 60／30／144 fps、100 ms 等 5 種幀長推進同一場，最終雜湊一致）。

## 2. 欄位
```jsonc
{
  "format": "windrun-replay",
  "v": 1,                                   // 格式版本；不符即拒絕
  "sim": { "version": 1, "dt": 0.0333…, "paramsHash": "8 位 hex" },
  "seed": 12345,                            // uint32
  "terrains": ["moss","gravel","shallows","frost","bridge"],   // 5 段 id
  "teams": [[{"id":"…","lv":3,"bonus":…,"cond":…}], [ … ]],    // 0=甲方(玩家) 1=乙方
  "ctrls": [{"kind":"player"},{"kind":"ai"}],  // kind: player｜ai｜shadow(帶 script)
  "noSwap": [false,false], "noSkill": [false,false],
  "meta": {},                               // 自由欄位（關卡 id、版本字串…）
  "decisions": [ {"k":120,"s":0,"a":"swap","i":1}, {"k":410,"s":0,"a":"skill","i":0} ],
  "checkpoints": { "every": 30, "h": ["…","…"] },  // 每 30 步＋比賽結束一個 8 位 hex（另含第 0 步）
  "result": { "over":true, "steps":2716, "winner":0, "duration":90.5, "finalHash":"…" }
}
```
- `decisions`：`k`＝步序（套用於第 k 步之前）、`s`＝邊、`a`＝`swap`｜`skill`、`i`＝換入嘅隊員索引（skill 為 0）。**所有成功決策**（玩家＋AI＋影子隊）都記錄，故回放唔使重算 AI。
- `paramsHash`：`PARAMS` 以「鍵排序 JSON」做 FNV-1a 32-bit。**改任何平衡參數 → 舊重播被拒絕**（刻意：舊重播唔可能再重現）。

## 3. 狀態雜湊 `hashState`
FNV-1a 32-bit，逐位元組餵入：`stepN`、`t`、`over`、`winner`；每邊：`pos`、`phase`、`phaseT`、`active`、`pending`、`cooldown`、`effect(type,mult,t)`、`shield`、`swaps`、`skills`、`lastSkillT`、`finishT`、`fieldTime`；每隻隊員：`stamina`、旗標（skillUsed／onField／exhausted）。浮點以 **IEEE-754 float64 little-endian** 位元組入雜湊。
**唔入雜湊**：RNG 內部狀態、AI／影子隊控制器內部狀態（`next`、`ei`）、可由上述狀態重算嘅導出值（speed／A／C／G／S）。原因：控制器只透過「決策」影響狀態，決策重現已足夠；RNG 若有偏差會即時反映喺位置／耐力。

## 4. 回放模式
| 模式 | 行為 | 用途 |
|---|---|---|
| `log`（預設） | 兩邊都唔跑控制器，只按 `decisions` 套用 | 正式重播／驗證 |
| `regen` | 玩家邊按記錄；非玩家邊由 AI／影子隊腳本重新產生 | 交叉驗證 AI 邏輯亦確定性 |
| `live` | 即時輸入，`record` 預設開 | 遊玩時錄製 |

驗證：`Api.verifyReplay(rp, {mode})` → `{ok, error, finalHash, steps, winner}`。檢查項：格式／版本／sim.version／paramsHash／dt、每 30 步檢查點、最終雜湊、步數、勝負、決策是否全部套用、決策步序是否遞增。

## 5. 版本策略
- `v` ＝檔案格式；`sim.version` ＝模擬規則（改公式結構時 +1）；`paramsHash` ＝數值參數。三者任一唔符就拒絕，不做自動遷移（重播屬短壽資料；長期紀錄用 `result` 摘要）。
- 日後加欄位（例如後端簽名、客戶端版本）→ `v` 升 2，`validateReplay` 同時接受 1。

## 6. 確定性規則（寫 sim 嘅人必須遵守）
1. 禁用 `Date`、`Math.random`、`performance`、DOM、`setTimeout`、`localStorage`（測試會掃）。
2. 所有隨機經 `makeRng(seed)`；迭代次序固定（陣列，不依賴物件鍵次序）。
3. 只用固定步長；表現層插值唔回寫 sim。
4. 任何新狀態欄位若影響結果，必須加入 `hashState` 並加測試。

## 7. 跨平台風險（未解決，如實標註）
- JS 以 float64 計算，同一 JS 引擎（V8／JavaScriptCore）加減乘除、`Math.imul` 結果一致；但 `Math.sin/cos/pow/exp` 等**超越函數在不同引擎／CPU 可能有 1 ulp 差異**。現時 sim 只用加減乘除、`Math.floor/min/max/sqrt`（`sqrt` 為 IEEE 要求正確捨入）——已 grep 確認 `sim.js`／`api.js` 冇用 `Math.sin/cos/pow/exp/log/tan/atan`。**未驗證**：JavaScriptCore（iOS Safari）同 Node 嘅逐位一致（只喺 Node 跑咗測試；需喺真機 Safari 跑 `verifyReplay`）。
- 若日後移植 Godot／Unity（C# float32 預設！GDScript 用 float64），必須固定使用 float64 或改定點數，並以呢份 replay＋檢查點做跨引擎一致性測試（plan Q15，後端週再處理）。

## 8. 使用例
```js
const m = Api.createMatch(setup, { mode: 'live' });
Api.submit(m, 0, { type: 'swap', i: 1 });
Api.advance(m, frameDt, 1);               // 每幀
const rp = Api.getReplay(m);              // 賽中／賽後匯出，可 JSON.stringify
const r = Api.verifyReplay(JSON.parse(JSON.stringify(rp)));   // {ok:true,…}
```
