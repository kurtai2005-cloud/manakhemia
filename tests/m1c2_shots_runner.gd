extends Node
## M1c.2：傢俬（含牆上散步鞋架）＋狩獵場（花園中景道具應已收埋）。

func _ready() -> void:
	_boot()


func _boot() -> void:
	await get_tree().process_frame
	var d := str(OS.get_environment("GODOT_SHOT_DIR"))
	if d == "":
		d = "/home/box/keep/godot/M1c2"
	DirAccess.make_dir_recursive_absolute(d)
	print("shots: start ", d)
	QualitySettings.set_tier(QualitySettings.Tier.LOW)
	var packed: PackedScene = load("res://scenes/Main.tscn")
	if packed == null:
		printerr("FAIL Main.tscn")
		get_tree().quit(1)
		return
	var main: Node = packed.instantiate()
	get_tree().root.add_child(main)
	await get_tree().process_frame
	await get_tree().process_frame
	if main.has_method("set_shot_size"):
		main.set_shot_size(390, 844)
	if TimeService:
		TimeService.use_fake(TimeService.local_wall_ms(12.0, 0.0))
	if main.has_method("qa_overview"):
		main.qa_overview()

	# 床（預設已有）＋地氈＋牆上鞋架
	if CollectionSystem:
		if CollectionSystem.stardust() < 40:
			CollectionSystem.add_shards(40, "old")
		if not CollectionSystem.is_owned("rug_leaf"):
			CollectionSystem.buy("rug_leaf")
		if not CollectionSystem.is_owned("wall_shoes"):
			CollectionSystem.buy("wall_shoes")
		CollectionSystem.place("bed_leaf", "bed")
		CollectionSystem.place("rug_leaf", "rug")
		CollectionSystem.place("wall_shoes", "wall")
	if main.has_method("refresh_furniture"):
		main.refresh_furniture()
	await get_tree().process_frame
	await get_tree().process_frame
	await _save(main, d, "m1c2-furniture")

	# 入場狩獵，睇遠景有冇花園中景道具
	if main.has_method("start_hunt"):
		main.start_hunt()
	if HuntSystem:
		var dur := float(GameData.m1b.get("hunt", {}).get("watch_sec", 18))
		HuntSystem.watch_elapsed = dur * 0.20
		HuntSystem.tick_watch(0.0)
	await get_tree().process_frame
	await get_tree().process_frame
	await get_tree().process_frame
	# 再等一幀讓鏡頭跟 hunt look_target
	for i in range(8):
		await get_tree().process_frame
	await _save(main, d, "m1c2-hunt")
	print("shots: done")
	get_tree().quit(0)


func _save(main: Node, d: String, stem: String) -> void:
	await get_tree().process_frame
	var vp: Viewport = get_tree().root.get_viewport()
	if main.has_method("get") and main.get("cam"):
		vp = (main as Node).get_viewport()
	var img: Image = vp.get_texture().get_image()
	if img:
		var path := "%s/%s.png" % [d, stem]
		img.save_png(path)
		print("screenshot ", stem, " ", img.get_width(), "x", img.get_height(), " ", path)
	else:
		printerr("FAIL no image for ", stem)
