# GAPS v6.7 (0.6.7-pilot, vc13, hk.vizard.glimmer.hd2dpilot)

- **Base:** 遊程's 0.6.6 merge (`/workspace/hd2d-v6_6-build`). Their code is untouched (renderer, perf, input, DOF, grade, `capture.gd` camera). The only edit in `capture.gd` is the version line: `hd2d v6.7 start`. A diff against their file shows nothing else.
- **Ground truth:** Kurt's Note10+ captures `phone_caps/v6_6_{high,low}_{1,2,3}.jpg`.
- **Renders, all at phone aspect 19:9:**
  - box: 1080×2280 (llvmpipe, gl_compat), plus 594×1254 (0.55 render scale) for the texel check;
  - PC RTX 4060, Mobile renderer, 540×1140, 2 rounds in fresh folders `C:\Users\nasa2\hd2d_test\v6_7b_r1` and `v6_7b_r2`. Each round's version line was checked (`config/version="0.6.7-pilot"`, `version/code=13`, log `hd2d v6.7 start`). No shutdown.
- **Walk-path set:** pet at the 4 walk corners + centre × camera yaw −30/0/+30 (box, phone aspect).
- **Side-by-side:** `previews/v6_6phone_vs_v6_7.png`. Top row = the 0.6.6 phone captures; bottom row = v6.7 at the nearest equivalent view.

## Status (TARGET_concept.jpg is the minimum; BELOW = not done)

| # | Item | 0.6.6 phone | v6.7 | Evidence / notes |
|---|---|---|---|---|
| A | Near-camera lawn | BELOW | **MATCHED** | `NearLawn` plane follows the camera. It has a 4 px/wu blade detail tile over a 2 px/wu macro with warm-gold and cool pools. At 0.55 scale a near texel is ≈1.15 screen px, the same density as the mid-ground; no blocky texels or uniform olive camo (`/tmp/w67/texel_cmp.png`: phone low_3 vs v6.7). |
| B | Flat dark discs behind canopies | BELOW | **MATCHED** | Cards now cover the full sphere, with dark leafy undersides (atlas row 3). The cores are a leaf-textured shader with a leafy rim discard. Walk views show no flat discs. Exception: from the back-right corner a ring-tree lobe can read as a smooth dark mass at the top edge (minor). |
| C | Grey-white diagonal bands / world-edge break | BELOW | **MATCHED** | Cause: 遊程's Shafts cards, my rays and the flat backdrop board were seen edge-on once the camera moved. Fix: a 360° cylinder backdrop (r 462); axis-billboarded rays, plus 遊程's Shafts children re-faced through their `alpha` param with a grazing fade; an outer ring of 20 trees and 30 bushes. No edges or bands in any of the 15 walk/yaw views. |
| D | Long hard shadow bands | BELOW | **PARTIAL** | The ground bake was redone with the sun raised to 38° elevation: shorter, soft, lighter, and the cookie noise removed. A wide mask covers the outer lawn. On High, the **live** prop shadows (lamp, fence) still use 遊程's 18° sun, so long diagonal bands remain in PC High. This needs 遊程 (note 1). |
| E | 團絨 hidden behind bushes/pots | BELOW | **MATCHED** | The corner sprays are gone. Planted plants are clamped to z ≥ 100, outside the walk bounds. The pet stays visible at hero, near and far shots and in all walk views. |
| F | Soft, warm foreground corners | BELOW | **PARTIAL** | Warm and grounded, but **crisp**, not soft like the concept. Real blur needs High near-DOF (遊程's DOF; note 5). |
| G | Wind sway | none | **MATCHED** | Vertex sway with a per-instance phase on canopies (0.035), bushes (0.025), tufts (0.9 wu tip) and planted plants. All use one shared `wind()`. The cost is a few ALU ops in the vertex shader; same on Low. |
| H | Scrolling dappled leaf light | none | **MATCHED** | `ground_dapple` overlay (1 draw): sun flecks in shade and leaf shade in sun, drifting with the same `wind()`. It is thinned near the lens, so there are no big yellow blobs (fixed after PC r1), and hidden at night. |
| I | Bushes/hedges as layered leafy clumps | BELOW | **MATCHED** | 2–5 mounds of varied height, broken leafy crowns, dark base gaps, flowered cells, contact AO. |
| J | Canopies | BELOW | **MATCHED** (shape) / BELOW (framing) | Big irregular masses: 20 % big clumps, small edge sprays at 1.02–1.14 r, dark interior gaps, and a lit-top-to-dark-bottom gradient. The tree **tops are still cut** at phone aspect. Fixing that is a camera framing change (K). |
| K | Phone framing | BELOW | **BELOW** (needs 遊程) | All renders are now judged at 19:9. My proposal is in note 4. It is camera code, so I did not change it. |
| — | Floating front sprays | BELOW | **MATCHED** | 4 planted crossed-quad plants with roots buried 1.5 wu. They cast shadows and have contact AO, dark tufts and flowers at the foot. They are depth-written, so they occlude 團絨 correctly. No screen-space cards. Grounded from every walk angle. |
| — | 360° garden from any pet position | n/a | **MATCHED**, one exception | With the pet at back-left (−140,−110), the camera ends up inside the big tree's crown or trunk. This is a camera/layout limit (note 3). |

**Visual closeness, on the same scale as v6.5 ≈ 80 %:** v6.6 phone ≈ 81 % (Kurt's captures exposed the world edges, discs and lawn). **v6.7 ≈ 85 %.**
- The earlier v6.7 draft said 86 %. That figure was judged on window-clamped PC frames, not at phone aspect.
- What still holds v6.7 back:
  - cut canopy tops (K);
  - live 18° shadows on High (D);
  - crisp foreground (F);
  - an olive haze band at the horizon (grade/fog, 遊程).

## Counts (PC Mobile, 540×1140, r2)

| Mode | Draws | Primitives | Budget (v6.5 Low) |
|---|---|---|---|
| Low | **132** | **65,032** | 145 draws / 68k prims ✔ |
| High | 206 | 70,962 | — |
| Night | 188 | 70,926 | — |

- **Cards:** clump 4,340 (152 canopy masses), tufts 216 + 25 flowers, base tufts 218, edge tufts 158 + 40, silhouette cards 335, halos 33, contact AO 71, fg flowers 8. Total ≈ 5,444 against 5,437 in v6.5: flat.
- Re-facing the cards on camera move rewrites one MultiMesh per frame, and only after the camera moves more than 6 wu or turns more than 0.06 rad.

## Notes for 遊程 (code I did not touch)
1. **Sun direction:** please set the realtime sun so live shadows match the new bake. In `capture.gd`, the sun light's direction vector (toward the ground) should be **(0.645, −0.616, 0.453)**: elevation **38°**, azimuth **54.9° from −Z toward −X** (the sun is behind-left of the cottage). It replaces `Vector3(0.74,−0.30,0.52)` (≈18°), which casts the long lamp/fence bands on High. `art_depth.gd` already uses `NEW_SUN_DIR` for the bake. 50° was tested and put the crown shadow on the clearing.
2. **Camera yaw/pitch limits:** the code applies pure XZ follow with no yaw and pitch fixed at 30°. Content is now 360°-dressed. I verified yaw −30/0/+30 at the walk corners; wider yaw and other pitches are untested. Please send the intended yaw/pitch limits so I can verify at min, mid and max.
3. **Walk bounds / follow limits:** the walk area is x −140..150, z −110..90, which puts the camera at x ≈ −128..162, z 80..280. At the back-left corner the camera sits inside the big tree (crown/trunk at (−88,−44)). Options: clamp the walk area to x ≥ −110 when z < −70, or clamp camera follow x ≥ −100 in that band.
4. **Framing proposal (K):** at 19:9 with KEEP_WIDTH hfov 50, the vertical half-fov is ≈44.5° and canopy tops are cut. Proposal: raise `PORTRAIT_TARGET.y` 38 → 58 and dist 250 → 270, keeping hfov 50. The trees should then fit. Untested: please check the pet's screen-height fraction stays ≥ 0.20. Alternative: hfov 46 with the target y +20.
5. **Foreground softness (F):** enable a light near DOF on High (near_transition ~40 wu, from the camera ~70 wu). Low stays crisp.
6. **Shafts:** I re-face your 12 `Shafts` cards each frame from `art_depth._grab_shafts` (axis billboard + grazing fade via your `alpha` param). If you rebuild `_setup_fx`, keep the node names or call the same re-facing.
7. **tuft.gdshader** (art shader) now sways (0.9 wu tip, shared `wind()`). Tell me if you want a uniform to switch it off.
