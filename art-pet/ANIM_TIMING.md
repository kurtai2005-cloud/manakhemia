# anim_timing.json — 寵物／訪客／小動物 clip 時機（遊音＋遊測）

疊喺 **art/m2-actions @ 230dab2f**（M1 底本 art/m1-icons-hunt @ 13a00477）。一份檔俾遊音對聲、遊測核對時機（相差超過 1 幀就 fail）。

生成：`PYTHONDONTWRITEBYTECODE=1 python3 art-pet/tools/build_anim_timing.py --root . --m1 <M1> --m2 <M2> --sfx-readme audio/README.md`

驗證：`PYTHONDONTWRITEBYTECODE=1 python3 art-pet/tools/validate_anim_timing.py --root . --m1 <M1> --m2 <M2> --sfx-readme audio/README.md`

腳本會讀晒 M1 hunt／critter 同 M2 pet／visitor 嘅 atlas JSON，再生成呢份檔。事件跟 build 腳本嘅姿勢對出來，唔會加姿勢入面冇嘅動作。

## 欄位

每個 clip：`id`、`zh`、`source`（m1／m2）、`kind`（pet／critter／visitor）、`sizes`（寵物 S／M／L；小動物／訪客得實際存在嗰檔）、`frameCount`、`fps`、`frameMs[]`（每幀整數 ms，加總唔漂移）、`durationMs`、`loop`、`events`。

每個 event 必有：

| 欄 | 說明 |
|---|---|
| `frameIndex` | 0-based，對應 atlas `_01`＝0 |
| `t_ms` | 由 clip 開頭計，等於 `sum(frameMs[:frameIndex])`（該幀開始） |
| `sfx_hook` | 須完全吻合 遊音 `audio/README.md` 已列嘅 `sfx_*` 名；對唔上就 `null`，唔自製 |
| `accent` | 只可以係 `land`／`peak`／`release` |

`toleranceFrames`＝1：遊測若 \|實際 − 本檔\| 超過 1 幀就 fail。

允許嘅 hook 名烘焙喺 JSON 嘅 `sfxHooks.names`（由 README 全文抽出：第 3 節同 §7.1／7.2／7.5／7.9／7.11）。§7.11 係 HD-2D UI hook；寵物動作多數用 §7.1／§7.9（例如 `sfx_pet_step_hop_a`、`sfx_pet_yawn`、`sfx_pet_scratch_a`）。
