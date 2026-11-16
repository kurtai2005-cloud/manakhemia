extends SceneTree
## Headless checks for the vc27 observation + care slice.
## Does not render the garden and does not claim frame rate or visual parity.

const Policy := preload("res://gameplay/m1_camera_policy.gd")
const Rules := preload("res://gameplay/m1_input_rules.gd")
const Gesture := preload("res://gameplay/m1_gesture.gd")
const Fade := preload("res://gameplay/m1_ui_fade.gd")
const Layout := preload("res://gameplay/m1_ui_layout.gd")

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


func _png_size(path: String) -> Vector2i:
	var img := Image.new()
	if img.load(path) != OK:
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
