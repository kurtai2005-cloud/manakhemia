# from_ref 尺寸比較：64 ／ 80 ／ 96（2026-11-01 HKT）

Kurt [pt93u]「可以出埋比我比較下」。三個尺寸都係由原圖 cutout **重新建**（唔係放大 64），同一套色盤／清理／1px 外框／glow 規則；腳點 bottom-centre、燈泡保留、idle 4 幀。

| 尺寸 | 目錄 | pivot | 地線 y | 冇眨眼（偵測唔到眼） |
|---|---|---|---|---|
| 64 | `../tuned/` | (32,61) | 61 | A1 B2 H3 |
| 80 | `../tuned_80/` | (40,77) | 77 | —（已手放眼位，24 隻全部有） |
| 96 | `../tuned_96/` | (48,93) | 93 | A1 B2 F3 H3 |

- 80／96 嘅燈泡、F1/G1 星天線、A/B 線泡泡按 K=S/64 程序放大（64 保持 byte-identical）。
- `size_compare_3x.png`：《微光小圃》H1、195×422 @3x，3 欄 64/80/96 × 3 行（A1 一階細、C2 二階、B3 三階大）；紅帶 = 頂部 UI ~52px／底部 UI ~100px，青框 = 寵物 bbox。`size_compare_preview.png` 係 1x 縮圖，`size_compare.json` 有淨空數字。
- `lineup_64_4x.png`／`lineup_80_4x.png`／`lineup_96_4x.png`：每個尺寸 24 隻。

## 淨空（art px）
| | 64 | 80 | 96 |
|---|---|---|---|
| 頂部 UI 淨空 | 182–191 | 167–178 | 151–165 |
| 底部 UI 淨空 | 28–29 | 28–29 | 28–29 |
| 佔畫面闊 | 19–26% | 24–32% | 29–38% |

腳點固定 (97,292)，所以底淨空唔受尺寸影響；三個尺寸都冇撞 UI。

## 建議
**80px**：手機上存在感明顯好過 64（細節、表情睇得清），又唔似 96 咁搶晒花園場景、遮到圍欄／屋。96 適合做「單隻主角特寫」或者進化演出鏡頭。

## 重建
```
python3 tools/build_from_ref_tuned.py all --size 80
python3 tools/build_from_ref_tuned.py all --size 96
python3 tools/build_from_ref_feeltest.py
python3 tools/build_from_ref_sizecompare.py
```

## 結果
Kurt [pt94u]「80好d」→ 80px 定為正式版，見 `../tuned_80/ENGINE_80.md`。（比較圖已用最新 80 重影。）
