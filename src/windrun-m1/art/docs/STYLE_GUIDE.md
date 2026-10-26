# 《風野競走》HD-2D 風格指引 v0.1（遊美）
> 2026-10-26｜M1 週1 前半｜全原創、全程式化自製（無第三方／光碟素材）｜對齊 `pet-one-pager.md` §10「夜燈絨毛感」＋ `art-pet/HD2D_STYLE.md`
> 風格板：`tracks/mossy_slope/style_board_mossy_slope.png`　垂直切片：野靈「窄樑貓」＋賽道「苔坡」

## 1. 風格定義
- **像素野靈**：64x64（部分 48x48）硬邊、無抗鋸齒、1px 外框（ink #2B2540，唔用純黑）、3 階 cel 色（高光／底／陰影，光源左上）。野靈 sprite **唔畫投影、唔烙模糊**。
- **立體場景**：分層視差（sky_far／mid／track／fore）；景深、bloom、tilt-shift、光圖由引擎後處理做。場景像素密度＝野靈像素之一半（野靈 6x、場景 2x），令角色「浮」喺較細緻嘅微縮模型上。
- **夜燈絨毛感**：低飽和冷藍夜＋暖黃燈籠，柔光、微縮感；日／黃昏／夜由同一套圖＋調色參數切換（只有 sky_far 分 3 張）。
- **可讀性鐵則**：①剪影清楚（野靈明度高於跑道）；②跑道永遠係最清晰一層；③5 地形主色相距 ≥60° 色相，一眼分；④技能／適性用光色，唔靠文字。

## 2. 色盤
### 2.1 野靈統一色盤（32 色＋透明 idx0；8 隻共用，每隻取子集）
| 組 | HEX（暗→亮） |
|---|---|
| 墨／深紫 | #2B2540 ink、#4A4066 plum |
| 石板藍（毛色） | #55618A、#7482B0、#9AA8D0、#C8D2EE、#F3F6FF frost |
| 沙米 | #D9B98C、#F0D6A8、#FBEBCB |
| 棕 | #5E3F3A、#8A5A44、#B98258 |
| 橘 | #D9692F、#F2A65A、#FFC87A |
| 燈黃光 | #FFD45E、#FFE98A、#FFFBD0 |
| 玫粉 | #D9667A、#F28B9B |
| 苔綠 | #2F6B45、#4FA05A、#8CD27A |
| 青（風）| #2E8F93、#4FD0C8、#A8F5E8 |
| 海藍 | #2A5E9A、#4FA3D9、#A6DAF2 |
| 紫 | #6A5BAA、#A99BE0 |
規則：每隻 ≤24 色（含技能 fx）；外框一律 ink；高光偏暖、陰影偏紫（plum／violet）；技能光只用「青／黃光／海藍／苔綠」組。完整 JSON：`palette/spirit_palette.json`（`spirit_palette.png`）。窄樑貓用 21 色（見 `sprites/narrowcat/palette_used.json`；含光色／fx）。

### 2.2 苔坡環境色盤（完整；`palette/env_palettes.json`、`mossy_palette.png`）
| 用途 | HEX |
|---|---|
| 遠山／近山 | #8FB3B8／#6E9AA0（再按時段混向天空底色） |
| 遠樹 底／亮 | #4E7E7A／#6A9C92（陰 #2F5F5C） |
| 近樹 底／亮／暗 | #2F5F5C／#477F76／#1F3F45 |
| 樹幹 | #2B2540（亮 #4A4066） |
| 燈籠 框／身／芯／邊 | #2B2540／#FFC87A／#FFFBD0／#D9692F |
| 苔 暗→亮 | #244F3A、#3E8250、#5AA85E、#8CD27A、#B9EE9A |
| 跑道泥徑 | #5E3F3A（暗）、#8A5A44、#B98258（底）、#D9B98C、#F0D6A8 |
| 石 | #6B7288、#9AA3B8、#C8D2EE |
| 前景草 暗→亮 | #1B3B35、#2F6B45、#6FBF6A、#B9EE9A |
| 螢火 | #FFE98A（芯 #FFFBD0） |
天空日 #7FC2F0→#FDF3D8｜黃昏 #4E4F92→#FFB27A｜夜 #10163A→#2F3C78（18 階＋4x4 Bayer 抖色）。

### 2.3 五地形主色（碎礫／淺灘／霜面／懸橋 只列主色，待 M1 後段／M2 展開）
| 地形 | 主色 | 暗 | 亮 | 重點 | 一眼辨識 |
|---|---|---|---|---|---|
| 苔坡（完整） | #5AA85E | #244F3A | #B9EE9A | #FFC87A 燈 | 綠＋暖泥徑 |
| 碎礫 | #8E8479 | #5B5046 | #C9B79C | #E0A458 | 暖灰褐＋碎石 |
| 淺灘 | #4FA3D9 | #2A5E9A | #A6DAF2 | #EAD7A8 沙 | 藍＋水光 |
| 霜面 | #DCEBFA | #6A7FB8 | #FFFFFF | #B5F0FF | 白冰藍＋冰屑 |
| 懸橋 | #8A5A44 | #3A2F5C（深淵紫） | #D9B98C | #E5584D 旗 | 木棕＋紫黑深淵 |
地形粒子色：苔坡草屑 #8CD27A／#B9EE9A；碎礫 #C9B79C；淺灘 #A6DAF2；霜面 #FFFFFF／#B5F0FF；懸橋 #D9B98C。

## 3. 光色規則
**時段**（引擎調色參數；乘色 tint＝RGB 乘數，亮度 br；同 `build_mossy_slope.py` 的 GRADE）
| 時段 | tint | br | 暖燈強度 | 月光冷光 | bloom | 主光／環境 |
|---|---|---|---|---|---|---|
| 日 | 1.00,0.99,0.94 | 1.00 | 0 | 0 | 0.22 | 主 #FFF1CC／環 #8FB4E8 |
| 黃昏 | 1.00,0.76,0.70 | 0.86 | 0.75 | 0.12 | 0.42 | 主 #FFA55C／環 #7A5FA8 |
| 夜 | 0.50,0.60,0.98 | 0.78 | 1.00 | 0.55 | 0.62 | 月 #7FA8FF＋燈 #FFB060／環 #1E2347 |
- 各層調色強度：sky 0.55、mid／track／fore 1.0（fore 0.9）、**野靈 0.45**（保持剪影可讀）。
- 暖燈光圖色 #FFB060（核 #FFECAA）；月光冷色 #6082DC。
- **野靈邊光（rim）**：只喺黃昏／夜，左上輪廓 1 sprite-px，黃昏 #FFBE78、夜 #96BEFF；由引擎疊，唔烙入 sprite。
- 野靈接地用 **blob shadow**：橢圓約 60x7 sprite-px，#241834 α0.45，模糊 σ6。
**技能光色**（蓄力→爆發→光環皆同色組）
| 技能 | 主光 | 色組（暗→亮） |
|---|---|---|
| 疾風衝 | 風青 | #2E8F93／#4FD0C8／#A8F5E8（眼 #FFFBD0 發光） |
| 絆草 | 苔綠＋暗紫 | #2F6B45／#8CD27A／#6A5BAA |
| 回氣 | 暖金 | #D9692F／#FFD45E／#FFFBD0（＋粉 #F28B9B 星點） |
| 風罩 | 冰藍白 | #2A5E9A／#A6DAF2／#F3F6FF |
**適性 4 級圖示色**：陌路 #8F85C2（紫灰，1 格）｜識路 #4FA3D9（藍，2 格）｜熟路 #6BBF6A（綠，3 格）｜乘風 #FFD45E（金＋青閃，4 格）。除顏色外必加「格數／形狀」輔助（色盲友善），圖示 M1 UI 工作項 5.4a 做。

## 4. 尺寸規格
- **參考畫面**：橫向 1920x1080（16:9，其他比例左右擴／裁，安全區中央 1600x900），WebGL／Canvas 邏輯像素；UI 另計。
- **野靈**：64x64 畫布（身形約 52x42）；小型 48x48（同一 pivot 規則）；整數倍放大 **6x（1080p）**，即螢幕約 384px。腳底線＝sprite y=61，**pivot (32,61)**，朝右，跑道線 y=940。
- **動畫幀數／fps（每隻野靈同標準）**
| state | 幀 | fps | loop | 備註 |
|---|---|---|---|---|
| run | 6 | 12（引擎按速度×0.6–1.4 縮放） | ✓ | 步頻跟速度，乘風快／陌路慢 |
| idle | 4 | 6 | ✓ | 呼吸、眨眼、尾擺 |
| skill_charge | 2 | 8（0.25s） | ✗ | 蓄力：光眼、聚光粒 |
| skill_burst | 2 | 12 | ✓ | 爆發＋持續光環，直至技能完 |
| win | 4 | 8 | ✗ | 蹲→跳→頂點→落地 |
| lose | 2 | 3 | ✓ | 垂頭坐低 |
- **場景分層（邏輯 px；顯示 2x；全部橫向無縫 tile 寬 1024）**
| 層 | 檔 | 尺寸 | 螢幕 Y（邏輯） | 備註 |
|---|---|---|---|---|
| sky_far | sky_far_{day,dusk,night} | 1024x540 | 0 | 不透明；星月、雲、兩層遠山 |
| mid | mid | 1024x320 | 160 | 透明；遠杉＋近圓樹＋燈籠線 |
| track | track | 1024x220 | 320 | 透明上緣；野靈跑道線 y=150（螢幕 940） |
| fore | fore | 1024x540 | 0 | 半透明草葉＋螢火；底貼 540 |
- 圖集：**≤2048x2048**，padding 2px，extrude 1px，PNG-24 RGBA sRGB；野靈圖集 `spirit_<名>_atlas.png/json`，場景層單獨貼圖（不入圖集，寬 1024）。
- **命名**：`spirit_<id>_<state>_<NN>.png`（NN 從 01）；`<layer>[_<time>].png`；`lightmap_<kind>.png`；`fx_<name>_<NN>.png`；`style_board_<track>[_<variant>].png`。id／track 小寫英數底線。

## 5. 後處理規格（高／中／低三檔；數值＝1080p 螢幕 px，σ＝高斯標準差）
| 項 | 高 | 中 | 低 |
|---|---|---|---|
| 景深 | 即時模糊：sky σ5、mid σ2.6、fore σ7、track 0（1/2 解析度模糊再放大） | sky 載入時預模糊一次；mid 用 `mid_lowfx`；fore 即時 1/4 解析度 σ7 | 全預烘：`mid_lowfx`、`fore_lowfx`、sky 預模糊；零即時模糊 |
| bloom | 亮度閾 0.78（夜 0.70）；1/4 解析度雙 pass（σ4＋σ12）；強度＝GRADE.bloom×0.9；lantern 另加 `emissive_mid` σ9 疊加 | 閾 0.78；1/4 解析度單 pass σ8；強度×0.7 | 關；只用 lightmap 暖光做假 bloom |
| tilt-shift | 焦點帶 y 30%–90%，上下漸變最大 σ6（1/2 解析度） | 關（用 vignette 代） | 關 |
| 光圖 | lightmap_warm／track／cool 加法混合（ADD），強度見 §3；另 ≤4 盞即時點光（野靈自帶微光、技能光） | 光圖 ADD，即時點光 ≤2 | 光圖 ADD 只留 warm，即時點光 0 |
| vignette | 即時，強度 0.3（夜 0.45） | 用 `vignette.png`（960x540 放大 2x） | 同中 |
| 預算建議 | 後處理 ≤4 ms／幀（中階 Android） | ≤2 ms | ≤0.5 ms，目標 ≥30 fps |
**自動降檔**：連續 2 秒幀時間 >20 ms → 降一檔；60 fps 穩定 10 秒才升一檔；省電模式強制低檔。**風格板**係「高」檔模擬（Pillow）；引擎實裝後以此板對照調參。

## 6. 引擎對接備註（HTML5 Pixi／Phaser／Godot 皆可）
- 紋理：野靈、fx **Nearest**、關 mipmap、整數倍縮放（6x）；場景層同樣 Nearest 2x（blur 由後處理做，唔好用 linear 放大）。
- 分層（z 低→高）：sky_far → lightmap_cool（ADD）→ mid → lightmap_warm（ADD，同 mid 視差）→ track → lightmap_track（ADD）→ 野靈 blob shadow → 野靈 → fx（草屑）→ fore → 後處理（bloom→tilt-shift→vignette）。
- 視差速度（相對 track＝1.0）：sky_far 0.05、lightmap_cool 0.2、mid（含 warm／emissive）0.35、track 1.0、fore 1.6。建議 1 m＝24 螢幕 px。
- tile：每層 `x = -(cam * k) mod 1024*scale`，並排兩張。
- 野靈錨點＝pivot (32,61)；`atlas.json` 內 `pivot` 為 0.5,0.953；Godot 用 `offset`；唔好 trim（姿勢位移已烘入幀）。
- 景深層：sky／mid／fore 各自 render texture 先模糊；track 同野靈唔模糊。fore 層建議 α0.92。
- 地形切換（每 200 m 一段）：換 track／mid（及 fx 色）貼圖，1 秒 crossfade；sky 與時段不變。

## 7. AI 草稿使用與來源記錄規則
1. 首選程式化自製（Pillow／numpy，腳本入 `tools/`，可重跑）；M1 目前 **零 AI 圖**。
2. 如用 GenerateImage 做草稿：只作構圖／色調參考，**唔直接入庫**；必須人手重繪／量化到統一色盤、統一 1px 外框。
3. 每份素材記 `ASSET_LOG.md`：檔名、日期、來源（腳本名或 prompt 全文＋工具）、後續修整、相似度檢查結果。
4. 不放任何第三方／光碟素材；prompt 不寫現有 IP／角色名／「X 風格」。
5. 每隻新野靈出 `contact_sheet.png`（run＋idle，8x，無字）做以圖搜圖相似度檢查（TinEye／Bing／Google Lens），結果記 ASSET_LOG；上線前再做商標／風格比對（承接 plan 第 10 節）。
