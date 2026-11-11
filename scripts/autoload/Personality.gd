extends Node
## 三軸性格：出世隨機＋照顧漂移。數值只由 data/personality.json 讀。

signal changed()

const AXES: PackedStringArray = ["motion", "work", "social"]

var birth_min := -3
var birth_max := 3
var axis_min := -10
var axis_max := 10
var day_shift_min := -2
var day_shift_max := 2
var walk_energetic_mul := 1.2
var walk_quiet_mul := 0.85
var clingy_axis_min := 5
var energetic_axis_min := 5


func _ready() -> void:
	_boot()


func _boot() -> void:
	var p: Dictionary = GameData.personality if GameData else {}
	var ax: Dictionary = p.get("axes", {})
	axis_min = int(ax.get("min", -10))
	axis_max = int(ax.get("max", 10))
	var birth: Dictionary = p.get("birth", {})
	var br: Variant = birth.get("each_axis_random", [-3, 3])
	if br is Array and br.size() >= 2:
		birth_min = int(br[0])
		birth_max = int(br[1])
	var ds: Dictionary = p.get("daily_shift", {})
	day_shift_max = int(ds.get("per_axis_max", 2))
	day_shift_min = int(ds.get("per_axis_min", -2))
	var mot: Dictionary = p.get("m1_motion", {})
	var wm: Dictionary = mot.get("walk_speed_mul", {})
	walk_energetic_mul = float(wm.get("mul", 1.2))
	walk_quiet_mul = float(wm.get("quiet_mul", 0.85))
	var fam: Dictionary = p.get("family_interactions", {})
	for k in fam.get("kinds", []):
		if not (k is Dictionary):
			continue
		if str(k.get("id", "")) == "walk_together":
			clingy_axis_min = int((k.get("clingy_threshold", {}) as Dictionary).get("axis_min", 5))
		elif str(k.get("id", "")) == "chase":
			energetic_axis_min = int((k.get("energetic_threshold", {}) as Dictionary).get("axis_min", 5))


func blank() -> Dictionary:
	return {"motion": 0, "work": 0, "social": 0, "day_key": "", "day_acc": {"motion": 0, "work": 0, "social": 0}}


func roll(rng: RandomNumberGenerator) -> Dictionary:
	var o := blank()
	for a in AXES:
		o[a] = rng.randi_range(birth_min, birth_max)
	return o


func clamp_axis(v: int) -> int:
	return clampi(v, axis_min, axis_max)


func get_for(id: String) -> Dictionary:
	if Sim == null or Sim.state.is_empty():
		return blank()
	var bag: Dictionary = Sim.state.get("personalities", {})
	if not (bag is Dictionary):
		bag = {}
	if not bag.has(id):
		var rng := RandomNumberGenerator.new()
		var seed := int(Sim.state.get("seed", 1))
		rng.seed = seed + int(id.hash())
		bag[id] = roll(rng)
		Sim.state["personalities"] = bag
	var rec: Dictionary = bag[id]
	for a in AXES:
		if not rec.has(a):
			rec[a] = 0
	return rec


func set_for(id: String, rec: Dictionary) -> void:
	if Sim == null:
		return
	var bag: Dictionary = Sim.state.get("personalities", {})
	bag[id] = rec
	Sim.state["personalities"] = bag
	changed.emit()


func axis(id: String, name: String) -> int:
	return int(get_for(id).get(name, 0))


func primary_type(id: String) -> String:
	# 絕對值最大嘅軸嘅嗰端；全部 |v|≤3 → 隨和
	var rec := get_for(id)
	var p: Dictionary = GameData.personality if GameData else {}
	var types: Dictionary = p.get("types", {})
	var easy_max := int(types.get("easygoing_when_all_abs_lte", 3))
	var best_abs := 0
	var best_axis := ""
	var all_small := true
	for a in AXES:
		var v := int(rec.get(a, 0))
		if absi(v) > easy_max:
			all_small = false
		if absi(v) > best_abs:
			best_abs = absi(v)
			best_axis = a
	if all_small:
		return str(types.get("easygoing_zh", "隨和"))
	var v2 := int(rec.get(best_axis, 0))
	match best_axis:
		"motion":
			return "活潑" if v2 > 0 else "文靜"
		"work":
			return "勤力" if v2 > 0 else "懶散"
		"social":
			return "黐人" if v2 > 0 else "獨立"
	return str(types.get("easygoing_zh", "隨和"))


func walk_speed_mul(id: String) -> float:
	# 按 motion 軸線性插值：−max→quiet_mul、0→1、＋max→energetic_mul
	var m := float(axis(id, "motion"))
	var t := clampf(m / maxf(float(axis_max), 1.0), -1.0, 1.0)
	if t >= 0.0:
		return lerpf(1.0, walk_energetic_mul, t)
	return lerpf(1.0, walk_quiet_mul, -t)


func expr_icon(id: String) -> String:
	var t := primary_type(id)
	var map := {
		"活潑": "expr_lively", "文靜": "expr_quiet", "勤力": "expr_diligent",
		"懶散": "expr_lazy", "黐人": "expr_clingy", "獨立": "expr_indep",
	}
	return str(map.get(t, "mood_ok"))


func apply_care_act(id: String, act: String, day_key: String) -> void:
	# 照顧漂移：每日每軸夾喺 per_axis_min..max，無自然回落。
	var p: Dictionary = GameData.personality if GameData else {}
	var ds: Dictionary = p.get("daily_shift", {})
	var delta := 0
	var which := ""
	for row in ds.get("actions", []):
		if not (row is Dictionary):
			continue
		var acts: Array = row.get("acts", [])
		var hit := false
		for a in acts:
			if str(a) == act:
				hit = true
				break
		if hit:
			which = str(row.get("axis", ""))
			delta = int(row.get("delta", 0))
			break
	if which == "" or delta == 0:
		return
	var rec := get_for(id)
	if str(rec.get("day_key", "")) != day_key:
		rec["day_key"] = day_key
		rec["day_acc"] = {"motion": 0, "work": 0, "social": 0}
	var acc: Dictionary = rec.get("day_acc", {})
	var used := int(acc.get(which, 0))
	var room_hi := day_shift_max - used
	var room_lo := day_shift_min - used
	var apply := clampi(delta, room_lo, room_hi)
	if apply == 0:
		return
	rec[which] = clamp_axis(int(rec.get(which, 0)) + apply)
	acc[which] = used + apply
	rec["day_acc"] = acc
	set_for(id, rec)


func act_weight(id: String, act: String) -> float:
	# personality_act_mul；冇就 1
	var p: Dictionary = GameData.personality if GameData else {}
	var needs: Dictionary = p.get("needs", {})
	var table: Dictionary = needs.get("personality_act_mul", {})
	var typ := primary_type(id)
	var row: Variant = table.get(typ, {})
	if row is Dictionary and row.has(act):
		return float(row[act])
	return 1.0
