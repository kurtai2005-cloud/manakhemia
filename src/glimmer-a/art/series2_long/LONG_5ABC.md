# 《微光小圃》5a–5c 長線養成美術（俾遊程）

來源：`docs-gdd/series2-4a4b-spec.md` v1.1 §5a–5c ＋ `series2-egg-v1.md` v1.4+。純 Pillow/numpy 程序生成，冇 AI 圖。
跟 4a（`sprites/series2/`）、4b（`sprites/series2_house/`，house.json 用遊策新版：葉仔床入屋預設、商店 7 件 165 碎）。
UI 一律 HD-2D（`ui/style_ref/hd2d`；`ui_hd2d_kit`／`ui_hd2d_icons` 只讀，新 icon 喺 `long_5abc_ui.py` 記憶體登記）。
像素規格：alpha 只有 0/255；新形態（S1/S2/S4*）每格 ≤12 色；光源左上、深色描邊。art 195×422，場景層 223×446。

驗證：`cd art-pet && python3 tools/validate_long_5abc.py`（冇參數＝有 json 嘅部份全驗；或 `5a` `5b` `5c`）

## 通用：strip 同 overlay 點對齊
* 所有 strip 都係 3a schema（body/face/fx）烘焙；每個 clip 嘅 canvas／pivot 用 `long_5abc_lib._geo(k, clip)`：
  * `idle/walk/cry/eat/sleep`（細佬 34）：48×48，pivot (24,45)，`series2/actions/`
  * `sit/prank_do/prank_got`（59）：`series2_house/actions/`（4b，冇重整）
  * `interact`（59，5a）／`depart/return`（成年 25，5b）：canvas＝base＋左右 6、頂 18 padding；pivot＝base pivot＋(6,18)
  * 團絨 idle/walk/sleep 係舊 frame-based 動畫（唔經 rig）→ overlay 只有 `base` 一行，引擎跟程序變形（已知限制）
* **overlay atlas**（工作帽、遺傳花紋）：每個形態一張 PNG，每行一個 clip、每格同對應 pet strip 一樣變形（同一條 nearest 變形公式），
  所以引擎：`畫 pet strip 第 i 格 → 喺同一個 pivot 畫 overlay 該行第 i 格`。行 meta（y、frames、frameW/H、pivot、petPng）喺 json。
  overlay 格可以比 pet 格大（帽要出頭頂）：用 overlay 自己嘅 pivot 對齊 pet pivot。

---
## 5a 家族同屋擴建 → `series2_long/5a/`
資料：`5a/long_5a.json`（養 2 隻、二揀一揀蛋、做主養、家族等級 Lv1–10 門檻／XP／解鎖、房間、interact clip）

**互動動作（屋內 2 個）**：坐（sit）同整蠱（prank）4b 已有，唔重整；新增 **interact 打招呼／貼貼** × 59 形態
* `5a/actions/<form>_interact.png`：8 格 × 120ms，唔 loop。0–1 望、2–3 傾身貼過去（向右；對方喺左就 flipX）、4 心心、5–6 彈、7 返原位
* 兩隻一齊：面對面（左正向、右 flipX），pivot 距離 `max(22, (兩隻 sit 第0格 bbox 闊)/2 − 4)`；同時播
* clip 數據喺 json `actions.interact.clipData`（runtime 亦可用 3a 引擎重現）
* 預覽：`5a/preview/interact_duo_room2.gif`、`interact_forms.gif`、`interact_all59_3x.png`

**擴房 3 間（直向）**：幾何同 4b 屋仔完全一樣 → house.json 嘅 grid／6 slot／walk／家具直接用；每間房 4 隻
| 房 | 解鎖 | 主題 | 牆紙 | 掛旗 |
|---|---|---|---|---|
| room2 森林閣樓 | Lv2 | 鼠尾草綠、深木 | 細葉 | 葉仔旗 |
| room3 星夜書房 | Lv5 | 薰衣草紫、梅紫牆裙 | 金十字星＋月亮貼紙 | 金星旗 |
| room4 海風小屋 | Lv8 | 水藍、白洗地板、窗外變海 | 細波浪 | 藍白旗 |
* `5a/rooms/<room>/{day,night}/`：sky/far/mid/fore（223×446）＋ lightmap/light_add/emissive/emissive_blur/vignette ＋ grade.json/palette.json ＋ raw/（未調色）— 同 4b room 一樣合成（`house_4b_room.compose`）
* 新房開咗係空房（冇送床）— 見 open question
* 預覽：`5a/preview/rooms_5a_3x.png`（4b 對照＋3 間日夜）、`roomN_empty_day_3x.png`

**UI（HD-2D，`5a/ui/*@3x.png`＋`5a/ui/layout.json`）**
* 屋內 HUD：左上返回、房名牌、右上 **家族 Lv chip**（icon＋Lv＋XP 細條；撳開族譜）、房名下 4 粒房間點、左上「n/4 隻」、左右切房箭嘴（下一間未開＝灰＋鎖）、左下「族譜」、右下「佈置」(4b)
* 寵物卡（撳屋內成年）：頭像、名、系列牌、「做主養」（已係主養＝灰「主養緊」＋金冠）、「打招呼」、「搬房」
* 家族升級彈窗：光芒＋大 medal＋「Lv N」＋解鎖卡（每級內容由 json 出）
* 揀蛋（二揀一）：團絨蛋／細佬蛋卡；有細佬養緊＝細佬蛋灰卡＋鎖＋「細佬養緊」
* 族譜：家族 Lv 卡（XP 條、下一級解鎖、XP 來源）＋每代 node（頭像、名、系列、遺傳花紋色塊、教錯咗乜道具＋一句）＋金連線；Lv10 金色版（金框、「微光之家」稱號）
* 預覽：`5a/preview/*_HD2D_3x.png`（585×1266）、`ui_5a_sheet_HD2D_3x.png`、`family_tree_sheet_HD2D_3x.png`、`ui_parts_5a_HD2D_3x.png`

重跑 5a：`cd art-pet/tools && python3 long_5a_build.py && python3 long_5a_ui.py && python3 long_5a_preview.py`

---
## 5b 遠足同工作 → `series2_long/5b/`
資料：`5b/long_5b.json`（每日規則、遠足、手信、工作、帽 atlas meta）。UI 預覽用 5a 嘅房，所以要先裝 5a。

**成年＝屋內可派嘅形態 25 隻**：團絨靜光 9 ＋ 細佬 S5/S6（A2–H2、A3–H3）16（GDD §3：S5＝現有第 2 階、S6＝第 3 階）

**出發／返屋 strip**（`5b/actions/<form>_{depart,return}.png`，10 格 × 120ms，canvas／pivot 同 interact）
* depart：背住細背囊（身後左邊、啡皮＋金扣＋葉仔吊飾＋1px 肩帶），0–2 揮手，3–9 行向門口。引擎：第 3 格後每格 x+2px（向右），7–9 格 alpha 1→0
* return：背囊脹晒（頂露樹枝＋星星）；0–3 由右邊行入（每格 x−2px），4 停，5–9 舉高手信
* **手信喺頭頂**：第 5–9 格，`headTop`（json `expedition.forms.<k>.headTop`，跟 strip 變形 dy）上 10px 畫手信 1x（pivot＝底中），bob 0/−1/0/1/0
* 預覽：`5b/preview/trip_A3_room2.gif`、`trip_evo_still_moon_room3.gif`、`trip_A3_{depart,return}_3x.png`、`trip_all_adults_3x.png`

**手信 10 款**（遠足 pool；`json.souvenirs`）
七彩貝殼／松果／星星石／藍羽毛／細蘑菇／紅楓葉／樽中信／雲朵糖／螢火燈／彩虹糖
* `5b/souvenir/<id>@3x.png`（HD icon）、`<id>_medal@3x.png`（金框 medal，toast／日記用）、`<id>_1x.png`（pixel 11–13px，≤12 色，頭頂／擺設用）
* 預覽：`5b/preview/souvenirs_sheet.png`

**工作 4 款 × 帽**（overlay atlas `5b/hats/<form>_hat_<job>.png`，每張 4 個 tier block × 每個 clip 一行）
| 工作 | 帽 | 
|---|---|
| post 郵差助手 | 藍圓帽＋右帽舌＋白帶＋信封章 |
| garden 園丁 | 草帽闊邊＋紅帶＋頂出芽仔 |
| watch 守夜 | 深藍睡帽歪右＋白毛邊＋尖端月亮＋星 |
| chef 廚師 | 白色三泡廚師帽 |
| tier | 等級 | 裝飾 |
|---|---|---|
| t1 | Lv1–2 | 原色 |
| t2 | Lv3–4 | 帽帶變金 |
| t3 | Lv5 | 金帶＋金星章 |
| t4 | Lv6（家族 Lv7 先開） | 金帶＋金星＋粉紅寶石 |
* 帽闊＝clip(headHW×1.3, 9, 19)；坐喺「第一行夠闊（≥45% 帽闊）」嘅頭頂，帽邊永遠喺眼上面 ≥3px；燈泡（protect）位挖空 → 燈泡永遠露出
* 行 meta：`jobs.forms.<k>.<job>.rows[]`＝{tier, clip, y, frames, frameW, frameH, pivot, petPng}；`pivot` 對齊 pet strip pivot 畫同一格
* 團絨靜光 idle 係 frame-based → 用 `base` 行（同 5a 一樣限制）
* 預覽：`5b/preview/job_hats_kid_3x.png`、`job_hats_tuanrong_3x.png`、`job_hats_on_pets.gif`

**UI（HD-2D，`5b/ui/*@3x.png`＋`5b/ui/layout.json` 座標）**
* 每日安排：遠足 n/2 chip、今日 n/12 碎 chip、每隻成年一行（portrait＋名＋遠足／工作／休息 segment＋狀態細字）；遠足中＝portrait 變暗＋背囊 icon；2/2 用晒＝遠足 segment 鎖
* 揀工作：2×2 卡（icon medal＋Lv 章＋名＋升級進度 bar＋每日產出）；Lv5 封頂＝金 bar＋「家族 Lv7 開 Lv6」
* 返屋 toast（上面滑落，手信 medal＋「滴滴返嚟喇！」＋碎 chip）；撳＝開團絨日記
* 團絨日記：一格故事（scene crop＋寵物返屋格）＋3 行字＋手信／碎／（30%）家具 chip＋左右翻頁
* 零件：`icon_job_*`、`icon_{expedition,rest,shards,job_lv}`、`badge_job_lv1–6`、`seg_{expedition,job,rest}_{on,off,locked}`、`job_card_*`、`toast_return`、`diary_page_example`
* 預覽：`5b/preview/ui_5b_sheet_HD2D_3x.png`、`daily_plan(_full)`、`job_picker`、`return_toast`、`diary_{pinecone,starstone}`（`_HD2D_3x.png`，585×1266）、`ui_parts_5b_HD2D_3x.png`


## 5c 傳承 → `series2_long/5c/`

**規則（`long_5c.json` › rules）**
* 新蛋孵之前揀屋內一隻成年（25 隻：團絨靜光 9＋細佬 S5/S6 16）做「上一代」
* 細佬繼承 1 款花紋（跟上一代系 `patternBySeries`／團絨路線 `patternByRoute`）＋1 招（上一代嗰課 lesson，`tricks` A–H）
* 團絨上一代：傳佢「示範」嗰課（runtime 記錄，json 係 null）
* 家族 Lv3 起：頭 2 階快 20%；團絨蛋唔計
* 族譜欄位：代／系／上一代／教錯咗乜（畫面喺 5a `family_tree_HD2D_3x.png`）

**花紋（8 款：wave bubble spark spot flame star diamond crescent）**
* `5c/patterns/{k}_pattern.png`：59 形態（KID34＋TR25），每張 8 pattern block × 全部 clip。灰階 mask（255＝hi、128＝lo）已經裁入 pet 不透明位，runtime 用上一代 `parents.<k>.tint` 染（`PT.colorize`：R≥190→hi，其他→lo）
* 行 meta：`overlay.forms.<k>.rows[]`＝{pattern, clip, y, frames, frameW, frameH, pivot, petPng}；pivot 同 pet strip 對齊畫同一格；`maskPx` 記每款嘅像素數
* 對比：上一代同細佬主色太近（ΔRGB<90）就 hi 推白、lo 變深（`tint.contrast`、`childDominant`）
* 蛋：`egg_tr`（6×32）、`egg_kid`（1×48）、`egg_kid_crack`（4×48）各 8 pattern 行 → 傳承喺新蛋已經睇到
* 團絨 frame-based clip 只有 `base` 行（同 5a／5b 一樣）
* 預覽：`5c/preview/inherit_eggs_3x.png`、`inherit_growth_line_3x.png`、`inherit_tuanrong_3x.png`、`inherit_all59_3x.png`、`inherit_forms.gif`

**UI（HD-2D，`5c/ui/*@3x.png`＋`5c/ui/layout.json`）**
* 揀上一代：2×3 成年卡（portrait＋名＋花紋 swatch＋招式 chip）＋底部「會遺傳」bar（花紋＋招式＋加速 pill：on／未到 Lv3 鎖／團絨蛋唔計）
* 遺傳咗！結果：新細佬（已染花紋）＋光線＋花紋／招式兩行＋加速 pill
* 零件：`parent_card_*`、`inherit_preview_bar`、`swatch_{pattern}_{parent}`、`chip_trick_A–H`、`icon_{inherit,pattern,trick,fast}`、`pill_fast_{on,locked,tr}`
* 預覽：`5c/preview/ui_5c_sheet_HD2D_3x.png`、`parent_pick(_tr_egg)`、`inherit_result_{S1,tr}`（`_HD2D_3x.png`，585×1266）、`ui_parts_5c_HD2D_3x.png`
