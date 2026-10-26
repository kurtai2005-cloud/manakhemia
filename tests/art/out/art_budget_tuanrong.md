# 貼圖預算檢查結果（art_budget_check.py）

> 目錄：`/workspace/game-design/art-pet`；預算 16 MB（模式 both）；atlas 上限 1024×1024；mipmap=off

## 1. 尺寸檢查（運行時貼圖）

| 檔案 | 尺寸 | 磁碟 | 解碼 RGBA | 判定 |
|---|---|---|---|---|
| `sprites/tuanrong/motion/atlas_props.png` | 1024×64 | 2.4 KB | 0.25 MB | PASS |
| `sprites/tuanrong/motion/atlas_radiant.png` | 1024×512 | 48.8 KB | 2.00 MB | PASS |
| `sprites/tuanrong/motion/atlas_soft.png` | 1024×512 | 46.4 KB | 2.00 MB | PASS |
| `sprites/tuanrong/motion/atlas_sprout.png` | 1024×256 | 19.4 KB | 1.00 MB | PASS |
| `sprites/tuanrong/pet_tuanrong_atlas.png` | 2048×134 | 23.5 KB | 1.05 MB | FAIL 超出 1024 WARN 非 2 次冪（補至 2048×256 ＝ 2.0 MB） |

## 2. 每組（寵物）運行時貼圖總量

| 組 | 張數 | 磁碟 | GPU（解碼） | 對預算 | 判定 |
|---|---|---|---|---|---|
| tuanrong | 5 | 0.14 MB (1%) | 6.30 MB (39%) | 16 MB | PASS |

## 3. atlas JSON 檢查（frame 越界／重疊／padding）

- `sprites/tuanrong/motion/atlas_props.json` → 圖 1024×64，18 frames（尺寸種類 [(16, 16), (24, 24), (32, 32), (48, 16)]），填充率 15.9%，最小間距 2px：PASS
- `sprites/tuanrong/motion/atlas_radiant.json` → 圖 1024×512，96 frames（尺寸種類 [(64, 64)]），填充率 75.0%，最小間距 2px：PASS
- `sprites/tuanrong/motion/atlas_soft.json` → 圖 1024×512，96 frames（尺寸種類 [(64, 64)]），填充率 75.0%，最小間距 2px：PASS
- `sprites/tuanrong/motion/atlas_sprout.json` → 圖 1024×256，96 frames（尺寸種類 [(32, 32)]），填充率 37.5%，最小間距 2px：PASS
- `sprites/tuanrong/pet_tuanrong_atlas.json` → 圖 2048×134，54 frames（尺寸種類 [(32, 32), (64, 64)]），填充率 56.0%，最小間距 2px：FAIL atlas 2048×134 超出 1024

## 4. 被排除但偏大嘅檔案（確認唔會打包入 app）

- `concepts/bg_sample.png` 1110 KB（非運行時（preview/concept…））
- `concepts/pet_mossback_concept.png` 837 KB（非運行時（preview/concept…））
- `concepts/pet_lampy_concept.png` 727 KB（非運行時（preview/concept…））
- `concepts/pet_shelly_concept.png` 702 KB（非運行時（preview/concept…））
- `concepts/pet_mumo_concept.png` 679 KB（非運行時（preview/concept…））

## 判定

**FAIL**（2 項）：
- sprites/tuanrong/pet_tuanrong_atlas.png: 2048×134 超出 1024×1024
- sprites/tuanrong/pet_tuanrong_atlas.json: atlas 2048×134 超出 1024×1024（對應 PNG）

WARN：
- sprites/tuanrong/pet_tuanrong_atlas.png: atlas 非 2 次冪 2048×134
