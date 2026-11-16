extends RefCounted
## In-scene r4 candidate. Low 19:9. Not an art acceptance and not a Mobile claim.
## Autonomous opening uses the live roam tick and whatever personality mul the
## isolated profile rolled. The four facing legs and the seek use the live
## manual walker (WALK_SPEED 48), the same function a ground tap uses after
## the raycast. The 20 wu/s leg sets motion axis 0 on this profile only, then
## uses the live roam tick. Care hold, blocked, and stop use real zero steps.

const TRACE_SEED := 2

static var _dead := false
static var _t := 0.0
static var _phase := "open"
static var _right := Vector2.RIGHT
static var _away := Vector2(0, -1)
static var _pads: Array[Vector2] = []
static var _dirs: Array[Vector2] = []
static var _names: PackedStringArray = []
static var _leg := 0
static var _goal := Vector2.ZERO
static var _phase0 := 0.0
static var _moved := 0.0
static var _pos := Vector2.ZERO
static var _have := false
static var _had_target := false
static var _tracking := false
static var _full: Array[float] = []
static var _expect := 48.0
static var _mark := 0.0
static var _hold_dest: Variant = null
static var _side_stop := false
static var _auto_wu := 0.0
static var _auto_sec := 0.0
static var _auto_full: Array[float] = []
static var _auto_partial := 0
static var _mul := 1.0
static var _seen_walk := false
static var _anchor := Vector2.ZERO
static var _rate_wu := 0.0
static var _last_walk := ""


static func fixture(care: Node) -> void:
	_require()
	var vp: Vector2 = care.call("_viewport_size")
	print("TRACE header walkclip=r4_candidate_not_accepted")
	print("TRACE header viewport=", vp, " mode=low aspect=19:9")
	print("TRACE header schedule=autonomous_zero_taps; care_hold; live_manual_48 right,left,stop_side_idle,back,front; roam_blocked; fixture_motion_0_live_roam_20")
	print("TRACE header speeds live_tap=manual_48 autonomous=roam_20_times_personality no_fps_cap")
	print("TRACE header rights=not_independently_verified not_commercially_cleared")
	print("TRACE header foot=side_identity_only front_back_projection_no_z_lock quantization_under_2wu_not_claimed")
	var roam = care.host.get("_roam")
	if roam and roam.has_method("seed"):
		roam.seed(TRACE_SEED)
	_right = care.host.call("walk_view_right")
	_away = care.host.call("walk_view_away")
	_dirs = [_right, -_right, _away, -_away]
	_names = PackedStringArray(["side_right", "side_left", "back", "front"])
	_pads = [Vector2(0, 55), Vector2(0, 70), Vector2(-60, 10), Vector2(100, 20), Vector2(-20, 60), Vector2(20, 60)]
	var personality := _personality()
	if personality:
		_mul = float(personality.call("walk_speed_mul", "tuanrong"))
	_pos = _xz(care)
	_have = true
	print("TRACE t=0 kind=view right=(", snapped(_right.x, 0.001), ",", snapped(_right.y, 0.001), ") away=(", snapped(_away.x, 0.001), ",", snapped(_away.y, 0.001), ") personality_mul=", snapped(_mul, 0.001), " provenance=actual_isolated_profile")
	print("profile walkclip user_data_dir=", OS.get_user_data_dir())


static func tick(care: Node, dt: float) -> void:
	if _dead:
		return
	_t += dt
	if not _contract(care):
		return
	var pos := _xz(care)
	var moved := 0.0
	if _have:
		moved = pos.distance_to(_pos)
	var target_on := care.host.get("_walk_target") != null
	if _tracking and _had_target:
		_moved += moved
		if target_on and dt > 0.0 and moved > 0.0001 and pos.distance_to(_goal) > 1.3:
			var spd := moved / dt
			_full.append(spd)
			if absf(spd - _expect) > 0.75:
				_fail("full step speed %s wanted %s" % [spd, _expect])
				return
	_pos = pos
	_have = true
	_had_target = target_on
	match _phase:
		"open":
			_tick_open(care, dt, moved)
		"hold":
			_tick_hold(care)
		"seek":
			_tick_seek(care)
		"leg":
			_tick_leg(care)
		"stop":
			_tick_stop(care)
		"blocked":
			_tick_blocked(care, moved)
		"rate20":
			_tick_rate20(care, dt, moved)
		_:
			_fail("unknown phase " + _phase)


static func _tick_open(care: Node, dt: float, moved: float) -> void:
	if care.host.get("_walk_target") != null:
		_fail("autonomous opening acquired a manual target")
		return
	var roam = care.host.get("_roam")
	if roam == null:
		_fail("roam missing")
		return
	if str(roam.motion) == "walk" and dt > 0.0:
		_seen_walk = true
		_auto_wu += moved
		_auto_sec += dt
		var spd := moved / dt
		var want_now := 20.0 * _mul
		if spd > want_now + 1.5:
			_fail("autonomous step %s is above 20*mul" % spd)
			return
		if spd >= want_now - 0.75:
			_auto_full.append(spd)
		elif moved > 0.0001:
			# The roam step is min(speed*dt, distance still left). A short remainder is not a new speed.
			_auto_partial += 1
	if _auto_sec >= 3.0 and _seen_walk:
		var measured := _auto_wu / _auto_sec
		var want := 20.0 * _mul
		var full_avg := 0.0
		for s in _auto_full:
			full_avg += s
		if _auto_full.size() > 0:
			full_avg /= float(_auto_full.size())
		print("TRACE t=", snapped(_t, 0.01), " kind=autonomous_open taps=0 walk_sec=", snapped(float(roam.walk_sec), 0.01), " path_wu_s=", snapped(measured, 0.01), " full_step_wu_s=", snapped(full_avg, 0.01), " full_steps=", _auto_full.size(), " short_remainders=", _auto_partial, " expected_wu_s=", snapped(want, 0.01), " mul=", snapped(_mul, 0.001), " cause=", str(roam.cause), " provenance=actual_roam_tick_zero_taps")
		if str(roam.cause) != "autonomous":
			_fail("opening cause was " + str(roam.cause))
			return
		if _auto_full.is_empty() or absf(full_avg - want) > 0.5:
			_fail("autonomous full steps averaged %s, want %s" % [full_avg, want])
			return
		_hold_dest = roam.dest
		roam.set_care_hold(true)
		_mark = _t
		_phase0 = float(care.host.call("walk_clip_state").get("phase_wu", 0.0))
		_anchor = _xz(care)
		_phase = "hold"
		return
	if _t >= 12.0:
		_fail("autonomous motion did not reach 3s, walk_sec=%s" % float(roam.walk_sec))


static func _tick_hold(care: Node) -> void:
	var roam = care.host.get("_roam")
	roam.set_care_hold(true)
	if _t < _mark + 0.15:
		return
	var st: Dictionary = care.host.call("walk_clip_state")
	var drift := _xz(care).distance_to(_anchor)
	if drift > 0.001:
		_fail("care hold moved the pet by %s" % drift)
		return
	if bool(st.get("moving", true)):
		_fail("care hold played a walk frame")
		return
	if absf(float(st.get("phase_wu", -1)) - _phase0) > 0.0001:
		_fail("care hold advanced the phase")
		return
	if _t < _mark + 0.55:
		return
	if str(roam.motion) != "hold":
		_fail("care hold motion was " + str(roam.motion))
		return
	if roam.dest != _hold_dest:
		_fail("care hold cleared the roam target")
		return
	print("TRACE t=", snapped(_t, 0.01), " kind=hold clip=", str(st.get("clip", "")), " phase_wu=", snapped(float(st.get("phase_wu", 0)), 0.01), " facing=", str(st.get("facing", "")), " provenance=live_care_hold_zero_distance")
	roam.set_care_hold(false)
	roam.dest = null
	roam._stash = null
	roam._pause = 0.0
	roam._manual = false
	_phase = "seek"


static func _tick_seek(care: Node) -> void:
	var here := _xz(care)
	var pad := _best_pad(care, here)
	if pad == Vector2.INF:
		_fail("no lawn pad has 12wu clear on right, left, back, and front")
		return
	if here.distance_to(pad) <= 1.5:
		print("TRACE t=", snapped(_t, 0.01), " kind=pad world=(", snapped(pad.x, 0.1), ",", snapped(pad.y, 0.1), ") provenance=already_there")
		_leg = 0
		_begin_leg(care)
		return
	if care.host.get("_walk_target") == null and not _tracking:
		print("TRACE t=", snapped(_t, 0.01), " kind=seek world=(", snapped(pad.x, 0.1), ",", snapped(pad.y, 0.1), ") provenance=live_manual_walk_target")
		_begin_manual(care, pad, 48.0)
		return
	if care.host.get("_walk_target") == null and _tracking and _moved > 1.0:
		if _full.is_empty():
			_fail("seek produced no full 48 step")
			return
		print("TRACE t=", snapped(_t, 0.01), " kind=seek_done samples=", _full.size(), " speed=", snapped(_full[0], 0.01), " provenance=live_manual_walk_target")
		_tracking = false
		_leg = 0
		_begin_leg(care)


static func _tick_leg(care: Node) -> void:
	if care.host.get("_walk_target") != null:
		var live: Dictionary = care.host.call("walk_clip_state")
		if bool(live.get("moving", false)):
			_last_walk = str(live.get("path", "")) + " frame=" + str(live.get("frame", -1))
		if _t >= _mark + 4.0:
			_fail("manual leg %s did not arrive" % _names[_leg])
		return
	if _moved < 8.0:
		_fail("manual leg %s moved only %s" % [_names[_leg], _moved])
		return
	if _full.is_empty():
		_fail("manual leg %s produced no full 48 step" % _names[_leg])
		return
	if _last_walk == "":
		_fail("manual leg %s never showed a walk frame" % _names[_leg])
		return
	var st: Dictionary = care.host.call("walk_clip_state")
	var phase_now := float(st.get("phase_wu", 0.0))
	if absf((phase_now - _phase0) - _moved) > 0.05:
		_fail("phase %s did not follow distance %s" % [phase_now - _phase0, _moved])
		return
	var want_face := "side"
	var want_flip := false
	if _names[_leg] == "side_left":
		want_flip = true
	elif _names[_leg] == "back":
		want_face = "back"
	elif _names[_leg] == "front":
		want_face = "front"
	if str(st.get("facing", "")) != want_face or bool(st.get("flip_h", false)) != want_flip:
		_fail("leg %s facing %s flip %s" % [_names[_leg], st.get("facing", ""), st.get("flip_h", false)])
		return
	print("TRACE t=", snapped(_t, 0.01), " kind=manual leg=", _names[_leg], " facing=", want_face, " flip=", want_flip, " dist_wu=", snapped(_moved, 0.01), " phase_delta=", snapped(phase_now - _phase0, 0.01), " full_steps=", _full.size(), " speed=", snapped(_full[0], 0.01), " last_walk=", _last_walk, " provenance=live_manual_walk_target speed_const=48")
	_side_stop = _names[_leg] == "side_left"
	_phase0 = phase_now
	_mark = _t
	_tracking = false
	_phase = "stop"


static func _tick_stop(care: Node) -> void:
	if care.host.get("_walk_target") != null:
		_fail("stop still had a manual target")
		return
	var st: Dictionary = care.host.call("walk_clip_state")
	if bool(st.get("moving", true)):
		if _t < _mark + 0.05:
			return
		_fail("stop kept walking")
		return
	if absf(float(st.get("phase_wu", 0.0)) - _phase0) > 0.0001:
		_fail("stop advanced the phase")
		return
	var clip := str(st.get("clip", ""))
	if _t < _mark + 0.4:
		return
	if not clip.ends_with("_idle"):
		_fail("stop clip was " + clip)
		return
	if _side_stop:
		var path := str(st.get("path", ""))
		if not path.ends_with("side_idle_01.png") or path.find("front_idle") >= 0:
			_fail("side stop used " + path)
			return
		if not bool(st.get("flip_h", false)):
			_fail("side stop lost the left flip")
			return
	print("TRACE t=", snapped(_t, 0.01), " kind=stop clip=", clip, " flip=", bool(st.get("flip_h", false)), " phase_wu=", snapped(float(st.get("phase_wu", 0)), 0.01), " provenance=zero_distance_after_manual")
	_leg += 1
	if _leg < _names.size():
		_begin_leg(care)
		return
	_begin_blocked(care)


static func _tick_blocked(care: Node, moved: float) -> void:
	var roam = care.host.get("_roam")
	roam.set_care_hold(false)
	roam._manual = false
	roam._pause = 0.0
	roam.dest = Vector2(80, -70)
	if moved > 0.05:
		_fail("blocked roam moved %s" % moved)
		return
	if _t < _mark + 0.45:
		return
	var st: Dictionary = care.host.call("walk_clip_state")
	if bool(st.get("moving", true)):
		_fail("blocked roam played a walk")
		return
	if absf(float(st.get("phase_wu", 0.0)) - _phase0) > 0.02:
		_fail("blocked roam advanced the phase")
		return
	if _xz(care).distance_to(_anchor) > 0.02:
		_fail("blocked roam left the cottage edge")
		return
	if str(roam.motion) != "idle":
		_fail("blocked motion was " + str(roam.motion))
		return
	print("TRACE t=", snapped(_t, 0.01), " kind=blocked clip=", str(st.get("clip", "")), " motion=", str(roam.motion), " provenance=live_roam_tick_into_cottage")
	_begin_rate20(care)


static func _tick_rate20(care: Node, dt: float, moved: float) -> void:
	var roam = care.host.get("_roam")
	if str(roam.motion) == "walk" and dt > 0.0 and moved > 0.0001:
		_rate_wu += moved
		var spd := moved / dt
		if spd > 20.75:
			_fail("fixture 20 leg ran at %s" % spd)
			return
		if spd >= 19.25:
			_full.append(spd)
	var here := _xz(care)
	if here.distance_to(_goal) > 1.6 and _t < _mark + 3.0:
		return
	if _full.is_empty() or _rate_wu < 8.0:
		_fail("fixture 20 leg samples %s dist %s" % [_full.size(), _rate_wu])
		return
	var st: Dictionary = care.host.call("walk_clip_state")
	print("TRACE t=", snapped(_t, 0.01), " kind=roam20 samples=", _full.size(), " speed=", snapped(_full[0], 0.01), " dist_wu=", snapped(_rate_wu, 0.01), " facing=", str(st.get("facing", "")), " phase_wu=", snapped(float(st.get("phase_wu", 0)), 0.01), " provenance=fixture_motion_axis_0_live_roam_tick")
	_dead = true
	print("PASS walkclip")
	care.get_tree().quit(0)


static func _begin_leg(care: Node) -> void:
	var here := _xz(care)
	var dir: Vector2 = _dirs[_leg]
	var span := _span(care, here, dir)
	if span < 12.0:
		_fail("leg %s clear span %s from %s" % [_names[_leg], span, here])
		return
	print("TRACE t=", snapped(_t, 0.01), " kind=leg_start leg=", _names[_leg], " span=", span, " provenance=live_manual_walk_target")
	_begin_manual(care, here + dir * span, 48.0)
	_phase = "leg"


static func _begin_blocked(care: Node) -> void:
	var pet: Node3D = care.host.get("_pet")
	pet.position = Vector3(80.0, pet.position.y, -39.999)
	care.host.call("walk_clip_rebase")
	var roam = care.host.get("_roam")
	roam.set_care_hold(false)
	roam.dest = Vector2(80, -70)
	roam._stash = null
	roam._pause = 0.0
	roam._manual = false
	care.host.set("_walk_target", null)
	_pos = Vector2(80.0, -39.999)
	_anchor = _pos
	_have = true
	_tracking = false
	_phase0 = float(care.host.call("walk_clip_state").get("phase_wu", 0.0))
	_mark = _t
	_phase = "blocked"
	print("TRACE t=", snapped(_t, 0.01), " kind=blocked_place world=(80,-39.999) note=rebase_so_the_placement_is_not_a_step provenance=live_roam_tick_into_cottage")


static func _begin_rate20(care: Node) -> void:
	var personality := _personality()
	if personality == null:
		_fail("personality missing")
		return
	var rec: Dictionary = personality.call("get_for", "tuanrong")
	rec = rec.duplicate(true)
	var before := int(rec.get("motion", 0))
	rec["motion"] = 0
	personality.call("set_for", "tuanrong", rec)
	var mul := float(personality.call("walk_speed_mul", "tuanrong"))
	if not is_equal_approx(mul, 1.0):
		_fail("motion 0 mul was %s" % mul)
		return
	var here := _xz(care)
	var goal := Vector2(here.x, here.y + 16.0)
	var roam = care.host.get("_roam")
	if not roam.segment_free(here, goal):
		goal = Vector2(here.x, here.y - 16.0)
	if not roam.segment_free(here, goal):
		_fail("no 16wu roam leg from the cottage edge")
		return
	roam.set_care_hold(false)
	roam.dest = goal
	roam._stash = null
	roam._pause = 0.0
	roam._manual = false
	care.host.set("_walk_target", null)
	_goal = goal
	_full = []
	_rate_wu = 0.0
	_mark = _t
	_phase = "rate20"
	print("TRACE t=", snapped(_t, 0.01), " kind=rate20_start motion_before=", before, " motion_now=0 goal=(", snapped(goal.x, 0.1), ",", snapped(goal.y, 0.1), ") provenance=fixture_motion_axis_0_live_roam_tick isolated_profile_only")


static func _begin_manual(care: Node, goal: Vector2, expect: float) -> void:
	var roam = care.host.get("_roam")
	roam.set_care_hold(false)
	roam.dest = null
	roam._stash = null
	roam._pause = 0.0
	roam._manual = false
	_goal = goal
	_phase0 = float(care.host.call("walk_clip_state").get("phase_wu", 0.0))
	_moved = 0.0
	_full = []
	_expect = expect
	_tracking = true
	_last_walk = ""
	# The target is armed for the next capture tick. That step must be counted.
	_had_target = true
	_mark = _t
	care.host.set("_walk_target", Vector3(goal.x, 0.0, goal.y))


static func _best_pad(care: Node, here: Vector2) -> Vector2:
	var roam = care.host.get("_roam")
	var best := Vector2.INF
	var best_score := -1.0
	var spots: Array[Vector2] = [here]
	for p in _pads:
		spots.append(p)
	for spot in spots:
		if spot != here and not roam.segment_free(here, spot):
			continue
		var score := 24.0
		for d in _dirs:
			score = minf(score, _span(care, spot, d))
		if score > best_score:
			best_score = score
			best = spot
	if best_score < 12.0:
		return Vector2.INF
	return best


static func _span(care: Node, origin: Vector2, dir: Vector2) -> float:
	var roam = care.host.get("_roam")
	var best := 0.0
	for d in [24.0, 16.0, 12.0, 8.0]:
		if roam.segment_free(origin, origin + dir * d):
			return d
		best = 0.0
	return best


static func _contract(care: Node) -> bool:
	var st: Dictionary = care.host.call("walk_clip_state")
	if st.is_empty():
		_fail("walk clip state missing")
		return false
	if not bool(st.get("centered", false)):
		_fail("sprite centering changed")
		return false
	if not is_equal_approx(float(st.get("pixel_size", 0)), 1.0):
		_fail("pixel size changed")
		return false
	if not is_equal_approx(float(st.get("y", 0)), 29.0):
		_fail("pet y changed")
		return false
	var off: Vector2 = st.get("offset", Vector2.INF)
	if off.length() > 0.001:
		_fail("a pivot offset was introduced")
		return false
	if int(st.get("tex_w", 0)) != 64 or int(st.get("tex_h", 0)) != 64:
		_fail("frame is not 64")
		return false
	if int(st.get("filter", -1)) != int(BaseMaterial3D.TEXTURE_FILTER_NEAREST):
		_fail("texture filter changed")
		return false
	if bool(st.get("sprite_flip_h", false)) != bool(st.get("flip_h", false)):
		_fail("sprite flip does not match the clip")
		return false
	if bool(st.get("z_lock", true)) or bool(st.get("continuous_lock", true)):
		_fail("clip claimed a lock the art does not have")
		return false
	return true


static func _xz(care: Node) -> Vector2:
	var pet: Node3D = care.host.get("_pet")
	return Vector2(pet.position.x, pet.position.z)


static func _personality() -> Node:
	var tree := Engine.get_main_loop()
	if tree == null:
		return null
	return tree.root.get_node_or_null("Personality")


static func _require() -> void:
	var want := OS.get_environment("HD2D_PROFILE_NAME")
	var got := OS.get_user_data_dir()
	if want == "" or got.find(want) < 0:
		_fail("walk clip trace is not on an isolated profile")


static func _fail(msg: String) -> void:
	print("FAIL ", msg)
	_dead = true
	var tree := Engine.get_main_loop()
	if tree:
		tree.quit(1)
