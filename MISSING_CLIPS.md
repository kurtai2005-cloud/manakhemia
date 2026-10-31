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

## 缺（按現有尺寸；請遊美出 noface＋faceov＋full＋anchors，3 form）
| # | 建議 clip 名 | 幀／fps | 用途（Kurt：「蠢蠢地但覺得自己好醒」） | 而家 fallback |
|---|---|---|---|---|
| 1 | `smug_pose` | 4／6，最後幀 hold 0.8s | 拍蟲撲空之後得意擺 pose（挺胸、合眼仰頭、ω 口） | `emo_happy` 身體 ×2 循環＋強制臉 eyes squint／mouth squint（ω）＋頭微轉＋小星火花 fx |
| 2 | `act_cool` | 4／5 | 嗅地打完噴嚏／望天跌低之後「扮冷靜」（別過頭、輕咳、拍拍身） | `sway` 身體＋強制臉 eyes squint gaze 望側（L）／mouth neutral |
| 3 | `lookup_tip` | 4／6 | 望天望到向後小小倒（坐低／後仰） | `lookup` 最後一幀＋程序化後仰（向後移 2px、壓扁 0.9、轉 −10°） |
| 4 | `getup` | 4／6 | 後仰之後起返身（撐起） | `wake` 身體＋強制臉 eyes surprised→neutral |
| 5 | fx `bug`（8×8，2–3 幀拍翼） | 2–3／10 | A2 拍走蟲仔嘅蟲仔（engine 飛近 head_r） | 程序化 2×2 黑點＋1px 翼閃（canvas 畫） |
| 6 | （可選）`sniff_itch` | 2／6 | 嗅到鼻癢嘅過渡幀（sniff→sneeze 之間） | 直接 sniff → sneeze 接駁 |

## 其他備註
- 微塵（dust）form 冇 live atlas，第二段全部新 clip 照舊用 idle＋程序化變形 placeholder（同第一段一樣）。螢絨（lumi）借柔光 clip。
- walk_happy 落地幀／walk_drag 落腳幀未有標註；程式暫定 walk_happy 索引 2、5 落地（每循環 2 跳）、walk_drag 索引 1、4 落腳（第 2／5 幀起塵），請遊美確認。
- lookup 舊 data.js 定義 2 幀 2fps（extra placeholder）；第二段改跟遊美 CLIPS.json：4 幀 5fps（live）。流星夜事件照用。
