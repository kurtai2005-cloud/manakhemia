extends Node
## M1 兩座工作建築：郵局、廚房。一鍵派工／收工；收工可併入一鍵收成。

signal dispatched(building: String, pets: Array)
signal work_ready(building: String)
signal collected(rec: Dictionary)

const ST_EMPTY := "empty"
const ST_WORK := "work"
const ST_READY := "ready"


func cfg() -> Dictionary:
	if GameData and "m1b" in GameData:
		return GameData.m1b.get("work", {})
	return {}


func buildings() -> Array:
	return cfg().get("buildings", [])


func building(id: String) -> Dictionary:
	for b in buildings():
		if b is Dictionary and str(b.get("id", "")) == id:
			return b
	return {}


func ensure(s: Dictionary = {}) -> Dictionary:
	if s.is_empty() and Sim:
		s = Sim.state
	if not s.has("jobs_state"):
		s["jobs_state"] = {
			"day_key": "",
			"sites": {
				"post": {"status": ST_EMPTY, "pets": [], "started_ms": 0, "watch": 0.0, "level": 1},
				"kitchen": {"status": ST_EMPTY, "pets": [], "started_ms": 0, "watch": 0.0, "level": 1},
			},
			"last_assign": {},
		}
	return s["jobs_state"]


func site(id: String) -> Dictionary:
	var st: Dictionary = ensure()
	var sites: Dictionary = st.get("sites", {})
	if not sites.has(id):
		sites[id] = {"status": ST_EMPTY, "pets": [], "started_ms": 0, "watch": 0.0, "level": 1}
		st["sites"] = sites
	return sites[id]


func can_dispatch(id: String, ids: Array) -> Dictionary:
	var b := building(id)
	if b.is_empty():
		return {"ok": false, "reason": "unknown"}
	var sit: Dictionary = site(id)
	if str(sit.get("status", ST_EMPTY)) != ST_EMPTY:
		return {"ok": false, "reason": "busy", "status": sit.get("status")}
	if ids.is_empty():
		return {"ok": false, "reason": "no_team"}
	for pid in ids:
		if HuntSystem and HuntSystem.hunts_today(str(pid)) >= 0:
			var h: Dictionary = HuntSystem.ensure()
			var used: Dictionary = h.get("worked_or_hunted", {})
			if bool(used.get(str(pid), false)):
				return {"ok": false, "reason": "work_or_hunt", "id": str(pid)}
	return {"ok": true}


func auto_team(prefer: Array) -> Array:
	# 上次分配，冇就按傳入名單
	var st: Dictionary = ensure()
	var last: Dictionary = st.get("last_assign", {})
	var out: Array = []
	for pid in prefer:
		out.append(str(pid))
	if out.is_empty() and last.has("default"):
		for pid in last["default"]:
			out.append(str(pid))
	return out


func dispatch(id: String, ids: Array) -> Dictionary:
	var gate := can_dispatch(id, ids)
	if not bool(gate.get("ok", false)):
		return gate
	var sit: Dictionary = site(id)
	sit["status"] = ST_WORK
	sit["pets"] = []
	for pid in ids:
		sit["pets"].append(str(pid))
	sit["started_ms"] = TimeService.now_ms() if TimeService else 0
	sit["watch"] = 0.0
	var st: Dictionary = ensure()
	var last: Dictionary = st.get("last_assign", {})
	last[id] = sit["pets"].duplicate()
	last["default"] = sit["pets"].duplicate()
	st["last_assign"] = last
	if HuntSystem:
		for pid in sit["pets"]:
			HuntSystem.mark_worked(str(pid))
	if Sim:
		Sim._dirty = true
	dispatched.emit(id, sit["pets"])
	return {"ok": true, "building": id, "pets": sit["pets"]}


func tick_watch(dt: float) -> void:
	var dur := float(cfg().get("watch_sec", 12))
	for b in buildings():
		var id := str(b.get("id", ""))
		var sit: Dictionary = site(id)
		if str(sit.get("status", "")) != ST_WORK:
			continue
		sit["watch"] = float(sit.get("watch", 0.0)) + dt
		if float(sit["watch"]) >= dur:
			sit["status"] = ST_READY
			work_ready.emit(id)
			if CollectionSystem:
				CollectionSystem.notify("work", true)
				CollectionSystem.notify("harvest", true)


func offline_tick(s: Dictionary, now_ms: int) -> void:
	var need := int(float(cfg().get("offline_ready_sec", 3600)) * 1000.0)
	for b in buildings():
		var id := str(b.get("id", ""))
		var sit: Dictionary = site(id)
		if str(sit.get("status", "")) != ST_WORK:
			continue
		var start := int(sit.get("started_ms", 0))
		if start > 0 and now_ms - start >= need:
			sit["status"] = ST_READY
			work_ready.emit(id)
			if CollectionSystem:
				CollectionSystem.notify("work", true)
				CollectionSystem.notify("harvest", true)


func is_ready(id: String = "") -> bool:
	if id != "":
		return str(site(id).get("status", "")) == ST_READY
	for b in buildings():
		if str(site(str(b.get("id", ""))).get("status", "")) == ST_READY:
			return true
	return false


func any_working() -> bool:
	for b in buildings():
		if str(site(str(b.get("id", ""))).get("status", "")) == ST_WORK:
			return true
	return false


func pay_shards(id: String) -> int:
	var sit: Dictionary = site(id)
	var lv := int(sit.get("level", 1))
	# economy: pay = level + 1
	return lv + 1


func collect(id: String = "") -> Dictionary:
	var recs: Array = []
	var total := 0
	var ids: Array = []
	if id != "":
		ids.append(id)
	else:
		for b in buildings():
			ids.append(str(b.get("id", "")))
	for bid in ids:
		var sit: Dictionary = site(str(bid))
		if str(sit.get("status", "")) != ST_READY:
			continue
		var sh := pay_shards(str(bid))
		total += sh
		if CollectionSystem:
			CollectionSystem.add_shards(sh, "jobs_trips")
		var row := {"ok": true, "act": "work", "building": bid, "shards": sh, "pets": sit.get("pets", [])}
		recs.append(row)
		sit["status"] = ST_EMPTY
		sit["pets"] = []
		sit["watch"] = 0.0
		sit["started_ms"] = 0
	if recs.is_empty():
		return {"ok": false, "reason": "none", "act": "work", "shards": 0, "items": []}
	var rec := {"ok": true, "act": "work", "shards": total, "items": recs}
	if Sim:
		Sim._dirty = true
		Sim.state_changed.emit()
	collected.emit(rec)
	if CollectionSystem and not is_ready():
		CollectionSystem.notify("work", false)
	return rec
