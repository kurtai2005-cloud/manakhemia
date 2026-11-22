extends RefCounted
## Root resource loader for frozen 675 bytes.
## Reads res://hd2d_stage/, which is a symlink map created by
## tools/stage_hd2d_assets.sh. Does not read or write godot_hd2d_v6.
## A missing stage is a failed load. There is no byte-copy fallback.

const STAGE_ROOT := "res://hd2d_stage/"
const COTTAGE := STAGE_ROOT + "meshes/cottage.glb"


static func staged_path(pilot_res: String) -> String:
	var path := str(pilot_res)
	if path.begins_with("res://art/"):
		return STAGE_ROOT + path.trim_prefix("res://art/")
	if path.begins_with("res://godot_hd2d_v6/art/"):
		return STAGE_ROOT + path.trim_prefix("res://godot_hd2d_v6/art/")
	return path


static func load_texture(pilot_res: String) -> Texture2D:
	var staged := staged_path(pilot_res)
	var loaded: Variant = load(staged)
	return loaded if loaded is Texture2D else null


static func load_cottage() -> PackedScene:
	var loaded: Variant = load(COTTAGE)
	return loaded if loaded is PackedScene else null
