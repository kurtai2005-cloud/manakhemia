# 貼圖預算檢查結果（art_budget_check.py）

> 目錄：`/tmp/glimmer-a/src/glimmer-a/art`；預算 16 MB（模式 both）；atlas 上限 1024×1024；mipmap=off

## 1. 尺寸檢查（運行時貼圖）

| 檔案 | 尺寸 | 磁碟 | 解碼 RGBA | 判定 |
|---|---|---|---|---|
| `atlas_egg.png` | 1024×64 | 2.2 KB | 0.25 MB | PASS |
| `atlas_events.png` | 1024×128 | 8.7 KB | 0.50 MB | PASS |
| `atlas_props.png` | 1024×64 | 2.4 KB | 0.25 MB | PASS |
| `atlas_radiant.png` | 1024×512 | 48.7 KB | 2.00 MB | PASS |
| `atlas_soft.png` | 1024×512 | 46.2 KB | 2.00 MB | PASS |
| `atlas_sprout.png` | 1024×256 | 19.3 KB | 1.00 MB | PASS |
| `daylight/bg_dusk.png` | 480×270 | 21.8 KB | 0.49 MB | PASS |
| `daylight/bg_early.png` | 480×270 | 17.8 KB | 0.49 MB | PASS |
| `daylight/bg_night.png` | 480×270 | 17.0 KB | 0.49 MB | PASS |
| `daylight/bg_noon.png` | 480×270 | 12.4 KB | 0.49 MB | PASS |
| `daylight/light_dusk.png` | 480×270 | 72.1 KB | 0.49 MB | PASS |
| `daylight/light_early.png` | 480×270 | 98.7 KB | 0.49 MB | PASS |
| `daylight/light_night.png` | 480×270 | 69.5 KB | 0.49 MB | PASS |
| `daylight/light_noon.png` | 480×270 | 22.5 KB | 0.49 MB | PASS |

## 2. 每組（寵物）運行時貼圖總量

| 組 | 張數 | 磁碟 | GPU（解碼） | 對預算 | 判定 |
|---|---|---|---|---|---|
| . | 6 | 0.12 MB (1%) | 6.00 MB (38%) | 16 MB | PASS |
| daylight | 8 | 0.32 MB (2%) | 3.96 MB (25%) | 16 MB | PASS |

## 3. atlas JSON 檢查（frame 越界／重疊／padding）

- `atlas_egg.json` → 圖 1024×64，6 frames（尺寸種類 [(32, 32)]），填充率 9.4%，最小間距 4px：PASS
- `atlas_events.json` → 圖 1024×128，31 frames（尺寸種類 [(32, 32)]），填充率 24.2%，最小間距 2px：PASS
  - 填充率 24% 偏低：atlas 大部分係空白 → 記憶體浪費（0.5 MB 只用 0.12 MB）；建議縮細或拆分。
- `atlas_props.json` → 圖 1024×64，18 frames（尺寸種類 [(16, 16), (24, 24), (32, 32), (48, 16)]），填充率 15.9%，最小間距 2px：PASS
- `atlas_radiant.json` → 圖 1024×512，96 frames（尺寸種類 [(64, 64)]），填充率 75.0%，最小間距 2px：PASS
- `atlas_soft.json` → 圖 1024×512，96 frames（尺寸種類 [(64, 64)]），填充率 75.0%，最小間距 2px：PASS
- `atlas_sprout.json` → 圖 1024×256，96 frames（尺寸種類 [(32, 32)]），填充率 37.5%，最小間距 2px：PASS

## 判定

**PASS**

WARN：
- atlas_events.json: 填充率 24%
