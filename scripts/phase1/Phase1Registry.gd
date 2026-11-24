class_name Phase1Registry
extends RefCounted
## Flat pet_registry. Ids are strings. Pets are never stored inside other pets.

static func ensure(state: Dictionary) -> Dictionary:
	var reg: Dictionary = state.get("pet_registry", {})
	if reg.is_empty():
		var pet := _from_legacy(state)
		reg[str(pet["id"])] = pet
		state["pet_registry"] = reg
	for key in reg.keys():
		var row: Dictionary = reg[key]
		row["id"] = str(key)
		row["parent_ids"] = _id_list(row.get("parent_ids", []))
		row["children_ids"] = _id_list(row.get("children_ids", []))
		row["fused_from_ids"] = _id_list(row.get("fused_from_ids", []))
		if not row.has("care"):
			row["care"] = {"飽食": 70, "心情": 60, "親密": 40, "體力": 80}
		if not row.has("stats"):
			row["stats"] = {"力量": 1, "身手": 1, "耐力": 1, "exp": 0, "lv": 1}
		reg[key] = row
	state["pet_registry"] = reg
	return reg


static func primary(state: Dictionary) -> Dictionary:
	var reg := ensure(state)
	if reg.has("tuanrong"):
		return reg["tuanrong"]
	var keys := reg.keys()
	if keys.is_empty():
		return {}
	return reg[keys[0]]


static func put(state: Dictionary, pet: Dictionary) -> void:
	var reg := ensure(state)
	var pid := str(pet.get("id", ""))
	if pid == "":
		return
	pet["id"] = pid
	reg[pid] = pet
	state["pet_registry"] = reg


static func add_child_pet(state: Dictionary) -> Dictionary:
	var reg := ensure(state)
	var n := reg.size() + 1
	var pid := "pet_%d" % n
	while reg.has(pid):
		n += 1
		pid = "pet_%d" % n
	var baby := {
		"id": pid,
		"name": "小團絨",
		"species_id": "baby",
		"stage": "baby",
		"generation": 1,
		"parent_ids": ["tuanrong"] if reg.has("tuanrong") else [],
		"children_ids": [],
		"partner_id": "",
		"fused_from_ids": [],
		"status": "idle",
		"care": {"飽食": 80, "心情": 70, "親密": 30, "體力": 80},
		"stats": {"力量": 1, "身手": 1, "耐力": 1, "exp": 0, "lv": 1},
		"zone_id": "garden",
	}
	reg[pid] = baby
	if reg.has("tuanrong"):
		var parent: Dictionary = reg["tuanrong"]
		var kids: Array = parent.get("children_ids", [])
		kids.append(pid)
		parent["children_ids"] = kids
		reg["tuanrong"] = parent
	state["pet_registry"] = reg
	return baby


static func acyclic(state: Dictionary) -> bool:
	var reg: Dictionary = state.get("pet_registry", {})
	for key in reg.keys():
		if _sees(reg, str(key), str(key), 0):
			return false
	return true


static func _sees(reg: Dictionary, start: String, cursor: String, depth: int) -> bool:
	if depth > 8:
		return true
	var row: Dictionary = reg.get(cursor, {})
	for pid in row.get("parent_ids", []):
		var nxt := str(pid)
		if nxt == start:
			return true
		if _sees(reg, start, nxt, depth + 1):
			return true
	return false


static func _id_list(value: Variant) -> Array:
	var out: Array = []
	if value is Array:
		for item in value:
			if item is Dictionary:
				continue
			out.append(str(item))
	return out


static func _from_legacy(state: Dictionary) -> Dictionary:
	var stage := str(state.get("stage", "baby"))
	if stage == "sprout" or stage == "newborn" or stage == "":
		stage = "baby"
	var species := "baby"
	if stage == "egg":
		species = "egg"
	elif stage == "child":
		species = "child"
	return {
		"id": "tuanrong",
		"name": "小團絨" if stage != "egg" else "微光蛋",
		"species_id": species,
		"stage": stage,
		"generation": 0,
		"parent_ids": [],
		"children_ids": [],
		"partner_id": "",
		"fused_from_ids": [],
		"status": "idle",
		"care": {
			"飽食": int(state.get("needs", {}).get("hunger", 70)),
			"心情": int(state.get("needs", {}).get("mood", 60)),
			"親密": 40,
			"體力": int(state.get("needs", {}).get("energy", 80)),
		},
		"stats": {"力量": 1, "身手": 1, "耐力": 1, "exp": 0, "lv": 1},
		"zone_id": "garden",
	}
