extends SceneTree
## Root side of the same-view comparison.
## Software GL output is not Mobile acceptance.
## The pilot side is a separate process. See the printed command.

var _main: Node
var _frames := 0


func _initialize() -> void:
	root.size = Vector2i(1080, 2280)
	var udir := OS.get_user_data_dir()
	print("same_view user_dir=", udir)
	if udir.find("vc27_root_adapter") < 0:
		print("FAIL user dir is not an isolated adapter profile")
		quit(2)
		return
	_main = load("res://scenes/Main.tscn").instantiate()
	root.add_child(_main)
	process_frame.connect(_on_frame)


func _on_frame() -> void:
	var pet: Node3D = _main.get("pet") if _main else null
	if pet == null:
		_frames += 1
		if _frames > 180:
			print("FAIL pet missing")
			quit(1)
		return
	process_frame.disconnect(_on_frame)
	_shoot(pet)


func _shoot(pet: Node3D) -> void:
	pet.global_position = Vector3.ZERO
	var exterior: Node = _main.call("enable_hd2d_exterior")
	if exterior == null:
		print("FAIL exterior missing")
		quit(1)
		return
	exterior.call("apply_same_view")
	var steps := int(OS.get_environment("HD2D_COMPARE_STEPS")) if OS.get_environment("HD2D_COMPARE_STEPS") != "" else 20
	var dt := 1.0 / 60.0
	for _i in steps:
		exterior.call("step_visual", dt)
	var info: Dictionary = exterior.call("comparison_state")
	info["driver"] = RenderingServer.get_current_rendering_driver_name()
	info["feet_note"] = "feet_global is the Walker origin. visual_global is the coat at local y=29, offset y=2. Compare visual_global to the pilot sprite, not the feet."
	var img: Image = null
	if OS.get_environment("HD2D_COMPARE_GRAB") == "1" and str(info.get("renderer_actual", "")) == "mobile":
		img = _grab()
	var out_dir := OS.get_environment("HD2D_COMPARE_OUT")
	if out_dir == "":
		out_dir = OS.get_user_data_dir().path_join("hd2d_compare")
	DirAccess.make_dir_recursive_absolute(out_dir)
	var png_path := out_dir.path_join("root_presentation_low.png")
	var wrote := false
	if img:
		wrote = img.save_png(png_path) == OK
	info["png"] = png_path if wrote else ""
	info["png_written"] = wrote
	info["viewport_texture"] = img != null
	info["headless"] = OS.has_feature("headless")
	info["pixel_compared"] = false
	info["mobile_acceptance"] = false
	var json_path := out_dir.path_join("root_presentation.json")
	var f := FileAccess.open(json_path, FileAccess.WRITE)
	f.store_string(JSON.stringify(info, "\t"))
	f.close()
	print("same_view json=", json_path, " png_written=", wrote, " follow=", info.get("follow_camera_steps", 0), " renderer=", info.get("renderer_actual", ""))
	exterior.call("restore_root_view")
	quit(0)


func _grab() -> Image:
	var vp := _main.get_viewport()
	if vp == null:
		return null
	var tex := vp.get_texture()
	if tex == null:
		return null
	return tex.get_image()


func _v3(v: Vector3) -> Array:
	return [v.x, v.y, v.z]

