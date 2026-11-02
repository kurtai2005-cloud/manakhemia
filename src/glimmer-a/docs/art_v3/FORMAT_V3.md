# 花園 H1–H4 · V3-A 光影（第 2 批）

底：`scenes/hd2d`（= art/glimmer-hd2d-live 嘅 HD-2D 場景層）。生成：`python3 art-pet/tools/build_garden_hd2d_v3.py [fx H1 H2 H3 H4 preview]`；驗證：`python3 art-pet/tools/validate_garden_hd2d_v3.py` → `validation.json`。全部 Pillow/numpy 程式繪製，無 AI 圖。

## 時段（日／夜）
| 變體 | 時段 | 光 |
|---|---|---|
| H1 晨光暖調 | 06–10 | 低角度暖陽體積光、葉隙光斑、地平線暖霧、塵埃 |
| H3 清新冷調 | 10–16 | 頂光冷調體積光（弱）、葉隙光斑、花粉 |
| H2 黃昏電影感 | 16–19 | 夕陽星芒放射光、燈泡串初亮、bloom 強；寵物光池 1.0（第 3 批加強，postLightmap .5）|
| H4 夜燈 | 19–06 | 燈泡串＋街燈＋窗光＋螢火瓶，光池、螢火、星空大星 |

H3 天氣（rain/overcast/fog）第 3 批已轉 V3（見下面 §天氣）；四季仍用 `scenes/hd2d/seasons`，第 4 批轉。

## 兼容
* 1x 層名／尺寸同 v2 一樣：`sky far mid fore lightmap light_add emissive emissive_blur`（223×446）、`vignette`（195×422）、`lut.png`（256×16）、`palette.json`、`grade.json`（v2 所有 key 保留）。舊 runtime 直接換目錄就用得。
* pivot 同 v2：sprite pivot (w/2, h−3)；團絨腳底 art (97,292)＝1x 層 (111,304)＝@3x 層 (333,912)。clearBox [30,210,165,300] 冇加新雜物（驗證 ≤8% 像素變動，只係草紋／光）。
* `raw/`：未調色 sprite 層（alpha 0/255）＋ `*_index.png`（材質索引）。v3 新增 11 個材質（index 65–75：FLOWER_B/W、BULB、JAR×2、IVY×2、BIRD、BERRY、CLOVER×2），raw 顏色 ≈72–73（v2 上限 64 → v3 上限 96）。

## @3x 烘焙層（`x3/`，669×1338，vignette 585×1266 = 螢幕）
| 層 | blend | 內容 |
|---|---|---|
| sky / far / mid / fore @3x | source-over | 1x×3 nearest 再烘 DoF（far 柔、mid 移軸：art y 262–340 清、fore 前景虛）|
| haze_far | source-over | 地平線高度霧 |
| mist | source-over | 地面薄霧，可橫向慢飄 2px@3x/s |
| lightmap | multiply | 環境光＋燈池＋葉隙光斑 |
| light_add | lighter | 體積光（god rays）＋暖光池 |
| emissive | lighter | 燈泡／窗／螢火瓶 |
| bloom | lighter | emissive＋高光 閾值 bloom（已模糊，× grade.v3.bloom3x.intensity）|
| vignette | multiply | 暗角（螢幕座標）|

## 即時層（唔烘，runtime 做）
* **pet**：sprite × petTint × ambientTint ＋ rim ＋ contact shadow。
* **petLight**：`fx/fx_glow_v3@3x.json#pet_pool`（240×96 @3x），anchor 腳底，`offset3x [0,6]`，blend lighter，intensity H1 .35／H3 .2／H2 1.0（第 3 批由 .55 加強，另加 postLightmap .5＋bounce）／H4 .9，**× petGlow**。
* **flares**：`grade.v3.flares[]` — 燈泡串／燈籠／街燈／螢火瓶／太陽星芒，`flare_{s21,m39,l63}_01..06` 6 幀閃爍，fps／phase 逐粒錯開。
* **particles**：`grade.v3.emitters[]` — dust／pollen／petal／firefly；核心像素用 `fx/particles_v3@3x.png`（alpha 0/255），柔光用 `glow_*`／`bokeh_*`（true alpha，lighter）。
* **emissive flicker**：H2/H4 對 emissive 做 ±6% 慢呼吸（可選）。
* **fog**：沿用 v2 `fog`。

疊層次序寫咗喺 `grade.json → v3.stack`（每項標 `baked` 或 `realtime`）：sky → far → haze_far → mid → mist → **pet**(+petLight) → fore → lightmap → light_add → emissive → bloom → flares → particles → fog → vignette → UI。

## 寵物光規則（Kurt：「除左佢訓就會關」）
跟 `ui/kit_hd2d_v3/layout_hd2d_v3.json → petGlow`：awake 1、sleepy .6、sleep／sleepClip／dreamEnter／dreaming = 0；熄 600ms easeInQuad，醒返 400ms easeOutQuad ＋ 150ms pulse 1→1.15→1。**場景燈唔受影響。**

## 第 3 批（已拆）
寵物光源 v3：逐個有光源／特效嘅形態，逐幀 anchor 嘅 @3x 光暈／光點 ＋ 場景光池，全部 × petGlow。今批只交通用 `petLight` 光池 hook。

## 預覽
`preview/compare_H*.png`（前 v2 ×3｜後 v3｜後＋UI v3）、`preview/H*_v3_3x.png`、`preview/H*_v3_ui_3x.png`、`preview/overview.png`、`preview/detail_ground_zoom.png`。預覽入面嘅寵物（團絨 evo_still_tide＋蝴蝶結、細佬）只係示意，唔係資產。

## 天氣（H3，V3，第 3 批）
`H3/grade_{rain,overcast,fog}.json`（v2 欄位＋`v3` block，`stack` 路徑相對 `H3/`；`scenes/hd2d/…` 開頭＝沿用 v2 共用素材）＋ `H3/<wx>/{sky,far,mid,fore}.png`（1x 相容）＋ `lut_<wx>.png` ＋ `H3/<wx>/x3/{sky,far,mid,fore,lightmap,light_add,bloom,haze_far,mist,vignette}@3x.png`。
* 雨：降飽和＋藍灰 tint，lightmap ×.85、體積光 ×.25；雨絲 `scenes/hd2d/rain/rain_tile.png` ×3 平鋪＋ripple。
* 陰：天空灰白化，lightmap ×.75、體積光 ×.15；疊 v2 `weather/overcast_clouds.png` ×3。
* 霧：遠景淡出 50%、高度霧加厚，lightmap ×.5；疊 v2 `weather/fog_bank.png` 遠／近兩帶 ×3。
* 寵物光池：雨／陰 .3、霧 .35（仍 × petGlow）。
* 四季（16 款）**未轉**，下批（第 4 批）做。
預覽：`preview/H3_weather_v3.png`、`preview/H3_weather_compare.png`。
