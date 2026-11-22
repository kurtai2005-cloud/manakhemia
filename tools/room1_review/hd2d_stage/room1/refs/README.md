# interior_room1_art_r1

Room1 首切室內美術包（候選，全部 `locked: false`）。

對齊只讀合同 `/home/box/keep/遊美/hd2d_loader_contract_0c2c50f04b5c/HD2D_LOADER_CONTRACT.md`（7075 bytes，SHA-256 `527b0cd25424d89d4f33f2c57173aa2bd565d80f5d020502bbcc8bda891eb8e7`）。

## 工程要載的檔（資料夾根，無 project.godot，無 symlink）

- `shell.glb` — 自包含真 3D（Y-up，地面 y=0，1 unit = 1 wu = 1 Godot unit，無隱藏縮放）
- `textures/` — PNG（亦已嵌入 GLB）
- `pack.json` — 合同 schema：`unit`、`transform`、`slots[]`、`collision`、`walkable`、`occlusion`、`door_anchor`

slot key 僅 bed／rug／table／lamp／wall／window。座標只以 `candidate_local` 出現，且每槽 `locked: false`（本切 loader 忽略座標；之後只在該槽亦為 locked:true 才讀）。不要寫入 save。

## 其餘（給美術／親審，不是 loader 入口）

- `SPEC.md` / `RIGHTS.md` / `QA.md` / `HANDOFF.md`
- `data/art_notes.json` — 房間候選尺、相機候選、走道意圖
- `previews/` — 19:9 與俯視真 3D 預覽（CPU raster，非 Godot Mobile）
- `tools/` — 生成腳本；不改工程 repo

寵物與 19:9 近景 apron **不在** shell.glb。
