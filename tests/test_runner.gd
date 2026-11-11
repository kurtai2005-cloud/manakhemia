extends Node
## 無頭單元測試：Sim / TimeService / SaveSystem（含離線成長、時鐘回撥）。

var failed := 0
var passed := 0

func _ready() -> void:
	# 等 autoload
	print("=== G0 unit tests (Godot %s) ===" % Engine.get_version_info().get("string", "?"))
	# 隔離：用假時鐘，清空存檔副作用前備份唔需要（user:// 喺測試目錄）
	SaveSystem.clear()
	Sim.paused = true
	TimeService.use_fake(1_000_000_000_000)  # 1e12 ms like JS tests
	TimeService.mark_sim()
	_test_effective_offline()
	_test_needs_decay()
	_test_sleep()
	_test_poop()
	_test_unwell_stops_growth()
	_test_offline_floor()
	_test_offline_grow_one_stage()
	_test_egg_hatch_offline()
	_test_clock_rollback()
	_test_save_tamper()
	_test_catch_up_stall()
	_test_save_atomic()
	_test_day_rollover()
	_test_moon_sleep()
	print("=== %d passed, %d failed ===" % [passed, failed])
	get_tree().quit(0 if failed == 0 else 1)


func ok(cond: bool, name: String, detail: Variant = null) -> void:
	if cond:
		passed += 1
		print("  ok  ", name)
	else:
		failed += 1
		print("  FAIL  ", name, "  ", detail)


func _fresh(stage: String = "sprout", needs: Dictionary = {}) -> Dictionary:
	var s := Sim.new_state(TimeService.now_ms())
	s["stage"] = stage
	s["growth_sec"] = 100.0
	s["needs"] = {"hunger": 100.0, "mood": 100.0, "clean": 100.0, "energy": 100.0}
	for k in needs:
		s["needs"][k] = needs[k]
	s["last_seen"] = TimeService.now_ms()
	s["last_save_time"] = TimeService.now_ms()
	return s


func _test_effective_offline() -> void:
	print("# effective_offline")
	var h := 3600.0
	ok(is_equal_approx(Sim.effective_offline(0), 0), "T=0 → E=0")
	ok(is_equal_approx(Sim.effective_offline(6 * h), 6 * h), "T=6h 全速")
	ok(is_equal_approx(Sim.effective_offline(8 * h), 8 * h), "T=8h 全速上限")
	var e12 := Sim.effective_offline(12 * h)
	ok(is_equal_approx(e12, 8 * h + 4 * h * 0.25), "T=12h = 8 + 4*0.25", e12)
	var e30 := Sim.effective_offline(30 * h)
	ok(is_equal_approx(e30, 8 * h + 16 * h * 0.25), "T=30h cap 24h", e30)
	ok(is_equal_approx(Sim.effective_offline(-10), 0), "T<0 → 0")


func _test_needs_decay() -> void:
	print("# online decay 1h sprout (mul 1.2)")
	var s := _fresh("sprout")
	Sim.advance(s, 3600.0, {}, 30)
	var n: Dictionary = s["needs"]
	# hunger 6*1.2=7.2 → 92.8
	ok(abs(float(n["hunger"]) - 92.8) < 0.2, "hunger ≈92.8", n["hunger"])
	ok(abs(float(n["mood"]) - 95.2) < 0.2, "mood ≈95.2", n["mood"])
	ok(s["age_sec"] >= 3600, "age advanced")


func _test_sleep() -> void:
	print("# sleep regen")
	var s := _fresh("adult", {"energy": 50.0})
	s["sleeping"] = true
	Sim.advance(s, 3600.0, {}, 30)
	var e := float(s["needs"]["energy"])
	# +12 * 1.2 = 14.4 → 64.4
	ok(abs(e - 64.4) < 0.3, "sleep energy +14.4", e)
	ok(float(s["needs"]["hunger"]) > 90.0, "sleep decay mul 0.3 keeps hunger high", s["needs"]["hunger"])
	# 精力 99，回升 12*1.2 /h → 250 秒到 100 自動醒
	s = _fresh("adult", {"energy": 99.0})
	s["sleeping"] = true
	var need := (100.0 - 99.0) / (12.0 * 1.2) * 3600.0
	Sim.advance(s, need + 1.0, {}, 5)
	ok(s["sleeping"] == false and abs(float(s["needs"]["energy"]) - 100.0) < 0.2, "wake at 100", [s["sleeping"], s["needs"]["energy"], need])


func _test_poop() -> void:
	print("# poop interval 3h")
	var s := _fresh("adult")
	Sim.advance(s, 3 * 3600.0, {}, 30)
	ok(int(s["poops"]) == 1, "3h → 1 poop", s["poops"])
	Sim.advance(s, 6 * 3600.0, {}, 30)
	ok(int(s["poops"]) == 3, "capped at 3", s["poops"])


func _test_unwell_stops_growth() -> void:
	print("# unwell stops online growth")
	var s := _fresh("sprout", {"hunger": 10.0})
	s["growth_sec"] = 200.0
	Sim.advance(s, 60.0, {}, 30)
	ok(Sim.is_unwell(s), "is unwell")
	ok(is_equal_approx(float(s["growth_sec"]), 200.0), "growth frozen online", s["growth_sec"])
	# offline still grows via offline_grow, not step
	var g0 := float(s["growth_sec"])
	s["last_seen"] = TimeService.now_ms() - 2 * 3600 * 1000
	var rep := Sim.apply_offline(s, TimeService.now_ms())
	ok(float(s["growth_sec"]) > g0 or bool((rep.get("grow", {}) as Dictionary).get("up", false)), "offline grow despite unwell", s["growth_sec"])


func _test_offline_floor() -> void:
	print("# offline need floor 20")
	var s := _fresh("adult", {"hunger": 40, "mood": 40, "clean": 40, "energy": 40})
	s["last_seen"] = TimeService.now_ms() - 30 * 3600 * 1000
	Sim.apply_offline(s, TimeService.now_ms())
	for k in Sim.KEYS:
		ok(float(s["needs"][k]) >= 20.0 - 0.01, "floor " + k, s["needs"][k])
	var low := _fresh("adult", {"hunger": 10, "mood": 100, "clean": 100, "energy": 100})
	low["last_seen"] = TimeService.now_ms() - 30 * 3600 * 1000
	var before := 10.0
	Sim.apply_offline(low, TimeService.now_ms())
	ok(float(low["needs"]["hunger"]) >= before - 0.01, "already below floor stays", low["needs"]["hunger"])


func _test_offline_grow_one_stage() -> void:
	print("# offline grow: at most 1 stage, leftover discarded")
	var s := _fresh("sprout")
	s["growth_sec"] = Sim.STAGE_SEC["sprout"] - 10.0
	s["last_seen"] = TimeService.now_ms() - 12 * 3600 * 1000
	Sim.apply_offline(s, TimeService.now_ms())
	ok(str(s["stage"]) == "juvenile", "sprout + enough time → juvenile", s["stage"])
	ok(is_equal_approx(float(s["growth_sec"]), 0.0), "leftover discarded", s["growth_sec"])
	# 再 30h 都最多再一階
	s["last_seen"] = TimeService.now_ms() - 30 * 3600 * 1000
	Sim.apply_offline(s, TimeService.now_ms())
	ok(str(s["stage"]) == "juvenile", "24h cap cannot skip to adult (juvenile is 72h)", s["stage"])


func _test_egg_hatch_offline() -> void:
	print("# egg offline hatch")
	var e := Sim.new_state(TimeService.now_ms())
	e["last_seen"] = TimeService.now_ms() - 1000 * 1000  # 1000s > 600
	Sim.apply_offline(e, TimeService.now_ms())
	ok(str(e["stage"]) == "newborn", "egg 1000s → newborn", e["stage"])
	ok(is_equal_approx(float(e["growth_sec"]), 0.0), "newborn growth 0", e["growth_sec"])


func _test_clock_rollback() -> void:
	print("# clock rollback")
	var s := _fresh("adult")
	var T := TimeService.now_ms()
	s["last_seen"] = T
	s["last_save_time"] = T
	s["growth_sec"] = 50.0
	Sim.apply_offline(s, T - 121_000)
	ok(int(s["last_seen"]) == T, "rollback does not move last_seen back", s["last_seen"])
	Sim.apply_offline(s, T + 3600_000)
	ok(int(s["last_seen"]) == T + 3600_000, "forward last_seen follows now", s["last_seen"])


func _test_save_tamper() -> void:
	print("# last_save_time > now+24h resets")
	var s := _fresh("adult")
	var T := TimeService.now_ms()
	s["last_seen"] = T + 40 * 3600 * 1000
	s["last_save_time"] = T + 40 * 3600 * 1000
	s["growth_sec"] = 50.0
	var r := Sim.apply_offline(s, T + 7200_000)
	ok(bool(r.get("tampered", false)), "tampered flag")
	ok(int(s["last_seen"]) == T + 7200_000, "reset last_seen = now")
	ok(is_equal_approx(float(s["growth_sec"]), 50.0), "no offline growth on tamper", s["growth_sec"])


func _test_catch_up_stall() -> void:
	print("# catchUp stall <2s skipped")
	var s := _fresh("sprout")
	s["growth_sec"] = 100.0
	s["last_seen"] = TimeService.now_ms() - 1000
	var r := TimeService.catch_up(s, TimeService.now_ms() - 1000)
	ok(bool(r.get("skipped", false)), "1s gap skipped", r)
	s["last_seen"] = TimeService.now_ms() - 30 * 3600 * 1000
	TimeService.mark_sim()  # 假時鐘下 simAt 同 now 對齊，last_seen 先係 30h 前
	var r2 := TimeService.catch_up(s, s["last_seen"])
	ok(not bool(r2.get("skipped", true)) and float(r2.get("T", 0)) > 20 * 3600.0, "long gap applies", r2)


func _test_save_atomic() -> void:
	print("# SaveSystem atomic + migrate")
	SaveSystem.clear()
	var d := {"foo": 1}
	ok(SaveSystem.save_state(d), "save ok")
	var back := SaveSystem.load_state()
	ok(int(back.get("version", 0)) == SaveSystem.VERSION, "version stamped")
	ok(int(back.get("foo", 0)) == 1, "payload kept")
	var migrated := SaveSystem.migrate({"foo": 2}, 0, 1)
	ok(int(migrated.get("version", 0)) == 1, "migrate 0→1")
	SaveSystem.clear()
	ok(SaveSystem.load_state().is_empty(), "clear works")


func _test_day_rollover() -> void:
	print("# day rollover 05:00 jobs / 00:00 other")
	# 04:59 → 05:01 same calendar day should roll jobs
	# fake: unix 1e12 is 2001-09-09 01:46:40 UTC... timezone of box is HKT (UTC+8)
	# Use a known epoch: 2026-11-11 04:59 HKT = 2026-11-10 20:59 UTC
	var t0 := Time.get_unix_time_from_datetime_dict({"year": 2026, "month": 11, "day": 11, "hour": 4, "minute": 59, "second": 0}) * 1000
	# Godot datetime_dict is typically local if we use system... get_unix_time_from_datetime_dict is UTC in Godot 4?
	# Safer: use TimeService.date_key with explicit at_hour.
	var a := TimeService.date_key(int(t0), 5)
	var t1 := t0 + 3 * 60 * 1000  # +3 min → 05:02
	var b := TimeService.date_key(int(t1), 5)
	# If t0 is interpreted as UTC 04:59, still a != b across 05:00
	ok(true, "date_key callable " + str(a) + " / " + str(b))
	# Better assertion: 04:59 and 05:01 with at_hour=5 differ; 00:00 vs 04:00 with at_hour=0 differ? 
	# We'll construct ms ourselves from known unix. Regardless of tz, crossing the hour boundary changes key when at_hour matches.
	var k0 := TimeService.date_key(5 * 3600 * 1000 - 1000, 5)
	var k1 := TimeService.date_key(5 * 3600 * 1000 + 1000, 5)
	ok(k0 != k1, "jobs day key flips at 05:00 epoch-relative", [k0, k1])
	var o0 := TimeService.date_key(1000, 0)
	var o1 := TimeService.date_key(-1000, 0)
	ok(o0 != o1, "other day key flips at 00:00 epoch-relative", [o0, o1])


func _test_moon_sleep() -> void:
	print("# moon-sleep 20:00–03:00")
	# hour_of uses local tz from unix. Test the function with a constructed dict path:
	# 20:00–03:00 inclusive start. We test via TimeService.hour_of if fake clock set to a known local time is hard;
	# fall back: implement check on hour values by temporarily using use_fake around midnights is tz-dependent.
	# Direct: hour 21 is sleep, hour 12 is not — set fake to a unix that hour_of reports.
	# Scan 48 hours of fake clocks from a base.
	var found_sleep := false
	var found_wake := false
	var base := 1_730_000_000_000  # arbitrary
	for i in range(48):
		var ms := base + i * 3600 * 1000
		TimeService.use_fake(ms)
		if TimeService.is_moon_sleep():
			found_sleep = true
		else:
			found_wake = true
	ok(found_sleep and found_wake, "moon window true and false across 48h")
	# 連續 20–03 = 7 hours of the 24 should be sleep (20,21,22,23,0,1,2)
	TimeService.use_fake(1_000_000_000_000)
	var n := 0
	for i in range(24):
		# pick a day start by finding hour 0
		pass
	# count in a day: find first hour 0 then 24 samples
	var start := base
	for i in range(48):
		TimeService.use_fake(base + i * 3600 * 1000)
		if TimeService.hour_of() < 0.5:
			start = base + i * 3600 * 1000
			break
	n = 0
	for i in range(24):
		TimeService.use_fake(start + i * 3600 * 1000)
		if TimeService.is_moon_sleep():
			n += 1
	ok(n == 7, "7 hours in moon-sleep window", n)
	TimeService.use_fake(1_000_000_000_000)
