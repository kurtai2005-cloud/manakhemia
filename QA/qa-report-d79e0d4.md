# QA：6a.1（`d79e0d4c`）

唯讀 `code/glimmer-6a1` @ `d79e0d4c0da1784042b87dd727b674f6954fe7fa`，tree `19402295db113759fe0630db53e7423a248b1b36`（已對）。祖先係 6a `6a3776b2`。`sim.js` 同 5c.1／6a 逐字一樣。冇改 code branch，冇推 main。

## 1. 上輪 P1：返嚟第一下撳

`ui.js:352` 撳落團絨先問 `G.petTapGate`。旗仲在就 `return`，`press` 保持 null，所以鬆手唔跑 `tch.up`、唔跑 `sysPress`（`ui.js:362-365`）。`long6aui.js:167` 的 gate：`happy()` 播畫面，然後 `takeHappy`（`long6a.js:200` 只睇唔用的係 `happyDue`）。

獨立頁面量度（心情共用額、摸頭委託 `n`、mem6 摸頭）：

| 手勢 | 三個數 | 其他 |
|---|---|---|
| 短撳（90ms） | 保持 0 | `press` 空、`g_tickle`、心心 4、得意臉、旗清、happy 次數 +1 |
| 長撳 1.3s（呼嚕門檻 0.4s／摸頭 3s） | 保持 0 | `press` 空、冇 grant、旗清 |
| 兩指一齊撳 | 保持 0 | 冇 grant、旗清 |
| 快撳 50ms | 保持 0 | 旗清、冇 grant |

第二下短撳：心情共用額 0→1、poke grant、摸頭委託 `n` 1、mem6 摸頭 1、`lastPetPress` 有寫（93ms）。長撳第二下：`nuzzle: true`、hold grant。多指之後再單指：照計 poke。旗冇留低。

`e2e-6a` 58／0，入面有「第一下純視覺三個數 0」同「第二下照舊 sysPress」。

`takeHappy` 喺 `happy()` 返回之後即刻做。`g_tickle` 用 60ms `setTimeout` 先播，心心同得意臉係同步畫出。旗唔會等到動畫完，所以快撳第二下會計數，亦唔會卡住。

## 2. 16 項同經濟

scan-v10-13 同 scan-v10-12 的 `total`、`tables`、`econ`、`cqMed`、`nightMoon`、`over30`、`lockDiff` 逐欄一樣。16／16。火苗 14.00、柔光 10.92、微塵 4.95、螢絨 5.47、晶角 15.32、月眠 18.72、夜貓月眠 82.4、疏玩 CQ 18、新系統分 25、星碎 19／28／22／25／23／23，舊帳最高 30。

經濟檔（`systems.js`、`long5b.js`、`house.js`、`visit.js`）同 6a 逐字一樣。cap42、165 ≥5 日、213 中位 14 日內、Lv5 71 日沿用上一輪。

## 3. 測試

Unit 27／27 檔，全部 exit 0，合共 **2030／0**（同 6a）。

E2E 24 套。並行嗰陣 `e2e-4a` 111／3（細佬掣、二人彈文案、自動朋友）。單獨再跑 **114／0**。其餘套件 0 失敗。用再跑結果計，合共 **1535／0**。`e2e-6a` 58／0。

## 4. 問題

**P0／P1／P2：** 冇。上輪第一下撳計數已收。
