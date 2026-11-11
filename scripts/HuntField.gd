extends Node3D
class_name HuntField
## 草原 1 區 3D 野外：實例化遊美 prairie 網格／貼圖；寵物同花園一樣直立 billboard。
## 打唔中（化妝）：受驚走位＋再追（sfx_critter_startle），唔播 sfx_mg_miss、唔扣戰利品。
## 捉到：變成果碌走，播 sfx_mg_catch。miss 機率／上限由 hunting.json pounce_miss 讀。

const ROOT := "res://art-pet/scenes/hunt3d/prairie/"

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
var cam_data: Dictionary = {}
var objects_doc: Dictionary = {}
var _did_catch := false
var _shake: Array = []  # {node, home, t}
var _next_pounce_at := 0.0
var _pounce_rng: RandomNumberGenerator


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
	if GameData and "m1c" in GameData and not GameData.m1c.is_empty():
		var p2: Variant = GameData.m1c.get("hunt", {}).get("field_origin", [])
		if p2 is Array and p2.size() >= 3:
			field_origin = Vector3(float(p2[0]), float(p2[1]), float(p2[2]))
	position = field_origin
	objects_doc = GardenLoader.load_json(ROOT + "objects.json")
	cam_data = GardenLoader.load_json(ROOT + "camera.json")
	if GameData and "m1c" in GameData:
		var ov: Dictionary = GameData.m1c.get("hunt", {}).get("camera", {})
		if not ov.is_empty():
			for k in ov.keys():
				cam_data[k] = ov[k]
	_build_ground()
	_build_meshes()
	_build_backdrops()
	_build_critters()
	name = "HuntField"


func look_target() -> Vector3:
	var t: Variant = cam_data.get("target", [0, 30, -72])
	if t is Array and t.size() >= 3:
		return field_origin + Vector3(float(t[0]), float(t[1]), float(t[2]))
	return field_origin + Vector3(0, 30, -72)


func cam_pitch() -> float:
	return float(cam_data.get("pitchDeg", 30))


func cam_dist() -> float:
	return float(cam_data.get("dist", 580))


func _tex(path: String) -> Texture2D:
	if path == "":
		return null
	if ResourceLoader.exists(path) or FileAccess.file_exists(path):
		return load(path)
	return null


func _build_ground() -> void:
	var g: Dictionary = objects_doc.get("ground", {})
	var cover: Array = g.get("cover", [-128, 128, -128, 128])
	var x0 := float(cover[0]) if cover.size() >= 4 else -128.0
	var x1 := float(cover[1]) if cover.size() >= 4 else 128.0
	var z0 := float(cover[2]) if cover.size() >= 4 else -128.0
	var z1 := float(cover[3]) if cover.size() >= 4 else 128.0
	# outer tiles first
	var tile_rel := str(g.get("tile", g.get("tile3x", "ground/ground_tile.png")))
	var tile3 := str(g.get("tile3x", ""))
	var tile_tex := _tex(ROOT + (tile3 if tile3 != "" else tile_rel))
	if tile_tex == null:
		tile_tex = _tex(ROOT + tile_rel)
	var ext: Dictionary = g.get("tileExtent", {})
	var xr: Array = ext.get("x", [-640, 640])
	var zr: Array = ext.get("z", [-480, 320])
	if tile_tex:
		var tmi := MeshInstance3D.new()
		tmi.mesh = GardenLoader.xz_plane(float(xr[0]), float(xr[1]), float(zr[0]), float(zr[1]), Vector2(-128, -128), 64.0)
		tmi.material_override = GardenLoader.opaque_tex_mat(tile_tex, true, true, true)
		tmi.position.y = -0.2
		tmi.name = "PrairieTile"
		add_child(tmi)
	var img := str(g.get("image3x", g.get("file3x", g.get("image", g.get("file", "ground/ground.png")))))
	var gtex := _tex(ROOT + img)
	if gtex == null:
		gtex = _tex(ROOT + str(g.get("image", g.get("file", "ground/ground.png"))))
	ground = MeshInstance3D.new()
	ground.mesh = GardenLoader.xz_plane(x0, x1, z0, z1, Vector2(-128, -128), 256.0)
	if gtex:
		ground.material_override = GardenLoader.opaque_tex_mat(gtex, true, false)
	ground.position.y = 0.05
	ground.name = "PrairieGround"
	add_child(ground)


func _build_meshes() -> void:
	bushes.clear()
	for o in objects_doc.get("objects", []):
		if not (o is Dictionary) or str(o.get("type", "")) != "mesh":
			continue
		var rel := str(o.get("mesh", ""))
		var doc := GardenLoader.load_json(ROOT + rel)
		if doc.is_empty():
			# try glb
			var glb_rel := str(o.get("glb", ""))
			if glb_rel != "" and ResourceLoader.exists(ROOT + glb_rel):
				var ps: Resource = load(ROOT + glb_rel)
				var inst: Node = null
				if ps is PackedScene:
					inst = (ps as PackedScene).instantiate()
				if inst:
					inst.position = Vector3(float(o.get("x", 0)), float(o.get("y", 0)), float(o.get("z", 0)))
					inst.rotation_degrees.y = float(o.get("yawDeg", 0))
					add_child(inst)
					bushes.append(inst)
			continue
		var tex_rel := str(doc.get("texture3x", doc.get("texture", "")))
		var tex := _tex(ROOT + tex_rel)
		if tex == null:
			tex = _tex(ROOT + str(doc.get("texture", "")))
		var unlit := false
		var mat := GardenLoader.make_mat(tex, unlit, float(doc.get("alphaTest", 0.5)))
		if bool(doc.get("doubleSided", false)):
			mat.cull_mode = BaseMaterial3D.CULL_DISABLED
		var mi := MeshInstance3D.new()
		mi.mesh = GardenLoader.mesh_from_json(doc, true)
		mi.material_override = mat
		mi.position = Vector3(float(o.get("x", 0)), float(o.get("y", 0)), float(o.get("z", 0)))
		mi.rotation_degrees.y = float(o.get("yawDeg", 0))
		if not bool(o.get("castShadow", true)):
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mi.name = str(o.get("id", "mesh"))
		add_child(mi)
		bushes.append(mi)


func _build_backdrops() -> void:
	for b in objects_doc.get("backdrops", []):
		if not (b is Dictionary):
			continue
		var rel := str(b.get("file3x", b.get("file", "")))
		var tex := _tex(ROOT + rel)
		if tex == null:
			tex = _tex(ROOT + str(b.get("file", "")))
		if tex == null:
			continue
		var sz: Array = b.get("sizePx", [512, 128])
		var w := float(sz[0]) if sz.size() >= 1 else 512.0
		var h := float(sz[1]) if sz.size() >= 2 else 128.0
		var mi := MeshInstance3D.new()
		mi.mesh = GardenLoader.backdrop_mesh(w, h)
		var mat := GardenLoader.make_mat(tex, true, 0.01)
		mi.material_override = mat
		mi.position = Vector3(0, 0, float(b.get("z", -400)))
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mi.name = str(b.get("id", "backdrop"))
		add_child(mi)
	_build_house_cover()


func _house_cover_cfg() -> Dictionary:
	if GameData and "m1c" in GameData:
		return GameData.m1c.get("hunt", {}).get("hide_garden_house", {})
	return {}


func _build_house_cover() -> void:
	# 遠丘／樹卡擋花園小屋；數字喺 m1c.json
	var cfg := _house_cover_cfg()
	if not bool(cfg.get("enabled", true)):
		return
	var cov: Dictionary = cfg.get("cover", {})
	if cov.is_empty():
		cov = {"id": "bg_hills_cover", "file3x": "backdrop/bg_hills@3x.png", "file": "backdrop/bg_hills.png", "z": -400, "sizePx": [1024, 220]}
	var rel := str(cov.get("file3x", cov.get("file", "")))
	var tex := _tex(ROOT + rel)
	if tex == null:
		tex = _tex(ROOT + str(cov.get("file", "")))
	if tex == null:
		return
	var sz: Array = cov.get("sizePx", [1024, 220])
	var w := float(sz[0]) if sz.size() >= 1 else 1024.0
	var h := float(sz[1]) if sz.size() >= 2 else 220.0
	var mi := MeshInstance3D.new()
	mi.mesh = GardenLoader.backdrop_mesh(w, h)
	var mat := GardenLoader.make_mat(tex, true, 0.01)
	mi.material_override = mat
	mi.position = Vector3(0, 0, float(cov.get("z", -400)))
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.name = str(cov.get("id", "bg_hills_cover"))
	add_child(mi)


func has_house_cover() -> bool:
	return get_node_or_null("bg_hills_cover") != null


func _sprite(tex: Texture2D, psize: float, pos: Vector3, frame_h: float = 32.0) -> Sprite3D:
	var s := Sprite3D.new()
	s.texture = tex
	s.pixel_size = psize
	# 同花園寵物：直立，只繞 Y 轉，唔會平躺向鏡頭
	s.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
	s.alpha_cut = SpriteBase3D.ALPHA_CUT_DISCARD
	s.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	s.shaded = false
	s.centered = true
	s.offset = Vector2(0, frame_h * 0.5)
	s.position = pos
	s.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(s)
	return s


func _build_critters() -> void:
	critters.clear()
	var doc_path := "res://art-pet/sprites/hunt/critters/critters.json"
	var items: Array = []
	if FileAccess.file_exists(doc_path):
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(doc_path))
		if parsed is Dictionary:
			items = parsed.get("items", [])
	var by_id: Dictionary = {}
	for it in items:
		if it is Dictionary:
			by_id[str(it.get("id", ""))] = it
	var spawn: Array = []
	var cdoc: Dictionary = objects_doc.get("critters", {})
	if cdoc.get("spawn") is Array:
		spawn = cdoc.get("spawn")
	if spawn.is_empty():
		spawn = [
			{"id": "dewlet", "x": -58, "z": 8},
			{"id": "loambun", "x": 66, "z": -18},
			{"id": "seedfluff", "x": 50, "z": 10},
			{"id": "mossback", "x": -78, "z": -100, "big": true},
		]
	for sp in spawn:
		if not (sp is Dictionary):
			continue
		var aid := str(sp.get("id", ""))
		var meta: Dictionary = by_id.get(aid, {})
		var tex := _tex("res://art-pet/sprites/hunt/critters/atlas_%s.png" % aid)
		if tex == null:
			continue
		var at := AtlasTexture.new()
		at.atlas = tex
		var sz := int(meta.get("size", 32))
		at.region = Rect2(0, 0, sz, sz)
		at.filter_clip = true
		var pos := Vector3(float(sp.get("x", 0)), 0, float(sp.get("z", 0)))
		var spr := _sprite(at, 1.0, pos, float(sz))
		spr.name = "Critter_%s" % aid
		critters.append({
			"id": aid,
			"big": bool(sp.get("big", meta.get("big", false))),
			"fruit": str(meta.get("fruit", "")),
			"node": spr,
			"home": spr.position,
			"alive": true,
			"startled": false,
			"caught": false,
			"size": sz,
			"atlas": tex,
		})


func art_fruit_tex(art_id: String) -> Texture2D:
	var p := "res://art-pet/sprites/hunt/fruits/%s.png" % art_id
	return _tex(p)


func attach_warehouse(root: Node3D) -> void:
	warehouse = root
	if warehouse and warehouse.get_node_or_null("Stack") == null:
		warehouse_stack = Node3D.new()
		warehouse_stack.name = "Stack"
		warehouse.add_child(warehouse_stack)


func hunt_sfx(key: String) -> String:
	var sfx: Dictionary = {}
	if GameData and "m1c" in GameData:
		sfx = GameData.m1c.get("hunt", {}).get("sfx", {})
	var defaults := {
		"start": "sfx_mg_start",
		"event": "sfx_event_treasure_hunt",
		"catch": "sfx_mg_catch",
		"win": "sfx_mg_win",
		"miss_startle": "sfx_critter_startle",
		"miss_shake": "sfx_critter_shake",
		"enter": "sfx_hunt_enter",
		"pounce": "sfx_hunt_pounce",
		"catch_transform": "sfx_critter_transform",
		"catch_roll": "sfx_critter_roll",
		"carry_pickup": "sfx_pet_pickup",
	}
	return str(sfx.get(key, defaults.get(key, "")))


func begin(team_walkers: Array) -> void:
	setup()
	visible = true
	active = true
	walkers = team_walkers
	_t = 0.0
	_last_phase = ""
	_roles.clear()
	_fruit_held.clear()
	_did_catch = false
	_shake.clear()
	_next_pounce_at = 0.0
	if _pounce_rng == null:
		_pounce_rng = RandomNumberGenerator.new()
		_pounce_rng.randomize()
	# reset critters
	for c in critters:
		c["alive"] = true
		c["startled"] = false
		c["caught"] = false
		c["misses"] = 0
		c["attempts"] = 0
		c.erase("roll")
		c.erase("flee")
		var spr: Sprite3D = c["node"]
		if spr:
			spr.position = c["home"]
			spr.visible = true
			if c.get("atlas"):
				var at := AtlasTexture.new()
				at.atlas = c["atlas"]
				var sz := int(c.get("size", 32))
				at.region = Rect2(0, 0, sz, sz)
				at.filter_clip = true
				spr.texture = at
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
	# 出發／入場聲由 AudioManager 接 HuntSystem 信號；唔喺呢度重播


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


func mesh_instance_count() -> int:
	var n := 0
	for c in get_children():
		if c is MeshInstance3D:
			n += 1
		n += _count_meshes(c)
	return n


func _count_meshes(n: Node) -> int:
	var c := 0
	for ch in n.get_children():
		if ch is MeshInstance3D:
			c += 1
		c += _count_meshes(ch)
	return c


func tick(dt: float, phase: String) -> void:
	if not active:
		return
	_t += dt
	if phase != _last_phase:
		_last_phase = phase
		_on_phase(phase)
	if phase == HuntSystem.PHASE_HUNT and not _did_catch and _t >= _next_pounce_at:
		try_pounce()
	# 受驚走位＋震動
	for c in critters:
		if bool(c.get("caught", false)):
			continue
		var spr: Sprite3D = c.get("node")
		if spr == null or not is_instance_valid(spr):
			continue
		if c.get("flee") != null:
			var dest: Vector3 = c["flee"]
			spr.position = spr.position.lerp(dest, clampf(dt * 3.0, 0.0, 1.0))
			c["home"] = spr.position
	for s in _shake:
		var spr2: Sprite3D = s.get("node")
		if spr2 == null or not is_instance_valid(spr2):
			continue
		s["t"] = float(s.get("t", 0)) + dt
		var tt: float = s["t"]
		if tt > 0.7:
			continue
		var amp := 3.0 * (1.0 - tt / 0.7)
		spr2.position = spr2.position + Vector3(sin(tt * 28.0) * amp * dt * 20.0, 0, cos(tt * 22.0) * amp * dt * 8.0)
	# 小怪被捉之後變果碌走
	for c in critters:
		if bool(c.get("caught", false)) and c.get("roll") != null:
			var spr3: Sprite3D = c["node"]
			var dest2: Vector3 = c["roll"]
			spr3.position = spr3.position.lerp(dest2, clampf(dt * 2.4, 0.0, 1.0))
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
			_next_pounce_at = _t
		HuntSystem.PHASE_CARRY:
			if not _did_catch:
				# 觀看時段結束仍未中，呢下必中（化妝；戰利品照 hunting.json）
				try_pounce(true)
			_pickup_and_line()
		HuntSystem.PHASE_READY, HuntSystem.PHASE_HOME:
			_deposit()
			_play_hook(hunt_sfx("win"))


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


func _pick_target() -> Dictionary:
	if HuntSystem and HuntSystem.big_encounter:
		for c in critters:
			if bool(c.get("big", false)):
				return c
	for c in critters:
		if not bool(c.get("big", false)) and bool(c.get("alive", true)):
			return c
	if critters.size():
		return critters[0]
	return {}


func lead_pet_id() -> String:
	if walkers.size() and walkers[0] is Walker:
		return str((walkers[0] as Walker).character)
	if HuntSystem and HuntSystem.team.size():
		return str(HuntSystem.team[0])
	return "tuanrong"


func retry_sec() -> float:
	return float(HuntSystem.pounce_miss_cfg().get("retry_sec", 1.6)) if HuntSystem else 1.6


func flee_units() -> float:
	return float(HuntSystem.pounce_miss_cfg().get("flee_units", 36)) if HuntSystem else 36.0


## 一次撲。force_hit=true 必中。force_roll 0..1 覆寫隨機（測試）。回傳 "miss" / "catch" / ""。
func try_pounce(force_hit: bool = false, force_roll: float = -1.0) -> String:
	if _did_catch:
		return ""
	var c: Dictionary = _pick_target()
	if c.is_empty():
		return ""
	c["attempts"] = int(c.get("attempts", 0)) + 1
	var misses := int(c.get("misses", 0))
	var is_miss := false
	if not force_hit and HuntSystem:
		is_miss = HuntSystem.roll_is_miss(lead_pet_id(), misses, _pounce_rng, force_roll)
	# 每次撲都有體勢氣流（a/b Randomizer）
	_play_hook(hunt_sfx("pounce"))
	if is_miss:
		_apply_miss(c)
		_next_pounce_at = _t + retry_sec()
		return "miss"
	_apply_catch(c)
	return "catch"


func _apply_miss(c: Dictionary) -> void:
	c["misses"] = int(c.get("misses", 0)) + 1
	c["startled"] = true
	# 受驚＋走位＋再追；唔播 sfx_mg_miss，唔扣戰利品
	_play_hook(hunt_sfx("miss_startle"))
	_play_hook(hunt_sfx("miss_shake"))
	var spr: Sprite3D = c.get("node")
	var rng := _pounce_rng if _pounce_rng else RandomNumberGenerator.new()
	var fu := flee_units()
	var ang := rng.randf() * TAU
	var from: Vector3 = spr.position if spr else c.get("home", Vector3.ZERO)
	var flee: Vector3 = from + Vector3(cos(ang) * fu, 0, sin(ang) * fu)
	c["flee"] = flee
	c["home"] = flee
	if spr:
		_shake.append({"node": spr, "home": flee, "t": 0.0})
	if walkers.size():
		var w: Walker = walkers[0]
		w.play_live_clip("pounce")
		w.go_to(field_origin + flee)


func _apply_catch(c: Dictionary) -> void:
	if _did_catch:
		return
	_did_catch = true
	_play_hook(hunt_sfx("catch"))
	var tms := 100
	var rms := 120
	if GameData and "m1c" in GameData:
		var sx: Dictionary = GameData.m1c.get("hunt", {}).get("sfx", {})
		tms = int(sx.get("catch_transform_delay_ms", 100))
		rms = int(sx.get("catch_roll_delay_ms", 120))
	_play_hook_later(hunt_sfx("catch_transform"), float(tms) / 1000.0)
	_play_hook_later(hunt_sfx("catch_roll"), float(rms) / 1000.0)
	_pounce_critter(c)


func _miss_one() -> void:
	# 測試／舊呼叫：強制呢下 miss（若未達上限）
	try_pounce(false, 0.0)


func _catch_one() -> void:
	try_pounce(true)


func _pounce_critter(c: Dictionary) -> void:
	c["alive"] = false
	c["caught"] = true
	var spr: Sprite3D = c["node"]
	# 換成果，碌走
	var art := str(c.get("fruit", "starberry"))
	if art == "" or art == "starberry":
		# prefer mapped fruit from pending
		if HuntSystem and HuntSystem.fruits.size():
			art = str(HuntSystem.fruits[0].get("art", HuntSystem.art_fruit(str(HuntSystem.fruits[0].get("id", "")))))
	var tex := art_fruit_tex(art)
	if tex and spr:
		spr.texture = tex
		spr.pixel_size = 1.0
		spr.offset = Vector2(0, 16)
	c["roll"] = (spr.position if spr else c.get("home", Vector3.ZERO)) + Vector3(40, 0, 20)
	if walkers.size():
		var w: Walker = walkers[0]
		w.play_live_clip("pounce")
		if HuntSystem and HuntSystem.big_encounter and walkers.size() >= 2:
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
		var frs: Array = HuntSystem.fruits if HuntSystem else []
		var art := "starberry"
		if i < frs.size():
			art = str(frs[i].get("art", HuntSystem.art_fruit(str(frs[i].get("id", "")))))
		var tex := art_fruit_tex(art)
		if tex and not _fruit_held.has(w):
			var fs := Sprite3D.new()
			fs.texture = tex
			fs.pixel_size = 1.0
			fs.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
			fs.alpha_cut = SpriteBase3D.ALPHA_CUT_DISCARD
			fs.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
			fs.centered = true
			fs.offset = Vector2(0, 16)
			add_child(fs)
			_fruit_held[w] = fs
			fruit_nodes.append(fs)
			_play_hook(hunt_sfx("carry_pickup"))
		w.play_live_clip("carry_fruit", true)
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


func _play_hook(hook: String) -> void:
	if hook == "" or hook == "sfx_mg_miss":
		return
	if AudioManager and AudioManager.has_method("play"):
		AudioManager.play(hook, null)


func _play_hook_later(hook: String, delay_sec: float) -> void:
	if hook == "" or hook == "sfx_mg_miss":
		return
	if AudioManager and AudioManager.has_method("play_later"):
		AudioManager.play_later(hook, delay_sec, null)
	elif delay_sec <= 0.0:
		_play_hook(hook)
