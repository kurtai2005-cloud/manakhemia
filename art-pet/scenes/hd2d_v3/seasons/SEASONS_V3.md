# 四季 16 款 V3（第 5 批）

H1 晨光暖調／H2 黃昏電影感／H3 清新冷調／H4 夜燈 × 春夏秋冬 = 16 款，全部轉 V3 HD-2D。
Build：`tools/build_seasons_v3.py fx all json`　Validator：`tools/validate_seasons_v3.py`（寫 `validation.json`）　預覽：`tools/preview_seasons_v3.py`

## 做法
1. 用 V3 花園 raw（`scenes/hd2d_v3/<H>/raw`）重跑 v2 季節筆刷（`build_seasons_v2` 嘅 SEASON_FN）；V3 新材質（IVY、FLOWER_B/W）補季節處理：秋紅／夏綠／冬啡＋雪頂，冬天花變雪色。
2. V3 烘焙（LUT＋split-tone、@3x DoF、葉隙光斑、體積光、bloom、高度霧、vignette）。季節光＝v2 季節 lightmap ÷ v2 H lightmap 嘅比例（clip .6–1.6、模糊）乘落 V3 lightmap。
3. 季節係數：體積光 VOLK 春 .9／夏 1／秋 .78／冬 .7；葉隙光斑 DAPK 春 1／夏 1.15／秋 .85／冬 .35。冬 H1 另有 WASH（體積光 ×.55、遠霧 ×.55、bloom 門檻 +.06、強度 ×.7），防雪地爆白。冬天 bloom 門檻 +.08。
4. 粒子：花瓣／花粉淨係春；冬天冇螢火蟲，秋天減半；冬天 dust/gold 染 #eef4ff。季節粒子 sheet：`fx/particles_seasons_v3@3x.{png,json}`（62 幀，24px cell，alpha 0/255，名 `<season>_<frame>`）。

## 檔案
`<season>/<H#>/`：同 V3 H 一樣 —— 1x 層（223×446；vignette 195×422 螢幕尺寸）、`x3/` sky/far/haze_far/mid/mist/fore/lightmap/light_add/emissive/bloom（669×1338）＋ vignette（585×1266）、`grade.json`（v3 block 加 `seasonParticles`、`seasonLight`）、`palette.json`、`raw/`。總表：`seasons_v3.json`。

## 寵物光
`grade.json → v3.petLight.multiplyBy = petGlow`，跟 `ui/kit_hd2d_v3/layout_hd2d_v3.json#petGlow`：瞓覺／sleepClip／入夢＝0，眼瞓 .6，醒 1；淡出 600ms easeInQuad、淡入 400ms easeOutQuad＋150ms pulse。場景燈唔熄。
