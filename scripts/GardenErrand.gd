extends Node
## One spatial errand on the existing garden: walk to a berry, carry it home, then wander.
## Reward is the existing fruit collection, granted once at the drop-off.

const FRUIT_ID := "starberry"
const FRUIT_TEX := "res://art-pet/sprites/hunt/fruits/starberry.png"
const WANT_BERRY := Vector3(48, 0, 36)
const WANT_HOME := Vector3(-40, 0, 16)

var main: Node3D
var walker: Walker
var berry: Sprite3D
var berry_area: Area3D
var home: Sprite3D
var held: Sprite3D
var berry_pos := Vector3.ZERO
var home_pos := Vector3.ZERO


func setup(host: Node3D, body: Walker) -> void:
	main = host
	walker = body
	name = "GardenErrand"
	berry_pos = _free_spot(WANT_BERRY)
	home_pos = _free_spot(WANT_HOME)
	if berry_pos.distance_to(home_pos) < 12.0:
		home_pos = _free_spot(berry_pos + Vector3(-28, 0, -18))
	_ensure_state()
	_build_markers()
	_restore_visual()
	resume_saved()


func resume_saved() -> void:
	var phase := str(_task().get("phase", "idle"))
	if phase == "to_pick":
		walker.set_errand(berry_pos)
	elif phase == "carry":
		walker.set_errand(home_pos)


func player_press() -> String:
	var task: Dictionary = _task()
	var phase := str(task.get("phase", "idle"))
	if _delivered(FRUIT_ID):
		return "already"
	if phase == "idle" or phase == "blocked":
		_set_phase("to_pick")
		walker.set_errand(berry_pos)
		return "start"
	_set_phase("idle")
	walker.clear_errand()
	_restore_visual()
	return "cancel"


func _process(dt: float) -> void:
	if walker == null or not walker.errand_active:
		return
	var pres := _presentation()
	walker.errand_hold = pres != null and pres.has_method("care_active") and bool(pres.call("care_active"))
	if walker.errand_hold:
		return
	var task: Dictionary = _task()
	var phase := str(task.get("phase", "idle"))
	if walker.errand_blocked and phase != "blocked":
		_set_phase("blocked")
		return
	if phase == "to_pick" and _close(berry_pos):
		_set_phase("carry")
		_restore_visual()
		walker.set_errand(home_pos)
	elif phase == "carry" and _close(home_pos):
		_grant_once()
		walker.clear_errand()
		walker.pause_t = 0.4
		_restore_visual()


func _grant_once() -> void:
	var task: Dictionary = _task()
	var done: Array = task.get("delivered", [])
	if FRUIT_ID in done:
		_set_phase("idle")
		return
	if CollectionSystem:
		CollectionSystem.add_fruit(FRUIT_ID, 1)
	done.append(FRUIT_ID)
	task["delivered"] = done
	task["phase"] = "idle"
	task["active_id"] = ""
	_write(task)


func _close(point: Vector3) -> bool:
	return Vector2(walker.global_position.x, walker.global_position.z).distance_to(Vector2(point.x, point.z)) < 1.8


func _free_spot(prefer: Vector3) -> Vector3:
	var feet: Footprints = walker.feet
	var rad := walker.radius
	if feet == null or not feet.blocked(prefer.x, prefer.z, rad):
		return Vector3(prefer.x, 0.0, prefer.z)
	var origin := walker.global_position
	for i in range(1, 16):
		var p := origin.lerp(prefer, 1.0 - float(i) / 16.0)
		if not feet.blocked(p.x, p.z, rad):
			return Vector3(p.x, 0.0, p.z)
	return Vector3(origin.x, 0.0, origin.z)


func _build_markers() -> void:
	var tex := load(FRUIT_TEX) as Texture2D
	berry = _marker("ForageBerry", berry_pos, tex)
	berry_area = Area3D.new()
	berry_area.name = "ForageBerryArea"
	berry_area.collision_layer = 32
	berry_area.collision_mask = 0
	berry_area.input_ray_pickable = true
	var shape := CollisionShape3D.new()
	var sphere := SphereShape3D.new()
	sphere.radius = 8.0
	shape.shape = sphere
	berry_area.add_child(shape)
	berry.add_child(berry_area)
	home = _marker("HomeDrop", home_pos, tex)
	home.modulate = Color(1, 1, 1, 0.45)
	held = Sprite3D.new()
	held.name = "CarriedBerry"
	held.texture = tex
	held.pixel_size = 0.35
	held.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
	held.shaded = true
	held.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	held.visible = false
	walker.add_child(held)
	held.position = Vector3(8, 22, 0)
	var held_area := Area3D.new()
	held_area.name = "CarriedBerryArea"
	held_area.collision_layer = 32
	held_area.collision_mask = 0
	held_area.input_ray_pickable = true
	var held_shape := CollisionShape3D.new()
	var held_sphere := SphereShape3D.new()
	held_sphere.radius = 6.0
	held_shape.shape = held_sphere
	held_area.add_child(held_shape)
	held.add_child(held_area)


func _marker(node_name: String, pos: Vector3, tex: Texture2D) -> Sprite3D:
	var spr := Sprite3D.new()
	spr.name = node_name
	spr.texture = tex
	spr.pixel_size = 0.35
	spr.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
	spr.shaded = true
	spr.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	spr.position = pos + Vector3(0, 6, 0)
	add_child(spr)
	return spr


func _restore_visual() -> void:
	var phase := str(_task().get("phase", "idle"))
	var gone := _delivered(FRUIT_ID)
	if berry:
		berry.visible = not gone and phase != "carry"
	if berry_area:
		berry_area.collision_layer = 32 if berry.visible else 0
	if held:
		held.visible = phase == "carry"
		var held_area := held.get_node_or_null("CarriedBerryArea")
		if held_area:
			held_area.collision_layer = 32 if held.visible else 0
	if home:
		home.visible = not gone


func _presentation() -> Node:
	if main == null:
		return null
	return main.get_node_or_null("Hd2dPresentation")


func _ensure_state() -> void:
	if Sim == null:
		return
	if not Sim.state.has("errand") or not Sim.state["errand"] is Dictionary:
		Sim.state["errand"] = {"phase": "idle", "active_id": "", "delivered": []}


func _task() -> Dictionary:
	_ensure_state()
	return Sim.state["errand"]


func _delivered(id: String) -> bool:
	return id in _task().get("delivered", [])


func _set_phase(phase: String) -> void:
	var task := _task()
	task["phase"] = phase
	task["active_id"] = FRUIT_ID if phase != "idle" else ""
	_write(task)
	_restore_visual()


func _write(task: Dictionary) -> void:
	Sim.state["errand"] = task
	Sim._dirty = true
	Sim._save_now(true)
