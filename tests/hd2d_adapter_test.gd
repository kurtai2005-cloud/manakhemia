extends SceneTree

const Door := preload("res://scripts/hd2d_door.gd")
## Isolated Main route for the 675 presentation adapter.
## Requires application/config/custom_user_dir_name to contain vc27_root_adapter.
## Software GL on this machine is not a phone or Mobile-renderer result.

var _fail := 0
var _main: Node
var _host: Node
var _phase := "boot"
var _frames := 0
var _min_z := 1000.0
var _moved := 0.0
var _last := Vector2.ZERO
var _stable := Vector2.ZERO
var _hold := 0
var _house: Dictionary = {}
var _version := -1
var _cams := 0
var _envs := 0
var _walkers := 0


func _initialize() -> void:
	var udir := OS.get_user_data_dir()
	print("adapter user_dir=", udir)
	if udir.find("vc27_root_adapter") < 0:
		print("FAIL user dir is not an isolated adapter profile")
		quit(2)
		return
	_geometry()
	_frozen()
	_main = load("res://scenes/Main.tscn").instantiate()
	if _main == null or not _main.has_method("enable_hd2d_presentation"):
		print("FAIL Main did not load. Global class cache may be missing.")
		quit(1)
		return
	root.add_child(_main)
	_phase = "wait_ready"
	process_frame.connect(_on_frame)


func _ok(cond: bool, name: String) -> void:
	if cond:
		print("PASS ", name)
	else:
		_fail += 1
		print("FAIL ", name)


func _geometry() -> void:
	var door := Door.threshold_world()
	_ok(is_equal_approx(door.x, 94.0) and is_equal_approx(door.y, 0.0) and is_equal_approx(door.z, -50.0), "threshold is (94, 0, -50)")
	_ok(Door.OUTWARD.is_equal_approx(Vector3(0, 0, 1)), "door faces +Z")
	_ok(is_equal_approx(Door.root_block_z(), -36.0), "root footprint blocks z <= -36 at the door")
	_ok(Door.root_blocked(94.0, -36.0), "z = -36 is blocked for radius 10")
	_ok(not Door.root_blocked(94.0, -35.99), "z just above -36 is clear")
	var anchor := Door.exterior_anchor()
	_ok(is_equal_approx(anchor.x, 94.0) and is_equal_approx(anchor.z, -29.5), "derived anchor is (94, 0, -29.5)")
	_ok(anchor.z - Door.TARGET_DESIRED > Door.root_block_z(), "a 6 wu early stop is still past the block")
	_ok(not Door.root_blocked(anchor.x, anchor.z), "anchor is outside the root footprint")
	_ok(not Door.pilot_blocked(Vector2(anchor.x, anchor.z), Door.pilot_props()), "anchor is outside the 675 block and prop circles")
	_ok(Door.pilot_blocked(Vector2(door.x, door.z), Door.pilot_props()), "threshold stays inside the 675 rect")
	_ok(Door.root_blocked(door.x, door.z), "threshold stays inside the root footprint")
	_ok(not Door.pilot_blocked(Vector2(94.0, -40.0), Door.pilot_props()), "675 rect far edge z=-40 is free")
	_ok(Door.root_blocked(94.0, -40.0), "z=-40 is still inside the root footprint")
	var src := FileAccess.get_file_as_string("res://godot_hd2d_v6/gameplay/m1_roam.gd")
	var needles := ["Vector2(-72.5, 22)", "Vector2(71, 24)", "Vector2(-39, 42)", "Vector2(35, 22)", "Vector2(-81, 70)", "Vector2(81, 54)", "Vector2(49, 22)", "Vector2(22, 18)", "Vector2(-24, 28)", "Vector2(48, 48)", "Vector2(18, 8)", "Vector2(-15, 35)", "Vector2(30, -20)"]
	var props_ok := needles.size() == Door.pilot_props().size()
	for needle in needles:
		if src.find(needle) < 0:
			props_ok = false
	_ok(props_ok, "prop circles match m1_roam._load_garden")
	var raw := FileAccess.get_file_as_string("res://godot_hd2d_v6/data/prop_bump.json")
	var parsed: Variant = JSON.parse_string(raw)
	var rect_ok := false
	if parsed is Dictionary:
		for row in (parsed as Dictionary).get("blocked_rects", []):
			if row is Dictionary and str(row.get("name", "")) == "cottage":
				rect_ok = is_equal_approx(float(row.get("x", 0)), Door.BLOCK_X) and is_equal_approx(float(row.get("z", 0)), Door.BLOCK_Z) and is_equal_approx(float(row.get("w", 0)), Door.BLOCK_W) and is_equal_approx(float(row.get("h", 0)), Door.BLOCK_H)
	_ok(rect_ok, "cottage block matches prop_bump.json")


func _frozen() -> void:
	var want := {
		"res://godot_hd2d_v6/scenes/capture.gd": "111dbfe7f2a0925f415545991449a8e5fd6d7c79be5a953def2fbda54788412f",
		"res://godot_hd2d_v6/scenes/capture.tscn": "ae8639e988df5c1c374b810f9e9d61204fd908c95cad2cffa812533251759c95",
		"res://godot_hd2d_v6/scenes/art_depth.gd": "fe53f5ad16619aea11f56343266a3ca179e40969a1c11c647fb301e2e4690d35",
		"res://godot_hd2d_v6/shaders/pet_shadow.gdshader": "e0bd9644fcdfe1b342a6177682d0bf243374d9563e7381b0546e3e94dcb4bc93",
		"res://godot_hd2d_v6/gameplay/m1_walk_clip.gd": "3f841bec501a1e229fe0f780a019e40547bcdb71c4f084f5f14aa79ffdf2c802",
	}
	for path in want.keys():
		_ok(_sha(path) == str(want[path]), "frozen bytes " + path.get_file())


func _sha(path: String) -> String:
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return ""
	var ctx := HashingContext.new()
	ctx.start(HashingContext.HASH_SHA256)
	ctx.update(f.get_buffer(f.get_length()))
	f.close()
	return ctx.finish().hex_encode()


func _boot() -> void:
	var method := RenderingServer.get_current_rendering_method()
	print("adapter renderer=", method, " project_mobile_not_claimed=true")
	_ok(method != "mobile", "this run is not the accepted mobile renderer")
	_host = _main.call("enable_hd2d_presentation")
	_cams = _count_type("Camera3D")
	_envs = _count_type("WorldEnvironment")
	_walkers = _count_type("Walker")
	_ok(_cams == 1, "one camera after the presentation attaches")
	_ok(_envs == 1, "one world environment")
	_ok(_walkers == _count_named_walkers(), "presentation adds no walker")
	_ok(_find_script("res://godot_hd2d_v6/scenes/capture.gd") == 0, "capture.tscn is not instanced")
	_ok(_find_script("res://godot_hd2d_v6/gameplay/m1_roam.gd") == 0, "pilot roam is not running")
	var placed: Dictionary = root.get_node("CollectionSystem").call("placed_items")
	_house = placed.duplicate(true)
	_version = int(root.get_node("Sim").get("state").get("version", -1))
	_ok(_version == 1, "save version stays 1")
	var pet: Node3D = _main.get("pet")
	_ok(pet.radius == 10.0 and is_equal_approx(pet.speed, 20.0), "pet radius and speed stay 10 and 20")
	_place(pet, Vector2(94.0, 2.0))
	pet.use_nav = false
	_ok(bool(_host.call("begin_approach_to", Vector3(94.0, 0.0, -50.0))) == false, "threshold is refused as a walk goal")
	_ok(is_equal_approx(pet.global_position.z, 2.0), "refused goal does not move the pet")
	_last = Vector2(pet.global_position.x, pet.global_position.z)
	_min_z = pet.global_position.z
	_phase = "foot"
	_frames = 0
	_ok(bool(_host.call("begin_approach")), "foot path accepts the derived anchor")


func _on_frame() -> void:
	if _phase == "done":
		return
	var pet: Node3D = _main.get("pet") if _main != null else null
	if _phase == "wait_ready":
		if pet == null:
			_frames += 1
			if _frames > 180:
				_ok(false, "Main did not spawn the pet")
				_finish()
			return
		_frames = 0
		_boot()
		return
	if pet == null:
		_ok(false, "pet missing before the route")
		_finish()
		return
	var z := pet.global_position.z
	var xz := Vector2(pet.global_position.x, pet.global_position.z)
	if _phase == "foot" or _phase == "nav" or _phase == "retarget" or _phase == "cancel" or _phase == "reanchor":
		_min_z = minf(_min_z, z)
		_moved += xz.distance_to(_last)
		_last = xz
		if Door.root_blocked(pet.global_position.x, z, pet.radius):
			_ok(false, "pet entered the root footprint during " + _phase)
			_finish()
			return
	_frames += 1
	if _phase == "foot":
		if bool(_host.get("arrived")):
			_ok(_min_z > -36.0, "foot approach stayed at z > -36")
			_ok(_moved > 20.0, "foot approach achieved real distance")
			var coat: Sprite3D = pet.get_node_or_null("Hd2dCoat")
			_ok(coat != null and coat.visible and coat.texture != null, "r4 coat is the visible pet")
			_ok(pet.sprite == null or not pet.sprite.visible, "the old walker sprite is hidden")
			_phase = "cancel"
			_place(pet, Vector2(94.0, 2.0))
			pet.use_nav = false
			_frames = 0
			_moved = 0.0
			_last = Vector2(94.0, 2.0)
			_host.call("begin_approach")
			return
		if _frames > 900:
			_ok(false, "foot approach did not arrive, z=%s" % z)
			_finish()
	elif _phase == "cancel":
		if _moved > 4.0 and _frames > 5:
			_host.call("cancel_approach")
			_stable = Vector2(pet.global_position.x, pet.global_position.z)
			_hold = 0
			_phase = "hold"
			_frames = 0
		elif _frames > 900:
			_ok(false, "cancel setup did not move")
			_finish()
	elif _phase == "hold":
		_hold += 1
		var drift := Vector2(pet.global_position.x, pet.global_position.z).distance_to(_stable)
		if drift > 0.2:
			_ok(false, "cancel did not hold the pet")
			_finish()
			return
		if _hold >= 8:
			_ok(true, "cancel holds the pet outside the door")
			_phase = "retarget"
			_frames = 0
			_moved = 0.0
			_min_z = pet.global_position.z
			_last = Vector2(pet.global_position.x, pet.global_position.z)
			pet.use_nav = false
			_ok(bool(_host.call("begin_approach_to", Vector3(110.0, 0.0, 10.0))), "retarget accepts a clear point")
	elif _phase == "retarget":
		if _moved > 3.0:
			_frames = 0
			_moved = 0.0
			_min_z = 1000.0
			_last = Vector2(pet.global_position.x, pet.global_position.z)
			_phase = "reanchor"
			_ok(bool(_host.call("begin_approach")), "second approach accepts the anchor")
		elif _frames > 900:
			_ok(false, "retarget did not move")
			_finish()
	elif _phase == "reanchor":
		if bool(_host.get("arrived")):
			_ok(_min_z > -36.0, "retarget approach stayed clear")
			_phase = "door"
			_frames = 0
		elif _frames > 900:
			_ok(false, "retarget did not reach the anchor")
			_finish()
	elif _phase == "nav":
		if bool(_host.get("arrived")):
			_ok(_min_z > -36.0, "nav approach stayed at z > -36")
			_ok(pet.global_position.z > -36.0, "nav arrival is outside the footprint")
			print("adapter nav_arrived=true z=", pet.global_position.z)
			_finish()
		elif _frames > 900:
			_ok(pet.global_position.z > -36.0, "nav did not enter the footprint when it did not arrive")
			print("adapter nav_arrived=false z=", pet.global_position.z, " moved=", _moved)
			_finish()
	elif _phase == "door":
		var before := pet.global_position
		_ok(bool(_host.call("commit_enter")), "enter runs only from a clear exterior stand")
		_ok(bool(_main.get("in_interior")), "interior flag follows the existing enter")
		_ok(bool(_host.call("commit_exit")), "exit returns through the existing exit")
		_ok(not bool(_main.get("in_interior")), "exit clears the interior flag")
		_ok(pet.global_position.distance_to(before) < 1.0 or pet.global_position.z > -36.0, "exit stand is the exterior approach, not the threshold")
		_ok(pet.global_position.z > -36.0, "exit position stays outside the footprint")
		var back := Vector2(pet.global_position.x, pet.global_position.z)
		var goal := Vector2(Door.exterior_anchor().x, Door.exterior_anchor().z)
		_ok(back.distance_to(goal) <= Door.TARGET_DESIRED and pet.global_position.z > -36.0, "exit stand is within 6 wu of the engineering anchor and past z=-36")
		var placed: Dictionary = root.get_node("CollectionSystem").call("placed_items")
		_ok(placed == _house, "furniture placement is unchanged")
		_ok(int(root.get_node("Sim").get("state").get("version", -1)) == 1, "save version is still 1")
		_ok(_count_type("Camera3D") == _cams, "camera count stays one")
		_ok(_count_type("WorldEnvironment") == _envs, "environment count stays one")
		_ok(_count_type("Walker") == _walkers, "walker count is unchanged")
		_phase = "nav"
		_place(pet, Vector2(94.0, 2.0))
		pet.use_nav = true
		_frames = 0
		_moved = 0.0
		_min_z = 2.0
		_last = Vector2(94.0, 2.0)
		_ok(bool(_host.call("begin_approach")), "nav path accepts the anchor")


func _place(pet: Node3D, xz: Vector2) -> void:
	pet.global_position = Vector3(xz.x, 0.0, xz.y)
	pet.pause_t = 0.0
	if pet.agent:
		pet.agent.target_position = pet.global_position


func _finish() -> void:
	_phase = "done"
	if _fail == 0:
		print("PASS hd2d_adapter")
		quit(0)
	else:
		print("FAIL hd2d_adapter ", _fail)
		quit(1)


func _count_type(kind: String) -> int:
	_tally = 0
	_walk(root, kind, 0)
	return _tally


var _tally := 0


func _walk(n: Node, kind: String, _acc: int) -> void:
	var script_path := ""
	if n.get_script():
		script_path = str(n.get_script().resource_path)
	if n.get_class() == kind or (kind == "Walker" and script_path.ends_with("Walker.gd")):
		_tally += 1
	for c in n.get_children():
		_walk(c, kind, 0)


func _count_named_walkers() -> int:
	_tally = 0
	_walk(root, "Walker", 0)
	return _tally


func _find_script(path: String) -> int:
	return _scan_script(root, path)


func _scan_script(n: Node, path: String) -> int:
	var hit := 0
	var s = n.get_script()
	if s and str(s.resource_path) == path:
		hit += 1
	for c in n.get_children():
		hit += _scan_script(c, path)
	return hit
