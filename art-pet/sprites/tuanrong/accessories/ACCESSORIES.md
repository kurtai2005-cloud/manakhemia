# 團絨 飾品 — 格式同引擎用法（ACCESSORIES）
遊美 2026-11-01，ACC1。分批計劃見 `ACC_PLAN.md`，spec 見 `ACCESSORIES.json`。全部用 Pillow／numpy 程式畫，冇 AI；飾品像素一律 v3 色盤，alpha 只得 0／255。

## 檔案
- `ACCESSORIES.json`：`slots`（每個 slot 最多 1 件）、`drawOrder`、`sizeClasses`（S ≤32、M 38–48、L 64）、`items`（13 件總表，status 分 done／planned）、`items.<key>.forms.<form>`（atlas 路徑、clips、visibleClips、frames、hidden、variant）、`fitRules`。
- `items/<item>/atlas_<item>_<form>.png/json`：TexturePacker 風格（frames／animations／hiddenClips／meta），padding 2、extrude 1，每幀 trim 過。
  - `spriteSourceSize` 係相對身體幀左上角計，可以係負數，即係飾品超出 frame 邊（overlayPad＝8）。
  - `sourceSize` 同身體幀一樣大。
  - `animations.<clip>` 嘅 fps／loop 抄身體 atlas。
- `items/<item>/fit_<item>.json`：每幀 fit 記錄（top、hw、ws、hs、ang、位置），validator 用嚟對位，亦方便日後手調。
- `ref/acc_<item>_{S,M,L}.png`：單件參考 sprite（衣櫃 icon／設計對照），分別由 sprout、evo_guard_radiant、radiant 嘅 idle_01 出。

## 引擎（遊程）
1. 畫法：身體 → 臉 → 飾品（`drawOrder`）→ emissive。飾品同身體用同一個 position、pivot 同 scaleX；鏡像時兩者一齊翻。
2. 揀幀：飾品幀名＝身體當前幀名。如果個 clip 喺 `hiddenClips`，成段唔畫，切返出嚟先再畫，唔會逐幀閃。
3. 冇需要喺 runtime 計 anchor 同變形，全部已經 bake 入每一幀。

## ACC1 數量
| item | 名 | slot | 幀 | clip（可見／總） | 備註 |
|---|---|---|---|---|---|
| straw | 草帽 | head | 4524 | 1030/1055 | 月眠／菇傘 4 個形態用帽針版；leaf_umbrella 收起 |
| bow | 蝴蝶結 | side_r | 4674 | 1055/1055 | 貼 head_r，跟傾角轉 |
| scarf | 頸巾 | neck | 4674 | 1055/1055 | 順剪影畫，尾巴有慣性 |

## 手調表（`tools/build_accessories.py`）
- `AXIS`：lumi 系 3 個形態用眼線定 axis，因為佢哋個 bulb 錨點係頭頂芽。
- `FIT`：逐形態 dx／dy／sc／variant。帽針版放月眠帽右邊、菇傘帽左邊；靜光燦光、柔光、火苗、月眠嘅帽同結大細有手調。
- `NECK_LIM`：靜光月眠頸巾唔包月牙。
- `HIDE`：手動收起嘅 clip 連原因。

<!-- ACC2-START -->
## ACC2 數量（2026-11-01）
| item | 名 | slot | 幀 | clip（可見／總） | 備註 |
|---|---|---|---|---|---|
| beanie | 毛冷帽 | head | 4524 | 1030/1055 | 針織直坑、反邊、pompom 偏左；月眠／菇傘帽針版；leaf_umbrella 收起 |
| acorn | 橡果帽 | head | 4524 | 1030/1055 | 鱗片紋＋帽邊＋帽蒂；帽針版；leaf_umbrella 收起 |
| crown | 小皇冠 | head | 4524 | 1030/1055 | 64px 形態加細節；帽針版；leaf_umbrella 收起 |
| straw（polish） | 草帽 | head | 4524 | 1030/1055 | 穩定化＋月眠守護帽針加大＋lumi 系莖洞執靚（幀名同數量不變） |

### head slot 手調（ACC2 起）
- `HEAD`：每件頭飾嘅闊（k×頭闊）、高闊比、沉落深度、帽針版大細同斜角。
- `stabilise_head`：頭頂點對中＋相對身體 bbox 平滑、ws median-3 夾 0.85–1.12、傾角每幀 ≤8°。validator 會檢查後兩項。
- `CUT_FULL`：lumi 系只挖葉同葉描邊。
- `FIT`：新三件沿用草帽嘅靜光燦光／柔光／火苗 sc；月眠守護帽針 sc 1.8，月眠靜光 0.8。
<!-- ACC2-END -->

<!-- ACC3-START -->
## ACC3 數量（2026-11-01）
| item | 名 | slot | 幀 | clip（可見／總） | 備註 |
|---|---|---|---|---|---|
| starclip | 星星髮夾 | side_l | 4674 | 1055/1055 | 金星＋藍夾；細尺寸手繪模板 |
| sakura | 櫻花髮飾 | side_l | 4674 | 1055/1055 | 5 瓣（細尺寸 4 瓣模板）＋金花芯 |
| glasses | 圓框眼鏡 | face | 4353 | 979/1055 | 跟眼距／傾角；L 級框粗 2；¾ 框；dot 半框；faceVisible=false 收起 |

### face／side_l 規則（ACC3 起）
- `head_l`：head_r 以兩眼中垂線鏡像；側面眼距太近用 fit 中軸。
- 眼鏡 `glasses_pre`＋`GL_RETRY`：clip 級鏡片大細，候選逐級試；`draw_glasses` 任何框像素落喺眼 blob 就當失敗。
- 已知（留 ACC5）：背面 side_l／side_r 唔對調（同 ACC1 蝴蝶結一樣）；月眠／菇傘帽針（head_l 鏡像）同 side_l 撞位要喺多 slot 衝突處理；evo_dot 用半框。
<!-- ACC3-END -->

<!-- ACC4-START -->
## ACC4 數量（2026-11-01）
| item | 名 | slot | 幀 | clip（可見／總） | 備註 |
|---|---|---|---|---|---|
| leafcollar | 葉仔領 | neck | 4674 | 1055/1055 | 尖頭葉兩色交替＋前右細花 |
| bell | 燈泡小鈴 | bulb | 4674 | 1055/1055 | suzu 模板 5／7／9；有擺動 |
| halo | 燈泡光環 | bulb | 4674 | 1055/1055 | 燈泡上面；非頭頂燈形態放頭頂；環洞透明 |
| nightcap | 睡帽 | head | 4524 | 1030/1055 | 長尾＋波波有擺動；shroom／moon 用 hatpin；sleepKeep |

### bulb slot 規則（ACC4 起）
- 燈泡玻璃半徑用 `BR` 表。`top_bulb(form)` 判斷燈泡係咪喺頭頂：lumi 系、dust、moon 唔係。
- 冇燈泡嘅形態（evo_dot／evo_sprout）：鈴吊頭頂芽右邊，光環放頭頂。
- 擺動 `_swing`：阻尼彈簧，夾 ±lim，每幀 ≤14°，loop clip 跑兩轉。
- 已知（留 ACC5）：
  - 睡帽／其他帽同 bulb slot（光環／鈴）同時戴嘅衝突。
  - moon 嘅 hatpin 睡帽細，似羽毛。
  - dust 個鈴吊喺尾燈下面，近地面。
<!-- ACC4-END -->

<!-- ACC5-START -->
## ACC5 定稿（2026-11-01）
### 可見度總覆核
| item | 名 | slot | clip 可見／總 | % | 全 clip 形態 |
|---|---|---|---|---|---|
| straw | 草帽 | head | 1030/1055 | 97.6% | 0/25 |
| bow | 蝴蝶結 | side_r | 1055/1055 | 100.0% | 25/25 |
| scarf | 頸巾 | neck | 1055/1055 | 100.0% | 25/25 |
| beanie | 毛冷帽 | head | 1030/1055 | 97.6% | 0/25 |
| acorn | 橡果帽 | head | 1030/1055 | 97.6% | 0/25 |
| crown | 小皇冠 | head | 1030/1055 | 97.6% | 0/25 |
| starclip | 星星髮夾 | side_l | 1055/1055 | 100.0% | 25/25 |
| sakura | 櫻花髮飾 | side_l | 1055/1055 | 100.0% | 25/25 |
| glasses | 圓框眼鏡 | face | 990/1055 | 93.8% | 1/25 |
| leafcollar | 葉仔領 | neck | 1055/1055 | 100.0% | 25/25 |
| bell | 燈泡小鈴 | bulb | 1055/1055 | 100.0% | 25/25 |
| halo | 燈泡光環 | bulb | 1055/1055 | 100.0% | 25/25 |
| nightcap | 睡帽 | head | 1030/1055 | 97.6% | 0/25 |

收起原因：撐葉傘：葉蓋住頭頂，頭飾收起 ×125、鏡框會壓到眼 ×36、faceVisible=false ×24、會遮五官 ×3、眼距 ×2。

### 同時戴（`COMBOS.json`）
- 每 slot 最多 1 件，最多 5 件；同 slot 換件。
- 讓位次序：halo > bell > starclip > sakura > bow > leafcollar > scarf > glasses > straw > beanie > acorn > crown > nightcap。
- 引擎查表：
  1. 戴住嘅每對 (a,b) 查 `forms[form]["a+b"][clip]`（冇就試 "b+a"）→ `{yield, off:[dx,dy]}` 或者 `{yield, hide:true}`。
  2. 每件讓位件取最大位移（|dx|+|dy|）；任何 hide 贏。
  3. 再查 `outfitOverrides[form][排好序用 + 連嘅組合][clip]`，列明嘅件收起。
  4. 位移係成段 clip 用（唔會逐幀跳）。
- 統計：344 對有規則；4,473 clip 位移、426 clip 收起；override 279。

### emissive
- 飾品畫喺 emissive 之前；emissive 用飾品 alpha 聯集遮走，燈泡 ±1 一直挖空。
- 平均遮咗：sakura 12.7%、nightcap 10.0%、beanie 9.0%、starclip 8.0%、acorn 7.4%、straw 7.2%、bow 5.8%、leafcollar 4.5%、scarf 4.5%、bell 3.7%、crown 3.3%、halo 2.0%、glasses 0.7%（`ACCESSORIES.json` → `emissive.overlap`，逐 item × form）。

### 其他 ACC5 改動
- 背面（turn_back_01）左右 slot 鏡像；moon 帽針睡帽 pincap；dust 鈴吊頭頂（top_low）；dot 眼鏡推上額頭。
- 預覽：`preview/accessories/acc5_contact_25x13_idle_2x.png`、`acc5_contact_25x13_walk03_2x.png`、`acc5_outfits_idle_3x.png` 等。
<!-- ACC5-END -->
