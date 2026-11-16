# Credits — godot_hd2d test

微光小圃 art (cottage, garden, 團絨) remains our own. We did not copy Square Enix / Octopath Traveler assets.

Techniques learned from open sources (method only; no code pasted from them):

- t3ssel8r — texel-snapped lighting / pixel 3D presentation
- David Holland, Jettelly, tentabrobpy — Godot texel-space lighting write-ups
- CBerry22/3d-Pixel-Art-In-Godot-4 (MIT) — post-process pixelation (different from our high-res 3D + pixel textures approach)
- KavyaJP/Godot-Hybrid2D3D-Renderer-GDExtension (MIT) — Hybrid2D3DSprite, nearest, Y-billboard, alpha scissor
- leopeltola/Godot-3d-pixelart-demo (MIT)
- Robert-K/godot-3d-pixel-art (MIT, t3ssel8r-inspired)
- astrellon/godot-3d-pixel-art (MIT)
- voithos/godot-smooth-pixel-camera-demo (MIT)
- kanaworksai-hue/tobidasu (MIT, Godot 4.7+)

`shaders/texel_lit.gdshader` is original text written for this test. Godot Engine is MIT.

## v3 AI target reference (2026-11-12)

- `TARGET_concept.jpg` was made with the Grok Bot GenerateImage tool, starting from our own v2 Godot render.
- It is a **concept / look-dev reference only**. It is **not shipped** and not used as an in-game asset. Everything in the game is the real Godot scene, built from our own hand-authored pixel textures and H1 meshes.
- Terms: xAI / SpaceXSI Consumer Terms of Service — https://x.ai/legal/terms-of-service (loaded and checked 2026-11-12, "Last Updated: October 27, 2026"). §4 says the user keeps ownership of Output, and Output must be attributed to the Service per the Brand Guidelines. Enterprise terms cover API use: https://x.ai/legal
- v3 shaders written for this test: `shaders/glow_add.gdshader` (dust and light-shaft cards), `shaders/grade.gdshader` (warm vignette and leak). Hand-authored glyph tiles: `textures/tiles/leaf_a|b.png` (organic bushes) and the softened `dirt_*` / `grass_*` tiles.

## v4 (2026-11-12)
- Starting numbers taken from GSansigolo/SimpleHD2D (no license, numbers only, no code or assets), the Acquire UE4 Fest 2018 slides, and Digital Foundry (see PRESET/HD2D_RECIPE.md).
- Octopath screenshots from Kurt: used only to read colour and value histograms. No assets copied, nothing decompiled.
- New original work: `shaders/tuft.gdshader`, `tools/author_v4_sprites.py` (tufts, flower clusters, dapple cookie), far forest, canopies.

## v5 (2026-11-12)
- New textures for brick, cobble, wood, timber, grass and leaf (`tools/author_v5_textures.py`). Made by a hand-written per-pixel script: designed height fields, a modelled top-left key light plus cavity AO, snapped to hand-picked hue-shifted ramps, and normal maps from the same height. No AI images, no photos, no noise textures, nothing copied from any game.
- `TEXTURE_SHEET_v5.png` shows each tile at 1×, 8× albedo and 8× normal.
- The 11 Octopath screenshots from Kurt (`../octopath_ref`) were only looked at as a style reference for shading and contrast. No pixels copied, nothing decompiled.
- New shader: `shaders/rim_overlay.gdshader` (original).


## v6 (2026-11-12)
- Same hand-authored per-pixel texture method as v5. Grass and wood tweaked (smoother golden lawn, softer knots). No AI textures used; optional request in AI_TEXTURE_REQUEST.md.

## v6.1 (2026-11-12): AI-assisted textures
- Tool: Grok Bot GenerateImage (three 1024×1024 JPG bases in `ai_src/`: `ai_lawn_base.jpg`, `ai_clapboard_wood.jpg`, `ai_leaf_clump.jpg`). Terms: https://x.ai/legal/terms-of-service
- Method: AI-assisted, then palette-snapped and hand-cleaned with `tools/ai_integrate_v6.py`. Steps: made seamless (half offset plus blended seams), box-downsampled to our texel density, nearest filtering, snapped by luminance to the hand-picked V3-A ramps (5–6 tones, golden highlights kept), normal maps from the luminance height. For the clapboard, each board was cut at its gap row and restacked so the pitch is exactly 8 px.
- What it made:
  - `textures/grass_macro_128.png`, `grass_outer_128.png` (+`_n`) — lawn and outer field. 5×5 median filter and only 4 tones, to keep it smooth.
  - `textures/tiles/wood_a|b|c.png` (+`_n`, 64×64; b and c are phase-shifted copies of a) → rebaked into `textures/cottage_rebaked_3x.png` (+`_n`).
  - `textures/tiles/leaf_a|b.png` (+`_n`, 128×128; b is a rolled copy of a) — bush and tree crowns, at 1 px/wu.
- Everything else stays hand-authored as in v5/v6. Nothing copied from any game, nothing decompiled.

## v6.3 (2026-11-12): the remaining AI-assisted textures and lawn B
- Tool: Grok Bot GenerateImage. Terms: https://x.ai/legal/terms-of-service
- New bases in `ai_src/` (1024×1024 JPG): `ai_brick_running.jpg`, `ai_cobble_path.jpg`, `ai_bark.jpg`, `ai_roof_tile.jpg`, `ai_lawn_base_b.jpg`. Prompts follow AI_TEXTURE_REQUEST.md.
- Method (`tools/ai_integrate_v6_3.py`): AI-assisted, then palette-snapped and hand-cleaned.
  - Brick and roof are re-laid on an exact grid, so they tile perfectly. Bricks and shingle rows are cut from the AI image and placed cell by cell.
  - Cobble and bark use variance-preserving offset+blend seams. For bark, the image is cut between the two best-matching rows so the vertical repeat is invisible.
  - Everything is box-downsampled to 1 texel = 1 wu (lawn: 2 px/wu on the garden ground), then snapped to muted, hand-picked V3-A ramps so it does not go yellow.
  - Hand clean-up rules: single-pixel speckle removed; lit top and shadowed bottom rows on bricks and shingles; chipped brick corners; moss on the lowest courses of brick_c; a 1 px shaded lower rim on cobbles.
  - Normal maps come from a designed height (material class + luminance).
- Outputs:
  - `textures/tiles/brick_a|b|c` (32×32, +`_n`): chimney (rebake), brick wall props, planter.
  - `textures/tiles/cobble_a|b|c` (64×64, +`_n`): cottage foundation (rebake) and the garden path/courtyard, filled in world space on the old stamp footprint (`tools/compose_ground_v2.py`).
  - `textures/tiles/roof_a|b|c` (32×32, +`_n`): cottage roof (rebake).
  - `textures/tiles/bark_a|b` (32×64, +`_n`): far-forest trunks.
  - `textures/tree_bark_atlas.png`: a copy of the tree mesh atlas with only the trunk strip repainted from bark_a (same UVs and silhouette).
  - `textures/grass_macro_b_128.png` and `textures/grass_outer_256.png` (+`_n`): lawn A and lawn B mixed with a tileable low-frequency mask and an ordered-dither border. This breaks the 64 wu repeat in Low mode. The lawn ramp is a little greener than v6.1.
- Octopath screenshots were used only as a learning reference for texture quality. Nothing copied, nothing decompiled. Our own building design, layout and 團絨 are unchanged.

## v6.4 (0.6.4-pilot) — concept-match depth pass
- **No new AI images.** All new sprites are procedural and original:
  - leaf clumps, ivy, hanging strands, tufts (`tools/silhouette_tex_v6_4.py`), derived in palette from the v6.1 AI leaf tile;
  - halo, mote, ray strip, treeline bands, soft foreground bush (`tools/scene_dress_v6_4.py`).
- Cottage depth: geometry relief and the atlas AO/variation/damage/red-brick bake (`tools/cottage_depth_bake_v6_4.py`, `scenes/art_depth.gd`).
- Ground:
  - 4-source lawn, overlays and decals (`tools/ground_overlays_v6_4.py`);
  - grade and specks (`tools/grade_v6_4.py`);
  - Low shadow bake from the game's own High render (`tools/bake_low_ground_v6_4.py`).
- Method write-up: `PRESET/METHOD_concept_match.md`. Octopath screenshots were a learning reference only: nothing copied, nothing decompiled.

## v6.5 (0.6.5-pilot)
- **New AI bases** (GenerateImage, original prompts, 1024 px), kept in `ai_src/`:
  - `ai_canopy_clumps.jpg`: 2×2 leaf clumps on magenta;
  - `ai_hedge.jpg`: boxy-round hedge on magenta;
  - `ai_bark_grooved.jpg`: deep vertical bark grooves.
- **Integration** (`tools/ai_integrate_v6_5.py`): AI-assisted, then palette-snapped and hand-cleaned:
  - magenta key, box-downsample (clumps 48 px per cell, hedge 64×44, bark 64 px tile);
  - rank-snap onto ramps sampled from TARGET_concept quantiles;
  - despeckle, edge fuzz knock-out and leaf tips (hedge);
  - variance-preserving seamless blend plus a moss keep (bark);
  - normal map from luminance.
- **Outputs**: `textures/tiles/canopy_clump_atlas.png`, `fg_clump_soft.png`, `hedge_a.png`, `bark_groove.png` (+`_n`).
- **Procedural (original)**: `haze_band.png`, `glow_soft.png`, the lower-contrast treeline bands, the fluted trunk mesh, lawn pits, stronger nail and damage bake.
- Octopath screenshots: learning reference only. Nothing copied, nothing decompiled.

## v6.6 (0.6.6-pilot)
- **New AI bases** (GenerateImage, original prompts), kept in `ai_src/`:
  - `ai_canopy_big.jpg`: 2×2 big lit-top canopy clusters on magenta;
  - `ai_forest_backdrop.jpg`: soft out-of-focus forest with golden light;
  - `ai_fg_flower_bush.jpg`: flower bush on blue (used in r1 only, superseded);
  - `ai_fg_corner.jpg`: leafy fern and leaf corner spray on blue.
- **Integration** (`tools/ai_integrate_v6_6.py`): AI-assisted, then palette-snapped and hand-cleaned:
  - `canopy_big_atlas.png` (2×2 × 64 px, rank-snapped to a lit concept ramp);
  - `forest_backdrop.png` (512×200, warm tint, vertical deep-green ramp, crown contrast);
  - `fg_corner_leafy.png` (blue key, de-saturated and warm, light premultiplied blur);
  - `fg_bush_blur.png` (r1 only, no longer referenced).
- **Procedural (original)**:
  - `hedge_fuzz.png` (leafy alpha edge on hedge_a);
  - `ray_warm.png`, `lawn_detail.png`;
  - softer brown lawn pits and pebbles (`tools/grade_v6_4.py`);
  - soft, dappled shadow bake (`tools/bake_low_ground_v6_4.py`).
- Octopath screenshots: learning reference only. Nothing copied, nothing decompiled.

## v6.7 (0.6.7-pilot)
- **No new AI images.** Derived assets:
  - `fg_corner_soft_L/R.png`: from `ai_src/ai_fg_corner.jpg`, colour-transferred to the concept's corner statistics and pre-blurred (`tools/ai_integrate_v6_6.py`);
  - `lawn_fine_detail.png`: from `ai_src/ai_lawn_base_b.jpg`, made seamless and kept as luminance detail only;
  - `near_macro.png`: from our own ground textures (`tools/near_lawn_v6_7.py`).
- **New original shader:** `shaders/near_lawn.gdshader`.
- Octopath screenshots: learning reference only. Nothing copied, nothing decompiled.

## v6.7 (0.6.7-pilot), concept-match pass on 遊程 0.6.6
- **New AI image:**
  - `ai_src/ai_fg_plant.jpg`, made with GenerateImage (original prompt, no reference to any game asset).
  - It is processed into `textures/tiles/fg_plant_a.png` by `tools/world_v6_7.py`: blue key removed, palette-snapped to olive, muted pink.
- **Procedural (original, `tools/world_v6_7.py`):**
  - `canopy_leafy_atlas.png`, `bush_leafy_atlas.png`;
  - `backdrop_ring.png`, `contact_ao.png`, `dapple_leaf.png`, `leaf_shade_tile.png`.
- **From our own scene:**
  - `near_macro.png` (`tools/near_lawn_v6_7.py`);
  - `ground_composed_low.png`, `sun_shadow_mask`, `shadow_wide_mask.png` (`tools/bake_low_ground_v6_4.py`, from our own top-down shadow captures).
- **New original shaders:** `core_leafy`, `ground_dapple`, `backdrop_ring`, `fg_plant`, `near_lawn` (region update). `clump_card` and `tuft` gained sway.
- Octopath screenshots: learning reference only. Nothing copied, nothing decompiled.

## v6.8 (0.6.8-pilot), on 遊程 0.6.7
- **New AI image:**
  - `ai_src/ai_sky_v68.jpg`, made with GenerateImage (original prompt: painted evening sky, white cumulus, warm glow; no references).
  - Hand clean-up in `tools/foliage_v6_8.py` → `textures/tiles/sky_v68.png`: tone transfer to the concept's green-gold, peach → warm gold, 48-tone palette, no JPEG noise.
- **Procedural (original, `tools/foliage_v6_8.py`):**
  - `canopy_spray_atlas.png` (leaf sprays);
  - `bush_serrated_atlas.png` (serrated-leaf mounds + florets);
  - `lawn_blades_v68.png` (blades, tufts, clover, patches);
  - `backdrop_ring_v68.png` (v6.7 forest ring with a procedural ragged treeline alpha).
- **New original shader:** `shaders/sky_dome.gdshader`.
- **Changed shaders:** `near_lawn` (colour blade mode, shade floor), `backdrop_ring` (treeline cut), `core_leafy` (leaf contrast), `ground_dapple` (fleck/shade amounts).
- Octopath screenshots: learning reference only. Nothing copied, nothing decompiled.

## v6.9 (0.6.9-pilot), on 遊程 0.6.8
- **No new AI image.** `sky_v69.png` is a re-grade of our own `ai_src/ai_sky_v68.jpg` (already credited and cleaned in v6.8) toward the concept's golden haze (`tools/dynamics_v6_9.py`).
- **Procedural (original, `tools/dynamics_v6_9.py`):** `cloud_shadow.png` (tileable fBm cloud-shadow field shared by ground, bushes, grass, shafts and sky).
- **From our own scene (`tools/bake_ground_v6_9.py`):** `ground_composed_low(_hard).png`, `shadow_wide_mask(_hard).png`, `near_macro(_hard).png`, `art/ground/sun_shadow_mask_v6_9.png`. Built from top-down captures of our own geometry (shadow, height and footprint passes), with height-proportional feathering, footprint AO and blue-violet fill.
- **New original shader:** `shaders/bake_height.gdshader` (bake-only height pass).
- **Changed shaders:** `tuft`, `fg_plant`, `clump_card` (pet bend via `pet_pos_ws` / `pet_lag_ws`, cloud shade); `ground_dapple` (cloud field).
- 遊程's `scenes/prop_bump.gd` + `data/prop_bump.json` are included unchanged.
- Octopath screenshots: learning reference only. Nothing copied, nothing decompiled.
## v6.10 (0.6.10-pilot), on 遊程 0.6.9-merged
- **No new AI image** (no GenerateImage use in this version).
- **Procedural (original):** `textures/tiles/ring_height_v610.png` (treeline height profile of our own backdrop ring), `pool_soft_v610.png` (night light-pool falloff), `glow_soft_v610.png` (warm dithered haze glow).
- **From our own scene (`tools/bake_ground_v6_10.py`):** `ground_composed_low(_props).png`, `shadow_wide_mask(_props).png`, `art/ground/sun_shadow_mask_v6_10.png` — per-class layered shadow bake from top-down shadow / height / footprint / class-ID captures of our own geometry.
- **New original shaders:** `light_shaft.gdshader`, `pet_shadow.gdshader`. Changed: `sky_dome`, `ground_dapple`, `near_lawn`.
- 遊程's `capture.gd` (version line only), `prop_bump.*`, `bed_flower.gdshader` included unchanged.
- Octopath screenshots: learning reference only. Nothing copied, nothing decompiled.


## v6.11 (0.6.11-pilot)
- **No new AI image** (no GenerateImage use in this version).
- **Derived from our own textures / scene (procedural, original tools):** `textures/tiles/lawn_blades_v611.png`, `textures/grass_outer_v611.png` (`tools/lawn_grade_v6_11.py`); `textures/tiles/canopy_spray_atlas_v611.png` (`tools/canopy_calm_v6_11.py`); `art/ground/ground_composed_clean_v611.png` + `textures/ground_composed_hi_v611.png` (`tools/ground_deblob_v6_11.py`); `textures/tiles/sky_cloud_v611.png` (`tools/sky_cloudmask_v6_11.py`, from our sky_v69); `ground_composed_low(_props).png`, `shadow_wide_mask(_props).png`, `art/ground/sun_shadow_mask_v6_11.png` (`tools/bake_ground_v6_11.py`, captures of our own geometry in `art/ground/bake_v6_11`); `near_macro.png` (`tools/near_lawn_v6_11.py`), `near_mover_shade.png` (`tools/near_mover_shade_v6_11.py`).
- **Changed original shaders:** `light_shaft`, `sky_dome`, `near_lawn` (custom light()), `clump_card`, `backdrop_ring`, `bed_flower` (idle sway added to 遊程's shader; pet bend unchanged).
- 遊程's `capture.gd` (version line only), `prop_bump.*` included unchanged.
- Octopath screenshots: learning reference only. Nothing copied, nothing decompiled.

## v6.12 (0.6.12-pilot)
- **No new AI image** (no GenerateImage use in this version).
- **Derived from our own textures / scene (procedural, original tools):** `textures/grass_outer_v612.png` (grass_outer_v611 ×0.84); re-baked `ground_composed_low(_props).png`, `shadow_wide_mask(_props).png`, `art/ground/sun_shadow_mask_v6_11.png` (`tools/bake_ground_v6_11.py`, v6.12 class values, same captures of our own geometry); `near_macro.png` (`tools/near_lawn_v6_12.py`), `near_mover_shade.png` (`tools/near_mover_shade_v6_12.py`).
- **Changed original shaders:** `near_lawn` (shade floor, mover decode), `light_shaft` (break boost), `clump_card` (aerial amount).
- 遊程's `capture.gd`: version line + ground lawn_center / lawn_radius / lawn_gain default (art-side values, see GAPS_v6_12 §5 step 10); `prop_bump.*`, `bed_flower.gdshader` unchanged from 0.6.11.
- Octopath screenshots: learning reference only. Nothing copied, nothing decompiled.

## v6.13 (0.6.13-pilot)
- **No new AI image** (no GenerateImage use in this version).
- **Procedural / derived (original tools):**
  - `textures/tiles/lawn_blades_v613.png` (fully procedural blades, clover, tiny flowers), `textures/grass_outer_v613.png`, `textures/ground_composed_hi_v613.png` (`tools/lawn_lush_v6_13.py`, from our own grass_outer_512 / ground_composed_clean_v611);
  - `textures/bedtop_shade_v613.png` (`tools/bedtop_shade_v6_13.py`, from a capture of our own geometry `art/ground/bake_v6_11/inner_sh_bedtop.png`);
  - re-baked `ground_composed_low(_props).png`, `near_macro.png`, `near_mover_shade.png` (`tools/near_mover_shade_v6_13.py`).
- **Changed original shaders:** `near_lawn`, `clump_card`, `leaf_card`. 遊程's `bed_flower.gdshader`: bed-top shade uniforms added (default off).
- 遊程's `capture.gd`: version line only this round.
- Octopath screenshots: learning reference only. Nothing copied, nothing decompiled.
