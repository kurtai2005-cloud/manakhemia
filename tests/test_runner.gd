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
	_test_gift_on_return()
	_test_rollback_zero_elapsed()
	_test_no_double_catch_up()
	_test_offline_matches_online()
	_test_autosave_only_when_dirty()
	_test_sim_params_from_data()
	_test_art_importer_timing()
	_test_hour_bands()
	_test_audio_actor_pitch()
	_test_walk_fps_not_overridden()
	_test_g01_actor_anim_and_lut()
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


func _test_gift_on_return() -> void:
	print("# light-grain gift on return (sim.js:468-474 offlineMinAwaySec=300, giftPerH=1, giftMax=10)")
	var now := TimeService.now_ms()
	var s := _fresh("adult")
	s["grains"] = 0
	s["last_seen"] = now - 60 * 1000  # 1 min < 5 min
	var r := Sim.apply_offline(s, now)
	ok(not bool(r.get("show", true)) and int(r.get("gift", -1)) == 0, "away 1min → no gift / no summary", r)
	s = _fresh("adult")
	s["grains"] = 0
	s["last_seen"] = now - 10 * 60 * 1000  # 10 min
	r = Sim.apply_offline(s, now)
	ok(bool(r.get("show", false)) and int(r.get("gift", 0)) == 1 and int(s["grains"]) == 1, "away 10min → gift 1", r)
	s = _fresh("adult")
	s["grains"] = 0
	s["last_seen"] = now - 8 * 3600 * 1000
	r = Sim.apply_offline(s, now)
	ok(int(r.get("gift", 0)) == 8 and int(s["grains"]) == 8, "away 8h → gift 8", r)
	s = _fresh("adult")
	s["grains"] = 0
	s["last_seen"] = now - 30 * 3600 * 1000
	r = Sim.apply_offline(s, now)
	ok(int(r.get("gift", 0)) == 10, "away 30h gift capped at 10 (uses T, not E)", r)


func _test_rollback_zero_elapsed() -> void:
	print("# clock rollback = 0 elapsed (sim.js:449 lastSeen 只向前；T=max(0,now-lastSeen))")
	var T := TimeService.now_ms()
	var s := _fresh("adult")
	s["growth_sec"] = 40.0
	s["grains"] = 3
	s["last_seen"] = T
	s["last_save_time"] = T
	var needs0: Dictionary = (s["needs"] as Dictionary).duplicate()
	var r := TimeService.catch_up(s, T)  # sim_at = T, but we'll call apply with past now via catch_up's now=fake
	# catch_up uses now_ms(); set fake back
	TimeService.use_fake(T - 3600_000)
	var r2 := TimeService.catch_up(s)
	ok(bool(r2.get("rollback", false)) and float(r2.get("T", -1)) == 0.0, "rollback report T=0", r2)
	ok(int(s["last_seen"]) == T, "last_seen not moved back", s["last_seen"])
	ok(is_equal_approx(float(s["growth_sec"]), 40.0), "no growth on rollback")
	ok(int(s["grains"]) == 3, "no gift on rollback")
	for k in Sim.KEYS:
		ok(is_equal_approx(float(s["needs"][k]), float(needs0[k])), "need unchanged " + k, s["needs"][k])
	TimeService.use_fake(T)


func _test_no_double_catch_up() -> void:
	print("# no double catch-up across resume/focus (sim.js:442-453 catchUp + lastSeen)")
	var now := TimeService.now_ms()
	var s := _fresh("sprout")
	s["growth_sec"] = 100.0
	s["last_seen"] = now - 8 * 3600 * 1000
	s["last_save_time"] = s["last_seen"]
	TimeService.mark_sim()
	var r1 := TimeService.catch_up(s, s["last_seen"])
	var g1 := float(s["growth_sec"])
	var n1 := float(s["needs"]["hunger"])
	var grains1 := int(s["grains"])
	# 模擬 focus 緊跟 resume：同一牆鐘再 catch_up 一次
	var r2 := TimeService.catch_up(s, s["last_seen"])
	ok(not bool(r1.get("skipped", true)) and float(r1.get("T", 0)) > 7 * 3600.0, "first pass applies 8h", r1)
	ok(bool(r2.get("skipped", false)) or bool(r2.get("duplicate", false)), "second pass skipped", r2)
	ok(is_equal_approx(float(s["growth_sec"]), g1), "growth not doubled", s["growth_sec"])
	ok(is_equal_approx(float(s["needs"]["hunger"]), n1), "needs not doubled", s["needs"]["hunger"])
	ok(int(s["grains"]) == grains1, "gift not doubled", s["grains"])


func _test_offline_matches_online() -> void:
	print("# 10min/1h/8h offline vs staying open = identical (sim.js:55-60 E=T when T<=8h; :411 floor only if hit; growth T)")
	for sec in [10 * 60, 3600, 8 * 3600]:
		var label := "%s offline vs online" % ("10min" if sec == 600 else ("1h" if sec == 3600 else "8h"))
		var on := _fresh("sprout")
		on["growth_sec"] = 1000.0
		on["poops"] = 0
		on["poop_timer"] = 0.0
		on["sleeping"] = false
		var off := on.duplicate(true)
		Sim.advance(on, float(sec), {}, 30)
		off["last_seen"] = TimeService.now_ms() - sec * 1000
		off["last_save_time"] = off["last_seen"]
		Sim.apply_offline(off, TimeService.now_ms())
		ok(str(on["stage"]) == str(off["stage"]), label + " stage", [on["stage"], off["stage"]])
		ok(abs(float(on["growth_sec"]) - float(off["growth_sec"])) < 0.5, label + " growth", [on["growth_sec"], off["growth_sec"]])
		ok(int(on["poops"]) == int(off["poops"]), label + " poops", [on["poops"], off["poops"]])
		for k in Sim.KEYS:
			ok(abs(float(on["needs"][k]) - float(off["needs"][k])) < 0.15, label + " " + k, [on["needs"][k], off["needs"][k]])


func _test_autosave_only_when_dirty() -> void:
	print("# autosave only when state changed (no 15s periodic serialize)")
	SaveSystem.clear()
	var s := _fresh("sprout")
	Sim.state = s
	Sim.paused = true
	Sim._dirty = false
	# 純 tick 衰減唔應該寫盤
	var wrote := false
	# _save_now 唔 dirty 就 skip
	Sim._save_now(false)
	ok(SaveSystem.load_state().is_empty(), "no write when not dirty")
	Sim._dirty = true
	Sim._save_now()
	var loaded := SaveSystem.load_state()
	ok(not loaded.is_empty() and str(loaded.get("stage", "")) == "sprout", "write when dirty")
	SaveSystem.clear()
	Sim.state = s


func _test_sim_params_from_data() -> void:
	print("# gameplay numbers only from data/sim.json + evolution.json (no hardcoded care/offline)")
	var p: Dictionary = GameData.sim
	ok(not p.is_empty(), "data/sim.json loaded")
	ok(is_equal_approx(Sim.OFF_FLOOR, float(p.get("offline_need_floor", -1))), "OFF_FLOOR from sim.json")
	ok(is_equal_approx(Sim.OFF_FULL_H, float(p.get("offline_full_h", -1))), "OFF_FULL_H from sim.json")
	ok(is_equal_approx(Sim.OFF_GROW_CAP_H, float(p.get("offline_grow_cap_h", -1))), "OFF_GROW_CAP_H from sim.json")
	ok(is_equal_approx(float(Sim.DECAY["hunger"]), float(p["decay_per_hour"]["hunger"])), "hunger decay from sim.json")
	ok(is_equal_approx(Sim.STAGE_SEC["sprout"], GameData.stage_duration("sprout")), "sprout duration from evolution.json")
	ok(is_equal_approx(Sim.STAGE_SEC["sprout"], 64800.0), "sprout 64800 (data.js / evolution.json)")
	ok(is_equal_approx(Sim.STAGE_SEC["egg"], 600.0), "egg 600s from evolution.json")


func _test_art_importer_timing() -> void:
	print("# ArtImporter: clip timing + SFX from anim_timing.json (fallback CLIPS frames/fps)")
	ok(ArtImporter != null, "ArtImporter autoload")
	var scratch: Dictionary = ArtImporter.clip_timing("scratch")
	ok(int(scratch.get("frames", 0)) == 6, "scratch 6 frames from timing", scratch)
	ok(abs(ArtImporter.frame_duration_sec("scratch", 0) - 0.125) < 0.02, "scratch frame duration from anim_timing", ArtImporter.frame_duration_sec("scratch", 0))
	var sneeze_frames: Array = ArtImporter.frames_of("sneeze")
	ok(sneeze_frames.size() == 5, "sneeze atlas frames", sneeze_frames.size())
	var cues: Array = ArtImporter.sfx_cues("sneeze")
	ok(cues.size() >= 1 and str(cues[0].get("id", "")) == "sneeze", "sneeze SFX cue from anim_timing", cues)
	ok(int(cues[0].get("frame", 0)) == 3, "sneeze cue at frame 3", cues[0])
	var pool: PackedStringArray = ArtImporter.liveliness_idle_pool()
	ok(pool.size() >= 3, "liveliness pool has scratch/sneeze/sniff", pool)
	ok(ArtImporter.frames_of("nuzzle").size() == 6, "nuzzle frames ready")
	ok(ArtImporter.frames_of("rush").size() == 6, "rush frames ready")
	ok(not ArtImporter.environments.is_empty() or ArtImporter.import_docs.size() > 0, "godot_import / environments ingested")


func _test_hour_bands() -> void:
	print("# hour_of 四段 05–11／11–17／17–22／22–05（唔用 is_moon_sleep 20–03）")
	# 用假時鐘：造一個已知 UTC 時刻再加 tz bias。直接用 hour_of 需要 now；我們用 unix 日期造 ms。
	# local_dict 用 now_ms/1000 + tz_bias。造「本地鐘」：選一個 UTC 令本地 hour 準確。
	var bias_h := float(TimeService.tz_bias_min()) / 60.0
	# 2026-11-11 00:00 UTC + 每個目標本地小時
	var base_utc := 1762819200  # 2026-11-11 00:00:00 UTC
	var cases := [
		[4.0, "night"], [5.0, "morning"], [10.0, "morning"],
		[11.0, "noon"], [16.0, "noon"],
		[17.0, "evening"], [21.0, "evening"],
		[22.0, "night"], [0.0, "night"], [2.0, "night"],
	]
	# moon-sleep 20–03 同 hour_band 夜段（22–05）唔同：20:00 係 evening
	ok(TimeService.hour_band(_local_ms(20)) == "evening", "20:00 is evening not moon-sleep night", TimeService.hour_band(_local_ms(20)))
	for c in cases:
		var h: float = c[0]
		var want: String = c[1]
		var got := TimeService.hour_band(_local_ms(h))
		ok(got == want, "hour %.0f → %s" % [h, want], got)


func _local_ms(local_hour: float) -> int:
	# TimeService.local_dict：unix = ms/1000 + tz_bias_min*60，再用 UTC parser 當本地。
	# 即 ms/1000 = 本地 unix - bias*60。用 2026-11-11 本地 00:00 + hour。
	var bias := TimeService.tz_bias_min() * 60
	var local_midnight_as_utc := Time.get_unix_time_from_datetime_dict({
		"year": 2026, "month": 11, "day": 11, "hour": 0, "minute": 0, "second": 0,
	})
	# 我哋想 local_dict(ms) hour = local_hour。
	# unix_for_parser = ms/1000 + bias = local_midnight_as_utc + local_hour*3600
	# ms/1000 = local_midnight_as_utc + local_hour*3600 - bias
	var sec := int(local_midnight_as_utc + local_hour * 3600.0) - bias
	return sec * 1000


func _test_audio_actor_pitch() -> void:
	print("# AudioManager.play(hook, actor)：聲由做動作嗰隻出，pitch 跟體型；null hook 靜音")
	ok(AudioManager != null, "AudioManager autoload")
	ok(is_equal_approx(AudioManager.size_pitch("S"), 1.12), "S pitch 1.12")
	ok(is_equal_approx(AudioManager.size_pitch("M"), 1.0), "M pitch 1.0")
	ok(is_equal_approx(AudioManager.size_pitch("L"), 0.88), "L pitch 0.88")
	var pet := Walker.new()
	pet.name = "Pet"
	pet.character = "tuanrong"
	pet.body_size = "L"
	var kid := Walker.new()
	kid.name = "Kid"
	kid.character = "kid"
	kid.body_size = "M"
	var vis := Walker.new()
	vis.name = "Visitor"
	vis.character = "visitor"
	vis.body_size = "S"
	# 通用：scratch／腳步，共用檔 + 體型變速
	var r_pet: Dictionary = AudioManager.resolve_play("sfx_pet_scratch_a", pet)
	ok(not bool(r_pet.get("silent", true)), "tuanrong scratch not silent", r_pet)
	ok(str(r_pet.get("character", "")) == "tuanrong" and str(r_pet.get("size", "")) == "L", "scratch actor is tuanrong L", r_pet)
	ok(is_equal_approx(float(r_pet.get("pitch", 0)), 0.88), "tuanrong L scratch pitch 0.88", r_pet)
	var r_kid: Dictionary = AudioManager.resolve_play("sfx_pet_scratch_a", kid)
	ok(str(r_kid.get("character", "")) == "kid" and str(r_kid.get("actor", "")) == "Kid", "scratch actor is kid", r_kid)
	ok(is_equal_approx(float(r_kid.get("pitch", 0)), 1.0), "kid M scratch pitch 1.0", r_kid)
	var r_step: Dictionary = AudioManager.resolve_play("sfx_pet_step_hop_a", vis)
	ok(str(r_step.get("actor", "")) == "Visitor", "step actor is visitor", r_step)
	ok(is_equal_approx(float(r_step.get("pitch", 0)), 1.12), "visitor S hop pitch 1.12", r_step)
	# 有聲線：先查 sfx_pet_sneeze_<character>_a/b，冇就團絨檔 + 體型變速
	var r_sn: Dictionary = AudioManager.resolve_play("sfx_pet_sneeze_a", kid)
	ok(not bool(r_sn.get("silent", true)), "kid sneeze falls back, not silent", r_sn)
	ok(str(r_sn.get("character", "")) == "kid", "sneeze character is kid not forced tuanrong", r_sn)
	ok(bool(r_sn.get("fallback", false)), "kid sneeze uses tuanrong file fallback", r_sn)
	ok(is_equal_approx(float(r_sn.get("pitch", 0)), 1.0), "kid sneeze fallback pitch M 1.0", r_sn)
	ok(str(r_sn.get("stream", "")).find("sneeze") >= 0, "sneeze stream is sneeze file", r_sn)
	var r_sn_l: Dictionary = AudioManager.resolve_play("sfx_pet_sneeze_a", pet)
	ok(is_equal_approx(float(r_sn_l.get("pitch", 0)), 0.88), "tuanrong L sneeze pitch 0.88", r_sn_l)
	# null hook 靜音
	var r_null: Dictionary = AudioManager.resolve_play(null, pet)
	ok(bool(r_null.get("silent", false)), "null hook is silent", r_null)
	var r_empty: Dictionary = AudioManager.resolve_play("", pet)
	ok(bool(r_empty.get("silent", false)), "empty hook is silent")
	# sniff 官方 hook 可為 null
	var sniff_cues: Array = ArtImporter.sfx_cues("sniff")
	if sniff_cues.size() and sniff_cues[0].get("sfx_hook", "x") == null:
		var r_sniff: Dictionary = AudioManager.resolve_play(sniff_cues[0].get("sfx_hook"), kid)
		ok(bool(r_sniff.get("silent", false)), "null sniff hook silent")
	# 細佬／訪客都可以用 scratch／sneeze／sniff（唔按物種關 clip）
	ok(ArtImporter.liveliness_idle_pool().size() >= 3, "shared liveliness pool still open")
	ok(ArtImporter.frames_of("scratch").size() == 6, "shared scratch frames available to all sizes")
	pet.free()
	kid.free()
	vis.free()


func _test_walk_fps_not_overridden() -> void:
	print("# Walker walk_fps 唔被團絨 walk_happy 蓋過（細佬由 data 讀 10 fps）")
	var w := Walker.new()
	w.walk_fps = ArtImporter.actor_walk_fps("kid")
	w.idle_fps = ArtImporter.actor_idle_fps("kid")
	w.moving = true
	ok(is_equal_approx(w.current_anim_fps(), 10.0), "kid walk stays 10 fps from data", w.current_anim_fps())
	w.moving = false
	ok(is_equal_approx(w.current_anim_fps(), 4.0), "idle stays 4 fps")
	w.free()


func _test_g01_actor_anim_and_lut() -> void:
	print("# G0.1：A1 pivot (24,45)、細佬 walk 10 fps、生命感 fallback、夜 LUT 檔")
	ok(ArtImporter.liveliness_pivot("M") == Vector2(24, 45), "M liveliness pivot is (24, 45) not 46", ArtImporter.liveliness_pivot("M"))
	ok(ArtImporter.liveliness_pivot("L") == Vector2(32, 61), "L pivot (32, 61)")
	ok(ArtImporter.liveliness_pivot("S") == Vector2(16, 29), "S pivot (16, 29)")
	ok(ArtImporter.actor_pivot("kid") == Vector2(24, 45), "kid actor pivot from data/actor_anim.json", ArtImporter.actor_pivot("kid"))
	ok(ArtImporter.actor_pivot("visitor") == Vector2(24, 45), "visitor pivot (24, 45)")
	ok(is_equal_approx(ArtImporter.actor_walk_fps("kid"), 10.0), "kid walk fps 10 from data", ArtImporter.actor_walk_fps("kid"))
	var shared: Array = ArtImporter.frames_of("scratch")
	var mid: Array = ArtImporter.frames_of("scratch", "M")
	ok(shared.size() == 6, "shared scratch frames", shared.size())
	ok(mid.size() == shared.size(), "M liveliness falls back to shared frames when M atlas missing", mid.size())
	ok(FileAccess.file_exists("res://art-pet/fx/luts/lut_night.png"), "lut_night present")
	ok(FileAccess.file_exists("res://art-pet/fx/luts/lut_dusk.png"), "lut_dusk present")
	ok(FileAccess.file_exists("res://art-pet/fx/luts/lut_day.png"), "lut_day present")
	ok(FileAccess.file_exists("res://data/actor_anim.json"), "actor_anim.json present")
	var w := Walker.new()
	w.body_size = "M"
	w.character = "kid"
	ok(w.body_size == "M", "kid walker size M")
	w.free()
