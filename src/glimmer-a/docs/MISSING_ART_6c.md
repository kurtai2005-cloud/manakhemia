# 6c「夢境探險」美術缺件清單

依家全部用程序畫嘅 placeholder 頂住（洋紅虛線 outline＋`data-ph`），UI 外框跟 6b.2（金邊半透明 CSS 面板，唔使新圖）。全部要原創，唔用任何第三方素材、字型或者圖案。

| 用途 | `data-ph` | 檔名建議 | 尺寸（CSS px） | 像素原圖 | 而家點頂 |
|---|---|---|---|---|---|
| 夢境 tileset・蘑菇森林（餵菇） | `6c:tile_forest` | `art/series2_long/6c/tile_forest.png` | 每格 100×100（3×5 地圖） | 50×50／格，最少 4 款變化 | 程序畫：綠地＋紅菇 |
| 夢境 tileset・水珠湖（淋水） | `6c:tile_lake` | `…/6c/tile_lake.png` | 100×100 | 50×50／格 ×4 | 程序畫：藍水波 |
| 夢境 tileset・玩具房（玩得多） | `6c:tile_toy` | `…/6c/tile_toy.png` | 100×100 | 50×50／格 ×4 | 程序畫：紫地＋積木 |
| 夢境 tileset・星空（夜晚嚟） | `6c:tile_star` | `…/6c/tile_star.png` | 100×100 | 50×50／格 ×4 | 程序畫：深藍＋星 |
| 團絨夢中行 clip（形狀變化） | `6c:dream_walk` | `dream_walk` clip（每個形態） | 80×80 | 40×40，6–8 幀，10fps | 暫用現有 idle 幀 0＋上下 bob |
| 睡帽疊層 | `6c:nightcap` | `…/6c/nightcap.png` | 36×28 | 18×14（跟 dream_walk 幀對位） | 程序畫藍白睡帽 |
| 夢碎片 icon | `6c:frag` | `…/6c/frag_<theme>.png` ×4 | 48×48 | 24×24，3 幀閃 | 程序畫十字星 |
| 夢圖鑑卡 ×20（f1–f5 森林、l1–l5 湖、t1–t5 玩具、s1–s5 星空） | `6c:card_<id>` | `…/6c/card_<id>.png`＋未解鎖剪影 `card_back.png` | 56×72 | 28×36 | 程序畫：已有＝主題色小圖，未有＝「?」剪影 |
| 入夢／出夢過場 | `6c:transition` | `…/6c/transition.png`（或 8 幀 sheet） | 390×844 全畫面 | 195×422 | CSS 放射漸層淡入淡出 1.2 秒 |
| 主 rail「入夢／夢簿」icon（可選） | — | `icon_dream_rail` | 36×36 | 72×72／@3x 108 | 暫用 5b `icon_rest` |

字型：標題／掣／分組標題照用自家 GlimmerFP12（6c 新字已入 `fonts/fp12-subset.ttf`）；內文 18、輔助 16 用系統 Noto Sans HK（裝置內建，唔打包）。

家具獎勵（砌齊主題送）用 5a 現有擺設：細蘑菇 `sv_mushroom`、七彩貝殼 `sv_shell`、彩虹糖 `sv_rainbow`、星星石 `sv_starstone`，冇新家具圖要畫。
