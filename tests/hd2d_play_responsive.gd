extends SceneTree
## Normal Main stays in the loop and receives an input event.
## Headless software GL is not a Windows Mobile pass.

var _main: Node
var _frames := 0
var _saw_mount := false


func _initialize() -> void:
	var udir := OS.get_user_data_dir()
	print("play user_dir=", udir)
	if OS.get_environment("PLAY_REQUIRE_ISOLATED") == "1" and udir.find("vc27_play_") < 0:
		print("FAIL user dir is not an isolated play profile")
		quit(2)
		return
	_main = load("res://scenes/Main.tscn").instantiate()
	root.add_child(_main)
	process_frame.connect(_on_frame)


func _on_frame() -> void:
	var pet: Node = _main.get("pet") if _main else null
	if pet == null:
		_frames += 1
		if _frames > 180:
			print("FAIL pet missing")
			quit(1)
		return
	var exterior: Node = _main.get("_hd2d_exterior")
	if exterior == null or exterior.get_node_or_null("cottage") == null:
		_frames += 1
		if _frames > 180:
			print("FAIL garden missing")
			quit(1)
		return
	if not _saw_mount:
		_saw_mount = true
		_frames = 0
		var vp: SubViewport = exterior.get("_compare_view")
		if vp == null or vp.size != Vector2i(1080, 2280):
			print("FAIL viewport ", vp.size if vp else "null")
			quit(1)
			return
		var cam: Camera3D = _main.get("cam")
		var pos := cam.global_position if cam else Vector3.INF
		if pos.distance_to(Vector3(12.0, 193.0, 207.8269)) > 1.0:
			print("FAIL camera ", pos)
			quit(1)
			return
		var method := RenderingServer.get_current_rendering_method()
		print("play renderer=", method)
		if OS.get_environment("PLAY_REQUIRE_MOBILE") == "1" and method != "mobile":
			print("FAIL renderer is not mobile")
			quit(1)
			return
		var before := int(_main.get("play_frames"))
		var ev := InputEventMouseButton.new()
		ev.button_index = MOUSE_BUTTON_LEFT
		ev.pressed = true
		ev.position = Vector2(120, 200)
		Input.parse_input_event(ev)
		_main.set_meta("play_before", before)
		return
	_frames += 1
	if _frames < 8:
		return
	var advanced := int(_main.get("play_frames")) - int(_main.get_meta("play_before"))
	var inputs := int(_main.get("play_inputs"))
	print("play frames_advanced=", advanced, " inputs=", inputs)
	if advanced < 5 or inputs < 1:
		print("FAIL main did not advance frames and input")
		quit(1)
		return
	var coat := (_main.get("pet") as Node).get_node_or_null("Hd2dCoat") as Node3D
	if coat == null or not coat.visible:
		print("FAIL coat hidden")
		quit(1)
		return
	print("PASS play responsive renderer=", RenderingServer.get_current_rendering_method())
	quit(0)
