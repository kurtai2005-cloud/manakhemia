# QA：5c.1（`0254f89b`）

唯讀 `code/glimmer-5c1` @ `0254f89b35f3d13b4629eb5713f7207c0975c683`，tree `f0bdc9897486036d5bffc3feb541aedc198cb3cc`（已對）。祖先包括 5c `e6a2cce5`。冇改 code branch，冇推 main。

## 1. 二代團絨蛋 §7

`sim.branchRoll`（`sim.js:234-238`）把鹽固定做 `BRANCH_GEN_SALT = 1`，唔再拌 `s.gen`。第 1 代同舊公式（`tag:seed:1`）bit-identical：`branchgen.test.js` 1200/1200。第 2、第 3 代同第 1 代一樣：1200/1200。

`tests/branchgen.test.js` 有測兩個起跳點（芽崽 `{}`、光卵 `{ egg: true }`），六個作息表併成一個百分比，預設每表 N＝150。兩邊最大偏差都係 **0pt**，900 隻全部落到 9 條路。佢冇逐表列出 |Δ|。

自己再掃 N＝1000 × 6 表，同種子配對，真 `route-sweep`（drops 5、fpats 2、mg2），`o.gen` 1 對 2：

| 起跳 | 配對結局唔同 | 每表每條路最大 \|Δ\| | 全體最大 \|Δ\| |
|---|---:|---:|---:|
| 芽崽 | 0／6000 | 0.00 | 0.00 |
| 光卵 | 0／6000 | 0.00 | 0.00 |

六表（勤力、普通、疏玩、夜貓、早起、餵食狂）每一條路都係 0.00。最大偏差 **0.00pt**。

## 2. 一代回歸

scan-v10-12 同 scan-v10-11 的 `total`、`tables`、`cqs`、`cqMed`、`nightMoon`、`econ`、`over30`、`lockDiff` 逐欄一樣。16／16，`lockDiff` 空。

| 項 | 5c／5c.1 |
|---|---:|
| 火苗 | 14.00 |
| 柔光 | 10.92 |
| 微塵 | 4.95 |
| 螢絨 | 5.47 |
| 晶角 | 15.32 |
| 月眠 | 18.72 |
| 夜貓月眠 | 82.4 |
| 疏玩 CQ 中位 | 18 |
| 新系統分 | 25 |
| 疏玩星碎 | 19 |
| 勤力／普通／夜貓／早起／餵食狂 | 28／22／25／23／23 |
| 舊帳單日最高 | 30，穿 30＝0 |

舊存檔：第 1 代 `branchRoll` 同 5c 600/600 相同。已進化存檔 `deserialize` 之後 `form`／`stage`／`gen` 照留（試過 adult／moon／gen 1）。未進化的第 2 代會改用第 1 代擲骰，呢個就係今次修正；第 1 代結果冇變。

## 3. 日記 ✕

360×800，48 探針：日記關閉 **52×52，8／8**，中心打中（`long5bui.js:178`）。翻頁 56×44 仍然 8／8。`e2e-5b` 亦量到 52×52 並且撳得閂。直向 `#rotate` 係 `display:none`。

5c.1 新加的掣就係呢粒日記 ✕。安排頁關閉、分段、「好！」上一輪已過，呢次冇改佢哋的熱區碼（`long5bui.js` 只改日記關閉）。

## 4. 單檔

自己 build：`/tmp/qa-single-5c1/index.html` **47,451,322** bytes，1841 個資產。對 5c 的 47,809,165，**−357,843**。

log：`skipped 60 files 2141724 raw bytes`（5c 的 51 個檔再加 9 個 5c UI）。HTML 入面搵唔到 `parent_card_A3`、`parent_card_evo_still_moon`、`inherit_preview_bar`、`icon_trick`、`icon_pattern`、`pill_fast_on`、`pill_fast_tr`、`pill_fast_locked`、`5c/ui/layout.json`。`long_5c.json`、`swatch_wave_A3`、`chip_trick_A` 仍然在。`e2e-5a2`：9 個、262KB、runtime 冇載。

## 5. 經濟

`systems.js`、`long5b.js`、`long5a.js`、`house.js`、`visit.js` 同 5c 逐字一樣。`shardcap.test.js` 12／0：舊 ≤30、5b ≤12、合共 42、互不搶位。

家具日數沿用 `edbba957`（收入路徑冇改）。165 中位／P10：勤力 5／5、普通 6／5、疏玩 10／9、夜貓 5／5、早起 6／5、餵食狂 5／5。213：6／6、7／7、12／11、7／6、7／7、7／6。最快 5 日，213 中位 6–12 日，14 日內。家族 Lv5 仍然 71 日（門檻 420，`long5a.js` 冇改）。

## 6. 測試

Unit 26／26 檔，全部 exit 0，合共 **1988／0**（5c 的 1982 加 `branchgen.test.js` 6）。

E2E 23 套全部 exit 0，合共 **1477／0**。5a2 75（含 9 個未用 UI 跳過）、5b 100（含日記 ✕ 52×52）、5c 70。其餘：4a 114、4b 92、5a 88、a 94、b3b 61、evo6 54、live 46、live2 43、mg2 46、playwright 37、read 94、s1 51、s2b 25、sys12b 48、uikit2 70、hd2d 51、route 55、touch 52、s3 32、sys12 79。

## 7. 問題

**P0／P1／P2：** 冇新問題。上一輪日記關閉 30×30、9 個未用 5c UI、二代 `s.gen` 擲骰，呢版都收咗。
