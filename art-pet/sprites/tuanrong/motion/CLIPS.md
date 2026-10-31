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



## 生命感 add-on（v2，10-31，精簡級）

全部喺 `liveliness/`；詳細疊法睇 `liveliness/FACE_RIG.md`。CLIPS.json 每個 clip 新增 `anchors[form][幀]`（frame 左上角 px）同 `layers.noface`；`liveliness/face_anchors.json` 係同一份錨點嘅鏡像。原 CLIPS.* 備份喺 `liveliness/_backup_v1/`。

- 無臉身體：每個 clip 有 `<clip>_noface`（atlas animation）＋ `liveliness/layers/<form>/<clip>_NN_noface.png`；`_faceov.png` 疊返＝原幀（逐像素驗證）。腮紅保留喺身體（舊 `layers/emo_*_noface` 冇腮紅，屬 v1）。
- 五官套：`eyes_<style>_<gaze>_<l|r>`、`mouth_<style>`；`bulb_base`＋`bulb_glow`。同身體幀一齊入 `atlas_<form>_live.png`。

### 新 clip（每 form 幀數相同，朝右）

| clip | 項目 | 幀數 | fps | loop | 優先級 | 可中斷 | 冷卻(s) | 觸發條件 | 播完接 | 備註 |
|---|---|---|---|---|---|---|---|---|---|---|
| `walk_happy` | A3 心情步姿 | 6 | 10 | 是 | 2 | 是 | — | walk 嘅替身：心情 ≥ 70（或 emo_happy 後 10 秒內）時 walk 改播 walk_happy | idle | 蹦跳步，每循環 2 跳；原地播，引擎移 x（建議每循環 ≈14px／64px、7px／32px，比 walk 快 15%）。可配腳步塵 G3。 |
| `walk_drag` | A3 心情步姿 | 6 | 6 | 是 | 2 | 是 | — | walk 嘅替身：精力 < 40 或飽腹 < 40 時 walk 改播 walk_drag | idle | 拖步：矮身、光芽垂低、第 2／5 幀腳邊起塵。引擎位移 ≈ walk 嘅 60%。 |
| `sniff` | A2 中途停低 | 4 | 6 | 否 | 2 | 是 | 25 | walk 途中每段 15% 機率停低（3 款 A2 平均抽）；或行經花盆／食物 | idle | 低頭嗅地兩下再抬頭；第 2–3 幀可配 0.3s 嗅嗅音效。 |
| `lookup` | A2 中途停低 | 4 | 5 | 否 | 2 | 是 | 25 | 同上；夜晚／有螢火／流星事件時權重 ×3 | idle | 抬頭望天；第 2–3 幀可 hold 0.8s（引擎延長）；配 gaze U。 |
| `swat` | A2 中途停低 | 4 | 8 | 否 | 2 | 否 | 40 | 同上；或場景有蟲仔／螢火 fx 飛近 head_r 範圍 | idle | 撥走蟲仔：第 3 幀（索引 2）出手判定；蟲仔 fx 由引擎（可用螢火 icon）。 |
| `scratch` | B1 抓癢 | 6 | 8 | 否 | 1 | 是 | 600 | idle 變化抽籤（權重 12）；同一小動作 ≥10 分鐘唔重複 | idle | 後爪去頭頂抓 2 下；第 2–5 幀可重播 1 次；表情舒服瞇眼。 |
| `sneeze` | B2 打噴嚏 | 5 | 8 | 否 | 1 | 否 | 600 | idle 變化抽籤（權重 8）；靠近花盆／曬太陽後機率 ×2；冷天 ×1.5 | idle | 第 3 幀（索引 2）乞嗤（噴霧點烙入幀）；可配音效；之後 30% 接 emo_surprised。 |
| `nuzzle` | D3 長按蹭手 | 6 | 6 | 是 | 4 | 是 | — | 長按寵物 ≥0.4s 持續；手指喺寵物右邊（左邊用 scaleX −1） | idle | 向右挨埋手指上下磨蹭；鬆手後播完當前幀回 idle；掛 heart（head_r）；取代 emo_cuddly 作長按版。 |
| `rush` | D5 久未見衝埋嚟 | 6 | 12 | 否 | 6 | 否 | — | 開 app 時離線 ≥6h（每日最多 1 次） | cheer_jump | 第 1 幀起步；第 2–5 幀（loopRange [1,4]）跑步循環直至到達玩家前位置；第 6 幀煞停 → 接 cheer_jump。速度線同塵烙入幀。 |
| `turn_back` | D2 點一下回頭 | 4 | 8 | 否 | 4 | 否 | — | 寵物背向／行緊路時被點一下；或 walk 中被點 | emo_happy | 第 1 幀背面（faceVisible=false，唔好疊五官）、第 2 幀 3/4 側（眼距收窄）、第 3 幀轉正彈起、第 4 幀定。之後按心情接 emo_happy（心情≥50）或 emo_surprised。 |
| `picked_up` | D6 被拎起（浮動團絨） | 6 | 8 | 是 | 7 | 否 | — | Android 浮動寵物：手指按住寵物頭頂拖動／長按拎起（拖曳開始）時播；直至放手 | idle | pivot＝anchors.grab（頭頂拎點），唔係腳底 pivot：引擎將 grab 對準手指位置。身體吊住微拉長、成個以 grab 為軸左右擺（鐘擺 shear）、兩隻腳交替輕踢。第一個循環建議 surprised（faceOnEnter），之後 happy。放手 → 引擎跌落／彈返地面再接 idle（或 emo_surprised）。可按拖動速度改 fps 6–12。 |
| `smug_pose` | S2 撲空扮醒（得意 pose） | 4 | 6 | 否 | 3 | 否 | 30 | swat／撲蟲撲空之後（蟲仔 fx 飛走）；或 catch_reach 接唔到時 50% 改播 | idle | 蠢蠢地但覺得自己好醒：第 1 幀撲空落地、第 2 幀企直、第 3–4 幀挺胸仰頭合眼 ω 口（雙手叉腰）；最後一幀 hold 0.8s（holdLast_s），第 4 幀頭頂閃一下（烙入幀）。表情 preset smug。 |
| `act_cool` | S2 扮冷靜 | 4 | 5 | 否 | 3 | 否 | 20 | sneeze 之後 40%／lookup_tip→getup 之後／picked_up 放低後 30% | idle | 扮冇事：第 1 幀別過頭（面向後偏 ft，眼 squint 望 L）、第 2 幀輕咳（咳氣烙入幀，向左）、第 3–4 幀拍拍身（塵烙入幀），最後仰少少頭側眼。 |
| `lookup_tip` | S2 望天望到跌 | 4 | 6 | 否 | 2 | 否 | 60 | lookup 播完後 20%（夜晚／流星 ×2）；接住 lookup 第 3 幀姿勢 | getup | 望天望到向後倒：前腳離地、搖兩搖、第 4 幀一屁股坐低（停住，接 getup）。 |
| `getup` | S2 起返身 | 4 | 6 | 否 | 2 | 否 | — | lookup_tip 播完自動接（或任何跌低／坐低後） | act_cool | 後手撐地（第 2 幀用力 angry 臉）→ 彈起 → 企定。播完 60% 接 act_cool，否則 idle。 |
| `sniff_itch` | S2 嗅到鼻癢（過渡） | 2 | 6 | 否 | 1 | 否 | — | sniff 第 3 幀之後如抽中 sneeze（機率 25%） | sneeze | sniff → sniff_itch → sneeze 過渡：第 1 幀鼻貼地抽兩抽（鼻癢線烙入幀）、第 2 幀抬頭瞇眼，下一幀直接接 sneeze_01。 |

名稱對照（策劃稿 → clip）：hop_walk→`walk_happy`、drag_walk→`walk_drag`、look_up→`lookup`、swat_bug→`swat`、dash→`rush`、D2 回頭→`turn_back`。A1／D1 邊行邊望＝gaze（唔使新 clip）。G1＝燈泡 overlay。

### 燈泡心情色（G1）

| mood | tint | intensity | 動態 |
|---|---|---|---|
| happy | `#FFD45E` | 1.0 | 1.2s 呼吸 0.85–1.0 |
| neutral | `#FFEFC4` | 0.8 | 無 |
| sleepy | `#8F85C2` | 0.55 | 3s 慢呼吸 0.4–0.6 |
| hungry | `#F2A65A` | 0.75 | 閃爍 0.8s（0.6–0.8） |
| grumpy | `#E5584D` | 0.85 | 0.4s 跳兩下 |

### 表情 preset（kit 組合）

| preset | eyes | gaze | mouth | 附圖示 |
|---|---|---|---|---|
| neutral | neutral | C | neutral | — |
| happy | happy | C | happy | — |
| sleepy | sleepy | C | sleepy | — |
| surprised | surprised | C | surprised | — |
| hungry | sad | D | wink | sweat |
| cuddly | squint | C | squint | heart |
| grumpy | angry | C | angry | — |
| curious | neutral | U | sleepy | question |
| wink | neutral（右眼 wink） | C | wink | — |
| smug | sleepy | C | squint | — |

<!-- EVO6A-START -->
## 進化 6 階 batch A（光卵／絨點／絨芽／絨跳，evo6 v3 lumi feel）
- 外觀＝`../evo6_concept/`（v3 lumi feel）；姿勢＝現有同名 clip（std23 ＋ 生命感 s1/s2，同 sprout/radiant/soft 一樣 fps／priority／anchors 結構），只換外觀層。
- 基本 31 色（`../palette.json`）、alpha 0/255、無 AA、向右；每形態一張 atlas（1024 闊、padding 2、extrude 1、每幀 pivotPx）＋ 同 layout emissive（白＝glow_core/glow_mid）。
- 每幀：`frames/<clip>_NN.png`、`layers/<clip>_NN_noface.png`／`_faceov.png`、`emissive/…`；錨點 `../evo6/<form>/face_anchors_<form>.json`（＝本檔 clips[].anchors.<form>）。
- face kit 按新尺寸重出：絨點／絨芽 4×4 豆眼（S 級）、絨跳 4×5（L 級＝燦光原裝）；bulb 只限絨跳（第一粒著燈）；picked_up pivot＝grab。
- 光卵冇 face rig（同舊蛋）：idle 4、glow 2、tap 4、hatch 6、picked_up 4（定義喺 `forms.evo_egg.clipDefs`）。

| 階 | 形態 | px | pivot | clip | 幀 | atlas |
|---|---|---|---|---|---|---|
| 1 | 光卵 `evo_egg` | 24 | (12, 21) | 5 | 20 | `../evo6/atlas_evo_egg.png`（1024×32，20 塊）＋ `_emissive` |
| 2 | 絨點 `evo_dot` | 28 | (14, 25) | 39 | 171 | `../evo6/atlas_evo_dot.png`（1024×512，426 塊）＋ `_emissive` |
| 3 | 絨芽 `evo_sprout` | 32 | (16, 29) | 39 | 171 | `../evo6/atlas_evo_sprout.png`（1024×512，426 塊）＋ `_emissive` |
| 4 | 絨跳 `evo_hop` | 38 | (19, 35) | 39 | 171 | `../evo6/atlas_evo_hop.png`（1024×1024，428 塊）＋ `_emissive` |

5 守夜者 44、6 靜光 48 ＝ batch B／C（未出）。
<!-- EVO6A-END -->

<!-- EVO6B-START -->
## 進化 6 階 守夜者 44 ×4（batch B）
- 外觀＝`../evo6_concept/`（v3 lumi feel，lf5_* 畫法逐幀 pose-aware 重畫）；姿勢＝現有同名 clip，只換外觀層；4×5 L 級 kit；picked_up pivot＝grab。
- 每幀 frames／layers（_noface／_faceov）／emissive；錨點 `../evo6/<form>/face_anchors_<form>.json`（bulb＝主燈；螢絨另有 bulb2／tail；靜光微塵 bulb2＝軌道吊燈）。
- 微塵另加 s3：nuzzle_purr 4、reunion_happy 5。

| 形態 | px | pivot | clip | 幀 | atlas | 色盤 |
|---|---|---|---|---|---|---|
| 守夜者・螢絨 `evo_guard_lumi` | 44 | (22, 41) | 39 | 171 | `../evo6/atlas_evo_guard_lumi.png`（1024×1024，426 塊）＋ `_emissive` | palette_lumi.json |
| 守夜者・燦光 `evo_guard_radiant` | 44 | (22, 41) | 39 | 171 | `../evo6/atlas_evo_guard_radiant.png`（1024×1024，426 塊）＋ `_emissive` | palette_base.json |
| 守夜者・柔光 `evo_guard_soft` | 44 | (22, 41) | 39 | 171 | `../evo6/atlas_evo_guard_soft.png`（1024×1024，426 塊）＋ `_emissive` | palette_base.json |
| 守夜者・微塵 `evo_guard_dust` | 44 | (22, 41) | 41 | 180 | `../evo6/atlas_evo_guard_dust.png`（1024×1024，444 塊）＋ `_emissive` | palette_dust.json |
<!-- EVO6B-END -->

<!-- LUMI-START -->
## 螢絨 lumi（隱藏稀有成年形態，round_s）
- atlas：`../atlas_lumi.png/.json`（1024×1024，290 塊，padding 2、extrude 1）＋ `../atlas_lumi_emissive.png`（同 layout，白＝發光）
- 64×64、pivot (32,61)、lumi 31 色（`../lumi/palette_lumi.json`）、alpha 0/255、向右。姿勢＝radiant 同名 clip（只換外觀層）。
- 五官：`<clip>_noface` ＋ kit（eyes_*/mouth_*，64px，眼高光 fly_core），錨點 `../lumi/face_anchors_lumi.json`（＝本檔 clips[].anchors.lumi）；bulb＝前觸角燈頭、另有 bulb2／tail。
- picked_up：pivot＝anchors.grab（同 radiant）。
- 共 24 clip／102 幀：std23 全套 23 clip（MVP 12 clip／46 幀）＋ picked_up。radiant 冇 grumpy clip（只係 face preset），所以冇出。

| clip | 幀 | fps | | 類 |
|---|---|---|---|---|
| idle | 4 | 6 | loop | MVP |
| blink | 4 | 10 | once | MVP |
| sway | 4 | 5 | once | std23 |
| yawn | 4 | 4 | once | std23 |
| emo_happy | 2 | 4 | once | MVP |
| emo_hungry | 2 | 3 | loop | MVP |
| emo_wantplay | 2 | 4 | loop | std23 |
| emo_sleepy | 2 | 2 | loop | MVP |
| emo_cuddly | 2 | 3 | loop | std23 |
| emo_surprised | 2 | 6 | once | std23 |
| walk | 6 | 10 | loop | MVP |
| play | 6 | 8 | once | MVP |
| fall_asleep | 4 | 3 | once | std23 |
| sleep_loop | 4 | 2 | loop | MVP |
| wake | 4 | 5 | once | std23 |
| sunbathe | 8 | 4 | loop | std23 |
| pot_bump | 8 | 8 | once | std23 |
| catch_reach | 6 | 8 | once | std23 |
| cheer_jump | 6 | 10 | once | std23 |
| droop | 6 | 4 | loop | MVP |
| eat | 4 | 8 | once | MVP |
| celebrate | 4 | 8 | once | MVP |
| sick | 2 | 3 | loop | MVP |
| picked_up | 6 | 8 | loop | 生命感（浮動） |

std23 餘下：冇（已齊）

<!-- LIVE-S3-START -->
## 生命感第三段（s3）— 遊美 2026-10-31

3 form（sprout 32×32 pivot (16,29)／radiant、soft 64×64 pivot (32,61)）；atlas `liveliness/atlas_<form>_live_s3.png/json`（1024 寬、pad 2、extrude 1、pivotPx）；五官 kit 仍喺 `atlas_<form>_live`；錨點 `clips[].anchors[form]`＝`liveliness/face_anchors.json`。詳見 `liveliness/LIVE_S3_NOTES.md`。

| clip | 幀／fps | loop | 優先 | 觸發 | 備註 |
|---|---|---|---|---|---|
| nuzzle_purr | 4／6fps | 循環 | 4 | nuzzle 連續 ≥1.2s（長按未放）→ 由 nuzzle 當前幀切去 nuzzle_purr 循環，直至放手 | 挨住右邊手指、合眼笑（eyes happy＋ω 口），身體細細震（sx/sy 交替＋shear 1px），背後呼嚕震線 ( ( 烙入幀（第 1/3 幀近、第 2/4 幀遠），第 2–4 幀頭頂右邊細心心升起（烙入幀）；放手播完當前幀 → idle（或 act_cool 30%：扮冇事）。可配 6fps 呼嚕 loop 音效。 |
| reunion_happy | 5／8fps | 單次 | 6 | rush（煞停）→ 衝過頭 → act_cool → reunion_happy（D5 久別重逢鏈最後一步） | 蠢蠢地但覺得自己好醒：第 1 幀扮冷靜側眼回望（ft 向後、gaze L）、第 2 幀破功（壓扁、驚喜眼）、第 3 幀彈起舉手（細心心）、第 4 幀最高點大心心 pop＋閃光、第 5 幀落地得意 ω 臉（細心心飄高）。引擎：播之前按玩家位置設 scaleX（衝過頭即係玩家喺後面 → 鏡像），第 1 幀先『望返轉頭』。心心烙入幀。 |
<!-- LIVE-S3-END -->
