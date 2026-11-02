# 6a 團絨記得你 — 表情疊層（得意／委屈）

純 Pillow／numpy 程序繪製（冇 AI 圖）。重跑：`python3 art-pet/tools/build_breakthrough_6a_faces.py`
沿用 3a `reactions_lib` 嘅 rig（眼 blob、嘴錨點、clean 底、腮紅 keep），所以同 3a faces 同一套對位。

## 檔案
| 檔 | 內容 |
|---|---|
| `face_smug.png`／`face_smug@3x.png` | 得意，預設形態 `evo_still_radiant`（48×48，3x＝144×144 最近鄰） |
| `face_pout.png`／`face_pout@3x.png` | 委屈，預設形態同上 |
| `per_pet/<pet>/face_{smug,pout}{,@3x}.png` | 49 隻逐隻版（25 舊團絨 evo＋24 新蛋線 A1–H3），命名同 3a `reactions/faces/<pet>_*` 一樣按 pet id 分 |
| `faces6a.json` | 每隻 frameSize、pivot、錨點、檔案路徑、patch 色數 |
| `preview_faces_3x.png` | 12 隻真形態：原面｜得意｜委屈（左 3 欄 3x 全身，右 3 欄面部近鏡 8x） |

## 對位（重要）
- **全幀 patch**：每張同該形態 idle 幀 0 一樣大（evo_still 48×48、guard 44、hop 38、sprout 32、radiant/soft/lumi 64、A1–H3 48），左上角對齊 base 幀左上，**pivot 唔使另計**（48 款＝(24,45)）。
- 疊法同 3a：base＝idle 幀 0 → face patch → wear（眼鏡／帽）→ body transform。即係 patch 要喺 transform 之前蓋。
- 只得同 base 唔同嘅像素（alpha 255）；眼／嘴原位用該形態皮色補返，所以**每隻要用自己嗰張**；預設 `face_*.png` 只啱 `evo_still_radiant`。
- 汗滴（委屈）同 ✦（得意）會畫出身外，但唔出 frame。
- alpha 只得 0／255；每張 patch ≤10 色；光源左上。

## 用法
| key | 樣 | 幾時用 |
|---|---|---|
| `smug` 得意 | 半眼（外眼角翹 1px、留一粒光）＋歪咀笑＋腮紅＋右上 ✦ | 幾日唔見之後第一下撚（比平時開心多啲嗰下）；建議 1200–1800ms 後返 idle |
| `pout` 委屈 | 淚光眼（眼底淺藍＋多粒白光）＋擔心眉＋︵扁嘴＋右邊鼓腮＋眼角淚珠＋頭右上汗滴 | 3 日（或以上）唔見，開 game 第一眼／講「我以為你搬咗屋。」時；撚一下就轉 `smug` |

- 3a 已經有一個 `smug`（扮醒）喺 `reactions/faces`；6a 呢個係另一張，引擎 key 建議叫 `smug6a`／`pout6a` 免撞名。
- 唔需要新 FX；如果要加淚滴下滑，可以用 3a `fx_tear`。
