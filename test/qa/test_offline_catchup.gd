extends GutTest
## 離線補時對照舊 HTML5 sim.js：保底 20、成長封頂 24h、光粒只在離線禮物、
## 時鐘回撥 T=0、resume／focus 唔雙重補、10 分／1h／8h／24h／48h、有變先寫檔。
## 跑喺 code/glimmer-godot @ 86769723。未改遊程碼。

const H := 3600.0


func before_each() -> void:
	Sim.paused = true
	TimeService.use_fake(1_700_000_000_000)
	TimeService.mark_sim()
	TimeService._in_catch_up = false


func test_fullness_floor_is_20() -> void:
	assert_almost_eq(Sim.OFF_FLOOR, 20.0, 0.001)
	var s := _sprout(100.0)
	var rep: Dictionary = Sim.apply_offline(s, _away(48.0 * H))
	var n: Dictionary = s["needs"]
	for k in ["hunger", "mood", "clean", "energy"]:
		assert_gte(float(n[k]), 20.0, "%s stayed at or above floor after 48h" % k)
	# 飢由 100 跌穿 20 之後要停喺保底，唔好再落到 0。
	assert_almost_eq(float(n["hunger"]), 20.0, 0.6, "hunger sits on the floor")
	# 本來已經低過保底就唔拉高。
	var low := _sprout(10.0)
	Sim.apply_offline(low, _away(8.0 * H))
	assert_almost_eq(float(low["needs"]["hunger"]), 10.0, 0.6, "floor does not raise a need already under 20")
	gut.p("48h E=%.0f hunger=%.2f" % [float(rep["E"]), float(n["hunger"])])


func test_growth_capped_at_24h() -> void:
	assert_almost_eq(Sim.OFF_GROW_CAP_H, 24.0, 0.001)
	for hours in [10.0 / 60.0, 1.0, 8.0, 24.0, 48.0]:
		var s := _sprout(100.0)
		s["growth_sec"] = 0.0
		var rep: Dictionary = Sim.apply_offline(s, _away(hours * H))
		var grow: Dictionary = rep["grow"]
		var expect := minf(hours * H, 24.0 * H)
		assert_almost_eq(float(grow["G"]), expect, 1.0, "growth G at %.2fh" % hours)
	gut.p("48h growth G capped at 24h")


func test_light_grains_are_offline_gift_only() -> void:
	var online := _sprout(80.0)
	online["grains"] = 4
	Sim.advance(online, H, {})
	assert_eq(int(online["grains"]), 4, "one online hour does not mint grains")
	var cases := {
		10.0 / 60.0: 1,
		1.0: 1,
		8.0: 8,
		24.0: 10,
		48.0: 10,
	}
	for hours in cases:
		var s := _sprout(80.0)
		s["grains"] = 0
		var rep: Dictionary = Sim.apply_offline(s, _away(float(hours) * H))
		assert_eq(int(rep["gift"]), int(cases[hours]), "gift at %.2fh" % float(hours))
		assert_eq(int(s["grains"]), int(cases[hours]), "wallet at %.2fh" % float(hours))
		gut.p("%.2fh gift=%d E=%.0f T=%.0f hunger=%.1f" % [
			float(hours), int(rep["gift"]), float(rep["E"]), float(rep["T"]), float(s["needs"]["hunger"])
		])


func test_clock_backwards_is_zero() -> void:
	var s := _sprout(90.0)
	var now := TimeService.now_ms()
	s["last_seen"] = now + int(H * 1000.0)
	s["grains"] = 5
	var before := int(s["last_seen"])
	var rep: Dictionary = TimeService.catch_up(s)
	assert_true(bool(rep.get("rollback", false)))
	assert_eq(float(rep.get("T", -1)), 0.0)
	assert_eq(int(s["grains"]), 5, "no gift when the clock moves backwards")
	assert_eq(int(s["last_seen"]), before, "last_seen is not pulled backwards")


func test_no_double_catch_up_across_return_paths() -> void:
	var s := _sprout(100.0)
	s["grains"] = 0
	var past := TimeService.now_ms() - int(8.0 * H * 1000.0)
	s["last_seen"] = past
	# 上次確實有模擬係 8 小時前；若 mark_sim 停喺而家，catch_up 會當已經補過。
	TimeService._last_sim_ms = past
	var first: Dictionary = TimeService.catch_up(s)
	var grains := int(s["grains"])
	assert_eq(int(first.get("gift", 0)), 8)
	# focus 之後再 resume：last_seen 已拉到而家，第二次唔再派。
	var second: Dictionary = TimeService.catch_up(s)
	assert_true(bool(second.get("skipped", false)))
	assert_eq(int(s["grains"]), grains, "resume then focus does not gift twice")
	# 重入（同一次回前台叠兩個通知）直接跳過。
	TimeService._in_catch_up = true
	var nested: Dictionary = TimeService.catch_up(s)
	TimeService._in_catch_up = false
	assert_true(bool(nested.get("duplicate", false)))
	assert_eq(int(s["grains"]), grains)
	# 回前台同聚焦係同一條 catch_up；冇第三條 visibility handler。
	var src := FileAccess.get_file_as_string("res://scripts/autoload/TimeService.gd")
	assert_true(src.find("NOTIFICATION_APPLICATION_RESUMED") >= 0)
	assert_true(src.find("NOTIFICATION_WM_WINDOW_FOCUS_IN") >= 0)
	assert_eq(src.find("NOTIFICATION_APPLICATION_FOCUS_IN"), -1)
	assert_eq(src.find("visibility"), -1)


func test_save_writes_only_when_something_changed() -> void:
	Sim.state = _sprout(70.0)
	Sim.state["grains"] = 2
	Sim._dirty = true
	Sim._save_now(false)
	var before := FileAccess.get_file_as_string("user://save_v1.json")
	Sim._dirty = false
	Sim._save_now(false)
	var after_clean := FileAccess.get_file_as_string("user://save_v1.json")
	assert_eq(after_clean, before, "clean _save_now does not rewrite")
	Sim.state["grains"] = 9
	Sim._dirty = true
	Sim._save_now(false)
	var after_dirty := FileAccess.get_file_as_string("user://save_v1.json")
	assert_ne(after_dirty, before)
	assert_true(after_dirty.find("\"grains\": 9") >= 0 or after_dirty.find("\"grains\":9") >= 0)


func _sprout(hunger: float) -> Dictionary:
	var s := Sim.new_state(TimeService.now_ms())
	s["stage"] = "sprout"
	s["growth_sec"] = 0.0
	s["needs"] = {"hunger": hunger, "mood": hunger, "clean": hunger, "energy": hunger}
	s["last_seen"] = TimeService.now_ms()
	s["last_save_time"] = TimeService.now_ms()
	s["grains"] = 0
	s["poops"] = 0
	s["poop_timer"] = 0.0
	s["sleeping"] = false
	return s


func _away(sec: float) -> int:
	return TimeService.now_ms() + int(sec * 1000.0)
