extends SceneTree
## Ecosystem gates. Linux headless is not an Android pass.

var _fails := 0


func _initialize() -> void:
	if OS.get_environment("VC27_R7_BOOT") == "1":
		await _boot_preview()
	else:
		root.get_node("Ecosystem")._ready()
		_font()
		_migration()
		_ledger()
		_combat()
		_zones()
		_fusion()
		_farm_rug_personality()
		_kids()
	if _fails == 0:
		print("R7_GATES_OK")
		quit(0)
	else:
		print("R7_GATES_FAIL ", _fails)
		quit(1)


func _fail(why: String) -> void:
	_fails += 1
	print("R7_FAIL ", why)


func _ok(line: String) -> void:
	print("R7_PASS ", line)


func _font() -> void:
	var face := load("res://art/fonts/vc27_label_fallback.otf") as Font
	var base := load("res://art/fonts/GenWanMin2TC-R.subset.otf") as Font
	var sample := "農圃巡場採集輕鬆細佬合體族譜力量身手耐力協同組合進化路線·（）：，"
	var missing := ""
	for i in range(sample.length()):
		var cp := sample.unicode_at(i)
		var hit := (face != null and face.has_char(cp)) or (base != null and base.has_char(cp))
		if not hit:
			missing += sample.substr(i, 1)
	if missing != "":
		_fail("font " + missing)
	else:
		_ok("font sample")


func _migration() -> void:
	var eco: Node = root.get_node("Ecosystem")
	print("R7_CFG ", eco.cfg.size(), " ", eco.cfg.get("_file", ""))
	var old := {
		"stage": "newborn",
		"form": "radiant",
		"needs": {"hunger": 80, "energy": 70},
		"wallet": {"stardust": 17},
		"house": {"owned": ["bed_leaf", "rug_leaf"], "placed": {"rug": "rug_leaf"}},
		"collection": {"discovered": {"glow_berry": true}, "critters": {"rumble_root": true}, "fruits": {"moon_grape": 2}},
		"errand": {"meals": 1, "paid_through": 1},
	}
	eco.migrate(old)
	if int(old.get("ecosystem_schema", 0)) != 1:
		_fail("schema")
		return
	if int(old.get("wallet", {}).get("stardust", 0)) != 17:
		_fail("shards overwritten")
		return
	if str(old.get("house", {}).get("placed", {}).get("rug", "")) != "rug_leaf":
		_fail("rug overwritten")
		return
	if int(old.get("unique_collect", 0)) < 2:
		_fail("unique_collect")
		return
	var pets: Array = old.get("pets", [])
	if pets.size() != 1 or str(pets[0].get("stage", "")) != "newborn":
		_fail("pet migrate")
		return
	_ok("migration shards=17 rug unique=%s" % str(old.get("unique_collect")))


func _ledger() -> void:
	var eco: Node = root.get_node("Ecosystem")
	var sim: Node = root.get_node("Sim")
	sim.state = {"daily_ledger": {}, "wallet": {"stardust": 0}, "collection": {"fruits": {}}}
	var paid := 0
	for _i in range(8):
		paid += int(eco.grant_shards(3, "jobs_trips"))
	if paid != 12:
		_fail("jt cap %s" % paid)
		return
	if int(sim.state.get("daily_ledger", {}).get("jt_shards", 0)) != 12:
		_fail("ledger")
		return
	var patrol: Dictionary = eco.observe_patrol()
	if int(patrol.get("shards", 1)) != 0 or str(patrol.get("label", "")).find("輕鬆巡場") < 0:
		_fail("patrol")
		return
	if int(sim.state.get("seeds", 0)) < 1:
		_fail("nonshard drop")
		return
	_ok("ledger jt=12 patrol=0 seeds=%s" % str(sim.state.get("seeds")))


func _combat() -> void:
	var eco: Node = root.get_node("Ecosystem")
	if absf(float(eco.power_interval_mul(1)) - 1.0) > 0.001:
		_fail("power1")
		return
	if absf(float(eco.power_interval_mul(10)) - 0.73) > 0.001:
		_fail("power10")
		return
	if absf(float(eco.agility_miss(1)) - 0.25) > 0.001:
		_fail("agi1")
		return
	if absf(float(eco.stamina_stay(10)) - 60.0) > 0.001:
		_fail("sta10")
		return
	var pet := {"combat": {"力量": 1, "身手": 1, "耐力": 1}, "combat_gained_today": {}}
	eco.grow_combat(pet, "力量", 5.0)
	if float(pet["combat"]["力量"]) > 2.01:
		_fail("growth cap")
		return
	var needs := {"hunger": 5.0, "energy": 4.0}
	eco.floor_needs(needs)
	if float(needs["hunger"]) < 20.0 or float(needs["energy"]) < 20.0:
		_fail("floor")
		return
	_ok("combat formulas clamp floor")


func _zones() -> void:
	var eco: Node = root.get_node("Ecosystem")
	var blocked := {
		"age_day": 1,
		"pets": [{"stage": "adult", "combat": {"力量": 1, "身手": 1, "耐力": 1}}],
		"lifetime_hunts": 1,
		"seeds": 0,
		"unique_collect": 0,
		"wallet": {"stardust": 0},
	}
	if bool(eco.zone_unlocked("zone_prairie_deep", blocked)):
		_fail("deep unlocked too early")
		return
	var ready := {
		"age_day": 4,
		"seeds": 1,
		"pets": [{"stage": "adult", "combat": {"力量": 4, "身手": 4, "耐力": 4}}],
		"lifetime_hunts": 5,
		"unique_collect": 1,
		"wallet": {"stardust": 12},
		"lifetime_paid": 4,
	}
	if not bool(eco.zone_unlocked("zone_farm", ready)):
		_fail("farm locked")
		return
	if not bool(eco.zone_unlocked("zone_prairie_deep", ready)):
		_fail("deep locked")
		return
	_ok("zones farm+deep")


func _fusion() -> void:
	var eco: Node = root.get_node("Ecosystem")
	var sim: Node = root.get_node("Sim")
	sim.state = {"pets": [
		{"id": "a", "stage": "adult", "combat": {"力量": 4, "身手": 3, "耐力": 2}, "fusion_state": "none"},
		{"id": "b", "stage": "adult", "combat": {"力量": 2, "身手": 6, "耐力": 5}, "fusion_state": "none"},
	]}
	var began: Dictionary = eco.begin_fusion(1000)
	if not bool(began.get("ok", false)):
		_fail("fuse")
		return
	if (sim.state.get("pets", []) as Array).size() != 2:
		_fail("pets removed")
		return
	if absf(float(eco.fusion_stat(4, 2, 2)) - 6.0) > 0.001:
		_fail("fusion stat")
		return
	eco.recover_fusion(int(sim.state.get("fusion", {}).get("ends_at_ms", 0)) + 1)
	if bool(sim.state.get("fusion", {}).get("active", true)):
		_fail("split")
		return
	if str(sim.state.get("pets", [])[0].get("fusion_state", "")) != "none":
		_fail("flag")
		return
	_ok("fusion split keeps both")


func _farm_rug_personality() -> void:
	var eco: Node = root.get_node("Ecosystem")
	var plot := {"stage": "seed", "age": 0.0}
	eco.advance_plot(plot, float(eco.crop_phase_sec(false)), false)
	if str(plot.get("stage", "")) != "sprout":
		_fail("sprout")
		return
	eco.advance_plot(plot, float(eco.crop_phase_sec(false)), false)
	if str(plot.get("stage", "")) != "mature":
		_fail("mature")
		return
	if not bool(eco.rug_exit(20, 100, false)):
		_fail("rug")
		return
	if absf(float(eco.walk_speed_mul(5)) - 1.2) > 0.001 or absf(float(eco.walk_speed_mul(-5)) - 0.85) > 0.001:
		_fail("speed")
		return
	if absf(float(eco.action_interval(5, 0)) - 15.3) > 0.05:
		_fail("interval %s" % str(eco.action_interval(5, 0)))
		return
	_ok("farm rug personality")


func _kids() -> void:
	var eco: Node = root.get_node("Ecosystem")
	if absf(float(eco.kid_offset_y("A1")) - -6.0) > 0.01:
		_fail("A1 offset")
		return
	if absf(float(eco.kid_offset_y("B1")) - -7.0) > 0.01 or absf(float(eco.kid_offset_y("H3")) - -7.0) > 0.01 or absf(float(eco.kid_offset_y("S4B")) - -7.0) > 0.01:
		_fail("special offset")
		return
	_ok("kid offsets")


func _boot_preview() -> void:
	var main := (load("res://scenes/Main.tscn") as PackedScene).instantiate()
	root.add_child(main)
	for _i in range(180):
		await process_frame
		if main.get("hud") != null and main.get_node_or_null("WorkOutdoorStove") != null:
			break
	var hud: Node = main.get("hud")
	var post: BaseButton = null
	var hunt: BaseButton = null
	if hud:
		for c in hud.find_children("*", "BaseButton", true, false):
			if str(c.text) == "重看郵局":
				post = c
			if str(c.text) == "重看狩獵":
				hunt = c
	if post == null or hunt == null:
		_fail("replay buttons")
		return
	if main.get_node_or_null("WorkOutdoorStove") == null or main.get_node_or_null("WorkOutdoorPost") == null:
		_fail("open air stations")
		return
	if main.get_node_or_null("KidMarker_A") == null or main.get_node_or_null("KidMarker_H") == null:
		_fail("kid markers")
		return
	if main.get_node_or_null("EcosystemHud") == null:
		_fail("zone hud")
		return
	var shards := int(root.get_node("CollectionSystem").call("stardust"))
	var at: Vector2 = post.get_global_rect().get_center()
	var down := InputEventScreenTouch.new()
	down.pressed = true
	down.position = at
	down.index = 0
	main.get_viewport().push_input(down)
	var up := down.duplicate() as InputEventScreenTouch
	up.pressed = false
	main.get_viewport().push_input(up)
	var mouse := InputEventMouseButton.new()
	mouse.button_index = MOUSE_BUTTON_LEFT
	mouse.pressed = true
	mouse.position = at
	mouse.device = -1
	main.get_viewport().push_input(mouse)
	for _i in range(30):
		await process_frame
	if int(root.get_node("CollectionSystem").call("stardust")) != shards:
		_fail("replay paid")
		return
	var drag := InputEventScreenDrag.new()
	drag.position = at
	drag.relative = Vector2(12, 0)
	main.get_viewport().push_input(drag)
	if str(root.get_node("Ecosystem").get("follow_id")) != "":
		_fail("follow survived drag")
		return
	root.get_node("Ecosystem").follow_pet("tuanrong")
	main.get_viewport().push_input(drag)
	if str(root.get_node("Ecosystem").get("follow_id")) != "":
		_fail("drag did not stop follow")
		return
	_ok("preview buttons stations kids drag")
