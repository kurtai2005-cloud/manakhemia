# 6b 散步美術（現實世界連動）— 遊美 2026-11-02

Kurt 親口批「6b 全部做」。全部 Pillow／numpy 程序化像素，冇 AI 圖；alpha 只得 0／255；光源左上；冇字（所以冇 FP12 問題）。
重跑：`python3 art-pet/tools/build_breakthrough_6b_walk.py`；驗：`python3 art-pet/tools/validate_breakthrough_6b.py`（21/21）。
資料：`walk6b.json`（全部 key、尺寸、pivot、模式、色數）。

## Key 一覽
| key | 檔 | 尺寸 | 備註 |
|---|---|---|---|
| `6b:walk_bg` | `walk_bg.png`／`walk_bg@3x.png` | 100×120（@3x 300×360） | 直向，全幅不透明，12 色（取 H1 palette＋暖桃天）。地平線 y=30；`stones` 6 粒踏腳石＝路上「格」位（由遠到近，可當 1000 步 1 格嘅落腳點）；`pathCenter` 每 4 行路中線 x |
| `6b:walk_clip` | `per_pet/<形態>/walk.png`／`walk@3x.png` | 橫條：幀 i 喺 x＝i×frameW | 49 隻，6 幀，10 fps loop（600ms）|
| `6b:deco_pebble` 等 8 個 | `deco/deco_<名>.png`／`@3x` | 16×16（@3x 48×48） | pebble 圓石仔、maple_leaf 紅葉、acorn 橡果、feather 羽毛、snail_shell 蝸牛殼、clover4 四葉草、button 鈕扣、ribbon 絲帶 |
| `icon_walk` | `ic_walk@1x.png`／`ic_walk@3x.png` | 16×16（@3x 48×48） | rail「散步」：小波鞋。同 kit_hd2d_v2 `icons/ic_*` 同規格同渲染（三階左上光＋#24172C 外描＋臉），可直接取代借用嘅 `ic_expedition` |

## walk_clip 規格
- **幀大小＝該形態 idle 幀大小，pivot＝idle pivot（同 6a faces6a.json 一致）**，所以可以直接頂替而家用緊嘅 idle 幀 0，唔使改對位。
  - 注意：唔係全部 48×48。分佈：48×48 pivot(24,45)：33 隻；44×44 pivot(22,41)：9 隻；64×64 pivot(32,61)：3 隻；32×32 pivot(16,29)：2 隻；28×28 pivot(14,25)：1 隻；38×38 pivot(19,35)：1 隻。
    如果引擎一定要 48×48 格，請按 pivot 對齊貼入 48×48（pivot→(24,45)）；64 幀（radiant／soft／lumi）內容闊過 48，要縮圖或者留原大。
- 向右行；向左用 flipX，pivot x 鏡像成 `W−1−px`。
- 6 幀 @ 10 fps，loop。由 idle 幀 0 **逐粒搬位**衍生：冇縮放、冇旋轉、冇新色（每幀色 ⊆ idle 色）。
- 兩種模式（`walk6b.json` 每隻 `mode`）：
  - `feet`（32 隻，有分開嘅腳）：身體 bob 0/−1、左右腳交替提起 1–2px、前後 ±1px；前推幀上半身向前 1px（lean）；身升起時腳頂補一格，唔會甩腳。
  - `hop`（17 隻，冇分開腳：evo_dot, A1, B1, B2, B3, C1, C2, C3, D1, D2, E1, E2, F1, F2, G1, G2, H2）：細彈跳 0/−1/−2/−2/−1/0，前 2 格上半身向前 1px。
- 每幀總有一幀底行＝idle 底行（踏地），內容唔出幀。

## 已知問題
- 舊 4a／evo 線同 from_ref 新線嘅 idle 幀 0 本身已經超過 12 色（42 隻），clip 冇加色，只係沿用 idle 色；如要 ≤12 要先處理 idle。
- lean 係上下半身 1px 錯位，大隻形態側邊會見到 1px 級級，屬像素動畫常見做法。
- 冇 ground shadow；如果背景要影，引擎畫一個橢圓（同 idle 一樣）。
- 預覽 `preview_6b_3x.png`：左上背景（放咗一隻 evo_still_radiant 喺第 5 粒石上，實際大細／縮放由引擎決定）、左下 8 deco＋金框 icon_walk、右邊 10 隻形態 6 幀。
