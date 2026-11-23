extends SceneTree
## Continuous sampled frames of normal inputs.
## Hunger, energy, and the starting fruit are fixture setup and are labeled.
## This file does not call play_care, enter_house, or exit_house.

var _out := ""
var _frames_dir := ""
var _main: Node
var _deadline := 0
var _trace: FileAccess
var _reason := ""
var _frame := 0
var _sample_n := 0
var _segment := ""
var _opening := Vector3.ZERO
var _opening_fov := 0.0
var _saw_eat := false
var _saw_happy := false
var _saw_nuzzle := false
var _saw_toss := false
var _saw_carry := false


func _initialize() -> void:
	var udir := OS.get_user_data_dir()
	print("motion user_dir=", udir)
	if udir.find("vc27_play_36bfd") >= 0 or udir.find("vc27_motion_capture") < 0:
		_die(2, "profile rejected")
		return
	_out = OS.get_environment("VC27_MOTION_OUT")
	if _out == "" or _out.find("vc27_play_36bfd") >= 0 or not DirAccess.dir_exists_absolute(_out):
		_die(2, "output folder rejected")
		return
	_frames_dir = _out.path_join("frames")
	DirAccess.make_dir_recursive_absolute(_frames_dir)
	_deadline = Time.get_ticks_msec() + 300000
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
	var cam: Camera3D = _main.get("cam")
	_opening = cam.global_position
	_opening_fov = cam.fov
	_fixture("before sequence", 40.0, 85.0, 1)
	_segment = "toss"
	if not await _click_tip("餵", "toss_input"):
		_die(1, _reason)
		return
	if not await _until_care("eat", "chew"):
		_die(1, _reason)
		return
	if not _saw_toss:
		_die(1, "tossed fruit was not visible")
		return
	if not await _until_care("emo_happy", "happy"):
		_die(1, _reason)
		return
	if _fruit() != 0:
		_die(1, "meal did not spend the setup fruit")
		return
	_segment = "forage"
	if not await _click_world(_berry_point(), "berry_input"):
		_die(1, _reason)
		return
	if not await _until_phase("carry", "pickup"):
		_die(1, _reason)
		return
	if not _saw_carry:
		_die(1, "carried fruit was not visible")
		return
	if not await _until_fruit(1, "deliver"):
		_die(1, _reason)
		return
	_fixture("refusal", 95.0, 85.0, -1)
	var held := _fruit()
	_segment = "refusal"
	if not await _click_tip("餵", "refusal_input"):
		_die(1, _reason)
		return
	await _sample_for(12)
	if _fruit() != held or str(_state().get("phase", "")) != "idle":
		_die(1, "full pet spent or tossed food")
		return
	_fixture("after refusal", 40.0, 85.0, -1)
	_segment = "pat"
	if not await _click_tip("摸", "pat_input"):
		_die(1, _reason)
		return
	if not await _until_care("nuzzle", "pat"):
		_die(1, _reason)
		return
	_segment = "rest_early"
	if not await _click_named("GoalRest", "rest_input"):
		_die(1, _reason)
		return
	if not await _until_inside(true, "door"):
		_die(1, _reason)
		return
	await _sample_for(18)
	if not await _click_text("返回", "early_return"):
		_die(1, _reason)
		return
	if not await _until_inside(false, "early_out"):
		_die(1, _reason)
		return
	if not await _until_camera("early return camera"):
		_die(1, _reason)
		return
	if str(_state().get("phase", "")) == "asleep" or bool(root.get_node("Sim").state.get("sleeping", false)):
		_die(1, "early return left the pet asleep")
		return
	_fixture("before auto-wake rest", 40.0, 60.0, -1)
	_segment = "rest_auto"
	if not await _click_named("GoalRest", "rest_again"):
		_die(1, _reason)
		return
	if not await _until_inside(true, "door_again"):
		_die(1, _reason)
		return
	_fixture("wake threshold", 40.0, 100.0, -1)
	if not await _until_inside(false, "auto_wake"):
		_die(1, _reason)
		return
	if not await _until_camera("auto-wake camera"):
		_die(1, _reason)
		return
	if str(_state().get("phase", "")) == "asleep" or bool(root.get_node("Sim").state.get("sleeping", false)):
		_die(1, "auto-wake left the pet asleep")
		return
	if not (_saw_eat and _saw_happy and _saw_nuzzle):
		_die(1, "missing eat, happy, or pat reaction")
		return
	_write(true, "")
	print("MOTION_CAPTURE_OK frames=", _frame, " renderer=", _running_renderer(), " driver=", _running_driver())
	quit(0)


func _fixture(note: String, hunger: float, energy: float, fruit_add: int) -> void:
	var sim := root.get_node("Sim")
	var needs: Dictionary = sim.state.get("needs", {})
	needs["hunger"] = hunger
	needs["energy"] = energy
	sim.state["needs"] = needs
	if note != "wake threshold":
		sim.state["sleeping"] = false
	if fruit_add > 0 and _fruit() < fruit_add:
		root.get_node("CollectionSystem").call("add_fruit", "starberry", fruit_add - _fruit())
	_line({"shot": note, "driver": "fixture", "note": "needs or starting fruit only"})


func _until_care(id: String, why: String) -> bool:
	var start := Time.get_ticks_msec()
	while Time.get_ticks_msec() - start < 45000:
		if Time.get_ticks_msec() > _deadline:
			_reason = "timeout " + why
			return false
		await process_frame
		_maybe_frame()
		var pres := _main.get_node_or_null("Hd2dPresentation")
		var now := str(pres.call("care_id")) if pres and pres.has_method("care_id") else ""
		if now == id:
			return true
	_reason = "timeout " + why
	return false


func _until_phase(phase: String, why: String) -> bool:
	var start := Time.get_ticks_msec()
	while Time.get_ticks_msec() - start < 40000:
		if Time.get_ticks_msec() > _deadline:
			_reason = "timeout " + why
			return false
		await process_frame
		_maybe_frame()
		if str(_state().get("phase", "")) == phase:
			return true
		if str(_state().get("phase", "")) == "blocked":
			_reason = "blocked " + why
			return false
	_reason = "timeout " + why
	return false


func _until_fruit(want: int, why: String) -> bool:
	var start := Time.get_ticks_msec()
	while Time.get_ticks_msec() - start < 40000:
		if Time.get_ticks_msec() > _deadline:
			_reason = "timeout " + why
			return false
		await process_frame
		_maybe_frame()
		if _fruit() == want and str(_state().get("phase", "")) == "idle":
			return true
	_reason = "timeout " + why
	return false


func _until_inside(inside: bool, why: String) -> bool:
	var start := Time.get_ticks_msec()
	while Time.get_ticks_msec() - start < 50000:
		if Time.get_ticks_msec() > _deadline:
			_reason = "timeout " + why
			return false
		await process_frame
		_maybe_frame()
		if bool(_main.get("in_interior")) == inside:
			return true
	_reason = "timeout " + why
	return false


func _sample_for(frames: int) -> void:
	for _i in range(frames):
		await process_frame
		_maybe_frame()


func _maybe_frame() -> void:
	_note_visuals()
	_sample_n += 1
	if _sample_n < 6:
		return
	_sample_n = 0
	_save_frame()


func _note_visuals() -> void:
	var pres := _main.get_node_or_null("Hd2dPresentation")
	var id := str(pres.call("care_id")) if pres and pres.has_method("care_id") else ""
	if id == "eat":
		_saw_eat = true
	elif id == "emo_happy":
		_saw_happy = true
	elif id == "nuzzle":
		_saw_nuzzle = true
	var toss := _main.get_node_or_null("GardenErrand/TossedFood") as Node3D
	if toss and toss.visible:
		_saw_toss = true
	var pet := _pet()
	var held := pet.get_node_or_null("CarriedBerry") if pet else null
	if held and held.visible:
		_saw_carry = true


func _save_frame() -> void:
	var img := _main.get_viewport().get_texture().get_image()
	if img == null or img.is_empty():
		return
	img.resize(270, 584, Image.INTERPOLATE_NEAREST)
	_frame += 1
	var name := "f_%04d.jpg" % _frame
	img.save_jpg(_frames_dir.path_join(name), 0.62)
	_line({"shot": _segment, "driver": "frame", "png": "frames/" + name})


func _click_tip(tip: String, shot: String) -> bool:
	var btn := _tip(tip)
	if btn == null or not btn.visible:
		_reason = shot + " button missing"
		return false
	return await _click_at(btn.get_global_rect().get_center(), shot, false)


func _click_text(text: String, shot: String) -> bool:
	var btn := _text(text)
	if btn == null or not btn.visible:
		_reason = shot + " button missing"
		return false
	return await _click_at(btn.get_global_rect().get_center(), shot, false)


func _click_named(node_name: String, shot: String) -> bool:
	await process_frame
	await process_frame
	var btn := _hud().find_child(node_name, true, false) as Button
	if btn == null or not btn.visible:
		_reason = shot + " button missing"
		return false
	return await _click_at(btn.get_global_rect().get_center(), shot, false)


func _click_world(point: Vector3, shot: String) -> bool:
	var cam: Camera3D = _main.get("cam")
	var screen := cam.unproject_position(point)
	var size := _main.get_viewport().get_visible_rect().size
	if screen.x < 0.0 or screen.y < 0.0 or screen.x > size.x or screen.y > size.y:
		_reason = shot + " off the window"
		return false
	return await _click_at(screen, shot, true)


func _click_at(screen: Vector2, shot: String, world: bool) -> bool:
	var before := int(_main.get("play_inputs"))
	var vp := _main.get_viewport()
	var down := InputEventMouseButton.new()
	down.button_index = MOUSE_BUTTON_LEFT
	down.pressed = true
	down.position = screen
	down.global_position = screen
	vp.push_input(down)
	await process_frame
	var up := InputEventMouseButton.new()
	up.button_index = MOUSE_BUTTON_LEFT
	up.pressed = false
	up.position = screen
	up.global_position = screen
	vp.push_input(up)
	await process_frame
	if world and int(_main.get("play_inputs")) <= before:
		_reason = shot + " did not reach Main"
		return false
	_line({"shot": shot, "driver": "input", "screen": [screen.x, screen.y]})
	_save_frame()
	return true


func _until_camera(why: String) -> bool:
	var start := Time.get_ticks_msec()
	while Time.get_ticks_msec() - start < 5000:
		await process_frame
		_maybe_frame()
		if _camera_ok():
			return true
	_reason = why + " left the opening view"
	return false


func _camera_ok() -> bool:
	var cam: Camera3D = _main.get("cam")
	if cam == null:
		return false
	return cam.global_position.distance_to(_opening) < 1.5 and absf(cam.fov - _opening_fov) < 0.2


func _wait_fade() -> void:
	var start := Time.get_ticks_msec()
	while Time.get_ticks_msec() - start < 4000:
		await process_frame
		_maybe_frame()
		var fade := _main.get("_fade_rect") as ColorRect
		if fade == null or fade.color.a < 0.15:
			return


func _wait_ready() -> bool:
	for _i in range(300):
		await process_frame
		if _main.get("pet") != null and _main.get_node_or_null("GardenErrand") != null and _main.get("cam") != null:
			await process_frame
			return true
	return false


func _berry_point() -> Vector3:
	return _main.get_node("GardenErrand").get("berry_pos") + Vector3(0, 18, 0)


func _line(extra: Dictionary) -> void:
	var walker := _pet()
	var pres := _main.get_node_or_null("Hd2dPresentation")
	var needs: Dictionary = root.get_node("Sim").state.get("needs", {})
	var row := {
		"segment": _segment,
		"shot": str(extra.get("shot", "")),
		"driver": str(extra.get("driver", "")),
		"phase": str(_state().get("phase", "")),
		"fruit": _fruit(),
		"hunger": float(needs.get("hunger", 0)),
		"energy": float(needs.get("energy", 0)),
		"inside": bool(_main.get("in_interior")),
		"sleeping": bool(root.get_node("Sim").state.get("sleeping", false)),
		"pos": [walker.global_position.x, walker.global_position.z] if walker else [],
		"care": str(pres.call("care_id")) if pres and pres.has_method("care_id") else "",
		"renderer_setting": str(ProjectSettings.get_setting("rendering/renderer/rendering_method")),
		"renderer": _running_renderer(),
		"rendering_driver": _running_driver(),
		"sample": "every 6th engine frame, playback 6 fps, not wall-clock realtime",
	}
	row.merge(extra, true)
	_trace.store_line(JSON.stringify(row))
	_trace.flush()


func _running_renderer() -> String:
	if RenderingServer.has_method("get_current_rendering_method"):
		return str(RenderingServer.call("get_current_rendering_method"))
	return ""


func _running_driver() -> String:
	if RenderingServer.has_method("get_current_rendering_driver_name"):
		return str(RenderingServer.call("get_current_rendering_driver_name"))
	return ""


func _fruit() -> int:
	return int(root.get_node("CollectionSystem").call("fruit_count", "starberry"))


func _state() -> Dictionary:
	var task: Variant = root.get_node("Sim").state.get("errand", {})
	return task if task is Dictionary else {}


func _pet() -> Node3D:
	return _main.get("pet") as Node3D


func _hud() -> Node:
	return _main.get("hud")


func _tip(tip: String) -> Button:
	for child in _hud().find_children("*", "Button", true, false):
		if child is Button and (child as Button).tooltip_text == tip:
			return child
	return null


func _text(text: String) -> Button:
	for child in _hud().find_children("*", "Button", true, false):
		if child is Button and (child as Button).text == text:
			return child
	return null


func _write(ok: bool, reason: String) -> void:
	var f := FileAccess.open(_out.path_join("result.json"), FileAccess.WRITE)
	if f == null:
		return
	f.store_string(JSON.stringify({
		"ok": ok,
		"reason": reason,
		"frames": _frame,
		"sample": "every 6th engine frame, playback 6 fps, not wall-clock realtime",
		"saw_toss": _saw_toss,
		"saw_carry": _saw_carry,
		"saw_eat": _saw_eat,
		"saw_happy": _saw_happy,
		"saw_nuzzle": _saw_nuzzle,
		"renderer": _running_renderer(),
		"rendering_driver": _running_driver(),
		"note": "Sampled game time. Not wall-clock realtime. Not RTX.",
	}, "\t"))
	f.close()


func _die(code: int, reason: String) -> void:
	print("MOTION_CAPTURE_FAIL ", reason)
	_write(false, reason)
	quit(code)
