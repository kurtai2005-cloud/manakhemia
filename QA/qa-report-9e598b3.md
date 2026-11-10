# QA：3D 花園 H1（`9e598b3e`）

唯讀 `code/glimmer-3d-h1` @ `9e598b3e332b6bf7d9fcaf69b716d2e05c902179`，tree `b4024cc86deb1c13c4143d8553fa998061f00ecb`。基 6d.2 `ecb2c3a3`。冇改 code branch，冇 merge，冇推 main。

`long6c.js`、`long6d.js`、`long6dui.js`、`house.js`、`long5a.js`、`sim.js`、`hd2d.js`、`hd2dv3.js`、`ui.js`、`data.js` blob 同 6d.2 一樣。有改嘅係 `render.js`（3D 合成）、`main.js`（`garden3d.install`）、`index.html`（加 `three.min.js`／`garden3d.js`）、`tools/build-single.py`（`art/garden3d` png 外置）。

截圖：`QA/shots-3d-h1/`。掃描：`QA/scan-v10-22.json`（16／16）。

畫面頂部「un…」係探測把 `s.form` 設成 `'radiant'`。`FORM_NAME` 冇呢個 key（形態 id 係 `bright`）。玩家正常形態唔會出呢行。下面唔當 bug。

## 1. 寵物 billboard 被前景遮擋

樹後（−88, −80）`occluded` 為 true，前排 (0, 0) 為 false。由前排行入樹後 13 步，遮擋旗只轉一次：`0,0,0,0,0,1,1,1,1,1,1,1,1`，冇行入行出閃。`occlude-tree.png` 樹幹蓋住身體，頭仲露出左邊。

深度：寵物係 `MeshLambertMaterial`，`alphaTest: 0.5`，寫深度（`garden3d.js:371`）。背景板 `depthWrite: false`、`renderOrder: -10`（`:352`、`:359`）。`occluded`（`:621–633`）由鏡頭射去寵物 y＝20，打中 `userData.id !== 'pet'` 而且命中距離 +1 短過寵物，先當被遮。

被遮嗰陣仍然撳得中。390 寬度 CSS 命中盒 **92×123.5**（≥48）。中心一撳 `notePat` +1；左上角 (12, 12) 唔加。`petDraw` 寬寫死 40 art px（`:611–615`），CSS 再按版面放大，四個尺寸實測 70×99、70×99、92×130、97×138。

點擊唔會穿透去背後物件。全屏 `#hit` 用呢個 AABB（`render.js:715` 寫入 `petRect`，`ui.js:349`）。入咗寵物盒就 return（`ui.js:350`），唔會落到 `:354` 嘅地面 tap。拖鏡如果 `petHit` 就 return（`garden3d.js:740`），唔會當拖空地。3D mesh 冇自己嘅 click listener。

## 2. 鏡頭 sway／follow

`swayYaw`（`garden3d.js:60–64`）係 `−A·cos(π·t/T)`，A＝5°、半周期 6 秒，單程緩入緩出。跟拍係指數阻尼（`:74–76`）。`Scene.update` 把 `dt` 夾喺 0–0.1（`:552`）。

`document.hidden` 嗰陣主迴圈唔畫（`main.js:154`）。返嚟先把 `last` 設成而家（`:276`），隱藏嗰幾秒唔會變成一格大 `dt`。實測隱藏約 600ms：`t` 停喺 2.783、yaw −0.567。返嚟再 400ms：`t` 3.153（+0.37s）、yaw 0.401。係跟住擺鏡公式行一小步，唔係跳鏡。寵物 art 盒 x＝81、y＝218、40×60，仲喺 195×422 裡面。四個直向尺寸 `petIn` 都係 true。

## 3. 窄屏 FOV（只直向）

`#rotate` 橫向仍然係 flex（`index.html:23`）。四張直向截圖：`vp-320x640.png`、`vp-360x640.png`、`vp-390x844.png`、`vp-412x915.png`。

`ui62.overlap` 四個尺寸都係 **0**。寵物喺畫面中。頂欄、右邊信件／圖鑑／散步／朋友、底欄四掣同五個分頁都喺畫面內，冇裁走。pageerror 空。3D 開住，畫質 high。fps 面板 `display: none`。

畫布：320 同 360 約 **296×640**（左右留邊），390 係 390×844，412 約 **412×892**（高過 915 嘅視窗少一截，底欄仍然完整）。

## 4. 三級畫質

`detectQuality`（`garden3d.js:145–156`）：`?3d=0` 或者冇 WebGL → low／2D；query 寫明 high／mid／low 就用嗰級；核數 ≤4 或者記憶體 ≤4GB，除非 `?3d=1`，否則 2D。存檔 `glimmer.g3d.quality` 只喺冇 query 嗰陣覆蓋。

自動只會降，唔會升。`noteFrame`（`:713–728`）先豁免 90 幀，之後每 120 幀；平均 >28ms 先算一窗慢，連續 2 窗先 `autoDrop`（high→mid→low，`:650–656`）。4× CPU 之下每 700ms 睇一次，8 次都係 **high**，冇來回跳。

fps／耗電面板默認關。`#g3dPerf` 一開始 `display:none`，`pointer-events:none`（`:665`），`glimmer.g3d.perf` 預設唔係 `'1'`（`:669`）。要開先入開發者，再開「3D 花園 H1」入面嗰個掣（`:797`）。「開發者」掣本身係原本個掣，6d.2 截圖都有，今次冇改成常開。

三級數字喺文末。

## 5. `?3d=0`、冇 WebGL、context lost、體積

`?3d=0`：`on()` false、quality low、`renderer.g3On` false（`garden3d.js:701`）。取樣像素 (90, 145, 100, 255)，唔係白。`fallback-2d.png` 同 `QA/shots-6d2/390-day-autumn.png`：欄、燈串、籬笆、屋、底欄同一套 HD-2D。6d.2 嗰張係秋日、月眠形態加朋友剪影；呢張係日景、探測強制咗形態。佈局一樣。

冇 WebGL（Chrome `--disable-webgl --disable-3d-apis`）：`hasWebGL` false，quality low，3D 關，pageerror 空。`t` 2.43→3.23，迴圈冇停。像素 (94, 139, 115)。`nowebgl.png` 係預設光卵 2D 花園（呢次冇強制成年），天、樹、籬、屋、底欄都喺，唔白。

Context lost：`WEBGL_lose_context.loseContext()` 之後 `draws` 13→28→58，`t` 繼續行，pageerror 空，中間像素停喺 (108, 101, 73)，唔白。`on()` 仍然 true，**冇自動返 2D**。見下面 P2。

體積：

| | 6d.2 | 3D H1 |
|---|---:|---:|
| 單檔 `index.html` | 50,182,114 | **51,172,871**（+990,757） |
| `three.min.js` | — | 669,656，打進單檔做 JS |
| `art/garden3d` | — | 488,744（80 個檔） |

長度 ≥100 嘅 `data:image` base64：**0**（得個 `data:,` favicon）。`build-single.py` 把 `art/garden3d/**.png` 同 v3 一樣外置去 `art/v3/_x/`，json 入資產表。開發伺服器載入 0 個 HTTP 404。單檔 `http://127.0.0.1:8245/index.html?3d=high`：0 個 404，3D ready，17 mesh。

## 6. 已知未做（唔當 bug）

3D 開住，設雨天＋冬天＋22:00：冇拋錯，`nightMix`＝1，3D 仍然開。冇雨粒、冇季節、冇天氣霧，係試點未做。夜景係日景底板乘色（`garden3d.js:440–443`，`mixLights`）。dir4 只得 radiant 一隻；其他形態走 2D sprite 後備（`:533–545`）。細佬／朋友畫喺 WebGL 上面嘅 L2（`render.js:711–714`），已知可以微 drift。`blocked()` 有，`render.js:642` 把 `beh.x`／`depth` 直接交俾 `update`，冇叫 `blocked`，碰撞未接 `moveTo`。上面幾樣都冇整壞餵食、底欄、2D 後備。

## 7. 6d.2 回歸

夢境自寫真 `enter`，同 6d.1／6d.2 六表差 **0 日**。錢包 0，cap 47，存量最高 1。表喺第 9 節。

scan-v10-22：16／16，`lockDiff` 空。火苗 14.00、柔光 10.92、微塵 4.95、螢絨 5.47、晶角 15.32、月眠 18.72、夜貓月眠 82.4、疏玩 CQ 18、新系統 25。星碎：疏玩 19、勤力 28、普通 22、夜貓 25、早起 23、餵食狂 23。舊帳最高 30，`over30` 0。

`house.js`／`long5a.js` 同 6d.2 一樣，商店 190／慢 238／家人 Lv5 71 日沿用。`long6dui.js:87` `SHADOW_A = 0.45` 冇改。`hd2d.js` 冇改，2D 霧算法沿用；3D 已知唔畫天氣霧。`e2e-touch` 52／0。`e2e-6b3` 57／0，360／390／412 重疊 0。`e2e-6d` 專跑 **115／0**（影子 opacity 0.45、熱區 ≥48、手信 3、過 24 小時影子走晒）。

Unit **35** 檔 **2324／0**（新 `garden3d.test.js` 33；`long5a` 77／77；`long6c` 85；`long6d` 55）。

E2E **31** 套。原樣全套：21 套 0 失敗，10 套有紅。紅嘅原因分三類，都唔係玩法壞咗：

1. `e2e-3d.js:181` 寫死 `/home/box/keep/3d-h1/fps-4x.json`。產品斷言當時已經全過（載入 17 mesh、遮擋、觸摸、日夜光、畫質、`?3d=0`、窄屏、4× CPU 仍然 3D）。改寫入路徑再跑：**33／0**，包括冇 pageerror。4× CPU 讀數維持 high，`lastMs` 0.6。
2. `e2e-6d` 全套一次 110／5：兩段朋友碼字 11.77（GlimmerV3Sans）、`?v3=0` 三段 Noto Sans HK 11.77、以及「過咗 24 粒鐘」visits 仍係 2 所以手信未到 3。專跑一次 115／0。同 6d.2 嗰次全套字型／24 小時時序同一類。
3. 其餘 8 套（`e2e-a`、`hd2d`、`live`、`live2`、`playwright`、`s1`、`s2b`、`s3`）嘅「console 無 warning」全部係 Chrome 一句：`Automatic fallback to software WebGL has been deprecated…swiftshader`。遊戲冇自己 `console.error`。3D 而家會開 WebGL（`garden3d.js:262`），軟件 GL 先出呢句。`e2e-a` 另外一句「1800ms 自動降一級」見 P2。`e2e-v3` 50／0、`sys12` 79／0、`sys12b` 48／0、`uikit2` 70／0。

2D 自動降畫質本身仍然工作。`qm.grace` 喺 boot 抄咗 90（`main.js:147`），之後先改 `graceFrames` 唔會清走進行中嘅 grace。3D＋swiftshader 呢次大約十餘 fps，等 5.3 秒 grace 仲有 22、`drops` 0。把 `qm.grace` 設 0 再等 2.5 秒：`settings.quality` high→mid，`drops` 1。

## 8. 問題

**P0：** 冇。

**P1：** 冇。

**P2：**

1. Context lost 冇 listener。`garden3d.js:262` 開咗 `WebGLRenderer` 之後冇聽 `webglcontextlost`。實測 `on()` 維持 true，唔切 2D；畫面留住最後一幀（像素唔白），`draws` 13→58，冇 pageerror，冇卡死。修法：lost 嗰陣 `enabled = false`、`setQuality('low')`，之後 `render.js:634` 自然走 2D。
2. `e2e-3d.js:181` 寫死 `/home/box/keep/3d-h1/fps-4x.json`。目錄唔存在就拋，全套記失敗，最後「冇 pageerror」未跑到。產品斷言已過；改路徑再跑 33／0。修法：`mkdirSync` 那個目錄，或者寫去 `SHOTS`。
3. `render.js:626` 行尾註解食咗 `this.frameNo++`（6d.2 留低）。`frameNo` 停喺 0，`hd2dv3.js:82` 同幀檢查失效。修法：`this.frameNo++` 搬去註解前面。
4. `e2e-a.js:225–228` 只等 1800ms。3D＋軟件 GL 之下 rAF 慢，原本 90 幀 grace 未數完，所以全套見到 `drops: 0`。降級路徑試過：grace 清 0 之後 2.5 秒 high→mid。修法：測試設 `__glimmer.qm.grace = 0`，或者等到 grace 歸零先斷言。
5. 8 套舊 e2e 把 Chrome 軟件 WebGL deprecation warning 當失敗（`hd2d`、`live`、`live2`、`playwright`、`s1`、`s2b`、`s3`，加 `e2e-a` 其中一句）。遊戲冇寫呢句。修法：斷言忽略呢句，或者 Chrome 加 `--enable-unsafe-swiftshader`。真 GPU 唔會出。
6. `e2e-6d` 全套一次 110／5（字 11.77，同 24 小時 visits 仍係 2）。專跑 115／0。修法沿用 6d.2：審核要等字族同字級到位；`setT` 之後等遊戲 tick 或者直接等 `n.gifts`。

## 9. 夢境六表

真 `long6c` @ `9e598b3e`。括號係 6d.1 `49d21e45`（6d.2 同呢欄一樣）。差超過 3 日的冇。

| 表 | 集齊 | 中位 | P10 | 最慢 |
|---|---:|---:|---:|---:|
| 勤力 | 200／200（200） | 84（84） | 80（80） | 92（92） |
| 普通 | 200／200（200） | 84（84） | 81（81） | 92（92） |
| 早起 | 200／200（200） | 84（84） | 81（81） | 92（92） |
| 餵食狂 | 200／200（200） | 84（84） | 80（80） | 91（91） |
| 夜貓 | 200／200（200） | 83（83） | 80（80） | 90（90） |
| 疏玩 | 199／200（199） | 147（147） | 132（132） | 179（179） |

## 10. 畫質三級效能

4× CPU（`Emulation.setCPUThrottlingRate` 4）、swiftshader。量嘅係 **rAF callback 入面嘅耗時**，唔係 vsync 格距。目標 p50／p95 ≤17ms。long task 用 `performance.getEntriesByType('longtask')`。heap 係 `usedJSHeapSize`。

| 級 | 畫面 | 樣本 | p50 | p95 | max | >17ms | draw call | 三角 | heap | long task |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| high | 3D | 65 | 0.7 | 6.6 | 14.5 | 0 | 21 | 1054 | 37.3MB | 0 |
| mid | 3D | 136 | 0.7 | 13.0 | 23.8 | 4 | 20 | 1046 | 46.2MB | 0 |
| low | 2D | 348 | 0.6 | 4.3 | 15.9 | 0 | — | — | 27.9MB | 0 |

三級 p50、p95 都 ≤17ms。mid 有 4 幀超過 17ms，最長 23.8ms，p95 仍然 13。low 係 2D，`renderer.info` 仲留住切之前嘅 20 call／1046 三角，表入面唔當 2D 嘅 draw call。8 次抽樣畫質都係 high，冇跳級。
