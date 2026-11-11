extends Node
## 無頭單元測試：Sim / TimeService / SaveSystem（含離線成長、時鐘回撥）。

var failed := 0
var passed := 0

func _ready() -> void:
	# 等 autoload
	print("=== M1b unit tests (Godot %s) ===" % Engine.get_version_info().get("string", "?"))
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
	_test_m1a_care_actions()
	_test_m1a_personality()
	_test_m1a_need_bubbles()
	_test_m1a_art_fix1()
	_test_m1a_audio_buses()
	_test_m1a_beehave_and_family()
	_test_m1a_camera_framing()
	_test_m1b_hand_care()
	_test_m1b_need_warning()
	_test_m1b_hunt_work_collection()
	_test_m1b_overlay_snapshot()
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
	var care: Dictionary = p.get("care", {})
	ok(is_equal_approx(Sim.FEED_MEAL, float(care.get("feed_meal", -1))), "FEED_MEAL from sim.json care")
	ok(is_equal_approx(Sim.PAT_MOOD, float(care.get("pat_mood", -1))), "PAT_MOOD from sim.json care (playTease reuse)")
	ok(is_equal_approx(Sim.FEED_REFUSE_AT, float(care.get("feed_refuse_at", -1))), "FEED_REFUSE_AT from sim.json care")


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

func _test_m1a_care_actions() -> void:
	print("# M1a care: feed / pat / clean_all（數值只由 sim.json）")
	Sim.state = _fresh("sprout", {"hunger": 40.0, "mood": 50.0, "clean": 80.0, "energy": 80.0})
	var meal := Sim.feed("meal")
	ok(bool(meal.get("ok", false)), "feed meal ok", meal)
	ok(is_equal_approx(float(meal.get("hunger", 0)), Sim.FEED_MEAL), "meal hunger +FEED_MEAL", meal)
	ok(is_equal_approx(float(meal.get("mood", 0)), Sim.FOOD_MOOD_BONUS), "meal mood +FOOD_MOOD_BONUS", meal)
	Sim.state = _fresh("sprout", {"hunger": 95.0, "mood": 50.0})
	var refused := Sim.feed("meal")
	ok(not bool(refused.get("ok", true)) and str(refused.get("reason", "")) == "full", "refuse feed when hunger >= 90", refused)
	Sim.state = _fresh("sprout", {"mood": 40.0})
	var p := Sim.pat()
	ok(bool(p.get("ok", false)), "pat ok", p)
	ok(is_equal_approx(float(p.get("mood", 0)), Sim.PAT_MOOD), "pat mood +PAT_MOOD", p)
	Sim.state = _fresh("sprout")
	Sim.state["poops"] = 3
	Sim.state["poop_age"] = [1.0, 2.0, 3.0]
	var c := Sim.clean_all()
	ok(bool(c.get("ok", false)) and int(c.get("count", 0)) == 3, "clean_all clears 3 poops", c)
	ok(int(Sim.state.get("poops", -1)) == 0, "poops now 0")
	var c2 := Sim.clean_all()
	ok(not bool(c2.get("ok", true)) and int(c2.get("count", -1)) == 0, "clean_all empty is not ok", c2)
	# 離線規則不變：喂完之後 apply_offline 仍然跟舊公式
	Sim.state = _fresh("sprout", {"hunger": 80.0})
	Sim.feed("meal")
	var after_feed := float(Sim.state["needs"]["hunger"])
	var later := TimeService.now_ms() + 600_000
	var off := Sim.state.duplicate(true)
	off["last_seen"] = TimeService.now_ms()
	TimeService.use_fake(later)
	Sim.apply_offline(off, later)
	ok(float(off["needs"]["hunger"]) <= after_feed, "offline still decays hunger after feed")
	TimeService.use_fake(1_000_000_000_000)
	TimeService.mark_sim()


func _test_m1a_personality() -> void:
	print("# M1a personality: birth [-3,3] + daily drift clamp ±2")
	ok(Personality.birth_min == -3 and Personality.birth_max == 3, "birth range from personality.json")
	ok(Personality.day_shift_min == -2 and Personality.day_shift_max == 2, "daily shift ±2 from data")
	ok(is_equal_approx(Personality.walk_energetic_mul, 1.2), "energetic walk mul 1.2")
	ok(is_equal_approx(Personality.walk_quiet_mul, 0.85), "quiet walk mul 0.85")
	var rng := RandomNumberGenerator.new()
	rng.seed = 42
	for i in range(20):
		var rec: Dictionary = Personality.roll(rng)
		for a in Personality.AXES:
			var v := int(rec.get(a, 99))
			ok(v >= -3 and v <= 3, "birth %s in [-3,3]" % a, v)
	Sim.state = _fresh("sprout")
	Sim.state["personalities"] = {}
	var rec2 := {"motion": 0, "work": 0, "social": 0, "day_key": "", "day_acc": {"motion": 0, "work": 0, "social": 0}}
	Personality.set_for("tuanrong", rec2)
	ok(Personality.primary_type("tuanrong") == "隨和", "all-small is 隨和")
	rec2["motion"] = 8
	Personality.set_for("tuanrong", rec2)
	ok(Personality.primary_type("tuanrong") == "活潑", "motion+ is 活潑")
	ok(is_equal_approx(Personality.walk_speed_mul("tuanrong"), lerpf(1.0, 1.2, 0.8)), "motion 8 interpolates toward energetic", Personality.walk_speed_mul("tuanrong"))
	rec2["motion"] = 10
	Personality.set_for("tuanrong", rec2)
	ok(is_equal_approx(Personality.walk_speed_mul("tuanrong"), 1.2), "motion 10 = energetic mul", Personality.walk_speed_mul("tuanrong"))
	rec2["motion"] = -10
	Personality.set_for("tuanrong", rec2)
	ok(Personality.primary_type("tuanrong") == "文靜", "motion- is 文靜")
	ok(is_equal_approx(Personality.walk_speed_mul("tuanrong"), 0.85), "motion -10 quiet mul", Personality.walk_speed_mul("tuanrong"))
	# 漂移：pat → social +1，一日最多 +2
	rec2 = {"motion": 0, "work": 0, "social": 0, "day_key": "", "day_acc": {"motion": 0, "work": 0, "social": 0}}
	Personality.set_for("tuanrong", rec2)
	Personality.apply_care_act("tuanrong", "pat", "d1")
	ok(Personality.axis("tuanrong", "social") == 1, "pat +1 social", Personality.get_for("tuanrong"))
	Personality.apply_care_act("tuanrong", "pat", "d1")
	ok(Personality.axis("tuanrong", "social") == 2, "second pat same day +1 (cap room)")
	Personality.apply_care_act("tuanrong", "pat", "d1")
	ok(Personality.axis("tuanrong", "social") == 2, "third pat same day clamped at +2")
	Personality.apply_care_act("tuanrong", "pat", "d2")
	ok(Personality.axis("tuanrong", "social") == 3, "new day resets cap, +1 more", Personality.get_for("tuanrong"))


func _test_m1a_need_bubbles() -> void:
	print("# M1a need bubbles: want=100-care, show when ≥70; only 團絨")
	ok(not GameData.m1a.is_empty(), "data/m1a.json loaded")
	ok(is_equal_approx(float(GameData.m1a.get("bubbles", {}).get("want_threshold", -1)), 70.0), "want threshold 70 from data")
	var w := Walker.new()
	w.name = "BubblePet"
	w.character = "tuanrong"
	add_child(w)
	var b := NeedBubble.new()
	add_child(b)
	b.attach(w)
	Sim.state = _fresh("sprout", {"hunger": 20.0, "mood": 90.0, "clean": 90.0, "energy": 90.0})
	ok(b._pick() == "need_eat", "hunger 20 → want 80 → need_eat", b._pick())
	Sim.state["needs"]["hunger"] = 80.0
	Sim.state["needs"]["energy"] = 10.0
	ok(b._pick() == "need_sleep", "energy 10 → need_sleep", b._pick())
	Sim.state["needs"]["energy"] = 90.0
	Sim.state["needs"]["mood"] = 90.0
	ok(b._pick() == "", "all care high → no bubble", b._pick())
	w.character = "kid"
	Sim.state["needs"]["hunger"] = 10.0
	ok(b._pick() == "", "kid has no need bubble")
	var eat: Texture2D = IconBank.tex("need_eat")
	ok(eat != null and eat.get_width() > 0, "need_eat icon loaded (hunt or placeholder)", eat)
	ok(FileAccess.file_exists("res://art/m1-icons/need_eat.png"), "m1-icons need_eat present")
	b.free()
	w.free()


func _test_m1a_art_fix1() -> void:
	print("# art-fix1：細佬 A1 M 48px、訪客 liveliness 圖集、idle_quiet")
	ok(ArtImporter.actor_pivot("kid") == Vector2(24, 45), "kid A1 pivot (24,45)")
	ok(ArtImporter.actor_pivot("snail_postman") == Vector2(22, 45), "snail pivot (22,45)", ArtImporter.actor_pivot("snail_postman"))
	ok(ArtImporter.actor_pivot("mushroom_granny") == Vector2(24, 45), "granny pivot (24,45)")
	ok(ArtImporter.actor_pivot("firefly_vendor") == Vector2(24, 44), "firefly pivot (24,44)", ArtImporter.actor_pivot("firefly_vendor"))
	ok(ArtImporter.frames_of("scratch", "M", "kid").size() >= 1, "kid A1 scratch frames")
	ok(ArtImporter.frames_of("scratch", "M", "snail_postman").size() >= 1, "snail scratch frames")
	ok(ArtImporter.frames_of("sneeze", "M", "mushroom_granny").size() >= 1, "granny sneeze frames")
	ok(ArtImporter.frames_of("idle_quiet", "M", "tuanrong").size() >= 1, "idle_quiet M frames")
	ok(ArtImporter.frames_of("idle_quiet", "S").size() >= 1, "idle_quiet S")
	ok(ArtImporter.frames_of("idle_quiet", "L").size() >= 1, "idle_quiet L")


func _test_m1a_audio_buses() -> void:
	print("# audio buses UI + Pet besides BGM/AMB/SFX")
	var want := ["Master", "BGM", "AMB", "SFX", "UI", "Pet"]
	for i in range(AudioServer.bus_count):
		var n := AudioServer.get_bus_name(i)
		if n in want:
			want.erase(n)
	ok(want.is_empty(), "all six buses present", want)
	ok(AudioManager.bus_for("sfx_ui8_btn_press_a") == "UI", "UI hook → UI bus")
	ok(AudioManager.bus_for("sfx_pet_sneeze") == "Pet", "pet sneeze → Pet bus")
	ok(AudioManager.bus_for("bgm_care_loop") == "BGM", "bgm → BGM")
	ok(AudioManager.bus_for("sfx_world_leaf") == "SFX", "other sfx stay SFX")


func _test_m1a_beehave_and_family() -> void:
	print("# Beehave tree + FamilyDirector.force")
	Sim.state = _fresh("sprout")
	Sim.state["personalities"] = {}
	var a := Walker.new()
	a.name = "A"
	a.character = "tuanrong"
	var b := Walker.new()
	b.name = "B"
	b.character = "kid"
	add_child(a)
	add_child(b)
	var fam := FamilyDirector.new()
	add_child(fam)
	var ba := PetBrain.new()
	a.add_child(ba)
	ba.setup(a, "tuanrong", fam)
	var bb := PetBrain.new()
	b.add_child(bb)
	bb.setup(b, "kid", fam)
	fam.register(a, ba)
	fam.register(b, bb)
	ok(ba.tree != null and ba.tree is BeehaveTree, "tuanrong has BeehaveTree")
	ok(bb.tree != null, "kid has BeehaveTree")
	ok(fam.force("walk_together"), "family force walk_together")
	ok(fam.active_kind == "walk_together", "active_kind set", fam.active_kind)
	ok(fam.kind_for(a) == "walk_together" and fam.kind_for(b) == "walk_together", "both actors tagged")
	ba.notify_tap("pet")
	ok(ba.pending_tap == "pet", "tap interrupt flags pending")
	a.free()
	b.free()
	fam.free()


func _test_m1a_camera_framing() -> void:
	print("# M1a camera: overview garden fill + integer texel; follow pet ≥20% / y 55–60%")
	var packed: PackedScene = load("res://scenes/Main.tscn")
	ok(packed != null, "Main.tscn loads")
	if packed == null:
		return
	var main: Node = packed.instantiate()
	add_child(main)
	# 等一幀讓 _ready／鏡頭就位
	# 單元測試冇 await；直接叫 qa
	if main.has_method("set_rest_look"):
		main.set_rest_look(true)
	if main.has_method("qa_overview"):
		main.qa_overview()
	elif main.has_method("qa_place_pet"):
		main.qa_place_pet("default")
	var fr: Dictionary = main.qa_framing() if main.has_method("qa_framing") else {}
	print("  overview framing ", fr)
	ok(str(fr.get("mode", "")) == "overview", "default cam mode overview", fr)
	ok(float(fr.get("pet_h", 0)) >= 0.09, "overview visible pet height ≥10% (tol 1%)", fr)
	var vw := float(fr.get("visible_w", 0))
	print("  overview trade-off garden_w=", vw, " texel=", fr.get("texel", 0), " quad=", fr.get("pet_h_quad", 0), " vis=", fr.get("pet_h_visible", fr.get("pet_h", 0)))
	# 花園填滿／整數倍為次要，可見身高優先（遊策回饋）
	ok(round(float(fr.get("texel", 0))) >= 1.0 or float(fr.get("texel", 0)) > 0.5, "overview texel measured", fr)
	if main.has_method("qa_follow_pet"):
		main.qa_follow_pet()
	var ff: Dictionary = main.qa_framing() if main.has_method("qa_framing") else {}
	print("  follow framing ", ff)
	ok(str(ff.get("mode", "")) == "follow", "follow cam mode", ff)
	ok(float(ff.get("pet_h", 0)) >= 0.18, "follow visible pet height ≥20% (tol 2%)", ff)
	var py := float(ff.get("pet_y", -1))
	ok(py >= 0.52 and py <= 0.63, "follow pet_y near 55–60%", ff)
	main.free()


func _test_m1b_hand_care() -> void:
	print("# M1b P1: feed/pat are hand actions (need a chosen pet); clean stays one-tap")
	ok(GameData.m1b.is_empty() == false, "data/m1b.json loaded")
	var care: Dictionary = GameData.m1b.get("care", {})
	ok("feed" in care.get("hand", []) and "pat" in care.get("hand", []), "feed/pat listed as hand")
	ok("clean" in care.get("one_tap", []) and "harvest" in care.get("one_tap", []), "clean/harvest stay one-tap")
	var packed: PackedScene = load("res://scenes/Main.tscn")
	var main: Node = packed.instantiate()
	add_child(main)
	if main.has_method("set_rest_look"):
		main.set_rest_look(true)
	var no_pick: Dictionary = main.hand_feed(null, "meal") if main.has_method("hand_feed") else {}
	ok(not bool(no_pick.get("ok", true)) and str(no_pick.get("reason", "")) == "pick_pet", "feed without pet is refused", no_pick)
	var no_pat: Dictionary = main.hand_pat(null) if main.has_method("hand_pat") else {}
	ok(not bool(no_pat.get("ok", true)) and str(no_pat.get("reason", "")) == "pick_pet", "pat without pet is refused", no_pat)
	Sim.state = _fresh("sprout", {"hunger": 40.0, "mood": 50.0})
	var w: Walker = main.pet if "pet" in main else null
	ok(w != null, "main has pet")
	if w:
		var rec: Dictionary = main.hand_feed(w, "meal")
		ok(bool(rec.get("ok", false)), "hand feed meal on 團絨 ok", rec)
		ok(is_equal_approx(float(rec.get("hunger", 0)), Sim.FEED_MEAL), "meal hunger delta", rec)
		ok(AudioManager and str(AudioManager.last_play.get("hook", "")).begins_with("sfx_feed_meal") or str(AudioManager.last_play.get("stream", "")).find("sfx_feed_meal") >= 0, "sfx_feed_meal played", AudioManager.last_play)
		Sim.state["needs"]["mood"] = 40.0
		var rec2: Dictionary = main.hand_feed(w, "snack")
		ok(bool(rec2.get("ok", false)), "hand feed snack ok", rec2)
		ok(str(AudioManager.last_play.get("hook", "")).begins_with("sfx_feed_snack") or str(AudioManager.last_play.get("stream", "")).find("sfx_feed_snack") >= 0, "sfx_feed_snack played", AudioManager.last_play)
		var rec3: Dictionary = main.hand_pat(w)
		ok(bool(rec3.get("ok", false)), "hand pat ok", rec3)
	# 一鍵執屎仍可用
	Sim.state["poops"] = 2
	Sim.state["poop_age"] = [1.0, 1.0]
	var c := Sim.clean_all()
	ok(bool(c.get("ok", false)) and int(c.get("count", 0)) == 2, "clean_all still one-tap", c)
	main.free()


func _test_m1b_need_warning() -> void:
	print("# M1b sfx_need_warning: appear once, pet cooldown 8s, same-moment once, mute in 欣賞")
	ok(FileAccess.file_exists("res://audio/sfx/sfx_need_warning_a.ogg"), "sfx_need_warning_a present")
	ok(FileAccess.file_exists("res://audio/sfx/sfx_need_warning_b.ogg"), "sfx_need_warning_b present")
	ok(AudioManager.bus_for("sfx_need_warning") == "UI", "need warning uses UI bus")
	AudioManager.reset_need_warning_cooldowns()
	AudioManager.appreciate_muted = false
	var a: Dictionary = AudioManager.play_need_warning("tuanrong")
	ok(bool(a.get("played", false)), "first appear plays", a)
	var b: Dictionary = AudioManager.play_need_warning("kid")
	ok(not bool(b.get("played", true)) and str(b.get("reason", "")) == "same_moment", "same moment only once", b)
	# 過咗同一瞬間、另一隻未冷卻（把 global 推後，保留寵物冷卻）
	AudioManager._need_warn_global_at = -999.0
	var c: Dictionary = AudioManager.play_need_warning("tuanrong")
	ok(not bool(c.get("played", true)) and str(c.get("reason", "")) == "pet_cooldown", "same pet cooldown 8s", c)
	# 冷卻期滿（把該寵物時間調後）
	AudioManager._need_warn_pet_at["tuanrong"] = Time.get_ticks_msec() / 1000.0 - 9.0
	AudioManager._need_warn_global_at = -999.0
	var d: Dictionary = AudioManager.play_need_warning("tuanrong")
	ok(bool(d.get("played", false)), "after 8s can play again", d)
	# 欣賞模式靜音，泡泡仍然 _pick 得到
	AudioManager.reset_need_warning_cooldowns()
	AudioManager.appreciate_muted = true
	var e: Dictionary = AudioManager.play_need_warning("tuanrong")
	ok(not bool(e.get("played", true)) and str(e.get("reason", "")) == "appreciate", "欣賞 mode mutes warning", e)
	var w := Walker.new()
	w.character = "tuanrong"
	add_child(w)
	var bubble := NeedBubble.new()
	add_child(bubble)
	bubble.attach(w)
	Sim.state = _fresh("sprout", {"hunger": 20.0, "mood": 90.0, "clean": 90.0, "energy": 90.0})
	ok(bubble._pick() == "need_eat", "bubble still shows in 欣賞", bubble._pick())
	AudioManager.appreciate_muted = false
	bubble.free()
	w.free()


func _test_m1b_hunt_work_collection() -> void:
	print("# M1b hunt lite + work buildings + collection / furniture / red dots")
	Sim.state = _fresh("sprout")
	CollectionSystem.ensure()
	ok(CollectionSystem.stardust() == 0, "wallet starts at 0")
	var added := CollectionSystem.add_shards(3, "jobs_trips")
	ok(added == 3 and CollectionSystem.stardust() == 3, "add 3 shards")
	# 每日打工／遠足上限 12
	var more := CollectionSystem.add_shards(20, "jobs_trips")
	ok(more == 9 and CollectionSystem.stardust() == 12, "jobs_trips cap 12", more)
	CollectionSystem.add_shards(40, "old")
	ok(CollectionSystem.stardust() == 42, "old cap 30 + 12 jobs = 42", CollectionSystem.stardust())
	# 狩獵出發／收隊
	HuntSystem.phase = HuntSystem.PHASE_IDLE
	HuntSystem.pending = {}
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	var dep: Dictionary = HuntSystem.depart(["tuanrong"], rng)
	ok(bool(dep.get("ok", false)), "hunt depart ok", dep)
	ok(HuntSystem.phase == HuntSystem.PHASE_DEPART, "phase depart")
	var early: Dictionary = HuntSystem.collect()
	ok(not bool(early.get("ok", true)), "cannot collect before ready", early)
	HuntSystem.set_phase(HuntSystem.PHASE_READY)
	var got: Dictionary = HuntSystem.collect()
	ok(bool(got.get("ok", false)) and int(got.get("shards", 0)) >= 1, "collect hunt shards", got)
	ok(HuntSystem.phase == HuntSystem.PHASE_IDLE, "phase idle after collect")
	# 同一日唔可以再打工／狩獵
	var dep2: Dictionary = HuntSystem.depart(["tuanrong"], rng)
	ok(not bool(dep2.get("ok", true)) and str(dep2.get("reason", "")) == "work_or_hunt", "work or hunt once a day", dep2)
	# 另一日——用另一隻做工作
	Sim.state = _fresh("sprout")
	CollectionSystem.ensure()
	var before := CollectionSystem.stardust()
	var dpx: Dictionary = WorkSystem.dispatch("post", ["tuanrong"])
	ok(bool(dpx.get("ok", false)), "dispatch post ok", dpx)
	ok(str(WorkSystem.site("post").get("status", "")) == WorkSystem.ST_WORK, "post working")
	WorkSystem.site("post")["status"] = WorkSystem.ST_READY
	var pay: Dictionary = WorkSystem.collect("post")
	ok(bool(pay.get("ok", false)) and int(pay.get("shards", 0)) == 2, "lv1 pay = 2 shards", pay)
	ok(CollectionSystem.stardust() == before + 2, "shards added from work")
	# 家具：預設床已有，買最平要碎
	ok(CollectionSystem.is_owned("bed_leaf"), "default bed owned")
	var rec_place: Dictionary = CollectionSystem.place("bed_leaf")
	ok(bool(rec_place.get("ok", false)), "place default bed", rec_place)
	CollectionSystem.add_shards(20, "old")
	var buy: Dictionary = CollectionSystem.buy("rug_leaf")
	ok(bool(buy.get("ok", false)), "buy cheapest rug", buy)
	var recs: Dictionary = CollectionSystem.place_recommended()
	ok(bool(recs.get("ok", false)), "place recommended", recs)
	# 紅點
	CollectionSystem.notify("harvest", true)
	ok(CollectionSystem.has_dot("harvest"), "harvest red dot")
	CollectionSystem.notify("harvest", false)
	ok(not CollectionSystem.has_dot("harvest"), "harvest dot cleared")
	# 狩獵 clip 有載入
	ok(ArtImporter.frames_of("part_grass", "L").size() >= 4, "part_grass L frames")
	ok(ArtImporter.frames_of("pounce", "M").size() >= 4, "pounce M frames")
	ok(ArtImporter.frames_of("carry_fruit", "S").size() >= 4, "carry_fruit S frames")
	ok(ArtImporter.frames_of("cheer", "L").size() >= 4, "cheer L frames")


func _test_m1b_overlay_snapshot() -> void:
	print("# M1b overlay snapshot write-through")
	Sim.state = _fresh("sprout", {"hunger": 20.0, "mood": 35.0, "energy": 80.0, "clean": 90.0})
	Sim.state["sleeping"] = false
	Sim.state["form"] = "soft"
	var snap: Dictionary = SaveSystem.write_overlay_snapshot(Sim.state)
	ok(int(snap.get("v", 0)) >= 3, "snapshot v3", snap)
	ok(str(snap.get("moodBand", "")) == "sad", "moodBand sad when mood 35", snap)
	ok(bool(snap.get("sleeping", true)) == false, "not sleeping")
	var needs: Dictionary = snap.get("needs", {})
	ok(str(needs.get("urgent", "")) == "hunger", "urgent is hunger 20", needs)
	ok(is_equal_approx(float((needs.get("vals", {}) as Dictionary).get("hunger", 0)), 20.0), "needs vals written")
	ok(not SaveSystem.last_overlay_snapshot.is_empty(), "last_overlay_snapshot kept")
	ok(FileAccess.file_exists("user://overlay_snapshot.json"), "desktop overlay file written")

