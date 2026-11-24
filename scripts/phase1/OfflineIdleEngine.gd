class_name OfflineIdleEngine
extends RefCounted

const MIN_AWAY_MS := 60000


static func settle(state: Dictionary, now_ms: int, force_ms: int = 0) -> Dictionary:
	var last := int(state.get("last_tick_ts", now_ms))
	var away := force_ms if force_ms > 0 else maxi(0, now_ms - last)
	state["last_tick_ts"] = now_ms
	var report := {"seconds": int(away / 1000), "shards": 0, "exp": 0, "crops": 0, "show": false}
	if away < MIN_AWAY_MS and force_ms <= 0:
		return report
	var hours := float(away) / 3600000.0
	var want := int(floor(hours * 4.0))
	if want < 1:
		want = 1
	var paid := want
	var eco := Phase1Config.node("Ecosystem")
	var bag := Phase1Config.node("CollectionSystem")
	if eco and eco.has_method("grant_shards"):
		paid = int(eco.call("grant_shards", want, "phase1_idle"))
	elif bag and bag.has_method("add_shards"):
		paid = int(bag.call("add_shards", want, "phase1_idle"))
	report["shards"] = paid
	var exp := int(floor(hours * 8.0))
	if exp < 1:
		exp = 1
	var pet := Phase1Registry.primary(state)
	if not pet.is_empty():
		var stats: Dictionary = pet.get("stats", {})
		stats["exp"] = int(stats.get("exp", 0)) + exp
		stats["lv"] = 1 + int(stats["exp"]) / 20
		pet["stats"] = stats
		Phase1Registry.put(state, pet)
	report["exp"] = exp
	var plots: Array = state.get("phase1_plots", ["empty", "empty", "empty", "empty"])
	var steps := mini(4, int(ceil(hours)))
	var grown := 0
	for i in range(plots.size()):
		var stage := str(plots[i])
		for _s in range(steps):
			var nxt := _grow(stage)
			if nxt != stage:
				stage = nxt
				grown += 1
		plots[i] = stage
	state["phase1_plots"] = plots
	report["crops"] = grown
	report["show"] = true
	return report


static func _grow(stage: String) -> String:
	if stage == "empty":
		return "sprout"
	if stage == "sprout":
		return "growing"
	if stage == "growing":
		return "ripe"
	return stage
