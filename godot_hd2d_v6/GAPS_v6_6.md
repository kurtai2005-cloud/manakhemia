# GAPS v6.6 (0.6.6-pilot, vc12) — concept-match pass on 遊程's merged 0.6.5 base

- **Base:** `/workspace/hd2d-v6_5-build/godot_hd2d_v6/`. I took `capture.gd`, `export_presets.cfg` and `project.godot` from it unchanged, apart from the version bump, and did not re-apply `PATCH_code_v6_5.diff`.
- **art_depth.gd** keeps 遊程's per-frame guard: it skips its ground-albedo swap when `_bake_shadow_ground` is set, so both Low and High use `ground_composed_low`.
- **v6.6 art changes**, ported onto that base: `scenes/art_depth.gd`, the new `shaders/lawn_detail.gdshader`, `tools/ai_integrate_v6_6.py`, `tools/grade_v6_4.py` and `tools/bake_low_ground_v6_4.py`.
- **Inputs:** the brief's 5 BELOW items plus Kurt's Note10+ notes on 0.6.5 (relayed by text, see the note below).
- **Renders:** RTX 4060 Mobile renderer, round 1 in `out_v6_6_r1_*` and round 2 in `out_v6_6_r2_*` (fresh folder `v6_6_r2b`).

## Status vs concept (concept = MINIMUM; BELOW is not done)

| # | Item | Status | What v6.6 did / what is still missing |
|---|---|---|---|
| 1 | Canopy | MATCHED | 64 px lit-top AI cluster atlas; fewer, bigger cards (clamp(r²/110, 5, 20) at 0.8–1.1 r); sunlit tops up to ~1.5 and a backlit rim; lighter core. The front tree reads as lit clusters, not a dark mass. |
| 2 | Hedges | MATCHED | `hedge_fuzz` leafy alpha edge; an irregular, gapped crown of sunlit highlight clumps (1.05–1.5); the dark side bobbles are gone. The crown is still a slightly even band. |
| 3 | Background (Low) | MATCHED | A pre-blurred painted forest backdrop (LINEAR) replaces the treeline bands and 4 milky haze cards. Far rows 1+2 are removed and row 0 is darkened with green-gold haze. Deep green plus golden glow, no hard pixel edges. |
| 4 | Foreground framing | BELOW | The dark balls are replaced by a leafy, lit AI fern-and-leaf corner spray pinned to both corners. It is still crisper and greener than the concept's soft, warm-dark out-of-focus corners. |
| 5 | Light rays | MATCHED | 5 thick warm-amber shafts fanning from one sun anchor, camera-billboarded. Alpha 0.5 in Low, 0.24 in High; hidden at night. |
| 6 | Lawn holes | MATCHED | 300+140 small, soft, brown pits with a lit lip; specks are brown; no black texels. |
| 7 | Near-camera grass detail | BELOW | A fine dark-blade grain plane (4 px/wu, 1 draw) is laid over the bottom third. The ground texel is still 1–2 px/wu underneath, so it is still coarser than the concept. |
| 8 | High tree shadows | MATCHED | Trees, trunks, birdhouse and trunk lantern now come from the bake (live tree casters off, as 遊程's policy intends). The bake is softer (blur 2.2, leafy edges), lighter (0.72 + 0.28·m) and dappled. |
| 9 | High prop shadows | BELOW | The live shadows of the lamp, flower beds, cans and boxes are still hard and long, because the sun is low. Softening them needs a sun shadow blur/opacity change in 遊程's renderer code, which I did not touch. |
| 10 | Bottom-third interest | MATCHED | 8 flower tufts, a small pot and baked pebble clusters; no clutter. |
| 11 | Grade (遊程's sat 0.80 / contrast 1.24, on) | BELOW | Reassessed on the PC: the lawn and cottage read fine, but the golden glow and backdrop go olive. The concept is warmer gold. I suggest 遊程 try sat 0.88 or a warm lift in highlights. |
| — | Trunks, nails, string lights, roof, haze glow | MATCHED | Unchanged from v6.5. |

**Honest score:** 11 of 15 items MATCHED (about 73 %); overall closeness to the concept is about 72 %. The 4 BELOW items are foreground blur, near grass texel density, live prop shadows and grade warmth.

## Budget (Mobile, RTX 4060; v6.5 → v6.6)

| Mode | Draw calls | Primitives | Clump cards |
|---|---|---|---|
| Low | 145 → **125** | 68 k → **43.4 k** | 5,437 → **1,210** (3 MultiMeshes) |
| High | → 198 | 49.3 k | |
| Night | → 181 | | |

Foreground: 2 corner instances (1 draw). Flowers: 8 tufts (2 draws). Lawn detail: 1 draw. Backdrop: 1 draw.

## Notes
- Kurt's Note10+ capture files named in the steering message were **not present on the box** when I checked (the path did not exist), so I acted on the text description of the 5 issues.
- PC rounds:
  - Round 1: v6.6 art before the Note10+ items.
  - Round 2: everything. The first round-2 attempt ran a stale extract (`Expand-Archive -Force` did not overwrite files). I caught it from the version print and re-rendered the same zip from a fresh folder; this still counts as round 2.
- No commit, no push, no PC shutdown. Only `C:\Users\nasa2\hd2d_test` was touched.
