# 給遊程嘅範圍說明（檔案，唔係改你哋 HANDOFF）

時間：2026-11-16 19:50 Asia/Shanghai UTC+8

呢份係獨立說明檔，**唔好當授權去改** `keep/遊程/HANDOFF.md`、`capture.gd`、`capture.tscn`。冇 APK、冇 merge 去 main。

## 凍結基準

用已套用完成嘅 zip，唔好再打 patch：

- SHA-256 `2da14bc862b491906c1fbec80506af2dfa12152e0359080eba59d4c406e0e6a4`
- 只讀副本：`/home/box/keep/godot/hd2d-pilot-v6/vc27_approved_baseline_r1/hd2d-vc27-rear-ground-r1-candidate.zip`
- 原核對副本（今次冇覆寫）：`/home/box/keep/godot/hd2d-pilot-v6/vc27_rear_ground_r1/hd2d-vc27-rear-ground-r1-candidate.zip`

重建順序同雜湊見同包 `PATCH_MANIFEST.md`。

## 遊程擁有、呢個美術包唔改

- `scenes/capture.gd`（版本行：`hd2d v6.18-pilot vc27`）
- `scenes/capture.tscn`
- `scenes/prop_bump.gd`、`data/prop_bump.json`

美術側關鍵綁定喺 `scenes/art_depth.gd`。新物件／材質若要同一外觀，要經現有綁定方式，而唔係當 texture 即插即用。

## 測試擷取（若遊程要對同一 19:9）

用已核對 `override_19x9.cfg`（SHA `b2e6782d…175d11`），開機前複製、用完刪；唔好改官方 `project.godot`。
