# QA 開放項 — interior_room1_art_r1

時間：2026-11-22 09:34 Asia/Hong_Kong UTC+8  
狀態：首切候選已對齊 loader 合同 schema，並做了一輪全房構圖／材質密度修正。**未鎖、未引擎驗、未手機驗。**

## 已自行看過（仍非驗收）

- 資料夾根為 `shell.glb` + `textures/` + `pack.json`；無 project.godot、無 symlink。
- `pack.json` 對齊 HD2D_LOADER_CONTRACT.md：unit、transform、slots 陣列（六原 key）、collision aabb 列表、walkable／occlusion mesh 空字串、door_anchor。所有 locked 均為 false。無花園空間測點。
- shell.glb 根節點無隱藏 transform，y=0，不含寵物與預覽 apron。
- 牆裙 64×256，灰泥 texel 比上一版密；hero／shell 可見床、毯、桌、窗、架；燈在左窗前（色較深，對裙腳對比仍弱）。
- 19:9 與俯視預覽已更新，標明非 Godot Mobile。

## 開放／待親審

1. 尺與布局仍是候選。`candidate_local` 不得當已鎖座標，不得寫入 save。
2. 未在 Godot 4.7.2 Mobile／Low 開過。stager 複製到 `res://hd2d_stage/room1/` 後的 import（glB embedded images、nearest）尚未跑。
3. 正式戶外門 anchor 未鎖。室內 door_anchor 為候選，不取代 675 recess。
4. 燈在 hero 已入畫，但帽頂偏暗、貼近裙腳，對比較弱；若親審要求更清楚，可再升高／提亮（key 不改，仍 locked:false）。
5. 窗光仍粗（不透明日光片＋玻璃混合）。
6. 床／燈／桌為佔位體積，不是 13 件最終造型。
7. `walkable.mesh`／`occlusion.mesh` 仍為空，且 locked:false；未授權可行走或用室內殼去遮戶外。
8. 預覽 apron 不在 glb。手寫 glTF 未跑官方 validator。
9. 權利未核證，見 RIGHTS.md。
10. 不宣稱已整合、95%、手機通過、all PASS。
