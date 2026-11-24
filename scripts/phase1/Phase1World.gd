class_name Phase1World
extends Node
## 675-scale yards parented in the live exterior. A matching .glb replaces the fallback.

const LOOK := {
	"garden": Vector3(12, 58, -26),
	"zone_farm": Vector3(-190, 58, 48),
	"zone_workshop": Vector3(220, 58, -40),
	"prairie_edge": Vector3(-240, 58, -140),
}
const ANCHOR := {
	"garden": Vector3(0, 0, 8),
	"zone_farm": Vector3(-190, 0, 112),
	"zone_workshop": Vector3(236, 0, -6),
	"prairie_edge": Vector3(-200, 0, -88),
}
const OLD_SPAN := 256.0
const WOOD := "res://hd2d_stage/textures/tiles/wood_a.png"
const DIRT := "res://hd2d_stage/textures/tiles/dirt_a.png"
const BARK := "res://hd2d_stage/textures/tiles/bark_a.png"

var host: Node
var zones: Node3D
var _stove := Vector3(190, 0, -12)
var _post := Vector3(278, 0, -8)


func build(exterior: Node) -> void:
	host = exterior
	zones = Node3D.new()
	zones.name = "Phase1ZonesRoot"
	exterior.add_child(zones)
	for i in range(3):
		_spawn_prop("dirt_path_tile", "FarmPath_%d" % i, Vector3(-190, 0, 150 + i * 12), 0.0, _path_fallback)
	for i in range(10):
		_spawn_prop("garden_fence_seg", "Fence_%d" % i, Vector3(-261 + i * 18.0, 0, 96), 0.0, _fence_fallback)
	for i in range(4):
		_bed(i, Vector3(-244 + i * 36, 0, 124))
	_sign("SignFarm", "農圃", Vector3(-168, 0, 205), 1.0)
	var stove := _spawn_prop("outdoor_stove", "WorkOutdoorStove", _stove, 0.2, _stove_fallback, 1.9)
	_spot(stove, "stove", Vector3(42, 36, 32))
	var post := _spawn_prop("outdoor_post_rack", "WorkOutdoorPost", _post, -0.2, _post_fallback, 1.9)
	_spot(post, "post", Vector3(36, 46, 24))
	_spawn_prop("wood_crate", "ShopCrate", Vector3(262, 0, 16), 0.4, _crate_fallback, 1.6)
	_spawn_prop("garden_lantern", "ShopLantern", Vector3(168, 0, 10), 0.0, _lantern_fallback, 1.7)
	for i in range(6):
		_spawn_prop("dirt_path_tile", "ShopPath_%d" % i, Vector3(214, 0, 28 - i * 12), 0.0, _path_fallback)
		_spawn_prop("garden_fence_seg", "ShopFence_%d" % i, Vector3(150 + i * 18, 0, -48), 0.0, _fence_fallback)
	_sign("SignShop", "工坊", Vector3(214, 0, 36), 1.4)
	_dress_yard(Vector3(220, 0, -55), 8, 120.0)
	var flower_scales := [1.5, 1.8, 2.0, 1.4, 1.7, 1.9, 1.6, 2.0]
	for i in range(8):
		var fx := -280.0 + (i % 4) * 28.0
		var fz := -108.0 + int(i / 4) * 22.0
		_spawn_prop("stepping_stone", "Step_%d" % i, Vector3(-250 + i * 12, 0, -60 - i * 4), 0.2, _stone_fallback, 1.6)
		var flower := _spawn_prop("prairie_flower_clump", "Flower_%d" % i, Vector3(fx, 0, fz), 0.4, _flower_fallback, flower_scales[i])
		if i == 0:
			_spot(flower, "prairie", Vector3(18, 14, 18))
	for i in range(5):
		_spawn_prop("dirt_path_tile", "PrairiePath_%d" % i, Vector3(-210, 0, -40 - i * 12), 0.0, _path_fallback)
		_spawn_prop("garden_fence_seg", "PrairieFence_%d" % i, Vector3(-300 + i * 18, 0, -130), 0.0, _fence_fallback)
	_sign("SignPrairie", "草原", Vector3(-188, 0, -48), 1.4)
	_dress_yard(Vector3(-240, 0, -160), 10, 130.0)
	_extend_lawn()
	_seed_plots()
	_refresh_beds()


func look_for(zone_id: String) -> Vector3:
	return LOOK.get(zone_id, LOOK["garden"])


func anchor_for(zone_id: String) -> Vector3:
	return ANCHOR.get(zone_id, ANCHOR["garden"])


func span_ratio() -> float:
	var width := 220.0 - (-240.0)
	var depth := 48.0 - (-140.0)
	return (width * depth) / (90.0 * 70.0)


func tap_bed(index: int) -> String:
	return _tap_bed(index)


func stove_pos() -> Vector3:
	var node := prop_named("WorkOutdoorStove")
	return node.global_position if node else _stove


func post_pos() -> Vector3:
	var node := prop_named("WorkOutdoorPost")
	return node.global_position if node else _post


func prairie_pos() -> Vector3:
	var node := prop_named("Flower_0")
	return node.global_position if node else Vector3(16, 0, -198)


func bed_pos(index: int) -> Vector3:
	var node := prop_named("FarmBed_%d" % index)
	return node.global_position if node else Vector3(-190, 0, 52)


func set_food(main: Node, _zh: String) -> void:
	if host and Phase1Config.node("Phase1"):
		Phase1Config.node("Phase1").call("feed_started")


func prop_named(prop_name: String) -> Node3D:
	if zones == null:
		return null
	return zones.find_child(prop_name, true, false) as Node3D


func _spawn_prop(key: String, node_name: String, pos: Vector3, rot_y: float, fallback: Callable, scale_v: float = 1.0) -> Node3D:
	var path := "res://art/phase1/props/%s.glb" % key
	var node: Node3D
	if ResourceLoader.exists(path):
		var packed := load(path) as PackedScene
		if packed:
			node = packed.instantiate() as Node3D
	if node == null:
		node = fallback.call()
	else:
		_crisp(node)
	node.name = node_name
	node.position = pos
	node.rotation.y = rot_y
	if scale_v != 1.0:
		node.scale = Vector3.ONE * scale_v
	zones.add_child(node)
	return node


func _crisp(node: Node) -> void:
	if node is MeshInstance3D:
		var mi := node as MeshInstance3D
		var mesh := mi.mesh
		if mesh:
			for i in mesh.get_surface_count():
				var mat := mi.get_active_material(i)
				if mat is BaseMaterial3D:
					var copy := (mat as BaseMaterial3D).duplicate() as BaseMaterial3D
					copy.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
					mi.set_surface_override_material(i, copy)
	for child in node.get_children():
		_crisp(child)


func _tap_bed(index: int) -> String:
	var sim := Phase1Config.node("Sim")
	if sim == null:
		return ""
	var state: Dictionary = sim.get("state")
	var plots: Array = state.get("phase1_plots", ["empty", "sprout", "growing", "ripe"])
	while plots.size() < 4:
		plots.append("empty")
	var stage := str(plots[index])
	var msg := ""
	var harvest := false
	if stage == "ripe":
		plots[index] = "empty"
		msg = "收成"
		harvest = true
		var fruits: Dictionary = state.get("collection", {})
		var fruit_bag: Dictionary = fruits.get("fruits", {})
		fruit_bag["berry"] = int(fruit_bag.get("berry", 0)) + 1
		fruits["fruits"] = fruit_bag
		state["collection"] = fruits
	else:
		plots[index] = "sprout" if stage == "empty" else ("growing" if stage == "sprout" else "ripe")
		msg = "播種" if stage == "empty" else "生長"
	state["phase1_plots"] = plots
	sim.set("state", state)
	_refresh_beds()
	var p1 := Phase1Config.node("Phase1")
	if p1:
		p1.call("tend_bed", bed_pos(index), harvest)
		p1.call("mark", "bed")
	return msg


func _seed_plots() -> void:
	var sim := Phase1Config.node("Sim")
	if sim == null:
		return
	var state: Dictionary = sim.get("state")
	var plots: Array = state.get("phase1_plots", [])
	var blank := plots.is_empty()
	if not blank and plots.size() >= 2 and str(plots[0]) == "empty" and str(plots[1]) == "empty":
		blank = true
	if blank:
		state["phase1_plots"] = ["empty", "sprout", "growing", "ripe"]
		sim.set("state", state)


func _refresh_beds() -> void:
	var sim := Phase1Config.node("Sim")
	if zones == null or sim == null:
		return
	var state: Dictionary = sim.get("state")
	var plots: Array = state.get("phase1_plots", ["empty", "sprout", "growing", "ripe"])
	for i in range(4):
		var stage := str(plots[i]) if i < plots.size() else "empty"
		for part in ["sprout", "growing", "ripe"]:
			var node := zones.find_child("Crop_%d_%s" % [i, part], true, false) as Node3D
			if node:
				node.visible = part == stage


func _bed(index: int, pos: Vector3) -> void:
	var root := _spawn_prop("farm_bed", "FarmBed_%d" % index, pos, 0.0, _bed_fallback)
	_spot(root, "bed", Vector3(28, 10, 18))
	root.set_meta("bed", index)
	for part in ["sprout", "growing", "ripe"]:
		var crop := _spawn_prop("crop_%s" % part, "Crop_%d_%s" % [index, part], pos, 0.0, _crop_fallback.bind(part))
		zones.remove_child(crop)
		root.add_child(crop)
		crop.position = Vector3(0, 5.8, 0)
		crop.rotation.y = 0.0
		crop.visible = false
	var mark := Marker3D.new()
	mark.name = "BedCrop_%d" % index
	mark.position = pos + Vector3(0, 12, 0)
	zones.add_child(mark)


func _sign(node_name: String, text: String, pos: Vector3, scale_v: float = 1.0) -> void:
	var root := _spawn_prop("zone_signpost", node_name, pos, 0.0, _sign_fallback, scale_v)
	var label := Label3D.new()
	label.name = node_name + "Text"
	label.text = text
	label.font = Vc27Fonts.ensure()
	label.font_size = 40
	label.pixel_size = 0.06
	label.width = 0.0
	label.position = Vector3(0, 14, 1.16)
	label.billboard = BaseMaterial3D.BILLBOARD_DISABLED
	label.modulate = Color("24170f")
	label.outline_size = 0
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	root.add_child(label)


func _spot(root: Node3D, kind: String, size: Vector3) -> void:
	var area := Area3D.new()
	area.name = "Tap_" + kind
	area.set_meta("spot", kind)
	if kind == "bed":
		area.set_meta("bed", int(str(root.name).trim_prefix("FarmBed_")))
	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = size
	shape.shape = box
	area.add_child(shape)
	root.add_child(area)


func _mat(tex_path: String, tint: Color) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	var tex := load(tex_path) as Texture2D
	if tex:
		mat.albedo_texture = tex
		mat.uv1_scale = Vector3(0.4, 0.4, 0.4)
	mat.albedo_color = tint
	mat.roughness = 0.9
	return mat


func _box(parent: Node3D, node_name: String, pos: Vector3, size: Vector3, mat: Material) -> MeshInstance3D:
	var box := MeshInstance3D.new()
	box.name = node_name
	var mesh := BoxMesh.new()
	mesh.size = size
	box.mesh = mesh
	box.material_override = mat
	box.position = pos
	parent.add_child(box)
	return box


func _dress_yard(center: Vector3, count: int, radius: float) -> void:
	var tree_scene := load("res://hd2d_stage/art/meshes/tree.glb") as PackedScene
	var bush_scene := load("res://hd2d_stage/art/meshes/bush_bL.glb") as PackedScene
	for i in count:
		var ang := -0.4 + float(i) * 2.2 / float(maxi(count - 1, 1))
		var pos := center + Vector3(sin(ang) * radius, 0, -absf(cos(ang)) * radius * 0.65)
		if tree_scene:
			var tree := tree_scene.instantiate() as Node3D
			tree.name = "YardTree_%d_%d" % [int(center.x), i]
			tree.position = pos
			tree.scale = Vector3.ONE * (0.82 + float(i % 3) * 0.08)
			zones.add_child(tree)
		if bush_scene and i % 2 == 0:
			var bush := bush_scene.instantiate() as Node3D
			bush.name = "YardBush_%d_%d" % [int(center.x), i]
			bush.position = pos + Vector3(14, 0, 18)
			bush.scale = Vector3.ONE * 1.05
			zones.add_child(bush)


func _extend_lawn() -> void:
	var tex := load("res://hd2d_stage/textures/grass_outer_512.png") as Texture2D
	var sh := load("res://hd2d_stage/shaders/texel_lit.gdshader") as Shader
	# The live lawn ends at x ±640 and z -480..320. These skirts continue that grass
	# so the downward camera never sees the yellow void past the square edge.
	_lawn_strip(Vector3(0, -0.05, -1240), Vector2(3600, 1520), tex, sh)
	_lawn_strip(Vector3(0, -0.05, 760), Vector2(3600, 880), tex, sh)
	_lawn_strip(Vector3(-1420, -0.05, -80), Vector2(1560, 800), tex, sh)
	_lawn_strip(Vector3(1420, -0.05, -80), Vector2(1560, 800), tex, sh)


func _lawn_strip(pos: Vector3, size: Vector2, tex: Texture2D, sh: Shader) -> void:
	var mi := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = size
	mi.mesh = plane
	mi.position = pos
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	if sh and tex:
		var mat := ShaderMaterial.new()
		mat.shader = sh
		mat.set_shader_parameter("albedo_tex", tex)
		mat.set_shader_parameter("uv_scale", Vector2(size.x / 512.0, size.y / 512.0))
		mat.set_shader_parameter("roughness_val", 1.0)
		mat.set_shader_parameter("alpha_cut", 0.0)
		mat.set_shader_parameter("flip_v", false)
		mi.material_override = mat
	zones.add_child(mi)


func _pad(node_name: String, pos: Vector3, size: Vector3) -> void:
	var root := Node3D.new()
	root.name = node_name
	_box(root, "Dirt", Vector3.ZERO, size, _mat(DIRT, Color(0.72, 0.58, 0.38)))
	root.position = pos
	zones.add_child(root)


func _path_fallback() -> Node3D:
	var root := Node3D.new()
	_box(root, "Dirt", Vector3(0, 0.2, 0), Vector3(170, 0.35, 14), _mat(DIRT, Color(0.78, 0.62, 0.4)))
	return root


func _fence_fallback() -> Node3D:
	var root := Node3D.new()
	var wood := _mat(WOOD, Color(0.72, 0.5, 0.28))
	_box(root, "Post", Vector3(0, 6, 0), Vector3(1.6, 12, 1.6), wood)
	_box(root, "Rail", Vector3(8, 8, 0), Vector3(16, 1.2, 0.8), wood)
	return root


func _bed_fallback() -> Node3D:
	var root := Node3D.new()
	var wood := _mat(WOOD, Color(0.62, 0.4, 0.2))
	_box(root, "RailL", Vector3(-22, 6, 0), Vector3(3, 10, 32), wood)
	_box(root, "RailR", Vector3(22, 6, 0), Vector3(3, 10, 32), wood)
	_box(root, "RailF", Vector3(0, 6, 14), Vector3(48, 10, 3), wood)
	_box(root, "RailB", Vector3(0, 6, -14), Vector3(48, 10, 3), wood)
	_box(root, "Soil", Vector3(0, 8, 0), Vector3(40, 4, 24), _mat(DIRT, Color(0.35, 0.22, 0.12)))
	return root


func _crop_fallback(stage: String) -> Node3D:
	var root := Node3D.new()
	var leaf := _mat(BARK, Color(0.35, 0.62, 0.28))
	if stage == "sprout":
		_box(root, "Shoot", Vector3(0, 6, 0), Vector3(2.4, 12, 2.4), leaf)
	elif stage == "growing":
		_box(root, "Stem", Vector3(0, 10, 0), Vector3(2.6, 20, 2.6), leaf)
		_box(root, "Leaf", Vector3(4, 16, 0), Vector3(12, 2.4, 6), leaf)
	else:
		_box(root, "Stem", Vector3(0, 12, 0), Vector3(3, 24, 3), leaf)
		var fruit := _mat(DIRT, Color(0.86, 0.18, 0.24))
		_box(root, "Berry", Vector3(0, 24, 0), Vector3(8, 8, 8), fruit)
	return root


func _stove_fallback() -> Node3D:
	var root := Node3D.new()
	var brick := _mat(DIRT, Color(0.62, 0.32, 0.22))
	var wood := _mat(WOOD, Color(0.55, 0.36, 0.18))
	_box(root, "Base", Vector3(0, 8, 0), Vector3(28, 16, 22), brick)
	_box(root, "Top", Vector3(0, 17, 0), Vector3(32, 3, 26), wood)
	_box(root, "Pot", Vector3(0, 22, 0), Vector3(12, 8, 12), _mat(BARK, Color(0.3, 0.32, 0.34)))
	_box(root, "Chimney", Vector3(8, 26, -6), Vector3(6, 10, 6), brick)
	return root


func _post_fallback() -> Node3D:
	var root := Node3D.new()
	var wood := _mat(WOOD, Color(0.58, 0.38, 0.2))
	_box(root, "Post", Vector3(0, 14, 0), Vector3(3, 28, 3), wood)
	_box(root, "Roof", Vector3(0, 28, 0), Vector3(18, 2, 12), wood)
	var flag := _box(root, "MailFlag", Vector3(0, 20, 3), Vector3(1.4, 7, 5), _mat(WOOD, Color(0.85, 0.55, 0.2)))
	flag.rotation.x = 0.5
	return root


func _crate_fallback() -> Node3D:
	var root := Node3D.new()
	var wood := _mat(WOOD, Color(0.7, 0.5, 0.28))
	_box(root, "Body", Vector3(0, 4, 0), Vector3(10, 8, 10), wood)
	_box(root, "Slat", Vector3(0, 8.2, 0), Vector3(10, 0.6, 2), wood)
	return root


func _lantern_fallback() -> Node3D:
	var root := Node3D.new()
	_box(root, "Post", Vector3(0, 8, 0), Vector3(1.2, 16, 1.2), _mat(WOOD, Color(0.5, 0.32, 0.16)))
	var cage := _box(root, "Cage", Vector3(0, 18, 0), Vector3(3, 4, 3), _mat(WOOD, Color(1.0, 0.82, 0.45)))
	var light := OmniLight3D.new()
	light.position = cage.position
	light.light_color = Color(1.0, 0.72, 0.35)
	light.light_energy = 0.7
	light.omni_range = 26.0
	root.add_child(light)
	return root


func _stone_fallback() -> Node3D:
	var root := Node3D.new()
	_box(root, "Stone", Vector3(0, 1.2, 0), Vector3(14, 2.2, 9), _mat(DIRT, Color(0.62, 0.62, 0.58)))
	return root


func _flower_fallback() -> Node3D:
	var root := Node3D.new()
	_box(root, "Stem", Vector3(0, 8, 0), Vector3(1.6, 16, 1.6), _mat(BARK, Color(0.3, 0.55, 0.25)))
	_box(root, "Bloom", Vector3(0, 18, 0), Vector3(12, 4, 12), _mat(DIRT, Color(0.95, 0.42, 0.58)))
	_box(root, "Heart", Vector3(0, 21, 0), Vector3(4, 3, 4), _mat(DIRT, Color(1.0, 0.86, 0.45)))
	return root


func _sign_fallback() -> Node3D:
	var root := Node3D.new()
	var wood := _mat(WOOD, Color(0.55, 0.34, 0.16))
	_box(root, "Post", Vector3(0, 12, 0), Vector3(2.4, 24, 2.4), wood)
	_box(root, "Board", Vector3(0, 28, 0), Vector3(36, 12, 1.6), _mat(WOOD, Color(0.93, 0.82, 0.58)))
	return root
