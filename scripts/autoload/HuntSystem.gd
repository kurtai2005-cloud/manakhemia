extends Node
## M1 野外狩獵 lite：草原 1 區、一鍵出發／收隊（收隊併入一鍵收成）。
## 觀察優先；觀看時用 watch_sec 壓縮；熄 app 就按 2 小時離線結算。

signal hunt_started()
signal hunt_phase(phase: String)
signal hunt_ready()
signal hunt_collected(rec: Dictionary)

const PHASE_IDLE := "idle"
const PHASE_DEPART := "depart"
const PHASE_HUNT := "hunt"
const PHASE_CARRY := "carry"
const PHASE_HOME := "home"
const PHASE_READY := "ready"

var phase := PHASE_IDLE
var team: Array = []  # walker names / ids
var started_ms := 0
var watch_elapsed := 0.0
var pending: Dictionary = {}
var big_encounter := false
var fruits: Array = []
var shards := 0
var bronze: Dictionary = {}  # monster id -> hunts


func cfg() -> Dictionary:
	if GameData and "m1b" in GameData:
		return GameData.m1b.get("hunt", {})
	return {}


func hdata() -> Dictionary:
	return GameData.hunting if GameData else {}


func ensure(s: Dictionary = {}) -> Dictionary:
	if s.is_empty() and Sim:
		s = Sim.state
	if not s.has("hunt"):
		s["hunt"] = {
			"day_key": "",
			"hunts_today": {},
			"worked_or_hunted": {},
			"pending": {},
			"bronze": {},
			"level": 1,
		}
	return s["hunt"]


func _day(s: Dictionary) -> String:
	return Sim._day_key() if Sim else ""


func hunts_today(pet_id: String) -> int:
	var h: Dictionary = ensure()
	var dk := _day({})
	if str(h.get("day_key", "")) != dk:
		h["day_key"] = dk
		h["hunts_today"] = {}
		h["worked_or_hunted"] = {}
	return int((h.get("hunts_today", {}) as Dictionary).get(pet_id, 0))


func can_depart(ids: Array = []) -> Dictionary:
	var hunt: Dictionary = hdata().get("hunt", {})
	var max_n := int((hdata().get("team", {}) as Dictionary).get("m1_max_adults", 3))
	var max_day := int(hunt.get("max_hunts_per_pet_per_day", 4))
	if phase != PHASE_IDLE and phase != PHASE_READY:
		return {"ok": false, "reason": "busy"}
	if phase == PHASE_READY:
		return {"ok": false, "reason": "collect_first"}
	if ids.is_empty():
		return {"ok": false, "reason": "no_team"}
	if ids.size() > max_n:
		return {"ok": false, "reason": "team_max", "max": max_n}
	for id in ids:
		var pid := str(id)
		if hunts_today(pid) >= max_day:
			return {"ok": false, "reason": "daily_pet_cap", "id": pid}
		var h: Dictionary = ensure()
		var used: Dictionary = h.get("worked_or_hunted", {})
		if bool(used.get(pid, false)):
			return {"ok": false, "reason": "work_or_hunt", "id": pid}
	return {"ok": true}


func depart(ids: Array, rng: RandomNumberGenerator = null) -> Dictionary:
	var gate := can_depart(ids)
	if not bool(gate.get("ok", false)):
		return gate
	if rng == null:
		rng = RandomNumberGenerator.new()
		rng.randomize()
	team = []
	for id in ids:
		team.append(str(id))
	var hd: Dictionary = hdata().get("hunt", {})
	shards = rng.randi_range(int(hd.get("shards_min", 1)), int(hd.get("shards_max", 3)))
	var nfruit := rng.randi_range(int(hd.get("fruit_min", 2)), int(hd.get("fruit_max", 4)))
	big_encounter = rng.randf() < float(hd.get("big_monster_chance", 0.2))
	if big_encounter:
		nfruit += int(hd.get("big_monster_extra_fruit", 1))
	var kinds: Array = ((hdata().get("areas", {}) as Dictionary).get("m1", {}) as Dictionary).get("fruits", [])
	var mkinds: Array = ((hdata().get("areas", {}) as Dictionary).get("m1", {}) as Dictionary).get("monsters", [])
	fruits = []
	for i in range(nfruit):
		var fr: Dictionary = {}
		for it in kinds:
			if it is Dictionary and str(it.get("id", "")) != "":
				if fr.is_empty() or rng.randf() < 0.35:
					fr = it
		if fr.is_empty():
			fr = {"id": "glow_berry", "zh": "微光莓"}
		fruits.append({"id": str(fr.get("id", "glow_berry")), "zh": str(fr.get("zh", "")), "art": art_fruit(str(fr.get("id", "")))})
	var mon_id := "puff_shroom"
	for it in mkinds:
		if it is Dictionary and str(it.get("id", "")) != "":
			if (big_encounter and bool(it.get("big", false))) or (not big_encounter and not bool(it.get("big", false))):
				mon_id = str(it.get("id", mon_id))
				if not big_encounter and rng.randf() < 0.5:
					break
	pending = {
		"shards": shards,
		"fruits": fruits.duplicate(true),
		"big": big_encounter,
		"monster": mon_id,
		"team": team.duplicate(),
		"started_ms": TimeService.now_ms() if TimeService else 0,
	}
	phase = PHASE_DEPART
	watch_elapsed = 0.0
	started_ms = int(pending.get("started_ms", 0))
	var h: Dictionary = ensure()
	var today: Dictionary = h.get("hunts_today", {})
	var used: Dictionary = h.get("worked_or_hunted", {})
	for pid in team:
		today[pid] = int(today.get(pid, 0)) + 1
		used[pid] = true
		bronze[mon_id] = int(bronze.get(mon_id, 0)) + 1
	h["hunts_today"] = today
	h["worked_or_hunted"] = used
	h["pending"] = pending
	h["bronze"] = bronze
	if Sim:
		Sim._dirty = true
	hunt_started.emit()
	hunt_phase.emit(phase)
	return {"ok": true, "pending": pending}


func set_phase(p: String) -> void:
	if phase == p:
		return
	phase = p
	hunt_phase.emit(phase)
	if p == PHASE_READY:
		hunt_ready.emit()
		if CollectionSystem:
			CollectionSystem.notify("harvest", true)
			CollectionSystem.notify("hunt", true)


func tick_watch(dt: float) -> void:
	if phase == PHASE_IDLE or phase == PHASE_READY:
		return
	watch_elapsed += dt
	var dur := float(cfg().get("watch_sec", 18))
	# 觀看階段：depart 0–12%，hunt 12–55%，carry 55–88%，home/ready 88–100%
	var r := watch_elapsed / maxf(dur, 1.0)
	if r < 0.12:
		set_phase(PHASE_DEPART)
	elif r < 0.55:
		set_phase(PHASE_HUNT)
	elif r < 0.88:
		set_phase(PHASE_CARRY)
	else:
		set_phase(PHASE_READY)


func offline_tick(s: Dictionary, now_ms: int) -> void:
	var h: Dictionary = ensure(s)
	var pend: Dictionary = h.get("pending", {})
	if pend.is_empty():
		return
	var start := int(pend.get("started_ms", 0))
	var need := int(float((hdata().get("hunt", {}) as Dictionary).get("duration_hours", 2)) * 3600.0 * 1000.0)
	if start > 0 and now_ms - start >= need:
		if phase != PHASE_READY:
			pending = pend
			fruits = pend.get("fruits", [])
			shards = int(pend.get("shards", 0))
			big_encounter = bool(pend.get("big", false))
			team = pend.get("team", [])
			set_phase(PHASE_READY)


func has_pending() -> bool:
	return phase == PHASE_READY or not pending.is_empty() and phase != PHASE_IDLE


func collect() -> Dictionary:
	if phase != PHASE_READY and not (phase == PHASE_IDLE and not pending.is_empty()):
		if phase == PHASE_IDLE:
			return {"ok": false, "reason": "none"}
		# 未完成唔可以收
		return {"ok": false, "reason": "not_ready", "phase": phase}
	var rec := {
		"ok": true,
		"act": "hunt",
		"shards": shards,
		"fruits": fruits.duplicate(true),
		"big": big_encounter,
		"monster": str(pending.get("monster", "")),
		"team": team.duplicate(),
	}
	if CollectionSystem:
		CollectionSystem.add_shards(shards, "jobs_trips")
		for fr in fruits:
			CollectionSystem.add_fruit(str(fr.get("id", "")), 1)
		if str(rec.get("monster", "")) != "":
			CollectionSystem.unlock_critter(str(rec.get("monster", "")))
			CollectionSystem.unlock_badge(str(rec.get("monster", "")), "bronze")
	pending = {}
	fruits = []
	shards = 0
	team = []
	big_encounter = false
	phase = PHASE_IDLE
	watch_elapsed = 0.0
	var h: Dictionary = ensure()
	h["pending"] = {}
	if Sim:
		Sim._dirty = true
		Sim.state_changed.emit()
	hunt_collected.emit(rec)
	if CollectionSystem:
		CollectionSystem.notify("harvest", false)
		CollectionSystem.notify("hunt", false)
	return rec


func art_fruit(id: String) -> String:
	var m: Dictionary = cfg().get("art_fruit", {})
	return str(m.get(id, id))


func art_critter(id: String) -> String:
	var m: Dictionary = cfg().get("art_critter", {})
	return str(m.get(id, id))


func mark_worked(pet_id: String) -> void:
	var h: Dictionary = ensure()
	var used: Dictionary = h.get("worked_or_hunted", {})
	used[str(pet_id)] = true
	h["worked_or_hunted"] = used


func pounce_miss_cfg() -> Dictionary:
	var h: Dictionary = hdata().get("hunt", {})
	var cfg: Dictionary = h.get("pounce_miss", {})
	return cfg


func miss_chance_for(pet_id: String) -> float:
	var cfg := pounce_miss_cfg()
	var ch := float(cfg.get("chance", 0.25))
	var typ := ""
	if Personality and pet_id != "":
		typ = str(Personality.primary_type(pet_id))
	var adj: Dictionary = cfg.get("personality_adjust", {})
	if typ != "" and adj.has(typ):
		ch += float(adj[typ])
	return clampf(ch, 0.0, 1.0)


func max_misses_per_critter() -> int:
	return int(pounce_miss_cfg().get("max_misses_per_critter", pounce_miss_cfg().get("always_hit_after_misses", 2)))


## misses_so_far >= cap → 呢一次必中。force 0..1 可覆寫 rng（測試用）。
func roll_is_miss(pet_id: String, misses_so_far: int, rng: RandomNumberGenerator = null, force: float = -1.0) -> bool:
	if misses_so_far >= max_misses_per_critter():
		return false
	var r := force
	if r < 0.0:
		if rng == null:
			rng = RandomNumberGenerator.new()
			rng.randomize()
		r = rng.randf()
	return r < miss_chance_for(pet_id)
