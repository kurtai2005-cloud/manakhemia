extends SceneTree
## Idle preview. The test does not call forage, feed, rest, dispatch, or collect.
## It only watches the pet, then taps the shop once. A second process only reads.

var _main: Node
var _log: Array = []
var _prev := {}


func _initialize() -> void:
	var udir := OS.get_user_data_dir()
	print("life user_dir=", udir)
	if udir.find("vc27_play_36bfd") >= 0 or udir.find("vc27_draft_try") >= 0 or udir.find("vc27_draft_preview") >= 0:
		print("LIFE_FAIL profile")
		quit(2)
		return
	if udir.find("vc27_life_") < 0:
		print("LIFE_FAIL profile")
		quit(2)
		return
	if OS.get_environment("VC27_DRAFT_PREVIEW") != "1":
		print("LIFE_FAIL env")
		quit(2)
		return
	var phase := OS.get_environment("VC27_LIFE_PHASE")
	if phase == "2":
		await _read_back()
		return
	if phase == "rug":
		await _rug_only()
		return
	if phase == "upgrade":
		await _upgrade()
		return
	await _fresh()


func _fresh() -> void:
	_boot()
	if not await _ready_pet():
		_die("pet did not appear")
		return
	_note("boot", "new preview save, no taps")
	var deadline := Time.get_ticks_msec() + 480000
	var saw_meal := false
	var saw_sleep := false
	var saw_wake := false
	var saw_kitchen := false
	var saw_pay := false
	var start_shards := int(root.get_node("CollectionSystem").call("stardust"))
	var trace_at := 0
	while Time.get_ticks_msec() < deadline:
		await process_frame
		_watch()
		var sim: Node = root.get_node("Sim")
		if int(sim.state.get("errand", {}).get("meals", 0)) >= 1:
			saw_meal = true
		if bool(sim.state.get("sleeping", false)):
			saw_sleep = true
		if saw_sleep and not bool(sim.state.get("sleeping", false)) and not bool(_main.get("in_interior")):
			saw_wake = true
		var work: Node = root.get_node("WorkSystem")
		if str(work.site("kitchen").get("status", "")) == "work":
			saw_kitchen = true
		if int(root.get_node("CollectionSystem").call("stardust")) >= start_shards + 2:
			saw_pay = true
		if Time.get_ticks_msec() >= trace_at:
			trace_at = Time.get_ticks_msec() + 5000
			var pet: Node3D = _main.get("pet")
			print("TRACE pos=", pet.global_position, " errand=", pet.get("errand_active"), " blocked=", pet.get("errand_blocked"), " phase=", sim.state.get("errand", {}).get("phase"))
		if saw_meal and saw_sleep and saw_wake and saw_kitchen and saw_pay:
			break
	_dump()
	if not saw_meal or not saw_sleep or not saw_wake or not saw_kitchen or not saw_pay:
		_die("idle loop did not finish meal=%s sleep=%s wake=%s kitchen=%s pay=%s" % [saw_meal, saw_sleep, saw_wake, saw_kitchen, saw_pay])
		return
	if str(root.get_node("Sim").state.get("stage", "")) == "egg":
		_die("preview delivery did not hatch")
		return
	if not await _buy_rug():
		return
	print("LIFE_FRESH_OK")
	quit(0)


func _rug_only() -> void:
	_boot()
	if not await _ready_pet():
		_die("rug pet missing")
		return
	if not await _buy_rug():
		return
	print("LIFE_RUG_OK")
	quit(0)


func _upgrade() -> void:
	_boot()
	if not await _ready_pet():
		_die("upgrade pet missing")
		return
	var sim: Node = root.get_node("Sim")
	if str(sim.state.get("stage", "")) != "newborn" or not bool(sim.state.get("preview_fixture", false)):
		_die("upgrade save was reseeded stage=%s fixture=%s" % [sim.state.get("stage"), sim.state.get("preview_fixture")])
		return
	_note("upgrade", "existing newborn preview, no taps")
	var gathers := 0
	var kitchen := false
	var deadline := Time.get_ticks_msec() + 45000
	while Time.get_ticks_msec() < deadline:
		await process_frame
		var phase := str(sim.state.get("errand", {}).get("phase", ""))
		if phase == "to_pick" and (_prev.get("phase", "") != "to_pick"):
			gathers += 1
		_watch()
		if str(root.get_node("WorkSystem").site("kitchen").get("status", "")) == "work":
			kitchen = true
			break
	_dump()
	if str(sim.state.get("stage", "")) != "newborn":
		_die("upgrade changed the stage")
		return
	if gathers > 0:
		_die("full newborn gathered again")
		return
	if not kitchen:
		_die("full newborn did not start the kitchen")
		return
	print("LIFE_UPGRADE_OK gathers=0 kitchen=started")
	quit(0)


func _read_back() -> void:
	_boot()
	if not await _ready_pet():
		_die("reread had no pet")
		return
	var sim: Node = root.get_node("Sim")
	var col: Node = root.get_node("CollectionSystem")
	var meals := int(sim.state.get("errand", {}).get("meals", 0))
	var fruit := int(col.call("fruit_count", "starberry"))
	var glow := bool(sim.state.get("collection", {}).get("discovered", {}).get("glow_berry", false))
	var shards := int(col.call("stardust"))
	var placed: Dictionary = col.placed_items()
	var owned: Array = col.owned()
	print("REREAD stage=", sim.state.get("stage"), " meals=", meals, " fruit=", fruit, " glow=", glow, " shards=", shards, " rug=", placed.get("rug", ""), " owned_rug=", "rug_leaf" in owned)
	if str(sim.state.get("stage", "")) == "egg" or meals < 1 or not glow or shards != 12 or str(placed.get("rug", "")) != "rug_leaf":
		_die("reread lost the earned rug or the meal")
		return
	print("LIFE_REREAD_OK")
	quit(0)


func _buy_rug() -> bool:
	var book := _button_text("圖鑑")
	if book == null:
		_die("book button missing")
		return false
	_touch(book.get_global_rect().get_center(), true)
	_touch(book.get_global_rect().get_center(), false)
	await _frames(4)
	var rug := _button_containing("葉仔地氈")
	if rug == null:
		_die("rug button missing")
		return false
	_touch(rug.get_global_rect().get_center(), true)
	_touch(rug.get_global_rect().get_center(), false)
	await _frames(6)
	var col: Node = root.get_node("CollectionSystem")
	var placed: Dictionary = col.placed_items()
	if str(placed.get("rug", "")) != "rug_leaf" or int(col.call("stardust")) != 12:
		_die("rug tap did not buy and place")
		return false
	_note("rug", "player tap bought 葉仔地氈")
	# Same path as leaving the app. Not a reward write.
	root.get_node("Sim").notification(NOTIFICATION_APPLICATION_PAUSED)
	return true


func _boot() -> void:
	_main = (load("res://scenes/Main.tscn") as PackedScene).instantiate()
	root.add_child(_main)


func _ready_pet() -> bool:
	for _i in range(240):
		await process_frame
		if _main.get("pet") != null and _main.get_node_or_null("GardenErrand") != null:
			return true
	return false


func _watch() -> void:
	var sim: Node = root.get_node("Sim")
	var col: Node = root.get_node("CollectionSystem")
	var work: Node = root.get_node("WorkSystem")
	var now := {
		"phase": str(sim.state.get("errand", {}).get("phase", "")),
		"stage": str(sim.state.get("stage", "")),
		"meals": int(sim.state.get("errand", {}).get("meals", 0)),
		"fruit": int(col.call("fruit_count", "starberry")),
		"glow": bool(sim.state.get("collection", {}).get("discovered", {}).get("glow_berry", false)),
		"sleep": bool(sim.state.get("sleeping", false)),
		"inside": bool(_main.get("in_interior")),
		"kitchen": str(work.site("kitchen").get("status", "")),
		"shards": int(col.call("stardust")),
		"hunger": int(sim.state.get("needs", {}).get("hunger", 0)),
		"energy": int(sim.state.get("needs", {}).get("energy", 0)),
	}
	if now == _prev:
		return
	var growth := float(sim.state.get("growth_sec", 0.0))
	var note := ""
	if _prev.has("stage") and str(_prev["stage"]) == "egg" and str(now["stage"]) != "egg":
		note = "EXISTING_PREVIEW_FIXTURE delivery fills the egg clock"
	if _prev.has("energy") and int(_prev["energy"]) < 95 and int(now["energy"]) >= 99 and bool(now["sleep"]):
		note = "EXISTING_PREVIEW_FIXTURE sleep starts one below wake"
	_prev = now.duplicate()
	var line := "LIFE t=%d phase=%s stage=%s meals=%d fruit=%d glow=%s sleep=%s inside=%s kitchen=%s shards=%d hunger=%d energy=%d growth=%.0f %s" % [Time.get_ticks_msec(), now["phase"], now["stage"], now["meals"], now["fruit"], now["glow"], now["sleep"], now["inside"], now["kitchen"], now["shards"], now["hunger"], now["energy"], growth, note]
	_log.append(line)
	print(line)


func _note(tag: String, text: String) -> void:
	print("LIFE ", tag, " ", text)


func _dump() -> void:
	pass


func _frames(n: int) -> void:
	for _i in range(n):
		await process_frame


func _touch(screen: Vector2, pressed: bool) -> void:
	var ev := InputEventScreenTouch.new()
	ev.index = 0
	ev.pressed = pressed
	ev.position = screen
	_main.get_viewport().push_input(ev)


func _button_text(text: String) -> BaseButton:
	return _find_button(text, false)


func _button_containing(text: String) -> BaseButton:
	return _find_button(text, true)


func _find_button(text: String, partial: bool) -> BaseButton:
	var hud: Node = _main.get("hud")
	if hud == null:
		return null
	for c in hud.find_children("*", "BaseButton", true, false):
		if not c.visible:
			continue
		if str(c.text) == text or (partial and str(c.text).find(text) >= 0):
			return c
		if not partial:
			continue
		for ch in c.find_children("*", "Label", true, false):
			if str(ch.text).find(text) >= 0:
				return c
	return null


func _die(why: String) -> void:
	print("LIFE_FAIL ", why)
	quit(1)
