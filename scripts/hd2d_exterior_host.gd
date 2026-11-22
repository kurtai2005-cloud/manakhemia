extends "res://hd2d_stage/scenes/capture.gd"
## Lifecycle binding for the generated exterior. This file is not a path remap.
## The path-only copies are listed in tools/hd2d_generated_provenance.txt.
##
## Calls the visual part of capture._ready:
##   _apply_measure_viewport, _resolve_mode, the shaft and grade env reads,
##   _clear_android_flag_secure, _build_scene, _configure_dof_quality,
##   _place_pet_shot.
## _build_scene still builds lights, environment, ground, meshes, the opening
## camera, art_depth, fx, and prop_bump.
##
## Does not call _add_m1_care, _setup_quality_toggle, _setup_fps_overlay,
## _smoke_walk_and_quit, _ready, _process, _tick_play, or _unhandled_input.
## art_depth keeps its own _process, which is the cloud, lag, and shadow update.
## prop_bump.tick is called from here so pet_pos_ws follows the root coat.

var root_main: Node3D
var root_walker: Node3D
var opening_transform := Transform3D.IDENTITY
var opening_fov := 50.0
var opening_near := 10.0
var opening_far := 4000.0
var opening_keep := Camera3D.KEEP_WIDTH
var opening_attrs: CameraAttributesPractical
var frame_index := 0
var _fixed := false
var _same_view := false
var _hidden: Array = []
var _env_backup: Environment
var _lock_prev := false
var _have_lock := false


func bind_root(main: Node3D, walker: Node3D) -> void:
	root_main = main
	root_walker = walker


func _ready() -> void:
	_apply_measure_viewport()
	_mode = _resolve_mode()
	var shafts := OS.get_environment("HD2D_SHAFTS").to_lower()
	if shafts in ["vol", "cards", "both"]:
		_shaft_style = shafts
	_capturing = false
	_dev_on = OS.get_environment("HD2D_DEV") == "1"
	_clear_android_flag_secure()
	if OS.get_environment("HD2D_GRADE").to_lower() in ["off", "0", "old"]:
		_grade_tweak = false
	_build_scene()
	_configure_dof_quality()
	_place_pet_shot()
	_keep_opening_camera()
	_bind_walker_visual()
	_ensure_cloud_tex()
	if OS.get_environment("HD2D_COMPARE_FIXED") == "1":
		begin_fixed_steps()


func _process(dt: float) -> void:
	if _fixed:
		return
	_tick_bump(dt)


func _unhandled_input(_event: InputEvent) -> void:
	pass


func begin_fixed_steps() -> void:
	_fixed = true
	var depth := get_node_or_null("ArtDepth")
	if depth:
		depth.set_process(false)
	var bump := get_node_or_null("PropBump")
	if bump:
		bump.set_process(false)


func step_visual(dt: float) -> void:
	# Fixed steps call the original cloud, lag, and shadow updates.
	# They do not call art_depth._process, whose _follow_camera reface does not
	# finish on this software-GL box. Engine-driven play still uses that _process.
	frame_index += 1
	if _same_view:
		_apply_opening_to_root_cam()
	_tick_bump(dt)
	var depth := get_node_or_null("ArtDepth")
	if depth:
		var night := str(_mode) == "night"
		depth.call("_dynamics", night, dt)
		depth.call("_low_fake_shadow", night)
	if _same_view:
		_apply_opening_to_root_cam()


func apply_same_view() -> void:
	_same_view = true
	_hold_walker(true)
	if root_main:
		_have_lock = true
		_lock_prev = bool(root_main.get("_interior_lock_cam"))
		root_main.set("_interior_lock_cam", true)
		var world: WorldEnvironment = root_main.get("env")
		if world:
			_env_backup = world.environment
			world.environment = null
		for light_name in ["sun", "fill"]:
			var light: Light3D = root_main.get(light_name)
			if light:
				_hidden.append({"node": light, "visible": light.visible})
				light.visible = false
		for child in root_main.get_children():
			if child == self or child == root_walker:
				continue
			if child is CanvasLayer or child is Camera3D:
				continue
			if child == root_main.get("sun") or child == root_main.get("fill") or child == root_main.get("env"):
				continue
			if child.name == "Hd2dPresentation":
				continue
			if child is Node3D:
				_hidden.append({"node": child, "visible": child.visible})
				child.visible = false
	_apply_opening_to_root_cam()


func restore_root_view() -> void:
	_same_view = false
	for item in _hidden:
		var node: Node = item["node"]
		if is_instance_valid(node):
			node.set("visible", bool(item["visible"]))
	_hidden.clear()
	if root_main:
		var world: WorldEnvironment = root_main.get("env")
		if world and _env_backup:
			world.environment = _env_backup
		if _have_lock:
			root_main.set("_interior_lock_cam", _lock_prev)
	_hold_walker(false)


func _keep_opening_camera() -> void:
	var pilot := _camera
	if pilot == null:
		return
	opening_transform = pilot.global_transform
	opening_fov = pilot.fov
	opening_near = pilot.near
	opening_far = pilot.far
	opening_keep = pilot.keep_aspect
	opening_attrs = pilot.attributes
	pilot.current = false
	var root_cam: Camera3D = root_main.get("cam") if root_main else null
	if root_cam:
		_camera = root_cam


func _bind_walker_visual() -> void:
	var pilot_pet := get_node_or_null("Tuanrong")
	if pilot_pet is Sprite3D:
		(pilot_pet as Sprite3D).visible = false
	var coat := root_walker.get_node_or_null("Hd2dCoat") if root_walker else null
	if coat is Sprite3D:
		_pet = coat


func _apply_opening_to_root_cam() -> void:
	if not root_main:
		return
	var root_cam: Camera3D = root_main.get("cam")
	if root_cam == null:
		return
	root_cam.global_transform = opening_transform
	root_cam.fov = opening_fov
	root_cam.near = opening_near
	root_cam.far = opening_far
	root_cam.keep_aspect = opening_keep
	if opening_attrs:
		root_cam.attributes = opening_attrs
	root_cam.current = true
	_camera = root_cam


func _ensure_cloud_tex() -> void:
	# project.godot declares the five 675 globals. This headless server does
	# not install them on its own, so register the same initial values here.
	# cloud_tex is the staged cloud image, not a blank texture.
	var tex: Texture2D = load("res://hd2d_stage/textures/tiles/cloud_shadow.png")
	_add_global("pet_pos_ws", RenderingServer.GLOBAL_VAR_TYPE_VEC3, Vector3.ZERO)
	_add_global("pet_lag_ws", RenderingServer.GLOBAL_VAR_TYPE_VEC3, Vector3(0, -1000, 0))
	_add_global("cloud_tex", RenderingServer.GLOBAL_VAR_TYPE_SAMPLER2D, tex)
	_add_global("cloud_off", RenderingServer.GLOBAL_VAR_TYPE_VEC2, Vector2.ZERO)
	_add_global("cloud_amt", RenderingServer.GLOBAL_VAR_TYPE_FLOAT, 0.22)


func _add_global(param: String, kind: int, value: Variant) -> void:
	var listed: PackedStringArray = RenderingServer.global_shader_parameter_get_list()
	if listed.has(param):
		if value != null:
			RenderingServer.global_shader_parameter_set(param, value)
		return
	RenderingServer.global_shader_parameter_add(param, kind, value)


func _tick_bump(dt: float) -> void:
	var bump := get_node_or_null("PropBump")
	if bump and bump.has_method("tick"):
		bump.tick(dt)


func _hold_walker(on: bool) -> void:
	if root_walker == null:
		return
	root_walker.set("pause_t", 30.0 if on else 0.0)
	var brain := root_walker.get_node_or_null("PetBrain")
	if brain and brain.get("tree"):
		brain.get("tree").set("enabled", not on)
