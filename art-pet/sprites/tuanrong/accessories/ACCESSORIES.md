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
