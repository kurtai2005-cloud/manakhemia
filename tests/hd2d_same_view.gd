extends SceneTree
## Root side of the same-view comparison.
## Software GL output is not Mobile acceptance.
## The pilot side is a separate process. See the printed command.

var _main: Node
var _frames := 0


func _initialize() -> void:
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
	var steps := 20
	var dt := 1.0 / 60.0
	for _i in steps:
		exterior.call("step_visual", dt)
	var img := _grab()
	var out_dir := OS.get_environment("HD2D_COMPARE_OUT")
	if out_dir == "":
		out_dir = OS.get_user_data_dir().path_join("hd2d_compare")
	DirAccess.make_dir_recursive_absolute(out_dir)
	var png_path := out_dir.path_join("root_presentation_low.png")
	var wrote := false
	if img:
		wrote = img.save_png(png_path) == OK
	var cam: Camera3D = _main.get("cam")
	var depth: Node = exterior.get_node_or_null("ArtDepth")
	var info := {
		"side": "root_presentation",
		"mobile_acceptance": false,
		"renderer": RenderingServer.get_current_rendering_method(),
		"driver": RenderingServer.get_current_rendering_driver_name(),
		"mode": str(exterior.get("_mode")),
		"viewport": [img.get_width(), img.get_height()] if img else [0, 0],
		"stepper_frames": int(exterior.get("frame_index")),
		"fixed_dt": dt,
		"opening_camera": _v3((exterior.get("opening_transform") as Transform3D).origin),
		"pet_global": _v3(pet.global_position),
		"camera_origin": _v3(cam.global_position) if cam else [],
		"camera_fov": cam.fov if cam else 0.0,
		"cloud_time": float(depth.get("_t")) if depth else 0.0,
		"cloud_image_loaded": depth != null and depth.get("_cloud_img") != null,
		"pet_lag": _v3(depth.get("_pet_lag")) if depth else [],
		"png": png_path if wrote else "",
		"png_written": wrote,
		"viewport_texture": img != null,
		"pilot_command": "HD2D_MODE=low HD2D_VP=1080x1920 HD2D_OUT=<empty-dir> godot --headless --path godot_hd2d_v6 --rendering-method gl_compatibility",
		"limitation": "This headless driver returned no viewport texture. Pilot HD2D_OUT saves at its frame 20 after one _tick_camera snap and engine dt. This root record uses the opening camera and 20 steps of dt=1/60 without art_depth._follow_camera. Pixel equality is a later GPU check. This is not Mobile acceptance.",
	}
	var json_path := out_dir.path_join("root_presentation_low.json")
	var f := FileAccess.open(json_path, FileAccess.WRITE)
	f.store_string(JSON.stringify(info, "\t"))
	f.close()
	print("same_view json=", json_path, " png_written=", wrote, " viewport_texture=", img != null, " renderer=", info["renderer"])
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

