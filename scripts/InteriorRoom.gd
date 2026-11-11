extends Node3D
class_name InteriorRoom
## 獨立 3D 室內：遊美 interior1 mesh（地板、後牆開窗、左右牆、窗夜光、門內面）。
## 尺寸／貼圖路徑由 data/m1d.json 同 art/garden3d/H1/interior/ 驅動。

const ART := "res://art/garden3d/H1/interior/"

var cfg: Dictionary = {}
var size := Vector3(160, 120, 128)
var tile_wu := 64.0
var texel_wu := 1.0
var furniture_root: Node3D
var nav_region: NavigationRegion3D
var door_pivot: Node3D
var door_mesh: MeshInstance3D
var window_mat: StandardMaterial3D
var _mats: Array = []
var _built := false
var _window_light: OmniLight3D


func setup() -> void:
	if _built:
		return
	_built = true
	name = "InteriorRoom"
	cfg = _load_cfg()
	var ic: Dictionary = cfg.get("interior", {})
	var orig: Variant = ic.get("origin", [0, 0, -900])
	if orig is Array and orig.size() >= 3:
		position = Vector3(float(orig[0]), float(orig[1]), float(orig[2]))
	var sz: Variant = ic.get("size_wu", [160, 120, 128])
	if sz is Array and sz.size() >= 3:
		size = Vector3(float(sz[0]), float(sz[1]), float(sz[2]))
	tile_wu = float(ic.get("tile_wu", 64))
	texel_wu = float(ic.get("texel_wu", 1.0))
	visible = false
	_build_from_art()
	_build_nav()
	_build_window_light()
	furniture_root = Node3D.new()
	furniture_root.name = "InteriorFurniture"
	add_child(furniture_root)
	apply_tier()


func _load_cfg() -> Dictionary:
	if Engine.get_main_loop() and Engine.get_main_loop().root:
		var gd: Node = Engine.get_main_loop().root.get_node_or_null("GameData")
		if gd and gd.get("m1d") is Dictionary and not (gd.get("m1d") as Dictionary).is_empty():
			return gd.get("m1d")
	if FileAccess.file_exists("res://data/m1d.json"):
		var raw := FileAccess.get_file_as_string("res://data/m1d.json")
		var p: Variant = JSON.parse_string(raw)
		if p is Dictionary:
			return p
	return {}


func interior_cfg() -> Dictionary:
	return cfg.get("interior", {})


func slot_pos(sl: String) -> Vector3:
	var slots: Dictionary = interior_cfg().get("slots", {})
	var a: Variant = slots.get(sl, [0, 0, 0])
	if a is Array and a.size() >= 3:
		return Vector3(float(a[0]), float(a[1]), float(a[2]))
	return Vector3.ZERO


func pet_enter_pos() -> Vector3:
	var a: Variant = interior_cfg().get("pet_enter", [48, 0, 8])
	if a is Array and a.size() >= 3:
		return to_global(Vector3(float(a[0]), float(a[1]), float(a[2])))
	return to_global(Vector3(size.x * 0.3, 0, 8))


func look_target() -> Vector3:
	var a: Variant = interior_cfg().get("camera", {}).get("look", [0, 48, -16])
	if a is Array and a.size() >= 3:
		return to_global(Vector3(float(a[0]), float(a[1]), float(a[2])))
	return to_global(Vector3(0, 48, -16))


func cam_pitch() -> float:
	return float(interior_cfg().get("camera", {}).get("pitchDeg", 30))


func cam_dist() -> float:
	return float(interior_cfg().get("camera", {}).get("dist", 300))


func cam_yaw() -> float:
	return float(interior_cfg().get("camera", {}).get("yawDeg", 26))


func door_world() -> Vector3:
	var a: Variant = interior_cfg().get("door", {}).get("local", [80, 0, 0])
	if a is Array and a.size() >= 3:
		return to_global(Vector3(float(a[0]), float(a[1]), float(a[2])))
	return to_global(Vector3(size.x * 0.5, 0, 0))


func fade_sec() -> float:
	return float(interior_cfg().get("fade_sec", 0.4))


func dolly_sec() -> float:
	return float(interior_cfg().get("dolly_sec", 0.45))


func door_open_sec() -> float:
	return float(interior_cfg().get("door_open_ms", 400)) / 1000.0


func door_close_sec() -> float:
	return float(interior_cfg().get("door_close_ms", 400)) / 1000.0


func room_bounds_local() -> AABB:
	return AABB(Vector3(-size.x * 0.5, 0, -size.z * 0.5), size)


func set_door_open(weight: float) -> void:
	if door_pivot == null:
		return
	# 0 = 關（貼牆），1 = 開（轉入房約 85°）
	door_pivot.rotation_degrees.y = lerpf(0.0, -85.0, clampf(weight, 0.0, 1.0))


func _build_from_art() -> void:
	var ic := interior_cfg()
	var obj_path := str(ic.get("objects", ART + "objects.json"))
	var doc: Dictionary = GardenLoader.load_json(obj_path) if obj_path != "" else {}
	var objs: Array = doc.get("objects", [])
	var root := str(ic.get("root", ART))
	if not root.ends_with("/"):
		root += "/"
	var unlit := true
	if Engine.get_main_loop() and Engine.get_main_loop().root:
		var qs: Node = Engine.get_main_loop().root.get_node_or_null("QualitySettings")
		if qs and qs.has_method("is_low"):
			unlit = bool(qs.is_low())
	for o in objs:
		if not (o is Dictionary):
			continue
		if str(o.get("type", "mesh")) != "mesh":
			continue
		var rel := str(o.get("mesh", ""))
		if rel == "":
			continue
		var mesh_doc: Dictionary = GardenLoader.load_json(root + rel)
		if mesh_doc.is_empty():
			continue
		var tex_rel := str(mesh_doc.get("texture", ""))
		var tex: Texture2D = load(root + tex_rel) if tex_rel != "" else null
		var em: Texture2D = null
		var em_rel := str(mesh_doc.get("emissive", tex_rel.replace(".png", "_emissive.png") if tex_rel != "" else ""))
		if em_rel != "" and ResourceLoader.exists(root + em_rel):
			em = load(root + em_rel)
		var mat := GardenLoader.make_mat(tex, unlit, float(mesh_doc.get("alphaTest", 0.5)), em)
		if unlit:
			# 低檔日間調色（ENGINE low albedo_mul_day）
			mat.albedo_color = Color(1.0, 0.965, 0.91)
		var mi := MeshInstance3D.new()
		var oid := str(o.get("id", "mesh"))
		mi.name = oid
		mi.mesh = GardenLoader.mesh_from_json(mesh_doc, true)
		var thick := float(ic.get("wall_thickness_wu", 3))
		if oid in ["floor", "wall_back", "wall_L", "wall_R"] and thick > 0.0:
			mi.mesh = GardenLoader.solidify_mesh(mi.mesh as ArrayMesh, thick)
		mat.cull_mode = BaseMaterial3D.CULL_DISABLED
		mi.material_override = mat
		mi.position = Vector3(float(o.get("x", 0)), float(o.get("y", 0)), float(o.get("z", 0)))
		mi.rotation_degrees.y = float(o.get("yawDeg", 0))
		if not bool(o.get("castShadow", true)):
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_mats.append(mat)
		if oid == "window":
			window_mat = mat
		if oid == "door":
			door_pivot = Node3D.new()
			door_pivot.name = "DoorPivot"
			# 鉸鏈喺門近鏡頭嗰邊（z=+33, x=79.6）
			door_pivot.position = Vector3(79.6, 0, 33.0)
			add_child(door_pivot)
			door_mesh = mi
			mi.position = Vector3(-79.6, 0, -33.0)
			door_pivot.add_child(mi)
			set_door_open(0.0)
		else:
			add_child(mi)


func _build_window_light() -> void:
	_window_light = OmniLight3D.new()
	_window_light.name = "WindowGlow"
	_window_light.position = Vector3(0, 76, -62)
	_window_light.light_color = Color(1.0, 0.784, 0.439)
	_window_light.light_energy = 0.0
	_window_light.omni_range = 90.0
	_window_light.shadow_enabled = false
	add_child(_window_light)


func apply_tier() -> void:
	var night := false
	var low := true
	if Engine.get_main_loop() and Engine.get_main_loop().root:
		var qs: Node = Engine.get_main_loop().root.get_node_or_null("QualitySettings")
		if qs and qs.has_method("is_low"):
			low = bool(qs.is_low())
		var main: Node = Engine.get_main_loop().root.get_node_or_null("Main")
		if main == null:
			var group: Node = Engine.get_main_loop().root.get_tree().get_first_node_in_group("glimmer_main") if Engine.get_main_loop().root.get_tree() else null
			main = group
		if main and main.get("_tod") != null:
			night = str(main.get("_tod")) == "night"
	if window_mat:
		window_mat.emission_energy_multiplier = (0.6 if low else 0.9) if night else 0.0
	if _window_light:
		_window_light.light_energy = (0.6 if low else 0.9) if night else 0.0
	for mat in _mats:
		if mat is StandardMaterial3D:
			var sm := mat as StandardMaterial3D
			if low:
				sm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
				sm.albedo_color = Color(0.416, 0.376, 0.533) if night else Color(1.0, 0.965, 0.91)
			else:
				sm.shading_mode = BaseMaterial3D.SHADING_MODE_PER_PIXEL
				sm.albedo_color = Color.WHITE


func _build_nav() -> void:
	nav_region = NavigationRegion3D.new()
	nav_region.name = "InteriorNav"
	add_child(nav_region)
	var nm := NavigationMesh.new()
	nm.agent_radius = 8.0
	nm.agent_height = 2.0
	nm.agent_max_climb = 2.0
	nm.agent_max_slope = 45.0
	nm.cell_size = 4.0
	nm.cell_height = 1.0
	nm.border_size = 2.0
	var src := NavigationMeshSourceGeometryData3D.new()
	var margin := float(interior_cfg().get("walk", {}).get("margin", 12))
	var x0 := -size.x * 0.5 + margin
	var x1 := size.x * 0.5 - margin
	var z0 := -size.z * 0.5 + margin
	var z1 := size.z * 0.5 - margin
	var faces := PackedVector3Array([
		Vector3(x0, 0, z0), Vector3(x1, 0, z1), Vector3(x1, 0, z0),
		Vector3(x0, 0, z0), Vector3(x0, 0, z1), Vector3(x1, 0, z1),
	])
	src.add_faces(faces, Transform3D.IDENTITY)
	NavigationServer3D.bake_from_source_geometry_data(nm, src)
	nav_region.navigation_mesh = nm


func walk_point(rng: RandomNumberGenerator) -> Vector3:
	var margin := float(interior_cfg().get("walk", {}).get("margin", 12))
	var x := rng.randf_range(-size.x * 0.5 + margin, size.x * 0.5 - margin)
	var z := rng.randf_range(-size.z * 0.5 + margin, size.z * 0.5 - margin)
	return to_global(Vector3(x, 0, z))
