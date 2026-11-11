extends Node3D
## G0 主場景：3D 花園、自主行寵物／細佬、執屎、最簡 HUD。

const H1 := "res://art/garden3d/H1/"
const DIR4 := "res://art/garden3d/dir4/"
const PET_RADIUS := 10.0
const KID_RADIUS := 8.0

var cam: Camera3D
var cam_data: Dictionary = {}
var feet := Footprints.new()
var pet: Walker
var kid: Walker
var visitor: Walker
var poop_root: Node3D
var sun: DirectionalLight3D
var fill: DirectionalLight3D
var env: WorldEnvironment
var hud: CanvasLayer
var nav_region: NavigationRegion3D
var cam_target := Vector3(0, 30, -72)
var follow_pos := Vector3(0, 30, -72)
var sway_t := 0.0
var rng := RandomNumberGenerator.new()
var show_visitor := true

func _ready() -> void:
	rng.randomize()
	var objs_doc := GardenLoader.load_json(H1 + "objects.json")
	cam_data = GardenLoader.load_json(H1 + "camera.json")
	var lights := GardenLoader.load_json(H1 + "lights.json")
	var objects: Array = objs_doc.get("objects", [])
	feet.load_from_objects(objects)
	_build_world(objs_doc, objects, lights)
	_build_nav()
	_spawn_actors()
	_sync_poops()
	hud = preload("res://scripts/Hud.gd").new()
	add_child(hud)
	QualitySettings.changed.connect(_on_quality)
	_on_quality(QualitySettings.tier)
	Sim.poops_changed.connect(func(_n): _sync_poops())
	# 第一次進，如果未有便便，放一粒方便 G0 驗「可撳執」
	if int(Sim.state.get("poops", 0)) == 0:
		Sim.add_poop()


func _build_world(objs_doc: Dictionary, objects: Array, lights: Dictionary) -> void:
	# 外圍草地 tile
	var tile_tex: Texture2D = load(H1 + "ground/ground_tile.png")
	var tile_mat := GardenLoader.make_mat(tile_tex, false, 0.0)
	tile_mat.transparency = BaseMaterial3D.TRANSPARENCY_DISABLED
	tile_mat.texture_repeat = true
	tile_mat.uv1_scale = Vector3(20, 12.5, 1)  # 1280/64 × 800/64
	var tile_mi := MeshInstance3D.new()
	tile_mi.mesh = GardenLoader.ground_mesh(1280, 1.0, false)
	# 覆蓋 x±640、z −480…+320 → 中心大約 z=-80，改用手動位移
	tile_mi.position = Vector3(0, -0.4, -80)
	# 重做正確覆蓋
	tile_mi.mesh = _rect_ground(-640, 640, -480, 320, 64.0)
	tile_mi.position = Vector3.ZERO
	tile_mi.material_override = tile_mat
	tile_mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(tile_mi)

	# 中心 256 地面＋AO
	var gtex: Texture2D = load(H1 + "ground/ground.png")
	var gmat := GardenLoader.make_mat(gtex, false, 0.0)
	gmat.transparency = BaseMaterial3D.TRANSPARENCY_DISABLED
	var ao: Texture2D = load(H1 + "ground/ground_ao.png")
	var gmi := MeshInstance3D.new()
	gmi.mesh = _rect_ground(-128, 128, -128, 128, 256.0)
	gmi.position.y = 0.05
	gmi.material_override = gmat
	gmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(gmi)
	if ao:
		var aomat := StandardMaterial3D.new()
		aomat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		aomat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		aomat.albedo_texture = ao
		aomat.albedo_color = Color(1, 1, 1, 0.55)
		aomat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
		aomat.texture_repeat = false
		aomat.blend_mode = BaseMaterial3D.BLEND_MODE_MUL
		var ami := MeshInstance3D.new()
		ami.mesh = gmi.mesh
		ami.position.y = 0.06
		ami.material_override = aomat
		ami.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(ami)

	# 背景板
	for o in objects:
		if str(o.get("type", "")) != "backdrop":
			continue
		var w := float(o.get("w", 100))
		var h := float(o.get("h", 50))
		var f := H1 + str(o.get("file", ""))
		var btex: Texture2D = load(f)
		var bmat := GardenLoader.make_mat(btex, true, 0.01)
		bmat.transparency = BaseMaterial3D.TRANSPARENCY_DISABLED
		if btex and str(o.get("id", "")).find("sky") >= 0:
			bmat.transparency = BaseMaterial3D.TRANSPARENCY_DISABLED
		elif btex:
			bmat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
			bmat.alpha_scissor_threshold = 0.5
		var bmi := MeshInstance3D.new()
		bmi.mesh = GardenLoader.backdrop_mesh(w, h)
		bmi.material_override = bmat
		bmi.position = Vector3(float(o.get("x", 0)), 0, float(o.get("z", 0)))
		bmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(bmi)

	# mesh 物件
	for o in objects:
		if str(o.get("type", "")) != "mesh":
			continue
		var rel := str(o.get("mesh", ""))
		var doc := GardenLoader.load_json(H1 + rel)
		if doc.is_empty():
			continue
		var tex_rel := str(doc.get("texture", ""))
		var tex: Texture2D = load(H1 + tex_rel) if tex_rel != "" else null
		var em: Texture2D = null
		# 發光圖：同路徑加 _emissive
		var em_guess := tex_rel.replace(".png", "_emissive.png")
		if ResourceLoader.exists(H1 + em_guess):
			em = load(H1 + em_guess)
		var unlit := false
		var mat := GardenLoader.make_mat(tex, unlit, float(doc.get("alphaTest", 0.5)), em)
		var mi := MeshInstance3D.new()
		mi.mesh = GardenLoader.mesh_from_json(doc, true)
		mi.material_override = mat
		mi.position = Vector3(float(o.get("x", 0)), float(o.get("y", 0)), float(o.get("z", 0)))
		mi.rotation_degrees.y = float(o.get("yawDeg", 0))
		if not bool(o.get("castShadow", true)):
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(mi)

	# 光
	var sun_d: Dictionary = lights.get("sun", {})
	sun = DirectionalLight3D.new()
	sun.light_color = GardenLoader.hex_color(str(sun_d.get("color", "#ffe6b8")))
	sun.light_energy = float(sun_d.get("intensity", 1.0))
	sun.shadow_enabled = false
	sun.directional_shadow_max_distance = 800
	sun.light_angular_distance = 2.0
	sun.shadow_opacity = float(sun_d.get("shadowIntensity", 0.3))
	var sdir: Array = sun_d.get("dir", [0.42, -0.72, 0.55])
	var travel := Vector3(float(sdir[0]), float(sdir[1]), float(sdir[2])).normalized()
	sun.position = -travel * 800.0
	add_child(sun)
	sun.look_at(Vector3.ZERO)
	var fill_d: Dictionary = lights.get("fill", {})
	fill = DirectionalLight3D.new()
	fill.light_color = GardenLoader.hex_color(str(fill_d.get("color", "#ffe2c4")))
	fill.light_energy = float(fill_d.get("intensity", 0.38))
	fill.shadow_enabled = false
	var fdir: Array = fill_d.get("dir", [0.2, -0.12, -0.97])
	var ftravel := Vector3(float(fdir[0]), float(fdir[1]), float(fdir[2])).normalized()
	fill.position = -ftravel * 800.0
	add_child(fill)
	fill.look_at(Vector3.ZERO)
	var amb: Dictionary = sun_d.get("ambient", {})
	env = WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = GardenLoader.hex_color(str((lights.get("fog", {}) as Dictionary).get("color", "#ffe8c8")))
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = GardenLoader.hex_color(str(amb.get("color", "#cfe0f0")))
	e.ambient_light_energy = float(amb.get("intensity", 0.55))
	e.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	e.glow_enabled = false
	e.ssao_enabled = false
	e.ssil_enabled = false
	e.sdfgi_enabled = false
	e.adjustment_enabled = false
	# fog cheap on mid/high only
	e.fog_enabled = false
	env.environment = e
	add_child(env)

	# 相機
	cam = Camera3D.new()
	cam.projection = Camera3D.PROJECTION_PERSPECTIVE
	cam.fov = float(cam_data.get("fovDeg", 40))
	cam.near = float(cam_data.get("near", 10))
	cam.far = float(cam_data.get("far", 4000))
	cam.current = true
	add_child(cam)
	cam_target = Vector3(float(cam_data.get("target", [0, 30, -72])[0]), float(cam_data.get("target", [0, 30, -72])[1]), float(cam_data.get("target", [0, 30, -72])[2]))
	follow_pos = cam_target
	_place_cam(0.0)


func _rect_ground(x0: float, x1: float, z0: float, z1: float, uv_unit: float) -> ArrayMesh:
	var verts := PackedVector3Array([
		Vector3(x0, 0, z0), Vector3(x1, 0, z0), Vector3(x1, 0, z1), Vector3(x0, 0, z1)
	])
	var nrm := PackedVector3Array([Vector3.UP, Vector3.UP, Vector3.UP, Vector3.UP])
	# 圖頂 = z 較細（遠）。Godot UV (0,0) = 貼圖左上。
	var u0 := x0 / uv_unit
	var u1 := x1 / uv_unit
	# z0=-128 → v=0（圖頂）；對中心地面 uv_unit=256，(z+128)/256
	var v0 := z0 / uv_unit
	var v1 := z1 / uv_unit
	# 為 256 地面：u=(x+128)/256 即 x0=-128 → 0。所以用 (x-x_origin)/size，origin = -half
	# 呢度 uv_unit 係「一張圖覆蓋幾多 unit」，以 (0,0) 對 tile 用 x/64。
	# 中心地面想 u=(x+128)/256 → x0=-128, uv_unit=256 → u=x/256 + 0.5。改做明確計算：
	var uv := PackedVector2Array([
		Vector2(u0, v0), Vector2(u1, v0), Vector2(u1, v1), Vector2(u0, v1)
	])
	if absf(uv_unit - 256.0) < 0.1:
		uv = PackedVector2Array([
			Vector2((x0 + 128.0) / 256.0, (z0 + 128.0) / 256.0),
			Vector2((x1 + 128.0) / 256.0, (z0 + 128.0) / 256.0),
			Vector2((x1 + 128.0) / 256.0, (z1 + 128.0) / 256.0),
			Vector2((x0 + 128.0) / 256.0, (z1 + 128.0) / 256.0),
		])
	var idx := PackedInt32Array([0, 2, 1, 0, 3, 2])
	var arrays: Array = []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = verts
	arrays[Mesh.ARRAY_NORMAL] = nrm
	arrays[Mesh.ARRAY_TEX_UV] = uv
	arrays[Mesh.ARRAY_INDEX] = idx
	var am := ArrayMesh.new()
	am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	return am


func _build_nav() -> void:
	nav_region = NavigationRegion3D.new()
	add_child(nav_region)
	var nm := NavigationMesh.new()
	nm.agent_radius = 12.0
	nm.agent_height = 2.0
	nm.agent_max_climb = 2.0
	nm.agent_max_slope = 45.0
	nm.cell_size = 4.0
	nm.cell_height = 1.0
	nm.border_size = 4.0
	var src := NavigationMeshSourceGeometryData3D.new()
	# 可行走地面（籬笆前）
	var x0 := -180.0
	var x1 := 180.0
	var z0 := -40.0
	var z1 := 200.0
	var faces := PackedVector3Array([
		Vector3(x0, 0, z0), Vector3(x1, 0, z1), Vector3(x1, 0, z0),
		Vector3(x0, 0, z0), Vector3(x0, 0, z1), Vector3(x1, 0, z1),
	])
	src.add_faces(faces, Transform3D.IDENTITY)
	for r in feet.rects:
		var verts := PackedVector3Array([
			Vector3(r["x0"], 0, r["z0"]), Vector3(r["x1"], 0, r["z0"]),
			Vector3(r["x1"], 0, r["z1"]), Vector3(r["x0"], 0, r["z1"]),
		])
		src.add_projected_obstruction(verts, -1.0, 40.0, true)
	for p in feet.polys:
		var pts: PackedVector2Array = p["pts"]
		var verts2 := PackedVector3Array()
		for pt in pts:
			verts2.append(Vector3(pt.x, 0, pt.y))
		src.add_projected_obstruction(verts2, -1.0, 40.0, true)
	NavigationServer3D.bake_from_source_geometry_data(nm, src)
	nav_region.navigation_mesh = nm


func _spawn_actors() -> void:
	poop_root = Node3D.new()
	poop_root.name = "Poops"
	add_child(poop_root)
	pet = Walker.new()
	pet.name = "Pet"
	pet.radius = PET_RADIUS
	pet.speed = 20.0
	add_child(pet)
	pet.position = Vector3(0, 0, 0)
	pet.set_feet(feet)
	pet.setup(_load_dir4(), 1.0, Vector2(32, 61), Vector2(64, 64))
	# 細佬：正面條，1px=1unit，48 框
	kid = Walker.new()
	kid.name = "Kid"
	kid.radius = KID_RADIUS
	kid.speed = 16.0
	kid.idle_fps = 4.0
	kid.walk_fps = 8.0
	add_child(kid)
	kid.position = Vector3(40, 0, 50)
	kid.set_feet(feet)
	kid.setup(_load_strip("res://art/kid/A1_idle.png", 48, 48, 4, "idle", "res://art/kid/A1_walk.png", 6), 1.0, Vector2(24, 46), Vector2(48, 48))
	if show_visitor:
		visitor = Walker.new()
		visitor.name = "Visitor"
		visitor.radius = KID_RADIUS
		visitor.speed = 14.0
		add_child(visitor)
		visitor.position = Vector3(-50, 0, 80)
		visitor.set_feet(feet)
		visitor.setup(_load_strip("res://art/kid/A1_idle.png", 48, 48, 4, "idle", "res://art/kid/A1_walk.png", 6), 1.0, Vector2(24, 46), Vector2(48, 48))
		if visitor.sprite:
			visitor.sprite.modulate = Color(0.85, 0.78, 1.15)


func _load_dir4() -> Dictionary:
	var doc := GardenLoader.load_json(DIR4 + "atlas_radiant_dir4.json")
	var atlas: Texture2D = load(DIR4 + "atlas_radiant_dir4.png")
	var out := {}
	var frames: Dictionary = doc.get("frames", {})
	for name in frames.keys():
		var info: Dictionary = frames[name]
		var fr: Dictionary = info.get("frame", {})
		var at := AtlasTexture.new()
		at.atlas = atlas
		at.region = Rect2(float(fr.get("x", 0)), float(fr.get("y", 0)), float(fr.get("w", 64)), float(fr.get("h", 64)))
		at.filter_clip = true
		var clip := str(name).substr(0, name.rfind("_"))  # front_idle_01 → front_idle
		# names like front_idle_01 — rfind last _
		if not out.has(clip):
			out[clip] = []
		out[clip].append(at)
	return out


func _load_strip(idle_path: String, fw: int, fh: int, n_idle: int, _k: String, walk_path: String, n_walk: int) -> Dictionary:
	var idle: Texture2D = load(idle_path)
	var walk: Texture2D = load(walk_path)
	var mk := func(tex: Texture2D, n: int) -> Array:
		var a: Array = []
		for i in range(n):
			var at := AtlasTexture.new()
			at.atlas = tex
			at.region = Rect2(i * fw, 0, fw, fh)
			at.filter_clip = true
			a.append(at)
		return a
	var idles: Array = mk.call(idle, n_idle)
	var walks: Array = mk.call(walk, n_walk)
	return {
		"front_idle": idles, "back_idle": idles, "side_idle": idles,
		"front_walk": walks, "back_walk": walks, "side_walk": walks,
	}


func _sync_poops() -> void:
	if poop_root == null:
		return
	var want := int(Sim.state.get("poops", 0))
	while poop_root.get_child_count() > want:
		poop_root.get_child(poop_root.get_child_count() - 1).queue_free()
		# queue_free 唔即減 child count；改用立即 free
	# 清晒重建最穩
	for c in poop_root.get_children():
		c.free()
	var tex: Texture2D = load("res://art/sprites/poop.png")
	for i in range(want):
		var n := Area3D.new()
		n.name = "Poop_%d" % i
		var spr := Sprite3D.new()
		spr.texture = tex
		spr.pixel_size = 1.0
		spr.centered = true
		spr.offset = Vector2(0, 6)
		spr.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
		spr.alpha_cut = SpriteBase3D.ALPHA_CUT_DISCARD
		spr.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
		spr.pixel_size = 1.2
		n.add_child(spr)
		var cs := CollisionShape3D.new()
		var sh := SphereShape3D.new()
		sh.radius = 12.0
		cs.shape = sh
		n.add_child(cs)
		n.input_ray_pickable = true
		n.collision_layer = 2
		n.collision_mask = 0
		n.position = feet.random_free(rng, 8.0, -80, 80, 10, 90)
		n.input_event.connect(_on_poop_input.bind(n))
		poop_root.add_child(n)


func _on_poop_input(_cam: Node, event: InputEvent, _pos: Vector3, _normal: Vector3, _shape: int, node: Area3D) -> void:
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.pressed and mb.button_index == MOUSE_BUTTON_LEFT:
			_clean_poop(node)
	elif event is InputEventScreenTouch:
		var st := event as InputEventScreenTouch
		if st.pressed:
			_clean_poop(node)


func _clean_poop(node: Area3D) -> void:
	if node and is_instance_valid(node):
		Sim.clean_one()


func _on_quality(tier: int) -> void:
	var low := tier == QualitySettings.Tier.LOW
	var mid := tier == QualitySettings.Tier.MID
	if sun:
		sun.shadow_enabled = not low
		sun.directional_shadow_mode = DirectionalLight3D.SHADOW_ORTHOGONAL
		sun.light_energy = 1.0 if not (tier == QualitySettings.Tier.HIGH) else 1.1
	if env and env.environment:
		var e := env.environment
		e.glow_enabled = tier == QualitySettings.Tier.HIGH
		e.glow_intensity = 0.4
		e.fog_enabled = not low
		if not low:
			e.fog_light_color = e.background_color
			e.fog_density = 0.0004
		# DoF 只 high
		e.background_mode = Environment.BG_COLOR
	# 低畫質唔開 MSAA；mid/high 都保持 compatibility 便宜
	get_viewport().msaa_3d = Viewport.MSAA_DISABLED
	if fill:
		fill.visible = true
		fill.light_energy = 0.2 if low else 0.38


func _place_cam(dt: float) -> void:
	if cam == null:
		return
	var A := float(cam_data.get("swayAmplitudeDeg", 5))
	var T := float(cam_data.get("swayHalfPeriodSec", 6))
	sway_t += dt
	var yaw := -A * cos(PI * sway_t / maxf(T, 0.1))
	var pitch := float(cam_data.get("pitchDeg", 30))
	var dist := float(cam_data.get("dist", 580))
	# follow
	var pet_pos := pet.global_position if pet else Vector3.ZERO
	var fw: Array = cam_data.get("followWeight", [0.25, 0.3])
	var fo: Array = cam_data.get("followOffset", [-20, 0])
	var origin: Array = cam_data.get("followOrigin", [-110, -40])
	var desired := cam_target + Vector3(
		float(fo[0]) + float(fw[0]) * (pet_pos.x - float(origin[0])),
		0,
		float(fo[1]) + float(fw[1]) * (pet_pos.z - float(origin[1]))
	)
	var damp := float(cam_data.get("followDamping", 2.0))
	if dt > 0.0:
		var k := 1.0 - exp(-damp * dt)
		follow_pos = follow_pos.lerp(desired, k)
	else:
		follow_pos = desired
	# 相機喺 target 後面：pitch 向下、yaw 繞 Y
	var rad_pitch := deg_to_rad(pitch)
	var rad_yaw := deg_to_rad(yaw)
	# 面向 -Z 為 0 yaw（+Z 向鏡頭，即鏡頭喺 +Z 一側望向 -Z）
	var offset := Vector3(0, 0, dist)
	offset = offset.rotated(Vector3.RIGHT, -rad_pitch)
	offset = offset.rotated(Vector3.UP, rad_yaw)
	cam.global_position = follow_pos + offset
	cam.look_at(follow_pos)


func _process(dt: float) -> void:
	_place_cam(dt)


func _unhandled_input(event: InputEvent) -> void:
	# 備用：ray 撳屎（萬一 Area 收唔到）
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.pressed and mb.button_index == MOUSE_BUTTON_LEFT:
			_try_tap(mb.position)
	elif event is InputEventScreenTouch:
		var st := event as InputEventScreenTouch
		if st.pressed:
			_try_tap(st.position)


func _try_tap(pos: Vector2) -> void:
	if cam == null:
		return
	var from := cam.project_ray_origin(pos)
	var dir := cam.project_ray_normal(pos)
	var to := from + dir * 4000.0
	var q := PhysicsRayQueryParameters3D.create(from, to)
	q.collide_with_areas = true
	q.collide_with_bodies = false
	q.collision_mask = 2
	var hit := get_world_3d().direct_space_state.intersect_ray(q)
	if hit and hit.get("collider") is Area3D:
		_clean_poop(hit["collider"])
