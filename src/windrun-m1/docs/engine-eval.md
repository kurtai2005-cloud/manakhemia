# 引擎／技術評估（plan §9 Q1–13；M1 第 1 週前半）

> **讀法**：每個數字標明來源——**〔實測〕**＝本 repo 內腳本喺 box 實跑；**〔查證〕**＝公開來源（附連結，查證日 2026-10-26）；**〔估〕**＝推斷／經驗，**未驗證**；**〔待核實〕**＝未查到或未能實測，留空，不填數。
> **所有幀時間均喺 box 嘅「無頭桌面 Chrome 156（SwiftShader 軟件 WebGL／CPU 光柵）」或「Godot 4.7.2 + llvmpipe（Xvfb）」量度，唔係 Android 真機。** 只可比較同一環境內嘅**相對差**，絕對值唔可直接當手機成績。真機判斷需喺目標機跑同一組腳本（見 §6）。
> Q14–20（後端週）只簡短標示，見文末。

## 0. 結論（3 行）
1. **M1 先留喺 Web**（Canvas2D；要 shader 級 bloom／tilt-shift 時升 WebGL／PixiJS）：`sim.js`／`api.js`／`save.js`／`town-map.js` 全部 DOM-free，遷移成本近零，部署即時；town-lab 喺所有檔位已走通 Q7 全部元素。
2. **Godot 4 係首選嘅原生後備**（MIT 授權〔查證〕、2D 燈光／TileMapLayer／AStarGrid2D／Y-sort 原生、同一張圖 A* 已交叉驗證）；Unity 對 HD-2D 光照同生態最強但最重、授權有收入門檻〔查證〕——**Unity 本輪冇實測**。
3. **最終引擎於第 2 週末、內部試玩＋真機跑 §9 腳本後定**；上述 APK 體積／fps／人日數字一律〔估〕或〔待核實〕，唔好當承諾。

## 1. 環境同方法（可重現）
| 項 | 內容 |
|---|---|
| 機器 | box：8 vCPU Xeon、無實體 GPU；Chrome 156.0.8078.47 headless，WebGL＝ANGLE→SwiftShader；Godot 4.7.2-stable，GL 為 llvmpipe（LLVM 19.1.7）〔實測〕 |
| Web 量度 | 不限速渲染迴圈；每幀結尾 `getImageData(1px)` 強制 flush；熱身 30 幀後取 240 幀（avg／p95／max）；另量 rAF 實際 fps |
| 視口 | 手機 390×844（dpr 1 與 2）、桌面 1280×720（dpr 1） |
| 腳本 | `tests/fx-bench.js`（後處理）、`tests/town-bench.js`（城鎮）、`tools/godot-bench/{bench,render_bench}.gd` |
| 限制 | SwiftShader 係 CPU 光柵：填充率主導嘅成本會被放大，GPU 紋理取樣／混合又同真機唔同；故只作「相對成本排序」。Unity 無法喺無頭 box 免登入安裝／授權〔待核實〕，未量度。 |

## 2. Q1 引擎比較（中低階 Android 60 fps vs 遷移成本）
| 維度 | Web（Canvas2D → WebGL／PixiJS） | Godot 4 | Unity |
|---|---|---|---|
| 現有 MVP 遷移 | **~0**：`sim.js` 372 行、`api.js` 212 行、`save.js` 132 行等無 DOM，直接沿用；`ui.js`（571 行）本來就係 Canvas | 要重寫 `sim`／`save`／`town-map` 為 GDScript／C#（約 1.1k 行邏輯）＋全部 UI；種子 RNG／雜湊要逐位對拍（見 `replay-format.md` §7）〔估：數週〕 | 同 Godot，另加 C# 專案／套件管理負擔〔估：數週〕 |
| 2D 圖塊＋光＋遮擋 | 自建（town-lab 已做：chunk 預渲染、Y 排序、光圖、DOF） | 原生 TileMapLayer、Y-sort、`PointLight2D`、`CanvasModulate`、`LightOccluder2D`；Compatibility 渲染器支援 2D 光影同 WorldEnvironment glow（簡化版）；**2D HDR 只限 Forward+／Mobile**〔查證：docs.godotengine.org 4.3 Environment and post-processing〕 | URP 2D Renderer 有 2D 燈／Tilemap／Sprite sorting〔待核實：本輪冇開官方文件〕 |
| 本輪 headless 量度 | town-lab 見 §4 | 同圖 25 盞 PointLight2D：2.7–3.2 ms（無燈）→ 7.1–7.9 ms（有燈）〔實測，llvmpipe，390×844，5 次運行〕 | 〔待核實〕 |
| A* 500 條隨機路徑 | JS 平均 0.033 ms／條（平均路長 17.79） | Godot `AStarGrid2D` 0.0087 ms／條（平均路長 **17.786，同 JS 一致**） | 〔待核實〕 |
| 部署 | 網址即玩、更新即時；iOS 可 PWA／加到主畫面 | Web 匯出可（單執行緒預設，免 COOP/COEP；官方 4.5 WebGL2 約 6.2 MB 壓縮，4.6.2 約 6.3 MB〔查證：deml.io 基準頁〕）；原生 APK／iOS 另需匯出範本，**體積〔待核實〕** | Android／iOS 原生；WebGL 輸出體積〔待核實〕 |
| 震動／觸覺 | Chrome Android 可；**iOS Safari 無**（見 Q6） | `Input.vibrate_handheld()` Android／iOS／Web 皆有實作，Web 同 Safari 不支援〔查證〕 | 原生 API／套件〔待核實〕 |
| 授權 | 自家碼；第三方庫（PixiJS／Phaser 等）〔待核實〕 | **MIT**〔查證：godotengine/godot LICENSE.txt〕 | Personal 限過去 12 個月收入＋資金 < **US$200,000**；Runtime Fee 已於 2024-09-12 取消；Unity 6 Personal 的 splash 可選〔查證：unity.com 條款／定價頁〕——超過門檻須轉 Pro |
| 風險 | 低端機 fillrate／記憶體由我哋自己管；無內建編輯器 | 工具鏈新；Web 版性能低於原生（官方文件亦註明）〔查證〕 | 學習／授權／專案體積最重；對 Kurt 現有流程嘅適配〔待核實〕 |

**結論**：中低階 Android 60 fps 嘅關鍵唔係引擎而係**後處理預算同 dpr**（§3、§4）：同一套美術，Web 只要守預算（baked 光、低 dpr、烘焙模糊）已有明顯餘裕；Godot／Unity 原生渲染器喺真機通常較省，但〔估〕——要真機證明。

## 3. Q2 後處理成本、可否烘焙／偽造（fx-lab，程序版素材）
腳本：`tests/fx-bench.js`；頁面：`fx-lab.html`。手機 390×844，每幀 ms〔實測，SwiftShader，乾淨重跑〕：

| 檔位（passes＝全螢幕填充次數） | dpr 1 avg／p95 | dpr 2 avg／p95 | 貼圖暫存 |
|---|---|---|---|
| off（7 passes） | 0.9／1.1 | 2.7／3.3 | 1.8／6.6 MB |
| low（14） | 3.9／4.8 | 14.5／16.9 | 3.4／13.0 MB |
| mid（19） | 7.3／8.8 | 26.7／30.5 | 3.6／13.6 MB |
| high（32） | 10.3／12.3 | 37.3／43.6 | 1.3／4.2 MB |
rAF 實際 fps（dpr1，非不限速）：off 60.5、low 60.5、mid 60.5、high 59.2。

**判讀**
- 成本約同「像素數×填充次數」成正比：dpr 1→2（4× 像素）令 low／mid／high 變成約 3.7／3.7／3.6 倍。**cap fx canvas 嘅 dpr ≤ 1–1.5 係最大單一收益**。
- 簡單「passes×單次成本」模型（校準：普通混合 0.11 ms／全屏、additive 0.26 ms／全屏）同實測差數倍，**唔可靠，唔好用嚟預測真機**，以實測為準。
- 各效果成本：town-lab 對照（見 §4）——live 光圖 vs baked：dpr1 約 −2.1 ms、dpr2 約 −7.3 ms、桌面 −4.7 ms（同為 glow=1、dof=0）；tilt-shift 景深：dpr1 約 0.6 ms、桌面約 1.8 ms（dpr2 該對數據 0.4 ms 但 p95 異常，視為雜訊）；bloom／glow 同 `lres` 同時變動，**無法單獨分離〔待補測〕**。體積光未實作〔待核實〕。

**烘焙／偽造策略（建議）**
| 效果 | 建議 |
|---|---|
| 2D 動態光 | 場景靜態光（窗、燈）**預烘到一張低解析光圖**（town-lab `baked`，0.29 MB）；只有玩家／螢火蟲／傳送門等少數動態光用 live |
| 景深／tilt-shift | 遠景層**預烘模糊**（平移視差代替重算）；只喺 high 檔做即時 tilt-shift 帶 |
| bloom | 用「emissive 圖層＋縮小模糊再加色」偽造（fx-lab 做法），唔做全屏高斯 |
| 暈影 | 烘進 UI 圖層（0 成本） |
| 體積光 | 偽造：加色光柱貼圖＋α 呼吸（引擎做 α，唔烘 GIF） |

### 3.1 真素材版（`?art=1`）——已重建（第 2 週，`src/fx-art.js`、`tests/fx-art-bench.js`）
全部為 **headless, not a real device**（桌面 Chrome 156、SwiftShader 軟光柵、960×540 畫布、night、240 幀；box 另開有桌面 Chrome，並非完全空閒）〔實測，2026-10-26 11:22 HKT〕。
| 檔位 | dpr1 avg／p95／max（ms） | dpr2 avg／p95／max（ms） | 解碼 RGBA | PNG 傳輸 |
|---|---|---|---|---|
| off | 1.55／2.40／5.1 | 5.90／6.80／8.5 | 6.9 MB | 0.09 MB |
| low | 2.03／2.70／5.5 | 21.15／27.0／34.8 | 10.1 MB | 0.44 MB |
| mid | 8.89／10.5／15.2 | 52.87／62.0／84.1 | 14.3 MB | 0.55 MB |
| high | 26.48／32.1／37.7 | 100.74／112.9／137.0 | 12.3 MB | 0.56–0.60 MB |
（同日 10:31 較早一次 dpr1：mid 9.11、high 24.65 → 機器噪音約 ±10%。早前記憶下嘅「dpr1 約 50 MB／dpr2 約 200 MB」今次無法重現（解碼後 RGBA 實測 7–14 MB，依檔位），**以本表為準**；兩者差異原因待核實。）
- 做咗：腳步粒子 run_02／run_05、螢火／草葉呼吸由引擎做、貓 pivot 修正（run y=55、idle 62、skill／lose 64；`catBloom` 0.7 → near-white 由 4.35% 降至 2.12%（mid）／7.75%→3.84%（high））、截圖 `screens/fx-art-*.png`。
- 美術規格問題：①模糊疊加＝預模糊（pre）同即時模糊（live）會疊成 √(σpre²+σlive²)，每層只該揀一種；low 檔 σ（mid 4.0／fore 8）大過規格（2.6／7）。②Bayer 抖動只喺天空層有摩爾紋（振幅 0.82→0.64 當 σ 由 0 升至 2），需整數縮放或 σ≥2。③螢火已烘入 fore.png → 引擎無法獨立閃爍，建議交 `fireflies.json`（位置／相位）。④爆發幀喺 x 邊緣被裁；跑步幀碰 x=0；town48 pivot 偏 1 px。⑤層圖解碼後 RGBA 14.3 MB（mid）可接受，但 dpr2 逐幀成本同 canvas 面積成正比（見表）→ 低檔機應鎖 dpr1 或 off／low。

## 4. Q7 同一張城鎮圖比較（town-lab：40×30、16px、多層 Tiled JSON）
**town-lab.html 已實作**（`src/town.js`＋`src/town-map.js`）：多層圖塊渲染與 chunk 預渲染、Y 排序遮擋（道具／NPC／玩家）＋遮擋圖塊層（樹冠、拱門、樹籬頂）、2D 動態光（25 盞：燈／窗／旗／傳送門／玩家，baked／live）、遠／近景景深（tilt-shift 帶）、點擊移動 A*（8 向、不切角、視線平滑）＋浮動搖桿、格子碰撞（AABB 逐軸）、傳送點（淡出入、雙向）、NPC 巡邏同對話、390×844 觸控＋1280×720 桌面。`tests/town-e2e.js` 全通過（點路、牆邊容錯、搖桿、遮擋截圖、傳送、對話、鍵盤、兩種視口）。截圖：`screens/town-*.png`（含遮擋前後對照 `town-390-occlusion-*.png`）。

**Web 幀時間〔實測，headless SwiftShader，非真機〕**（avg／p95 ms；chunk＝預渲染開）
| 設定 | 手機 dpr1 | 手機 dpr2 | 桌面 1280×720 |
|---|---|---|---|
| off | 0.43／0.60 | 1.44／1.70 | 1.12／1.40 |
| off，無 chunk | 1.63／2.00 | 2.67／3.10 | 2.48／2.90 |
| low（baked 光） | 2.02／2.90 | 6.23／7.10 | 4.32／5.10 |
| mid（live 光＋暈影） | 2.11／2.40 | 6.85／7.80 | 5.10／5.80 |
| high（live 光＋景深＋glow） | 4.49／5.30 | 14.36／16.60 | 11.21／13.20 |
| high，無 chunk | 5.57／6.50 | 15.64／18.10 | 12.63／14.80 |
| high−景深 | 3.89／4.50 | 13.94／29.10* | 9.40／10.70 |
| high 改 baked 光、無景深 | 1.81／2.20 | 6.67／7.60 | 4.68／5.30 |
\* p95 受雜訊影響。

- **chunk 預渲染**：每幀繪製圖塊數 390–501 → 4（一次 blit）；off 檔 ×3.8（dpr1）；開光／景深後主導成本轉去光同景深，收益縮至 1–1.3 ms。預渲染一次 2.5–4.7 ms、整張圖 372,736 px＝**1.42 MB**；baked 光圖 0.29 MB；圖塊集 0.05 MB。
- **載入**：地圖 JSON 讀取＋建立 4.0–6.8 ms；進入城鎮 2.4 ms、進入路線 1.4 ms；資源檔：town JSON 24.2 KB、route 12.9 KB、tileset PNG 4.2 KB、角色 4 張各 0.7 KB。
- **A\***：JS 500 條隨機路徑，town 0.033 ms／條（p95 0.10）、route 0.023 ms／條；可忽略。
- **建議降級**：見 Q4。

**Godot 4.7.2 同圖〔實測〕**
- `bench.gd`（`--headless`，載入同一份 Tiled JSON）：JSON 讀取 0.91 ms、`AStarGrid2D` 建格 0.23 ms、500 條路徑 0.0087 ms／條（p95 0.025）、`TileMapLayer` 建立 1.19 ms；平均路長 17.786＝同 JS 一致（交叉驗證格子／碰撞解讀相同）。
- `render_bench.gd`（Xvfb＋`opengl3`／gl_compatibility＋llvmpipe，窗口 390×844，`--disable-vsync`，240 幀）：無燈 avg 2.68–3.17 ms（p95 3.7–6.0）；25 盞 `PointLight2D`＋`CanvasModulate` avg 7.10–7.85 ms（p95 8.6–12.6，max 30–40 ms）。**同 Web 唔可直接比大細**（不同光柵器、量度點不同：Godot 以 process 間隔計，無 getImageData flush；Web 為 CPU 軟光柵）。可得結論只有：Godot 內置光源亦係成本大項（約 +4.5 ms），同 Web live 光圖嘅量級類似，**冇證據顯示 Godot 喺同一光柵器下更快或更慢**。
- Godot 本輪**未做**：後處理（glow／tilt-shift）、Web 匯出、Android 匯出、記憶體。〔待核實〕

**Q7 結論表**
| 項 | Web（自建） | Godot | Unity |
|---|---|---|---|
| 多層圖塊 | 自建 chunk（已做） | TileMapLayer 原生（已載入同一 JSON） | Tilemap 原生〔待核實〕 |
| 2D 動態光 | 自建 live／baked（已做） | PointLight2D（已做）| URP 2D Lights〔待核實〕 |
| 遮擋排序 | Y 排序＋遮擋層（已做） | Y-sort／z_index 原生 | Sorting layer／Custom axis〔待核實〕 |
| 景深／視差 | 自建 tilt-shift（已做）；視差層需自做 | ParallaxBackground 原生；DOF 需自寫 shader〔待核實〕 | 後處理 Volume 有 DOF，但係 3D 向〔待核實〕 |
| 觸控搖桿／點擊移動 | 已做 | 需自寫（簡單） | 需自寫／套件 |

## 5. Q3 真 3D＋2D 精靈 vs 純 2D 分層光圖〔估，無實測〕
- 純 2D 分層：工作量＝美術出分層圖（art 包已按此規格）；光圖／視差由引擎處理；中低階機可守預算（§4）。**M1 建議用呢條路。**
- 真 3D 場景：要建模／UV／3D 光照／陰影／LOD；中低階 Android 成本顯著（頂點、陰影貼圖、記憶體）；Web 路線要 three.js／Babylon 類庫〔待核實授權〕。視覺上得到真透視、動態陰影同真景深。
- 判斷：視覺差距存在但 M1「冒險垂直切片」未必值得；建議以 2D 分層＋偽景深作基線，3D 只留作後期「大場景」嘅選項。**工作量倍數不作數字承諾〔待核實〕。**

## 6. Q4 低檔降級與預算（建議，基於 §3／§4）
| 檔 | 設定（`WR.Town.QUAL`） | 用途 |
|---|---|---|
| off | 無光、無 DOF、無 glow、無暈影 | 極低端／省電 |
| low | baked 光 | 中低階預設 |
| mid | live 光＋暈影 | 中階 |
| high | live 光＋DOF＋glow | 旗艦／桌面 |
- **自動檔位**：入場後量 30–60 幀 EMA，若 p95 > 14 ms 降一檔、連續 5 s < 8 ms 升一檔（含遲滯）〔建議，未實作〕。
- **預算建議〔估，須真機覆核〕**：渲染 ≤ 8 ms／幀（50% 預算，留俾 sim／UI／GC）；fx canvas dpr ≤ 1.5（low 檔 ≤ 1）；live 光 ≤ 12 盞（同屏）；全螢幕填充 ≤ 14 passes（low）；層圖 ≤ 1× 存放，單場景貼圖暫存 ≤ 64 MB〔估〕。
- 真機量度方法（比值法）：喺目標機同 box 各跑 `tests/town-bench.js` 同款量度（頁面提供 `bench()`），以 off 檔作基準換算比例；SwiftShader 同 GPU 嘅比例唔固定，**唔准直接乘**。

## 7. Q5 動畫工具鏈
- 現況：`tools/gen_town_assets.py` 產生 `char_*.png`（64×96：列＝d/l/r/u 四向、行＝4 幀，每格 16×24）；道具單張 PNG；圖塊集 16 欄、`town_tiles.names.txt` 命名（gid＝行號，firstgid=1）。
- 建議：像素原稿用逐幀（像素風唔建議骨骼）；輸出＝圖集 PNG＋JSON（幀名 `角色_動作_方向_序號`）；Web 用自建幀動畫器（讀圖集），Godot 用 `AnimatedSprite2D`／`SpriteFrames`，Unity 用 Sprite Atlas＋Animator。骨骼（Spine 等）只適合大型怪物，授權費用〔待核實〕。
- 編輯工具（Aseprite 等）授權／價格〔待核實〕，M1 唔強制。

## 8. Q6 震動／觸覺
| 平台 | 支援 | 來源 |
|---|---|---|
| Web，Chrome／Edge／Opera／Samsung／Android WebView（Blink） | `navigator.vibrate` 可用，需使用者手勢；跨域 iframe 受限 | W3C Vibration API Implementation Report（2026-04 核對原始碼）；caniuse |
| Web，Safari／iOS 全部瀏覽器（WebKit） | **不支援**，WebKit 正式立場 Oppose | 同上；caniuse 顯示 iOS 至 27.2 皆 ❌ |
| Web，Firefox | 桌面 129 起移除；Android 版有 API 但無效果 | 同上 |
| Godot | `Input.vibrate_handheld(duration_ms, amplitude)` 實作於 Android／iOS／Web；Android 需 VIBRATE 權限；iOS 指定時長需 iOS 13+；Web 不可調強度；Safari 等不支援 | docs.godotengine.org Input 類 |
| Unity／原生 iOS 精細觸覺（Core Haptics） | 〔待核實〕 | — |
- **結論**：Web 路線喺 **iOS 無法震動**（只可用聲音／畫面回饋代替）；Android Chrome 可。若觸覺係 iOS 賣點，須走原生殼（Godot／Unity／Capacitor 類，後者〔待核實〕）。設計上觸覺只作加分項，唔作必要回饋。

## 9. Q8 地圖工具
- **選用：Tiled**。授權〔查證〕：Tiled 編輯器本體與其外掛 GPL；`libtiled` 為 BSD 2-clause（github.com/mapeditor/tiled COPYING／LICENSE.BSD）；用 Tiled 製作嘅地圖／JSON 匯出屬作者自己作品，不受 GPL 影響，TMX／JSON 格式開放、無實作條件（Tiled 論壇作者回覆）；圖塊美術另有其授權。→ **適合公開 repo**（只要我哋自己嘅圖塊資產授權清楚）。
- 注意：本 repo 嘅示範地圖係**程序生成嘅 Tiled JSON 子集**，**未用 Tiled GUI 開啟驗證**〔待核實〕；匯入 Tiled 時需設定 tileset 路徑。
- **匯出格式**：JSON（orthogonal、`tilewidth=16`、`infinite=false`）。圖塊層用 `data` 陣列（gid，0＝空）；物件層用 tile object（含 `gid`）或 point object。
- **圖層命名（固定）**
| 層 | 型別 | 內容 |
|---|---|---|
| `ground` | tilelayer | 地面 |
| `decor` | tilelayer | 地面貼花（花、石、告示） |
| `occlusion` | tilelayer | 會遮住角色嘅圖塊（樹籬頂、拱門頂） |
| `collision` | tilelayer | 非 0＝不可行走 |
| `props` | objectgroup | tile object（樹、屋、燈、井）；腳印碰撞於生成時寫入 `collision` |
| `npcs` | objectgroup | `npc_<id>`；屬性 `display`、`sprite`、`dir`、`dialog`（對話 id）、`patrol`（`x,y;x,y`） |
| `portals` | objectgroup | `to_<map>`；屬性 `target`、`spawn`、`glow` |
| `lights` | objectgroup（point） | 名＝kind（lamp／window／banner／lantern／portal）；屬性 `radius`、`kind` |
| `spawns` | objectgroup（point） | `start`、`from_<map>`；屬性 `dir` |
| `events` | objectgroup | 門口（`door_<building>`）、對話觸發、日後遇敵區（`encounters`） |
- 地圖層級屬性：`name`、`tod`（day／dusk／night）。圖塊 gid＝`town_tiles.names.txt` 行號；道具 gid＝101＋`PROP_NAMES` 索引。
- 命名規則：小寫＋底線；物件名全局唯一；`dialog`／flag 等字串走 §12 規則。

### 9.1 第 2 週更新：直接載入遊美 Tiled（batch2 為準）
- `src/tiled.js`＋`town-lab.html`／`walk.html` 直接讀遊美 `tilemap_town.json`（40×30、external .tsj、extruded 版自動替換）。舊 corner 圖同遊策生成圖保留為 fallback（`?map=corner`／`?map=adv`）；舊程序生成頁保留為 `town-lab-gen.html`。
- 實際層名：ground／deco／occlusion／collision＋events 物件層（上表為早期程序版）。collision 值＝`gid − firstgid + 1`，firstgid 由 tilemap 讀（batch2＝545、舊圖＝193）。報告見 `docs/tiled-compat.md`。

## 10. Q9 碰撞與尋路（已實作、已測）
- **碰撞**：格子（16px）而非多邊形——`collision` 圖塊層；道具腳印矩形寫入格子；玩家用 AABB，**逐軸移動**（先 X 後 Y，貼牆滑行）；`moveBox`、`lineClear` 於 `town-map.js`。多邊形碰撞〔未做，M1 唔需要；斜牆／圓形物件才需要〕。
- **點擊移動**：A\* 於格網；8 向、**不切角**（斜走需兩側格皆可行）；結果以視線檢查平滑（`smoothPath`）；**觸控誤點容錯**：點中不可行格→自動跳去最近可行格（`nearestWalkable`，牆內／屋內點擊測試通過）。
- **性能**：JS 0.033 ms、Godot 0.0087 ms／條（§4）；路長一致。
- **NPC 巡邏**：巡邏點序列＋停頓；避讓＝簡單（NPC 同玩家遇阻即停等），**未做動態避讓／群體避障**。
- **未做／待決**：NPC 之間互相阻擋、移動障礙物導致重算、地圖大於 256×256 嘅 chunk 化 A\*。

## 11. Q10 對話系統
| 方案 | 授權〔查證〕 | 平台 | 評估 |
|---|---|---|---|
| **自建 JSON 節點＋旗標條件**（建議 M1） | 自家 | Web／原生皆可 | 零依賴、可匯出、同 `flags`（§13）直接對接；要自己做編輯流程 |
| ink（inkle） | **MIT**（含 inkjs，後者為社群維護）| inkjs 可喺 Web 跑；Unity 有整合 | 強大（條件、變數、選項、縫合）；需編譯流程，資料非純 JSON 節點 |
| Yarn Spinner | 核心庫／Unity 版 **MIT**；**Godot（GDScript）／Unreal 版為 Yarn Spinner Public License（YSPL）**：商用遊戲免費，但禁止拿去訓練 AI 同包裝成競爭對話工具 | Unity、Godot | 授權混合——用 Godot 版前須法務／Kurt 確認 YSPL 條款 |
| Dialogic（Godot） | **MIT**（v2 需 Godot ≥ 4.5） | 僅 Godot | 編輯器整合好，但綁定 Godot，唔利於 Web 先行 |
- **建議資料形狀（自建，未實作）**：
```json
{ "id": "dlg.elder.intro", "nodes": {
  "n1": { "speaker": "npc_elder", "text": "t.elder.intro.1", "next": "n2" },
  "n2": { "text": "t.elder.intro.2", "choices": [
     { "text": "t.elder.intro.c1", "if": "story.ch1.seen_race>=1", "set": {"story.ch1.met_elder": true}, "next": "n3" },
     { "text": "t.elder.intro.c2", "next": null } ] } } }
```
條件語法：`flag`、`flag>=n`、`!flag`、`a && b`（小型解析器，單元測試固定）。
- **現況（第 2 週）**：自建 dialogue/v1 已實作：`src/dialogue.js`（節點執行、cond、actions、lint）＋`src/dialogue-ui.js`（打字機、頭像、選項、skip）；12 個對白集由遊策文件匯入，`tests/dialogue.test.js` 173 斷言。匯入備註見 `docs/dialogue-import-notes.md`。

## 12. Q11 劇情工具流程＋本地化
- **撰寫**：遊策以**表格／Markdown**起草 → 轉成 `dialogue/*.json`（一檔一章）；檔案入 git，用 diff 比版本。
- **檢查**：腳本檢查——節點可達、`next`／`choices` 指向存在、旗標已登記於 `flags.md`、text key 存在於語言表、變數拼字；錯字用語言工具另行校對〔工具待遊策定〕。
- **本地化結構**：文字全部外置為 key：`locales/zh-HK.json`（先做）、`en.json`、`ja.json`（`settings.lang` 已預留）；key 規則 `t.<npc或場景>.<段>.<序>`；對白 JSON 只放 key。顯示時缺 key → 回退 zh-HK 並記 log。字型子集、換行（CJK 禁則）、文字速度（`settings.textSpeed`）列為 UI 工作。
- **匯入**：載入時校驗 schema，失敗時 fail loud（開發）／略過該節點（正式）。

## 13. Q12 存檔結構
已實作：`src/save.js`、`tests/save.test.js`（3438 項斷言通過）、**欄位表／遷移／存檔碼／衝突規則見 `docs/save-format.md`**。重點：版本化 JSON v1；v0（MVP）→v1 遷移；`too_new` 拒寫；存檔碼 `WRS1.<base64url>.<fnv8>`；Store 主檔＋備份；衝突 `conflict()`（超集優先、否則由玩家揀）。

## 14. Q13 事件／旗標
- **命名**：`<域>.<章或物>.<事件>`，小寫底線，≥2 段、≤5 段（`^[a-z][a-z0-9_]*(\.[a-z0-9_]+){1,4}$`，同存檔 sanitize 規則）。例：`story.ch1.met_elder`、`npc.fern.talked`、`item.key_moss.got`。
- **賽事完成集合**：`cleared[]` 存 matchId，格式 `cup.<盃id>.m<序>`（例 `cup.fernshade.m1`）；舊 MVP 關卡遷移為 `legacy.stage<N>`。
- **章節進度**：`chapter:{id,step}`；步驟只前進；`step` 由旗標集合推導時，以 `chapter` 為準。
- **對接賽事資料（A.4）**：賽事定義（隊伍、地形、AI）只引用 `matchId`；通關由 `Api` 結果事件觸發 → 寫 `cleared` ＋ 設相應旗標 → 對話條件讀旗標。旗標只增不改名；改名須寫遷移。
- 第 2 週：旗標＝扁平 snake_case（遊策），登記表 `data/flags.json`＋`docs/flags.md`；存檔 flag 規則放寬至單段。上面「≥2 段」係第 1 週草案，已被取代。

## 15. Q14–20：待後端週
14 後端選型、15 模擬權威／浮點跨平台（見 `replay-format.md` §7 嘅初步風險）、16 帳號、17 即時版、18 反作弊／私隱、19 平台優先、20 2P 近距碼——**全部「待後端週」，本輪不答。**

## 16. 缺口／未驗證清單
- 全部幀時間為無頭軟光柵；**真機（Android 中低階、iOS）未測**。
- Unity：完全未實測；數字／功能均〔待核實〕。
- `?art=1` 真素材 fx-lab 已重建（見 §3.1）；仍係無頭軟光柵數字，**headless, not a real device**。
- Godot：未測 Web／Android 匯出、後處理、記憶體、真 GPU。
- Tiled GUI 開啟地圖未驗證；對話系統只有設計無實作；`flags.md` 未建。
- bloom 單獨成本、體積光未測。
