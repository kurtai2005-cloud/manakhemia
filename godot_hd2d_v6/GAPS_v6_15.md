# GAPS v6.15 (0.6.15-pilot, vc21): art on 遊程 v6.14-code (not delivered; ~91 %)

- **Base:** 0.6.14. Version bumped: `project.godot` line 1 + `config/version="0.6.15-pilot"`, export `version/code=21`, capture.gd header + "hd2d v6.15 start", art_depth "art depth v6.15 ready" / "perf v6.15 mode=".
- **遊程 coordination (art only this round):** engine items (bake-pass shadow policy, material-null errors, left-fence dark-rectangle bake bounds, Mobile tonemap diffs, phone fps) are 遊程's. art_depth.gd: the `_bake_shadow_ground` conflict guard (~line 235) and `_hybrid_shadow` (func ~2369) were NOT touched (diff vs 0.6.14 checked), so his move to capture.gd merges cleanly.
- **PC:** RTX 4060 Laptop, Godot 4.7.2 Mobile/Vulkan.
  - Round 1: fresh folder `v6_15_r1`.
  - Round 2: `v6_15_r2` was interrupted by accident at ~45 s, so round 2 ran in the fresh folder `v6_15_r2b` (zip md5 522eb1ec…). That is the 2nd and last Mobile round.
  - The version line was checked each time. There is no SCRIPT or shader error in any log, and the PC was not shut down.
- **Rebase onto 遊程 v6.14-code (after round 2):**
  - `scenes/capture.gd` and `scenes/prop_bump.gd` were taken from `/home/box/keep/遊程/v6_14/`. My 0.6.15 capture.gd changes (header, start print, pool defaults, `pool_off`) were re-applied.
  - art_depth: the per-frame forced bake sun in `_process` was removed, because his bake_pass keeps the sun ON.
  - The `_bake_shadow_ground` guard (~229) and `_hybrid_shadow` were left as they were.
  - Box check: default Low equals `HD2D_LOW_FAKE=1` (mean 82.5 vs 82.5). Every PC Low shot and the walk were taken with `HD2D_LOW_FAKE=1`, so the r2b Low look is the rebased default. No −7 compensation was needed on the art side.
  - The staging zip = the r2b art + 遊程's capture.gd / prop_bump.gd. That exact combination was NOT run on Mobile; the box only.
- **Not done (usage):** widening the left-fence bake bounds in `_setup_shadow_bake`. It needs a full re-bake plus sharpness checks. It is next.
- **Evidence (previews/):**
  - `v6_8phone_v6_9_vs_v6_15.png`: concept | 0.6.8 phone | 0.6.9 | 0.6.14 Low | 0.6.15 Low | 0.6.15 High.
  - `lawn_closeup_v6_15.png`: concept | 0.6.9 | 0.6.14 | 0.6.15 Low/High.
  - `walk_low_v6_15.mp4`: the ONE Low 19:9 walk, PC r2b, 540x1140, 900 frames @30 fps, shipped defaults, x264 crf 30, 22.7 MB.

## Done (box + PC r1)
1. **Baked warm-gold sun patches** — `tools/sun_gold_v6_15.py` (from the engine's wide sun bake):
   - carves soft canopy sun breaks into the big tree shadows outside the inner bake → `textures/shadow_wide_mask_v615.png`, `shadow_wide_mask_props_v615.png` (originals kept; art_depth now loads the v615 masks for GroundDapple / Low-fake swap);
   - gold mask `textures/sun_gold_v615.png` (±450 wu, 1 px/wu): sunlit ground inside / beside canopy + prop shade, plus big soft open pools, σ 4 wu edges; never inside shade.
   - Sampled by `near_lawn.gdshader` (replaces the v6.14 sine field; × smoothstep(0.62, 0.95, vr)) and `texel_lit.gdshader` (new `gold_tex/gold_half/gold_amt/gold_gain`, default off) on GroundInner + GroundOuter. art_depth `_gold_setup()`; day only (`gold_amt` 0 at night).
   - Defaults after PC r1 (r1 read too gentle on Mobile): near (1.85, 1.50, 0.78), ground (1.60, 1.36, 0.80). Env `HD2D_GOLD`, `HD2D_GOLDG`, `HD2D_GOLDAMT`.
2. **Edge tuft silhouettes** — art_depth `_edge_tufts_v615()`: 287 crossed tuft cards (tuft_fg / tuft_dark_b, existing tuft.gdshader with wind + 團絨 push) around prop footprints (lamp, mushrooms, can, jar, pots incl. copies, bed) and the hedge / bush bases round the clearing. +4 draws (Low 133 → 137).
3. **Stronger pooling toward 團絨 / cottage** — new `pool_off` (18, −18) wu (centre shifted toward the cottage), core (1.60, 1.34, 0.86) at 0.08–0.62 r, edge (0.72, 0.74, 0.84) at 0.40–1.05 r (warmer / lighter edge than r1's 0.64/0.74/0.90 because the concept bottom is warm 68/61/29, ours went 51/58/14 = too dark-green).
4. **Canopy big soft lit masses** — `tools/canopy_soft_v6_15.py` → `canopy_spray_atlas_v615.png`: alpha unchanged (wispy edges kept), interior luminance detail ×0.30 toward a 5 px mean, hue softened inside, edges keep ×0.50. Lobes fewer / bigger (nl r/26, 2..4), lit-top term 0.40 → 0.48. Zero runtime cost.
5. **Perf PC r1 (FORCE_MOBILE 1080x2280):** Low shipped 0.687 ms (0.6.14 0.666; +4 tuft draws + gold fetch), High 0.900, night 0.633. Est. 57–60 fps unchanged, not phone-measured. No visual cut.

## Read by eye (PC r2b) — honest ~91 % (same as 0.6.14)
- **Better than 0.6.14:**
  - The clearing in front of 團絨 / the cottage is warmer and brighter (centre 113/97/31 vs 105/91/30), so the focus reads more like the concept.
  - The canopy interiors are a little softer and more painterly, with the wispy edges kept.
  - Tuft silhouettes now sit at the prop and hedge bases.
  - The gold patches show on the mid lawn and the back lawn.
- **Same as 0.6.14:** the bottom / near lawn (54/61/15 vs 56/64/16). The baked gold barely reaches the bottom band on Mobile (gold0 = default there).
- **Worse than 0.6.9 (still open):** the warm-gold vs olive patch variety on the bottom lawn. 0.6.9 wins there, and the concept bottom is warm 68/61/29. Fix: put gold sun breaks into the near band itself (z 90–170, where the camera looks) in `sun_gold_v6_15.py`, and lift the bottom edge. This needs a 3rd Mobile round.
- **Perf PC r2b (FORCE_MOBILE 1080x2280):** Low shipped 0.688 ms (0.6.14: 0.666), High 0.896, Low live 0.775, night 0.629. Draws Low 137 / High 210 (+4 tuft draws). Est. 57–60 fps, not phone-measured.

## Next (resume here)
1. Bottom-band gold patches + a warmer bottom (above). Then verify on Mobile with the rebased build.
2. Widen the bake extent past the left fence (`_setup_shadow_bake` cam.size / max_distance; keep the 8192 atlas sharp) and re-bake.
3. Phone fps (遊程's 開發者 FPS log).

## For 遊程 (step 13: rebased on your v6.14-code; per-frame forced bake sun removed from art_depth._process, cumulative with GAPS_v6_14 §5 steps 1–12)
- New textures: `sun_gold_v615.png`, `shadow_wide_mask_v615.png`, `shadow_wide_mask_props_v615.png`, `tiles/canopy_spray_atlas_v615.png`. New tools `sun_gold_v6_15.py`, `canopy_soft_v6_15.py` (re-run sun_gold after any wide re-bake).
- `texel_lit.gdshader`: `gold_*` uniforms (off by default), `pool_off`. `near_lawn.gdshader`: `gold_tex/gold_half/gold_amt`, `pool_off` (v6.14 `gold_tile` removed).
- capture.gd `_setup_ground`: pool defaults changed + `pool_off`. No new passes; +4 draws (tufts).
