# 6b 散步 V3-A 光影（第 6 批）

底：`art/breakthrough/6b`（commit a1a6e9a2）原檔一隻都冇郁；`walk6b.json`、1x key、尺寸照用。V3 全部喺 `6b/v3/`，入口 `walk6b_v3.json`。
生成：`art-pet/tools/build_walkdream_v3.py walk`；驗證：`validate_walkdream_v3.py`；預覽：`preview_walkdream_v3.py`。

## walk_bg（300×360 @3x，同原 walk_bg@3x 同框頂替）
三個時段跟現實時間：`day` 06–17、`dusk` 17–19、`night` 19–06。每個時段 `walk_bg/<v>/`：
- `x3/sky|far|mid|fore@3x.png`：分層（sky 全幅；far、fore 已烘 DoF；mid＝路／石／木牌，alpha 0/255；夜晚 mid 加木牌小燈籠）
- `x3/haze_far|mist@3x.png`（真 alpha）、`x3/lightmap@3x.png`（multiply：大樹投影＋葉隙光斑；夜晚＝月光＋燈籠暖光池）
- `x3/light_add@3x.png`（lighter：god rays 由日／月 (31,7) 射落、日月暈、地平線光）、`x3/bloom|emissive@3x.png`、`x3/vignette@3x.png`
- 1x fallback：`sky|far|mid|fore|lightmap|light_add.png`（100×120）；`lut.png`（256×16）；`grade.json`
- `grade.json#v3`：stack、flares、emitters（日＝花粉、黃昏＝金塵、夜＝螢火蟲）、stoneGlow、petLight、petPop
- `walk_bg/stone_glow@3x.png`：而家行到嗰粒踏腳石底光（lighter，pulse .6Hz）；行過嘅 alpha .3

疊層次序：`walk6b_v3.json#stack`（sky→far→haze→mid→stone_glow→mist→pet→deco→fore→lightmap→light_add→bloom→emissive→flares→particles→fog→vignette）。

## 寵物光
散步＝醒，`petLight.multiplyBy = petGlow`（layout_hd2d_v3.json#petGlow：awake 1、sleepy .6、sleep／sleepClip／dreamEnter／dreaming 0）。
`walkScale`：day .5、dusk .8、night 1。逐形態光暈：`walk6b_v3.json#pets.<pid>.petglow`（A–H→series2 petglow_v3；evo_*→tuanrong petglow_v3）；
`sprout／evo_dot／evo_sprout` 本身冇光源（petglow index notLight），只用通用 pet_pool。

## deco（8 款）
`deco/<n>_v3@3x.png`（48×48，rim 烘入，alpha 0/255，外形同原檔一樣）、`deco/<n>_glow@3x.png`（72×72 真 alpha）、`deco_ao@3x.png`、`sparkle@3x.png`（6 幀 24×24，12fps，撿到用）。
