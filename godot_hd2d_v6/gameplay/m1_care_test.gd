extends SceneTree
## Headless checks for the vc27 observation + care slice.
## Does not render the garden and does not claim frame rate or visual parity.

const Policy := preload("res://gameplay/m1_camera_policy.gd")
const Rules := preload("res://gameplay/m1_input_rules.gd")
const Gesture := preload("res://gameplay/m1_gesture.gd")
const Fade := preload("res://gameplay/m1_ui_fade.gd")
const Layout := preload("res://gameplay/m1_ui_layout.gd")
const Profile := preload("res://gameplay/m1_profile_run.gd")
const Roam := preload("res://gameplay/m1_roam.gd")
const WalkClip := preload("res://gameplay/m1_walk_clip.gd")

var fails := 0


func _init() -> void:
	process_frame.connect(_run, CONNECT_ONE_SHOT)


func _run() -> void:
	_test_camera()
	_test_rules()
	_test_gesture()
	_test_fade()
	_test_care_and_save()
	_test_ui_r1()
	_test_roam()
	_test_poop_marker()
	_test_walk_clip()
	if fails == 0:
		print("m1_care_test PASS")
		quit(0)
	else:
		print("m1_care_test FAIL ", fails)
		quit(1)


func _ok(cond: bool, name: String) -> void:
	if cond:
		print("PASS ", name)
	else:
		fails += 1
		print("FAIL ", name)


func _test_camera() -> void:
	var base := Vector3(1, 50, 3)
	var origin := Vector3(0, 0, 0)
	var pet := Vector3(10, 99, -4)
	var followed := Policy.desired(base, origin, pet, false)
	var again := Policy.desired(base, origin, pet, false)
	var wide := Policy.desired(base, origin, pet, true)
	_ok(followed == Vector3(11, 50, -1), "follow is xz offset only")
	_ok(followed == again, "idle follow stays put")
	_ok(Policy.keeps_height(base, followed), "follow keeps camera height")
	_ok(wide == base, "overview returns to opening camera")
	_ok(wide.y == base.y and followed.y == base.y, "no vertical sway")
	var opening := Vector3(12.0, 193.0, 207.82685902179844)
	var scale := Policy.zoom_scale(0.083, 0.20)
	_ok(is_equal_approx(scale, 0.083 / 0.20), "follow zoom is the measured fraction over the m1a minimum")
	var pet_w := Vector3(0, 29, 0)
	var zoomed := Policy.zoomed_along(opening, pet_w, scale)
	var again_z := Policy.zoomed_along(opening, pet_w, scale)
	_ok(zoomed == again_z, "follow zoom does not sway")
	_ok(opening.distance_to(pet_w) > zoomed.distance_to(pet_w), "follow zoom moves closer along the opening axis")
	var dir_far := (opening - pet_w).normalized()
	var dir_near := (zoomed - pet_w).normalized()
	_ok(dir_far.distance_to(dir_near) < 0.001, "follow zoom keeps the opening view direction")
	_ok(is_equal_approx(Policy.zoom_scale(0.25, 0.20), 1.0), "follow does not zoom once the pet is already large enough")
	_ok(is_equal_approx(Policy.zoom_scale(0.083, 0.0), 1.0), "a missing follow minimum does not move the camera")
	_ok(not Policy.accept_follow(0.199, 0.20), "0.199 does not pass the 0.20 line")
	_ok(Policy.accept_follow(0.20, 0.20), "0.20 passes the 0.20 line")
	var look := Vector3(12, 58, -26)
	var narrow := Vector2(540, 1140)
	var tall := Vector2(1080, 2280)
	var opening_n := Policy.portrait_box_fraction(opening, opening, look, pet_w, narrow, 50.0, 54.0)
	var opening_t := Policy.portrait_box_fraction(opening, opening, look, pet_w, tall, 50.0, 54.0)
	_ok(opening_n > 0.083 and opening_n < 0.084, "540x1140 opening box stays at the approved panorama")
	_ok(is_equal_approx(opening_n, opening_t), "1080x2280 is the same 19:9 fraction as 540x1140")
	var scale_n := Policy.zoom_scale(opening_n, 0.20)
	var zoomed_n := Policy.zoomed_along(opening, pet_w, scale_n)
	var settled_n := Policy.portrait_box_fraction(zoomed_n, opening, look, pet_w, narrow, 50.0, 54.0)
	var settled_t := Policy.portrait_box_fraction(zoomed_n, opening, look, pet_w, tall, 50.0, 54.0)
	_ok(settled_n >= 0.20 and settled_t >= 0.20, "settled follow box is at least 0.20 on both 19:9 viewports")
	var early := Policy.approached(opening, zoomed_n, 2.0, 1.2)
	var early_f := Policy.portrait_box_fraction(early, opening, look, pet_w, narrow, 50.0, 54.0)
	var late := Policy.approached(opening, zoomed_n, 2.0, 6.0)
	var late_f := Policy.portrait_box_fraction(late, opening, look, pet_w, narrow, 50.0, 54.0)
	_ok(early_f < 0.20 and late_f >= 0.20, "an in-flight sample can sit under 0.20 while the settled camera does not")
	_ok(Policy.desired(base, origin, pet, true) == base, "overview is never the zoomed camera")


func _test_rules() -> void:
	_ok(Rules.action("tap", true, false, 2, 1) == "follow", "tap pet follows")
	_ok(Rules.action("tap", false, false, 2, 1) == "overview", "tap empty leaves follow")
	_ok(Rules.action("tap", false, true, 2, 1) == "walk", "tap empty in overview walks")
	_ok(Rules.action("swipe", false, false, 2, 1) == "ignore", "swipe with one pet does not walk")
	_ok(Rules.action("swipe", false, false, 2, 2) == "cycle", "swipe cycles when several pets")
	_ok(Rules.action("long", false, false, 2, 1) == "clean_all", "long press cleans when poop exists")
	_ok(Rules.action("long", false, true, 0, 1) == "ignore", "long press without poop does nothing")
	_ok(Rules.action("long", true, false, 2, 1) == "follow", "long press on pet does not clean")
	_ok(Rules.LONG_PRESS_SEC > 0.0 and Rules.SWIPE_PX > 0.0, "gesture thresholds are set")


func _test_gesture() -> void:
	var g: RefCounted = Gesture.new()
	g.down(Vector2.ZERO)
	_ok(g.move(Vector2(Rules.SWIPE_PX + 4.0, 0)) == "swipe", "drag past threshold is a swipe")
	_ok(g.up(Vector2(Rules.SWIPE_PX + 4.0, 0)) == "", "swipe release is not a tap")
	g.down(Vector2.ZERO)
	_ok(g.up(Vector2(4, 2)) == "tap", "short press is a tap")
	g.down(Vector2.ZERO)
	_ok(g.tick(0.2) == "", "hold under the threshold is not a long press")
	_ok(g.tick(Rules.LONG_PRESS_SEC) == "long", "hold reaches the long press")
	_ok(g.up(Vector2(2, 0)) == "", "long press release is not a tap")
	g.down(Vector2(10, 10))
	g.move(Vector2(10 + Rules.SWIPE_PX, 12))
	_ok(g.tick(1.0) == "", "a swipe is not also a long press")


func _gd(node_name: String) -> Node:
	return get_root().get_node(node_name)


func _test_fade() -> void:
	var f: RefCounted = Fade.new()
	var m1a: Dictionary = _gd("GameData").get("m1a")
	f.fade_sec = float(m1a.get("observe_ui_fade_sec", -1))
	_ok(is_equal_approx(f.fade_sec, 3.0), "fade uses m1a 3s")
	f.tick(2.9)
	_ok(is_equal_approx(f.alpha, 1.0), "ui stays up before 3s")
	f.tick(0.2)
	_ok(f.alpha < 1.0, "ui starts fading after 3s")
	f.note_input()
	_ok(is_equal_approx(f.alpha, 1.0), "pointer restores faded ui")
	f.toggle_appreciate()
	_ok(f.appreciate and is_equal_approx(f.alpha, 0.0), "appreciate hides ui")
	f.tick(4.0)
	_ok(is_equal_approx(f.alpha, 0.0), "appreciate stays hidden")
	f.note_input()
	_ok(is_equal_approx(f.alpha, 0.0), "pointer does not cancel appreciate")
	f.toggle_appreciate()
	_ok((not f.appreciate) and is_equal_approx(f.alpha, 1.0), "appreciate toggles back")


func _test_care_and_save() -> void:
	var sim := _gd("Sim")
	var clock := _gd("TimeService")
	var saves := _gd("SaveSystem")
	_ok(is_equal_approx(float(sim.get("RINSE")), 50.0), "rinse value is loaded")
	_ok(is_equal_approx(float(sim.get("PLAY_TEASE")), 15.0), "play tease value is loaded")
	sim.set("state", sim.call("new_state", clock.call("now_ms"), 7))
	var state: Dictionary = sim.get("state")
	state["stage"] = "sprout"
	var needs: Dictionary = state.get("needs", {})
	needs["hunger"] = 40.0
	needs["mood"] = 10.0
	needs["clean"] = 55.0
	state["needs"] = needs
	sim.set("state", state)
	var before_clean := 55.0
	var fed: Dictionary = sim.call("feed", "meal")
	_ok(bool(fed.get("ok", false)), "feed meal succeeds")
	var after: Dictionary = (sim.get("state") as Dictionary).get("needs", {})
	_ok(is_equal_approx(float(after.get("hunger", -1)), 80.0), "feed adds meal amount")
	_ok(is_equal_approx(float(after.get("clean", -1)), before_clean), "feed does not apply rinse")
	var patted: Dictionary = sim.call("pat")
	_ok(bool(patted.get("ok", false)), "pat succeeds")
	after = (sim.get("state") as Dictionary).get("needs", {})
	_ok(float(after.get("mood", 0)) > 10.0, "pat raises mood")
	sim.call("add_poop")
	sim.call("add_poop")
	var one: bool = sim.call("clean_one")
	_ok(one and int((sim.get("state") as Dictionary).get("poops", -1)) == 1, "clean one removes a single poop")
	var all: Dictionary = sim.call("clean_all")
	_ok(bool(all.get("ok", false)) and int(all.get("count", 0)) == 1, "clean all clears the rest")
	_ok(int((sim.get("state") as Dictionary).get("poops", -1)) == 0, "no poops remain")
	var empty: Dictionary = sim.call("clean_all")
	_ok(not bool(empty.get("ok", true)), "clean all with no poop does not succeed")
	saves.call("save_state", sim.get("state"))
	var loaded: Dictionary = saves.call("load_state")
	var loaded_needs: Dictionary = loaded.get("needs", {})
	_ok(is_equal_approx(float(loaded_needs.get("hunger", -1)), float(after.get("hunger", -2))), "save keeps hunger")
	_ok(int(loaded.get("poops", -1)) == 0, "save keeps poop count")
	_ok(str(loaded.get("stage", "")) == "sprout", "save keeps stage")


func _test_ui_r1() -> void:
	var s540 := Layout.layout_scale(540)
	var s1080 := Layout.layout_scale(1080)
	_ok(s540 == 1 and s1080 == 2, "layout scale follows viewport width")
	_ok(Layout.tex_mul(s540) == 2 and Layout.tex_mul(s1080) == 4, "nearest multiples are 2x and 4x")
	_ok(Layout.button_display(s540) == 80 and Layout.button_touch(s540) == 96, "540 shows 80 and touches 96")
	_ok(Layout.button_display(s1080) == 160 and Layout.button_touch(s1080) == 192, "1080 shows 160 and touches 192")
	_ok(Layout.bubble_display(s540) == 96 and Layout.bubble_display(s1080) == 192, "need bubble display is 96 and 192")
	var row540: Dictionary = Layout.care_row(Vector2(540, 1140), s540)
	var slot0: Dictionary = (row540["slots"] as Array)[0]
	_ok((slot0["display"] as Vector2).is_equal_approx(Vector2(98, 1032)), "540 care row starts at the spec point")
	var row1080: Dictionary = Layout.care_row(Vector2(1080, 1920), s1080)
	var y1080 := float(( (row1080["slots"] as Array)[0]["display"] as Vector2).y)
	_ok(y1080 >= 0.0 and y1080 + 160.0 <= 1920.0, "1080 care row stays inside the window")
	var admire: Dictionary = Layout.admire_slot(Vector2(540, 1140), 1)
	_ok((admire["display"] as Vector2).is_equal_approx(Vector2(436, 28)), "admire sits at the spec corner")
	_ok(Layout.effect("pat") == "pat" and Layout.effect("water") == "none", "palm is pat and water has no effect")
	_ok(Layout.effect("poop") == "clean_one" and Layout.effect("feed") == "feed", "poop cleans one and feed stays feed")
	_ok(Layout.blocks_ground(true, 1.0), "visible controls block the ground")
	_ok(not Layout.blocks_ground(true, 0.0), "fully faded controls do not block")
	_ok(_png_size("res://gameplay/ui_r1/assets/icons/icon_care_pat_32.png") == Vector2i(32, 32), "pat icon is 32")
	_ok(_png_size("res://gameplay/ui_r1/assets/buttons/btn_care_water_disabled.png") == Vector2i(40, 40), "water button is 40")
	_ok(_png_size("res://gameplay/ui_r1/assets/bubbles/bubble_need_eat.png") == Vector2i(48, 48), "need bubble is 48")
	_ok(not FileAccess.file_exists("res://gameplay/ui_r1/assets/buttons/btn_care_play_normal.png"), "no play care button")
	_ok(_sha("res://gameplay/ui_r1/assets/icons/icon_care_pat_32.png") == "d5c5a9c12b93c9ea738c806a41b3930ae6f10eff8a2cbe7a54c3427e96f32831", "pat icon hash matches the pack")
	_ok(not Layout.debug_chrome_visible(false), "debug chrome stays hidden until developer mode")
	_ok(Layout.debug_chrome_visible(true), "debug chrome shows in developer mode")
	var head := Vector2(200, 400)
	var moved := head + Vector2(30, -12)
	var a := Layout.bubble_top_left(head, 96)
	var b := Layout.bubble_top_left(moved, 96)
	_ok(b - a == moved - head, "bubble keeps the pet's screen delta with no extra drift")
	_ok(is_equal_approx(a.x + 48.0, head.x) and is_equal_approx(a.y + 96.0, head.y), "bubble is centered on the head with no sideways bias")
	_ok(Layout.bubble_shown(true, false, 1.0), "need bubble shows while the panel is up")
	_ok(not Layout.bubble_shown(true, true, 1.0), "appreciate hides the need bubble")
	_ok(not Layout.bubble_shown(true, false, 0.0), "full fade hides the need bubble")
	_test_restore_prediction()


func _test_restore_prediction() -> void:
	var saved := {
		"stage": "sprout",
		"poops": 0,
		"last_seen": 1710000000000,
		"last_save_time": 1710000000000,
		"needs": {"hunger": 80.0, "mood": 70.0, "clean": 90.0, "energy": 100.0},
	}
	var same: Dictionary = Profile.predict_reload(saved, 1710000000000 + 500)
	var same_needs: Dictionary = same.get("needs", {})
	_ok(is_equal_approx(float(same_needs.get("hunger", -1)), 80.0) and int(same.get("poops", -1)) == 0, "reload inside 2s stall keeps hunger and poops")
	var later: Dictionary = Profile.predict_reload(saved, 1710000000000 + 10000)
	var later_needs: Dictionary = later.get("needs", {})
	_ok(float(later_needs.get("hunger", 80)) < 80.0, "reload after the stall applies ordinary hunger decay")
	_ok(int(later.get("poops", -1)) == 0, "that same decay does not invent or remove poops")
	_ok(Layout.effect("water") == "none", "water still has no care effect")
	_ok(Layout.CARE_IDS[2] == "poop" and Layout.CARE_IDS[1] == "water", "poop and water keep their button slots")
	_test_profile_guard()


func _test_profile_guard() -> void:
	_ok(Layout.profile_allowed("", "/home/default", ""), "ordinary play may use the default save")
	_ok(not Layout.profile_allowed("visual", "/home/.local/share/godot/app_userdata/pilot", ""), "visual without a profile name is refused")
	_ok(not Layout.profile_allowed("seed", "/home/.local/share/godot/app_userdata/pilot", "vc27_care_restore_9"), "seed does not accept the default save dir")
	_ok(not Layout.profile_allowed("verify", "/home/.local/share/godot/app_userdata/pilot", "vc27_care_restore_9"), "verify does not accept the default save dir")
	_ok(Layout.profile_allowed("visual", "/home/.local/share/vc27_care_restore_9", "vc27_care_restore_9"), "visual accepts its isolated profile")
	_ok(not Layout.profile_allowed("walkclip", "/home/.local/share/godot/app_userdata/pilot", ""), "walk clip trace without a profile name is refused")
	_ok(not Layout.profile_allowed("walkclip", "/home/.local/share/godot/app_userdata/pilot", "vc27_walkclip_1"), "walk clip trace does not accept the default save dir")
	_ok(Layout.profile_allowed("walkclip", "/home/.local/share/vc27_walkclip_1", "vc27_walkclip_1"), "walk clip trace accepts its isolated profile")
	var hunger := Layout.hunger_for_need_bubble(70.0)
	_ok(is_equal_approx(hunger, 30.0), "bubble hunger is 100 minus the existing threshold")
	_ok(100.0 - hunger >= 70.0, "that hunger still asks for food")
	_ok(100.0 - (hunger + 40.0) < 70.0, "one existing meal drops the ask below the bubble line")
	_ok(hunger < 90.0, "that hunger is still under the existing refuse line")


func _test_roam() -> void:
	var agent = Roam.new()
	agent.boot()
	_ok(agent.garden_blocked(Vector2(80, -70)), "cottage footprint blocks a roam step")
	_ok(agent.garden_blocked(Vector2(30, -20)), "a prop footprint blocks a roam step")
	_ok(not agent.inside_walk(Vector2(-130, -100)), "back-left tree corner stays outside walk bounds")
	_ok(agent.garden_free(Vector2.ZERO), "the pet spawn stays walkable")
	var near_max := 0.0
	var far_hit := false
	var bad_path := 0
	for s in 40:
		agent.seed(1000 + s)
		var near: Vector2 = agent.choose_dest(Vector2.ZERO, 0)
		var far: Vector2 = agent.choose_dest(Vector2.ZERO, -5)
		near_max = maxf(near_max, near.length())
		if far.length() > 70.0:
			far_hit = true
		if not agent.segment_free(Vector2.ZERO, near) or not agent.segment_free(Vector2.ZERO, far):
			bad_path += 1
	_ok(bad_path == 0, "roam picks stay on a free path")
	_ok(near_max <= 70.01, "ordinary roam stays inside the nearby pick radius")
	_ok(far_hit, "a low social axis may pick the farther roam radius")
	agent.seed(7)
	agent.dest = Vector2(0, 80)
	agent._pause = 0.0
	agent._manual = false
	var stepped: Vector2 = agent.tick(Vector2.ZERO, 1.0, 1.0, 0)
	_ok(is_equal_approx(stepped.y, 20.0) and is_equal_approx(stepped.x, 0.0), "autonomous speed is the existing walker speed")
	_ok(agent.cause == "autonomous" and agent.motion == "walk", "that step is logged as autonomous walking")
	agent.dest = Vector2(80, -70)
	agent._pause = 0.0
	var blocked_from := Vector2(50, -39)
	var held: Vector2 = agent.tick(blocked_from, 1.0, 1.0, 0)
	_ok(held.distance_to(blocked_from) < 0.01 and not agent.garden_blocked(held), "a blocked step does not enter the cottage")
	agent.dest = Vector2(0, 40)
	agent.begin_manual()
	var during: Vector2 = agent.tick(Vector2(5, 5), 0.5, 1.0, 0)
	_ok(during == Vector2(5, 5) and agent.cause == "tap_directed", "a manual target takes precedence")
	agent.notify_manual_done()
	_ok(agent.cause == "autonomous" and agent.dest == Vector2(0, 40), "the agent target resumes after the manual target")
	agent.seed(3)
	agent.dest = null
	agent._pause = 1.2
	var idle_at := Vector2(3, 4)
	var idled: Vector2 = agent.tick(idle_at, 0.4, 1.0, 0)
	_ok(idled == idle_at and agent.motion == "idle", "the idle pause does not move the pet")
	var armed: Vector2 = agent.tick(idle_at, 1.0, 1.0, 0)
	_ok(armed == idle_at and agent.dest != null, "the idle pause arms the next roam target")
	var resumed: Vector2 = agent.tick(armed, 0.5, 1.0, 0)
	_ok(agent.motion == "walk" and resumed.distance_to(idle_at) > 0.5, "roam resumes after the idle pause")
	var kept = agent.dest
	agent.set_care_hold(true)
	var frozen: Vector2 = agent.tick(resumed, 0.5, 1.0, 0)
	_ok(frozen == resumed and agent.dest == kept and agent.motion == "hold", "care pauses without clearing the target")
	agent.note_camera()
	_ok(agent.dest == kept and agent.cause == "autonomous", "observe and follow do not clear the agent target")
	var raw: Vector2 = agent.far_free(Vector2(0, 75))
	_ok(raw.x < -80.0, "the farthest clear spot from the front lawn is the left edge")
	var open: Vector2 = agent.far_visible(Vector2(0, 75), func(p: Vector2) -> bool: return p.x > -80.0)
	_ok(open.x > -80.0, "a trace walk goal can reject the off-screen left spot")
	agent.set_care_hold(false)


func _test_poop_marker() -> void:
	var cap = load("res://scenes/capture.gd")
	var box := float(cap.get_script_constant_map()["PET_VISIBLE_H"])
	var icon := _png_size("res://gameplay/ui_r1/assets/icons/icon_care_poop_32.png")
	var marker: Dictionary = Layout.poop_marker(box, float(icon.y))
	var old_height := 2.0 * float(icon.y)
	var old_center := 8.0
	_ok(is_equal_approx(box, 54.0), "poop marker uses the existing 54-unit pet box")
	_ok(icon == Vector2i(32, 32), "poop icon file stays 32 pixels")
	_ok(is_equal_approx(float(marker["height"]), box / 4.0), "marker height is a quarter of the pet box")
	_ok(float(marker["height"]) < old_height, "marker is shorter than the old pixel_size 2 quad")
	_ok(is_equal_approx(float(marker["pixel_size"]) * float(icon.y), float(marker["height"])), "pixel size times the icon height is the world height")
	_ok(is_equal_approx(float(marker["bottom_y"]), 0.0), "marker feet sit on the ground")
	_ok(is_equal_approx(float(marker["center_y"]), float(marker["height"]) * 0.5), "centered sprite is raised by half its height")
	_ok(float(marker["top_y"]) < box * 0.5, "marker top stays below the pet center, not across the face")
	_ok(old_center - old_height * 0.5 < 0.0, "the old marker center at y 8 put its feet underground")
	_ok(Layout.button_touch(1) == 96, "poop button touch pad stays 96")
	_ok(Rules.action("long", false, false, 2, 1) == "clean_all", "long press still cleans from the ground")
	_ok(Rules.action("tap", false, true, 2, 1) == "walk", "a ground tap is still a walk, not a shrunken poop pick")


func _test_walk_clip() -> void:
	var right := Vector2(1, 0)
	var away := Vector2(0, -1)
	var clip = WalkClip.new()
	_ok(not clip.moving and clip.facing == "front" and not clip.flip_h, "walk starts on the front idle")
	_ok(clip.texture_path().ends_with("front_idle_01.png"), "the opening frame is the front idle file")
	clip.advance(Vector2.ZERO, right, away)
	_ok(not clip.moving and is_equal_approx(clip.phase_wu, 0.0), "a zero step does not start the cycle")
	clip.advance(Vector2(4, 0), right, away)
	_ok(clip.moving and clip.facing == "side" and not clip.flip_h, "screen-right motion uses the right-facing side sheet")
	_ok(clip.frame_index() == 2 and clip.texture_path().ends_with("side_walk_03.png"), "4 wu is the third side frame")
	clip.advance(Vector2.ZERO, right, away)
	_ok(not clip.moving and clip.facing == "side" and not clip.flip_h, "stopping keeps the side facing")
	_ok(clip.texture_path().ends_with("side_idle_01.png") and clip.texture_path().find("front_idle") < 0, "a stopped side uses side idle, not the front idle")
	_ok(is_equal_approx(clip.phase_wu, 4.0), "the stop keeps the distance already walked")
	var phase_held: float = clip.phase_wu
	for _i in 4:
		clip.advance(Vector2.ZERO, right, away)
	_ok(is_equal_approx(clip.phase_wu, phase_held) and not clip.moving, "repeated zero steps do not fake a walk")
	clip.advance(Vector2(-2, 0), right, away)
	_ok(clip.facing == "side" and clip.flip_h and clip.frame_index() == 3, "screen-left flips the side sheet and continues the phase")
	clip.advance(Vector2.ZERO, right, away)
	_ok(clip.flip_h and clip.texture_path().ends_with("side_idle_01.png"), "a stopped left side keeps the flip and the side idle")
	clip.advance(Vector2(0, -4), right, away)
	_ok(clip.facing == "back" and not clip.flip_h and clip.moving, "motion away from the camera uses the back sheet")
	_ok(not bool(clip.state().get("z_lock", true)), "back does not claim a Z foot lock")
	clip.advance(Vector2.ZERO, right, away)
	_ok(clip.texture_path().ends_with("back_idle_01.png") and not clip.flip_h, "a stop facing away uses the back idle")
	clip.advance(Vector2(0, 4), right, away)
	_ok(clip.facing == "front" and not clip.flip_h, "motion toward the camera uses the front sheet")
	var kept: String = clip.facing
	clip.advance(Vector2(3, -3), right, away)
	_ok(clip.facing == kept, "an equal diagonal keeps the facing already on screen")
	var slow = WalkClip.new()
	for _i in 6:
		slow.advance(Vector2(20.0 * 0.1, 0), right, away)
	_ok(slow.moving and is_equal_approx(slow.phase_wu, 12.0) and slow.frame_index() == 0, "20 wu/s for 0.6s is one 12 wu cycle")
	var fast = WalkClip.new()
	fast.advance(Vector2(48.0 * 0.25, 0), right, away)
	_ok(fast.moving and is_equal_approx(fast.phase_wu, 12.0) and fast.frame_index() == 0, "48 wu/s for 0.25s is the same 12 wu cycle")
	var stepped = WalkClip.new()
	stepped.advance(Vector2(48.0 / 48.0, 0), right, away)
	_ok(stepped.frame_index() == 0 and stepped.texture_path().ends_with("side_walk_01.png"), "1 wu at 48 still shows the first frame")
	stepped.advance(Vector2(48.0 / 48.0, 0), right, away)
	_ok(stepped.frame_index() == 1, "the second wu advances one frame at either speed")
	var mid = WalkClip.new()
	mid.advance(Vector2(10, 0), right, away)
	_ok(mid.frame_index() == 5 and mid.texture_path().ends_with("side_walk_06.png"), "10 wu is the sixth frame")
	mid.advance(Vector2.ZERO, right, away)
	_ok(mid.texture_path().ends_with("side_idle_01.png") and is_equal_approx(mid.phase_wu, 10.0), "stopping mid-cycle snaps to contact idle and keeps the phase")
	mid.advance(Vector2(2, 0), right, away)
	_ok(mid.frame_index() == 0 and is_equal_approx(mid.phase_wu, 12.0), "resume continues from the achieved distance")
	var agent = Roam.new()
	agent.boot()
	agent.dest = Vector2(80, -70)
	agent._pause = 0.0
	agent._manual = false
	var edge := Vector2(80, -39.999)
	var blocked: Vector2 = agent.tick(edge, 0.05, 1.0, 0)
	var blocked_clip = WalkClip.new()
	blocked_clip.advance(Vector2(6, 0), right, away)
	var blocked_phase: float = blocked_clip.phase_wu
	blocked_clip.advance(blocked - edge, right, away)
	_ok(blocked.distance_to(edge) < 0.0001 and agent.motion == "idle", "a roam step into the cottage does not move")
	_ok(not blocked_clip.moving and is_equal_approx(blocked_clip.phase_wu, blocked_phase), "that blocked step does not advance the clip")
	_ok(blocked_clip.texture_path().ends_with("side_idle_01.png"), "the blocked pet stays on the side idle")
	agent.dest = Vector2(0, 40)
	agent._pause = 0.0
	agent.set_care_hold(true)
	var held_from := Vector2(5, 5)
	var held: Vector2 = agent.tick(held_from, 0.5, 1.0, 0)
	blocked_clip.advance(held - held_from, right, away)
	_ok(held == held_from and agent.motion == "hold" and not blocked_clip.moving, "care hold is zero distance and stays idle")
	agent.set_care_hold(false)
	var again: Vector2 = agent.tick(held, 0.5, 1.0, 0)
	var before_resume: float = blocked_clip.phase_wu
	blocked_clip.advance(again - held, right, away)
	_ok(agent.motion == "walk" and blocked_clip.moving and blocked_clip.phase_wu > before_resume + 0.5, "resume after hold walks the achieved step")
	var cap = load("res://scenes/capture.gd")
	var roam_script = load("res://gameplay/m1_roam.gd")
	_ok(is_equal_approx(float(cap.get_script_constant_map()["WALK_SPEED"]), 48.0), "the live manual speed constant is still 48")
	_ok(is_equal_approx(float(cap.get_script_constant_map()["PET_CENTER_Y"]), 29.0), "the pet center stays at y 29")
	_ok(is_equal_approx(float(roam_script.get_script_constant_map()["SPEED"]), 20.0), "the autonomous base speed is still 20")
	var paths := WalkClip.frame_paths()
	_ok(paths.size() == 21, "the candidate is 21 separate frames")
	var seen := {}
	var atlas := false
	for p in paths:
		seen[p] = true
		if str(p).find("atlas") >= 0:
			atlas = true
	_ok(seen.size() == 21 and not atlas, "each frame is its own file and none is an atlas")
	var want := {
		"pet_tuanrong_radiant_back_idle_01.png": "fe626c694503d9e2f0d4af55090523c62f9ac4ddd4db199b76d6af954d2078a0",
		"pet_tuanrong_radiant_back_walk_01.png": "fe626c694503d9e2f0d4af55090523c62f9ac4ddd4db199b76d6af954d2078a0",
		"pet_tuanrong_radiant_back_walk_02.png": "414025c9d21650125262243b8e661fc6f11a1f646f1b1924999d46cd4c561554",
		"pet_tuanrong_radiant_back_walk_03.png": "912a06b22f72363dcb8d3156eef39f2db7c64ce0afba5b313d18115a5878d73a",
		"pet_tuanrong_radiant_back_walk_04.png": "ba51820f70713ec6b4db45dc2efa7199acc95f2304bdcc1865c72d9096a548d0",
		"pet_tuanrong_radiant_back_walk_05.png": "40d808787eb9c6b47a122d5a0b080d3901615d1cef337b6d7f5a44212a6ffdfa",
		"pet_tuanrong_radiant_back_walk_06.png": "7e1ef85f6fa2200b5a8cd2d9562655bf2d648500e5170d713e5030b7b7865475",
		"pet_tuanrong_radiant_front_idle_01.png": "f2bceb847ea214c58301f841a4bcc1ce4065e07264696b7c7e6084bbea3762d1",
		"pet_tuanrong_radiant_front_walk_01.png": "f2bceb847ea214c58301f841a4bcc1ce4065e07264696b7c7e6084bbea3762d1",
		"pet_tuanrong_radiant_front_walk_02.png": "eb10ced72591075f9fbddf5002e523edd3f3f5dbed04ae031b0c5e48b0f66e76",
		"pet_tuanrong_radiant_front_walk_03.png": "7ff5be0dfbe7ff20a1bf5c2e6eab28e1fe3a9a5e045256b5d511820c78497e47",
		"pet_tuanrong_radiant_front_walk_04.png": "77db9882c2fd3e85d81c7ba88f94723b14930379d5bcd04f3290bd78fc4c8867",
		"pet_tuanrong_radiant_front_walk_05.png": "6e3e43c82d69ccf9efe4b5759afc5ba74ffbae62de3e49c0dcdb9ca4ebe2f876",
		"pet_tuanrong_radiant_front_walk_06.png": "4defff8b73d18a835d11797f1bd34eb0063238546d6166f78266d8673806d081",
		"pet_tuanrong_radiant_side_idle_01.png": "307d394ad7d6fe164ef23e33ff688db616ec1ae7bbd6ebf76375d88ab99ce210",
		"pet_tuanrong_radiant_side_walk_01.png": "307d394ad7d6fe164ef23e33ff688db616ec1ae7bbd6ebf76375d88ab99ce210",
		"pet_tuanrong_radiant_side_walk_02.png": "b5bcb3ebe0bc05e167dd9bbe6ae784b86274f3aa3d52d909eda5391fd1908799",
		"pet_tuanrong_radiant_side_walk_03.png": "da03e63b786cb623d31b2705660ed0f3158ca3ea931faa18e570f178a8bab397",
		"pet_tuanrong_radiant_side_walk_04.png": "552c3ef8895d11242bb29e14c1aeb4713bc44242ca6e3df92fba73578350f25d",
		"pet_tuanrong_radiant_side_walk_05.png": "098f5895c32ffb88750406581c6b2ed5316576d423b762c409bb491ee17f5486",
		"pet_tuanrong_radiant_side_walk_06.png": "4321f92ba4b6a93850b4262292b7e2edfdeec4a5aac4f616f0ca7c3a0fe380da",
	}
	var hashed := 0
	for name in want.keys():
		var path := "res://art/pet/r4/" + str(name)
		if _png_size(path) == Vector2i(64, 64) and _sha(path) == str(want[name]):
			hashed += 1
	_ok(hashed == 21, "all 21 frames are 64 and match the r4 byte list")
	_ok(_sha("res://art/pet/pet_tuanrong_radiant_idle_01.png") == str(want["pet_tuanrong_radiant_front_idle_01.png"]), "front idle matches the previous single idle byte for byte")
	_ok(_sha("res://art/pet/r4/pet_tuanrong_radiant_side_idle_01.png") != _sha("res://art/pet/r4/pet_tuanrong_radiant_front_idle_01.png"), "side idle is not the front idle")
	_ok(bool(clip.state().get("continuous_lock", true)) == false, "the clip does not claim a continuous foot lock")


func _png_size(path: String) -> Vector2i:
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return Vector2i.ZERO
	var img := Image.new()
	var err := img.load_png_from_buffer(f.get_buffer(f.get_length()))
	f.close()
	if err != OK:
		return Vector2i.ZERO
	return Vector2i(img.get_width(), img.get_height())


func _sha(path: String) -> String:
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return ""
	var ctx := HashingContext.new()
	ctx.start(HashingContext.HASH_SHA256)
	ctx.update(f.get_buffer(f.get_length()))
	f.close()
	return ctx.finish().hex_encode()
