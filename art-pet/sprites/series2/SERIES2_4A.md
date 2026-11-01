# series2「細佬」batch 4a 美術（畀遊程）

規格：`docs-gdd/series2-4a4b-spec.md` §4a，加埋 `series2-egg-v1.md` v1.6 同 `batch3-fun-spec.md`。全部用 Pillow/numpy 程序生成，冇用 AI 生圖。
像素規格跟 tuned_48：48×48，pivot (24,45)，腳喺 y=46（B 系跟 B1，腳喺 y=45），alpha 只有 0/255，新 sprite 每幀 ≤12 色。Glow 由引擎畫。

## 重跑（`cd art-pet`）
```
python3 tools/build_series2_4a.py     # 形態、蛋、34 階段 5 動作 strip（約 5s）
python3 tools/build_series2_4a_b.py   # 道具、新 FX、教錯課 8＋照抄 8、細佬表情 patch
python3 tools/build_series2_4a_c.py   # 道具 icon 8＋夢泡泡 8（B2 貼紙，3x）
python3 tools/build_series2_4a_d.py   # 雙人 clip 6（含孵化第一眼）＋升級 3
python3 tools/build_series2_4a_e.py   # 4x 陣容圖＋動作 GIF
python3 tools/validate_series2_4a.py  # 應該出 PASS 0 error
```
輔助檔：`tools/series2_lib.py`、`tools/series2_forms.py`、`tools/series2_props.py`。重用咗 3a 嘅 `reactions_lib.py`（rig、表情、FX、clip schema）同 `ui_v2_kit.py`。

## 1. 新形態 10 個＋蛋
| 階段 | key | 檔案 |
|---|---|---|
| 蛋 | – | `egg/egg_48.png`、`egg/egg_crack.png`（4 幀：0 冇裂 → 3 大裂） |
| S1 蛋殼仔 | S1 | `forms/sprites/S1_48.png`，頭頂戴半個殼、下面仲坐喺殼入面 |
| S2 BB | S2 | 圓碌碌，頭頂有粒細光 |
| S4 少年 | S4A–S4H | 由該系 1 階加高 3px，加頸巾同系特徵（A 尾鰭、C 火角、D 金刺、E 火尾、F/G 耳仔） |

- `forms/tuned.json` 同 tuned_48 格式一樣，rig 讀得到，另外加咗 stage、mass、colors 欄位。
- idle 用 `forms/idle/<K>_idle.png`（4 幀，[260,180,260,140]ms）。
- S3／S5／S6 直接用返 from_ref 1／2／3 階（A1…H3）。

## 2. 5 動作：34 個階段都有
我揀咗一律烘焙成 strip。S1、S2、S4×8，加 24 個現有形態，每個都有 `actions/<K>_{idle,walk,cry,eat,sleep}.png`，引擎直接播。
- 定義喺 `actions/actions.json`，用 3a 嘅 body/face/fx schema。
- walk：6×100ms，向右（向左就 flipX）。
- cry：6×150ms，有眼淚 `fx2_tear`。
- eat：6×120ms。食物 icon 由引擎喺 chest 前面畫。
- sleep：4×450ms。Zzz 由引擎疊 3a 嘅 `fx_zzz`（headTop，dx 6）。
- 現有 24 個 from_ref 本身已經 >12 色，所以呢批冇壓色，調色板同 idle 一樣，只係多咗表情／眼淚色（validator 限 ≤6 隻新色）。

## 3. 教錯課（§4）
所有嘢喺 `lessons/lessons.json`。
- **道具（每系一件）**：A 水壺、B 泡泡棒、C 火柴、D 石仔、E 辣椒、F 望遠鏡、G 書、H 月亮燈。
  - 疊層喺 `lessons/props/prop_*.png`（有 pivot，部分 2–3 幀）。
  - fx id 係 `prop_<kind>`。
- **新 FX**：`lessons/fx/` 入面有 fx2_drops、splash、bubble（細→中→大→爆）、fire、steam、tiny、tear。
- **團絨示範（`demo`，3000ms）**：任何 `evo_still_*` 都用得，因為錨點由 rig 計。團絨只用 3a 現有表情。

  | 系 | 做錯咗乜 |
  |---|---|
  | A | 水壺淋自己個頭 |
  | B | 自己入咗泡泡，浮起再跌 |
  | C | 用個頭擦火柴，冒煙 |
  | D | 坐喺石仔上面孵 |
  | E | 當士多啤梨咁食辣椒，噴火 |
  | F | 望遠鏡拎倒轉，撞嘢暈 |
  | G | 本書拎倒轉讀，讀到瞓著 |
  | H | 月亮燈當帽戴，跌落遮住眼 |

- **細佬照抄（`copy`，2000ms）**：同一套錯嘢壓到 2/3 時長。smug 換成 happy，embarrassed 換成 pout。
- **細佬表情 patch**：`faces/<K>_faces.png`，排法見 `faces/faces.json`（13 個 3a 表情＋cry_a、cry_b、chew_o、chew_c、happy、pout）。

## 4. UI（B2 繪本貼紙，3x）
- `ui/prop_icons/icon_prop_<系>_<kind>@3x.png`，8 個，每個 90px。
- `ui/dream_bubbles/dream_<系>_<kind>@3x.png`，8 個，每個 132px。夢泡泡入面係當日最多嘅照顧類型（對應同一系嘅道具）。
- 索引：`ui/ui_series2_4a.json`。

## 5. 雙人 clip（`duo/duo.json`）
座標全部相對場景 pivot (97,292)。actor 嘅 dx/dy 加 track 嘅 x/y 就係寵物 pivot 位置。團絨用 evo_still 現有 clip 名，細佬用 actions strip，疊層喺 `duo/overlays/`。

| clip | 時長 | 內容 |
|---|---|---|
| cuddle_egg 攬蛋瞓 | 2000ms loop | 團絨 sleep_loop，蛋輕輕郁，有 dream_slot |
| hatch_first_glance 孵化第一眼 | 2000ms，可跳 | 全畫面 195×422，2x。蛋裂、光、殼飛，S1 眨眼，團絨由左邊探頭，有心心。分層同時間線寫喺 JSON |
| follow_walk 跟住行 | 3000ms | 細佬跟喺後面 30px，遲 300ms 起步 |
| comfort_cry 哄喊 | 3600ms | 細佬喊，團絨 nuzzle，細佬收聲，出心心 |
| eat_together 一齊食 | 1500ms loop | 兩隻一齊食 |
| sleep_together 一齊瞓 | 1800ms loop | 兩隻瞓，蓋住被 `ov_blanket`，有雙 Zzz |

## 6. 升級小場面（`levelup/levelup.json`）
- 跟班 4s、朋友 5s、家人 6s。
- 每個都有徽章 `badge_*`、空白絲帶 `ov_ribbon`（字由引擎寫 `ribbonText`）、彩紙 `ov_confetti`，朋友嗰段仲有大心心。

## 預覽（`preview/`）
- 陣容：`lineup_4x.png`（蛋→S6，每系一行）
- UI：`ui_props_dreams.png`
- 細佬動作：`actions_new_1.gif`、`actions_new_2.gif`、`actions_existing_sample.gif`
- 教錯課：`lesson_A…H.gif`（團絨教，跟住細佬抄）
- 雙人 clip：`duo_*.gif`
- 升級：`levelup_*.gif`
- 教錯課 contact sheet：`lessons/_preview/demo_*_contact.png`

## 已知問題
- S4H 漸層較平，偏淡紫；S4F 頭頂星仔支柄長咗少少。
- 現有 24 形態嘅 walk/cry/eat/sleep 係通用變形加表情，唔係逐隻手繪，所以動作幅度一樣。
- 團絨示範用 rot 嘅段落（D）有少少鋸齒，已經用 rotStep 3° 減輕。
- 細佬抄錯時道具尺寸同團絨一樣，所以細佬拎住會顯得大少少（算係刻意）。
- GIF 預覽冇壓色，因為道具係疊層，唔計入 sprite 嘅 12 色。
