# QA：3D 花園 H1.4（`ea64ad29`）

唯讀 `code/glimmer-3d-h1` @ `ea64ad29056735dbdf0e884be50aa8ab5f2ba8fe`，tree `6ca0b083fa7209c1fd4bb77007249255377048e4`。APK 版本字串 `versionCode` 11、`versionName` `1.4.4-3d`（`native/android/README.md:45`）。呢部機冇 H1.4 APK，冇拆包裝。冇改 code branch，冇 merge。上一輪 `ed28e28a` 報告留低。

截圖：`QA/shots-3d-h14/`。掃描：`QA/scan-v10-25.json`。

## 上輪 P1 — 清屎

細佬企喺屎上面（盒包住個點）撳 20 次：`hitActor` 20／20 係 `poop`，20／20 `poops` 由 3 跌到 2。撳細佬本身、個點唔喺屎盒：20／20 係 `kid`，`poops` 20／20 冇變。

`hitActor` 而家屎盒優先（`garden3d.js:1179–1190`，`return poop || best`）。`e2e-3d` **71／0**，清到 `poops === 0`。上輪 59／2 已過。

## 上輪 P1 — 6d 朋友影子

半透明 actor 用 `alphaTest` 0.1（`garden3d.js:444`、`:1061–1063`），唔再係 0.5。假朋友影子：`transparent` true、`depthWrite` false、`maxA` 0.451、有像素 1101。截圖 `friend-shadow.png` 長凳上見到紫色剪影。同一次盒邊抽樣 white 像素 0，寵物／屎冇白邊。上輪「被切走」已過。

## 上輪 P1 — 散步／朋友掣

`long6dui.js:418–429` 用掣高加 8px，重疊就搬去左邊。穩定之後（等 rail 排完）：

| 尺寸 | 重疊 |
|---|---|
| 360×640 | 0（朋友 left 280、散步 left 356，同一 top，盒隔開） |
| 390×844 | 0 |
| 412×915 | 0 |
| 768×1024 | 0 |

`ui62.overlap` 其餘 UI 都係 0。寵物喺畫面、`flipY` true。`e2e-3d` 四個尺寸斷言包喺 71／0。開頁未等 rail 嗰下會短暫疊住，排完就分開。唔再當 P1。

## P0

冇。

## P2 — 4× CPU rAF callback p95，high／mid 仍然高過 4.5ms

方法同 `e2e-3d.js:174–206`：`Emulation.setCPUThrottlingRate` 4，量 rAF **callback 長度**（唔係 vsync 間隔），丟開頭 8 幀，丟掉 ≥80ms。long task 今次乾淨抽樣全部 0。

| 畫質 | e2e n／p50／p95 | 獨立再量 p50／p95 | 上輪 H1.3 |
|---|---|---|---|
| high（影圖 2048、每 3 幀、PCF） | 111／1.2／**8.7** | 116／0.8／**6.8** | 6.5 |
| mid（影圖 256、每幀、PCF） | 126／1.1／**9.1** | 129／0.8／**6.8** | 5.7 |
| low（2D） | 144／0.7／3.5 | 151／0.6／3.1 | 3.7 |

low 過線。high、mid 兩次都未過。縮影圖、關 soft shadow 之後，high／mid 比上輪 6.5／5.7 冇落返 4.5 以下。

同一套 4× 抽樣拆開（獨立再量，p95，單位 ms）：

| 段 | high | mid | low | 邊度 |
|---|---:|---:|---:|---|
| rAF callback | 6.8 | 6.8 | 3.1 | 成幀 |
| `renderer.frame`（2D＋3D） | 6.4 | 7.9 | 2.8 | `render.js:631` |
| `Scene.draw` | 5.4 | 5.8 | — | `garden3d.js:972` |
| `WebGLRenderer.render` | **5.1** | **4.9** | — | `garden3d.js:984` |
| 影圖更新嗰幀 draw 中位 | 2.3 | 2.7 | — | `:977–980` |
| 跳過影圖嗰幀 draw p95 | 4.3 | — | — | 每 3 幀先更新 |
| `tickWorld`（行為 `update`） | 0.8 | 1.6 | 0.8 | `main.js:226`、`behavior.js:830` |
| billboard `syncActors` | 0.0 | 0.1 | — | `render.js:724` |
| 細佬 `s2Tick` | 0.9 | 0.5 | 0.3 | `main.js:161` |

超過 4.5 嘅係 WebGL 主渲染，同包住佢嘅 `frame`。行為、billboard、細佬都低過 1.6。影圖更新幀中位只有 2.3ms；14 幀入面有一幀去到 22ms，所以個小樣本 p95 唔好當穩定成本。跳過影圖嘅幀 p95 4.3，已經貼近預算，主 pass 先至超。

`Scene.draw` 每幀都 `resize` → `setSize`（`garden3d.js:975`、`:967`）。high 係 dpr 2、影圖 2048。

修法：尺寸冇變就唔好 `setSize`。high 影圖再降或者花園畫布唔好用 dpr 2，等 `render` p95 落到大約 3ms，成個 callback 先有機會 ≤4.5。再縮 shadow 更新頻率幫唔到跳過影圖嗰啲幀。

### 同遊程數字差喺邊

遊程 high 9.8／mid 7.9／low 4.6，同今次 e2e 8.7／9.1／3.5 係同一類：4× 之下 rAF callback p95。差在機器同係咪丟開頭／尖峰。

遊程寫 3D draw 2.4–2.8ms，對應 `lastMs`（`Scene.draw` 最後一幀）。今次 e2e high `lastMs` **2.8**、mid **1.9**。呢個係單幀，唔係 p95。p95 係成個 callback（6.8–9.1），入面 WebGL render 先佔 4.9–5.1。

雨：200 點、`size` 6、`sizeAttenuation` false、色 `0x4a6a96`（`garden3d.js:445`）。`rain.png` 見到藍色方點，冇白屏。同一次 4×：晴天 rAF p95 6.8，雨 7.9；`threeRender` 雨 4.3、晴 5.1。雨冇再拉高 WebGL。

## P2 — 寵物同細佬仍然冇互撞

10 分鐘行為時間（36000 步，CPU 1.6 秒）。腳下碰撞 0、出界 0、2 秒冇進展 0。寵物最長 `stay` 3.2 秒。距離 <12 單位 26 次（上升沿），合共 920 步。`g3dWalk` 只測物件 footprint，冇把另一隻當障礙。同 H1.3 一樣。

修法：footprint 測試加入寵物／細佬半徑。

| | z | x |
|---|---|---|
| 寵物 | −125 … 91 | −132.2 … 137.2 |
| 細佬 | −125 … 96.9 | −137.3 … 132.4 |

## P3

`readaudit.js:50` 改用平均對比，唔再 `worst×1.4`。`e2e-6b` 連跑 **10／10**，每次 **64／0**。上輪「開」抽樣今次冇再中。

`e2e-6d` 只審 ≥12px，加咗 768×1024（`tests/e2e-6d.js:58`）。連跑 **10／10**，每次 **126／0**。

8 套 e2e 唯一失敗係 SwiftShader deprecation（a、hd2d、live、live2、playwright、s1、s2b、s3）。`e2e-a` 降級斷言過咗（`drops` 1、畫質 mid）。環境，唔當產品。

## 回歸

直向四張：`vp-360x640.png`、`vp-390x844.png`、`vp-412x915.png`、`vp-768x1024.png`。寵物喺畫面、企直。橫向 844×390：`#rotate` `display:flex`，字「請轉直向」（`index.html:179`，`land-844x390.png`）。

切走再返：hidden 時 yaw −4.968，0.5 秒後 −4.932（約 2°），`t` +0.1 秒。返嚟 0.27 秒再行到 −4.769。係擺鏡，唔係跳鏡。

`?3d=0`：`on()` false、quality low。`--disable-webgl`：`on()` false、quality low、pageerror 空。`fallback-2d.png`、`nowebgl.png`。

Context lost：`loseContext()` 之後 `lost` true、`on()` false（`garden3d.js:573–576`、`:485`）。

夢境差 0：cap 47、viol 0。勤力 200／84／80／92；普通 200／84／81／92；早起 200／84／81／92；餵食狂 200／84／80／91；夜貓 200／83／80／90；疏玩 199／147／132／179。

`scan-v10-25`：16／16，`lockDiff` 空。`nightMoon` 82.4，`cqMed` 18。玩法中位：勤力 28、普通 22、疏玩 19、夜貓 25、早起 23、餵食狂 23。全體螢絨 5.47、晶角 15.32、月眠 18.72、火苗 14、柔光 10.92、微塵 4.95。

Unit：35 個檔 exit 0。末行加總 **2382／0**（`garden3d` **91**；H1.3 係 87，其餘檔冇變）。

e2e 31 套（port 8249）：

- 綠 23：3d **71**、4a 114、4b 95、5a2 75、5a 88、5b 100、5c 70、6a 69、6b2 51、6b3 57、6b 64、6c 103、6d **126**、b3b 61、evo6 54、mg2 46、read 94、route 55、sys12b 48、sys12 79、touch 52、uikit2 70、v3 50。
- 紅 8：全部係上面嗰句 SwiftShader warning。冇產品紅。

今次冇 P0，冇 P1。
