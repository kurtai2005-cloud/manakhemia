extends RefCounted

const WalkClip := preload("res://gameplay/m1_walk_clip.gd")
## Evidence fixture for the r4 walk candidate. Not art acceptance.
## Does not change speeds, camera policy, or normal tap-return.
## A ground tap while follow is on still leaves follow and does not walk.
## This fixture never sends that tap. It calls _enter_follow, then sets
## _walk_target or a roam dest directly, so follow stays on.
##
## Movie frame mapping, Godot 4.7.2 main.cpp:
## process runs, then draw increments Engine.get_frames_drawn(), then
## MovieWriter.add_frame writes the viewport texture.
## PNG suffix N is the frames_drawn value sampled in the process whose
## draw becomes that image, when every iteration draws once.
## The window title "MovieWriter: Frame N" is that value plus 1.
## process_frames is not a movie frame. It is logged only so a skipped
## draw is visible. AVI has no per-frame filename.

const TRACE_SEED := 2
const ROUTE_WU := 24.0
const STOP_SEC := 0.30
const MOVIE_W := 1080
const MOVIE_H := 2280

static var _dead := false
static var _t := 0.0
static var _phase := "open"
static var _stage := "run"
static var _right := Vector2.RIGHT
static var _away := Vector2(0, -1)
static var _origin := Vector2.ZERO
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
static var _auto_wu := 0.0
static var _auto_sec := 0.0
static var _auto_full: Array[float] = []
static var _auto_partial := 0
static var _mul := 1.0
static var _seen_walk := false
static var _leg_name := ""
static var _stop_next := ""
static var _stop_drawn := -1
static var _rate_wu := 0.0
static var _movie_judged := false
static var _threshold := 70.0
static var _anchor := Vector2.ZERO
static var _settle_next := "follow48"
static var _ab_done := false
static var _ab_stage := "old"
static var _shadow_force := ""


static func fixture(care: Node) -> void:
	_require()
	_keep_bubble(care)
	print("TRACE header walkclip=r4_evidence_fixture_not_accepted")
	print("TRACE header schedule=autonomous_zero_taps; hold>=0.30; panorama_side48_24wu; stop>=0.30 plus one rendered frame; follow settle; character_grounding offset0 then offset2; shadow_only uncorrected then corrected with offset2 held; existing_follow_side48_24wu; stop; isolated_profile_side20_24wu; stop")
	print("TRACE header speeds live_manual=48 fixture_roam20=motion_axis_0_only no_fps_cap")
	print("TRACE header movie_png_index=frames_drawn_in_process_before_draw title_frame=frames_drawn_plus_1 process_frames_is_not_a_movie_frame")
	print("TRACE header rights=not_independently_verified not_commercially_cleared")
	_log_sizes(care, "boot")
	var roam = care.host.get("_roam")
	if roam and roam.has_method("seed"):
		roam.seed(TRACE_SEED)
	_right = care.host.call("walk_view_right")
	_away = care.host.call("walk_view_away")
	var personality := _personality()
	if personality:
		_mul = float(personality.call("walk_speed_mul", "tuanrong"))
	_pos = _xz(care)
	_have = true
	_threshold = _want_threshold()
	print("TRACE t=0 kind=view right=(", snapped(_right.x, 0.001), ",", snapped(_right.y, 0.001), ") away=(", snapped(_away.x, 0.001), ",", snapped(_away.y, 0.001), ") personality_mul=", snapped(_mul, 0.001), " provenance=actual_isolated_profile ", _frame_tag())
	print("profile walkclip user_data_dir=", OS.get_user_data_dir())


static func tick(care: Node, dt: float) -> void:
	if _dead:
		return
	_t += dt
	_keep_bubble(care)
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
	if (_phase == "leg" or _phase == "rate20") and _leg_name != "":
		if not _visible(care):
			return
	match _phase:
		"open":
			_tick_open(care, dt, moved)
		"hold":
			_tick_hold(care)
		"leg":
			_tick_leg(care)
		"stop":
			_tick_stop(care)
		"follow_wait":
			_tick_follow_wait(care)
		"anchor_ab":
			_tick_anchor_ab(care)
		"shadow_ab":
			_tick_shadow_ab(care)
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
			_auto_partial += 1
	if _auto_sec < 3.0 or not _seen_walk:
		if _t >= 12.0:
			_fail("autonomous motion did not reach 3s, walk_sec=%s" % float(roam.walk_sec))
		return
	var measured := _auto_wu / _auto_sec
	var want := 20.0 * _mul
	var full_avg := 0.0
	for s in _auto_full:
		full_avg += s
	if _auto_full.size() > 0:
		full_avg /= float(_auto_full.size())
	print("TRACE t=", snapped(_t, 0.01), " kind=autonomous_open taps=0 walk_sec=", snapped(float(roam.walk_sec), 0.01), " path_wu_s=", snapped(measured, 0.01), " full_step_wu_s=", snapped(full_avg, 0.01), " full_steps=", _auto_full.size(), " short_remainders=", _auto_partial, " expected_wu_s=", snapped(want, 0.01), " mul=", snapped(_mul, 0.001), " cause=", str(roam.cause), " provenance=actual_roam_tick_zero_taps ", _frame_tag())
	if str(roam.cause) != "autonomous":
		_fail("opening cause was " + str(roam.cause))
		return
	if _auto_full.is_empty() or absf(full_avg - want) > 0.5:
		_fail("autonomous full steps averaged %s, want %s" % [full_avg, want])
		return
	_hold_dest = roam.dest
	roam.set_care_hold(true)
	_mark = _t
	_stage = "hold"
	_phase0 = float(care.host.call("walk_clip_state").get("phase_wu", 0.0))
	_anchor = _xz(care)
	print("TRACE t=", snapped(_t, 0.01), " kind=hold_begin provenance=live_care_hold_zero_distance ", _frame_tag())
	_phase = "hold"


static func _tick_hold(care: Node) -> void:
	var roam = care.host.get("_roam")
	roam.set_care_hold(true)
	if _stage == "gap":
		if Engine.get_frames_drawn() <= _stop_drawn:
			return
		if roam.dest != _hold_dest:
			_fail("care hold cleared the roam target")
			return
		print("TRACE t=", snapped(_t, 0.01), " kind=hold_gap rendered_after_end=true ", _frame_tag())
		roam.set_care_hold(false)
		roam.dest = null
		roam._stash = null
		roam._pause = 0.0
		roam._manual = false
		_arm_panorama_from_search(care)
		return
	if _t < _mark + 0.15:
		return
	var st: Dictionary = care.host.call("walk_clip_state")
	if _xz(care).distance_to(_anchor) > 0.001:
		_fail("care hold moved the pet")
		return
	if bool(st.get("moving", true)):
		_fail("care hold played a walk frame")
		return
	if absf(float(st.get("phase_wu", -1.0)) - _phase0) > 0.0001:
		_fail("care hold advanced the phase")
		return
	if _t < _mark + STOP_SEC:
		return
	if str(roam.motion) != "hold":
		_fail("care hold motion was " + str(roam.motion))
		return
	if roam.dest != _hold_dest:
		_fail("care hold cleared the roam target")
		return
	_stop_drawn = Engine.get_frames_drawn()
	_stage = "gap"
	print("TRACE t=", snapped(_t, 0.01), " kind=hold_end held_sec=", snapped(_t - _mark, 0.01), " clip=", str(st.get("clip", "")), " select_png_index=", _stop_drawn, " ", _frame_tag())


static func _tick_leg(care: Node) -> void:
	if care.host.get("_walk_target") != null:
		if _t >= _mark + 4.0:
			_fail("manual leg %s did not arrive" % _leg_name)
		return
	if _moved < ROUTE_WU - 0.05:
		_fail("manual leg %s moved only %s" % [_leg_name, _moved])
		return
	if _full.is_empty():
		_fail("manual leg %s produced no full 48 step" % _leg_name)
		return
	var st: Dictionary = care.host.call("walk_clip_state")
	var phase_now := float(st.get("phase_wu", 0.0))
	if absf((phase_now - _phase0) - _moved) > 0.05:
		_fail("phase %s did not follow distance %s" % [phase_now - _phase0, _moved])
		return
	if str(st.get("facing", "")) != "side" or bool(st.get("flip_h", true)):
		_fail("leg %s facing %s flip %s" % [_leg_name, st.get("facing", ""), st.get("flip_h", true)])
		return
	var cycles := _moved / 12.0
	print("TRACE t=", snapped(_t, 0.01), " kind=leg_end leg=", _leg_name, " facing=side flip=false dist_wu=", snapped(_moved, 0.01), " cycles=", snapped(cycles, 0.01), " phase_delta=", snapped(phase_now - _phase0, 0.01), " full_steps=", _full.size(), " speed=", snapped(_full[0], 0.01), " provenance=live_manual_walk_target ", _frame_tag())
	_begin_stop(care, "follow_setup" if _leg_name == "panorama48" else "rate20_setup")


static func _tick_stop(care: Node) -> void:
	var roam_stop = care.host.get("_roam")
	roam_stop.set_care_hold(true)
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
	if _stage == "gap":
		if Engine.get_frames_drawn() <= _stop_drawn:
			return
		if not clip.ends_with("side_idle") or bool(st.get("flip_h", true)):
			_fail("gap frame left side idle, clip=%s flip=%s" % [clip, st.get("flip_h", true)])
			return
		print("TRACE t=", snapped(_t, 0.01), " kind=stop_gap rendered_after_end=true select_png_index=", _stop_drawn, " ", _frame_tag())
		_after_stop(care)
		return
	if _t < _mark + STOP_SEC:
		return
	if not clip.ends_with("side_idle") or bool(st.get("flip_h", true)):
		_fail("stop clip was %s flip=%s" % [clip, st.get("flip_h", true)])
		return
	_stop_drawn = Engine.get_frames_drawn()
	_stage = "gap"
	print("TRACE t=", snapped(_t, 0.01), " kind=stop_end held_sec=", snapped(_t - _mark, 0.01), " clip=", clip, " flip=false select_png_index=", _stop_drawn, " next_not_armed=true ", _frame_tag())


static func _tick_follow_wait(care: Node) -> void:
	var roam = care.host.get("_roam")
	roam.set_care_hold(true)
	if care.host.get("_walk_target") != null:
		_fail("follow settle armed a manual target")
		return
	if not bool(care.call("follow_close")):
		_fail("follow did not stay on")
		return
	var st: Dictionary = care.host.call("follow_zoom_state")
	if not bool(st.get("settled", false)) or float(st.get("frac", 0.0)) < float(st.get("need", 0.20)):
		if _t >= _mark + 12.0:
			_fail("follow did not settle, frac=%s" % st.get("frac", 0.0))
		return
	if not _movie_judged:
		_movie_judged = true
		if not _judge_movie_close(care, st):
			return
	if Engine.get_frames_drawn() <= _stop_drawn:
		return
	print("TRACE t=", snapped(_t, 0.01), " kind=follow_settled next=", _settle_next, " frac=", st.get("frac", 0), " need=", st.get("need", 0), " dist=", st.get("dist", 0), " no_ground_tap=true ", _frame_tag())
	_log_sizes(care, "follow_settled")
	if _settle_next == "rate20":
		roam.set_care_hold(false)
		_start_rate20(care)
		return
	if not _ab_done:
		_ab_done = true
		_begin_anchor_plate(care, false)
		return
	roam.set_care_hold(false)
	_arm_route(care, "follow48", 48.0)


static func _tick_rate20(care: Node, dt: float, moved: float) -> void:
	var roam = care.host.get("_roam")
	if not bool(care.call("follow_close")):
		_fail("side20 left follow")
		return
	if str(roam.motion) == "walk" and dt > 0.0 and moved > 0.0001:
		_rate_wu += moved
		var spd := moved / dt
		if spd > 20.75:
			_fail("fixture 20 leg ran at %s" % spd)
			return
		if spd >= 19.25:
			_full.append(spd)
	var here := _xz(care)
	if here.distance_to(_goal) > 1.6 and _t < _mark + 4.0:
		return
	if _rate_wu < ROUTE_WU - 0.05 or _full.is_empty():
		_fail("fixture 20 leg samples %s dist %s" % [_full.size(), _rate_wu])
		return
	var clip: Dictionary = care.host.call("walk_clip_state")
	var cycles := _rate_wu / 12.0
	print("TRACE t=", snapped(_t, 0.01), " kind=leg_end leg=follow20 facing=", str(clip.get("facing", "")), " flip=", bool(clip.get("flip_h", true)), " dist_wu=", snapped(_rate_wu, 0.01), " cycles=", snapped(cycles, 0.01), " speed=", snapped(_full[0], 0.01), " provenance=fixture_motion_axis_0_live_roam_tick ", _frame_tag())
	if str(clip.get("facing", "")) != "side" or bool(clip.get("flip_h", true)):
		_fail("side20 did not stay on unflipped side")
		return
	_phase0 = float(clip.get("phase_wu", 0.0))
	_begin_stop(care, "finish")


static func _after_stop(care: Node) -> void:
	match _stop_next:
		"follow_setup":
			_place_origin(care)
			care.call("_enter_follow", care.host.get("_pet"))
			var roam = care.host.get("_roam")
			roam.set_care_hold(true)
			roam.dest = null
			care.host.set("_walk_target", null)
			_settle_next = "follow48"
			_mark = _t
			_stop_drawn = Engine.get_frames_drawn()
			_phase = "follow_wait"
			print("TRACE t=", snapped(_t, 0.01), " kind=follow_enter via=_enter_follow no_ground_tap=true ", _frame_tag())
		"rate20_setup":
			_place_origin(care)
			_settle_next = "rate20"
			var roam_r = care.host.get("_roam")
			roam_r.set_care_hold(true)
			roam_r.dest = null
			care.host.set("_walk_target", null)
			_mark = _t
			_stop_drawn = Engine.get_frames_drawn()
			_phase = "follow_wait"
		"finish":
			_log_sizes(care, "done")
			print("PASS walkclip")
			_dead = true
			care.get_tree().quit(0)
		_:
			_fail("unknown stop next " + _stop_next)


static func _begin_stop(care: Node, next: String) -> void:
	var st: Dictionary = care.host.call("walk_clip_state")
	_phase0 = float(st.get("phase_wu", 0.0))
	_stop_next = next
	_stage = "hold"
	_mark = _t
	_tracking = false
	_phase = "stop"
	var roam = care.host.get("_roam")
	roam.set_care_hold(true)
	roam._stash = null
	care.host.set("_walk_target", null)
	print("TRACE t=", snapped(_t, 0.01), " kind=stop_begin clip=", str(st.get("clip", "")), " facing=", str(st.get("facing", "")), " flip=", bool(st.get("flip_h", true)), " ", _frame_tag())


static func _begin_anchor_plate(care: Node, grounded: bool) -> void:
	care.host.call("set_foot_visual_anchor", grounded)
	_ab_stage = "grounded" if grounded else "old"
	_stage = "hold"
	_mark = _t
	_phase = "anchor_ab"
	var label := "grounded_offset_y2_sole_boundary_y0" if grounded else "old_node_y29_offset0"
	print("TRACE t=", snapped(_t, 0.01), " kind=anchor_begin source=", label, " ", _anchor_line(care))


static func _tick_anchor_ab(care: Node) -> void:
	var roam = care.host.get("_roam")
	roam.set_care_hold(true)
	if care.host.get("_walk_target") != null:
		_fail("anchor plate armed a walk")
		return
	var got: Dictionary = care.host.call("foot_anchor_state")
	if absf(float(got.get("node_y", -1.0)) - 29.0) > 0.001:
		_fail("anchor plate moved the walk root")
		return
	if _stage == "gap":
		if Engine.get_frames_drawn() <= _stop_drawn:
			return
		print("TRACE t=", snapped(_t, 0.01), " kind=anchor_gap source=", _ab_stage, " rendered_after_end=true ", _frame_tag())
		if _ab_stage == "old":
			_begin_anchor_plate(care, true)
		else:
			_begin_shadow_plate(care, false)
		return
	if _t < _mark + STOP_SEC:
		return
	if not _live_shadow_ok(care, true):
		return
	_stop_drawn = Engine.get_frames_drawn()
	_stage = "gap"
	print("TRACE t=", snapped(_t, 0.01), " kind=anchor_end held_sec=", snapped(_t - _mark, 0.01), " source=", _ab_stage, " select_png_index=", _stop_drawn, " ", _anchor_line(care), " ", _shadow_line(care, true), " ", _frame_tag())


static func _anchor_line(care: Node) -> String:
	var got: Dictionary = care.host.call("foot_anchor_state")
	var oy := float(got.get("offset_y", 0.0))
	var sole := float(got.get("sole_boundary_y", 0.0))
	return "plate=character_grounding node_y=%.3f offset_y=%.3f sole_boundary_y=%.3f row61_center_y=%.3f row62_center_y=%.3f row62_span_y=%.3f..%.3f" % [
		float(got.get("node_y", 0.0)), oy, sole,
		float(got.get("row61_center_y", 0.0)), float(got.get("row62_center_y", 0.0)),
		float(got.get("row62_bottom_y", 0.0)), float(got.get("row62_top_y", 0.0)),
	]


static func _begin_shadow_plate(care: Node, corrected: bool) -> void:
	care.host.call("set_foot_visual_anchor", true)
	_ensure_shadow_force(care)
	_shadow_force = "corrected" if corrected else "uncorrected"
	care.host.set_meta("vc27_shadow_force", _shadow_force)
	_stage = "hold"
	_mark = _t
	_phase = "shadow_ab"
	var label := "corrected_visual_center" if corrected else "uncorrected_node_height"
	print("TRACE t=", snapped(_t, 0.01), " kind=shadow_begin mode=", label, " pick=shadow_end foot_offset_held=2 ", _shadow_line(care, corrected), " ", _frame_tag())


static func _tick_shadow_ab(care: Node) -> void:
	var roam = care.host.get("_roam")
	roam.set_care_hold(true)
	if care.host.get("_walk_target") != null:
		_fail("shadow plate armed a walk")
		return
	var got: Dictionary = care.host.call("foot_anchor_state")
	if _shadow_force == "corrected" and absf(float(got.get("offset_y", -1.0)) - WalkClip.GROUNDED_OFFSET_Y) > 0.001:
		_fail("shadow plate changed the foot offset")
		return
	if _shadow_force == "uncorrected" and care.host.has_meta("vc27_draw_offset"):
		if absf(float(care.host.get_meta("vc27_draw_offset")) - WalkClip.GROUNDED_OFFSET_Y) > 0.001:
			_fail("the uncorrected plate drew the feet at the wrong offset")
			return
	if absf(float(got.get("node_y", -1.0)) - 29.0) > 0.001:
		_fail("shadow plate moved the walk root")
		return
	_ensure_shadow_force(care)
	care.host.set_meta("vc27_shadow_force", _shadow_force)
	if _stage == "gap":
		if Engine.get_frames_drawn() <= _stop_drawn:
			return
		print("TRACE t=", snapped(_t, 0.01), " kind=shadow_gap mode=", _shadow_force, " rendered_after_end=true ", _frame_tag())
		if _shadow_force == "uncorrected":
			_begin_shadow_plate(care, true)
		else:
			_shadow_force = ""
			care.host.set_meta("vc27_shadow_force", "")
			roam.set_care_hold(false)
			_arm_route(care, "follow48", 48.0)
		return
	if _t < _mark + STOP_SEC:
		return
	var corrected := _shadow_force == "corrected"
	if not _live_shadow_ok(care, corrected):
		return
	if corrected:
		var feet: Dictionary = care.host.call("foot_anchor_state")
		if absf(float(feet.get("offset_y", -1.0)) - WalkClip.GROUNDED_OFFSET_Y) > 0.001:
			_fail("corrected shadow plate moved the foot offset")
			return
	elif absf(float(care.host.get_meta("vc27_draw_offset", -1.0)) - WalkClip.GROUNDED_OFFSET_Y) > 0.001:
		_fail("uncorrected plate did not restore the foot offset before the draw")
		return
	_stop_drawn = Engine.get_frames_drawn()
	_stage = "gap"
	var label := "corrected_visual_center" if corrected else "uncorrected_node_height"
	print("TRACE t=", snapped(_t, 0.01), " kind=shadow_end held_sec=", snapped(_t - _mark, 0.01), " mode=", label, " select_png_index=", _stop_drawn, " foot_offset_held=2 ", _shadow_line(care, corrected), " ", _frame_tag())


static func _ensure_shadow_force(care: Node) -> void:
	if care.host.get_node_or_null("ShadowForceZero") != null:
		return
	var script := load("res://gameplay/m1_shadow_force.gd")
	var early := Node.new()
	early.name = "ShadowForceZero"
	early.set_script(script)
	early.set("job", "zero")
	early.process_priority = -1000
	care.host.add_child(early)
	var late := Node.new()
	late.name = "ShadowForceRestore"
	late.set_script(script)
	late.set("job", "restore")
	late.process_priority = 100000
	care.host.add_child(late)


static func _shadow_line(care: Node, use_offset: bool) -> String:
	var pet := care.host.get("_pet") as Sprite3D
	var sh := care.host.get_node_or_null("PetShadow_v610") as MeshInstance3D
	if pet == null:
		return "shadow=missing"
	var L := Vector3(0.645, 0.0, 0.453) / 0.616
	var lift := pet.offset.y * pet.pixel_size if use_offset else 0.0
	var yc := pet.global_position.y + lift
	var origin := Vector3(pet.global_position.x, 0.25, pet.global_position.z) + L * yc
	var node_only := Vector3(pet.global_position.x, 0.25, pet.global_position.z) + L * pet.global_position.y
	var delta := origin - node_only
	var measured := sh.global_position if sh != null else Vector3.INF
	return "center_y=%.3f projection=(%.3f,%.3f,%.3f) delta_from_node_height=(%.3f,%.3f) delta_wu=%.3f measured=(%.3f,%.3f,%.3f) pixel_size=%.3f" % [
		yc, origin.x, origin.y, origin.z, delta.x, delta.z, Vector2(delta.x, delta.z).length(),
		measured.x, measured.y, measured.z, pet.pixel_size,
	]


static func _live_shadow_ok(care: Node, use_offset: bool) -> bool:
	var pet := care.host.get("_pet") as Sprite3D
	var sh := care.host.get_node_or_null("PetShadow_v610") as MeshInstance3D
	if pet == null or sh == null or not sh.visible:
		_fail("low fake shadow is not showing")
		return false
	var L := Vector3(0.645, 0.0, 0.453) / 0.616
	var lift := pet.offset.y * pet.pixel_size if use_offset else 0.0
	var yc := pet.global_position.y + lift
	var want := Vector3(pet.global_position.x, 0.25, pet.global_position.z) + L * yc
	if sh.global_position.distance_to(want) > 0.05:
		_fail("shadow origin %s wanted %s use_offset=%s frame=%s" % [sh.global_position, want, use_offset, Engine.get_process_frames()])
		return false
	return true


static func _arm_route(care: Node, leg: String, speed: float) -> void:
	var goal := _origin + _right * ROUTE_WU
	var roam = care.host.get("_roam")
	if not roam.segment_free(_origin, goal):
		_fail("route is no longer a free 24wu segment")
		return
	_leg_name = leg
	_phase = "leg"
	_expect = speed
	_goal = goal
	_phase0 = float(care.host.call("walk_clip_state").get("phase_wu", 0.0))
	_moved = 0.0
	_full = []
	_tracking = true
	_had_target = true
	_mark = _t
	roam.set_care_hold(false)
	roam.dest = null
	roam._stash = null
	roam._pause = 0.0
	roam._manual = false
	care.host.set("_walk_target", Vector3(goal.x, 0.0, goal.y))
	print("TRACE t=", snapped(_t, 0.01), " kind=leg_start leg=", leg, " dist_wu=", ROUTE_WU, " cycles=2 speed_const=", speed, " provenance=live_manual_walk_target ", _frame_tag())
	_log_sizes(care, "leg_start_" + leg)


static func _start_rate20(care: Node) -> void:
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
	_place_origin(care)
	# Roam stops when the remaining distance is within its existing ARRIVE.
	# Aim past the 24 wu mark by that radius so the walked distance still reaches two cycles.
	var arrive := float((load("res://gameplay/m1_roam.gd") as GDScript).get_script_constant_map()["ARRIVE"])
	var goal := _origin + _right * (ROUTE_WU + arrive)
	var roam = care.host.get("_roam")
	if not roam.segment_free(_origin, goal):
		_fail("side20 segment is not free for 24wu plus the existing arrival radius")
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
	_tracking = false
	_leg_name = "follow20"
	_mark = _t
	_phase = "rate20"
	print("TRACE t=", snapped(_t, 0.01), " kind=leg_start leg=follow20 dist_wu=", ROUTE_WU, " cycles=2 motion_before=", before, " motion_now=0 provenance=fixture_motion_axis_0_live_roam_tick isolated_profile_only ", _frame_tag())


static func _place_origin(care: Node) -> void:
	var pet: Node3D = care.host.get("_pet")
	pet.position = Vector3(_origin.x, pet.position.y, _origin.y)
	care.host.call("walk_clip_rebase")
	_pos = _origin
	_have = true
	print("TRACE t=", snapped(_t, 0.01), " kind=rebase_to_route_origin note=placement_is_not_a_step world=(", snapped(_origin.x, 0.1), ",", snapped(_origin.y, 0.1), ")")


static func _find_and_store_origin(care: Node) -> bool:
	var roam = care.host.get("_roam")
	var spots: Array[Vector2] = [_xz(care), Vector2(0, 55), Vector2(0, 70), Vector2(-60, 10), Vector2(-20, 60), Vector2(20, 60), Vector2(100, 20)]
	for spot in spots:
		var goal := spot + _right * ROUTE_WU
		if roam.segment_free(spot, goal):
			_origin = spot
			return true
	_fail("no straight 24wu side segment; not shortening the route")
	return false


static func _arm_panorama_from_search(care: Node) -> void:
	if not _find_and_store_origin(care):
		return
	if _xz(care).distance_to(_origin) > 0.05:
		_place_origin(care)
	_arm_route(care, "panorama48", 48.0)


static func _visible(care: Node) -> bool:
	var cam: Camera3D = care.host.get("_camera") as Camera3D
	var pet: Node3D = care.host.get("_pet") as Node3D
	if cam == null or pet == null:
		_fail("missing camera or pet for visibility")
		return false
	var vp: Vector2 = care.call("_viewport_size")
	var head := pet.global_position + Vector3(0, 27, 0)
	var ground := Vector3(pet.global_position.x, 0.0, pet.global_position.z)
	var anchor: Dictionary = care.host.call("foot_anchor_state")
	var sole := Vector3(pet.global_position.x, float(anchor.get("sole_boundary_y", 0.0)), pet.global_position.z)
	if not _point_in(cam, vp, head) or not _point_in(cam, vp, ground) or not _point_in(cam, vp, sole):
		_fail("head or feet left the visible rect during " + _leg_name)
		return false
	var bubble: CanvasItem = care.get("_bubble") as CanvasItem
	if bubble == null or not bubble.visible:
		_fail("need bubble was not visible during " + _leg_name)
		return false
	var bp: Vector2 = bubble.position
	var bs: Vector2 = bubble.size
	if bp.x < 0.0 or bp.y < 0.0 or bp.x + bs.x > vp.x or bp.y + bs.y > vp.y:
		_fail("bubble rect left the visible rect during " + _leg_name)
		return false
	if not bool(care.call("bubble_fits_at", Vector2(pet.global_position.x, pet.global_position.z))):
		_fail("bubble_fits_at rejected the live pet during " + _leg_name)
		return false
	return true


static func _point_in(cam: Camera3D, vp: Vector2, world: Vector3) -> bool:
	if cam.is_position_behind(world):
		return false
	var sp := cam.unproject_position(world)
	return sp.x >= 0.0 and sp.y >= 0.0 and sp.x <= vp.x and sp.y <= vp.y


static func _judge_movie_close(care: Node, st: Dictionary) -> bool:
	var render := _render_size(care)
	var visible: Vector2 = care.call("_viewport_size")
	var frac := float(st.get("frac", 0.0))
	var box_on_render := _box_px(care)
	var movie := Engine.get_write_movie_path()
	_log_sizes(care, "movie_judge")
	print("TRACE t=", snapped(_t, 0.01), " kind=movie_judge render=", render, " visible=", visible, " unproject_box_px=", snapped(box_on_render, 1.0), " frac_on_visible=", snapped(frac, 0.001), " settled=", bool(st.get("settled", false)), " movie=", movie)
	if movie == "":
		print("TRACE kind=movie_close skipped_not_movie render=", render, " visible=", visible, " note=window_or_visible_fraction_is_not_movie_close")
		return true
	if render.x != MOVIE_W or render.y != MOVIE_H:
		_fail("movie render texture is %s x %s, not %s x %s; a clamped window fraction is not movie close" % [render.x, render.y, MOVIE_W, MOVIE_H])
		return false
	var need_px := 0.20 * float(MOVIE_H)
	if box_on_render + 1.5 < need_px:
		_fail("movie pet box is %s px on the %s render, under 0.20 of that height" % [box_on_render, MOVIE_H])
		return false
	print("TRACE kind=movie_close PASS render=", render, " unproject_box_px=", snapped(box_on_render, 1.0), " need_px=", snapped(need_px, 1.0), " basis=viewport_texture_not_window")
	return true


static func _box_px(care: Node) -> float:
	var cam: Camera3D = care.host.get("_camera") as Camera3D
	var pet: Node3D = care.host.get("_pet") as Node3D
	if cam == null or pet == null:
		return 0.0
	var mid := pet.global_position
	var top := cam.unproject_position(mid + Vector3(0, 27, 0))
	var bot := cam.unproject_position(mid + Vector3(0, -27, 0))
	return absf(bot.y - top.y)


static func _render_size(care: Node) -> Vector2i:
	var vp := care.get_viewport()
	if vp == null:
		return Vector2i.ZERO
	var tex := vp.get_texture()
	if tex == null:
		return Vector2i.ZERO
	return tex.get_size()


static func _log_sizes(care: Node, tag: String) -> void:
	var visible: Vector2 = care.call("_viewport_size")
	var win := DisplayServer.window_get_size()
	var screen := DisplayServer.screen_get_size()
	var render := _render_size(care)
	var req_w := int(ProjectSettings.get_setting("display/window/size/viewport_width"))
	var req_h := int(ProjectSettings.get_setting("display/window/size/viewport_height"))
	var stretch := str(ProjectSettings.get_setting("display/window/stretch/mode"))
	var clamped := win.y + 8 < req_h
	print("TRACE t=", snapped(_t, 0.01), " kind=size tag=", tag, " requested=", req_w, "x", req_h, " window=", win, " visible=", visible, " render_texture=", render, " screen=", screen, " stretch=", stretch, " window_clamped=", clamped, " movie=", Engine.get_write_movie_path(), " ", _frame_tag())


static func _frame_tag() -> String:
	var drawn := Engine.get_frames_drawn()
	var proc := Engine.get_process_frames()
	return "frames_drawn=%s process_frames=%s png_index=%s title_frame=%s draw_matches_process=%s" % [drawn, proc, drawn, drawn + 1, drawn == proc or drawn + 1 == proc]


static func _keep_bubble(care: Node) -> void:
	var fade = care.get("fade")
	if fade and fade.has_method("note_input"):
		fade.call("note_input")
	var tree := Engine.get_main_loop()
	if tree == null:
		return
	var sim: Node = tree.root.get_node_or_null("Sim")
	if sim == null:
		return
	var state: Dictionary = sim.get("state")
	var needs: Dictionary = state.get("needs", {})
	needs["hunger"] = 100.0 - _threshold
	state["needs"] = needs
	sim.set("state", state)


static func _want_threshold() -> float:
	var tree := Engine.get_main_loop()
	if tree == null:
		return 70.0
	var gd: Node = tree.root.get_node_or_null("GameData")
	if gd == null:
		return 70.0
	var m1a: Dictionary = gd.get("m1a")
	var bubbles: Dictionary = m1a.get("bubbles", {})
	return float(bubbles.get("want_threshold", 70.0))


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
	if absf(off.x) > 0.001 or (absf(off.y) > 0.001 and absf(off.y - WalkClip.GROUNDED_OFFSET_Y) > 0.001):
		_fail("sprite offset is not the old plate or the grounded sole anchor")
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
