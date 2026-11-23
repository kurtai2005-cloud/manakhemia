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
	sim._save_now(true)
	print("LINK_PHASE1_OK stage=egg fruit=1 glow_berry=true no_hatch=true")
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
	print("RESTART stage=", stage, " fruit=", fruit, " glow_berry=", bool(found.get("glow_berry", false)), " hatch_unlock=", bool(forms.get("radiant_newborn", false)))
	if stage != "egg" or fruit != 1 or not bool(found.get("glow_berry", false)) or bool(forms.get("radiant_newborn", false)):
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


func _arrived(point: Vector3, steps: int) -> bool:
	var walker: Node3D = _main.get("pet")
	for _i in range(steps):
		walker._process(0.05)
		var pres := _main.get_node_or_null("Hd2dPresentation")
		if pres:
			pres._process(0.05)
		_main.get_node("GardenErrand")._process(0.05)
		if Vector2(walker.global_position.x, walker.global_position.z).distance_to(Vector2(point.x, point.z)) < 1.2:
			return true
	return false


func _die(why: String) -> void:
	print("LINK_FAIL ", why)
	quit(1)
