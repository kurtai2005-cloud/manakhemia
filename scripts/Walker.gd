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

func setup(tex_frames: Dictionary, p_size: float, pvt: Vector2, fsize: Vector2) -> void:
	frames = tex_frames
	pixel_size = p_size
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
	# pivot：置中後把腳底對準 origin
	sprite.offset = Vector2(frame_size.x * 0.5 - pivot.x, pivot.y - frame_size.y * 0.5)
	add_child(sprite)
	_add_blob()
	agent = NavigationAgent3D.new()
	agent.path_desired_distance = 4.0
	agent.target_desired_distance = 6.0
	agent.avoidance_enabled = false
	agent.radius = radius
	agent.max_speed = speed
	add_child(agent)
	pause_t = rng.randf_range(0.4, 1.2)
	_apply_frame()


func set_feet(f: Footprints) -> void:
	feet = f


func _process(dt: float) -> void:
	if frames.is_empty() or sprite == null:
		return
	if pause_t > 0.0:
		pause_t -= dt
		moving = false
		_anim(dt)
		if pause_t <= 0.0:
			_pick_target()
		return
	var dest := agent.get_next_path_position() if use_nav else _fallback_dest
	var pos := global_position
	var to := dest - pos
	to.y = 0
	if use_nav and agent.is_navigation_finished():
		moving = false
		pause_t = rng.randf_range(pause_min, pause_max)
		_anim(dt)
		return
	if to.length() < 1.5:
		moving = false
		pause_t = rng.randf_range(pause_min, pause_max)
		_anim(dt)
		return
	var step := to.normalized() * speed * dt
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


func _anim(dt: float) -> void:
	var clip := dir + ("_walk" if moving else "_idle")
	var arr: Array = frames.get(clip, frames.get("front_idle", []))
	if arr.is_empty():
		return
	var fps := walk_fps if moving else idle_fps
	frame_t += dt
	var step_t := 1.0 / maxf(fps, 0.1)
	if frame_t >= step_t:
		frame_t = fmod(frame_t, step_t)
		frame_i = (frame_i + 1) % arr.size()
	if sprite.texture != arr[frame_i]:
		sprite.texture = arr[frame_i]


func _apply_frame() -> void:
	frame_i = 0
	_anim(0.0)

func _add_blob() -> void:
	# 低成本腳底影（低畫質唔開 shadow map 都用呢個；唔替代 3D 遮擋）
	var blob := MeshInstance3D.new()
	blob.name = "BlobShadow"
	var q := QuadMesh.new()
	q.size = Vector2(radius * 1.8, radius * 1.1)
	blob.mesh = q
	blob.rotation_degrees.x = -90
	blob.position = Vector3(0, 0.08, 0.4)
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.albedo_color = Color(0, 0, 0, 0.28)
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	blob.material_override = mat
	blob.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(blob)
