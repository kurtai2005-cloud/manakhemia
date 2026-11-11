# anim_timing.json — 寵物／訪客／小動物 clip 時機（遊音＋遊測）

疊喺 **art/anim-timing-fix1 @ f6d60b5e**（再疊 art/anim-timing @ 330d3a57；art/m2-actions @ 230dab2f；M1 底本 art/m1-icons-hunt @ 13a00477）。一份檔俾遊音對聲、遊測核對時機（相差超過 1 幀就 fail）。

生成：`PYTHONDONTWRITEBYTECODE=1 python3 art-pet/tools/build_anim_timing.py --root .`

驗證（唔使加參數；預設讀 `audio/anim_sfx_map.json`）：`PYTHONDONTWRITEBYTECODE=1 python3 art-pet/tools/validate_anim_timing.py`

**驗證依賴：** art 分支本身冇 `audio/anim_sfx_map.json`。要無參數跑過，須同時有遊音 **audio/pet-plan-a @ 07762d21**（PR #16，tree `904bc635`）嘅 `audio/anim_sfx_map.json`。遊程請將嗰個 commit 嘅呢份 JSON 放入工作樹（唔使連 ogg 一齊），或用 `--sfx-map <路徑>`。呢次 staging zip **冇**夾帶 audio 檔。已刪 `art-pet/sfx_hooks.json`，名單只得一個來源。

`--sfx-map` 可覆蓋 map 路徑。`--sfx-readme` 只係後備（無 map 先用，由 README 抽 `sfx_*` 名；**唔好**用本 repo 舊稿 `audio/README.md`）。已唔再支援 `--refresh-hooks`。

腳本會讀晒 M1 hunt／critter 同 M2 pet／visitor 嘅 atlas JSON，再生成 `anim_timing.json`。事件跟 build 腳本嘅姿勢對出來，唔會加姿勢入面冇嘅動作。`sfx_hook` 由 **`audio/anim_sfx_map.json`** 填：42 個事件入面 41 個用 map 畀嘅 hook；`idle_lively` 嘅 `hop_peak` @250 ms 刻意 `sfx_hook: null`（落地已有 `step_hop`，峰頂再加聲會太密）。允許名單＝map 入面嘅 `sfx_hook` 加 `files[]` 檔名（含 a/b 交替）。timing 入面嘅 hook 若唔喺名單，validator 會明確 fail。

## 欄位

每個 clip：`id`、`zh`、`source`（m1／m2）、`kind`（pet／critter／visitor）、`sizes`（寵物 S／M／L；小動物／訪客得實際存在嗰檔）、`frameCount`、`fps`、`frameMs[]`（每幀整數 ms，加總唔漂移）、`durationMs`、`loop`、`events`。

每個 event 必有：

| 欄 | 說明 |
|---|---|
| `frameIndex` | 0-based，對應 atlas `_01`＝0 |
| `t_ms` | 由 clip 開頭計，等於 `sum(frameMs[:frameIndex])`（該幀開始） |
| `sfx_hook` | 須完全吻合 `audio/anim_sfx_map.json` 已列嘅 `sfx_*` 名；對唔上或者刻意無聲就 `null`，唔自製 |
| `accent` | 只可以係 `land`／`peak`／`release` |

可選欄（有就用，冇就當預設；唔影響舊必填 schema）：

| 欄 | 說明 |
|---|---|
| `preroll_ms` | 播放起點＝`t_ms − preroll_ms`。而家得 `idle_lazy.yawn` ＝ 600（約喺 clip t=0 開始播，令呵欠峰對準 frame 3） |
| `kind` | `foley`（共用，按體型調 pitch：S 1.12／M 1.0／L 0.88）或 `voice`（而家得團絨檔） |
| `accent_offset_ms` | 檔內能量峰相對檔頭嘅 ms（遊音量度；執行可忽略） |
| `loopPlay` | 循環 clip 嘅播放策略：`on_enter`（小動物驚嚇：只喺入狀態播一次，唔好每圈重播）；`every_n_loops`（`idle_lazy.yawn` 檔長可能疊下一圈；訪客遞信建議隔幾圈先播）。冇呢欄就跟 clip 每圈觸發（例如落地腳步） |
| `character` | 聲線角色（而家 `tuanrong`；細佬／訪客尚未做，fallback＝團絨檔＋體型音高） |

`toleranceFrames`＝1：遊測若 |實際 − 本檔| 超過 1 幀就 fail。
