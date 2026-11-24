class_name Phase1World
extends Node
## Yards in the live 675 scene, on the same meter scale as the cottage.

const LOOK := {
	"garden": Vector3(12, 58, -26),
	"zone_farm": Vector3(-190, 58, 36),
	"zone_workshop": Vector3(250, 58, -36),
	"prairie_edge": Vector3(16, 58, -220),
}
const OLD_SPAN := 256.0

var host: Node
var zones: Node3D


func build(exterior: Node) -> void:
	host = exterior
	zones = Node3D.new()
	zones.name = "Phase1ZonesRoot"
	exterior.add_child(zones)
	_path(Vector3(-40, 0.12, -10), Vector3(160, 0.08, 10))
	_fence(-250, -120, 8)
	for i in range(4):
		_bed(i, Vector3(-246 + i * 38, 0, 48))
	_sign("SignFarm", "農圃", Vector3(-150, 0, 70))
	_sprite("WorkOutdoorStove", "res://art/ecosystem_v1/props/work_outdoor_stove_table.png", Vector3(228, 0, -30), 0.45)
	_sprite("WorkOutdoorPost", "res://art/ecosystem_v1/props/work_outdoor_post_rack.png", Vector3(292, 0, -16), 0.45)
	_crate(Vector3(258, 0, -6))
	_lantern(Vector3(206, 0, -6))
	_sign("SignShop", "工坊", Vector3(188, 0, 8))
	_fence(170, 320, -62)
	for i in range(4):
		_stone(Vector3(-6 + i * 16, 0, -188 - i * 14))
		_flower(i, Vector3(-28 + i * 20, 0, -214))
	_sign("SignPrairie", "草原", Vector3(40, 0, -196))
	_seed_plots()
	_refresh_beds()


func look_for(zone_id: String) -> Vector3:
	return LOOK.get(zone_id, LOOK["garden"])


func span_ratio() -> float:
	var width := 250.0 - (-190.0)
	var depth := -16.0 - (-220.0)
	return (width * depth) / (90.0 * 70.0)


func tap_bed(index: int) -> String:
	return _tap_bed(index)


func set_food(main: Node, zh: String) -> void:
	if zones == null:
		return
	var node := zones.get_node_or_null("Phase1Food") as Sprite3D
	if node == null:
		node = Sprite3D.new()
		node.name = "Phase1Food"
		node.pixel_size = 1.5
		node.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
		node.shaded = false
		node.texture = load("res://art-pet/sprites/hunt/fruits/starberry.png") as Texture2D
		zones.add_child(node)
	var pet := main.get("pet") as Node3D
	var pos := Vector3(10, 16, 8)
	if pet:
		var coat := pet.get_node_or_null("Hd2dCoat") as Node3D
		var feet := coat.global_position if coat else pet.global_position
		pos = Vector3(feet.x + 22.0, 20.0, feet.z + 18.0)
	node.global_position = pos
	node.visible = true
	node.set_meta("food", zh)


func prop_named(prop_name: String) -> Node3D:
	if zones == null:
		return null
	return zones.get_node_or_null(prop_name) as Node3D


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
	if stage == "ripe":
		plots[index] = "empty"
		msg = "收成"
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
		p1.call("toast", msg)
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
	var files := {
		"empty": "res://art/ecosystem_v1/props/farm_plot_empty.png",
		"sprout": "res://art/ecosystem_v1/props/farm_crop_stage1_sprout.png",
		"growing": "res://art/ecosystem_v1/props/farm_crop_stage2_growing.png",
		"ripe": "res://art/ecosystem_v1/props/farm_crop_stage3_ripe.png",
	}
	for i in range(4):
		var stage := str(plots[i]) if i < plots.size() else "empty"
		var spr := zones.get_node_or_null("BedCrop_%d" % i) as Sprite3D
		if spr:
			spr.texture = load(str(files.get(stage, files["empty"]))) as Texture2D


func _bed(index: int, pos: Vector3) -> void:
	var body := _wood("FarmBed_%d" % index, pos + Vector3(0, 3, 0), Vector3(28, 6, 18))
	var area := Area3D.new()
	area.name = "BedTap_%d" % index
	area.position = pos + Vector3(0, 4, 0)
	area.set_meta("bed", index)
	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(28, 10, 18)
	shape.shape = box
	area.add_child(shape)
	area.input_event.connect(func(_cam, ev, _pos, _norm, _idx, idx := index):
		if ev is InputEventMouseButton and (ev as InputEventMouseButton).pressed:
			_tap_bed(idx)
	)
	zones.add_child(area)
	var spr := Sprite3D.new()
	spr.name = "BedCrop_%d" % index
	spr.pixel_size = 0.62
	spr.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
	spr.shaded = false
	spr.position = pos + Vector3(0, 16, 0)
	zones.add_child(spr)
	body.set_meta("bed", index)


func _path(pos: Vector3, size: Vector3) -> void:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.62, 0.48, 0.3)
	mat.roughness = 1.0
	var box := MeshInstance3D.new()
	box.name = "FarmPath"
	var mesh := BoxMesh.new()
	mesh.size = size
	box.mesh = mesh
	box.material_override = mat
	box.position = pos
	zones.add_child(box)


func _fence(x0: float, x1: float, z: float) -> void:
	var x := x0
	var n := 0
	while x <= x1:
		_wood("Fence_%d_%d" % [int(z), n], Vector3(x, 5, z), Vector3(1.4, 10, 1.4))
		x += 18.0
		n += 1


func _wood(node_name: String, pos: Vector3, size: Vector3) -> MeshInstance3D:
	var box := MeshInstance3D.new()
	box.name = node_name
	var mesh := BoxMesh.new()
	mesh.size = size
	box.mesh = mesh
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.48, 0.3, 0.16)
	mat.roughness = 0.9
	box.material_override = mat
	box.position = pos
	zones.add_child(box)
	return box


func _crate(pos: Vector3) -> void:
	_wood("ShopCrate", pos + Vector3(0, 4, 0), Vector3(10, 8, 10))


func _lantern(pos: Vector3) -> void:
	var post := _wood("LanternPost", pos + Vector3(0, 8, 0), Vector3(1.2, 16, 1.2))
	var light := OmniLight3D.new()
	light.name = "ShopLantern"
	light.position = post.position + Vector3(0, 10, 0)
	light.light_color = Color(1.0, 0.72, 0.35)
	light.light_energy = 0.6
	light.omni_range = 28.0
	zones.add_child(light)


func _stone(pos: Vector3) -> void:
	var box := MeshInstance3D.new()
	box.name = "Step_%d_%d" % [int(pos.x), int(pos.z)]
	var mesh := BoxMesh.new()
	mesh.size = Vector3(8, 0.6, 5)
	box.mesh = mesh
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.55, 0.54, 0.5)
	mat.roughness = 1.0
	box.material_override = mat
	box.position = pos + Vector3(0, 0.4, 0)
	zones.add_child(box)


func _flower(index: int, pos: Vector3) -> void:
	var spr := Sprite3D.new()
	spr.name = "Flower_%d" % index
	spr.texture = load("res://hd2d_stage/textures/tiles/flower_a.png") as Texture2D
	spr.pixel_size = 0.8
	spr.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
	spr.shaded = false
	spr.position = pos + Vector3(0, 6, 0)
	zones.add_child(spr)


func _sign(node_name: String, text: String, pos: Vector3) -> void:
	_wood(node_name, pos + Vector3(0, 8, 0), Vector3(1.6, 16, 1.6))
	var label := Label3D.new()
	label.name = node_name + "Text"
	label.text = text
	label.font = Vc27Fonts.ensure()
	label.font_size = 64
	label.pixel_size = 0.12
	label.position = pos + Vector3(0, 20, 0)
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.modulate = Color(1, 0.96, 0.88)
	label.outline_size = 12
	zones.add_child(label)


func _sprite(node_name: String, path: String, pos: Vector3, px: float) -> void:
	var tex := load(path) as Texture2D
	if tex == null:
		return
	var spr := Sprite3D.new()
	spr.name = node_name
	spr.texture = tex
	spr.pixel_size = px
	spr.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
	spr.shaded = false
	spr.position = pos + Vector3(0, 22, 0)
	zones.add_child(spr)
