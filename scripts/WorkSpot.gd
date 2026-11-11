extends Node3D
class_name WorkSpot
## 花園入面嘅工作建築（郵局／廚房）：真 3D 體，寵物行過去做嘢。

var building_id := ""
var title := ""
var glow: MeshInstance3D
var icon: Sprite3D
var body: MeshInstance3D
var click: Area3D
var working: Array = []


func setup(id: String, zh: String, pos: Vector3, col: Color) -> void:
	building_id = id
	title = zh
	name = "Work_%s" % id
	position = pos
	body = MeshInstance3D.new()
	var box := BoxMesh.new()
	box.size = Vector3(36, 34, 28)
	body.mesh = box
	var mat := StandardMaterial3D.new()
	mat.albedo_color = col
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	body.material_override = mat
	body.position = Vector3(0, 17, 0)
	add_child(body)
	# 屋頂
	var roof := MeshInstance3D.new()
	var rb := BoxMesh.new()
	rb.size = Vector3(42, 8, 34)
	roof.mesh = rb
	var rm := StandardMaterial3D.new()
	rm.albedo_color = col.darkened(0.15)
	rm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	roof.material_override = rm
	roof.position = Vector3(0, 38, 0)
	add_child(roof)
	# 門口金光（收工時亮）
	glow = MeshInstance3D.new()
	var gb := BoxMesh.new()
	gb.size = Vector3(10, 16, 2)
	glow.mesh = gb
	var gm := StandardMaterial3D.new()
	gm.albedo_color = Color(1.0, 0.85, 0.25, 0.95)
	gm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	gm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	glow.material_override = gm
	glow.position = Vector3(0, 14, 15)
	glow.visible = false
	add_child(glow)
	icon = Sprite3D.new()
	icon.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	icon.pixel_size = 0.45
	icon.position = Vector3(0, 50, 0)
	icon.alpha_cut = SpriteBase3D.ALPHA_CUT_DISCARD
	icon.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	if IconBank:
		icon.texture = IconBank.tex("ev_work")
	add_child(icon)
	click = Area3D.new()
	click.name = "Click"
	click.input_ray_pickable = true
	click.collision_layer = 8
	click.collision_mask = 0
	var cs := CollisionShape3D.new()
	var sh := BoxShape3D.new()
	sh.size = Vector3(40, 44, 32)
	cs.shape = sh
	cs.position = Vector3(0, 20, 0)
	click.add_child(cs)
	add_child(click)


func set_ready_glow(on: bool) -> void:
	if glow:
		glow.visible = on


func door_pos() -> Vector3:
	return global_position + Vector3(0, 0, 22)
