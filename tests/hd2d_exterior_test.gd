extends SceneTree
## Exterior host checks. Isolated user dir. Software GL is not Mobile acceptance.

const Door := preload("res://scripts/hd2d_door.gd")

var _fail := 0
var _main: Node
var _frames := 0


func _initialize() -> void:
	var udir := OS.get_user_data_dir()
	print("exterior user_dir=", udir)
	if udir.find("vc27_root_adapter") < 0:
		print("FAIL user dir is not an isolated adapter profile")
		quit(2)
		return
	_provenance()
	_project_settings()
	_main = load("res://scenes/Main.tscn").instantiate()
	root.add_child(_main)
	process_frame.connect(_on_frame)


func _ok(cond: bool, name: String) -> void:
	if cond:
		print("PASS ", name)
	else:
		_fail += 1
		print("FAIL ", name)


func _on_frame() -> void:
	var pet: Node3D = _main.get("pet") if _main else null
	if pet == null:
		_frames += 1
		if _frames > 180:
			_ok(false, "Main did not spawn the pet")
			_finish()
		return
	_frames = 0
	process_frame.disconnect(_on_frame)
	_run(pet)


func _run(pet: Node3D) -> void:
	var method := RenderingServer.get_current_rendering_method()
	print("exterior renderer=", method, " mobile_acceptance=false")
	_ok(method != "mobile", "this run is not claimed as the Mobile renderer")
	var hud: Node = _main.get("hud")
	_ok(hud != null, "root HUD is present before the exterior")
	var cams_before := _current_cameras()
	_ok(cams_before == 1, "one current camera on H1")
	_main.call("enter_house", true)
	_ok(bool(_main.get("in_interior")), "H1 enter_house still runs")
	_main.call("exit_house", true)
	_ok(not bool(_main.get("in_interior")), "H1 exit_house still runs")
	var sim: Node = root.get_node("Sim")
	_ok(int(sim.get("state").get("version", -1)) == 1, "save version is 1 before the exterior")
	OS.set_environment("HD2D_COMPARE_FIXED", "1")
	OS.set_environment("HD2D_VP", "1080x2280")
	for param in ["pet_pos_ws", "pet_lag_ws", "cloud_tex", "cloud_off", "cloud_amt"]:
		_ok(ProjectSettings.has_setting("shader_globals/" + param), "project already declares " + param)
	var exterior: Node = _main.call("enable_hd2d_exterior")
	_ok(exterior != null, "exterior host loads")
	if exterior == null:
		_finish()
		return
	_ok(exterior.get_node_or_null("M1Care") == null, "pilot care node is absent")
	_ok(exterior.get("_roam") == null, "pilot roam is not constructed")
	_ok(_count_script("SaveSystem.gd") == 1, "one SaveSystem")
	_ok(_count_script("Sim.gd") == 1, "one Sim")
	_ok(_current_cameras() == 1, "root camera stays the only current camera")
	var pilot_pet := exterior.get_node_or_null("Tuanrong")
	_ok(pilot_pet is Sprite3D and not (pilot_pet as Sprite3D).visible, "generated pet sprite is hidden")
	var coat := pet.get_node_or_null("Hd2dCoat")
	_ok(coat is Sprite3D and exterior.get("_pet") == coat, "shadow pet is the root coat")
	_ok(coat is Sprite3D and is_equal_approx((coat as Sprite3D).offset.y, 2.0), "coat keeps offset 2")
	_ok(exterior.get_node_or_null("ArtDepth") != null, "art_depth is attached")
	var visual := exterior.get_viewport().get_visible_rect().size
	_ok(int(visual.x) == 1080 and int(visual.y) == 2280, "art_depth viewport is the 1080x2280 compare target")
	var ui := _main.get_viewport().get_visible_rect().size
	_ok(int(ui.x) == 390 and int(ui.y) == 844, "root UI viewport stays 390x844")
	var host_src := FileAccess.get_file_as_string("res://scripts/hd2d_exterior_host.gd")
	_ok(host_src.find("global_shader_parameter_get_list") < 0, "host does not call the editor-only global list")
	_ok(exterior.get_node_or_null("GroundInner") != null, "ground was built")
	_ok(exterior.get_node_or_null("cottage") != null, "cottage mesh was built")
	var names: PackedStringArray = RenderingServer.global_shader_parameter_get_list()
	_ok(names.has("cloud_tex") and names.has("cloud_off") and names.has("cloud_amt"), "cloud globals are registered")
	_ok(names.has("pet_pos_ws") and names.has("pet_lag_ws"), "pet globals are registered")
	var cloud_file: Texture2D = load("res://hd2d_stage/textures/tiles/cloud_shadow.png")
	_ok(cloud_file != null, "cloud_tex file loads as a texture")
	var depth: Node = exterior.get_node_or_null("ArtDepth")
	var before: float = float(depth.get("_t"))
	exterior.call("begin_fixed_steps")
	exterior.call("apply_same_view")
	exterior.call("step_visual", 1.0 / 60.0)
	_ok(float(depth.get("_t")) > before, "cloud time advanced with the original step")
	_ok(depth.get("_cloud_img") != null, "cloud image was read from the staged texture")
	var lag: Vector3 = depth.get("_pet_lag")
	_ok(lag.distance_to(Vector3(0, -1000, 0)) > 1.0, "pet lag moved from the 675 initial value")
	var shadow := exterior.get_node_or_null("PetShadow_v610")
	_ok(shadow != null, "low fake shadow node was created")
	var depth_src := FileAccess.get_file_as_string("res://hd2d_stage/scenes/art_depth.gd")
	_ok(depth_src.find("0.0 if night else CLOUD_AMT") >= 0, "night cloud amount is the original expression")
	exterior.set("_mode", "night")
	exterior.call("_apply_mode")
	exterior.call("step_visual", 1.0 / 60.0)
	_ok(str(exterior.get("_mode")) == "night", "night mode uses the existing apply path")
	exterior.set("_mode", "low")
	exterior.call("_apply_mode")
	exterior.call("restore_root_view")
	_ok(_current_cameras() == 1, "restored view keeps one current camera")
	_ok(hud != null and is_instance_valid(hud), "root HUD remains after the exterior")
	_main.call("disable_hd2d_exterior")
	_main.call("enter_house", true)
	_ok(bool(_main.get("in_interior")), "enter_house works after the exterior is removed")
	_main.call("exit_house", true)
	_ok(not bool(_main.get("in_interior")), "exit_house works after the exterior is removed")
	_ok(int(sim.get("state").get("version", -1)) == 1, "save version stays 1")
	_ok(is_equal_approx(Door.exterior_anchor().z, -29.5), "engineering candidate stays -29.5")
	_ok(not FileAccess.file_exists("res://hd2d_stage/room1/pack.json"), "interior pack is not consumed")
	_finish()


func _provenance() -> void:
	var text := FileAccess.get_file_as_string("res://tools/hd2d_generated_provenance.txt")
	var rows := 0
	for raw in text.split("\n"):
		if raw.begins_with("#") or raw.strip_edges() == "":
			continue
		var parts := raw.split(" ")
		_ok(parts.size() == 5, "provenance row has kind and both hashes")
		if parts.size() != 5:
			continue
		var frozen := FileAccess.get_file_as_string("res://" + parts[3])
		var generated := FileAccess.get_file_as_string("res://" + parts[4])
		_ok(generated.replace("res://hd2d_stage/", "res://") == frozen, "generated script is a res:// prefix of " + parts[3])
		rows += 1
	_ok(rows == 6, "six path-only scripts are recorded")
	var host := FileAccess.get_file_as_string("res://scripts/hd2d_exterior_host.gd")
	_ok(host.find("_add_m1_care(") < 0 or host.find("Does not call _add_m1_care") >= 0, "host does not invoke pilot care")
	_ok(host.find("func _process") >= 0 and host.find("_tick_play(") < 0, "host process does not tick the pilot walk")
	_ok(host.find("depth._process(dt)") >= 0, "full compare step includes art_depth._process")
	_ok(host.find("camera_overwritten_each_step") >= 0, "compare state records that the camera is not rewritten each step")


func _project_settings() -> void:
	var body := FileAccess.get_file_as_string("res://project.godot")
	_ok(body.find("rendering_method.mobile=\"mobile\"") >= 0, "root mobile renderer is mobile")
	_ok(body.find("rendering_method=\"gl_compatibility\"") >= 0, "desktop renderer stays gl_compatibility")
	_ok(body.find("pet_pos_ws=") >= 0 and body.find("pet_lag_ws=") >= 0, "pet shader globals are declared")
	_ok(body.find("cloud_tex=") >= 0 and body.find("cloud_shadow.png") >= 0, "cloud_tex points at the staged cloud texture")
	_ok(body.find("\"value\": 0.22") >= 0, "cloud_amt initial value is 0.22")
	_ok(FileAccess.file_exists("res://hd2d_stage/textures/tiles/cloud_shadow.png"), "cloud texture file was copied")
	_ok(FileAccess.file_exists("res://hd2d_stage/scenes/art_depth.gd"), "art_depth copy exists")
	_ok(not FileAccess.file_exists("res://hd2d_stage/gameplay/m1_care.gd"), "pilot care script is not staged")


func _current_cameras() -> int:
	_cam_n = 0
	_walk_cam(root, 0)
	return _cam_n


var _cam_n := 0


func _walk_cam(node: Node, _unused: int) -> void:
	if node is Camera3D and (node as Camera3D).current:
		_cam_n += 1
	for child in node.get_children():
		_walk_cam(child, 0)


func _count_script(suffix: String) -> int:
	_script_n = 0
	_script_suffix = suffix
	_walk_script(root)
	return _script_n


var _script_n := 0
var _script_suffix := ""


func _walk_script(node: Node) -> void:
	var scr: Script = node.get_script()
	if scr and str(scr.resource_path).ends_with(_script_suffix):
		_script_n += 1
	for child in node.get_children():
		_walk_script(child)


func _finish() -> void:
	if _fail == 0:
		print("PASS hd2d_exterior")
		quit(0)
	else:
		print("FAIL hd2d_exterior ", _fail)
		quit(1)
