extends SceneTree
## Three enter/exit cycles, a pending rest, back, save, and the prairie clamp.

var _fails := 0


func _initialize() -> void:
	var font := load("res://art/fonts/vc27_label_fallback.otf") as Font
	var cook := font != null and font.has_char(0x716E) and font.has_char(0x563F)
	print("FONT_COOK_HEY=", cook)
	if not cook:
		_fails += 1
	var main: Node = (load("res://scenes/Main.tscn") as PackedScene).instantiate()
	root.add_child(main)
	for _i in range(220):
		await process_frame
		if main.get_node_or_null("Phase1Hud") != null:
			break
	var p1: Node = root.get_node("Phase1")
	if p1.hud.modal and p1.hud.modal.visible:
		p1.close_modal()
	var pet: Node3D = main.get("pet")
	for cycle in range(3):
		var before := pet.global_position
		main.request_house_enter()
		var entered := await _until(main, "in_interior", true, 14000)
		var leave: Button = p1.hud.leave_btn
		print("CYCLE", cycle, " ENTER=", entered, " LEAVE=", leave.visible if leave else false, " LOCK=", main.get("_interior_lock_cam"))
		if not entered or leave == null or not leave.visible:
			_fails += 1
		main.request_house_exit()
		var left := await _until(main, "in_interior", false, 8000)
		var at: Vector3 = pet.global_position
		var near := Vector2(at.x, at.z).distance_to(Vector2(94, -13)) < 28.0
		print("CYCLE", cycle, " EXIT=", left, " PET=", at, " NEAR_DOOR=", near, " LOCK=", main.get("_interior_lock_cam"))
		if not left or not near or bool(main.get("_interior_lock_cam")):
			_fails += 1
		if pet.global_position.distance_to(before) < 1.0 and cycle == 0:
			print("PET_DID_NOT_TRAVEL")
			_fails += 1
		await _ms(1600)
	await _ms(1600)
	var errand := main.get_node_or_null("GardenErrand")
	if errand and errand.has_method("_start_door_rest"):
		errand.call("_start_door_rest")
	main.request_house_enter()
	var job_in := await _until(main, "in_interior", true, 14000)
	print("JOB_ENTER=", job_in, " LEG=", main.get("_house_leg"))
	if not job_in:
		_fails += 1
	var sim: Node = root.get_node_or_null("Sim")
	if sim:
		var state: Dictionary = sim.get("state")
		state["phase1_inside"] = true
		sim.set("state", state)
		if sim.has_method("_save_now"):
			sim.call("_save_now")
		print("SAVED_INSIDE=", sim.get("state").get("phase1_inside"))
	main.notification(Node.NOTIFICATION_WM_GO_BACK_REQUEST)
	var backed := await _until(main, "in_interior", false, 8000)
	print("BACK_EXIT=", backed)
	if not backed:
		_fails += 1
	main.phase1_on = true
	main.phase1_to = Vector3(240, 58, -100)
	main.phase1_pan(Vector2(0, 5000))
	print("PAN_Z=", main.phase1_to.z)
	if main.phase1_to.z > -680.0:
		print("PAN_EXCLUDES_PRAIRIE")
		_fails += 1
	print("R15_DOOR_FAILS=", _fails)
	quit(_fails)


func _until(main: Node, prop: String, want: bool, ms: int) -> bool:
	var start := Time.get_ticks_msec()
	while Time.get_ticks_msec() - start < ms:
		await process_frame
		if bool(main.get(prop)) == want:
			return true
	return false


func _ms(ms: int) -> void:
	var start := Time.get_ticks_msec()
	while Time.get_ticks_msec() - start < ms:
		await process_frame
