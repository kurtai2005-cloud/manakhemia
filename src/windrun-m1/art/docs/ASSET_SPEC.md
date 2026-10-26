# 資產規格（俾遊程）v0.1 — 窄樑貓＋苔坡垂直切片
根目錄：`/workspace/game-design/art-wind/`（暫唔入 repo）。重跑：`cd tools && python3 build_palettes.py && python3 build_narrowcat.py && python3 build_mossy_slope.py`（Pillow＋numpy；固定亂數種子，輸出可重現）。

## A. 野靈「窄樑貓」`sprites/narrowcat/`（id=`narrowcat`，64x64，朝右）
| 檔案 | 說明 |
|---|---|
| `frames/spirit_narrowcat_<state>_<NN>.png` | 單幀 64x64 RGBA，共 20 幀 |
| `spirit_narrowcat_atlas.png` / `.json` | 圖集 2048x68，padding 2、extrude 1；JSON＝Pixi/Phaser hash 格式＋`animations`（frames／fps／loop）＋每幀 `pivot`＋`meta.anchor_px=[32,61]` |
| `spirit_narrowcat_sheet.png` | 6 列（run/idle/skill_charge/skill_burst/win/lose）×最多 6 欄，無 padding |
| `spirit_narrowcat_preview_8x.png/.gif` | 8x 預覽（深綠底）／全 state 動畫 |
| `contact_sheet.png` | run 6＋idle 4，8x，無字（相似度檢查） |
| `palette_used.json` | 32 色統一色盤＋本隻用色（21 色） |
| 動畫 | state｜幀｜fps｜loop：run 6｜12｜✓；idle 4｜6｜✓；skill_charge 2｜8｜✗；skill_burst 2｜12｜✓；win 4｜8｜✗；lose 2｜3｜✓ |
- **錨點／pivot**：(32,61)＝腳底中心（腳底最後一行 y=60）。跳躍／技能位移已烘入幀，引擎唔好再 offset。
- **顯示**：6x，Nearest；螢幕腳底 y＝(track.y 320 + 150)×2＝940。blob shadow 由引擎生成（見 STYLE_GUIDE §3）。
- **速度同步**：run 播放 fps＝12×(實際速度／該野靈基準速度)，限 0.6–1.4；適性乘風用上限、陌路用下限。
- **技能（疾風衝）時間軸**：charge 2 幀（0.25s）→ burst loop（技能 3 秒）→ 結束回 run。光環已烘入 sprite；引擎再疊 bloom／點光 #4FD0C8。
- **幀對照表**：run_01–06 循環一步（一個週期＝0.5 s@12fps）；idle_01 站、02 吸氣、03 眨眼耳後、04 呼氣；win_01 蹲、02 起跳、03 頂點（星）、04 落地；lose_01–02 垂頭＋汗滴。

## B. 苔坡賽道 `tracks/mossy_slope/`（全部可橫向無縫 tile，寬 1024）
| 檔案 | 尺寸 | 模式 | 螢幕 Y（邏輯，2x 顯示） | z（低→高） | 視差 | 說明 |
|---|---|---|---|---|---|---|
| `sky_far_day/dusk/night.png` | 1024x540 | RGBA 不透明 | 0 | 1 | 0.05 | 天空、星／日月、雲、兩層遠山；時段切換換貼圖 |
| `lightmap_cool.png` | 1024x540 | RGB | 0 | 2 | 0.2 | 月光束，ADD，夜 0.55／黃昏 0.12 |
| `mid.png` | 1024x320 | RGBA | 160 | 3 | 0.35 | 遠杉、近樹剪影＋燈籠線（12 盞燈籠，位置見 emissive_mid）|
| `lightmap_warm.png` | 1024x320 | RGB | 160 | 4 | 0.35 | 燈籠暖光，ADD，同 mid 對齊，強度夜 1／黃昏 0.75 |
| `emissive_mid.png` | 1024x320 | RGBA | 160 | （bloom 輸入） | 0.35 | 只有燈泡，供 bloom／發光 pass |
| `track.png` | 1024x220 | RGBA | 320 | 5 | 1.0 | 苔坡＋跑道；**野靈跑道線 y=150**；上緣透明 |
| `lightmap_track.png` | 1024x220 | RGB | 320 | 6 | 1.0 | 路面暖光池，ADD，夜／黃昏 |
| `lightmap_track_moon.png` | 1024x220 | RGB | 320 | 6（可選） | 1.0 | 路面月光斑（冷），ADD，可選 |
| `fx_grass_shred_01–04.png`＋`_sheet.png` | 24x24 | RGBA | 腳底 | 8 | — | 草屑粒子 4 幀，8–12 fps，單次；**錨點 (12,22)＝腳底**；朝後飄（螢幕左）；每步踏地觸發，可同時 2–3 個 |
| `fore.png` | 1024x540 | RGBA 半透明 | 0（底貼 540） | 9 | 1.6 | 前景草葉＋16 粒螢火；建議層 α0.92，強模糊 |
| `mid_lowfx.png`／`fore_lowfx.png` | 同上 | RGBA | 同上 | 同上 | 同上 | **低檔預模糊版**（wrap-aware，仍可 tile） |
| `vignette.png` | 960x540 | RGBA | 全屏 | 最頂 | — | 低／中檔暈影，拉伸至全屏 |
| `style_board_mossy_slope.png` | 1920x2160 | RGB | — | — | — | 風格板：夜（主）＋日＋黃昏＋夜無後處理對照＋夜技能爆發 |
| `style_board_mossy_slope_{day,dusk,night,night_nopost,night_skill}.png` | 1920x1080 | RGB | — | — | — | 單張 |
- **tile**：全部層寬 1024，左右邊接合（已檢查接縫）。螢幕寬 1920 需並排 1–2 張（2x 後 2048 px／張）。
- **時段切換**：sky_far 換圖；其餘層用 tint＋brightness（STYLE_GUIDE §3）。燈籠常亮，白天 warm 光圖強度 0。
- **分段**：1 段＝200 m；M1 只有苔坡，其餘地形用同尺寸／命名 `<layer>.png` 放 `tracks/<terrain>/`，換段時換貼圖＋crossfade 1 s。
- **碰撞／邏輯**：無；跑道線 y=150 只係視覺基準線，賽道上下拉鏡由引擎決定。

## C. 其他
- `palette/`：`spirit_palette.json/png`（32 色）、`env_palettes.json`（苔坡完整＋5 地形主色＋技能光色＋適性色）、`mossy_palette.png`。
- 工具：`tools/wind_palette.py`（共用色盤）、`build_palettes.py`、`build_narrowcat.py`、`build_mossy_slope.py`（`--board-only` 只重出風格板）。

## D. 已知問題／待遊程回饋
1. 後處理只係 Pillow 模擬，實裝參數要按引擎實測微調（§5 三檔數值係起點）。
2. 野靈 run 循環係「飛躍式」，尚未加地形腳步粒子觸發點表（建議遊程按 run_02／run_05 落地幀觸發草屑）。
3. fore 草葉較稀、形狀簡單（強模糊下 OK）；螢火唔會閃，可由引擎做 α 呼吸。
4. 適性圖示、HUD、換棒頭像框未做（5.4a／1.2）。
