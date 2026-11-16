# GAPS v6.10 (0.6.10-pilot, vc16): art on 遊程 v6.9-merged code

- **Base:** `godot_hd2d_v6_9-merged`. Copied unchanged: `capture.gd` (version header line 2 + "hd2d v6.10 start" print only), `prop_bump.gd`, `data/prop_bump.json`, `bed_flower.gdshader`.
- **Minimum:** TARGET_concept.jpg at phone aspect. BELOW is never "done".
- **PC:** RTX 4060 Laptop, Godot 4.7.2 Mobile/Vulkan. Shots at 540x1140 (19:9). Perf with FORCE_MOBILE at 1080x2280, average of frames 120–720.
  - Rounds: r1a/r1p (round 1), r2b + r2c (round 2). r2c was a re-run because r2b's walk quit after 20 frames (a script bug set HD2D_OUT for the walk); it also checked the night-pool gain.
- **Evidence (previews/):**
  - `shadow_layering_v6_10.png`: before/after, same view, Low + High, crops + value table.
  - `sky_light_v6_10.png`
  - `perf_quality_check_v6_10.png`: same view live vs shipped Low, High vs High-hy, diff maps, perf table.
  - `v6_8phone_v6_9_vs_v6_10.png`: concept | 0.6.8 phone | 0.6.9 | 0.6.10, Low and High.
  - `walk_low_v6_10.mp4`: PC Mobile Low, 19:9 540x1140, 900 frames at 30 fps. Frame diff median 7.5, max 10.9, no spikes.
  - `walk_strip_low_v6_10.png`, `pan_low_v6_10.png`

## 1. Status vs concept (phone aspect, vs 0.6.8 phone + 0.6.9)
| # | Item | Status | Note |
|---|---|---|---|
| A | Shadow hierarchy: deep / light per object | **MATCHED** | Per-class bake (§2). Deepest: cottage, crates, canopy cores. Lightest: fence, posts. Canopy core→edge by density. Contact hardening from the real occluder distance. |
| B | Far ground has shadows | **MATCHED** | The static shade is no longer faded with distance: aerial lift +0.25 and haze tint. The painted backdrop ring casts an analytic treeline shadow (0 draws). See the far-lawn crop in `shadow_layering`. |
| C | Sky light soft, no bands, rays vary and drift, blends into gold haze | **MATCHED** (box + PC) | Glow and rays now live in the sky dome around the real sun vector. Shafts are multi-beam gaussians along SUN_TO; v6.9 had vertical columns. Glow texture is warm 256 px and dithered (old one stepped in 7 bands). Rays read clearly in the walk; in some stills the cloud gate makes them faint. |
| D | Low 60 fps, no visible loss | **MATCHED (estimate)** / **not measured on the phone** | §3. Shipped Low has no shadow pass. Its PC GPU time is 0.625–0.633 ms (baked-only 0.590, hybrid 0.668). |
| E | High 50+ | **BELOW / unverified** | No cheap GPU win on PC without visible loss (§3). `casters=hy` cuts 49 draws and looks identical, but saves 0 PC GPU. |
| F | Bottom lawn (dark / busy) | **CLOSER, still BELOW** | Shipped Low bottom is 63/60/16 vs concept 67/60/28 (0.6.9: 53/56/7). The blade texture is still busier and less golden than the concept. |
| G | Night ground pools (string lights, window, lamp) | **MATCHED (subtle)** | Additive MultiMesh, gain 0.5, drawn before the pet. Checked on PC at gains 0 / 0.22 / 0.5; r1/r2b at full gain made a beige slab over 團絨. |
| H | Flower-bed bend | **MATCHED** (遊程 `bed_flower.gdshader`) | |
| I | Mid-ground exposure / warmth | **BELOW** | Concept rows 400–800 are 119/95/44; ours are 81–84/67–71/22–29. The concept's lit lawn is much brighter and more golden. Not changed: no PC round left to verify. Proposal in §5.4. |
| J | Background softness (concept DOF) | **BELOW on Low** | High has DOF. Low has none (cost). |
| K | Canopy busyness | **BELOW** | Crowns are finer and noisier than the concept's rounded clumps. Not touched this round. |

**Visual estimate:** about 89% (0.6.9 was about 86%). It is not 95%; the main gaps are I, F, K and J.

## 2. Shadow values (art side; `tools/bake_ground_v6_10.py`, art/ground/bake_v6_10 inputs)
Inputs: top-down 1024² passes (inner 256 wu, wide 900 wu): sun shadow, height (`HD2D_BAKE_HEIGHT`), footprint (`HD2D_BAKE_FOOT`) and class ID (`HD2D_BAKE_ID`, new). Each shadow texel is marched toward the sun to find the occluder distance d and its class.

| Class | Lit fraction at core | Softness × σ | Contact AO weight |
|---|---|---|---|
| cottage (eaves, walls, porch, posts) | 0.47 | 0.6 | 1.0 |
| prop (crates, pots, cans, jar) | 0.53 | 0.7 | 1.0 |
| canopy | 0.50 core → 0.72 edge (by shade density), ±0.05 dapple | 1.0 | 0.55 |
| trunk | 0.58 | 0.8 | 0.85 |
| bush | 0.62 | 1.1 | 0.80 |
| fence | 0.80 | 1.4 | 0.40 |
| lamp / string-light post | 0.82 | 1.5 | 0.45 |
| none (fallback) | 0.66 | 1.0 | 0 |

- **σ** = (0.5 + 0.03·d) × class softness.
- **Lifts:** long shadows +0.30·clip(d/260); cottage +0.12·clip((d−20)/120).
- **Aerial:** far = smoothstep(280, 620) of distance from the camera (12, 208). Lift +0.25·far. Tint cool (0.90, 0.95, 1.16) near → haze (1.04, 1.00, 0.86) far.
- **Blur and AO:** dark map blurred 2.5 wu. AO = 0.60·g(1.4) + 0.34·g(4.5), strength 0.34.
- **Measured inner brightness (p10 / median):** canopy .55/.63, trunk .55/.59, cottage .47/.55, fence .59/.74, bush .61/.67, prop .52/.54, post .83/.88.
- **Runtime (`ground_dapple.gdshader`):**
  - static_amt 0.34 (art_depth); scol = mix(shade_col, haze_col (0.36, 0.33, 0.17), far); st × (1 − 0.20·far).
  - Only flecks and leaf shade fade at 360–480.
  - Ring shadow: ring_h = `ring_height_v610.png` (512x4, h/400), r 462, yaw 180°, h_scale 0.55, amt 0.30, penumbra 10 + 0.1·d.
- **Low without sun:**
  - `ground_composed_low_props.png` + `shadow_wide_mask_props.png`: props / jar baked (`--props`, HD2D_BAKE_PROPS=1).
  - `near_mover_shade.png` (`tools/near_mover_shade_v6_10.py`): fg-plant cards projected along the sun (they face the camera, so a top-down bake can't see them) + prop shade. Applied after the near-lawn shade floor (`mover_amt`).
  - Pet: `pet_shadow.gdshader` silhouette quad sheared by L = (0.645, 0, 0.453)/0.616. 9-tap blur 0.6→4 px, opacity 0.58, cloud-modulated, 1 draw.

## 3. Perf (PC GPU ms, FORCE_MOBILE 1080x2280) and phone estimate
| Case | GPU ms | Draws / prims |
|---|---|---|
| 0.6.9 Low baked-only (≈0.6.8, phone 60) | 0.590 | 132 |
| 0.6.9 Low hybrid (phone 47–48) | 0.668 | 145 |
| 0.6.9 High (phone 41–43) | 0.747 | – |
| 0.6.10 Low live sun shadow | 0.718 | 144 / 37.4k |
| **0.6.10 Low shipped (sun shadow off)** | **0.625–0.633** | **133 / 36.5k** |
| … rays off / sky fx off / pet shadow off | 0.615 / 0.634 / 0.635 | 128 / 133 / 132 |
| 0.6.10 High | 0.780–0.788 | 206 / 42.4k |
| High casters=hy / +1 split +300 | 0.779 / 0.796 | 157 / 37.6k |
| 0.6.10 Night | 0.594 | 128 |

- **Estimate:** on 0.6.9, the shadow pass (+0.078 PC ms) cost 60→47 fps on the Note10+. Shipped Low has no shadow pass and is +0.035–0.043 PC ms of ALU over baked-only (rays 0.018 of it). **Estimate 57–60 fps, not measured.** If it lands at 55–57, set rays off on Low (−0.018 ms). The visual cost is the soft diagonal rays on Low, so that needs Kurt's OK.
- **Kept, because cutting them is visible:** DOF off on High (0.680 ms, visible loss); glow off (visible). Atlas 1024 / dist 300 saves only 0.012–0.02 ms, with local differences (p99 24).
- **High 50+:** not reachable on PC numbers without visible loss. `casters=hy` (pet, FgPlants, pots/cans/crates live; cottage, fence and trees from the bake) is visually identical (mean diff 1.3) and removes 49 draws. It may help a CPU/driver-bound phone, but it is unproven.

## 4. For 遊程: exact changes (code side)
1. **Low:** `_sun.shadow_enabled = false` when mode == low (day). Keep the bake. The art layer auto-detects Low with sun shadow off and turns on the props ground, the props wide mask, near mover shade and the pet silhouette (`art_depth._low_fake_shadow`). Preview flag: `HD2D_LOW_FAKE=1`.
2. **Bake pass bug:** `_apply_shadow_policy` sets `_sun.shadow_enabled = (not night) and (not bake_pass)`, which made the bake empty (3 draws). Art forces it ON in `_setup_shadow_bake` and `_process` while baking. Please make bake_pass keep the sun shadow.
3. **Jar:** not a live caster (your v6.9). It is now baked (removed from art HY_PROPS).
4. **Your 12 High shafts:** the art layer swaps their material to `light_shaft.gdshader` (tint (1, 0.86, 0.62), alpha = your alpha × 1.6 × graze × cloud), width ×1.7 (min 40), cast_shadow OFF, axis = SUN_TO.
5. **Ambient (0.62, 0.66, 0.86) +0.05 tested (HD2D_AMB=1, PC High):** mean diff 1.85. Shadows turn slightly bluer, away from the concept's olive-gold shade. **Recommend NOT applying**; the bake already tints the interiors blue-violet.
6. **Export filter:** added `art/ground/bake_*, textures/*_hard.png(.import)`.
7. **"Parameter material is null" ×4:** present in the merged build before and after reimport; looks like capture.gd ~169. Non-fatal, still open.
8. **Test hooks (env only, inert otherwise):** `HD2D_HI=atlas=,dist=,softq=,splits=1,shafts=0,dof=0,glow=0,casters=hy,rays=0,skyfx=0,petsh=0`, `HD2D_AMB=1`, `HD2D_POOL_GAIN=`, `HD2D_FG_LIST=1`, `HD2D_DBG_NOCAST=<prefix|ALL>`.

## 5. Open / next
1. Phone-measure Low shipped fps (Note10+). If below 58, try rays=0 and compare stills.
2. Live-sun Low bottom lawn on PC Mobile is much darker than v6.9 hybrid (44 vs 53). Live shade stacks on the bake. Moot if 4.1 ships.
3. Canopy busyness: merge fine sprays into larger lit/dark clumps (concept).
4. Mid-ground exposure (I): try `HD2D_LAWN` 0.6 → 0.8 and +0.1 sun energy on Low/High, checked at phone aspect. Unverified proposal.
5. Low background softness (concept DOF): a cheap far-blur card / mip bias on the backdrop.
