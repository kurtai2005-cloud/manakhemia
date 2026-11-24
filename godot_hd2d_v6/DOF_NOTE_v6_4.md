# DOF / shadow note for 遊程 (v6.4) — proposals only, no DOF/renderer code changed

Kurt's v6.2 High phone capture (and the v6.4 RTX 4060 Mobile render) show DOF far too strong, with focus off 團絨.

## Recommended Mobile DOF (High only)
- Focus on 團絨: every frame set `far_distance = d_pet + 90`, `near_distance = max(d_pet - 70, 10)`, where `d_pet = camera.global_position.distance_to(pet.global_position)` (≈ 335 at the opening shot).
- `dof_blur_far_transition = 260` (was 220), `dof_blur_near_transition = 90` (was 64).
- `dof_blur_amount = 0.06` on Mobile (was 0.12; 0.28 at setup). Keep `dof_blur_quality = LOW`, bokeh shape BOX.
- Near blur: either off on Mobile or ≤ 0.04. The v6.4 foreground frame sprites are already pre-softened, so Low and High look alike without near blur.

## Sun shadows / fake shadows on Mobile
- v6.4 already bakes the High sun-shadow mask into `textures/ground_composed_low.png` (art only). `art_depth.gd` swaps it in whenever `_sun.shadow_enabled == false`, so Low has long tree/house shadows at 0 runtime cost.
- If High is still slow on Note10+: keep the baked ground and enable the real sun shadow only for the cottage, pet and props:
  - `directional_shadow_max_distance ≈ 450`;
  - `shadow_mode = PARALLEL_2_SPLITS`;
  - shadow atlas 2048;
  - set the trees' and canopies' `cast_shadow = OFF`, because the bake already has their shadows.
- Re-run the bake (`HD2D_BAKE_SHADOW=1`, see tools/bake_low_ground_v6_4.py) after moving any tree or the cottage.

## Grade (environment = your code; proposal)
On the RTX 4060 Mobile render the lawn mean is (62,60,18) vs TARGET (62,57,20): close. B/G is 0.30 vs 0.36. Proposals:
- `adjustment_saturation` 0.86 → 0.80;
- `adjustment_contrast` 1.18 → 1.24.
Both are free on Mobile.
