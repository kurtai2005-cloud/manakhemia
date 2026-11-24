extends SceneTree

var _fails := 0
const SAMPLE := "農巡採吃欣賞獵看飽食心情親密體力餵食清潔摸摸鍛鍊地圖小屋農圃工坊草原跟寵離線收益結算進化完成露水莓星星果暖心湯"


func _initialize() -> void:
	var main := (load("res://scenes/Main.tscn") as PackedScene).instantiate()
	root.add_child(main)
	for _i in range(240):
		await process_frame
		if main.get_node_or_null("Phase1Hud") != null:
			break
	_font(main)
	await _overlap(main)
	_buttons()
	await _map()
	_idle_evo_save()
	if _fails == 0:
		print("P1_R11_GATES_OK")
		quit(0)
	else:
		print("P1_R11_GATES_FAIL ", _fails)
		quit(1)


func _fail(why: String) -> void:
	_fails += 1
	print("P1_FAIL ", why)


func _font(main: Node) -> void:
	var nodes: Array = []
	nodes.append_array(main.find_children("*", "Label", true, false))
	nodes.append_array(main.find_children("*", "Button", true, false))
	var missing := 0
	var chars := _chars()
	for node in nodes:
		var face: Font = (node as Control).get_theme_font("font")
		if face == null or not face.has_char(SAMPLE.unicode_at(0)):
			missing += 1
			_fail("font " + str(node.name))
			continue
		var text := str(node.get("text"))
		for i in text.length():
			var ch := text.unicode_at(i)
			if ch > 127 and String.chr(ch).strip_edges() != "" and not face.has_char(ch):
				missing += 1
				_fail("glyph " + text.substr(i, 1))
				break
	var theme := Vc27Fonts.ensure()
	var cmap_miss := 0
	for key in chars.keys():
		if not theme.has_char(int(key)):
			cmap_miss += 1
	for i in SAMPLE.length():
		if not theme.has_char(SAMPLE.unicode_at(i)):
			cmap_miss += 1
			_fail("sample " + SAMPLE.substr(i, 1))
	print("NODE_FONT_MISSING=%d" % missing)
	print("ALL_DATA_CMAP_CHECKED=%d" % chars.size())
	print("ALL_DATA_CMAP_MISSING=%d" % cmap_miss)


func _overlap(main: Node) -> void:
	var p1: Node = root.get_node("Phase1")
	p1.layout_override = true
	p1.layout_window = Vector2i(1080, 2280)
	p1.layout_safe = Rect2i(0, 84, 1080, 2148)
	p1.layout_viewport = Vector2(390, 844)
	var hud := main.get_node("Phase1Hud") as Phase1Hud
	hud.modal.visible = false
	hud.drawer.visible = false
	hud.feed_row.visible = false
	hud.train_row.visible = false
	hud.map_row.visible = false
	hud.apply_layout()
	await process_frame
	var safe := hud._safe()
	var rects: Array[Rect2] = []
	var overlap := 0
	var root_ui := hud.root
	for c in root_ui.get_children():
		if str(c.name) == "ZoneWash":
			continue
		if not (c is Control) or not (c as Control).is_visible_in_tree():
			continue
		var rr: Rect2 = (c as Control).get_global_rect()
		if rr.size.x < 2.0 or rr.size.y < 2.0:
			continue
		if rr.position.y < safe.position.y - 1.0 or rr.end.y > safe.end.y + 1.0:
			_fail("outside " + str(c.name))
		for prev in rects:
			if rr.intersects(prev):
				overlap += 1
				_fail("overlap " + str(c.name))
				break
		rects.append(rr)
	print("HUD_OVERLAP_COUNT=%d" % overlap)


func _buttons() -> void:
	var p1: Node = root.get_node("Phase1")
	var hud := p1.hud as Phase1Hud
	var dead := 0
	for b in hud.root.find_children("*", "Button", true, false):
		if not (b as Control).is_visible_in_tree():
			continue
		var before := int(p1.action_n)
		(b as Button).pressed.emit()
		if int(p1.action_n) <= before:
			dead += 1
			_fail("dead " + str(b.name))
	for row_name in ["FeedRow", "TrainRow", "MapRow"]:
		var row := hud.root.get_node(row_name) as Control
		row.visible = true
		for b in row.get_children():
			if b is Button:
				var before2 := int(p1.action_n)
				(b as Button).pressed.emit()
				if int(p1.action_n) <= before2:
					dead += 1
					_fail("dead " + str(b.name))
	if hud.drawer:
		hud.drawer.visible = true
		for b in hud.drawer.find_children("*", "Button", true, false):
			var before3 := int(p1.action_n)
			(b as Button).pressed.emit()
			if int(p1.action_n) <= before3:
				dead += 1
				_fail("dead " + str(b.name))
	if dead == 0:
		print("ZERO_DEAD_BUTTONS_PASS")


func _map() -> void:
	var world := root.get_node("Phase1").world as Phase1World
	var home := world.look_for("garden")
	var farm := world.look_for("zone_farm")
	var shop := world.look_for("zone_workshop")
	var field := world.look_for("prairie_edge")
	var span := home.distance_to(farm) + farm.distance_to(shop) + home.distance_to(field)
	if span < 256.0 * 3.0:
		_fail("span %s" % str(span))
		return
	if world.span_ratio() < 3.0:
		_fail("area")
		return
	var main := root.get_child(root.get_child_count() - 1)
	if main.has_method("phase1_glide_to"):
		main.phase1_glide_to(farm)
		var before: Vector3 = main.follow_pos
		for _i in range(20):
			await process_frame
		if main.follow_pos.distance_to(before) < 10.0:
			_fail("camera still")
			return
	print("EXPANDED_MAP_ZONES_PASS")


func _idle_evo_save() -> void:
	var sim: Node = root.get_node("Sim")
	var before := int(sim.state.get("pet_registry", {}).get("tuanrong", {}).get("stats", {}).get("exp", 0))
	var report: Dictionary = OfflineIdleEngine.settle(sim.state, int(Time.get_unix_time_from_system() * 1000.0), 3600000)
	if int(report.get("exp", 0)) <= 0:
		_fail("idle")
		return
	print("OFFLINE_IDLE_PASS")
	var evo: Dictionary = EvolutionEngine.force_next(root.get_node("Phase1").doc, sim.state)
	if not bool(evo.get("ok", false)):
		_fail("evo")
		return
	if int(sim.state["pet_registry"]["tuanrong"]["stats"]["exp"]) < before:
		_fail("exp drop")
		return
	print("BRANCHING_EVO_PASS")
	if not Phase1Registry.acyclic(sim.state):
		_fail("cycle")
		return
	var nested := false
	for key in sim.state["pet_registry"].keys():
		var row: Dictionary = sim.state["pet_registry"][key]
		if row.get("parent_ids") is Dictionary:
			nested = true
	if nested:
		_fail("nested")
		return
	print("FLAT_REGISTRY_NO_CYCLE_PASS")
	var shards := int(root.get_node("CollectionSystem").call("stardust"))
	sim.state.erase("pet_registry")
	Phase1Registry.ensure(sim.state)
	if int(root.get_node("CollectionSystem").call("stardust")) != shards:
		_fail("migration shards")
		return
	if not sim.state.get("pet_registry", {}).has("tuanrong"):
		_fail("migration pet")
		return
	print("SAVE_MIGRATION_PASS")


func _chars() -> Dictionary:
	var chars := {}
	var data := DirAccess.open("res://data")
	if data:
		data.list_dir_begin()
		var name := data.get_next()
		while name != "":
			if name.ends_with(".json"):
				_eat("res://data/" + name, chars)
			name = data.get_next()
	_walk("res://scripts", ".gd", chars)
	_walk("res://scenes", ".tscn", chars)
	return chars


func _walk(path: String, suffix: String, chars: Dictionary) -> void:
	var dir := DirAccess.open(path)
	if dir == null:
		return
	dir.list_dir_begin()
	var name := dir.get_next()
	while name != "":
		if not name.begins_with("."):
			var full := path + "/" + name
			if dir.current_is_dir():
				_walk(full, suffix, chars)
			elif name.ends_with(suffix):
				_eat(full, chars)
		name = dir.get_next()


func _eat(path: String, chars: Dictionary) -> void:
	var text := FileAccess.get_file_as_string(path)
	for i in text.length():
		var ch := text.unicode_at(i)
		if ch > 127 and String.chr(ch).strip_edges() != "":
			chars[ch] = true
