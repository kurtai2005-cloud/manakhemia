extends SceneTree
## Preview profile only. The normal egg clock is not changed.
## vc27_draft_preview. Does not touch vc27_draft_try or vc27_play_36bfd.

var _main: Node


func _initialize() -> void:
	var udir := OS.get_user_data_dir()
	print("preview user_dir=", udir)
	if udir.find("vc27_play_36bfd") >= 0 or udir.find("vc27_draft_try") >= 0 or udir.find("vc27_draft_preview") < 0:
		print("PREVIEW_FAIL profile")
		quit(2)
		return
	if OS.get_environment("VC27_DRAFT_PREVIEW") != "1":
		print("PREVIEW_FAIL env")
		quit(2)
		return
	if OS.get_environment("VC27_PREVIEW_PHASE") == "2":
		await _check()
		return
	await _play()


func _play() -> void:
	_main = (load("res://scenes/Main.tscn") as PackedScene).instantiate()
	root.add_child(_main)
	if not await _ready_pet():
		_die("pet did not appear")
		return
	var sim: Node = root.get_node("Sim")
	if not bool(sim.state.get("preview_fixture", false)) or str(sim.state.get("stage", "")) != "egg":
		_die("preview seed missing")
		return
	var errand: Node = _main.get_node("GardenErrand")
	if str(errand.call("player_press")) != "start":
		_die("berry click did not start")
		return
	if not _arrived(errand.get("berry_pos"), 500) or not _arrived(errand.get("home_pos"), 700):
		_die("delivery did not finish")
		return
	if str(sim.state.get("stage", "")) != "newborn":
		_die("preview delivery did not hatch")
		return
	var col: Node = root.get_node("CollectionSystem")
	var found: Dictionary = sim.state.get("collection", {}).get("discovered", {})
	var forms: Dictionary = sim.state.get("collection", {}).get("forms", {})
	if int(col.call("fruit_count", "starberry")) != 1 or not bool(found.get("glow_berry", false)) or not bool(forms.get("radiant_newborn", false)):
		_die("preview delivery reward missing")
		return
	if float(sim.state.get("needs", {}).get("energy", 100)) >= float(sim.get("SLEEP_MIN_ENERGY")):
		_die("preview energy was not lowered after hatch")
		return
	var post: Node = _main.get("work_spots").get("post")
	var kitchen: Node = _main.get("work_spots").get("kitchen")
	if post == null or kitchen == null:
		_die("work buildings were not in the garden")
		return
	var work: Node = root.get_node("WorkSystem")
	var shards := int(col.call("stardust"))
	var sent: Dictionary = _main.call("one_tap_dispatch")
	if not bool(sent.get("ok", false)) or str(sent.get("building", "")) != "kitchen":
		_die("dispatch did not choose the kitchen")
		return
	var walker: Node3D = _main.get("pet")
	var dest: Vector3 = walker.get("errand_dest")
	var spot_at: Vector3 = kitchen.global_position
	if Vector2(dest.x, dest.z).distance_to(Vector2(spot_at.x, spot_at.z)) > 40.0:
		_die("dispatch did not aim at the kitchen")
		return
	if not _arrived(dest, 800):
		_die("pet did not walk to the kitchen")
		return
	work.tick_watch(12.0)
	_main.call("_on_building_tapped", kitchen.get("click"))
	_main.call("_on_building_tapped", post.get("click"))
	if int(col.call("stardust")) != shards + 2 or str(work.site("post").get("status", "")) != "empty":
		_die("kitchen pay or the same-day post gate failed")
		return
	if str(errand.call("press_food")) != "toss":
		_die("meal did not start")
		return
	if not _until_phase("idle", 900):
		_die("meal did not finish")
		return
	if int(col.call("fruit_count", "starberry")) != 0:
		_die("meal did not spend one fruit")
		return
	if str(errand.call("press_rest")) != "rest":
		_die("rest did not start")
		return
	if not _until_inside(800):
		_die("did not enter")
		return
	for _i in range(8):
		_pump()
	if not bool(sim.state.get("sleeping", false)):
		_die("not asleep")
		return
	print("FIXTURE smoke calls Sim.tick. Sleep regen rate is unchanged.")
	var steps := 0
	while steps < 2000 and (bool(sim.state.get("sleeping", false)) or bool(_main.get("in_interior"))):
		sim.tick(0.25)
		_main.get_node("GardenErrand")._process(0.05)
		steps += 1
	if bool(sim.state.get("sleeping", false)) or bool(_main.get("in_interior")):
		_die("wake did not return outside")
		return
	sim._save_now(true)
	print("PREVIEW_PHASE1_OK stage=newborn fruit=0 glow_berry=true")
	quit(0)


func _check() -> void:
	_main = (load("res://scenes/Main.tscn") as PackedScene).instantiate()
	root.add_child(_main)
	if not await _ready_pet():
		_die("restart had no pet")
		return
	var sim: Node = root.get_node("Sim")
	var col: Node = root.get_node("CollectionSystem")
	var found: Dictionary = sim.state.get("collection", {}).get("discovered", {})
	var forms: Dictionary = sim.state.get("collection", {}).get("forms", {})
	var stage := str(sim.state.get("stage", ""))
	var fruit := int(col.call("fruit_count", "starberry"))
	var meals := int(sim.state.get("errand", {}).get("meals", 0))
	var shards := int(col.call("stardust"))
	print("RESTART stage=", stage, " fruit=", fruit, " meals=", meals, " shards=", shards, " glow=", bool(found.get("glow_berry", false)), " unlock=", bool(forms.get("radiant_newborn", false)), " preview=", bool(sim.state.get("preview_fixture", false)), " inside=", bool(_main.get("in_interior")), " sleeping=", bool(sim.state.get("sleeping", false)))
	if stage != "newborn" or fruit != 0 or meals < 1 or shards < 27 or not bool(found.get("glow_berry", false)) or not bool(forms.get("radiant_newborn", false)) or not bool(sim.state.get("preview_fixture", false)):
		_die("restart lost preview progress")
		return
	if bool(_main.get("in_interior")) or bool(sim.state.get("sleeping", false)):
		_die("restart still inside or asleep")
		return
	print("PREVIEW_PHASE2_OK")
	quit(0)


func _ready_pet() -> bool:
	for _i in range(240):
		await process_frame
		if _main.get("pet") != null and _main.get_node_or_null("GardenErrand") != null:
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


func _arrived(point: Vector3, steps: int) -> bool:
	var walker: Node3D = _main.get("pet")
	for _i in range(steps):
		_pump()
		if Vector2(walker.global_position.x, walker.global_position.z).distance_to(Vector2(point.x, point.z)) < 1.2:
			return true
	return false


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
	print("PREVIEW_FAIL ", why)
	quit(1)
