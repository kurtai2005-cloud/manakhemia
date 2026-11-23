extends SceneTree
## r4 idle. No forage, feed, rest, dispatch, hunt, or collect calls.
## The save is an already-played preview. This process only watches, then quits.

var _main: Node


func _initialize() -> void:
	var udir := OS.get_user_data_dir()
	print("r4 user_dir=", udir)
	if udir.find("vc27_life_r4") < 0 or udir.find("vc27_play_36bfd") >= 0 or udir.find("vc27_draft_try") >= 0:
		print("R4_FAIL profile")
		quit(2)
		return
	if OS.get_environment("VC27_DRAFT_PREVIEW") != "1":
		print("R4_FAIL env")
		quit(2)
		return
	var phase := OS.get_environment("VC27_LIFE_PHASE")
	if phase == "reread":
		await _reread()
		return
	_main = (load("res://scenes/Main.tscn") as PackedScene).instantiate()
	root.add_child(_main)
	if not await _pet():
		_die("pet missing")
		return
	if phase == "mid":
		await _mid()
		return
	if phase == "resume":
		await _resume()
		return
	if phase == "huntresume":
		await _hunt_resume()
		return
	await _outings()


func _pet() -> bool:
	var deadline := Time.get_ticks_msec() + 8000
	while Time.get_ticks_msec() < deadline:
		await process_frame
		var pet: Node = _main.get("pet")
		if pet != null:
			return true
	return false


func _outings() -> void:
	var sim: Node = root.get_node("Sim")
	var work: Node = root.get_node("WorkSystem")
	var hunt: Node = root.get_node("HuntSystem")
	var col: Node = root.get_node("CollectionSystem")
	var start := int(col.call("stardust"))
	var meals := int(sim.state.get("errand", {}).get("meals", 0))
	print("R4_BOOT stage=", sim.state.get("stage"), " meals=", meals, " shards=", start, " rug=", sim.state.get("house", {}).get("placed", {}).get("rug", ""), " glow=", bool(sim.state.get("collection", {}).get("discovered", {}).get("glow_berry", false)))
	if str(sim.state.get("stage", "")) != "newborn" or meals < 1 or start != 12:
		_die("fixture was reseeded")
		return
	var post_near := false
	var post_paid := false
	var gate_near := false
	var field_near := false
	var hunt_paid := false
	var moved_on_field := false
	var field_pos := Vector3.ZERO
	var deadline := Time.get_ticks_msec() + 150000
	var trace := 0
	while Time.get_ticks_msec() < deadline:
		await process_frame
		var pet: Node3D = _main.get("pet")
		var p: Vector3 = pet.global_position
		if str(work.site("post").get("status", "")) == "work" and p.x < -140.0 and p.z > 55.0:
			post_near = true
		if int(col.call("stardust")) == start + 2 and str(work.site("post").get("status", "")) == "empty":
			post_paid = true
		if str(hunt.phase) == "depart" and absf(p.x) < 8.0 and p.z < -20.0 and p.z > -50.0:
			gate_near = true
		if str(hunt.phase) == "hunt" and p.z > 400.0:
			field_near = true
			if field_pos == Vector3.ZERO:
				field_pos = p
			elif p.distance_to(field_pos) > 4.0:
				moved_on_field = true
		if post_paid and int(col.call("stardust")) > start + 2 and str(hunt.phase) == "idle":
			hunt_paid = true
			break
		if Time.get_ticks_msec() >= trace:
			trace = Time.get_ticks_msec() + 4000
			print("R4 t phase=", hunt.phase, " hold=", hunt.travel_hold, " post=", work.site("post").get("status"), " pos=", p, " shards=", col.call("stardust"), " blocked=", pet.get("errand_blocked"))
	print("R4_SEEN post_door=", post_near, " post_paid=", post_paid, " gate=", gate_near, " field=", field_near, " moved=", moved_on_field, " hunt_paid=", hunt_paid, " shards=", col.call("stardust"))
	if not post_near or not post_paid or not gate_near or not field_near or not moved_on_field or not hunt_paid:
		_die("outing incomplete")
		return
	var paid := int(col.call("stardust"))
	var fruits := _fruit_total()
	var critter := _critter()
	if fruits < 1 or critter == "":
		_die("hunt reward missing")
		return
	var hold := Time.get_ticks_msec() + 4000
	while Time.get_ticks_msec() < hold:
		await process_frame
	if int(col.call("stardust")) != paid or _fruit_total() != fruits or str(work.site("post").get("status", "")) != "empty" or str(work.site("kitchen").get("status", "")) == "work":
		_die("reward repeated")
		return
	if int(sim.state.get("errand", {}).get("meals", 0)) < 1 or str(sim.state.get("house", {}).get("placed", {}).get("rug", "")) != "rug_leaf":
		_die("r3 progress dropped")
		return
	root.get_node("Sim").notification(NOTIFICATION_APPLICATION_PAUSED)
	print("R4_OUTING_OK shards=", paid, " fruits=", fruits, " critter=", critter)
	quit(0)


func _mid() -> void:
	var work: Node = root.get_node("WorkSystem")
	var deadline := Time.get_ticks_msec() + 40000
	while Time.get_ticks_msec() < deadline:
		await process_frame
		var sit: Dictionary = work.site("post")
		if str(sit.get("status", "")) == "work" and float(sit.get("watch", 0.0)) > 1.0:
			root.get_node("Sim").notification(NOTIFICATION_APPLICATION_PAUSED)
			print("R4_MID_OK watch=", sit.get("watch"), " shards=", root.get_node("CollectionSystem").call("stardust"))
			quit(0)
			return
	_die("post did not start")


func _resume() -> void:
	var sim: Node = root.get_node("Sim")
	var work: Node = root.get_node("WorkSystem")
	var hunt: Node = root.get_node("HuntSystem")
	var col: Node = root.get_node("CollectionSystem")
	var start := int(col.call("stardust"))
	print("R4_RESUME_BOOT shards=", start, " post=", work.site("post").get("status"), " watch=", work.site("post").get("watch"), " hunt=", hunt.phase)
	if start != 12 or str(work.site("post").get("status", "")) != "work":
		_die("mid save was not kept")
		return
	var became_ready := false
	var deadline := Time.get_ticks_msec() + 30000
	while Time.get_ticks_msec() < deadline:
		await process_frame
		if str(work.site("post").get("status", "")) == "ready":
			became_ready = true
		if int(col.call("stardust")) == start + 2 and str(work.site("post").get("status", "")) == "empty":
			break
	if int(col.call("stardust")) != start + 2:
		_die("post pay on resume shards=%s ready=%s" % [col.call("stardust"), became_ready])
		return
	# Continue into the hunt and leave in the middle. One process, still no gameplay calls.
	var saw_hunt := false
	deadline = Time.get_ticks_msec() + 40000
	while Time.get_ticks_msec() < deadline:
		await process_frame
		if str(hunt.phase) == "hunt" and float(hunt.watch_elapsed) > 2.0:
			saw_hunt = true
			sim.notification(NOTIFICATION_APPLICATION_PAUSED)
			print("R4_HUNT_MID_OK watch=", hunt.watch_elapsed, " shards=", col.call("stardust"), " pos=", (_main.get("pet") as Node3D).global_position)
			quit(0)
			return
	_die("hunt did not resume into the field saw=%s phase=%s" % [saw_hunt, hunt.phase])


func _hunt_resume() -> void:
	var hunt: Node = root.get_node("HuntSystem")
	var col: Node = root.get_node("CollectionSystem")
	var work: Node = root.get_node("WorkSystem")
	var start := int(col.call("stardust"))
	print("R4_HUNT_RESUME_BOOT shards=", start, " phase=", hunt.phase, " watch=", hunt.watch_elapsed, " pending=", not hunt.pending.is_empty())
	if start != 14 or str(hunt.phase) == "idle" or str(hunt.phase) == "ready":
		_die("hunt mid save was not kept")
		return
	var deadline := Time.get_ticks_msec() + 30000
	var paid := false
	while Time.get_ticks_msec() < deadline:
		await process_frame
		if str(hunt.phase) == "idle" and int(col.call("stardust")) > start:
			paid = true
			break
	var end := int(col.call("stardust"))
	if not paid or end - start < 1 or end - start > 3 or _fruit_total() < 1:
		_die("hunt resume pay shards=%s fruits=%s" % [end, _fruit_total()])
		return
	var hold := Time.get_ticks_msec() + 3000
	while Time.get_ticks_msec() < hold:
		await process_frame
	if int(col.call("stardust")) != end or str(work.site("post").get("status", "")) != "empty":
		_die("second reward after resume")
		return
	root.get_node("Sim").notification(NOTIFICATION_APPLICATION_PAUSED)
	print("R4_HUNT_RESUME_OK shards=", end, " fruits=", _fruit_total())
	quit(0)


func _reread() -> void:
	for _i in range(30):
		await process_frame
	var sim: Node = root.get_node("Sim")
	var st: Dictionary = sim.state
	var shards := int(st.get("wallet", {}).get("stardust", -1))
	var meals := int(st.get("errand", {}).get("meals", 0))
	var rug := str(st.get("house", {}).get("placed", {}).get("rug", ""))
	var glow := bool(st.get("collection", {}).get("discovered", {}).get("glow_berry", false))
	var fruits := 0
	for k in st.get("collection", {}).get("fruits", {}).keys():
		fruits += int(st.get("collection", {}).get("fruits", {}).get(k, 0))
	var critters: Dictionary = st.get("collection", {}).get("critters", {})
	var post := str(st.get("jobs_state", {}).get("sites", {}).get("post", {}).get("status", ""))
	var pending: Dictionary = st.get("hunt", {}).get("pending", {})
	print("R4_REREAD stage=", st.get("stage"), " meals=", meals, " glow=", glow, " rug=", rug, " shards=", shards, " fruits=", fruits, " critters=", critters.size(), " post=", post, " pending=", not pending.is_empty())
	if str(st.get("stage", "")) != "newborn" or meals < 1 or not glow or rug != "rug_leaf":
		_die("r3 progress missing on reread")
		return
	if shards <= 14 or fruits < 1 or critters.is_empty() or post != "empty" or not pending.is_empty():
		_die("hunt or post did not stay saved")
		return
	print("R4_REREAD_OK")
	quit(0)


func _fruit_total() -> int:
	var n := 0
	var fr: Dictionary = root.get_node("Sim").state.get("collection", {}).get("fruits", {})
	for k in fr.keys():
		n += int(fr[k])
	return n


func _critter() -> String:
	var c: Dictionary = root.get_node("Sim").state.get("collection", {}).get("critters", {})
	for k in c.keys():
		if bool(c[k]):
			return str(k)
	return ""


func _die(why: String) -> void:
	print("R4_FAIL ", why)
	quit(1)
