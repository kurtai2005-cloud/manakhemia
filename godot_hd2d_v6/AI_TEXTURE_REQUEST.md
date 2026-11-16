# AI texture request (optional) — v6

> **Status (v6.3, 2026-11-12):** all 7 are now integrated (lawn, clapboard, leaf in v6.1; brick, cobble, bark, roof and a second lawn base in v6.3). See CREDITS.md.

v6 ships **hand-authored** textures (tools/author_v5_textures.py). AI bases would help most where the hand-made tiles are still weakest: they are flat at 16 px and repeat visibly on large areas.
If you make them, I will **not** use them raw. I will snap each one to our V3-A palette ramps (5–6 tones), resample it to 1 texel = 1 wu with nearest filtering, keep it tileable, and derive the normal map from height.

General prompt suffix for every image: `seamless tileable texture, orthographic top-down / front-on flat view, even soft lighting from top-left, no perspective, no shadows cast from outside, no text, pixel-art friendly, 16-bit JRPG HD-2D style, warm golden-hour palette`

| # | File name | Size | Tiling | Prompt (plus the suffix above) | Where it is used |
|---|---|---|---|---|---|
| 1 | `ai_lawn_base.png` | 512×512 | seamless both axes | "lush mown lawn grass seen from above, olive and golden-yellow greens, tiny clover and a few small pale flowers, soft clumps, low contrast, no dirt holes" | centre lawn (`ground_composed`), outer field |
| 2 | `ai_clapboard_wood.png` | 256×256 | seamless horizontally, 8 boards high | "horizontal painted-warm pine clapboard siding, each board with a slightly darker lower lip shadow, fine wood grain, a few small knots, honey-orange timber" | cottage walls (rebake) |
| 3 | `ai_brick_running.png` | 256×256 | seamless both axes, running bond, 8 courses | "old red clay brick wall, running bond, recessed light grey-beige mortar, chipped corners, a few hairline cracks, slight moss at the bottom" | chimney, garden wall props |
| 4 | `ai_cobble_path.png` | 256×256 | seamless both axes | "rounded grey cobblestones with dark soil gaps, some flat worn tops catching light, a little moss between stones" | path, cottage foundation |
| 5 | `ai_leaf_clump.png` | 256×256 | seamless both axes | "dense bush foliage of small pointed leaves, layered, highlights on upper leaves, darker gaps between leaves, olive-green" | bushes, tree crowns |
| 6 | `ai_bark.png` | 256×512 | seamless vertically | "vertical tree bark with long grain ridges and deep cracks, dark warm brown" | tree trunks, far forest, timber |
| 7 | `ai_roof_tile.png` | 256×256 | seamless both axes | "terracotta clay roof tiles, overlapping rows, each tile edge lit at top and shadowed below, weathered" | cottage roof |

Priority if you only make a few: **1 (lawn), 2 (clapboard), 5 (leaf)**. These are the largest areas on screen in the portrait framing.
