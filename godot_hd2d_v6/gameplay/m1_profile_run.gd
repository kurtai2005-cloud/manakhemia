extends RefCounted
## Two-process save/restore and the optional visual trace.
## Seed and visual may write an isolated profile. Verify only reads.

const Layout := preload("res://gameplay/m1_ui_layout.gd")

# Deterministic visual-trace seed. Not a care or economy value.
# Live play still uses Walker.randomize().
const TRACE_ROAM_SEED := 2

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


static func visual_fixture(care: Node) -> void:
	# Separate from the restore seed. Hunger is the existing bubble line:
	# want_eat = 100 - hunger, shown when want > threshold - 0.01.
	_require_profile_dir()
	print("TRACE header wake=pointer_down_calls_note_input_only_when_appreciate_is_false")
	print("TRACE header key_n=capture_unhandled_input_returns_before_care_and_does_not_toggle_appreciate")
	print("TRACE header walk=autonomous_then_tap_directed")
	print("TRACE header autonomous_walk=walker_speed_and_idle_pause petbrain_nearby_pick")
	print("TRACE header art=pet_tuanrong_radiant_idle_01 only no_walk_cycle movement_is_billboard_position")
	print("TRACE header day_night=key_n_only_after_the_appreciate_hold_and_it_does_not_wake_the_ui")
	print("TRACE schedule autonomous_motion>=3s_before_any_ground_tap; then empty_tap_leaves_follow; tap_walk_a; tap_walk_b; feed; pat; clean_one; longpress; quiet+1.5 ui_shown; quiet+3.5 ui_hidden; quiet+3.9 pointer_wake; quiet+4.3 wake_restored; quiet+4.6 appreciate; appreciate+2.2 hold_no_input mode_low; appreciate+2.6 key_n; appreciate+3.1 mode_night appreciate_still_on")
	var roam = care.host.get("_roam") if care and care.host else null
	if roam and roam.has_method("seed"):
		# Trace seed only. Live play still randomizes like Walker.
		roam.seed(TRACE_ROAM_SEED)
	print("profile visual user_data_dir=", OS.get_user_data_dir())
	if _sim() == null:
		_fail("visual missing Sim")
		return
	if str(_state().get("stage", "egg")) == "egg" and _sim().has_method("force_stage"):
		_sim().call("force_stage", "sprout")
	while int(_state().get("poops", 0)) < 2 and _sim().has_method("add_poop"):
		_sim().call("add_poop")
	var needs: Dictionary = _state().get("needs", {})
	needs["hunger"] = Layout.hunger_for_need_bubble(_threshold())
	_state()["needs"] = needs
	print("profile visual fixture hunger=", needs["hunger"], " threshold=", _threshold(), " poops=", _poops())


static func tick_visual(care: Node, dt: float) -> void:
	if _dead:
		return
	_t += dt
	var pos := _pet_pos(care)
	var step_wu := 0.0
	if _have_prev:
		step_wu = pos.distance_to(_walk_prev)
		_walked += step_wu
	_walk_prev = pos
	_have_prev = true
	if care.host.get("_walk_target") != null:
		_tap_walk_sec += dt
		_tap_wu += step_wu
	if _hold_until >= 0.0 and _t >= _hold_until:
		_trace_pointer(care, _ground(care), false, "longpress_up")
		_hold_until = -1.0
	_sample_walk(care)
	var mark := _vn
	if mark == 0 and _t >= 0.6 and not _bubble_seen:
		_trace_state(care, "bubble_before_feed", true, "shown", false, "low")
		if not _bubble_on(care):
			_fail("need bubble was not visible before feed")
			return
		if _walk_cause(care) != "autonomous":
			_fail("opening bubble sample was not autonomous, cause=%s" % _walk_cause(care))
			return
		_bubble_seen = true
	if mark == 0 and _auto_ready(care):
		var roam = care.host.get("_roam")
		_auto_at = _t
		_auto_sec = float(roam.walk_sec)
		_auto_wu = _walked
		_opening_logged = float(care.host.call("_pet_height_frac"))
		_trace_state(care, "autonomous_open", true, "fading", false, "low")
		print("TRACE t=", snapped(_t, 0.01), " kind=autonomous_check walk_sec=", snapped(_auto_sec, 0.01), " path_wu=", snapped(_auto_wu, 0.1), " cause=", _walk_cause(care), " motion=", str(roam.motion), " taps=", snapped(_tap_walk_sec, 0.01), " opening_frac=", snapped(_opening_logged, 0.001), " follow_min=", snapped(float(care.host.call("_follow_pet_min")), 0.001))
		if _auto_sec < 3.0 or _tap_walk_sec > 0.0 or _last_input >= 0.0:
			_fail("autonomous opening was not 3s of motion without taps")
			return
		_vn = 1
	elif mark == 0 and _t >= 8.0:
		_fail("autonomous motion did not reach 3s before t=8, walk_sec=%s" % _roam_walk_sec(care))
		return
	elif mark == 1 and _follow_step == 0 and _t >= _auto_at + 0.3:
		var pet_px: Vector2 = care.call("_pet_point")
		_trace_pointer(care, pet_px, true, "follow_pet_down")
		_trace_pointer(care, pet_px, false, "follow_pet_up")
		_follow_step = 1
	elif mark == 1 and _follow_step == 1:
		var roam_hold = care.host.get("_roam")
		if roam_hold:
			roam_hold.set_care_hold(true)
		var st: Dictionary = care.host.call("follow_zoom_state")
		var frac := float(st.get("frac", 0.0))
		var need := float(st.get("need", 0.0))
		var close := bool(care.call("follow_close"))
		if not _follow_transient_logged:
			_follow_transient_logged = true
			print("TRACE t=", snapped(_t, 0.01), " kind=follow_zoom phase=transient frac=", snapped(frac, 0.001), " need=", snapped(need, 0.001), " err=", snapped(float(st.get("err", -1)), 0.1), " settled=false")
		if bool(st.get("settled", false)):
			if roam_hold:
				roam_hold.set_care_hold(false)
			print("TRACE t=", snapped(_t, 0.01), " kind=follow_zoom phase=settled frac=", frac, " need=", need, " close=", close, " opening_frac=", _opening_logged, " err=", snapped(float(st.get("err", -1)), 0.1))
			if not close:
				_fail("pet tap did not enter follow")
				return
			if need > 0.0 and frac < need:
				_fail("settled follow box %s is under %s" % [frac, need])
				return
			_follow_step = 2
		elif _t >= _auto_at + 8.0:
			if roam_hold:
				roam_hold.set_care_hold(false)
			print("TRACE t=", snapped(_t, 0.01), " kind=follow_zoom phase=unsettled frac=", frac, " need=", need, " err=", snapped(float(st.get("err", -1)), 0.1))
			_fail("follow did not settle at or above %s, last frac %s" % [need, frac])
			return
	elif mark == 1 and _follow_step == 2 and _t >= _auto_at + 2.8:
		var away := Vector2(80, 200)
		_trace_pointer(care, away, true, "leave_follow_down")
		_trace_pointer(care, away, false, "leave_follow_up")
		_vn = 2
	elif mark == 2 and _t >= _auto_at + 3.6:
		_walk_from = pos
		var here := Vector2(pos.x, pos.z)
		var goal: Vector2 = care.host.get("_roam").far_free(here)
		_trace_pointer(care, _screen_of(care, Vector3(goal.x, 0, goal.y)), true, "walk_a_down")
		_trace_pointer(care, _screen_of(care, Vector3(goal.x, 0, goal.y)), false, "walk_a_up")
		_leg_at = _t
		_vn = 3
	elif mark == 3 and _t >= _leg_at + 1.6:
		var here_b := Vector2(pos.x, pos.z)
		var goal_b: Vector2 = care.host.get("_roam").far_free(here_b)
		_trace_pointer(care, _screen_of(care, Vector3(goal_b.x, 0, goal_b.y)), true, "walk_b_down")
		_trace_pointer(care, _screen_of(care, Vector3(goal_b.x, 0, goal_b.y)), false, "walk_b_up")
		_vn = 4
	elif mark == 4 and _t >= _leg_at + 4.2:
		var roam_now = care.host.get("_roam")
		var auto_sec := _auto_sec
		print("TRACE t=", snapped(_t, 0.01), " kind=walk_check path_wu=", snapped(_walked, 0.1), " auto_wu=", snapped(_auto_wu, 0.1), " auto_sec=", snapped(auto_sec, 0.01), " tap_directed_sec=", snapped(_tap_walk_sec, 0.01), " tap_wu=", snapped(_tap_wu, 0.1), " straight_from_start=", snapped(pos.distance_to(_walk_from), 0.1), " cause=", _walk_cause(care), " motion=", str(roam_now.motion) if roam_now else "none")
		if auto_sec < 3.0:
			_fail("autonomous opening was short, sec=%s" % auto_sec)
			return
		if _tap_walk_sec < 1.5 or _tap_wu < 60.0:
			_fail("tap-directed walk was short, sec=%s wu=%s" % [_tap_walk_sec, _tap_wu])
			return
		if float(care.get("fade").alpha) < 0.95:
			_fail("UI faded before feed, alpha=%s" % care.get("fade").alpha)
			return
		if not _bubble_on(care):
			_fail("bubble disappeared before the feed tap")
			return
		if not _bubble_in_view(care):
			_fail("need bubble was outside the viewport before feed")
			return
		_hunger_before_feed = _hunger()
		_trace_pointer(care, care.call("_button_center", 0), true, "feed_down")
		_trace_pointer(care, care.call("_button_center", 0), false, "feed_up")
		_vn = 5
	elif mark == 5 and _t >= _leg_at + 4.7:
		var got := _hunger()
		var meal := float(_sim().get("FEED_MEAL"))
		if absf((got - _hunger_before_feed) - meal) > 0.25:
			_fail("visual feed delta %s meal %s" % [got - _hunger_before_feed, meal])
			return
		if _bubble_on(care):
			_fail("bubble still visible after feed")
			return
		_trace_state(care, "after_feed", false, "shown", false, "low")
		_trace_pointer(care, care.call("_button_center", 3), true, "pat_down")
		_trace_pointer(care, care.call("_button_center", 3), false, "pat_up")
		_vn = 6
	elif mark == 6 and _t >= _leg_at + 5.1:
		_poops_before_one = _poops()
		_trace_pointer(care, care.call("_button_center", 2), true, "clean_one_down")
		_trace_pointer(care, care.call("_button_center", 2), false, "clean_one_up")
		_vn = 7
	elif mark == 7 and _t >= _leg_at + 5.5:
		if _poops() != _poops_before_one - 1 or _poops() <= 0:
			_fail("visual clean_one poops %s from %s" % [_poops(), _poops_before_one])
			return
		_trace_pointer(care, _ground(care), true, "longpress_down")
		_hold_until = _t + 0.7
		_vn = 8
	elif mark == 8 and _hold_until < 0.0 and _t >= _leg_at + 6.3:
		if _poops() != 0:
			_fail("visual longpress poops %s" % _poops())
			return
		_quiet_at = _t
		print("TRACE t=", snapped(_t, 0.01), " kind=quiet_start last_input=", snapped(_last_input, 0.01), " expected_ui=shown_until_idle_reaches_fade_sec no_input_from_here")
		_vn = 9
	elif mark == 9 and _t >= _quiet_at + 1.5:
		_trace_state(care, "fade_not_yet", false, "shown", false, "low")
		if float(care.get("fade").alpha) < 0.95:
			_fail("UI faded before the 3s idle, alpha=%s" % care.get("fade").alpha)
			return
		_vn = 10
	elif mark == 10 and _t >= _quiet_at + 3.5:
		_trace_state(care, "fade_hidden", false, "hidden", false, "low")
		if _t - _last_input < 3.0:
			_fail("fade window had input at t=%s" % _last_input)
			return
		if float(care.get("fade").alpha) > 0.05:
			_fail("fade did not hide UI after 3.5s idle, alpha=%s" % care.get("fade").alpha)
			return
		_vn = 11
	elif mark == 11 and _t >= _quiet_at + 3.9:
		var admire: Vector2 = _admire(care)
		_trace_pointer(care, admire, true, "wake_down_any_pointer_restores_faded_ui")
		_trace_pointer(care, admire, false, "wake_up_button_was_ignore_so_appreciate_stays_off")
		_vn = 12
	elif mark == 12 and _t >= _quiet_at + 4.3:
		_trace_state(care, "wake_restored", false, "shown", false, "low")
		if bool(care.get("fade").appreciate):
			_fail("wake tap toggled appreciate; it should only restore the fade")
			return
		if float(care.get("fade").alpha) < 0.95:
			_fail("wake pointer did not restore the UI, alpha=%s" % care.get("fade").alpha)
			return
		_vn = 13
	elif mark == 13 and _t >= _quiet_at + 4.6:
		var admire2: Vector2 = _admire(care)
		_trace_pointer(care, admire2, true, "appreciate_down")
		_trace_pointer(care, admire2, false, "appreciate_up")
		_appreciate_at = _t
		_vn = 14
	elif mark == 14 and _t >= _appreciate_at + 2.2:
		if not bool(care.get("fade").appreciate):
			_fail("appreciate did not stay on for 2s")
			return
		if _t - _last_input < 2.0:
			_fail("input during appreciate window at t=%s" % _last_input)
			return
		_trace_state(care, "appreciate_hold", false, "hidden", true, "low")
		_vn = 15
	elif mark == 15 and _t >= _appreciate_at + 2.6:
		_trace_key_n(care)
		_vn = 16
	elif mark == 16 and _t >= _appreciate_at + 3.1:
		var mode := str(care.host.get("_mode"))
		if mode != "night":
			_fail("night key did not switch mode, mode=%s" % mode)
			return
		if not bool(care.get("fade").appreciate):
			_fail("night key cleared appreciate; key input must not wake it")
			return
		if float(care.get("fade").alpha) > 0.05:
			_fail("night key woke the UI, alpha=%s" % care.get("fade").alpha)
			return
		_trace_state(care, "night_after_appreciate", false, "hidden", true, "night")
		print("PASS visual")
		care.get_tree().quit(0)


static var _vn := 0
static var _walk_from := Vector3.ZERO
static var _quiet_at := 0.0
static var _appreciate_at := 0.0
static var _last_input := -1.0
static var _walked := 0.0
static var _walk_prev := Vector3.ZERO
static var _have_prev := false
static var _tap_walk_sec := 0.0
static var _bubble_seen := false
static var _auto_at := 0.0
static var _auto_sec := 0.0
static var _auto_wu := 0.0
static var _follow_step := 0
static var _follow_transient_logged := false
static var _opening_logged := 0.0
static var _leg_at := 0.0
static var _tap_wu := 0.0


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
	var roam = care.host.get("_roam")
	var roam_cause := "none"
	if roam:
		roam_cause = str(roam.cause)
	print("profile water result moved=", snapped(moved, 0.001), " hunger=", hunger_was, "->", hunger_now, " walk=", walk, " roam=", roam_cause)
	if walk != null or roam_cause == "tap_directed":
		_fail("water press started a ground walk")
	elif roam == null and moved > 1.0:
		_fail("water press moved the pet by %s" % moved)
	elif roam != null and roam_cause != "autonomous" and roam_cause != "none" and moved > 1.0:
		_fail("water press moved the pet by %s" % moved)
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


static func _trace_pointer(care: Node, pos: Vector2, pressed: bool, note: String) -> void:
	care.call("_pointer", pos, pressed)
	_last_input = _t
	print("TRACE t=", snapped(_t, 0.01), " kind=pointer pressed=", pressed, " pos=", pos, " note=", note, " ", _snap(care))


static func _trace_key_n(care: Node) -> void:
	var ev := InputEventKey.new()
	ev.keycode = KEY_N
	ev.pressed = true
	var vp := care.get_viewport()
	if vp:
		vp.push_input(ev)
	_last_input = _t
	print("TRACE t=", snapped(_t, 0.01), " kind=key key=N expected_wake=false expected_appreciate=true ", _snap(care))


static func _trace_state(care: Node, tag: String, expect_bubble: bool, expect_ui: String, expect_appreciate: bool, expect_mode: String) -> void:
	var quiet := _t - _last_input if _last_input >= 0.0 else -1.0
	print("TRACE t=", snapped(_t, 0.01), " kind=state tag=", tag,
		" expected_bubble=", expect_bubble, " actual_bubble=", _bubble_on(care),
		" expected_ui=", expect_ui, " actual_alpha=", _alpha(care),
		" expected_appreciate=", expect_appreciate, " actual_appreciate=", _appreciate(care),
		" expected_mode=", expect_mode, " no_input_sec=", snapped(quiet, 0.01),
		" ", _snap(care))


static func _sample_walk(care: Node) -> void:
	var slot := int(_t / 0.5)
	if slot == _sample_slot:
		return
	_sample_slot = slot
	if _vn != 0 and (_vn < 3 or _vn > 4):
		return
	print("TRACE t=", snapped(_t, 0.01), " kind=walk_sample cause=", _walk_cause(care), " ", _snap(care))


static var _sample_slot := -1


static func _snap(care: Node) -> String:
	var pet := _pet_pos(care)
	var target: Variant = care.host.get("_walk_target")
	var dest := " target_none"
	if target is Vector3:
		var tv: Vector3 = target
		dest = " target=(%.1f,%.1f)" % [tv.x, tv.z]
	var motion := "none"
	var roam = care.host.get("_roam")
	if roam:
		motion = str(roam.motion)
	return "walk_cause=%s motion=%s pet=(%.1f,%.1f) hunger=%.2f poops=%s mode=%s%s %s" % [
		_walk_cause(care), motion, pet.x, pet.z, _hunger(), _poops(), str(care.host.get("_mode")),
		dest, _bubble_px(care),
	]


static func _bubble_px(care: Node) -> String:
	var bubble: CanvasItem = care.get("_bubble") as CanvasItem
	if bubble == null:
		return "bubble_px=none"
	var p: Vector2 = bubble.position
	var s: Vector2 = bubble.size
	return "bubble_px=(%.0f,%.0f) bubble_size=(%.0f,%.0f) bubble_vis=%s" % [p.x, p.y, s.x, s.y, bubble.visible]


static func _bubble_in_view(care: Node) -> bool:
	var bubble: CanvasItem = care.get("_bubble") as CanvasItem
	if bubble == null or not bubble.visible:
		return false
	var vp: Vector2 = care.call("_viewport_size")
	var p: Vector2 = bubble.position
	var s: Vector2 = bubble.size
	return p.x >= 0.0 and p.y >= 0.0 and p.x + s.x <= vp.x and p.y + s.y <= vp.y


static func _walk_cause(care: Node) -> String:
	if care.host.get("_walk_target") != null:
		return "tap_directed"
	var roam = care.host.get("_roam")
	if roam == null:
		return "none"
	return str(roam.cause)


static func _auto_ready(care: Node) -> bool:
	var roam = care.host.get("_roam")
	if roam == null or care.host.get("_walk_target") != null:
		return false
	return float(roam.walk_sec) >= 3.0 and str(roam.cause) == "autonomous" and str(roam.motion) == "walk"


static func _roam_walk_sec(care: Node) -> float:
	var roam = care.host.get("_roam")
	if roam == null:
		return 0.0
	return float(roam.walk_sec)


static func _bubble_on(care: Node) -> bool:
	var bubble: CanvasItem = care.get("_bubble") as CanvasItem
	if bubble == null:
		return false
	return bubble.visible


static func _alpha(care: Node) -> float:
	return float(care.get("fade").alpha)


static func _appreciate(care: Node) -> bool:
	return bool(care.get("fade").appreciate)


static func _pet_pos(care: Node) -> Vector3:
	var pet: Node3D = care.host.get("_pet") as Node3D
	if pet == null:
		return Vector3.ZERO
	return pet.global_position


static func _screen_of(care: Node, world: Vector3) -> Vector2:
	var cam: Camera3D = care.host.get("_camera") as Camera3D
	if cam == null:
		return _mid(care)
	return cam.unproject_position(world)


static func _mid(care: Node) -> Vector2:
	var vp: Vector2 = care.call("_viewport_size")
	return Vector2(vp.x * 0.50, vp.y * 0.36)


static func _admire(care: Node) -> Vector2:
	return care.call("_admire_center")


static func _threshold() -> float:
	var tree := Engine.get_main_loop()
	if tree == null:
		return 70.0
	var gd: Node = tree.root.get_node_or_null("GameData")
	if gd == null:
		return 70.0
	var m1a: Dictionary = gd.get("m1a")
	var bubbles: Dictionary = m1a.get("bubbles", {})
	return float(bubbles.get("want_threshold", 70.0))


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
