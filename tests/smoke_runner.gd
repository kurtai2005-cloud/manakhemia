extends Node
## 單元測試之後：低／中 frame time、日夜、412／768 闊、寵物前後遮擋截圖。

func _shot_dir() -> String:
	var d := str(OS.get_environment("GODOT_SHOT_DIR"))
	if d == "":
		d = "/home/box/keep/godot/M1a"
	DirAccess.make_dir_recursive_absolute(d)
	return d


func _save_shot(vp: Viewport, stem: String) -> void:
	if vp == null:
		return
	await RenderingServer.frame_post_draw
	var img := vp.get_texture().get_image()
	if img == null:
		return
	var d := _shot_dir()
	img.save_png("/tmp/%s.png" % stem)
	img.save_png("%s/%s.png" % [d, stem])
	print("screenshot ", stem, " ", img.get_width(), "x", img.get_height())


func _measure(label: String, n_warm: int, n: int) -> void:
	for i in range(n_warm):
		await get_tree().process_frame
	var times: Array = []
	var t0 := Time.get_ticks_usec()
	for i in range(n):
		await get_tree().process_frame
		var t1 := Time.get_ticks_usec()
		times.append(float(t1 - t0) / 1000.0)
		t0 = t1
	times.sort()
	var sum := 0.0
	for x in times:
		sum += float(x)
	var avg := sum / times.size()
	var p95: float = times[int(floor((times.size() - 1) * 0.95))]
	var mx: float = times[times.size() - 1]
	print("%s frame_ms avg=%.2f p95=%.2f max=%.2f n=%d" % [label, avg, p95, mx, times.size()])


func _prep(main: Node, tod: String, pose: String) -> void:
	if main and main.has_method("set_rest_look"):
		main.set_rest_look(true)
	if main and main.has_method("qa_place_pet"):
		main.qa_place_pet(pose)
	if main and main.has_method("set_time_of_day"):
		main.set_time_of_day(tod)
	# 截圖時鐘同日夜段對齊（夜晚唔好仲顯示朝早）
	if TimeService:
		var hour := 12.0
		if tod == "morning":
			hour = 8.0
		elif tod == "evening":
			hour = 18.0
		elif tod == "night":
			hour = 23.0
		elif tod == "day" or tod == "noon":
			hour = 12.0
		TimeService.use_fake(TimeService.local_wall_ms(hour, 0.0))
	for i in range(6):
		await get_tree().process_frame
	if main and main.has_method("qa_framing"):
		print("framing ", tod, " ", pose, " ", main.qa_framing())


func _ready() -> void:
	print("=== M1a smoke ===")
	print("visual checklist: res://tools/visual_checklist.md")
	QualitySettings.set_tier(QualitySettings.Tier.LOW)
	await get_tree().process_frame
	var packed: PackedScene = load("res://scenes/Main.tscn")
	if packed == null:
		printerr("FAIL: Main.tscn missing")
		get_tree().quit(1)
		return
	var root := packed.instantiate()
	get_tree().root.add_child(root)
	await get_tree().process_frame
	await get_tree().process_frame
	if root.get_child_count() == 0:
		printerr("FAIL: Main has no children — scene did not build")
		get_tree().quit(2)
		return
	print("Main children=", root.get_child_count())
	var main := get_tree().root.get_node_or_null("Main")
	if str(OS.get_environment("GODOT_SMOKE_QUICK")) == "1":
		await _quick_m1a(main)
		print("SMOKE_QUICK_OK")
		get_tree().quit(0)
		return
	await _prep(main, "day", "default")

	# LOW cap（目標 ~33ms @30fps）— 喺休息鏡頭量，避免行路干擾
	await _measure("LOW cap", 40, 120)
	var cap := Engine.max_fps
	Engine.max_fps = 0
	await _measure("LOW uncapped", 20, 90)
	Engine.max_fps = cap

	var vp := get_viewport()
	# 設計闊 390：日／夜低檔
	await _prep(main, "day", "default")
	await _save_shot(vp, "g01-day")
	await _prep(main, "night", "default")
	await _save_shot(vp, "g01-night")

	# 遮擋：寵物喺樹／小屋前同後（低檔日間）
	await _prep(main, "day", "front_tree")
	await _save_shot(vp, "g01-day-front-tree")
	await _prep(main, "day", "behind_tree")
	await _save_shot(vp, "g01-day-behind-tree")
	await _prep(main, "day", "front_cottage")
	await _save_shot(vp, "g01-day-front-cottage")
	await _prep(main, "day", "behind_cottage")
	await _save_shot(vp, "g01-day-behind-cottage")

	# mid：同一 3D 花園
	QualitySettings.set_tier(QualitySettings.Tier.MID)
	await _prep(main, "day", "default")
	await _measure("MID cap", 20, 60)
	Engine.max_fps = 0
	await _measure("MID uncapped", 10, 45)
	Engine.max_fps = 60
	await _save_shot(vp, "g01-mid-day")
	await _prep(main, "night", "default")
	await _save_shot(vp, "g01-mid-night")

	# 闊度 412／768（低＋中，日；另加低檔夜）
	for pair in [Vector2i(412, 892), Vector2i(768, 1024)]:
		var w: int = pair.x
		var h: int = pair.y
		if main and main.has_method("set_shot_size"):
			main.set_shot_size(w, h)
		for i in range(8):
			await get_tree().process_frame
		QualitySettings.set_tier(QualitySettings.Tier.LOW)
		await _prep(main, "day", "default")
		await _save_shot(vp, "g01-w%d-day" % w)
		await _prep(main, "night", "default")
		await _save_shot(vp, "g01-w%d-night" % w)
		QualitySettings.set_tier(QualitySettings.Tier.MID)
		await _prep(main, "day", "default")
		await _save_shot(vp, "g01-w%d-mid-day" % w)

	# M1a 玩法截圖（總覽、跟拍、需要泡泡、一鍵照顧＋總結卡）
	if main and main.has_method("set_shot_size"):
		main.set_shot_size(390, 844)
	QualitySettings.set_tier(QualitySettings.Tier.LOW)
	if main and main.has_method("qa_overview"):
		main.qa_overview()
	else:
		await _prep(main, "day", "default")
	for i in range(8):
		await get_tree().process_frame
	if main and main.has_method("qa_framing"):
		print("framing overview ", main.qa_framing())
	await _save_shot(vp, "m1a-overview")
	if main and main.has_method("qa_follow_pet"):
		main.qa_follow_pet()
	for i in range(8):
		await get_tree().process_frame
	if main and main.has_method("qa_framing"):
		print("framing follow ", main.qa_framing())
	await _save_shot(vp, "m1a-follow")
	if main and main.has_method("qa_overview"):
		main.qa_overview()
	if main and main.has_method("qa_force_needs"):
		main.qa_force_needs(20.0, 90.0, 90.0, 90.0)
	for i in range(10):
		await get_tree().process_frame
	await _save_shot(vp, "m1a-bubbles")
	# 一鍵摸頭／餵／執 → 總結卡（退出跟拍先睇到底欄）
	if main and main.has_method("qa_overview"):
		main.qa_overview()
	if Sim:
		Sim.state["poops"] = 2
		Sim.state["poop_age"] = [1.0, 2.0]
		var n: Dictionary = Sim.state.get("needs", {})
		n["hunger"] = 40.0
		n["mood"] = 50.0
		Sim.state["needs"] = n
		Sim.state_changed.emit()
		Sim.feed("meal")
		Sim.pat()
		Sim.clean_all()
	for i in range(12):
		await get_tree().process_frame
	await _save_shot(vp, "m1a-care")
	if main and main.has_method("qa_family") and main.qa_family("walk_together"):
		for i in range(10):
			await get_tree().process_frame
		await _save_shot(vp, "m1a-family")

	print("SMOKE_OK")
	get_tree().quit(0)


func _quick_m1a(main: Node) -> void:
	var vp := get_viewport()
	print("quick: prep")
	QualitySettings.set_tier(QualitySettings.Tier.LOW)
	await _prep(main, "day", "default")
	print("quick: care")
	if Sim:
		var n: Dictionary = Sim.state.get("needs", {})
		n["hunger"] = 40.0
		n["mood"] = 50.0
		Sim.state["needs"] = n
		Sim.state["poops"] = 2
		Sim.state["poop_age"] = [1.0, 2.0]
		print("quick: state")
		Sim.state_changed.emit()
		print("quick: feed", Sim.feed("meal"))
		print("quick: pat", Sim.pat())
		print("quick: clean", Sim.clean_all())
	print("quick: frames")
	for i in range(4):
		await get_tree().process_frame
		print("quick: frame ", i)
	print("quick: save care")
	await _save_shot(vp, "m1a-care")
	print("quick: saved care")
	if main and main.has_method("qa_overview"):
		main.qa_overview()
	if main and main.has_method("qa_family"):
		main.qa_family("walk_together")
	for i in range(10):
		await get_tree().process_frame
	await _save_shot(vp, "m1a-family")
