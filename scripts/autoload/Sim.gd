extends Node
## 核心需求／成長模擬（由 JS sim.js 移植；G0 保留 §7 階段＋離線規則）。
## 五路線照顧分要等互動系統，G0 入成體只按 CQ 判燦光／柔光／微塵。

# 玩法數值只由 data/*.json 讀（data/sim.json＋evolution.json），呢度只係容器。
var KEYS: PackedStringArray = ["hunger", "mood", "clean", "energy"]
var STAGES: PackedStringArray = ["egg", "newborn", "sprout", "juvenile", "adult", "elder"]
var DECAY := {}
var STAGE_DECAY := {}
var STAGE_SEC := {}
var START_NEEDS_HATCH := {}
var SLEEP_REGEN := 12.0
var SLEEP_DECAY_MUL := 0.3
var SLEEP_WAKE_AT := 100.0
var SLEEP_MIN_ENERGY := 90.0
var TRAIT_SLEEP_REGEN := 1.2
var TRAIT_CLEAN_DECAY := 1.3
var POOP_INTERVAL_H := 3.0
var POOP_PENALTY_H := 1.0
var POOP_MAX := 3
var SICK := 15.0
var OFF_FULL_H := 8.0
var OFF_CAP_H := 24.0
var OFF_DISC := 0.25
var OFF_FLOOR := 20.0
var OFF_GROW_CAP_H := 24.0
var OFF_MIN_AWAY := 300.0
var OFF_STALL := 2.0
var OFF_GIFT_PER_H := 1.0
var OFF_GIFT_MAX := 10
var CQ_START := 50.0
var CQ_MIN := 0.0
var CQ_MAX := 100.0
var BRIGHT_CQ := 30.0
var SOFT_CQ := 20.0
var AHEAD_H := 24.0

# 照顧回升（data/sim.json care；舊 data.js PARAMS）
var FEED_SNACK := 20.0
var FEED_MEAL := 40.0
var FEED_SOUP := 20.0
var FOOD_MOOD_BONUS := 3.0
var FEED_REFUSE_AT := 90.0
var PLAY_TEASE := 15.0
var PLAY_ENERGY_COST := 3.0
var RINSE := 50.0
var PAT_MOOD := 15.0
signal care_done(act: String, result: Dictionary)

signal state_changed()
signal poops_changed(count: int)
signal stage_changed(stage: String)
signal cleaned()

var state: Dictionary = {}
var _dirty := false
var paused := false

func _ready() -> void:
	_boot_params()
	var loaded := SaveSystem.load_state()
	if loaded.is_empty():
		state = new_state(TimeService.now_ms())
		SaveSystem.save_state(state)
	else:
		state = loaded
	TimeService.catch_up(state)
	TimeService.mark_sim()
	_dirty = true
	state_changed.emit()


func _boot_params() -> void:
	# 遊策單一來源：data/sim.json（衰減／離線／睡眠）＋ data/evolution.json（階段時長）
	var p: Dictionary = GameData.sim if GameData else {}
	var keys_v: Variant = p.get("need_keys", ["hunger", "mood", "clean", "energy"])
	if keys_v is Array or keys_v is PackedStringArray:
		var ks := PackedStringArray()
		for k in keys_v:
			ks.append(str(k))
		if ks.size():
			KEYS = ks
	var dec: Dictionary = p.get("decay_per_hour", {})
	DECAY = {}
	for k in KEYS:
		DECAY[k] = float(dec.get(k, 0.0))
	var sdm: Dictionary = p.get("stage_decay_mul", {})
	STAGE_DECAY = {}
	for k in sdm.keys():
		if str(k).begins_with("_"):
			continue
		STAGE_DECAY[str(k)] = float(sdm[k])
	STAGE_SEC = {}
	for s in GameData.stage_list():
		if s is Dictionary:
			STAGE_SEC[str(s.get("id", ""))] = float(s.get("duration_sec", 0))
	var hatch: Dictionary = p.get("start_needs_hatch", {})
	START_NEEDS_HATCH = {}
	for k in KEYS:
		START_NEEDS_HATCH[k] = float(hatch.get(k, 100.0))
	SLEEP_REGEN = float(p.get("sleep_regen_per_hour", SLEEP_REGEN))
	SLEEP_DECAY_MUL = float(p.get("sleep_decay_mul", SLEEP_DECAY_MUL))
	SLEEP_WAKE_AT = float(p.get("sleep_wake_at", SLEEP_WAKE_AT))
	SLEEP_MIN_ENERGY = float(p.get("sleep_min_energy_to_sleep", SLEEP_MIN_ENERGY))
	TRAIT_SLEEP_REGEN = float(p.get("trait_sleep_regen_mul", TRAIT_SLEEP_REGEN))
	TRAIT_CLEAN_DECAY = float(p.get("trait_clean_decay_mul", TRAIT_CLEAN_DECAY))
	POOP_INTERVAL_H = float(p.get("poop_interval_h", POOP_INTERVAL_H))
	POOP_PENALTY_H = float(p.get("poop_clean_penalty_per_h", POOP_PENALTY_H))
	POOP_MAX = int(p.get("poop_max", POOP_MAX))
	SICK = float(p.get("sick_threshold", SICK))
	OFF_FULL_H = float(p.get("offline_full_h", OFF_FULL_H))
	OFF_CAP_H = float(p.get("offline_cap_h", OFF_CAP_H))
	OFF_DISC = float(p.get("offline_discount_rate", OFF_DISC))
	OFF_FLOOR = float(p.get("offline_need_floor", OFF_FLOOR))
	OFF_GROW_CAP_H = float(p.get("offline_grow_cap_h", OFF_GROW_CAP_H))
	OFF_MIN_AWAY = float(p.get("offline_min_away_sec", OFF_MIN_AWAY))
	OFF_STALL = float(p.get("offline_stall_sec", OFF_STALL))
	OFF_GIFT_PER_H = float(p.get("offline_gift_per_h", OFF_GIFT_PER_H))
	OFF_GIFT_MAX = int(p.get("offline_gift_max", OFF_GIFT_MAX))
	CQ_START = float(p.get("cq_start", CQ_START))
	CQ_MIN = float(p.get("cq_min", CQ_MIN))
	CQ_MAX = float(p.get("cq_max", CQ_MAX))
	AHEAD_H = float(p.get("last_save_max_ahead_h", AHEAD_H))
	var br: Dictionary = p.get("branch_g0", {})
	BRIGHT_CQ = float(br.get("bright_cq", BRIGHT_CQ))
	SOFT_CQ = float(br.get("soft_cq", SOFT_CQ))

	var care: Dictionary = p.get("care", {})
	FEED_SNACK = float(care.get("feed_snack", FEED_SNACK))
	FEED_MEAL = float(care.get("feed_meal", FEED_MEAL))
	FEED_SOUP = float(care.get("feed_soup", FEED_SOUP))
	FOOD_MOOD_BONUS = float(care.get("food_mood_bonus_warm", FOOD_MOOD_BONUS))
	FEED_REFUSE_AT = float(care.get("feed_refuse_at", FEED_REFUSE_AT))
	PLAY_TEASE = float(care.get("play_tease", PLAY_TEASE))
	PLAY_ENERGY_COST = float(care.get("play_energy_cost", PLAY_ENERGY_COST))
	RINSE = float(care.get("rinse", RINSE))
	PAT_MOOD = float(care.get("pat_mood", PAT_MOOD))


func new_state(now_ms: int, seed: int = 0) -> Dictionary:
	return {
		"version": 1,
		"created_at": now_ms,
		"last_seen": now_ms,
		"last_save_time": now_ms,
		"seed": seed if seed != 0 else (now_ms % 1000000000),
		"stage": "egg",
		"form": "",
		"gen": 1,
		"fade_ready": false,
		"needs": {"hunger": 100.0, "mood": 100.0, "clean": 100.0, "energy": 100.0},
		"sleeping": false,
		"poops": 0,
		"poop_timer": 0.0,
		"poop_age": [],
		"growth_sec": 0.0,
		"age_sec": 0.0,
		"cq": CQ_START,
		"grains": 0,
		"ev": [],
		"jobs_day": "",
		"other_day": "",
		"save_resets": 0,
		"save_reset_at": 0,
		"auto_moon_sleep": true,
		"personalities": {},
	}


func is_unwell(s: Dictionary = {}) -> bool:
	if s.is_empty():
		s = state
	if str(s.get("stage", "egg")) == "egg":
		return false
	var n: Dictionary = s.get("needs", {})
	for k in KEYS:
		if float(n.get(k, 100.0)) < SICK:
			return true
	return false


func effective_offline(t_sec: float) -> float:
	var t: float = maxf(0.0, t_sec)
	var h := 3600.0
	var full := minf(t, OFF_FULL_H * h)
	var disc := minf(maxf(t - OFF_FULL_H * h, 0.0), (OFF_CAP_H - OFF_FULL_H) * h)
	return full + disc * OFF_DISC


func step(s: Dictionary, dt: float, opts: Dictionary = {}) -> void:
	var gm := float(opts.get("growth_mul", 1.0))
	s["age_sec"] = float(s.get("age_sec", 0.0)) + dt
	var st := str(s.get("stage", "egg"))
	if st == "egg":
		s["growth_sec"] = float(s.get("growth_sec", 0.0)) + dt * gm
		_check_stage(s)
		return
	var hr := dt / 3600.0
	var dm := float(STAGE_DECAY.get(st, 1.0))
	var slp := bool(s.get("sleeping", false))
	var mul := SLEEP_DECAY_MUL if slp else 1.0
	var n: Dictionary = s.get("needs", {})
	var prev := {"hunger": float(n.get("hunger", 0)), "mood": float(n.get("mood", 0)), "clean": float(n.get("clean", 0)), "energy": float(n.get("energy", 0))}
	n["hunger"] = float(n.get("hunger", 0)) - DECAY["hunger"] * dm * mul * hr
	n["mood"] = float(n.get("mood", 0)) - DECAY["mood"] * dm * mul * hr
	var poops := int(s.get("poops", 0))
	n["clean"] = float(n.get("clean", 0)) - (DECAY["clean"] * TRAIT_CLEAN_DECAY + poops * POOP_PENALTY_H) * dm * mul * hr
	if slp:
		n["energy"] = float(n.get("energy", 0)) + SLEEP_REGEN * TRAIT_SLEEP_REGEN * hr
	else:
		n["energy"] = float(n.get("energy", 0)) - DECAY["energy"] * dm * hr
	for k in KEYS:
		n[k] = clampf(float(n[k]), 0.0, 100.0)
	if slp and float(n["energy"]) >= SLEEP_WAKE_AT:
		s["sleeping"] = false
		n["energy"] = 100.0
		_push_ev(s, {"type": "wake"})
	s["needs"] = n
	s["poop_timer"] = float(s.get("poop_timer", 0.0)) + dt
	var pi := POOP_INTERVAL_H * 3600.0
	while float(s["poop_timer"]) >= pi:
		s["poop_timer"] = float(s["poop_timer"]) - pi
		if int(s.get("poops", 0)) < POOP_MAX:
			s["poops"] = int(s.get("poops", 0)) + 1
			var ages: Array = s.get("poop_age", [])
			ages.append(0.0)
			s["poop_age"] = ages
		if int(s.get("poops", 0)) >= POOP_MAX:
			s["poop_timer"] = 0.0
	if bool(opts.get("offline", false)):
		for k in KEYS:
			n[k] = maxf(float(n[k]), minf(float(prev[k]), OFF_FLOOR))
		s["needs"] = n
	var ages2: Array = s.get("poop_age", [])
	if int(s.get("poops", 0)) > 0:
		for i in range(ages2.size()):
			ages2[i] = minf(1e9, float(ages2[i]) + dt)
		s["poop_age"] = ages2
	elif ages2.size():
		s["poop_age"] = []
	# 線上不適暫停成長；離線成長改由 offline_grow 計（呢度 growth_mul 通常 0）
	if (not is_unwell(s)) or bool(opts.get("offline", false)):
		s["growth_sec"] = float(s.get("growth_sec", 0.0)) + dt * gm
	if not bool(opts.get("offline", false)):
		_check_stage(s)


func advance(s: Dictionary, sec: float, opts: Dictionary = {}, chunk: float = 30.0) -> void:
	var left := maxf(0.0, sec)
	while left > 1e-9:
		var d := minf(chunk, left)
		step(s, d, opts)
		left -= d


func offline_grow(s: Dictionary, t_sec: float) -> Dictionary:
	var g := minf(maxf(0.0, t_sec), OFF_GROW_CAP_H * 3600.0)
	var from := str(s.get("stage", "egg"))
	var r := {"G": g, "from": from, "to": from, "up": false}
	var sec := float(STAGE_SEC.get(from, 0.0))
	if g <= 0.0 or sec <= 0.0:
		return r
	if from == "elder":
		s["growth_sec"] = minf(sec, float(s.get("growth_sec", 0.0)) + g)
		if float(s["growth_sec"]) >= sec and not bool(s.get("fade_ready", false)):
			s["fade_ready"] = true
			_push_ev(s, {"type": "fade_ready", "form": s.get("form", "")})
			r["up"] = true
			r["to"] = "fade"
		return r
	if float(s.get("growth_sec", 0.0)) + g < sec:
		s["growth_sec"] = float(s.get("growth_sec", 0.0)) + g
		return r
	_enter_stage(s, _next_stage(from))
	s["growth_sec"] = 0.0
	r["up"] = true
	r["to"] = str(s.get("stage", from))
	return r


func apply_offline(s: Dictionary, now_ms: int) -> Dictionary:
	var reset := _sanitize_save_time(s, now_ms)
	var last := int(s.get("last_seen", now_ms))
	var t := maxf(0.0, float(now_ms - last) / 1000.0)
	# 回撥：now < last → T=0，唔拉後 last_seen（reset 除外）
	var e := effective_offline(t)
	var before_stage := str(s.get("stage", ""))
	var before_needs: Dictionary = (s.get("needs", {}) as Dictionary).duplicate()
	if e > 0.0:
		advance(s, e, {"offline": true, "growth_mul": 0.0}, 60.0)
	var grow := offline_grow(s, t)
	if reset:
		s["last_seen"] = now_ms
	else:
		s["last_seen"] = max(int(s.get("last_seen", 0)), now_ms)
	var show := t >= OFF_MIN_AWAY
	var rep := {
		"T": t, "E": e, "tampered": reset, "show": show, "skipped": false,
		"stage_changed": str(s.get("stage", "")) != before_stage,
		"withdrawn": false, "grow": grow, "gift": 0,
	}
	if str(s.get("stage", "")) != "egg" and e > 0.0:
		var n: Dictionary = s.get("needs", {})
		for k in KEYS:
			if float(n.get(k, 100)) <= OFF_FLOOR + 0.5 and float(before_needs.get(k, 100)) > OFF_FLOOR:
				rep["withdrawn"] = true
	if show:
		var gift := clampi(int(floor(t / 3600.0 * OFF_GIFT_PER_H)), 1, OFF_GIFT_MAX)
		s["grains"] = int(s.get("grains", 0)) + gift
		rep["gift"] = gift
	return rep


func after_catch_up(rep: Dictionary) -> void:
	_dirty = true
	if bool(rep.get("stage_changed", false)):
		stage_changed.emit(str(state.get("stage", "")))
	poops_changed.emit(int(state.get("poops", 0)))
	state_changed.emit()
	_save_now()


func clean_one() -> bool:
	var n := int(state.get("poops", 0))
	if n <= 0:
		return false
	state["poops"] = n - 1
	var ages: Array = state.get("poop_age", [])
	if ages.size():
		ages.pop_front()
		state["poop_age"] = ages
	_dirty = true
	poops_changed.emit(int(state["poops"]))
	cleaned.emit()
	state_changed.emit()
	return true


func add_poop() -> void:
	if int(state.get("poops", 0)) >= POOP_MAX:
		return
	state["poops"] = int(state.get("poops", 0)) + 1
	var ages: Array = state.get("poop_age", [])
	ages.append(0.0)
	state["poop_age"] = ages
	_dirty = true
	poops_changed.emit(int(state["poops"]))
	state_changed.emit()


func set_sleeping(v: bool) -> void:
	state["sleeping"] = v
	_dirty = true
	state_changed.emit()


func tick(dt: float) -> void:
	# 月眠 20:00–03:00：自動瞓（精力未滿而且唔係啱啱醒爆）
	if bool(state.get("auto_moon_sleep", true)) and str(state.get("stage", "")) != "egg":
		var moon := TimeService.is_moon_sleep()
		if moon and not bool(state.get("sleeping", false)):
			if float((state.get("needs", {}) as Dictionary).get("energy", 100)) < SLEEP_WAKE_AT:
				state["sleeping"] = true
		elif (not moon) and bool(state.get("sleeping", false)):
			# 出月眠窗自動醒（開發者手動瞓仍然跟精力醒）
			pass
	var before_stage := str(state.get("stage", ""))
	var before_poops := int(state.get("poops", 0))
	var before_sleep := bool(state.get("sleeping", false))
	var before_fade := bool(state.get("fade_ready", false))
	step(state, dt, {})
	TimeService.mark_sim()
	state["last_seen"] = TimeService.now_ms()
	# 連續衰減唔做定期全量序列化；只喺階段／便便／睡眠／化光等狀態變咗先寫盤
	if (str(state.get("stage", "")) != before_stage or int(state.get("poops", 0)) != before_poops
			or bool(state.get("sleeping", false)) != before_sleep or bool(state.get("fade_ready", false)) != before_fade):
		_dirty = true
		_save_now()


func _process(dt: float) -> void:
	if paused or state.is_empty():
		return
	tick(minf(dt, 0.25))


func _save_now(force: bool = false) -> void:
	if state.is_empty():
		return
	if not force and not _dirty:
		return
	state["last_save_time"] = TimeService.now_ms()
	SaveSystem.save_state(state)
	_dirty = false


func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_PAUSED or what == NOTIFICATION_WM_CLOSE_REQUEST:
		# 暫停／離開一定寫盤（包括 last_seen），等離線補時對得準
		_dirty = true
		_save_now(true)


func _next_stage(st: String) -> String:
	var i := STAGES.find(st)
	if i < 0 or i >= STAGES.size() - 1:
		return ""
	return STAGES[i + 1]


func _enter_stage(s: Dictionary, st: String) -> void:
	if st == "":
		return
	s["stage"] = st
	if st == "newborn":
		s["form"] = ""
		s["needs"] = START_NEEDS_HATCH.duplicate()
		s["cq"] = CQ_START
		_push_ev(s, {"type": "hatch"})
	elif st == "sprout" or st == "juvenile":
		_push_ev(s, {"type": "grow", "stage": st})
	elif st == "adult":
		var form := decide_form(float(s.get("cq", CQ_START)))
		s["form"] = form
		_push_ev(s, {"type": "evolve", "form": form, "why": "cq_g0"})
		s["cq"] = CQ_START
	elif st == "elder":
		_push_ev(s, {"type": "elder", "form": s.get("form", "")})
	if s == state:
		stage_changed.emit(st)


func _check_stage(s: Dictionary) -> void:
	for _g in range(8):
		var st := str(s.get("stage", "egg"))
		var sec := float(STAGE_SEC.get(st, 0.0))
		if sec <= 0.0 or float(s.get("growth_sec", 0.0)) < sec:
			return
		if st == "elder":
			s["growth_sec"] = sec
			if not bool(s.get("fade_ready", false)):
				s["fade_ready"] = true
				_push_ev(s, {"type": "fade_ready", "form": s.get("form", "")})
			return
		s["growth_sec"] = float(s.get("growth_sec", 0.0)) - sec
		_enter_stage(s, _next_stage(st))


func decide_form(cq: float) -> String:
	# G0：完整 §7 五路線（潮／菇／晶／月／火）要照顧分，未做互動所以未計。
	# 保留 CQ 門檻：燦光 ≥ brightCQ，否則柔光（暫定 soft 門檻），否則微塵。
	if cq >= BRIGHT_CQ:
		return "bright"
	if cq >= SOFT_CQ:
		return "soft"
	return "dust"


func _sanitize_save_time(s: Dictionary, now_ms: int) -> bool:
	var last_save := int(s.get("last_save_time", 0))
	if last_save > 0 and last_save > now_ms + int(AHEAD_H * 3600.0 * 1000.0):
		s["last_save_time"] = now_ms
		s["last_seen"] = now_ms
		s["save_resets"] = int(s.get("save_resets", 0)) + 1
		s["save_reset_at"] = now_ms
		return true
	return false


func _push_ev(s: Dictionary, ev: Dictionary) -> void:
	var arr: Array = s.get("ev", [])
	arr.append(ev)
	s["ev"] = arr


func stage_zh(st: String = "") -> String:
	if st == "":
		st = str(state.get("stage", "egg"))
	var names := {"egg": "光卵", "newborn": "絨點", "sprout": "芽崽", "juvenile": "跳跳期", "adult": "守夜者", "elder": "靜光"}
	var zh := str(names.get(st, st))
	if bool(state.get("fade_ready", false)):
		zh += " · 準備化光"
	return zh


func _day_key(ms: int = 0) -> String:
	if ms == 0:
		ms = TimeService.now_ms() if TimeService else 0
	var d: Dictionary = TimeService.local_dict(ms) if TimeService else {}
	return "%04d-%02d-%02d" % [int(d.get("year", 0)), int(d.get("month", 0)), int(d.get("day", 0))]


func _apply_need(n: Dictionary, key: String, delta: float) -> float:
	var before := float(n.get(key, 0))
	n[key] = clampf(before + delta, 0.0, 100.0)
	return float(n[key]) - before


func feed(food: String = "meal") -> Dictionary:
	var st := str(state.get("stage", "egg"))
	if st == "egg":
		return {"ok": false, "reason": "egg", "act": "feed"}
	if bool(state.get("sleeping", false)):
		return {"ok": false, "reason": "sleeping", "act": "feed"}
	var n: Dictionary = state.get("needs", {})
	if float(n.get("hunger", 0)) >= FEED_REFUSE_AT:
		return {"ok": false, "reason": "full", "act": "feed", "hunger": float(n.get("hunger", 0))}
	var add := FEED_MEAL
	var mood_add := FOOD_MOOD_BONUS
	if food == "snack":
		add = FEED_SNACK
		mood_add = 0.0
	elif food == "soup":
		add = FEED_SOUP
	var dh := _apply_need(n, "hunger", add)
	var dm := _apply_need(n, "mood", mood_add)
	state["needs"] = n
	if Personality:
		Personality.apply_care_act("tuanrong", "eat_together" if food != "snack" else "feed", _day_key())
	_dirty = true
	var rec := {"ok": true, "act": "feed", "food": food, "hunger": dh, "mood": dm}
	_push_ev(state, {"type": "fed", "food": food})
	state_changed.emit()
	care_done.emit("feed", rec)
	return rec


func pat() -> Dictionary:
	var st := str(state.get("stage", "egg"))
	if st == "egg":
		return {"ok": false, "reason": "egg", "act": "pat"}
	var n: Dictionary = state.get("needs", {})
	var dm := _apply_need(n, "mood", PAT_MOOD)
	state["needs"] = n
	if Personality:
		Personality.apply_care_act("tuanrong", "pat", _day_key())
	_dirty = true
	var rec := {"ok": true, "act": "pat", "mood": dm}
	_push_ev(state, {"type": "pat"})
	state_changed.emit()
	care_done.emit("pat", rec)
	return rec


func force_stage(st: String) -> void:
	_enter_stage(state, st)
	_dirty = true
	state_changed.emit()


func clean_all() -> Dictionary:
	var n := 0
	var guard := maxi(int(state.get("poops", 0)), 0) + 2
	while n < guard and clean_one():
		n += 1
	var rec := {"ok": n > 0, "act": "clean", "count": n}
	if n > 0:
		care_done.emit("clean", rec)
	return rec

