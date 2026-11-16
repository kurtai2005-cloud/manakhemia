# GAPS v6.4: why the cottage and lawn read flat, and why patterns look repetitive

Written before any v6.4 edits. Compared: our v6.3 box renders (GODOT_HIGH / GODOT_LOW, cottage and lawn crops), TARGET_concept.jpg, and the 11 Octopath screenshots in `../octopath_ref`. Octopath was used for learning only, never copied.

Low is the phone default (Mobile renderer). Low turns off sun shadows, glow, fog and DOF, and SSAO is off in both modes. So any depth has to come from geometry, per-face lighting and baked shading.

## A. Cottage

| # | Gap (verified) | Evidence |
|---|---|---|
| A1 | The walls are single flat planes (box x ±29.5, z ±22). All detail (boards, corner timber, frames, vent) is only painted on. | cottage.json: 84 triangles; front wall = one plane at z=22 |
| A2 | The window has a 2 wu recess but no protruding frame, sill or lintel. The cross is painted on the glass. | planes z=20 (recess), no geometry beyond z=22 except the flower box |
| A3 | The door has a 3 wu recess but no frame posts, lintel or step. | plane z=19; nothing at z>22 around the door |
| A4 | No corner posts or beams. The corner "timber" is a 3 wu painted strip (`CORNER_TIMBER`), so the silhouette edge is razor thin. | rebake_cottage_atlas.py |
| A5 | The roof is a 3 wu slab with a 6/4 wu overhang, but there is no bargeboard or fascia board, no ridge cap, and the gable roof edge reads as a thin line. | planes z=±26 only 3 wu tall |
| A6 | The chimney has no cap. It is a plain box with stripes. | plane y=142 = flat top |
| A7 | No foundation plinth. The stone band is painted on the wall plane (y<8). | FOUNDATION_Y painted |
| A8 | No baked AO or contact shadow: nothing under the eaves, around frames, at the wall base, at corners or under the flower box. With no SSAO and no Low shadows, nothing darkens creases. | atlas = tiles × official colours only |
| A9 | Every board has the same value. One continuous 64 px clapboard tile, so there is no per-board value or hue, no butt joints, no nail or knot marks (the target has dark nail holes and varied boards). | v6.3 render: wall reads as uniform stripes |
| A10 | Face values hardly differ. The front (+Z) faces away from the low sun and gets only ambient/fill, so front, right wall and soffit all sit in the same mid-brown. The target separates lit and shade faces clearly. | cottage crop High vs Low ≈ identical |
| A11 | The cottage material is per-vertex shaded, so its normal map does nothing (in Low or High). Relief must be geometry or baked. | `_apply_atlas_materials` sets SHADING_MODE_PER_VERTEX |
| A12 | No weathering: no dirt splash at the base, no moss at the corners, no sun-fade on the lit wall, no soot on the chimney. | atlas |

## B. Lawn

| # | Gap | Evidence |
|---|---|---|
| B1 | A single flat ground plane (512 px, 2 px/wu) plus a tiled outer field. No height or volume. | capture.gd ground + outer planes |
| B2 | Mid-frequency "camo" blotches (lawn A) dominate. Too much speckle relative to the target's soft moss. | lawn crops |
| B3 | No large-scale light-to-shade value gradient. The target has a sunlit clearing, darker edges and a dark foreground. | target vs ours |
| B4 | No baked contact AO where the lawn meets the cottage, path, fence, bed, trees, lamp or props. Objects look pasted on, especially in Low (no shadows). | ground_composed |
| B5 | Tufts are sparse and only at the edges. No darker grass edge along paths, walls, fence or tree bases. No blades breaking the silhouette of edges. | `_setup_tufts`, 216 tufts |
| B6 | Few decals: no pebbles, fallen leaves, clover or tiny flowers spread through the lawn (the target has many tiny specks). | ground_composed |

## C. Patterns too regular / repetitive (Kurt)

| # | Gap | Where |
|---|---|---|
| C1 | One base image per material. Variants b/c are only rolled or flipped copies, so stones, boards and shingles repeat. | wood, cobble, roof, bark |
| C2 | No per-element variation (value, hue, shape) for each board, stone, brick or shingle. | all |
| C3 | No macro overlays: moss patches, weathering, dirt near the ground, sun-faded areas. | cottage, roof, path, lawn |
| C4 | No decals to break repeats: flowers, pebbles, leaves, cracks. | lawn, path, cottage |
| C5 | Lawn still repeats every 128 wu on the outer field, and the A/B mask is a smooth sine. | grass_outer_256 |

## Plan (once, highest quality; renderer / perf / input / DOF code untouched)
- Geometry (new `scenes/cottage_depth.gd`, one call from capture.gd):
  - window frame and lintel; door posts, lintel and stone step;
  - 4 corner posts and a tie beam;
  - bargeboards on both gables, eave fascia boards and a ridge cap;
  - chimney cap and a stone plinth.
  - All parts get per-vertex AO: dark where they touch the wall or ground.
- Cottage bake post-pass (`tools/cottage_depth_bake_v6_4.py`, world position per atlas texel from the rebake):
  - per-face lit/shade value;
  - AO under eaves and the gable edge, around window/door frames, at the wall base and corners, under the flower box, inside the recesses, at the chimney/roof junction;
  - per-board value/hue, butt joints and nail marks;
  - per-shingle and per-brick value/hue;
  - moss on the roof and wall base, dirt splash, sun-fade, chimney soot.
- Lawn and ground:
  - 512 px four-source lawn mix (A, B and their 180° turns, irregular dithered mask), unique over the whole 256 wu ground; the outer field repeats only every 512 wu;
  - large-scale gradient (lit clearing, darker edges and foreground);
  - contact AO around every object;
  - decals (pebbles, leaves, clover, tiny flowers, worn soil);
  - darker edge tufts along paths, walls, fence, trees and bed (MultiMesh cards, cheap on Mobile), plus a few small tufts in the clearing.
- Path: per-stone value/hue/moss in world space (labelled stones, so no two repeats look alike), cracks, pebbles and leaves in the gaps.
- Extra tile variants: brick_d, roof_d, cobble_d, wood_d are genuinely different, not rolls.
- Budget: about 40 extra boxes (<500 triangles) and about 300 extra tuft instances, all baked or static, so Low cost is close to v6.3.

## D. Kurt's v6.2 phone captures (ground truth)
The two attachment paths given (`…/attachments/4792647ac5….jpg` Low ~60 fps, `…/dd937cc4e1….jpg` High 35–55 fps) were **not found on the box**; the observations below are the parent's read of them.

| # | Observation (phone) | Fix in v6.4 (art only) |
|---|---|---|
| D1 | Low: huge camo blotches on the lawn | 512 px 4-source lawn at half macro size, dithered borders, less high-frequency noise, grade (`tools/grade_v6_4.py`) |
| D2 | Low: no cottage shadow side | per-face value baked in the atlas (left 1.10 warm / right 0.80 cool / back 0.84) |
| D3 | Low: no eave or contact shadow | atlas AO under eaves, around frames, wall base; vertex-AO relief parts; ground contact AO |
| D4 | Low: flat orange roof | per-shingle value/hue, moss, sun-fade, shingle-tip tabs, bargeboards, ridge cap |
| D5 | Low: trees cast no ground shadow, evenly lit | the game's own High sun-shadow mask baked into `ground_composed_low.png` (swapped in at runtime only when sun shadows are off) |
| D6 | Low: empty foreground | foreground tufts (plain/flowered 75/25), clover/flower decals, soft framing bush + pot in the near corners |
| D7 | High: DOF far too strong, focus not on 團絨 | not touched (遊程 owns DOF) → `DOF_NOTE_v6_4.md` |
| D8 | High: cottage still flat | same geometry/bake fixes as D2–D4 |

## E. SILHOUETTE
| # | Gap | Fix |
|---|---|---|
| E1 | Trees/bushes read as smooth spheres | camera-facing alpha-scissor leaf-clump cards (`leaf_clump_a/b/c`, 32 px) around every leaf ball's screen rim, 5 more on the visible face, hanging strands under big canopies (`shaders/leaf_card.gdshader`, `art_depth.gd::_leaf_fringe`) |
| E2 | Straight roof edge | 1 merged mesh of shingle-tip tabs (2–4.2 wu, varied width/rotation) along both eaves and gables |
| E3 | Straight wall edges | ivy clump cards up the front-left corner and over the window, hanging strands |
| E4 | Even fence top | 7 extra stakes, 15–21 wu tall, ±5° tilt |
| E5 | Objects pasted on the lawn | dark tuft rings at the base of every prop (from `art/props_v6_4.json`) + path/wall/fence/tree edge tufts |
| E6 | Blend sorting cost | all silhouette cards are alpha-scissor (no blending); only halos/rays/motes are additive |

## F. Concept gap list (parent's side-by-side, 1–10) — status after PC round 2
Concept = **minimum baseline**. BELOW = not done.

| # | Item | What v6.4 does | Status |
|---|---|---|---|
| 1 | Raking upper-left sun, god rays, motes, long diagonal shadows | High: sun shadows + shafts + dust (遊程's). Low: baked shadow mask, 5 additive ray strips, 60 static motes | BELOW (no soft atmospheric glow; rays thinner than target) |
| 2 | Lawn: fine dark short grass, holes, dirt specks, golden centre, less yellow | grade (olive balance, blue lift, green-black toe), golden centre lift, 5 200 holes/specks/blade tips | BELOW (close; target holes bigger and more visible) |
| 3 | Trunks: thick red-brown, grooves, ivy, mushroom birdhouse, lantern | r 10.5–14.5 + root flare 23, bark_a triplanar 24 wu, ivy cards, mushroom birdhouse, trunk lantern + halo | BELOW (grooves too weak at phone distance) |
| 4 | Canopy: clustered clumps, backlit translucent edges | leaf-clump rim cards + BACKLIGHT + upper-left value lift | BELOW (interior still sphere-like) |
| 5 | Bushes: boxy-round, fuzzy edges, top highlights | rim cards + 2 sun-caught crown cards | BELOW (still round) |
| 6 | House: nail holes/damage, ivy corner, tile relief + edge lip, red layered-brick chimney | nails ×2, cracks, chips, rot; ivy cards; shingle tabs; red brick + corbel bands | chimney/ivy/roof edge MATCHED; boards BELOW (nail dots fainter) |
| 7 | Background: layered hazy forest | 3 alpha-cut haze treeline bands in front of bg_sky + 3D far rows with fringe | BELOW in Low (sharper than target); High relies on DOF |
| 8 | Foreground framing: blurred bushes + pots in near corners | pre-softened dark bush cards both corners + 1 pot | BELOW (less lush) |
| 9 | Grade: deeper darks, warm highs, strong contrast | texture-side grade on ground; env grade untouched (renderer) | BELOW (screen blue still low; env proposal in DOF_NOTE) |
| 10 | String lights glow + halo even in Low | per-bulb unshaded additive halo found from the emissive mask (33 halos) | MATCHED |

## G. Self-critique after PC round 1 (Mobile renderer, RTX 4060)
| Found below concept | Why | Fix (round 2) |
|---|---|---|
| Trunks flat saturated orange | tint (1.18, 0.80, 0.62) too warm under Mobile tonemap | tint (0.92, 0.64, 0.52), bark tile 24 wu |
| Foreground frame bushes too light, read as stickers | sprite values too high | sprite base darkened ~35 % so it frames like a vignette |
| Bushes no top highlight | rim cards only | 2 crown cards per bush ball at value 1.35 |
| Lawn grade first pass went grey/olive | blue lift too strong (×1.2 + 0.16 L) | inner (1.0, 0.97, ×1.3 + 0.10 L), outer greener (0.98, 1.0, ×1.15 + 0.05 L) |
| High DOF far too strong | 遊程's code | DOF_NOTE_v6_4.md only |
