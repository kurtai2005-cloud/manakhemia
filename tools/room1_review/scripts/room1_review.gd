extends Node
## Standalone room1 review. Does not load Main, Sim, or the save.
## Does not read locked:false coordinates into the live garden.
## shell.glb.json "path" is an old absolute path and is never opened.

const SHELL := "res://hd2d_stage/room1/shell.glb"
const PACK := "res://hd2d_stage/room1/pack.json"
const SHELL_META := "res://hd2d_stage/room1/data/shell.glb.json"
const PET := "res://pet/pet_tuanrong_radiant_front_idle_01.png"
const SLOT_KEYS: PackedStringArray = ["bed", "rug", "table", "lamp", "wall", "window"]

## art_notes.json hero_after_20261122_0938. Candidate only.
const FULL_NAME := "hero_after_20261122_0938"
const FULL_EYE := Vector3(-55, 48, 400)
const FULL_TARGET := Vector3(10, 40, -20)
const FULL_VFOV := 46.0
## art_notes.json pet_scale_19x9. Candidate close-up, not a hand tune.
const CLOSE_NAME := "pet_scale_19x9"
const CLOSE_EYE := Vector3(18, 42, 130)
const CLOSE_TARGET := Vector3(10, 22, -14)
const CLOSE_VFOV := 44.0

## Day and night numbers copied from frozen capture.gd so this review
## uses that Mobile light set. They are not a new indoor lock.
const SUN_TRAVEL := Vector3(0.645, -0.616, 0.453)
const FILL_TRAVEL := Vector3(0.2005, -0.1203, -0.9723)

var view: SubViewport
var cam: Camera3D
var sun: DirectionalLight3D
var fill: DirectionalLight3D
var env: Environment
var banner: Label
var info: Dictionary = {}
var _built := false


func _ready() -> void:
	if OS.get_environment("ROOM1_CAPTURE") == "1":
		return
	var err := build()
	if err != "":
		push_error(err)


func build() -> String:
	if _built:
		return ""
	var pack_err := _load_pack()
	if pack_err != "":
		return pack_err
	_make_view()
	var shell_err := _load_shell()
	if shell_err != "":
		return shell_err
	var pet_err := _load_pet()
	if pet_err != "":
		return pet_err
	_load_collision()
	_note_ignored_meta()
	view.size = Vector2i(1080, 2280)
	if view.size.x != 1080 or view.size.y != 2280:
		return "room1 viewport stayed %s" % view.size
	apply_shot(shot_plan()[0])
	_built = true
	return ""


func shot_plan() -> Array:
	return [
		{"id": "day_fullroom", "file": "day_fullroom.png", "night": false, "camera": FULL_NAME, "eye": [FULL_EYE.x, FULL_EYE.y, FULL_EYE.z], "target": [FULL_TARGET.x, FULL_TARGET.y, FULL_TARGET.z], "vfov": FULL_VFOV},
		{"id": "night_fullroom", "file": "night_fullroom.png", "night": true, "camera": FULL_NAME, "eye": [FULL_EYE.x, FULL_EYE.y, FULL_EYE.z], "target": [FULL_TARGET.x, FULL_TARGET.y, FULL_TARGET.z], "vfov": FULL_VFOV},
		{"id": "day_closeup", "file": "day_closeup.png", "night": false, "camera": CLOSE_NAME, "eye": [CLOSE_EYE.x, CLOSE_EYE.y, CLOSE_EYE.z], "target": [CLOSE_TARGET.x, CLOSE_TARGET.y, CLOSE_TARGET.z], "vfov": CLOSE_VFOV},
		{"id": "night_closeup", "file": "night_closeup.png", "night": true, "camera": CLOSE_NAME, "eye": [CLOSE_EYE.x, CLOSE_EYE.y, CLOSE_EYE.z], "target": [CLOSE_TARGET.x, CLOSE_TARGET.y, CLOSE_TARGET.z], "vfov": CLOSE_VFOV},
	]


func apply_shot(shot: Dictionary) -> void:
	var eye := _vec3(shot["eye"])
	var target := _vec3(shot["target"])
	cam.keep_aspect = Camera3D.KEEP_HEIGHT
	cam.fov = float(shot["vfov"])
	cam.near = 2.0
	cam.far = 900.0
	cam.look_at_from_position(eye, target, Vector3.UP)
	cam.current = true
	_apply_day(bool(shot["night"]))
	var when := "night" if bool(shot["night"]) else "day"
	banner.text = "REVIEW locked:false  not integrated  %s  %s  vfov %s" % [when, str(shot["camera"]), str(shot["vfov"])]


func grab_image() -> Image:
	if view == null:
		return null
	var tex := view.get_texture()
	if tex == null:
		return null
	return tex.get_image()


func viewport_size() -> Vector2i:
	if view == null:
		return Vector2i.ZERO
	return view.size


func _make_view() -> void:
	var layer := CanvasLayer.new()
	layer.name = "ReviewLayer"
	add_child(layer)
	var host := SubViewportContainer.new()
	host.name = "ReviewHost"
	host.set_anchors_preset(Control.PRESET_FULL_RECT)
	host.stretch = false
	host.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(host)
	view = SubViewport.new()
	view.name = "Room1Viewport"
	view.size = Vector2i(1080, 2280)
	view.own_world_3d = true
	view.transparent_bg = false
	view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	view.handle_input_locally = false
	host.add_child(view)
	env = Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ssao_enabled = false
	env.glow_enabled = false
	env.fog_enabled = false
	env.volumetric_fog_enabled = false
	var world := WorldEnvironment.new()
	world.name = "ReviewEnvironment"
	world.environment = env
	view.add_child(world)
	sun = DirectionalLight3D.new()
	sun.name = "ReviewSun"
	sun.shadow_enabled = true
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	sun.directional_shadow_max_distance = 560.0
	sun.shadow_bias = 0.4
	sun.shadow_normal_bias = 1.0
	sun.shadow_blur = 0.2
	sun.basis = Basis.looking_at(SUN_TRAVEL.normalized(), Vector3.UP)
	view.add_child(sun)
	fill = DirectionalLight3D.new()
	fill.name = "ReviewFill"
	fill.shadow_enabled = false
	fill.basis = Basis.looking_at(FILL_TRAVEL.normalized(), Vector3.UP)
	view.add_child(fill)
	cam = Camera3D.new()
	cam.name = "ReviewCamera"
	view.add_child(cam)
	var banner_layer := CanvasLayer.new()
	banner_layer.name = "ReviewBanner"
	view.add_child(banner_layer)
	var bar := ColorRect.new()
	bar.color = Color(0, 0, 0, 0.55)
	bar.position = Vector2(0, 2228)
	bar.size = Vector2(1080, 52)
	banner_layer.add_child(bar)
	banner = Label.new()
	banner.position = Vector2(16, 2236)
	banner.add_theme_font_size_override("font_size", 22)
	banner.add_theme_color_override("font_color", Color(1, 1, 1, 1))
	banner_layer.add_child(banner)


func _mesh_count(node: Node) -> int:
	var count := 0
	if node is MeshInstance3D:
		count += 1
	for child in node.get_children():
		count += _mesh_count(child)
	return count


func _vec3(value: Variant) -> Vector3:
	if value is Vector3:
		return value
	var row: Array = value
	return Vector3(float(row[0]), float(row[1]), float(row[2]))


func _apply_day(night: bool) -> void:
	if night:
		sun.light_energy = 0.12
		sun.light_color = Color(0.55, 0.62, 0.85)
		fill.light_energy = 0.0
		env.ambient_light_color = Color("4a5a90")
		env.ambient_light_energy = 0.35
		env.background_color = Color(0.18, 0.20, 0.35, 1.0)
	else:
		sun.light_energy = 2.6
		sun.light_color = Color(1.0, 0.84, 0.68)
		fill.light_energy = 0.22
		fill.light_color = Color(1.0, 0.86, 0.68)
		env.ambient_light_color = Color(0.52, 0.58, 0.68)
		env.ambient_light_energy = 0.26
		env.background_color = Color(1.0, 0.84, 0.54, 1.0)


func _load_pack() -> String:
	if not FileAccess.file_exists(PACK):
		return "room1 pack.json missing at " + PACK
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(PACK))
	if not parsed is Dictionary:
		return "room1 pack.json did not parse"
	var pack: Dictionary = parsed
	var locked := _locked_rows(pack)
	for row in locked:
		if bool(row["value"]):
			return "room1 pack has locked:true at " + str(row["at"])
	var keys: PackedStringArray = []
	for slot in pack.get("slots", []):
		if slot is Dictionary:
			keys.append(str(slot.get("key", "")))
	if keys != SLOT_KEYS:
		return "room1 slot keys are %s" % [str(keys)]
	var collision: Array = pack.get("collision", [])
	for item in collision:
		if not item is Dictionary:
			return "room1 collision row is not an object"
		var aabb: Array = item.get("aabb", [])
		if aabb.size() != 6:
			return "room1 collision aabb is not 6 numbers: " + str(item.get("name", ""))
		if float(aabb[3]) <= 0.0 or float(aabb[4]) <= 0.0 or float(aabb[5]) <= 0.0:
			return "room1 collision size is not positive: " + str(item.get("name", ""))
	var walk: Dictionary = pack.get("walkable", {})
	var occ: Dictionary = pack.get("occlusion", {})
	if str(walk.get("mesh", "")) != "" or str(occ.get("mesh", "")) != "":
		return "room1 walkable or occlusion mesh is set; this fixture will not invent a walk mesh"
	info = {
		"protocol": "room1_review_fixture_v1",
		"review_only": true,
		"integrated": false,
		"save_written": false,
		"locked_true_count": 0,
		"locked_flags": locked.size(),
		"shell_loaded_from": SHELL,
		"pack_loaded_from": PACK,
		"transform_applied": false,
		"slot_keys": ["bed", "rug", "table", "lamp", "wall", "window"],
		"slots": pack.get("slots", []),
		"collision": collision,
		"walkable_mesh": "",
		"occlusion_mesh": "",
		"door_anchor_applied": false,
		"camera_locked": false,
		"rights": "unverified",
		"rights_note": "RIGHTS.md says commercial use is not claimed. Unknown rights block release.",
		"mobile_acceptance": false,
		"pixel_compared": false,
		"care_built": false,
	}
	return ""


func _locked_rows(pack: Dictionary) -> Array:
	var rows: Array = []
	if pack.get("transform", {}) is Dictionary:
		rows.append({"at": "transform", "value": bool(pack["transform"].get("locked", false))})
	for slot in pack.get("slots", []):
		if slot is Dictionary:
			rows.append({"at": "slot:" + str(slot.get("key", "")), "value": bool(slot.get("locked", false))})
	for key in ["walkable", "occlusion", "door_anchor"]:
		var block: Variant = pack.get(key, {})
		if block is Dictionary:
			rows.append({"at": key, "value": bool(block.get("locked", false))})
	return rows


func _load_shell() -> String:
	if not FileAccess.file_exists(SHELL):
		return "room1 shell.glb missing at " + SHELL
	var packed := load(SHELL) as PackedScene
	if packed == null:
		return "room1 shell.glb failed to load as a scene: " + SHELL
	var node := packed.instantiate()
	info["shell_imported_root"] = str(node.name)
	node.name = "Shell"
	view.add_child(node)
	view.size = Vector2i(1080, 2280)
	var meshes := _mesh_count(node)
	info["shell_mesh_count"] = meshes
	if meshes < 1:
		return "room1 shell loaded with no meshes"
	return ""


func _load_pet() -> String:
	if not FileAccess.file_exists(PET):
		return "room1 review pet frame missing at " + PET
	var tex := load(PET) as Texture2D
	if tex == null:
		return "room1 review pet frame failed to load: " + PET
	var sprite := Sprite3D.new()
	sprite.name = "ReviewPet"
	sprite.texture = tex
	sprite.pixel_size = 1.0
	sprite.centered = true
	sprite.offset = Vector2(0, 2)
	sprite.position = Vector3(0, 29, 8)
	sprite.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
	sprite.shaded = true
	sprite.double_sided = true
	sprite.alpha_cut = SpriteBase3D.ALPHA_CUT_DISCARD
	sprite.alpha_scissor_threshold = 0.5
	sprite.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	sprite.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	view.add_child(sprite)
	var shadow := MeshInstance3D.new()
	shadow.name = "ReviewShadow"
	var quad := QuadMesh.new()
	quad.size = Vector2(36, 18)
	shadow.mesh = quad
	shadow.position = Vector3(0, 0.25, 8)
	shadow.basis = Basis(Vector3(1, 0, 0), Vector3(0, 0, -1), Vector3(0, 1, 0))
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.albedo_color = Color(0, 0, 0, 0.35)
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	shadow.material_override = mat
	shadow.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	view.add_child(shadow)
	info["pet"] = {
		"enabled": true,
		"review_only": true,
		"path": PET,
		"node_y": 29.0,
		"offset_y": 2.0,
		"pixel_size": 1.0,
		"feet_world_y": 0.0,
		"shadow_y": 0.25,
		"pos_xz": [0, 8],
	}
	return ""


func _load_collision() -> void:
	for item in info.get("collision", []):
		var aabb: Array = item["aabb"]
		var size := Vector3(float(aabb[3]), float(aabb[4]), float(aabb[5]))
		var origin := Vector3(float(aabb[0]), float(aabb[1]), float(aabb[2]))
		var box := BoxMesh.new()
		box.size = size
		var mi := MeshInstance3D.new()
		mi.name = "ReviewCollision_" + str(item.get("name", "box"))
		mi.mesh = box
		mi.position = origin + size * 0.5
		var mat := StandardMaterial3D.new()
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		mat.albedo_color = Color(0.25, 0.75, 1.0, 0.16)
		mat.cull_mode = BaseMaterial3D.CULL_DISABLED
		mi.material_override = mat
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		view.add_child(mi)


func _note_ignored_meta() -> void:
	info["shell_meta_present"] = FileAccess.file_exists(SHELL_META)
	info["shell_meta_path_ignored"] = true
	if not info["shell_meta_present"]:
		return
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(SHELL_META))
	if parsed is Dictionary:
		info["shell_meta_path_value"] = str(parsed.get("path", ""))
		info["shell_meta_path_followed"] = false
		var nodes: Variant = parsed.get("nodes", [])
		if nodes is Array and nodes.has("interior_room1"):
			info["shell_source_node"] = "interior_room1"
