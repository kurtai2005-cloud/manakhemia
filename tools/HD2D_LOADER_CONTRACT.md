# Root loader contract

This is the file contract for the art owner. Root code owns the loader. The art owner owns the bytes. This slice does not place an interior, does not lock room or slot coordinates, and does not treat the engineering stand as the official exterior anchor.

## What the root project can load

Godot ignores `res://godot_hd2d_v6/` because that folder has its own `project.godot`. `load()` of those paths fails even though the files are on disk. The root import path is `res://hd2d_stage/`, a symlink map built by `tools/stage_hd2d_assets.sh`. The symlinks point at the frozen files. The script does not copy or edit them.

Run the stager, then import the root project once:

```
tools/stage_hd2d_assets.sh
godot --headless --path . --import --quit
```

After that import:

- `res://hd2d_stage/pet/r4/<frame>.png` loads as `CompressedTexture2D`.
- `res://hd2d_stage/meshes/cottage.glb` loads as `PackedScene`. Its import setting `gltf/embedded_image_handling` is `Embed as Uncompressed` (3), so the importer keeps the glb images inside the scene and does not write sibling pngs.

`scripts/hd2d_assets.gd` is the only loader. A missing stage returns null. It does not decode PNG bytes and it does not instance `capture.tscn`.

The 675 cottage scene is loaded for measurement only. The live garden keeps the existing H1 cottage, the closed door, and the existing footprint colliders. This slice does not hide that cottage or drop a second one into the garden.

Shaders, `art_depth.gd`, and `capture.gd` are not staged. Importing them would not reproduce the accepted exterior, because that look is built by the pilot scene at runtime. Doing that here would be a second runtime. See the options at the bottom if a full exterior mount is required later.

## Units and the pet

1 world unit equals 1 art pixel for the pet frames only. Do not convert furniture pixel sizes into world units.

Pet frames are 64×64. The coat node sits at local `(0, 29, 0)` with texture offset `(0, 2)`, so the sole is at world y=0. Ground y stays 0. The Walker origin stays the feet.

The cottage glb has no node translation, rotation, or scale. Its mesh stays in the file's local bounds (about x −35.5..35.5, y 0..142, z −26..26). The pilot places that node at `(82.5, 0, −72)`, yaw 0, scale 1. The root game's visible cottage is a different transform and is not this contract.

## Exterior door

Measured 675 threshold, cottage at `(82.5, 0, −72)`: world `(94, 0, −50)`. The front is a closed recess, not a passage. Outward is +Z. The root footprint still blocks `z <= −36` at the door for radius 10. Do not shrink that collider and do not move the cottage to make a test pass.

`(94, 0, −29.5)` is an engineering test point, not an art-locked anchor. The baked root navigation mesh, with the existing agent radius 12 and cell size 4, ends at z=−28. The test point is off that mesh. The agent can path to the closest on-mesh point and then stops up to `target_desired_distance` (6) short of it. The official exterior anchor stays unset until a measured on-mesh path and a positive clearance from z=−36 are accepted as the anchor. This slice does not write either number into art data.

Entering the house is the existing cut. The pet does not walk through the door.

## Future room-1 pack

The owner is making an art-only shell, six slot volumes, and furniture volumes. Not thirteen finished items. Room size, camera, and slot coordinates are candidates. The loader will not read a coordinate as locked.

Deliver one folder of files. Do not put a `project.godot` inside it. The root will symlink that folder under `res://hd2d_stage/room1/` the same way it stages the pet and the cottage.

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

## If the full 675 exterior must be the live scene

That is a larger choice than this loader. The frozen files stay as they are until one of these is chosen:

1. Keep the stage as the resource map and keep the current H1 garden as the live scene. This is the current choice.
2. Hide the H1 cottage and instance the staged glb with root materials only. That is not the accepted 675 exterior, because the depth, ground, and lighting stay in `art_depth.gd`.
3. Stop ignoring `godot_hd2d_v6/` by removing or renaming its `project.godot`, or by running `capture.tscn` as the scene. That edits the pilot project boundary or starts a second runtime. It is not done here.
