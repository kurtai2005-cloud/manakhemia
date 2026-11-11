# QA：3D 花園 H1.6（`56d04d14`）

唯讀 `code/glimmer-3d-h1` @ `56d04d143242c0b2051975c5e8053e7141536142`，tree `d385f2c11c59b74f203550e30cd1483b91eb259e`。APK 字串 `versionCode` 13、`versionName` `1.4.6-3d`（`native/android/README.md:47`）。冇改 code branch，冇 merge。mid／high 嘅 p95 按話暫停，冇再獨立量。

截圖：`QA/shots-3d-h16/`。掃描：`QA/scan-v10-27.json`。

## 預設畫質

`detectQuality`（`garden3d.js:457–468`）冇 query 時回 `low`／`want: false`。16 核都係 `reason: "auto"`，唔再自動 high。4 核係 `lowend`。`?3d=1` 同樣 low。`?3d=high`／`mid` 先至 `want: true`。

瀏覽器（呢部機 4 核）：

| 情況 | 畫質 | 3D |
|---|---|---|
| 冇 query | low | 關 |
| 存檔 high、冇 `qManual` | low | 關 |
| 存檔 high、`qManual=1` | high | 開、ready |
| `?3d=mid` | mid | 開 |
| `?3d=high` | high | 開 |
| 當頁 `setQuality('mid'/'high')` | 跟住變 | 開 |

開發者掣寫 `setQuality(q, { manual: true })`（`garden3d.js:1420–1422`、`:1225`）。手動旗先可以喺下次冇 query 時留喺 mid／high。

## low 4× CPU

`Emulation.setCPUThrottlingRate` 4，預設 low（`on()` false）。每輪丟開頭 30 幀，其餘 ≥600。

| 輪 | n | p50 | p95 | p99 | long task |
|---|---:|---:|---:|---:|---|
| 1 | 619 | 0.6 | **4.5** | 8.1 | 1（67ms） |
| 2 | 614 | 0.7 | 4.3 | 8.6 | 0 |
| 3 | 612 | 0.5 | 2.9 | 4.4 | 0 |

三次 p95 都 ≤4.5。long task 唔係零：第一輪有一條 67ms。`autosaveSec` 係 5（`data.js:538`），存檔搬去 `requestIdleCallback`（`main.js:180–181`）之後仍然可以係主線程長任務。

`e2e-3d` 短窗 low p95 3.3（佢順手印咗 high 6.6、mid 5.7，我哋冇再拆）。

3D 開住（`?3d=high`）數 `drawPetBeh`：形態 `bright` 兩秒 **0** 次。形態 `moon` 兩秒 **21** 次。見下面 P2。

## 離線補時

`SIM.catchUp`（`sim.js:442–447`）先把 `lastSeen` 推到上次 `simAt`，空隙細過 `offlineStallSec` 2 秒就跳過。四條瀏覽器路（rAF stall、`pageshow`、`focus`、Capacitor `appStateChange`）各跳 1 小時，結果一樣：飽腹 93.4、便便 0、成長 4600、光粒 +1。再觸發一次（包括 pageshow 加 focus）數字唔變。時鐘倒行 10 小時：冇拋錯，飽腹維持 100、成長維持 1000、光粒 0。

同「一直開住」`SIM.advance` 比較（跳跳期、成長秒 1000、需求滿）：

| 離開 | 飽腹差 | 成長差 | 便便差 | 光粒差 |
|---|---:|---:|---:|---:|
| 10 分 | 0 | 0 | 0 | +1 |
| 1 小時 | 0 | 0 | 0 | +1 |
| 8 小時 | 0 | 0 | 0 | +8 |
| 24 小時 | +20.8 | +43860 | 0 | +10 |
| 48 小時 | +20.8 | +43860 | 0 | +10 |

≤8 小時，飽腹、成長、便便同開住一樣。光粒係離線禮物（`sim.js:474`，每小時 1、上限 10），開住唔會送，呢個差係規格。

24／48 小時：離線飽腹停喺保底 20（`sim.js:384–386`，`offlineNeedFloor`），開住會跌到 0。離線成長加滿 24 小時（`offlineGrow`，`sim.js:411–412`）；開住跌到不適之後 `step` 唔再加成長（`sim.js:391`），所以離線成長更多。便便兩邊都頂到 3。有效時間 E 喺 24 小時係 12 小時（8 小時全速 + 16 小時 ×0.25，`sim.js:55–60`）。呢啲差跟註解，唔當重複補時。

夢境同掃描喺新 `sim.js` 上重跑，差 0（下面）。兩次 `catchUp` 冇再加光粒，所以夢境／平衡冇被補時路徑重複計。

## P0

冇。

## P2 — 非 dir4 形態 3D 開住仍然畫 2D 寵物

`preparePet3d`（`render.js:1017–1022`）只對 radiant／bright 跳過 `drawPetBeh`。其他形態 key 包含 `b.frame`，幀一變就喺可見嘅 L2 canvas 畫一次。`moon` 兩秒 21 次。L2 之後仍然貼上主畫面，所以會同 3D billboard 疊一隻 2D 寵物。

修法：精靈畫去離屏 canvas 再交 `setPetSprite`，唔好傳可見嘅 L2 context 入 `drawPetBeh`。

## P2 — low 有一條 67ms long task

p95 已過。3 次入面 1 次有 long task 67ms。存檔每 5 秒（`data.js:538`）經 `requestIdleCallback` 跑 `G.save`（`main.js:180–181`），idle callback 一樣算長任務。

修法：存檔再拆細，或者 long task 觀測排除已知嘅 idle save；玩家體感就係每 5 秒可能頓一頓。

## P3 — 412 同 768 星星數同心聲 chip 疊幾 px

散步掣同朋友掣唔疊。`#grains` 同 `#s12chip` 喺 412 疊 83×7、768 疊 95×8。chip 被釘喺 `left:302px; top:10px`（`hd2dui.js:78`），寬屏會撞到頂欄星星。

修法：chip 改跟 `#grains` 嘅底邊再落一格。

## 回歸

清屎：細佬盒包住，20／20 回 `poop` 而且清到。撳細佬本身 20／20 回 `kid`，屎冇變。朋友影子 `alphaTest` 0.1、`maxA` 0.45，`friend-shadow.png` 見到紫色剪影。

360×640 穩定之後朋友同散步並排（x 237 同 286，同一 y），重疊 0。768×1024 兩粒唔相交。390 亦係 0。寵物喺畫面、`flipY` true。天空亮度約 220，冇黑底。

10 分鐘：寵物 z −125…91、細佬 z −125…99，兩邊腳下碰撞 0、出界 0、2 秒冇進展 0。

`?3d=0`：`on()` false、quality low、畫面中位亮度 164、暗像素 0。`fallback-2d.png` 係完整 2D。橫向 844×390 顯示「請轉直向」。

夢境差 0：cap 47、viol 0。勤力 200／84／80／92；普通 200／84／81／92；早起 200／84／81／92；餵食狂 200／84／80／91；夜貓 200／83／80／90；疏玩 199／147／132／179。

`scan-v10-27`：16／16，`lockDiff` 空。火苗 14、柔光 10.92、微塵 4.95、螢絨 5.47、晶角 15.32、月眠 18.72、夜貓月眠 82.4、疏玩 CQ 中位 18。星碎：疏玩 19、勤力 28、普通 22、夜貓 25、早起 23、餵食狂 23。商店價錢加總仍然 190（`house.js:17–25`）。

Unit：35 檔 exit 0，末行加總 **2393／0**（`garden3d` **98**、`sim` **103**）。

e2e：`e2e-3d` **75／0**、`e2e-6b` **64／0**、`e2e-6d` **126／0**。

今次冇 P0，冇 P1。
