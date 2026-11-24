extends SceneTree
## Berry delivery hatches the egg and records the existing dex fruit.
## Isolated profile vc27_draft_link. Does not touch vc27_draft_try or vc27_play_36bfd.
## No clock fixture. The delivery uses the existing growth check.

var _main: Node


func _initialize() -> void:
	var udir := OS.get_user_data_dir()
	print("link user_dir=", udir)
	if udir.find("vc27_play_36bfd") >= 0 or udir.find("vc27_draft_try") >= 0 or udir.find("vc27_draft_link") < 0:
		print("LINK_FAIL profile")
		quit(2)
		return
	var phase := OS.get_environment("VC27_LINK_PHASE")
	if phase == "2":
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
	if str(sim.state.get("stage", "")) != "egg":
		_die("fresh save was not an egg")
		return
	var errand: Node = _main.get_node("GardenErrand")
	if str(errand.call("player_press")) != "start":
		_die("berry click did not start")
		return
	if not _arrived(errand.get("berry_pos"), 500):
		_die("did not reach the berry")
		return
	if not _arrived(errand.get("home_pos"), 700):
		_die("did not reach home")
		return
	if str(sim.state.get("stage", "")) != "egg":
		_die("a normal delivery changed the egg clock")
		return
	var col: Node = root.get_node("CollectionSystem")
	if int(col.call("fruit_count", "starberry")) != 1:
		_die("delivery did not store one fruit")
		return
	var found: Dictionary = sim.state.get("collection", {}).get("discovered", {})
	if not bool(found.get("glow_berry", false)):
		_die("delivery did not record glow_berry")
		return
	var forms: Dictionary = sim.state.get("collection", {}).get("forms", {})
	if bool(forms.get("radiant_newborn", false)):
		_die("normal delivery unlocked a hatch")
		return
	if not bool(col.call("has_dot", "collection")):
		_die("book dot was not set")
		return
	if str(errand.call("player_press")) != "start" or str(errand.call("player_press")) != "cancel":
		_die("berry trip did not cancel")
		return
	if int(col.call("fruit_count", "starberry")) != 1:
		_die("cancel changed the fruit")
		return
	var post: Node = _main.get("work_spots").get("post")
	var kitchen: Node = _main.get("work_spots").get("kitchen")
	if post == null or kitchen == null:
		_die("work buildings were not in the garden")
		return
	var shards := int(col.call("stardust"))
	var sent: Dictionary = _main.call("one_tap_dispatch")
	var work: Node = root.get_node("WorkSystem")
	if not bool(sent.get("ok", false)) or str(sent.get("building", "")) != "kitchen":
		_die("dispatch did not choose the kitchen")
		return
	if str(work.site("kitchen").get("status", "")) != "work":
		_die("kitchen job did not start")
		return
	_main.call("_on_building_tapped", kitchen.get("click"))
	if str(work.site("kitchen").get("status", "")) != "work" or int(col.call("stardust")) != shards:
		_die("second kitchen click paid early")
		return
	var walker: Node3D = _main.get("pet")
	var dest: Vector3 = walker.get("errand_dest")
	var spot_at: Vector3 = kitchen.global_position
	if Vector2(dest.x, dest.z).distance_to(Vector2(spot_at.x, spot_at.z)) > 40.0:
		_die("dispatch did not aim at the kitchen")
		return
	if not _arrived(dest, 800):
		print("WORK_POS ", walker.global_position, " aim ", dest)
		_die("pet did not walk to the kitchen")
		return
	work.tick_watch(12.0)
	if not bool(work.call("is_ready", "kitchen")):
		_die("kitchen was not ready after the existing 12s watch")
		return
	_main.call("_on_building_tapped", kitchen.get("click"))
	if int(col.call("stardust")) != shards + 2:
		_die("kitchen pay was not the existing level+1")
		return
	var again: Dictionary = work.collect("kitchen")
	if bool(again.get("ok", false)) or int(col.call("stardust")) != shards + 2:
		_die("collecting the kitchen twice paid again")
		return
	var again_send: Dictionary = _main.call("one_tap_dispatch")
	_main.call("_on_building_tapped", post.get("click"))
	if bool(again_send.get("ok", false)) or str(work.site("post").get("status", "")) != "empty":
		_die("a second workplace started on the same day")
		return
	sim._save_now(true)
	print("LINK_PHASE1_OK stage=egg fruit=1 glow_berry=true kitchen_shards=2")
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
	var shards := int(col.call("stardust"))
	print("RESTART stage=", stage, " fruit=", fruit, " glow_berry=", bool(found.get("glow_berry", false)), " shards=", shards, " hatch_unlock=", bool(forms.get("radiant_newborn", false)))
	if stage != "egg" or fruit != 1 or not bool(found.get("glow_berry", false)) or bool(forms.get("radiant_newborn", false)) or shards < 27:
		_die("restart lost the normal delivery")
		return
	print("LINK_PHASE2_OK")
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


func _die(why: String) -> void:
	print("LINK_FAIL ", why)
	quit(1)
