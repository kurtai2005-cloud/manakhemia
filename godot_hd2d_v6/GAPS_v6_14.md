# GAPS v6.14 (0.6.14-pilot, vc20): art on the 0.6.13 state (遊程 v6.9-merged code)

- **Base:** 0.6.13.
  - Version: `project.godot` line 1 + `config/version="0.6.14-pilot"`, export `version/code=20`.
  - `capture.gd` header + "hd2d v6.14 start"; art_depth "art depth v6.14 ready" / "perf v6.14 mode=".
- **Kurt's 0.6.13 review:** ~90 % agreed. The lawn is green again but reads flat / uniform like a carpet. This version targets the five points below. It is judged by eye at phone aspect and against 0.6.13 for regressions.
- **PC:** RTX 4060 Laptop, Godot 4.7.2 Mobile/Vulkan.
  - Fresh folders `v6_14_r1` and `v6_14_r2`; the version line was checked both times.
  - 2 Mobile rounds (the max). The PC was not shut down.
  - Each zip was sent in 3 parts, joined on the PC and MD5-verified (r1 9ec73f01…, r2 58212328…).
  - No SCRIPT ERROR or shader error in any r2 log. The non-fatal "material is null" ×4 is unchanged.
- **Evidence (previews/):**
  - `v6_8phone_v6_9_vs_v6_14.png`: concept | 0.6.8 phone | 0.6.9 | 0.6.13 Low | 0.6.14 Low (shipped) | 0.6.14 High.
  - `lawn_closeup_v6_14.png`: concept | 0.6.9 | 0.6.13 | 0.6.14 Low | 0.6.14 High; near lawn + clearing.
  - `walk_low_v6_14.mp4`: the ONE Low 19:9 walk, PC r2, 540x1140, 900 frames @30 fps, shipped defaults. 10 fps frame-diff median 19.0 / max 23.0. It is x264 crf 26 (52 MB), larger than before because the clumped grass has more detail.

## 1. Status vs concept (judged by eye at phone aspect, PC r2)
| # | Item | Status | Read |
|---|---|---|---|
| 1 | **Near lawn depth** (blade clumps, dark gaps, sunlit tufts, gold patches, edge tufts, flower / clover clusters) | **MUCH BETTER than 0.6.13; beats 0.6.9 on clump depth, not yet on golden variety** | **New tile (`lawn_depth_v6_14.py`):** jittered-grid tufts (cell 13 px ≈ 3 wu, r 1.5–2.75 wu). Each tuft is a mound: sunlit upper part, own shade low, deep-green gap at the rim. Blades lean out from the tuft centre with yellow-green tips (more inside the gold pools). It adds 14 clover clumps (rounded leaves), 18 flower clusters (5–9 blooms: white / butter / pink) and a few single blooms. In-engine: gold patches where the sun breaks through the dapple (near_lawn), and the highlight compress is relaxed (0.55 → 0.30). **PC read:** the bottom now reads as tufted living grass with dark gaps and lit tufts, not a carpet. Mid-scale (clump) contrast on the near-lawn crop is 12.1 (0.6.13: 9.0). Hue median is 70° (greener; 0.6.13: 63°). **vs 0.6.9:** the blade / clump depth is better. 0.6.9 still has bolder warm-gold vs olive patch variety; 0.6.14's gold patches are visible but gentle on Mobile. Edge tuft cards are the existing sets (path / cottage / fence / tree-base / foreground); no new tuft cards were added. |
| 2 | **Light pooling** (lit centre warmer / brighter, edges + tree shade cooler / darker) | **DONE (moderate)** | Centre gain (1.26, 1.14, 0.90) around 團絨 / props, and edge gain (0.76, 0.84, 0.94) at the clearing rim / bottom, on both GroundInner and the near lawn. PC: centre 105/91/30 (0.6.13 102/88/30), bottom 56/64/15 (0.6.13 62/65/17). The vignette-like focus toward 團絨 + cottage reads, but it is softer than the concept. |
| 3 | **Hedge warmth on Mobile** (diagnose + fix) | **FIXED** | **Diagnosis (same-pixel compare, PC Mobile vs box gl_compatibility):** the hedges start at the same colour (PC 52/79/16, box 53/81/11). On Mobile, `warm_gain` is a linear multiply before Filmic: ×1.8 shows as only +29 % on screen (52 → 67), while the box showed +68 %. A multiply on a dark saturated green also stays green. So the cause is the Mobile linear-HDR → Filmic path, not a missing shader branch. **Fix:** `warm_add`, a gold add scaled by the card's own value, on top of the gain. PC hedge pixels: off 51/76/16 → 0.6.13 62/86/15 → **0.6.14 80/93/18**, warm sunlit yellow-green with the gaps kept. |
| 4 | **Softer tree clumps** | **SLIGHTLY softer** | Lobe seams are blended and the gaps are shallower (cav −0.22 → −0.16). r1 used a wider blend (σ 0.42 r); it averaged the lobes away and the lit masses dimmed, so r2 uses σ 0.16 r and the big masses are back. The softening is small on the phone; the canopy is still crisper than the concept. |
| 5 | **Picket shadows** (trim bed plants nearest the fence) | **DONE (small)** | Back-row seedling cards are trimmed to 62 % height. More soil shows behind them, and the picket / trunk shade on the bed soil reads more. Front row untouched. |
| S | Sky shafts, object shadows, cottage, night | **kept** | as 0.6.13 (night unaffected: warm_add = 0 and pool/gold live only inside the day lawn block) |
| D | Low 60 fps | **estimate OK, not phone-measured** | §3 |

**Visual estimate: about 91 %.** Up from 90 %: the carpet lawn is gone, the hedges read warm on Mobile, and the clearing has a light focus. **Not 95 %, do not deliver.** Biggest gaps:
- The golden patch variety on the bottom lawn is still gentler than 0.6.9 / the concept.
- The pooling is softer than the concept's.
- The canopy is still crisper than the concept.
- The dark rectangle behind the left fence is a pre-existing bake edge, not new.

## 2. 0.6.14 values (changes only)
- **Blade tile `lawn_blades_v614.png`** 256² (64 wu):
  - Base cool (30, 60, 30) ↔ warm (70, 80, 28) by hue σ 22.
  - Gold pools ×(1.24, 1.18, 0.86) by pool σ 18.
  - Tufts: cell 13 px, r 6–11 px. Mound 0.70 + 0.58·inside^0.6·(0.75 − 0.45·dy); gap ×(1 − 0.32·gap) + deep green (16, 42, 18).
  - Blades: 0.30·N² blades; tip (138, 152, 58); final ×1.10. Mean 57/75/29; luminance p5/50/95 30/58/117.
- **Pool:** core (1.26, 1.14, 0.90) at 0.10–0.60 r; edge (0.76, 0.84, 0.94) at 0.45–1.15 r; `lawn_center` (10, 0, 5), `lawn_radius` (170, 110).
- **Gold patches:** gain (1.42, 1.28, 0.86), `gold_tile` 37, vr 0.88–1.12. `fg_hi_cut` 0.30.
- **Hedge:** `warm_gain` (1.62, 1.40, 0.86), unchanged. New `warm_add` (0.050, 0.024, 0.003). PC r2 alternative tested: `add2` (0.070, 0.034, 0.004) → 87/96/19, a bit hot.
- **Bed:** `back_trim` 0.62, `back_z` −1.
- **Canopy:** blend σ 0.16 r; val = 0.63 + 0.55·lg·(0.55 + 0.45·grad) + 0.40·lg² + 0.32·lit·(0.5 + 0.5·rim) + 0.03·h2 − 0.16·cav; lg = smoothstep(−0.65, 0.92).
- **PC r2 tested but NOT shipped:** `pool_mild` (edge 0.84/0.90/0.96, core 1.16/1.08/0.92, gold 1.25/1.15/0.90). The focus read weaker.

## 3. Perf (PC GPU ms, FORCE_MOBILE 1080x2280)
| Case | 0.6.13 r2 | 0.6.14 r1 | 0.6.14 r2 | Draws / prims |
|---|---|---|---|---|
| **Low shipped** | 0.656 | 0.664 | **0.666** | 133 / 36.5k |
| Low rays off | 0.635 | 0.644 | 0.643 | 128 |
| Low live sun | 0.741 | 0.802 | 0.750 | 144 / 37.4k |
| **High** | 0.869 | 0.875 | **0.877** | 206 / 42.4k |
| Night | 0.613 | 0.611 | 0.619 | 128 |

- Shipped Low is +0.010 ms (a few ALU ops in the lawn / hedge / bed shaders; no new texture fetches). Draws and prims are unchanged.
- The estimate stays 57–60 fps on the Note10+, **not phone-measured**.
- No visual quality was traded for perf.

## 5. For 遊程: exact changes (cumulative) — 0.6.10 steps 1–8, 0.6.11 step 9, 0.6.12 step 10, 0.6.13 step 11, 0.6.14 step 12; all still valid in 0.6.14
1. **Low:** `_sun.shadow_enabled = false` when mode == low (day). Keep the bake. The art layer auto-detects Low with sun shadow off and turns on the props ground, the props wide mask, near mover shade and the pet silhouette (`art_depth._low_fake_shadow`). Preview flag: `HD2D_LOW_FAKE=1`.
2. **Bake pass bug:** `_apply_shadow_policy` sets `_sun.shadow_enabled = (not night) and (not bake_pass)`, which made the bake empty (3 draws). Art forces it ON in `_setup_shadow_bake` and `_process` while baking. Please make bake_pass keep the sun shadow.
3. **Jar:** not a live caster (your v6.9). It is now baked (removed from art HY_PROPS).
4. **Your 12 High shafts:** the art layer swaps their material to `light_shaft.gdshader` (tint (1, 0.86, 0.62), alpha = your alpha × 1.6 × graze × cloud), width ×1.7 (min 40), cast_shadow OFF, axis = SUN_TO.
5. **Ambient (0.62, 0.66, 0.86) +0.05 tested (HD2D_AMB=1, PC High):** mean diff 1.85. Shadows turn slightly bluer, away from the concept's olive-gold shade. **Recommend NOT applying**; the bake already tints the interiors blue-violet.
6. **Export filter:** added `art/ground/bake_*, textures/*_hard.png(.import)`.
7. **"Parameter material is null" ×4:** present in the merged build before and after reimport; looks like capture.gd ~169. Non-fatal, still open.
8. **Test hooks (env only, inert otherwise):** `HD2D_HI=atlas=,dist=,softq=,splits=1,shafts=0,dof=0,glow=0,casters=hy,rays=0,skyfx=0,petsh=0`, `HD2D_AMB=1`, `HD2D_POOL_GAIN=`, `HD2D_FG_LIST=1`, `HD2D_DBG_NOCAST=<prefix|ALL>`.


9. **0.6.11 additions for 遊程 (art side, no code change needed):** bake pass now sets an 8192 orthogonal sun shadow (`_setup_shadow_bake`), enables far casters only in the bake, `HD2D_BAKE_SUNVIEW` diagnostic; GroundInner High albedo → `ground_composed_hi_v611.png`; `LawnBounce_v611` DirectionalLight (High only by default; please keep it out of any light-count limits); env fog values set every day frame, reset to 0 at night. Export filter + `art/ground/ground_composed_clean_*`.
10. **0.6.12 additions for 遊程:** `capture.gd` now also sets the ground's `lawn_center` (10, 0, 5) and `lawn_radius` (170, 110) next to `lawn_gain` (default 0.6 → 1.0; env `HD2D_LAWN`, `HD2D_LAWNZ`, `HD2D_LAWNRX`, `HD2D_LAWNRZ`). Low exposure 1.58 → 1.50. Clump cards get a warm day `light_mul` (1.12, 1.07, 0.96) (env `HD2D_CLUMP=r,g,b`; night unchanged). High day fog 0.05 → 0.04, fog light energy 0.85 → 0.70 (Low fog stays off). `near_lawn.gdshader` decodes `near_mover_shade.png` with pow 2.2 (display ratio) and its shade floor is 0.48. Shaft alpha ×1.4 for both art rays and your 12 High shafts (now your alpha × 1.6 × 1.4 × graze × cloud); `light_shaft.gdshader` break_boost 1.25. Outer lawn texture → `grass_outer_v612.png`. No new nodes, draws or passes.
11. **0.6.13 additions for 遊程:**
    - **Lawn textures:** near-lawn blade tile → `lawn_blades_v613.png`; outer lawn → `grass_outer_v613.png`; High GroundInner → `ground_composed_hi_v613.png`.
    - **Bed shade (Low only):** `capture.gd`'s `_bed_flower_mats` get `bedtop_tex` / `bedtop_amt`, set by `art_depth._low_fake_shadow` (1 in Low without sun shadow, 0 otherwise). Please keep `_bed_flower_mats` and `_is_bed_node()` (the bake pass uses `_is_bed_node` to hide beds).
    - **New bake pass:** `HD2D_BAKE_RECV_Y=6` raises GroundInner to the bed top and hides the beds (bake only).
    - **Shader uniforms:** `bed_flower.gdshader` has new uniforms (`bedtop_tex`, `bedtop_amt`; default 0 = old look). `clump_card` / `leaf_card` get `warm_zone` / `warm_gain`; art_depth sets it per frame, and night = 1.
    - **New env hooks (inert by default):** `HD2D_HEDGE=r,g,b`, `HD2D_DUMP_ZONE=1` (debug print).
    - **Cost:** no new nodes, draws or passes.
12. **0.6.14 additions for 遊程:**
    - **Lawn texture:** near-lawn blade tile → `lawn_blades_v614.png` (new tool `tools/lawn_depth_v6_14.py`). GroundInner / outer lawn textures were re-baked with the same tools. The only change is a back-edge taper of the back-lawn darkening, which made no visible difference.
    - **Light pooling (`texel_lit.gdshader` + `near_lawn.gdshader`, inside the existing `lawn_gain` block):** new uniforms `pool_core` (centre gain, default 1 = off), `pool_edge` (edge gain, default 1 = off) and `pool_r`. `capture.gd` `_setup_ground` sets them on the ground material: core (1.26, 1.14, 0.90) at r < 0.10–0.60, edge (0.76, 0.84, 0.94) at r 0.45–1.15 of `lawn_radius` around `lawn_center`. `art_depth._near_lawn` sets the same values on the near lawn, because the copy from the ground ran before capture.gd set them.
    - **Golden patches (`near_lawn.gdshader`):** `gold_gain` (1.42, 1.28, 0.86) where the bake says sun (vr 0.88–1.12) × a slow world-space break-up field (`gold_tile` 37 wu). `fg_hi_cut` 0.55 → 0.30 on the near lawn.
    - **Hedge warmth on Mobile (`clump_card` / `leaf_card`):** new `warm_add` (0.050, 0.024, 0.003) day, ZERO at night. It is added on top of `warm_gain`, scaled by the card's own value, so the gaps stay dark. art_depth sets it next to `warm_gain`.
    - **Bed (`bed_flower.gdshader`):** `back_trim` 0.62 and `back_z` −1. Cards in the back row (local −z, toward the fence) are scaled to 62 % height above `stem_y`. Front rows are untouched.
    - **Canopy (`art_depth` lobe shading):** the lobe normal is a soft blend of the near lobes at the seams (σ 0.16 r). The shading curve changed from 0.60 / 0.42 / 0.32 / −0.22 cav to 0.63 / 0.40 / 0.32 / −0.16 cav, with a wider top ramp.
    - **New env hooks (inert by default):** `HD2D_POOL=r,g,b`, `HD2D_POOLC=r,g,b`, `HD2D_GOLD=r,g,b`, `HD2D_FGCUT=`, `HD2D_HEDGEADD=r,g,b`. Helpers are `_envf_ad` / `_envv3` at the end of art_depth.gd.
    - **Cost:** no new nodes, draws or passes. Draws are 133 / 206, the same as 0.6.13.


## 6. Open / next
1. Bottom lawn: bolder warm-gold vs olive patch variety (0.6.9 still wins there). Try larger, fewer gold pools in the macro (bake side), not only the shader field.
2. Pooling: a little stronger centre on Mobile if Kurt wants more focus (env `HD2D_POOLC` / `HD2D_POOL` for a quick read).
3. Canopy: a softer painterly interior needs atlas-level work (spray texture), not only lobe shading.
4. Dark rectangle behind the left fence (pre-existing): the bake's shadow-map extent edge. Fix by widening the bake ortho extent.
5. Phone-measure Low fps.
