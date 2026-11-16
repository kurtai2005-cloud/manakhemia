# Runtime wiring（唔係獨立美術檔）

呢個包入面嘅 texture／shader／preset **唔係即插即用**。接受外觀靠凍結基準裏面嘅場景腳本綁定。

必需（喺凍結 zip `godot_hd2d_v6/` 之內，今次冇複製出嚟改）：

- `scenes/art_depth.gd` — 每幀綁 GroundInner / GroundOuter / NearLawn／tuft 材質；夜 fill、macro／outer、gain。
- `scenes/capture.gd`、`scenes/capture.tscn` — **遊程擁有**。版本行寫住 `hd2d v6.18-pilot vc27`。呢個包同呢次工作都唔准改。
- `scenes/prop_bump.gd`、`data/prop_bump.json` — **遊程擁有**，CREDITS 寫明照收唔改。

測試用 19:9 開機 override（唔係遊戲預設、唔好寫入 `project.godot`）：

- `capture_refs/override_19x9.cfg` SHA-256 `b2e6782d92e20e3be91c5205e130e1b55af25fe7edf7824f57bffaeb05175d11`
- 內容只有 viewport 540×1140。開機前複製做 `override.cfg`，用完刪走。
- 官方 `project.godot` 仍然係 1080×1920。Movie Maker 會喺開機鎖定解像度。

引擎：Godot 4.7.2-stable。已接受測試用 `--rendering-method mobile`。引擎本身唔喺呢個包入面。
