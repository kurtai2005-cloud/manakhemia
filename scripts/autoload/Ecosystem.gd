extends Node
## Living ecosystem v1. Every tunable number is read from data/ecosystem_v1.json.

const DATA_PATH := "res://data/ecosystem_v1.json"
const MEASURE_PATH := "res://art/ecosystem_v1/series2_measurements.json"
const ART_ROOT := "res://art/ecosystem_v1/"

var cfg: Dictionary = {}
var follow_id := ""
var follow_pet_id := ""
var patrol_label := ""
var current_zone := "garden"
var rug_phase := ""
var _main: Node = null
var _rug_left := 0.0
var _fusion_t := 0.0
var _fusion_fade := 0.0
var _fusion_out := false


var layout_override := false
var layout_window := Vector2i.ZERO
var layout_safe := Rect2i()
var layout_viewport := Vector2.ZERO


func _ready() -> void:
	Vc27Fonts.ensure()
	cfg = _load_json(DATA_PATH)
	print("ECO_READY keys=", cfg.size(), " exists=", FileAccess.file_exists(DATA_PATH))


func _load_json(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		push_error("missing " + path)
		return {}
	var raw := FileAccess.get_file_as_string(path)
	var parsed: Variant = JSON.parse_string(raw)
	if parsed is Dictionary:
		return parsed
	push_error("bad json " + path + " len=" + str(raw.length()))
	return {}


func preview_now() -> bool:
	return SaveSystem != null and SaveSystem.has_method("is_preview") and SaveSystem.is_preview()


func migrate(state: Dictionary) -> void:
	if state.is_empty() or cfg.is_empty():
		return
	var mig: Dictionary = cfg.get("save_migration", {})
	var cur := int(state.get("ecosystem_schema", 0))
	if cur >= int(mig.get("schema_version", 1)):
		_sync_mirror(state)
		return
	var defaults: Dictionary = mig.get("defaults_if_missing", {})
	for k in defaults.keys():
		if state.has(k) and k != "unique_collect" and k != "pets":
			continue
		if k == "unique_collect" or k == "pets":
			continue
		state[k] = (defaults[k] as Variant).duplicate(true) if defaults[k] is Dictionary or defaults[k] is Array else defaults[k]
	if not state.has("pets") or not (state["pets"] is Array) or (state["pets"] as Array).is_empty():
		var pet := {
			"id": "tuanrong",
			"stage": str(state.get("stage", "egg")),
			"form": str(state.get("form", "")),
			"needs": (state.get("needs", {}) as Dictionary).duplicate(true),
			"combat": _initial_combat(),
			"fusion_state": "none",
			"route": str(state.get("form", "lumi")),
		}
		state["pets"] = [pet]
	_sync_mirror(state)
	state["unique_collect"] = _recompute_unique(state)
	if not state.has("family_tree"):
		state["family_tree"] = {"nodes": [{"id": "tuanrong"}], "edges": []}
	state["ecosystem_schema"] = int(mig.get("schema_version", 1))


func _initial_combat() -> Dictionary:
	var init: Dictionary = cfg.get("combat_stats", {}).get("initial", {})
	return {"力量": float(init.get("力量", 1)), "身手": float(init.get("身手", 1)), "耐力": float(init.get("耐力", 1))}


func _sync_mirror(state: Dictionary) -> void:
	var pets: Array = state.get("pets", [])
	if pets.is_empty() or not (pets[0] is Dictionary):
		return
	var pet: Dictionary = pets[0]
	if pet.has("combat"):
		state["combat"] = (pet["combat"] as Dictionary).duplicate(true)
	elif state.has("combat"):
		pet["combat"] = (state["combat"] as Dictionary).duplicate(true)
	_clamp_combat(pet["combat"] if pet.has("combat") else state.get("combat", {}))


func _clamp_combat(c: Dictionary) -> void:
	var live: Array = cfg.get("combat_stats", {}).get("live_pet_clamp", [1, 10])
	var lo := float(live[0])
	var hi := float(live[1])
	for k in ["力量", "身手", "耐力"]:
		c[k] = clampf(float(c.get(k, 1)), lo, hi)


func _recompute_unique(state: Dictionary) -> int:
	var col: Dictionary = state.get("collection", {})
	var n := 0
	for bucket in ["discovered", "critters", "forms", "badges", "fruits"]:
		var d: Dictionary = col.get(bucket, {})
		for k in d.keys():
			if d[k]:
				n += 1
	if bool(col.get("discovered", {}).get("glow_berry", false)):
		pass
	return n


func grant_shards(amount: int, source: String) -> int:
	if Sim == null or Sim.state.is_empty():
		return 0
	var caps: Dictionary = cfg.get("existing_caps_unchanged", {})
	var jt_cap := int(caps.get("jobs_and_trips_daily", 12))
	var total_cap := int(caps.get("stardust_daily_total", 47))
	var ledger: Dictionary = Sim.state.get("daily_ledger", {})
	var day := Sim._day_key() if Sim.has_method("_day_key") else ""
	if str(ledger.get("day_key", "")) != day:
		ledger = {"day_key": day, "jt_shards": 0, "total_shards": 0, "pet_mode": {}, "pet_paid_count": {}}
	var room_jt := jt_cap - int(ledger.get("jt_shards", 0))
	var room_total := total_cap - int(ledger.get("total_shards", 0))
	var pay := mini(amount, mini(room_jt, room_total))
	if pay < 0:
		pay = 0
	ledger["jt_shards"] = int(ledger.get("jt_shards", 0)) + pay
	ledger["total_shards"] = int(ledger.get("total_shards", 0)) + pay
	Sim.state["daily_ledger"] = ledger
	if pay > 0 and CollectionSystem:
		CollectionSystem.add_shards(pay, source)
	return pay


func observe_patrol() -> Dictionary:
	var rules: Dictionary = cfg.get("reward_rules", {})
	patrol_label = str(rules.get("already_worked_prairie_label_zh", ""))
	if Sim and not Sim.state.is_empty():
		var col: Dictionary = Sim.state.get("collection", {})
		var fruits: Dictionary = col.get("fruits", {})
		fruits["patrol_seed"] = int(fruits.get("patrol_seed", 0)) + 1
		col["fruits"] = fruits
		Sim.state["collection"] = col
		Sim.state["seeds"] = int(Sim.state.get("seeds", 0)) + 1
	return {"ok": true, "shards": 0, "label": patrol_label}


func power_interval_mul(stat: float) -> float:
	var f: Dictionary = cfg.get("combat_stats", {}).get("formulas", {}).get("power_pounce_interval_mul", {})
	var v := 1.0 - (stat - 1.0) * 0.03
	return clampf(v, float(f.get("min", 0.73)), float(f.get("max", 1.0)))


func agility_miss(stat: float) -> float:
	var f: Dictionary = cfg.get("combat_stats", {}).get("formulas", {}).get("agility_miss_rate", {})
	var cut := minf(0.15, (stat - 1.0) * 0.015)
	var v := float(f.get("base_miss_rate", 0.25)) - cut
	return clampf(v, float(f.get("min", 0.05)), float(f.get("max", 0.35)))


func stamina_stay(stat: float) -> float:
	var f: Dictionary = cfg.get("combat_stats", {}).get("formulas", {}).get("stamina_deep_stay_sec", {})
	var v := 24.0 + (stat - 1.0) * 4.0
	return clampf(v, float(f.get("min", 24)), float(f.get("max", 60)))


func grow_combat(pet: Dictionary, key: String, delta: float) -> void:
	var stats: Dictionary = cfg.get("combat_stats", {})
	var cap := float(stats.get("daily_growth_cap_per_stat_preview", 9.0) if preview_now() else stats.get("daily_growth_cap_per_stat_normal", 1.0))
	var gained: Dictionary = pet.get("combat_gained_today", {})
	var room := cap - float(gained.get(key, 0.0))
	var add := minf(delta, maxf(0.0, room))
	var combat: Dictionary = pet.get("combat", _initial_combat())
	combat[key] = float(combat.get(key, 1.0)) + add
	_clamp_combat(combat)
	pet["combat"] = combat
	gained[key] = float(gained.get(key, 0.0)) + add
	pet["combat_gained_today"] = gained
	if Sim:
		_sync_mirror(Sim.state)


func floor_needs(needs: Dictionary) -> void:
	var dead: Dictionary = cfg.get("combat_stats", {}).get("anti_deadlock", {})
	var hf := float(dead.get("miss_or_low_stamina_never_drains_hunger_below", 20))
	var ef := float(dead.get("miss_or_low_stamina_never_drains_energy_below", 20))
	needs["hunger"] = maxf(float(needs.get("hunger", 100)), hf)
	needs["energy"] = maxf(float(needs.get("energy", 100)), ef)


func zone_unlocked(zone_id: String, state: Dictionary) -> bool:
	var zones: Dictionary = cfg.get("zones", {})
	var starting: Array = zones.get("starting_always_on", [])
	if zone_id in starting:
		return true
	var spec: Dictionary = zones.get("unlockable", {}).get(zone_id, {})
	if spec.is_empty():
		return false
	var prev: Array = spec.get("requires_previous", [])
	for p in prev:
		if not zone_unlocked(str(p), state):
			return false
	var mul := float(cfg.get("preview", {}).get("threshold_mul", 1.0)) if preview_now() else 1.0
	var all: Dictionary = spec.get("require_all", {})
	if not _need_ok(all, state, mul, spec):
		return false
	var any: Dictionary = spec.get("require_any", {})
	if any.is_empty():
		return true
	for k in any.keys():
		var one := {k: any[k]}
		if _need_ok(one, state, mul, spec):
			return true
	return false


func _need_ok(need: Dictionary, state: Dictionary, mul: float, spec: Dictionary) -> bool:
	for k in need.keys():
		var want := float(need[k]) * mul
		if _metric(str(k), state, spec) + 0.0001 < want:
			return false
	return true


func _metric(key: String, state: Dictionary, spec: Dictionary) -> float:
	if key == "day_min":
		return float(state.get("age_day", 0))
	if key == "pets":
		return float((state.get("pets", []) as Array).size())
	if key == "lifetime_shards":
		return float(state.get("wallet", {}).get("stardust", 0))
	if key == "hunts":
		return float(state.get("lifetime_hunts", 0))
	if key == "seeds":
		return float(state.get("seeds", 0))
	if key == "empty_pantry":
		return float(state.get("empty_pantry_days", 0))
	if key == "paid_actions":
		return float(state.get("lifetime_paid", 0))
	if key == "unique_collect":
		return float(state.get("unique_collect", 0))
	if key in ["力量", "身手", "耐力"]:
		return _best_stat(state, key, str(spec.get("stat_check_scope", "")))
	return 0.0


func _best_stat(state: Dictionary, key: String, scope: String) -> float:
	var best := 0.0
	for p in state.get("pets", []):
		if not (p is Dictionary):
			continue
		if scope == "best_adult_pet" and str(p.get("stage", "")) != "adult" and str(p.get("stage", "")) != "elder":
			continue
		best = maxf(best, float(p.get("combat", {}).get(key, 0)))
	if best <= 0.0 and state.has("combat"):
		best = float(state.get("combat", {}).get(key, 0))
	return best


func fusion_stat(a: float, b: float, bonus: float) -> float:
	var hi := float(cfg.get("combat_stats", {}).get("live_pet_clamp", [1, 10])[1])
	return minf(hi, maxf(a, b) + bonus)


func begin_fusion(now_ms: int) -> Dictionary:
	if Sim == null:
		return {"ok": false}
	var pets: Array = Sim.state.get("pets", [])
	if pets.size() < 2:
		return {"ok": false, "reason": "need_two"}
	var fus: Dictionary = cfg.get("fusion", {})
	var dur := int(fus.get("duration", {}).get("preview_sec", 45)) if preview_now() else int(float(fus.get("duration", {}).get("normal_hours", 2)) * 3600.0)
	var cool := int(fus.get("cooldown", {}).get("preview_sec", 90)) if preview_now() else int(float(fus.get("cooldown", {}).get("normal_hours", 8)) * 3600.0)
	var rec := {
		"active": true,
		"pet_ids": [str(pets[0].get("id", "a")), str(pets[1].get("id", "b"))],
		"started_at_ms": now_ms,
		"ends_at_ms": now_ms + dur * 1000,
		"cooldown_until_ms": now_ms + (dur + cool) * 1000,
	}
	pets[0]["fusion_state"] = "fused"
	pets[1]["fusion_state"] = "fused"
	Sim.state["pets"] = pets
	Sim.state["fusion"] = rec
	return {"ok": true, "fusion": rec}


func recover_fusion(now_ms: int) -> void:
	if Sim == null:
		return
	var fus: Dictionary = Sim.state.get("fusion", {})
	if not bool(fus.get("active", false)):
		return
	var ids: Array = fus.get("pet_ids", [])
	var missing := ids.size() != 2
	var pets: Array = Sim.state.get("pets", [])
	if not missing:
		for id in ids:
			var found := false
			for p in pets:
				if p is Dictionary and str(p.get("id", "")) == str(id):
					found = true
			if not found:
				missing = true
	if missing or now_ms >= int(fus.get("ends_at_ms", 0)):
		for p in pets:
			if p is Dictionary:
				p["fusion_state"] = "none"
		fus["active"] = false
		Sim.state["fusion"] = fus
		Sim.state["pets"] = pets


func crop_phase_sec(tide: bool) -> float:
	var farm: Dictionary = cfg.get("farm", {})
	var key := "preview" if preview_now() else "normal"
	var sec := float(farm.get("crop_phase_sec", {}).get(key, 3600))
	if tide:
		sec *= float(farm.get("tide_on_farm_mul", cfg.get("combo_bonuses", {}).get("tide_on_farm", {}).get("crop_phase_sec_mul", 1)))
	return sec


func advance_plot(plot: Dictionary, dt: float, tide: bool) -> void:
	plot["age"] = float(plot.get("age", 0.0)) + dt
	var phase := crop_phase_sec(tide)
	var stages: Array = cfg.get("farm", {}).get("stages", ["seed", "sprout", "mature"])
	var idx := stages.find(str(plot.get("stage", "seed")))
	if idx < 0:
		idx = 0
	if float(plot["age"]) >= phase and idx < stages.size() - 1:
		plot["stage"] = str(stages[idx + 1])
		plot["age"] = 0.0


func rug_exit(hunger: float, energy: float, bedtime: bool) -> bool:
	var rules: Dictionary = cfg.get("rug_leaf_rules", {})
	if hunger <= float(rules.get("exit_immediately_on_hunger_lte", 25)):
		return true
	if energy <= float(rules.get("exit_immediately_on_energy_lte", 25)):
		return true
	return bedtime and bool(rules.get("exit_immediately_on_bedtime", true))


func walk_speed_mul(motion: float) -> float:
	var qa: Dictionary = cfg.get("qa_personality_assertions", {})
	var thr := float(qa.get("axis_threshold_abs", 5))
	var pair: Array = qa.get("motion_high_vs_low", {}).get("walk_speed_mul", [1.2, 0.85])
	if motion >= thr:
		return float(pair[0])
	if motion <= -thr:
		return float(pair[1])
	return 1.0


func action_interval(motion: float, work: float) -> float:
	var base := float(cfg.get("division_weights", {}).get("action_rest_interval_sec", {}).get("base", 18))
	var spec: Dictionary = cfg.get("division_weights", {}).get("action_rest_interval_sec", {})
	var v := base
	var thr := float(cfg.get("qa_personality_assertions", {}).get("axis_threshold_abs", 5))
	if motion >= thr:
		v *= float(spec.get("energetic_mul", 0.85))
	elif motion <= -thr:
		v *= float(spec.get("quiet_mul", 1.15))
	if work >= thr:
		v *= float(spec.get("diligent_mul", 0.9))
	elif work <= -thr:
		v *= float(spec.get("lazy_mul", 1.2))
	return v


func kid_offset_y(form_id: String) -> float:
	var doc := _load_json(MEASURE_PATH)
	var groups: Dictionary = doc.get("offset_groups", {})
	for k in groups.keys():
		var ids: Array = groups[k]
		if form_id in ids:
			if str(k).find("-7") >= 0:
				return -7.0
			return -6.0
	return -6.0


func station_world(building_id: String) -> Vector3:
	if building_id == "kitchen":
		return Vector3(78, 0, -18)
	if building_id == "post":
		return Vector3(108, 0, -18)
	return Vector3.ZERO


func stop_follow() -> void:
	follow_id = ""
	follow_pet_id = ""
	_sync_portrait()


func follow_pet(pet_id: String) -> void:
	follow_id = pet_id
	follow_pet_id = pet_id
	_sync_portrait()


func _process(dt: float) -> void:
	if _main == null:
		return
	_tick_kids(dt)
	_tick_partner(dt)
	_tick_fusion_visual(dt)
	_refresh_pantry()
	var card := _main.get_node_or_null("EcosystemHud/Root/CombatCard")
	if card is Label:
		(card as Label).text = _combat_line()
	var prairie := _main.get_node_or_null("EcosystemHud/Root/PrairieObserve")
	if prairie is Control:
		prairie.visible = current_zone == "prairie_edge" or current_zone == "zone_prairie_deep"


func present(main: Node) -> void:
	_main = main
	_ground_prop(main, "WorkOutdoorStove", "props/work_outdoor_stove_table.png", station_world("kitchen"))
	_ground_prop(main, "WorkOutdoorPost", "props/work_outdoor_post_rack.png", station_world("post"))
	_ground_prop(main, "FarmPlot", "props/farm_plot_empty.png", Vector3(40, 0, 30))
	_ground_prop(main, "PantryPile", "props/storage_fruit_pile_low.png", Vector3(20, 0, 36))
	_ground_prop(main, "FamilyWall", "props/family_wall_board.png", Vector3(-20, 0, 48))
	_frame_slots(main)
	_partner(main)
	_kids(main)
	_hud(main)
	set_plot_stage("empty")


func set_plot_stage(stage: String) -> void:
	if _main == null:
		return
	var plot := _main.get_node_or_null("FarmPlot") as Sprite3D
	if plot == null:
		return
	var file := "props/farm_plot_empty.png"
	if stage == "seed":
		file = "props/farm_crop_stage1_sprout.png"
	elif stage == "sprout":
		file = "props/farm_crop_stage2_growing.png"
	elif stage == "mature":
		file = "props/farm_crop_stage3_ripe.png"
	var tex := load(ART_ROOT + file) as Texture2D
	if tex == null:
		return
	plot.texture = tex
	plot.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR
	var h := float(tex.get_height())
	plot.offset.y = _sole(file) - h * 0.5
	plot.position.y = 0.0


func _sole(file: String) -> float:
	var doc := _load_json(ART_ROOT + "MANIFEST.json")
	for item in doc.get("items", []):
		if item is Dictionary and str(item.get("path", "")) == file:
			return float(item.get("sole_edge", 0))
	return 0.0


func _refresh_pantry() -> void:
	if _main == null or Sim == null:
		return
	var pile := _main.get_node_or_null("PantryPile") as Sprite3D
	if pile == null:
		return
	var n := 0
	var fruits: Dictionary = Sim.state.get("collection", {}).get("fruits", {})
	for k in fruits.keys():
		n += int(fruits[k])
	var file := "props/storage_fruit_pile_full.png" if n >= 3 else "props/storage_fruit_pile_low.png"
	var tex := load(ART_ROOT + file) as Texture2D
	if tex:
		pile.texture = tex
		pile.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR


func drive_rug(walker: Walker, dt: float) -> bool:
	if walker == null or Sim == null:
		return false
	if str(Sim.state.get("house", {}).get("placed", {}).get("rug", "")) != "rug_leaf":
		return false
	var needs: Dictionary = Sim.state.get("needs", {})
	var hunger := float(needs.get("hunger", 100))
	var energy := float(needs.get("energy", 100))
	var hour := 12.0
	if TimeService:
		hour = float(TimeService.hour_of())
	var bedtime := hour >= 21.0 or hour < 3.0
	if rug_exit(hunger, energy, bedtime):
		if rug_phase != "":
			_rug_stop(walker)
		return false
	if rug_phase == "roll":
		_rug_left -= dt
		walker.global_position = _rug_point(walker)
		walker.rotation.y += dt * 2.2
		if _rug_left <= 0.0:
			_rug_stop(walker)
		return true
	if rug_phase == "walk":
		var spot := Vector3(8, 0, 18)
		if walker.global_position.distance_to(spot) < 1.6:
			rug_phase = "roll"
			var span: Array = cfg.get("rug_leaf_rules", {}).get("roll_duration_sec", [4, 6])
			_rug_left = float(span[0])
			walker.clear_errand()
		return true
	var cool := float(cfg.get("rug_leaf_rules", {}).get("cooldown_sec_preview" if preview_now() else "cooldown_sec_normal", 90))
	var last := float(Sim.state.get("rug_last_ms", 0))
	var now := float(Time.get_ticks_msec())
	if last > 0.0 and now - last < cool * 1000.0:
		return false
	rug_phase = "walk"
	walker.brain_driven = false
	walker.set_errand(Vector3(8, 0, 18))
	return true


func _rug_point(walker: Walker) -> Vector3:
	var t := float(Time.get_ticks_msec()) / 1000.0
	return Vector3(8.0 + sin(t * 3.0) * 1.2, 0.0, 18.0 + cos(t * 2.0) * 0.6)


func _rug_stop(walker: Walker) -> void:
	rug_phase = ""
	walker.rotation.y = 0.0
	walker.brain_driven = true
	walker.clear_errand()
	if Sim:
		Sim.state["rug_last_ms"] = Time.get_ticks_msec()
	if walker.has_method("play_live_clip"):
		walker.play_live_clip("idle_quiet", true)


func _tick_fusion_visual(dt: float) -> void:
	if _main == null or Sim == null:
		return
	if bool(Sim.state.get("fusion", {}).get("active", false)):
		recover_fusion(Time.get_ticks_msec())
	var pet := _main.get("pet") as Node3D
	if pet == null:
		return
	var active := bool(Sim.state.get("fusion", {}).get("active", false))
	var echo := _main.get_node_or_null("FusionEcho") as Sprite3D
	var halo := _main.get_node_or_null("FusionHalo") as Sprite3D
	if active and echo == null:
		_fusion_fade = 0.0
		_fusion_out = false
		echo = Sprite3D.new()
		echo.name = "FusionEcho"
		echo.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR
		echo.centered = true
		echo.pixel_size = 1.0
		_main.add_child(echo)
		halo = Sprite3D.new()
		halo.name = "FusionHalo"
		halo.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR
		var halo_tex := load(ART_ROOT + "ui/ui_pet_portrait_frame.png") as Texture2D
		halo.texture = halo_tex
		halo.pixel_size = 0.7
		_main.add_child(halo)
	if not active and echo != null and not _fusion_out:
		_fusion_out = true
		_fusion_fade = 0.0
	if echo == null:
		return
	var coat := pet.get_node_or_null("Hd2dCoat") as Sprite3D
	if coat and coat.texture:
		echo.texture = coat.texture
	elif pet is Sprite3D and (pet as Sprite3D).texture:
		echo.texture = (pet as Sprite3D).texture
	_fusion_t += dt
	var wave := 0.5 + 0.5 * sin(TAU * _fusion_t / 1.6)
	var gold := Color("F2D98A")
	var cyan := Color("7EC8C3")
	var tint := gold.lerp(cyan, wave)
	var strength := lerpf(0.28, 0.40, wave)
	if _fusion_out:
		_fusion_fade += dt
		var a := clampf(1.0 - _fusion_fade / 0.40, 0.0, 1.0)
		echo.modulate = Color(tint.r, tint.g, tint.b, 0.45 * a)
		if halo:
			halo.modulate.a = lerpf(0.22, 0.48, wave) * a
		if _fusion_fade >= 0.40:
			echo.queue_free()
			if halo:
				halo.queue_free()
		return
	_fusion_fade = minf(_fusion_fade + dt, 0.35)
	var inn := clampf(_fusion_fade / 0.35, 0.0, 1.0)
	echo.global_position = pet.global_position + Vector3(6, 0, 0)
	echo.modulate = Color(tint.r, tint.g, tint.b, 0.45 * inn * strength / 0.28)
	echo.modulate.a = 0.45 * inn
	if halo:
		halo.global_position = pet.global_position + Vector3(0, 1, 0)
		halo.modulate = Color(tint.r, tint.g, tint.b, lerpf(0.22, 0.48, wave) * inn)


func _ground_prop(main: Node, node_name: String, file: String, pos: Vector3) -> void:
	if main.get_node_or_null(node_name) != null:
		return
	var tex := load(ART_ROOT + file) as Texture2D
	if tex == null:
		return
	var s := Sprite3D.new()
	s.name = node_name
	s.texture = tex
	s.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR
	s.pixel_size = 1.0
	s.centered = true
	s.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
	s.position = pos
	s.position.y = 0.0
	s.offset.y = _sole(file) - float(tex.get_height()) * 0.5
	main.add_child(s)


func _frame_slots(main: Node) -> void:
	var board := main.get_node_or_null("FamilyWall") as Node3D
	if board == null:
		return
	for i in range(3):
		var slot := Sprite3D.new()
		slot.name = "FamilyFrame_%d" % i
		var tex := load(ART_ROOT + "props/family_wall_frame_slot.png") as Texture2D
		slot.texture = tex
		slot.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR
		slot.centered = true
		slot.pixel_size = 0.45
		slot.position = board.position + Vector3(-8 + i * 8, 18, 1)
		main.add_child(slot)


func _partner(main: Node) -> void:
	var body := Sprite3D.new()
	body.name = "PartnerPet"
	var tex := load("res://art-pet/sprites/series2/A2_idle.png") as Texture2D
	body.texture = tex
	body.centered = true
	body.pixel_size = 1.0
	body.position = Vector3(12, 29, 8)
	body.set_meta("home", body.position)
	main.add_child(body)


func set_kid_action(letter: String, action: String) -> void:
	if _main == null:
		return
	var body := _main.get_node_or_null("KidBody_%s" % letter) as Sprite3D
	if body == null:
		return
	var form := letter + "1"
	if letter == "B":
		form = "B1"
	var tex := load("res://art-pet/sprites/series2/%s_%s.png" % [form, action]) as Texture2D
	if tex:
		body.texture = tex
	body.offset.y = kid_offset_y(form)
	body.set_meta("action", action)


func _tick_kids(dt: float) -> void:
	if _main == null:
		return
	var letters := ["A", "B", "C", "D", "E", "F", "G", "H"]
	var actions := ["idle", "walk", "eat", "sleep", "cry"]
	var step := int(Time.get_ticks_msec() / 800) % actions.size()
	for letter in letters:
		var body := _main.get_node_or_null("KidBody_%s" % letter) as Sprite3D
		if body == null:
			continue
		var action := str(body.get_meta("action", actions[step]))
		if action == "walk":
			body.position.x += sin(float(Time.get_ticks_msec()) / 400.0) * dt
		set_kid_action(letter, action if body.has_meta("action") else actions[step])


func _tick_partner(dt: float) -> void:
	if _main == null:
		return
	var body := _main.get_node_or_null("PartnerPet") as Sprite3D
	if body == null:
		return
	var home: Vector3 = body.get_meta("home", body.position)
	body.position.x = home.x + sin(float(Time.get_ticks_msec()) / 500.0) * 4.0


func _kids(main: Node) -> void:
	var letters := ["A", "B", "C", "D", "E", "F", "G", "H"]
	for i in range(letters.size()):
		var letter: String = letters[i]
		var form := letter + "1"
		var spr := Sprite3D.new()
		spr.name = "KidBody_%s" % letter
		var tex := load("res://art-pet/sprites/series2/%s_idle.png" % form) as Texture2D
		if tex:
			spr.texture = tex
		spr.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
		spr.centered = true
		spr.pixel_size = 1.0
		spr.offset = Vector2(0, kid_offset_y(form))
		spr.position = Vector3(-40 + i * 14, 29, 20)
		main.add_child(spr)
		var mark := Sprite3D.new()
		mark.name = "KidMarker_%s" % letter
		var mt := load(ART_ROOT + "kids_markers/kid_marker_%s.png" % letter) as Texture2D
		if mt:
			mark.texture = mt
		mark.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR
		mark.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		mark.pixel_size = 0.35
		mark.position = spr.position + Vector3(0, 22, 0)
		main.add_child(mark)


func _pill(active: bool) -> StyleBoxTexture:
	var box := StyleBoxTexture.new()
	var path := ART_ROOT + ("ui/ui_zone_pill_active.png" if active else "ui/ui_zone_pill_bg.png")
	var tex := load(path) as Texture2D
	if tex:
		tex.get_rid()
	box.texture = tex
	box.texture_margin_left = 28
	box.texture_margin_right = 28
	box.texture_margin_top = 12
	box.texture_margin_bottom = 12
	box.axis_stretch_horizontal = StyleBoxTexture.AXIS_STRETCH_MODE_STRETCH
	box.axis_stretch_vertical = StyleBoxTexture.AXIS_STRETCH_MODE_STRETCH
	return box


func _safe_viewport_rect() -> Rect2:
	# Window pixels from the display cutout, converted the same way as Hud.
	var live_safe: Rect2i = DisplayServer.get_display_safe_area()
	var live_win: Vector2i = DisplayServer.window_get_size()
	var vp := layout_viewport if layout_override else _viewport_size()
	var win := layout_window if layout_override else live_win
	var safe := layout_safe if layout_override else live_safe
	if safe.size.x < 2 or safe.size.y < 2:
		if win.x < 2 or win.y < 2:
			win = Vector2i(maxi(1, int(vp.x)), maxi(1, int(vp.y)))
		safe = Rect2i(Vector2i.ZERO, win)
	var fit := 1.0
	var ox := 0.0
	var oy := 0.0
	if win.x > 0 and win.y > 0 and vp.x > 1.0 and vp.y > 1.0:
		fit = minf(float(win.x) / vp.x, float(win.y) / vp.y)
		if fit <= 0.0:
			fit = 1.0
		ox = (float(win.x) - vp.x * fit) * 0.5
		oy = (float(win.y) - vp.y * fit) * 0.5
	var left := maxf(0.0, (float(safe.position.x) - ox) / fit)
	var top := maxf(0.0, (float(safe.position.y) - oy) / fit)
	var right := minf(vp.x, (float(safe.position.x + safe.size.x) - ox) / fit)
	var bottom := minf(vp.y, (float(safe.position.y + safe.size.y) - oy) / fit)
	left += 16.0
	top += 8.0
	right -= 16.0
	bottom -= 8.0
	return Rect2(Vector2(left, top), Vector2(maxf(0.0, right - left), maxf(0.0, bottom - top)))


func _viewport_size() -> Vector2:
	if _main and _main.get_viewport():
		return _main.get_viewport().get_visible_rect().size
	return Vector2(390, 844)


func apply_safe_layout() -> void:
	if _main == null:
		return
	var root := _main.get_node_or_null("EcosystemHud/Root") as Control
	if root == null:
		return
	var safe := _safe_viewport_rect()
	var hud: Node = _main.get("hud")
	var bar_top := safe.position.y + safe.size.y
	if hud and hud.get("bar") is Control and (hud.get("bar") as Control).visible:
		var br: Rect2 = (hud.get("bar") as Control).get_global_rect()
		if br.size.y > 1.0:
			bar_top = minf(bar_top, br.position.y)
	var blocked := safe.position.y
	if hud:
		for key in ["time_lbl", "shard_lbl", "food_lbl", "btn_book", "back_btn", "hide_btn", "dev_btn", "preview_lbl", "btn_replay_post", "btn_replay_hunt", "replay_reason"]:
			var node: Object = hud.get(key)
			if node is Control and (node as Control).visible:
				var rr: Rect2 = (node as Control).get_global_rect()
				if rr.size.y > 1.0 and rr.position.x < safe.position.x + safe.size.x * 0.55:
					blocked = maxf(blocked, rr.end.y)
	# The 9-slice pill needs its 28px margins, so each zone button is 84 wide.
	# Two rows stay inside the safe width and above the bottom action bar.
	var row_w := 84.0
	var row_h := 56.0
	var gap := 4.0
	var zones: Array = ["garden", "cottage_yard_work", "prairie_edge", "zone_farm", "zone_workshop", "zone_prairie_deep", "zone_family_wall"]
	var y2 := minf(safe.end.y, bar_top) - 8.0 - row_h
	var y1 := y2 - gap - row_h
	for i in range(zones.size()):
		var count := 4 if i < 4 else 3
		var index := i if i < 4 else i - 4
		var total := row_w * float(count) + gap * float(count - 1)
		var row_x := safe.position.x + maxf(0.0, (safe.size.x - total) * 0.5)
		var row_y := y1 if i < 4 else y2
		var b := root.get_node_or_null("Zone_%s" % str(zones[i])) as Control
		if b:
			_place(b, row_x + float(index) * (row_w + gap), row_y, row_w, row_h)
	var label_w := minf(220.0, safe.size.x)
	var label_y := y1 - 74.0
	_place(root.get_node_or_null("RoleLabel") as Control, safe.position.x, label_y, label_w, 22.0)
	_place(root.get_node_or_null("CombatCard") as Control, safe.position.x, label_y + 22.0, label_w, 22.0)
	_place(root.get_node_or_null("PatrolLabel") as Control, safe.position.x, label_y + 44.0, label_w, 22.0)
	_place(root.get_node_or_null("ComboBadge") as Control, safe.position.x + label_w + 8.0, label_y, 120.0, 22.0)
	var observe := root.get_node_or_null("PrairieObserve") as Control
	_place(observe, safe.position.x, blocked + 12.0, 144.0, 48.0)
	var portrait := root.get_node_or_null("PetPortrait") as Control
	_place(portrait, safe.end.x - 64.0, maxf(safe.position.y, 60.0), 64.0, 64.0)
	_sync_portrait()


func _place(node: Control, x: float, y: float, w: float, h: float) -> void:
	if node == null:
		return
	node.anchor_left = 0.0
	node.anchor_top = 0.0
	node.anchor_right = 0.0
	node.anchor_bottom = 0.0
	node.offset_left = x
	node.offset_top = y
	node.offset_right = x + w
	node.offset_bottom = y + h
	node.position = Vector2(x, y)
	node.size = Vector2(w, h)
	node.custom_minimum_size = Vector2(w, h)


func _sync_portrait() -> void:
	if _main == null:
		return
	var portrait := _main.get_node_or_null("EcosystemHud/Root/PetPortrait") as Button
	if portrait == null:
		return
	var file := "ui/ui_pet_portrait_frame_active.png" if follow_pet_id != "" else "ui/ui_pet_portrait_frame.png"
	var tex := load(ART_ROOT + file) as Texture2D
	if tex:
		portrait.icon = tex


func _hud(main: Node) -> void:
	var layer := CanvasLayer.new()
	layer.name = "EcosystemHud"
	layer.layer = 21
	main.add_child(layer)
	var root := Control.new()
	root.name = "Root"
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.theme = Vc27Fonts.theme()
	layer.add_child(root)
	var zones: Array = ["garden", "cottage_yard_work", "prairie_edge", "zone_farm", "zone_workshop", "zone_prairie_deep", "zone_family_wall"]
	var icons := {
		"garden": "icon_zone_garden.png",
		"cottage_yard_work": "icon_zone_cottage_yard_work.png",
		"prairie_edge": "icon_zone_prairie_edge.png",
		"zone_farm": "icon_zone_zone_farm.png",
		"zone_workshop": "icon_zone_zone_workshop.png",
		"zone_prairie_deep": "icon_zone_zone_prairie_deep.png",
		"zone_family_wall": "icon_zone_zone_family_wall.png",
	}
	for zid in zones:
		var id := str(zid)
		var b := Button.new()
		b.name = "Zone_%s" % id
		b.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
		b.icon = load(ART_ROOT + "ui/" + str(icons[id])) as Texture2D
		b.add_theme_stylebox_override("normal", _pill(false))
		b.add_theme_stylebox_override("hover", _pill(true))
		b.add_theme_stylebox_override("pressed", _pill(true))
		b.add_theme_stylebox_override("disabled", _pill(false))
		b.add_theme_constant_override("icon_max_width", 28)
		b.clip_contents = true
		Vc27Fonts.bind(b)
		var open := zone_unlocked(id, Sim.state if Sim else {})
		b.disabled = not open
		b.modulate = Color.WHITE if open else Color(1, 1, 1, 0.45)
		b.pressed.connect(func():
			current_zone = id
			stop_follow()
			if _main:
				_main.follow_pos = _zone_look(id)
				if _main.has_method("set_cam_follow"):
					_main.set_cam_follow(null)
		)
		root.add_child(b)
	var portrait := Button.new()
	portrait.name = "PetPortrait"
	portrait.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	portrait.icon = load(ART_ROOT + "ui/ui_pet_portrait_frame.png") as Texture2D
	var empty := StyleBoxEmpty.new()
	portrait.add_theme_stylebox_override("normal", empty)
	portrait.add_theme_stylebox_override("hover", empty)
	portrait.add_theme_stylebox_override("pressed", empty)
	portrait.add_theme_stylebox_override("focus", empty)
	portrait.clip_contents = true
	Vc27Fonts.bind(portrait)
	portrait.pressed.connect(func():
		follow_pet("tuanrong")
		if _main and _main.get("pet"):
			_main.set_cam_follow(_main.get("pet"))
		_sync_portrait()
	)
	root.add_child(portrait)
	var observe := HBoxContainer.new()
	observe.name = "PrairieObserve"
	observe.visible = false
	observe.mouse_filter = Control.MOUSE_FILTER_IGNORE
	for stat_file in ["icon_stat_power.png", "icon_stat_agility.png", "icon_stat_stamina.png"]:
		var icon := TextureRect.new()
		icon.texture = load(ART_ROOT + "ui/" + stat_file) as Texture2D
		icon.custom_minimum_size = Vector2(40, 40)
		icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		icon.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
		icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
		observe.add_child(icon)
	root.add_child(observe)
	var roles := Label.new()
	roles.name = "RoleLabel"
	roles.text = "種嘢 採集 工作 戰鬥狩獵 組合協同"
	Vc27Fonts.bind(roles)
	root.add_child(roles)
	var card := Label.new()
	card.name = "CombatCard"
	card.text = _combat_line()
	Vc27Fonts.bind(card)
	root.add_child(card)
	var patrol := Label.new()
	patrol.name = "PatrolLabel"
	patrol.text = patrol_label
	Vc27Fonts.bind(patrol)
	root.add_child(patrol)
	apply_safe_layout()


func _zone_look(id: String) -> Vector3:
	if id == "cottage_yard_work":
		return station_world("kitchen")
	if id == "zone_farm":
		return Vector3(40, 30, 30)
	if id == "zone_family_wall":
		return Vector3(-20, 30, 48)
	if id == "prairie_edge" or id == "zone_prairie_deep":
		return Vector3(0, 30, -24)
	return Vector3(0, 30, 8)


func show_combo(kind: String) -> void:
	if _main == null:
		return
	var root := _main.get_node_or_null("EcosystemHud/Root")
	if root == null:
		return
	var badge := root.get_node_or_null("ComboBadge") as Label
	if badge == null:
		badge = Label.new()
		badge.name = "ComboBadge"
		root.add_child(badge)
	badge.text = kind
	Vc27Fonts.bind(badge)
	apply_safe_layout()


func _combat_line() -> String:
	var c: Dictionary = {}
	if Sim and Sim.state.has("combat"):
		c = Sim.state.get("combat", {})
	return "力量 %d  身手 %d  耐力 %d" % [int(c.get("力量", 1)), int(c.get("身手", 1)), int(c.get("耐力", 1))]
