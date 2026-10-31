# HD-2D 場景進度（遊美）
| 時間（HKT） | 段 | 路徑 | 備註 |
|---|---|---|---|
| 10-31 10:47 | ① 共用場景層 | scenes/hd2d/index/（sky／far／mid／fore 索引＋每款 sky_index_H#）、index/materials.json、layout.json、layout_preview_2x.png | 64 index；直向 223×446 層、195×422 美術格 |
| 10-31 10:47 | ② H1 晨光暖調（全套） | scenes/hd2d/H1/（sky/far/mid/fore.png 預烘、raw/、lightmap、light_add、emissive、emissive_blur、vignette、lut.png、grade.json、palette.json、mockup_×3＋2x）；FORMAT.md；tools/validate_hd2d_scenes.py | raw 62 色；validator 0 FAIL |
| 10-31 10:48 | ③ H3 清新冷調 | scenes/hd2d/H3/（同 H1 一套檔） | raw 61 色；petTint #ecdcc8 壓暗團絨、rim 冷色向右下作陰影邊，唔重畫 |
| 10-31 10:48 | ④ H4 夜燈 | scenes/hd2d/H4/（同 H1 一套檔） | raw 63 色；迭代 2 輪（窗光縮細、燈柱光池加強、petTint 改暖） |
| 10-31 10:48 | ⑤a H2 黃昏電影感 | scenes/hd2d/H2/（同 H1 一套檔） | raw 61 色；逆光 rim dir [0.2,-0.98] |
| 10-31 10:48 | ⑤b 雨（H3 落雨中） | scenes/hd2d/rain/rain_tile.png/.json（64×64×4 可平鋪）、rain/ripple.png/.json（16×8×4）、H3/grade_rain.json、H3/rain/{sky,far,mid,fore}.png、H3/rain/lut_rain.png、H3/rain/mockup_rain_×3＋2x | 飽和 0.677、對比 0.972；light_add 建議 ×0.3 |
| 10-31 10:49 | ⑥ 粒子 | scenes/hd2d/particles/particles.png、particles.json（mote/gold/petal/firefly ×6 幀 8×8）、particles_preview_8x.png | json 含 types（幀表、fps、動態建議） |
| 10-31 10:49 | ⑦ rim mask | tools/build_tuanrong_rim.py；sprites/tuanrong/rim/rim_{sprout,radiant,soft}.png/.json（同 atlas 尺寸／rect／幀名 96×3）、rim/<form>/<frame>.png、rim_preview_4x.png | 可重跑；可加 atlas 參數；唔掂 liveliness/ |
| 10-31 10:50 | ⑧ crossfade | scenes/hd2d/crossfade/crossfade_H1-H3-H2-H4.gif（195×422）、_2x.gif、crossfade_keys_strip.png | H1→H3→H2→H4→H1，radiant idle 4 幀，每款停 0.9s＋淡 1.1s |
