extends Node
## 單元測試之後：低／中 frame time、日夜、412／768 闊、寵物前後遮擋截圖。

func _shot_dir() -> String:
	var d := str(OS.get_environment("GODOT_SHOT_DIR"))
	if d == "":
		d = "/home/box/keep/godot/G0.1"
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
	print("=== G0.1 smoke ===")
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

	print("SMOKE_OK")
	get_tree().quit(0)
