# art/ — 遊美垂直切片素材（窄樑貓＋苔坡）
來源：`/workspace/game-design/art-wind/`（複製，唔改原目錄；全原創、程式化自製）。
- `tracks/mossy_slope/`　苔坡 4 層＋光圖＋低檔預模糊＋草屑＋暈影＋風格板
- `sprites/narrowcat/`　窄樑貓 64×64 單幀＋圖集（atlas.png/json）
- `palette/`　色盤；`docs/`　ASSET_SPEC／STYLE_GUIDE／ASSET_LOG（原文）
用於 `fx-lab.html?art=1`（`src/fx-art.js`）。規格問題見 `docs/engine-eval.md`。

## 第 2 週新增（皆複製自 /workspace/game-design/art-wind/，唔改原目錄）
- `tiles/morningmoss/`　晨苔鎮 batch2：`tilemap_town.json`（40×30）、b2／landmarks／collision tilesets（collision firstgid 545）、舊 `tilemap_corner.json`（193）、extruded 版
- `sprites/npc/{npc_elder,npc_fern,npc_registry}/`　NPC 圖集（32px，pivot (16,31)）
- `portraits/`　頭像 sheet＋ portraits.json（portrait_id＋expression）
- `adventure/`　遊策生成圖（arena／trail／舊 town）＋ placeholder tileset，`MISSING_ASSETS.json` 列明缺口
