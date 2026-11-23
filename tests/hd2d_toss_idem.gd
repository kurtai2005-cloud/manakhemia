extends SceneTree
## Inventory only. Not a picture pass.
## Same process: calls press_food, reads user://save_v1.json, puts that dict back
## into the live Sim autoload, then frees Main and instances it again.
## The autoloads are not restarted. This is not a new OS process.

func _initialize() -> void:
	var udir := OS.get_user_data_dir()
	print("toss_idem user_dir=", udir)
	if udir.find("vc27_play_36bfd") >= 0 or udir.find("vc27_toss_idem") < 0:
		print("TOSS_IDEM_FAIL profile")
		quit(2)
		return
	var main := await _boot()
	if main == null:
		quit(1)
		return
	_fixture(main, 1)
	var errand := main.get_node("GardenErrand")
	var before := _fruit()
	var first := str(errand.call("press_food"))
	var cancel := str(errand.call("press_food"))
	print("CANCEL first=", first, " second=", cancel, " fruit=", _fruit(), " phase=", _phase())
	if first != "toss" or cancel != "cancel" or _fruit() != before or _phase() != "idle":
		print("TOSS_IDEM_FAIL cancel")
		quit(1)
		return
	var again := str(errand.call("press_food"))
	if again != "toss":
		print("TOSS_IDEM_FAIL relaunch ", again)
		quit(1)
		return
	await process_frame
	var mid: Dictionary = root.get_node("SaveSystem").call("load_state")
	var mid_fruit := int(mid.get("collection", {}).get("fruits", {}).get("starberry", 0))
	var mid_err: Dictionary = mid.get("errand", {})
	print("MIDSAVE fruit=", mid_fruit, " seq=", mid_err.get("toss_seq"), " paid=", mid_err.get("toss_paid"), " phase=", mid_err.get("phase"))
	if mid_fruit != before or int(mid_err.get("toss_paid", 0)) != 0:
		print("TOSS_IDEM_FAIL mid-toss save already spent")
		quit(1)
		return
	root.get_node("CollectionSystem").call("add_fruit", "starberry", 4)
	root.get_node("Sim").state = root.get_node("SaveSystem").call("load_state")
	if _fruit() != before:
		print("TOSS_IDEM_FAIL reload mid-toss changed the fruit count")
		quit(1)
		return
	var start := Time.get_ticks_msec()
	while Time.get_ticks_msec() - start < 20000:
		await process_frame
		if _fruit() == before - 1 and _phase() == "idle":
			break
	var paid := int(_errand_state().get("toss_paid", 0))
	var seq := int(_errand_state().get("toss_seq", 0))
	print("EAT fruit=", _fruit(), " phase=", _phase(), " seq=", seq, " paid=", paid)
	if _fruit() != before - 1 or paid != seq or paid <= 0:
		print("TOSS_IDEM_FAIL spend")
		quit(1)
		return
	main.queue_free()
	await process_frame
	await process_frame
	var reloaded := await _boot()
	if reloaded == null:
		quit(1)
		return
	print("RELOAD fruit=", _fruit(), " phase=", _phase(), " paid=", int(_errand_state().get("toss_paid", 0)))
	if _fruit() != before - 1 or int(_errand_state().get("toss_paid", 0)) != paid:
		print("TOSS_IDEM_FAIL reload duplicated or dropped the fruit")
		quit(1)
		return
	var none := str(reloaded.get_node("GardenErrand").call("press_food"))
	if none != "none" or _fruit() != before - 1:
		print("TOSS_IDEM_FAIL empty press ", none)
		quit(1)
		return
	print("TOSS_IDEM_OK")
	quit(0)


func _boot() -> Node:
	var main := (load("res://scenes/Main.tscn") as PackedScene).instantiate()
	root.add_child(main)
	for _i in range(240):
		await process_frame
		if main.get("pet") != null and main.get_node_or_null("GardenErrand") != null:
			return main
	print("TOSS_IDEM_FAIL no errand")
	return null


func _fixture(main: Node, fruit_target: int) -> void:
	var sim := root.get_node("Sim")
	var needs: Dictionary = sim.state.get("needs", {})
	needs["hunger"] = 40.0
	needs["energy"] = 80.0
	sim.state["needs"] = needs
	sim.state["sleeping"] = false
	var have := _fruit()
	if have < fruit_target:
		root.get_node("CollectionSystem").call("add_fruit", "starberry", fruit_target - have)
	print("FIXTURE fruit=", _fruit(), " hunger=40")


func _fruit() -> int:
	return int(root.get_node("CollectionSystem").call("fruit_count", "starberry"))


func _errand_state() -> Dictionary:
	var task: Variant = root.get_node("Sim").state.get("errand", {})
	return task if task is Dictionary else {}


func _phase() -> String:
	return str(_errand_state().get("phase", ""))
