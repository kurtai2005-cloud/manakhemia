extends Node
## 核心需求／成長模擬（由 JS sim.js 移植；G0 保留 §7 階段＋離線規則）。
## 五路線照顧分要等互動系統，G0 入成體只按 CQ 判燦光／柔光／微塵。

const KEYS: PackedStringArray = ["hunger", "mood", "clean", "energy"]
const STAGES: PackedStringArray = ["egg", "newborn", "sprout", "juvenile", "adult", "elder"]
const DECAY := {"hunger": 6.0, "mood": 4.0, "clean": 3.0, "energy": 5.0}
const STAGE_DECAY := {"egg": 0.0, "newborn": 1.2, "sprout": 1.2, "juvenile": 1.1, "adult": 1.0, "elder": 1.0}
const STAGE_SEC := {"egg": 600.0, "newborn": 21600.0, "sprout": 64800.0, "juvenile": 259200.0, "adult": 604800.0, "elder": 345600.0}
const START_NEEDS_HATCH := {"hunger": 70.0, "mood": 70.0, "clean": 90.0, "energy": 100.0}

const SLEEP_REGEN := 12.0
const SLEEP_DECAY_MUL := 0.3
const SLEEP_WAKE_AT := 100.0
const SLEEP_MIN_ENERGY := 90.0
const TRAIT_SLEEP_REGEN := 1.2
const TRAIT_CLEAN_DECAY := 1.3
const POOP_INTERVAL_H := 3.0
const POOP_PENALTY_H := 1.0
const POOP_MAX := 3
const SICK := 15.0
const OFF_FULL_H := 8.0
const OFF_CAP_H := 24.0
const OFF_DISC := 0.25
const OFF_FLOOR := 20.0
const OFF_GROW_CAP_H := 24.0
const OFF_MIN_AWAY := 300.0
const OFF_STALL := 2.0
const OFF_GIFT_PER_H := 1.0
const OFF_GIFT_MAX := 10
const CQ_START := 50.0
const CQ_MIN := 0.0
const CQ_MAX := 100.0
const BRIGHT_CQ := 30.0
const SOFT_CQ := 20.0  # G0 簡化：CQ 夠就柔光，否則微塵；完整 §7 五路線待互動
const AHEAD_H := 24.0

signal state_changed()
signal poops_changed(count: int)
signal stage_changed(stage: String)
signal cleaned()

var state: Dictionary = {}
var _dirty := false
var _save_acc := 0.0
var paused := false

func _ready() -> void:
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
	step(state, dt, {})
	TimeService.mark_sim()
	state["last_seen"] = TimeService.now_ms()
	_dirty = true
	_save_acc += dt
	if _save_acc >= 15.0:
		_save_acc = 0.0
		_save_now()


func _process(dt: float) -> void:
	if paused or state.is_empty():
		return
	tick(minf(dt, 0.25))


func _save_now() -> void:
	if state.is_empty():
		return
	state["last_save_time"] = TimeService.now_ms()
	SaveSystem.save_state(state)
	_dirty = false


func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_PAUSED or what == NOTIFICATION_WM_CLOSE_REQUEST:
		_save_now()


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
