# GAPS v6.9 (0.6.9-pilot, vc15): art on 遊程 v6.8 build

- **Code:** 遊程's `scenes/capture.gd` is unchanged except the version line (header line 2 + "hd2d v6.9 start" print). `prop_bump.gd` and `data/prop_bump.json` are 遊程's, unchanged.
- **Minimum:** TARGET_concept.jpg. BELOW is never "done".
- **Evidence:**
  - Side-by-side vs the phone 0.6.8 captures: `previews/v6_8phone_vs_v6_9.png`.
  - Walk videos: `previews/walk_low_v6_9.mp4`, `walk_high_v6_9.mp4`, `walk_low_hard_vs_soft_v6_9.mp4`.
  - Strips: `walk_strip_{low,high}_v6_9.png`.
  - Corner pans: `pan_{low,high}_v6_9.png`.
  - Shadow comparisons: `shadow_baked_vs_hybrid.png`, `shadow_hard_vs_soft.png`.

## 1. Status vs concept (and vs phone 0.6.8)
| # | Item | Status | Evidence / note |
|---|---|---|---|
| A | Foliage cores → leaf cards, no balls | **MATCHED** | Interior spheres are off (CORE_SPHERES=false) and replaced by dark spray/serrated cards. The voxel domes on trees_bL/bR are hidden and replaced by a grooved trunk plus sprays. Phone high_1 had a dark ball silhouette top-left; v6.9 has leaf masses. |
| B | Shadows shaped by real objects, no discs | **MATCHED** | The bake now uses real leaf-alpha cards turned to face the sun. DappleCaster and the AO discs are out of the bake. Phone high_1/2 had round black blobs; v6.9 has ragged leaf shadows. |
| C | Every object casts | **MATCHED** (garden) | Trees, bushes, fence, cottage, beds and props: baked. Pet, props and fg plants: live (hybrid). Far ring trees only cast trunk-weighted shadows, which is enough at that distance. |
| D | Dynamic light (shafts / glow / dapple, clouds, 38° sun) | **MATCHED** | One shared cloud field drives ground, bushes, grass, shafts, haze and sky. Shaft axis = SUN_TO. Each shaft is gated by the cloud at its foot, plus flicker and width breathe. Visible in the walk videos. |
| E | Walk videos + frame/strip check | **MATCHED** content / **BELOW** aspect | Frame-diff shows no popping spikes. The videos are 9:16 (720x1280) because the movie writer used the 1080x1920 project viewport, not 19:9. Fix in §5.5. 19:9 walk-path stills (540x1140) are OK. |
| F | Grass / bush / flower bend from `pet_pos_ws` | **MATCHED** for tufts, fg plants, bushes; **BELOW** for flower-bed flowers | The bed flowers are 遊程's meshes and have no bend yet (§5.4). Props wobble via 遊程's prop_bump (hits are in the walk logs). |
| G | Hybrid shadows, Low | **MATCHED** hero / **BELOW by 1 draw** walking | Hero: 139 draws / 37.3k prims. Walk average: 146 (includes ~6 HUD draws). Trade in §5.6. |
| S | Sky → golden haze | **MATCHED** | `sky_v69` re-grade, clouds kept. Haze glow follows the cloud field. |
| SS | Soft natural shadows (Kurt 11:22) | **MATCHED** | Height-proportional feather, footprint contact AO, blue-violet interiors at 64→78% brightness (texture still reads), live blur/angular. See `shadow_hard_vs_soft.png`. |
| PL | Small point lights lighting nearby ground (night) | **BELOW** | The lamp pools light on the ground. String lights and window glow read as emitters, but their ground pools are weak (night capture). Next step: window radius 80→110, energy ×1.4; one string-light omni at the mid-span, radius 120. Still within 8 lights per mesh. |
| PF | Low ≤145 draws / 68k prims / 60 fps | Hero OK, walking 146 (+1) | Note10+ fps is **not measured**. PC numbers are in §3. |

**Visual match to concept: ~85%** (v6.8 was ~78%). The remaining gaps are night ground pools, 19:9 movies, and flower-bed bend.

## 2. Per-object technique (one material, one method)
| Object | Technique | Why |
|---|---|---|
| Tree crowns (front/back) | Leaf-spray alpha cards, dark interior cards, no spheres | Spheres read as balls. Cards give a ragged silhouette and shadow. |
| Back trees bL/bR | Grooved trunk + sprays (voxel dome hidden) | The dome was the "ball" in phone high_1. |
| Bushes | Serrated clump cards, `pet_push` (push 4, r1 36), per-instance cloud | Mounds bend as a whole and pick up cloud shade. |
| Lawn tufts | `tuft` shader, push 7, wind + cloud | Cheap per-vertex bend, tips move most. |
| Fg plants | `fg_plant`, push 9 per-vertex from foot, live shadow caster | Biggest on screen, so it gets a real shadow. |
| Ground shadow | Baked from real geometry: height ray-march, σ=0.5+0.03·d, footprint AO, blue-violet tint | Soft edges at no runtime cost, shaped by the actual casters. |
| Ground dapple | `ground_dapple` + shared cloud, fleck 0.17 | Moving light without realtime cost. |
| Props / pet | Realtime 1024 ortho atlas (hybrid), blur 2.0 | They move, so their shadow must move with them. |
| Shafts | Additive cards on SUN_TO, cloud-gated | Point the right way, breathe with the clouds. |
| Sky | Painted dome `sky_v69` | Golden haze from the concept. |
| Night lights | 7 omnis (art/lights.json) + emissive bulbs | Mobile limit of 8 lights per mesh. |

## 3. Counts / perf (PC RTX 4060 Laptop, Godot Mobile renderer, 540x1140, round r2)
| Mode | Hero draws / prims | Walk avg draws | GPU ms | Uncapped fps |
|---|---|---|---|---|
| Low baked-only | 126 / 36,266 | 132 | 0.375 | 1221 |
| Low hybrid (soft) | 139 / 37,260 | 146 | 0.555 | 943 |
| Low hybrid hard | n/a | 146 | 0.555 | 918 |
| High soft | 200 / 42,196 | 207 | 0.791 | 760 |
| High hard | n/a | 207 | 0.789 | 765 |
| High HYBRID=0 | n/a | 207 | 0.842 | 740 |
| Night | 182 / 42,160 | 189 | 0.732 | 798 |

- Soft vs hard: about 0 GPU cost.
- Hybrid vs baked-only on Low: +0.18 ms GPU (+48%), +13 draws. Compare against 16.6 ms at 60 fps; it must be confirmed on the Note10+.

## 4. Prop bump spec (data/prop_bump.json format), suggestions for 遊程
```json
"pot_s_fill": {
  "_doc": "Dense-fill small pot at (100,-30); same pot as pot_s but sits among bushes, so lighter push",
  "match": ["pot_S_100_-30"],
  "pivot_y": 0.0, "mass": 1.0, "radius": 7.0, "max_tilt_deg": 10.0,
  "stiffness": 70.0, "damping": 6.0, "max_push": 3.0,
  "residual_frac": 0.18, "angular_gain": 0.04, "linear_gain": 0.08
},
"mushrooms": {
  "_doc": "suggested: soft squash, no travel",
  "match": ["mushrooms"],
  "pivot_y": 0.0, "mass": 0.3, "radius": 5.0, "max_tilt_deg": 18.0,
  "stiffness": 90.0, "damping": 7.0, "max_push": 0.0,
  "residual_frac": 0.0, "angular_gain": 0.06, "linear_gain": 0.0
}
```
- **Plant bend (art side, shaders), same globals:**
  - `pet_pos_ws` (vec3, y = pet centre) and `pet_lag_ws` (spring copy, k 100, damping 9, fed in art_depth `_dynamics`).
  - push_r0 8, push_r1 30 (bush 36), y falloff 25–50.
  - push: tuft 7, fg_plant 9, clump 4.

## 5. Notes for 遊程 (copy-ready)
1. **Unhooked pot_S at (100,-30):**
   - Exact node path at runtime: `/root/Capture/@Node3D@63`. It is unnamed: the glb root is auto-named, so a prefix match can never hit it.
   - It is spawned by `capture.gd:758 _spawn_copy("pot_S", 100, -30, true, 1.0)`. The copy at (128,8) (line 750) has the same problem.
   - Fix: in `_spawn_copy`, add `inst.name = "%s_%d_%d" % [id, int(x), int(z)]` before `add_child`, which gives `pot_S_100_-30`. Then use the `pot_s_fill` entry above, or keep `match: ["pot_S"]`, which now also catches it.
   - If it wobbles, it must also be a live caster (add it to the hybrid set), or its baked shadow will not follow it.
2. **DirectionalLight / shadow values to copy into capture.gd:**
   - Low (hybrid):
     - `RenderingServer.directional_shadow_atlas_set_size(1024, false)`
     - `sun.shadow_enabled = true` (false at night)
     - `sun.directional_shadow_mode = SHADOW_ORTHOGONAL` (1 split)
     - `sun.directional_shadow_max_distance = 300`
     - `sun.shadow_blur = 2.0`
     - `sun.light_angular_distance = 0.6`
     - `sun.shadow_opacity = 0.55`
     - `soft_shadow_filter_quality.mobile` unchanged (project value)
     - Casters ON: pet, pot_S*, pot_L*, pot_R*, can*, jar*, CrateWood* (lids ride on the crate), fg plants. Every other GeometryInstance3D: `cast_shadow = OFF` on Low (the bake covers them).
   - High: `shadow_blur = 2.2`, `light_angular_distance = 0.9`, `shadow_opacity = 0.55`. Atlas, mode and distance stay as in your v6.8 settings.
   - Shadow colour: the baked shadows are tinted blue-violet (0.90, 0.95, 1.16) at 64→78% brightness.
     - For the live shadows to match, suggest ambient_light_color ≈ (0.62, 0.66, 0.86) and ambient energy +0.05 over v6.8.
     - This ambient change is **untested**; the art layer did not change the Environment.
   - Today the art layer applies all of this as a preview in `art_depth._hybrid_shadow()`. `HD2D_HYBRID=0` turns it off. Once your capture.gd sets these values, delete that function.
3. **Bake:** DappleCaster must never be visible in bake passes; it caused the round blobs. The art layer hides it in bake mode.
4. **Flower-bed flowers:** not bending. Add `pet_push()` from `shaders/tuft.gdshader` to the bed flower material, or swap them to the tuft shader.
5. **19:9 movies:** `--write-movie` ignores `--resolution`. Put an `override.cfg` next to project.godot with `display/window/size/viewport_width=1080` and `viewport_height=2280` for movie runs only.
6. **Low walking is at 146 draws (+1):** options are fg-plant live caster off (−1) or jar caster off (−1). My pick: jar off, because the jar is tiny and its baked contact AO is enough.
7. **art/lights.json:**
   - Lanterns 1/3/5 radius 130, night energy 0.55; lanterns 2/4 removed.
   - Lamp 95, window 80, side window 64.
   - Still BELOW on ground pools; see PL in §1.
