extends SceneTree
## One isolated draft of the existing loop.
## Phase 1 plays it and saves. Phase 2 is a new process reading that save.
## Lines that start with FIXTURE advance the existing Sim clock. Stage lengths are unchanged.
## This does not touch vc27_play_36bfd.

var _main: Node


func _initialize() -> void:
	var udir := OS.get_user_data_dir()
	print("draft user_dir=", udir)
	if udir.find("vc27_play_36bfd") >= 0 or udir.find("vc27_draft_loop") < 0:
		print("DRAFT_FAIL profile")
		quit(2)
		return
	var phase := OS.get_environment("VC27_DRAFT_PHASE")
	if phase == "2":
		await _check_restart()
		return
	await _play()


func _play() -> void:
	_main = (load("res://scenes/Main.tscn") as PackedScene).instantiate()
	root.add_child(_main)
	if not await _ready_pet():
		_die("pet did not appear")
		return
	var sim: Node = root.get_node("Sim")
	var col: Node = root.get_node("CollectionSystem")
	var errand: Node = _main.get_node("GardenErrand")
	if str(sim.state.get("stage", "")) != "egg":
		_die("a fresh save was not an egg")
		return
	if not _deliver():
		_die("berry delivery did not finish")
		return
	if int(col.call("fruit_count", "starberry")) != 1:
		_die("delivery did not store one fruit")
		return
	if bool(errand.call("food_choice")):
		_die("egg offered a meal")
		return
	var before_egg_fruit := int(col.call("fruit_count", "starberry"))
	errand.call("press_food")
	if int(col.call("fruit_count", "starberry")) != before_egg_fruit:
		_die("egg meal spent fruit")
		return
	print("FIXTURE Sim.advance 620s so the existing 600s egg can hatch. duration_sec is unchanged.")
	sim.call("advance", sim.state, 620.0, {})
	if str(sim.state.get("stage", "")) != "newborn":
		_die("egg did not hatch on the existing clock")
		return
	var unlock := "radiant_newborn"
	var forms: Dictionary = sim.state.get("collection", {}).get("forms", {})
	if not bool(forms.get(unlock, false)):
		_die("hatch did not unlock " + unlock)
		return
	if int(col.call("fruit_count", "starberry")) != 1:
		_die("hatch changed the stored fruit")
		return
	var hunger_before := float(sim.state.get("needs", {}).get("hunger", 0))
	if str(errand.call("press_food")) != "toss":
		_die("hatched meal did not toss")
		return
	if not _until_phase("idle", 900):
		_die("pet did not finish the meal")
		return
	if int(col.call("fruit_count", "starberry")) != 0:
		_die("meal did not spend the one fruit")
		return
	if int(sim.state.get("errand", {}).get("meals", 0)) < 1:
		_die("meal was not recorded")
		return
	if float(sim.state.get("needs", {}).get("hunger", 0)) <= hunger_before:
		_die("meal did not raise hunger")
		return
	print("FIXTURE Sim.advance until energy is below the existing rest line. Decay rates are unchanged.")
	var waited := 0.0
	while float(sim.state.get("needs", {}).get("energy", 100)) >= float(sim.get("SLEEP_MIN_ENERGY")) and waited < 8.0 * 3600.0:
		sim.call("advance", sim.state, 600.0, {})
		waited += 600.0
	if not bool(errand.call("rest_offered")):
		_die("rest was not offered after the meal and the existing energy line")
		return
	if str(errand.call("press_rest")) != "rest":
		_die("rest button did not start the door walk")
		return
	if not _until_inside(800):
		_die("pet did not enter the house to sleep")
		return
	for _i in range(8):
		_pump()
	if not bool(sim.state.get("sleeping", false)):
		_die("inside pet was not asleep")
		return
	print("FIXTURE Sim.advance 4h while asleep so the existing wake point is reached.")
	sim.call("advance", sim.state, 4.0 * 3600.0, {})
	_main.get_node("GardenErrand")._process(0.05)
	if bool(sim.state.get("sleeping", false)) or bool(_main.get("in_interior")):
		_die("wake did not return the pet outside")
		return
	sim._save_now(true)
	print("DRAFT_PHASE1_OK stage=", sim.state.get("stage"), " fruit=", col.call("fruit_count", "starberry"), " meals=", sim.state.get("errand", {}).get("meals", 0), " unlock=", unlock)
	quit(0)


func _check_restart() -> void:
	_main = (load("res://scenes/Main.tscn") as PackedScene).instantiate()
	root.add_child(_main)
	if not await _ready_pet():
		_die("restart had no pet")
		return
	var sim: Node = root.get_node("Sim")
	var col: Node = root.get_node("CollectionSystem")
	var stage := str(sim.state.get("stage", ""))
	var meals := int(sim.state.get("errand", {}).get("meals", 0))
	var fruit := int(col.call("fruit_count", "starberry"))
	var forms: Dictionary = sim.state.get("collection", {}).get("forms", {})
	var inside := bool(_main.get("in_interior"))
	var sleeping := bool(sim.state.get("sleeping", false))
	var woke := false
	for ev in sim.state.get("ev", []):
		if ev is Dictionary and str(ev.get("type", "")) == "wake":
			woke = true
	print("RESTART stage=", stage, " fruit=", fruit, " meals=", meals, " unlock=", bool(forms.get("radiant_newborn", false)), " inside=", inside, " sleeping=", sleeping, " woke=", woke)
	if stage != "newborn" or meals < 1 or not bool(forms.get("radiant_newborn", false)) or inside or sleeping or not woke:
		_die("restart did not keep the played loop")
		return
	print("DRAFT_PHASE2_OK")
	quit(0)


func _ready_pet() -> bool:
	for _i in range(240):
		await process_frame
		if _main.get("pet") != null and _main.get_node_or_null("GardenErrand") != null:
			return true
	return false


func _deliver() -> bool:
	var errand: Node = _main.get_node("GardenErrand")
	if str(errand.call("player_press")) != "start":
		return false
	if not _arrived(errand.get("berry_pos"), 500):
		return false
	return _arrived(errand.get("home_pos"), 700)


func _arrived(point: Vector3, steps: int) -> bool:
	var walker: Node3D = _main.get("pet")
	for _i in range(steps):
		_pump()
		if Vector2(walker.global_position.x, walker.global_position.z).distance_to(Vector2(point.x, point.z)) < 1.2:
			return true
	return false


func _pump() -> void:
	var walker: Node3D = _main.get("pet")
	walker._process(0.05)
	var pres := _main.get_node_or_null("Hd2dPresentation")
	if pres:
		pres._process(0.05)
	_main.get_node("GardenErrand")._process(0.05)
	if _main.has_method("_commit_door_if_arrived"):
		_main.call("_commit_door_if_arrived")


func _until_phase(phase: String, steps: int) -> bool:
	for _i in range(steps):
		_pump()
		if str(_main.get_node("GardenErrand")._task().get("phase", "")) == phase:
			return true
	return false


func _until_inside(steps: int) -> bool:
	for _i in range(steps):
		_pump()
		if bool(_main.get("in_interior")):
			return true
	return false


func _die(why: String) -> void:
	print("DRAFT_FAIL ", why)
	quit(1)
