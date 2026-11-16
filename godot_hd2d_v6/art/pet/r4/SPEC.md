# 團絨步行美術 r4 — parent 內審／實景候選，未接入

2026-11-16 23:54 HKT（Asia/Hong_Kong UTC+8）。只做美術；沒有改工程、PC、場景、鏡頭、引擎或速度，沒有發訊、消費或 APK。

## 判定先行

**可交 parent 親看，再作工程實景候選；不可稱遊戲已無滑／已驗收。**
側向完整循環的兩次新落腳均向前 **6 wu**，不是 r3 的 −6 / +18。每隻腳有固定身份，跨圈支撐也有驗；原來「短腳做不到對稱步」的結論不成立，問題是把正面左右腳的 18px 間距錯當成側向前後跨距。重畫下緣短腳後，6px 接觸跨距已足夠。

尚有限制：6幀離散貼圖只能在採樣時刻精確鎖 X，幀間平滑 root 的量化微滑 <2 wu；front/back 仍只係投影。48wu/s = 24fps / 4圈每秒，偏急，必須實景看，沒有擅改速度。遠腳 passing 時會遮到只剩 1 個可見足底像素；這是固定遠近遮擋，不是腳換身份。低比例畫面可讀性未驗。

## 必看檔

1. `previews/contact_side_walk_r4_8x.png` — 6 張獨立圖的聯絡表
2. `evidence/side_feet_16x.png` — 真正生產色小腳輪廓
3. `evidence/side_identity_visible_16x.png` — **debug 假色，非素材**：橙＝R近，紫＝L遠；固定深度次序
4. `evidence/side_complete_world_trajectory.png` — 同時追兩腳，完整圈及跨圈
5. `evidence/side_travel_grid_2wu_6x.png` — 固定世界格線逐時刻 travel，t0..8
6. `previews/side_treadmill_20wu_s.gif`／`side_treadmill_48wu_s.gif` — 身體固定、格線移動，內審節奏
7. `previews/side_travel_20wu_s.gif`／`side_travel_48wu_s.gif` — 3 圈 travel；片尾 RESET 是畫布重置，**不是一步**
8. `compare/r3_vs_r4_side_4x.png` — 同尺度；r3／r4 身體、臉、光球不變

GIF／聯絡表不是遊戲實錄、不是 APK／GPU 驗收。

## 像素與造型

- 生產圖只在 `frames/r4/`：21 張獨立 64×64 RGBA PNG；每方向 walk6 + idle1。
- side 朝右；向左可 flip_h。R_near 永遠近層亮橙，L_far 永遠遠層深橙，**不隨支撐腳切換深度層**。R/L 是本包持久追蹤標籤，並不聲稱源圖提供解剖學左右證據。flip_h 後仍是同兩腳標籤，僅畫面左右反轉。
- side 源身體 **行0–57完全相同**，沒有身體 bob、拉伸、整張平移、換臉或光球擺動。只重畫行58–62的小腳及肚底遮擋。
- 腳章最寬6px、最高5px；接觸雙腳中心只隔6px，passing 會投影重疊。近腳亮面、遠腳無亮面；深度層不交換。
- side 每幀12色，均來自既有 side 源圖；alpha僅0/255，nearest，不加抗鋸齒。front/back 原圖逐byte保留（back只用既有子色盤，不擅補新色）。
- **side_idle_01＝新side_walk_01**（雙支撐 contact）。不再要求等於舊側面圖，亦不使用正面 idle。front_idle 保持現認可原檔，SHA見清單。back全數沿用r3。
- 沒有獨立起步／停步過渡。硬回contact可能有相位 snap，屬後續實景項，不冒稱已解。

## Pivot／座標（勿混淆三種量）

- 畫布保持64格、原 `centered=true`、`pixel_size=1` 的尺寸慣例；不帶新增 offset。**不要求工程改位置**。
- 像素欄／行 index 是0..63；表中 x 是四個足底像素的欄 index 平均，如34.5。真正在貼圖邊界座標的足底中心是 `x+0.5 =35`。
- 中心貼圖原點是 (32,32)，像素邊界座標；因此水平世界座標 `worldX = rootX + x_index_mean +0.5 −32`。r3採 index直接減32有固定−0.5偏差，但不影響其 −6/+18 錯誤。
- 保留舊包 layout anchor `(32,61)`，**不是足底**。新舊接觸腳底行都是62，底邊是63，比anchor低2px。若沿現有 Sprite3D center_y29，足底邊世界y=−2（舊圖亦如此），不能寫成新包已貼世界y0。地面線只係證據圖統一的足底平面，沒有驗3D實景地表。
- 不可把聯絡表、假色或 layers 當 Sprite3D 貼圖；64單圖避免原有按texture尺寸計影的問題。

## 完整循環驗算

12wu／圈，6幀，root每幀+2wu。接觸點：

- R落腳 `t=0`: root0 +35−32 = **3wu**
- L新落腳 `t=3`: root6 +35−32 = **9wu**，相對前一落腳 **+6**
- R下圈落腳 `t=6`: root12 +35−32 = **15wu**，相對前一落腳 **+6**

R在t0..3（含換腳雙支撐）各幀的x index=34.5,32.5,30.5,28.5，world全為3。
L在t3..6（含06→下圈01）同樣34.5,32.5,30.5,28.5，world全為9。
L在上一圈t−3..0也全為−3。因此不是只鎖兩個分段、跳過跨圈，也不把遠腳換名成近腳。

新落腳接續前進6wu，不是同一隻腳瞬移6wu；該腳先離地，swing worldX單調前進，再落下一點。
所有grounded相鄰幀及三圈資料見 `MEASUREMENTS.json`、`evidence/feet_identity_trajectory.csv`。實心線=同一腳的grounded區間，虛線=swing，綠圈=新footplant。

### 兩腳逐幀表

G＝腳底在共同足底平面（sole行62）；S＝swing。x/y為pixel index，不是整張最底行mid。worldX以像素中心換算。

|幀 / t|root|R近 x,y|R狀態|R worldX|L遠 x,y|L狀態|L worldX|
|---|---:|---|---|---:|---|---|---:|
|01 / 0|0|34.5,62|G 新落|3|28.5,62|G 前圈末|−3|
|02 / 1|2|32.5,62|G|3|30.5,60|S 抬2|1|
|03 / 2|4|30.5,62|G|3|34.5,61|S 降1|7|
|04 / 3|6|28.5,62|G 離地前|3|34.5,62|G 新落|9|
|05 / 4|8|30.5,60|S 抬2|7|32.5,62|G|9|
|06 / 5|10|34.5,61|S 降1|13|30.5,62|G|9|
|01' / 6|12|34.5,62|G 新落|15|28.5,62|G 跨圈末|9|

遠腳在02的4個足底像素只有1個可見（其餘被近腳／身體遮擋），03可見3個；近腳仍有完整4個。所有grounded足底均4個可見。`side_identity_visible_16x.png` 用**實際合成所有權mask**證明，不靠同色像素相等假推身份。分層原圖只放 evidence，不是工程多層要求。

### 連續時間限制：沒有用0掩蓋真實量化

上面0wu只係**採樣幀間**的X抵銷。幀保持時若root連續走：設距離相位 `d=2k+u, 0≤u<2`，第k張的stance localX不變，則腳世界X是 `plantX+u`，到下一張退回plantX。因此鋸齒微滑幅度 **<2wu**，不是任意時間0。
本輪無修改工程，不能宣稱自動做到subpixel連續足底鎖定，也沒有靠全身後移補償。實景比例可能把2wu量化看成正常像素步進，也可能仍看得出；要parent／工程做實景判斷。

只在**side純X、原pixel_size1**幾何上可作這個採樣鎖定判定。斜向、fixed-Y billboard相對camera yaw／投影、Z向與真實地面均未驗。front/back只是既有抬腳＋遮擋，沒有鎖Z。

## Front/back 保留，不擴scope

所有14個檔案byte不變，包括front idle＝現用idle。
兩腳index表（front/back同幾何；只是背面五官與腳踭色不同）：

|幀|L x,y／grounded|R x,y／grounded|
|---|---|---|
|01|23,62／true|40,62／true|
|02|23,62／true|42,60／false|
|03|23,62／true|41,61／false|
|04|23,61／false|40,62／true|
|05|25,60／false|40,62／true|
|06|24,61／false|40,62／true|

這兩向不作world footplant表，因根沿Z不能套side X公式假稱鎖地。

## 距離時鐘（規格，沒有實作）

`anim_fps = frame_count * actual_XZ_speed / stride = 6*speed/12 = speed/2`

|速度wu/s|fps|一圈秒|步數/秒（兩落腳/圈）|
|---:|---:|---:|---:|
|17|8.5|0.706|2.83|
|20|10|0.6|3.33|
|24|12|0.5|4|
|48|24|0.25|8|

48是8次踏地/秒，偏碎急；**沒有改roam20或manual48**，沒有把快速度鎖回10fps（那會多滑）。GIF以10ms粒度交替40/50ms表達24fps，6幀總250ms；20版每幀100ms。
起停、轉向、hold應看實際位移，不用timer假走。本輪只交貼圖／metadata，工程由parent親看後再交遊程。

## 自檢、回歸與權利

`QA.json`機讀：21張64格；二值alpha；body行0..57相同；side無新色；front/back byte一致；兩次plant +6/+6；含跨圈每隻腳grounded相鄰採樣殘餘0。已看side／front／back聯絡表、腳放大、身份遮擋圖及travel序列；這不等於遊戲中動態／手機驗收。

觀感修正：r3兩腳分居兩端的橫向站姿已改為側向投影重疊；現在接觸→遠腳收起→遠腳前落→近腳收起，沒有全張跳。代價是腳集中肚底、passing遠腳很細，不能保證低倍率看清。body／臉／光球未退步；side舊contact腳輪廓是有意放棄的項，不冒稱位元組一致。

權利：來源已定位，**權利未獨立核證，不得推定可商用**。詳 `RIGHTS.md`／`SOURCE_MAP.md`。

不填憑感覺完成百分比、不報假評分。反省：先按側面投影建立持久腳身份，再驗整圈落腳位置；段內0並不等於步態正確。
