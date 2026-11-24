extends SceneTree
## Project the live camera and name meshes that cover zone marks.

func _initialize() -> void:
	var main: Node = (load("res://scenes/Main.tscn") as PackedScene).instantiate()
	root.add_child(main)
	for _i in range(200):
		await process_frame
		if main.get_node_or_null("Phase1Hud") != null:
			break
	var p1: Node = root.get_node("Phase1")
	if p1 and p1.hud and p1.hud.modal:
		p1.close_modal()
	var exterior: Node = main.get("_hd2d_exterior")
	var views := {
		"home": Vector3(12, 58, -26),
		"farm": Vector3(-410, 58, 20),
		"workshop": Vector3(410, 58, 20),
		"prairie": Vector3(240, 58, -680),
	}
	var marks := {
		"home": [Vector3(94, 20, -40), Vector3(94, 8, -20), Vector3(20, 16, 30)],
		"farm": [Vector3(-395, 12, 25), Vector3(-320, 16, 42), Vector3(-410, 8, 90)],
		"workshop": [Vector3(358, 14, -18), Vector3(326, 16, 48), Vector3(410, 8, 80)],
		"prairie": [Vector3(240, 8, -500), Vector3(240, 8, -680)],
	}
	for key in ["home", "farm", "workshop", "prairie"]:
		main.phase1_glide_to(views[key])
		main.phase1_t = 1.0
		main.phase1_to = views[key]
		main._place_cam(0.0)
		await process_frame
		await process_frame
		var cam: Camera3D = main.get("cam")
		print("VIEW ", key, " cam=", cam.global_position)
		for spot in marks[key]:
			var sp := cam.unproject_position(spot)
			print(" MARK ", spot, " screen=", sp)
			_occluders(exterior, cam, spot, sp)
		if key == "farm" or key == "workshop" or key == "home":
			_dump_near(exterior, cam, key)
	print("BIG")
	for node in exterior.find_children("*", "GeometryInstance3D", true, false):
		var gi := node as GeometryInstance3D
		if not (node as Node3D).visible:
			continue
		var sz := gi.get_aabb().size
		if sz.y < 40.0:
			continue
		var pos: Vector3 = (node as Node3D).global_position
		print(" B ", node.name, " pos=", pos, " size=", sz)
	print("TREES")
	for node in exterior.find_children("*", "Node3D", true, false):
		var n := str(node.name).to_lower()
		if n.find("tree") < 0 and n.find("trunk") < 0:
			continue
		print(" T ", node.name, " ", (node as Node3D).global_position, " vis=", (node as Node3D).visible)
	print("SIGHT_DONE")
	quit(0)


func _dump_near(exterior: Node, cam: Camera3D, key: String) -> void:
	var rows: Array = []
	for node in exterior.find_children("*", "Node3D", true, false):
		var n := str(node.name)
		var path := str(node.get_path())
		var treeish := n.find("tree") >= 0 or n.find("Tree") >= 0 or n.find("bush") >= 0 or n.find("Bush") >= 0 or path.find("FarForest") >= 0 or path.find("OuterRing") >= 0 or path.find("Canopies") >= 0
		if not treeish or not node.visible:
			continue
		var pos: Vector3 = node.global_position
		if pos == Vector3.ZERO and node.get_child_count() == 0:
			continue
		if cam.is_position_behind(pos):
			continue
		var sc := cam.unproject_position(pos + Vector3(0, 20, 0))
		var depth := cam.global_position.distance_to(pos)
		if depth > 420.0 or sc.x < -40.0 or sc.x > 580.0 or sc.y < -40.0 or sc.y > 1200.0:
			continue
		rows.append([depth, "%s d=%.0f scr=(%.0f,%.0f) pos=%s" % [n, depth, sc.x, sc.y, pos]])
	rows.sort_custom(func(a, b): return float(a[0]) < float(b[0]))
	print("NEAR ", key)
	for row in rows.slice(0, 18):
		print("  ", row[1])


func _occluders(exterior: Node, cam: Camera3D, spot: Vector3, screen: Vector2) -> void:
	if exterior == null:
		return
	var hits: Array = []
	for node in exterior.find_children("*", "GeometryInstance3D", true, false):
		if not (node is Node3D) or not (node as Node3D).visible:
			continue
		var n := str(node.name)
		var path := str(node.get_path())
		var treeish := n.find("tree") >= 0 or n.find("Tree") >= 0 or n.find("bush") >= 0 or n.find("Bush") >= 0 or n.find("pot") >= 0 or n.find("Pot") >= 0 or n.find("crate") >= 0 or n.find("Crate") >= 0 or path.find("OuterRing") >= 0 or path.find("FarForest") >= 0 or path.find("Canopies") >= 0
		if not treeish:
			continue
		var gi := node as GeometryInstance3D
		var aabb := gi.get_aabb()
		var center: Vector3 = (node as Node3D).global_transform * aabb.get_center()
		if cam.is_position_behind(center):
			continue
		var sc := cam.unproject_position(center)
		if sc.distance_to(screen) > 90.0:
			continue
		var depth := cam.global_position.distance_to(center)
		var mark_d := cam.global_position.distance_to(spot)
		if depth > mark_d + 30.0:
			continue
		hits.append("%s d=%.0f screen=%s pos=%s" % [path, depth, sc, (node as Node3D).global_position])
	hits.sort()
	for line in hits.slice(0, 8):
		print("  OCC ", line)
