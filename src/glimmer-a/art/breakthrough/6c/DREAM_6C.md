# breakthrough 6c 夢境探索 — 美術交付（遊美，2026-11-02）

依據：`docs-gdd/breakthrough-6a6d-spec.md` §6c（spec 優先）；尺寸／key 對齊遊程未 commit 嘅 6c code（`st_long6c.js`／`st_long6cui.js` placeholder）。
全部 Pillow／numpy 程序化像素，冇 AI 圖；alpha 只得 0／255；新畫嘅嘢每件 ≤12 色；光源左上；每個 1x 都有 `@3x`（nearest ×3）。
Builder：`art-pet/tools/build_breakthrough_6c_dream.py`（＋`_6c_tiles.py`、`_6c_cards.py`、共用 `bt6_px.py`）。
驗證：`python3 art-pet/tools/validate_breakthrough_6c.py` → **29/29 PASS**。機讀：`dream6c.json`。

## Key／尺寸／幀
| key | 檔（1x；@3x 同名加 `@3x`） | art 尺寸 | 幀／fps | 備註 |
|---|---|---|---|---|
| `6c:tile_forest` `6c:tile_lake` `6c:tile_toy` `6c:tile_star` | `tiles/tile_<th>.png` | 224×56（56×56 ×4 款橫條） | — | 款 v 喺 x＝v×56；顯示 112 css（×2）；中間留空俾團絨企 |
| `6c:fog` | `tiles/fog.png` | 56×56 | — | 未揭開格；75% 實色棋盤，取代 CSS `rgba(10,8,26,.82)` |
| `6c:frag_<th>` | `icons/frag_<th>.png` | 16×16 | — | 夢碎片（森林孢子／水珠／玩具星／星屑）；code 顯示 48 css＝16×3 |
| `icon_dream` | `icons/ic_dream.png` | 16×16 | — | rail「入夢」（月亮戴睡帽），可取代借用嘅 5b icon_rest |
| `icon_dreambook` | `icons/ic_dreambook.png` | 16×16 | — | 夢卡圖鑑入口 |
| `6c:card_<id>` ×20 | `cards/card_<id>.png` | 28×36（56×72 css） | — | 金框＋主題底＋插畫窗；底部 5 粒序號（亮＝第幾張）；**卡面冇字**，標題由 code FP12 寫 |
| `6c:card_back` | `cards/card_back.png` | 28×36 | — | 未解鎖 |
| `6c:transition` | `fx/transition_in.png` | 1950×422（195×422 ×10） | 10 幀 @8fps＝1250ms | 入夢順播 0→9（夜幕由外圍收埋，尾 3 幀月亮浮現，最後一幀全滿）；出夢倒播 9→0；未覆蓋位透明 |
| `6c:dream_bg` | `fx/dream_bg.png` | 195×422 | — | 夢境地圖底（夜空＋星＋底雲），全幅不透明，可取代 code 畫星 |
| `6c:nightcap_S/M/L` | `nightcap/nightcap_<S\|M\|L>.png` | 23×10／35×15／46×19 | — | 由 `accessories/nightcap` front＋tail 合成；json 有 pivot（帽簷底中） |
| `6c:dream_walk` | `per_pet/<pid>/dream_walk.png` ×49 | 幀大小＝該形態 idle（32×32 或 48×48），橫條 ×6 | 6 幀 @6fps＝1000ms，loop | 閉眼夢遊；向右，向左 flipX（pivot x 鏡像 W−1−px） |

卡 id（同遊程 CARDS 一致，冇改）：f1 會唱歌嘅菇、f2 菇傘下避雨、f3 森林博士上堂、f4 巨型暖菇飯、f5 菇菇捉迷藏；l1 水珠浮浮、l2 湖底月光、l3 游水冠軍、l4 雨點合唱團、l5 倒影另一隻我；t1 積木城堡、t2 發條團絨、t3 波波池、t4 玩具火車、t5 拼圖少一塊；s1 數星星、s2 流星許願、s3 月亮韆鞦、s4 團絨星座、s5 銀河散步。

## dream_walk 做法
idle 幀 0 → 閉眼（`rig.eyes[i].pix` 填返 skin 色，用原本 ink 色畫 ‿）→ 沿用 6b 步序（32 隻 feet、17 隻 hop），只搬像素、唔縮放／旋轉、冇新色。
比 6b（10fps）慢：6fps，似瞓眼惺忪咁行。

## 睡帽 overlay（spec「形變＋睡帽 overlay」）
`dream6c.json → pets.<pid>.nightcap`：`size`（S 9 隻／M 19／L 21，按頭頂下 2 行頭闊揀）、`xy`＝每幀帽圖左上角喺該幀嘅 art 座標（跟 lean／bodyDy 郁；可以係負數＝出幀，所以帽**唔可以**畫喺 clip 幀入面，要另一層、唔好 clip overflow）、`z: above`。
向左行：`x' = frameW − x − capW`，帽都要 flipX。

## 3×5 格
tile 56 art＝112 css；遊程 TX＝23＋c·116 css → art x＝11.5＋58c（半格會糊），建議 TX 改 22 或 24 css。preview 用 x0＝11 art（22 css）、y0＝64、gap 2。

## 已知問題
- 睡帽 L 46×19 遠大過遊程 placeholder canvas 18×14（left 24／top −4 css 固定位）；要改讀 json 逐隻逐幀位置。
- 少數形態頭頂有葉／觸角／火苗，睡帽會遮住部分（例：sprout 葉）；未做逐隻避位。
- 碎片 icon 16×16，遊程 slot 係 24 canvas／48 css：16×3＝48 css 啱，canvas 改 16 或置中。
- 卡插畫細（20×21 窗），屬 v1，可以之後逐張加細節。
- dream_walk 冇睡帽合成版（因帽會出幀）；preview 係合成睇效果。
