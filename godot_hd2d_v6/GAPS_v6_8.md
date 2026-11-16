# GAPS v6.8 (0.6.8-pilot, vc14, hk.vizard.glimmer.hd2dpilot)

- **Base:** 遊程's 0.6.7 merge (`/workspace/hd2d-v6_7-build`): sun 38°, camera target y 58 / dist 270 / hfov 50, High near DOF 0.05, walk clamp.
  - Their `capture.gd` is used as-is. The only edits are the version line (`hd2d v6.8 start`) and the header comment.
  - All art changes are in `scenes/art_depth.gd`, shaders and textures.
- **Ground truth:** Kurt's 0.6.7 phone captures `phone_caps/v6_7_{low_1,low_2,high_1,high_2}.jpg`, plus `TARGET_concept.jpg`.
- **Kurt's words (the only feedback that counts):**
  - 粒粒波 → 一絲絲: wispy leaf strands, not round beads;
  - big smooth balls on the tall tree tops;
  - black in the sky;
  - a weird seam mid-sky;
  - wants white clouds and a detailed sky.
- **Renders:**
  - box at **1080×2280** (phone 19:9), plus a 594×1254 (0.55 render scale) lawn texel check;
  - PC RTX 4060 Mobile at 540×1140 (19:9; the window can't open at 2280 tall). 2 rounds in fresh folders `C:\Users\nasa2\hd2d_test\v6_8_r1` / `v6_8_r2`. Version line checked both times (`0.6.8-pilot`, code 14, log `hd2d v6.8 start`). No shutdown.
- **Pan path:** pet at the 4 walk corners (back-left uses 遊程's clamp, −110,−110) + centre, at the real camera (yaw 0), plus yaw ±30 at the centre and corners for robustness. High and Low.
- **Side-by-side:**
  - `previews/v6_7phone_vs_v6_8.png`: top row = phone 0.6.7, bottom = v6.8 at the nearest pan position;
  - `previews/lawn_v6_7phone_vs_v6_8_055.png`: lawn at phone scale.

## Status

| # | Item | 0.6.7 phone | v6.8 | Evidence / cause / fix |
|---|---|---|---|---|
| 1 | Foliage: wispy strands, no beads | BELOW | **MATCHED** | **Canopy:** every card is a leaf spray (twig, small pointed leaves, wispy tips). It is rooted inside the crown and rolled to point outward, so the outline is strands. **Bushes:** serrated-leaf mounds with lumpy crowns and florets. Card budget is lower (4,131 vs 4,340 clump cards). Left: crowns read a little "noisy" up close compared with the concept's painterly sprays. |
| 2 | Big smooth balls on tall tree tops | BELOW | **MATCHED** | **Cause:** 遊程's voxel `tree` ArrayMesh (4 instances) has smooth dome crowns that were still visible. v6.7 never hid them, and a first v6.8 check missed the scaled ones (it tested the world AABB). **Fix:** hidden at build and again at frames 3 and 12; kept for the bake tool. Small back voxel trees get spray crowns. No dome in any pan view. |
| 3 | Black horizontal streaks in the sky | BELOW | **MATCHED** | **Cause:** 遊程's `DappleCaster`, a 600 wu leaf-cookie plane at y 230. With the ground bake, their shadow policy sets it to `SHADOW_CASTING_SETTING_OFF`, which makes it **visible**: black cookie blobs seen almost edge-on (High). **Fix:** the art layer hides it unless it is SHADOWS_ONLY. No streaks in any High or Low pan view. |
| 4 | Mid-sky seam | BELOW | **MATCHED** | **Cause:** the v6.7 backdrop cylinder's painted sky came from a mirror cross-fade texture (mirror line mid-sky), plus the hidden flat `bg_sky` board. **Fix:** one sky dome mapped by view direction. The image spans the front 200°, the back 160° is mirrored, and the fold sits at ±100° (outside ±45° yaw + half-fov). The forest ring now carries only a ragged treeline; its painted sky is cut out. `bg_sky` is hidden. |
| 5 | Detailed sky, white clouds, warm sunset | BELOW | **MATCHED** | AI base `ai_sky_v68.jpg`, then toned (teal → green-gold, peach → warm gold, ×0.9) and palette-reduced to 48 tones. Clouds drift slowly with the shared wind. Night is dimmed to deep blue. The sun glow sits upper-left, where our sun is. It is brighter and airier than the concept's hazy gold, by Kurt's request. |
| 6 | Near lawn: golden-green fine detail | BELOW | **MATCHED (Low)** / PARTIAL (High) | **Cause of the mush:** the blurred macro carried the colour. **Fix:** the colour now comes from a blade tile (1 px blades, tufts, clover, dry and moss patches, 4 px/wu); the macro only shades it, with a shade floor of 0.66. Hand-over to the ground is dithered over 80 wu, with flecks thinned near the lens. At 0.55 scale the blades are readable. On **High**, 遊程's near DOF (0.05) still blurs the bottom (note 5). |
| 7 | Bushes in straight rows | BELOW | **MATCHED** | Ring bushes are clusters of 1–3, mixed sizes, reflected off the walk edge, with irregular 70–160 wu gaps. 遊程's long hedge boxes are split into segments that are pushed sideways, vary in height and have gaps. One of their hedges still runs diagonally, but now reads as a lumpy cluster, not a row. |
| 8 | Grey-white diagonal band (high_2) | BELOW | **MATCHED** | **Cause:** rays and 遊程's Shafts stood inside the garden (z −117..−280) and crossed the left trees once the camera panned left. **Fix:** all of them now stand behind the garden (z ≤ −270), with axis billboard + grazing fade + camera-distance fade. No band at any pan position or yaw ±30. |

**Visual closeness, same scale (v6.5 ≈ 80 %):** 0.6.7 on Kurt's phone ≈ 82 % (the streaks, domes, beads and mush cost what the box renders hid). **v6.8 ≈ 88 %.**
- What still separates it from the concept:
  - the concept is a tighter portrait (framing approved by Kurt, unchanged);
  - the High bottom blur;
  - the sky is brighter than the concept's hazy gold;
  - canopy sprays are crisper and noisier than painted leaves.
- 60 fps on the Note10+ is not measured here. Low stays inside the draw/primitive budget (below).

## Per-object technique (one material, one method)

| Object | Technique | Why |
|---|---|---|
| Canopy (trees, ring trees, back voxel trees) | Procedural **leaf-spray atlas** (`tools/foliage_v6_8.py`): twig + alternating lanceolate leaves 4–7 px, bare wispy tips, light/dark cluster per side twig, back layer darker. Cards **rooted inside the crown and rolled outward** (roll kept when re-facing). Dark textured core shrunk to 0.70 r. | Kurt wants 一絲絲 strands: the silhouette must be made of twig ends, and the root→tip axis must point outward. Only per-leaf construction plus roll gives that. An AI image couldn't give clean per-cell alpha anchored at the root. |
| Bushes / hedges | Procedural **serrated-leaf mound atlas**: ovate leaves with toothed edges, radiating from the base, lumpy envelope, deeper blue-green, 5-petal florets. Small roll jitter only (upright). Long hedges are split into clusters. | Shrubs read by leaf shape (pointed/serrated) and mass, not twigs. A different leaf and palette from the canopy, so they no longer look like the same stamp. |
| Lawn | Procedural **colour blade tile** (4 px/wu): 1 px blades with dark root → gold-green tip, fanning tufts, clover trefoils, dry/moss patches. Macro = shading only. | Grass is individual blades. Detail has to live in the colour, not in a blurred macro; it is checked at 0.55 phone scale. |
| Bark | Unchanged v6.5 **AI-based groove bark** + geometric fissures (vertex-colour darkened). | It already reads as vertical fissures on the phone. |
| Sky | **AI base + hand clean-up** (tone transfer, 48-tone palette, de-JPEG). Direction-mapped dome, mirrored back, slow wind drift. | Soft cloud volumes with depth are what painting is good at. Direction mapping gives one continuous sky with no card edges. |
| Distant forest | v6.7 painted ring with a **procedural ragged crown-line alpha** (dithered cut). | Gives depth under the sky without a flat hill line or the old painted rays. |
| Light rays | Unchanged look; **placement** moved behind the garden, plus a distance fade. | The band was a placement problem, not a look problem. |

## Counts (PC Mobile 540×1140, r2)

| Mode | Draws | Primitives |
|---|---|---|
| Low (hero) | **130** | **66,726** |
| Low (pet near) | 132 | 67,942 |
| High | 203 | 72,654 |
| Night | 185 | 72,618 |
| Budget, Low | ≤ 145 | ≤ 68k |

- **Low passes, with only 0.1–1.9 % primitive headroom.**
- **Cards:** clump 4,131 (156 canopy masses + bushes), tufts 216 + 25, base tufts 218, edge tufts 158 + 40, silhouette 347, halos 33, contact AO 92, fg flowers 8. Total ≈ 5,268 (v6.7: 5,444).

## Notes for 遊程 (code I did not touch)
1. **DappleCaster:** when `tree_live` is false, `_apply_mode` sets it to `SHADOW_CASTING_SETTING_OFF`, which makes it **visible** (black sky streaks). Please set `visible = tree_live`, or keep SHADOWS_ONLY and toggle visibility instead. The art layer hides it for now.
2. **Voxel `tree` meshes:** their dome crowns show above the leaf masses. The art layer hides every `tree` ArrayMesh (local AABB height > 200). Instancing only the trunk, or not instancing these meshes, would be cleaner.
3. **`bg_sky` board:** hidden by the art layer (replaced by `SkyDome_v68`). It can go from your setup.
4. **Shafts:** `_grab_shafts` moves cards with z > −270 to z −270..−340, so they never cross the garden. If you rebuild `_setup_fx`, please place them there.
5. **High near DOF 0.05** blurs the new blade lawn in the bottom third. Proposal: `dof_blur_near_distance` ≈ 140 with transition 40 (the bottom of the frame is ≈ 53 wu away), or near blur only below 0.03. Low is unaffected.
6. **Yaw:** I checked yaw ±30. The sky fold sits at ±100°, so up to ±45° yaw stays seamless. The forest ring and the tree/bush ring are 360°.
7. **Primitive headroom on Low is small** (≤ 1.9 %). Please tell me before adding Low geometry; I can trim ring cores or bush cards.
