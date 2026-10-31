# 螢絨 (lumi) — idle 概念草圖（Kurt 已批：「翼移去背後先開動畫」）

> 2026-10-31 13:00 HKT：翼已由頭頂移去背後；動畫已出（見 `../lumi/`、`../atlas_lumi.*`）。Python Pillow／numpy 程式逐像素繪製，**無 AI**，原創設計。
> 腳本：`art-pet/tools/build_lumi_concept.py`（可重跑；import `build_tuanrong.py` 嘅 Cv／眼口模板）。

## 檔案
| 檔 | 說明 |
|---|---|
| `lumi_idle_64.png` | 64×64 RGBA，alpha 0/255，無 AA，向右；pivot (32,61) |
| `lumi_idle_emissive_64.png` | 64×64，白＝發光像素（fly／fly_core：尾燈、觸角燈頭、身上光點），俾 H4 夜景 glow |
| `lumi_concept_8x.png` | 8x 並排：燦光 idle｜柔光 idle｜螢絨 idle｜螢絨喺 H4 夜景（crop，按 FORMAT.md 公式簡化合成＋emissive glow） |
| `palette_lumi.json` | lumi 用 31 色色盤（index→hex） |

## 骨架（round_s，同燦光／柔光）
- 身 ellipse rx 19、ry 16（＝燦光），腳底 y 60、pivot (32,61)；腳、手、眼、口、腮紅位置同模板一樣 → 現有 face rig／clip 骨架可直接套。
- 唯一骨架外差異：面整體右移 2px（向右睇），尾燈喺左後下（身後）。

## 設計重點（一眼分得出）
| | 燦光 | 柔光 | **螢絨** |
|---|---|---|---|
| 毛色 | 奶油黃 | 蜜桃橘 | **夜藍紫**（冷色，唯一冷色成年形態） |
| 頭頂 | 蒲公英光芒燈泡 | 葉芽小燈 | **兩條觸角＋螢光綠燈頭**（冇芽莖） |
| 輪廓 | 圓團 | 大圓團 | 圓團＋**左後下突出嘅螢火尾燈**＋**背後（中／下背）一對淺藍小翼，喺身體後面、左邊露出輪廓外一截**（唔再似帽） |
| 光色 | 暖黃 | 暖黃 | **螢光黃綠**（呼應 H4 firefly 粒子 #e4ff8c） |
- 身上 8 粒小光點（plus 形／單點），集中背同後半，越近尾越密。
- 眼睛高光用 fly_core（淡螢光），夜晚會帶少少綠閃。
- 腳保留橙色＝物種識別（同其他形態一致）。

## 色盤（仍然 31 色）
共用 `palette.json` 31 色，**換 6 個 lumi 用唔著嘅槽**（同 index，atlas_lumi 用自己色盤）：
| idx | 原 | → lumi | hex | 原用途 |
|---|---|---|---|---|
| 7 | peach0 | lumi_fur0 | #A99FD8 | 柔光專用 |
| 8 | peach1 | lumi_fur1 | #C6BDEA | 柔光專用 |
| 9 | peach2 | lumi_fur2 | #E2DCF6 | 柔光專用 |
| 17 | egg_shade | fly | #CFF26A | 光卵專用 |
| 18 | egg_dark | fly_d | #8FCB4E | 光卵專用 |
| 27 | cyan | fly_core | #F2FFB8 | 未用 |
- 毛色 ramp（暗→亮）：zzz #8F85C2 → lumi_fur0 → lumi_fur1 → lumi_fur2，高光 white #F3EEFA；翼 drop #7FC4E8＋white。
- 草圖實用 13 色；其餘槽（sick、berry、zzz、hearts 等）保留俾之後 clip 用。

## emissive
- 只標 fly、fly_core（亮兩級）；fly_d（尾燈外圈）唔發光，保留形狀。
- H4 預覽：發光像素唔食 petTint×ambientTint；glow＝emissive Gaussian σ3 × #cff26a ×1.4 ＋ σ1 × #f2ffb8 ×0.35（lighter）。遊程可用同一遮罩做呼吸閃爍。

## 翼（v2，13:00）
- 兩塊旋轉橢圓（drop＋white 內光＋drop_d 翼脈），畫喺身體之前（＝身後），錨喺靜止身寬 rx 19：下翼 (cx−0.78rx, cy−0.10ry) 166°、上翼 (cx−0.58rx, cy−0.36ry) 142°；fluff 參數帶 ±7° 輕拍。
- renderer 已改成 parametric `render_lumi(p)`（同 render_pet 參數），概念圖＝`render_lumi({})`。

## 狀態
- ✅ MVP 12 clip／46 幀＋picked_up、fall_asleep、wake（共 15 clip／60 幀）→ `../atlas_lumi.png/.json`＋`../atlas_lumi_emissive.png`；散檔 `../lumi/`；build `tools/build_lumi.py`、驗證 `tools/validate_lumi.py`。
- ⏳ std23 餘下：sway、yawn、emo_wantplay、emo_cuddly、emo_surprised、cheer_jump、catch_reach、sunbathe、pot_bump。
