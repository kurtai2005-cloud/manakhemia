extends SceneTree
## Rendered capture of normal Main. Clicks go through the live ray.
## Fixture steps are marked in the trace. This file does not print a pass
## until the PNG files exist and reload.

const ERRAND_PROFILE := "vc27_errand_capture"
const PROGRESS_PROFILE := "vc27_progress_capture"

var _out := ""
var _stage := ""
var _main: Node
var _deadline := 0
var _trace: FileAccess
var _shots: Array[String] = []
var _reason := ""
var _inputs_seen := 0
var _drew := false


func _initialize() -> void:
	var udir := OS.get_user_data_dir()
	print("capture user_dir=", udir)
	if not _profile_ok(udir):
		_die(2, "profile rejected")
		return
	_stage = OS.get_environment("CAPTURE_STAGE")
	_out = OS.get_environment("CAPTURE_OUT")
	if not _out_ok():
		_die(2, _reason if _reason != "" else "output folder rejected")
		return
	var limit := int(OS.get_environment("CAPTURE_MAX_MS"))
	if limit <= 0:
		limit = 200000
	_deadline = Time.get_ticks_msec() + limit
	_trace = FileAccess.open(_out.path_join("trace.jsonl"), FileAccess.WRITE)
	if _trace == null:
		_die(1, "cannot open trace")
		return
	_main = (load("res://scenes/Main.tscn") as PackedScene).instantiate()
	root.add_child(_main)
	process_frame.connect(_boot)


func _boot() -> void:
	process_frame.disconnect(_boot)
	await _run()


func _run() -> void:
	if not await _wait_ready():
		_die(1, "pet did not appear")
		return
	var ok := false
	match _stage:
		"errand_out":
			ok = await _errand_out()
		"errand_resume":
			ok = await _errand_resume()
		"progress":
			ok = await _progress()
		_:
			_die(2, "unknown stage")
			return
	if not ok:
		_die(1, _reason if _reason != "" else "stage failed")
		return
	if not _validate_pngs():
		_die(1, _reason if _reason != "" else "png validation failed")
		return
	_write_result(true, "")
	print("CAPTURE_OK stage=", _stage, " pngs=", _shots.size(), " renderer=", RenderingServer.get_current_rendering_method(), " display=", DisplayServer.get_name())
	quit(0)


func _errand_out() -> bool:
	if not await _shot("01_berry_ground", "observe"):
		return false
	if not await _click_berry("02_walk_started"):
		return false
	if not await _until_phase("carry", 800, "pickup"):
		return false
	return await _shot("03_carry_visible", "observe")


func _errand_resume() -> bool:
	var sim := _sim()
	var phase := str(_errand_state().get("phase", ""))
	var fruits := _fruits()
	if phase != "carry":
		_reason = "reopen is not carrying"
		return false
	if not await _shot("04_reopen_carry", "observe"):
		return false
	var before := fruits
	if not await _until_phase("idle", 800, "drop"):
		return false
	if _fruits() != before + 1:
		_reason = "drop did not pay exactly one"
		return false
	if not await _shot("05_drop_receipt", "observe"):
		return false
	var berry: Node3D = _errand().get("berry")
	if berry == null or not berry.visible:
		_reason = "berry did not respawn"
		return false
	if not await _shot("06_berry_respawn", "observe"):
		return false
	var paid := int(_errand_state().get("paid_through", 0))
	if not await _click_berry("07_second_walk"):
		return false
	if not await _until_phase("carry", 800, "second pickup"):
		return false
	if int(_errand_state().get("paid_through", 0)) != paid:
		_reason = "second pickup paid early"
		return false
	if not await _shot("07_second_carry", "observe"):
		return false
	return await _care_pair()


func _progress() -> bool:
	if not await _shot("01_berry_ground", "observe"):
		return false
	if not await _click_berry("02_walk_started"):
		return false
	if not await _until_phase("idle", 1400, "first delivery"):
		return false
	if _fruits() != 1:
		_reason = "first delivery count"
		return false
	if not await _shot("02_drop_receipt", "observe"):
		return false
	if not await _click_berry("03_second_walk"):
		return false
	if not await _until_phase("idle", 1400, "second delivery"):
		return false
	if _fruits() != 2:
		_reason = "second delivery count"
		return false
	_fixture_need("hunger", 40.0)
	if not await _click_home("04_meal_walk"):
		return false
	if not await _until_phase("idle", 800, "meal"):
		return false
	if _fruits() != 1 or int(_errand_state().get("meals", 0)) < 1:
		_reason = "meal did not spend one fruit"
		return false
	if not await _shot("04_meal", "observe"):
		return false
	var held := _fruits()
	_fixture_need("hunger", 95.0)
	if not await _click_home("05_refusal_click"):
		return false
	await process_frame
	if _fruits() != held:
		_reason = "refusal spent a fruit"
		return false
	if not await _shot("05_refusal", "observe"):
		return false
	_fixture_need("hunger", 10.0)
	_sim().get("state")["growth_sec"] = 0.0
	_sim().call("step", _sim().get("state"), 10.0, {})
	_line({"shot": "06_growth_paused", "driver": "fixture", "note": "unwell step is not player time"})
	if float(_sim().get("state").get("growth_sec", 0.0)) > 0.01:
		_reason = "unwell growth moved"
		return false
	if not await _shot("06_growth_paused", "fixture"):
		return false
	_fixture_need("hunger", 40.0)
	if not await _click_home("07_growth_meal"):
		return false
	if not await _until_phase("idle", 800, "second meal"):
		return false
	_sim().get("state")["growth_sec"] = 0.0
	_sim().call("step", _sim().get("state"), 10.0, {})
	_line({"shot": "07_growth_resumed", "driver": "fixture", "note": "well step is not player time"})
	if float(_sim().get("state").get("growth_sec", 0.0)) <= 0.0:
		_reason = "growth did not resume"
		return false
	if not await _shot("07_growth_resumed", "fixture"):
		return false
	_fixture_need("energy", 30.0)
	if not await _click_home("08_rest_walk"):
		return false
	if not await _until_interior(true, 800, "rest"):
		return false
	if not bool(_sim().get("state").get("sleeping", false)):
		_reason = "rest did not sleep"
		return false
	if not await _shot("08_rest_interior", "observe"):
		return false
	_sim().call("advance", _sim().get("state"), 10.0 * 3600.0, {})
	_line({"shot": "09_wake_garden", "driver": "fixture", "note": "ten hour advance is not player time"})
	if not await _until_interior(false, 60, "wake"):
		return false
	return await _shot("09_wake_garden", "observe")


func _care_pair() -> bool:
	var walker := _pet()
	var pres := _main.get_node_or_null("Hd2dPresentation")
	if pres == null or not pres.has_method("play_care"):
		_reason = "presentation missing"
		return false
	walker.set("dir", "front")
	_line({"shot": "08_care_front", "driver": "fixture", "note": "facing and care clip are not a player click"})
	if not bool(pres.call("play_care", "nuzzle")):
		_reason = "front care did not start"
		return false
	await process_frame
	if not await _shot("08_care_front", "fixture"):
		return false
	if pres.has_method("cancel_care"):
		pres.call("cancel_care")
	walker.set("dir", "back")
	_line({"shot": "09_care_back", "driver": "fixture", "note": "back facing must not flip the coat"})
	if not bool(pres.call("play_care", "eat")):
		_reason = "back care did not start"
		return false
	await process_frame
	var coat: Sprite3D = walker.get_node_or_null("Hd2dCoat")
	if coat == null or not coat.visible or coat.flip_h:
		_reason = "back care flipped or hid the coat"
		return false
	if not await _shot("09_care_back", "fixture"):
		return false
	if pres.has_method("cancel_care"):
		pres.call("cancel_care")
	return true


func _click_berry(shot: String) -> bool:
	var errand := _errand()
	var point: Vector3 = errand.get("berry_pos")
	return await _click_world(point + Vector3(0, 6, 0), shot)


func _click_home(shot: String) -> bool:
	var errand := _errand()
	var point: Vector3 = errand.get("home_pos")
	return await _click_world(point + Vector3(0, 6, 0), shot)


func _click_world(point: Vector3, shot: String) -> bool:
	var cam: Camera3D = _main.get("cam")
	if cam == null:
		_reason = "camera missing"
		return false
	var screen := cam.unproject_position(point)
	var vp := _main.get_viewport()
	var size := vp.get_visible_rect().size
	if screen.x < 0.0 or screen.y < 0.0 or screen.x > size.x or screen.y > size.y:
		_reason = "click is off the window"
		return false
	var before := int(_main.get("play_inputs"))
	var ev := InputEventMouseButton.new()
	ev.button_index = MOUSE_BUTTON_LEFT
	ev.pressed = true
	ev.position = screen
	ev.global_position = screen
	vp.push_input(ev)
	await process_frame
	await process_frame
	var after := int(_main.get("play_inputs"))
	if after <= before:
		_reason = "click did not reach Main"
		return false
	_inputs_seen += after - before
	_line({"shot": shot, "driver": "input", "note": "viewport mouse button through Main raycast", "screen": [screen.x, screen.y]})
	return await _shot(shot, "input")


func _until_phase(phase: String, frames: int, why: String) -> bool:
	for _i in range(frames):
		if Time.get_ticks_msec() > _deadline:
			_reason = "timeout " + why
			return false
		await process_frame
		if str(_errand_state().get("phase", "")) == phase:
			return true
		if str(_errand_state().get("phase", "")) == "blocked":
			_reason = "path blocked during " + why
			return false
	_reason = "timeout " + why
	return false


func _until_interior(inside: bool, frames: int, why: String) -> bool:
	for _i in range(frames):
		if Time.get_ticks_msec() > _deadline:
			_reason = "timeout " + why
			return false
		await process_frame
		if bool(_main.get("in_interior")) == inside:
			return true
	_reason = "timeout " + why
	return false


func _wait_ready() -> bool:
	for _i in range(300):
		if Time.get_ticks_msec() > _deadline:
			return false
		await process_frame
		if _main.get("pet") != null and _main.get_node_or_null("GardenErrand") != null and _main.get("cam") != null:
			await process_frame
			await process_frame
			return true
	return false


func _shot(name: String, driver: String) -> bool:
	if Time.get_ticks_msec() > _deadline:
		_reason = "timeout before " + name
		return false
	_drew = false
	var draw_path := "frame_post_draw"
	if not RenderingServer.frame_post_draw.is_connected(_mark_drawn):
		RenderingServer.frame_post_draw.connect(_mark_drawn)
	for _i in range(8):
		await process_frame
		if _drew:
			break
	if not _drew:
		RenderingServer.force_draw()
		draw_path = "force_draw"
	var vp := _main.get_viewport()
	var img := _viewport_image(vp)
	if img == null or img.is_empty() or img.get_width() < 8 or img.get_height() < 8:
		_reason = "viewport image missing for " + name
		return false
	var path := _out.path_join(name + ".png")
	if img.save_png(path) != OK:
		_reason = "png write failed for " + name
		return false
	if not _png_file_ok(path):
		_reason = "png rejected for " + name
		return false
	_shots.append(name)
	_line({"shot": name, "driver": driver, "png": name + ".png", "draw_path": draw_path})
	return true


func _line(extra: Dictionary) -> void:
	var walker := _pet()
	var coat: Sprite3D = walker.get_node_or_null("Hd2dCoat") if walker else null
	var berry: Node3D = _errand().get("berry") if _errand() else null
	var held: Node3D = walker.get_node_or_null("CarriedBerry") if walker else null
	var home: Sprite3D = _errand().get("home") if _errand() else null
	var needs: Dictionary = _sim().get("state").get("needs", {})
	var task := _errand_state()
	var faces := 0
	if walker:
		for child in walker.get_children():
			if child is Sprite3D and (child as Sprite3D).visible and str(child.name).begins_with("Face_"):
				faces += 1
	var row := {
		"stage": _stage,
		"shot": str(extra.get("shot", "")),
		"driver": str(extra.get("driver", "")),
		"note": str(extra.get("note", "")),
		"phase": str(task.get("phase", "")),
		"pos": [walker.global_position.x, walker.global_position.y, walker.global_position.z] if walker else [],
		"berry_visible": berry != null and berry.visible,
		"held_visible": held != null and held.visible,
		"home_alpha": home.modulate.a if home else -1.0,
		"fruit_count": _fruits(),
		"open_seq": int(task.get("open_seq", 0)),
		"paid_through": int(task.get("paid_through", 0)),
		"meals": int(task.get("meals", 0)),
		"hunger": float(needs.get("hunger", -1)),
		"energy": float(needs.get("energy", -1)),
		"growth_sec": float(_sim().get("state").get("growth_sec", 0)),
		"stage_name": str(_sim().get("state").get("stage", "")),
		"sleeping": bool(_sim().get("state").get("sleeping", false)),
		"in_interior": bool(_main.get("in_interior")),
		"coat": "Hd2dCoat" if coat else "",
		"coat_visible": coat != null and coat.visible,
		"coat_flip_h": coat.flip_h if coat else false,
		"dir": str(walker.get("dir")) if walker else "",
		"face_sprites": faces,
		"renderer": RenderingServer.get_current_rendering_method(),
		"display": DisplayServer.get_name(),
		"play_inputs": int(_main.get("play_inputs")),
		"png": str(extra.get("png", "")),
		"draw_path": str(extra.get("draw_path", "")),
	}
	if extra.has("screen"):
		row["screen"] = extra["screen"]
	_trace.store_line(JSON.stringify(row))
	_trace.flush()


func _mark_drawn() -> void:
	_drew = true


func _viewport_image(vp: Viewport) -> Image:
	if vp == null:
		return null
	var tex := vp.get_texture()
	if tex:
		var from_tex := tex.get_image()
		if from_tex and not from_tex.is_empty() and from_tex.get_width() >= 8:
			return from_tex
	var rid := RenderingServer.viewport_get_texture(vp.get_viewport_rid())
	if rid.is_valid():
		var from_rid := RenderingServer.texture_2d_get(rid)
		if from_rid and not from_rid.is_empty() and from_rid.get_width() >= 8:
			return from_rid
	return null


func _png_file_ok(path: String) -> bool:
	if not FileAccess.file_exists(path):
		return false
	var bytes := FileAccess.get_file_as_bytes(path)
	if bytes.size() < 64:
		return false
	var sig := PackedByteArray([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a])
	for i in range(sig.size()):
		if bytes[i] != sig[i]:
			return false
	var check := Image.new()
	if check.load(path) != OK:
		return false
	return check.get_width() >= 8 and check.get_height() >= 8


func _validate_pngs() -> bool:
	if _shots.is_empty():
		_reason = "no shots"
		return false
	for name in _shots:
		var path := _out.path_join(name + ".png")
		if not _png_file_ok(path):
			_reason = "final png check failed " + name
			return false
	return true


func _fixture_need(key: String, value: float) -> void:
	var needs: Dictionary = _sim().get("state").get("needs", {})
	needs[key] = value
	_sim().get("state")["needs"] = needs
	_line({"shot": "fixture_" + key, "driver": "fixture", "note": "need write is not player input"})


func _profile_ok(udir: String) -> bool:
	var norm := udir.replace("\\", "/").to_lower()
	if norm.find("vc27_play_36bfd") >= 0:
		print("FAIL profile is the player save")
		return false
	var want := ERRAND_PROFILE if _stage_family() == "errand" else PROGRESS_PROFILE
	if _stage != "errand_out" and _stage != "errand_resume" and _stage != "progress":
		print("FAIL stage")
		return false
	if not norm.ends_with("/" + want) and not norm.ends_with("\\" + want):
		print("FAIL profile is not ", want)
		return false
	return true


func _stage_family() -> String:
	_stage = OS.get_environment("CAPTURE_STAGE")
	if _stage.begins_with("errand"):
		return "errand"
	return "progress"


func _out_ok() -> bool:
	if _out == "" or not _out.is_absolute_path():
		_reason = "output folder must be absolute"
		return false
	var norm := _out.replace("\\", "/").to_lower()
	if norm.find("vc27_play_36bfd") >= 0:
		_reason = "output folder touches the player profile"
		return false
	var udir := OS.get_user_data_dir().replace("\\", "/").to_lower()
	if norm == udir or norm.begins_with(udir + "/"):
		_reason = "output folder is inside the capture profile"
		return false
	var proj := OS.get_environment("CAPTURE_PROJECT").replace("\\", "/")
	if proj != "" and (_out.replace("\\", "/") == proj or _out.replace("\\", "/").begins_with(proj + "/")):
		_reason = "output folder is inside the project"
		return false
	if not DirAccess.dir_exists_absolute(_out):
		_reason = "output folder does not exist"
		return false
	if _stage == "errand_out" or _stage == "progress":
		var dir := DirAccess.open(_out)
		if dir == null:
			_reason = "output folder cannot be read"
			return false
		dir.list_dir_begin()
		var fn := dir.get_next()
		while fn != "":
			if fn != "." and fn != "..":
				_reason = "output folder is not empty"
				dir.list_dir_end()
				return false
			fn = dir.get_next()
		dir.list_dir_end()
	return true


func _sim() -> Node:
	return root.get_node("Sim")


func _errand() -> Node:
	return _main.get_node("GardenErrand")


func _pet() -> Node3D:
	return _main.get("pet")


func _errand_state() -> Dictionary:
	var raw: Variant = _sim().get("state").get("errand", {})
	return raw if raw is Dictionary else {}


func _fruits() -> int:
	return int(root.get_node("CollectionSystem").call("fruit_count", "starberry"))


func _write_result(ok: bool, reason: String) -> void:
	var row := {
		"ok": ok,
		"stage": _stage,
		"reason": reason,
		"user_dir": OS.get_user_data_dir(),
		"renderer": RenderingServer.get_current_rendering_method(),
		"display": DisplayServer.get_name(),
		"shots": _shots,
		"play_inputs": _inputs_seen,
		"headless_note": "A headless or software display is not a GPU or phone pass.",
	}
	var f := FileAccess.open(_out.path_join("result.json"), FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify(row, "\t"))
		f.flush()
		f.close()


func _die(code: int, reason: String) -> void:
	print("FAIL ", reason)
	if _out != "" and DirAccess.dir_exists_absolute(_out):
		_write_result(false, reason)
	quit(code)
