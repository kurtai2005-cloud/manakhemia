class_name Phase1Actions
extends Node
## The pet runs along open paths. Rewards and prop effects start only after arrival.

signal arrived(kind: String)

var host: Node
var zones: Node3D
var _kind := ""
var _phase := ""
var _t := 0.0
var _origin := Vector3.ZERO
var _scale := Vector3.ONE
var _dest := Vector3.ZERO
var _focus := Vector3.ZERO
var _fx: Node3D
var _bowl: Node3D
var _flag: Node3D
var _berry: Node3D
var _bell: Node3D
var _floaters: Array[Node3D] = []
var _path: PackedVector3Array = PackedVector3Array()
var _path_i := 0
var _speed := 40.0
var _run_t := 0.0
var _run_len := 0.0
var _run_done := 0.0
var _micro_at := -1.0
var _micro_done := false
var _dust_bucket := -1
var vfx_fired := false
var spark_runtime_allocs := 0
var _pool_root: Node3D
var _free: Array[MeshInstance3D] = []
var _busy: Array[Dictionary] = []
var _ring: MeshInstance3D
const PROP_SCALE := 2.4
const POOL_N := 28
const NODES := {
	"home": Vector3(0, 0, 45),
	"west": Vector3(-125, 0, 15),
	"farm_gate": Vector3(-302, 0, 20),
	"farm": Vector3(-365, 0, 25),
	"east": Vector3(125, 0, 15),
	"shop_gate": Vector3(302, 0, 20),
	"shop": Vector3(410, 0, 22),
	"east_north": Vector3(125, 0, -125),
	"prairie_east": Vector3(240, 0, -125),
	"prairie_gate": Vector3(240, 0, -330),
	"prairie": Vector3(240, 0, -385),
}
const LINKS := [
	["home", "west"], ["west", "farm_gate"], ["farm_gate", "farm"],
	["home", "east"], ["east", "shop_gate"], ["shop_gate", "shop"],
	["east", "east_north"], ["east_north", "prairie_east"], ["prairie_east", "prairie_gate"], ["prairie_gate", "prairie"],
]


func bind(main: Node, yard: Node3D) -> void:
	host = main
	zones = yard
	_ensure_pool()


func cancel() -> void:
	_kind = ""
	_phase = ""
	_t = 0.0
	var pet := _pet()
	if pet:
		pet.global_position.y = 0.0
		if _scale != Vector3.ZERO:
			pet.scale = _scale
		pet.set("phase1_scripted", false)
		pet.set("moving", false)
	if _fx and is_instance_valid(_fx):
		_fx.queue_free()
	_fx = null
	_bowl = null
	_berry = null
	_bell = null
	_floaters.clear()
	if _ring:
		_ring.visible = false


func play_feed(food_zh: String) -> void:
	_start("feed")
	_bowl = _prop("prop_food_bowl", _origin + Vector3(0, 0, 14), 0.0, _bowl_fallback)
	_note(food_zh)


func play_clean() -> void:
	_start("clean")
	_prop("prop_broom", _origin + Vector3(16, 0, 8), 0.5, _broom_fallback)
	for i in 8:
		var bubble := _orb(Color(0.72, 0.94, 1.0, 0.62), randf_range(3.0, 6.0), _origin + Vector3(randf_range(-14, 14), 14, randf_range(-8, 12)))
		if bubble:
			_floaters.append(bubble)


func play_pat() -> void:
	_start("pat")
	for i in 6:
		var heart := _heart(_origin + Vector3(randf_range(-8, 8), 20, randf_range(-6, 8)))
		if heart:
			_floaters.append(heart)


func play_train(stat: String) -> void:
	_start(stat)
	if stat == "力量":
		_bell = _prop("prop_dumbbell", _origin + Vector3(16, 0, 8), 0.3, _bell_fallback)


func play_garden(bed_pos: Vector3, harvest: bool) -> void:
	var stand := Vector3(bed_pos.x + 10.0, 0.0, bed_pos.z + 12.0)
	_travel("harvest" if harvest else "water", stand, bed_pos, true)


func play_stove(stove_pos: Vector3) -> void:
	_travel("stove", Vector3(stove_pos.x + 22.0, 0.0, stove_pos.z + 16.0), stove_pos, true)


func play_post(post_pos: Vector3) -> void:
	_travel("post", Vector3(post_pos.x - 14.0, 0.0, post_pos.z + 14.0), post_pos, true)


func play_forage(spot: Vector3) -> void:
	_travel("forage", Vector3(spot.x, 0.0, spot.z + 8.0), spot, true)


func jog_to(dest: Vector3) -> void:
	_travel("jog", Vector3(dest.x, 0.0, dest.z), dest, false)


func goal_distance() -> float:
	var pet := _pet()
	if pet == null:
		return 0.0
	return Vector2(pet.global_position.x, pet.global_position.z).distance_to(Vector2(_dest.x, _dest.z))


func busy() -> bool:
	return _kind != ""


func _start(kind: String) -> void:
	cancel()
	_kind = kind
	_phase = "act"
	_t = 0.0
	vfx_fired = false
	var pet := _pet()
	if pet == null or zones == null:
		return
	_origin = pet.global_position
	_origin.y = 0.0
	_scale = pet.scale
	_dest = _origin
	pet.set("phase1_scripted", true)
	pet.set("moving", false)
	pet.set("live_clip", "")
	_fx = Node3D.new()
	_fx.name = "Phase1Fx"
	zones.add_child(_fx)


func _travel(kind: String, dest: Vector3, focus: Vector3, follow: bool) -> void:
	_start(kind)
	_phase = "run"
	_dest = Vector3(dest.x, 0.0, dest.z)
	_focus = focus
	_path = _route(_origin, _dest)
	_path_i = 1 if _path.size() > 1 else 0
	_run_t = 0.0
	_run_done = 0.0
	_run_len = _length(_path)
	var wobble := fposmod(_run_len * 0.17, 1.0)
	_speed = (38.0 + wobble * 4.0) if _run_len <= 90.0 else (58.0 + wobble * 10.0)
	_micro_at = -1.0
	_micro_done = false
	_dust_bucket = -1
	if _run_len > 90.0 and randf() < 0.25:
		_micro_at = randf_range(0.40, 0.60)
	vfx_fired = false
	print("RUN kind=", kind, " len=", snappedf(_run_len, 0.1), " speed=", snappedf(_speed, 0.1), " path=", _path)
	if follow:
		_maybe_follow()


func _process(dt: float) -> void:
	_tick_puffs(dt)
	if _kind == "":
		return
	var pet := _pet()
	if pet == null:
		return
	pet.set("phase1_scripted", true)
	if _phase == "run":
		_tick_run(pet, dt)
		return
	_t += dt
	var dur := 2.2
	var u := clampf(_t / dur, 0.0, 1.0)
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
		_tick_act_bob(pet, u)
	elif _kind == "stove" or _kind == "post" or _kind == "forage":
		_tick_act_bob(pet, u)
	if _t >= dur:
		pet.global_position = Vector3(_dest.x, 0.0, _dest.z) if _kind != "feed" and _kind != "clean" and _kind != "pat" and _kind != "力量" and _kind != "身手" and _kind != "耐力" else Vector3(_origin.x, 0.0, _origin.z)
		if _kind == "feed":
			pet.global_position = _origin + Vector3(12, 0, 8)
			pet.global_position.y = 0.0
		pet.scale = _scale
		pet.rotation.z = 0.0
		pet.set("moving", false)
		pet.set("phase1_scripted", false)
		_kind = ""
		_phase = ""


func _tick_run(pet: Node3D, dt: float) -> void:
	pet.set("moving", true)
	if _path_i >= _path.size():
		_finish_run(pet)
		return
	var target := _path[_path_i]
	var pos := Vector3(pet.global_position.x, 0.0, pet.global_position.z)
	var to := target - pos
	to.y = 0.0
	var dist := to.length()
	if dist < 1.4:
		_path_i += 1
		if _path_i >= _path.size():
			_finish_run(pet)
		return
	var dir := to / dist
	var step := minf(_speed * dt, dist)
	_run_t += dt
	_run_done += step
	var hop := absf(sin(_run_t * 14.0)) * 1.5
	if _run_t < 0.25:
		hop += sin(clampf(_run_t / 0.25, 0.0, 1.0) * PI) * 2.4
	if _micro_at > 0.0 and not _micro_done and _run_len > 1.0 and _run_done / _run_len >= _micro_at:
		_micro_done = true
		hop += 3.6
		_mood()
	var nxt := pos + dir * step
	pet.global_position = Vector3(nxt.x, hop, nxt.z)
	if pet.has_method("_update_dir"):
		pet.call("_update_dir", dir.x, dir.z)
	var bucket := int(_run_t / 0.18)
	if bucket != _dust_bucket:
		_dust_bucket = bucket
		_dust(Vector3(nxt.x, 0.15, nxt.z))


func _finish_run(pet: Node3D) -> void:
	pet.global_position = Vector3(_dest.x, 0.0, _dest.z)
	pet.set("moving", false)
	if _kind == "jog":
		pet.set("phase1_scripted", false)
		var done := _kind
		_kind = ""
		_phase = ""
		emit_signal("arrived", done)
		return
	_phase = "act"
	_t = 0.0
	_fire_vfx()
	vfx_fired = true
	emit_signal("arrived", _kind)


func _fire_vfx() -> void:
	if _kind == "water" or _kind == "harvest":
		_prop("prop_watering_can", _focus + Vector3(8, 8, 10), -0.9, _can_fallback)
		if _kind == "harvest":
			_berry = _sphere(Color(0.9, 0.16, 0.28), 5.0, _focus + Vector3(0, 18, 0))
		for i in 6:
			var drop := _orb(Color(0.35, 0.72, 1.0, 0.9) if _kind == "water" else Color(0.9, 0.22, 0.28, 0.9), 1.6, _focus + Vector3(0, 16 - i * 1.5, 4))
			if drop:
				_floaters.append(drop)
	elif _kind == "stove":
		var glow := OmniLight3D.new()
		glow.name = "StoveGlow"
		glow.light_color = Color(1.0, 0.55, 0.18)
		glow.light_energy = 1.6
		glow.omni_range = 28.0
		glow.shadow_enabled = false
		if _fx:
			_fx.add_child(glow)
			glow.global_position = _focus + Vector3(0, 14, 0)
		for i in 6:
			var puff := _orb(Color(0.95, 0.95, 0.92, 0.7), 2.2, _focus + Vector3(0, 16, 0))
			if puff:
				_floaters.append(puff)
	elif _kind == "post":
		_flag = _find("MailFlag")
		_prop("wood_crate", _focus + Vector3(0, 12, 4), 0.2, _parcel_fallback)
	elif _kind == "forage":
		for i in 8:
			var petal := _orb(Color(0.95, 0.55, 0.72, 0.9), 1.8, _focus + Vector3(randf_range(-8, 8), 8, randf_range(-6, 6)))
			if petal:
				_floaters.append(petal)


func _tick_act_bob(pet: Node3D, u: float) -> void:
	pet.global_position = Vector3(_dest.x, absf(sin(u * TAU * 3.0)) * 1.4, _dest.z)
	if _kind == "harvest" and _berry:
		var arc := sin(clampf((u - 0.2) / 0.5, 0.0, 1.0) * PI)
		_berry.global_position = _focus + Vector3(u * 10.0, 12.0 + arc * 14.0, 4)
	if _kind == "stove":
		for i in _floaters.size():
			var puff := _floaters[i]
			if puff:
				puff.global_position = _focus + Vector3(sin(float(i)) * 4.0, 16.0 + u * 22.0 + float(i) * 2.0, 0)
	if _kind == "post" and _flag:
		_flag.rotation.x = lerpf(0.6, -0.8, _smooth(clampf((u - 0.2) / 0.4, 0.0, 1.0)))
	if _kind == "forage":
		_orbit(_floaters, 14.0, 10.0, u)
	if int(_t * 8.0) % 2 == 0:
		var tint := Color(1.0, 0.82, 0.35)
		if _kind == "water":
			tint = Color(0.35, 0.65, 0.95)
		elif _kind == "stove":
			tint = Color(1.0, 0.42, 0.1)
		_spark(_focus + Vector3(0, 12, 0), tint)


func _tick_feed(pet: Node3D, u: float) -> void:
	var walk := clampf(u / 0.22, 0.0, 1.0)
	var at := _origin.lerp(_origin + Vector3(12, 0, 8), _smooth(walk))
	var bob := 0.0
	if u > 0.22 and u < 0.82:
		bob = absf(sin((u - 0.22) * TAU * 3.0)) * 2.4
		if int(_t * 8.0) % 2 == 0:
			_spark(_bowl.global_position + Vector3(0, 8, 0) if _bowl else at, Color(1.0, 0.82, 0.45))
			_spark(at + Vector3(0, 22, 0), Color(0.95, 0.35, 0.45))
	pet.global_position = at
	pet.global_position.y = bob
	pet.scale = _scale * Vector3(1.0, 0.9 if bob > 1.0 else 1.0, 1.0)


func _tick_clean(pet: Node3D, u: float) -> void:
	pet.global_position = _origin
	pet.global_position.y = sin(u * TAU * 5.0) * 1.2
	pet.rotation.z = sin(u * TAU * 4.0) * 0.12
	_orbit(_floaters, 16.0, 14.0, u)
	if int(_t * 8.0) % 2 == 0:
		_spark(_origin + Vector3(0, 22, 4), Color(1.0, 0.88, 0.35))


func _tick_pat(pet: Node3D, u: float) -> void:
	var squash_y := 1.0 + sin(u * TAU * 2.0) * 0.12
	pet.scale = Vector3(_scale.x * (2.0 - squash_y), _scale.y * squash_y, _scale.z * (2.0 - squash_y))
	pet.global_position = _origin + Vector3(sin(u * TAU) * 2.0, absf(sin(u * TAU * 2.0)) * 3.0, 0)
	for i in _floaters.size():
		var heart := _floaters[i]
		if heart:
			heart.global_position = _origin + Vector3(sin(u * TAU + float(i)) * 10.0, 20.0 + u * 18.0 + float(i) * 2.0, 6.0)
	_ring_at(_origin, 8.0 + u * 10.0)


func _tick_power(pet: Node3D, u: float) -> void:
	var lift := absf(sin(u * TAU * 3.0))
	pet.global_position = _origin + Vector3(0, lift * 3.0, 0)
	pet.scale = _scale * Vector3(1.06, 0.92 + lift * 0.1, 1.06)
	if _bell:
		_bell.global_position = _origin + Vector3(16, 12.0 + lift * 12.0, 6)
	if int(_t * 9.0) % 2 == 0:
		_spark(_origin + Vector3(8, 14, 2), Color(0.55, 0.8, 1.0))


func _tick_agi(pet: Node3D, u: float) -> void:
	var x := sin(u * TAU * 2.0) * 18.0
	var z := sin(u * TAU * 4.0) * 8.0
	pet.global_position = _origin + Vector3(x, absf(sin(u * TAU * 6.0)) * 1.4, z)
	if int(_t * 12.0) % 2 == 0:
		_dust(pet.global_position)


func _tick_stam(pet: Node3D, u: float) -> void:
	var hop := absf(sin(u * TAU * 3.0))
	pet.global_position = _origin + Vector3(0, hop * 8.0, 0)
	if hop > 0.85:
		_ring_at(_origin, 6.0 + hop * 6.0)
	if int(_t * 8.0) % 2 == 0:
		_spark(_origin + Vector3(0, 16, 0), Color(0.55, 0.85, 0.5))


func _maybe_follow() -> void:
	if host == null or bool(host.get("phase1_manual")):
		return
	var pet := _pet()
	if pet and host.has_method("phase1_follow"):
		host.phase1_follow(pet)


func _mood() -> void:
	var p1 := host.get_node_or_null("/root/Phase1") if host else null
	if p1 == null:
		p1 = get_node_or_null("/root/Phase1")
	var hud: Node = p1.get("hud") if p1 else null
	if hud and hud.has_method("show_emote"):
		hud.call("show_emote", "嘿")


func _route(start: Vector3, goal: Vector3) -> PackedVector3Array:
	var out := PackedVector3Array()
	out.append(start)
	if start.distance_to(goal) <= 90.0 and not _hits_cottage(start, goal):
		out.append(goal)
		return out
	var a := _nearest(start)
	var b := _nearest(goal)
	for key in _shortest(a, b):
		var p: Vector3 = NODES[key]
		if out[out.size() - 1].distance_to(p) > 1.5:
			out.append(p)
	if out[out.size() - 1].distance_to(goal) > 1.5:
		out.append(goal)
	return out


func _nearest(p: Vector3) -> String:
	var best := "home"
	var best_d := INF
	for key in NODES:
		var node: Vector3 = NODES[key]
		var d := p.distance_to(node)
		if d < best_d and not _hits_cottage(p, node):
			best_d = d
			best = key
	if best_d == INF:
		for key in NODES:
			var node: Vector3 = NODES[key]
			var d := p.distance_to(node)
			if d < best_d:
				best_d = d
				best = key
	return best


func _shortest(a: String, b: String) -> Array:
	if a == b:
		return [a]
	var dist := {}
	var prev := {}
	var open: Array[String] = []
	for key in NODES:
		dist[key] = INF
		open.append(key)
	dist[a] = 0.0
	while not open.is_empty():
		var pick := open[0]
		for key in open:
			if float(dist[key]) < float(dist[pick]):
				pick = key
		open.erase(pick)
		if pick == b:
			break
		for link in LINKS:
			if link[0] != pick and link[1] != pick:
				continue
			var nxt: String = link[1] if link[0] == pick else link[0]
			if not open.has(nxt) and nxt != b and float(dist[nxt]) < INF:
				continue
			var step: float = (NODES[pick] as Vector3).distance_to(NODES[nxt])
			var alt := float(dist[pick]) + step
			if alt < float(dist[nxt]):
				dist[nxt] = alt
				prev[nxt] = pick
	var chain: Array = [b]
	var cursor := b
	var guard := 0
	while cursor != a and guard < 16:
		guard += 1
		if not prev.has(cursor):
			return [a, b]
		cursor = str(prev[cursor])
		chain.push_front(cursor)
	return chain


func _length(path: PackedVector3Array) -> float:
	var total := 0.0
	for i in range(1, path.size()):
		total += path[i - 1].distance_to(path[i])
	return total


func _hits_cottage(a: Vector3, b: Vector3) -> bool:
	for i in 13:
		var p := a.lerp(b, float(i) / 12.0)
		if p.x > 46.0 and p.x < 120.0 and p.z > -100.0 and p.z < -42.0:
			return true
	return false


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


func _ensure_pool() -> void:
	if _pool_root != null or zones == null:
		return
	_pool_root = Node3D.new()
	_pool_root.name = "SparkPool"
	zones.add_child(_pool_root)
	var mesh := SphereMesh.new()
	mesh.radius = 1.0
	mesh.height = 2.0
	for i in POOL_N:
		var bit := MeshInstance3D.new()
		bit.name = "Spark_%d" % i
		bit.mesh = mesh
		var mat := StandardMaterial3D.new()
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		mat.emission_enabled = true
		mat.emission_energy_multiplier = 1.2
		bit.material_override = mat
		bit.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		bit.visible = false
		_pool_root.add_child(bit)
		_free.append(bit)
	_ring = MeshInstance3D.new()
	_ring.name = "SparkRing"
	var torus := TorusMesh.new()
	torus.inner_radius = 1.0
	torus.outer_radius = 1.08
	_ring.mesh = torus
	var ring_mat := StandardMaterial3D.new()
	ring_mat.albedo_color = Color(1.0, 0.82, 0.35, 0.85)
	ring_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	ring_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_ring.material_override = ring_mat
	_ring.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_ring.visible = false
	_pool_root.add_child(_ring)
	spark_runtime_allocs = 0


func _spark(pos: Vector3, color: Color) -> void:
	_puff(pos, color, 3.0, 0.28, 7.0)


func _dust(pos: Vector3) -> void:
	_puff(pos, Color(0.62, 0.5, 0.34, 0.72), 2.2, 0.34, 2.4)


func _puff(pos: Vector3, color: Color, scale: float, life: float, rise: float) -> void:
	_ensure_pool()
	if _free.is_empty():
		return
	var bit: MeshInstance3D = _free.pop_back()
	var mat := bit.material_override as StandardMaterial3D
	if mat:
		mat.albedo_color = color
		mat.emission = Color(color.r, color.g, color.b)
	bit.scale = Vector3.ONE * scale
	bit.global_position = pos
	bit.visible = true
	_busy.append({"n": bit, "life": life, "max": life, "rise": rise, "y": pos.y})


func _tick_puffs(dt: float) -> void:
	var keep: Array[Dictionary] = []
	for item in _busy:
		var bit: MeshInstance3D = item["n"]
		if bit == null or not is_instance_valid(bit):
			continue
		item["life"] = float(item["life"]) - dt
		var y := float(item["y"]) + float(item["rise"]) * dt
		item["y"] = y
		bit.global_position.y = y
		if float(item["life"]) <= 0.0:
			bit.visible = false
			_free.append(bit)
		else:
			keep.append(item)
	_busy = keep


func _ring_at(pos: Vector3, radius: float) -> void:
	if _ring == null:
		return
	_ring.visible = true
	_ring.global_position = pos + Vector3(0, 0.3, 0)
	_ring.scale = Vector3(radius, radius, radius)


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
		node.global_position = _origin + Vector3(cos(ang) * radius, height + sin(u * TAU + float(i)) * 4.0, sin(ang) * radius * 0.6)


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
	bit.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
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


func _sphere(color: Color, radius: float, pos: Vector3) -> MeshInstance3D:
	var bit := MeshInstance3D.new()
	var mesh := SphereMesh.new()
	mesh.radius = radius
	mesh.height = radius * 2.0
	bit.mesh = mesh
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	bit.material_override = mat
	bit.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
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
