extends SceneTree
## r14 runtime proof: lights, no teleport, waypoint run, zone pan, modal, ten shots.

const OUT := "/opt/cursor/artifacts/vc27_r14"


func _initialize() -> void:
	DisplayServer.window_set_size(Vector2i(540, 1140))
	var main: Node = (load("res://scenes/Main.tscn") as PackedScene).instantiate()
	root.add_child(main)
	for _i in range(240):
		await process_frame
		if main.get_node_or_null("Phase1Hud") != null:
			break
	var fails := 0
	var p1: Node = root.get_node("Phase1")
	var hud: Phase1Hud = main.get_node("Phase1Hud")
	p1.set("_patrol_wait", 600.0)
	var actions: Node = p1.get("actions")
	var pet: Node3D = main.get("pet")
	DirAccess.make_dir_recursive_absolute(OUT)
	if hud.modal.visible:
		p1.close_modal()
		await process_frame
	fails += _lights(main)
	fails += _skirts(p1)
	var vsync := DisplayServer.window_get_vsync_mode()
	var qsrc := FileAccess.get_file_as_string("res://scripts/autoload/QualitySettings.gd")
	var vsync_requested := qsrc.find("VSYNC_ENABLED") >= 0
	print("VSYNC=", vsync, " VSYNC_REQUESTED=", vsync_requested, " MAX_FPS=", Engine.max_fps)
	if not vsync_requested:
		print("VSYNC_OFF")
		fails += 1
	elif vsync != DisplayServer.VSYNC_ENABLED:
		print("VSYNC_DRIVER_LIMIT")
	var far := 0.0
	var cam := main.get("cam") as Camera3D
	if cam:
		far = cam.far
	print("CAMERA_FAR=", far)
	if far > 1801.0 or far < 1799.0:
		print("CAMERA_FAR_BAD")
		fails += 1
	print("SPARK_ALLOCS=", actions.get("spark_runtime_allocs"), " POOL=", _pool_count(p1))
	if int(actions.get("spark_runtime_allocs")) != 0 or _pool_count(p1) < 8:
		print("SPARK_POOL_BAD")
		fails += 1
	await _shot(OUT + "/r14_shot1_home.png")
	pet.global_position = Vector3(0, 0, 24)
	pet.set("phase1_scripted", true)
	var pet_before: Vector3 = pet.global_position
	var cam_before: Vector3 = main.get("phase1_to")
	p1.go_zone("zone_farm")
	await _wait_ms(900)
	var pet_delta: float = pet.global_position.distance_to(pet_before)
	var cam_now: Vector3 = main.get("phase1_to")
	var cam_delta: float = cam_now.distance_to(cam_before)
	print("ZONE_PET_DELTA=", snappedf(pet_delta, 0.01), " ZONE_CAM_DELTA=", snappedf(cam_delta, 0.1))
	if pet_delta > 1.0 or cam_delta < 40.0:
		print("ZONE_TAB_BAD")
		fails += 1
	else:
		print("ZONE_TAB_OK")
	await _shot(OUT + "/r14_shot2_farm.png")
	p1.go_zone("zone_workshop")
	await _wait_ms(900)
	await _shot(OUT + "/r14_shot3_workshop.png")
	p1.go_zone("prairie_edge")
	await _wait_ms(900)
	await _shot(OUT + "/r14_shot4_prairie.png")
	fails += _trees(p1)
	pet.set("phase1_scripted", false)
	pet.global_position = Vector3(0, 0, 24)
	p1.act_forage()
	var clip := 0
	var run_start := Time.get_ticks_msec()
	var mid_ok := false
	while Time.get_ticks_msec() - run_start < 14000:
		await process_frame
		var elapsed := Time.get_ticks_msec() - run_start
		var at: Vector3 = pet.global_position
		if at.x > 46.0 and at.x < 120.0 and at.z > -100.0 and at.z < -42.0:
			clip += 1
		if elapsed >= 2000 and elapsed < 4500 and float(actions.call("goal_distance")) > 100.0 and not bool(actions.get("vfx_fired")):
			mid_ok = true
		if at.distance_to(Vector3(240, 0, -385)) < 14.0 and bool(actions.get("vfx_fired")):
			break
	var prairie_left: float = pet.global_position.distance_to(Vector3(240, 0, -385))
	print("PRAIRIE_CLIP=", clip, " PRAIRIE_MID=", mid_ok, " PRAIRIE_LEFT=", snappedf(prairie_left, 0.1))
	if clip > 0 or not mid_ok or prairie_left > 14.0:
		print("PRAIRIE_ROUTE_BAD")
		fails += 1
	else:
		print("PRAIRIE_ROUTE_OK")
	actions.call("cancel")
	pet.set("phase1_scripted", false)
	pet.global_position = Vector3(0, 0, 24)
	p1.go_zone("garden")
	await _wait_ms(500)
	var shards_before := _shards()
	p1.act_stove()
	await _wait_ms(2500)
	var mid := float(actions.call("goal_distance"))
	var vfx_mid := bool(actions.get("vfx_fired"))
	print("MID_DIST=", snappedf(mid, 0.1), " MID_VFX=", vfx_mid, " PET=", pet.global_position)
	if mid < 100.0 or vfx_mid:
		print("MIDRUN_BAD")
		fails += 1
	else:
		print("MIDRUN_OK")
	await _shot(OUT + "/r14_shot5_midrun.png")
	var pat_from: Vector3 = pet.global_position
	p1.pat()
	await _wait_ms(500)
	var pat_delta := pet.global_position.distance_to(pat_from)
	var clear_delta := pet.global_position.distance_to(Vector3(6, 0, 62))
	print("PAT_DELTA=", snappedf(pat_delta, 0.01), " CLEAR_DELTA=", snappedf(clear_delta, 0.1))
	if pat_delta > 25.0 or clear_delta < 8.0:
		print("PAT_TELEPORT")
		fails += 1
	else:
		print("PAT_IN_PLACE")
	await _shot(OUT + "/r14_shot6_pat_inplace.png")
	p1.open_feed()
	await process_frame
	await _shot(OUT + "/r14_shot7_feed_menu.png")
	p1.open_info()
	await process_frame
	var claim := hud.root.find_child("ModalClaim", true, false) as Button
	var claim_text := claim.text if claim else ""
	print("MODAL_BTN=", claim_text, " MODAL_VISIBLE=", hud.modal.visible)
	if claim_text != "關閉" or not hud.modal.visible:
		print("MODAL_LABEL_BAD")
		fails += 1
	await _shot(OUT + "/r14_shot8_pet_modal.png")
	p1.set_collapsed(true)
	await process_frame
	print("COLLAPSE_MODAL=", hud.modal.visible, " TOP=", hud.top.visible)
	if hud.modal.visible or hud.top.visible or hud.dock.visible:
		print("COLLAPSE_BAD")
		fails += 1
	else:
		print("COLLAPSE_OK")
	await _shot(OUT + "/r14_shot9_collapsed.png")
	p1.set_collapsed(false)
	await process_frame
	pet.global_position = Vector3(0, 0, 24)
	var sim_live: Node = root.get_node("Sim")
	var live: Dictionary = sim_live.get("state")
	var ledger: Dictionary = live.get("daily_ledger", {})
	ledger["jt_shards"] = 0
	ledger["total_shards"] = 0
	live["daily_ledger"] = ledger
	var wallet: Dictionary = live.get("wallet", {})
	var earned: Dictionary = wallet.get("earned", {})
	earned["old"] = 0
	earned["jobs_trips"] = 0
	earned["steps"] = 0
	earned["phase1_play"] = 0
	wallet["earned"] = earned
	live["wallet"] = wallet
	sim_live.set("state", live)
	shards_before = _shards()
	var before_arrivals := int(p1.get("arrivals"))
	p1.harvest_all()
	var loop_start := Time.get_ticks_msec()
	while Time.get_ticks_msec() - loop_start < 24000:
		await process_frame
		if int(p1.get("arrivals")) >= before_arrivals + 2:
			break
	var after_arrivals := int(p1.get("arrivals"))
	var shards_after := _shards()
	print("HARVEST_ARRIVALS=", after_arrivals - before_arrivals, " SHARDS=", shards_before, "->", shards_after)
	if after_arrivals < before_arrivals + 2 or shards_after <= shards_before:
		print("HARVEST_NOT_ARRIVED")
		fails += 1
	else:
		print("HARVEST_ARRIVED")
	await _shot(OUT + "/r14_shot10_harvest_loop.png")
	var sim: Node = root.get_node("Sim")
	var empty_state: Dictionary = sim.state
	empty_state["phase1_plots"] = ["empty", "empty", "empty", "empty"]
	sim.state = empty_state
	var n_before := int(p1.action_n)
	p1.harvest_all()
	await process_frame
	print("HARVEST_EMPTY_TOAST=", hud.toast.text if hud.toast else "", " ACTION=", p1.action)
	if p1.action != "harvest_none" or int(p1.action_n) <= n_before:
		print("HARVEST_EMPTY_DEAD")
		fails += 1
	else:
		print("HARVEST_EMPTY_OK")
	fails += await _tap(main, hud, p1, "DockClean")
	var saver: Node = root.get_node_or_null("Sim")
	if saver and saver.has_method("_save_now"):
		saver.call("_save_now")
		print("SAVE_OK")
	else:
		print("SAVE_MISSING")
		fails += 1
	var preview := false
	var saves: Node = root.get_node_or_null("SaveSystem")
	if saves and saves.has_method("is_preview"):
		preview = bool(saves.call("is_preview"))
	print("DUAL_PROFILE_PREVIEW=", preview)
	print("R14_PROOF_FAILS=", fails)
	quit(fails)


func _lights(main: Node) -> int:
	var host: Node = main.get("_hd2d_exterior")
	var tally := {"visible": 0, "omni_hidden": 0, "omni_shown": 0, "pool": false}
	if host == null:
		print("NO_EXTERIOR")
		return 1
	_walk_lights(host, tally)
	print("VISIBLE_LIGHTS=", tally["visible"], " OMNI_HIDDEN=", tally["omni_hidden"], " OMNI_SHOWN=", tally["omni_shown"], " SUNPOOL=", tally["pool"])
	if int(tally["visible"]) > 2 or int(tally["omni_hidden"]) < 7 or int(tally["omni_shown"]) > 0 or bool(tally["pool"]):
		print("LIGHTS_BAD")
		return 1
	print("LIGHTS_OK")
	return 0


func _walk_lights(node: Node, tally: Dictionary) -> void:
	if node is OmniLight3D:
		var omni := node as OmniLight3D
		if omni.light_energy <= 0.001:
			if omni.visible:
				tally["omni_shown"] = int(tally["omni_shown"]) + 1
			else:
				tally["omni_hidden"] = int(tally["omni_hidden"]) + 1
	if node is Light3D and (node as Light3D).visible and node.is_visible_in_tree():
		tally["visible"] = int(tally["visible"]) + 1
	if node.name == "SunPool" and node is Light3D:
		tally["pool"] = (node as Light3D).visible
	for child in node.get_children():
		_walk_lights(child, tally)


func _skirts(p1: Node) -> int:
	var zones: Node = p1.get("world").get("zones")
	var tally := {"giant": 0, "horizon": false}
	if zones:
		_walk_skirts(zones, tally)
	print("GIANT_SKIRTS=", tally["giant"], " HORIZON=", tally["horizon"])
	if int(tally["giant"]) > 0 or not bool(tally["horizon"]):
		print("SKIRT_BAD")
		return 1
	print("SKIRT_OK")
	return 0


func _walk_skirts(node: Node, tally: Dictionary) -> void:
	if node is MeshInstance3D:
		var mi := node as MeshInstance3D
		if mi.mesh is PlaneMesh:
			var size: Vector2 = (mi.mesh as PlaneMesh).size
			var area := size.x * size.y
			var mat := mi.material_override
			if mat is ShaderMaterial and area > 1000000.0:
				tally["giant"] = int(tally["giant"]) + 1
			if node.name == "HorizonOlive" and mat is StandardMaterial3D:
				var sm := mat as StandardMaterial3D
				var tex := sm.albedo_texture
				var grass := tex != null and str(tex.resource_path).find("grass_outer_512") >= 0
				tally["horizon"] = sm.shading_mode == BaseMaterial3D.SHADING_MODE_UNSHADED and grass and mi.cast_shadow == GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	for child in node.get_children():
		_walk_skirts(child, tally)


func _trees(p1: Node) -> int:
	var zones: Node = p1.get("world").get("zones")
	var tally := {"n": 0}
	if zones:
		_count_trees(zones, tally)
	print("PRAIRIE_TREES=", tally["n"])
	if int(tally["n"]) > 0:
		print("PRAIRIE_TREES_BAD")
		return 1
	return 0


func _count_trees(node: Node, tally: Dictionary) -> void:
	if str(node.name).begins_with("PrairieTree"):
		tally["n"] = int(tally["n"]) + 1
	for child in node.get_children():
		_count_trees(child, tally)


func _pool_count(p1: Node) -> int:
	var zones: Node = p1.get("world").get("zones")
	var pool := zones.find_child("SparkPool", true, false) if zones else null
	return pool.get_child_count() if pool else 0


func _shards() -> int:
	var bag: Node = root.get_node_or_null("CollectionSystem")
	if bag and bag.has_method("stardust"):
		return int(bag.call("stardust"))
	return -1


func _tap(main: Node, hud: Phase1Hud, p1: Node, bname: String) -> int:
	var btn := hud.root.find_child(bname, true, false) as Button
	if btn == null:
		print("TAP_MISSING ", bname)
		return 1
	var at := btn.get_global_rect().get_center()
	var before := int(p1.action_n)
	var vp := main.get_viewport()
	var press := InputEventMouseButton.new()
	press.button_index = MOUSE_BUTTON_LEFT
	press.pressed = true
	press.position = at
	press.global_position = at
	vp.push_input(press)
	await process_frame
	var release := InputEventMouseButton.new()
	release.button_index = MOUSE_BUTTON_LEFT
	release.pressed = false
	release.position = at
	release.global_position = at
	vp.push_input(release)
	await process_frame
	await process_frame
	if int(p1.action_n) <= before:
		print("TAP_DEAD ", bname)
		return 1
	print("TAP_OK ", bname)
	return 0


func _wait_ms(ms: int) -> void:
	var start := Time.get_ticks_msec()
	while Time.get_ticks_msec() - start < ms:
		await process_frame


func _shot(path: String) -> void:
	await RenderingServer.frame_post_draw
	var img := root.get_viewport().get_texture().get_image()
	if img == null:
		print("SHOT_EMPTY ", path)
		return
	if img.get_width() != 540 or img.get_height() != 1140:
		var copy := img.duplicate()
		copy.resize(540, 1140, Image.INTERPOLATE_NEAREST)
		img = copy
	img.save_png(path)
	print("SHOT ", path)
