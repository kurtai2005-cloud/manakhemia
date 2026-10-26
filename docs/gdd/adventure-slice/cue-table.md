# 演出 cue 表：換棒／技能／衝線／入場／結算

> 遊策｜週 1｜草稿 v1｜全原創｜給：遊音（核對 `windrun-audio/README.md` 暫定 cue 對應）、遊美（特效／鏡頭）、遊程（觸發點）、遊測（逐 cue 驗證）
> 音效 id 已按 `/workspace/遊音-staging/windrun-audio/README.md`（現有 24 個 SFX＋3 條 BGM）核對；**★＝現時未有、建議新增**（含優先級）。時間以「cue 起點＝0」計。
> M1＝範圍內必做；M2／M3＝已預留 id 但唔做。鏡頭規則沿用計劃 ①：預設跟拍現役；M3 才加換棒微拉遠／慢鏡。
> 全部特效「用光色表達、唔靠文字」；「減少動態」設定開啟時，關閉震屏／慢鏡／粒子密度減半（遊程實作旗標 `fx_reduced`）。

## 0. 規則與優先級

1. 同一幀多個 cue：優先級 **結算 > 衝線 > 技能 > 換棒 > 地形／UI**；低優先級音效若與高優先級重疊，音量壓 −3 dB（由遊音混音策略處理）。
2. 賽中 BGM：`bgm_race_loop`（128 BPM，小節 1.875 s）；進入末段（最後 100 m）喺**下一條小節線**以 0.3 s 等功率 crossfade 切 `bgm_race_final_loop`（做法見 windrun-audio README §3）。
3. 比賽模擬同表現分離：cue 由模擬事件（`event.type`）驅動，表現層可丟棄／延遲 cue，但**不得改變模擬結果**（同一種子重播一致）。

## 1. 入場（賽前，A 層／6.4a；非賽中模擬）

| id | 觸發條件 | 鏡頭 | 特效 | 音效 id | 時長 | M |
|---|---|---|---|---|---|---|
| `cue_reg_open` | 同報名處 NPC 互動、報名介面打開 | 固定（對話鏡頭，桑姨居中） | 木枱／紙張小動畫 | `sfx_register_open` | ≈1.0 s | M1 |
| `cue_reg_menu_move` | 報名介面移動選項游標 | — | 游標高亮 | `sfx_menu_move` | — | M1 |
| `cue_reg_ok` | `register_match` 成功 | 同上 | 蓋章閃光；葉幣數字扣減 | `sfx_register_confirm`；扣費後延遲 ≈0.3 s 不播幣聲 | ≈1.3 s | M1 |
| `cue_reg_denied` | 資格／葉幣不足 | 不變 | 介面輕抖 4 px | `sfx_register_denied` | 0.67 s | M1 |
| `cue_entry_tunnel` | `ev_gate_entry`（已報名，見 maps-and-events.md；同一張賽場地圖，唔切場景） | 跟拍玩家行過入場通道 (14–20,7–9)；可點擊跳過 | 閘口向兩側打開，通道燈帶逐盞亮起 | `sfx_interact_door`（閘口）；腳步 `sfx_step_wood_floor_*` | 閘口 0.6 s＋行路 ≈4 s | M1 |
| `cue_fast_entry` | `ev_fast_entry`（按「快速入場」） | 黑幕 0.3 s → 直切起跑區 (31,7) | 風掃過渡 | `sfx_zone_enter`（由黑幕開始觸發） | ≤1.2 s | M1 |
| `cue_team_intro` | `ev_stand_intro`（每場首次進入看台區，可跳過） | 先 pan 對手隊（1.5 s），再 pan 玩家隊（1.5 s），≤5 s | 隊名條由兩側滑入；頭像逐一亮起 | ★`stinger_entry`（入場 stinger，約 3 s；P1） | ≤5 s | M1 |
| `cue_formation_open` | `ev_formation` 佈陣介面打開 | UI 疊層，場景 BGM 低通 | 首發格高亮 | `sfx_dialog_open`（借用，P3 想要專用可★） | — | M1 |
| `cue_start_line` | `ev_start_line`（玩家站上起跑線，已佈陣） | 拉遠至全景（0.6 s） | 起跑線發光；NPC 看台揮手 | `sfx_interact_confirm` | 0.6 s | M1 |
| `cue_countdown` | 起跑線確認後倒數 3-2-1 | 固定全景→貼地 | 大數字（光色）；GO 時閘門打開光柱 | ★`sfx_countdown_tick`（3、2、1 各一下，P1）；GO＝`sfx_countdown_go` | 3.0 s＋0.9 s | M1 |
| `cue_race_bgm_start` | GO 瞬間 | — | — | `bgm_race_loop` 第 0 樣本起播；城鎮 BGM 於 `cue_countdown` 開始時淡出 0.5 s（不做拍子對齊，兩者速度不同） | — | M1 |

## 2. 換棒（賽中，整段 ≤1.5 s）

換棒序列：按下換人 → 交棒者減速鞠躬（`swap_out`，約 0.5–1.4 s，依冷靜值，見參數 `swap_out_*`）→ 新人入場加速（`swap_in_time` 1.5 s，G 0.7→1.0）。cue 時間以按下換人為 0。

| id | 觸發條件 | 鏡頭 | 特效 | 音效 id | 時長 | M |
|---|---|---|---|---|---|---|
| `cue_swap_press` | 玩家按後備頭像（有效） | 不變 | 頭像按鈕縮放 0.9→1.0；冷卻環開始（4 s） | `sfx_menu_move`（小音量，輕觸感） | 0.1 s | M1 |
| `cue_swap_denied` | 冷卻中／被技能封鎖時按換人 | 不變 | 按鈕紅色輕抖 | `sfx_register_denied`（借用，音量 −6 dB）；P3★`sfx_swap_denied` | 0.3 s | M1 |
| `cue_swap_out` | `event: swap_out_start`（t=0） | 跟拍交棒者；速度降時鏡頭微追（lerp 0.12） | 交棒者鞠躬；光尾由亮減弱；地形腳步粒子減半；頭像縮到場邊 | `sfx_baton_out` | 0.55 s | M1 |
| `cue_swap_in` | `event: swap_in_start`（約 t=0.4 起，與 `swap_out` 重疊） | 於 0.3 s 內由交棒者平滑移到新人（ease-in-out），之後跟拍新人 | 新人頭像由場邊飛入（簡版：直線＋殘影）；入場加速光尾（由弱至強）；落地小塵／草屑（按地形） | `sfx_baton_in` | ≈1.1 s（總序列 ≤1.5 s） | M1 |
| `cue_swap_ready` | 冷卻結束 | 不變 | 頭像按鈕一次脈衝發光（光色＝野靈主色） | 無（純視覺，避免音效疲勞） | 0.4 s | M1 |
| `cue_swap_zoom` | 同上（M3） | 微拉遠 5%，保持兩人入鏡 | — | — | 0.5 s | M3 |

換棒光色語言：交棒＝暖黃光尾淡出；入場＝該野靈主色光尾增強；不用文字（遊美統一在 M3 完整版）。

## 3. 技能（M1 只做疾風衝／絆草；回氣／風罩 M2 但 id 預留）

技能序列：蓄力 0.3 s → 爆發（同一幀）→ 持續狀態光環（疾風衝 3 s、絆草 3 s、風罩 5 s；回氣即時）→ 結束。

| id | 觸發條件 | 鏡頭 | 特效 | 音效 id | 時長 | M |
|---|---|---|---|---|---|---|
| `cue_skill_press` | 玩家按技能鍵（有效） | 不變 | 技能鍵變灰（每場一次）；現役野靈身上聚光 | `sfx_menu_move`（輕） | 0.1 s | M1 |
| `cue_skill_charge` | `event: skill_charge_start`（t=0） | 跟拍；輕微 zoom-in 3%（0.3 s） | 野靈蓄力：身周光點向內收；地面風紋 | `sfx_skill_charge` | 0.3 s（精確） | M1 |
| `cue_skill_boost` | t=0.3：疾風衝 爆發 | 跟拍；短速度線（鏡頭 FOV 不變，後處理徑向模糊 0.3 s） | 衝擊環＋風掃；持續光環＝金白速度殘影（3 s） | `sfx_skill_burst_gale` | 1.15 s（光環 3 s） | M1 |
| `cue_skill_trip` | t=0.3：絆草命中對手 | **切入被絆者 0.4 s 小特寫，再回跟拍**（若玩家方放技）；對手放技則維持跟拍 | 草叢由地面纏上被絆者；被絆者短暫綠色減速光圈（3 s）；2 下絆倒屈身 | `sfx_skill_trip_grass` | 0.64 s（光圈 3 s） | M1 |
| `cue_skill_recover` | t=0.3：回氣 | 跟拍 | 暖色光點上升；耐力條回彈動畫 +20 | `sfx_skill_recover` | 1.3 s | M2 |
| `cue_skill_shield_up` | t=0.3：風罩 | 跟拍 | 旋風罩（半透明）5 s；邊緣微亮 | `sfx_skill_wind_shield` | 1.45 s（光環 5 s） | M2 |
| `cue_skill_shield_block` | 風罩期間被技能指向（免疫） | 短切被指向者 0.3 s | 罩面漣漪；來技能光彈碎裂 | `sfx_hit_stop_impact`（借用）；P3★`sfx_shield_block` | 0.3 s | M2 |
| `cue_skill_hit_stop` | 技能命中 | 全畫面凍結 2–4 幀（60 fps）；`fx_reduced` 時關 | 白閃一幀；輕震動（可關） | `sfx_hit_stop_impact` | 3 幀 | M2 |
| `cue_skill_end` | 持續狀態結束 | — | 光環淡出 0.3 s | 無 | 0.3 s | M1 |
| `cue_skill_unavail` | 交棒／入場期間嘗試放技 | 不變 | 技能鍵灰＋抖 | `sfx_register_denied`（借用，−6 dB） | 0.3 s | M1 |

## 4. 賽中提示（地形段界、耐力、末段）

| id | 觸發條件 | 鏡頭 | 特效 | 音效 id | 時長 | M |
|---|---|---|---|---|---|---|
| `cue_seg_change` | 現役野靈跨越段界（每 200 m） | 不變 | 賽道條下一段高亮閃一次；地形粒子換型 | 腳步循環切換：`sfx_step_moss`／`sfx_step_gravel`／`sfx_step_shallow_water`（M2 加霜面／懸橋） | 0.5 s | M1 |
| `cue_step` | 按步頻（跟速度） | — | 腳印粒子 | 對應地形腳步 sfx，playbackRate ±5%（遊音建議） | 循環 | M1 |
| `cue_stamina_low` | 現役耐力 ≤30% | 不變 | 耐力條轉橙＋脈動；野靈喘氣小動畫 | ★`sfx_stamina_warn`（P2，柔和低頻心跳式 1 下，每次跨越只播一次） | 0.4 s | M1 |
| `cue_stamina_empty` | 耐力 ≤10%／耗盡 | 不變 | 條轉紅；野靈步伐沉重（動畫減速 20%）；螢幕邊緣輕暗角 | ★`sfx_stamina_empty`（P2） | 0.5 s | M1 |
| `cue_final_100` | 任一方領先者距終點 ≤100 m（取首次觸發） | 跟拍；鏡頭 zoom-in 5%（0.5 s） | 賽道條末段金邊；觀眾旗幟加速揮動 | BGM 於下一小節線 crossfade 至 `bgm_race_final_loop`（0.3 s 等功率） | — | M1 |

## 5. 衝線

| id | 觸發條件 | 鏡頭 | 特效 | 音效 id | 時長 | M |
|---|---|---|---|---|---|---|
| `cue_finish` | `event: finish`（領先者越線，**越線一幀即響**） | 切衝線特寫：低機位側拍，領先者衝入畫面中央（0.8 s）；落後者仍在後方入鏡 | 布帶斷開、彩葉紙屑噴發；白閃一幀 | `sfx_finish_line`（BGM 淡出 ≥0.3 s） | 1.8 s | M1 |
| `cue_finish_close` | 衝線時兩隊差距 <3 m（M3） | 慢鏡 0.8 s（模擬時間不變，只放慢表現） | 暈影 | 同上；BGM 同時降低 | 0.8 s | M3 |
| `cue_finish_other` | 落後者越線 | 回全景，不特寫 | 小紙屑 | 無 | 1.0 s | M1 |
| `cue_finish_hold` | 衝線後 0.8 s | 全景定格兩隊位置，顯示「勝／敗」標示（光色） | 勝方光柱／敗方柔光 | `sfx_stinger_win` 或 `sfx_stinger_lose`（**建議喺 `sfx_finish_line` 後 ≥1.0 s 起，finish_line 尾巴自然淡出**；stinger 期間 BGM 已淡出） | 2.8–3.0 s | M1 |

## 6. 結算（6.4a⑦／1.6）

結算面板序列（總長目標 ≤12 s，可按「跳過」直達面板最終狀態）：

| id | 觸發條件 | 鏡頭 | 特效 | 音效 id | 時長 | M |
|---|---|---|---|---|---|---|
| `cue_result_panel` | `cue_finish_hold` 之後 | 場景模糊（景深）＋面板滑入 | 勝／敗標題：勝＝暖金光、敗＝柔藍光（鼓勵語氣） | （stinger 已播） | 0.5 s | M1 |
| `cue_result_margin` | 面板顯示 | — | 差距數字滾動（`margin_m`，例：+12.5 m） | `sfx_dialog_next`（輕） | 0.8 s | M1 |
| `cue_reward_leaf` | 獎金數字滾動 | — | 葉幣圖示跳動、總葉幣加算 | `sfx_leafcoin_get`（面板出現後 +0.3 s） | 0.6 s | M1 |
| `cue_exp_bar` | 每隻出場野靈經驗條逐隻增加 | — | 經驗條填滿動畫；每隻間隔 0.4 s | ★`sfx_exp_tick`（P3，短 tick，可重複；暫用 `sfx_menu_move`） | 每隻 0.6 s | M1 |
| `cue_levelup` | 野靈升級 | 面板上小特寫 | 金色環＋能力值 +N 逐項跳出 | ★`jingle_levelup`（P2，約 1.2 s） | 1.2 s | M1 |
| `cue_capture_bond` | 結緣戰勝出（`capture`） | 切野靈特寫：野靈走近、與主角互動 | 葉光環繞、結緣光圈；命名視窗 | ★`jingle_capture`（P1，約 2 s）；M1 暫用 `sfx_item_get` | 2.0 s | M1 |
| `cue_seal_get` | 冠軍賽勝出（風印） | 風印升起、旋轉 1 圈 | 風印光柱（金綠） | ★`jingle_seal`（P2，≈3 s） | 3 s | M2 |
| `cue_unlock_hint` | 新場次／新區域解鎖 | UI 提示 | 地圖圖示閃動 | `sfx_item_get` | 0.9 s | M2 |
| `cue_return_town` | 經 `door_town` 離開賽場（或結算面板「回城」捷徑） | 黑幕 0.3 s | 風掃過渡 | `sfx_zone_enter`；城鎮 BGM `bgm_town_morningmoss_loop` 於黑幕後淡入（0.5–1.0 s） | 0.9 s | M1 |

## 7. 一場完整賽事的時間線（驗收用）

| 時間 | cue |
|---|---|
| 報名 → 進場 | `cue_reg_open` → `cue_reg_ok` → `cue_entry_tunnel`（或 `cue_fast_entry`） |
| 看台 | `cue_team_intro` → `cue_formation_open` → `cue_start_line` |
| 起跑 | `cue_countdown` → `cue_race_bgm_start` |
| 賽中（約 60–120 s） | `cue_step`／`cue_seg_change` 循環；玩家操作 `cue_swap_*`、`cue_skill_*`；`cue_stamina_*` 視情況 |
| 末段 | `cue_final_100`（BGM 切換）→ `cue_finish` → `cue_finish_hold` |
| 結算 | `cue_result_panel` → `cue_result_margin` → `cue_reward_leaf` → `cue_exp_bar` → `cue_levelup`／`cue_capture_bond`（如有）→ `cue_return_town` |

## 8. ★ 建議新增音效清單（給遊音，已按優先級）

| 優先 | id | 用途 | 長度建議 | 備註 |
|---|---|---|---|---|
| P1 | `stinger_entry` | 隊伍介紹（`cue_team_intro`） | ≈3 s | 計劃 6.9a 已列「入場 stinger」，M1 必須 |
| P1 | `sfx_countdown_tick` | 倒數 3-2-1 | ≤0.2 s | `sfx_countdown_go` 已有 |
| P1 | `jingle_capture` | 結緣成功（M1 驗收 ④） | ≈2 s | M1 暫用 `sfx_item_get` |
| P2 | `jingle_levelup` | 升級 | ≈1.2 s | |
| P2 | `sfx_stamina_warn`、`sfx_stamina_empty` | 耐力提示 | ≤0.5 s | 柔和，唔刺耳 |
| P2 | `amb_wind_title` | 序章／標題風聲 ambience | 循環 ≥15 s | 見 prologue-script.md P0 |
| P3 | `sfx_exp_tick`、`sfx_swap_denied`、`sfx_shield_block`、`jingle_seal` | 結算細節／M2 | — | M2 前處理 |

## 9. 給遊測嘅檢查清單

1. 逐 cue 觸發一次：id 存在、音效檔存在、無 404／靜音。
2. 換棒總序列 ≤1.5 s；`cue_skill_charge` 長度 = 0.3 s（與模擬 `skill_charge` 同步，誤差 ≤1 幀）。
3. `cue_finish` 同 `sfx_finish_line` 起音差 ≤1 幀（windrun-audio 已量度起音 ≤1.2 ms）。
4. BGM 切換落小節線（量度 `T − 0.3 s` 起排程）；切換前後無 click。
5. `fx_reduced` 開啟：無震屏／慢鏡，粒子密度減半，音效保持。
6. 同一種子重播：cue 序列（id＋時間戳）逐幀一致。
