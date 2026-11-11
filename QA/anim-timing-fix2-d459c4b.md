# anim timing fix2

`art/anim-timing-fix2` 已推。`d459c4bec2a9d5a1b4c50e4d6f76b1f16f1f9ac3`，父 commit 係 fix1 `f6d60b5e`。只讀，冇 merge。`art-pet/sfx_hooks.json` 已刪。

驗證器預設讀 `<root>/audio/anim_sfx_map.json`。art 分支冇呢份檔。跑之前把 `audio/pet-plan-a` @ `07762d21` 的 `audio/anim_sfx_map.json`（blob `03df3ef6`）放到工作樹，冇加任何參數：

```
PYTHONDONTWRITEBYTECODE=1 python3 art-pet/tools/validate_anim_timing.py
```

**PASS**，exit 0。

```
OK  clips=31 (atlas=31)  events=42  hooked=41  null=1  warnings=0
```

42 個 event 都過。唯一 null 係 `idle_lively`／`hop_peak`，frame 2，`t_ms` 250。其餘 41 個 `sfx_hook` 同 `07762d21` 的 map 逐條相同，frame 同 `t_ms` 亦相同。

## 可選欄

| event | 欄 | 值 | 結果 |
|---|---|---|---|
| idle_lazy／yawn @600 | preroll_ms | 600 | 有，播放起點＝0 |
| idle_lazy／yawn | loopPlay | every_n_loops | 有 |
| dewlet／loambun／mossback／seedfluff 的 startle | loopPlay | on_enter | 四個都有 |
| snail_postman／offer（遞信）@375 | loopPlay | every_n_loops | 有 |

其他 event 冇 `loopPlay`，包括落地步、點頭、搖瓶、奉種子。文件話冇呢欄就每圈觸發。

`every_n_loops` 冇整數 N。`ANIM_TIMING.md` 只寫「隔幾圈」。

## GUT

`test/qa/test_anim_sfx.gd` 已改去 fix2，未接入遊程。編碼：hop_peak @250 無聲；呵欠 `preroll_ms=600`；四個 startle 只喺入狀態播；呵欠同遞信 `every_n_loops`（JSON 冇 N，草稿用 2）；冇 `loopPlay` 的落地同搖瓶每圈都播；pitch S 1.12／M 1.0／L 0.88。Godot 4.7 只做語法檢查。

## P0–P3

冇 P0。冇 P1。冇 P2。

P3。`every_n_loops` 未寫隔幾多圈。檔：`art-pet/anim_timing.json`（`idle_lazy.yawn`、`snail_postman_snail_deliver.offer`）、`art-pet/ANIM_TIMING.md`。commit `d459c4be`。
