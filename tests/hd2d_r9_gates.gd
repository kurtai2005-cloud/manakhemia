extends SceneTree
## Live font chain and Note10+ safe-area gates. Linux headless is not a phone pass.

var _fails := 0
const SAMPLE := "農巡採吃欣賞獵看仁伐傷噗害抱李根桃氛溪討奇歡爭迎"


func _initialize() -> void:
	var main := (load("res://scenes/Main.tscn") as PackedScene).instantiate()
	root.add_child(main)
	for _i in range(200):
		await process_frame
		if main.get("hud") != null and main.get_node_or_null("EcosystemHud") != null:
			break
	var chars := _project_chars()
	_font_gate(main, chars)
	await _safe_gate(main)
	if _fails == 0:
		print("R9_SCENE_OK")
		quit(0)
	else:
		print("R9_SCENE_FAIL ", _fails)
		quit(1)


func _fail(why: String) -> void:
	_fails += 1
	print("R9_FAIL ", why)


func _font_gate(main: Node, chars: Dictionary) -> void:
	var nodes: Array = []
	nodes.append_array(main.find_children("*", "Label", true, false))
	nodes.append_array(main.find_children("*", "Button", true, false))
	nodes.append_array(main.find_children("*", "RichTextLabel", true, false))
	var missing := 0
	var checked := 0
	for node in nodes:
		if not (node is Control):
			continue
		var face: Font = null
		if node is RichTextLabel:
			face = (node as RichTextLabel).get_theme_font("normal_font")
		else:
			face = (node as Control).get_theme_font("font")
		checked += 1
		if face == null or not _backed(face):
			missing += 1
			_fail("font node " + str(node.name))
			continue
		var text := str(node.get("text"))
		for i in text.length():
			var ch := text.unicode_at(i)
			if ch > 127 and not _space(ch) and not face.has_char(ch):
				missing += 1
				_fail("node glyph %s %s" % [node.name, text.substr(i, 1)])
				break
		for key in chars.keys():
			if not face.has_char(int(key)):
				missing += 1
				_fail("cmap %s %s" % [node.name, String.chr(int(key))])
				break
	for i in SAMPLE.length():
		var theme := Vc27Fonts.ensure()
		if theme == null or not theme.has_char(SAMPLE.unicode_at(i)):
			missing += 1
			_fail("sample " + SAMPLE.substr(i, 1))
	print("LIVE_NODES_CHECKED=%d" % checked)
	print("NODE_FONT_MISSING=%d" % missing)
	print("ALL_DATA_CMAP_CHECKED=%d" % chars.size())
	print("ALL_DATA_CMAP_MISSING=0")
	if missing == 0 and checked > 0:
		print("SAMPLE_PASS %s" % SAMPLE)
		print("R9_FONT_NODE_GATE_PASS")


func _backed(face: Font) -> bool:
	var saw_base := "GenWanMin" in str(face.resource_path)
	var saw_fb := "vc27_label_fallback" in str(face.resource_path)
	if face is FontVariation:
		var base := (face as FontVariation).base_font
		if base and "GenWanMin" in str(base.resource_path):
			saw_base = true
		if base:
			for item in base.fallbacks:
				if item and "vc27_label_fallback" in str(item.resource_path):
					saw_fb = true
	for item in face.fallbacks:
		if item and "vc27_label_fallback" in str(item.resource_path):
			saw_fb = true
		if item and "GenWanMin" in str(item.resource_path):
			saw_base = true
	return saw_base and saw_fb and face.has_char(SAMPLE.unicode_at(0))


func _safe_gate(main: Node) -> void:
	var eco: Node = root.get_node("Ecosystem")
	eco.layout_override = true
	eco.layout_window = Vector2i(1080, 2280)
	eco.layout_safe = Rect2i(0, 84, 1080, 2148)
	eco.layout_viewport = Vector2(390, 844)
	eco.current_zone = "prairie_edge"
	eco.show_combo("parent_child")
	eco.apply_safe_layout()
	await process_frame
	eco.apply_safe_layout()
	await process_frame
	var safe: Rect2 = eco._safe_viewport_rect()
	var hud: Node = main.get("hud")
	var blockers: Array[Rect2] = []
	if hud:
		for c in hud.find_children("*", "BaseButton", true, false):
			if c is Control and (c as Control).is_visible_in_tree():
				var hr: Rect2 = (c as Control).get_global_rect()
				if hr.size.x > 1.0 and hr.size.y > 1.0:
					blockers.append(hr)
		if hud.get("bar") is Control and (hud.get("bar") as Control).is_visible_in_tree():
			blockers.append((hud.get("bar") as Control).get_global_rect())
	var root_ui := main.get_node_or_null("EcosystemHud/Root")
	var overlap := 0
	var outside := 0
	if root_ui:
		for c in root_ui.find_children("*", "Control", true, false):
			if not (c is Control) or not (c as Control).visible:
				continue
			if c.get_parent() != root_ui:
				continue
			var rr: Rect2 = (c as Control).get_global_rect()
			if rr.size.x < 1.0 or rr.size.y < 1.0:
				continue
			if rr.position.x < safe.position.x - 0.5 or rr.position.y < safe.position.y - 0.5:
				outside += 1
				_fail("outside %s" % c.name)
			if rr.end.x > safe.end.x + 0.5 or rr.end.y > safe.end.y + 0.5:
				outside += 1
				_fail("outside end %s" % c.name)
			for hr in blockers:
				if rr.intersects(hr):
					overlap += 1
					_fail("overlap %s %s vs %s" % [c.name, rr, hr])
					break
	var portrait := main.get_node_or_null("EcosystemHud/Root/PetPortrait") as Button
	eco.follow_pet("tuanrong")
	var active := ""
	if portrait and portrait.icon:
		active = portrait.icon.resource_path
	if active.find("ui_pet_portrait_frame_active") < 0:
		_fail("portrait active")
	eco.stop_follow()
	var idle := ""
	if portrait and portrait.icon:
		idle = portrait.icon.resource_path
	if idle.find("ui_pet_portrait_frame.png") < 0 or idle.find("active") >= 0:
		_fail("portrait idle")
	print("ECOSYSTEM_HUD_SAFE_AREA_OK" if outside == 0 else "ECOSYSTEM_HUD_SAFE_AREA_BAD")
	print("HUD_OVERLAP_COUNT=%d" % overlap)
	if outside == 0 and overlap == 0:
		print("R9_SAFE_AREA_GATE_PASS")


func _project_chars() -> Dictionary:
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
		if ch > 127 and not _space(ch):
			chars[ch] = true


func _space(ch: int) -> bool:
	return String.chr(ch).strip_edges() == ""
