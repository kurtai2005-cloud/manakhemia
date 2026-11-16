extends RefCounted
## Two-process save/restore and real button coverage.
## Seed may write the isolated profile. Verify only reads, then compares.

static var _t := 0.0
static var _n := 0
static var _hold_until := -1.0
static var _pet0 := Vector3.ZERO
static var _needs0 := {}
static var _poops_before_one := -1
static var _hunger_before_feed := -1.0
static var _dead := false


static func seed_fixture() -> void:
	# Only the seed process may set a starting fixture.
	_require_profile_dir()
	print("profile seed user_data_dir=", OS.get_user_data_dir())
	if _sim() == null:
		_fail("seed missing Sim")
		return
	if str(_state().get("stage", "egg")) == "egg" and _sim().has_method("force_stage"):
		_sim().call("force_stage", "sprout")
	while int(_state().get("poops", 0)) < 2 and _sim().has_method("add_poop"):
		_sim().call("add_poop")
	var needs: Dictionary = _state().get("needs", {})
	# Below the existing refuse line so the feed button is allowed. Not a new rule.
	needs["hunger"] = float(_sim().get("FEED_REFUSE_AT")) - float(_sim().get("FEED_MEAL"))
	_state()["needs"] = needs
	print("profile seed fixture hunger=", needs["hunger"], " poops=", int(_state().get("poops", 0)), " stage=", _state().get("stage", ""))


static func tick_seed(care: Node, dt: float) -> void:
	if _dead:
		return
	_t += dt
	if _hold_until >= 0.0 and _t >= _hold_until:
		care.call("_pointer", _ground(care), false)
		_hold_until = -1.0
		print("profile release longpress t=", snapped(_t, 0.01), " poops=", _poops())
	if _n == 0 and _t >= 0.45:
		_remember(care)
		var water: Vector2 = care.call("_button_center", 1)
		care.call("_pointer", water, true)
		care.call("_pointer", water, false)
		print("profile water press/release at ", water, " hunger=", _hunger())
		_n = 1
	elif _n == 1 and _t >= 0.9:
		_assert_water(care)
		if _dead:
			return
		_poops_before_one = _poops()
		if _poops_before_one < 2:
			_fail("need at least 2 poops before clean_one, have %s" % _poops_before_one)
			return
		var poop_at: Vector2 = care.call("_button_center", 2)
		care.call("_pointer", poop_at, true)
		care.call("_pointer", poop_at, false)
		print("profile clean_one press at ", poop_at, " poops_before=", _poops_before_one)
		_n = 2
	elif _n == 2 and _t >= 1.35:
		var left := _poops()
		if left != _poops_before_one - 1:
			_fail("clean_one expected %s poops, got %s" % [_poops_before_one - 1, left])
			return
		if left <= 0:
			_fail("clean_one removed every poop; cannot tell it from clean_all")
			return
		print("PASS clean_one left ", left, " of ", _poops_before_one)
		care.call("_pointer", _ground(care), true)
		_hold_until = _t + 0.7
		print("profile longpress down")
		_n = 3
	elif _n == 3 and _hold_until < 0.0 and _t >= 2.3:
		if _poops() != 0:
			_fail("longpress expected 0 poops, got %s" % _poops())
			return
		print("PASS longpress cleared remainder")
		_hunger_before_feed = _hunger()
		var feed_at: Vector2 = care.call("_button_center", 0)
		care.call("_pointer", feed_at, true)
		care.call("_pointer", feed_at, false)
		print("profile feed press hunger_before=", _hunger_before_feed)
		_n = 4
	elif _n == 4 and _t >= 2.7:
		var got := _hunger()
		var meal := float(_sim().get("FEED_MEAL"))
		if absf((got - _hunger_before_feed) - meal) > 0.2:
			_fail("feed button hunger delta %s, meal is %s" % [got - _hunger_before_feed, meal])
			return
		print("PASS feed hunger ", _hunger_before_feed, " -> ", got)
		var pat_at: Vector2 = care.call("_button_center", 3)
		care.call("_pointer", pat_at, true)
		care.call("_pointer", pat_at, false)
		print("profile pat press")
		_n = 5
	elif _n == 5 and _t >= 3.05:
		_write_expect()
		print("PASS seed saved")
		care.get_tree().quit(0)


static func verify_and_quit(care: Node) -> void:
	_require_profile_dir()
	print("profile verify user_data_dir=", OS.get_user_data_dir())
	var disk := _read_json(_save_path())
	if disk.is_empty():
		_fail("verify found no save at %s" % _save_path())
	var now := _now()
	var predicted := predict_reload(disk, now)
	var live := _relevant(_state())
	var want := _relevant(predicted)
	var gap := _gap_sec(disk, now)
	print("profile gap_sec=", snapped(gap, 0.001), " offline=", gap >= 2.0)
	print("profile saved ", _fmt(_relevant(disk)))
	print("profile predicted ", _fmt(want))
	print("profile restored ", _fmt(live))
	if str(live["stage"]) != str(want["stage"]) or int(live["poops"]) != int(want["poops"]):
		_fail("restore stage/poops live=%s/%s predicted=%s/%s" % [live["stage"], live["poops"], want["stage"], want["poops"]])
	for key in ["hunger", "mood", "clean", "energy"]:
		if absf(float(live[key]) - float(want[key])) > 0.05:
			_fail("restore %s live=%s predicted=%s (drift already in the prediction)" % [key, live[key], want[key]])
	print("PASS restore")
	care.get_tree().quit(0)


static func predict_reload(saved: Dictionary, now_ms: int) -> Dictionary:
	# Same 2s stall as TimeService.catch_up. Longer gaps use Sim.apply_offline.
	var out := saved.duplicate(true)
	var last := int(out.get("last_seen", now_ms))
	if now_ms < last:
		return out
	if float(now_ms - last) / 1000.0 < 2.0:
		return out
	var sim := _sim()
	if sim:
		sim.call("apply_offline", out, now_ms)
	return out


static func _assert_water(care: Node) -> void:
	var pet: Node3D = care.host.get("_pet") as Node3D
	var pos := pet.global_position if pet else Vector3.ZERO
	var moved := pos.distance_to(_pet0)
	var hunger_now := _hunger()
	var hunger_was := float((_needs0 as Dictionary).get("hunger", hunger_now))
	var walk: Variant = care.host.get("_walk_target")
	print("profile water result moved=", snapped(moved, 0.001), " hunger=", hunger_was, "->", hunger_now, " walk=", walk)
	if moved > 1.0:
		_fail("water press moved the pet by %s" % moved)
	if walk != null:
		_fail("water press started a ground walk")
	if absf(hunger_now - hunger_was) > 0.05:
		_fail("water press changed hunger by %s" % (hunger_now - hunger_was))
	for key in ["mood", "clean", "energy"]:
		var was := float((_needs0 as Dictionary).get(key, 0))
		var now := float((_state().get("needs", {}) as Dictionary).get(key, 0))
		if absf(now - was) > 0.05:
			_fail("water press changed %s by %s" % [key, now - was])
	print("PASS water consumed input")


static func _remember(care: Node) -> void:
	var pet: Node3D = care.host.get("_pet") as Node3D
	_pet0 = pet.global_position if pet else Vector3.ZERO
	_needs0 = (_state().get("needs", {}) as Dictionary).duplicate()


static func _write_expect() -> void:
	_state()["last_seen"] = _now()
	_sim().call("_save_now", true)
	var snap := _relevant(_state())
	snap["last_seen"] = int(_state().get("last_seen", 0))
	snap["last_save_time"] = int(_state().get("last_save_time", 0))
	var path := OS.get_environment("HD2D_EXPECT_FILE")
	if path == "":
		path = OS.get_user_data_dir().path_join("expect_restore.json")
	var f := FileAccess.open(path, FileAccess.WRITE)
	if f == null:
		_fail("cannot write expect file %s" % path)
	f.store_string(JSON.stringify(snap))
	f.close()
	print("profile expect ", path, " ", _fmt(snap))
	print("profile save ", _save_path())


static func _save_path() -> String:
	return OS.get_user_data_dir().path_join("save_v1.json")


static func _read_json(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {}
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if typeof(parsed) != TYPE_DICTIONARY:
		return {}
	return parsed


static func _relevant(s: Dictionary) -> Dictionary:
	var n: Dictionary = s.get("needs", {})
	return {
		"hunger": float(n.get("hunger", s.get("hunger", 0))),
		"mood": float(n.get("mood", s.get("mood", 0))),
		"clean": float(n.get("clean", s.get("clean", 0))),
		"energy": float(n.get("energy", s.get("energy", 0))),
		"poops": int(s.get("poops", 0)),
		"stage": str(s.get("stage", "")),
	}


static func _gap_sec(saved: Dictionary, now_ms: int) -> float:
	return float(now_ms - int(saved.get("last_seen", now_ms))) / 1000.0


static func _fmt(s: Dictionary) -> String:
	return "stage=%s poops=%s hunger=%s mood=%s clean=%s energy=%s" % [
		s.get("stage", ""), s.get("poops", ""), s.get("hunger", ""),
		s.get("mood", ""), s.get("clean", ""), s.get("energy", ""),
	]


static func _sim() -> Node:
	var tree := Engine.get_main_loop()
	if tree == null:
		return null
	return tree.root.get_node_or_null("Sim")


static func _state() -> Dictionary:
	var sim := _sim()
	if sim == null:
		return {}
	return sim.get("state")


static func _now() -> int:
	var tree := Engine.get_main_loop()
	if tree == null:
		return 0
	var clock: Node = tree.root.get_node_or_null("TimeService")
	if clock == null:
		return 0
	return int(clock.call("now_ms"))


static func _hunger() -> float:
	return float((_state().get("needs", {}) as Dictionary).get("hunger", -1))


static func _poops() -> int:
	return int(_state().get("poops", -1))


static func _ground(care: Node) -> Vector2:
	return care.call("_ground_point")


static func _require_profile_dir() -> void:
	var want := OS.get_environment("HD2D_PROFILE_NAME")
	var got := OS.get_user_data_dir()
	if want == "":
		_fail("HD2D_PROFILE_NAME is empty")
		return
	if got.find(want) < 0:
		_fail("user dir %s is not isolated profile %s" % [got, want])


static func _fail(msg: String) -> void:
	print("FAIL ", msg)
	_dead = true
	var tree := Engine.get_main_loop()
	if tree:
		tree.quit(1)
