# 6c「夢境探險」美術狀態

2026-11-03（HKT）：已接 Kurt 交嘅 6c 美術（art 6c @ af5b4821 → `art/breakthrough/6c/`）同 walkdream-v3（ba0d4345 → `art/breakthrough/6c/v3/`）。全部原創，冇第三方素材。
圖未載到／載唔到先退返程序畫 placeholder（洋紅虛線 outline＋`data-ph`）；`?l6cart=0` 強制 placeholder（QA 用）。

## 已用

| 用途 | V3 開（預設） | V3 關（`?v3=0`） | 顯示 |
|---|---|---|---|
| 夢境背景 | `v3/dream_bg/dream_bg_v3@3x.png`（烘好嗰張） | `fx/dream_bg.png` | 全畫面 |
| 4 主題 tileset（森林／湖／玩具房／星空）×4 變化 | `v3/tiles/tile_<th>_v3@3x.png`＋`tile_<th>_glow@3x.png`（呼吸，跟 json flicker）＋湖 `tile_lake_caustic@3x.png` | `tiles/tile_<th>.png` | 每格 56 art px＝112 CSS（整數 2×），變化＝(格號＋夜晚 hash)%4 |
| 未揭格霧 | `v3/tiles/fog_v3@3x.png` 8 幀 4fps；揭開 `fog_reveal@3x.png` 8 幀 500ms＋`tile_reveal_glow@3x.png` 閃 | `tiles/fog.png`（75% 棋盤） | |
| 夢碎片 | `icons/frag_<th>@3x.png` | 同 | 48 CSS |
| 團絨夢中行 | `per_pet/<form>/dream_walk`（49 個形態，6fps，pivot 對位，1 art px＝2 CSS，向左 flipX） | 同 | |
| 睡帽 | `nightcap/*`（dream6c.json 逐幀 xy） | 同 | |
| 入夢／出夢過場 | `v3/transition/transition_in_v3_00–09@3x.png` 10 幀 125ms（入 0→9；出 0→9 → 小結 9→0） | `fx/transition_in.png` | 全畫面 |
| 夢圖鑑卡 ×20＋未砌 card_back | `v3/cards/card_<id>_v3@3x.png` | `cards/card_<id>.png` | V3 84×108／1x 28×36 原尺 ×2 |
| rail「入夢／夢簿」icon | `icons/ic_dream.png`／`ic_dreambook.png` | 同 | 32 CSS |

V3 開時夢入面寵物光＝0（v3 petGlow state `dreaming`）。

## 有圖但未用（等 Kurt 話用唔用）

- `card_glow`、`card_shine`（新卡砌到嗰下嘅閃光）
- tile emissive mask（已用 glow 層頂）
- dream_bg 分層 stack（用咗烘好嗰張；parallax 未做）
- motes 浮塵、流星、moon flare、LUT
- 6b/v3 walk V3-A（花園行路 V3 版）未 merge — 唔屬 6c，等 Kurt 決定

## 冇缺圖

家具獎勵用 5a 現有擺設（`sv_mushroom`、`sv_shell`、`sv_rainbow`、`sv_starstone`）。字：V3 開用源雲明體 GenWanMin2 TC R／SB（OFL 1.1，已打包，`tools/font_v3_subset.py` 出子集），V3 關照 6b.3 規則（標題 FP12）。
