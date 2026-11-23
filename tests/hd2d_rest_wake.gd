extends SceneTree
## Narrow check that an asleep interior pet leaves at the wake point.
## enter_house here is fixture placement. No button is pressed.
## Hunger and energy writes are fixture setup.

func _initialize() -> void:
	var udir := OS.get_user_data_dir()
	print("rest_wake user_dir=", udir)
	if udir.find("vc27_play_36bfd") >= 0 or udir.find("vc27_rest_wake") < 0:
		print("REST_WAKE_FAIL profile")
		quit(2)
		return
	var main := (load("res://scenes/Main.tscn") as PackedScene).instantiate()
	root.add_child(main)
	for _i in range(240):
		await process_frame
		if main.get("pet") != null and main.get_node_or_null("GardenErrand") != null:
			break
	if main.get_node_or_null("GardenErrand") == null:
		print("REST_WAKE_FAIL no errand")
		quit(1)
		return
	var sim := root.get_node("Sim")
	var inputs_before := int(main.get("play_inputs"))
	var needs: Dictionary = sim.state.get("needs", {})
	needs["hunger"] = 50.0
	needs["energy"] = 40.0
	sim.state["needs"] = needs
	var task: Dictionary = sim.state.get("errand", {})
	task["phase"] = "asleep"
	task["meals"] = 1
	sim.state["errand"] = task
	sim.set_sleeping(true)
	print("FIXTURE placement enter_house, energy=40, hunger=50, meals=1, phase=asleep")
	main.call("enter_house", true)
	await process_frame
	await process_frame
	if not bool(main.get("in_interior")) or not bool(sim.state.get("sleeping", false)):
		print("REST_WAKE_FAIL did not stay asleep inside below wake")
		quit(1)
		return
	if str(sim.state.get("errand", {}).get("phase", "")) != "asleep":
		print("REST_WAKE_FAIL phase left asleep before wake")
		quit(1)
		return
	needs = sim.state.get("needs", {})
	needs["energy"] = float(sim.get("SLEEP_WAKE_AT"))
	sim.state["needs"] = needs
	print("FIXTURE energy set to SLEEP_WAKE_AT, no button")
	for _i in range(30):
		await process_frame
		if not bool(main.get("in_interior")) and not bool(sim.state.get("sleeping", false)):
			break
	var phase := str(sim.state.get("errand", {}).get("phase", ""))
	var inside := bool(main.get("in_interior"))
	var sleeping := bool(sim.state.get("sleeping", false))
	var inputs_after := int(main.get("play_inputs"))
	print("RESULT inside=", inside, " sleeping=", sleeping, " phase=", phase, " inputs=", inputs_before, "->", inputs_after)
	if inside or sleeping or phase != "idle" or inputs_after != inputs_before:
		print("REST_WAKE_FAIL")
		quit(1)
		return
	print("REST_WAKE_OK")
	quit(0)
