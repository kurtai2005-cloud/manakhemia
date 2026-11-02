# #83 HD-2D V3 美術缺件／未接清單

來源：本機 art repo `art/workscenes-v3` @ 23471a4a（tree e704a33c），`tools/import_v3.py` 只抽需要嘅檔落 `art/v3/`。全部自家美術，冇第三方素材（冇八方旅人）。

## 缺圖（runtime）
今次範圍內 **0 張缺圖**：花園 H1–H4、四季 × H1–H4（16 款）、petGlow（團絨＋細佬）、屋仔 4 房 × 日／夜、傢俬／手信、窗光 3 款、walk_bg 日／黃昏／夜、UI atlas／icon（@3x、@6x）、Noto CJK TC subset 全部載到
（`__qa.hd2d.v3().missing`、`__qa.house.v3().missing`、`__qa.l6b.v3().missing` 都係 `[]`；`tests/v3.test.js` ⑧ 驗齊）。
如果之後有圖缺，畫面會出洋紅虛線框＋尺寸（6b 規則）。

## 有規格、未接／照舊
| 項目 | 狀況 | 要乜 |
|---|---|---|
| 頭像（portrait） | V3 包只有 `ui/portrait/portrait_rects.json`，冇頭像圖 → 照用 v2 頭像 | V3 頭像框＋寵物頭像 @3x（如要換） |
| 「收埋 UI」掣 icon | 照用 6b.3 canvas 點陣眼 | 可選：`icon_ui_hide/show` @3x（見 MISSING_ART_6b3.md） |
| 屋仔手信多位（HOUSE_V3 floor_2 取代 shelf_0） | 遊戲而家得 1 個手信位（DECO_ANCHOR），程式冇 shelf_0 → 多位規則未用 | 遊策定多個手信位先接 |
| 屋仔即時倒影 | 只做傢俬；寵物倒影未做（規格可選） | — |
| 夢遊 6c V3／族譜／工作場景 | 範圍外：留俾 6c、#78 | — |
