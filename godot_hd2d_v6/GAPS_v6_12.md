# GAPS v6.12 (0.6.12-pilot, vc18): art on the 0.6.11 state (遊程 v6.9-merged code)

- **Base:** 0.6.11 (this pilot). Version: `project.godot` line 1 + `config/version="0.6.12-pilot"`, export `version/code=18`, `capture.gd` header + "hd2d v6.12 start", `art_depth.gd` "art depth v6.12 ready" / "perf v6.12 mode=".
- **PC:** RTX 4060 Laptop, Godot 4.7.2 Mobile/Vulkan. Fresh folders `v6_12_r1`, `v6_12_r2`, version line checked (`config/version="0.6.12-pilot"`). 2 Mobile rounds used (max). PC was not shut down. Shots 540x1140 (19:9), perf FORCE_MOBILE 1080x2280. No "SCRIPT ERROR" or parse error in any r2 log. The "material is null" ×4 is pre-existing.
- **Evidence (previews/):**
  - `v6_8phone_v6_9_vs_v6_12.png`: concept | 0.6.8 phone Low | 0.6.9 PC Low | 0.6.11 PC Low (shipped) | 0.6.12 PC Low (shipped) | 0.6.12 PC High. All at phone aspect.
  - `shadow_shapes_v6_12.png`: **game-view crops** (PC r2, ×2 nearest; not masks), 0.6.11 Low | 0.6.12 Low | 0.6.12 High. Rows: props; lamp + pickets + bed; cottage roof/chimney; left fg plant + bottom lawn. Far row (pet far shot) 0.6.11 vs 0.6.12.
  - `sky_shafts_v6_12.png`: PC sky crops, 0.6.11 vs 0.6.12, Low + High.
  - `walk_low_v6_12.mp4`: the ONE Low 19:9 walk (PC Mobile r2, 540x1140, 900 frames @30 fps = 30 s, crf 29). **Shipped defaults** (Low, sun shadow off, bounce 0, exposure 1.50, no grade env). Sampled at 10 fps: frame diff median 16.8, max 21.2 (no spikes).

## 1. Status vs concept (phone aspect)
| # | Item | Status | Note |
|---|---|---|---|
| S1 | **Object shadows READ on camera** (priority 1) | **CLOSER: props now read; pickets/lamp still faint in Low** | Bake classes: prop 0.53 → 0.38, cottage 0.47 → 0.42, fence/post 0.70 → 0.62 (GAPS §6), σ class 0.7 for fence/post, 0.5 for prop/cottage (sharper near contact). Class-depth blur 2.5 → 0.9 wu. Contact AO 0.34 → 0.42. **Tree shade lighter and dappled so objects layer on top:** canopy 0.50–0.72 → 0.72–0.88 + dapple ±0.08; bush 0.62 → 0.72; trunk 0.64. Inner bake medians: canopy 0.77, bush 0.76, trunk 0.67, fence 0.62, post 0.66, cottage 0.50, prop 0.40. The per-object hierarchy holds. **Two in-camera killers found and fixed:** (1) the near-lawn mover shade was sampled as linear, so a 0.50 shade showed as 0.73 on screen. It is now decoded as a display ratio (pow 2.2), and the mover ratio uses γ 1.15 with floor 0.36. (2) The AI base ground's painted value noise competed with the shade, so the bake keeps 40 % of the base's fine contrast (σ 2 wu low-pass; paths and beds kept). near_lawn shade_floor 0.66 → 0.48. **Result (PC r2):** crate, jar, toolbox, can and pot shadows are visible as dark shapes to the right of each prop. The left fg plant shadow reads. **Gaps:** lamp-post line and picket shadows are still faint in Low. Pickets fall on the bed meshes, which are not part of the baked ground. Low prop shade is still softer than High live. Cottage roof/chimney shade lands on the hedge and ground right of the cottage: it reads as a mass, but the chimney notch is not distinct at phone size. |
| S2 | Far trees / hedges cast shadows | **MATCHED (bake), kept** | Unchanged from 0.6.11; far row in `shadow_shapes_v6_12`. |
| S3 | **Sky shafts visibly emerge from cloud gaps on PC** (priority 2) | **MATCHED on PC** | Alpha ×1.4: art rays Low 0.80 → 1.12, High 0.42 → 0.59; 遊程's 12 High shafts a0×1.6 → a0×1.6×1.4. break_boost 0.9 → 1.25 (brightest right under the break). Cloud occlusion 0.92 kept, plus a soft shoulder, so no hard top line or core. PC r2 Low/High: 3 beams visible from the cloud break down to the treeline at phone aspect (`sky_shafts_v6_12.png`). |
| a | **Mid-ground balance** (priority 3) | **CLOSER: upper mid ≈ target, lower mid still under** | PC r2 Low shipped, rows 400–560: **122/96/44** (target 114/98/42; 0.6.11 134/107/53). Rows 560–800: **100/79/31** (target 121/94/45; 0.6.11 102/82/34). Changes: Low exposure 1.50 (tested: 1.58 → 103/82/32, 1.44 → 98/77/29); back lawn behind the cottage line albedo ×0.84 (bake, z −30 → −95) and outer lawn ×0.84; clump aerial haze 0.52 → 0.30; lawn lift centred on the clearing (gain 1.0, z 5, rz 110); warm clump day light ×(1.12, 1.07, 0.96). Lower mid is dominated by the hedge/bed belt (rows 560–680 = 90 vs concept 131, a much closer framing with a sunlit wall). Lawn/clump lifts moved it +1–3 only on Mobile (the variant with HD2D_CLUMP 1.22/1.15/1.0 and LAWN 1.3 also gave only +2). |
| 2 | **Bottom lawn down ~10 and calmer** | **MATCHED** | PC r2 Low rows 800–1140: **71/62/28** (concept 75/64/32; 0.6.11 86/76/34). Calmer base (bake 40 % fine contrast). Fg plant shade is deeper. |
| e | **Canopy closer to concept clump size** (priority 4) | **CLOSER** | Lobes clamp(r/13, 3, 7) → clamp(r/20, 2, 5) (fewer, bigger masses), deeper gaps (cavity 0.12 → 0.22) and a stronger lit top. Same card count, so no cost. Still crisper/sprayier than the concept's soft painted clumps. |
| b | High bottom DOF smudges | **kept** | PC High bottom 53/45/18 (0.6.11 61/53/21; darker with the calmer lawn, still lifted vs 0.6.10 43/41/9). |
| c | Warm bounce | **kept** | High 0.26, Low 0 (default). |
| d | Atmospheric layering | **kept, slightly less glare** | High fog 0.04, light 0.70; clump aerial 0.30; ring haze 0.50. High rows 400–560 128/103/50 (0.6.11 135/109/55). |
| f | Idle wind sway | **MATCHED** (unchanged) | |
| D | Low 60 fps | **estimate OK, not phone-measured** | §3: shipped Low 0.640 ms (0.6.11 0.648). |
| E | High 50+ | **unverified** | 0.848 ms (0.6.11 0.853). |
| N | Night | **unchanged** | PC 42/40/25 top (same as 0.6.11). |

**Visual estimate: about 93%** (0.6.11 was 91%). **Not 95%, do not deliver.** Biggest gaps:
- Lamp and picket shadows are still faint in Low.
- Lower mid is ~20 under the concept (it is a framing/hedge-belt issue more than exposure).
- Low prop shade is softer than High.
- The canopy is still finer than the concept.

## 2. 0.6.12 values (changes only; the rest as GAPS_v6_11 §2)

**Bake (`tools/bake_ground_v6_11.py`, same inputs `art/ground/bake_v6_11`)**
- Class dark/σ:
  - canopy 0.70/1.0 → canopy shade 0.88 − 0.16·core, dapple ±0.08·(1 − 0.6·core);
  - trunk 0.64/0.7; bush 0.72/1.0;
  - cottage 0.42/0.5; prop 0.38/0.5;
  - fence 0.62/0.7; post 0.62/0.7.
- Dark map blur 0.9 wu. AO 0.42.
- Base ground: 0.40·base + 0.60·blur(base, 2 wu). Back-lawn albedo ×(1 − 0.16·smooth((−30 − z)/65)).

**Near lawn**
- `tools/near_lawn_v6_12.py` (same as v6.11; the base calm now lives in the bake).
- `tools/near_mover_shade_v6_12.py`: mover = max(ratio^1.15, 0.36), σ 0.25.
- `near_lawn.gdshader`: shade_floor 0.48, mover decoded pow 2.2.

**Grade**
- Low exposure 1.50.
- High fog 0.04, fog light energy 0.70.
- Lawn lift gain 1.0 at (10, 0, 5), r (170, 110).
- Clump day light (1.12, 1.07, 0.96).
- clump aer_amt 0.30.
- grass_outer_v612 ×0.84.

**Shafts:** alpha ×1.4 (Low 1.12 / High 0.59; 遊程 a0×2.24), break_boost 1.25.

**Canopy:** nl = clamp(r/20, 2, 5); `val = 0.60 + 0.55·lg·(0.55+0.45·grad) + 0.42·lg² + 0.32·lit·(0.5+0.5·rim) + 0.03·h2 − 0.22·cav`; cav = clamp((lr − 0.50)/0.55)·clamp(0.65 − ln.y).

**New env hooks (inert by default):** `HD2D_CLUMP=r,g,b`, `HD2D_LAWNZ`, `HD2D_LAWNRX`, `HD2D_LAWNRZ`.

## 3. Perf (PC GPU ms, FORCE_MOBILE 1080x2280)
| Case | 0.6.11 r2 | 0.6.12 r1 | 0.6.12 r2 | Draws / prims |
|---|---|---|---|---|
| **Low shipped (sun shadow off, bounce 0)** | 0.648 | 0.642 | **0.640** | 133 / 36.5k |
| Low shipped, rays off | (0.728 noisy) | 0.623 | 0.619 | 128 |
| Low live sun | 0.778 | 0.727 | 0.722 | 144 / 37.4k |
| **High** | 0.853 | 0.856 | **0.848** | 206 / 42.4k |
| Night | 0.603 | 0.602 | 0.600 | 128 |

- Every 0.6.12 change is texture-side or a uniform: no new draws, passes or lights. Shipped Low is within noise of 0.6.11 (−0.008 ms), so the estimate stays 57–60 fps on the Note10+. **Not phone-measured.** No visual quality was traded for perf.

## 4. PC rounds
- **r1** (`v6_12_r1`): shots low / low_live / low_far / high / night + exposure 1.58 / 1.44 + clump/lawn lift variant; perf ×5. This round found the lower-mid gap and the weak lawn/clump lift on Mobile.
- **r2** (`v6_12_r2`): r1 plus lighter canopy/bush shade (bake), fog tweak (High); shots + perf + the ONE walk (shipped defaults). The 161 MB avi was split into 90 MB parts on the PC, joined on the box and encoded with crf 29.

## 5. For 遊程: exact changes (cumulative) — 0.6.10 steps 1–8, 0.6.11 step 9, 0.6.12 step 10; all still valid in 0.6.12
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


## 6. Open / next
1. Low lamp-post line + picket shadows: bake the bed tops into the ground (or a small decal strip on the bed soil), then post 0.55.
2. Lower mid (rows 560–680): lift the hedge/bed belt itself (bush hull shader warm lit side), not the lawn.
3. Low prop shade: a slightly sharper props pass (σ class 0.35) after a phone check.
4. Canopy: softer painted clump interiors.
5. Phone-measure Low shipped fps.
