extends SceneTree
## Root side of the same-view comparison.
## Software GL output is not Mobile acceptance.
## The pilot side is a separate process. See the printed command.

var _main: Node
var _frames := 0
var _info: Dictionary = {}
var _out_dir := ""
var _png_path := ""
var _exterior: Node


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
	var out_dir := OS.get_environment("HD2D_COMPARE_OUT")
	if out_dir == "":
		out_dir = OS.get_user_data_dir().path_join("hd2d_compare")
	DirAccess.make_dir_recursive_absolute(out_dir)
	var grab := OS.get_environment("HD2D_COMPARE_GRAB") == "1"
	_info = info
	_out_dir = out_dir
	_png_path = out_dir.path_join("root_presentation.png")
	_exterior = exterior
	if grab and not _display_blocked():
		process_frame.connect(_capture_png)
		return
	_write(false, null)
	if grab:
		print("FAIL root viewport PNG missing or not 1080x2280")
		quit(1)
		return
	quit(0)


func _capture_png() -> void:
	process_frame.disconnect(_capture_png)
	var img: Image = _exterior.call("grab_compare_image")
	var wrote := _png_ok(img, _png_path)
	_write(wrote, img)
	if not wrote:
		print("FAIL root viewport PNG missing or not 1080x2280")
		quit(1)
		return
	quit(0)


func _write(wrote: bool, img: Image) -> void:
	_info["png"] = _png_path if wrote else ""
	_info["png_written"] = wrote
	_info["viewport_texture"] = img != null
	_info["display_blocked"] = _display_blocked()
	_info["headless"] = OS.has_feature("headless") or DisplayServer.get_name() == "headless"
	_info["pixel_compared"] = false
	_info["mobile_acceptance"] = false
	var json_path := _out_dir.path_join("root_presentation.json")
	var f := FileAccess.open(json_path, FileAccess.WRITE)
	f.store_string(JSON.stringify(_info, "\t"))
	f.close()
	print("same_view json=", json_path, " png_written=", wrote, " follow=", _info.get("follow_camera_steps", 0), " renderer=", _info.get("renderer_actual", ""))
	if _exterior:
		_exterior.call("restore_root_view")


func _display_blocked() -> bool:
	if OS.get_environment("HD2D_COMPARE_DISPLAY") != "1":
		return true
	if OS.has_feature("headless") or DisplayServer.get_name() == "headless":
		return true
	return false


func _png_ok(img: Image, path: String) -> bool:
	if img == null:
		return false
	if img.get_width() != 1080 or img.get_height() != 2280:
		return false
	if img.is_empty():
		return false
	if img.save_png(path) != OK:
		return false
	if not FileAccess.file_exists(path) or FileAccess.get_size(path) < 32:
		return false
	var back := Image.new()
	if back.load(path) != OK:
		return false
	return back.get_width() == 1080 and back.get_height() == 2280


