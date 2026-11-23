extends Node
## Spatial forage on the existing garden.
## Each delivery has its own number and pays the existing fruit collection once.
## The berry comes back. One stored fruit is one existing meal.
## The first meal unlocks rest: the pet walks home, uses the existing door, and sleeps.

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
var home_area: Area3D


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
	elif phase == "carry" or phase == "to_eat" or phase == "to_rest":
		walker.set_errand(home_pos)


func press_target(area: Area3D) -> String:
	if area != null and str(area.name) == "HomeDropArea":
		return press_home()
	return player_press()


func player_press() -> String:
	var task: Dictionary = _task()
	var phase := str(task.get("phase", "idle"))
	if phase == "idle" or phase == "blocked":
		var paid := int(task.get("paid_through", 0))
		if int(task.get("open_seq", 0)) <= paid:
			task["open_seq"] = paid + 1
		_set_phase("to_pick")
		walker.set_errand(berry_pos)
		return "start"
	_set_phase("idle")
	walker.clear_errand()
	_restore_visual()
	return "cancel"


func press_home() -> String:
	var phase := str(_task().get("phase", "idle"))
	if phase == "to_eat" or phase == "to_rest":
		_set_phase("idle")
		walker.clear_errand()
		return "cancel"
	if phase != "idle":
		return "busy"
	# Tired enough to rest on its own: rest wins over another meal.
	if _rest_ready() and float(_needs().get("energy", 100)) < 50.0:
		_clear_care()
		_set_phase("to_rest")
		walker.set_errand(home_pos)
		return "rest"
	if _fruit_count() > 0 and not _feed_blocked():
		_clear_care()
		_set_phase("to_eat")
		walker.set_errand(home_pos)
		return "eat"
	if _rest_ready():
		_clear_care()
		_set_phase("to_rest")
		walker.set_errand(home_pos)
		return "rest"
	if _fruit_count() > 0 and float(_needs().get("hunger", 0)) >= Sim.FEED_REFUSE_AT:
		return "full"
	return "none"


func _process(dt: float) -> void:
	if walker == null:
		return
	var task: Dictionary = _task()
	var phase := str(task.get("phase", "idle"))
	if phase == "asleep":
		_watch_rest()
		return
	if not walker.errand_active:
		_maybe_rest()
		return
	var pres := _presentation()
	walker.errand_hold = pres != null and pres.has_method("care_active") and bool(pres.call("care_active"))
	if walker.errand_hold:
		return
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
	elif phase == "to_eat" and _close(home_pos):
		_eat_one()
		walker.clear_errand()
		walker.pause_t = 0.6
		_restore_visual()
	elif phase == "to_rest" and _close(home_pos):
		walker.clear_errand()
		_begin_rest()


func _grant_once() -> void:
	var task: Dictionary = _task()
	var phase := str(task.get("phase", "idle"))
	var open := int(task.get("open_seq", 0))
	var paid := int(task.get("paid_through", 0))
	if open <= 0:
		if phase != "carry":
			_set_phase("idle")
			return
		if _delivered(FRUIT_ID) and paid > 0:
			_set_phase("idle")
			return
		open = paid + 1
	if open <= paid:
		_set_phase("idle")
		return
	if CollectionSystem:
		CollectionSystem.add_fruit(FRUIT_ID, 1)
	var done: Array = task.get("delivered", [])
	if FRUIT_ID not in done:
		done.append(FRUIT_ID)
	task["delivered"] = done
	task["paid_through"] = open
	task["open_seq"] = 0
	task["phase"] = "idle"
	task["active_id"] = ""
	_write(task)
	_restore_visual()


func _eat_one() -> Dictionary:
	if _fruit_count() <= 0:
		_set_phase("idle")
		return {"ok": false, "reason": "none"}
	if _feed_blocked():
		_set_phase("idle")
		return {"ok": false, "reason": "blocked"}
	var rec: Dictionary = Sim.feed("meal")
	if not bool(rec.get("ok", false)):
		_set_phase("idle")
		return rec
	if CollectionSystem:
		CollectionSystem.spend_fruit(FRUIT_ID, 1)
	var task := _task()
	task["meals"] = int(task.get("meals", 0)) + 1
	task["phase"] = "idle"
	task["active_id"] = ""
	_write(task)
	var pres := _presentation()
	if pres and pres.has_method("play_care"):
		pres.call("play_care", "eat")
	return rec


func _begin_rest() -> void:
	if main == null or bool(main.get("in_interior")):
		return
	Sim.set_sleeping(true)
	if main.has_method("enter_house"):
		main.call("enter_house", true)
	var task := _task()
	task["phase"] = "asleep"
	task["active_id"] = ""
	_write(task)
	_restore_visual()


func _watch_rest() -> void:
	var energy := float(_needs().get("energy", 0))
	var sleeping := bool(Sim.state.get("sleeping", false))
	if sleeping and energy < Sim.SLEEP_WAKE_AT:
		return
	Sim.set_sleeping(false)
	if main and bool(main.get("in_interior")) and main.has_method("exit_house"):
		main.call("exit_house", true)
	_set_phase("idle")
	walker.pause_t = 0.4


func _maybe_rest() -> void:
	if str(_task().get("phase", "idle")) != "idle":
		return
	if not _rest_ready():
		return
	if float(_needs().get("energy", 100)) >= 50.0:
		return
	var pres := _presentation()
	if pres and pres.has_method("care_active") and bool(pres.call("care_active")):
		return
	_set_phase("to_rest")
	walker.set_errand(home_pos)


func _rest_ready() -> bool:
	if int(_task().get("meals", 0)) < 1:
		return false
	if bool(Sim.state.get("sleeping", false)):
		return false
	return float(_needs().get("energy", 100)) < Sim.SLEEP_MIN_ENERGY


func _feed_blocked() -> bool:
	if str(Sim.state.get("stage", "egg")) == "egg":
		return true
	if bool(Sim.state.get("sleeping", false)):
		return true
	return float(_needs().get("hunger", 0)) >= Sim.FEED_REFUSE_AT


func _needs() -> Dictionary:
	var n: Variant = Sim.state.get("needs", {})
	return n if n is Dictionary else {}


func _fruit_count() -> int:
	if CollectionSystem == null:
		return 0
	return int(CollectionSystem.fruit_count(FRUIT_ID))


func _close(point: Vector3) -> bool:
	return Vector2(walker.global_position.x, walker.global_position.z).distance_to(Vector2(point.x, point.z)) < 1.2


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
	home_area = Area3D.new()
	home_area.name = "HomeDropArea"
	home_area.collision_layer = 32
	home_area.collision_mask = 0
	home_area.input_ray_pickable = true
	var home_shape := CollisionShape3D.new()
	var home_sphere := SphereShape3D.new()
	home_sphere.radius = 6.0
	home_shape.shape = home_sphere
	home_area.add_child(home_shape)
	home.add_child(home_area)
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
	var inside := main != null and bool(main.get("in_interior"))
	if berry:
		berry.visible = phase != "carry" and not inside
	if berry_area:
		berry_area.collision_layer = 32 if berry.visible else 0
	if held:
		held.visible = phase == "carry"
		var held_area := held.get_node_or_null("CarriedBerryArea")
		if held_area:
			held_area.collision_layer = 32 if held.visible else 0
	if home:
		home.visible = not inside
		var fed := int(_task().get("meals", 0)) >= 1
		home.modulate = Color(1, 1, 1, 1.0 if fed else 0.45)
	if home_area:
		home_area.collision_layer = 32 if home != null and home.visible else 0


func _clear_care() -> void:
	var pres := _presentation()
	if pres and pres.has_method("cancel_care"):
		pres.call("cancel_care")


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
