# QA：6d.2（`ecb2c3a3`）

唯讀 `code/glimmer-6d2` @ `ecb2c3a3f6bb1558570733bce7743af492465c2a`，tree `04084f34ed6ca408f6e25a04d335133be475c7b0`。基 6d.1 `49d21e45`。`long6c.js`、`long6d.js`、`house.js`、`long5a.js`、`sim.js`、`build-single.py` blob 同 6d.1 一樣。冇改 code branch，冇推 main。

## 1. 朋友影子半透明

`long6dui.js:87` `SHADOW_A = 0.45`。剪影像素仍然係三階紫 `#EEE2FF`／`#A98BF0`／`#5C3FB0`，alpha 255（`shadowCanvas` 寫滿）。半透明係 `paintShadow`（`:141`）只對影子 canvas 設 CSS `opacity: 0.45`。四個尺寸都量到：相鄰像素 >0（唔係 4×4 格仔）、canvas opacity 0.45、徽章 computed opacity 1。`.sh6` 父層冇 opacity，徽章同泡泡唔跟住淡。花園發光／粒子喺 renderer，唔係呢塊 canvas。

撳位 `.ht` 佈局 56×76，opacity 1、`pointer-events: auto`。半透明冇縮細撳位。360 螢幕像素約 42×58，係原本 ui 縮放，唔係今次 opacity。

企定時同團絨 `petRect`、右邊 rail 都冇相交。互動時會行去團絨隔籬（`long6dui.js:316`），係原本設計。

快取命中之後 `layTick` p95 **0.1–0.2ms**。4× CPU、影子同夢境開住，畫面格距 p95 **16.7ms**（冇掉去 33ms）。像素唔使每格重寫，淡出係 CSS。

截圖（日／夜、春夏秋冬）：`QA/shots-6d2/320-day-spring.png`、`360-night-summer.png`、`390-day-autumn.png`、`412-night-winter.png`。日景剪影盒 p90 對比約 2.8，夜景約 4.6–6.2；目視剪影完整、徽章實色。

## 2. `dt` 下限 0

`render.js:626`：`dt = Math.max(0, Math.min(dt, 0.1))`。實測 `frame(-0.25)`：`t`、`sunMix` 0.4、`sleepMix` 0.55、視差 0.2／−0.15 都唔郁。`frame(0.016)` 先至向前：`t` +0.016，`sunMix` 0.387，`sleepMix` 0.531，視差有走。冇因為負 `dt` 倒播。

同一行註解食咗 `this.frameNo++`。負 `dt` 同正 `dt` 之後 `frameNo` 都停喺 0。`hd2dv3.js:82` 用 `petBlit.fn === frameNo` 當「今幀有畫」；兩個都係 0，守衛失效。

## 3. `?v3=0` 字型

`fontsReady`（`long6dui.js:136`）等 `document.fonts.check`，上限 4 秒，之後照樣完。`open`（`:201`）先 `render()`，字型好先再畫，面板唔等佢。中止 otf／ttf 之後，面板 **2ms** 就出現，500ms 後仍然在。載唔到唔會卡死。

`e2e-6d` 連跑 10 次：**7 過、3 失敗**。兩次 `?v3=0` 主面板字族係 Noto Sans HK、有效 11.77。一次入碼／預覽字族係 GlimmerV3Sans，有效仍然 11.77。`e2e-6d.js` 的 `fontsOk` 超時 5 秒之後 `.catch` 照樣審。`e2e-6b3` 連跑 10 次都係 57／0，冇落到系統字。

## 4. 回歸

夢境自寫真 `enter`，同 6d.1 六表中位／P10／集齊差 **0 日**。錢包 0，cap 47，存量最高 1。

scan-v10-21：16／16，`lockDiff` 空。火苗 14.00、柔光 10.92、微塵 4.95、螢絨 5.47、晶角 15.32、月眠 18.72、夜貓月眠 82.4、疏玩 CQ 18。星碎：疏玩 19、勤力 28、普通 22、夜貓 25、早起 23、餵食狂 23。舊帳最高 30，`over30` 0。

`house.js`／`long5a.js` 同 6d.1 一樣，190／238／Lv5 71 日沿用。霧格距 p95 16.7ms（4× CPU，夢境開住）。`e2e-touch` 52／0。外置單檔腳本同美術同 6d.1 一樣，大細沿用 **50,182,114**。`long6d.js` 冇改，手信唔入錢包。橫向 `#rotate` 仍然係 flex。

Unit **34** 檔 **2291／0**。E2E **30** 套，`e2e-6d` 全套一次 113／2（24 小時自動走，visits 仍係 2、手信未到 3）；專跑 10 次呢句都過。其餘 29 套 0 失敗，包括 `sys12` 79／0、`sys12b` 48／0、`uikit2` 70／0。

## 5. 問題

**P0：** 冇。

**P1：** 冇。

**P2：**

1. `render.js:626` 行尾註解食咗 `this.frameNo++`，`frameNo` 停喺 0，`hd2dv3.js:82` 同幀檢查失效。修法：`this.frameNo++` 搬去註解前面。
2. `e2e-6d` 10 次有 3 次字未到位（2 次 Noto Sans HK，1 次 GlimmerV3Sans 但有效 11.77）。`fontsOk` 超時之後照審。面板唔卡死（4 秒上限，中止字型檔 2ms 就開到）。修法：審核要等目標元素的字族同字級到位；`check` 失敗就唔好當過。
3. 全套一次「過咗 24 粒鐘」visits 仍係 2（`e2e-6d` 113／2）。專跑 10 次該句都過。修法：`setT` 之後多等遊戲 tick，或者直接等 `n.gifts`。

## 6. 夢境六表

真 `long6c` @ `ecb2c3a3`。括號係 6d.1 `49d21e45`。差超過 3 日的冇。

| 表 | 集齊 | 中位 | P10 | 最慢 |
|---|---:|---:|---:|---:|
| 勤力 | 200／200（200） | 84（84） | 80（80） | 92（92） |
| 普通 | 200／200（200） | 84（84） | 81（81） | 92（92） |
| 早起 | 200／200（200） | 84（84） | 81（81） | 92（92） |
| 餵食狂 | 200／200（200） | 84（84） | 80（80） | 91（91） |
| 夜貓 | 200／200（200） | 83（83） | 80（80） | 90（90） |
| 疏玩 | 199／200（199） | 147（147） | 132（132） | 179（179） |
