# 屋仔 V3-A（第 4 批）

跟概念 `ui/style_ref/hd2d_v3/house_v3A_3x.png`：室內暖光、窗光體積光、地板反射、浮塵。
1x 原像素（4b 屋仔＋5a 房 2–4）唔改，V3 全部係疊上去嘅光影層；家具／紀念品 @3x 用 nearest，alpha 保持 0/255；光影層 @3x 用真 alpha。

## 檔案
- `rooms/<room1..4>/<day|night>/`：1x `sky far mid fore lut lightmap light_add emissive emissive_blur vignette grade.json`；`x3/` @3x 版（669×1338，vignette 585×1266）＋ `floor_reflect bloom`。
- `light/<none|win_curtain|win_star>_{beam,patch}@3x.png`：窗光 gobo，跟窗 slot 家具換；色同強度由 `grade.json#v3.windowBeam` 決定。
- `furniture/x3/*@3x.png`（像素 0/255）、`*_ao@3x.png`、燈 `*_lift/_halo/_pool@3x.png`；`furniture_v3.json`。
- `souvenir/x3/<id>@3x.png`、發光手信 `<id>_glow@3x.png`、`sv_ao@3x.png`；`souvenir_v3.json`（擺位 spots：窗台／檯面／層架／地板）。
- `house_v3.json`：疊層次序 `stack`、房間列表、petGlow 映射。

## 疊層（由底到面）
sky → far → 牆身家具 → mid → floor_reflect → 實時倒影 → 地氈 → AO → 燈光池 → y-sort（家具／寵物／紀念品）→ fore → × lightmap（＋燈 lift）→ ＋light_add → ＋窗 beam／patch → bloom → 燈 halo／emissive → 紀念品光 → 寵物光 → flare → 浮塵 → 霧 → vignette。

## 寵物光（Kurt：「除左佢訓就會關」）
寵物自己嘅光 × `petGlow`（source of truth `ui/kit_hd2d_v3/layout_hd2d_v3.json#petGlow`）：
醒 1、sleepy .6、瞓床（sleep_loop／同床瞓）0；熄 600ms easeInQuad，醒返 400ms easeOutQuad＋150ms pulse 1→1.15→1。
屋仔用 `petLight.houseScale`（日 .5／夜 1）。燈、窗光、紀念品光係場景光，唔熄。

## 工具
`tools/build_house_v3.py [furniture souvenir rooms json preview]`、`tools/preview_house_v3.py`、`tools/validate_house_v3.py`。
