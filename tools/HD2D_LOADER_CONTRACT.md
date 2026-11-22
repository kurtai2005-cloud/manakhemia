# Root loader contract

This is the file contract for the art owner. Root code owns the loader. The art owner owns the bytes. This slice does not place an interior, does not lock room or slot coordinates, and does not treat the engineering stand as the official exterior anchor.

## What the root project can load

Godot ignores `res://godot_hd2d_v6/` because that folder has its own `project.godot`. `load()` of those paths fails even though the files are on disk. The root import path is `res://hd2d_stage/`. `tools/stage_hd2d_assets.py` (also `tools/stage_hd2d_assets.sh`) copies regular files from `godot_hd2d_v6/art/` into that folder after each source matches `tools/hd2d_stage_prerequisites.sha256`. The copy is a normal file. The script does not create a symlink, junction, or hard link, and it does not edit the frozen source. Windows does not need `core.symlinks` or Developer Mode.

Run the stager, then import the root project once:

```
tools/stage_hd2d_assets.sh
godot --headless --path . --import --quit
```

After that import:

- `res://hd2d_stage/pet/r4/<frame>.png` loads as `CompressedTexture2D`.
- `res://hd2d_stage/meshes/cottage.glb` loads as `PackedScene`. Its import setting `gltf/embedded_image_handling` is `Embed as Uncompressed` (3), so the importer keeps the glb images inside the scene and does not write sibling pngs.

`scripts/hd2d_assets.gd` loads the coat frames and the cottage measurement scene. A missing stage returns null. It does not decode PNG bytes and it does not instance `capture.tscn`.

The 675 cottage scene from that loader is for measurement only. The live garden keeps the existing H1 cottage, the closed door, and the existing footprint colliders. This slice does not hide that cottage or drop a second one into the garden.

Frozen originals stay in `godot_hd2d_v6/`. Nothing there is edited. `tools/stage_hd2d_assets.py` writes generated copies under `res://hd2d_stage/`:

- Byte copies: `textures/`, `shaders/`, `art/`, `data/prop_bump.json`, the 21 r4 PNGs, and `cottage.glb`. The hash matches the frozen file.
- Path-prefix script copies: `scenes/capture.gd`, `scenes/art_depth.gd`, `scenes/prop_bump.gd`, `gameplay/m1_walk_clip.gd`, `gameplay/m1_camera_policy.gd`, `gameplay/m1_ui_layout.gd`. The only text change is `res://` to `res://hd2d_stage/`. `tools/hd2d_generated_provenance.txt` records both hashes.
- Not a generated copy: `scripts/hd2d_exterior_host.gd`. That is the root lifecycle binding. It calls the visual build and `art_depth._process` for the comparison step. It does not call `_add_m1_care`, `_tick_play`, or `_tick_camera`.

One actor, one input, and one current camera: root `Main`, root `Walker`, root input. The generated pilot sprite stays hidden. There is one `Sim` and one `SaveSystem`. No `M1Care` node.

## Units and the pet

1 world unit equals 1 art pixel for the pet frames only. Do not convert furniture pixel sizes into world units.

Pet frames are 64×64. The coat node sits at local `(0, 29, 0)` with texture offset `(0, 2)` and `pixel_size` 1, so the sole is at world y=0. The low shadow uses `global_position.y + offset.y * pixel_size` (29 + 2 = 31) and still sits 0.25 above the ground. Ground y stays 0. The Walker origin stays the feet. Compare the coat, not the feet, with the pilot sprite.

The cottage glb has no node translation, rotation, or scale. Its mesh stays in the file's local bounds (about x −35.5..35.5, y 0..142, z −26..26). The pilot places that node at `(82.5, 0, −72)`, yaw 0, scale 1. The root game's visible cottage is a different transform and is not this contract.

## Exterior door

Measured 675 threshold, cottage at `(82.5, 0, −72)`: world `(94, 0, −50)`. The front is a closed recess, not a passage. Outward is +Z. The root footprint still blocks `z <= −36` at the door for radius 10. Do not shrink that collider and do not move the cottage to make a test pass.

Three different positions are in use. None of them is the official exterior anchor.

- Engineering candidate, off the baked mesh: `(94, 0, −29.5)`.
- Closest on-mesh point the agent is given: `(94, 0, −28)`. The mesh south edge is z=−28 with the existing agent radius 12 and cell size 4. The source polygon starts at z=−40.
- Walked stop: about `(94, 0, −22.5)`. `target_desired_distance` is 6, so the agent stops short of the on-mesh point. Clearance from this stop to the block line z=−36 is about 13.5 wu.

The off-mesh candidate is not the walked stop. The official exterior anchor stays unset. This slice does not write any of these numbers into art data.

Entering the house is the existing cut. The pet does not walk through the door.

## Future room-1 pack

The owner is making an art-only shell, six slot volumes, and furniture volumes. Not thirteen finished items. Room size, camera, and slot coordinates are candidates. The loader will not read a coordinate as locked.

Deliver one folder of regular files. Do not put a `project.godot` inside it. The root stager will copy that folder to `res://hd2d_stage/room1/` the same way it copies the pet frames and the cottage. Do not deliver symlinks.

`shell.glb`

- One scene. Y up. 1 world unit = 1 Godot unit.
- Ground contact at local y=0.
- No hidden scale. If the shell needs a transform, put it in `pack.json`, not in a second copy of the mesh.

`textures/`

- PNG files referenced by the glb. The root imports them as `CompressedTexture2D` with nearest filtering when they are shown as sprites. The glb may use its own materials.

`pack.json`

```json
{
  "unit": "wu",
  "transform": { "position": [0, 0, 0], "rotation_y_deg": 0, "scale": [1, 1, 1], "locked": false },
  "slots": [
    { "key": "bed" },
    { "key": "rug" },
    { "key": "table" },
    { "key": "lamp" },
    { "key": "wall" },
    { "key": "window" }
  ],
  "collision": [],
  "walkable": { "mesh": "", "locked": false },
  "occlusion": { "mesh": "", "locked": false },
  "door_anchor": { "threshold_local": [0, 0, 0], "outward": [0, 0, 1], "locked": false }
}
```

Fields the loader will accept, and what it will not invent:

- `slots[].key` must be exactly `bed`, `rug`, `table`, `lamp`, `wall`, `window`. Those are the save keys. Furniture ids stay the existing ids (`bed_leaf`, `bed_cloud`, `table_stump`, `table_round`, `wall_shelf`, `wall_frame`, `wall_shoes`, `rug_round`, `rug_leaf`, `win_curtain`, `win_star`, `lamp_mushroom`, `lamp_firefly`). One id per slot. No coordinates in the save.
- A slot may include `candidate_local` as `[x, y, z]`. This slice ignores it. A later slice may read it only when that slot also has `"locked": true`.
- `collision` is a list of `{ "name", "aabb": [x, y, z, w, h, d] }` or `{ "name", "mesh" }`. Volumes stay as authored. The loader will not shrink them.
- `walkable.mesh` is an optional mesh name inside the glb. The root does not walk on it until `"locked": true`.
- `occlusion.mesh` is an optional mesh name. The root does not hide the exterior with it in this slice.
- `door_anchor.locked` stays false until the owner says the threshold is final. The exterior door remains the closed 675 recess above. An interior door anchor does not replace it.
- `transform.locked` stays false while position and rotation are still candidates. The root will not move the live garden to this transform.

## Not in this slice

Care, offline catch-up, work, hunt, and family are unchanged root systems. The coat does not drive them. The interior room stays the existing placeholder. Renderer acceptance still needs a real Mobile run. This software-GL run is not that.

## Exterior candidate

`tools/stage_hd2d_assets.py` also copies `textures/`, `shaders/`, `art/`, and `data/prop_bump.json` into `res://hd2d_stage/`, and writes path-prefix copies of `capture.gd`, `art_depth.gd`, `prop_bump.gd`, and the three gameplay scripts those files preload. `tools/hd2d_generated_provenance.txt` records frozen and generated hashes. The only script change in those copies is the `res://` prefix. `scripts/hd2d_exterior_host.gd` is the lifecycle binding, not a generated copy. It does not call pilot care, walk, or the pilot camera loop.

Desktop flag: `renderer/rendering_method="gl_compatibility"`. Phone flag: `renderer/rendering_method.mobile="mobile"`. Rollback of the phone line is `tools/HD2D_RENDERER_ROLLBACK.txt`. A desktop GL run is not a Mobile result.

Five shader globals, same names and initial values as 675. `cloud_tex` points at the staged copy of `textures/tiles/cloud_shadow.png`.

| name | 675 initial value | meaning | who writes it each frame |
|---|---|---|---|
| `pet_pos_ws` | `(0, 0, 0)` | visual center, y mode `center` (coat or pilot sprite, not the feet) | `prop_bump.tick` |
| `pet_lag_ws` | `(0, -1000, 0)` | spring follow of that center; if the lag is still `(0, 0, 0)` it snaps to the center first. `k=100`, damping `9`, step `clamp(dt, 0, 0.05)` | `art_depth._dynamics` |
| `cloud_tex` | staged `cloud_shadow.png` | cloud field texture | not rewritten each frame; loaded once |
| `cloud_off` | `(0, 0)` | `(5.2, 3.9) * t`, and `t` grows by `clamp(dt, 0, 0.1)` | `art_depth._dynamics` |
| `cloud_amt` | `0.22` | `0` at night, otherwise `0.22` | `art_depth._dynamics` |

This is not the whole game and not Mobile acceptance. Room 1 stays `"locked": false` and is not read. No interior layout is added here. The official exterior anchor stays unset. The off-mesh candidate, the on-mesh goal, and the walked stop stay three different positions.

Same-view command. Portrait is 1080×2280 (19:9), not 1080×1920. Both processes use `--rendering-method mobile` and the same 20 steps at dt=1/60, including `art_depth._process` / `_follow_camera`. Neither side calls `_tick_camera`. `_follow_camera` moves cards with the camera. It does not move the camera. Record eye, target, and fov after those steps. Do not promise a pixel match.

Head `61ae7968817149d4c9a9c4e63af1b248cbcec80f`, one headless Mobile run, after the 20 follow steps: eye `(12, 193, 207.826858520508)`, target `(12, 58, -26)`, fov 50, `png_written` false. That is a state record, not a picture.

The root frame is a 1080×2280 SubViewport. The H1 window stays 390×844. The pilot frame is the window of a temporary 675 project copy set to 1080×2280. The frozen tree is not edited. Those are different render targets at the same size, so a later grab can still differ.

```
HD2D_COMPARE_OUT=<empty-dir> tools/run_hd2d_mobile_compare.sh
```
