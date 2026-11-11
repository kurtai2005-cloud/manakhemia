extends Node
## 載入主場景、跑幀、量低畫質 frame time、截圖。

func _ready() -> void:
	print("=== G0 smoke ===")
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
	for i in range(60):
		await get_tree().process_frame
	var times: Array = []
	var t0 := Time.get_ticks_usec()
	for i in range(120):
		await get_tree().process_frame
		var t1 := Time.get_ticks_usec()
		var ms := float(t1 - t0) / 1000.0
		t0 = t1
		times.append(ms)
	times.sort()
	var sum := 0.0
	for x in times:
		sum += float(x)
	var avg := sum / times.size()
	var p95: float = times[int(floor((times.size() - 1) * 0.95))]
	var mx: float = times[times.size() - 1]
	print("LOW frame_ms avg=%.2f p95=%.2f max=%.2f n=%d (target ~33ms for 30fps)" % [avg, p95, mx, times.size()])
	# 解鎖 30fps cap 量真實 frame time
	var cap := Engine.max_fps
	Engine.max_fps = 0
	for i in range(20):
		await get_tree().process_frame
	times.clear()
	t0 = Time.get_ticks_usec()
	for i in range(90):
		await get_tree().process_frame
		var t2 := Time.get_ticks_usec()
		times.append(float(t2 - t0) / 1000.0)
		t0 = t2
	times.sort()
	sum = 0.0
	for x in times:
		sum += float(x)
	avg = sum / times.size()
	p95 = times[int(floor((times.size() - 1) * 0.95))]
	mx = times[times.size() - 1]
	print("LOW uncapped frame_ms avg=%.2f p95=%.2f max=%.2f n=%d" % [avg, p95, mx, times.size()])
	Engine.max_fps = cap
	var vp := get_viewport()
	if vp:
		await RenderingServer.frame_post_draw
		var img := vp.get_texture().get_image()
		if img:
			img.save_png("/tmp/g0_smoke.png")
			img.save_png("user://g0_smoke.png")
			print("screenshot /tmp/g0_smoke.png ", img.get_width(), "x", img.get_height())
	print("SMOKE_OK")
	get_tree().quit(0)
