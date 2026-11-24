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
var _floaters: Array[Node3D] = []
var _focus := Vector3.ZERO
const CLEAR := Vector3(6, 0, 62)
const PROP_SCALE := 2.4


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
	_floaters.clear()


func play_feed(food_zh: String) -> void:
	_stage_clear()
	_start("feed")
	_bowl = _prop("prop_food_bowl", _origin + Vector3(0, 0, 20), 0.0, _bowl_fallback)
	_note(food_zh)


func play_clean() -> void:
	_stage_clear()
	_start("clean")
	_prop("prop_broom", _origin + Vector3(24, 0, 8), 0.5, _broom_fallback)
	for i in 8:
		var bubble := _orb(Color(0.72, 0.94, 1.0, 0.62), randf_range(3.0, 6.0), _origin + Vector3(randf_range(-18, 18), 14, randf_range(-8, 14)))
		if bubble:
			_floaters.append(bubble)


func play_pat() -> void:
	_stage_clear()
	_start("pat")
	for i in 6:
		var heart := _heart(_origin + Vector3(randf_range(-10, 10), 20, randf_range(-6, 8)))
		if heart:
			_floaters.append(heart)


func play_train(stat: String) -> void:
	_stage_clear()
	_start(stat)
	if stat == "力量":
		_bell = _prop("prop_dumbbell", _origin + Vector3(22, 0, 8), 0.3, _bell_fallback)


func play_garden(bed_pos: Vector3, harvest: bool) -> void:
	_start("harvest" if harvest else "water")
	_dest = Vector3(bed_pos.x + 22.0, 0.0, bed_pos.z + 16.0)
	_prop("prop_watering_can", bed_pos + Vector3(16, 8, 18), -0.9, _can_fallback)
	if harvest:
		_berry = _sphere(Color(0.9, 0.16, 0.28), 5.0, bed_pos + Vector3(0, 30, 0))
	for i in 6:
		var drop := _orb(Color(0.35, 0.72, 1.0, 0.9), 1.6, bed_pos + Vector3(0, 22 - i * 2.0, 6))
		if drop:
			_floaters.append(drop)


func play_stove(stove_pos: Vector3) -> void:
	_start("stove")
	_dest = Vector3(stove_pos.x + 38.0, 0.0, stove_pos.z + 2.0)
	_focus = stove_pos
	var glow := OmniLight3D.new()
	glow.light_color = Color(1.0, 0.55, 0.18)
	glow.light_energy = 2.4
	glow.omni_range = 36.0
	if _fx:
		_fx.add_child(glow)
		glow.global_position = stove_pos + Vector3(0, 16, 0)
	for i in 6:
		var puff := _orb(Color(0.95, 0.95, 0.92, 0.7), 2.4 + float(i) * 0.35, stove_pos + Vector3(0, 22, 0))
		if puff:
			_floaters.append(puff)


func play_post(post_pos: Vector3) -> void:
	_start("post")
	_dest = Vector3(post_pos.x - 12.0, 0.0, post_pos.z + 10.0)
	_flag = _find("MailFlag")
	_prop("wood_crate", post_pos + Vector3(0, 16, 4), 0.2, _parcel_fallback)


func play_forage(spot: Vector3) -> void:
	_start("forage")
	_dest = Vector3(spot.x + 22.0, 0.0, spot.z + 8.0)
	for i in 8:
		var petal := _orb(Color(0.95, 0.55, 0.72, 0.9), 1.8, spot + Vector3(randf_range(-8, 8), 8, randf_range(-6, 6)))
		if petal:
			_floaters.append(petal)


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
			_bowl.scale = Vector3.ONE * PROP_SCALE * (1.0 - (u - 0.82) / 0.18)
	pet.global_position = at
	pet.global_position.y = bob
	pet.scale = _scale * Vector3(1.0, 0.86 if bob > 1.0 else 1.0, 1.0)


func _tick_clean(pet: Node3D, u: float) -> void:
	pet.global_position = _origin
	pet.global_position.y = sin(u * TAU * 5.0) * 1.6
	pet.rotation.z = sin(u * TAU * 4.0) * 0.18
	_orbit(_floaters, 20.0, 16.0, u)
	if int(_t * 8.0) % 2 == 0:
		_spark(_origin + Vector3(0, 26, 6), Color(1.0, 0.88, 0.35))


func _tick_pat(pet: Node3D, u: float) -> void:
	var squash_y := 1.0 + sin(u * TAU * 2.0) * 0.18
	pet.scale = Vector3(_scale.x * (2.0 - squash_y), _scale.y * squash_y, _scale.z * (2.0 - squash_y))
	pet.global_position = _origin + Vector3(sin(u * TAU) * 3.0, absf(sin(u * TAU * 2.0)) * 6.0, 0)
	for i in _floaters.size():
		var heart := _floaters[i]
		if heart:
			heart.global_position = _origin + Vector3(sin(u * TAU + float(i)) * 12.0, 22.0 + u * 28.0 + float(i) * 3.0, 8.0)
	_ring(_origin, 12.0 + u * 16.0)


func _tick_power(pet: Node3D, u: float) -> void:
	var lift := absf(sin(u * TAU * 3.0))
	pet.global_position = _origin + Vector3(0, lift * 4.0, 0)
	pet.scale = _scale * Vector3(1.08, 0.9 + lift * 0.15, 1.08)
	if _bell:
		_bell.global_position = _origin + Vector3(22, 16.0 + lift * 18.0, 6)
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
	for i in _floaters.size():
		var puff := _floaters[i]
		if puff:
			puff.global_position = _focus + Vector3(sin(float(i)) * 5.0, 24.0 + u * 28.0 + float(i) * 2.5, 0)
	if u > 0.2 and int(_t * 6.0) % 2 == 0:
		_spark(_focus + Vector3(0, 18, 4), Color(1.0, 0.42, 0.1))


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
	_orbit(_floaters, 16.0, 12.0, u * 1.4)
	if u > 0.35 and int(_t * 8.0) % 2 == 0:
		_spark(pet.global_position + Vector3(0, 18, 0), Color(1.0, 0.82, 0.35))


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


func _stage_clear() -> void:
	var pet := _pet()
	if pet:
		pet.global_position = CLEAR
		pet.global_position.y = 0.0


func _prop(key: String, pos: Vector3, rot_y: float, fallback: Callable, scale_v: float = PROP_SCALE) -> Node3D:
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
	node.scale = Vector3.ONE * scale_v
	_fx.add_child(node)
	node.global_position = pos
	return node


func _orbit(nodes: Array[Node3D], radius: float, height: float, u: float) -> void:
	for i in nodes.size():
		var node := nodes[i]
		if node == null:
			continue
		var ang := u * TAU + float(i) * TAU / maxf(float(nodes.size()), 1.0)
		node.global_position = _origin + Vector3(cos(ang) * radius, height + sin(u * TAU + float(i)) * 6.0, sin(ang) * radius * 0.6)


func _orb(color: Color, radius: float, pos: Vector3) -> MeshInstance3D:
	if _fx == null:
		return null
	var bit := MeshInstance3D.new()
	var mesh := SphereMesh.new()
	mesh.radius = radius
	mesh.height = radius * 2.0
	bit.mesh = mesh
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.emission_enabled = true
	mat.emission = Color(color.r, color.g, color.b)
	mat.emission_energy_multiplier = 0.8
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	bit.material_override = mat
	_fx.add_child(bit)
	bit.global_position = pos
	return bit


func _heart(pos: Vector3) -> Node3D:
	if _fx == null:
		return null
	var root := Node3D.new()
	_fx.add_child(root)
	root.global_position = pos
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.95, 0.35, 0.48)
	mat.emission_enabled = true
	mat.emission = Color(0.95, 0.28, 0.42)
	mat.emission_energy_multiplier = 1.1
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	for off in [Vector3(-2.2, 2.2, 0), Vector3(2.2, 2.2, 0)]:
		var lobe := MeshInstance3D.new()
		var sphere := SphereMesh.new()
		sphere.radius = 3.2
		sphere.height = 6.4
		lobe.mesh = sphere
		lobe.material_override = mat
		lobe.position = off
		root.add_child(lobe)
	var tip := MeshInstance3D.new()
	var box := BoxMesh.new()
	box.size = Vector3(6.4, 6.4, 3.2)
	tip.mesh = box
	tip.material_override = mat
	tip.position = Vector3(0, -1.2, 0)
	tip.rotation.z = PI * 0.25
	root.add_child(tip)
	return root


func _spark(pos: Vector3, color: Color) -> void:
	if _fx == null:
		return
	var bit := MeshInstance3D.new()
	var mesh := SphereMesh.new()
	mesh.radius = 3.2
	mesh.height = 6.4
	bit.mesh = mesh
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.emission_enabled = true
	mat.emission = color
	mat.emission_energy_multiplier = 1.4
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
