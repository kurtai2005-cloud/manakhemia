# QA：3D 花園 H1.2（`136dee5d`）

唯讀 `code/glimmer-3d-h1` @ `136dee5d4364369db4dd501f38aa8cce8d70e7c9`，tree `7198c84201a60c4274ee6a365a66b8e0761f6c09`。APK `versionCode` 9、`versionName` `1.4.2-3d`（`native/android/README.md:43`）。冇改 code branch，冇 merge。上一輪 `f5985c88` 報告留低。

截圖：`QA/shots-3d-h12/`。掃描：`QA/scan-v10-23.json`。

`long6c.js`、`house.js`、`long5a.js`、`sim.js`、`hd2d.js`、`data.js`、`long6d.js`、`long6dui.js`、`tests/readaudit.js` 同 6d.2 byte 一樣。

畫面「un…」係探測把 `s.form` 設成 `'radiant'`。`FORM_NAME` 冇呢個 key。唔當 bug。

## 上輪 P0 — 立體行已接到行為機

`bindBehHooks` 掛喺 `D.PARAMS.beh`（`garden3d.js:1154`、`:1158–1196`）。五個都係 function：`g3dWalk`、`g3dOn`、`g3dPickWalk`、`g3dSpot`、`g3dClampX`。父物件 `PARAMS.g3dWalk` 係 `undefined`。

`g3dClampX` 2D 分支讀 `beh.rangeX`（`:1191–1193`）。`S.on()` 為 false 時 `g3dClampX(200)` ＝ **62**，唔係 NaN。`rangeX` 係 `[-62, 62]`（`data.js:346`）。

經 `behavior.step`（唔係直接 `buildPath`），速度用 `walkSpeed` 15 再乘 `walkStep3d`（`garden3d.js:142–144`，20/15）：

| 目標 | 結果 | 秒 | 腳下 |
|---|---|---:|---|
| (+80, 0) | (80.1, 1.9) stay | 3.55 | 空 |
| (−80, 0) | (−78.2, 0.7) stay | 3.52 | 空 |
| (0, +60) | (1.1, 58.7) stay | 2.63 | 空 |
| (0, −30) | (1.2, −28.6) stay | 1.38 | 空 |
| 屋後 (82, −110) | (83.9, −109.7) stay | 10.98 | 空 |
| 樹後 (−88, −80) | (−87.7, −78.4) stay | 9.45 | 空 |
| 大花盆後 (−81, 40) | (−82.7, 39.9) stay | 5.62 | 空 |

z 會變。四向都停喺目標 2 單位內。繞屋、樹、花盆唔入 footprint。屋內 (82.5, −72) 不再卡喺 x＝62：`snapDest` 去 (44, −109)，12.63 秒後停喺 (45.9, −109)，距離 snap 1.85，腳下空。

`e2e-3d.js:296–304` 用 `Glimmer.behavior.step` 行去 (20, 36)，斷言 `z > 4`。全套 **52／0**，同遊程自報一樣。fps 寫 `process.env.FPS4X` 或 `/tmp/g3d-fps-4x.json`（`e2e-3d.js:181`），唔再寫死 `/home/box/keep`。

## 上輪 P1 — 撳地有 z，被擋會停

地面 tap 寫 `b.tx`，`tp.z != null` 就寫 `b.tz`（`behavior.js:301`）。`tap()` 把 `opt.z` 存落隊列（`:231`）。UI 用 `artToGround` 反投影再 `tap(..., { z: w.z })`（`ui.js:355–361`）。Node：`tap(ground, 40, {z:25})` 之後 `state=follow`、`tx=40`、`tz=25`，第一步 z 已經 0.43。

`snapDest` 用 12 格（96 單位）搵最近可企格（`garden3d.js:226–257`，`NEAR_FREE_R = 12`）。`followPath` 冇進展 16 步就 `stuck` 兼 `arrived`（`:228`、`:359–361`）。`g3dWalk` 同樣用 `_g3dStall >= 16`（`:1177`）。

10 個被擋目標，全部 `stay`、距離 snap ≤1.91、腳下碰撞 0：

| 名 | snap | 秒 | dist |
|---|---|---:|---:|
| 屋中心 | (44, −109) | 12.63 | 1.85 |
| 小花盆 | (36, 3) | 1.50 | 1.91 |
| 圍欄 | (4, −29) | 1.28 | 1.75 |
| 屋 2 | (36, −109) | 12.98 | 1.80 |
| 樹 | (−108, −69) | 8.23 | 1.76 |
| 屋 3 | (124, −37) | 5.83 | 1.72 |
| 花盆 2 | (36, 3) | 1.50 | 1.91 |
| 圍欄 2 | (−4, −69) | 12.75 | 1.88 |
| 屋 4 | (36, −85) | 13.73 | 1.69 |
| 圍欄 3 | (−44, −69) | 11.02 | 1.75 |

冇再沿邊不停擺。`buildPath` 喺 `nearFree` 仍然失敗時仲會回傳單點（`:315`）。今次 10 個都 snap 成功，冇走到呢條。

行速：`WALK_SPEED_3D = 20`（`garden3d.js:17`），`data.js` 嘅 `walkSpeed` 仍然 15。心情 ≥70 會 `walk_happy` ×1.15（`data.js:374`）。今次種子心情 80，由 x＝0 行到 118.3 用 5.22 秒，約 **22.7 u/s**（20×1.15＝23）。H1.1 行為機未接到 hook，live 係 15 u/s（開心約 17.3）。橫越 `RANGE3` 全寬 280 單位：而家開心約 12 秒，上一輪約 16 秒。

## 上輪 P2

Context lost：`webglcontextlost` 同 `webglcontextrestored` 都有 listener（`garden3d.js:520–527`）。`on()` 要求 `!this.lost`（`:432`）。`loseContext()` 之後 `lost` true、`on()` false，3D 停畫，主迴圈返 2D 路徑。`restoreContext()` 喺呢個 headless 800ms 內事件冇到，`lost` 保持 true。listener 會 `_build` 再 `lost=false`。真機先至睇得到返 3D。唔再算未修。

`render.js:626` 而家係 `this.t += dt; this.frameNo++;`，唔再吞喺註解。`hd2dv3.js:82` 用 `b.fn !== R.frameNo` 擋同拍。`e2e-3d.js:319–324` 斷言 `frameNo` 加 1，52／0 入面過咗。

花盆：`occluded` 射 y＝8／16／24（`garden3d.js:934–937`）。x＝49、z＝22 同 z＝8：合併結果 true，只得 y＝8 打中（盆高約 19，y＝16／24 穿過盆頂）。z＝40 同 z＝0 三條都 false。小屋 z＝−70、−110 三條都 true；z＝−40 三條都 false。`occlude-pot.png`、`occlude-house.png`。

three.js MIT：`src/glimmer-a/src/vendor/LICENSE.three.txt`（Copyright 2010–2023）。`src/vendor/README.md:4` 指向呢個檔。

## 鏡頭、網格、四尺寸

直向四張：`vp-360x640.png`、`vp-390x844.png`、`vp-412x915.png`、`vp-768x1024.png`。樹、籬、燈、屋、寵物都喺畫面。`petIn` 全 true。`ui62.overlap` 全 **0**。`flipY` true，frame 係 `front_idle_*`。`gridOn` 全 false。fps 面板 `display: none`。`#rotate` 直向 `none`。

768×1024 遊戲欄喺中間，左右係放大模糊嘅延伸底，欄內 UI 冇裁。橫向 844×390：`#rotate` `display:flex`，畫面係「請轉直向」（`index.html:23`，`land-844x390.png`）。橫向唔會當直向玩。

網格預設關：`KEY_GRID` 預設 `'0'`（`garden3d.js:1035`）。新開頁 `gridOn()` false。開發者有「地面網格（預設關）」（`:1146`）。

隱藏約 600ms：yaw 同 `t` 停喺 4.89°／6.400。返嚟 0.37 秒，yaw 4.60°（差 0.29°）。係擺鏡行一小步。

`?3d=0`：`on()` false、quality low、`g3On` false。`fallback-2d.png`。冇 WebGL：`on()` false、quality low、`error` null、pageerror 空。`nowebgl.png`。

## P2 — 三級畫質 callback p95 高過 4.5ms

4× CPU、swiftshader。量嘅係 rAF callback 耗時，唔係格距。long task 0。8 次抽樣畫質都係 high，冇來回跳。

| 級 | 畫面 | 樣本 | p50 | p95 | max | >4.5ms | draw | 三角 | long task |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| high | 3D | 68 | 0.7 | **5.7** | 36.3 | 15 | 23 | 1094 | 0 |
| mid | 3D | 78 | 0.8 | **7.8** | 12.1 | 18 | 23 | 1094 | 0 |
| low | 2D | 86 | 0.6 | 4.4 | 11.0 | 5 | （殘 23） | （殘 1094） | 0 |

p50 仍然低過 1ms。high／mid 嘅 p95 過咗今次 ≤4.5ms 呢條線。`e2e-3d` 自己嘅 4× 窗口 `lastMs` 係 4.5 然後 1.6，仍然 high。修法：mid 再縮 shadow map，或者呢條線改量格距。low 嘅 draw call 係切去 2D 之前留低嘅 WebGL 數字。

## 回歸

夢境真 `long6c.enter`，N＝200，違規 0，cap 47，存量最高 1，錢包 0。

| 表 | 完成 | 中位 | P10 | 最慢 |
|---|---:|---:|---:|---:|
| 勤力 | 200 | 84 | 80 | 92 |
| 普通 | 200 | 84 | 81 | 92 |
| 早起 | 200 | 84 | 81 | 92 |
| 餵食狂 | 200 | 84 | 80 | 91 |
| 夜貓 | 200 | 83 | 80 | 90 |
| 疏玩 | 199 | 147 | 132 | 179 |

五表 200／200、中位 83–84、P10 80–81。疏玩 199／200、中位 147。同 6d.1 差 0 日。

scan-v10-23：16／16，`lockDiff` 空。火苗 14.00、柔光 10.92、微塵 4.95、螢絨 5.47、晶角 15.32、月眠 18.72、夜貓月眠 82.4、疏玩 CQ 18。星碎 疏玩 19、勤力 28、普通 22、夜貓 25、早起 23、餵食狂 23。舊帳最高 30，`over30` 0。`house.js`／`long5a.js` 同 6d.2 一樣，傢俬 190、小販 238、家族 Lv5 71 日沿用。

Unit 35 檔全部 exit 0。尾行加總 **2356／0**（`garden3d.test.js` 65，上一輪 42）。遊程自報 2425／0；今次冇失敗檔。

## e2e-6b「開」

`readaudit.js` 同 6d.2 一樣。`:45` 仍然係 `cr = min(平均, 最差×1.4)`。pill「開」坐喺 `btn_pri` 高光上，最差一成像素對比近 1 就會讀成 1.4。字號 18.46 高過審查門檻 14（`:38`）。係抽樣，唔係 H1.2 回歸。全套一次嘅結果見下面。

## e2e-6d ×10

`e2e-6d.js` 加咗 `fontOn`（`:38–50`）等字型上到先審，24 粒鐘改為直接 `long6d.process` 再等 visits 清空（`:141–157`）。

十次：**24 粒鐘 visits 10／10 過**（「過咗 24 粒鐘 → 影子全部走」每次都 ✓）。字型審核 **5／10** 全套 115／0（第 1、2、3、6、10 次）。另外 5 次只紅字型，冇其他項：

- 第 4、5、8 次：入碼／預覽「貼上朋友碼…」有效字號 11.77（低過審查 14），或者「貼上／揀相／睇吓」對比 1.00–1.12。對比 1.x 同「開」一樣，係 `:45` 最差一成乘 1.4。
- 第 7、9 次：`?v3=0` 主面板三段 Noto Sans HK、有效字號 11.77–12.31，對比 13 以上。`fontOn` 只要求 selector 入面有一段字型到位，其餘段仲未縮放就開始審。

修法（測試）：`fontOn` 等晒可見文字 `eff ≥ 14` 先 `audit`。唔當產品 P。

## P3 — 冇

產品面冇新開 P3。字型 5／10 同 headless 未打到 `contextrestored` 都寫喺上面，唔另開。

## E2E 全套

31 套。`e2e-3d` **52／0**（含 `behavior.step` 的 z、hook 掛 `PARAMS.beh`、網格預設關、花盆遮擋、`frameNo++`）。fps 寫入 `/tmp`，唔使再改路徑。

21 套 0 失敗：3d 52、4a 114、4b 95、5a 88、5a2 75、5b 100、5c 70、6a 69、6b2 51、6b3 57、6c 103、b3b 61、evo6 54、mg2 46、read 94、route 55、sys12 79、sys12b 48、touch 52、uikit2 70、v3 50。

10 套有紅，玩法斷言冇壞：

1. **swiftshader 警告only。** `e2e-hd2d` 50／1、`e2e-live` 45／1、`e2e-live2` 42／1、`e2e-playwright` 36／1、`e2e-s1` 50／1、`e2e-s2b` 24／1、`e2e-s3` 31／1。`--disable-webgl` 實測返 2D。
2. **`e2e-a` 92／2。** 同一句警告，加上降級窗口等唔夠（`drops` 0，畫質仍然 high）。呢部機幀太快。8 次抽樣畫質冇跳級。
3. **`e2e-6b` 63／1。** 只係「開」對比 1.4。見上節，`readaudit.js:45`。
4. **`e2e-6d` 114／1。** 24 粒鐘過咗。紅嘅係 `?v3=0` 字型，同十次入面第 7、9 次同一行。

今次冇 P0，冇 P1。
