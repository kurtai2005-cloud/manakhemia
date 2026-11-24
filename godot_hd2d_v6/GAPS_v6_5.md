# GAPS v6.5 — concept-match foliage pass (0.6.5-pilot, vc 11)
Rule: TARGET_concept.jpg is the **minimum**. BELOW = not done. Ground truth = RTX 4060 Mobile renders (`previews/pc_mobile_v6_5/`).

## Before edits (from the v6.4 BELOW list, in priority order)
| # | Gap (v6.4 Mobile) | Why | Plan |
|---|---|---|---|
| 1 | Canopy interior reads as textured spheres | the sphere texture is the visible surface; fringe cards only on the rim | rebuild every leaf ball as an AI clump-card cluster over the camera-facing hemisphere + an inner darker layer; the sphere becomes a dark unshaded core (= the dark gaps) |
| 2 | Bushes round | lobes are spheres | AI boxy-round hedge card sized to the lobes' AABB, fuzzy clumps on the top/sides, lobes → dark core |
| 3 | Trunk grooves invisible at phone distance | 32 px bark at 24 wu, smooth cylinder | 24-side fluted mesh (every other vertex in 16–24 %), vertex-dark fissures, AI deep-groove bark (64 px ↔ 48 wu) + normal |
| 4 | Lawn holes too small / faint | 1–2 px specks only | 5–8 × 3–5 px pits (≈ 3×2 wu) with a lit dirt lip, 360 inner + 160 outer |
| 5 | Nail holes faint | 1 nail, AO 0.42 | 2 nails per board end at AO 0.22 + a lit texel, worm holes, cracks 0.42 on 22 % of boards, chips 16 % |
| 6 | Background sharp | contrasty treeline bands | lower-contrast bands ramping to the sky colour + 4 fake haze cards + clump haze ×1.7 |
| 7 | Foreground thin | 1 blob per corner | 7 pre-softened AI clumps + flowered tufts + a pot per corner |
| 8 | No soft haze glow | — | 4 additive soft-glow sprites (sun gap, clearing, lantern line) |

## Self-critique after PC round 1 → fixes in round 2
| Found | Why | Fix |
|---|---|---|
| Background milky / pale ghosts | haze cards alpha 0.55–0.9 and clump haze ×2.6 | alpha 0.28–0.65, haze ×1.7 (max 0.4) |
| Hedges look like identical lego rows | same proportions and value | per-hedge width/height jitter, value 0.84–0.96, +1 side clump per side |
| FG corners still thin | no accents | 6 flowered tufts per corner |
| 454 draw calls (Compatibility Low) | ~230 individual core spheres | cores merged per haze level into 1 low-res mesh each (8×4), originals shadow-only → Mobile Low **145 draws, 68 k primitives** |

## Status after PC round 2 (Mobile)
| Item | Status | Remaining gap |
|---|---|---|
| 1 Canopy clusters / depth / dark gaps / backlit edges | **BELOW** | the big front crown is a dark noisy mass. The concept has fewer, larger, clearly separated clusters with bright yellow tops. Far crowns are too pale. Next: 3–4 big clusters per crown (sprite 64 px), strong top-lit value 1.4+ |
| 2 Hedges boxy-round + fuzzy | **BELOW** | the shape is right but the edge fuzz is weaker than the concept, and the crown clumps read as dark bobbles. Next: an alpha-cut leafy top edge on the hedge sprite itself; drop the dark side clumps |
| 3 Trunk grooves | MATCHED | — |
| 4 Lawn holes / specks | MATCHED | — |
| 5 Nails / damage | MATCHED | — |
| 6 Background soft / layered / hazy | **BELOW** | still too pale, with pixel-hard edges. The concept is dark-green bokeh with golden light. Next: darker mid band, a pre-blurred forest sprite (like the FG trick), less haze on the nearest row |
| 7 Foreground framing | **BELOW** | sparse. Next: 2–3× the clump count, bigger pots partly cropped, pink flower clusters |
| 8 Soft haze glow | MATCHED | — |
| (v6.4) Light / rays | **BELOW** | the rays are thinner than the concept's volumetric shafts |
| (v6.4) Grade | **BELOW** | the background pushes the overall image pale. The env grade belongs to 遊程 |
| String lights, roof edge, chimney, ivy, fence, path, lamp | MATCHED | — |
