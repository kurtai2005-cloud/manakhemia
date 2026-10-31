# MILESTONE 1 — 團絨五官 rig（俾遊程先接）

日期：2026-10-31（HKT）。根目錄：`art-pet/sprites/tuanrong/motion/liveliness/`

## 已交（3 form：sprout／radiant／soft）
- `idle_noface`（4 幀）、`walk_noface`（6 幀）——其實**全部 33 個 clip 嘅 `_noface` 已一齊出**（見下面數量）
- 眼層：8 款 × gaze（L、CL、C、CR、R＋U、D；閉眼款只 C）× 左右眼；口 8 款；燈泡 base＋glow
- 錨點：`CLIPS.json → clips[].anchors[form][幀]`（frame 左上角 px）＋鏡像 `face_anchors.json`
- 疊法：`FACE_RIG.md`

## 檔案數量
| form | noface 幀 | faceov | 新 clip 完整幀 | kit 散件 | atlas |
|---|---|---|---|---|---|
| sprout | 147 | 147 | 51 | 86 | atlas_sprout_live.png |
| radiant | 147 | 147 | 51 | 86 | atlas_radiant_live.png |
| soft | 147 | 147 | 51 | 86 | atlas_soft_live.png |

## piece 尺寸／pivotPx
- sprout: eyes 7x6 pivot (3, 3)；mouth 5x3 pivot (2, 0)；bulb 5x5 pivot (2, 2)
- radiant: eyes 9x8 pivot (4, 4)；mouth 7x4 pivot (3, 0)；bulb 11x11 pivot (5, 5)
- soft: eyes 9x8 pivot (4, 4)；mouth 7x4 pivot (3, 0)；bulb 7x7 pivot (3, 3)

## 路徑
- `atlas_<form>_live.png/json`
- `layers/<form>/<clip>_NN_noface.png`／`_faceov.png`
- `kit/<form>/eyes_*.png`、`mouth_*.png`、`bulb_*.png`
- `preview/<form>/A1_walk_gaze_8x.gif`（walk＋gaze 示範）

