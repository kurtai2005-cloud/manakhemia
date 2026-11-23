extends SceneTree
## Screen-touch route. A mouse event with device -1 is the click Android
## synthesizes from the same finger. Calling gameplay methods is not this test.

var _main: Node


func _initialize() -> void:
	var udir := OS.get_user_data_dir()
	print("touch user_dir=", udir)
	if udir.find("vc27_play_36bfd") >= 0 or udir.find("vc27_draft_try") >= 0 or udir.find("vc27_android_touch") < 0:
		print("TOUCH_FAIL profile")
		quit(2)
		return
	_main = (load("res://scenes/Main.tscn") as PackedScene).instantiate()
	root.add_child(_main)
	if not await _ready_pet():
		_die("pet did not appear")
		return
	var hud: Node = _main.get("hud")
	if hud == null or bool(hud.get("observing")) or bool(hud.get("care_bar").visible):
		_die("care row was open before a pet tap")
		return
	var errand: Node = _main.get_node("GardenErrand")
	var berry: Vector3 = errand.get("berry_pos")
	var screen := (_main.get("cam") as Camera3D).unproject_position(berry)
	_touch(screen, true)
	await _frames(2)
	_mouse(screen)
	await _frames(2)
	if str(errand.call("_task").get("phase", "")) != "to_pick":
		_die("finger touch did not keep the berry carry")
		return
	_touch(screen, true)
	await _frames(2)
	if str(errand.call("_task").get("phase", "")) != "idle":
		_die("a second finger touch did not cancel")
		return
	var dispatch := _button("派工")
	if dispatch == null:
		_die("dispatch button missing")
		return
	var at: Vector2 = dispatch.get_global_rect().get_center()
	_touch(at, true)
	_touch(at, false)
	await _frames(4)
	if bool(hud.get("care_bar").visible) or bool(hud.get("observing")):
		_die("care row stayed up after dispatch")
		return
	var card: CanvasItem = hud.get("card")
	if card and card.visible:
		var until := Time.get_ticks_msec() + 8000
		while card.visible and Time.get_ticks_msec() < until:
			await process_frame
		if card.visible:
			_die("summary card stayed up")
			return
	_touch(screen, true)
	_mouse(screen)
	await _frames(2)
	if str(errand.call("_task").get("phase", "")) != "to_pick":
		_die("berry touch was blocked after the card")
		return
	_touch(screen, true)
	await _frames(2)
	var house: Node3D = _main.get_node_or_null("HouseClick")
	if house == null:
		_die("house click missing")
		return
	var door_screen := (_main.get("cam") as Camera3D).unproject_position(house.global_position)
	_touch(door_screen, true)
	await _frames(2)
	var entered := Time.get_ticks_msec() + 25000
	while not bool(_main.get("in_interior")) and Time.get_ticks_msec() < entered:
		await process_frame
	if not bool(_main.get("in_interior")):
		var pres := _main.get_node_or_null("Hd2dPresentation")
		var pet_now: Node3D = _main.get("pet")
		print("DOOR_DEBUG pending=", _main.get("_door_pending"), " pos=", pet_now.global_position, " errand=", pet_now.get("errand_active"), " blocked=", pet_now.get("errand_blocked"), " arrived=", pres.get("arrived") if pres else "none", " approaching=", pres.get("approaching") if pres else "none", " goal=", pres.get("goal") if pres else "none")
		_die("door touch did not enter")
		return
	var back := _button("返回")
	if back == null or not back.visible:
		_die("back button missing inside")
		return
	var back_at: Vector2 = back.get_global_rect().get_center()
	_touch(back_at, true)
	_touch(back_at, false)
	var left := Time.get_ticks_msec() + 8000
	while bool(_main.get("in_interior")) and Time.get_ticks_msec() < left:
		await process_frame
	if bool(_main.get("in_interior")):
		_die("back touch did not leave")
		return
	var pet: Node3D = _main.get("pet")
	var coat := pet.get_node_or_null("Hd2dCoat") as Sprite3D
	var cam := _main.get("cam") as Camera3D
	if coat == null or not coat.visible:
		_die("pet coat hidden after leaving")
		return
	var p := cam.unproject_position(coat.global_position)
	var sz := _main.get_viewport().get_visible_rect().size
	var framed := p.x >= 0.0 and p.y >= 0.0 and p.x <= sz.x and p.y <= sz.y and not cam.is_position_behind(coat.global_position)
	if not framed:
		_die("pet not on screen after leaving")
		return
	if pet.global_position.z < -200.0:
		_die("pet still at the interior")
		return
	var room := _main.get_node_or_null("InteriorRoom")
	if room and room.visible:
		_die("interior still showing outside")
		return
	print("TOUCH_OK berry=kept card=dismissed pet_on_screen=true")
	quit(0)


func _ready_pet() -> bool:
	for _i in range(240):
		await process_frame
		if _main.get("pet") != null and _main.get_node_or_null("GardenErrand") != null and _main.get("hud") != null:
			return true
	return false


func _frames(n: int) -> void:
	for _i in range(n):
		await process_frame


func _touch(screen: Vector2, pressed: bool) -> void:
	var ev := InputEventScreenTouch.new()
	ev.index = 0
	ev.pressed = pressed
	ev.position = screen
	_main.get_viewport().push_input(ev)


func _mouse(screen: Vector2) -> void:
	var ev := InputEventMouseButton.new()
	ev.button_index = MOUSE_BUTTON_LEFT
	ev.pressed = true
	ev.position = screen
	ev.global_position = screen
	ev.device = -1
	_main.get_viewport().push_input(ev)


func _button(text: String) -> BaseButton:
	var hud: Node = _main.get("hud")
	if hud == null:
		return null
	for c in hud.find_children("*", "BaseButton", true, false):
		if not c.visible:
			continue
		if str(c.text) == text:
			return c
		for ch in c.find_children("*", "Label", true, false):
			if str(ch.text) == text:
				return c
	return null


func _die(why: String) -> void:
	print("TOUCH_FAIL ", why)
	quit(1)
