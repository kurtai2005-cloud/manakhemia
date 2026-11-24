# SPEC — interior_room1_art_r1（首切候選，locked:false）

時間：2026-11-22 09:34 Asia/Hong_Kong UTC+8

本包是 room1 的 **art-only 真 3D 室內殼 + set-A 佔位**。**不是已鎖定、不是已接入、不是 Godot Mobile 驗收。**

## 載入接口（已對齊正式合同）

只讀合同：`/home/box/keep/遊美/hd2d_loader_contract_0c2c50f04b5c/HD2D_LOADER_CONTRACT.md`（7075 bytes，SHA-256 `527b0cd25424d89d4f33f2c57173aa2bd565d80f5d020502bbcc8bda891eb8e7`）。未改合同正文。

交付為一個普通檔資料夾，**無 `project.godot`、無 symlink**。根目錄三件套，供 stager 複製到 `res://hd2d_stage/room1/`：

- `shell.glb`：單場景，Y-up，1 wu = 1 Godot unit，地面接觸 local y=0，根節點 `interior_room1` 無隱藏 translation／rotation／scale。若要變換，只寫在 pack.json 的 `transform`（現為恆等且 `locked: false`）。
- `textures/`：PNG。GLB 已嵌入同一批圖並使用自身 materials。
- `pack.json`：僅合同欄位（外加合同允許的 `slots[].id`、`slots[].candidate_local`、各 `locked`）。

`pack.json` 形狀：

- `unit`: `"wu"`
- `transform`: `{ position:[0,0,0], rotation_y_deg:0, scale:[1,1,1], locked:false }`
- `slots`: 陣列，key 恰好為 bed、rug、table、lamp、wall、window；各帶既有家具 id 與 `candidate_local`，**全部 locked:false**
- `collision`: `{name, aabb:[x,y,z,w,h,d]}` 列表（min corner + size）。體積按作者原樣，loader 不應自行縮小。
- `walkable`: `{ mesh:"", locked:false }`（尚未授權可行走 mesh）
- `occlusion`: `{ mesh:"", locked:false }`
- `door_anchor`: `{ threshold_local:[61,0,24], outward:[1,0,0], locked:false }`

**沒有任何 locked 被設成 true。** 不把候選座標寫進 save。室內 `door_anchor` 不取代 675 外門 recess，亦 **沒有** 把花園空間測點（含 (94,0,−29.5) 等）寫入本包。正式外門 anchor 仍未鎖。`transform.locked` 為 false 時，root 不應用此 transform 去搬 live garden。

房間尺、相機候選、走道意圖在 `data/art_notes.json` 與下文，不是 loader 必讀欄位。

## 單位

- 1 glTF unit = 1 wu = 1 Godot unit。
- **僅寵物幀** 1 wu = 1 art px。不要把傢俬像素換成世界單位。

## 候選房間與 set A（未鎖）

寬 128 × 深 148 × 高 108，牆厚 3。正面開放。依據：44 wu 寵物、走廊 ≥48、19:9 正面穩定取景。

| key | id | candidate_local |
|-----|----|-----------------|
| bed | bed_leaf | (28, 0, −42) |
| rug | rug_leaf | (2, 0.2, 6) |
| table | table_stump | (−46, 0, 28) |
| lamp | lamp_mushroom | (−34, 0, −50) |
| wall | wall_shelf | (28, 58, −71) 後牆、床上方 |
| window | win_curtain | (−30, 54, −71) |

室內門在右牆（+X），關閉，outward +X。進門仍用既有 cut，不穿門。

## 預覽

`previews/*.png` 為 Numba CPU 真 3D 光柵，圖上標 **offline CPU 3D raster — not Godot Mobile acceptance**。寵物是 r4 預覽實例，不在 shell.glb。19:9 近景 floor apron 只在預覽。

本輪構圖／密度：牆裙貼圖改為 64×256，灰泥在 V 向不再被拉長；燈移到窗前可入鏡；架移到後牆床上方，hero 可見六個 slot 佔位。

## 本切不做

不改 675 原檔；不改工程；不打穿 675 門；不新增傢俬 ID；不完成其餘 13 件；不把 locked 翻成 true；不宣稱已整合、95%、手機通過。
