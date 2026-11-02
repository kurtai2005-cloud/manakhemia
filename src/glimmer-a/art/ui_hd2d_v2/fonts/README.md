# Fusion Pixel（OFL 1.1）— 微光小圃用嘅子集

- 來源：遊美 HD-2D UI kit v2（art-pet/ui/kit_hd2d_v2/fonts/，art/ui-kit-hd2d-v2 @ f01d4efe）＝ TakWolf Fusion Pixel Font
  `fusion-pixel-{8,10,12}px-proportional-zh_hk.ttf`（https://github.com/TakWolf/fusion-pixel-font）。
- 授權：SIL Open Font License 1.1，全文見 `OFL_fusion-pixel.txt`（Copyright (c) 2022, TakWolf）。授權冇指定 Reserved Font Name。
- `fp{8,10,12}-subset.ttf`：用 fontTools `pyftsubset` 抽出遊戲源碼／資料用到嘅 1574 個字（ASCII＋中文＋標點），冇改字形；
  原裝 TTF 3.7–7.3 MB，子集 190–300 KB。Modified Version 照樣以 OFL 1.1 發佈，唔單獨出售。
- 用法（UI_KIT_V2.md §字體）：fp12＝標題、fp10＝掣／內文、fp8＝細字；CSS 字號＝像素尺寸 × 2（1 art px ＝ 2 CSS px）。
- 5a.1（清晰度）：`fp12-subset.ttf` 由同一個原裝 `fusion-pixel-12px-proportional-zh_hk.ttf` 重新抽（pyftsubset，1599 字，涵蓋而家源碼／資料用到嘅全部字）。v2 UI 而家只用 FP12，字號 24px（2×）或 36px（3×）；子集冇嘅字（例如 ✓ ✿ ≥）由 hd2dui2 讀 cmap 判斷，成句轉系統中文字型。fp8／fp10 子集留低未刪（v1／後備），v2 唔再用。
- 5b：同一個原裝 `fusion-pixel-12px-proportional-zh_hk.ttf` 再抽一次（pyftsubset，舊 1599 字＋5b 新用嘅 24 字＝1623 字；冇改字形）。
- 6a：同一個原裝 `fusion-pixel-12px-proportional-zh_hk.ttf` 再抽一次（pyftsubset，舊 1628 字＋6a 對白新用嘅 8 字＝1636 字；冇改字形）。
