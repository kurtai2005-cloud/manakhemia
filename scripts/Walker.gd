extends Node3D
class_name Walker
## 自主行：優先 NavigationAgent3D，否則 footprint 迴避亂走。Sprite3D billboard。

@export var speed: float = 20.0
@export var radius: float = 10.0
@export var idle_fps: float = 4.0
@export var walk_fps: float = 10.0
@export var pause_min: float = 1.2
@export var pause_max: float = 3.5

var agent: NavigationAgent3D
var sprite: Sprite3D
var frames: Dictionary = {}  # "front_idle" -> Array[Texture2D]
var flip_x := false
var dir := "front"  # front / back / side
var moving := false
var frame_i := 0
var frame_t := 0.0
var pause_t := 0.0
var rng := RandomNumberGenerator.new()
var feet: Footprints
var use_nav := true
var pixel_size := 1.0
var pivot := Vector2(32, 61)
var frame_size := Vector2(64, 64)
var live_clip := ""
var live_frames: Array = []
var live_i := 0
var live_t := 0.0
var _clip_loops := 0
var _sfx_fired: Dictionary = {}
var character := "tuanrong"
var body_size := "L"  # S / M / L；clip 共用，各自用自己尺寸同 anchor
var _step_cool := 0.0
var _clip_elapsed := 0.0
var _base_pixel_size := 1.0
var _live_src_size := 64.0
var _base_modulate := Color.WHITE
var _tod_modulate := Color.WHITE
var _low_unshaded := false
var brain_driven := false
var speed_mul := 1.0
var follow_target: Node3D
var follow_dist := 16.0
var click_area: Area3D
var walk_bob := false
var _bob_t := 0.0
var _base_offset := Vector2.ZERO
var _vis_tex: Texture2D
var _vis_top := 0.0
var _vis_bot := 0.0
var _vis_ok := false

func setup(tex_frames: Dictionary, p_size: float, pvt: Vector2, fsize: Vector2) -> void:
	frames = tex_frames
	pixel_size = p_size
	_base_pixel_size = p_size
	pivot = pvt
	frame_size = fsize
	rng.randomize()
	sprite = Sprite3D.new()
	sprite.centered = true
	sprite.pixel_size = pixel_size
	sprite.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
	sprite.alpha_cut = SpriteBase3D.ALPHA_CUT_DISCARD
	sprite.alpha_scissor_threshold = 0.5
	sprite.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	sprite.shaded = true
	sprite.double_sided = true
	# pivot：置中後把腳底對準 origin（之後所有 clip 都經 _apply_clip_sheet）
	_base_offset = foot_offset(frame_size, pivot)
	sprite.offset = _base_offset
	add_child(sprite)
	_base_modulate = sprite.modulate
	_add_blob()
	agent = NavigationAgent3D.new()
	agent.path_desired_distance = 4.0
	agent.target_desired_distance = 6.0
	agent.avoidance_enabled = false
	agent.radius = radius
	agent.max_speed = speed
	add_child(agent)
	pause_t = rng.randf_range(0.4, 1.2)
	_add_click_area()
	_apply_frame()


func set_feet(f: Footprints) -> void:
	feet = f


func _process(dt: float) -> void:
	if frames.is_empty() or sprite == null:
		return
	if follow_target and is_instance_valid(follow_target):
		var gap := global_position.distance_to(follow_target.global_position)
		if gap > follow_dist + 2.0:
			var dest := follow_target.global_position
			if use_nav and agent:
				agent.target_position = dest
			_fallback_dest = dest
			pause_t = 0.0
	if pause_t > 0.0:
		pause_t -= dt
		moving = false
		_anim(dt)
		if pause_t <= 0.0:
			live_clip = ""
			if not brain_driven:
				_pick_target()
		return
	var dest := agent.get_next_path_position() if use_nav else _fallback_dest
	var pos := global_position
	var to := dest - pos
	to.y = 0
	if use_nav and agent.is_navigation_finished():
		moving = false
		if not brain_driven:
			pause_t = rng.randf_range(pause_min, pause_max)
			_maybe_liveliness()
		_anim(dt)
		return
	if to.length() < 1.5:
		moving = false
		if not brain_driven:
			pause_t = rng.randf_range(pause_min, pause_max)
			_maybe_liveliness()
		_anim(dt)
		return
	var step := to.normalized() * speed * maxf(speed_mul, 0.1) * dt
	if step.length() > to.length():
		step = to
	var nxt := pos + step
	if feet and feet.blocked(nxt.x, nxt.z, radius):
		# 滑過或者改目標
		_pick_target()
		moving = false
		_anim(dt)
		return
	nxt.y = 0
	global_position = nxt
	moving = true
	_update_dir(step.x, step.z)
	_anim(dt)


var _fallback_dest: Vector3 = Vector3.ZERO

func _pick_target() -> void:
	var t: Vector3
	if feet:
		t = feet.random_free(rng, radius)
	else:
		t = Vector3(rng.randf_range(-120, 120), 0, rng.randf_range(-20, 140))
	_fallback_dest = t
	if use_nav and agent:
		# nav map 可能未 bake
		agent.target_position = t
		if not agent.is_target_reachable() and not agent.is_target_reachable():
			pass


func _update_dir(dx: float, dz: float) -> void:
	if absf(dx) >= absf(dz):
		dir = "side"
		flip_x = dx < 0.0
	elif dz > 0.0:
		dir = "front"
		flip_x = false
	else:
		dir = "back"
		flip_x = false
	sprite.flip_h = flip_x


func _maybe_liveliness() -> void:
	if live_clip != "" or not (ArtImporter and ArtImporter.has_method("liveliness_idle_pool")):
		return
	if rng.randf() > 0.5:
		return
	var pool: PackedStringArray = ArtImporter.liveliness_idle_pool()
	if pool.is_empty():
		return
	var name := str(pool[rng.randi() % pool.size()])
	var arr: Array = ArtImporter.frames_of(name, body_size, character)
	if arr.is_empty():
		return
	live_clip = name
	live_frames = arr
	_live_src_size = 64.0
	if arr[0] is AtlasTexture:
		var rg: Rect2 = (arr[0] as AtlasTexture).region
		if rg.size.x > 0.0:
			_live_src_size = rg.size.x
	elif ArtImporter and ArtImporter.has_method("size_px"):
		# 無 region 就當來源係 L 64 fallback
		_live_src_size = 64.0
	live_i = 0
	live_t = 0.0
	_clip_elapsed = 0.0
	_clip_loops = 0
	_sfx_fired.clear()
	_apply_live_display(true)
	_fire_sfx(0)


func foot_offset(fs: Vector2, pv: Vector2) -> Vector2:
	# Sprite3D centered=true：把每張圖嘅腳錨對準 origin
	return Vector2(fs.x * 0.5 - pv.x, pv.y - fs.y * 0.5)


func _apply_live_display(on: bool) -> void:
	# 用該圖集自己嘅 frame size／foot pivot；世界尺吋跟角色官方體型，唔好逐 clip 轉 ×2/×3
	if sprite == null:
		return
	if on and ArtImporter:
		var rec: Dictionary = ArtImporter.clip_sheet(live_clip, body_size, character)
		var fs: Vector2 = rec.get("frame_size", Vector2(_live_src_size, _live_src_size))
		if fs.x <= 0.0:
			fs = Vector2(_live_src_size if _live_src_size > 0.0 else 64.0, _live_src_size if _live_src_size > 0.0 else 64.0)
		var pv: Vector2 = rec.get("pivot", ArtImporter.liveliness_pivot(body_size))
		if pv == Vector2.ZERO:
			pv = ArtImporter.liveliness_pivot(body_size)
		var official := ArtImporter.size_px(body_size)
		if official <= 0.0:
			official = frame_size.x if frame_size.x > 0.0 else 64.0
		sprite.pixel_size = official / fs.x * _base_pixel_size
		_base_offset = foot_offset(fs, pv)
	else:
		sprite.pixel_size = pixel_size
		_base_offset = foot_offset(frame_size, pivot)
	sprite.offset = _base_offset


func _fire_sfx(frame_index: int) -> void:
	# 讀正式 t_ms／sfx_hook／frameIndex，同草稿 frame（1-based）
	if live_clip == "" or ArtImporter == null:
		return
	for cue in ArtImporter.sfx_cues(live_clip):
		if not (cue is Dictionary):
			continue
		var hook = cue.get("sfx_hook", cue.get("hook", null))
		var id := str(cue.get("id", ""))
		var key := str(hook) if hook != null else id
		if key == "" or _sfx_fired.get(key, false):
			continue
		var fi := int(cue.get("frameIndex", -1))
		var fr := int(cue.get("frame", 0))
		var tms := int(cue.get("t_ms", cue.get("time_ms", -1)))
		var hit := false
		if fi >= 0 and fi == frame_index:
			hit = true
		elif fr > 0 and fr == frame_index + 1:
			hit = true
		elif tms >= 0 and _clip_elapsed * 1000.0 + 0.5 >= float(tms):
			hit = true
		if not hit:
			continue
		var every_n := int(cue.get("every_n_loops", 1))
		if every_n > 1 and (_clip_loops % every_n) != 0:
			continue
		if bool(cue.get("on_enter", false)) and _clip_loops > 0:
			continue
		_sfx_fired[key] = true
		# hook 係 null → 靜音（仍然 emit 方便測試）
		var hook_s := "" if hook == null else str(hook)
		# 只 emit；AudioManager 已 connect sfx_cue，避免播兩次
		ArtImporter.sfx_cue.emit(live_clip, hook_s, frame_index, self)


func _anim(dt: float) -> void:
	if live_clip != "" and live_frames.size():
		if dt > 0.0:
			live_t += dt
			_clip_elapsed += dt
			var step := ArtImporter.frame_duration_sec(live_clip, live_i)
			while live_t >= step and live_clip != "":
				live_t -= step
				live_i += 1
				if live_i >= live_frames.size():
					var loop := bool(ArtImporter.clip_timing(live_clip).get("loop", false))
					if loop:
						live_i = 0
						_clip_elapsed = 0.0
						_clip_loops += 1
						var keep: Dictionary = {}
						for cue2 in ArtImporter.sfx_cues(live_clip):
							if not (cue2 is Dictionary):
								continue
							if bool(cue2.get("on_enter", false)):
								var hk = cue2.get("sfx_hook", cue2.get("hook", null))
								var kk := str(hk) if hk != null else str(cue2.get("id", ""))
								if kk != "" and bool(_sfx_fired.get(kk, false)):
									keep[kk] = true
						_sfx_fired = keep
					else:
						live_clip = ""
						live_i = 0
						_apply_live_display(false)
						break
				if live_clip != "":
					_fire_sfx(live_i)
					step = ArtImporter.frame_duration_sec(live_clip, live_i)
		if live_clip != "" and live_i < live_frames.size():
			sprite.texture = live_frames[live_i]
			return
	var clip := dir + ("_walk" if moving else "_idle")
	var arr: Array = frames.get(clip, frames.get("front_idle", []))
	if arr.is_empty():
		return
	# 行路 fps 用呢隻 Walker 自己嘅 walk_fps／idle_fps（由 data 讀），唔好用團絨 walk_happy 蓋過
	var fps := walk_fps if moving else idle_fps
	var prev_i := frame_i
	frame_t += dt
	var step_t := 1.0 / maxf(fps, 0.1)
	if frame_t >= step_t:
		frame_t = fmod(frame_t, step_t)
		frame_i = (frame_i + 1) % arr.size()
	frame_i = frame_i % arr.size()
	if sprite.texture != arr[frame_i]:
		sprite.texture = arr[frame_i]
	_step_cool = maxf(0.0, _step_cool - dt)
	if moving and frame_i != prev_i:
		_maybe_footstep(arr.size())

	_apply_walk_bob(dt)

func _maybe_footstep(nframes: int) -> void:
	# 落地點：6 幀用 0／3，其他對半。心情揀 hop／drag／plod；步距 ≥0.45 s。
	if _step_cool > 0.0:
		return
	var land2 := 3 if nframes >= 6 else maxi(1, nframes / 2)
	if frame_i != 0 and frame_i != land2:
		return
	var hook := "sfx_pet_step_hop_a"
	if Sim and Sim.state:
		var needs: Dictionary = Sim.state.get("needs", {})
		var mood := float(needs.get("mood", 70))
		var energy := float(needs.get("energy", 70))
		if mood < 40.0:
			hook = "sfx_pet_step_drag_a"
		elif energy < 55.0:
			hook = "sfx_pet_step_plod_a"
		else:
			hook = "sfx_pet_step_hop_a"
	_step_cool = 0.45
	# 只 emit；AudioManager 已 connect sfx_cue，避免播兩次（同 _fire_sfx）
	if ArtImporter:
		ArtImporter.sfx_cue.emit("walk", hook, frame_i, self)


func _apply_frame() -> void:
	frame_i = 0
	_anim(0.0)

func current_anim_fps() -> float:
	# 俾測試核對：行路用呢隻自己嘅 walk_fps，唔會被團絨 walk_happy 蓋過
	return walk_fps if moving else idle_fps


func park() -> void:
	# 截圖用：停行、停生命感，企定喺而家位置
	pause_t = 1.0e9
	moving = false
	live_clip = ""
	live_frames = []
	_apply_live_display(false)
	use_nav = false
	if agent:
		agent.target_position = global_position
	frame_i = 0
	frame_t = 0.0
	_anim(0.0)


func set_base_modulate(c: Color) -> void:
	_base_modulate = c
	_refresh_modulate()


func apply_tod_modulate(tint: Color) -> void:
	_tod_modulate = tint
	_refresh_modulate()


func apply_billboard_quality(low: bool) -> void:
	# 低檔 0.67 縮放＋受光 billboard 會把日間團絨洗白；低檔改 unshaded、保持 nearest 無 mip。
	# unshaded 唔受夜光，要另乘時段 modulate，以免夜間仍然全日色。
	if sprite == null:
		return
	_low_unshaded = low
	sprite.shaded = not low
	sprite.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	_refresh_modulate()


func _refresh_modulate() -> void:
	if sprite == null:
		return
	if _low_unshaded:
		sprite.modulate = _base_modulate * _tod_modulate
	else:
		sprite.modulate = _base_modulate


func _add_blob() -> void:
	# 低成本腳底圓影（唔用實心方塊；低檔唔開 shadow map 都靠呢個）
	var img := Image.create(64, 64, false, Image.FORMAT_RGBA8)
	var c := Vector2(31.5, 31.5)
	for y in range(64):
		for x in range(64):
			var nx := (float(x) - c.x) / 30.0
			var ny := (float(y) - c.y) / 22.0
			var d := sqrt(nx * nx + ny * ny)
			var a := clampf(1.0 - d, 0.0, 1.0)
			a = a * a * 0.5
			img.set_pixel(x, y, Color(0, 0, 0, a))
	var tex := ImageTexture.create_from_image(img)
	var blob := MeshInstance3D.new()
	blob.name = "BlobShadow"
	var q := QuadMesh.new()
	q.size = Vector2(radius * 2.4, radius * 1.5)
	blob.mesh = q
	blob.rotation_degrees.x = -90
	blob.position = Vector3(0, 0.08, 0.05)
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.albedo_texture = tex
	mat.albedo_color = Color(1, 1, 1, 1)
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR
	blob.material_override = mat
	blob.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(blob)


func _add_click_area() -> void:
	click_area = Area3D.new()
	click_area.name = "Click"
	click_area.input_ray_pickable = true
	click_area.collision_layer = 4
	click_area.collision_mask = 0
	var cs := CollisionShape3D.new()
	var sh := SphereShape3D.new()
	sh.radius = maxf(radius, 14.0)
	cs.shape = sh
	cs.position = Vector3(0, maxf(radius, 14.0), 0)
	click_area.add_child(cs)
	add_child(click_area)


func play_live_clip(name: String, loop: bool = false) -> bool:
	if name == "" or ArtImporter == null:
		return false
	var arr: Array = ArtImporter.frames_of(name, body_size, character)
	if arr.is_empty():
		arr = ArtImporter.frames_of(name + "_noface", body_size)
	if arr.is_empty():
		arr = ArtImporter.frames_of(name, "")
	if arr.is_empty():
		return false
	live_clip = name
	live_frames = arr
	_live_src_size = 64.0
	if arr[0] is AtlasTexture:
		var rg: Rect2 = (arr[0] as AtlasTexture).region
		if rg.size.x > 0.0:
			_live_src_size = rg.size.x
	live_i = 0
	live_t = 0.0
	_clip_elapsed = 0.0
	_clip_loops = 0
	_sfx_fired.clear()
	_apply_live_display(true)
	_fire_sfx(0)
	# 非循環會喺播完自己清；強制 loop 時等呼叫者停
	if loop and ArtImporter and ArtImporter.has_method("clip_timing"):
		pass
	return true


func cancel_move() -> void:
	moving = false
	follow_target = null
	pause_t = 0.0
	if agent:
		agent.target_position = global_position
	_fallback_dest = global_position


func cancel_follow() -> void:
	follow_target = null


func stop_live() -> void:
	live_clip = ""
	_apply_live_display(false)


func go_to(dest: Vector3) -> void:
	dest.y = 0
	pause_t = 0.0
	_fallback_dest = dest
	if use_nav and agent:
		agent.target_position = dest


func pick_nearby(radius_u: float = 70.0) -> void:
	var t: Vector3
	if feet:
		t = feet.random_free(rng, radius)
		# 限制距離
		var d := t - global_position
		d.y = 0
		if d.length() > radius_u and d.length() > 0.01:
			t = global_position + d.normalized() * radius_u
			t.y = 0
	else:
		var ang := rng.randf() * TAU
		t = global_position + Vector3(cos(ang), 0, sin(ang)) * rng.randf_range(20.0, radius_u)
	go_to(t)


func follow_node(n: Node3D, dist: float = 16.0) -> void:
	follow_target = n
	follow_dist = dist
	pause_t = 0.0
	if n and is_instance_valid(n):
		go_to(n.global_position)


func try_liveliness() -> void:
	_maybe_liveliness()


func world_height() -> float:
	# 腳底到頭頂嘅世界高度（1 texel＝pixel_size 世界單位）——廣告牌框，唔係可見像素
	return frame_size.y * maxf(pixel_size, 0.001)


func _apply_walk_bob(dt: float) -> void:
	# 彈跳只加喺腳錨 offset 上面，停步唔好把 offset 清成 0（否則半個身體沒入地）
	if sprite == null:
		return
	var bob := 0.0
	if walk_bob and moving:
		_bob_t += dt
		bob = sin(_bob_t * TAU * 5.0) * 3.0
	else:
		_bob_t = 0.0
	sprite.offset = _base_offset + Vector2(0.0, bob)


func _scan_visible(tex: Texture2D) -> void:
	# 非透明像素嘅頂／底（圖框座標，y 向下）
	_vis_ok = false
	_vis_tex = tex
	_vis_top = 0.0
	_vis_bot = frame_size.y if frame_size.y > 0.0 else 64.0
	if tex == null:
		return
	var img: Image = null
	var region := Rect2(0, 0, 0, 0)
	if tex is AtlasTexture:
		var at := tex as AtlasTexture
		region = at.region
		if at.atlas:
			img = at.atlas.get_image()
	else:
		img = tex.get_image()
		region = Rect2(0, 0, tex.get_width(), tex.get_height())
	if img == null or region.size.x < 1.0 or region.size.y < 1.0:
		# headless 或者壓縮紋理讀唔到時：用框高 60% 估算（遊策量到可見約六成）
		_vis_top = _vis_bot * 0.08
		_vis_bot = _vis_bot * 0.92
		_vis_ok = true
		return
	var x0 := int(region.position.x)
	var y0 := int(region.position.y)
	var w := int(region.size.x)
	var h := int(region.size.y)
	var top := h
	var bot := -1
	for y in range(h):
		var hit := false
		for x in range(w):
			var px := img.get_pixel(x0 + x, y0 + y)
			if px.a > 0.12:
				hit = true
				break
		if hit:
			if y < top:
				top = y
			if y > bot:
				bot = y
	if bot < 0 or top > bot:
		_vis_top = h * 0.08
		_vis_bot = h * 0.92
	else:
		_vis_top = float(top)
		_vis_bot = float(bot)
	_vis_ok = true


func visible_bounds_px() -> Vector2:
	var tex: Texture2D = sprite.texture if sprite else null
	if tex != _vis_tex or not _vis_ok:
		_scan_visible(tex)
	return Vector2(_vis_top, _vis_bot)


func visible_world_top() -> float:
	# 由腳錨（pivot.y）上到可見頂
	var b := visible_bounds_px()
	return maxf(4.0, (pivot.y - b.x) * maxf(pixel_size, 0.001))


func visible_world_bottom() -> float:
	# 可見底相對腳錨（可能略低於 0）
	var b := visible_bounds_px()
	return (pivot.y - b.y) * maxf(pixel_size, 0.001)


func visible_world_height() -> float:
	return maxf(4.0, visible_world_top() - visible_world_bottom())

