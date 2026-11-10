# QA：3D 花園 H1.5（`9a599ac3`）

唯讀 `code/glimmer-3d-h1` @ `9a599ac36428edac9a14d9c5f6970b5d6acbd278`，tree `28868eb6741a4c699f949d8d89af2b955c294790`。APK 字串 `versionCode` 12、`versionName` `1.4.5-3d`（`native/android/README.md:46`）。冇改 code branch，冇 merge。

截圖：`QA/shots-3d-h15/`。掃描：`QA/scan-v10-26.json`。

## 設定核實

`QSET`（`garden3d.js:441–443`）同畫面量到嘅一樣：

| 畫質 | dpr | 幀緩衝 | 影圖 | 更新 |
|---|---:|---|---:|---|
| high | 1.5 | 293×633 | 1024 | 每 3 幀 |
| mid | 1.25 | 244×528 | 256 | 每 2 幀 |
| low | 1 | 唔用 3D | 0 | — |

`resize` 只喺寬高變先 `setSize`（`garden3d.js:984–988`）。九次 ≥600 幀窗口入面，`setSize` 增量全部係 **0**。`resize` 本身每格都入，但提早返回，p95 係 0ms。

## P0

冇。

## P2 — 4× CPU rAF p95，high／mid 未過 4.5ms

`Emulation.setCPUThrottlingRate` 4。每級 3 次，每次丟掉開頭 30 幀之後仲有 ≥600 個 callback。p95／p99 用 nearest-rank。long task 係 `PerformanceObserver` `longtask`。

| 畫質 | 三次 p95 | 三次 p99 | long task |
|---|---|---|---|
| high | 8.7、9.2、7.1 | 18.3、18.1、15.4 | 1（52ms）、0、1（67ms） |
| mid | 6.3、6.2、7.2 | 16.3、14.7、15.6 | 0、0、1（53ms） |
| low | 3.9、3.6、3.9 | 7.5、7.0、7.3 | 0、1（142ms）、0 |

high、mid 九次入面六次都高過 4.5。low 三次 p95 都過線。long task 唔係零：9 次入面 4 次有 1 條（52–142ms）。

`e2e-3d` 自己嗰段短窗（丟 8 幀、約 2.8 秒，`tests/e2e-3d.js`）係 high **6.1**、mid **5.7**、low **3.3**，`lastMs` high 2.9。同遊程講嘅 6.0–7.7／5.4–7.2／3.2–4.8 同一帶。600 幀窗會見到更高嘅尾（high 去到 9.2）。

### 拆開（p50／p95，ms）

佔比係對遊戲幀 `renderer.frame` 嘅 p50，唔係對成堆短 callback。rAF p50 只有 0.6–0.8，因為一半 callback 唔係遊戲幀。

| 段 | high p50／p95 | mid p50／p95 | low p50／p95 | 佔 high 幀 p50 |
|---|---|---|---|---|
| rAF callback | 0.8／7.1–9.2 | 0.7／6.2–7.2 | 0.6／3.6–3.9 | — |
| `renderer.frame` | 2.7–3.3／10.8–11.5 | 2.9／8.1–9.5 | 2.0／4.1–4.6 | 100% |
| `WebGLRenderer.render` | 1.4–1.6／7.3–7.8 | 1.4–1.5／5.3–5.9 | — | 約一半 |
| `Scene.draw` | 1.6–1.8／8.3–10 | 1.7–1.8／6.0–6.9 | — | 略高過 render |
| `drawL2` | 0.6–0.8／1.6–2.1 | 0.6–0.7／1.6–2.0 | 0.8／1.8–2.2 | 約四分一 |
| `g3d.update` | 0.1–0.2／0.8–1.4 | 0.1／0.9–1.3 | — | 約 5% |
| `tickWorld`（包含 `behavior.step`） | 0.1–0.2／0.8–1.9 | 0.1／0.7–1.0 | 0／0.6–0.7 | 約 5% |
| `resize`／`setSize` | 0／0 | 0／0 | 0／0 | 0 |

影圖更新幀同跳過幀嘅 `Scene.draw` p95 都係 7–12ms。影圖唔係而家超標嘅主因。`behavior.step` 喺 `tickWorld` 裡面（`main.js:226`、`behavior.js:830`），成段 p95 都低過 2ms。

CPU profile（high 第三次，200µs，11046 個 sample）：self time 頭五，撇咗 `(idle)` 62.7%（等下一幀）：

| 函數 | 位置 | 成段 self | 修法 | 預計 |
|---|---|---:|---|---|
| `(program)` | 原生 WebGL，對應 `garden3d.js:1007` | 224.8ms（10.2%） | high dpr 1.5 降到 1。像素少 2.25 倍，render p95 由約 7.5 落到約 3.3 | 慳約 **4ms** |
| `(garbage collector)` | V8 | 28.6ms（1.3%） | 幀迴圈唔好再分配 Color／臨時陣列。`mixHex` 已重用（`garden3d.js:790` 一帶） | 唔係穩態 ms；消 p99 同 50–140ms long task |
| `drawImage` | canvas blit，`garden3d.js:1009–1010` | 25.8＋18.8ms | 緩衝係 293×633，貼去 390×844，所以開咗平滑。緩衝對齊顯示尺寸，或者整數倍先關平滑 | 慳約 **0.5–1ms** |
| `getBoundingClientRect` | rail 量高，`long6dui.js:417–420` | 23.6ms | 掣高快取，唔好每秒量一次又喺重疊迴圈再量 | 慳約 **0.2ms** |
| `drawL2` | `render.js:809` | 7.8ms | 3D 已跳過舞台（`:813`），但寵物仍然畫。`drawPetBeh`（`:1014`）同 `tintSprite`（`:542`）喺 profile 緊接其後 | 3D 開時唔畫 2D 寵物，慳約 **1–1.5ms** |

`UI.update`（`ui.js:400`）self 7.2ms，同 `drawL2` 同級，低過 WebGL。

遊程懷疑剩低時間喺 `drawL2`／`update`／`tickWorld`。呢三段 p95 分別約 2、1.4、1.9ms。超 4.5 嘅係 `WebGLRenderer.render`。`Scene.draw` 中位 1.6–1.8ms，就係「3D draw 約 2ms」；p95 係 8–10ms。

### low 點解會去到 4.8

low 唔用 3D 幀緩衝，dpr 上限唔影響佢。`!g3` 先至畫 L0／L1（`render.js:691`、`:705`），所以 2D 路徑仲畫晒。今次 rAF p95 係 3.6–3.9。遊戲幀 `frame` p95 係 4.1–4.6，同遊程 4.8 同一段 2D 幀，唔係今次改動加咗嘢。

## P3

`e2e-6d` 全套一次 **125／1**。失敗係入碼三粒掣「貼上／揀相／睇吓」對比 1.02–1.15，字號 22px、`GlimmerV3Sans`，唔係字未到位。跟住再跑一次 **126／0**。抽樣，唔當產品。

8 套 e2e 唯一紅係 SwiftShader deprecation（a、hd2d、live、live2、playwright、s1、s2b、s3）。`e2e-a` 降級斷言本身過咗。

## 回歸

清屎：細佬盒包住個點，撳 20／20 回 `poop` 而且清到。撳細佬本身 20／20 回 `kid`，屎冇變。朋友影子 `alphaTest` 0.1、`maxA` 0.45，`friend-shadow.png` 見到紫色剪影。360×640 同 768×1024（另外 390、412）掣重疊 0，其餘 UI 0。寵物喺畫面、`flipY` true。

10 分鐘行為時間：寵物同細佬腳下碰撞 0、出界 0、2 秒冇進展 0。寵物 z −125…91，細佬 z −123…97。

開 3D 之後 1 秒，`ovStat.moonStars` 同 `lanterns` 唔再加（停喺 4）。天空亮度約 210，草地約 130，冇黑底。`vp-390x844.png` 有天、雲、樹、燈串、屋、寵物、UI。

`?3d=0`：`on()` false、quality low、畫面中位亮度 204、暗像素 0、撳咗畫面冇 pageerror。`fallback-2d.png` 係完整 2D 花園。冇 WebGL 同樣返 2D。橫向 844×390 顯示「請轉直向」。

夢境差 0：cap 47、viol 0。勤力 200／84／80／92；普通 200／84／81／92；早起 200／84／81／92；餵食狂 200／84／80／91；夜貓 200／83／80／90；疏玩 199／147／132／179。

`scan-v10-26`：16／16，`lockDiff` 空。火苗 14、柔光 10.92、微塵 4.95、螢絨 5.47、晶角 15.32、月眠 18.72、夜貓月眠 82.4、疏玩 CQ 中位 18。星碎中位：疏玩 19、勤力 28、普通 22、夜貓 25、早起 23、餵食狂 23。商店八件價錢加總 190（`house.js:17–25`）。小販 238、家族 Lv5 71 日嘅來源檔相對 H1.4 冇改。

Unit：35 檔 exit 0，末行加總 **2387／0**（`garden3d` **96**）。

e2e 31 套：3d **75／0**、6b **64／0**、6d 125／1（再跑 126／0）。其餘綠：4a 114、4b 95、5a2 75、5a 88、5b 100、5c 70、6a 69、6b2 51、6b3 57、6c 103、b3b 61、evo6 54、mg2 46、read 94、route 55、sys12b 48、sys12 79、touch 52、uikit2 70、v3 50。紅 8 套都係 SwiftShader。

## 畀遊程嘅熱點修法（先做邊樣）

1. **先減 WebGL 主 pass**（`garden3d.js:1007`）。`setSize` 已經唔再每格叫，再跳 shadow 都唔夠：跳過影圖嘅幀 p95 仍然約 7ms。high dpr 1.5→1，預計 render p95 由約 7.5 落到約 3.3，成個 callback 先有機會 ≤4.5。
2. **緩衝對齊顯示尺寸**（`garden3d.js:1008–1010`）。而家每格把 293×633 平滑放大貼上 390×844。預計再慳 0.5–1ms。
3. **3D 開時唔畫 2D 寵物**（`render.js:838` 之後、`drawPetBeh` `:1014`）。舞台已經跳過，寵物仲畫。預計慳 1–1.5ms。
4. **清幀內配對**。long task 4／9 次，52–142ms，profile 有 GC 1.3%。呢項消尖峰，唔係穩態 p95。
5. **`drawL2`／`update`／`tickWorld` 唔使先動。** 三段 p95 都 ≤2ms，唔係而家超 4.5 嘅原因。

今次冇 P0，冇 P1。未過嘅係 P2：high／mid 嘅 rAF p95，同埋偶發 long task。
