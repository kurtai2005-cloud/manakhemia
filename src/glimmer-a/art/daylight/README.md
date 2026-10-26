# 時段背景光 daylight（early／noon／dusk／night）
480x270 邏輯解像度；全程式化（`tools/build_daylight.py`，可重跑）；構圖沿用 `concepts/bg_sample.png`（木房、窗、紫被、盆栽、碗、球）。
- `bg_<t>.png`：場景底圖（RGB，4 時段同構圖，已烘窗光光斑含窗格影、檯燈點光、天空／星／月）。
- `light_<t>.png`：RGBA overlay（暗角＋窗光暈＋檯燈暈＋環境色；alpha 8 階 dither；normal blend 疊喺整個畫面，連寵物）。
- `daylight.json`：每時段色彩參數（ambientMultiply、mainLight、sky、lamp、bloom、vignette、`pet.multiply／add／rim` 寵物 tint）、建議時間、切換 blend 秒數。
- `preview_<t>.png`（2x）、`preview_all.png`（4 格 1x）、`preview_all_2x.png`：團絨 radiant 放入 4 時段（已套 pet tint＋rim＋blob shadow＋overlay）。
- 寵物 pivot 建議 (240,232)，1x 放入 480x270，整體再整數倍放大。bg 唔係調色盤受限（每時段約 90–180 色）；寵物 sprite 仍用團絨 31 色，tint 由引擎 shader 做。
