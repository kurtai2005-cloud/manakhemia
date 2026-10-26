# Clip 格式規格（方案 A，以遊美 `art/CLIPS.md`／`CLIPS.json` 為準）

> 原則：**遊美格式就係標準**。引擎（`src/data.js` 嘅 `CLIPS`／`FORMS`、`src/render.js` 嘅 atlas loader）跟佢，唔反過嚟要求美術遷就。本文件記錄引擎點樣消費呢套格式、同埋發現嘅格式問題。

## 1. 圖集（atlas）

| 項目 | 規格 | 引擎處理 |
|---|---|---|
| 檔案 | `art/atlas_<form>.png/json`（`egg`／`sprout`／`radiant`／`soft`／`props`） | `render.loadAtlases()` 載入 5 組；失敗 → `atlasReady=false` → 退回程序化精靈（不白屏） |
| 尺寸 | **≤1024×1024**（sprout 1024×256、radiant／soft 1024×512、props 1024×64、egg 1024×64） | e2e／單元測試逐個驗證；舊 `pet_tuanrong_atlas.png`（2048×134）已棄用，glimmer-a 內冇檔案、冇引用（測試有掃描） |
| 排版 | padding 2px、extrude 1px、免 trim、冇 rotate | 直接用 `frame.{x,y,w,h}`，唔做 trim 偏移 |
| 幀名 | `pet_tuanrong_<form>_<clip>_<NN>` | 由 `animations[clip].frames[]` 順序讀 |
| 載入策略 | **只載入當前形態＋props**（目標；現階段全載 5 張，PNG 合計見 `du art/*.png`，見 §6 風險） | `D.FORMS[fk].atlas` 決定用邊張 |
| 繪畫 | Nearest、關平滑、整數像素座標 | `imageSmoothingEnabled=false`＋`Math.round` |

## 2. Pivot（錨點）

- 標準：**底部中心 `(w/2, h-3)`**。sprout (16,29)、radiant／soft (32,61)。
- `atlas_sprout／radiant／soft／props` 每幀有 `pivotPx`；`atlas_egg` **冇 `pivotPx`** → 引擎 fallback 用同一公式 `(w/2, h-3)`（`render.atlasSrc()`）。
- 引擎把 pivot 放喺地面接觸點（blob shadow 中心）；幀內位移／擠壓已烙入圖，引擎只移動 pivot。

## 3. 方向與鏡像

- 所有 clip 一律**朝右**；朝左＝`scale(-1,1)`（`behavior.dir`）。
- 圖示／zzz 用 anchor `head_r`：**anchor 嘅 x 跟鏡像翻轉，但圖示本身唔鏡像**（避免心形／問號反咗）。

## 4. Clip 表（`CLIPS.json` → `data.js:CLIPS`）

欄位對應：

| 遊美 `CLIPS.json` | 引擎 `CLIPS[name]` | 備註 |
|---|---|---|
| `frames`／`fps` | 同名 | 時長＝`frames/fps`（`BEH.clipDur`） |
| `loop`＋`loopFrom` | 同名 | `loopFrom`：播完後由該幀循環（droop 第 4 幀起） |
| `repeat` | 同名 | emo_happy 2 幀 ×4（≈2 s） |
| `priority`／`interruptible` | 同名 | 「否」嘅 clip 屬 NONINT，播完先處理下一個 |
| `cooldown_s` | `cooldown` | 命名不同（見 §7） |
| `next` | `next` | 播完接 |
| `attach[]` {prop, anchor, fromFrame, ground} | `attach` | 道具獨立圖層，**唔烙入幀** |
| `status`（已交付／待定） | **`ready`** | `ready:false` → 用 **placeholder**（見 §5） |
| —（引擎自加） | `extra:true` | 美術表冇、行為需要（jump／grumpy／lookup／dig） |

### 道具／anchor 疊層

`圖示左上 = pet pivot + anchor − prop.pivotPx`（mirror 時 anchor.x 乘 -1）。anchor 表：

| form | head_r | pot | sun |
|---|---|---|---|
| sprout | (9,-14) | (22,0) | (0,0) |
| radiant | (16,-28) | (31,0) | (0,0) |
| soft | (18,-30) | (34,0) | (0,0) |

花盆（`flowerpot_idle/bump`）同光斑（`sun_patch`）係**獨立場景道具圖層**，由 `attach`（`fromFrame`、`ground:true` 墊底）驅動，唔屬寵物 sprite。

## 5. Placeholder 規則（`ready:false` 嘅 clip）

1. `art.usePending=false`（預設）：用該形態 `idle` 幀＋程序化 transform（`placeholderXform`：位移／擠壓／彈跳）扮演動作；
2. `art.usePending=true`：atlas 內已有「待定」幀（遊美已先行放入）就直接用；冇嘅 clip 仍走 placeholder；
3. 事件 icon：遊美 `fx/events` 9 個已交付（見 §9），`iconPlaceholder` 已移除；日後新增事件如未有 icon，可再設 `iconPlaceholder:true`（UI 會顯示 `◌`）——目前 UI 已唔再處理此旗標，需要時要補回。
4. 遊美交付後只需：把該 clip 喺 `CLIPS.json` 標「已交付」→ 引擎 `ready:true`，**無需改行為碼**（clip 名即 contract）。

## 6. 效能／記憶體

- 5 張 PNG 解碼後 ≈ 1024×(256+512+512+64+64)×4B ≈ 5.7MB 顯存；現階段全載。**待改**：按當前 `form` 只載入該形態＋props（進化時換載）。未做，因為進化過場需要前後兩形態同時存在。
- 低畫質（`low`）下 blob shadow／光效降級，atlas 不變。

## 7. 發現嘅格式問題（請遊美／遊策確認）

1. `droop`：`loop:true`＋`loopFrom:3` 但 md 寫「否→第4幀起循環」，兩個欄位語意重疊。引擎以 `loopFrom` 為準。
2. `emo_happy`：`loop:false` 又 `repeat:4`，「repeat」唔喺通用欄位定義內；引擎特別處理。建議統一寫 `loop:false, repeat:N`。
3. `CLIPS.json` 用 `cooldown_s`，引擎／數據用 `cooldown`（單位同為秒）；並且 `sunbathe`(120)／`pot_bump`(180) 嘅 clip 冷卻被遊策 `PARAMS.beh.envCooldown=260` 取代（環境互動共用冷卻）。
4. `atlas_egg.json` 無 `pivotPx`，同其餘 atlas 不一致（引擎已 fallback）。
5. 美術無表：**dirty**（污漬用程序化 overlay 佔位）、**jump／grumpy／lookup／dig**（行為需要，標 `extra`）、**dust 形態無 atlas**（用程序化精靈）。
6. 表情：美術 6 款（happy／hungry／wantplay／sleepy／cuddly／surprised）同原行為映射（unwell／dirty／neutral）有差異：unwell→`sick` clip、neutral→idle、dirty→overlay。
7. `yawn` 權重「精力<30 ×3」：精力<30 時多數已進入睏睏／睡眠流程，**實際打唔到**（不可達，唔影響體驗）。
8. 連點：美術 `emo_cuddly`＝「2 秒內 ≥3 次」；原 README 建議「1.5 秒內 ≥4 次＝鬧脾氣」。遊策定案：**鬧脾氣＝10 秒內連點 5 次**，同 cuddly 唔衝突（cuddly 先到）。
9. sprout 畫布淨高 4px（headroom 緊），跳躍幅度已被美術縮小；大幅度事件動作（cheer_jump）喺 sprout 上可能較弱。
10. 圖示 pivot 方式不一（zzz 左下 [2,22]，其餘 [8,14] 中下）——引擎一律按各自 `pivotPx` 處理，無需特判；僅提示美術保持一致更易維護。

## 8. 交付狀態（更新：遊美全 clip 已交付）

- 23 個 clip 全部 `已交付`（`CLIPS.json` 23 項，`data.js` CLIPS 全 `ready:true`；`usePending` 已無作用，保留作 fallback 開關）；atlas_sprout／radiant／soft 已重打並覆蓋；`atlas_props` 無變。
- **仍冇美術**：額外 clip `jump`／`grumpy`／`lookup`／`dig`（`extra:true`，用 placeholder）、`dirty` 表情（程序化 overlay）、dust 形態 atlas。
- **play 位移為 0**（遊美註明）：引擎 render 層於 frame4–5（idx 3,4）加前衝 root-motion（64px 形態 +4、32px sprout +2；`PARAMS.art.playRootMotion`，只影響繪畫位置，唔動 sim x）。

## 9. 事件 icon（`atlas_events`）與 daylight（新增）

**atlas_events.png／json**（1024×128，32×32，pivot (16,16)，`animations[<icon>]`＝{frames,fps,loop,icon}）。id→icon：gift→gift_return、butterfly、meteor→meteor_night、rainbow、sleeptalk→sleep_talk、grumpy→tantrum、treasure、flash→shiny_day、firefly_walk。引擎用法：① 提示卡 48×48（CSS 放大、nearest）循環播放；② 事件頭 `cardSec`（5 秒）喺寵物頭頂 1x 顯示（淡入出）。
**daylight**（`art/daylight/`）：`daylight.json`（4 時段 ambientMultiply／pet.multiply／add／rimColor／bloom／vignette／lamp／sky、`blendSeconds` 1800）＋ `bg_*.png`／`light_*.png`（480×270）。引擎對應：早→early、午→noon、晚→dusk、夜→night（**以遊策時段 07／11／17／23 為界，daylight.json 嘅 `hours` 05:30／09:30／16:00／19:30 只作參考**）；新時段開始後 30 分鐘 mix 0→1 淡入。
- 預設（花園）：ambientMultiply 整屏 multiply（`PARAMS.light.dlAmbient` 0.6）、bloom／vignette 倍率、寵物 sprite 套 multiply＋add＋1px rim（窗光側）。
- 可選「房間」皮膚（`PARAMS.art.daylightBg` 或 `?room=1`）：bg 1x（pivot 對齊 GROUND_Y、x 以 240 為中心裁 195 寬）＋ light overlay cross-fade，取代花園 L0/L1/L3。

## 10. 新發現嘅格式／整合問題

1. **bg／light 係 480×270 橫向室內場景**，本遊戲係 195×422 直向花園（art 格 ×2）。1x 擺放（pet 64px）尺寸一致，但只能裁出 195 寬、上下各餘 60／92px 要填色 → 預設唔用 bg，只用 JSON 色彩；房間皮膚作可選項，需策劃決定係咪改為房間場景。
2. `daylight.json` 嘅 `hours`（05:30／09:30／16:00／19:30）同遊策時段（07／11／17／23）唔一致；引擎以遊策為準。
3. `light_*.png` 已烘環境色＋暗角（房間皮膚）；花園模式改用 ambientMultiply，兩者唔可同時疊（會雙重壓暗）。
4. bloom／tilt-shift 預覽係模擬，引擎用自家 canvas bloom／tilt-shift，`bloom`／`vignette` 數值只作倍率（參考值 0.4／0.3）。
5. `play` 位移 0：root-motion 由引擎補（見 §8）。
6. `atlas_events` 幀名為 `<icon>_NN`；`icon_<id>.png` 靜態圖已喺 atlas 內（引擎未用）。
