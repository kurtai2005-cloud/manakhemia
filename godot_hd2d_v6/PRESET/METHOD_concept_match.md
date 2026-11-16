# METHOD — building a Godot HD-2D scene from a concept image (generic, reusable)

Distilled from the 微光小圃 v6.x pilot. It is not tied to that scene. Units: 1 world unit (wu) ≈ 1 screen px at the hero distance. Nearest filtering everywhere.

## 0. Rules
1. **The concept image is the MINIMUM baseline.** Every item must match or exceed it, and nothing may be worse. In the comparison, mark each item **MATCHED**, **EXCEEDS** or **BELOW**. An item that is BELOW is never "done".
2. **Ground truth = real-device / real-GPU renders with the shipping renderer** (Mobile for phones), not software previews. A phone capture beats a PC render, and a PC render beats llvmpipe.
3. **Low must carry the look on its own:**
   - no SSAO, shadows, glow, DOF or fog;
   - everything that defines form (AO, shade side, contact and cast shadows, glow halos) is baked into albedo or vertex colour, or drawn with unshaded sprites.
4. **Art changes never touch** renderer, perf, input or DOF code owned by someone else. Write a note with proposed values instead.
5. Reference screenshots of commercial games are for learning only. Never copy assets or decompile.
6. **Fix once, at the highest quality**: write the gaps file first, then edit.

## 1. Side-by-side gap checklist (fill this in per object before editing)
Put the concept and the current render side by side at the same crop and scale (phone view distance). For each category, write what is below the concept, why, and the fix.

| Category | What to look for |
|---|---|
| Silhouette | Smooth spheres or boxes, straight roof and wall lines, even fence tops, objects with no grass at their base |
| 3D relief | Frames, sills, recesses, posts, beams, slab thickness, overhangs, caps and plinths protruding 1–3 wu |
| Shadows & light direction | Shade side of every object; eave and contact shadows; long cast shadows matching the sun azimuth and elevation; god rays and motes |
| Pattern variation | Visible repeat at phone distance; same board, stone or shingle twice; no macro overlays or decals |
| Texture quality | Texel density, noise frequency (no high-frequency fizz), palette snap, element shapes |
| Colour grade | Per-region mean RGB and the B/G and R/G ratios vs the concept; p5 and p95 luma; how deep the darks go; warmth of the highlights |
| Background layers | Number of depth layers, haze ramp with distance, gaps in the sky |
| Foreground framing | Near-corner masses (bushes, pots), darker vignette value, soft edges |
| Emissives | Glow plus halo readable in Low; core colour vs halo colour; night boost |

Measure the colour, don't eyeball it: crop the same region in both images and compare the means and ratios (see `grade_v6_4.py` header).

## 2. Per-object recipes (technique · parameters · texel size)

| Object | Recipe |
|---|---|
| **Tree trunk** | CylinderMesh, 10 radial segments, r_top ≈ 0.72 × r_base, plus a root-flare cylinder (r ×1.6, h ≈ 0.11 × trunk). Bark tile 32×64 px, world triplanar, tile 24 wu, tint toward red-brown (0.92, 0.64, 0.52). Vertical grooves come from the bark texture (raise its contrast if they don't read). Ivy: 9 alpha-scissor clump cards (24 px sprite, 7–11 wu) spiralling up the camera side. Decor (birdhouse, lantern) as tiny primitives; lanterns get a halo. |
| **Canopy** | Clustered low-poly spheres (12×6) carry the mass. Silhouette: camera-facing alpha-scissor leaf-clump cards (3 variants, 32 px, 60–70 leaves each, isolated specks removed): `clamp(r/3.2, 5, 14)` on the screen-space rim at 0.98–1.10 r, sized 0.55–0.9 r; 5 more on the visible face; 3 hanging strands (12×32 px) under big crowns. Value lift toward the sun on screen (+0.30); `BACKLIGHT` (0.55, 0.62, 0.16) for translucent edges. Far rows: half the cards plus the row's haze. Orient cards on the CPU; MODELVIEW billboards break MultiMesh on Compatibility. |
| **Bush / hedge** | Same as canopy, plus 2 crown "sun-caught" cards (value 1.35). For boxy hedges use a squashed rounded box (scale y 0.7) under the cards. Base tuft ring. |
| **Lawn** | Inner ground: one unique 512 px texture at 2 px/wu. Outer field: 512 px, built from 4 sources (A at half macro size, B, and both turned 180°) with an irregular Bayer-dithered mask, so it repeats only every 512 wu. Overlays, each quantized: large value gradient (lit clearing, darker edges), contact AO around every prop (k 0.34–0.45), worn soil, decals (leaves, pebbles, clover, tiny flowers), 1–2 px holes, dirt specks and sun-caught blade tips (~5 000 per 512²). Grade toward the concept's measured R/G and B/G with a green-black toe. Edge tufts are MultiMesh cards: dark tufts along paths, walls and fences; plain and flowered foreground tufts 75/25. |
| **Path** | World-space cobble fill: label each stone (percentile-40 threshold, then open/fill), give each stone its own value, hue and moss, add cracks, put pebbles and leaves in the gaps, edge tufts, darker mortar. Tile 64 px at 1 px/wu. |
| **Cottage walls** | Bake post-pass on the rebaked atlas (world position per texel):<br>• per-face value: lit 1.10 warm / shade 0.80 cool / back 0.84 / soffit 0.58;<br>• AO under eaves, at the base and corners, around frames, under boxes and inside recesses, quantized 1/20;<br>• per board: value 0.90–1.10, hue ±, butt joints at 24–46 wu, 1–2 nails, knots, cracks (~14 %), chipped edges (~10 %), rot near the ground;<br>• macro overlays: weathering noise, dirt splash below 14 wu, base moss, sun-fade.<br>Geometry relief: ~30 boxes with vertex AO for frames, sills, mullions, door posts, step, corner posts, beams, plinth, bargeboards, fascia, ridge and chimney cap. |
| **Roof** | Per shingle (4×4 wu): value 0.86–1.14, hue ±, moss below the ridge, sun-fade on the lit slope. Edge: a single merged mesh of shingle-tip tabs (2–4.2 wu long, 3–3.8 wu wide, ±7° twist) along the eaves and gables. Plus bargeboards and a fascia lip. Roof tile 32 px. |
| **Chimney** | Repaint the texels as red layered brick: 8×4 wu bricks in running bond, mortar 0.45 wu, a darker corbel band every 7 courses, per-brick hue, soot fading in near the top. Add a cap slab and a soot lip. |
| **Fence** | Keep the alpha-cut picket atlas. Add a few independent stakes (15–21 wu, ±5° tilt) so the top line is uneven. Base tufts and contact AO strip. |
| **Props** | Contact AO in the ground texture plus a tuft ring (5–9 tufts at r + 1.5–3 wu). Keep the prop's own pixel-art atlas. |
| **Lights** | Find the bulb positions from the emissive mask (sample at mesh UVs, then cluster on a 6 wu grid). Give each an unshaded additive billboard halo (32 px banded radial sprite with a 0.18 r white core): 11 wu for string bulbs, 18 wu for lamps. Alpha: 0.85 Low, 0.6 High (glow helps there), 1.0 night. |
| **Sun light (Low)** | Render a top-down orthographic shadow pass of the High scene (other geometry SHADOWS_ONLY, grey ground). Bake it as `shade 0.60 + 0.40·mask` with a cool tint into a Low-only ground texture, and swap it in at runtime only when sun shadows are off, so High never gets double shadows. Add 5 additive ray strips (16×128 px sprite, alpha 0.16) and ~60 static motes. Re-bake after moving any big object. |
| **Background** | 3D far rows (with fringe cards) plus 3 alpha-cut treeline bands (512×128 px), each paler and lower-contrast with distance. Place them just in front of the opaque sky board. |
| **Foreground frame** | Pre-softened sprites (blurred inside an alpha-scissor outline, ~35 % darker) in both near corners, placed by ray-casting the screen corners to the ground. Add one prop half-cropped by the frame. Reads as out-of-focus even without DOF. |

## 3. Mobile budgets (Note10+ class)
- **Low (target ≈ 60 fps):**
  - no real-time shadows, SSAO, glow, DOF or fog;
  - extra geometry ≤ ~1 000 triangles in merged meshes;
  - alpha-scissor cards ≤ ~4 000 instances in ≤ 10 MultiMeshes;
  - additive sprites ≤ ~100 instances (halos, motes) plus ≤ 6 large ray quads;
  - no per-frame CPU work besides the texture swap check.
- **High (35–55 fps acceptable):** Low plus sun shadows (2 splits, ≤ 450 wu), weak DOF (amount ≤ 0.06, focus on the hero), glow, fog, shafts and dust.
- If Low drops below 55 fps on the phone, cut in this order:
  1. halve the canopy face cards;
  2. halve the rim cards on far rows;
  3. drop the hanging strands;
  4. drop the ray strips.

## 4. Order of work
1. Lock the camera and composition; keep the hero objects and the pet.
2. Render the current scene on the real renderer (Mobile) and put it side by side with the concept.
3. Fill in the gap checklist (§1) per object. Write `GAPS_<ver>.md`.
4. Silhouettes and 3D relief (geometry and cards).
5. Shade side, AO and contact shadows baked (atlas and vertex colour).
6. Cast shadows: bake the shadow mask into the Low ground. Add the light FX for Low.
7. Pattern variation: per-element hashing, ≥ 3–4 variants per material, macro overlays, decals, repeat-break check.
8. Background layers, then foreground framing, then emissive halos.
9. Colour grade, measured against the concept (region means and ratios).
10. Box smoke and walk test (no script errors). Zip, then do real-GPU render round 1.
11. **Self-critique loop (mandatory before reporting):**
    - after the first real-GPU render, compare every object against the concept and write down what is below it, why, and how to fix it;
    - fix it;
    - re-render (round 2; max 2 PC rounds).
    The report lists the problems found, the fixes made and what is still below the concept. It does not ask for approval.
12. Per-object comparison sheet with a MATCHED / EXCEEDS / BELOW tag per item, honest % estimates, remaining gaps.

## 4b. Learned in v6.5
- **Foliage = cards over a dark core, not textured spheres.** Keep the sphere only as an unshaded green-black backdrop; the dark gaps come from it showing through. Put 8–44 clump cards on the camera-facing hemisphere (`clamp(r²/42, 8, 44)`; halve for hazy rows), sized 0.50–0.76 r at 0.86–1.02 r, plus `want/3` inner cards at value ≈ 0.35 for depth.
  - Bake the light per card in COLOR: `0.40 + 0.26·max(0, n.y) + 0.60·max(0, n·sun + 0.15)·(0.35 + 0.65·rim)`, then ×0.72 for undersides.
  - Use an unshaded shader with `light_mul` for night.
- Use a **2×2 atlas picked by `INSTANCE_ID`** (plus a random mirror). One MultiMesh per haze level, so a whole forest is ~5 draws.
- **Merge static backdrops**: core spheres per haze level go into one low-res mesh. Originals become `SHADOWS_ONLY`. In this scene that took Low draws from 454 to 223 (Compatibility) and to 145 on Mobile.
- **Fluted trunks**: 24 sides, alternate vertices pushed in 16–24 %, vertex colour 0.40 in the grooves vs 0.95 on the ridges, bark texel 0.75 wu. The grooves read on a phone even with no shadows.
- **AI bases**: generate on a flat magenta (#FF00FF) background, key it out, then box-downsample to the target texel size and **rank-snap** luminance percentiles onto a ramp sampled from the concept's quantiles (5/25/50/75/95 %). Add ±0.05 rank jitter to break flat bands. Despeckle (open, then drop islands < 2 %).
- **Haze is easy to overdo**: haze cards above ~0.5 alpha turn the background milky. Check the background *value* against the concept, not only its softness.
- **Draw counts**: print the `Performance` monitors (draw calls, objects, primitives) at frame 20 in every capture log and record them per version.

## 4c. Learned in v6.6
- **Check on the real phone, not only the PC.** Kurt's Note10+ captures of 0.6.5 showed problems that PC renders hid: black-square lawn pits, foreground blobs that read as "dark balls", hard live tree-shadow bands in High, and a milky Low background. Score the phone capture, then the PC render.
- **Bigger clusters mean fewer cards and a better look.** For canopies, use 64 px lit-top AI cluster cells with clamp(r²/110, 5, 20) cards per sphere at 0.8–1.1 r. Values: 0.74 + 0.42·up + rim term, max ~1.5; undersides ×0.66. Clump cards went from 5,437 to 1,210 and the front tree stopped reading as a dark noisy mass.
- **Show distance by value, not with cream haze.** Scale far rows' values by (1 − 2.4·haze) and use a green-gold haze colour (0.46, 0.48, 0.24) capped at 0.22. A cream haze above 0.3 turns pale and milky.
- **Background = one pre-blurred painted backdrop card, LINEAR filter.** This is the one sanctioned exception to nearest filtering, because it is out of focus. It replaces treeline bands and haze cards. Size it so its dark crown band fills the top of the screen, not its glow. Drop 3D far rows that sit behind it (fewer draws).
- **Rays are camera-billboarded strips that fan from one sun anchor.** A strip laid along a low sun direction ends up almost horizontal and gets hidden by the ground. Use a thick soft gaussian strip in warm amber (255, 178, 78), alpha 0.5 in Low and 0.24 in High.
- **Foreground framing: an irregular leafy spray, not round bushes.** Pin the AI corner sprite to the screen corners with `project_position` at a fixed depth and mirror it for the other side. Premultiplied blur stays at k ≤ 1.7 so leaf shapes still read. A round blurred bush always reads as a ball.
- **Lawn pits:** 2–4 × 1–3 px warm-brown cores with a soft falloff and a lit lip. Never use pure-black texels: at 1–2 px/wu they read as black squares on the phone.
- **Near-camera detail:** an alpha-blend dark-blade grain plane (1 draw, world-tiled at 4 px/wu, faded at the far edge). A `blend_mul` plane went black in High on Compatibility, so don't use it.
- **Shadow bake:** add leafy noise on the penumbra, blur 2.2, sun-flecks only inside shadow, and lighter shade (0.72 + 0.28·m). Register every tree-attached mesh (trunk, birdhouse, trunk lantern) as a tree caster, or it keeps a hard live shadow in High.
- **PC transfers:** `Expand-Archive -Force` over an existing folder did NOT replace files, so the first round-2 render ran the stale build. Extract each round into a fresh folder (`ZipFile.ExtractToDirectory`) and verify a version string before rendering.

## 4d. Learned in v6.7
- **Always unzip each PC round into a NEW, empty folder and check the version line before rendering.**
  - Use `[IO.Compression.ZipFile]::ExtractToDirectory`, and abort if the folder already exists.
  - Grep `config/version` in `project.godot` and one string that changed this round.
  - Check that the `perf vX.Y` line in the log has the right version.
  - `Expand-Archive -Force` over an old folder silently kept stale files in v6.6.
- **Score the phone's bottom third against the phone capture, not the PC frame.**
  - The PC window is clamped to 1080×1410, which hides the near field.
  - Render an extra phone-aspect frame (540×1140, 19:9) each round.
  - Phone framing (0.6.5 Note10+) is wider than the box/PC capture with the same code, so near-field fixes must cover z up to about 310.
- **Near-field ground:** never stretch a 1–2 px/wu texture across the bottom of a portrait frame. Use an overlay plane (1 draw):
  - albedo = LINEAR macro colour of the real ground (bake + outer, 2 px/wu, σ 0.8 wu) × a 4 px/wu blade-detail tile (luminance ratio to the local mean, stored ×0.5);
  - add soft pits and specks after the blur;
  - texel-snapped lighting, so High live shadows still land on it;
  - Bayer-dithered fade into the old ground (opaque pass, no blending).
- **Out-of-focus corners:**
  - Colour-transfer the sprite's foliage pixels per channel (mean/std) to the concept's own corner crops (left = deep warm shade, right = golden olive). Mute the flower pink.
  - Then apply a strong premultiplied blur (σ 6 at 256 px).
  - Crisp, saturated leaves read as "stickers", not depth of field.

## 4e. Learned in v6.7 (on 遊程's 0.6.6 base)
- **Always unzip to a fresh folder and verify the version line** (`config/version`, `version/code`, the `hd2d vX start` log) before judging a render. Old folders and caches lie.
- **Judge at the phone's aspect and scale.** Render 1080×2280 (19:9) and 0.55 scale (594×1254). PC windows clamp to 1080×1410 and hide cut canopy tops and world edges.
- **The camera moves, so dress 360°.** Any fixed-orientation card (rays, backdrop boards, sprays) turns into an edge-on band. Use axis billboards with a grazing fade, a cylinder backdrop and an outer ring of trees and bushes. Check a walk set: 4 corners + centre × 3 yaws.
- **Cover canopies on the full sphere,** not only the hero-facing side. Use dark leafy undersides and textured cores; flat cores read as discs from below or the side.
- **Plant foreground props in the world** (buried roots, contact AO, tufts at the foot, depth-written) outside the walk area, never camera-space cards. That keeps the pet visible.
- **Bake hygiene:** turn soft-sun angular and blur off for the top-down bake (they add cookie noise). Threshold to real shadows only, then soften. Re-bake when the sun changes and send 遊程 the sun vector so live shadows match.
- **Near-lens effects need distance thinning.** Dapple flecks that look right at mid-ground become big blobs under the lens.
- `OUT_DIR` defaults to the main project folder, so copy captures out by name. Save comparison sheets under new filenames, because the image viewer caches stale files.

## 4f. Rule (v6.8, Kurt): one material, one method; no universal stamp
- **Study each material's real texture, then pick the technique that builds that structure:**
  - canopy = sprays of small layered leaves with light/dark clusters;
  - bushes = pointed/serrated leaves in mounds;
  - lawn = individual blades, tufts, clover, patches;
  - bark = vertical fissures;
  - sky = soft cloud volumes.
- **Don't reuse one atlas or one card shape for everything.** The round "leaf mass" stamp read as 粒粒波 (bead balls) on every object.
- **Silhouette comes from structure.** Leaf sprays are rooted inside the crown and rolled to point outward, and the roll must survive camera re-facing. Edges become strands (一絲絲), not round clump outlines.
- **List the technique per object, and why, in GAPS.**

## 4g. Learned in v6.8
- **Hide-by-size checks must use the local AABB.** Scaled instances (tree2 at 0.78) slipped under a world-size threshold and kept their dome crowns.
- **"OFF" is not "hidden".** A shadows-only helper switched to `SHADOW_CASTING_SETTING_OFF` becomes visible geometry (the black sky streaks). Check every helper caster when the shadow policy changes.
- **Never mirror-wrap a texture where the mirror line can be seen.** Map the sky by view direction and put the fold outside the yaw range.
- **Colour belongs in the fine tile; the macro only shades.** A blurred macro carrying the colour is what made the near lawn look like mush.
- **Rays and other big cards belong behind the play space.** The pan path, not the hero view, decides placement.

## 4h. Learned in v6.9: dynamics/physics check and soft shadows
- **Dynamics check (do it before marking anything MATCHED):**
  - Record a walk video at phone aspect, then check it frame by frame and as a strip.
  - Frame-diff spikes mean popping. Look for any shadow, shaft or glow that stays frozen while the clouds move.
  - Movie writer: `--write-movie` ignores `--resolution`. It records at the project viewport (1080x1920). For 19:9, set an override.cfg with viewport 1080x2280 first.
- **One cloud field, many readers:** ground, bushes, grass, shafts, haze and sky all sample the same `cloud_tex` / `cloud_off`.
  - Use the lookup `g = p.xz − SUN.xz·(p.y/SUN.y)` so a crown and its ground shadow darken together.
  - Separate per-system noise looks fake.
- **Shafts follow the sun vector** (`SUN_TO`), never the camera. Gate them with the cloud value at their foot.
- **Bend:** one global `pet_pos_ws` plus a lagged spring copy `pet_lag_ws` (k 100, damping 9) gives a follow-through sway for free.
  - Push grows toward the tips. Convert the world offset with `inverse(mat3(MODEL_MATRIX))`.
- **Bake from the real casters only.** Helper planes (DappleCaster, cookie planes, AO discs) stay out of every bake pass, because they were the source of the round blobs.
- **Soft shadows (real reference: late-afternoon garden shadows):**
  - Edges get softer with distance from the caster: penumbra σ ≈ 0.5 + 0.03·d wu.
  - The darkest, tightest shadow sits at the contact point, shaped by the footprint (fill_holes, σ 1.6 + 5 wu, ×0.30), not by a circle.
  - Shadow interiors are lit by the sky. Use blue-violet (0.90, 0.95, 1.16) at 64→78% brightness, so texture still reads; never black.
  - Live shadows: blur 2.0–2.2, angular_distance 0.6–0.9, opacity 0.55. On PC Mobile this costs about 0 GPU compared with hard shadows.
- **Hybrid:** static scenery is baked. Only movers (pet, bumpable props, fg plants) cast into a 1024 orthographic atlas, max 300.
  - Cost: +0.18 ms GPU on the PC and +13 draws. Remember the HUD counts about 6 draws when budgeting.

## 4i. Learned in v6.10: shadow hierarchy (Kurt: "要深就深，要淺就淺，有層次")
- **One shadow value for everything reads flat.** Give every caster CLASS its own darkness, softness and AO weight, and derive the rest from physics:
  - deepest = mass + contact: dense canopy cores, eaves, crate/pot undersides (bright 0.47–0.53, σ ×0.6–0.7, AO 1.0);
  - mid = trunks, bushes (0.58–0.62);
  - lightest = thin/see-through casters: fence, posts, string-light poles (0.80–0.82, σ ×1.4–1.5, AO 0.4);
  - canopy core→edge by local shade density (0.50 core → 0.72 edge) + ±0.05 dapple noise.
- **Contact hardening** from the real occluder distance: march each shadow texel toward the sun through the height map, σ = (0.5 + 0.03·d) × class softness; long shadows also lift (+0.30·d/260).
- **Aerial perspective, not fade.** Far shadows keep their shape but lift (+0.25) and tint toward the haze (cool (0.90,0.95,1.16) near → warm (1.04,1.00,0.86) far). Never fade far shade to zero — "the farthest ground has no shadow" was the v6.9 complaint.
- **The painted backdrop must cast too.** A ring of painted trees has no geometry; give it an analytic shadow (treeline height profile × ray to the sun, penumbra 10 + 0.1·distance), haze-tinted. 0 extra draws.
- **Class map = one extra top-down pass** (unshaded flat colours per class). Fill empty texels with the nearest class, otherwise the shadow edge picks up "none".
- **Perf/quality:** on a phone the realtime shadow pass costs far more than its PC ms suggest. For the low tier, bake everything that does not move (props too) and give the one mover a projected, contact-hardened silhouette quad (1 draw). Prove "no visible loss" with a same-view phone-aspect before/after, not a number.
- **Light from the sky:** sun glow and rays belong IN the sky dome around the real sun vector (smooth double falloff, angular-noise rays drifting with the cloud field, dithered) — a pasted sprite glow always looks stiff and bands. Shafts must run along SUN_TO, not toward a point above the camera.

## 5. Pitfalls seen
- Shading mode PER_VERTEX ignores normal maps. Depth must come from geometry and baked AO.
- GDScript: give explicit types for values read from untyped arrays or loops, otherwise you get "Cannot infer type" errors.
- `MODELVIEW_MATRIX` billboards on MultiMesh fail on Compatibility. Orient the cards on the CPU.
- `INSTANCE_CUSTOM` is unreliable on Compatibility. Pack per-instance data in `COLOR`.
- Fibonacci-sphere placement with an early `break` puts every card on the top of the ball. Iterate all points and filter by facing instead.
- Python edits to generated files must be idempotent. Post-passes must read pre-pass outputs, never their own output.
- Check the edit actually applied (tabs vs spaces) before trusting an A/B render.
- New `_n.png` imports need `compress/normal_map=1`.
- A box (gl_compatibility / llvmpipe) preview is not ground truth for additive + HDR + glow. Night pools that look subtle on the box blew out to white on PC Mobile; calibrate additive alpha on the target renderer.
