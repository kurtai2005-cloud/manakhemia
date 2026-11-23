extends Node
## Spatial forage on the existing garden.
## Each delivery has its own number and pays the existing fruit collection once.
## The berry comes back. One stored fruit is one existing meal.
## The first meal unlocks rest: the pet walks home, uses the existing door, and sleeps.

const FRUIT_ID := "starberry"
const FRUIT_TEX := "res://art-pet/sprites/hunt/fruits/starberry.png"
# Open foreground grass, in view of the opening camera and off the crate cluster
# and the left canopy. The rest mark is the door stand, not this drop point.
const WANT_BERRY := Vector3(46, 0, 40)
const WANT_HOME := Vector3(28, 0, 22)
const TOSS_ARC_SEC := 1.05
const TOSS_ARC_H := 26.0

var main: Node3D
var walker: Walker
var berry: Sprite3D
var berry_area: Area3D
var home: Sprite3D
var held: Sprite3D
var berry_pos := Vector3.ZERO
var home_pos := Vector3.ZERO
var home_area: Area3D
var goal_bubble: Sprite3D
var toss: Sprite3D
var rest_mark: Sprite3D
var toss_from := Vector3.ZERO
var toss_land := Vector3.ZERO
var toss_age := 0.0
var _after_eat := ""
var _saw_eat := false


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
	elif phase == "toss" or phase == "to_eat":
		_place_toss(_toss_land())
		if phase == "toss":
			var task := _task()
			task["phase"] = "to_eat"
			_write(task)
		walker.set_errand(_toss_land())
	elif phase == "carry":
		walker.set_errand(home_pos)
	elif phase == "to_rest":
		var stand: Vector3 = _door_stand()
		walker.set_errand(stand)


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


func offer() -> String:
	if rest_offered() and float(_needs().get("energy", 100)) < 50.0:
		return "rest"
	if food_offered():
		return "food"
	if rest_offered():
		return "rest"
	return ""


func food_offered() -> bool:
	return food_choice() and not _feed_blocked()


func food_choice() -> bool:
	if str(_task().get("phase", "idle")) != "idle" or _fruit_count() <= 0:
		return false
	if str(Sim.state.get("stage", "egg")) == "egg":
		return false
	if bool(Sim.state.get("sleeping", false)):
		return false
	return true


func rest_offered() -> bool:
	return str(_task().get("phase", "idle")) == "idle" and _rest_ready()


func press_food() -> String:
	var phase := str(_task().get("phase", "idle"))
	if phase == "toss" or phase == "to_eat":
		if not _toss_consumed():
			_cancel_toss()
			return "cancel"
		return "busy"
	if phase != "idle":
		return "busy"
	if _fruit_count() <= 0:
		return "none"
	if _feed_blocked():
		return "full"
	_clear_care()
	_begin_toss()
	return "toss"


func press_rest() -> String:
	if str(_task().get("phase", "idle")) != "idle":
		return "busy"
	_clear_care()
	return _start_door_rest()


func press_home() -> String:
	var phase := str(_task().get("phase", "idle"))
	if phase == "toss" or phase == "to_eat" or phase == "to_rest":
		if phase != "to_rest" and not _toss_consumed():
			_cancel_toss()
		else:
			_set_phase("idle")
			walker.clear_errand()
		if main:
			main.set("_door_pending", false)
		return "cancel"
	if phase != "idle":
		return "busy"
	var shown := offer()
	if shown == "food":
		return press_food()
	if shown == "rest":
		return press_rest()
	if _fruit_count() > 0 and float(_needs().get("hunger", 0)) >= Sim.FEED_REFUSE_AT:
		return "full"
	return "none"


func _process(dt: float) -> void:
	if walker == null:
		return
	var task: Dictionary = _task()
	var phase := str(task.get("phase", "idle"))
	_tick_reaction()
	if phase == "asleep":
		_watch_rest()
		_pulse_markers(phase)
		return
	if phase == "toss":
		_fly_toss(dt)
		_pulse_markers(phase)
		return
	if phase == "to_rest":
		_watch_door()
		_pulse_markers(phase)
		return
	_pulse_markers(phase)
	if not walker.errand_active:
		_maybe_rest()
		return
	var pres := _presentation()
	walker.errand_hold = pres != null and pres.has_method("care_active") and bool(pres.call("care_active"))
	if walker.errand_hold:
		return
	if walker.errand_blocked and (phase == "to_pick" or phase == "carry" or phase == "to_eat"):
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
	elif phase == "to_eat" and _close(_toss_land()):
		_eat_one()
		walker.clear_errand()
		# Eat is 1s and the happy clip after it is 2s. The pause has to cover both.
		walker.pause_t = 3.6
		_restore_visual()
	elif phase == "to_rest":
		_watch_door()


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
		CollectionSystem.discover_fruit(FRUIT_ID)
	if Sim and Sim.has_method("credit_egg_exploration"):
		Sim.credit_egg_exploration()
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
	var task := _task()
	var open := int(task.get("toss_seq", 0))
	var paid := int(task.get("toss_paid", 0))
	if open <= paid:
		_hide_toss()
		_set_phase("idle")
		return {"ok": false, "reason": "already"}
	if _fruit_count() <= 0 or _feed_blocked():
		_hide_toss()
		_set_phase("idle")
		return {"ok": false, "reason": "full" if _feed_blocked() else "none"}
	var rec: Dictionary = Sim.feed("meal")
	if not bool(rec.get("ok", false)):
		_hide_toss()
		_set_phase("idle")
		return rec
	if CollectionSystem:
		CollectionSystem.spend_fruit(FRUIT_ID, 1)
	task = _task()
	task["meals"] = int(task.get("meals", 0)) + 1
	task["toss_paid"] = open
	task["phase"] = "idle"
	task["active_id"] = ""
	_write(task)
	var pres := _presentation()
	if pres and pres.has_method("play_care"):
		pres.call("play_care", "eat")
		_after_eat = "eat"
		_saw_eat = false
	return rec


func _start_door_rest() -> String:
	if main == null or bool(main.get("in_interior")):
		return "busy"
	if not _rest_ready():
		return "none"
	walker.clear_errand()
	var pres := _presentation()
	if pres == null or not pres.has_method("begin_approach") or not bool(pres.call("begin_approach")):
		return "blocked"
	var stand: Vector3 = pres.get("goal")
	walker.set_errand(stand)
	main.set("_door_pending", true)
	_set_phase("to_rest")
	return "rest"


func _watch_door() -> void:
	var pres := _presentation()
	if pres != null and bool(pres.get("arrived")):
		walker.clear_errand()
	if pres != null and bool(pres.get("blocked_stop")):
		var stand: Vector3 = pres.get("goal")
		if walker.global_position.distance_to(stand) > 15.0:
			pres.set("blocked_stop", false)
			pres.set("approaching", true)
			walker.set_errand(stand)
			return
		walker.clear_errand()
		_set_phase("idle")
		return
	if main != null and bool(main.get("in_interior")):
		walker.clear_errand()
		Sim.set_sleeping(true)
		if bool(Sim.state.get("preview_fixture", false)):
			var needs: Dictionary = Sim.state.get("needs", {})
			needs["energy"] = maxf(0.0, float(Sim.SLEEP_WAKE_AT) - 1.0)
			Sim.state["needs"] = needs
		var task := _task()
		task["phase"] = "asleep"
		task["active_id"] = ""
		_write(task)
		_restore_visual()


func _watch_rest() -> void:
	var energy := float(_needs().get("energy", 0))
	var sleeping := bool(Sim.state.get("sleeping", false))
	var inside := main != null and bool(main.get("in_interior"))
	if not inside:
		if sleeping:
			Sim.set_sleeping(false)
		_set_phase("idle")
		walker.pause_t = 0.4
		return
	if sleeping and energy < Sim.SLEEP_WAKE_AT:
		return
	Sim.set_sleeping(false)
	if main.has_method("exit_house"):
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
	_start_door_rest()


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
	berry.pixel_size = 1.25
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
	held.pixel_size = 1.15
	held.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
	held.shaded = false
	held.no_depth_test = true
	held.render_priority = 12
	held.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	held.visible = false
	walker.add_child(held)
	held.position = Vector3(0, 48, 0)
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
	goal_bubble = Sprite3D.new()
	goal_bubble.name = "GoalBubble"
	goal_bubble.pixel_size = 0.55
	goal_bubble.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
	goal_bubble.shaded = false
	goal_bubble.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	goal_bubble.visible = false
	walker.add_child(goal_bubble)
	goal_bubble.position = Vector3(0, 62, 0)
	toss = _marker("TossedFood", Vector3.ZERO, tex)
	toss.pixel_size = 1.2
	toss.shaded = false
	toss.no_depth_test = true
	toss.render_priority = 12
	toss.visible = false
	var sleep_tex: Texture2D = load("res://art/m1-icons/need_sleep.png")
	rest_mark = _marker("DoorRest", _door_stand(), sleep_tex if sleep_tex != null else tex)
	rest_mark.shaded = false
	rest_mark.no_depth_test = true
	rest_mark.render_priority = 11
	rest_mark.visible = false


func _pulse_markers(phase: String) -> void:
	if berry and berry.visible:
		berry.position.y = 8.0 + sin(float(Time.get_ticks_msec()) / 280.0) * 2.0
	if goal_bubble == null:
		return
	var bubble_path := ""
	if phase == "to_rest" or phase == "asleep":
		bubble_path = "res://art/m1-icons/bubble_need_sleep.png"
	if bubble_path == "" or not ResourceLoader.exists(bubble_path):
		goal_bubble.visible = false
		return
	goal_bubble.texture = load(bubble_path)
	goal_bubble.visible = true


func _marker(node_name: String, pos: Vector3, tex: Texture2D) -> Sprite3D:
	var spr := Sprite3D.new()
	spr.name = node_name
	spr.texture = tex
	spr.pixel_size = 1.05
	spr.shaded = false
	spr.no_depth_test = true
	spr.render_priority = 10
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
		home.visible = not inside and phase == "carry"
		home.texture = load(FRUIT_TEX)
		home.modulate = Color(1, 1, 1, 1)
	if home_area:
		home_area.collision_layer = 32 if home != null and home.visible else 0
	if rest_mark:
		var show_rest := not inside and (phase == "to_rest" or offer() == "rest")
		rest_mark.visible = show_rest
		rest_mark.position = _door_stand() + Vector3(0, 12, 0)
	if toss and phase != "toss" and phase != "to_eat":
		toss.visible = false


func _begin_toss() -> void:
	var task := _task()
	var paid := int(task.get("toss_paid", 0))
	if int(task.get("toss_seq", 0)) <= paid:
		task["toss_seq"] = paid + 1
	var origin := walker.global_position if walker else Vector3.ZERO
	toss_land = _open_land(origin)
	_quiet_brain(true)
	walker.pause_t = TOSS_ARC_SEC + 0.2
	toss_from = origin + Vector3(0, 28, 0)
	toss_age = 0.0
	var land := [toss_land.x, toss_land.y, toss_land.z]
	task["toss_land"] = land
	_write(task)
	_place_toss(toss_from)
	_set_phase("toss")


func _fly_toss(dt: float) -> void:
	toss_age += dt
	var u := clampf(toss_age / TOSS_ARC_SEC, 0.0, 1.0)
	var p := toss_from.lerp(toss_land + Vector3(0, 3, 0), u)
	p.y += sin(u * PI) * TOSS_ARC_H
	_place_toss(p)
	if u < 1.0:
		return
	_place_toss(toss_land + Vector3(0, 3, 0))
	_set_phase("to_eat")
	_quiet_brain(false)
	walker.set_errand(toss_land)


func _cancel_toss() -> void:
	_hide_toss()
	_quiet_brain(false)
	walker.clear_errand()
	_after_eat = ""
	_set_phase("idle")


func _place_toss(at: Vector3) -> void:
	if toss == null:
		return
	toss.visible = true
	toss.global_position = at


func _open_land(origin: Vector3) -> Vector3:
	# CrateWood is the 16-unit box at (22, 18). CrateWood2 is at (-24, 28).
	var crates: Array[Vector3] = [Vector3(22, 0, 18), Vector3(-24, 0, 28)]
	var best := origin
	var best_gap := -1.0
	for off in [Vector3(0, 0, 16), Vector3(0, 0, -14), Vector3(-12, 0, 4), Vector3(10, 0, -10)]:
		var spot := _free_spot(origin + off)
		var gap := 999.0
		for crate in crates:
			gap = minf(gap, Vector2(spot.x, spot.z).distance_to(Vector2(crate.x, crate.z)))
		if gap > best_gap:
			best = spot
			best_gap = gap
	return best


func _quiet_brain(on: bool) -> void:
	if walker == null:
		return
	var brain := walker.get_node_or_null("PetBrain")
	if brain == null:
		return
	var tree: Node = brain.get("tree")
	if tree:
		tree.set("enabled", not on)
	brain.set("busy", on)


func _hide_toss() -> void:
	if toss:
		toss.visible = false


func _toss_land() -> Vector3:
	var raw: Variant = _task().get("toss_land", [])
	if raw is Array and raw.size() >= 3:
		return Vector3(float(raw[0]), 0.0, float(raw[2]))
	if toss_land != Vector3.ZERO:
		return toss_land
	return home_pos


func _toss_consumed() -> bool:
	var task := _task()
	return int(task.get("toss_seq", 0)) <= int(task.get("toss_paid", 0)) and int(task.get("toss_seq", 0)) > 0


func _door_stand() -> Vector3:
	if ClassDB.class_exists("Hd2dDoor"):
		return Hd2dDoor.exterior_anchor()
	return Vector3(94.0, 0.0, -29.0)


func _tick_reaction() -> void:
	if _after_eat == "":
		return
	var pres := _presentation()
	if pres == null or not pres.has_method("care_id"):
		_after_eat = ""
		return
	var id := str(pres.call("care_id"))
	var active := pres.has_method("care_active") and bool(pres.call("care_active"))
	if _after_eat == "eat":
		if id == "eat":
			_saw_eat = true
			var frame := int(pres.call("care_frame")) if pres.has_method("care_frame") else 0
			if frame >= 2:
				_hide_toss()
		elif _saw_eat and not active and pres.has_method("play_care"):
			pres.call("play_care", "emo_happy")
			_after_eat = "happy"
			_saw_eat = false
	elif _after_eat == "happy" and not active:
		_after_eat = ""


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
