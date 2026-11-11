# anim timing 330d3a57

對象：`art/anim-timing` @ `330d3a572e89e21bfe1a6af674024b7aba817a49`。只讀，冇 merge。

指令：

```
PYTHONDONTWRITEBYTECODE=1 python3 art-pet/tools/validate_anim_timing.py --root . --sfx-readme /tmp/yinyin-audio-README.md
```

工作區同全機都冇檔名叫 `yinyin-audio-README.md`。`--sfx-readme` 用咗 `origin/audio/pet-plan-a` @ `07762d21`（2026-11-11 00:50，遊音「pet anim sfx」）的 `audio/README.md`，sha256 `7f2d34db638f80dbb41af7e4af8b44eaebfa0c4d7ad03cb4b161ab00e2b37d1a`。呢份有 §7.12，對住 31 clip／42 個配聲點。如果上載檔唔係呢一版，要再跑。

## 驗證器

**PASS**（exit 0）。錯誤 0。

```
OK  clips=31 (atlas=31)  events=42  hooked=6  null=36  warnings=1
```

錯誤清單：空。

警告 1 條：檔內烘焙 hook 表 83 個名，而家 README 抽出 120 個。烘焙表入面嘅名全部仍喺 README（`only_baked` 空）。README 多出 37 個，驗證器只印頭 8 個，全部係：

`sfx_critter_roll_a`、`sfx_critter_roll_b`、`sfx_critter_shake_a`、`sfx_critter_shake_b`、`sfx_critter_startle_a`、`sfx_critter_startle_b`、`sfx_critter_transform_a`、`sfx_critter_transform_b`、`sfx_hook`、`sfx_pet_clap_a`、`sfx_pet_clap_b`、`sfx_pet_grass_rustle_a`、`sfx_pet_grass_rustle_b`、`sfx_pet_jump_a`、`sfx_pet_jump_b`、`sfx_pet_letter_drop_a`、`sfx_pet_letter_drop_b`、`sfx_pet_pickup_a`、`sfx_pet_pickup_b`、`sfx_pet_place_a`、`sfx_pet_place_b`、`sfx_pet_point_a`、`sfx_pet_point_b`、`sfx_pet_proud_a`、`sfx_pet_proud_b`、`sfx_pet_reach_a`、`sfx_pet_reach_b`、`sfx_pet_step_walk_a`、`sfx_pet_step_walk_b`、`sfx_pet_stretch_a`、`sfx_pet_stretch_b`、`sfx_visitor_nod_a`、`sfx_visitor_nod_b`、`sfx_visitor_offer_letter`、`sfx_visitor_offer_seed`、`sfx_visitor_rattle_a`、`sfx_visitor_rattle_b`。

`sfx_hook` 係 README 用反引號寫欄名，抽出器當成音檔名。其餘 36 個係 §7.12 新 foley。timing 檔未貼呢批 hook，所以 36 個 event 仍然 `sfx_hook=null`。已接上嘅 6 個都喺 README：`pounce` land 500 ms `sfx_pet_step_hop_a`、`cheer` cheer_peak 200 ms `sfx_pet_happy`、`cheer` land 400 ms `sfx_pet_step_hop_a`、`idle_lively` land 500 ms `sfx_pet_step_hop_a`、`idle_lazy` yawn 600 ms `sfx_pet_yawn`、`scratch_head` scratch 250 ms `sfx_pet_scratch_a`。

## 自己覆核

用圖集 JSON 的 `fps`、`frameCount`、`loop` 同 `frames` 長度再算一次，冇跟驗證器嘅通過結果抄。`t_ms` 預期值係 `sum(frameMs[:frameIndex])`，`frameMs` 用 `round(i*1000/fps)` 差分，同圖集幀數、時長對。

- 每個 event 的 `frameIndex` 都喺 `0 .. frameCount-1`，`t_ms` 同圖集換算一致。對唔上：0。
- 內容係 31 個 clip、42 個 event。`counts` 同實際數一樣（hook 6、null 36）。圖集 clip 集合同 timing 的 id 集合一樣。
- 寵物 S／M／L 齊。16 個 pet clip（hunt 4 加 m2 12），每個都有 S、M、L 的 json、png、法線、發光貼圖。三個尺寸的 fps、幀數、loop 同 `clips.json` 一致，`frames` 長度等於 `frameCount`。缺檔：0。

小動物同訪客唔係三套體型。dewlet、loambun、seedfluff 係 32px（timing 標 S），mossback 係 48px（標 M），三位訪客各一張 M。呢啲係單尺寸圖，唔當缺 L。
