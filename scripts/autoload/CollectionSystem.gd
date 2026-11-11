extends Node
## 收藏簿（團絨 9×6＋細佬 A–H×3）、家具擺位、紅點、星星碎（沿用每日上限，唔加新貨幣）。

signal shards_changed(total: int)
signal unlocked(kind: String, id: String)
signal placed(item_id: String)
signal bought(item_id: String)
signal dots_changed()
var silent_unlocks := false

const JOBS_TRIPS_CAP := 12
const OLD_CAP := 30
const STEPS_CAP := 5
const TOTAL_CAP := 47


func econ() -> Dictionary:
	return GameData.economy if GameData else {}


func starting_shards() -> int:
	if GameData and "m1c" in GameData and not GameData.m1c.is_empty():
		return int(GameData.m1c.get("starting_shards", 25))
	return 25


func ensure(s: Dictionary = {}) -> Dictionary:
	if s.is_empty() and Sim:
		s = Sim.state
	if not s.has("wallet"):
		s["wallet"] = {
			"stardust": starting_shards(),
			"day_key": "",
			"earned": {"old": 0, "jobs_trips": 0, "steps": 0},
			"starter_granted": true,
		}
	if not s.has("collection"):
		s["collection"] = {
			"forms": {},
			"kids": {},
			"critters": {},
			"badges": {},
			"fruits": {},
			"new": {},
		}
	if not s.has("house"):
		var default_id := "bed_leaf"
		var furn: Dictionary = econ().get("furniture", {})
		if str(furn.get("default_item", "")) != "":
			default_id = str(furn.get("default_item"))
		s["house"] = {
			"owned": [default_id],
			"placed": {},  # slot -> item id
			"new": [],
		}
	if not s.has("notifs"):
		s["notifs"] = {"harvest": false, "collection": false, "work": false, "hunt": false}
	return s


func wallet(s: Dictionary = {}) -> Dictionary:
	return ensure(s)["wallet"]


func _roll_day(w: Dictionary) -> void:
	var dk := Sim._day_key() if Sim else ""
	if str(w.get("day_key", "")) != dk:
		w["day_key"] = dk
		w["earned"] = {"old": 0, "jobs_trips": 0, "steps": 0}


func stardust() -> int:
	return int(wallet().get("stardust", 0))


func add_shards(n: int, bucket: String = "jobs_trips") -> int:
	if n <= 0:
		return 0
	var w: Dictionary = wallet()
	_roll_day(w)
	var earned: Dictionary = w.get("earned", {})
	var cap := JOBS_TRIPS_CAP
	if bucket == "old":
		cap = OLD_CAP
	elif bucket == "steps":
		cap = STEPS_CAP
	var already := int(earned.get(bucket, 0))
	var room_b := maxi(0, cap - already)
	var total := int(w.get("stardust", 0))
	# 每日總上限 47
	var earned_all := int(earned.get("old", 0)) + int(earned.get("jobs_trips", 0)) + int(earned.get("steps", 0))
	var room_t := maxi(0, TOTAL_CAP - earned_all)
	var add := mini(n, mini(room_b, room_t))
	if add <= 0:
		return 0
	w["stardust"] = total + add
	earned[bucket] = already + add
	w["earned"] = earned
	if Sim:
		Sim._dirty = true
		Sim.state_changed.emit()
	shards_changed.emit(int(w["stardust"]))
	return add


func spend_shards(n: int) -> bool:
	var w: Dictionary = wallet()
	if n <= 0 or int(w.get("stardust", 0)) < n:
		return false
	w["stardust"] = int(w.get("stardust", 0)) - n
	if Sim:
		Sim._dirty = true
		Sim.state_changed.emit()
	shards_changed.emit(int(w["stardust"]))
	return true


func notify(key: String, on: bool) -> void:
	var s := ensure()
	var n: Dictionary = s.get("notifs", {})
	if bool(n.get(key, false)) == on:
		return
	n[key] = on
	s["notifs"] = n
	dots_changed.emit()


func has_dot(key: String) -> bool:
	return bool(ensure().get("notifs", {}).get(key, false))


func harvest_pending() -> bool:
	return has_dot("harvest") or (HuntSystem and HuntSystem.phase == HuntSystem.PHASE_READY) or (WorkSystem and WorkSystem.is_ready())


func unlock_form(id: String) -> void:
	var col: Dictionary = ensure()["collection"]
	var forms: Dictionary = col.get("forms", {})
	if bool(forms.get(id, false)):
		return
	forms[id] = true
	col["forms"] = forms
	_mark_new("form", id)
	unlocked.emit("form", id)


func unlock_kid(id: String) -> void:
	var col: Dictionary = ensure()["collection"]
	var kids: Dictionary = col.get("kids", {})
	if bool(kids.get(id, false)):
		return
	kids[id] = true
	col["kids"] = kids
	_mark_new("kid", id)
	unlocked.emit("kid", id)


func unlock_critter(id: String) -> void:
	var col: Dictionary = ensure()["collection"]
	var c: Dictionary = col.get("critters", {})
	if bool(c.get(id, false)):
		return
	c[id] = true
	col["critters"] = c
	_mark_new("critter", id)
	unlocked.emit("critter", id)


func unlock_badge(mon: String, grade: String = "bronze") -> void:
	var col: Dictionary = ensure()["collection"]
	var b: Dictionary = col.get("badges", {})
	var key := "%s_%s" % [mon, grade]
	if bool(b.get(key, false)):
		return
	b[key] = true
	col["badges"] = b
	_mark_new("badge", key)
	unlocked.emit("badge", key)


func add_fruit(id: String, n: int = 1) -> void:
	if id == "" or n <= 0:
		return
	var col: Dictionary = ensure()["collection"]
	var fr: Dictionary = col.get("fruits", {})
	fr[id] = int(fr.get(id, 0)) + n
	col["fruits"] = fr


func fruit_count(id: String) -> int:
	return int(ensure()["collection"].get("fruits", {}).get(id, 0))


func _mark_new(kind: String, id: String) -> void:
	var col: Dictionary = ensure()["collection"]
	var neu: Dictionary = col.get("new", {})
	neu[kind + ":" + id] = true
	col["new"] = neu
	notify("collection", true)


func clear_new() -> void:
	var col: Dictionary = ensure()["collection"]
	col["new"] = {}
	notify("collection", false)


func furniture_items() -> Array:
	var furn: Dictionary = econ().get("furniture", {})
	return furn.get("items", [])


func owned() -> Array:
	return ensure()["house"].get("owned", [])


func is_owned(id: String) -> bool:
	return str(id) in owned()


func placed_items() -> Dictionary:
	return ensure()["house"].get("placed", {})


func buy(id: String) -> Dictionary:
	var item := _item(id)
	if item.is_empty():
		return {"ok": false, "reason": "unknown"}
	if is_owned(id):
		return {"ok": false, "reason": "owned"}
	var price = item.get("price", null)
	if price == null:
		return {"ok": false, "reason": "not_shop"}
	var p := int(price)
	if p > 0 and not spend_shards(p):
		return {"ok": false, "reason": "shards", "need": p, "have": stardust()}
	var house: Dictionary = ensure()["house"]
	var own: Array = house.get("owned", [])
	own.append(id)
	house["owned"] = own
	var neu: Array = house.get("new", [])
	neu.append(id)
	house["new"] = neu
	notify("collection", true)
	if Sim:
		Sim._dirty = true
	bought.emit(id)
	return {"ok": true, "id": id, "price": p}


func place(id: String, slot: String = "") -> Dictionary:
	if not is_owned(id):
		return {"ok": false, "reason": "not_owned"}
	var item := _item(id)
	var sl := slot if slot != "" else str(item.get("slot", "bed"))
	var house: Dictionary = ensure()["house"]
	var pl: Dictionary = house.get("placed", {})
	pl[sl] = id
	house["placed"] = pl
	if Sim:
		Sim._dirty = true
	placed.emit(id)
	return {"ok": true, "id": id, "slot": sl}


func place_recommended() -> Dictionary:
	# 一鍵擺返推薦位置：已有未擺嘅，按 slot 各擺一件（價錢最低／預設優先）
	var done: Array = []
	var used_slot: Dictionary = placed_items().duplicate()
	var items := furniture_items()
	# 預設床先
	for it in items:
		if not (it is Dictionary):
			continue
		var id := str(it.get("id", ""))
		if not is_owned(id):
			continue
		var sl := str(it.get("slot", ""))
		if sl != "" and not used_slot.has(sl):
			var r := place(id, sl)
			if bool(r.get("ok", false)):
				used_slot[sl] = id
				done.append(r)
	return {"ok": not done.is_empty(), "items": done}


func _item(id: String) -> Dictionary:
	for it in furniture_items():
		if it is Dictionary and str(it.get("id", "")) == id:
			return it
	return {}


func form_ids() -> Array:
	# 團絨 9 路線 × 6 階：用現有 evo 名單，唔夠就留空格
	var out: Array = []
	if GameData:
		var ev: Dictionary = GameData.evolution
		var routes: Array = ev.get("routes", ev.get("route_list", []))
		# fallback 固定 9 名
		if routes.is_empty():
			routes = ["soft", "radiant", "lumi", "ember", "tide", "moon", "crystal", "dust", "shroom"]
		var stages := ["sprout", "hop", "still", "guard", "form5", "form6"]
		# 嘗試由 evolution.json 抽
		var stg: Dictionary = ev.get("stages", {})
		var lst: Array = stg.get("list", [])
		if lst.size() >= 2:
			stages = []
			for s in lst:
				if s is Dictionary and str(s.get("id", "")) not in ["egg"]:
					stages.append(str(s.get("id", "")))
		for r in routes:
			var rid: String = ""
			if r is String:
				rid = r
			elif r is Dictionary:
				rid = str((r as Dictionary).get("id", ""))
			else:
				rid = str(r)
			for st in stages:
				out.append("%s_%s" % [rid, st])
	while out.size() < 54:
		out.append("form_%d" % out.size())
	return out.slice(0, 54)


func kid_ids() -> Array:
	var out: Array = []
	for ch in ["A", "B", "C", "D", "E", "F", "G", "H"]:
		for n in range(1, 4):
			out.append("%s%d" % [ch, n])
	return out
