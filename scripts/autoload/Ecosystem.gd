extends Node
## Living ecosystem v1. Every tunable number is read from data/ecosystem_v1.json.

const DATA_PATH := "res://data/ecosystem_v1.json"
const MEASURE_PATH := "res://art/ecosystem_v1/series2_measurements.json"
const ART_ROOT := "res://art/ecosystem_v1/"

var cfg: Dictionary = {}
var follow_id := ""
var patrol_label := ""
var _main: Node = null


func _ready() -> void:
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


func follow_pet(pet_id: String) -> void:
	follow_id = pet_id


func present(main: Node) -> void:
	_main = main
	_sprite(main, "WorkOutdoorStove", ART_ROOT + "props/work_outdoor_stove_table.png", station_world("kitchen"))
	_sprite(main, "WorkOutdoorPost", ART_ROOT + "props/work_outdoor_post_rack.png", station_world("post"))
	_sprite(main, "FarmPlot", ART_ROOT + "props/farm_crop_stage1_sprout.png", Vector3(40, 0, 30))
	_sprite(main, "PantryPile", ART_ROOT + "props/storage_fruit_pile_low.png", Vector3(20, 0, 36))
	_sprite(main, "FamilyWall", ART_ROOT + "props/family_wall_board.png", Vector3(-20, 0, 48))
	_kids(main)
	_hud(main)


func _sprite(main: Node, node_name: String, path: String, pos: Vector3) -> void:
	if main.get_node_or_null(node_name) != null:
		return
	var tex := load(path) as Texture2D
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
	s.position.y = 0
	main.add_child(s)


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


func _hud(main: Node) -> void:
	var layer := CanvasLayer.new()
	layer.name = "EcosystemHud"
	layer.layer = 21
	main.add_child(layer)
	var root := Control.new()
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(root)
	var zones: Array = ["garden", "cottage_yard_work", "prairie_edge", "zone_farm", "zone_workshop", "zone_prairie_deep", "zone_family_wall"]
	var x := 16.0
	for zid in zones:
		var b := Button.new()
		b.name = "Zone_%s" % str(zid)
		b.text = str(cfg.get("zones", {}).get("unlockable", {}).get(zid, {}).get("zh", zid))
		if zid == "garden":
			b.text = "花園"
		elif zid == "cottage_yard_work":
			b.text = "屋旁"
		elif zid == "prairie_edge":
			b.text = "草原邊"
		b.custom_minimum_size = Vector2(64, 56)
		b.position = Vector2(x, 700)
		var id := str(zid)
		b.pressed.connect(func():
			stop_follow()
			if _main and _main.has_method("set_cam_follow"):
				_main.set_cam_follow(null)
		)
		root.add_child(b)
		x += 52.0
	var roles := Label.new()
	roles.name = "RoleLabel"
	roles.text = "種嘢 採集 工作 戰鬥狩獵 組合協同"
	roles.position = Vector2(16, 612)
	root.add_child(roles)
	var card := Label.new()
	card.name = "CombatCard"
	card.text = _combat_line()
	card.position = Vector2(16, 640)
	root.add_child(card)
	var patrol := Label.new()
	patrol.name = "PatrolLabel"
	patrol.text = patrol_label
	patrol.position = Vector2(16, 668)
	root.add_child(patrol)


func _combat_line() -> String:
	var c: Dictionary = {}
	if Sim and Sim.state.has("combat"):
		c = Sim.state.get("combat", {})
	return "力量 %d  身手 %d  耐力 %d" % [int(c.get("力量", 1)), int(c.get("身手", 1)), int(c.get("耐力", 1))]
