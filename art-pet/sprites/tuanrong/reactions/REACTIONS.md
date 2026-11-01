# 團絨 反應 batch 3a — 觸摸 ×5 ＋ 蠢萌 ×6（兩條寵物線）

純 Pillow／numpy 程序生成（冇用 AI 圖）。重跑：`python3 tools/build_reactions.py`（約 30s；會清空重建 `sprites/tuanrong/reactions/`）。
源碼：`tools/reactions_lib.py`（rig／面／FX／系列幀／穿戴／參考合成器）＋ `tools/build_reactions.py`（clip 定義＋輸出）。

## 兩條線點覆蓋

| 線 | 寵物 | base 幀 | 面／錨點來源 |
|---|---|---|---|
| 舊 團絨 evo（留喺遊戲） | 25 款可穿戴形態：sprout, radiant, soft, lumi, evo_dot, evo_sprout, evo_hop, evo_guard_tide, evo_guard_moon, evo_guard_shroom, evo_guard_crystal, evo_guard_ember, evo_guard_radiant, evo_guard_soft, evo_guard_dust, evo_guard_lumi, evo_still_tide, evo_still_moon, evo_still_shroom, evo_still_crystal, evo_still_ember, evo_still_radiant, evo_still_soft, evo_still_dust, evo_still_lumi | evo6 / attach `idle_01` | `accessories/attach/<form>.json`（face／eyes／head／side／bulbPt）＋ `layers/idle_01_noface/_faceov`（sprout/radiant/soft 冇 → 用 ATTACH 眼 blob 自動拆） |
| 新蛋線 | 24 隻 A1–H3 | `tuned_48/idle/{KEY}_idle.png` 幀 0（48×48，pivot 24,45） | `tuned_48/tuned.json`（eyes／mouth／bulbXY／outline） |

**全部 49 隻用同一套** clip（transform keyframe）＋ 通用 FX；每隻有自己嘅 面 patch、穿戴 patch（眼鏡／四方帽）、手仔，同埋按『系』嘅自訂幀（暈星 orbit、撞／落地 puff）。

### 系 → 自訂幀 token

| 系 id | token | 寵物 |
|---|---|---|
| `old_base` | leaf | sprout, evo_dot, evo_sprout, evo_hop |
| `old_radiant` | star | radiant, evo_guard_radiant, evo_still_radiant |
| `old_soft` | fluff | soft, evo_guard_soft, evo_still_soft |
| `old_lumi` | firefly | lumi, evo_guard_lumi, evo_still_lumi |
| `old_tide` | drop | evo_guard_tide, evo_still_tide |
| `old_moon` | crescent | evo_guard_moon, evo_still_moon |
| `old_shroom` | spore | evo_guard_shroom, evo_still_shroom |
| `old_crystal` | shard | evo_guard_crystal, evo_still_crystal |
| `old_ember` | ember | evo_guard_ember, evo_still_ember |
| `old_dust` | mote | evo_guard_dust, evo_still_dust |
| `new_A` | drop | A1, A2, A3 |
| `new_B` | bubble | B1, B2, B3 |
| `new_C` | ember | C1, C2, C3 |
| `new_D` | pebble | D1, D2, D3 |
| `new_E` | flame | E1, E2, E3 |
| `new_F` | star | F1, F2, F3 |
| `new_G` | star_blue | G1, G2, G3 |
| `new_H` | crescent | H1, H2, H3 |

## 檔案

```
sprites/tuanrong/reactions/
  reactions.json          ← 全部 clip（引擎讀呢個）＋觸發規則＋引擎模型
  anchors.json            ← 49 隻：pivot／錨點／headHW／面·穿戴·手仔檔路徑
  fx/*.png + fx.json      ← 通用 FX 橫條（每幀同大），pivot＝落點；fx_mirror_mask.png（玻璃 mask）
  series/<系>_orbit.png   ← 8 幀頭頂轉星（25×13，pivot 12,6）
  series/<系>_puff.png    ← 3 幀撞／落地煙＋系碎片（17×10，pivot 8,9）＋ series.json
  faces/<pet>_faces.png   ← 面 patch 橫條（每幀 = 全幀大細；次序見 anchors.json faces.order）
  wear/<pet>_glasses.png  ← 2 幀（0 普通、1 反光）全幀 patch
  wear/<pet>_hat.png      ← 2 幀（流蘇擺）全幀 patch；燈泡／莖位已挖空
  paws/<pet>_paw.png      ← 4 幀手仔（拳／1／2／3），身側皮膚色＋自己外框，pivot 左中
  preview/<clip>.gif      ← 4 隻並排：evo_hop、evo_still_ember（舊）｜A1、H3（新），H1 花園背景，3x，40ms
  reactions_sheet_4x.png  ← 4x 資產表（FX、各系幀、8 隻嘅面／穿戴／手仔）
  reactions_keyframes_2x.png ← 每 clip 6 個時間點（evo_still_ember＋H3）
  check/faces_all_2x.png  ← 49 隻 × 全部面，肉眼檢查
  check/validation.json   ← 驗證結果
```

## 引擎模型（遊程 接）

- **drawOrder**：["base = idle 幀 0（反應期間 idle 停）", "face patch（clip.face 軌，null = 原面）", "wear patch（glasses／hat，全幀，hat 已挖燈泡位）", "→ body transform（下）", "FX：z=back 喺寵物後、z=front 喺前；FX 本身唔縮放唔旋轉"]
- **transform**：keys {t, sx, sy, rot(度，順時針), x, y, flip(0/1), e}；缺欄沿用；段內 easing 用『下一格』嘅 e；origin = 錨點名（預設 pivot）；最近鄰取樣；rotStep 有就 snap 角度；groundLock = 每幀將最低實色行貼返 pivot.y（碌地用）
- **easing**：{"linear": "t", "in": "t²", "out": "1-(1-t)²", "inout": "2t² / 1-2(1-t)²", "outBack": "1+2.70158(t-1)³+1.70158(t-1)²", "step": "跳到下一格（到 t 先變）"}
- **fx**：{id, anchor, dx, dy, t0, t1, ms, loop(預設 true), frames(幀序列，選填), follow(預設 true：錨點跟 body 變形), atGround(y = pivot.y), mirrorX, z, move:[[ms,dx,dy]..] 線性}；id: fx_* = fx/fx.json；series_orbit / series_puff = series/<寵物系>.json；paw = paws/<pet>_paw.png
- **anchors**：anchors.json 每隻：pivot, face, eyeL, eyeR, mouth, headTop, bulb, side_l, side_r, center, chest（base 幀像素座標）；touch = 引擎傳入手指位置
- **events**：clip.events [{t, id}] — pat（摸頭計數）、line:*（對白，文字唔喺 art）

參考實作：`reactions_lib.Comp.render(clip, t)`（同 preview 一模一樣），可以照抄做 shader／canvas 版。

### 錨點（每隻見 anchors.json；座標 = base 幀像素）

| 錨點 | 意思 |
|---|---|
| pivot | 腳底（新 24,45；evo w/2,h-3；sprout 16,29；radiant/soft/lumi 32,61） |
| face / eyeL / eyeR / mouth | 面中、兩眼中心、嘴 |
| headTop | 頭殼頂（唔計燈泡／角／月／光環）— 四方帽、數字、轉星 |
| bulb | 燈泡（帽唔遮） |
| side_l / side_r | 身兩側（眼下 ~4px）— 笑紋、牆、鏡、黑板、手仔 |
| center | bbox 中心（碌地 origin） |
| chest | 嘴下（書） |
| touch | 引擎傳入手指位置 |

示範（新 A1／舊 evo_hop）：
- `A1`：{"bulb": [24.0, 9.0], "headTop": [24.0, 17.0], "face": [24.5, 35.5], "eyeL": [18.5, 35.5], "eyeR": [30.5, 35.5], "center": [23.5, 26.5], "chest": [24.5, 42.0], "side_r": [36.0, 40.0], "side_l": [11.0, 40.0], "pivot": [24.0, 45.0], "mouth": [23.5, 39.5]}，headHW 4
- `evo_hop`：{"headTop": [18.8, 13.6], "side_r": [31.0, 17.0], "side_l": [9.0, 17.0], "bulb": [20.0, 8.0], "face": [19.5, 24.0], "eyeL": [14.5, 24.0], "eyeR": [24.5, 24.0], "center": [17.0, 20.5], "chest": [19.5, 32.0], "pivot": [19.0, 35.0], "mouth": [20.0, 28.0]}，headHW 12
- `H3`：{"bulb": [25.0, 14.0], "headTop": [28.0, 16.0], "face": [27.5, 33.0], "eyeL": [22.0, 33.0], "eyeR": [33.0, 33.0], "center": [23.5, 28.0], "chest": [27.5, 40.5], "side_r": [36.0, 37.0], "side_l": [5.0, 37.0], "pivot": [24.0, 45.0], "mouth": [26.5, 36.5]}，headHW 14
- `evo_still_ember`：{"headTop": [22.3, 19.7], "side_r": [38.0, 24.0], "side_l": [12.0, 24.0], "bulb": [24.0, 16.0], "face": [24.5, 33.0], "eyeL": [18.5, 33.0], "eyeR": [30.5, 33.0], "center": [22.0, 24.0], "chest": [24.5, 41.0], "pivot": [24.0, 45.0], "mouth": [24.0, 37.0]}，headHW 16

## 觸發規則

**觸摸**

- poke：tap <250ms & <12px
- longPress：>=600ms → touch_pet_loop；3000ms = 1 次 pat event
- tickle：1000ms 內 >=4 次方向反轉（每段 >=8px）
- pull：拖 >40px → touch_pull_hold；放手 → touch_pull_release
- shake：1000ms 內 2 次 >2.5g → dizzy；cooldown 30000ms；60000ms 內第 3 次 → pretend
- asleep：任何手勢 → touch_sleep_rub
- duringDim：poke → touch_embarrassed（中斷 dim）

**蠢萌（dim）**：{"idleMinMs": 20000, "rollEveryMs": 60000, "chance": 0.25, "minGapMs": 180000, "maxPerDay": 8, "pick": "6 款平均隨機，唔重複上一次；瞓緊／被摸緊／UI 開住唔觸發；被戳 → touch_embarrassed 中斷"}
即：idle 滿 20s 之後，每 60s 擲一次 25%；兩次之間 ≥3 分鐘；每日最多 8 次。

## 面（face patch）

| 名 | 用途 |
|---|---|
| `blink` | 眨眼（戳） |
| `squint` | ^ ^ 舒服瞇眼（長按 loop） |
| `squint_blush` | 瞇眼＋腮紅加深（長按 loop 第 2 格） |
| `laugh_a` | > < 大笑張大口（搔癢） |
| `laugh_b` | > < 笑（細口） |
| `dizzy_a` | @ @ 暈（搖機） |
| `dizzy_b` | @ @ 暈第 2 格（轉 90°） |
| `sleepy` | 眼瞓半眼（睇書） |
| `sleep` | 瞓著 ︶ ︶ |
| `surprised` | 驚訝：眼上移＋o 口（拉開／照鏡） |
| `smug` | 扮醒：半眼＋得意嘴角 |
| `embarrassed` | 尷尬：眼望低＋斜線腮紅＋波浪口（呆反應做緊被戳） |
| `lookup` | 望上諗嘢（計數） |

## Clips

| clip | 組 | 長度 ms | loop | origin | 觸發 |
|---|---|---|---|---|---|
| `touch_poke` | touch | 500 |  | pivot | tap（按落→放 <250ms、移動 <12px）。瞓緊 → touch_sleep_rub；蠢萌反應進行中 → touch_embarrassed |
| `touch_pet_loop` | touch | 1200 | ✓ | pivot | 長按 ≥600ms 開始 loop；放手即停（回 idle 用 120ms ease-out）。連續按滿 3000ms → event pat（計一次摸頭，之後每 3000ms 再計） |
| `touch_tickle_laugh` | touch | 480 | ✓ | pivot | 搓：1000ms 內 ≥4 次方向反轉（每段 ≥8px）→ 笑 loop，持續搓就繼續；停手 → touch_tickle_roll |
| `touch_tickle_roll` | touch | 3000 |  | center +groundLock | tickle_laugh 完（停搓 ≥300ms）→ 喺地上碌 3 秒：碌左一圈再碌返轉頭 |
| `touch_pull_hold` | touch | 400 | ✓ | pivot | 按住拖 >40px：hold loop；引擎按拖嘅距離 d 實時加 stretch：sy *= 1+min(d/160,0.25)、sx *= 1-min(d/320,0.12)，rot 向拖方向（±12°） |
| `touch_pull_release` | touch | 700 |  | pivot | 拉住（>40px）後放手 → 彈返原位＋落地壓扁；系列煙 |
| `touch_shake_dizzy` | touch | 2000 |  | pivot | 1000ms 內 2 次 >2.5g（加速度計）→ 暈 2 秒＋頭頂轉星；冷卻 30000ms（冷卻中再搖：唔觸發）。60s 內第 3 次 → touch_shake_pretend |
| `touch_shake_pretend` | touch | 2400 |  | pivot | 60s 內第 3 次搖：唔暈，扮冇事發生（望天吹口哨），引擎顯示對白 line_pretend（文字由 遊策 提供） |
| `touch_sleep_rub` | touch | 1600 |  | pivot | 瞓緊（sleep state）時任何手勢 → 揉眼、轉身（flipX）繼續瞓；唔會醒 |
| `touch_embarrassed` | touch | 1000 |  | pivot | 蠢萌反應進行中被戳 → 中斷該反應，播尷尬臉（之後回 idle） |
| `dim_glasses_count` | dim | 4400 |  | pivot | DIM（見下）：戴眼鏡數嘢 1、2、3…數唔掂 → 問號、側頭 |
| `dim_book_sleep` | dim | 5200 |  | pivot | DIM：睇書 → 揭頁 → 頭耷耷 → 瞓著，本書合埋跌落地；之後交返 sleep state（或 2s 後自己醒） |
| `dim_wall_bump` | dim | 3800 |  | side_r | DIM：自己行去右邊，撞埋一幅牆（牆左邊緣 = side_r.x + 11px，貼地），彈返、暈、系列星 |
| `dim_mirror` | dim | 4600 |  | pivot | DIM：見到鏡，以為係另一隻寵物 → 嚇親（!）→ 眨眼、對方又一齊眨 → 側頭疑惑。倒影 = 同一幀寵物左右反轉縮細、clip 落玻璃 |
| `dim_count_fingers` | dim | 4200 |  | pivot | DIM：舉手仔數手指 1、2、…4（數錯，第 3 下叫 4）→ 得意 |
| `dim_professor` | dim | 4800 |  | pivot | DIM：戴四方帽、拎教鞭，喺黑板寫「1+1=3」＋「雲＝棉花糖」；引擎同步出自信錯誤對白（6×3 條，由 遊策 提供） |

### `touch_poke` — 500ms

tap（按落→放 <250ms、移動 <12px）。瞓緊 → touch_sleep_rub；蠢萌反應進行中 → touch_embarrassed

- face：`[{"t": 0, "f": "blink"}, {"t": 150, "f": null}]`
- FX（anchor ＋ dx,dy 偏移）：
  - `fx_poke` @ touch (0,0) 0–180ms 固定（唔跟身）

```json
{"body": [{"t": 0}, {"t": 60, "sx": 1.15, "sy": 0.85, "e": "out"}, {"t": 150, "sx": 0.95, "sy": 1.06, "e": "inout"}, {"t": 260, "sx": 1, "sy": 1, "e": "outBack"}]}
```

### `touch_pet_loop` — 1200ms

長按 ≥600ms 開始 loop；放手即停（回 idle 用 120ms ease-out）。連續按滿 3000ms → event pat（計一次摸頭，之後每 3000ms 再計）

- events：`[{"t": 3000, "id": "pat", "repeatEvery": 3000, "note": "相對 long-press 開始計（包埋前 600ms）"}]`
- face：`[{"t": 0, "f": ["squint", "squint", "squint_blush", "squint_blush"], "ms": 300}]`
- FX（anchor ＋ dx,dy 偏移）：
  - `fx_heart` @ headTop (7,-2) 200–1100ms

```json
{"body": [{"t": 0}, {"t": 300, "sx": 1.04, "sy": 0.96, "rot": -2, "e": "inout"}, {"t": 600, "sx": 1, "sy": 1, "rot": 0, "e": "inout"}, {"t": 900, "sx": 1.04, "sy": 0.96, "rot": 2, "e": "inout"}, {"t": 1200, "sx": 1, "sy": 1, "rot": 0, "e": "inout"}]}
```

### `touch_tickle_laugh` — 480ms

搓：1000ms 內 ≥4 次方向反轉（每段 ≥8px）→ 笑 loop，持續搓就繼續；停手 → touch_tickle_roll

- face：`[{"t": 0, "f": ["laugh_a", "laugh_b"], "ms": 120}]`
- FX（anchor ＋ dx,dy 偏移）：
  - `fx_laugh_l` @ side_l (-1,0) 0–480ms
  - `fx_laugh_r` @ side_r (1,0) 0–480ms
  - `fx_tear` @ eyeR (3,1) 0–480ms

```json
{"body": [{"t": 0, "rot": -6, "y": 0}, {"t": 120, "rot": 6, "y": -2, "e": "inout"}, {"t": 240, "rot": -6, "y": 0, "e": "inout"}, {"t": 360, "rot": 6, "y": -2, "e": "inout"}, {"t": 480, "rot": -6, "y": 0, "e": "inout"}]}
```

### `touch_tickle_roll` — 3000ms

tickle_laugh 完（停搓 ≥300ms）→ 喺地上碌 3 秒：碌左一圈再碌返轉頭

- face：`[{"t": 0, "f": ["laugh_a", "laugh_b"], "ms": 140}, {"t": 2850, "f": "squint"}]`
- FX（anchor ＋ dx,dy 偏移）：
  - `series_puff` @ pivot (-18,0) 1350–1650ms 固定（唔跟身） z=back
  - `fx_sparkle` @ headTop (0,-3) 2850–3000ms

```json
{"body": [{"t": 0}, {"t": 1400, "rot": -360, "x": -18, "e": "inout"}, {"t": 1600, "rot": -360, "x": -18}, {"t": 2850, "rot": 0, "x": 0, "e": "inout"}, {"t": 3000}], "origin": "center", "rotStep": 45}
```

### `touch_pull_hold` — 400ms

按住拖 >40px：hold loop；引擎按拖嘅距離 d 實時加 stretch：sy *= 1+min(d/160,0.25)、sx *= 1-min(d/320,0.12)，rot 向拖方向（±12°）

- face：`[{"t": 0, "f": "surprised"}]`
- FX（anchor ＋ dx,dy 偏移）：
  - `fx_sweat` @ headTop (8,2) 0–400ms

```json
{"body": [{"t": 0, "sx": 0.92, "sy": 1.1, "y": -2}, {"t": 200, "sx": 0.9, "sy": 1.12, "y": -3, "e": "inout"}, {"t": 400, "sx": 0.92, "sy": 1.1, "y": -2, "e": "inout"}]}
```

### `touch_pull_release` — 700ms

拉住（>40px）後放手 → 彈返原位＋落地壓扁；系列煙

- face：`[{"t": 0, "f": "surprised"}, {"t": 120, "f": "blink"}, {"t": 260, "f": null}]`
- FX（anchor ＋ dx,dy 偏移）：
  - `series_puff` @ pivot (-11,0) 120–420ms 固定（唔跟身） z=back
  - `series_puff` @ pivot (11,0) 120–420ms 固定（唔跟身） 鏡像 z=back

```json
{"body": [{"t": 0, "sx": 0.88, "sy": 1.18, "y": -6}, {"t": 120, "sx": 1.22, "sy": 0.8, "y": 0, "e": "in"}, {"t": 260, "sx": 0.94, "sy": 1.08, "e": "out"}, {"t": 420, "sx": 1.03, "sy": 0.97, "e": "inout"}, {"t": 600, "sx": 1, "sy": 1, "e": "outBack"}, {"t": 700}]}
```

### `touch_shake_dizzy` — 2000ms

1000ms 內 2 次 >2.5g（加速度計）→ 暈 2 秒＋頭頂轉星；冷卻 30000ms（冷卻中再搖：唔觸發）。60s 內第 3 次 → touch_shake_pretend

- face：`[{"t": 0, "f": ["dizzy_a", "dizzy_b"], "ms": 160}, {"t": 1900, "f": "blink"}, {"t": 2000, "f": null}]`
- FX（anchor ＋ dx,dy 偏移）：
  - `series_orbit` @ headTop (0,-3) 0–1900ms
  - `fx_sweat` @ headTop (-8,3) 400–1300ms

```json
{"body": [{"t": 0, "sx": 1.1, "sy": 0.9}, {"t": 120, "sx": 1, "sy": 1, "e": "outBack"}, {"t": 355, "rot": 7, "x": 1, "e": "inout"}, {"t": 590, "rot": -7, "x": -1, "e": "inout"}, {"t": 825, "rot": 7, "x": 1, "e": "inout"}, {"t": 1060, "rot": -7, "x": -1, "e": "inout"}, {"t": 1295, "rot": 7, "x": 1, "e": "inout"}, {"t": 1530, "rot": -7, "x": -1, "e": "inout"}, {"t": 1765, "rot": 7, "x": 1, "e": "inout"}, {"t": 2000, "rot": 0, "x": 0, "e": "inout"}]}
```

### `touch_shake_pretend` — 2400ms

60s 內第 3 次搖：唔暈，扮冇事發生（望天吹口哨），引擎顯示對白 line_pretend（文字由 遊策 提供）

- events：`[{"t": 300, "id": "line:shake_pretend"}]`
- face：`[{"t": 0, "f": "smug"}, {"t": 1200, "f": "lookup"}, {"t": 1350, "f": "smug"}]`
- FX（anchor ＋ dx,dy 偏移）：
  - `fx_sweat` @ headTop (-8,3) 600–2000ms
  - `fx_sparkle` @ headTop (10,-4) 300–900ms

```json
{"body": [{"t": 0}, {"t": 200, "x": 2, "rot": 3, "e": "out"}, {"t": 2100, "x": 2, "rot": 3}, {"t": 2400, "x": 0, "rot": 0, "e": "inout"}]}
```

### `touch_sleep_rub` — 1600ms

瞓緊（sleep state）時任何手勢 → 揉眼、轉身（flipX）繼續瞓；唔會醒

- face：`[{"t": 0, "f": "sleepy"}, {"t": 650, "f": "sleep"}]`
- FX（anchor ＋ dx,dy 偏移）：
  - `paw` @ eyeR (-1,1) 100–620ms
  - `fx_zzz` @ headTop (6,-1) 900–1600ms

```json
{"body": [{"t": 0}, {"t": 120, "sx": 1.06, "sy": 0.94, "e": "out"}, {"t": 300, "sx": 1, "sy": 1, "e": "inout"}, {"t": 650, "sx": 0.94, "sy": 1.04, "e": "in"}, {"t": 700, "flip": 1, "sx": 1.1, "sy": 0.9, "e": "step"}, {"t": 850, "sx": 1, "sy": 1, "e": "outBack"}, {"t": 1600}]}
```

### `touch_embarrassed` — 1000ms

蠢萌反應進行中被戳 → 中斷該反應，播尷尬臉（之後回 idle）

- face：`[{"t": 0, "f": "embarrassed"}]`
- FX（anchor ＋ dx,dy 偏移）：
  - `fx_sweat` @ headTop (8,2) 100–1000ms

```json
{"body": [{"t": 0}, {"t": 120, "sx": 1.06, "sy": 0.92, "y": 1, "e": "out"}, {"t": 800, "sx": 1.04, "sy": 0.94, "y": 1}, {"t": 1000, "sx": 1, "sy": 1, "y": 0, "e": "outBack"}]}
```

### `dim_glasses_count` — 4400ms

DIM（見下）：戴眼鏡數嘢 1、2、3…數唔掂 → 問號、側頭

- wear：`[{"id": "glasses", "t0": 0, "t1": 4400, "frames": [{"t": 0, "f": 0}, {"t": 300, "f": 1}, {"t": 520, "f": 0}, {"t": 3000, "f": 1}, {"t": 3200, "f": 0}]}]`
- face：`[{"t": 0, "f": null}, {"t": 700, "f": "lookup"}, {"t": 2800, "f": "blink"}, {"t": 2950, "f": null}]`
- FX（anchor ＋ dx,dy 偏移）：
  - `fx_num_1` @ headTop (-6,-3) 800–2700ms
  - `fx_num_2` @ headTop (0,-5) 1400–2700ms
  - `fx_num_3` @ headTop (6,-3) 2000–2700ms
  - `fx_question` @ headTop (7,-3) 2900–4400ms

```json
{"body": [{"t": 0, "sy": 1.06, "sx": 0.96}, {"t": 200, "sy": 1, "sx": 1, "e": "outBack"}, {"t": 800}, {"t": 900, "y": -1, "e": "out"}, {"t": 1000, "y": 0, "e": "in"}, {"t": 1500, "y": -1, "e": "out"}, {"t": 1600, "y": 0, "e": "in"}, {"t": 2100, "y": -1, "e": "out"}, {"t": 2200, "y": 0, "e": "in"}, {"t": 2800, "rot": 0}, {"t": 3100, "rot": -8, "e": "outBack"}, {"t": 4100, "rot": -8}, {"t": 4400, "rot": 0, "e": "inout"}]}
```

### `dim_book_sleep` — 5200ms

DIM：睇書 → 揭頁 → 頭耷耷 → 瞓著，本書合埋跌落地；之後交返 sleep state（或 2s 後自己醒）

- face：`[{"t": 0, "f": null}, {"t": 1000, "f": "blink"}, {"t": 1150, "f": null}, {"t": 1800, "f": "sleepy"}, {"t": 3150, "f": "sleep"}]`
- FX（anchor ＋ dx,dy 偏移）：
  - `fx_book` @ chest (0,4) 0–3200ms
  - `fx_book` @ pivot (10,0) 3200–5200ms 固定（唔跟身）
  - `fx_zzz` @ headTop (6,-1) 3400–5200ms

```json
{"body": [{"t": 0}, {"t": 1800, "y": 0}, {"t": 2100, "y": 1, "rot": 3, "e": "inout"}, {"t": 2300, "y": 0, "rot": 0, "e": "out"}, {"t": 2700, "y": 1, "rot": 4, "e": "inout"}, {"t": 2900, "y": 0, "rot": 0, "e": "out"}, {"t": 3200, "y": 2, "rot": 6, "sx": 1.05, "sy": 0.94, "e": "in"}, {"t": 4200, "sy": 0.96}, {"t": 4700, "sy": 0.94, "e": "inout"}, {"t": 5200, "sy": 0.96, "e": "inout"}]}
```

### `dim_wall_bump` — 3800ms

DIM：自己行去右邊，撞埋一幅牆（牆左邊緣 = side_r.x + 11px，貼地），彈返、暈、系列星

- face：`[{"t": 0, "f": null}, {"t": 1500, "f": "surprised"}, {"t": 1700, "f": ["dizzy_a", "dizzy_b"], "ms": 160}, {"t": 3600, "f": "blink"}, {"t": 3700, "f": null}]`
- FX（anchor ＋ dx,dy 偏移）：
  - `fx_wall` @ side_r (11,0) 0–3800ms 固定（唔跟身） 貼地 z=front
  - `series_puff` @ side_r (9,-4) 1500–1800ms 固定（唔跟身）
  - `series_orbit` @ headTop (0,-3) 1750–3500ms

```json
{"body": [{"t": 0}, {"t": 150, "x": 1, "y": -1, "e": "linear"}, {"t": 300, "x": 2, "y": 0, "e": "linear"}, {"t": 450, "x": 3, "y": -1, "e": "linear"}, {"t": 600, "x": 4, "y": 0, "e": "linear"}, {"t": 750, "x": 5, "y": -1, "e": "linear"}, {"t": 900, "x": 6, "y": 0, "e": "linear"}, {"t": 1050, "x": 7, "y": -1, "e": "linear"}, {"t": 1200, "x": 8, "y": 0, "e": "linear"}, {"t": 1350, "x": 9, "y": -1, "e": "linear"}, {"t": 1500, "x": 10, "y": 0, "e": "linear"}, {"t": 1560, "x": 10, "y": 0, "sx": 0.82, "sy": 1.08, "e": "out"}, {"t": 1700, "x": 8, "sx": 1.04, "sy": 0.97, "e": "out"}, {"t": 1900, "x": 6, "y": -3, "sx": 1, "sy": 1, "e": "out"}, {"t": 2100, "x": 5, "y": 0, "e": "in"}, {"t": 2200, "sx": 1.08, "sy": 0.92, "e": "out"}, {"t": 2350, "sx": 1, "sy": 1, "e": "outBack"}, {"t": 2590, "rot": 5, "e": "inout"}, {"t": 2830, "rot": -5, "e": "inout"}, {"t": 3070, "rot": 5, "e": "inout"}, {"t": 3310, "rot": -5, "e": "inout"}, {"t": 3550, "rot": 0, "e": "inout"}, {"t": 3800}], "origin": "side_r"}
```

### `dim_mirror` — 4600ms

DIM：見到鏡，以為係另一隻寵物 → 嚇親（!）→ 眨眼、對方又一齊眨 → 側頭疑惑。倒影 = 同一幀寵物左右反轉縮細、clip 落玻璃

- face：`[{"t": 0, "f": null}, {"t": 750, "f": "surprised"}, {"t": 1500, "f": null}, {"t": 2000, "f": "blink"}, {"t": 2150, "f": null}, {"t": 2700, "f": "blink"}, {"t": 2850, "f": null}, {"t": 3300, "f": "lookup"}]`
- FX（anchor ＋ dx,dy 偏移）：
  - `fx_mirror_back` @ side_r (13,0) 0–4600ms 固定（唔跟身） 貼地 z=back
  - `fx_mirror_front` @ side_r (13,0) 0–4600ms 固定（唔跟身） 貼地 z=front
  - `fx_exclaim` @ headTop (0,-3) 800–1500ms
  - `fx_question` @ headTop (6,-3) 3450–4600ms

```json
{"body": [{"t": 0}, {"t": 700}, {"t": 800, "sx": 1.1, "sy": 0.9, "e": "out"}, {"t": 950, "sx": 0.94, "sy": 1.08, "y": -4, "e": "out"}, {"t": 1100, "sx": 1, "sy": 1, "y": 0, "e": "in"}, {"t": 1200, "sx": 1.06, "sy": 0.94, "e": "out"}, {"t": 1350, "sx": 1, "sy": 1, "e": "outBack"}, {"t": 3300, "rot": 0}, {"t": 3550, "rot": 7, "e": "outBack"}, {"t": 4400, "rot": 7}, {"t": 4600, "rot": 0, "e": "inout"}]}
```

### `dim_count_fingers` — 4200ms

DIM：舉手仔數手指 1、2、…4（數錯，第 3 下叫 4）→ 得意

- face：`[{"t": 0, "f": "lookup"}, {"t": 3200, "f": "smug"}]`
- FX（anchor ＋ dx,dy 偏移）：
  - `paw` @ side_r (-1,-3) 200–4000ms
  - `fx_num_1` @ side_r (4,-14) 600–1400ms
  - `fx_num_2` @ side_r (4,-14) 1400–2200ms
  - `fx_num_4` @ side_r (4,-14) 2200–4000ms
  - `fx_sparkle` @ headTop (-8,-2) 3200–3800ms

```json
{"body": [{"t": 0}, {"t": 200, "rot": -3, "e": "out"}, {"t": 3200, "rot": -3}, {"t": 3350, "rot": 0, "y": -2, "e": "out"}, {"t": 3500, "y": 0, "e": "in"}, {"t": 4200}]}
```

### `dim_professor` — 4800ms

DIM：戴四方帽、拎教鞭，喺黑板寫「1+1=3」＋「雲＝棉花糖」；引擎同步出自信錯誤對白（6×3 條，由 遊策 提供）

- events：`[{"t": 2200, "id": "line:professor"}]`
- wear：`[{"id": "hat", "t0": 0, "t1": 4800, "frames": [{"t": 0, "f": [0, 1], "ms": 300}]}]`
- face：`[{"t": 0, "f": "smug"}, {"t": 1600, "f": "blink"}, {"t": 1750, "f": "smug"}]`
- FX（anchor ＋ dx,dy 偏移）：
  - `fx_board` @ side_l (-14,0) 0–4800ms 固定（唔跟身） 貼地 z=back
  - `fx_pointer` @ side_l (1,0) 300–4800ms 鏡像
  - `fx_sparkle` @ headTop (9,-3) 3450–4100ms

```json
{"body": [{"t": 0, "sx": 1.06, "sy": 0.94}, {"t": 180, "sx": 1, "sy": 1, "e": "outBack"}, {"t": 2000}, {"t": 2150, "rot": -4, "e": "out"}, {"t": 2300, "rot": 0, "e": "out"}, {"t": 2450, "rot": -4, "e": "out"}, {"t": 2600, "rot": 0, "e": "out"}, {"t": 3300, "sy": 1}, {"t": 3450, "sy": 1.06, "sx": 0.96, "y": -1, "e": "out"}, {"t": 3700, "sy": 1, "sx": 1, "y": 0, "e": "outBack"}, {"t": 4800}]}
```

## 驗證

- 全部 sprite／patch alpha 只有 0/255；每個 sprite ≤12 色；面 patch 全部喺身體 mask 入面；`neutral` 面重畫 = base（49 隻 diff 0 px）。見 `check/validation.json`。

## 未解決／注意

1. 四方帽／數字／轉星用 `headTop`：新線有角、月牙、光環嘅（F3、G3、H3、E3、A 系水滴尖）係估算位，帽會疊喺月牙／光環前面；如要逐隻微調，改 `anchors.json` headTop 即可（帽 patch 要重跑生成）。
2. 旋轉用最近鄰：碌地 45° 位會有鋸齒（已加 `rotStep:45` 建議；引擎可以改 90 減鋸齒）。
3. 對白（扮冇事、扮教授 6×3 條）只出 event `line:*`，文字由 遊策 文件提供，art 唔畫字。
4. 拉扯 hold 嘅實時拉長公式喺 trigger 欄，數值要真機調。搖晃 2.5g 閾值／搓 4 次都未上機試。
5. 舊線 sprout／radiant／soft 冇 idle noface layer → 用 ATTACH 眼 blob 自動拆面（已檢查 diff 0），但 evo6 kit 本身有現成表情，如要可以換返用嗰套。
6. 鏡入面倒影只係靜態縮細（跟面，所以會一齊眨眼），唔跟身體彈跳。
