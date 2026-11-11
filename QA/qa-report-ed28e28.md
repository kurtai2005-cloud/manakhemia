# QA：3D 花園 H1.3（`ed28e28a`）

唯讀 `code/glimmer-3d-h1` @ `ed28e28a8a909483170bc354606e8c551dd8aa35`，tree `4057cd8d08265bc39f54c908ab8d39e3f1ee16ca`。APK 版本字串 `versionCode` 10、`versionName` `1.4.3-3d`（`native/android/README.md:44`）。呢部機冇 H1.3 APK 檔，冇拆包裝。冇改 code branch，冇 merge。上一輪 `136dee5d` 報告留低。遊程報告只作對照，下面數字係今次自己量。

截圖：`QA/shots-3d-h13/`。掃描：`QA/scan-v10-24.json`。

## 自主 XZ（冇撳，行為時間 10 分鐘）

`behavior.step` 固定 `fixedDt`，36000 步＝600 秒行為時間（CPU 1.2 秒，唔係牆鐘 10 分鐘）。細佬用 `s2ui.js:258–281` 同一條公式，`_g3dStall` 交畀 `g3dWalk`，外力唔清零。`RANGE3` 係 x `[−140, 140]`、z `[−125, 100]`。

| | z | x | 腳下碰撞 | 出界 | 2 秒冇進展 |
|---|---|---|---:|---:|---:|
| 寵物 | −125 … 91 | −132.2 … 137.2 | 0 | 0 | 0 |
| 細佬 | −116.2 … 97.2 | −132 … 137.6 | 0 | 0 | 0 |

寵物最長 `stay` 3.2 秒，剛好係 `G3D_IDLE_WALK_SEC`（`garden3d.js:419`、`shouldForceWalk` `:423–428`）。過咗就開行。瀏覽器冇撳約 3 秒，z 由 0 去到 41。權重 `walk×2.6`、`stay×0.4`（`behavior.js:127–131`）。

兩隻互相唔撞。`g3dWalk` 只測物件 footprint。10 分鐘內距離 <12 單位 31 次（上升沿），合共 975 步、約 16 秒。見下面 P2。

## 2D 物件入 3D billboard

Actor mesh：`alphaTest` 0.5、`transparent: false`、`castShadow: false`（`garden3d.js:1085–1089`）。會寫 depth，屋仔／花盆可以擋住。腳底 blob 影子另外每幀跟位。`hitActor` 用投影盒，最近 ndc z 贏（`:1158–1169`）。`pointerdown` 先處理 actor，先至寵物盒（`ui.js:342–359`）。

| 物件 | 寫入 | 影子 | 撳 |
|---|---|---|---|
| 屎 | `render.js:907` `hit:true` | 有 | 實測 |
| 波 | `:925`、`:1225` `hit:false` | 有 | 唔入 hitActor，寵物盒先 |
| 食物 | `:920` `hit:false` `shadow:false` | 冇 | 同上 |
| 訪客 | `b3bui.js:251` `hit:true` | 有 | `b3bTap` 回 true 先截住 |
| 友誼擺設 | `b3bui.js:289` `hit:false` | 有 | 唔截撳 |
| 6d 朋友影子 | `long6dui.js:370` `alpha:0.45` `hit:true` | 有 | 見 P1 |
| 雨 | `garden3d.js:737–743` Points 140 | — | 唔係撳目標 |

清屎 raycast（每次重讀盒、重置 `poops=3`）：冇被擋 `poop-0` **20／20**（`occ false`，kind `poop`）。被擋 `poop-1`（z＝16，`occ true`）**20／20**，仍然 kind `poop`。屋仔擋住唔會令清屎失效，只要細佬盒冇包住個點。

同寵物重疊：把寵物放到屎嘅 xz，個點嘅 `hitActor` 係 `poop`，寵物螢幕盒冇包住個點。代碼上如果兩盒都包住，屎會 `return`（`ui.js:345`），寵物摸唔到。同細佬重疊就唔係：見 P1。

雨：`rainMesh.visible` true、140 點、`depthWrite: false`、`opacity` 0.75、`size` 1.6。冇白屏、冇 pageerror。`rain.png` 睇落仍然係晴天，點太細。4× callback 切去雨嗰陣 p95 14.2（晴天對照 15.3，兩次都有切換尖峰）。雨冇再把 p95 拉高過晴天尖峰。見 P2。

## P0

冇。

## P1 — 細佬盒搶咗清屎

`e2e-3d` **59／2**。失敗兩條都係同一下：「屎喺 3D 出現、hitActor 命中」回傳 `hit:"kid"`，之後 `poops` 仍係 2（`tests/e2e-3d.js:378–388`）。

`hitActor` 所有盒入面揀 ndc z 最小（最近鏡頭）嗰隻（`garden3d.js:1158–1169`）。細佬盒高 45（`s2ui.js:425`），企喺屎前面就包住個點，細佬近過屎，清屎唔會行。我單獨撳空位係 20／20，所以唔係屎盒本身打唔中。

修法：地面細物件（`poop`）喺自己盒入面優先於 `kid`／`visitor`，或者點落喺屎盒就直接回屎，唔好只比 z。

## P1 — 6d 朋友影子喺 3D 會被切走

`l6dActors` 用 `alpha: SHADOW_A`，`SHADOW_A = 0.45`（`long6dui.js:87`、`:370`）。畫上 canvas 之後 `destination-in` 把 alpha 設成 0.45（`garden3d.js:1073–1078`）。材質 `alphaTest` 0.5（`:1085`）會丟掉低過 0.5 嘅片元，成張 billboard 唔畫。同一刻 2D canvas 設 `visibility:hidden`（`long6dui.js:349`）。有朋友影子時，3D 同 2D 都睇唔到。撳盒仍然 `hit:true`，可以撳到一隻睇唔見嘅影子。

修法：`alphaTest` 低過 0.45（例如 0.05），或者 `transparent: true` 而唔用 0.5 去切。3D 真係畫到先至收起 2D canvas。

## P1 — 360 同 768 散步掣同朋友掣重疊

清走 toast 之後 `ui62.overlap`：

| 尺寸 | 重疊 |
|---|---|
| 360×640 | 1：`#l6dbtn` 同 `#l6bbtn`，42×42 |
| 390×844 | 0 |
| 412×915 | 0 |
| 768×1024 | 1：同一對，67×67 |

朋友掣排喺最底一粒 rail 下面 70px（`long6dui.js:412–418`）。呢兩個寬度 70px 唔夠掣高，兩粒疊住。390 截圖兩粒係分開嘅。寵物喺畫面內、`flipY` true。直向 `#rotate` 係 `none`。

修法：用掣嘅 `getBoundingClientRect` 高度加間距；仍然重疊就搬去左邊列（同檔 `:419` 已有呢條分支）。

## P2 — 4× CPU callback p95 仍然高過 4.5ms

量嘅係 `Emulation.setCPUThrottlingRate` 4 之下 rAF callback 長度，唔係 vsync 間隔。long task 全部 0。

| 畫質 | shadow | 更新 | n | p50 | p95 | max | >4.5 |
|---|---:|---:|---:|---:|---:|---:|---:|
| high | 2048 | 每 3 幀（`garden3d.js:439`、`:973–977`） | 69 | 0.5 | **6.5** | 9.2 | 18 |
| mid | 512（`:440`） | 每幀 | 90 | 0.7 | **5.7** | 18.9 | 18 |
| low | 0 | 2D | 103 | 0.5 | 3.7 | 20.4 | 2 |

low 過線。high、mid 未過。腳底 blob 喺 high 下跟寵物 x＝−16…16 每步都啱，冇拖後。日光 shadow map 每 3 幀先更新；屋仔係靜態，唔會拖影。未逐幀對圖，所以唔宣稱完全冇閃。

修法：mid 影圖再縮，或者 high 唔好每 3 幀先更新一次又同時用 2048；用同一支 4× callback 抽樣直到 p95 ≤4.5。

## P2 — 寵物同細佬冇互撞

見上表。31 次行到 12 單位以內，腳下物件碰撞仍然 0，所以唔係卡死。`g3dWalk` 冇把另一隻當障礙。

修法：`followPath` 嘅 footprint 測試加入寵物／細佬／影子嘅半徑。

## P2 — 雨點幾乎睇唔到

`garden3d.js:741` `size: 1.6`。場景有 140 點，截圖 `rain.png` 仍然係晴天草地。冇穿模、冇白屏。

修法：加大 `size`，或者改成短線 sprite，再截一張雨天對照。

## P3 — e2e-6b「開」公式未改

`readaudit.js:44` 仍然 `Math.min(mean, worst * 1.4)`。今次全套 `e2e-6b` **64／0**，呢次抽樣未中「開」。公式冇改，維持 P3，唔當新產品 bug。

## P3 — e2e-6d 字型審核 8／10

`fontOn` 等 `document.fonts.ready`，再等**其中一個**可見節點係目標字型而且 ≥12px（`tests/e2e-6d.js:38–50`）。10 次：8 次 **115／0**。第 1、第 9 次 **114／1**，只係 `?v3=0` 主面板：Noto Sans HK 11.77／12.31，對比 13.19–13.6。`readaudit` 嘅 `minEff` 14 會抓呢個字號。對比合格，係審核起步太早，唔當產品 P。

## 回歸

直向四張：`vp-360x640.png`、`vp-390x844.png`、`vp-412x915.png`、`vp-768x1024.png`。寵物喺畫面、企直。重疊見 P1，其餘兩張 0。橫向 844×390：`#rotate` `display:flex`，字「請轉直向」（`index.html:179`，`land-844x390.png`）。

切走再返：hidden 時 yaw 3.36°、`t` 16.410 凍住；0.34 秒後 yaw 3.96°（+0.60°）。係擺鏡一小步，唔係跳鏡。

`?3d=0`：`on()` false、quality low。`--disable-webgl`：`on()` false、quality low、pageerror 空。`fallback-2d.png`、`nowebgl.png`。

Context lost：listener 喺 `garden3d.js:573–580`，`on()` 要求 `!this.lost`（`:485`）。`loseContext()` 之後 `lost` true、`on()` false。今次冇再等 `restoreContext`。

夢境（`sleeping` 先設 true 再 `canEnter`）同 6d.1／H1.2 一樣：cap 47、viol 0。勤力 200／84／80／92 bank 1 wallet 0；普通 200／84／81／92；早起 200／84／81／92；餵食狂 200／84／80／91；夜貓 200／83／80／90；疏玩 199／147／132／179。差 0。

`scan-v10-24`：16／16，`fail` 空，`lockDiff` 空。`nightMoon` 82.4，`cqMed` 18。玩法中位：勤力 28、普通 22、疏玩 19、夜貓 25、早起 23、餵食狂 23。`over30` 0。

Unit：35 個檔 exit 0。末行加總 **2378／0**（`garden3d` **87**）。遊程寫約 2379，差在點算法，冇失敗檔。

e2e 31 套（port 8248）：

- 綠 22：4a 114、4b 95、5a2 75、5a 88、5b 100、5c 70、6a 69、6b2 51、6b3 57、6b 64、6c 103、6d 115、b3b 61、evo6 54、mg2 46、read 94、route 55、sys12b 48、sys12 79、touch 52、uikit2 70、v3 50。
- 產品紅 1：`e2e-3d` 59／2（P1 清屎）。
- `e2e-a` 93／1：降級斷言過咗（`{"q":"mid","drops":1,"auto":true}`）。唯一失敗係 SwiftShader console warning。
- 其餘 7 套都係同一句 SwiftShader deprecation（hd2d 50／1、live 45／1、live2 42／1、playwright 36／1、s1 50／1、s2b 24／1、s3 31／1）。環境，唔當產品。

three.js LICENSE：`tools/build-single.py:62–73` 有 `EXT` 就抄去 `vendor/LICENSE.three.txt`，否則以 `text/plain` 打入單檔。來源檔 `src/vendor/LICENSE.three.txt` 在。呢部機冇 APK，未拆包裝核對。

今次有 P1，冇 P0。
