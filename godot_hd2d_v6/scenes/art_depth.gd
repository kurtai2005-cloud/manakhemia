extends Node
## v6.4 art depth pass (art only — no renderer / perf / input / DOF code).
## - Cottage relief: window + door frames, door step, corner posts, tie beam,
##   bargeboards, eave fascia, ridge cap, chimney cap, stone plinth.
##   Every part carries per-vertex AO (dark where it meets the wall / ground),
##   so it reads in Low (no shadows, no SSAO) as well as High.
## - Edge / foreground grass tufts (MultiMesh cards, same cheap shader as v6).
## - Low mode: swaps the ground to a copy with the High sun shadows baked in
##   (textures/ground_composed_low.png), because Low has no sun shadows.
## - HD2D_BAKE_SHADOW=1 (box tool only): top-down orthographic shadow-mask capture.

var host: Node3D
var _ground_mat: ShaderMaterial
var _tex_high: Texture2D
var _tex_low: Texture2D
var _last_low := -1
var _mats := {}

const TIMBER := "res://textures/tiles/timber_b.png"
const STONE := "res://textures/tiles/cobble_a.png"


func _ready() -> void:
	if host == null:
		return
	var hde := OS.get_environment("HD2D_HEDGE").split(",", false)
	if hde.size() == 3:
		_hedge_warm = Vector3(float(hde[0]), float(hde[1]), float(hde[2]))
	var cde := OS.get_environment("HD2D_CLUMP").split(",", false)
	if cde.size() == 3:
		_clump_day = Vector3(float(cde[0]), float(cde[1]), float(cde[2]))
	var cot := host.get_node_or_null("cottage") as Node3D
	if cot:
		_build_cottage_relief(cot)
		_roof_tabs(cot)
		_ivy(cot)
	_outer_ring()  # v6.7: 360° tree + bush ring (the camera follows 團絨 anywhere)
	_canopy_clusters()  # v6.5 (replaces v6.4 _leaf_fringe); v6.7 leafy masses
	_fence_stakes()
	_edge_tufts()
	_edge_tufts_v615()
	_base_tufts()
	_trunks()
	_halos()
	_low_light()
	_backdrop_layers()
	var g := host.get_node_or_null("GroundInner") as MeshInstance3D
	if g and g.material_override is ShaderMaterial:
		_ground_mat = g.material_override as ShaderMaterial
		_tex_high = _ground_mat.get_shader_parameter("albedo_tex")
		if ResourceLoader.exists("res://textures/ground_composed_hi_v613.png") and OS.get_environment("HD2D_BAKE_SHADOW") != "1":
			_tex_high = load("res://textures/ground_composed_hi_v613.png")   # v6.13: lush green grade (v6.11: painted blob shade removed)
			_ground_mat.set_shader_parameter("albedo_tex", _tex_high)
		if ResourceLoader.exists("res://textures/ground_composed_low.png"):
			_tex_low = load("res://textures/ground_composed_low.png")
	_fg_frame()   # v6.7: after _ground_mat (near lawn copies the lawn lift)
	_ground_dapple()
	_flush_ao()
	call_deferred("_grab_shafts")
	if OS.get_environment("HD2D_BAKE_SHADOW") == "1":
		call_deferred("_setup_shadow_bake")
	print("art depth v6.18-pilot vc27 ready")


var _low_only: Array[Node3D] = []
var _haze_mats: Array[StandardMaterial3D] = []
var _halo_mat: StandardMaterial3D
var _backdrop_mat: StandardMaterial3D
var _day_only: Array[Node3D] = []
var _ray_mat: StandardMaterial3D
var _ray_low := true
var _fg_mat: StandardMaterial3D
var _fg_mats: Array[StandardMaterial3D] = []


var _clump_mats: Array[ShaderMaterial] = []
var _bed_fake := -1
# v6.12 mid-ground balance: the hedge / bush belt around the clearing read dark-green (PC rows
# 560–800 102 vs concept 121) → warm day lift on the unshaded clump cards (HD2D_CLUMP=r,g,b)
var _clump_day := Vector3(1.12, 1.07, 0.96)
# v6.13 lower mid: the hedge / bed-strip clumps around the clearing get a warm sunlit lift (HD2D_HEDGE=r,g,b)
var _hedge_warm := Vector3(1.62, 1.40, 0.86)   # PC r1: 1.42 too subtle on Mobile
var _frames := 0
# v6.7 world pass
const LEAFY := "res://textures/tiles/canopy_leafy_atlas.png"
const BUSHY := "res://textures/tiles/bush_leafy_atlas.png"
# v6.8 (Kurt: 粒粒波 → 一絲絲; one material, one method): canopy = leaf SPRAYS rooted inside the
# crown and rolled to point outward; bushes = SERRATED-leaf mounds; lawn = blade tile; sky = dome.
const SPRAY := "res://textures/tiles/canopy_spray_atlas_v615.png"   # v6.15 painterly interior, wispy outline kept (tools/canopy_soft_v6_15.py; v6.11 calm before)
const SERR := "res://textures/tiles/bush_serrated_atlas.png"
var _sky_sm: ShaderMaterial
var _dapple_sm: ShaderMaterial
# v6.9 dynamics: one cloud field drives ground cloud shadows, shafts, haze glow and sky sun glow
const CLOUD_SCALE := 560.0                 # wu per cloud-texture tile
const CLOUD_VEL := Vector2(5.2, 3.9)       # wu/s, along the shared wind direction (0.8, 0.6)
const CLOUD_AMT := 0.22                    # how much a cloud dims the sun
var _cloud_img: Image
var _light_now := 1.0
var _pet_lag := Vector3.ZERO
var _pet_lag_v := Vector3.ZERO
var _hybrid := false
var _sky_mi: MeshInstance3D
const NEW_SUN_DIR := Vector3(0.645, -0.616, 0.453)  # light travel; elevation 38°, azimuth 54.9° (from −Z toward −X = back-left). 50° tried: the main crown shadow lands on the clearing.
var _ring_spheres: Array = []      # [centre, r, ry, haze] virtual canopy spheres (outer ring)
var _ring_bushes: Array = []       # AABB of ring bushes
var _ring_cores: Array = []        # [centre, radius, y_scale] merged dark cores of ring bushes
var _ao_items: Array = []          # [Vector3 pos, float size]
var _rays: Array = []              # [MeshInstance3D, axis, centre, material, alpha_scale(Callable-free: 0 mine / 1 theirs), a0]
var _facing_sets: Array = []       # [MultiMesh, PackedVector3Array pos, PackedVector2Array size, stride]
var _reo_cam := Vector3.INF
var _reo_basis := Basis()
var _reo_i := 0
var _near_mi: MeshInstance3D
var _dapple_mi: MeshInstance3D
var _ring_sm: ShaderMaterial
const RING_YAW := 180.0  # hero view → the dark-crown side of the paint, gold glow upper-left


func _process(_dt: float) -> void:
	_frames += 1
	if _frames == 20:
		print("perf v6.8: draw_calls=", Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
			" objects=", Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME),
			" primitives=", Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME),
			" mode=", host.get("_mode"))
	if _frames == 18 and OS.get_environment("HD2D_DEBUG_PRIM") == "1":
		for n in _all(host):
			if n is GeometryInstance3D and (n as GeometryInstance3D).is_visible_in_tree():
				var tri := 0
				var mesh: Mesh = null
				var cnt := 1
				if n is MeshInstance3D:
					mesh = (n as MeshInstance3D).mesh
				elif n is MultiMeshInstance3D and (n as MultiMeshInstance3D).multimesh:
					mesh = (n as MultiMeshInstance3D).multimesh.mesh
					cnt = (n as MultiMeshInstance3D).multimesh.instance_count
				if mesh:
					for si in mesh.get_surface_count():
						var arr := mesh.surface_get_arrays(si)
						var ix = arr[Mesh.ARRAY_INDEX]
						tri += (ix.size() if ix != null else (arr[Mesh.ARRAY_VERTEX] as PackedVector3Array).size()) / 3
				if tri * cnt > 1500:
					print("prim ", n.get_path(), " ", tri * cnt)
	if _frames == 18 and OS.get_environment("HD2D_DEBUG_BIG") == "1":
		for n in _all(host):
			if n is MeshInstance3D and (n as MeshInstance3D).is_visible_in_tree():
				var mi := n as MeshInstance3D
				var bb := mi.get_aabb()
				var mt = mi.material_override if mi.material_override else (mi.mesh.surface_get_material(0) if mi.mesh and mi.mesh.get_surface_count() > 0 else null)
				var sp := ""
				if mt is ShaderMaterial and (mt as ShaderMaterial).shader:
					sp = (mt as ShaderMaterial).shader.resource_path
				elif mt:
					sp = mt.get_class()
				print("big ", mi.get_path(), " ", mi.mesh.get_class() if mi.mesh else "-", " ", bb.size.round(), " ", mi.global_position.round(), " ", sp)
	if _frames == 19 and OS.get_environment("HD2D_DEBUG_SHADOW") == "1":
		print("caster dump")
		for n in _all(host):
			if n is GeometryInstance3D and (n as GeometryInstance3D).is_visible_in_tree() and (n as GeometryInstance3D).cast_shadow != GeometryInstance3D.SHADOW_CASTING_SETTING_OFF:
				var bb := (n as GeometryInstance3D).get_aabb()
				if bb.size.length() > 20.0:
					print("caster ", n.get_path(), " ", bb.size, " ", (n as Node3D).global_position)
	var night := str(host.get("_mode")) == "night"
	# v6.15: per-frame forced bake sun removed — 遊程 v6.14-code bake_pass keeps the sun shadow ON itself.
	# v6.8 (black streaks in the sky, phone high_1 / high_2): 遊程's DappleCaster is a 600 wu
	# leaf-cookie plane at y 230, meant to be SHADOWS_ONLY. With the ground bake their policy
	# sets it to SHADOW_CASTING_SETTING_OFF, which makes it VISIBLE: black cookie blobs seen
	# almost edge-on above the trees. Hide it whenever it is not a shadows-only caster.
	if _frames == 3 or _frames == 12:
		_hide_voxel_crowns()   # some voxel trees are instanced after _ready
	if _frames == 12 and OS.get_environment("HD2D_DUMP_ZONE") == "1":
		for n in _all(host):
			if n is GeometryInstance3D and (n as Node3D).visible:
				var bb := (n as GeometryInstance3D).get_aabb()
				var c := (n as Node3D).global_transform * bb.get_center()
				if c.z > -115.0 and c.z < -35.0 and absf(c.x) < 130.0 and c.y < 40.0:
					var mo = (n as GeometryInstance3D).material_override
					var sp := ""
					if mo is ShaderMaterial and (mo as ShaderMaterial).shader:
						sp = (mo as ShaderMaterial).shader.resource_path
					print("ZONE ", n.get_path(), " ", c, " ", n.get_class(), " ", sp)
	var dcst := host.get_node_or_null("DappleCaster") as GeometryInstance3D
	if dcst:
		dcst.visible = dcst.cast_shadow == GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY and not _bake_mode
	if _sky_sm:
		_sky_sm.set_shader_parameter("light_mul", Vector3(0.07, 0.09, 0.17) if night else Vector3.ONE)
	if _gold_mats.is_empty():
		_gold_setup()
	for gm in _gold_mats:
		gm.set_shader_parameter("gold_amt", 0.0 if night else _gold_amt)
	if _near_gold_mat:
		_near_gold_mat.set_shader_parameter("fg_night_toe", 1.0 if night else 0.0)
		_near_gold_mat.set_shader_parameter("fg_dim", 1.0 if night else 0.86)   # r2: POOL_GAIN never reaches the crushed bottom band; stop night dim crush
	_apply_night_surface_toe(night)
	for cm in _clump_mats:
		cm.set_shader_parameter("light_mul", Vector3(0.26, 0.30, 0.46) if night else _clump_day)
		cm.set_shader_parameter("warm_gain", Vector3.ONE if night else _hedge_warm)
		cm.set_shader_parameter("warm_add", Vector3.ZERO if night else _envv3("HD2D_HEDGEADD", Vector3(0.050, 0.024, 0.003)))   # v6.14 Mobile hedge warmth (see clump_card)
	for hm in _haze_mats:
		if not hm.has_meta("a0"):
			hm.set_meta("a0", hm.albedo_color.a)
		var c := hm.albedo_color
		c.a = float(hm.get_meta("a0")) * (0.15 if night else 1.0)
		hm.albedo_color = c
	if _backdrop_mat:
		_backdrop_mat.albedo_color = Color(0.26, 0.30, 0.46) if night else Color.WHITE
	if _ring_sm:
		_ring_sm.set_shader_parameter("light_mul", Vector3(0.26, 0.30, 0.46) if night else Vector3.ONE)
	if _dapple_mi:
		_dapple_mi.visible = not night
	_dynamics(night, _dt)
	_low_fake_shadow(night)
	_grade_v611(night)
	if _frames == 3 or _frames == 10:
		_perf_tests(night)
	_walk_loop()
	_perf_log(_dt)
	_follow_camera(night)
	for fmat in _fg_mats:
		fmat.albedo_color = Color(0.26, 0.28, 0.42) if night else Color.WHITE
	for n in _day_only:
		n.visible = not night
	for n in _night_only:
		n.visible = night
	var sun := host.get("_sun") as DirectionalLight3D
	if sun:
		var low := str(host.get("_mode")) == "low"   # v6.9: Low may now have a live sun shadow
		for n in _low_only:
			n.visible = low and str(host.get("_mode")) != "night"
		_ray_low = low
		if _halo_mat:
			_halo_mat.albedo_color.a = 1.0 if str(host.get("_mode")) == "night" else (0.85 if low else 0.6)
	# Low mode has no sun shadows → show the ground with the sun shadows baked in.
	# v6.5 code: capture.gd keeps the bake on High as well (tree casters off).
	# Skip this swap so we do not overwrite that policy every frame.
	if host and host.get("_bake_shadow_ground"):
		return
	if _ground_mat == null or _tex_low == null:
		return
	if sun == null:
		return
	var lowi := 1 if str(host.get("_mode")) == "low" else 0
	if lowi != _last_low:
		_last_low = lowi
		_ground_mat.set_shader_parameter("albedo_tex", _tex_low if lowi == 1 else _tex_high)


# ------------------------------------------------------------------ materials
func _mat(key: String, tex_path: String, tile_wu: float, tint: Color) -> StandardMaterial3D:
	if _mats.has(key):
		return _mats[key]
	var m := StandardMaterial3D.new()
	m.albedo_texture = load(tex_path)
	m.albedo_color = tint
	m.vertex_color_use_as_albedo = true
	var np := tex_path.get_basename() + "_n.png"
	if ResourceLoader.exists(np):
		m.normal_enabled = true
		m.normal_texture = load(np)
		m.normal_scale = 0.8
	m.uv1_triplanar = true
	m.uv1_world_triplanar = true
	m.uv1_scale = Vector3.ONE / tile_wu
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	m.roughness = 1.0
	m.metallic = 0.0
	m.specular_mode = BaseMaterial3D.SPECULAR_DISABLED
	_mats[key] = m
	return m


# ------------------------------------------------------------------ geometry
## Box from local min/max. `ao` = faces of the box that touch something
## ("x-","x+","y-","y+","z-","z+"): vertices on those sides get darkened.
func _box(parent: Node3D, mn: Vector3, mx: Vector3, mat: Material, ao: Array, xf := Transform3D.IDENTITY, ao_k := 0.55) -> void:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	_box_into(st, mn, mx, ao, xf, ao_k)
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	mi.material_override = mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	parent.add_child(mi)


func _box_into(st: SurfaceTool, mn: Vector3, mx: Vector3, ao: Array, xf := Transform3D.IDENTITY, ao_k := 0.55) -> void:
	var c := [
		Vector3(mn.x, mn.y, mn.z), Vector3(mx.x, mn.y, mn.z), Vector3(mx.x, mx.y, mn.z), Vector3(mn.x, mx.y, mn.z),
		Vector3(mn.x, mn.y, mx.z), Vector3(mx.x, mn.y, mx.z), Vector3(mx.x, mx.y, mx.z), Vector3(mn.x, mx.y, mx.z)]
	var faces := [
		[[4, 5, 6, 7], Vector3(0, 0, 1)], [[1, 0, 3, 2], Vector3(0, 0, -1)],
		[[5, 1, 2, 6], Vector3(1, 0, 0)], [[0, 4, 7, 3], Vector3(-1, 0, 0)],
		[[7, 6, 2, 3], Vector3(0, 1, 0)], [[0, 1, 5, 4], Vector3(0, -1, 0)]]
	for f in faces:
		var idx: Array = f[0]
		var n: Vector3 = f[1]
		var col := []
		for i in idx:
			var v: Vector3 = c[i]
			var k := 1.0
			if "x-" in ao and is_equal_approx(v.x, mn.x): k = min(k, ao_k)
			if "x+" in ao and is_equal_approx(v.x, mx.x): k = min(k, ao_k)
			if "y-" in ao and is_equal_approx(v.y, mn.y): k = min(k, ao_k)
			if "y+" in ao and is_equal_approx(v.y, mx.y): k = min(k, ao_k)
			if "z-" in ao and is_equal_approx(v.z, mn.z): k = min(k, ao_k)
			if "z+" in ao and is_equal_approx(v.z, mx.z): k = min(k, ao_k)
			col.append(Color(k, k, k))
		for t in [[0, 1, 2], [0, 2, 3]]:
			for j in t:
				st.set_normal(xf.basis * n)
				st.set_color(col[j])
				st.add_vertex(xf * (c[idx[j]] as Vector3))


func _build_cottage_relief(cot: Node3D) -> void:
	var root := Node3D.new()
	root.name = "CottageRelief_v64"
	cot.add_child(root)
	var tim := _mat("timber", TIMBER, 16.0, Color(1.05, 0.92, 0.80))
	var trim := _mat("trim", TIMBER, 16.0, Color(1.35, 1.12, 0.86))   # lighter trim (window / door frame)
	var stone := _mat("stone", STONE, 64.0, Color(0.95, 0.92, 0.88))
	var F := 22.0  # front wall plane (+Z faces the camera)
	# Window frame (opening x -22.5..-4.5, y 52..72, recess to z=20)
	_box(root, Vector3(-24.5, 50.5, F), Vector3(-22.5, 74.0, F + 1.6), trim, ["z-"])
	_box(root, Vector3(-4.5, 50.5, F), Vector3(-2.5, 74.0, F + 1.6), trim, ["z-"])
	_box(root, Vector3(-25.5, 72.0, F), Vector3(-1.5, 75.0, F + 2.4), trim, ["z-", "y-"])   # lintel / drip cap
	_box(root, Vector3(-24.5, 50.0, F), Vector3(-2.5, 52.0, F + 1.0), trim, ["z-"])          # bottom rail on the flower box
	_box(root, Vector3(-14.25, 52.0, 20.0), Vector3(-12.75, 72.0, 20.8), trim, [])            # real mullion
	_box(root, Vector3(-22.5, 61.25, 20.0), Vector3(-4.5, 62.75, 20.8), trim, [])
	# Door frame (opening x 3.5..19.5, y 0..48, recess to z=19) + stone step
	_box(root, Vector3(1.5, 0.0, F), Vector3(3.5, 50.0, F + 1.6), trim, ["z-", "y-"])
	_box(root, Vector3(19.5, 0.0, F), Vector3(21.5, 50.0, F + 1.6), trim, ["z-", "y-"])
	_box(root, Vector3(0.5, 48.0, F), Vector3(22.5, 51.5, F + 2.4), trim, ["z-", "y-"])
	_box(root, Vector3(1.0, 0.0, F - 3.0), Vector3(22.0, 2.6, F + 5.0), stone, ["y-", "z-"])
	# Corner posts (stick out 1.5 wu past both walls), full wall height to the eave
	for sx in [-1.0, 1.0]:
		for sz in [-1.0, 1.0]:
			var cx: float = 29.5 * sx
			var cz: float = 22.0 * sz
			_box(root, Vector3(cx - 2.0, 0.0, cz - 2.0), Vector3(cx + 2.0, 93.0, cz + 2.0), tim, ["y-"])
	# Tie beam across the front and back gable base
	_box(root, Vector3(-31.5, 88.0, F), Vector3(31.5, 92.0, F + 2.0), tim, ["z-", "y-"])
	_box(root, Vector3(-31.5, 88.0, -F - 2.0), Vector3(31.5, 92.0, -F), tim, ["z+", "y-"])
	# Stone plinth around the base (gap for the door)
	_box(root, Vector3(-31.5, 0.0, F - 1.0), Vector3(1.5, 7.0, F + 1.8), stone, ["y-", "y+"])
	_box(root, Vector3(21.5, 0.0, F - 1.0), Vector3(31.5, 7.0, F + 1.8), stone, ["y-", "y+"])
	_box(root, Vector3(-31.5, 0.0, -F - 1.8), Vector3(31.5, 7.0, -F + 1.0), stone, ["y-", "y+"])
	_box(root, Vector3(28.5, 0.0, -F), Vector3(31.3, 7.0, F), stone, ["y-", "y+"])
	_box(root, Vector3(-31.3, 0.0, -F), Vector3(-28.5, 7.0, F), stone, ["y-", "y+"])
	# Bargeboards on both gables: sloped boards proud of the roof slab end (z = ±26)
	var ang := atan(43.3 / 35.5)
	var L := sqrt(35.5 * 35.5 + 43.3 * 43.3) + 3.0
	for gz in [26.0, -27.6]:
		for side in [-1.0, 1.0]:
			var mid := Vector3(side * 17.75, 107.5, 0.0)
			var b := Basis(Vector3(0, 0, 1), -side * ang)
			var xf := Transform3D(b, Vector3(mid.x, mid.y, gz))
			_box(root, Vector3(-L * 0.5, -3.6, 0.0), Vector3(L * 0.5, 2.2, 1.6), tim, ["z-" if gz > 0 else "z+"], xf)
	# Eave fascia boards along both side eaves
	for sx in [-1.0, 1.0]:
		var x0 := 35.5 if sx > 0 else -37.0
		_box(root, Vector3(x0, 82.6, -27.6), Vector3(x0 + 1.5, 87.4, 27.6), tim, ["x-" if sx > 0 else "x+"])
	# Ridge cap
	_box(root, Vector3(-2.6, 127.6, -27.8), Vector3(2.6, 132.2, 27.8), tim, ["y-"])
	# Chimney cap + soot-dark flue lip
	_box(root, Vector3(10.0, 142.0, -11.5), Vector3(21.0, 145.0, -0.5), stone, ["y-"])
	_box(root, Vector3(12.5, 145.0, -9.0), Vector3(18.5, 146.2, -3.0), _mat("soot", STONE, 64.0, Color(0.35, 0.32, 0.30)), [])
	print("cottage relief v6.4: ", root.get_child_count(), " parts")


# ------------------------------------------------------------------ tufts
func _path_d(p: Vector2) -> float:
	var path := [Vector2(0, 28), Vector2(8, 12), Vector2(18, -2), Vector2(30, -16), Vector2(44, -30), Vector2(58, -42), Vector2(70, -50), Vector2(96, -52)]
	var best := 1e9
	for i in path.size() - 1:
		var a: Vector2 = path[i]
		var b: Vector2 = path[i + 1]
		var ab := b - a
		var t := clampf((p - a).dot(ab) / ab.length_squared(), 0.0, 1.0)
		best = minf(best, p.distance_to(a + ab * t))
	return best


func _edge_tufts() -> void:
	if not host.has_method("_card_multimesh"):
		return
	var da: Array = []
	var db: Array = []
	var fg: Array = []
	var k := 0
	# along both path edges (outside the stones), every ~5 wu, alternating sides
	var path := [Vector2(0, 28), Vector2(8, 12), Vector2(18, -2), Vector2(30, -16), Vector2(44, -30), Vector2(58, -42), Vector2(70, -50), Vector2(96, -52)]
	for i in path.size() - 1:
		var a: Vector2 = path[i]
		var b: Vector2 = path[i + 1]
		var dir := (b - a).normalized()
		var nrm := Vector2(-dir.y, dir.x)
		var n := int(a.distance_to(b) / 5.0)
		for j in n:
			var p := a + (b - a) * (float(j) / float(max(n, 1)))
			for s in [-1.0, 1.0]:
				k += 1
				var q: Vector2 = p + nrm * s * (14.5 + 2.5 * fposmod(float(k) * 0.618, 1.0))
				if _path_d(q) < 13.0:
					continue
				(da if k % 2 == 0 else db).append(Vector3(q.x, q.y, float((k * 37) % 90)))
	# cottage wall base ring (world: cottage at 82.5,-72; walls ±29.5 / ±22 + plinth)
	for i in 26:
		var t := float(i) / 26.0
		var q := Vector2(82.5 - 33.0 + 66.0 * t, -72.0 + 25.5 + 1.5 * sin(t * 37.0))
		if q.x > 82.5 + 0.0 and q.x < 82.5 + 23.0:
			continue  # keep the door step clear
		(da if i % 2 == 0 else db).append(Vector3(q.x, q.y, float((i * 53) % 90)))
	for i in 14:
		var t := float(i) / 13.0
		for sx in [-1.0, 1.0]:
			var q: Vector2 = Vector2(82.5 + sx * 33.0, -72.0 - 22.0 + 44.0 * t)
			(db if i % 2 == 0 else da).append(Vector3(q.x, q.y, float((i * 29) % 90)))
	# fence base line and tree bases
	for i in 36:
		var q := Vector2(-118.0 + 5.0 * float(i), -52.0 + 2.5 + 1.2 * sin(float(i) * 2.3))
		if _path_d(q) < 14.0:
			continue
		(da if i % 3 != 0 else db).append(Vector3(q.x, q.y, float((i * 41) % 90)))
	for tr in [Vector3(-88, -44, 1.0), Vector3(-145, 10, 0.78), Vector3(165, -70, 0.82), Vector3(175, -130, 0.88)]:
		for i in 9:
			var a := float(i) / 9.0 * TAU
			var r: float = 12.0 * tr.z + 3.0 * fposmod(float(i) * 0.618, 1.0)
			da.append(Vector3(tr.x + cos(a) * r, tr.y + sin(a) * r, float(i * 40)))
	# foreground clumps (the bottom of the portrait frame was empty)
	var g := 1.32471795724474602596
	for i in 40:   # v6.7: fewer + smaller (walk-path views: big lone spindles on the lawn)
		var u := fposmod(0.5 + float(i) / g, 1.0)
		var v := fposmod(0.5 + float(i) / (g * g), 1.0)
		var q := Vector2(-140.0 + u * 300.0, 78.0 + v * 70.0)
		if _path_d(q) < 14.0:
			continue
		fg.append(Vector3(q.x, q.y, float((i * 61) % 90)))
	host.call("_card_multimesh", "res://textures/tiles/tuft_dark_a.png", da, 7.5)
	host.call("_card_multimesh", "res://textures/tiles/tuft_dark_b.png", db, 6.5)
	var fg_a: Array = []
	var fg_b: Array = []
	for i in fg.size():
		(fg_b if i % 7 == 0 else fg_a).append(fg[i])   # v6.10: fewer flowered tufts in the near lawn (concept: sparse)
	host.call("_card_multimesh", "res://textures/tiles/tuft_fg.png", fg_a, 7.0)
	host.call("_card_multimesh", "res://textures/tiles/tuft_fg_fl.png", fg_b, 8.0)
	print("edge tufts ", da.size() + db.size(), " foreground ", fg.size())


# ------------------------------------------------------------------ shadow bake (box tool)
func _setup_shadow_bake() -> void:
	_bake_mode = true
	# v6.6: 遊程's shadow policy turns tree casters off when a bake exists — the bake itself needs them.
	var tsn = host.get("_tree_shadow_nodes")
	if tsn is Array:
		for t in tsn:
			host.call("_tag_shadow", t, true)
	# v6.9 (Kurt: shadows are round blobs pasted on): NO proxy spheres / voxel domes in the
	# bake. The real leaf cards cast (alpha-cut atlas → leafy dappled edges, bush-shaped,
	# trunk-shaped), turned square-on to the sun so each card throws its true silhouette.
	for n in _all(host):
		if n is MeshInstance3D and (n as MeshInstance3D).mesh is ArrayMesh and str(n.name) == "tree" and (n as MeshInstance3D).get_aabb().size.y > 200.0:
			(n as MeshInstance3D).visible = false
		if n is MeshInstance3D and n.has_meta("core_cast"):
			(n as MeshInstance3D).visible = false
	# v6.11 (Kurt: far trees / hedges cast no shadow): in the bake every far tree / ring bush /
	# far-forest crown casts too (aerial-perspective lightening is done by the bake tool).
	var sunview := OS.get_environment("HD2D_BAKE_SUNVIEW") == "1"
	var far_on := 0
	for n in _all(host):
		if n is GeometryInstance3D and not n.has_meta("core_cast"):
			var pth := str(n.get_path())
			if pth.contains("FarForest") or pth.contains("OuterRing_v67") or str(n.name).begins_with("Clumps_") or pth.contains("Canopies"):
				if (n as GeometryInstance3D).cast_shadow == GeometryInstance3D.SHADOW_CASTING_SETTING_OFF:
					far_on += 1
				(n as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	print("bake v6.11 far casters enabled ", far_on)
	var sun_far := SUN_TO.normalized() * 100000.0
	for fs in _facing_sets:
		if fs.size() > 4:
			_reface(fs, sun_far)
	for n in _all(host):
		if n is MultiMeshInstance3D and str(n.name).begins_with("Clumps_"):
			(n as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	for n in _all(host):
		if n is GeometryInstance3D and n.name != "GroundInner" and (n as Node3D).visible:
			var gi := n as GeometryInstance3D
			if gi.cast_shadow != GeometryInstance3D.SHADOW_CASTING_SETTING_OFF:
				gi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
			else:
				gi.visible = false
		if n is Sprite3D:
			(n as Sprite3D).visible = false  # 團絨 moves; no baked pet shadow
		if n is GeometryInstance3D and _hy_dynamic(n) and OS.get_environment("HD2D_BAKE_PROPS") != "1":
			(n as GeometryInstance3D).visible = false   # v6.9: props / bending plants cast live, not baked
		# v6.10 HD2D_BAKE_PROPS=1: Low-without-live-shadow variant — props / fg plants baked too
	# v6.9: 遊程's DappleCaster (600 wu leaf-cookie plane, y 230) printed the ROUND blobs over
	# the whole bake (Kurt: "round blobs pasted on") → never in the bake; real leaves cast instead.
	var dc := host.get_node_or_null("DappleCaster") as Node3D
	if dc:
		dc.visible = false
	var dbg_hide := OS.get_environment("HD2D_BAKE_DBG_HIDE")
	if dbg_hide != "":
		for n in _all(host):
			if n is GeometryInstance3D and str(n.name).begins_with(dbg_hide):
				(n as Node3D).visible = false
	var g := host.get_node("GroundInner") as MeshInstance3D
	# v6.13 (Kurt: picket / lamp shadows): bed-top receiver pass — the receiving plane is raised
	# to the soil / frame top (HD2D_BAKE_RECV_Y, bed local y 6) and the beds hidden, so the sun
	# map shows exactly what falls ON the beds (pickets, lamp, cottage, trees). Used by
	# bed_flower.gdshader in Low (no live sun shadow).
	var recv_y := OS.get_environment("HD2D_BAKE_RECV_Y")
	if recv_y != "":
		g.position.y = float(recv_y)
		for n in _all(host):
			if n is GeometryInstance3D and host.has_method("_is_bed_node") and host.call("_is_bed_node", n):
				(n as GeometryInstance3D).visible = false
		print("bake v6.13 bed-top receiver y=", recv_y)
	var w := StandardMaterial3D.new()
	w.albedo_color = Color(0.5, 0.5, 0.5)
	w.roughness = 1.0
	w.specular_mode = BaseMaterial3D.SPECULAR_DISABLED
	g.material_override = w
	# v6.7 (D): bake with the raised sun (38° elevation, same azimuth) → shorter, softer shadows.
	var sun := host.get("_sun") as DirectionalLight3D
	if sun:
		# v6.10: 遊程's v6.9 policy turns the sun shadow OFF in a bake pass (bake_pass) → empty
		# bake. The bake tool needs it ON (High atlas / 2 splits / 450, as in v6.9; forced in _process).
		sun.shadow_enabled = true
		sun.basis = Basis.looking_at(NEW_SUN_DIR.normalized(), Vector3.UP)
		sun.shadow_blur = 0.2
		sun.light_angular_distance = 0.0   # 遊程's High soft-sun (1.8°) shows as blotchy noise in a bake
		# v6.11 (Kurt: shadows are not the objects' shapes): the v6.10 bake used the High atlas /
		# 2 splits / 450 → ~0.3 wu texels, stair-stepped and then blurred into blobs. One
		# orthogonal 8192 map over the bake frame → ~0.06 wu (inner) / 0.2 wu (wide) texels: the
		# engine's own shadow of every real mesh (same casters as High live), shape-exact.
		if OS.get_environment("HD2D_BAKE_HIRES") != "0":
			RenderingServer.directional_shadow_atlas_set_size(8192, true)
			sun.directional_shadow_mode = DirectionalLight3D.SHADOW_ORTHOGONAL
			sun.directional_shadow_max_distance = 1300.0 if OS.get_environment("HD2D_BAKE_WIDE") == "1" else 480.0
			sun.shadow_bias = 0.03
			sun.shadow_normal_bias = 0.6
		if "shadow_opacity" in sun:
			sun.set("shadow_opacity", 1.0)
	var wide := OS.get_environment("HD2D_BAKE_WIDE") == "1"
	if wide:
		var wp := MeshInstance3D.new()
		var pmw := PlaneMesh.new()
		pmw.size = Vector2(1000, 1000)
		wp.mesh = pmw
		var wmat := StandardMaterial3D.new()
		wmat.albedo_color = Color(0.5, 0.5, 0.5)
		wmat.roughness = 1.0
		wmat.specular_mode = BaseMaterial3D.SPECULAR_DISABLED
		wp.material_override = wmat
		wp.position = Vector3(0, -0.02, 0)
		wp.name = "BakeWidePlane"
		host.add_child(wp)
	var cam := host.get("_camera") as Camera3D
	cam.projection = Camera3D.PROJECTION_ORTHOGONAL
	cam.keep_aspect = Camera3D.KEEP_WIDTH
	cam.size = 900.0 if wide else 256.0   # v6.9: wide bake covers the back trees / undergrowth too
	cam.transform = Transform3D(Basis(Vector3.RIGHT, -PI * 0.5), Vector3(0, 420, 0))
	cam.far = 1200.0
	var env := host.get("_env") as Environment
	env.fog_enabled = false
	env.glow_enabled = false
	env.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	env.tonemap_exposure = 0.6
	_ground_mat = null
	if OS.get_environment("HD2D_BAKE_HEIGHT") == "1":
		# v6.9: caster height map (same framing) for contact-hardening + footprint AO
		var hm := ShaderMaterial.new()
		hm.shader = load("res://shaders/bake_height.gdshader")
		if OS.get_environment("HD2D_BAKE_FOOT") == "1":
			hm.set_shader_parameter("clip_y", 7.0)
		var blk := StandardMaterial3D.new()
		blk.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		blk.albedo_color = Color.BLACK
		for n in _all(host):
			if n is GeometryInstance3D and (n as Node3D).visible:
				var gi := n as GeometryInstance3D
				var foot := OS.get_environment("HD2D_BAKE_FOOT") == "1"
				if n.name == "GroundInner" or n.name == "BakeWidePlane" or gi.cast_shadow == GeometryInstance3D.SHADOW_CASTING_SETTING_OFF:
					gi.material_override = blk
				elif foot and n is MultiMeshInstance3D and gi.material_override is ShaderMaterial and str(n.name).begins_with("Clumps_"):
					gi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
					var fm := (gi.material_override as ShaderMaterial).duplicate() as ShaderMaterial
					fm.set_shader_parameter("foot_y", 12.0)
					gi.material_override = fm
				else:
					gi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
					gi.material_override = hm
		env.tonemap_exposure = 1.0
		env.adjustment_enabled = false
		env.background_mode = Environment.BG_COLOR
		env.background_color = Color.BLACK
	if OS.get_environment("HD2D_BAKE_ID") == "1":
		# v6.10 (Kurt: 影未必統一 — shadows should not all be one depth): caster CLASS map, same
		# framing. tools/bake_ground_v6_10.py marches each shadow texel to its occluder and reads
		# the class there → per-object shadow depth / softness / tint (shadow hierarchy).
		var cls_cols := {}
		for n in _all(host):
			if n is GeometryInstance3D and (n as Node3D).visible:
				var gi := n as GeometryInstance3D
				var col := Color.BLACK
				if n.name != "GroundInner" and n.name != "BakeWidePlane" and gi.cast_shadow != GeometryInstance3D.SHADOW_CASTING_SETTING_OFF:
					col = _bake_class_color(gi)
				var um: StandardMaterial3D = cls_cols.get(col)
				if um == null:
					um = StandardMaterial3D.new()
					um.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
					um.albedo_color = col
					um.cull_mode = BaseMaterial3D.CULL_DISABLED
					cls_cols[col] = um
				gi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				gi.material_override = um
		env.tonemap_mode = Environment.TONE_MAPPER_LINEAR
		env.tonemap_exposure = 1.0
		env.adjustment_enabled = false
		env.background_mode = Environment.BG_COLOR
		env.background_color = Color.BLACK
	if sunview:
		# v6.11 (Kurt: shadows must follow each object's real silhouette): orthographic camera
		# looking ALONG the 38° sun ray. On flat ground the shadow of anything is exactly its
		# silhouette seen from the sun, so tools/bake_ground_v6_11.py reprojects this coverage
		# image onto the ground grid: true roof / chimney / picket / leaf-gap shapes, no shadow-map
		# texel stair-steps, no blobs. Cards were turned square-on to the sun above.
		for n in _all(host):
			if n is GeometryInstance3D:
				var gi := n as GeometryInstance3D
				var nm := str(n.name)
				if nm == "GroundInner" or nm == "BakeWidePlane" or nm.begins_with("Ground") or nm.begins_with("BackdropRing") or nm.begins_with("NearLawn") or nm.begins_with("Sky"):
					gi.visible = false
				elif gi.cast_shadow == GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY:
					gi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
		var t := NEW_SUN_DIR.normalized()
		var ctr := Vector3.ZERO
		var vs := float(OS.get_environment("HD2D_SV_SIZE")) if OS.get_environment("HD2D_SV_SIZE") != "" else (1300.0 if wide else 380.0)
		cam.transform = Transform3D(Basis.looking_at(t, Vector3.UP), ctr - t * 2500.0)
		cam.size = vs
		cam.near = 10.0
		cam.far = 6000.0
		get_viewport().debug_draw = Viewport.DEBUG_DRAW_UNSHADED
		env.background_mode = Environment.BG_COLOR
		env.background_color = Color(1, 0, 1)
		env.tonemap_mode = Environment.TONE_MAPPER_LINEAR
		env.tonemap_exposure = 1.0
		env.adjustment_enabled = false
		env.glow_enabled = false
		env.fog_enabled = false
		env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
		var b := cam.global_transform.basis
		print("SUNVIEW o=%.4f,%.4f,%.4f x=%.6f,%.6f,%.6f y=%.6f,%.6f,%.6f size=%.3f" % [cam.global_transform.origin.x, cam.global_transform.origin.y, cam.global_transform.origin.z, b.x.x, b.x.y, b.x.z, b.y.x, b.y.y, b.y.z, vs])
	if OS.get_environment("HD2D_BAKE_LIST") == "1":
		for n in _all(host):
			if n is GeometryInstance3D and (n as Node3D).visible:
				var gi := n as GeometryInstance3D
				print("BL ", n.get_path(), " cs=", gi.cast_shadow)
	print("shadow bake camera ready")


# v6.10 bake class colours: canopy R, trunk G, cottage B, fence Y, bush M, prop C, post/lamp W
func _bake_class_color(gi: GeometryInstance3D) -> Color:
	var path := str(gi.get_path())
	var nm := str(gi.name)
	var ab := gi.get_aabb()
	var c := gi.global_transform * (ab.position + ab.size * 0.5)
	var sz := (gi.global_transform.basis * ab.size).abs()
	if nm.begins_with("Clumps_"):
		return Color(1, 0, 0) if c.y > 60.0 else Color(1, 0, 1)
	if path.contains("/cottage") or nm.begins_with("BrickWall") or nm == "PorchFloor" or nm == "TimberPost":
		return Color(0, 0, 1)
	if nm.begins_with("fence") or nm.begins_with("FenceStakes") or path.contains("/fence"):
		return Color(1, 1, 0)
	if nm == "lamp" or nm.begins_with("lantern") or path.contains("lantern"):
		return Color(1, 1, 1)
	if nm.begins_with("RingTrunks") or (sz.y > 100.0 and sz.x < 70.0) or (c.y > 45.0 and sz.y < 20.0):
		return Color(0, 1, 0)
	if nm.begins_with("tree") or nm.begins_with("trees_") or nm.begins_with("bush"):
		return Color(1, 0, 0) if c.y > 60.0 else Color(1, 0, 1)
	return Color(0, 1, 1)


func _all(n: Node) -> Array:
	var out := [n]
	for c in n.get_children():
		out.append_array(_all(c))
	return out



# ------------------------------------------------------------------ silhouettes
var _cam_pos := Vector3(12, 163, 190)
var _card_groups := {}  # key → [tex, haze, Array of [Transform3D, Color, Color(custom)]]


func _card(tex: String, haze: float, pos: Vector3, size: Vector2, nrm: Vector3, val: float) -> void:
	var key := "%s|%.2f" % [tex, haze]
	if not _card_groups.has(key):
		_card_groups[key] = [tex, haze, []]
	var fw := (_cam_pos - pos).normalized()
	var rt := Vector3.UP.cross(fw).normalized()
	var up := fw.cross(rt).normalized()
	var b := Basis(rt * size.x, up * size.y, fw)
	var n := nrm.normalized() * 0.5 + Vector3(0.5, 0.5, 0.5)
	(_card_groups[key][2] as Array).append([Transform3D(b, pos), Color(n.x, n.y, n.z, clampf(val / 1.5, 0.0, 1.0))])


func _flush_cards() -> void:
	var sh := load("res://shaders/leaf_card.gdshader") as Shader
	var total := 0
	for key in _card_groups:
		var g: Array = _card_groups[key]
		var items: Array = g[2]
		var q := QuadMesh.new()
		q.size = Vector2.ONE
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.use_colors = true
		mm.mesh = q
		mm.instance_count = items.size()
		for i in items.size():
			mm.set_instance_transform(i, items[i][0])
			mm.set_instance_color(i, items[i][1])
		var mat := ShaderMaterial.new()
		mat.shader = sh
		mat.set_shader_parameter("albedo_tex", load(g[0]))
		mat.set_shader_parameter("haze_amt", g[1])
		var mmi := MultiMeshInstance3D.new()
		mmi.multimesh = mm
		mmi.material_override = mat
		mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		host.add_child(mmi)
		_clump_mats.append(mat)   # v6.13: gets warm_gain (hedge / bed-strip lift); light_mul / push are not leaf_card params → ignored
		total += items.size()
	_card_groups.clear()
	print("silhouette cards ", total)


func _leaf_fringe() -> void:
	# Break every leaf ball's round outline: leafy alpha-cut clumps around its screen-space
	# rim (+ a few on top), hanging strands under big canopies. Deterministic layout.
	var cam := host.get("_camera") as Camera3D
	if cam:
		_cam_pos = cam.global_position
	var cam_pos := _cam_pos
	var clumps := ["res://textures/tiles/leaf_clump_a.png", "res://textures/tiles/leaf_clump_b.png", "res://textures/tiles/leaf_clump_c.png"]
	var k := 0
	for n in _all(host):
		if not (n is MeshInstance3D):
			continue
		var mi := n as MeshInstance3D
		if not (mi.mesh is SphereMesh) or not (mi.material_override is ShaderMaterial):
			continue
		var t = (mi.material_override as ShaderMaterial).get_shader_parameter("albedo_tex")
		if t == null or not (t as Texture2D).resource_path.contains("leaf_"):
			continue
		var hv = (mi.material_override as ShaderMaterial).get_shader_parameter("haze_amt")
		var haze: float = 0.0 if hv == null else float(hv)
		var xf := mi.global_transform
		var c := xf.origin
		var r := (mi.mesh as SphereMesh).radius * xf.basis.get_scale().x
		var ry := (mi.mesh as SphereMesh).radius * xf.basis.get_scale().y * 0.9
		var v := (cam_pos - c).normalized()
		var u1 := v.cross(Vector3.UP).normalized()
		var u2 := u1.cross(v).normalized()
		var cnt := clampi(int(r / 3.2), 5, 14)
		if haze > 0.12:
			cnt = maxi(4, cnt / 2)
		for i in cnt:
			k += 1
			var th := float(i) / float(cnt) * TAU + fposmod(float(k) * 0.618, 1.0) * 0.6
			var d := (u1 * cos(th) * r + u2 * sin(th) * ry)
			var dn := (u1 * cos(th) + u2 * sin(th)).normalized()
			var sz := r * (0.55 + 0.35 * fposmod(float(k) * 0.414, 1.0))
			var p := c + d * (0.98 + 0.12 * fposmod(float(k) * 0.29, 1.0)) + v * r * 0.2
			# screen upper-left = toward the sun → backlit, brighter rim clumps
			var lit := clampf(0.5 * sin(th) - 0.5 * cos(th), -1.0, 1.0)
			var val := 0.95 + 0.30 * lit + 0.10 * fposmod(float(k) * 0.73, 1.0)
			_card(clumps[k % 3], haze, p, Vector2(sz, sz), dn + v * 0.4 + Vector3.UP * 0.3, val)
		# a couple on the visible face so the ball surface is not a smooth sphere
		for i in 5:
			k += 1
			var a := fposmod(float(k) * 0.618, 1.0) * TAU
			var rr2 := 0.25 + 0.45 * fposmod(float(k) * 0.37, 1.0)
			var p2 := c + v * r * 0.85 + (u1 * cos(a) + u2 * sin(a)) * r * rr2
			var lit2 := clampf(0.6 * sin(a) - 0.4 * cos(a), -1.0, 1.0)
			_card(clumps[(k + 1) % 3], haze, p2, Vector2(r * 0.45, r * 0.45), v + Vector3.UP * 0.4, 1.0 + 0.25 * lit2)
		if mi.get_parent().name.begins_with("Bush_"):
			# r2: hedge top highlight — two sun-caught clumps on the crown
			for i in 2:
				k += 1
				var tp := c + Vector3(0, ry * 0.82, 0) + u1 * r * (0.35 * float(i * 2 - 1)) + v * r * 0.35
				_card(clumps[k % 3], haze, tp, Vector2(r * 0.55, r * 0.4), Vector3.UP + v * 0.3, 1.35)
		if r > 16.0 and haze < 0.01:
			for i in 3:
				k += 1
				var hx := (fposmod(float(k) * 0.618, 1.0) - 0.5) * 1.4 * r
				var hp := c - u2 * ry * 0.92 + u1 * hx + v * r * 0.3 + Vector3(0, -r * 0.18, 0)
				_card("res://textures/tiles/leaf_hang.png", haze, hp, Vector2(r * 0.16, r * 0.42), v - Vector3.UP * 0.3, 0.8)
	_flush_cards()


func _roof_tabs(cot: Node3D) -> void:
	# Ragged roof edge: shingle tips of varied length along both eaves and both gable edges.
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var ang := atan(43.3 / 35.5)
	var k := 0
	for side in [-1.0, 1.0]:
		var d := Vector3(side * cos(ang), -sin(ang), 0)       # down the slope, outward
		var nrm := Vector3(side * sin(ang), cos(ang), 0)
		var eave := Vector3(side * 35.5, 86.7, 0)
		var z := -27.0
		while z < 27.0:
			k += 1
			var ln := 2.0 + 2.2 * fposmod(float(k) * 0.618, 1.0)
			var w := 3.0 + 0.8 * fposmod(float(k) * 0.37, 1.0)
			var b := Basis(d, nrm, Vector3(0, 0, 1)).rotated(nrm, (fposmod(float(k) * 0.29, 1.0) - 0.5) * 0.25)
			var o := eave + Vector3(0, 0, z + w * 0.5) - d * 1.0
			_box_into(st, Vector3(0, -1.3, -w * 0.5 + 0.25), Vector3(ln + 1.0, 0.0, w * 0.5 - 0.25), ["y-"], Transform3D(b, o), 0.6)
			z += w
		# gable edges (front + back): tips proud of the bargeboard, following the slope
		for gz in [1.0, -1.0]:
			var t := 0.04
			while t < 0.98:
				k += 1
				var p := Vector3(side * 35.5 * (1.0 - t), 86.7 + 43.3 * t, gz * 27.4)
				var ln2 := 1.2 + 1.6 * fposmod(float(k) * 0.618, 1.0)
				var b2 := Basis(Vector3(0, 0, gz), nrm, Vector3(0, 0, gz).cross(nrm)).orthonormalized()
				var len_s := 3.4
				var xf := Transform3D(Basis(d.cross(Vector3(0, 0, 1)).normalized() * -side, nrm, Vector3(0, 0, 1)), p)
				_box_into(st, Vector3(-len_s * 0.5 + 0.3, -1.2, 0.0 if gz > 0 else -ln2), Vector3(len_s * 0.5 - 0.3, 0.2, ln2 if gz > 0 else 0.0), ["z-" if gz > 0 else "z+"], xf, 0.6)
				t += len_s / 56.0
	var mi := MeshInstance3D.new()
	mi.name = "RoofTabs_v64"
	mi.mesh = st.commit()
	mi.material_override = _mat("rooftab", "res://textures/tiles/roof_b.png", 32.0, Color(1.0, 0.95, 0.9))
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	cot.add_child(mi)


func _ivy(cot: Node3D) -> void:
	# Ivy clumps climbing the front-left corner post and spilling over the window corner,
	# breaking the straight wall edges (the atlas ivy stays as the flat base).
	var gx := cot.global_position
	var k := 0
	for i in 16:
		k += 1
		var y := 4.0 + float(i) * 5.6
		var x := -30.0 + (fposmod(float(k) * 0.618, 1.0) - 0.4) * 5.0
		var sz := 6.0 + 4.0 * fposmod(float(k) * 0.41, 1.0)
		_card("res://textures/tiles/ivy_clump.png", 0.0, gx + Vector3(x, y, 23.6), Vector2(sz, sz), Vector3(-0.4, 0.3, 1.0), 0.9 + 0.2 * fposmod(float(k) * 0.7, 1.0))
	for i in 5:
		k += 1
		_card("res://textures/tiles/ivy_clump.png", 0.0, gx + Vector3(-24.0 + float(i) * 2.6, 74.0 + float(i % 2) * 2.5, 24.6), Vector2(6, 6), Vector3(0, 0.5, 1), 1.0)
	_card("res://textures/tiles/leaf_hang.png", 0.0, gx + Vector3(-23.0, 66.0, 24.8), Vector2(3, 10), Vector3(0, 0.2, 1), 0.85)
	_card("res://textures/tiles/leaf_hang.png", 0.0, gx + Vector3(-30.5, 86.0, 24.5), Vector2(3, 11), Vector3(0, 0.2, 1), 0.85)
	_flush_cards()


func _fence_stakes() -> void:
	# Fence line (z = -52): a few taller / leaning stakes so the top edge is not one straight line.
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var xs := [-112.0, -91.0, -63.0, -38.0, -9.0, 19.0, 47.0]
	for i in xs.size():
		var h := 15.0 + 6.0 * fposmod(float(i) * 0.618 + 0.2, 1.0)
		var tilt := (fposmod(float(i) * 0.37, 1.0) - 0.5) * 0.18
		var b := Basis(Vector3(0, 0, 1), tilt)
		_box_into(st, Vector3(-1.3, 0, -1.3), Vector3(1.3, h, 1.3), ["y-"], Transform3D(b, Vector3(xs[i], 0, -50.5)), 0.5)
		_box_into(st, Vector3(-0.9, h, -0.9), Vector3(0.9, h + 1.4, 0.9), [], Transform3D(b, Vector3(xs[i], 0, -50.5)))
	var mi := MeshInstance3D.new()
	mi.name = "FenceStakes_v64"
	mi.mesh = st.commit()
	mi.material_override = _mat("stake", TIMBER, 16.0, Color(1.2, 1.0, 0.82))
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	host.add_child(mi)


func _base_tufts() -> void:
	# Grass tufts at the base of every prop so nothing looks pasted onto the lawn.
	var objs: Array = []
	var f := FileAccess.open("res://art/props_v6_4.json", FileAccess.READ)
	if f:
		for e in JSON.parse_string(f.get_as_text()):
			objs.append(Vector3(float(e[0]), float(e[1]), minf(float(e[2]), 18.0)))
	var a: Array = []
	var b: Array = []
	var k := 0
	for o in objs:
		var n := 5 if o.z < 12 else 9
		for i in n:
			k += 1
			var th := float(i) / float(n) * TAU + float(k) * 0.37
			var r: float = o.z + 1.5 + 1.5 * fposmod(float(k) * 0.618, 1.0)
			var q := Vector2(o.x + cos(th) * r, o.y + sin(th) * r * 0.7)
			if _path_d(q) < 12.0:
				continue
			(a if k % 2 == 0 else b).append(Vector3(q.x, q.y, float((k * 47) % 90)))
	host.call("_card_multimesh", "res://textures/tiles/tuft_dark_a.png", a, 6.0)
	host.call("_card_multimesh", "res://textures/tiles/tuft_dark_b.png", b, 5.5)
	print("base tufts ", a.size() + b.size())



# ------------------------------------------------------------------ dressing (gap list 1,3,7,8,10)
func _unshaded(tex: String, add: bool, a := 1.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.albedo_texture = load(tex)
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	m.albedo_color = Color(1, 1, 1, a)
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	if add:
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
		m.no_depth_test = false
		m.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_DISABLED
	else:
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
		m.alpha_scissor_threshold = 0.5
	return m


func _facing_mm(mat: Material, items: Array, nm: String) -> MultiMeshInstance3D:
	# items: [pos, size(Vector2)] → camera-facing quads (CPU-oriented)
	var q := QuadMesh.new()
	q.size = Vector2.ONE
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.mesh = q
	mm.instance_count = items.size()
	for i in items.size():
		var pos: Vector3 = items[i][0]
		var sz: Vector2 = items[i][1]
		var fw := (_cam_pos - pos).normalized()
		var rt := Vector3.UP.cross(fw).normalized()
		var up := fw.cross(rt).normalized()
		mm.set_instance_transform(i, Transform3D(Basis(rt * sz.x, up * sz.y, fw), pos))
	var pp := PackedVector3Array()
	var ss := PackedVector2Array()
	for it in items:
		pp.append(it[0])
		ss.append(it[1])
	_facing_sets.append([mm, pp, ss, 12])  # v6.7: re-faced when the camera follows 團絨
	var mmi := MultiMeshInstance3D.new()
	mmi.name = nm
	mmi.multimesh = mm
	mmi.material_override = mat
	mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	host.add_child(mmi)
	return mmi


const TREES := [Vector4(-88, -44, 1.0, 0), Vector4(-145, 10, 0.78, 12), Vector4(165, -70, 0.82, -8), Vector4(175, -130, 0.88, 0)]


func _trunks() -> void:
	# Thicker red-brown trunks with root flare, vertical grooves (bark_a, world triplanar),
	# ivy climbing the camera side, mushroom birdhouse + hanging lantern on the main tree.
	var bark := _bark_mat()
	for t in TREES:
		var s: float = t.z
		var base := Vector3(t.x, 0, t.y)
		var mi := MeshInstance3D.new()
		mi.mesh = _groove_trunk(14.5 * s, 10.5 * s, 150.0 * s, int(t.w) + 3)
		mi.material_override = bark
		mi.position = base
		host.add_child(mi)
		_register_tree_caster(mi)
		# ivy up the camera side
		var k := int(t.w) + 7
		for i in 9:
			k += 1
			var y := 8.0 * s + float(i) * 12.0 * s
			var ang := (fposmod(float(k) * 0.618, 1.0) - 0.5) * 1.6
			var rr := lerpf(14.5, 10.5, y / (150.0 * s)) * s + 1.0
			var p := base + Vector3(sin(ang) * rr, y, cos(ang) * rr)
			var sz := (7.0 + 4.0 * fposmod(float(k) * 0.41, 1.0)) * s
			_card("res://textures/tiles/ivy_clump.png", 0.0, p, Vector2(sz, sz), Vector3(sin(ang), 0.3, cos(ang)), 0.85 + 0.25 * fposmod(float(k) * 0.7, 1.0))
	_flush_cards()
	# mushroom birdhouse on the main (left) tree, facing the camera
	var m0: Vector4 = TREES[0]
	var front := Vector3(m0.x + 3.0, 0, m0.y + 13.0)
	var body := CylinderMesh.new()
	body.top_radius = 4.2
	body.bottom_radius = 4.8
	body.height = 8.0
	body.radial_segments = 8
	var bmi := MeshInstance3D.new()
	bmi.mesh = body
	bmi.material_override = _mat("bh_body", TIMBER, 16.0, Color(1.35, 1.2, 0.95))
	bmi.position = front + Vector3(0, 82, 2)
	host.add_child(bmi)
	_register_tree_caster(bmi)  # v6.6: on the tree → baked, not a hard live shadow
	var cap := CylinderMesh.new()
	cap.top_radius = 0.6
	cap.bottom_radius = 7.5
	cap.height = 5.0
	cap.radial_segments = 8
	var cmi := MeshInstance3D.new()
	cmi.mesh = cap
	cmi.material_override = _mat("bh_cap", "res://textures/tiles/roof_b.png", 24.0, Color(1.25, 0.62, 0.5))
	cmi.position = front + Vector3(0, 88.5, 2)
	host.add_child(cmi)
	_register_tree_caster(cmi)  # v6.6: on the tree → baked, not a hard live shadow
	var hole := MeshInstance3D.new()
	var hq := QuadMesh.new()
	hq.size = Vector2(2.4, 2.4)
	hole.mesh = hq
	var hm := StandardMaterial3D.new()
	hm.albedo_color = Color(0.08, 0.05, 0.04)
	hm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	hole.material_override = hm
	hole.position = front + Vector3(0, 82.5, 6.9)
	host.add_child(hole)
	# trunk lantern (hook + box), lit by a halo in _halos()
	var lan := Vector3(m0.x - 9.0, 58.0, m0.y + 12.0)
	var lb := MeshInstance3D.new()
	var lbx := BoxMesh.new()
	lbx.size = Vector3(4, 6, 4)
	lb.mesh = lbx
	var lm := StandardMaterial3D.new()
	lm.albedo_color = Color(1.0, 0.78, 0.4)
	lm.emission_enabled = true
	lm.emission = Color(1.0, 0.66, 0.28)
	lm.emission_energy_multiplier = 1.4
	lb.material_override = lm
	lb.position = lan
	host.add_child(lb)
	_register_tree_caster(lb)  # v6.6: on the tree → baked, not a hard live shadow
	_extra_lights.append(lan)


var _extra_lights: Array[Vector3] = []


func _halos() -> void:
	# String-light / lamp halos that read in Low too: unshaded additive billboard per bulb.
	var pts: Array[Vector3] = []
	for id in ["lanterns", "lamp"]:
		var node := host.get_node_or_null(id)
		if node == null:
			continue
		var ep := "res://art/meshes/%s_emissive.png" % id
		if not ResourceLoader.exists(ep):
			continue
		var img := (load(ep) as Texture2D).get_image()
		if img.is_compressed():
			img.decompress()
		var cells := {}
		for n in _all(node):
			if not (n is MeshInstance3D):
				continue
			var mi := n as MeshInstance3D
			var arr := mi.mesh.surface_get_arrays(0)
			var vs: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			var uvs: PackedVector2Array = arr[Mesh.ARRAY_TEX_UV]
			for i in vs.size():
				var u := uvs[i]
				var px := clampi(int(u.x * img.get_width()), 0, img.get_width() - 1)
				var py := clampi(int(u.y * img.get_height()), 0, img.get_height() - 1)
				if img.get_pixel(px, py).v < 0.5:
					continue
				var w := mi.global_transform * vs[i]
				var key := Vector3i(floori(w.x / 6.0), floori(w.y / 6.0), floori(w.z / 6.0))
				if not cells.has(key):
					cells[key] = [Vector3.ZERO, 0]
				cells[key][0] += w
				cells[key][1] += 1
		for key in cells:
			pts.append((cells[key][0] as Vector3) / float(cells[key][1]))
	# merge near-duplicates
	var merged: Array[Vector3] = []
	for p in pts:
		var dup := false
		for q in merged:
			if p.distance_to(q) < 5.0:
				dup = true
				break
		if not dup:
			merged.append(p)
	for e in _extra_lights:
		merged.append(e)
	var items: Array = []
	for p in merged:
		var big := p.y < 75.0  # lamp head / trunk lantern: bigger halo than string bulbs
		items.append([p + (_cam_pos - p).normalized() * 3.0, Vector2.ONE * (18.0 if big else 11.0)])
	_halo_mat = _unshaded("res://textures/tiles/halo_soft.png", true, 0.85)
	_facing_mm(_halo_mat, items, "Halos_v64")
	print("halos ", items.size())
	_night_pools(merged)


# v6.10 (GAPS PL, night): warm light pools on the ground under the string bulbs, the lamp, the
# window and the door. Omni lights alone gave weak pools (Mobile: ≤ 8 lights per mesh and long
# radius = faint). Cheap HD-2D way: one additive MultiMesh of smooth ground-lying pools, night
# only, sized / weighted by each light's height and power. 1 draw at night, 0 by day.
var _night_only: Array[Node3D] = []


# v6.10 r2b: PC Mobile night (HDR + exposure + glow) amplifies additive pools far more than the
# box preview; r1/r2 read as a flat beige slab. Gain calibrated on the PC (HD2D_POOL_GAIN test).
var _pool_gain := 0.5   # PC r2c: 0 = none, 0.22 = barely, 0.5 = soft warm pool, no slab

func _night_pools(bulbs: Array[Vector3]) -> void:
	if OS.get_environment("HD2D_POOL_GAIN") != "":
		_pool_gain = float(OS.get_environment("HD2D_POOL_GAIN"))
	var items: Array = []   # [pos, size Vector2, alpha]
	var bi := 0
	for b in bulbs:
		bi += 1
		if b.y > 75.0 and bi % 2 == 0:
			continue        # v6.10 r2b: every other string bulb (overlap stacked into a flat slab)
		if b.y > 75.0:      # string bulbs: broad, faint, overlapping into a warm band on the open lawn
			var hsh := fposmod(b.x * 0.137 + b.y * 0.071, 1.0)
			var sz := clampf(b.y * 0.62, 60.0, 96.0) * (0.85 + 0.3 * hsh)
			items.append([Vector3(b.x + 8.0, 0.35, b.z + 22.0 + 26.0 * hsh), Vector2(sz, sz * (0.6 + 0.25 * hsh)), 0.028 + 0.014 * hsh])   # v6.10 r2: PC Mobile HDR+glow blew r1 pools to white → ~1/4
		else:               # lamp head / trunk lantern
			items.append([Vector3(b.x + 4.0, 0.35, b.z + 12.0), Vector2(100.0, 80.0), 0.13])
	items.append([Vector3(72.0, 0.35, 4.0), Vector2(76.0, 44.0), 0.11])     # window → lawn in front of the bed
	items.append([Vector3(94.0, 0.35, -36.0), Vector2(44.0, 28.0), 0.09])   # door / porch
	items.append([Vector3(126.0, 0.35, -64.0), Vector2(44.0, 60.0), 0.09])  # side window
	var q := QuadMesh.new()
	q.size = Vector2.ONE
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_colors = true
	mm.mesh = q
	mm.instance_count = items.size()
	for i in items.size():
		var p: Vector3 = items[i][0]
		var sz: Vector2 = items[i][1]
		mm.set_instance_transform(i, Transform3D(Basis(Vector3(sz.x, 0, 0), Vector3(0, 0, -sz.y), Vector3(0, 1, 0)), p))
		mm.set_instance_color(i, Color(1.0, 0.60, 0.28, float(items[i][2]) * _pool_gain))
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.albedo_texture = load("res://textures/tiles/pool_soft_v610.png")
	m.vertex_color_use_as_albedo = true
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_DISABLED
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.render_priority = -1   # v6.10 r2b: before 團絨 / props (r2 PC: the additive pools washed over the pet)
	var mmi := MultiMeshInstance3D.new()
	mmi.name = "NightPools_v610"
	mmi.multimesh = mm
	mmi.material_override = m
	mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	host.add_child(mmi)
	_night_only.append(mmi)
	print("v6.10 night pools ", items.size())


func _low_light() -> void:
	# Warm ray strips fanning from the sun gap (Low and High; High at lower alpha) + Low motes.
	# v6.7 (0.6.6 phone high_1: rays seen edge-on as grey-white bands when the camera moved):
	# every ray is an AXIS billboard — its long axis stays fixed (sun anchor → floor), its face
	# turns to the camera every frame — and fades out when viewed along the axis.
	var rays := Node3D.new()
	rays.name = "LowRays_v64"
	host.add_child(rays)
	var sun_anchor := Vector3(-40, 420, -440)
	# v6.8 (phone high_2: a grey-white band across the left trees when 團絨 walks left): the rays
	# stood in the garden (z −130..−280) and crossed the near trees once the camera panned.
	# Now all rays stand behind the garden (z ≤ −270), and fade with camera distance as well.
	var centres := [Vector3(-30, 150, -380), Vector3(40, 140, -400), Vector3(110, 160, -410), Vector3(-90, 135, -360), Vector3(170, 150, -420)]   # v6.10: along SUN_TO, upper ends in the open sky
	for i in centres.size():
		# v6.10: soft multi-beam shader (shaders/light_shaft.gdshader) instead of the flat strip
		var rm := ShaderMaterial.new()
		rm.shader = load("res://shaders/light_shaft.gdshader")
		rm.set_shader_parameter("seed", float(i) * 1.37 + 0.4)
		rm.set_shader_parameter("tint", Color(1.0, 0.76, 0.42))
		rm.set_shader_parameter("energy", 1.0)
		rm.set_shader_parameter("sky_cloud", load("res://textures/tiles/sky_cloud_v611.png"))   # v6.11 born in cloud gaps
		# v6.10: beams run along the REAL sun vector (38°, back-left) — v6.9 aimed them at a point
		# straight above, so they stood as vertical columns in the middle of the sky.
		var axis := SUN_TO.normalized()
		var q := QuadMesh.new()
		q.size = Vector2(90.0 + 30.0 * float(i % 3), 500.0)   # v6.10 r2: narrower cards; v6.11: longer — the top end sits inside the clouds
		var mi := MeshInstance3D.new()
		mi.mesh = q
		mi.material_override = rm
		mi.position = centres[i]
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		rays.add_child(mi)
		_rays.append([mi, axis, centres[i], rm, 0, 1.0])
	_day_only.append(rays)
	var items: Array = []
	for i in 60:
		var f1 := fposmod(float(i) * 0.618034, 1.0)
		var f2 := fposmod(float(i) * 0.414214, 1.0)
		var f3 := fposmod(float(i) * 0.754878, 1.0)
		items.append([Vector3(-180.0 + 330.0 * f1, 15.0 + 120.0 * f2, -170.0 + 260.0 * f3), Vector2.ONE * (1.2 + 1.2 * f2)])
	var motes := _facing_mm(_unshaded("res://textures/tiles/mote.png", true, 0.9), items, "LowMotes_v64")
	_low_only.append(motes)


func _grab_shafts() -> void:
	# 遊程's High light-shaft cards (capture.gd _setup_fx) had the same fixed orientation → the
	# grey-white diagonal bands in high_1. Their look (colour / alpha / size) is kept; only the
	# facing is driven here (axis billboard + grazing fade), from the art layer. Note to 遊程.
	var sh := host.get_node_or_null("Shafts")
	if sh == null:
		return
	for c in sh.get_children():
		if c is MeshInstance3D:
			var mi := c as MeshInstance3D
			var a0 := 0.15
			if mi.material_override is ShaderMaterial:
				var av = (mi.material_override as ShaderMaterial).get_shader_parameter("alpha")
				if av != null:
					a0 = float(av)
			# v6.8: their x −260..−100, z −117..−247 cards crossed the left tree line when the
			# camera panned left (phone high_2) → pushed back behind the garden (z ≤ −270).
			if mi.position.z > -270.0:
				mi.position.z = -270.0 - fposmod(mi.position.x * 0.37, 1.0) * 70.0
			# v6.10: same colour / alpha, soft multi-beam shader (their flat strips read as hard bands)
			var sm2 := ShaderMaterial.new()
			sm2.shader = load("res://shaders/light_shaft.gdshader")
			sm2.set_shader_parameter("seed", float(_rays.size()) * 2.11 + 0.9)
			sm2.set_shader_parameter("tint", Color(1.0, 0.86, 0.62))
			sm2.set_shader_parameter("energy", 1.0)
			sm2.set_shader_parameter("alpha", a0)
			sm2.set_shader_parameter("sky_cloud", load("res://textures/tiles/sky_cloud_v611.png"))
			mi.material_override = sm2
			if mi.mesh is QuadMesh:
				(mi.mesh as QuadMesh).size.x = maxf((mi.mesh as QuadMesh).size.x * 1.7, 40.0)
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			_rays.append([mi, mi.basis.y.normalized(), mi.position, sm2, 1, a0 * 1.6 * 1.4])   # v6.12: ×1.4
	print("v6.8 shafts axis-billboarded (pushed behind the garden) ", sh.get_child_count())


func _backdrop_layers() -> void:
	# v6.7: the painted forest on a 360° inward cylinder (r 462, centred on the garden) instead
	# of one flat board — no camera position / yaw sees an edge-on card, a black streak or the
	# end of the world. Bottom at y −30 (meets the lawn), seam behind the camera (+Z).
	var cy := CylinderMesh.new()
	cy.top_radius = 462.0
	cy.bottom_radius = 462.0
	cy.height = 420.0   # v6.8: forest band only (y −30..390); the sky dome is above / behind it
	cy.radial_segments = 64
	cy.rings = 1
	cy.cap_top = false
	cy.cap_bottom = false
	var mi := MeshInstance3D.new()
	mi.name = "BackdropRing_v67"
	mi.mesh = cy
	var m := ShaderMaterial.new()
	m.shader = load("res://shaders/backdrop_ring.gdshader")
	m.set_shader_parameter("tex", load("res://textures/tiles/backdrop_ring_v68.png"))  # v6.8: forest only, sky cut out
	m.set_shader_parameter("haze_amt", _ring_haze)   # v6.11
	m.set_shader_parameter("repeats", 1.0)
	mi.material_override = m
	mi.position = Vector3(0, 180.0, 0)
	mi.rotation_degrees = Vector3(0, RING_YAW, 0)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	host.add_child(mi)
	_ring_sm = m
	_sky_dome()
	_haze_glow()


func _hide_voxel_crowns() -> void:
	for n in _all(host):
		if n is MeshInstance3D and (n as MeshInstance3D).mesh is ArrayMesh and str(n.name) == "tree":
			var tbb := (n as MeshInstance3D).global_transform * (n as MeshInstance3D).get_aabb()
			if (n as MeshInstance3D).get_aabb().size.y > 200.0:   # local size (trees are scaled); v6.9: also in the bake
				(n as MeshInstance3D).visible = false
				n.set_meta("core_cast", true)
		if n is MeshInstance3D and (str(n.name) == "trees_bL" or str(n.name) == "trees_bR") and n.has_meta("core_cast"):
			(n as MeshInstance3D).visible = false


var _bake_mode := false


func _sky_dome() -> void:
	# v6.8 (Kurt: black in the sky, weird seam mid-sky, wants white clouds / a detailed sky):
	# ONE continuous sky: an inward sphere that rides with the camera, painted clouds
	# (AI base ai_sky_v68.jpg → toned + palette clean-up) mapped by view direction. The image
	# spans the front 200° (sun glow → upper-left, where our sun is); the back 160° is the
	# mirrored image, so the wrap is continuous and the fold sits outside any ±45° yaw.
	# The flat bg_sky board is hidden (its edge was the mid-sky seam).
	var bg := host.get_node_or_null("bg_sky") as Node3D
	if bg:
		bg.visible = false
	var sp := SphereMesh.new()
	sp.radius = 1500.0
	sp.height = 3000.0
	sp.radial_segments = 24
	sp.rings = 12
	var mi := MeshInstance3D.new()
	mi.name = "SkyDome_v68"
	mi.mesh = sp
	var m := ShaderMaterial.new()
	m.shader = load("res://shaders/sky_dome.gdshader")
	m.set_shader_parameter("tex", load("res://textures/tiles/sky_v69.png"))  # v6.9: toward the concept's golden haze
	m.set_shader_parameter("sky_cloud", load("res://textures/tiles/sky_cloud_v611.png"))   # v6.11 rim light
	mi.material_override = m
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.extra_cull_margin = 4000.0
	host.add_child(mi)
	_sky_sm = m
	_sky_mi = mi


func _ground_at(cam: Camera3D, sp: Vector2) -> Vector3:
	var vp := host.get_viewport().get_visible_rect().size
	var o := cam.project_ray_origin(sp * vp)
	var d := cam.project_ray_normal(sp * vp)
	if absf(d.y) < 1e-4:
		return Vector3(INF, 0, 0)
	return o + d * (-o.y / d.y)


func _fg_frame() -> void:
	# v6.7 (Kurt: the two front sprays float in mid-air / hide 團絨): no screen-space cards.
	# Real planted plants: 3 crossed cards each, rooted 1.5 wu into the soil, soft contact
	# shadow + soil + grass at the foot, lit like the lawn, depth-written (correct occlusion
	# with the pet), outside the walk bounds (z > 90) so they frame the bottom corners of the
	# default view and stay low enough never to cover 團絨 when the camera follows it.
	var cam := host.get("_camera") as Camera3D
	if cam == null:
		return
	var spots := [[Vector2(0.10, 0.95), 34.0], [Vector2(0.92, 0.93), 30.0], [Vector2(-0.02, 0.83), 26.0], [Vector2(1.02, 0.80), 24.0]]
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var tufts: Array = []
	var k := 0
	var placed := 0
	for sp in spots:
		var g := _ground_at(cam, sp[0])
		if g.x == INF:
			continue
		g.z = maxf(g.z, 100.0)
		var sz: float = sp[1]
		placed += 1
		if OS.get_environment("HD2D_FG_LIST") == "1":
			print("fg plant ", g, " sz ", sz)
		for j in 3:
			k += 1
			var yaw := deg_to_rad(float(j) * 60.0 + float(k * 23 % 40))
			var rt := Vector3(cos(yaw), 0, -sin(yaw)) * sz * 0.5
			var b0 := g + Vector3(0, -1.5, 0)
			var top := Vector3(0, sz, 0)
			var ph := Color(fposmod(float(placed) * 0.37, 1.0), 0, 0)
			var quad := [[b0 - rt, Vector2(0, 1)], [b0 + rt, Vector2(1, 1)], [b0 + rt + top, Vector2(1, 0)],
				[b0 - rt, Vector2(0, 1)], [b0 + rt + top, Vector2(1, 0)], [b0 - rt + top, Vector2(0, 0)]]
			for qv in quad:
				st.set_color(ph)
				st.set_uv(qv[1])
				st.set_normal(Vector3.UP)
				st.add_vertex(qv[0])
		_ao_items.append([g, sz * 1.3])
		for j in 7:
			k += 1
			var a := float(j) / 7.0 * TAU + float(k) * 0.3
			var rr := sz * (0.30 + 0.12 * fposmod(float(k) * 0.618, 1.0))
			tufts.append(Vector3(g.x + cos(a) * rr, g.z + sin(a) * rr * 0.7, float(k * 37 % 90)))
	var mi := MeshInstance3D.new()
	mi.name = "FgPlants_v67"
	mi.mesh = st.commit()
	var fm := ShaderMaterial.new()
	fm.shader = load("res://shaders/fg_plant.gdshader")
	fm.set_shader_parameter("albedo_tex", load("res://textures/tiles/fg_plant_a.png"))
	mi.material_override = fm
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	mi.set_meta("hy_dyn", true)   # v6.9: bends with 團絨 → live shadow (not baked)
	host.add_child(mi)
	host.call("_card_multimesh", "res://textures/tiles/tuft_dark_a.png", tufts, 8.0)
	# sparse bottom-third interest: flowered tufts, world-placed from the default view
	var fl_pts: Array = []
	var fspots := [Vector2(0.18, 0.74), Vector2(0.40, 0.80), Vector2(0.58, 0.74), Vector2(0.70, 0.92),
		Vector2(0.88, 0.76), Vector2(0.48, 0.95), Vector2(0.26, 0.82), Vector2(0.64, 0.84)]
	for sp in fspots:
		var g := _ground_at(cam, sp)
		if g.x != INF:
			fl_pts.append(Vector3(g.x, g.z, float(int(g.x * 13.0) % 90)))
	host.call("_card_multimesh", "res://textures/tiles/tuft_fg_fl.png", fl_pts, 8.0)
	_near_lawn()
	print("fg frame v6.7: planted plants ", placed, ", flowers ", fl_pts.size())


func _near_lawn() -> void:
	# v6.7 near-field lawn base: fine 4 px/wu blades × smooth macro colour of the real ground
	# (tools/near_lawn_v6_7.py). r3: the plane rides with the camera (any pet position / yaw);
	# the shader fades it by horizontal distance from the camera. 1 draw.
	var pm := PlaneMesh.new()
	pm.size = Vector2(440.0, 440.0)
	var mi := MeshInstance3D.new()
	mi.name = "NearLawn_v67"
	mi.mesh = pm
	var m := ShaderMaterial.new()
	m.shader = load("res://shaders/near_lawn.gdshader")
	m.set_shader_parameter("macro_tex", load("res://textures/near_macro.png"))
	m.set_shader_parameter("detail_tex", load("res://textures/tiles/lawn_fine_detail.png"))
	# v6.8 (Kurt 0.6.7: blurry brown-yellow mush at the bottom): colour blade tile (individual
	# blades, tufts, clover, patches) carries the lawn; the macro only shades it (bake shadows).
	m.set_shader_parameter("blade_tex", load("res://textures/tiles/lawn_blades_v614.png"))   # v6.14 clumped blades with real value depth (tools/lawn_depth_v6_14.py)
	m.set_shader_parameter("region", Vector4(-340.0, -120.0, 340.0, 330.0))
	m.set_shader_parameter("near_d", 140.0)
	_near_gold_mat = m   # v6.15: baked gold patches (see _gold_setup)
	m.set_shader_parameter("fg_warm", _envv3("HD2D_FGWARM", Vector3(1.24, 1.04, 0.74)))   # v6.16 warm bottom band
	m.set_shader_parameter("fg_hi_cut", _envf_ad("HD2D_FGCUT", 0.30))   # v6.14: 0.55 → 0.30 so the sunlit tufts / golden pools survive near the camera
	m.set_shader_parameter("fade_len", 80.0)   # long dithered hand-over: no line where it meets the ground
	if _tex_low:
		m.set_shader_parameter("ground_tex", _tex_low)   # vc27: night radiance uses the inner bake
	if _ground_mat:
		for p in ["lawn_gain", "lawn_center", "lawn_radius", "lawn_tint", "pool_edge", "pool_r", "pool_core"]:
			var v = _ground_mat.get_shader_parameter(p)
			if v != null:
				m.set_shader_parameter(p, v)
	# v6.14: the ground's pool params may be set after this copy → set them here too (same env / defaults)
	m.set_shader_parameter("pool_edge", _envv3("HD2D_POOL", Vector3(0.72, 0.74, 0.84)))
	m.set_shader_parameter("pool_core", _envv3("HD2D_POOLC", Vector3(1.60, 1.34, 0.86)))
	m.set_shader_parameter("pool_r", Vector2(0.40, 1.05))
	m.set_shader_parameter("pool_off", Vector2(18.0, -18.0))
	mi.material_override = m
	mi.position = Vector3(12.0, 0.08, 190.0)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	host.add_child(mi)
	_near_mi = mi


func _ground_dapple() -> void:
	# v6.7 (H): moving leaf-light synced to the wind (shaders/ground_dapple.gdshader), plus the
	# wide-bake tree shadows on the outer lawn. 1 blended draw, hidden at night.
	var pm := PlaneMesh.new()
	pm.size = Vector2(920.0, 880.0)
	var mi := MeshInstance3D.new()
	mi.name = "GroundDapple_v67"
	mi.mesh = pm
	var m := ShaderMaterial.new()
	m.shader = load("res://shaders/ground_dapple.gdshader")
	m.set_shader_parameter("dapple", load("res://textures/tiles/dapple_leaf.png"))
	if ResourceLoader.exists("res://textures/shadow_wide_mask_v615.png"):
		m.set_shader_parameter("wide_mask", load("res://textures/shadow_wide_mask_v615.png"))   # v6.15: + soft canopy sun breaks (tools/sun_gold_v6_15.py)
	m.set_shader_parameter("wide_half", 450.0)
	m.set_shader_parameter("shade_col", Color(0.10, 0.11, 0.19))   # v6.9: cool blue-violet sky fill, never black
	m.set_shader_parameter("static_amt", 0.34)   # v6.10: the wide mask now carries per-object depth
	m.set_shader_parameter("ring_h", load("res://textures/tiles/ring_height_v610.png"))
	m.set_shader_parameter("ring_yaw", deg_to_rad(RING_YAW))
	m.render_priority = -1
	mi.material_override = m
	mi.position = Vector3(0, 0.2, -40.0)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	host.add_child(mi)
	_dapple_mi = mi
	_dapple_sm = m


func _flush_ao() -> void:
	# soft contact shadows under ring trees, bushes and planted plants (1 blended draw)
	# v6.9 (Kurt: round blobs pasted on): the round AO discs are gone — contact AO is now baked
	# from the real footprints (tools/bake_ground_v6_9.py) into the ground and the wide mask.
	if _ao_items.is_empty() or not AO_DISCS:
		return
	var q := QuadMesh.new()
	q.size = Vector2.ONE
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.mesh = q
	mm.instance_count = _ao_items.size()
	for i in _ao_items.size():
		var p: Vector3 = _ao_items[i][0]
		var sz: float = _ao_items[i][1]
		mm.set_instance_transform(i, Transform3D(Basis(Vector3(sz, 0, 0), Vector3(0, 0, -sz * 0.8), Vector3(0, 1, 0)), Vector3(p.x, 0.14, p.z)))
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.albedo_texture = load("res://textures/tiles/contact_ao.png")
	m.albedo_color = Color(1, 1, 1, 0.55)
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_DISABLED
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR
	m.render_priority = -2
	var mmi := MultiMeshInstance3D.new()
	mmi.name = "ContactAO_v67"
	mmi.multimesh = mm
	mmi.material_override = m
	mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	host.add_child(mmi)
	print("v6.7 contact AO ", _ao_items.size())


func _outer_ring() -> void:
	# v6.7 360° dressing: a ring of trees (merged grooved trunks, leafy canopy masses) and bushes
	# outside the walk bounds (x −140..150, z −110..90) so no pet position / yaw shows an edge.
	var root := Node3D.new()
	root.name = "OuterRing_v67"
	host.add_child(root)
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var trees: Array = []
	var k := 0
	for side in [-1.0, 1.0]:
		var z := -330.0
		while z < 240.0:
			k += 1
			var x: float = side * (250.0 + 70.0 * fposmod(float(k) * 0.618034, 1.0))
			trees.append(Vector3(x, z, 0.8 + 0.35 * fposmod(float(k) * 0.414214, 1.0)))
			z += 62.0 + 30.0 * fposmod(float(k) * 0.7548, 1.0)
	for e in [Vector3(-200, 300, 1.0), Vector3(205, 310, 0.95), Vector3(-60, 360, 1.1), Vector3(90, 370, 1.0)]:
		trees.append(e)
	# r15: six outer-ring trunks sit in the combined RingTrunks mesh and cover the
	# farm sign / right approach and the workshop lower-left entry. Split only those
	# out, same bark and caster policy, and park them on the back edge of that yard.
	var ring_shift := {
		5: ["RingTrunk_FarmRightBack_k6", Vector2(-299.6, 49.7), Vector2(-188.0, -130.0)],
		6: ["RingTrunk_FarmRightBack_k7", Vector2(-272.8, 127.5), Vector2(-248.0, -240.0)],
		7: ["RingTrunk_FarmRightBack_k8", Vector2(-316.1, 198.0), Vector2(-175.0, -95.0)],
		13: ["RingTrunk_ShopLeftBack_k14", Vector2(295.7, 55.4), Vector2(240.0, -230.0)],
		14: ["RingTrunk_ShopLeftBack_k15", Vector2(268.9, 134.4), Vector2(190.0, -320.0)],
		15: ["RingTrunk_ShopLeftBack_k16", Vector2(312.2, 206.1), Vector2(270.0, -150.0)],
	}
	var bark := _bark_mat()
	var idx := 0
	for t in trees:
		var s: float = t.z
		var base := Vector3(t.x, 0, t.y)
		var h := 120.0 * s
		var tm := _groove_trunk(11.0 * s, 8.0 * s, h, k, 12, 6)
		if ring_shift.has(idx):
			var spec: Array = ring_shift[idx]
			var was: Vector2 = spec[1]
			var nxt: Vector2 = spec[2]
			if Vector2(base.x, base.z).distance_to(was) > 2.0:
				push_error("r15 ring shift missed %s at %s" % [spec[0], base])
				st.append_from(tm, 0, Transform3D(Basis(), base))
			else:
				base = Vector3(nxt.x, 0.0, nxt.y)
				var mi := MeshInstance3D.new()
				mi.name = str(spec[0])
				mi.mesh = tm
				mi.material_override = bark
				mi.position = base
				mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
				root.add_child(mi)
				_register_tree_caster(mi)
				print("r15 ring relocate ", spec[0], " from ", was, " to ", nxt)
		else:
			st.append_from(tm, 0, Transform3D(Basis(), base))
		idx += 1
		k += 1
		var lobes := [Vector4(0, h + 16.0 * s, 0, 36.0 * s), Vector4(-24.0 * s, h - 6.0 * s, 6.0 * s, 25.0 * s), Vector4(22.0 * s, h - 2.0 * s, -8.0 * s, 26.0 * s)]
		for lb in lobes:
			var c := base + Vector3(lb.x, lb.y, lb.z)
			_ring_spheres.append([c, lb.w, lb.w * 0.85, 0.0, true])
			# hidden caster sphere for the shadow bake (shown only by the bake tool)
			var cs := MeshInstance3D.new()
			var sm := SphereMesh.new()
			sm.radius = lb.w * 0.9
			sm.height = lb.w * 1.6
			sm.radial_segments = 10
			sm.rings = 5
			cs.mesh = sm
			cs.position = c
			cs.visible = false
			cs.set_meta("core_cast", true)
			root.add_child(cs)
			_ring_cores.append([c, lb.w * 0.70, 0.85])
		_ao_items.append([base, 30.0 * s])
	var tr := MeshInstance3D.new()
	tr.name = "RingTrunks_v67"
	tr.mesh = st.commit()
	tr.material_override = bark
	root.add_child(tr)
	_register_tree_caster(tr)
	# v6.8 (Kurt 0.6.7 low_2 / high_2: bushes in straight rows): organic CLUSTERS of 1–4 bushes
	# of mixed size, scattered round a jittered centre, irregular gaps between clusters, kept
	# outside the walk bounds (|x| ≥ 170).
	var bk := 0
	for side in [-1.0, 1.0]:
		var z: float = -236.0 + 14.0 * side
		while z < 200.0:
			bk += 1
			var ccx: float = side * (184.0 + 70.0 * fposmod(float(bk) * 0.618, 1.0))
			var nb := 1 + int(fposmod(float(bk) * 0.7548, 1.0) * 2.99)
			for j in nb:
				bk += 1
				var w := 16.0 + 26.0 * fposmod(float(bk) * 0.414, 1.0)
				var hh := 10.0 + 18.0 * fposmod(float(bk) * 0.7548, 1.0)
				var ang := fposmod(float(bk) * 0.381966, 1.0) * TAU
				var rr := 26.0 * sqrt(fposmod(float(bk) * 0.29, 1.0)) * (0.0 if j == 0 else 1.0)
				var x: float = ccx + cos(ang) * rr
				if absf(x) < 172.0:
					x = side * (344.0 - absf(x))   # reflect off the walk edge (no clamped line)
				var zz: float = z + sin(ang) * rr * 1.3
				var wide := fposmod(float(bk) * 0.57, 1.0) > 0.5
				var sx := w if wide else w * 0.7
				var sz2 := w * 0.7 if wide else w
				_ring_bushes.append(AABB(Vector3(x - sx * 0.5, 0, zz - sz2 * 0.5), Vector3(sx, hh, sz2)))
				_ring_cores.append([Vector3(x, hh * 0.45, zz), minf(hh, w * 0.35) * 0.7, 0.8])
			z += 70.0 + 90.0 * fposmod(float(bk) * 0.17, 1.0)
	# back undergrowth (z −330..−430): the far lawn read as an empty field up to the backdrop
	var x2 := -430.0
	while x2 < 430.0:
		bk += 1
		var w2 := 46.0 + 24.0 * fposmod(float(bk) * 0.414, 1.0)
		var h2 := 26.0 + 18.0 * fposmod(float(bk) * 0.7548, 1.0)
		var z2 := -345.0 - 70.0 * fposmod(float(bk) * 0.618, 1.0)
		if Vector2(x2, z2).length() < 452.0:
			_ring_bushes.append(AABB(Vector3(x2 - w2 * 0.5, 0, z2 - w2 * 0.25), Vector3(w2, h2, w2 * 0.5)))
			_ring_cores.append([Vector3(x2, h2 * 0.45, z2), minf(h2, w2 * 0.3) * 0.8, 0.8])
		x2 += w2 * (0.55 + 1.3 * fposmod(float(bk) * 0.33, 1.0))  # v6.8: irregular gaps (clusters)
	print("v6.8 outer ring trees ", trees.size(), " bushes ", _ring_bushes.size())


var _t := 0.0


func _windf(t: float, ph: float) -> float:
	return sin(t * 1.15 + ph) * 0.7 + sin(t * 2.7 + ph * 1.9) * 0.3


func _cloud_sample(g: Vector2) -> float:
	if _cloud_img == null:
		return 0.0
	var uv := (g - CLOUD_VEL * _t) / CLOUD_SCALE
	var w := _cloud_img.get_width()
	var h := _cloud_img.get_height()
	var x := fposmod(uv.x, 1.0) * float(w) - 0.5
	var y := fposmod(uv.y, 1.0) * float(h) - 0.5
	var x0 := int(floor(x))
	var y0 := int(floor(y))
	var fx := x - float(x0)
	var fy := y - float(y0)
	var a := _cloud_img.get_pixel(posmod(x0, w), posmod(y0, h)).r
	var b := _cloud_img.get_pixel(posmod(x0 + 1, w), posmod(y0, h)).r
	var c := _cloud_img.get_pixel(posmod(x0, w), posmod(y0 + 1, h)).r
	var d := _cloud_img.get_pixel(posmod(x0 + 1, w), posmod(y0 + 1, h)).r
	return lerpf(lerpf(a, b, fx), lerpf(c, d, fx), fy)


func _dynamics(night: bool, dt: float) -> void:
	# v6.9 (D): one moving light. The cloud field drifts along the shared wind; ground, foliage
	# and grass read it in their shaders (cloud_off), the shafts / haze glow / sky sun glow read
	# it here on the CPU at the same points, so a passing cloud dims all of them together.
	_t += clampf(dt, 0.0, 0.1)
	if _cloud_img == null:
		var ct := load("res://textures/tiles/cloud_shadow.png") as Texture2D
		if ct:
			_cloud_img = ct.get_image()
			if _cloud_img and _cloud_img.is_compressed():
				_cloud_img.decompress()
	RenderingServer.global_shader_parameter_set("cloud_off", CLOUD_VEL * _t)
	RenderingServer.global_shader_parameter_set("cloud_amt", 0.0 if night else CLOUD_AMT)
	var pet := host.get("_pet") as Node3D
	var cam := host.get("_camera") as Camera3D
	var focus := pet.global_position if pet else Vector3.ZERO
	_light_now = 1.0 - _cloud_sample(Vector2(focus.x, focus.z))
	for hm in _haze_mats:
		var c := hm.albedo_color
		c.a *= 0.72 + 0.28 * _light_now * (0.9 + 0.1 * _windf(_t * 0.4, 0.7))
		hm.albedo_color = c
	if _sky_sm and not night:
		_sky_sm.set_shader_parameter("light_mul", _sky_tint * (0.94 + 0.06 * _light_now))
	# lagged pet for the plant spring-back (critically under-damped: ζ≈0.45, ~1.6 Hz)
	if pet:
		if _pet_lag == Vector3.ZERO:
			_pet_lag = focus
		var k := 100.0
		var cdmp := 9.0
		var h := clampf(dt, 0.0, 0.05)
		_pet_lag_v += ((focus - _pet_lag) * k - _pet_lag_v * cdmp) * h
		_pet_lag += _pet_lag_v * h
		RenderingServer.global_shader_parameter_set("pet_lag_ws", _pet_lag)
	var pt := OS.get_environment("HD2D_PUSH_TEST")   # bend check only: fixed push point x,z
	if pt != "":
		var q := pt.split(",")
		var pp := focus if pt == "pet" else Vector3(float(q[0]), 29.0, float(q[1]))
		RenderingServer.global_shader_parameter_set("pet_pos_ws", pp)
		RenderingServer.global_shader_parameter_set("pet_lag_ws", pp)
		if OS.get_environment("HD2D_PUSH_GAIN") != "" and _frames == 4:
			var gn := float(OS.get_environment("HD2D_PUSH_GAIN"))
			for tm in host.get("_tuft_mats"):
				(tm as ShaderMaterial).set_shader_parameter("push", 7.0 * gn)
				if OS.get_environment("HD2D_PUSH_WIDE") == "1":
					(tm as ShaderMaterial).set_shader_parameter("push_r0", 150.0)
					(tm as ShaderMaterial).set_shader_parameter("push_r1", 400.0)
			for cm in _clump_mats:
				var pv = cm.get_shader_parameter("push")
				if pv != null and float(pv) > 0.0:
					cm.set_shader_parameter("push", 4.0 * gn)
					if OS.get_environment("HD2D_PUSH_WIDE") == "1":
						cm.set_shader_parameter("push_r0", 150.0)
						cm.set_shader_parameter("push_r1", 400.0)
	_hybrid_shadow(night)


func _follow_camera(night: bool) -> void:
	var cam := host.get("_camera") as Camera3D
	if cam == null:
		return
	var cp := cam.global_position
	if _near_mi:
		_near_mi.global_position = Vector3(cp.x, 0.08, cp.z)
	if _sky_mi:
		_sky_mi.global_position = cp   # sky at infinity: rides with the camera (no parallax)
	# rays: axis billboards + grazing fade (mine and 遊程's shafts)
	for r in _rays:
		var mi := r[0] as MeshInstance3D
		if not is_instance_valid(mi):
			continue
		var axis: Vector3 = r[1]
		var ctr: Vector3 = r[2]
		var to_c := (cp - ctr).normalized()
		var xax := axis.cross(to_c)
		if xax.length() < 1e-3:
			continue
		xax = xax.normalized()
		var zax := xax.cross(axis).normalized()
		mi.basis = Basis(xax, axis, zax)
		var graze := smoothstep(0.15, 0.45, 1.0 - absf(axis.dot(to_c)))
		var dxz := Vector2(cp.x - ctr.x, cp.z - ctr.z).length()
		graze *= smoothstep(300.0, 400.0, dxz)   # v6.8: never a band in front of the garden
		# v6.9 (Kurt: the central light looks like a pasted picture): each shaft lives — the
		# cloud over its foot dims it, leaves crossing the beam flicker it with the shared wind,
		# it brightens when the camera looks into the sun and its width breathes slightly.
		var ri := _rays.find(r)
		var cl := _cloud_sample(Vector2(ctr.x, ctr.z) - Vector2(SUN_TO.x, SUN_TO.z) * (ctr.y / SUN_TO.y))
		var fl := 0.82 + 0.18 * _windf(_t * 0.8, float(ri) * 1.7)
		var look := clampf(Vector2(-to_c.x, -to_c.z).normalized().dot(Vector2(SUN_TO.x, SUN_TO.z).normalized()), 0.0, 1.0)
		var dyn := (1.0 - 0.85 * cl) * fl * (0.75 + 0.35 * look)
		mi.scale = Vector3(1.0 + 0.07 * _windf(_t * 0.5, float(ri) * 2.3), 1.0, 1.0)
		if int(r[4]) == 0:
			(r[3] as ShaderMaterial).set_shader_parameter("alpha", (1.12 if _ray_low else 0.59) * graze * dyn)   # v6.12: ×1.4 (0.6.11 PC: shafts too faint at phone aspect)
		elif r[3] is ShaderMaterial:
			(r[3] as ShaderMaterial).set_shader_parameter("alpha", float(r[5]) * graze * dyn)
	# re-face camera-facing cards after the camera moved (one MultiMesh per frame)
	var bas := cam.global_transform.basis
	if _reo_cam == Vector3.INF:
		_reo_cam = cp
		_reo_basis = bas
	if _bake_mode:
		return
	if _reo_i == 0 and (cp.distance_to(_reo_cam) > 6.0 or bas.z.angle_to(_reo_basis.z) > 0.06):
		_reo_cam = cp
		_reo_basis = bas
		_reo_i = 1
	if _reo_i > 0:
		if _reo_i - 1 < _facing_sets.size():
			_reface(_facing_sets[_reo_i - 1], _reo_cam)
			_reo_i += 1
		else:
			_reo_i = 0


func _reface(fs: Array, cp: Vector3) -> void:
	var mm := fs[0] as MultiMesh
	var pos: PackedVector3Array = fs[1]
	var siz: PackedVector2Array = fs[2]
	var stride: int = fs[3]
	var rolls := PackedFloat32Array()
	if fs.size() > 4:
		rolls = fs[4]
	var buf := mm.buffer
	if buf.size() < pos.size() * stride:
		return
	for i in pos.size():
		var p := pos[i]
		var fw := (cp - p).normalized()
		var rt := Vector3.UP.cross(fw).normalized()
		var up := fw.cross(rt)
		if i < rolls.size() and rolls[i] != 0.0:
			var cr := cos(rolls[i])
			var sr := sin(rolls[i])
			var rt2 := rt * cr + up * sr
			up = -rt * sr + up * cr
			rt = rt2
		var sx := siz[i].x
		var sy := siz[i].y
		var o := i * stride
		buf[o + 0] = rt.x * sx
		buf[o + 1] = up.x * sy
		buf[o + 2] = fw.x
		buf[o + 4] = rt.y * sx
		buf[o + 5] = up.y * sy
		buf[o + 6] = fw.y
		buf[o + 8] = rt.z * sx
		buf[o + 9] = up.z * sy
		buf[o + 10] = fw.z
	mm.buffer = buf


func _lawn_detail(cam: Camera3D) -> void:
	# finer near-camera grass grain over the bottom third (multiply detail, 1 draw)
	var pts: Array = []
	for sp in [Vector2(-0.05, 0.58), Vector2(1.05, 0.58), Vector2(-0.05, 1.02), Vector2(1.05, 1.02)]:
		var g := _ground_at(cam, sp)
		if g.x != INF:
			pts.append(g)
	if pts.size() < 4:
		return
	var mn: Vector3 = pts[0]
	var mx: Vector3 = pts[0]
	for p in pts:
		mn = mn.min(p)
		mx = mx.max(p)
	var pm := PlaneMesh.new()
	pm.size = Vector2(mx.x - mn.x, mx.z - mn.z)
	var mi := MeshInstance3D.new()
	mi.name = "LawnDetail_v66"
	mi.mesh = pm
	var m := ShaderMaterial.new()
	m.shader = load("res://shaders/lawn_detail.gdshader")
	m.set_shader_parameter("detail", load("res://textures/tiles/lawn_detail.png"))
	m.set_shader_parameter("tile", 64.0)
	m.set_shader_parameter("strength", 0.85)
	mi.material_override = m
	mi.position = Vector3((mn.x + mx.x) * 0.5, 0.12, (mn.z + mx.z) * 0.5)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	host.add_child(mi)



# ------------------------------------------------------------------ v6.5 foliage rebuild
const SUN_TO := Vector3(-0.645, 0.616, -0.453)  # v6.7: toward the raised sun (38°, upper-left, behind)
var _clump_groups := {}  # key → [tex, cells, haze, Array of [Transform3D, Color], sway, positions, sizes]
var _clump_total := 0


func _clump(tex: String, cells: float, haze: float, pos: Vector3, size: Vector2, val: float, warm: float, cell := -1, sway := 0.0, roll := 0.0) -> void:
	var key := "%s|%.2f|%.3f" % [tex, haze, sway]
	if not _clump_groups.has(key):
		_clump_groups[key] = [tex, cells, haze, [], sway, PackedVector3Array(), PackedVector2Array(), PackedFloat32Array()]
	var fw := (_cam_pos - pos).normalized()
	var rt := Vector3.UP.cross(fw).normalized()
	var up := fw.cross(rt).normalized()
	if roll != 0.0:
		# v6.8: in-plane roll so a spray's root→tip axis points outward from the crown
		var cr := cos(roll)
		var sr := sin(roll)
		var rt2 := rt * cr + up * sr
		up = -rt * sr + up * cr
		rt = rt2
	var v := clampf(val, 0.0, 1.6) / 1.6
	# v6.7: COLOR.a < 1 picks an explicit atlas cell (lit / edge / dark rows)
	var a := 1.0 if cell < 0 else (float(cell) + 0.5) / (cells * cells)
	var c := Color(clampf(v * (1.0 + 0.10 * warm), 0, 1), v, clampf(v * (1.0 - 0.16 * warm), 0, 1), a)
	(_clump_groups[key][3] as Array).append([Transform3D(Basis(rt * size.x, up * size.y, fw), pos), c])
	(_clump_groups[key][5] as PackedVector3Array).append(pos)
	(_clump_groups[key][6] as PackedVector2Array).append(size)
	(_clump_groups[key][7] as PackedFloat32Array).append(roll)


func _flush_clumps() -> int:
	var sh := load("res://shaders/clump_card.gdshader") as Shader
	var total := 0
	for key in _clump_groups:
		var g: Array = _clump_groups[key]
		var items: Array = g[3]
		var q := QuadMesh.new()
		q.size = Vector2.ONE
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.use_colors = true
		mm.mesh = q
		mm.instance_count = items.size()
		for i in items.size():
			mm.set_instance_transform(i, items[i][0])
			mm.set_instance_color(i, items[i][1])
		var mat := ShaderMaterial.new()
		mat.shader = sh
		mat.set_shader_parameter("atlas", load(g[0]))
		mat.set_shader_parameter("cells", g[1])
		mat.set_shader_parameter("haze_amt", clampf(float(g[2]) * 1.2, 0.0, 0.22))  # v6.6: was ×1.7 / 0.4 (pale)
		mat.set_shader_parameter("haze", Color(0.46, 0.48, 0.24))  # v6.6: green-gold haze, not cream
		mat.set_shader_parameter("sway", g[4])  # v6.7 wind
		if str(g[0]) == SERR:
			mat.set_shader_parameter("push", 4.0)     # v6.9: bushes give way to 團絨 (tuft 7, flowers 9)
			mat.set_shader_parameter("push_r1", 36.0)
		_clump_mats.append(mat)
		var mmi := MultiMeshInstance3D.new()
		mmi.name = "Clumps_" + str(_clump_groups.keys().find(key))
		mmi.multimesh = mm
		mmi.material_override = mat
		mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		host.add_child(mmi)
		_facing_sets.append([mm, g[5], g[6], 16, g[7]])
		total += items.size()
	print("v6.8 clump cards ", total, " in ", _clump_groups.size(), " multimeshes")
	_clump_total += total
	_clump_groups.clear()
	return total


func _core_mat(haze: float) -> ShaderMaterial:
	# v6.7: leafy-edged, leaf-textured dark core (0.6.6 phone: flat dark discs behind canopies)
	var m := ShaderMaterial.new()
	m.shader = load("res://shaders/core_leafy.gdshader")
	m.set_shader_parameter("leaf_tile", load("res://textures/tiles/leaf_shade_tile.png"))
	m.set_shader_parameter("col", Color(0.12, 0.15, 0.055).lerp(Color(0.20, 0.24, 0.10), clampf(haze * 6.0, 0.0, 1.0)))
	_clump_mats.append(m)
	return m


func _canopy_clusters() -> void:
	var cam := host.get("_camera") as Camera3D
	if cam:
		_cam_pos = cam.global_position
	var bushes := {}
	var k := 0
	var cores := {}
	# v6.6 r2: far rows 1+2 (trunks + crowns) are replaced by the painted backdrop
	var ff := host.get_node_or_null("FarForest")
	if ff:
		for c0 in ff.get_children():
			if c0 is Node3D and (c0 as Node3D).global_position.z < -360.0:
				(c0 as Node3D).visible = false
	var spheres: Array = []
	for n in _all(host):
		if not (n is MeshInstance3D):
			continue
		var mi := n as MeshInstance3D
		if not (mi.mesh is SphereMesh) or not (mi.material_override is ShaderMaterial):
			continue
		var t = (mi.material_override as ShaderMaterial).get_shader_parameter("albedo_tex")
		if t == null or not (t as Texture2D).resource_path.contains("leaf_"):
			continue
		var hv = (mi.material_override as ShaderMaterial).get_shader_parameter("haze_amt")
		var haze: float = 0.0 if hv == null else float(hv)
		if mi.get_parent().name == "FarForest" and mi.global_position.z < -360.0:  # r2: rows 1+2 → backdrop
			mi.visible = false
			continue
		var parent := mi.get_parent()
		if parent.name.begins_with("Bush_"):
			if not bushes.has(parent):
				bushes[parent] = []
			(bushes[parent] as Array).append(mi)
			continue
		var hk := "%.2f" % haze
		if not cores.has(hk):
			cores[hk] = [_core_mat(haze), []]
		(cores[hk][1] as Array).append(mi)
		var xf := mi.global_transform
		var r := (mi.mesh as SphereMesh).radius * xf.basis.get_scale().x
		var ry := (mi.mesh as SphereMesh).radius * xf.basis.get_scale().y * 0.9
		spheres.append([xf.origin, r, ry, haze])
	# v6.8: 遊程's voxel tree meshes carry smooth dome crowns (the "big smooth balls" above the
	# leaf masses, phone 0.6.7 low_2 / high_1). Trunks are ours (_trunks) → hide the mesh (kept
	# for the shadow-bake tool). The small back voxel trees get spray crowns over their blobs.
	for n in _all(host):
		if n is MeshInstance3D and (n as MeshInstance3D).mesh is ArrayMesh:
			var tnm := str(n.name)
			var tbb := (n as MeshInstance3D).global_transform * (n as MeshInstance3D).get_aabb()
			if tnm == "tree" and (n as MeshInstance3D).get_aabb().size.y > 200.0:
				(n as MeshInstance3D).visible = false
				n.set_meta("core_cast", true)
			elif tnm == "trees_bL" or tnm == "trees_bR":
				var tc := tbb.get_center() + Vector3(0, tbb.size.y * 0.18, 0)
				var trr := maxf(tbb.size.x, tbb.size.z) * 0.42
				spheres.append([tc, trr, trr * 0.8, 0.0])
				# v6.9 (Kurt 0.6.8: the darker trees still read as balls): this voxel mesh IS the
				# dark ball inside those crowns → hidden (play and bake); our grooved trunk
				# instead, so the crown is leaf sprays all the way through and the shadow is
				# trunk + leaves, not a disc.
				(n as MeshInstance3D).visible = false
				n.set_meta("core_cast", true)
				var bt := MeshInstance3D.new()
				var th := tbb.size.y * 0.62
				var tr0 := maxf(tbb.size.x, tbb.size.z) * 0.07
				bt.mesh = _groove_trunk(tr0, tr0 * 0.72, th, int(tbb.get_center().x) & 7)
				bt.material_override = _bark_mat()
				bt.position = Vector3(tbb.get_center().x, tbb.position.y, tbb.get_center().z)
				host.add_child(bt)
				_register_tree_caster(bt)
	for rs in _ring_spheres:
		spheres.append(rs)   # ring: [c, r, ry, haze, far=true]
	for sp in spheres:
		k = _canopy_mass(sp[0], sp[1], sp[2], sp[3], k, sp.size() > 4)
	# draw-call consolidation: every dark core sphere of a haze level → one merged mesh;
	for hk in cores:
		_merge_cores(cores[hk][1], cores[hk][0], "Cores_" + hk)
	var ring_core := _core_mat(0.0)
	_merge_core_spheres(_ring_cores, ring_core, "RingCores_v67")
	_hedges(bushes)
	_flush_cards()
	_flush_clumps()
	print("v6.8 canopy masses ", spheres.size(), " cards total ", _clump_total)


func _canopy_mass(c: Vector3, r: float, ry: float, haze: float, k: int, sparse := false) -> int:
	# v6.8 (Kurt 0.6.7: canopy reads as 粒粒波 round beads → wants 一絲絲 fine leaf strands):
	# every card is a leaf SPRAY (canopy_spray_atlas: twig + small pointed leaves, wispy tips)
	# rooted INSIDE the crown and rolled so it points outward (projected radial direction), so
	# the outline is made of strands, not round clump edges. Few big sprays = masses, row-2
	# wisps poke past the outline, row-3 dark hanging sprays underneath. Same card budget.
	var L := SUN_TO.normalized()
	var v := (_cam_pos - c).normalized()
	var rt0 := Vector3.UP.cross(v).normalized()
	var up0 := v.cross(rt0).normalized()
	var want := clampi(int(r * r / 70.0), 7, 30)
	if haze > 0.08 or sparse:
		want = maxi(6, want * 3 / 5)
	var tries := int(float(want) * 1.6)
	var sw := 0.035 if haze < 0.05 else 0.0
	# v6.11 (concept: big readable leaf clumps; 0.6.10 crowns read as fine busy noise): the crown
	# is split into a few LOBES; every spray is shaded by its lobe's own normal (lit top, dark
	# underside, dark gap between lobes) instead of one smooth gradient + per-card noise. Same
	# card count and wispy spray outline, so no balls and no cost.
	var lobes: Array = []
	if _lobes_on:
		var nl := clampi(int(r / 26.0), 2, 4)   # v6.15: fewer, bigger lit masses (v6.12 r/20, 2..5)   # v6.12: bigger clumps (concept clump size; was r/13, 3..7)
		for j in nl:
			var fyl := 0.85 - 1.3 * (float(j) + 0.5) / float(nl)
			var frl := sqrt(maxf(0.0, 1.0 - fyl * fyl))
			var fal := float(j) * 2.39996 + float(k % 7)
			var dl := Vector3(cos(fal) * frl, fyl, sin(fal) * frl)
			if dl.dot(v) < -0.3:
				dl = (dl + v * 0.8).normalized()
			lobes.append(c + Vector3(dl.x * r, dl.y * ry, dl.z * r) * 0.52)
	for i in tries:
		k += 1
		var fy := 1.0 - 2.0 * (float(i) + 0.5) / float(tries)
		var fr := sqrt(maxf(0.0, 1.0 - fy * fy))
		var fa := float(i) * 2.39996 + float(k % 13)
		var d := Vector3(cos(fa) * fr, fy, sin(fa) * fr)
		var facing := d.dot(v)
		if facing < -0.55:
			continue
		var h1 := fposmod(float(k) * 0.618034, 1.0)
		var h2 := fposmod(float(k) * 0.414214, 1.0)
		var h3 := fposmod(float(k) * 0.7548777, 1.0)
		var rim := 1.0 - absf(facing)
		var ndl := d.dot(L)
		var grad := smoothstep(-0.75, 0.95, d.y)
		var val := 0.56 + 0.80 * grad * grad + 0.36 * maxf(0.0, ndl + 0.1) * (0.4 + 0.6 * rim) + 0.10 * h2
		if lobes.size() > 0:
			var pp := c + Vector3(d.x * r, d.y * ry, d.z * r) * 0.62
			var best := 0
			var bd := INF
			for j in lobes.size():
				var dj := pp.distance_squared_to(lobes[j])
				if dj < bd:
					bd = dj
					best = j
			# v6.14 softer clumps (Kurt): the lobe normal is a soft blend of the near lobes (no hard
			# value step where two lobes meet), wider top ramp, shallower gaps.
			var lnv := Vector3.ZERO
			var ws := (r * 0.16) * (r * 0.16)   # PC r1: 0.42 averaged the lobes away (lit masses lost) → blend only at the seams
			for j in lobes.size():
				var dv: Vector3 = pp - (lobes[j] as Vector3)
				lnv += dv.normalized() * exp(-(dv.length_squared() - bd) / ws)
			var ln := lnv.normalized() if lnv.length() > 1e-4 else (pp - (lobes[best] as Vector3)).normalized()
			var lr := sqrt(bd) / (r * 0.55)
			var lg := smoothstep(-0.65, 0.92, ln.y)
			var lit := maxf(0.0, ln.dot(L) + 0.15)
			var cav := clampf((lr - 0.50) / 0.60, 0.0, 1.0) * clampf(0.60 - ln.y, 0.0, 1.0)   # lobe underside / gap
			# sky-lit top of each lobe (concept: bright clump tops), sun adds on the back-left side
			val = 0.62 + 0.55 * lg * (0.55 + 0.45 * grad) + 0.48 * lg * lg + 0.32 * lit * (0.5 + 0.5 * rim) + 0.02 * h2 - 0.16 * cav   # v6.15: brighter big lit masses   # v6.14: softer seams + gaps (v6.12 0.60 / 0.42 / 0.32 / 0.22), masses kept
		var cell := int(h3 * 8.0)
		var sz := r * (0.62 + 0.30 * h2)
		var rin := 0.50 + 0.25 * h1
		if h1 > 0.82:
			sz = r * (0.95 + 0.20 * h2)   # a few big sprays → the masses
			rin = 0.30
		elif h1 < 0.30:
			sz = r * (0.55 + 0.20 * h2)   # wispy strands past the outline
			rin = 0.78
			cell = 8 + int(h3 * 4.0)
		if d.y < -0.30:
			cell = 12 + int(h3 * 4.0)     # dark hanging sprays underneath
			val = 0.82 + 0.25 * h2
		val *= 1.0 - 2.4 * haze
		var dx := d.dot(rt0)
		var dy := d.dot(up0)
		var roll := (h2 - 0.5) * 2.6        # facing the camera: random fan
		if dx * dx + dy * dy > 0.04:
			roll = atan2(-dx, dy)          # point outward
		roll += (h3 - 0.5) * 0.7
		var up2 := -rt0 * sin(roll) + up0 * cos(roll)
		var root := c + Vector3(d.x * r, d.y * ry, d.z * r) * rin + v * 1.5
		_clump(SPRAY, 4.0, haze, root + up2 * sz * 0.45, Vector2(sz, sz * (0.95 + 0.2 * h1)), val, clampf(ndl + 0.2, 0.0, 1.0), cell, sw, roll)
	# v6.9: the dark interior is leaves all the way through (no core sphere): layered dark
	# spray cards from 0.15 r to 0.65 r, so the shadowed side still shows leaf shapes.
	for i in maxi(4, want / 2):
		k += 1
		var a := fposmod(float(k) * 0.618034, 1.0) * TAU
		var e := (fposmod(float(k) * 0.414214, 1.0) - 0.5) * 1.6
		var dd := Vector3(cos(a) * cos(e), sin(e) * 0.7, sin(a) * cos(e))
		var p2 := c + dd * r * (0.15 + 0.50 * fposmod(float(k) * 0.29, 1.0)) + v * r * 0.1
		_clump(SPRAY, 4.0, haze, p2, Vector2.ONE * r * 0.95, (0.80 + 0.25 * fposmod(float(k) * 0.53, 1.0)) * (1.0 - 2.0 * haze), 0.0, 12 + k % 4, 0.0, fposmod(float(k) * 0.29, 1.0) * TAU)
	if r > 16.0 and haze < 0.01:
		var u1b := v.cross(Vector3.UP).normalized()
		var u2b := u1b.cross(v).normalized()
		for i in 3:
			k += 1
			var hx := (fposmod(float(k) * 0.618, 1.0) - 0.5) * 1.4 * r
			var hp := c - u2b * ry * 0.92 + u1b * hx + v * r * 0.3 + Vector3(0, -r * 0.18, 0)
			_card("res://textures/tiles/leaf_hang.png", haze, hp, Vector2(r * 0.16, r * 0.42), v - Vector3.UP * 0.3, 0.8)
	return k


func _merge_cores(meshes: Array, mat: Material, nm: String) -> void:
	# v6.9 (Kurt 0.6.8: the dark trees / bushes still read as balls): NO smooth core spheres any
	# more — the originals are only hidden; the dark interior is dark leaf cards (_canopy_mass /
	# _bush_mass), so shadowed sides show leaves and broken outlines too.
	for mi in meshes:
		(mi as MeshInstance3D).visible = false
		(mi as MeshInstance3D).set_meta("core_cast", false)
	if CORE_SPHERES:
		_merge_cores_old(meshes, mat, nm)


const CORE_SPHERES := false
const AO_DISCS := false


func _merge_cores_old(meshes: Array, mat: Material, nm: String) -> void:
	if meshes.is_empty():
		return
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for mi in meshes:
		var m := mi as MeshInstance3D
		# low-res stand-in (10×5) — dark leafy core behind the clump cards (core_leafy.gdshader)
		var lo := SphereMesh.new()
		var shrink := 0.64 if m.get_parent().name == "FarForest" else 0.70  # v6.8: never past the sprays
		lo.radius = (m.mesh as SphereMesh).radius * shrink
		lo.height = (m.mesh as SphereMesh).height * shrink
		lo.radial_segments = 8
		lo.rings = 4
		st.append_from(lo, 0, m.global_transform)
		# v6.6: hide the textured original (遊程's policy would flip SHADOWS_ONLY → OFF = visible).
		m.set_meta("core_cast", m.cast_shadow != GeometryInstance3D.SHADOW_CASTING_SETTING_OFF)
		m.visible = false
	var out := MeshInstance3D.new()
	out.name = nm
	out.mesh = st.commit()
	out.material_override = mat
	out.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	host.add_child(out)


func _merge_core_spheres(items: Array, mat: Material, nm: String) -> void:
	if items.is_empty() or not CORE_SPHERES:   # v6.9: leaf cards instead of core spheres
		return
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for it in items:
		var lo := SphereMesh.new()
		lo.radius = float(it[1])
		lo.height = float(it[1]) * 2.0
		lo.radial_segments = 6
		lo.rings = 3
		var b := Basis.from_scale(Vector3(1.0, float(it[2]), 1.0))
		st.append_from(lo, 0, Transform3D(b, it[0]))
	var out := MeshInstance3D.new()
	out.name = nm
	out.mesh = st.commit()
	out.material_override = mat
	out.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	host.add_child(out)


func _hedges(bushes: Dictionary) -> void:
	# v6.7 (Kurt: hedges are the LEAST like the concept): no hedge card, no flat trim. Each bush
	# becomes 2–5 layered leafy mounds of varied height along its length (leaf-built atlas,
	# some with pink / white flowers), ragged crown sprays, dark leafy gaps at the base and
	# between mounds, a contact shadow; dark leafy core lobes behind. Cards all round the hull.
	var core := _core_mat(0.0)
	var all_lobes: Array = []
	var k := 0
	for b in bushes:
		var lobes: Array = bushes[b]
		var box := AABB()
		var first := true
		for mi in lobes:
			var m := mi as MeshInstance3D
			var bb := m.global_transform * m.get_aabb()
			box = bb if first else box.merge(bb)
			first = false
			all_lobes.append(m)
		# v6.8 (Kurt 0.6.7 low_2 / high_2: hedges read as straight rows): a long hedge box is
		# broken into an organic cluster — segments of mixed length / height, pushed in and out
		# sideways, with a gap or two — instead of one straight run.
		var hl := maxf(box.size.x, box.size.z)
		if hl > 40.0:
			var along := Vector3.RIGHT if box.size.x >= box.size.z else Vector3.BACK
			var side := Vector3.BACK if box.size.x >= box.size.z else Vector3.RIGHT
			var dep := minf(box.size.x, box.size.z)
			var nseg := int(ceil(hl / 24.0))
			var cen := box.get_center()
			for si in nseg:
				k += 1
				var hs1 := fposmod(float(k) * 0.618034, 1.0)
				var hs2 := fposmod(float(k) * 0.414214, 1.0)
				var hs3 := fposmod(float(k) * 0.7548777, 1.0)
				if hs1 < 0.34 and si > 0 and si < nseg - 1:
					continue   # gap
				var t := ((float(si) + 0.5) / float(nseg) - 0.5) * hl
				var seg_l := hl / float(nseg) * (0.8 + 0.7 * hs2)
				var seg_h := box.size.y * (0.65 + 0.7 * hs3)
				var seg_d := dep * (0.9 + 0.8 * hs1)
				var pc := cen + along * (t + (hs3 - 0.5) * 10.0) + side * ((hs2 - 0.5) * (dep * 2.0 + 22.0))
				var sbox := AABB(Vector3(pc.x, box.position.y, pc.z) - (along * seg_l + side * seg_d) * 0.5, Vector3.ZERO)
				sbox.size = (along * seg_l + side * seg_d).abs() + Vector3(0, seg_h, 0)
				k = _bush_mass(sbox, k)
		else:
			k = _bush_mass(box, k)
	for rb in _ring_bushes:
		k = _bush_mass(rb, k)
	_merge_cores(all_lobes, core, "HedgeCores")


func _bush_mass(box: AABB, k: int) -> int:
	var L := SUN_TO.normalized()
	var c := box.get_center()
	var w := maxf(box.size.x, box.size.z)
	var dep := minf(box.size.x, box.size.z)
	var h := box.size.y
	var lng := Vector3.RIGHT if box.size.x >= box.size.z else Vector3.BACK
	var sid := Vector3.BACK if box.size.x >= box.size.z else Vector3.RIGHT
	var y0 := box.position.y
	var nm := clampi(int(w / 14.0), 1, 4)
	_ao_items.append([Vector3(c.x, 0.0, c.z), w * 0.85])   # v6.9: tight contact, not a big disc
	for mo in nm:
		k += 1
		var t := (float(mo) + 0.5) / float(nm) - 0.5 + (fposmod(float(k) * 0.37, 1.0) - 0.5) * 0.15
		var mh := h * (0.62 + 0.62 * fposmod(float(k) * 0.618034, 1.0))
		var mw := w / float(nm) * (1.30 + 0.30 * fposmod(float(k) * 0.41, 1.0))
		var md := dep * (0.85 + 0.25 * fposmod(float(k) * 0.29, 1.0))
		var mc := c + lng * t * w * 0.90 + sid * (fposmod(float(k) * 0.53, 1.0) - 0.5) * dep * 0.25
		mc.y = y0 + mh * 0.5
		var rad := Vector3(mw * 0.5, mh * 0.5, md * 0.5)
		var n := 6   # v6.8: serrated mounds are denser per card than the old blobs → fewer cards
		for j in n:
			k += 1
			var fy := 1.0 - 2.0 * (float(j) + 0.5) / float(n) * 0.78
			var fr := sqrt(maxf(0.0, 1.0 - fy * fy))
			var fa := float(j) * 2.39996 + float(k % 11)
			var d := Vector3(cos(fa) * fr, fy, sin(fa) * fr)
			var h1 := fposmod(float(k) * 0.618034, 1.0)
			var h2 := fposmod(float(k) * 0.414214, 1.0)
			var grad := smoothstep(-0.5, 0.9, d.y)
			var val := 0.62 + 0.55 * grad + 0.28 * maxf(0.0, d.dot(L) + 0.1) + 0.08 * h2
			var cell := int(h1 * 8.0)
			if h2 > 0.55 and d.y > -0.2:
				cell = 8 + int(h1 * 8.0)   # flowered mounds
			var off := lng * d.x * rad.x + Vector3.UP * d.y * rad.y + sid * d.z * rad.z
			var sz := (rad.x + rad.y) * (0.85 + 0.30 * h2)
			_clump(SERR, 4.0, 0.0, mc + off * 0.78, Vector2(sz, sz * 0.85), val, 0.6, cell, 0.025, (h1 - 0.5) * 0.5)
		# v6.9: dark serrated leaves through the mound's interior (no core ball behind)
		for j2 in 2:
			k += 1
			var ip := mc + lng * (fposmod(float(k) * 0.37, 1.0) - 0.5) * rad.x * 0.8 + Vector3(0, -rad.y * 0.1, 0)
			_clump(SERR, 4.0, 0.0, ip, Vector2(rad.x, rad.y * 1.1) * 1.4, 0.42 + 0.1 * float(j2), 0.0, k % 8, 0.02, (fposmod(float(k) * 0.61, 1.0) - 0.5) * 0.8)
		# ragged crown spray, sun-caught
		k += 1
		_clump(SERR, 4.0, 0.0, mc + Vector3(0, rad.y * 0.85, 0) + lng * (fposmod(float(k) * 0.7, 1.0) - 0.5) * rad.x,
			Vector2.ONE * rad.x * (0.7 + 0.3 * fposmod(float(k) * 0.3, 1.0)), 1.30, 1.0, k % 16, 0.03, (fposmod(float(k) * 0.53, 1.0) - 0.5) * 0.6)
	# darker leafy gaps along the base, both faces
	for j in nm + 1:
		k += 1
		var t2 := float(j) / float(nm) - 0.5
		for sgn in [-1.0, 1.0]:
			var p: Vector3 = c + lng * t2 * w * 0.9 + sid * sgn * dep * 0.42
			p.y = y0 + h * 0.22
			_clump(SERR, 4.0, 0.0, p, Vector2(w / float(nm) * 0.9, h * 0.55), 0.50, 0.0, (k + j) % 8, 0.0)
	return k


func _register_tree_caster(n: Node) -> void:
	# baked into the ground shadow → follow 遊程's tree shadow policy (live only without a bake)
	var tsn = host.get("_tree_shadow_nodes")
	if tsn is Array:
		(tsn as Array).append(n)
	if bool(host.get("_bake_shadow_ground")):
		host.call("_tag_shadow", n, false)


func _bark_mat() -> StandardMaterial3D:
	# v6.5: AI-based deep-groove bark (64 px ↔ 48 wu → grooves ≈ 3 wu apart, readable on a
	# phone), vertex colour darkens the geometric fissures so they read in Low without shadows.
	var m := StandardMaterial3D.new()
	m.albedo_texture = load("res://textures/tiles/bark_groove.png")
	m.normal_enabled = true
	m.normal_texture = load("res://textures/tiles/bark_groove_n.png")
	m.normal_scale = 1.2
	m.vertex_color_use_as_albedo = true
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	m.albedo_color = Color(1.12, 0.96, 0.88)
	m.roughness = 1.0
	return m


func _groove_trunk(rb: float, rt: float, h: float, seed: int, segs := 24, rings := 12) -> ArrayMesh:
	# Fluted trunk: 24 sides, every other vertex pushed in 16–24 % → deep vertical grooves
	# in the silhouette and shading; root flare (×1.6 at the ground, 12 wu falloff).
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var pts := []
	var cols := []
	var uvs := []
	for j in rings + 1:
		var y := h * float(j) / float(rings)
		var row := []
		var crow := []
		var urow := []
		var rr := lerpf(rb, rt, y / h) * (1.0 + 0.6 * exp(-y / 12.0))
		for i in segs + 1:
			var a := TAU * float(i % segs) / float(segs)
			var gv := fposmod(float((i % segs) * 7 + seed * 13) * 0.618034, 1.0)
			var groove := (i % 2 == 1)
			var k := 1.0 - ((0.16 + 0.08 * gv) if groove else 0.0)
			var sway := 0.04 * sin(y / 23.0 + float(i) * 0.7 + float(seed))
			row.append(Vector3(cos(a) * rr * (k + sway), y, sin(a) * rr * (k + sway)))
			var cv := (0.40 + 0.08 * gv) if groove else (0.95 + 0.10 * gv)
			if y < 10.0:
				cv *= 0.75 + 0.025 * y  # contact darkening at the root
			crow.append(Color(cv, cv * 0.97, cv * 0.95))
			urow.append(Vector2(float(i) / float(segs) * TAU * rr / 48.0, -y / 48.0))
		pts.append(row)
		cols.append(crow)
		uvs.append(urow)
	for j in rings:
		for i in segs:
			var quad := [[j, i], [j, i + 1], [j + 1, i + 1], [j, i], [j + 1, i + 1], [j + 1, i]]
			for q in quad:
				st.set_color(cols[q[0]][q[1]])
				st.set_uv(uvs[q[0]][q[1]])
				st.add_vertex(pts[q[0]][q[1]])
	st.generate_normals()
	st.generate_tangents()
	return st.commit()



func _haze_glow() -> void:
	# v6.5 soft haze glow (gap #8): a few big additive radial sprites where the concept's
	# golden light blooms (upper-left sun gap, the clearing behind the cottage, lantern line).
	var g := _unshaded("res://textures/tiles/glow_soft_v610.png", true, 0.32)   # v6.10: 256 px smooth double falloff, dithered (no rings)
	g.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR
	_haze_mats.append(g)
	var items := [
		[Vector3(-150, 230, -380), Vector2(520, 520)],
		[Vector3(-40, 120, -300), Vector2(380, 300)],
		[Vector3(40, 90, -200), Vector2(240, 180)],
	]
	_facing_mm(g, items, "HazeGlow_v65")


# ------------------------------------------------------------------ v6.9 hybrid + soft shadows
# Art-side PREVIEW of the values 遊程 is asked to copy into capture.gd (_apply_shadow_policy).
# Baked shadows stay for the static world (trees, cottage, fence, ring); on Low a low-res live
# sun shadow is added for the things that move (團絨, the 11 bump props, bushes / tufts / plants
# that bend). High keeps 遊程's live casters with the soft values below.
# HD2D_HYBRID=0 turns this art preview off (then 遊程's policy is untouched).
const HY_ATLAS := 1024
const HY_MAX_DIST := 300.0        # wu from the camera (camera→pet is 270)
const HY_BLUR_LOW := 2.0
const HY_BLUR_HIGH := 2.2
const HY_ANGULAR_LOW := 0.6       # degrees, small penumbra
const HY_ANGULAR_HIGH := 0.9
const HY_OPACITY := 0.55          # shadow keeps 45 % of the sun → matches the bake (64–78 %), interiors keep texture
const HY_PROPS := ["pot_S", "pot_L", "pot_R", "can", "CrateWood"]   # v6.10: jar is not a live caster (遊程 v6.9) → it must be baked   # lids ride on the crate: its shadow covers theirs (−2 draws)
var _hy_state := ""
var _hy_saved := {}


func _hy_dynamic(n: Node) -> bool:
	var pet := host.get("_pet") as Node
	if pet and (n == pet or pet.is_ancestor_of(n)):
		return true
	var nm := str(n.name)
	for pre in HY_PROPS:
		if nm.begins_with(pre):
			return true
	var par := n.get_parent()
	while par and par != host:
		for pre in HY_PROPS:
			if str(par.name).begins_with(pre):
				return true
		par = par.get_parent()
	if n.has_meta("hy_dyn"):
		return true
	return false


func _hard_preview() -> void:
	# previews/shadow_hard_vs_soft only (HD2D_SHADOW_HARD=1): v6.9 bake without feathering /
	# contact AO / tint, and hard live-shadow values.
	if _hard_done or OS.get_environment("HD2D_SHADOW_HARD") != "1":
		return
	_hard_done = true
	var t := load("res://textures/ground_composed_low_hard.png")
	if t:
		host.set("_ground_tex_low", t)
		if host.has_method("_apply_ground_bake"):
			host.call("_apply_ground_bake")
	if _near_mi and _near_mi.material_override is ShaderMaterial:
		(_near_mi.material_override as ShaderMaterial).set_shader_parameter("macro_tex", load("res://textures/near_macro_hard.png"))
	if _dapple_sm:
		_dapple_sm.set_shader_parameter("wide_mask", load("res://textures/shadow_wide_mask_hard.png"))
		_dapple_sm.set_shader_parameter("shade_col", Color(0.02, 0.03, 0.01))
		_dapple_sm.set_shader_parameter("static_amt", 0.42)


var _hard_done := false


func _hybrid_shadow(night: bool) -> void:
	# v6.9: sun / atlas / live-caster policy moved to capture._apply_shadow_policy
	# so Low jar casters stay off and Low/High values are not overwritten every frame.
	if _bake_mode:
		return
	if OS.get_environment("HD2D_SHADOW_HARD") == "1":
		_hard_preview()
	return
	# (previous preview implementation left below, unreachable)
	if _bake_mode or OS.get_environment("HD2D_HYBRID") == "0":
		return
	_hard_preview()
	var hard := OS.get_environment("HD2D_SHADOW_HARD") == "1"
	var sun := host.get("_sun") as DirectionalLight3D
	if sun == null:
		return
	var mode := str(host.get("_mode"))
	var low := mode == "low"
	var st := mode
	if st != _hy_state:
		_hy_state = st
		if low:
			RenderingServer.directional_shadow_atlas_set_size(HY_ATLAS, false)
			for n in _all(host):
				if n is GeometryInstance3D:
					var gi := n as GeometryInstance3D
					if _hy_dynamic(gi):
						if not _hy_saved.has(gi):
							_hy_saved[gi] = gi.cast_shadow
						gi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
					elif gi.cast_shadow != GeometryInstance3D.SHADOW_CASTING_SETTING_OFF:
						if not _hy_saved.has(gi):
							_hy_saved[gi] = gi.cast_shadow
						gi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		else:
			RenderingServer.directional_shadow_atlas_set_size(int(ProjectSettings.get_setting("rendering/lights_and_shadows/directional_shadow/size.mobile", 2048)), false)
			for gi in _hy_saved:
				if is_instance_valid(gi):
					(gi as GeometryInstance3D).cast_shadow = _hy_saved[gi]
			_hy_saved.clear()
	if low:
		sun.shadow_enabled = not night
		sun.directional_shadow_mode = DirectionalLight3D.SHADOW_ORTHOGONAL
		sun.directional_shadow_max_distance = HY_MAX_DIST
		sun.shadow_blur = 0.2 if hard else HY_BLUR_LOW
		sun.light_angular_distance = 0.0 if hard else HY_ANGULAR_LOW
	elif sun.shadow_enabled:
		sun.shadow_blur = 0.2 if hard else HY_BLUR_HIGH
		sun.light_angular_distance = 0.0 if hard else HY_ANGULAR_HIGH
	if "shadow_opacity" in sun and sun.shadow_enabled:
		sun.set("shadow_opacity", 0.92 if hard else HY_OPACITY)


# ------------------------------------------------------------------ v6.9 test drivers (env only)
# HD2D_WALKLOOP=1: 團絨 walks a loop through the lawn, flowers, bushes and past the props
# (used with --write-movie for previews/walk_*.mp4). HD2D_PERF=1: uncapped frame timing log.
const WALK_PTS := [Vector2(-50, 60), Vector2(-100, 80), Vector2(-30, 88), Vector2(60, 75), Vector2(110, 40), Vector2(95, 0), Vector2(10, -5), Vector2(-50, 10)]
var _walk_i := 0
var _perf := {}


# ------------------------------------------------------------------ v6.10 Low without the live sun pass
# Phone (Note10+) 0.6.9: Low 47–48 fps with the hybrid live shadow, 60 with bake only. Proposal
# for 遊程 (GAPS_v6_10 §5): Low sun.shadow_enabled = false. The art layer then shows
#   • the props / fg plants / jar BAKED into the Low ground (ground_composed_low_props.png), and
#   • 團絨's projected silhouette shadow (shaders/pet_shadow.gdshader, 1 draw).
# Detected automatically (Low + sun shadow off), so it works the moment capture.gd changes.
# HD2D_LOW_FAKE=1 = preview of that change (turns the Low sun shadow off from here; test only).
var _pet_sh: MeshInstance3D
var _pet_sh_mat: ShaderMaterial
var _tex_low_props: Texture2D
var _fake_on := -1
var _pet_sh_off := false
var _lobes_on := OS.get_environment("HD2D_LOBES") != "0"
# v6.11 grade (Kurt: mid-ground darker / less golden than the concept). Day only.
var _sun_gain := 1.16
var _sun_col := Color(1.0, 0.84, 0.66)   # warmth from R, keep the blue (concept lawn B 28)
var _sky_tint := Vector3(0.98, 0.88, 0.74) * 0.92
var _grade_init := false
var _exp_day := 1.45
var _exp_low := 1.50   # v6.12: 1.58 → 1.50 (mid-ground balance; PC upper mid 134 vs concept 114)
var _amb_day := Color(0.52, 0.58, 0.68)
var _amb_e := 0.26
# v6.11 Low/High distance haze (concept: soft golden background). Depth fog was set up by 遊程 but
# fog_density 0.0 (=off). Fog is evaluated in the existing material shaders → no new pass / draw.
var _fog_d := 0.04   # v6.12: 0.05 → 0.04 (PC r1 rows 400–480 151 vs concept 127: haze too bright)
var _ring_haze := 0.50
var _fog_b := 400.0
var _fog_e := 1100.0
var _near_fake := -1


func _low_fake_shadow(night: bool) -> void:
	if _bake_mode:
		return
	var sun := host.get("_sun") as DirectionalLight3D
	var pet := host.get("_pet") as Sprite3D
	if sun == null or pet == null:
		return
	var low := str(host.get("_mode")) == "low"
	if low and OS.get_environment("HD2D_LOW_FAKE") == "1" and sun.shadow_enabled:
		sun.shadow_enabled = false
	var fake := low and not night and not sun.shadow_enabled
	if _pet_sh == null:
		var q := QuadMesh.new()
		q.size = Vector2.ONE
		_pet_sh = MeshInstance3D.new()
		_pet_sh.name = "PetShadow_v610"
		_pet_sh.mesh = q
		_pet_sh_mat = ShaderMaterial.new()
		_pet_sh_mat.shader = load("res://shaders/pet_shadow.gdshader")
		_pet_sh_mat.render_priority = 1
		_pet_sh.material_override = _pet_sh_mat
		_pet_sh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		host.add_child(_pet_sh)
		if ResourceLoader.exists("res://textures/ground_composed_low_props.png"):
			_tex_low_props = load("res://textures/ground_composed_low_props.png")
	_pet_sh.visible = fake and not _pet_sh_off
	if fake:
		var tex := pet.texture
		_pet_sh_mat.set_shader_parameter("pet_tex", tex)
		var w := float(tex.get_width()) * pet.pixel_size if tex else 64.0
		var h := float(tex.get_height()) * pet.pixel_size if tex else 64.0
		var L := Vector3(0.645, 0.0, 0.453) / 0.616      # ground offset per wu of height
		var gp := Vector3(pet.global_position.x, 0.25, pet.global_position.z)
		# Sprite3D offset is pixels, +Y raises the quad. pixel_size converts it to world units.
		var yc := pet.global_position.y + pet.offset.y * pet.pixel_size
		_pet_sh.global_transform = Transform3D(Basis(Vector3(w, 0, 0), L * h, Vector3(0, 1, 0)), gp + L * yc)
	var fi := 1 if fake else 0
	# v6.13: baked shade ON the beds (pickets / lamp / cottage / trees) when Low has no live sun shadow
	if fi != _bed_fake and ResourceLoader.exists("res://textures/bedtop_shade_v613.png"):
		var bms = host.get("_bed_flower_mats")
		if bms is Array and (bms as Array).size() > 0:
			_bed_fake = fi
			var bt := load("res://textures/bedtop_shade_v613.png")
			for bm in bms:
				(bm as ShaderMaterial).set_shader_parameter("bedtop_tex", bt)
				(bm as ShaderMaterial).set_shader_parameter("bedtop_amt", 1.0 if fake else 0.0)
	# near lawn plane (built a few frames later than this first runs) → its own state
	if fi != _near_fake and _near_mi and _near_mi.material_override is ShaderMaterial and ResourceLoader.exists("res://textures/near_mover_shade.png"):
		_near_fake = fi
		var nmat := _near_mi.material_override as ShaderMaterial
		nmat.set_shader_parameter("mover_tex", load("res://textures/near_mover_shade.png"))
		nmat.set_shader_parameter("mover_amt", 1.0 if fake else 0.0)
	if fi != _fake_on and _ground_mat and _tex_low_props:
		_fake_on = fi
		if fake:
			_ground_mat.set_shader_parameter("albedo_tex", _tex_low_props)
		else:
			var cur = host.get("_ground_tex_low")
			if cur:
				_ground_mat.set_shader_parameter("albedo_tex", cur)
		# the near / outer lawn (outside the inner bake) gets the fg-plant + prop shade from the wide props mask
		if _dapple_sm:
			var wm := "res://textures/shadow_wide_mask_props_v615.png" if fake else "res://textures/shadow_wide_mask_v615.png"   # v6.15 canopy sun breaks
			if ResourceLoader.exists(wm):
				_dapple_sm.set_shader_parameter("wide_mask", load(wm))


# v6.10 test hooks (PC perf / look checks only; nothing here runs unless the env var is set).
#   HD2D_AMB=1                 遊程's ambient suggestion (0.62,0.66,0.86), energy +0.05
#   HD2D_HI="atlas=1024,dist=300,softq=1,splits=1,shafts=0,dof=0,glow=0,casters=hy,rays=0,skyfx=0,petsh=0"
func _perf_tests(night: bool) -> void:
	var env := host.get("_env") as Environment
	if OS.get_environment("HD2D_AMB") == "1" and env and not night and not env.has_meta("amb_done"):
		env.set_meta("amb_done", true)
		env.ambient_light_color = Color(0.62, 0.66, 0.86)
		env.ambient_light_energy += 0.05
	var nc := OS.get_environment("HD2D_DBG_NOCAST")   # debug: which live caster makes a shade
	if nc != "":
		for gi in host.call("_all_geom", host):
			if nc == "ALL" or str((gi as Node).name).begins_with(nc):
				(gi as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var hi := OS.get_environment("HD2D_HI")
	if hi == "":
		return
	var sun := host.get("_sun") as DirectionalLight3D
	for kv in hi.split(","):
		var p := kv.split("=")
		if p.size() != 2:
			continue
		match p[0]:
			"atlas":
				RenderingServer.directional_shadow_atlas_set_size(int(p[1]), false)
			"dist":
				sun.directional_shadow_max_distance = float(p[1])
			"softq":
				RenderingServer.directional_soft_shadow_filter_set_quality(int(p[1]) as RenderingServer.ShadowQuality)
			"splits":
				sun.directional_shadow_mode = DirectionalLight3D.SHADOW_ORTHOGONAL if p[1] == "1" else DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS
			"shafts":
				var sh := host.get_node_or_null("Shafts") as Node3D
				if sh:
					sh.visible = p[1] != "0"
			"dof":
				var ca = host.get("_attrs")
				if ca:
					ca.set("dof_blur_far_enabled", p[1] != "0")
					ca.set("dof_blur_near_enabled", p[1] != "0")
			"glow":
				if env:
					env.glow_enabled = p[1] != "0"
			"casters":
				if p[1] == "hy" and host.has_method("_apply_hybrid_casters"):
					host.call("_apply_hybrid_casters")
			"rays":
				for r in _rays:
					if int(r[4]) == 0:
						(r[0] as Node3D).visible = p[1] != "0"
			"skyfx":
				if _sky_sm and p[1] == "0":
					_sky_sm.set_shader_parameter("glow_amt", 0.0)
					_sky_sm.set_shader_parameter("ray_amt", 0.0)
			"petsh":
				_pet_sh_off = p[1] == "0"
	if _frames == 10:
		print("v6.10 HD2D_HI applied ", hi)


func _walk_loop() -> void:
	if OS.get_environment("HD2D_WALKLOOP") != "1" or _frames < 15:
		return
	if host.get("_walk_target") == null:
		var p: Vector2 = WALK_PTS[_walk_i % WALK_PTS.size()]
		_walk_i += 1
		host.set("_walk_target", Vector3(p.x, 0.0, p.y))


func _perf_log(dt: float) -> void:
	if OS.get_environment("HD2D_PERF") != "1":
		return
	var vp := get_viewport().get_viewport_rid()
	if _frames == 5:
		RenderingServer.viewport_set_measure_render_time(vp, true)
		Engine.max_fps = 0
		DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
		_perf = {"n": 0, "gpu": 0.0, "cpu": 0.0, "dt": 0.0, "dr": 0.0, "pr": 0.0}
	if _frames > 120 and _frames <= 720:
		_perf["n"] += 1
		_perf["gpu"] += RenderingServer.viewport_get_measured_render_time_gpu(vp)
		_perf["cpu"] += RenderingServer.viewport_get_measured_render_time_cpu(vp) + RenderingServer.get_frame_setup_time_cpu()
		_perf["dt"] += dt
		_perf["dr"] += Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)
		_perf["pr"] += Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)
	if _frames == 721:
		var n := float(_perf["n"])
		print("perf v6.18-pilot vc27 mode=", host.get("_mode"), " hybrid=", OS.get_environment("HD2D_HYBRID"), " hard=", OS.get_environment("HD2D_SHADOW_HARD"),
			" gpu_ms=%.3f cpu_ms=%.3f fps_uncapped=%.1f draws=%.0f prims=%.0f" % [_perf["gpu"] / n, _perf["cpu"] / n, n / _perf["dt"], _perf["dr"] / n, _perf["pr"] / n])
		get_tree().quit()


# v6.11: concept lit lawn median 81/78/28, highlights 163/138/58 (warm, R > G); 0.6.10 Low 70/68/18
# and 142/134/51 (neutral). Sky top concept 140/108/55, ours 159/142/86 (pale). → a little more,
# warmer sun on the scene and a warmer, slightly darker sky. Same pipeline, no new pass.
# Test: HD2D_GRADE="sun=1.16,sky=0" etc.
# v6.11 (c) warm bounce from the sunlit lawn onto walls / prop undersides / leaf undersides:
# one shadowless directional light travelling UP and back (-z), so it never touches the
# up-facing ground and only fills faces turned down / toward the camera. Day only.
var _bounce_e := 0.26
var _bounce_set := false   # PC r2 (Mobile 1080×2280): +0.047 ms GPU on Low (0.648 → 0.695) → High only by default; Low: HD2D_GRADE=bounce=0.26
var _bounce: DirectionalLight3D

func _grade_v611(night: bool) -> void:
	if _bake_mode:
		return
	if not _grade_init:
		_grade_init = true
		var g := OS.get_environment("HD2D_GRADE")
		for kv in g.split(",", false):
			var p := kv.split("=")
			if p.size() != 2:
				continue
			match p[0]:
				"sun":
					_sun_gain = float(p[1])
				"warm":
					if p[1] == "0":
						_sun_col = Color(1.0, 0.84, 0.68)
				"sky":
					_sky_tint = Vector3(0.98, 0.88, 0.74) * float(p[1]) if p[1] != "0" else Vector3.ONE
				"bounce":
					_bounce_e = float(p[1])
					_bounce_set = true
				"expl":
					_exp_low = float(p[1])
				"exp":
					_exp_day = float(p[1])
				"amb":
					_amb_e = float(p[1])
				"ring":
					_ring_haze = float(p[1])
					if _ring_sm:
						_ring_sm.set_shader_parameter("haze_amt", _ring_haze)
				"fog":
					_fog_d = float(p[1])
				"fogb":
					_fog_b = float(p[1])
				"foge":
					_fog_e = float(p[1])
		var go := host.get_node_or_null("GroundOuter") as MeshInstance3D
		if go and go.material_override is ShaderMaterial and ResourceLoader.exists("res://textures/grass_outer_v613.png"):
			(go.material_override as ShaderMaterial).set_shader_parameter("albedo_tex", load("res://textures/grass_outer_v613.png"))   # v6.13: lush green (v6.12 ×0.84 kept)
	if not _bounce_set and str(host.get("_mode")) == "low":
		_bounce_e = 0.0
	if _bounce == null and _bounce_e > 0.0:
		_bounce = DirectionalLight3D.new()
		_bounce.name = "LawnBounce_v611"
		_bounce.shadow_enabled = false
		_bounce.light_color = Color(1.0, 0.76, 0.44)
		_bounce.light_specular = 0.0
		_bounce.sky_mode = DirectionalLight3D.SKY_MODE_LIGHT_ONLY
		host.add_child(_bounce)
		_bounce.basis = Basis.looking_at(Vector3(0.15, 0.85, -0.50).normalized(), Vector3.FORWARD)
	if _bounce:
		_bounce.visible = not night
		_bounce.light_energy = _bounce_e * (0.6 + 0.4 * _light_now)
	var sun := host.get("_sun") as DirectionalLight3D
	if night:
		var envn := host.get("_env") as Environment
		if envn:
			envn.fog_density = 0.0   # v6.11: no day haze at night (keep capture.gd night look)
		return
	if sun == null:
		return
	sun.light_energy = 2.6 * _sun_gain
	sun.light_color = _sun_col
	var env := host.get("_env") as Environment
	if env and OS.get_environment("HD2D_EXP") == "":
		env.tonemap_exposure = _exp_low if str(host.get("_mode")) == "low" else _exp_day
		env.ambient_light_color = _amb_day
		env.ambient_light_energy = _amb_e
		env.fog_density = _fog_d
		env.fog_depth_begin = _fog_b
		env.fog_depth_end = _fog_e
		env.fog_depth_curve = 1.2
		env.fog_light_color = Color(1.0, 0.84, 0.58)
		env.fog_light_energy = 0.70   # v6.12: 0.85 → 0.70 (layering kept, less glare in the upper mid)
		env.fog_sun_scatter = 0.35



# v0.6.18-pilot vc27: night indirect sky = irradiance × fragment albedo (not a constant RGB add).
# vc26 r2 constant EMISSION made a steel-blue slab; this keeps baked grass chroma and shade contrast.
# HD2D_NIGHT_TOE: unset = 0.3 at night (GPU still); "0" = off (vc25 look). Explicit value still overrides. Mask: ground|tuft|near|combined.
# HD2D_NIGHT_SKY: optional r,g,b irradiance tint (default 0.70,0.92,1.00), multiplied by albedo.
func _night_toe_gain(night: bool) -> float:
	if not night:
		return 0.0
	var ev := OS.get_environment("HD2D_NIGHT_TOE")
	if ev == "0":
		return 0.0
	if ev == "":
		return 0.3
	return clampf(float(ev), 0.0, 2.0)


func _night_toe_mask() -> Dictionary:
	var m := OS.get_environment("HD2D_NIGHT_TOE_MASK").strip_edges().to_lower()
	if m == "baseline" or m == "off":
		return {"ground": false, "tuft": false, "near": false}
	if m == "ground":
		return {"ground": true, "tuft": false, "near": false}
	if m == "tuft" or m == "cards":
		return {"ground": false, "tuft": true, "near": false}
	if m == "near":
		return {"ground": false, "tuft": false, "near": true}
	return {"ground": true, "tuft": true, "near": true}


func _bind_night_ground(mat: ShaderMaterial, gain: float, sky: Vector3) -> void:
	mat.set_shader_parameter("night_toe_gain", gain)
	mat.set_shader_parameter("night_sky_rgb", sky)
	# Same wide ground the near lawn already samples. Unset (0) keeps a material on the bake only.
	if ResourceLoader.exists("res://textures/near_macro.png"):
		mat.set_shader_parameter("night_macro", load("res://textures/near_macro.png"))
		mat.set_shader_parameter("night_macro_on", 1.0)
		mat.set_shader_parameter("night_region", Vector4(-340.0, -120.0, 340.0, 330.0))
	var outer := host.get_node_or_null("GroundOuter") as MeshInstance3D
	if outer and outer.material_override is ShaderMaterial:
		var om := outer.material_override as ShaderMaterial
		var otex = om.get_shader_parameter("albedo_tex")
		if otex is Texture2D:
			mat.set_shader_parameter("night_outer", otex)
			mat.set_shader_parameter("night_outer_on", 1.0)
			var osc = om.get_shader_parameter("uv_scale")
			if osc is Vector2:
				mat.set_shader_parameter("night_outer_scale", osc)
			var pm := outer.mesh as PlaneMesh
			if pm:
				var gp := outer.global_position
				mat.set_shader_parameter("night_outer_plane", Vector4(gp.x, gp.z, pm.size.x, pm.size.y))
		if mat == om:
			mat.set_shader_parameter("night_own_grass", 1.0)


func _apply_night_surface_toe(night: bool) -> void:
	var gain := _night_toe_gain(night)
	var mask := _night_toe_mask()
	var g := gain if mask["ground"] else 0.0
	var t := gain if mask["tuft"] else 0.0
	var n := gain if mask["near"] else 0.0
	var sky := _envv3("HD2D_NIGHT_SKY", Vector3(0.70, 0.92, 1.00))
	if _ground_mat:
		_bind_night_ground(_ground_mat, g, sky)
	# Outer gets the same gain only once the wide macro is bound. Without it the
	# repeating 1280×800 tile would emit on its own, which is the slab we are not adding.
	var go := host.get_node_or_null("GroundOuter") as MeshInstance3D
	if go and go.material_override is ShaderMaterial and ResourceLoader.exists("res://textures/near_macro.png"):
		_bind_night_ground(go.material_override as ShaderMaterial, g, sky)
	if _near_gold_mat:
		_near_gold_mat.set_shader_parameter("night_toe_gain", n)
		_near_gold_mat.set_shader_parameter("night_sky_rgb", sky)
	var tms: Array = host.get("_tuft_mats") as Array if host.get("_tuft_mats") is Array else []
	for tm in tms:
		if tm is ShaderMaterial:
			(tm as ShaderMaterial).set_shader_parameter("night_toe_gain", t)
			(tm as ShaderMaterial).set_shader_parameter("night_sky_rgb", sky)
	if _frames == 3 and night and OS.get_environment("HD2D_NIGHT_TOE_LOG") == "1":
		print(
			"vc27 night sky mode=", host.get("_mode"),
			" path=emission*albedo",
			" HD2D_NIGHT_TOE=", OS.get_environment("HD2D_NIGHT_TOE"),
			" mask=", OS.get_environment("HD2D_NIGHT_TOE_MASK"),
			" gain=", gain, " ground=", g, " tuft=", t, " near=", n,
			" sky=", sky,
			" mats ground=", _ground_mat != null, " near=", _near_gold_mat != null,
			" tuft_n=", tms.size()
		)


# v6.14 env helpers (tuning overrides; defaults ship)
func _envf_ad(k: String, d: float) -> float:
	var v := OS.get_environment(k)
	return float(v) if v != "" else d


func _envv3(k: String, d: Vector3) -> Vector3:
	var p := OS.get_environment(k).split(",")
	return Vector3(float(p[0]), float(p[1]), float(p[2])) if p.size() == 3 else d


# v6.15 baked warm-gold sun patches (tools/sun_gold_v6_15.py): ground inner + outer + near lawn, day only
var _gold_mats: Array = []
var _near_gold_mat: ShaderMaterial = null
var _gold_amt := 1.0
func _gold_setup() -> void:
	if not ResourceLoader.exists("res://textures/sun_gold_v615.png"):
		return
	_gold_amt = _envf_ad("HD2D_GOLDAMT", 1.0)
	var tex := load("res://textures/sun_gold_v615.png")
	var mats: Array = []
	if _near_gold_mat:
		mats.append([_near_gold_mat, _envv3("HD2D_GOLD", Vector3(1.85, 1.50, 0.78))])   # PC r1: 1.62 read too gentle on Mobile
	var gi = host.get("_ground_mat")
	if gi is ShaderMaterial:
		mats.append([gi, _envv3("HD2D_GOLDG", Vector3(1.60, 1.36, 0.80))])
	var go := host.get_node_or_null("GroundOuter") as MeshInstance3D
	if go and go.material_override is ShaderMaterial:
		mats.append([go.material_override, _envv3("HD2D_GOLDG", Vector3(1.60, 1.36, 0.80))])
	for e in mats:
		var mm: ShaderMaterial = e[0]
		mm.set_shader_parameter("gold_tex", tex)
		mm.set_shader_parameter("gold_half", 450.0)
		mm.set_shader_parameter("gold_gain", e[1])
		_gold_mats.append(mm)


# v6.15 (Kurt: edge tuft cards with silhouettes along the lawn edges / prop bases). Same tuft
# multimesh as the v6.4 edge tufts (2 crossed cards, tuft.gdshader: wind + 團絨 push). +2 sets.
func _edge_tufts_v615() -> void:
	if not host.has_method("_card_multimesh"):
		return
	var a: Array = []
	var b: Array = []
	var k := 0
	# prop footprints (x0, x1, z0, z1) incl. the spawned copies; pots / jar as squares
	var rects := [[-77.0, -68.0, 19.0, 25.0], [62.0, 82.0, 20.0, 28.0], [-46.0, -30.0, 37.0, 47.0], [32.0, 38.0, 19.0, 25.0],
		[-88.0, -74.0, 63.0, 77.0], [74.0, 88.0, 47.0, 61.0], [44.0, 54.0, 17.0, 27.0], [123.0, 133.0, 3.0, 13.0],
		[128.0, 142.0, 43.0, 57.0], [95.0, 105.0, -35.0, -25.0], [-81.0, -13.0, -40.0, -22.0]]
	for r in rects:
		var x0: float = r[0] - 1.8
		var x1: float = r[1] + 1.8
		var z0: float = r[2] - 1.8
		var z1: float = r[3] + 1.8
		var per := 2.0 * ((x1 - x0) + (z1 - z0))
		var n := int(per / 4.2)
		for i in n:
			var t := float(i) / float(n) * per
			var q := Vector2.ZERO
			if t < x1 - x0:
				q = Vector2(x0 + t, z1)                      # front edge (toward the camera) first
			elif t < (x1 - x0) + (z1 - z0):
				q = Vector2(x1, z1 - (t - (x1 - x0)))
			elif t < 2.0 * (x1 - x0) + (z1 - z0):
				q = Vector2(x1 - (t - (x1 - x0) - (z1 - z0)), z0)
			else:
				q = Vector2(x0, z0 + (t - 2.0 * (x1 - x0) - (z1 - z0)))
			k += 1
			q += Vector2(fposmod(float(k) * 0.618, 1.0) - 0.5, fposmod(float(k) * 0.382, 1.0) - 0.5) * 1.6
			if _path_d(q) < 13.0:
				continue
			(a if k % 3 != 0 else b).append(Vector3(q.x, q.y, float((k * 47) % 90)))
	# hedge / bush bases around the clearing (lawn edge)
	for bu in [Vector3(-125, 30, 20), Vector3(-130, -20, 18), Vector3(-118, 70, 16), Vector3(155, 25, 20), Vector3(148, -25, 18),
			Vector3(118, -55, 16), Vector3(-70, 125, 20), Vector3(95, 118, 20)]:
		for i in 14:
			var an := float(i) / 14.0 * TAU
			var rr: float = bu.z + 2.0 + 2.5 * fposmod(float(i) * 0.618, 1.0)
			var q := Vector2(bu.x + cos(an) * rr, bu.y + sin(an) * rr * 0.8)
			if _path_d(q) < 13.0:
				continue
			k += 1
			(a if k % 3 != 0 else b).append(Vector3(q.x, q.y, float((k * 53) % 90)))
	host.call("_card_multimesh", "res://textures/tiles/tuft_fg.png", a, 6.0)
	host.call("_card_multimesh", "res://textures/tiles/tuft_dark_b.png", b, 5.5)
	print("edge tufts v6.15 ", a.size() + b.size())
