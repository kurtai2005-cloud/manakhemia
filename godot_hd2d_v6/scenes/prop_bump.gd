extends Node
## Spring-damper prop bump (v6.8 prototype). No RigidBody, no extra draw calls.
## Parameters: res://data/prop_bump.json (遊美 fills pivot/mass/tilt later).
## Grass reserve: RenderingServer.global_shader_parameter_set(pet_pos_ws) each tick.
## Temporary uniform name pet_pos_ws — rename when 遊美 confirms.
## Audio hooks for 遊音 (signals only, no audio files):
##   prop_bump_hit(type, strength 0-1 from 團絨 speed, pos)
##   prop_settle(type)
##   grass_rustle(intensity, pos)

signal prop_bump_hit(type: String, strength: float, pos: Vector3)
signal prop_settle(type: String)
signal grass_rustle(intensity: float, pos: Vector3)

var host: Node = null

const CFG_PATH := "res://data/prop_bump.json"
const SETTLE_EPS_PUSH := 0.04

var _cfg: Dictionary = {}
var _param_name := "pet_pos_ws"
var _enabled := true
var _items: Array[Dictionary] = []
var _blocked: Array[Rect2] = []
var _bounds := Rect2(-140, -110, 290, 200)
var _pet_radius := 12.0
var _active_radius := 80.0
var _impulse_scale := 1.0
var _cooldown := 0.18
var _settle_tilt := deg_to_rad(0.12)
var _settle_speed := 0.4

var _pet_last_xz := Vector2.ZERO
var _pet_vel_xz := Vector2.ZERO
var _have_pet_last := false

# Cost stats (usec).
var _cost_frames := 0
var _cost_sum_us := 0
var _cost_max_us := 0
var _cost_last_us := 0
var _cost_last_ticked := 0
var _cost_last_active := 0
var _hit_log: PackedStringArray = PackedStringArray()

# Demo / GIF path.
var _demo := false
var _demo_i := 0
var _demo_wait := 0.0
var _demo_targets: Array[Vector3] = []
var _demo_done := false

# 遊音: per-prop audio cooldown (0.25s) is separate from the physics contact cooldown.
const AUDIO_HIT_COOL := 0.25
const RUSTLE_PERIOD := 0.3
const RUSTLE_MOVE := 8.0
const SPEED_REF := 48.0
var _audio_cool: Dictionary = {}
var _rustle_wait := 0.0
var _rustle_rects: Array[Rect2] = []
var _audio_hit_n := 0
var _audio_settle_n := 0
var _audio_rustle_n := 0


func _ready() -> void:
	if host == null:
		host = get_parent()
	_load_cfg()
	_discover()
	_demo = OS.get_environment("HD2D_BUMP_DEMO") == "1"
	if _demo:
		# Approach points 14 wu from the prop (inside bump radius, outside walk-block 10
		# so a later path does not have to walk through the prop). Waypoints avoid crates.
		# Approach points stay inside bump radius but outside walk-block 10.
		# Extra waypoints cross the lawn tufts and the two flower beds (bend preview).
		_demo_targets = [
			Vector3(0.0, 0, 40.0),    # lawn tufts
			Vector3(8.8, 0, 7.2),     # into CrateWood (22, 18)
			Vector3(36.0, 0, 6.0),    # around the crate
			Vector3(35.0, 0, 22.0),   # into pot_S (49, 22)
			Vector3(48.0, 0, 30.0),   # toward the can
			Vector3(48.0, 0, 34.0),   # into can (48, 48)
			Vector3(20.0, 0, -12.0),
			Vector3(-20.0, 0, -18.0), # toward bed (-47, -31)
			Vector3(-47.0, 0, -18.0), # along flower-bed cards
			Vector3(-70.0, 0, -18.0),
			Vector3(40.0, 0, -16.0),
			Vector3(55.0, 0, -8.0),   # second bed (55, -20)
		]
		_demo_wait = 0.35
	_setup_rustle_rects()
	print("prop_bump ready items=", _items.size(), " param=", _param_name, " enabled=", _enabled, " types=", ",".join(_type_names()), " rustle_rects=", _rustle_rects.size())


func _process(dt: float) -> void:
	# Simulation is ticked from capture._tick_play (also Low). Demo only steers the walk target.
	if _demo:
		_tick_demo(dt)


func tick(dt: float) -> void:
	var t0 := Time.get_ticks_usec()
	var pet: Node3D = host.get("_pet") as Node3D if host else null
	if pet == null:
		return
	var pz := Vector2(pet.global_position.x, pet.global_position.z)
	if _have_pet_last and dt > 1e-6:
		_pet_vel_xz = (pz - _pet_last_xz) / dt
	else:
		_pet_vel_xz = Vector2.ZERO
	_pet_last_xz = pz
	_have_pet_last = true
	_set_pet_shader(pet)
	if not _enabled:
		_account(t0, 0, 0)
		return

	var pet_moving := _pet_vel_xz.length() > 2.0
	var n_near := 0
	var n_tick := 0
	for i in _items.size():
		var it: Dictionary = _items[i]
		var pivot: Node3D = it["pivot"]
		if pivot == null or not is_instance_valid(pivot):
			continue
		var rest: Vector2 = it["rest"]
		var d := pz.distance_to(rest)
		var settled: bool = bool(it["settled"])
		if d > _active_radius and settled:
			continue
		n_near += 1
		_tick_audio_cool(it, dt)
		_try_impulse(it, pz, d, dt)
		var need: bool = pet_moving or not settled or d <= float(it["radius"]) + _pet_radius
		if not need:
			continue
		n_tick += 1
		_integrate(it, dt)
		_apply_xform(it)
		if not settled and bool(it["settled"]):
			_emit_settle(it)
	_tick_rustle(pet, dt)
	_account(t0, n_near, n_tick)


func smoke_drive_hits() -> void:
	# Called from capture smoke (no visible frames). Lunge 團絨 into crate / pot / can.
	var pet: Node3D = host.get("_pet") as Node3D if host else null
	if pet == null:
		return
	var start := pet.position
	for typ in ["crate", "pot_s", "can"]:
		var it := _first_of(typ)
		if it.is_empty():
			print("prop_bump smoke missing type ", typ)
			continue
		var rest: Vector2 = it["rest"]
		var rad := float(it["radius"]) + _pet_radius
		var dir := (rest - Vector2(0, 0))
		if dir.length() < 0.001:
			dir = Vector2(1, 0)
		dir = dir.normalized()
		# Start just outside, then step in so contact is guaranteed (walk_blocked would stop short).
		var outer := rest - dir * (rad + 2.0)
		pet.position = Vector3(outer.x, float(host.get("PET_CENTER_Y") if host.get("PET_CENTER_Y") != null else 29.0), outer.y)
		_have_pet_last = true
		_pet_last_xz = outer
		tick(0.05)
		var inner := rest - dir * (rad - 2.5)
		pet.position = Vector3(inner.x, pet.position.y, inner.y)
		tick(0.05)
		for _j in 18:
			tick(0.05)
	# grass_rustle: walk across the lawn and a flower bed while moving.
	for dest in [Vector2(0, 40), Vector2(-47, -18), Vector2(55, -8)]:
		var from := Vector2(pet.position.x, pet.position.z)
		_have_pet_last = true
		_pet_last_xz = from
		for step in 12:
			var u := float(step + 1) / 12.0
			var p := from.lerp(dest, u)
			pet.position = Vector3(p.x, pet.position.y, p.y)
			tick(0.05)
		for _k in 8:
			tick(0.05)
	pet.position = start
	tick(0.0)
	_print_cost("smoke")
	print("prop_bump hits=", ", ".join(_hit_log) if _hit_log.size() else "(none)")
	print("audio smoke hits=", _audio_hit_n, " settles=", _audio_settle_n, " rustles=", _audio_rustle_n)


func _first_of(typ: String) -> Dictionary:
	var prefer := {
		"crate": Vector2(22, 18),
		"pot_s": Vector2(49, 22),
		"can": Vector2(48, 48),
	}
	var want: Vector2 = prefer.get(typ, Vector2.ZERO)
	var best: Dictionary = {}
	var best_d := 1.0e9
	for it in _items:
		if str(it["type"]) != typ:
			continue
		var rest: Vector2 = it["rest"]
		var d := rest.distance_to(want)
		if d < best_d:
			best_d = d
			best = it
	return best


func _load_cfg() -> void:
	var f := FileAccess.open(CFG_PATH, FileAccess.READ)
	if f == null:
		push_warning("prop_bump missing " + CFG_PATH)
		_cfg = {}
		return
	var data = JSON.parse_string(f.get_as_text())
	f.close()
	if typeof(data) != TYPE_DICTIONARY:
		push_warning("prop_bump JSON is not an object")
		_cfg = {}
		return
	_cfg = data
	_enabled = bool(_cfg.get("enabled", true))
	_pet_radius = float(_cfg.get("pet_radius", 12.0))
	_active_radius = float(_cfg.get("active_radius", 80.0))
	_impulse_scale = float(_cfg.get("impulse_scale", 1.0))
	_cooldown = float(_cfg.get("contact_cooldown", 0.18))
	_settle_tilt = deg_to_rad(float(_cfg.get("settle_tilt_deg", 0.12)))
	_settle_speed = float(_cfg.get("settle_speed", 0.4))
	_param_name = str(_cfg.get("pet_shader_param", "pet_pos_ws"))
	var b: Dictionary = _cfg.get("bounds", {})
	_bounds = Rect2(
		float(b.get("x_min", -140.0)),
		float(b.get("z_min", -110.0)),
		float(b.get("x_max", 150.0)) - float(b.get("x_min", -140.0)),
		float(b.get("z_max", 90.0)) - float(b.get("z_min", -110.0))
	)
	_blocked.clear()
	for r in _cfg.get("blocked_rects", []):
		if typeof(r) != TYPE_DICTIONARY:
			continue
		var rd: Dictionary = r
		_blocked.append(Rect2(float(rd.get("x", 0)), float(rd.get("z", 0)), float(rd.get("w", 0)), float(rd.get("h", 0))))


func _discover() -> void:
	_items.clear()
	if host == null:
		return
	var used: Dictionary = {}
	# Groups first (crate + lid).
	for g in _cfg.get("groups", []):
		if typeof(g) != TYPE_DICTIONARY:
			continue
		var gd: Dictionary = g
		var typ := str(gd.get("type", "crate"))
		var parent_pat := str(gd.get("parent_match", "CrateWood"))
		var attach_pats: Array = gd.get("attach_match", [])
		var same_xz := float(gd.get("same_xz_wu", 2.0))
		for n in _all_nodes(host):
			if not (n is Node3D):
				continue
			if n.get_parent() != host:
				continue
			if used.has(n):
				continue
			if not _name_matches(n.name, parent_pat):
				continue
			var typc := _type_cfg(typ)
			if typc.is_empty():
				continue
			var attaches: Array[Node3D] = []
			for m in _all_nodes(host):
				if m == n or not (m is Node3D) or used.has(m):
					continue
				var ok := false
				for pat in attach_pats:
					if _name_matches(m.name, str(pat)):
						ok = true
						break
				if not ok:
					continue
				var d := Vector2(n.global_position.x - m.global_position.x, n.global_position.z - m.global_position.z).length()
				if d <= same_xz:
					attaches.append(m as Node3D)
			_register(n as Node3D, typ, typc, attaches)
			used[n] = true
			for a in attaches:
				used[a] = true
	# Remaining typed props.
	var types: Dictionary = _cfg.get("types", {})
	# Longer match first so CrateWood2 wins over CrateWood.
	var order: Array[String] = []
	for typ in types.keys():
		order.append(str(typ))
	order.sort_custom(func(a: String, b: String) -> bool:
		return _max_match_len(types[a]) > _max_match_len(types[b])
	)
	for typ in order:
		var typc: Dictionary = types[typ]
		if typeof(typc) != TYPE_DICTIONARY:
			continue
		for n in _all_nodes(host):
			if not (n is Node3D) or used.has(n):
				continue
			if n.get_parent() != host:
				continue
			var hit := false
			for pat in typc.get("match", []):
				if _name_matches(n.name, str(pat)):
					hit = true
					break
			if not hit:
				continue
			_register(n as Node3D, typ, typc, [])
			used[n] = true
	print("prop_bump discovered:")
	for it in _items:
		var p: Node3D = it["pivot"]
		print("  ", it["type"], " ", it["src_name"], " rest=", it["rest"], " radius=", it["radius"])


func _max_match_len(typc) -> int:
	var m := 0
	if typeof(typc) != TYPE_DICTIONARY:
		return 0
	for pat in (typc as Dictionary).get("match", []):
		m = maxi(m, str(pat).length())
	return m


func _type_cfg(typ: String) -> Dictionary:
	var types: Dictionary = _cfg.get("types", {})
	if types.has(typ) and typeof(types[typ]) == TYPE_DICTIONARY:
		return types[typ]
	return {}


func _name_matches(n: String, pat: String) -> bool:
	if n == pat:
		return true
	if n.begins_with(pat):
		var rest := n.substr(pat.length())
		# Godot uniquify: pot_S2, can2
		if rest.is_valid_int():
			return true
		# _spawn_copy names: id_x_z  (pot_S_100_-30, can_48_48, mushrooms_-15_35)
		if rest.begins_with("_"):
			var body := rest.substr(1).replace("_", "").replace("-", "")
			return body.is_valid_int()
	return false


func _all_nodes(n: Node) -> Array[Node]:
	var out: Array[Node] = []
	var stack: Array[Node] = [n]
	while stack:
		var cur: Node = stack.pop_back()
		out.append(cur)
		for c in cur.get_children():
			stack.append(c)
	return out


func _register(root: Node3D, typ: String, typc: Dictionary, extra: Array[Node3D]) -> void:
	var rest := Vector2(root.global_position.x, root.global_position.z)
	var pivot_y := float(typc.get("pivot_y", 0.0))
	var pivot := Node3D.new()
	pivot.name = "BumpPivot_%s" % typ
	var parent := root.get_parent()
	if parent == null:
		return
	parent.add_child(pivot)
	pivot.global_position = Vector3(rest.x, pivot_y, rest.y)
	# Keep sibling index near the original so draw order stays similar (no new geometry).
	var nodes: Array[Node3D] = [root]
	for e in extra:
		nodes.append(e)
	for n in nodes:
		var xf := n.global_transform
		var old_parent := n.get_parent()
		if old_parent:
			old_parent.remove_child(n)
		pivot.add_child(n)
		n.global_transform = xf
	var it := {
		"type": typ,
		"src_name": root.name,
		"pivot": pivot,
		"rest": rest,
		"rest_push": Vector2.ZERO,
		"push": Vector2.ZERO,
		"push_vel": Vector2.ZERO,
		"lean": Vector2.ZERO,
		"lean_vel": Vector2.ZERO,
		"cool": 0.0,
		"inside": false,
		"settled": true,
		"mass": maxf(float(typc.get("mass", 1.0)), 0.05),
		"radius": float(typc.get("radius", 8.0)),
		"max_tilt": deg_to_rad(float(typc.get("max_tilt_deg", 8.0))),
		"stiffness": float(typc.get("stiffness", 70.0)),
		"damping": float(typc.get("damping", 6.0)),
		"max_push": float(typc.get("max_push", 4.0)),
		"residual_frac": float(typc.get("residual_frac", 0.2)),
		"angular_gain": float(typc.get("angular_gain", 0.04)),
		"linear_gain": float(typc.get("linear_gain", 0.1)),
	}
	_items.append(it)


func _try_impulse(it: Dictionary, pet_xz: Vector2, d_to_rest: float, dt: float) -> void:
	var cool: float = it["cool"]
	if cool > 0.0:
		it["cool"] = maxf(cool - dt, 0.0)
	var rad := float(it["radius"]) + _pet_radius
	# Use current (possibly pushed) position for contact.
	var pivot: Node3D = it["pivot"]
	var cur := Vector2(pivot.global_position.x, pivot.global_position.z)
	var delta := cur - pet_xz
	var dist := delta.length()
	var inside := dist < rad and dist > 0.001
	var was: bool = bool(it["inside"])
	it["inside"] = inside
	if not inside:
		return
	if was and cool > 0.0:
		return
	var nrm := delta / dist
	var approach := _pet_vel_xz.dot(nrm)
	if approach < 4.0 and was:
		return
	if approach < 1.0 and not was:
		approach = 8.0  # entered while almost still: give a small nudge
	var mass: float = it["mass"]
	var j := approach * _impulse_scale / mass
	var lin: float = float(it["linear_gain"])
	var ang: float = float(it["angular_gain"])
	it["push_vel"] = it["push_vel"] + nrm * (j * lin)
	it["lean_vel"] = it["lean_vel"] + nrm * (j * ang)
	var rest_push: Vector2 = it["rest_push"]
	rest_push += nrm * (j * lin * float(it["residual_frac"]) * 0.15)
	it["rest_push"] = _clamp_push(rest_push, float(it["max_push"]), it["rest"])
	it["cool"] = _cooldown
	it["settled"] = false
	var msg := "%s %s v=%.1f" % [str(it["type"]), str(it["src_name"]), approach]
	_hit_log.append(msg)
	print("prop_bump hit ", msg, " at ", cur)
	# 遊音: first frame of contact only (inside and not was), 0.25s per-prop cooldown.
	if not was:
		_emit_hit(it, Vector3(cur.x, 0.0, cur.y))


func _integrate(it: Dictionary, dt: float) -> void:
	if dt <= 0.0:
		return
	var k: float = float(it["stiffness"])
	var damp: float = float(it["damping"])
	var drag := exp(-damp * dt)
	var rest_push: Vector2 = it["rest_push"]
	# Linear spring toward residual rest (not always origin — allows leftover slide).
	var push: Vector2 = it["push"]
	var pvel: Vector2 = it["push_vel"]
	pvel += -k * (push - rest_push) * dt
	pvel *= drag
	push += pvel * dt
	push = _clamp_push(push, float(it["max_push"]), it["rest"])
	# If clamp hit a wall, kill outward velocity.
	if push.length() >= float(it["max_push"]) - 0.001:
		if pvel.dot(push) > 0.0:
			pvel = pvel.slide(push.normalized())
	it["push"] = push
	it["push_vel"] = pvel
	# Angular spring toward 0 (tilt always settles upright).
	var lean: Vector2 = it["lean"]
	var lvel: Vector2 = it["lean_vel"]
	lvel += -k * lean * dt
	lvel *= drag
	lean += lvel * dt
	var max_t: float = float(it["max_tilt"])
	var llen := lean.length()
	if llen > max_t and llen > 1e-6:
		lean *= max_t / llen
		if lvel.dot(lean) > 0.0:
			lvel = lvel.slide(lean.normalized())
	it["lean"] = lean
	it["lean_vel"] = lvel
	var settled := lean.length() < _settle_tilt and lvel.length() < _settle_speed \
		and pvel.length() < _settle_speed and (push - rest_push).length() < SETTLE_EPS_PUSH
	it["settled"] = settled


func _clamp_push(push: Vector2, max_push: float, rest: Vector2) -> Vector2:
	if push.length() > max_push and push.length() > 1e-6:
		push = push * (max_push / push.length())
	var world := rest + push
	world.x = clampf(world.x, _bounds.position.x, _bounds.position.x + _bounds.size.x)
	world.y = clampf(world.y, _bounds.position.y, _bounds.position.y + _bounds.size.y)
	for r in _blocked:
		if r.has_point(world):
			# Push back to the nearest edge of the rect.
			world = _closest_outside(r, world)
	return world - rest


func _closest_outside(r: Rect2, p: Vector2) -> Vector2:
	var left := p.x - r.position.x
	var right := r.position.x + r.size.x - p.x
	var top := p.y - r.position.y
	var bot := r.position.y + r.size.y - p.y
	var m := minf(minf(left, right), minf(top, bot))
	if m == left:
		return Vector2(r.position.x - 0.2, p.y)
	if m == right:
		return Vector2(r.position.x + r.size.x + 0.2, p.y)
	if m == top:
		return Vector2(p.x, r.position.y - 0.2)
	return Vector2(p.x, r.position.y + r.size.y + 0.2)


func _apply_xform(it: Dictionary) -> void:
	var pivot: Node3D = it["pivot"]
	var rest: Vector2 = it["rest"]
	var push: Vector2 = it["push"]
	pivot.position.x = rest.x + push.x
	pivot.position.z = rest.y + push.y
	var lean: Vector2 = it["lean"]
	# lean.x = lean toward +X → rotate around +Z; lean.z/+Y in Vector2 is toward +Z → rotate around -X.
	pivot.rotation = Vector3(-lean.y, 0.0, lean.x)


func _set_pet_shader(pet: Node3D) -> void:
	# Temporary name pet_pos_ws (declared in project.godot). Safe if no shader samples it.
	var mode := str(_cfg.get("pet_shader_y_mode", "center"))
	var p := pet.global_position
	if mode == "ground":
		p.y = 0.0
	RenderingServer.global_shader_parameter_set(_param_name, p)


func _account(t0: int, n_near: int, n_tick: int) -> void:
	var us := int(Time.get_ticks_usec() - t0)
	_cost_last_us = us
	_cost_last_active = n_near
	_cost_last_ticked = n_tick
	_cost_frames += 1
	_cost_sum_us += us
	if us > _cost_max_us:
		_cost_max_us = us


func _print_cost(tag: String) -> void:
	var avg := 0.0
	if _cost_frames > 0:
		avg = float(_cost_sum_us) / float(_cost_frames)
	print("prop_bump cost ", tag, " items=", _items.size(), " frames=", _cost_frames,
		" last_us=", _cost_last_us, " avg_us=", snapped(avg, 0.1), " max_us=", _cost_max_us,
		" last_near=", _cost_last_active, " last_ticked=", _cost_last_ticked, " extra_draws=0")


func _tick_demo(dt: float) -> void:
	if _demo_done:
		return
	if _demo_wait > 0.0:
		_demo_wait -= dt
		return
	var pet: Node3D = host.get("_pet") as Node3D if host else null
	if pet == null:
		return
	# Drive 團絨 ourselves. _walk_blocked would cancel a target whose first step
	# clips the prop we just bumped (e.g. crate → pot goes through the crate).
	if host.get("_walk_target") != null:
		host.set("_walk_target", null)
	if _demo_i < _demo_targets.size():
		var dest: Vector3 = _demo_targets[_demo_i]
		var cur := Vector2(pet.position.x, pet.position.z)
		var goal := Vector2(dest.x, dest.z)
		var to := goal - cur
		var dist := to.length()
		var speed := 48.0
		var v = host.get("WALK_SPEED")
		if typeof(v) == TYPE_FLOAT or typeof(v) == TYPE_INT:
			speed = float(v)
		if dist <= maxf(speed * dt, 1.0):
			pet.position.x = dest.x
			pet.position.z = dest.z
			_demo_i += 1
			_demo_wait = 0.35
			print("prop_bump demo arrived ", dest)
			return
		var step := to.normalized() * speed * dt
		pet.position.x += step.x
		pet.position.z += step.y
		return
	_demo_done = true
	_print_cost("demo")
	print("prop_bump demo done hits=", ", ".join(_hit_log) if _hit_log.size() else "(none)")
	get_tree().create_timer(1.4).timeout.connect(func() -> void:
		if OS.get_environment("HD2D_BUMP_DEMO") == "1":
			get_tree().quit(0)
	)


func _type_names() -> PackedStringArray:
	var out := PackedStringArray()
	var types: Dictionary = _cfg.get("types", {})
	for typ in types.keys():
		out.append(str(typ))
	return out


func _tick_audio_cool(it: Dictionary, dt: float) -> void:
	var id: Node3D = it["pivot"]
	if not _audio_cool.has(id):
		return
	var left := float(_audio_cool[id]) - dt
	if left <= 0.0:
		_audio_cool.erase(id)
	else:
		_audio_cool[id] = left


func _emit_hit(it: Dictionary, pos: Vector3) -> void:
	var id: Node3D = it["pivot"]
	if _audio_cool.has(id) and float(_audio_cool[id]) > 0.0:
		return
	_audio_cool[id] = AUDIO_HIT_COOL
	var typ := str(it["type"])
	var strength := clampf(_pet_vel_xz.length() / SPEED_REF, 0.0, 1.0)
	_audio_hit_n += 1
	emit_signal("prop_bump_hit", typ, strength, pos)
	print("audio prop_bump_hit type=", typ, " strength=", snapped(strength, 0.01), " pos=", pos)


func _emit_settle(it: Dictionary) -> void:
	var typ := str(it["type"])
	_audio_settle_n += 1
	emit_signal("prop_settle", typ)
	print("audio prop_settle type=", typ)


func _setup_rustle_rects() -> void:
	_rustle_rects.clear()
	# Garden lawn: GroundInner 256×256 at origin, minus cottage / fence blocked rects.
	# Flower beds are added back so rustle still plays in the beds even near the fence.
	var lawn := Rect2(-128, -128, 256, 256)
	# Membership tests lawn then subtracts blocked_rects, plus beds.
	_rustle_rects.append(lawn)
	# Explicit beds (objects.json bed + dense-fill copy).
	var beds: Array[Rect2] = [
		Rect2(-81.0, -40.0, 68.0, 18.0),  # bed at (-47, -31)
		Rect2(21.0, -29.0, 68.0, 18.0),   # bed_55_-20 (yaw ~-10, approx)
	]
	# Prefer live bed AABBs if the nodes exist.
	if host:
		for n in _all_nodes(host):
			if not (n is Node3D):
				continue
			var nm := str(n.name)
			if nm != "bed" and not nm.begins_with("bed_"):
				continue
			if n.get_parent() != null and str(n.get_parent().name).begins_with("bed"):
				continue
			var p := n as Node3D
			# bed.glb half-extents ≈ 34 x 9; pad 4 wu.
			_rustle_rects.append(Rect2(p.global_position.x - 38.0, p.global_position.z - 13.0, 76.0, 26.0))
		# If no live beds found, use the fallback list (already have lawn as [0]).
		if _rustle_rects.size() == 1:
			for b in beds:
				_rustle_rects.append(b)


func _in_grass_or_bed(xz: Vector2) -> bool:
	# First rect is the lawn; remaining are beds (or extra lawn if discovery failed).
	var in_bed := false
	for i in range(1, _rustle_rects.size()):
		if _rustle_rects[i].has_point(xz):
			in_bed = true
			break
	if in_bed:
		return true
	if _rustle_rects.is_empty() or not _rustle_rects[0].has_point(xz):
		return false
	for r in _blocked:
		if r.has_point(xz):
			return false
	return true


func _tick_rustle(pet: Node3D, dt: float) -> void:
	var speed := _pet_vel_xz.length()
	var xz := Vector2(pet.global_position.x, pet.global_position.z)
	if speed < RUSTLE_MOVE or not _in_grass_or_bed(xz):
		_rustle_wait = 0.0
		return
	_rustle_wait -= dt
	if _rustle_wait > 0.0:
		return
	_rustle_wait = RUSTLE_PERIOD
	var intensity := clampf(speed / SPEED_REF, 0.0, 1.0)
	_audio_rustle_n += 1
	emit_signal("grass_rustle", intensity, pet.global_position)
	print("audio grass_rustle intensity=", snapped(intensity, 0.01), " pos=", pet.global_position)
