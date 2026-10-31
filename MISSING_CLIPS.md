# 生命感第二段 — 缺 clip 清單（遊程 2026-10-31 14:3x HKT）

對照來源：
- `code/glimmer-combo` @ b4a5616 `src/glimmer-a/art/liveliness/`（atlas_<form>_live＋CLIPS.json＋face_anchors.json）
- `art/glimmer-hd2d-live` @ ec22d5a：**冇** liveliness clip（只有 HD-2D 場景、base atlas、rim），所以唔係來源
- `art/glimmer-pickup` @ e173e2b／`art/glimmer-lumi` @ c0abfbe：liveliness 檔同 combo 一樣（多咗 picked_up／lumi，第二段用唔著）

## 已齊（3 form：sprout 32×32 pivot (16,29)／radiant 64×64 pivot (32,61)／soft 64×64 pivot (32,61)；noface＋faceov＋anchors＋rim_live 全有）
| clip | 幀／fps | 用途 |
|---|---|---|
| sniff | 4／6 | A2 嗅地 |
| lookup | 4／5 | A2 望天（舊 base atlas 冇，只得 live 版） |
| swat | 4／8 | A2 拍走蟲仔（第 3 幀出手） |
| scratch | 6／8 | B1 抓癢 |
| sneeze | 5／8 | B2 打噴嚏（第 3 幀乞嗤） |
| walk_happy | 6／10 | A3 開心蹦跳步 |
| walk_drag | 6／6 | A3 攰／肚餓拖步 |
音效（sfx_pet_scratch／sneeze／step_hop／step_drag／bug_pat a/b）combo 入面嘅檔同 audio/pet-plan-a @ 2bfce1b blob 完全一樣，唔使再抓；冇帶雨聲 v2.1。

## ✅ 已補（遊美 2026-10-31 live_s2，s2b 已接入引擎；遊美 validator ALL PASS）
來源：`/workspace/live-s2-art-staging.zip`（222 檔）→ repo `art-pet/`＋引擎 `src/glimmer-a/art/liveliness/`（`atlas_<form>_live_s2.{png,json}`、`fx/atlas_fx_live.{png,json}`、CLIPS.json／face_anchors.json 更新；舊 `atlas_<form>_live` 冇郁）。
| # | clip | 幀／fps | 狀態 | 引擎接法（s2b） |
|---|---|---|---|---|
| 1 | `smug_pose` | 4／6＋holdLast 0.8s | **已補** | 拍蟲撲空 → smug_pose，尾幀 hold 0.8s；face preset `smug`（eyes sleepy／gaze C／mouth squint ω）；頭頂閃已烙入幀（唔再加程序化 spark） |
| 2 | `act_cool` | 4／5 | **已補** | 噴嚏後／getup 後扮冷靜 |
| 3 | `lookup_tip` | 4／6 | **已補** | 望天 → lookup_tip（冇程序化後仰） |
| 4 | `getup` | 4／6 | **已補** | lookup_tip → getup → act_cool |
| 5 | fx `fx_bug`（8×8，3 幀，pivot (4,4)，01→02→03→02 @10fps） | 3／10 | **已補** | 取代程序化 2×2 點；飛走跟方向 flip |
| 6 | `sniff_itch` | 2／6 | **已補** | sniff 第 3 幀 → sniff_itch → sneeze_01 |
未 ready（?live=0／dust）時以上全部自動退返舊 fallback（見下表），行為一樣。

### 舊 fallback（保留作退路）
| # | 建議 clip 名 | 幀／fps | 用途（Kurt：「蠢蠢地但覺得自己好醒」） | fallback |
|---|---|---|---|---|
| 1 | `smug_pose` | 4／6，最後幀 hold 0.8s | 拍蟲撲空之後得意擺 pose（挺胸、合眼仰頭、ω 口） | `emo_happy` 身體 ×2 循環＋強制臉 eyes squint／mouth squint（ω）＋頭微轉＋小星火花 fx |
| 2 | `act_cool` | 4／5 | 嗅地打完噴嚏／望天跌低之後「扮冷靜」（別過頭、輕咳、拍拍身） | `sway` 身體＋強制臉 eyes squint gaze 望側（L）／mouth neutral |
| 3 | `lookup_tip` | 4／6 | 望天望到向後小小倒（坐低／後仰） | `lookup` 最後一幀＋程序化後仰（向後移 2px、壓扁 0.9、轉 −10°） |
| 4 | `getup` | 4／6 | 後仰之後起返身（撐起） | `wake` 身體＋強制臉 eyes surprised→neutral |
| 5 | fx `bug` | 2–3／10 | A2 拍走蟲仔嘅蟲仔（engine 飛近 head_r） | 程序化 2×2 黑點＋1px 翼閃（canvas 畫） |
| 6 | `sniff_itch` | 2／6 | 嗅到鼻癢嘅過渡幀 | 直接 sniff → sneeze 接駁 |

## 生命感第三段（s3：D3 磨蹭／D5 久別重逢／G1 燈泡）— 轉遊美
已有（直接用）：`nuzzle`（6／6fps loop，frame 1 起 head_r 心心）、`rush`（6／12fps，loopRange [1,4]，速度線＋塵已畫入幀，next cheer_jump）—— sprout／radiant／soft 三個 live atlas＋face_anchors 齊；`bulb_base`＋灰階 `bulb_glow` 三 form 齊（5 心情 tint 用 face.bulb.moods）。音效 sfx_pet_nuzzle_purr_a/b、sfx_pet_reunion_happy_a/b 齊。

| # | 缺 clip | 用途 | 而家 fallback |
|---|---|---|---|
| 1 | `nuzzle_purr` | 磨蹭 ≥1.2s 後嘅呼嚕（合眼、輕震） | `nuzzle` 身體繼續 loop＋強制臉 ['happy','C','happy']（合眼笑）＋purr 聲（每圈一次 a/b 交替） |
| 2 | `reunion_happy` | 衝埋嚟煞停扮冷靜之後嘅開心重逢 | `cheer_jump` ×2 跳（hopH 0.6）＋心心 burst＋reunion_happy 聲 |
| 3 | dust form live atlas（舊限制） | 微塵 form 嘅 nuzzle／rush | idle＋程序化變形；螢絨（lumi）借柔光 |

## 其他備註
- 微塵（dust）form 冇 live atlas，第二段全部新 clip 照舊用 idle＋程序化變形 placeholder（同第一段一樣）。螢絨（lumi）借柔光 clip。dust／lumi／rim_live 仲未有 s2 版本 → 繼續 fallback（rim 退 rimFallback）。
- **步佐幀（遊美 s2 量度，已改）**：walk_happy 落地＝索引 0、3（2、5 係最高點）→ step_hop；walk_drag 拖地起塵＋拖地聲（step_drag）＝索引 1、4，踏地聲（新 cue step_plod）＝索引 2、5。step_plod 暫時借 sfx_pet_step_hop a/b（gain 0.5、rate 0.82），待遊音出專屬檔。
- lookup 舊 data.js 定義 2 幀 2fps（extra placeholder）；第二段改跟遊美 CLIPS.json：4 幀 5fps（live）。流星夜事件照用。
