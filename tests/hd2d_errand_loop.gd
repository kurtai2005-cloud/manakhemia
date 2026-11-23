extends SceneTree
## Spatial berry errand on normal Main: walk, carry, drop once, care, save.
## Headless is not a phone or GPU pass.

var _main: Node
var _ran := false
var _frames := 0


func _initialize() -> void:
	var udir := OS.get_user_data_dir()
	print("errand user_dir=", udir)
	if OS.get_environment("ERRAND_REQUIRE_ISOLATED") == "1" and udir.find("vc27_errand_") < 0:
		print("FAIL isolated user dir")
		quit(2)
		return
	_main = (load("res://scenes/Main.tscn") as PackedScene).instantiate()
	root.add_child(_main)
	process_frame.connect(_on_frame)


func _on_frame() -> void:
	if _ran:
		return
	_frames += 1
	if _frames > 240:
		print("FAIL pet did not appear")
		quit(1)
		return
	if _main.get("pet") == null or _main.get_node_or_null("GardenErrand") == null:
		return
	_ran = true
	process_frame.disconnect(_on_frame)
	await _run()


func _run() -> void:
	var walker: Node3D = _main.get("pet")
	var errand: Node = _main.get_node("GardenErrand")
	var sim: Node = root.get_node("Sim")
	_ok(str(sim.get("state").get("version", 0)) == "1", "save version stays 1")
	_ok(not sim.get("state").has("errand") or sim.get("state")["errand"] is Dictionary, "legacy errand key is optional")
	var berry: Vector3 = errand.get("berry_pos")
	var home: Vector3 = errand.get("home_pos")
	_ok(berry.distance_to(home) > 12.0, "berry and home are apart")
	var cam: Camera3D = _main.get("cam")
	var screen: Vector2 = cam.unproject_position(berry + Vector3(0, 6, 0))
	_main.call("_try_tap", screen)
	var started := str(sim.get("state")["errand"].get("phase", "")) == "to_pick"
	_ok(started, "screen ray starts the walk")
	if not started:
		errand.call("player_press")
	_ok(not _arrived(walker, berry, 8, false), "does not teleport onto the berry")
	_ok(_arrived(walker, berry, 400), "walks to the berry")
	_ok(str(sim.get("state")["errand"].get("phase", "")) == "carry", "picked up")
	var carried: Node3D = walker.get_node_or_null("CarriedBerry")
	_ok(carried != null and carried.visible, "carried berry is visible on the pet")
	_ok(not _arrived(walker, home, 40, false), "does not teleport home")
	_ok(_arrived(walker, home, 500), "carries the berry home")
	var count := int(root.get_node("CollectionSystem").call("fruit_count", "starberry"))
	_ok(count == 1, "one fruit reward")
	_ok(str(sim.get("state")["errand"].get("phase", "")) == "idle", "returns to idle")
	errand.call("_grant_once")
	_ok(int(root.get_node("CollectionSystem").call("fruit_count", "starberry")) == 1, "no second reward")
	# Cancel and blocked.
	sim.get("state")["errand"] = {"phase": "idle", "active_id": "", "delivered": []}
	errand.call("_restore_visual")
	_ok(errand.call("player_press") == "start", "retry starts")
	_ok(errand.call("player_press") == "cancel", "second click cancels")
	_ok(not walker.errand_active, "cancel stops navigation")
	walker.global_position = Vector3(0, 0, 0)
	var wall := Footprints.new()
	wall.rects.append({"x0": 6.0, "x1": 200.0, "z0": -200.0, "z1": 200.0})
	walker.feet = wall
	errand.set("berry_pos", Vector3(48, 0, 36))
	_ok(errand.call("player_press") == "start", "blocked attempt starts")
	var blocked := false
	for _i in range(80):
		walker._process(0.05)
		errand._process(0.05)
		if bool(walker.get("errand_blocked")):
			blocked = true
			break
	_ok(blocked, "solid wall stops the walk")
	_ok(int(root.get_node("CollectionSystem").call("fruit_count", "starberry")) == 1, "blocked path grants nothing")
	# Care hold, then move again.
	walker.feet = _main.get("feet")
	walker.global_position = Vector3(0, 0, 0)
	sim.get("state")["errand"]["delivered"] = []
	errand.call("player_press")
	var pres: Node = _main.get_node_or_null("Hd2dPresentation")
	if pres and pres.has_method("play_care"):
		pres.call("play_care", "nuzzle")
		var held_at: Vector3 = walker.global_position
		errand._process(0.2)
		walker._process(0.2)
		_ok(walker.global_position.distance_to(held_at) < 0.2, "care holds the feet")
		pres.set("_care_id", "")
		walker.errand_hold = false
		var moved := false
		var before := walker.global_position
		for _j in range(10):
			walker._process(0.05)
		if walker.global_position.distance_to(before) > 0.4:
			moved = true
		_ok(moved, "movement resumes after care")
		if pres.has_method("play_care"):
			walker.dir = "back"
			pres.call("play_care", "eat")
			var coat: Sprite3D = walker.get_node_or_null("Hd2dCoat")
			_ok(coat != null and not coat.flip_h, "back-facing care stays unflipped")
			pres.set("_care_id", "")
	# A save with no errand key still loads.
	var legacy: Dictionary = sim.get("state").duplicate(true)
	legacy.erase("errand")
	root.get_node("SaveSystem").call("save_state", legacy)
	var loaded_legacy: Dictionary = root.get_node("SaveSystem").call("load_state")
	_ok(not loaded_legacy.has("errand"), "legacy save has no errand key")
	_ok(int(loaded_legacy.get("version", 0)) == 1, "legacy save stays version 1")
	# Close mid-carry, open again, then walk the last step. Pay once.
	sim.get("state")["errand"] = {"phase": "carry", "active_id": "starberry", "delivered": []}
	var again := int(root.get_node("CollectionSystem").call("fruit_count", "starberry"))
	sim._dirty = true
	sim._save_now(true)
	var home_again: Vector3 = errand.get("home_pos")
	_main.queue_free()
	await process_frame
	_main = (load("res://scenes/Main.tscn") as PackedScene).instantiate()
	root.add_child(_main)
	var appeared := false
	for _k in range(240):
		if _main.get("pet") != null and _main.get_node_or_null("GardenErrand") != null:
			appeared = true
			break
		await process_frame
	_ok(appeared, "reopened main has the pet")
	var errand2: Node = _main.get_node("GardenErrand")
	var walker2: Node3D = _main.get("pet")
	_ok(str(sim.get("state")["errand"].get("phase", "")) == "carry", "reopen keeps the carry")
	_ok(int(root.get_node("CollectionSystem").call("fruit_count", "starberry")) == again, "reopen does not pay early")
	var carried2: Node3D = walker2.get_node_or_null("CarriedBerry")
	_ok(carried2 != null and carried2.visible, "reopen still shows the carried berry")
	walker2.global_position = home_again + Vector3(8, 0, 0)
	walker2.call("set_errand", home_again)
	_ok(_arrived(walker2, home_again, 80), "reloaded carry finishes by walking")
	_ok(int(root.get_node("CollectionSystem").call("fruit_count", "starberry")) == again + 1, "drop after reload pays once")
	errand2._process(0.05)
	_ok(int(root.get_node("CollectionSystem").call("fruit_count", "starberry")) == again + 1, "reload drop does not repeat")
	var fruits_now := int(root.get_node("CollectionSystem").call("fruit_count", "starberry"))
	sim.get("state")["last_seen"] = int(root.get_node("TimeService").call("now_ms")) + 3600 * 1000
	var rolled: Dictionary = root.get_node("TimeService").call("catch_up", sim.get("state"))
	_ok(bool(rolled.get("rollback", false)), "backwards clock is ignored")
	_ok(int(root.get_node("CollectionSystem").call("fruit_count", "starberry")) == fruits_now, "backwards clock grants no fruit")
	sim.get("state")["last_seen"] = int(root.get_node("TimeService").call("now_ms")) - int(100.0 * 3600.0 * 1000.0)
	var away: Dictionary = root.get_node("TimeService").call("catch_up", sim.get("state"))
	_ok(float(away.get("E", 0.0)) <= 24.0 * 3600.0 + 1.0, "offline apply stays capped")
	_ok(int(root.get_node("CollectionSystem").call("fruit_count", "starberry")) == fruits_now, "offline catch-up grants no errand fruit")
	var offline := float(sim.call("effective_offline", 100.0 * 3600.0))
	_ok(offline <= 24.0 * 3600.0, "offline time stays capped")
	print("PASS errand loop" if _fails == 0 else "FAIL errand loop")
	quit(0 if _fails == 0 else 1)


func _arrived(walker: Node3D, point: Vector3, steps: int, loud: bool = true) -> bool:
	for _i in range(steps):
		walker._process(0.05)
		var errand: Node = _main.get_node("GardenErrand")
		errand._process(0.05)
		if Vector2(walker.global_position.x, walker.global_position.z).distance_to(Vector2(point.x, point.z)) < 1.2:
			return true
	if loud:
		print("stop at ", walker.global_position, " want ", point, " phase ", _main.get_node("GardenErrand")._task().get("phase"))
	return false


var _fails := 0


func _ok(cond: bool, name: String) -> void:
	if cond:
		print("PASS ", name)
	else:
		_fails += 1
		print("FAIL ", name)
