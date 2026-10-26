# CLIPS（團絨動態 clip 表，俾遊程）

三形態 sprout 32px／radiant 64px／soft 64px **共用同一份 clip 表**：clip 名、幀數、fps、pivot 規則完全一樣。機讀版：`CLIPS.json`。
引擎：Nearest、關 mipmap、整數倍縮放；腳底接地用 blob shadow（唔烙入 sprite）。

## 檔案

- `atlas_<form>.png/json`：每形態單一圖集（1024 寬；padding 2px、extrude 1px、免 trim；`animations` 內有 clip→幀序列＋fps＋loop＋loopFrom）。
- `atlas_props.png/json`：共用道具圖集（花盆、光斑、zzz、心、汗、驚嘆號、問號），每幀有 `pivotPx`。
- `frames/<form>/<clip>_<NN>.png` 單幀；`layers/<form>/emo_*_NN_noface.png`＋`_overlay.png`：表情 6 款嘅「無五官身體」＋「五官 overlay」（眼／口／眉／加強腮紅），需要逐部位換表情時用；完整幀同 atlas 一致。
- `preview/<form>/<clip>_8x.gif`（連道具合成）、`contact_<form>.png`；`palette.json`（31 色，同 `../palette.json`）。

## 規格

- **pivot**：底部中心 `(w/2, h-3)`（sprout (16,29)；radiant／soft (32,61)）。引擎把 pivot 放喺地面接觸點／blob shadow 中心。腳掌輪廓最底約 pivot 下 2px（sprout 貼底）。
- 全部 PNG-24 RGBA、無抗鋸齒、alpha 只有 0／255、只用 `palette.json` 色（已逐檔驗證）。
- 動作內部嘅位移（dx）、斜傾（shear）、擠壓拉伸已烙入幀；引擎只需移動 pivot。幀內位移最大 ±4px（64px 形態）／±2px（32px 形態）。
- 32px 形態因畫布淨高 4px，跳躍幅度同位移已自動縮小（`_stats.json` 的 `fit_adjustments`），動作節奏／幀數與 64px 形態一致。
- **Zzz／圖示係獨立圖層**，幀內唔烙入；位置用下表 anchor。圖層 pivot 對準 anchor：`圖示左上 = pet pivot + anchor − prop pivotPx`。

### Anchor（相對 pet pivot，px；y 向下為正）

| form | head_r（頭右上，圖示／zzz） | pot（花盆 pivot） | sun（光斑中心） |
|---|---|---|---|
| sprout | (9, -14) | (22, 0) | (0, 0) |
| radiant | (16, -28) | (31, 0) | (0, 0) |
| soft | (18, -30) | (34, 0) | (0, 0) |

## Clip 表（每形態幀數一致）

優先級：數字越大越高；高優先級可打斷低優先級嘅「可中斷」clip；「否」嘅 clip 必須播完（或至 hold 完）先處理下一個。

| clip | 狀態 | 類別 | 幀數 | fps | loop | 觸發條件 | 優先級 | 可中斷 | 冷卻(s) | 播完接 | 備註 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `idle` | 已交付 | 待機 | 4 | 6 | 是 | 預設基礎動畫；無其他 clip 時循環 | 0 | 是 | — | — | 沿用舊 idle（4 幀）。引擎冇指令時回到呢個。 |
| `blink` | 已交付 | 待機變化 | 4 | 10 | 否 | 待機 6–15 秒隨機抽一次（權重 blink 50／sway 30／yawn 20） | 1 | 是 | — | idle | 一次過播完回 idle；每次抽籤間隔 random(6,15) 秒。 |
| `sway` | 已交付 | 待機變化 | 4 | 5 | 否 | 同上（權重 30） | 1 | 是 | — | idle | 光芽左右擺；愛睏時（精力<60）權重減半。 |
| `yawn` | 已交付 | 待機變化 | 4 | 4 | 否 | 同上（權重 20；精力<60 時權重 ×2，精力<30 時 ×3） | 1 | 是 | — | idle | 第 2–3 幀張口最大；可配 0.8 秒呵欠音效。 |
| `emo_happy` | 已交付 | 表情 | 2 | 4 | 否（重複×4） | 剛被照顧（餵食／清潔／玩耍完成後） | 4 | 是 | — | idle | 2 幀循環 ×4（≈2 秒）；無圖示；可疊 fx 開心星星。 |
| `emo_hungry` | 已交付 | 表情 | 2 | 3 | 是 | 飽腹 < 30 持續 | 3 | 是 | — | — | 狀態成立期間取代 idle 循環；光芽變暗；掛 sweat 圖示（head_r）。 |
| `emo_wantplay` | 已交付 | 表情 | 2 | 4 | 是 | 心情 < 30 持續（且未飢餓／未睏） | 3 | 是 | — | — | 取代 idle 循環；掛 question 圖示；舉手期待。 |
| `emo_sleepy` | 已交付 | 表情 | 2 | 2 | 是 | 精力 < 30 持續 | 3 | 是 | — | — | 取代 idle 循環；掛 zzz 圖層；精力 < 15 可直接進 fall_asleep。 |
| `emo_cuddly` | 已交付 | 表情 | 2 | 3 | 是 | 連續摸（2 秒內 ≥3 次，持續按摸） | 4 | 是 | — | idle | 撒嬌磨蹭；摸停後再播完當前幀回 idle；掛 heart 圖示；最少播 1.5 秒。 |
| `emo_surprised` | 已交付 | 表情 | 2 | 6 | 否 | 突然點擊（閒置 >5 秒後首點）／事件彈出／被嚇 | 4 | 否 | — | idle | 只播 1 次，停喺最後幀 0.6 秒；掛 exclaim。膽小：之後 60% 機會接 walk 離開觸點。 |
| `walk` | 已交付 | 自主動作 | 6 | 10 | 是 | 狀態機抽中：隨機走動，或朝最近觸點（5 秒內） | 2 | 是 | — | idle | 朝右；朝左由引擎 scaleX=-1。位移建議每循環 6 幀 ≈ 12px（64px 形態）／6px（32px 形態）；原地播，由引擎移動 x。 |
| `play` | 已交付 | 自主動作 | 6 | 8 | 否 | 狀態機抽中（心情<70 或被逗玩）／玩具互動 | 3 | 否 | 8 | idle | 前撲：蹲→扭→彈→撲→落地；朝右，引擎可跟位移（第 3–5 幀向右約 4px）。 |
| `fall_asleep` | 已交付 | 睡眠流程 | 4 | 3 | 否 | 精力 < 30 且閒置 >10 秒；晚／夜時段機率 ×3；或玩家按「睡覺」 | 5 | 否 | — | sleep_loop | 第 2 幀起掛 zzz。 |
| `sleep_loop` | 已交付 | 睡眠流程 | 4 | 2 | 是 | fall_asleep 播完自動接 | 5 | 是 | — | — | 循環至精力 ≥ 90 或被點擊／事件／鬧鐘；掛 zzz；月光夜光效果由引擎做。 |
| `wake` | 已交付 | 睡眠流程 | 4 | 5 | 否 | sleep_loop 結束（精力滿／被摸／事件） | 5 | 否 | — | idle | 伸懶腰；被摸醒可接 emo_surprised 之前先播 wake 第 1–2 幀（引擎可截短）。 |
| `sunbathe` | 已交付 | 環境互動 | 8 | 4 | 是 | 晴天＋早／午時段，狀態機隨機；寵物行到光斑上才播 | 2 | 是 | 120 | idle | 掛 sun_patch（ground，墊底）；持續 8–20 秒（循環 8 幀）；被點擊中斷→emo_surprised。團絨怕冷：冷天機率 ×1.5。 |
| `pot_bump` | 已交付 | 環境互動 | 8 | 8 | 否 | 狀態機隨機（場景有花盆）；先 walk 到花盆左側 anchor | 2 | 否 | 180 | idle | 第 4 幀（索引 3）撞擊；同一刻起播 flowerpot_bump（4 幀）。花盆喺寵物右邊；如花盆喺左邊整個合成 scaleX=-1。 |
| `catch_reach` | 已交付 | 小遊戲／事件 | 6 | 8 | 否 | 接星屑小遊戲：星屑進接取範圍／玩家點擊接取 | 6 | 否 | — | idle | 第 4 幀（索引 3）判定「接到」；第 5–6 幀慶祝。接失敗唔播（改播 droop 或 emo_surprised）。 |
| `cheer_jump` | 已交付 | 小遊戲／事件 | 6 | 10 | 否 | 小遊戲過關／高分結算／事件獎勵 | 6 | 否 | — | idle | 單次；第 3 幀頂點；可配 fx 開心星星。 |
| `droop` | 已交付 | 小遊戲／事件 | 6 | 4 | 否→第4幀起循環 | 小遊戲失敗／未達標／任務失敗 | 6 | 是 | — | — | 第 1–3 幀進入，之後第 4–6 幀（loopFrom=3）循環抽泣直至離開結算畫面；掛 sweat。 |
| `eat` | 已交付 | 既有 | 4 | 8 | 否 | 餵食 | 5 | 否 | — | emo_happy | 舊 eat 4 幀（原 build_tuanrong.py）。 |
| `celebrate` | 已交付 | 既有 | 4 | 8 | 否 | 進化完成／升級／慶祝（舊 happy 4 幀） | 5 | 否 | — | idle | 舊 `happy` 改名 celebrate（避免同表情 emo_happy 撞名）。 |
| `sick` | 已交付 | 既有 | 2 | 3 | 是 | 生病狀態持續 | 5 | 是 | — | — | 舊 sick 2 幀；優先級高過所有表情；可配 fx 汗滴。 |

**範圍說明**：遊策已批准全部動作（①②④ 已交付；③ 走／玩耍、⑤ 曬太陽／碰花盆、⑥ catch_reach／cheer_jump／droop 經美術驗收，狀態＝已交付）。花盆（flowerpot_*）、光斑（sun_patch）道具同屬已交付。時段背景光：`../../../scenes/daylight/`；事件 icon：`../../../fx/events/`。

**v2 修訂（驗收時）**：`walk` 改為完整步態（左步＋右步，6 幀可無縫循環，逐步抬腳、幀內 dx 週期為 0，朝右）；`play` 幀內 dx 淨值為 0（蹲後撲前、落地後回中，無尾幀跳位），引擎如要追位移，喺第 4–5 幀額外向右約 4px（64px）／2px（32px）；sprout 跳躍（play／catch_reach／cheer_jump）提升到 2px（頂部淨 4px 內，光芽喺跳躍幀固定 1.0 倍）。clip 名／幀數／fps／pivot 不變。

每形態合計 96 幀（含舊 idle 4／eat 4／celebrate 4／sick 2）；新增 82 幀。

## 圖層道具（props）

| prop | 說明 | 幀數 | pivotPx | fps | loop | 尺寸 | anchor | 用途 |
|---|---|---|---|---|---|---|---|---|
| `flowerpot_idle` | 花盆（靜態） | 1 | [16, 29] | 1 | 是 | 32x32 | pot | pot_bump 期間常駐；場景亦可獨立擺放 |
| `flowerpot_bump` | 花盆被碰搖動 4 幀 | 4 | [16, 29] | 8 | 否 | 32x32 | pot | pet pot_bump 第 4 幀（索引 3）起播；fps 8、播 1 次後回 flowerpot_idle |
| `sun_patch` | 曬太陽光斑 2 幀 loop | 2 | [24, 8] | 2 | 是 | 48x16 | sun | sunbathe 期間墊喺寵物腳下（pivot＝光斑中心）；引擎可再疊 additive 暖光 |
| `zzz` | Zzz 3 幀 loop（獨立圖層） | 3 | [2, 22] | 2 | 是 | 24x24 | head_r | sleep_loop／fall_asleep／emo_sleepy；pivot 左下 |
| `heart` | 心 2 幀 | 2 | [8, 14] | 3 | 是 | 16x16 | head_r | emo_cuddly |
| `sweat` | 汗滴 2 幀 | 2 | [8, 14] | 3 | 是 | 16x16 | head_r | emo_hungry／droop |
| `exclaim` | 驚嘆號 2 幀 | 2 | [8, 14] | 4 | 是 | 16x16 | head_r | emo_surprised |
| `question` | 問號 2 幀 | 2 | [8, 14] | 3 | 是 | 16x16 | head_r | emo_wantplay |

### 掛載（attachments）

| clip | prop | anchor | 由第幾幀（0 起）開始 | 墊底 |
|---|---|---|---|---|
| `emo_hungry` | `sweat` | head_r | 0 | 否 |
| `emo_wantplay` | `question` | head_r | 0 | 否 |
| `emo_sleepy` | `zzz` | head_r | 0 | 否 |
| `emo_cuddly` | `heart` | head_r | 0 | 否 |
| `emo_surprised` | `exclaim` | head_r | 0 | 否 |
| `fall_asleep` | `zzz` | head_r | 1 | 否 |
| `sleep_loop` | `zzz` | head_r | 0 | 否 |
| `sunbathe` | `sun_patch` | sun | 0 | 是 |
| `pot_bump` | `flowerpot_idle` | pot | 0 | 否 |
| `pot_bump` | `flowerpot_bump` | pot | 3 | 否 |
| `droop` | `sweat` | head_r | 3 | 否 |

## 狀態機建議

1. **基礎層**（循環）：優先 `sick` > `emo_hungry`(飽腹<30) > `emo_sleepy`(精力<30) > `emo_wantplay`(心情<30) > `idle`。需求狀態成立時以對應 emo clip 取代 idle 作循環基礎。
2. **待機變化**：只喺基礎層係 idle 時，每 random(6,15) 秒按權重抽 blink／sway／yawn，播完回 idle。
3. **自主行為**：每 4–10 秒 tick 一次，團絨權重 idle 40／隨機走動 15／朝觸點走 25／玩耍 8／曬太陽 10／碰花盆 6／入睡 12；條件修正見 `CLIPS.json.stateMachine.weightMods`。
4. **反應層**（打斷）：點擊→`emo_surprised`（閒置>5 秒後首點）；連續摸→`emo_cuddly`；照顧完成→`emo_happy`；小遊戲結果→`catch_reach`／`cheer_jump`／`droop`。
5. **睡眠流程**：`fall_asleep`→`sleep_loop`→`wake`；睡眠中被點擊先 `wake` 再按需要接 `emo_surprised`。
6. **環境互動**：`sunbathe`（晴天早／午，冷卻 120s）、`pot_bump`（有花盆，冷卻 180s，先 walk 到 anchor）；同一時間只一個。
7. 朝向：全部朝右；朝左用 scaleX=-1（pivot 喺水平中心，鏡像唔偏移）。

