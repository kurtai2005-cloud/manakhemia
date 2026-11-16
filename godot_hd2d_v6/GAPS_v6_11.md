# GAPS v6.11 (0.6.11-pilot, vc17): art on the 0.6.10 state (遊程 v6.9-merged code)

- **Base:** 0.6.10 (this pilot). `capture.gd`: version header + "hd2d v6.11 start" print only.
- **PC:** RTX 4060 Laptop, Godot 4.7.2 Mobile/Vulkan. Fresh folders `v6_11_r1`, `v6_11_r2` (version line checked: `config/version="0.6.11-pilot"`). 2 Mobile rounds used (max). Shots 540x1140 (19:9), perf FORCE_MOBILE 1080x2280.
- **Evidence (previews/):**
  - `v6_8phone_v6_9_vs_v6_11.png`: concept | 0.6.8 phone | 0.6.9 | 0.6.10 | 0.6.11 (PC r2), Low row + High row.
  - `shadow_shapes_v6_11.png`: top-down per object (v6.10 | v6.11 | caster outline/footprint | v6.11 sun mask), in-camera crops 0.6.10 vs 0.6.11 Low + High, far crop + wide-bake mask.
  - `sky_shafts_v6_11.png`: sky crops ×2, 0.6.10 vs 0.6.11, Low + High.
  - `walk_low_v6_11.mp4`: the ONE Low 19:9 walk (PC Mobile, 540x1140, 900 frames @30 fps, crf 29). Sampled at 10 fps: frame diff median 17.1, max 21.3 (no spikes). Note: rendered with the lawn bounce ON (0.26); shipped Low default is bounce 0 (see D) — only the cottage-wall warmth differs.

## 1. Status vs concept (phone aspect)
| # | Item | Status | Note |
|---|---|---|---|
| S1 | **Shadows follow each object's real silhouette** (top priority) | **CLOSER — shape-exact in the bake, still weakly readable in camera** | Bake shadow map is now ONE orthogonal 8192 map (0.06 wu texels, was ~0.3 wu High atlas/2 splits → stair-steps → blurred blobs). Inner bake 1024² (4 px/wu). Softness ≈ physical sun penumbra σ = (0.12 + 0.0045·d)·class. **Painted round shade blobs removed** from the base ground (`ground_composed.png` had v6.4 blobs; `tools/ground_deblob_v6_11.py` → clean base; High uses it too). Near-lawn macro re-derived from the new bake, random "cool shade pools" removed. Mask column in `shadow_shapes` shows lamp post + lantern head, pickets, crates, pots, cottage block. **Gap:** in the hero view most of the clearing lies inside the main canopy's (true) shadow and per-object shade is mild (0.53–0.70), so pickets / lamp / chimney read only faintly in camera. Next: deepen post/fence to ~0.62 and blur the class-depth map 1.2 wu instead of 2.5 wu (texture-only, no fps cost) — not done because no PC round was left to verify. |
| S2 | **Far trees / bushes / hedges cast shadows** | **MATCHED (bake)** | 129 far casters (FarForest rows, OuterRing trees + bushes, all leaf clumps) cast in the bake now; far shade lifted / haze-tinted with distance (+0.25) and contact AO at the bases. Painted backdrop ring keeps its analytic treeline shadow (0 draws). Wide mask in `shadow_shapes`. |
| S3 | **Sky shafts emerge from the clouds** | **MATCHED on box, FAINT on PC** | `tools/sky_cloudmask_v6_11.py` → `sky_cloud_v611.png` (R cloud body, G sun-facing edge) from our own sky. `light_shaft.gdshader` looks the sky up with the dome's exact mapping: above the break the beam is occluded by the cloud body (no start line / no top edge), brightest right under the break, long fade. Cards 380 → 500 tall. `sky_dome.gdshader`: golden rim on sun-facing cloud edges (rim_amt 0.6) + slight gap glow. On PC Mobile the beams are faint overall (as in 0.6.10); readable in the walk. |
| a | Mid-ground warm golden-hour light | **CLOSER / overshoots in rows 400–560** | Lawn texture grade, exposure Low 1.58 / High 1.45, sky tint ×0.92, warm sun (1, 0.84, 0.66) ×1.16. PC r2 Low rows 400–560 = 134/107/53 (concept 114/98/42, 0.6.10 95/79/31); rows 560–800 = 102/82/34 (concept 121/94/45, 0.6.10 79/66/23). Upper mid now a bit too bright, lower mid still under. |
| 2 | Bottom lawn calmer, ~67/60/28 | **CLOSER** | Blade tile: large-scale ochre/green blotches ×0.55, local detail ×0.72; detail 0.24 → 0.18; contrast mix 0.80 → 0.70; foreground highlight cut, olive desat + blue toe. PC Low rows 800–1140 = 86/76/34 (concept 75/64/32; 0.6.10 64/60/16): hue/blue now right, ~10 too bright; still more texture than the concept (std 32 vs 27). |
| b | High bottom dark DOF-like smudges | **CLOSER** | `near_lawn` light(): foreground directional shadow lifted ×0.45 (shape kept). PC High bottom 61/53/21 (0.6.10 43/41/9). |
| c | Warm bounce onto walls / prop undersides | **High: MATCHED (subtle); Low: option** | One shadowless DirectionalLight travelling up/back (never lights the up-facing lawn), (1, 0.76, 0.44) × 0.26. PC cost +0.046 ms High, +0.047 ms Low (0.648 → 0.695) → Low default 0 (`HD2D_GRADE=bounce=0.26` to enable). |
| d | Atmospheric layering fore/mid/back | **CLOSER** | clump_card aerial haze (gold, 330→760 wu) aer_amt 0.52; backdrop ring haze 0.50; High depth fog 0.05 (400→1100). Low env fog stays off (fog_enabled = high in capture.gd); Low distance haze is in-shader (0 cost). |
| e | Canopy = larger leaf masses, lit vs shadow sides | **CLOSER** | 3–7 lobes per crown, sprays shaded from their lobe normal (top-lit / underside dark, cavity term), calmer spray atlas (interior std 34.7 → 25.0). Wispy edges kept. Still finer than the concept's soft painterly clumps. |
| f | Idle wind sway (leaves / flowers / grass) | **MATCHED** | Leaves (clump_card), tufts, fg plants already swayed with the shared wind(); bed flowers now too (`bed_flower.gdshader` idle_sway 0.9, vertex only). |
| 4 | Low background haze / blur | **CLOSER (haze), blur BELOW** | Haze free (shader). No real Low DOF (cost). |
| 5 | Low rays | **KEPT** | rays=0 option saves ~0.02 ms (r1 0.632 → 0.617); r2 norays reading 0.728 is noise. |
| D | Low 60 fps | **estimate OK, not phone-measured** | §3. |
| E | High 50+ | **BELOW / unverified** | unchanged from 0.6.10. |
| N | Night | **unchanged** | PC night 42/40/25 top (0.6.10 r1 40/39/24); day fog is reset to 0 at night. |

**Visual estimate: about 91%** (0.6.10 was 89%). **Not 95% — do not deliver.** Biggest gaps: S1 readability in camera, S3 faint on PC, mid-ground balance (upper mid too bright, lower mid too dark), bottom lawn still busier/brighter than the concept, canopy still finer than the concept.

## 2. 0.6.11 values
- **Grade (`art_depth._grade_v611`, day only; HD2D_GRADE keys sun, warm, sky, expl, exp, amb, ring, fog, fogb, foge, bounce):** sun 2.6×1.16, colour (1, 0.84, 0.66); exposure Low 1.58 / High 1.45; sky tint (0.98, 0.88, 0.74)×0.92; ambient (0.52, 0.58, 0.68)×0.26; fog density 0.05, 400→1100, curve 1.2, light (1, 0.84, 0.58)×0.85, sun scatter 0.35 (High only); ring haze 0.50; bounce 0.26 (High).
- **Lawn grade (`tools/lawn_grade_v6_11.py`):** c·(1.17, 1.04, 1.00) + (2, 2, 10)·(1 − c/255); blade tile calmer (above). Applied to `lawn_blades_v611.png`, `grass_outer_v611.png`, `ground_composed_low(_props).png`, `ground_composed_hi_v611.png`.
- **Near lawn (`near_lawn.gdshader`):** fg_dim 0.86 (70→190 wu), fg_hi_cut 0.55, desat 0.16 + blue toe (0.0015, 0.0025, 0.0085), fg_sh_lift 0.45 (custom Lambert light()).
- **Bake (`tools/bake_ground_v6_11.py`, inputs `art/ground/bake_v6_11`, `art/ground/ground_composed_clean_v611.png`):** 8192 orthogonal map (`HD2D_BAKE_HIRES`, default on; max dist 480 inner / 1300 wide, bias 0.03, normal bias 0.6); threshold 0.30–0.50; fence 0.70 σ×1.0, post 0.70 σ×1.0 (others as 0.6.10); far casters on. `--sunview` = diagnostic sun-view silhouette reprojection (HD2D_BAKE_SUNVIEW=1) — **not used**: it also shows voxel-tree parts that never cast in game; the engine shadow map stays the truth so Low bake == High live shapes.
- **Near macro / mover shade:** `tools/near_lawn_v6_11.py` (inner at full 4 px/wu, σ 0.3 wu, no cool pools, warm pools ×0.5); `tools/near_mover_shade_v6_11.py` (prop shade from the 4 px/wu inner bakes).
- **Sky:** `sky_cloud_v611.png`; shaft cloud_occl 0.92, break_boost 0.9; dome rim_amt 0.60, break_amt 0.10.
- **Canopy:** lobes nl = clamp(r/13, 3, 7) at 0.52 r; `val = 0.62 + 0.55·lg·(0.55+0.45·grad) + 0.38·lg² + 0.30·lit·(0.5+0.5·rim) + 0.04·h2 − 0.12·cav`; `canopy_spray_atlas_v611.png`. HD2D_LOBES=0 disables.

## 3. Perf (PC GPU ms, FORCE_MOBILE 1080x2280)
| Case | 0.6.10 | 0.6.11 r1 | 0.6.11 r2 | Draws / prims |
|---|---|---|---|---|
| **Low shipped (sun shadow off), bounce 0** | 0.625–0.633 | 0.632 | **0.648** | 133 / 36.5k |
| Low shipped + bounce 0.26 | – | – | 0.695 | 133 |
| Low shipped, rays off | 0.615 | 0.617 | (0.728, noisy) | 128 |
| Low live sun | 0.718 | 0.715 | 0.778 | 144 / 37.4k |
| **High (bounce 0.26)** | 0.780–0.788 | 0.784 | **0.853** | 206 / 42.4k |
| High bounce 0 | – | – | 0.807 | 206 |
| High fog 0 | – | 0.784 | – | 206 |
| Night | 0.594 | 0.596 | 0.603 | 128 |

- Shipped Low +0.015–0.023 ms vs 0.6.10 (1024² ground + near macro sampling, sky/shaft cloud lookups). Estimate still 57–60 fps on the Note10+ (0.6.10 estimate), **not phone-measured**.
- High +0.07 ms (+0.046 is the bounce). High 50+ was already unverified.

## 5. For 遊程: exact changes (code side) — 0.6.10 steps, still valid in 0.6.11
1. **Low:** `_sun.shadow_enabled = false` when mode == low (day). Keep the bake. The art layer auto-detects Low with sun shadow off and turns on the props ground, the props wide mask, near mover shade and the pet silhouette (`art_depth._low_fake_shadow`). Preview flag: `HD2D_LOW_FAKE=1`.
2. **Bake pass bug:** `_apply_shadow_policy` sets `_sun.shadow_enabled = (not night) and (not bake_pass)`, which made the bake empty (3 draws). Art forces it ON in `_setup_shadow_bake` and `_process` while baking. Please make bake_pass keep the sun shadow.
3. **Jar:** not a live caster (your v6.9). It is now baked (removed from art HY_PROPS).
4. **Your 12 High shafts:** the art layer swaps their material to `light_shaft.gdshader` (tint (1, 0.86, 0.62), alpha = your alpha × 1.6 × graze × cloud), width ×1.7 (min 40), cast_shadow OFF, axis = SUN_TO.
5. **Ambient (0.62, 0.66, 0.86) +0.05 tested (HD2D_AMB=1, PC High):** mean diff 1.85. Shadows turn slightly bluer, away from the concept's olive-gold shade. **Recommend NOT applying**; the bake already tints the interiors blue-violet.
6. **Export filter:** added `art/ground/bake_*, textures/*_hard.png(.import)`.
7. **"Parameter material is null" ×4:** present in the merged build before and after reimport; looks like capture.gd ~169. Non-fatal, still open.
8. **Test hooks (env only, inert otherwise):** `HD2D_HI=atlas=,dist=,softq=,splits=1,shafts=0,dof=0,glow=0,casters=hy,rays=0,skyfx=0,petsh=0`, `HD2D_AMB=1`, `HD2D_POOL_GAIN=`, `HD2D_FG_LIST=1`, `HD2D_DBG_NOCAST=<prefix|ALL>`.


9. **0.6.11 additions for 遊程 (art side, no code change needed):** bake pass now sets an 8192 orthogonal sun shadow (`_setup_shadow_bake`), enables far casters only in the bake, `HD2D_BAKE_SUNVIEW` diagnostic; GroundInner High albedo → `ground_composed_hi_v611.png`; `LawnBounce_v611` DirectionalLight (High only by default; please keep it out of any light-count limits); env fog values set every day frame, reset to 0 at night. Export filter + `art/ground/ground_composed_clean_*`.

## 6. Open / next
1. S1 in-camera readability: post/fence 0.62, class-depth blur 1.2 wu, maybe cottage 0.42 — texture-only, verify on PC.
2. Mid-ground balance: Low exposure 1.58 → ~1.50 and lift rows 560–800 (cottage wall / lawn behind the fence) instead of the whole frame.
3. Shafts on PC: alpha ×1.3–1.5 on Low (additive; verify no wash).
4. Phone-measure Low shipped fps; decide bounce on Low (+0.047 PC ms) and rays.
5. Canopy: softer painterly clump interiors (concept), still not balls.
