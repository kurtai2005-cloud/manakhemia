# HANDOFF — interior_room1_art_r1

時間：2026-11-22 09:47 Asia/Hong_Kong UTC+8  
狀態：**本輪封存。** Parent 已親看新 hero：整房／門／床可讀，有實際改善。**不交用戶、不鎖定。** 全部 pack.json locked:false。不改 675 pet、不改工程、不翻 locked、不寫 save、不另擴資產。先等遊程獨立 review fixture 的 Godot Mobile 實圖再調。

回退：`/workspace/interior_room1_art_r1_rollback_20261122_0934/`（keep 同名）。  
包：`/workspace/interior_room1_art_r1/`　keep：`/home/box/keep/interior_room1_art_r1/`  
SHA 清單：`data/SHA256_ARCHIVE_20261122_0947.txt`

## 相機／bbox／上下留白（已記 data/art_notes.json）

- Before（被拒 09:34）：eye [0, 48, 170]，target [0, 28, −20]，vfov 50，apron true。1080 寵物 bbox 寬 63.2%、高 37.7%。
- After（現行 CAM_HERO）：eye [−55, 48, 400]，target [10, 40, −20]，vfov 46，apron false。輕微 −X cutaway。寵物世界尺未改。
- After 1080×2280 實量寵物 bbox：x 353–647，y 1035–1412，295×378 px，**寬 27.3%、高 16.6%**。
- 上下留白（hero 與 hero_shell 相同，不含預覽 caption）：內容 y 585–1488（904 px，佔全框 39.6%）；上留白 585 px（25.7%）；下留白（caption 之上）709 px（31.1%）；預覽 caption 82 px（y 2198–2279，只在離線圖，不進引擎）。
- Parent 已決定：不因填滿 19:9 盲目加高房間至 200+，亦不再離線反覆調相機。

## 寵物腳底（給工程，不改 675 pet）

預覽 `pet_quad` **只用** `center_y=31` 作為 64×64 畫布中心。`center_y` 已是 `node_y 29 + offset.y 2`，**沒有再加一次 2**。畫布世界 y = −1..63。所用 r4 idle 幀最後實心列 row 62，世界底緣 **y=0.0**。工程請用官方 r4 Sprite3D：pixel_size 1、64×64、node 在 y=29、offset.y=2、腳在 y=0。**不要**把 node 設成 31 又保留 offset.y=2。預覽寵物不在 shell.glb。

## 牆影與光材質來源（給 Mobile fixture）

- 離線預覽把牆（及天花）`receive_shadow=False`，只因為 raster 高度圖陰影在垂直牆打出橫線。**這不是正式美術決策。** 此旗標沒有寫進 glTF。引擎必須有形態合理的柔陰影（牆／地／傢俱），**不可把關牆影當成修好。**
- 離線預覽光在 `tools/build_room1.py`（light_dir 指向光源 (−0.18, 0.78, −0.60)，ambient (0.30, 0.28, 0.25)，key (1.08, 0.94, 0.72)，fill (0.22, 0.26, 0.32)）＋ `raster3d.py` Lambert／平面影。圖已標明非 Godot Mobile 驗收，只作構圖／比例／反照參考。
- Fixture 載入 `shell.glb` + `textures/` + `pack.json`（locked:false，不能正式消費）。材質以 glb 內 PBR＋14 張 PNG 為準。燈光以正式 67519344 Godot Mobile 場景環境／日光／補光／陰影為準，不要把離線 raster 光或花園 `lights.json` 當成室內鎖定。詳見 `data/art_notes.json` 的 `review_fixture_sources`。

## 下一步

等真引擎回圖再調。本封存步未重出 glb／貼圖／預覽。


---

Previous handoff:

# HANDOFF — interior_room1_art_r1

時間：2026-11-22 09:42 Asia/Hong_Kong UTC+8

## 本輪（相機／牆／地板，親核 bbox）

回退點：`/workspace/interior_room1_art_r1_rollback_20261122_0934/`（keep 同名）。全部仍 locked:false。

**診斷：** 上一張 hero 真正用的是 `build_room1.py` 的 `CAM_HERO` eye=(0,48,170) target=(0,28,−20) vfov=50，並在 `render_view` 自動加了 preview apron。1080 實量寵物 bbox 佔寬 63.2%、高 37.7%。不是新全房構圖。牆橙黃滴紋來自 675 plaster 磚＋陰影圖在垂直牆量化出橫線。

**After 相機（已寫入 data/art_notes.json）：**
- before: eye [0, 48, 170], target [0, 28, −20], vfov 50, apron true. pet 63.2%×37.7%
- after: eye [−55, 48, 400], target [10, 40, −20], vfov 46, apron false. 輕微 −X cutaway 以看見右牆門正面（純正面只會看到門的邊）。
- 1080×2280 實量寵物 bbox：x 353–647, y 1035–1412，295×378 px，**寬 27.3%、高 16.6%**（目標高 15–23%）。寵物世界尺未改（64、center_y 31、offset 2）。
- 框內：左牆、右牆、地板近邊、右側門正面、整張床、枱、窗、架、燈。無 apron。

**牆／地板：** 改為低對比暖灰泥（不用 675 滴紋磚）；木裙腳＋天花木樑。預覽關掉牆面接陰影（陰影圖在垂直牆會打出橫線）。地板改寬板、縫約 2 wu。

**未完全滿足之處：** 19:9 畫面上下仍有大塊空帶。在房間 128×148×108、寵物世界尺不變、bbox 高要 15–23% 的條件下，房間垂直張角大約只有 FOV 的一半。若要鋪滿 19:9 又不放大寵物，需要明顯加大候選房間（約高 200+、更深）。本輪沒有擅自改房間尺。

預覽：`previews/room1_19x9_hero.png`、`room1_19x9_hero_shell.png`。


---

Previous handoff:

# HANDOFF — interior_room1_art_r1

時間：2026-11-22 09:34 Asia/Hong_Kong UTC+8  
狀態：**首切候選已對齊正式 loader 合同，並完成一輪構圖／密度修正。** 全部 locked:false。不改 675 原檔、不改工程、未把 locked 翻 true、未把正式座標寫入 save。

## 合同

只讀：`/home/box/keep/遊美/hd2d_loader_contract_0c2c50f04b5c/HD2D_LOADER_CONTRACT.md`  
7075 bytes，SHA-256 `527b0cd25424d89d4f33f2c57173aa2bd565d80f5d020502bbcc8bda891eb8e7`（已核，與宣告一致）。未改正文。指針在 `refs/CONTRACT_POINTER.txt`。

## 包位置

`/workspace/interior_room1_art_r1/`  
keep 鏡像：`/home/box/keep/interior_room1_art_r1/`

Loader 三件套（資料夾根，無 project.godot、無 symlink）：

- `shell.glb` — 120736 bytes，SHA-256 `a29777868cd214e0ef805dfabdd0f753d950242cea4bc51bb1697bf16f92bc96`。36 primitives／566 triangles／14 張嵌入 PNG。根 `interior_room1`，y=0，無隱藏縮放。
- `textures/` — 14 張 PNG
- `pack.json` — 合同 schema。`transform`／每個 slot／`walkable`／`occlusion`／`door_anchor` 皆 **locked: false**。slots 為陣列，含既有 id 與 `candidate_local`。collision 為 9 個 `{name, aabb:[x,y,z,w,h,d]}`。`walkable.mesh` 與 `occlusion.mesh` 為空字串。室內 `door_anchor.threshold_local` [61, 0, 24]，outward [1,0,0]（右牆）；**不取代** 675 外門，亦無花園測點。

藝術附註（非 loader 入口）：`data/art_notes.json`。

## 本輪美術修正

- 牆裙貼圖改 64×256，灰泥在高度方向不再被拉長。
- 燈候選位移到窗前 (−34, 0, −50)，hero 可看到；架移到後牆床上方 (28, 58, −71)，六個 slot 在 hero_shell 都讀得到。
- 窗光略暖。候選房間尺未改（128×148×108）。

預覽已重出（CPU 真 3D，標明非 Godot Mobile）：`previews/room1_19x9_hero.png`、`hero_shell`、`door_approach`、`pet_scale`、`room1_ortho_top.png`。

## 請 parent 看什麼

1. pack.json 是否符合合同（仍全部 locked:false）。
2. 構圖：六件佔位在全房 19:9 是否夠清楚；燈對裙腳對比是否要再提。
3. 牆／地板密度是否更近 675。
4. 要改尺或機位的話，仍然 locked:false，直到有人顯式鎖定。

下一步只在親審後做必要修正。不自行接工程、不打 675 門、不畫齊 13 件、不翻 locked。
