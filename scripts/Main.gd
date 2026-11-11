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
var rest_look := false  # 截圖／對位：停 sway、follow 固定喺 camera.json target
var _sky_w := 1634.3
var _ground_mats: Array = []
var _tod := "day"
var follow_pos := Vector3(0, 30, -72)
var sway_t := 0.0
var rng := RandomNumberGenerator.new()
var show_visitor := true
var _emissive_mats: Array = []
var _sky_mat: ProceduralSkyMaterial
var _day_ambient := Color(0.81, 0.88, 0.94)
var _hills_mats: Array = []
var _omni_lights: Array = []  # {node, data}
var _luts: Dictionary = {}
var _obs_pitch := 0.0

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
	follow_device_clock()
	Sim.poops_changed.connect(func(_n): _sync_poops())
	# 第一次進，如果未有便便，放一粒方便 G0 驗「可撳執」
	if int(Sim.state.get("poops", 0)) == 0:
		Sim.add_poop()


func _build_world(objs_doc: Dictionary, objects: Array, lights: Dictionary) -> void:
	# 外圍草地（對齊 H1：以 (−128,−128) 起每 64u 一格；鋪到地平，望唔到米色清屏）
	# 貼圖本身冇烘光，用 unshaded + 關 cull，避免 ArrayMesh／背臉被裁走。
	var tile_tex: Texture2D = load(H1 + "ground/ground_tile.png")
	var tile_mat := GardenLoader.opaque_tex_mat(tile_tex, true, true, true)
	_ground_mats.append(tile_mat)
	var tile_mi := MeshInstance3D.new()
	tile_mi.name = "GroundTile"
	# FORMAT：畫面大約望到 z −1250…+240；再加大保證地平全係草
	tile_mi.mesh = GardenLoader.xz_plane(-960, 960, -1600, 480, Vector2(-128, -128), 64.0)
	tile_mi.material_override = tile_mat
	tile_mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(tile_mi)

	# 中心 256 地面（路徑／泥面／花圃貼圖）＋ AO
	var gtex: Texture2D = load(H1 + "ground/ground.png")
	var gmat := GardenLoader.opaque_tex_mat(gtex, true, false)
	_ground_mats.append(gmat)
	var gmi := MeshInstance3D.new()
	gmi.name = "Ground256"
	gmi.mesh = GardenLoader.xz_plane(-128, 128, -128, 128, Vector2(-128, -128), 256.0)
	gmi.position.y = 0.05
	gmi.material_override = gmat
	gmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(gmi)
	var ao: Texture2D = load(H1 + "ground/ground_ao.png")
	if ao:
		var aomat := StandardMaterial3D.new()
		aomat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		aomat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		aomat.blend_mode = BaseMaterial3D.BLEND_MODE_MUL
		aomat.albedo_texture = ao
		aomat.albedo_color = Color(1, 1, 1, 0.7)
		aomat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
		aomat.cull_mode = BaseMaterial3D.CULL_DISABLED
		var ami := MeshInstance3D.new()
		ami.name = "GroundAO"
		ami.mesh = gmi.mesh
		ami.position.y = 0.06
		ami.material_override = aomat
		ami.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(ami)

	# 遠景：天卡＋山丘（H1 day 構圖）；關 cull、unshaded
	for o in objects:
		if str(o.get("type", "")) != "backdrop":
			continue
		var w := float(o.get("w", 100))
		var h := float(o.get("h", 50))
		var f := H1 + str(o.get("file", ""))
		var btex: Texture2D = load(f)
		var is_sky := str(o.get("id", "")).find("sky") >= 0
		var bmat := GardenLoader.make_mat(btex, true, 0.5 if not is_sky else 0.01)
		bmat.cull_mode = BaseMaterial3D.CULL_DISABLED
		bmat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		if is_sky:
			bmat.transparency = BaseMaterial3D.TRANSPARENCY_DISABLED
		else:
			bmat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
			bmat.alpha_scissor_threshold = 0.5
		var bmi := MeshInstance3D.new()
		bmi.name = str(o.get("id", "backdrop"))
		bmi.mesh = GardenLoader.backdrop_mesh(w, h)
		bmi.material_override = bmat
		bmi.position = Vector3(float(o.get("x", 0)), 0, float(o.get("z", 0)))
		if is_sky:
			_sky_w = w
		bmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(bmi)
		bmat.set_meta("is_sky_card", is_sky)
		if is_sky:
			_emissive_mats.append(bmat)  # 夜晚把天卡調暗
		else:
			_hills_mats.append(bmat)  # 遠山獨立染色（unshaded，單靠 LUT 唔夠暗）

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
		if em:
			_emissive_mats.append(mat)
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
	_build_omni_lights(lights)
	var amb: Dictionary = sun_d.get("ambient", {})
	env = WorldEnvironment.new()
	var e := Environment.new()
	# 背景色跟天空（#87bde0），唔用霧色米色 #ffe8c8
	_sky_mat = ProceduralSkyMaterial.new()
	_sky_mat.sky_top_color = Color(135.0 / 255.0, 189.0 / 255.0, 224.0 / 255.0)
	_sky_mat.sky_horizon_color = Color(255.0 / 255.0, 224.0 / 255.0, 156.0 / 255.0)
	_sky_mat.ground_horizon_color = Color(255.0 / 255.0, 224.0 / 255.0, 156.0 / 255.0)
	_sky_mat.ground_bottom_color = Color(103.0 / 255.0, 129.0 / 255.0, 53.0 / 255.0)
	_sky_mat.sky_curve = 0.12
	_sky_mat.use_debanding = false
	var sky := Sky.new()
	sky.sky_material = _sky_mat
	e.background_mode = Environment.BG_SKY
	e.sky = sky
	e.background_color = Color(135.0 / 255.0, 189.0 / 255.0, 224.0 / 255.0)
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	_day_ambient = GardenLoader.hex_color(str(amb.get("color", "#cfe0f0")))
	e.ambient_light_color = _day_ambient
	e.ambient_light_energy = float(amb.get("intensity", 0.55))
	e.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	e.glow_enabled = false
	e.ssao_enabled = false
	e.ssil_enabled = false
	e.sdfgi_enabled = false
	e.adjustment_enabled = false
	e.fog_enabled = false
	env.environment = e
	add_child(env)
	_load_luts()

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
	_apply_vis_fov()
	_fit_sky_card()


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
	pet.character = "tuanrong"
	pet.body_size = "L"
	# 細佬：正面條，1px=1unit，48 框
	kid = Walker.new()
	kid.name = "Kid"
	kid.radius = KID_RADIUS
	kid.speed = 16.0
	kid.idle_fps = ArtImporter.actor_idle_fps("kid") if ArtImporter else 4.0
	kid.walk_fps = ArtImporter.actor_walk_fps("kid") if ArtImporter else 10.0
	add_child(kid)
	kid.position = Vector3(40, 0, 50)
	kid.set_feet(feet)
	var kid_pvt := ArtImporter.actor_pivot("kid") if ArtImporter else Vector2(24, 45)
	kid.setup(_load_strip("res://art/kid/A1_idle.png", 48, 48, 4, "idle", "res://art/kid/A1_walk.png", 6), 1.0, kid_pvt, Vector2(48, 48))
	kid.character = "kid"
	kid.body_size = "M"
	if show_visitor:
		visitor = Walker.new()
		visitor.name = "Visitor"
		visitor.radius = KID_RADIUS
		visitor.speed = 14.0
		visitor.idle_fps = ArtImporter.actor_idle_fps("visitor") if ArtImporter else 4.0
		visitor.walk_fps = ArtImporter.actor_walk_fps("visitor") if ArtImporter else 10.0
		add_child(visitor)
		visitor.position = Vector3(-50, 0, 80)
		visitor.set_feet(feet)
		var vis_pvt := ArtImporter.actor_pivot("visitor") if ArtImporter else Vector2(24, 45)
		visitor.setup(_load_strip("res://art/kid/A1_idle.png", 48, 48, 4, "idle", "res://art/kid/A1_walk.png", 6), 1.0, vis_pvt, Vector2(48, 48))
		visitor.character = "visitor"
		visitor.body_size = "M"
		if visitor.sprite:
			visitor.set_base_modulate(Color(0.85, 0.78, 1.15))


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
		out[clip].append({"name": str(name), "tex": at})
	var sorted_out := {}
	for clip in out.keys():
		var arr: Array = out[clip]
		arr.sort_custom(func(a, b): return str(a["name"]) < str(b["name"]))
		var texs: Array = []
		for it in arr:
			texs.append(it["tex"])
		sorted_out[clip] = texs
	return sorted_out


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
		if AudioManager:
			AudioManager.play("sfx_clean_poop")
		Sim.clean_one()


func _on_quality(tier: int) -> void:
	# 三檔共用同一 3D 花園：mesh、相機、nav、billboard、遮擋一律保留。
	# 低檔只關貴嘅效果，唔換場景、唔改做分層 2D。
	var low := tier == QualitySettings.Tier.LOW
	if sun:
		sun.shadow_enabled = not low  # 低：冇 shadow map；腳底 blob 仍在
		sun.directional_shadow_mode = DirectionalLight3D.SHADOW_ORTHOGONAL
		# 日光能量交俾 set_time_of_day，避免切畫質時沖掉夜晚 0.12
	if env and env.environment:
		var e := env.environment
		# glow／fog 只開 high：mid 開咗 0.0004 霧會令全日／夜發白、對比下降（G0.1 QA）
		e.glow_enabled = tier == QualitySettings.Tier.HIGH
		e.glow_intensity = 0.4
		e.fog_enabled = tier == QualitySettings.Tier.HIGH
		if e.fog_enabled:
			e.fog_light_color = Color(135.0 / 255.0, 189.0 / 255.0, 224.0 / 255.0)
			e.fog_density = 0.00025
		if e.background_mode != Environment.BG_SKY:
			e.background_mode = Environment.BG_SKY
	var vp := get_viewport()
	vp.msaa_3d = Viewport.MSAA_DISABLED
	vp.screen_space_aa = Viewport.SCREEN_SPACE_AA_DISABLED
	vp.scaling_3d_scale = QualitySettings.render_scale()
	# 3D 縮放用雙線性會令像素糊；低檔 0.67 都保持最近鄰，先至唔會睇成錯 filter
	if vp.has_method("set_scaling_3d_mode"):
		pass
	vp.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	if fill:
		fill.visible = true
	for w in [pet, kid, visitor]:
		if w and w.has_method("apply_billboard_quality"):
			w.apply_billboard_quality(low)
	# 切畫質之後重套日夜，避免太陽／補光／環境光被重置
	set_time_of_day(_tod)


func _place_cam(dt: float) -> void:
	if cam == null:
		return
	var A := 0.0 if rest_look else float(cam_data.get("swayAmplitudeDeg", 5))
	var T := float(cam_data.get("swayHalfPeriodSec", 6))
	sway_t += dt
	var yaw := 0.0 if rest_look else -A * cos(PI * sway_t / maxf(T, 0.1))
	var base_pitch := float(cam_data.get("pitchDeg", 30))
	# 每次由基線重算，唔好把上一鏡（例如遮擋位）嘅俯角累積落去
	_obs_pitch = maxf(base_pitch, 42.0)
	# 稍近稍俯，令天空唔超過畫面頂 25%，同時保留樹頂／屋簷
	var dist := float(cam_data.get("dist", 580)) * 0.92
	# 遊策 §0.5 觀察模式：寵物企喺畫面由上計 55–60%（中下），腳底下面見到地；跟拍都保持同一構圖。
	# rest_look 只停 sway，仍然跟寵物構圖（QA 截圖要用呢個規格）。
	var desired := cam_target
	if pet:
		var ppos := pet.global_position
		desired = Vector3(ppos.x, 42.0, ppos.z - 36.0)
	var damp := float(cam_data.get("followDamping", 2.0))
	if rest_look:
		follow_pos = desired
	elif dt > 0.0:
		var k := 1.0 - exp(-damp * dt)
		follow_pos = follow_pos.lerp(desired, k)
	else:
		follow_pos = desired
	_apply_cam_offset(yaw, _obs_pitch, dist)
	_refine_observation(yaw, dist)


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



func _apply_vis_fov() -> void:
	# H1 唔直接用 camera.json fovDeg 40：VIS hfov 29° → VIS vfov，再 setViewOffset 成窗口 vfov ≈37.7°。
	# Godot 未接非對稱 frustum，用窗口等效垂直 FOV（對稱近似）。
	if cam == null:
		return
	var vis: Dictionary = cam_data.get("vis", {"x": 2, "y": 64, "w": 152, "h": 278})
	if vis.is_empty():
		vis = {"x": 2, "y": 64, "w": 152, "h": 278}
	var hf := float(cam_data.get("visHfovDeg", 29))
	var vis_w := float(vis.get("w", 152))
	var vis_h := float(vis.get("h", 278))
	var vis_y := float(vis.get("y", 64))
	var vis_vf := 2.0 * atan(tan(deg_to_rad(hf) * 0.5) * vis_h / maxf(vis_w, 1.0))
	var win_w := float(cam_data.get("designW", 195))
	var win_h := float(cam_data.get("designH", 422))
	var film_half := vis_h * 0.5
	var tan_half := tan(vis_vf * 0.5)
	var ang_up := atan(((vis_y + film_half) / film_half) * tan_half)
	var ang_down := atan(((win_h - vis_y - film_half) / film_half) * tan_half)
	cam.fov = rad_to_deg(ang_up + ang_down)


func _ray_y_at_z(nx: float, ny: float, z: float) -> float:
	if cam == null:
		return 0.0
	var vp := get_viewport().get_visible_rect().size
	var screen := Vector2(nx * vp.x, ny * vp.y)
	var origin := cam.project_ray_origin(screen)
	var dir := cam.project_ray_normal(screen)
	if absf(dir.z) < 0.0001:
		return 0.0
	var t := (z - origin.z) / dir.z
	return origin.y + t * dir.y


func _fit_sky_card() -> void:
	# 官方 bg_sky h=425，但鏡頭可見帶只係山線到畫面頂一截；用成 425 就只睇到圖底暖黃。
	# 把卡高縮到可見帶，令藍頂＋暖地平線梯度落入畫面（H1 day）。
	var sky := get_node_or_null("bg_sky") as MeshInstance3D
	if sky == null or cam == null:
		return
	var z := sky.position.z
	var y_top := _ray_y_at_z(0.5, 0.0, z)
	var hills := get_node_or_null("bg_hills") as MeshInstance3D
	var hill_y := 79.6
	var hill_z := -380.0
	if hills:
		hill_z = hills.position.z
		var aabb := hills.get_aabb()
		hill_y = hills.position.y + aabb.size.y
	var cam_p := cam.global_position
	var d := Vector3(0, hill_y, hill_z) - cam_p
	var y_hill := 50.0
	if absf(d.z) > 0.001:
		var t := (z - cam_p.z) / d.z
		y_hill = cam_p.y + t * d.y
	if y_top <= y_hill + 4.0:
		y_top = y_hill + 90.0
	var y0 := y_hill - 16.0
	var h := (y_top + 10.0) - y0
	sky.mesh = GardenLoader.backdrop_mesh(_sky_w, h)
	sky.position.y = y0



func qa_park_actors() -> void:
	for w in [pet, kid, visitor]:
		if w:
			w.park()


func qa_place_pet(where: String) -> void:
	qa_park_actors()
	if pet == null:
		return
	match where:
		"front_tree":
			pet.global_position = Vector3(-78, 0, 18)
		"behind_tree":
			pet.global_position = Vector3(-88, 0, -70)
		"front_cottage":
			pet.global_position = Vector3(64, 0, -20)
		"behind_cottage":
			pet.global_position = Vector3(82, 0, -110)
		_:
			pet.global_position = Vector3(0, 0, 24)
	if kid:
		kid.global_position = Vector3(40, 0, 50)
	if visitor:
		visitor.global_position = Vector3(-50, 0, 80)
	_place_cam(0.0)
	_fit_sky_card()


func set_shot_size(w: int, h: int) -> void:
	var win := get_window()
	if win:
		win.size = Vector2i(w, h)
		win.content_scale_size = Vector2i(w, h)
		win.content_scale_mode = Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
		win.content_scale_aspect = Window.CONTENT_SCALE_ASPECT_EXPAND
	_place_cam(0.0)
	_apply_vis_fov()
	_fit_sky_card()

func set_rest_look(on: bool) -> void:
	rest_look = on
	if on:
		sway_t = 0.0
		follow_pos = cam_target
	_place_cam(0.0)
	_fit_sky_card()

func follow_device_clock() -> void:
	# 燈光同 BGM 跟本機時鐘四段（hour_of），唔好永遠停喺日間。
	set_time_of_day(TimeService.hour_band())


func set_time_of_day(tod: String) -> void:
	# 四段：morning 05–11、noon／day 11–17、evening 17–22、night 22–05。
	if tod == "day":
		tod = "noon"
	_tod = tod
	var night := tod == "night"
	var evening := tod == "evening"
	var morning := tod == "morning"
	if sun:
		if night:
			sun.light_energy = 0.12
			sun.light_color = Color(0.55, 0.65, 1.0)
		elif evening:
			sun.light_energy = 0.62
			sun.light_color = Color(1.0, 0.62, 0.38)
		elif morning:
			sun.light_energy = 0.95
			sun.light_color = Color(1.0, 0.93, 0.78)
		else:
			sun.light_energy = 1.0
			sun.light_color = GardenLoader.hex_color("#ffe6b8")
	if fill:
		if night:
			fill.light_energy = 0.0
		elif evening:
			fill.light_energy = 0.18
		else:
			fill.light_energy = 0.28 if QualitySettings.is_low() else 0.38
	if env and env.environment:
		var e := env.environment
		if night:
			e.ambient_light_color = Color(0.29, 0.35, 0.56)
			e.ambient_light_energy = 0.35
			e.background_color = Color(0.12, 0.14, 0.28)
		elif evening:
			e.ambient_light_color = Color(0.75, 0.5, 0.38)
			e.ambient_light_energy = 0.48
			e.background_color = Color(0.85, 0.45, 0.28)
		elif morning:
			e.ambient_light_color = Color(0.85, 0.9, 0.98)
			e.ambient_light_energy = 0.52
			e.background_color = Color(135.0 / 255.0, 189.0 / 255.0, 224.0 / 255.0)
		else:
			e.ambient_light_color = _day_ambient
			e.ambient_light_energy = 0.55
			e.background_color = Color(135.0 / 255.0, 189.0 / 255.0, 224.0 / 255.0)
		_apply_band_lut(e, tod)
	if _sky_mat:
		if night:
			_sky_mat.sky_top_color = Color(0.08, 0.10, 0.22)
			_sky_mat.sky_horizon_color = Color(0.22, 0.20, 0.38)
			_sky_mat.ground_horizon_color = Color(0.16, 0.16, 0.24)
			_sky_mat.ground_bottom_color = Color(0.08, 0.10, 0.08)
		elif evening:
			_sky_mat.sky_top_color = Color(0.35, 0.28, 0.55)
			_sky_mat.sky_horizon_color = Color(0.95, 0.5, 0.28)
			_sky_mat.ground_horizon_color = Color(0.85, 0.45, 0.25)
			_sky_mat.ground_bottom_color = Color(0.25, 0.16, 0.1)
		elif morning:
			_sky_mat.sky_top_color = Color(0.45, 0.7, 0.92)
			_sky_mat.sky_horizon_color = Color(1.0, 0.9, 0.75)
			_sky_mat.ground_horizon_color = Color(1.0, 0.9, 0.75)
			_sky_mat.ground_bottom_color = Color(103.0 / 255.0, 129.0 / 255.0, 53.0 / 255.0)
		else:
			_sky_mat.sky_top_color = Color(135.0 / 255.0, 189.0 / 255.0, 224.0 / 255.0)
			_sky_mat.sky_horizon_color = Color(255.0 / 255.0, 224.0 / 255.0, 156.0 / 255.0)
			_sky_mat.ground_horizon_color = Color(255.0 / 255.0, 224.0 / 255.0, 156.0 / 255.0)
			_sky_mat.ground_bottom_color = Color(103.0 / 255.0, 129.0 / 255.0, 53.0 / 255.0)
	# unshaded 地面／遠山都要跟四段染色（LUT 單獨唔夠壓暗中綠同米色遠山）
	# 夜地目標 luma ≈26（environments.json night_ground_target_luma）；遠山更暗更冷。
	var ground_mul := Color.WHITE
	var hills_mul := Color.WHITE
	if night:
		ground_mul = Color(0.22, 0.28, 0.24)
		hills_mul = Color(0.12, 0.16, 0.14)
	elif evening:
		ground_mul = Color(0.7, 0.55, 0.45)
		hills_mul = Color(0.55, 0.42, 0.36)
	elif morning:
		ground_mul = Color(1.0, 0.96, 0.90)
		hills_mul = Color(1.0, 0.97, 0.92)
	for m in _ground_mats:
		if m is StandardMaterial3D:
			(m as StandardMaterial3D).albedo_color = ground_mul
	for m in _hills_mats:
		if m is StandardMaterial3D:
			(m as StandardMaterial3D).albedo_color = hills_mul
	for m in _emissive_mats:
		if m is StandardMaterial3D:
			var sm := m as StandardMaterial3D
			if sm.has_meta("is_sky_card") and bool(sm.get_meta("is_sky_card")):
				if night:
					sm.albedo_color = Color(0.35, 0.4, 0.7)
				elif evening:
					sm.albedo_color = Color(1.0, 0.75, 0.55)
				elif morning:
					sm.albedo_color = Color(1.0, 0.96, 0.92)
				else:
					sm.albedo_color = Color.WHITE
			if sm.emission_enabled:
				sm.emission_energy_multiplier = 1.2 if night else (0.4 if evening else 0.0)
	for rec in _omni_lights:
		if not (rec is Dictionary):
			continue
		var om: OmniLight3D = rec.get("node")
		var d: Dictionary = rec.get("data", {})
		if om == null:
			continue
		var day_e := float(d.get("intensity", 0.0))
		var night_e := float(d.get("intensityNight", 0.0))
		if night:
			om.light_energy = night_e
		elif evening:
			om.light_energy = night_e * 0.35
		else:
			om.light_energy = day_e
	var pet_tint := Color.WHITE
	if night:
		pet_tint = Color(0.40, 0.46, 0.68)
	elif evening:
		pet_tint = Color(0.90, 0.70, 0.55)
	elif morning:
		pet_tint = Color(1.0, 0.97, 0.92)
	for w in [pet, kid, visitor]:
		if w and w.has_method("apply_tod_modulate"):
			w.apply_tod_modulate(pet_tint)
	if AudioManager:
		AudioManager.sync_bgm(tod)


func _build_omni_lights(lights: Dictionary) -> void:
	# 按 lights.json 起夜間點光（燈柱、燈籠、窗、側窗 window_side、螢火瓶）
	for rec in _omni_lights:
		if rec is Dictionary and rec.get("node"):
			var old: Node = rec["node"]
			if is_instance_valid(old):
				old.queue_free()
	_omni_lights.clear()
	var arr: Variant = lights.get("lights", [])
	if not (arr is Array):
		return
	for item in arr:
		if not (item is Dictionary):
			continue
		var om := OmniLight3D.new()
		om.name = "Omni_%s" % str(item.get("id", "light"))
		om.position = Vector3(float(item.get("x", 0)), float(item.get("y", 0)), float(item.get("z", 0)))
		om.light_color = GardenLoader.hex_color(str(item.get("color", "#ffd890")))
		om.omni_range = float(item.get("radius", 40))
		om.light_energy = float(item.get("intensity", 0.0))
		om.shadow_enabled = false
		om.omni_attenuation = 1.5
		add_child(om)
		_omni_lights.append({"node": om, "data": item})


func _load_luts() -> void:
	_luts.clear()
	for id in ["day", "dusk", "night", "identity"]:
		var path := "res://art-pet/fx/luts/lut_%s.png" % id
		var tex := _lut_texture3d(path)
		if tex:
			_luts[id] = tex


func _lut_texture3d(path: String) -> Texture3D:
	# environments.json：官方 1089×33 橫條、33³。Runtime 砌 Texture3D，唔依賴 import 設定。
	if not ResourceLoader.exists(path):
		return null
	var tex2: Texture2D = load(path)
	if tex2 == null:
		return null
	var img := tex2.get_image()
	if img == null:
		return null
	if img.is_compressed():
		img.decompress()
	const N := 33
	if img.get_width() < N * N or img.get_height() < N:
		return null
	var slices: Array[Image] = []
	for i in N:
		var sl := Image.create(N, N, false, Image.FORMAT_RGB8)
		sl.blit_rect(img, Rect2i(i * N, 0, N, N), Vector2i.ZERO)
		slices.append(sl)
	var t3 := ImageTexture3D.new()
	var err := t3.create(Image.FORMAT_RGB8, N, N, N, false, slices)
	if err != OK:
		return null
	return t3


func _apply_band_lut(e: Environment, tod: String) -> void:
	# LUT／調色低檔都開（成本低）。glow／fog 仍然只開 high。
	var lut_id := "day"
	if tod == "evening":
		lut_id = "dusk"
	elif tod == "night":
		lut_id = "night"
	var lut: Texture3D = _luts.get(lut_id)
	e.adjustment_enabled = lut != null
	e.adjustment_color_correction = lut
	e.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	if tod == "night":
		e.tonemap_exposure = 0.88
		e.adjustment_brightness = 1.0
		e.adjustment_contrast = 1.04
		e.adjustment_saturation = 0.96
	elif tod == "evening":
		e.tonemap_exposure = 0.92
		e.adjustment_brightness = 1.0
		e.adjustment_contrast = 1.02
		e.adjustment_saturation = 1.0
	elif tod == "morning":
		e.tonemap_exposure = 1.0
		e.adjustment_brightness = 1.0
		e.adjustment_contrast = 1.0
		e.adjustment_saturation = 1.0
	else:
		e.tonemap_exposure = 1.0
		e.adjustment_brightness = 1.0
		e.adjustment_contrast = 1.0
		e.adjustment_saturation = 1.0


func _apply_cam_offset(yaw: float, pitch: float, dist: float) -> void:
	if cam == null:
		return
	var rad_pitch := deg_to_rad(pitch)
	var rad_yaw := deg_to_rad(yaw)
	var offset := Vector3(0, 0, dist)
	offset = offset.rotated(Vector3.RIGHT, -rad_pitch)
	offset = offset.rotated(Vector3.UP, rad_yaw)
	cam.global_position = follow_pos + offset
	cam.look_at(follow_pos)


func _refine_observation(yaw: float, dist: float) -> void:
	# 調 look-at 高度同俯角：寵物 55–60%、天空最多頂 25%，腳底下面仲見到地。
	if cam == null or pet == null:
		return
	var vp := get_viewport().get_visible_rect().size
	if vp.y < 16.0:
		return
	for _i in range(8):
		_apply_cam_offset(yaw, _obs_pitch, dist)
		var ppos := pet.global_position
		if cam.is_position_behind(ppos):
			return
		var frac := cam.unproject_position(ppos).y / vp.y
		var err := frac - 0.575
		if absf(err) > 0.008:
			follow_pos.y = clampf(follow_pos.y - err * 90.0, 8.0, 140.0)
		var hill := Vector3(follow_pos.x, 80.0, -380.0)
		var sky_frac := cam.unproject_position(hill).y / vp.y
		if sky_frac > 0.25:
			_obs_pitch = clampf(_obs_pitch + (sky_frac - 0.24) * 30.0, 30.0, 50.0)
		elif sky_frac < 0.16 and frac >= 0.54:
			_obs_pitch = clampf(_obs_pitch - (0.16 - sky_frac) * 10.0, 30.0, 50.0)
	_apply_cam_offset(yaw, _obs_pitch, dist)


func qa_framing() -> Dictionary:
	var out := {"pet_y": -1.0, "sky_y": -1.0, "ok": false, "pitch": _obs_pitch}
	if cam == null or pet == null:
		return out
	var vp := get_viewport().get_visible_rect().size
	if vp.y < 16.0:
		return out
	out["pet_y"] = cam.unproject_position(pet.global_position).y / vp.y
	out["sky_y"] = cam.unproject_position(Vector3(follow_pos.x, 80.0, -380.0)).y / vp.y
	out["ok"] = float(out["pet_y"]) >= 0.55 and float(out["pet_y"]) <= 0.60 and float(out["sky_y"]) <= 0.25
	return out
