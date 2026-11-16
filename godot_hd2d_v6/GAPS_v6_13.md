# GAPS v6.13 (0.6.13-pilot, vc19): art on the 0.6.12 state (遊程 v6.9-merged code)

- **Base:** 0.6.12. Version: `project.godot` line 1 + `config/version="0.6.13-pilot"`, export `version/code=19`, `capture.gd` header + "hd2d v6.13 start", art_depth "art depth v6.13 ready" / "perf v6.13 mode=".
- **Kurt's 0.6.12 review (accepted):** 93 % was overstated. The main lawn read as a brown/olive DIRT field with sticks; matching mean RGB hid it. From 0.6.13 it is judged by what it reads as (material, lushness, hue variety), against the concept crop AND 0.6.9.
- **PC:** RTX 4060 Laptop, Godot 4.7.2 Mobile/Vulkan. Fresh folders `v6_13_r1`, `v6_13_r2`; version line checked; 2 Mobile rounds (max). PC not shut down. The PC dropped out briefly during the r2 zip copy; the zip was sent in 3 parts, joined on the PC and MD5-verified (e1433771…). No SCRIPT ERROR in any r2 log.
- **Evidence (previews/):** `v6_8phone_v6_9_vs_v6_13.png` (concept | 0.6.8 phone | 0.6.9 | 0.6.12 | 0.6.13 Low | 0.6.13 High), `lawn_closeup_v6_13.png` (concept vs 0.6.9 vs 0.6.12 vs 0.6.13 Low/High: lawn + clearing), `shadow_shapes_v6_13.png` (game-view crops 0.6.12 Low | 0.6.13 Low | 0.6.13 High + far), `walk_low_v6_13.mp4` (the ONE Low 19:9 walk, PC r2, 540x1140, 900 frames @30 fps, shipped defaults; 10 fps frame diff median 17.0 / max 21.3).

## 1. Status vs concept (judged by visual read at phone aspect)
| # | Item | Status | Read |
|---|---|---|---|
| L | **Lush living green lawn in golden light** (priority 1) | **FIXED the regression; still a bit flat vs 0.6.9** | **Cause:** desaturated olive albedo (≈60/68/33) × golden sun (1, 0.84, 0.66) × the v6.11 R×1.17 grade × olive desat → R ≥ G → ochre dirt; dark "stick" stems in the old blade tile. **Fix:** new original blade tile (`tools/lawn_lush_v6_13.py`): dense short blades, darker green base → warm yellow-green sunlit tips (more in lit patches), cool↔warm green hue field, soft lit patches, clover clusters, tiny white / butter / pink flowers, **no stick stems**. Lush grade for ground / outer lawn (saturation ×1.30, gain 0.88/1.05/0.86). Shade tint changed from blue-violet / warm to cool green-olive (bake, near lawn, mover shade). Near lawn: no red push, hue_keep 0.20 → 0.06, calm desat toward green. **PC read:** the lawn is green grass with golden light, small flowers, darker green (not brown) shade, calm. Lawn hue median 63° (0.6.12: 42° ochre; 0.6.9: 64°). **Still short of the concept / 0.6.9:** at phone size the bottom lawn is a little flat and hazy. It has less blade-clump depth and fewer golden pools than 0.6.9; the concept is softer and more golden-olive. |
| S1 | Object shadows readable on the green | **KEPT / clearer** | Prop shadows now read as cool dark-green shapes on the lawn. Low prop σ 0.5 → 0.35 (sharper), mover σ 0.15, mover floor 0.42 (the fg-plant shade was near-black). |
| S1b | **Picket / lamp shadows** (priority 2) | **PARTLY** | **Bed tops baked:** a new bake pass puts the receiver plane at the bed soil / frame top (y 6) with the beds hidden. The engine's own 8192 map gives the shade that falls ON the beds; `bed_flower.gdshader` applies it in Low to up-facing soil / frame tops (seedling cards fade with height). The Low bed now matches High (trunk / picket shade on the soil). Picket teeth are mostly hidden behind the bed plants at phone size. Lamp post 0.62 → 0.50, σ 0.45 and fence 0.56: the post line is visible but thin. |
| a | **Lower mid: hedge / bed strip lifted, warmer** (priority 3) | **CLOSER (small on Mobile)** | Warm sunlit lift on the leaf clumps / leaf cards around the clearing (elliptical zone x 5±190, z −40±135, stronger on card tops, below y 90): (1.62, 1.40, 0.86). PC: the hedges behind the fence and the side bushes turn warmer yellow-green, but Mobile shows it weaker than the box (r1 1.42 → near-invisible, so raised). Rows 560–800 88/81/23 (green now, not ochre). |
| 4 | **vs 0.6.9 lushness** (priority 4) | **sky, shafts, shadows, cottage, hedges better; bottom lawn still slightly behind 0.6.9** | Not fixed this round: both Mobile rounds were used, and an unverified change would break the "walk = shipped" rule. Listed first in §6. |
| S3 | Sky shafts | **kept** | as 0.6.12 |
| D | Low 60 fps | **estimate OK, not phone-measured** | §3 |
| N | Night | **unchanged** | PC 42/40/25 top |

**Visual estimate: about 90 %.** 0.6.12 was re-rated by Kurt's read; the dirt lawn made it nearer 85–87 %, not 93 %. **Not 95 %, do not deliver.** Biggest gaps:
- The bottom lawn is a little flat and hazy vs 0.6.9 / concept: it needs deeper blade clumps and golden pools.
- Picket shadows are hidden by the bed plants.
- The hedge warmth is subtle on Mobile.
- The canopy is still crisper than the concept.

## 2. 0.6.13 values (changes only)
- **Blade tile:** `lawn_blades_v613.png` 256² (64 wu). Base cool (34, 64, 32) ↔ warm (68, 78, 30) by hue noise σ 22; lit patches ×(0.90 + 0.17·n) σ 16. 0.55·N² blades, 2–5 px. Tip (142, 134, 62) weight 0.62·f²·(0.45 + 0.35·hue + 0.20·lit). Clover (46, 96, 34) clusters N²/900. Flowers N²/520 (white / butter / pink).
- **Lush grade (`grade_v613`):** saturation ×1.30, gain (0.88, 1.05, 0.86). Outer lawn ×0.86×(1.08, 0.95, 0.94).
- **Shade tints:** bake (0.88, 1.00, 0.96); near_lawn shade (0.90, 1.03, 0.96), mover (0.86, 1.00, 0.96); toe (0.0040, 0.0056, 0.0040).
- **Bake classes:** prop 0.38 / σ 0.35; post 0.50 / σ 0.45; fence 0.56 / σ 0.5 (others as 0.6.12). Mover floor 0.42, σ 0.15 (`tools/near_mover_shade_v6_13.py`).
- **Bed top:** `art/ground/bake_v6_11/inner_sh_bedtop.png` (BVP 2048, `HD2D_BAKE_RECV_Y=6`) → `tools/bedtop_shade_v6_13.py` → `textures/bedtop_shade_v613.png` (0.56–1.0).
- **Hedge warm:** `warm_zone` (5, −40, 190, 135), `warm_gain` (1.62, 1.40, 0.86) day.

## 3. Perf (PC GPU ms, FORCE_MOBILE 1080x2280)
| Case | 0.6.12 r2 | 0.6.13 r1 | 0.6.13 r2 | Draws / prims |
|---|---|---|---|---|
| **Low shipped** | 0.640 | 0.657 | **0.656** | 133 / 36.5k |
| Low rays off | 0.619 | 0.635 | 0.635 | 128 |
| Low live sun | 0.722 | 0.741 | 0.741 | 144 / 37.4k |
| **High** | 0.848 | 0.867 | **0.869** | 206 / 42.4k |
| Night | 0.600 | 0.612 | 0.613 | 128 |

- Shipped Low is +0.016 ms. Night, which has none of the new work, moved +0.013, so most of this is session drift. The rest is the bed texture fetch and the zone math. Draws are unchanged. The estimate stays 57–60 fps on the Note10+, **not phone-measured**. No visual quality was traded for perf.

## 5. For 遊程: exact changes (cumulative) — 0.6.10 steps 1–8, 0.6.11 step 9, 0.6.12 step 10, 0.6.13 step 11; all still valid in 0.6.13
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


## 6. Open / next
1. Bottom lawn depth vs 0.6.9: bigger blade clumps (2–3 px darker gaps between tufts), stronger golden pools, less haze at the bottom. Needs one PC round.
2. Picket shadows: show on the soil in front of the bed plants (shift the bed seedlings back) or accept as hidden.
3. Hedge warmth on Mobile: check why clump light reads weaker on Mobile than on the box (tonemap / unshaded path).
4. Canopy: softer painterly clump interiors.
5. Phone-measure Low fps.
