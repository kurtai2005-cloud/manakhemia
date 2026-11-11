# QA：3D 花園 H1.1（`f5985c88`）

唯讀 `code/glimmer-3d-h1` @ `f5985c88d91eb677fc0bdca94df3d71b927798b1`，tree `c9b8a64f893aedead85788c66dce27d78232b09c`。基 6d.2 `ecb2c3a3`。上一版 `9e598b3e` 已經做完，報告 `QA/qa-report-9e598b3.md` 同截圖 `QA/shots-3d-h1/` 留低做對比，冇刪。冇改 code branch，冇 merge，冇推 main。

相對 `9e598b3e` 多兩個 commit：`c26d1b94`（直立、XZ、地面網格）、`f5985c88`（`?3d=0` 時 gaitForce 掉頭仍然用 1D）。`long6c.js`、`long6d.js`、`long6dui.js`、`house.js`、`long5a.js`、`sim.js`、`hd2d.js`、`data.js` 同 6d.2 byte 一樣。有改嘅係 `behavior.js`、`render.js`，再加 `garden3d.js`。

截圖：`QA/shots-3d-h11/`。掃描：`QA/scan-v10-22.json`（16／16，`lockDiff` 空）。

畫面頂部「un…」係探測把 `s.form` 設成 `'radiant'`。`FORM_NAME` 冇呢個 key（玩家形態 id 係 `bright`）。下面唔當 bug。dir4 仍然只得 radiant 一隻，其他形態用 2D sprite 後備，同上次，唔當 bug。

## P0 — XZ 走位掛咗喺 behavior 睇唔到嘅物件

`behavior.js` 嘅 `P` 係 `D.PARAMS.beh`（`behavior.js:11`）。`moveTo` 只會喺 `typeof P.g3dWalk === 'function'` 嗰陣用 3D（`:99–101`）。gaitForce 掉頭亦只喺 `P.g3dOn()` 為 true 先用 3D（`:414`）。`g3dPickWalk`／`g3dSpot`／`g3dClampX` 同樣讀呢個 `P`（`:172`、`:193`、`:199`、`:435`、`:487`、`:834`）。

`garden3d.install` 嘅 `P` 係 `D.PARAMS`（`garden3d.js:841`），hook 寫喺父物件（`:968–994`），唔係 `PARAMS.beh`。行為機每步搵嘅 `g3dWalk` 係 `undefined`，`moveTo` 永遠落到舊 1D（`:103–106`）。`?3d=0` 嗰個保險都係睇緊一條從未被賦值嘅 `beh.g3dOn`，所以 3D 開住嗰陣 `use3d` 仍然係 false。

實測（`__qa.g3d.on()` 為 true，`autoDowngrade` 關掉，直接 `behavior.step` 40 步）：

| 目標 | 結果 |
|---|---|
| (+70, 0) | x 每步 +0.57，`dir` 1，z 一直 0 |
| (−70, 0) | x 每步 −0.57，`dir` −1，z 一直 0 |
| (0, +60)／(0, −30) | 第 0 步就 `stay`，z 仍然 0（1D 見 `tx === x` 就當到咗） |
| 屋內 (82.5, −72) | 只沿 x 行到 **62** 就停，z 一直 0 |
| 花盆 (49, 22) | 行到 x＝49、z＝0 就停 |
| 圍欄 (0, −40) | 第 0 步就停喺原點 |

62 係 `data.js:346` 嘅 `beh.rangeX` 上限 `[-62, 62]`。1D `moveTo` 會把 tx 夾進呢段（`behavior.js:103`）。屋仔 x 超出 62，寵物行到邊界就當到達，深度完全冇郁。冇穿屋、亦冇抖，因為 3D 碰撞函數根本冇跑到。

修法：`garden3d.js:968` 起五個 hook 改掛 `D.PARAMS.beh`。`g3dClampX` 嘅 2D 分支（`:992`）而家讀 `P.rangeX`，`P` 係 `PARAMS`，嗰度冇 `rangeX`，接上之後會變 NaN；要改讀 `D.PARAMS.beh.rangeX`。

單元同 `e2e-3d` 嘅 A* 斷言係直接叫 `Glimmer.garden3d.buildPath`／`followPath`，唔經 `behavior.moveTo`，所以 42／0、43／0 都捉唔到呢個斷線。

## P1 — 點地面冇 z；目標喺障礙入面會沿邊抖停唔到

地面 tap 只寫 `b.tx = tp.x`（`behavior.js:301`），冇 `b.tz`。就算上面 P0 掛對，點地面仍然只係沿住而家嘅 z 行去某個 x，去唔到點擊嘅深度，亦去唔到屋仔裡面。

修法：地面 tap 用鏡頭反投影出世界 (x, z)，寫 `b.tx` 同 `b.tz`。

算法本身（直接叫 `buildPath`／`followPath`／`stepXZ`，唔經行為機）另外有一個停唔到嘅洞。目標格被 footprint 擋住嗰陣：

- `buildPath` 用 `nearFree` 最多 4 格搵可踏格（`garden3d.js:198–209`）。屋中心 (82.5, −72) 離可踏格超過 4 格，`nearFree` 失敗，路徑退化成 `[{tx,tz}]` 呢一點（`:209`）。
- `followPath` 嘅終點仍然係原來嗰個擋住嘅點（`:240`）。`atGoal` 要求距離 ≤ 步長而且腳下唔係 blocked（`:245`）。目標喺障礙裡面，呢個條件永遠唔成立。
- `stepXZ` 八個方向有一個行得通就繼續滑（`:173–178`）。`stuck` 只喺八向全敗先至 true（`:180`）。沿住圍欄滑永遠有一個方向行得通，所以 `stuck` 唔會亮，`arrived` 亦唔會亮。

Node 量到嘅尾段（2500 步之後再睇 199 步）：

| 目標 | 尾段擺幅 | `stuck` |
|---|---|---|
| 圍欄 (0, −40)，`blocked` 回 `fence` | x 4.2、z 1.5，圍住 (1, −35) 打轉 | 從來唔係 |
| 屋內 (82.5, −72) | x 7.3、z 1.1，圍住 (92, −35) | 從來唔係 |
| 小花盆 (49, 22) | x 4.7、z 2.1，圍住 (42, 6) | 從來唔係 |

空地四向（+80,0）（−80,0）（0,+70）同埋地標「屋後 (82,−110)」「樹後 (−88,−80)」都到得到，腳下 `blocked` 空。呢段同單元 `:78–90` 一致。玩家而家睇唔到呢個抖，係因為 P0 令行為機未叫到 `followPath`。P0 一接上、目標又係障礙入面，寵物就會沿邊一直滑。

修法：目標 `blocked` 就把終點改成 `nearFree` 嗰格（`:235` 而家只喺目標係空地先 push 真終點）。距離連續幾步唔縮，或者 `stepXZ` 回 `stuck`，就喺而家嘅空地設 `arrived` 停低。屋中心要加 `nearFree` 半徑，或者失敗時由邊緣再搵，唔好退回 `[{tx,tz}]`。

A* 耗時（Node，格 8，約 35×28，2352 對可踏點，每次換目標先重建，唔係每幀）：平均 **2.04ms**，最壞 **12.2ms**（(−84, 100) → (28, −125)，42 格）。四角對四角最壞 **8.1ms**。一次點擊可以接受，唔會變成每幀 long task。

## P2

1. **Context lost 仍然冇返 2D。** `WebGLRenderer` 喺 `garden3d.js:392`，全檔冇 `webglcontextlost`。`loseContext()` 之後 `on()` 仍然 true，`draws` 19 → 74，中間像素 (255, 224, 156)，唔白、迴圈冇停，畫面停喺最後一幀。同 `9e598b3e`。修法：lost 時 `enabled = false` 再 `setQuality('low')`，restore 先再考慮拉返 3D。
2. **`render.js:626` 嘅 `this.frameNo++` 仍然喺註釋入面。** `hd2dv3.js` 同幀守衛繼續死。6d.2 遺留，行號冇因為今次 pet 區塊而改。
3. **`e2e-3d.js:181` 仍然寫死 `/home/box/keep/3d-h1/fps-4x.json`。** 呢行喺新嘅 section I 前面。目錄建唔到就拋 ENOENT，直立／四向／A* 斷言全部唔會跑。今次把 `writeFileSync` 指去 `/tmp` 之後先跑到 section I（43／0）。修法：改寫 `SHOTS` 或者 `os.tmpdir()`，而且要喺 section I 之後先寫，寫失敗唔好中斷斷言。
4. **花盆遮擋射線打唔中。** `occluded` 由鏡頭射去 (x, 20, z)（`garden3d.js:785–793`）。小屋 x＝82：z＝−40 false，z＝−60 起 true，行入只轉一次。花盆 x＝49（z＝40／30／22／10／0／−10）同 x＝−81（z＝60／40／20／0）全部 false。花盆 mesh 在（`objects.json` `pot_L`），但胸口高度 y＝20 高過盆。修法：沿寵物高度多射幾條，或者命中盆身 AABB 都當遮。

## 1. 寵物直立

`flipY` 改做 true（`garden3d.js:528–529`、`:639`、`:657`）。註釋 `:535–537`：pivot (32, 61)，腳底局部 y＝−29，`petYOffset = 29` 令腳貼地。H1 用 `flipY false` 先會頭腳倒轉。`__qa.g3d.petFlipY()` 實測 true。

dir4（`s.form = 'radiant'`，3D 開住）：

| 鏡 | frame | 畫面 |
|---|---|---|
| 向鏡頭 | `front_idle_01` | `dir4-front.png`，面喺上、腳喺下 |
| 背向屋 | `back_idle_01` | `dir4-back.png`，背殼喺上，冇面 |
| 向右 | `side_idle_04`，`flip` false | `dir4-right.png` |
| 向左 | `side_idle_03`，`flip` true | `dir4-left.png` |

`e2e-3d` section I 同一套：flipY true、上半身飽和度達標、front／side／side 鏡像／back 四個 frame 名都中。圓身側幀仍然睇到一點面，背幀同正面係兩張唔同嘅圖，頭腳冇倒轉。

九個形態（bright、soft、dust、lumi、tide、shroom、crystal、moon、ember）走後備 sprite，`frame` 係 `fallback`，`flipY` true。`form-*-front.png` 同 `form-moon-live.png`：面喺上。bright、ember 肉眼都係正立。後備圖嘅左右鏡像由 `render.js:1071` `setPetSprite(draw, { mir })` 決定，唔係 `facing.flip`。`behavior` 行向右 `dir` 1、行向左 `dir` −1，同 2D 一樣。

鏡頭：`cam-sway-neg.png`／`cam-sway-pos.png` yaw ∓0.17°（`orbit` 單位係度，夾喺 ±10，`garden3d.js:805–807`）、`cam-follow.png`、`cam-q-mid.png`、`narrow-320-front.png`。high／mid／窄屏都係正立。`setQuality('low')` 之後 `on()` false，畫面係 2D（`cam-q-low.png`、`q-low.png`），billboard 採樣唔再適用。

細佬：`__qa.s2.hatch()` 開咗孵化全畫面，`kid.png` 係正立嘅蛋同光芒，唔係倒轉。朋友影子係 WebGL 上面嘅 2D 層。`long6dui.js` 同 6d.2 相同，`SHADOW_A` 0.45（`__qa.l6d.SHADOW_A` 實測 0.45）。`flipY` 唔影響呢兩層。今次冇影到朋友剪影企喺花園入面（要成套換碼），唔當已覆蓋。

## 2. 四向同繞障

見 P0、P1。直接叫 A* 可以繞過圍欄去屋後同樹後，腳唔入 footprint。行為機做唔到同一件事。

行向同動畫：dir4 強制 `dx/dz` 嗰陣，frame 名同 `dirOf`（`garden3d.js:91–94`）一致，e2e 已核。後備形態嘅鏡像跟 `beh.dir`，1D 左右行同 `dir` 符號一致。z 方向因為 P0，行為機冇產生過 `dz`，所以 live 行路冇 back／front walk 幀。

## 3. 屋仔／花盆遮擋

小屋行入只轉一次遮擋旗（z −40 → −60）。被遮時 390 寬 CSS 命中盒 **92×119**（art 盒 40×54，`petDraw` 寬寫死 40，`garden3d.js:771–776`）。中心一撳 `notePat` +1；之後點 (18, 18) 仍然係 1，角上冇加，點擊冇穿透。`occlude-cottage.png` 寵物企喺屋後，畫面主要見草地同屋。拖鏡 `petHit` 就 return（`garden3d.js:900`），地面 tap 喺 `ui.js` 寵物盒入面先 return，同 9e598b3e。

花盆見 P2。`occlude-pot.png`、`occlude-pot-behind.png`。

## 4. 地面網格同近大遠細

网格畫喺 y＝0.08 嘅平面（`garden3d.js` 地面網格，`flipY` true）。截圖近格大、遠格小，屋同樹有透視，比例同欄、籬同一套，冇變成一塊豎起嘅板。

觸控寬唔跟透視縮。40 art px 喺 390 寬係 92 CSS，最遠 (0, −110) 同邊位 (−20, −120) 都係 **min 92**。高由近 66 art 收到遠 53 art，390 寬 CSS 高 143 → 118，仍然 ≥48。320 寬嘅近處寵物 min 命中 **70**。四個直向尺寸都 ≥48。

## 5. 鏡頭、四尺寸、畫質、後備

隱藏約 700ms：`t` 停 35.082，yaw −4.26°，look 唔變。返嚟再約 450ms：`t` 35.499（+0.42s），yaw −4.66°（差 0.4°）。係擺鏡行一小步，唔係跳。`main.js:154` 隱藏唔畫，返嚟先更新 `last`，隱藏嗰幾秒唔會變成一格大 dt。

直向四張：`vp-320x640.png`、`vp-360x640.png`、`vp-390x844.png`、`vp-412x915.png`。`petIn` 全 true。清走徽章 toast 之後 `ui62.overlap` 係 **0**（`vp-412-clean.png`）。412 喺「+5 星星碎」toast 仲喺度嗰陣 `overlap()` 報過 1 下，對唔到係邊兩個框，清走就係 0，唔另開 bug。頂欄、右欄、底欄都喺畫面內。fps 面板四個尺寸 `display: none`。

`#g3dPerf` 新開一頁（清 localStorage）`display: none`。🛠「開發者」掣係 `devmode.js:17` 預設出（`glimmer.devBtn` 未寫 0），6d.2 一樣，要入設定撳版本 5 下先收。耗電面板本身默認關（`garden3d.js:829`）。

自動降級只降唔升。`noteFrame` 先豁免 90 幀，之後每 120 幀，平均 >28ms 連續 2 窗先降（`garden3d.js:873–889`）。4× CPU 之下 8 次抽樣都係 `high:1`，冇來回跳。`e2e-3d` 嘅 4× CPU 窗口亦保持 high（fps 讀數 72 然後 240，`lastMs` 2.4／3.3）。

`?3d=0`：`on()` false、quality low、`renderer.g3On` false。像素 (90, 145, 100, 255)，唔白。`fallback-2d.png` 同 `QA/shots-6d2/390-day-autumn.png` 同一套 HD-2D 欄、燈串、籬、屋、底欄。6d.2 嗰張係秋日加朋友剪影；呢張係日景、探測形態。佈局一樣。

冇 WebGL（`--disable-webgl --disable-gpu`）：`on()` false、quality low、`g3On` false、`error` null、pageerror 空。`nowebgl.png` 係預設光卵 2D 花園（呢次冇強制成年），天、樹、籬、屋、底欄都喺，唔白。

Context lost 見 P2。

## 6. `?3d=0` 回歸

夢境真 `long6c.enter`（先 `sleeping = true` 再 `canEnter`），N＝200。同 6d.1 鎖定差 **0 日**。錢包合計 0，`SHARD_DAILY_TOTAL_CAP` 47，存量最高 1，違規 0。

| 表 | 完成 | 中位 | P10 | 最慢 |
|---|---:|---:|---:|---:|
| 勤力 | 200 | 84 | 80 | 92 |
| 普通 | 200 | 84 | 81 | 92 |
| 早起 | 200 | 84 | 81 | 92 |
| 餵食狂 | 200 | 84 | 80 | 91 |
| 夜貓 | 200 | 83 | 80 | 90 |
| 疏玩 | 199 | 147 | 132 | 179 |

scan-v10-22：16／16。火苗 14.00、柔光 10.92、微塵 4.95、螢絨 5.47、晶角 15.32、月眠 18.72、夜貓月眠 82.4、疏玩 CQ 18。星碎中位：疏玩 19、勤力 28、普通 22、夜貓 25、早起 23、餵食狂 23。舊帳最高 30，`over30` 0。跑完參數返 `w` 1、`cap` 4、`kinds.mg.w` 2。

`house.js`／`long5a.js` 同 6d.2 byte 一樣，商店 190／慢 238／家人 Lv5 71 日沿用。`hd2d.js` byte 一樣。今次再量霧格距：`?3d=0`、天氣 fog、`__qa.l6c.start()` 入到夢境 `play`、4× CPU，rAF **格距** p95 **16.6ms**（p50 0.5，樣本 804）。6d.2 係 16.7ms。3D 已知唔畫天氣霧，見第 7 節。朋友碼／手信喺冇改嘅 `long6d.js`。`e2e-6d` 115／0。`e2e-touch` 52／0。

Unit **35** 檔全數 exit 0，合計 **2333／0**。`garden3d.test.js` 42（上次 33，多咗 XZ／A* 段）、`long5a` 77／77、`long6c` 85、`long6d` 55、`behavior` 187。單元唔經瀏覽器，所以 P0 冇被捉到。

## 7. 已知未做（唔當 bug）

3D 冇雨、冇季節、冇天氣霧。夜景係日景底板乘色（`garden3d.js:596–599` backdrop，`mixLights` 夜晚乘暗藍）。dir4 只得 radiant。細佬／朋友仍然畫喺 WebGL 上面嘅 L2。

## 8. 畫質三級（4× CPU）

`Emulation.setCPUThrottlingRate` 4，swiftshader。量嘅係 **rAF callback 入面嘅耗時**，唔係 vsync 格距。目標 p50／p95 ≤17ms。long task 用 `performance.getEntriesByType('longtask')`。heap 係 `usedJSHeapSize`。low 轉咗 2D 之後 `renderer.info` 仲留住切之前嘅 draw call，表入面唔當 2D 嘅數字。

| 級 | 畫面 | 樣本 | p50 | p95 | max | >17ms | draw call | 三角 | heap | long task |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| high | 3D | 72 | 0.6 | 4.2 | 4.5 | 0 | 23 | 1082 | 27MB | 0 |
| mid | 3D | 78 | 0.6 | 4.5 | 9.7 | 0 | 24 | 1066 | 29MB | 0 |
| low | 2D | 126 | 0.5 | 2.8 | 8.3 | 0 | （殘 24） | （殘 1066） | 30MB | 0 |

三級 p50、p95 都 ≤17ms，今次冇幀超過 17ms。8 次抽樣畫質都係 high。開發伺服器載入 HTTP 404：**0**。

## 9. E2E

31 套。`e2e-3d` 用 `node -r` 把 `fps-4x.json` 指去 `/tmp`（遊戲檔冇改），先跑到 section I：**43／0**，包括 flipY、四向 frame、屋後遮擋、A* 到樹後、冇 pageerror。未改嘅腳本會喺 `:181` ENOENT，section I 唔會跑（P2）。

其餘 21 套 0 失敗：4a 114、4b 95、5a 88、5a2 75、5b 100、5c 70、6a 69、6b2 51、6b3 57、6c 103、6d 115、b3b 61、evo6 54、mg2 46、read 94、route 55、sys12 79、sys12b 48、touch 52、uikit2 70、v3 50。

9 套有紅，都唔係玩法壞咗：

1. **swiftshader 警告。** Chrome 印 `Automatic fallback to software WebGL has been deprecated…swiftshader`。3D 會開 WebGL context，所以呢句出現。只因此紅、其餘斷言全過：`e2e-hd2d` 50／1、`e2e-live` 45／1、`e2e-live2` 42／1、`e2e-playwright` 36／1、`e2e-s1` 50／1、`e2e-s2b` 24／1、`e2e-s3` 31／1。`--disable-webgl` 實測會返 2D，唔白。唔當玩家 bug。
2. **`e2e-a` 92／2。** 除咗上面嗰句警告，仲有「窗口平均 > slowMs 就降一級」冇發生（`drops` 0，畫質仍然 high）。呢部機幀太快，測試等唔夠慢窗。同 9e598b3e 嗰次 `e2e-a.js` 1800ms 太短同一類，唔係降級壞咗。今次 4× CPU 抽樣畫質冇來回跳，見第 5 節。
3. **`e2e-6b` 散步路「開」。** 全套一次 63／1。專跑 10 次：**3 次失敗、7 次 64／0**。三次失敗都係同一行，冇第二項紅：`["開", 18.46, 1.4, "GlimmerV3Sans"]`。`long6bui.js` 同 6d.2 byte 一樣。pill「開」畫喺 `btn_pri` 貼圖上（`long6bui.js:218`）。`readaudit.js:42–45` 取字形盒最差 10% 像素，`cr = min(平均, 最差×1.4)`。高光像素對比接近 1 嗰陣，讀數就係 **1.4**。字號 18.46 高過審查真正門檻 14（`readaudit.js:38`），唔係失敗原因。係對比抽樣，唔係產品回歸。唔開 bug。
