extends SceneTree
## Preview replay buttons. Presses are ScreenTouch plus the device -1 mouse
## Android synthesizes. Calling replay_post or replay_hunt is not this test.

var _main: Node


func _initialize() -> void:
	var udir := OS.get_user_data_dir()
	print("r5 user_dir=", udir)
	if udir.find("vc27_life_r5") < 0 or udir.find("vc27_play_36bfd") >= 0 or udir.find("vc27_draft_try") >= 0:
		print("R5_FAIL profile")
		quit(2)
		return
	var phase := OS.get_environment("VC27_LIFE_PHASE")
	if phase == "normal":
		if OS.get_environment("VC27_DRAFT_PREVIEW") == "1":
			print("R5_FAIL normal env")
			quit(2)
			return
		await _normal()
		return
	if OS.get_environment("VC27_DRAFT_PREVIEW") != "1":
		print("R5_FAIL env")
		quit(2)
		return
	if phase == "reread" or phase == "resume":
		await _read(phase)
		return
	_main = (load("res://scenes/Main.tscn") as PackedScene).instantiate()
	root.add_child(_main)
	if not await _pet():
		_die("pet missing")
		return
	if phase == "mid":
		await _mid()
		return
	await _both()


func _pet() -> bool:
	var deadline := Time.get_ticks_msec() + 8000
	while Time.get_ticks_msec() < deadline:
		await process_frame
		if _main.get("pet") != null and _main.get("hud") != null:
			return true
	return false


func _both() -> void:
	var post_btn := _button("重看郵局")
	var hunt_btn := _button("重看狩獵")
	if post_btn == null or hunt_btn == null:
		_die("replay buttons missing on preview")
		return
	var sim: Node = root.get_node("Sim")
	if bool(sim.state.get("preview_fixture", false)):
		_die("upgrade save still had preview_fixture")
		return
	print("R6_UPGRADE_VISIBLE stage=", sim.state.get("stage"), " meals=", sim.state.get("errand", {}).get("meals"), " paid=", sim.state.get("errand", {}).get("paid_through"), " fixture=", sim.state.get("preview_fixture", false))
	_probe_preview()
	if not _layout(post_btn, hunt_btn):
		return
	var before := _snap()
	print("R5_BOOT ", _fmt(before))
	if not await _tap_and_play(post_btn, "post"):
		return
	var after_post := _snap()
	if not _same(before, after_post):
		_die("post replay changed state")
		return
	if not await _tap_and_play(post_btn, "post"):
		return
	if not _same(before, _snap()):
		_die("second post replay changed state")
		return
	if not await _tap_and_play(hunt_btn, "hunt"):
		return
	if not _same(before, _snap()):
		_die("hunt replay changed state")
		return
	if not await _tap_and_play(hunt_btn, "hunt"):
		return
	var after := _snap()
	if not _same(before, after):
		_die("second hunt replay changed state")
		return
	var pet: Node3D = _main.get("pet")
	var coat := pet.get_node_or_null("Hd2dCoat")
	var brain: Node = pet.get_node_or_null("PetBrain")
	if coat == null or not coat.visible or pet.global_position.z > 200.0:
		_die("pet not back on the lawn")
		return
	if brain == null or bool(brain.get("busy")) or not bool(pet.get("brain_driven")):
		_die("autonomous life did not resume")
		return
	var idle_until := Time.get_ticks_msec() + 3000
	while Time.get_ticks_msec() < idle_until:
		await process_frame
		if str(_main.get("replay_kind")) != "":
			_die("replay still running")
			return
	if not _same(before, _snap()):
		_die("idle resume changed state")
		return
	root.get_node("Sim").notification(NOTIFICATION_APPLICATION_PAUSED)
	print("R5_REPLAY_OK ", _fmt(after))
	quit(0)


func _tap_and_play(btn: BaseButton, kind: String) -> bool:
	if btn.disabled:
		_die("%s button disabled before tap reason=%s" % [kind, _reason()])
		return false
	var at: Vector2 = btn.get_global_rect().get_center()
	_touch(at, true)
	_touch(at, false)
	_mouse(at, true)
	_mouse(at, false)
	var started := Time.get_ticks_msec() + 4000
	var saw := false
	while Time.get_ticks_msec() < started:
		await process_frame
		if str(_main.get("replay_kind")) == kind:
			saw = true
			break
	if not saw:
		_die("%s tap did not start replay reason=%s" % [kind, _reason()])
		return false
	# The synthesized click must not cancel or stack a second run.
	await _frames(8)
	if str(_main.get("replay_kind")) != kind:
		_die("%s mouse cancelled the replay" % kind)
		return false
	if _reason() != "重看中":
		_die("%s missing disabled reason %s" % [kind, _reason()])
		return false
	var other := _button("重看狩獵" if kind == "post" else "重看郵局")
	if other == null or not other.disabled:
		_die("other replay button stayed enabled")
		return false
	var origin: Vector3 = (_main.get("pet") as Node3D).global_position
	var moved := false
	var deadline := Time.get_ticks_msec() + 90000
	var saw_place := false
	while Time.get_ticks_msec() < deadline:
		await process_frame
		var pet: Node3D = _main.get("pet")
		if kind == "post" and pet.global_position.x < -140.0 and pet.global_position.z > 55.0:
			saw_place = true
		if kind == "hunt" and pet.global_position.z > 400.0:
			saw_place = true
		if pet.global_position.distance_to(origin) > 8.0:
			moved = true
		if str(_main.get("replay_kind")) == "":
			break
	if str(_main.get("replay_kind")) != "":
		_die("%s replay did not finish" % kind)
		return false
	if not moved or not saw_place:
		_die("%s replay was not spatial moved=%s place=%s" % [kind, moved, saw_place])
		return false
	print("R5_DONE ", kind, " reason_after=", _reason())
	return true


func _mid() -> void:
	var btn := _button("重看郵局")
	if btn == null:
		_die("mid button missing")
		return
	var at: Vector2 = btn.get_global_rect().get_center()
	_touch(at, true)
	_touch(at, false)
	_mouse(at, true)
	_mouse(at, false)
	var deadline := Time.get_ticks_msec() + 20000
	while Time.get_ticks_msec() < deadline:
		await process_frame
		var pet: Node3D = _main.get("pet")
		if str(_main.get("replay_kind")) == "post" and pet.global_position.x < -20.0:
			root.get_node("Sim").notification(NOTIFICATION_APPLICATION_PAUSED)
			print("R5_MID_OK shards=", _snap()["shards"])
			quit(0)
			return
	_die("mid replay did not move")


func _read(phase: String) -> void:
	for _i in range(20):
		await process_frame
	if phase == "reread":
		_probe_preview()
	var sim: Node = root.get_node("Sim")
	var st: Dictionary = sim.state
	var shards := int(st.get("wallet", {}).get("stardust", -1))
	var post := str(st.get("jobs_state", {}).get("sites", {}).get("post", {}).get("status", ""))
	var hunt_phase := str(st.get("hunt", {}).get("phase", ""))
	var pending: Dictionary = st.get("hunt", {}).get("pending", {})
	var meals := int(st.get("errand", {}).get("meals", 0))
	var rug := str(st.get("house", {}).get("placed", {}).get("rug", ""))
	print("R5_READ phase=", phase, " shards=", shards, " post=", post, " hunt=", hunt_phase, " pending=", not pending.is_empty(), " meals=", meals, " rug=", rug, " preview=", st.get("preview_fixture"))
	if phase == "resume":
		if shards != 17 or post != "empty" or not pending.is_empty() or meals < 1 or rug != "rug_leaf":
			_die("mid replay resumed as a paid job")
			return
		print("R5_RESUME_OK")
		quit(0)
		return
	if shards != 17 or post != "empty" or not pending.is_empty() or meals < 1 or rug != "rug_leaf":
		_die("reload lost or paid the replay")
		return
	print("R5_REREAD_OK")
	quit(0)


func _normal() -> void:
	_main = (load("res://scenes/Main.tscn") as PackedScene).instantiate()
	root.add_child(_main)
	if not await _pet():
		_die("normal pet missing")
		return
	if _button("重看郵局") != null or _button("重看狩獵") != null:
		_die("normal save showed replay buttons")
		return
	if bool(root.get_node("Sim").state.get("preview_fixture", false)):
		_die("normal save became preview")
		return
	print("R6_NORMAL_OK")
	quit(0)


func _probe_preview() -> void:
	var save: Node = root.get_node("SaveSystem")
	var live := str(save.call("read_proc_cmdline"))
	var preview_name := "hk.vizard.glimmer.fpet.vc27draft:vc27preview"
	var normal_name := "hk.vizard.glimmer.fpet.vc27draft"
	print("R6_PROC live=", live.replace("\n", " "))
	print("R6_PROC preview=", save.call("text_is_preview_process", preview_name), " normal=", save.call("text_is_preview_process", normal_name))


func _layout(post_btn: BaseButton, hunt_btn: BaseButton) -> bool:
	var book := _button("圖鑑")
	var vp: Vector2 = _main.get_viewport().get_visible_rect().size
	for b in [post_btn, hunt_btn]:
		var r: Rect2 = b.get_global_rect()
		var font: Font = b.get_theme_font("font")
		var missing := ""
		if font:
			for ch in b.text:
				if not font.has_char(ch.unicode_at(0)):
					missing += ch
		var scale := minf(1080.0 / 390.0, 2280.0 / 844.0)
		var x0: float = (1080.0 - 390.0 * scale) * 0.5 + r.position.x * scale
		var y0: float = r.position.y * scale
		var x1: float = x0 + r.size.x * scale
		var y1: float = y0 + r.size.y * scale
		var on_screen: bool = r.position.x >= 0.0 and r.position.y >= 72.0 and r.position.x + r.size.x <= vp.x and r.position.y + r.size.y <= vp.y and r.size.x > 40.0 and r.size.y > 40.0
		var phone: bool = x0 >= 48.0 and y0 >= 160.0 and x1 <= 1080.0 - 48.0 and y1 <= 2280.0 - 48.0
		var book_hit := false
		if book:
			book_hit = r.intersects(book.get_global_rect())
		print("R6_LAYOUT ", b.text, " rect=", r, " missing=", missing, " viewport_ok=", on_screen, " note10_ok=", phone, " overlaps_book=", book_hit)
		if missing != "" or not on_screen or not phone or book_hit:
			_die("layout " + b.text)
			return false
	return true


func _snap() -> Dictionary:
	var sim: Node = root.get_node("Sim")
	var st: Dictionary = sim.state
	var fruits := 0
	for k in st.get("collection", {}).get("fruits", {}).keys():
		fruits += int(st.get("collection", {}).get("fruits", {}).get(k, 0))
	var critters: Dictionary = st.get("collection", {}).get("critters", {})
	return {
		"shards": int(st.get("wallet", {}).get("stardust", -1)),
		"fruits": fruits,
		"critters": critters.size(),
		"meals": int(st.get("errand", {}).get("meals", 0)),
		"rug": str(st.get("house", {}).get("placed", {}).get("rug", "")),
		"stage": str(st.get("stage", "")),
		"post": str(st.get("jobs_state", {}).get("sites", {}).get("post", {}).get("status", "")),
		"hunt": str(st.get("hunt", {}).get("phase", "")),
		"pending": not (st.get("hunt", {}).get("pending", {}) as Dictionary).is_empty(),
		"worked": bool(st.get("hunt", {}).get("worked_or_hunted", {}).get("tuanrong", false)),
	}


func _same(a: Dictionary, b: Dictionary) -> bool:
	for k in a.keys():
		if str(a[k]) != str(b[k]):
			print("R5_DIFF ", k, " ", a[k], " -> ", b[k])
			return false
	return true


func _fmt(s: Dictionary) -> String:
	return "shards=%s fruits=%s critters=%s meals=%s post=%s hunt=%s" % [s["shards"], s["fruits"], s["critters"], s["meals"], s["post"], s["hunt"]]


func _reason() -> String:
	var hud: Node = _main.get("hud")
	if hud == null:
		return ""
	var lbl: Node = hud.get("replay_reason")
	if lbl == null:
		return ""
	return str(lbl.get("text"))


func _button(text: String) -> BaseButton:
	var hud: Node = _main.get("hud")
	if hud == null:
		return null
	for c in hud.find_children("*", "BaseButton", true, false):
		if str(c.text) == text:
			return c
	return null


func _touch(screen: Vector2, pressed: bool) -> void:
	var ev := InputEventScreenTouch.new()
	ev.index = 0
	ev.pressed = pressed
	ev.position = screen
	_main.get_viewport().push_input(ev)


func _mouse(screen: Vector2, pressed: bool) -> void:
	var ev := InputEventMouseButton.new()
	ev.button_index = MOUSE_BUTTON_LEFT
	ev.pressed = pressed
	ev.position = screen
	ev.global_position = screen
	ev.device = -1
	_main.get_viewport().push_input(ev)


func _frames(n: int) -> void:
	for _i in range(n):
		await process_frame


func _die(why: String) -> void:
	print("R5_FAIL ", why)
	quit(1)
