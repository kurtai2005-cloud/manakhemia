# 《微光小圃》HD-2D 場景 H1–H4 — 引擎格式（canvas2D 版）

> 遊美出，對應遊程 canvas2D 引擎（冇 shader）。全部 Python（Pillow／numpy）程式逐像素繪製，無 AI，全原創。
> 腳本：`art-pet/tools/build_hd2d_scenes.py`（可重跑）、驗證：`art-pet/tools/validate_hd2d_scenes.py`。

## 0. 座標同尺寸
| 項 | 值 |
|---|---|
| 美術格（螢幕） | **195×422**（顯示 ×2＝390×844，整數倍、Nearest） |
| 層畫布 | **223×446**＝美術格＋邊距 `MX=14, MY=12`（俾視差位移）；層座標＝art＋(14,12) |
| 團絨腳底 | art **(97,292)**（層 (111,304)）；pivot＝(w/2, h−3)；sprout 32px、radiant／soft 64px（1x，唔放大） |
| 活動範圍 | x＝97±62（art 35–159）；地面線 y＝292（`layout.json` → `pet`、`ground`） |
| UI 安全區 | 頂 HUD art y 0–62、底按鈕 y 378–422、彈出面板 y 330–378（只放天空／葉／草） |

`lightmap / light_add / emissive / emissive_blur` 全部 223×446，**同 mid 層一齊位移**（光源都屬 mid；太陽／月喺 sky，視差差 ≤ 幾 px，可接受）。`vignette.png` 係 195×422 螢幕固定。

## 1. 每款檔案（`H1/ H2/ H3/ H4/`）
| 檔 | 格式 | 用途 |
|---|---|---|
| `sky.png` `far.png` `mid.png` `fore.png` | 223×446 RGBA | **已預烘 LUT＋飽和＋對比＋DoF**；sky 全不透明，其餘透明 PNG（模糊後 alpha 有中間值） |
| `raw/{sky,far,mid,fore}.png` | 223×446 RGBA，alpha 0/255 | 預烘前色盤鎖定版（四層合共 ≤64 色），用嚟驗色／重新出圖，引擎唔使用 |
| `palette.json` | index→hex | 呢款色盤（同 `../index/materials.json` 對應） |
| `lightmap.png` | 223×446 RGB | **multiply**；白＝不變。陰影、樹蔭斑駁、AO、夜晚光池 |
| `light_add.png` | 223×446 RGB（黑底） | **lighter（additive）**；光柱、光池、夕陽光暈 |
| `emissive.png` | 223×446 RGBA alpha 0/255 | 發光像素位置（燈、窗、燈籠、日月星）；俾引擎做動態閃爍／遮罩用 |
| `emissive_blur.png` | 223×446 RGB（黑底） | emissive 已模糊＝**預烘 bloom**；lighter 疊，`globalAlpha = bloom.intensity` |
| `vignette.png` | 195×422 RGBA | normal（source-over）疊喺最頂 |
| `lut.png` | 256×16 RGB | 16³ LUT strip（見 §4），**淨係對色用**；已預烘入場景層 |
| `grade.json` | JSON | 見 §3 |
| `mockup_{sprout,radiant,soft}.png`＋`_2x.png` | 195×422／390×844 | 按本格式合成嘅效果圖（idle_01，視差 0），俾遊程對色 |
| H3 額外：`grade_rain.json`、`rain/{sky,far,mid,fore}.png`、`rain/lut_rain.png` | | 落雨中用嘅預烘層（降飽和＋雨 tint），切換時 crossfade |

共用：`layout.json`、`index/*_index.png`（L 模式索引圖；0＝透明）＋`index/materials.json`、`particles/`、`rain/`、`crossfade/`。

## 2. 疊層次序同公式（每幀）
```
ctx.globalCompositeOperation = 'source-over'
draw sky   @ offs.sky
draw far   @ offs.far
draw mid   @ offs.mid
draw pet   （見下：petTint × ambientTint ＋ rim）＋ 引擎動態物件／粒子
draw fore  @ offs.fore
'multiply' : draw lightmap      @ offs.mid           // C = C × LM
'lighter'  : draw light_add     @ offs.mid           // C = C + LA
'lighter'  : globalAlpha = bloom.intensity; draw emissive_blur @ offs.mid   // C = C + EB × bloom.intensity
              （＋ 寵物燈泡 glow：引擎 radial sprite，顏色 bulbGlowTint）
'source-over': fillStyle = fog.color, globalAlpha = fog.density, fillRect(全屏)   // C = C×(1−d) + fog×d
'source-over': draw vignette.png（螢幕固定）                                         // C = C×(1−a) + V×a
```
- **寵物唔過 LUT**：`pet = sprite × petTint × ambientTint`（canvas：sprite → multiply petTint → multiply ambientTint → destination-in sprite alpha），再加 rim（§5）。之後同場景一齊食 lightmap／light_add。
- `ambientTint` 已經烘入 LUT（場景層），引擎淨係再用喺寵物同動態 sprite（粒子、道具、便便等），令佢哋同場景同色溫。
- 視差 `layout.json → parallaxSuggest`：sky 0.15、far 0.35、mid 1.0、fore 1.6（建議值，遊程可改；最大位移唔好超過邊距 14／12px）。
- 時段切換 crossfade：同時畫舊款／新款兩套結果用 alpha 混（或者每層各自 alpha 混），建議 2–4 秒；`crossfade/` 有預覽。
- 落雨（只 H3）：sky/far/mid/fore 換 `H3/rain/*`，grade 換 `grade_rain.json`，再加雨層（§7）。

## 3. grade.json 欄位
| 欄位 | 類型 | 範圍 | 說明 |
|---|---|---|---|
| `variant` `name` `hours` | string | — | 識別用（可選） |
| `ambientTint` | "#rrggbb" | — | 環境色；已烘入 LUT；引擎用喺寵物／動態 sprite（multiply） |
| `petTint` | "#rrggbb" | — | 寵物專用額外 multiply（H3 用嚟壓暗團絨提對比） |
| `saturation` | number | 0–2 | 已烘入 LUT（1＝不變） |
| `contrast` | number | 0.5–1.5 | 已烘入 LUT（以 0.5 灰為中心） |
| `bloom.threshold` | number | 0–1 | 出 emissive_blur 時嘅門檻（記錄） |
| `bloom.intensity` | number | 0–2 | 疊 emissive_blur 嘅 globalAlpha（>1 時畫兩次或 clamp 1） |
| `fog.color` | "#rrggbb" | — | 單色霧 |
| `fog.density` | number | 0–0.3 | 霧 alpha |
| `dof.far` `dof.mid` `dof.fore` | number | 0–8 | 高斯 σ（art px）；**只係記錄，已預烘**。mid 係移軸式：地面帶（art y 262–340）0，向上／向下漸增到 `dof.mid` |
| `vignette` | number | 0–1 | 強度（記錄；vignette.png 已按此出） |
| `rim.color` | "#rrggbb" | — | 輪廓光色 |
| `rim.intensity` | number | 0–1 | 輪廓光 alpha |
| `rim.dir` | [x, y] | 單位向量 | 光**嚟自**嘅方向（螢幕座標，y 向下）；例 [-0.7,-0.7]＝左上 |
| `bulbGlowTint` | "#rrggbb" | — | 團絨頭頂燈泡 glow 顏色（亮度仍由心情參數驅動） |
| `particles.type` | string | mote／gold／petal／firefly | 對應 `particles/particles.json` |
| `particles.rate` | number | 0–10 | 每秒生成數（建議壽命 5–8 秒） |
| `particles.color` | "#rrggbb" | — | 粒子 tint（粒子圖已有色，可用 multiply 微調） |
| `rain.saturation` `rain.contrast` | number | 0–2／0.5–1.5 | 落雨時相對倍數（H3 已預烘成 rain/ 層；其他款備用） |
| `rain.tint` | "#rrggbb" | — | 落雨時額外 multiply |
`grade_rain.json` 同一 schema（另加 `baseVariant`、`note`），數值＝已套用落雨後嘅最終值。

## 4. LUT（lut.png）
- 256×16 RGB，16 格 × 16×16：**x = b×16 + r，y = g**（r,g,b ∈ 0..15，對應 0–1 線性步長 1/15），三線性插值。
- 內容＝`grade(rgb)`：`c = rgb × ambientTint → c = (c−0.5)×contrast+0.5 → lum = dot(c,(0.2126,0.7152,0.0722)) → c = lum+(c−lum)×saturation → clamp`。
- 場景層＝LUT(raw) 之後再做 DoF；validator 會驗 `sky.png ≈ LUT(raw/sky.png)`（Δ ≤ 2/255）。

## 5. rim mask（`art-pet/sprites/tuanrong/rim/`）
- `rim_<form>.png`＋`rim_<form>.json`：同 `motion/atlas_<form>.png` **同尺寸、同 rect、同幀名**（直接用 atlas 嘅 frame rect 取 rim）。單幀：`rim/<form>/<frame>.png`。
- 像素：sprite 1px **內緣** alpha 255；RGB 編碼外向法線 `R = (nx×0.5+0.5)×255, G = (ny×0.5+0.5)×255, B = 255`。
- 簡單用法：rim 色 fill → destination-in rim mask → globalAlpha＝`rim.intensity` 疊上寵物（全邊一圈）。
- 方向用法（建議）：載入時每款 grade 預計一次 `w = max(0, nx×dir.x + ny×dir.y)`，生成「方向 rim」canvas cache；scaleX −1 時用 `dir.x` 取反。
- 重跑：`python3 tools/build_tuanrong_rim.py [extra_atlas.json ...]`（新 clip／liveliness atlas 出咗之後加參數就得）。

## 6. 粒子（`particles/`）
`particles.png`＋`particles.json`（TexturePacker hash 格式），8×8，每款 6 幀：`mote_01..06`（H1 光塵）、`gold_01..06`（H2 金塵）、`petal_01..06`（H3 花瓣）、`firefly_01..06`（H4 螢火）。alpha 0/255。建議 fps 6–8、慢速飄（H1 上升 2–4 px/s、H3 斜落 8–12 px/s＋左右擺、H4 隨機漂＋明暗呼吸）。螢火／光塵可另加 lighter glow。

## 7. 雨層（`rain/`，H3 落雨中）
- `rain_tile.png`：64×64 可平鋪雨絲 × 4 幀（橫排，json 有 rect）；每幀向下移 16px 循環＝無縫；建議 fps 12，globalAlpha 0.5–0.7，畫喺 emissive_blur 之後、fog 之前（唔食 lightmap，雨絲喺陰影位都睇得見）。
- `ripple.png`：16×8 水氹漣漪 × 4 幀；隨機落喺 `layout.json → ground.walkable` 範圍。
- `H3/grade_rain.json`＋`H3/rain/*.png`：預烘落雨版場景層。

<!-- SYS12-START -->
## SYS12. 天氣（陰／霧）＋季節（systems12 第 1 批）
- 天氣權重：晴 60／陰 20／雨 15／霧 5（雨＝§7 `rain/`，唔變）。只 H3 戶外有天氣層。
- 陰：`H3/grade_overcast.json`＋`H3/overcast/{sky,far,mid,fore}.png`（已預烘 `lut_overcast.png`）＋ `weather/overcast_clouds.png`：陰天：疊喺 sky 之上、far 之下（parallax 同 sky 0.15）；art y −6 起（層座標 y 6）；橫向慢飄 2 px/s 循環；globalAlpha 0.85；唔食 lightmap
- 霧：`H3/grade_fog.json`＋`H3/fog/{sky,far,mid,fore}.png`（遠景預烘淡出）＋ `weather/fog_bank.png`（far／near 兩帶）：霧天：far 帶畫喺 far 之後（art y 200–272，0.35 parallax，飄 3 px/s，globalAlpha 0.7）；near 帶畫喺 fore 之前（art y 300–372，飄 6 px/s 反方向，globalAlpha 0.45）；Bayer 抖色 alpha 0/255
- 季節（香港月份：春 3–5／夏 6–8／秋 9–11／冬 12–2）：`seasons/<season>/<H#>/{sky,far,mid,fore,lightmap}.png`＋`lut.png`（256×16）＋`grade.json`（同 §5 schema）。晴天先用季節層；雨／陰／霧時用 H3/<weather>/*。換季 3s crossfade。
- 團絨：落雨 → `leaf_umbrella`；霧／冬 → `shiver` 抽中率加大（CLIPS.json `systems12B1`）。
- 季節 v2（Kurt 02:12「4季唔夠明顯分別」）：每季每時段有自己場景內容，預烘層照舊（code 唔使改）。`seasons/<season>/<H#>/raw/{sky,far,mid,fore}.png`＝季節版未烘層（alpha 0/255），`palette.json`＝佢哋用色；預烘層＝`bake(raw, grade, lut)`。春：櫻花樹冠＋粉色遠樹＋地面花瓣；夏：深綠＋積雲＋向日葵＋蟬；秋：紅／橙／金樹冠＋落葉堆＋南瓜＋金草；冬：禿枝積雪＋雪地＋屋頂／欄杆積雪＋冰柱＋聖誕花。
- 季節粒子疊層：`seasons/<season>/particles/sheet.png`（8px 格，v3 色盤，alpha 0/255）＋`particles.json`（frames／anims／types[emitter：spawn、ratePerSec、max、vx/vy、sway、lifeSec、perVariant H1–H4 倍率]）。春 petal、夏 firefly＋sunmote、秋 leaf、冬 snow。畫喺 fore 之上、UI 之下，唔乘 lightmap（H4 乘 0.75）。`seasons.json` v2 每季有 `particleOverlay`。
<!-- SYS12-END -->
