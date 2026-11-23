extends SceneTree
## Exit must put back the 675 garden, not the hidden H1 cottage, kid, or visitor.
## Headless node counts are not a GPU pass.

var _main: Node
var _ran := false
var _frames := 0
var _fails := 0


func _initialize() -> void:
	var udir := OS.get_user_data_dir()
	print("layers user_dir=", udir)
	if udir.find("vc27_play_36bfd") >= 0:
		print("FAIL player profile")
		quit(2)
		return
	_main = (load("res://scenes/Main.tscn") as PackedScene).instantiate()
	root.add_child(_main)
	process_frame.connect(_boot)


func _boot() -> void:
	if _ran:
		return
	_frames += 1
	if _frames > 240:
		print("FAIL pet did not appear")
		quit(1)
		return
	if _main.get("pet") == null:
		return
	_ran = true
	process_frame.disconnect(_boot)
	_run()


func _run() -> void:
	var base := _census("baseline")
	_expect_play(base, "baseline")
	_main.call("enter_house", true)
	_ok(bool(_main.get("in_interior")), "first enter")
	_expect_legacy_hidden("inside first")
	_main.call("exit_house", true)
	_ok(not bool(_main.get("in_interior")), "first exit")
	_expect_play(_census("exit1"), "exit1")
	_main.call("enter_house", true)
	_ok(bool(_main.get("in_interior")), "second enter")
	_expect_legacy_hidden("inside second")
	_main.call("exit_house", true)
	_ok(not bool(_main.get("in_interior")), "second exit")
	_expect_play(_census("exit2"), "exit2")
	print("PASS exit layers" if _fails == 0 else "FAIL exit layers")
	quit(0 if _fails == 0 else 1)


func _census(tag: String) -> Dictionary:
	var pet: Node3D = _main.get("pet")
	var kid: Node = _main.get("kid")
	var visitor: Node = _main.get("visitor")
	var coat: Sprite3D = pet.get_node_or_null("Hd2dCoat") if pet else null
	var sprite: Sprite3D = pet.get("sprite") if pet else null
	var legacy_houses := 0
	var exterior_houses := 0
	for node in _main.find_children("cottage", "", true, false):
		if not bool(node.get("visible")):
			continue
		if _under_exterior(node):
			exterior_houses += 1
		else:
			legacy_houses += 1
	var extra_walkers := 0
	for node in _main.find_children("*", "Walker", true, false):
		if node == pet or not bool(node.get("visible")):
			continue
		if _under_exterior(node):
			continue
		extra_walkers += 1
	var row := {
		"tag": tag,
		"coat": coat != null and coat.visible,
		"root_sprite": sprite != null and sprite.visible,
		"kid": kid != null and kid.visible,
		"visitor": visitor != null and visitor.visible,
		"legacy_houses": legacy_houses,
		"exterior_houses": exterior_houses,
		"extra_walkers": extra_walkers,
	}
	print("CENSUS ", row)
	return row


func _expect_play(row: Dictionary, tag: String) -> void:
	_ok(bool(row["coat"]), tag + " coat visible")
	_ok(not bool(row["root_sprite"]), tag + " root sprite hidden")
	_ok(not bool(row["kid"]), tag + " kid hidden")
	_ok(not bool(row["visitor"]), tag + " visitor hidden")
	_ok(int(row["legacy_houses"]) == 0, tag + " no legacy cottage")
	_ok(int(row["extra_walkers"]) == 0, tag + " no extra actors")
	_ok(int(row["exterior_houses"]) >= 1, tag + " approved cottage remains")


func _expect_legacy_hidden(tag: String) -> void:
	var row := _census(tag)
	_ok(not bool(row["kid"]), tag + " kid hidden")
	_ok(not bool(row["visitor"]), tag + " visitor hidden")
	_ok(int(row["legacy_houses"]) == 0, tag + " no legacy cottage")
	_ok(int(row["extra_walkers"]) == 0, tag + " no extra actors")


func _under_exterior(node: Node) -> bool:
	var cur := node
	while cur:
		if str(cur.name) == "Hd2dExterior":
			return true
		cur = cur.get_parent()
	return false


func _ok(cond: bool, name: String) -> void:
	if cond:
		print("PASS ", name)
	else:
		_fails += 1
		print("FAIL ", name)
