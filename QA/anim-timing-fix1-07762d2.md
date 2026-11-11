# anim timing fix1 × pet-plan-a

兩條 code branch 只讀，冇 merge。

- 美術：`art/anim-timing-fix1` @ `f6d60b5e351a92b990b5ae613934edc26419aa4b`（2026-11-11 00:46 UTC）。`art-pet/sfx_hooks.json` 在。
- 音訊：`audio/pet-plan-a` @ `07762d21f732f014a590003895d99154a509ef07`（2026-11-11 00:50 UTC，PR #16）。

指令（冇 `--sfx-readme`）：

```
PYTHONDONTWRITEBYTECODE=1 python3 art-pet/tools/validate_anim_timing.py --root .
```

檔案喺 `art-pet/tools/`，唔係 repo 根的 `tools/`。exit 0。

```
OK  clips=31 (atlas=31)  events=42  hooked=6  null=36  warnings=0
```

## 1. 每個 event（驗證器）

驗證器查 `anim_timing.json` 自己的 `sfx_hook`：要喺 `sfx_hooks.json`（83 個名）或者 `null`；`t_ms` 等於 `sum(frameMs[:frameIndex])`；accent 係 land／peak／release；frameIndex 喺幀數內。42 個都 **PASS**。失敗：無。

美術檔而家只接咗 6 個舊 hook。其餘 36 個係 `null`，所以驗證器當合格，唔係已經播到遊音新檔。

| clip | event | frame | t_ms | 美術 sfx_hook | 結果 |
|---|---|---:|---:|---|---|
| part_grass | grass_rustle | 2 | 250 | null | PASS |
| pounce | jump | 2 | 250 | null | PASS |
| pounce | land | 4 | 500 | sfx_pet_step_hop_a | PASS |
| carry_fruit | footstep | 0 | 0 | null | PASS |
| carry_fruit | footstep | 3 | 300 | null | PASS |
| cheer | jump | 1 | 100 | null | PASS |
| cheer | cheer_peak | 2 | 200 | sfx_pet_happy | PASS |
| cheer | land | 4 | 400 | sfx_pet_step_hop_a | PASS |
| dewlet_scared | startle | 0 | 0 | null | PASS |
| dewlet_tofruit | shake | 0 | 0 | null | PASS |
| dewlet_tofruit | transform | 3 | 375 | null | PASS |
| dewlet_tofruit | roll | 4 | 500 | null | PASS |
| loambun_scared | startle | 0 | 0 | null | PASS |
| loambun_tofruit | shake | 0 | 0 | null | PASS |
| loambun_tofruit | transform | 3 | 375 | null | PASS |
| loambun_tofruit | roll | 4 | 500 | null | PASS |
| mossback_scared | startle | 0 | 0 | null | PASS |
| mossback_tofruit | shake | 0 | 0 | null | PASS |
| mossback_tofruit | transform | 3 | 375 | null | PASS |
| mossback_tofruit | roll | 4 | 500 | null | PASS |
| seedfluff_scared | startle | 0 | 0 | null | PASS |
| seedfluff_tofruit | shake | 0 | 0 | null | PASS |
| seedfluff_tofruit | transform | 3 | 375 | null | PASS |
| seedfluff_tofruit | roll | 4 | 500 | null | PASS |
| mail_post | footstep | 0 | 0 | null | PASS |
| mail_post | letter_drop | 4 | 500 | null | PASS |
| mail_post | clap | 5 | 625 | null | PASS |
| idle_lively | hop_peak | 2 | 250 | null | PASS |
| idle_lively | land | 4 | 500 | sfx_pet_step_hop_a | PASS |
| idle_diligent | pickup | 2 | 250 | null | PASS |
| idle_diligent | place | 5 | 625 | null | PASS |
| idle_lazy | yawn | 3 | 600 | sfx_pet_yawn | PASS |
| idle_clingy | reach | 2 | 250 | null | PASS |
| scratch_head | scratch | 2 | 250 | sfx_pet_scratch_a | PASS |
| stretch | stretch | 2 | 250 | null | PASS |
| proud_hips | hands_hips | 2 | 250 | null | PASS |
| point_frame | point | 3 | 375 | null | PASS |
| snail_postman_snail_deliver | offer | 3 | 375 | null | PASS |
| mushroom_granny_granny_seed | nod | 2 | 250 | null | PASS |
| mushroom_granny_granny_seed | offer | 3 | 375 | null | PASS |
| firefly_vendor_vendor_show | rattle | 2 | 250 | null | PASS |
| firefly_vendor_vendor_show | rattle | 4 | 500 | null | PASS |

## 2. map 對 timing

`audio/anim_sfx_map.json` 42 條，同上面 42 個 `(clip, event, t_ms, frameIndex)` 一一對上。多出或缺少：無。

- 41 條有 hook，對應 ogg 都喺 `audio/sfx/`（42 個檔，a/b 拆開計）。缺檔：無。
- `idle_lively`／`hop_peak` @ 250：`sfx_hook` null，`files` 空。刻意無聲。
- hook 名都出現喺 README §7.12。
- 庫內冇 `_preview*`／`_prev` 音檔。`sfx/_preview_pet_anim.ogg` 未提交。`audio/tools/preview_pet_anim.py`、`preview_ui8.py` 係腳本。

能量峰用 8 ms RMS、44.1 kHz 解碼量。新檔峰 9.8–27.0 ms。最慢係 `sfx_visitor_offer_letter.ogg` 27.0 ms，等於遊音講的上限，細過一幀（fps 8 → 125 ms）。`toleranceFrames=1` 全部新檔都過。

現有檔：

- `sfx_pet_step_hop_a/b` 峰 12.2／10.7 ms，對 map 的 12 ms。
- `sfx_pet_happy.ogg` 峰 62.7 ms，對 map 的 63 ms。cheer 一幀 100 ms，仍喺 1 幀內。呢個係舊檔，README 寫明約 63 ms，唔納入「新檔 ≤27 ms」。
- `sfx_pet_yawn.ogg` 峰 603.4 ms。播放起點係 `t_ms − 600`，對事件 600 差 3.4 ms。
- `sfx_pet_scratch_a/b` 起音 7.0／3.9 ms（對 map 的 7 ms）。中段最響 290／359 ms 係後面幾下，README 話 accent 係起音。

## 3. 之後 M1 GUT 要守的規則

草稿 `test/qa/test_anim_sfx.gd` 已寫呢幾條，未接入遊程：

- 邊隻做動作就用邊個體型的 pitch：S 1.12、M 1.0、L 0.88。
- `sfx_pet_yawn` 由 `t_ms − 600` 開始播。
- 四種小動物 `startle` 只喺進入狀態播一次，循環唔再播。
- 招牌執葉／伸手、訪客遞信／點頭／搖瓶、呵欠：同一圈內唔再播（750 ms，呵欠 1200 ms）。`idle_lively` 的落地步每圈仍然播；`hop_peak` @ 250 保持無聲。
- 聽到的時間同 event `t_ms` 相差唔可以超過 1 幀。

## P0–P3

冇 P0。冇 P1。冇 P2。

P3。`art-pet/sfx_hooks.json` 係 2026-11-09 快照，83 個名，未收 §7.12 新名。`anim_timing.json` 因此保持 36 個 `sfx_hook=null`。驗證器見 null 就過。遊音 map 的 41 個檔未寫入 timing。把新名貼入 timing 之前，要先更新 `sfx_hooks.json`，否則而家這支驗證器會拒。檔：`art-pet/sfx_hooks.json`、`art-pet/anim_timing.json`、`audio/anim_sfx_map.json`。commit：`f6d60b5e`、`07762d21`。
