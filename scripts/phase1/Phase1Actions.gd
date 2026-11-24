class_name Phase1Actions
extends Node
## Visible pet motion and 3D effects. A new action cancels the one still playing.

var host: Node
var zones: Node3D
var _kind := ""
var _t := 0.0
var _dur := 2.8
var _origin := Vector3.ZERO
var _scale := Vector3.ONE
var _dest := Vector3.ZERO
var _fx: Node3D
var _bowl: Node3D
var _flag: Node3D
var _berry: Node3D
var _bell: Node3D


func bind(main: Node, yard: Node3D) -> void:
	host = main
	zones = yard


func cancel() -> void:
	_kind = ""
	_t = 0.0
	var pet := _pet()
	if pet:
		pet.global_position.y = 0.0
		if _scale != Vector3.ZERO:
			pet.scale = _scale
	if _fx and is_instance_valid(_fx):
		_fx.queue_free()
	_fx = null
	_bowl = null
	_berry = null
	_bell = null


func play_feed(food_zh: String) -> void:
	_start("feed")
	_bowl = _prop("prop_food_bowl", _origin + Vector3(18, 0, 14), 0.0, _bowl_fallback)
	_note(food_zh)


func play_clean() -> void:
	_start("clean")
	_prop("prop_broom", _origin + Vector3(18, 0, 12), 0.6, _broom_fallback)


func play_pat() -> void:
	_start("pat")


func play_train(stat: String) -> void:
	_start(stat)
	if stat == "力量":
		_bell = _prop("prop_dumbbell", _origin + Vector3(16, 0, 10), 0.0, _bell_fallback)


func play_garden(bed_pos: Vector3, harvest: bool) -> void:
	_start("harvest" if harvest else "water")
	_dest = Vector3(bed_pos.x, 0.0, bed_pos.z + 14.0)
	_prop("prop_watering_can", _dest + Vector3(8, 0, 4), -0.5, _can_fallback)
	if harvest:
		_berry = _sphere(Color(0.85, 0.2, 0.35), 3.2, bed_pos + Vector3(0, 28, 0))


func play_stove(stove_pos: Vector3) -> void:
	_start("stove")
	_dest = Vector3(stove_pos.x - 10.0, 0.0, stove_pos.z + 12.0)


func play_post(post_pos: Vector3) -> void:
	_start("post")
	_dest = Vector3(post_pos.x - 12.0, 0.0, post_pos.z + 10.0)
	_flag = _find("MailFlag")
	_prop("wood_crate", post_pos + Vector3(0, 16, 4), 0.2, _parcel_fallback)


func play_forage(spot: Vector3) -> void:
	_start("forage")
	_dest = Vector3(spot.x, 0.0, spot.z + 10.0)


func jog_to(dest: Vector3) -> void:
	_start("jog")
	_dest = Vector3(dest.x, 0.0, dest.z)


func _start(kind: String) -> void:
	cancel()
	_kind = kind
	_dur = 2.8 if kind != "jog" else 1.3
	var pet := _pet()
	if pet == null or zones == null:
		return
	_origin = pet.global_position
	_origin.y = 0.0
	_scale = pet.scale
	_dest = _origin
	_fx = Node3D.new()
	_fx.name = "Phase1Fx"
	zones.add_child(_fx)


func _process(dt: float) -> void:
	if _kind == "":
		return
	_t += dt
	var u := clampf(_t / _dur, 0.0, 1.0)
	var pet := _pet()
	if pet == null:
		return
	if _kind == "feed":
		_tick_feed(pet, u)
	elif _kind == "clean":
		_tick_clean(pet, u)
	elif _kind == "pat":
		_tick_pat(pet, u)
	elif _kind == "力量":
		_tick_power(pet, u)
	elif _kind == "身手":
		_tick_agi(pet, u)
	elif _kind == "耐力":
		_tick_stam(pet, u)
	elif _kind == "water" or _kind == "harvest":
		_tick_garden(pet, u)
	elif _kind == "stove":
		_tick_stove(pet, u)
	elif _kind == "post":
		_tick_post(pet, u)
	elif _kind == "forage":
		_tick_forage(pet, u)
	elif _kind == "jog":
		pet.global_position = _origin.lerp(_dest, _smooth(u))
		pet.global_position.y = sin(u * TAU * 4.0) * 1.4
	if _t >= _dur:
		pet.global_position = _dest if _kind == "jog" or _kind == "water" or _kind == "harvest" or _kind == "stove" or _kind == "post" or _kind == "forage" else _origin
		pet.global_position.y = 0.0
		pet.scale = _scale
		pet.rotation.z = 0.0
		_kind = ""


func _tick_feed(pet: Node3D, u: float) -> void:
	var walk := clampf(u / 0.22, 0.0, 1.0)
	var at := _origin.lerp(_origin + Vector3(16, 0, 12), _smooth(walk))
	var bob := 0.0
	if u > 0.22 and u < 0.82:
		bob = absf(sin((u - 0.22) * TAU * 3.0)) * 3.2
		if int(_t * 8.0) % 2 == 0:
			_spark(_bowl.global_position + Vector3(0, 8, 0) if _bowl else at, Color(1.0, 0.82, 0.45))
			_spark(at + Vector3(0, 28, 0), Color(0.95, 0.35, 0.45))
	if u > 0.82:
		bob = sin((u - 0.82) * TAU) * 6.0
		if _bowl:
			_bowl.scale = Vector3.ONE * (1.0 - (u - 0.82) / 0.18)
	pet.global_position = at
	pet.global_position.y = bob
	pet.scale = _scale * Vector3(1.0, 0.86 if bob > 1.0 else 1.0, 1.0)


func _tick_clean(pet: Node3D, u: float) -> void:
	pet.global_position = _origin
	pet.global_position.y = sin(u * TAU * 5.0) * 1.6
	pet.rotation.z = sin(u * TAU * 4.0) * 0.12
	if int(_t * 10.0) % 2 == 0:
		var ang := u * TAU * 2.0
		_spark(_origin + Vector3(cos(ang) * 14.0, 16.0 + sin(u * 6.0) * 4.0, sin(ang) * 14.0), Color(0.75, 0.9, 1.0, 0.8))
		_spark(_origin + Vector3(0, 22, 0), Color(1.0, 0.92, 0.55))


func _tick_pat(pet: Node3D, u: float) -> void:
	var squash := 1.0 + sin(u * TAU * 2.0) * 0.12
	pet.scale = Vector3(_scale.x * (2.0 - squash), _scale.y * squash, _scale.z * (2.0 - squash))
	pet.global_position = _origin + Vector3(sin(u * TAU) * 2.0, absf(sin(u * TAU * 2.0)) * 5.0, 0)
	if int(_t * 8.0) % 2 == 0:
		_spark(_origin + Vector3(randf_range(-8, 8), 18 + u * 20.0, randf_range(-6, 6)), Color(0.95, 0.4, 0.5))
	_ring(_origin, 8.0 + u * 18.0)


func _tick_power(pet: Node3D, u: float) -> void:
	var lift := absf(sin(u * TAU * 3.0))
	pet.global_position = _origin + Vector3(0, lift * 4.0, 0)
	pet.scale = _scale * Vector3(1.08, 0.9 + lift * 0.15, 1.08)
	if _bell:
		_bell.global_position = _origin + Vector3(16, 6.0 + lift * 14.0, 10)
	if int(_t * 9.0) % 2 == 0:
		_spark(_origin + Vector3(10, 16 + lift * 8.0, 4), Color(0.55, 0.8, 1.0))
		_spark(_origin + Vector3(-4, 24, 0), Color(1.0, 0.84, 0.35))


func _tick_agi(pet: Node3D, u: float) -> void:
	var x := sin(u * TAU * 2.0) * 28.0
	var z := sin(u * TAU * 4.0) * 10.0
	pet.global_position = _origin + Vector3(x, absf(sin(u * TAU * 6.0)) * 2.0, z)
	if int(_t * 12.0) % 2 == 0:
		_spark(pet.global_position + Vector3(0, 2, 0), Color(0.72, 0.58, 0.32))


func _tick_stam(pet: Node3D, u: float) -> void:
	var hop := absf(sin(u * TAU * 3.0))
	pet.global_position = _origin + Vector3(0, hop * 14.0, 0)
	if hop > 0.85:
		_ring(_origin, 6.0 + hop * 8.0)
	if int(_t * 8.0) % 2 == 0:
		_spark(_origin + Vector3(0, 20, 0), Color(0.55, 0.85, 0.5))


func _tick_garden(pet: Node3D, u: float) -> void:
	var walk := clampf(u / 0.35, 0.0, 1.0)
	pet.global_position = _origin.lerp(_dest, _smooth(walk))
	pet.global_position.y = sin(u * TAU * 3.0) * 1.5
	if u > 0.35 and int(_t * 10.0) % 2 == 0:
		var drop := Color(0.35, 0.65, 0.95) if _kind == "water" else Color(0.55, 0.36, 0.18)
		_spark(_dest + Vector3(0, 14 - u * 8.0, 0), drop)
	if _kind == "harvest" and _berry:
		var arc := sin(clampf((u - 0.4) / 0.4, 0.0, 1.0) * PI)
		_berry.global_position = _dest + Vector3(u * 16.0, 10.0 + arc * 18.0, 4)


func _tick_stove(pet: Node3D, u: float) -> void:
	var walk := clampf(u / 0.3, 0.0, 1.0)
	pet.global_position = _origin.lerp(_dest, _smooth(walk))
	pet.global_position.y = sin(u * TAU * 4.0) * 1.2
	if u > 0.3 and int(_t * 8.0) % 2 == 0:
		_spark(_dest + Vector3(8, 18 + u * 10.0, -6), Color(0.95, 0.95, 0.95))
		_spark(_dest + Vector3(8, 12, -6), Color(1.0, 0.45, 0.15))


func _tick_post(pet: Node3D, u: float) -> void:
	var walk := clampf(u / 0.3, 0.0, 1.0)
	pet.global_position = _origin.lerp(_dest, _smooth(walk))
	pet.global_position.y = absf(sin(u * TAU * 3.0)) * 3.0
	if _flag:
		_flag.rotation.x = lerpf(0.6, -0.8, _smooth(clampf((u - 0.35) / 0.3, 0.0, 1.0)))
	if u > 0.35 and int(_t * 8.0) % 2 == 0:
		_spark(_dest + Vector3(6, 16 + u * 12.0, 0), Color(1.0, 0.82, 0.35))


func _tick_forage(pet: Node3D, u: float) -> void:
	var walk := clampf(u / 0.4, 0.0, 1.0)
	pet.global_position = _origin.lerp(_dest, _smooth(walk))
	pet.global_position.y = sin(u * TAU * 2.0) * 1.2
	if u > 0.4 and int(_t * 9.0) % 2 == 0:
		var ang := u * TAU * 3.0
		_spark(pet.global_position + Vector3(cos(ang) * 8.0, 14, sin(ang) * 8.0), Color(0.95, 0.55, 0.7))
		_spark(pet.global_position + Vector3(0, 8, 0), Color(0.45, 0.7, 0.35))


func _pet() -> Node3D:
	if host == null:
		return null
	return host.get("pet") as Node3D


func _find(node_name: String) -> Node3D:
	if zones == null:
		return null
	return zones.find_child(node_name, true, false) as Node3D


func _smooth(u: float) -> float:
	return u * u * (3.0 - 2.0 * u)


func _note(_text: String) -> void:
	pass


func _prop(key: String, pos: Vector3, rot_y: float, fallback: Callable) -> Node3D:
	if zones == null or _fx == null:
		return null
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
	node.rotation.y = rot_y
	_fx.add_child(node)
	node.global_position = pos
	return node


func _spark(pos: Vector3, color: Color) -> void:
	if _fx == null:
		return
	var bit := MeshInstance3D.new()
	var mesh := SphereMesh.new()
	mesh.radius = 2.4
	mesh.height = 4.8
	bit.mesh = mesh
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.emission_enabled = true
	mat.emission = color
	mat.emission_energy_multiplier = 0.4
	bit.material_override = mat
	_fx.add_child(bit)
	bit.global_position = pos


func _ring(pos: Vector3, radius: float) -> void:
	if _fx == null:
		return
	var ring := MeshInstance3D.new()
	var mesh := TorusMesh.new()
	mesh.inner_radius = radius
	mesh.outer_radius = radius + 0.6
	ring.mesh = mesh
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(1.0, 0.82, 0.35, 0.85)
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	ring.material_override = mat
	_fx.add_child(ring)
	ring.global_position = pos + Vector3(0, 0.4, 0)


func _sphere(color: Color, radius: float, pos: Vector3) -> MeshInstance3D:
	var bit := MeshInstance3D.new()
	var mesh := SphereMesh.new()
	mesh.radius = radius
	mesh.height = radius * 2.0
	bit.mesh = mesh
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	bit.material_override = mat
	if _fx:
		_fx.add_child(bit)
		bit.global_position = pos
	return bit


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


func _bowl_fallback() -> Node3D:
	var bowl := _block(Color(0.72, 0.48, 0.26), Vector3(12, 4, 12))
	var berry := _block(Color(0.86, 0.16, 0.28), Vector3(4, 4, 4))
	berry.position = Vector3(0, 4, 0)
	bowl.add_child(berry)
	return bowl


func _broom_fallback() -> Node3D:
	var root := Node3D.new()
	var handle := _block(Color(0.55, 0.36, 0.18), Vector3(1.2, 14, 1.2))
	handle.position = Vector3(0, 8, 0)
	root.add_child(handle)
	var head := _block(Color(0.72, 0.62, 0.4), Vector3(6, 2, 2))
	head.position = Vector3(0, 1, 0)
	root.add_child(head)
	return root


func _bell_fallback() -> Node3D:
	return _block(Color(0.28, 0.32, 0.38), Vector3(16, 4, 4))


func _can_fallback() -> Node3D:
	return _block(Color(0.25, 0.55, 0.85), Vector3(4, 6, 3))


func _parcel_fallback() -> Node3D:
	return _block(Color(0.72, 0.5, 0.28), Vector3(6, 5, 6))


func _block(color: Color, size: Vector3) -> MeshInstance3D:
	var box := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = size
	box.mesh = mesh
	var mat := StandardMaterial3D.new()
	var tex := load("res://hd2d_stage/textures/tiles/wood_a.png") as Texture2D
	if tex:
		mat.albedo_texture = tex
	mat.albedo_color = color
	mat.roughness = 0.86
	box.material_override = mat
	return box
