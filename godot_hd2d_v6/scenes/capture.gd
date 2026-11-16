extends Node3D

const M1CameraPolicy := preload("res://gameplay/m1_camera_policy.gd")
const M1UiLayout := preload("res://gameplay/m1_ui_layout.gd")
## 微光小圃 HD-2D test v6.18 (0.6.18-pilot vc27: vc25 pace + night sky×albedo via art_depth). Modes: HD2D_MODE=high|low|night (default: low).
## Phone renderer is Mobile only. High DOF focus follows 團絨; light near blur on High.
## Screenshots: HD2D_CAPTURE=1 and/or HD2D_OUT=<dir>; HD2D_PET_SHOT=near|mid|far. 開發者模式 has in-app 截圖 + FPS log.
## Interactive: 畫質 High/Low; 色調 tweak (sat 0.88 + warm highlights); tap ground to walk. Camera: damped XZ only.
## Camera stays target y 58 / dist 270 / hfov 50 (團絨 ≈ 10%). Yaw not user-rotated (遊美 verified ±30, sky seamless to ±45).
## Low day: sun shadows OFF so art_depth._low_fake_shadow can show baked props + pet silhouette. Bake pass keeps sun ON.

var OUT_DIR: String = OS.get_environment("HD2D_OUT") if OS.get_environment("HD2D_OUT") != "" else "/workspace/game-design/detail_pilot/godot_hd2d_v6"

# Tighten framing so the cottage reads. Follow dist must keep the 54 wu pet
# at ≥20% of screen height (fov 40° → dist ≤ ~370).
const V2_TARGET := Vector3(36, 40, -40)
const V2_DIST := 315.0
const V2_PITCH_DEG := 30.0
const V2_FOV_DEG := 40.0
const PET_VISIBLE_H := 54.0
const PORTRAIT_TARGET := Vector3(12, 58, -26)
const PORTRAIT_DIST := 270.0
const PORTRAIT_HFOV := 50.0

var _camera: Camera3D
var _sun: DirectionalLight3D
var _fill: DirectionalLight3D
var _env: Environment
var _attrs: CameraAttributesPractical
var _omnis: Array[OmniLight3D] = []
var _emissive_mats: Array[StandardMaterial3D] = []
var _backdrop_mats: Array[StandardMaterial3D] = []
var _mode := "high"
var _frame := 0
var _saved := false
var _capturing := false
var _quality_btn: Button
var _fps_label: Label
var _fps_accum := 0.0
var _fps_frames := 0
var _pet: Sprite3D
var _walk_target: Variant = null  # Vector3 or null
var _roam = null
var _pet_origin_xz := Vector3.ZERO
var _cam_base_pos := Vector3.ZERO
var _cam_follow_pos := Vector3.ZERO
var _cam_look := Vector3.ZERO
var _opening_pet_frac := 0.0
var _follow_zoom_scale := 1.0
var _flag_secure_was_set := false
const PET_CENTER_Y := 29.0
const WALK_SPEED := 48.0
const CAM_FOLLOW_DAMPING := 2.0
# Walk bounds (v6.7): shrink the back-left corner so the follow camera
# does not sit inside the big tree (trunk/crown ≈ (-88, -44)).
const WALK_X_MIN := -140.0
const WALK_X_MAX := 150.0
const WALK_Z_MIN := -110.0
const WALK_Z_MAX := 90.0
const WALK_BACK_Z := -70.0
const WALK_BACK_LEFT_X_MIN := -110.0
const CAM_TREE_BAND_Z := 120.0
const CAM_FOLLOW_X_MIN := -100.0
# v6.8 Mobile DOF (High only): far follow + light near. One amount drives both.
# Near plane is ~140 wu (not d_pet-40≈225) so the bottom blade lawn does not mush;
# amount 0.03 keeps the residual near blur light. 團絨 at ~265 stays sharp.
const DOF_FAR_PAD := 90.0
const DOF_NEAR_PAD := 40.0
const DOF_NEAR_DIST := 140.0
const DOF_NEAR_MIN := 10.0
const DOF_FAR_TRANS := 260.0
const DOF_NEAR_TRANS := 40.0
const DOF_AMOUNT_MOBILE := 0.03
const DOF_DAMPING := 3.0
const SUN_DIR_V67 := Vector3(0.645, -0.616, 0.453)  # light travel; elev 38°, matches bake
const GRADE_SAT_DEFAULT := 0.86
const GRADE_CON_DEFAULT := 1.18
const GRADE_SAT_TWEAK := 0.88
const GRADE_CON_TWEAK := 1.24
# v6.9 hybrid shadows (GAPS): Low keeps the bake as the base; live shadows only
# for 團絨, swaying leaves (fg plants) and props. Do not change sun elevation
# (38°, matches the v6.9 bake).
const SHADOW_BLUR_HIGH := 2.2
const SHADOW_BLUR_LOW := 2.0
const SHADOW_BLUR_BASE := 0.2
const SHADOW_ANGULAR_HIGH := 0.9
const SHADOW_ANGULAR_LOW := 0.6
const SHADOW_ANGULAR_BASE := 0.5
const SHADOW_OPACITY_HIGH := 0.55
const SHADOW_OPACITY_LOW := 0.55
const SHADOW_OPACITY_BASE := 0.92
const SHADOW_ATLAS_LOW := 1024
const SHADOW_MAX_DIST_LOW := 300.0
const SHADOW_MAX_DIST_HIGH := 450.0
const GRADE_LEAK_TWEAK := 0.14
const GRADE_LEAK_BASE := 0.08
const GRADE_GLOW_INT_TWEAK := 0.58
const GRADE_GLOW_INT_BASE := 0.50
const GRADE_GLOW_HDR_TWEAK := 0.92
const GRADE_GLOW_HDR_BASE := 1.0
var _dof_d_pet := 0.0
var _dof_inited := false
var _grade_tweak := true
var _grade_btn: Button
var _grade_lut: Texture
var _grade_fx_mat: ShaderMaterial
var _ground_mat: ShaderMaterial
var _ground_tex_high: Texture2D
var _ground_tex_low: Texture2D
var _bake_shadow_ground := false
var _tree_shadow_nodes: Array[Node] = []
var _day_glow_mats: Array[StandardMaterial3D] = []
var _fx_nodes: Array[Node] = []   # High-only effects (dust, shafts, grade)
var _dust: CPUParticles3D
var _dust_mat: ShaderMaterial
var _rim_mats: Array[ShaderMaterial] = []
var _tuft_mats: Array[ShaderMaterial] = []
var _pool: SpotLight3D
var _shaft_style := "both"  # cards + thin volumetric (Forward+); best match in r2
var _shadow_cast_saved: Dictionary = {}
var _shadow_cast_inited := false
var _shadow_policy_ready := false
var _bed_flower_mats: Array[ShaderMaterial] = []
var _dev_on := false
var _dev_entry: Button
var _dev_btn: Button
var _shot_btn: Button
var _dev_log: Label
var _fps_min := 9999.0
var _fps_max := 0.0
var _fps_sum := 0.0
var _fps_n := 0
var _fps_log_left := 0.0
var _dev_ff: FontFile


func _apply_measure_viewport() -> void:
	# Headless defaults to 64×64, which would skip the portrait camera path.
	# Force 1080×1920 (or HD2D_VP=WxH) so framing / walk-clamp smoke match the APK.
	var vp_s := OS.get_environment("HD2D_VP")
	var force := OS.has_feature("headless") or OS.get_environment("HD2D_SMOKE") == "1" or vp_s != ""
	if not force:
		return
	var want := Vector2i(1080, 1920)
	if vp_s != "":
		var parts := vp_s.split("x")
		if parts.size() == 2:
			want = Vector2i(int(parts[0]), int(parts[1]))
	DisplayServer.window_set_size(want)
	get_viewport().size = want
	print("hd2d viewport forced=", get_viewport().get_visible_rect().size, " want=", want)


func _ready() -> void:
	_apply_measure_viewport()
	_mode = _resolve_mode()
	var ss := OS.get_environment("HD2D_SHAFTS").to_lower()
	if ss in ["vol", "cards", "both"]:
		_shaft_style = ss
	_capturing = OS.get_environment("HD2D_CAPTURE") == "1" or OS.get_environment("HD2D_OUT") != ""
	var driver := RenderingServer.get_current_rendering_driver_name()
	var method := RenderingServer.get_current_rendering_method()
	print("hd2d v6.18-pilot vc27 start  mode=", _mode, " capture=", _capturing, " driver=", driver, " method=", method, " out=", OUT_DIR)
	_dev_on = OS.get_environment("HD2D_DEV") == "1"
	_clear_android_flag_secure()
	if OS.get_environment("HD2D_GRADE").to_lower() in ["off", "0", "old"]:
		_grade_tweak = false
	_build_scene()
	_configure_dof_quality()
	_place_pet_shot()
	if not _capturing:
		_add_m1_care()
		_setup_quality_toggle()
		_setup_fps_overlay()
	if OS.get_environment("HD2D_SMOKE") == "1":
		# Headless smoke: take a few steps then quit (no GPU capture).
		call_deferred("_smoke_walk_and_quit")


func _process(_dt: float) -> void:
	if not _capturing:
		_tick_play(_dt)
		return
	_frame += 1
	# Shadows + DOF + SSAO need a few frames, more on a real GPU first run.
	if not _saved and _frame >= 20:
		_tick_camera(1.0)  # snap follow
		_tick_dof(0.0, true)
		RenderingServer.force_draw()
		_save_shot()
		_saved = true
		get_tree().quit(0)
	elif _frame >= 120:
		push_error("timeout before save, frame=%s" % _frame)
		get_tree().quit(1)


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_Q:
			_set_high(_mode == "low")
			get_viewport().set_input_as_handled()
		elif event.keycode == KEY_N:
			_mode = "high" if _mode == "night" else "night"
			_apply_mode()
			_refresh_quality_btn()
			get_viewport().set_input_as_handled()
		elif event.keycode == KEY_G:
			_toggle_grade()
			get_viewport().set_input_as_handled()
		return
	if _capturing:
		return
	if event is InputEventScreenTouch or event is InputEventScreenDrag or event is InputEventMouseButton or event is InputEventMouseMotion:
		var care := get_node_or_null("M1Care")
		if care and care.has_method("handle_event"):
			care.call("handle_event", event)
			get_viewport().set_input_as_handled()
			return
		if event is InputEventScreenTouch and event.pressed:
			_try_walk_tap((event as InputEventScreenTouch).position)
			get_viewport().set_input_as_handled()
		elif event is InputEventMouseButton and event.pressed and (event as InputEventMouseButton).button_index == MOUSE_BUTTON_LEFT:
			_try_walk_tap((event as InputEventMouseButton).position)
			get_viewport().set_input_as_handled()


func _resolve_mode() -> String:
	var env_m := OS.get_environment("HD2D_MODE").to_lower()
	if env_m in ["high", "low", "night"]:
		return env_m
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--mode="):
			var m := a.substr(7).to_lower()
			if m in ["high", "low", "night"]:
				return m
	return "low"


func _build_scene() -> void:
	var cam_j: Dictionary = _load_json("res://art/camera.json")
	var light_j: Dictionary = _load_json("res://art/lights.json")
	var obj_j: Dictionary = _load_json("res://art/objects.json")
	_setup_environment(light_j)
	_setup_lights(light_j)
	_setup_camera(cam_j)
	_setup_ground()
	_setup_backdrops(obj_j)
	_setup_meshes(obj_j)
	_setup_pet()
	_setup_tile_props()
	_setup_dense_fill()
	_setup_far_forest()
	_setup_canopies()
	_setup_dapple()
	_setup_tufts()
	_add_art_depth()  # v6.4/v6.5 art-only pass (scenes/art_depth.gd)
	_setup_fx()
	_setup_pool()
	_setup_rims(self)
	_apply_mode()
	_print_pet_framing()
	_add_prop_bump()
	_apply_bed_flower_shader()
	_shadow_policy_ready = true
	_shadow_cast_inited = false
	_shadow_cast_saved.clear()
	_apply_shadow_policy(_mode != "low")


func _load_json(path: String) -> Dictionary:
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		push_error("missing json " + path)
		return {}
	var data = JSON.parse_string(f.get_as_text())
	if typeof(data) != TYPE_DICTIONARY:
		push_error("bad json " + path)
		return {}
	return data


func _hex(c: String) -> Color:
	return Color(c)


func _renderer() -> String:
	return RenderingServer.get_current_rendering_method()


func _is_forward() -> bool:
	# CameraAttributes DOF works on Forward+ and Mobile; not on gl_compatibility.
	return _renderer() != "gl_compatibility"


func _is_forward_plus() -> bool:
	return _renderer() == "forward_plus"


func _setup_environment(_light_j: Dictionary) -> void:
	_env = Environment.new()
	_env.background_mode = Environment.BG_SKY
	var sky := Sky.new()
	var proc := ProceduralSkyMaterial.new()
	if _mode == "night":
		proc.sky_top_color = Color(0.10, 0.12, 0.22)
		proc.sky_horizon_color = Color(0.16, 0.16, 0.28)
		proc.ground_bottom_color = Color(0.06, 0.07, 0.10)
		proc.ground_horizon_color = Color(0.10, 0.11, 0.16)
		proc.sun_angle_max = 4.0
	else:
		proc.sky_top_color = Color(0.42, 0.64, 0.88)
		proc.sky_horizon_color = Color(0.78, 0.86, 0.92)
		proc.ground_bottom_color = Color(0.55, 0.62, 0.48)
		proc.ground_horizon_color = Color(0.70, 0.78, 0.82)
		proc.sun_angle_max = 12.0
	sky.sky_material = proc
	_env.sky = sky
	# HD2D_TONE=filmic uses SimpleHD2D's Filmic tonemap (numbers only, cited in HD2D_RECIPE.md).
	if OS.get_environment("HD2D_TONE") != "linear":
		_env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
		_env.tonemap_exposure = 1.35
		_env.tonemap_white = 6.0
	else:
		_env.tonemap_mode = Environment.TONE_MAPPER_LINEAR
		_env.tonemap_exposure = 1.18
	if OS.get_environment("HD2D_EXP") != "":
		_env.tonemap_exposure = float(OS.get_environment("HD2D_EXP"))
	_env.adjustment_enabled = true
	_env.adjustment_contrast = 1.18
	_env.adjustment_saturation = 0.86
	# SSAO off by default (v6.2 phone budget: even High keeps it off).
	_env.ssao_enabled = false
	_env.ssao_radius = 22.0
	_env.ssao_intensity = 2.4
	_env.ssao_power = 1.6
	_env.ssao_detail = 0.6
	_env.ssao_horizon = 0.06
	_env.ssao_sharpness = 0.98
	_env.ssao_light_affect = 0.15
	_env.ssil_enabled = false
	_env.sdfgi_enabled = false
	# Glow only on highlights (roof rims, night lamps).
	_env.glow_enabled = true
	_env.glow_intensity = 0.5
	_env.glow_strength = 1.0
	_env.glow_bloom = 0.05
	_env.glow_hdr_threshold = 1.0
	_env.glow_blend_mode = Environment.GLOW_BLEND_MODE_ADDITIVE
	# Depth-only, light, warm fog. NO volumetric (v1 Vulkan went grey).
	_env.fog_enabled = true
	_env.fog_mode = Environment.FOG_MODE_DEPTH
	_env.fog_light_color = Color(0.95, 0.82, 0.62)
	_env.fog_light_energy = 0.40
	_env.fog_density = 0.0
	_env.fog_aerial_perspective = 0.0
	_env.fog_sky_affect = 0.0
	_env.fog_depth_begin = 700.0
	_env.fog_depth_end = 1400.0
	_env.fog_depth_curve = 1.6
	_env.fog_sun_scatter = 0.6
	# Volumetric fog only for HD2D_SHAFTS=vol|both. Warm, thin, no ambient
	# inject (v1 Vulkan washed grey because of neutral fog + ambient inject).
	_env.volumetric_fog_enabled = false
	_env.volumetric_fog_density = float(OS.get_environment("HD2D_VOLD")) if OS.get_environment("HD2D_VOLD") != "" else 0.00003
	_env.volumetric_fog_albedo = Color(1.0, 0.93, 0.80)
	_env.volumetric_fog_emission = Color(0, 0, 0)
	_env.volumetric_fog_anisotropy = 0.75
	_env.volumetric_fog_length = 700.0
	_env.volumetric_fog_detail_spread = 2.0
	_env.volumetric_fog_ambient_inject = 0.0
	_env.volumetric_fog_sky_affect = 0.0
	_env.volumetric_fog_gi_inject = 0.0
	_env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	var sun_j: Dictionary = _light_j.get("sun", {})
	var amb: Dictionary = sun_j.get("ambient", {})
	# Warm-green bounce so shadow sides read (target: golden hour, not grey).
	_env.ambient_light_color = Color(0.52, 0.58, 0.68)
	_env.ambient_light_energy = 0.26
	_env.reflected_light_source = Environment.REFLECTION_SOURCE_DISABLED
	var world := WorldEnvironment.new()
	world.environment = _env
	add_child(world)


func _setup_lights(light_j: Dictionary) -> void:
	var sun_j: Dictionary = light_j.get("sun", {})
	var dir: Array = sun_j.get("dir", [0.4206, -0.721, 0.5507])
	var sun_dir := Vector3(dir[0], dir[1], dir[2]).normalized()
	# v3 golden hour: low warm sun from back-left (target concept).
	sun_dir = SUN_DIR_V67.normalized()  # v6.7: 38° elevation, same azimuth as the new ground bake
	_sun = DirectionalLight3D.new()
	_sun.name = "Sun"
	_sun.light_color = Color(1.0, 0.84, 0.68)
	_sun.light_energy = 2.6
	_sun.light_volumetric_fog_energy = 6.0
	_sun.shadow_enabled = true
	_sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	_sun.directional_shadow_max_distance = 560.0
	_sun.shadow_bias = 0.4
	_sun.shadow_normal_bias = 1.0
	_sun.shadow_blur = 0.2
	if "shadow_opacity" in _sun:
		_sun.set("shadow_opacity", 0.92)
	_sun.basis = Basis.looking_at(sun_dir, Vector3.UP)
	add_child(_sun)
	var travel := -_sun.global_transform.basis.z.normalized()
	var elev := rad_to_deg(asin(clampf(-travel.y, -1.0, 1.0)))
	print("hd2d sun travel=", travel, " elev=", snapped(elev, 0.1), " expected=", SUN_DIR_V67.normalized())

	var fill_j: Dictionary = light_j.get("fill", {})
	var fdir: Array = fill_j.get("dir", [0.2005, -0.1203, -0.9723])
	_fill = DirectionalLight3D.new()
	_fill.name = "Fill"
	_fill.light_color = _hex(str(fill_j.get("color", "#ffe2c4")))
	_fill.light_energy = 0.22
	_fill.light_color = Color(1.0, 0.86, 0.68)
	_fill.shadow_enabled = false
	_fill.basis = Basis.looking_at(Vector3(fdir[0], fdir[1], fdir[2]).normalized(), Vector3.UP)
	add_child(_fill)

	for L in light_j.get("lights", []):
		var omni := OmniLight3D.new()
		omni.name = str(L.get("id", "omni"))
		omni.position = Vector3(float(L["x"]), float(L["y"]), float(L["z"]))
		omni.light_color = _hex(str(L.get("color", "#ffd890")))
		omni.light_energy = 0.0
		omni.omni_range = float(L.get("radius", 40))
		omni.omni_attenuation = 1.2
		omni.shadow_enabled = false
		omni.light_volumetric_fog_energy = 1.5
		omni.set_meta("day_energy", 0.35 if str(L.get("id", "")).begins_with("lantern") else 0.0)
		omni.set_meta("night_energy", float(L.get("intensityNight", 0.7)))
		add_child(omni)
		_omnis.append(omni)


func _setup_camera(cam_j: Dictionary) -> void:
	var target := V2_TARGET
	var pitch := deg_to_rad(float(cam_j.get("pitchDeg", V2_PITCH_DEG)))
	var dist := V2_DIST
	if _is_portrait():
		target = PORTRAIT_TARGET
		dist = PORTRAIT_DIST
	var offset := Vector3(0.0, dist * sin(pitch), dist * cos(pitch))

	_attrs = CameraAttributesPractical.new()
	_attrs.exposure_multiplier = 1.0
	_attrs.auto_exposure_enabled = false
	# v6.7: starting distances only; High follow sets far/near from d_pet every frame.
	var can_dof := _is_forward()
	_attrs.dof_blur_near_enabled = false
	_attrs.dof_blur_near_distance = 225.0
	_attrs.dof_blur_near_transition = DOF_NEAR_TRANS
	_attrs.dof_blur_far_enabled = can_dof
	_attrs.dof_blur_far_distance = 425.0
	_attrs.dof_blur_far_transition = DOF_FAR_TRANS
	_attrs.dof_blur_amount = 0.0

	_camera = Camera3D.new()
	_camera.name = "Camera"
	_camera.fov = float(cam_j.get("fovDeg", V2_FOV_DEG))
	if _is_portrait():
		# v6 portrait: same layout, keep the horizontal span (lamp → cottage) and let
		# the extra height show lawn below and canopy / golden backlight above.
		_camera.keep_aspect = Camera3D.KEEP_WIDTH
		_camera.fov = PORTRAIT_HFOV
	_camera.near = float(cam_j.get("near", 10))
	_camera.far = float(cam_j.get("far", 4000))
	_camera.attributes = _attrs
	_camera.position = target + offset
	add_child(_camera)
	_camera.look_at(target)
	_camera.current = true
	_cam_base_pos = _camera.position
	_cam_follow_pos = _camera.position
	_cam_look = target
	print("camera pos=", _camera.position, " target=", target, " dist=", dist)


func _tex(path: String) -> Texture2D:
	var t := load(path) as Texture2D
	if t == null:
		push_warning("missing texture " + path)
	return t


func _setup_ground() -> void:
	var inner := MeshInstance3D.new()
	inner.name = "GroundInner"
	var plane := PlaneMesh.new()
	plane.size = Vector2(256, 256)
	inner.mesh = plane
	inner.position = Vector3(0, 0, 0)
	inner.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	var gm := _tiling_mat(_tex("res://textures/ground_composed.png"), Vector2(1, 1), false)
	if gm is ShaderMaterial:
		(gm as ShaderMaterial).set_shader_parameter("lawn_gain", _envf("HD2D_LAWN", 1.0))  # v6.12: 0.6 → 1.0 on the clearing (lower mid lift); v6.1: was 0.85
		# v6.12 mid-ground balance: the warm sunlit-lawn lift sits on the clearing (lower mid), not the bottom
		(gm as ShaderMaterial).set_shader_parameter("lawn_center", Vector3(10.0, 0.0, _envf("HD2D_LAWNZ", 5.0)))
		(gm as ShaderMaterial).set_shader_parameter("lawn_radius", Vector2(_envf("HD2D_LAWNRX", 170.0), _envf("HD2D_LAWNRZ", 110.0)))
		var pe := OS.get_environment("HD2D_POOL").split(",")   # v6.14 light pooling: edge multiplier
		(gm as ShaderMaterial).set_shader_parameter("pool_edge", Vector3(float(pe[0]), float(pe[1]), float(pe[2])) if pe.size() == 3 else Vector3(0.72, 0.74, 0.84))   # v6.15: warmer, lighter edge (concept bottom 68/61/29 is warm, not dark green)
		var pc := OS.get_environment("HD2D_POOLC").split(",")
		(gm as ShaderMaterial).set_shader_parameter("pool_core", Vector3(float(pc[0]), float(pc[1]), float(pc[2])) if pc.size() == 3 else Vector3(1.60, 1.34, 0.86))
		(gm as ShaderMaterial).set_shader_parameter("pool_r", Vector2(0.40, 1.05))
		(gm as ShaderMaterial).set_shader_parameter("pool_off", Vector2(18.0, -18.0))   # v6.15 toward 團絨 / cottage
		_ground_mat = gm as ShaderMaterial
		_ground_tex_high = _ground_mat.get_shader_parameter("albedo_tex")
		if ResourceLoader.exists("res://textures/ground_composed_low.png"):
			_ground_tex_low = load("res://textures/ground_composed_low.png")
			_bake_shadow_ground = _ground_tex_low != null
			print("hd2d baked ground shadows available")
	inner.material_override = gm
	add_child(inner)

	# 128 px macro = 128 wu at 1 px = 1 wu.
	var outer := MeshInstance3D.new()
	outer.name = "GroundOuter"
	var oplane := PlaneMesh.new()
	oplane.size = Vector2(1280, 800)
	outer.mesh = oplane
	outer.position = Vector3(0, -0.05, -80)
	outer.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	outer.material_override = _tiling_mat(_tex("res://textures/grass_outer_512.png"), Vector2(1280.0 / 512.0, 800.0 / 512.0), false)  # v6.4: 4-source lawn, repeats every 512 wu
	add_child(outer)

	# Infinite XZ plane so taps can raycast the lawn (does not change the meshes).
	var body := StaticBody3D.new()
	body.name = "GroundBody"
	var col := CollisionShape3D.new()
	col.shape = WorldBoundaryShape3D.new()
	body.add_child(col)
	add_child(body)


func _tiling_mat(tex: Texture2D, uv_scale: Vector2, flip_v: bool) -> Material:
	var sh := load("res://shaders/texel_lit.gdshader") as Shader
	if sh:
		var sm := ShaderMaterial.new()
		sm.shader = sh
		sm.set_shader_parameter("albedo_tex", tex)
		sm.set_shader_parameter("uv_scale", uv_scale)
		sm.set_shader_parameter("roughness_val", 1.0)
		sm.set_shader_parameter("alpha_cut", 0.0)
		sm.set_shader_parameter("flip_v", flip_v)
		# v5: matching *_n.png normal map → real-time relief.
		if tex and tex.resource_path != "":
			var np := tex.resource_path.get_basename() + "_n.png"
			if ResourceLoader.exists(np):
				sm.set_shader_parameter("normal_tex", load(np))
				sm.set_shader_parameter("use_normal", true)
				sm.set_shader_parameter("normal_depth", _envf("HD2D_NDEPTH", 1.0))
		return sm
	var m := StandardMaterial3D.new()
	m.albedo_texture = tex
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	m.uv1_scale = Vector3(uv_scale.x, uv_scale.y, 1)
	m.roughness = 1.0
	m.metallic = 0.0
	m.shading_mode = BaseMaterial3D.SHADING_MODE_PER_PIXEL
	m.specular_mode = BaseMaterial3D.SPECULAR_DISABLED
	m.texture_repeat = true
	return m


func _box_mat(tex: Texture2D, uv_scale: Vector2) -> Material:
	return _tiling_mat(tex, uv_scale, false)


func _setup_backdrops(obj_j: Dictionary) -> void:
	for o in obj_j.get("objects", []):
		if str(o.get("type", "")) != "backdrop":
			continue
		if str(o.get("id", "")) == "bg_hills":
			continue  # v4: replaced by layered 3D forest + depth fog
		if str(o.get("id", "")) == "bg_sky":
			# v6.8: SkyDome_v68 replaced this flat board (its edge was the mid-sky seam).
			print("skip bg_sky (replaced by SkyDome_v68)")
			continue
		var w := float(o.get("w", 100))
		var h := float(o.get("h", 40))
		var mi := MeshInstance3D.new()
		mi.name = str(o.get("id", "bg"))
		var q := QuadMesh.new()
		q.size = Vector2(w, h)
		mi.mesh = q
		mi.position = Vector3(float(o.get("x", 0)), h * 0.5, float(o.get("z", 0)))
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		var mat := StandardMaterial3D.new()
		var f := str(o.get("file", ""))
		mat.albedo_texture = _tex("res://art/" + f)
		mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
		mat.alpha_scissor_threshold = 0.5
		mat.texture_repeat = false
		mat.cull_mode = BaseMaterial3D.CULL_DISABLED
		mi.material_override = mat
		_backdrop_mats.append(mat)
		add_child(mi)
		print("backdrop ", mi.name, " at ", mi.position, " size=", q.size)


func _setup_meshes(obj_j: Dictionary) -> void:
	for o in obj_j.get("objects", []):
		if str(o.get("type", "")) != "mesh":
			continue
		var id := str(o.get("id", ""))
		if id.begins_with("bush_"):
			_spawn_bush(float(o.get("x", 0)), float(o.get("z", 0)), 1.2, id.hash())
			continue
		# v6.8: voxel `tree` ArrayMesh is trunk+dome crown. Art already has _trunks + spray
		# canopies at the same 4 sites. Skip in play (keep only for HD2D_BAKE_SHADOW).
		if id == "tree" and OS.get_environment("HD2D_BAKE_SHADOW") != "1":
			print("skip voxel tree mesh at (", o.get("x", 0), ",", o.get("z", 0), ") (art trunks + spray canopy)")
			continue
		var glb := str(o.get("glb", "meshes/%s.glb" % id))
		var packed := load("res://art/" + glb) as PackedScene
		if packed == null:
			push_warning("missing glb " + glb)
			continue
		var inst := packed.instantiate() as Node3D
		inst.name = id
		var y := float(o["y"]) if o.has("y") else 0.0
		inst.position = Vector3(float(o.get("x", 0)), y, float(o.get("z", 0)))
		if o.get("yawDeg", 0):
			inst.rotation_degrees = Vector3(0, float(o.get("yawDeg", 0)), 0)
		var shadow: bool = bool(o.get("castShadow", true))
		_tag_shadow(inst, shadow)
		var emis_path := "res://art/meshes/%s_emissive.png" % id
		var emis: Texture2D = load(emis_path) if ResourceLoader.exists(emis_path) else null
		var before := _emissive_mats.size()
		_apply_atlas_materials(inst, emis)
		if id == "lanterns" or id == "lamp":
			for k in range(before, _emissive_mats.size()):
				_emissive_mats[k].set_meta("day_mul", 3.2 if id == "lanterns" else 1.4)
				if id == "lamp":
					# v5: amber lamp head (was white): multiply mask by amber.
					_emissive_mats[k].emission_operator = BaseMaterial3D.EMISSION_OP_MULTIPLY
					_emissive_mats[k].emission = Color(1.0, 0.56, 0.18)
				_day_glow_mats.append(_emissive_mats[k])
		if id == "cottage":
			var rebaked := _tex("res://textures/cottage_rebaked_3x.png")
			if rebaked:
				_set_albedo(inst, rebaked)
				_set_normal(inst, _tex("res://textures/cottage_rebaked_3x_n.png"))
				print("cottage using rebaked tile atlas + normal")
		if id == "tree":
			_retexture(inst, _tex("res://textures/tree_bark_atlas.png"))  # v6.3: trunk strip repainted with AI bark
		if id.begins_with("tree"):
			_tree_shadow_nodes.append(inst)
		# fence keeps its official alpha-cut picket atlas (triplanar plank test lost the pickets)
		add_child(inst)
		print("mesh ", id, " at ", inst.position)


func _set_albedo(node: Node, tex: Texture2D) -> void:
	if node is MeshInstance3D:
		var mi := node as MeshInstance3D
		var mesh := mi.mesh
		var nsurf := mesh.get_surface_count() if mesh else 0
		for i in nsurf:
			var mat: Material = mi.get_surface_override_material(i)
			if mat is StandardMaterial3D:
				(mat as StandardMaterial3D).albedo_texture = tex
	for c in node.get_children():
		_set_albedo(c, tex)


func _tag_shadow(node: Node, on: bool) -> void:
	if node is GeometryInstance3D:
		(node as GeometryInstance3D).cast_shadow = (
			GeometryInstance3D.SHADOW_CASTING_SETTING_ON if on
			else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		)
	for c in node.get_children():
		_tag_shadow(c, on)


func _apply_atlas_materials(node: Node, emis: Texture2D) -> void:
	if node is MeshInstance3D:
		var mi := node as MeshInstance3D
		var mesh := mi.mesh
		var nsurf := mesh.get_surface_count() if mesh else 0
		for i in nsurf:
			var src: Material = mi.get_active_material(i)
			var sm: StandardMaterial3D
			if src is StandardMaterial3D:
				sm = (src as StandardMaterial3D).duplicate()
			else:
				sm = StandardMaterial3D.new()
				if src is BaseMaterial3D and (src as BaseMaterial3D).albedo_texture:
					sm.albedo_texture = (src as BaseMaterial3D).albedo_texture
			sm.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
			sm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
			sm.alpha_scissor_threshold = 0.5
			sm.shading_mode = BaseMaterial3D.SHADING_MODE_PER_VERTEX
			sm.roughness = 1.0
			sm.specular_mode = BaseMaterial3D.SPECULAR_DISABLED
			sm.metallic = 0.0
			sm.texture_repeat = false
			if emis:
				sm.emission_enabled = true
				sm.emission_texture = emis
				sm.emission_energy_multiplier = 0.0
				_emissive_mats.append(sm)
			mi.set_surface_override_material(i, sm)
	for c in node.get_children():
		_apply_atlas_materials(c, emis)


func _setup_pet() -> void:
	var spr := Sprite3D.new()
	spr.name = "Tuanrong"
	spr.texture = _tex("res://art/pet/pet_tuanrong_radiant_idle_01.png")
	spr.pixel_size = 1.0
	spr.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
	spr.alpha_cut = SpriteBase3D.ALPHA_CUT_OPAQUE_PREPASS
	spr.alpha_scissor_threshold = 0.5
	spr.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	spr.shaded = true
	spr.double_sided = true
	spr.centered = true
	spr.position = Vector3(0, PET_CENTER_Y, 0)
	spr.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	add_child(spr)
	_pet = spr
	_pet_origin_xz = Vector3(spr.position.x, 0.0, spr.position.z)
	print("pet at ", spr.position)


func _setup_tile_props() -> void:
	_add_box("CrateWood", Vector3(22, 8, 18), Vector3(16, 16, 16),
		"res://textures/tiles/wood_a.png", Vector2(1, 1))
	_add_box("CrateTimberLid", Vector3(22, 16.6, 18), Vector3(16, 1.2, 16),
		"res://textures/tiles/timber_a.png", Vector2(1, 1))
	_add_box("BrickWallA", Vector3(50, 6, -48), Vector3(16, 12, 8),
		"res://textures/tiles/brick_a.png", Vector2(16.0 / 32.0, 12.0 / 32.0))  # v6.3: 32 px brick tile, 1 texel = 1 wu
	_add_box("BrickWallB", Vector3(58, 6, -48), Vector3(16, 12, 8),
		"res://textures/tiles/brick_b.png", Vector2(16.0 / 32.0, 12.0 / 32.0))
	_add_box("PorchFloor", Vector3(86, 1.2, -49), Vector3(28, 2.4, 14),
		"res://textures/tiles/floor_a.png", Vector2(28.0 / 16.0, 14.0 / 16.0))
	_add_box("TimberPost", Vector3(42, 12, -46), Vector3(6, 24, 6),
		"res://textures/tiles/timber_b.png", Vector2(0.4, 1.5))
	_add_box("CrateWood2", Vector3(-24, 8, 28), Vector3(16, 16, 16),
		"res://textures/tiles/wood_b.png", Vector2(1, 1))
	_add_box("BrickPlanter", Vector3(30, 5, -20), Vector3(20, 10, 10),
		"res://textures/tiles/brick_c.png", Vector2(20.0 / 32.0, 10.0 / 32.0))
	# Foreground blur-ready props (bottom of the tightened frame).


func _add_box(id: String, pos: Vector3, size: Vector3, tex_path: String, uv: Vector2) -> void:
	var mi := MeshInstance3D.new()
	mi.name = id
	var box := BoxMesh.new()
	box.size = size
	mi.mesh = box
	mi.position = pos
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	mi.material_override = _box_mat(_tex(tex_path), uv)
	add_child(mi)


func _spawn_copy(id: String, x: float, z: float, shadow: bool = true, scale: float = 1.0, yaw: float = 0.0, y: float = 0.0) -> void:
	if id.begins_with("bush_"):
		_spawn_bush(x, z, scale, int(x * 7.0 + z * 13.0))
		return
	if id == "tree" and OS.get_environment("HD2D_BAKE_SHADOW") != "1":
		print("skip voxel tree mesh at (", x, ",", z, ") (art trunks + spray canopy)")
		return
	var packed := load("res://art/meshes/%s.glb" % id) as PackedScene
	if packed == null:
		push_warning("missing extra mesh " + id)
		return
	var inst := packed.instantiate() as Node3D
	inst.position = Vector3(x, y, z)
	inst.scale = Vector3(scale, scale, scale)
	if yaw != 0.0:
		inst.rotation_degrees = Vector3(0, yaw, 0)
	# v6.9: stable names so prop_bump can match spawn copies (pot_S_100_-30, can_48_48, …).
	inst.name = "%s_%d_%d" % [id, int(x), int(z)]
	_tag_shadow(inst, shadow)
	_apply_atlas_materials(inst, null)
	if id == "tree":
		_retexture(inst, _tex("res://textures/tree_bark_atlas.png"))  # v6.3: trunk strip repainted with AI bark
	if id.begins_with("tree"):
		_tree_shadow_nodes.append(inst)
	add_child(inst)


func _setup_dense_fill() -> void:
	# Same H1 kit, more of it, so the field is not an empty lawn.
	# Foreground (high +Z) is for tilt-shift near blur.
	_spawn_copy("bush_bL", -70, 125, true, 1.05)
	_spawn_copy("bush_bL2", 95, 118, true, 1.1, -15)
	# Mid sides
	_spawn_copy("bush_bL", -125, 30, true, 1.15, 8)
	_spawn_copy("bush_bR", -130, -20, true, 1.0, 180)
	_spawn_copy("bush_bL2", -118, 70, true, 0.9)
	_spawn_copy("tree", -145, 10, true, 0.78, 12)
	_spawn_copy("bush_bR", 155, 25, true, 1.1, -30)
	_spawn_copy("bush_bL", 148, -25, true, 1.0)
	_spawn_copy("tree", 165, -70, true, 0.82, -8)
	_spawn_copy("pot_S", 128, 8, true, 1.0)
	_spawn_copy("pot_L", 135, 50, true, 0.9)
	# Around the cottage
	_spawn_copy("bush_bL2", 48, -100, true, 1.0)
	_spawn_copy("bush_bR", 125, -95, true, 1.05, 25)
	_spawn_copy("bush_bL", 118, -55, true, 0.9)
	_spawn_copy("tree", 175, -130, true, 0.88)
	_spawn_copy("bed", 55, -20, true, 1.0, -10)
	_spawn_copy("pot_S", 100, -30, true, 1.0)
	# Far mid belt (between the garden and the hill card)
	_spawn_copy("bush_bL", -90, -145, false, 1.2)
	_spawn_copy("bush_bR", -20, -155, false, 1.1, 12)
	_spawn_copy("bush_bL2", 50, -148, false, 1.15)
	_spawn_copy("bush_bR", 130, -160, false, 1.2, -20)
	# No full-size trees immediately behind the cottage — keep a garden clearing.
	_spawn_copy("trees_bL", -200, -210, false, 1.0)
	_spawn_copy("trees_bR", 200, -220, false, 1.0)
	# Extra mid garden props
	_spawn_copy("mushrooms", -15, 35, true, 0.85, 40)
	_spawn_copy("jar", 18, 8, true, 1.0)
	_spawn_copy("can", 48, 48, true, 0.9, 25)
	print("dense fill instanced")


func _apply_mode() -> void:
	var high := _mode != "low"
	var night := _mode == "night"
	var forward := _is_forward()
	_apply_phone_budget(high)
	_apply_shadow_policy(high)
	_env.glow_enabled = high
	_env.fog_enabled = high
	# SSAO + volumetric fog stay off even on High (Note10+ lag). Never enable
	# volumetric fog on Mobile — unsupported, must not error.
	_env.ssao_enabled = false
	_env.volumetric_fog_enabled = false
	for n in _fx_nodes:
		if n is Node3D and n.name == "DappleCaster":
			continue  # visibility owned by _apply_shadow_policy (must stay hidden unless SHADOWS_ONLY)
		if n is Node3D:
			# No sun shafts at night (bug seen in v3 NIGHT render).
			(n as Node3D).visible = high and not (night and n.name == "Shafts")
		elif n is CanvasLayer:
			(n as CanvasLayer).visible = high
	# v6.7 High DOF: light far + light near (one amount). Low stays crisp.
	# Near is gentle so 團絨 stays sharp; focus still tracks d_pet every frame.
	var use_dof := high and forward
	_attrs.dof_blur_near_enabled = use_dof
	_attrs.dof_blur_far_enabled = use_dof
	_attrs.dof_blur_amount = (DOF_AMOUNT_MOBILE if use_dof else 0.0)
	_attrs.dof_blur_far_transition = DOF_FAR_TRANS
	_attrs.dof_blur_near_transition = DOF_NEAR_TRANS
	_dof_inited = false
	if use_dof:
		_tick_dof(0.0, true)
	_apply_grade()

	var light_j: Dictionary = _load_json("res://art/lights.json")
	var night_j: Dictionary = light_j.get("night", {})
	if night:
		_sun.light_energy = float(night_j.get("sun", 0.12))
		_sun.light_color = Color(0.55, 0.62, 0.85)
		_fill.light_energy = 0.0
		_env.ambient_light_color = _hex(str(night_j.get("ambient", "#4a5a90")))
		_env.ambient_light_energy = float(night_j.get("ambientIntensity", 0.35))
		_env.fog_light_color = Color(0.55, 0.52, 0.70)
		_env.fog_light_energy = 0.22
		_env.glow_hdr_threshold = 0.45
		_env.glow_intensity = 0.7
		for omni in _omnis:
			omni.light_energy = float(omni.get_meta("night_energy", 0.7))
		for sm in _emissive_mats:
			sm.emission_energy_multiplier = 1.6
		for sm in _day_glow_mats:
			sm.emission_energy_multiplier = 4.0
		if _dust_mat:
			_dust_mat.set_shader_parameter("tint", Color(0.80, 1.0, 0.55, 1.0))
	else:
		for omni in _omnis:
			omni.light_energy = float(omni.get_meta("day_energy", 0.0)) if high else 0.0
		for sm in _emissive_mats:
			sm.emission_energy_multiplier = 0.0
		for sm in _day_glow_mats:
			sm.emission_energy_multiplier = float(sm.get_meta("day_mul", 3.2)) if high else 0.6

	var rim_on := high and not night
	for rm in _rim_mats:
		rm.set_shader_parameter("amt", float(rm.get_meta("amt", 0.45)) if rim_on else 0.0)
	for tm in _tuft_mats:
		tm.set_shader_parameter("rim_top", _envf("HD2D_TIP", 0.25) if rim_on else 0.0)
	if _pool:
		_pool.visible = not night
		_pool.shadow_enabled = false  # r1: shadowed pool was blocked by canopies → no effect
		_pool.light_energy = _envf("HD2D_POOL", 0.5)
	var bg := Color(0.18, 0.20, 0.35, 1.0) if night else Color(1.0, 0.84, 0.54, 1.0)
	for mat in _backdrop_mats:
		mat.albedo_color = bg


func _set_high(high: bool) -> void:
	if _mode == "night":
		_mode = "night" if high else "low"
	else:
		_mode = "high" if high else "low"
	_apply_mode()
	_refresh_quality_btn()
	print("quality -> ", _mode)


func _setup_quality_toggle() -> void:
	var layer := CanvasLayer.new()
	layer.layer = 20
	add_child(layer)
	var font_path := "res://art/ui/GenWanMin2TC-R.subset.otf"
	var ff: FontFile = null
	if ResourceLoader.exists(font_path):
		ff = FontFile.new()
		ff.load_dynamic_font(font_path)
	_quality_btn = Button.new()
	_quality_btn.position = Vector2(24, 24)
	_quality_btn.custom_minimum_size = Vector2(220, 64)
	if ff:
		_quality_btn.add_theme_font_override("font", ff)
		_quality_btn.add_theme_font_size_override("font_size", 28)
	_quality_btn.pressed.connect(_on_quality_pressed)
	layer.add_child(_quality_btn)
	_refresh_quality_btn()
	_grade_btn = Button.new()
	_grade_btn.position = Vector2(24, 100)
	_grade_btn.custom_minimum_size = Vector2(220, 56)
	if ff:
		_grade_btn.add_theme_font_override("font", ff)
		_grade_btn.add_theme_font_size_override("font_size", 24)
	_grade_btn.pressed.connect(_toggle_grade)
	layer.add_child(_grade_btn)
	_refresh_grade_btn()
	_dev_ff = ff
	_dev_btn = Button.new()
	_dev_btn.position = Vector2(24, 176)
	_dev_btn.custom_minimum_size = Vector2(220, 56)
	if ff:
		_dev_btn.add_theme_font_override("font", ff)
		_dev_btn.add_theme_font_size_override("font_size", 24)
	_dev_btn.pressed.connect(_toggle_dev)
	layer.add_child(_dev_btn)
	_shot_btn = Button.new()
	_shot_btn.position = Vector2(24, 244)
	_shot_btn.custom_minimum_size = Vector2(220, 56)
	_shot_btn.text = "截圖"
	if ff:
		_shot_btn.add_theme_font_override("font", ff)
		_shot_btn.add_theme_font_size_override("font_size", 24)
	_shot_btn.pressed.connect(_dev_screenshot)
	layer.add_child(_shot_btn)
	_dev_log = Label.new()
	_dev_log.position = Vector2(24, 312)
	_dev_log.size = Vector2(700, 220)
	_dev_log.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_dev_log.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_dev_log.add_theme_font_size_override("font_size", 16)
	_dev_log.add_theme_color_override("font_color", Color(1, 1, 1, 0.9))
	_dev_log.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.75))
	_dev_log.add_theme_constant_override("outline_size", 4)
	if ff:
		_dev_log.add_theme_font_override("font", ff)
	layer.add_child(_dev_log)
	_dev_entry = Button.new()
	_dev_entry.name = "DevEntry"
	_dev_entry.text = "開發"
	_dev_entry.focus_mode = Control.FOCUS_NONE
	_dev_entry.anchor_left = 0.0
	_dev_entry.anchor_right = 0.0
	_dev_entry.anchor_top = 1.0
	_dev_entry.anchor_bottom = 1.0
	_dev_entry.offset_left = 12.0
	_dev_entry.offset_right = 76.0
	_dev_entry.offset_top = -44.0
	_dev_entry.offset_bottom = -12.0
	if ff:
		_dev_entry.add_theme_font_override("font", ff)
		_dev_entry.add_theme_font_size_override("font_size", 16)
	_dev_entry.pressed.connect(_toggle_dev)
	layer.add_child(_dev_entry)
	_quality_btn.name = "QualityBtn"
	_grade_btn.name = "GradeBtn"
	_dev_btn.name = "DevToggle"
	_refresh_dev_ui()


func _on_quality_pressed() -> void:
	_set_high(_mode == "low")


func _refresh_quality_btn() -> void:
	if _quality_btn == null:
		return
	var label := "畫質：高"
	if _mode == "low":
		label = "畫質：低"
	elif _mode == "night":
		label = "畫質：夜"
	_quality_btn.text = label


func _solve_follow_scale(opening_frac: float, need: float) -> float:
	# Find the distance scale that reaches m1a follow_pet_min_frac.
	# The camera is moved only for the measurement and then put back.
	if need <= 0.001 or opening_frac + 0.002 >= need:
		return 1.0
	var pet := _pet.global_position
	var far := _camera.global_position
	var saved := far
	var lo := 0.35
	var hi := M1CameraPolicy.zoom_scale(opening_frac, need)
	for _i in 8:
		var mid := (lo + hi) * 0.5
		_camera.global_position = M1CameraPolicy.zoomed_along(far, pet, mid)
		var got := _pet_height_frac()
		if got < need:
			hi = mid
		else:
			lo = mid
	_camera.global_position = saved
	return hi


func _pet_height_frac() -> float:
	if _camera == null or _pet == null:
		return 0.0
	var vp := get_viewport().get_visible_rect().size
	var mid := _pet.global_position
	var top: Vector2 = _camera.unproject_position(mid + Vector3(0, PET_VISIBLE_H * 0.5, 0))
	var bot: Vector2 = _camera.unproject_position(mid + Vector3(0, -PET_VISIBLE_H * 0.5, 0))
	return absf(bot.y - top.y) / maxf(vp.y, 1.0)


func _follow_pet_min() -> float:
	if GameData == null:
		return 0.0
	var cam: Dictionary = (GameData.m1a as Dictionary).get("camera", {})
	return float(cam.get("follow_pet_min_frac", 0.0))


func _overview_pet_min() -> float:
	if GameData == null:
		return 0.0
	var cam: Dictionary = (GameData.m1a as Dictionary).get("camera", {})
	return float(cam.get("overview_pet_min_frac", 0.0))


func _print_pet_framing() -> void:
	if _camera == null or _pet == null:
		return
	var vp := get_viewport().get_visible_rect().size
	var mid := _pet.global_position
	var top: Vector2 = _camera.unproject_position(mid + Vector3(0, PET_VISIBLE_H * 0.5, 0))
	var bot: Vector2 = _camera.unproject_position(mid + Vector3(0, -PET_VISIBLE_H * 0.5, 0))
	var frac := absf(bot.y - top.y) / maxf(vp.y, 1.0)
	_opening_pet_frac = frac
	var follow_min := _follow_pet_min()
	var overview_min := _overview_pet_min()
	print("pet screen height fraction=", snapped(frac, 0.001),
		" context=opening_panorama",
		" vp=", vp,
		" dist=", snapped(_camera.global_position.distance_to(mid), 0.1),
		" hfov=", _camera.fov,
		" keep=", _camera.keep_aspect,
		" target_y=", PORTRAIT_TARGET.y,
		" portrait_dist=", PORTRAIT_DIST,
		" box_wu=", PET_VISIBLE_H,
		" m1a_overview_min=", overview_min,
		" m1a_follow_min=", follow_min,
		" opening_camera_moved=false")
	_follow_zoom_scale = _solve_follow_scale(frac, follow_min)
	print("follow zoom scale=", snapped(_follow_zoom_scale, 0.001), " opening_camera_restored=true")
	var cot_top: Vector2 = _camera.unproject_position(Vector3(82.5, 142, -72))
	var cot_bot: Vector2 = _camera.unproject_position(Vector3(82.5, 0, -72))
	var cfrac := absf(cot_bot.y - cot_top.y) / maxf(vp.y, 1.0)
	print("cottage screen height fraction=", snapped(cfrac, 0.001))


func _save_shot() -> void:
	var vp := get_viewport()
	var img: Image = vp.get_texture().get_image()
	if img == null:
		push_error("viewport image is null")
		return
	if _looks_flipped(img):
		img.flip_y()
		print("viewport looked flipped; applied flip_y")
	var name := "GODOT_%s.png" % _mode.to_upper()
	DirAccess.make_dir_recursive_absolute(OUT_DIR)
	var path := OUT_DIR.path_join(name)
	var err := img.save_png(path)
	print("wrote ", path, " ", img.get_width(), "x", img.get_height(), " err=", err)
	var vp_h := float(img.get_height())
	var top: Vector2 = _camera.unproject_position(Vector3(0, PET_VISIBLE_H, 0))
	var bot: Vector2 = _camera.unproject_position(Vector3(0, 0, 0))
	print("pet screen height fraction at save=", snapped(absf(bot.y - top.y) / vp_h, 0.001))
	if _mode == "high":
		_save_crop(img)
	if OS.get_environment("HD2D_PRESET") != "":
		var pd := OS.get_environment("HD2D_PRESET")
		DirAccess.make_dir_recursive_absolute(pd)
		var e1 := ResourceSaver.save(_env.duplicate(), pd.path_join("hd2d_env_%s.tres" % _mode))
		var e2 := ResourceSaver.save(_attrs.duplicate(), pd.path_join("hd2d_camera_attrs_%s.tres" % _mode))
		print("preset saved ", pd, " ", e1, " ", e2)


func _looks_flipped(img: Image) -> bool:
	var w := img.get_width()
	var h := img.get_height()
	var top := _region_luma(img, 0, 0, w, int(h * 0.12))
	var bot := _region_luma(img, 0, int(h * 0.88), w, h)
	print("luma top=", top, " bot=", bot)
	return bot > top + 0.08


func _region_luma(img: Image, x0: int, y0: int, x1: int, y1: int) -> float:
	var acc := 0.0
	var n := 0
	var stepx := maxi(1, (x1 - x0) / 32)
	var stepy := maxi(1, (y1 - y0) / 8)
	for y in range(y0, y1, stepy):
		for x in range(x0, x1, stepx):
			var c := img.get_pixel(x, y)
			acc += c.r * 0.3 + c.g * 0.59 + c.b * 0.11
			n += 1
	return acc / float(maxi(n, 1))


func _save_crop(img: Image) -> void:
	var world := Vector3(72, 40, -56)
	var sp: Vector2 = _camera.unproject_position(world)
	var cw := 480
	var ch := 360
	var x := clampi(int(sp.x) - cw / 2, 0, img.get_width() - cw)
	var y := clampi(int(sp.y) - ch / 2, 0, img.get_height() - ch)
	var crop := img.get_region(Rect2i(x, y, cw, ch))
	crop.resize(cw * 2, ch * 2, Image.INTERPOLATE_NEAREST)
	var path := OUT_DIR.path_join("GODOT_COTTAGE_CROP.png")
	crop.save_png(path)
	print("wrote ", path, " from screen ", sp, " region ", x, ",", y)



func _glow_mat(tint: Color, energy: float, alpha: float, mask: int, bb: bool) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = load("res://shaders/glow_add.gdshader")
	m.set_shader_parameter("tint", tint)
	m.set_shader_parameter("energy", energy)
	m.set_shader_parameter("alpha", alpha)
	m.set_shader_parameter("mask_mode", mask)
	m.set_shader_parameter("billboard", bb)
	return m


func _spawn_bush(x: float, z: float, scale: float, key: int) -> void:
	# Organic bush: 4–5 squashed low-poly spheres with the hand leaf tile.
	var root := Node3D.new()
	root.name = "Bush_%d_%d" % [int(x), int(z)]
	root.position = Vector3(x, 0, z)
	add_child(root)
	var k := absi(key)
	var lobes := [
		Vector4(0, 0, 0, 1.0), Vector4(-0.75, 0, 0.25, 0.78),
		Vector4(0.7, 0, -0.2, 0.82), Vector4(0.15, 0.55, -0.1, 0.7),
		Vector4(-0.3, 0, -0.6, 0.66),
	]
	var n := 4 + (k % 2)
	var base_r := 13.0 * scale
	for i in n:
		var L: Vector4 = lobes[i]
		var r := base_r * L.w * (0.92 + 0.08 * float((k >> i) % 3))
		var mi := MeshInstance3D.new()
		var sp := SphereMesh.new()
		sp.radius = r
		sp.height = r * 2.0
		sp.radial_segments = 14
		sp.rings = 7
		mi.mesh = sp
		mi.position = Vector3(L.x * base_r, r * 0.72 + L.y * base_r * 0.6, L.z * base_r)
		mi.scale = Vector3(1.0, 0.82, 1.0)
		mi.rotation_degrees = Vector3(0, float((k * (i + 3)) % 360), 0)
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
		var tex := _tex("res://textures/tiles/leaf_a.png" if (i + k) % 2 == 0 else "res://textures/tiles/leaf_b.png")
		var circ := TAU * r
		mi.material_override = _tiling_mat(tex, _leaf_uv(tex, circ), false)
		root.add_child(mi)


func _setup_fx() -> void:
	var sun_dir := -_sun.global_transform.basis.z.normalized()
	# --- light-shaft cards (god rays) from back-left, through the tree line ---
	if _shaft_style in ["cards", "both"]:
		var shafts := Node3D.new()
		shafts.name = "Shafts"
		add_child(shafts)
		_fx_nodes.append(shafts)
		var to_cam := (_camera.global_position - Vector3(0, 40, -60)).normalized()
		var yax := -sun_dir
		var xax := yax.cross(to_cam).normalized()
		var zax := xax.cross(yax).normalized()
		var bas := Basis(xax, yax, zax)
		var spots := [
			Vector4(-150, 40, -130, 30), Vector4(-112, 30, -100, 18),
			Vector4(-80, 26, -150, 40), Vector4(-40, 30, -120, 16),
			Vector4(-20, 34, -170, 26), Vector4(-130, 20, -40, 14),
			Vector4(10, 30, -150, 12), Vector4(-60, 20, -60, 20),
			Vector4(-170, 30, -60, 24), Vector4(30, 40, -200, 30),
			Vector4(-100, 60, -220, 36), Vector4(60, 30, -240, 20),
		]
		for i in spots.size():
			var s: Vector4 = spots[i]
			var q := QuadMesh.new()
			q.size = Vector2(s.w, 420.0)
			var mi := MeshInstance3D.new()
			mi.mesh = q
			mi.basis = bas
			# centre the card so its lower end lands near (x, y, z)
			mi.position = Vector3(s.x, s.y, s.z) + yax * 170.0
			# v6.8: keep Shafts behind the garden so they never cross the left trees when panning.
			if mi.position.z > -270.0:
				mi.position.z = -270.0 - fposmod(s.x * 0.37, 1.0) * 70.0
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			mi.material_override = _glow_mat(Color(1.0, 0.92, 0.72), 1.0, 0.14 + 0.04 * float(i % 3), 1, false)
			shafts.add_child(mi)
	# --- floating dust motes (bloom + DOF bokeh near camera) ---
	_dust = CPUParticles3D.new()
	_dust.name = "Dust"
	_dust.amount = 110 if OS.has_feature("mobile") else 170
	_dust.lifetime = 10.0
	_dust.preprocess = 10.0
	_dust.explosiveness = 0.0
	_dust.randomness = 1.0
	if "use_fixed_seed" in _dust:
		_dust.set("use_fixed_seed", true)
		_dust.set("seed", 1977)
	_dust.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	_dust.emission_box_extents = Vector3(200, 70, 150)
	_dust.position = Vector3(10, 75, -50)
	_dust.direction = Vector3(0.3, 1, 0)
	_dust.spread = 180.0
	_dust.gravity = Vector3(0, 0.4, 0)
	_dust.initial_velocity_min = 0.5
	_dust.initial_velocity_max = 2.5
	_dust.scale_amount_min = 0.6
	_dust.scale_amount_max = 1.6
	var q2 := QuadMesh.new()
	q2.size = Vector2(1.2, 1.2)
	_dust.mesh = q2
	_dust_mat = _glow_mat(Color(1.0, 0.84, 0.52), 2.4, 1.0, 0, true)
	_dust.material_override = _dust_mat
	_dust.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_dust)
	_fx_nodes.append(_dust)
	# --- screen grade: warm vignette + top-left leak ---
	var layer := CanvasLayer.new()
	layer.layer = 10
	add_child(layer)
	var rect := ColorRect.new()
	rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var gm := ShaderMaterial.new()
	gm.shader = load("res://shaders/grade.gdshader")
	rect.material = gm
	_grade_fx_mat = gm
	layer.add_child(rect)
	_fx_nodes.append(layer)
	print("fx: shafts=", _shaft_style, " dust=", _dust.amount)



# ---------------- v4 additions ----------------
func _leaf_cluster(parent: Node3D, center: Vector3, r: float, lobes: int, key: int, shadow: bool, haze_amt: float = 0.0) -> void:
	# Clustered pixel-leaf spheres (canopy / far trees). Deterministic layout.
	for i in lobes:
		var a := float(i) * 2.39996 + float(key % 7)
		var rr := r * (0.55 + 0.25 * fposmod(float(i) * 0.618034 + float(key) * 0.1, 1.0))
		var off := Vector3(cos(a) * r * 0.62, (float(i % 3) - 0.8) * r * 0.32, sin(a) * r * 0.45)
		if i == 0:
			off = Vector3.ZERO
			rr = r * 0.8
		var mi := MeshInstance3D.new()
		var sp := SphereMesh.new()
		sp.radius = rr
		sp.height = rr * 1.8
		sp.radial_segments = 12
		sp.rings = 6
		mi.mesh = sp
		mi.position = center + off
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if shadow else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		var tex := _tex("res://textures/tiles/leaf_a.png" if (i + key) % 2 == 0 else "res://textures/tiles/leaf_b.png")
		var circ := TAU * rr
		var lm := _tiling_mat(tex, _leaf_uv(tex, circ), false)
		if lm is ShaderMaterial and haze_amt > 0.0:
			(lm as ShaderMaterial).set_shader_parameter("haze_amt", haze_amt)
		mi.material_override = lm
		parent.add_child(mi)


func _setup_canopies() -> void:
	# Fuller canopies on the framing trees (official tree canopy centre ≈ local (22,185,0)).
	var trees := [Vector4(-88, -44, 1.0, 0), Vector4(-145, 10, 0.78, 1), Vector4(165, -70, 0.82, 2), Vector4(175, -130, 0.88, 3)]
	var root := Node3D.new()
	root.name = "Canopies"
	add_child(root)
	_tree_shadow_nodes.append(root)
	for t in trees:
		var s: float = t.z
		_leaf_cluster(root, Vector3(t.x + 18.0 * s, 178.0 * s, t.y), 50.0 * s, 8, int(t.w) * 11 + 3, true)


func _setup_far_forest() -> void:
	# Layered tree silhouettes behind the garden; depth fog turns them into warm haze.
	var root := Node3D.new()
	root.name = "FarForest"
	add_child(root)
	var bark := _tex("res://textures/tiles/bark_a.png")  # v6.3: AI-based bark (32×64)
	var rows := [Vector3(-300, 96, 1.0), Vector3(-400, 118, 1.2), Vector3(-520, 140, 1.45)]  # v6: sparser → golden sky shows between crowns
	for ri in rows.size():
		var row: Vector3 = rows[ri]
		var step: float = row.y
		var x := -420.0 + float(ri) * 23.0
		var n := 0
		while x < 520.0:
			var k := ri * 97 + n * 31
			var jz := (fposmod(float(k) * 0.618034, 1.0) - 0.5) * 40.0
			var sc: float = row.z * (0.8 + 0.4 * fposmod(float(k) * 0.414214, 1.0))
			var h := 55.0 * sc
			# skip trees that would sit right behind the cottage roof / pet (keep the clearing)
			if true:
				var trunk := MeshInstance3D.new()
				var cy := CylinderMesh.new()
				cy.top_radius = 5.0 * sc
				cy.bottom_radius = 7.0 * sc
				cy.height = h
				cy.radial_segments = 8
				trunk.mesh = cy
				trunk.position = Vector3(x, h * 0.5, row.x + jz)
				trunk.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				var hz := 0.05 + 0.06 * float(ri)
				var tm := _tiling_mat(bark, Vector2(maxf(1.0, round(TAU * 6.0 * sc / 32.0)), maxf(1.0, round(h / 64.0))), false)
				if tm is ShaderMaterial:
					(tm as ShaderMaterial).set_shader_parameter("haze_amt", hz)
				trunk.material_override = tm
				root.add_child(trunk)
				_leaf_cluster(root, Vector3(x, h + 30.0 * sc, row.x + jz), 42.0 * sc, 6, k, false, 0.05 + 0.06 * float(ri))
			x += step * (0.85 + 0.3 * fposmod(float(k) * 0.7548, 1.0))
			n += 1


func _setup_dapple() -> void:
	# Sun-dappled light: invisible shadows-only leaf cookie high along the sun ray.
	var sun_dir := -_sun.global_transform.basis.z.normalized()
	var h := 230.0
	var t := h / -sun_dir.y
	var ground := Vector3(20, 0, -40)
	var c := ground - sun_dir * t
	var mi := MeshInstance3D.new()
	mi.name = "DappleCaster"
	var pm := PlaneMesh.new()
	pm.size = Vector2(600, 600)
	mi.mesh = pm
	mi.position = c
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
	var m := StandardMaterial3D.new()
	m.albedo_texture = _tex("res://textures/dapple_cookie.png")
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
	m.alpha_scissor_threshold = 0.5
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	mi.material_override = m
	add_child(mi)
	_fx_nodes.append(mi)
	print("dapple caster at ", c)


func _blocked(p: Vector2) -> bool:
	# Keep tufts off the path, cottage, fence, beds, pet and props.
	var path := [Vector2(0, 28), Vector2(8, 12), Vector2(18, -2), Vector2(30, -16), Vector2(44, -30), Vector2(58, -42), Vector2(70, -50), Vector2(96, -52)]
	for i in path.size() - 1:
		var a: Vector2 = path[i]
		var b: Vector2 = path[i + 1]
		var ab := b - a
		var tt := clampf((p - a).dot(ab) / ab.length_squared(), 0.0, 1.0)
		if p.distance_to(a + ab * tt) < 16.0:
			return true
	var rects := [Rect2(47, -100, 72, 60), Rect2(-120, -60, 182, 14), Rect2(-84, -43, 74, 24), Rect2(22, -34, 66, 28), Rect2(-20, -20, 40, 30)]
	for r in rects:
		if (r as Rect2).has_point(p):
			return true
	var props := [Vector2(-72.5, 22), Vector2(71, 24), Vector2(-39, 42), Vector2(35, 22), Vector2(-81, 70), Vector2(81, 54), Vector2(49, 22), Vector2(22, 18), Vector2(-24, 28), Vector2(48, 48), Vector2(18, 8), Vector2(-15, 35), Vector2(30, -20)]
	for q in props:
		if p.distance_to(q) < 13.0:
			return true
	return false


func _card_multimesh(tex_path: String, pts: Array, size: float) -> void:
	var sh := load("res://shaders/tuft.gdshader") as Shader
	var mat := ShaderMaterial.new()
	mat.shader = sh
	mat.set_shader_parameter("albedo_tex", _tex(tex_path))
	_tuft_mats.append(mat)
	for yaw in [0.0, 90.0]:
		var q := QuadMesh.new()
		q.size = Vector2(size, size)
		q.center_offset = Vector3(0, size * 0.5, 0)
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.mesh = q
		mm.instance_count = pts.size()
		for i in pts.size():
			var p: Vector3 = pts[i]
			var b := Basis(Vector3.UP, deg_to_rad(yaw + p.z)) * (0.8 + 0.4 * fposmod(float(i) * 0.618, 1.0))
			mm.set_instance_transform(i, Transform3D(b, Vector3(p.x, 0, p.y)))
		var mmi := MultiMeshInstance3D.new()
		mmi.multimesh = mm
		mmi.material_override = mat
		mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(mmi)


func _setup_tufts() -> void:
	# R2 low-discrepancy placement (deterministic, even, not a grid, not noise).
	var g := 1.32471795724474602596
	var a1 := 1.0 / g
	var a2 := 1.0 / (g * g)
	var ta: Array = []
	var tb: Array = []
	var fa: Array = []
	var fb: Array = []
	for i in 340:
		var u := fposmod(0.5 + a1 * float(i), 1.0)
		var v := fposmod(0.5 + a2 * float(i), 1.0)
		var p := Vector2(-230.0 + u * 470.0, -170.0 + v * 330.0)
		if _blocked(p):
			continue
		# v6: keep the sunlit centre lawn smooth (target look) — tufts only toward the edges
		if Vector2((p.x - 10.0) / 150.0, (p.y - 30.0) / 105.0).length() < 1.0 and i % 4 != 0:
			continue
		var yaw := float((i * 37) % 90)
		# flower clusters cluster near fence line, beds and the cottage front
		var near_bed := (p.y > -70.0 and p.y < 10.0 and p.x > -130.0 and p.x < 130.0)
		if i % 11 == 0 or (near_bed and i % 5 == 0):
			(fa if i % 2 == 0 else fb).append(Vector3(p.x, p.y, yaw))
		elif i % 2 == 0:
			ta.append(Vector3(p.x, p.y, yaw))
		else:
			tb.append(Vector3(p.x, p.y, yaw))
	_card_multimesh("res://textures/tiles/tuft_a.png", ta, 7.0)
	_card_multimesh("res://textures/tiles/tuft_b.png", tb, 7.0)
	_card_multimesh("res://textures/tiles/fcluster_a.png", fa, 9.0)
	_card_multimesh("res://textures/tiles/fcluster_b.png", fb, 9.0)
	print("tufts ", ta.size() + tb.size(), " flowers ", fa.size() + fb.size())



# ---------------- v5 additions ----------------
func _envf(k: String, d: float) -> float:
	return float(OS.get_environment(k)) if OS.get_environment(k) != "" else d


func _setup_pool() -> void:
	# Warm "sun pool" on the centre lawn: a shadowed spot light along the sun ray,
	# no distance falloff, soft cone edge. Makes centre bright, surroundings dark.
	var sun_dir := -_sun.global_transform.basis.z.normalized()
	var centre := Vector3(20, 0, -20)
	_pool = SpotLight3D.new()
	_pool.name = "SunPool"
	_pool.position = centre + Vector3(-0.40, 0.85, -0.34).normalized() * 600.0  # r3: steeper warm sky pool (grazing pool was too weak)
	_pool.light_color = Color(1.0, 0.80, 0.52)
	_pool.light_energy = 1.8
	_pool.light_specular = 0.0
	_pool.spot_range = 1100.0
	_pool.spot_attenuation = 0.0
	_pool.spot_angle = 14.0
	_pool.spot_angle_attenuation = 2.2
	_pool.shadow_enabled = true
	_pool.shadow_bias = 0.6
	_pool.shadow_normal_bias = 1.5
	_pool.shadow_blur = 0.5
	add_child(_pool)
	_pool.look_at(centre, Vector3.UP)
	# the pool light must respect the night/low toggles
	_apply_mode()


func _setup_rims(node: Node) -> void:
	if node.name in ["FarForest", "DappleCaster", "Shafts", "Dust"]:
		return
	if node is MeshInstance3D:
		var mi := node as MeshInstance3D
		if mi.mesh and not (mi.mesh is PlaneMesh or mi.mesh is QuadMesh) and mi.cast_shadow != GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY:
			var in_cottage := false
			var p: Node = mi
			while p:
				if str(p.name) == "cottage":
					in_cottage = true
					break
				p = p.get_parent()
			var m := ShaderMaterial.new()
			m.shader = load("res://shaders/rim_overlay.gdshader")
			var sun_dir := -_sun.global_transform.basis.z.normalized()
			m.set_shader_parameter("to_sun", -sun_dir)
			var a := _envf("HD2D_RIM", 0.35) * (0.45 if in_cottage else 1.0)
			m.set_meta("amt", a)
			m.set_shader_parameter("amt", a)
			mi.material_overlay = m
			_rim_mats.append(m)
	for c in node.get_children():
		_setup_rims(c)


func _set_normal(node: Node, ntex: Texture2D) -> void:
	if ntex == null:
		return
	if node is MeshInstance3D:
		var mi := node as MeshInstance3D
		for i in (mi.mesh.get_surface_count() if mi.mesh else 0):
			var m := mi.get_surface_override_material(i)
			if m is StandardMaterial3D:
				var sm := m as StandardMaterial3D
				sm.normal_enabled = true
				sm.normal_texture = ntex
				sm.normal_scale = _envf("HD2D_NDEPTH", 1.0)
	for c in node.get_children():
		_set_normal(c, ntex)


func _wood_triplanar(node: Node) -> void:
	# v5: fence rails/posts get the new plank tile + normal, world-triplanar (1 texel = 1 wu).
	if node is MeshInstance3D:
		var mi := node as MeshInstance3D
		for i in (mi.mesh.get_surface_count() if mi.mesh else 0):
			var sm := StandardMaterial3D.new()
			sm.albedo_texture = _tex("res://textures/tiles/timber_b.png")
			sm.albedo_color = Color(1.25, 1.1, 0.95)
			sm.normal_enabled = true
			sm.normal_texture = _tex("res://textures/tiles/timber_b_n.png")
			sm.uv1_triplanar = true
			sm.uv1_world_triplanar = true
			sm.uv1_scale = Vector3(1.0 / 16.0, 1.0 / 16.0, 1.0 / 16.0)
			sm.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
			sm.roughness = 1.0
			sm.specular_mode = BaseMaterial3D.SPECULAR_DISABLED
			mi.set_surface_override_material(i, sm)
	for c in node.get_children():
		_wood_triplanar(c)



# ---------------- v6 additions ----------------
func _is_portrait() -> bool:
	var sz := get_viewport().get_visible_rect().size
	return sz.y > sz.x


var _phone_init := false


func _apply_phone_budget(high: bool) -> void:
	# Note10+ class phone (Forward+ on Vulkan). Desktop / box captures stay at full res.
	if not OS.has_feature("mobile") and OS.get_environment("HD2D_FORCE_MOBILE") != "1":
		return
	var vp := get_viewport()
	vp.scaling_3d_mode = Viewport.SCALING_3D_MODE_BILINEAR
	# v6.2: High 0.5 (was 0.72); Low stays 0.60. SSAO / vol fog are off in _apply_mode.
	vp.scaling_3d_scale = 0.5 if high else 0.6
	if not _phone_init:
		_phone_init = true
		_configure_dof_quality()
		RenderingServer.environment_glow_set_use_bicubic_upscale(false)
		RenderingServer.directional_soft_shadow_filter_set_quality(RenderingServer.SHADOW_QUALITY_SOFT_LOW)
		Engine.max_fps = 60


func _leaf_uv(tex: Texture2D, circ: float) -> Vector2:
	# 16 px hand tile ≈ 9 wu; larger (AI-based, 128 px) leaf tile at 1 px/wu.
	var tw := float(tex.get_width()) if tex else 16.0
	var tile_wu := 9.0 if tw <= 16.0 else tw
	return Vector2(maxf(1.0, round(circ / tile_wu)), maxf(1.0, round(circ * 0.5 / tile_wu)))


# ---------------- v6.2 play + screenshot + HUD ----------------
func _clear_android_flag_secure() -> void:
	# Godot 4.7.2 Android does not set FLAG_SECURE (window_set_flag is a no-op;
	# no such flag in export presets, manifest, or the official Java/Kotlin host).
	# Still clear it at runtime in case an OEM / overlay left it on.
	if not OS.has_feature("android"):
		print("hd2d screenshot: not android; engine FLAG_SECURE not used")
		return
	var runtime: Object = Engine.get_singleton("AndroidRuntime")
	if runtime == null:
		push_warning("hd2d screenshot: AndroidRuntime missing")
		return
	var activity = runtime.getActivity()
	if activity == null:
		push_warning("hd2d screenshot: no activity")
		return
	# FLAG_SECURE = 0x00002000. Use the literal so a wrap failure cannot skip the clear.
	const FLAG_SECURE := 0x2000
	var window = activity.call("getWindow")
	if window == null:
		push_warning("hd2d screenshot: no window")
		return
	var attrs = window.call("getAttributes")
	var flags := 0
	if attrs != null:
		var f = attrs.get("flags")
		if f != null:
			flags = int(f)
	_flag_secure_was_set = (flags & FLAG_SECURE) != 0
	window.call("clearFlags", FLAG_SECURE)
	print("hd2d screenshot: FLAG_SECURE was_set=", _flag_secure_was_set, " cleared via AndroidRuntime")


func _setup_fps_overlay() -> void:
	var layer := CanvasLayer.new()
	layer.layer = 21
	layer.name = "FpsHud"
	add_child(layer)
	_fps_label = Label.new()
	_fps_label.name = "FpsLabel"
	_fps_label.anchor_left = 1.0
	_fps_label.anchor_right = 1.0
	_fps_label.anchor_top = 0.0
	_fps_label.anchor_bottom = 0.0
	_fps_label.offset_left = -420.0
	_fps_label.offset_right = -20.0
	_fps_label.offset_top = 20.0
	_fps_label.offset_bottom = 72.0
	_fps_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_fps_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_fps_label.add_theme_font_size_override("font_size", 18)
	_fps_label.add_theme_color_override("font_color", Color(1, 1, 1, 0.85))
	_fps_label.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.7))
	_fps_label.add_theme_constant_override("outline_size", 4)
	var font_path := "res://art/ui/GenWanMin2TC-R.subset.otf"
	if ResourceLoader.exists(font_path):
		var ff := FontFile.new()
		ff.load_dynamic_font(font_path)
		_fps_label.add_theme_font_override("font", ff)
	_fps_label.text = "– FPS"
	layer.add_child(_fps_label)
	_refresh_fps_label(0.0)
	_refresh_dev_ui()


func _refresh_fps_label(fps: float) -> void:
	if _fps_label == null:
		return
	var q := "Low"
	if _mode == "high":
		q = "High"
	elif _mode == "night":
		q = "Night"
	var fps_s := "–" if fps <= 0.0 else str(int(round(fps)))
	if _dev_on and _fps_n > 0:
		_fps_label.text = "%s FPS  %s  %s  min %d  avg %d  max %d" % [
			fps_s, _renderer(), q, int(round(_fps_min)), int(round(_fps_sum / float(_fps_n))), int(round(_fps_max))
		]
	else:
		_fps_label.text = "%s FPS  %s  %s" % [fps_s, _renderer(), q]


func _tick_play(dt: float) -> void:
	_tick_walk(dt)
	_tick_camera(dt)
	_tick_dof(dt, false)
	var bump := get_node_or_null("PropBump")
	if bump and bump.has_method("tick"):
		bump.call("tick", dt)
	_fps_accum += dt
	_fps_frames += 1
	if _fps_accum >= 0.5:
		var fps := float(_fps_frames) / _fps_accum
		_note_fps(fps)
		_refresh_fps_label(fps)
		_fps_accum = 0.0
		_fps_frames = 0


func _try_walk_tap(screen_pos: Vector2) -> void:
	if _pet == null or _camera == null:
		return
	var hit := _raycast_ground(screen_pos)
	if hit == Vector3.INF:
		return
	hit.y = 0.0
	var dest := _clamp_walkable(hit)
	if dest == Vector3.INF:
		return
	_walk_target = dest
	if _roam:
		_roam.begin_manual()
	print("hd2d walk dest=", dest)


func _raycast_ground(screen_pos: Vector2) -> Vector3:
	var origin := _camera.project_ray_origin(screen_pos)
	var dir := _camera.project_ray_normal(screen_pos)
	var far := origin + dir * 5000.0
	var space := get_world_3d().direct_space_state
	if space != null:
		var q := PhysicsRayQueryParameters3D.create(origin, far)
		q.collide_with_areas = false
		q.collide_with_bodies = true
		var hit: Dictionary = space.intersect_ray(q)
		if not hit.is_empty() and hit.has("position"):
			return hit["position"] as Vector3
	# Fallback: intersect the y=0 lawn plane (same as the visible ground).
	if absf(dir.y) < 0.0001:
		return Vector3.INF
	var t := -origin.y / dir.y
	if t <= 0.0:
		return Vector3.INF
	return origin + dir * t


func _walk_blocked(p: Vector2) -> bool:
	# Cottage, fence, and props. The garden path and the pet spawn stay walkable.
	# The same query drives tap steps and autonomous roam.
	if _roam == null:
		var roam_script := load("res://gameplay/m1_roam.gd") as GDScript
		if roam_script:
			_roam = roam_script.new()
			_roam.boot()
	if _roam == null:
		return false
	return bool(_roam.garden_blocked(p))


func _in_walk_bounds(p: Vector2) -> bool:
	if p.x < WALK_X_MIN or p.x > WALK_X_MAX or p.y < WALK_Z_MIN or p.y > WALK_Z_MAX:
		return false
	# Back-left corner: pet at (-140, -110) puts the camera inside the big tree.
	if p.y < WALK_BACK_Z and p.x < WALK_BACK_LEFT_X_MIN:
		return false
	return true


func _clamp_walkable(dest: Vector3) -> Vector3:
	var p := Vector2(dest.x, dest.z)
	p.x = clampf(p.x, WALK_X_MIN, WALK_X_MAX)
	p.y = clampf(p.y, WALK_Z_MIN, WALK_Z_MAX)
	if p.y < WALK_BACK_Z:
		p.x = maxf(p.x, WALK_BACK_LEFT_X_MIN)
	if not _walk_blocked(p):
		return Vector3(p.x, 0.0, p.y)
	# Walk toward the tap until just outside the obstacle.
	var start := Vector2(_pet.position.x, _pet.position.z)
	for i in range(8, 0, -1):
		var s := start.lerp(p, float(i) / 8.0)
		if _in_walk_bounds(s) and not _walk_blocked(s):
			return Vector3(s.x, 0.0, s.y)
	return Vector3.INF


func _tick_walk(dt: float) -> void:
	if _pet == null:
		return
	if _walk_target != null:
		if _roam and not _roam._manual:
			_roam.begin_manual()
		_tick_manual_walk(dt)
		return
	# Prop-bump demo drives the pet itself and clears any target.
	if OS.get_environment("HD2D_BUMP_DEMO") == "1":
		return
	if _roam == null:
		return
	var mul := 1.0
	var social := 0
	if Personality:
		mul = float(Personality.walk_speed_mul("tuanrong"))
		social = int(Personality.axis("tuanrong", "social"))
	var nxt: Vector2 = _roam.tick(Vector2(_pet.position.x, _pet.position.z), dt, mul, social)
	_pet.position = Vector3(nxt.x, PET_CENTER_Y, nxt.y)


func _tick_manual_walk(dt: float) -> void:
	var dest: Vector3 = _walk_target
	var pos := _pet.position
	var from := Vector3(pos.x, 0.0, pos.z)
	var to := Vector3(dest.x, 0.0, dest.z)
	var delta := to - from
	var dist := delta.length()
	if dist <= 1.25:
		_pet.position = Vector3(dest.x, PET_CENTER_Y, dest.z)
		_walk_target = null
		if _roam:
			_roam.notify_manual_done()
		return
	var step := WALK_SPEED * dt
	var nxt := from + delta * (minf(step, dist) / dist)
	var np := Vector2(nxt.x, nxt.z)
	if _walk_blocked(np) or not _in_walk_bounds(np):
		var sx := Vector3(nxt.x, 0.0, from.z)
		var sz := Vector3(from.x, 0.0, nxt.z)
		if not _walk_blocked(Vector2(sx.x, sx.z)) and _in_walk_bounds(Vector2(sx.x, sx.z)):
			nxt = sx
		elif not _walk_blocked(Vector2(sz.x, sz.z)) and _in_walk_bounds(Vector2(sz.x, sz.z)):
			nxt = sz
		else:
			_walk_target = null
			if _roam:
				_roam.notify_manual_done()
			return
	_pet.position = Vector3(nxt.x, PET_CENTER_Y, nxt.z)


func _tick_camera(dt: float) -> void:
	if _camera == null or _pet == null:
		return
	# Pure XZ translation, same offset as the opening shot. No yaw, no sway.
	# Yaw is not user-controlled (fixed opening heading). Pitch is fixed at V2_PITCH_DEG.
	# Observation overview holds the opening camera. Follow uses the same offset.
	var subject: Node3D = _pet
	var origin := _pet_origin_xz
	var overview := false
	var care := get_node_or_null("M1Care")
	if care:
		if care.has_method("camera_overview") and bool(care.call("camera_overview")):
			overview = true
		if not overview and care.has_method("follow_subject"):
			var picked: Variant = care.call("follow_subject")
			if picked is Node3D and is_instance_valid(picked):
				subject = picked
		if care.has_method("subject_origin"):
			var got: Variant = care.call("subject_origin", subject)
			if got is Vector3:
				origin = got
	var desired: Vector3 = M1CameraPolicy.desired(_cam_base_pos, origin, Vector3(subject.position.x, 0.0, subject.position.z), overview)
	var close := false
	if care and not overview and care.has_method("follow_close"):
		close = bool(care.call("follow_close"))
	if close:
		var scale := _follow_zoom_scale if _follow_zoom_scale > 0.0 else M1CameraPolicy.zoom_scale(_opening_pet_frac, _follow_pet_min())
		desired = M1CameraPolicy.zoomed_along(desired, subject.global_position, scale)
	# v6.7: do not let the follow camera enter the back-left tree (x ≥ -100 in that band).
	if not overview and desired.z <= CAM_TREE_BAND_Z:
		desired.x = maxf(desired.x, CAM_FOLLOW_X_MIN)
	var k := 1.0 - exp(-CAM_FOLLOW_DAMPING * dt)
	_cam_follow_pos = _cam_follow_pos.lerp(desired, k)
	if not overview and _cam_follow_pos.z <= CAM_TREE_BAND_Z:
		_cam_follow_pos.x = maxf(_cam_follow_pos.x, CAM_FOLLOW_X_MIN)
	_camera.position = _cam_follow_pos


func _smoke_walk_and_quit() -> void:
	print("hd2d smoke renderer=", _renderer(), " mode=", _mode, " pet=", _pet != null, " cam=", _camera != null)
	if _pet == null or _camera == null:
		push_error("hd2d smoke missing pet/camera")
		get_tree().quit(1)
		return
	var travel := -_sun.global_transform.basis.z.normalized() if _sun else Vector3.ZERO
	var elev := rad_to_deg(asin(clampf(-travel.y, -1.0, 1.0))) if _sun else 0.0
	print("hd2d smoke sun travel=", travel, " elev=", snapped(elev, 0.1), " match=", travel.distance_to(SUN_DIR_V67.normalized()) < 0.01)
	var corner := _clamp_walkable(Vector3(-140, 0, -110))
	print("hd2d smoke clamp back-left=", corner, " in_bounds_raw=", _in_walk_bounds(Vector2(-140, -110)))
	var saved_pet := _pet.position
	_pet.position = Vector3(corner.x, PET_CENTER_Y, corner.z)
	_tick_camera(10.0)
	print("hd2d smoke cam at back-left pet=", _pet.position, " cam=", _camera.position, " cam_x_ok=", _camera.position.x >= CAM_FOLLOW_X_MIN - 0.01)
	_pet.position = saved_pet
	_tick_camera(10.0)
	_print_pet_framing()
	print("hd2d dof policy amount=", DOF_AMOUNT_MOBILE, " near_dist=", DOF_NEAR_DIST, " near_pad=", DOF_NEAR_PAD, " near_trans=", DOF_NEAR_TRANS, " far_pad=", DOF_FAR_PAD, " far_trans=", DOF_FAR_TRANS, " near_want=", _mode != "low" and _is_forward())
	var dapple := get_node_or_null("DappleCaster") as GeometryInstance3D
	if dapple:
		print("hd2d dapple visible=", dapple.visible, " cast=", dapple.cast_shadow, " want_hidden=", not (dapple.visible and dapple.cast_shadow != GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY))
	var shafts := get_node_or_null("Shafts")
	if shafts:
		var zmin := 1.0e9
		var zmax := -1.0e9
		for c in shafts.get_children():
			if c is Node3D:
				zmin = minf(zmin, (c as Node3D).position.z)
				zmax = maxf(zmax, (c as Node3D).position.z)
		print("hd2d shafts count=", shafts.get_child_count(), " z=", snapped(zmin, 0.1), "..", snapped(zmax, 0.1), " name=", shafts.name)
	print("hd2d skip bg_sky=", get_node_or_null("bg_sky") == null, " voxel_tree_play=", _count_voxel_trees())
	_print_geo_counts("smoke")
	var dest := _clamp_walkable(Vector3(18, 0, 8))
	if dest == Vector3.INF:
		dest = Vector3(8, 0, 8)
	_walk_target = dest
	# Advance a few steps without waiting for the frame loop in case dt is 0 on dummy.
	for i in range(8):
		_tick_walk(0.05)
		_tick_camera(0.05)
		_tick_dof(0.05, false)
		var bump_w := get_node_or_null("PropBump")
		if bump_w and bump_w.has_method("tick"):
			bump_w.call("tick", 0.05)
	print("hd2d smoke after walk pet=", _pet.position, " cam=", _camera.position, " target=", _walk_target, " d_pet=", snapped(_dof_d_pet, 0.1), " far=", snapped(_attrs.dof_blur_far_distance, 0.1), " amount=", _attrs.dof_blur_amount, " near_on=", _attrs.dof_blur_near_enabled, " bake=", _bake_shadow_ground, " grade=", _grade_tweak, " sat=", snapped(_env.adjustment_saturation, 0.01), " contrast=", snapped(_env.adjustment_contrast, 0.01), " lut=", _env.adjustment_color_correction != null, " blur=", snapped(_sun.shadow_blur, 0.01), " angular=", snapped(_sun.light_angular_distance, 0.01), " sh_op=", snapped(float(_sun.get("shadow_opacity")) if "shadow_opacity" in _sun else -1.0, 0.01), " sun_on=", _sun.shadow_enabled, " sun_mode=", _sun.directional_shadow_mode, " sun_dist=", _sun.directional_shadow_max_distance, " beds=", _bed_flower_mats.size())
	_print_shadow_caster_counts()
	var bump_s := get_node_or_null("PropBump")
	if bump_s and bump_s.has_method("smoke_drive_hits"):
		bump_s.call("smoke_drive_hits")
	var galbedo = _ground_mat.get_shader_parameter("albedo_tex") if _ground_mat else null
	var gpath := ""
	if galbedo is Texture2D:
		gpath = (galbedo as Texture2D).resource_path
	print("hd2d ground bake=", _bake_shadow_ground, " albedo=", gpath)
	_print_bake_bounds()
	_print_tone()
	_scan_null_materials("smoke")

	# Always print the follow formula at near/mid/far (even when this box cannot enable DOF).
	var saved := _pet.position
	for shot in ["near", "mid", "far"]:
		OS.set_environment("HD2D_PET_SHOT", shot)
		_place_pet_shot()
		var d := _camera.global_position.distance_to(_pet.global_position)
		var near_d := minf(DOF_NEAR_DIST, maxf(d - DOF_NEAR_PAD, DOF_NEAR_MIN))
		print("hd2d dof math shot=", shot, " pet=", _pet.position, " d=", snapped(d, 0.1), " far=", snapped(d + DOF_FAR_PAD, 0.1), " near=", snapped(near_d, 0.1), " applied_far=", snapped(_attrs.dof_blur_far_distance, 0.1), " applied_amount=", _attrs.dof_blur_amount, " near_on=", _attrs.dof_blur_near_enabled, " renderer=", _renderer())
	_pet.position = saved
	get_tree().quit(0)





func _configure_dof_quality() -> void:
	# Safe on Mobile. BOX bokeh is cheaper and smaller than hexagon (DOF_NOTE).
	RenderingServer.camera_attributes_set_dof_blur_quality(RenderingServer.DOF_BLUR_QUALITY_LOW, false)
	RenderingServer.camera_attributes_set_dof_blur_bokeh_shape(RenderingServer.DOF_BOKEH_BOX)


func _tick_dof(dt: float, snap: bool) -> void:
	if _attrs == null or _camera == null or _pet == null:
		return
	if _mode == "low" or not _is_forward():
		return
	var d := _camera.global_position.distance_to(_pet.global_position)
	if not _dof_inited or snap:
		_dof_d_pet = d
		_dof_inited = true
	else:
		var k := 1.0 - exp(-DOF_DAMPING * maxf(dt, 0.0))
		_dof_d_pet = lerpf(_dof_d_pet, d, k)
	_attrs.dof_blur_far_distance = _dof_d_pet + DOF_FAR_PAD
	# Cap the near plane at 140 wu so mid/bottom lawn stays sharp; still keep a
	# 40 wu focus margin in front of 團絨 if the pet is ever closer than 180.
	_attrs.dof_blur_near_distance = minf(DOF_NEAR_DIST, maxf(_dof_d_pet - DOF_NEAR_PAD, DOF_NEAR_MIN))


func _apply_shadow_policy(high: bool) -> void:
	# v6.14-code:
	# - bake_pass MUST keep sun.shadow_enabled ON (previous `not bake_pass` emptied the bake).
	# - Skip hybrid caster cutoff during bake; restore saved casts and keep tree casters on.
	# - Low day play: sun OFF so art_depth._low_fake_shadow can show baked-prop ground + pet silhouette.
	#   Escape hatch: HD2D_LOW_LIVE=1 keeps the previous Low hybrid live sun.
	# - DappleCaster is never visible in a bake pass and stays hidden when tree_live is off.
	# Do not replace 遊美 bake textures on this box. Cloud / light motion stays in art_depth._dynamics.
	var night := _mode == "night"
	var bake_pass := OS.get_environment("HD2D_BAKE_SHADOW") == "1"
	_snapshot_shadow_casts()
	if bake_pass:
		_sun.shadow_enabled = true
		var def_atlas_b := int(ProjectSettings.get_setting("rendering/lights_and_shadows/directional_shadow/size.mobile", 2048))
		RenderingServer.directional_shadow_atlas_set_size(max(def_atlas_b, 2048), false)
		_sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS
		_sun.directional_shadow_max_distance = SHADOW_MAX_DIST_HIGH
		_sun.shadow_blur = SHADOW_BLUR_HIGH
		_sun.light_angular_distance = SHADOW_ANGULAR_HIGH
		if "shadow_opacity" in _sun:
			_sun.set("shadow_opacity", SHADOW_OPACITY_HIGH)
		_restore_shadow_casts()
		for n in _tree_shadow_nodes:
			_tag_shadow(n, true)
		var dapple_b := get_node_or_null("DappleCaster")
		if dapple_b is GeometryInstance3D:
			var gib := dapple_b as GeometryInstance3D
			gib.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
			gib.visible = false
		_apply_ground_bake()
		print("hd2d shadow policy bake_pass sun_on=", _sun.shadow_enabled, " trees_on=1 dapple_hidden=1")
		return
	# Play: Low day turns live sun shadows off (baked + silhouette). High keeps live shadows.
	var low_live := OS.get_environment("HD2D_LOW_LIVE") == "1"
	_sun.shadow_enabled = (not night) and (high or low_live)
	if high:
		var def_atlas := int(ProjectSettings.get_setting("rendering/lights_and_shadows/directional_shadow/size.mobile", 2048))
		RenderingServer.directional_shadow_atlas_set_size(def_atlas, false)
		_sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS
		_sun.directional_shadow_max_distance = SHADOW_MAX_DIST_HIGH
		_sun.shadow_blur = SHADOW_BLUR_HIGH
		_sun.light_angular_distance = SHADOW_ANGULAR_HIGH
		if "shadow_opacity" in _sun:
			_sun.set("shadow_opacity", SHADOW_OPACITY_HIGH)
		_restore_shadow_casts()
	else:
		RenderingServer.directional_shadow_atlas_set_size(SHADOW_ATLAS_LOW, false)
		_sun.directional_shadow_mode = DirectionalLight3D.SHADOW_ORTHOGONAL
		_sun.directional_shadow_max_distance = SHADOW_MAX_DIST_LOW
		_sun.shadow_blur = SHADOW_BLUR_LOW
		_sun.light_angular_distance = SHADOW_ANGULAR_LOW
		if "shadow_opacity" in _sun:
			_sun.set("shadow_opacity", SHADOW_OPACITY_LOW)
		if _sun.shadow_enabled:
			_apply_hybrid_casters()
		else:
			# Live casters off while the sun is off; baked map + pet silhouette carry the shadows.
			_restore_shadow_casts()
			for gi in _all_geom(self):
				if str(gi.name) == "DappleCaster" or _is_under_name(gi, "DappleCaster"):
					gi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
					continue
				# Leave saved casts; no live sun means they will not draw shadows anyway.
	var tree_live := high and not _bake_shadow_ground and not bake_pass
	for n in _tree_shadow_nodes:
		_tag_shadow(n, tree_live)
	var dapple := get_node_or_null("DappleCaster")
	if dapple is GeometryInstance3D:
		# Always SHADOWS_ONLY so the 600 wu cookie plane is never drawn into the sky.
		# Hide when live tree shadows are off, and always hide during a bake pass.
		var gi := dapple as GeometryInstance3D
		gi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
		gi.visible = tree_live and not bake_pass
	_apply_ground_bake()


func _snapshot_shadow_casts() -> void:
	if not _shadow_policy_ready:
		return
	if _shadow_cast_inited:
		return
	_shadow_cast_inited = true
	_shadow_cast_saved.clear()
	for n in _all_geom(self):
		_shadow_cast_saved[n] = n.cast_shadow


func _restore_shadow_casts() -> void:
	for n in _shadow_cast_saved:
		if is_instance_valid(n):
			(n as GeometryInstance3D).cast_shadow = _shadow_cast_saved[n]


func _all_geom(n: Node) -> Array[GeometryInstance3D]:
	var out: Array[GeometryInstance3D] = []
	var stack: Array[Node] = [n]
	while stack:
		var cur: Node = stack.pop_back()
		if cur is GeometryInstance3D:
			out.append(cur as GeometryInstance3D)
		for c in cur.get_children():
			stack.append(c)
	return out


func _is_hybrid_live_caster(n: Node) -> bool:
	# Jars are excluded on purpose (GAPS §5.6: tiny, baked contact AO is enough, −1 walk draw).
	if _pet != null and (n == _pet or _pet.is_ancestor_of(n)):
		return true
	if n.has_meta("hy_dyn"):
		return true
	var p: Node = n
	while p != null and p != self:
		var nm := str(p.name)
		if nm.begins_with("pot_S") or nm.begins_with("pot_L") or nm.begins_with("pot_R") or nm.begins_with("CrateWood"):
			return true
		if nm == "can" or nm.begins_with("can_"):
			return true
		p = p.get_parent()
	return false


func _apply_hybrid_casters() -> void:
	var n_on := 0
	var n_jar_off := 0
	for gi in _all_geom(self):
		if str(gi.name) == "DappleCaster" or _is_under_name(gi, "DappleCaster"):
			gi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
			continue
		if _is_hybrid_live_caster(gi):
			gi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
			n_on += 1
		else:
			if _is_under_name(gi, "jar") or str(gi.name).begins_with("jar"):
				n_jar_off += 1
			gi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	print("hd2d hybrid casters on=", n_on, " jar_off=", n_jar_off, " atlas=", SHADOW_ATLAS_LOW, " mode=orthogonal dist=", SHADOW_MAX_DIST_LOW)


func _is_under_name(n: Node, prefix: String) -> bool:
	var p: Node = n
	while p != null and p != self:
		var nm := str(p.name)
		if nm == prefix or nm.begins_with(prefix + "_") or (prefix.length() > 0 and nm.begins_with(prefix) and nm.substr(prefix.length()).is_valid_int()):
			return true
		p = p.get_parent()
	return false


func _apply_bed_flower_shader() -> void:
	# bed.glb is one mesh: wood frame + soil (local y ≤ 6) and seedling cards (y up to 29).
	# Swap to bed_flower.gdshader so only the cards use tuft-style pet_push.
	var sh := load("res://shaders/bed_flower.gdshader") as Shader
	if sh == null:
		push_warning("missing bed_flower.gdshader")
		return
	var n_beds := 0
	for n in _all_geom(self):
		if not (n is MeshInstance3D):
			continue
		if not _is_bed_node(n):
			continue
		var mi := n as MeshInstance3D
		var tex: Texture2D = null
		var src: Material = mi.material_override
		if src == null:
			src = mi.get_active_material(0)
		if src is ShaderMaterial:
			var ev = (src as ShaderMaterial).get_shader_parameter("albedo_tex")
			if ev is Texture2D:
				tex = ev as Texture2D
		elif src is BaseMaterial3D:
			tex = (src as BaseMaterial3D).albedo_texture
		var mat := ShaderMaterial.new()
		mat.shader = sh
		if tex:
			mat.set_shader_parameter("albedo_tex", tex)
		mat.set_shader_parameter("push", 7.0)
		mat.set_shader_parameter("stem_y", 6.0)
		mi.material_override = mat
		_bed_flower_mats.append(mat)
		n_beds += 1
	print("hd2d bed-flower shader on ", n_beds, " meshes, param=pet_pos_ws")


func _is_bed_node(n: Node) -> bool:
	var p: Node = n
	while p != null and p != self:
		var nm := str(p.name)
		if nm == "bed" or nm.begins_with("bed_"):
			return true
		p = p.get_parent()
	return false


func _apply_ground_bake() -> void:
	if _ground_mat == null or _ground_tex_low == null:
		return
	# Use the bake whenever live tree shadows are off (Low, or High with bake).
	var use_bake := _bake_shadow_ground
	_ground_mat.set_shader_parameter("albedo_tex", _ground_tex_low if use_bake else _ground_tex_high)


func _ensure_grade_lut() -> Texture:
	if _grade_lut != null:
		return _grade_lut
	# 256×1 1D LUT (Mobile-supported color correction): warm highlights, mid/shadows ~identity.
	# Fixes the sat-0.80 olive cast on golden haze; 原調 leaves this unset.
	var img := Image.create(256, 1, false, Image.FORMAT_RGB8)
	for i in 256:
		var t := float(i) / 255.0
		var w := smoothstep(0.50, 0.92, t)
		var r := clampf(t + 0.10 * w, 0.0, 1.0)
		var g := clampf(t + 0.03 * w, 0.0, 1.0)
		var b := clampf(t - 0.05 * w, 0.0, 1.0)
		img.set_pixel(i, 0, Color(r, g, b))
	_grade_lut = ImageTexture.create_from_image(img)
	return _grade_lut


func _apply_grade() -> void:
	if _env == null:
		return
	_env.adjustment_enabled = true
	var use_tweak := _grade_tweak and _mode != "night"
	_env.adjustment_saturation = GRADE_SAT_TWEAK if use_tweak else GRADE_SAT_DEFAULT
	_env.adjustment_contrast = GRADE_CON_TWEAK if use_tweak else GRADE_CON_DEFAULT
	_env.adjustment_color_correction = _ensure_grade_lut() if use_tweak else null
	if _grade_fx_mat:
		_grade_fx_mat.set_shader_parameter("leak_strength", GRADE_LEAK_TWEAK if use_tweak else GRADE_LEAK_BASE)
	# Glow warmth only in day — night keeps its own glow numbers in _apply_mode.
	if _mode != "night":
		_env.glow_intensity = GRADE_GLOW_INT_TWEAK if use_tweak else GRADE_GLOW_INT_BASE
		_env.glow_hdr_threshold = GRADE_GLOW_HDR_TWEAK if use_tweak else GRADE_GLOW_HDR_BASE


func _toggle_grade() -> void:
	_grade_tweak = not _grade_tweak
	_apply_grade()
	_refresh_grade_btn()
	print("hd2d grade tweak=", _grade_tweak, " sat=", _env.adjustment_saturation if _env else -1.0, " contrast=", _env.adjustment_contrast if _env else -1.0, " lut=", (_env.adjustment_color_correction != null) if _env else false)


func _refresh_grade_btn() -> void:
	if _grade_btn == null:
		return
	_grade_btn.text = "色調：微調" if _grade_tweak else "色調：原調"


func _place_pet_shot() -> void:
	if _pet == null or _camera == null:
		return
	var shot := OS.get_environment("HD2D_PET_SHOT").to_lower()
	if shot == "":
		return
	var p := Vector3.ZERO
	if shot == "near":
		p = Vector3(0.0, 0.0, 48.0)
	elif shot == "far":
		p = Vector3(18.0, 0.0, -36.0)
	elif shot == "mid":
		p = Vector3(0.0, 0.0, 0.0)
	else:
		return
	_pet.position = Vector3(p.x, PET_CENTER_Y, p.z)
	_walk_target = null
	var delta := Vector3(_pet.position.x - _pet_origin_xz.x, 0.0, _pet.position.z - _pet_origin_xz.z)
	_cam_follow_pos = _cam_base_pos + delta
	_camera.position = _cam_follow_pos
	_tick_dof(0.0, true)
	print("hd2d pet shot=", shot, " pet=", _pet.position, " d_pet=", snapped(_dof_d_pet, 0.1), " far=", snapped(_attrs.dof_blur_far_distance, 0.1))

func _retexture(node: Node, tex: Texture2D) -> void:
	# v6.3 texture swap only (same UVs/material settings).
	if node is MeshInstance3D:
		var mi := node as MeshInstance3D
		for i in (mi.mesh.get_surface_count() if mi.mesh else 0):
			var m := mi.get_surface_override_material(i)
			if m is StandardMaterial3D:
				(m as StandardMaterial3D).albedo_texture = tex
	for c in node.get_children():
		_retexture(c, tex)


func _print_shadow_caster_counts() -> void:
	var n_on := 0
	var n_off := 0
	var n_only := 0
	var names_on: PackedStringArray = PackedStringArray()
	for gi in _all_geom(self):
		if not gi.is_visible_in_tree():
			continue
		var cs := gi.cast_shadow
		if cs == GeometryInstance3D.SHADOW_CASTING_SETTING_OFF:
			n_off += 1
		elif cs == GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY:
			n_only += 1
		else:
			n_on += 1
			if names_on.size() < 24:
				names_on.append(gi.name)
	var draws := Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)
	var prims := Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)
	print("hd2d casters visible on=", n_on, " off=", n_off, " shadows_only=", n_only, " draws=", draws, " prims=", prims, " on_names=", ", ".join(names_on))


func _add_m1_care() -> void:
	# Gameplay slice. Does not edit art_depth, shaders, or mesh placement.
	var roam_script := load("res://gameplay/m1_roam.gd") as GDScript
	if roam_script:
		_roam = roam_script.new()
		_roam.boot()
	var script := load("res://gameplay/m1_care.gd") as GDScript
	if script == null:
		push_warning("missing m1_care.gd")
		return
	var n: Node = script.new()
	n.name = "M1Care"
	add_child(n)
	if n.has_method("bind_host"):
		n.call("bind_host", self)


func _add_prop_bump() -> void:
	# v6.8 prototype: spring-damper prop bump + pet_pos_ws reserve. See scenes/prop_bump.gd.
	var script := load("res://scenes/prop_bump.gd") as GDScript
	if script == null:
		push_warning("missing prop_bump.gd")
		return
	var n: Node = script.new()
	n.name = "PropBump"
	n.set("host", self)
	add_child(n)
	if n.has_signal("prop_bump_hit"):
		n.connect("prop_bump_hit", _on_audio_prop_bump_hit)
	if n.has_signal("prop_settle"):
		n.connect("prop_settle", _on_audio_prop_settle)
	if n.has_signal("grass_rustle"):
		n.connect("grass_rustle", _on_audio_grass_rustle)


func _add_art_depth() -> void:
	# v6.4/v6.5: cottage relief, edge tufts, baked-shadow ground (art).
	# Ground albedo swap on High is owned by _apply_ground_bake() so tree
	# shadows stay baked when live tree casters are off.
	var script := load("res://scenes/art_depth.gd") as GDScript
	if script == null:
		push_warning("missing art_depth.gd")
		return
	var ad: Node = script.new()
	ad.name = "ArtDepth"
	ad.set("host", self)
	add_child(ad)


func _count_voxel_trees() -> int:
	var n := 0
	for c in get_children():
		if c is MeshInstance3D and str(c.name) == "tree" and (c as MeshInstance3D).mesh is ArrayMesh:
			n += 1
	return n


func _print_geo_counts(tag: String) -> void:
	# Headless gl_compat reports 0 from Performance monitors; walk the tree instead.
	var vis := 0
	var hidden := 0
	var prims_vis := 0
	var prims_all := 0
	var stack: Array[Node] = [self]
	while stack:
		var n: Node = stack.pop_back()
		for c in n.get_children():
			stack.append(c)
		if n is MultiMeshInstance3D and (n as MultiMeshInstance3D).multimesh:
			var mm := (n as MultiMeshInstance3D).multimesh
			var tri := 0
			if mm.mesh:
				for si in mm.mesh.get_surface_count():
					var arr := mm.mesh.surface_get_arrays(si)
					var ix = arr[Mesh.ARRAY_INDEX]
					tri += (ix.size() if ix != null else (arr[Mesh.ARRAY_VERTEX] as PackedVector3Array).size()) / 3
			var p := tri * mm.instance_count
			prims_all += p
			if (n as MultiMeshInstance3D).visible:
				vis += 1
				prims_vis += p
			else:
				hidden += 1
		elif n is MeshInstance3D and (n as MeshInstance3D).mesh:
			var mesh := (n as MeshInstance3D).mesh
			var tri := 0
			for si in mesh.get_surface_count():
				var arr := mesh.surface_get_arrays(si)
				var ix = arr[Mesh.ARRAY_INDEX]
				tri += (ix.size() if ix != null else (arr[Mesh.ARRAY_VERTEX] as PackedVector3Array).size()) / 3
			prims_all += tri
			if (n as MeshInstance3D).visible:
				vis += 1
				prims_vis += tri
			else:
				hidden += 1
	print("hd2d geo ", tag, " visible_mi=", vis, " hidden_mi=", hidden, " prims_vis=", prims_vis, " prims_all=", prims_all, " perf_draws=", Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME), " perf_prims=", Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME))



func _toggle_dev() -> void:
	_dev_on = not _dev_on
	_refresh_dev_ui()
	print("hd2d dev mode=", _dev_on)
	_refresh_fps_label(0.0)


func _refresh_dev_ui() -> void:
	var show_tools := M1UiLayout.debug_chrome_visible(_dev_on)
	if _dev_btn:
		_dev_btn.text = "開發者：開" if _dev_on else "開發者：關"
		_dev_btn.visible = show_tools
	if _quality_btn:
		_quality_btn.visible = show_tools
	if _grade_btn:
		_grade_btn.visible = show_tools
	if _shot_btn:
		_shot_btn.visible = show_tools
	if _dev_log:
		_dev_log.visible = show_tools
		if _dev_on and _dev_log.text == "":
			_dev_log.text = "開發者：截圖寫入 user://shots 同相簿；音效事件會列喺呢度。"
	if _fps_label:
		_fps_label.visible = show_tools
	if _dev_entry:
		_dev_entry.visible = true
		_dev_entry.text = "開發中" if _dev_on else "開發"


func _note_fps(fps: float) -> void:
	if fps <= 0.5:
		return
	_fps_n += 1
	_fps_sum += fps
	_fps_min = minf(_fps_min, fps)
	_fps_max = maxf(_fps_max, fps)
	if not _dev_on:
		return
	_fps_log_left -= 0.5
	if _fps_log_left > 0.0:
		return
	_fps_log_left = 2.0
	var line := "fps t=%.1f cur=%.1f min=%.1f avg=%.1f max=%.1f mode=%s" % [
		Time.get_ticks_msec() * 0.001, fps, _fps_min, _fps_sum / float(_fps_n), _fps_max, _mode
	]
	print("hd2d ", line)
	var f := FileAccess.open("user://fps_session.txt", FileAccess.READ_WRITE)
	if f == null:
		f = FileAccess.open("user://fps_session.txt", FileAccess.WRITE)
	if f:
		f.seek_end()
		f.store_line(line)
		f.close()


func _dev_screenshot() -> void:
	var vp := get_viewport()
	var img: Image = vp.get_texture().get_image()
	if img == null:
		push_warning("dev screenshot: viewport image is null")
		return
	if _looks_flipped(img):
		img.flip_y()
	var stamp := Time.get_datetime_string_from_system().replace(":", "").replace("T", "_")
	var rel := "user://shots"
	DirAccess.make_dir_recursive_absolute(rel)
	var path := rel.path_join("hd2d_%s.png" % stamp)
	var err := img.save_png(path)
	var abs_path := ProjectSettings.globalize_path(path)
	print("hd2d dev screenshot ", abs_path, " ", img.get_width(), "x", img.get_height(), " err=", err)
	_dev_audio_line("截圖 " + abs_path)
	var pics := OS.get_system_dir(OS.SYSTEM_DIR_PICTURES)
	if pics != "":
		DirAccess.make_dir_recursive_absolute(pics)
		var alt := pics.path_join("hd2d_%s.png" % stamp)
		var e2 := img.save_png(alt)
		print("hd2d dev screenshot pictures ", alt, " err=", e2)


func _dev_audio_line(msg: String) -> void:
	# Prints live in prop_bump.gd; here we only fill the 開發者 on-screen log.
	if _dev_log == null:
		return
	if not _dev_on:
		return
	var lines := _dev_log.text.split("
")
	var kept: PackedStringArray = PackedStringArray()
	kept.append(msg)
	var n := 0
	for L in lines:
		if n >= 6:
			break
		if L != "" and L != msg:
			kept.append(L)
			n += 1
	_dev_log.text = "
".join(kept)


func _on_audio_prop_bump_hit(type: String, strength: float, pos: Vector3) -> void:
	_dev_audio_line("prop_bump_hit type=%s strength=%.2f pos=(%.1f,%.1f,%.1f)" % [type, strength, pos.x, pos.y, pos.z])


func _on_audio_prop_settle(type: String) -> void:
	_dev_audio_line("prop_settle type=%s" % type)


func _on_audio_grass_rustle(intensity: float, pos: Vector3) -> void:
	_dev_audio_line("grass_rustle intensity=%.2f pos=(%.1f,%.1f,%.1f)" % [intensity, pos.x, pos.y, pos.z])


func _print_bake_bounds() -> void:
	# Capture owns GroundInner size; the bake camera / atlas live in art_depth._setup_shadow_bake.
	print("hd2d bake bounds GroundInner plane 256x256 at (0,0,0) xz[-128,128] (capture._setup_ground)")
	print("hd2d bake bounds left fence ~= (-120,-60) is 8 wu inside the GroundInner edge — dark rectangle is a bake-extent cutoff")
	print("hd2d bake bounds art_depth._setup_shadow_bake (do not edit here): cam.size=256 KEEP_WIDTH at (0,420,0) far=1200; HD2D_BAKE_WIDE=1 uses cam.size=900 plane 1000x1000; sun atlas 8192, max_distance 480 inner / 1300 wide")


func _print_tone() -> void:
	if _env == null:
		return
	var exp_a := -1.0
	if _attrs and "exposure_multiplier" in _attrs:
		exp_a = float(_attrs.get("exposure_multiplier"))
	print("hd2d tone mode=", _env.tonemap_mode, " exposure=", snapped(_env.tonemap_exposure, 0.01), " white=", snapped(_env.tonemap_white, 0.01), " attrs_mult=", snapped(exp_a, 0.01), " sat=", snapped(_env.adjustment_saturation, 0.01), " contrast=", snapped(_env.adjustment_contrast, 0.01))


func _scan_null_materials(tag: String) -> void:
	var n_null := 0
	for gi in _all_geom(self):
		if gi is SpriteBase3D or gi is Label3D:
			continue
		var has := gi.material_override != null or gi.material_overlay != null
		if gi is MeshInstance3D:
			var mi := gi as MeshInstance3D
			if mi.mesh:
				for s in mi.mesh.get_surface_count():
					if mi.get_active_material(s) != null:
						has = true
		elif gi is MultiMeshInstance3D:
			var mm := gi as MultiMeshInstance3D
			if mm.material_override != null:
				has = true
			elif mm.multimesh and mm.multimesh.mesh:
				for s in mm.multimesh.mesh.get_surface_count():
					if mm.multimesh.mesh.surface_get_material(s) != null:
						has = true
		if not has:
			n_null += 1
			print("hd2d null material ", gi.get_path(), " class=", gi.get_class(), " name=", gi.name)
	print("hd2d null material scan ", tag, " count=", n_null)
