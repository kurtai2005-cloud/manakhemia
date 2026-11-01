# 團絨飾品 runtime vs baked 對照（13 件 × 25 形態）

由 `tools/build_accessory_runtime.py run_compare` 生成；數據：`RUNTIME_COMPARE.json`。

- 準則：acceptable＝重心距離 ≤2px、面積比 0.6–1.67、IoU ≥0.45
- pixelDiff%＝（runtime ∪ baked 嘅 alpha 像素入面，顏色唔同嘅比例）。runtime 係用 label-map 即場 render，高光／陰影位同手調 baked 唔會逐粒一樣，所以呢個數一般 15–40%；**判斷合格睇 okPct／IoU，唔睇 pixelDiff**。
- visAgree＝成個 clip 「畫／收起」決定同 baked 一致嘅比例。

**總計：59449/59628 幀合格（99.70%）；clip 可見性一致 13689/13715（99.81%）**

| 件 | clips | 可見性一致 | 幀 | 合格幀 | ok% | mean pixelDiff% | mean IoU | 問題幀 | 可見性唔同 |
|---|---|---|---|---|---|---|---|---|---|
| straw | 1055 | 1055 (100.0%) | 4524 | 4524 | 100.0 | 29.47 | 0.944 | 0 | 0 |
| bow | 1055 | 1050 (99.53%) | 4644 | 4638 | 99.87 | 18.68 | 0.924 | 6 | 5 |
| scarf | 1055 | 1055 (100.0%) | 4674 | 4650 | 99.49 | 0.39 | 0.998 | 24 | 0 |
| beanie | 1055 | 1055 (100.0%) | 4524 | 4524 | 100.0 | 28.37 | 0.966 | 0 | 0 |
| acorn | 1055 | 1055 (100.0%) | 4524 | 4524 | 100.0 | 22.22 | 0.962 | 0 | 0 |
| crown | 1055 | 1055 (100.0%) | 4524 | 4524 | 100.0 | 16.63 | 0.942 | 0 | 0 |
| starclip | 1055 | 1055 (100.0%) | 4674 | 4674 | 100.0 | 25.90 | 0.902 | 0 | 0 |
| sakura | 1055 | 1055 (100.0%) | 4674 | 4674 | 100.0 | 20.69 | 0.904 | 0 | 0 |
| glasses | 1055 | 1034 (98.01%) | 4320 | 4190 | 96.99 | 10.98 | 0.893 | 130 | 21 |
| leafcollar | 1055 | 1055 (100.0%) | 4674 | 4674 | 100.0 | 0.36 | 0.998 | 0 | 0 |
| bell | 1055 | 1055 (100.0%) | 4674 | 4674 | 100.0 | 1.46 | 0.994 | 0 | 0 |
| halo | 1055 | 1055 (100.0%) | 4674 | 4670 | 99.91 | 5.21 | 0.968 | 4 | 0 |
| nightcap | 1055 | 1055 (100.0%) | 4524 | 4509 | 99.67 | 42.87 | 0.899 | 15 | 0 |

自動修正（formOverrides dx/dy）：0 個（冇需要：每個 item×form 都 ≥95% 或者偏移唔一致）

## 人手審閱結論

- **nightcap**：嚴重幀（cd≈7px，evo_dot wake／catch_reach／turn_back／lookup_tip／getup；evo_still_radiant sleep_loop 等）——baked atlas 個帽浮咗喺頭頂上 ~7px，runtime 跟 fit 頂點貼頭，**runtime 先啱**；列為 baked outlier，冇改 data。
- **scarf**：soft／radiant lookup_tip、evo_guard_moon sneeze——baked 用斜切 shear，runtime 用整數角旋轉，邊緣裁法唔同（cd 2.5–4.8px），睇落可接受。
- **glasses**：鏡片改用 lens ladder＋retry 之後 ~97%；21 個 clip runtime 收起（「鏡框會壓到眼」／「眼距太窄（側面）」），屬保守：寧願唔戴都唔壓眼。剩低問題幀多數係 wake／blink 閉眼幀 IoU 低（鏡片細咗 1 級），中心冇偏。
- **bow**：5 個 clip（play_05／rush_03 喺幾隻 evo 形態）runtime 判「會遮五官」收起——nearest 放大 L 款（17→19）比 baked 原生 size 大少少；接受（保守）。evo_still_radiant 一組 cd≈2.5px 情緒幀屬同一原因。
- **halo**：4 幀 1px 垂直差（光環梯級 round 邊界），可接受。

## 嚴重（cd>4）clip 清單

| 件 | 形態 | clips |
|---|---|---|
| scarf | soft | lookup_tip |
| scarf | evo_guard_moon | sneeze |
| nightcap | evo_dot | wake, catch_reach, turn_back, lookup_tip, getup |
| nightcap | evo_guard_radiant | getup |
| nightcap | evo_still_radiant | sleep_loop, wake, sniff, lookup_tip, getup, sniff_itch |
| nightcap | evo_still_ember | lookup_tip, getup |

## 問題幀（每件最多 40 行；全數見 JSON）

### bow

| 形態 | 幀 | IoU | cd | 面積比 | dxy |
|---|---|---|---|---|---|
| evo_still_radiant | emo_hungry_01 | 0.565 | 2.54 | 1.157 | [1.89, -1.7] |
| evo_still_radiant | emo_sleepy_01 | 0.565 | 2.54 | 1.157 | [1.89, -1.7] |
| evo_still_radiant | droop_02 | 0.565 | 2.54 | 1.157 | [1.89, -1.7] |
| evo_still_radiant | sick_01 | 0.565 | 2.54 | 1.157 | [1.89, -1.7] |
| evo_still_radiant | sick_02 | 0.565 | 2.54 | 1.157 | [1.89, -1.7] |
| evo_guard_crystal | play_01 | 0.538 | 2.77 | 1.212 | [2.07, -1.83] |

可見性唔同：

- evo_guard_lumi play：runtime=收（play_05: 會遮五官）／baked=畫（None）
- evo_still_radiant play：runtime=收（play_05: 會遮五官）／baked=畫（None）
- evo_still_crystal play：runtime=收（play_05: 會遮五官）／baked=畫（None）
- evo_still_ember play：runtime=收（play_05: 會遮五官）／baked=畫（None）
- evo_still_ember rush：runtime=收（rush_03: 會遮五官）／baked=畫（None）

### scarf

| 形態 | 幀 | IoU | cd | 面積比 | dxy |
|---|---|---|---|---|---|
| radiant | lookup_tip_02 | 0.868 | 3.08 | 0.868 | [2.68, 1.52] |
| radiant | lookup_tip_03 | 0.886 | 2.62 | 0.886 | [2.31, 1.24] |
| soft | lookup_tip_02 | 0.803 | 4.84 | 0.803 | [4.35, 2.13] |
| soft | lookup_tip_03 | 0.831 | 4.32 | 0.831 | [3.94, 1.75] |
| evo_still_shroom | lookup_tip_02 | 0.849 | 3.07 | 0.849 | [2.69, 1.47] |
| evo_guard_moon | yawn_02 | 0.835 | 2.78 | 0.835 | [2.39, 1.43] |
| evo_guard_moon | yawn_03 | 0.829 | 2.77 | 0.829 | [2.38, 1.41] |
| evo_guard_moon | emo_happy_02 | 0.868 | 2.15 | 0.868 | [1.87, 1.05] |
| evo_guard_moon | emo_wantplay_02 | 0.868 | 2.15 | 0.868 | [1.87, 1.05] |
| evo_guard_moon | emo_cuddly_01 | 0.877 | 2.19 | 0.877 | [1.91, 1.06] |
| evo_guard_moon | emo_surprised_02 | 0.839 | 2.71 | 0.839 | [2.38, 1.3] |
| evo_guard_moon | play_03 | 0.857 | 2.09 | 0.857 | [1.92, 0.84] |
| evo_guard_moon | wake_02 | 0.829 | 2.77 | 0.829 | [2.38, 1.41] |
| evo_guard_moon | wake_03 | 0.807 | 3.37 | 0.807 | [2.89, 1.73] |
| evo_guard_moon | catch_reach_02 | 0.798 | 3.43 | 0.798 | [2.92, 1.79] |
| evo_guard_moon | catch_reach_03 | 0.795 | 3.4 | 0.795 | [2.92, 1.75] |
| evo_guard_moon | swat_04 | 0.868 | 2.16 | 0.868 | [1.93, 0.96] |
| evo_guard_moon | sneeze_03 | 0.8 | 3.1 | 0.8 | [2.62, 1.66] |
| evo_guard_moon | sneeze_04 | 0.765 | 4.11 | 0.765 | [3.53, 2.12] |
| evo_guard_moon | rush_02 | 0.864 | 2.1 | 0.864 | [1.92, 0.85] |
| evo_guard_moon | rush_04 | 0.864 | 2.1 | 0.864 | [1.92, 0.85] |
| evo_guard_moon | act_cool_03 | 0.871 | 2.23 | 0.871 | [1.91, 1.15] |
| evo_guard_moon | getup_02 | 0.808 | 3.28 | 0.808 | [2.82, 1.67] |
| evo_guard_moon | getup_03 | 0.826 | 2.75 | 0.826 | [2.35, 1.43] |

### glasses

| 形態 | 幀 | IoU | cd | 面積比 | dxy |
|---|---|---|---|---|---|
| sprout | wake_01 | 0.403 | 0.9 | 1.02 | [-0.73, 0.53] |
| sprout | wake_02 | 0.293 | 0.98 | 0.98 | [0.29, 0.94] |
| sprout | wake_03 | 0.293 | 0.98 | 0.98 | [0.29, 0.94] |
| sprout | wake_04 | 0.293 | 0.98 | 0.98 | [0.29, 0.94] |
| sprout | lookup_tip_01 | 0.304 | 0.46 | 1.028 | [0.45, 0.1] |
| sprout | lookup_tip_03 | 0.389 | 0.83 | 1.027 | [0.71, -0.44] |
| sprout | lookup_tip_04 | 0.397 | 0.77 | 1.077 | [0.66, -0.39] |
| radiant | lookup_04 | 0.412 | 0.99 | 0.939 | [0.0, -0.99] |
| soft | lookup_04 | 0.412 | 0.99 | 0.939 | [0.0, -0.99] |
| evo_dot | walk_01 | 0.245 | 1.3 | 1.2 | [1.15, -0.61] |
| evo_dot | walk_02 | 0.38 | 0.53 | 1.156 | [0.5, -0.17] |
| evo_dot | walk_03 | 0.38 | 0.53 | 1.156 | [0.5, -0.17] |
| evo_dot | walk_04 | 0.245 | 1.3 | 1.2 | [1.15, -0.61] |
| evo_dot | walk_05 | 0.38 | 0.53 | 1.156 | [0.5, -0.17] |
| evo_dot | walk_06 | 0.38 | 0.53 | 1.156 | [0.5, -0.17] |
| evo_sprout | smug_pose_01 | 0.136 | 0.84 | 0.887 | [0.71, 0.46] |
| evo_sprout | smug_pose_02 | 0.124 | 0.44 | 0.852 | [0.13, 0.42] |
| evo_sprout | smug_pose_03 | 0.112 | 1.01 | 0.8 | [-0.08, 1.01] |
| evo_sprout | smug_pose_04 | 0.112 | 1.01 | 0.8 | [-0.08, 1.01] |
| evo_hop | lookup_04 | 0.184 | 1.1 | 0.837 | [0.0, -1.1] |
| evo_hop | scratch_01 | 0.447 | 0.84 | 1.115 | [-0.81, 0.24] |
| evo_hop | scratch_02 | 0.447 | 0.84 | 1.115 | [-0.81, 0.24] |
| evo_hop | scratch_03 | 0.447 | 0.84 | 1.115 | [-0.81, 0.24] |
| evo_hop | scratch_04 | 0.447 | 0.84 | 1.115 | [-0.81, 0.24] |
| evo_hop | scratch_05 | 0.447 | 0.84 | 1.115 | [-0.81, 0.24] |
| evo_hop | scratch_06 | 0.447 | 0.84 | 1.115 | [-0.81, 0.24] |
| evo_guard_lumi | eat_01 | 0.44 | 0.56 | 0.929 | [0.53, -0.19] |
| evo_guard_lumi | eat_02 | 0.44 | 0.56 | 0.929 | [0.53, -0.19] |
| evo_guard_lumi | eat_03 | 0.44 | 0.56 | 0.929 | [0.53, -0.19] |
| evo_guard_lumi | eat_04 | 0.44 | 0.56 | 0.929 | [0.53, -0.19] |
| evo_guard_radiant | eat_01 | 0.44 | 0.56 | 0.929 | [0.53, -0.19] |
| evo_guard_radiant | eat_02 | 0.44 | 0.56 | 0.929 | [0.53, -0.19] |
| evo_guard_radiant | eat_03 | 0.44 | 0.56 | 0.929 | [0.53, -0.19] |
| evo_guard_radiant | eat_04 | 0.44 | 0.56 | 0.929 | [0.53, -0.19] |
| evo_guard_radiant | scratch_01 | 0.403 | 1.28 | 1.077 | [-1.27, -0.19] |
| evo_guard_radiant | scratch_02 | 0.403 | 1.28 | 1.077 | [-1.27, -0.19] |
| evo_guard_radiant | scratch_04 | 0.403 | 1.28 | 1.077 | [-1.27, -0.19] |
| evo_guard_radiant | scratch_06 | 0.403 | 1.28 | 1.077 | [-1.27, -0.19] |
| evo_guard_soft | eat_01 | 0.444 | 0.5 | 0.926 | [0.41, -0.29] |
| evo_guard_soft | eat_02 | 0.444 | 0.5 | 0.926 | [0.41, -0.29] |
| … | 另外 90 幀 | | | | |

可見性唔同：

- sprout swat：runtime=收（swat_02: 鏡框會壓到眼）／baked=畫（None）
- sprout scratch：runtime=收（scratch_01: 眼距 8.5px 太窄（側面），戴唔落）／baked=畫（None）
- radiant swat：runtime=收（swat_01: 鏡框會壓到眼）／baked=畫（None）
- radiant lookup_tip：runtime=收（lookup_tip_01: 鏡框會壓到眼）／baked=畫（None）
- soft swat：runtime=收（swat_02: 鏡框會壓到眼）／baked=畫（None）
- soft lookup_tip：runtime=收（lookup_tip_01: 鏡框會壓到眼）／baked=畫（None）
- evo_hop swat：runtime=收（swat_02: 鏡框會壓到眼）／baked=畫（None）
- evo_guard_lumi act_cool：runtime=收（act_cool_01: 鏡框會壓到眼）／baked=畫（None）
- evo_guard_radiant act_cool：runtime=收（act_cool_01: 鏡框會壓到眼）／baked=畫（None）
- evo_guard_soft lookup_tip：runtime=收（lookup_tip_01: 鏡框會壓到眼）／baked=畫（None）
- evo_guard_dust act_cool：runtime=收（act_cool_01: 鏡框會壓到眼）／baked=畫（None）
- evo_guard_tide act_cool：runtime=收（act_cool_01: 鏡框會壓到眼）／baked=畫（None）
- evo_guard_tide reunion_happy：runtime=收（reunion_happy_02: 鏡框會壓到眼）／baked=畫（None）
- evo_guard_shroom act_cool：runtime=收（act_cool_01: 鏡框會壓到眼）／baked=畫（None）
- evo_guard_shroom reunion_happy：runtime=收（reunion_happy_02: 鏡框會壓到眼）／baked=畫（None）
- evo_guard_crystal act_cool：runtime=收（act_cool_01: 鏡框會壓到眼）／baked=畫（None）
- evo_guard_crystal reunion_happy：runtime=收（reunion_happy_02: 鏡框會壓到眼）／baked=畫（None）
- evo_guard_moon act_cool：runtime=收（act_cool_01: 鏡框會壓到眼）／baked=畫（None）
- evo_guard_moon reunion_happy：runtime=收（reunion_happy_02: 鏡框會壓到眼）／baked=畫（None）
- evo_guard_ember act_cool：runtime=收（act_cool_01: 鏡框會壓到眼）／baked=畫（None）
- evo_guard_ember reunion_happy：runtime=收（reunion_happy_02: 鏡框會壓到眼）／baked=畫（None）

### halo

| 形態 | 幀 | IoU | cd | 面積比 | dxy |
|---|---|---|---|---|---|
| evo_guard_soft | sneeze_02 | 0.357 | 1.0 | 1.0 | [0.0, 1.0] |
| evo_still_shroom | pot_bump_07 | 0.37 | 1.0 | 0.947 | [0.0, 1.0] |
| evo_still_shroom | swat_03 | 0.37 | 1.0 | 0.947 | [0.0, 1.0] |
| evo_still_crystal | lookup_tip_01 | 0.333 | 1.0 | 1.0 | [0.0, 1.0] |

### nightcap

| 形態 | 幀 | IoU | cd | 面積比 | dxy |
|---|---|---|---|---|---|
| evo_dot | wake_01 | 0.086 | 6.97 | 0.883 | [0.28, 6.96] |
| evo_dot | catch_reach_05 | 0.064 | 7.24 | 0.908 | [-0.04, 7.24] |
| evo_dot | turn_back_02 | 0.033 | 7.49 | 0.952 | [0.03, 7.49] |
| evo_dot | lookup_tip_04 | 0.043 | 7.65 | 0.921 | [-0.06, 7.65] |
| evo_dot | getup_01 | 0.049 | 7.58 | 0.921 | [0.31, 7.57] |
| evo_guard_radiant | getup_01 | 0.188 | 7.62 | 0.979 | [0.08, 7.62] |
| evo_still_radiant | sleep_loop_01 | 0.21 | 8.13 | 1.105 | [1.43, 8.0] |
| evo_still_radiant | wake_01 | 0.202 | 8.85 | 1.191 | [1.18, 8.77] |
| evo_still_radiant | sniff_03 | 0.218 | 9.0 | 1.137 | [2.79, 8.56] |
| evo_still_radiant | lookup_tip_02 | 0.177 | 8.18 | 1.494 | [1.86, 7.96] |
| evo_still_radiant | lookup_tip_04 | 0.386 | 5.7 | 1.157 | [2.73, 5.0] |
| evo_still_radiant | getup_01 | 0.283 | 7.21 | 1.143 | [2.95, 6.57] |
| evo_still_radiant | sniff_itch_01 | 0.208 | 9.3 | 1.19 | [2.29, 9.02] |
| evo_still_ember | lookup_tip_02 | 0.269 | 6.57 | 1.06 | [1.05, 6.48] |
| evo_still_ember | getup_01 | 0.183 | 7.75 | 0.989 | [0.65, 7.72] |

