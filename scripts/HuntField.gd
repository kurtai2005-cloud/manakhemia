extends Node3D
class_name HuntField
## 草原 1 區 3D 野外：寵物撥草、撲小怪、抱果排隊返倉。低檔都係真 3D。

const FIELD := Vector3(0, 0, 520)

var ground: MeshInstance3D
var critters: Array = []
var fruit_nodes: Array = []
var bushes: Array = []
var warehouse: Node3D
var warehouse_stack: Node3D
var _built := false
var field_origin := Vector3(0, 0, 520)
var active := false
var walkers: Array = []
var _roles: Dictionary = {}
var _fruit_held: Dictionary = {}
var _t := 0.0
var _last_phase := ""


func _ready() -> void:
	visible = false


func setup() -> void:
	if _built:
		return
	_built = true
	if GameData and "m1b" in GameData:
		var p: Variant = GameData.m1b.get("hunt", {}).get("field_origin", [0, 0, 520])
		if p is Array and p.size() >= 3:
			field_origin = Vector3(float(p[0]), float(p[1]), float(p[2]))
	position = field_origin
	_build_ground()
	_build_bushes()
	_build_critters()
	name = "HuntField"


func _mat(col: Color, unshaded: bool = true) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = col
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED if unshaded else BaseMaterial3D.SHADING_MODE_PER_PIXEL
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	return m


func _box(sz: Vector3, col: Color, pos: Vector3) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var b := BoxMesh.new()
	b.size = sz
	mi.mesh = b
	mi.material_override = _mat(col)
	mi.position = pos
	add_child(mi)
	return mi


func _build_ground() -> void:
	ground = MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(420, 320)
	ground.mesh = plane
	ground.material_override = _mat(Color(0.55, 0.72, 0.38))
	ground.position = Vector3(0, 0.05, 0)
	add_child(ground)
	# 遠山卡
	var hills := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(520, 160)
	hills.mesh = pm
	hills.material_override = _mat(Color(0.62, 0.78, 0.88))
	hills.rotation_degrees = Vector3(-80, 0, 0)
	hills.position = Vector3(0, 70, -170)
	add_child(hills)


func _build_bushes() -> void:
	var spots := [
		Vector3(-70, 8, -40), Vector3(50, 8, -20), Vector3(-20, 8, 40),
		Vector3(80, 8, 30), Vector3(-90, 8, 50), Vector3(10, 8, -70),
	]
	for i in range(spots.size()):
		var mi := _box(Vector3(18, 16, 14), Color(0.28, 0.52, 0.22), spots[i])
		bushes.append(mi)


func _tex(path: String) -> Texture2D:
	if ResourceLoader.exists(path) or FileAccess.file_exists(path):
		return load(path)
	return null


func _sprite(tex: Texture2D, psize: float, pos: Vector3) -> Sprite3D:
	var s := Sprite3D.new()
	s.texture = tex
	s.pixel_size = psize
	s.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	s.alpha_cut = SpriteBase3D.ALPHA_CUT_DISCARD
	s.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	s.centered = true
	s.offset = Vector2(0, 16)
	s.position = pos
	add_child(s)
	return s


func _build_critters() -> void:
	var doc_path := "res://art-pet/sprites/hunt/critters/critters.json"
	var items: Array = []
	if FileAccess.file_exists(doc_path):
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(doc_path))
		if parsed is Dictionary:
			items = parsed.get("items", [])
	var spots := [Vector3(-60, 0, 10), Vector3(40, 0, 25), Vector3(-10, 0, 60), Vector3(70, 0, -50)]
	var i := 0
	for it in items:
		if not (it is Dictionary):
			continue
		var aid := str(it.get("id", ""))
		var tex := _tex("res://art-pet/sprites/hunt/critters/atlas_%s.png" % aid)
		if tex == null:
			continue
		# 用圖集第一格（idle）
		var at := AtlasTexture.new()
		at.atlas = tex
		var sz := int(it.get("size", 32))
		at.region = Rect2(0, 0, sz, sz)
		at.filter_clip = true
		var pos: Vector3 = spots[i % spots.size()]
		var spr := _sprite(at, 1.0, pos + Vector3(0, 0, 0))
		spr.position.y = 0
		spr.offset = Vector2(0, float(sz) * 0.5)
		critters.append({"id": aid, "big": bool(it.get("big", false)), "fruit": str(it.get("fruit", "")), "node": spr, "home": spr.position, "alive": true})
		i += 1


func art_fruit_tex(art_id: String) -> Texture2D:
	var p := "res://art-pet/sprites/hunt/fruits/%s.png" % art_id
	return _tex(p)


func attach_warehouse(root: Node3D) -> void:
	warehouse = root
	if warehouse and warehouse.get_node_or_null("Stack") == null:
		warehouse_stack = Node3D.new()
		warehouse_stack.name = "Stack"
		warehouse.add_child(warehouse_stack)


func begin(team_walkers: Array) -> void:
	setup()
	visible = true
	active = true
	walkers = team_walkers
	_t = 0.0
	_last_phase = ""
	_roles.clear()
	_fruit_held.clear()
	# 性格分工：第一隻撥草、第二隻撲、第三隻抱
	var jobs := ["part_grass", "pounce", "carry_fruit"]
	for i in range(walkers.size()):
		var w: Walker = walkers[i]
		_roles[w] = jobs[i % jobs.size()]
		var brain: Node = w.get_node_or_null("PetBrain")
		if brain:
			brain.busy = true
			if "pending_tap" in brain:
				brain.pending_tap = ""
		w.brain_driven = false
		w.cancel_move()


func end_duty() -> void:
	active = false
	for w in walkers:
		if w == null or not is_instance_valid(w):
			continue
		w.stop_live()
		w.brain_driven = true
		var brain: Node = w.get_node_or_null("PetBrain")
		if brain:
			brain.busy = false
	walkers = []


func field_pos(local: Vector3) -> Vector3:
	return field_origin + local


func tick(dt: float, phase: String) -> void:
	if not active:
		return
	_t += dt
	if phase != _last_phase:
		_last_phase = phase
		_on_phase(phase)
	# 小怪被撲之後變果碌走
	for c in critters:
		if not bool(c.get("alive", true)) and c.get("roll") != null:
			var spr: Sprite3D = c["node"]
			var dest: Vector3 = c["roll"]
			spr.position = spr.position.lerp(dest, clampf(dt * 2.4, 0.0, 1.0))
	# 抱果跟隨
	for w in walkers:
		if w == null:
			continue
		if _fruit_held.has(w):
			var fs: Sprite3D = _fruit_held[w]
			if is_instance_valid(fs):
				fs.global_position = w.global_position + Vector3(0, 28, 2)


func _on_phase(phase: String) -> void:
	match phase:
		HuntSystem.PHASE_HUNT:
			_scatter()
		HuntSystem.PHASE_CARRY:
			_pickup_and_line()
		HuntSystem.PHASE_READY, HuntSystem.PHASE_HOME:
			_deposit()


func _scatter() -> void:
	for i in range(walkers.size()):
		var w: Walker = walkers[i]
		if w == null:
			continue
		var bush: Vector3 = field_pos(Vector3(-70 + i * 60, 0, -20 + (i % 2) * 40))
		w.go_to(bush)
		var role := str(_roles.get(w, "part_grass"))
		if not w.play_live_clip(role, role == "carry_fruit"):
			w.play_live_clip("sniff")
	# 撲一隻小怪
	if HuntSystem and HuntSystem.big_encounter:
		for c in critters:
			if bool(c.get("big", false)):
				_pounce_critter(c)
				break
	else:
		for c in critters:
			if not bool(c.get("big", false)) and bool(c.get("alive", true)):
				_pounce_critter(c)
				break


func _pounce_critter(c: Dictionary) -> void:
	c["alive"] = false
	var spr: Sprite3D = c["node"]
	# 換成果
	var art := str(c.get("fruit", "starberry"))
	var tex := art_fruit_tex(art)
	if tex:
		spr.texture = tex
		spr.pixel_size = 1.0
	c["roll"] = spr.position + Vector3(40, 0, 20)
	if walkers.size():
		var w: Walker = walkers[0]
		w.play_live_clip("pounce")
		if HuntSystem and HuntSystem.big_encounter and walkers.size() >= 2:
			# 驚嚇：第二隻靠近（撐葉 clip 未到就用 nuzzle／scratch）
			var pal: Walker = walkers[1]
			pal.go_to(w.global_position + Vector3(12, 0, 0))
			if not pal.play_live_clip("scratch"):
				pal.play_live_clip("sneeze")
			w.play_live_clip("cheer")


func _pickup_and_line() -> void:
	var gate := field_origin + Vector3(0, 0, -140)
	for i in range(walkers.size()):
		var w: Walker = walkers[i]
		if w == null:
			continue
		# 抱一粒果
		var frs: Array = HuntSystem.fruits if HuntSystem else []
		var art := "starberry"
		if i < frs.size():
			art = str(frs[i].get("art", HuntSystem.art_fruit(str(frs[i].get("id", "")))))
		var tex := art_fruit_tex(art)
		if tex and not _fruit_held.has(w):
			var fs := Sprite3D.new()
			fs.texture = tex
			fs.pixel_size = 1.0
			fs.billboard = BaseMaterial3D.BILLBOARD_ENABLED
			fs.alpha_cut = SpriteBase3D.ALPHA_CUT_DISCARD
			fs.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
			fs.centered = true
			add_child(fs)
			_fruit_held[w] = fs
			fruit_nodes.append(fs)
		w.play_live_clip("carry_fruit", true)
		# 排隊：隊長行頭，其他人跟住
		if i == 0:
			w.go_to(gate)
		else:
			var lead: Walker = walkers[0]
			w.follow_node(lead, 18.0 + float(i) * 6.0)


func _deposit() -> void:
	for w in walkers:
		if w and is_instance_valid(w):
			w.play_live_clip("cheer")
			w.cancel_follow()
	# 果堆入倉
	if warehouse_stack:
		for w in _fruit_held.keys():
			var fs: Sprite3D = _fruit_held[w]
			if not is_instance_valid(fs):
				continue
			var n := warehouse_stack.get_child_count()
			fs.get_parent().remove_child(fs)
			warehouse_stack.add_child(fs)
			fs.position = Vector3(0, 8 + n * 10, 0)
		_fruit_held.clear()
	# 寵物返花園入口，責任喺 Main 放返
