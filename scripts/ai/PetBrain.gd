extends Node
class_name PetBrain
## 一隻寵物一個 Beehave 樹：性格加權自主行（遊、嗅、瞓、跟家人、一齊玩），玩家撳會插隊。

const S := BeehaveTree.SUCCESS
const F := BeehaveTree.FAILURE
const R := BeehaveTree.RUNNING

var walker: Walker
var actor_id := "tuanrong"
var tree: BeehaveTree
var board: Blackboard
var family: Node  # FamilyDirector
var rng := RandomNumberGenerator.new()
var chosen := "wander"
var rechoose_t := 0.0
var action_t := 0.0
var pending_tap := ""  # "pet" | "poke" | ""
var expr_name := ""
var expr_t := 0.0
var busy := false

func setup(w: Walker, id: String, fam: Node = null) -> void:
	walker = w
	actor_id = id
	family = fam
	rng.randomize()
	if walker:
		walker.brain_driven = true
		walker.speed_mul = Personality.walk_speed_mul(actor_id) if Personality else 1.0
	_build_tree()
	_pick_action(true)


func _build_tree() -> void:
	board = Blackboard.new()
	tree = BeehaveTree.new()
	tree.name = "Beehave_%s" % actor_id
	tree.process_thread = BeehaveTree.ProcessThread.IDLE
	tree.tick_rate = 1
	tree.blackboard = board
	var root := SelectorReactiveComposite.new()
	root.name = "Root"
	# 1) 玩家插隊
	var seq_tap := SequenceComposite.new()
	seq_tap.name = "Tap"
	seq_tap.add_child(_cond("HasTap", func(_a, _b): return pending_tap != ""))
	seq_tap.add_child(_act("ReactTap", _tick_tap))
	root.add_child(seq_tap)
	# 2) 家人之間互動
	var seq_fam := SequenceComposite.new()
	seq_fam.name = "Family"
	seq_fam.add_child(_cond("HasFamily", func(_a, _b): return _family_kind() != ""))
	seq_fam.add_child(_act("DoFamily", _tick_family))
	root.add_child(seq_fam)
	# 3) 自主
	var sel := SelectorComposite.new()
	sel.name = "Auto"
	sel.add_child(_seq_act("nap", "sleep"))
	sel.add_child(_seq_act("follow", "follow_family"))
	sel.add_child(_seq_act("play", "play"))
	sel.add_child(_seq_act("sniff", "sniff"))
	sel.add_child(_act("Wander", _tick_wander))
	root.add_child(sel)
	tree.add_child(root)
	add_child(tree)
	if walker:
		tree.actor_node_path = tree.get_path_to(walker) if walker.is_inside_tree() else NodePath("..")
	tree.enabled = true


func _seq_act(kind: String, wkey: String) -> SequenceComposite:
	var seq := SequenceComposite.new()
	seq.name = kind.capitalize()
	seq.add_child(_cond("Is_%s" % kind, func(_a, _b): return chosen == kind))
	seq.add_child(_act("Do_%s" % kind, func(a, b): return _tick_kind(kind, wkey, a, b)))
	return seq


func _cond(p_name: String, fn: Callable) -> BtCond:
	var c := BtCond.new()
	c.name = p_name
	c.fn = fn
	return c


func _act(p_name: String, fn: Callable) -> BtAct:
	var a := BtAct.new()
	a.name = p_name
	a.fn = fn
	return a


func _family_kind() -> String:
	if family and family.has_method("kind_for"):
		return str(family.kind_for(walker))
	return ""


func notify_tap(kind: String = "pet") -> void:
	pending_tap = kind if kind != "" else "pet"
	if tree:
		tree.interrupt()
	if walker:
		walker.cancel_move()


func _process(dt: float) -> void:
	if expr_t > 0.0:
		expr_t -= dt
		if expr_t <= 0.0:
			expr_name = ""
	if pending_tap != "" or _family_kind() != "":
		return
	rechoose_t -= dt
	if rechoose_t <= 0.0 and not busy:
		_pick_action(false)


func _pick_action(force: bool) -> void:
	var needs: Dictionary = (GameData.personality if GameData else {}).get("needs", {})
	var window: Variant = needs.get("rechoose_sec", [8, 15])
	var lo := 8.0
	var hi := 15.0
	if window is Array and window.size() >= 2:
		lo = float(window[0])
		hi = float(window[1])
	rechoose_t = rng.randf_range(lo, hi)
	var scores := {
		"wander": 1.0,
		"sniff": 0.8 * Personality.act_weight(actor_id, "explore") if Personality else 0.8,
		"nap": 0.5 * Personality.act_weight(actor_id, "sleep") if Personality else 0.5,
		"play": 0.7 * Personality.act_weight(actor_id, "play") if Personality else 0.7,
		"follow": 0.4 * Personality.act_weight(actor_id, "seek_player") if Personality else 0.4,
	}
	# 需求同性格：攰就瞓、悶就玩、黐人就跟
	var care: Dictionary = Sim.state.get("needs", {}) if Sim else {}
	var energy := float(care.get("energy", 70))
	var mood := float(care.get("mood", 70))
	if energy < 40.0:
		scores["nap"] = float(scores["nap"]) + 1.5
	if mood < 45.0:
		scores["play"] = float(scores["play"]) + 1.0
	if Personality and Personality.axis(actor_id, "social") >= 5:
		scores["follow"] = float(scores["follow"]) + 1.2
	if Personality and Personality.axis(actor_id, "motion") <= -5:
		scores["nap"] = float(scores["nap"]) + 0.6
		scores["wander"] = float(scores["wander"]) * 0.7
	if Personality and Personality.axis(actor_id, "motion") >= 5:
		scores["play"] = float(scores["play"]) + 0.8
		scores["wander"] = float(scores["wander"]) + 0.3
	if Personality and Personality.axis(actor_id, "social") <= -5:
		scores["follow"] = float(scores["follow"]) * 0.3
		scores["sniff"] = float(scores["sniff"]) + 0.5
	var jitter := float(needs.get("score_random_pct", 10)) / 100.0
	var best := "wander"
	var best_s := -1.0
	for k in scores.keys():
		var s: float = float(scores[k]) * (1.0 + rng.randf_range(-jitter, jitter))
		if s > best_s:
			best_s = s
			best = str(k)
	if force or best != chosen:
		chosen = best
		action_t = 0.0
		busy = false
		if walker:
			walker.cancel_move()


func _tick_tap(_a: Node, _b: Blackboard) -> int:
	if pending_tap == "":
		return F
	# 摸／戳：表情＋動作（nuzzle／emo_happy），無文字
	if action_t <= 0.0:
		action_t = 0.01
		expr_name = Personality.expr_icon(actor_id) if Personality else "mood_happy"
		expr_t = 2.2
		if walker:
			var clip := "nuzzle"
			if pending_tap == "poke":
				clip = "emo_surprised"
			if not walker.play_live_clip(clip):
				walker.play_live_clip("emo_happy")
			if AudioManager:
				AudioManager.play("sfx_pet_nuzzle_purr" if pending_tap == "pet" else "sfx_pet_curious", walker)
		pending_tap = "running"
	if walker and walker.live_clip != "":
		return R
	pending_tap = ""
	action_t = 0.0
	chosen = "wander"
	return S


func _tick_family(_a: Node, _b: Blackboard) -> int:
	if family and family.has_method("tick_actor"):
		return int(family.tick_actor(walker, self))
	return F


func _tick_kind(kind: String, _wkey: String, _a: Node, _b: Blackboard) -> int:
	if chosen != kind:
		return F
	action_t += get_process_delta_time()
	if kind == "nap":
		return _do_nap()
	if kind == "sniff":
		return _do_sniff()
	if kind == "play":
		return _do_play()
	if kind == "follow":
		return _do_follow()
	return _tick_wander(_a, _b)


func _do_nap() -> int:
	if walker == null:
		return F
	if not busy:
		busy = true
		walker.cancel_move()
		# 文靜用 art-fix1 坐低 idle_quiet
		var quiet := Personality and Personality.primary_type(actor_id) == "文靜"
		if quiet and walker.play_live_clip("idle_quiet", true):
			pass
		elif not walker.play_live_clip("fall_asleep"):
			walker.play_live_clip("yawn")
	if walker.live_clip == "fall_asleep":
		return R
	if walker.live_clip == "idle_quiet":
		if action_t > rng.randf_range(4.0, 8.0):
			walker.stop_live()
			busy = false
			_pick_action(true)
			return S
		return R
	if walker.live_clip != "sleep_loop":
		walker.play_live_clip("sleep_loop", true)
	if action_t > rng.randf_range(4.0, 8.0):
		walker.play_live_clip("wake")
		busy = false
		_pick_action(true)
		return S
	return R


func _do_sniff() -> int:
	if walker == null:
		return F
	if not busy:
		busy = true
		walker.pick_nearby(40.0)
	if walker.moving:
		return R
	if walker.live_clip != "sniff" and walker.live_clip != "sniff_itch":
		if not walker.play_live_clip("sniff"):
			walker.play_live_clip("sniff_itch")
		return R
	if walker.live_clip != "":
		return R
	busy = false
	_pick_action(true)
	return S


func _do_play() -> int:
	if walker == null:
		return F
	# 搵附近家人一齊玩（FamilyDirector 有就交佢；否則自己 play clip）
	if family and family.has_method("try_play") and family.try_play(walker):
		return R
	if not busy:
		busy = true
		if not walker.play_live_clip("play"):
			walker.play_live_clip("rush")
	if walker.live_clip != "":
		return R
	busy = false
	_pick_action(true)
	return S


func _do_follow() -> int:
	if walker == null or family == null or not family.has_method("other_of"):
		return _tick_wander(null, null)
	var other: Walker = family.other_of(walker)
	if other == null:
		return _tick_wander(null, null)
	walker.follow_node(other, 18.0)
	if action_t > rng.randf_range(6.0, 12.0):
		walker.cancel_move()
		_pick_action(true)
		return S
	return R


func _tick_wander(_a: Node, _b: Blackboard) -> int:
	if walker == null:
		return F
	if not walker.moving and walker.live_clip == "":
		var far := Personality.axis(actor_id, "social") <= -5 if Personality else false
		walker.pick_nearby(120.0 if far else 70.0)
	if action_t > rng.randf_range(8.0, 16.0):
		_pick_action(true)
		return S
	action_t += get_process_delta_time()
	# 抵達之後有機會做生命感
	if not walker.moving and walker.live_clip == "" and rng.randf() < 0.02:
		walker.try_liveliness()
	return R


func current_action() -> String:
	if pending_tap != "":
		return "react"
	var fk := _family_kind()
	if fk != "":
		return fk
	return chosen
