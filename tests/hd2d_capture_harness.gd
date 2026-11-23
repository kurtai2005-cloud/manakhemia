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
var _combined: FileAccess
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
	_trace = FileAccess.open(_out.path_join("trace_%s.jsonl" % _stage), FileAccess.WRITE)
	if _trace == null:
		_die(1, "cannot open trace")
		return
	var combined_path := _out.path_join("trace.jsonl")
	if FileAccess.file_exists(combined_path):
		_combined = FileAccess.open(combined_path, FileAccess.READ_WRITE)
		if _combined:
			_combined.seek_end()
	else:
		_combined = FileAccess.open(combined_path, FileAccess.WRITE)
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
	var before_second := _fruits()
	if not await _click_berry("07_second_walk"):
		return false
	if not await _until_phase("carry", 800, "second pickup"):
		return false
	if int(_errand_state().get("paid_through", 0)) != paid or _fruits() != before_second:
		_reason = "second pickup paid early"
		return false
	if not await _shot("07_second_carry", "observe"):
		return false
	if not await _until_phase("idle", 800, "second drop"):
		return false
	if _fruits() != before_second + 1:
		_reason = "second drop did not pay exactly one"
		return false
	if not await _shot("07_second_drop", "observe"):
		return false
	var berry2: Node3D = _errand().get("berry")
	if berry2 == null or not berry2.visible:
		_reason = "berry did not respawn after the second drop"
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
	if not await _shot("04_before_meal", "observe"):
		return false
	if _fruits() != 2:
		_reason = "before-meal shot lost the fruit count"
		return false
	_fixture_need("hunger", 40.0)
	if not await _click_world(_errand().get("home_pos") + Vector3(0, 6, 0), "04_meal_click", false):
		return false
	if not await _until_phase("idle", 800, "meal"):
		return false
	if _fruits() != 1 or int(_errand_state().get("meals", 0)) < 1:
		_reason = "meal did not spend one fruit"
		return false
	if not await _shot("04_meal", "observe"):
		return false
	if not await _shot("05_before_refusal", "observe"):
		return false
	var held := _fruits()
	_fixture_need("hunger", 95.0)
	if not await _click_world(_errand().get("home_pos") + Vector3(0, 6, 0), "05_refusal_click", false):
		return false
	await process_frame
	await process_frame
	if _fruits() != held:
		_reason = "refusal spent a fruit"
		return false
	if not await _shot("05_refusal", "observe"):
		return false
	if _fruits() != held:
		_reason = "refusal shot does not match the inventory"
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
	var home_before: Vector3 = _errand().get("home_pos")
	if not await _click_berry("08_outward_click"):
		return false
	if not await _until_away(home_before, 12.0, 800, "outward walk"):
		return false
	if bool(_main.get("in_interior")):
		_reason = "entered during the outward walk"
		return false
	if not await _shot("08_rest_outward", "observe"):
		return false
	if not await _click_berry("08_outward_cancel"):
		return false
	await process_frame
	await process_frame
	if str(_errand_state().get("phase", "")) != "idle":
		_reason = "outward walk did not cancel"
		return false
	_fixture_need("energy", 30.0)
	Engine.time_scale = 0.02
	_line({"shot": "08_rest_pace", "driver": "fixture", "note": "time_scale 0.02 only spaces the walk across frames. It does not advance the sim hour or the HUD clock."})
	if not await _click_home("08_rest_click"):
		return false
	if not await _until_outside_rest(home_before, 800):
		return false
	if not await _shot("08_rest_approach", "observe"):
		return false
	Engine.time_scale = 1.0
	if bool(_main.get("in_interior")):
		_reason = "approach frame is already indoors"
		return false
	if not await _until_interior(true, 800, "rest"):
		return false
	if not bool(_sim().get("state").get("sleeping", false)):
		_reason = "rest did not sleep"
		return false
	var saw_pet := false
	for _inside in range(12):
		if not bool(_main.get("in_interior")):
			_reason = "left the house before the interior frame"
			return false
		var sleeper := _pet()
		if sleeper != null and _on_screen(sleeper.global_position + Vector3(0, 10, 0)):
			saw_pet = true
			break
		await process_frame
	if not saw_pet:
		var sleeper2 := _pet()
		_reason = "interior frame misses the pet at %s" % _screen_of(sleeper2.global_position + Vector3(0, 10, 0) if sleeper2 else Vector3.ZERO)
		return false
	var held_sleeper := _pet()
	held_sleeper.pause_t = 30.0
	held_sleeper.call("clear_errand")
	if not await _shot("08_rest_interior", "observe"):
		return false
	if not _on_screen(held_sleeper.global_position + Vector3(0, 10, 0)):
		_reason = "interior picture lost the pet"
		return false
	var wall_before := _wall_ms()
	var growth_before := float(_sim().get("state").get("growth_sec", 0.0))
	_sim().call("advance", _sim().get("state"), 10.0 * 3600.0, {})
	var wall_after := _wall_ms()
	_line({
		"shot": "09_sim_advance",
		"driver": "fixture",
		"note": "Sim.advance 10h changes growth and needs only. The HUD clock is TimeService wall time and is not set by this call.",
		"wall_before_ms": wall_before,
		"wall_after_ms": wall_after,
		"growth_before": growth_before,
	})
	if not await _until_interior(false, 90, "wake"):
		return false
	for _settle in range(8):
		await process_frame
	if not _play_garden_visible():
		return false
	if not await _shot("09_wake_garden", "observe"):
		return false
	if not _play_garden_visible():
		_reason = "wake frame lost the pet or the house"
		return false
	return true


func _care_pair() -> bool:
	var pres := _main.get_node_or_null("Hd2dPresentation")
	if pres == null or not pres.has_method("play_care"):
		_reason = "presentation missing"
		return false
	if not await _hold_projection("front", "08_care_front"):
		return false
	if not await _hold_projection("back", "09_care_back"):
		return false
	return true


func _hold_projection(want: String, shot: String) -> bool:
	if not await _step_facing(want):
		return false
	var walker := _pet()
	walker.pause_t = 60.0
	var held := walker.global_position
	_line({"shot": shot, "driver": "fixture", "note": "real step selected the %s projection. Not a player click." % want})
	if not _projection_is(want):
		return false
	walker.global_position = held
	if not await _shot(shot, "fixture"):
		return false
	walker.global_position = held
	if not _projection_is(want):
		return false
	return true


func _projection_is(want: String) -> bool:
	var pres := _main.get_node("Hd2dPresentation")
	var clip: Object = pres.get("clip")
	var coat: Sprite3D = _pet().get_node_or_null("Hd2dCoat")
	var facing := str(clip.get("facing")) if clip != null else ""
	var path := str(clip.call("texture_path")) if clip != null and clip.has_method("texture_path") else ""
	if facing != want or path.find(want) < 0 or coat == null or not coat.visible or coat.flip_h:
		_reason = "projection is %s %s flip=%s, wanted %s" % [facing, path, str(coat.flip_h if coat else true), want]
		return false
	return true


func _step_facing(want: String) -> bool:
	var walker := _pet()
	var cam: Camera3D = _main.get("cam")
	var pres := _main.get_node_or_null("Hd2dPresentation")
	if walker == null or cam == null or pres == null:
		_reason = "facing setup missing"
		return false
	walker.call("clear_errand")
	walker.pause_t = 60.0
	var away := Vector3(-cam.global_transform.basis.z.x, 0.0, -cam.global_transform.basis.z.z)
	var right := Vector3(cam.global_transform.basis.x.x, 0.0, cam.global_transform.basis.x.z)
	var choices: Array[Vector3] = [away, -away, right, -right]
	for raw in choices:
		var step: Vector3 = raw
		if step.length() < 0.001:
			continue
		step = step.normalized()
		for _i in range(4):
			walker.global_position += step * 1.5
			await process_frame
			var clip: Object = pres.get("clip")
			if clip != null and str(clip.get("facing")) == want:
				return true
	_reason = "coat did not face " + want
	return false


func _facing_is(want: String, care: String) -> bool:
	var pres := _main.get_node("Hd2dPresentation")
	var clip: Object = pres.get("clip")
	var coat: Sprite3D = _pet().get_node_or_null("Hd2dCoat")
	var facing := str(clip.get("facing")) if clip != null else ""
	var care_now := str(pres.call("care_id")) if pres.has_method("care_id") else ""
	if facing != want or care_now != care or coat == null or not coat.visible or coat.flip_h:
		_reason = "care frame is %s/%s flip=%s, wanted %s/%s" % [facing, care_now, str(coat.flip_h if coat else true), want, care]
		return false
	return true


func _click_berry(shot: String) -> bool:
	var errand := _errand()
	var point: Vector3 = errand.get("berry_pos")
	return await _click_world(point + Vector3(0, 6, 0), shot)


func _click_home(shot: String) -> bool:
	var errand := _errand()
	var point: Vector3 = errand.get("home_pos")
	return await _click_world(point + Vector3(0, 6, 0), shot)


func _click_world(point: Vector3, shot: String, take_shot: bool = true) -> bool:
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
	if not take_shot:
		return true
	return await _shot(shot, "input")


func _until_away(home: Vector3, min_dist: float, frames: int, why: String) -> bool:
	for _i in range(frames):
		if Time.get_ticks_msec() > _deadline:
			_reason = "timeout " + why
			return false
		await process_frame
		if bool(_main.get("in_interior")):
			_reason = "went inside during " + why
			return false
		var walker := _pet()
		if walker == null:
			_reason = "pet missing during " + why
			return false
		if Vector2(walker.global_position.x, walker.global_position.z).distance_to(Vector2(home.x, home.z)) >= min_dist:
			return true
	_reason = "timeout " + why
	return false


func _until_outside_rest(home: Vector3, frames: int) -> bool:
	for _i in range(frames):
		if Time.get_ticks_msec() > _deadline:
			_reason = "timeout outside rest approach"
			return false
		await process_frame
		if bool(_main.get("in_interior")):
			_reason = "entered before the outside rest frame"
			return false
		var walker := _pet()
		var phase := str(_errand_state().get("phase", ""))
		var dist := Vector2(walker.global_position.x, walker.global_position.z).distance_to(Vector2(home.x, home.z))
		if phase == "to_rest" and dist > 3.0:
			return true
	_reason = "timeout outside rest approach"
	return false


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
		"coat_facing": _coat_facing(),
		"care_id": _care_now(),
		"renderer": RenderingServer.get_current_rendering_method(),
		"display": DisplayServer.get_name(),
		"play_inputs": int(_main.get("play_inputs")),
		"png": str(extra.get("png", "")),
		"draw_path": str(extra.get("draw_path", "")),
	}
	if extra.has("screen"):
		row["screen"] = extra["screen"]
	var ts: Node = root.get_node("TimeService")
	var wall := int(ts.call("now_ms"))
	var local: Dictionary = ts.call("local_dict", wall)
	row["wall_unix_ms"] = wall
	row["wall_clock"] = "%02d:%02d:%02d" % [int(local.get("hour", 0)), int(local.get("minute", 0)), int(local.get("second", 0))]
	row["sim_age_sec"] = float(_sim().get("state").get("age_sec", 0.0))
	if extra.has("wall_before_ms"):
		row["wall_before_ms"] = extra["wall_before_ms"]
		row["wall_after_ms"] = extra["wall_after_ms"]
		row["growth_before"] = extra["growth_before"]
	var text := JSON.stringify(row)
	_trace.store_line(text)
	_trace.flush()
	if _combined:
		_combined.store_line(text)
		_combined.flush()


func _coat_facing() -> String:
	var pres := _main.get_node_or_null("Hd2dPresentation")
	if pres == null:
		return ""
	var clip: Object = pres.get("clip")
	return str(clip.get("facing")) if clip != null else ""


func _care_now() -> String:
	var pres := _main.get_node_or_null("Hd2dPresentation")
	if pres == null or not pres.has_method("care_id"):
		return ""
	return str(pres.call("care_id"))


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


func _wall_ms() -> int:
	return int(root.get_node("TimeService").call("now_ms"))


func _screen_of(world: Vector3) -> String:
	var cam: Camera3D = _main.get("cam")
	if cam == null:
		return "no-cam"
	if cam.is_position_behind(world):
		return "behind"
	var screen := cam.unproject_position(world)
	return "(%.0f,%.0f)" % [screen.x, screen.y]


func _on_screen(world: Vector3) -> bool:
	var cam: Camera3D = _main.get("cam")
	if cam == null or cam.is_position_behind(world):
		return false
	var screen := cam.unproject_position(world)
	var size := _main.get_viewport().get_visible_rect().size
	return screen.x > 12.0 and screen.y > 12.0 and screen.x < size.x - 12.0 and screen.y < size.y - 12.0


func _play_garden_visible() -> bool:
	if bool(_main.get("in_interior")):
		_reason = "garden frame is still indoors"
		return false
	var walker := _pet()
	var coat: Sprite3D = walker.get_node_or_null("Hd2dCoat") if walker else null
	if coat == null or not coat.visible:
		_reason = "garden frame has no coat"
		return false
	var pet_screen := _screen_of(walker.global_position + Vector3(0, 20, 0))
	if not _on_screen(walker.global_position + Vector3(0, 20, 0)):
		_reason = "pet is outside the settled garden frame at %s pos=%s" % [pet_screen, walker.global_position]
		return false
	var door: Vector3 = _main.call("cottage_door_world")
	var door_screen := _screen_of(door + Vector3(0, 20, 0))
	if not _on_screen(door + Vector3(0, 20, 0)):
		_reason = "house is outside the settled garden frame at %s" % door_screen
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
	var f := FileAccess.open(_out.path_join("result_%s.json" % _stage), FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify(row, "\t"))
		f.flush()
		f.close()


func _die(code: int, reason: String) -> void:
	print("FAIL ", reason)
	if _out != "" and DirAccess.dir_exists_absolute(_out):
		_write_result(false, reason)
	quit(code)
