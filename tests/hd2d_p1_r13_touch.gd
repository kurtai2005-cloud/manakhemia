extends SceneTree
## Dock taps, pan deadzone, and the r13 prop budget.

func _initialize() -> void:
	var main: Node = (load("res://scenes/Main.tscn") as PackedScene).instantiate()
	root.add_child(main)
	for _i in range(180):
		await process_frame
		if main.get_node_or_null("Phase1Hud") != null:
			break
	var fails := 0
	var old: Node = main.get("hud")
	if old == null or old.visible or old.is_processing():
		print("OLD_HUD_FAIL visible=", old.visible if old else "missing", " processing=", old.is_processing() if old else "missing")
		fails += 1
	else:
		print("OLD_HUD_PAUSED")
	var hud: Phase1Hud = main.get_node("Phase1Hud")
	var p1: Node = root.get_node("Phase1")
	var vp := main.get_viewport()
	for bname in ["DockFeed", "DockClean", "DockPat", "DockTrain", "DockMap"]:
		fails += await _tap_button(vp, hud, p1, bname)
	hud.feed_row.visible = true
	hud.apply_layout()
	await process_frame
	fails += await _tap_button(vp, hud, p1, "FoodDew")
	hud.feed_row.visible = false
	hud.train_row.visible = true
	hud.apply_layout()
	await process_frame
	fails += await _tap_button(vp, hud, p1, "TrainPower")
	hud.train_row.visible = false
	hud.map_row.visible = true
	hud.apply_layout()
	await process_frame
	fails += await _tap_button(vp, hud, p1, "ZoneHome")
	var before: Vector3 = main.phase1_to
	var dock_btn := hud.dock.get_node("DockFeed") as Control
	var origin := dock_btn.get_global_rect().get_center()
	await _drag(vp, origin, Vector2(4, 0))
	if main.phase1_to.distance_to(before) > 0.01:
		print("MICRO_DRAG_PANNED")
		fails += 1
	else:
		print("MICRO_DRAG_HELD")
	var ground := Vector2(hud._safe().size.x * 0.5, hud._safe().position.y + 180.0)
	var before2: Vector3 = main.phase1_to
	await _drag(vp, ground, Vector2(24, 0))
	var moved: float = before2.x - main.phase1_to.x
	if moved < 4.0 or moved > 12.0:
		print("GROUND_DRAG_BAD delta=", moved)
		fails += 1
	else:
		print("GROUND_DRAG_ONCE delta=", moved)
	var dock_bottom := hud.dock.position.y + hud.dock.size.y
	var vp_h := hud.get_viewport().get_visible_rect().size.y
	var gap := vp_h - dock_bottom
	print("DOCK_SAFE_GAP=", gap)
	if gap < 18.0:
		print("DOCK_TOO_LOW")
		fails += 1
	if not vp.size_changed.is_connected(hud.apply_layout):
		print("SIZE_CHANGED_UNHOOKED")
		fails += 1
	else:
		print("SIZE_CHANGED_HOOKED")
	_budget(main, p1)
	var host := FileAccess.get_file_as_string("res://scripts/hd2d_exterior_host.gd")
	print("ANDROID_WINDOW_GUARD=", host.find("OS.has_feature(\"android\")") >= 0)
	print("COMPARE_VIEW_GUARD=", host.find("HD2D_COMPARE_GRAB") >= 0)
	print("MAX_FPS=", Engine.max_fps)
	print("R13_TOUCH_FAILS=", fails)
	quit(fails)


func _tap_button(vp: Viewport, hud: Phase1Hud, p1: Node, bname: String) -> int:
	var btn := hud.root.find_child(bname, true, false) as Button
	if btn == null or not btn.visible:
		print("TAP_MISSING ", bname)
		return 1
	var at := btn.get_global_rect().get_center()
	var before := int(p1.action_n)
	await _click(vp, at, true)
	await _click(vp, at, false)
	await process_frame
	await process_frame
	if int(p1.action_n) <= before:
		print("TAP_DEAD ", bname)
		return 1
	print("TAP_OK ", bname)
	return 0


func _click(vp: Viewport, at: Vector2, as_touch: bool) -> void:
	if as_touch:
		var down := InputEventScreenTouch.new()
		down.position = at
		down.pressed = true
		down.index = 0
		vp.push_input(down)
		await process_frame
		var up := InputEventScreenTouch.new()
		up.position = at
		up.pressed = false
		up.index = 0
		vp.push_input(up)
		await process_frame
	var press := InputEventMouseButton.new()
	press.button_index = MOUSE_BUTTON_LEFT
	press.pressed = true
	press.position = at
	press.global_position = at
	vp.push_input(press)
	await process_frame
	var release := InputEventMouseButton.new()
	release.button_index = MOUSE_BUTTON_LEFT
	release.pressed = false
	release.position = at
	release.global_position = at
	vp.push_input(release)
	await process_frame


func _drag(vp: Viewport, origin: Vector2, delta: Vector2) -> void:
	var down := InputEventScreenTouch.new()
	down.position = origin
	down.pressed = true
	vp.push_input(down)
	await process_frame
	var drag := InputEventScreenDrag.new()
	drag.position = origin + delta
	drag.relative = delta
	drag.index = 0
	vp.push_input(drag)
	await process_frame
	var up := InputEventScreenTouch.new()
	up.position = origin + delta
	up.pressed = false
	vp.push_input(up)
	await process_frame


func _budget(main: Node, p1: Node) -> void:
	var zones: Node = p1.get("world").get("zones")
	var tally := {"trees": 0, "bushes": 0, "nodes": 0, "meshes": 0, "shadows": 0, "omnis": 0, "paths": 0, "fences": 0, "stones": 0, "flowers": 0}
	_walk(zones, tally)
	print("BEFORE trees=18 bushes=9 paths=14 fences=21 stones=8 flowers=8")
	print("AFTER trees=", tally["trees"], " bushes=", tally["bushes"], " paths=", tally["paths"], " fences=", tally["fences"], " stones=", tally["stones"], " flowers=", tally["flowers"], " phase1_nodes=", tally["nodes"], " meshes=", tally["meshes"], " shadow_casters=", tally["shadows"], " zone_omnis=", tally["omnis"])
	var scene := {"omnis": 0}
	_count_omni(main, scene)
	print("SCENE_OMNIS=", scene["omnis"])


func _walk(node: Node, tally: Dictionary) -> void:
	tally["nodes"] = int(tally["nodes"]) + 1
	var n := str(node.name)
	if n.begins_with("ShopTree") or n.begins_with("PrairieTree"):
		tally["trees"] = int(tally["trees"]) + 1
	if n.find("Bush") >= 0:
		tally["bushes"] = int(tally["bushes"]) + 1
	if n.begins_with("FarmPath") or n.begins_with("ShopPath") or n.begins_with("PrairiePath"):
		tally["paths"] = int(tally["paths"]) + 1
	if n.find("Fence") >= 0:
		tally["fences"] = int(tally["fences"]) + 1
	if n.begins_with("Step_"):
		tally["stones"] = int(tally["stones"]) + 1
	if n.begins_with("Flower_"):
		tally["flowers"] = int(tally["flowers"]) + 1
	if node is MeshInstance3D:
		tally["meshes"] = int(tally["meshes"]) + 1
		if (node as MeshInstance3D).cast_shadow != GeometryInstance3D.SHADOW_CASTING_SETTING_OFF:
			tally["shadows"] = int(tally["shadows"]) + 1
	if node is OmniLight3D:
		tally["omnis"] = int(tally["omnis"]) + 1
	for child in node.get_children():
		_walk(child, tally)


func _count_omni(node: Node, tally: Dictionary) -> void:
	if node is OmniLight3D:
		tally["omnis"] = int(tally["omnis"]) + 1
	for child in node.get_children():
		_count_omni(child, tally)
