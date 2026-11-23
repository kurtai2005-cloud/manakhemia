extends SceneTree
## Repeatable forage, one meal per fruit, rest through the existing door.
## Headless is not a phone or GPU pass.

var _main: Node
var _ran := false
var _frames := 0
var _fails := 0


func _initialize() -> void:
	var udir := OS.get_user_data_dir()
	print("progress user_dir=", udir)
	if OS.get_environment("PROGRESS_REQUIRE_ISOLATED") == "1" and udir.find("vc27_progress_") < 0:
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
	var sim: Node = root.get_node("Sim")
	var col: Node = root.get_node("CollectionSystem")
	_deliver(1)
	_ok(int(col.call("fruit_count", "starberry")) == 1, "first delivery pays one")
	var errand: Node = _main.get_node("GardenErrand")
	errand.call("_grant_once")
	_ok(int(col.call("fruit_count", "starberry")) == 1, "same delivery does not pay again")
	var berry: Node3D = errand.get("berry")
	_ok(berry != null and berry.visible, "berry comes back after the drop")
	_deliver(2)
	_ok(int(col.call("fruit_count", "starberry")) == 2, "second delivery pays one more")
	# Mid-carry reload of a third trip.
	errand = _main.get_node("GardenErrand")
	_ok(str(errand.call("player_press")) == "start", "third trip starts")
	var walker: Node3D = _main.get("pet")
	_ok(_arrived(walker, errand.get("berry_pos"), 400), "third trip reaches the berry")
	_ok(str(sim.get("state")["errand"].get("phase", "")) == "carry", "third trip is carrying")
	var before_reload := int(col.call("fruit_count", "starberry"))
	sim._dirty = true
	sim._save_now(true)
	var home: Vector3 = errand.get("home_pos")
	_main.queue_free()
	await process_frame
	_main = (load("res://scenes/Main.tscn") as PackedScene).instantiate()
	root.add_child(_main)
	var appeared := false
	for _i in range(240):
		if _main.get("pet") != null and _main.get_node_or_null("GardenErrand") != null:
			appeared = true
			break
		await process_frame
	_ok(appeared, "reopened main has the pet")
	errand = _main.get_node("GardenErrand")
	walker = _main.get("pet")
	_ok(str(sim.get("state")["errand"].get("phase", "")) == "carry", "reopen is still carrying")
	_ok(int(col.call("fruit_count", "starberry")) == before_reload, "reopen does not pay early")
	walker.global_position = home + Vector3(8, 0, 0)
	walker.call("set_errand", home)
	_ok(_arrived(walker, home, 80), "reloaded carry finishes by walking")
	_ok(int(col.call("fruit_count", "starberry")) == before_reload + 1, "reload pays the open delivery once")
	errand._process(0.05)
	_ok(int(col.call("fruit_count", "starberry")) == before_reload + 1, "reload does not pay twice")
	# Meal from the stored fruit.
	var needs: Dictionary = sim.get("state")["needs"]
	needs["hunger"] = 40.0
	sim.get("state")["needs"] = needs
	var social_before := int(root.get_node("Personality").call("axis", "tuanrong", "social"))
	_ok(str(errand.call("press_home")) == "eat", "home click starts the meal walk")
	_ok(_arrived(walker, errand.get("home_pos"), 80), "pet walks to eat")
	_ok(int(col.call("fruit_count", "starberry")) == before_reload, "one fruit was eaten")
	_ok(float(sim.get("state")["needs"]["hunger"]) > 40.0, "meal raises hunger")
	_ok(int(sim.get("state")["errand"].get("meals", 0)) == 1, "one forage meal is recorded")
	var social_after := int(root.get_node("Personality").call("axis", "tuanrong", "social"))
	_ok(social_after == social_before + 1, "meal shifts the existing social bond")
	var home_sprite: Sprite3D = errand.get("home")
	_ok(home_sprite != null and is_equal_approx(home_sprite.modulate.a, 1.0), "home marker shows the rest spot")
	var coat: Sprite3D = walker.get_node_or_null("Hd2dCoat")
	_ok(coat != null and coat.visible, "eat stays on the one coat")
	# Full pet does not spend.
	needs = sim.get("state")["needs"]
	needs["hunger"] = 95.0
	sim.get("state")["needs"] = needs
	var held_fruits := int(col.call("fruit_count", "starberry"))
	_ok(str(errand.call("press_home")) == "full", "a full pet does not start another meal")
	_ok(int(col.call("fruit_count", "starberry")) == held_fruits, "a refused meal spends nothing")
	# Growth stays the existing clock: frozen while unwell, moving after the meal.
	needs = sim.get("state")["needs"]
	needs["hunger"] = 10.0
	sim.get("state")["needs"] = needs
	sim.get("state")["growth_sec"] = 0.0
	sim.call("step", sim.get("state"), 10.0, {})
	_ok(is_equal_approx(float(sim.get("state")["growth_sec"]), 0.0), "unwell growth stays still")
	needs = sim.get("state")["needs"]
	needs["hunger"] = 40.0
	sim.get("state")["needs"] = needs
	_ok(str(errand.call("press_home")) == "eat", "second meal starts")
	_ok(_arrived(walker, errand.get("home_pos"), 40), "second meal reaches home")
	_ok(float(sim.get("state")["needs"]["hunger"]) >= 15.0, "second meal clears unwell")
	sim.get("state")["growth_sec"] = 0.0
	sim.call("step", sim.get("state"), 10.0, {})
	_ok(float(sim.get("state")["growth_sec"]) > 0.0, "growth moves once the pet is well")
	# Rest uses the existing door.
	needs = sim.get("state")["needs"]
	needs["energy"] = 30.0
	sim.get("state")["needs"] = needs
	_ok(str(errand.call("press_home")) == "rest", "home click starts rest")
	var rested := false
	for _r in range(120):
		if bool(_main.get("in_interior")):
			rested = true
			break
		walker._process(0.05)
		errand._process(0.05)
		if bool(_main.get("in_interior")):
			rested = true
			break
	_ok(rested, "pet walks home and enters the existing house")
	_ok(bool(_main.get("in_interior")), "rest enters the existing house")
	_ok(bool(sim.get("state").get("sleeping", false)), "rest uses the existing sleep flag")
	sim.call("advance", sim.get("state"), 10.0 * 3600.0, {})
	errand._process(0.05)
	_ok(not bool(sim.get("state").get("sleeping", false)), "existing wake clears sleep")
	_ok(not bool(_main.get("in_interior")), "wake uses the existing exit")
	var fruits_now := int(col.call("fruit_count", "starberry"))
	sim.get("state")["last_seen"] = int(root.get_node("TimeService").call("now_ms")) + 3600 * 1000
	var rolled: Dictionary = root.get_node("TimeService").call("catch_up", sim.get("state"))
	_ok(bool(rolled.get("rollback", false)), "backwards clock is ignored")
	sim.get("state")["last_seen"] = int(root.get_node("TimeService").call("now_ms")) - int(100.0 * 3600.0 * 1000.0)
	var away: Dictionary = root.get_node("TimeService").call("catch_up", sim.get("state"))
	_ok(float(away.get("E", 0.0)) <= 24.0 * 3600.0 + 1.0, "offline apply stays capped")
	_ok(int(col.call("fruit_count", "starberry")) == fruits_now, "offline grants no delivery")
	print("PASS forage progress" if _fails == 0 else "FAIL forage progress")
	quit(0 if _fails == 0 else 1)


func _deliver(n: int) -> void:
	var errand: Node = _main.get_node("GardenErrand")
	var walker: Node3D = _main.get("pet")
	_ok(str(errand.call("player_press")) == "start", "delivery %d starts" % n)
	_ok(_arrived(walker, errand.get("berry_pos"), 400), "delivery %d reaches the berry" % n)
	_ok(_arrived(walker, errand.get("home_pos"), 500), "delivery %d reaches home" % n)


func _arrived(walker: Node3D, point: Vector3, steps: int) -> bool:
	for _i in range(steps):
		walker._process(0.05)
		var errand: Node = _main.get_node("GardenErrand")
		errand._process(0.05)
		if Vector2(walker.global_position.x, walker.global_position.z).distance_to(Vector2(point.x, point.z)) < 1.2:
			return true
	print("stop at ", walker.global_position, " want ", point, " phase ", _main.get_node("GardenErrand")._task().get("phase"))
	return false


func _ok(cond: bool, name: String) -> void:
	if cond:
		print("PASS ", name)
	else:
		_fails += 1
		print("FAIL ", name)
