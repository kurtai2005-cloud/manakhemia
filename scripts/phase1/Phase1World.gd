class_name Phase1World
extends Node
## Four connected yards. The camera targets sit far enough apart to be different pictures.

const LOOK := {
	"garden": Vector3(0, 18, 12),
	"zone_farm": Vector3(-340, 12, 40),
	"zone_workshop": Vector3(340, 12, 40),
	"prairie_edge": Vector3(0, 18, -320),
}
const OLD_SPAN := 256.0

var host: Node


func build(main: Node) -> void:
	host = main
	_pad(main, "FarmPad", Color(0.72, 0.38, 0.14), Vector3(-340, 0.3, 40), Vector3(300, 0.6, 220))
	_pad(main, "ShopPad", Color(0.22, 0.28, 0.42), Vector3(340, 0.3, 40), Vector3(300, 0.6, 220))
	_banner(main, "FarmBanner", Color(0.85, 0.42, 0.12), Vector3(-340, 22, 40))
	_banner(main, "ShopBanner", Color(0.18, 0.32, 0.72), Vector3(340, 22, 40))
	_pad(main, "PrairiePad", Color(0.32, 0.58, 0.28), Vector3(0, 0.2, -320), Vector3(200, 0.4, 160))
	_sign(main, "SignFarm", "農圃", Vector3(-220, 0, 70))
	_sign(main, "SignShop", "工坊", Vector3(220, 0, 70))
	_sign(main, "SignPrairie", "草原", Vector3(40, 0, -250))
	for i in range(4):
		var bed := _pad(main, "FarmBed_%d" % i, Color(0.36, 0.22, 0.12), Vector3(-320 + i * 28, 0.4, 24), Vector3(22, 1.2, 16))
		bed.set_meta("bed", i)
		var area := Area3D.new()
		area.name = "BedTap_%d" % i
		area.position = bed.position
		var shape := CollisionShape3D.new()
		var box := BoxShape3D.new()
		box.size = Vector3(22, 4, 16)
		shape.shape = box
		area.add_child(shape)
		area.input_event.connect(func(_cam, _ev, _pos, _norm, _idx = i):
			if _ev is InputEventMouseButton and (_ev as InputEventMouseButton).pressed:
				_tap_bed(_idx)
		)
		main.add_child(area)
	_sprite(main, "WorkOutdoorStove", "res://art/ecosystem_v1/props/work_outdoor_stove_table.png", Vector3(300, 0, 30))
	_sprite(main, "WorkOutdoorPost", "res://art/ecosystem_v1/props/work_outdoor_post_rack.png", Vector3(370, 0, 48))
	_refresh_beds(host)


func look_for(zone_id: String) -> Vector3:
	return LOOK.get(zone_id, LOOK["garden"])


func span_ratio() -> float:
	var width := 800.0
	var depth := 660.0
	return (width * depth) / (OLD_SPAN * OLD_SPAN)


func tap_bed(index: int) -> String:
	return _tap_bed(index)


func set_food(main: Node, zh: String) -> void:
	var node := main.get_node_or_null("Phase1Food") as Sprite3D
	if node == null:
		node = Sprite3D.new()
		node.name = "Phase1Food"
		node.pixel_size = 0.4
		node.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		var tex := load("res://art-pet/sprites/hunt/fruits/starberry.png") as Texture2D
		node.texture = tex
		main.add_child(node)
	var pet := main.get("pet") as Node3D
	var pos := Vector3(8, 2, 16)
	if pet:
		pos = pet.global_position + Vector3(6, 2, 0)
	node.global_position = pos
	node.visible = true
	node.set_meta("food", zh)


func _tap_bed(index: int) -> String:
	var sim := Phase1Config.node("Sim")
	if sim == null:
		return ""
	var state: Dictionary = sim.get("state")
	var plots: Array = state.get("phase1_plots", ["empty", "empty", "empty", "empty"])
	while plots.size() < 4:
		plots.append("empty")
	var stage := str(plots[index])
	var msg := ""
	if stage == "ripe":
		plots[index] = "empty"
		msg = "收成"
		var bag := Phase1Config.node("CollectionSystem")
		if bag and bag.has_method("add_shards"):
			bag.call("add_shards", 0, "phase1_harvest")
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
	_refresh_beds(host)
	var p1 := Phase1Config.node("Phase1")
	if p1:
		p1.call("toast", msg)
		p1.call("mark", "bed")
	return msg


func _refresh_beds(main: Node) -> void:
	var sim := Phase1Config.node("Sim")
	if main == null or sim == null:
		return
	var state: Dictionary = sim.get("state")
	var plots: Array = state.get("phase1_plots", ["empty", "empty", "empty", "empty"])
	var files := {
		"empty": "res://art/ecosystem_v1/props/farm_plot_empty.png",
		"sprout": "res://art/ecosystem_v1/props/farm_crop_stage1_sprout.png",
		"growing": "res://art/ecosystem_v1/props/farm_crop_stage2_growing.png",
		"ripe": "res://art/ecosystem_v1/props/farm_crop_stage3_ripe.png",
	}
	for i in range(4):
		var stage := str(plots[i]) if i < plots.size() else "empty"
		var spr := main.get_node_or_null("BedCrop_%d" % i) as Sprite3D
		if spr == null:
			spr = Sprite3D.new()
			spr.name = "BedCrop_%d" % i
			spr.pixel_size = 0.35
			spr.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
			spr.position = Vector3(-320 + i * 28, 2, 24)
			main.add_child(spr)
		spr.texture = load(str(files.get(stage, files["empty"]))) as Texture2D


func _banner(main: Node, node_name: String, color: Color, pos: Vector3) -> void:
	var tex := load("res://art-pet/sprites/hunt/fruits/starberry.png") as Texture2D
	var board := Sprite3D.new()
	board.name = node_name
	board.texture = tex
	board.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	board.shaded = false
	board.pixel_size = 4.0
	board.position = pos
	board.modulate = color
	main.add_child(board)


func _pad(main: Node, node_name: String, color: Color, pos: Vector3, size: Vector3) -> MeshInstance3D:
	var box := MeshInstance3D.new()
	box.name = node_name
	var mesh := BoxMesh.new()
	mesh.size = size
	box.mesh = mesh
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.albedo_color = color
	box.material_override = mat
	box.position = pos
	main.add_child(box)
	return box


func _sign(main: Node, node_name: String, text: String, pos: Vector3) -> void:
	var post := _pad(main, node_name, Color(0.42, 0.28, 0.14), pos + Vector3(0, 6, 0), Vector3(2, 12, 2))
	var label := Label3D.new()
	label.text = text
	label.font_size = 48
	label.position = post.position + Vector3(0, 10, 0)
	label.font = Vc27Fonts.ensure()
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.modulate = Color(1, 0.96, 0.86)
	label.outline_size = 8
	main.add_child(label)


func _sprite(main: Node, node_name: String, path: String, pos: Vector3) -> void:
	if main.get_node_or_null(node_name):
		return
	var tex := load(path) as Texture2D
	if tex == null:
		return
	var spr := Sprite3D.new()
	spr.name = node_name
	spr.texture = tex
	spr.pixel_size = 0.5
	spr.position = pos + Vector3(0, 8, 0)
	spr.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
	main.add_child(spr)
