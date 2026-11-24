extends Node
## Phase 1 facade: one UI, four yards, flat pets, idle and evolution.

var doc: Dictionary = {}
var active := false
var host: Node
var world: Phase1World
var hud: Phase1Hud
const _Actions := preload("res://scripts/phase1/Phase1Actions.gd")
var actions: Node
var action := ""
var action_n := 0
var layout_override := false
var layout_window := Vector2i.ZERO
var layout_safe := Rect2i()
var layout_viewport := Vector2.ZERO
var _save_wait := 0.0
var _import_text := ""


func _ready() -> void:
	doc = Phase1Config.load_doc()


func attach(main: Node) -> void:
	if active:
		return
	host = main
	active = true
	if Sim:
		Phase1Registry.ensure(Sim.state)
		if not Sim.state.has("phase1_plots"):
			Sim.state["phase1_plots"] = ["empty", "empty", "empty", "empty"]
		if int(Sim.state.get("last_tick_ts", 0)) <= 0:
			Sim.state["last_tick_ts"] = int(Time.get_unix_time_from_system() * 1000.0)
	var old_hud: Node = main.get("hud")
	if old_hud is CanvasItem:
		(old_hud as CanvasItem).visible = false
	var old := main.get_node_or_null("EcosystemHud")
	if old:
		old.visible = false
	world = Phase1World.new()
	world.name = "Phase1World"
	var exterior: Node = main.get("_hd2d_exterior")
	if exterior == null:
		exterior = main
	exterior.add_child(world)
	world.build(exterior)
	hud = Phase1Hud.new()
	hud.name = "Phase1Hud"
	main.add_child(hud)
	hud.build()
	actions = _Actions.new()
	actions.name = "Phase1Actions"
	add_child(actions)
	actions.call("bind", main, world.zones)
	_apply_visual()
	if main.has_method("phase1_hold_opening"):
		main.phase1_hold_opening()
	var away := OfflineIdleEngine.settle(Sim.state, int(Time.get_unix_time_from_system() * 1000.0))
	if bool(away.get("show", false)):
		_show_idle(away)
	mark("boot")


func _process(dt: float) -> void:
	if not active:
		return
	_save_wait += dt
	if _save_wait >= 10.0:
		_save_wait = 0.0
		_save()


func mark(kind: String) -> void:
	action = kind
	action_n += 1
	_save_wait = 0.0
	_save()
	if hud:
		hud.refresh()


func toast(text: String) -> void:
	if hud:
		hud.show_toast(text)


func open_info() -> void:
	var pet := Phase1Registry.primary(Sim.state)
	var care: Dictionary = pet.get("care", {})
	var stats: Dictionary = pet.get("stats", {})
	var spec := Phase1Config.species(doc, str(pet.get("species_id", "baby")))
	hud.show_modal("寵物資料", "HP %d\n力量 %d  身手 %d  耐力 %d\nLv %d  EXP %d\n被動 %s" % [
		int(care.get("體力", 0)), int(stats.get("力量", 1)), int(stats.get("身手", 1)), int(stats.get("耐力", 1)),
		int(stats.get("lv", 1)), int(stats.get("exp", 0)), str(spec.get("passive", ""))
	])
	mark("info")


func open_feed() -> void:
	hud.feed_row.visible = true
	hud.train_row.visible = false
	hud.map_row.visible = false
	mark("feed_open")


func feed(fid: String) -> void:
	var food := Phase1Config.food(doc, fid)
	var pet := Phase1Registry.primary(Sim.state)
	var care: Dictionary = pet.get("care", {})
	care["飽食"] = mini(100, int(care.get("飽食", 0)) + int(food.get("hunger", 0)))
	care["心情"] = mini(100, int(care.get("心情", 0)) + int(food.get("mood", 0)))
	care["親密"] = mini(100, int(care.get("親密", 0)) + int(food.get("bond", 0)))
	care["體力"] = mini(100, int(care.get("體力", 0)) + int(food.get("stamina", 0)))
	pet["care"] = care
	var stats: Dictionary = pet.get("stats", {})
	stats["力量"] = int(stats.get("力量", 1)) + int(food.get("power", 0))
	pet["stats"] = stats
	Phase1Registry.put(Sim.state, pet)
	if actions:
		actions.call("play_feed", str(food.get("zh", "")))
	if hud:
		hud.show_emote("好好味")
	mark("feed")


func clean() -> void:
	var cleaned := 0
	if Sim and Sim.has_method("clean_one"):
		while Sim.clean_one():
			cleaned += 1
			if cleaned > 8:
				break
	var pet := Phase1Registry.primary(Sim.state)
	var care: Dictionary = pet.get("care", {})
	care["心情"] = mini(100, int(care.get("心情", 0)) + 8)
	pet["care"] = care
	Phase1Registry.put(Sim.state, pet)
	_hide_rows()
	if actions:
		actions.call("play_clean")
	if hud:
		hud.show_emote("清潔")
	mark("clean")


func pat() -> void:
	var pet := Phase1Registry.primary(Sim.state)
	var care: Dictionary = pet.get("care", {})
	care["心情"] = mini(100, int(care.get("心情", 0)) + 6)
	care["親密"] = mini(100, int(care.get("親密", 0)) + 6)
	pet["care"] = care
	Phase1Registry.put(Sim.state, pet)
	_hide_rows()
	if actions:
		actions.call("play_pat")
	if hud:
		hud.show_emote("心")
	mark("pat")


func open_train() -> void:
	hud.train_row.visible = true
	hud.feed_row.visible = false
	hud.map_row.visible = false
	mark("train_open")


func train(stat: String) -> void:
	var pet := Phase1Registry.primary(Sim.state)
	var care: Dictionary = pet.get("care", {})
	if int(care.get("體力", 0)) < 8:
		toast("體力不足")
		mark("train_block")
		return
	care["體力"] = int(care.get("體力", 0)) - 8
	pet["care"] = care
	var stats: Dictionary = pet.get("stats", {})
	stats[stat] = int(stats.get(stat, 1)) + 1
	stats["exp"] = int(stats.get("exp", 0)) + 4
	stats["lv"] = 1 + int(stats["exp"]) / 20
	pet["stats"] = stats
	Phase1Registry.put(Sim.state, pet)
	_hide_rows()
	if actions:
		actions.call("play_train", stat)
	if hud:
		hud.show_emote(stat)
	mark("train")


func open_map() -> void:
	hud.map_row.visible = not hud.map_row.visible
	hud.feed_row.visible = false
	hud.train_row.visible = false
	mark("map")


func go_zone(zone_id: String) -> void:
	var pet := Phase1Registry.primary(Sim.state)
	pet["zone_id"] = zone_id
	Phase1Registry.put(Sim.state, pet)
	_hide_rows()
	if host and host.has_method("phase1_glide_to") and world:
		host.phase1_glide_to(world.look_for(zone_id))
	if actions and world:
		actions.call("jog_to", world.anchor_for(zone_id))
	var spec := Phase1Config.zone(doc, zone_id)
	toast(str(spec.get("zh", zone_id)))
	mark("zone")


func follow_pet() -> void:
	if host and host.get("pet") and host.has_method("phase1_follow"):
		host.phase1_follow(host.get("pet"))
	if Ecosystem:
		Ecosystem.follow_pet("tuanrong")
	toast("跟寵")
	mark("follow")


func set_collapsed(v: bool) -> void:
	if hud:
		hud.set_collapsed(v)
	mark("collapse" if v else "expand")


func toggle_drawer() -> void:
	if hud:
		hud.drawer.visible = not hud.drawer.visible
	mark("drawer")


func idle_hour() -> void:
	var now := int(Time.get_unix_time_from_system() * 1000.0)
	var report := OfflineIdleEngine.settle(Sim.state, now, 3600000)
	_show_idle(report)
	if world:
		world._refresh_beds()
	mark("idle")


func grant_debug() -> void:
	var paid := 50
	if Ecosystem and Ecosystem.has_method("grant_shards"):
		paid = int(Ecosystem.grant_shards(50, "phase1_debug"))
	elif CollectionSystem:
		paid = int(CollectionSystem.add_shards(50, "phase1_debug"))
	toast("+%d 碎" % paid)
	mark("grant")


func force_evo() -> void:
	var rec := EvolutionEngine.force_next(doc, Sim.state)
	_apply_visual()
	if hud and bool(rec.get("ok", false)):
		hud.show_modal("進化完成！", "%s\n%s" % [str(rec.get("name", "")), EvolutionEngine.zh(doc, str(rec.get("stage", "")))])
	mark("evo")


func spawn_pet() -> void:
	var baby := Phase1Registry.add_child_pet(Sim.state)
	toast("新寵物 %s" % str(baby.get("id", "")))
	mark("egg")


func export_save() -> void:
	_import_text = JSON.stringify(Sim.state)
	if hud:
		hud.show_import(_import_text)
	mark("export")


func import_save() -> void:
	if hud:
		hud.show_import(_import_text)
	mark("import")


func close_modal() -> void:
	if hud:
		hud.modal.visible = false
	mark("close")


func confirm_modal() -> void:
	if hud and hud.import_box.visible:
		var parsed: Variant = JSON.parse_string(hud.import_box.text)
		if parsed is Dictionary:
			var keep_shards := 0
			if CollectionSystem:
				keep_shards = int(CollectionSystem.stardust())
			Sim.state = parsed
			if not Sim.state.has("wallet"):
				Sim.state["wallet"] = {"stardust": keep_shards}
			Phase1Registry.ensure(Sim.state)
			toast("已匯入")
	if hud:
		hud.modal.visible = false
	mark("confirm")


func reset_profile() -> void:
	var shards := 0
	if CollectionSystem:
		shards = int(CollectionSystem.stardust())
	Sim.state["pet_registry"] = {}
	Sim.state["phase1_plots"] = ["empty", "empty", "empty", "empty"]
	Sim.state["last_tick_ts"] = int(Time.get_unix_time_from_system() * 1000.0)
	Phase1Registry.ensure(Sim.state)
	if CollectionSystem and CollectionSystem.has_method("add_shards") and shards > int(CollectionSystem.stardust()):
		CollectionSystem.add_shards(shards - int(CollectionSystem.stardust()), "phase1_keep")
	_apply_visual()
	toast("已重置測試檔")
	mark("reset")


func try_world_tap(screen: Vector2) -> bool:
	if host == null or world == null or world.zones == null:
		return false
	var cam := host.get("cam") as Camera3D
	if cam == null:
		return false
	var from := cam.project_ray_origin(screen)
	var dir := cam.project_ray_normal(screen)
	var q := PhysicsRayQueryParameters3D.create(from, from + dir * 800.0)
	q.collide_with_areas = true
	q.collide_with_bodies = true
	var space: PhysicsDirectSpaceState3D = host.get_world_3d().direct_space_state
	var hit: Dictionary = space.intersect_ray(q)
	var col: Object = hit.get("collider")
	if col is Node and (col as Node).has_meta("bed"):
		world.tap_bed(int((col as Node).get_meta("bed")))
		return true
	if col is Node and (col as Node).has_meta("spot"):
		var spot := str((col as Node).get_meta("spot"))
		if spot == "stove":
			act_stove()
		elif spot == "post":
			act_post()
		elif spot == "prairie":
			act_forage()
		else:
			return false
		return true
	return false


func replay(kind: String) -> void:
	if host and kind == "post" and host.has_method("replay_post"):
		host.replay_post()
	elif host and host.has_method("replay_hunt"):
		host.replay_hunt()
	mark("replay")


func _show_idle(report: Dictionary) -> void:
	if hud == null:
		return
	hud.feed_row.visible = false
	hud.train_row.visible = false
	hud.map_row.visible = false
	hud.drawer.visible = false
	hud.show_modal("離線收益結算", "離開 %d 秒\n星星碎 +%d\n經驗 +%d\n農圃生長 %d" % [
		int(report.get("seconds", 0)), int(report.get("shards", 0)), int(report.get("exp", 0)), int(report.get("crops", 0))
	])


func _apply_visual() -> void:
	if host == null:
		return
	var pet := host.get("pet") as Node3D
	if pet == null or Sim == null:
		return
	var row := Phase1Registry.primary(Sim.state)
	var col := EvolutionEngine.tint_of(doc, str(row.get("species_id", "baby")))
	var sc := EvolutionEngine.scale_of(doc, str(row.get("species_id", "baby")))
	if pet is GeometryInstance3D:
		(pet as GeometryInstance3D).material_overlay = null
	var sprite := pet.get_node_or_null("Sprite3D") as Sprite3D
	if sprite == null:
		sprite = pet.get_node_or_null("Hd2dCoat") as Sprite3D
	if sprite:
		sprite.modulate = col
	pet.scale = Vector3(sc, sc, sc)


func _hide_rows() -> void:
	if hud == null:
		return
	hud.feed_row.visible = false
	hud.train_row.visible = false
	hud.map_row.visible = false


func tend_bed(bed_at: Vector3, harvest: bool) -> void:
	if actions:
		actions.call("play_garden", bed_at, harvest)
	if hud:
		hud.show_emote("收成" if harvest else "澆水")


func act_stove() -> void:
	if actions and world:
		actions.call("play_stove", world.stove_pos())
	_spark_reward("灶")
	mark("stove")


func act_post() -> void:
	if actions and world:
		actions.call("play_post", world.post_pos())
	_spark_reward("郵")
	mark("post")


func act_forage() -> void:
	if actions and world:
		actions.call("play_forage", world.prairie_pos())
	_spark_reward("花")
	mark("forage")


func _spark_reward(word: String) -> void:
	if Ecosystem and Ecosystem.has_method("grant_shards"):
		Ecosystem.grant_shards(1, "phase1_play")
	if hud:
		hud.show_emote(word)


func _save() -> void:
	if Sim and Sim.has_method("_save_now"):
		Sim._save_now()
