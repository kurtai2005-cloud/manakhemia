extends SceneTree

var _fails := 0


func _initialize() -> void:
	if OS.get_environment("VC27_DRAFT_PREVIEW") != "1":
		print("R8_FAIL env")
		quit(2)
		return
	var main := (load("res://scenes/Main.tscn") as PackedScene).instantiate()
	root.add_child(main)
	for _i in range(200):
		await process_frame
		if main.get("hud") != null and main.get_node_or_null("EcosystemHud") != null:
			break
	await _hud(main)
	await _drag(main)
	await _props(main)
	await _kids(main)
	await _rug(main)
	await _fusion(main)
	_slice0(main)
	if _fails == 0:
		print("R8_GATES_OK")
		quit(0)
	else:
		print("R8_GATES_FAIL ", _fails)
		quit(1)


func _fail(why: String) -> void:
	_fails += 1
	print("R8_FAIL ", why)


func _hud(main: Node) -> void:
	var root_ui := main.get_node_or_null("EcosystemHud/Root")
	if root_ui == null:
		_fail("hud root")
		return
	var zones := ["garden", "cottage_yard_work", "prairie_edge", "zone_farm", "zone_workshop", "zone_prairie_deep", "zone_family_wall"]
	var icons := 0
	for zid in zones:
		var b := root_ui.get_node_or_null("Zone_%s" % zid) as Button
		if b == null or b.icon == null:
			_fail("zone icon " + zid)
			return
		if b.texture_filter != CanvasItem.TEXTURE_FILTER_LINEAR:
			_fail("zone filter")
			return
		var box := b.get_theme_stylebox("normal") as StyleBoxTexture
		if box == null or box.texture == null:
			_fail("pill")
			return
		if absf(box.texture_margin_left - 28.0) > 0.1 or absf(b.custom_minimum_size.y - 56.0) > 0.1:
			_fail("slice")
			return
		icons += 1
	var portrait := root_ui.get_node_or_null("PetPortrait") as Button
	var observe := root_ui.get_node_or_null("PrairieObserve") as Control
	if portrait == null or portrait.icon == null or observe == null or observe.get_child_count() != 3:
		_fail("portrait or stats")
		return
	root.get_node("Ecosystem").current_zone = "prairie_edge"
	await process_frame
	if not observe.visible:
		_fail("prairie hidden")
		return
	var book := _btn(main, "圖鑑")
	var post := _btn(main, "重看郵局")
	var hunt := _btn(main, "重看狩獵")
	for node in [portrait, observe]:
		var r: Rect2 = (node as Control).get_global_rect()
		if book and r.intersects(book.get_global_rect()):
			_fail("overlap book")
			return
		if post and r.intersects(post.get_global_rect()):
			_fail("overlap post")
			return
		if hunt and r.intersects(hunt.get_global_rect()):
			_fail("overlap hunt")
			return
	print("R8_PASS hud_textures")


func _drag(main: Node) -> void:
	var eco: Node = root.get_node("Ecosystem")
	eco.follow_pet("tuanrong")
	var drag := InputEventScreenDrag.new()
	drag.position = Vector2(200, 400)
	drag.relative = Vector2(20, 0)
	main.get_viewport().push_input(drag)
	await process_frame
	if str(eco.get("follow_pet_id")) != "":
		_fail("follow remained")
		return
	print("R8_PASS drag_cancels_follow")


func _props(main: Node) -> void:
	var eco: Node = root.get_node("Ecosystem")
	var plot := main.get_node_or_null("FarmPlot") as Sprite3D
	if plot == null:
		_fail("plot")
		return
	var names := ["farm_plot_empty", "farm_crop_stage1_sprout", "farm_crop_stage2_growing", "farm_crop_stage3_ripe"]
	var stages := ["empty", "seed", "sprout", "mature"]
	for i in range(stages.size()):
		eco.set_plot_stage(stages[i])
		var path := ""
		if plot.texture:
			path = plot.texture.resource_path
		if path.find(names[i]) < 0:
			_fail("plot texture " + stages[i] + " " + path)
			return
	if main.get_node_or_null("FarmPlot2") != null:
		_fail("stacked plot")
		return
	var sim: Node = root.get_node("Sim")
	sim.state["collection"] = {"fruits": {"a": 1}}
	await process_frame
	var pile := main.get_node_or_null("PantryPile") as Sprite3D
	if pile == null or pile.texture == null or pile.texture.resource_path.find("storage_fruit_pile_low") < 0:
		_fail("pile low")
		return
	sim.state["collection"] = {"fruits": {"a": 4}}
	await process_frame
	if pile.texture.resource_path.find("storage_fruit_pile_full") < 0:
		_fail("pile full")
		return
	if main.get_node_or_null("FamilyFrame_0") == null:
		_fail("frames")
		return
	var pet := main.get("pet") as Node3D
	if pet == null or not pet.has_method("set_errand"):
		_fail("pet walk")
		return
	eco.rug_phase = ""
	sim.state["rug_last_ms"] = Time.get_ticks_msec()
	var brain := pet.get_node_or_null("PetBrain")
	if brain:
		brain.busy = true
	pet.set("brain_driven", false)
	for building in ["kitchen", "post"]:
		var spot: Vector3 = eco.station_world(building)
		pet.global_position = spot + Vector3(4, 0, 0)
		pet.set_errand(spot)
		var before := pet.global_position.distance_to(spot)
		for _i in range(30):
			await process_frame
		if pet.global_position.distance_to(spot) > before - 0.4:
			_fail("walk " + building)
			return
	print("R8_PASS world_props")


func _kids(main: Node) -> void:
	var eco: Node = root.get_node("Ecosystem")
	var body := main.get_node_or_null("KidBody_B") as Sprite3D
	if body == null or absf(body.offset.y - eco.kid_offset_y("B1")) > 0.01:
		_fail("B1 offset")
		return
	for action in ["idle", "walk", "eat", "sleep", "cry"]:
		eco.set_kid_action("A", action)
		var tex := (main.get_node_or_null("KidBody_A") as Sprite3D).texture
		if tex == null or tex.resource_path.find("A1_%s" % action) < 0:
			_fail("kid " + action)
			return
	if main.get_node_or_null("KidMarker_H") == null:
		_fail("marker")
		return
	var partner := main.get_node_or_null("PartnerPet") as Sprite3D
	if partner == null:
		_fail("partner")
		return
	var x0 := partner.position.x
	for _i in range(20):
		await process_frame
	if absf(partner.position.x - x0) < 0.01:
		_fail("partner still")
		return
	eco.show_combo("parent_child")
	if main.get_node_or_null("EcosystemHud/Root/ComboBadge") == null:
		_fail("combo")
		return
	print("R8_PASS kids_anim_and_multipet")


func _rug(main: Node) -> void:
	root.get_node("TimeService").call("use_fake", 12 * 3600 * 1000)
	var sim: Node = root.get_node("Sim")
	var house: Dictionary = sim.state.get("house", {})
	var placed: Dictionary = house.get("placed", {})
	placed["rug"] = "rug_leaf"
	house["placed"] = placed
	sim.state["house"] = house
	sim.state["rug_last_ms"] = 0
	var needs: Dictionary = sim.state.get("needs", {})
	needs["hunger"] = 80
	needs["energy"] = 80
	sim.state["needs"] = needs
	var eco: Node = root.get_node("Ecosystem")
	var saw := false
	for _i in range(400):
		await process_frame
		if str(eco.get("rug_phase")) == "roll" or str(eco.get("rug_phase")) == "walk":
			saw = true
			break
	if not saw:
		_fail("rug never started")
		return
	needs["hunger"] = 20
	sim.state["needs"] = needs
	for _i in range(60):
		await process_frame
		if str(eco.get("rug_phase")) == "":
			print("R8_PASS rug_roll_live")
			return
	_fail("rug did not exit")


func _fusion(main: Node) -> void:
	var sim: Node = root.get_node("Sim")
	sim.state["pets"] = [
		{"id": "tuanrong", "stage": "adult", "combat": {"力量": 1, "身手": 1, "耐力": 1}, "fusion_state": "none"},
		{"id": "partner", "stage": "adult", "combat": {"力量": 2, "身手": 2, "耐力": 2}, "fusion_state": "none"},
	]
	var eco: Node = root.get_node("Ecosystem")
	var began: Dictionary = eco.begin_fusion(Time.get_ticks_msec())
	if not bool(began.get("ok", false)):
		_fail("fuse start %s pets=%d" % [str(began), (sim.state.get("pets", []) as Array).size()])
		return
	var echo: Sprite3D = null
	for _i in range(120):
		await process_frame
		echo = main.get_node_or_null("FusionEcho") as Sprite3D
		if echo and echo.modulate.a > 0.4:
			break
	if echo == null:
		_fail("echo")
		return
	var pet := main.get("pet") as Node3D
	if absf(echo.global_position.x - pet.global_position.x - 6.0) > 1.5:
		_fail("echo offset")
		return
	if absf(echo.modulate.a - 0.45) > 0.08:
		_fail("echo alpha %s" % str(echo.modulate.a))
		return
	if main.get_node_or_null("FusionHalo") == null:
		_fail("halo")
		return
	sim.state["fusion"]["ends_at_ms"] = 0
	for _i in range(50):
		await process_frame
	if main.get_node_or_null("FusionEcho") != null:
		_fail("echo remained")
		return
	if (sim.state.get("pets", []) as Array).size() < 2:
		_fail("pet lost")
		return
	print("R8_PASS fusion_visual_and_split")


func _slice0(main: Node) -> void:
	if _btn(main, "重看郵局") == null or _btn(main, "重看狩獵") == null:
		_fail("replay missing")
		return
	var shards := int(root.get_node("CollectionSystem").call("stardust"))
	if int(root.get_node("Sim").state.get("daily_ledger", {}).get("jt_shards", 0)) > 12:
		_fail("cap")
		return
	if shards < 0:
		_fail("wallet")
		return
	print("R8_PASS slice0_and_migration")


func _btn(main: Node, text: String) -> BaseButton:
	var hud: Node = main.get("hud")
	if hud == null:
		return null
	for c in hud.find_children("*", "BaseButton", true, false):
		if str(c.text) == text:
			return c
	return null
