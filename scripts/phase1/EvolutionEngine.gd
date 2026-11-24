class_name EvolutionEngine
extends RefCounted

const ORDER := ["egg", "baby", "child", "adult", "ultimate"]


static func zh(doc: Dictionary, stage: String) -> String:
	for item in doc.get("stages", []):
		if item is Dictionary and str(item.get("id", "")) == stage:
			return str(item.get("zh", stage))
	return stage


static func next_stage(stage: String) -> String:
	var i := ORDER.find(stage)
	if i < 0 or i >= ORDER.size() - 1:
		return stage
	return str(ORDER[i + 1])


static func branch_species(doc: Dictionary, pet: Dictionary, stage: String) -> String:
	if stage == "egg":
		return "egg"
	if stage == "baby":
		return "baby"
	if stage == "child":
		return "child"
	var stats: Dictionary = pet.get("stats", {})
	var care: Dictionary = pet.get("care", {})
	var power := int(stats.get("力量", 1))
	var agi := int(stats.get("身手", 1))
	var sta := int(stats.get("耐力", 1))
	var bond := int(care.get("親密", 0))
	var mood := int(care.get("心情", 0))
	if stage == "ultimate":
		if bond >= 70:
			return "soft"
		if power >= agi and power >= sta:
			return "bright"
		if agi >= sta:
			return "dust"
		return "lumi"
	if mood >= 80 and bond >= 60:
		return "moon"
	if power >= agi and power >= sta:
		return "ember"
	if agi >= sta:
		return "tide"
	if sta >= 3:
		return "crystal"
	return "shroom"


static func force_next(doc: Dictionary, state: Dictionary) -> Dictionary:
	var pet := Phase1Registry.primary(state)
	if pet.is_empty():
		return {"ok": false}
	var stage := next_stage(str(pet.get("stage", "baby")))
	var species := branch_species(doc, pet, stage)
	var spec := Phase1Config.species(doc, species)
	pet["stage"] = stage
	pet["species_id"] = species
	pet["name"] = str(spec.get("zh", pet.get("name", "")))
	var stats: Dictionary = pet.get("stats", {})
	stats["exp"] = int(stats.get("exp", 0)) + 20
	stats["lv"] = 1 + int(stats["exp"]) / 20
	pet["stats"] = stats
	Phase1Registry.put(state, pet)
	state["stage"] = stage
	return {"ok": true, "stage": stage, "species": species, "name": pet["name"]}


static func tint_of(doc: Dictionary, species_id: String) -> Color:
	var spec := Phase1Config.species(doc, species_id)
	var hex := str(spec.get("tint", "FFFFFF"))
	return Color.html(hex) if hex != "" else Color.WHITE


static func scale_of(doc: Dictionary, species_id: String) -> float:
	return float(Phase1Config.species(doc, species_id).get("scale", 1.0))
