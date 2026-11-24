extends SceneTree

func _initialize() -> void:
	var main: Node = (load("res://scenes/Main.tscn") as PackedScene).instantiate()
	root.add_child(main)
	for _i in range(220):
		await process_frame
		if main.get_node_or_null("Phase1Hud") != null:
			break
	for _i in range(30):
		await process_frame
	var mode := OS.get_environment("R15_RELOAD")
	if mode == "check":
		print("RELOAD_INSIDE=", main.get("in_interior"))
		var pet: Node3D = main.get("pet")
		print("RELOAD_PET=", pet.global_position if pet else Vector3.ZERO)
		if bool(main.get("in_interior")) and main.has_method("request_house_exit"):
			main.request_house_exit()
			var start := Time.get_ticks_msec()
			while Time.get_ticks_msec() - start < 8000 and bool(main.get("in_interior")):
				await process_frame
		print("RELOAD_AFTER=", main.get("in_interior"))
		var sim: Node = root.get_node_or_null("Sim")
		if sim and sim.has_method("_save_now"):
			sim.call("_save_now")
		quit(0 if not bool(main.get("in_interior")) else 1)
		return
	if not bool(main.get("in_interior")):
		main.enter_house(true)
		await process_frame
	var sim: Node = root.get_node("Sim")
	if sim.has_method("_save_now"):
		sim.call("_save_now")
	print("ARMED_INSIDE=", main.get("in_interior"), " FLAG=", sim.get("state").get("phase1_inside"))
	quit(0 if bool(main.get("in_interior")) else 1)
