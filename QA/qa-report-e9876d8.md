# QA：第 3a 批（`e9876d88`）

唯讀 `code/glimmer-evo6` @ `e9876d888dae4e435e624178ec75e5a21509a91b`，tree `32262f63668da96df49f56a0b0b261f7eed0a118`（已對）。冇改 code branch，冇推 main。

## 1. 觸摸手感

閾值喺 `PARAMS.touch`，可調。

| 項 | 值 | 出處 |
|---|---|---|
| 戳 | `< poke.maxMs`（300） | `src/data.js:800`，`src/touch.js:90` |
| 來回擦一步 | `≥ tickle.minSwingPx`（6） | `src/data.js:802`，`src/touch.js:75` |
| 長按瞇眼 | `≥ hold.sec`（0.6s） | `src/data.js:801`，`src/touch.js:82` |
| 摸頭 | `≥ hold.patSec`（3s） | `src/data.js:801`，`src/touch.js:83` |
| 搖機 | 加速度 `> shake.g`（2.5g），唔係 px | `src/data.js:804`，`src/touch.js:102` |

邊界（真 `createRecognizer`）：

| 輸入 | 分類 |
|---|---|
| 299ms、冇郁 | 戳 |
| 300ms、301ms、冇郁 | release（`< 300`，同 `src/ui.js:358` 短撳 `ms < shortTapMs` 一樣） |
| 來回 5px | 0 個轉折，唔係搔癢 |
| 來回 6px、7px | 有轉折；8 下入面出搔癢 |

舊長撳同新摸頭唔搶同一件事。0.4s 開始磨蹭（`src/data.js:394` `nuzzleHoldMs`），1.2s 入呼嚕同之後的扮冷靜（`purrAfterSec`）。3s 先 `notePat` 一次（`src/touchui.js:35`）。鬆手如果已經計過摸頭，`src/sys12ui.js:125` 唔再計第二次。短撳仍然計委託摸頭，係 v10.2 舊規則，註解寫明保留。

多指：第二隻手指唔開新一下（`src/ui.js:338`）。`pointercancel` 傳入 recognizer 唔出手勢（`src/touch.js:86`，`src/ui.js:353-356`）。辨識器本身係單指；再 call `down` 會換走上一點，介面冇咁做。

## 2. 提示排隊

`src/data.js:799`：最多 3 個等候、等超過 20s 作廢、句與句隔 0.25s。`src/touch.js:136-154`：而家出緊的句未完，新句只入隊；同一句唔再排；urgent 先頂走現時。滿額丟最舊的等候句，過期的不出。`src/sys12ui.js:104-117` 心聲同觸摸句都經 `G.say`。`tests/touch.test.js` ⓪ 過。

## 3. 反應讓位

`src/data.js:808` `yieldTo`：nuzzle、nuzzle_purr、rush、reunion_happy、eat、play、catch_reach、dig。`src/render.js:938` 播緊呢啲 clip 就唔用反應 clip 換身。扮醒呆要 `state === 'stay'` 先抽（`src/touchui.js:70-72`），磨蹭／衝刺期間唔插入。

`e9876d88` 的讓位係「唔蓋專屬 clip，只疊程序化」。`src/render.js:974` 仍然把觸摸的縮放／位移乘上身體，`src/render.js:1046` 仍然畫 fx。呼嚕 clip 冇被換走。

## 4. 心情同摸頭額

五種：poke、hold、tickle、pull、shake（`src/touch.js:13`）。每種當日第一次心情 +1，同懸浮共用 `localStorage` key `fpet_daily_v1`，每日 ≤5（`src/data.js:805`，`src/touch.js:49-62`）。第二日 `simDay`／`bridgeDay` 換 key 就重置。滿額唔加心情。瞓覺、光卵唔加、唔食額。唔經 `noteCare`。

3 秒摸頭走 `notePat`（`src/touchui.js:35`）。懸浮每日 queue 上限仍然 12（`src/data.js:266` `overlayPatPerDay`）。`tests/touch.test.js` 摸頭一節斷言 12。

拖步踏地：`src/behavior.js:481` `step_plod`，`src/audio.js:90-92` 交替 `pet_step_plod_a/b`。檔案 `audio/sfx/sfx_pet_step_plod_a.ogg`、`sfx_pet_step_plod_b.ogg` 在。音量同 rate 喺 `src/data.js:733`。

## 5. 平衡回歸（scan-v10-8，真參數，冇覆寫）

**16／16。** 同 mg2.3 鎖定值差冇一項過 3pt。疏玩 CQ 中位 18。夜貓月眠 82.4。疏玩上線日星星碎 19。

| # | 目標 | 結果 | 實數 | 對鎖定 |
|---|---|---|---:|---|
| 1 | 9 條路 ≥2% | ✅ | 最低微塵 4.95 | 4.95 |
| 2 | 每表 ≥2 結局 ≥2% | ✅ | 夜貓螢絨＋月眠 | |
| 3 | 單一 ≤85% | ✅ | 82.4 | 82.4 |
| 4 | 螢絨 3–10% | ✅ | 5.47 | 5.47 |
| 5 | 每表菇傘 ≤30% | ✅ | 最高 25.2 | |
| 6 | 晶角 ≥5% | ✅ | 15.32 | 15.32 |
| 7 | 月眠 ≥5% | ✅ | 18.72 | 18.72 |
| 8 | 每表燦光 ≤50% | ✅ | 最高 22.9 | |
| 9 | 疏玩柔光＋微塵 ≥2% | ✅ | 28.3／29.7 | |
| 10 | 疏玩 CQ 15–35 | ✅ | 18 | |
| 11 | 新系統分 ≤25% | ✅ | 25 | |
| 12 | 疏玩上線日星碎 15–30 | ✅ | 19 | 19 |
| 13 | 其餘 5 表 15–30 | ✅ | 28／22／25／23／23 | |
| 14 | 冇一日穿 30 | ✅ | 最高 30 | |
| 15 | 火苗 12–18% | ✅ | 14.00 | 14.00 |
| 16 | 柔光 ≥10% | ✅ | 10.92 | 10.92 |

火苗額仍然每日 4 局、每局 +1，窗內唔佔額：21:00 四局月眠 +4、火苗 +0、額 0；同日 13:00 火苗 +1（`src/sim.js:154-156`）。

直向：390×844、360×800 唔擋。橫向 1280×720 滑鼠同 844×390 觸控都全屏「請轉直向」（`index.html:23`）。

觸控：⚙／📖／圖鑑同第 2 批掣，390 最細 49px，360×800 最細 48.9px。小遊戲 × 方格 56.33／52。

懸浮：`overlayOpenGame`、600s 冷卻、`fpet_daily_v1` 仍在程式。呢個 commit 冇 APK，未重裝真機。

## 6. 測試

unit 15 個檔，我跑到 **1410／0**（audio 48、behavior 187、branches5 204、events 161、evo6 176、minigames2 70、overlay-status 24、reactclip 38、route-clarity 51、route-garden 7、sim 99、systems12 138、systems12b 135、touch 59、economy-sys12b 13）。`economy-v102.test.js` 未再跑（同 scan-v10-8 同一條路線）；佢固定再有 22 個斷言，加埋 1432。遊程報 1433，差 1 個斷言，套件本身 0 失敗。

e2e 14 套全部 0 失敗，加總 **713**：touch 52、s3 32、mg2 46、sys12b 48、sys12 79、s1 51、s2b 25、evo6 54、route 55、hd2d 51、live 46、live2 43、playwright 37、a 94。同遊程 713 一樣。

## P0／P1／P2

**P0：** 無。

**P1：** 無。

**P2：** 無。
