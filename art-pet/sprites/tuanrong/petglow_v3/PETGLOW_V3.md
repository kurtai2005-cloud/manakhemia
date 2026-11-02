# 寵物光源 v3（第 3 批）

生成：`python3 art-pet/tools/build_petglow_v3.py [forms garden weather preview]`；驗證：`python3 art-pet/tools/validate_petglow_v3.py` → `validation.json`。Pillow／numpy（scipy.ndimage 連通區）；無 AI 圖。

## 有光源／特效嘅形態（20）
`index.json` 有齊。來源＝ `sprites/tuanrong/evo6/atlas_<form>_emissive.png`（白＝發光）。
| 分支 | 形態 | 光 | 粒子 |
|---|---|---|---|
| 光卵 egg | evo_egg | 暖金 | mote |
| 絨跳 hop | evo_hop（第一粒燈芽） | 暖金 | mote |
| 燦光 radiant | guard／still | 金色大光暈，呼吸 .4Hz | mote |
| 柔光 soft | guard／still | 暖、細、慢呼吸 | mote |
| 微塵 dust | guard／still | 細光點閃 | mote |
| 火苗 ember | guard／still | 火光亂閃 9Hz ±16% | ember（火星上升）|
| 螢絨 lumi | guard／still | 螢光一明一暗 | fly |
| 月眠 moon | guard／still | 月白柔光 | star |
| 晶角 crystal | guard／still | 稜光＋星芒（借 fx flare_s）| prism |
| 菇傘 shroom | guard／still | 菌光 | spore |
| 水珠 tide | guard／still | 水光閃 | drop |
唔算光源：絨點（得 1px 眼高光）、絨芽（冇 emissive）→ 只用花園通用 petLight 光池。

## 檔案
* `<form>.json`（compact）：`tints` core/mid/outer（取自該形態 palette）、`flicker`、`sceneScale`（H1 .55／H3 .45／H2 .9／H4 1）、`pool`、`emitter`、`petGlow`、`clipGlow`、`frames`。
* `frames[<幀名>] = {e, a:[[dx3, dy3, r3, w], …]}`：**逐幀 anchor**，相對該幀 `pivotPx`（picked_up* 用 grab pivot）嘅 @3x 偏移；寵物腳底位 ＋ (dx3 × scaleX, dy3)。`r3` 揀 halo（≤24 halo_s、≤40 halo_m、其餘 halo_l）；`w` 強度；`e` 該幀發光量（相對 awake 中位數，瞓覺幀自然細啲）。`{same: 幀名}`＝同另一幀一樣（noface 幀大多 same）。每幀最多 8 個 anchor（細點併入最近）。
* `<form>_glow@3x.png/.json`：`halo_s/m/l`、`core_12`（真 alpha，已上色）＋ `<粒子>_01..04`（alpha 0/255）。

## 畫法（每幀）
1. pool：scene `grade.v3.petLight` 光池；tint ＝ mix(scene tint, form pool.tint, .5)；× petGlow；畫喺 pet 之前（lightmap 之前）。
2. sprite＋飾品（唔變）。醒時發光像素唔食 petTint×ambientTint；瞓時同身體一樣。
3. emissive（sprite 自帶 mask）lighter ×.33 × petGlow。
4. halo：每個 anchor，globalAlpha ＝ w × e × flicker × sceneScale × petGlow，lighter。
5. core_12：最大 anchor。
6. 粒子：emitter 由 anchor 按 w 抽位生；核心 source-over，配 halo_s lighter。
4–6 喺 lightmap／light_add／bloom 之後畫（自己發光，唔被場景陰影食）。

## 瞓覺關光（Kurt：「除左佢訓就會關」）
`clipGlow`：`fall_asleep`＝sleepClip（第 1 幀開始 600ms easeInQuad 淡出）、`sleep_loop`＝0、`wake`＝0 → 最後一幀 400ms easeOutQuad 淡入＋150ms pulse 1→1.15→1；`yawn`／`emo_sleepy`＝sleepy .6；其他＝awake 1。dreamEnter／dreaming 由夢遊系統設 0。乘晒 pool／halo／core／粒子／emissive；sprite 本體唔變；**場景燈唔受影響**。對應 `ui/kit_hd2d_v3/layout_hd2d_v3.json#petGlow`。

## 花園改動
* `scenes/hd2d_v3/H*/grade.json → v3.petLight` 加 `formLight`、`tintMode`。
* **H2 黃昏光池加強**：intensity .55 → 1.0、size3x 240×96 → 320×120、`postLightmap .5`（一半光池喺 lightmap 後再疊，唔俾暗地食走），加 `bounce`（身底暖反光 #ffb070 α.24）。`build_garden_hd2d_v3.py` PETLIGHT 同步；重建花園後要再跑 `build_petglow_v3.py garden`。
* H3 天氣 V3：見 `scenes/hd2d_v3/FORMAT_V3.md` §天氣。

## 預覽
`preview/petglow_grid.png`（8 形態 × H3 日醒／日瞓／H2 黃昏醒／H4 夜醒／夜瞓）、`preview/H4_evo_still_lumi_awake_vs_sleep.png`、`preview/H4_evo_still_ember_awake_vs_sleep.png`、`preview/H2_pool_before_after.png`。
