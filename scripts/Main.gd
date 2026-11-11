extends Node3D
## M1b 主場景：人手餵摸、可見身高鏡頭、狩獵 lite、郵局／廚房、收藏家具。低檔仍然係完整 3D。

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
enum CamMode { OVERVIEW, FOLLOW }
var cam_mode := CamMode.OVERVIEW
var follow_walker: Walker
var family: FamilyDirector
var _cam_dist := 580.0
var _texel_px := 0.0
var _pet_h_frac := 0.0
var _pet_h_quad := 0.0
var _visible_w := 0.0
var hunt_field: HuntField
var work_spots: Dictionary = {}
var furniture_root: Node3D
var warehouse: Node3D
var _hunt_team: Array = []
var in_hunt_view := false
var interior_room: InteriorRoom
var in_interior := false
var _interior_lock_cam := false
var _interior_guest: Walker
var _interior_guest_home := Vector3.ZERO
var _fade_rect: ColorRect
var _house_click: Area3D
var _rotate_layer: CanvasLayer
var _exterior_door: Node3D
signal door_open
signal door_close
signal enter_interior
signal exit_interior

func _ready() -> void:
	rng.randomize()
	add_to_group("glimmer_main")
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
	_setup_rotate_overlay()
	if get_viewport():
		get_viewport().size_changed.connect(_sync_rotate_overlay)
	_sync_rotate_overlay()
	QualitySettings.changed.connect(_on_quality)
	_on_quality(QualitySettings.tier)
	follow_device_clock()
	Sim.poops_changed.connect(func(_n): _sync_poops())
	# M1a 可玩照顧：新檔如果仲喺蛋就入萌芽（產蛋規則測試仍用 Sim.new_state）。
	if str(Sim.state.get("stage", "egg")) == "egg" and Sim.has_method("force_stage"):
		Sim.force_stage("sprout")
	# 第一次進，如果未有便便，放一粒方便驗「可撳執」
	if int(Sim.state.get("poops", 0)) == 0:
		Sim.add_poop()
	_setup_m1b()


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
		mi.name = str(o.get("id", "mesh"))
		mi.mesh = GardenLoader.mesh_from_json(doc, true)
		mi.material_override = mat
		if em:
			_emissive_mats.append(mat)
		mi.position = Vector3(float(o.get("x", 0)), float(o.get("y", 0)), float(o.get("z", 0)))
		mi.rotation_degrees.y = float(o.get("yawDeg", 0))
		if not bool(o.get("castShadow", true)):
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(mi)
	_apply_cottage_exterior()

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
	cam.near = minf(float(cam_data.get("near", 10)), 2.0)
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
		visitor.character = "snail_postman"
		visitor.body_size = "M"
		# art-fix1 未有訪客行路圖：行路用自己 liveliness 幀＋上下彈，唔再用細佬 A1 行路循環。
		_apply_visitor_own_walk(visitor)
	_setup_gameplay_ai()


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
	# 即刻 free（queue_free 唔減 child count，唔好 while queue_free）
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
	if interior_room and interior_room.has_method("apply_tier"):
		interior_room.apply_tier()
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
		if (not in_interior) and e.background_mode != Environment.BG_SKY:
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


func _cam_cfg() -> Dictionary:
	var cfg: Dictionary = {}
	if GameData:
		cfg = GameData.m1a.get("camera", {}).duplicate(true)
		if "m1b" in GameData and not GameData.m1b.is_empty():
			var b: Dictionary = GameData.m1b.get("camera", {})
			for k in b.keys():
				cfg[k] = b[k]
	return cfg


func set_cam_follow(w: Walker) -> void:
	if w == null:
		cam_mode = CamMode.OVERVIEW
		follow_walker = null
		if hud and hud.has_method("set_observing"):
			hud.set_observing(false)
		if hud and hud.has_method("set_care_target"):
			hud.set_care_target(null)
	else:
		cam_mode = CamMode.FOLLOW
		follow_walker = w
		if hud and hud.has_method("set_observing"):
			hud.set_observing(true)
	_place_cam(0.0)
	_fit_sky_card()


func _place_cam(dt: float) -> void:
	if cam == null:
		return
	var A := 0.0 if rest_look else float(cam_data.get("swayAmplitudeDeg", 5))
	var T := float(cam_data.get("swayHalfPeriodSec", 6))
	sway_t += dt
	var yaw := 0.0 if rest_look else -A * cos(PI * sway_t / maxf(T, 0.1))
	var base_pitch := float(cam_data.get("pitchDeg", 30))
	if _interior_lock_cam:
		return
	var hunt_overview := in_hunt_view and hunt_field != null and cam_mode != CamMode.FOLLOW
	if in_interior and interior_room:
		_obs_pitch = interior_room.cam_pitch()
		yaw = interior_room.cam_yaw()
	elif in_hunt_view and hunt_field:
		# 草原用遊美鏡頭（pitch 30），唔好再強制 42° 令寵物睇落好似瞓低
		_obs_pitch = hunt_field.cam_pitch()
	else:
		_obs_pitch = maxf(base_pitch, 42.0)
	var cfg := _cam_cfg()
	var desired := cam_target
	var look: Variant = cfg.get("overview_look", [0, 24, 16])
	var glook: Variant = garden_cfg().get("overview_look", [])
	if glook is Array and glook.size() >= 3:
		look = glook
	if look is Array and look.size() >= 3:
		desired = Vector3(float(look[0]), float(look[1]), float(look[2]))
	if in_interior and interior_room:
		desired = interior_room.look_target()
	elif hunt_overview:
		desired = hunt_field.look_target()
	var subject: Walker = pet
	if cam_mode == CamMode.FOLLOW and follow_walker and is_instance_valid(follow_walker):
		subject = follow_walker
		var ppos := subject.global_position
		desired = Vector3(ppos.x, 28.0, ppos.z)
	var damp := float(cam_data.get("followDamping", 2.0))
	if rest_look:
		follow_pos = desired
	elif dt > 0.0:
		var k := 1.0 - exp(-damp * dt)
		follow_pos = follow_pos.lerp(desired, k)
	else:
		follow_pos = desired
	var tex_scale := int(cfg.get("follow_texel_scale", 3) if cam_mode == CamMode.FOLLOW else cfg.get("overview_texel_scale", 2))
	var dist_tex := _dist_for_texel(float(tex_scale))
	var dist := dist_tex
	if cam_mode == CamMode.OVERVIEW:
		if in_interior and interior_room:
			dist = interior_room.cam_dist()
		elif hunt_overview:
			dist = hunt_field.cam_dist()
		else:
			var dist_g := _dist_for_garden_width(float(cfg.get("garden_width", 256)))
			# 預設：花園填滿畫面闊。窄屏可能只能 ×1；唔好為咗 ×2 切走花園。
			dist = dist_g
	_cam_dist = dist
	_apply_cam_offset(yaw, _obs_pitch, dist)
	if in_interior:
		# 室內用 data 鏡頭距離，唔好再用花園整數倍／寵物最低高度去拉遠
		_measure_cam_metrics()
		return
	if cam_mode == CamMode.FOLLOW:
		_refine_observation(yaw, dist)
		_ensure_follow_pet_min(yaw)
	else:
		# 全景：先花園填滿，再保證寵物 ≥10%，先至考慮整數倍
		_ensure_overview_pet_min(yaw)
	if not hunt_overview:
		_snap_integer_dist(yaw, tex_scale)
	if not hunt_overview and cam_mode == CamMode.OVERVIEW:
		_ensure_cottage_roof_in_frame(yaw)
	# 狩獵全景一樣保證可見高度 ≥10%
	_measure_cam_metrics()


func _process(dt: float) -> void:
	_place_cam(dt)
	if HuntSystem:
		HuntSystem.tick_watch(dt)
		if hunt_field and hunt_field.active:
			hunt_field.tick(dt, HuntSystem.phase)
			_sync_hunt_view()
	if WorkSystem:
		WorkSystem.tick_watch(dt)
		_sync_work_glow()


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


func _ray_area(pos: Vector2, mask: int) -> Area3D:
	if cam == null:
		return null
	var from := cam.project_ray_origin(pos)
	var dir := cam.project_ray_normal(pos)
	var q := PhysicsRayQueryParameters3D.create(from, from + dir * 4000.0)
	q.collide_with_areas = true
	q.collide_with_bodies = false
	q.collision_mask = mask
	var hit := get_world_3d().direct_space_state.intersect_ray(q)
	if hit and hit.get("collider") is Area3D:
		return hit["collider"]
	return null


func _try_tap(pos: Vector2) -> void:
	if cam == null:
		return
	var pet_hit := _ray_area(pos, 4)
	if pet_hit:
		var w := pet_hit.get_parent()
		if w is Walker:
			_on_pet_tapped(w)
			return
	var poop_hit := _ray_area(pos, 2)
	if poop_hit:
		_clean_poop(poop_hit)
		return
	if not in_interior and not in_hunt_view:
		var house := _ray_area(pos, 16)
		if house:
			enter_house()
			return
	var bld := _ray_area(pos, 8)
	if bld:
		_on_building_tapped(bld)
		return
	# 撳空地：跟拍中返全景
	if cam_mode == CamMode.FOLLOW:
		set_cam_follow(null)



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
	# 截圖預設用總覽；follow_* 先跟拍
	if where.begins_with("follow"):
		pass
	else:
		if cam_mode != CamMode.OVERVIEW:
			set_cam_follow(null)
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
	_sync_rotate_overlay()

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
		if in_interior:
			_apply_interior_background(true)
		elif night:
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
	_measure_cam_metrics()
	var cfg := _cam_cfg()
	var out := {
		"pet_y": -1.0, "sky_y": -1.0, "ok": false, "pitch": _obs_pitch,
		"mode": "follow" if cam_mode == CamMode.FOLLOW else "overview",
		"pet_h": _pet_h_frac, "texel": _texel_px, "visible_w": _visible_w, "dist": _cam_dist,
	}
	if cam == null or pet == null:
		return out
	var vp := get_viewport().get_visible_rect().size
	if vp.y < 16.0:
		return out
	out["pet_y"] = cam.unproject_position(pet.global_position).y / vp.y
	out["sky_y"] = cam.unproject_position(Vector3(follow_pos.x, 80.0, -380.0)).y / vp.y
	out["pet_h_quad"] = _pet_h_quad
	out["pet_h_visible"] = _pet_h_frac
	if cam_mode == CamMode.FOLLOW:
		out["ok"] = (
			float(out["pet_y"]) >= float(cfg.get("pet_y_frac_min", 0.55)) - 0.03
			and float(out["pet_y"]) <= float(cfg.get("pet_y_frac_max", 0.60)) + 0.03
			and float(out["sky_y"]) <= float(cfg.get("sky_frac_max", 0.25)) + 0.04
			and _pet_h_frac >= float(cfg.get("follow_pet_min_frac", 0.20)) - 0.02
		)
	else:
		# 可見身高 ≥10% 優先；花園填滿／整數倍可以讓路
		out["ok"] = _pet_h_frac >= float(cfg.get("overview_pet_min_frac", 0.10)) - 0.01
		out["garden_fill"] = _visible_w
		out["texel_integer"] = absf(_texel_px - round(_texel_px)) < 0.25
	return out


func _setup_gameplay_ai() -> void:
	family = FamilyDirector.new()
	family.name = "FamilyDirector"
	add_child(family)
	for pair in [[pet, "tuanrong"], [kid, "kid"], [visitor, "snail_postman"]]:
		var w: Walker = pair[0]
		var id := str(pair[1])
		if w == null:
			continue
		var brain := PetBrain.new()
		brain.name = "PetBrain"
		w.add_child(brain)
		brain.setup(w, id, family)
		if family:
			family.register(w, brain)
		var bubble := NeedBubble.new()
		bubble.name = "NeedBubble"
		w.add_child(bubble)
		bubble.attach(w)
	# 文靜角色休息時可用坐低 idle_quiet（art-fix1）
	if Personality and pet and Personality.primary_type("tuanrong") == "文靜":
		pass


func _on_pet_tapped(w: Walker) -> void:
	set_cam_follow(w)
	if hud and hud.has_method("set_care_target"):
		hud.set_care_target(w)
	var brain: Node = w.get_node_or_null("PetBrain")
	if brain and brain.has_method("notify_tap"):
		brain.notify_tap("pet")
	if AudioManager:
		AudioManager.play("sfx_ui8_btn_press")


func pet_all_react() -> void:
	for w in [pet, kid, visitor]:
		if w == null:
			continue
		var brain: Node = w.get_node_or_null("PetBrain")
		if brain and brain.has_method("notify_tap"):
			brain.notify_tap("pet")


func _dist_for_texel(texel_px: float) -> float:
	var vp := get_viewport().get_visible_rect().size
	if cam == null or vp.y < 8.0:
		return float(cam_data.get("dist", 580))
	var vfov := deg_to_rad(cam.fov)
	return (vp.y * 0.5) / (tan(vfov * 0.5) * maxf(texel_px, 0.5))


func _dist_for_garden_width(want_w: float) -> float:
	var vp := get_viewport().get_visible_rect().size
	if cam == null or vp.y < 8.0 or vp.x < 8.0:
		return float(cam_data.get("dist", 580))
	var aspect := vp.x / vp.y
	var vfov := deg_to_rad(cam.fov)
	var hfov := 2.0 * atan(tan(vfov * 0.5) * aspect)
	return (maxf(want_w, 8.0) * 0.5) / tan(hfov * 0.5)


func _ensure_follow_pet_min(yaw: float) -> void:
	if cam == null or pet == null or cam_mode != CamMode.FOLLOW:
		return
	_measure_cam_metrics()
	var need := float(_cam_cfg().get("follow_pet_min_frac", 0.20))
	if _pet_h_frac >= need - 0.002 or _pet_h_frac <= 0.001:
		return
	var ratio := _pet_h_frac / need
	_cam_dist = clampf(_cam_dist * ratio, 80.0, 1600.0)
	_apply_cam_offset(yaw, _obs_pitch, _cam_dist)
	_refine_observation(yaw, _cam_dist)
	_measure_cam_metrics()


func _ensure_overview_pet_min(yaw: float) -> void:
	if cam == null or pet == null or cam_mode != CamMode.OVERVIEW:
		return
	_measure_cam_metrics()
	var need := float(_cam_cfg().get("overview_pet_min_frac", 0.10))
	if _pet_h_frac >= need - 0.002 or _pet_h_frac <= 0.001:
		return
	var ratio := _pet_h_frac / need
	_cam_dist = clampf(_cam_dist * ratio, 80.0, 1600.0)
	_apply_cam_offset(yaw, _obs_pitch, _cam_dist)
	_measure_cam_metrics()


func _snap_integer_dist(yaw: float, prefer: int) -> void:
	if cam == null or pet == null:
		return
	_measure_cam_metrics()
	var target := float(prefer)
	if _texel_px <= 0.1:
		return
	# 拉近／拉遠到最接近嘅整數倍
	var snapped := maxf(1.0, round(_texel_px))
	if cam_mode == CamMode.FOLLOW:
		snapped = maxf(float(prefer), 1.0)
		if _texel_px >= 2.5 and prefer <= 3:
			snapped = 3.0
		elif _texel_px >= 1.5:
			snapped = maxf(2.0, float(prefer) if prefer <= 2 else 2.0)
		var need_f := float(_cam_cfg().get("follow_pet_min_frac", 0.20))
		var pet_f := _pet_h_frac * (snapped / _texel_px) if _texel_px > 0.01 else 0.0
		if pet_f < need_f - 0.005:
			return
	else:
		# 總覽：可見身高優先；整數倍同花園填滿可以讓路（遊策 M1a 回饋）
		var need := float(_cam_cfg().get("overview_pet_min_frac", 0.10))
		var pet2 := _pet_h_frac * (snapped / _texel_px) if _texel_px > 0.01 else 0.0
		if pet2 < need - 0.005:
			return
	var ratio := _texel_px / snapped
	if absf(ratio - 1.0) < 0.04:
		return
	_cam_dist = clampf(_cam_dist * ratio, 80.0, 1600.0)
	_apply_cam_offset(yaw, _obs_pitch, _cam_dist)
	if cam_mode == CamMode.FOLLOW:
		_refine_observation(yaw, _cam_dist)


func _measure_cam_metrics() -> void:
	_texel_px = 0.0
	_pet_h_frac = 0.0
	_visible_w = 0.0
	if cam == null or pet == null:
		return
	var vp := get_viewport().get_visible_rect().size
	if vp.y < 8.0:
		return
	var feet := pet.global_position
	if cam.is_position_behind(feet):
		return
	var up := feet + Vector3(0, 1, 0)
	_texel_px = absf(cam.unproject_position(up).y - cam.unproject_position(feet).y)
	var hh := pet.world_height() if pet.has_method("world_height") else 64.0
	var head := feet + Vector3(0, hh, 0)
	_pet_h_quad = absf(cam.unproject_position(head).y - cam.unproject_position(feet).y) / vp.y
	# 遊策：用可見（非透明）像素高度，唔用廣告牌框
	var y_top := hh
	var y_bot := 0.0
	if pet.has_method("visible_world_top"):
		y_top = pet.visible_world_top()
		y_bot = pet.visible_world_bottom() if pet.has_method("visible_world_bottom") else 0.0
	var p_top := feet + Vector3(0, y_top, 0)
	var p_bot := feet + Vector3(0, y_bot, 0)
	_pet_h_frac = absf(cam.unproject_position(p_top).y - cam.unproject_position(p_bot).y) / vp.y
	# 可見闊（睇住點所在、垂直視線平面）
	var mid := Vector2(vp.x * 0.5, vp.y * 0.5)
	var left := Vector2(0.0, vp.y * 0.5)
	var right := Vector2(vp.x, vp.y * 0.5)
	var p0 := _ray_at_plane(mid)
	var pl := _ray_at_plane(left)
	var pr := _ray_at_plane(right)
	if p0 != Vector3.INF and pl != Vector3.INF and pr != Vector3.INF:
		_visible_w = pl.distance_to(pr)


func _ray_at_plane(screen: Vector2) -> Vector3:
	# 同鏡頭望向平面（經過 follow_pos、法線＝鏡頭向前）相交
	if cam == null:
		return Vector3.INF
	var origin := cam.project_ray_origin(screen)
	var dir := cam.project_ray_normal(screen)
	var nrm := -cam.global_transform.basis.z.normalized()
	var denom := dir.dot(nrm)
	if absf(denom) < 0.0001:
		return Vector3.INF
	var t := (follow_pos - origin).dot(nrm) / denom
	if t < 0.0:
		return Vector3.INF
	return origin + dir * t



func qa_follow_pet() -> void:
	if pet:
		set_cam_follow(pet)


func qa_overview() -> void:
	set_cam_follow(null)
	qa_place_pet("default")


func qa_force_needs(hunger: float = 100.0, mood: float = 100.0, clean: float = 100.0, energy: float = 100.0) -> void:
	if Sim == null:
		return
	var n: Dictionary = Sim.state.get("needs", {})
	n["hunger"] = hunger
	n["mood"] = mood
	n["clean"] = clean
	n["energy"] = energy
	Sim.state["needs"] = n
	Sim.state_changed.emit()


func qa_family(kind: String) -> bool:
	return family != null and family.force(kind)


func _setup_m1b() -> void:
	if CollectionSystem:
		CollectionSystem.ensure()
		CollectionSystem.silent_unlocks = true
		var form := str(Sim.state.get("form", "radiant"))
		if form == "":
			form = "radiant"
		CollectionSystem.unlock_form("%s_%s" % [form, str(Sim.state.get("stage", "sprout"))])
		CollectionSystem.unlock_kid("A1")
		CollectionSystem.silent_unlocks = false
	_build_work_spots()
	_build_warehouse()
	hunt_field = HuntField.new()
	add_child(hunt_field)
	hunt_field.setup()
	hunt_field.attach_warehouse(warehouse)
	_setup_interior()
	refresh_furniture()
	if HuntSystem and HuntSystem.has_signal("hunt_phase"):
		HuntSystem.hunt_phase.connect(func(p): _on_hunt_phase(str(p)))
	if WorkSystem and WorkSystem.has_signal("dispatched"):
		WorkSystem.dispatched.connect(func(id, pets): _send_pets_to_work(str(id), pets))


func _apply_visitor_own_walk(w: Walker) -> void:
	if w == null or ArtImporter == null:
		return
	var frames: Array = ArtImporter.frames_of("scratch", w.body_size, w.character)
	if frames.is_empty():
		frames = ArtImporter.frames_of("sniff", w.body_size, w.character)
	if frames.is_empty():
		return
	# 用自己外形行路（未有 walk 圖就重複自己幀＋彈跳）
	w.frames["front_walk"] = frames
	w.frames["back_walk"] = frames
	w.frames["side_walk"] = frames
	var idle: Array = ArtImporter.frames_of("sniff", w.body_size, w.character)
	if idle.is_empty():
		idle = frames
	w.frames["front_idle"] = idle
	w.frames["back_idle"] = idle
	w.frames["side_idle"] = idle
	w.walk_bob = true


func _build_work_spots() -> void:
	var buildings: Array = WorkSystem.buildings() if WorkSystem else []
	var cols := {"post": Color(0.78, 0.62, 0.38), "kitchen": Color(0.82, 0.48, 0.36)}
	for b in buildings:
		if not (b is Dictionary):
			continue
		var id := str(b.get("id", ""))
		var pos_a: Variant = b.get("pos", [0, 0, 0])
		var pos := Vector3(0, 0, 0)
		if pos_a is Array and pos_a.size() >= 3:
			pos = Vector3(float(pos_a[0]), float(pos_a[1]), float(pos_a[2]))
		# 佔位色塊搬去花園邊位，唔好堵門口或中間草地
		if GameData and "m1d" in GameData:
			var key := "post_pos" if id == "post" else ("kitchen_pos" if id == "kitchen" else "")
			if key != "":
				var pp: Variant = GameData.m1d.get("garden", {}).get(key, [])
				if pp is Array and pp.size() >= 3:
					pos = Vector3(float(pp[0]), float(pp[1]), float(pp[2]))
		var spot := WorkSpot.new()
		add_child(spot)
		spot.setup(id, str(b.get("zh", id)), pos, cols.get(id, Color(0.7, 0.6, 0.45)))
		work_spots[id] = spot


func _build_warehouse() -> void:
	warehouse = Node3D.new()
	warehouse.name = "Warehouse"
	var pos := Vector3(18, 0, -96)
	if GameData and "m1b" in GameData:
		var p: Variant = GameData.m1b.get("hunt", {}).get("warehouse", [18, 0, -96])
		if p is Array and p.size() >= 3:
			pos = Vector3(float(p[0]), float(p[1]), float(p[2]))
	var wp: Variant = garden_cfg().get("warehouse_pos", [])
	if wp is Array and wp.size() >= 3:
		pos = Vector3(float(wp[0]), float(wp[1]), float(wp[2]))
	warehouse.position = pos
	var box := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(28, 22, 20)
	box.mesh = bm
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.55, 0.4, 0.28)
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	box.material_override = mat
	box.position = Vector3(0, 11, 0)
	warehouse.add_child(box)
	add_child(warehouse)


func refresh_furniture() -> void:
	if furniture_root:
		furniture_root.queue_free()
	furniture_root = Node3D.new()
	furniture_root.name = "Furniture"
	add_child(furniture_root)
	var indoor_root: Node3D = null
	if interior_room and is_instance_valid(interior_room):
		if interior_room.furniture_root and is_instance_valid(interior_room.furniture_root):
			for c in interior_room.furniture_root.get_children():
				c.queue_free()
			indoor_root = interior_room.furniture_root
	if CollectionSystem == null:
		return
	var placed: Dictionary = CollectionSystem.placed_items()
	# 花園只擺戶外件；室內件擺喺獨立房間
	var garden_slots := {
		"bed": Vector3(70, 4, -48),
		"table": Vector3(52, 4, -36),
		"rug": Vector3(64, 0.4, -40),
		"lamp": Vector3(44, 8, -52),
		"wall": Vector3(86, 16, -44),
		"window": Vector3(78, 18, -60),
	}
	for sl in placed.keys():
		var id := str(placed[sl])
		var zone := furniture_zone(id, str(sl))
		var node: Node3D
		if zone == "indoor" and indoor_root and interior_room:
			var pos: Vector3 = interior_room.slot_pos(str(sl))
			node = _make_furniture(id, str(sl), pos)
			if node:
				node.name = "Furn_%s" % id
				indoor_root.add_child(node)
		else:
			var pos: Vector3 = garden_slots.get(sl, Vector3(64, 4, -40))
			node = _make_furniture(id, str(sl), pos)
			if node:
				node.name = "Furn_%s" % id
				furniture_root.add_child(node)


func hand_feed(w: Walker, food: String = "meal") -> Dictionary:
	if w == null:
		return {"ok": false, "reason": "pick_pet", "act": "feed"}
	set_cam_follow(w)
	if hud and hud.has_method("set_care_target"):
		hud.set_care_target(w)
	var brain: Node = w.get_node_or_null("PetBrain")
	if brain and brain.has_method("notify_tap"):
		brain.notify_tap("feed")
	if AudioManager:
		var hook := "sfx_feed_meal" if food != "snack" else "sfx_feed_snack"
		AudioManager.play(hook, w)
	if str(w.character) == "tuanrong":
		return Sim.feed(food)
	return {"ok": true, "act": "feed", "hunger": 0, "mood": 0, "flavor": true}


func hand_pat(w: Walker) -> Dictionary:
	if w == null:
		return {"ok": false, "reason": "pick_pet", "act": "pat"}
	set_cam_follow(w)
	if hud and hud.has_method("set_care_target"):
		hud.set_care_target(w)
	var brain: Node = w.get_node_or_null("PetBrain")
	if brain and brain.has_method("notify_tap"):
		brain.notify_tap("pat")
	if str(w.character) == "tuanrong":
		return Sim.pat()
	return {"ok": true, "act": "pat", "mood": 0, "flavor": true}


func family_team() -> Array:
	var out: Array = []
	for w in [pet, kid]:
		if w:
			out.append(w)
	return out


func start_hunt() -> Dictionary:
	var ids: Array = []
	var ws: Array = []
	for w in family_team():
		ids.append(str(w.character))
		ws.append(w)
	if ids.is_empty():
		return {"ok": false, "reason": "no_team"}
	var rec: Dictionary = HuntSystem.depart(ids)
	if not bool(rec.get("ok", false)):
		return rec
	_hunt_team = ws
	if hunt_field:
		# 先排隊去後門
		var gate := Vector3(0, 0, -118)
		if GameData and "m1b" in GameData:
			var g: Variant = GameData.m1b.get("hunt", {}).get("gate", [0, 0, -118])
			if g is Array and g.size() >= 3:
				gate = Vector3(float(g[0]), float(g[1]), float(g[2]))
		for i in range(ws.size()):
			var w: Walker = ws[i]
			var brain: Node = w.get_node_or_null("PetBrain")
			if brain:
				brain.busy = true
			w.brain_driven = false
			w.go_to(gate + Vector3(float(i) * 16.0 - 8.0, 0, 0))
	return rec


func _on_hunt_phase(phase: String) -> void:
	if phase == HuntSystem.PHASE_HUNT:
		# 帶隊入野外
		if hunt_field:
			for i in range(_hunt_team.size()):
				var w: Walker = _hunt_team[i]
				if w:
					w.global_position = hunt_field.field_pos(Vector3(-20 + i * 24, 0, 20))
			hunt_field.begin(_hunt_team)
			in_hunt_view = true
			set_garden_hidden_for_hunt(true)
	elif phase == HuntSystem.PHASE_CARRY:
		pass
	elif phase == HuntSystem.PHASE_READY or phase == HuntSystem.PHASE_HOME:
		_return_from_hunt()


func _return_from_hunt() -> void:
	var home := Vector3(0, 0, 24)
	for i in range(_hunt_team.size()):
		var w: Walker = _hunt_team[i]
		if w == null or not is_instance_valid(w):
			continue
		w.global_position = Vector3(home.x + float(i) * 18.0, 0, home.z)
		w.cancel_follow()
	if hunt_field:
		hunt_field.end_duty()
		# 野外隱藏，花園倉保留果堆
		hunt_field.visible = false
	in_hunt_view = false
	set_garden_hidden_for_hunt(false)
	_place_cam(0.0)
	_fit_sky_card()


func _sync_hunt_view() -> void:
	if not in_hunt_view or hunt_field == null or cam == null:
		return
	# 觀察野外：鏡頭望住隊
	var look := hunt_field.look_target()
	if cam_mode != CamMode.FOLLOW:
		follow_pos = follow_pos.lerp(look, 0.2)


func one_tap_dispatch() -> Dictionary:
	# 照上次，冇就自動派團絨去空建築（先郵局）
	var ids: Array = []
	if WorkSystem:
		ids = WorkSystem.auto_team(["tuanrong"])
	if ids.is_empty():
		ids = ["tuanrong"]
	# 揀一間空建築
	for b in (WorkSystem.buildings() if WorkSystem else []):
		var bid := str(b.get("id", ""))
		var r: Dictionary = WorkSystem.dispatch(bid, ids)
		if bool(r.get("ok", false)):
			return r
	return {"ok": false, "reason": "busy"}


func _send_pets_to_work(building_id: String, ids: Array) -> void:
	var spot: WorkSpot = work_spots.get(building_id)
	if spot == null:
		return
	var door: Vector3 = spot.door_pos()
	for w in [pet, kid, visitor]:
		if w == null:
			continue
		if str(w.character) in ids or (str(w.character) == "tuanrong" and "tuanrong" in ids):
			var brain: Node = w.get_node_or_null("PetBrain")
			if brain:
				brain.busy = true
			w.brain_driven = false
			w.go_to(door)
			if not w.play_live_clip("idle_quiet", true):
				w.play_live_clip("scratch")
	# 工作完（ready）會喺 _sync_work_glow 解除


func _sync_work_glow() -> void:
	for id in work_spots.keys():
		var spot: WorkSpot = work_spots[id]
		if spot:
			spot.set_ready_glow(WorkSystem.is_ready(str(id)) if WorkSystem else false)
	# 收工之後放寵物返自主
	if WorkSystem:
		for b in WorkSystem.buildings():
			var id := str(b.get("id", ""))
			var sit: Dictionary = WorkSystem.site(id)
			if str(sit.get("status", "")) == WorkSystem.ST_EMPTY:
				for w in [pet, kid]:
					if w and not w.brain_driven and (HuntSystem == null or HuntSystem.phase == HuntSystem.PHASE_IDLE):
						var brain: Node = w.get_node_or_null("PetBrain")
						if brain and brain.busy and (HuntSystem == null or not HuntSystem.team.has(str(w.character))):
							# 可能仲喺狩獵；只喺呢座已經清空先放
							pass


func _on_building_tapped(area: Area3D) -> void:
	var spot: Node = area.get_parent()
	if spot == null or not (spot is WorkSpot):
		return
	var bid := str((spot as WorkSpot).building_id)
	# 未派就派；做好就收。成功功能聲由 AudioManager 接信號；失敗播 error。
	if WorkSystem and WorkSystem.is_ready(bid):
		var rec: Dictionary = WorkSystem.collect(bid)
		if hud and hud.has_method("_on_care"):
			hud._on_care("work", rec)
		# 放返寵物
		for w in [pet, kid]:
			if w:
				w.brain_driven = true
				var brain: Node = w.get_node_or_null("PetBrain")
				if brain:
					brain.busy = false
		return
	var sit: Dictionary = WorkSystem.site(bid) if WorkSystem else {}
	if str(sit.get("status", "empty")) == "empty":
		var ids: Array = WorkSystem.auto_team(["tuanrong"]) if WorkSystem else ["tuanrong"]
		if ids.is_empty():
			ids = ["tuanrong"]
		var r: Dictionary = WorkSystem.dispatch(bid, ids)
		if not bool(r.get("ok", false)):
			if AudioManager:
				AudioManager.play("sfx_ui8_error")
		elif hud and hud.has_method("_queue_or_show"):
			hud._queue_or_show([{"icon": "ev_work", "num": str((spot as WorkSpot).title)}])
	else:
		# 睇佢做嘢：跟住正在做嘢嗰隻
		if pet:
			set_cam_follow(pet)


func qa_force_hungry() -> void:
	qa_force_needs(18.0, 88.0, 88.0, 88.0)



func furniture_mount(id: String, sl: String = "") -> String:
	# 每件 mount: wall／floor（data/economy.json；slot 後備喺 m1c.json）
	var item: Dictionary = {}
	if CollectionSystem and CollectionSystem.has_method("_item"):
		item = CollectionSystem._item(id)
	if str(item.get("mount", "")) != "":
		return str(item.get("mount"))
	var by_slot: Dictionary = {}
	var default := "floor"
	if GameData and "m1c" in GameData:
		var furn: Dictionary = GameData.m1c.get("furniture", {})
		by_slot = furn.get("mount_by_slot", {})
		default = str(furn.get("default_mount", "floor"))
	if sl != "" and by_slot.has(sl):
		return str(by_slot[sl])
	if sl == "wall" or sl == "window":
		return "wall"
	return default


func furniture_sprite_y(id: String, sl: String, pos: Vector3) -> float:
	# 掛牆用 slot 嘅 pos.y（牆槽舊色塊 y=16）；落地寫 0，唔寫死喺程式
	if furniture_mount(id, sl) == "wall":
		return pos.y
	return 0.0


func _make_furniture(id: String, sl: String, pos: Vector3) -> Node3D:
	var dir := "res://art-pet/sprites/series2_house/furniture/"
	if GameData and "m1c" in GameData:
		dir = str(GameData.m1c.get("furniture", {}).get("art_dir", dir))
	var psize := 1.0
	if GameData and "m1c" in GameData:
		psize = float(GameData.m1c.get("furniture", {}).get("pixel_size", 1.0))
	var path := dir + id + ".png"
	var tex: Texture2D = null
	if ResourceLoader.exists(path) or FileAccess.file_exists(path):
		tex = load(path)
	var y := furniture_sprite_y(id, sl, pos)
	if tex == null:
		# 冇遊美圖就用色塊（仍然用晒 slot pos，包括牆槽 y）
		var mi := MeshInstance3D.new()
		var box := BoxMesh.new()
		box.size = Vector3(12, 8 if sl != "rug" else 1.2, 12 if sl != "wall" else 4)
		mi.mesh = box
		var mat := StandardMaterial3D.new()
		mat.albedo_color = Color(0.75, 0.62, 0.42)
		if sl == "bed":
			mat.albedo_color = Color(0.62, 0.78, 0.48)
		elif sl == "lamp":
			mat.albedo_color = Color(1.0, 0.85, 0.4)
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mi.material_override = mat
		mi.position = pos
		return mi
	if sl == "rug":
		# 平放喺地上
		var mi := MeshInstance3D.new()
		var sz := tex.get_size()
		var pm := PlaneMesh.new()
		pm.size = Vector2(sz.x * psize, sz.y * psize)
		mi.mesh = pm
		var mat := StandardMaterial3D.new()
		mat.albedo_texture = tex
		mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
		mat.alpha_scissor_threshold = 0.5
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
		mat.cull_mode = BaseMaterial3D.CULL_DISABLED
		mi.material_override = mat
		mi.position = Vector3(pos.x, pos.y if pos.y != 0.0 else 0.4, pos.z)
		return mi
	# 立體傢俬：貼圖喺正面，側面／頂有厚度，會同寵物遮擋。唔再用 Sprite3D 廣告牌。
	return _make_furniture_box(id, sl, pos, tex, psize, y)


func _furniture_depth(sl: String, tex: Texture2D) -> float:
	var depths: Dictionary = {}
	if GameData and "m1d" in GameData:
		depths = GameData.m1d.get("interior", {}).get("furniture_depth_wu", {})
	if depths.has(sl):
		return float(depths[sl])
	if sl == "bed":
		return 32.0
	if sl == "table":
		return 22.0
	if sl == "lamp":
		return 14.0
	if sl == "wall" or sl == "window":
		return 8.0
	if tex:
		return maxf(10.0, float(tex.get_width()) * 0.28)
	return 16.0


func _make_furniture_box(id: String, sl: String, pos: Vector3, tex: Texture2D, psize: float, y: float) -> Node3D:
	var w := float(tex.get_width()) * psize
	var h := float(tex.get_height()) * psize
	var d := _furniture_depth(sl, tex)
	if d < 0.5:
		d = 8.0
	var root := Node3D.new()
	root.name = "FurnBox"
	var place := pos
	var yaw := 0.0
	# 掛牆件貼實後牆／側牆，正面朝房內
	if furniture_mount(id, sl) == "wall" and interior_room:
		var sz: Vector3 = interior_room.size
		var back_z := -sz.z * 0.5
		var left_x := -sz.x * 0.5
		var right_x := sz.x * 0.5
		var dist_back := absf(pos.z - back_z)
		var dist_l := absf(pos.x - left_x)
		var dist_r := absf(pos.x - right_x)
		if dist_back <= dist_l and dist_back <= dist_r:
			place = Vector3(pos.x, y, back_z + d * 0.5 + 0.2)
			yaw = 0.0
		elif dist_l <= dist_r:
			place = Vector3(left_x + d * 0.5 + 0.2, y, pos.z)
			yaw = -90.0
		else:
			place = Vector3(right_x - d * 0.5 - 0.2, y, pos.z)
			yaw = 90.0
	else:
		place = Vector3(pos.x, y, pos.z)
	root.position = place
	root.rotation_degrees.y = yaw
	var mi := MeshInstance3D.new()
	mi.name = "Mesh"
	mi.mesh = _furniture_box_mesh(w, h, d)
	var mat := StandardMaterial3D.new()
	mat.albedo_texture = tex
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
	mat.alpha_scissor_threshold = 0.5
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mi.material_override = mat
	mi.position = Vector3(0, 0, 0)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root.add_child(mi)
	return root


func _furniture_box_mesh(w: float, h: float, d: float) -> ArrayMesh:
	# 原點＝底面中心，正面朝 +Z。UV：正面／背面用成張圖，側面用左右邊緣一條，頂／底用上下邊緣。
	var hw := w * 0.5
	var hd := d * 0.5
	var verts := PackedVector3Array()
	var nrm := PackedVector3Array()
	var uv := PackedVector2Array()
	var idx := PackedInt32Array()
	# front +Z
	_box_quad(verts, nrm, uv, idx,
		Vector3(-hw, 0, hd), Vector3(hw, 0, hd), Vector3(hw, h, hd), Vector3(-hw, h, hd),
		Vector3(0, 0, 1), Vector2(0, 1), Vector2(1, 1), Vector2(1, 0), Vector2(0, 0))
	# back -Z
	_box_quad(verts, nrm, uv, idx,
		Vector3(hw, 0, -hd), Vector3(-hw, 0, -hd), Vector3(-hw, h, -hd), Vector3(hw, h, -hd),
		Vector3(0, 0, -1), Vector2(1, 1), Vector2(0, 1), Vector2(0, 0), Vector2(1, 0))
	# left -X（用圖左邊一條）
	_box_quad(verts, nrm, uv, idx,
		Vector3(-hw, 0, -hd), Vector3(-hw, 0, hd), Vector3(-hw, h, hd), Vector3(-hw, h, -hd),
		Vector3(-1, 0, 0), Vector2(0.04, 1), Vector2(0.0, 1), Vector2(0.0, 0), Vector2(0.04, 0))
	# right +X
	_box_quad(verts, nrm, uv, idx,
		Vector3(hw, 0, hd), Vector3(hw, 0, -hd), Vector3(hw, h, -hd), Vector3(hw, h, hd),
		Vector3(1, 0, 0), Vector2(0.96, 1), Vector2(1, 1), Vector2(1, 0), Vector2(0.96, 0))
	# top +Y
	_box_quad(verts, nrm, uv, idx,
		Vector3(-hw, h, hd), Vector3(hw, h, hd), Vector3(hw, h, -hd), Vector3(-hw, h, -hd),
		Vector3(0, 1, 0), Vector2(0, 0.04), Vector2(1, 0.04), Vector2(1, 0.0), Vector2(0, 0.0))
	# bottom -Y
	_box_quad(verts, nrm, uv, idx,
		Vector3(-hw, 0, -hd), Vector3(hw, 0, -hd), Vector3(hw, 0, hd), Vector3(-hw, 0, hd),
		Vector3(0, -1, 0), Vector2(0, 1), Vector2(1, 1), Vector2(1, 0.96), Vector2(0, 0.96))
	var arrays: Array = []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = verts
	arrays[Mesh.ARRAY_NORMAL] = nrm
	arrays[Mesh.ARRAY_TEX_UV] = uv
	arrays[Mesh.ARRAY_INDEX] = idx
	var am := ArrayMesh.new()
	am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	return am


func _box_quad(verts: PackedVector3Array, nrm: PackedVector3Array, uv: PackedVector2Array, idx: PackedInt32Array, a: Vector3, b: Vector3, c: Vector3, d: Vector3, n: Vector3, ua: Vector2, ub: Vector2, uc: Vector2, ud: Vector2) -> void:
	var base := verts.size()
	verts.append(a)
	verts.append(b)
	verts.append(c)
	verts.append(d)
	for _i in range(4):
		nrm.append(n)
	uv.append(ua)
	uv.append(ub)
	uv.append(uc)
	uv.append(ud)
	idx.append(base)
	idx.append(base + 1)
	idx.append(base + 2)
	idx.append(base)
	idx.append(base + 2)
	idx.append(base + 3)

func hunt_hidden_garden_ids() -> Array:
	var ids: Array = ["cottage", "tree", "lanterns"]
	if GameData and "m1c" in GameData:
		var cfg: Dictionary = GameData.m1c.get("hunt", {}).get("hide_garden_house", {})
		if cfg.get("hide_node_ids") is Array and not cfg["hide_node_ids"].is_empty():
			ids = cfg["hide_node_ids"]
	return ids


func set_garden_hidden_for_hunt(on: bool) -> void:
	# 隱藏花園中景／遠景道具，避免喺狩獵場背景透出
	for id in hunt_hidden_garden_ids():
		var n := find_child(str(id), true, false)
		if n:
			n.visible = not on
	# 工作點／倉／已擺傢俬都喺花園中景，一併收埋
	if furniture_root and is_instance_valid(furniture_root):
		furniture_root.visible = not on
	if warehouse and is_instance_valid(warehouse):
		warehouse.visible = not on
	for sid in work_spots.keys():
		var spot = work_spots[sid]
		if spot and is_instance_valid(spot):
			spot.visible = not on
	# 花園角色／便便，同花園專用地板（狩獵場自己有 PrairieGround／PrairieTile）
	for id in ["Kid", "Visitor", "Ground256", "GroundAO"]:
		var actor := find_child(str(id), true, false)
		if actor:
			actor.visible = not on
	if poop_root and is_instance_valid(poop_root):
		poop_root.visible = not on
	for poop in find_children("Poop_*", "", true, false):
		poop.visible = not on


func set_garden_hidden_for_interior(on: bool) -> void:
	# 入屋近鏡：收埋整個花園（草地／天空／道具／佔位色塊），淨低室內同跟入去嘅寵物。
	var ids: Array = garden_cfg().get("hide_ids_in_interior", [])
	if ids.is_empty():
		ids = ["cottage", "tree", "lanterns", "fence", "bed", "lamp", "mushrooms", "can", "jar", "pot_L", "pot_R", "pot_S", "bush_bR", "trees_bR", "bush_bL", "bush_bL2", "trees_bL", "bg_sky", "bg_hills", "GroundTile", "Ground256", "GroundAO", "Warehouse", "Furniture", "Kid", "Visitor"]
	for id in ids:
		var n := find_child(str(id), true, false)
		if n:
			n.visible = not on
	if furniture_root and is_instance_valid(furniture_root):
		furniture_root.visible = not on
	if warehouse and is_instance_valid(warehouse):
		warehouse.visible = not on
	for sid in work_spots.keys():
		var spot = work_spots[sid]
		if spot and is_instance_valid(spot):
			spot.visible = not on
	if poop_root and is_instance_valid(poop_root):
		poop_root.visible = not on
	for poop in find_children("Poop_*", "", true, false):
		poop.visible = not on
	# 訪客／細佬：如果唔係跟入屋嘅 guest 就收埋
	for w in [kid, visitor]:
		if w and is_instance_valid(w) and w != _interior_guest:
			w.visible = not on
	_apply_interior_background(on)


func _apply_interior_background(on: bool) -> void:
	if env == null or env.environment == null:
		return
	var e := env.environment
	var col_a: Variant = GameData.m1d.get("interior", {}).get("bg_color", [0.14, 0.09, 0.07]) if GameData and "m1d" in GameData else [0.14, 0.09, 0.07]
	var warm := Color(0.14, 0.09, 0.07)
	if col_a is Array and col_a.size() >= 3:
		warm = Color(float(col_a[0]), float(col_a[1]), float(col_a[2]))
	if on:
		e.background_mode = Environment.BG_COLOR
		e.background_color = warm
		e.ambient_light_color = warm
		if _sky_mat:
			_sky_mat.sky_top_color = warm
			_sky_mat.sky_horizon_color = warm
			_sky_mat.ground_horizon_color = warm
			_sky_mat.ground_bottom_color = warm
	else:
		e.background_mode = Environment.BG_SKY
		# 交返 set_time_of_day 恢復晝夜色
		set_time_of_day(_tod if _tod != "" else "noon")


func furniture_zone(id: String, sl: String = "") -> String:
	if CollectionSystem and CollectionSystem.has_method("furniture_zone"):
		return CollectionSystem.furniture_zone(id, sl)
	return "indoor"


func _setup_interior() -> void:
	if interior_room and is_instance_valid(interior_room):
		return
	interior_room = InteriorRoom.new()
	add_child(interior_room)
	interior_room.setup()
	_setup_house_click()
	_setup_fade()


func _setup_house_click() -> void:
	var house_id := "cottage"
	if GameData and "m1d" in GameData:
		house_id = str(GameData.m1d.get("garden", {}).get("house_id", "cottage"))
	var house := find_child(house_id, true, false)
	if house == null:
		return
	_house_click = Area3D.new()
	_house_click.name = "HouseClick"
	_house_click.input_ray_pickable = true
	_house_click.collision_layer = 16
	_house_click.collision_mask = 0
	var cs := CollisionShape3D.new()
	var box := BoxShape3D.new()
	# 小屋 bounds 約 71×142×52；包實門同牆
	box.size = Vector3(72, 140, 56)
	cs.shape = box
	cs.position = Vector3(0, 70, 0)
	_house_click.add_child(cs)
	house.add_child(_house_click)


func _setup_fade() -> void:
	if _fade_rect and is_instance_valid(_fade_rect):
		return
	var layer := CanvasLayer.new()
	layer.name = "InteriorFade"
	layer.layer = 40
	add_child(layer)
	_fade_rect = ColorRect.new()
	_fade_rect.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_fade_rect.color = Color(0.05, 0.04, 0.04, 0.0)
	_fade_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(_fade_rect)


func cottage_door_world() -> Vector3:
	var house_id := "cottage"
	var door_local := Vector3(11.5, 24, 22)
	if GameData and "m1d" in GameData:
		var g: Dictionary = GameData.m1d.get("garden", {})
		house_id = str(g.get("house_id", "cottage"))
		var a: Variant = g.get("door_local", [11.5, 24, 22])
		if a is Array and a.size() >= 3:
			door_local = Vector3(float(a[0]), float(a[1]), float(a[2]))
	var house := find_child(house_id, true, false)
	if house is Node3D:
		return (house as Node3D).to_global(door_local)
	return Vector3(94.0, 24.0, -50.0)


func _pick_interior_guest() -> Walker:
	if follow_walker and is_instance_valid(follow_walker):
		return follow_walker
	var door := cottage_door_world()
	var best: Walker = pet
	var best_d := 1.0e9
	for w in [pet, kid]:
		if w == null or not is_instance_valid(w):
			continue
		var ww: Walker = w
		var d: float = ww.global_position.distance_to(door)
		if d < best_d:
			best_d = d
			best = ww
	return best


func enter_house(instant: bool = false, guest: Walker = null) -> void:
	if in_interior or in_hunt_view or interior_room == null:
		return
	if guest == null:
		guest = _pick_interior_guest()
	_interior_guest = guest
	if guest:
		_interior_guest_home = guest.global_position
	if instant:
		_cut_to_interior()
		if interior_room:
			interior_room.set_door_open(1.0)
		if AudioManager and AudioManager.has_method("set_interior_ambience"):
			AudioManager.set_interior_ambience(true)
		enter_interior.emit()
		return
	_interior_lock_cam = true
	_run_enter_transition()


func exit_house(instant: bool = false) -> void:
	if not in_interior:
		return
	if instant:
		_cut_to_garden()
		set_exterior_door(0.0)
		if AudioManager and AudioManager.has_method("set_interior_ambience"):
			AudioManager.set_interior_ambience(false)
		exit_interior.emit()
		return
	_interior_lock_cam = true
	_run_exit_transition()


func _run_enter_transition() -> void:
	if cam == null or interior_room == null:
		_cut_to_interior()
		return
	var fade_s := interior_room.fade_sec()
	var dolly_s := interior_room.dolly_sec()
	var open_s := interior_room.door_open_sec()
	var start_pos := cam.global_position
	var door := cottage_door_world()
	var dolly_pos := door + Vector3(0, 16, 70)
	_emit_audio_hook("door_open")
	door_open.emit()
	set_exterior_door(0.0)
	var tw := create_tween()
	tw.set_parallel(true)
	tw.tween_method(func(w: float):
		set_exterior_door(w)
	, 0.0, 1.0, open_s).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	tw.tween_method(func(w: float):
		if cam == null:
			return
		cam.global_position = start_pos.lerp(dolly_pos, w)
		if cam.global_position.distance_to(door) > 0.01:
			cam.look_at(door)
	, 0.0, 1.0, dolly_s).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tw.tween_method(func(a: float):
		if _fade_rect:
			var c := _fade_rect.color
			c.a = a
			_fade_rect.color = c
	, 0.0, 1.0, fade_s).set_delay(maxf(0.0, dolly_s - fade_s * 0.35))
	tw.set_parallel(false)
	tw.tween_callback(func():
		_cut_to_interior()
		if interior_room:
			interior_room.set_door_open(1.0)
		_emit_audio_hook("enter_interior")
		enter_interior.emit()
		if AudioManager and AudioManager.has_method("set_interior_ambience"):
			AudioManager.set_interior_ambience(true)
	)
	tw.tween_method(func(a: float):
		if _fade_rect:
			var c := _fade_rect.color
			c.a = a
			_fade_rect.color = c
	, 1.0, 0.0, fade_s)
	tw.tween_callback(func():
		_interior_lock_cam = false
		_place_cam(0.0)
	)


func _run_exit_transition() -> void:
	if cam == null or interior_room == null:
		_cut_to_garden()
		return
	var fade_s := interior_room.fade_sec()
	var close_s := interior_room.door_close_sec()
	_emit_audio_hook("exit_interior")
	exit_interior.emit()
	var tw := create_tween()
	tw.tween_method(func(a: float):
		if _fade_rect:
			var c := _fade_rect.color
			c.a = a
			_fade_rect.color = c
	, 0.0, 1.0, fade_s)
	tw.tween_callback(func():
		_cut_to_garden()
		set_exterior_door(1.0)
		if AudioManager and AudioManager.has_method("set_interior_ambience"):
			AudioManager.set_interior_ambience(false)
		_emit_audio_hook("door_close")
		door_close.emit()
	)
	tw.set_parallel(true)
	tw.tween_method(func(a: float):
		if _fade_rect:
			var c := _fade_rect.color
			c.a = a
			_fade_rect.color = c
	, 1.0, 0.0, fade_s)
	tw.tween_method(func(w: float):
		set_exterior_door(1.0 - w)
	, 0.0, 1.0, close_s).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN)
	tw.set_parallel(false)
	tw.tween_callback(func():
		_interior_lock_cam = false
		_place_cam(0.0)
	)


func _cut_to_interior() -> void:
	in_interior = true
	set_garden_hidden_for_interior(true)
	if interior_room:
		interior_room.visible = true
	var guest: Walker = _interior_guest
	if guest and is_instance_valid(guest) and interior_room:
		guest.global_position = interior_room.pet_enter_pos()
		guest.cancel_follow()
		guest.brain_driven = false
		guest.use_nav = true
		guest.in_interior = true
		guest.pause_t = 0.0
		if guest.agent and interior_room.nav_region:
			guest.agent.set_navigation_map(interior_room.nav_region.get_navigation_map())
		# 入屋後行兩步，顯得房間用得
		guest.go_to(interior_room.walk_point(rng if rng else RandomNumberGenerator.new()))
	if hud and hud.has_method("set_in_interior"):
		hud.set_in_interior(true)
	cam_mode = CamMode.OVERVIEW
	var mid_fade := _fade_rect != null and _fade_rect.color.a > 0.5
	_interior_lock_cam = false
	_place_cam(0.0)
	# 過渡中途切鏡：鏡頭已對準室內，鎖住直到 fade in 完
	if mid_fade:
		_interior_lock_cam = true


func _cut_to_garden() -> void:
	var guest: Walker = _interior_guest
	if guest and is_instance_valid(guest):
		var home := _interior_guest_home
		if home == Vector3.ZERO:
			home = cottage_door_world() + Vector3(0, 0, 36)
		home.y = 0
		guest.global_position = home
		guest.brain_driven = true
		guest.use_nav = true
		if guest.agent and nav_region:
			guest.agent.set_navigation_map(nav_region.get_navigation_map())
		guest.in_interior = false
		guest.pause_t = 0.4
	_interior_guest = null
	in_interior = false
	set_garden_hidden_for_interior(false)
	if interior_room:
		interior_room.visible = false
	if hud and hud.has_method("set_in_interior"):
		hud.set_in_interior(false)
	# 鏡頭先放喺屋門前，fade in 先再 _place_cam 拉回總覽
	var door := cottage_door_world()
	if cam:
		cam.global_position = door + Vector3(0, 28, 80)
		cam.look_at(door)
	cam_mode = CamMode.OVERVIEW



func _emit_audio_hook(key: String) -> void:
	var hook := key
	if GameData and "m1d" in GameData:
		hook = str(GameData.m1d.get("audio", {}).get("hooks", {}).get(key, "sfx_" + key))
	if AudioManager:
		AudioManager.play(hook)


func garden_cfg() -> Dictionary:
	if GameData and "m1d" in GameData:
		return GameData.m1d.get("garden", {})
	return {}


func _apply_cottage_exterior() -> void:
	var house := find_child("cottage", true, false)
	if house == null or not (house is Node3D):
		return
	var g := garden_cfg()
	var sc: Variant = g.get("cottage_scale", [2, 2, 2])
	if sc is Array and sc.size() >= 3:
		(house as Node3D).scale = Vector3(float(sc[0]), float(sc[1]), float(sc[2]))
	var pos: Variant = g.get("cottage_position", [82.5, 0, -94])
	if pos is Array and pos.size() >= 3:
		(house as Node3D).position = Vector3(float(pos[0]), float(pos[1]), float(pos[2]))
	if house is MeshInstance3D:
		var hmi := house as MeshInstance3D
		var hmat := hmi.material_override as StandardMaterial3D
		if hmat:
			hmat.cull_mode = BaseMaterial3D.CULL_DISABLED
	_widen_cottage_door(house as MeshInstance3D if house is MeshInstance3D else null, 28.0, 48.0)
	_make_exterior_door(house as Node3D)


func _widen_cottage_door(house: MeshInstance3D, unscaled_w: float, _unscaled_h: float) -> void:
	# 均勻 ×2 之後門洞只有 32 闊；改局部 x 令世界闊變成 56（28 局部）。鉸鏈中心維持 11.5。
	if house == null or house.mesh == null:
		return
	var am := house.mesh as ArrayMesh
	if am == null or am.get_surface_count() < 1:
		return
	var arr := am.surface_get_arrays(0)
	if arr.is_empty() or arr[Mesh.ARRAY_VERTEX] == null:
		return
	var verts: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
	var cx := 11.5
	var old_l := 3.5
	var old_r := 19.5
	var new_l := cx - unscaled_w * 0.5
	var new_r := cx + unscaled_w * 0.5
	var changed := false
	for i in range(verts.size()):
		var v := verts[i]
		# 只改前門洞兩框（z 近 19–22、y 喺門高之內），唔好郁上層前牆／屋頂
		if v.z < 18.5 or v.y > 48.5:
			continue
		if is_equal_approx(v.x, old_l) or absf(v.x - old_l) < 0.05:
			v.x = new_l
			verts[i] = v
			changed = true
		elif is_equal_approx(v.x, old_r) or absf(v.x - old_r) < 0.05:
			v.x = new_r
			verts[i] = v
			changed = true
	if not changed:
		return
	arr[Mesh.ARRAY_VERTEX] = verts
	var neu := ArrayMesh.new()
	neu.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	house.mesh = neu
	var cmat := house.material_override as StandardMaterial3D
	if cmat == null:
		cmat = StandardMaterial3D.new()
		if house.get_surface_override_material(0):
			cmat = house.get_surface_override_material(0) as StandardMaterial3D
		if cmat:
			house.material_override = cmat
	if cmat:
		cmat.cull_mode = BaseMaterial3D.CULL_DISABLED
		cmat.no_depth_test = false


func _make_exterior_door(house: Node3D) -> void:
	if house == null:
		return
	if _exterior_door and is_instance_valid(_exterior_door):
		_exterior_door.queue_free()
	var g := garden_cfg()
	# 局部未放大：闊 28、高 48，×2 之後 56×96。鉸鏈喺左邊框。
	var w := 28.0
	var h := 48.0
	var cx := 11.5
	var hinge_x := cx - w * 0.5
	var z := 20.5
	var pivot := Node3D.new()
	pivot.name = "ExteriorDoorPivot"
	pivot.position = Vector3(hinge_x, 0, z)
	house.add_child(pivot)
	var mi := MeshInstance3D.new()
	mi.name = "ExteriorDoor"
	var q := QuadMesh.new()
	q.size = Vector2(w, h)
	mi.mesh = q
	mi.position = Vector3(w * 0.5, h * 0.5, 0)
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	var tex: Texture2D = load("res://art/garden3d/H1/interior/meshes/door.png")
	if tex:
		mat.albedo_texture = tex
	else:
		mat.albedo_color = Color(0.58, 0.32, 0.18)
	mi.material_override = mat
	pivot.add_child(mi)
	_exterior_door = pivot
	set_exterior_door(0.0)


func set_exterior_door(weight: float) -> void:
	if _exterior_door == null or not is_instance_valid(_exterior_door):
		return
	# 0 關，1 開（向屋內 -Z 轉）
	_exterior_door.rotation_degrees.y = lerpf(0.0, 95.0, clampf(weight, 0.0, 1.0))


func _cottage_frame_points(house: Node3D) -> Array:
	# 屋頂、前簷、左右上角、門頂——近鏡頭嘅屋簷會比煙囪更高出畫面
	var locals: Array = [
		Vector3(0, 142, 0),
		Vector3(-35.5, 86.7, 26),
		Vector3(35.5, 86.7, 26),
		Vector3(-29.5, 94, 22),
		Vector3(29.5, 94, 22),
		Vector3(0, 130, 26),
		Vector3(11.5, 48, 22),
		Vector3(-29.5, 0, 22),
		Vector3(29.5, 0, 22),
	]
	var out: Array = []
	for p in locals:
		out.append(house.to_global(p))
	return out


func _cottage_out_of_frame(house: Node3D, vp: Vector2) -> bool:
	if cam == null:
		return false
	var pad_x := vp.x * 0.05
	var pad_y := vp.y * 0.10
	for p in _cottage_frame_points(house):
		if cam.is_position_behind(p):
			return true
		var sp: Vector2 = cam.unproject_position(p)
		if sp.y < pad_y or sp.y > vp.y - pad_y or sp.x < pad_x or sp.x > vp.x - pad_x:
			return true
	return false


func _ensure_cottage_roof_in_frame(yaw: float) -> void:
	var g := garden_cfg()
	if not bool(g.get("keep_roof_in_frame", true)):
		return
	var house := find_child("cottage", true, false)
	if house == null or cam == null:
		return
	var vp := get_viewport().get_visible_rect().size
	if vp.y <= 1.0:
		return
	# 屋 ×2 之後拉遠先可以見到成個屋頂；寵物可見身高保底 6%（M1a 10% 喺呢個尺度對唔上）
	for _i in range(12):
		if not _cottage_out_of_frame(house as Node3D, vp):
			break
		var prev := _cam_dist
		_cam_dist *= 1.05
		_apply_cam_offset(yaw, _obs_pitch, _cam_dist)
		_measure_cam_metrics()
		if _pet_h_frac < 0.06:
			_cam_dist = prev
			_apply_cam_offset(yaw, _obs_pitch, _cam_dist)
			_measure_cam_metrics()
			break


func is_portrait_window() -> bool:
	var vp := get_viewport().get_visible_rect().size if get_viewport() else Vector2.ZERO
	var win := get_window()
	if win:
		# 以視窗像素為準（桌面拉橫 852×393）
		vp = Vector2(win.size)
	return vp.y >= vp.x and vp.x > 0.0


func _setup_rotate_overlay() -> void:
	if _rotate_layer and is_instance_valid(_rotate_layer):
		return
	_rotate_layer = CanvasLayer.new()
	_rotate_layer.name = "RotatePortrait"
	_rotate_layer.layer = 80
	add_child(_rotate_layer)
	var root := Control.new()
	root.name = "RotateRoot"
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_STOP
	_rotate_layer.add_child(root)
	var bg := ColorRect.new()
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	bg.color = Color(0.07, 0.06, 0.05, 0.94)
	root.add_child(bg)
	var lab := Label.new()
	lab.name = "RotateLabel"
	lab.text = "請轉為直向"
	lab.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lab.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	lab.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var font: Font = load("res://art/fonts/GenWanMin2TC-R.subset.otf")
	if font:
		lab.add_theme_font_override("font", font)
	lab.add_theme_font_size_override("font_size", 28)
	lab.add_theme_color_override("font_color", Color(1.0, 0.96, 0.9))
	root.add_child(lab)
	_rotate_layer.visible = false


func _sync_rotate_overlay() -> void:
	# 橫向視窗唔好改 HUD 做橫版；只顯示請轉直向。
	var portrait := is_portrait_window()
	if _rotate_layer:
		_rotate_layer.visible = not portrait
	if hud:
		hud.visible = portrait
