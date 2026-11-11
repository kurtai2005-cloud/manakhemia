extends Node
class_name FamilyDirector
## 家人之間自發互動（§0.5 B）。間隔／冷卻由 personality.json family_interactions 讀。

const S := BeehaveTree.SUCCESS
const F := BeehaveTree.FAILURE
const R := BeehaveTree.RUNNING

var walkers: Array = []  # Walker
var brains: Dictionary = {}  # Walker -> PetBrain
var interval_min := 60.0
var interval_max := 180.0
var no_repeat := 600.0
var next_at := 8.0  # 開局稍等；GIF／測試可用 force
var last_kind := ""
var last_at := -9999.0
var active_kind := ""
var active_a: Walker
var active_b: Walker
var active_t := 0.0
var clock := 0.0
var rng := RandomNumberGenerator.new()

func _ready() -> void:
	rng.randomize()
	var fam: Dictionary = (GameData.personality if GameData else {}).get("family_interactions", {})
	var unit := str(fam.get("interval_unit", "分鐘"))
	var mul := 60.0 if unit.find("分") >= 0 or unit == "min" else 1.0
	# 演示／GIF：GODOT_M1A_DEMO=1 縮短到幾秒內見到互動（正式數值不變）
	if str(OS.get_environment("GODOT_M1A_DEMO")) == "1":
		mul = 0.08
	interval_min = float(fam.get("interval_min", 1)) * mul
	interval_max = float(fam.get("interval_max", 3)) * mul
	no_repeat = float(fam.get("no_repeat_within_min", 10)) * (60.0 if mul >= 1.0 else 1.0)
	if str(OS.get_environment("GODOT_M1A_DEMO")) == "1":
		no_repeat = 6.0
	next_at = rng.randf_range(minf(8.0, interval_min), interval_min + 4.0)


func register(w: Walker, brain: PetBrain) -> void:
	if w == null:
		return
	if walkers.find(w) < 0:
		walkers.append(w)
	brains[w] = brain


func kind_for(w: Walker) -> String:
	if active_kind != "" and (w == active_a or w == active_b):
		return active_kind
	return ""


func other_of(w: Walker) -> Walker:
	for o in walkers:
		if o != w and is_instance_valid(o):
			# 黐人跟最親／最近嗰隻
			return o
	return null


func try_play(w: Walker) -> bool:
	var o := other_of(w)
	if o == null:
		return false
	return start("play_together", w, o)


func _process(dt: float) -> void:
	clock += dt
	if active_kind != "":
		active_t += dt
		if active_t > 14.0:
			_stop()
		return
	if clock >= next_at:
		_try_auto()


func _try_auto() -> void:
	next_at = clock + rng.randf_range(interval_min, interval_max)
	if walkers.size() < 2:
		return
	if clock - last_at < no_repeat and last_kind != "":
		# 仲可以揀唔同種類
		pass
	var kinds := _eligible()
	if kinds.is_empty():
		return
	# 10 分鐘內唔重複同一種
	var filtered: Array = []
	for k in kinds:
		if k != last_kind or clock - last_at >= no_repeat:
			filtered.append(k)
	if filtered.is_empty():
		return
	var kind: String = str(filtered[rng.randi() % filtered.size()])
	var pair := _pair_for(kind)
	if pair.size() < 2:
		return
	start(kind, pair[0], pair[1])


func _eligible() -> Array:
	var out: Array = []
	var night := TimeService and TimeService.hour_band() == "night"
	var care: Dictionary = Sim.state.get("needs", {}) if Sim else {}
	var hunger := float(care.get("hunger", 70))
	# 一齊行：有黐人或者就咁兩隻都喺度
	out.append("walk_together")
	if night:
		out.append("leaf_shelter")
		out.append("sleep_side_by_side")
	if hunger <= 50.0:
		out.append("share_food")
	# 追逐：兩隻活潑／悶
	var lively := 0
	for w in walkers:
		var id := _id_of(w)
		if Personality and Personality.axis(id, "motion") >= 0:
			lively += 1
	if lively >= 1:
		out.append("chase")
	out.append("play_together")
	return out


func _pair_for(_kind: String) -> Array:
	var living: Array = []
	for w in walkers:
		if is_instance_valid(w):
			living.append(w)
	if living.size() < 2:
		return []
	living.shuffle()
	return [living[0], living[1]]


func _id_of(w: Walker) -> String:
	if w and "character" in w:
		return str(w.character)
	return w.name.to_lower() if w else ""


func start(kind: String, a: Walker, b: Walker) -> bool:
	if a == null or b == null or kind == "":
		return false
	_stop()
	active_kind = kind
	active_a = a
	active_b = b
	active_t = 0.0
	last_kind = kind
	last_at = clock
	for w in [a, b]:
		if w:
			w.cancel_move()
	# 開場動作
	match kind:
		"walk_together", "chase":
			if a:
				a.pick_nearby(90.0)
			if b:
				b.follow_node(a, 16.0 if kind == "walk_together" else 10.0)
			if kind == "chase" and a:
				a.speed_mul = maxf(a.speed_mul, 1.25)
				a.play_live_clip("rush")
		"share_food":
			if b:
				b.follow_node(a, 12.0)
			if a:
				a.play_live_clip("eat")
		"sleep_side_by_side":
			if b:
				b.go_to(a.global_position + Vector3(16, 0, 0))
			if a:
				a.play_live_clip("fall_asleep")
		"leaf_shelter":
			if b:
				b.go_to(a.global_position + Vector3(12, 0, 2))
		"play_together":
			if b:
				b.follow_node(a, 14.0)
			if a:
				if not a.play_live_clip("play"):
					a.play_live_clip("rush")
		"welcome_home":
			if a:
				a.play_live_clip("reunion_happy")
			if b:
				b.follow_node(a, 12.0)
	# 打斷行為樹去家庭分支
	for w in [a, b]:
		var br: PetBrain = brains.get(w)
		if br and br.tree:
			br.tree.interrupt()
			br.busy = true
	return true


func force(kind: String) -> bool:
	var pair := _pair_for(kind)
	if pair.size() < 2:
		return false
	return start(kind, pair[0], pair[1])


func tick_actor(w: Walker, brain: PetBrain) -> int:
	if active_kind == "" or (w != active_a and w != active_b):
		return F
	var other: Walker = active_b if w == active_a else active_a
	match active_kind:
		"walk_together":
			if w == active_b and other:
				w.follow_node(other, 16.0)
			elif w == active_a and not w.moving:
				w.pick_nearby(80.0)
		"chase":
			if w == active_a and not w.moving:
				w.pick_nearby(100.0)
			elif w == active_b and other:
				w.follow_node(other, 10.0)
		"share_food":
			if w == active_b and other:
				if w.global_position.distance_to(other.global_position) < 18.0:
					w.play_live_clip("eat")
					w.cancel_move()
				else:
					w.follow_node(other, 12.0)
		"sleep_side_by_side":
			if w.live_clip != "sleep_loop" and w.live_clip != "fall_asleep":
				if not w.play_live_clip("fall_asleep"):
					w.play_live_clip("sleep_loop", true)
			elif w.live_clip == "fall_asleep":
				pass
			elif w.live_clip != "sleep_loop":
				w.play_live_clip("sleep_loop", true)
		"leaf_shelter":
			if other and w.global_position.distance_to(other.global_position) > 16.0:
				w.go_to(other.global_position + Vector3(10, 0, 0))
			elif w.live_clip == "":
				w.play_live_clip("lookup")
		"play_together":
			if w.live_clip == "" and not w.moving:
				if not w.play_live_clip("play"):
					w.play_live_clip("nuzzle")
		"welcome_home":
			if w == active_b and other:
				w.follow_node(other, 12.0)
	if active_t > _duration(active_kind):
		if brain:
			brain.busy = false
			brain._pick_action(true)
		# 兩邊都完先停
		_stop()
		return S
	return R


func _duration(kind: String) -> float:
	match kind:
		"sleep_side_by_side":
			return 8.0
		"chase", "walk_together":
			return 9.0
		"share_food":
			return 5.0
		_:
			return 6.0


func _stop() -> void:
	if active_a:
		active_a.speed_mul = Personality.walk_speed_mul(_id_of(active_a)) if Personality else 1.0
		active_a.cancel_follow()
	if active_b:
		active_b.speed_mul = Personality.walk_speed_mul(_id_of(active_b)) if Personality else 1.0
		active_b.cancel_follow()
	active_kind = ""
	active_a = null
	active_b = null
	active_t = 0.0
