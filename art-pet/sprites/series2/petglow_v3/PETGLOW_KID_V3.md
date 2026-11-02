# 細佬 series2 petglow v3（第 5 批）

34 形態入面 33 款有光源（S1 冇光）。Build：`tools/build_kid_petglow_v3.py`；驗：`tools/validate_seasons_v3.py`（kid 部份）。Schema 同第 3 批團絨 petglow v3 一樣。

- `<form>.json`：`frames{<clip>_<nn>: {e, a:[[dx3,dy3,r3,w]]} 或 {same}}`、`clipGlow`、`pool`、`emitter`、`flicker`、`sceneScale`（花園／屋仔日 .5／屋仔夜 1）、`petGlow`。
- `<form>_glow@3x.{png,json}`：halo_s/m/l、core_12、粒子幀。`index.json`：33 款總表。
- Clips：idle 4、walk 6、cry 6、eat 6、sleep 4（共 26 幀）。**sleep＝0**（fadeOut 600ms easeInQuad；離開 sleep fadeIn 400ms easeOutQuad＋pulse 1→1.15→1），其他 clip＝1。Kurt：「除左佢訓就會關」。
- Anchor：逐幀用燈泡色追蹤（±9px）；另加眼 anchor（glow/glow_angry/star 眼，瞓覺唔要）、葉脈 anchor（最多 3 組）。
- 光風格：A＝水滴、B／S＝光點、C／D／E＝火星、F／G／H＝星。
- 已知：S4F 有 2 幀追唔到燈泡，用 fallback anchor；冇逐像素 emissive mask（淨係 anchor 光暈）。
