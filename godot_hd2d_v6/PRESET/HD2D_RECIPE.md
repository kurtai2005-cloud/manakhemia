# 微光小圃 HD-2D recipe (v4, Godot 4.7.2, Forward+ / Mobile)

Use this for new scenes. Drop `hd2d_env_high.tres` into a WorldEnvironment and `hd2d_camera_attrs_high.tres` into a Camera3D.
On Low, turn off glow, fog, SSAO, volumetric fog and DOF (see `hd2d_env_low.tres`). Night is `hd2d_env_night.tres` plus the night light values below.
World scale: **1 wu = 1 game pixel** (pet ≈ 54 wu ≈ 0.8 m, so 1 m ≈ 67 wu). Values copied from metre-scale projects have to be converted (×67 for distances, ÷67 for densities).

## Borrowed starting numbers (sources)
| Value | Source | Raw | What we used |
|---|---|---|---|
| Tonemap | SimpleHD2D `levels/castle_level.tscn` | `tonemap_mode = 2` (Filmic) | Filmic, exposure 1.1, white 6 (picked from 0.95 / 1.15 / 1.45 tests on the PC) |
| Glow | SimpleHD2D same file | `glow_bloom = 0.05`, `glow_blend_mode = 0` (additive) | bloom 0.05, additive, intensity 0.5, HDR threshold 1.0 |
| DOF | SimpleHD2D `assets/camera_attributes/new_camera_attributes_practical.tres` | far only, `dof_blur_far_distance = 28.43` m with a 6 m spring arm, `dof_blur_amount = 0.09` | near and far (tilt-shift band): near 240 / 60, far 400 / 140, amount 0.22. Theirs is a gentle start; Octopath and our target need a stronger band |
| Sun shadow | SimpleHD2D DirectionalLight3D | `shadow_opacity = 0.72` | 0.80 (deeper Octopath-style shadows) |
| Volumetric fog | SimpleHD2D has none. Godot docs: keep global density low and use FogVolumes locally | — | 0.0001 per wu (≈0.007 per m), anisotropy 0.75, albedo (1, .93, .80), ambient/GI inject 0. v3 used 0.00045 and washed orange |
| Post stack | Acquire/Square Enix UE4 Fest 2018 talk 「OCTOPATH TRAVELERはこうして作られた」 (slides) | Only PostProcessVolume features: ColorGrading, Bloom, Bokeh DOF, Lens flare, Ambient Cubemap, vignette. DOF changes with the camera. Narrow FOV. Light that still shows the texture in dark areas. | glow + DOF + warm grade/vignette + cool ambient colour (stands in for the ambient cubemap). FOV 40 |
| Look | Digital Foundry, "Octopath Traveler: a 90s-style JRPG…" (2018) | Strong bokeh DOF, sharp centre, blurred foreground and background, tilt-shift miniature look | sharp middle band, near and far blur |

Sources:
- SimpleHD2D (Godot 4.1), GSansigolo: https://github.com/GSansigolo/SimpleHD2D. The repo has **no license file**, so we took **numbers only**: no code or assets were copied. Read 2026-11-12.
- Acquire UE4 Fest slides: https://www.slideshare.net/slideshow/nintendo-switchoctopath-traveler/119821741
- Digital Foundry: https://www.digitalfoundry.net/articles/digitalfoundry-2018-octopath-traveler-a-hybrid-game-for-a-hybrid-console
- Godot docs, volumetric fog: https://docs.godotengine.org/en/stable/tutorials/3d/volumetric_fog.html
- The 11 Octopath screenshots Kurt sent (`../octopath_ref/`) were used to **read colour and value only** (histograms). No assets were copied and nothing was decompiled.
  Day refs: mean RGB ≈ (73–80, 57–79, 42–63), luma p5 2–17, p50 45–70, p95 155–197. Shadows are crushed, highlights are local pools, greens are olive.

## Final High values (v4, PC round 3 = shipped GODOT_HIGH)
- Sun: dir (0.74, -0.42, 0.52) (low, from back-left), colour (1.0, 0.84, 0.68), energy 2.2, vol-fog energy 6, PSSM 4 splits, max distance 700, bias 0.4 / normal bias 1.0, blur 0.4, opacity 0.80
- Fill: colour (1.0, 0.86, 0.68), energy 0.22
- Ambient: colour (0.52, 0.58, 0.68) (cool, so shadows get some blue), energy 0.45
- Adjust: contrast 1.18, saturation 0.86
- Depth fog: light (0.95, 0.82, 0.62), energy 0.55, sun scatter 0.6, sky affect 0.35, begin 420, end 900, curve 1.6
- SSAO radius 0.9, intensity 0.7 (Forward+ only)
- Grade overlay (`shaders/grade.gdshader`): vignette (0.08, 0.07, 0.05) at 0.65, leak (1, .86, .62) at 0.14
- Lantern strings: emission ×3.2 by day, omni 0.35. Lamp: emission ×0.35, omni 0 by day (lamp omni 0.6 burned out the crate in r4)
- Dust: 170 CPUParticles3D billboards, `glow_add` additive, tint (1, .84, .52), energy 2.4
- Light-shaft cards (`glow_add`, mask 1): tint (1, .92, .72), alpha 0.18–0.26, 420 wu long, aligned to the sun

## Material and foliage recipe
- Pixel tiles: hand-authored 16×16 glyph maps (`tools/author_*.py`), nearest filter, no mipmaps, `texel_lit.gdshader` (texel-centre lighting). Optional `haze` / `haze_amt` gives far layers their haze. `rim_amt` defaults to 0; 0.3 turned the bushes lime.
- Bushes and canopies: clusters of 6–8 SphereMesh lobes (12×6 segments) using leaf_a/leaf_b, UV = circumference/9 so leaves stay about 9 wu each. Canopy at the tree's local (18, 178)·scale, r = 50·scale.
- Far forest: 4 rows at z = -300 / -390 / -490 / -600, spacing 62–96, trunk 55·scale, canopy r 54·scale, haze 0.15 + 0.12·row, no shadows.
- Ground clutter: R2 low-discrepancy points (not noise), with masks for path, house, fence, beds, props and pet. Tufts are 7 wu cross-cards, flowers are 9 wu, `tuft.gdshader` shade 0.72 with the normal pointing up. About 400 tufts and 48 flower clusters.
- Dapples: a shadows-only plane 230 wu up along the sun ray, with a 256 px alpha-scissor blob cookie (~57% cover). The garden centre is cleared so the pet and house stay lit.

## Lessons (v4)
- Exposure is the biggest lever. Filmic 1.45 was 1.5× too bright; at 1.1 the mean colour matched the target (79,67,32 vs 80,68,31).
- More sun plus rim (r4) gave lime bushes and a burned-out crate, and the error went up (MAE 35 vs 23.5). Keep it moody.
- Wide volumetric fog washes out the scene. Keep it thin and put the god-rays in cards.

---
# v5 update (2026-11-12): depth, contrast, textures with normal maps
These values come from the shipped v5 HIGH (PC round 3, variant exposure 1.35 / pool 1.8). The `.tres` files in this folder were saved by that run.

## Light and depth
- **Sun:** dir (0.74, -0.30, 0.52), about 17° up, so tree and house shadows run long. Colour (1.0, 0.84, 0.68), energy 2.2, shadow opacity 0.80.
- **Ambient:** (0.52, 0.58, 0.68) at **0.30**, so shadows stay deep.
- **"SunPool" SpotLight3D:** the bright centre lawn. Placed above the lawn at (-0.40, 0.85, -0.34)·600 from (20, 0, -20), angle 14°, angle attenuation 2.2, distance attenuation 0, colour (1.0, 0.80, 0.52), energy 1.8, specular 0, **no shadow**.
  - Round 1 put it along the sun ray with a shadow. The canopies blocked it, so it did nothing.
  - Off at night. On Low, but without shadow.
- **SSAO at pixel scale** (1 wu = 1 px): radius 22, intensity 2.4, power 1.6, detail 0.6, horizon 0.06, sharpness 0.98, light affect 0.15. The old radius 0.9 did nothing at this scale.
- **Tilt-shift:** near 272 / 64, far 392 / 110, amount 0.34. The pet sits about 290 wu from the camera, the cottage 340–380.
- **Fog:**
  - Depth fog: light (0.95, 0.82, 0.62), energy 0.40, begin 520, end 900, sky affect 0.2.
  - Volumetric fog: 0.00006.
  - Sky card: (0.72, 0.64, 0.46).
  - Far-forest haze: 0.10 + 0.10·row. This cut the milky top band.
- **Tonemap:** Filmic, exposure 1.35, white 6. Contrast 1.18, saturation 0.86.

## Edges and lamp
- **Golden rim** (`shaders/rim_overlay.gdshader`): an additive `material_overlay` on every 3D prop mesh (bushes, canopies, trees, pots, crates, cottage).
  - Formula: fresnel^2.5 × (facing the sun)². Colour (1, .76, .40), amount 0.45, or 0.2 on the cottage (eaves and edges).
  - Only on High day; Low and Night have it off.
- **Grass tufts:** golden tips via `tuft.gdshader` `rim_top` 0.35 on the top half of each card.
- **Amber lamp head:** lamp emissive uses `EMISSION_OP_MULTIPLY` × (1.0, 0.56, 0.18). Day emission ×1.4, night ×4.

## Materials (v5 textures)
- Generator: `tools/author_v5_textures.py`. Each tile starts from a designed **height field**:
  - **brick:** running bond 8×4 with bevelled edges; crack, chip and moss at fixed coordinates
  - **cobble:** hand-placed seed points, domed stones with gaps
  - **wood:** clapboards with a lip, sine grain, fixed knots, one butt joint
  - **timber:** grain columns with checks
  - **grass:** 34 designed blades, dark base and lit tip
  - **leaf:** 7 pointed leaves with a midrib
- Albedo = baked top-left key light (Lambert on the height normal) − cavity AO, snapped to a 5–6 tone hue-shifted ramp. Normal map = the same height (Sobel, Godot/OpenGL Y+).
- 3 variants each (a, b, c), plus `*_n.png`. Imported with `compress/normal_map=1` and lossless.
- Where the normals are used:
  - `texel_lit.gdshader` gains `normal_tex`, `use_normal`, `normal_depth`. `_tiling_mat` finds `<tile>_n.png` on its own.
  - Cottage: `cottage_rebaked_3x_n.png`, baked by the same rebake pass, only on replaced field pixels (official details stay flat).
  - Ground: `ground_composed_n.png` and `grass_outer_128_n.png`, made by running the ground composer on luminance-height tiles.
- Roof normals are derived from the existing roof tiles' luminance. Roof wasn't rebuilt this time.
- The fence keeps its official alpha-cut picket atlas. A triplanar plank test turned it into a solid wall, so I reverted it.

## v5 scores (96×54 MAE vs TARGET_concept, lower is better; centre/surround luma, target 1.19)
| Run | MAE | centre/surround |
|---|---|---|
| v4 shipped | 23.5 | 1.02 |
| v5 r1 (shadowed grazing pool) | 26.0 | 0.96 |
| v5 r2 | 24.5 | 1.03 |
| **v5 r3 (shipped)** | **24.4** | **1.08** |


---
# v6 (2026-11-12, box only — phone APK test): portrait + phone budget
v6 was tuned on the box (llvmpipe), so the PRESET .tres files are still the v5 PC values. The v6 numbers below are what the code now uses. Re-save the presets after a real-GPU run.

## Portrait framing
- Viewport 1080×1920, `window/handheld/orientation=1`.
- Camera `KEEP_WIDTH`, horizontal FOV 50, target (12, 38, -26), distance 250, pitch 30.
- The same layout as v5 fits across the width: lamp, bed, pet, cottage, lantern string and both framing trees. The extra height shows lawn below and tree crowns against golden sky above.
- Pet is about 11.5% of screen height. Fitting lamp → cottage across the width caps it there. 21% would need cropping the lamp or the cottage.

## Fixes
- **Top haze:**
  - Depth fog begins 700 / ends 1400, sky affect 0.
  - Volumetric fog 0.00003, sky affect 0.
  - Far DOF from 470 with transition 220, amount 0.28.
  - Sky card gold (1.0, 0.84, 0.54). Far forest is 3 sparser rows with smaller crowns and haze 0.05 + 0.06·row, so tree shapes read against the gold.
  - Leak 0.08.
- **Golden lawn:**
  - `texel_lit.gdshader` gets a `lawn_gain` albedo lift: centre (10, 0, 30), radius (170, 120), tint (1, .86, .52), gain 0.85. Lifting albedo keeps shadows dark, which a fill light didn't.
  - Pool light cut to 0.5 because it was filling the long shadows.
  - Tufts: 340 samples, only 1 in 4 kept inside the lawn ellipse, shade 0.9, golden tips 0.25.
  - Grass tile: 16 blades, softer light and AO, golden-olive ramp.
- **Long shadows:** sun 2.6, shadow opacity 0.92, blur 0.2, max distance 560, ambient 0.26.
- **Rim:** 0.35.
- **Phone** (`OS.has_feature("mobile")`, Forward+ via `--rendering-method forward_plus`, Note10+):
  - 3D scale 0.72 on High, 0.60 on Low (bilinear).
  - SSAO quality low, half size.
  - DOF blur quality low, hexagon bokeh.
  - Directional shadow 2048 with 2 splits, soft shadow filter low.
  - Volumetric fog volume 64×48, dust 110, 60 fps cap.
  - Low = same scene with shadows, glow, fog, DOF and rim off.
