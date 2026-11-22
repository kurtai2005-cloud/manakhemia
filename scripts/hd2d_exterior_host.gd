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
var follow_camera_steps := 0
var _fixed := false
var _same_view := false
var _hidden: Array = []
var _env_backup: Environment
var _lock_prev := false
var _have_lock := false
var _compare_view: SubViewport
var _cam_parent: Node


func bind_root(main: Node3D, walker: Node3D) -> void:
	root_main = main
	root_walker = walker


func _ready() -> void:
	# capture and art_depth read get_viewport() while they place the foreground
	# and screen-height fractions. That has to be the 1080x2280 compare
	# viewport. The root window stays the 390x844 UI host. Halo clustering
	# reads mesh pixels, not this viewport.
	_ensure_visual_viewport()
	_apply_measure_viewport()
	_restore_ui_window()
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
	# One matched step. The camera is not written again here.
	# HD2D_COMPARE_FULL=1 runs art_depth._process, including _follow_camera.
	# Without that flag, only the cloud, lag, and shadow calls run. That shorter
	# path is not a same-view frame.
	frame_index += 1
	_tick_bump(dt)
	var depth := get_node_or_null("ArtDepth")
	if depth == null:
		return
	if OS.get_environment("HD2D_COMPARE_FULL") == "1":
		depth._process(dt)
		follow_camera_steps += 1
		return
	var night := str(_mode) == "night"
	depth.call("_dynamics", night, dt)
	depth.call("_low_fake_shadow", night)


func comparison_state() -> Dictionary:
	var depth := get_node_or_null("ArtDepth")
	var cam: Camera3D = _camera
	var visual := _pet as Sprite3D
	var cloud_t := float(depth.get("_t")) if depth else 0.0
	var lag := Vector3.ZERO
	if depth and depth.get("_pet_lag") is Vector3:
		lag = depth.get("_pet_lag")
	var origin := Vector3.ZERO
	var fov := 0.0
	var keep := 0
	var basis := Basis.IDENTITY
	if cam:
		origin = cam.global_position
		fov = cam.fov
		keep = cam.keep_aspect
		basis = cam.global_transform.basis
	var vp := Vector2(_compare_view.size) if _compare_view else (get_viewport().get_visible_rect().size if get_viewport() else Vector2.ZERO)
	var visual_at := visual.global_position if visual else Vector3.ZERO
	var feet := root_walker.global_position if root_walker else Vector3.ZERO
	return {
		"protocol": "hd2d_same_view_v2",
		"side": "root_presentation",
		"viewport_requested": [1080, 2280],
		"viewport_actual": [int(vp.x), int(vp.y)],
		"aspect": "19:9",
		"mode": str(_mode),
		"steps": frame_index,
		"fixed_dt": 1.0 / 60.0,
		"follow_camera_steps": follow_camera_steps,
		"tick_camera_called": false,
		"tick_play_called": false,
		"care_present": get_node_or_null("M1Care") != null,
		"camera_set_once": true,
		"camera_overwritten_each_step": false,
		"camera_origin": [origin.x, origin.y, origin.z],
		"camera_basis": [basis.x.x, basis.x.y, basis.x.z, basis.y.x, basis.y.y, basis.y.z, basis.z.x, basis.z.y, basis.z.z],
		"camera_fov": fov,
		"camera_keep_aspect": keep,
		"feet_global": [feet.x, feet.y, feet.z],
		"visual_global": [visual_at.x, visual_at.y, visual_at.z],
		"visual_offset_y": visual.offset.y if visual else 0.0,
		"visual_pixel_size": visual.pixel_size if visual else 0.0,
		"cloud_t": cloud_t,
		"pet_lag": [lag.x, lag.y, lag.z],
		"renderer_actual": RenderingServer.get_current_rendering_method(),
		"mobile_acceptance": false,
		"render_target": "subviewport_1080x2280" if _compare_view else "window",
		"ui_viewport_unchanged": [390, 844],
		"pixel_compared": false,
	}


func _ensure_visual_viewport() -> void:
	if _compare_view or root_main == null:
		return
	_compare_view = SubViewport.new()
	_compare_view.name = "Hd2dCompareViewport"
	_compare_view.size = Vector2i(1080, 2280)
	_compare_view.own_world_3d = false
	_compare_view.handle_input_locally = false
	if OS.get_environment("HD2D_COMPARE_GRAB") == "1":
		_compare_view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	else:
		_compare_view.render_target_update_mode = SubViewport.UPDATE_DISABLED
	root_main.add_child(_compare_view)
	reparent(_compare_view)


func _restore_ui_window() -> void:
	# _apply_measure_viewport also asks the OS window for 1080x2280. Put the
	# root UI viewport back. The visual viewport is the SubViewport.
	var window := root_main.get_viewport() if root_main else null
	if window == null or window == get_viewport():
		return
	window.size = Vector2i(390, 844)
	DisplayServer.window_set_size(Vector2i(390, 844))


func _open_compare_viewport() -> void:
	# The root project window stays 390x844 for H1. The compare frame is a
	# 1080x2280 subviewport in the same world, using the opening camera once.
	_ensure_visual_viewport()
	if _compare_view == null:
		return
	var cam: Camera3D = root_main.get("cam")
	if cam == null or cam.get_parent() == _compare_view:
		if cam:
			_camera = cam
		return
	_cam_parent = cam.get_parent()
	cam.reparent(_compare_view)
	cam.global_transform = opening_transform
	cam.fov = opening_fov
	cam.near = opening_near
	cam.far = opening_far
	cam.keep_aspect = opening_keep
	if opening_attrs:
		cam.attributes = opening_attrs
	cam.current = true
	_camera = cam


func grab_compare_image() -> Image:
	if _compare_view == null:
		return null
	var tex := _compare_view.get_texture()
	if tex == null:
		return null
	return tex.get_image()


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
	_open_compare_viewport()


func restore_root_view() -> void:
	_same_view = false
	var built: Camera3D = null
	for child in get_children():
		if child is Camera3D and child != _camera:
			built = child
			break
	var cam: Camera3D = root_main.get("cam") if root_main else null
	if cam and _cam_parent and is_instance_valid(_cam_parent):
		cam.reparent(_cam_parent)
	_cam_parent = null
	# The host was parented into the compare viewport so art_depth measured
	# that viewport. Move it back before the viewport is freed.
	if _compare_view and get_parent() == _compare_view and root_main:
		reparent(root_main)
	if built:
		built.current = false
	if cam:
		cam.current = true
	if _compare_view and is_instance_valid(_compare_view):
		_compare_view.queue_free()
	_compare_view = null
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
	# project.godot declares the five 675 globals and the renderer creates
	# them from that declaration. cloud_tex is the staged cloud image.
	var tex: Texture2D = load("res://hd2d_stage/textures/tiles/cloud_shadow.png")
	_add_global("pet_pos_ws", RenderingServer.GLOBAL_VAR_TYPE_VEC3, Vector3.ZERO)
	_add_global("pet_lag_ws", RenderingServer.GLOBAL_VAR_TYPE_VEC3, Vector3(0, -1000, 0))
	_add_global("cloud_tex", RenderingServer.GLOBAL_VAR_TYPE_SAMPLER2D, tex)
	_add_global("cloud_off", RenderingServer.GLOBAL_VAR_TYPE_VEC2, Vector2.ZERO)
	_add_global("cloud_amt", RenderingServer.GLOBAL_VAR_TYPE_FLOAT, 0.22)


func _add_global(param: String, kind: int, value: Variant) -> void:
	# The editor-only global list errors on the RD renderer and comes back
	# empty. Adding after that then errors because the project declaration
	# already created the global.
	if ProjectSettings.has_setting("shader_globals/" + param):
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
