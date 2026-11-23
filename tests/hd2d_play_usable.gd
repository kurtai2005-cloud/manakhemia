extends SceneTree
## Player-input proof of the forage, meal, and door loop.
## Needs values written here are fixture setup and are labeled in the trace.
## This file does not call enter_house or exit_house.

var _out := ""
var _main: Node
var _deadline := 0
var _trace: FileAccess
var _reason := ""
var _shots: Array[String] = []
var _drew := false
var _motion := 0
var _clicked := false


func _initialize() -> void:
	var udir := OS.get_user_data_dir()
	print("usable user_dir=", udir)
	if udir.find("vc27_play_36bfd") >= 0 or udir.find("vc27_play_usable") < 0:
		_die(2, "profile rejected")
		return
	_out = OS.get_environment("VC27_USABLE_OUT")
	if _out == "" or _out.find("vc27_play_36bfd") >= 0 or not DirAccess.dir_exists_absolute(_out):
		_die(2, "output folder rejected")
		return
	_deadline = Time.get_ticks_msec() + 420000
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
	if not _hud_clear():
		_die(1, _reason)
		return
	_fixture_needs(40.0, 80.0, "forage setup")
	if not await _click_world(_berry_point(), "01_berry"):
		_die(1, _reason)
		return
	if not await _motion_until("carry", 6):
		_die(1, _reason)
		return
	if not await _shot("02_carry", "input"):
		_die(1, _reason)
		return
	if not await _care_pause_resume():
		_die(1, _reason)
		return
	if not await _until_fruit(1, "first drop"):
		_die(1, _reason)
		return
	if not await _shot("05_drop", "input"):
		_die(1, _reason)
		return
	var goal_now := _hud().find_child("GoalBar", true, false) as Control
	var berry_now: Vector2 = (_main.get("cam") as Camera3D).unproject_position(_berry_point())
	if goal_now != null and goal_now.visible and goal_now.get_global_rect().has_point(berry_now):
		_die(1, "goal buttons cover the berry")
		return
	if not await _click_world(_berry_point(), "06_berry_again"):
		_die(1, _reason)
		return
	if not await _until_fruit(2, "second drop"):
		_die(1, _reason)
		return
	if not await _shot("06_second", "input"):
		_die(1, _reason)
		return
	if str(_hud().find_child("FoodCount", true, false).text) != "2":
		_die(1, "stored food count is not 2")
		return
	var goal := _hud().find_child("GoalBar", true, false) as Control
	var berry_screen: Vector2 = (_main.get("cam") as Camera3D).unproject_position(_berry_point())
	if goal != null and goal.visible and goal.get_global_rect().has_point(berry_screen):
		_die(1, "goal buttons cover the berry")
		return
	if str(_home_texture()).find("need_eat") < 0:
		_die(1, "home marker is not the eat icon")
		return
	if not await _click_button("GoalFood", "07_meal"):
		_die(1, _reason)
		return
	if not await _until_fruit(1, "meal spend"):
		_die(1, _reason)
		return
	if not await _shot("07_meal", "input"):
		_die(1, _reason)
		return
	if str(_hud().find_child("FoodCount", true, false).text) != "1":
		_die(1, "stored food count did not fall to 1")
		return
	_fixture_needs(95.0, 80.0, "refusal setup")
	var before := _fruit()
	if not await _click_button("GoalFood", "08_refusal"):
		_die(1, _reason)
		return
	await process_frame
	await process_frame
	if _fruit() != before:
		_die(1, "refusal spent a fruit")
		return
	if not await _shot("08_refusal", "input"):
		_die(1, _reason)
		return
	_fixture_needs(40.0, 60.0, "rest setup")
	if not _errand().call("rest_offered"):
		_die(1, "rest button is not offered")
		return
	if str(_home_texture()).find("need_sleep") < 0 and str(_home_texture()).find("need_eat") < 0:
		_die(1, "home marker has no action icon")
		return
	if not await _click_button("GoalRest", "09_rest"):
		_die(1, _reason)
		return
	if not await _until_phase("to_rest", 90, "door approach"):
		_die(1, _reason)
		return
	if bool(_main.get("in_interior")):
		_die(1, "entered before the outside frame")
		return
	if not await _shot("09_door", "input"):
		_die(1, _reason)
		return
	if not await _until_inside(true, 900, "door arrival"):
		_die(1, _reason)
		return
	if not await _shot("10_inside", "input"):
		_die(1, _reason)
		return
	if not await _click_button("返回", "11_exit", true):
		_die(1, _reason)
		return
	if not await _until_inside(false, 180, "return button"):
		_die(1, _reason)
		return
	await _wait_fade()
	if not await _shot("11_exit", "input"):
		_die(1, _reason)
		return
	if not await _click_world(_door_point() + Vector3(0, 18, 0), "12_door_click"):
		_die(1, _reason)
		return
	if not await _until_inside(true, 900, "door click"):
		_die(1, _reason)
		return
	if not await _shot("12_inside_click", "input"):
		_die(1, _reason)
		return
	if not await _click_button("返回", "13_out", true):
		_die(1, _reason)
		return
	if not await _until_inside(false, 180, "second return"):
		_die(1, _reason)
		return
	if not _pngs_ok():
		_die(1, _reason)
		return
	_write(true, "")
	print("PLAY_USABLE_OK shots=", _shots.size(), " motion=", _motion)
	quit(0)


func _hud_clear() -> bool:
	var dev := _button("開發者")
	if dev != null and dev.visible:
		_reason = "developer button is visible in normal mode"
		return false
	var admire := _button("欣賞")
	var bar := _hud().get("bar") as Control
	if admire == null or bar == null:
		_reason = "hud buttons missing"
		return false
	if admire.get_global_rect().intersects(bar.get_global_rect()):
		_reason = "appreciate overlaps the bottom buttons"
		return false
	_line({"shot": "hud", "driver": "observe", "note": "developer hidden, appreciate clear of the bottom row"})
	return true


func _care_pause_resume() -> bool:
	var pet := _pet()
	var pres := _main.get_node("Hd2dPresentation")
	var origin := pet.global_position
	if not pres.has_method("play_care"):
		_reason = "care missing"
		return false
	if not bool(pres.call("play_care", "eat")):
		_reason = "care clip did not start"
		return false
	await process_frame
	if pet.global_position.distance_to(origin) > 0.35:
		_reason = "care did not hold the carry"
		return false
	if not await _shot("03_pause", "input"):
		return false
	for _i in range(40):
		await process_frame
		if pres.has_method("care_active") and not bool(pres.call("care_active")):
			break
	var held := pet.global_position
	var moved := false
	for _i in range(90):
		await process_frame
		if pet.global_position.distance_to(held) > 1.0:
			moved = true
			break
	if not moved:
		_reason = "carry did not resume after care"
		return false
	return await _shot("04_resume", "input")


func _motion_until(phase: String, limit: int) -> bool:
	var last := _pet().global_position
	for _i in range(600):
		if Time.get_ticks_msec() > _deadline:
			_reason = "timeout motion"
			return false
		await process_frame
		var now: Vector3 = _pet().global_position
		if _motion < limit and now.distance_to(last) > 1.5:
			_motion += 1
			if not await _shot("motion_%02d" % _motion, "input"):
				return false
			last = now
		if str(_state().get("phase", "")) == phase:
			return true
		if str(_state().get("phase", "")) == "blocked":
			_reason = "path blocked"
			return false
	_reason = "timeout before " + phase
	return false


func _click_world(point: Vector3, shot: String) -> bool:
	var cam: Camera3D = _main.get("cam")
	if cam == null:
		_reason = "camera missing"
		return false
	var screen := cam.unproject_position(point)
	var vp := _main.get_viewport()
	var size := vp.get_visible_rect().size
	if screen.x < 0.0 or screen.y < 0.0 or screen.x > size.x or screen.y > size.y:
		_reason = shot + " is off the window"
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
	if int(_main.get("play_inputs")) <= before:
		_reason = shot + " did not reach Main"
		return false
	_line({"shot": shot, "driver": "input", "screen": [screen.x, screen.y]})
	return true


func _click_button(name_or_text: String, shot: String, by_text: bool = false) -> bool:
	var btn := _button(name_or_text) if by_text else _hud().find_child(name_or_text, true, false) as Button
	if btn == null or not btn.visible:
		_reason = shot + " button missing"
		return false
	_clicked = false
	if not btn.pressed.is_connected(_mark_click):
		btn.pressed.connect(_mark_click)
	var screen := btn.get_global_rect().get_center()
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
	await process_frame
	if btn.pressed.is_connected(_mark_click):
		btn.pressed.disconnect(_mark_click)
	if not _clicked:
		_reason = shot + " button did not fire"
		return false
	_line({"shot": shot, "driver": "input", "button": name_or_text, "screen": [screen.x, screen.y]})
	return true


func _mark_click() -> void:
	_clicked = true


func _fixture_needs(hunger: float, energy: float, note: String) -> void:
	var sim := root.get_node("Sim")
	var needs: Dictionary = sim.state.get("needs", {})
	needs["hunger"] = hunger
	needs["energy"] = energy
	sim.state["needs"] = needs
	sim.state["sleeping"] = false
	_line({"shot": note, "driver": "fixture", "note": "needs only, clock unchanged", "hunger": hunger, "energy": energy})


func _until_fruit(want: int, why: String) -> bool:
	for _i in range(900):
		if Time.get_ticks_msec() > _deadline:
			_reason = "timeout " + why
			return false
		await process_frame
		if _fruit() == want and str(_state().get("phase", "")) == "idle":
			return true
		if str(_state().get("phase", "")) == "blocked":
			_reason = "blocked during " + why
			return false
	_reason = "timeout " + why
	return false


func _until_phase(phase: String, frames: int, why: String) -> bool:
	for _i in range(frames):
		await process_frame
		if str(_state().get("phase", "")) == phase:
			return true
	_reason = "timeout " + why
	return false


func _wait_fade() -> void:
	var start := Time.get_ticks_msec()
	while Time.get_ticks_msec() - start < 4000:
		await process_frame
		var fade := _main.get("_fade_rect") as ColorRect
		if fade == null or fade.color.a < 0.15:
			return


func _until_inside(inside: bool, _frames: int, why: String) -> bool:
	var start := Time.get_ticks_msec()
	while Time.get_ticks_msec() - start < 25000:
		if Time.get_ticks_msec() > _deadline:
			_reason = "timeout " + why
			return false
		await process_frame
		if bool(_main.get("in_interior")) == inside:
			return true
	var where := _pet().global_position if _pet() else Vector3.ZERO
	_reason = "timeout %s at %s" % [why, where]
	return false


func _shot(name: String, driver: String) -> bool:
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
	var img := _main.get_viewport().get_texture().get_image()
	if img == null or img.is_empty() or img.get_width() < 8:
		_reason = "image missing for " + name
		return false
	var path := _out.path_join(name + ".png")
	if img.save_png(path) != OK or not _png_ok(path):
		_reason = "png rejected for " + name
		return false
	_shots.append(name)
	_line({"shot": name, "driver": driver, "png": name + ".png", "draw_path": draw_path})
	return true


func _mark_drawn() -> void:
	_drew = true


func _line(extra: Dictionary) -> void:
	var walker := _pet()
	var needs: Dictionary = root.get_node("Sim").state.get("needs", {})
	var row := {
		"shot": str(extra.get("shot", "")),
		"driver": str(extra.get("driver", "")),
		"phase": str(_state().get("phase", "")),
		"fruit": _fruit(),
		"hunger": float(needs.get("hunger", 0)),
		"energy": float(needs.get("energy", 0)),
		"inside": bool(_main.get("in_interior")),
		"pos": [walker.global_position.x, walker.global_position.z] if walker else [],
		"renderer_setting": str(ProjectSettings.get_setting("rendering/renderer/rendering_method")),
		"renderer": _running_renderer(),
		"rendering_driver": _running_driver(),
		"display": str(DisplayServer.get_name()),
	}
	row.merge(extra, true)
	_trace.store_line(JSON.stringify(row))
	_trace.flush()


func _png_ok(path: String) -> bool:
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null or f.get_length() < 64:
		return false
	var sig := f.get_buffer(8)
	f.close()
	if sig.size() < 8 or sig[0] != 137 or sig[1] != 80:
		return false
	var img := Image.new()
	return img.load(path) == OK and img.get_width() >= 8 and img.get_height() >= 8


func _pngs_ok() -> bool:
	if _shots.size() < 8 or _motion < 3:
		_reason = "not enough frames"
		return false
	for name in _shots:
		if not _png_ok(_out.path_join(name + ".png")):
			_reason = "missing " + name
			return false
	return true


func _wait_ready() -> bool:
	for _i in range(300):
		await process_frame
		if _main.get("pet") != null and _main.get_node_or_null("GardenErrand") != null and _main.get("cam") != null:
			await process_frame
			return true
	return false


func _berry_point() -> Vector3:
	return _errand().get("berry_pos") + Vector3(0, 8, 0)


func _door_point() -> Vector3:
	var door := _main.get_node_or_null("HouseClick") as Node3D
	if door == null:
		return Vector3(94, 12, -29)
	return door.global_position


func _home_texture() -> String:
	var home := _errand().get("home") as Sprite3D
	if home == null or home.texture == null:
		return ""
	return home.texture.resource_path


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


func _errand() -> Node:
	return _main.get_node("GardenErrand")


func _pet() -> Node3D:
	return _main.get("pet") as Node3D


func _hud() -> Node:
	return _main.get("hud")


func _button(text: String) -> Button:
	var hud := _hud()
	if hud == null:
		return null
	for child in hud.find_children("*", "Button", true, false):
		if child is Button and (child as Button).text == text:
			return child
	return null


func _write(ok: bool, reason: String) -> void:
	var f := FileAccess.open(_out.path_join("result.json"), FileAccess.WRITE)
	if f == null:
		return
	f.store_string(JSON.stringify({"ok": ok, "reason": reason, "shots": _shots, "motion": _motion, "head": "see shell"}, "\t"))
	f.close()


func _die(code: int, reason: String) -> void:
	print("PLAY_USABLE_FAIL ", reason)
	_write(false, reason)
	quit(code)
